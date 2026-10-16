"""Part 01's sculpt of the foot (spec 01 §4.2-§4.3) as displacement fields in frame F.

Pass A is a set of fields, each the displacement of the foot's vertices for a unit amount (a millimetre, a
per cent of a width): the heel's width and back, the malleoli, the dorsum, the midfoot's girth, the arch,
the metatarsal-head line, the plan outline seen from above (the lateral and medial borders, the 5th head's
corner and the sections' fullness, 2026-10-14), and each toe's length, width and thickness. A sculpt of
fields is linear in its amounts, so fit_sculpt.py solves them by least squares against the dimensions of
spec 01 §3.1 and §3.3, exactly as fit_targets.py solves MPFB's targets, and params.json ("sculpt") keeps the
result; the build only applies it. The brush positions are the landmarks of §3.2, anchored on this body's
surface (MPFB's foot sits a few millimetres off the spec's idealised frame, so a landmark is taken where the
skin is).

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
    "heel_end_w": ("%", -5.0, 40.0, 0.0),      # heel width at its back end (y_F -8): a round heel, not a point
    "heel_back_w": ("%", -5.0, 25.0, 8.0),     # heel width, back third (y_F -20)
    "heel_mid_w": ("%", -5.0, 20.0, 6.0),      # heel width at 15 % L (y_F -44)
    "heel_fore_w": ("%", -12.0, 10.0, -2.0),   # heel width under the malleoli (y_F -64): the heel's plan
                                               # is a rounded box, not a wedge widening into the midfoot
    "heel_low_w": ("%", -5.0, 20.0, 4.0),      # the heel pad's lower bulge (z < 20)
    "heel_top_w": ("%", -20.0, 20.0, 0.0),     # the heel above the pad (z 35-55): its breadth there, apart
                                               # from the pad's
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
    # the plan outline (the shape pass, 2026-10-14, spec 01 §3.1 note; Jeff: "from the top it looks too long and too
    # round"): the lateral midfoot drawn in, so the border runs straight from the heel to the 5th metatarsal head and
    # the ball is the widest part; the medial border drawn in ahead of the navicular (the dip along the first
    # metatarsal seen from above); the 5th head's corner pushed out. 0 is the build before the pass
    "lat_mid_in": ("mm", -2.0, 16.0, 0.0),
    "med_mid_in": ("mm", -2.0, 8.0, 0.0),
    "head5_out": ("mm", -2.0, 6.0, 0.0),
    "mid_lat_up": ("mm", -3.0, 4.0, 0.0),     # the midfoot's lateral column raised (the instep's fullness)
    "fore_lat_up": ("mm", -3.0, 4.0, 0.0),    # the forefoot's lateral column raised (the ball's); more than
                                              # about 4 reads as a cushion along the lateral border in V3
    "fore_low_fill": ("mm", -2.0, 4.0, 0.0),  # the forefoot's sides below the heads' bulges filled out
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
    "toe_dip_deg": {2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0},   # DIP flexion
    "hallux_ip_deg": 0.0,     # the hallux's IP flexion (it rests nearly straight)
    "toe_mtp_floor": False,   # extend each lesser toe at its MTP until its pad is back on the floor (a curled
                              # toe's tip would otherwise go through it): the knuckle rises, the tip tucks down
    "toe_mid_short_mm": {2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0},  # middle phalanx shortened (MPFB's are long)
    "toe_gap_mm": 1.5,        # the least gap kept between neighbouring toes in rest (separate_toes)
    "toe_gather": False,      # and the most: the lesser toes turned toward the hallux until they touch
    "toe_gap_pairs": {},      # {"1-2": [least, most]}: a pair's own gap band (the hallux stands apart)
    "hallux_width_mm": 0.0,   # the hallux widened from its IP forward to this plan width (0: as fitted)
    "nail_size": {},          # {toe: [width, visible length]} over §3.3's (the nail scaled with its toe)
    "web_y": {},              # {"3-4": y_F}: the cleft between two toes closed back from y_F (webs forward)
    "web_gap_mm": 0.2,        # what is left of a closed cleft: the toes touch but do not intersect
    "hallux_short_mm": [0.0, 0.0],  # [proximal phalanx, distal segment]: the hallux shortened (shorten_hallux)
    # shape pass 2 (2026-10-15, critic series foot_shape round 1; spec 01 §4.3 note): the lesser toes' knuckles
    # (dorsal bump, the dip past it, mm; their waists are filled on the dense skin, research/foot_hires/macro.py),
    # the heel tapered above its pad (heel_taper) and the front of the ankle's fillet tightened (ankle_front); the
    # first pass's knuckles and empty tables are the build before
    "lesser_knuckle_mm": [0.8, 0.4],
    "heel_taper": {},
    "ankle_front": {},
}
SIDE_KEYED = ("hallux_valgus_deg", "toe5_yaw_deg", "toe5_roll_deg", "toe4_roll_deg", "toe2_ext_extra_mm")
TOE_KEYED = ("toe_curl_deg", "toe_dip_deg", "toe_mid_short_mm", "nail_size")
NAILS = {1: (19.5, 15.3, 1.5), 2: (11.0, 10.0, 1.2), 3: (10.0, 9.0, 1.0), 4: (9.0, 8.0, 1.0),
         5: (7.0, 6.0, 0.8)}  # §3.3: plate width x visible length, and the free edge beyond the bed (the
# hallux's 19.5 x 18.35 since Jeff's lock of 2026-10-10, from reference photos: 17 x 16 scaled with the toe; 15.3 long
# since 2026-10-15, shortened with its distal segment, 36.2 -> 30.2 mm from the IP: Jeff's shorter big toe)
NAIL_RADIUS = {1: 11.0, 2: 6.0, 3: 5.5, 4: 5.0, 5: 4.0}  # §3.3: the plate's transverse radius of curvature
NAIL_TIP_MARGIN = {1: 2.5, 2: 1.6, 3: 1.5, 4: 1.4, 5: 1.2}  # skin left beyond the free edge, in plan
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
        mids, halves = [], []
        for y in ys:
            sl = b[(np.abs(b[:, 1] - y) < 6.0) & (b[:, 2] < 70.0)]
            mids.append((sl[:, 0].min() + sl[:, 0].max()) / 2.0 if len(sl) > 3 else np.nan)
            halves.append((sl[:, 0].max() - sl[:, 0].min()) / 2.0 if len(sl) > 3 else np.nan)
        mids, halves = np.array(mids), np.array(halves)
        ok = np.isfinite(mids)
        self._xc = (ys[ok], mids[ok])
        self._hw = (ys[ok], halves[ok])   # the half-breadth below z 70 (the plan fields' side weights)
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

    def hw(self, y):
        return np.interp(y, *self._hw)

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
    F["heel_end_w"] = dx((x - xc) * 0.01 * _gauss(y, -8.0, 8.0) * wz_heel)
    F["heel_back_w"] = dx((x - xc) * 0.01 * _gauss(y, -20.0, 13.0) * wz_heel)
    F["heel_mid_w"] = dx((x - xc) * 0.01 * _gauss(y, -44.0, 11.0) * wz_heel)
    F["heel_fore_w"] = dx((x - xc) * 0.01 * _gauss(y, -64.0, 9.0) * wz_heel)
    F["heel_low_w"] = dx((x - xc) * 0.01 * _plateau(y, 2.0, -12.0, -60.0, -90.0) * (1.0 - S.smoothstep(z, 8.0, 30.0)))
    F["heel_top_w"] = dx((x - xc) * 0.01 * _plateau(y, 5.0, -5.0, -50.0, -70.0)
                         * S.smoothstep(z, 28.0, 40.0) * (1.0 - S.smoothstep(z, 50.0, 75.0)))
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

    # the plan outline (the shape pass, 2026-10-14): moves across the foot, by side (the share of the half-breadth
    # out from the centre line), so the side profiles stay. The lateral side drawn in over the midfoot, fully at
    # the bottom where MPFB's lateral border bulges and by 40 % at the top, nothing at the heel or the 5th head;
    # the medial wall drawn in ahead of the navicular, between the arch's underside and the dorsum; the 5th head's
    # lateral surface inflated where it sits (7 mm behind the MTP joint cube, which part 01 moves with the foot)
    rel = (x - xcy) / np.maximum(foot.hw(y), 10.0)
    win_lat = _gauss(y, -0.49 * L, 0.095 * L) * (1.0 - S.smoothstep(y, -0.60 * L, -0.66 * L))
    F["lat_mid_in"] = dx(-S.smoothstep(rel, 0.2, 0.9) * win_lat * (1.0 - 0.6 * S.smoothstep(z, 25.0, 55.0)))
    win_med = _gauss(y, -0.57 * L, 0.06 * L) * S.smoothstep(y, -0.42 * L, -0.48 * L) \
        * (1.0 - S.smoothstep(y, -0.66 * L, -0.72 * L))
    F["med_mid_in"] = dx(S.smoothstep(-rel, 0.2, 0.9) * win_med * _plateau(z, 4.0, 14.0, 44.0, 62.0))
    y5 = float(foot.joint["toe-5-1"][1]) + 7.0
    c5 = foot.surface(q, (float(foot.xc(y5)), y5, 16.0), (1.0, 0.0, 0.0), window=8.0)
    F["head5_out"] = S.inflate_field(q, nq, c5, 18.0, "smooth", foot.body.astype(float))
    # the sections' fullness, where it moves neither the plan's extremes (they lie low and are moved across the foot
    # only) nor the side profiles (the crest, on the 2nd metatarsal's line, stays the highest skin of every
    # section): the lateral column raised above the sole, more toward the lateral border, so its wall is taller and
    # the slope from the crest to the border flatter; MPFB's lateral column tapers thin. A real forefoot's section
    # through the 1st and 5th heads is near a 105 x 40 rounded box (ANSUR: ball girth 259 for a breadth of 104.5)
    lateral = S.smoothstep(rel, 0.1, 0.8)
    above_sole = S.smoothstep(z, 2.0, 40.0)   # the column stretched over its height (a ramp to z 20 stood an edge)
    no_toe = 1.0 - np.clip(sum(foot.w[k] for k in TOES), 0.0, 1.0)
    F["mid_lat_up"] = dz(lateral * above_sole * _plateau(y, -0.33 * L, -0.40 * L, -0.56 * L, -0.63 * L))
    F["fore_lat_up"] = dz(lateral * above_sole * no_toe * _plateau(y, -0.56 * L, -0.61 * L, -0.74 * L, -0.80 * L))
    # and the forefoot's sides below the heads' bulges (z 2-15) filled out along the skin's horizontal normal: a
    # standing forefoot's section is near a box down to the sole, not rounded off under the heads
    nh = nq.copy()
    nh[:, 2] = 0.0
    side_w = S.smoothstep(np.linalg.norm(nh, axis=1), 0.45, 0.8)
    nh /= np.maximum(np.linalg.norm(nh, axis=1), 1e-9)[:, None]
    F["fore_low_fill"] = nh * (side_w * no_toe * _plateau(y, -0.58 * L, -0.63 * L, -0.74 * L, -0.80 * L)
                               * _plateau(z, 1.5, 4.0, 10.0, 15.0))[:, None]

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


def options(params=None):
    """Pass B's fixed operations: FIXED with params.json's "fixed" merged over it (JSON keys are strings,
    so a per-toe table's keys are made ints again)."""
    got = (params or {}).get("fixed") or {}
    out = {}
    for k, v in FIXED.items():
        g = got.get(k, v)
        if isinstance(v, dict) and isinstance(g, dict):
            merged = dict(v)
            merged.update(g)
            if k in TOE_KEYED:
                g = {int(t): (x if isinstance(x, (list, tuple)) else float(x)) for t, x in merged.items()}
            else:
                g = merged
        out[k] = g
    unknown = sorted(set(got) - set(FIXED))
    if unknown:
        raise ValueError(f"params.json 'fixed' names unknown operations {unknown}; known: {sorted(FIXED)}")
    return out


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
    # the hallux broadened (Jeff's reference photos, 2026-10-10), then the toes' resting pose: the lesser toes
    # curled, the middle and distal phalanges flexed at the PIP and the distal at the DIP, the knuckle up;
    # the hallux nearly straight
    q = shape_hallux(foot, q, o)
    for k in (1, 2, 3, 4, 5):
        q = pose_lesser_toe(foot, q, k, o)
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
        bump, dip = (1.2, 0.4) if k == 1 else (float(v) for v in o["lesser_knuckle_mm"])
        r = 6.0 if k == 1 else 5.0
        tw = foot.w[k]
        q += bump * S.inflate_field(q, foot.nq, knuckle, r, "smooth", tw)
        q += S.move_field(q, knuckle + a * 4.5 - np.array([0.0, 0.0, 0.6]), 3.5, (0.0, 0.0, -dip), "smooth", tw)
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
    # the hallux shortened (Jeff, 2026-10-15), after its knuckle and pulp are placed, so both travel with it; the
    # heel tapered above its pad and the ankle's front fillet tightened (shape pass 2)
    q = shorten_hallux(foot, q, o.get("hallux_short_mm"))
    if o.get("heel_taper"):
        q = heel_taper(foot, q, o["heel_taper"])
    if o.get("ankle_front"):
        q = ankle_front(foot, q, o["ankle_front"])
    # 5. bony landmarks (§3.2, §4.2 steps 2, 5, 6, 8), anchored on the skin as it now is
    L = foot.L
    # (radii about 1.7 x the local vertex spacing, 8-10 mm on the midfoot and heel, or a bump is one vertex
    # and subdivides to a pimple)
    bumps = (("navicular", -120.0, 42.0, (-1.0, 0.0, 0.0), 15.0, 3.0, "smooth"),
             ("mt5_base", -150.0, 17.0, (1.0, 0.0, 0.0), 16.0, 4.5, "smooth"),
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
        q = nail_beds(foot, q, adj, o.get("nail_size"))
    # 7. no two toes closer than toe_gap_mm in rest (§4.3 step 5); fit_sculpt.py leaves it out (see Body);
    #    then the clefts named in web_y closed back from there, the toes touching (webs forward)
    if separate:
        q = separate_toes(foot, q, gap=float(o["toe_gap_mm"]), gather=bool(o["toe_gather"]),
                          bands=o.get("toe_gap_pairs"))
        q = close_webs(foot, q, o)
        q = resolve_contacts(foot, q, gap=min(float(o.get("web_gap_mm", 0.2)), float(o["toe_gap_mm"])))
    return q


def resolve_contacts(foot, q, gap=0.2, rounds=4):
    """Toes may touch, never cross (Jeff, 2026-10-10): any vertex clearly of one toe that ends inside its
    neighbour (curled knuckles, the closed webs' tapers) is pushed out along the neighbour's nearest face
    normal until `gap` is left. A few vertices move a millimetre or two; the subdivision smooths them."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    q = q.copy()
    moved = {}
    for _ in range(rounds):
        pushed = 0
        for k in (1, 2, 3, 4):
            for me, other in ((k, k + 1), (k + 1, k)):
                rows = np.nonzero((foot.w[me] > 0.5) & (foot.w[other] < 0.2) & foot.body)[0]
                splits = foot.toe_tris_both[other]
                if not len(rows) or not len(splits):
                    continue
                trees = [BVHTree.FromPolygons(q.tolist(), t.tolist(), all_triangles=True) for t in splits]
                for i in rows.tolist():
                    worst = None  # the deepest of the two triangulations' readings
                    for tree in trees:
                        loc, nrm, _, d = tree.find_nearest(Vector(q[i]), INSIDE_MM)
                        if loc is None:
                            continue
                        n = np.array(nrm) * foot.frame.s  # outward in F (F mirrors the right foot)
                        off = float((q[i] - np.array(loc)) @ n)
                        if off < -0.5 * d:  # inside: behind the face, not merely beside one of its edges
                            depth = -off
                        elif d < gap:  # outside, nearer than the gap
                            depth = -d
                        else:
                            continue
                        if worst is None or depth > worst[0]:
                            worst = (depth, n)
                    if worst is None:
                        continue
                    depth, n = worst
                    q[i] += (depth + gap) * n
                    pushed += 1
                    moved[f"{me}>{other}"] = moved.get(f"{me}>{other}", 0) + 1
        if not pushed:
            break
    foot.contacts_resolved = moved
    return q


def _joint_now(foot, q, k, j):
    """Toe k's joint cube j (1 MTP, 2 PIP or IP, 3 DIP, 4 the tip's end) on the current positions."""
    rows = foot.cube_rows.get(f"toe-{k}-{j}")
    return q[rows].mean(axis=0) if rows is not None and len(rows) else None


def pose_lesser_toe(foot, q, k, o):
    """A lesser toe's resting pose (§4.3 step 5, §7.3): the middle phalanx shortened, the DIP then the PIP
    flexed about the toe's transverse axis (distal first, so each pivot travels with what is proximal to it),
    and with toe_mtp_floor the whole toe extended at the MTP until its pad is back at the height it had,
    which is how a curled toe stands: knuckle up, tip down on the floor. The defaults (PIP only, no lift)
    are the first pass's curl."""
    T = foot.toe[k]
    side_axis = np.array([T["n"][0], T["n"][1], 0.0])
    wk = foot.w[k]
    mine = (wk > 0.5) & foot.body
    mtp0 = _joint_now(foot, q, k, 1)
    t0 = (q - (mtp0 if mtp0 is not None else T["mtp"])) @ T["a"]
    distal = mine & (t0 > 0.45 * T["len"])
    low0 = float(q[distal, 2].min()) if distal.any() else None
    if k == 1:  # the hallux: one interphalangeal joint (cube 2), no middle phalanx
        short, flex = 0.0, ((2, float(o["hallux_ip_deg"])),)
    else:
        short = float(o["toe_mid_short_mm"].get(k, 0.0))
        flex = ((3, float(o["toe_dip_deg"].get(k, 0.0))), (2, float(o["toe_curl_deg"].get(k, 0.0))))
    pip, dip = _joint_now(foot, q, k, 2), _joint_now(foot, q, k, 3)
    if short and pip is not None and dip is not None:
        tp, td = (pip - mtp0) @ T["a"], (dip - mtp0) @ T["a"]
        q = q - (short * wk * S.smoothstep(t0, tp, td))[:, None] * T["a"][None, :]
    for j, ang in flex:
        piv = _joint_now(foot, q, k, j)
        if not ang or piv is None:
            continue
        t = (q - piv) @ T["a"]
        q = q + S.rotation_field(q, piv, side_axis, ang, wk * S.smoothstep(t, -1.5, 3.0))
    if o["toe_mtp_floor"] and low0 is not None and mtp0 is not None:
        mtp = _joint_now(foot, q, k, 1)
        w = wk * S.smoothstep((q - mtp) @ T["a"], -2.0, 6.0)

        def low(alpha):
            return float((q + S.rotation_field(q, mtp, side_axis, -alpha, w))[distal, 2].min())

        lo, hi = 0.0, 35.0
        if low(lo) < low0:
            for _ in range(30):  # the pad rises monotonically with the extension here
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if low(mid) < low0 else (lo, mid)
            q = q + S.rotation_field(q, mtp, side_axis, -hi, w)
            foot.mtp_lift = getattr(foot, "mtp_lift", {})
            foot.mtp_lift[k] = hi
    return q


def shorten_hallux(foot, q, short):
    """Jeff, 2026-10-15 (spec 01 §3.3 note): "toe 2 looks right; it is the big toe that is too long". The hallux
    shortened as its anatomy would be, along its plan axis: the proximal phalanx by short[0] (a smooth ramp over its
    middle, so the MTP stays and the IP moves back by it) and the distal segment by short[1] (compressed between 2 mm
    past the IP and the pulp's last 6 mm, which moves back whole, so the pulp stays round and the nail bed shortens
    with the segment; nail_beds then sizes the bed to the shorter nail). Width and depth are untouched: every move is
    along the axis."""
    sp, sd = (float(v) for v in (short or (0.0, 0.0)))
    if not (sp or sd):
        return q
    T = foot.toe[1]
    w = foot.w[1]
    mine = (w > 0.5) & foot.body
    mtp, ip = _joint_now(foot, q, 1, 1), _joint_now(foot, q, 1, 2)
    if mtp is None or ip is None:
        return q
    a = T["a"]
    t = (q - mtp) @ a
    t_ip, t_tip = float((ip - mtp) @ a), float(t[mine].max())
    # the distal compression's rate: a plateau from the IP to the pulp, integrated and normalised to 1 at the pulp
    grid = np.linspace(t_ip, t_tip, 400)
    rate = _plateau(grid, t_ip + 1.0, t_ip + 4.0, t_tip - 9.0, t_tip - 6.0)
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (rate[1:] + rate[:-1]) * np.diff(grid))])
    ramp_d = np.interp(t, grid, cum / max(cum[-1], 1e-9))
    ramp_p = S.smoothstep(t, 0.25 * t_ip, 0.9 * t_ip)
    d = (sp * ramp_p + sd * ramp_d) * w
    foot.hallux_short = {"t_ip": round(t_ip, 2), "t_tip": round(t_tip, 2), "proximal": sp, "distal": sd}
    return q - d[:, None] * a[None, :]


