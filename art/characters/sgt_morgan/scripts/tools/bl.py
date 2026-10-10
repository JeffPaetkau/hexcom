"""Client and command line for the persistent Blender server (spec 18 §4.8.1).

  python -I scripts/tools/bl.py start [--blend FILE] [--parts 05,15] [--factory-startup] [--no-warm]
  python -I scripts/tools/bl.py stop | shutdown | ping | status
  python -I scripts/tools/bl.py exec "len(bpy.data.objects)"
  python -I scripts/tools/bl.py set key:Body.Mesh:jaw=0.3 xf:Boot.L:location:2=0.01
  python -I scripts/tools/bl.py get [NAME ...]
  python -I scripts/tools/bl.py snapshot [K] | restore [K] | save PART | load PART [--link]
  python -I scripts/tools/bl.py build PART [--stage S] [--params JSON] [--rebuild] [--check] [--proxy IDS]
  python -I scripts/tools/bl.py render [--out PNG] [--preset P] [--tier form] [--size W H] [--aa 8|FXAA]
  python -I scripts/tools/bl.py measure girth ob=Body.Mesh plane=700 around=[130,-38,700] [kind=loop]
  python -I scripts/tools/bl.py measure --part 06 | --calls '[{"fn": "bbox", "args": {"ob": "Body.Mesh"}}]'
  python -I scripts/tools/bl.py silhouette --preset ref.soldier_full [--objects Body.*,Rifle.*] [--out PNG]
                                           [--diff PNG] [--method span|splat] [--scale S] [--band 3]
  python -I scripts/tools/bl.py variants SPEC.json | '{"grid": {...}, "measure": [...], "render": {...}}'
  python -I scripts/tools/bl.py optimise SPEC.json | '{"method": "cmaes", "params": {...}, "objective": [...]}'
  python -I scripts/tools/bl.py selftest [--lib] [--modules measure,optim] [--bench] [--keep]

Every command takes --name (default $SGT_SERVER, else "a": one server per agent, a and b). Standard
library only, so it runs on the image-tools Python, the cloud's python3 or Blender's own. Results print
as JSON; the exit status is 0, 1 for an error, or for `build` the part's own exit code (§4.4), and for
`measure --part` 2 when a tolerance fails. The measurement primitives and their arguments are
scripts/lib/measure.py's; variants and optimise take a JSON object (inline or a file) as the server's
commands of the same names document them, and print the server's progress lines to stderr.
"""
import argparse
import json
import os
import shutil
import signal
import socket
import struct
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/; -I leaves it out
from lib import cache, env  # noqa: E402
from server import protocol  # noqa: E402

SERVER_PY = env.path("scripts", "server", "blender_server.py")
# errors that are answers rather than bugs: printed without the server's traceback
EXPECTED = ("NotImplementedError", "MissingDependency", "PermissionError", "FileNotFoundError", "LookupError")


class ServerError(Exception):
    pass


def rel(path):
    return os.path.relpath(path, env.PROJECT_DIR).replace(os.sep, "/")


# --------------------------------------------------------------------------- processes

def _win_process(pid, access=0x1000):  # PROCESS_QUERY_LIMITED_INFORMATION
    import ctypes
    from ctypes import wintypes as wt
    k32 = ctypes.WinDLL("kernel32")
    k32.OpenProcess.restype = wt.HANDLE
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    return k32, k32.OpenProcess(access, False, pid)


