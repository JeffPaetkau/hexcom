"""The toenail plates of spec 01 §4.4: Foot.<S>.Nail.<k>, one shell per nail, made from the sculpted nail
beds of Body.Mesh (the faces of MPFB's `toenails` group, 20 per nail).

Each plate is the bed's faces lifted 0.35 mm off the bed (which pass B sank 0.4 mm), with its proximal end
and sides sunk 0.9 mm into the skin over their last 2.5 mm, so the plate emerges from under the cuticle and
its lateral grooves as a real nail does and only the free edge shows an edge (on a 4 mm mesh the folds
cannot overlap a plate, so the plate dives under them instead); the free edge is extruded past the
hyponychium by §3.3's length, bent 0.3 mm down, its corners rounded. Solidify gives the thickness, Bevel
rounds the rim and Subdivision smooths it. A plate rides its toe's distal bone (bone parenting with the
inverse set, so it stays where it was built).
"""
import math

import numpy as np

from lib import sculpt as S

# §3.3: width x visible length (from the proximal fold to the free edge's tip), free edge, thickness (mm)
PLATES = {1: (17.0, 16.0, 1.5, 1.1), 2: (11.0, 10.0, 1.2, 0.8), 3: (10.0, 9.0, 1.0, 0.7),
          4: (9.0, 8.0, 1.0, 0.7), 5: (7.0, 6.0, 0.8, 0.9)}
LIFT_MM = 0.35       # off the sunk bed (§4.4)
BURY_MM, BURY_LEN_MM = 0.9, 2.5  # the proximal end and sides sunk under the folds, over their last 2.5 mm
ARCH_MM = 0.6        # the plate's centre line raised a little more: a toenail is curved across (§3.3)
CORNER_MM = 0.35     # the straight-cut nail's rounded corners
DISTAL_BONE = {1: "toe1-2", 2: "toe2-3", 3: "toe3-3", 4: "toe4-3", 5: "toe5-3"}
# how much of the tip's downward slope a free edge follows: the small nails' beds curve steeply at the
# tip, and a straighter edge stood off them as a ledge
EDGE_SLOPE = {1: 0.3, 2: 0.6, 3: 0.6, 4: 0.6, 5: 0.6}


def bed_length(k):
    """The bed's length along the toe: the plate's visible length less its free edge."""
    w, vis, fe, t = PLATES[k]
    return vis - fe


def nail_faces(ob, co, side, toe_w, nail_w):
    """{toe: polygon indices} of one side's nail beds: faces whose corners all lie in `toenails`, given to
    the toe whose deform groups hold them."""
    me = ob.data
    ls, lt, lv = S.topology(me)
    s = 1.0 if side == "L" else -1.0
    out = {k: [] for k in PLATES}
    in_nail = nail_w > 0.5
    for p in range(len(ls)):
        vs = lv[ls[p]:ls[p] + lt[p]]
        if not in_nail[vs].all() or s * co[vs, 0].mean() <= 0:
            continue
        k = max(PLATES, key=lambda kk: toe_w[kk][vs].sum())
        out[k].append(p)
    return out


