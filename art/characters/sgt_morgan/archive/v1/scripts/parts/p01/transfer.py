"""The foot's large forms transferred from a real foot's scan (Jeff, 2026-10-17; spec 01 §0, §3.1 and §4.2 notes of that
date): "The 3d scan overall shape of the foot is way better than ours. The only exception is between the toes, which is
almost certainly a resolution issue. We are better between toes but they are better everywhere else."

The surface (scanref.py): subject 038's seated scan (mBW, near-unloaded) for the rest shape and his standing scan (fBW)
for the loaded key, mirrored for the left foot and as scanned for the right (frame F mirrors the right foot, so one
scan in F serves both), aligned and scaled as scan.py did (the heel's centre, the line to toe 2's tip, the pternion,
the floor; 274.3 mm), and placed on this foot by re-zeroing it the same way (scanfit.rezero).

The transfer moves the region's vertices so that the rendered (Catmull-Clark limit) surface lies on the scan:

  1. prewarp: each toe turned about its MTP joint in plan and stretched along its axis so its tip lands on the scan's
     toe's tip (scan_tips), a toe much longer than the scan's first carried back whole, so the projection below meets
     the right toe;
  2. masks: `keep`, the skin between the toes (the clefts' floors, the webs and the walls that face a neighbouring toe:
     rays in a cone about the normal that meet another toe within `reach` mm), where the scan's 1.4 mm mesh fuses the
     toes and ours keeps them apart, faded over the cage's next ring; `blend`, 1 below blend_z[0] and 0 above
     blend_z[1], the scan's cut at 125 mm giving way to the leg above: the data's weight falls to nothing over it and
     the displacement eases out up the leg to `hold` mm over the cut, where the leg is held (038's leg stands 12 mm
     further back at the Achilles than ours there: pinned at the cut, the Achilles met our leg in a notch);
  3. fit: the cage displacement U minimising sum (1 - keep) blend |limit(q0 + U) - target|^2
     + mu sum_edges |U_i - U_j|^2, the target the scan's nearest point to the current limit point (a compatible facing:
     normals within ~80 degrees, nearer than max_dist); solved by conjugate gradients, the
     nearest points refreshed and mu lowered over the iterations (coarse to fine). Where `keep` is 1 the data term is
     gone and U is the smooth extension of its surroundings: our geometry between the toes, carried with the toes. A
     smooth U keeps MakeHuman's quads in their layout (nothing slides into a pile, nothing folds); the helpers (the
     joint cubes) follow their toes' nearest skin.

Everything is numpy on the region's quads (limit stencils, a matrix-free Laplacian), with mathutils' BVH trees for
nearest points and rays when run in Blender; outside Blender a KD-tree over points sampled on the scan stands in.
"""
import math

import numpy as np

from lib import sculpt as S
from parts.p01 import scanref

TOES = (1, 2, 3, 4, 5)

# params.json "transfer" over these (the build's knobs; `on` 0 is the fitted fields' build of 2026-10-16)
DEFAULTS = {
    "on": 0,
    "scan": "038",            # subject: Jeff saw 038 beside ours (2026-10-17)
    "loaded": "fBW",          # the loaded key's scan condition
    # round 3b's fixes (2026-10-27, critic series foot_shape round 3b m2, m8, m10: from behind the ankle a broad flat
    # face and the column leaning medially, a notch in the Achilles' line at z 110): the scan's ankle is kept through
    # z 110 and fades into the leg by the cut (was 95-125, so the medial malleolus' hollows and the Achilles' line above
    # z 95 were half ours), and our leg is first laid on the scan's sections at the cut (leg_align: its plan centre and
    # its breadths across and along over `leg.band`), the alignment easing out up the leg over `leg.ease` (smootherstep,
    # so the leg's outline keeps its slope at both ends); the displacement is then held from `hold` over the cut, past
    # the alignment's reach, so the notch where 038's Achilles (6 mm further back than ours at the cut) met our leg goes
    "blend_z": [110.0, 124.0],  # the scan to the leg above (its cut at 125, 126.6 once scaled) ...
    "hold": 128.0,            # ... and the leg held from this far over the cut (the displacement eases out between)
    "leg": {"on": 1, "band": [108.0, 122.0], "below": [60.0, 100.0], "ease": [124.0, 252.0], "scale": 1},
    # round 3b's fixes (m1, m3, m5, m9, m12, m21: the toes read as fingers, our kept walls cylinders with clefts back to
    # the webs, a see-through slit along the hallux and toe 2): `keep` is now only the skin between the toes whose
    # nearest point on the scan is shared, lying as near another of our toes as its own (`shared`: the margin in mm
    # over which it fades; where the scan's 1.4 mm mesh bridges two toes, the clefts' floors and the walls pressed
    # together under its bridges), not every wall within `reach` of another toe (133 cage vertices a foot before): a
    # wall whose nearest scan point is its own toe's follows the scan's soft groove, and `close` then lays the hallux's
    # wall against toe 2's along their length (the scan's hallux lies against toe 2; ours stood 1.5-3 mm off it)
    "keep": {"reach": 6.0, "cone_deg": 42.0, "rays": 10, "occ": [0.12, 0.4], "rings": 1, "own": 0.3,
             "shared": [0.6, 2.0]},
    "close": {"pairs": [[1, 2]], "gap": 0.3, "full": 2.5, "reach": 4.5, "rounds": 6, "keep": [0.1, 0.5], "smooth": 3},
    "iters": 16,
    "mu": [4.0, 0.04],        # smoothness of the displacement, first and last iteration (geometric in between)
    "max_dist": [24.0, 8.0],  # the farthest nearest point accepted, first and last iteration (mm)
    "facing": 0.15,           # least cosine between our normal and the scan face's
    "retire": "all",          # pass A's amounts set to 0 under the transfer (or a list of name prefixes) ...
    "keep_fields": [],        # ... but these (the fitted metatarsal heads' line, mt_back_1 and mt_back_5, moved toes
                              # 3 and 4 back 6-10 mm short of the scan's; without it only toe 5 is long, and its base
                              # goes back in the prewarp: toes 1-4 keep MakeHuman's joints, where the rig's bones are)
    "base_share": 0.6,        # a toe longer than the scan's: this share of the difference carries its base back
    "prewarp": 1,
    "cg_iters": 400,
    "helper_sigma": 4.0,      # the helpers follow the skin within this (Gaussian, mm)
    "contact_gap": 0.2,       # the toes' contacts resolved after the transfer to this gap (fields.resolve_contacts;
                              # pressed together, a few cage vertices still read up to 0.2 mm inside a neighbour)
    "floor_flat": [1.0, 2.2],  # the loaded key: what lies within [0] mm of the floor goes onto it (the scans read
                               # contact as under 1 mm), fading by [1]
}


