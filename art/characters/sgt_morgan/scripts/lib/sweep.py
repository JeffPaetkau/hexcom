"""Straps and laces swept along paths (spec 18 §4.3; used by spec 02's ankle strap, stays and laces, spec 13's
webbing and spec 12's straps).

Millimetres and world space in the API; meshes come out in metres at the identity transform. The pieces:

* `Surface(ob)`: a BVH of an object's evaluated mesh in world mm, with smooth (interpolated vertex) normals,
  for projection, ray tests and signed distances.
* `Path`: points (N, 3) with per-point normals, `fixed` (the normal is a constraint on the frame), `on` (how
  much the point lies on the surface, 0..1, for conforming a strip across its width), `closed`, and the
  Surface it was made on. `surface_path()` makes one: a centripetal Catmull-Rom curve through control
  points, projected onto the target by nearest point, then three rounds of resampling to an even `step`
  along the surface, smoothing along the path (a far projection onto facets zigzags) and moving each point
  onto the surface along its normal (a nearest-point move would slide it sideways again); its normals
  smoothed along the path; lifted by `standoff` (one value, or one per control point: a lace's crossing
  lifts).
* `rmf_frames(path)`: rotation-minimising frames (T, N, B) by the double reflection method (Wang et al. 2008),
  with the roll corrected to every fixed normal and interpolated between them in arc length, so a strip on
  a surface keeps the surface normal and twists as little as possible between constraints (through a
  buckle); without constraints a closed path spreads its holonomy so the frame closes.
* `strip()`: a solid strap swept along the path: its underside lies on the path (surface + standoff), its
  thickness grows along N (the convention of the prototype's webbing recipe, made exact: the sweep builds
  the thickness itself, so there is no Solidify sign to get wrong and a fold can turn the strap over);
  quads across, seeded roll (`twist_deg`) and wander (`jitter`), `sag` (a lift along N: one bay over the
  path, (amplitude, pitch) bays between tacks with ±20 % seeded amplitudes, or a per-point array), and the
  underside conformed to the surface across its width where the path is on it (a 15 mm strap on a 60 mm
  shaft would otherwise float 0.5 mm at its edges).
* `fold_end(strip, length)`: the end folded under for `length` mm (the folded layer under the strap, the
  strap lifted over it on a short ramp, a half-round turn between), at either end.
* `tube(path, radius, sides)`: a round (or squashed) tube on the frames, radius per point if wanted: laces
  as meshes, piping, cords.
* `thread(path, hardware, slots)`: the path re-routed through slots (a buckle's, a ladder-lock's, a keeper's,
  an eyelet's): a lead-in from the path, straight through each slot along its axis with the strip's normal
  set to the slot's `up`, an arc between slots that clears the bar between them, and a lead-out back onto
  the path (or straight out when the path ends there). Leads are cubics whose tangent lengths minimise the
  sharpest bend, lengthened when `min_radius` asks for gentler bends than the lead allows.
* Diagnostics: `Path.turning_deg()`, `Path.min_bend_radius()`, `roll_steps()` (twist against parallel
  transport), `penetration()`, `Sweep.manifold()`, `Sweep.volume()`.

Every sweep is a closed, consistently outward-oriented manifold (checked by its signed volume), with a
`UV.Real` layer in metres (u along, v around the perimeter; spec 16 §5.1: straps are unwrapped straight
with u along them). `penetration()` measures how deep a sweep's vertices sit inside a Surface.
"""
import math

import numpy as np

MM = 0.001


# --------------------------------------------------------------------------- small maths

def _unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(n > 1e-12, n, 1.0)


def _smoothstep(x, a, b):
    if b == a:
        return (np.asarray(x, float) >= a).astype(float)
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _arclen(co):
    if len(co) < 2:
        return np.zeros(len(co))
    return np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(co, axis=0), axis=1))])


def _cr_scalar(values, t):
    """Uniform Catmull-Rom of scalar values at fractional indices t (clamped at the ends)."""
    v = np.asarray(values, float)
    if len(v) == 1:
        return np.full(len(np.atleast_1d(t)), v[0])
    t = np.clip(np.asarray(t, float), 0.0, len(v) - 1.0)
    i = np.minimum(np.floor(t).astype(int), len(v) - 2)
    f = t - i
    p0, p1 = v[np.maximum(i - 1, 0)], v[i]
    p2, p3 = v[i + 1], v[np.minimum(i + 2, len(v) - 1)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)


def catmull_rom(points, closed=False, per_mm=4.0):
    """A centripetal Catmull-Rom curve through the points, sampled about per_mm samples a millimetre.
    Returns (samples (M, 3), parameter (M,): control index + fraction)."""
    P = np.asarray(points, float)
    if len(P) < 3:
        n = max(2, int(math.ceil(np.linalg.norm(P[-1] - P[0]) * per_mm)) + 1)
        f = np.linspace(0.0, 1.0, n)
        return P[0] + f[:, None] * (P[-1] - P[0]), f * (len(P) - 1)
    ext = np.vstack([P[-1], P, P[0], P[1]]) if closed else np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    segs = len(P) if closed else len(P) - 1
    out, par = [], []
    for k in range(segs):
        p0, p1, p2, p3 = ext[k], ext[k + 1], ext[k + 2], ext[k + 3]
        t0 = 0.0
        t1 = t0 + max(np.linalg.norm(p1 - p0), 1e-9) ** 0.5
        t2 = t1 + max(np.linalg.norm(p2 - p1), 1e-9) ** 0.5
        t3 = t2 + max(np.linalg.norm(p3 - p2), 1e-9) ** 0.5
        n = max(2, int(math.ceil(np.linalg.norm(p2 - p1) * per_mm)))
        last = (k == segs - 1) and not closed
        f = np.linspace(0.0, 1.0, n + 1 if last else n, endpoint=last)
        t = (t1 + f * (t2 - t1))[:, None]
        a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
        a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
        a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
        b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
        b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
        out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
        par.append(k + f)
    return np.vstack(out), np.concatenate(par)


def _resample(co, step, closed=False, extra=()):
    """Even samples every ~step along the polyline (the closing segment too when closed); extra arrays
    (N,) or (N, k) are interpolated with it. Returns (co, [extras])."""
    pts = np.vstack([co, co[:1]]) if closed else co
    ex = [np.concatenate([e, e[:1]]) if closed else e for e in (np.asarray(e, float) for e in extra)]
    s = _arclen(pts)
    L = s[-1]
    n = max(int(round(L / step)), 1)
    t = np.linspace(0.0, L, n, endpoint=False) if closed else np.linspace(0.0, L, n + 1)
    out = np.stack([np.interp(t, s, pts[:, k]) for k in range(3)], 1)
    res = []
    for e in ex:
        if e.ndim == 1:
            res.append(np.interp(t, s, e))
        else:
            res.append(np.stack([np.interp(t, s, e[:, k]) for k in range(e.shape[1])], 1))
    return out, res


