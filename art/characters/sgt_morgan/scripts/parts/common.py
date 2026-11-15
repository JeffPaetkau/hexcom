"""Shared helpers for take 2's part scripts (round 1 on): load the body, build offset shells from it, bind a
part to Morgan.Rig, save and load a part cache, measure clearance, and render a part in rest and in the
hero pose through the matched hero camera beside the reference crop.

A part script (scripts/parts/<part>.py) runs inside Blender:

    import common as C
    body, rig = C.open_base()                      # cache/stages/base.blend, rig at rest
    bd = C.body_data(body)                         # rest vertices (m), faces, normals, bone weights
    coll = C.part_collection("Trousers")           # Part.Trousers, emptied of its old objects
    ob = C.mesh_object("Trousers.Shell", V, F, coll, mat=C.flat_material("Trousers.Mat.Camo", "#2b2925"))
    C.bind(ob, body, rig)                          # weights from Body.Mesh (Data Transfer, nearest face
                                                   # interpolated, deform bones only) + Armature modifier
    C.save_part("trousers", coll, extra)           # cache/parts/trousers.blend (+ .json), only the part's own data
    C.render_part("trousers", coll, (0, 0, 600), 1250, crops=("ref.legs_knees",))
                                                   # renders/trousers/: rest clay x3, hero render + pair per crop

Toolbox (mm arrays unless noted): submesh, refine_on_skin, limit_by_gap, convexify_along, taubin, despike,
push_out, bisect, voxel_remesh, surface_patch (pockets/panels on a limb shell), tube_along, boundary_loops;
leg_frame / leg_section / BOOT (fit numbers shared by trousers and boots); clearance (skin poke-through),
covered (one garment inside another, ray test: the right check for open shells), apply_hero_pose (round 0's
stages/pose.py, else hero_pose.json), render_rest_views, render_view, render_hero, pair_sheet.

Geometry helpers work in millimetres on numpy arrays unless a name says _m. The body is MPFB's mesh with
its helper geometry masked; body_data() keeps the original vertex indices (the mask is switched off while
reading, `in_body` marks the real skin), so bone weights can select regions.

Caches hold only the part's objects, meshes and materials: the Armature modifier's object is cleared
before writing (the rig's name is kept in the object's "sgt_armature" property) and load_part() points it
back at the scene's rig, so a cache never drags a second copy of Morgan.Rig into a scene.

    "$SGT_BLENDER" -b --python scripts/parts/common.py -- --together trousers shirt boots gloves
        loads the base body and the named part caches, poses, renders renders/round_01/clothing_hero.png
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
SCRIPTS = os.path.join(PROJECT, "scripts")
for p in (SCRIPTS, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

BASE_BLEND = os.path.join(PROJECT, "cache", "stages", "base.blend")
BASE_JSON = os.path.join(PROJECT, "cache", "stages", "base.json")
HERO_JSON = os.path.join(PROJECT, "scripts", "stages", "hero_pose.json")
PARTS_DIR = os.path.join(PROJECT, "cache", "parts")
RENDERS = os.path.join(PROJECT, "renders")
REF_DIR = os.path.join(PROJECT, "ref")
BODY, RIG = "Body.Mesh", "Morgan.Rig"
MM = 0.001

# Shared fit numbers between parts (mm). The boot is built around the rest foot with its footbed under it:
# heel seat 36, ball seat 24 (LOWA Zephyr class, take 1 spec 02 §3.1); the hero pose (round 0) lifts the
# feet onto those seats, so in the pose the soles land on the floor. In REST the boot sole is below z = 0.
BOOT = {
    "heel_seat": 36.0, "ball_seat": 24.0,       # floor -> footbed top
    "rim_h": 212.0,                             # floor -> collar rim at the sides (outside height 210)
    "shaft_rim_ab": (69.0, 53.0),               # outer half-axes at the rim: front-back, side (138 x 106)
}
BOOT["rim_z_rest"] = BOOT["rim_h"] - BOOT["heel_seat"]     # 176: the rim in the rest body's frame


def say(tag, *a):
    print(f"[{tag}]", *a, flush=True)


# --------------------------------------------------------------------------- scene and body

def open_base():
    """Open cache/stages/base.blend; the rig in rest (all pose transforms cleared). Returns (body, rig)."""
    import bpy
    bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)
    body, rig = bpy.data.objects[BODY], bpy.data.objects[RIG]
    rest_pose(rig)
    return body, rig


def rest_pose(rig):
    import bpy
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pb.location = (0.0, 0.0, 0.0)
        pb.scale = (1.0, 1.0, 1.0)
    rig.data.pose_position = "POSE"
    bpy.context.view_layer.update()


def apply_hero_pose(rig):
    """Round 0's hero pose. Uses scripts/stages/pose.py apply_hero_pose(rig) when it exists, else applies
    hero_pose.json's local quaternions and root location here. Returns a string saying which was used."""
    import bpy
    used = None
    try:
        sp = os.path.join(SCRIPTS, "stages")
        if sp not in sys.path:
            sys.path.insert(0, sp)
        from pose import apply_hero_pose as _apply   # noqa: E402
        _apply(rig)
        used = "scripts/stages/pose.py apply_hero_pose(rig)"
    except Exception as e:  # noqa: BLE001 - fall back to the JSON on any import/apply problem
        say("common", f"pose.py not usable ({type(e).__name__}: {e}); applying hero_pose.json directly")
        d = json.load(open(HERO_JSON))
        rest_pose(rig)
        for n, q in d["bones"].items():
            pb = rig.pose.bones.get(n)
            if pb is not None:
                pb.rotation_mode = "QUATERNION"
                pb.rotation_quaternion = q
        rig.pose.bones[d.get("root_bone", "root")].location = d["root_location"]
        used = "common.apply_hero_pose (hero_pose.json)"
    rig.data.pose_position = "POSE"
    bpy.context.view_layer.update()
    try:
        st = os.stat(HERO_JSON)
        import time
        used += f"; hero_pose.json of {time.strftime('%Y-%m-%d %H:%M', time.localtime(st.st_mtime))}"
    except OSError:
        pass
    return used


def base_json():
    return json.load(open(BASE_JSON))


def bone_mm(name, end="head"):
    """Rest head or tail of a bone in mm (rig space = world)."""
    import bpy
    b = bpy.data.objects[RIG].data.bones[name]
    v = b.head_local if end == "head" else b.tail_local
    return np.array(v) * 1000.0


