"""The sock of spec 01 §3.6, §4.10-4.11 (Sock.<S>.Body on its target Foot.<S>.SockTarget), and the envelope the
last shares (last.py, §4.13).

The foot the sock wraps is the body's rendered surface (Catmull-Clark level 2 of Body.Mesh, the scan-transferred
foot, with the nail plates as they render), not the 5 mm cage: the malleoli, the toes' tips and the nails stand
proud of the cage's chords by up to 2 mm. The sock is a tube of rings, lofted, not a cone shrinkwrapped onto a
remesh (§4.11 step 1 already rejected the cone; the remesh's 2.5 mm voxels and the shrinkwrap's sliding were the
rest of the problem):

  rings     sections of the foot by three families of planes in frame F: horizontal down the leg (z from the
            cuff's top to the fan's corner C), a fan of half-planes through a line across the foot at C (in the
            air in front of the shin and above the instep, so no two planes meet inside the foot) that turns
            from horizontal to vertical round the heel, and vertical across the foot from C to the toes' front.
            Each section's convex hull is one course of the knit: a stretched tube is a hoop under tension, so
            it spans the toes' clefts, the retro-malleolar hollows and the transverse vault as a tape does.
            Resampled at N points of equal arclength from a seam down the back of the leg, round the heel and
            along the middle of the sole, so the columns are wales; across the foot each ring keeps the columns of
            the one behind it (follow_ring), and over the toes holds it drawn in at 40 degrees (tube's taper), so
            a toe that ends between two sections tapers on instead of stepping in and folding the quads.
  envelope  the knit is also stretched along the leg: a membrane over an obstacle (the foot). Each vertex
            moves along its own normal line only (no sliding), pulled by the Laplacian of its ring and column
            neighbours and held at least `off` mm outside the outermost skin on that line (ray cast once).
            Over convex skin it stays on the skin; across a concavity (the notches between the toes' tips in
            plan, the sulcus, the ankle crease, the hollow over the Achilles) it spans.
  closing   the last ring, across the tips of the hallux and toe 2, is linked top to bottom like a real
            sock's toe (a row of quads, a triangle at each end), not a fan with a pole.
  render    the inner surface keeps its 0.3 mm where it renders, not only at its cage: the Catmull-Clark limit's
            sinking is made up (settle), and wherever Blender's own level-2 subdivision still dips under the skin
            the floors near it are raised (repair; inside by ray parity).

Sock.<S>.Body is the sock's inner surface 0.3 mm off its target, with a Solidify outward (§4.11 step 5; the
thickness per region from the `sock_thickness` group, §3.6), a Subdivision (1 / render 2) and the knit's
relief as a Geometry Nodes displacement on the outer shell after it (`Sock.GN.Knit`: the 1x1 cuff rib, the 2x2
leg rib, the arch band, the toe seam), so the ribs are geometry at the silhouette. UV.Real is metric: u the
share of the way round times C_REF (168 wales of 1.6 mm, so the stitches stretch with the girth as a real
knit's do), v the arclength along each wale from the cuff's top.
"""
import math

import numpy as np

from lib import sculpt as S

N_AROUND = 96                 # points per ring (a 1x1 rib of 3.6 mm needs ~5 samples a period at render level 2)
TOP_Z = 260.0                 # §3.6: the cuff's top
CUFF_Z = 228.0                # the welt's lower edge (32 mm folded double)
LEG_Z = 90.0                  # the 2x2 rib's lower end
FAN_Z = 120.0                 # the fan's corner height: above the malleoli and the ankle crease
FAN_MARGIN = 5.0              # C stands this far in front of the shin's foremost point above FAN_Z
LEG_STEP, FOOT_STEP, N_FAN = 3.0, 3.0, 36
OFFSET_MM = 0.3               # §4.11 step 2: the inner surface off its target
NEEDLES = 150                 # wales round the leg: §3.6's 168-needle cylinder knits 1.42 mm stitches on this lean leg
                              # (239 mm at z 160), under §1.4 item 8's 1.5-1.8; 150 gives 1.6 there (spec 01 §4.11 note)
C_REF = NEEDLES * 1.6         # mm: the UV's u at the full way round (the knit's 1.6 mm wale at C_REF)
THICK = {"leg": 1.6, "cuff": 2.4, "heel": 2.2, "toe": 2.2, "sole": 3.0}   # §3.6 (mm), unloaded
LOADED_SOLE = 0.6             # §3.5: under load the plantar thickness 3.0 -> 1.8
T_MAX = 3.0                   # the Solidify thickness; the group weight is t / T_MAX
RIB = {"leg": (36, 0.30, 3.5 / 7.5), "cuff": (72, 0.20, 0.5), "band": (72, 0.15, 0.5)}  # ribs round, half-relief
                              # (mm, §5.4: 0.6 / 0.4 / 0.3 strength about mid-level), ridge share of a period
SEAM_MM = 1.0                 # §3.6: the linked toe seam, 1 mm proud, 1.5 wide
MEMBRANE = {"iters": 300, "lam": 0.6, "hoop": 1.0, "length": 1.0}
GN_NAME = "Sock.GN.Knit"


# --------------------------------------------------------------------------- the foot's rendered surface

