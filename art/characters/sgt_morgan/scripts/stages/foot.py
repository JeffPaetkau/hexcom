"""Body stage: take 1's foot on take 2's body (scripts/parts/body.md §5, boots.md §6; Jeff, 2026-11-14: "For the
foot and boot work it's probably worth referencing all the work we did in the previous iteration").

Take 1's part 01 (archive/v1/scripts/parts/01_foot_ankle_sock.py and p01/) ported onto base.py's body. The modules
under scripts/stages/foot/ are copies of p01's (fields, footmetrics, transfer, scanref, scanfit, nails, sock, last,
matmasks, params.json, scan_targets.json) with their imports pointed here; nothing is imported from archive/.

What it does to Body.Mesh (in this order, all numpy on the shape-key mix, then written as layers):
  1. the MPFB foot targets take 1 fitted to ANSUR (params.json "targets": foot depth/horizontal scale, vert-decr,
     ankle girth) as shape keys. They are loaded AFTER the rig is fitted, so they move no bone: MPFB's vert-decr
     lowers the ankle joint cube from 75 to 64 mm and take 1's rig followed it below the malleoli (its spec 01 §4.1
     note); here the ankle bone stays where base.py put it, on the malleoli's level.
  2. Foot.Sculpt: the large forms transferred from subject 038's seated CC0 scan (Schuster, Kelly & Cresswell,
     zenodo 10360304; transfer.py) onto MakeHuman's topology, keeping its UVs, groups and weights, scaled to the
     274.3 mm foot; our geometry kept only in the toes' clefts (Foot.ScanKeep); pass B's toe poses and spacing and
     the nail beds; the scan handing over to the leg from z 110 and the leg eased onto it up to z 252.
  3. Foot.L/R.Nail.1-5, ten plates on the nail beds, bone-parented to the distal toe bones (collection Body).
  4. The geometric masks (Foot.Region, Foot.Sole, Foot.PlantarContact, Foot.ContactZone, Foot.NailBed.1-5,
     Foot.ScanKeep).
  5. Foot.Contact: the loaded foot from 038's standing scan, value 0 at rest (the last is built from it at 1.0).

The sock and the last are not built here: they are the boots' (scripts/parts/boots.py builds them from this body
with stages/foot/sock.py and last.py), so base.blend stays the body.

  "$SGT_BLENDER" -b --python scripts/stages/foot.py -- [--in cache/stages/base.blend] [--out FILE] [--render]
      standalone: opens --in, applies the foot, saves --out (default cache/stages/foot_dev.blend) and
      cache/stages/foot.json; --render adds the bare-foot clay views in renders/foot/.
  from base.py:  import foot; foot.apply(body, rig) -> record (base.py saves base.blend and base.json after it)

About 40 s on the workstation (the transfer's conjugate-gradient solves, two feet, rest and loaded).
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
SCRIPTS = os.path.join(PROJECT, "scripts")
for p in (SCRIPTS,):
    if p not in sys.path:
        sys.path.insert(0, p)

PARAMS = os.path.join(HERE, "foot", "params.json")
BODY, RIG, COLL = "Body.Mesh", "Morgan.Rig", "Body"
KEYS = ("Foot.Sculpt", "Foot.Contact")
REGION_TOP_MM = 130.0     # Foot.Region ends at MakeHuman's ankle seam ring (take 1 spec 01 §4.6)
OUT_JSON = os.path.join(PROJECT, "cache", "stages", "foot.json")
RENDER_DIR = os.path.join(PROJECT, "renders", "foot")


def say(*a):
    print("[foot]", *a, flush=True)


def params():
    with open(PARAMS, encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- layers on the body

def _drop(ob, *names):
    sk = ob.data.shape_keys
    for n in names:
        if sk is not None and n in sk.key_blocks:
            ob.shape_key_remove(sk.key_blocks[n])
        g = ob.vertex_groups.get(n)
        if g is not None:
            ob.vertex_groups.remove(g)


def _set_group(ob, name, weights, eps=1e-4):
    import numpy as np
    g = ob.vertex_groups.new(name=name)
    w = np.round(np.asarray(weights, float), 4)
    for value in np.unique(w[w > eps]):
        g.add(np.nonzero(w == value)[0].tolist(), float(value), "REPLACE")
    return g


def foot_targets(body, targets):
    """The MPFB foot targets (take 1's fit, params.json "targets") as shape keys on the body: {key: value}."""
    import bpy
    mod = "bl_ext.user_default.mpfb"
    if mod not in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_enable(module=mod)
    from bl_ext.user_default.mpfb.services.targetservice import TargetService
    sk = body.data.shape_keys
    out = {}
    for name, w in targets.items():
        kb = sk.key_blocks.get(name) if sk else None
        if kb is None:
            path = TargetService.target_full_path(name)
            if not path or os.path.basename(path).split(".")[0] != name:
                raise FileNotFoundError(f"MPFB has no target {name!r}")
            kb = TargetService.load_target(body, path, weight=w)
        kb.value = float(w)
        out[kb.name] = round(float(kb.value), 6)
        sk = body.data.shape_keys
    return out


def _joint_cubes(ob, side, co_world):
    """{cube ("toe-1-1", "ankle", ...): world mm} of one side's MakeHuman joint cubes on the sculpted rest body."""
    from lib import sculpt as S
    sl = "l" if side == "L" else "r"
    pre = f"joint-{sl}-"
    names = [g.name for g in ob.vertex_groups if g.name.startswith(pre + "toe-") or g.name in (pre + "ankle", pre + "foot-1", pre + "foot-2")]
    W = S.group_weights_many(ob, names)
    out = {}
    for n in names:
        sel = W[n] > 0.5
        if sel.any():
            out[n[len(pre):]] = co_world[sel].mean(axis=0)
    return out


def apply(body, rig, prm=None, nail_collection=None):
    """Applies the foot to body (Body.Mesh, rig at rest): targets, Foot.Sculpt, nails, masks, Foot.Contact.
    Re-running replaces its own layers and objects. Returns a JSON-able record."""
    import bpy
    import numpy as np
    from lib import sculpt as S
    from stages.foot import fields, footmetrics as fm, nails, transfer as X
    t0 = time.perf_counter()
    prm = prm or params()
    rec = {"source": "take 1 part 01 (archive/v1/scripts/parts/01_foot_ankle_sock.py, p01/), ported to "
                     "scripts/stages/foot/", "params": os.path.relpath(PARAMS, PROJECT).replace("\\", "/")}
    rig.data.pose_position = "REST"
    # 1. the MPFB foot targets
    rec["targets"] = foot_targets(body, prm["targets"])
    # 2. the sculpt: the scan transfer
    _drop(body, *KEYS)
    bpy.context.view_layer.update()
    fm._INDEX.clear()
    B = fields.Body(body, exclude=KEYS)
    cfg = X.config(prm)
    a = fields.amounts(prm)
    co = B.positions(a, fields.options(prm), transfer=cfg)
    S.key_from_positions(body, "Foot.Sculpt", co / 1000.0, base=B.co / 1000.0)
    rec["transfer"] = {}
    for side in fields.SIDES:
        foot = B.feet[side]
        tr = getattr(foot, "transfer", None)
        if tr is not None:
            last = tr["fit"][-1]
            rec["transfer"][side] = {"scan": cfg["scan"], "on_scan": f"{last['n']}/{last['of']}",
                                     "rms_mm": last["rms"], "max_mm": last["max"],
                                     "kept_cage_vertices": int((tr["keep"] > 0.5).sum()), "leg": tr.get("leg")}
            say(f"{side} transfer onto scan {cfg['scan']}: {last['n']}/{last['of']} cage vertices on it, rms {last['rms']} "
                f"max {last['max']} mm, {int((tr['keep'] > 0.5).sum())} kept between the toes")
    rest = S.mix(body, exclude=("Foot.Contact",)) * 1000.0
    # 3. the nails
    for o in [o for o in bpy.data.objects if o.name.startswith(("Foot.L.Nail.", "Foot.R.Nail."))]:
        me = o.data
        bpy.data.objects.remove(o)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    coll = nail_collection or bpy.data.collections.get(COLL) or bpy.context.scene.collection
    made = {}
    for side in fields.SIDES:
        foot = B.feet[side]
        tw = {k: sum(B.groups[g] for g in fm.toe_bones(k, side) if g in B.groups) for k in fields.TOES}
        faces = nails.nail_faces(body, rest / 1000.0, side, tw, B.groups["toenails"])
        for k in fields.TOES:
            if not faces[k]:
                say(f"warning: no nail bed on toe {k} of the {side} foot")
                continue
            axis = foot.frame.vec_to_w((getattr(foot, "axis_now", None) or {}).get(k, foot.toe[k]["a"]))
            w, vis, fe, thick = nails.PLATES[k]
            name = f"Foot.{side}.Nail.{k}"
            radius = (getattr(foot, "nail_radius", None) or fields.NAIL_RADIUS)[k]
            me, dims, frame = nails.build_plate(name, body, rest / 1000.0, faces[k], axis, thick, fe, radius,
                                                nails.CORNER_MM[k])
            nob = bpy.data.objects.new(name, me)
            coll.objects.link(nob)
            nails.finish(nob, thick)
            nails.parent_to_bone(nob, rig, f"{nails.DISTAL_BONE[k]}.{side}")
            nob["sgt_clay"] = (0.80, 0.74, 0.70)
            made[name] = {k2: round(v, 2) for k2, v in dims.items()}
    rec["nails"] = made
    _nail_material(list(bpy.data.objects[n] for n in made))
    # 4. the geometric masks
    names = ["Foot.Region", "Foot.Sole", "Foot.PlantarContact", "Foot.ContactZone"] + \
        [f"Foot.NailBed.{k}" for k in fields.TOES] + ["Foot.ScanKeep"]
    _drop(body, *names)
    nrm = S.vertex_normals(rest, *B.topo)
    n = len(rest)
    W = {nm: np.zeros(n) for nm in names}
    bodymask = np.zeros(n, bool)
    bodymask[B.m0.orig if B.m0.orig is not None else np.arange(n)] = True
    for side in fields.SIDES:
        foot = B.feet[side]
        R = foot.R[foot.body]
        z = rest[R, 2]
        W["Foot.Region"][R] = (z < REGION_TOP_MM).astype(float)
        W["Foot.Sole"][R] = S.smoothstep(-nrm[R, 2], 0.3, 0.6) * (1.0 - S.smoothstep(z, 8.0, 14.0))
        W["Foot.PlantarContact"][R] = 1.0 - S.smoothstep(z, 1.0, 4.0)
        W["Foot.ContactZone"][R] = 1.0 - S.smoothstep(z, 12.0, 20.0)
        for k in fields.TOES:
            W[f"Foot.NailBed.{k}"][foot.R[foot.nail_rows[k]]] = 1.0
        if getattr(foot, "transfer", None) is not None:
            W["Foot.ScanKeep"][foot.R] = foot.transfer["keep"]
    for nm in names:
        _set_group(body, nm, W[nm] * bodymask)
    # 5. the loaded foot
    loaded = rest.copy()
    for side in fields.SIDES:
        foot = B.feet[side]
        q = foot.frame.to_f(rest[foot.R])
        loaded[foot.R] = foot.frame.to_w(fields.contact(B, side, q, transfer=cfg))
    S.key_from_positions(body, "Foot.Contact", loaded / 1000.0, base=rest / 1000.0, value=0.0)
    bpy.context.view_layer.update()
    rec["measure"] = measure(body)
    rec["seconds"] = round(time.perf_counter() - t0, 1)
    say(json.dumps(rec["measure"]))
    return rec


def _nail_material(plates):
    """Spec 16's Nail.Plate / Nail.FreeEdge from the library when it loads, else a flat nail colour."""
    import bpy
    try:
        from lib import materials as M
        M.ensure_groups()
        for nob in plates:
            k = int(nob.name.split(".")[-1])
            from stages.foot import nails
            w, vis, fe, thick = nails.PLATES[k]
            free = M.nail_coords(nob, vis, fe)
            nob.data.materials.clear()
            M.assign(nob, "Nail.Plate")
            M.assign(nob, "Nail.FreeEdge", faces=free)
            sol = nob.modifiers.get("Solidify")
            if sol is not None:
                sol.material_offset_rim = 0
        return "library"
    except Exception as e:  # noqa: BLE001 - a flat colour on any library problem
        say(f"nail materials from the library failed ({type(e).__name__}: {e}); flat colour")
        m = bpy.data.materials.get("Foot.Mat.Nail") or bpy.data.materials.new("Foot.Mat.Nail")
        m.diffuse_color = (0.80, 0.70, 0.66, 1.0)
        for nob in plates:
            nob.data.materials.clear()
            nob.data.materials.append(m)
        return "flat"


# --------------------------------------------------------------------------- measurement

def measure(body):
    """Per foot (frame F, mm): length (pternion to the longest toe), the heading, ball and heel breadths, the
    malleoli, the frame's origin; the lowest skin point (z 0 stays the floor); the toe tips."""
    import numpy as np
    from stages.foot import footmetrics as fm
    fm._INDEX.clear()
    m = fm.read(body)
    ix = fm.index(body, m)
    out = {}
    co = m.co * 1000.0
    for side in ("L", "R"):
        f = fm.frame(m, ix, side)
        v = fm.foot(m, ix, side, toes=False)
        q = f.to_f(co[ix.region[side]])
        tips = {}
        for k in (1, 2, 3, 4, 5):
            tq = f.to_f(co[ix.toe[side][k]])
            tips[k] = round(float(-tq[:, 1].min()), 1)
        out[side] = {"foot_length": round(v["foot_length"], 1), "heading_deg": round(f.heading_deg(), 2),
                     "frame_origin_mm": [round(float(c), 1) for c in f.o],
                     "toe_reach_from_pternion": tips,
                     "max_breadth_below_z60": round(float(np.ptp(q[q[:, 2] < 60.0][:, 0])), 1)}
        for k in ("ball_breadth", "heel_breadth", "bimalleolar", "ankle_circ_min", "malleolus_lateral_z",
                  "malleolus_medial_z", "dorsum_h50", "dorsum_h60", "dorsum_h70", "arch_medial_45"):
            if k in v:
                out[side][k] = round(float(v[k]), 1)
    out["lowest_z_mm"] = round(float(co[:, 2].min()), 2)
    return out


def foot_landmarks(body):
    """base.json's foot landmarks on the body with the foot (stages/foot/marks.py: base.py's definition, which
    pose_solve seats on the footbeds and boots.py builds its sole plane from)."""
    from stages.foot import marks
    return marks.foot_landmarks(body)


# --------------------------------------------------------------------------- renders (bare foot, clay)

def isolate(body, side, top_mm=300.0):
    """One foot of the evaluated body cut below top_mm, with its nails joined, smooth, subdivision 2 for render."""
    import bmesh
    import bpy
    s = 1.0 if side == "L" else -1.0
    dg = bpy.context.evaluated_depsgraph_get()
    name = f"Aux.Foot.{side}"
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old)
    me = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    me.name = name
    bm = bmesh.new()
    bm.from_mesh(me)
    kill = [v for v in bm.verts if not (s * v.co.x > 0.03 and v.co.z < top_mm / 1000.0)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    sub = ob.modifiers.new("Subdivision", "SUBSURF")
    sub.levels, sub.render_levels = 2, 2
    ob["sgt_clay"] = (0.78, 0.72, 0.66)
    return ob


def render(body, rig, tag="foot"):
    """Clay views of the bare left and right feet (rest), frame-F cameras like take 1's p01 presets: V1f (dorsal
    oblique, far), V2 (medial), V3 (lateral), V4 (plantar), V5f (toes), V8 (posterior). renders/foot/<tag>_*.png."""
    import bpy
    import numpy as np
    sys.path.insert(0, os.path.join(SCRIPTS, "parts"))
    import common as C
    from stages.foot import footmetrics as fm
    C.rest_pose(rig)
    fm._INDEX.clear()
    m = fm.read(body)
    ix = fm.index(body, m)
    os.makedirs(RENDER_DIR, exist_ok=True)
    sc = bpy.context.scene
    # (eye, target) in frame F (mm), lens: take 1 spec 01 §1.3 (V1f / V5f are the far versions for proportion)
    views = {"V1f": ((690.0, -1680.0, 1260.0), (0.0, -150.0, 40.0), 180.0),
             "V2": ((-650.0, -140.0, 95.0), (0.0, -140.0, 55.0), 70.0),
             "V3": ((650.0, -140.0, 95.0), (0.0, -140.0, 55.0), 70.0),
             "V4": ((0.0, -140.0, -600.0), (0.0, -140.0, 0.0), 50.0),
             "V5f": ((-150.0, -1500.0, 450.0), (-30.0, -265.0, 15.0), 250.0),
             "V8": ((0.0, 700.0, 60.0), (0.0, -60.0, 60.0), 135.0)}
    out = []
    for side in ("L", "R"):
        f = fm.frame(m, ix, side)
        aux = isolate(body, side)
        nails_ = [o for o in bpy.data.objects if o.name.startswith(f"Foot.{side}.Nail.")]
        keep = {aux.name, *[o.name for o in nails_]}
        hidden = []
        for o in sc.objects:
            if o.name not in keep and not o.hide_render:
                o.hide_render = True
                hidden.append(o)
        C._workbench(sc, "OBJECT", bg=(0.86, 0.86, 0.84))
        for o in (aux, *nails_):
            o.color = (*(o.get("sgt_clay") or (0.8, 0.74, 0.7)), 1.0)
        cam = C._aux_camera()
        sc.camera = cam
        sc.render.resolution_x = sc.render.resolution_y = 1000
        for vname, (eye, tgt, lens) in views.items():
            cam.data.type, cam.data.lens, cam.data.sensor_fit = "PERSP", lens, "AUTO"
            e = f.to_w(np.array(eye))
            t = f.to_w(np.array(tgt))
            C._look(cam, e, t)
            p = os.path.join(RENDER_DIR, f"{tag}_{vname}_{side}.png")
            C._render(p)
            out.append(p)
        for o in hidden:
            o.hide_render = False
        bpy.data.objects.remove(aux)
    say("renders:", ", ".join(os.path.basename(p) for p in out))
    return out


# --------------------------------------------------------------------------- standalone

def main():
    import bpy
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(name, default):
        return argv[argv.index(name) + 1] if name in argv else default
    src = os.path.join(PROJECT, opt("--in", os.path.join("cache", "stages", "base.blend")))
    dst = os.path.join(PROJECT, opt("--out", os.path.join("cache", "stages", "foot_dev.blend")))
    if os.path.abspath(dst) == os.path.abspath(os.path.join(PROJECT, "cache", "stages", "base.blend")) and "--in-place" not in argv:
        raise SystemExit("refusing to overwrite base.blend without --in-place (base.py calls foot.apply itself)")
    bpy.ops.wm.open_mainfile(filepath=src)
    body, rig = bpy.data.objects[BODY], bpy.data.objects[RIG]
    rec = apply(body, rig)
    rec["landmarks"] = foot_landmarks(body)
    rec["in"], rec["out"] = os.path.relpath(src, PROJECT), os.path.relpath(dst, PROJECT)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".tmp.blend"
    bpy.ops.wm.save_as_mainfile(filepath=tmp, copy=True, compress=False)
    os.replace(tmp, dst)
    with open(opt("--json", OUT_JSON), "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=1)
    say(f"saved {os.path.relpath(dst, PROJECT)} in {rec['seconds']} s")
    if "--render" in argv:
        render(body, rig, opt("--tag", "foot"))
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        rc = 1
    sys.stdout.flush()
    os._exit(rc)
