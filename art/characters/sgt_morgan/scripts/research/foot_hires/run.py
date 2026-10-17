"""The high-resolution foot trial's entry point: build one method's region on the default build's left foot
and render it (notes/research_foot_hires.md).

  blender -b cache/body/rigged.blend --python-exit-code 1 --python scripts/research/foot_hires/run.py --
      --method base|fields|sdf|scan [--level N] [--views hr.front,hr.hallux] [--tier form|eval|look]
      [--tag NAME] [--params JSON] [--save]

Methods: `base` is part 01's foot as built (its closeup copy at Subdivision 3 and its plates), the trial's
before; `fields` (method a) subdivides the copy and shapes the region with displacement fields at that
resolution (method_fields.py); `sdf` (method b) rebuilds the region as a signed distance field combined
with anatomical primitives and polygonised by OpenVDB (method_sdf.py); `scan` puts a real foot's aligned scan in
this foot's frame for reference renders (scan.build, the scan-driven pass of 2026-10-16; not with --save). Renders go to
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
    ap.add_argument("--method", default="base", choices=("base", "fields", "sdf", "scan"))
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
    elif a.method == "scan":   # the scan-driven pass (2026-10-16): a real foot's scan in this foot's frame, as reference
        import scan
        scan.build(ctx)
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
            # round 5: the toes' hair (hair.py) renders in Cycles only; the clay judges form
            hair = bpy.data.objects.get("Hires.L.Hair")
            if hair is not None:
                hair.hide_render = tier == "form"
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
            ids = [v for v in a.views.split(",") if v]
            plans = [v for v in ids if v in PLAN_VIEWS]
            sides = C.render([v for v in ids if v not in PLAN_VIEWS], tier, out_dir, samples=a.samples,
                             hide=("Hires.L.SkinPlan",))
            for v in plans:   # the cut copy shows, the full skin is hidden (the preset's own hide list)
                cut = plan_copy(skin, PLAN_VIEWS[v])
                sides.update(C.render([v], tier, out_dir, samples=a.samples))
                cut.hide_render = True
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
    """The region's skin and plates as numpy arrays (world mm, faces), for the bake and export checks; with the
    toes' weights (toe_w, one column a toe) and the joints (F mm, JSON) for shape.py's measures."""
    import numpy as np
    import method_fields
    import toes as T
    path = os.path.join(C.CACHE, f"{ctx.args.method}{('_' + ctx.args.tag) if ctx.args.tag else ''}.npz")
    os.makedirs(C.CACHE, exist_ok=True)
    data = {}
    for name, ob in [("skin", ctx.skin)] + [(f"nail{k}", o) for k, (o, _) in ctx.plates.items()]:
        me = ob.data
        co = np.array([ob.matrix_world @ v.co for v in me.vertices]) * C.MM
        data[name + "_co"] = co.astype(np.float32)
        data[name + "_faces"] = np.array([list(p.vertices) + [-1] * (4 - len(p.vertices)) for p in me.polygons], np.int32)
    data["F_R"], data["F_o"] = ctx.frame.R, ctx.frame.o      # frame F: q = (p - F_o) @ F_R
    groups = method_fields.read_groups(ctx.skin)
    data["toe_w"] = np.stack([T.toe_weight(groups, k) for k in (1, 2, 3, 4, 5)], 1).astype(np.float16)
    data["joints"] = json.dumps({k: np.asarray(v).tolist() for k, v in ctx.joints.items()})
    np.savez_compressed(path, **data)
    return os.path.relpath(path, C.env.PROJECT_DIR)


# the plan views: a true top orthographic camera sees the leg's section at z 300 over the heel, so these render a
# copy of the skin cut level just above the malleoli and capped (plan_copy), the full skin hidden (the shape pass,
# 2026-10-14)
PLAN_VIEWS = {"hr.plan": 125.0}


def plan_copy(skin, z_cut_mm, name="Hires.L.SkinPlan"):
    """The skin cut by the plane z = z_cut (F and world z agree: frame F is a rotation about Z on the floor) and the
    cut capped, in the skin's collections, the same material slots: the foot's plan without the leg above."""
    import bmesh
    import bpy
    old = bpy.data.objects.get(name)
    if old is not None:
        me_old = old.data
        bpy.data.objects.remove(old)
        bpy.data.meshes.remove(me_old)
    me = skin.data.copy()
    me.name = name
    bm = bmesh.new()
    bm.from_mesh(me)
    z = z_cut_mm / C.MM
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-7,
                                 plane_co=(0.0, 0.0, z), plane_no=(0.0, 0.0, 1.0), clear_outer=True)
    cut = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if cut:
        bmesh.ops.holes_fill(bm, edges=cut, sides=0)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    for g in skin.vertex_groups:   # the weights came with the mesh; the names (in order) are the object's
        ob.vertex_groups.new(name=g.name)
    for coll in skin.users_collection:
        coll.objects.link(ob)
    return ob


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sys.exit(main(argv))
