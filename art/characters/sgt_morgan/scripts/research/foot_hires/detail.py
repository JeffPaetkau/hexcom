"""Surface detail at sub-millimetre resolution: a toenail's bed, folds and plate, and the joint creases, as
height fields in local frames applied to whatever dense skin a method made (frame F, mm).

The nail is fitted to its toe. Its frame is the toe's distal segment, rolled so the plate faces up and a
little medially (spec 01 §3.3). The skin's dorsal surface is sampled into a height map over that frame and
blurred (sigma `blur` mm): MakeHuman's own nail patch (a recess with raised sides) and part 01's knuckle dip
leave ripples that the nail would otherwise copy, so within the nail's reach the skin is rebuilt from the
blurred map. The plate is fitted to that map station by station along the toe: its centre a little proud
of the skin, its visible edges a fold's height below it (the lateral folds fading toward the free edge,
where the plate's sides stand free), its root diving under the proximal fold toward the matrix, its
visible width never more than the toe's dorsum allows (the nail narrows where the toe does, as near the
tip). So the folds' heights are what the parameters say and the toe keeps its dorsum. The skin then fits
the plate:

  * under the visible plate it is the bed, just beneath the plate (seen pink through it), climbing over the
    last half millimetre to the plate's top so that it leaves the plate exactly at the outline whatever the
    mesh (a step there put the contact line on the vertices: a 0.2 mm staircase);
  * outside the outline it comes down onto the plate's edge in a lip, 1 - (1 - s/w)^3 across (steep at the
    plate, level with the toe's skin at its crest), rising into a roll of the fold's least height where the
    skin would not stand that high by itself, so no groove is cut round the nail (the reviews' "caps in
    grooves"), and the plate's root and hidden margins run on under at least `cover` of skin;
  * past the bed the plate runs on straight as the free edge and the skin keeps below it, opening into the
    dark line under a real nail's tip.

The free edge ends `tip_margin` short of the toe's nose, so the pulp leads the nail as on a real toe.

Creases are wrinkle sections (a groove with low shoulders) along curves across a segment, varied along
their length by a seeded wobble.
"""
import math

import numpy as np

import toes as T


def _smooth1d(y, n):
    """A moving average of half-width n samples, edges held."""
    if n <= 0:
        return y
    k = np.ones(2 * n + 1) / (2 * n + 1)
    pad = np.concatenate([np.full(n, y[0]), y, np.full(n, y[-1])])
    return np.convolve(pad, k, mode="valid")


def _fill(H, max_iter=400):
    """Holes and margins of a map (NaN) filled outward by repeated means of the finite 4-neighbours: every
    lookup inside the grid is then finite, so nothing that samples it can switch on a missing cell (round 1's
    sawtooth at the free-edge corners: the gates fell to zero cell by cell where no dorsal vertex fell)."""
    H = H.copy()
    for _ in range(max_iter):
        nan = np.isnan(H)
        if not nan.any():
            break
        Pd = np.pad(H, 1, constant_values=np.nan)
        stack = np.stack([Pd[:-2, 1:-1], Pd[2:, 1:-1], Pd[1:-1, :-2], Pd[1:-1, 2:]])
        cnt = np.isfinite(stack).sum(axis=0)
        mean = np.where(np.isfinite(stack), stack, 0.0).sum(axis=0) / np.maximum(cnt, 1)
        H = np.where(nan & (cnt > 0), mean, H)
    return H


def _blur2d(H, sigma_cells):
    """A Gaussian blur of a map with holes (NaN), normalised by the blurred coverage (separable)."""
    r = max(1, int(3.0 * sigma_cells))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_cells) ** 2)
    k /= k.sum()
    ok = np.isfinite(H)
    A = np.where(ok, H, 0.0)
    M = ok.astype(float)
    for axis in (0, 1):
        A = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), axis, A)
        M = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), axis, M)
    out = np.where(M > 0.3, A / np.maximum(M, 1e-9), np.nan)
    return np.where(ok, out, np.nan)


