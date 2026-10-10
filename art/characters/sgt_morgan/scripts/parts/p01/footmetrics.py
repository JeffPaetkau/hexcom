"""Part 01's foot measurements (spec 01 §3.1, §3.3, §8.2) in frame F, on spec 18's primitives.

Frame F of a foot (spec 01, conventions): origin at the pternion projected onto the floor, +Z up, toes toward
-Y, +X lateral for the left foot; the right foot is the mirror (its F coordinates have x negated), so every
table of the spec, written for the left foot, reads the same for both. The heading is the line from the
pternion to the tip of the second toe in plan, the long axis an anthropometer follows.

Everything reads a measure.Mesh (an evaluated read with polygons and the original-index map), so the same
code measures the depsgraph's mesh and a mesh predicted by the linear target model (with_positions()): the
S1 target fit (fit_targets.py) and the part's measure() use one definition of every number. Lengths are
mm; widths are calliper readings perpendicular to the long axis; girths are tape (convex-hull) readings,
the ANSUR convention.
"""
import copy
import math

import numpy as np

from lib import measure

MM = 1000.0
SIDES = {"L": 1.0, "R": -1.0}
TOES = (1, 2, 3, 4, 5)


# --------------------------------------------------------------------------- reads and index sets

def read(ob):
    """One evaluated read of the body with what every measurement here needs."""
    return measure.evaluate(ob, ("tris", "polys", "orig"))


def with_positions(m, co_mm):
    """A copy of read m whose vertices are co_mm, the object's own vertices in world mm (n_orig, 3): how a
    prediction of the linear target model is measured without the depsgraph."""
    out = copy.copy(m)
    co = np.asarray(co_mm, float) / MM
    out.co = co if m.orig is None else co[m.orig]
    out._full = None
    return out


def toe_bones(k, side):
    """The deform groups of toe k, proximal first (the hallux has two phalanges)."""
    return [f"toe{k}-{j}.{side}" for j in ((1, 2) if k == 1 else (1, 2, 3))]


class Index:
    """Vertex index sets of the evaluated read (its own order): each foot's region and each toe, from the
    rig's deform groups, and the toenails. Built once per body topology."""

    def __init__(self, ob, m):
        self.name, self.n = ob.name, len(m.co)
        orig = m.orig

        def ev(w):
            return w if orig is None else w[orig]

        co = m.co * MM
        self.region, self.toe, self.toe_distal, self.nail = {}, {}, {}, {}
        nails = ev(measure.group_weights(ob, "toenails")) > 0.5
        for side, s in SIDES.items():
            self.region[side] = np.nonzero((s * co[:, 0] > 40.0) & (co[:, 2] < 300.0))[0]
            names = [n for k in TOES for n in toe_bones(k, side)]
            W = np.stack([ev(measure.group_weights(ob, n)) for n in names], axis=1)
            top = np.argmax(W, axis=1)
            strong = W[np.arange(len(W)), top] > 0.5
            col = 0
            self.toe[side], self.toe_distal[side], self.nail[side] = {}, {}, {}
            for k in TOES:
                cols = list(range(col, col + len(toe_bones(k, side))))
                col += len(cols)
                mine = strong & np.isin(top, cols)
                self.toe[side][k] = np.nonzero(mine)[0]
                self.toe_distal[side][k] = np.nonzero(strong & (top == cols[-1]))[0]
                self.nail[side][k] = np.nonzero(mine & nails)[0]


_INDEX = {}


def index(ob, m):
    key = (ob.name, len(m.co), m.n_orig)
    if key not in _INDEX:
        _INDEX[key] = Index(ob, m)
    return _INDEX[key]


# --------------------------------------------------------------------------- frame F