def config(params=None):
    """DEFAULTS with params.json's "transfer" merged one level deep."""
    got = (params or {}).get("transfer") or {}
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULTS.items()}
    for k, v in got.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


def smootherstep(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


# --------------------------------------------------------------------------- the reference surface

class Surface:
    """A triangle mesh to project onto (mm, any frame): nearest points with their face normals, and rays."""

    def __init__(self, q, T):
        self.q, self.T = np.asarray(q, float), np.asarray(T, np.int64)
        self.fn = scanref.tri_normals(self.q, self.T)
        try:
            from mathutils.bvhtree import BVHTree
            self.tree = BVHTree.FromPolygons(self.q.tolist(), self.T.tolist(), all_triangles=True)
            self.kd = None
        except ImportError:   # the image venv: nearest sample points (0.25 mm apart) instead of exact projections
            from scipy.spatial import cKDTree
            self.tree = None
            self.pts, self.pid = scanref.sample_tris(self.q, self.T, 0.25)
            self.kd = cKDTree(self.pts)

    def nearest(self, P, phong=0.0):
        """(points, face normals, distances) nearest to each of P. With `phong` (0-1) the point is lifted off its flat
        facet onto Phong tessellation's curved patch through the facet's corners (each corner's tangent plane by its
        vertex normal, blended by the barycentric weights; Boubekeur and Alexa 2008): the scan's 1.5 mm facets would
        otherwise print on a dense skin laid on them."""
        P = np.asarray(P, float)
        if self.tree is None:
            d, j = self.kd.query(P)
            return self.pts[j], self.fn[self.pid[j]], d
        from mathutils import Vector
        C = np.empty_like(P)
        N = np.empty_like(P)
        D = np.empty(len(P))
        I = np.empty(len(P), np.int64)
        for i, p in enumerate(P.tolist()):
            loc, nrm, idx, dist = self.tree.find_nearest(Vector(p))
            C[i], I[i], D[i] = loc, idx, dist
        N[:] = self.fn[I]
        if phong:
            if getattr(self, "vn", None) is None:
                self.vn = scanref.vertex_normals(self.q, self.T)
            A, B, Cc = (self.q[self.T[I, j]] for j in range(3))
            b = _barycentric(C, A, B, Cc)
            star = np.zeros_like(C)
            for j, X0 in enumerate((A, B, Cc)):
                n = self.vn[self.T[I, j]]
                proj = C - np.einsum("ij,ij->i", C - X0, n)[:, None] * n
                star += b[:, j:j + 1] * proj
            C = (1.0 - phong) * C + phong * star
            D = np.linalg.norm(C - P, axis=1)
        return C, N, D


def _barycentric(P, A, B, C):
    """Barycentric weights (n, 3) of points P in triangles ABC (each point on its own triangle)."""
    v0, v1, v2 = B - A, C - A, P - A
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-18)
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    out = np.clip(np.stack([1.0 - v - w, v, w], 1), 0.0, 1.0)
    return out / out.sum(1, keepdims=True)


def without_cap(q, T, cut_z, margin=1.5):
    """The scan's triangles less its flat top (the cut capped at cut_z): faces near the cut facing up."""
    fn = scanref.tri_normals(q, T)
    cz = q[T].mean(axis=1)[:, 2]
    return T[~((cz > cut_z - margin) & (fn[:, 2] > 0.7))]


