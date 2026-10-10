"""Method (b)'s large forms: the forefoot as a signed distance field (frame F, mm), edited by smooth
combinations with anatomical primitives, and realised either by polygonising the field (method b proper:
OpenVDB's volume-to-mesh, a new topology) or by projecting the dense MakeHuman-derived skin onto it (the
hybrid: the field's shape on the base mesh's topology, UVs and weights).

The field is an OpenVDB level set of the dense skin, cropped at y_F `y_cut` and capped (a level set needs a
closed surface), with a narrow band wide enough for the edits (`half_mm`). A box around the region is
copied into numpy, edited slab by slab, and written back. Primitives are approximate distances (Inigo
Quilez's ellipsoid bound, spheres, capsules); a union is a polynomial smooth minimum whose radius k is the
fillet the two forms share, which is what makes a pulp or a prominence grow out of the toe rather than sit
on it. The web is a morphological closing (dilate by r, re-distance, erode by r) masked to the cleft's
floor: it fills a concavity narrower than 2r there and nowhere else, as a fill brush would.
"""
import numpy as np

import toes as T


# --------------------------------------------------------------------------- primitives and operators

def smin(a, b, k):
    """Polynomial smooth minimum (union) with fillet radius k."""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def smax(a, b, k):
    """Smooth maximum (intersection; with -b, a subtraction)."""
    return -smin(-a, -b, k)


def ellipsoid(P, seg, centre_tuh, radii_tuh):
    """An ellipsoid given in a segment's frame (centre and radii as (t, u, h)): Quilez's bound."""
    t, u, h = seg.local(P)
    p = np.stack([t - centre_tuh[0], u - centre_tuh[1], h - centre_tuh[2]], -1)
    r = np.asarray(radii_tuh, float)
    k0 = np.linalg.norm(p / r, axis=-1)
    k1 = np.linalg.norm(p / (r * r), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def sphere(P, c, r):
    return np.linalg.norm(P - np.asarray(c), axis=-1) - r


def capsule(P, pts, r):
    """Distance to a polyline less r."""
    pts = np.asarray(pts, float)
    best = np.full(P.shape[:-1], np.inf)
    for a, b in zip(pts[:-1], pts[1:]):
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0.0, 1.0)
        best = np.minimum(best, np.linalg.norm(P - (a + t[..., None] * ab), axis=-1))
    return best - r


# --------------------------------------------------------------------------- the field

class Field:
    """The forefoot's signed distance as an OpenVDB level set in frame F (mm)."""

    def __init__(self, q, quads, y_cut=-140.0, voxel=0.2, half_mm=4.5):
        import openvdb as vdb
        self.vdb, self.voxel, self.half = vdb, voxel, half_mm
        pts, tris, qd = crop_and_cap(q, quads, y_cut)
        self.xf = vdb.createLinearTransform(voxelSize=voxel)
        self.grid = vdb.FloatGrid.createLevelSetFromPolygons(
            pts.astype(np.float32), triangles=tris.astype(np.uint32), quads=qd.astype(np.uint32),
            transform=self.xf, halfWidth=half_mm / voxel)
        self.y_cut = y_cut
        self.A = None

    def box(self, lo, hi):
        """Copy the field over a box (F mm) into self.A; voxel (i, j, k) of A is at lo_ijk + (i, j, k)."""
        v = self.voxel
        self.lo = np.floor(np.asarray(lo, float) / v).astype(int)
        hi_i = np.ceil(np.asarray(hi, float) / v).astype(int)
        shape = tuple(int(x) for x in hi_i - self.lo + 1)
        self.A = np.zeros(shape, np.float32)
        self.grid.copyToArray(self.A, ijk=tuple(int(x) for x in self.lo))
        return self.A

    def slab_points(self, j0, j1):
        """World (F) coordinates of the box's voxels with j in [j0, j1): an (ni, j1 - j0, nk, 3) array."""
        v = self.voxel
        ni, _, nk = self.A.shape
        i = (self.lo[0] + np.arange(ni)) * v
        j = (self.lo[1] + np.arange(j0, j1)) * v
        k = (self.lo[2] + np.arange(nk)) * v
        I, J, K = np.meshgrid(i, j, k, indexing="ij")
        return np.stack([I, J, K], -1)

    def edit_local(self, fn, centre, radius):
        """Apply fn(P, f) -> f' only to the voxels within a sphere's bounding box (F mm): a primitive's
        influence ends at its radius plus its fillet, and most of the box is untouched by any one."""
        v = self.voxel
        lo = np.floor((np.asarray(centre) - radius) / v).astype(int) - self.lo
        hi = np.ceil((np.asarray(centre) + radius) / v).astype(int) - self.lo + 1
        lo = np.clip(lo, 0, np.array(self.A.shape))
        hi = np.clip(hi, 0, np.array(self.A.shape))
        if np.any(hi <= lo):
            return
        i = (self.lo[0] + np.arange(lo[0], hi[0])) * v
        j = (self.lo[1] + np.arange(lo[1], hi[1])) * v
        k = (self.lo[2] + np.arange(lo[2], hi[2])) * v
        I, J, K = np.meshgrid(i, j, k, indexing="ij")
        P = np.stack([I, J, K], -1)
        sub = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))
        self.A[sub] = fn(P, self.A[sub].astype(np.float64)).astype(np.float32)

    def edit(self, fn, slab=40):
        """Apply fn(P, f) -> f' over the box, slab by slab along y."""
        ny = self.A.shape[1]
        for j0 in range(0, ny, slab):
            j1 = min(ny, j0 + slab)
            P = self.slab_points(j0, j1)
            self.A[:, j0:j1, :] = fn(P, self.A[:, j0:j1, :].astype(np.float64)).astype(np.float32)

    def commit(self):
        """Write the edited box back into the level set (the band's clamp kept)."""
        bg = self.grid.background
        np.clip(self.A, -bg, bg, out=self.A)
        g = self.grid.deepCopy()
        g.copyFromArray(self.A, ijk=tuple(int(x) for x in self.lo), tolerance=0.0)
        self.grid = g

    def close(self, r, mask_fn, slab=40):
        """A morphological closing by r, blended in where mask_fn(P) > 0: dilate (the level set's r
        isosurface), re-distance it as a new level set, erode by r, then f + (closed - f) x mask (a closing only
        ever adds). The box is updated and committed."""
        vdb = self.vdb
        self.commit()
        pts, qd = self.grid.convertToQuads(isovalue=r)
        g2 = vdb.FloatGrid.createLevelSetFromPolygons(pts, quads=qd, transform=self.xf, halfWidth=self.half / self.voxel)
        D = np.zeros_like(self.A)
        g2.copyToArray(D, ijk=tuple(int(x) for x in self.lo))
        ny = self.A.shape[1]
        for j0 in range(0, ny, slab):
            j1 = min(ny, j0 + slab)
            P = self.slab_points(j0, j1)
            f = self.A[:, j0:j1, :]
            closed = D[:, j0:j1, :] + r
            m = mask_fn(P)
            self.A[:, j0:j1, :] = f + np.minimum(closed - f, 0.0) * m
        self.commit()

    def polygonise(self):
        pts, qd = self.grid.convertToQuads(isovalue=0.0)
        return pts.astype(np.float64), qd.astype(np.int64)

    def sample(self, P):
        """Trilinear samples of the edited box at points (F mm); NaN outside it."""
        v = self.voxel
        g = np.asarray(P, float) / v - self.lo
        i0 = np.floor(g).astype(int)
        f = g - i0
        n = np.array(self.A.shape)
        ok = np.all((i0 >= 0) & (i0 < n - 1), axis=1)
        out = np.full(len(P), np.nan)
        i0, f = i0[ok], f[ok]
        acc = np.zeros(len(i0))
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                    acc += w * self.A[i0[:, 0] + dx, i0[:, 1] + dy, i0[:, 2] + dz]
        out[ok] = acc
        return out

    def project(self, P, weight, iterations=4, h=0.1, max_step=3.0):
        """Move points onto the edited zero set by Newton steps along the field's gradient (central
        differences of the trilinear field), each scaled by weight; points off the box or the band stay."""
        P = np.asarray(P, float).copy()
        idx = np.nonzero(weight > 1e-4)[0]
        Q = P[idx]
        w = weight[idx]
        for _ in range(iterations):
            f = self.sample(Q)
            gx = (self.sample(Q + [h, 0, 0]) - self.sample(Q - [h, 0, 0])) / (2 * h)
            gy = (self.sample(Q + [0, h, 0]) - self.sample(Q - [0, h, 0])) / (2 * h)
            gz = (self.sample(Q + [0, 0, h]) - self.sample(Q - [0, 0, h])) / (2 * h)
            g = np.stack([gx, gy, gz], 1)
            gg = np.einsum("ij,ij->i", g, g)
            ok = np.isfinite(f) & np.isfinite(gg) & (gg > 1e-6) & (np.abs(f) < self.grid.background * 0.95)
            step = np.zeros_like(Q)
            step[ok] = -(f[ok] / gg[ok])[:, None] * g[ok]
            ln = np.linalg.norm(step, axis=1)
            step *= np.minimum(1.0, max_step / np.maximum(ln, 1e-9))[:, None]
            Q = Q + step * w[:, None]
        P[idx] = Q
        return P