def alive(pid):
    """Is the process running? (os.kill(pid, 0) would terminate it on Windows, so ask the kernel.)"""
    if not pid:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes as wt
        k32, h = _win_process(pid)
        if not h:
            return False
        try:
            code = wt.DWORD()
            k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
            return bool(k32.GetExitCodeProcess(h, ctypes.byref(code))) and code.value == 259  # STILL_ACTIVE
        finally:
            k32.CloseHandle(h)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def image_name(pid):
    """The process's executable (Windows) or command line (Linux); '' when it cannot be read."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes as wt
        k32, h = _win_process(pid)
        if not h:
            return ""
        try:
            buf, size = ctypes.create_unicode_buffer(1024), wt.DWORD(1024)
            k32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
            return buf.value if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)) else ""
        finally:
            k32.CloseHandle(h)
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().replace(b"\0", b" ").decode(errors="replace")
    except OSError:
        return ""


def kill(pid):
    """Terminate a server process, but only if the pid still belongs to a Blender (pids are reused)."""
    name = image_name(pid)
    if name and "blender" not in name.lower():
        return False
    try:
        os.kill(pid, signal.SIGTERM)  # TerminateProcess on Windows
    except OSError:
        return False
    if os.name != "nt":
        t0 = time.time()
        while alive(pid) and time.time() - t0 < 3:
            time.sleep(0.05)
        if alive(pid):
            os.kill(pid, signal.SIGKILL)
    return True


def _spawn(argv, environ, logf):
    kw = dict(stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=environ, cwd=env.PROJECT_DIR)
    if os.name != "nt":
        return subprocess.Popen(argv, start_new_session=True, **kw)  # outlives this command and its terminal
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    try:  # also leave any job object this command runs in, if the job allows it
        return subprocess.Popen(argv, creationflags=flags | 0x01000000, **kw)  # CREATE_BREAKAWAY_FROM_JOB
    except OSError:
        return subprocess.Popen(argv, creationflags=flags, **kw)


def _read(path):
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def tail(path, n=25):
    return "\n".join(_read(path).splitlines()[-n:])


# --------------------------------------------------------------------------- the client

class Client:
    """One connection to a named server; call() sends a request and waits for its reply."""

    def __init__(self, name, timeout=900.0, on_progress=None):
        self.name = name
        self.state = cache.read_json(protocol.state_path(name))
        if not self.state:
            raise ServerError(f"no server {name!r} is running (python -I scripts/tools/bl.py start --name {name})")
        try:
            self.sock = socket.create_connection((protocol.HOST, self.state["port"]), timeout=10)
        except OSError as e:
            raise ServerError(f"server {name!r} does not answer on port {self.state['port']}: {e}") from None
        self.sock.settimeout(timeout)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.lines, self.backlog, self.n = protocol.Lines(), [], 0
        self.on_progress = on_progress  # called with each progress line of the request in hand

    def call(self, cmd, args=None, token=None):
        """The raw reply: {id, ok, result | error, ms}. Progress lines ({id, progress}, no "ok") of a long
        command go to on_progress on the way."""
        self.n += 1
        self.sock.sendall(protocol.encode(protocol.request(self.n, token or self.state["token"], cmd, args)))
        while True:
            while self.backlog:
                msg = protocol.decode(self.backlog.pop(0))
                if msg.get("id") != self.n:
                    continue
                if "ok" in msg:
                    return msg
                if self.on_progress is not None and "progress" in msg:
                    self.on_progress(msg["progress"])
            data = self.sock.recv(1 << 16)
            if not data:
                raise ServerError(f"server {self.name!r} closed the connection")
            self.backlog += self.lines.feed(data)

    def result(self, cmd, args=None):
        msg = self.call(cmd, args)
        if not msg["ok"]:
            expected = msg["error"].split(":")[0] in EXPECTED
            raise ServerError(msg["error"] + ("" if expected or not msg.get("trace") else f"\n{msg['trace']}"))
        return msg["result"]

    def close(self):
        self.sock.close()


def start(name, blend=None, parts="", factory=False, warm=True, timeout=180.0):
    """Launch a server, wait for its LISTENING line, render the warm-up frame; returns its state."""
    st = cache.read_json(protocol.state_path(name))
    if st and alive(st.get("pid")):
        try:
            c = Client(name, timeout=10)
            c.result("ping")
            c.close()
            return dict(st, already_running=True)
        except (OSError, ServerError) as e:
            raise ServerError(f"server {name!r} (pid {st['pid']}) runs but does not answer ({e}); "
                              f"bl.py stop --name {name}") from None
    os.makedirs(protocol.SERVER_DIR, exist_ok=True)
    args = (["-b"] + ([os.path.abspath(blend)] if blend else []) + (["--factory-startup"] if factory else [])
            + ["--python", SERVER_PY, "--", "--name", name, "--port", "0"] + (["--parts", parts] if parts else []))
    argv, environ = env.blender_cmd(args)
    if not (os.path.isfile(argv[0]) or shutil.which(argv[0])):
        raise ServerError(f"Blender not found ({argv[0]}): run scripts/setup_session.sh or set SGT_BLENDER_EXE")
    import secrets
    token = secrets.token_hex(16)
    environ[protocol.TOKEN_ENV] = token
    log_path = protocol.log_path(name)
    if os.path.exists(protocol.events_path(name)):  # one server's lifetime per log, like its .log
        os.remove(protocol.events_path(name))
    t0 = time.perf_counter()
    with open(log_path, "wb") as logf:
        proc = _spawn(argv, environ, logf)
    while True:
        port = protocol.listening_port(_read(log_path))
        if port:
            break
        if proc.poll() is not None:
            raise ServerError(f"the server exited ({proc.returncode}) before listening; "
                              f"{rel(log_path)}:\n{tail(log_path)}")
        if time.perf_counter() - t0 > timeout:
            kill(proc.pid)
            raise ServerError(f"no LISTENING line in {timeout:.0f} s; {rel(log_path)}:\n{tail(log_path)}")
        time.sleep(0.01)
    st = {"name": name, "pid": proc.pid, "port": port, "token": token, "started": time.strftime("%Y-%m-%d %H:%M:%S"),
          "blend": rel(os.path.abspath(blend)) if blend else None, "log": rel(log_path),
          "listening_s": round(time.perf_counter() - t0, 3)}
    cache.write_json(protocol.state_path(name), st)
    if warm:  # the first render in a process compiles shaders (4-8 s on the cloud CPU); pay it now
        t = time.perf_counter()
        c = Client(name)
        r = c.result("render", {"warm": True})
        c.close()
        st.update(warm_s=round(time.perf_counter() - t, 3), warm_render_s=r["s"])
        cache.write_json(protocol.state_path(name), st)
    return st


def stop(name, timeout=20.0):
    """Ask the server to shut down; kill it if it will not; remove its state file."""
    path = protocol.state_path(name)
    st = cache.read_json(path)
    if not st:
        return {"name": name, "stopped": False, "note": "no state file: not running"}
    pid, how, t0 = st.get("pid"), "shutdown", time.perf_counter()
    try:
        c = Client(name, timeout=timeout)
        c.result("shutdown")
        c.close()
    except (OSError, ServerError):
        how = "no answer"
    while alive(pid) and time.perf_counter() - t0 < timeout:
        time.sleep(0.02)
    if alive(pid):
        how = "killed" if kill(pid) else "refused to kill: the pid is no longer a Blender"
    if os.path.exists(path):
        os.remove(path)
    return {"name": name, "pid": pid, "stopped": not alive(pid), "how": how, "s": round(time.perf_counter() - t0, 3)}


# --------------------------------------------------------------------------- self-test

def png_size(path):
    try:
        with open(path, "rb") as f:
            head = f.read(24)
    except OSError:
        return None
    return list(struct.unpack(">II", head[16:24])) if head[:8] == b"\x89PNG\r\n\x1a\n" else None


def _ms(fn):
    t = time.perf_counter()
    out = fn()
    return (time.perf_counter() - t) * 1e3, out


# the selftest's own cube and camera (Blender's default framing), whatever startup file the session has
_SELFTEST_SCENE = """
import math
bpy.ops.mesh.primitive_cube_add(size=2.0)
cube = bpy.context.active_object
cube.name = cube.data.name = "Selftest.Cube"
cube.shape_key_add(name="Basis")
cube.shape_key_add(name="Selftest.Key")
cam = bpy.data.objects.new("Selftest.Camera", bpy.data.cameras.new("Selftest.Camera"))
bpy.context.scene.collection.objects.link(cam)
cam.location, cam.rotation_euler = (7.36, -6.93, 4.96), (math.radians(63.6), 0.0, math.radians(46.7))
bpy.context.scene.camera = cam
"""

# a shape key that lifts the cube 1 m, for the linear-model solve through the server
_SELFTEST_KEY = """
kb = bpy.data.objects["Selftest.Cube"].shape_key_add(name="Selftest.Up", from_mix=False)
for p in kb.data:
    p.co.z += 1.0
