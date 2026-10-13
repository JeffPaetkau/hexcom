"""Method (a)'s large forms as explicit fields on the dense skin (frame F, mm): what part 01 does on the
5 mm cage, done again where a field can be as small as the form it makes.

Each field is a displacement of the skin's vertices: an inflation along the normals inside a compact
ellipsoid window (the pulps, the first MTP prominence, the metatarsal head, the tendons), a groove along a
curve (detail.crease) or a fairing pass (the web). The windows are compact ((1 - r^2)^3), so a pulp moves
its pulp and nothing else.
"""
import numpy as np

import detail as D
import toes as T


def window(q, seg, centre_tuh, radii_tuh):
    """(1 - r^2)^3 inside an ellipsoid given in a segment's frame (centre and radii as (t, u, h))."""
    t, u, h = seg.local(q)
    r2 = ((t - centre_tuh[0]) / radii_tuh[0]) ** 2 + ((u - centre_tuh[1]) / radii_tuh[1]) ** 2 \
        + ((h - centre_tuh[2]) / radii_tuh[2]) ** 2
    return np.clip(1.0 - r2, 0.0, 1.0) ** 3


def sphere(q, c, r):
    r2 = np.sum((q - np.asarray(c)) ** 2, axis=1) / (r * r)
    return np.clip(1.0 - r2, 0.0, 1.0) ** 3


def along_line(q, pts, r):
    """(1 - (d/r)^2)^3 of the distance to a polyline, tapered to nothing over the first and last fifth."""
    pts = np.asarray(pts, float)
    best = np.full(len(q), np.inf)
    s_best = np.zeros(len(q))
    total = sum(np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1))
    run = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        ln = np.linalg.norm(ab)
        t = np.clip(((q - a) @ ab) / (ln * ln), 0.0, 1.0)
        d = np.linalg.norm(q - (a + np.outer(t, ab)), axis=1)
        better = d < best
        best[better] = d[better]
        s_best[better] = (run + t[better] * ln) / total
        run += ln
    w = np.clip(1.0 - (best / r) ** 2, 0.0, 1.0) ** 3
    return w * T.window(s_best, 0.0, 0.2, 0.8, 1.0)


def skin_top(q, x, y, window_mm=3.0):
    """The highest skin point over a plan point (F)."""
    sel = (np.abs(q[:, 0] - x) < window_mm) & (np.abs(q[:, 1] - y) < window_mm)
    c = q[sel]
    return c[np.argmax(c[:, 2])]


def medial_point(q, y, z, window_mm=4.0):
    """The most medial skin point (least x) at a plan height and station."""
    sel = (np.abs(q[:, 1] - y) < window_mm) & (np.abs(q[:, 2] - z) < window_mm)
    c = q[sel]
    return c[np.argmin(c[:, 0])]


def vertex_normals_like(q, nrm):
    """The normals the fields were given (the fairing only needs which way the skin faces)."""
    return nrm


def adjacency(edges, n):
    """CSR neighbours from an edge list."""
    e = np.concatenate([edges, edges[:, ::-1]])
    order = np.argsort(e[:, 0], kind="stable")
    e = e[order]
    ptr = np.zeros(n + 1, np.int64)
    np.add.at(ptr, e[:, 0] + 1, 1)
    return np.cumsum(ptr), e[:, 1]


def relax_tangent(q, adj, nrm, weight, iterations=10, lam=0.5):
    """Laplacian relaxation within the surface: each step toward the neighbours' mean with its component
    along the vertex normal (nrm, held for the call) taken out, so vertices crowded onto a new surface spread
    over it instead of shrinking it. Runs on the weighted vertices' subgraph, as taubin."""
    ptr, nb = adj
    active = np.nonzero(weight > 1e-4)[0]
    if not len(active):
        return q
    deg = np.diff(ptr)
    counts = deg[active]
    offs = np.repeat(ptr[active] - np.concatenate([[0], np.cumsum(counts)[:-1]]), counts) + np.arange(counts.sum())
    nbr = nb[offs]
    row = np.repeat(np.arange(len(active)), counts)
    sub = np.unique(np.concatenate([active, nbr]))
    loc = np.searchsorted(sub, nbr)
    act = np.searchsorted(sub, active)
    Q = q[sub].copy()
    w = weight[active][:, None]
    na = nrm[active]
    inv = 1.0 / np.maximum(counts, 1)[:, None]
    for _ in range(iterations):
        Qn = Q[loc]
        mean = np.stack([np.bincount(row, Qn[:, k], minlength=len(active)) for k in range(3)], 1) * inv
        d = mean - Q[act]
        d -= np.einsum("ij,ij->i", d, na)[:, None] * na
        Q[act] += lam * w * d
    q = q.copy()
    q[sub] = Q
    return q


def taubin(q, adj, weight, iterations=60, lam=0.5, mu=-0.53):
    """Taubin's lambda|mu fairing where weight > 0 (the weight scales each step): a narrow concavity (a slot
    between two toes) rounds out and fills without the rest shrinking. Runs on the weighted vertices'
    subgraph only (their neighbours held), so a pass costs what the region costs, not the foot."""
    ptr, nb = adj
    active = np.nonzero(weight > 1e-4)[0]
    if not len(active):
        return q
    deg = np.diff(ptr)
    counts = deg[active]
    offs = np.repeat(ptr[active] - np.concatenate([[0], np.cumsum(counts)[:-1]]), counts) + np.arange(counts.sum())
    nbr = nb[offs]
    row = np.repeat(np.arange(len(active)), counts)
    sub = np.unique(np.concatenate([active, nbr]))
    loc = np.searchsorted(sub, nbr)
    act = np.searchsorted(sub, active)
    Q = q[sub].copy()
    w = weight[active][:, None]
    inv = 1.0 / np.maximum(counts, 1)[:, None]
    for _ in range(iterations):
        for f in ((lam, mu) if mu else (lam,)):
            Qn = Q[loc]
            mean = np.stack([np.bincount(row, Qn[:, k], minlength=len(active)) for k in range(3)], 1) * inv
            Q[act] += f * w * (mean - Q[act])
    q = q.copy()
    q[sub] = Q
    return q