def _gauss_smooth(v, step, sigma, closed=False):
    """Gaussian smoothing of evenly spaced per-point vectors (spacing `step`, sigma in mm): wrapped when
    closed, point-reflected at the ends when open (so the end points and straight runs stay where they are)."""
    v = np.asarray(v, float)
    n = len(v)
    k = int(math.ceil(3.0 * sigma / max(step, 1e-9)))
    if sigma <= 0 or n < 3 or k < 1:
        return v
    k = min(k, n - 1)
    x = np.arange(-k, k + 1) * step
    g = np.exp(-0.5 * (x / sigma) ** 2)
    g /= g.sum()
    if closed:
        pad = np.vstack([v[-k:], v, v[:k]])
    else:
        pad = np.vstack([2 * v[0] - v[k:0:-1], v, 2 * v[-1] - v[-2:-k - 2:-1]])
    out = np.empty_like(v)
    for c in range(v.shape[1]):
        out[:, c] = np.convolve(pad[:, c], g, mode="valid")
    return out


def noise(s, seed, corr, period=None):
    """Smooth seeded 1-D noise in about [-1, 1] at arc lengths s: Catmull-Rom through uniform random knots
    every `corr` mm (periodic over `period` when given, so a closed strap's roll meets itself)."""
    s = np.asarray(s, float)
    rng = np.random.default_rng(seed)
    if period:
        k = max(int(round(period / corr)), 3)
        knots = rng.uniform(-1.0, 1.0, k)
        u = (s / period) * k
        i = np.floor(u).astype(int)
        f = u - i
        p = [knots[(i + d) % k] for d in (-1, 0, 1, 2)]
    else:
        k0 = int(math.floor(s.min() / corr)) - 2 if len(s) else 0
        k1 = int(math.ceil(s.max() / corr)) + 3 if len(s) else 3
        knots = rng.uniform(-1.0, 1.0, k1 - k0 + 1)
        u = s / corr - k0
        i = np.floor(u).astype(int)
        f = u - i
        p = [knots[np.clip(i + d, 0, len(knots) - 1)] for d in (-1, 0, 1, 2)]
    p0, p1, p2, p3 = p
    v = 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f
               + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)
    return np.clip(v, -1.0, 1.0)


def _hermite(p0, m0, p1, m1, step):
    """A cubic Hermite from p0 (tangent m0) to p1 (tangent m1), resampled every ~step; p0 excluded."""
    u = np.linspace(0.0, 1.0, 400)[:, None]
    h00, h10 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u
    h01, h11 = -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
    c = h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1
    out, _ = _resample(c, step)
    return out[1:]


_FACTORS = np.array([0.5, 0.7, 0.85, 1.0, 1.2, 1.45, 1.75, 2.1, 2.5, 3.0])


def _blend(p0, t0, p1, t1, step):
    """A cubic Hermite from p0 (direction t0) to p1 (direction t1) whose two tangent lengths are picked from
    multiples of the chord to make its sharpest bend as gentle as possible; p0 excluded. A plain Hermite
    with chord-length tangents puts the whole turn at the end where the directions disagree (a 60° turn
    into a 6 mm lead bends at 1.7 mm radius, tighter than a 4 mm lace)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ch = max(float(np.linalg.norm(p1 - p0)), 1e-9)
    t0, t1 = _unit(np.asarray(t0, float)), _unit(np.asarray(t1, float))
    u = np.linspace(0.0, 1.0, 65)[None, :, None]
    a, b = (x.ravel()[:, None, None] for x in np.meshgrid(_FACTORS, _FACTORS))
    m0, m1 = a * ch * t0, b * ch * t1
    c1 = (6 * u ** 2 - 6 * u) * p0 + (3 * u ** 2 - 4 * u + 1) * m0 + (-6 * u ** 2 + 6 * u) * p1 + (3 * u ** 2 - 2 * u) * m1
    c2 = (12 * u - 6) * p0 + (6 * u - 4) * m0 + (-12 * u + 6) * p1 + (6 * u - 2) * m1
    sp = np.linalg.norm(c1, axis=2)
    kappa = np.linalg.norm(np.cross(c1, c2), axis=2) / np.maximum(sp, 1e-9) ** 3
    score = kappa.max(1) * (1.0 + 0.01 * (a.ravel() + b.ravel()))  # ties go to the shorter curve
    k = int(np.argmin(score))
    return _hermite(p0, m0[k, 0], p1, m1[k, 0], step)


# --------------------------------------------------------------------------- the target surface

class Surface:
    """A BVH of an object's evaluated mesh in world mm, with its vertex normals for smooth interpolation."""

    def __init__(self, ob, depsgraph=None):
        import bpy
        from mathutils.bvhtree import BVHTree
        dg = depsgraph or bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        try:
            me.calc_loop_triangles()
            V, T = len(me.vertices), len(me.loop_triangles)
            co = np.empty(V * 3)
            me.vertices.foreach_get("co", co)
            vn = np.empty(V * 3)
            me.vertex_normals.foreach_get("vector", vn)
            tri = np.empty(T * 3, np.int64)
            me.loop_triangles.foreach_get("vertices", tri)
        finally:
            ev.to_mesh_clear()
        M = np.array(ob.matrix_world, float)
        self.co = (co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]) / MM
        self.vn = _unit(vn.reshape(-1, 3) @ np.linalg.inv(M[:3, :3]))
        self.tris = tri.reshape(-1, 3)
        self.name = ob.name
        self.bvh = BVHTree.FromPolygons(self.co.tolist(), self.tris.tolist())

    def _normal(self, p, ti):
        a, b, c = self.co[self.tris[ti]]
        v0, v1, v2 = b - a, c - a, p - a
        d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
        d20, d21 = v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-18:
            w = np.array([1 / 3, 1 / 3, 1 / 3])
        else:
            v = (d11 * d20 - d01 * d21) / den
            w_ = (d00 * d21 - d01 * d20) / den
            w = np.clip(np.array([1 - v - w_, v, w_]), 0.0, 1.0)
            w /= max(w.sum(), 1e-12)
        return _unit(w @ self.vn[self.tris[ti]])

    def nearest(self, p):
        """(point, smooth normal, face normal, distance) of the nearest surface point, or None."""
        loc, nf, idx, d = self.bvh.find_nearest(tuple(p))
        if loc is None:
            return None
        q = np.array(loc)
        return q, self._normal(q, idx), np.array(nf), d

    def ray(self, origin, direction, dist):
        """(point, smooth normal, distance) of the first hit along direction within dist, or None."""
        loc, nf, idx, d = self.bvh.ray_cast(tuple(origin), tuple(direction), dist)
        if loc is None:
            return None
        q = np.array(loc)
        return q, self._normal(q, idx), d

    def signed_distance(self, pts):
        """Signed distance (mm) of each point from the surface: negative inside (against the face normal)."""
        out = np.empty(len(pts))
        for i, p in enumerate(np.asarray(pts, float)):
            q, _, nf, d = self.nearest(p)
            out[i] = d if (p - q) @ nf >= 0 else -d
        return out


def _surface(target):
    return target if isinstance(target, Surface) else Surface(target)


def _onto(surf, co, reach=2.0):
    """Points near the surface moved onto it along their smooth normals (a ray from reach mm above), not to
    their nearest points: on a faceted mesh the nearest point slides sideways from facet to facet, the
    normal move does not. Returns (points, normals); a ray that slips through an edge falls back on the
    nearest point."""
    out, nrm = np.empty_like(co), np.empty_like(co)
    for i, p in enumerate(co):
        q, n, _, d = surf.nearest(p)
        r = reach + d
        h = surf.ray(p + n * r, -n, 2.0 * r)
        out[i], nrm[i] = (h[0], h[1]) if h is not None else (q, n)
    return out, nrm