def scan_tips(q, T, middle=0.25, front=0.5):
    """The scan's toes along its front: five (x, y) tips, medial first, from scanref.toe_line's clefts and anterior
    outline. A toe's tip is the most forward point of its outline over the middle of its stretch between clefts (the
    stretch less `middle` of its width at each end): toe_line's own tip, the most forward point over the whole
    stretch, falls on the slope of a longer neighbour (038: toe 3 on toe 2's flank, toe 5 on toe 4's), where a
    pressed-together toe's outline keeps falling; x is the centre of the outline within `front` mm of that point."""
    pts, _ = scanref.sample_tris(q, T, 0.6)
    tl = scanref.toe_line(pts)
    xs, fr = tl["xs"], tl["front"]
    ok = np.isfinite(fr)
    edges = [float(xs[ok][0])] + list(tl["clefts"]) + [float(xs[ok][-1])]
    tips = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = middle * (b - a)
        w = ok & (xs >= a + m) & (xs <= b - m)
        if not w.any():
            w = ok & (xs >= a) & (xs <= b)
        y0 = float(np.min(fr[w]))
        tips.append([float(xs[w & (fr < y0 + front)].mean()), y0])
    if len(tips) != 5:
        raise ValueError(f"the scan's toe line reads {len(tips)} toes (clefts at {tl['clefts']}), not five")
    return np.array(tips, float), tl


# --------------------------------------------------------------------------- the cage

class Cage:
    """One foot's region as the transfer sees it: rows (region rows of the body), quads (region rows), the body's
    rows, the Catmull-Clark limit stencil of every vertex whose ring is complete, and the edge list."""

    def __init__(self, quads, n, body):
        self.n = n
        self.quads = np.asarray(quads, np.int64)
        self.body = np.asarray(body, bool)
        Q = self.quads
        e = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
        e.sort(axis=1)
        self.edges = np.unique(e, axis=0)
        # valence (incident quads), edge neighbours and the opposite corners of each incident quad
        val = np.bincount(Q.ravel(), minlength=n)
        rows, cols, vals = [], [], []
        ne = np.bincount(self.edges.ravel(), minlength=n)
        # interior vertices: as many edges as quads (a boundary vertex has one more edge)
        self.interior = (val > 0) & (ne == val)
        nv = np.maximum(val, 1).astype(float)
        den = nv * (nv + 5.0)
        # centre n^2 / (n (n + 5))
        idx = np.nonzero(self.interior)[0]
        rows.append(idx)
        cols.append(idx)
        vals.append((nv[idx] ** 2) / den[idx])
        # each edge: 4 / (n (n + 5)) for both ends
        for a, b in ((0, 1), (1, 0)):
            r, c = self.edges[:, a], self.edges[:, b]
            ok = self.interior[r]
            rows.append(r[ok])
            cols.append(c[ok])
            vals.append(4.0 / den[r[ok]])
        # each quad's opposite corner: 1 / (n (n + 5))
        for i in range(4):
            r, c = Q[:, i], Q[:, (i + 2) % 4]
            ok = self.interior[r]
            rows.append(r[ok])
            cols.append(c[ok])
            vals.append(1.0 / den[r[ok]])
        self.S = (np.concatenate(rows), np.concatenate(cols), np.concatenate(vals))
        tri = np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
        self.tris = tri

    def limit(self, q):
        """Limit positions (vertices without a complete ring keep their own)."""
        r, c, v = self.S
        out = np.asarray(q, float).copy()
        L = np.zeros_like(out)
        for k in range(3):
            L[:, k] = np.bincount(r, weights=v * q[c, k], minlength=self.n)
        out[self.interior] = L[self.interior]
        return out

    def normals(self, q):
        n = np.zeros_like(q)
        Q = self.quads
        fn = np.cross(q[Q[:, 2]] - q[Q[:, 0]], q[Q[:, 3]] - q[Q[:, 1]])
        for i in range(4):
            for k in range(3):
                n[:, k] += np.bincount(Q[:, i], weights=fn[:, k], minlength=self.n)
        return n / np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]


# --------------------------------------------------------------------------- solving

def _cg(apply, b, x0, iters, tol=1e-6):
    x = x0.copy()
    r = b - apply(x)
    p = r.copy()
    rr = float((r * r).sum())
    b2 = max(float((b * b).sum()), 1e-30)
    for _ in range(iters):
        if rr < tol * tol * b2:
            break
        Ap = apply(p)
        alpha = rr / max(float((p * Ap).sum()), 1e-30)
        x += alpha * p
        r -= alpha * Ap
        rr_new = float((r * r).sum())
        p = r + (rr_new / rr) * p
        rr = rr_new
    return x


