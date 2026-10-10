"""The persistent Blender server (spec 18 §4.8.1): one warm Blender per agent, driven over JSON lines
on 127.0.0.1 by scripts/tools/bl.py.

  blender -b [file.blend] --python scripts/server/blender_server.py -- --name a --port 0 [--parts 05,15]

Started by `bl.py start`, which passes the token in SGT_SERVER_TOKEN and reads the port from the
`LISTENING <port>` line of the server's log. Single-threaded on purpose: Blender's operators must run
on its main thread, so requests from several connections queue and run one at a time. Before a build,
a render or a measurement every changed module under scripts/ is reloaded in place, with the modules
that import it, so an edited part or library runs without a restart.

Long commands (optimise, variants) stream progress when the request asks: lines {"id", "progress"} with
no "ok", before the reply, on the same connection; bl.py prints them and keeps waiting.
"""
import argparse
import ast
import contextlib
import glob
import hmac
import importlib
import importlib.util
import io
import itertools
import json
import math
import os
import selectors
import socket
import sys
import time
import traceback

import bpy
import numpy as np

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from lib import cache, cli, env, linmodel, log, measure, naming, optim, params, replace  # noqa: E402
from server import protocol  # noqa: E402

RESTART_BUILDS = 200  # §4.8.1 hygiene: a restart is advised after this many builds ...
RESTART_RSS_MB = 5000  # ... or past this resident size (two servers fit in 15 GB with Cycles headroom)
SILHOUETTE_ARGS = ("preset", "objects", "method", "scale", "out", "diff", "band", "declared", "view")


def rel(path):
    return os.path.relpath(path, env.PROJECT_DIR).replace(os.sep, "/")


def _mtime(path):
    try:
        return os.stat(path).st_mtime_ns
    except OSError:
        return None


def rss_mb():
    """Resident memory of this process in MB (the restart rule)."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes as wt

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD)] + [
                (n, ctypes.c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                                               "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                                               "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
        k32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
        k32.GetCurrentProcess.restype = wt.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(Counters), wt.DWORD]
        c = Counters()
        c.cb = ctypes.sizeof(Counters)
        psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb)
        return round(c.WorkingSetSize / 1e6, 1)
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return round(int(line.split()[1]) / 1e3, 1)
    except OSError:
        pass
    return None


class Reloader:
    """Reloads every changed module under scripts/ (by mtime) and the modules that import it,
    dependencies first, so `from x import y` bindings are refreshed too (§4.8.1, build). Reloading in
    place keeps module identity, so the server's own references and the parameter registry hold."""

    def __init__(self):
        self.mtimes = {}
        self.scan()

    @staticmethod
    def tracked():
        server_dir = cache._norm(os.path.join(SCRIPTS, "server")) + os.sep
        scripts = cache._norm(SCRIPTS) + os.sep
        out = {}
        for name, m in list(sys.modules.items()):
            f = getattr(m, "__file__", None)
            if not f or name == "__main__" or name.startswith("part_"):  # parts are re-imported, not reloaded
                continue
            nf = cache._norm(f)
            if nf.startswith(scripts) and not nf.startswith(server_dir):
                out[name] = m
        return out

    def scan(self):
        self.mtimes = {n: _mtime(m.__file__) for n, m in self.tracked().items()}

    def refresh(self):
        """Reload what changed; returns the reloaded module names in order."""
        mods = self.tracked()
        changed = {n for n, m in mods.items() if _mtime(m.__file__) != self.mtimes.get(n)}
        if not changed:
            return []
        by_file = {cache._norm(m.__file__): n for n, m in mods.items()}
        deps = {n: {by_file[f] for f in cache.direct_imports(m.__file__) if f in by_file} - {n}
                for n, m in mods.items()}
        todo = set(changed)
        while True:  # everything that imports a reloaded module, transitively
            more = {n for n, d in deps.items() if n not in todo and d & todo}
            if not more:
                break
            todo |= more
        order = []
        while todo - set(order):
            ready = sorted(n for n in todo - set(order) if not (deps[n] & todo) - set(order))
            order += ready or sorted(todo - set(order))  # a cycle: take the rest as they come
        for n in order:
            importlib.reload(mods[n])
        self.scan()
        return order


