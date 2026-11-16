"""Boots, round 3: a pair of LOWA Zephyr MK2 GTX Hi TF class tactical boots (210 mm outside height, a
leather and Cordura upper on a two-density PU midsole and a lugged rubber outsole, padded collar, gusseted
tongue, five eyelets and two speed hooks, and the drawing's cuff strap with its ladder-lock and keepers), built
round take 1's real last on take 1's scan-transferred foot (scripts/stages/foot.py). Notes: scripts/parts/boots.md.

  "$SGT_BLENDER" -b --python scripts/parts/boots.py [-- --no-render] [--base FILE] [--tag NAME]
  -> cache/parts/boots.blend (Part.Boots: Sock.{L,R}.Body, Boot.{L,R}.Upper, .Stays, .Tongue, .Collar, .Rand,
     .Sole, .Lugs, .Eyelets, .Hooks, .Laces, .Strap, .Keepers, .Buckle, .Stitches, .Tacks),
     cache/parts/boots.json, cache/parts/boots_lasts.blend (Boot.{L,R}.Last and its markers: the construction
     lasts, kept out of the part so the assembly's clash test never sees the foot inside them), renders/boots/*.png
  --base: the body file (default cache/stages/base.blend; a development copy such as cache/stages/foot_dev.blend);
  --tag: the cache name (default boots).

Round 3 (boots.md §5): take 1's work reused (archive/v1/spec/02_boots.md §4, part 01's sock.py and last.py).
1. The sock (take 1 part 01 §4.10-4.11, stages/foot/sock.py): lofted from section hulls of the rendered foot with
   its nails, relaxed as a membrane 0.3 mm off the skin, ribbed by Geometry Nodes; part of the boots, bound to the rig.
2. The last (part 01 §4.13, stages/foot/last.py): the rest foot loaded (Foot.Contact 1), socked at the loaded
   thickness, the allowances (ball sides +2, instep +2, heel sides +1), the insole plane, the toe box 15 mm ahead
   of the standing socked toe, 12 degrees of toe spring about the 1st-5th metatarsal heads' line.
3. The upper's outer form is that last grown 3.5 mm (2.0 leather + 1.5 lining; take 1 spec 02 §4.4), 9.5 over the
   ankle padding, with the shaft ellipses of the drawing (138 x 106 at the rim) where they are bigger.
4. Detail laid where the boot flexes and loads (spec 02 §4.15): seeded flex folds along the metatarsal heads' line
   (different on each boot), ankle-break folds, padding over the malleoli, soft Cordura wrinkles; the throat's
   foot (E1) at h 79 (round 6: the lacing runs on down the vamp to about 125 mm behind the toe; at h 86 it stopped
   150 mm behind it and the bare vamp read as a galosh), the leather quarter's edge rising toward the throat, a
   stitched leather mudguard falling from the heel to the ball, the toe cap 1.6 mm proud.
5. The library's hardware, webbing and stitches (scripts/lib/gear_hardware, gear_webbing, gn_stitches, sweep):
   rolled eyelets, plate speed hooks, the cuff strap round the shaft at h 158 through a ladder-lock at phi 150
   and two leather keepers at phi +-72, stitch rows on the toe cap, the counter, the stays and the collar.

Frame: the boot is built in the REST body's frame with its footbed under the rest foot; the sole plane is the one
the hero pose seats the foot on (pose_solve.py: the heel landmark at 36, the 1st and 5th metatarsal heads at 24,
each at its rest height), so in rest the soles reach below z = 0 and in the pose they land on the floor.
Coordinates along the foot: s (mm from the heel landmark toward the toe landmark), t (lateral), z (rest).
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
UPPER_OFF = 3.5                                  # round 3: the last -> upper outer surface: leather 2.0 + lining 1.5
PAD_OFF = 6.0                                    # the ankle padding's foam over the last above h 120 (spec 02 §3.2)
TOE_ALLOW = 2.0                                  # the last carries the toe room (15 mm ahead of the standing socked toe);
HEEL_ALLOW = 2.5                                 # these few mm let the ends round off (a slab of points is flat-backed)
NOSE, HEEL_END = 52.0, 38.0                      # lengths of the rounded toe and heel ends (round 9: nose 44 -> 40,
                                                 # with a blunter, higher nose: NOSE_H, NOSE_EXP)
NOSE_H, NOSE_EXP, NOSE_PLAN = 24.0, 0.42, 0.80   # round 9 (critics r8 m4, "sneaker": a low pointed wedge toe): the nose
                                                 # section keeps NOSE_H mm of height at the very tip (was 12) and rounds
                                                 # with e ** NOSE_EXP in profile (0.5), e ** NOSE_PLAN in plan (0.6)
TOE_PUFF = 6.0                                   # round 9: the toe box raised this much ahead of the ball (a Zephyr-class
                                                 # boot's high rounded toe box; spec 02 §3.1 internal 73 x 27 at the hallux)
ARCH_H = 6.0                                     # round 9: the outsole's waist recessed this much between heel breast and
                                                 # forefoot (the drawn sole shows a heel block and a gap under the arch)
SOCK_CLEAR = 4.2                                 # round 10: the upper's outer face this far off the skin at least
                                                 # (sock 0.3 + its 2.2 outward Solidify + the upper's 1.6 inward)
UPPER_W_MAX = 119.0                              # round 10: the upper's widest section (mm; was 128.6); 113 cut into the
                                                 # 5th metatarsal head and robust_push left a lump there
NOSE_RELAX = 16.0                                # round 10: the nose's sections may lie this much (x its share of the
                                                 # nose) inside take 1's square toe box, so the toe rounds in plan
TOE_ROUND, TOE_RELAX = 0.40, 12.0                 # round 10: the forefoot's sections round over above 45 % of their
                                                 # height, up to 6 mm inside take 1's square toe-box corners
SEC_N = 2.7                                      # superellipse exponent of the arches (2 = ellipse)
TOE_SPRING = 15.0
STACK_HEEL, STACK_BALL, STACK_TOE = 40.0, 21.0, 19.0   # floor -> midsole stripe top; the rand rises above it
RAND = {"side": 12.0, "heel": 16.0, "toe": 14.0, "proud": 2.0, "lip": 0.8, "toe_exp": 4.0}   # round 10: a low strip
                                                 # (round 9: side 13, toe 26, proud 3.2, lip 1.4 with cos^10 at the toe)
RUBBER_TOE = (60.0, 30.0, 1.8)                   # round 10 (D9, D10: a squared bumper wall): the rubber toe cap is an
                                                 # overlay moulded on the toe box itself, RUBBER_TOE[0] mm back from the
                                                 # tip, its top edge RUBBER_TOE[1] mm over the stripe at the tip curving
                                                 # down into the rand along the sides, RUBBER_TOE[2] mm proud; the rand is
                                                 # a low strip (round 9: a 26 mm wall with a lip, read as a slab)
LUG, SIDEWALL, CUP = 5.0, 1.5, 9.0               # lug height, sole grown past the upper, outsole cup wall (round 9:
                                                 # cup 6 -> 9, a deeper lug wall; the teeth wrap TOOTH_WRAP up it;
                                                 # round 10: sidewall 3 -> 1.5, the sole 116-125 wide as a real one)
TOOTH_WRAP, TOOTH_PROUD = 8.0, 1.4               # round 9: perimeter teeth wrap 8 mm up the sidewall (3); round 10: 1.4
                                                 # proud (round 9: 2.6)
SHAFT = [(74.0, (64.0, 50.0)), (122.0, (68.0, 52.0)), (RIM_Z, C.BOOT["shaft_rim_ab"])]   # rest z: (front-back, side)
SHAFT_ZLO = -60.0                                # the shaft runs down into the sole (tapered), so no ledge
CROWN_R = 9.0                                    # the soft crown's radius across the instep (mm)
K_UNION = 16.0                                   # smooth-union radius (mm) where shaft meets instep
NOTCH = 6.0                                      # Achilles notch at the back of the rim
COLLAR = {"tall": 22.0, "thick": 8.0}
LACE_PITCH, LACE_TOP = 22.5, 5.0                 # eyelet pitch along the throat, top hook below the rim
E1_DS = 12.0                                     # round 10: E1 no further forward than s_ball + 12 (about 64 mm behind
                                                 # the toe tip; round 9: s_ball - 5, 80 behind)
E1_H = 62.0                                      # round 6: the lowest eyelet's height (86 put E1 151 mm behind the toe and
                                                 # left a 90 mm bare vamp: the critics' galosh; the drawn E1 is ~137 behind)
                                                 # round 9: 79 -> 72 (with the throat line to the ball + 50): lower on the raised toe box (critics r8 m4);
                                                 # 64 with the line to the ball + 62 ran the stays and laces off the nose
QUARTER = (98.0, 14.0, 60.0)                     # round 6: the leather quarter's top edge, h 98 at the back rising 14 mm over
                                                 # 60 mm toward the throat (a straight h 98 read as a hard collar seam)
MUD = (92.0, 45.0, 1.0)                          # round 6: the leather mudguard's top edge, h 92 behind falling to 45 at the
                                                 # ball, standing 1.0 proud (the drawn boot's diagonal panel line)
VAMP = (12.0, 0.95)                              # round 10: vamp_s(): s_ball - 12 at h 50, slanting back 0.95 mm per mm up
SUEDE = {"albedo_hex": "#4a4642", "rough": 0.90, "rough_span": 0.08, "normal_strength": 0.12,
         "polish__rough": 0.90, "polish__coat": 0.0, "sheen_mottle__rough": 0.02, "edge__amount": 0.3,
         "dust__amount": 1.4}
                                                 # round 10: the suede vamp and mudguard (Leather.Boot.FullGrain made
                                                 # matte, its grain flattened, no polish): Boot.Mat.Suede
TOECAP_LIFT = 1.6                                # round 6: the toe cap's step over the vamp (0.8 did not read in profile)
GAP = (30.0, 44.0)                               # throat gap between the stays at E1 and at the top
STAY_W, STAY_PROUD = 22.0, 2.4
LACE_R = 2.0
COLOURS = {"leather": "#201e1c", "cordura": "#1c1b1a", "suede": "#2a2826", "collar": "#1b1b1c", "midsole": "#262a30",
           "outsole": "#121212", "rubber": "#151515", "metal": "#3c3937", "lace": "#333129"}
CLAY = {"Upper": (0.36, 0.36, 0.37), "Stays": (0.30, 0.30, 0.31), "Tongue": (0.33, 0.33, 0.34),
        "Collar": (0.30, 0.30, 0.31), "Rand": (0.22, 0.22, 0.23), "Sole": (0.25, 0.25, 0.26),
        "Lugs": (0.20, 0.20, 0.21), "Eyelets": (0.55, 0.55, 0.56), "Laces": (0.42, 0.40, 0.38)}


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def gauss1d(x, sigma):
    if sigma <= 0:
        return x
    r = int(math.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    xp = np.concatenate([np.repeat(x[:1], r), x, np.repeat(x[-1:], r)])
    return np.convolve(xp, k, mode="valid")


def envelope(req, sigma, iters=12):
    """The smallest smooth curve above req: repeatedly smooth and lift back onto req."""
    x = req.copy()
    for _ in range(iters):
        x = np.maximum(req, gauss1d(x, sigma))
    return gauss1d(x, sigma * 0.5)


class FootFrame:
    """Along-foot coordinate s (mm from the heel back, toward the toe), lateral t, and the sole functions."""

    LANDMARKS = None   # set by main(): stages/foot/marks.foot_landmarks(body), the points the pose seats

    def __init__(self, side):
        lm = FootFrame.LANDMARKS or C.base_json()["landmarks"]
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
        # round 3: the sole plane is the pose's (pose_solve seats the heel landmark itself at HEEL_SEAT and the
        # metatarsal heads at BALL_SEAT); round 2 put HEEL_SEAT 30 mm ahead of it, which sank the posed soles 3 mm
        self.s_seat = 0.0
        self.k = (HEEL_SEAT - BALL_SEAT) / (self.s_ball - self.s_seat)
        self.tip = self.length + 20.0                              # set by the last

    def s_of(self, P):
        return (np.atleast_2d(P)[:, :2] - self.heel[:2]) @ self.u[:2]

    def t_of(self, P):
        return (np.atleast_2d(P)[:, :2] - self.heel[:2]) @ self.t[:2]

    def xyz(self, s, t, z):
        s, t, z = np.broadcast_arrays(np.asarray(s, float), np.asarray(t, float), np.asarray(z, float))
        xy = self.heel[:2] + s[..., None] * self.u[:2] + t[..., None] * self.t[:2]
        return np.concatenate([xy, z[..., None]], -1)

    def z_bottom(self, s):
        s = np.asarray(s, float)
        z = -HEEL_SEAT + self.k * (s - self.s_seat)
        spring = TOE_SPRING * np.clip((s - self.s_ball) / (self.tip - self.s_ball), 0, 1) ** 2
        return z + spring

    def arch(self, s):
        """Round 9: the outsole's waist recess (0 under the heel block and the forefoot)."""
        s = np.asarray(s, float)
        return ARCH_H * smoothstep(68.0, 84.0, s) * smoothstep(self.s_ball - 52.0, self.s_ball - 72.0, s)

    def stack(self, s):
        return np.interp(s, [0.0, 60.0, self.s_ball, self.tip], [STACK_HEEL, STACK_HEEL, STACK_BALL, STACK_TOE])

    def z_top(self, s):
        return self.z_bottom(s) + self.stack(s)

    def h_of(self, P):
        """Height above the floor in the pose, near enough: above the sole plane (no toe spring)."""
        s = np.clip(self.s_of(P), -20.0, self.s_ball)
        return np.atleast_2d(P)[:, 2] - (-HEEL_SEAT + self.k * (s - self.s_seat))


# --------------------------------------------------------------------------- the last and the shaft