class Solver:
    """sum_i w_i |(S U)_i - g_i|^2 + mu sum_edges e_ab |U_a - U_b|^2 over the free vertices' U (the others held at
    0), with S the limit stencil (identity when limit=False: a dense skin, already its own limit) and e the edges'
    weights (1 unless edge_w is given)."""

    def __init__(self, cage, free, limit=True, edge_w=None):
        self.c = cage
        self.free = np.asarray(free, bool)
        self.ew = None if edge_w is None else np.asarray(edge_w, float)[:, None]   # per edge (a dense skin's 1 / l^2)
        r, c, v = cage.S
        if limit:
            ok = cage.interior[r]
            self.S = (r[ok], c[ok], v[ok])
            # rows without a complete ring are their own limit
            idx = np.nonzero(~cage.interior)[0]
            self.S = (np.concatenate([self.S[0], idx]), np.concatenate([self.S[1], idx]),
                      np.concatenate([self.S[2], np.ones(len(idx))]))
        else:
            idx = np.arange(cage.n)
            self.S = (idx, idx, np.ones(cage.n))
        e = cage.edges
        self.ea, self.eb = e[:, 0], e[:, 1]
        self.deg = np.bincount(e.ravel(), minlength=cage.n).astype(float)

    def _S(self, U):
        r, c, v = self.S
        out = np.zeros_like(U)
        for k in range(U.shape[1]):
            out[:, k] = np.bincount(r, weights=v * U[c, k], minlength=self.c.n)
        return out

    def _St(self, Y):
        r, c, v = self.S
        out = np.zeros_like(Y)
        for k in range(Y.shape[1]):
            out[:, k] = np.bincount(c, weights=v * Y[r, k], minlength=self.c.n)
        return out

    def _lap(self, U):
        d = U[self.ea] - U[self.eb]
        if self.ew is not None:
            d = d * self.ew
        out = np.zeros_like(U)
        for k in range(U.shape[1]):
            out[:, k] = np.bincount(self.ea, weights=d[:, k], minlength=self.c.n) - \
                np.bincount(self.eb, weights=d[:, k], minlength=self.c.n)
        return out

    def solve(self, w, g, mu, U0, iters=400):
        fr = self.free[:, None]

        def apply(U):
            U = U * fr
            return (self._St(w[:, None] * self._S(U)) + mu * self._lap(U)) * fr

        b = self._St(w[:, None] * g) * fr
        return _cg(apply, b, U0 * fr, iters) * fr


# --------------------------------------------------------------------------- the steps

def rezero_params(q, tris, tip2):
    """(R, o) taking this foot's F coordinates into the scans' frame (scanfit.rezero on points sampled on its quads'
    triangles: the cage's few heel vertices alone cannot find the heel's centre)."""
    from parts.p01 import scanfit
    pts, _ = scanref.sample_tris(q, tris, 0.5)
    _, (R, o) = scanfit.rezero(pts, tip2)
    return R, o


def to_frame(p, R, o):
    out = np.asarray(p, float).copy()
    out[..., :2] = p[..., :2] @ R - o
    return out


def from_frame(p, R, o):
    out = np.asarray(p, float).copy()
    out[..., :2] = (p[..., :2] + o) @ R.T
    return out


def our_tips(q, w, body, front=1.5):
    """Each toe's tip in plan as toe_line reads one: the centre of its skin within `front` mm of its most forward point."""
    out = []
    for k in TOES:
        t = q[(w[:, k - 1] > 0.5) & body]
        y0 = t[:, 1].min()
        f = t[t[:, 1] < y0 + front]
        out.append([float(f[:, 0].mean()), float(y0)])
    return np.array(out)


def prewarp(q, w, joints, ours, theirs, ramp=(-0.06, 0.1), base_share=0.6, base_sigma=10.0):
    """Each toe turned about its MTP joint in plan and stretched along its axis, its tip from `ours` to `theirs`; the
    toe's own weight times a ramp along it (nothing behind the joint, all of it from `ramp[1]` of the toe's length
    ahead of it), so a toe is turned and scaled evenly along its length. A toe the scan's is shorter than is first
    carried back whole by `base_share` of the shortfall, its joint with it and the forefoot's skin round the joint
    (fading over `base_sigma` mm), and compressed by the rest: 038's toe 5 ends 20 mm behind MakeHuman's, and pressed
    into the scan's 14 mm ahead of the joint all its rings crumpled into a slab. Returns (positions, per-toe record)."""
    q = np.asarray(q, float).copy()
    rec = {}
    other = 1.0 - np.clip(w.sum(axis=1), 0.0, 1.0)
    for k in TOES:
        m = np.asarray(joints[f"toe-{k}-1"], float)
        a0 = ours[k - 1] - m[:2]
        u = a0 / np.linalg.norm(a0)
        short = np.linalg.norm(a0) - np.linalg.norm(theirs[k - 1] - m[:2])
        back = base_share * short if short > 0.0 else 0.0
        if back:
            rel = q[:, :2] - m[:2]
            t = rel @ u
            v = rel - np.outer(t, u)
            wk = np.clip(w[:, k - 1], 0.0, 1.0) * smootherstep(t, -6.0, 0.0)
            soft = other * np.exp(-0.5 * (np.maximum(-t, 0.0) ** 2 + (v ** 2).sum(axis=1)) / base_sigma ** 2)
            q[:, :2] -= (np.maximum(wk, soft) * back)[:, None] * u[None, :]
            m = m.copy()
            m[:2] -= back * u
            ours = ours.copy()
            ours[k - 1] = ours[k - 1] - back * u
        a0, a1 = ours[k - 1] - m[:2], theirs[k - 1] - m[:2]
        L0, L1 = np.linalg.norm(a0), np.linalg.norm(a1)
        th = math.atan2(a1[1], a1[0]) - math.atan2(a0[1], a0[0])
        rel = q[:, :2] - m[:2]
        t = rel @ u
        v = rel - np.outer(t, u)
        st = np.outer(t * (L1 / L0), u) + v
        c, s = math.cos(th), math.sin(th)
        rot = np.stack([c * st[:, 0] - s * st[:, 1], s * st[:, 0] + c * st[:, 1]], 1)
        wk = np.clip(w[:, k - 1], 0.0, 1.0) * smootherstep(t / L0, ramp[0], ramp[1])
        q[:, :2] += wk[:, None] * (rot - rel)
        rec[k] = {"turn_deg": round(math.degrees(th), 2), "stretch_mm": round(L1 - L0, 2), "base_back_mm": round(back, 2),
                  "tip_from": np.round(ours[k - 1] + back * u, 2).tolist(), "tip_to": np.round(theirs[k - 1], 2).tolist()}
    return q, rec