@contextlib.contextmanager
def _kept(obj, names):
    """Restore these properties afterwards, so a render does not change the session's settings."""
    old = {n: getattr(obj, n) for n in names}
    try:
        yield obj
    finally:
        for n, v in old.items():
            try:
                setattr(obj, n, v)
            except (AttributeError, TypeError, ValueError):
                pass


def workbench(out, size=None, aa="8"):
    """A Workbench form render of the scene camera (spec 17's `form` look: clay matcap, single colour
    0.8, cavity ridge and valley 1.0, no shadows); returns seconds and the image size."""
    sc = bpy.context.scene
    if sc.camera is None:
        raise RuntimeError("the scene has no camera to render from")
    r, disp, sh = sc.render, sc.display, sc.display.shading
    with _kept(r, ("engine", "resolution_x", "resolution_y", "resolution_percentage", "filepath",
                   "film_transparent", "use_file_extension")), \
            _kept(r.image_settings, ("file_format", "color_mode", "color_depth")), _kept(disp, ("render_aa",)), \
            _kept(sh, ("light", "studio_light", "color_type", "single_color", "show_cavity", "cavity_type",
                       "cavity_ridge_factor", "cavity_valley_factor", "show_shadows")):
        r.engine = "BLENDER_WORKBENCH"
        sh.light = "MATCAP"
        try:
            sh.studio_light = "clay_studio.exr"
        except TypeError:  # not in this Blender's matcaps: keep its default
            pass
        sh.color_type, sh.single_color = "SINGLE", (0.8, 0.8, 0.8)
        sh.show_cavity, sh.cavity_type = True, "BOTH"
        sh.cavity_ridge_factor = sh.cavity_valley_factor = 1.0
        sh.show_shadows = False
        disp.render_aa = aa
        if size:
            r.resolution_x, r.resolution_y = int(size[0]), int(size[1])
        r.resolution_percentage = 100
        r.film_transparent, r.use_file_extension = False, True
        r.image_settings.file_format, r.image_settings.color_mode, r.image_settings.color_depth = "PNG", "RGB", "8"
        t = time.perf_counter()
        with cache.atomic(out) as tmp:
            r.filepath = tmp
            bpy.ops.render.render(write_still=True)
        return {"s": round(time.perf_counter() - t, 4), "size": [r.resolution_x, r.resolution_y]}


