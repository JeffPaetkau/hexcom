"""Whole foot, pass 1 (2026-10-13; notes/research_foot_hires.md): the detail the trial's region lacked, for every
toe, applied after the stage (the large forms and the webs), so none of it rebuilds the stage cache.

  * tendons: the extensor hallucis longus as a cord over the first metatarsal, the MTP and the hallux's proximal
    phalanx, fading at the IP, and the extensor digitorum's four slips onto toes 2-5, fading into the dorsum
    proximally and over the proximal phalanges distally; strongest over the metatarsal heads, where the skin is
    thinnest (round 5's blocking m1). Each is a raised section along a plan polyline, a little gutter either side;
  * creases: the dorsal knuckle creases as clusters of short, broken, uneven grooves, a different draw per joint
    (round 5's m6 and m15: one stamp of long parallel grooves). The geometry is a few hundredths of a millimetre,
    so no crease dents the profile; the shader draws them from Foot.Crease. The plantar flexion creases are
    macro.plan_crease's, on every toe;
  * masks the materials read: Foot.Ridges (the friction ridges' phase field: a whorl or loop on each pulp, arcs on
    the toes' proximal pads and on the ball, breaking at the creases; spec 16's MG.Skin.Micro reads it, round 5's
    m5), Hires.Sheen (the forefoot dorsum made matte, look.py), Foot.Tendon (the cords' crests, the recipe's own
    tendon lightening), and the stand-in corn removed.
"""
import math

import numpy as np

import common as C
import macro as M
import toes as T

TENDONS = {
    # amplitude (mm), the section's radius (mm: (1 - (d / r)^2)^2, about 0.54 r at half height), a gutter beside the
    # cord (share of the amplitude) and where along the path (0 start, 1 end) the cord rises to full and fades out.
    # The first build's (1 - x^2)^1.5 over 2.6 mm with a 0.16 gutter, along a polyline, read in clay as piping with
    # a groove each side and kinks at the polyline's corners: the paths are now Catmull-Rom curves, the sections
    # broader and softer, no gutter
    "ehl": {"amp": 1.1, "half": 3.6, "gutter": 0.0, "rise": (0.05, 0.35), "fade": (0.84, 1.0)},
    "edl": {"amp": [0.62, 0.55, 0.5, 0.4], "half": 2.6, "gutter": 0.0, "rise": (0.25, 0.6), "fade": (0.8, 1.0)},
    "mask_share": 0.3,    # Foot.Tendon on the crests (the recipe adds 1.5 mm of bump and 3 % lightening at 1)
}

# the dorsal knuckle creases: segment, centre (mm along it; "ip" = the hallux IP's shifted station), spread (mm
# either side), half-span across (mm), count, depth (mm), crease weight, roll (degrees, as detail.Nail's), seed
KNUCKLES = [
    ("h2", "ip", 2.3, 8.5, 6, 0.022, 0.85, 0.0, 101),
    ("h1", 4.5, 1.4, 7.0, 2, 0.010, 0.3, 0.0, 102),
    ("t2m", 0.4, 1.7, 5.5, 5, 0.018, 0.8, 0.0, 103),
    ("t2d", 1.2, 0.9, 4.2, 3, 0.012, 0.55, 0.0, 104),
    ("t3m", 0.4, 1.5, 5.0, 4, 0.017, 0.75, 0.0, 105),
    ("t3d", 1.0, 0.8, 3.8, 2, 0.011, 0.5, 0.0, 106),
    ("t4m", 0.4, 1.4, 4.6, 4, 0.016, 0.7, -9.0, 107),
    ("t4d", 0.9, 0.8, 3.5, 2, 0.011, 0.45, -9.0, 108),
    ("t5m", 0.3, 1.2, 4.2, 3, 0.015, 0.65, -30.0, 109),
    ("t5d", 0.7, 0.7, 3.0, 2, 0.010, 0.4, -38.0, 110),
]

# the friction ridges' patterns on the pulps: a whorl (concentric, a one-ridge spiral) or a loop opening to a
# side (+1 lateral, -1 medial)
RIDGES = {"pulp": {1: ("whorl", 0), 2: ("loop", 1), 3: ("whorl", 0), 4: ("loop", 1), 5: ("loop", 1)},
          "sole_centre": (-5.0, -125.0, -40.0), "core_mm": (0.25, 0.8), "gap_mm": 0.35}