def body_data(body):
    """The rest body as arrays (mm): V, F (list of index tuples), N (vertex normals), in_body (skin, not
    helper geometry), groups (name -> weight array). The Mask modifier is off while reading, so indices are
    Body.Mesh's own."""
    import bpy
    mask = [m for m in body.modifiers if m.type == "MASK"]
    saved = [(m, m.show_viewport) for m in mask]
    for m in mask:
        m.show_viewport = False
    try:
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = body.evaluated_get(dg)
        me = ev.to_mesh()
        n = len(me.vertices)
        V = np.empty(n * 3)
        me.vertices.foreach_get("co", V)
        N = np.empty(n * 3)
        me.vertices.foreach_get("normal", N)
        F = [tuple(p.vertices) for p in me.polygons]
        ev.to_mesh_clear()
    finally:
        for m, v in saved:
            m.show_viewport = v
    V = V.reshape(-1, 3) * 1000.0
    N = N.reshape(-1, 3)
    names = [g.name for g in body.vertex_groups]
    W = np.zeros((n, len(names)), np.float32)
    for v in body.data.vertices:
        for e in v.groups:
            W[v.index, e.group] = e.weight
    groups = {nm: W[:, i] for i, nm in enumerate(names)}
    in_body = groups["body"] > 0.5
    return {"V": V, "F": F, "N": N, "in_body": in_body, "groups": groups, "names": names}


def weight_sum(bd, test):
    """Sum of the bone weights whose group name satisfies test(name)."""
    s = np.zeros(len(bd["V"]), np.float32)
    for nm, w in bd["groups"].items():
        if test(nm):
            s += w
    return s


def is_arm(nm):
    return any(nm.startswith(p) for p in ("clavicle", "shoulder01", "upperarm", "lowerarm", "wrist", "finger",
                                          "metacarpal"))


def is_hand(nm):
    return any(nm.startswith(p) for p in ("wrist", "finger", "metacarpal"))


def is_leg(nm):
    return any(nm.startswith(p) for p in ("pelvis.", "upperleg", "lowerleg", "foot", "toe"))


def is_head(nm):
    return nm in ("head", "jaw") or nm.startswith(("neck", "oris", "tongue", "levator", "special", "eye",
                                                     "orbicularis", "oculi", "risorius", "temporalis"))


def submesh(V, F, keep):
    """Faces whose vertices are all kept, re-indexed. Returns (V', F', original index of each new vertex)."""
    keep = np.asarray(keep, bool)
    Fk = [f for f in F if keep[list(f)].all()]
    used = np.unique(np.concatenate([np.array(f) for f in Fk])) if Fk else np.zeros(0, int)
    remap = -np.ones(len(V), int)
    remap[used] = np.arange(len(used))
    return V[used].copy(), [tuple(remap[list(f)]) for f in Fk], used


def refine_on_skin(V, F, bvh, cuts=1):
    """Split every edge (bmesh subdivide, grid fill) and snap the vertices back onto the skin; returns V, F
    and the skin normal at each vertex. Gives the offset shells more vertices than MPFB's coarse legs."""
    import bmesh
    from mathutils import Vector
    bm = arrays_to_bm(V, F)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    bm.verts.index_update()
    V2, F2 = bm_to_arrays(bm)
    bm.free()
    N2 = np.zeros_like(V2)
    for i, v in enumerate(V2):
        loc, n, _i, _d = bvh.find_nearest(Vector(v))
        if loc is not None:
            V2[i] = loc
            N2[i] = n
    Ns = vertex_normals(V2, F2)
    N2 = N2 + Ns
    N2 /= np.maximum(np.linalg.norm(N2, axis=1, keepdims=True), 1e-9)
    return V2, F2, N2


def edges_of(F):
    E = set()
    for f in F:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            E.add((a, b) if a < b else (b, a))
    return np.array(sorted(E), int)


def boundary_verts(F, nv):
    cnt = {}
    for f in F:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            k = (a, b) if a < b else (b, a)
            cnt[k] = cnt.get(k, 0) + 1
    b = np.zeros(nv, bool)
    for (a, c), k in cnt.items():
        if k == 1:
            b[a] = b[c] = True
    return b


def voxel_remesh(V, F, voxel_mm=3.0, fill_holes=True):
    """Close the open boundaries (ngon fill) and voxel-remesh (Blender's Remesh modifier, OpenVDB) a mesh
    given in mm arrays: a clean manifold surface from a crumpled or self-intersecting one. Returns V, F."""
    import bpy
    import bmesh
    bm = arrays_to_bm(V, F)
    if fill_holes:
        edges = [e for e in bm.edges if e.is_boundary]
        if edges:
            bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    me = bpy.data.meshes.new("Aux.Remesh")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Aux.Remesh", me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("Remesh", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel_mm          # the mesh is in mm units here (unscaled data)
    m.adaptivity = 0.0
    m.use_smooth_shade = True
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    em = ev.to_mesh()
    V2 = np.array([tuple(v.co) for v in em.vertices])
    F2 = [tuple(p.vertices) for p in em.polygons]
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return V2, F2


def boundary_loops(F):
    """Ordered vertex loops along the open boundaries of a polygon mesh."""
    cnt = {}
    for f in F:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            k = (a, b) if a < b else (b, a)
            cnt[k] = cnt.get(k, 0) + 1
    nb = {}
    for (a, b), k in cnt.items():
        if k == 1:
            nb.setdefault(a, []).append(b)
            nb.setdefault(b, []).append(a)
    loops, seen = [], set()
    for start in nb:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [v for v in nb[cur] if v != prev and (v not in seen or (v == start and len(loop) > 2))]
            if not nxt or nxt[0] == start:
                break
            prev, cur = cur, nxt[0]
            loop.append(cur)
            seen.add(cur)
        loops.append(loop)
    return loops


def tube_along(loop_pts, outward, profile, closed=True):
    """A tube swept along a loop of points: profile is a list of (out, up) offsets (mm) around the section,
    placed with the loop's outward horizontal direction and +Z. Returns V, F (quads, outward faces when the
    profile runs counter-clockwise seen along the loop)."""
    P = np.asarray(loop_pts, float)
    O = np.asarray(outward, float)
    m, k = len(P), len(profile)
    V = []
    for i in range(m):
        for (o, u) in profile:
            V.append(P[i] + O[i] * o + np.array([0.0, 0.0, u]))
    F = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        j = (i + 1) % m
        for a in range(k):
            b = (a + 1) % k
            F.append((i * k + a, j * k + a, j * k + b, i * k + b))
    return np.array(V), F