class Last:
    """The upper's outer form as an implicit field (negative inside), fitted to the offset skin."""

    def __init__(self, ff, cloud, log):
        self.ff = ff
        s, t, z = ff.s_of(cloud), ff.t_of(cloud), cloud[:, 2]
        # ---- the foot: per station across the foot, the convex hull of the offset skin; its half widths
        # (medial and lateral of the crown) per height band; the ankle above 60 mm behind the instep belongs
        # to the shaft
        zl_all = 60.0 + 50.0 * smoothstep(95.0, 140.0, s)
        foot = z < zl_all
        sf, tf, zf, zlim = s[foot], t[foot], z[foot], zl_all[foot]
        self.s_back = float(sf.min() - HEEL_ALLOW)
        self.s_tip = float(sf.max() + TOE_ALLOW)
        ff.tip = self.s_tip
        st = np.arange(self.s_back, self.s_tip + 0.1, 4.0)
        zb = ff.z_top(st) - 8.0
        zk = np.arange(-12.0, 150.1, 3.0)
        WM, WL = np.zeros((len(st), len(zk))), np.zeros((len(st), len(zk)))
        tc = np.full(len(st), np.nan)
        for i, x in enumerate(st):
            m = np.abs(sf - x) < 3.0
            if m.sum() < 4:
                continue
            ti, zi = tf[m], zf[m] - zb[i]
            pts = np.vstack([np.column_stack([ti, zi]), [[ti.min(), zk[0]], [ti.max(), zk[0]]]])
            H = C.hull2d(pts)
            capped = (zf[m] > zlim[m] - 3.0).any()
            c = 0.5 * (ti.min() + ti.max()) if capped else float(H[np.argmax(H[:, 1]), 0])
            tc[i] = c
            for k, zz in enumerate(zk):
                iv = hull_interval(H, zz)
                if iv is not None:
                    WM[i, k], WL[i, k] = max(c - iv[0], 0.0), max(iv[1] - c, 0.0)
        have = ~np.isnan(tc)
        tc = np.interp(st, st[have], tc[have])
        for k in range(len(zk)):
            WM[~have, k] = np.interp(st[~have], st[have], WM[have, k])
            WL[~have, k] = np.interp(st[~have], st[have], WL[have, k])
        WM_req, WL_req = WM.copy(), WL.copy()
        def top_of(Wm, Wl):
            w = np.maximum(Wm, Wl)
            k = np.nonzero(w > 1.5)[0]
            if not len(k):
                return float(zk[0])
            k = int(k.max())
            if k + 1 >= len(zk):
                return float(zk[-1])
            return float(zk[k] + (zk[k + 1] - zk[k]) * (w[k] - 1.5) / max(w[k] - w[k + 1], 1e-6))
        # the rounded toe: the nose station's section shrunk elliptically in plan and squashed in profile
        sn = self.s_tip - NOSE
        i_n = int(np.searchsorted(st, sn))
        H0 = max(top_of(WM[j], WL[j]) for j in range(max(0, i_n - 3), i_n + 1))
        jn = max(range(max(0, i_n - 3), i_n + 1), key=lambda j: WM[j, 0] + WL[j, 0])
        for i in range(i_n, len(st)):
            q = min(max((st[i] - sn) / NOSE, 0.0), 1.0)
            e = math.sqrt(max(1 - q * q, 0.0))
            Hn = NOSE_H + (H0 + 3.0 - NOSE_H) * e ** NOSE_EXP   # round 3: a domed toe puff (was e ** 1.1, a wedge);
                                                                # round 9: higher and blunter (12, e ** 0.5)
            f = max(Hn - zk[0], 1.0) / max(H0 - zk[0], 1.0)
            zz = zk[0] + (zk - zk[0]) / f
            # round 10: up to NOSE_RELAX mm inside take 1's last there (its toe box is a stretched sock, square in plan,
            # whose corners ahead of the toes are empty: the nose kept them and the toe read as a square slab, D9, D10)
            WM[i] = np.maximum(WM_req[i] - NOSE_RELAX * q, np.interp(zz, zk, WM[jn], right=0.0) * e ** NOSE_PLAN)
            WL[i] = np.maximum(WL_req[i] - NOSE_RELAX * q, np.interp(zz, zk, WL[jn], right=0.0) * e ** NOSE_PLAN)
            if not have[i]:
                tc[i] = tc[i_n]
        # the rounded heel: half-ellipse in plan
        sh = self.s_back + HEEL_END
        i_h = int(np.searchsorted(st, sh))
        for i in range(0, i_h):
            q = min(max((sh - st[i]) / HEEL_END, 0.0), 1.0)
            e = math.sqrt(max(1 - q * q, 0.0))
            WM[i] = np.maximum(WM_req[i], WM[i_h] * e)
            WL[i] = np.maximum(WL_req[i], WL[i_h] * e)
        # smooth along the foot in each section's own height fraction (eta = 0 at the base, 1 at the top), so
        # a tall instep never lifts the toe box: the top line H(s) and the widths at each eta get an upper
        # envelope (nothing of the toes or the arch shows through); a section's widths never grow upward, so
        # a higher top keeps every point inside
        H_req = np.array([top_of(WM[i], WL[i]) for i in range(len(st))]) + 1.0
        H_req += TOE_PUFF * smoothstep(ff.s_ball + 5.0, ff.s_ball + 45.0, st)   # round 9: the high toe box
        eta = np.linspace(0.0, 1.0, 41)
        EM, EL = np.zeros((len(st), len(eta))), np.zeros((len(st), len(eta)))
        for i in range(len(st)):
            zz = zk[0] + eta * (H_req[i] - zk[0])
            EM[i] = np.interp(zz, zk, WM[i])
            EL[i] = np.interp(zz, zk, WL[i])
        H = envelope(H_req, 2.5, iters=6)
        H[-1] = H_req[-1]
        for j in range(len(eta)):
            EM[:, j] = envelope(EM[:, j], 3.0, iters=6)
            EL[:, j] = envelope(EL[:, j], 3.0, iters=6)
        EM[:, -1] = EL[:, -1] = 0.0                       # the crown closes at the top
        EM[-1] = EL[-1] = 0.0
        for i in range(len(st)):                          # never wider higher up
            EM[i] = np.minimum.accumulate(EM[i])
            EL[i] = np.minimum.accumulate(EL[i])
        # round 10 (critics r9 m1, D9, D10: a galosh with a long flat wedge toe and a squared bumper; the sole 141-147
        # wide against a real 116-125): (1) no station of the upper wider than UPPER_W_MAX (the cloud is take 1's last
        # grown 3.5 mm, whose forefoot hull reached 128; the skin is held 2.5 mm inside by robust_push in main());
        # (2) the forefoot sections round over to the crown above TOE_ROUND of their height (an elliptical shoulder,
        # the toe box domed across instead of flat-topped and square-cornered), cutting at most TOE_RELAX mm into
        # take 1's square toe-box corners
        for i in range(len(st)):
            wmax = EM[i, 0] + EL[i, 0]
            if wmax > UPPER_W_MAX:
                f = UPPER_W_MAX / wmax
                EM[i] *= f
                EL[i] *= f
            k = smoothstep(ff.s_ball - 40.0, ff.s_ball + 5.0, st[i])
            if k <= 0.0:
                continue
            zz = zk[0] + eta * (H[i] - zk[0])
            rm = np.interp(zz, zk, WM_req[i]) - TOE_RELAX
            rl = np.interp(zz, zk, WL_req[i]) - TOE_RELAX
            x = np.clip((eta - TOE_ROUND) / (1.0 - TOE_ROUND), 0.0, 1.0)
            ell = np.sqrt(np.maximum(1.0 - x * x, 0.0))
            EM[i] = np.maximum(np.minimum(rm, EM[i]), (1 - k) * EM[i] + k * np.minimum(EM[i], EM[i, 0] * ell))
            EL[i] = np.maximum(np.minimum(rl, EL[i]), (1 - k) * EL[i] + k * np.minimum(EL[i], EL[i, 0] * ell))
        # round 3: the smoothing along the foot and the never-wider rule carried the heel's full width to its very
        # back (a flat-backed box, the sole's heel square in plan): the rear HEEL_END mm are capped again to a
        # half-ellipse in plan, never inside what the last requires at that height fraction
        EMr, ELr = np.zeros_like(EM), np.zeros_like(EL)
        for i in range(len(st)):
            zz = zk[0] + eta * (H[i] - zk[0])
            EMr[i] = np.interp(zz, zk, WM_req[i])
            ELr[i] = np.interp(zz, zk, WL_req[i])
        for i in range(0, i_h):
            q = min(max((sh - st[i]) / HEEL_END, 0.0), 1.0)
            e = math.sqrt(max(1 - q * q, 0.0)) ** 0.85
            EM[i] = np.maximum(EMr[i], np.minimum(EM[i], EM[i_h] * e))
            EL[i] = np.maximum(ELr[i], np.minimum(EL[i], EL[i_h] * e))
        self.st, self.zb, self.eta, self.EM, self.EL = st, zb, eta, EM, EL
        self.tc = gauss1d(tc, 3.0)
        self.h = H
        self.w = 0.5 * (EM[:, 0] + EL[:, 0])
        self.wm, self.wl = EM.max(1), EL.max(1)
        # ---- the shaft: horizontal ellipses centred on the leg, in the foot frame (a along s, b along t)
        zs = np.arange(SHAFT_ZLO - 30.0, RIM_Z + 40.1, 5.0)
        cs, ct = np.full(len(zs), np.nan), np.full(len(zs), np.nan)
        for i, zz in enumerate(zs):
            m = (np.abs(z - zz) < 4.0) & (z > 78.0)
            if m.sum() >= 6:
                cs[i], ct[i] = 0.5 * (s[m].min() + s[m].max()), 0.5 * (t[m].min() + t[m].max())
        ok = ~np.isnan(cs)
        A, Bc = np.polyfit(zs[ok], cs[ok], 1), np.polyfit(zs[ok], ct[ok], 1)   # the shin is straight here
        cs, ct = np.polyval(A, zs), np.polyval(Bc, zs)
        a = np.interp(zs, [p[0] for p in SHAFT], [p[1][0] for p in SHAFT])
        b = np.interp(zs, [p[0] for p in SHAFT], [p[1][1] for p in SHAFT])
        taper = 1.0 - 0.22 * smoothstep(96.0, 40.0, zs)        # the shaft narrows into the heel counter
        a, b = a * taper, b * taper
        for i, zz in enumerate(zs):
            m = (np.abs(z - zz) < 4.0) & (z > 56.0) & ((z > 100.0) | (s < 100.0))   # not the instep or the foot
            if m.sum() >= 3:
                rho = np.sqrt(((s[m] - cs[i]) / a[i]) ** 2 + ((t[m] - ct[i]) / b[i]) ** 2).max()
                if rho > 1.0:
                    a[i] *= rho
                    b[i] *= rho
        self.zs, self.cs, self.ct = zs, cs, ct
        self.a, self.b = envelope(a, 2.0), envelope(b, 2.0)
        i_r = int(np.argmin(np.abs(zs - RIM_Z)))
        self.rim_c = np.array([cs[i_r], ct[i_r]])
        wid = self.wm + self.wl
        iw = int(np.argmax(wid))
        log("width/top z every 20 mm: " + " ".join(f"{x:.0f}:{np.interp(x, st, wid):.0f}/{np.interp(x, st, zb + self.h):.0f}"
                                                for x in range(0, 290, 20)))
        log(f"last {ff.side}: s {self.s_back:.1f}..{self.s_tip:.1f} (upper length {self.s_tip - self.s_back:.1f}); "
            f"widest {wid[iw]:.1f} at s {st[iw]:.0f}; shaft at the rim "
            f"{2 * self.a[i_r]:.0f} x {2 * self.b[i_r]:.0f}, centre s {cs[i_r]:.1f} t {ct[i_r]:.1f}")

    # fields (P: (n, 3) rest mm) ---------------------------------------------------------------------
    def foot_field(self, s, t, z):
        st, eta = self.st, self.eta
        fi = np.clip((s - st[0]) / (st[1] - st[0]), 0, len(st) - 1.001)
        i0 = fi.astype(int)
        wi = fi - i0
        zb = np.interp(s, st, self.zb)
        H = np.interp(s, st, self.h)
        e = (z - zb + 12.0) / np.maximum(H + 12.0, 1.0)
        fk = np.clip(e / (eta[1] - eta[0]), 0, len(eta) - 1.001)
        k0 = fk.astype(int)
        wk = fk - k0

        def bil(W):
            return ((W[i0, k0] * (1 - wk) + W[i0, k0 + 1] * wk) * (1 - wi)
                    + (W[i0 + 1, k0] * (1 - wk) + W[i0 + 1, k0 + 1] * wk) * wi)
        tc = np.interp(s, st, self.tc)
        W = np.where(t < tc, bil(self.EM), bil(self.EL))
        # a soft |t - tc| (round 3): with the plain absolute value the sections' crowns met in a sharp ridge along the
        # instep, whose flipping normal threw the throat's stays and laces off to one side
        dt = (t - tc) * np.tanh((t - tc) / CROWN_R)
        d = np.maximum(dt - W, z - zb - np.interp(s, st, self.h))
        return np.maximum(d, np.maximum(self.s_back - s, s - self.s_tip))

    def shaft_field(self, s, t, z):
        zc = np.clip(z, self.zs[0], self.zs[-1])
        cs, ct = np.interp(zc, self.zs, self.cs), np.interp(zc, self.zs, self.ct)
        a, b = np.interp(zc, self.zs, self.a), np.interp(zc, self.zs, self.b)
        rho = np.sqrt(((s - cs) / a) ** 2 + ((t - ct) / b) ** 2)
        return np.maximum((rho - 1.0) * np.minimum(a, b), SHAFT_ZLO - z)

    def base(self, P):
        P = np.atleast_2d(P)
        s, t, z = self.ff.s_of(P), self.ff.t_of(P), P[:, 2]
        return smin(self.foot_field(s, t, z), self.shaft_field(s, t, z), K_UNION)

    def rim_z(self, P):
        s, t = self.ff.s_of(P), self.ff.t_of(P)
        ang = np.arctan2(t - self.rim_c[1], s - self.rim_c[0])      # 0 = front (toward the toe), pi = back
        back = np.clip(-np.cos(ang), 0, 1) ** 6
        return RIM_Z - NOTCH * back

    def z_cut(self, P):
        return self.ff.z_top(self.ff.s_of(P)) - 4.0

    def field(self, P):
        P = np.atleast_2d(P)
        d = self.base(P)
        d = np.maximum(d, P[:, 2] - self.rim_z(P))
        return np.maximum(d, self.z_cut(P) - P[:, 2])

    def normal(self, P, f=None, h=0.3):
        f = f or self.base
        g = np.stack([f(P + e) - f(P - e) for e in np.eye(3) * h], -1)
        return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)

    def cast(self, O, D, f=None, far=420.0, step=1.5):
        """First exit of rays O + r D from the inside (march, then bisect)."""
        f = f or self.field
        O, D = np.broadcast_arrays(np.atleast_2d(np.asarray(O, float)), np.atleast_2d(np.asarray(D, float)))
        n = len(D)
        lo = np.zeros(n)
        hi = np.full(n, far)
        done = np.zeros(n, bool)
        r = 0.0
        while r < far and not done.all():
            r += step
            idx = np.nonzero(~done)[0]
            out = f(O[idx] + D[idx] * r) > 0.0
            hit = idx[out]
            hi[hit] = r
            lo[hit] = r - step
            done[hit] = True
        for _ in range(16):
            mid = 0.5 * (lo + hi)
            inside = f(O + D * mid[:, None]) < 0.0
            lo, hi = np.where(inside, mid, lo), np.where(inside, hi, mid)
        return O + D * (0.5 * (lo + hi))[:, None], done


def hull_interval(H, y):
    """The x interval where the horizontal line at y crosses the convex polygon H, or None."""
    xs = []
    n = len(H)
    for i in range(n):
        (x1, y1), (x2, y2) = H[i], H[(i + 1) % n]
        if (y1 - y) * (y2 - y) <= 0 and y1 != y2:
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        elif y1 == y == y2:
            xs += [x1, x2]
    return (min(xs), max(xs)) if xs else None


# --------------------------------------------------------------------------- the sock and the last (take 1 part 01)

SOCK_LAST_DOC = ("take 1 part 01 (archive/v1/scripts/parts/01_foot_ankle_sock.py stages sock and last), on "
                 "scripts/stages/foot/sock.py and last.py")


def _joint_cubes(body, side, co_world):
    """{cube ("toe-1-1", ...): world mm} of one side's MakeHuman joint cubes on the rest body with the foot."""
    from lib import sculpt as S
    pre = "joint-l-" if side == "L" else "joint-r-"
    names = [g.name for g in body.vertex_groups if g.name.startswith(pre + "toe-") or g.name == pre + "ankle"]
    W = S.group_weights_many(body, names)
    return {n[len(pre):]: co_world[W[n] > 0.5].mean(axis=0) for n in names if (W[n] > 0.5).any()}


def _toe_line(m, ix, f, side, cubes_f):
    co = m.co * 1000.0
    tips = {}
    for k in (1, 5):
        q = f.to_f(co[ix.toe[side][k]])
        tips[k] = q[np.argmin(q[:, 1])]
    return {"mtp1": tuple(cubes_f["toe-1-1"][:2]), "mtp5": tuple(cubes_f["toe-5-1"][:2]),
            "tip1": tuple(tips[1][:2]), "tip5": tuple(tips[5][:2])}


def _ball_points(m, ix, f, side, cubes_f):
    """The 1st metatarsal head's medial and the 5th's lateral extreme (F, z 5-40) across the MTP joint cubes."""
    q = f.to_f(m.co[ix.region[side]] * 1000.0)
    q = q[(q[:, 2] > 5.0) & (q[:, 2] < 40.0)]
    out = []
    for name, sign in (("toe-1-1", -1.0), ("toe-5-1", 1.0)):
        y = cubes_f[name][1]
        sl = q[np.abs(q[:, 1] - y) < 5.0]
        p = sl[np.argmax(sign * sl[:, 0])]
        out.append(np.array([p[0], y, p[2]]))
    return out[0], out[1]