class Frame:
    """World mm <-> frame F mm for one foot."""

    def __init__(self, origin, heading, side):
        self.side, self.s = side, SIDES[side]
        h = np.array([heading[0], heading[1], 0.0])
        h /= np.linalg.norm(h)
        self.ey = -h                                   # F's +Y points back, toward the heel
        self.ex = np.array([self.ey[1], -self.ey[0], 0.0])  # ey x z: lateral for the left foot
        self.o = np.array([origin[0], origin[1], 0.0])

    def to_f(self, p):
        d = np.asarray(p, float) - self.o
        return np.stack([self.s * (d @ self.ex), d @ self.ey, d[..., 2]], axis=-1)

    def to_w(self, q):
        q = np.asarray(q, float)
        return self.o + (self.s * q[..., 0:1]) * self.ex + q[..., 1:2] * self.ey + q[..., 2:3] * np.array([0, 0, 1.0])

    def vec_to_w(self, v):
        v = np.asarray(v, float)
        return (self.s * v[..., 0:1]) * self.ex + v[..., 1:2] * self.ey + v[..., 2:3] * np.array([0, 0, 1.0])

    def vec_to_f(self, v):
        v = np.asarray(v, float)
        return np.stack([self.s * (v @ self.ex), v @ self.ey, v[..., 2]], axis=-1)

    def heading_deg(self):
        """The toes' direction in plan, degrees from -Y toward +X (world)."""
        return math.degrees(math.atan2(-self.ey[0], self.ey[1]))

    def matrix(self):
        """4 x 4 world matrix (metres) of frame F as an Empty carries it: a rotation about Z, no mirror (the
        presets mirror the right side's coordinates themselves)."""
        M = np.eye(4)
        M[:3, 0], M[:3, 1], M[:3, 2] = self.ex, self.ey, (0, 0, 1)
        M[:3, 3] = self.o / MM
        return M


def frame(m, ix, side):
    """Frame F from the mesh: the pternion (the most posterior point of the heel below z 60) and the line
    to the tip of the second toe; returned with the foot length (pternion to the most anterior point)."""
    co = m.co * MM
    R = ix.region[side]
    low = R[co[R, 2] < 60.0]
    pt = co[low[np.argmax(co[low, 1])]]
    t2 = ix.toe_distal[side][2]
    tip2 = co[t2[np.argmin(co[t2, 1])]]
    f = Frame(pt, tip2 - pt, side)
    q = f.to_f(co[low])
    f = Frame(f.to_w(np.array([0.0, q[:, 1].max(), 0.0])), tip2 - pt, side)  # the pternion in F, exactly
    return f


# --------------------------------------------------------------------------- sections

def _section_points(m, plane):
    recs = measure.section(m, plane)
    return np.vstack([r["points"] for r in recs]) if recs else np.zeros((0, 3))


def _box(q, x=(-90.0, 90.0), y=(-330.0, 70.0), z=(-5.0, 400.0)):
    return q[(q[:, 0] > x[0]) & (q[:, 0] < x[1]) & (q[:, 1] > y[0]) & (q[:, 1] < y[1]) & (q[:, 2] > z[0])
             & (q[:, 2] < z[1])]


def horizontal(m, f, height, **box):
    """Frame-F points of the horizontal section at a height (mm), this foot's only."""
    return _box(f.to_f(_section_points(m, float(height))), **box)


def vertical(m, f, y_f, **box):
    """Frame-F points of the section across the foot at y_F (a plane perpendicular to the long axis)."""
    p = f.to_w(np.array([0.0, y_f, 0.0]))
    return _box(f.to_f(_section_points(m, {"point": p, "normal": f.ey})), **box)


def sagittal(m, f, x_f=0.0, **box):
    p = f.to_w(np.array([x_f, 0.0, 0.0]))
    return _box(f.to_f(_section_points(m, {"point": p, "normal": f.ex})), **box)


def _extent(q, band, axis=0):
    """(min, max, point at min, point at max) along an axis of the points inside a y_F band."""
    q = q[(q[:, 1] >= band[0]) & (q[:, 1] <= band[1])]
    if not len(q):
        return None
    i, j = np.argmin(q[:, axis]), np.argmax(q[:, axis])
    return q[i, axis], q[j, axis], q[i], q[j]