def skin_read(ob, frame, contact=0.0, nails=(), nail_shift=None, levels=2):
    """The body's evaluated surface at subdivision `levels` (the closeups' level 2), with Foot.Contact at
    `contact`, cut to one foot (frame F's box), plus the nail plates as evaluated (their Solidify and
    Subdivision), each moved by nail_shift[name] (F mm, the loaded toe's displacement): (V (n, 3) F mm,
    T (m, 3) outward-wound triangles in F)."""
    from lib import measure
    sk = ob.data.shape_keys
    kb = sk.key_blocks.get("Foot.Contact") if sk else None
    old = kb.value if kb else None
    mod = ob.modifiers.new("Foot.Sock.Subdivision", "SUBSURF")
    mod.levels = mod.render_levels = levels
    try:
        if kb is not None:
            kb.value = contact
        m = measure.evaluate(ob, ("tris",))
    finally:
        ob.modifiers.remove(mod)
        if kb is not None:
            kb.value = old
    Vs, Ts = [frame.to_f(m.co * 1000.0)], [m.tris]
    for nob in nails:
        mn = measure.evaluate(nob, ("tris",))
        q = frame.to_f(mn.co * 1000.0)
        if nail_shift and nob.name in nail_shift:
            q = q + np.asarray(nail_shift[nob.name], float)
        Vs.append(q)
        Ts.append(mn.tris)
    V, T, base = [], [], 0
    for q, t in zip(Vs, Ts):
        inside = (np.abs(q[:, 0]) < 95.0) & (q[:, 1] > -340.0) & (q[:, 1] < 80.0) & (q[:, 2] > -10.0) & (q[:, 2] < 345.0)
        keep = inside[t].all(axis=1)
        used = np.unique(t[keep])
        remap = np.full(len(q), -1, np.int64)
        remap[used] = np.arange(len(used)) + base
        V.append(q[used])
        T.append(remap[t[keep]])
        base += len(used)
    V, T = np.vstack(V), np.vstack(T)
    if frame.s < 0:          # frame F mirrors the right foot, and the winding with it
        T = T[:, [0, 2, 1]]
    return V, T


def bvh(V, T):
    from mathutils.bvhtree import BVHTree
    return BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)


# --------------------------------------------------------------------------- the planes

def fan_corner(V, z_c=FAN_Z, margin=FAN_MARGIN):
    """C = (y, z) in frame F: in front of the foremost point of the foot above z_c by `margin` (so the quadrant
    in front of and above C is empty, and no fan half-plane's other half meets the foot)."""
    up = V[V[:, 2] >= z_c]
    return float(up[:, 1].min() - margin), float(z_c)


def stations(V, top_z=TOP_Z, z_c=FAN_Z, leg_step=LEG_STEP, foot_step=FOOT_STEP, n_fan=N_FAN, front=None,
             fine_from=None, fine_step=1.5):
    """The rings' planes from the cuff's top to the toes' front: [(kind, origin (3,), d (3,))], d the in-plane
    direction of 'outward' (the seam's side: the back, then round the heel, then down), x across the foot the
    other in-plane axis. kind leg | fan | foot."""
    yc, zc = fan_corner(V, z_c)
    out = []
    nz = max(2, int(round((top_z - zc) / leg_step)))
    for z in np.linspace(top_z, zc, nz, endpoint=False):
        out.append(("leg", np.array([0.0, 0.0, z]), np.array([0.0, 1.0, 0.0])))
    for th in np.linspace(0.0, math.pi / 2.0, n_fan + 1)[:-1]:
        out.append(("fan", np.array([0.0, yc, zc]), np.array([0.0, math.cos(th), -math.sin(th)])))
    y_front = float(V[:, 1].min()) if front is None else front
    if fine_from is None or fine_from >= yc:
        ys = list(np.arange(yc, y_front + 8.0, -foot_step))
    else:                       # over the toes' tips the rings close up, so no tip falls between two of them
        ys = list(np.arange(yc, fine_from, -foot_step))
        ys += list(np.arange(ys[-1] - fine_step, y_front + 4.0, -fine_step))
    ys += [y_front + 3.0, y_front + 1.6]   # the toe closes 1.6 mm short of the tips (rings nearer cross under the membrane)
    keep = [ys[0]]
    for y in ys[1:]:            # two rings closer than 0.6 mm make sliver quads, whose normals the Solidify cannot hold
        if keep[-1] - y >= 0.6:
            keep.append(y)
    for y in keep:
        out.append(("foot", np.array([0.0, y, 0.0]), np.array([0.0, 0.0, -1.0])))
    return out, (yc, zc)


def plane_normal(d):
    """The normal of the plane spanned by x and d: x cross d."""
    return np.array([0.0, -d[2], d[1]])


def section_points(V, T, origin, d, edges=None, half=False):
    """The points where the triangles' edges cross the plane through `origin` spanned by x and d, as plane
    coordinates (a = x, b = along d from origin); with `half`, only the half-plane b > -1 (a fan's)."""
    n = plane_normal(d)
    s = (V - origin) @ n
    E = edges if edges is not None else np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    sa, sb = s[E[:, 0]], s[E[:, 1]]
    cut = (sa > 0.0) != (sb > 0.0)
    if not cut.any():
        return np.zeros((0, 2))
    a, b = E[cut, 0], E[cut, 1]
    t = (sa[cut] / (sa[cut] - sb[cut]))[:, None]
    P = V[a] + (V[b] - V[a]) * t
    rel = P - origin
    ab = np.stack([rel[:, 0], rel @ d], axis=1)
    return ab[ab[:, 1] > -1.0] if half else ab


def hull2d(P):
    """Convex hull of 2-D points, counter-clockwise (Andrew's monotone chain), as (k, 2)."""
    pts = np.unique(np.round(P, 6), axis=0)
    if len(pts) < 3:
        return pts

    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1])
                                   - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0.0:
                h.pop()
            h.append((p[0], p[1]))
        return h

    lst = pts.tolist()
    lower = half(lst)
    upper = half(lst[::-1])
    return np.array(lower[:-1] + upper[:-1])