def build_socks_and_lasts(body, rig, coll, say):
    """Take 1's sock and last on this body (its Foot.Contact key, Foot.NailBed groups and nail plates come from
    scripts/stages/foot.py). The socks go into the part (bound to the rig by main); the lasts are returned (world mm
    grids, faces, markers) and written to their own cache by main(). Returns ({side: record}, the knit group)."""
    import bpy
    from lib import sculpt as S
    from lib import materials as M
    from stages.foot import footmetrics as fm, sock as SK, last as LS
    if body.data.shape_keys is None or "Foot.Contact" not in body.data.shape_keys.key_blocks:
        raise RuntimeError("Body.Mesh has no Foot.Contact: the body needs scripts/stages/foot.py (base.py runs it)")
    fm._INDEX.clear()
    m = fm.read(body)
    ix = fm.index(body, m)
    rest = S.mix(body, exclude=("Foot.Contact",)) * 1000.0
    kb = body.data.shape_keys.key_blocks["Foot.Contact"]
    old = kb.value
    kb.value = 1.0
    loaded = S.mix(body) * 1000.0
    kb.value = old
    beds = S.group_weights_many(body, [f"Foot.NailBed.{k}" for k in range(1, 6)])
    group = SK.knit_group()
    out = {}
    for side in ("L", "R"):
        f = fm.frame(m, ix, side)
        plates = [bpy.data.objects[n] for n in (f"Foot.{side}.Nail.{k}" for k in range(1, 6)) if n in bpy.data.objects]
        cubes = {k: f.to_f(v) for k, v in _joint_cubes(body, side, rest).items()}
        toe = _toe_line(m, ix, f, side, cubes)
        L = fm.foot(m, ix, side, toes=False)["foot_length"]
        # the sock: the rest foot's rendered surface with its nails, a membrane 0.3 mm off
        V, T = SK.skin_read(body, f, 0.0, plates)
        res = SK.make(V, T, toe, L)
        name = f"Sock.{side}.Body"
        sob = bpy.data.objects.new(name, SK.build_mesh(name, res["inner"], f))
        coll.objects.link(sob)
        groups = {f"sock_{k}": v for k, v in res["regions"].items()}
        groups["sock_thickness"] = res["thickness"] / SK.T_MAX
        SK.set_groups(sob, groups)
        try:
            sob.data.materials.clear()
            M.assign(sob, "Knit.Sock.WoolNylon")
            for g in ("sock_heel", "sock_toe"):
                if sob.vertex_groups.get(g) is not None:
                    M.assign(sob, "Knit.Sock.WoolNylon.Reinforced", faces=g)
        except Exception as e:  # noqa: BLE001
            say(f"{side}: sock knit material failed ({type(e).__name__}: {e})")
        sob["sgt_clay"] = (0.55, 0.50, 0.42)
        sob["doc"] = "take 1 spec 01 §4.11: the sock's inner surface 0.3 mm off the skin; Solidify, Subdivision, Knit"
        # the last: the loaded foot (Foot.Contact 1), its nails moved with their toes, socked at the loaded thickness
        shift = LS.nail_shift(body, f, side, rest, loaded, beds)
        V, T = SK.skin_read(body, f, 1.0, plates, shift)
        tree = SK.bvh(V, T)
        b1, b5 = _ball_points(m, ix, f, side, cubes)
        z_b = LS.insole_z()
        sts, corner = SK.stations(V, top_z=LS.COLLAR_Z, fine_from=toe["tip5"][1] + 10.0)

        def off(G0, N0, kept, b1=b1, b5=b5, toe=toe, L=L):
            reg = SK.regions(G0, N0, L, toe, float(G0[..., 1].max()))
            t_ = SK.thickness(reg, loaded=True)
            a = LS.regions(G0, N0, L, float(0.5 * (b1[1] + b5[1])))
            return SK.OFFSET_MM + LS.FACET_MM + t_ + LS.ALLOW["ball_side"] * a["ball"] + \
                LS.ALLOW["instep"] * a["instep"] + LS.ALLOW["heel_side"] * a["heel"]

        sk_front = LS.socked_toe_y(V)
        G, kept, info = LS.build(V, T, sts, tree, off, sk_front - LS.TOE_ALLOWANCE, b1, b5, z_b,
                                 taper_from=toe["tip5"][1] + 10.0)
        P = G.reshape(-1, 3)
        tip, pt = P[np.argmin(P[:, 1])], P[np.argmax(P[:, 1])]
        spring = LS.spring_angle(P[P[:, 2] < z_b + 25.0], b1, b5, z_b)
        bl = 0.5 * (b1[1] + b5[1])
        out[side] = {"G_f": G, "G_w": f.to_w(G), "N_w": f.vec_to_w(SK.grid_normals(G)), "frame": f,
                     "faces": LS.faces(G.shape[0], SK.N_AROUND), "insole_z": z_b,
                     "markers_f": {"Pternion": [pt[0], pt[1], z_b], "Ball1": [b1[0], b1[1], z_b],
                                   "Ball5": [b5[0], b5[1], z_b], "ToeTip": tip.tolist()},
                     "measure": {"last_length_mm": round(info["length"], 2), "toe_box_stretch": round(info["k"], 4),
                                 "insole_z_frameF_mm": round(z_b, 2),
                                 "socked_toe_front_y_mm": round(sk_front, 2),
                                 "toe_room_ahead_of_standing_socked_toe_mm": round(sk_front - float(P[:, 1].min()), 2),
                                 "toe_room_ahead_of_standing_bare_toe_mm": round(float(V[:, 1].min() - P[:, 1].min()), 2),
                                 "foot_length_mm": round(L, 2),
                                 "toe_spring_deg_read": None if spring is None else round(spring, 2),
                                 "width_at_ball_line_mm": round(float(np.ptp(P[np.abs(P[:, 1] - bl) < 4.0][:, 0])), 1),
                                 "sock_rings": int(res["inner"].shape[0])}}
        say(f"{side}: sock {res['inner'].shape[0]} rings; last {info['length']:.1f} mm, tip {LS.TOE_ALLOWANCE} ahead of "
            f"the standing socked toe; toe spring read {spring}")
    return out, group


def _inside(bvh, p):
    from mathutils import Vector
    votes = 0
    for d in ((0.2718, 0.5772, 0.7701), (-0.6931, -0.1414, 0.7071), (0.11, -0.83, -0.55)):
        dv = Vector(d).normalized()
        o, n = Vector(p), 0
        for _ in range(64):
            hit = bvh.ray_cast(o, dv, 3000.0)
            if hit[0] is None:
                break
            n += 1
            o = hit[0] + dv * 1e-3
        votes += n % 2
    return votes >= 2


def robust_signed(V, bvh, near=6.0):
    """Signed distance (mm) to the skin, + outside: the nearest distance, its sign from ray parity (for points
    within `near` or read inside by the face normal), else from the face normal."""
    from mathutils import Vector
    d, _ = C.signed_dist(V, bvh)
    for i in np.nonzero(d < near)[0]:
        loc, n, _k, dist = bvh.find_nearest(Vector(V[i]))
        d[i] = -dist if _inside(bvh, V[i]) else dist
    return d


def robust_push(V, bvh, clear, iters=3):
    """Points nearer than `clear` mm to the skin (or inside it, by parity) moved out to `clear`: along the line from
    the nearest point when outside, along the face normal when inside."""
    from mathutils import Vector
    V = np.array(V, float)
    for _ in range(iters):
        d = robust_signed(V, bvh)
        bad = np.nonzero(d < clear)[0]
        if not len(bad):
            break
        for i in bad:
            loc, n, _k, dist = bvh.find_nearest(Vector(V[i]))
            loc = np.array(loc)
            u = (V[i] - loc) / max(dist, 1e-6) if d[i] > 0.05 else np.array(n)
            V[i] = loc + u * clear
    return V


def last_cloud(rec):
    """The upper's required outer cloud from the last: its grid grown UPPER_OFF along the last's normals, plus the
    ankle padding's foam on the sides and back above rest z 84 (h 120) (world mm)."""
    G, N = rec["G_w"].reshape(-1, 3), rec["N_w"].reshape(-1, 3)
    pad = PAD_OFF * smoothstep(80.0, 96.0, G[:, 2]) * smoothstep(0.3, -0.1, N[:, 2])
    return G + N * (UPPER_OFF + pad)[:, None]


def save_lasts(lasts, path, say):
    """cache/parts/<tag>_lasts.blend: Boot.{L,R}.Last (world, rest) and Empties for its markers."""
    import bpy
    from stages.foot import sock as SK
    ids = set()
    coll = bpy.data.collections.new("Aux.Boots.Lasts")
    bpy.context.scene.collection.children.link(coll)
    for side, rec in lasts.items():
        name = f"Boot.{side}.Last"
        me = SK.build_mesh(name, rec["G_f"], rec["frame"], face_list=rec["faces"], uv=False)
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        ob.hide_render = True
        ob["doc"] = SOCK_LAST_DOC
        ob["measure"] = json.dumps(rec["measure"])
        ids.add(ob)
        for k, p in rec["markers_f"].items():
            e = bpy.data.objects.new(f"{name}.{k}", None)
            e.empty_display_type, e.empty_display_size = "SPHERE", 0.004
            e.location = tuple(rec["frame"].to_w(np.asarray(p, float)) / 1000.0)
            coll.objects.link(e)
            ids.add(e)
    ids.add(coll)
    tmp = path + ".tmp.blend"
    bpy.data.libraries.write(tmp, ids, path_remap="NONE", fake_user=True, compress=False)
    os.replace(tmp, path)
    say("boots", "lasts saved", path)
    return coll


# --------------------------------------------------------------------------- the upper


def build_upper(last, ff, n_phi=240, n_th=300):
    """Rays from a point inside over a grid whose first row is the rim. Returns V, F, face materials
    (0 leather, 1 Cordura), the grid's rim row indices and the casting origin."""
    i_r = int(np.argmin(np.abs(last.zs - 100.0)))
    O = ff.xyz(last.cs[i_r] - 8.0, last.ct[i_r], 75.0)[None]
    phi = 2.0 * np.pi * np.arange(n_phi) / n_phi           # 0 = back of the heel (-s), toward +t (lateral)
    dirs_h = np.stack([-np.cos(phi), np.sin(phi)], -1)       # (s, t) components

    def world_dir(th, ph_dir):
        sth = np.sin(th)
        dst = ph_dir * sth[:, None]
        xy = dst[:, :1] * ff.u[:2] + dst[:, 1:2] * ff.t[:2]
        return np.column_stack([xy, np.cos(th)])

    lo, hi = np.full(n_phi, 0.02), np.full(n_phi, 1.5)
    for _ in range(26):                                      # the rim: the steepest ray leaving through the side
        mid = 0.5 * (lo + hi)
        P, _ = last.cast(np.repeat(O, n_phi, 0), world_dir(mid, dirs_h))
        top = P[:, 2] > last.rim_z(P) - 0.25
        lo, hi = np.where(top, mid, lo), np.where(top, hi, mid)
    th0 = hi + 0.003
    u = np.linspace(0.0, 1.0, n_th) ** 1.0                  # rows a little denser near the rim
    TH = th0[None, :] + (np.pi - 0.02 - th0[None, :]) * u[:, None]
    D = np.concatenate([world_dir(TH[i], dirs_h) for i in range(n_th)])
    P, _ = last.cast(np.repeat(O, len(D), 0), D)
    idx = np.arange(n_th * n_phi).reshape(n_th, n_phi)
    F, Fij = [], []
    for i in range(n_th - 1):
        for j in range(n_phi):
            j1 = (j + 1) % n_phi
            F.append((idx[i, j], idx[i, j1], idx[i + 1, j1], idx[i + 1, j]))
            Fij.append(((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)))   # grid corners (column n_phi = the seam)
    # orient outward
    a, b, c = P[F[n_phi * 40][0]], P[F[n_phi * 40][1]], P[F[n_phi * 40][2]]
    if np.cross(b - a, c - a) @ (a - O[0]) < 0:
        F = [tuple(reversed(f)) for f in F]
        Fij = [tuple(reversed(f)) for f in Fij]
    build_upper.grid = (n_th, n_phi, Fij)
    return P, F, idx[0], O[0]


def _folds(rng, n_major, spacing, depth, n_fine):
    """A seeded set of folds across a band: [(offset mm from the band's line, depth, wander amplitude, wander
    wavelength, phase, fade side (+1 fades laterally, -1 medially, 0 neither), fade start share)]."""
    out, d = [], float(rng.uniform(-6.0, -2.0))
    for k in range(n_major):
        out.append((d, float(rng.uniform(*depth)) * (1.0 - 0.15 * k), float(rng.uniform(1.5, 3.0)),
                    float(rng.uniform(18.0, 30.0)), float(rng.uniform(0, 2 * math.pi)),
                    int(rng.choice([-1, 0, 1])), float(rng.uniform(0.55, 0.85))))
        d += float(rng.uniform(*spacing))
    for _ in range(n_fine):
        out.append((float(rng.uniform(-14.0, d + 6.0)), float(rng.uniform(0.25, 0.55)), float(rng.uniform(1.0, 2.0)),
                    float(rng.uniform(10.0, 20.0)), float(rng.uniform(0, 2 * math.pi)),
                    int(rng.choice([-1, 1])), float(rng.uniform(0.2, 0.6))))
    return out


def _fold_profile(x, depth):
    """A fold across x (mm): a narrow valley between broad rounded shoulders, the toe-side shoulder (x < 0 here,
    toward the toe) the higher (the leather buckles forward). Negative is in."""
    return depth * (-np.exp(-(x / 0.95) ** 2) + 0.42 * np.exp(-((x + 2.6) / 2.4) ** 2) + 0.28 * np.exp(-((x - 2.4) / 2.6) ** 2))


def ankle_s(last):
    """s of the shaft's front at h 70 (the ankle's front), the start of the quarter's rise and the ankle folds."""
    i_a = int(np.argmin(np.abs(last.zs - 70.0)))
    return float(last.cs[i_a])


def quarter_h(last, s):
    """Round 6: the leather quarter's top edge (under the Cordura) at s: h 98 at the back, rising toward the throat."""
    s0 = ankle_s(last)
    return QUARTER[0] + QUARTER[1] * smoothstep(s0, s0 + QUARTER[2], s)


def vamp_s(ff, h):
    """Round 10 (critics r9 m1: "stitched suede and textile panels over the vamp and quarters, with visible panel
    seams"): the suede vamp's back edge at height h, a seam slanting back from the mudguard behind the ball up to the
    lace stays (the Zephyr-class pattern: a suede vamp and toe, Cordura quarter panels behind it)."""
    return ff.s_ball - VAMP[0] - VAMP[1] * (np.asarray(h, float) - 50.0)


def mud_h(ff, s):
    """Round 6: the mudguard's top edge at s: high at the heel, falling to MUD[1] at the ball."""
    return MUD[0] + (MUD[1] - MUD[0]) * smoothstep(60.0, ff.s_ball - 10.0, s)