def breadth(m, f, band, zs):
    """Calliper breadth across the foot inside a y_F band, the extremes taken over the heights zs:
    (breadth, medial point, lateral point) in F."""
    lo, hi = None, None
    for z in zs:
        e = _extent(horizontal(m, f, z), band)
        if e is None:
            continue
        if lo is None or e[0] < lo[0]:
            lo = (e[0], e[2])
        if hi is None or e[1] > hi[0]:
            hi = (e[1], e[3])
    if lo is None or hi is None:
        return None, None, None
    return hi[0] - lo[0], lo[1], hi[1]


def loops(m, f, plane, keep=0.5, **box):
    """This foot's section loops in frame F: [(points (n, 3), closed)], a loop kept when most of it lies in
    the box (the other foot and leg are 400 mm away, so a box separates them)."""
    out = []
    for r in measure.section(m, plane):
        p = f.to_f(r["points"])
        if len(_box(p, **box)) > keep * len(p):
            out.append((p, r["closed"]))
    return out


def width_at(m, f, y_f, z):
    """Width of the foot along the line y = y_F at height z: where the horizontal section's loops cross the
    line, outermost crossings (the heel widths of spec 01 §4.2 step 3)."""
    xs = []
    for p, closed in loops(m, f, float(z)):
        P = np.vstack([p, p[:1]]) if closed else p
        a, b = P[:-1], P[1:]
        da, db = a[:, 1] - y_f, b[:, 1] - y_f
        hit = (da * db <= 0.0) & (da != db)
        t = da[hit] / (da[hit] - db[hit])
        xs += (a[hit, 0] + t * (b[hit, 0] - a[hit, 0])).tolist()
    return max(xs) - min(xs) if len(xs) >= 2 else None


def tape(m, f, plane_point_f, normal_w):
    """Tape girth (mm) of the loop of this foot in the plane through a frame-F point with a world normal."""
    p = f.to_w(np.asarray(plane_point_f, float))
    return measure.girth(m, {"point": p, "normal": normal_w}, around=p, kind="tape")


# --------------------------------------------------------------------------- the measurements

def ankle(m, f, band=(-90.0, -40.0)):
    """The malleoli (spec 01 §3.1, §8.2): each side's profile across the ankle (the extreme x of the sections at
    z 56-112, within a y_F band around the bones at -60 and -73) and its apex, the profile's most prominent
    local peak refined by a parabola (ANSUR's apex: the bone's most protruding point, not the widest the foot
    gets lower down); bimalleolar is the breadth between the two apexes. A side with no peak reports its widest
    point between z 68 and 100, flagged unresolved."""
    zs = np.arange(56.0, 114.0, 2.0)
    prof = {"lat": [], "med": []}
    for z in zs:
        e = _extent(horizontal(m, f, z), band)
        prof["lat"].append(e[1] if e else np.nan)
        prof["med"].append(-e[0] if e else np.nan)
    out = {}
    for side in ("lat", "med"):
        p = np.array(prof[side])
        best, resolved = None, False
        for i in range(1, len(p) - 1):
            if np.isfinite(p[i - 1:i + 2]).all() and p[i] >= p[i - 1] and p[i] > p[i + 1]:
                left, right = np.nanmin(p[:i + 1]), np.nanmin(p[i:])
                prom = p[i] - max(left, right)
                if best is None or prom > best[0]:
                    best = (prom, i)
        if best is not None and best[0] > 0.2:
            i = best[1]
            a, b, c = p[i - 1], p[i], p[i + 1]
            den = a - 2.0 * b + c
            t = 0.5 * (a - c) / den if den else 0.0
            z, x, resolved = zs[i] + 2.0 * t, b - 0.25 * (a - c) * t, True
        else:
            sel = (zs >= 68.0) & (zs <= 100.0) & np.isfinite(p)
            i = int(np.nanargmax(np.where(sel, p, -np.inf)))
            z, x = zs[i], p[i]
        out[side] = (float(x), float(z), resolved)
    def at(side, z):
        return float(np.interp(z, zs, np.nan_to_num(np.array(prof[side]), nan=-1e3)))

    # how far each bone stands out from the ankle just below it (a smooth reading for the fit, which gets
    # no gradient from an apex that does not exist yet): lateral 76 against 62, medial 89 against 72
    return {"bimalleolar": out["lat"][0] + out["med"][0],
            "malleolus_lateral_z": out["lat"][1], "malleolus_medial_z": out["med"][1],
            "malleolus_lateral_x": out["lat"][0], "malleolus_medial_x": -out["med"][0],
            "malleoli_resolved": int(out["lat"][2]) + int(out["med"][2]),
            "malleolus_lateral_prom": at("lat", 76.0) - at("lat", 62.0),
            "malleolus_medial_prom": at("med", 89.0) - at("med", 72.0)}