def resample_ring(H, n=N_AROUND, snap_deg=25.0):
    """A closed 2-D polygon resampled at n points of equal arclength, starting where the ray from its centroid
    along +b leaves it (the seam), going toward +a first."""
    H = np.asarray(H, float)
    if len(H) < 3:
        c = H.mean(axis=0) if len(H) else np.zeros(2)
        return np.repeat(c[None], n, axis=0)
    x, y = H[:, 0], H[:, 1]
    x1, y1 = np.roll(x, -1), np.roll(y, -1)
    cr = x * y1 - x1 * y
    A = cr.sum() / 2.0
    if abs(A) < 1e-9:
        c = H.mean(axis=0)
    else:
        c = np.array([((x + x1) * cr).sum(), ((y + y1) * cr).sum()]) / (6.0 * A)
    if A > 0:                                   # counter-clockwise: reverse to clockwise (toward +a from the top)
        H = H[::-1]
    # the seam: the edge the vertical line a = c_a crosses above the centroid
    P0, P1 = H, np.roll(H, -1, axis=0)
    da0, da1 = P0[:, 0] - c[0], P1[:, 0] - c[0]
    hit = np.nonzero((da0 <= 0.0) & (da1 > 0.0) | (da0 >= 0.0) & (da1 < 0.0))[0]
    best, t_best, k_best = -np.inf, 0.0, 0
    for k in hit:
        t = da0[k] / (da0[k] - da1[k])
        b = P0[k, 1] + t * (P1[k, 1] - P0[k, 1])
        if b > best:
            best, t_best, k_best = b, t, k
    seam = P0[k_best] + t_best * (P1[k_best] - P0[k_best])
    poly = np.vstack([seam[None], H[k_best + 1:], H[:k_best + 1], seam[None]])
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    s = np.r_[0.0, np.cumsum(seg)]
    want = np.linspace(0.0, s[-1], n, endpoint=False)
    out = np.stack([np.interp(want, s, poly[:, 0]), np.interp(want, s, poly[:, 1])], axis=1)
    # a sharp corner of the hull (the end of a bridge, the last's feather) keeps a sample on it, so no chord cuts it
    v_in = poly[1:-1] - poly[:-2]
    v_out = poly[2:] - poly[1:-1]
    cosang = np.einsum("ij,ij->i", v_in, v_out) / np.maximum(np.linalg.norm(v_in, axis=1) * np.linalg.norm(v_out, axis=1), 1e-12)
    for k in np.nonzero(cosang < math.cos(math.radians(snap_deg)))[0]:
        j = int(np.argmin(np.abs(want - s[k + 1])))
        out[j] = poly[k + 1]
    return out


def shrunk(R, by):
    """A closed 2-D ring's points moved `by` mm inward along their normals (the ring's centroid side)."""
    t = np.roll(R, -1, axis=0) - np.roll(R, 1, axis=0)
    nrm = np.stack([t[:, 1], -t[:, 0]], axis=1)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    c = R.mean(axis=0)
    if np.sum(nrm * (R - c)) < 0.0:
        nrm = -nrm
    return R - by * nrm


def ring_points(V, T, st, n=N_AROUND, edges=None, bottom=None, follow=None, carry=None):
    """One ring (n, 3) in F: the convex hull of the plane's section, resampled. `bottom` (a z, foot rings only):
    the hull also takes each point's drop onto that plane, drawn in toward the ring's middle by a fifth of its
    height (the last's flat bottom and its feather, last.py)."""
    kind, o, d = st
    ab = section_points(V, T, o, d, edges, half=(kind == "fan"))
    if len(ab) < 3:
        return None
    if bottom is not None and (kind == "foot" or (kind == "fan" and d[2] < -0.94)):   # fans past 70 degrees: the floor
        # line lies under the arch (steeper ones meet the floor behind the heel)
        # the drop runs down the plane (along d), so a fan half-plane keeps its points; across the foot it is vertical
        z = o[2] + ab[:, 1] * d[2]
        low = z < bottom + 25.0
        mid = 0.5 * (ab[:, 0].min() + ab[:, 0].max())
        inset = 0.2 * np.clip(z[low] - bottom, 0.0, None)
        drop = np.stack([ab[low, 0] - np.sign(ab[low, 0] - mid) * np.minimum(inset, np.abs(ab[low, 0] - mid)),
                         np.full(low.sum(), (bottom - o[2]) / d[2])], axis=1)
        ab = np.vstack([ab, drop])
    if carry is not None:       # the ring behind, drawn in: a toe that ends tapers into the next rings, not a step
        ab = np.vstack([ab, carry])
    H = hull2d(ab)
    R = resample_ring(H, n) if follow is None else follow_ring(H, follow, n)
    return o[None, :] + R[:, :1] * np.array([1.0, 0.0, 0.0]) + R[:, 1:2] * d[None, :]


def follow_ring(H, prev, n=N_AROUND, uniform=0.15, smooth=3):
    """A ring's samples that keep the previous ring's columns (2-D, the same plane axes): each previous point's
    nearest point on this hull, by its arclength from this hull's seam, blended a little toward equal spacing and
    smoothed along the ring, in order. Where a toe ends between two sections, equal arclength would slide every
    column round by the lost lobe's share and fold the quads beside it; a nearest point on a convex curve moves
    only where the curve did."""
    U = resample_ring(H, 4 * n)                  # the hull, densely, from its seam: arclength by index
    seg = np.linalg.norm(np.diff(np.vstack([U, U[:1]]), axis=0), axis=1)
    s_all = np.r_[0.0, np.cumsum(seg)]
    total = s_all[-1]
    d2 = ((prev[:, None, :] - U[None, :, :]) ** 2).sum(axis=-1)
    k = np.argmin(d2, axis=1)
    s = s_all[k].copy()
    s = np.unwrap(s * 2.0 * np.pi / total) * total / (2.0 * np.pi)   # continuous round the ring
    s -= np.floor(s[0] / total) * total
    s = np.maximum.accumulate(s)                                    # in order
    want = s[0] + np.arange(n) * total / n
    s = (1.0 - uniform) * s + uniform * want
    for _ in range(smooth):
        s[1:-1] = 0.25 * s[:-2] + 0.5 * s[1:-1] + 0.25 * s[2:]
    s = np.mod(s, total)
    poly = np.vstack([U, U[:1]])
    return np.stack([np.interp(s, s_all, poly[:, 0]), np.interp(s, s_all, poly[:, 1])], axis=1)