def decorate_upper(last, ff, P, F, throat, side="L"):
    """Overlays, folds, padding and the throat as displacement along the field's normal; face materials (0 leather,
    1 Cordura). Round 3 (spec 02 §3.5, §4.4 step 5, §4.15): the vamp's folds lie along the metatarsal heads' line,
    two or three dominant ones at seeded spacings and depths with a field of fine wrinkles, each wandering and fading
    out towards one side; 2-3 ankle-break folds on the quarters in front of the ankle, deeper laterally; padding
    over the malleoli; soft compression wrinkles on the Cordura. Each boot takes its own seed (a pair, not a
    mirror)."""
    rng = np.random.default_rng(11 if side == "L" else 29)
    N = last.normal(P)
    s, t, h = ff.s_of(P), ff.t_of(P), ff.h_of(P)
    tc = np.interp(s, last.st, last.tc)
    sc = s + 0.0045 * (t - tc) ** 2                           # stations bowed back toward the sides
    toecap = smoothstep(last.s_tip - 82.0, last.s_tip - 80.0, sc)
    counter = smoothstep(98.0, 96.0, h + 0.42 * s) * smoothstep(92.0, 88.0, s)
    # Cordura shaft panels above the quarters (leather below 98 mm, the counter, the stays and backstrap)
    dback = np.abs(t - last.rim_c[1])
    backstrap = smoothstep(11.0, 9.0, dback) * smoothstep(last.rim_c[0] - 20.0, last.rim_c[0] - 40.0, s)
    qh = quarter_h(last, s)
    mud = smoothstep(mud_h(ff, s) + 1.0, mud_h(ff, s) - 1.0, h) * (1 - toecap) * (1 - counter)
    # round 10: the suede vamp ahead of its slanting seam (vamp_s), the Cordura quarter panels behind it down to the
    # mudguard (round 9: smooth leather all round below h 98, the critics' galosh)
    vamp = smoothstep(-1.0, 1.0, s - vamp_s(ff, h)) * (1 - toecap) * (1 - mud)
    quarter_tx = (1 - vamp) * (1 - mud) * (1 - toecap) * (1 - counter) * (1 - backstrap) * smoothstep(40.0, 50.0, h)
    cordura = np.maximum(smoothstep(qh - 1.0, qh + 1.0, h) * (1 - backstrap) * (1 - counter), quarter_tx)
    # round 10: the rubber toe cap (RUBBER_TOE), its top edge an arc falling from the tip into the rand
    xb = np.maximum(last.s_tip - sc, 0.0)
    hs = P[:, 2] - ff.z_top(s)
    rt_top = RAND["side"] + (RUBBER_TOE[1] - RAND["side"]) * np.clip(1.0 - xb / RUBBER_TOE[0], 0.0, 1.0) ** 1.4
    rubber = smoothstep(rt_top + 0.8, rt_top - 0.8, hs) * smoothstep(RUBBER_TOE[0] + 2.0, RUBBER_TOE[0] - 2.0, xb)
    lift = 0.8 * (1 - cordura) + TOECAP_LIFT * toecap + 0.8 * counter + MUD[2] * mud + 0.2 * vamp + RUBBER_TOE[2] * rubber
    # the vamp's flex folds along the metatarsal heads' line (oblique: the 5th head lies behind the 1st)
    lm = FootFrame.LANDMARKS or C.base_json()["landmarks"]
    m1 = np.array(lm[f"mt1_{side}"]["rest_mm"])
    m5 = np.array(lm[f"mt5_{side}"]["rest_mm"])
    a1 = np.array([ff.s_of(m1)[0], ff.t_of(m1)[0]])
    a5 = np.array([ff.s_of(m5)[0], ff.t_of(m5)[0]])
    tl = (a5 - a1) / np.linalg.norm(a5 - a1)
    nl = np.array([tl[1], -tl[0]])
    if nl[0] < 0:
        nl = -nl                                              # toward the toe
    d_line = (np.column_stack([s, t]) - a1) @ nl + 8.0        # the folds sit just behind the heads (where it bends)
    u_line = (np.column_stack([s, t]) - a1) @ tl              # along the line, 0 at the 1st head
    width = float(np.linalg.norm(a5 - a1))
    w_half = np.maximum(np.interp(s, last.st, last.w), 1.0)
    on_vamp = smoothstep(30.0, 46.0, h) * smoothstep(0.98, 0.7, np.abs(t - tc) / w_half) * (1 - toecap * 0.85)
    hc = np.zeros(len(P))
    # round 10 (m1: "a flex crease across the vamp"): the dominant folds deeper (1.5-2.4 -> 2.6-3.6 mm), fewer fine ones
    for d0, dep, wa, wl, ph, fade, f0 in _folds(rng, int(rng.integers(2, 4)), (9.0, 16.0), (2.6, 3.6),
                                                int(rng.integers(3, 6))):
        x = d_line - d0 - wa * np.sin(u_line / wl + ph)
        uu = np.clip(u_line / max(width, 1.0), -0.3, 1.3)
        fd = np.ones(len(P)) if fade == 0 else (smoothstep(f0 + 0.35, f0, uu) if fade > 0 else smoothstep(1 - f0 - 0.35, 1 - f0, uu))
        lat = 0.8 + 0.35 * smoothstep(0.1, 0.9, uu)           # deeper laterally
        hc += _fold_profile(x, dep) * fd * lat
    hc *= on_vamp
    # ankle-break folds on the quarters in front of the ankle, rising toward the back, deeper laterally
    s_ank = ankle_s(last)
    lateral = np.sign(t - tc)
    front_q = smoothstep(s_ank - 5.0, s_ank + 25.0, s) * smoothstep(1.05, 0.55, np.abs(t - tc) / np.maximum(w_half, 30.0)) * \
        (1 - throat.gap_mask(P))
    ab = np.zeros(len(P))
    hb = float(rng.uniform(98.0, 104.0))
    for k in range(int(rng.integers(2, 4))):
        h0 = hb + 11.0 * k + 0.22 * (s - s_ank - 40.0) * -1.0
        dep = float(rng.uniform(0.9, 1.5)) * (1.0 - 0.2 * k) * (1.0 + 0.3 * (lateral > 0))
        ab += _fold_profile(-(h - h0 - 1.5 * np.sin((s + 13.0 * k) / 9.0)), dep)
    ab *= front_q * smoothstep(82.0, 92.0, h) * smoothstep(150.0, 138.0, h) * (0.6 + 0.4 * cordura)
    # padding over the malleoli: a soft swell each side of the ankle on the quarters
    pad = np.zeros(len(P))
    for sgn, z0, amp in ((1.0, 110.0, 2.6), (-1.0, 122.0, 2.2)):   # lateral lower, medial higher (as the bones)
        pad += amp * np.exp(-((s - s_ank - 4.0) / 24.0) ** 2 - ((h - z0) / 18.0) ** 2) * smoothstep(0.2, 0.6, sgn * (t - tc) / np.maximum(w_half, 30.0))
    # soft compression wrinkles on the Cordura: short, mostly horizontal, seeded
    ang = np.arctan2(t - last.rim_c[1], s - last.rim_c[0])
    cw = np.zeros(len(P))
    for _ in range(16):
        a0, z0 = float(rng.uniform(-math.pi, math.pi)), float(rng.uniform(112.0, 196.0))
        ln, tilt, dep = float(rng.uniform(0.25, 0.6)), float(rng.uniform(-0.25, 0.25)), float(rng.uniform(0.25, 0.55))
        da = (ang - a0 + math.pi) % (2 * math.pi) - math.pi
        cw += _fold_profile(h - z0 - tilt * da * 55.0, dep) * np.exp(-(da / ln) ** 2)
    cw *= cordura * smoothstep(RIM_Z + 34.0, RIM_Z + 26.0, h)
    # the throat: between the stays the tongue and gussets sit 1.2 mm below the quarters
    tongue = throat.gap_mask(P) * 1.2
    disp = lift + hc + ab + pad + cw - tongue
    V = P + N * disp[:, None]
    fc = np.array([cordura[list(f)].mean() for f in F])
    fs = np.array([np.maximum(vamp, mud)[list(f)].mean() for f in F])
    fr = np.array([rubber[list(f)].mean() for f in F])
    fmat = np.where(fr > 0.5, 3, np.where(fc > 0.5, 1, np.where(fs > 0.5, 2, 0)))   # 0 leather, 1 Cordura, 2 suede, 3 rubber
    crease = smoothstep(0.15, 0.6, -(hc + ab + cw))
    return V, fmat, {"crease": crease, "zones": {"toecap": toecap, "counter": counter, "cordura": cordura,
                                                 "backstrap": backstrap, "mudguard": mud, "vamp": vamp,
                                                 "rubber_toe": rubber}}