class Nail:
    """One toenail fitted to its toe's skin. q, nrm: the skin's vertices and normals (F, mm); mine: the
    distal segment's vertices; seg: that segment's frame; P: the nail's parameters (toes.PARAMS)."""

    CELL = 0.25   # the height map's cell (mm)

    def __init__(self, k, seg, q, nrm, mine, P):
        self.k, self.P = k, dict(P)
        self.a = seg.a
        self.n = T.rotate(seg.n, seg.a, P.get("roll_deg", 0.0))   # positive rolls the nail toward medial
        self.b = np.cross(self.n, self.a)
        self.o = seg.o
        t, u, h = self.local(q[mine])
        dorsal = nrm[mine] @ self.n > 0.15
        self._height_map(t[dorsal], u[dorsal], h[dorsal])
        # the toe's midline along t (the middle of its breadth), as a straight line near the nail
        tb, uc = [], []
        for b0 in np.arange(np.floor(t.min()) + 2.0, np.ceil(t.max()) - 2.0, 1.0):
            s = np.abs(t - b0) < 0.75
            if s.sum() > 12:
                tb.append(b0)
                uc.append(0.5 * (u[s].min() + u[s].max()))
        tb, uc = np.array(tb), np.array(uc)
        L = P["length"]
        self.t_nose = float(t.max())
        sel = tb > self.t_nose - (L + 10.0)
        self.c_u = np.polyfit(tb[sel], uc[sel], 1)
        self.t_fe = self.t_nose - P["tip_margin"]
        self.t0 = self.t_fe - L
        self.L = L
        self.L_bed = L - P["free_edge"]
        self._fit_plate()

    # ---- frames and coordinates
    def local(self, q):
        d = np.asarray(q, float) - self.o
        return d @ self.a, d @ self.b, d @ self.n

    def point(self, t, u, h):
        return self.o + np.multiply.outer(t, self.a) + np.multiply.outer(u, self.b) + np.multiply.outer(h, self.n)

    def vx(self, q):
        """(v, x, h): along from the visible proximal fold, across from the centre line, up."""
        t, u, h = self.local(q)
        return t - self.t0, u - np.polyval(self.c_u, t), h

    def to_world(self, v, x, h):
        t = np.asarray(v, float) + self.t0
        return self.point(t, np.asarray(x, float) + np.polyval(self.c_u, t), h)

    # ---- the skin's dorsal height map, raw and blurred
    def _height_map(self, t, u, h):
        c = self.CELL
        pad = 4.0     # mm of margin, filled outward, so the nail's whole domain samples finite values
        self.hm_t0, self.hm_u0 = t.min() - pad, u.min() - pad
        nt = int((t.max() + pad - self.hm_t0) / c) + 3
        nu = int((u.max() + pad - self.hm_u0) / c) + 3
        it = ((t - self.hm_t0) / c).astype(int)
        iu = ((u - self.hm_u0) / c).astype(int)
        H = np.full((nt, nu), -np.inf)
        np.maximum.at(H, (it, iu), h)
        H[~np.isfinite(H)] = np.nan
        for _ in range(2):   # fill interior cells no vertex fell in (three or four finite neighbours)
            nan = np.isnan(H)
            if not nan.any():
                break
            Pd = np.pad(H, 1, constant_values=np.nan)
            stack = np.stack([Pd[:-2, 1:-1], Pd[2:, 1:-1], Pd[1:-1, :-2], Pd[1:-1, 2:]])
            cnt = np.isfinite(stack).sum(axis=0)
            fill = np.where(cnt >= 3, np.where(np.isfinite(stack), stack, 0.0).sum(axis=0) / np.maximum(cnt, 1), np.nan)
            H = np.where(nan, fill, H)
        # where the map holds real dorsal skin (1) or only a filled extension (0), softened over 0.5 mm: the
        # blurred dorsum may stand in for the skin only where it is real (filled values over a steep side are
        # the top surface extended, millimetres above it)
        self.hm_cover = _blur2d(np.isfinite(H).astype(float), 2.0)
        self.hm = _fill(H)
        # the blur takes out MakeHuman's nail-patch ripples but also lowers a convex dorsum by about
        # sigma^2 / 2R (0.2 mm on toe 2, a step where the blurred skin meets the raw at the toe's sides): blurring
        # twice and taking 2 b - b(b) ("twicing") keeps the dome and still drops the ripples
        sig = self.P.get("blur", 1.8) / c
        b1 = _fill(_blur2d(H, sig))
        self.hs = 2.0 * b1 - _blur2d(b1, sig)

    def _sample(self, M, t, u):
        c = self.CELL
        ft = (np.asarray(t, float) - self.hm_t0) / c
        fu = (np.asarray(u, float) - self.hm_u0) / c
        i0 = np.clip(np.floor(ft).astype(int), 0, M.shape[0] - 2)
        j0 = np.clip(np.floor(fu).astype(int), 0, M.shape[1] - 2)
        a, b = np.clip(ft - i0, 0.0, 1.0), np.clip(fu - j0, 0.0, 1.0)
        out = (M[i0, j0] * (1 - a) * (1 - b) + M[i0 + 1, j0] * a * (1 - b) + M[i0, j0 + 1] * (1 - a) * b
               + M[i0 + 1, j0 + 1] * a * b)
        off = (ft < 0) | (fu < 0) | (ft > M.shape[0] - 1) | (fu > M.shape[1] - 1)
        return np.where(off, np.nan, out)

    def skin_vx(self, v, x, blurred=True):
        t = np.asarray(v, float) + self.t0
        return self._sample(self.hs if blurred else self.hm, t, np.asarray(x, float) + np.polyval(self.c_u, t))

    # ---- the plate, fitted station by station
    def _fold_share(self, v):
        lo, hi = self.P.get("lat_fade", (0.45, 0.85))
        return 1.0 - T.smoothstep(v, lo * self.L, hi * self.L)

    def fold_lat(self, v):
        """The lateral folds' height over the plate's visible edge: full proximally, none near the free edge
        (where the plate rests on the skin, `edge_rest` above it)."""
        f = self._fold_share(v)
        return self.P["fold_lat"] * f - self.P.get("edge_rest", 0.08) * (1.0 - f)

    def fold_min(self, v):
        """The lateral lips' least height over the plate's edge, fading out with the lateral folds."""
        return self.P.get("fold_lat_min", 0.15) * self._fold_share(v)

    def hidden(self, v):
        """The plate's margin under each lateral fold: all of it proximally, none where the sides are free,
        and never more than the skin beside the edge covers (fitted per station)."""
        if not hasattr(self, "fit_hidden"):
            return self.P["hidden_side"] * self._fold_share(v)
        return np.interp(np.clip(v, self.fit_v[0], self.fit_v[-1]), self.fit_v, self.fit_hidden)

    def _plate_raw(self, v, x, margin):
        """The plate's top at (v, x) during the fit, before its hidden margins are settled."""
        c, al, be = self._coef(v)
        side = max(abs(float(x)) - float(self.half_vis(v)), 0.0)
        return float(c + al * x + be * x * x) - self._side_dive(side)

    def _side_dive(self, side):
        """How far the plate's side falls into its lateral groove `side` mm past the visible edge: a curve
        down, as a real nail's edges turn into their grooves."""
        hs = max(self.P["hidden_side"], 1e-3)
        return self.P.get("side_dive", 0.8) * np.clip(np.asarray(side, float) / hs, 0.0, 1.5) ** 2

    def _fit_plate(self):
        """Per 0.25 mm station from behind the root to the bed's end, on the blurred dorsum: the visible
        half-width (the nail's own, or the dorsum's breadth `level` mm below its crest less `side_margin`,
        whichever is less), then a parabola across through the centre (the skin plus `lift`) and the two
        visible edges (the skin less the fold's height), its curvature held between `radius_min` and
        `radius_max`, smoothed along the toe; past the bed the plate runs on straight (the free edge)."""
        P = self.P
        st = 0.25
        vs = np.arange(-P["root"] - 1.0, self.L_bed + 1e-6, st)
        c = self.skin_vx(vs, 0.0 * vs) + P.get("lift", 0.12)
        ok = np.isfinite(c)
        c = np.interp(vs, vs[ok], c[ok])
        c = _smooth1d(c, int(2.0 / st))
        # the dorsum's breadth: walk out from the midline until the blurred skin drops `level` below the crest
        xs = np.arange(0.0, 0.5 * P["width"] + 4.0, 0.1)
        half = np.full(len(vs), 0.5 * P["width"])
        # also where the skin falls below the domed plate's own edge (its least curvature, less `slack`): near the
        # tip the toe's sides fall away, and a plate kept wide there stood 1-3 mm over them, the fold dragging
        # the skin up to it and crumpling (the dark crease at toe 2's distal corner)
        dome = xs * xs / (2.0 * P["radius"]) + P.get("slack", 0.35)
        for i, v in enumerate(vs):
            for sgn in (-1.0, 1.0):
                hh = self.skin_vx(np.full(len(xs), v), sgn * xs)
                low = np.nonzero(~np.isfinite(hh) | (hh < c[i] - P.get("level", 2.6)) | (hh < c[i] - dome))[0]
                if len(low):
                    half[i] = min(half[i], xs[low[0]] - P.get("side_margin", 0.9))
        half = np.clip(_smooth1d(half, int(1.5 / st)), P.get("min_width", 0.25) * P["width"], 0.5 * P["width"])
        self.fit_half = half
        el = self.skin_vx(vs, -half) - self.fold_lat(vs)
        er = self.skin_vx(vs, half) - self.fold_lat(vs)
        sag = half * half / (2.0 * P["radius"])
        el = np.where(np.isfinite(el), el, np.where(np.isfinite(er), er, c - sag))
        er = np.where(np.isfinite(er), er, el)
        # behind the visible fold the root dives toward the matrix
        dip = P.get("root_dive", 1.2) * T.smoothstep(-vs, 0.0, P.get("root_fall", 2.2))
        c, el, er = c - dip, el - dip, er - dip
        alpha = (er - el) / (2.0 * half)
        beta = (0.5 * (er + el) - c) / (half * half)
        # at least the nail's own transverse curvature (spec 01 §3.3: 11 mm on the hallux, 6 on toe 2), domed
        # more only where the dorsum is; round 1 allowed up to 26 mm and the plate read as a flat tile
        R = P["radius"]
        beta = np.clip(beta, -1.0 / (2.0 * P.get("radius_min", 0.75 * R)), -1.0 / (2.0 * P.get("radius_max", R)))
        n = int(1.5 / st)
        self.fit_v = vs
        self.fit_c, self.fit_alpha, self.fit_beta = _smooth1d(c, n), _smooth1d(alpha, n), _smooth1d(beta, n)
        self.free_slope = (self.fit_c[-1] - self.fit_c[-9]) / (vs[-1] - vs[-9])
        # the hidden margins: as far as the skin beside the visible edge stands `cover` over the plate there
        # (on a steep side a margin run straight out would come through the side wall)
        self.fit_hidden = np.full(len(vs), P["hidden_side"])
        self.fit_hidden = self.fit_hidden * self._fold_share(vs)
        steps = np.arange(0.0, P["hidden_side"] + 1e-6, 0.1)
        lim = np.zeros(len(vs))
        for i, v in enumerate(vs):
            ok_m = 0.0
            for m in steps:
                good = True
                for sgn in (-1.0, 1.0):
                    xx = sgn * (half[i] + m)
                    sk = self.skin_vx(v, xx)
                    if not np.isfinite(sk) or sk < self._plate_raw(v, xx, m) + P.get("cover", 0.1) + 0.05:
                        good = False
                if not good:
                    break
                ok_m = m
            lim[i] = ok_m
        lim = np.minimum.accumulate(lim[::-1])[::-1] if P.get("hidden_monotone", True) else lim
        self.fit_hidden = np.minimum(self.fit_hidden, _smooth1d(lim, int(3.0 / st)))

    def _coef(self, v):
        v = np.asarray(v, float)
        vc = np.clip(v, self.fit_v[0], self.fit_v[-1])
        c = np.interp(vc, self.fit_v, self.fit_c) + np.maximum(v - self.fit_v[-1], 0.0) * self.free_slope
        return c, np.interp(vc, self.fit_v, self.fit_alpha), np.interp(vc, self.fit_v, self.fit_beta)

    def half_vis(self, v):
        """The visible half-width at v (after the bed, the bed's last)."""
        return np.interp(np.clip(v, self.fit_v[0], self.fit_v[-1]), self.fit_v, self.fit_half)

    def burial(self):
        """How far the skin (the blurred dorsum before the nail) stands over the plate's visible edges, medial
        and lateral, at a few stations: the folds' height the fit leaves (round 1: up to 2.5 mm laterally at the
        free edge, a plate buried in the toe's side), and the plate's transverse radius there."""
        out = {}
        for v in (0.0, 0.5 * self.L, self.L_bed - 0.5):
            hv = float(self.half_vis(v))
            sk = self.skin_vx(np.array([v, v]), np.array([-hv, hv]))
            pl = self.plate_top(np.array([v, v]), np.array([-hv, hv]))
            beta = float(np.interp(v, self.fit_v, self.fit_beta))
            out[f"v{v:.1f}"] = {"medial": round(float(sk[0] - pl[0]), 2), "lateral": round(float(sk[1] - pl[1]), 2),
                                "radius": round(-0.5 / beta, 1), "half": round(hv, 2)}
        return out

    def half_width(self, v):
        """The plate's half-width at v: the visible half-width, the hidden margin, the rounded corners of the
        free edge's trim and of the root (negative off the plate's length)."""
        P = self.P
        v = np.asarray(v, float)
        cf, cr, root, L = P["corner"], P.get("corner_root", 3.0), P["root"], self.L
        e1 = np.clip(v - (L - cf), 0.0, cf)
        e2 = np.clip((-root + cr) - v, 0.0, cr)
        half = self.half_vis(v) + self.hidden(v) - (cf - np.sqrt(cf * cf - e1 * e1)) - (cr - np.sqrt(cr * cr - e2 * e2))
        return np.where((v < -root) | (v > L), -1.0, np.maximum(half, 0.3))

    def plate_top(self, v, x):
        """The plate's top: the station's parabola, and under the lateral folds an extra dive into the
        lateral grooves."""
        c, al, be = self._coef(v)
        x = np.asarray(x, float)
        side = np.maximum(np.abs(x) - self.half_vis(v), 0.0)
        return c + al * x + be * x * x - self._side_dive(side)

    def thickness(self, v):
        P = self.P
        return P["thick_root"] + (P["thick_edge"] - P["thick_root"]) * T.smoothstep(v, 0.0, self.L)

    # ---- the free edge's line and the plate's end, a little uneven (a trimmed nail is cut by hand)
    def _wave(self, x, k):
        """A fixed, seeded wobble across the nail (-1..1 roughly), one per use k."""
        ph = np.random.default_rng(31 * self.k + k).uniform(0.0, 2.0 * math.pi, 3)
        x = np.asarray(x, float)
        return 0.55 * np.sin(2.0 * math.pi * x / 6.3 + ph[0]) + 0.3 * np.sin(2.0 * math.pi * x / 2.9 + ph[1]) \
            + 0.15 * np.sin(2.0 * math.pi * x / 1.7 + ph[2])

    def L_bed_x(self, x):
        """Where the plate leaves the bed (the onychodermal band's distal line) across the nail."""
        return self.L_bed + self.P.get("bed_wave", 0.0) * self._wave(x, 0)

    def L_x(self, x):
        """The free edge's line across the nail."""
        return self.L + self.P.get("edge_wave", 0.0) * self._wave(x, 1)

    # ---- the visible outline: open toward the free edge, a curved cuticle line, its corners rounded
    def cuticle(self, x):
        """The visible proximal fold's line (v at x): an arc rising `cuticle` mm toward the sides, so the
        root reads as a curve with no proximal corners (round 1's was straight across)."""
        W0 = max(float(self.half_vis(0.0)), 1e-3)
        a = np.asarray(x, float) / W0
        return self.P.get("cuticle", 0.0) * a * a

    def outline(self, v, x):
        """Signed distance to the visible outline in the (v, x) plane (negative inside), the nearest outline
        point and p, the proximal fold's share there (1) against the lateral fold's (0). The proximal line is
        the cuticle's arc, the sides the visible half-width; the two meet in a smooth maximum of radius
        `corner_prox`, so every output is a smooth function of (v, x): no switch for the vertices to straddle."""
        P = self.P
        v, x = np.asarray(v, float), np.asarray(x, float)
        W0 = max(float(self.half_vis(0.0)), 1e-3)
        cu = P.get("cuticle", 0.0)
        slope = 2.0 * cu * x / (W0 * W0)                       # dv/dx of the cuticle
        ln = np.sqrt(1.0 + slope * slope)
        s_p = (self.cuticle(x) - v) / ln                         # > 0 behind (proximal of) the cuticle
        s_l = np.abs(x) - self.half_vis(v)                       # > 0 outside the sides
        sx = np.where(x < 0.0, -1.0, 1.0)
        k = P.get("corner_prox", 3.5)
        hh = np.clip(0.5 + 0.5 * (s_p - s_l) / k, 0.0, 1.0)      # the proximal line's share
        s = s_l + (s_p - s_l) * hh + k * hh * (1.0 - hh)
        gv = hh * (-1.0 / ln)
        gx = hh * (slope / ln) + (1.0 - hh) * sx
        gn = np.maximum(np.hypot(gv, gx), 1e-6)
        nv = v - s * gv / gn
        nx = x - s * gx / gn
        return s, nv, nx, hh

    def fold_h(self, v):
        """The lateral folds' height over the plate's edge, fading toward the free edge."""
        return self.P["fold_lat"] * self._fold_share(v)

    def skin_target(self, v, x, h):
        """The skin's height at (v, x) given its reference height h. Every regime meets the next at the same
        height (round 1 switched between them at the outline and at the bed's end, which the 0.17 mm vertices
        sampled as a sawtooth):

          * inside the outline, over the bed: the bed just under the plate, climbing over `ramp` to the
            plate's top at the outline (the contact line);
          * inside, past the bed (`past`, at the onychodermal band): the hyponychium, under the free edge
            with the undercut's dark gap, and never above the skin's own height;
          * outside, where the plate rests on the bed: the fold lands on the plate's top and rises in a soft
            roll, the eponychium lying `epo_lap` mm on the plate at the root (`epo_h` thick, so the plate's
            root and edge never show), a lateral fold over each side, then the toe's own skin;
          * outside, along the free sides: the skin passes under the plate and the groove opens out;
          * beyond the free edge the nail lets go of the skin over 1.5 mm.

        Where the plate runs on under the skin (its hidden margins and root) the skin stays `cover` above it.
        Returns (target, s)."""
        P = self.P
        s, nv, nx, p = self.outline(v, x)
        top = self.plate_top(v, x)
        e = self.plate_top(nv, nx)                                   # the plate's top at the outline point
        Lb, Lb_n = self.L_bed_x(x), self.L_bed_x(nx)
        past = T.smoothstep(v, Lb - 0.3, Lb + 0.9)                    # from the bed to under the free edge
        past_n = T.smoothstep(nv, Lb_n - 0.3, Lb_n + 0.9)
        bed_gap, undercut = P.get("bed_gap", 0.03), P.get("undercut", 0.45)

        def inner_at(top_, v_, past_):
            under_ = top_ - self.thickness(v_) - bed_gap - undercut * past_
            return under_ + (np.minimum(h, under_) - under_) * past_

        inner = inner_at(top, v, past)
        ramp = p * P.get("ramp_prox", 0.7) + (1.0 - p) * P.get("ramp_lat", 0.5)
        climb = T.smoothstep(s, -ramp, 0.0) ** 2
        inside = inner + (top - inner) * (1.0 - past) * climb
        land = e * (1.0 - past_n) + inner_at(e, nv, past_n) * past_n   # = inside at s = 0
        # the folds over the bed: rise, lie (the eponychium), then hand over to the toe's skin
        rise = p * P.get("epo_w", 0.35) + (1.0 - p) * P["lat_width"]
        lap = p * P.get("epo_lap", 1.4)
        back = p * P.get("fold_back_prox", 1.2) + (1.0 - p) * P.get("fold_back_lat", 2.2)
        Hc = p * P.get("epo_h", P["fold_prox"]) + (1.0 - p) * self.fold_h(nv)
        # proximal: the eponychium rises off the plate, lies on it for `epo_lap`, then hands over to the dorsum
        xs = np.clip(s / np.maximum(rise, 1e-6), 0.0, 1.0)
        fold = land + Hc * (1.0 - (1.0 - xs) ** 2)
        t_prox = fold + (h - fold) * T.smoothstep(s, rise + lap, rise + lap + back)
        # lateral: from the plate's edge to the toe's own skin across the fold's width, a soft roll on the way.
        # Where the side stands higher the fold laps down onto the edge; where it falls away (near the tip, up to
        # 2.2 mm within a millimetre of the edge) the skin wraps the edge and follows the side: a fold held at
        # the plate's level for its width stood there as a shelf and crumpled (round 2's first try)
        xl = np.clip(s / P["lat_width"], 0.0, 1.0)
        t_lat = land + (h - land) * (1.0 - (1.0 - xl) ** 2) + self.fold_h(nv) * 4.0 * xl * (1.0 - xl)
        t_bed = t_prox * p + t_lat * (1.0 - p)
        # along the free sides: under the plate's edge, opening out at `open` (a slope) to the skin's own
        reach = land + P.get("open", 1.0) * np.maximum(s, 0.0)
        t_free = np.minimum(h, reach) - 0.15 * np.log1p(np.exp(-np.abs(h - reach) / 0.15)) \
            * T.smoothstep(s, 0.0, 0.3)
        outside = t_bed * (1.0 - past_n) + t_free * past_n
        sig = T.smoothstep(s, -0.08, 0.08)
        target = inside * (1.0 - sig) + outside * sig
        # where the plate runs on under the skin (hidden margins, the root) the skin stays `cover` over it
        Le = self.L_x(x)
        covered = T.smoothstep(self.half_width(v) + 0.1 - np.abs(x), -0.25, 0.25) \
            * T.smoothstep(v, -P["root"] - 0.3, -P["root"] + 0.3) * (1.0 - T.smoothstep(v, Le - 0.25, Le + 0.35))
        hid = covered * T.smoothstep(s, 0.0, 0.3) * (1.0 - past_n)
        need = top + P.get("cover", 0.1) - target
        k = 0.08
        lift = k * np.logaddexp(0.0, need / k)                         # a soft max(need, 0)
        target = target + lift * hid
        # beyond the free edge the nail lets go
        beyond = T.smoothstep(v, Le + 0.2, Le + 1.7)
        target = target + (h - target) * beyond
        if getattr(self, "_dbg", None) is not None:
            self._dbg.update(p=p, covered=covered, past=past, past_n=past_n, inside=inside, outside=outside,
                             hid=hid, lift=lift, land=land, e=e, top=top, Hc=Hc, t_bed=t_bed, t_free=t_free,
                             nv=nv, nx=nx, beyond=beyond)
        return target, s

    def apply(self, q, nrm, region):
        """Rebuild this toe's dorsal skin near the nail: the blurred dorsum, then the nail's target, along the
        nail's normal (region: bool, the candidates). Returns the new positions and the bed mask."""
        P = self.P
        v, x, h = self.vx(q)
        W2 = 0.5 * P["width"]
        reach_v = P["root"] + P["prox_width"] + P.get("reach_back", 8.0)
        reach_x = W2 + P["hidden_side"] + P["lat_width"] + 3.0
        dom = region & (v > -reach_v) & (v < self.L + 2.5) & (np.abs(x) < reach_x) \
            & (nrm @ self.n > -0.25) & (h > self.plate_top(v, x) - 5.0)
        idx = np.nonzero(dom)[0]
        vi, xi, hi = v[idx], x[idx], h[idx]
        # only the top-most skin is a height field over the nail's frame: on a steep side several vertices
        # share one (v, x), and one target for them all would fold the surface into pleats
        # (the maps are filled, so the gate is smooth wherever the domain reaches; round 1's NaN cells made it
        # a per-vertex switch at the free-edge corners, the sawtooth's cause)
        raw = self.skin_vx(vi, xi, blurred=False)
        on_top = T.smoothstep(nrm[idx] @ self.n, 0.05, 0.35) * (1.0 - T.smoothstep(np.nan_to_num(raw - hi, nan=9.0), 0.7, 1.8))
        hs = self.skin_vx(vi, xi)
        # the blurred dorsum stands in for the skin only over the bed (where MakeHuman's nail patch leaves its
        # ripples): past the bed's end a blur lifts the falling corners of the tip (round 2's first try: a lip
        # 0.45 mm proud just ahead of the free edge's corners)
        lb = self.L_bed_x(xi)
        tt = vi + self.t0
        cov = np.nan_to_num(self._sample(self.hm_cover, tt, xi + np.polyval(self.c_u, tt)), nan=0.0)
        wd = T.smoothstep(cov, 0.55, 0.95) * T.window(vi, -reach_v, -reach_v + 5.0, lb - 1.0, lb + 0.5) \
            * (1.0 - T.smoothstep(np.abs(xi), reach_x - 2.0, reach_x)) \
            * T.smoothstep(nrm[idx] @ self.n, 0.3, 0.8) * np.isfinite(hs)
        href = hi + (np.nan_to_num(hs, nan=0.0) - hi) * wd
        if P.get("debug_dump"):
            self._dbg = {}
        tgt, s = self.skin_target(vi, xi, href)
        # the domain's own edge faded, so nothing a target does near it can leave a step
        edge = T.window(vi, -reach_v, -reach_v + 1.5, self.L + 0.5, self.L + 2.0)             * (1.0 - T.smoothstep(np.abs(xi), reach_x - 1.5, reach_x))
        if P.get("debug_dump"):
            import os
            import common as C
            os.makedirs(C.CACHE, exist_ok=True)
            np.savez_compressed(os.path.join(C.CACHE, f"nail{self.k}_dbg.npz"), idx=idx, v=vi, x=xi, h=hi, hs=hs,
                                raw=raw, on_top=on_top, wd=wd, href=href, tgt=tgt, s=s, edge=edge,
                                nn=nrm[idx] @ self.n, L=self.L, L_bed=self.L_bed, fit_v=self.fit_v, fit_c=self.fit_c,
                                fit_alpha=self.fit_alpha, fit_beta=self.fit_beta, fit_half=self.fit_half,
                                fit_hidden=self.fit_hidden, hm=self.hm, hs_map=self.hs, hm_t0=self.hm_t0,
                                hm_u0=self.hm_u0, c_u=self.c_u, t0=self.t0, **self._dbg)
            self._dbg = None
        q = q.copy()
        q[idx] += ((tgt - hi) * on_top * edge)[:, None] * self.n[None, :]
        bed = np.zeros(len(q))
        lb = self.L_bed_x(xi)
        bed[idx] = (1.0 - T.smoothstep(s, -0.4, 0.05)) * (1.0 - T.smoothstep(vi, lb - 0.1, lb + 0.5))
        return q, bed

    def plate_mesh(self, dv=0.15, dx=0.15, rim_rows=5, bulge=0.3):
        """The plate as a closed shell (F, mm): top and bottom grids over its outline (the hidden root and
        side margins included, the free edge trimmed straight with rounded corners) joined by a half-round
        rim, with (u, v, w) per vertex for the nail recipes (u across, v from the visible proximal fold, w past
        the bed). Returns (vertices, quads, uvw)."""
        P = self.P
        root, L = P["root"], self.L
        nv = int(math.ceil((L + root) / dv)) + 1
        vs = np.linspace(-root, L, nv)
        half = self.half_width(vs)
        nx = int(math.ceil(2.0 * (0.5 * P["width"] + P["hidden_side"]) / dx)) + 1
        ss = np.linspace(-1.0, 1.0, nx)
        S = np.repeat(vs[:, None], nx, axis=1)
        X = half[:, None] * ss[None, :]
        # the rows warped so one lies on the bed's (uneven) end and the last on the (uneven) free edge: the
        # free edge's material starts exactly there, its band a little uneven in width, the cut not ruled
        Lb = self.L_bed
        d_bed = self.L_bed_x(X) - Lb
        d_end = self.L_x(X) - L
        r1 = T.smoothstep(S, Lb - 3.0, Lb)
        r2 = np.clip((S - Lb) / max(L - Lb, 1e-6), 0.0, 1.0)
        V = S + d_bed * r1 * (1.0 - r2) + d_end * r2
        # (the width stays the unwarped station's: the free edge's rounded corner makes half_width all but
        # vertical at L, and taken at the warped station it put kinks in the rim)
        top_h = self.plate_top(V, X)
        th = self.thickness(V)
        flat_top = self.to_world(V, X, top_h).reshape(-1, 3)
        flat_bot = self.to_world(V, X, top_h - th).reshape(-1, 3)
        idx = np.arange(nv * nx).reshape(nv, nx)
        ring = np.concatenate([idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]])
        jj, ii = np.divmod(ring, nx)
        jn = np.clip(jj + np.where(jj == 0, 1, np.where(jj == nv - 1, -1, 0)), 0, nv - 1)
        in_ = np.clip(ii + np.where(ii == 0, 1, np.where(ii == nx - 1, -1, 0)), 0, nx - 1)
        out = flat_top[ring] - flat_top[jn * nx + in_]
        out -= np.multiply.outer(out @ self.n, self.n)
        out /= np.maximum(np.linalg.norm(out, axis=1), 1e-9)[:, None]
        verts = [flat_top, flat_bot]
        uvw0 = np.stack([X.ravel(), V.ravel(), (V - self.L_bed_x(X)).ravel()], axis=1)
        uvws = [uvw0, uvw0]
        jg, ig = np.meshgrid(np.arange(nv - 1), np.arange(nx - 1), indexing="ij")
        a, b = idx[jg, ig].ravel(), idx[jg, ig + 1].ravel()
        c, d = idx[jg + 1, ig + 1].ravel(), idx[jg + 1, ig].ravel()
        quads = [np.stack([a, d, c, b], 1), np.stack([a, b, c, d], 1) + nv * nx]
        tp, bp, thr = flat_top[ring], flat_bot[ring], th.ravel()[ring]
        rows = [ring]
        base = 2 * nv * nx
        for r in range(1, rim_rows):
            ang = math.pi * r / rim_rows
            f = 0.5 - 0.5 * math.cos(ang)                   # 0 at the top edge, 1 at the bottom
            # flatter than a half-round (0.5): a trimmed edge is a cut face, not a rolled bead
            verts.append(tp * (1.0 - f) + bp * f + out * (bulge * thr * math.sin(ang))[:, None])
            uvws.append(uvw0[ring])
            rows.append(base + np.arange(len(ring)))
            base += len(ring)
        rows.append(ring + nv * nx)
        m = len(ring)
        nxt = (np.arange(m) + 1) % m
        for r0, r1 in zip(rows[:-1], rows[1:]):
            quads.append(np.stack([r0, r0[nxt], r1[nxt], r1], 1))
        return np.vstack(verts), np.vstack(quads), np.vstack(uvws)


