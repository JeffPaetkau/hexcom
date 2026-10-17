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
INSIDE_MM = 3.0  # a vertex this near another toe's surface, behind its face (not beside an edge), is inside
                 # it (a toe's faces are an open patch: further off, the nearest point can be on its rim,
                 # where a side means nothing)


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
    # the stations along the foot (15 % L, 45-70 % L, the plan's) are shares of the length the skeleton gives, the
    # ball length over spec 01 §3.1's 74.5 %: Jeff's shorter hallux (2026-10-15) shortened the foot to its longest
    # toe by 7 mm and must not move the midfoot's stations with it (spec 01 §3.1 note)
    L = station_length(out["ball_length"], L)
    out["station_length"] = L
    # the 5th head's lateral bulge, looked for where the heads are (60-78 % L), not in the midfoot. (The shape
    # pass, 2026-10-14: with the lateral border now straight from the heel to the head, the extreme falls on its
    # last centimetre, 13-16 mm behind the head itself, and the ball's tape with it: 258 there, 246-248 over the
    # head, against ANSUR's 259; spec 01 §3.1 note)
    _, _, lat = breadth(m, f, (-0.78 * L, -0.60 * L), np.arange(6.0, 31.0, 3.0))
    out["ball_length_lateral"] = -float(lat[1]) if lat is not None else None

    # the heel: the widest point within 60 mm of the pternion below z 45, and the widths at 15 % L
    hb, _, _ = breadth(m, f, (-60.0, 5.0), np.arange(4.0, 45.0, 4.0))
    out["heel_breadth"] = hb
    for z in (10, 20, 30):
        out[f"heel_width_z{z}"] = width_at(m, f, -0.15 * L, z)

    out.update(ankle(m, f))
    _, widest = heel_outline(m, f, ys=(), zs=())
    out["heel_widest_y"], out["heel_widest"] = widest

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


BALL_SHARE = 210.0 / 282.0   # spec 01 §3.1: the ball length 74.5 % of the foot's length (ANSUR)


def station_length(ball_length, foot_length):
    """The length the foot's stations are shares of: the ball length over BALL_SHARE (the skeleton's foot, whatever
    the toes do), or the foot's own length when the ball is not found."""
    return float(ball_length) / BALL_SHARE if ball_length else float(foot_length)


PLAN_Z_CUT = 125.0   # the plan outline is the foot's below this height (the leg above the malleoli left out)
HEAD5_PCT = 100.0 * 185.0 / 282.0   # spec 01 §3.1: the 5th metatarsal head 185 mm from the pternion


def _peak(pcts, vals, lo, hi, sign=1.0):
    """The extreme (max of sign * vals) within pcts [lo, hi], refined by a parabola: (pct, value)."""
    sel = np.nonzero((pcts >= lo) & (pcts <= hi) & np.isfinite(vals))[0]
    i = sel[np.argmax(sign * vals[sel])]
    if 0 < i < len(vals) - 1 and np.isfinite(vals[i - 1:i + 2]).all():
        a, b, c = sign * vals[i - 1], sign * vals[i], sign * vals[i + 1]
        den = a - 2.0 * b + c
        t = float(np.clip(0.5 * (a - c) / den, -0.5, 0.5)) if den else 0.0
        return float(pcts[i] + t * (pcts[1] - pcts[0])), float(sign * (b - 0.25 * (a - c) * t))
    return float(pcts[i]), float(vals[i])