def keep_mask(q, cage, w, body, cfg, region_z=(None, 60.0), surface=None):
    """The skin between the toes (DEFAULTS["keep"]): for every body vertex of the forefoot, rays in a cone about its
    normal (the normal and `rays` more at `cone_deg`); the share that meets a toe other than its own within `reach`
    mm, mapped through smoothstep(occ); with `surface` (the scan) and cfg["shared"], only where the vertex's nearest
    scan point (facing it) is shared: no further from another of our toes than from the vertex, fading out by
    shared[1] mm more (where the scan's 1.4 mm mesh bridges two toes, that point is on the bridge; where it lies on
    the vertex's own toe, the scan's groove is the toe's own and is followed); then grown `rings` rings at half
    strength (the blend into the transfer). A vertex's toe is its strongest toe weight over `own` (0: the foot)."""
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    n = len(q)
    lab = np.where(w.max(axis=1) > cfg["own"], np.argmax(w, axis=1) + 1, 0)
    T = cage.tris
    # a face's toe: the majority of its corners' (ties to the first)
    flab = np.array([np.bincount(lab[t], minlength=6).argmax() for t in T])
    tree = BVHTree.FromPolygons(q.tolist(), T.tolist(), all_triangles=True)
    nrm = cage.normals(q)
    toes_any = np.clip(w.sum(axis=1), 0.0, 1.0)
    cand = np.nonzero(body & (q[:, 2] < region_z[1]) & (toes_any > 0.05))[0]
    k = int(cfg["rays"])
    ang = math.radians(cfg["cone_deg"])
    reach = float(cfg["reach"])
    occ = np.zeros(n)
    for i in cand.tolist():
        nn = nrm[i]
        a = np.cross(nn, [0.0, 0.0, 1.0] if abs(nn[2]) < 0.9 else [1.0, 0.0, 0.0])
        a /= np.linalg.norm(a)
        b = np.cross(nn, a)
        dirs = [nn] + [math.cos(ang) * nn + math.sin(ang) * (math.cos(t) * a + math.sin(t) * b)
                       for t in np.linspace(0.0, 2.0 * math.pi, k, endpoint=False)]
        p0 = Vector((q[i] + 0.05 * nn).tolist())
        hits = 0
        for d in dirs:
            loc, _, fi, dist = tree.ray_cast(p0, Vector(d.tolist()), reach)
            if loc is not None and flab[fi] != lab[i] and flab[fi] != 0:
                hits += 1
        occ[i] = hits / float(len(dirs))
    m = S.smoothstep(occ, *cfg["occ"])
    if surface is not None and cfg.get("shared"):
        # each wall's nearest scan point (facing it), and that point's distance to the nearest other toe's limit
        # surface against its distance to the wall: shared (kept) where the other toe is as near, fading by shared[1]
        sel = np.nonzero(m > 0.0)[0]
        L = cage.limit(q)
        nl = cage.normals(q)
        Cp, N, D = surface.nearest(L[sel])
        facing = np.einsum("ij,ij->i", nl[sel], N) > 0.15
        trees = {}
        for k in range(1, 6):
            tk = T[(lab[T] == k).all(axis=1)]
            if len(tk):
                trees[k] = BVHTree.FromPolygons(L.tolist(), tk.tolist(), all_triangles=True)
        other = np.full(len(sel), np.inf)
        for j, i in enumerate(sel.tolist()):
            p = Vector(Cp[j].tolist())
            for k, tr in trees.items():
                if k == lab[i]:
                    continue
                hit = tr.find_nearest(p, float(D[j]) + float(cfg["shared"][1]) + 1.0)
                if hit[0] is not None:
                    other[j] = min(other[j], hit[3])
        own_d = np.where(facing, D, 0.0)
        sh = 1.0 - S.smoothstep(other - own_d, *cfg["shared"])
        m[sel] *= np.where(facing, sh, 1.0)
    # grow by rings: each ring takes half of its strongest neighbour's (the cage's next ring is the blend: 2-4 mm on
    # the toes)
    ea, eb = cage.edges[:, 0], cage.edges[:, 1]
    for _ in range(int(cfg["rings"])):
        nb = np.zeros(n)
        np.maximum.at(nb, ea, m[eb])
        np.maximum.at(nb, eb, m[ea])
        m = np.maximum(m, 0.5 * nb * body)
    return m * body, occ