def heel_back(m, f, sq=None):
    """The heel's back in the sagittal plane: the pternion's height (where the profile reaches furthest back,
    refined by a parabola) and how far the calcaneus stands out behind the Achilles insertion 22 mm above it
    and the heel's lower curve 18 mm below (§3.1: pternion 30, insertion 52)."""
    sq = sagittal(m, f, 0.0, z=(-5.0, 80.0)) if sq is None else sq
    sq = sq[sq[:, 1] > -60.0]
    if not len(sq):
        return {}
    zs = np.arange(4.0, 78.0, 2.0)
    prof = []
    for z in zs:
        sel = np.abs(sq[:, 2] - z) < 1.6
        prof.append(sq[sel, 1].max() if sel.any() else np.nan)
    p = np.array(prof)
    ok = np.isfinite(p)
    p = np.interp(zs, zs[ok], p[ok])
    i = int(np.argmax(p))
    z_apex, y_apex = zs[i], p[i]
    if 0 < i < len(p) - 1:
        a, b, c = p[i - 1], p[i], p[i + 1]
        den = a - 2.0 * b + c
        t = 0.5 * (a - c) / den if den else 0.0
        z_apex, y_apex = zs[i] + 2.0 * t, b - 0.25 * (a - c) * t
    return {"pternion_z": float(z_apex),
            "heel_prom": float(y_apex - max(np.interp(z_apex + 22.0, zs, p), np.interp(z_apex - 18.0, zs, p)))}


def subdivided(ob, levels=2):
    """A read of the body's subdivided surface, the one the closeups render (a Subdivision modifier added for
    the read and removed after): MakeHuman's ankle quads are 13 mm, so on the cage a malleolus's apex can only
    be found at a vertex row."""
    mod = ob.modifiers.new("Foot.Measure.Subdivision", "SUBSURF")
    mod.levels = mod.render_levels = levels
    try:
        return measure.evaluate(ob, ("polys",))
    finally:
        ob.modifiers.remove(mod)


