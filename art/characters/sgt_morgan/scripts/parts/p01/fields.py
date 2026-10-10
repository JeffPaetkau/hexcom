"""Part 01's sculpt of the foot (spec 01 §4.2-§4.3) as displacement fields in frame F.

Pass A is a set of fields, each the displacement of the foot's vertices for a unit amount (a millimetre, a
per cent of a width): the heel's width and back, the malleoli, the dorsum, the midfoot's girth, the arch,
the metatarsal-head line, and each toe's length, width and thickness. A sculpt of fields is linear in its
amounts, so fit_sculpt.py solves them by least squares against the dimensions of spec 01 §3.1 and §3.3,
exactly as fit_targets.py solves MPFB's targets, and params.json ("sculpt") keeps the result; the build
only applies it. The brush positions are the landmarks of §3.2, anchored on this body's surface (MPFB's
foot sits a few millimetres off the spec's idealised frame, so a landmark is taken where the skin is).

Pass B is fixed: the toe axes (hallux valgus, the 4th and 5th toes' roll, §4.3 step 5), a light smoothing,
the knuckles and pulps (§4.3 steps 3-4), the small bony landmarks (§4.2 steps 2, 5, 6, 8) and the nail beds
(§4.3 step 6). It runs on pass A's result, so its anchors follow the fitted shape.

contact() makes the loaded foot of §4.7 from the sculpted one. Everything here is numpy on the shape-key
mix: no depsgraph, no Blender operators, so the fit can evaluate the whole pipeline thousands of times.
"""
import math

import numpy as np

from lib import sculpt as S
from parts.p01 import footmetrics as fm

SIDES = ("L", "R")
TOES = (1, 2, 3, 4, 5)
REGION_Z = 330.0  # the part's reach up the leg (the sock's cuff is at 260)

# Pass A: name -> (unit, lower bound, upper bound, start). The start values come from the S2 body's
# measurements against spec 01 §3.1 (renders/01_foot/measure.json has the latest).
FIELDS = {
    "heel_back_w": ("%", -5.0, 25.0, 8.0),     # heel width, back third (y_F -20)
    "heel_mid_w": ("%", -5.0, 20.0, 6.0),      # heel width at 15 % L (y_F -44)
    "heel_fore_w": ("%", -12.0, 10.0, -2.0),   # heel width under the malleoli (y_F -64): the heel's plan
                                               # is a rounded box, not a wedge widening into the midfoot
    "heel_low_w": ("%", -5.0, 20.0, 4.0),      # the heel pad's lower bulge (z < 20)
    "heel_back_low": ("mm", -3.0, 10.0, 3.0),  # the calcaneus's back pushed back, apex near z 30
    "heel_back_high": ("mm", 0.0, 8.0, 2.0),   # the Achilles insertion above it recessed (forward only)
    "mall_lat": ("mm", 0.0, 12.0, 4.0),        # lateral malleolus (+38, -60, 76)
    "mall_med": ("mm", 0.0, 12.0, 5.0),        # medial malleolus (-38, -73, 89)
    "dorsum_50": ("mm", -8.0, 8.0, 0.0),
    "dorsum_60": ("mm", -8.0, 8.0, 3.0),
    "dorsum_70": ("mm", -8.0, 8.0, 0.0),
    "mid_widen": ("%", -3.0, 18.0, 6.0),       # the midfoot's breadth (30-70 % L), lower half
    "mid_fill": ("mm", -2.0, 8.0, 3.0),        # its sides, filled toward a boxy section
    "fore_w": ("%", -6.0, 4.0, 0.0),           # the forefoot's breadth across the metatarsal heads
    "arch_drop": ("mm", -3.0, 9.0, 4.0),       # the medial arch's plantar surface lowered
    "mt_back_1": ("mm", -3.0, 12.0, 3.0),      # the metatarsal-head line moved back, medial end
    "mt_back_5": ("mm", -3.0, 22.0, 12.0),     # and lateral end (the line turns oblique)
}
for _k in TOES:
    FIELDS[f"toe{_k}_ext"] = ("mm", -10.0, 16.0, 2.0)   # length, at the tip
    FIELDS[f"toe{_k}_w"] = ("%", -30.0, 12.0, -3.0)     # width across the toe
    FIELDS[f"toe{_k}_h"] = ("%", -35.0, 12.0, -12.0)    # thickness, about the plantar line
FIELD_NAMES = tuple(FIELDS)