def crease(q, nrm, seg, t0, depth, width, side=1.0, bow=0.0, half=10.0, u0=0.0, wrap=0.35, seed=0, wobble=0.25):
    """A skin crease across a segment along t = t0 + bow (u/half)^2 on its dorsal (side +1) or plantar (-1)
    face: a wrinkle's section (a groove `depth` deep with low shoulders either side, the Ricker profile of
    sigma `width`), its depth and line varied along its length by a seeded wobble so no two creases repeat,
    fading toward its ends at |u - u0| = half. Returns the displacement (along the normals) and the crease
    weight (0-1, for the shader's crease mask)."""
    t, u, h = seg.local(q)
    face = T.smoothstep(side * (nrm @ seg.n), wrap - 0.3, wrap + 0.15)
    across = (u - u0) / half
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0.0, 2.0 * np.pi, 4)
    vary = 1.0 + wobble * (np.sin(2.1 * across + ph[0]) + 0.6 * np.sin(4.7 * across + ph[1]))
    shift = 0.35 * width * (np.sin(1.7 * across + ph[2]) + 0.5 * np.sin(3.9 * across + ph[3]))
    d = (t - (t0 + bow * across ** 2 + shift)) / width
    prof = (1.0 - d * d) * np.exp(-0.5 * d * d)
    ends = (1.0 - T.smoothstep(np.abs(across), 0.55, 1.0)) * face
    w = np.clip(prof, 0.0, 1.0) * ends
    return -(depth * np.clip(vary, 0.3, 1.6) * prof * ends)[:, None] * nrm, w


def mesh_object(name, verts_mm, quads, coll=None, smooth=True, recalc=True):
    """A Blender mesh object from world vertices in mm and quads, its normals made consistent outward."""
    import bmesh
    import bpy
    me = bpy.data.meshes.new(name)
    verts = (np.asarray(verts_mm, float) / 1000.0)
    quads = np.asarray(quads, np.int64)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel().astype(np.float32))
    me.loops.add(quads.size)
    me.loops.foreach_set("vertex_index", quads.ravel().astype(np.int32))
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", (np.arange(len(quads)) * 4).astype(np.int32))
    me.polygons.foreach_set("loop_total", np.full(len(quads), 4, np.int32))
    me.update(calc_edges=True)
    me.validate()
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    me.polygons.foreach_set("use_smooth", np.full(len(me.polygons), smooth))
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob
