"""Render harness: a preset at a tier, a PNG and a JSON sidecar (spec 17 §4.9; spec 18 §4.8.2, §4.8.7).

Tiers: `form` is Workbench (matcap clay_studio.exr, single colour 0.8, cavity both at 1.0, no shadows,
anti-aliasing 8, or FXAA for sweeps) on a transparent film with the floor hidden, so its alpha is the
model's silhouette; `look`, `eval`, `cal` and `final` are Cycles on the device lib/env.py chooses
(SGT_DEVICE, else the setup probe: OptiX on Jeff's machine). A Cycles render writes
<stem>_ungraded.png (16-bit RGBA after AgX), <stem>.png (grade.py's display grade composited over the
flat backdrop, the image to compare) and, from eval up, a multilayer <stem>.exr with the passes. Every
render writes <stem>.json: preset, tier, engine, device, samples, seed, seconds, Blender version and
build, git commit, camera.

  python scripts/eval/render.py --preset ref.boots_feet --tier form       (launches Blender on the scene)
  blender -b cache/scene_eval.blend --python scripts/eval/render.py -- --preset ref.full --tier eval
  blender -b cache/scene_eval.blend --python scripts/eval/render.py -- --part 02 --tier form
In a live session (the server): from eval import render; render.render_preset("ref.boots_feet", "form").
Output: renders/<part>/<preset>_<tier>.png, the part from the preset's owner, unless --out.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(HERE))  # scripts/
from lib import env  # noqa: E402
from eval import camera, grade  # noqa: E402

SCENE_BLEND = env.path("cache", "scene_eval.blend")
SEED = 17
# §4.9. percent applies on top of the preset's scale; passes beyond Combined go to the EXR.
TIERS = {
    "form": {"engine": "BLENDER_WORKBENCH", "percent": 100},
    "look": {"engine": "CYCLES", "percent": 50, "samples": 16, "min_samples": 0, "adaptive": 0.05,
             "denoise": "FAST", "prefilter": "ACCURATE", "passes": (), "exr": None},
    "eval": {"engine": "CYCLES", "percent": 100, "samples": 64, "min_samples": 16, "adaptive": 0.02,
             "denoise": "HIGH", "prefilter": "ACCURATE", "passes": ("mist", "z", "crypto", "index"), "exr": "16"},
    "cal": {"engine": "CYCLES", "percent": 100, "samples": 128, "min_samples": 0, "adaptive": None,
            "denoise": None, "passes": ("mist", "z", "crypto", "index", "colour"), "store_denoise": True, "exr": "32"},
    "final": {"engine": "CYCLES", "percent": 200, "samples": 512, "min_samples": 64, "adaptive": 0.005,
              "denoise": "HIGH", "prefilter": "ACCURATE", "passes": ("mist", "z", "crypto", "index"), "exr": "16",
              "clamp_indirect": 10.0},
}
AA = ("OFF", "FXAA", "5", "8", "11", "16", "32")
_device = None  # the Cycles device is chosen once per process


def cycles_common(scene):
    """The settings every Cycles tier shares (§4.9): seed 17, Blackman-Harris 1.5 px, clamps, bounces,
    no caustics, light tree, no path guiding, OIDN on the CPU so a re-render is bit-identical."""
    c = scene.cycles
    c.seed, c.use_animated_seed = SEED, False
    c.pixel_filter_type, c.filter_width = "BLACKMAN_HARRIS", 1.5
    c.sample_clamp_direct, c.sample_clamp_indirect = 0.0, 5.0
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces = 12, 4, 4
    c.transmission_bounces, c.volume_bounces, c.transparent_max_bounces = 12, 0, 32
    c.caustics_reflective = c.caustics_refractive = False
    c.blur_glossy = 1.0
    c.use_light_tree, c.use_guiding = True, False
    c.film_exposure = 1.0
    # the denoiser's device is set with the render device below (env.use_device): on the GPU it
    # is 11 of the 15 s of a 1080p frame when left on the CPU
    c.denoiser, c.denoising_input_passes = "OPENIMAGEDENOISE", "RGB_ALBEDO_NORMAL"


def _set_tier(scene, tier, samples=None, aa="8", form=None):
    """Engine and quality for a tier; returns (engine description, device)."""
    global _device
    T = TIERS[tier]
    r = scene.render
    r.engine = T["engine"]
    if T["engine"] == "BLENDER_WORKBENCH":
        o = form or {}
        sh = scene.display.shading
        sh.light = o.get("light", "MATCAP")
        if sh.light == "MATCAP":
            sh.studio_light = "clay_studio.exr"
        sh.color_type, sh.single_color = "SINGLE", tuple(o.get("color", (0.8, 0.8, 0.8)))
        sh.show_cavity, sh.cavity_type = bool(o.get("cavity", sh.light != "FLAT")), "BOTH"
        sh.cavity_ridge_factor = sh.cavity_valley_factor = 1.0
        sh.curvature_ridge_factor = sh.curvature_valley_factor = 1.0
        sh.show_shadows = sh.show_object_outline = sh.show_xray = sh.use_dof = False
        sh.show_backface_culling = False
        scene.display.render_aa = aa
        return "workbench", None
    c = scene.cycles
    cycles_common(scene)
    c.samples = int(samples or T["samples"])
    c.use_adaptive_sampling = T["adaptive"] is not None
    if c.use_adaptive_sampling:
        c.adaptive_threshold, c.adaptive_min_samples = T["adaptive"], T["min_samples"]
    c.use_denoising = T["denoise"] is not None
    if c.use_denoising:
        c.denoising_quality, c.denoising_prefilter = T["denoise"], T["prefilter"]
    if T.get("clamp_indirect"):
        c.sample_clamp_indirect = T["clamp_indirect"]
    vl, p = scene.view_layers[0], T["passes"]
    vl.use_pass_mist, vl.use_pass_z, vl.use_pass_object_index = "mist" in p, "z" in p, "index" in p
    vl.use_pass_cryptomatte_object = vl.use_pass_cryptomatte_material = "crypto" in p
    vl.pass_cryptomatte_depth = 6
    vl.use_pass_diffuse_color = vl.use_pass_glossy_color = "colour" in p
    vl.cycles.denoising_store_passes = bool(T.get("store_denoise"))
    if _device is None:
        _device = env.use_device(scene)
    else:
        scene.cycles.device = "CPU" if _device == "CPU" else "GPU"
        scene.cycles.denoising_use_gpu = _device != "CPU"
    return "cycles", _device


class _Temporarily:
    """Set attributes for the length of a render and put them back afterwards, errors or not."""

    def __init__(self):
        self.saved = []

    def set(self, obj, **attrs):
        for k, v in attrs.items():
            old = getattr(obj, k)
            if hasattr(old, "__len__") and not isinstance(old, str):
                old = tuple(old)  # bpy arrays are live views; keep the values, not the view
            self.saved.append((obj, k, old))
            setattr(obj, k, v)

    def restore(self):
        for obj, k, v in reversed(self.saved):
            setattr(obj, k, v)
        self.saved = []


def pick_scene(p, tier, force=None):
    import bpy
    want = force or p["scene"]
    hero = bpy.data.scenes.get("Hero") or bpy.context.scene
    if want == "lookdev":
        look = bpy.data.scenes.get("LookDev")
        if look is not None:
            return look, "lookdev"
        if tier == "form":  # Workbench ignores the lights, so the hero scene renders the same form
            return hero, "hero (LookDev not built; form ignores lights)"
        raise LookupError(f"{p['id']} asks for the LookDev scene, which is not built yet (spec 17 §4.8, "
                          "lookdev.py); pass --scene hero to render it under the hero lights")
    return hero, "hero"


def git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=env.PROJECT_DIR, capture_output=True,
                             text=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _save(scene, path, fmt, depth, mode="RGBA"):
    import bpy
    im = scene.render.image_settings
    im.file_format, im.color_mode, im.color_depth = fmt, mode, depth
    if fmt == "PNG":
        im.compression = 15
    else:
        im.exr_codec = "ZIP"
    bpy.data.images["Render Result"].save_render(filepath=path, scene=scene)


def render_preset(preset, tier="form", out_dir=None, stem=None, mode="equiv", aa="8", samples=None,
                  scene_name=None, keep_floor=False, do_grade=True, view=0, registry=None):
    """Render one view of a preset and write its files; returns the sidecar dict."""
    import bpy
    t0 = time.time()
    reg = registry or camera.load_registry()
    p = preset if isinstance(preset, dict) else reg.get(preset)
    if tier == "preset":
        tier = p["render"]["tier"]
    if tier not in TIERS:
        raise ValueError(f"tier {tier!r} not in {tuple(TIERS)}")
    T = TIERS[tier]
    scene, scene_note = pick_scene(p, tier, scene_name)
    r = scene.render
    tmp = _Temporarily()
    try:
        cam_info = camera.apply(p, scene, mode=mode, percent=T["percent"], view=view)
        engine, device = _set_tier(scene, tier, samples, aa, p.get("form"))
        film = bool(p["render"].get("film_transparent", True))
        if engine == "workbench":
            film = film and not (p.get("form") or {}).get("background")
            # matcaps are authored for a plain display transform; look first, so the restore runs in reverse
            tmp.set(scene.view_settings, look="None", view_transform="Standard")
            bg = (p.get("form") or {}).get("background")
            if bg and scene.world is not None:
                tmp.set(scene.world, color=tuple(bg))
        tmp.set(r, film_transparent=film)
        hide = list(p.get("hide") or [])
        if engine == "workbench" and not keep_floor:
            hide.append("Scene.Floor*")  # the form tier shows the model alone
        obs, colls = camera.hidden(hide, scene)
        for x in obs + colls:
            tmp.set(x, hide_render=True)
        out_dir = out_dir or camera.part_dir(p.get("owner"))
        os.makedirs(out_dir, exist_ok=True)
        views = camera.views(p)
        stem = (stem or f"{p['id']}_{tier}") + (f"_t{view}" if views > 1 else "")
        base = os.path.join(out_dir, stem)
        t1 = time.time()
        bpy.ops.render.render(scene=scene.name)
        seconds = time.time() - t1
        outputs = {}
        if engine == "workbench":
            _save(scene, base + ".png", "PNG", "8", "RGBA" if film else "RGB")
            outputs["png"] = base + ".png"
        else:
            _save(scene, base + "_ungraded.png", "PNG", "16", "RGBA" if film else "RGB")
            outputs["ungraded"] = base + "_ungraded.png"
            if T["exr"]:
                _save(scene, base + ".exr", "OPEN_EXR_MULTILAYER", T["exr"])
                outputs["exr"] = base + ".exr"
    finally:
        tmp.restore()
    if engine == "cycles":
        if do_grade:
            grade.grade_file(outputs["ungraded"], base + ".png")
            outputs["png"] = base + ".png"
        else:
            outputs["png"] = outputs["ungraded"]
    c = scene.cycles
    side = {
        "preset": p["id"], "label": p.get("label"), "alias_of": p.get("alias_of"), "tier": tier,
        "engine": r.engine if engine == "cycles" else "BLENDER_WORKBENCH", "device": device,
        "samples": c.samples if engine == "cycles" else None,
        "adaptive_threshold": (c.adaptive_threshold if c.use_adaptive_sampling else None) if engine == "cycles" else None,
        "denoise": (c.denoising_quality if c.use_denoising else None) if engine == "cycles" else None,
        "aa": aa if engine == "workbench" else None, "seed": SEED if engine == "cycles" else None,
        "seconds": round(seconds, 3), "seconds_total": round(time.time() - t0, 3),
        "resolution": cam_info.get("res"), "camera": cam_info, "scene": scene_note,
        "view_transform": [scene.view_settings.view_transform, scene.view_settings.look] if engine == "cycles" else ["Standard", "None"],
        "graded": bool(engine == "cycles" and do_grade), "film_transparent": film,
        "blender": bpy.app.version_string, "build_hash": bpy.app.build_hash.decode() if isinstance(bpy.app.build_hash, bytes) else bpy.app.build_hash,
        "commit": git_commit(), "light_solution": None,
        "blend": os.path.relpath(bpy.data.filepath, env.PROJECT_DIR).replace(os.sep, "/") if bpy.data.filepath else None,
        "time_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "outputs": {k: os.path.relpath(v, env.PROJECT_DIR).replace(os.sep, "/") for k, v in outputs.items()},
    }
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(side, f, indent=1)
        f.write("\n")
    return side


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--preset", nargs="+", default=[], metavar="NAME", help="preset ids or names")
    ap.add_argument("--part", help="every preset a part owns (01, 02, 17, ...)")
    ap.add_argument("--tier", default="form", choices=tuple(TIERS) + ("preset",),
                    help="render tier (default form; 'preset' uses each preset's own)")
    ap.add_argument("--out", help="output folder (default renders/<part>/)")
    ap.add_argument("--name", help="file stem (one preset only)")
    ap.add_argument("--border", action="store_true", help="render crops with a render border instead of the equivalent camera")
    ap.add_argument("--aa", default="8", choices=AA, help="form tier anti-aliasing (FXAA for sweeps)")
    ap.add_argument("--samples", type=int, help="override the tier's sample count")
    ap.add_argument("--scene", choices=("hero",), help="render look-dev presets in the hero scene")
    ap.add_argument("--floor", action="store_true", help="keep the floor in form renders")
    ap.add_argument("--no-grade", action="store_true")
    ap.add_argument("--view", type=int, help="one view of a turntable preset (default all)")
    ap.add_argument("--blend", help="scene to open when launched from plain Python (default cache/scene_eval.blend)")
    a = ap.parse_args(argv)
    if not camera.in_blender():
        blend = env.path(a.blend) if a.blend else SCENE_BLEND
        if not os.path.exists(blend):
            print(f"[render] {os.path.relpath(blend, env.PROJECT_DIR)} is missing; build it with "
                  "python scripts/eval/scene.py --build --proxy", flush=True)
            return 3
        return camera.run_in_blender(__file__, [x for x in argv], blend)
    import bpy
    reg = camera.load_registry()
    names = list(a.preset) + (reg.owner_ids(a.part) if a.part else [])
    if not names:
        ap.error("give --preset or --part")
    if a.name and len(names) > 1:
        ap.error("--name needs a single preset")
    out_dir = env.path(a.out) if a.out else None
    results, skipped = [], []
    for scene in bpy.data.scenes:
        scene.render.use_persistent_data = len(names) > 1
    for name in names:
        try:  # a view whose frame or scene is missing is reported and skipped; the rest still render
            p = reg.get(name)
            for v in ([a.view] if a.view is not None else range(camera.views(p))):
                side = render_preset(p, a.tier, out_dir, a.name, "border" if a.border else "equiv", a.aa, a.samples,
                                     a.scene, a.floor, not a.no_grade, v, reg)
                print(f"[render] {side['preset']} {side['tier']} {side['resolution']} on {side['device'] or side['engine']}: "
                      f"{side['seconds']:.2f} s render, {side['seconds_total']:.2f} s in all -> {side['outputs']['png']}", flush=True)
                results.append({k: side[k] for k in ("preset", "tier", "device", "seconds", "seconds_total", "outputs")})
        except (camera.MissingObject, LookupError) as e:
            print(f"[render] skipped: {e}", flush=True)
            skipped.append({"preset": name, "reason": str(e)})
    print("RESULT " + json.dumps({"renders": results, "skipped": skipped}), flush=True)
    return 3 if skipped else 0


if __name__ == "__main__":
    sys.exit(main(camera.script_args()))