# --------------------------------------------------------------------------- paths

class Path:
    """A sampled path in world mm (see the module docstring)."""

    def __init__(self, co, normal=None, fixed=None, on=None, closed=False, surface=None, standoff=0.0):
        self.co = np.array(co, float).reshape(-1, 3)
        n = len(self.co)
        self.normal = np.zeros((n, 3)) if normal is None else _unit(np.array(normal, float).reshape(-1, 3))
        if fixed is None:
            fixed = normal is not None
        self.fixed = np.broadcast_to(np.asarray(fixed, bool), (n,)).copy()
        self.on = np.broadcast_to(np.asarray(0.0 if on is None else on, float), (n,)).copy()
        self.closed, self.surface, self.standoff = bool(closed), surface, float(np.mean(standoff))

    def __len__(self):
        return len(self.co)

    @property
    def s(self):
        return _arclen(self.co)

    @property
    def length(self):
        L = self.s[-1]
        return L + (np.linalg.norm(self.co[0] - self.co[-1]) if self.closed else 0.0)

    def tangents(self):
        c = self.co
        if self.closed:
            d = np.roll(c, -1, 0) - np.roll(c, 1, 0)
        else:
            d = np.gradient(c, axis=0) if len(c) > 1 else np.array([[1.0, 0.0, 0.0]])
        return _unit(d)

    def turning_deg(self):
        """The turn at each interior point (degrees) between its two segments."""
        d = _unit(np.diff(np.vstack([self.co, self.co[:1]]) if self.closed else self.co, axis=0))
        if self.closed:
            dots = np.sum(d * np.roll(d, 1, 0), 1)
        else:
            dots = np.sum(d[1:] * d[:-1], 1)
        return np.degrees(np.arccos(np.clip(dots, -1.0, 1.0)))

    def min_bend_radius(self):
        """The tightest bend (mm): segment length over turn angle. A tube folds inside itself below its
        radius, a strap bent toward its top face below its thickness."""
        turn = np.radians(self.turning_deg())
        if not len(turn):
            return math.inf
        pts = np.vstack([self.co, self.co[:1]]) if self.closed else self.co
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        ds = 0.5 * (seg + np.roll(seg, 1)) if self.closed else 0.5 * (seg[:-1] + seg[1:])
        return float((ds / np.maximum(turn, 1e-12)).min())

    def sub(self, i0, i1):
        """Points i0..i1-1 as an open path."""
        return Path(self.co[i0:i1], self.normal[i0:i1], self.fixed[i0:i1], self.on[i0:i1], False,
                    self.surface, self.standoff)

    def reversed(self):
        return Path(self.co[::-1], self.normal[::-1], self.fixed[::-1], self.on[::-1], self.closed,
                    self.surface, self.standoff)

    def resampled(self, step):
        co, (nrm, fx, on) = _resample(self.co, step, self.closed, (self.normal, self.fixed.astype(float), self.on))
        return Path(co, nrm, fx > 0.999, on, self.closed, self.surface, self.standoff)

    def lifted(self, lift):
        """The path moved along its normals by lift (mm, scalar or per point)."""
        p = Path(self.co + self.normal * np.asarray(lift, float).reshape(-1, 1), self.normal, self.fixed,
                 self.on, self.closed, self.surface, self.standoff)
        return p

    @staticmethod
    def join(parts, surface=None, standoff=None):
        parts = [p for p in parts if len(p)]
        return Path(np.vstack([p.co for p in parts]), np.vstack([p.normal for p in parts]),
                    np.concatenate([p.fixed for p in parts]), np.concatenate([p.on for p in parts]), False,
                    surface if surface is not None else parts[0].surface,
                    standoff if standoff is not None else parts[0].standoff)


def surface_path(target, points, standoff=0.0, step=1.0, *, closed=False, smooth=True, iterations=3,
                 path_sigma=2.0, normal_sigma=2.0, max_dist=None):
    """A path through the control points (mm, world) laid on the target's surface (see the module
    docstring). standoff: mm above the surface, one value or one per control point. Between projection
    rounds the points are smoothed along the path (path_sigma, mm): a point projected from far off a
    faceted surface lands where its facet's normal sends it, so a smooth curve 15 mm off a mesh of 2 mm
    facets comes back with 0.3 mm of sideways zigzag (15-20° turns a millimetre) that re-projecting
    cannot remove. max_dist: refuse control points farther than this from the surface (a misplaced
    point drags the path elsewhere)."""
    surf = _surface(target)
    P = np.asarray(points, float)
    if len(P) < 2:
        raise ValueError("a path needs two control points or more")
    dev = [surf.nearest(p)[3] for p in P]
    if max_dist is not None and max(dev) > max_dist:
        raise ValueError(f"control point {int(np.argmax(dev))} lies {max(dev):.1f} mm off {surf.name} "
                         f"(max_dist {max_dist})")
    if smooth:
        co, par = catmull_rom(P, closed)
    else:
        seg = [np.linspace(P[k], P[(k + 1) % len(P)], 64, endpoint=False) for k in range(len(P) - (0 if closed else 1))]
        co = np.vstack(seg + ([] if closed else [P[-1:]]))
        par = np.concatenate([k + np.linspace(0, 1, 64, endpoint=False) for k in range(len(seg))]
                             + ([] if closed else [[len(P) - 1.0]]))
    co, (par,) = _resample(co, step / 4.0, closed, (par,))
    for it in range(iterations):
        co = np.array([surf.nearest(p)[0] for p in co]) if it == 0 else _onto(surf, co)[0]
        co, (par,) = _resample(co, step, closed, (par,))
        co = _gauss_smooth(co, step, path_sigma, closed)
    co, normals = _onto(surf, co)
    seg = np.linalg.norm(np.diff(co, axis=0), axis=1)
    normals = _unit(_gauss_smooth(normals, float(seg.mean()) if len(seg) else step, normal_sigma, closed))
    so = np.atleast_1d(np.asarray(standoff, float))
    if len(so) == 1:
        lift = np.full(len(co), so[0])
    elif len(so) == len(P):
        lift = _cr_scalar(np.concatenate([so, so[:1]]) if closed else so, par)
    else:
        raise ValueError(f"{len(so)} standoffs for {len(P)} control points")
    path = Path(co + normals * lift[:, None], normals, True, 1.0, closed, surf, float(so.mean()))
    path.control_deviation = float(max(dev))
    return path


# --------------------------------------------------------------------------- frames

def _rmf(x, T, r0):
    n = len(x)
    r = np.empty((n, 3))
    r[0] = r0
    for i in range(n - 1):
        v1 = x[i + 1] - x[i]
        c1 = v1 @ v1
        if c1 < 1e-18:
            r[i + 1] = r[i]
            continue
        rL = r[i] - (2.0 / c1) * (v1 @ r[i]) * v1
        tL = T[i] - (2.0 / c1) * (v1 @ T[i]) * v1
        v2 = T[i + 1] - tL
        c2 = v2 @ v2
        r[i + 1] = rL - (2.0 / c2) * (v2 @ rL) * v2 if c2 > 1e-18 else rL
    return r


