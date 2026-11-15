"""Shared helpers for the gear parts (carrier, armour, belt), take 2 round 1 on. Built on common.py (the
clothing agent's module: load the body, bind, save a cache, render through the hero camera), which this
module only reads; everything here is what the gear needs on top of it.

  * The surface under the gear: `Under` casts rays from outside inward against the body (or a clothing
    cache when it exists) and returns the outermost surface, plus an assumed clothing allowance where the
    garment's cache is missing (shirt 4 mm over the skin, trousers 12 mm).
  * Geometry: `slab()` (a closed panel of given thickness over a parametric surface, its outline given as a
    u-range per v row, optionally closed around u for rings), `rbox()` (a rounded box in a frame),
    `strip()` (a rectangular section swept along a path), `cyl()` (a capped cylinder along an axis).
    All take millimetres, build world-space meshes on identity objects, and give them a Bevel modifier
    with hardened normals so a blockout reads as moulded or sewn rather than as a cube.
  * Rigging: `soft_bind()` (common.bind, weight transfer from the body, with arm weights collapsed where an
    item must not follow the arm), `rigid_bind()` (every vertex 100 % to one bone plus an Armature modifier:
    a rigid bone attachment that survives common.save_part/load_part and exports to glTF as skinning) and
    `dominant_bone()` (the bone whose weights rule the skin under a point).
  * Evaluation: `render_rest()` (front, side, back and three-quarter clay on the rest body), `render_part_hero()`
    (the posed part through the hero camera beside its reference crops), `check_posed()` (interpenetration:
    triangle overlaps gear/body, gear/clothing, gear/gear, carbine/gear, and the clearance to the skin),
    `load_carbine()` (the carbine cache placed in the right hand from hero_pose.json), and `together()`
    which renders renders/round_01/gear_hero.png.

    "$SGT_BLENDER" -b --python scripts/parts/gear_common.py -- --together [carrier armour belt]
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import common as C  # noqa: E402

MM = 0.001
SHIRT_MM = 4.0          # assumed shirt (and its seams) over the skin where no shirt cache exists
TROUSERS_MM = 12.0      # assumed trousers over the skin where no trousers cache exists
CLOTHING = ("trousers", "shirt", "boots", "gloves")
GEAR = ("carrier", "armour", "belt")


def unit(v):
    v = np.asarray(v, float)
    return v / max(np.linalg.norm(v), 1e-12)


def say(*a):
    C.say("gear", *a)


# --------------------------------------------------------------------------- body masks and BVHs

def masks(bd):
    """Per-vertex region masks of the rest skin: arm, head (head bone and face, not the neck), leg."""
    arm = C.weight_sum(bd, C.is_arm)
    head = C.weight_sum(bd, lambda n: n in ("head", "jaw") or n.startswith(("oris", "tongue", "levator", "special",
                                                                             "eye", "orbicularis", "oculi",
                                                                             "risorius", "temporalis")))
    leg = C.weight_sum(bd, C.is_leg)
    limb = C.weight_sum(bd, lambda n: n.startswith(("upperarm", "lowerarm", "wrist", "finger", "metacarpal")))
    return {"arm": arm, "limb": limb, "head": head, "leg": leg}


def skin_bvh(bd, keep=None):
    """BVH (mm) of the rest skin faces whose vertices all pass `keep` (and are real skin)."""
    ib = bd["in_body"] if keep is None else (bd["in_body"] & keep)
    return C.bvh_from(bd["V"], [f for f in bd["F"] if ib[list(f)].all()])


def objects_bvh(objs):
    """BVH (mm, world) of the evaluated meshes of several objects together (at the rig's current pose)."""
    Vs, Fs, n = [], [], 0
    for ob in objs:
        if ob.type != "MESH":
            continue
        V, F = C.evaluated_world_mm(ob, disable=())
        Vs.append(V)
        Fs += [tuple(i + n for i in f) for f in F]
        n += len(V)
    if not Vs:
        return None
    return C.bvh_from(np.concatenate(Vs), Fs)


class Under:
    """The surface the gear sits on. layers: list of (bvh, extra_mm); a ray cast from outside inward finds
    each layer's first (outermost) hit and the effective surface is the outermost of (hit moved out by
    extra). hit(start, dir_in, maxd) -> (point, outward normal) or (None, None)."""

    def __init__(self, layers):
        self.layers = [(b, e) for b, e in layers if b is not None]

    def hit(self, start, d_in, maxd=1500.0):
        from mathutils import Vector
        best, bn = None, None
        s = Vector(start)
        dv = Vector(d_in)
        for bvh, extra in self.layers:
            h = bvh.ray_cast(s, dv, maxd)
            if h[0] is None:
                continue
            t = h[3] - extra
            if best is None or t < best:
                best, bn = t, np.array(h[1])
        if best is None:
            return None, None
        n = unit(bn)
        if n.dot(np.asarray(d_in)) > 0:
            n = -n
        return np.asarray(start, float) + np.asarray(d_in, float) * best, n

    def hit_out(self, start, d_out, maxd=300.0):
        """From a point inside (a limb axis) outward: each layer's first hit, the outermost of (hit + extra).
        Immune to neighbouring limbs that an inward ray would meet first."""
        from mathutils import Vector
        best, bn = None, None
        dv = Vector(d_out)
        for bvh, extra in self.layers:
            h = bvh.ray_cast(Vector(start), dv, maxd)
            if h[0] is None:
                continue
            t, nn = h[3], h[1]
            # a garment with thickness (Solidify) has an inner and an outer face: walk on through faces closer
            # than 15 mm to the last one, so t lands on the outer face, not on a neighbouring limb
            for _ in range(6):
                h2 = bvh.ray_cast(Vector(np.asarray(start, float) + np.asarray(d_out, float) * (t + 0.05)), dv, 15.0)
                if h2[0] is None:
                    break
                t, nn = t + 0.05 + h2[3], h2[1]
            h = (None, nn, None, t)
            t = h[3] + extra
            if best is None or t > best:
                best, bn = t, np.array(h[1])
        if best is None:
            return None, None
        n = unit(bn)
        if n.dot(np.asarray(d_out)) < 0:
            n = -n
        return np.asarray(start, float) + np.asarray(d_out, float) * best, n


# --------------------------------------------------------------------------- materials

def mat(name, hexcol, rough=0.8):
    return C.flat_material(name, hexcol, rough)


# --------------------------------------------------------------------------- geometry

def _finish(ob, bevel_mm=0.0, segments=2, smooth=True, harden=True, angle=60.0):
    me = ob.data
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.update()
    me.polygons.foreach_set("use_smooth", np.full(len(me.polygons), bool(smooth)))
    if smooth:
        try:
            me.set_sharp_from_angle(angle=math.radians(angle))
        except AttributeError:
            pass
    if bevel_mm > 0:
        b = ob.modifiers.new("Bevel", "BEVEL")
        b.width = bevel_mm * MM
        b.segments = segments
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
        b.harden_normals = harden
        b.use_clamp_overlap = True
    return ob


def new_mesh(name, V, F, coll, material=None, bevel_mm=0.0, segments=2, smooth=True, angle=60.0):
    ob = C.mesh_object(name, V, F, coll, mat=material, smooth=smooth)
    return _finish(ob, bevel_mm, segments, smooth, angle=angle)


def grid_points(surf, urange, v0, v1, nu, nv, closed_u=False):
    """Sample a parametric surface: rows v_j in [v0, v1], u_i spread over urange(v) (or over [0, 2pi) when
    closed_u). surf(u, v) -> (P, N) arrays (mm). Returns P, N of shape (nv+1, nu', 3) and the (u, v) grid."""
    P = []
    N = []
    UV = []
    for j in range(nv + 1):
        v = v0 + (v1 - v0) * j / nv
        if closed_u:
            us = np.linspace(0.0, 2 * math.pi, nu, endpoint=False)
        else:
            a, b = urange(v)
            us = np.linspace(a, b, nu + 1)
        row = [surf(u, v) for u in us]
        P.append([r[0] for r in row])
        N.append([r[1] for r in row])
        UV.append([(u, v) for u in us])
    return np.array(P, float), np.array(N, float), UV


def slab_from_grid(P, N, t, closed_u=False, t_field=None, outer=None):
    """A closed slab from an inner grid surface P (rows x cols x 3) with outward normals N: outer = P + N t
    (t may vary per point via t_field). Returns V, F."""
    nr, nc = P.shape[:2]
    T = np.full((nr, nc), float(t)) if t_field is None else np.asarray(t_field, float)
    inner = P.reshape(-1, 3)
    outer = (P + N * T[..., None]).reshape(-1, 3) if outer is None else np.asarray(outer, float).reshape(-1, 3)
    V = np.concatenate([inner, outer])
    off = nr * nc

    def idx(j, i):
        return j * nc + (i % nc)
    F = []
    ci = nc if closed_u else nc - 1
    for j in range(nr - 1):
        for i in range(ci):
            a, b, c, d = idx(j, i), idx(j, i + 1), idx(j + 1, i + 1), idx(j + 1, i)
            F.append((a, d, c, b))                      # inner, facing in
            F.append((a + off, b + off, c + off, d + off))  # outer
    # boundary walls
    if closed_u:
        loops = [[idx(0, i) for i in range(nc)] + [idx(0, 0)], [idx(nr - 1, i) for i in range(nc)] + [idx(nr - 1, 0)]]
    else:
        ring = [idx(0, i) for i in range(nc)] + [idx(j, nc - 1) for j in range(1, nr)] + \
               [idx(nr - 1, i) for i in range(nc - 2, -1, -1)] + [idx(j, 0) for j in range(nr - 2, -1, -1)]
        loops = [ring]
    for lp in loops:
        for k in range(len(lp) - 1):
            a, b = lp[k], lp[k + 1]
            if a == b:
                continue
            F.append((a, b, b + off, a + off))
    return V, F


def slab(name, coll, surf, urange, v0, v1, t, material, nu=24, nv=24, bevel_mm=3.0, closed_u=False,
         post=None, t_field_fn=None, segments=2):
    """A closed panel over surf (see grid_points), thickness t mm outward. post(P, N, UV) may edit the grid
    before the slab is built (clamping behind another part, etc.)."""
    P, N, UV = grid_points(surf, urange, v0, v1, nu, nv, closed_u)
    tf = None
    if post is not None:
        P, N = post(P, N, UV)
    if t_field_fn is not None:
        tf = np.array([[t_field_fn(u, v) for (u, v) in row] for row in UV])
    V, F = slab_from_grid(P, N, t, closed_u, tf)
    return new_mesh(name, V, F, coll, material, bevel_mm=bevel_mm, segments=segments)


def frame(origin, x, z):
    """4x4 (numpy) with columns x, y = z cross x, z (orthonormalised, z kept)."""
    z = unit(z)
    x = unit(np.asarray(x, float) - z * np.dot(x, z))
    y = np.cross(z, x)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, origin
    return M


def rbox(name, coll, size, M, material, bevel_mm=4.0, segments=3, taper=None):
    """A box size (sx, sy, sz) mm centred at the frame M's origin along its axes, rounded by a Bevel.
    taper: (fx, fz) scale of the +y face (a box narrowing toward its front)."""
    sx, sy, sz = [s / 2.0 for s in size]
    V = []
    for k in (-1, 1):
        for j in (-1, 1):
            for i in (-1, 1):
                fx = fz = 1.0
                if taper is not None and j > 0:
                    fx, fz = taper
                V.append([i * sx * fx, j * sy, k * sz * fz])
    V = np.array(V)
    F = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    W = V @ M[:3, :3].T + M[:3, 3]
    return new_mesh(name, W, F, coll, material, bevel_mm=min(bevel_mm, min(size) / 2.0 - 0.05),
                    segments=segments, smooth=True)


def box_verts(size, M, taper=None):
    sx, sy, sz = [s / 2.0 for s in size]
    V = []
    for k in (-1, 1):
        for j in (-1, 1):
            for i in (-1, 1):
                fx = fz = 1.0
                if taper is not None and j > 0:
                    fx, fz = taper
                V.append([i * sx * fx, j * sy, k * sz * fz])
    V = np.array(V)
    F = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return V @ M[:3, :3].T + M[:3, 3], F


def boxes(name, coll, specs, material, bevel_mm=4.0, segments=3):
    """Several boxes [(size, M[, taper])] as one object (one rigid item made of blocks, e.g. a pouch body and
    its flap), so their touching blocks do not count as interpenetration between items."""
    Vs, Fs, n = [], [], 0
    smin = 1e9
    for sp in specs:
        V, F = box_verts(sp[0], sp[1], sp[2] if len(sp) > 2 else None)
        Vs.append(V)
        Fs += [tuple(i + n for i in f) for f in F]
        n += len(V)
        smin = min(smin, min(sp[0]))
    ob = C.mesh_object(name, np.concatenate(Vs), Fs, coll, mat=material, smooth=True)
    import bmesh
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    b = ob.modifiers.new("Bevel", "BEVEL")
    b.width = min(bevel_mm, smin / 2.0 - 0.05) * MM
    b.segments = segments
    b.limit_method = "ANGLE"
    b.angle_limit = math.radians(40)
    b.harden_normals = True
    b.use_clamp_overlap = True
    return ob


def seat(under, M, size, grid=5, gap=0.5):
    """Move a box (frame M, size, local y = depth outward) along its local +y until its whole back face
    clears the surface `under` by gap: rays from outside inward at grid x grid points of the back face."""
    M = np.array(M, float)
    n = M[:3, 1]
    best = -1e9
    for a in np.linspace(-0.5, 0.5, grid):
        for b in np.linspace(-0.5, 0.5, grid):
            q = M[:3, 3] + M[:3, 0] * a * size[0] - n * size[1] / 2.0 + M[:3, 2] * b * size[2]
            p, _ = under.hit(q + n * 300.0, -n, 600.0)
            if p is not None:
                best = max(best, float(np.dot(p - q, n)))
    if best > -1e8:
        M[:3, 3] += n * (best + gap)
    return M


def join(target, others):
    """Merge other objects' meshes into target (world space, identity objects; target keeps its modifiers
    and materials, others' material slots are appended). Returns target."""
    import bpy
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(target.data)
    for ob in others:
        me = ob.data
        nmat = len(target.data.materials)
        for m in me.materials:
            if m.name not in [x.name for x in target.data.materials if x]:
                target.data.materials.append(m)
        tmp = bmesh.new()
        tmp.from_mesh(me)
        names = [x.name for x in target.data.materials]
        for f in tmp.faces:
            mm = me.materials[f.material_index] if me.materials else None
            f.material_index = names.index(mm.name) if mm else 0
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.objects.remove(ob, do_unlink=True)
        del nmat
    bm.to_mesh(target.data)
    bm.free()
    target.data.update()
    return target


def strip(name, coll, path, normals, width, thick, material, bevel_mm=0.6, closed=False):
    """A flat strap: a width x thick rectangle swept along path (n x 3 mm), its underside on the path and
    its thickness along normals (outward). Returns the object."""
    P = np.asarray(path, float)
    Nn = np.array([unit(n) for n in normals])
    n = len(P)
    T = np.zeros_like(P)
    for i in range(n):
        a = P[(i - 1) % n] if (closed or i > 0) else P[i]
        b = P[(i + 1) % n] if (closed or i < n - 1) else P[i]
        T[i] = unit(b - a)
    V = []
    for i in range(n):
        Ni = unit(Nn[i] - T[i] * np.dot(Nn[i], T[i]))
        B = unit(np.cross(T[i], Ni))
        h = width / 2.0
        V += [P[i] - B * h, P[i] + B * h, P[i] + B * h + Ni * thick, P[i] - B * h + Ni * thick]
    F = []
    m = n if closed else n - 1
    for i in range(m):
        j = (i + 1) % n
        for k in range(4):
            a, b = i * 4 + k, i * 4 + (k + 1) % 4
            c, d = j * 4 + (k + 1) % 4, j * 4 + k
            F.append((a, d, c, b))
    if not closed:
        F.append((0, 1, 2, 3))
        e = (n - 1) * 4
        F.append((e + 3, e + 2, e + 1, e))
    return new_mesh(name, np.array(V), F, coll, material, bevel_mm=bevel_mm, segments=1)


def cyl(name, coll, base, axis, radius, length, material, n=24, bevel_mm=1.0, dome=0.0):
    """A capped cylinder from base along axis (mm); dome > 0 rounds the far end into a cap that high."""
    a = unit(axis)
    e1 = unit(np.cross(a, [0.0, 0.0, 1.0]) if abs(a[2]) < 0.9 else np.cross(a, [1.0, 0.0, 0.0]))
    e2 = np.cross(a, e1)
    rings = [(0.0, radius), (length, radius)]
    if dome > 0:
        for k in range(1, 5):
            th = k / 5.0 * math.pi / 2
            rings.append((length + dome * math.sin(th), radius * math.cos(th)))
    V = []
    for (h, r) in rings:
        for i in range(n):
            ph = 2 * math.pi * i / n
            V.append(np.asarray(base, float) + a * h + (e1 * math.cos(ph) + e2 * math.sin(ph)) * r)
    F = []
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            F.append((k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i))
    F.append(tuple(range(n - 1, -1, -1)))
    last = (len(rings) - 1) * n
    F.append(tuple(range(last, last + n)))
    return new_mesh(name, np.array(V), F, coll, material, bevel_mm=bevel_mm, segments=2)


def convex_radii(cx, cy, Q, thetas):
    """Radii, from the centre (cx, cy) along angles thetas, of the 2-D convex hull of the points Q."""
    H = C.hull2d(np.asarray(Q, float))
    A, B = H, np.roll(H, -1, 0)
    out = np.zeros(len(thetas))
    for k, th in enumerate(thetas):
        u = np.array([math.cos(th), math.sin(th)])
        ex, ey = B[:, 0] - A[:, 0], B[:, 1] - A[:, 1]
        den = u[0] * ey - u[1] * ex
        ok = np.abs(den) > 1e-9
        ax, ay = A[:, 0] - cx, A[:, 1] - cy
        s = np.where(ok, (ax * ey - ay * ex) / np.where(ok, den, 1), -1)
        w = np.where(ok, (ax * u[1] - ay * u[0]) / np.where(ok, den, 1), -1)
        hit = ok & (s > 0) & (w >= -1e-6) & (w <= 1 + 1e-6)
        out[k] = s[hit].max() if hit.any() else np.nan
    return out


# --------------------------------------------------------------------------- limb frames

def limb_frame(a, b, side, front=(0.0, -1.0, 0.0)):
    """Axis from a to b (mm). Returns d (along the limb), f (front, -Y made perpendicular), l (lateral: away
    from the body's midline on the given side)."""
    d = unit(np.asarray(b, float) - np.asarray(a, float))
    f = unit(np.asarray(front, float) - d * np.dot(front, d))
    lat = unit(np.cross(d, f))
    if lat[0] * (1.0 if side == "L" else -1.0) < 0:
        lat = -lat
    return d, f, lat


def limb_radius(under, a, d, e0, e1, s, theta, rmax=220.0, outward=False):
    """Outermost radius of the surface around the limb axis (a, d) at station s (mm along d) and angle
    theta from e0 toward e1 (rad), by a ray cast from rmax inward. Returns r (or nan) and the hit normal."""
    dr = math.cos(theta) * e0 + math.sin(theta) * e1
    c = np.asarray(a, float) + d * s
    p, n = under.hit_out(c, dr, rmax) if outward else under.hit(c + dr * rmax, -dr, rmax)
    if p is None:
        return float("nan"), dr
    return float(np.dot(p - c, dr)), n


def smooth_grid(R, iters=4, lam=0.5):
    R = np.array(R, float)
    for _ in range(iters):
        Rp = np.pad(R, 1, mode="edge")
        avg = (Rp[:-2, 1:-1] + Rp[2:, 1:-1] + Rp[1:-1, :-2] + Rp[1:-1, 2:]) / 4.0
        R = R + lam * (avg - R)
    return R


def fill_nan(R):
    R = np.array(R, float)
    if np.isnan(R).all():
        return R
    m = np.nanmean(R)
    R[np.isnan(R)] = m
    return R


# --------------------------------------------------------------------------- smooth limb surfaces

class Field:
    """A smooth radius field R(a, b) over a rectangular parameter grid, from raw ray samples: smoothed,
    then pushed back outside the raw samples so a rigid shell bridges folds but never sinks in."""

    def __init__(self, raw, a, b, iters=8):
        raw = fill_nan(raw)
        R = smooth_grid(raw, iters)
        for _ in range(3):
            R = np.maximum(R, raw)
            R = smooth_grid(R, 2)
        R = np.maximum(R, raw)
        self.R, self.a, self.b = R, np.asarray(a), np.asarray(b)

    def __call__(self, a, b):
        A, B = self.a, self.b
        i = np.clip(np.searchsorted(A, a) - 1, 0, len(A) - 2)
        j = np.clip(np.searchsorted(B, b) - 1, 0, len(B) - 2)
        ta = np.clip((a - A[i]) / (A[i + 1] - A[i]), 0, 1)
        tb = np.clip((b - B[j]) / (B[j + 1] - B[j]), 0, 1)
        R = self.R
        return ((1 - ta) * (1 - tb) * R[j, i] + ta * (1 - tb) * R[j, i + 1] + (1 - ta) * tb * R[j + 1, i]
                + ta * tb * R[j + 1, i + 1])


def numeric_normal(f, u, v, out_hint, h=0.5):
    pu = (f(u + h, v) - f(u - h, v))
    pv = (f(u, v + h) - f(u, v - h))
    n = unit(np.cross(pu, pv))
    return n if np.dot(n, out_hint) >= 0 else -n


class LimbSurf:
    """Surface around a limb axis: P(theta, s) = a + d s + dir(theta) (R(theta, s) + off), theta (rad) from e0
    toward e1."""

    def __init__(self, under, a, d, e0, e1, th_range, s_range, nth=36, ns=24, iters=8, rmax=200.0, outward=False):
        self.a, self.d, self.e0, self.e1 = np.asarray(a, float), d, e0, e1
        ths = np.linspace(th_range[0], th_range[1], nth)
        ss = np.linspace(s_range[0], s_range[1], ns)
        rm = rmax if callable(rmax) else (lambda t, r=rmax: r)
        raw = np.array([[limb_radius(under, a, d, e0, e1, s, t, rm(t), outward)[0] for t in ths] for s in ss])
        self.F = Field(raw, ths, ss, iters)

    def dirv(self, th):
        return math.cos(th) * self.e0 + math.sin(th) * self.e1

    def point(self, th, s, off):
        th = (th + math.pi) % (2 * math.pi) - math.pi
        return self.a + self.d * s + self.dirv(th) * (self.F(th, s) + off)

    def surf(self, off, r0=None):
        """surf(u, v) with u in mm of arc (at radius r0) when r0 is given, else radians; v = s (mm)."""
        def f(u, v):
            th = u / r0 if r0 else u
            p = self.point(th, v, off)
            n = numeric_normal(lambda uu, vv: self.point(uu / r0 if r0 else uu, vv, off), u, v, self.dirv(th))
            return p, n
        return f


# --------------------------------------------------------------------------- rigging

ARM_PREFIX = ("shoulder01", "upperarm01", "upperarm02", "lowerarm01", "lowerarm02", "wrist")


def arms_to_clavicle():
    """collapse= map for common.bind: every arm bone (from shoulder01 down) into its clavicle, so torso gear
    follows the shoulder girdle but not the arm."""
    return {f"{p}.{s}": f"clavicle.{s}" for s in ("L", "R") for p in ARM_PREFIX}


def soft_bind(ob, body, rig, collapse=None):
    """common.bind (weight transfer from Body.Mesh, Armature modifier first), Bevel kept after it."""
    C.bind(ob, body, rig, collapse=collapse)
    ob["sgt_bind"] = "weights"
    return ob


def rigid_bind(ob, rig, bone):
    """Attach ob rigidly to one bone: every vertex weighted 1.0 to `bone` and an Armature modifier at the top
    of the stack, the object parented to the rig like common.bind does. Equivalent to bone parenting under
    any pose, and it survives common.save_part/load_part and glTF export as plain skinning."""
    import bpy
    for g in list(ob.vertex_groups):
        ob.vertex_groups.remove(g)
    g = ob.vertex_groups.new(name=bone)
    g.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
    arm = ob.modifiers.new("Armature", "ARMATURE")
    arm.object = rig
    arm.use_vertex_groups = True
    arm.use_bone_envelopes = False
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.modifier_move_to_index(modifier=arm.name, index=0)
    ob.parent = rig
    ob.matrix_parent_inverse = rig.matrix_world.inverted()
    ob["sgt_bind"] = f"rigid:{bone}"
    return ob


def dominant_bone(bd, point, allowed=None, k=24):
    """The deform bone with the largest summed weight over the k skin vertices nearest `point` (mm),
    among `allowed` names if given."""
    V = bd["V"]
    ib = np.nonzero(bd["in_body"])[0]
    d = np.linalg.norm(V[ib] - np.asarray(point, float), axis=1)
    near = ib[np.argsort(d)[:k]]
    best, bw = None, -1.0
    for nm, w in bd["groups"].items():
        if nm == "body" or (allowed is not None and nm not in allowed):
            continue
        s = float(w[near].sum())
        if s > bw:
            best, bw = nm, s
    return best


# --------------------------------------------------------------------------- caches and scene

def load_clothing(rig):
    """Append every clothing cache that exists (common.load_part). Returns {part: collection}."""
    out = {}
    for p in CLOTHING:
        if os.path.exists(os.path.join(C.PARTS_DIR, f"{p}.blend")):
            try:
                out[p] = C.load_part(p, rig)
            except Exception as e:  # noqa: BLE001
                say(f"could not load {p}: {e}")
    return out


def region_bvh(bd, objs, keep):
    """BVH (mm, current pose = rest here) of the faces of objs whose vertices all lie nearest to a skin
    vertex in `keep` (e.g. the shirt's body without its sleeves)."""
    from mathutils import Vector
    from mathutils.kdtree import KDTree
    idx = np.nonzero(bd["in_body"])[0]
    kd = KDTree(len(idx))
    for k, i in enumerate(idx):
        kd.insert(Vector(bd["V"][i]), k)
    kd.balance()
    Vs, Fs, n = [], [], 0
    for ob in objs:
        if ob.type != "MESH":
            continue
        V, F = C.evaluated_world_mm(ob, disable=())
        ok = np.array([bool(keep[idx[kd.find(Vector(v))[1]]]) for v in V])
        Fk = [f for f in F if ok[list(f)].all()]
        Vs.append(V)
        Fs += [tuple(i + n for i in f) for f in Fk]
        n += len(V)
    if not Fs:
        return None
    return C.bvh_from(np.concatenate(Vs), Fs)


def clothing_under(bd, clothing, region):
    """Under() for a body region with the clothing that covers it: 'torso'/'arm' use the shirt cache or the
    skin + SHIRT_MM; 'leg' uses the trousers cache (outermost of shell and pockets) or the skin +
    TROUSERS_MM. Returns (Under, note)."""
    mk = masks(bd)
    if region == "torso":
        keep = (mk["limb"] < 0.5) & (mk["head"] < 0.5)
        cache = clothing.get("shirt")
        fallback = SHIRT_MM
    elif region == "arm":
        keep = mk["arm"] > 0.3
        cache = clothing.get("shirt")
        fallback = SHIRT_MM
    elif region == "leg":
        keep = mk["leg"] > 0.3
        cache = clothing.get("trousers")
        fallback = TROUSERS_MM
    elif region == "waist":
        keep = (mk["limb"] < 0.5) & (mk["head"] < 0.5)
        cache = clothing.get("trousers")
        fallback = TROUSERS_MM
    else:
        raise ValueError(region)
    sk = skin_bvh(bd, keep)
    if cache is not None:
        ob_bvh = region_bvh(bd, list(cache.all_objects), keep)
        # the cache is the surface; the skin + a minimum allowance stays as a floor where the garment is thin
        return Under([(ob_bvh, 0.8), (sk, 2.0)]), f"fitted to the {cache.name} cache (+0.8 mm)"
    return Under([(sk, fallback)]), f"no cache: skin + {fallback:g} mm assumed"


# --------------------------------------------------------------------------- rendering

def _clay_of(ob, default=(0.45, 0.46, 0.48)):
    if ob.get("sgt_clay"):
        return tuple(ob["sgt_clay"])
    if ob.type == "MESH" and ob.data.materials and ob.data.materials[0] is not None:
        c = ob.data.materials[0].diffuse_color
        g = 0.42
        return tuple(0.55 * (c[i] ** (1 / 2.2)) + 0.45 * g for i in range(3))
    return default


def render_rest(part, colls, context_colls, target_mm, size_mm, out_dir=None,
                views=("front", "side", "back", "threequarter")):
    """Workbench clay renders on the rest body: front (from -Y), side (from his right, -X), back (from +Y),
    three-quarter (front-right, perspective). Gear in tinted clay from its material, clothing context in a
    dark neutral clay."""
    import bpy
    sc = bpy.context.scene
    out_dir = out_dir or os.path.join(C.RENDERS, part)
    restore = C.visible_only(list(colls) + list(context_colls))
    C._workbench(sc, "OBJECT", bg=(0.86, 0.86, 0.84))
    bpy.data.objects[C.BODY].color = (*C.SKIN_CLAY, 1.0)
    for c in context_colls:
        for ob in c.all_objects:
            ob.color = (0.30, 0.31, 0.33, 1.0)
    for c in colls:
        for ob in c.all_objects:
            ob.color = (*_clay_of(ob), 1.0)
    cam = C._aux_camera()
    sc.camera = cam
    t = np.asarray(target_mm, float)
    out = []
    for v in views:
        if v in ("front", "side", "back"):
            cam.data.type, cam.data.ortho_scale = "ORTHO", size_mm * MM * 0.75
            off = {"front": [0, -4000, 0], "side": [-4000, 0, 0], "back": [0, 4000, 0]}[v]
            C._look(cam, t + off, t)
        else:
            cam.data.type, cam.data.lens = "PERSP", 85.0
            dd = size_mm * 85.0 / 24.0 * 0.75
            C._look(cam, t + np.array([-0.62, -0.78, 0.18]) * dd, t)
        sc.render.resolution_x, sc.render.resolution_y = 900, 1200
        sc.render.resolution_percentage = 100
        out.append(C._render(os.path.join(out_dir, f"{part}_rest_{v}.png")))
    restore()
    return out


def load_carbine(rig):
    """Append Part.Carbine from cache/parts/carbine.blend and place Carbine.Root in the posed right hand
    (hero_pose.json carbine_frame: matrix_in_parent_bone relative to the posed pose_bone.matrix of wrist.R).
    Call after the rig is posed. Returns the collection or None."""
    import bpy
    from mathutils import Matrix
    path = os.path.join(C.PARTS_DIR, "carbine.blend")
    if not os.path.exists(path):
        return None
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == "Part.Carbine"]
    coll = dst.collections[0]
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    cf = json.load(open(C.HERO_JSON))["carbine_frame"]
    pb = rig.pose.bones[cf["parent_bone"]]
    M = rig.matrix_world @ pb.matrix @ Matrix(cf["matrix_in_parent_bone"])
    root = bpy.data.objects["Carbine.Root"]
    root.matrix_world = M
    bpy.context.view_layer.update()
    return coll