class Plan:
    """A toe's plan frame (round 4): stations along the toe's direction in the ground plane from a joint, so
    a station is a vertical plane; u across (lateral +), h up; and the toe's section at each station from its
    own skin (midline u, half-width, lowest and highest h), smoothed over a few stations.

    Why not the segment frames: their stations are planes square to the bones, and the curled toes' bones dip
    21 to 36 degrees, so on the plantar skin, 8 to 13 mm below the joint centres, a segment's station lands 3
    to 8 mm proximal of where it lands on the dorsum. Round 3's waist (t 8 on toe 2's middle phalanx) fell on
    the plantar flexion fold under the PIP, and, pulled in along normals that turn sharply in that fold, it
    folded the skin over itself (35 inverted faces: the critics' 'sleeve cuff' with flaps past the outline);
    the plantar creases sat under the phalanges rather than the joints (the hallux's 6 mm proximal of its IP,
    on top of the neck: the V-notch in profile)."""

    def __init__(self, q, mine, origin, toward, step=1.0):
        a = np.asarray(toward, float) - np.asarray(origin, float)
        a[2] = 0.0
        self.a = a / np.linalg.norm(a)
        self.n = np.array([0.0, 0.0, 1.0])
        self.b = np.cross(self.n, self.a)
        if self.b[0] < 0.0:
            raise ValueError("plan frame: b is not lateral (+x); the frame assumes the left foot")
        self.o = np.asarray(origin, float)
        s, u, h = self.local(q[mine])
        st = np.arange(np.floor(s.min()), np.ceil(s.max()) + step, step)
        rows = []
        for s0 in st:
            m = np.abs(s - s0) < 0.75 * step
            if m.sum() < 8:
                rows.append([np.nan] * 4)
                continue
            rows.append([0.5 * (u[m].min() + u[m].max()), 0.5 * (u[m].max() - u[m].min()), h[m].min(), h[m].max()])
        R = np.asarray(rows, float)
        for k in range(4):
            ok = np.isfinite(R[:, k])
            col = np.interp(st, st[ok], R[ok, k])
            R[:, k] = np.convolve(np.pad(col, 2, mode="edge"), np.ones(5) / 5.0, mode="valid")
        self.st, self.R = st, R
        self.s_max = float(s.max())

    def local(self, q):
        d = np.asarray(q, float) - self.o
        return d @ self.a, d @ self.b, d @ self.n

    def section(self, s):
        """(midline u, half-width, lowest h, highest h) at stations s."""
        return tuple(np.interp(s, self.st, self.R[:, k]) for k in range(4))

    def station(self, p):
        return float(self.local(np.asarray(p, float)[None, :])[0][0])


def sections(seg, qm, step=1.0):
    """A distal segment's section extents along it, from its own vertices qm (F): functions of t giving the
    section's lowest and highest h and its midline u (each smoothed over a few stations)."""
    t, u, h = seg.local(qm)
    st = np.arange(np.floor(t.min()), np.ceil(t.max()) + step, step)
    lo, hi, mid = [], [], []
    for s in st:
        m = np.abs(t - s) < 0.75 * step
        if m.sum() < 8:
            lo.append(np.nan), hi.append(np.nan), mid.append(np.nan)
            continue
        lo.append(h[m].min()), hi.append(h[m].max()), mid.append(0.5 * (u[m].min() + u[m].max()))
    arrs = []
    for a in (lo, hi, mid):
        a = np.asarray(a, float)
        ok = np.isfinite(a)
        a = np.interp(st, st[ok], a[ok])
        a = np.convolve(np.pad(a, 2, mode="edge"), np.ones(5) / 5.0, mode="valid")
        arrs.append(a)
    return (lambda x: np.interp(x, st, arrs[0])), (lambda x: np.interp(x, st, arrs[1])), \
        (lambda x: np.interp(x, st, arrs[2])), float(t.max())


def smin(a, b, k):
    """Polynomial smooth minimum (union) with fillet radius k."""
    hh = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * hh - k * hh * (1.0 - hh)


