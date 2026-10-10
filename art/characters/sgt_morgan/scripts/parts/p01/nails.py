"""The toenail plates of spec 01 §4.4: Foot.<S>.Nail.<k>, one shell per nail on the sculpted nail bed of
Body.Mesh (the faces of MPFB's `toenails` group, sized, bent across and placed by fields.nail_beds).

A plate is not the bed's faces copied: twenty faces on a 4 mm cage made a faceted lid that its bevel creased,
and its free edge, one extruded row, read in closeups as a thin flake standing off the toe. It is a smooth
grid laid over a surface fitted to the bed: a circular arc across, of §3.3's transverse radius, on the bed's
own curve along the toe, lifted 0.35 mm off the bed. Its outline is the bed's, rounded at the root and cut
straight at the free edge with rounded corners. The free edge carries the plate's curve on past the
hyponychium by §3.3's length, so it follows the toe down instead of standing off it, and the bed is placed
so that the free edge ends short of the pulp's tip (fields.nail_beds): seen from above a little skin shows
beyond the nail, as on a real toe. The root and the sides dive under the nail folds over their last
millimetres, so only the free edge shows an edge. Solidify gives the thickness, outward; a row of the grid
just inside the free edge holds that thickness through the subdivision, which rounds the rim (no bevel). A
plate rides its toe's distal bone (bone parenting with the inverse set, so it stays where it was built).
"""
import math

import numpy as np

from lib import sculpt as S

# §3.3: width x visible length (from the proximal fold to the free edge's tip), free edge, thickness (mm)
PLATES = {1: (19.5, 18.35, 1.5, 1.1), 2: (11.0, 10.0, 1.2, 0.8), 3: (10.0, 9.0, 1.0, 0.7),
          4: (9.0, 8.0, 1.0, 0.7), 5: (7.0, 6.0, 0.8, 0.9)}
LIFT_MM = 0.35       # off the sunk bed (§4.4)
BURY_MM = 1.3        # how deep the root and the sides go under the folds
BURY_ROOT_MM = 3.0   # over the root's last 3 mm (under the eponychium)
BURY_SIDE_MM = 2.0   # and the sides' last 2 mm (under the lateral folds), at most 16 % of the width
CORNER_MM = {1: 2.5, 2: 1.6, 3: 1.5, 4: 1.4, 5: 1.2}  # the straight-cut free edge's rounded corners
ROOT_ROUND = 0.35    # the root's curve: an ellipse a third of the half-width deep
GRID = (12, 16)      # quads across and along a plate
SUPPORT_MM = 0.3     # the support row inside the free edge (and inside the plate's other ends)
DISTAL_BONE = {1: "toe1-2", 2: "toe2-3", 3: "toe3-3", 4: "toe4-3", 5: "toe5-3"}


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


def arc_drop(u, radius):
    """How far a circular arc of the radius falls below its crown at u off the centre line (mm)."""
    u = np.minimum(np.abs(np.asarray(u, float)), 0.98 * radius)
    return radius - np.sqrt(radius * radius - u * u)


def bed_frame(P, polys, axis):
    """The bed's centre, outward normal (area-weighted, as the body's winding is) and its axes along and
    across the toe."""
    nrm = np.zeros(3)
    for poly in polys:
        for i in range(1, len(poly) - 1):
            nrm += np.cross(P[poly[i]] - P[poly[0]], P[poly[i + 1]] - P[poly[0]])
    nrm /= np.linalg.norm(nrm)
    a = np.asarray(axis, float)
    a = a - (a @ nrm) * nrm
    a /= np.linalg.norm(a)
    return P.mean(axis=0), nrm, a, np.cross(nrm, a)


def _stations(v0, v_end, n):
    """Rows along the plate: even, with support rows just inside both ends."""
    inner = np.linspace(v0 + SUPPORT_MM, v_end - SUPPORT_MM, n - 1)
    return np.concatenate([[v0], inner, [v_end]])