def _perp(t, hint=None):
    h = np.asarray(hint, float) if hint is not None else None
    if h is None or np.linalg.norm(np.cross(h, t)) < 1e-6:
        h = np.eye(3)[int(np.argmin(np.abs(t)))]
    p = h - (h @ t) * t
    return p / np.linalg.norm(p)


def _angle_about(r, d, T):
    return np.arctan2(np.sum(np.cross(r, d) * T, 1), np.sum(r * d, 1))


def rmf_frames(path, up=None):
    """Rotation-minimising frames (T, N, B), each (N, 3), corrected to the path's fixed normals (see the
    module docstring). up: the first normal when nothing is fixed."""
    P = path if isinstance(path, Path) else Path(path)
    x, n = P.co, len(P)
    T = P.tangents()
    fi = np.flatnonzero(P.fixed)
    if len(fi):
        d_all = P.normal - np.sum(P.normal * T, 1, keepdims=True) * T
        ok = np.linalg.norm(d_all, axis=1) > 1e-3
        fi = fi[ok[fi]]
    r0 = _perp(T[0], P.normal[fi[0]] if len(fi) else up)
    r = _unit(_rmf(x, T, r0))
    r = _unit(r - np.sum(r * T, 1, keepdims=True) * T)
    s = P.s
    alpha = np.zeros(n)
    if len(fi):
        d = _unit(d_all[fi])
        a = np.unwrap(_angle_about(r[fi], d, T[fi]))
        alpha = np.interp(s, s[fi], a)
    elif P.closed and n > 2:
        r_close = _rmf(np.vstack([x[-1:], x[:1]]), np.vstack([T[-1:], T[:1]]), r[-1])[1]
        r_close = _unit(r_close - (r_close @ T[0]) * T[0])
        a_end = float(_angle_about(r_close[None], r[:1], T[:1])[0])
        alpha = a_end * s / P.length
    N = np.cos(alpha)[:, None] * r + np.sin(alpha)[:, None] * np.cross(T, r)
    N = _unit(N)
    return T, N, np.cross(T, N)


# --------------------------------------------------------------------------- sweeps

class Sweep:
    """Swept geometry in mm: verts (V, 3), faces (list of index tuples), uv per face corner (metres)."""

    smooth = False
    uv_name = "UV.Real"

    def __init__(self):
        self._geo = None

    def geometry(self):
        if self._geo is None:
            v, f, uv = self._build()
            if _signed_volume(v, f) < 0:
                f = [tuple(reversed(x)) for x in f]
                uv = [u[::-1] for u in uv]
            self._geo = (v, f, uv)
        return self._geo

    @property
    def verts(self):
        return self.geometry()[0]

    @property
    def faces(self):
        return self.geometry()[1]

    def volume(self):
        v, f, _ = self.geometry()
        return _signed_volume(v, f)

    def manifold(self):
        """True when the surface is closed and consistently oriented: every directed edge once, with its
        reverse in a neighbouring face."""
        v, f, _ = self.geometry()
        a = np.concatenate([np.asarray(x, np.int64) for x in f])
        b = np.concatenate([np.roll(np.asarray(x, np.int64), -1) for x in f])
        fwd, rev = a * len(v) + b, b * len(v) + a
        return bool(len(np.unique(fwd)) == len(fwd) and np.isin(rev, fwd).all())

    def mesh(self, name, smooth=None):
        """A bpy Mesh (metres, world space) with the UV.Real layer."""
        import bpy
        v, f, uv = self.geometry()
        me = bpy.data.meshes.new(name)
        me.from_pydata((v * MM).tolist(), [], [list(x) for x in f])
        lay = me.uv_layers.new(name=self.uv_name)
        lay.data.foreach_set("uv", np.concatenate(uv).astype(np.float32).ravel())
        if self.smooth if smooth is None else smooth:
            me.shade_smooth()
        me.validate()
        me.update()
        return me

    def to_object(self, name, coll=None, scope=None, smooth=None):
        """The sweep as an object: through scope.new_object (replace.part_scope) when given, else linked to
        coll (default the scene's collection)."""
        import bpy
        me = self.mesh(name, smooth)
        if scope is not None:
            return scope.new_object(name, me, coll)
        ob = bpy.data.objects.new(name, me)
        (coll or bpy.context.scene.collection).objects.link(ob)
        return ob


def _fan(faces):
    """Fan triangles (T, 3) of the faces, grouped by face size so numpy does the work."""
    by = {}
    for f in faces:
        by.setdefault(len(f), []).append(f)
    tris = []
    for n, fs in by.items():
        a = np.asarray(fs, np.int64)
        for k in range(1, n - 1):
            tris.append(a[:, [0, k, k + 1]])
    return np.vstack(tris) if tris else np.zeros((0, 3), np.int64)


def _signed_volume(v, faces):
    t = _fan(faces)
    return float(np.einsum("ij,ij->i", v[t[:, 0]], np.cross(v[t[:, 1]], v[t[:, 2]])).sum() / 6.0)


def _sweep_rings(rings, perim, u, closed, caps):
    """Faces and corner UVs of rings (n, K, 3) joined in order; perim (K + 1,) the unrolled position of
    each ring vertex around the section (mm), u (n,) along (mm). caps: list of (ring index, faces) to add
    with their corner UVs, each a list of ring-vertex index tuples."""
    n, K = rings.shape[:2]
    verts = rings.reshape(-1, 3)
    faces, uvs = [], []
    segs = n if closed else n - 1
    L_close = u[-1] + (np.linalg.norm(rings[0].mean(0) - rings[-1].mean(0)) if closed else 0.0)
    for i in range(segs):
        j = (i + 1) % n
        ui, uj = u[i], (u[j] if j > i else L_close)
        for k in range(K):
            k2 = (k + 1) % K
            faces.append((i * K + k, j * K + k, j * K + k2, i * K + k2))
            vk, vk2 = perim[k], perim[k + 1]
            uvs.append(np.array([(ui, vk), (uj, vk), (uj, vk2), (ui, vk2)]) * MM)
    for i, cap_faces, uv_fn in caps:
        for cf in cap_faces:
            faces.append(tuple(i * K + k for k in cf))
            uvs.append(np.array([uv_fn(k) for k in cf]) * MM)
    return verts, faces, uvs