def ellipsoid_sdf(Pts, centre, axes, radii):
    """Quilez's bound of the distance to an ellipsoid (negative inside): centre (F), axes as rows."""
    d = (np.asarray(Pts, float) - centre) @ np.asarray(axes).T
    r = np.asarray(radii, float)
    k0 = np.linalg.norm(d / r, axis=-1)
    k1 = np.linalg.norm(d / (r * r), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def grow(q, nrm, prim, k, weight, dmax=8.0, iterations=24):
    """How far each vertex moves along its normal to lie on the smooth union of the skin and a primitive
    (prim: signed distance, negative inside; k: the fillet). Bisection on the ray p + d n for the least d >= 0
    with smin(d, prim(p + d n), k) >= 0: the toe grows into the primitive and blends out over k, and only ever
    grows, so a pulp adds flesh where the toe is short of it and leaves the rest alone."""
    out = np.zeros(len(q))
    sel = np.nonzero(weight > 1e-4)[0]
    if not len(sel):
        return out
    need = smin(0.0, prim(q[sel]), k) < -1e-4
    idx = sel[need]
    p, n = q[idx], nrm[idx]
    lo, hi = np.zeros(len(idx)), np.full(len(idx), dmax)
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        neg = smin(mid, prim(p + mid[:, None] * n), k) < 0.0
        lo, hi = np.where(neg, mid, lo), np.where(neg, hi, mid)
    out[idx] = hi * weight[idx]
    return out


def pulps(q, nrm, segs, groups, P, report):
    """The pulps as smooth unions with ellipsoids, after the other fields (spec 01 §3.3: 5-8 mm of pulp past
    the bone). Each pad is an oval in plan, widest mid-pad, its front rounding into the tip; the hallux's rests
    on the floor (its frame level with the floor), toe 2's follows its curled distal phalanx and sinks
    `sink` mm below its present underside. Returns the new positions."""
    floor = float(q[:, 2].min())
    out = q.copy()
    rep = {}
    for key, segname, g in (("pulp1_e", "h2", "toe1-2.L"), ("pulp2_e", "t2d", "toe2-3.L")):
        E = P.get(key)
        if not E:
            continue
        seg = segs[segname]
        mine = groups[g] > 0.5
        hbot, htop, umid, t_tip = sections(seg, q[mine])
        tc = t_tip - E["back"]
        if E.get("frame") == "floor":
            a = seg.a.copy()
            a[2] = 0.0
            a /= np.linalg.norm(a)
            z = np.array([0.0, 0.0, 1.0])
            b = np.cross(z, a)
            axes = np.stack([a, b, z])
            c = seg.point(tc, float(umid(tc)), 0.0)
            c[2] = floor + E.get("lift", 0.15) + E["radii"][2]
        else:
            axes = np.stack([seg.a, seg.b, seg.n])
            c = seg.point(tc, float(umid(tc)), float(hbot(tc)) + E["radii"][2] - E.get("sink", 0.0))
        c = c + axes[1] * E.get("u_shift", 0.0)
        w = np.clip(groups[g], 0.0, 1.0)
        d = grow(q, nrm, lambda Pts: ellipsoid_sdf(Pts, c, axes, E["radii"]), E["k"], w)
        out += d[:, None] * nrm
        rep[key] = {"centre_F": np.round(c, 2).tolist(), "front_F": np.round(c + axes[0] * E["radii"][0], 2).tolist(),
                    "max_mm": round(float(d.max()), 2)}
    report["pulps"] = rep
    return out


def deepen(q, segs, groups, P, report=None):
    """Round 5 (critic round 4 m5: the hallux about 29-31 mm wide but only 21-22 deep at the IP and 18.5 at the
    nail root, a broad flat paddle; Jeff's direction pairs the 30 mm width with about 25 mm of depth at the IP,
    and his photographs show a round, full big toe): the hallux made deeper in its own plan frame (Plan, so a
    station is a vertical plane). The upper part of each section (by its height in the section) rises by
    `deepen1_up` from 6 mm past the MTP to the IP, fully over the distal phalanx, easing to `deepen1_tip` of
    itself at the tip; the lower part under the IP and the proximal pad sinks by `deepen1_down`, never nearer
    the floor than `deepen1_floor`. Moves are vertical and change slower than 1:1 with height, so nothing
    folds; the web's closing (after) blends the toe's lateral side into the web again. Returns positions."""
    up, down = P.get("deepen1_up", 0.0), P.get("deepen1_down", 0.0)
    if not (up or down):
        return q
    h1, h2 = segs["h1"], segs["h2"]
    w1 = np.clip(groups["toe1-1.L"] + groups["toe1-2.L"], 0.0, 1.0)
    pl = Plan(q, w1 > 0.5, h1.o, h2.point(h2.length, 0.0, 0.0))
    s, u, h = pl.local(q)
    umid, half, hlo, hhi = pl.section(s)
    rel = (h - hlo) / np.maximum(hhi - hlo, 1.0)
    s_ip = pl.station(h2.o) + P.get("ip_shift", 0.0)
    s_tip = pl.s_max
    tip = P.get("deepen1_tip", 0.45)
    prof_up = T.smoothstep(s, 6.0, s_ip - 2.0) * (1.0 - (1.0 - tip) * T.smoothstep(s, s_tip - 9.0, s_tip))
    dz = up * prof_up * T.smoothstep(rel, 0.3, 0.85)
    prof_dn = T.window(s, 8.0, s_ip - 8.0, s_ip + 3.0, s_ip + 9.0)
    floor = float(q[:, 2].min())
    want = down * prof_dn * (1.0 - T.smoothstep(rel, 0.1, 0.45))
    room = np.maximum(q[:, 2] - (floor + P.get("deepen1_floor", 0.6)), 0.0)
    k = 0.15
    dn = -np.clip(-k * np.logaddexp(-want / k, -room / k), 0.0, None)     # down by softmin(want, room)
    fade = T.smoothstep(w1, 0.25, 0.85)
    out = q.copy()
    out[:, 2] += (dz + dn) * fade
    if report is not None:
        report["deepen"] = {"up_max": round(float((dz * fade).max()), 2), "down_max": round(float((-dn * fade).max()), 2),
                            "s_ip": round(float(s_ip), 2), "s_tip": round(float(s_tip), 2)}
    return out


def apply(q, nrm, segs, groups, adj, P, report):
    """The large forms of the region (method a). groups: {name: weights} of the dense skin; returns the
    new positions and the crease weight."""
    h2, t2d, t2m, h1 = segs["h2"], segs["t2d"], segs["t2m"], segs["h1"]
    plantar = lambda seg: T.smoothstep(-(nrm @ seg.n), -0.35, 0.35)   # noqa: E731
    w_h = np.clip(groups["toe1-1.L"] + groups["toe1-2.L"], 0.0, 1.0)
    w_2 = np.clip(groups["toe2-1.L"] + groups["toe2-2.L"] + groups["toe2-3.L"], 0.0, 1.0)
    dq = np.zeros_like(q)
    # the pulps: a fleshy pad under and around each tip (spec 01 §3.3: 5-8 mm of pulp past the bone); round 2
    # grows them as ellipsoid unions instead (pulps()), so these default to nothing
    L = h2.length
    if P["pulp1"]:
        dq += (P["pulp1"] * window(q, h2, (0.60 * L, 0.0, -7.0), (12.0, 15.0, 9.0)) * plantar(h2) * w_h)[:, None] * nrm
    L2 = t2d.length
    if P["pulp2"]:
        dq += (P["pulp2"] * window(q, t2d, (0.55 * L2, 0.0, -3.5), (7.5, 8.0, 5.5)) * plantar(t2d) * w_2)[:, None] * nrm
    # the tips: the pulp's nose carried forward below the nail (from above a rim of it shows beyond the free
    # edge), so the end of a toe is a pad, not a sawn-off cylinder
    for seg, g, amt, (dt, dh), radii in ((h2, "toe1-2.L", P["tip1"], (3.0, -4.5), (7.0, 14.0, 6.0)),
                                          (t2d, "toe2-3.L", P["tip2"], (2.0, -2.5), (4.5, 8.0, 4.0))):
        if not amt:
            continue
        mine = groups[g] > 0.5
        t_tip = float(seg.local(q[mine])[0].max())
        wt = window(q, seg, (t_tip - dt, 0.0, dh), radii) * np.clip(groups[g], 0.0, 1.0)
        dq += (amt * wt)[:, None] * (seg.a - 0.25 * seg.n)[None, :]
    # the distal dorsum raised toward the tip: MakeHuman's hallux falls 19 degrees from the IP to the tip (its
    # joint cubes sit under the dorsum, so the segment's axis is the dorsal line), where a real one keeps ~19 mm
    # of depth at the nail root and runs nearly level to the free edge. The upper part of each section moves
    # up, the pad stays, so the toe thickens rather than tilts
    for seg, g, amt in ((h2, "toe1-2.L", P.get("lift1", 0.0)), (t2d, "toe2-3.L", P.get("lift2", 0.0))):
        if not amt:
            continue
        mine = groups[g] > 0.5
        hbot, htop, umid, t_tip = sections(seg, q[mine])
        t, u, hh = seg.local(q)
        rel = (hh - hbot(t)) / np.maximum(htop(t) - hbot(t), 1.0)
        ramp = T.smoothstep(t, P.get("lift_from", 3.0), t_tip - 4.0)
        dq += (amt * ramp * T.smoothstep(rel, 0.3, 0.75) * np.clip(groups[g], 0.0, 1.0))[:, None] * np.array([0.0, 0.0, 1.0])
    # the crown: the dorsum over the nail raised along its midline, so the section is domed under a domed plate
    # (the plate's transverse radius is 11 mm on the hallux, 6 on toe 2; a flat dorsum buries its edges)
    for seg, g, amt, nl, ru in ((h2, "toe1-2.L", P.get("crown1", 0.0), P["nail1"]["length"], 14.0),
                                (t2d, "toe2-3.L", P.get("crown2", 0.0), P["nail2"]["length"], 8.0)):
        if not amt:
            continue
        mine = groups[g] > 0.5
        hbot, htop, umid, t_tip = sections(seg, q[mine])
        t, u, hh = seg.local(q)
        tc = t_tip - 3.0 - 0.5 * nl
        r2 = ((t - tc) / (0.5 * nl + 5.0)) ** 2 + ((u - umid(t)) / ru) ** 2
        wc = np.clip(1.0 - r2, 0.0, 1.0) ** 2 * T.smoothstep(hh - htop(t), -0.45 * (htop(t) - hbot(t)), -0.1 * (htop(t) - hbot(t)))
        dq += (amt * wc * T.smoothstep(nrm @ seg.n, 0.2, 0.6) * np.clip(groups[g], 0.0, 1.0))[:, None] * nrm
    # the neck: the pad's sides pinched in a little at the flexion crease (the IP on the hallux, the DIP on
    # toe 2). Round 4: in the toe's plan frame (a vertical plane at the crease, Plan) and sideways on the lower
    # sides only; round 3 pulled along the normals on the plantar face too, in the segment's tilted plane, so
    # it raised the hallux's plantar outline 0.7 mm 6 mm behind its IP, and with the crease on it read as a
    # V-notch in profile
    for seg, g, g_prox, amt, s_c in ((h2, "toe1-2.L", "toe1-1.L", P.get("neck1", 0.0), P.get("crease1_s", 1.0)),
                                     (t2d, "toe2-3.L", "toe2-2.L", P.get("neck2", 0.0), P.get("crease2d_s", 0.6))):
        if not amt:
            continue
        g_all = np.clip(groups[g] + groups[g_prox], 0.0, 1.0)
        pl = Plan(q, g_all > 0.5, seg.o, seg.point(seg.length, 0.0, 0.0))
        s, u, hh = pl.local(q)
        umid, half, hlo, hhi = pl.section(s)
        du = u - umid
        win = np.clip(1.0 - ((s - s_c) / 3.5) ** 2, 0.0, 1.0) ** 2
        side = T.smoothstep(np.abs(du) / np.maximum(half, 1.0), 0.45, 0.95)
        low = 1.0 - T.smoothstep((hh - hlo) / np.maximum(hhi - hlo, 1.0), 0.3, 0.65)
        dq += (-amt * win * side * low * g_all * np.sign(du))[:, None] * pl.b[None, :]
    dq += toe2_outline(q, nrm, segs, groups, P, report)
    # the first MTP prominence on the inner border, and the metatarsal head's dorsal knuckle
    mtp = segs["h1"].o
    c = medial_point(q, mtp[1] + 3.0, mtp[2] - 8.0)
    dq += (P["mtp_prom"] * sphere(q, c, 15.0))[:, None] * nrm
    top = skin_top(q, mtp[0], mtp[1] + 4.0)
    dq += (P["mt_head"] * sphere(q, top, 11.0))[:, None] * nrm
    # the long extensors: the hallux's (EHL) and toe 2's (EDL) cords onto their toes' bases
    ehl = [skin_top(q, x, y) - np.array([0.0, 0.0, 1.0]) for x, y in ((-23.0, -168.0), (-26.0, -195.0),
                                                                        (mtp[0] + 2.0, mtp[1] - 8.0))]
    dq += (P["ehl"] * along_line(q, ehl, 4.0))[:, None] * nrm
    j2 = segs["t2p"].o
    edl = [skin_top(q, x, y) - np.array([0.0, 0.0, 1.0]) for x, y in ((-7.0, -170.0), (-5.5, -195.0),
                                                                        (j2[0] + 0.5, j2[1] - 6.0))]
    dq += (P["edl"] * along_line(q, edl, 3.0))[:, None] * nrm
    # the distal segments' sections squared a little (flat-topped, broad-bottomed, rounded at the corners,
    # not round: "fingers, not toes") and the hallux's end widened into a spade rather than a dome
    # a negative amount rounds the upper corners in instead (the shoulders beside a domed nail), the pad left
    # to the pulp's union; it works per station (the section's own centre), the old way on the segment's box
    for seg, g, amt, t_from in ((h2, "toe1-2.L", P["square1"], 4.0), (t2d, "toe2-3.L", P["square2"], 1.0)):
        if not amt:
            continue
        mine = groups[g] > 0.5
        t, u, hh = seg.local(q)
        if amt > 0:
            tm, um, hm = seg.local(q[mine])
            uc, hc = 0.5 * (um.min() + um.max()), 0.5 * (hm.min() + hm.max())
            upper = None
        else:
            hbot, htop, umid, _ = sections(seg, q[mine])
            uc, hc = umid(t), 0.5 * (hbot(t) + htop(t))
        du, dh = u - uc, hh - hc
        r = np.hypot(du, dh)
        th = np.arctan2(dh, du)
        if amt > 0:
            upper = 0.25 + 0.75 * T.smoothstep(dh, -2.0, 2.0)      # the pad's underside stays round
        else:
            upper = T.smoothstep(dh, -1.0, 3.0)
        push = amt * upper * np.sin(2.0 * th) ** 2 * r * T.smoothstep(t, t_from, t_from + 4.0) * np.clip(groups[g], 0.0, 1.0)
        dq += (push / np.maximum(r, 1e-6))[:, None] * (np.outer(du, seg.b) + np.outer(dh, seg.n))
    t, u, hh = h2.local(q)
    mine = groups["toe1-2.L"] > 0.5
    tm, um = t[mine], u[mine]
    uc, t_tip = 0.5 * (um.min() + um.max()), float(tm.max())
    spread = P["spade1"] * (u - uc) * T.smoothstep(t, t_tip - 16.0, t_tip - 5.0) * np.clip(groups["toe1-2.L"], 0.0, 1.0)
    dq += spread[:, None] * h2.b[None, :]
    # the droop: each tip's last stretch of dorsum turned down toward its nose, so the nail's free edge
    # rides a descending dorsum and the pulp leads it (MakeHuman's toes end as flat-topped cylinders); round 2
    # keeps it to the stretch ahead of the free edge (`droop_reach`), so the nail itself is not tipped down
    for seg, g, amt, reach in ((h2, "toe1-2.L", P["droop1"], P.get("droop_reach1", 9.0)),
                               (t2d, "toe2-3.L", P["droop2"], P.get("droop_reach2", 5.5))):
        mine = groups[g] > 0.5
        t, u, hh = seg.local(q)
        t_tip, crest = float(t[mine].max()), float(hh[mine].max())
        ramp = T.smoothstep(t, t_tip - reach, t_tip + 1.0) ** 1.5
        if P.get("droop_sections", True):
            # over the whole front face (each station's own depth), so the top-front corner rounds over; round
            # 1's 3 mm band folded the face, a crease 1-2 mm under the free edge
            hbot, htop, _, _ = sections(seg, q[mine])
            upper = T.smoothstep((hh - hbot(t)) / np.maximum(htop(t) - hbot(t), 1.0), 0.15, 0.95)
        else:
            upper = T.smoothstep(hh, -3.0, crest)
        dq += (-amt * ramp * upper * np.clip(groups[g], 0.0, 1.0))[:, None] * seg.n[None, :]
    q = q + dq
    report["anchors"] = {"mtp_prominence": c.round(2).tolist(), "mt_head": top.round(2).tolist()}
    # the distal segments' dorsum faired (MakeHuman's nail patch and part 01's knuckle dip leave ripples
    # that the nail's fit would otherwise copy)
    if P.get("fair_dorsum", 0):
        nq = vertex_normals_like(q, nrm)
        dorsal = np.zeros(len(q))
        for seg, g in ((h2, "toe1-2.L"), (t2d, "toe2-3.L")):
            dorsal = np.maximum(dorsal, np.clip(groups[g], 0.0, 1.0) * T.smoothstep(nq @ seg.n, 0.2, 0.6))
        q = taubin(q, adj, 0.8 * dorsal, iterations=int(P["fair_dorsum"]))
    # the 1-2 web: the slot's floor faired (a slot is concave across, so fairing fills it from its floor)
    if P.get("web_fair", 0):
        cleft = web_zone(q, segs, P)
        q = taubin(q, adj, cleft, iterations=int(P["web_fair"]))
    return q


def _blur_rows(H, sigma_cells):
    """A Gaussian blur of a map along its first axis only, normalised by the coverage (NaN holes)."""
    r = max(1, int(3.0 * sigma_cells))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_cells) ** 2)
    k /= k.sum()
    ok = np.isfinite(H)
    A = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, np.where(ok, H, 0.0))
    M = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, ok.astype(float))
    return np.where(ok & (M > 0.3), A / np.maximum(M, 1e-9), np.nan)