# Pass B and the pair's asymmetries (spec 01 §3.3): per side
FIXED = {
    "hallux_valgus_deg": {"L": 9.0, "R": 7.0},        # angle of the hallux from the foot's axis, lateral
                                                      # (§3.3: 8, left 10, right 7; 10 closes the 1-2 gap)
    "toe5_yaw_deg": {"L": -5.0, "R": -5.0},           # 5th toe's axis, negative = medial (§3.3 says 12,
                                                      # which MPFB's toe cannot take without touching the 4th)
    "toe5_roll_deg": {"L": 40.0, "R": 35.0},          # nail turned up-and-lateral
    "toe4_roll_deg": {"L": 10.0, "R": 10.0},
    "toe2_ext_extra_mm": {"L": 0.0, "R": -1.5},       # right 2nd toe 1.5 mm shorter
    "toe_curl_deg": {2: 8.0, 3: 8.0, 4: 7.0, 5: 5.0},  # PIP flexion of the resting lesser toes
}
NAILS = {1: (17.0, 16.0, 1.5), 2: (11.0, 10.0, 1.2), 3: (10.0, 9.0, 1.0), 4: (9.0, 8.0, 1.0),
         5: (7.0, 6.0, 0.8)}  # §3.3: plate width x visible length, and the free edge beyond the bed
JOINT_SHARE = {1: 0.55, 2: 0.56, 3: 0.56, 4: 0.55, 5: 0.46}  # MTP -> IP/PIP over MTP -> tip, §3.3


# --------------------------------------------------------------------------- the foot as the sculpt sees it

class Foot:
    """One foot's geometry from the body's shape-key mix: the region's vertices in frame F (mm), their
    normals, the body/helper split, each toe's membership from the rig's deform groups, and the joint
    cubes. Built once per sculpt; the fields are built from it once and reused."""

    def __init__(self, ob, side, co, m0, ix, topo, groups):
        self.side = side
        self.co = co
        f = fm.frame(fm.with_positions(m0, co), ix, side)
        self.frame = f
        n = len(co)
        body = np.zeros(n, bool)
        body[m0.orig if m0.orig is not None else np.arange(n)] = True
        s = fm.SIDES[side]
        self.R = np.nonzero((s * co[:, 0] > 40.0) & (co[:, 2] < REGION_Z))[0]
        self.body = body[self.R]
        self.q = f.to_f(co[self.R])
        nrm = S.vertex_normals(co, *topo)
        self.nq = f.vec_to_f(nrm[self.R])
        b = self.q[self.body]
        heel = b[(b[:, 1] < -15.0) & (b[:, 1] > -55.0) & (b[:, 2] > 5.0) & (b[:, 2] < 40.0)]
        self.xc_heel = float((heel[:, 0].min() + heel[:, 0].max()) / 2.0)
        low = b[b[:, 2] < 60.0]
        self.L = float(low[:, 1].max() - low[:, 1].min())
        # the centre line of the foot in plan, slice by slice (for widening about it)
        ys = np.arange(-330.0, 40.0, 8.0)
        mids = []
        for y in ys:
            sl = b[(np.abs(b[:, 1] - y) < 6.0) & (b[:, 2] < 70.0)]
            mids.append((sl[:, 0].min() + sl[:, 0].max()) / 2.0 if len(sl) > 3 else np.nan)
        mids = np.array(mids)
        ok = np.isfinite(mids)
        self._xc = (ys[ok], mids[ok])
        # toes: membership, joints and axes
        sl = "l" if side == "L" else "r"
        self.w = {k: sum(groups.get(g, np.zeros(n)) for g in fm.toe_bones(k, side))[self.R] for k in TOES}
        self.joint = {}
        for name, g in groups.items():
            if name.startswith(f"joint-{sl}-"):
                sel = g > 0.5
                if sel.any():
                    self.joint[name[len(f"joint-{sl}-"):]] = f.to_f(co[sel].mean(axis=0))
        self.toe = {k: self._toe(k) for k in TOES}

    def xc(self, y):
        return np.interp(y, *self._xc)

    def _toe(self, k):
        """A toe's frame: MTP (the joint cube), plan axis toward the tip, plan normal, length, and its
        centre line and plantar line along the axis."""
        mtp = self.joint[f"toe-{k}-1"]
        mine = (self.w[k] > 0.5) & self.body
        tq = self.q[mine]
        tip = tq[np.argmin(tq[:, 1])]
        a = (tip - mtp)[:2]
        a = np.array([a[0], a[1], 0.0]) / np.linalg.norm(a)
        nrm = np.array([-a[1], a[0], 0.0])  # +x side (lateral) for a toe pointing -y
        if nrm[0] < 0:
            nrm = -nrm
        t_all = (self.q - mtp) @ a
        length = float((tip - mtp) @ a)
        t = (tq - mtp) @ a
        bins = np.arange(-6.0, length + 6.0, 3.0)
        cl, zb = [], []
        for b0 in bins:
            s = tq[np.abs(t - b0) < 2.5]
            cl.append(float(((s - mtp) @ nrm).mean()) if len(s) > 2 else np.nan)
            zb.append(float(s[:, 2].min()) if len(s) > 2 else np.nan)
        cl, zb = np.array(cl), np.array(zb)
        okc, okz = np.isfinite(cl), np.isfinite(zb)
        axis3 = tip - mtp
        return {"mtp": mtp, "tip": tip, "a": a, "n": nrm, "len": length, "t": t_all,
                "axis3": axis3 / np.linalg.norm(axis3),
                "cl": (bins[okc], cl[okc]), "zb": (bins[okz], zb[okz])}

    def extreme(self, q, y_range, z0, toward, window=6.0):
        """The skin's most prominent point along `toward` among body vertices with y in y_range within
        `window` of height z0, returned at height z0 (its x and y from that vertex)."""
        t = np.asarray(toward, float)
        b = q[self.body]
        sel = (b[:, 1] >= y_range[0]) & (b[:, 1] <= y_range[1]) & (np.abs(b[:, 2] - z0) < window)
        if not sel.any():
            raise LookupError(f"foot {self.side}: no skin at y {y_range}, z {z0}")
        c = b[sel][np.argmax(b[sel] @ t)]
        return np.array([c[0], c[1], z0])

    def surface(self, q, p0, toward, window=7.0):
        """The skin where a ray along `toward` through the landmark p0 leaves the foot: p0 moved along the ray
        to the furthest body vertex within `window` of the line (so a bump sits at the landmark's own height,
        not at the widest vertex near it)."""
        t = np.asarray(toward, float)
        t = t / np.linalg.norm(t)
        b = q[self.body]
        p0 = np.asarray(p0, float)
        d = b - p0
        off = np.linalg.norm(d - np.outer(d @ t, t), axis=1)
        proj = b @ t
        # only the skin on the ray's exit side counts: on a sparse patch the nearest vertex to the line can
        # lie on the far side of the limb (the lateral malleolus once landed on the medial skin)
        wide = off < 3.0 * window
        if not wide.any():
            raise LookupError(f"foot {self.side}: no skin along {list(toward)} through {list(p0)}")
        exit_side = proj > proj[wide].max() - 20.0
        for w in (window, 1.5 * window, 2.5 * window):  # a sparse patch of the mesh: look a little wider
            sel = (off < w) & exit_side
            if sel.any():
                return p0 + (float(proj[sel].max()) - p0 @ t) * t
        raise LookupError(f"foot {self.side}: no skin along {list(toward)} through {list(p0)}")