def heel_taper(foot, q, cfg):
    """Shape pass 2 (2026-10-15; critics: from behind the heel is a box, vertical sides about 71 apart from z 13 to
    54, square shoulders, tight lower corners). The heel drawn in about its centre line above the pad, by `pct` % of
    each point's offset, rising from z[0] to z[1] and fading out from z[2] to z[3] under the malleoli, over y[0]..y[3]
    (the back of the heel to the malleoli's front), so from behind it narrows from the pad into the Achilles; and its
    lower corners rounded (`low_pct` below low_z). The widths spec 01 §3.1 holds at z 10-30 (heel H1) barely move."""
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    xc = foot.xc_heel
    yw = _plateau(y, *cfg.get("y", (12.0, 2.0, -50.0, -75.0)))
    zw = _plateau(z, *cfg.get("z", (30.0, 52.0, 60.0, 76.0)))
    share = 0.01 * float(cfg.get("pct", 0.0)) * zw
    lz = cfg.get("low_z", (2.0, 12.0))
    share = share + 0.01 * float(cfg.get("low_pct", 0.0)) * (1.0 - S.smoothstep(z, lz[0], lz[1]))
    out = q.copy()
    out[:, 0] -= (x - xc) * share * yw * foot.body
    # the back face domed in plan: its sides drawn forward (`back_round` mm), its middle and the pternion left, so the
    # tuberosity reads as a rounded bulb from behind rather than a flat face
    br = float(cfg.get("back_round", 0.0))
    if br:
        out[:, 1] -= (br * S.smoothstep(np.abs(x - xc), 8.0, 30.0) * _plateau(z, 8.0, 18.0, 50.0, 66.0)
                      * S.smoothstep(y, -40.0, -14.0) * foot.body)
    return out


