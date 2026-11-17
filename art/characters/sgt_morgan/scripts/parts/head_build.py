"""The head part's build, from round 10 (scripts/parts/head.md section 13): the skin's look, the eyes and tear
lines (head_look.py), the hair, brows, lashes, stubble and the export proxy (head_groom.py).

  "$SGT_PYIMG" -I scripts/assemble.py --rebuild head                                  # the part alone, ~80 s
  "$SGT_BLENDER" -b --python scripts/parts/head_build.py [-- --no-render] [--samples 64] [--prefix head_]

Writes cache/parts/head.blend (+ head.json) and cache/parts/head_look.blend (Head.Mat.Skin, which assemble.py's
hook, head_look.on_assemble, puts on Body.Mesh).

Why a file of its own and not head.py's bl_build: base.py imports head_skin.py, which imports head.py, so any
edit to head.py (or a module it imports) makes assemble.py call base.blend stale, and a base rebuild rebuilds
every part. Round 10 was not to rebuild the base, so head.py is left as committed (the likeness fit, the checks,
rounds 1-2's cap and the render helpers used here) and assemble.py builds the head item from this script. Fold
it back into head.py at the next base rebuild if wanted.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
SCRIPTS = os.path.join(PROJECT, "scripts")
for p in (SCRIPTS, HERE, os.path.join(SCRIPTS, "stages")):
    if p not in sys.path:
        sys.path.insert(0, p)


def visible_only(raw, colls, keep_body=True):
    """common.visible_only, with the export proxy (ob["sgt_role"] == "export") and the base's objects the part
    replaces (Body.Eyes, and the brow and lash cards) kept out of the render."""
    import bpy
    restore = raw(colls, keep_body)
    have = {o.name for c in colls for o in c.all_objects}
    for o in bpy.data.objects:
        if o.get("sgt_role") == "export" or (o.name == "Body.Eyes" and "Head.Eyes" in have) \
                or (o.name == "Body.Eyebrows" and "Head.Brows" in have) or (o.name == "Body.Eyelashes" and "Head.Lashes" in have):
            o.hide_render = True
    return restore


def bl_build(argv):
    import bpy
    import common as C
    import head as H
    import head_groom as HG
    import head_look as HL
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--prefix", default="head_")
    args = ap.parse_args(argv)
    t0 = time.perf_counter()
    body, rig = C.open_base()
    bd = C.body_data(body)
    marks = C.base_json()["landmarks"]
    coll = C.part_collection("Head")
    L = HL.landmarks(bd, marks)
    eyes, einfo, E = HL.build_eyes(C, coll, rig, marks)
    lids = HL.lid_lines(bd, eyes, E, L)
    HL.split_wet(coll, eyes)
    cover, stub, ginfo = HG.build(C, bd, coll, body, rig, marks, L, lids)
    skin, sinfo, _ = HL.build_skin(C, body, bd, marks, scalp_cover=cover, stubble=stub)
    tear, tinfo = HL.build_tearline(C, coll, body, rig, lids)
    proxy = bpy.data.objects.get("Head.Hair.Proxy")
    rest_clear = C.clearance([proxy], body, "rest") if proxy is not None else None
    fit = json.load(open(H.FIT_JSON)) if os.path.exists(H.FIT_JSON) else {}
    extra = {"part": "head", "groom": ginfo, "skin": sinfo, "eyes": einfo, "tearline": tinfo,
             "hair": ginfo["hair"], "stubble": ginfo["stubble"],
             "clearance_rest": rest_clear, "look": "cache/parts/head_look.blend (Head.Mat.Skin; head_look.on_assemble)",
             "face_targets": len(fit.get("targets", {})), "face_fit": "scripts/parts/head_fit.json",
             "face_shape": "scripts/parts/head-shape.target (head_shape.py)", "base": C.BASE_BLEND}
    C.save_part("head", coll, extra)
    HL.save_look([skin])
    # for this part's own renders (the body is not saved): what assemble.py's hook does
    HL.apply_to_scene(body, skin, coll)
    HL.attach_to_bones(coll, rig)
    if not args.no_render:
        OUT = H.OUT
        os.makedirs(OUT, exist_ok=True)
        pre = args.prefix
        raw = C.visible_only                         # head.py's and common's renders hide and show through it
        C.visible_only = lambda colls, keep_body=True: visible_only(raw, colls, keep_body)
        H.render_rest_head(coll, args.samples, pre)
        used = C.apply_hero_pose(rig)
        extra["clearance_posed"] = C.clearance([proxy], body, "posed") if proxy is not None else None
        C.render_hero([coll], "ref.head_face", os.path.join(OUT, f"{pre}hero_head_face.png"))
        H.sheet3(H.REF_CROP, os.path.join(OUT, f"{pre}hero_head_face.png"), os.path.join(OUT, f"{pre}hero_head_face_pair.png"))
        H.render_hero_cycles(coll, "ref.head_face", os.path.join(OUT, f"{pre}hero_head_face_cycles.png"), args.samples)
        H.sheet3(H.REF_CROP, os.path.join(OUT, f"{pre}hero_head_face_cycles.png"), os.path.join(OUT, f"{pre}hero_head_face_cycles_pair.png"))
        H.render_zooms(coll, args.samples, pre)
        extra["pose"] = used
    extra["seconds"] = round(time.perf_counter() - t0, 1)
    with open(os.path.join(C.PARTS_DIR, "head.json"), "w") as f:
        json.dump(extra, f, indent=1, default=str)
    print("[head]", json.dumps({k: extra[k] for k in ("hair", "seconds")}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        rc = bl_build(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    except Exception:
        import traceback
        traceback.print_exc()
        rc = 1
    sys.stdout.flush()
    os._exit(rc)