"""

# the cloud probe's framing (spec 18 §1.3, §3.2): the hero camera and two equivalent crop cameras
_BENCH_SETUP = """
import numpy as np
human = bpy.data.objects["Human"]
cam = bpy.context.scene.camera
def crop(x0, y0, x1, y1, s):
    w, h = x1 - x0, y1 - y0
    cam.data.sensor_width, cam.data.sensor_fit = 36.0, "HORIZONTAL"
    cam.data.lens = 46.0 * 1672 / w
    cam.data.shift_x = ((x0 + x1) / 2 - 836) / w
    cam.data.shift_y = (470.5 - (y0 + y1) / 2) / w
    return [int(w * s), int(h * s)]
LM = None
def landmarks():
    global LM
    dg = bpy.context.evaluated_depsgraph_get()
    ev = human.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    LM = np.linspace(0, len(co) - 1, 200).astype(int) if LM is None else LM
    return float(co[LM, 2].max())
[k.name for k in human.data.shape_keys.key_blocks][1:]
"""

_MAKE_HUMAN = """
import bpy, math, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")
from bl_ext.user_default.mpfb.services.humanservice import HumanService
h = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                              feet_on_ground=True, scale=0.1)
h.name = "Human"
cam = bpy.data.objects.new("Scene.Cam.Hero", bpy.data.cameras.new("Scene.Cam.Hero"))
bpy.context.scene.collection.objects.link(cam)
cam.location, cam.rotation_euler = (0.0, -4.5, 0.6), (math.radians(93.9), 0.0, 0.0)
bpy.context.scene.camera = cam
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1], compress=False)
"""


def _bench(report):
    """The cloud probe's measurements (spec 18 §3.2) against an MPFB human, for comparison."""
    import statistics
    blend = env.path("cache", "selftest", "mpfb_human.blend")
    if not os.path.isfile(blend):
        os.makedirs(os.path.dirname(blend), exist_ok=True)
        argv, environ = env.blender_cmd(["-b", "--python-expr", _MAKE_HUMAN, "--", blend])
        subprocess.run(argv, env=environ, cwd=env.PROJECT_DIR, capture_output=True, timeout=300, check=True)
    name = "bench"
    stop(name)
    st = start(name, blend=blend)
    b = {"listening_s": st["listening_s"], "first_render_s": st["warm_render_s"]}
    c = Client(name)
    try:
        keys = c.result("exec", {"code": _BENCH_SETUP})["value"]
        key = f"key:Human:{keys[0]}"
        lat = [_ms(lambda: c.call("ping"))[0] for _ in range(200)]
        b["ping_ms_median"] = round(statistics.median(lat), 3)
        sets, meas = [], []
        for i in range(30):
            sets.append(_ms(lambda: c.result("set", {key: 0.3 + 0.1 * (i % 3)}))[0])
            meas.append(_ms(lambda: c.result("exec", {"code": "landmarks()"}))[0])
        b["set_key_ms_median"] = round(statistics.median(sets), 3)
        b["measure_200_after_set_ms_median"] = round(statistics.median(meas), 3)
        for label, box, n in (("soldier_x1", (580, 20, 1020, 935, 1), 4), ("head_x5", (715, 30, 885, 200, 5), 3)):
            size = c.result("exec", {"code": f"crop{box}"})["value"]
            out = f"renders/selftest/bench_{label}.png"
            ts = [c.result("render", {"out": out, "size": size, "aa": "FXAA"})["s"] for _ in range(n)]
            b[f"workbench_{label}_fxaa_s"] = ts
            assert png_size(env.path(out)) == size, (out, png_size(env.path(out)))
        b["blend"] = rel(blend)
        b["vertices"] = c.result("exec", {"code": "len(human.data.vertices)"})["value"]
        snap = c.result("snapshot", {"k": "bench"})  # last: a restore leaves the exec names dangling
        b.update(snapshot_s=snap["s"], snapshot_mb=round(snap["bytes"] / 1e6, 1),
                 restore_s=c.result("restore", {"k": "bench"})["s"])
    finally:
        c.close()
        b["stop"] = stop(name)
        if os.path.exists(protocol.snapshot_path(name, "bench")):
            os.remove(protocol.snapshot_path(name, "bench"))
    report["bench"] = b