def ankle_front(foot, q, cfg):
    """Shape pass 2 (2026-10-15; critic C2: the front of the ankle one soft oversized fillet from z 140 into the
    dorsum, the instep about 98 mm high at 40 % L). In the side plane (y, z): the shin's front line through `shin` and
    `corner`, the dorsum's through `corner` and `dorsum`, and a fillet of radius `r` between them; skin standing in
    front of that fillet is moved back along its bisector by `k` of the excess (a move that keeps each point's place
    across the bisector, so it never folds), full within x_half[0] of the instep's crest and gone by x_half[1]. The
    corner is the crease (spec 01 §3.2: z 80-84). On the 13 mm ankle cage the subdivided surface rounds the corner
    by more than the cage does, so `k` above 1 overshoots the cage to bring the rendered surface onto the fillet
    (measured on the level-2 surface, as the closeups render it)."""
    C = np.array(cfg["corner"], float)
    u1 = np.array(cfg["shin"], float) - C
    u2 = np.array(cfg["dorsum"], float) - C
    u1, u2 = u1 / np.linalg.norm(u1), u2 / np.linalg.norm(u2)
    bis = (u1 + u2) / np.linalg.norm(u1 + u2)
    td = (u1 - u2) / np.linalg.norm(u1 - u2)
    alpha = 0.5 * math.acos(float(np.clip(u1 @ u2, -1.0, 1.0)))
    r, k = float(cfg.get("r", 30.0)), float(cfg.get("k", 0.85))
    d = q[:, 1:] - C
    b, t = d @ bis, d @ td
    at = np.abs(t)
    arc = at < r * math.cos(alpha)
    bt = np.where(arc, r / math.sin(alpha) - np.sqrt(np.maximum(r * r - at * at, 0.0)), at / math.tan(alpha))
    e = b - bt
    knee = 1.5   # a soft max(e, 0): nothing at or behind the fillet, quadratic over the first knee mm
    move = k * np.where(e <= 0.0, 0.0, np.where(e < knee, e * e / (2.0 * knee), e - 0.5 * knee))
    x0 = float(cfg.get("x", -4.0))
    xh = cfg.get("x_half", (22.0, 40.0))
    wx = 1.0 - S.smoothstep(np.abs(q[:, 0] - x0), xh[0], xh[1])
    yz = cfg.get("y_from", (-134.0, -124.0))   # the dorsum ahead of the fillet's tangent stays
    zone = S.smoothstep(q[:, 2], 55.0, 65.0) * S.smoothstep(q[:, 1], yz[0], yz[1]) * (1.0 - S.smoothstep(q[:, 2], 170.0, 190.0))
    m = move * wx * zone * foot.body
    out = q.copy()
    out[:, 1] -= m * bis[0]
    out[:, 2] -= m * bis[1]
    foot.ankle_front = {"moved_max": round(float(m.max()), 2), "alpha_deg": round(math.degrees(alpha), 1)}
    return out