SHEEN = {"forefoot_y": (135.0, 170.0), "up": (0.15, 0.55), "toes": 0.75}


def _cfg(P, key, base):
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
    for k, v in (P.get(key) or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


def catmull_rom(pts, n=24):
    """A smooth plan curve through the points (uniform Catmull-Rom, ends repeated), n samples a span."""
    P_ = np.asarray(pts, float)[:, :2]
    P_ = np.vstack([P_[0], P_, P_[-1]])
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        t = np.linspace(0.0, 1.0, n, endpoint=False)[:, None]
        out.append(0.5 * (2.0 * p1 + (p2 - p0) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t * t
                          + (3.0 * p1 - p0 - 3.0 * p2 + p3) * t ** 3))
    out.append(P_[-2][None, :])
    return np.vstack(out)


def polyline_plan(q, pts):
    """Each point's distance in plan (x, y) to a polyline and its share of the way along it (0..1)."""
    pts = np.asarray(pts, float)[:, :2]
    xy = q[:, :2]
    best = np.full(len(q), np.inf)
    s_best = np.zeros(len(q))
    seglen = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    total = float(seglen.sum())
    run = 0.0
    for i in range(len(pts) - 1):
        a, ab = pts[i], pts[i + 1] - pts[i]
        t = np.clip(((xy - a) @ ab) / (ab @ ab), 0.0, 1.0)
        d = np.linalg.norm(xy - (a + np.outer(t, ab)), axis=1)
        better = d < best
        best[better] = d[better]
        s_best[better] = (run + t[better] * seglen[i]) / total
        run += seglen[i]
    return best, s_best


def tendons(q, nrm, segs, groups, J, P, report=None):
    """The long extensors as raised cords (round 5's blocking m1). Returns (positions, a 0-1 crest mask)."""
    cfg = _cfg(P, "tendons", TENDONS)
    up = T.smoothstep(nrm[:, 2], 0.25, 0.65)
    dq = np.zeros(len(q))
    crest = np.zeros(len(q))
    ip = segs["h2"].point(P.get("ip_shift", 0.0) - 1.0, 0.0, 0.0)
    m1 = J["toe-1-1"]
    paths = [("ehl", cfg["ehl"], cfg["ehl"]["amp"], [(-12.0, -120.0), (-21.5, -170.0), (m1[0] + 1.0, m1[1]),
                                                     (ip[0], ip[1])])]
    x0s = (-5.0, 1.0, 7.0, 13.0)
    for i, k in enumerate((2, 3, 4, 5)):
        mk, pk = J[f"toe-{k}-1"], J[f"toe-{k}-2"]
        paths.append((f"edl{k}", cfg["edl"], cfg["edl"]["amp"][i], [(x0s[i], -125.0), (0.5 * (x0s[i] + mk[0]), -170.0),
                                                                   (mk[0], mk[1]), (pk[0], pk[1])]))
    rep = {}
    for name, c, amp, pts in paths:
        lo = np.min(np.asarray(pts, float), axis=0) - 2.0 * c["half"]
        hi = np.max(np.asarray(pts, float), axis=0) + 2.0 * c["half"]
        box = np.nonzero(np.all((q[:, :2] > lo) & (q[:, :2] < hi), axis=1))[0]
        d = np.full(len(q), np.inf)
        s = np.zeros(len(q))
        d[box], s[box] = polyline_plan(q[box], catmull_rom(pts))
        near = d < 2.0 * c["half"]
        x = d[near] / c["half"]
        cord = np.clip(1.0 - x * x, 0.0, 1.0) ** 2 - c["gutter"] * np.exp(-((x - 1.35) / 0.45) ** 2)
        along = T.smoothstep(s[near], *c["rise"]) * (1.0 - T.smoothstep(s[near], *c["fade"]))
        h = amp * cord * along * up[near]
        dq[near] += h
        crest[near] = np.maximum(crest[near], np.clip(cord, 0.0, 1.0) * along * up[near] * amp / cfg["ehl"]["amp"])
        rep[name] = {"max_mm": round(float(h.max()), 2), "n": int((h > 0.05).sum())}
    if report is not None:
        report["tendons"] = rep
    return q + dq[:, None] * nrm, np.clip(crest, 0.0, 1.0)


def _knuckle(q, nrm, seg, t_c, spread, half, n, depth, weight, rng):
    """One joint's cluster of short creases on a segment's dorsum. Returns (depth field, weight field)."""
    t, u, h = seg.local(q)
    gate = T.smoothstep(nrm @ seg.n, 0.15, 0.5)
    sel = np.nonzero((np.abs(t - t_c) < spread + 3.0) & (np.abs(u) < half + 2.0) & (gate > 1e-3))[0]
    D_ = np.zeros(len(q))
    W_ = np.zeros(len(q))
    if not len(sel):
        return D_, W_
    ts, us, gs = t[sel], u[sel], gate[sel]
    offs = np.linspace(-spread, spread, n) + rng.normal(0.0, 0.22 * spread / max(n - 1, 1), n)
    jobs = []
    for i, o in enumerate(offs):
        central = 1.0 - 0.45 * abs(o) / max(spread, 1e-3)
        L = half * rng.uniform(0.3, 0.72) * central
        jobs.append((t_c + o, half * rng.uniform(-0.3, 0.3), L, math.radians(rng.normal(0.0, 8.0)),
                     rng.uniform(-0.6, 0.9), depth * rng.uniform(0.45, 1.0) * central, rng.uniform(0.15, 0.28),
                     weight * rng.uniform(0.55, 1.0) * central, rng.random() < 0.45, rng.uniform(-0.5, 0.5)))
        if rng.random() < 0.3:      # a short fork off one end
            sgn = 1.0 if rng.random() < 0.5 else -1.0
            jobs.append((t_c + o + rng.uniform(0.15, 0.4), jobs[-1][1] + sgn * 0.8 * L, 0.35 * L,
                         jobs[-1][3] + sgn * math.radians(rng.uniform(18.0, 32.0)), 0.0, 0.6 * jobs[-1][5], 0.15,
                         0.6 * jobs[-1][7], False, 0.0))
    for tc, uc, L, th, bow, dep, wid, wt, broken, gap_at in jobs:
        ct, st = math.cos(th), math.sin(th)
        along = (us - uc) * ct + (ts - tc) * st
        across = (ts - tc - bow * (along / max(L, 1e-3)) ** 2) * ct - (us - uc) * st
        prof = np.exp(-0.5 * (across / wid) ** 2)
        taper = 1.0 - T.smoothstep(np.abs(along), 0.45 * L, L)
        vary = 0.75 + 0.25 * np.sin(along * 2.3 + 7.0 * uc)
        if broken:
            vary = vary * (1.0 - 0.92 * np.exp(-0.5 * ((along - gap_at * L) / (0.18 * L + 0.1)) ** 2))
        f = prof * taper * vary * gs
        D_[sel] = np.maximum(D_[sel], dep * f)
        W_[sel] = np.maximum(W_[sel], wt * f)
    return D_, W_


def creases(q, nrm, segs, P, groups, report=None):
    """The skin creases of every toe: the dorsal knuckle clusters (KNUCKLES) and the plantar flexion creases
    (macro.plan_crease, in each toe's plan frame). Returns (displacement, crease weight)."""
    dq = np.zeros_like(q)
    cw = np.zeros(len(q))
    k_ = P.get("crease_scale", 1.0)
    kn = P.get("knuckles") or {}
    owner = {"h": 1, "t2": 2, "t3": 3, "t4": 4, "t5": 5}
    for segname, tc, spread, half, n, depth, weight, roll, seed in KNUCKLES:
        seg = T.rolled(segs[segname], roll)
        if tc == "ip":
            tc = P.get("ip_shift", 0.0) + 0.3
        depth = depth * kn.get("depth", 1.3) * k_
        weight = weight * kn.get("weight", 1.4)
        D_, W_ = _knuckle(q, nrm, seg, tc, spread, half, n, depth, weight, np.random.default_rng(seed))
        wk = T.smoothstep(T.toe_weight(groups, owner[segname[:2] if segname[0] == "t" else "h"]), 0.3, 0.7)
        dq -= (D_ * wk)[:, None] * nrm
        cw = np.maximum(cw, W_ * wk)
    # the plantar flexion creases: round 4's for the hallux and toe 2, and the lesser toes' PIP and DIP
    pl_k = {}
    for k in (1, 2, 3, 4, 5):
        wk = T.toe_weight(groups, k) > 0.5
        segd = segs[T.TOES[k][0]]
        tip = segd.point(segd.length, 0.0, 0.0)
        if k == 1:
            pl_k[(1, "ip")] = M.Plan(q, wk, segs["h2"].o, tip)
        else:
            pl_k[(k, "pip")] = M.Plan(q, wk, segs[f"t{k}m"].o, tip)
            pl_k[(k, "dip")] = M.Plan(q, wk, segs[f"t{k}d"].o, tip)
    pc = P.get("plantar_lesser") or {}
    jobs = [((1, "ip"), P.get("crease1_s", 1.0), 0.3, 1.0, -1.5, 8.0, 17 + 3),
            ((2, "pip"), P.get("crease2p_s", 1.5), P.get("crease2p_d", 0.22), P.get("crease2p_w", 0.7), -0.6, 5.0, 17 + 10),
            ((2, "dip"), P.get("crease2d_s", 0.8), 0.2, 0.6, -0.5, 4.5, 17 + 11)]
    # (the first build's 0.12 / 0.16 mm with ends fading over half their span read from below as slots cut in
    # each middle phalanx: shallower, wider, longer)
    for k, hw in ((3, 5.6), (4, 5.3), (5, 5.0)):
        jobs.append(((k, "pip"), pc.get("pip_s", 1.6), pc.get("pip_d", 0.07), pc.get("pip_w", 1.2), -0.5, hw, 40 + k))
        jobs.append(((k, "dip"), pc.get("dip_s", 0.8), pc.get("dip_d", 0.07), pc.get("dip_w", 0.85), -0.4, hw - 0.4, 50 + k))
    for key, t0, depth, width, bow, half, seed in jobs:
        d, w = M.plan_crease(q, pl_k[key], t0, k_ * depth, width, bow=bow, half=half, seed=seed)
        dq += d
        cw = np.maximum(cw, 0.35 * w)
    if report is not None:
        report["creases"] = {"dorsal_clusters": len(KNUCKLES), "plantar": len(jobs),
                             "weight_max": round(float(cw.max()), 2)}
    return dq, cw


def ridge_field(q, nrm, groups, J, segs, cw, P):
    """Foot.Ridges: (phase mm, coverage, amplitude) per vertex. The ridges are the phase's level lines at spec 16's
    pitch (MG.Skin.Micro's Ridge Field mm): on each pulp a whorl (distance from a core, plus one pitch per turn,
    so the rings close into a spiral without a seam) or a loop (distance to a line from the core out to one side:
    hairpins round the core); on the toes' proximal pads and the ball, arcs (distance from a far centre). The
    amplitude falls to nothing at the flexion creases, at each region's border (where the phase jumps) and at a
    whorl's core."""
    from lib import mat_catalogue as CAT
    cfg = _cfg(P, "ridges", RIDGES)
    pitch = float(CAT.SKIN_FOOT["micro"]["D_ridges"]["pitch_mm"])
    phase = np.linalg.norm(q - np.asarray(cfg["sole_centre"]), axis=1)     # the sole: arcs round the arch
    amp = np.ones(len(q))
    wt = T.toes_weight(groups)
    amp *= 1.0 - np.exp(-0.5 * ((wt - 0.5) / 0.1) ** 2)                     # the toes' bases: a break
    gap = cfg["gap_mm"]
    for k in (1, 2, 3, 4, 5):
        wk = T.toe_weight(groups, k)
        mine = wk > 0.5
        segd = segs[T.TOES[k][0]]
        tip = segd.point(segd.length, 0.0, 0.0)
        pl = M.Plan(q, mine, J[f"toe-{k}-1"], tip)
        s, u, h = pl.local(q)
        if k == 1:
            s_b = pl.station(J["toe-1-2"]) + P.get("crease1_s", 1.0)
        else:
            s_b = pl.station(J[f"toe-{k}-3"]) + P.get("crease2d_s", 0.8)
        s_tip = float(s[mine].max())
        s_c = s_b + 0.52 * (s_tip - s_b)
        umid, half, hlo, hhi = pl.section(np.array([s_c]))
        core = pl.o + s_c * pl.a + float(umid[0]) * pl.b + (float(hlo[0]) + 0.4) * pl.n
        pulp = mine & (s > s_b)
        pad = mine & (s <= s_b)
        kind, side = cfg["pulp"][k]
        dlt = q[pulp] - core
        if kind == "whorl":
            al = dlt @ pl.a
            r = np.sqrt((al / 1.25) ** 2 + np.sum(dlt * dlt, axis=1) - al * al)
            th = np.arctan2(dlt @ pl.b, al)
            phase[pulp] = r + pitch * th / (2.0 * math.pi)
            amp[pulp] *= T.smoothstep(r, *cfg["core_mm"])
        else:
            e = side * pl.b
            tt = np.clip(dlt @ e, 0.0, 20.0)
            r = np.linalg.norm(dlt - np.outer(tt, e), axis=1)
            phase[pulp] = r
            amp[pulp] *= T.smoothstep(r, *cfg["core_mm"])
        far = core - 70.0 * pl.a                                          # the pads: gentle arcs, convex distally
        phase[pad] = np.linalg.norm(q[pad] - far, axis=1)
        amp *= np.where(mine, 1.0 - np.exp(-0.5 * ((s - s_b) / gap) ** 2), 1.0)
    amp *= 1.0 - T.smoothstep(cw, 0.12, 0.5)
    return np.stack([phase, np.ones(len(q)), np.clip(amp, 0.0, 1.0)], 1)


def sheen_mask(q, nrm, groups, P):
    """Hires.Sheen: the forefoot's dorsum (up-facing skin ahead of the midfoot), less on the toes (look.py makes
    it matter: rougher, less coat)."""
    cfg = _cfg(P, "sheen", SHEEN)
    y0, y1 = cfg["forefoot_y"]
    w = T.smoothstep(nrm[:, 2], *cfg["up"]) * T.smoothstep(-q[:, 1], y0, y1)
    wt = T.toes_weight(groups)
    return w * (1.0 - (1.0 - cfg["toes"]) * wt)


def write_masks(ctx, skin, q, groups, cw, P):
    """The materials' masks on the finished skin: Foot.Ridges, Hires.Sheen, Foot.Tendon; the stand-in corn off
    (`corn` 0: a zero group, which lookdev_p01's stand-ins leave alone). Returns a report."""
    me = skin.data
    nrm = C.vertex_normals(q, C.faces(skin))
    segs = T.segments(ctx.joints)
    out = {}
    if P.get("ridges", {}) is not None:
        R = ridge_field(q, nrm, groups, ctx.joints, segs, cw, P)
        att = me.attributes.get("Foot.Ridges")
        if att is not None:
            me.attributes.remove(att)
        me.attributes.new("Foot.Ridges", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", R.astype(np.float32).ravel())
        out["ridges"] = {"amp_mean_sole": round(float(R[q[:, 2] < 3.0, 2].mean()), 3)}
    sh = sheen_mask(q, nrm, groups, P)
    att = me.attributes.get("Hires.Sheen")
    if att is not None:
        me.attributes.remove(att)
    me.attributes.new("Hires.Sheen", "FLOAT", "POINT").data.foreach_set("value", sh.astype(np.float32))
    out["sheen_n"] = int((sh > 0.5).sum())
    tm = getattr(ctx, "tendon_mask", None)
    if tm is not None:
        C.set_group(skin, "Foot.Tendon", TENDONS["mask_share"] * tm)
        out["tendon_n"] = int((tm > 0.2).sum())
    if not P.get("corn", 0):
        C.set_group(skin, "Foot.Corn.L4", np.zeros(len(q)))
        out["corn"] = "off"
    # the callus stand-ins softer (lookdev_p01 paints hard-edged discs, read as stickers from below): the same
    # places, a diffuse, broken falloff (the stand-ins leave a mask that exists alone)
    rng = np.random.default_rng(5)
    ph = rng.uniform(0.0, 6.3, 6)
    for name, c, r in (("Foot.Callus.Ball", (-28.0, -208.0, 0.0), (19.0, 14.0, 8.0)),
                       ("Foot.Callus.MTP5", (50.0, -185.0, 4.0), (12.0, 12.0, 11.0))):
        d = np.sqrt(sum(((q[:, i] - c[i]) / r[i]) ** 2 for i in range(3)))
        brk = 0.75 + 0.25 * np.sin(0.21 * q[:, 0] + ph[0]) * np.sin(0.17 * q[:, 1] + ph[1])
        C.set_group(skin, name, 0.6 * (1.0 - T.smoothstep(d, 0.15, 1.1)) * brk)
    out["callus"] = "soft"
    me.update()
    return out