def _resample(M, f):
    """A smooth map at f times its resolution (separable linear interpolation), its interpolation creases
    blurred away over about two coarse cells' tenth: bilinear samples of the coarse map itself faceted the
    surface they shaped (a 0.5 mm grid of facets in clay)."""
    n0, n1 = M.shape
    x0, x1 = np.arange(n0), np.arange(n1)
    g0, g1 = np.linspace(0.0, n0 - 1.0, (n0 - 1) * f + 1), np.linspace(0.0, n1 - 1.0, (n1 - 1) * f + 1)
    A = np.stack([np.interp(g0, x0, M[:, j]) for j in range(n1)], axis=1)
    A = np.stack([np.interp(g1, x1, A[i, :]) for i in range(len(g0))], axis=0)
    return D._blur2d(A, 0.5 * f)


def close_folds(q, segs, groups, P, adj=None, report=None):
    """Round 4 (critic round 3, m1): toe 2's plantar flexion fold under the curled PIP rounded into a soft
    infold. Part 01's curl (PIP 25 degrees) leaves the underside a sharp concave kink there, its faces squeezed
    to 0.003-0.015 mm across: in clay a crisp straight line ringing the toe's underside, on which round 3's
    waist built its cuff.

    The underside is sampled as a height map over the toe's plan frame (the lowest skin per 0.5 mm cell,
    holes filled, smoothed over 0.5 mm; at 0.2 mm cells half were empty and the map pulled the skin into
    spikes), each column smoothed along the toe (a Gaussian of `fold_close_sigma` mm), and the closed surface
    is the smooth minimum of the two: the kink's corner cut away, the convex pads (below their own blur) left
    alone. The squeezed band's vertices are first spread over the surface (a Laplacian relaxation of their plan
    coordinates, `fold_close_relax` passes; moved straight down onto the surface they stacked into degenerate
    faces whose normals drew the line again), then set on the closed surface. Only near the PIP and the DIP,
    on toe 2's own underside, fading at its sides and up its walls. Returns positions."""
    sig = float(P.get("fold_close_sigma", 0.0))
    if not sig:
        return q
    t2m, t2d = segs["t2m"], segs["t2d"]
    w2 = np.clip(groups["toe2-1.L"] + groups["toe2-2.L"] + groups["toe2-3.L"], 0.0, 1.0)
    mine = w2 > 0.5
    pl = Plan(q, mine, t2m.o, t2d.point(t2d.length, 0.0, 0.0))
    s, u, h = pl.local(q)
    cell = 0.5
    s0, u0 = s[mine].min() - 1.0, u[mine].min() - 1.0
    ns, nu = int((s[mine].max() + 1.0 - s0) / cell) + 2, int((u[mine].max() + 1.0 - u0) / cell) + 2
    i, j = ((s[mine] - s0) / cell).astype(int), ((u[mine] - u0) / cell).astype(int)
    H = np.full((ns, nu), np.inf)
    np.minimum.at(H, (i, j), h[mine])
    H[~np.isfinite(H)] = np.nan
    Hs = D._fill(D._blur2d(D._fill(H), 0.5 / cell))
    Hb = _blur_rows(Hs, sig / cell)
    # round 5 (critic round 4 m4: a crisp seam with a glinting ridge still rings toe 2's underside): the soft
    # minimum's knee was 0.06 mm, so the closed surface creased where the blur crossed the raw underside, a line
    # either side of the closed fold; `fold_close_k` rounds the crossing over a few tenths of a millimetre
    k = P.get("fold_close_k", 0.06)
    Hc = Hb - k * np.logaddexp(0.0, (Hb - Hs) / k)          # smin(Hs, Hb): the closed underside
    fine = 5
    Sf, Cf = _resample(Hs, fine), _resample(Hc, fine)
    c2 = cell / fine
    nf0, nf1 = Sf.shape

    def sample(M, ss, uu):
        # the coarse map's cell i is centred on s0 + (i + 0.5) cell; the fine map's node m on the same
        # origin + m c2
        fs, fu = (ss - s0) / c2 - 0.5 * fine, (uu - u0) / c2 - 0.5 * fine
        a0 = np.clip(np.floor(fs).astype(int), 0, nf0 - 2)
        b0 = np.clip(np.floor(fu).astype(int), 0, nf1 - 2)
        a, b = np.clip(fs - a0, 0.0, 1.0), np.clip(fu - b0, 0.0, 1.0)
        return (M[a0, b0] * (1 - a) * (1 - b) + M[a0 + 1, b0] * a * (1 - b) + M[a0, b0 + 1] * (1 - a) * b
                + M[a0 + 1, b0 + 1] * a * b)

    own = T.smoothstep(w2, 0.4, 0.8)                         # toe 2's own skin, not the webs beside it
    sel = np.nonzero(own > 1e-4)[0]
    ss, uu, hh = s[sel], u[sel], h[sel]
    surf = sample(Sf, ss, uu)
    lowest = 1.0 - T.smoothstep(hh - surf, 0.4, 2.0)        # the underside's own skin, not the dorsum above
    umid, half, _, _ = pl.section(ss)
    side = 1.0 - T.smoothstep(np.abs(uu - umid) / np.maximum(half, 1.0), P.get("fold_close_side", 0.55), 1.0)
    s_dip = pl.station(t2d.o)
    w0, w1, w2, w3 = P.get("fold_close_win", (-4.5, -2.5, 5.5, 7.5))
    win = np.maximum(T.window(ss, w0, w1, w2, w3), T.window(ss, s_dip - 3.0, s_dip - 1.5, s_dip + 1.5, s_dip + 3.0))
    omega = lowest * side * win * own[sel]
    # spread the band: relax the plan coordinates (s, u) where omega is full, the rest held
    s2, u2 = ss, uu
    n_rel = int(P.get("fold_close_relax", 0))
    if n_rel and adj is not None:
        w_all = np.zeros(len(q))
        w_all[sel] = T.smoothstep(omega, 0.5, 0.95)
        P2 = np.zeros((len(q), 3))
        P2[:, 0], P2[:, 1] = s, u
        P2 = taubin(P2, adj, 0.9 * w_all, iterations=n_rel, lam=0.5, mu=0.0)
        s2, u2 = P2[sel, 0], P2[sel, 1]
    # on the surface at the new plan position, then down onto the closed surface by omega
    h2 = hh + (sample(Sf, s2, u2) - surf)
    closed = sample(Cf, s2, u2)
    h2 = h2 + omega * np.minimum(closed - h2, 0.0)
    out = q.copy()
    out[sel] = pl.o + np.outer(s2, pl.a) + np.outer(u2, pl.b) + np.outer(h2, pl.n)
    if report is not None:
        moved = np.linalg.norm(out[sel] - q[sel], axis=1)
        report["fold_close"] = {"sigma": sig, "relax": n_rel, "moved_max": round(float(moved.max()), 3),
                                "moved_n": int((moved > 0.01).sum())}
    return out