def _tri_bvh(ob):
    V, F = C.evaluated_world_mm(ob, disable=())
    return C.bvh_from(V, F)


def check_posed(gear_colls, body, others=None, label="posed"):
    """Interpenetration in the current pose: for every gear object, the count of intersecting triangle pairs
    against the body, each clothing/other object, and every other gear object (BVH overlap), plus the
    signed clearance of its vertices to the skin. Returns a dict."""
    others = others or []
    gear = [o for c in gear_colls for o in c.all_objects if o.type == "MESH"]
    oth = [o for c in others for o in c.all_objects if o.type == "MESH"]
    bvh = {o.name: _tri_bvh(o) for o in gear + oth}
    body_b = C.body_bvh(body)
    rep = {"body": {}, "other": {}, "gear": {}, "clearance": {}}
    for o in gear:
        n = len(bvh[o.name].overlap(body_b))
        if n:
            rep["body"][o.name] = n
    for o in gear:
        for q in oth:
            n = len(bvh[o.name].overlap(bvh[q.name]))
            if n:
                rep["other"][f"{o.name} x {q.name}"] = n
    for i, o in enumerate(gear):
        for q in gear[i + 1:]:
            n = len(bvh[o.name].overlap(bvh[q.name]))
            if n:
                rep["gear"][f"{o.name} x {q.name}"] = n
    cl = C.clearance(gear, body, label)
    rep["clearance"] = {k: v["min_mm"] for k, v in cl.items()}
    say(label, "overlaps body", json.dumps(rep["body"]))
    say(label, "overlaps other", json.dumps(rep["other"]))
    say(label, "overlaps gear", json.dumps(rep["gear"]))
    return rep