# --------------------------------------------------------------------------- pass A: the fitted fields

def _gauss(x, mu, sigma):
    return np.exp(-0.5 * ((np.asarray(x, float) - mu) / sigma) ** 2)


def _plateau(x, a0, a1, b1, b0):
    """0 outside [a0, b0], 1 inside [a1, b1], smooth between (works whichever way the axis runs)."""
    return S.smoothstep(x, a0, a1) * (1.0 - S.smoothstep(x, b1, b0))


def fields(foot):
    """{name: (n_region, 3) displacement in F for a unit amount} for every pass-A field."""
    q, nq, L = foot.q, foot.nq, foot.L
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    zero = np.zeros_like(q)
    F = {}

    def dx(w):
        out = zero.copy()
        out[:, 0] = w
        return out

    def dy(w):
        out = zero.copy()
        out[:, 1] = w
        return out

    def dz(w):
        out = zero.copy()
        out[:, 2] = w
        return out

    # the heel: widened about its centre line, its pad's lower bulge, and its back reshaped so that the
    # most posterior point sits lower (§3.1: heel breadth 71, 66/70/71 at 15 % L, pternion at z 30)
    xc = foot.xc_heel
    wz_heel = 1.0 - S.smoothstep(z, 32.0, 70.0)  # fading out under the malleoli (a quicker fade left a groove)
    F["heel_back_w"] = dx((x - xc) * 0.01 * _gauss(y, -20.0, 13.0) * wz_heel)
    F["heel_mid_w"] = dx((x - xc) * 0.01 * _gauss(y, -44.0, 11.0) * wz_heel)
    F["heel_fore_w"] = dx((x - xc) * 0.01 * _gauss(y, -64.0, 9.0) * wz_heel)
    F["heel_low_w"] = dx((x - xc) * 0.01 * _plateau(y, 2.0, -12.0, -60.0, -90.0) * (1.0 - S.smoothstep(z, 8.0, 30.0)))
    post = S.smoothstep(y, -30.0, -6.0) * (1.0 - S.smoothstep(np.abs(x - xc), 18.0, 40.0))
    F["heel_back_low"] = dy(post * _gauss(z, 24.0, 10.0))
    F["heel_back_high"] = dy(-post * _gauss(z, 58.0, 10.0))

    # the malleoli (§3.2: lateral apex (+38, -60, 76), medial (-38, -73, 89), each with the hollow under it),
    # anchored on this ankle's skin. MakeHuman's ankle quads are about 13 mm, so a bone spans a 2 x 2 patch:
    # the brushes reach the nearest vertex's ring (radius about 1.7 x the spacing) or they move one vertex;
    # they sit 3 mm above the apexes because the ankle flares below them and pulls a dome's top down
    # (MPFB's medial ankle is most prominent 8 mm ahead of the spec's idealised apex, so each bone is centred
    # on this ankle's own most prominent skin within 12 mm of the spec's position, at the spec's height)
    for name, (y0, z0, r, sign) in {"mall_lat": (-60.0, 79.0, 22.0, 1.0), "mall_med": (-73.0, 92.0, 24.0, -1.0)}.items():
        c = foot.extreme(q, (y0 - 12.0, y0 + 12.0), z0, (sign, 0.0, 0.0))
        bump = S.inflate_field(q, nq, c, r, "smooth")
        under = S.inflate_field(q, nq, c - np.array([0.0, 0.0, 0.9 * r]), 0.6 * r, "smooth")
        F[name] = bump - 0.3 * under

    # the dorsum, raised or lowered along its top at 50, 60 and 70 % L (§3.1: 66 / 56 / 40)
    top = S.smoothstep(nq[:, 2], 0.30, 0.80)
    for p, sigma in ((50, 14.0), (60, 14.0), (70, 11.0)):
        F[f"dorsum_{p}"] = dz(top * _gauss(y, -p / 100.0 * L, sigma) * (1.0 - S.smoothstep(z, 110.0, 140.0)))

    # the midfoot: wider in its lower half and fuller at the sides, so its section is boxy rather than a
    # teardrop (§3.1: instep girth 263 with a dorsum of 66 needs a broad, steep-sided section)
    band = _plateau(y, -0.26 * L, -0.36 * L, -0.56 * L, -0.65 * L)
    xcy = foot.xc(y)
    F["mid_widen"] = dx((x - xcy) * 0.01 * band * (1.0 - 0.65 * S.smoothstep(z, 30.0, 62.0)))
    sides = S.smoothstep(np.abs(nq[:, 0]), 0.35, 0.75) * (1.0 - S.smoothstep(np.abs(nq[:, 2]), 0.55, 0.85))
    F["mid_fill"] = nq * (band * sides * _plateau(z, 10.0, 20.0, 46.0, 62.0))[:, None]
    # (the band stops short of the metatarsal heads: the foot's widest point stays the ball)
    fore = _plateau(y, -0.56 * L, -0.62 * L, -0.78 * L, -0.84 * L)
    F["fore_w"] = dx((x - xcy) * 0.01 * fore * (1.0 - S.smoothstep(z, 40.0, 60.0)))

    # the medial arch's plantar surface (§3.1: 13 mm clear at 45 % L, standing)
    medial = S.smoothstep(xcy - x, 2.0, 22.0)
    plantar = S.smoothstep(-nq[:, 2], 0.15, 0.55)
    F["arch_drop"] = dz(-_gauss(y, -0.45 * L, 30.0) * medial * plantar * (1.0 - S.smoothstep(z, 30.0, 48.0)))

    # the metatarsal-head line moved back, more laterally than medially, the toes travelling with their
    # heads (§4.2 step 8: MPFB's heads sit too far forward and its head line is too square)
    x1, x5 = foot.joint["toe-1-1"][0], foot.joint["toe-5-1"][0]
    u = S.smoothstep(x, x1, x5)
    ramp = S.smoothstep(y, -0.42 * L, -0.70 * L)
    F["mt_back_1"] = dy((1.0 - u) * ramp)
    F["mt_back_5"] = dy(u * ramp)

    # each toe: length along its axis (the tip moves the amount, the MTP not at all), width across it and
    # thickness above its plantar line, beyond the web
    for k in TOES:
        T = foot.toe[k]
        w = foot.w[k]
        t = T["t"]
        F[f"toe{k}_ext"] = (np.clip(t, 0.0, None) / T["len"] * w)[:, None] * T["a"][None, :]
        ramp_t = S.smoothstep(t, 0.05 * T["len"], 0.35 * T["len"])
        side = (q - T["mtp"]) @ T["n"] - np.interp(t, *T["cl"])
        F[f"toe{k}_w"] = (side * 0.01 * w * ramp_t)[:, None] * T["n"][None, :]
        F[f"toe{k}_h"] = dz((z - np.interp(t, *T["zb"])) * 0.01 * w * ramp_t)

    return F