TAPER = math.tan(math.radians(40.0))   # over the toes a ring holds the one behind it drawn in at this slope


def tube(V, T, sts, n=N_AROUND, bottom=None, taper_from=None):
    """The rings of every station that cuts the foot, (rings, n, 3) in F, and the stations kept. Across the foot each
    ring follows the one behind it (follow_ring); ahead of taper_from (y) each also holds the one behind it drawn in by
    TAPER x the step, so where a toe ends the knit runs on from its tip at 40 degrees instead of stepping in (a taut
    sock spans from one toe's tip to the next toe's side)."""
    edges = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    edges = np.unique(np.sort(edges, axis=1), axis=0)
    rings, kept = [], []
    prev, prev_y = None, None
    for st in sts:
        carry = None
        if taper_from is not None and prev is not None and st[0] == "foot" and st[1][1] < taper_from:
            carry = shrunk(prev, TAPER * (prev_y - st[1][1]))
        r = ring_points(V, T, st, n, edges, bottom, follow=prev, carry=carry)
        if r is not None:
            rings.append(r)
            kept.append(st)
            prev = np.stack([r[:, 0], -r[:, 2]], axis=1) if st[0] == "foot" else None
            prev_y = st[1][1]
    return np.array(rings), kept


# --------------------------------------------------------------------------- the envelope (a membrane over the foot)

def grid_normals(G):
    """Outward vertex normals of a ring grid (rings, n, 3): ring tangent x wale tangent, oriented away from each
    ring's centroid (on the whole, so a flat stretch keeps its sign)."""
    th = np.roll(G, -1, axis=1) - np.roll(G, 1, axis=1)
    tl = np.empty_like(G)
    tl[1:-1] = G[2:] - G[:-2]
    tl[0] = G[1] - G[0]
    tl[-1] = G[-1] - G[-2]
    N = np.cross(th, tl)
    N /= np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-12)
    c = G.mean(axis=1, keepdims=True)
    if np.sum(N * (G - c)) < 0.0:
        N = -N
    return N


def obstacle(tree, G, N, reach=40.0):
    """The height along each vertex's normal line of the outermost skin on it (mm; -inf where the line misses):
    a ray from reach mm outside, inward."""
    from mathutils import Vector
    h = np.full(G.shape[:2], -np.inf)
    O = G + reach * N
    for i in range(G.shape[0]):
        for j in range(G.shape[1]):
            loc, nrm, idx, dist = tree.ray_cast(Vector(O[i, j]), Vector(-N[i, j]), 2.0 * reach)
            if loc is not None:
                h[i, j] = reach - dist
    return h


def membrane(G, N, hmin, off, iters=None, lam=None, hoop=None, length=None, fixed=None):
    """Heights h along the normals: Jacobi steps of the grid's Laplacian (1/d^2 weights, ring and wale
    neighbours) projected on the normal, each step clamped to h >= hmin + off. Returns h (rings, n)."""
    P = MEMBRANE
    iters = P["iters"] if iters is None else iters
    lam = P["lam"] if lam is None else lam
    kh = P["hoop"] if hoop is None else hoop
    kl = P["length"] if length is None else length
    lo = np.maximum(hmin, 0.0) + off     # never inside the hull ring: the knit's hoop is taut (no sag into a cleft)
    h = np.maximum(np.zeros(G.shape[:2]), lo)
    dh = np.linalg.norm(np.roll(G, -1, axis=1) - G, axis=-1)
    wp = kh / np.maximum(dh, 0.3) ** 2                     # to j + 1
    wm = np.roll(wp, 1, axis=1)                            # to j - 1
    dl = np.linalg.norm(G[1:] - G[:-1], axis=-1)
    if np.ndim(kl) == 2:                                   # a weight per vertex: each wale edge takes the mean
        kl = 0.5 * (kl[1:] + kl[:-1])
    wl = kl / np.maximum(dl, 0.3) ** 2
    wu = np.zeros(G.shape[:2])
    wd = np.zeros(G.shape[:2])
    wu[1:] = wl                                            # to i - 1
    wd[:-1] = wl                                           # to i + 1
    W = wp + wm + wu + wd
    for _ in range(iters):
        X = G + h[..., None] * N
        L = wp[..., None] * (np.roll(X, -1, axis=1) - X) + wm[..., None] * (np.roll(X, 1, axis=1) - X)
        L[1:] += wu[1:, :, None] * (X[:-1] - X[1:])
        L[:-1] += wd[:-1, :, None] * (X[1:] - X[:-1])
        delta = np.sum(L * N, axis=-1) / W
        if fixed is not None:
            delta[fixed] = 0.0
        h = np.maximum(h + lam * delta, lo)
    return h


def envelope(V, T, sts, off=0.0, n=N_AROUND, tree=None, iters=None, length=None):
    """The membrane over the foot from the hull rings: (grid (rings, n, 3) F, normals, stations kept)."""
    G, kept = tube(V, T, sts, n)
    N = grid_normals(G)
    tree = tree or bvh(V, T)
    hmin = obstacle(tree, G, N)
    h = membrane(G, N, hmin, off, iters=iters, length=length)
    G = G + h[..., None] * N
    return G, grid_normals(G), kept


# --------------------------------------------------------------------------- the mesh