def build_plate(name, ob, co_m, faces, axis_w, thickness, free_edge, radius, corner=1.5):
    """A plate mesh (metres, world) over the bed faces of a nail; returns the bpy mesh and the plate's
    measurements (mm): width, visible length, thickness and the frame it was laid in."""
    import bpy
    ls, lt, lv = S.topology(ob.data)
    verts = sorted({int(v) for p in faces for v in lv[ls[p]:ls[p] + lt[p]]})
    local = {v: i for i, v in enumerate(verts)}
    P = co_m[verts] * 1000.0
    polys = [[local[int(v)] for v in lv[ls[p]:ls[p] + lt[p]]] for p in faces]
    c, nrm, a, b = bed_frame(P, polys, axis_w)
    d = P - c
    u, v, h = d @ b, d @ a, d @ nrm
    # the bed's surface, h = f(u, v) quadratic; the plate keeps its tilt and its curve along the toe and
    # replaces its curve across with the arc (the bed was bent to the same arc where it was flatter)
    A = np.stack([np.ones_like(u), u, v, u * u, u * v, v * v], axis=1)
    cf = np.linalg.lstsq(A, h, rcond=None)[0]
    u_lo, u_hi = float(u.min()), float(u.max())
    uc, half = 0.5 * (u_lo + u_hi), 0.5 * (u_hi - u_lo)
    v0, v1 = float(v.min()), float(v.max())
    v_end = v1 + free_edge
    nu, nv = GRID
    rows = _stations(v0, v_end, nv)
    cols = np.linspace(-1.0, 1.0, nu + 1)
    root = ROOT_ROUND * half
    side = min(BURY_SIDE_MM, 0.32 * half)
    pts = []
    for vv in rows:
        hw = half
        if vv < v0 + root:  # the root's curve
            hw *= math.sqrt(max(0.0, 1.0 - ((v0 + root - vv) / root) ** 2)) * 0.85 + 0.15
        if vv > v_end - corner:  # the free edge's corners
            hw -= corner - math.sqrt(max(0.0, corner * corner - (vv - (v_end - corner)) ** 2))
        for s in cols:
            uu = uc + s * hw
            crown = cf[0] + cf[1] * uu + cf[2] * vv + cf[3] * uc * uc + cf[4] * uu * vv + cf[5] * vv * vv
            hh = crown - arc_drop(uu - uc, radius) + LIFT_MM
            # under the folds: the root and the sides behind the hyponychium dive into the skin
            dive = 1.0 - S.smoothstep(vv, v0, v0 + BURY_ROOT_MM)
            edge = S.smoothstep(abs(uu - uc), hw - side, hw) * (1.0 - S.smoothstep(vv, v1 - 2.0, v1))
            hh -= BURY_MM * max(float(dive), float(edge))
            pts.append(c + uu * b + vv * a + hh * nrm)
    quads = []
    for i in range(nv):
        for j in range(nu):
            p0 = i * (nu + 1) + j
            quads.append([p0, p0 + 1, p0 + nu + 2, p0 + nu + 1])
    # winding: the plate's faces point away from the bed, as the body's do
    q0 = quads[0]
    pp = np.array(pts)
    fn = np.cross(pp[q0[1]] - pp[q0[0]], pp[q0[2]] - pp[q0[0]])
    if fn @ nrm < 0:
        quads = [list(reversed(f)) for f in quads]
    me = bpy.data.meshes.new(name)
    me.from_pydata((pp / 1000.0).tolist(), [], quads)
    me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    dims = {"width": float(2.0 * half), "length": float(v_end - v0), "thickness": thickness,
            "radius": float(radius), "bed_to_tip_free_edge_mm": float(free_edge)}
    return me, dims, {"centre": c.tolist(), "normal": nrm.tolist(), "along": a.tolist(), "across": b.tolist(),
                      "v_root": v0, "v_hyponychium": v1, "v_end": v_end, "u_centre": uc}


def transverse_radius(co, axis, normal_hint=(0.0, 0.0, 1.0)):
    """A plate's transverse radius of curvature (mm): a circle fitted across its middle third (co in mm),
    leaving out the sides that dive under the folds."""
    co = np.asarray(co, float)
    c = co.mean(axis=0)
    d = co - c
    a = np.asarray(axis, float)
    nrm = np.linalg.svd(d, full_matrices=False)[2][-1]
    nrm = nrm if nrm @ np.asarray(normal_hint, float) >= 0 else -nrm
    a = a - (a @ nrm) * nrm
    a /= np.linalg.norm(a)
    b = np.cross(nrm, a)
    v, uu = d @ a, d @ b
    half = 0.5 * (uu.max() - uu.min())
    mid = (np.abs(v - 0.5 * (v.max() + v.min())) < 0.18 * (v.max() - v.min())) & \
          (np.abs(uu - 0.5 * (uu.max() + uu.min())) < half - min(BURY_SIDE_MM, 0.32 * half))
    u, h = d[mid] @ b, d[mid] @ nrm
    if len(u) < 3:
        return None
    A = np.stack([u, h, np.ones_like(u)], axis=1)
    D, E, F = np.linalg.lstsq(A, -(u * u + h * h), rcond=None)[0]
    r2 = D * D / 4.0 + E * E / 4.0 - F
    return float(np.sqrt(r2)) if r2 > 0 else None


def free_edge_thickness(ob, frame):
    """The plate's thickness 0.5 mm inside its free edge on the centre line, on its evaluated (solidified,
    subdivided) mesh (mm): from the top sheet's vertex there, along its inward normal, to the bottom sheet."""
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        M = np.array(ev.matrix_world)
        co = np.array([v.co for v in me.vertices]) @ M[:3, :3].T * 1000.0 + M[:3, 3] * 1000.0
        nr = np.array([v.normal for v in me.vertices]) @ M[:3, :3].T
        me.calc_loop_triangles()
        tris = [tuple(t.vertices) for t in me.loop_triangles]
    finally:
        ev.to_mesh_clear()
    c, nrm, a, b = (np.asarray(frame[k], float) for k in ("centre", "normal", "along", "across"))
    d = co - c
    u, v, h = d @ b - frame["u_centre"], d @ a, d @ nrm
    near = (np.abs(v - (frame["v_end"] - 0.5)) < 0.4) & (np.abs(u) < 0.6) & (nr @ nrm > 0.5)  # the top sheet
    if not near.any():
        return None
    i = np.nonzero(near)[0][np.argmin(np.abs(v[near] - (frame["v_end"] - 0.5)) + np.abs(u[near]))]
    n = nr[i] / np.linalg.norm(nr[i])
    tree = BVHTree.FromPolygons(co.tolist(), tris, all_triangles=True)
    start = co[i] - 0.01 * n
    hit = tree.ray_cast(Vector(start), Vector(-n), 5.0)
    return None if hit[0] is None else float(hit[3] + 0.01)


def finish(ob, thickness):
    """Solidify (outward from the bed, the rim closed) and subdivision (§4.4; the bevel is gone: the grid's
    support rows round the rim without thinning it)."""
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness, sol.offset = thickness / 1000.0, 1.0
    sol.use_rim, sol.use_even_offset = True, True
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