def _extents(P):
    return np.array([P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max()])


def leg_align(q, cage, ref, cfg):
    """Our leg laid on the scan's at the cut (DEFAULTS["leg"], round 3b's fixes): the limit surface's horizontal
    sections over `band` against the scan's (the foot's front left out: y over -160), their mean extents across (x)
    and along (y); each point moved in plan by the map taking ours onto the scan's (the centre, and with `scale` the
    breadths), by a weight rising over `below` and easing out over `ease` (smootherstep), so the leg above the cut
    runs on from the scan's ankle and returns to its own by ease[1]. Returns (positions, record)."""
    from parts.p01 import scanfit
    c = cfg.get("leg") or {}
    if not c.get("on"):
        return q, None
    L = cage.limit(q)
    ours, theirs = [], []
    for z in np.arange(c["band"][0], c["band"][1] + 0.1, 2.0):
        a = scanfit.section_points(L, cage.tris, 2, float(z))
        b = scanfit.section_points(ref.q, ref.T, 2, float(z))
        a, b = a[a[:, 1] > -160.0], b[b[:, 1] > -160.0]
        if len(a) > 20 and len(b) > 20:
            ours.append(_extents(a))
            theirs.append(_extents(b))
    if not ours:
        return q, None
    eo, es = np.mean(ours, axis=0), np.mean(theirs, axis=0)
    co, cs = np.array([eo[0] + eo[1], eo[2] + eo[3]]) / 2.0, np.array([es[0] + es[1], es[2] + es[3]]) / 2.0
    sc = np.array([(es[1] - es[0]) / (eo[1] - eo[0]), (es[3] - es[2]) / (eo[3] - eo[2])]) if c.get("scale", 1) \
        else np.ones(2)
    z = q[:, 2]
    w = smootherstep(z, *c["below"]) * (1.0 - smootherstep(z, *c["ease"]))
    mapped = cs + (q[:, :2] - co) * sc
    out = q.copy()
    out[:, :2] += w[:, None] * (mapped - q[:, :2])
    return out, {"ours": np.round(eo, 2).tolist(), "scan": np.round(es, 2).tolist(),
                 "shift_mm": np.round(cs - co, 2).tolist(), "scale": np.round(sc, 4).tolist()}