def faces(rings, n=N_AROUND):
    """Quads ring to ring (columns wrapping), then the toe's linking: the last ring's columns paired across its
    lateral-medial line, (n/4 + k) with (n/4 - k), a triangle at each end."""
    F = []
    for i in range(rings - 1):
        a, b = i * n, (i + 1) * n
        for j in range(n):
            j1 = (j + 1) % n
            F.append((a + j, a + j1, b + j1, b + j))
    base = (rings - 1) * n
    q = n // 4
    for k in range(n // 2):
        p0, p1 = (q + k) % n, (q + k + 1) % n
        m0, m1 = (q - k) % n, (q - k - 1) % n
        if p0 == m0:
            F.append((base + p0, base + p1, base + m1))
        elif p1 == m1:
            F.append((base + p0, base + p1, base + m0))
        else:
            F.append((base + p0, base + p1, base + m1, base + m0))
    return F


def uv_real(G, F, n=N_AROUND):
    """UV.Real per face corner, metres: u = (j / n) C_REF (the seam's corners of the wrap faces at C_REF), v the
    arclength down each wale from the top ring."""
    rings = G.shape[0]
    seg = np.linalg.norm(G[1:] - G[:-1], axis=-1)
    v = np.vstack([np.zeros((1, n)), np.cumsum(seg, axis=0)])
    U = []
    for f in F:
        js = [k % n for k in f]
        wrap = 0 in js and (n - 1) in js
        for vi in f:
            i, k = vi // n, vi % n
            uu = C_REF if (wrap and k == 0) else k / n * C_REF
            U.append((uu / 1000.0, v[i, k] / 1000.0))
    return np.array(U, np.float32)


def build_mesh(name, G, frame, n=N_AROUND, face_list=None, uv=True):
    """A bpy mesh from a ring grid in F (world metres), its faces wound outward, with UV.Real (`uv`)."""
    import bpy
    rings = G.shape[0]
    W = frame.to_w(G.reshape(-1, 3)) / 1000.0
    F = list(face_list) if face_list is not None else faces(rings, n)
    # outward winding: the first quad's normal against the grid's outward normal there
    Nn = grid_normals(G).reshape(-1, 3)
    f0 = F[0]
    p = G.reshape(-1, 3)
    nf = np.cross(p[f0[1]] - p[f0[0]], p[f0[3]] - p[f0[0]])
    flip = (nf @ Nn[f0[0]] < 0.0) != (frame.s < 0)
    if flip:
        F = [tuple(reversed(f)) for f in F]
    me = bpy.data.meshes.new(name)
    me.from_pydata(W.tolist(), [], F)
    if uv:
        layer = me.uv_layers.new(name="UV.Real")
        layer.data.foreach_set("uv", uv_real(G, F, n).ravel())
    for poly in me.polygons:
        poly.use_smooth = True
    me.update()
    return me


# --------------------------------------------------------------------------- regions (§3.6, §4.11 step 4)

def regions(G, N, L, toe, y_heel_back):
    """Region weights per grid vertex (rings, n) from frame-F positions and normals: cuff, leg, band (the arch
    band at 45-55 % L), heel (the turned heel's pocket behind its gore lines), toe (the cap from about the webs
    forward), sole (plantar), seam (the linked toe seam across the toes' tops), grime. `toe` holds the toe line:
    {"mtp1": (x, y), "mtp5": (x, y), "tip1": (x, y), "tip5": (x, y)} in F."""
    x, y, z = G[..., 0], G[..., 1], G[..., 2]
    nz = N[..., 2]
    sm = S.smoothstep
    out = {}
    out["cuff"] = sm(z, CUFF_Z - 2.0, CUFF_Z + 2.0)
    out["leg"] = sm(z, LEG_Z - 3.0, LEG_Z + 3.0) * (1.0 - out["cuff"])
    out["band"] = sm(-y, 0.45 * L - 1.5, 0.45 * L + 1.5) * (1.0 - sm(-y, 0.55 * L - 1.5, 0.55 * L + 1.5)) * (z < 90.0)
    # the heel pocket: below the line from 25 mm up the Achilles over the pternion to 45 mm under the heel (§3.6)
    z_top, y_low = 58.0, -45.0
    k = z_top / (y_heel_back - y_low)
    dist = (z_top + k * (y - y_heel_back) - z) / math.hypot(1.0, k)
    out["heel"] = sm(dist, -1.5, 1.5)
    # the toe cap: the courses ahead of the 4-5 web (10 mm ahead of the 5th MTP): a sock's reinforced toe is its
    # last courses, knitted in the other yarn, so its edge is a course straight across the foot (a ring here), not a
    # line slanted with the toes (whose faces stepped across the rings)
    y_cap = toe["mtp5"][1] - 10.0
    y_ring = np.broadcast_to(y.mean(axis=-1, keepdims=True), y.shape)   # the course's station, not each vertex's y
    out["toe"] = sm(-y_ring, -y_cap - 1.0, -y_cap + 1.0) * (1.0 - out["heel"])
    plantar = sm(-nz, 0.2, 0.6) * (1.0 - sm(z, 18.0, 28.0))
    out["sole"] = plantar
    # the toe seam: 1.5 mm wide across the toes' tops, from 24 mm behind the hallux's tip to 6 behind toe 5's
    (tx1, ty1), (tx5, ty5) = toe["tip1"], toe["tip5"]
    s1, s5 = np.array([tx1 - 15.0, ty1 + 24.0]), np.array([tx5 + 12.0, ty5 + 6.0])
    ts = s5 - s1
    ls = np.linalg.norm(ts)
    ts = ts / ls
    rel = np.stack([x, y], axis=-1) - s1
    along = rel @ ts
    across = np.abs(rel @ np.array([ts[1], -ts[0]]))
    top = sm(nz, 0.2, 0.45)
    out["seam"] = (1.0 - sm(across, 0.6, 1.4)) * sm(along, -2.0, 2.0) * (1.0 - sm(along, ls - 2.0, ls + 2.0)) * top
    out["grime"] = np.maximum(plantar, 0.6 * out["heel"] * (z < 35.0))
    return out


def smooth_grid(w, iters):
    """A (rings, n) field averaged with its ring and wale neighbours `iters` times (the ends held to one side)."""
    w = np.asarray(w, float).copy()
    for _ in range(iters):
        up = np.vstack([w[:1], w[:-1]])
        dn = np.vstack([w[1:], w[-1:]])
        w = 0.5 * w + 0.125 * (np.roll(w, 1, axis=1) + np.roll(w, -1, axis=1) + up + dn)
    return w


def thickness(reg, loaded=False, soften=12):
    """§3.6's thickness per vertex (mm): the leg's 1.6, the heel pocket and the toe cap 2.2, the sole 3.0 (1.8 under
    load, and the heel's and toe's bottoms with it), the welt 2.4 over everything above its fold. The terry and the
    plating change the thickness inside the knit, not at a seam, so the field is softened over a few rings (`soften`;
    a 0.6-1.4 mm step read as a ridge round the sole and the cap); the welt's fold keeps its edge."""
    t = np.full(reg["cuff"].shape, THICK["leg"])
    cap = np.maximum(reg["heel"], reg["toe"])
    t = t + (THICK["heel"] - t) * cap
    t = t + (THICK["sole"] - t) * reg["sole"] * (1.0 - cap)
    if loaded:
        t = t * (1.0 - (1.0 - LOADED_SOLE) * reg["sole"])
    if soften and t.ndim == 2:
        t = smooth_grid(t, soften)
    t = t + (THICK["cuff"] - t) * reg["cuff"]
    return t


def set_groups(ob, weights):
    """Vertex groups from (rings, n) weight grids, by name (replaced)."""
    for name, w in weights.items():
        g = ob.vertex_groups.get(name)
        if g is not None:
            ob.vertex_groups.remove(g)
        g = ob.vertex_groups.new(name=name)
        w = np.round(np.clip(np.asarray(w, float).ravel(), 0.0, 1.0), 4)
        for value in np.unique(w[w > 1e-4]):
            g.add(np.nonzero(w == value)[0].tolist(), float(value), "REPLACE")


# --------------------------------------------------------------------------- the knit's relief (Geometry Nodes)

def knit_group():
    """`Sock.GN.Knit`: the outer shell (Solidify's `sock_shell`) displaced along its normals by the cuff's 1x1 rib,
    the leg's 2x2 rib, the arch band's 1x1 rib and the toe seam (mm in the group's inputs). The rib's phase is
    the share of the way round from UV.Real's u, taken as cos and sin on the face corners and averaged to the
    points, so the seam's two u (0 and C_REF) agree; a whole number of ribs goes round every course."""
    import bpy
    ng = bpy.data.node_groups.get(GN_NAME)
    if ng is not None:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(GN_NAME, "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    for nm, val in (("Leg rib mm", RIB["leg"][1]), ("Cuff rib mm", RIB["cuff"][1]), ("Band rib mm", RIB["band"][1]),
                    ("Seam mm", SEAM_MM)):
        s = ng.interface.new_socket(name=nm, in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = val
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")

    def math_node(op, a, b=None, value=None):
        nd = N.new("ShaderNodeMath")
        nd.operation = op
        for k, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                nd.inputs[k].default_value = float(v)
            else:
                L.new(v, nd.inputs[k])
        if value is not None:
            nd.inputs[1].default_value = value
        return nd.outputs[0]

    def attr(name):
        nd = N.new("GeometryNodeInputNamedAttribute")
        nd.data_type = "FLOAT"
        nd.inputs["Name"].default_value = name
        return nd.outputs["Attribute"]

    uvn = N.new("GeometryNodeInputNamedAttribute")
    uvn.data_type = "FLOAT_VECTOR"
    uvn.inputs["Name"].default_value = "UV.Real"
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(uvn.outputs["Attribute"], sep.inputs[0])
    ang = math_node("MULTIPLY", sep.outputs[0], 2.0 * math.pi / (C_REF / 1000.0))
    cs = []
    for op in ("COSINE", "SINE"):
        v = math_node(op, ang)
        dom = N.new("GeometryNodeFieldOnDomain")
        dom.data_type, dom.domain = "FLOAT", "CORNER"
        L.new(v, dom.inputs[0])
        cs.append(dom.outputs[0])
    phi = math_node("ARCTAN2", cs[1], cs[0])

    def rib(n_ribs, share, amp_socket, weight):
        c = math_node("COSINE", math_node("MULTIPLY", phi, float(n_ribs)))
        c0 = math.cos(math.pi * share)
        mr = N.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        L.new(c, mr.inputs["Value"])
        mr.inputs["From Min"].default_value = c0 - 0.3
        mr.inputs["From Max"].default_value = c0 + 0.3
        mr.inputs["To Min"].default_value = -1.0
        mr.inputs["To Max"].default_value = 1.0
        return math_node("MULTIPLY", math_node("MULTIPLY", mr.outputs["Result"], gi.outputs[amp_socket]), attr(weight))

    d = math_node("ADD", rib(RIB["leg"][0], RIB["leg"][2], "Leg rib mm", "sock_leg"),
                  rib(RIB["cuff"][0], RIB["cuff"][2], "Cuff rib mm", "sock_cuff"))
    d = math_node("ADD", d, rib(RIB["band"][0], RIB["band"][2], "Band rib mm", "sock_band"))
    d = math_node("ADD", d, math_node("MULTIPLY", attr("sock_seam"), gi.outputs["Seam mm"]))
    d = math_node("MULTIPLY", math_node("MULTIPLY", d, attr("sock_shell")), 0.001)
    nrm = N.new("GeometryNodeInputNormal")
    sc = N.new("ShaderNodeVectorMath")
    sc.operation = "SCALE"
    L.new(nrm.outputs["Normal"], sc.inputs[0])
    L.new(d, sc.inputs["Scale"])
    sp = N.new("GeometryNodeSetPosition")
    L.new(gi.outputs["Geometry"], sp.inputs["Geometry"])
    L.new(sc.outputs["Vector"], sp.inputs["Offset"])
    L.new(sp.outputs["Geometry"], go.inputs["Geometry"])
    return ng


def add_modifiers(ob, group):
    """§4.11 step 5 without the Armature, Shrinkwrap and Corrective Smooth (they come with the weights, §7.4):
    Solidify (outward, the thickness by `sock_thickness`, the rim closed, the outer shell weighted to
    `sock_shell`), Subdivision (1 / render 2), the knit's relief (`group`, knit_group())."""
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness, sol.offset = T_MAX / 1000.0, 1.0
    # not even: the toe's linking is a knife edge, where an even offset (thickness over the cosine) runs to infinity
    sol.use_even_offset, sol.use_quality_normals, sol.use_rim = False, True, True
    sol.vertex_group, sol.thickness_vertex_group = "sock_thickness", 0.0
    sol.shell_vertex_group = "sock_shell"
    sol.material_offset = sol.material_offset_rim = 0
    sub = ob.modifiers.new("Subdivision", "SUBSURF")
    sub.levels, sub.render_levels, sub.quality = 1, 2, 3
    gn = ob.modifiers.new("Knit", "NODES")
    gn.node_group = group
    return sol, sub, gn


# --------------------------------------------------------------------------- one foot's sock

def toe_cap_length_weight(G, toe, boost=8.0):
    """The wales' stiffness per vertex: 1 up the leg and over the foot, `boost` ahead of the metatarsal heads,
    where the knit is stretched over the toes and spans the notches between their tips (a hoop alone leaves a
    crease at each tip)."""
    y1 = min(toe["mtp1"][1], toe["mtp5"][1])
    return 1.0 + (boost - 1.0) * S.smoothstep(-G[..., 1], -y1 - 10.0, -y1 + 15.0)


def make(V, T, toe, L, tree=None, n=N_AROUND):
    """The sock of one foot from its rendered surface (frame F): {"target": the envelope at 0 mm (the sock's
    target), "inner": the sock's inner surface (OFFSET_MM off), "normals", "regions", "thickness" (mm), "stations",
    "corner"}, grids (rings, n[, 3])."""
    tree = tree or bvh(V, T)
    sts, corner = stations(V, fine_from=toe["tip5"][1] + 10.0)
    G0, kept = tube(V, T, sts, n, taper_from=toe["tip5"][1] + 10.0)
    N0 = grid_normals(G0)
    hmin = obstacle(tree, G0, N0)
    kl = toe_cap_length_weight(G0, toe) * MEMBRANE["length"]
    out = {"stations": kept, "corner": corner, "hull": G0, "hull_normals": N0, "hmin": hmin, "kl": kl}
    out["target"] = G0 + membrane(G0, N0, hmin, 0.0, length=kl)[..., None] * N0
    out["inner"] = G0 + settle(G0, N0, hmin, OFFSET_MM, length=kl)[..., None] * N0
    repair(out, tree)
    out["normals"] = grid_normals(out["inner"])
    y_back = float(out["inner"][..., 1].max())
    out["regions"] = regions(out["inner"], out["normals"], L, toe, y_back)
    out["thickness"] = thickness(out["regions"])
    out["y_back"] = y_back
    return out


# --------------------------------------------------------------------------- measuring (spec 01 §8.2)

def ring_concavity(G, kept, y_lo, y_hi):
    """The deepest point of the foot rings between y_lo and y_hi inside its own ring's convex hull (mm): a sock that
    bridges the toes' clefts reads near 0."""
    worst = 0.0
    for i, (kind, o, d) in enumerate(kept):
        if kind != "foot" or not (y_lo <= o[1] <= y_hi):
            continue
        ab = np.stack([G[i, :, 0], G[i, :, 2]], axis=1)
        H = hull2d(ab)
        if len(H) < 3:
            continue
        P0, P1 = H, np.roll(H, -1, axis=0)
        e = P1 - P0
        ln = np.maximum(np.linalg.norm(e, axis=1), 1e-9)
        nrm = np.stack([e[:, 1], -e[:, 0]], axis=1) / ln[:, None]
        # distance of each ring point inside the hull: the least over the hull's edge lines (exact inside a
        # convex polygon)
        dist = np.min(np.abs(np.einsum("pkj,kj->pk", ab[:, None, :] - P0[None], nrm)), axis=1)
        worst = max(worst, float(dist.max()))
    return worst


def skin_cleft_depth(V, T, ys):
    """For comparison: how deep the skin's own sections across the toes go inside their hulls (mm)."""
    edges = np.unique(np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1), axis=0)
    worst = 0.0
    for y in ys:
        ab = section_points(V, T, np.array([0.0, y, 0.0]), np.array([0.0, 0.0, -1.0]), edges)
        if len(ab) < 3:
            continue
        H = hull2d(ab)
        P0, P1 = H, np.roll(H, -1, axis=0)
        e = P1 - P0
        ln = np.maximum(np.linalg.norm(e, axis=1), 1e-9)
        nrm = np.stack([e[:, 1], -e[:, 0]], axis=1) / ln[:, None]
        dist = np.min(np.abs(np.einsum("pkj,kj->pk", ab[:, None, :] - P0[None], nrm)), axis=1)
        worst = max(worst, float(dist.max()))
    return worst


def signed_gaps(tree, P):
    """Signed distances (mm) of points to the surface in `tree` (negative inside, by the nearest face's normal)."""
    from mathutils import Vector
    out = np.full(len(P), np.inf)
    for i, p in enumerate(P):
        loc, nrm, idx, dist = tree.find_nearest(Vector(p), 20.0)
        if loc is None:
            continue
        out[i] = dist if (Vector(p) - loc).dot(nrm) >= 0.0 else -dist
    return out


def limit_delta(G, N):
    """How far each vertex's Catmull-Clark limit point lies along its normal from it (mm; negative where the subdivided
    surface sinks inside the control mesh, on convex skin): the regular valence-4 stencil (16 v + 4 sum of edge
    neighbours + sum of the diagonals) / 36, the last ring linked to its partner across the toe's seam, the cuff's top
    ring by the boundary rule (v_-1 + 4 v + v_+1) / 6."""
    R, n = G.shape[:2]
    q = n // 4
    Lm = np.empty_like(G)
    jp, jm = np.roll(np.arange(n), -1), np.roll(np.arange(n), 1)
    # interior rings
    up, dn = G[:-2], G[2:]
    mid = G[1:-1]
    E = mid[:, jp] + mid[:, jm] + up + dn
    D = up[:, jp] + up[:, jm] + dn[:, jp] + dn[:, jm]
    Lm[1:-1] = (16.0 * mid + 4.0 * E + D) / 36.0
    Lm[0] = (G[0, jm] + 4.0 * G[0] + G[0, jp]) / 6.0
    last, prev = G[-1], G[-2]
    part = (2 * q - np.arange(n)) % n
    E = last[jp] + last[jm] + prev + last[part]
    D = prev[jp] + prev[jm] + last[(part + 1) % n] + last[(part - 1) % n]
    Lm[-1] = (16.0 * last + 4.0 * E + D) / 36.0
    Lm[-1, part == np.arange(n)] = last[part == np.arange(n)]
    return np.sum((Lm - G) * N, axis=-1)


def settle(G0, N0, hmin, off, length=None, rounds=3, iters=None):
    """The membrane with the subdivision's shrinkage made up: each round raises a vertex's floor by how far its limit
    point sank under it in the last, so the rendered (level-2) surface, not the cage, keeps `off` from the skin."""
    extra = np.zeros(G0.shape[:2])
    for _ in range(rounds):
        h = membrane(G0, N0, hmin, off + extra, length=length, iters=iters)
        G = G0 + h[..., None] * N0
        d = limit_delta(G, grid_normals(G))
        extra = np.maximum(extra, np.maximum(0.0, -d))
    return h


RAYS = ((0.0, 0.0, -1.0), (0.31, 0.12, -0.94), (-0.17, -0.29, -0.94))


def inside_parity(tree, P, dirs=RAYS, eps=1e-3):
    """True where a point is inside the surface in `tree` by ray parity (rays downward, so the leg's open cut above is
    never crossed; the nail plates are closed shells, so a point over one crosses it twice): odd crossings on at least
    two of the three rays. The nearest face's normal, which signed_gaps reads, is no guide in a cleft, where the
    nearest skin is a wall facing the neighbouring toe."""
    from mathutils import Vector
    out = np.zeros(len(P), bool)
    for i, p in enumerate(P):
        odd = 0
        for d in dirs:
            dv = Vector(d).normalized()
            o = Vector(p)
            hits = 0
            for _ in range(64):
                loc, nrm, idx, dist = tree.ray_cast(o, dv, 1000.0)
                if loc is None:
                    break
                hits += 1
                o = loc + dv * eps
            odd += hits % 2
        out[i] = odd >= 2
    return out


def subdivided_points(G, levels=2, face_list=None):
    """The points of a ring grid's Catmull-Clark subdivision at `levels` (F mm), through a temporary object (Blender's
    own subdivision, as the render makes it)."""
    import bpy
    n = G.shape[1]
    me = bpy.data.meshes.new("Sock.Tmp.Probe")
    me.from_pydata((G.reshape(-1, 3) / 1000.0).tolist(), [], list(face_list) if face_list is not None else faces(G.shape[0], n))
    ob = bpy.data.objects.new("Sock.Tmp.Probe", me)
    bpy.context.scene.collection.objects.link(ob)
    try:
        sub = ob.modifiers.new("Subdivision", "SUBSURF")
        sub.levels = sub.render_levels = levels
        sub.quality = 3
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        m = ev.to_mesh()
        co = np.empty(len(m.vertices) * 3)
        m.vertices.foreach_get("co", co)
        ev.to_mesh_clear()
        return co.reshape(-1, 3) * 1000.0
    finally:
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)