class Strip(Sweep):
    """A solid strap along a path (see strip())."""

    def __init__(self, path, width, thickness, quads_across=6, twist_deg=0.0, sag=0.0, seed=0, jitter=0.0,
                 conform=True, uv_offset=None):
        super().__init__()
        if len(path) < 2:
            raise ValueError("a strip needs a path of two points or more")
        self.path, self.width, self.thickness = path, float(width), float(thickness)
        self.quads_across, self.twist_deg, self.sag, self.seed = int(quads_across), float(twist_deg), sag, seed
        self.jitter, self.conform = float(jitter), bool(conform)
        rng = np.random.default_rng(seed + 7919)
        self.uv_offset = rng.uniform(200.0, 800.0) if uv_offset is None else float(uv_offset)  # mm
        self.folds = []

    def _lift(self, s, L):
        sag = self.sag
        if sag is None or (np.isscalar(sag) and sag == 0):
            return np.zeros(len(s))
        if isinstance(sag, tuple):
            amp, pitch = sag
            k = np.floor(s / pitch).astype(int)
            rng = np.random.default_rng(self.seed + 104729)
            amps = amp * (1.0 + 0.2 * rng.uniform(-1.0, 1.0, int(k.max()) + 2))
            t = (s - k * pitch) / pitch
            return amps[k] * np.sin(np.pi * t) ** 0.8
        sag = np.asarray(sag, float)
        if sag.ndim == 0:
            return float(sag) * np.sin(np.pi * np.clip(s / L, 0.0, 1.0)) ** 0.8
        if len(sag) != len(s):
            raise ValueError(f"{len(sag)} sag values for {len(s)} path points")
        return sag

    def stations(self):
        """The sweep's stations before folds: mid-surface rows m (n, q+1, 3), normals (n, 3), tangents (n, 3),
        arc lengths u (n,)."""
        P, w, t, q = self.path, self.width, self.thickness, self.quads_across
        T, N, B = rmf_frames(P)
        s, L = P.s, P.length
        per = L if P.closed else None
        if self.twist_deg:
            th = math.radians(self.twist_deg) * noise(s, self.seed, 40.0, per)[:, None]
            N, B = np.cos(th) * N + np.sin(th) * B, np.cos(th) * B - np.sin(th) * N
        c = P.co + (B * (self.jitter * noise(s, self.seed + 1, 60.0, per))[:, None] if self.jitter else 0.0)
        x = np.linspace(-w / 2.0, w / 2.0, q + 1)
        b = c[:, None, :] + x[None, :, None] * B[:, None, :]
        if self.conform and P.surface is not None and np.any(P.on > 0):
            R = max(3.0 * t, 3.0)
            surf = P.surface

            def drop(p, n):
                """Height of the surface below p along -n (a ray, or the nearest point when a ray slips
                through a mesh edge)."""
                h = surf.ray(p + n * R, -n, 4.0 * R + 20.0)
                q = h[0] if h is not None else surf.nearest(p)[0]
                return (q - p) @ n

            for i in np.flatnonzero(P.on > 0):
                dc = drop(c[i], N[i])
                for j in range(q + 1):
                    b[i, j] += N[i] * (drop(b[i, j], N[i]) - dc) * P.on[i]
        b += N[:, None, :] * self._lift(s, L)[:, None, None]
        return {"m": b + N[:, None, :] * (t / 2.0), "n": N, "T": T, "u": s.copy()}

    def _build(self):
        st = self.stations()
        t = self.thickness
        step = max(float(np.median(np.diff(st["u"]))) if len(st["u"]) > 1 else 1.0, 1e-3)
        for at, length, gap in self.folds:
            if at in ("end", "both"):
                st = _fold(st, length, gap, t, step)
            if at in ("start", "both"):
                st = _reverse(_fold(_reverse(st), length, gap, t, step))
        m, nrm, u = st["m"], st["n"], st["u"]
        q = self.quads_across
        top = m + nrm[:, None, :] * (t / 2.0)
        bot = (m - nrm[:, None, :] * (t / 2.0))[:, ::-1]
        rings = np.concatenate([top, bot], axis=1)
        K = 2 * (q + 1)
        x = np.linspace(0.0, self.width, q + 1)
        perim = np.concatenate([x, self.width + t + x, [2 * self.width + 2 * t]])
        u = u + self.uv_offset
        caps = []
        if not self.path.closed:
            cap = [(j, j + 1, K - 2 - j, K - 1 - j) for j in range(q)]
            for i, sgn in ((0, -1.0), (len(rings) - 1, 1.0)):
                ui = u[i]

                def fn(k, ui=ui):
                    return (ui + (0.0 if k <= q else t), x[k] if k <= q else x[K - 1 - k])
                caps.append((i, cap if sgn < 0 else [c[::-1] for c in cap], fn))
        return _sweep_rings(rings, perim, u, self.path.closed, caps)


def _reverse(st):
    return {"m": st["m"][::-1, ::-1], "n": st["n"][::-1], "T": -st["T"][::-1], "u": st["u"][::-1]}


def _fold(st, length, gap, t, step):
    """Fold the last `length` mm under: lift the strap over it, turn a half round, run back underneath."""
    m, nrm, T, u = st["m"], st["n"], st["T"], st["u"]
    d = np.abs(u - u[-1])
    if length >= d[0] - 2.0 * t:
        raise ValueError(f"fold of {length} mm on a strip of {d[0]:.1f} mm")
    sgn = 1.0 if u[-1] >= u[0] else -1.0
    ramp = max(2.0 * t, 2.0)
    lift = (t + gap) * (1.0 - _smoothstep(d, length, length + ramp))
    main = m + nrm[:, None, :] * lift[:, None, None]
    r = (t + gap) / 2.0
    under = m[-1] - nrm[-1] * (t / 2.0)  # the underside row at the end, before the lift
    centre = under + nrm[-1] * (t + gap / 2.0)
    K = max(6, int(math.ceil(math.pi * r / max(step * 0.5, 0.2))))
    phi = np.pi * np.arange(1, K) / K
    TS, NS = T[-1], nrm[-1]
    rad = np.sin(phi)[:, None] * TS + np.cos(phi)[:, None] * NS
    turn_m = centre[None] + r * rad[:, None, :]
    turn_T = np.cos(phi)[:, None] * TS - np.sin(phi)[:, None] * NS
    back = np.flatnonzero(d <= length)[::-1]
    back_m = m[back]
    return {"m": np.concatenate([main, turn_m, back_m]),
            "n": np.concatenate([nrm, rad, -nrm[back]]),
            "T": np.concatenate([T, turn_T, -T[back]]),
            "u": np.concatenate([u, u[-1] + sgn * r * phi, u[-1] + sgn * (np.pi * r + d[back])])}


class Tube(Sweep):
    """A tube along a path (see tube())."""

    smooth = True

    def __init__(self, path, radius, sides=8, twist_deg=0.0, squash=None, caps=True):
        super().__init__()
        self.path, self.radius, self.sides = path, radius, int(sides)
        self.twist_deg, self.squash, self.caps = float(twist_deg), squash, bool(caps)

    def _build(self):
        P, K = self.path, self.sides
        T, N, B = rmf_frames(P)
        s = P.s
        n = len(P)
        r = np.broadcast_to(np.asarray(self.radius, float), (n,))
        sq = np.broadcast_to(np.asarray(1.0 if self.squash is None else self.squash, float), (n,))
        tw = math.radians(self.twist_deg) * s / max(P.length, 1e-9)
        phi = 2 * np.pi * np.arange(K) / K
        ang = phi[None, :] + tw[:, None]
        rings = (P.co[:, None, :] + r[:, None, None] * (np.cos(ang)[..., None] * B[:, None, :]
                                                         + sq[:, None, None] * np.sin(ang)[..., None] * N[:, None, :]))
        perim = np.linspace(0.0, 1000.0, K + 1)  # v 0..1 around (curve-UV convention), in UV metres x 1000
        caps = []
        if self.caps and not P.closed:
            for i, order in ((0, list(range(K))), (n - 1, list(range(K))[::-1])):
                def fn(k, i=i):
                    return (s[i] + 0.5 * r[i] * math.cos(phi[k]), 0.5 * r[i] * math.sin(phi[k]))
                caps.append((i, [tuple(order)], fn))
        return _sweep_rings(rings, perim, s, P.closed, caps)