def selftest(lib=False, bench=False, keep=False, modules=None):
    """Start a server, ping it, set and get, one Workbench render, snapshot and restore, a scratch part's
    builds, the measurement commands, then stop (spec 18 §8.4, run by setup_session.sh --check); --lib
    adds every lib module's selftest() (or the named modules')."""
    import statistics
    name = "selftest"
    report, problems = {}, []

    def check(cond, what):
        if not cond:
            problems.append(what)
        return cond

    stop(name)
    scratch = env.path("cache", "selftest", "server")
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    st = start(name)
    report.update(listening_s=st["listening_s"], warm_s=st["warm_s"], warm_render_s=st["warm_render_s"])
    c = Client(name)
    try:
        lat = [_ms(lambda: c.call("ping")) for _ in range(100)]
        check(all(r["ok"] for _, r in lat), "ping")
        report["ping_ms_median"] = round(statistics.median(ms for ms, _ in lat), 3)
        report["ping_server_ms_median"] = round(statistics.median(r["ms"] for _, r in lat), 4)

        c.result("exec", {"code": _SELFTEST_SCENE})
        key, times = "key:Selftest.Cube:Selftest.Key", []
        for i in range(20):
            v = round(0.1 * (i % 5), 3)
            ms, got = _ms(lambda: (c.result("set", {key: v}), c.result("get", {"names": [key]}))[1])
            times.append(ms)
            check(abs(got[key] - v) < 1e-6, f"set/get round trip {v} -> {got}")
        report["set_get_ms_median"] = round(statistics.median(times), 3)

        out = "renders/selftest/workbench.png"
        if os.path.exists(env.path(out)):
            os.remove(env.path(out))
        r = [c.result("render", {"out": out, "size": [440, 915]}) for _ in range(3)]
        report["workbench_440x915_s"] = [x["s"] for x in r]
        check(png_size(env.path(out)) == [440, 915], f"render wrote {png_size(env.path(out))}")

        z = "xf:Selftest.Cube:location:2"
        c.result("set", {z: 0.0})
        snap = c.result("snapshot", {"k": "t"})
        c.result("set", {z: 1.5})
        rest = c.result("restore", {"k": "t"})
        check(c.result("get", {"names": [z]})[z] == 0.0, "restore")
        report.update(snapshot_s=snap["s"], restore_s=rest["s"])

        # a part built through the server: its cache key, an edited library module reloaded with its
        # importers, an edited part script re-imported, a tolerance failure, save and load
        from lib import cli
        src = os.path.join(scratch, "95_cli_selftest.py")
        with open(src, "w", newline="\n") as f:
            f.write(cli.TEST_PART.format(scripts=env.SCRIPTS_DIR, parts=os.path.join(scratch, "parts"),
                                         script=rel(src)))
        c.result("exec", {"code": f"server.parts_dir = {scratch!r}"})
        b = [c.result("build", {"part": "95"})]
        check(b[0]["status"] == "pass" and b[0]["cache"] == "saved", f"build: {b[0].get('status')} {b[0].get('error')}")
        b.append(c.result("build", {"part": "95"}))
        check(b[1]["cache"] == "fresh" and b[1]["key"] == b[0]["key"], f"second build: cache {b[1]['cache']}")
        os.utime(env.path("scripts", "lib", "naming.py"))  # touched, not changed: reloaded, key unmoved
        with open(src, "a", newline="\n") as f:
            f.write("# edited\n")
        b.append(c.result("build", {"part": "95"}))
        check("lib.naming" in b[2]["reloaded"] and b[2].get("stale") == ["script"] and b[2]["cache"] == "saved",
              f"after edits: reloaded {b[2]['reloaded']}, stale {b[2].get('stale')}, cache {b[2]['cache']}")
        b.append(c.result("build", {"part": "95", "params": {"size_mm": 30}}))
        check(b[3]["exit"] == 2 and b[3]["failed"] == ["size"], f"tolerance build: {b[3]['status']}")
        check(c.result("save", {"part": "95"})["objects"] == 2, "save")
        check(c.result("load", {"part": "95"})["objects"] == 2, "load")
        report["build_s"] = [x["timings"]["total"] for x in b]
        report["reloaded"] = b[2]["reloaded"]

        # the measurement commands on the cube (2 m, centred on the origin): a primitive, the scratch part's
        # measure(), a silhouette, a variant sweep put back afterwards, an optimiser with progress lines
        # and the linear-model solve
        z = "xf:Selftest.Cube:location:2"
        ms, r = _ms(lambda: c.result("measure", {"fn": "bbox", "args": {"ob": "Selftest.Cube"}}))
        check([round(v, 3) for v in r["size"]] == [2000.0] * 3, f"measure bbox: {r}")
        report["measure_bbox_ms"] = round(ms, 2)
        r = c.result("measure", {"part": "95"})
        check(abs(r["metrics"][0]["value"] - 30.0) < 1e-3 and r["pass"] is False, f"measure part 95: {r}")
        ms, r = _ms(lambda: c.result("silhouette", {"preset": "ref.full", "objects": ["Selftest.Cube"]}))
        check(r["size"] == [1672, 941] and r["px"] > 100000, f"silhouette: {r}")
        report["silhouette_full_frame_ms"] = round(ms, 1)
        seen = []
        c.on_progress = seen.append
        r = c.result("variants", {"list": [{z: 0.0}, {z: 0.5}], "progress": 1, "measure": [
            {"fn": "bbox", "args": {"ob": "Selftest.Cube"}, "metric": "min.2", "name": "bottom"}]})
        check([round(v["metrics"]["bottom"], 3) for v in r["variants"]] == [-1000.0, -500.0]
              and c.result("get", {"names": [z]})[z] == 0.0 and len(seen) == 2, f"variants: {r} progress {seen}")
        del seen[:]
        r = c.result("optimise", {"method": "cd", "params": {z: [-1.0, 1.0]}, "run": "selftest", "progress": 5,
                                  "objective": [{"fn": "bbox", "args": {"ob": "Selftest.Cube"}, "metric": "min.2",
                                                 "target": -500.0, "tol": 1.0}]})
        log_file = env.path(r["log"])
        check(abs(r["x"][z] - 0.5) < 1e-3 and r["f_confirm"] < 1e-3 and seen and os.path.isfile(log_file),
              f"optimise: {r} progress {len(seen)}")
        report["optimise_cd_nfev"], report["optimise_cd_s"] = r["nfev"], r["s"]
        c.on_progress = None
        if os.path.exists(log_file):
            os.remove(log_file)
        c.result("set", {z: 0.0})
        c.result("exec", {"code": _SELFTEST_KEY})
        v0 = c.result("measure", {"fn": "landmarks", "args": {"ob": "Selftest.Cube", "spec": {"v0": 0}}})["v0"]
        r = c.result("optimise", {"method": "lsq", "object": "Selftest.Cube", "keys": ["Selftest.Up"],
                                  "landmarks": {"v0": 0}, "targets": {"v0": [v0[0], v0[1], v0[2] + 300.0]},
                                  "bounds": [0.0, 1.0], "restore": True})
        check(abs(r["x"]["Selftest.Up"] - 0.3) < 1e-9 and r["confirm_max_err_mm"] < 1e-3, f"optimise lsq: {r}")
        r = c.call("measure", {"fn": "nonsense"})
        check(not r["ok"] and "no measurement" in r["error"], f"measure of nothing answered {r}")
        r = c.call("ping", token="0" * 32)
        check(not r["ok"] and "bad token" in r["error"], "a wrong token was accepted")
        r = c.call("exec", {"code": "import sys; sys.exit(3)"})
        check(not r["ok"] and c.call("ping")["ok"], "exec'd sys.exit stopped the server")
        status = c.result("status")
        report["rss_mb"] = status["rss_mb"]

        if lib:
            res = c.result("selftest", {"modules": modules} if modules else {})
            report["lib"] = {n: ("ok" if v["ok"] else v["error"]) for n, v in res.items()}
            report["lib_s"] = {n: v["s"] for n, v in res.items()}
            report["lib_results"] = {n: v["result"] for n, v in res.items() if v["ok"] and v.get("result")}
            for n, v in res.items():
                if not check(v["ok"], f"lib.{n}.selftest"):
                    print(f"--- lib.{n} ---\n{v.get('trace') or v['error']}", file=sys.stderr)
    finally:
        c.close()
        if not keep:
            report["stop"] = stop(name)
            check(report["stop"]["stopped"], "stop")
            shutil.rmtree(scratch, ignore_errors=True)
            snap = protocol.snapshot_path(name, "t")
            if os.path.exists(snap):
                os.remove(snap)
    if bench:
        _bench(report)
    report["problems"] = problems
    report["pass"] = not problems
    return report