class Throat:
    """The lace throat: a centre line on the upper from the rim down the shaft front and over the instep,
    the lateral direction along it, and points across it at a given distance (cast onto the upper)."""

    def __init__(self, last, ff, O):
        self.last, self.ff, self.O = last, ff, O
        # round 3: down the shaft front by horizontal casts from the shaft's axis (from the point inside, the casts
        # toward the rim left the shaft through its front wall half way up, and the throat began at h 168)
        z_m = 96.0
        zz = np.arange(RIM_Z - 1.0, z_m, -2.0)
        Os = ff.xyz(np.interp(zz, last.zs, last.cs), np.interp(zz, last.zs, last.ct), zz)
        Q1, _ = last.cast(Os, np.repeat(ff.u[None], len(zz), 0))
        sl = ff.s_ball + 62.0          # past E1, so the stays' lower ends and the bottom bar have line under them
                                       # (round 6: +45, was +30: the line ended above h 79 and capped E1 at h 93)
        low = ff.xyz(sl, np.interp(sl, last.st, last.tc), np.interp(sl, last.st, last.zb + last.h) + 6.0)
        mid = Q1[-1] + ff.u * 6.0
        tg = np.vstack([mid + (low - mid) * x for x in np.linspace(0, 1, 70)[1:]])
        D = tg - O
        D /= np.linalg.norm(D, axis=1, keepdims=True)
        Q2, _ = last.cast(np.repeat(O[None], len(D), 0), D)
        # round 6: over the instep, rays from the ankle point leave the vamp short of targets further forward (they
        # dip), so also cast straight up from inside the last's bottom under each target and keep the nearer hit
        st_, tt_ = ff.s_of(tg), ff.t_of(tg)
        zb_ = np.interp(st_, last.st, last.zb) + 12.0
        B0 = ff.xyz(st_, tt_, zb_)
        Du = ff.xyz(st_, tt_, zb_ + 10.0) - B0
        Du /= np.linalg.norm(Du, axis=1, keepdims=True)
        Q2b, okb = last.cast(B0, Du, far=200.0)
        nearer = okb & (np.linalg.norm(Q2b - tg, axis=1) < np.linalg.norm(Q2 - tg, axis=1))
        Q2[nearer] = Q2b[nearer]
        Q = np.vstack([Q1, Q2])
        L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))])
        self.Lmax = float(L[-1])
        # resample by arc length, smooth the lateral wobble
        g = np.arange(0.0, L[-1], 1.0)
        Q = np.column_stack([np.interp(g, L, Q[:, k]) for k in range(3)])
        for k in range(3):
            Q[:, k] = gauss1d(Q[:, k], 4.0)
        self.L, self.Q = g, Q
        self.N = last.normal(Q, h=4.0)
        for k in range(3):
            self.N[:, k] = gauss1d(self.N[:, k], 6.0)
        self.N /= np.linalg.norm(self.N, axis=1, keepdims=True)
        T = np.gradient(Q, axis=0)
        T /= np.linalg.norm(T, axis=1, keepdims=True)
        lat = np.cross(T, self.N)
        lat /= np.linalg.norm(lat, axis=1, keepdims=True)
        if (lat[len(lat) // 2, :2] @ ff.t[:2]) < 0:
            lat = -lat
        self.T, self.lat = T, lat                                   # lat points lateral (+t)
        hq = ff.h_of(Q)
        # round 10: E1 where the throat comes down to E1_H or forward to s_ball + E1_DS, whichever comes first (the
        # raised, rounded toe box keeps the crown above h 70 ahead of the ball, so a height alone ran E1 onto the nose)
        below = np.nonzero(((hq <= E1_H) | (ff.s_of(Q) >= ff.s_ball + E1_DS)) & (g > LACE_TOP + 6 * 15.0))[0]
        i1 = int(below[0]) if len(below) else len(g) - 1      # E1: where the throat comes down to E1_H
        self.e1_L = float(min(g[i1], g[-1] - 20.0))
        self.pitch = (self.e1_L - LACE_TOP) / 6.0

    def at(self, Ls):
        Ls = np.atleast_1d(Ls)
        i = np.clip(np.round(Ls).astype(int), 0, len(self.L) - 1)
        return self.Q[i], self.N[i], self.lat[i], self.T[i]

    def gap(self, Ls):
        f = np.clip(Ls / self.e1_L, 0, 1)                           # 0 at the rim, 1 at E1
        return GAP[1] + (GAP[0] - GAP[1]) * f

    def across(self, Ls, a, lift=0.0):
        """Surface points at lateral distance a (mm, + lateral) from the centre line at arc lengths Ls."""
        Q, N, lat, _ = self.at(Ls)
        a = np.broadcast_to(np.asarray(a, float), (len(Q),))
        # round 3: cast along the local normal from just inside (casting from the one point inside left the stays and
        # laces ragged where the throat bends from the shaft onto the instep)
        p0 = Q + lat * a[:, None]
        n0 = self.last.normal(p0, h=4.0) + N
        n0 /= np.linalg.norm(n0, axis=1, keepdims=True)
        start = p0 - n0 * 40.0
        bad = self.last.field(start) > 0.0                # a thin spot: start from the centre line's inside instead
        start[bad] = Q[bad] - N[bad] * 25.0
        P, _ = self.last.cast(start, n0, far=90.0, step=0.75)
        Nn = self.last.normal(P)
        lift = np.broadcast_to(np.asarray(lift, float), (len(P),))
        return P + Nn * lift[:, None], Nn

    def gap_mask(self, P):
        """1 between the stays (from the rim to below E1, with soft edges), else 0."""
        out = np.zeros(len(P))
        lo, hi = self.Q.min(0) - 45.0, self.Q.max(0) + 45.0
        cand = np.nonzero(np.all((P > lo) & (P < hi), axis=1))[0]
        if not len(cand):
            return out
        P = P[cand]
        d = np.linalg.norm(P[:, None, :] - self.Q[None, ::2, :], axis=2)
        j = np.argmin(d, axis=1) * 2
        Ls = self.L[j]
        rel = P - self.Q[j]
        a = np.abs(np.einsum("ij,ij->i", rel, self.lat[j]))
        along = np.einsum("ij,ij->i", rel, self.T[j])
        inside = smoothstep(0.5 * self.gap(Ls) + 1.0, 0.5 * self.gap(Ls) - 1.0, a)
        inside *= smoothstep(self.e1_L + 14.0, self.e1_L + 8.0, Ls + along) * (d.min(1) < 40.0)
        out[cand] = inside
        return out


def build_stays(throat):
    """Two leather strips either side of the throat, from below E1 to the rim, standing proud."""
    L0, L1 = -1.0, throat.e1_L + 12.0
    Ls = np.linspace(L0 + 1.0, L1, 64)
    V, F = [], []
    for sgn in (1.0, -1.0):
        base = len(V)
        nu = 9
        rows = []
        for k, Lk in enumerate(Ls):
            g = 0.5 * throat.gap(Lk)
            a = sgn * (g + np.linspace(0.0, STAY_W, nu))
            # the stay's lower end rounds off toward the vamp
            end = smoothstep(L1, L1 - 10.0, Lk)
            lift = STAY_PROUD * (0.35 + 0.65 * end) * (1 - 0.35 * (np.linspace(0, 1, nu) ** 6))
            P, _ = throat.across(np.full(nu, Lk), a, lift)
            rows.append(P)
        R = np.array(rows)
        V.extend(R.reshape(-1, 3).tolist())
        # outward winding, checked against the throat's normal (Solidify "inward" then really goes inward)
        i0, j0 = len(Ls) // 2, nu // 2
        nrm = np.cross(R[i0, j0 + 1] - R[i0, j0], R[i0 + 1, j0] - R[i0, j0])
        flip = nrm @ throat.at(np.array([Ls[i0]]))[1][0] < 0
        for i in range(len(Ls) - 1):
            for j in range(nu - 1):
                q = (base + i * nu + j, base + i * nu + j + 1, base + (i + 1) * nu + j + 1, base + (i + 1) * nu + j)
                F.append(tuple(reversed(q)) if flip else q)
    return np.array(V), F


def build_tongue(last, ff, throat):
    """The tongue's padded top, rising 10 mm above the rim between the stays (below the rim the tongue is the
    upper's own surface in the gap); it leans a little forward over the rim."""
    ir = int(np.argmin(np.abs(last.zs - RIM_Z)))
    cs, ct, a, b = last.cs[ir], last.ct[ir], last.a[ir], last.b[ir]
    half = 0.5 * GAP[1] + 8.0
    V, F = [], []
    nu, nv = 13, 8
    for k, zz in enumerate(np.linspace(RIM_Z - 10.0, RIM_Z + 10.0, nv)):
        for j, x in enumerate(np.linspace(-1, 1, nu)):
            top = RIM_Z + 10.0 - 8.0 * abs(x) ** 4
            z = min(zz, top)
            q = np.clip(half * x / b, -0.95, 0.95)
            lean = 3.0 * smoothstep(RIM_Z - 4.0, RIM_Z + 10.0, z)
            s_ = cs + (a - 2.6) * math.sqrt(1 - q * q) + lean
            V.append(ff.xyz(s_, ct + half * x, z))
    for i in range(nv - 1):
        for j in range(nu - 1):
            F.append((i * nu + j, i * nu + j + 1, (i + 1) * nu + j + 1, (i + 1) * nu + j))
    V = np.array(V).reshape(-1, 3)
    c = ff.xyz(cs, ct, RIM_Z)
    f = F[len(F) // 2]
    if np.cross(V[f[1]] - V[f[0]], V[f[3]] - V[f[0]]) @ (V[f[0]] - c) < 0:
        F = [tuple(reversed(q)) for q in F]
    return V, F


def build_collar(last, ff, P, rim_row, throat):
    """The padded collar: a 10 x 22 roll round the rim from one stay top round the back to the other."""
    R = P[rim_row]
    c = R[:, :2].mean(0)
    ang = np.arctan2(R[:, 1] - c[1], R[:, 0] - c[0])
    o = np.argsort(ang)
    R, ang = R[o], ang[o]
    grid = np.linspace(-math.pi, math.pi, 97)[:-1]
    Pr = np.column_stack([np.interp(grid, ang, R[:, k], period=2 * math.pi) for k in range(3)])
    # leave out the front between the stays: angle of the throat's top centre
    Qt = throat.Q[0]
    a_front = math.atan2(Qt[1] - c[1], Qt[0] - c[0])
    rel = (grid - a_front + math.pi) % (2 * math.pi) - math.pi
    r_c = np.linalg.norm(Pr[:, :2] - c, axis=1).mean()
    a_open = (0.5 * GAP[1] + 6.0) / r_c
    keep = np.abs(rel) > a_open
    order = np.argsort((rel[keep] + 2 * math.pi) % (2 * math.pi))
    Pk = Pr[keep][order]
    O = np.zeros_like(Pk)
    O[:, :2] = Pk[:, :2] - c
    O /= np.maximum(np.linalg.norm(O, axis=1, keepdims=True), 1e-9)
    th, tall = COLLAR["thick"], COLLAR["tall"]
    m, k = len(Pk), 12
    V = []
    for i in range(m):
        e = min(i, m - 1 - i)
        sc = min(1.0, 0.45 + 0.55 * e / 4.0)                     # the ends taper into the stays
        for q in range(k):
            a = 2 * math.pi * q / k
            o_, u_ = 0.5 * th * sc * math.cos(a) - 1.0, 0.5 * tall * (0.6 + 0.4 * sc) * math.sin(a) - 0.5 * tall + 5.0
            V.append(Pk[i] + O[i] * o_ + np.array([0, 0, u_]))
    F = []
    for i in range(m - 1):
        for q in range(k):
            q1 = (q + 1) % k
            F.append((i * k + q, (i + 1) * k + q, (i + 1) * k + q1, i * k + q1))
    V = np.array(V)
    for i0, rev in ((0, True), (m - 1, False)):            # end caps
        cap = tuple(i0 * k + q for q in range(k))
        F.append(tuple(reversed(cap)) if rev else cap)
    f = F[len(F) // 2]
    cen = V[list(f)].mean(0)
    sec = Pk[m // 2] + O[m // 2] * 1.5 + np.array([0, 0, 6.0 - 0.5 * tall])
    if np.cross(V[f[1]] - V[f[0]], V[f[3]] - V[f[0]]) @ (cen - sec) < 0:
        F = [tuple(reversed(q)) for q in F]
    return V, F


# --------------------------------------------------------------------------- hardware and laces


def torus(c, n, R, r, nu=16, nv=8):
    n = n / np.linalg.norm(n)
    e1 = np.cross(n, [0.0, 0.0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    V = []
    for i in range(nu):
        a = 2 * math.pi * i / nu
        d = math.cos(a) * e1 + math.sin(a) * e2
        for j in range(nv):
            b = 2 * math.pi * j / nv
            V.append(c + d * (R + r * math.cos(b)) + n * (r * math.sin(b)))
    F = [(i * nv + j, i * nv + (j + 1) % nv, ((i + 1) % nu) * nv + (j + 1) % nv, ((i + 1) % nu) * nv + j)
         for i in range(nu) for j in range(nv)]
    return np.array(V), F


def tube(path, r, sides=8, caps=True):
    P = np.asarray(path, float)
    n = len(P)
    T = np.gradient(P, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    ref = np.array([0.0, 0.0, 1.0]) if abs(T[0, 2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    Nf = [np.cross(np.cross(T[0], ref), T[0])]
    Nf[0] /= np.linalg.norm(Nf[0])
    for k in range(1, n):
        v = Nf[-1] - T[k] * (Nf[-1] @ T[k])
        Nf.append(v / max(np.linalg.norm(v), 1e-9))
    Nf = np.array(Nf)
    B = np.cross(T, Nf)
    a = 2 * np.pi * np.arange(sides) / sides
    V = (P[:, None, :] + r * (np.cos(a)[None, :, None] * Nf[:, None, :] + np.sin(a)[None, :, None] * B[:, None, :]))
    V = V.reshape(-1, 3)
    F = []
    for k in range(n - 1):
        for j in range(sides):
            j1 = (j + 1) % sides
            F.append((k * sides + j, k * sides + j1, (k + 1) * sides + j1, (k + 1) * sides + j))
    if caps:
        V = np.vstack([V, P[0], P[-1]])
        c0, c1 = len(V) - 2, len(V) - 1
        for j in range(sides):
            j1 = (j + 1) % sides
            F.append((j1, j, c0))
            F.append(((n - 1) * sides + j, (n - 1) * sides + j1, c1))
    return V, F


def join(pieces):
    V, F = [], []
    for v, f in pieces:
        b = len(V)
        V.extend(np.asarray(v, float).tolist())
        F.extend(tuple(i + b for i in q) for q in f)
    return np.array(V), F


def lace_positions(throat):
    """Arc lengths along the throat and lateral distances of the 7 positions (top hook first)."""
    Ls = LACE_TOP + throat.pitch * np.arange(7)
    a = 0.5 * throat.gap(Ls) + 10.0
    return Ls, a


def build_hardware(throat):
    Ls, a = lace_positions(throat)
    pieces = []
    holes = {}
    for k, (Lk, ak) in enumerate(zip(Ls, a)):
        for sgn in (1.0, -1.0):
            P, N = throat.across(np.array([Lk]), sgn * ak, STAY_PROUD + 0.3)
            p, n = P[0], N[0]
            if k >= 2:                                    # five round eyelets: flange 10, hole 5.5
                pieces.append(torus(p, n, 3.9, 1.15, nu=14, nv=6))
                holes[(k, sgn)] = p - n * 0.8
            else:                                         # two speed hooks: plate and a bent wire
                _, _, lat, T = throat.at(np.array([Lk]))
                out = sgn * lat[0]                        # away from the throat
                pl = []
                for du, dv in ((-7, -2), (7, -2), (7, 12), (-7, 12)):
                    pl.append(p + T[0] * du + out * dv)
                pv = np.array(pl + [q + n * 1.2 for q in pl])
                pf = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
                pieces.append((pv, pf))
                r = 3.0
                c = p + out * (-1.0 + r) + n * 3.5
                path = [p + n * 0.5] + [c + r * (math.cos(b) * out + math.sin(b) * n)
                                        for b in np.linspace(math.pi, -0.25 * math.pi, 10)]
                pieces.append(tube(path, 1.25, sides=8))
                holes[(k, sgn)] = c + n * 0.0 - out * r * 0.2
    return join(pieces), holes


def build_laces(throat, holes):
    """Criss-cross from E1 up: each strand from one side's eyelet over the tongue to the other side's next,
    lying at a constant height over the upper (cast under each point), entering the eyelets at its ends."""
    Ls, a = lace_positions(throat)
    pieces = []
    order = list(range(6, -1, -1))                       # E1 (index 6) up to the top hook (0)
    rng = np.random.default_rng(int(abs(throat.Q[0, 0])) % 97)

    def strand(ka, sa, kb, sb, sag, drift):
        """From hole (ka, side sa) to (kb, side sb) over the tongue: laid in the throat's own (L, a) coordinates
        at a height over the surface, the crossing drifting `drift` mm off the centre line, the ends running into
        the holes."""
        x = np.linspace(0.0, 1.0, 22)
        L_ = Ls[ka] + (Ls[kb] - Ls[ka]) * x
        a_ = sa * a[ka] + (sb * a[kb] - sa * a[ka]) * x + drift * np.sin(np.pi * x)
        S, Ns = throat.across(L_, a_, 0.0)
        hgt = STAY_PROUD + LACE_R + 0.6 + sag * np.sin(np.pi * x)
        pts = S + Ns * hgt[:, None]
        for k in range(3):                                # the cord does not follow the surface's facets
            pts[:, k] = gauss1d(pts[:, k], 1.6)
        p0, p1 = holes[(ka, sa)], holes[(kb, sb)]
        w = np.clip(np.minimum(x, 1 - x) / 0.14, 0, 1)
        q = p0[None] + (p1 - p0)[None] * x[:, None]
        return q + (pts - q) * w[:, None]

    k0 = order[0]
    pieces.append(tube(strand(k0, 1.0, k0, -1.0, 0.3, 0.0), LACE_R, sides=8))
    for side0 in (1.0, -1.0):
        sgn = side0
        for i in range(len(order) - 1):
            ka, kb = order[i], order[i + 1]
            sag = 1.8 if (side0 > 0) == (i % 2 == 0) else 0.3   # the strands take turns riding over
            slack = 0.6 * max(0.0, 1.0 - i / 3.0)                # slacker low, tight at the ankle (spec 02 §4.11)
            pieces.append(tube(strand(ka, sgn, kb, -sgn, sag + slack, float(rng.uniform(-3.0, 3.0))), LACE_R, sides=8))
            sgn = -sgn
    Q, N, _, _ = throat.at(np.array([1.0]))
    pieces.append(torus(Q[0] + N[0] * 5.0, N[0], 3.0, 1.9, nu=10, nv=6))   # the knot, under the hem
    return join(pieces)


# --------------------------------------------------------------------------- rand, sole, lugs


def plan_outline(last, ff, dz_of_psi, n=180, iters=3, centre_s=150.0, cap=None):
    """Horizontal sections of the upper at heights z_top(s) + dz(psi): casts from a point inside the foot. cap: at
    most this share of the upper's own height over the stripe there (round 3: the low sprung toe of the real last
    left the bumper's top rows above the toe box, where the casts ran back and folded)."""
    psi = 2.0 * np.pi * np.arange(n) / n                     # 0 = toward the toe, + toward lateral
    D2 = np.stack([np.cos(psi), np.sin(psi)], -1)
    Dw = np.column_stack([D2[:, :1] * ff.u[:2] + D2[:, 1:2] * ff.t[:2], np.zeros(n)])
    tc = float(np.interp(centre_s, last.st, last.tc))
    s_hit = np.full(n, centre_s)
    dz = dz_of_psi(psi)
    for _ in range(iters):
        dzi = dz if cap is None else np.minimum(dz, cap * np.maximum(
            np.interp(s_hit, last.st, last.zb + last.h) - ff.z_top(s_hit), 2.0))
        z = ff.z_top(s_hit) + dzi
        O = ff.xyz(np.full(n, centre_s), np.full(n, tc), z)
        P, _ = last.cast(O, Dw, f=last.base, far=260.0, step=1.0)
        s_hit = ff.s_of(P)
    return P, psi


def plan_normals(P):
    n = len(P)
    nrm = np.zeros((n, 3))
    c = P[:, :2].mean(0)
    for i in range(n):
        d = P[(i + 1) % n, :2] - P[i - 1, :2]
        nn = np.array([d[1], -d[0]])
        nn /= max(np.linalg.norm(nn), 1e-9)
        if nn @ (P[i, :2] - c) < 0:
            nn = -nn
        nrm[i, :2] = nn
    # smooth the normals a little (the outline is sampled finely)
    for _ in range(3):
        nrm = 0.25 * np.roll(nrm, 1, 0) + 0.5 * nrm + 0.25 * np.roll(nrm, -1, 0)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    return nrm


def rand_height(psi):
    toe = np.clip(np.cos(psi), 0, 1) ** RAND.get("toe_exp", 10.0)   # round 10: 10 -> 4, a toe cap wrapping the
                                                                     # toe's front and sides with a curved top edge
    heel = np.clip(-np.cos(psi), 0, 1) ** 4
    return RAND["side"] + (RAND["toe"] - RAND["side"]) * toe + (RAND["heel"] - RAND["side"]) * heel


def build_rand(last, ff):
    """The rubber rand round the upper above the midsole stripe, rising into a toe bumper with a lip."""
    fr = [(-1.5, 0.0), (0.0, 0.0), (0.33, 0.0), (0.66, 0.0), (1.0, -2.2), (1.0, -1.2), (1.0, 0.0)]
    rows = []
    for k, (f, extra) in enumerate(fr):
        if k == 0:
            P, psi = plan_outline(last, ff, lambda p: np.full(len(p), -1.5))
        else:
            P, psi = plan_outline(last, ff, lambda p, f=f, extra=extra: rand_height(p) * f + extra, cap=0.62 * max(f, 0.3))
        nrm = plan_normals(P)
        if k >= 2:                                        # follow the toe box's slope, not the plan
            n3 = last.normal(P)
            wgt = min(1.0, 0.6 + 0.2 * (k - 1))           # round 3: hug the toe box (the wall stood off it as a visor)
            nrm = n3 * wgt + nrm * (1 - wgt)
            nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
        proud = {0: RAND["proud"], 4: RAND["proud"] + RAND["lip"], 5: RAND["proud"] + RAND["lip"] * 0.8,
                 6: 0.6}.get(k, RAND["proud"])
        rows.append(P + nrm * proud)
    n = len(rows[0])
    V = np.vstack(rows)
    F = []
    for r in range(len(rows) - 1):
        for i in range(n):
            j = (i + 1) % n
            F.append((r * n + i, r * n + j, (r + 1) * n + j, (r + 1) * n + i))
    c = V.mean(0)
    f = F[0]
    if np.cross(V[f[1]] - V[f[0]], V[f[3]] - V[f[0]]) @ (V[f[0]] - c) < 0:
        F = [tuple(reversed(q)) for q in F]
    return V, F


def build_sole(last, ff):
    """Outsole cup and midsole stripe as one closed solid from the upper's outline at the stripe top."""
    P, psi = plan_outline(last, ff, lambda p: np.full(len(p), 0.5))
    nrm = plan_normals(P)
    Pw = P + nrm * SIDEWALL
    s = ff.s_of(Pw)
    zb = ff.z_bottom(s) + LUG + ff.arch(s)                   # the sole's base; the lugs stand below it (round 9:
                                                             # recessed under the arch)
    zt = ff.z_top(s)
    axis = ff.xyz(s, np.interp(s, last.st, last.tc), 0.0)[:, :2]
    rings = []
    for fr in (0.35, 0.7):
        Q = axis + (Pw[:, :2] - axis) * fr
        rings.append(np.column_stack([Q, zb]))
    rings.append(np.column_stack([Pw[:, :2] - nrm[:, :2] * 1.5, zb]))
    rings.append(np.column_stack([Pw[:, :2], zb + 1.5]))
    rings.append(np.column_stack([Pw[:, :2], zb + CUP - 0.6]))          # outsole cup's top edge
    rings.append(np.column_stack([Pw[:, :2] - nrm[:, :2] * 0.5, zb + CUP]))   # a groove at the join
    rings.append(np.column_stack([Pw[:, :2] - nrm[:, :2] * 0.2, zb + CUP + 0.8]))
    rings.append(np.column_stack([Pw[:, :2] + nrm[:, :2] * 0.3, zt - 1.5]))
    rings.append(np.column_stack([Pw[:, :2] - nrm[:, :2] * 1.0, zt]))
    rings.append(np.column_stack([Pw[:, :2] - nrm[:, :2] * 4.0, zt]))
    V = np.vstack(rings)
    n = len(Pw)
    F, mat = [], []
    R = len(rings)
    for r in range(R - 1):
        for i in range(n):
            j = (i + 1) % n
            F.append((r * n + i, r * n + j, (r + 1) * n + j, (r + 1) * n + i))
            mat.append(1 if r < 5 else 0)                    # 1 = outsole, 0 = midsole
    F.append(tuple(range(n - 1, -1, -1)))
    mat.append(1)
    F.append(tuple(range((R - 1) * n, R * n)))
    mat.append(0)
    a, b, cc = V[F[-2][0]], V[F[-2][1]], V[F[-2][2]]
    if np.cross(b - a, cc - a)[2] > 0:
        F = [tuple(reversed(f)) for f in F]
    outline = np.column_stack([Pw[:, :2] - nrm[:, :2] * 1.5, zb])
    return V, F, mat, outline, nrm


def prism(poly_st, ff, z_top_of, z_bot_of, draft=0.8):
    """A lug: a plan polygon (s, t; counter-clockwise seen from below or above, either) extruded from its top
    (inside the sole's base) down to the floor plane, the bottom face inset by `draft`."""
    Pst = np.asarray(poly_st, float)
    c = Pst.mean(0)
    inset = c + (Pst - c) * np.maximum(1 - draft / np.maximum(np.linalg.norm(Pst - c, axis=1), 1e-6), 0.3)[:, None]
    top = ff.xyz(Pst[:, 0], Pst[:, 1], z_top_of(Pst[:, 0]))
    bot = ff.xyz(inset[:, 0], inset[:, 1], z_bot_of(inset[:, 0]))
    m = len(Pst)
    V = np.vstack([top, bot])
    F = [tuple(range(m)), tuple(range(2 * m - 1, m - 1, -1))]
    for i in range(m):
        j = (i + 1) % m
        F.append((i, m + i, m + j, j))
    # orient: the bottom face's normal must point down
    a, b, cc = V[m], V[m + 1], V[m + 2]
    if np.cross(b - a, cc - a)[2] < 0:
        F = [tuple(reversed(f)) for f in F]
    return V, F


def point_in_poly(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


def build_lugs(last, ff, outline, nrm_out):
    """Perimeter teeth wrapping 3 mm up the sidewall, forefoot chevrons, waist bars and heel blocks."""
    zbase = lambda s: ff.z_bottom(s) + LUG + 0.8 + ff.arch(s)  # sunk into the base
    zfloor = lambda s: ff.z_bottom(s)
    zwaist = lambda s: ff.z_bottom(s) + 2.0 + ff.arch(s)      # the waist bars stand 3 mm (raised arch)
    O_st = np.column_stack([ff.s_of(outline), ff.t_of(outline)])
    inner = O_st.mean(0) + (O_st - O_st.mean(0)) * 0.9
    pieces = []
    # perimeter teeth
    L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(np.vstack([O_st, O_st[:1]]), axis=0), axis=1))])
    pos, x = [], 0.0
    while x < L[-1] - 6:
        i = int(np.searchsorted(L, x)) % len(O_st)
        si = O_st[i, 0]
        pos.append(x)
        x += 15.0 if si > ff.s_ball - 50 else 26.0
    for x in pos:
        i = int(np.searchsorted(L, x)) % len(O_st)
        j = (i + 2) % len(O_st)
        p = O_st[i]
        tg = O_st[j] - O_st[i - 2]
        tg /= max(np.linalg.norm(tg), 1e-9)
        nn = np.array([nrm_out[i, :2] @ ff.u[:2], nrm_out[i, :2] @ ff.t[:2]])
        nn /= max(np.linalg.norm(nn), 1e-9)
        sv = float(p[0])
        if 128.0 > sv > 78.0 or ff.arch(sv) > 1.0:     # the waist: no teeth under the arch (round 9: nor its recess)
            continue
        ln = 12.0 if sv > ff.s_ball - 50 else 19.0
        poly = [p - tg * ln / 2 + nn * TOOTH_PROUD, p + tg * ln / 2 + nn * TOOTH_PROUD, p + tg * ln / 2 * 0.8 - nn * 10.0,
                p - tg * ln / 2 * 0.8 - nn * 10.0]
        V, F = prism(poly, ff, lambda s: ff.z_bottom(s) + LUG + TOOTH_WRAP, zfloor, draft=1.2)
        pieces.append((V, F))
    # forefoot chevrons, two per row, pointing toward the toe
    tcen = lambda s: float(np.interp(s, last.st, last.tc))
    for k, s0 in enumerate(np.arange(ff.s_ball - 35.0, last.s_tip - 22.0, 15.0)):
        for side in (1.0, -1.0):
            tc0 = tcen(s0) + side * 20.0
            for arm in (1.0, -1.0):
                a0 = np.array([s0 + 4.0, tc0])
                d = np.array([-math.sin(math.radians(30)), arm * math.cos(math.radians(30))])
                e = np.array([-d[1], d[0]])
                poly = [a0 - e * 4.5, a0 + d * 17.0 - e * 4.5, a0 + d * 17.0 + e * 4.5, a0 + e * 4.5]
                if all(point_in_poly(q, inner) for q in poly):
                    pieces.append(prism(poly, ff, zbase, zfloor, draft=0.8))
    # waist bars
    for s0 in np.arange(84.0, 126.0, 14.0):
        tc0 = tcen(s0)
        poly = [(s0 - 4, tc0 - 26), (s0 + 4, tc0 - 26), (s0 + 4, tc0 + 26), (s0 - 4, tc0 + 26)]
        if all(point_in_poly(q, inner) for q in poly):
            pieces.append(prism(poly, ff, zbase, zwaist, draft=0.6))
    # heel blocks: two columns, three rows; the front row's leading face is the heel breast
    for s0 in (14.0, 39.0, 63.0):
        for side in (1.0, -1.0):
            tc0 = tcen(s0) + side * 13.0
            poly = [(s0 - 10, tc0 - 10), (s0 + 10, tc0 - 10), (s0 + 10, tc0 + 10), (s0 - 10, tc0 + 10)]
            if all(point_in_poly(q, inner) for q in poly):
                pieces.append(prism(poly, ff, zbase, zfloor, draft=0.9))
    return join(pieces)


# --------------------------------------------------------------------------- round 3: the library's hardware, strap, stitches

STRAP_H, STRAP_W, STRAP_T, STRAP_SO = 158.0, 15.0, 1.5, 1.0     # spec 02 §3.4: 15 x 1.5 webbing at h 158, 1 proud
LOCK_PHI, KEEPER_PHI = 150.0, 72.0                              # spec 02 §0 item 5


def _surface(ob):
    from lib import sweep
    return sweep.Surface(ob)


def _rest_z(ff, h, s):
    """Rest z of a height h above the floor (the pose's sole plane, no toe spring) at station s."""
    return h + (-HEEL_SEAT + ff.k * (s - ff.s_seat))


def shaft_point(S, last, ff, phi_deg, h, out=0.0):
    """The upper's surface point at spec 02's phi (0 the toe side, + lateral, 180 the back) and height h: a ray
    from the shaft's axis outward. Returns (point, normal) in world mm."""
    zc = _rest_z(ff, h, float(np.interp(h - 36.0, last.zs, last.cs)))
    cs, ct = float(np.interp(zc, last.zs, last.cs)), float(np.interp(zc, last.zs, last.ct))
    a = math.radians(phi_deg)
    d = math.cos(a) * ff.u + math.sin(a) * ff.t
    o = ff.xyz(cs, ct, zc)
    hit = S.ray(o, d / np.linalg.norm(d), 250.0)
    if hit is None or hit[0] is None:
        raise RuntimeError(f"no shaft surface at phi {phi_deg}, h {h}")
    p, n = np.asarray(hit[0], float), np.asarray(hit[1], float)
    return p + n * out, n


def phi_of(last, ff, P, h):
    zc = _rest_z(ff, h, float(np.interp(h - 36.0, last.zs, last.cs)))
    cs, ct = float(np.interp(zc, last.zs, last.cs)), float(np.interp(zc, last.zs, last.ct))
    return math.degrees(math.atan2(float(ff.t_of(P)[0]) - ct, float(ff.s_of(P)[0]) - cs))


def _out_frame(M, outward):
    """frame_on's frame with +Z turned to the outward side (the stays' mesh normals are not reliably outward)."""
    if M[:3, 2] @ outward < 0:
        M = M.copy()
        M[:3, 2] = -M[:3, 2]
        M[:3, 1] = np.cross(M[:3, 2], M[:3, 0])
    return M


def build_hardware_lib(throat, S_stays, coll, side):
    """Rolled eyelets (five a side) and plate speed hooks (two a side) from lib/gear_hardware on the stays, each
    seated a little unevenly (seeded). Returns (eyelets object, hooks object, {(k, sgn): lace point})."""
    from lib import gear_hardware as GH
    Ls, a = lace_positions(throat)
    ey, hook = GH.eyelet(), GH.speed_hook()
    seed0 = 0 if side == "L" else 50
    e_pieces, h_pieces, holes = [], [], {}
    for k, (Lk, ak) in enumerate(zip(Ls, a)):
        for sgn in (1.0, -1.0):
            P, Nn = throat.across(np.array([Lk]), sgn * ak, STAY_PROUD)
            _, _, lat, T = throat.at(np.array([Lk]))
            up = -T[0]                                            # the throat runs from the rim down
            sd = seed0 + k * 3 + (0 if sgn > 0 else 1)
            if k >= 2:
                M = _out_frame(GH.frame_on(S_stays, P[0], up, seed=sd, seat_mm=0.3, tilt_deg=3.0), Nn[0])
                e_pieces.append(GH.conform(ey, S_stays, M).transformed(M))
                holes[(k, sgn)] = M[:3, 3] - M[:3, 2] * 0.8
            else:
                M = _out_frame(GH.frame_on(S_stays, P[0], up, seed=sd, seat_mm=0.2, tilt_deg=2.0), Nn[0])
                toward = -sgn * lat[0]                            # toward the throat's centre line
                pc = hook if (M[:3, 1] @ toward) > 0 else hook.mirrored("Y")
                pw = GH.conform(pc, S_stays, M).transformed(M)
                h_pieces.append(pw)
                holes[(k, sgn)] = np.asarray(pw.anchors["wrap"][0], float)
    from lib.gear_hardware import Piece
    eo = GH.to_object(f"Boot.{side}.Eyelets", Piece.join(e_pieces, bevel=ey.bevel), material="Metal.Gunmetal",
                      part="Boot", coll=coll)
    ho = GH.to_object(f"Boot.{side}.Hooks", Piece.join(h_pieces, bevel=hook.bevel), material="Metal.Gunmetal",
                      part="Boot", coll=coll)
    return eo, ho, holes


def build_strap(S, last, ff, throat, coll, side):
    """The drawing's cuff strap (spec 02 §4.10, take 1's lib_gear.build_strap on the real boot): a three-quarter
    ring at h 158 from under the medial stay round the heel to a ladder-lock at phi 150, the lateral strap from under
    the lateral stay back through the lock and forward on itself through the lateral keeper as the tail; two
    leather keepers at phi +-72; tacks at the folds and anchors."""
    from lib import gear_hardware as GH, gear_webbing as GW, gn_stitches as GS, sweep
    h, w, t, so = STRAP_H + (0.0 if side == "L" else 1.5), STRAP_W, STRAP_T, STRAP_SO
    sd = 0 if side == "L" else 40
    # where the stays' back edges stand at the strap's height: the strap's ends tuck under them
    Lq = throat.L[np.argmin(np.abs(ff.h_of(throat.Q) - h))]
    edge = {}
    for sgn in (1.0, -1.0):
        P, _ = throat.across(np.array([Lq]), sgn * (0.5 * throat.gap(Lq) + STAY_W - 4.0), 0.0)
        edge[sgn] = phi_of(last, ff, P, h)
    pb, nb = shaft_point(S, last, ff, LOCK_PHI, h)
    fwd = shaft_point(S, last, ff, LOCK_PHI - 10.0, h)[0] - shaft_point(S, last, ff, LOCK_PHI + 10.0, h)[0]
    lock = GH.ladder_lock(24.0, 18.0, 3.0, 3.0, 2, arch=1.2, edge_r=1.1)
    M = GH.frame_on(S, pb, (0.0, 0.0, 1.0), lift=6.3)
    y = sweep._unit(fwd - (fwd @ M[:3, 2]) * M[:3, 2])
    x = np.cross(y, M[:3, 2])
    M[:3, 0], M[:3, 1] = x, y
    lock_ob = GH.to_object(f"Boot.{side}.Buckle", lock, matrix=M, material="Metal.Gunmetal", part="Boot", coll=coll)
    rear_bar = M[:3, :3] @ np.array([0.0, -7.5, 1.2 * (1 - (15.0 / 18.0) ** 2)]) + M[:3, 3]
    gap = 3.4
    s_end = float(nb @ (rear_bar - pb)) - (t + gap / 2.0)
    e_m = edge[-1.0]
    phis = [e_m, -55.0 if e_m > -55.0 else e_m - 10.0, -90.0, -125.0, -160.0, 180.0, 165.0]
    ctrl = [shaft_point(S, last, ff, p, h)[0] for p in phis]
    end = rear_bar - nb * (t + gap / 2.0)
    path_m = sweep.surface_path(S, ctrl + [end - nb * s_end], standoff=[so] * len(phis) + [s_end], step=1.0)
    strap_m = GW.strap(path_m, w, t, roll_deg=0.4, z_jitter=0.3, seed=5 + sd)
    sweep.fold_end(strap_m, 12.0, gap=gap)
    tail_so = so + t + 0.3
    e_l = edge[1.0]
    p_in = sweep.surface_path(S, [shaft_point(S, last, ff, p, h)[0] for p in (e_l, 60.0, 90.0, 120.0, 140.0, 152.0)],
                              standoff=so + t, step=1.0)
    path_in = sweep.Path(p_in.co, -p_in.normal, True, p_in.on, False, p_in.surface, p_in.standoff)
    path_out = sweep.surface_path(S, [shaft_point(S, last, ff, p, h)[0] for p in (146.0, 130.0, 100.0, KEEPER_PHI,
                                                                                  KEEPER_PHI - 20.0, KEEPER_PHI - 30.0)],
                                  standoff=tail_so, step=1.0)
    joined = sweep.Path.join([path_in, path_out])
    slots = [GH.through(lock, 0, thickness=t, direction=1, wrap=-1, snug=True), GH.over(lock, 1, direction=1),
             GH.through(lock, 1, thickness=t, direction=-1, wrap=1, snug=True)]
    threaded = sweep.thread(joined, lock_ob, slots, lead=5.0, clear=0.3)
    strap_l = GW.strap(threaded, w, t, roll_deg=0.4, z_jitter=0.25, seed=6 + sd)
    sweep.fold_end(strap_l, 10.0)
    straps = GW.webbing(f"Boot.{side}.Strap", [strap_m, strap_l], part="Boot", coll=coll)
    keepers, kst = [], []
    for phi, standoff in ((KEEPER_PHI, 5.2), (-KEEPER_PHI, 3.4)):
        c, n = shaft_point(S, last, ff, phi, h)
        along = shaft_point(S, last, ff, phi + 3.0, h)[0] - shaft_point(S, last, ff, phi - 3.0, h)[0]
        keepers.append(GW.keeper(S, c, along, span=19.5, width=12.0, thickness=2.0, standoff=standoff, tab=8.0,
                                 seed=int(phi) + sd))
    kob = GW.webbing(f"Boot.{side}.Keepers", [k.strip for k in keepers], part="Boot", coll=coll, bevel=0.5,
                     material="Leather.Boot.FullGrain")
    for k, kp in enumerate(keepers):
        kst.append(kp.box_x(kob, size=(6.0, 9.0), pitch=2.4, seed=7 + k + sd))
    tacks = [GW.fold_tack(straps, strap_l, length=12.0, width=4.0, seed=1 + sd),
             GW.fold_tack(straps, strap_m, length=12.0, width=4.0, from_end=7.5, seed=2 + sd)]
    pen = {nm: round(sweep.penetration(sw, S)["max_mm"], 2) for nm, sw in (("medial", strap_m), ("lateral", strap_l))}
    info = {"h": h, "anchor_phi": [round(e_m, 1), round(e_l, 1)], "lock_phi": LOCK_PHI, "keeper_phi": KEEPER_PHI,
            "into_boot_mm": pen, "tightest_bend_mm": round(threaded.min_bend_radius(), 2)}
    return [straps, kob, lock_ob], kst, tacks, info


def iso_points(V, F, field, keep):
    """Points where `field` crosses 0 on the mesh's edges whose two ends are both kept (world mm)."""
    E = C.edges_of(F)
    a, b = E[:, 0], E[:, 1]
    fa, fb = field[a], field[b]
    m = (fa * fb < 0) & keep[a] & keep[b]
    u = fa[m] / (fa[m] - fb[m])
    return V[a[m]] + (V[b[m]] - V[a[m]]) * u[:, None]


def ordered(P, key, step=5.0, smooth=2.0):
    """Points sorted by key and thinned to about one per `step` mm of key (their mean), lightly smoothed."""
    o = np.argsort(key)
    P, key = P[o], key[o]
    bins = np.floor((key - key[0]) / step).astype(int)
    out = np.array([P[bins == b].mean(0) for b in np.unique(bins)])
    if smooth and len(out) > 4:
        for k in range(3):
            out[:, k] = gauss1d(out[:, k], smooth)
    return out


def _rows_toward(GS, path, S, offs, toward, seed):
    """Double rows on the side of the path that `toward(point)` scores positive."""
    from lib import sweep
    T, Nn, B = sweep.rmf_frames(path)
    mid = len(path.co) // 2
    sign = 1.0 if toward(path.co[mid] + B[mid] * 3.0) > toward(path.co[mid] - B[mid] * 3.0) else -1.0
    return GS.rows(path, tuple(sign * o for o in offs), 3.4, 0.8, target=S, seed=seed)


def build_stitches(S, S_stays, Vu, Fu, last, ff, throat, zones, coll, side):
    """Stitch rows (gn_stitches, spec 02 §4.9): the toe cap's seam (two rows on the cap), the counter's top edge (two
    on the counter), the leather quarter's edge under the Cordura (two on the leather) and three rows on each stay
    (one by the throat edge, two by its back edge). Returns the Stitches."""
    from lib import gn_stitches as GS
    sd = 100 if side == "L" else 300
    s, t, h = ff.s_of(Vu), ff.t_of(Vu), ff.h_of(Vu)
    tc = np.interp(s, last.st, last.tc)
    out, info = [], {}
    gapm = throat.gap_mask(Vu) < 0.5
    above = h > ff.stack(s) + RAND["side"] + 4.0                       # above the rand
    # toe cap seam: sc = s_tip - 81
    sc = s + 0.0045 * (t - tc) ** 2
    P = iso_points(Vu, Fu, sc - (last.s_tip - 81.0), above)
    if len(P) > 8:
        path = GS.seam_path(S, ordered(P, ff.t_of(P)), step=1.0)
        out.append(_rows_toward(GS, path, S, (1.6, 5.4), lambda p: ff.s_of(p)[0], sd + 1))
        info["toecap_mm"] = round(float(path.s[-1]), 1)
    # counter top edge: h + 0.42 s = 97, s < 90
    P = iso_points(Vu, Fu, h + 0.42 * s - 97.0, above & (s < 88.0))
    if len(P) > 8:
        c = np.array([40.0, float(np.interp(40.0, last.st, last.tc))])
        ang = np.arctan2(ff.t_of(P) - c[1], -(ff.s_of(P) - c[0]))
        path = GS.seam_path(S, ordered(P, ang, step=0.08), step=1.0)
        out.append(_rows_toward(GS, path, S, (1.6, 5.4), lambda p: -(ff.h_of(p)[0] + 0.42 * ff.s_of(p)[0]), sd + 2))
        info["counter_mm"] = round(float(path.s[-1]), 1)
    # the leather quarter's top edge under the Cordura (quarter_h: h 98 rising toward the throat), each side
    for sgn in (1.0, -1.0):
        keep = gapm & (s > 70.0) & (sgn * (t - tc) > 0)
        P = iso_points(Vu, Fu, h - quarter_h(last, s), keep)
        if len(P) > 8:
            path = GS.seam_path(S, ordered(P, ff.s_of(P)), step=1.0)
            out.append(_rows_toward(GS, path, S, (1.6, 5.4), lambda p: -ff.h_of(p)[0], sd + 3 + int(sgn > 0)))
            info[f"quarter_{'lat' if sgn > 0 else 'med'}_mm"] = round(float(path.s[-1]), 1)
    # round 6: the mudguard's top edge (mud_h), two rows on the mudguard, each side, from behind the ball to the counter
    for sgn in (1.0, -1.0):
        keep = above & gapm & (s > 75.0) & (sc < last.s_tip - 84.0) & (sgn * (t - tc) > 0)
        P = iso_points(Vu, Fu, h - mud_h(ff, s), keep)
        if len(P) > 8:
            path = GS.seam_path(S, ordered(P, ff.s_of(P)), step=1.0)
            out.append(_rows_toward(GS, path, S, (1.6, 5.4), lambda p: -ff.h_of(p)[0], sd + 20 + int(sgn > 0)))
            info[f"mudguard_{'lat' if sgn > 0 else 'med'}_mm"] = round(float(path.s[-1]), 1)
    # round 10: the suede vamp's back edge (vamp_s), two rows on the vamp, each side, from the mudguard up to the stays
    for sgn in (1.0, -1.0):
        keep = above & gapm & (h > mud_h(ff, s) + 1.0) & (h < 112.0) & (sc < last.s_tip - 84.0) & (sgn * (t - tc) > 0)
        P = iso_points(Vu, Fu, s - vamp_s(ff, h), keep)
        if len(P) > 8:
            path = GS.seam_path(S, ordered(P, ff.h_of(P)), step=1.0)
            out.append(_rows_toward(GS, path, S, (1.6, 5.4), lambda p: ff.s_of(p)[0], sd + 30 + int(sgn > 0)))
            info[f"vamp_{'lat' if sgn > 0 else 'med'}_mm"] = round(float(path.s[-1]), 1)
    # the stays: one row 1.8 from the throat edge, two near the back edge
    Ls = np.linspace(2.0, throat.e1_L + 8.0, 40)
    for sgn in (1.0, -1.0):
        for k, off in enumerate((1.8, STAY_W - 5.2, STAY_W - 1.8)):
            a = sgn * (0.5 * throat.gap(Ls) + off)
            P, _ = throat.across(Ls, a, STAY_PROUD)
            path = GS.seam_path(S_stays, P, step=1.0)
            out.append(GS.running(path, 3.4, 0.8, seed=sd + 10 + k + (5 if sgn > 0 else 0)))
    st = GS.Stitches.join(out)
    info["stitches"] = len(st)
    info["thread_mm"] = round(st.thread_mm(), 1)
    return st, info


# --------------------------------------------------------------------------- materials


def grid_uv(V, n_th, n_phi):
    """UV.Real (metres) of the upper's grid: arc length round each row and down each column."""
    G = V.reshape(n_th, n_phi, 3)
    seg_u = np.linalg.norm(np.roll(G, -1, 1) - G, axis=2) * 0.001
    U = np.concatenate([np.zeros((n_th, 1)), np.cumsum(seg_u, axis=1)], axis=1)
    seg_v = np.linalg.norm(np.diff(G, axis=0), axis=2) * 0.001
    Vv = np.vstack([np.zeros((1, n_phi)), np.cumsum(seg_v, axis=0)])
    Vv = np.concatenate([Vv, Vv[:, :1]], axis=1)
    return U, -Vv


def set_loop_uv(ob, corner_uv):
    """corner_uv: one (u, v) per face corner in polygon order; returns False if the mesh's loops differ."""
    me = ob.data
    if len(corner_uv) != len(me.loops):
        return False
    lay = me.uv_layers.get("UV.Real") or me.uv_layers.new(name="UV.Real")
    lay.data.foreach_set("uv", np.asarray(corner_uv, np.float32).ravel())
    return True


def vertex_uv(ob, uv):
    """Per-vertex UV.Real (metres) spread to the loops."""
    me = ob.data
    vi = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", vi)
    return set_loop_uv(ob, np.asarray(uv)[vi])


def strip_uv(V):
    """A plain metric UV for a strip or tube built row by row: arc length along the first two axes it spans
    (principal components), good enough for a grain or weave at real scale."""
    c = V.mean(0)
    _, _, vt = np.linalg.svd(V - c, full_matrices=False)
    return (V - c) @ vt[:2].T * 0.001


def apply_library(built, side, ff, last, upper_info, say):
    """The take 1 boot recipes (scripts/lib/materials.py) on the round 2 geometry: leather and Cordura on the
    upper by its panels, leather on the stays and tongue, Cordura on the collar, the rand and outsole
    rubbers, the PU midsole, gunmetal hardware, the nylon lace; dust zones from the preset boot.toe (the left
    boot the dustier, as drawn). Returns the materials used, or raises (the caller falls back to flat)."""
    from lib import materials as M
    up = built["Upper"]
    me = up.data
    Vr = np.array([tuple(v.co) for v in me.vertices]) * 1000.0
    s, t, h = ff.s_of(Vr), ff.t_of(Vr), ff.h_of(Vr)
    # UV.Real on the upper from the grid
    n_th, n_phi, Fij, keepf, Vgrid = upper_info
    U, Vv = grid_uv(Vgrid, n_th, n_phi)
    corner = [(U[i, j], Vv[i, j]) for k in keepf for (i, j) in Fij[k]]
    if not set_loop_uv(up, corner):
        say(f"{side}: upper loops changed; UV.Real from strip_uv")
        vertex_uv(up, strip_uv(Vr))
    fm = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get("material_index", fm)
    att = me.attributes.get("polish") or me.attributes.new("polish", "FLOAT", "POINT")
    polish = np.maximum(0.85 * smoothstep(98.0, 92.0, h + 0.42 * s) * smoothstep(92.0, 86.0, s),
                        0.6 * smoothstep(last.s_tip - 80.0, last.s_tip - 70.0, s))
    att.data.foreach_set("value", polish.astype(np.float32))
    M.assign(up, "Leather.Boot.FullGrain", part="Boot", faces=np.nonzero(fm == 0)[0])
    M.assign(up, "Cordura.500D.Black", part="Boot", faces=np.nonzero(fm == 1)[0])
    if (fm == 3).any():   # round 10: the rubber toe cap moulded on the toe box
        M.assign(up, "Rubber.Rand.Black", part="Boot", faces=np.nonzero(fm == 3)[0])
    if (fm == 2).any():   # round 10: the suede vamp and mudguard
        M.assign(up, "Leather.Boot.FullGrain", part="Boot", faces=np.nonzero(fm == 2)[0], variant="Leather.Suede", **SUEDE)
    zones = {"toe": smoothstep(last.s_tip - 85.0, last.s_tip - 60.0, s) * smoothstep(85.0, 70.0, h),
             "vamp": smoothstep(last.s_tip - 140.0, last.s_tip - 110.0, s) * smoothstep(48.0, 62.0, h),
             "quarters": smoothstep(100.0, 90.0, h), "shaft_sides": smoothstep(90.0, 100.0, h),
             "collar_top": smoothstep(196.0, 206.0, h)}
    M.wear_zones(up, "boot.toe", zones)
    for k in ("Stays", "Tongue"):
        ob = built[k]
        vertex_uv(ob, strip_uv(np.array([tuple(v.co) for v in ob.data.vertices]) * 1000.0))
        M.assign(ob, "Leather.Boot.FullGrain", part="Boot")
    ob = built["Collar"]
    vertex_uv(ob, strip_uv(np.array([tuple(v.co) for v in ob.data.vertices]) * 1000.0))
    M.assign(ob, "Cordura.500D.Black", part="Boot")
    M.wear_zones(ob, "boot.toe", {"collar_top": 1.0})
    rand = built["Rand"]
    Rr = np.array([tuple(v.co) for v in rand.data.vertices]) * 1000.0
    bump = smoothstep(last.s_tip - 70.0, last.s_tip - 40.0, ff.s_of(Rr))
    a2 = rand.data.attributes.new("bumper", "FLOAT", "POINT")
    a2.data.foreach_set("value", bump.astype(np.float32))
    M.assign(rand, "Rubber.Rand.Black", part="Boot")
    M.wear_zones(rand, "boot.toe", {"bumper_top": bump, "quarters": 1.0})
    so = built["Sole"]
    sm = np.empty(len(so.data.polygons), np.int32)
    so.data.polygons.foreach_get("material_index", sm)
    M.assign(so, "EVA.Midsole.BlueGrey", part="Boot", faces=np.nonzero(sm == 0)[0])
    M.assign(so, "Rubber.Outsole.Black", part="Boot", faces=np.nonzero(sm == 1)[0])
    M.assign(built["Lugs"], "Rubber.Outsole.Black", part="Boot")
    M.assign(built["Eyelets"], "Metal.Gunmetal", part="Boot")
    la = built["Laces"]
    vertex_uv(la, strip_uv(np.array([tuple(v.co) for v in la.data.vertices]) * 1000.0))
    M.assign(la, "Lace.Nylon.Black", part="Boot")
    M.wear_zones(la, "boot.toe", {"laces": 1.0})
    for ob in built.values():
        ob["wear_dust_scale"] = 1.0 if side == "L" else 0.7
        # drop the flat round 1 slots the library replaced (keeps the cache lean)
        used = set()
        pm = np.empty(len(ob.data.polygons), np.int32)
        ob.data.polygons.foreach_get("material_index", pm)
        used = set(pm.tolist())
        for i in range(len(ob.data.materials) - 1, -1, -1):
            if i not in used and i == len(ob.data.materials) - 1:
                ob.data.materials.pop(index=i)
    return sorted({m.name for ob in built.values() for m in ob.data.materials if m})


# --------------------------------------------------------------------------- main


def _isolate_foot(body, side, top_mm=300.0):
    """One foot of the evaluated rest body below top_mm, as a render copy (the other foot hidden from X-ray views)."""
    import bmesh
    import bpy
    sg = 1.0 if side == "L" else -1.0
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not (sg * v.co.x > 0.03 and v.co.z < top_mm / 1000.0)],
                     context="VERTS")
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    return bpy.data.objects.new(f"Aux.Foot.{side}", me)


def slice_edges(V, F, axis, value):
    """Points where the mesh's edges cross the plane coordinate[axis] = value (V (n, 3), F faces)."""
    E = C.edges_of(F)
    a, b = V[E[:, 0], axis] - value, V[E[:, 1], axis] - value
    m = a * b < 0
    u = a[m] / (a[m] - b[m])
    return V[E[m, 0]] + (V[E[m, 1]] - V[E[m, 0]]) * u[:, None]


def sections(body, lasts, uppers, path):
    """Section data in frame F for the left and right feet (JSON for the plotting step, renders/boots/sections_*.png):
    the long section through the 2nd toe's axis (x 0), across the ball line, across the heel 35 mm ahead of the
    pternion; the loaded bare foot, the last, and the upper's outer surface."""
    import bpy
    from stages.foot import footmetrics as fm, sock as SK
    fm._INDEX.clear()
    out = {}
    for side, rec in lasts.items():
        f = rec["frame"]
        plates = [bpy.data.objects[n] for n in (f"Foot.{side}.Nail.{k}" for k in range(1, 6)) if n in bpy.data.objects]
        Vf, Tf = SK.skin_read(body, f, 1.0, plates)
        G = rec["G_f"].reshape(-1, 3)
        Vu, Fu = uppers[side]
        Uf = f.to_f(Vu)
        b1, b5 = rec["markers_f"]["Ball1"], rec["markers_f"]["Ball5"]
        yb = 0.5 * (b1[1] + b5[1])
        cuts = {"long_x0": (0, 0.0, (1, 2)), "ball": (1, yb, (0, 2)), "heel": (1, -35.0, (0, 2))}
        o = {}
        for name, (ax, val, keep) in cuts.items():
            o[name] = {"skin": slice_edges(Vf, [tuple(t) for t in Tf], ax, val)[:, list(keep)].round(2).tolist(),
                       "last": slice_edges(G, rec["faces"], ax, val)[:, list(keep)].round(2).tolist(),
                       "upper": slice_edges(Uf, Fu, ax, val)[:, list(keep)].round(2).tolist(),
                       "axes": ["xyz"[k] for k in keep], "at": round(float(val), 2)}
        o["insole_z"] = rec["insole_z"]
        o["measure"] = rec["measure"]
        out[side] = o
    with open(path, "w") as fh:
        json.dump(out, fh)
    return path


def render_round3(coll, lasts_path, extra, say):
    """The round's renders: rest clay x3 and the hero crops (render_part), closeups of the left boot (lateral, front
    three-quarter, medial-back, below, the throat and laces, the right boot's medial profile), and the left last
    over the foot in X-ray (lateral and top)."""
    import bpy
    C.render_part(TAG, coll, (0, -40, 90), (700, 420), crops=("ref.boots_feet", "ref.soldier_full"))
    rig_ = bpy.data.objects[C.RIG]
    C.rest_pose(rig_)
    out_dir = os.path.join(C.RENDERS, TAG)
    for side, views in (("L", None), ("R", None)):
        sc_ = bpy.data.collections.new(f"Aux.Boot{side}")
        bpy.context.scene.collection.children.link(sc_)
        for o in coll.all_objects:
            if f".{side}." in o.name:
                sc_.objects.link(o)
        ff = extra[side]["ff"]
        cen = ff.xyz(140.0, 20.0, 60.0)
        if side == "L":
            th = extra[side]["throat"]
            q = th.at(np.array([th.e1_L * 0.5]))[0][0]
            shots = (("L_lateral", ff.t * 1.0 + np.array([0, 0, 0.12]), cen, 1150.0, 85.0),
                     ("L_front34", ff.u * 0.75 + ff.t * 0.55 + np.array([0, 0, 0.35]), cen, 1150.0, 85.0),
                     ("L_medial_back", -ff.u * 0.6 - ff.t * 0.7 + np.array([0, 0, 0.3]), cen, 1150.0, 85.0),
                     ("L_rear", -ff.u + np.array([0, 0, 0.15]), cen, 1150.0, 85.0),
                     ("L_below", np.array([0.0, 0.0, -1.0]) + ff.t * 0.02, cen, 1150.0, 85.0),
                     ("L_throat", ff.u * 0.8 + ff.t * 0.2 + np.array([0, 0, 0.45]), q, 420.0, 85.0),
                     ("L_laces_front", ff.u * 1.0 + np.array([0, 0, 0.25]), q, 520.0, 85.0))
        else:
            shots = (("R_medial", -ff.t * 1.0 + np.array([0, 0, 0.12]), cen, 1150.0, 85.0),
                     ("R_front34", ff.u * 0.75 - ff.t * 0.55 + np.array([0, 0, 0.35]), cen, 1150.0, 85.0))
        for name, d, tgt, dist, lens in shots:
            d = d / np.linalg.norm(d)
            restore = C.visible_only([sc_], keep_body=False)
            C._workbench(bpy.context.scene, "OBJECT", bg=(0.86, 0.86, 0.84))
            for ob in sc_.all_objects:
                ob.color = (*(ob.get("sgt_clay") or (0.4, 0.4, 0.4)), 1.0)
            cam = C._aux_camera()
            bpy.context.scene.camera = cam
            cam.data.type, cam.data.lens, cam.data.sensor_fit = "PERSP", lens, "AUTO"
            bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 1100, 800
            C._look(cam, np.asarray(tgt) + d * dist, tgt)
            C._render(os.path.join(out_dir, f"{TAG}_closeup_{name}.png"))
            restore()
        bpy.data.collections.remove(sc_)
    # the left last over the bare foot (X-ray), lateral and from above, then the boot over the last
    with bpy.data.libraries.load(lasts_path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n == "Boot.L.Last"]
    lc = bpy.data.collections.new("Aux.Last")
    bpy.context.scene.collection.children.link(lc)
    for ob in dst.objects:
        lc.objects.link(ob)
        ob.hide_render = False
        ob["sgt_clay"] = (0.35, 0.55, 0.85)
    sc = bpy.context.scene
    ff = extra["L"]["ff"]
    cen = ff.xyz(150.0, 5.0, 40.0)
    body = bpy.data.objects[C.BODY]
    foot = _isolate_foot(body, "L")
    lc.objects.link(foot)
    nails = [o for o in bpy.data.objects if o.name.startswith("Foot.L.Nail.")]
    for name, d, with_boot in (("last_L_lateral", ff.t * 1.0, False), ("last_L_top", np.array([0.0, 0.0, 1.0]) + ff.u * 0.01, False),
                               ("last_L_in_boot_lateral", ff.t * 1.0, True)):
        keep = [lc] + ([coll] if with_boot else [])
        restore = C.visible_only(keep, keep_body=False)
        for o in nails:
            o.hide_render = False
        C._workbench(sc, "OBJECT", bg=(0.95, 0.95, 0.94))
        sh = sc.display.shading
        sh.show_xray, sh.xray_alpha = True, 0.35
        for o in lc.all_objects:
            o.color = (0.35, 0.55, 0.85, 1.0)
        foot.color = (0.85, 0.45, 0.40, 1.0)
        if with_boot:
            for o in coll.all_objects:
                o.hide_render = not o.name.startswith("Boot.L.")
                o.color = (0.3, 0.3, 0.3, 1.0)
        cam = C._aux_camera()
        sc.camera = cam
        cam.data.type, cam.data.ortho_scale, cam.data.sensor_fit = "ORTHO", 0.36, "AUTO"
        sc.render.resolution_x, sc.render.resolution_y = 1200, 900 if "top" not in name else 1000
        C._look(cam, cen + d / np.linalg.norm(d) * 1500.0, cen)
        C._render(os.path.join(out_dir, f"{TAG}_{name}.png"))
        sh.show_xray = False
        restore()
    bpy.data.collections.remove(lc)


def _args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(name, default):
        return argv[argv.index(name) + 1] if name in argv else default
    return argv, opt


def main():
    import bpy
    import time
    from stages.foot import marks
    t0 = time.perf_counter()
    args, opt = _args()
    base = opt("--base", None)
    if base:
        C.BASE_BLEND = os.path.join(C.PROJECT, base)
    tag = opt("--tag", TAG)
    body, rig = C.open_base()
    FootFrame.LANDMARKS = marks.foot_landmarks(body)
    coll = C.part_collection(PART, "Part.Boots")
    bd = C.body_data(body)
    bvh0 = C.skin_bvh(bd)
    mats = {k: C.flat_material(f"Boot.Mat.{k.title()}", h, {"leather": 0.45, "metal": 0.35, "midsole": 0.35}.get(k, 0.8))
            for k, h in COLOURS.items()}
    mats["metal"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.8
    say = lambda *a: C.say(TAG, *a)
    lasts, knit = build_socks_and_lasts(body, rig, coll, say)
    say(f"socks and lasts in {time.perf_counter() - t0:.1f} s")
    objs, meas, extra, uppers = [], {}, {}, {}
    for side in ("L", "R"):
        ff = FootFrame(side)
        last = Last(ff, last_cloud(lasts[side]), say)
        P, F, rim_row, O = build_upper(last, ff)
        E_ = C.edges_of(F)
        P = C.despike(P, E_, factor=2.5, iters=4)
        pin = np.zeros(len(P), bool)
        pin[rim_row] = True
        P = C.taubin(P, E_, iters=6, lam=0.5, mu=-0.53, pin=pin)
        throat = Throat(last, ff, O)
        Ls_, a_ = lace_positions(throat)
        say(f"{side}: throat {throat.Lmax:.0f} mm long, E1 at L {throat.e1_L:.0f}, pitch {throat.pitch:.1f}; lace rows at h "
            f"{np.round(ff.h_of(throat.at(Ls_)[0]), 0).tolist()}, s {np.round(ff.s_of(throat.at(Ls_)[0]), 0).tolist()}")
        Vu, fmat, attrs = decorate_upper(last, ff, P, F, throat, side)
        # the floor of the upper lies inside the sole: drop the faces on the bottom cut
        on_cut = (Vu[:, 2] - last.z_cut(P)) < 0.8
        keepf = [i for i, f in enumerate(F) if not on_cut[list(f)].all()]
        n_th_, n_phi_, Fij_ = build_upper.grid
        upper_info = (n_th_, n_phi_, Fij_, keepf, Vu.copy())
        F2 = [F[i] for i in keepf]
        fm2 = [int(fmat[i]) for i in keepf]
        Vu2, F2, used = C.submesh(Vu, F2, np.ones(len(Vu), bool))
        # safety: the skin must stay inside with 2.5 mm (signs by ray parity: the nearest face's normal misreads
        # points behind the Achilles' concave profile as inside, and pushing them made spikes in round 3's first run)
        d0 = robust_signed(Vu2, bvh0)
        E2 = C.edges_of(F2)
        bad = d0 < 0.0
        for _ in range(6):
            if not bad.any():
                break
            acc = np.zeros_like(Vu2)
            deg = np.zeros(len(Vu2))
            np.add.at(acc, E2[:, 0], Vu2[E2[:, 1]])
            np.add.at(acc, E2[:, 1], Vu2[E2[:, 0]])
            np.add.at(deg, E2[:, 0], 1)
            np.add.at(deg, E2[:, 1], 1)
            Vu2[bad] = acc[bad] / np.maximum(deg[bad], 1)[:, None]
        if (d0 < 0.0).any():
            bv = Vu2[d0 < 0.0]
            say(f"{side}: {int((d0 < 0).sum())} upper vertices read inside the skin: s {np.round(np.percentile(ff.s_of(bv), [0, 50, 100]), 0).tolist()}, "
                f"t {np.round(np.percentile(ff.t_of(bv), [0, 50, 100]), 0).tolist()}, h {np.round(np.percentile(ff.h_of(bv), [0, 50, 100]), 0).tolist()}")
        Vu2 = robust_push(Vu2, bvh0, 2.5)
        # round 10: the narrower upper (UPPER_W_MAX, NOSE_RELAX) came close enough to the forefoot that the sock (its
        # Solidify grows outward to 2.2-3.0 mm) poked through the upper's inner face as a lump at the 5th metatarsal
        # head: clear the skin by SOCK_CLEAR there, then smooth the pushed patch (Taubin, 3 rings round it) and push
        # again, so the clearance shows as a soft swell, not a bump
        V0 = Vu2.copy()
        Vu2 = robust_push(Vu2, bvh0, SOCK_CLEAR)
        moved = np.linalg.norm(Vu2 - V0, axis=1) > 0.05
        if moved.any():
            reg = moved.copy()
            for _ in range(4):
                g = reg.copy()
                g[E2[:, 0]] |= reg[E2[:, 1]]
                g[E2[:, 1]] |= reg[E2[:, 0]]
                reg = g
            Vu2 = C.taubin(Vu2, E2, iters=8, lam=0.5, mu=-0.53, pin=~reg)
            Vu2 = robust_push(Vu2, bvh0, SOCK_CLEAR)
        say(f"{side}: {int(moved.sum())} upper vertices cleared to {SOCK_CLEAR} mm of the skin (the sock), "
            f"{int(reg.sum()) if moved.any() else 0} smoothed")
        # and the last inside the upper's inner face (the upper is 1.6 thick inward): clearance from the last
        lf = lasts[side]["faces"] if lasts[side]["frame"].s > 0 else [tuple(reversed(q)) for q in lasts[side]["faces"]]
        bl = C.bvh_from(lasts[side]["G_w"].reshape(-1, 3), lf)
        dl, _ = C.signed_dist(Vu2, bl)
        say(f"{side}: upper {len(Vu2)} verts; {int((d0 < 2.5).sum())} pushed out to 2.5 mm from the skin (min was "
            f"{d0.min():.1f}); upper outer face to the last: min {dl.min():.1f}, 1st percentile {np.percentile(dl, 1):.1f} mm")
        up = C.mesh_object(f"Boot.{side}.Upper", Vu2, F2, coll, mats=[mats["leather"], mats["cordura"], mats["suede"],
                                                                                  mats["rubber"]],
                           face_mat=fm2)
        crease = attrs["crease"][used]
        att = up.data.attributes.new("crease", "FLOAT", "POINT")
        att.data.foreach_set("value", crease.astype(np.float32))
        built = {"Upper": up}
        Vs, Fs = build_stays(throat)
        built["Stays"] = C.mesh_object(f"Boot.{side}.Stays", Vs, Fs, coll, mat=mats["leather"])
        Vt, Ft = build_tongue(last, ff, throat)
        built["Tongue"] = C.mesh_object(f"Boot.{side}.Tongue", Vt, Ft, coll, mat=mats["leather"])
        Vc, Fc = build_collar(last, ff, P, rim_row, throat)
        built["Collar"] = C.mesh_object(f"Boot.{side}.Collar", Vc, Fc, coll, mat=mats["collar"])
        Vr, Fr = build_rand(last, ff)
        built["Rand"] = C.mesh_object(f"Boot.{side}.Rand", Vr, Fr, coll, mat=mats["rubber"])
        Vso, Fso, smat, outline, nrm_out = build_sole(last, ff)
        built["Sole"] = C.mesh_object(f"Boot.{side}.Sole", Vso, Fso, coll, mats=[mats["midsole"], mats["outsole"]],
                                      face_mat=smat, smooth=False)
        Vl, Fl = build_lugs(last, ff, outline, nrm_out)
        built["Lugs"] = C.mesh_object(f"Boot.{side}.Lugs", Vl, Fl, coll, mat=mats["outsole"], smooth=False)
        S_up, S_st = C_surface(built["Upper"]), C_surface(built["Stays"])
        try:
            eo, ho, holes = build_hardware_lib(throat, S_st, coll, side)
            built["Eyelets"], built["Hooks"] = eo, ho
        except Exception as e:  # noqa: BLE001 - round 2's simple hardware on any library problem
            import traceback
            traceback.print_exc()
            say(f"{side}: library hardware failed ({type(e).__name__}: {e}); round 2's rings and hooks")
            (Ve, Fe), holes = build_hardware(throat)
            built["Eyelets"] = C.mesh_object(f"Boot.{side}.Eyelets", Ve, Fe, coll, mat=mats["metal"])
        Vla, Fla = build_laces(throat, holes)
        built["Laces"] = C.mesh_object(f"Boot.{side}.Laces", Vla, Fla, coll, mat=mats["lace"])
        try:
            lib_mats = apply_library(built, side, ff, last, upper_info, say)
            say(f"{side}: library materials: {', '.join(lib_mats)}")
        except Exception as e:  # noqa: BLE001 - the flat colours stay on any library problem
            import traceback
            traceback.print_exc()
            say(f"{side}: library materials failed ({type(e).__name__}: {e}); flat colours kept")
        gear, st_info, strap_info = [], {}, {}
        try:
            from lib import gn_stitches as GS
            sobs, kst, tacks, strap_info = build_strap(S_up, last, ff, throat, coll, side)
            st, st_info = build_stitches(S_up, S_st, Vu2, F2, last, ff, throat, attrs["zones"], coll, side)
            built["Stitches"] = GS.stitch_object(f"Boot.{side}.Stitches", GS.Stitches.join([st] + kst), part="Boot",
                                                 radius=0.2, sink=0.1, bow=0.15, coll=coll)
            built["Tacks"] = GS.tack_object(f"Boot.{side}.Tacks", GS.Stitches.join(tacks), part="Boot", coll=coll)
            for ob in sobs:
                built[ob.name.split(".")[-1]] = ob
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            say(f"{side}: strap or stitches failed ({type(e).__name__}: {e})")
        for k, ob in built.items():
            ob["sgt_clay"] = CLAY.get(k, (0.30, 0.30, 0.31))
            bake_transform(ob)           # round 3 workaround; common.load_part keeps transforms since round 4 (harmless)
            if k in ("Sole", "Lugs"):
                C.bind(ob, body, rig, only=[f"foot.{side}"],
                       collapse={"toe*": f"foot.{side}", f"lowerleg02.{side}": f"foot.{side}"})
            else:
                C.bind(ob, body, rig, collapse={"toe*": f"foot.{side}"})
        n_fixed = {k: fill_unweighted(built[k], built["Upper"]) for k in built if k != "Upper"}
        if any(n_fixed.values()):
            say(f"{side}: unweighted vertices given the upper's nearest weights: "
                f"{ {k: v for k, v in n_fixed.items() if v} }")
        sock = bpy.data.objects[f"Sock.{side}.Body"]
        C.bind(sock, body, rig)
        from stages.foot import sock as SK
        SK.add_modifiers(sock, knit)
        built["Sock"] = sock
        C.solidify(built["Upper"], 1.6, inward=True)
        C.solidify(built["Stays"], 2.0, inward=True)
        C.solidify(built["Tongue"], 6.0, inward=True)
        C.solidify(built["Rand"], 2.0, inward=True)
        for k in ("Upper", "Stays", "Tongue", "Collar", "Rand"):
            C.subsurf(built[k], 1)
        objs += list(built.values())
        L = float(np.ptp(ff.s_of(outline)))
        W = float(np.ptp(ff.t_of(outline)))
        s_line = ff.s_ball
        near = np.abs(ff.s_of(outline) - s_line) < 6.0
        # round 10: the widest SECTION across the foot (10 mm stations); round 9's "outsole_width_max_mm" (141-147)
        # was the outline's whole extent across the foot frame's axis, which the sole's own slant (a few degrees off
        # the heel-toe landmark line) inflates by about 15-20 mm; kept under its old key for comparison
        so_s, so_t = ff.s_of(outline), ff.t_of(outline)
        sec = [float(np.ptp(so_t[np.abs(so_s - x) < 5.0])) for x in np.arange(so_s.min() + 5.0, so_s.max() - 5.0, 5.0)
               if (np.abs(so_s - x) < 5.0).sum() >= 2]
        meas[side] = {"outsole_length_mm": round(L + 3.0, 1), "outsole_width_max_mm": round(W + 3.0, 1),
                      "outsole_section_width_max_mm": round(max(sec) + 3.0, 1),
                      "outsole_width_at_ball_mm": round(float(np.ptp(ff.t_of(outline[near]))) + 3.0, 1) if near.any() else None,
                      "upper_length_mm": round(last.s_tip - last.s_back, 1),
                      "foot_length_mm": round(lasts[side]["measure"]["foot_length_mm"], 1), "s_ball_mm": round(ff.s_ball, 1),
                      "last": lasts[side]["measure"],
                      "rim_above_floor_at_heel_mm": round(RIM_Z + HEEL_SEAT, 1),
                      "shaft_rim_mm": [round(2 * float(np.interp(RIM_Z, last.zs, last.a)), 1),
                                       round(2 * float(np.interp(RIM_Z, last.zs, last.b)), 1)],
                      "throat_E1_height_mm": round(float(ff.h_of(throat.at(np.array([throat.e1_L]))[0])[0]), 1),
                      "lugs_faces": len(Fl), "strap": strap_info, "stitches": st_info}
        extra[side] = {"ff": ff, "last": last, "throat": throat}
        uppers[side] = (Vu2, F2)
    sec_path = sections(body, lasts, uppers, os.path.join(C.PARTS_DIR, f"{tag}_sections.json"))
    lasts_path = os.path.join(C.PARTS_DIR, f"{tag}_lasts.blend")
    lcoll = save_lasts(lasts, lasts_path, say)
    check = [o for o in objs if o.name.endswith((".Upper", ".Collar", ".Tongue", ".Sole"))]
    rest = C.clearance(check, body, "rest")
    used = C.apply_hero_pose(rig)
    posed = C.clearance(check, body, "hero pose")
    floor = {}
    for side in ("L", "R"):
        Vp, _ = C.evaluated_world_mm(bpy.data.objects[f"Boot.{side}.Lugs"])
        Vq, _ = C.evaluated_world_mm(bpy.data.objects[f"Boot.{side}.Sole"])
        floor[side] = {"lug_min_z_mm": round(float(Vp[:, 2].min()), 1),
                       "lug_p2_z_mm": round(float(np.percentile(Vp[:, 2], 2)), 1),
                       "sole_base_min_z_mm": round(float(Vq[:, 2].min()), 1)}
        so = bpy.data.objects[f"Boot.{side}.Sole"]
        R0 = np.array([tuple(v.co) for v in so.data.vertices]) * 1000.0
        sr = FootFrame(side).s_of(R0)
        d = Vq[int(np.argmax(sr)), :2] - Vq[int(np.argmin(sr)), :2]
        floor[side]["posed_heading_deg_from_-Y_toward_his_left(+X)"] = round(math.degrees(math.atan2(d[0], -d[1])), 1)
        floor[side]["posed_toe_tip_mm"] = [round(float(x)) for x in Vq[int(np.argmax(sr))]]
        floor[side]["posed_length_in_plan_mm"] = round(float(np.linalg.norm(d)), 1)
    say("posed soles:", json.dumps(floor))
    C.rest_pose(rig)
    say(json.dumps(meas, default=str))
    bpy.data.collections.remove(lcoll)
    C.save_part(tag, coll, {"round": 3, "base": os.path.relpath(C.BASE_BLEND, C.PROJECT), "measure_mm": meas,
                            "posed_soles": floor, "clearance_rest": rest, "clearance_posed": posed, "pose": used,
                            "lasts": os.path.relpath(lasts_path, C.PROJECT), "seconds": round(time.perf_counter() - t0, 1)})
    if "--no-render" not in args:
        render_round3(coll, lasts_path, extra, say)


def bake_transform(ob):
    """Move an object's own transform into its mesh (round 3: the ladder-lock came from gear_hardware with a
    matrix; common.load_part reads matrix_world from the freshly loaded cache before any depsgraph update, gets the
    identity and so put the buckles on the floor between the feet in the assembly). Round 4: common.save_part and
    load_part now carry object transforms themselves; this stays, harmless."""
    from mathutils import Matrix
    if ob.type != "MESH" or ob.parent is not None:
        return
    M = ob.matrix_basis.copy()
    if all(abs(M[i][j] - (1.0 if i == j else 0.0)) < 1e-9 for i in range(4) for j in range(4)):
        return
    ob.data.transform(M)
    ob.matrix_basis = Matrix.Identity(4)


def fill_unweighted(ob, ref):
    """Vertices the weight transfer left with no weight (they would stay at rest under the Armature: round 3's
    stitch carriers drew threads from the posed boot back to its rest place) take the weights of the nearest
    vertex of ref (the upper). Returns how many. Round 4: common.bind now fills such vertices from the nearest skin
    vertex itself, so this normally finds none; it stays as a check."""
    from mathutils import kdtree
    me = ob.data
    if not len(me.vertices):
        return 0
    zero = [v.index for v in me.vertices if sum(e.weight for e in v.groups) < 1e-6]
    if not zero:
        return 0
    rv = ref.data.vertices
    kd = kdtree.KDTree(len(rv))
    for v in rv:
        kd.insert(v.co, v.index)
    kd.balance()
    names = {g.index: g.name for g in ref.vertex_groups}
    for i in zero:
        _, j, _ = kd.find(me.vertices[i].co)
        for e in rv[j].groups:
            nm = names[e.group]
            g = ob.vertex_groups.get(nm) or ob.vertex_groups.new(name=nm)
            g.add([i], e.weight, "REPLACE")
    return len(zero)


def C_surface(ob):
    from lib import sweep
    return sweep.Surface(ob)


if __name__ == "__main__":
    main()