def foot(m, ix, side, toes=True):
    """Every §3.1 dimension of one foot, and with toes the §3.3 toe tips, widths and heights: {name: value}."""
    f = frame(m, ix, side)
    co = m.co * MM
    R = ix.region[side]
    q = f.to_f(co[R])
    foot_q = q[q[:, 2] < 60.0]
    L = float(foot_q[:, 1].max() - foot_q[:, 1].min())
    out = {"foot_length": L, "heading_deg": f.heading_deg()}

    # the ball: the medial bulge of the 1st MT head and the lateral bulge of the 5th, over the heights
    # where the heads are (spec 01 §3.2: 22 and 18 mm), and the calliper breadth between them
    fore = (-0.86 * L, -0.55 * L)
    bb, med, _ = breadth(m, f, fore, np.arange(6.0, 41.0, 3.0))
    out["ball_breadth"] = bb
    out["ball_length"] = -float(med[1]) if med is not None else None
    # the 5th head's lateral bulge, looked for where the heads are (60-78 % L), not in the midfoot
    _, _, lat = breadth(m, f, (-0.78 * L, -0.60 * L), np.arange(6.0, 31.0, 3.0))
    out["ball_length_lateral"] = -float(lat[1]) if lat is not None else None

    # the heel: the widest point within 60 mm of the pternion below z 45, and the widths at 15 % L
    hb, _, _ = breadth(m, f, (-60.0, 5.0), np.arange(4.0, 45.0, 4.0))
    out["heel_breadth"] = hb
    for z in (10, 20, 30):
        out[f"heel_width_z{z}"] = width_at(m, f, -0.15 * L, z)

    out.update(ankle(m, f))

    # the minimum ankle circumference above the malleoli
    girths = []
    for z in np.arange(100.0, 224.0, 4.0):
        g = _leg_girth(m, f, z)
        if g is not None:
            girths.append((g, z))
    if girths:
        g0, z0 = min(girths)
        for z in np.arange(z0 - 3.0, z0 + 3.5, 1.0):
            g = _leg_girth(m, f, z)
            if g is not None and g < g0:
                g0, z0 = g, z
        out["ankle_circ_min"], out["ankle_circ_min_z"] = g0, z0

    sq = sagittal(m, f, 0.0, z=(-5.0, 80.0))
    out.update(heel_back(m, f, sq))

    # heel-ankle girth (ANSUR II): the tape over the front of the ankle at the crease height, z 85 (spec 01
    # §3.1's B column), and around the bottom of the heel at its posterior-inferior point, the heel
    # profile's extreme toward back-and-down (a plane through the pternion itself reads 40 mm short)
    front = ankle_front(m, f, 85.0)
    back = sq[sq[:, 1] > -60.0] if len(sq) else sq
    if front is not None and len(back):
        a = back[np.argmax(back[:, 1] - back[:, 2])]
        d = f.vec_to_w(front - a)
        n = np.cross(f.vec_to_w(np.array([1.0, 0.0, 0.0])), d)
        out["crease_z"] = float(front[2])
        try:
            out["heel_ankle_circ"] = tape(m, f, (a + front) / 2.0, n / np.linalg.norm(n))
        except LookupError:
            out["heel_ankle_circ"] = None

    # the ball girth: through the two bulges, vertical
    if med is not None and lat is not None:
        d = f.vec_to_w(lat - med)
        n = np.cross(d, (0.0, 0.0, 1.0))
        mid = (med + lat) / 2.0
        mid[2] = 20.0
        try:
            out["ball_circ"] = tape(m, f, mid, n / np.linalg.norm(n))
        except LookupError:
            out["ball_circ"] = None

    # instep girth and dorsum heights across the foot; the arch clearances
    try:
        out["instep_circ"] = tape(m, f, (0.0, -0.5 * L, 30.0), f.ey)
    except LookupError:
        out["instep_circ"] = None
    for p in (50, 60, 70):
        v = vertical(m, f, -p / 100.0 * L, z=(-5.0, 150.0))
        out[f"dorsum_h{p}"] = float(v[:, 2].max()) if len(v) else None
    out["arch_medial_45"] = _border_clearance(vertical(m, f, -0.45 * L, z=(-5.0, 150.0)), medial=True)
    out["lateral_clear_50"] = _border_clearance(vertical(m, f, -0.50 * L, z=(-5.0, 150.0)), medial=False)

    if toes:
        out.update(toe_dims(m, ix, f, side))
    out["_frame"] = f
    return out


def ankle_front(m, f, z):
    """The front of the ankle at height z: the most anterior point of the section near x_F 0, in F."""
    q = horizontal(m, f, z, x=(-15.0, 15.0), y=(-200.0, -20.0))
    if not len(q):
        return None
    return q[np.argmin(q[:, 1])]


def _leg_girth(m, f, z):
    q = horizontal(m, f, z, y=(-200.0, 120.0))
    if len(q) < 3:
        return None
    c = q.mean(axis=0)
    try:
        return measure.girth(m, float(z), around=f.to_w(np.array([c[0], c[1], z])), kind="tape")
    except LookupError:
        return None


def _border_clearance(v, medial):
    """Height of the plantar surface under one border: the lowest point of the outer fifth of a cross-section."""
    if not len(v):
        return None
    x0, x1 = v[:, 0].min(), v[:, 0].max()
    w = x1 - x0
    sel = v[v[:, 0] < x0 + 0.2 * w] if medial else v[v[:, 0] > x1 - 0.2 * w]
    return float(sel[:, 2].min())