# --------------------------------------------------------------------------- command line

def _value(text):
    try:
        return json.loads(text)
    except ValueError:
        return text


def _json_arg(text):
    """A JSON value given inline, as a file name, or as @file."""
    path = text[1:] if text.startswith("@") else text
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(text)


def _print_progress(p):
    print("progress " + json.dumps(p, separators=(",", ":")), file=sys.stderr, flush=True)


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--name", default=os.environ.get("SGT_SERVER", "a"), help="server name (a, b)")
    ap = argparse.ArgumentParser(prog="bl.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def cmd(n, **kw):
        return sub.add_parser(n, parents=[common], **kw)

    p = cmd("start")
    p.add_argument("--blend")
    p.add_argument("--parts", default="")
    p.add_argument("--factory-startup", action="store_true", help="no user preferences, so no MPFB; starts faster")
    p.add_argument("--no-warm", action="store_true")
    p.add_argument("--timeout", type=float, default=180.0)
    for n in ("stop", "shutdown", "ping", "status"):
        cmd(n)
    cmd("exec").add_argument("code")
    cmd("set").add_argument("pairs", nargs="+", help="NAME=VALUE; VALUE is JSON (0.3, [0,0,1], true) or text")
    cmd("get").add_argument("names", nargs="*")
    for n in ("snapshot", "restore"):
        cmd(n).add_argument("k", nargs="?", default="0")
    cmd("save").add_argument("part")
    p = cmd("load")
    p.add_argument("part")
    p.add_argument("--link", action="store_true")
    p = cmd("build")
    p.add_argument("part")
    for o in ("--stage", "--params", "--proxy", "--quality", "--views"):
        p.add_argument(o)
    p.add_argument("--seed", type=int)
    for f in ("--rebuild", "--check", "--render", "--from-cache"):
        p.add_argument(f, action="store_true")
    p = cmd("render")
    p.add_argument("--out")
    p.add_argument("--preset")
    p.add_argument("--tier", default="form")
    p.add_argument("--size", nargs=2, type=int, metavar=("W", "H"))
    p.add_argument("--aa", default="8")
    p = cmd("measure")
    p.add_argument("fn", nargs="?", help="a primitive of scripts/lib/measure.py (girth, section, landmarks, "
                                         "project, clearance, stature, bbox, silhouette), or a JSON request")
    p.add_argument("pairs", nargs="*", help="ARG=VALUE; VALUE is JSON (700, [130,-38,700]) or text (object names)")
    p.add_argument("--part", help="the part's own measure() on the session")
    p.add_argument("--params", help="with --part: a JSON object merged over its params.json")
    p.add_argument("--calls", help="several primitives sharing one mesh read: a JSON list of {fn, args}, inline or a file")
    p = cmd("silhouette")
    p.add_argument("--preset", default="ref.soldier_full")
    p.add_argument("--objects", help="object names or patterns, comma-separated (default: what renders)")
    p.add_argument("--method", choices=("span", "splat"), default="span")
    p.add_argument("--scale", type=float, help="override the preset's scale")
    p.add_argument("--out", help="write the mask PNG here")
    p.add_argument("--diff", help="write the silhouette map (p18.V2 colours) here")
    p.add_argument("--band", type=int, default=3, help="the don't-care band around the reference edge, px")
    p.add_argument("--no-declared", action="store_true", help="count the declared differences too")
    for n in ("variants", "optimise"):
        p = cmd(n)
        p.add_argument("spec", help="a JSON object, inline or a file")
        p.add_argument("--quiet", action="store_true", help="no progress lines on stderr")
    p = cmd("selftest")
    p.add_argument("--lib", action="store_true", help="also run every lib module's selftest() in the server")
    p.add_argument("--modules", help="with --lib: only these modules, comma-separated (measure,optim)")
    p.add_argument("--bench", action="store_true", help="also time the cloud probe's operations on an MPFB human")
    p.add_argument("--keep", action="store_true", help="leave the selftest server running")
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # Git Bash and the cloud read UTF-8; a Windows pipe defaults to ANSI
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    try:
        if a.cmd == "start":
            out = start(a.name, a.blend, a.parts, a.factory_startup, not a.no_warm, a.timeout)
            out = {k: v for k, v in out.items() if k != "token"}  # it stays in the state file only
        elif a.cmd in ("stop", "shutdown"):
            out = stop(a.name)
        elif a.cmd == "selftest":
            out = selftest(a.lib, a.bench, a.keep, [m for m in (a.modules or "").split(",") if m] or None)
            print(json.dumps(out, indent=1))
            print("SELFTEST " + ("PASS" if out["pass"] else "FAIL: " + "; ".join(out["problems"])))
            return 0 if out["pass"] else 1
        else:
            args, progress = {}, None
            if a.cmd == "exec":
                args = {"code": a.code}
            elif a.cmd == "set":
                args = {k: _value(v) for k, _, v in (p.partition("=") for p in a.pairs)}
            elif a.cmd == "get":
                args = {"names": a.names}
            elif a.cmd in ("snapshot", "restore"):
                args = {"k": a.k}
            elif a.cmd in ("save", "load", "build"):
                args = {k: v for k, v in vars(a).items()
                        if k not in ("cmd", "name") and v is not None and v is not False}
                if isinstance(args.get("params"), str):
                    args["params"] = json.loads(args["params"])
            elif a.cmd == "render":
                args = {k: v for k, v in vars(a).items() if k not in ("cmd", "name") and v is not None}
            elif a.cmd == "measure":
                if a.part:
                    args = {"part": a.part, **({"params": json.loads(a.params)} if a.params else {})}
                elif a.calls:
                    args = {"calls": _json_arg(a.calls)}
                elif a.fn and a.fn.lstrip().startswith("{"):
                    args = json.loads(a.fn)  # a whole request, as the server takes it
                elif a.fn:
                    args = {"fn": a.fn, "args": {k: _value(v) for k, _, v in (p.partition("=") for p in a.pairs)}}
                else:
                    raise ValueError("measure needs a primitive (girth ob=... plane=...), --part or --calls")
            elif a.cmd == "silhouette":
                args = {"preset": a.preset, "method": a.method, "band": a.band, "declared": not a.no_declared}
                for k in ("scale", "out", "diff"):
                    if getattr(a, k) is not None:
                        args[k] = getattr(a, k)
                if a.objects:
                    args["objects"] = [o for o in a.objects.split(",") if o]
            elif a.cmd in ("variants", "optimise"):
                args = _json_arg(a.spec)
                if not a.quiet:
                    args.setdefault("progress", 1 if a.cmd == "variants" else 10)
                    progress = _print_progress
            c = Client(a.name, on_progress=progress)
            out = c.result(a.cmd, args)
            c.close()
        print(json.dumps(out, indent=1))
        if a.cmd == "measure" and isinstance(out, dict) and "part" in out:
            return 0 if out.get("pass") else 2  # §4.4's exit 2: a tolerance failed
        return out.get("exit", 0) if a.cmd == "build" else 0
    except (ServerError, OSError, ValueError) as e:
        print(f"bl.py {a.cmd}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
