"""The persistent Blender server (spec 18 §4.8.1): one warm Blender per agent, driven over JSON lines
on 127.0.0.1 by scripts/tools/bl.py.

  blender -b [file.blend] --python scripts/server/blender_server.py -- --name a --port 0 [--parts 05,15]

Started by `bl.py start`, which passes the token in SGT_SERVER_TOKEN and reads the port from the
`LISTENING <port>` line of the server's log. Single-threaded on purpose: Blender's operators must run
on its main thread, so requests from several connections queue and run one at a time. Before a build
(or a render) every changed module under scripts/ is reloaded in place, with the modules that import
it, so an edited part or library runs without a restart.
"""
import argparse
import ast
import contextlib
import glob
import hmac
import importlib
import importlib.util
import io
import json
import os
import selectors
import socket
import sys
import time
import traceback

import bpy

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from lib import cache, cli, env, log, naming, params, replace  # noqa: E402
from server import protocol  # noqa: E402

RESTART_BUILDS = 200  # §4.8.1 hygiene: a restart is advised after this many builds ...
RESTART_RSS_MB = 5000  # ... or past this resident size (two servers fit in 15 GB with Cycles headroom)
NOT_YET = {"measure": "lib/measure.py, spec 18 §4.8.4", "silhouette": "lib/measure.py silhouette(), §4.8.4",
           "variants": "the variant sweep, §4.8.1 (needs measure)", "optimise": "lib/optim.py, §4.8.5"}


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
        self.ns = {"bpy": bpy, "server": self, "cache": cache, "cli": cli, "env": env, "log": log,
                   "naming": naming, "params": params, "replace": replace}  # exec's namespace, kept

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
                        try:
                            conn.sendall(protocol.encode(self.handle(line)))
                        except OSError:
                            break
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

    def _not_yet(self, cmd):
        raise NotImplementedError(f"{cmd}: not implemented yet ({NOT_YET[cmd]}; a later session)")

    def cmd_measure(self, a):
        self._not_yet("measure")

    def cmd_silhouette(self, a):
        self._not_yet("silhouette")

    def cmd_variants(self, a):
        self._not_yet("variants")

    def cmd_optimise(self, a):
        self._not_yet("optimise")

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
