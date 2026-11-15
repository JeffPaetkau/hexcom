"""Round 2 of the pose: the real surfaces for the solver, and the hands' close-up check (Blender side).

  "$SGT_BLENDER" -b cache/stages/base.blend --python scripts/stages/pose_contact.py -- --export [--if-stale]
      cache/stages/contact.npz: what pose_solve.py's contact terms read (see export_contact). pose.py --solve
      runs this first (with --if-stale: only when a part cache, base.blend, this script or face_targets.json is
      newer than contact.npz).
  "$SGT_BLENDER" -b --python scripts/stages/pose_contact.py -- --render-hands
      the hands on the carbine in cache/assembled.blend (assemble.py --round N), each hand along the hero
      camera's line, from the gun's right and left sides, from above and from the front:
      renders/pose/pose_hands_<side>_<view>.png ("--quick": build the scene from the caches instead)

Kept apart from pose.py on purpose: the part scripts import pose.py (common.apply_hero_pose), and assemble.py
counts every module they import as an input of every part, so code here would make every part stale.
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
HERO_JSON = os.path.join(HERE, "hero_pose.json")
BASE_BLEND = os.path.join(PROJECT, "cache", "stages", "base.blend")
RIG = "Morgan.Rig"
sys.path.insert(0, HERE)
from pose import apply_hero_pose  # noqa: E402

# --------------------------------------------------------------------------- contact data
#
# The solver (pose_solve.py, outside Blender) needs the real surfaces the hands, arms and carbine must touch
# and must not enter. export_contact() writes cache/stages/contact.npz:
#   carbine_occ   inside/outside voxels of every Carbine.* mesh (all closed) in the carbine frame
#                 (Carbine.Root's local space, mm), by ray parity along x, y and z (majority vote)
#   carrier_occ   the same for the carrier (posed in the current hero pose, world mm) and the posed matrix of
#                 the carrier's reference bone (spine02) then, so the solver can carry it with the chest
#   pts_<set>     rest vertices (mm), top-4 bone weights and rest normals of the surfaces that touch them:
#                 the glove shells, knuckle guards and PIP pads (the hands' outer surface, 1.8 mm over the
#                 skin), the shirt sleeves, the forearm guards, the hand skin (finger self-contact) and the
#                 face vertices face_targets.json names
CONTACT_NPZ = os.path.join(PROJECT, "cache", "stages", "contact.npz")
FACE_JSON = os.path.join(HERE, "face_targets.json")
CONTACT_INPUTS = [os.path.join(PROJECT, "cache", "parts", f"{p}.blend") for p in ("carbine", "carrier", "gloves", "shirt", "armour")]
CARBINE_GRID = {"lo": (-320.0, -60.0, -215.0), "hi": (570.0, 60.0, 115.0), "h": 1.0}
CARRIER_GRID = {"lo": (-330.0, -230.0, 1020.0), "hi": (260.0, 120.0, 1560.0), "h": 1.5}
CARRIER_REF_BONE = "spine02"


def _voxelize(meshes, lo, hi, h):
    """meshes: [(V (n,3) mm in the grid frame, polys)]; closed meshes. Inside voxels by ray parity along
    each axis (offset off the voxel centres so no ray grazes an edge), majority of the three."""
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    shape = tuple(int(math.ceil(v)) for v in (hi - lo) / h)
    votes = np.zeros(shape, np.uint8)
    jit = (0.1371, 0.2913, 0.0617)
    for V, P in meshes:
        bvh = BVHTree.FromPolygons([Vector(v) for v in V], P, epsilon=0.0)
        mlo, mhi = V.min(0), V.max(0)
        i0 = np.clip(np.floor((mlo - lo) / h).astype(int) - 1, 0, None)
        i1 = np.minimum(np.ceil((mhi - lo) / h).astype(int) + 1, shape)
        if np.any(i1 <= i0):
            continue
        for ax in range(3):
            a1, a2 = [k for k in range(3) if k != ax]
            occ = np.zeros(shape, bool)
            d = Vector([1.0 if k == ax else 0.0 for k in range(3)])
            start = mlo[ax] - 2.0
            span = mhi[ax] - mlo[ax] + 4.0
            for j in range(i0[a1], i1[a1]):
                for k in range(i0[a2], i1[a2]):
                    o = [0.0, 0.0, 0.0]
                    o[a1] = lo[a1] + (j + 0.5 + jit[a1] * 0.01) * h + jit[ax] * 0.01
                    o[a2] = lo[a2] + (k + 0.5 + jit[a2] * 0.01) * h + jit[a1] * 0.013
                    o[ax] = start
                    org, hits, travelled = Vector(o), [], 0.0
                    for _ in range(64):
                        loc, _n, _i, dist = bvh.ray_cast(org, d, span - travelled + 1.0)
                        if loc is None:
                            break
                        hits.append(loc[ax])
                        travelled += dist + 1e-4
                        org = loc + d * 1e-4
                    if len(hits) < 2:
                        continue
                    if len(hits) % 2:
                        hits = hits[:-1]
                    for t0, t1 in zip(hits[0::2], hits[1::2]):
                        c0 = int(math.ceil((t0 - lo[ax]) / h - 0.5))
                        c1 = int(math.floor((t1 - lo[ax]) / h - 0.5))
                        c0, c1 = max(c0, 0), min(c1, shape[ax] - 1)
                        if c1 < c0:
                            continue
                        idx = [slice(None)] * 3
                        idx[ax], idx[a1], idx[a2] = slice(c0, c1 + 1), j, k
                        occ[tuple(idx)] = True
            votes += occ
    return votes >= 2, lo, h


def _weights_top4(ob, vids, bone_index):
    import numpy as np
    n = len(vids)
    bi, bw = np.zeros((n, 4), np.int32), np.zeros((n, 4), np.float32)
    gname = {g.index: g.name for g in ob.vertex_groups}
    for r, vi in enumerate(vids):
        ws = sorted(((e.weight, gname[e.group]) for e in ob.data.vertices[vi].groups
                     if gname[e.group] in bone_index and e.weight > 1e-4), reverse=True)[:4]
        s = sum(w for w, _ in ws) or 1.0
        for c, (w, g) in enumerate(ws):
            bi[r, c], bw[r, c] = bone_index[g], w / s
    return bi, bw


def export_contact(out=CONTACT_NPZ):
    """Write contact.npz (see above). Runs in a Blender process on base.blend."""
    import bpy
    import numpy as np
    from mathutils import Matrix
    sys.path.insert(0, os.path.join(PROJECT, "scripts", "parts"))
    import common as C
    t0 = time.perf_counter()
    body, rig = C.open_base()
    names = [b.name for b in rig.data.bones]
    bone_index = {n: i for i, n in enumerate(names)}
    colls = {p: C.load_part(p, rig) for p in ("gloves", "carrier", "shirt", "armour")}
    data = {"bone_names": np.array(names)}

    bd = None

    def rest_set(key, ob, vids):
        vids = list(vids)
        if ob is body:          # the body's rest shape is its evaluated mesh (MPFB's targets are shape keys)
            V, N = bd["V"][vids], bd["N"][vids]
        else:
            V = np.array([ob.matrix_world @ ob.data.vertices[i].co for i in vids]) * 1000.0
            N = np.array([(ob.matrix_world.to_3x3() @ ob.data.vertices[i].normal).normalized() for i in vids])
        bi, bw = _weights_top4(ob, vids, bone_index)
        return V, N, bi, bw

    sets = {}

    def add(key, ob, vids, tag):
        V, N, bi, bw = rest_set(key, ob, vids)
        s = sets.setdefault(key, {"V": [], "N": [], "bi": [], "bw": [], "obj": []})
        s["V"].append(V)
        s["N"].append(N)
        s["bi"].append(bi)
        s["bw"].append(bw)
        s["obj"] += [tag] * len(vids)
    rig.data.pose_position = "REST"
    bpy.context.view_layer.update()
    bd = C.body_data(body)
    for side in "LR":
        for o in sorted(colls["gloves"].all_objects, key=lambda o: o.name):
            if o.type == "MESH" and o.name.startswith(f"Glove.{side}."):
                add(f"glove_{side}", o, range(len(o.data.vertices)), o.name)
        for o in sorted(colls["armour"].all_objects, key=lambda o: o.name):
            if o.type == "MESH" and o.name.startswith(f"Guard.{side}."):
                add(f"guard_{side}", o, range(len(o.data.vertices)), o.name)
        sh = bpy.data.objects["Shirt.Shell"]
        gi = {g.index: g.name for g in sh.vertex_groups}
        vids = []
        for v in sh.data.vertices:
            w = sum(e.weight for e in v.groups if gi[e.group].startswith(("upperarm", "lowerarm", "wrist"))
                    and gi[e.group].endswith(side))
            if w > 0.3:
                vids.append(v.index)
        add(f"sleeve_{side}", sh, vids, "Shirt.Shell")
        gb = {g.index: g.name for g in body.vertex_groups}
        bodyg = body.vertex_groups["body"].index
        vids = []
        for v in body.data.vertices:
            ws = {gb[e.group]: e.weight for e in v.groups}
            if ws.get("body", 0) < 0.5:
                continue
            w = sum(x for g, x in ws.items() if g.startswith(("wrist", "finger", "metacarpal")) and g.endswith(side))
            if w > 0.5:
                vids.append(v.index)
        add(f"skin_{side}", body, vids, "Body.Mesh")
    if os.path.exists(FACE_JSON):
        fv = json.load(open(FACE_JSON, encoding="utf-8"))["vertex_ids"]
        add("face", body, fv, "Body.Mesh")
    for k, s in sets.items():
        data[f"pts_{k}_V"] = np.concatenate(s["V"]).astype(np.float32)
        data[f"pts_{k}_N"] = np.concatenate(s["N"]).astype(np.float32)
        data[f"pts_{k}_bi"] = np.concatenate(s["bi"])
        data[f"pts_{k}_bw"] = np.concatenate(s["bw"])
        data[f"pts_{k}_obj"] = np.array(s["obj"])
    print(f"[pose] contact point sets: { {k: len(v['obj']) for k, v in sets.items()} }", flush=True)

    # the carbine, in its own frame
    with bpy.data.libraries.load(os.path.join(PROJECT, "cache", "parts", "carbine.blend"), link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == "Part.Carbine"]
    cc = dst.collections[0]
    bpy.context.scene.collection.children.link(cc)
    bpy.context.view_layer.update()
    root = bpy.data.objects["Carbine.Root"]
    Minv = root.matrix_world.inverted()
    dg = bpy.context.evaluated_depsgraph_get()
    meshes, names_c = [], []
    for o in cc.all_objects:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        M = Minv @ o.matrix_world
        V = np.array([M @ v.co for v in me.vertices]) * 1000.0
        P = [tuple(p.vertices) for p in me.polygons]
        ev.to_mesh_clear()
        meshes.append((V, P))
        names_c.append(o.name)
    t1 = time.perf_counter()
    occ, lo, h = _voxelize(meshes, CARBINE_GRID["lo"], CARBINE_GRID["hi"], CARBINE_GRID["h"])
    data.update(carbine_occ=np.packbits(occ), carbine_shape=np.array(occ.shape), carbine_lo=lo, carbine_h=h)
    for nm in ("Carbine.Stock.ButtPad", "Carbine.Grip"):
        V, _ = meshes[names_c.index(nm)]
        data[f"carbine_{nm.split('.')[-1].lower()}_V"] = V.astype(np.float32)
    print(f"[pose] carbine voxels {occ.shape} {int(occ.sum())} inside, {time.perf_counter() - t1:.1f} s", flush=True)

    # the carrier, posed now (it follows the spine), in world mm
    sys.path.insert(0, HERE)
    apply_hero_pose(rig)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    meshes = []
    for o in colls["carrier"].all_objects:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        V = np.array([o.matrix_world @ v.co for v in me.vertices]) * 1000.0
        P = [tuple(p.vertices) for p in me.polygons]
        ev.to_mesh_clear()
        if (V.max(0) < np.array(CARRIER_GRID["lo"])).any() or (V.min(0) > np.array(CARRIER_GRID["hi"])).any():
            continue
        meshes.append((V, P))
    t1 = time.perf_counter()
    occ, lo, h = _voxelize(meshes, CARRIER_GRID["lo"], CARRIER_GRID["hi"], CARRIER_GRID["h"])
    pb = rig.pose.bones[CARRIER_REF_BONE]
    Mref = np.array(rig.matrix_world @ pb.matrix)
    Mref[:3, 3] *= 1000.0
    data.update(carrier_occ=np.packbits(occ), carrier_shape=np.array(occ.shape), carrier_lo=lo, carrier_h=h,
                carrier_ref_bone=np.array(CARRIER_REF_BONE), carrier_ref_matrix_mm=Mref,
                pose_json_mtime=np.array(os.path.getmtime(HERO_JSON)))
    print(f"[pose] carrier voxels {occ.shape} {int(occ.sum())} inside, {time.perf_counter() - t1:.1f} s", flush=True)
    tmp = out + ".tmp.npz"
    np.savez_compressed(tmp, **data)
    os.replace(tmp, out)
    print(f"[pose] wrote {os.path.relpath(out, PROJECT)} in {time.perf_counter() - t0:.1f} s", flush=True)
    return 0


HAND_VIEW_COLOURS = {"Body": (0.78, 0.72, 0.66), "Glove": (0.58, 0.42, 0.64), "Carbine": (0.22, 0.22, 0.24),
                     "Carrier": (0.84, 0.62, 0.30), "Guard": (0.30, 0.68, 0.68), "Shirt": (0.44, 0.52, 0.66),
                     "Pauldron": (0.30, 0.68, 0.68), "ElbowCap": (0.30, 0.68, 0.68)}


def render_hands(assembled=os.path.join(PROJECT, "cache", "assembled.blend"), quick=False, tag=""):
    """The hands on the carbine from the assembled hero pose (cache/assembled.blend, assemble.py): Workbench,
    each hand along the hero camera's line, from the gun's right and left sides, from above and from the
    front (-Y), orthographic 200 mm; renders/pose/pose_hands<tag>_<side>_<view>.png. quick: build the
    scene here instead (base.blend, the gloves, shirt, armour and carrier caches, hero_pose.json, the carbine)."""
    import bpy
    import numpy as np
    sys.path.insert(0, os.path.join(PROJECT, "scripts", "parts"))
    sys.path.insert(0, os.path.join(PROJECT, "scripts"))
    import common as C
    from eval import camproj
    if quick:
        import assemble as A
        body, rig = C.open_base()
        for p in ("gloves", "shirt", "armour", "carrier"):
            C.load_part(p, rig)
        C.apply_hero_pose(rig)
        A.place_carbine(rig, json.load(open(HERO_JSON, encoding="utf-8")))
    else:
        bpy.ops.wm.open_mainfile(filepath=assembled)
    rig = bpy.data.objects[RIG]
    rig.data.pose_position = "POSE"
    bpy.context.view_layer.update()
    keep = [c for c in bpy.data.collections if c.name.startswith("Part.")]
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH":
            key = ob.name.split(".")[0]
            ob.color = (*HAND_VIEW_COLOURS.get(key, (0.5, 0.5, 0.5)), 1.0)
    for ob in bpy.context.scene.objects:
        if ob.name.startswith(("Scene.", "Body.Eye")):
            ob.hide_render = True
    cam_loc = np.array(camproj.HERO_LOC) * 1000.0
    outs = []
    for side in "RL":
        pb = rig.pose.bones[f"metacarpal3.{side}"]
        t = np.array(rig.matrix_world @ ((pb.head + pb.tail) / 2)) * 1000.0
        cdir = (cam_loc - t) / np.linalg.norm(cam_loc - t)
        Gm = np.array(bpy.data.objects["Carbine.Root"].matrix_world)[:3, :3] if "Carbine.Root" in bpy.data.objects else np.eye(3)
        views = (("camera", cdir), ("gun_right", -Gm[:, 1] + 0.15 * Gm[:, 2]), ("gun_left", Gm[:, 1] + 0.15 * Gm[:, 2]),
                 ("above", (0, -0.02, 1)), ("front", (0, -1, 0)))
        for name, d in views:
            d = np.asarray(d, float) / np.linalg.norm(d)
            outs.append(C.render_view("pose", keep, f"hands{tag}_{side}_{name}", t + d * 1500.0, t, 200.0, res=700))
    print("[pose] hand views:", outs, flush=True)
    return 0


def contact_stale():
    if not os.path.exists(CONTACT_NPZ):
        return True
    t = os.path.getmtime(CONTACT_NPZ)
    ins = CONTACT_INPUTS + [BASE_BLEND, os.path.abspath(__file__)] + ([FACE_JSON] if os.path.exists(FACE_JSON) else [])
    return any(os.path.exists(f) and os.path.getmtime(f) > t for f in ins)


def main(argv):
    if "--render-hands" in argv:
        return render_hands(quick="--quick" in argv, tag=argv[argv.index("--tag") + 1] if "--tag" in argv else "")
    if "--export" in argv:
        if "--if-stale" in argv and not contact_stale():
            print("[pose] contact.npz is fresh", flush=True)
            return 0
        return export_contact()
    print(__doc__)
    return 2


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    try:
        rc = main(argv)
    except Exception:
        import traceback
        traceback.print_exc()
        rc = 1
    sys.stdout.flush()
    if rc:
        os._exit(rc)