class Server:
    def __init__(self, name, port, token):
        self.name, self.port, self.token = name, port, token
        self.t0, self.requests, self.builds, self.done = time.time(), 0, 0, False
        self.reloader = Reloader()
        self.parts = {}  # part id -> (path, mtime, module)
        self.parts_dir = os.path.join(SCRIPTS, "parts")  # a selftest points this at a scratch folder
        self.events = protocol.events_path(name)
        self.models = {}  # (object, keys) -> linmodel.LinearModel, dropped when the session's meshes change
        self._conn, self._rid, self._progress = None, None, False  # the request in hand, for progress lines
        self.ns = {"bpy": bpy, "server": self, "cache": cache, "cli": cli, "env": env, "log": log,
                   "naming": naming, "params": params, "replace": replace, "measure": measure,
                   "linmodel": linmodel, "optim": optim}  # exec's namespace, kept

    # ------------------------------------------------------------------ transport

    def serve(self):
        srv = socket.create_server((protocol.HOST, self.port))
        srv.setblocking(False)
        sel = selectors.DefaultSelector()
        sel.register(srv, selectors.EVENT_READ, None)
        print(f"{protocol.LISTENING} {srv.getsockname()[1]}", flush=True)
        try:
            while not self.done:
                for key, _ in sel.select(timeout=1.0):
                    if key.data is None:
                        conn, _ = srv.accept()
                        conn.setblocking(True)
                        conn.settimeout(300)  # a client that stops reading cannot hang the server
                        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                        sel.register(conn, selectors.EVENT_READ, protocol.Lines())
                        continue
                    conn = key.fileobj
                    try:
                        data = conn.recv(1 << 16)
                        lines = key.data.feed(data) if data else None
                    except (OSError, ValueError):
                        lines = None
                    if lines is None:
                        sel.unregister(conn)
                        conn.close()
                        continue
                    for line in lines:
                        self._conn = conn
                        try:
                            conn.sendall(protocol.encode(self.handle(line)))
                        except OSError:
                            break
                        finally:
                            self._conn = None
                        if self.done:
                            break
        finally:
            for key in list(sel.get_map().values()):
                key.fileobj.close()
            sel.close()
        print("SERVER_EXIT", flush=True)

    def handle(self, line):
        t = time.perf_counter()
        rid, cmd, args = None, "?", {}
        try:
            req = protocol.decode(line)
            rid, cmd, args = req.get("id"), str(req.get("cmd")), req.get("args") or {}
            if not hmac.compare_digest(str(req.get("token", "")), self.token):
                raise PermissionError("bad token")
            self._rid, self._progress = rid, bool(isinstance(args, dict) and args.get("progress"))
            fn = getattr(self, "cmd_" + cmd, None)
            if fn is None:
                raise KeyError(f"unknown command {cmd!r}; the commands are {', '.join(protocol.COMMANDS)}")
            msg = protocol.reply(rid, 0, result=log.jsonable(fn(args)))
        except (Exception, SystemExit) as e:  # exec'd code calling sys.exit must not stop the server
            msg = protocol.reply(rid, 0, error=f"{type(e).__name__}: {e}", trace=traceback.format_exc(limit=-6))
        msg["ms"] = round((time.perf_counter() - t) * 1e3, 3)
        self.requests += 1
        if cmd not in ("ping", "status"):
            extra = {"code": args.get("code")} if cmd == "exec" else {}
            log.jsonl(self.events, cmd=cmd, id=rid, ok=msg["ok"], ms=msg["ms"], error=msg.get("error"), **extra)
        return msg

    # ------------------------------------------------------------------ helpers

    def restart_advised(self, mem=None):
        mem = rss_mb() if mem is None else mem
        return self.builds >= RESTART_BUILDS or (mem or 0) > RESTART_RSS_MB

    def progress(self, rec):
        """A progress line for the request in hand, if it asked for them: {"id", "progress"}, no "ok"."""
        if self._conn is None or not self._progress:
            return
        try:
            self._conn.sendall(protocol.encode({"id": self._rid, "progress": log.jsonable(rec)}))
        except OSError:  # the client went away; finish the work regardless
            self._conn = None

    def invalidate(self):
        """The session's meshes may have changed under the measurement caches (a build, load or restore)."""
        measure.forget()
        self.models.clear()

    def refresh_code(self):
        """Reload changed modules before a measurement; models built by an old linmodel are dropped."""
        reloaded = self.reloader.refresh()
        if reloaded:
            self.invalidate()
        return reloaded

    def part_module(self, pid, force=False):
        """The part script for an id, imported afresh when it changed or anything was reloaded."""
        hits = sorted(glob.glob(os.path.join(self.parts_dir, f"{pid}_*.py")))
        if not hits:
            raise cli.MissingDependency(f"no {rel(self.parts_dir)}/{pid}_*.py")
        path, have = hits[0], self.parts.get(pid)
        if have and have[0] == path and have[1] == _mtime(path) and not force:
            return have[2]
        name = "part_" + os.path.basename(path)[:-3]
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        for need in ("PART", "build"):
            if not hasattr(mod, need):
                raise AttributeError(f"{rel(path)} defines no {need}")
        self.parts[pid] = (path, _mtime(path), mod)
        return mod

    # ------------------------------------------------------------------ commands

    def cmd_ping(self, a):
        return {"pong": True, "name": self.name, "pid": os.getpid()}

    def cmd_status(self, a):
        mem = rss_mb()
        return {"name": self.name, "pid": os.getpid(), "uptime_s": round(time.time() - self.t0, 1),
                "requests": self.requests, "builds": self.builds, "rss_mb": mem,
                "restart_advised": self.restart_advised(mem), "blend": bpy.data.filepath,
                "blender": bpy.app.version_string, "objects": len(bpy.data.objects),
                "meshes": len(bpy.data.meshes),
                "parts": {c.name + (" (linked)" if c.library else ""): len(c.all_objects)
                          for c in bpy.data.collections if c.name.startswith("Part") and c.name != naming.PARTS},
                "params": sorted(params.REGISTRY)}

    def cmd_exec(self, a):
        """Run Python in the session (debugging only; logged). The last expression's value is returned."""
        tree = ast.parse(a["code"], "<exec>", "exec")
        last = tree.body.pop() if tree.body and isinstance(tree.body[-1], ast.Expr) else None
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(tree, "<exec>", "exec"), self.ns)
            value = eval(compile(ast.Expression(last.value), "<exec>", "eval"), self.ns) if last else None
        return {"value": log.jsonable(value), "stdout": out.getvalue()}

    def cmd_set(self, a):
        return params.write(a)

    def cmd_get(self, a):
        return params.read(a.get("names") or None)

    def cmd_snapshot(self, a):
        k = str(a.get("k", "0"))
        path = protocol.snapshot_path(self.name, k)
        t = time.perf_counter()
        with cache.atomic(path) as tmp:
            bpy.ops.wm.save_as_mainfile(filepath=tmp, copy=True, compress=False)
        return {"k": k, "path": rel(path), "bytes": os.path.getsize(path), "s": round(time.perf_counter() - t, 4)}

    def cmd_restore(self, a):
        k = str(a.get("k", "0"))
        path = protocol.snapshot_path(self.name, k)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"no snapshot {k!r} of server {self.name}")
        t = time.perf_counter()
        bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)
        self.invalidate()
        return {"k": k, "objects": len(bpy.data.objects), "s": round(time.perf_counter() - t, 4)}

    def cmd_save(self, a):
        """cache.save_part from the live session. The session may have drifted from any build's inputs
        (set, exec), so the cache is marked manual and never counts as fresh."""
        part = self.part_module(str(a["part"]).zfill(2)).PART
        rec = cache.save_part(part, manual=True)
        return {"blend": rel(cache.part_path(part)), "bytes": rec["bytes"], "objects": len(rec["objects"])}

    def cmd_load(self, a):
        pid = str(a["part"]).zfill(2)
        link = bool(a.get("link"))
        coll = cache.load_part(pid if link else self.part_module(pid).PART, link=link)
        self.invalidate()
        return {"collection": coll.name, "objects": len(coll.all_objects), "linked": coll.library is not None}

    def cmd_build(self, a):
        """The part's build() in this session through cli.run, as its command line would (§4.4)."""
        pid = str(a["part"]).zfill(2)
        reloaded = self.reloader.refresh()
        mod = self.part_module(pid, force=bool(reloaded))
        argv = ["--json"]
        for flag in ("rebuild", "check", "render", "from_cache"):
            if a.get(flag):
                argv.append("--" + flag.replace("_", "-"))
        for opt in ("stage", "seed", "proxy", "quality", "views"):
            if a.get(opt) not in (None, ""):
                argv += ["--" + opt, str(a[opt])]
        extra = dict(params.constants(pid), **(a.get("params") or {}))
        if extra:
            argv += ["--params", json.dumps(extra)]
        res = cli.run(mod.PART, mod.build, getattr(mod, "measure", None), argv)
        self.builds += 1
        replace.purge()
        self.invalidate()
        res.update(reloaded=reloaded, restart_advised=self.restart_advised())
        return res

    def cmd_render(self, a):
        """With a preset: spec 17's harness, scripts/eval/render.py render_preset() (the equivalent crop
        camera, the tier, a JSON sidecar). Without one, and for the warm-up frame: a Workbench form
        render of the scene camera as it stands, to `out`."""
        if a.get("preset") and not a.get("warm"):
            if not os.path.isfile(env.path("scripts", "eval", "render.py")):
                raise FileNotFoundError("a preset render needs scripts/eval/render.py (spec 17), not written yet")
            self.reloader.refresh()
            harness = importlib.import_module("eval.render")  # import_module: `import eval` would shadow eval()
            kw = {"tier": a.get("tier", "form"), "aa": a.get("aa", "8")}
            if a.get("out"):
                out = a["out"] if os.path.isabs(a["out"]) else env.path(a["out"])
                kw.update(out_dir=os.path.dirname(out), stem=os.path.splitext(os.path.basename(out))[0])
            t = time.perf_counter()
            side = harness.render_preset(a["preset"], **kw)
            return {"engine": "eval.render", "s": round(time.perf_counter() - t, 4), "sidecar": side}
        out = a.get("out") or os.path.join("renders", "server", f"{self.name}.png")
        out = out if os.path.isabs(out) else env.path(out)
        if a.get("warm"):
            out = os.path.join(protocol.SERVER_DIR, f"{self.name}_warm.png")
        size = a.get("size") or ([64, 64] if a.get("warm") else None)
        sc, temp = bpy.context.scene, None
        if a.get("warm") and sc.camera is None:  # a blend without a camera still warms up
            temp = bpy.data.objects.new("Server.WarmCam", bpy.data.cameras.new("Server.WarmCam"))
            sc.collection.objects.link(temp)
            sc.camera = temp
        try:
            res = workbench(out, size, a.get("aa", "8"))
        finally:
            if temp is not None:
                data = temp.data
                bpy.data.objects.remove(temp)
                bpy.data.cameras.remove(data)
        return dict(res, engine="workbench", out=rel(out))

    def cmd_selftest(self, a):
        """Every lib module's selftest() in this session (bl.py selftest --lib)."""
        self.reloader.refresh()
        lib_dir = os.path.join(SCRIPTS, "lib")
        names = a.get("modules") or sorted(f[:-3] for f in os.listdir(lib_dir)
                                           if f.endswith(".py") and f != "__init__.py")
        out = {}
        for n in names:
            t = time.perf_counter()
            try:
                fn = getattr(importlib.import_module(f"lib.{n}"), "selftest", None)
                if fn is None:
                    raise AttributeError(f"lib/{n}.py has no selftest() (spec 18 §4.3 asks every module for one)")
                out[n] = {"ok": True, "result": log.jsonable(fn())}
            except Exception as e:
                out[n] = {"ok": False, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc(limit=-6)}
            out[n]["s"] = round(time.perf_counter() - t, 3)
        return out

    # ------------------------------------------------------------------ measurement (spec 18 §4.8.1, §4.8.4-6)

    def _part_measure(self, pid, extra=None):
        """A part's measure() on the session as it stands, in the §4.8.4 envelope; the context is the part's
        last run in this session, else a fresh one from its params.json."""
        pid = str(pid).zfill(2)
        mod = self.part_module(pid)
        fn = getattr(mod, "measure", None)
        if fn is None:
            raise AttributeError(f"part {pid} ({mod.__file__}) defines no measure()")
        ctx = cli.LAST.get(pid)
        if ctx is None or extra:
            ctx = cli.Context(mod.PART, cli.parse(["--params", json.dumps(extra)] if extra else []))
        t = time.perf_counter()
        metrics = cli.envelopes(mod.PART, fn(ctx, ctx.args))
        failed = [m["metric"] for m in metrics if m.get("pass") is False]
        return {"part": pid, "metrics": metrics, "failed": failed, "pass": not failed,
                "passed": f"{sum(1 for m in metrics if m.get('pass'))}/{len(metrics)}",
                "ms": round((time.perf_counter() - t) * 1e3, 2)}

    def cmd_measure(self, a):
        """A part's measure() ({"part", "params"}), one lib/measure.py primitive ({"fn", "args"}, objects by
        name) or several ({"calls": [{"fn", "args"}, ...]}, sharing one mesh read per object)."""
        self.refresh_code()
        if "part" in a:
            return self._part_measure(a["part"], a.get("params"))
        if "calls" in a:
            reads = {}
            return [measure.call(c["fn"], c.get("args"), reads) for c in a["calls"]]
        if "fn" not in a:
            raise KeyError(f"measure takes part, fn (with args) or calls; the primitives are {', '.join(measure.PRIMITIVES)}")
        return measure.call(a["fn"], a.get("args"))

    def cmd_silhouette(self, a):
        """The objects' mask through a preset (default: what renders) and its IoU against the preset's
        reference mask: {preset, objects, method, scale, out, diff, band, declared, view}."""
        self.refresh_code()
        if not a.get("preset"):
            raise KeyError("silhouette needs a preset (ref.soldier_full, ref.head_face, ...)")
        return log.jsonable(measure.silhouette_report(**{k: v for k, v in a.items() if k in SILHOUETTE_ARGS}))

    def _metrics(self, specs, reads):
        out = {}
        for j, s in enumerate(specs):
            name = s.get("name") or (f"p{s['part']}" if "part" in s else f"{s.get('fn')}{j}")
            if "part" in s:
                r = self._part_measure(s["part"], s.get("params"))
                out[name] = r["passed"]
                out.update({f"{name}.{m['metric']}": m["value"] for m in r["metrics"]})
            else:
                out[name] = measure.pick(measure.call(s["fn"], s.get("args"), reads), s.get("metric"))
        return out

    def cmd_variants(self, a):
        """For each variant: set it, measure, optionally render, then put the session back (§4.8.1).

        {base: {name: value}, list: [{name: value}, ...] | grid: {name: [values]}, delta: values are added to
        the base, measure: [{fn, args, metric, name} | {part}], objective: terms (measure.Objective),
        render: {preset, tier (form), aa (FXAA)}, run, out (folder)}. Every variant is checked against its
        parameters' bounds before anything changes. With a render, the run's JSON for sheet.py is written
        beside the images: {preset, variants: [{image, params (the deltas), metrics, objective}]}."""
        self.refresh_code()
        harness, cam = importlib.import_module("eval.render"), importlib.import_module("eval.camera")
        if a.get("grid"):
            names = list(a["grid"])
            variants = [dict(zip(names, combo)) for combo in itertools.product(*(a["grid"][n] for n in names))]
        else:
            variants = [dict(v) for v in a.get("list") or []]
        if not variants:
            raise ValueError("variants needs a non-empty list or grid")
        touched = list(dict.fromkeys(list(a.get("base") or {}) + [k for v in variants for k in v]))
        snap = params.snapshot(touched)
        start = dict(snap, **(a.get("base") or {}))
        if a.get("delta"):
            variants = [{k: (start[k] + v if not isinstance(v, list) else [s + d for s, d in zip(start[k], v)])
                         for k, v in var.items()} for var in variants]
        for i, var in enumerate(variants):
            for k, v in dict(start, **var).items():
                p = params.lookup(k)
                comps = v if isinstance(v, list) else [v]
                if any((p.lo is not None and c < p.lo) or (p.hi is not None and c > p.hi) for c in comps):
                    raise ValueError(f"variant {i}: {k} = {v} is outside [{p.lo}, {p.hi}]")
        specs = list(a.get("measure") or [])
        objective = measure.Objective(a["objective"]) if a.get("objective") else None
        rnd = a.get("render") or None
        preset = (rnd or {}).get("preset") or a.get("preset")
        run = a.get("run") or time.strftime("variants_%Y%m%d_%H%M%S")
        owner = a.get("part") or (measure.preset_of(preset).get("owner") if preset else None) or "18"
        out_dir = env.path(a["out"]) if a.get("out") else os.path.join(cam.part_dir(owner), "variants")
        records, t0 = [], time.perf_counter()
        with params.keep_macro_targets(), self._restoring(snap):
            for i, var in enumerate(variants):
                t = time.perf_counter()
                values = dict(start, **var)
                params.write(values)
                reads = {}
                metrics = self._metrics(specs, reads)
                f = objective() if objective else None
                image = None
                if rnd:
                    side = harness.render_preset(preset, tier=rnd.get("tier", "form"), out_dir=out_dir,
                                                 stem=f"{run}_v{i:02d}", aa=rnd.get("aa", "FXAA"))
                    image = side["outputs"]["png"]
                delta = {k: (round(values[k] - snap[k], 9) if isinstance(values[k], (int, float)) else values[k])
                         for k in touched if values[k] != snap[k]}
                records.append({"i": i, "values": {k: values[k] for k in touched}, "params": delta,
                                "metrics": metrics, "objective": f["f"] if f else None,
                                "objective_values": f["values"] if f else None, "image": image,
                                "ms": round((time.perf_counter() - t) * 1e3, 1)})
                self.progress({"variant": i + 1, "of": len(variants), "objective": records[-1]["objective"]})
        out = {"run": run, "preset": preset, "variants": records, "restored": snap, "json": None,
               "s": round(time.perf_counter() - t0, 3)}
        if rnd:
            path = os.path.join(out_dir, f"{run}.json")
            sheet = {"preset": preset, "run": run, "variants": [
                {"image": os.path.relpath(env.path(r["image"]), out_dir).replace(os.sep, "/"), "params": r["params"],
                 "metrics": {k: v for k, v in r["metrics"].items() if isinstance(v, (int, float))},
                 "objective": r["objective"]} for r in records]}
            cache.write_json(path, sheet)
            out["json"] = rel(path)
        return out

    def _bounds(self, a, names, need):
        lo, hi = [], []
        given = a["params"] if isinstance(a.get("params"), dict) else {}
        for n in names:
            b = (a.get("bounds") or {}).get(n) or given.get(n)
            p = params.lookup(n)
            lo_n, hi_n = (b[0], b[1]) if b else (p.lo, p.hi)
            if (lo_n is None or hi_n is None) and need:
                raise ValueError(f"{n} has no bounds: register them or pass bounds {{{n!r}: [lo, hi]}}")
            if b and ((p.lo is not None and lo_n < p.lo) or (p.hi is not None and hi_n > p.hi)):
                raise ValueError(f"bounds {b} for {n} leave its registered range [{p.lo}, {p.hi}]")
            lo.append(-math.inf if lo_n is None else float(lo_n))
            hi.append(math.inf if hi_n is None else float(hi_n))
        return lo, hi

    def cmd_optimise(self, a):
        """An optimiser of lib/optim.py on registered parameters against a term objective (§4.8.5).

        {method: cmaes | cd | lm | lsq, params: [names] | {name: [lo, hi]}, bounds, objective (terms, see
        measure.Objective), budget, seed, sigma0, x0: {name: value}, ftarget, tol, fd_step, clamp, run,
        part, progress (a line every n evaluations), restore}. Every evaluation goes to
        renders/<part>/opt/<run>.jsonl; the session is left at the best point found (restore: at the
        start), confirmed by one more evaluation. lsq is the linear target model's solve (§4.8.6), see
        _lsq. A result on a bound is reported in at_bound, never hidden."""
        self.refresh_code()
        method = a.get("method", "cmaes")
        if method == "lsq":
            return self._lsq(a)
        if method not in ("cmaes", "cd", "lm"):
            raise ValueError(f"method {method!r}: cmaes, cd, lm or lsq")
        names = list(a["params"])
        lo, hi = self._bounds(a, names, need=method != "lm")
        objective = measure.Objective(a["objective"])
        start = params.snapshot(names)
        if any(not isinstance(v, (int, float)) for v in start.values()):
            raise ValueError("optimise works on scalar parameters (address one axis: xf:Obj:location:2)")
        x0 = [float((a.get("x0") or {}).get(n, start[n])) for n in names]
        cam = importlib.import_module("eval.camera")
        run = a.get("run") or time.strftime(f"{method}_%Y%m%d_%H%M%S")
        path = os.path.join(cam.part_dir(a.get("part") or "18"), "opt", f"{run}.jsonl")
        every = int(a.get("progress") or 0)
        state = {"n": 0, "best": math.inf, "t0": time.perf_counter()}
        if os.path.exists(path):
            os.remove(path)

        def evaluate(x):
            values = dict(zip(names, (float(v) for v in x)))
            params.write(values, bounds=False)
            r = objective()
            state["n"] += 1
            state["best"] = min(state["best"], r["f"])
            log.jsonl(path, i=state["n"], x=values, f=r["f"], values=r["values"])
            if every and state["n"] % every == 0:
                self.progress({"nfev": state["n"], "f": r["f"], "best": state["best"],
                               "s": round(time.perf_counter() - state["t0"], 2)})
            return r

        budget = int(a.get("budget", 2000 if method != "lm" else 1000))
        with params.keep_macro_targets():
            with self._restoring(start, always=bool(a.get("restore"))):
                f0 = evaluate(x0)["f"]
                if method == "cd":
                    res = optim.coordinate_descent(lambda x: evaluate(x)["f"], x0, lo, hi, tol=a.get("tol", 1e-4),
                                                   budget=budget)
                elif method == "cmaes":
                    res = optim.cmaes(lambda x: evaluate(x)["f"], x0, lo, hi, sigma0=a.get("sigma0", 0.25),
                                      seed=a.get("seed", 17), budget=budget, ftarget=a.get("ftarget", -math.inf))
                else:
                    res = optim.levenberg_marquardt(lambda x: evaluate(x)["residuals"], x0, lo=lo, hi=hi,
                                                    max_iter=a.get("max_iter", 30), fd_step=a.get("fd_step", 0.1),
                                                    clamp=a.get("clamp", 0.15), budget=budget)
            best = dict(zip(names, (float(v) for v in res["x"])))
            out = {"method": method, "x": best, "start": start, "f_start": f0, "f": res["f"], "nfev": state["n"],
                   "nit": res["nit"], "converged": res["converged"], "message": res["message"],
                   "at_bound": [names[i] for i in res["at_bound"]], "log": rel(path),
                   "s": round(time.perf_counter() - state["t0"], 3)}
            if not a.get("restore"):
                out["f_confirm"] = evaluate(res["x"])["f"]
        self.progress({"done": True, "nfev": state["n"], "f": res["f"]})
        return out

    @contextlib.contextmanager
    def _restoring(self, snap, always=True):
        """Put the parameters back afterwards: always, or only when the work inside fails."""
        ok = False
        try:
            yield
            ok = True
        finally:
            if always or not ok:
                params.restore(snap)

    def _lsq(self, a):
        """§4.8.6's solve: shape-key weights by bounded linear least squares against landmark targets through
        the linear target model, then set and confirmed by the depsgraph. {object, keys (default: the
        non-macro keys), landmarks (a measure.landmarks spec), targets ({name: [x, y, z] mm}), weights
        ({name: w}, default 1), lam (toward w0), w0 ("current" or a list), bounds ([lo, hi] or {key: [lo,
        hi]}, default [-1, 1]), restore}."""
        t0 = time.perf_counter()
        ob, keys = a["object"], a.get("keys")
        mkey = (ob, tuple(keys) if keys else None)
        model = self.models.get(mkey)
        if model is None:
            model = self.models[mkey] = linmodel.LinearModel(ob, keys)
        else:
            model.refresh()
        rows = model.rows(a["landmarks"])
        targets = a["targets"]
        missing = [n for n in rows.names if n not in targets]
        if missing:
            raise KeyError(f"no target for landmarks {missing[:5]}")
        b = np.array([[float(c) for c in targets[n]] for n in rows.names]).reshape(-1) - rows.p0_flat
        wts = a.get("weights") or {}
        W = [float(wts.get(n, 1.0)) if isinstance(wts, dict) else float(wts) for n in rows.names for _ in range(3)]
        bnd = a.get("bounds", [-1.0, 1.0])
        lo = [(bnd.get(k) or [-1.0, 1.0])[0] if isinstance(bnd, dict) else bnd[0] for k in model.keys]
        hi = [(bnd.get(k) or [-1.0, 1.0])[1] if isinstance(bnd, dict) else bnd[1] for k in model.keys]
        w_start = model.values()
        w0 = w_start if a.get("w0", "current") == "current" else a["w0"]
        res = optim.bounded_lsq(rows.J, b, lo, hi, weights=W, lam=float(a.get("lam", 0.0)), w0=w0)
        model.apply(res["x"])
        actual = measure.landmarks(ob, a["landmarks"])
        actual = actual if isinstance(actual, dict) else dict(zip(rows.names, actual))
        pred = rows.predict(res["x"])
        err = max(float(np.abs(pred[i] - actual[n]).max()) for i, n in enumerate(rows.names))
        miss = [float(np.linalg.norm(np.asarray(actual[n]) - np.asarray(targets[n], float))) for n in rows.names]
        out = {"method": "lsq", "x": dict(zip(model.keys, res["x"].tolist())), "f": res["f"], "kkt": res["kkt"],
               "at_bound": [model.keys[i] for i in res["at_bound"]], "confirm_max_err_mm": err,
               "rms_mm": float(sum(m * m for m in miss) / len(miss)) ** 0.5, "max_miss_mm": max(miss),
               "keys": len(model.keys), "landmarks": len(rows.names), "ms": round((time.perf_counter() - t0) * 1e3, 2)}
        if a.get("restore"):
            model.apply(w_start)
        return out

    def cmd_shutdown(self, a):
        self.done = True
        return {"bye": self.name, "requests": self.requests, "builds": self.builds}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="blender_server.py")
    ap.add_argument("--name", default="a")
    ap.add_argument("--port", type=int, default=0, help="0: any free port, printed on the LISTENING line")
    ap.add_argument("--parts", default="", help="part ids to append from their caches at start")
    a = ap.parse_args(argv)
    token = os.environ.pop(protocol.TOKEN_ENV, "")  # popped: processes the session starts need not see it
    if not token:
        print(f"blender_server: {protocol.TOKEN_ENV} is not set; start the server with scripts/tools/bl.py start",
              flush=True)
        sys.exit(4)
    server = Server(a.name, a.port, token)
    for pid in [p for p in a.parts.split(",") if p]:
        try:
            print(f"[server] loaded part {pid}: {server.cmd_load({'part': pid})}", flush=True)
        except Exception as e:
            print(f"[server] could not load part {pid}: {e}", flush=True)
    server.serve()


if __name__ == "__main__":
    main()