def _plan_axis(qt):
    """A toe's plan axis toward its tip from the principal direction of its vertices (as footmetrics reads)."""
    c = qt[:, :2] - qt[:, :2].mean(axis=0)
    a = np.linalg.svd(c, full_matrices=False)[2][0]
    a = a if a[1] < 0 else -a
    return np.array([a[0], a[1], 0.0])


def hallux_width(foot, q):
    """The hallux's plan width as §8.2 measures it: across its axis, over its distal 65 %."""
    qt = q[(foot.w[1] > 0.5) & foot.body]
    a = _plan_axis(qt)
    n = np.array([-a[1], a[0], 0.0])
    t = qt @ a
    d = qt[t > t.min() + 0.35 * (t.max() - t.min())]
    s = d @ n
    return float(s.max() - s.min())


def shape_hallux(foot, q, o, rounds=5):
    """Jeff's broad hallux (2026-10-10, from reference photos): widened about its own centre line from its IP
    forward to hallux_width_mm, and thickened above its plantar line by half the same share, so the pulp
    stays a broad round pad rather than a toe squashed sideways. Measured as §8.2 measures it; a few rounds,
    since the widest section moves as the toe widens."""
    target = float(o.get("hallux_width_mm") or 0.0)
    if not target:
        return q
    w1 = foot.w[1]
    mine = (w1 > 0.5) & foot.body
    for _ in range(rounds):
        width = hallux_width(foot, q)
        share = target / width - 1.0
        if abs(share) < 0.002:
            break
        qt = q[mine]
        a = _plan_axis(qt)
        n = np.array([-a[1], a[0], 0.0])
        t_all, s_all = q @ a, q @ n
        t, s = qt @ a, qt @ n
        t0, t1 = t.min(), t.max()
        bins = np.arange(t0, t1 + 3.0, 2.0)
        cs, zs = [], []
        for b in bins:
            sl = np.abs(t - b) < 2.5
            cs.append(0.5 * (s[sl].min() + s[sl].max()) if sl.sum() > 2 else np.nan)
            zs.append(qt[sl, 2].min() if sl.sum() > 2 else np.nan)
        cs, zs = np.array(cs), np.array(zs)
        okc, okz = np.isfinite(cs), np.isfinite(zs)
        centre = np.interp(t_all, bins[okc], cs[okc])
        floor = np.interp(t_all, bins[okz], zs[okz])
        g = w1 * S.smoothstep((t_all - t0) / (t1 - t0), 0.30, 0.65)
        q = q + (share * (s_all - centre) * g)[:, None] * n[None, :]
        q[:, 2] += 0.5 * share * np.maximum(q[:, 2] - floor, 0.0) * g
    return q