def render_part_hero(part, coll, crops, extra_colls=()):
    """The posed part (with extra collections, e.g. clothing and carbine) through the hero camera for each
    crop preset, each beside its reference crop. The rig must be posed."""
    out = []
    for pid in crops:
        lab = pid.split(".", 1)[1]
        o = os.path.join(C.RENDERS, part)
        C.render_hero([coll, *extra_colls], pid, os.path.join(o, f"{part}_hero_{lab}.png"),
                      os.path.join(o, f"{part}_hero_{lab}_pair.png"))
        out.append(lab)
    return out


def finish_part(part, coll, body, rig, clothing, rest_target, rest_size, crops, extra=None):
    """Save the cache, render rest views, pose, render the hero crops (with the clothing and the carbine),
    check interpenetration posed, write renders/<part>/<part>_check.json."""
    import bpy
    C.save_part(part, coll, extra=extra)
    C.rest_pose(rig)
    render_rest(part, [coll], list(clothing.values()), rest_target, rest_size)
    rest_rep = check_posed([coll], body, list(clothing.values()), f"{part} rest")
    used = C.apply_hero_pose(rig)
    carb = load_carbine(rig)
    ctx = list(clothing.values()) + ([carb] if carb else [])
    render_part_hero(part, coll, crops, ctx)
    rep = check_posed([coll], body, ctx, f"{part} posed")
    rep["pose"] = used
    rep["rest"] = rest_rep
    os.makedirs(os.path.join(C.RENDERS, part), exist_ok=True)
    with open(os.path.join(C.RENDERS, part, f"{part}_check.json"), "w") as f:
        json.dump(rep, f, indent=1)
    C.rest_pose(rig)
    return rep


