"""Boots, round 2: a pair of LOWA Zephyr MK2 GTX Hi TF class tactical boots (210 mm outside height, a
leather and Cordura upper on a two-density PU midsole and a lugged rubber outsole, padded collar, gusseted
tongue, five eyelets and two speed hooks), built around the rest feet. Notes: scripts/parts/boots.md.

  "$SGT_BLENDER" -b --python scripts/parts/boots.py [-- --no-render]
  -> cache/parts/boots.blend (Part.Boots: Boot.{L,R}.Upper, .Stays, .Tongue, .Collar, .Rand, .Sole, .Lugs,
     .Eyelets, .Laces), cache/parts/boots.json, renders/boots/*.png

Frame: the boot is built in the REST body's frame with its footbed under the rest foot (heel seat 36 mm,
ball seat 24 mm, common.BOOT), so in rest the soles reach below z = 0; round 0's hero pose lifts each foot
onto those seats and the soles land on the floor (checked and reported here). Coordinates along the foot:
s (mm from the heel point toward the toe landmark), t (lateral, outward), z (rest).

The upper is a shoe last's form, not the skin's: the foot's skin is offset 5 mm and sliced across the foot
every 4 mm; each slice is fitted with a superellipse arch (centre, half width, height above a base inside
the sole) that contains every point; the arches are smoothed along the foot by an upper envelope (so the
toes and the arch hollow vanish under a smooth toe box and instep), and the ends are closed by
half-ellipses (a 48 mm rounded toe, 10 mm past the offset toes, and a rounded heel). The shaft is a stack
of horizontal ellipses (at least the drawn 128 x 100 to 138 x 106, centred on the leg, containing the
offset ankle and shin). The two are joined by a smooth union (an implicit field), cut at the rim (with an
Achilles notch) and at the sole top, and meshed by casting rays from a point inside (the first row is the
rim, so the opening has a clean edge). Leather overlays (toe cap, heel counter, quarters) stand 0.8 mm proud
of the Cordura shaft panels, and three flex creases cross the vamp. The lace stays are separate strips
standing on the upper either side of the throat, the tongue shows between them and rises 10 mm above the
rim, the padded collar rolls round the rim behind the stays. Five round eyelets and two speed hooks per
side, a criss-crossed round lace over the tongue. The sole: the upper's outline at the midsole top grown
3 mm, an outsole cup with a 5 mm lug layer (perimeter teeth wrapping up the sidewall, forefoot chevrons,
waist bars, heel blocks and the heel breast), toe spring 15 mm, the PU midsole stripe, and a rubber rand on
the upper rising into a toe bumper with a lip. Upper, stays, tongue, collar, rand, eyelets and laces take
weights from the body (toes merged into the foot); sole and lugs are rigid on the foot bone.
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
UPPER_OFF = 5.0                                  # skin -> upper outer surface: leather 2 + lining 1.5 + air 1.5
TOP_EXTRA = 1.0                                  # more over the toes and the instep (toe puff, tongue)
TOE_ALLOW = 10.0                                 # past the offset toe: the last's toe room (outsole ~303)
HEEL_ALLOW = 3.0                                 # the counter's thickness behind the heel
NOSE, HEEL_END = 50.0, 34.0                      # lengths of the rounded toe and heel ends
SEC_N = 2.7                                      # superellipse exponent of the arches (2 = ellipse)
TOE_SPRING = 15.0
STACK_HEEL, STACK_BALL, STACK_TOE = 40.0, 21.0, 19.0   # floor -> midsole stripe top; the rand rises above it
RAND = {"side": 10.0, "heel": 12.0, "toe": 26.0, "proud": 2.5, "lip": 1.0}
LUG, SIDEWALL, CUP = 5.0, 3.0, 6.0               # lug height, sole grown past the upper, outsole cup wall
SHAFT = [(74.0, (64.0, 50.0)), (122.0, (68.0, 52.0)), (RIM_Z, C.BOOT["shaft_rim_ab"])]   # rest z: (front-back, side)
SHAFT_ZLO = -60.0                                # the shaft runs down into the sole (tapered), so no ledge
K_UNION = 16.0                                   # smooth-union radius (mm) where shaft meets instep
NOTCH = 6.0                                      # Achilles notch at the back of the rim
COLLAR = {"tall": 22.0, "thick": 10.0}
LACE_PITCH, LACE_TOP = 22.5, 8.0                 # eyelet pitch along the throat, top hook below the rim
E1_S = 0.60                                      # the lowest eyelet at 57 % of the boot's length from the heel
GAP = (30.0, 44.0)                               # throat gap between the stays at E1 and at the top
STAY_W, STAY_PROUD = 22.0, 2.4
LACE_R = 2.0
COLOURS = {"leather": "#201e1c", "cordura": "#1c1b1a", "collar": "#1b1b1c", "midsole": "#262a30",
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
            m = np.abs(sf - x) < 5.0
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
            Hn = 8.0 + (H0 - 8.0) * e ** 1.1
            f = max(Hn - zk[0], 1.0) / max(H0 - zk[0], 1.0)
            zz = zk[0] + (zk - zk[0]) / f
            WM[i] = np.maximum(WM_req[i], np.interp(zz, zk, WM[jn], right=0.0) * e ** 0.9)
            WL[i] = np.maximum(WL_req[i], np.interp(zz, zk, WL[jn], right=0.0) * e ** 0.9)
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
        d = np.maximum(np.abs(t - tc) - W, z - zb - np.interp(s, st, self.h))
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


def skin_cloud(bd, side, bvh0):
    """The foot and lower leg's skin (refined) and its normals; the offset cloud the last must contain."""
    V0 = bd["V"]
    sg = 1.0 if side == "L" else -1.0
    leg = C.weight_sum(bd, C.is_leg)
    keep = bd["in_body"] & (leg > 0.5) & (V0[:, 2] < RIM_Z + 120.0) & (np.sign(V0[:, 0]) == sg)
    V, F, _ = C.submesh(V0, bd["F"], keep)
    V, F = C.bisect(V, F, (0, 0, RIM_Z + 60.0), (0, 0, 1), keep="below")
    V, F, N = C.refine_on_skin(V, F, bvh0, cuts=2)
    off = UPPER_OFF + TOP_EXTRA * np.clip(N[:, 2], 0, 1)
    return V, N, V + N * off[:, None]


