"""Project paths, the recorded environment, the Blender launcher and the Cycles device (spec 18 §4.3).

Imports under Blender's Python and under a plain Python alike; only the Cycles functions need bpy.
`cache/env.json` is written by scripts/setup_session.sh; everything here falls back to sensible
defaults when it is missing, so a part script still runs on a box set up by hand.

Device choice (spec 18 §4.2.4): `SGT_DEVICE` (OPTIX, CUDA, HIP, ONEAPI, METAL or CPU) wins, then the
device the setup probe recorded, then CPU. Results that depend on it (noise, not geometry) record it.
"""
import json
import os
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
CACHE_DIR = os.path.join(PROJECT_DIR, "cache")
RENDERS_DIR = os.path.join(PROJECT_DIR, "renders")
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
REF_DIR = os.path.join(PROJECT_DIR, "ref")
ENV_JSON = os.path.join(CACHE_DIR, "env.json")

# The order in which a probe prefers GPU back ends: OptiX uses the RTX cores, CUDA is the fallback
# on older NVIDIA cards, HIP is AMD, oneAPI Intel Arc, Metal Apple.
GPU_TYPES = ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL")


def bootstrap():
    """Put scripts/ on sys.path so `from lib import ...` works from any entry point."""
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)


def path(*parts):
    return os.path.join(PROJECT_DIR, *parts)


_env = None


def load():
    global _env
    if _env is None:
        try:
            with open(ENV_JSON) as f:
                _env = json.load(f)
        except (OSError, ValueError):
            _env = {}
    return _env


def blender_exe():
    return os.environ.get("SGT_BLENDER_EXE") or load().get("blender") or "blender"


def user_resources():
    return load().get("blender_user_resources") or os.path.join(CACHE_DIR, "blender_user")


def blender_cmd(args):
    """(argv, environ) for a Blender run with the project's user resources (MPFB lives there)."""
    environ = dict(os.environ)
    environ["BLENDER_USER_RESOURCES"] = user_resources()
    return [blender_exe()] + list(args), environ


def run_blender(args, **kw):
    cmd, environ = blender_cmd(args)
    return subprocess.run(cmd, env=environ, cwd=PROJECT_DIR, **kw)


def threads():
    """Render threads: SGT_THREADS, or 0 for Blender's automatic count."""
    try:
        return int(os.environ.get("SGT_THREADS", "0"))
    except ValueError:
        return 0


def device():
    d = (os.environ.get("SGT_DEVICE") or load().get("device") or "CPU").upper()
    return d if d in GPU_TYPES + ("CPU",) else "CPU"


# --------------------------------------------------------------------------- Cycles (needs bpy)

def _cycles_prefs():
    import bpy
    addon = bpy.context.preferences.addons.get("cycles")
    if addon is None:
        bpy.ops.preferences.addon_enable(module="cycles")
        addon = bpy.context.preferences.addons["cycles"]
    return addon.preferences


def gpu_devices(kind):
    """Names of the non-CPU devices Cycles sees for one back end (empty if unsupported)."""
    prefs = _cycles_prefs()
    try:
        prefs.compute_device_type = kind
    except TypeError:  # back end not compiled into this build
        return []
    prefs.refresh_devices()
    return [d.name for d in prefs.get_devices_for_type(kind) if d.type != "CPU"]


def probe_gpu():
    """The best GPU back end on this machine, or 'CPU'."""
    for kind in GPU_TYPES:
        if gpu_devices(kind):
            return kind
    return "CPU"


def use_device(scene=None, kind=None):
    """Point Cycles at the chosen device for this process and scene. Returns what was actually set.

    Enables every GPU of the chosen back end and leaves the CPU out of a GPU render (mixing them
    slows OptiX down on a small card), and moves the OIDN denoiser onto the GPU too: Blender's
    default denoises on the CPU, which on the RTX 3050 was 11 of the 15 s of a 1080p 32-spp render
    (4.0 s with it on the GPU, 2026-10-10). Falls back to CPU, with a message, if the GPU is missing.
    """
    import bpy
    scene = scene or bpy.context.scene
    kind = (kind or device()).upper()
    if kind != "CPU":
        names = gpu_devices(kind)
        if names:
            prefs = _cycles_prefs()
            for d in prefs.get_devices_for_type(kind):
                d.use = d.type != "CPU"
            scene.cycles.device = "GPU"
            scene.cycles.denoising_use_gpu = True
            return kind
        print(f"[env] no {kind} device found; rendering on the CPU", flush=True)
    scene.cycles.device = "CPU"
    scene.cycles.denoising_use_gpu = False
    if threads():
        scene.render.threads_mode = "FIXED"
        scene.render.threads = threads()
    return "CPU"


def selftest():
    assert os.path.isdir(os.path.join(PROJECT_DIR, "spec")), PROJECT_DIR
    cmd, environ = blender_cmd(["--version"])
    assert environ["BLENDER_USER_RESOURCES"]
    assert device() in GPU_TYPES + ("CPU",)
    return {"project_dir": PROJECT_DIR, "blender": cmd[0], "device": device(), "threads": threads()}


if __name__ == "__main__":
    print(json.dumps(selftest(), indent=1))