def plan(m, f, L, z_cut=PLAN_Z_CUT, step=2.5):
    """The foot's outline seen from above (the shape pass, 2026-10-14, spec 01 §3.1 note): the medial and lateral
    extremes of the sections across the foot every `step` % of the length, below z_cut. Returns the breadth at 40,
    50 and 60 % L; the 5th metatarsal head's corner (the lateral extreme at 58-75 % L) and the 1st head's (the
    medial extreme at 66-82 % L) and the breadth between them; `plan_lat_bulge`, how far the lateral border stands
    outside the straight chord from the heel (its lateral extreme below z 45 at 15 % L) to the 5th head's corner,
    between 30 % L and the corner (a real lateral border runs straight there, the styloid a small bump on it);
    `plan_med_dip`, how far the medial border lies inside the chord from the heel to the 1st head's corner, between
    40 % L and the corner (seen from above it dips along the first metatarsal); and the widest station."""
    pcts = np.arange(10.0, 87.5 + 1e-6, step)
    med, lat = np.full(len(pcts), np.nan), np.full(len(pcts), np.nan)
    for i, p in enumerate(pcts):
        v = vertical(m, f, -p / 100.0 * L, z=(-5.0, z_cut))
        if len(v):
            med[i], lat[i] = v[:, 0].min(), v[:, 0].max()
    heel = vertical(m, f, -0.15 * L, z=(-5.0, 45.0))
    out = {}
    br = lat - med
    for p in (40, 50, 60):
        out[f"plan_b{p}"] = float(np.interp(p, pcts, br))
    p5, x5 = _peak(pcts, lat, 58.0, 75.0, 1.0)
    p1, x1 = _peak(pcts, med, 66.0, 82.0, -1.0)
    out.update(plan_head5_pct=p5, plan_head5_x=x5, plan_head1_pct=p1, plan_head1_x=x1, plan_ball=x5 - x1)
    if len(heel):
        h_lat, h_med = float(heel[:, 0].max()), float(heel[:, 0].min())
        # the lateral chord ends at the 5th head where spec 01 has it (185 mm, 65.6 % L), so a border widest
        # before the head counts as a bulge, whatever its own extreme
        ph = HEAD5_PCT
        xh = float(np.interp(ph, pcts, lat))
        span = (pcts >= 30.0) & (pcts <= ph - 2.0)
        chord = h_lat + (pcts - 15.0) * (xh - h_lat) / (ph - 15.0)
        out["plan_lat_bulge"] = float(np.nanmax(np.where(span, lat - chord, np.nan)))
        span = (pcts >= 40.0) & (pcts <= p1 - 2.0)
        chord = h_med + (pcts - 15.0) * (x1 - h_med) / (p1 - 15.0)
        out["plan_med_dip"] = float(np.nanmax(np.where(span, med - chord, np.nan)))
    body = (pcts >= 30.0) & (pcts <= 85.0)
    out["plan_widest_pct"], out["plan_widest"] = _peak(pcts, np.where(body, br, np.nan), 30.0, 85.0, 1.0)
    out["plan_mid_ratio"] = out["plan_b50"] / out["plan_ball"]
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
    """A toe's axis in plan (unit F vector toward the tip) from the principal direction of its vertices; for a toe
    nearly as broad as it is long, whose principal direction is ill-defined (the scan transfer's hallux, 2026-10-17:
    35 mm across, its principal axis read 21 degrees off and its thickness 4 mm), the line from the centroid of its
    back 35 % to that of its front 15 % along the foot."""
    c = q_toe[:, :2] - q_toe[:, :2].mean(axis=0)
    _, sv, vt = np.linalg.svd(c, full_matrices=False)
    a = vt[0]
    if len(sv) > 1 and sv[0] < 1.6 * sv[1]:
        y = q_toe[:, 1]
        span = y.max() - y.min()
        d = q_toe[y < y.min() + 0.15 * span, :2].mean(axis=0) - q_toe[y > y.max() - 0.35 * span, :2].mean(axis=0)
        a = d / np.linalg.norm(d)
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
        # (the reach grows with a broad toe: the scan transfer's hallux, 35 mm across, keeps few points within 14)
        reach = max(14.0, 0.8 * out.get(f"toe{k}_width", 16.0))
        for r in measure.section(m, {"point": f.to_w(cj), "normal": f.vec_to_w(ax)}):
            pr = f.to_f(r["points"])
            near = pr[np.linalg.norm(pr - cj, axis=1) < reach]
            if len(near) > len(ring):
                ring = near
        if len(ring) > 3:
            side_n = np.cross(up, ax)
            ring = ring[np.abs((ring - cj) @ side_n) < 0.5 * out.get(f"toe{k}_width", 16.0) + 1.0]
            out[f"toe{k}_height"] = float((ring @ up).max() - (ring @ up).min())
    return out


def _segments_distance(A, B):
    """The least distance between two closed polylines (n, 2), vertex to segment both ways."""
    def one(P, Q):
        Q1 = np.roll(Q, -1, axis=0)
        d = Q1 - Q
        L2 = np.maximum((d * d).sum(axis=1), 1e-12)
        t = np.clip(((P[:, None, :] - Q[None]) * d[None]).sum(axis=2) / L2[None], 0.0, 1.0)
        return float(np.linalg.norm(P[:, None, :] - (Q[None] + t[..., None] * d[None]), axis=2).min())
    return min(one(A, B), one(B, A))