def smooth_field(x, E, iters=10, lam=0.5, pin=None):
    """Laplacian smoothing of a per-vertex field (scalar or vector) over edges E."""
    x = np.array(x, float)
    n = len(x)
    deg = np.zeros(n)
    np.add.at(deg, E[:, 0], 1)
    np.add.at(deg, E[:, 1], 1)
    deg = np.maximum(deg, 1)
    for _ in range(iters):
        acc = np.zeros_like(x)
        np.add.at(acc, E[:, 0], x[E[:, 1]])
        np.add.at(acc, E[:, 1], x[E[:, 0]])
        avg = acc / (deg if x.ndim == 1 else deg[:, None])
        step = lam * (avg - x)
        if pin is not None:
            step[pin] = 0
        x = x + step
    return x


def despike(V, E, factor=2.5, iters=3):
    """Replace vertices that stand far off their neighbours' average (more than factor x the mean edge
    length there) by that average: removes the odd spike a bad normal leaves (MPFB's nails, folds)."""
    V = np.array(V, float)
    n = len(V)
    deg = np.zeros(n)
    np.add.at(deg, E[:, 0], 1)
    np.add.at(deg, E[:, 1], 1)
    deg = np.maximum(deg, 1)
    for _ in range(iters):
        acc = np.zeros_like(V)
        np.add.at(acc, E[:, 0], V[E[:, 1]])
        np.add.at(acc, E[:, 1], V[E[:, 0]])
        avg = acc / deg[:, None]
        el = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
        le = np.zeros(n)
        np.add.at(le, E[:, 0], el)
        np.add.at(le, E[:, 1], el)
        le /= deg
        bad = np.linalg.norm(V - avg, axis=1) > factor * np.median(le)
        if not bad.any():
            break
        V[bad] = avg[bad]
    return V


def taubin(V, E, iters=10, lam=0.5, mu=-0.53, pin=None):
    """Taubin (lambda/mu) smoothing of positions: smooths without the shrinkage plain Laplacian causes."""
    for _ in range(iters):
        V = smooth_field(V, E, 1, lam, pin)
        V = smooth_field(V, E, 1, mu, pin)
    return V


def vertex_normals(V, F):
    N = np.zeros_like(V)
    for f in F:
        p = V[list(f)]
        c = np.zeros(3)
        for i in range(len(f)):        # Newell normal of the polygon
            a, b = p[i], p[(i + 1) % len(f)]
            c += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
        for i in f:
            N[i] += c
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def hull2d(P):
    """Convex hull (counter-clockwise) of 2-D points, Andrew's monotone chain."""
    P = np.unique(np.round(P, 6), axis=0)
    if len(P) < 3:
        return P
    P = P[np.lexsort((P[:, 1], P[:, 0]))]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in P[::-1]:
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return np.array(lo[:-1] + hi[:-1])