def together(parts=GEAR):
    """All gear caches, the clothing caches that exist and the carbine on the posed body through the hero
    camera beside the reference soldier crop: renders/round_01/gear_hero.png (+ _render.png, .json)."""
    import bpy
    body, rig = C.open_base()
    clothing = load_clothing(rig)
    gear = []
    for p in parts:
        if os.path.exists(os.path.join(C.PARTS_DIR, f"{p}.blend")):
            gear.append(C.load_part(p, rig))
    used = C.apply_hero_pose(rig)
    carb = load_carbine(rig)
    out = os.path.join(C.RENDERS, "round_01", "gear_hero.png")
    colls = [c for c in gear if c] + list(clothing.values()) + ([carb] if carb else [])
    C.render_hero(colls, "ref.soldier_full", out.replace(".png", "_render.png"), out)
    C.render_hero(colls, "ref.torso_vest", out.replace(".png", "_torso_render.png"),
                  out.replace(".png", "_torso.png"))
    C.render_hero(colls, "ref.belt_hips", out.replace(".png", "_belt_render.png"),
                  out.replace(".png", "_belt.png"))
    rep = check_posed([c for c in gear if c], body, list(clothing.values()) + ([carb] if carb else []),
                      "all gear posed")
    rep["pose"] = used
    rep["clothing"] = list(clothing)
    with open(out.replace(".png", ".json"), "w") as f:
        json.dump(rep, f, indent=1)
    return out