def close_pairs(cage, q, W, body, keep, cfg, say=None):
    """Each facing pair of toe walls laid together (DEFAULTS["close"], round 3b's fixes: the hallux stood 1.5-3 mm off
    toe 2 along its distal 35-40 mm, the scan's lying against it): on the limit surface, each wall point of toe a within
    `reach` of toe b's surface (signed, along b's normal) moved toward it by half the gap less `gap`, fully under `full`
    and fading by `reach`, only on the walls the transfer kept (keep over cfg["keep"]: the outer surfaces stay on the
    scan); the move put on the cage (a limit point moves by about half its vertex's move, so `rounds` rounds) and
    smoothed over `smooth` rings. Returns (positions, record)."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    lab = toe_labels(W)
    gate = S.smoothstep(keep, *cfg["keep"]) * body
    ea, eb = cage.edges[:, 0], cage.edges[:, 1]
    deg = np.maximum(np.bincount(cage.edges.ravel(), minlength=cage.n), 1).astype(float)
    q = q.copy()
    rec = {}
    for r in range(int(cfg["rounds"])):
        L = cage.limit(q)
        nrm = cage.normals(q)
        d = np.zeros_like(q)
        for a, b in cfg["pairs"]:
            tb = cage.tris[(lab[cage.tris] == b).all(axis=1)]
            ta = cage.tris[(lab[cage.tris] == a).all(axis=1)]
            if not len(tb) or not len(ta):
                continue
            for src, tt in ((a, tb), (b, ta)):
                tree = BVHTree.FromPolygons(L.tolist(), tt.tolist(), all_triangles=True)
                idx = np.nonzero((lab == src) & (gate > 0.0))[0]
                for i in idx.tolist():
                    loc, n, fi, dist = tree.find_nearest(Vector(L[i].tolist()), float(cfg["reach"]) + 1.0)
                    if loc is None:
                        continue
                    n = np.array(n)
                    if float(np.dot(nrm[i], n)) > -0.3:     # not facing it
                        continue
                    s = float(np.dot(L[i] - np.array(loc), n))
                    wgt = (1.0 - float(S.smoothstep(s, cfg["full"], cfg["reach"]))) * gate[i]
                    d[i] += -0.5 * (s - cfg["gap"]) * wgt * n
                    if r == 0:
                        rec.setdefault(f"{a}-{b}", []).append(s)
        for _ in range(int(cfg["smooth"])):
            avg = np.zeros_like(d)
            for k in range(3):
                avg[:, k] = (np.bincount(ea, weights=d[eb, k], minlength=cage.n)
                             + np.bincount(eb, weights=d[ea, k], minlength=cage.n)) / deg
            moved = np.linalg.norm(d, axis=1) > 0.0
            d = np.where(moved[:, None], 0.5 * (d + avg), 0.5 * avg * gate[:, None])
        q += d
    out = {k: {"n": len(v), "gap_min": round(float(min(v)), 2), "gap_max": round(float(max(v)), 2)}
           for k, v in rec.items()}
    if say:
        say(f"transfer close_pairs: {out}")
    return q, out


def fit(cage, q0, surface, keep, blend, free, cfg, say=None, limit=True):
    """The fit of the module's step 3. q0: the prewarped cage (F-like mm, the surface's frame); keep, blend: per vertex;
    free: the vertices that may move. Returns (q, report)."""
    sol = Solver(cage, free, limit=limit)
    L0 = cage.limit(q0) if limit else q0.copy()
    U = np.zeros_like(q0)
    n_it = int(cfg["iters"])
    mu0, mu1 = cfg["mu"]
    d0, d1 = cfg["max_dist"]
    rep = []
    act = np.nonzero(free & (keep < 1.0) & (blend > 0.0))[0]
    for it in range(n_it):
        f = it / max(n_it - 1, 1)
        mu = mu0 * (mu1 / mu0) ** f
        dmax = d0 + (d1 - d0) * f
        q = q0 + U
        L = cage.limit(q) if limit else q
        nrm = cage.normals(q)
        C, N, D = surface.nearest(L[act])
        ok = (D < dmax) & (np.einsum("ij,ij->i", nrm[act], N) > cfg["facing"])
        w = np.zeros(len(q0))
        g = np.zeros_like(q0)
        tgt = C
        w[act[ok]] = (1.0 - keep[act[ok]]) * blend[act[ok]]
        g[act[ok]] = tgt[ok] - L0[act[ok]]
        # the leg held where it was from `hold` mm over the cut up; between the cut and there no data, the displacement
        # carried on smoothly up the leg
        held = free & (q0[:, 2] > cfg["blend_z"][1] + cfg["hold"])
        w[held] = 1.0
        g[held] = 0.0
        U = sol.solve(w, g, mu, U, iters=int(cfg["cg_iters"]))
        # the residual where the scan is meant to hold fully (below the blend, away from the kept skin)
        full = ok & (blend[act] > 0.999) & (keep[act] < 0.05)
        res = np.linalg.norm((cage.limit(q0 + U) if limit else q0 + U)[act[full]] - tgt[full], axis=1)
        rep.append({"it": it, "mu": round(mu, 4), "n": int(ok.sum()), "of": int(len(act)), "full": int(full.sum()),
                    "rms": round(float(np.sqrt(np.mean(res ** 2))), 3), "max": round(float(res.max()), 2)})
        if say:
            say(f"transfer it {it}: mu {mu:.3g}, {ok.sum()}/{len(act)} on the scan, residual rms {rep[-1]['rms']} "
                f"max {rep[-1]['max']}")
    return q0 + U, rep


def follow(q_before, q_after, rows_from, rows_to, label, sigma):
    """Helpers (rows_to) moved by the Gaussian-weighted mean displacement of the skin (rows_from) near them, the skin
    of their own toe where they have one (label: a toe per row, 0 for the foot)."""
    d = q_after - q_before
    out = q_after.copy()
    for i in rows_to:
        same = rows_from[label[rows_from] == label[i]] if label[i] else rows_from
        if not len(same):
            same = rows_from
        r2 = ((q_before[same] - q_before[i]) ** 2).sum(axis=1)
        g = np.exp(-0.5 * r2 / (sigma * sigma))
        if g.sum() < 1e-6:
            j = same[np.argsort(r2)[:6]]
            out[i] = q_before[i] + d[j].mean(axis=0)
        else:
            out[i] = q_before[i] + (g[:, None] * d[same]).sum(axis=0) / g.sum()
    return out


# --------------------------------------------------------------------------- the reference and a foot's transfer

class Reference:
    """A scan as the transfer's target, in the scans' frame: its surface less the cap, its toes' tips, its info."""

    def __init__(self, q, T, info):
        self.q, self.info = np.asarray(q, float), info
        self.T = without_cap(self.q, np.asarray(T, np.int64), info["cut_z"])
        self.tips, self.toe_line = scan_tips(self.q, self.T)
        self.surface = Surface(self.q, self.T)


def load_reference(sid, cond="mBW", path=None, align_to=None):
    """scanref.load's scan as a Reference; with `align_to` (the unloaded Reference) a loaded scan is first laid on it
    by register() (its footprint where it lies, its leg's posture taken out)."""
    q, T, info = scanref.load(sid, cond, path)
    if align_to is not None:
        q, rec = register(q, T, align_to)
        info = dict(info, registered=rec)
    return Reference(q, T, info)


