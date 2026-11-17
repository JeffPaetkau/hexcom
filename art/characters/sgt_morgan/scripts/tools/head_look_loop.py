"""The head's look loop (head round 10, scripts/parts/head.md section 13): rebuild the head part IN MEMORY on a
copy of the assembled soldier and render the hero head crop, without touching any cache.

  cp cache/assembled.blend cache/look_head.blend
  "$SGT_BLENDER" -b cache/look_head.blend --python scripts/tools/head_look_loop.py -- --out renders/head/r10/a1
      [--r5 | --r6] [--samples 64] [--crops head_face,soldier_full] [--keep-part] [--zooms]

Open a COPY of cache/assembled.blend beside it in cache/ (never the build artifact, never saved). The rig goes
to rest, the copy's Part.Head objects are removed and the part is built again from scripts/parts/head_look.py
and head_groom.py (so an edit there shows without a rebuild); --r5 first puts head_shape_r5.py's sculpt on
Body.Mesh as a shape key (the part is then built on that face; since round 11 the wired face IS round 5's, so
--r5 is obsolete), --r6 head_shape_r6.py's on the wired round-5 face; --keep-part skips the rebuild and renders the
part the copy holds. Then the hero pose again and each crop in Cycles as assemble.py renders it, graded, beside
the reference (<crop>_pair.png).
"""
import argparse
import json
import os
import sys
import time

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(SCRIPTS)
for p in (SCRIPTS, os.path.join(SCRIPTS, "parts"), os.path.join(SCRIPTS, "stages")):
    if p not in sys.path:
        sys.path.insert(0, p)


def main(argv):
    import bpy
    import common as C
    import head as H
    import head_look as HL
    from eval import camera, grade as GR, render as R, scene as S
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--crops", default="head_face")
    ap.add_argument("--r5", action="store_true")
    ap.add_argument("--r6", action="store_true")
    ap.add_argument("--keep-part", action="store_true")
    ap.add_argument("--zooms", action="store_true")
    a = ap.parse_args(argv)
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    t0 = time.perf_counter()
    body, rig = bpy.data.objects[C.BODY], bpy.data.objects[C.RIG]
    sc = bpy.context.scene
    info = {}
    if not a.keep_part:
        rig.data.pose_position = "REST"
        bpy.context.view_layer.update()
        bd = C.body_data(body)
        marks = C.base_json()["landmarks"]
        if a.r5:
            import head_shape_r5 as R5
            D5, info["r5"], _ = R5.delta(C, bd, marks)
            R5.apply_dev(body, D5)
            bd = C.body_data(body)
        if a.r6:
            import head_shape_r6 as R6
            import head_shape_r5 as R5
            D6, info["r6"], _ = R6.delta(C, bd, marks)
            R5.apply_dev(body, D6, name="head-shape-r6-dev")
            bd = C.body_data(body)
        coll = C.part_collection("Head")
        import head_groom as HG
        L = HL.landmarks(bd, marks)
        eyes, info["eyes"], E = HL.build_eyes(C, coll, rig, marks)
        lids = HL.lid_lines(bd, eyes, E, L)
        HL.split_wet(coll, eyes)
        cover, stub, info["groom"] = HG.build(C, bd, coll, body, rig, marks, L, lids)
        skin, info["skin"], _ = HL.build_skin(C, body, bd, marks, scalp_cover=cover, stubble=stub)
        HL.build_tearline(C, coll, body, rig, lids)
        HL.apply_to_scene(body, skin, coll)
        HL.attach_to_bones(coll, rig)
        rig.data.pose_position = "POSE"
        bpy.context.view_layer.update()
    for o in bpy.data.objects:
        if o.get("sgt_role") == "export":
            o.hide_render = True
    print("[head-look] built in", round(time.perf_counter() - t0, 1), "s", flush=True)
    floor = bpy.data.objects.get("Scene.Floor.C.Slab")
    reg = camera.load_registry()
    jobs = [(lab, reg.get(f"ref.{lab}")) for lab in a.crops.split(",")]
    if a.zooms:
        jobs += [("zoom_" + n, {"camera": {"type": "hero"}, "render": {"border_px": list(box), "scale": scale}})
                 for n, (box, scale) in H.ZOOMS.items()]
    for lab, p in jobs:
        camera.apply(p, sc, percent=100)
        R._set_tier(sc, "look", samples=a.samples)
        sc.cycles.denoising_quality = "HIGH"
        S.colour_management(sc)
        sc.render.film_transparent = True
        if floor:
            floor.hide_render = False
        tt = time.perf_counter()
        bpy.ops.render.render()
        ung = os.path.join(out, f"{lab}_cycles_ungraded.png")
        R._save(sc, ung, "PNG", "16", "RGBA")
        g = os.path.join(out, f"{lab}_cycles.png")
        GR.grade_file(ung, g)
        ref = os.path.join(PROJECT, p["compare"][0]) if p.get("compare") else os.path.join(PROJECT, "ref", "face_zooms", lab[5:] + ".png")
        if os.path.exists(ref):
            H.sheet3(ref, g, os.path.join(out, f"{lab}_pair.png"))
        print(f"[head-look] {lab} {time.perf_counter() - tt:.1f} s", flush=True)
    with open(os.path.join(out, "head_look_loop.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=1, default=str)
    print("[head-look] done in", round(time.perf_counter() - t0, 1), "s", flush=True)
    return 0


if __name__ == "__main__":
    try:
        rc = main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    except Exception:
        import traceback
        traceback.print_exc()
        rc = 1
    sys.stdout.flush()
    os._exit(rc)