def inside_points(tree, P):
    """(points, depths mm) of P inside the surface in `tree` (the nearest face's side, confirmed by ray parity)."""
    g = signed_gaps(tree, P)
    cand = np.nonzero(g < 0.0)[0]
    if not len(cand):
        return P[:0], np.zeros(0)
    ok = cand[inside_parity(tree, P[cand])]
    return P[ok], -g[ok]


INSIDE_MM = 0.02   # a render-level point deeper than this under the skin counts as inside (shallower is float noise)


def repair(res, tree, off=OFFSET_MM, rounds=6, reach=4.0, margin=0.15):
    """Where the inner surface as it renders (level 2) still dips under the skin (between rings over a toe's tip), the
    floors of the base vertices within `reach` of each such point are raised by its depth and `margin` and the
    membrane settled again. Returns the rounds' [points inside] counts."""
    from mathutils import kdtree
    G0, N0, hmin, kl = res["hull"], res["hull_normals"], res["hmin"], res["kl"]
    extra = np.zeros(G0.shape[:2])
    flat = G0.reshape(-1, 3)
    counts = []
    for _ in range(rounds):
        P, depth = inside_points(tree, subdivided_points(res["inner"]))
        P, depth = P[depth > INSIDE_MM], depth[depth > INSIDE_MM]
        counts.append(int(len(P)))
        if not len(P):
            break
        cur = res["inner"].reshape(-1, 3)
        kd = kdtree.KDTree(len(cur))
        for i, p in enumerate(cur):
            kd.insert(p, i)
        kd.balance()
        e = extra.reshape(-1)
        for p, d in zip(P, depth):
            for _co, i, dist in kd.find_range(p, reach):
                e[i] = max(e[i], d + margin)
        h = settle(G0, N0, hmin, off + extra, length=kl)
        res["inner"] = G0 + h[..., None] * N0
    res["repair"] = counts
    return counts