def _tri_normals(q, tris):
    """Area-weighted vertex normals of a region from its triangles (rows of q)."""
    n = np.zeros_like(q)
    fn = np.cross(q[tris[:, 1]] - q[tris[:, 0]], q[tris[:, 2]] - q[tris[:, 0]])
    for c in range(3):
        np.add.at(n, tris[:, c], fn)
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 0
    n[ok] /= ln[ok, None]
    return n


def close_webs(foot, q, o, passes=4):
    """Jeff's webs forward (2026-10-10): each cleft named in web_y is closed from its web forward to y_F,
    the facing sides of the two toes brought together until web_gap_mm is left between them, so that the
    toes touch there as real toes do in front of their commissure and the cleft opens only at y_F. The
    topology stays MakeHuman's (a web cannot be grown without new faces), so the closed stretch is two
    surfaces 0.2 mm apart: a line, not a gap. Each facing vertex is moved half the gap along the pair's
    transverse direction, measured by a ray to the neighbour's surface, in a few passes; nothing moves
    further than 5-9 mm behind the old web (the pair's mean mid-proximal-phalanx, where MPFB's webs are) or
    ahead of y_F."""
    webs = o.get("web_y") or {}
    if not webs:
        return q
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    gap = float(o.get("web_gap_mm", 0.2))
    tris = foot.region_tris
    q = q.copy()
    foot.webs_closed = {}
    for pair, y_new in sorted(webs.items()):
        k = int(str(pair).split("-")[0])
        a, b = k, k + 1
        ma, mb = _joint_now(foot, q, a, 1), _joint_now(foot, q, b, 1)
        pa, pb = _joint_now(foot, q, a, 2), _joint_now(foot, q, b, 2)
        if any(v is None for v in (ma, mb, pa, pb)):
            continue
        y_old = 0.25 * (ma[1] + pa[1] + mb[1] + pb[1])  # the pair's mean mid-proximal phalanx: MPFB's webs
        am = foot.toe[a]["a"] + foot.toe[b]["a"]
        am /= np.linalg.norm(am)
        p = np.array([-am[1], am[0], 0.0])
        if p @ (mb - ma) < 0:
            p = -p
        y = q[:, 1]
        # closed from the old web to y_new, the cleft opening by 0.5 mm within a millimetre of y_new (behind the
        # web the walls are the sides of the dorsal groove between the toes: closing them there crossed them)
        W = S.smoothstep(y, y_new - 2.5, y_new + 1.5) * (1.0 - S.smoothstep(y, y_old + 1.0, y_old + 4.0))
        moved = 0
        for _ in range(passes):
            nrm = _tri_normals(q, tris) * foot.frame.s  # frame F mirrors the right foot, and its winding with it
            delta = np.zeros_like(q)
            for me, other, sgn in ((a, b, 1.0), (b, a, -1.0)):
                rows = np.nonzero((foot.w[me] > 0.5) & foot.body & (W > 0.0))[0]
                H = S.smoothstep(sgn * (nrm[rows] @ p), 0.15, 0.5)
                rows, H = rows[H > 0.0], H[H > 0.0]
                tb = foot.toe_tris[other]
                if not len(rows) or not len(tb):
                    continue
                tree = BVHTree.FromPolygons(q.tolist(), tb.tolist(), all_triangles=True)
                d = sgn * p
                for i, h in zip(rows.tolist(), H.tolist()):
                    hit = tree.ray_cast(Vector(q[i]), Vector(d), 8.0)
                    if hit[0] is None:
                        continue
                    move = max(0.0, hit[3] - gap) / 2.0 * W[i] * h
                    if move > 1e-4:
                        delta[i] += move * d
            if not np.any(delta):
                break
            q += delta
            moved = max(moved, int(np.count_nonzero(np.linalg.norm(delta, axis=1) > 0.01)))
        # nothing may end inside the neighbour: a vertex nearer than the gap, or inside it (the walls are not
        # parallel, so two half-moves can cross), is pushed back out along p; a few rounds, since a push along
        # p is not along the neighbour's normal
        for _ in range(3):
            pushed = 0
            for me, other, sgn in ((a, b, 1.0), (b, a, -1.0)):
                rows = np.nonzero((foot.w[me] > 0.5) & foot.body & (W > 0.0))[0]
                tb = foot.toe_tris[other]
                if not len(rows) or not len(tb):
                    continue
                tree = BVHTree.FromPolygons(q.tolist(), tb.tolist(), all_triangles=True)
                for i in rows.tolist():
                    hit = tree.find_nearest(Vector(q[i]), INSIDE_MM + 1.0)
                    if hit[0] is None:
                        continue
                    outside = (Vector(q[i]) - hit[0]).dot(hit[1]) * foot.frame.s >= 0.0
                    short = gap - hit[3] if outside else gap + hit[3]
                    if short > 0.01:
                        q[i] -= sgn * p * short
                        pushed += 1
            if not pushed:
                break
        foot.webs_closed[pair] = {"from_y": round(float(y_old), 1), "to_y": float(y_new), "vertices": moved}
    return q


