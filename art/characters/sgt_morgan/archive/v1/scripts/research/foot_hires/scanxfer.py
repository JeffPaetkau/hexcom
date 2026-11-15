"""The dense skin laid on the scan (the scan transfer, 2026-10-17; notes/research_foot_hires.md "Scan transfer").

Part 01 transfers the foot's large forms from subject 038's scan onto its cage (scripts/parts/p01/transfer.py), whose
quads (4 mm on the toes, 10-20 mm on the foot and ankle) carry the scan to within about a millimetre at their limit
points and round off what lies between them: the heel pad's rim, the arch's edge, the ball's crescent, the tendons and
the malleoli. Here the trial's dense copy (0.1-0.4 mm) is laid on the scan itself, with part 01's masks and placement:

  * where: the scan's frame onto this foot by the matrix part 01 stored on Frame.Foot.L ("p01_scan"), so the dense
    skin meets the very surface its cage was fitted to;
  * what: every vertex's nearest point on the scan (no further than `max_dist`, facing within ~70 degrees), lifted off
    the scan's 1.5 mm facets onto their Phong patch (`phong`), so no facet prints in clay;
  * how much: all of it below blend_z[0], none above blend_z[1] (a smootherstep share between: the dense skin there
    is the cage's, which part 01 has already eased from the scan into the leg; fading the data's weight instead, as
    the cage does, left the dense skin on the scan until its weight was gone and creased it round the ankle at the
    cut, xfer4); nothing where part 01's Foot.ScanKeep group is 1 (the skin between the toes, ours), fading with it;
  * smoothly: the displacement solved as part 01's (transfer.Solver, no limit stencil: a dense skin is its own limit),
    its smoothness weighted by edge length so it acts over about `smooth_mm` whatever the local spacing, which also
    carries the kept zones along with the toes they lie between; `iters` passes, each with fresh nearest points.

Runs in the stage (method_fields.build) right after the curled toes' folds are closed, before the nails, creases,
veins, tendons and hair, which stay the trial's.
"""
import json
import math
import os
import sys

import numpy as np

import common as C

SCRIPTS = os.path.dirname(os.path.dirname(C.HERE))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

SCAN_TRANSFER = {"on": 1, "iters": 2, "phong": 0.75, "smooth_mm": 0.9, "max_dist": 5.0, "facing": 0.3,
                 "blend_z": [100.0, 118.0], "keep_group": "Foot.ScanKeep", "cg_iters": 400,
                 "band_smooth": {"z": [94.0, 102.0, 118.0, 130.0], "k": 1.0},
                 "lift": {"on": 1, "band": [100.0, 116.0], "ease": [116.0, 252.0], "bins": 120, "sigma_deg": 7.0,
                          "run_mm": 15.0, "run_max": 3.0,
                          "front_y": -150.0}}
# Round 3b's fixes (2026-10-27; critic series foot_shape round 3b m2, m8, m10: from behind a broad flat face over the
# heel's medial side, the column leaning medially; a notch in the Achilles' line at z 110). The scan's ankle is kept
# through z 110 and fades by 124 (part 01's blend_z, was 95-125: the Achilles' cord and its hollows above z 95 were half
# ours), and above it the dense skin carries the scan's section at the cut (`lift`): over `band` the scan's horizontal
# sections against the dense skin's own (the cage's limit, which part 01 has already laid on the scan's breadths there),
# as radii from the scan's centre in `bins` sectors, smoothed over `sigma_deg`; each leg vertex above the band moved
# radially in plan by its sector's difference, easing out over `ease` (smootherstep): the Achilles' cord and the hollows
# beside it run on up the leg and fade into it, as a real Achilles does, instead of stopping at the scan's cut. (The first
# build, the blend over 110-124 with the dense skin's own 0.9 mm smoothness, turned the scan's slope above the malleoli
# onto the leg's within a few millimetres: a faint horizontal line round the ankle at the cut in clay. The blend now
# runs over 100-118, clear of the scan's last 8 mm under its cut (126.6 once scaled), where its walls turn in toward the
# cap (medially 1.5 mm and in front 2.3 over 120-125); the lift is read at every height of 100-116 (section_lift), so
# within the blend the lifted cage is the scan's own section and the two surfaces it mixes agree (a band-averaged lift
# left a faint line where the blend began); above the band it runs on at its slope there, damped (`run_mm`), so the leg
# leaves the band at the scan's slope. A smoothness 16 times stronger over the band (`band_smooth.k`) was tried and is
# off: it flattened the band into a bright facet with an edge at each end in clay.)