# --------------------------------------------------------------------------- detail helpers (round 2)

def hw_object(name, coll, piece, M, material):
    """A lib.gear_hardware Piece (ladder-lock, tri-glide, rivet, screw head...) placed by the 4 x 4 frame M
    (mm) as a world-space identity object with one flat material (the binds and checks expect that)."""
    from mathutils import Matrix
    from lib import gear_hardware as GH
    ob = GH.to_object(name, piece, matrix=M, material=None, coll=coll)
    ob.data.transform(ob.matrix_world)
    ob.matrix_world = Matrix.Identity(4)
    ob.data.materials.clear()
    ob.data.materials.append(material)
    return ob


def tube(name, coll, pts, radius, material, closed=False, sides=10, step=2.0):
    """A round tube (lib.sweep.Tube) along points (mm): shock cord, piping, rolled edges."""
    from lib import sweep as SW
    P = SW.Path(np.asarray(pts, float), closed=closed).resampled(step)
    ob = SW.Tube(P, radius, sides=sides, caps=not closed).to_object(name, coll)
    ob.data.materials.clear()
    ob.data.materials.append(material)
    return ob


def edge_profile(e, bead=0.9, bead_w=3.0, ramp=1.5):
    """Thickness added at distance e (mm) inside a moulded plate's outline: a rolled rim bead `bead` proud
    for `bead_w` mm, blending to zero over `ramp` mm (use with slab(t_field_fn=...))."""
    if e <= bead_w:
        return bead
    if e >= bead_w + ramp:
        return 0.0
    t = (e - bead_w) / ramp
    return bead * (1.0 - t * t * (3.0 - 2.0 * t))


def smoothstep(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


if __name__ == "__main__":
    a = C._argv()
    if a and a[0] == "--together":
        together(tuple(a[1:]) or GEAR)