def room(q, mine, others, gap):
    """How far each of `mine`'s vertices may move out before it comes within `gap` of the `others` (bool
    masks; a k-d tree's nearest distance, conservative for growth along the normal). 0 elsewhere."""
    from mathutils.kdtree import KDTree
    out = np.zeros(len(q))
    oi, mi = np.nonzero(others)[0], np.nonzero(mine)[0]
    if not len(oi) or not len(mi):
        out[mi] = np.inf
        return out
    kd = KDTree(len(oi))
    for i, j in enumerate(oi):
        kd.insert(q[j], i)
    kd.balance()
    out[mi] = [kd.find(q[j])[2] for j in mi]
    return np.maximum(out - gap, 0.0)


def toe2_outline(q, nrm, segs, groups, P, report):
    """Toe 2's outline in plan (critic round 2, m5: an even tube from the PIP to the pulp): the PIP knuckle
    broad (the proximal phalanx's head: its condyles to the sides and a little on top), a waist over the
    middle phalanx, a slight swelling at the DIP and the pulp flaring under the nail. Each is a Gaussian along
    its segment on the toe's sides (|n . b|^1.5), moved along the normals; what grows stays `t2_gap` from any
    other toe's skin (toes 2 and 3 touch, so the knuckle and the flare grow on the free sides and on top), by a
    soft minimum so the limit leaves no crease. Returns the displacement.

    Round 4 (critic round 3, m1: a crisp ledge ringing toe 2's underside like a sleeve cuff): the stations and
    the directions are the toe's plan frame's (Plan), not the segments' planes and the vertex normals. Round 3's
    waist, centred at t 8 on the middle phalanx's tilted axis, landed on the plantar flexion fold under the PIP,
    where the normals turn sharply, and pulling in along them folded the skin over itself. Now each Gaussian
    moves the skin sideways (horizontally, away from the section's midline) by its share of the side
    (|u - midline| / half-width: nothing at the plantar and dorsal midlines), and the knuckle also up on the top,
    so the field is a smooth function of position whatever the normals do; its gradient stays under 0.5."""
    t2m, t2d = segs["t2m"], segs["t2d"]
    w2 = np.clip(groups["toe2-1.L"] + groups["toe2-2.L"] + groups["toe2-3.L"], 0.0, 1.0)
    pl = Plan(q, w2 > 0.5, t2m.o, t2d.point(t2d.length, 0.0, 0.0))
    s, u, h = pl.local(q)
    umid, half, hlo, hhi = pl.section(s)
    du = u - umid
    side = T.smoothstep(np.abs(du) / np.maximum(half, 1.0), 0.2, 0.95)
    top = T.smoothstep((h - 0.5 * (hlo + hhi)) / np.maximum(0.5 * (hhi - hlo), 1.0), 0.15, 0.75)
    s_dip = pl.station(t2d.o)
    s_tip = float(s[groups["toe2-3.L"] > 0.5].max())
    jobs = [  # amount, centre station (mm from the PIP in plan), sigma (mm), share on top
        (P.get("t2_knuckle", 0.0), P.get("t2_knuckle_s", -0.8), 2.4, 0.45),
        (P.get("t2_waist", 0.0), P.get("t2_waist_s", 0.5 * s_dip), 2.4, 0.0),
        (P.get("t2_dip", 0.0), s_dip + 0.3, 1.5, 0.0),
        (P.get("t2_flare", 0.0), s_tip - P.get("t2_flare_back", 6.5), 2.3, 0.0),
    ]
    g = np.zeros(len(q))
    up = np.zeros(len(q))
    # round 5 (critic round 4 m4: from below the outline stepped in at the PIP, the toe's end a cap fitted on):
    # the knuckle's condyles stand out on the upper sides; on the lower sides, the outline seen from below, only
    # `t2_knuckle_low` of it
    upper = T.smoothstep((h - hlo) / np.maximum(hhi - hlo, 1.0), 0.3, 0.7)
    low = P.get("t2_knuckle_low", 1.0)
    for i, (amt, sc, sig, sh) in enumerate(jobs):
        if not amt:
            continue
        gs = T.gauss(s - sc, sig)
        g += amt * gs * side * ((low + (1.0 - low) * upper) if i == 0 else 1.0)
        up += sh * max(amt, 0.0) * gs * top
    g, up = g * w2, up * w2
    pos = np.maximum(g, 0.0) + up
    grow = pos > 1e-3
    scale = np.ones(len(q))
    if grow.any():
        lo, hi = q[grow].min(axis=0) - 5.0, q[grow].max(axis=0) + 5.0
        near = np.all((q > lo) & (q < hi), axis=1) & (w2 < 0.05)
        r = room(q, grow, near, P.get("t2_gap", 0.35))
        k = 0.08
        lim = np.clip(-k * np.logaddexp(-pos[grow] / k, -r[grow] / k), 0.0, None)
        scale[grow] = lim / pos[grow]
        report["toe2_outline"] = {"grow_max": round(float(pos.max()), 2), "limited_n": int((r[grow] < pos[grow]).sum()),
                                  "grown_n": int(grow.sum()), "s_dip": round(s_dip, 2), "s_tip": round(s_tip, 2)}
    sideways = np.where(g > 0.0, g * scale, g) * np.sign(du)
    return sideways[:, None] * pl.b[None, :] + (up * scale)[:, None] * pl.n[None, :]