def _cfg(P):
    out = dict(SCAN_TRANSFER)
    out.update(P.get("scan_transfer") or {})
    return out


def placement(frame_name="Frame.Foot.L"):
    """Part 01's record of where its reference scan lies on this foot: (scan id, 4 x 4 scans' frame -> world, mm)."""
    import bpy
    fr = bpy.data.objects.get(frame_name)
    if fr is None or "p01_scan" not in fr:
        return None, None
    rec = json.loads(fr["p01_scan"])
    return rec, np.array(rec["M"], float)


class _Dense:
    """The dense skin as transfer.Solver reads a cage: its edges, every vertex its own limit."""

    def __init__(self, n, edges):
        self.n = n
        self.edges = np.asarray(edges, np.int64)
        self.interior = np.ones(n, bool)
        idx = np.arange(n)
        self.S = (idx, idx, np.ones(n))


def section_lift(q, tris, sq, sT, cfg):
    """The scan's sections carried onto the cage's leg and up it (SCAN_TRANSFER["lift"]): at each height over `band`
    (1.5 mm apart) the scan's horizontal section against the dense skin's own, as radii from the scan's centre in
    `bins` sectors, smoothed over `sigma_deg` and across neighbouring heights; a function of positions (F, mm) giving
    each one's plan displacement (n, 2): its height's difference within the band (the lowest below it), the band's
    top one above it easing out over `ease`. Within the band the cage so lifted is the scan's own section, so the blend
    from the scan to it joins two near-equal surfaces (one band-averaged difference left a line where it began)."""
    from parts.p01 import scanfit
    from parts.p01 import transfer as X
    c = cfg
    zs = np.arange(c["band"][0], c["band"][1] + 0.1, 1.5)
    S_, O_ = [], []
    for z in zs:
        a = scanfit.section_points(sq, sT, 2, float(z))
        b = scanfit.section_points(q, tris, 2, float(z))
        S_.append(a[a[:, 1] > c["front_y"]])
        O_.append(b[b[:, 1] > c["front_y"]])
    Sa = np.concatenate(S_)
    ctr = np.array([0.5 * (Sa[:, 0].min() + Sa[:, 0].max()), 0.5 * (Sa[:, 1].min() + Sa[:, 1].max())])
    nb = int(c["bins"])
    idx = np.arange(nb)
    sig = c["sigma_deg"] / (360.0 / nb)
    ker = np.exp(-0.5 * (np.arange(-3 * int(sig + 1), 3 * int(sig + 1) + 1) / sig) ** 2)
    ker /= ker.sum()
    pad = len(ker) // 2

    def radii(P):
        d = P[:, :2] - ctr
        th = np.arctan2(d[:, 1], d[:, 0])
        k = np.clip(((th + math.pi) / (2.0 * math.pi) * nb).astype(int), 0, nb - 1)
        out = np.full(nb, -np.inf)
        np.maximum.at(out, k, np.linalg.norm(d, axis=1))
        return np.where(np.isfinite(out), out, np.nan)
    D = np.zeros((len(zs), nb))
    for i in range(len(zs)):
        dr = radii(S_[i]) - radii(O_[i])
        ok = np.isfinite(dr)
        dr = np.interp(idx, idx[ok], dr[ok], period=nb)
        D[i] = np.convolve(np.concatenate([dr[-pad:], dr, dr[:pad]]), ker, mode="valid")
    if len(zs) > 2:   # across heights, [1, 2, 1] / 4 with the ends held
        Dp = np.vstack([D[:1], D, D[-1:]])
        D = 0.25 * Dp[:-2] + 0.5 * Dp[1:-1] + 0.25 * Dp[2:]
    # above the band the difference runs on at its slope there, saturating over `run_mm` (a damped extrapolation,
    # at most `run_max` mm more), so the lifted leg leaves the band at the scan's slope and turns to the cage's
    # gradually: held at the top's value it left the band at the cage's slope, a crease round the ankle at 116
    # (back-medially the scan rises straight, r +0.1 mm per mm, the cage flares at +0.25)
    k = min(3, len(zs) - 1)
    Ds = (D[-1] - D[-1 - k]) / (zs[-1] - zs[-1 - k]) if k > 0 else np.zeros(nb)
    L_run = float(c.get("run_mm", 15.0))
    Ds = np.clip(Ds, -c.get("run_max", 3.0) / L_run, c.get("run_max", 3.0) / L_run)

    def lift(p):
        d = p[:, :2] - ctr
        th = np.arctan2(d[:, 1], d[:, 0])
        u = d / np.maximum(np.linalg.norm(d, axis=1), 1e-9)[:, None]
        f = (th + math.pi) / (2.0 * math.pi) * nb - 0.5
        j0 = np.floor(f).astype(int)
        s_ = f - j0
        j0 %= nb
        j1 = (j0 + 1) % nb
        g = np.clip((p[:, 2] - zs[0]) / 1.5, 0.0, len(zs) - 1.0)
        i0 = np.minimum(np.floor(g).astype(int), len(zs) - 1)
        i1 = np.minimum(i0 + 1, len(zs) - 1)
        t = g - i0
        dv = ((1.0 - t) * ((1.0 - s_) * D[i0, j0] + s_ * D[i0, j1]) + t * ((1.0 - s_) * D[i1, j0] + s_ * D[i1, j1]))
        above = np.maximum(p[:, 2] - zs[-1], 0.0)
        dv = dv + ((1.0 - s_) * Ds[j0] + s_ * Ds[j1]) * L_run * (1.0 - np.exp(-above / L_run))
        w = (1.0 - X.smootherstep(p[:, 2], *c["ease"])) * (p[:, 1] > c["front_y"] - 10.0)
        return (dv * w)[:, None] * u
    rec = {"centre": np.round(ctr, 2).tolist(), "heights": [float(zs[0]), float(zs[-1])],
           "dr_min": round(float(D.min()), 2), "dr_max": round(float(D.max()), 2),
           "dr_back_top": round(float(np.interp(nb * 0.75 - 0.5, idx, D[-1], period=nb)), 2)}
    return lift, rec