def taper(P, pts):
    """0 along a polyline's middle, rising to 1 at and beyond its ends: a cord that thins out instead of
    ending in a knob."""
    pts = np.asarray(pts, float)
    a, b = pts[0], pts[-1]
    ab = b - a
    t = ((P - a) @ ab) / (ab @ ab)
    return 1.0 - T.window(t, -0.05, 0.25, 0.75, 1.05)


def crop_and_cap(q, quads, y_cut):
    """The quads wholly in front of y_cut and a fan over each hole the cut leaves (F, mm): (points,
    triangles, quads) for a closed level set."""
    keep = np.all(q[quads][:, :, 1] < y_cut, axis=1)
    qd = quads[keep]
    used = np.unique(qd)
    remap = np.full(len(q), -1, np.int64)
    remap[used] = np.arange(len(used))
    pts = q[used]
    qd = remap[qd]
    # boundary edges: used by one face only, oriented as their face has them
    e = np.concatenate([qd[:, [0, 1]], qd[:, [1, 2]], qd[:, [2, 3]], qd[:, [3, 0]]])
    key = np.sort(e, axis=1)
    _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    bnd = e[cnt[inv.ravel()] == 1]
    nxt = {int(a): int(b) for a, b in bnd}
    tris = []
    seen = set()
    extra = []
    for start in list(nxt):
        if start in seen:
            continue
        loop = [start]
        seen.add(start)
        cur = nxt[start]
        while cur != start and cur not in seen and cur in nxt:
            loop.append(cur)
            seen.add(cur)
            cur = nxt[cur]
        if len(loop) < 3:
            continue
        c = len(pts) + len(extra)
        extra.append(pts[loop].mean(axis=0))
        for a, b in zip(loop, loop[1:] + loop[:1]):
            tris.append((b, a, c))     # reversed: the cap faces out of the cut
    pts = np.vstack([pts] + ([np.array(extra)] if extra else []))
    return pts, np.array(tris, np.int64).reshape(-1, 3), qd


# --------------------------------------------------------------------------- the region's large forms