GAP_MM = 1.5  # §4.3 step 5 asks for 1.0 between neighbouring toes in rest; the margin covers the subdivision
              # and measure()'s slightly different toe sets (FIXED["toe_gap_mm"] carries it now)
INSIDE_MM = 3.0  # a vertex this near a neighbouring toe's surface, behind it, is inside that toe


def toe_gaps(foot, q, beyond=0.4):
    """{k: the smallest signed distance from toe k's outer vertices to toe k+1's surface} (F, mm; negative
    where a vertex is inside the neighbour, so curled knuckles that cross read as crossing)."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    out = {}
    for k in (1, 2, 3, 4):
        best = None
        for me, other in ((k, k + 1), (k + 1, k)):  # both ways: a curled toe can cross into either neighbour
            A = np.nonzero((foot.w[me] > 0.5) & foot.body)[0]
            T = foot.toe[me]
            t = (q[A] - T["mtp"]) @ T["a"]
            A = A[t > beyond * T["len"]]
            tb = foot.toe_tris[other]
            if not len(A) or not len(tb):
                continue
            tree = BVHTree.FromPolygons(q.tolist(), tb.tolist(), all_triangles=True)
            for i in A.tolist():
                loc, nrm, _, d = tree.find_nearest(Vector(q[i]))
                if loc is None:
                    continue
                # inside the neighbour: behind its nearest face, near it (a toe's faces are an open patch, so
                # a far vertex whose nearest point is on the patch's rim has no meaningful side; F mirrors the
                # right foot's winding)
                if d < INSIDE_MM and (Vector(q[i]) - loc).dot(nrm) * foot.frame.s < -0.5 * d:
                    d = -d  # behind the face itself, not beside one of its edges
                best = d if best is None else min(best, d)
        if best is not None:
            out[k] = best
    return out


def separate_toes(foot, q, gap=GAP_MM, rounds=3, gather=False, bands=None):
    """Where two neighbouring toes come closer than `gap`, the outer one and every toe beyond it turn away
    by the shortfall at their tips (nothing moves at the MTP): the toes stay a set, spaced as real toes in
    a relaxed foot. With gather, toes further apart than `gap` turn toward each other the same way, so the
    lesser toes rest against each other and the hallux, as real toes do. bands gives a pair its own
    [least, most] gap (the hallux standing apart from toes 2-5, which move as a group)."""
    bands = {int(str(p).split("-")[0]): (float(v[0]), float(v[1])) for p, v in (bands or {}).items()}
    for _ in range(rounds + (2 if (gather or bands) else 0)):
        gaps = toe_gaps(foot, q)
        short = {}
        for k, g in gaps.items():
            lo, hi = bands.get(k, (gap, gap if gather else float("inf")))
            if g < lo - 0.05:
                short[k] = lo - g
            elif g > hi + 0.05:
                short[k] = hi - g
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


def nail_size(k, sizes=None):
    """A nail's (width, visible length, free edge), §3.3's or the nail_size option's (the free edge kept)."""
    w, vis, fe = NAILS[k]
    got = (sizes or {}).get(k)
    return (float(got[0]), float(got[1]), fe) if got else (w, vis, fe)