def apply(ctx, q, topo, P, report=None):
    """The dense skin (frame F, mm) laid on the scan. Returns positions."""
    from parts.p01 import transfer as X
    cfg = _cfg(P)
    if not cfg.get("on"):
        return q
    rec, M = placement()
    if rec is None:
        if report is not None:
            report["scan_transfer"] = "part 01 has no scan placement (its transfer is off): skipped"
        return q
    ref = X.load_reference(rec["id"], rec.get("rest", "mBW"))
    # the scan into this foot's frame F: scans' frame -> world (part 01's matrix) -> F
    w = ref.q @ M[:3, :3].T + M[:3, 3]
    sq = ctx.frame.to_f(w)
    T = ref.T if np.linalg.det(M[:3, :3]) > 0 else ref.T[:, ::-1]
    surf = X.Surface(sq, T)
    keep = np.clip(C.group(ctx.skin, cfg["keep_group"]), 0.0, 1.0)
    edges, lengths = C.edge_lengths(ctx.skin)
    dense = _Dense(len(q), edges)
    z = q[:, 2]
    blend = 1.0 - X.smootherstep(z, *cfg["blend_z"])
    lc = cfg.get("lift") or {}
    top = max(cfg["blend_z"][1], lc["ease"][1] if lc.get("on") else 0.0)
    free = z < top + 15.0
    lift_d = np.zeros_like(q)
    lift_rec = None
    if lc.get("on"):
        from parts.p01 import scanfit
        tris = scanfit.triangles(*topo)
        lift, lift_rec = section_lift(q, tris, sq, T, lc)
        sel = np.nonzero(free & (z > lc["band"][0] - 6.0))[0]
        lift_d[sel, :2] = lift(q[sel])
    # the smoothness term per edge (h0 / l)^2 with h0 1 mm, so its reach is smooth_mm whatever the spacing (energy:
    # sum |U - g|^2 over vertices ~ integral / l^2, sum w |dU|^2 over edges ~ 2 integral |grad U|^2: length^2 = 2 mu)
    ew = np.clip((1.0 / np.maximum(lengths, 1e-3)) ** 2, 0.0, 400.0)
    bs = cfg.get("band_smooth") or {}
    if bs.get("k", 1.0) > 1.0:
        zb = bs["z"]
        zm = 0.5 * (z[edges[:, 0]] + z[edges[:, 1]])
        ew = ew * (1.0 + (bs["k"] - 1.0) * X.smootherstep(zm, zb[0], zb[1]) * (1.0 - X.smootherstep(zm, zb[2], zb[3])))
    mu = 0.5 * cfg["smooth_mm"] ** 2
    sol = X.Solver(dense, free, limit=False, edge_w=ew)
    act = np.nonzero(free & (keep < 0.999) & (blend > 0.0))[0]
    U = np.zeros_like(q)
    nrm = C.vertex_normals(q, topo)
    rep = []
    for it in range(int(cfg["iters"])):
        cur = q + U
        nrm = C.vertex_normals(cur, topo)
        Cp, N, D = surf.nearest(cur[act], phong=cfg["phong"])
        ok = (D < cfg["max_dist"]) & (np.einsum("ij,ij->i", nrm[act], N) > cfg["facing"])
        wgt = np.zeros(len(q))
        g = np.zeros_like(q)
        a_ok = act[ok]
        wgt[a_ok] = 1.0 - keep[a_ok]
        # toward the blended point, from where the skin began: the scan below, the cage's leg carrying the scan's section
        # at the cut above (lift_d, round 3b's fixes)
        g[a_ok] = blend[a_ok, None] * (Cp[ok] - q[a_ok]) + (1.0 - blend[a_ok, None]) * lift_d[a_ok]
        held = free & (blend <= 0.0)                       # over the cut the dense skin is the cage's, lifted
        wgt[held], g[held] = 1.0, lift_d[held]
        U = sol.solve(wgt, g, mu, U, iters=int(cfg["cg_iters"]))
        full = a_ok[(keep[a_ok] < 0.05) & (blend[a_ok] > 0.999)]
        res = np.linalg.norm((q + U)[full] - (q[full] + g[full]), axis=1)
        Cf, Nf, Df = surf.nearest((q + U)[full[::25]], phong=cfg["phong"])
        rep.append({"it": it, "on_scan": int(ok.sum()), "of": int(len(act)),
                    "moved_rms": round(float(np.sqrt(np.mean(np.sum(U[a_ok] ** 2, 1)))), 3),
                    "residual_rms": round(float(np.sqrt(np.mean(res ** 2))), 3),
                    "off_scan_rms": round(float(np.sqrt(np.mean(Df ** 2))), 3),
                    "off_scan_p95": round(float(np.percentile(Df, 95)), 3)})
    if report is not None:
        report["scan_transfer"] = {"scan": rec["id"], "passes": rep, "kept": int((keep > 0.5).sum()),
                                   "moved_max": round(float(np.linalg.norm(U, axis=1).max()), 2), "lift": lift_rec}
    return q + U
