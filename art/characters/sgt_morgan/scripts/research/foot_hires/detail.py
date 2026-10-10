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
        self.hm_t0, self.hm_u0 = t.min() - c, u.min() - c
        nt = int((t.max() - self.hm_t0) / c) + 3
        nu = int((u.max() - self.hm_u0) / c) + 3
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
        self.hm = H
        self.hs = _blur2d(H, self.P.get("blur", 1.8) / c)

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
        for i, v in enumerate(vs):
            for sgn in (-1.0, 1.0):
                hh = self.skin_vx(np.full(len(xs), v), sgn * xs)
                low = np.nonzero(~np.isfinite(hh) | (hh < c[i] - P.get("level", 2.6)))[0]
                if len(low):
                    half[i] = min(half[i], xs[low[0]] - P.get("side_margin", 0.9))
        half = np.clip(_smooth1d(half, int(1.5 / st)), 0.25 * P["width"], 0.5 * P["width"])
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
        beta = np.clip(beta, -1.0 / (2.0 * P.get("radius_min", 9.0)), -1.0 / (2.0 * P.get("radius_max", 26.0)))
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

    # ---- the visible outline: open toward the free edge, its proximal corners rounded
    def outline(self, v, x):
        """Signed distance to the visible outline in the (v, x) plane (negative inside), the nearest outline
        point and p, the proximal fold's share there (1) against the lateral fold's (0)."""
        P = self.P
        v, x = np.asarray(v, float), np.asarray(x, float)
        W2 = self.half_vis(v)
        W20 = float(self.half_vis(0.0))
        rc = min(P.get("corner_prox", 3.5), 0.9 * W20)
        ax, sx = np.abs(x), np.where(x < 0.0, -1.0, 1.0)
        cx = W20 - rc
        corner = (v < rc) & (ax > cx)
        dv, dx = v - rc, ax - cx
        dist = np.hypot(dv, dx)
        safe = np.maximum(dist, 1e-9)
        near_prox = -v > ax - W2
        s = np.where(corner, dist - rc, np.maximum(-v, ax - W2))
        nv = np.where(corner, rc + dv / safe * rc, np.where(near_prox, 0.0, v))
        nx = np.where(corner, cx + dx / safe * rc, np.where(near_prox, ax, W2)) * sx
        p = np.where(corner, np.clip(np.arctan2(-dv, dx) / (0.5 * math.pi), 0.0, 1.0), near_prox.astype(float))
        return s, nv, nx, p

    def skin_target(self, v, x, h):
        """The skin's height at (v, x) given its reference height h: the bed under the plate, the lip onto the
        plate's edge outside it, the skin kept under the plate where the plate is the higher. Returns
        (target, s)."""
        P = self.P
        L = self.L
        s, nv, nx, p = self.outline(v, x)
        e = self.plate_top(nv, nx)
        h_edge = self.skin_vx(nv, nx)
        h_edge = np.where(np.isfinite(h_edge), h_edge, e)
        drop = h_edge - e                                         # the skin's height over the plate's edge
        w = p * P["prox_width"] + (1.0 - p) * P["lat_width"]
        xs = np.clip(s / np.maximum(w, 1e-6), 0.0, 1.0)
        rs = 1.0 - (1.0 - xs) ** 3
        Hmin = p * P["fold_prox"] + (1.0 - p) * self.fold_min(nv)
        descend = h - np.maximum(drop, 0.0) * (1.0 - rs)
        back = T.smoothstep(s, w, w + p * P.get("fold_back_prox", 1.2) + (1.0 - p) * P.get("fold_back_lat", 2.2))
        roll_up = (e + Hmin * rs) * (1.0 - back) + h * back
        # the roll only where the skin beside the nail is level with its edge or above it: where the toe's
        # side falls away (near the tip) a roll would stand as a fin
        lip = descend + np.maximum(roll_up - descend, 0.0) * T.smoothstep(Hmin - drop, -0.05, 0.05)             * T.smoothstep(h - e, -0.3, 0.0)
        gap = P.get("bed_gap", 0.03) + P.get("undercut", 0.45) * T.smoothstep(v, self.L_bed - 0.4, L)
        top = self.plate_top(v, x)
        under = top - self.thickness(v) - gap
        # a transition over a few vertices, not one: a one-vertex switch puts a sawtooth on the free edge
        covered = T.smoothstep(self.half_width(v) + 0.1 - np.abs(x), -0.25, 0.25) \
            * T.smoothstep(v, -P["root"] - 0.3, -P["root"] + 0.3) * (1.0 - T.smoothstep(v, L - 0.25, L + 0.35))
        past = T.smoothstep(v, self.L_bed, self.L_bed + 1.0)     # from the bed onto the hyponychium
        bed = under + (np.minimum(h, under) - under) * past
        ramp = p * P.get("ramp_prox", 0.7) + (1.0 - p) * P.get("ramp_lat", 0.5)
        climb = T.smoothstep(s, -ramp, 0.0) ** 2
        inside = bed + (np.maximum(top, bed) - bed) * climb * (1.0 - past)
        free = (1.0 - T.smoothstep(Hmin, 0.0, 0.05)) * T.smoothstep(-drop, 0.0, 0.1)
        kept = np.minimum(h, under) * covered + h * (1.0 - covered)
        outside = lip * (1.0 - free) + kept * free
        target = np.where(s < 0.0, inside * covered + np.minimum(h, under) * (1.0 - covered), outside)
        cover = P.get("cover", 0.1)
        hid = covered * T.smoothstep(s, 0.0, 0.3)
        need = top + cover - target
        k = 0.08
        lift = k * np.logaddexp(0.0, need / k)                    # a soft max(need, 0)
        target = target + lift * hid
        return target, s

    def apply(self, q, nrm, region):
        """Rebuild this toe's dorsal skin near the nail: the blurred dorsum, then the nail's target, along the
        nail's normal (region: bool, the candidates). Returns the new positions and the bed mask."""
        P = self.P
        v, x, h = self.vx(q)
        W2 = 0.5 * P["width"]
        reach_v = P["root"] + P["prox_width"] + P.get("reach_back", 8.0)
        reach_x = W2 + P["hidden_side"] + P["lat_width"] + 3.0
        dom = region & (v > -reach_v) & (v < self.L + 2.0) & (np.abs(x) < reach_x) \
            & (nrm @ self.n > -0.25) & (h > self.plate_top(v, x) - 5.0)
        idx = np.nonzero(dom)[0]
        vi, xi, hi = v[idx], x[idx], h[idx]
        # only the top-most skin is a height field over the nail's frame: on a steep side several vertices
        # share one (v, x), and one target for them all would fold the surface into pleats
        raw = self.skin_vx(vi, xi, blurred=False)
        on_top = T.smoothstep(nrm[idx] @ self.n, 0.05, 0.35) * (1.0 - T.smoothstep(np.nan_to_num(raw - hi, nan=9.0), 0.5, 1.2))
        hs = self.skin_vx(vi, xi)
        wd = T.window(vi, -reach_v, -reach_v + 5.0, self.L + 0.5, self.L + 2.0) \
            * (1.0 - T.smoothstep(np.abs(xi), reach_x - 2.0, reach_x)) \
            * T.smoothstep(nrm[idx] @ self.n, 0.45, 0.8) * np.isfinite(hs)
        href = hi + (np.nan_to_num(hs, nan=0.0) - hi) * wd
        tgt, s = self.skin_target(vi, xi, href)
        # the domain's own edge faded, so nothing a target does near it can leave a step
        edge = T.window(vi, -reach_v, -reach_v + 1.5, self.L + 0.5, self.L + 2.0)             * (1.0 - T.smoothstep(np.abs(xi), reach_x - 1.5, reach_x))
        q = q.copy()
        q[idx] += ((tgt - hi) * on_top * edge)[:, None] * self.n[None, :]
        bed = np.zeros(len(q))
        bed[idx] = (1.0 - T.smoothstep(s, -0.4, 0.05)) * (vi < self.L_bed + 0.3)
        return q, bed

    def plate_mesh(self, dv=0.15, dx=0.15, rim_rows=5):
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
        V = np.repeat(vs[:, None], nx, axis=1)
        X = half[:, None] * ss[None, :]
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
        uvw0 = np.stack([X.ravel(), V.ravel(), (V - self.L_bed).ravel()], axis=1)
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
            verts.append(tp * (1.0 - f) + bp * f + out * (0.5 * thr * math.sin(ang))[:, None])
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