def strip(path, width, thickness, quads_across=6, twist_deg=0.0, sag=0.0, seed=0, *, jitter=0.0, conform=True,
          uv_offset=None):
    """A solid strap of width x thickness mm along the path (its underside on the path); see the module
    docstring for twist_deg, sag, seed, jitter and conform. Returns a Strip (geometry built on demand)."""
    return Strip(path, width, thickness, quads_across, twist_deg, sag, seed, jitter, conform, uv_offset)


def fold_end(strip, length, at="end", gap=None):
    """Fold the strip's end ('end', 'start' or 'both') under by `length` mm; the two layers are `gap` mm
    apart (default a quarter of the thickness: the inner radius of the turn). Returns the strip."""
    if strip.path.closed:
        raise ValueError("a closed strip has no end to fold")
    if at not in ("end", "start", "both"):
        raise ValueError(f"at {at!r}: 'end', 'start' or 'both'")
    strip.folds.append((at, float(length), 0.25 * strip.thickness if gap is None else float(gap)))
    strip._geo = None
    return strip


def tube(path, radius, sides=8, *, twist_deg=0.0, squash=None, caps=True):
    """A tube of radius mm (scalar or per point) with `sides`, on the path's frames; squash (per point
    allowed) scales the radius along N (a flattened cord: 0.625 for 3.0 x 4.8); twist_deg turns the
    section along the path (the braid's own twist). Returns a Tube."""
    return Tube(path, radius, sides, twist_deg, squash, caps)


# --------------------------------------------------------------------------- threading through hardware

def _slots_world(hardware, slots):
    import bpy
    M = None
    if hardware is not None:
        if hasattr(hardware, "matrix_world"):
            M = np.array(hardware.matrix_world, float)
            M[:3, 3] /= MM
        else:
            M = np.asarray(hardware, float)
    out = []
    for sl in slots:
        if isinstance(sl, str) or hasattr(sl, "matrix_world"):
            ob = bpy.data.objects[sl] if isinstance(sl, str) else sl
            W = np.array(ob.matrix_world, float)
            out.append({"c": W[:3, 3] / MM, "a": _unit(W[:3, 2]), "up": _unit(W[:3, 1]),
                        "depth": float(ob.get("depth_mm", 2.0))})
            continue
        c = np.asarray(sl["centre"], float)
        a = np.asarray(sl["axis"], float)
        up = sl.get("up")
        if M is not None:
            c = M[:3, :3] @ c + M[:3, 3]
            a = M[:3, :3] @ a
            up = None if up is None else M[:3, :3] @ np.asarray(up, float)
        a = _unit(a)
        if up is not None:
            up = _unit(np.asarray(up, float) - (np.asarray(up, float) @ a) * a)
        out.append({"c": c, "a": a, "up": up, "depth": float(sl.get("depth", 2.0))})
    return out


def thread(path, hardware, slots, *, lead=None, clear=3.0, step=None, min_radius=None):
    """The path re-routed through the slots in order (see the module docstring). hardware: an object (slot
    dicts are in its local mm frame), a 4 x 4 matrix (mm), or None (world mm). A slot is a dict
    {"centre", "axis" (the direction of travel), "up" (the strip's normal in the slot; optional), "depth"
    (mm of straight run, default 2)} or an Empty (or its name): location the centre, local Z the axis, local
    Y up, custom property depth_mm. The path is the strip's underside or the tube's axis, so a slot's centre
    is where that passes. lead: mm of path replaced on each side (default max(4 clear, 10)); clear: the
    height of the arc over a bar between two slots whose axes oppose. min_radius: the tightest bend the
    leads may have (a lace: about 1.25 x its radius; a tube folds into itself below its radius): each lead
    is lengthened (1.5, 2, 3 x) until its blend clears it, else the gentlest is kept. The record of the
    leads used is left on the returned path as `.leads` (mm, bend radius)."""
    P = path
    if P.closed:
        raise ValueError("thread() works on an open path")
    W = _slots_world(hardware, slots)
    if not W:
        return P
    step = step or float(np.median(np.linalg.norm(np.diff(P.co, axis=0), axis=1)))
    lead = max(4.0 * clear, 10.0) if lead is None else float(lead)
    s, T = P.s, P.tangents()
    tries = (1.0,) if min_radius is None else (1.0, 1.5, 2.0, 3.0)
    leads = []

    def piece(co, normal=None, fixed=False, on=0.0):
        co = np.atleast_2d(co)
        return Path(co, np.zeros_like(co) if normal is None else np.broadcast_to(normal, co.shape), fixed, on,
                    False, P.surface, P.standoff)

    def pick(make):
        """The first lead (of `tries`) whose blend clears min_radius, else the gentlest; make(L) gives
        (index, blend, the points around it to judge the bend by) or None past the path's end."""
        best = None
        for f in tries:
            got = make(lead * f)
            if got is None:
                break
            r = Path(got[2]).min_bend_radius()
            if best is None or r > best[3]:
                best = (*got[:2], lead * f, r)
            if min_radius is None or r >= min_radius:
                break
        if best is not None:
            leads.append((round(best[2], 2), round(best[3], 3)))
        return best

    e0 = W[0]["c"] - W[0]["a"] * W[0]["depth"] / 2.0
    i_near = int(np.argmin(np.linalg.norm(P.co - e0, axis=1)))

    def lead_in(L):
        i = int(np.searchsorted(s, s[i_near] - L, side="right")) - 1
        if i < 0:
            return None
        h = _blend(P.co[i], T[i], e0, W[0]["a"], step)
        return i, h, np.vstack([P.co[max(i - 1, 0):i + 1], h, e0 + W[0]["a"] * step])

    parts = []
    got = pick(lead_in)
    if got is not None:
        i_in, h = got[0], got[1]
        parts.append(P.sub(0, i_in + 1))
        n = len(h) - 1  # the conforming fades out over the first half of the lead-in
        parts.append(piece(h[:-1], on=P.on[i_in] * (1.0 - _smoothstep(np.linspace(0, 1, max(n, 1)), 0.0, 0.5))[:n]))
    for k, sl in enumerate(W):
        e = sl["c"] - sl["a"] * sl["depth"] / 2.0
        x = sl["c"] + sl["a"] * sl["depth"] / 2.0
        n = max(int(math.ceil(sl["depth"] / step)), 2)
        run = e[None] + np.linspace(0.0, 1.0, n + 1)[:, None] * (x - e)[None]
        parts.append(piece(run, sl["up"], sl["up"] is not None))
        if k + 1 < len(W):
            nx = W[k + 1]
            e2 = nx["c"] - nx["a"] * nx["depth"] / 2.0
            ch = np.linalg.norm(e2 - x)
            Lt = ch + 4.0 * clear * max(0.0, -float(sl["a"] @ nx["a"]))
            h = _hermite(x, sl["a"] * Lt, e2, nx["a"] * Lt, step)
            parts.append(piece(h[:-1]))
    last = W[-1]
    x = last["c"] + last["a"] * last["depth"] / 2.0
    lo = max(i_near, 0)
    j_near = lo + int(np.argmin(np.linalg.norm(P.co[lo:] - x, axis=1)))

    def lead_out(L):
        j = int(np.searchsorted(s, s[j_near] + L, side="left"))
        if j >= len(P):
            return None
        h = _blend(x, last["a"], P.co[j], T[j], step)
        return j, h, np.vstack([x - last["a"] * step, x, h, P.co[j + 1:j + 2]])

    got = pick(lead_out)
    if got is None:
        n = max(int(math.ceil(lead / step)), 1)
        parts.append(piece(x[None] + np.linspace(0.0, lead, n + 1)[1:, None] * last["a"][None]))
    else:
        j_out, h = got[0], got[1]
        n = len(h) - 1
        parts.append(piece(h[:-1], on=P.on[j_out] * _smoothstep(np.linspace(0, 1, max(n, 1)), 0.5, 1.0)[:n]))
        parts.append(P.sub(j_out, len(P)))
    out = Path.join(parts)
    out.leads = leads
    return out


# --------------------------------------------------------------------------- checks

def penetration(sweep, target):
    """How deep the sweep's vertices sit inside the target (mm, >= 0), and how many are inside."""
    surf = _surface(target)
    v = sweep.verts if isinstance(sweep, Sweep) else np.asarray(sweep, float)
    sd = surf.signed_distance(v)
    inside = sd < 0
    return {"max_mm": float(-sd.min()) if inside.any() else 0.0, "inside": int(inside.sum()), "of": int(len(v))}


def roll_steps(path):
    """The roll of the frame about T at each step (degrees), measured against parallel transport (one
    double-reflection step): bending is not counted, only twist, so a flip or a kinked roll shows."""
    P = path if isinstance(path, Path) else Path(path)
    T, N, _ = rmf_frames(P)
    out = np.zeros(max(len(P) - 1, 0))
    for i in range(len(P) - 1):
        r = _rmf(P.co[i:i + 2], T[i:i + 2], N[i])[1]
        r = _unit(r - (r @ T[i + 1]) * T[i + 1])
        out[i] = math.degrees(float(_angle_about(r[None], N[i + 1:i + 2], T[i + 1:i + 2])[0]))
    return out


# --------------------------------------------------------------------------- self-test

def _cylinder_object(name, r=50.0, h=200.0, seg=128, rings=50, rough=0.0, seed=0):
    import bpy
    z = np.linspace(0.0, h, rings + 1)
    a = 2 * np.pi * np.arange(seg) / seg
    dr = np.random.default_rng(seed).uniform(-rough, rough, (rings + 1, seg))
    v = [((r + dr[i, k]) * math.cos(t) * MM, (r + dr[i, k]) * math.sin(t) * MM, zz * MM)
         for i, zz in enumerate(z) for k, t in enumerate(a)]
    v += [(0.0, 0.0, 0.0), (0.0, 0.0, h * MM)]
    f = []
    for i in range(rings):
        for k in range(seg):
            k2 = (k + 1) % seg
            f.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    b, tp = len(v) - 2, len(v) - 1
    f += [(b, (k + 1) % seg, k) for k in range(seg)]
    f += [(tp, rings * seg + k, rings * seg + (k + 1) % seg) for k in range(seg)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.shade_smooth()
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _plane_object(name, size=200.0):
    import bpy
    h = size / 2 * MM
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def selftest():
    """A ring and a vertical path on a cylinder (radii, spacing, normals, conforming), rotation-minimising
    frames on a helix against its Frenet torsion, a closed strap's volume, a fold, a tube's volume, and a
    strap threaded through a two-slot buckle (centres, axes, ups, no kinks), all sweeps closed manifolds."""
    import bpy
    R, made = {}, []
    try:
        cyl = _cylinder_object("SelftestSw.Cylinder")
        made.append(cyl)
        surf = Surface(cyl)
        # a closed ring at z 100 through 12 control points 8 mm off the surface: lands on it at 1 mm standoff
        ang = 2 * np.pi * np.arange(12) / 12
        ctrl = np.stack([58 * np.cos(ang), 58 * np.sin(ang), np.full(12, 100.0)], 1)
        ring = surface_path(surf, ctrl, standoff=1.0, step=1.0, closed=True)
        rad = np.linalg.norm(ring.co[:, :2], axis=1)
        seg = np.linalg.norm(np.diff(np.vstack([ring.co, ring.co[:1]]), axis=0), axis=1)
        radial = np.stack([np.cos(np.arctan2(ring.co[:, 1], ring.co[:, 0])),
                           np.sin(np.arctan2(ring.co[:, 1], ring.co[:, 0])), np.zeros(len(ring))], 1)
        assert np.all(np.abs(rad - 51.0) < 0.05), (rad.min(), rad.max())
        assert np.all(np.abs(ring.co[:, 2] - 100.0) < 0.05) and np.all(np.abs(seg - seg.mean()) < 0.05)
        assert abs(seg.mean() * 50.0 / 51.0 - 1.0) < 0.002  # the step is measured on the surface
        assert np.all(np.sum(ring.normal * radial, 1) > 0.9995)
        R["ring"] = {"points": len(ring), "r_mm": [round(float(rad.min()), 4), round(float(rad.max()), 4)]}

        # control points 20 mm off a rough mesh (0.05 mm facet noise): projected straight, they would zigzag
        rough = _cylinder_object("SelftestSw.Rough", seg=96, rings=60, rough=0.05, seed=4)
        made.append(rough)
        rs = Surface(rough)
        far = np.stack([70 * np.cos(ang), 70 * np.sin(ang), np.full(12, 100.0)], 1)
        raw = surface_path(rs, far, standoff=0.3, step=1.0, closed=True, path_sigma=0.0)
        fair = surface_path(rs, far, standoff=0.3, step=1.0, closed=True)
        t_raw, t_fair = float(raw.turning_deg().max()), float(fair.turning_deg().max())
        # a path on a 96-gon turns by its 3.75° facet dihedral at each edge, plus the roughness's tilts
        assert t_raw > 20.0 and t_fair < 360.0 / 96 + 2.5 and fair.min_bend_radius() > 8.0, (t_raw, t_fair)
        assert np.all(np.abs(np.linalg.norm(fair.co[:, :2], axis=1) - 50.3) < 0.35)
        R["rough_ring_max_turn_deg"] = {"unsmoothed": round(t_raw, 2), "smoothed": round(t_fair, 2)}

        # frames: the ring's are radial (fixed); a free helix's are rotation-minimising (no spin about T)
        T, N, B = rmf_frames(ring)
        assert np.all(np.sum(N * radial, 1) > 0.9995) and np.allclose(np.sum(N * T, 1), 0, atol=1e-9)
        th = np.linspace(0, 4 * np.pi, 1200)
        helix = Path(np.stack([50 * np.cos(th), 50 * np.sin(th), 100 * th / (2 * np.pi)], 1))
        T, N, B = rmf_frames(helix)
        spin = np.abs(np.sum((N[1:] - N[:-1]) * B[:-1], 1)).max()
        ds = float(np.linalg.norm(helix.co[1] - helix.co[0]))
        torsion = (100 / (2 * np.pi)) / (50 ** 2 + (100 / (2 * np.pi)) ** 2)
        assert spin < 0.02 * torsion * ds, (spin, torsion * ds)  # Frenet frames would spin by torsion x ds
        assert np.allclose(np.linalg.norm(N, axis=1), 1) and np.allclose(np.sum(T * B, 1), 0, atol=1e-9)
        R["helix_spin_per_step"] = float(spin)

        # a closed strap 15 x 1.5 on the ring: volume, radii, manifold, seated (no penetration)
        st = strip(ring, 15.0, 1.5, 6, twist_deg=0.4, seed=2)
        v = st.verts
        rv = np.linalg.norm(v[:, :2], axis=1)
        want = 15.0 * 2 * np.pi * 51.75 * 1.5
        assert st.manifold() and abs(st.volume() / want - 1) < 0.01, (st.volume(), want)
        assert rv.min() > 50.9 and rv.max() < 52.6, (rv.min(), rv.max())
        pen = penetration(st, surf)
        assert pen["inside"] == 0, pen
        R["closed_strip"] = {"volume_ratio": round(st.volume() / want, 4), "faces": len(st.faces)}

        # a vertical strap: its width wraps around the cylinder, so the underside must conform across it
        line = surface_path(surf, [(52, 0, 40), (52, 0, 160)], standoff=0.5, step=1.0)
        flat = strip(line, 15.0, 1.5, 6, conform=False)
        hug = strip(line, 15.0, 1.5, 6)
        under = lambda sw: np.linalg.norm(sw.stations()["m"][:, :, :2], axis=2) - 0.75
        float_flat = float(under(flat).max() - 50.5)
        float_hug = float(np.abs(under(hug) - 50.5).max())
        assert float_flat > 0.4 and float_hug < 0.05, (float_flat, float_hug)
        v0 = hug.volume()
        fold_end(hug, 15.0)
        assert hug.manifold(), "the folded strap is not closed"
        extra = hug.volume() - v0
        r_u = (1.5 + 0.375) / 2
        want = 15.0 * 1.5 * (15.0 + np.pi * r_u)
        assert abs(extra / want - 1) < 0.12, (extra, want)
        top = np.linalg.norm(hug.verts[:, :2], axis=1).max()
        assert abs(top - (50.5 + 3.0 + 0.375)) < 0.1, top  # two layers and the gap over the fold
        fold_end(hug, 10.0, at="start")
        assert hug.manifold()
        R["fold"] = {"extra_volume_ratio": round(extra / want, 4), "float_flat_mm": round(float_flat, 3),
                     "float_conformed_mm": round(float_hug, 4)}

        # a tube along the helix: the volume of its 12-gon prism
        tb = tube(helix, 2.0, 12)
        want = 0.5 * 12 * math.sin(2 * np.pi / 12) * 4.0 * helix.length
        assert tb.manifold() and abs(tb.volume() / want - 1) < 0.01, (tb.volume(), want)
        R["tube_volume_ratio"] = round(tb.volume() / want, 4)

        # threading: a strap along a plane through a two-slot buckle: up through slot 1, over the bar,
        # down through slot 2 (the slots in the buckle's frame, the buckle turned 30° about Z)
        plane = _plane_object("SelftestSw.Plane")
        made.append(plane)
        a30 = math.radians(30)
        c30, s30 = math.cos(a30), math.sin(a30)
        flat_path = surface_path(plane, [(-60 * c30, -60 * s30, 0), (60 * c30, 60 * s30, 0)], standoff=0.3, step=1.0)
        Mb = np.eye(4)
        Mb[:3, :3] = [[c30, -s30, 0], [s30, c30, 0], [0, 0, 1]]
        Mb[:3, 3] = (0, 0, 0.0)
        k = 1 / math.sqrt(2)
        slots = [{"centre": (-4.5, 0, 4.0), "axis": (k, 0, k), "up": (-k, 0, k), "depth": 2.0},
                 {"centre": (4.5, 0, 4.0), "axis": (k, 0, -k), "up": (k, 0, k), "depth": 2.0}]
        tp = thread(flat_path, Mb, slots, lead=12.0)
        W = _slots_world(Mb, slots)
        T, N, B = rmf_frames(tp)
        for sl in W:
            i = int(np.argmin(np.linalg.norm(tp.co - sl["c"], axis=1)))
            assert np.linalg.norm(tp.co[i] - sl["c"]) < 0.6 and T[i] @ sl["a"] > 0.99 and N[i] @ sl["up"] > 0.99
        turn = tp.turning_deg()
        assert turn.max() < 20.0, turn.max()
        assert tp.co[:, 2].max() > 5.0, "the strap did not pass over the bar"
        tst = strip(tp, 15.0, 1.5, 6)
        roll = float(np.abs(roll_steps(tp)).max())
        assert tst.manifold() and roll < 2.0, roll
        R["thread"] = {"points": len(tp), "max_turn_deg": round(float(turn.max()), 2),
                       "top_mm": round(float(tp.co[:, 2].max()), 2), "max_roll_deg_per_step": round(roll, 3)}

        # an Empty as a slot, and the object round trip with its UV layer
        e = bpy.data.objects.new("SelftestSw.Slot", None)
        bpy.context.scene.collection.objects.link(e)
        made.append(e)
        from mathutils import Matrix
        e.matrix_world = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0.004), (0, 0, 0, 1)))  # Z->+X, Y->+Z
        e["depth_mm"] = 3.0
        straight = surface_path(plane, [(-50, 0, 0), (50, 0, 0)], standoff=0.3, step=1.0)
        tp2 = thread(straight, None, ["SelftestSw.Slot"])
        assert np.linalg.norm(tp2.co - (0, 0, 4.0), axis=1).min() < 0.6
        # a steep slot 6 mm up: a 4 mm lead would bend hard; min_radius lengthens it until the bend clears
        steep = [{"centre": (0.0, 0.0, 6.0), "axis": (0.34, 0.0, 0.94), "depth": 2.0}]
        short = thread(straight, None, steep, lead=4.0)
        long_ = thread(straight, None, steep, lead=4.0, min_radius=5.0)
        assert short.leads[0][1] < 5.0 and long_.leads[0][0] > 4.0 and long_.leads[0][1] >= 5.0, (short.leads,
                                                                                                    long_.leads)
        R["adaptive_lead"] = {"short": short.leads[0], "lengthened": long_.leads[0]}
        ob = tst.to_object("SelftestSw.Strap")
        made.append(ob)
        uv = ob.data.uv_layers.get("UV.Real")
        assert uv is not None and len(ob.data.polygons) == len(tst.faces)
        us = np.empty(len(uv.data) * 2)
        uv.data.foreach_get("uv", us)
        span = us[0::2].max() - us[0::2].min()
        assert abs(span - (tp.length + 1.5) * MM) < 0.01, (span, tp.length)
        R["uv_u_span_m"] = round(float(span), 4)
        return R
    finally:
        for o in made:
            data = o.data
            bpy.data.objects.remove(o)
            if data is not None and data.users == 0:
                bpy.data.meshes.remove(data)