def _pair_at(m, f, Q, k, y):
    """At the section across the foot at y_F: (joined, gap) of toes k and k+1, or None where either toe has no
    skin near y. Joined: one section loop holds both toes' centres; else the gap between their two loops."""
    na, nb = Q[k][np.abs(Q[k][:, 1] - y) < 3.0], Q[k + 1][np.abs(Q[k + 1][:, 1] - y) < 3.0]
    if len(na) < 3 or len(nb) < 3:
        return None
    lp = [p[:, [0, 2]] for p, closed in loops(m, f, {"point": f.to_w(np.array([0.0, y, 0.0])), "normal": f.ey},
                                                keep=0.5, x=(-90.0, 100.0), z=(-5.0, 80.0)) if closed]
    ca, cb = na[:, [0, 2]].mean(axis=0), nb[:, [0, 2]].mean(axis=0)
    la = [i for i, p in enumerate(lp) if measure._inside(ca, p)]
    lb = [i for i, p in enumerate(lp) if measure._inside(cb, p)]
    if not la or not lb:
        return None
    if set(la) & set(lb):
        return True, 0.0
    return False, _segments_distance(lp[la[0]], lp[lb[0]])


def webs(m, ix, side, f=None, step=0.5, open_mm=0.5):
    """Where neighbouring toes part (spec 01 §3.2's toe webs, y_F mm), scanning sections across the foot from
    behind the shorter toe's base forward: `saddle_y`, the commissure (the first section in which the toes
    are two loops), and `open_y`, where the cleft between them is first open by open_mm (toes that touch in
    front of their commissure, as real toes do, are not yet apart). With each toe's tip y and its visible
    length from its web(s) to its tip in plan."""
    co = m.co * MM
    f = f or frame(m, ix, side)
    Q = {k: f.to_f(co[ix.toe[side][k]]) for k in TOES}
    tips = {k: float(Q[k][:, 1].min()) for k in TOES}
    out = {"tips": tips}
    run = 3  # a state counts once it holds for three sections (1.5 mm): one odd section is a cage artefact
    for k in (1, 2, 3, 4):
        start = min(Q[k][:, 1].max(), Q[k + 1][:, 1].max()) - 1.0
        end = max(tips[k], tips[k + 1]) + 1.0
        ys, states = [], []
        for y in np.arange(start, end, -step):
            st = _pair_at(m, f, Q, k, float(y))
            if st is not None:
                ys.append(float(y))
                states.append(st)
        saddle = opened = None
        for i in range(len(states) - run + 1):
            win = states[i:i + run]
            if saddle is None and not any(j for j, _ in win):
                saddle = ys[i]
            if opened is None and all(not j and g >= open_mm for j, g in win):
                opened = ys[i]
                break
        out[f"{k}-{k + 1}"] = {"saddle_y": saddle, "open_y": opened}
    vis = {}
    for k in TOES:
        ws = [out[p]["open_y"] for p in (f"{k - 1}-{k}", f"{k}-{k + 1}") if p in out and out[p]["open_y"] is not None]
        if ws:
            vis[k] = float(np.mean(ws) - tips[k])
    out["visible"] = vis
    return out


def heel_outline(m, f, ys=(-6.0, -10.0, -14.0, -20.0, -28.0, -35.0, -42.0, -50.0, -56.0, -62.0, -70.0),
                 zs=(10.0, 20.0, 30.0)):
    """The heel's plan: its width across the foot at stations y_F and heights z ({(y, z): mm}), and where it is
    widest at z 20-30 between y_F -6 and -75 (the y and the width)."""
    out = {(y, z): width_at(m, f, y, z) for y in ys for z in zs}
    best = (None, None)
    for y in np.arange(-6.0, -76.0, -2.0):
        w = [width_at(m, f, float(y), z) for z in (20.0, 25.0, 30.0)]
        w = max(x for x in w if x is not None) if any(x is not None for x in w) else None
        if w is not None and (best[1] is None or w > best[1]):
            best = (float(y), w)
    return out, best