def build_plate(name, ob, co_m, faces, axis_w, thickness, free_edge, slope=0.3):
    """A plate mesh (metres, world) from bed faces: lifted, tucked, its free edge extruded; returns the
    bpy mesh and the plate's measurements (mm)."""
    import bmesh
    import bpy
    me_src = ob.data
    ls, lt, lv = S.topology(me_src)
    verts = sorted({int(v) for p in faces for v in lv[ls[p]:ls[p] + lt[p]]})
    local = {v: i for i, v in enumerate(verts)}
    P = co_m[verts].copy()
    polys = [[local[int(v)] for v in lv[ls[p]:ls[p] + lt[p]]] for p in faces]
    # the bed's normal (area-weighted, outward as the body's winding is) and its axes
    nrm = np.zeros(3)
    for poly in polys:
        for i in range(1, len(poly) - 1):
            nrm += np.cross(P[poly[i]] - P[poly[0]], P[poly[i + 1]] - P[poly[0]])
    nrm /= np.linalg.norm(nrm)
    a = np.asarray(axis_w, float)
    a = a - (a @ nrm) * nrm
    a /= np.linalg.norm(a)
    b = np.cross(nrm, a)
    c = P.mean(axis=0)
    t = (P - c) @ a
    tmin = t.min()
    span = t.max() - tmin
    # lift off the bed; the proximal end and the sides dive under the folds, the free edge's end stays up
    P += LIFT_MM / 1000.0 * nrm
    count = {}
    for poly in polys:
        for i, j in zip(poly, poly[1:] + poly[:1]):
            e = (min(i, j), max(i, j))
            count[e] = count.get(e, 0) + 1
    rim = sorted({i for e, n_ in count.items() if n_ == 1 for i in e if t[i] < tmin + 0.8 * span})
    d = np.min(np.linalg.norm(P[:, None, :] - P[rim][None, :, :], axis=2), axis=1) if rim else np.full(len(P), 1.0)
    sink = np.clip(1.0 - d / (BURY_LEN_MM / 1000.0), 0.0, 1.0)
    sink *= 1.0 - np.clip((t - (tmin + 0.7 * span)) / (0.25 * span), 0.0, 1.0)
    P -= (BURY_MM / 1000.0 * sink)[:, None] * nrm
    across = (P - c) @ b
    half = max(float(np.abs(across).max()), 1e-6)
    P += (ARCH_MM / 1000.0 * (1.0 - (across / half) ** 2))[:, None] * nrm  # curved across, highest on the axis
    bm = bmesh.new()
    bv = [bm.verts.new(p) for p in P]
    for poly in polys:
        bm.faces.new([bv[i] for i in poly])
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    # the distal boundary: boundary edges across the toe in the distal half; the free edge carries on between
    # the plate's own slope there and the toe's axis (a bent lip read as a chisel tip; the slope alone, short)
    distal = []
    for e in bm.edges:
        if not e.is_boundary:
            continue
        p0, p1 = (np.array(v.co) for v in e.verts)
        d = (p1 - p0) / max(np.linalg.norm(p1 - p0), 1e-12)
        mid = ((p0 + p1) / 2.0 - c) @ a
        if abs(d @ a) < 0.6 and mid > tmin + 0.5 * span:
            distal.append(e)
    if not distal:
        raise RuntimeError(f"{name}: found no free edge on its bed")
    ext = bmesh.ops.extrude_edge_only(bm, edges=distal)
    new = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    SLOPE = slope
    for v in new:
        # along the bed's distal slope: from the row behind the free edge to the edge itself
        e = [ed for ed in v.link_edges if ed.other_vert(v) not in new]
        prev = np.array(e[0].other_vert(v).co) if e else np.array(v.co) - a * 1e-3
        step = np.array(v.co) - prev
        step = step / max(np.linalg.norm(step), 1e-9)
        step = SLOPE * step + (1.0 - SLOPE) * a  # between the tip's slope and straight on: past the pulp, no ledge
        v.co += type(v.co)(step / np.linalg.norm(step) * free_edge / 1000.0)
    # a straight cut with rounded corners: the new row's outer vertices pulled in a little
    s_new = np.array([(np.array(v.co) - c) @ b for v in new])
    if len(new) >= 2:
        for i in (int(np.argmin(s_new)), int(np.argmax(s_new))):
            inward = -np.sign(s_new[i]) * b
            new[i].co += type(new[i].co)(inward * CORNER_MM / 1000.0)
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    canonical(me)
    for poly in me.polygons:
        poly.use_smooth = True
    co = np.array([v.co for v in me.vertices]) * 1000.0
    cc = c * 1000.0
    dims = {"width": float(((co - cc) @ b).max() - ((co - cc) @ b).min()),
            "length": float(((co - cc) @ a).max() - ((co - cc) @ a).min()),
            "thickness": thickness}
    return me, dims


def canonical(me):
    """Rebuild a mesh with its faces in a fixed order, each starting at its lowest vertex (winding kept):
    bmesh's extrude emits new faces in an order that changes from run to run (its working sets are keyed by
    pointer), and the part cache's mesh hash reads the face order (spec 18 §4.7 rule 1)."""
    verts = [tuple(v.co) for v in me.vertices]
    faces = []
    for p in me.polygons:
        f = list(p.vertices)
        i = f.index(min(f))
        faces.append(f[i:] + f[:i])
    faces.sort()
    me.clear_geometry()
    me.from_pydata(verts, [], faces)
    me.update()


def finish(ob, thickness):
    """Solidify (outward from the bed), a rounded rim, subdivision (§4.4)."""
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness, sol.offset = thickness / 1000.0, 1.0
    sol.use_rim, sol.use_even_offset = True, True
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width, bev.segments = 0.25 / 1000.0, 2
    bev.limit_method, bev.angle_limit = "ANGLE", math.radians(40.0)
    sub = ob.modifiers.new("Subdivision", "SUBSURF")
    sub.levels, sub.render_levels = 2, 3


def parent_to_bone(ob, rig, bone_name):
    """Bone-parent ob to rig's bone, keeping it where it is (its vertices are in world space)."""
    from mathutils import Matrix
    bone = rig.data.bones[bone_name]
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = bone_name
    tip = rig.matrix_world @ bone.matrix_local @ Matrix.Translation((0.0, bone.length, 0.0))
    ob.matrix_parent_inverse = tip.inverted()
    ob.matrix_basis = Matrix.Identity(4)