# --------------------------------------------------------------------------- the upper


def build_upper(last, ff, n_phi=240, n_th=210):
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
    u = np.linspace(0.0, 1.0, n_th) ** 1.15                  # rows a little denser near the rim
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


def decorate_upper(last, ff, P, F, throat):
    """Overlays, creases and the throat: displacement along the field's normal; face materials."""
    N = last.normal(P)
    s, t, h = ff.s_of(P), ff.t_of(P), ff.h_of(P)
    tc = np.interp(s, last.st, last.tc)
    sc = s + 0.0045 * (t - tc) ** 2                           # stations bowed back toward the sides
    toecap = smoothstep(last.s_tip - 82.0, last.s_tip - 80.0, sc)
    counter = smoothstep(98.0, 96.0, h + 0.42 * s) * smoothstep(92.0, 88.0, s)
    # Cordura shaft panels above the quarters (leather below 98 mm, the counter, the stays and backstrap)
    dback = np.abs(t - last.rim_c[1])
    backstrap = smoothstep(11.0, 9.0, dback) * smoothstep(last.rim_c[0] - 20.0, last.rim_c[0] - 40.0, s)
    cordura = smoothstep(97.0, 99.0, h) * (1 - backstrap) * (1 - counter)
    lift = 0.8 * (1 - cordura) + 0.8 * toecap + 0.8 * counter
    # flex creases across the vamp (spec 02 §3.5): three folds behind the toe cap, deeper laterally
    side = smoothstep(42.0, 58.0, h) * smoothstep(0.95, 0.6, np.abs(t - tc) / np.maximum(np.interp(s, last.st, last.w), 1))
    hc = np.zeros(len(P))
    rel = sc - ff.s_ball
    for s0, amp, ph in ((-14.0, 1.0, 0.0), (-2.0, 0.85, 1.7), (9.0, 0.6, 3.1)):
        along = amp * (0.65 + 0.35 * np.sin((t - tc) / 7.0 + ph)) * (0.75 + 0.25 * smoothstep(-30, 30, t - tc))
        hc += along * (0.45 * np.exp(-((rel - s0 - 5.5) / 3.5) ** 2) - np.exp(-((rel - s0) / 1.5) ** 2))
    hc *= 1.6 * side
    # the throat: between the stays the tongue and gussets sit 1.2 mm below the quarters
    tongue = throat.gap_mask(P) * 1.2
    disp = lift + hc - tongue
    V = P + N * disp[:, None]
    fc = np.array([cordura[list(f)].mean() for f in F])
    return V, (fc > 0.5).astype(int), {"crease": smoothstep(0.15, 0.6, -hc)}