def nail_beds(foot, q, adj, sizes=None):
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
        nw, nvis, nfe = nail_size(k, sizes)
        tw, tl = nw, nvis - nfe  # the bed: the visible length less the free edge
        sa, sb = tl / length, tw / width
        # the patch scales in its own plane; a ring two vertices deep around it follows by half and a quarter
        ring1 = np.setdiff1d(np.unique(np.concatenate([nb[indptr[i]:indptr[i + 1]] for i in P])), P)
        ring2 = np.setdiff1d(np.unique(np.concatenate([nb[indptr[i]:indptr[i + 1]] for i in ring1])), np.r_[P, ring1])
        for rows, share in ((P, 1.0), (ring1, 0.5), (ring2, 0.2)):
            d = q[rows] - c
            q[rows] += share * (((d @ a) * (sa - 1.0))[:, None] * a + ((d @ b) * (sb - 1.0))[:, None] * b)
        # the bed placed so that its plate's free edge ends short of the pulp's tip, as on a real toe (seen
        # from above a rim of skin shows beyond the nail; a free edge past the tip stood off it like a flake)
        mine = (foot.w[k] > 0.5) & foot.body
        ah = np.array([a[0], a[1], 0.0]) / max(np.hypot(a[0], a[1]), 1e-9)  # in plan: the bed tilts down
        reach = float(((q[mine] - c) @ ah).max())
        end = float(((q[P] - c) @ ah).max()) + nfe * float(a @ ah)
        shift = min(0.0, reach - NAIL_TIP_MARGIN[k] - end)
        # the folds go back with the bed, the skin in front of it does not: it is the tip that shows beyond
        q[P] += shift * ah
        for rows, share in ((ring1, 0.6), (ring2, 0.25)):
            along = ((q[rows] - c) @ a) / max(tl / 2.0, 1e-6)
            q[rows] += (share * shift * (1.0 - S.smoothstep(along, 0.3, 0.8)))[:, None] * ah
        foot.nail_shift = getattr(foot, "nail_shift", {})
        foot.nail_shift[k] = round(shift, 2)
        # the bed bent across to the plate's arc (§3.3's transverse radius: 11 mm on the hallux, 4-6 on the
        # lesser toes), its sides down into the lateral grooves: a toe's own dorsum is flatter than its nail;
        # the bed's curve across is read beside its curve along the toe, and a bed curved enough is left
        d = q[P] - c
        u, v, h = d @ b, d @ a, d @ nrm
        coef = np.linalg.lstsq(np.stack([np.ones_like(u), u, v, v * v, u * u], axis=1), h, rcond=None)[0]
        uc = 0.5 * (u.min() + u.max())
        R = NAIL_RADIUS[k]
        drop = R - np.sqrt(R * R - np.minimum(np.abs(u - uc), 0.98 * R) ** 2)
        q[P] -= np.maximum(0.0, drop + coef[4] * (u - uc) ** 2)[:, None] * nrm
        q[P] -= 0.4 * nrm
        # folds: proximal (eponychium) 0.6, lateral 0.45, none at the free edge (the hyponychium): enough over
        # a subdivided 4 mm cage to cover the plate's root and sides where they dive (nails.py)
        d = q[ring1] - c
        along = (d @ a) / max(tl / 2.0, 1e-6)
        lift = np.where(along < -0.6, 0.6, np.where(along > 0.7, 0.0, 0.45))
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
            foot.region_tris = tris
            foot.toe_tris = {k: tris[((foot.w[k] > 0.5) & foot.body)[tris].all(axis=1)] for k in TOES}
            # each quad split both ways: a warped quad's two triangulations differ by a millimetre or two
            # (Blender's own may be either), so contacts are resolved against both
            alt = _region_tris(self.topo, foot.R, len(self.co), both=True)[len(tris):]
            alt = alt[(alt >= 0).all(axis=1)]
            foot.toe_tris_both = {k: [t[((foot.w[k] > 0.5) & foot.body)[t].all(axis=1)] for t in (tris, alt)]
                                  for k in TOES}
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


def _region_tris(topo, rows, n, both=False):
    """Fan triangles of the polygons lying wholly in a region, as region rows (T, 3); with both, each quad's
    other diagonal's two triangles as well."""
    ls, lt, lv = topo
    pos = np.full(n, -1, np.int64)
    pos[rows] = np.arange(len(rows))
    out = []
    for k in range(1, int(lt.max()) - 1):
        ok = lt > k + 1
        tri = np.stack([lv[ls[ok]], lv[ls[ok] + k], lv[ls[ok] + k + 1]], axis=1)
        out.append(pos[tri])
    if both:
        quad = lt == 4
        s = ls[quad]
        out.append(pos[np.stack([lv[s + 1], lv[s + 2], lv[s + 3]], axis=1)])
        out.append(pos[np.stack([lv[s + 1], lv[s + 3], lv[s]], axis=1)])
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