def web_zone(q, segs, P):
    """The 1-2 cleft's floor: between the hallux and toe 2, behind the commissure line P['web_y'], low."""
    a, b = segs["h1"].o, segs["t2p"].o
    xm = 0.5 * (a[0] + b[0])
    xw = 0.5 * abs(b[0] - a[0])
    zone = (1.0 - T.smoothstep(np.abs(q[:, 0] - xm), 0.35 * xw, 0.75 * xw)) \
        * T.window(q[:, 1], P["web_y"] - 6.0, P["web_y"] - 1.0, a[1] + 4.0, a[1] + 12.0) \
        * (1.0 - T.smoothstep(q[:, 2], 18.0, 26.0))
    return zone


def plan_crease(q, pl, t0, depth, width, bow=0.0, half=8.0, seed=0, wobble=0.2, under=(0.12, 0.4), shoulders=False):
    """A plantar flexion crease in a toe's plan frame (round 4): a soft dip (a Gaussian section of sigma
    `width`; with `shoulders`, detail.crease's groove with low raised shoulders, which in profile put a bump on
    each side of the dip) with detail.crease's seeded wobble, centred under the joint (station t0 of the plan
    frame pl), cut straight up into the toe, confined to the underside by position (the section's lowest part,
    `under` as shares of its height) and fading toward its ends at |u - midline| = half.

    Not along the normals: under the curled toe's PIP part 01's curl squeezed the plantar skin into a band of
    faces 0.003-0.015 mm across whose normals turn 45 degrees across it, and a groove cut along them flipped
    35 faces there. A displacement f(p) along one fixed direction e maps space with determinant 1 + df/de, so
    it cannot fold anything while f falls slower than 1:1 along e; here df/dz comes only from the `under`
    fade (about 0.3 at most). Returns (displacement, crease weight)."""
    s, u, h = pl.local(q)
    _, _, hlo, hhi = pl.section(s)
    u0 = float(pl.section(np.array([t0]))[0][0])
    across = (u - u0) / half
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0.0, 2.0 * np.pi, 4)
    vary = 1.0 + wobble * (np.sin(2.1 * across + ph[0]) + 0.6 * np.sin(4.7 * across + ph[1]))
    shift = 0.35 * width * (np.sin(1.7 * across + ph[2]) + 0.5 * np.sin(3.9 * across + ph[3]))
    d = (s - (t0 + bow * across ** 2 + shift)) / width
    prof = ((1.0 - d * d) if shoulders else 1.0) * np.exp(-0.5 * d * d)
    low = 1.0 - T.smoothstep((h - hlo) / np.maximum(hhi - hlo, 1.0), under[0], under[1])
    ends = (1.0 - T.smoothstep(np.abs(across), 0.5, 1.0)) * low
    w = np.clip(prof, 0.0, 1.0) * ends
    return (depth * np.clip(vary, 0.4, 1.5) * prof * ends)[:, None] * pl.n[None, :], w


