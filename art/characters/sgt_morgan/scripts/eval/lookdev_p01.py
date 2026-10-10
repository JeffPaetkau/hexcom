"""Part 01's foot in spec 17's LookDev under spec 16's materials: the look-dev of the skin, nail and sock
recipes on the real foot, at render time, without touching the part's script or caches.

  python scripts/eval/lookdev_p01.py [--views p01.V1.L,p01.V2.L,p01.V3.L,p01.V5.L] [--tier eval]
                                     [--samples N] [--sock] [--out renders/16_materials/foot]

Opens cache/body/rigged.blend (Body.Mesh and Morgan.Rig, build_all.py S2), puts part 01's layers back on
Body.Mesh from its layer cache (the sculpt, the contact key, the masks: parts/p01/layers.py, as the part's
own --from-cache does), appends the part cache (nails and frames, and the sock and guides once they are
there), assigns the recipes the way part 01's materials stage is to call them (`M.assign(body, "Skin.Foot",
part="Body", faces="Foot.Region")`, `M.nail_coords` and the two nail recipes per plate, the sock recipes by
its heel and toe groups), makes the closeup copies with the part's own isolate_copies() (they inherit the
body's materials), turns the opened scene into LookDev and renders the views into renders/16_materials/foot/
(not renders/01_foot/, which is the part's). Prints which of spec 01's masks and attributes are missing:
those layers render as off; --standin-masks paints rough versions of the missing §3.4 masks on the copies
only, to judge the regional layers before part 01 publishes its own (renders *_standin). Lints what it
assigned. Nothing is saved.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(HERE))  # scripts/
from lib import env  # noqa: E402
from eval import camera  # noqa: E402

BODY_BLEND = env.path("cache", "body", "rigged.blend")
PART_SCRIPT = env.path("scripts", "parts", "01_foot_ankle_sock.py")
OUT = env.path("renders", "16_materials", "foot")
VIEWS = "p01.V1.L,p01.V2.L,p01.V3.L,p01.V5.L"
# spec 01 §3.3: the lunula shows on the hallux (a 3.5 mm crescent) and faintly on the 2nd toe; the right
# hallux carries an old trauma ridge 5 mm from the fold
LUNULA_MM = {1: 3.5, 2: 1.5}
RIDGE = {("R", 1): 5.0}


def _smooth(x, a, b):
    import numpy as np
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def standin_masks(copies):
    """Rough versions of spec 01 §3.4 and §4.6's material masks, painted on the closeup copies only, so the
    regional layers can be judged before part 01 publishes its own (which win: a mask the copy already has
    is left alone). Positions are §3.4's, in frame F of each foot (mm; the right foot mirrored in X)."""
    import numpy as np
    import bpy
    made = {}
    for cp in copies:
        side = cp.name.split(".")[1]
        F = np.array(bpy.data.objects[f"Frame.Foot.{side}"].matrix_world)
        co = np.array([v.co for v in cp.data.vertices]) @ np.array(cp.matrix_world)[:3, :3].T + np.array(cp.matrix_world)[:3, 3]
        q = (np.c_[co, np.ones(len(co))] @ np.linalg.inv(F).T)[:, :3] * 1000.0
        if side == "R":
            q[:, 0] *= -1.0
        x, y, z = q[:, 0], q[:, 1], q[:, 2]

        def ell(cx, cy, cz, rx, ry, rz):
            d = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2)
            return 1.0 - _smooth(d, 0.6, 1.0)

        plantar = 1.0 - _smooth(z, 4.0, 9.0)
        masks = {
            "Foot.ToeRed": _smooth(-y, 222.0, 262.0),
            "Foot.Callus.Heel": _smooth(y, -48.0, -38.0) * _smooth(z, 1.0, 3.5) * (1.0 - _smooth(z, 10.0, 15.0)),
            "Foot.Callus.Ball": ell(-28, -208, 0, 16, 11, 7),
            "Foot.Callus.MTP5": ell(50, -185, 4, 10, 10, 10),
            "Foot.Callus.Hallux": ell(-53, -250, 10, 8, 6, 7),
            "Foot.Pressure": np.maximum(np.maximum(ell(0, -30, 0, 27, 24, 8), ell(-5, -205, 0, 45, 20, 8)),
                                        _smooth(-y, 240.0, 250.0) * plantar),
            "Foot.DorsumThin": _smooth(z, 18.0, 24.0) * (1.0 - _smooth(-y, 195.0, 210.0)),
            "Foot.SSSScale": np.where(-y > 210.0, 0.65, np.where(z < 8.0, 0.7, 1.0)),
            "Foot.Rub.Achilles": ell(0, 2, 57, 11, 8, 15),
        }
        if side == "L":
            masks["Foot.Corn.L4"] = ell(25, -233, 22, 3.5, 3.5, 3.5)
        for name, w in masks.items():
            if cp.vertex_groups.get(name) is not None:
                continue
            g = cp.vertex_groups.new(name=name)
            w = np.round(np.clip(w, 0.0, 1.0), 3)
            for value in np.unique(w[w > 1e-3]):
                g.add(np.nonzero(w == value)[0].tolist(), float(value), "REPLACE")
            made.setdefault(cp.name, []).append(name)
    return made


