"""The high-resolution foot trial's entry point: build one method's region on the default build's left foot
and render it (notes/research_foot_hires.md).

  blender -b cache/body/rigged.blend --python-exit-code 1 --python scripts/research/foot_hires/run.py --
      --method base|fields|sdf [--level N] [--views hr.front,hr.hallux] [--tier form|eval|look]
      [--tag NAME] [--params JSON] [--save]

Methods: `base` is part 01's foot as built (its closeup copy at Subdivision 3 and its plates), the trial's
before; `fields` (method a) subdivides the copy and shapes the region with displacement fields at that
resolution (method_fields.py); `sdf` (method b) rebuilds the region as a signed distance field combined
with anatomical primitives and polygonised by OpenVDB (method_sdf.py). Renders go to
renders/research/foot_hires/<method>[_<tag>]/; --save also writes the region's mesh to
cache/research/foot_hires/ for the export and bake checks. Nothing is saved to a .blend.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import common as C  # noqa: E402

VIEWS = "hr.front,hr.top34,hr.medial,hr.plantar,hr.hallux,hr.toe2,p01.V5f.L,p01.V1f.L"


def parse(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--method", default="base", choices=("base", "fields", "sdf"))
    ap.add_argument("--level", type=int, default=None, help="Catmull-Clark level of the dense copy")
    ap.add_argument("--views", default=VIEWS)
    ap.add_argument("--tier", default="form", help="a tier, or several: form,eval (form first, then the Cycles ones)")
    ap.add_argument("--samples", type=int)
    ap.add_argument("--tag", default="")
    ap.add_argument("--params", default="{}", help="JSON overriding the method's parameters")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    return ap.parse_args(argv)


class Ctx:
    """What a method gets: the part module, the body, frame F, the joints, the dense skin and its options."""

    def __init__(self, args):
        self.args = args
        self.params = json.loads(args.params)
        self.part, self.body = C.open_build()
        self.frame = C.Frame()
        self.joints = C.joints(self.body, self.frame)
        self.skin = None
        self.plates = {}       # toe -> (object, uvw mm or None)
        self.extra_skins = []  # more skin objects that render with the region (method b's rest of the foot)
        self.report = {}

    def p(self, name, default):
        return self.params.get(name, default)


def method_base(ctx):
    """Part 01's foot as built: the closeup copy at its render level (3) and the part's plates."""
    import bpy
    ctx.skin = C.dense_copy(ctx.part, ctx.body, ctx.args.level or 3, name="Hires.L.Skin")
    for k in (1, 2, 3, 4, 5):
        ctx.plates[k] = (bpy.data.objects[f"Foot.L.Nail.{k}"], None)


def main(argv):
    import bpy
    a = parse(argv)
    t0 = time.time()
    ctx = Ctx(a)
    timings = {"open": round(time.time() - t0, 2)}
    t = time.time()
    if a.method == "base":
        method_base(ctx)
    elif a.method == "fields":
        import method_fields
        method_fields.build(ctx)
    else:
        import method_sdf
        method_sdf.build(ctx)
    timings["build"] = round(time.time() - t, 2)
    skin = ctx.skin
    ctx.report["skin"] = {"vertices": len(skin.data.vertices), "faces": len(skin.data.polygons)}
    out_dir = os.path.join(C.OUT, a.method + (f"_{a.tag}" if a.tag else ""))
    os.makedirs(out_dir, exist_ok=True)
    if a.save:
        ctx.report["saved"] = save_region(ctx, out_dir)
    if not a.no_render:
        # part 01's own plates that a method replaced stay out of every view
        hide = [o.name for o in bpy.data.objects if o.name.startswith("Foot.L.Nail.")
                and o not in [p[0] for p in ctx.plates.values()]]
        for o in bpy.data.objects:
            if o.name.startswith("Foot.R.") or o.name in hide:
                o.hide_render = True
        dressed = False
        for tier in a.tier.split(","):
            t = time.time()
            if tier != "form" and not dressed:
                import look
                for sk in [skin] + list(getattr(ctx, "extra_skins", [])):
                    look.dress_skin(sk)
                for k, (nob, uvw) in sorted(ctx.plates.items()):
                    look.dress_plate(nob, k, uvw, ridge_mm=0.0)
                look.lookdev_scene()
                dressed = True
                timings["dress"] = round(time.time() - t, 2)
            t = time.time()
            sides = C.render([v for v in a.views.split(",") if v], tier, out_dir, samples=a.samples)
            timings[f"render_{tier}"] = round(time.time() - t, 2)
            ctx.report.setdefault("renders", {}).update({f"{k}_{tier}": s["outputs"]["png"] for k, s in sides.items()})
            ctx.report.setdefault("render_seconds", {}).update({f"{k}_{tier}": s["seconds"] for k, s in sides.items()})
    timings["total"] = round(time.time() - t0, 2)
    ctx.report["timings"] = timings
    ctx.report["args"] = vars(a)
    C.write_json(os.path.join(out_dir, f"report_{a.tier.replace(',', '_')}.json"), ctx.report)
    print("RESULT " + json.dumps({k: ctx.report[k] for k in ("timings", "skin")}), flush=True)
    return 0


def save_region(ctx, out_dir):
    """The region's skin and plates as numpy arrays (world mm, faces), for the bake and export checks."""
    import numpy as np
    path = os.path.join(C.CACHE, f"{ctx.args.method}{('_' + ctx.args.tag) if ctx.args.tag else ''}.npz")
    os.makedirs(C.CACHE, exist_ok=True)
    data = {}
    for name, ob in [("skin", ctx.skin)] + [(f"nail{k}", o) for k, (o, _) in ctx.plates.items()]:
        me = ob.data
        co = np.array([ob.matrix_world @ v.co for v in me.vertices]) * C.MM
        data[name + "_co"] = co.astype(np.float32)
        data[name + "_faces"] = np.array([list(p.vertices) + [-1] * (4 - len(p.vertices)) for p in me.polygons], np.int32)
    data["F_R"], data["F_o"] = ctx.frame.R, ctx.frame.o      # frame F: q = (p - F_o) @ F_R
    np.savez_compressed(path, **data)
    return os.path.relpath(path, C.env.PROJECT_DIR)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sys.exit(main(argv))