def creases(q, nrm, segs, P, groups=None):
    """The joints' skin creases (detail.crease): dorsal and plantar at the hallux IP, toe 2's PIP and DIP,
    and the faint lines at the hallux's base. Returns (displacement, crease weight).

    Round 4 (critic round 3, m1, m4, m21): the plantar flexion creases are placed in the toes' plan frames
    (Plan: a vertical plane through the joint), so each lies under its joint; in the segments' tilted frames
    they sat 3 to 8 mm proximal (toe 2's PIP crease under its proximal phalanx, read as a slot at the toe's
    base; its DIP crease under the middle phalanx). They are soft infolds (wider, shallower) cut straight up
    on the underside only (plan_crease), fading before the sides, and they shade the skin less (`shade`, the
    share written to Foot.Crease), so the shader's crease groove does not cut them."""
    dq = np.zeros_like(q)
    cw = np.zeros(len(q))
    k = P.get("crease_scale", 1.0)
    jobs = [  # segment, t0, depth, width, side, bow, half[, wrap, shade]
        # hallux IP: dorsal wrinkles (curved distally at the centre)
        ("h2", -1.4, 0.035, 0.5, 1.0, 1.2, 8.0), ("h2", 0.7, 0.055, 0.55, 1.0, 1.4, 9.0),
        ("h2", 2.8, 0.03, 0.45, 1.0, 1.4, 7.0),
        # hallux base (MTP), dorsal, faint
        ("h1", 4.0, 0.06, 0.45, 1.0, 0.0, 9.0),
        # toe 2: PIP knuckle wrinkles, DIP crease
        ("t2m", -1.8, 0.05, 0.32, 1.0, 0.8, 6.0), ("t2m", -0.4, 0.07, 0.34, 1.0, 0.8, 6.5),
        ("t2m", 1.0, 0.06, 0.32, 1.0, 0.8, 6.0), ("t2m", 2.3, 0.04, 0.3, 1.0, 0.8, 5.0),
        ("t2d", 0.6, 0.05, 0.34, 1.0, 0.6, 5.0),
        # the plantar flexion creases, soft dips in plan frames from their joints (P: crease1_s, crease2p_s,
        # crease2d_s; sigma `width`); toe 2's PIP crease lies in the fold close_folds rounded
        ("plan_h2", P.get("crease1_s", 1.0), 0.3, 1.0, -1.0, -1.5, 8.0, 0.8, 0.35),
        ("plan_t2m", P.get("crease2p_s", 1.5), P.get("crease2p_d", 0.22), P.get("crease2p_w", 0.7), -1.0, -0.6, 5.0, 0.8,
         0.35),
        ("plan_t2d", P.get("crease2d_s", 0.8), 0.2, 0.6, -1.0, -0.5, 4.5, 0.8, 0.35),
    ]
    plans = {}
    if groups is not None:
        h2, t2m, t2d = segs["h2"], segs["t2m"], segs["t2d"]
        w1 = np.clip(groups["toe1-1.L"] + groups["toe1-2.L"], 0.0, 1.0) > 0.5
        w2 = np.clip(groups["toe2-1.L"] + groups["toe2-2.L"] + groups["toe2-3.L"], 0.0, 1.0) > 0.5
        tip2 = t2d.point(t2d.length, 0.0, 0.0)
        plans = {"plan_h2": Plan(q, w1, h2.o, h2.point(h2.length, 0.0, 0.0)),
                 "plan_t2m": Plan(q, w2, t2m.o, tip2), "plan_t2d": Plan(q, w2, t2d.o, tip2)}
    seeds = (0, 1, 2, 4, 5, 6, 7, 8, 9, 3, 10, 11)   # round 3's order, so the dorsal creases keep their wobble
    for i, job in zip(seeds, jobs):
        name, t0, depth, width, side, bow, half = job[:7]
        wrap, shade = (job[7], job[8]) if len(job) > 7 else (0.35, 1.0)
        if name.startswith("plan_"):
            if name not in plans:
                continue
            d, w = plan_crease(q, plans[name], t0, k * depth, width, bow=bow, half=half, seed=17 + i)
        else:
            seg = segs[name]
            if name == "h2":
                t0 += P.get("ip_shift", 0.0)
            d, w = D.crease(q, nrm, seg, t0, k * depth, width, side=side, bow=bow, half=half, wrap=wrap, seed=17 + i)
        dq += d
        cw = np.maximum(cw, shade * w)
    return dq, cw