def toe_axis(q_toe):
    """A toe's axis in plan (unit F vector toward the tip) from the principal direction of its vertices."""
    c = q_toe[:, :2] - q_toe[:, :2].mean(axis=0)
    _, _, vt = np.linalg.svd(c, full_matrices=False)
    a = vt[0]
    return a if a[1] < 0 else -a


def toe_dims(m, ix, f, side):
    """Per toe (spec 01 §3.3): the tip's y_F, the toe's greatest width across its axis beyond the web, and its
    thickness (dorsal-plantar extent) at the IP / PIP joint, taken at the joint's share of the toe."""
    co = m.co * MM
    out = {}
    share = {1: 0.55, 2: 0.56, 3: 0.56, 4: 0.55, 5: 0.46}  # §3.3: MTP->IP over MTP->tip
    for k in TOES:
        T = ix.toe[side][k]
        if not len(T):
            continue
        q = f.to_f(co[T])
        a = toe_axis(q)
        n = np.array([-a[1], a[0]])
        t = q[:, :2] @ a
        out[f"toe{k}_tip_y"] = float(q[:, 1].min())  # the tip's reach along the foot (the §3.3 cascade)
        base, end = t.min(), t.max()
        dist = q[t > base + 0.35 * (end - base)]
        if len(dist):
            s = dist[:, :2] @ n
            out[f"toe{k}_width"] = float(s.max() - s.min())
        # thickness across the toe's own sloping axis at the joint: the section of the body by the plane through
        # the toe's centre there, perpendicular to the line through its centres 5 mm either side, read along the
        # plane's upward direction (a section is continuous in the vertices; a slab of vertices is not)
        jt = base + share[k] * (end - base)

        def centre(tt):
            sl = q[np.abs(t - tt) < 3.5]
            return sl.mean(axis=0) if len(sl) > 1 else None

        c0, cj, c1 = centre(jt - 5.0), centre(jt), centre(jt + 5.0)
        if cj is None:
            continue
        ax = np.array([a[0], a[1], 0.0]) if c0 is None or c1 is None else (c1 - c0) / np.linalg.norm(c1 - c0)
        up = np.array([0.0, 0.0, 1.0]) - ax[2] * ax
        up /= np.linalg.norm(up)
        ring = []
        for r in measure.section(m, {"point": f.to_w(cj), "normal": f.vec_to_w(ax)}):
            pr = f.to_f(r["points"])
            near = pr[np.linalg.norm(pr - cj, axis=1) < 14.0]
            if len(near) > len(ring):
                ring = near
        if len(ring) > 3:
            side_n = np.cross(up, ax)
            ring = ring[np.abs((ring - cj) @ side_n) < 0.5 * out.get(f"toe{k}_width", 16.0) + 1.0]
            out[f"toe{k}_height"] = float((ring @ up).max() - (ring @ up).min())
    return out


def toe_gaps(m, ix, side, beyond=0.4):
    """The smallest distance (mm) between neighbouring toes, toe k's distal vertices against toe k+1's
    surface, beyond the web (the outer `beyond` share of each toe): {"1-2": gap, ...}."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    co = m.co * MM
    f = frame(m, ix, side)
    tris = m.tris
    out = {}
    for k in (1, 2, 3, 4):
        A, B = ix.toe[side][k], ix.toe[side][k + 1]
        if not len(A) or not len(B):
            continue
        qa = f.to_f(co[A])
        ta = qa[:, :2] @ toe_axis(qa)
        A = A[ta > ta.min() + beyond * (ta.max() - ta.min())]
        inB = np.zeros(len(co), bool)
        inB[B] = True
        tb = tris[inB[tris].all(axis=1)]
        if not len(tb) or not len(A):
            continue
        tree = BVHTree.FromPolygons(co.tolist(), tb.tolist(), all_triangles=True)
        best = None
        for i in A.tolist():
            hit = tree.find_nearest(Vector(co[i]))
            if hit[0] is not None and (best is None or hit[3] < best):
                best = hit[3]
        out[f"{k}-{k + 1}"] = best
    return out