def toe_gaps(m, ix, side, beyond=0.4):
    """The smallest distance (mm) between neighbouring toes, each toe's distal vertices against the other's
    surface, beyond the web (the outer `beyond` share of each toe): {"1-2": gap, ...}; negative where a
    vertex lies inside the neighbour (curled toes whose knuckles cross)."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    co = m.co * MM
    f = frame(m, ix, side)
    splits = _quad_splits(m)
    out = {}
    for k in (1, 2, 3, 4):
        best = None
        for me, other in ((k, k + 1), (k + 1, k)):
            A, B = ix.toe[side][me], ix.toe[side][other]
            if not len(A) or not len(B):
                continue
            qa = f.to_f(co[A])
            ta = qa[:, :2] @ toe_axis(qa)
            A = A[ta > ta.min() + beyond * (ta.max() - ta.min())]
            inB = np.zeros(len(co), bool)
            inB[B] = True
            trees = []
            for tris in splits:
                tb = tris[inB[tris].all(axis=1)]
                if len(tb):
                    trees.append(BVHTree.FromPolygons(co.tolist(), tb.tolist(), all_triangles=True))
            if not trees or not len(A):
                continue
            for i in A.tolist():
                # a warped quad's two triangulations differ by a few tenths, and which one Blender's evaluated mesh
                # holds is not the same in every session (the scan transfer's pressed toes, 2026-10-17: 2-3 read
                # -0.36 in the build and +0.21 reloaded): each vertex reads the more generous of the two
                ds = []
                for tree in trees:
                    hit = tree.find_nearest(Vector(co[i]))
                    if hit[0] is None:
                        continue
                    inside = hit[3] < INSIDE_MM and (Vector(co[i]) - hit[0]).dot(hit[1]) < -0.5 * hit[3]
                    ds.append(-hit[3] if inside else hit[3])
                if not ds:
                    continue
                d = max(ds)
                if best is None or d < best:
                    best = d
        out[f"{k}-{k + 1}"] = best
    return out


def _quad_splits(m):
    """The read's polygons triangulated both ways (a quad by either diagonal; others as fans), world winding: two
    (T, 3) arrays of vertex indices into m.co."""
    ls, lt, lv = m.loop_start, m.loop_total, m.loop_vert
    quad = lt == 4
    s = ls[quad]
    a = np.concatenate([np.stack([lv[s], lv[s + 1], lv[s + 2]], 1), np.stack([lv[s], lv[s + 2], lv[s + 3]], 1)])
    b = np.concatenate([np.stack([lv[s + 1], lv[s + 2], lv[s + 3]], 1), np.stack([lv[s + 1], lv[s + 3], lv[s]], 1)])
    rest = []
    for k in range(1, int(lt.max()) - 1):
        ok = (lt > k + 1) & ~quad
        if ok.any():
            rest.append(np.stack([lv[ls[ok]], lv[ls[ok] + k], lv[ls[ok] + k + 1]], 1))
    extra = np.concatenate(rest) if rest else np.zeros((0, 3), np.int64)
    return np.concatenate([a, extra]), np.concatenate([b, extra])


def hallux_gap(m, ix, side, f=None, distal=0.6):
    """The gap between the hallux and the second toe at the tips: the least signed distance from toe 2's
    distal 40 % to the hallux's surface (mm)."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    co = m.co * MM
    f = f or frame(m, ix, side)
    A = ix.toe[side][2]
    q = f.to_f(co[A])
    ta = q[:, :2] @ toe_axis(q)
    A = A[ta > ta.min() + distal * (ta.max() - ta.min())]
    inB = np.zeros(len(co), bool)
    inB[ix.toe[side][1]] = True
    tb = m.tris[inB[m.tris].all(axis=1)]
    if not len(A) or not len(tb):
        return None
    tree = BVHTree.FromPolygons(co.tolist(), tb.tolist(), all_triangles=True)
    best = None
    for i in A.tolist():
        hit = tree.find_nearest(Vector(co[i]))
        if hit[0] is None:
            continue
        d = -hit[3] if (hit[3] < INSIDE_MM and (Vector(co[i]) - hit[0]).dot(hit[1]) < -0.5 * hit[3]) else hit[3]
        best = d if best is None else min(best, d)
    return best