def convexify_along(V, sel, origin, direction, slab=6.0, k=0.85, centre=None):
    """Cloth spans the body's concavities: within slabs across an axis (origin, direction, mm), move the
    selected points a fraction k of the way out to their slab's 2-D convex hull, radially from the slab's
    centre. Returns new V."""
    V = np.array(V, float)
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    e1 = np.cross(d, [0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.cross(d, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1)
    idx = np.nonzero(sel)[0]
    R = V[idx] - np.asarray(origin, float)
    t = R @ d
    Q = np.column_stack([R @ e1, R @ e2])
    bins = np.floor(t / slab).astype(int)
    for b in np.unique(bins):
        m = np.nonzero(np.abs(bins - b) <= 1)[0]          # hull from the slab and its neighbours
        own = np.nonzero(bins == b)[0]
        if len(m) < 6:
            continue
        H = hull2d(Q[m])
        if len(H) < 3:
            continue
        c = H.mean(0) if centre is None else centre
        A, B = H, np.roll(H, -1, 0)
        for j in own:
            u = Q[j] - c
            r = np.linalg.norm(u)
            if r < 1e-6:
                continue
            u /= r
            # ray c + s u against segments A + w (B - A)
            ex, ey = B[:, 0] - A[:, 0], B[:, 1] - A[:, 1]
            den = u[0] * ey - u[1] * ex
            ok = np.abs(den) > 1e-9
            ax, ay = A[:, 0] - c[0], A[:, 1] - c[1]
            sv = np.where(ok, (ax * ey - ay * ex) / np.where(ok, den, 1), -1)
            wv = np.where(ok, (ax * u[1] - ay * u[0]) / np.where(ok, den, 1), -1)
            hit = ok & (sv > 0) & (wv >= -1e-6) & (wv <= 1 + 1e-6)
            if not hit.any():
                continue
            Rh = sv[hit].max()
            if Rh > r:
                Q[j] = c + u * (r + k * (Rh - r))
    V[idx] = np.asarray(origin, float) + np.outer(t, d) + np.outer(Q[:, 0], e1) + np.outer(Q[:, 1], e2)
    return V


# --------------------------------------------------------------------------- BVH: gaps, push-out, clearance

def body_bvh(body, posed=False):
    """BVH of the evaluated Body.Mesh (helpers masked) in mm, at whatever pose the rig is in."""
    import bpy
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    V = [tuple(v.co * 1000.0) for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(V, F, all_triangles=False)


def bvh_from(V, F):
    from mathutils.bvhtree import BVHTree
    return BVHTree.FromPolygons([tuple(v) for v in V], [tuple(f) for f in F], all_triangles=False)


def skin_bvh(bd):
    """BVH (mm) of the rest skin only: faces whose vertices are all real body (no MPFB helper geometry)."""
    ib = bd["in_body"]
    return bvh_from(bd["V"], [f for f in bd["F"] if ib[list(f)].all()])


def limit_by_gap(V, N, off, bvh, share=0.5, floor=1.0):
    """Cap an outward offset where the body faces itself across a gap (crotch, armpit, between fingers):
    a ray along the normal that hits the body at distance t limits the offset to share * t - 0.3 mm."""
    from mathutils import Vector
    off = np.array(off, float)
    for i in range(len(V)):
        o = Vector(V[i] + N[i] * 0.3)
        hit = bvh.ray_cast(o, Vector(N[i]), off[i] / share + 2.0)
        if hit[0] is not None:
            off[i] = min(off[i], max(floor, share * hit[3] - 0.3))
    return off


def signed_dist(V, bvh):
    """Signed distance (mm) of points to a closed-ish surface: + outside along the face normal."""
    from mathutils import Vector
    d = np.empty(len(V))
    nrm = np.zeros((len(V), 3))
    for i, v in enumerate(V):
        loc, n, _idx, dist = bvh.find_nearest(Vector(v))
        if loc is None:
            d[i] = 1e9
            continue
        s = 1.0 if (Vector(v) - loc).dot(n) >= 0 else -1.0
        d[i] = s * dist
        nrm[i] = n
    return d, nrm


def push_out(V, bvh, clear, iters=3):
    """Move points that are closer than `clear` mm to (or inside) the surface out along its normal."""
    V = np.array(V, float)
    clear = np.broadcast_to(np.asarray(clear, float), (len(V),))
    for _ in range(iters):
        d, n = signed_dist(V, bvh)
        bad = d < clear
        if not bad.any():
            break
        V[bad] += n[bad] * (clear[bad] - d[bad])[:, None]
    return V


def evaluated_world_mm(ob, disable=("SOLIDIFY", "SUBSURF")):
    """The evaluated mesh of ob (with its Armature, without solidify/subsurf by default), world mm."""
    import bpy
    saved = [(m, m.show_viewport) for m in ob.modifiers if m.type in disable]
    for m, _ in saved:
        m.show_viewport = False
    try:
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        mw = np.array(ob.matrix_world)
        V = np.array([tuple(v.co) for v in me.vertices]) @ mw[:3, :3].T + mw[:3, 3]
        F = [tuple(p.vertices) for p in me.polygons]
        ev.to_mesh_clear()
    finally:
        for m, v in saved:
            m.show_viewport = v
    return V * 1000.0, F


def clearance(objs, body, label=""):
    """How far the parts' outer surfaces sit outside the body (mm), at the rig's current pose. A negative
    minimum means skin pokes through the garment there. Returns a dict per object."""
    bvh = body_bvh(body)
    out = {}
    for ob in objs:
        if ob.type != "MESH":
            continue
        V, _F = evaluated_world_mm(ob)
        d, _ = signed_dist(V, bvh)
        out[ob.name] = {"min_mm": round(float(d.min()), 2), "p01_mm": round(float(np.percentile(d, 1)), 2),
                        "inside": int((d < 0).sum()), "under_1mm": int((d < 1.0).sum()), "verts": len(d),
                        "min_at_mm": [round(float(x)) for x in V[int(np.argmin(d))]]}
    say("clearance", label, json.dumps(out))
    return out


def clearance_between(outer, inner, label="", within=None):
    """How far `outer`'s surface sits outside `inner`'s (both evaluated, current pose): layering checks such
    as trouser cuff over boot shaft. inner is used as the reference surface. within (mm): only the outer
    vertices that lie within this distance of the inner surface's bounding box (the overlap zone)."""
    Vi, Fi = evaluated_world_mm(inner)
    bvh = bvh_from(Vi, Fi)
    Vo, _ = evaluated_world_mm(outer)
    if within is not None:
        lo, hi = Vi.min(0) - within, Vi.max(0) + within
        Vo = Vo[np.all((Vo > lo) & (Vo < hi), axis=1)]
    if not len(Vo):
        return {"min_mm": None, "inside": 0, "verts": 0}
    d, _ = signed_dist(Vo, bvh)
    r = {"min_mm": round(float(d.min()), 2), "inside": int((d < 0).sum()), "verts": len(d),
         "min_at_mm": [round(float(x)) for x in Vo[int(np.argmin(d))]]}
    say("layering", label, outer.name, "over", inner.name, json.dumps(r))
    return r


def covered(inner, outer, select_rest=None, reach=60.0, label="", outward_only=True):
    """Is `inner` covered by `outer` (current pose)? For each inner vertex (optionally only those whose REST
    position satisfies select_rest(V_rest_mm) -> bool mask), a ray outward along its normal must hit
    outer within `reach` mm. Reports the uncovered count, which is what poke-through of one garment
    through another means for open shells."""
    from mathutils import Vector
    Vi, Fi = evaluated_world_mm(inner)
    Ni = vertex_normals(Vi, Fi)
    Vo, Fo = evaluated_world_mm(outer)
    bvh = bvh_from(Vo, Fo)
    sel = np.ones(len(Vi), bool)
    if select_rest is not None:
        R = np.array([tuple(v.co) for v in inner.data.vertices]) * 1000.0
        sel = np.asarray(select_rest(R), bool)
    if outward_only and sel.any():            # only the faces looking away from the selection's centre
        c = Vi[sel].mean(0)
        sel &= np.einsum("ij,ij->i", Ni, Vi - c) > 0.0
    idx = np.nonzero(sel)[0]
    miss = []
    for i in idx:
        hit = bvh.ray_cast(Vector(Vi[i] - Ni[i] * 0.5), Vector(Ni[i]), reach)
        if hit[0] is None:
            miss.append(i)
    r = {"checked": int(len(idx)), "uncovered": len(miss),
         "uncovered_at_mm": [[round(float(x)) for x in Vi[j]] for j in miss[:3]]}
    say("covered", label, inner.name, "under", outer.name, json.dumps(r))
    return r


# --------------------------------------------------------------------------- objects, materials, bind

def part_collection(part, name=None):
    """Collection Part.<Part> (or `name`) linked to the scene, with every object named <Part>.* removed
    first (e.g. part_collection("Boot", "Part.Boots") owns Boot.L.Sole)."""
    import bpy
    name = name or f"Part.{part}"
    for ob in list(bpy.data.objects):
        if ob.name.startswith(part + "."):
            bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.name.startswith(part + ".") and me.users == 0:
            bpy.data.meshes.remove(me)
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def hex_rgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def flat_material(name, hexcol, rough=0.8, sheen=0.0):
    """A flat Principled material (round 1: one colour per component, sampled from the reference); the
    viewport colour is set too, so Workbench MATERIAL renders show it."""
    import bpy
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    rgb = hex_rgb(hexcol)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = sheen
    m.diffuse_color = (*rgb, 1.0)
    m.roughness = rough
    m["sgt_hex"] = hexcol
    return m


def mesh_object(name, V_mm, F, coll, mat=None, smooth=True, mats=None, face_mat=None):
    """A mesh object from mm vertices and polygon tuples, linked to coll. mats/face_mat: several materials
    and a per-face material index."""
    import bpy
    me = bpy.data.meshes.get(name)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    me.from_pydata((np.asarray(V_mm) * MM).tolist(), [], [list(f) for f in F])
    me.validate(clean_customdata=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    for m in (mats or ([mat] if mat else [])):
        me.materials.append(m)
    if face_mat is not None and len(face_mat) == len(me.polygons):
        me.polygons.foreach_set("material_index", np.asarray(face_mat, np.int32))
    if smooth:
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    return ob


def bm_to_arrays(bm):
    bm.verts.ensure_lookup_table()
    V = np.array([tuple(v.co) for v in bm.verts])
    F = [tuple(v.index for v in f.verts) for f in bm.faces]
    return V, F


def arrays_to_bm(V, F):
    import bmesh
    bm = bmesh.new()
    vs = [bm.verts.new(tuple(v)) for v in V]
    for f in F:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bm.verts.index_update()
    return bm


def bisect(V, F, plane_co, plane_no, keep="below", extra=None):
    """Cut a mesh (mm arrays) with a plane and keep the side opposite the normal ("below") or along it.
    extra: per-vertex arrays (n, k) interpolated onto the new vertices. Returns V, F[, extra]."""
    import bmesh
    no = np.asarray(plane_no, float)
    if keep != "below":
        no = -no
    bm = arrays_to_bm(V, F)
    lay = None
    if extra is not None:
        extra = np.atleast_2d(np.asarray(extra, float).T).T
        lay = [bm.verts.layers.float.new(f"x{k}") for k in range(extra.shape[1])]
        bm.verts.ensure_lookup_table()
        for i, v in enumerate(bm.verts):
            for k, L in enumerate(lay):
                v[L] = float(extra[i, k])
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4,
                           plane_co=tuple(plane_co), plane_no=tuple(no), clear_outer=True)
    bm.verts.index_update()
    Vn, Fn = bm_to_arrays(bm)
    if lay is not None:
        ex = np.array([[v[L] for L in lay] for v in bm.verts])
        bm.free()
        return Vn, Fn, ex
    bm.free()
    return Vn, Fn


def add_mod(ob, kind, name=None, **props):
    m = ob.modifiers.get(name or kind.title()) or ob.modifiers.new(name or kind.title(), kind)
    for k, v in props.items():
        setattr(m, k, v)
    return m


def solidify(ob, thickness_mm, inward=True, even=False):
    """Solidify (thickness in mm, grown inward by default). Even offset stays off unless asked: on thin or
    folded regions (fingertips, a toe box) it throws long spikes."""
    return add_mod(ob, "SOLIDIFY", "Solidify", thickness=thickness_mm * MM, offset=-1.0 if inward else 1.0,
                   use_even_offset=even, use_quality_normals=True, use_rim=True)


def subsurf(ob, levels=1):
    return add_mod(ob, "SUBSURF", "Subdivision", levels=levels, render_levels=levels, quality=3)


def bind(ob, body, rig, collapse=None, only=None):
    """Weights from Body.Mesh by a Data Transfer modifier (vertex groups, nearest face interpolated, deform
    bones only; source evaluated at rest with the helpers masked), applied; then an Armature modifier on
    Morgan.Rig at the top of the stack. collapse: {group-name prefix or name: target group} merged after
    the transfer (e.g. toes into the foot for a rigid sole). only: keep just these groups (renormalised)."""
    import bpy
    pp = rig.data.pose_position
    rig.data.pose_position = "REST"
    bpy.context.view_layer.update()
    deform = [b.name for b in rig.data.bones if b.use_deform]
    for n in deform:
        if n in body.vertex_groups and n not in ob.vertex_groups:
            ob.vertex_groups.new(name=n)
    m = ob.modifiers.new("Bind.Transfer", "DATA_TRANSFER")
    m.object = body
    m.use_vert_data = True
    m.data_types_verts = {"VGROUP_WEIGHTS"}
    m.vert_mapping = "POLYINTERP_NEAREST"
    m.layers_vgroup_select_src = "ALL"
    m.layers_vgroup_select_dst = "NAME"
    m.mix_mode = "REPLACE"
    m.mix_factor = 1.0
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0)
        bpy.ops.object.modifier_apply(modifier=m.name)
    rig.data.pose_position = pp
    for g in list(ob.vertex_groups):
        if g.name not in deform:
            ob.vertex_groups.remove(g)
    # gather weights, collapse, normalise, drop empty groups
    names = [g.name for g in ob.vertex_groups]
    W = np.zeros((len(ob.data.vertices), len(names)), np.float32)
    for v in ob.data.vertices:
        for e in v.groups:
            W[v.index, e.group] = e.weight
    if collapse:
        for src, dst in collapse.items():
            if dst not in names:
                ob.vertex_groups.new(name=dst)
                names.append(dst)
                W = np.concatenate([W, np.zeros((len(W), 1), np.float32)], 1)
            j = names.index(dst)
            for i, nm in enumerate(names):
                if i != j and (nm == src or (src.endswith("*") and nm.startswith(src[:-1]))):
                    W[:, j] += W[:, i]
                    W[:, i] = 0
    if only:
        for i, nm in enumerate(names):
            if nm not in only:
                W[:, i] = 0
    s = W.sum(1, keepdims=True)
    W = np.where(s > 1e-6, W / np.maximum(s, 1e-6), W)
    for i, nm in enumerate(names):
        g = ob.vertex_groups[nm]
        col = W[:, i]
        if not (col > 1e-4).any():
            ob.vertex_groups.remove(g)
            continue
        g.remove(list(range(len(col))))
        for val in np.unique(np.round(col[col > 1e-4], 4)):
            idx = np.nonzero(np.abs(np.round(col, 4) - val) < 1e-9)[0].tolist()
            g.add(idx, float(val), "REPLACE")
    arm = ob.modifiers.new("Armature", "ARMATURE")
    arm.object = rig
    arm.use_vertex_groups = True
    arm.use_bone_envelopes = False
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.modifier_move_to_index(modifier=arm.name, index=0)
    ob.parent = rig
    ob.matrix_parent_inverse = rig.matrix_world.inverted()
    return arm


# --------------------------------------------------------------------------- caches

def save_part(part, coll, extra=None):
    """Write cache/parts/<part>.blend with only the collection, its objects, meshes and materials (the
    Armature modifiers' object and the rig parent are cleared while writing and restored after)."""
    import bpy
    os.makedirs(PARTS_DIR, exist_ok=True)
    path = os.path.join(PARTS_DIR, f"{part}.blend")
    saved = []
    for ob in coll.all_objects:
        for m in ob.modifiers:
            if m.type == "ARMATURE" and m.object is not None:
                ob["sgt_armature"] = m.object.name
                saved.append(("mod", m, m.object))
                m.object = None
        if ob.parent is not None and ob.parent.type == "ARMATURE":
            ob["sgt_parent"] = ob.parent.name
            saved.append(("parent", ob, ob.parent, ob.matrix_parent_inverse.copy()))
            mw = ob.matrix_world.copy()
            ob.parent = None
            ob.matrix_world = mw
    try:
        ids = {coll, *coll.all_objects}
        tmp = path + ".tmp.blend"
        bpy.data.libraries.write(tmp, ids, path_remap="NONE", fake_user=True, compress=False)
        os.replace(tmp, path)
    finally:
        for s in saved:
            if s[0] == "mod":
                s[1].object = s[2]
            else:
                mw = s[1].matrix_world.copy()
                s[1].parent = s[2]
                s[1].matrix_parent_inverse = s[3]
                s[1].matrix_world = mw
    if extra is not None:
        with open(os.path.join(PARTS_DIR, f"{part}.json"), "w") as f:
            json.dump(extra, f, indent=1)
    say(part, "saved", path)
    return path


def load_part(part, rig=None):
    """Append Part.<Part> from cache/parts/<part>.blend into the open scene and point its Armature
    modifiers (and rig parents) at the scene's rig. Returns the collection."""
    import bpy
    path = os.path.join(PARTS_DIR, f"{part}.blend")
    rig = rig or bpy.data.objects.get(RIG)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c.startswith("Part.")]
    for c in dst.collections:
        if c.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(c)
        for ob in c.all_objects:
            for m in ob.modifiers:
                if m.type == "ARMATURE" and m.object is None:
                    m.object = bpy.data.objects.get(ob.get("sgt_armature", RIG)) or rig
            if ob.get("sgt_parent") and ob.parent is None:
                mw = ob.matrix_world.copy()
                ob.parent = bpy.data.objects.get(ob["sgt_parent"]) or rig
                ob.matrix_parent_inverse = ob.parent.matrix_world.inverted()
                ob.matrix_world = mw
    return dst.collections[0] if dst.collections else None


# --------------------------------------------------------------------------- rendering

SKIN_CLAY = (0.78, 0.72, 0.66)
SKIN_FLAT = "#b08a74"


def _workbench(sc, color_type, bg=(0.82, 0.82, 0.8), transparent=False):
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = color_type
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.cavity_ridge_factor = 1.0
    sh.cavity_valley_factor = 1.0
    sh.show_object_outline = False
    sh.show_specular_highlight = True
    sh.show_shadows = False
    sc.display.render_aa = "16"
    if sc.world is None:
        import bpy
        sc.world = bpy.data.worlds.new("Aux.World")
    sc.world.color = bg
    sc.render.film_transparent = transparent
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"


def _aux_camera():
    import bpy
    cam = bpy.data.objects.get("Aux.Cam")
    if cam is None:
        cam = bpy.data.objects.new("Aux.Cam", bpy.data.cameras.new("Aux.Cam"))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.sensor_width, cam.data.sensor_fit = 36.0, "HORIZONTAL"
    cam.data.clip_start, cam.data.clip_end = 0.01, 100.0
    cam.data.shift_x = cam.data.shift_y = 0.0
    return cam


def _look(cam, pos_mm, target_mm):
    from mathutils import Vector
    pos, tgt = Vector(pos_mm) * MM, Vector(target_mm) * MM
    q = (tgt - pos).to_track_quat("-Z", "Y")
    cam.matrix_world = q.to_matrix().to_4x4()
    cam.location = pos


def _render(path):
    import bpy
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    say("render", path)
    return path


def visible_only(keep_colls, keep_body=True):
    """Hide every object except the body (optional) and the given collections' objects; returns a restore
    function."""
    import bpy
    keep = set()
    for c in keep_colls:
        keep |= {o.name for o in c.all_objects}
    if keep_body:
        keep |= {BODY, "Body.Eyes", "Body.Eyebrows", "Body.Eyelashes"}
    saved = []
    for ob in bpy.context.scene.objects:
        if ob.type in ("MESH", "CURVE", "EMPTY", "ARMATURE", "FONT"):
            saved.append((ob, ob.hide_render))
            ob.hide_render = ob.name not in keep
    return lambda: [setattr(o, "hide_render", h) for o, h in saved]


def render_rest_views(part, colls, target_mm, size_mm, clay=None, out_dir=None, views=("front", "side", "threequarter")):
    """Workbench clay renders of the part on the rest body: front (from -Y), side (from his right, -X),
    three-quarter (front-right, perspective). target_mm: view centre; size_mm: the frame's height (a
    portrait 3:4 frame) or (width, height) in mm."""
    import bpy
    sc = bpy.context.scene
    out_dir = out_dir or os.path.join(RENDERS, part)
    restore = visible_only(colls)
    _workbench(sc, "OBJECT", bg=(0.86, 0.86, 0.84))
    bpy.data.objects[BODY].color = (*SKIN_CLAY, 1.0)
    for c in colls:
        for ob in c.all_objects:
            col = ob.get("sgt_clay") or clay or (0.45, 0.47, 0.5)
            ob.color = (*col, 1.0)
    cam = _aux_camera()
    sc.camera = cam
    t = np.asarray(target_mm, float)
    fw, fh = (size_mm * 0.75, size_mm) if np.isscalar(size_mm) else size_mm
    px = 1200.0 / max(fw, fh)
    sc.render.resolution_x, sc.render.resolution_y = int(round(fw * px)), int(round(fh * px))
    out = []
    for v in views:
        if v == "front":
            cam.data.type, cam.data.ortho_scale = "ORTHO", max(fw, fh) * MM
            _look(cam, t + [0, -4000, 0], t)
        elif v == "side":
            cam.data.type, cam.data.ortho_scale = "ORTHO", max(fw, fh) * MM
            _look(cam, t + [-4000, 0, 0], t)
        else:
            cam.data.type, cam.data.lens = "PERSP", 85.0
            d = max(fw, fh) * 85.0 / 36.0 * 1.05
            _look(cam, t + np.array([-0.62, -0.78, 0.18]) * d, t)
        cam.data.sensor_fit = "AUTO"
        sc.render.resolution_percentage = 100
        out.append(_render(os.path.join(out_dir, f"{part}_rest_{v}.png")))
    restore()
    return out


def render_view(part, colls, name, eye_mm, target_mm, ortho_mm, res=900, clay=None):
    """One extra Workbench clay view of the part on the body at the current pose (orthographic, looking
    from eye_mm at target_mm), written to renders/<part>/<part>_<name>.png."""
    import bpy
    sc = bpy.context.scene
    restore = visible_only(colls)
    _workbench(sc, "OBJECT", bg=(0.86, 0.86, 0.84))
    bpy.data.objects[BODY].color = (*SKIN_CLAY, 1.0)
    for c in colls:
        for ob in c.all_objects:
            ob.color = (*(ob.get("sgt_clay") or clay or (0.45, 0.47, 0.5)), 1.0)
    cam = _aux_camera()
    sc.camera = cam
    cam.data.type, cam.data.ortho_scale, cam.data.sensor_fit = "ORTHO", ortho_mm * MM, "AUTO"
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    _look(cam, eye_mm, target_mm)
    out = _render(os.path.join(RENDERS, part, f"{part}_{name}.png"))
    restore()
    return out


def _load_px(path):
    import bpy
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1]          # top row first