def amounts(params=None):
    """Pass A's amounts: the fitted values in params.json ("sculpt"), else the start values."""
    got = (params or {}).get("sculpt") or {}
    return {k: float(got.get(k, FIELDS[k][3])) for k in FIELD_NAMES}


def pass_a(foot, F, a):
    out = foot.q.copy()
    for k in FIELD_NAMES:
        v = a.get(k, 0.0)
        if v:
            out += v * F[k]
    return out


# --------------------------------------------------------------------------- pass B: fixed operations

def _toe_angle(T):
    """The toe's plan angle from the foot's axis, degrees, positive lateral."""
    return math.degrees(math.atan2(T["a"][0], -T["a"][1]))


def pass_b(foot, q, adj, opts=None, nails=True, separate=True):
    """The fixed operations on pass A's result q (F, mm); returns the new positions."""
    o = dict(FIXED, **(opts or {}))
    side = foot.side
    q = q.copy()
    qa = q.copy()

    def toe_now(k):
        """The toe's MTP and tip on the current positions (its MTP cube moved with pass A)."""
        T = foot.toe[k]
        mine = (foot.w[k] > 0.5) & foot.body
        cube = foot.cube_rows.get(f"toe-{k}-1")
        mtp = q[cube].mean(axis=0) if cube is not None and len(cube) else T["mtp"]
        tq = q[mine]
        tip = tq[np.argmax((tq - mtp) @ T["a"])]
        return mtp, tip

    # 1. toe axes: hallux valgus, the 5th toe turned in and both outer toes rolled (§4.3 step 5)
    for k, yaw, roll in ((1, o["hallux_valgus_deg"][side] - _toe_angle(foot.toe[1]), 0.0),
                         (4, 0.0, o["toe4_roll_deg"][side]),
                         (5, o["toe5_yaw_deg"][side] - _toe_angle(foot.toe[5]), o["toe5_roll_deg"][side])):
        T = foot.toe[k]
        mtp, tip = toe_now(k)
        t = (q - mtp) @ T["a"]
        w = foot.w[k] * S.smoothstep(t, -0.05 * T["len"], 0.30 * T["len"])
        if yaw:
            q += S.rotation_field(q, mtp, (0.0, 0.0, 1.0), yaw, w)
        if roll:
            axis = tip - mtp
            q += S.rotation_field(q, mtp, -axis, roll, w)  # about the distal axis, negated: the nail turns lateral
    # 2. (§4.2 step 10's smoothing pass is left out: every field here is smooth, and a Laplacian pass over
    #    the foot flattened the malleoli the fit had placed, so the fit drove them to their bounds)
    # the lesser toes rest slightly curled: the middle and distal phalanges flexed at the PIP, the knuckle up
    for k in (2, 3, 4, 5):
        T = foot.toe[k]
        mtp, tip = toe_now(k)
        cube = foot.cube_rows.get(f"toe-{k}-2")
        if cube is None or not len(cube):
            continue
        pip = q[cube].mean(axis=0)
        t = (q - pip) @ T["a"]
        w = foot.w[k] * S.smoothstep(t, -1.5, 3.0)
        side_axis = np.array([T["n"][0], T["n"][1], 0.0])
        q += S.rotation_field(q, pip, side_axis, o["toe_curl_deg"][k], w)
    # 3. knuckles: the IP / PIP joints raised dorsally, the skin just past them lowered (§4.3 step 3)
    for k in TOES:
        T = foot.toe[k]
        mtp, tip = toe_now(k)
        a = T["a"]
        jt = JOINT_SHARE[k] * float((tip - mtp) @ a)
        t = (q - mtp) @ a
        mine = (foot.w[k] > 0.5) & foot.body & (np.abs(t - jt) < 3.0)
        if not mine.any():
            continue
        knuckle = q[mine][np.argmax(q[mine][:, 2])]
        amt, r = (1.2, 6.0) if k == 1 else (0.8, 5.0)
        tw = foot.w[k]
        q += amt * S.inflate_field(q, foot.nq, knuckle, r, "smooth", tw)
        q += S.move_field(q, knuckle + a * 4.5 - np.array([0.0, 0.0, 0.6]), 3.5, (0.0, 0.0, -0.4), "smooth", tw)
    # 4. pulps: the plantar pad of each toe filled (§4.3 step 4); the hallux pad stays 2 mm off the floor
    for k in TOES:
        T = foot.toe[k]
        mtp, tip = toe_now(k)
        c = tip - T["a"] * 4.0
        c[2] = max(0.0, tip[2] - 4.0)
        amt = 1.5 if k == 1 else 1.0
        down = S.smoothstep(-foot.nq[:, 2], -0.2, 0.4)
        q += amt * S.inflate_field(q, foot.nq, c, 7.0, "smooth", foot.w[k] * down)
    for ks, floor in (((1,), 2.0), ((2, 3, 4, 5), 1.0)):  # the hallux pad 2 mm up, the others 1 (§4.3 step 4)
        pad = sum(foot.w[k] for k in ks) * foot.body
        lifted = floor + np.logaddexp(0.0, 3.0 * (q[:, 2] - floor)) / 3.0  # a smooth max(z, floor)
        q[:, 2] += (np.where(q[:, 2] < floor + 2.0, lifted, q[:, 2]) - q[:, 2]) * pad
    # 5. bony landmarks (§3.2, §4.2 steps 2, 5, 6, 8), anchored on the skin as it now is
    L = foot.L
    # (radii about 1.7 x the local vertex spacing, 8-10 mm on the midfoot and heel, or a bump is one vertex
    # and subdivides to a pimple)
    bumps = (("navicular", -120.0, 42.0, (-1.0, 0.0, 0.0), 15.0, 3.0, "smooth"),
             ("mt5_base", -150.0, 18.0, (1.0, 0.0, 0.0), 14.0, 3.0, "smooth"),
             ("peroneal", -60.0, 22.0, (1.0, 0.0, 0.0), 11.0, 1.0, "smooth"),
             ("tuberosity", -6.0, 52.0, (0.0, 1.0, 0.0), 15.0, 1.5, "smooth"),
             ("mt1_head", -0.745 * L, 22.0, (-1.0, 0.0, 0.0), 14.0, 1.5, "smooth"))
    for _name, y0, z0, toward, r, amt, kind in bumps:
        c = foot.surface(q, (foot.xc_heel if toward[1] else 0.0, y0, z0), toward, window=8.0)
        q += amt * S.inflate_field(q, foot.nq, c, r, kind, foot.body.astype(float))
    xc = foot.xc_heel
    tendon = [foot.surface(q, (xc, 0.0, z), (0.0, 1.0, 0.0), window=6.0) for z in (62.0, 100.0, 140.0)]
    q += 3.0 * foot.nq * S.line_weights(q, tendon, 12.0)[:, None] * foot.body[:, None]
    for sgn in (1.0, -1.0):
        c = foot.surface(q, (0.0, -28.0, 95.0), (sgn, 0.0, 0.0), window=9.0)
        q -= 3.5 * S.inflate_field(q, foot.nq, c, 18.0, "smooth", foot.body.astype(float))
    crest = [_top(foot, q, x0, y0) for x0, y0 in ((-12.0, -140.0), (-6.0, -95.0))]
    q += 1.5 * foot.nq * S.line_weights(q, crest, 10.0)[:, None] * foot.body[:, None]
    # 6. nail beds: each nail patch sized to §3.3, sunk 0.4 mm, its folds raised (§4.3 step 6)
    if nails:
        q = nail_beds(foot, q, adj)
    # 7. no two toes closer than GAP_MM in rest (§4.3 step 5); fit_sculpt.py leaves it out (see Body)
    return separate_toes(foot, q) if separate else q