def part_module():
    spec = importlib.util.spec_from_file_location("part01_lookdev", PART_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dress(part, standin=False):
    """Layers, the part cache, the materials and the closeup copies; returns a report."""
    import bpy
    from lib import cache, materials as M
    from parts.p01 import layers, nails
    body = bpy.data.objects["Body.Mesh"]
    if not layers.apply(part.PART, body):
        raise RuntimeError("part 01's layer cache is missing or was made on another body: run "
                           "scripts/parts/01_foot_ankle_sock.py first")
    cache.load_part(part.PART)
    rep = {"body_groups": sorted(g.name for g in body.vertex_groups if g.name.startswith("Foot."))}
    M.ensure_groups()
    M.assign(body, "Skin.Foot", part="Body", faces="Foot.Region")
    plates = sorted((o for o in bpy.data.objects if o.name.startswith(("Foot.L.Nail.", "Foot.R.Nail."))),
                    key=lambda o: o.name)
    for nob in plates:
        side, k = nob.name.split(".")[1], int(nob.name.split(".")[-1])
        w, vis, fe, thick = nails.PLATES[k]
        free = M.nail_coords(nob, vis, fe, lunula_mm=LUNULA_MM.get(k, 0.0), ridge_mm=RIDGE.get((side, k), 0.0))
        nob.data.materials.clear()
        M.assign(nob, "Nail.Plate")
        M.assign(nob, "Nail.FreeEdge", faces=free)
        sol = nob.modifiers.get("Solidify")
        if sol is not None:
            # each rim takes its own face's material: the distal rim is free edge (spec 01 §4.4), while the
            # sides and the root, which dive under the folds, stay plate (an offset of 1 drew white lines there)
            sol.material_offset_rim = 0
    rep["nails"] = len(plates)
    socks = [o for o in bpy.data.objects if o.name.startswith("Sock.") and o.type == "MESH"]
    for ob in socks:
        ob.data.materials.clear()
        M.assign(ob, "Knit.Sock.WoolNylon")
        for g in ("sock_heel", "sock_toe"):
            if ob.vertex_groups.get(g) is not None:
                M.assign(ob, "Knit.Sock.WoolNylon.Reinforced", faces=g)
    rep["socks"] = [o.name for o in socks]
    copies = part.isolate_copies(body)
    rep["copies"] = {c.name: [m.name for m in c.data.materials if m] for c in copies}
    rep["standin"] = standin_masks(copies) if standin else {}
    rep["missing"] = {}
    for ob in copies + plates[:1] + socks:
        for mat, r in M.inputs_report(ob).items():
            if r["missing"]:
                rep["missing"][f"{mat} on {ob.name}"] = r["missing"]
    issues = M.lint([body] + plates + copies + socks)
    rep["lint"] = {"errors": [f"{i.code} {i.target}: {i.message}" for i in issues if i.level == "error"],
                   "warnings": sorted({f"{i.code} {i.target.split(' on ')[0]}" for i in issues if i.level == "warning"})}
    return rep, socks


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--views", default=VIEWS)
    ap.add_argument("--tier", default="eval")
    ap.add_argument("--samples", type=int)
    ap.add_argument("--sock", action="store_true", help="show the sock (spec 01 V7) instead of the bare foot")
    ap.add_argument("--standin-masks", action="store_true",
                    help="paint rough §3.4 masks on the closeup copies where part 01 has none yet (renders *_standin)")
    ap.add_argument("--out", default=os.path.relpath(OUT, env.PROJECT_DIR))
    ap.add_argument("--no-sheet", action="store_true")
    a = ap.parse_args(argv)
    if not camera.in_blender():
        for need, how in ((BODY_BLEND, "python scripts/build_all.py --to S2"),
                          (env.path("cache", "parts", "01_foot_ankle_sock.blend"), "the part 01 script")):
            if not os.path.exists(need):
                print(f"[lookdev_p01] {os.path.relpath(need, env.PROJECT_DIR)} is missing: build it with {how}", flush=True)
                return 3
        return camera.run_in_blender(__file__, argv, BODY_BLEND)
    import bpy
    from eval import lookdev, render
    t0 = time.time()
    part = part_module()
    rep, socks = dress(part, a.standin_masks)
    scene = lookdev.build(bpy.context.scene)
    for ob in socks:
        ob.hide_render = not a.sock
    rep["setup_s"] = round(time.time() - t0, 2)
    print("[lookdev_p01] " + json.dumps({k: rep[k] for k in ("body_groups", "copies", "socks", "standin")}), flush=True)
    for k, v in rep["missing"].items():
        print(f"[lookdev_p01] missing on {k}: {', '.join(v)}", flush=True)
    out_dir = env.path(a.out)
    tag = ("_sock" if a.sock else "") + ("_standin" if a.standin_masks else "")
    files, timings = [], {}
    for v in [x for x in a.views.split(",") if x]:
        side = render.render_preset(v, tier=a.tier, out_dir=out_dir, stem=f"{v}{tag}_{a.tier}", samples=a.samples)
        files.append(env.path(side["outputs"]["png"]))
        timings[v] = side["seconds"]
        print(f"[lookdev_p01] {v} {a.tier} {side['resolution']}: {side['seconds']:.1f} s -> {side['outputs']['png']}",
              flush=True)
    sheet = None
    pyimg = env.load().get("pyimg")
    if pyimg and files and not a.no_sheet:
        sheet = os.path.join(out_dir, f"sheet_{a.tier}{tag}.png")
        cmd = [pyimg, "-I", env.path("scripts", "tools", "sheet.py"), "sheet", "--preset", a.views.split(",")[0],
               "--title", f"part 01 look-dev, spec 16 materials, {a.tier}", "--out", sheet,
               "--images"] + files + ["--labels"] + [os.path.basename(f)[:-4] for f in files]
        p = subprocess.run(cmd, cwd=env.PROJECT_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode != 0 or not os.path.isfile(sheet):
            print(f"[lookdev_p01] sheet failed: {p.stdout[-300:]} {p.stderr[-300:]}", flush=True)
            sheet = None
        else:
            sheet = os.path.relpath(sheet, env.PROJECT_DIR).replace(os.sep, "/")
    res = {"renders": [os.path.relpath(f, env.PROJECT_DIR).replace(os.sep, "/") for f in files], "seconds": timings,
           "setup_s": rep["setup_s"], "total_s": round(time.time() - t0, 1), "missing": rep["missing"],
           "standin": rep["standin"], "lint": rep["lint"], "sheet": sheet, "lookdev": scene}
    print("RESULT " + json.dumps(res), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(camera.script_args()))
