"""The look loop: re-render the assembled soldier's hero crops after a materials or light change, without
rebuilding any part (take 2, round 8's look pass; round 5 had a scratch version of this).

  cp cache/assembled.blend cache/look_<tag>.blend
  "$SGT_BLENDER" -b cache/look_<tag>.blend --python scripts/tools/look_loop.py -- \
      --out renders/look/v1 [--crops torso_vest,legs_knees] [--samples 64] [--no-update] [--no-mask]
      [--scene-lights] [--key-temp 5800] [--cool-color 0.66,0.82,1.0] [--white-balance 5200,0]
      [--set Armour.Mat.Shell:albedo_hex=#5a6068 ...]
  "$SGT_PYIMG" -I scripts/tools/look_stats.py renders/look/v1 --grade --sheet

Open a COPY of cache/assembled.blend, beside it in cache/ (its relative image paths, the skin's among them,
resolve from there; elsewhere they render magenta), never the build artifact itself, never saved. Then:
  1. every library material in the file is brought up to date (materials.get with its recorded recipe,
     variant and overrides: a catalogue or builder change reaches it), then each part's MATERIALS table
     (scripts/parts/<part>.py, imported) is applied over it, so an override changed in a part script shows
     too; the carbine's make_materials() is re-run; parts' own shader-only additions need nothing else;
  2. the scene's lights and colour management as given (the key's temperature, a white balance);
  3. each ref.<crop> preset rendered as assemble.py renders it (Cycles, the `look` tier at --samples, OIDN
     high, AgX Medium High Contrast, film transparent, the floor on) to <out>/<crop>_cycles.png, and a
     Workbench FLAT pass with one exact colour per part to <out>/<crop>_mask.png (look_stats.py reads it).
Nothing here writes a cache or a .blend; part caches are rebuilt only by scripts/assemble.py.
"""
import argparse
import importlib
import json
import os
import sys
import time

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (SCRIPTS, os.path.join(SCRIPTS, "parts"), os.path.join(SCRIPTS, "stages")):
    if p not in sys.path:
        sys.path.insert(0, p)

# the part masks: exact, unshaded colours (Workbench FLAT, Standard view), one per part; look_stats.py
# decodes them back by nearest colour
MASK = {"body": (255, 0, 0), "head": (255, 0, 0), "trousers": (0, 255, 0), "shirt": (0, 0, 255),
        "boots": (255, 255, 0), "gloves": (255, 0, 255), "carrier": (0, 255, 255), "armour": (255, 128, 0),
        "belt": (128, 0, 255), "carbine": (128, 128, 128)}
PART_NAMES = {"trousers": "Trousers", "shirt": "Shirt", "gloves": "Glove", "carrier": "Carrier",
              "armour": "Armour", "belt": "Belt"}
CROPS = ("full", "soldier_full", "torso_vest", "arm_R", "arm_L", "hands_rifle", "belt_hips", "legs_knees",
         "boots_feet")


def update_materials(log):
    import bpy
    from lib import materials as M
    n = 0
    for m in list(bpy.data.materials):
        if m.library is not None or m.get("lib_version") is None or not m.get("recipe"):
            continue
        part = m.name.split(".Mat.")[0]
        try:
            over = json.loads(m.get("overrides", "{}"))
            M.get(m["recipe"], part, m.get("variant"), **over)
            n += 1
        except Exception as e:          # a recipe renamed or removed: say so, keep going
            log(f"  {m.name}: {type(e).__name__}: {e}")
    log(f"[look] {n} library materials brought up to date")
    for mod, part in PART_NAMES.items():
        try:
            tab = importlib.import_module(mod).MATERIALS
        except Exception as e:
            log(f"  {mod}.MATERIALS: {type(e).__name__}: {e}")
            continue
        k = 0
        for flat, (rid, var, over) in tab.items():
            name = f"{part}.Mat.{var}"
            if bpy.data.materials.get(name) is None:
                continue
            M.get(rid, part, var, **(over or {}))
            k += 1
        log(f"[look] {mod}: {k} table entries applied")
    k = 0
    for ob in bpy.data.objects:          # round 8: what the library pass would add (a print on the rest mesh)
        if ob.type != "MESH":
            continue
        attrs = set()
        for m in ob.data.materials:
            if m is not None and m.get("reads"):
                attrs.update(json.loads(m["reads"]).get("attributes", []))
        if "rest_pos" in attrs:
            M.rest_position(ob)
            k += 1
        if "edge_near" in attrs:
            M.edge_distance(ob)
            k += 1
    log(f"[look] rest_pos / edge_near written ({k})")
    try:
        # carbine.py builds the gun when imported (it ends in main()), so only its material functions are run:
        # hex_rgb, lib_material, ALU_F0 and make_materials, taken from its source
        import ast
        src = open(os.path.join(SCRIPTS, "parts", "carbine.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in ("srgb_to_linear", "hex_rgb", "lib_material",
                                                                                      "make_materials"))
                or (isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "ALU_F0" for t in n.targets))]
        ns = {"LIBMAT": M, "PART": "Carbine", "MATS": {}}
        exec(compile(ast.Module(body=keep, type_ignores=[]), "carbine.py (materials)", "exec"), ns)
        ns["make_materials"]()
        # round 8 renamed the barrel's and the A2's slot (Bronze -> Barrel, Muzzle): re-point an older file
        for ob in bpy.data.objects:
            if ob.type == "MESH":
                for i, m in enumerate(ob.data.materials):
                    if m is not None and m.name == "Carbine.Mat.Bronze":
                        ob.data.materials[i] = bpy.data.materials["Carbine.Mat." + ("Muzzle" if "Muzzle" in ob.name
                                                                                     else "Barrel")]
        log("[look] carbine: make_materials()")
    except Exception as e:
        log(f"  carbine: {type(e).__name__}: {e}")