def register(q, T, ref, band=(100.0, 120.0), fade=(40.0, 95.0)):
    """A loaded scan laid on its unloaded twin. Both already share the heel (its centre at x 0, the pternion at y 0)
    and the footprint's axis (to toe 2's tip), which stay put on the floor under load; standing, the leg sits about
    6 mm further medial over that footprint than seated (038: the sections at z 100-120), the foot pronating under
    it. The character's leg is the rig's, so the posture is taken out: every point moved in plan by minus the leg's
    offset (the mean of the sections' centres over `band`, the twin's taken from it), fully above fade[1] and not at
    all below fade[0], so the leg meets the seated one where the transfer hands over to ours and the footprint stays
    where it lies. Returns (q, record)."""
    from parts.p01 import scanfit

    def centres(qq, TT):
        out = []
        for z in np.arange(band[0], band[1] + 0.1, 5.0):
            s = scanfit.section_points(qq, TT, 2, float(z))
            s = s[s[:, 1] > -160.0]
            out.append([0.5 * (s[:, 0].min() + s[:, 0].max()), 0.5 * (s[:, 1].min() + s[:, 1].max())])
        return np.mean(out, axis=0)

    off = centres(np.asarray(q, float), T) - centres(ref.q, ref.T)
    out = np.asarray(q, float).copy()
    out[:, :2] -= smootherstep(out[:, 2], *fade)[:, None] * off[None, :]
    return out, {"leg_offset_mm": np.round(off, 2).tolist(), "fade_z": list(fade), "band_z": list(band)}


def joints_now(foot, q):
    """Each toe's MTP joint (its joint cube's centre) on positions q (F, mm)."""
    out = {}
    for k in TOES:
        rows = foot.cube_rows.get(f"toe-{k}-1")
        out[f"toe-{k}-1"] = q[rows].mean(axis=0) if rows is not None and len(rows) else np.asarray(foot.joint[f"toe-{k}-1"])
    return out


def toe_labels(w, own=0.3):
    return np.where(w.max(axis=1) > own, np.argmax(w, axis=1) + 1, 0)


def placement(foot, q, cage):
    """(R, o): the scans' frame of this foot as it stands before the transfer (scan.py's re-zeroing: the heel's
    centre, the line to toe 2's tip, the pternion)."""
    body = foot.body
    t2 = q[(foot.w[2] > 0.5) & body]
    return rezero_params(q, cage.tris, t2[np.argmin(t2[:, 1])])


def run(foot, q, cage, ref, cfg, place=None, keep=None, say=None, align_leg=True):
    """One foot's transfer onto `ref` from positions q (frame F, mm, the region's rows). Returns (positions, record);
    the record keeps the placement and the masks for the loaded key and the masks stage. align_leg False (the loaded
    key, which starts from the transferred rest, its leg already laid on the seated scan) leaves the leg as it is."""
    body = foot.body
    W = np.stack([foot.w[k] for k in TOES], 1)
    R, o = place if place is not None else placement(foot, q, cage)
    qs = to_frame(q, R, o)
    rec = {"R": R, "o": o}
    if cfg.get("prewarp", 1):
        js = {k: to_frame(v[None], R, o)[0] for k, v in joints_now(foot, q).items()}
        ours = our_tips(qs, W, body)
        qw, rec["prewarp"] = prewarp(qs, W, js, ours, ref.tips, base_share=float(cfg.get("base_share", 0.6)))
    else:
        qw = qs
    if align_leg:
        qw, rec["leg"] = leg_align(qw, cage, ref, cfg)
    if keep is None:
        keep, _ = keep_mask(qw, cage, W, body, cfg["keep"], surface=ref.surface)
    blend = 1.0 - smootherstep(qs[:, 2], *cfg["blend_z"])
    free = body & (qs[:, 2] < cfg["blend_z"][1] + cfg["hold"] + 15.0)
    qf, rep = fit(cage, qw, ref.surface, keep, blend, free, cfg, say=say)
    if (cfg.get("close") or {}).get("pairs"):
        qf, rec["close"] = close_pairs(cage, qf, W, body, keep, cfg["close"], say=say)
    # the helpers (MakeHuman's joint cubes and the rest of its helper geometry) follow their toe's skin
    lab = toe_labels(W)
    helpers = np.nonzero(~body & (qs[:, 2] < cfg["blend_z"][1] + cfg["hold"] + 15.0))[0]
    qf = follow(qs, qf, np.nonzero(body & free)[0], helpers, lab, cfg["helper_sigma"])
    rec.update(keep=keep, blend=blend, fit=rep, tips_scan=np.round(ref.tips, 2).tolist())
    return from_frame(qf, R, o), rec


def floor_flat(cage, q, z0, z1, rounds=4):
    """The loaded foot's contact pressed flat on the floor (z 0, frame F): cage vertices whose limit lies below z1 are
    moved down by their limit's height (all of it below z0, fading to none at z1), a few rounds (a vertex's limit
    leans on its neighbours), then nothing below the floor."""
    q = q.copy()
    for _ in range(rounds):
        L = cage.limit(q)
        w = 1.0 - smootherstep(L[:, 2], z0, z1)
        q[:, 2] -= w * L[:, 2] * cage.body
    q[:, 2] = np.where(cage.body, np.maximum(q[:, 2], 0.0), q[:, 2])
    return q