def _save_px(arr, path):
    import bpy
    arr = np.ascontiguousarray(arr[::-1], np.float32)
    h, w = arr.shape[:2]
    img = bpy.data.images.new("Aux.Sheet", w, h, alpha=True)
    img.pixels.foreach_set(arr.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    say("sheet", path)


def _fit(a, h, w):
    """Nearest-neighbour resize (enough for a contact sheet)."""
    ys = (np.arange(h) * a.shape[0] / h).astype(int)
    xs = (np.arange(w) * a.shape[1] / w).astype(int)
    return a[ys][:, xs]


def pair_sheet(ref_png, render_png, out_png, bg=(0.16, 0.16, 0.17)):
    """[reference crop | render on a flat background | render over the reference at 60 %]."""
    ref = _load_px(ref_png)
    rnd = _load_px(render_png)
    h, w = rnd.shape[:2]
    if ref.shape[:2] != (h, w):
        ref = _fit(ref, h, w)
    a = rnd[..., 3:4]
    solo = rnd[..., :3] * a + np.array(bg) * (1 - a)
    over = rnd[..., :3] * a * 0.6 + ref[..., :3] * (1 - 0.6 * a)
    gap = np.ones((h, 10, 3), np.float32)
    sheet = np.concatenate([ref[..., :3], gap, solo, gap, over], 1)
    sheet = np.concatenate([sheet, np.ones((h, sheet.shape[1], 1), np.float32)], 2)
    _save_px(sheet, out_png)
    return out_png


def render_hero(colls, preset_id, out_png, pair_png=None, percent=100):
    """The visible collections on the posed body through the matched hero camera (scripts/eval/camera.py
    preset, equivalent crop camera), Workbench with the flat material colours, transparent background;
    then a sheet beside the preset's reference crop. The rig must already be posed."""
    import bpy
    from eval import camera as CAM
    sc = bpy.context.scene
    restore = visible_only(colls)
    reg = CAM.load_registry()
    p = reg.get(preset_id)
    CAM.apply(p, sc, mode="equiv", percent=percent)
    _workbench(sc, "MATERIAL", transparent=True)
    body = bpy.data.objects[BODY]
    skin = flat_material("Aux.Skin", SKIN_FLAT, 0.6)
    if not body.data.materials:
        body.data.materials.append(skin)
    _render(out_png)
    restore()
    if pair_png:
        ref = os.path.join(PROJECT, p["compare"][0])
        pair_sheet(ref, out_png, pair_png)
    return out_png


def render_part(part, coll, rest_target_mm, rest_size_mm, crops=("ref.soldier_full",), clay=None):
    """The round's standard set for one part: rest clay front/side/three-quarter, then the hero pose through
    the hero camera for each crop preset (render + pair sheet). Returns the pose source string."""
    import bpy
    rig = bpy.data.objects[RIG]
    rest_pose(rig)
    render_rest_views(part, [coll], rest_target_mm, rest_size_mm, clay=clay)
    used = apply_hero_pose(rig)
    out = os.path.join(RENDERS, part)
    for pid in crops:
        lab = pid.split(".", 1)[1]
        render_hero([coll], pid, os.path.join(out, f"{part}_hero_{lab}.png"),
                    os.path.join(out, f"{part}_hero_{lab}_pair.png"))
    return used


# --------------------------------------------------------------------------- leg frames (trousers and boots)

def leg_axis_point(side, z):
    """A point on the rest leg's bone chain (hip -> knee -> ankle) at height z (mm), and the chain's unit
    direction there (downward)."""
    s = side
    hip, knee = bone_mm(f"upperleg01.{s}"), bone_mm(f"lowerleg01.{s}")
    ankle = bone_mm(f"foot.{s}")
    if z >= knee[2]:
        a, b = hip, knee
    else:
        a, b = knee, ankle
    t = (z - a[2]) / (b[2] - a[2])
    d = (b - a) / np.linalg.norm(b - a)
    return a + t * (b - a), d


def leg_frame(side, z):
    """Bone-chain point a, downward direction d, front f (towards -Y) and outward lateral l at height z."""
    a, d = leg_axis_point(side, z)
    f = np.array([0.0, -1.0, 0.0]) - d * (-d[1])
    f /= np.linalg.norm(f)
    lat = np.cross(d, f)
    lat /= np.linalg.norm(lat)
    if lat[0] * (1.0 if side == "L" else -1.0) < 0:
        lat = -lat
    return a, d, f, lat


def surface_patch(shell_bvh, frame_fn, theta0, zc, w, h, depth, edge=10.0, nu=24, nv=28, lift=1.0, tilt=0.0):
    """A pocket or panel as a sheet lying on a garment shell: a (2w x 2h mm) grid in arc length around and
    height along a limb frame, each point found by a ray from the limb axis to the shell, raised by
    lift + depth x a pillow profile (flat top, `edge` mm rounded falloff to the outline). frame_fn(z) ->
    (a, d, f, l) as leg_frame. tilt: degrees the patch's vertical rotates about its centre. Returns V, F."""
    from mathutils import Vector
    a0, _d0, f0, l0 = frame_fn(zc)
    dir0 = math.cos(math.radians(theta0)) * f0 + math.sin(math.radians(theta0)) * l0
    hit = shell_bvh.ray_cast(Vector(a0), Vector(dir0), 1000.0)
    r0 = hit[3] if hit[0] is not None else 80.0
    us = np.linspace(-w, w, nu + 1)
    vs = np.linspace(-h, h, nv + 1)
    V = []
    ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    for v in vs:
        for u in us:
            uu, vv = ct * u - st * v, st * u + ct * v
            a, _d, f, l = frame_fn(zc + vv)
            ang = math.radians(theta0) + uu / r0
            dr = math.cos(ang) * f + math.sin(ang) * l
            hit = shell_bvh.ray_cast(Vector(a), Vector(dr), 1000.0)
            if hit[0] is None:
                p, n = a + dr * r0, dr
            else:
                p, n = np.array(hit[0]), np.array(hit[1])
                if n.dot(dr) < 0:
                    n = -n
                n = 0.5 * n + 0.5 * dr
                n /= np.linalg.norm(n)
            du = max(0.0, abs(u) - (w - edge)) / edge
            dv = max(0.0, abs(v) - (h - edge)) / edge
            q = min(1.0, math.hypot(du, dv))
            prof = math.cos(q * math.pi / 2.0) ** 0.7
            V.append(p + n * (lift + depth * prof))
    V = np.array(V)
    F = []
    for j in range(nv):
        for i in range(nu):
            k = j * (nu + 1) + i
            F.append((k, k + 1, k + nu + 2, k + nu + 1))
    c = F[(nv // 2) * nu + nu // 2]
    nrm = np.cross(V[c[1]] - V[c[0]], V[c[3]] - V[c[0]])
    if nrm.dot(dir0) < 0:
        F = [tuple(reversed(f)) for f in F]
    return V, F


def leg_section(bd, side, z, half=6.0, keep=None):
    """Centroid (x, y) and half-extents (x, y) of the leg skin within a horizontal slab around z (mm)."""
    V = bd["V"]
    sel = bd["in_body"] & (np.abs(V[:, 2] - z) < half)
    sel &= (V[:, 0] > 0) if side == "L" else (V[:, 0] < 0)
    sel &= weight_sum(bd, is_leg) > 0.5
    if keep is not None:
        sel &= keep
    P = V[sel]
    if len(P) < 4:
        return None
    lo, hi = P[:, :2].min(0), P[:, :2].max(0)
    return {"c": (lo + hi) / 2.0, "half": (hi - lo) / 2.0, "n": int(len(P))}


# --------------------------------------------------------------------------- CLI: all parts together

def together(parts, out_png=None, preset="ref.soldier_full"):
    import bpy
    body, rig = open_base()
    colls = [load_part(p, rig) for p in parts]
    used = apply_hero_pose(rig)
    say("together", "pose:", used)
    out_png = out_png or os.path.join(RENDERS, "round_01", "clothing_hero.png")
    raw = out_png.replace(".png", "_render.png")
    render_hero([c for c in colls if c], preset, raw, out_png)
    for extra in ("ref.torso_vest", "ref.hands_rifle", "ref.legs_knees", "ref.boots_feet"):
        lab = extra.split(".", 1)[1]
        render_hero([c for c in colls if c], extra, out_png.replace(".png", f"_{lab}_render.png"),
                    out_png.replace(".png", f"_{lab}.png"))
    # clearance of every part on the posed body
    objs = [o for c in colls if c for o in c.all_objects]
    rep = clearance(objs, body, "posed, all parts")
    lay = {}
    ob = bpy.data.objects.get
    for sd in "LR":
        if ob(f"Boot.{sd}.Upper") and ob("Trousers.Shell"):
            # the boot shaft's top 16 mm and its collar must be inside the trouser hem
            lay[f"Boot.{sd}.Upper top under trousers"] = covered(ob(f"Boot.{sd}.Upper"), ob("Trousers.Shell"),
                                                                 lambda R: R[:, 2] > BOOT["rim_z_rest"] - 16, label="posed")
            lay[f"Boot.{sd}.Collar under trousers"] = covered(ob(f"Boot.{sd}.Collar"), ob("Trousers.Shell"), label="posed")
        if ob(f"Glove.{sd}.Shell") and ob("Shirt.Shell"):
            wr = bone_mm(f"wrist.{sd}")
            el = bone_mm(f"lowerarm01.{sd}")
            d = (wr - el) / np.linalg.norm(wr - el)
            sg = 1.0 if sd == "L" else -1.0
            lay[f"sleeve {sd} end under glove cuff"] = covered(
                ob("Shirt.Shell"), ob(f"Glove.{sd}.Shell"),
                lambda R, wr=wr, d=d, sg=sg: (np.sign(R[:, 0]) == sg) & ((R - wr) @ d > -35.0), label="posed")
    if ob("Shirt.Shell") and ob("Trousers.Shell"):
        lay["shirt tail under trousers"] = covered(ob("Shirt.Shell"), ob("Trousers.Shell"),
                                                   lambda R: (R[:, 2] < 1035.0) & (np.abs(R[:, 0]) < 260), label="posed")
    if ob("Shirt.Shell") and ob("Shirt.Gaiter"):
        lay["collar under gaiter"] = covered(ob("Shirt.Shell"), ob("Shirt.Gaiter"),
                                             lambda R: (R[:, 2] > 1530.0) & (np.abs(R[:, 0]) < 80.0), label="posed")
    with open(out_png.replace(".png", ".json"), "w") as f:
        json.dump({"pose": used, "parts": parts, "clearance_posed": rep, "layering_posed": lay}, f, indent=1)
    return out_png


def _argv():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


if __name__ == "__main__":
    a = _argv()
    if a and a[0] == "--together":
        together(a[1:] or ["trousers", "shirt", "boots", "gloves"])