def apply_sets(sets, log):
    """--set Mat:key=value: an override on one library material (dotted keys as materials.get takes them)."""
    import bpy
    from lib import materials as M
    for s in sets:
        name, kv = s.split(":", 1)
        k, v = kv.split("=", 1)
        m = bpy.data.materials[name]
        over = json.loads(m.get("overrides", "{}"))
        try:
            over[k] = json.loads(v)
        except ValueError:
            over[k] = v
        M.get(m["recipe"], name.split(".Mat.")[0], m.get("variant"), **over)
        log(f"[look] {name}: {k} = {over[k]}")


def part_of_objects():
    import bpy
    out = {}
    for c in bpy.data.collections:
        if c.name.startswith("Part."):
            p = c.name[5:].lower()
            for o in c.all_objects:
                out[o.name] = p
    return out


def main(argv):
    import bpy
    from eval import camera, render as R, scene as S
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--crops", default=",".join(CROPS))
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--no-update", action="store_true")
    ap.add_argument("--no-mask", action="store_true")
    ap.add_argument("--no-cycles", action="store_true")
    ap.add_argument("--key-temp", type=float, default=None)
    ap.add_argument("--white-balance", default=None, help="temperature,tint (Blender 4.5 view white balance)")
    ap.add_argument("--cool-color", default=None, help="r,g,b of the cool side light")
    ap.add_argument("--scene-lights", action="store_true",
                    help="rebuild the lights from scripts/eval/scene.py (x assemble.LIGHT_SCALE), as a new assembly would")
    ap.add_argument("--set", nargs="*", default=[])
    a = ap.parse_args(argv)
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    logf = open(os.path.join(out, "look_loop.log"), "a", encoding="utf-8")

    def log(s):
        print(s, flush=True)
        logf.write(s + "\n")

    t0 = time.perf_counter()
    if not a.no_update:
        update_materials(log)
    apply_sets(a.set, log)
    sc = bpy.context.scene
    if a.scene_lights:
        import assemble
        for ob in list(bpy.data.objects):
            if ob.name.startswith("Scene.Light."):
                bpy.data.objects.remove(ob, do_unlink=True)
        for L in S.build_lights(sc):
            L.data.energy *= assemble.LIGHT_SCALE
        log("[look] lights rebuilt from scene.py")
    cool = bpy.data.objects.get("Scene.Light.L.Cool")
    if a.cool_color and cool is not None:
        cool.data.color = tuple(float(v) for v in a.cool_color.split(","))
        log(f"[look] cool light colour {a.cool_color}")
    key = bpy.data.objects.get("Scene.Light.R.Key")
    if a.key_temp and key is not None:
        key.data.use_temperature, key.data.temperature = True, a.key_temp
        log(f"[look] key temperature {a.key_temp:g} K")
    log(f"[look] materials and lights in {time.perf_counter() - t0:.1f} s")
    part_of = part_of_objects()
    floor = bpy.data.objects.get("Scene.Floor.C.Slab")
    shown = [o for o in sc.objects if o.type == "MESH" and not o.name.startswith("Scene.")]
    reg = camera.load_registry()
    for lab in a.crops.split(","):
        p = reg.get(f"ref.{lab}")
        camera.apply(p, sc, percent=100)
        if not a.no_cycles:
            R._set_tier(sc, "look", samples=a.samples)
            sc.cycles.denoising_quality = "HIGH"
            S.colour_management(sc)
            if a.white_balance:
                t, tint = (float(v) for v in a.white_balance.split(","))
                vs = sc.view_settings
                vs.use_white_balance, vs.white_balance_temperature, vs.white_balance_tint = True, t, tint
            sc.render.film_transparent = True
            if floor:
                floor.hide_render = False
            tt = time.perf_counter()
            bpy.ops.render.render()
            R._save(sc, os.path.join(out, f"{lab}_cycles.png"), "PNG", "8", "RGBA")
            log(f"[look] {lab} cycles {time.perf_counter() - tt:.1f} s")
        if not a.no_mask:
            R._set_tier(sc, "form", form={"light": "FLAT", "cavity": False})
            sh = sc.display.shading
            sh.color_type = "OBJECT"
            for o in shown:
                o.color = (*[c / 255.0 for c in MASK.get(part_of.get(o.name, "body"), (255, 0, 0))], 1.0)
            sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
            sc.view_settings.use_white_balance = False
            sc.render.film_transparent = True
            sc.display.render_aa = "OFF"
            if floor:
                floor.hide_render = True
            bpy.ops.render.render()
            R._save(sc, os.path.join(out, f"{lab}_mask.png"), "PNG", "8", "RGBA")
    log(f"[look] done in {time.perf_counter() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []))