GAP_MM = 1.5  # §4.3 step 5 asks for 1.0 between neighbouring toes in rest; the margin covers the subdivision
              # and measure()'s slightly different toe sets


def toe_gaps(foot, q, beyond=0.4):
    """{k: the smallest distance from toe k's outer vertices to toe k+1's surface} (F, mm)."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    out = {}
    for k in (1, 2, 3, 4):
        A = np.nonzero((foot.w[k] > 0.5) & foot.body)[0]
        T = foot.toe[k]
        t = (q[A] - T["mtp"]) @ T["a"]
        A = A[t > beyond * T["len"]]
        tb = foot.toe_tris[k + 1]
        if not len(A) or not len(tb):
            continue
        tree = BVHTree.FromPolygons(q.tolist(), tb.tolist(), all_triangles=True)
        out[k] = min(tree.find_nearest(Vector(q[i]))[3] for i in A.tolist())
    return out


def separate_toes(foot, q, gap=GAP_MM, rounds=3):
    """Where two neighbouring toes come closer than `gap`, the outer one and every toe beyond it turn away
    by the shortfall at their tips (nothing moves at the MTP): the toes stay a set, spaced as real toes in
    a relaxed foot."""
    for _ in range(rounds):
        gaps = toe_gaps(foot, q)
        short = {k: gap - g for k, g in gaps.items() if g < gap - 0.05}
        if not short:
            break
        for k, d in short.items():
            for j in range(k + 1, 6):
                T = foot.toe[j]
                t = (q - T["mtp"]) @ T["a"]
                q[:, 0] += 1.15 * d * foot.w[j] * np.clip(t / T["len"], 0.0, 1.0)
    return q


def plane_normal(points, hint):
    """The normal of the plane through points (the direction of least spread), on the side of hint."""
    d = points - points.mean(axis=0)
    n = np.linalg.svd(d, full_matrices=False)[2][-1]
    return n if n @ hint >= 0 else -n


def _top(foot, q, x0, y0, window=8.0):
    """The dorsal skin over a plan point: the highest body vertex within `window` of (x0, y0)."""
    b = q[foot.body]
    sel = (np.abs(b[:, 0] - x0) < window) & (np.abs(b[:, 1] - y0) < window) & (b[:, 2] < 150.0)
    if not sel.any():
        raise LookupError(f"foot {foot.side}: no dorsum over x {x0}, y {y0}")
    c = b[sel]
    return c[np.argmax(c[:, 2])]


def nail_beds(foot, q, adj):
    indptr, nb = adj
    for k in TOES:
        P = foot.nail_rows[k]
        if not len(P):
            continue
        T = foot.toe[k]
        c = q[P].mean(axis=0)
        nrm = plane_normal(q[P], foot.nq[P].mean(axis=0))
        a = T["a"] - (T["a"] @ nrm) * nrm
        a /= np.linalg.norm(a)
        b = np.cross(nrm, a)
        da, db = (q[P] - c) @ a, (q[P] - c) @ b
        width, length = db.max() - db.min(), da.max() - da.min()
        tw, tl = NAILS[k][0], NAILS[k][1] - NAILS[k][2]  # the bed: the visible length less the free edge
        sa, sb = tl / length, tw / width
        # the patch scales in its own plane; a ring two vertices deep around it follows by half and a quarter
        ring1 = np.setdiff1d(np.unique(np.concatenate([nb[indptr[i]:indptr[i + 1]] for i in P])), P)
        ring2 = np.setdiff1d(np.unique(np.concatenate([nb[indptr[i]:indptr[i + 1]] for i in ring1])), np.r_[P, ring1])
        for rows, share in ((P, 1.0), (ring1, 0.5), (ring2, 0.2)):
            d = q[rows] - c
            q[rows] += share * (((d @ a) * (sa - 1.0))[:, None] * a + ((d @ b) * (sb - 1.0))[:, None] * b)
        q[P] -= 0.4 * nrm
        # folds: proximal (eponychium) 0.4, lateral 0.3, none at the free edge (the hyponychium)
        d = q[ring1] - c
        along = (d @ a) / max(tl / 2.0, 1e-6)
        lift = np.where(along < -0.6, 0.4, np.where(along > 0.7, 0.0, 0.3))
        q[ring1] += lift[:, None] * nrm
    return q


# --------------------------------------------------------------------------- the whole sculpt

class Body:
    """What the sculpt reads from the body once: the mix, a measure read, the index sets, the topology
    with its adjacency, and the vertex groups it uses."""

    def __init__(self, ob, exclude=()):
        self.ob = ob
        self.co = S.mix(ob, exclude=exclude) * 1000.0
        self.m0 = fm.read(ob)
        self.ix = fm.index(ob, self.m0)
        self.topo = S.topology(ob.data)
        self.adj = S.adjacency(len(self.co), S.edges_from_polys(*self.topo))
        names = [g.name for g in ob.vertex_groups if g.name.startswith(("toe", "joint-l-", "joint-r-"))]
        names.append("toenails")
        self.groups = S.group_weights_many(ob, names)
        self.feet = {}
        for side in SIDES:
            foot = Foot(ob, side, self.co, self.m0, self.ix, self.topo, self.groups)
            # rows of the joint cubes and nails within the region, for pass B
            pos = {int(v): i for i, v in enumerate(foot.R)}
            sl = "l" if side == "L" else "r"
            foot.cube_rows = {}
            for name, g in self.groups.items():
                if name.startswith(f"joint-{sl}-toe-"):
                    rows = [pos[i] for i in np.nonzero(g > 0.5)[0] if i in pos]
                    foot.cube_rows[name[len(f"joint-{sl}-"):]] = np.array(rows, np.int64)
            nails = self.groups["toenails"][foot.R] > 0.5
            foot.nail_rows = {k: np.nonzero(nails & (foot.w[k] > 0.5) & foot.body)[0] for k in TOES}
            # the region's own adjacency (row indices), for smoothing and the nail rings; each toe's triangles
            foot.adj = _sub_adjacency(self.adj, foot.R, len(self.co))
            tris = _region_tris(self.topo, foot.R, len(self.co))
            foot.toe_tris = {k: tris[((foot.w[k] > 0.5) & foot.body)[tris].all(axis=1)] for k in TOES}
            self.feet[side] = foot
        self._fields = {}

    def fields(self, side):
        if side not in self._fields:
            self._fields[side] = fields(self.feet[side])
        return self._fields[side]

    def sculpt_side(self, side, a, opts=None, separate=True):
        """Frame-F positions of one foot's region after both passes, for the amounts a. separate=False leaves
        out the toe separation, a threshold that would make a fit's differences meaningless (it moves the toes
        sideways by a millimetre or two, which no fitted dimension reads)."""
        foot = self.feet[side]
        a = dict(a)
        o = dict(FIXED, **(opts or {}))
        a["toe2_ext"] = a.get("toe2_ext", 0.0) + o["toe2_ext_extra_mm"][side]
        qa = pass_a(foot, self.fields(side), a)
        return pass_b(foot, qa, foot.adj, o, separate=separate)

    def positions(self, a, opts=None, sides=SIDES):
        """World positions (mm, every vertex) of the sculpted body."""
        out = self.co.copy()
        for side in sides:
            foot = self.feet[side]
            out[foot.R] = foot.frame.to_w(self.sculpt_side(side, a, opts))
        return out


def _region_tris(topo, rows, n):
    """Fan triangles of the polygons lying wholly in a region, as region rows (T, 3)."""
    ls, lt, lv = topo
    pos = np.full(n, -1, np.int64)
    pos[rows] = np.arange(len(rows))
    out = []
    for k in range(1, int(lt.max()) - 1):
        ok = lt > k + 1
        tri = np.stack([lv[ls[ok]], lv[ls[ok] + k], lv[ls[ok] + k + 1]], axis=1)
        out.append(pos[tri])
    tri = np.concatenate(out)
    return tri[(tri >= 0).all(axis=1)]


def _sub_adjacency(adj, rows, n):
    """The adjacency restricted to a subset of vertices, re-indexed to the subset's rows."""
    indptr, nb = adj
    pos = np.full(n, -1, np.int64)
    pos[rows] = np.arange(len(rows))
    counts, out = [], []
    for v in rows:
        nn = pos[nb[indptr[v]:indptr[v + 1]]]
        nn = nn[nn >= 0]
        counts.append(len(nn))
        out.append(nn)
    ptr = np.zeros(len(rows) + 1, np.int64)
    ptr[1:] = np.cumsum(counts)
    return ptr, (np.concatenate(out) if out else np.zeros(0, np.int64))