class Throat:
    """The lace throat: a centre line on the upper from the rim down the shaft front and over the instep,
    the lateral direction along it, and points across it at a given distance (cast onto the upper)."""

    def __init__(self, last, ff, O):
        self.last, self.ff, self.O = last, ff, O
        ir = int(np.argmin(np.abs(last.zs - RIM_Z)))
        top = ff.xyz(last.cs[ir] + last.a[ir] + 30.0, last.ct[ir], RIM_Z - 1.0)
        s_mid = 0.5 * (last.cs[ir] + last.a[ir] + ff.s_ball) + 5.0
        mid = ff.xyz(s_mid, np.interp(s_mid, last.st, last.tc), 120.0)
        sl = ff.s_ball + 15.0
        low = ff.xyz(sl, np.interp(sl, last.st, last.tc), np.interp(sl, last.st, last.zb + last.h) + 12.0)
        tg = np.vstack([top + (mid - top) * x for x in np.linspace(0, 1, 60)] +
                       [mid + (low - mid) * x for x in np.linspace(0, 1, 60)[1:]])
        D = tg - O
        D /= np.linalg.norm(D, axis=1, keepdims=True)
        Q, _ = last.cast(np.repeat(O[None], len(D), 0), D)
        L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))])
        self.Lmax = float(L[-1])
        # resample by arc length, smooth the lateral wobble
        g = np.arange(0.0, L[-1], 1.0)
        Q = np.column_stack([np.interp(g, L, Q[:, k]) for k in range(3)])
        for k in range(3):
            Q[:, k] = gauss1d(Q[:, k], 4.0)
        self.L, self.Q = g, Q
        self.N = last.normal(Q)
        T = np.gradient(Q, axis=0)
        T /= np.linalg.norm(T, axis=1, keepdims=True)
        lat = np.cross(T, self.N)
        lat /= np.linalg.norm(lat, axis=1, keepdims=True)
        if (lat[len(lat) // 2, :2] @ ff.t[:2]) < 0:
            lat = -lat
        self.T, self.lat = T, lat                                   # lat points lateral (+t)
        sq = ff.s_of(Q)
        i1 = int(np.argmax(sq >= E1_S * (last.s_tip - last.s_back) + last.s_back))
        self.e1_L = float(g[i1]) if i1 > 0 else LACE_TOP + 6 * LACE_PITCH   # E1 at 57 % of the length
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
        tg = Q + lat * a[:, None] + N * 6.0
        D = tg - self.O
        D /= np.linalg.norm(D, axis=1, keepdims=True)
        P, _ = self.last.cast(np.repeat(self.O[None], len(D), 0), D)
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
        for i in range(len(Ls) - 1):
            for j in range(nu - 1):
                q = (base + i * nu + j, base + i * nu + j + 1, base + (i + 1) * nu + j + 1, base + (i + 1) * nu + j)
                F.append(q if sgn > 0 else tuple(reversed(q)))
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
            o_, u_ = 0.5 * th * sc * math.cos(a) + 1.5, 0.5 * tall * (0.6 + 0.4 * sc) * math.sin(a) - 0.5 * tall + 6.0
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
    last, O = throat.last, throat.O
    pieces = []
    order = list(range(6, -1, -1))                       # E1 (index 6) up to the top hook (0)

    def strand(p0, p1, sag):
        x = np.linspace(0.0, 1.0, 18)
        q = p0[None] + (p1 - p0)[None] * x[:, None]
        D = q - O
        D /= np.linalg.norm(D, axis=1, keepdims=True)
        S, _ = last.cast(np.repeat(O[None], len(D), 0), D)
        Ns = last.normal(S)
        hgt = STAY_PROUD + LACE_R + 0.5 + sag * np.sin(np.pi * x)
        w = np.clip(np.minimum(x, 1 - x) / 0.12, 0, 1)
        pts = S + Ns * hgt[:, None]
        pts = q + (pts - q) * w[:, None]                  # the ends stay in the eyelets
        return pts

    k0 = order[0]
    pieces.append(tube(strand(holes[(k0, 1.0)], holes[(k0, -1.0)], 0.6), LACE_R, sides=8))
    for side0 in (1.0, -1.0):
        sgn = side0
        for i in range(len(order) - 1):
            ka, kb = order[i], order[i + 1]
            sag = 1.6 if side0 > 0 else 0.2             # one strand rides over the other at the crossings
            pieces.append(tube(strand(holes[(ka, sgn)], holes[(kb, -sgn)], sag), LACE_R, sides=8))
            sgn = -sgn
    Q, N, _, _ = throat.at(np.array([2.0]))
    pieces.append(torus(Q[0] + N[0] * 6.0, N[0], 4.0, 2.6, nu=10, nv=6))   # the knot, under the hem
    return join(pieces)


# --------------------------------------------------------------------------- rand, sole, lugs


def plan_outline(last, ff, dz_of_psi, n=180, iters=3, centre_s=150.0):
    """Horizontal sections of the upper at heights z_top(s) + dz(psi): casts from a point inside the foot."""
    psi = 2.0 * np.pi * np.arange(n) / n                     # 0 = toward the toe, + toward lateral
    D2 = np.stack([np.cos(psi), np.sin(psi)], -1)
    Dw = np.column_stack([D2[:, :1] * ff.u[:2] + D2[:, 1:2] * ff.t[:2], np.zeros(n)])
    tc = float(np.interp(centre_s, last.st, last.tc))
    s_hit = np.full(n, centre_s)
    dz = dz_of_psi(psi)
    for _ in range(iters):
        z = ff.z_top(s_hit) + dz
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
    toe = np.clip(np.cos(psi), 0, 1) ** 10
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
            P, psi = plan_outline(last, ff, lambda p, f=f, extra=extra: rand_height(p) * f + extra)
        nrm = plan_normals(P)
        if k >= 2:                                        # follow the toe box's slope, not the plan
            n3 = last.normal(P)
            nrm = n3 * smoothstep(0.0, 1.0, (k - 1) / 2.0) + nrm * (1 - smoothstep(0.0, 1.0, (k - 1) / 2.0))
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
    zb = ff.z_bottom(s) + LUG                                # the sole's base; the lugs stand below it
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
    zbase = lambda s: ff.z_bottom(s) + LUG + 0.8              # sunk into the base
    zfloor = lambda s: ff.z_bottom(s)
    zwaist = lambda s: ff.z_bottom(s) + 2.0                   # the waist bars stand 3 mm (raised arch)
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
        if 128.0 > sv > 78.0:                          # the waist: no teeth under the arch
            continue
        ln = 11.0 if sv > ff.s_ball - 50 else 18.0
        poly = [p - tg * ln / 2 + nn * 1.4, p + tg * ln / 2 + nn * 1.4, p + tg * ln / 2 * 0.8 - nn * 9.0,
                p - tg * ln / 2 * 0.8 - nn * 9.0]
        V, F = prism(poly, ff, lambda s: ff.z_bottom(s) + LUG + 3.0, zfloor, draft=0.9)
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


def main():
    import bpy
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    body, rig = C.open_base()
    coll = C.part_collection(PART, "Part.Boots")
    bd = C.body_data(body)
    bvh0 = C.skin_bvh(bd)
    mats = {k: C.flat_material(f"Boot.Mat.{k.title()}", h, {"leather": 0.45, "metal": 0.35, "midsole": 0.35}.get(k, 0.8))
            for k, h in COLOURS.items()}
    mats["metal"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.8
    say = lambda *a: C.say(TAG, *a)
    objs, meas = [], {}
    for side in ("L", "R"):
        ff = FootFrame(side)
        Vs_, Ns_, cloud = skin_cloud(bd, side, bvh0)
        last = Last(ff, cloud, say)
        P, F, rim_row, O = build_upper(last, ff)
        E_ = C.edges_of(F)
        P = C.despike(P, E_, factor=2.5, iters=4)
        pin = np.zeros(len(P), bool)
        pin[rim_row] = True
        P = C.taubin(P, E_, iters=6, lam=0.5, mu=-0.53, pin=pin)
        throat = Throat(last, ff, O)
        Vu, fmat, attrs = decorate_upper(last, ff, P, F, throat)
        # the floor of the upper lies inside the sole: drop the faces on the bottom cut
        on_cut = (Vu[:, 2] - last.z_cut(P)) < 0.8
        keepf = [i for i, f in enumerate(F) if not on_cut[list(f)].all()]
        n_th_, n_phi_, Fij_ = build_upper.grid
        upper_info = (n_th_, n_phi_, Fij_, keepf, Vu.copy())
        F2 = [F[i] for i in keepf]
        fm2 = [int(fmat[i]) for i in keepf]
        Vu2, F2, used = C.submesh(Vu, F2, np.ones(len(Vu), bool))
        # safety: the skin must stay inside with 2.5 mm (a few vertices near the malleoli and the toes)
        d0, _ = C.signed_dist(Vu2, bvh0)
        E2 = C.edges_of(F2)
        bad = d0 < 0.0                                    # a stray ray that stopped short: its neighbours' mean
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
        Vu2 = C.push_out(Vu2, bvh0, 2.5)
        say(f"{side}: upper {len(Vu2)} verts; {int((d0 < 2.5).sum())} pushed out to 2.5 mm (min was {d0.min():.1f})")
        up = C.mesh_object(f"Boot.{side}.Upper", Vu2, F2, coll, mats=[mats["leather"], mats["cordura"]], face_mat=fm2)
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
        for k, ob in built.items():
            ob["sgt_clay"] = CLAY[k]
            if k in ("Sole", "Lugs"):
                C.bind(ob, body, rig, only=[f"foot.{side}"],
                       collapse={"toe*": f"foot.{side}", f"lowerleg02.{side}": f"foot.{side}"})
            else:
                C.bind(ob, body, rig, collapse={"toe*": f"foot.{side}"})
        C.solidify(built["Upper"], 1.6, inward=True)
        C.solidify(built["Stays"], 2.0, inward=True)
        C.solidify(built["Tongue"], 6.0, inward=True)
        C.solidify(built["Rand"], 2.0, inward=True)
        for k in ("Upper", "Stays", "Tongue", "Collar", "Rand"):
            C.subsurf(built[k], 1)
        objs += list(built.values())
        L = float(np.ptp(ff.s_of(outline)))
        W = float(np.ptp(ff.t_of(outline)))
        meas[side] = {"outsole_length_mm": round(L + 3.0, 1), "outsole_width_max_mm": round(W + 3.0, 1),
                      "upper_length_mm": round(last.s_tip - last.s_back, 1),
                      "foot_length_mm": round(ff.length, 1), "s_ball_mm": round(ff.s_ball, 1),
                      "toe_room_mm": round(last.s_tip - ff.length - UPPER_OFF, 1),
                      "rim_above_sole_bottom_at_heel_mm": round(RIM_Z + HEEL_SEAT, 1),
                      "shaft_rim_mm": [round(2 * float(np.interp(RIM_Z, last.zs, last.a)), 1),
                                       round(2 * float(np.interp(RIM_Z, last.zs, last.b)), 1)],
                      "throat_E1_height_mm": round(float(ff.h_of(throat.at(np.array([throat.e1_L]))[0])[0]), 1),
                      "lugs": len(Fl)}
    rest = C.clearance([o for o in objs if o.name.endswith((".Upper", ".Collar", ".Tongue", ".Sole"))], body, "rest")
    used = C.apply_hero_pose(rig)
    posed = C.clearance([o for o in objs if o.name.endswith((".Upper", ".Collar", ".Tongue", ".Sole"))], body, "hero pose")
    floor = {}
    for side in ("L", "R"):
        Vp, _ = C.evaluated_world_mm(bpy.data.objects[f"Boot.{side}.Lugs"])
        Vq, _ = C.evaluated_world_mm(bpy.data.objects[f"Boot.{side}.Sole"])
        floor[side] = {"lug_min_z_mm": round(float(Vp[:, 2].min()), 1),
                       "lug_p2_z_mm": round(float(np.percentile(Vp[:, 2], 2)), 1),
                       "sole_base_min_z_mm": round(float(Vq[:, 2].min()), 1)}
        Vt_, _ = C.evaluated_world_mm(bpy.data.objects[f"Boot.{side}.Upper"])
        so = bpy.data.objects[f"Boot.{side}.Sole"]
        R0 = np.array([tuple(v.co) for v in so.data.vertices]) * 1000.0
        sr = FootFrame(side).s_of(R0)
        d = Vq[int(np.argmax(sr)), :2] - Vq[int(np.argmin(sr)), :2]
        floor[side]["posed_heading_deg_from_-Y_toward_his_left(+X)"] = round(math.degrees(math.atan2(d[0], -d[1])), 1)
        floor[side]["posed_toe_tip_mm"] = [round(float(x)) for x in Vq[int(np.argmax(sr))]]
        floor[side]["posed_length_in_plan_mm"] = round(float(np.linalg.norm(d)), 1)
    say("posed soles:", json.dumps(floor))
    C.rest_pose(rig)
    say(json.dumps(meas))
    C.save_part(TAG, coll, {"measure_mm": meas, "posed_soles": floor, "clearance_rest": rest,
                            "clearance_posed": posed, "pose": used})
    if "--no-render" not in args:
        C.render_part(TAG, coll, (0, -40, 90), (700, 420), crops=("ref.boots_feet", "ref.soldier_full"))
        # closeups of one boot on the rest body (the foot stands through the sole; the body is hidden)
        rig_ = bpy.data.objects[C.RIG]
        C.rest_pose(rig_)
        lc = bpy.data.collections.new("Aux.BootL")
        bpy.context.scene.collection.children.link(lc)
        for o in coll.all_objects:
            if ".L." in o.name:
                lc.objects.link(o)
        ff = FootFrame("L")
        cen = ff.xyz(140.0, 20.0, 60.0)
        for name, d in (("L_lateral", ff.t * 1.0 + np.array([0, 0, 0.12])), ("L_front34", ff.u * 0.75 + ff.t * 0.55 + np.array([0, 0, 0.35])),
                        ("L_medial_back", -ff.u * 0.6 - ff.t * 0.7 + np.array([0, 0, 0.3])), ("L_below", np.array([0.0, 0.0, -1.0]) + ff.t * 0.02)):
            d = d / np.linalg.norm(d)
            restore = C.visible_only([lc], keep_body=False)
            C._workbench(bpy.context.scene, "OBJECT", bg=(0.86, 0.86, 0.84))
            for ob in lc.all_objects:
                ob.color = (*(ob.get("sgt_clay") or (0.4, 0.4, 0.4)), 1.0)
            cam = C._aux_camera()
            bpy.context.scene.camera = cam
            cam.data.type, cam.data.lens, cam.data.sensor_fit = "PERSP", 85.0, "AUTO"
            bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 1100, 800
            C._look(cam, cen + d * 1150.0, cen)
            C._render(os.path.join(C.RENDERS, TAG, f"boots_closeup_{name}.png"))
            restore()


if __name__ == "__main__":
    main()
