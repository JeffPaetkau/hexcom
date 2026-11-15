"""Boots, round 1 blockout: a pair of LOWA Zephyr MK2 GTX Hi TF class tactical boots (210 mm outside height,
two-density PU midsole on a rubber outsole, padded collar), built around the rest feet. Notes:
scripts/parts/boots.md.

  "$SGT_BLENDER" -b --python scripts/parts/boots.py [-- --no-render]
  -> cache/parts/boots.blend (Part.Boots: Boot.{L,R}.Upper, .Sole, .Collar), cache/parts/boots.json,
     renders/boots/*.png

Frame: the boot is built in the REST body's frame with its footbed under the rest foot (heel seat 36 mm,
ball seat 24 mm, common.BOOT), so in rest the soles reach below z = 0; round 0's hero pose lifts each foot
onto those seats and the soles land on the floor (checked and reported here).

Method, per side: the foot and ankle skin (up to the rim + 25 mm) is copied and refined, pushed out 6 mm,
the toes pushed forward into a toe box (last = foot + 15 mm), each cross-section across the foot moved to
its convex hull (no toes, no arch hollow on top), the ankle and shaft widened to the measured shaft
ellipses (128 x 100 at h 110 to 138 x 106 at the rim), smoothed, cut at the rim and clamped flat into the
sole at the sole top. The sole is the upper's footprint grown 4 mm, from the sole plane (flat, toe spring
15 mm) up to the visible stack (49 mm at the heel, 23 at the ball). The collar is a padded roll swept round
the rim. Upper and collar take weights from the body (toes merged into the foot); the sole is rigid on
the foot bone.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PART, TAG = "Boot", "boots"
HEEL_SEAT, BALL_SEAT = C.BOOT["heel_seat"], C.BOOT["ball_seat"]
RIM_Z = C.BOOT["rim_z_rest"]                     # 176: rim in the rest frame (212 above the sole)
UPPER_OFF = 5.0                                  # leather 2.0 + lining 1.5 + air 1.5
TOE_ALLOW = 10.0                                 # beyond the 5 mm offset: last 289 for a 274 foot
TOE_SPRING = 15.0
STACK_HEEL, STACK_BALL, STACK_TOE = 49.0, 23.0, 21.0   # visible sole: floor -> rand top (spec 02 §3.1, M)
SIDEWALL = 3.0
SHAFT = [(74.0, (64.0, 50.0)), (122.0, (68.0, 52.0)), (RIM_Z, C.BOOT["shaft_rim_ab"])]   # rest z: (front-back, side)
COLLAR = {"tall": 22.0, "thick": 10.0}
COLOURS = {"leather": "#201e1c", "collar": "#1b1b1c", "midsole": "#262626", "outsole": "#121212"}


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


class FootFrame:
    """Along-foot coordinate s (mm from the heel back, toward the toe), lateral t, and the sole functions."""

    def __init__(self, side):
        lm = C.base_json()["landmarks"]
        self.side = side
        self.heel = np.array(lm[f"heel_{side}"]["rest_mm"])
        toe = np.array(lm[f"toe_{side}"]["rest_mm"])
        ball = (np.array(lm[f"mt1_{side}"]["rest_mm"]) + np.array(lm[f"mt5_{side}"]["rest_mm"])) / 2.0
        u = toe[:2] - self.heel[:2]
        self.length = float(np.linalg.norm(u))
        self.u = np.array([*(u / self.length), 0.0])
        self.t = np.array([-self.u[1], self.u[0], 0.0])           # left of the foot axis
        if (self.t[0] > 0) != (side == "L"):
            self.t = -self.t                                       # t points outward (lateral)
        self.s_ball = float((ball - self.heel)[:2] @ self.u[:2])
        self.s_seat = 30.0
        self.k = (HEEL_SEAT - BALL_SEAT) / (self.s_ball - self.s_seat)

    def s_of(self, P):
        return (np.atleast_2d(P)[:, :2] - self.heel[:2]) @ self.u[:2]

    def t_of(self, P):
        return (np.atleast_2d(P)[:, :2] - self.heel[:2]) @ self.t[:2]

    def z_bottom(self, s, tip):
        s = np.asarray(s, float)
        z = -HEEL_SEAT + self.k * (s - self.s_seat)
        spring = TOE_SPRING * np.clip((s - self.s_ball) / (tip - self.s_ball), 0, 1) ** 2
        return z + spring

    def stack(self, s):
        return np.interp(s, [0.0, 60.0, self.s_ball, self.length + 20], [STACK_HEEL, STACK_HEEL, STACK_BALL, STACK_TOE])

    def z_top(self, s, tip):
        return self.z_bottom(s, tip) + self.stack(s)


def ellipse_r(u, ab):
    a_y, a_x = ab
    return 1.0 / np.sqrt((u[..., 0] / a_x) ** 2 + (u[..., 1] / a_y) ** 2)


def shaft_ab(z):
    zs = [p[0] for p in SHAFT]
    return (np.interp(z, zs, [p[1][0] for p in SHAFT]), np.interp(z, zs, [p[1][1] for p in SHAFT]))


def build_upper(bd, side, ff, bvh0):
    V0 = bd["V"]
    sg = 1.0 if side == "L" else -1.0
    leg = C.weight_sum(bd, C.is_leg)
    keep = bd["in_body"] & (leg > 0.5) & (V0[:, 2] < RIM_Z + 250.0) & (np.sign(V0[:, 0]) == sg)
    V, F, _ = C.submesh(V0, bd["F"], keep)
    V, F = C.bisect(V, F, (0, 0, RIM_Z + 50.0), (0, 0, 1), keep="below")   # MPFB's shin faces are long: cut, not filter
    V, F, N = C.refine_on_skin(V, F, bvh0, cuts=1)
    V1 = V + N * UPPER_OFF
    # toe box: the front pushed forward (and a little up) into the last's toe allowance
    s = ff.s_of(V1)
    ramp = smoothstep(ff.s_ball - 30.0, ff.length, s)
    V1 += np.outer(ramp * TOE_ALLOW, ff.u)
    # cross-sections across the foot to their convex hulls (bridges the toes, fills the top of the arch)
    foot = V1[:, 2] < 95.0
    V1 = C.convexify_along(V1, foot, ff.heel, ff.u, slab=6.0, k=1.0)
    # toe box dome: a thermoplastic toe puff keeps the forefoot domed across, not flat over the toes
    s = ff.s_of(V1)
    tt = ff.t_of(V1)
    fore = smoothstep(ff.s_ball - 40.0, ff.s_ball + 10.0, s)
    for x in np.unique(np.round(s[fore > 0] / 6.0)):
        m = (np.round(s / 6.0) == x) & (fore > 0) & (V1[:, 2] > 12.0)
        if m.sum() < 4:
            continue
        lo, hi = tt[m].min(), tt[m].max()
        q = (tt[m] - (lo + hi) / 2.0) / max((hi - lo) / 2.0, 1.0)
        V1[m, 2] += 7.0 * fore[m] * np.clip(1 - q * q, 0, 1) * smoothstep(12.0, 30.0, V1[m, 2])
    # ankle and shaft: at least the measured shaft ellipse, centred on the leg's section at the rim
    sec = C.leg_section(bd, side, RIM_Z - 5.0, half=12.0)
    c = sec["c"]
    for i in range(len(V1)):
        z = V1[i, 2]
        if z < 40.0:
            continue
        r = V1[i, :2] - c
        rl = np.linalg.norm(r)
        if rl < 1e-6:
            continue
        uu = r / rl
        re = float(ellipse_r(uu[None], shaft_ab(z))[0])
        w = float(smoothstep(40.0, 85.0, z))
        if z > 95.0:
            V1[i, :2] = c + uu * (rl + (re - rl) * w)          # the shaft is the ellipse
        elif rl < re:
            V1[i, :2] = c + uu * (rl + (re - rl) * w)          # low down: only widen to it
    # a clean closed surface from the folded one, then smooth
    V1, F = C.voxel_remesh(V1, F, voxel_mm=4.5)
    V1, F = C.bisect(V1, F, (0, 0, RIM_Z + 30.0), (0, 0, 1), keep="below")     # open the filled top again
    E = C.edges_of(F)
    V1 = C.taubin(V1, E, iters=60, lam=0.5, mu=-0.53, pin=C.boundary_verts(F, len(V1)))
    # rim cut (the filled top, 50 mm higher, goes with it), then the clearance
    V1, F = C.bisect(V1, F, (0, 0, RIM_Z), (0, 0, 1), keep="below")
    V1 = C.push_out(V1, bvh0, 3.5)
    # clamp flat into the sole: nothing below the sole top less 4 mm
    tip = ff.s_of(V1).max()
    zt = ff.z_top(ff.s_of(V1), tip) - 4.0
    # tongue and lace stays: a strip 48 mm wide standing 3.5 mm proud, from the throat up the shaft front
    Nn = C.vertex_normals(V1, F)
    sv, tv = ff.s_of(V1), ff.t_of(V1)
    t_axis = float(ff.t_of(np.array([[*c, 0.0]]))[0])
    band = (1 - smoothstep(20.0, 26.0, np.abs(tv - t_axis))) * smoothstep(95.0, 105.0, sv)         * (1 - smoothstep(170.0, 182.0, sv)) * smoothstep(30.0, 45.0, V1[:, 2])
    band *= (Nn @ np.array([*(-ff.u[:2] * 0 + ff.u[:2]), 0.0]) * 0 + 1.0) * ((Nn[:, 2] > -0.2) & ((Nn[:, :2] @ ff.u[:2]) > -0.2))
    V1 = V1 + Nn * (3.5 * band)[:, None]
    clamped = V1[:, 2] <= zt + 0.5
    V1[:, 2] = np.maximum(V1[:, 2], zt)
    # the flattened floor lies inside the sole: drop its faces (they would make Solidify degenerate)
    F = [f for f in F if not clamped[list(f)].all()]
    V1, F, _ = C.submesh(V1, F, np.ones(len(V1), bool))
    return V1, F, tip


def footprint(V, ff, tip, step=5.0):
    """The upper's outline in plan near the sole top: per station along the foot, the extreme lateral and
    medial points; returns an ordered loop of (s, t) going round."""
    s, t = ff.s_of(V), ff.t_of(V)
    zt = ff.z_top(s, tip)
    low = V[:, 2] < zt + 14.0
    s, t = s[low], t[low]
    st = np.arange(s.min() + 1.0, s.max() - 0.5, step)
    lat, med = [], []
    for x in st:
        m = np.abs(s - x) < step * 0.75
        if m.sum() < 2:
            continue
        lat.append((x, t[m].max()))
        med.append((x, t[m].min()))
    lat, med = np.array(lat), np.array(med)
    ker = np.ones(7) / 7.0
    for ch in (lat, med):                          # smooth the chains: no wobble in the sidewall
        pad = np.concatenate([ch[:1, 1].repeat(3), ch[:, 1], ch[-1:, 1].repeat(3)])
        ch[:, 1] = np.convolve(pad, ker, mode="valid")
    # rounded ends: the last R mm at the toe and heel replaced by half-ellipses
    def arc(chain_lat, chain_med, s_end, R, sdir, n=9):
        keep = (chain_lat[:, 0] - s_end) * sdir < -R
        la, me_ = chain_lat[keep], chain_med[keep]
        p_l, p_m = (la[-1], me_[-1]) if sdir > 0 else (la[0], me_[0])
        cen_t, rad_t = (p_l[1] + p_m[1]) / 2.0, (p_l[1] - p_m[1]) / 2.0
        cs = p_l[0]
        ext = abs(s_end - cs)
        pts = [(cs + sdir * ext * math.sin(math.pi * k / n), cen_t + rad_t * math.cos(math.pi * k / n)) for k in range(1, n)]
        return keep, pts
    keep_t, toe = arc(lat, med, s.max(), 22.0, +1.0)
    lat, med = lat[keep_t], med[keep_t]
    keep_h, heel = arc(lat, med, s.min(), 16.0, -1.0)
    lat, med = lat[keep_h], med[keep_h]
    heel = heel[::-1]
    loop = list(map(tuple, lat)) + toe + list(map(tuple, med[::-1])) + heel
    return np.array(loop)


def st_to_xy(ff, st):
    return ff.heel[:2] + np.outer(st[:, 0], ff.u[:2]) + np.outer(st[:, 1], ff.t[:2])


def build_sole(ff, loop_st, tip):
    """Outsole + midsole as one closed solid: rings from the bottom, 4 mm sidewall grown outward."""
    n = len(loop_st)
    cen_line_t = 0.0
    # outward normals of the plan loop
    P = st_to_xy(ff, loop_st)
    c = P.mean(0)
    nrm = np.zeros_like(P)
    for i in range(n):
        d = P[(i + 1) % n] - P[i - 1]
        nn = np.array([d[1], -d[0]])
        nn /= max(np.linalg.norm(nn), 1e-9)
        if nn @ (P[i] - c) < 0:
            nn = -nn
        nrm[i] = nn
    Pw = P + nrm * SIDEWALL
    s = loop_st[:, 0]
    zb = ff.z_bottom(s, tip)
    zt = ff.z_top(s, tip)
    rings = []
    # bottom inner rings (toward the foot axis), then the outline at the bottom edge, outsole top, top
    axis_xy = ff.heel[:2] + np.outer(s, ff.u[:2]) + cen_line_t
    for f in (0.35, 0.7):
        Q = axis_xy + (Pw - axis_xy) * f
        rings.append(np.column_stack([Q, zb]))
    rings.append(np.column_stack([Pw - nrm * 1.5, zb]))             # bottom edge, slightly bevelled
    rings.append(np.column_stack([Pw, zb + 2.0]))
    rings.append(np.column_stack([Pw, zb + 8.0]))                   # outsole / midsole line
    rings.append(np.column_stack([Pw + nrm * 0.8, zb + 9.0]))
    rings.append(np.column_stack([Pw + nrm * 0.8, zt - 2.0]))
    rings.append(np.column_stack([Pw - nrm * 1.0, zt]))
    V = np.vstack(rings)
    F, mat = [], []
    R = len(rings)
    for r in range(R - 1):
        for i in range(n):
            j = (i + 1) % n
            F.append((r * n + i, r * n + j, (r + 1) * n + j, (r + 1) * n + i))
            mat.append(1 if r < 4 else 0)                            # 1 = outsole, 0 = midsole
    F.append(tuple(range(n - 1, -1, -1)))                            # bottom cap (innermost ring)
    mat.append(1)
    F.append(tuple(range((R - 1) * n, R * n)))                       # top cap
    mat.append(0)
    # orient outward: the bottom cap's normal must point down
    a, b, cc = V[F[-2][0]], V[F[-2][1]], V[F[-2][2]]
    if np.cross(b - a, cc - a)[2] > 0:
        F = [tuple(reversed(f)) for f in F]
    return V, F, mat


def build_collar(V, F):
    bnd = np.nonzero(C.boundary_verts(F, len(V)) & (V[:, 2] > RIM_Z - 4.0))[0]
    c = V[bnd, :2].mean(0)
    ang = np.arctan2(V[bnd, 1] - c[1], V[bnd, 0] - c[0])
    order = bnd[np.argsort(ang)]
    # resample evenly by angle (the bisect's loop can be uneven)
    P0 = V[order]
    a0 = np.sort(ang)
    grid = np.linspace(-math.pi, math.pi, 73)[:-1]
    P = np.column_stack([np.interp(grid, a0, P0[:, k], period=2 * math.pi) for k in range(3)])
    O = np.zeros_like(P)
    O[:, :2] = P[:, :2] - c
    O /= np.maximum(np.linalg.norm(O, axis=1, keepdims=True), 1e-9)
    # thicker roll: the padded collar's section (out, up) from inside the rim round the outside, 10 x 22
    th, tall = COLLAR["thick"], COLLAR["tall"]
    prof = []
    for k in range(12):
        a = 2 * math.pi * k / 12
        prof.append((0.5 * th * math.cos(a) + 1.5, 0.5 * tall * math.sin(a) - 0.5 * tall + 6.0))
    Vc, Fc = C.tube_along(P, O, prof)
    # orient outward
    i0 = 0
    f = Fc[i0]
    nrm = np.cross(Vc[f[1]] - Vc[f[0]], Vc[f[3]] - Vc[f[0]])
    cen = Vc[[f[0], f[1], f[2], f[3]]].mean(0)
    sec_c = P[0] + O[0] * 1.5 + np.array([0, 0, 6.0 - 0.5 * tall])
    if nrm @ (cen - sec_c) < 0:
        Fc = [tuple(reversed(q)) for q in Fc]
    return Vc, Fc


def main():
    import bpy
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    body, rig = C.open_base()
    coll = C.part_collection(PART, "Part.Boots")
    bd = C.body_data(body)
    bvh0 = C.skin_bvh(bd)
    mats = {k: C.flat_material(f"Boot.Mat.{k.title()}", h, 0.5 if k == "leather" else 0.8) for k, h in COLOURS.items()}
    objs, meas = [], {}
    for side in ("L", "R"):
        ff = FootFrame(side)
        Vu, Fu, tip = build_upper(bd, side, ff, bvh0)
        up = C.mesh_object(f"Boot.{side}.Upper", Vu, Fu, coll, mat=mats["leather"])
        up["sgt_clay"] = (0.36, 0.36, 0.37)
        loop = footprint(Vu, ff, tip)
        Vs, Fs, fm = build_sole(ff, loop, tip)
        so = C.mesh_object(f"Boot.{side}.Sole", Vs, Fs, coll, mats=[mats["midsole"], mats["outsole"]], face_mat=fm,
                           smooth=False)
        so["sgt_clay"] = (0.25, 0.25, 0.26)
        Vc, Fc = build_collar(Vu, Fu)
        co = C.mesh_object(f"Boot.{side}.Collar", Vc, Fc, coll, mat=mats["collar"])
        co["sgt_clay"] = (0.30, 0.30, 0.31)
        C.bind(up, body, rig, collapse={"toe*": f"foot.{side}"})
        C.bind(co, body, rig, collapse={"toe*": f"foot.{side}"})
        C.bind(so, body, rig, only=[f"foot.{side}"], collapse={"toe*": f"foot.{side}", f"lowerleg02.{side}": f"foot.{side}"})
        # no Solidify on the upper: it is closed but for the rim, which the collar covers (and the convex-hull
        # step leaves near-coincident vertices in the toe box that make Solidify's offsets explode)
        for o in (up, co, so):
            C.subsurf(o, 1)
        so.modifiers["Subdivision"].levels = so.modifiers["Subdivision"].render_levels = 0
        objs += [up, so, co]
        P = st_to_xy(ff, loop)
        L = float(ff.s_of(np.column_stack([P, np.zeros(len(P))])).ptp()) + 2 * SIDEWALL
        W = float(np.abs(ff.t_of(np.column_stack([P, np.zeros(len(P))]))).max() * 0 +
                  ff.t_of(np.column_stack([P, np.zeros(len(P))])).ptp()) + 2 * SIDEWALL
        meas[side] = {"outsole_length_mm": round(L, 1), "outsole_width_max_mm": round(W, 1),
                      "foot_length_mm": round(ff.length, 1), "s_ball_mm": round(ff.s_ball, 1),
                      "rim_above_sole_bottom_at_heel_mm": round(RIM_Z + HEEL_SEAT, 1),
                      "sole_bottom_rest_z_heel_mm": round(float(ff.z_bottom(ff.s_seat, tip)), 1)}
    rest = C.clearance(objs, body, "rest")
    used = C.apply_hero_pose(rig)
    posed = C.clearance(objs, body, "hero pose")
    floor = {}
    for side in ("L", "R"):
        Vp, _ = C.evaluated_world_mm(bpy.data.objects[f"Boot.{side}.Sole"])
        floor[side] = {"sole_min_z_mm": round(float(Vp[:, 2].min()), 1),
                       "sole_heel_z_mm": round(float(np.percentile(Vp[:, 2], 2)), 1)}
        # how high the bare foot's lowest skin sits above the footbed (posed): the foot's sole vs sole top
    C.say(TAG, "posed soles:", json.dumps(floor))
    C.rest_pose(rig)
    C.say(TAG, json.dumps(meas))
    C.save_part(TAG, coll, {"measure_mm": meas, "posed_soles": floor, "clearance_rest": rest,
                            "clearance_posed": posed, "pose": used})
    if "--no-render" not in args:
        C.render_part(TAG, coll, (0, -40, 90), (700, 420), crops=("ref.boots_feet", "ref.soldier_full"))


if __name__ == "__main__":
    main()