# --------------------------------------------------------------------------- the loaded foot (§4.7)

def contact(body, side, q):
    """The loaded foot from the sculpted rest foot q (F, mm): the plantar contact flattened onto the floor,
    the heel pad's rim spread 3.5 mm, the medial arch down 2.5, the ball's rim spread 1.5, the toe tips 2
    mm further forward and the toe pads down onto the floor."""
    foot = body.feet[side]
    L = foot.L
    q = q.copy()
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    bodyw = foot.body.astype(float)
    # the heel pad's sides bulge 3.5 mm outward near the floor, the ball's rim 1.5 mm: along the skin's
    # own horizontal normal, most at z 2-10 and gone by z 20
    nxy = foot.nq[:, :2]
    nlen = np.linalg.norm(nxy, axis=1)
    out = nxy / np.maximum(nlen, 1e-9)[:, None]
    sides = S.smoothstep(nlen, 0.25, 0.6) * bodyw
    low = _plateau(z, -1.0, 2.0, 10.0, 20.0)
    heel = _plateau(y, 10.0, 0.0, -55.0, -75.0)
    ball = _gauss(y, -0.70 * L, 18.0) * (1.0 - sum(foot.w.values()).clip(0.0, 1.0))
    q[:, :2] += ((1.75 * heel + 0.75 * ball) * low * sides)[:, None] * out  # §3.5's spreads are of the width
    # the arch drops 2.5 mm medially at 35-55 % L
    medial = S.smoothstep(foot.xc(y) - x, 0.0, 20.0)
    q[:, 2] -= 2.5 * _gauss(y, -0.45 * L, 22.0) * medial * (1.0 - S.smoothstep(z, 40.0, 70.0)) * bodyw
    # toes 2 mm longer; their pads settle onto the floor
    for k in TOES:
        T = foot.toe[k]
        w = foot.w[k] * S.smoothstep(T["t"], 0.0, 0.6 * T["len"])
        q[:, :2] += 2.0 * w[:, None] * T["a"][None, :2]
        mine = foot.w[k] > 0.5
        low = q[mine, 2].min() if mine.any() else 0.0
        pad = foot.w[k] * (1.0 - S.smoothstep(q[:, 2] - low, 1.0, 6.0)) * S.smoothstep(T["t"], 0.4 * T["len"], 0.7 * T["len"])
        q[:, 2] -= min(low, 1.5) * pad
    # the plantar contact flattened onto z 0: what lies within 4 mm of the floor (Foot.PlantarContact) goes
    # down onto it, fading out by 8 mm (§3.5: the pad compresses 4 mm)
    flat = (1.0 - S.smoothstep(q[:, 2], 4.0, 8.0)) * bodyw
    q[:, 2] *= 1.0 - flat
    q[:, 2] = np.maximum(q[:, 2], 0.0)
    return q