def region_forms(field, q, nrm, segs, groups, P, report):
    """Method (b)'s edits of the region, the counterparts of macro.apply's fields: the pulps and their
    noses (smooth unions of ellipsoids under and before each tip), the tips' top-front corners rounded
    (smooth subtractions), the first MTP prominence and the metatarsal head (spheres), the extensor tendons
    (capsules under the skin), then the 1-2 web (a closing of radius P['web_r'] masked to the cleft's floor).
    q, nrm: the dense skin (F) the anchors are found on."""
    import macro as M
    h2, t2d = segs["h2"], segs["t2d"]

    def station(seg, g, t0, side):
        """The skin's extreme height (side -1: the plantar surface, +1: the dorsum) near the toe's midline
        at station t0 of its segment frame."""
        mine = groups[g] > 0.5
        t, u, hh = seg.local(q[mine])
        uc = 0.5 * (u.min() + u.max())
        sel = (np.abs(t - t0) < 1.0) & (np.abs(u - uc) < 3.0)
        return float((hh[sel] * side).max() * side) if sel.any() else float(hh.min() if side < 0 else hh.max())

    tips = {}
    for name, seg, g in (("h", h2, "toe1-2.L"), ("2", t2d, "toe2-3.L")):
        mine = groups[g] > 0.5
        t = seg.local(q[mine])[0]
        tips[name] = float(t.max())
    mtp = segs["h1"].o
    c_prom = M.medial_point(q, mtp[1] + 3.0, mtp[2] - 8.0)
    i = np.argmin(np.linalg.norm(q - c_prom, axis=1))
    n_prom = nrm[i]
    top = M.skin_top(q, mtp[0], mtp[1] + 4.0)
    ehl = [M.skin_top(q, x, y) for x, y in ((-23.0, -168.0), (-26.0, -195.0), (mtp[0] + 2.0, mtp[1] - 8.0))]
    j2 = segs["t2p"].o
    edl = [M.skin_top(q, x, y) for x, y in ((-7.0, -170.0), (-5.5, -195.0), (j2[0] + 0.5, j2[1] - 6.0))]
    L, L2 = h2.length, t2d.length
    th, t2 = tips["h"], tips["2"]
    tp1, tp2 = 0.60 * L, 0.55 * L2
    pb1, pb2 = station(h2, "toe1-2.L", tp1, -1.0), station(t2d, "toe2-3.L", tp2, -1.0)    # the pads' undersides
    nb1, nb2 = station(h2, "toe1-2.L", th - 5.0, -1.0), station(t2d, "toe2-3.L", t2 - 3.0, -1.0)
    dt1, dt2 = station(h2, "toe1-2.L", th - 3.0, 1.0), station(t2d, "toe2-3.L", t2 - 2.0, 1.0)   # the dorsa near the tips
    r_prom = 11.0
    k = P.get("sdf_k", 1.0)
    report["sdf_stations"] = {"pulp1": pb1, "pulp2": pb2, "nose1": nb1, "nose2": nb2, "dorsum1": dt1, "dorsum2": dt2}

    def ell(seg, c_tuh, r_tuh):
        """An ellipsoid primitive and its bounding sphere (centre in F, radius)."""
        centre = seg.point(c_tuh[0], c_tuh[1], c_tuh[2])
        return (lambda Pts: ellipsoid(Pts, seg, c_tuh, r_tuh)), centre, max(r_tuh)

    ops = []   # (union +1 / subtraction -1, primitive, bounding centre, bounding radius, fillet)
    # the pulps: an ellipsoid under each distal phalanx, its underside `pulp` mm below the base's pad
    ops.append((1, *ell(h2, (tp1, 0.0, pb1 + 8.0 - P["pulp1"]), (11.5, 13.5, 8.0)), 3.0 * k))
    ops.append((1, *ell(t2d, (tp2, 0.0, pb2 + 5.0 - P["pulp2"]), (6.5, 7.0, 5.0)), 2.0 * k))
    # the noses: the pulp carried forward under the free edge
    ops.append((1, *ell(h2, (th - 6.0 + P["tip1"], 0.0, nb1 + 5.5), (6.5, 11.0, 5.5)), 2.5 * k))
    ops.append((1, *ell(t2d, (t2 - 3.5 + P["tip2"], 0.0, nb2 + 3.5), (3.8, 6.5, 3.5)), 1.5 * k))
    # the top-front corners rounded: an ellipsoid of air over each, subtracted
    ops.append((-1, *ell(h2, (th + 3.0, 0.0, dt1 + 6.0 - P["droop1"]), (9.0, 22.0, 6.0)), 2.5 * k))
    ops.append((-1, *ell(t2d, (t2 + 2.0, 0.0, dt2 + 4.0 - P["droop2"]), (5.5, 12.0, 4.0)), 1.5 * k))
    # the first MTP prominence and the head's knuckle
    cp = c_prom - n_prom * (r_prom - P["mtp_prom"])
    ops.append((1, lambda Pts: sphere(Pts, cp, r_prom), cp, r_prom, 6.0 * k))
    ch = top - np.array([0.0, 0.0, 8.0 - P["mt_head"]])
    ops.append((1, lambda Pts: sphere(Pts, ch, 8.0), ch, 8.0, 4.0 * k))
    # the extensor tendons: broad, low cords just under the skin, tapering out at both ends
    for pts, r, amt in ((ehl, P.get("ehl_r", 3.0), P["ehl"]), (edl, P.get("edl_r", 2.4), P["edl"])):
        axis = [p - np.array([0.0, 0.0, r - amt]) for p in pts]
        mid = np.mean(axis, axis=0)
        reach = max(np.linalg.norm(p - mid) for p in axis) + r
        ops.append((1, (lambda Pts, axis=axis, r=r: capsule(Pts, axis, r) + 0.6 * r * taper(Pts, axis)), mid, reach,
                    2.5 * k))

    for sign, prim, centre, radius, fil in ops:
        if sign > 0:
            field.edit_local(lambda Pts, f, prim=prim, fil=fil: smin(f, prim(Pts), fil), centre, radius + 2.0 * fil)
        else:
            field.edit_local(lambda Pts, f, prim=prim, fil=fil: smax(f, -prim(Pts), fil), centre, radius + 2.0 * fil)
    report["sdf_anchors"] = {"mtp_prominence": c_prom.round(2).tolist(), "tips": tips}
    if P.get("web_r", 0.0) > 0.0:
        a, b = segs["h1"].o, segs["t2p"].o
        xm, xw = 0.5 * (a[0] + b[0]), 0.5 * abs(b[0] - a[0])

        def web_mask(Pts):
            x, y, z = Pts[..., 0], Pts[..., 1], Pts[..., 2]
            return (1.0 - T.smoothstep(np.abs(x - xm), 0.45 * xw, 0.85 * xw)) \
                * T.window(y, P["web_y"] - 3.5, P["web_y"] + 0.5, a[1] + 6.0, a[1] + 14.0) \
                * (1.0 - T.smoothstep(z, 20.0, 27.0))

        field.close(P["web_r"], web_mask)
    else:
        field.commit()
