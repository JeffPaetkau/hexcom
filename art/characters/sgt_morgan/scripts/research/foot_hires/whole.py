"""Whole foot, passes 1 and 2 (2026-10-13; notes/research_foot_hires.md): the detail the trial's region lacked, for
every toe, applied after the stage (the large forms and the webs), so none of it rebuilds the stage cache.

Pass 2 (critic series foot_whole, round 1) adds, in build order after the stage: the touching lesser toes brought
into contact (toe_contact, in place of the lesser webs' closing, which folded 10,731 face pairs); the midfoot's
plantar vault, the instep's convexity and the navicular tuberosity (arch); the Achilles cord and the retro-malleolar
hollows (achilles); after the tendons, the dorsal veins as raised cords with their tint mask (veins); and the
wear masks the materials read (wear_masks: the heel callus as a feathered rim band, pressure redness, dryness and
the skin tone's regional unevenness).

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
    ("t5m", 0.3, 1.2, 4.2, 3, 0.015, 0.65, -46.0, 109),   # (toe 5's roll: -30 / -38 before shape pass 2)
    ("t5d", 0.7, 0.7, 3.0, 2, 0.010, 0.4, -54.0, 110),
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


# the lesser toes' plantar flexion creases (plan stations from each joint, mm; depth; Gaussian sigma). Pass 2: the PIP
# fold of the curled toes is closed now (macro.close_folds lays its Z on a rounded surface, where round 1's slit drew
# a ruler-straight cut), so the crease is this soft fold, at the old kink (0.2 mm past the joint), 0.28 mm deep and
# about 1.6 mm across, with a fainter second one 1.3 mm proximal (`pip2_*`; toe 2's from crease2p_s)
# (shape pass 2: 0.28 and 0.12 deep before; from below the creases read as rings round banded stalks, round 1's m4)
PLANTAR_LESSER = {"pip_s": 0.2, "pip_d": 0.16, "pip_w": 0.7, "pip2_ds": -1.3, "pip2_d": 0.06, "pip2_w": 0.55,
                  "dip_s": 0.8, "dip_d": 0.07, "dip_w": 0.85}


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
    pc = dict(PLANTAR_LESSER, **(P.get("plantar_lesser") or {}))
    jobs = [((1, "ip"), P.get("crease1_s", 1.0), 0.3, 1.0, -1.5, 8.0, 17 + 3),
            ((2, "pip"), P.get("crease2p_s", 1.5), P.get("crease2p_d", 0.22), P.get("crease2p_w", 0.7), -0.6, 5.0, 17 + 10),
            ((2, "dip"), P.get("crease2d_s", 0.8), 0.2, 0.6, -0.5, 4.5, 17 + 11)]
    # (the first build's 0.12 / 0.16 mm with ends fading over half their span read from below as slots cut in
    # each middle phalanx: shallower, wider, longer)
    for k, hw in ((3, 5.6), (4, 5.3), (5, 5.0)):
        jobs.append(((k, "pip"), pc["pip_s"], pc["pip_d"], pc["pip_w"], -0.5, hw, 40 + k))
        jobs.append(((k, "dip"), pc["dip_s"], pc["dip_d"], pc["dip_w"], -0.4, hw - 0.4, 50 + k))
    # pass 2: the PIP creases doubled, the second fainter and a little proximal (round 1's m7: "often doubled")
    for k, hw in ((2, 5.0), (3, 5.2), (4, 4.9), (5, 4.6)):
        s2 = (P.get("crease2p_s", 1.5) if k == 2 else pc["pip_s"]) + pc["pip2_ds"]
        jobs.append(((k, "pip"), s2, pc["pip2_d"], pc["pip2_w"], -0.4, hw, 60 + k))
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
    # the toes' bases: a break. Pass 2 (round 1's m12, m28: thin brown stair-stepped arcs over the toes' plantar bases):
    # the phase jumps from the sole's arcs to a pad's where that toe's own weight crosses 0.5 (`mine` below), but the
    # break was on the sum of the toes' weights, which at the plantar bases a neighbour's weight lifts well past 0.5
    # there, so the faces straddling the jump kept their amplitude while the interpolated phase swept through dozens
    # of ridges inside them: a dark line along the faces. Now each toe's own weight, nothing within 0.06 of the jump
    gap = cfg["gap_mm"]
    for k in (1, 2, 3, 4, 5):
        wk = T.toe_weight(groups, k)
        amp *= smoother(np.abs(wk - 0.5), 0.06, 0.22)
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
    # pass 2: the heel callus as a feathered rim band (the stand-in was a cap over the whole heel ending in a straight
    # line across it, round 1's m4), the veins' tint (Foot.Vein), and the wear and tone of Hires.Wear
    if P.get("wear", {}) is not None:
        heel, wear = wear_masks(ctx, q, nrm, groups, segs, P, out)
        C.set_group(skin, "Foot.Callus.Heel", heel)
        att = me.attributes.get("Hires.Wear")
        if att is not None:
            me.attributes.remove(att)
        me.attributes.new("Hires.Wear", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", wear.astype(np.float32).ravel())
    vm = getattr(ctx, "vein_mask", None)
    if vm is not None:
        C.set_group(skin, "Foot.Vein", vm)
        out["vein_n"] = int((vm > 0.2).sum())
    me.update()
    return out


# --------------------------------------------------------------------------- pass 2 (2026-10-13): shared helpers

def smoother(x, a, b):
    """Perlin's smootherstep: 0 below a, 1 above b, its first and second derivatives 0 at both ends (a large move
    shaped by smoothstep shows its curvature steps as lines in clay)."""
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


def smoother_window(x, a0, a1, b1, b0):
    """0 outside [a0, b0], 1 inside [a1, b1], smootherstep between."""
    return smoother(x, a0, a1) * (1.0 - smoother(x, b1, b0))


def wave_noise(p, scale_mm, seed, n=8):
    """A smooth, irregular field (standard deviation about 1) of n plane waves in random directions with
    wavelengths of 0.6-1.6 x scale_mm: seeded, smooth at any resolution, cheap on a million vertices."""
    rng = np.random.default_rng(seed)
    out = np.zeros(len(p))
    for _ in range(n):
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        out += np.sin(np.asarray(p, float) @ d * (2.0 * math.pi / (scale_mm * rng.uniform(0.6, 1.6)))
                      + rng.uniform(0.0, 2.0 * math.pi))
    return out / math.sqrt(0.5 * n)


def blob_noise(p, sigma_mm, seed, count=400):
    """A smooth, isotropic field (standard deviation about 1): Gaussian blobs of random sign and size (0.7-1.3 sigma)
    at random places over the points' bounding box. A sum of a few plane waves reads as stripes over a large surface
    (pass 2's first broad tone drew pale bands across the shin)."""
    p = np.asarray(p, float)
    rng = np.random.default_rng(seed)
    lo, hi = p.min(axis=0) - sigma_mm, p.max(axis=0) + sigma_mm
    out = np.zeros(len(p))
    for _ in range(count):
        c = lo + rng.random(3) * (hi - lo)
        s = sigma_mm * rng.uniform(0.7, 1.3)
        sgn = 1.0 if rng.random() < 0.5 else -1.0
        near = np.nonzero(np.all(np.abs(p - c) < 3.0 * s, axis=1))[0]
        if len(near):
            out[near] += sgn * np.exp(-0.5 * np.sum((p[near] - c) ** 2, axis=1) / (s * s))
    return out / max(float(out.std()), 1e-9)


def line_noise(t, seed, lams=(23.0, 9.5)):
    """A slow wobble along a curve's arc length t (mm), about -1..1."""
    ph = np.random.default_rng(seed).uniform(0.0, 2.0 * math.pi, len(lams))
    w = [0.6, 0.4, 0.3][:len(lams)]
    return sum(wi * np.sin(2.0 * math.pi * np.asarray(t, float) / L + p) for wi, L, p in zip(w, lams, ph))


def _rings(adj, zone, n):
    """A 0/1 zone grown by n rings of the mesh."""
    ptr, nb = adj
    deg = np.diff(ptr)
    row = np.repeat(np.arange(len(deg)), deg)
    for _ in range(n):
        zone = np.maximum(zone, (np.bincount(row, zone[nb], minlength=len(deg)) > 0).astype(float))
    return zone


def _kdtree(pts):
    from mathutils.kdtree import KDTree
    kd = KDTree(len(pts))
    for i, p in enumerate(pts):
        kd.insert(p, i)
    kd.balance()
    return kd


def _nearest(kd, pts):
    """Each point's nearest index in a KDTree and the distance."""
    idx = np.empty(len(pts), np.int64)
    dist = np.empty(len(pts))
    for i, p in enumerate(pts):
        _, j, d = kd.find(p)
        idx[i], dist[i] = j, d
    return idx, dist


# --------------------------------------------------------------------------- pass 2: the touching toes

# Round 1's m7 and the folded faces: the lesser webs' closing (method_fields.webs_lesser) filled the slit between
# touching toes and crumpled both walls onto the filled surface (10,731 folded pairs; the dark seams along the
# touching sides and the hairline cut across toes 3 and 4 where its mask began). Instead each facing wall moves
# toward its neighbour by half the gap less `gap`, fully where the gap is under `full` mm, fading out by `reach`, so
# the walls meet where the toes touch and part in a soft V where they don't: the new gap is a monotone function of
# the old, so nothing folds. Along the other wall's normal at the nearest vertex (the signed gap, so a slight overlap
# is pushed apart too), the displacement smoothed over `smooth` Laplacian passes (nearest-vertex normals jitter at
# the vertices' scale), each toe's own skin only (weights over `own`: the commissures stay part 01's)
# (shape pass 2: closed fully under 1.0 mm and fading by 2.4, was 0.35 and 1.4; round 1's m2, m14, m15: see-through
# gaps along the lesser toes in plan)
CONTACT = {"pairs": [[2, 3], [3, 4], [4, 5]], "gap": 0.05, "full": 1.0, "reach": 2.4, "own": [0.55, 0.85],
           "smooth": 8}


def toe_contact(q, nrm, groups, adj, P, report=None):
    """The touching lesser toes brought into contact (CONTACT). Returns positions."""
    import macro as M
    cfg = _cfg(P, "contact", CONTACT)
    if not cfg.get("pairs"):
        return q
    g0, full, reach = cfg["gap"], cfg["full"], cfg["reach"]
    o0, o1 = cfg["own"]
    d = np.zeros_like(q)
    rep = {}
    for ka, kb in cfg["pairs"]:
        wa, wb = T.toe_weight(groups, ka), T.toe_weight(groups, kb)
        A, B = np.nonzero(wa > o0)[0], np.nonzero(wb > o0)[0]
        stats = []
        for src, dst, wsrc in ((A, B, wa), (B, A, wb)):
            lo, hi = q[dst].min(axis=0) - reach, q[dst].max(axis=0) + reach
            cand = src[np.all((q[src] > lo) & (q[src] < hi), axis=1)]
            if not len(cand):
                continue
            j, dist = _nearest(_kdtree(q[dst]), q[cand])
            keep = dist < reach + 0.6
            cand, near = cand[keep], dst[j[keep]]
            nb = nrm[near]
            s = np.einsum("ij,ij->i", q[cand] - q[near], nb)
            w = (1.0 - T.smoothstep(s, full, reach)) * T.smoothstep(wsrc[cand], o0, o1)
            d[cand] += (-0.5 * (s - g0) * w)[:, None] * nb
            touch = w > 0.5
            stats.append({"n": int((w > 0.05).sum()), "gap_min": round(float(s[touch].min()), 3) if touch.any() else None})
        rep[f"{ka}-{kb}"] = stats
    zone = _rings(adj, (np.abs(d).sum(axis=1) > 1e-6).astype(float), 3)
    d = M.taubin(d, adj, 0.9 * zone, iterations=int(cfg["smooth"]), lam=0.5, mu=0.0)
    if report is not None:
        ln = np.linalg.norm(d, axis=1)
        report["contact"] = {"pairs": rep, "moved_n": int((ln > 0.01).sum()), "moved_max": round(float(ln.max()), 3)}
    return q + d


# --------------------------------------------------------------------------- pass 2: the arch and the instep

# Round 1's m5 (all three critics): from the medial side the foot read flat, the border a few millimetres over the
# floor from heel to ball, the instep a straight ramp. Sliced, the midfoot's underside was a flat shelf 8-10 mm up
# from x -20 to +5 (so from V2's camera the visible bottom was that shelf's edge, about 5 mm up, and the sole's paler
# skin filled the recess), the lateral column 5-6 mm off the floor, and the dorsum a straight line from y -140 to
# -200 with a concave corner where the ankle's front met it. Spec 01 §3.1's figures: medial clearance 13 at 45 % L,
# lateral border 4 at 50 % L, navicular 42, dorsum 66 / 56 / 40 at 50 / 60 / 70 % L.
#  * the vault: the underside of the medial two thirds raised (`mid` mm, eased under the medial border so its
#    clearance stays in the spec's range), the lateral column lowered toward the floor (`lat`, never nearer than
#    `floor_gap`), as a vertical move over plan (x, y) by the share of the foot's breadth (0 lateral, 1 medial),
#    enveloped between the heel's and the ball's contact (`y`), fading with height (`height` mm above the floor),
#    so the dorsum stays and nothing folds (a vertical move whose rate of change with height is under 1);
#  * the instep: the dorsum raised along a bell over y (`instep`), so the profile curves over the midfoot;
#  * the navicular tuberosity: a 2 mm dome on the medial wall (spec 01 §3.2: (-40, -120, 42), 12 mm).
ARCH = {
    # (the first build's 3.2 mm under a flat shelf lifted the medial view's bottom edge only 3 mm: the vault now rises
    # 7 mm over the middle of the breadth and eases to a tenth of that under the medial border, so the underside is a
    # concave vault whose apex lies inside the border, seen from the medial side as a shadowed recess under the lit
    # wall, while the border's clearance stays near spec 01's 13 mm. Every profile is a smootherstep, C2: a sin^0.8
    # envelope creased the sole straight across at its onset, and plain smoothsteps' curvature steps drew faint lines
    # along the sole in clay. `y` is the envelope's (heel's contact, plateau, plateau, ball's contact))
    # (shape pass 2, round 1's m8 and m31: the vault rose 7 mm over the middle of the breadth and eased back to nothing
    # under the medial border, which from below read as one long central trough with a hard rim from heel to ball. It
    # now rises toward the medial border, eased to a quarter of itself only at the border's last fifth, and lower (the
    # medial clearance at 45 % L read 17 at 4.5 mm). A steeper rise beside the band (s 0.22-0.55) and a 20 mm heel
    # end drew a sharp-edged rectangular pocket in clay; the lateral column's drop stops short of the heel (lat_y), as
    # under part 01's tapered heel it creased the lateral heel wall at y -60)
    # (the scan-driven pass, 2026-10-16: part 01's sole is now fitted to three real men's plantar sections
    # (parts/p01/scanfit.py), the lateral band on the floor and the medial vault where theirs are, so the vault's rise
    # and the lateral drop here are off; 3.5 and 2.2 before)
    "y": [-190.0, -160.0, -86.0, -58.0],
    "mid": 0.0, "mid_s": [0.25, 0.8], "edge_ease": [0.8, 1.0, 0.75],
    "lat": 0.0, "lat_s": [0.18, 0.52], "lat_y": [-170.0, -130.0, -95.0, -75.0],
    "floor_gap": 0.8, "height": [18.0, 40.0],
    # (r 9, amp 2: a knob stuck on, in clay; 1.5 pushed the medial extreme out and with it spec 01's clearance window)
    "navicular": {"y": -120.0, "z": 42.0, "r": 14.0, "amp": 1.2},
    # the shape pass (2026-10-14; round 2's m3, all three critics: no 5th metatarsal styloid): part 01 now draws the
    # lateral border straight from the heel to the 5th head and puts a 4.5 mm bump on its 5 mm cage at the styloid,
    # which the cage's subdivision rounds into a swelling; here the dense skin gets the knob itself, spec 01 §3.2's
    # (+50, -150, 18), 8 mm across and 2.5 mm proud, on the border's lateral extreme at that station; drawn out
    # along the border (`r` across, `ry` along: a round dome, r 9, read in clay as a knob stuck on), where the 5th
    # metatarsal's base flares and the peroneus brevis runs into it
    "styloid": {"y": -150.0, "z": 17.0, "r": 9.0, "ry": 16.0, "amp": 1.8},
    "instep": {"y": -158.0, "half": 40.0, "amp": 2.5, "up": [0.3, 0.75]},
}


def arch(q, nrm, P, report=None):
    """The midfoot's vault, the instep and the navicular (ARCH). Returns positions."""
    import macro as M
    import detail as Dt
    cfg = _cfg(P, "arch", ARCH)
    floor = float(q[:, 2].min())
    zr = q[:, 2] - floor
    ya, yb, yc, yd = cfg["y"]
    y0, y1 = yd, ya
    h0, h1 = cfg["height"]
    out = q.copy()
    rep = {}
    sel = np.nonzero((q[:, 1] < y0 + 2.0) & (q[:, 1] > y1 - 2.0) & (zr < h1 + 1.0))[0]
    if len(sel) and (cfg["mid"] or cfg["lat"]):
        p = q[sel]
        # the low foot's breadth per 1 mm row: its lateral and medial extremes under 25 mm, smoothed over 9 mm
        rows = np.arange(np.floor(y1) - 8.0, np.ceil(y0) + 9.0, 1.0)
        low = q[(zr < 25.0) & (q[:, 1] > rows[0]) & (q[:, 1] < rows[-1])]
        iy = np.clip(np.round(low[:, 1] - rows[0]).astype(int), 0, len(rows) - 1)
        xmin, xmax = np.full(len(rows), np.inf), np.full(len(rows), -np.inf)
        np.minimum.at(xmin, iy, low[:, 0])
        np.maximum.at(xmax, iy, low[:, 0])
        k = np.ones(9) / 9.0
        xmin = np.convolve(np.pad(xmin, 4, mode="edge"), k, mode="valid")
        xmax = np.convolve(np.pad(xmax, 4, mode="edge"), k, mode="valid")
        xm, xM = np.interp(p[:, 1], rows, xmin), np.interp(p[:, 1], rows, xmax)
        s = np.clip((xM - p[:, 0]) / np.maximum(xM - xm, 10.0), 0.0, 1.0)
        env = smoother_window(p[:, 1], ya, yb, yc, yd)
        a, b = cfg["mid_s"]
        e0, e1, ek = cfg["edge_ease"]
        rise = cfg["mid"] * env * smoother(s, a, b) * (1.0 - ek * smoother(s, e0, e1))
        la, lb = cfg["lat_s"]
        drop = cfg["lat"] * smoother_window(p[:, 1], *cfg["lat_y"]) * (1.0 - smoother(s, la, lb))
        # never nearer the floor than floor_gap: each column's bottom from a 1 mm plan map of the lowest skin, and the
        # drop eased to smoothstep(room / 2 drop) of itself, which never takes more than the room and is 0 with it
        x0g, y0g = np.floor(p[:, 0].min()) - 1.0, np.floor(p[:, 1].min()) - 1.0
        nx, ny = int(np.ceil(p[:, 0].max() - x0g)) + 3, int(np.ceil(p[:, 1].max() - y0g)) + 3
        ix, jy = (p[:, 0] - x0g).astype(int), (p[:, 1] - y0g).astype(int)
        Zb = np.full((nx, ny), np.inf)
        np.minimum.at(Zb, (ix, jy), zr[sel])
        Zb[~np.isfinite(Zb)] = np.nan
        Zb = Dt._blur2d(Dt._fill(Zb), 1.5)
        Zb = Dt._fill(Zb)
        # bilinear, cell centres at +0.5 (read by nearest cell the limit stepped every millimetre: a hatched patch on
        # the lateral border in clay where the floor held the drop back)
        fx, fy = p[:, 0] - x0g - 0.5, p[:, 1] - y0g - 0.5
        i0 = np.clip(np.floor(fx).astype(int), 0, nx - 2)
        j0 = np.clip(np.floor(fy).astype(int), 0, ny - 2)
        ax, ay = np.clip(fx - i0, 0.0, 1.0), np.clip(fy - j0, 0.0, 1.0)
        zb = (Zb[i0, j0] * (1 - ax) * (1 - ay) + Zb[i0 + 1, j0] * ax * (1 - ay) + Zb[i0, j0 + 1] * (1 - ax) * ay
              + Zb[i0 + 1, j0 + 1] * ax * ay)
        room = np.maximum(zb - cfg["floor_gap"], 0.0)
        drop = drop * T.smoothstep(room / np.maximum(2.0 * drop, 1e-6), 0.0, 1.0)
        delta = rise - drop
        dz = delta * (1.0 - smoother(zr[sel], h0, h1))
        out[sel, 2] += dz
        rep["vault"] = {"rise_max": round(float(rise.max()), 2), "drop_max": round(float(drop.max()), 2),
                        "dz_range": [round(float(dz.min()), 2), round(float(dz.max()), 2)]}
    nav = cfg.get("navicular")
    if nav and nav.get("amp"):
        c = M.medial_point(out, nav["y"], floor + nav["z"], window_mm=2.0)
        out = out + (nav["amp"] * M.sphere(out, c, nav["r"]))[:, None] * nrm
        rep["navicular"] = np.round(c, 1).tolist()
    sty = cfg.get("styloid")
    if sty and sty.get("amp"):
        near = (np.abs(out[:, 1] - sty["y"]) < 2.0) & (np.abs(out[:, 2] - (floor + sty["z"])) < 2.0)
        c = out[near][np.argmax(out[near][:, 0])]
        d = (out - c) / np.array([sty["r"], sty.get("ry", sty["r"]), sty["r"]])
        win = np.clip(1.0 - np.sum(d * d, axis=1), 0.0, 1.0) ** 3
        out = out + (sty["amp"] * win)[:, None] * nrm
        rep["styloid"] = np.round(c, 1).tolist()
    ins = cfg.get("instep")
    if ins and ins.get("amp"):
        by = np.clip(1.0 - ((out[:, 1] - ins["y"]) / ins["half"]) ** 2, 0.0, 1.0) ** 2
        out[:, 2] += ins["amp"] * by * T.smoothstep(nrm[:, 2], *ins["up"]) * T.smoothstep(zr, 25.0, 35.0)
    if report is not None:
        rep["figures"] = {"before": arch_figures(q), "after": arch_figures(out)}
        report["arch"] = rep
    return out


def arch_figures(q, L=282.0):
    """Spec 01 §3.1's arch figures on a skin (F, mm above the floor): the medial clearance at 45 % L (the lowest skin
    within 12 mm of the medial extreme), the lateral border at 50 % L (the lowest skin in the section's lateral
    third), the dorsum's height at 50, 60 and 70 % L, and the medial border's clearance along the arch every 10 mm."""
    floor = float(q[:, 2].min())

    def row(y):
        return q[(np.abs(q[:, 1] - y) < 0.5) & (q[:, 2] - floor < 110.0)]

    def medial(y):
        c = row(y)
        return round(float(c[c[:, 0] < c[:, 0].min() + 12.0, 2].min() - floor), 1)

    c = row(-0.5 * L)
    lat = c[c[:, 0] > c[:, 0].max() - (c[:, 0].max() - c[:, 0].min()) / 3.0]
    return {"medial_45": medial(-0.45 * L), "lateral_50": round(float(lat[:, 2].min() - floor), 1),
            "dorsum_50_60_70": [round(float(row(-f * L)[:, 2].max() - floor), 1) for f in (0.5, 0.6, 0.7)],
            "medial_border": {int(y): medial(y) for y in range(-50, -200, -10)}}


# --------------------------------------------------------------------------- pass 2: the Achilles

# Round 1's m2 (blocking for C2): from behind the back of the ankle was a smooth column, a faint ridge on a convex
# arc (sliced: within 12 mm of the midline it falls away like a 10 mm radius, then steadily, with no concavity
# anywhere). Spec 01 §3.2: the Achilles a cord 16 wide x 7 proud at z 100, the retro-malleolar hollows 4 deep either
# side. A horizontal move along the skin's horizontal normal on the back of the ankle (`back`: the normal's backward
# share), by the offset across from the tendon's line x0: the cord raised (`cord`: (1 - (dx / half)^2)^2, about
# 0.54 half at half height, its insertion fading at z 50-62 into the heel) and a hollow either side sunk (`hollow`: a
# Gaussian at |dx| = `at`), so the cord's flanks become concave, which is what reads as a cord from behind
ACHILLES = {
    # (the first build's hollows, sigma 3.4 at 14 mm and starting over 14 mm of height, read in clay as two narrow
    # tram-line grooves standing on a ledge: broader, a little shallower, fading in over 26 mm)
    "x0": -2.0, "behind": -62.0, "back": [0.0, 0.4],
    "cord": {"amp": 1.4, "half": 11.5, "z": [42.0, 66.0, 150.0, 240.0]},
    # (the scan-driven pass, 2026-10-16: three real heels stay 33-41 wide 20 mm in front of the pternion at z 60, ours
    # 26: the hollows start higher, above the calcaneus, so the heel's upper part is a bell's shoulder, not a neck;
    # z [44, 70, ...] before)
    "hollow": {"amp": 3.2, "at": 15.5, "sigma": 5.0, "z": [54.0, 78.0, 112.0, 175.0]},
}


def achilles(q, nrm, P, report=None):
    """The Achilles cord and the hollows beside it (ACHILLES). Returns positions."""
    cfg = _cfg(P, "achilles", ACHILLES)
    floor = float(q[:, 2].min())
    zr = q[:, 2] - floor
    Cc, H = cfg["cord"], cfg["hollow"]
    z_lo = min(Cc["z"][0], H["z"][0]) - 1.0
    z_hi = max(Cc["z"][3], H["z"][3]) + 1.0
    sel = np.nonzero((q[:, 1] > cfg["behind"]) & (zr > z_lo) & (zr < z_hi))[0]
    out = q.copy()
    if not len(sel):
        return out
    n = nrm[sel].copy()
    n[:, 2] = 0.0
    ln = np.linalg.norm(n, axis=1)
    n /= np.maximum(ln, 1e-9)[:, None]
    back = T.smoothstep(n[:, 1], *cfg["back"]) * T.smoothstep(ln, 0.3, 0.6)
    dx = q[sel, 0] - cfg["x0"]
    z = zr[sel]
    cord = np.clip(1.0 - (dx / Cc["half"]) ** 2, 0.0, 1.0) ** 2 * smoother_window(z, *Cc["z"])
    hol = np.exp(-0.5 * ((np.abs(dx) - H["at"]) / H["sigma"]) ** 2) * smoother_window(z, *H["z"])
    d = (Cc["amp"] * cord - H["amp"] * hol) * back
    out[sel] += d[:, None] * n
    if report is not None:
        report["achilles"] = {"cord_max": round(float(d.max()), 2), "hollow_max": round(float(-d.min()), 2),
                              "moved_n": int((np.abs(d) > 0.05).sum())}
    return out


def forms(ctx, q, topo, groups, segs, P):
    """Pass 2's large forms after the stage, in order: the lesser toes' waists filled (shape pass 2), the toes'
    contact, the arch, the Achilles, the sole's landscape and the ankle crease (shape pass 2). Returns positions."""
    import macro as M
    edges, _ = C.edge_lengths(ctx.skin)
    adj = M.adjacency(edges, len(q))
    q = toe_fill(q, groups, segs, ctx.joints, P, ctx.report)
    q = toe_contact(q, C.vertex_normals(q, topo), groups, adj, P, ctx.report)
    q = arch(q, C.vertex_normals(q, topo), P, ctx.report)
    q = achilles(q, C.vertex_normals(q, topo), P, ctx.report)
    q = sole(q, C.vertex_normals(q, topo), groups, segs, ctx.joints, P, adj, ctx.report)
    q = scan_sole(q, C.vertex_normals(q, topo), topo, groups, P, ctx.report)
    q = ankle_crease(q, C.vertex_normals(q, topo), P, ctx.report)
    return q


# The scan-driven pass (2026-10-16; notes/research_foot_hires.md): what part 01's fitted sole (parts/p01/scanfit.py,
# its 2 mm cells read at 12 stations x 8 shares of the breadth) leaves of the three men's mean underside is taken off
# here, on the dense skin: the same measure on this skin in the scans' frame (the heel's centre to toe 2's tip), each
# sample's difference spread to the plantar skin by a normalised Gaussian (`sigma` mm across, along), a share `k` of
# it, faded at the grid's edge, off the toes, above `height` and on skin not facing down; never nearer the floor than
# `floor`. (Part 01's cage carries the large forms; this closes the 1-2 mm it cannot: the lateral band's gap behind
# the 5th metatarsal's base, the ball's crescent across the middle heads.)
SCAN_SOLE = {"k": 0.85, "sigma": [7.0, 9.0], "height": [6.0, 16.0], "plantar": [0.3, 0.7], "floor": 0.15,
             "edge": [0.25, 0.6], "max": 4.0}


def scan_sole(q, nrm, topo, groups, P, report=None):
    """The sole's remaining difference from the scans' mean (SCAN_SOLE). Returns positions."""
    cfg = _cfg(P, "scan_sole", SCAN_SOLE)
    if not cfg.get("k"):
        return q
    import os
    import sys
    scripts = os.path.dirname(os.path.dirname(C.HERE))
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from parts.p01 import scanfit as SF
    tg = SF.load_targets()
    if tg is None:
        return q
    w2 = T.toe_weight(groups, 2) > 0.5
    t2 = q[w2]
    tip = t2[np.argmin(t2[:, 1])]
    Tr = SF.triangles(*topo)
    qs, (R, o) = SF.rezero(q, tip)
    meas = SF.measures(qs, Tr, pts=qs)
    # the samples: (x, y) in the scans' frame and ours - target there
    px, py, d = [], [], []
    under = qs[qs[:, 2] < SF.PLAN_Z]
    for p in SF.SOLE_PCTS:
        y = -p / 100.0 * SF.LENGTH
        b = under[np.abs(under[:, 1] - y) < 0.75]
        if len(b) < 4:
            continue
        a, bb = b[:, 0].min(), b[:, 0].max()
        for u, z in zip(SF.SOLE_U, meas["sole"][str(p)]):
            t = tg["values"].get(f"sole_{p}_{int(round(u * 100)):02d}")
            if z is None or t is None:
                continue
            px.append(a + u * (bb - a))
            py.append(y)
            d.append(z - t)
    px, py, d = np.array(px), np.array(py), np.clip(np.array(d), -cfg["max"], cfg["max"])
    floor = float(q[:, 2].min())
    zr = q[:, 2] - floor
    sel = np.nonzero((zr < cfg["height"][1]) & (nrm[:, 2] < -0.1))[0]
    out = q.copy()
    if not len(sel) or not len(d):
        return out
    sx, sy = cfg["sigma"]
    X, Y = qs[sel, 0][:, None], qs[sel, 1][:, None]
    G = np.exp(-0.5 * (((X - px[None, :]) / sx) ** 2 + ((Y - py[None, :]) / sy) ** 2))
    wsum = G.sum(1)
    corr = (G @ d) / np.maximum(wsum, 1e-9)
    w = (T.smoothstep(wsum, *cfg["edge"]) * T.smoothstep(-nrm[sel, 2], *cfg["plantar"])
         * (1.0 - T.smoothstep(zr[sel], *cfg["height"])) * (1.0 - T.toes_weight(groups)[sel]))
    z0 = q[sel, 2]
    dk = cfg["k"] * corr * w
    # lowering saturates smoothly at the room left above the floor's margin, room (1 - exp(-d / room)), the room itself
    # a softplus: a hard clamp drew rings round the heel pad's contact and blobs on the ball in clay (the first build)
    kk = 0.3
    room = kk * np.logaddexp(0.0, (z0 - floor - cfg["floor"]) / kk)
    down = np.where(dk > 0.0, room * (1.0 - np.exp(-np.maximum(dk, 0.0) / np.maximum(room, 1e-6))), dk)
    out[sel, 2] = z0 - down
    if report is not None:
        moved = out[sel, 2] - q[sel, 2]
        report["scan_sole"] = {"samples": int(len(d)), "diff_rms": round(float(np.sqrt(np.mean(d ** 2))), 2),
                               "moved": [round(float(moved.min()), 2), round(float(moved.max()), 2)],
                               "n": int((np.abs(moved) > 0.05).sum())}
    return out


# --------------------------------------------------------------------------- shape pass 2 (2026-10-15)

# Critic series foot_shape, round 1 (notes/critic/foot_shape_r1/tally.md): the lesser toes read as slender, waisted,
# knobbly fingers standing apart (m2, m14-m16). Each lesser toe's plan outline is filled out side by side to the
# widest section distal of each station (in the toe's plan frame, macro.Plan: stations are vertical planes from the
# MTP joint toward the tip), so no section is narrower than one nearer the tip and the toe is broadest at its base;
# each side moves by its own shortfall (capped at `max`), over the side's share of the section (`side`), from `base`
# mm past the MTP to `end` mm short of the tip, never nearer another toe than `gap` (half the room: both neighbours
# fill). Then toe_contact (CONTACT, reach widened) brings the facing walls together along the toes' length.
# (toe 5 at half: its free lateral side, filled fully, swelled into a lump)
TOE_FILL = {"toes": [2, 3, 4, 5], "share": 1.0, "share_toe": {"5": 0.45}, "max": 2.2, "gap": 0.08, "side": [0.25, 0.9],
            "base": [2.0, 7.0], "end": [6.0, 3.0]}


def toe_fill(q, groups, segs, J, P, report=None):
    """The lesser toes' waists filled (TOE_FILL). Returns positions."""
    cfg = _cfg(P, "toe_fill", TOE_FILL)
    if not cfg.get("share"):
        return q
    out = q.copy()
    rep = {}
    every = T.toes_weight(groups)
    for k in cfg["toes"]:
        wk = T.toe_weight(groups, k)
        mine = wk > 0.5
        seg = segs[f"t{k}d"]
        pl = M.Plan(q, mine, J[f"toe-{k}-1"], seg.point(seg.length, 0.0, 0.0))
        s, u, h = pl.local(q)
        sm, um = s[mine], u[mine]
        st = np.arange(np.floor(sm.min()), np.ceil(sm.max()) + 1.0, 1.0)
        i = np.clip(np.round(sm - st[0]).astype(int), 0, len(st) - 1)
        lo, hi = np.full(len(st), np.inf), np.full(len(st), -np.inf)
        np.minimum.at(lo, i, um)
        np.maximum.at(hi, i, um)
        ok = np.bincount(i, minlength=len(st)) >= 8
        k5 = np.ones(5) / 5.0
        lo = np.convolve(np.pad(np.interp(st, st[ok], lo[ok]), 2, mode="edge"), k5, mode="valid")
        hi = np.convolve(np.pad(np.interp(st, st[ok], hi[ok]), 2, mode="edge"), k5, mode="valid")
        need_hi = np.maximum.accumulate(hi[::-1])[::-1] - hi
        need_lo = lo - np.minimum.accumulate(lo[::-1])[::-1]
        need_hi = np.minimum(np.convolve(np.pad(need_hi, 2, mode="edge"), k5, mode="valid"), cfg["max"])
        need_lo = np.minimum(np.convolve(np.pad(need_lo, 2, mode="edge"), k5, mode="valid"), cfg["max"])
        s_tip = float(sm.max())
        mid = np.interp(s, st, 0.5 * (lo + hi))
        half = np.maximum(np.interp(s, st, 0.5 * (hi - lo)), 1.0)
        rel = (u - mid) / half
        a0, a1 = cfg["side"]
        b0, b1 = cfg["base"]
        e0, e1 = cfg["end"]
        along = T.smoothstep(s, b0, b1) * (1.0 - T.smoothstep(s, s_tip - e0, s_tip - e1))
        fade = T.smoothstep(wk, 0.3, 0.8)
        share = float((cfg.get("share_toe") or {}).get(str(k), cfg["share"]))
        d = share * along * fade * (np.interp(s, st, need_hi) * T.smoothstep(rel, a0, a1)
                                           - np.interp(s, st, need_lo) * T.smoothstep(-rel, a0, a1))
        grow = np.abs(d) > 1e-3
        if grow.any():
            lo3, hi3 = q[grow].min(axis=0) - 5.0, q[grow].max(axis=0) + 5.0
            near = np.all((q > lo3) & (q < hi3), axis=1) & (wk < 0.05) & (every > 0.3)
            r = 0.5 * M.room(q, grow, near, cfg["gap"])
            kk = 0.08
            mag = np.abs(d[grow])
            lim = np.clip(-kk * np.logaddexp(-mag / kk, -r[grow] / kk), 0.0, None)
            d[grow] = np.sign(d[grow]) * lim
        out += d[:, None] * pl.b[None, :]
        rep[str(k)] = {"need_max": round(float(max(need_hi.max(), need_lo.max())), 2),
                       "moved_max": round(float(np.abs(d).max()), 2)}
    if report is not None:
        report["toe_fill"] = rep
    return out


# The sole (round 1's m4, m8, m31: a blank slab with a central trough, the toes banded stalks from below). The arch's
# vault now rises toward the medial border instead of easing back to the floor under it (ARCH below, the trough's
# cause), and here: the toe sulcus, a soft groove across the plantar toe bases `ahead` mm in front of the MTP joints,
# parting the ball's cushion from the toes; the ball's back edge, a broad shallow groove `behind` mm behind the MTP
# joints' line, fading out over the lateral band (`lat_x`), so the ball reads as a transverse cushion; each lesser
# toe's plantar skin faired (`fair`: Taubin passes, the curled toes' closed folds stood as hard ring bands from below)
# and its proximal pad filled out below its phalanx (`pads`: along the plantar normal, a Gaussian along the proximal
# segment), so the toes read as a row of plump pads.
# (the scan-driven pass, 2026-10-16: three men's lesser toes rise 5.6-8 mm from the pad to the sulcus, ours 2-3; the
# groove deeper and broader, 1.0 mm and sigma 1.9 before; 1.6 and 2.8 folded toe 4 at its base)
SOLE = {
    "sulcus": {"depth": 1.3, "sigma": 2.4, "ahead": 11.0, "pad_x": 8.0, "below": 16.0, "plantar": [0.15, 0.55]},
    "ball_back": {"depth": 0.7, "sigma": 5.0, "behind": 26.0, "below": 14.0, "lat_x": [34.0, 52.0], "plantar": [0.3, 0.7]},
    "fair": {"iterations": 40, "plantar": [0.1, 0.5], "toes": [2, 3, 4, 5]},
    "pads": {"amp": 0.7, "at": 0.55, "sigma": 0.28, "plantar": [0.2, 0.6], "toes": [2, 3, 4, 5]},
}


def sole(q, nrm, groups, segs, J, P, adj=None, report=None):
    """The sole's landscape (SOLE). Returns positions."""
    cfg = _cfg(P, "sole", SOLE)
    out = q.copy()
    fr = cfg.get("fair") or {}
    if fr.get("iterations") and adj is not None:
        w = np.clip(sum(T.toe_weight(groups, k) for k in fr["toes"]), 0.0, 1.0) * T.smoothstep(-nrm[:, 2], *fr["plantar"])
        out = M.taubin(out, adj, 0.9 * w, iterations=int(fr["iterations"]))
        rep_fair = int((w > 0.05).sum())
    else:
        rep_fair = 0
    rep = {}
    floor = float(q[:, 2].min())
    sc = cfg.get("sulcus") or {}
    if sc.get("depth"):
        pts = []
        for k in (1, 2, 3, 4, 5):
            m = np.asarray(J[f"toe-{k}-1"], float)
            seg = segs["h1"] if k == 1 else segs[f"t{k}p"]
            a = np.array([seg.a[0], seg.a[1], 0.0])
            a /= np.linalg.norm(a)
            pts.append(m + sc["ahead"] * a)
        pts = sorted(pts, key=lambda p: p[0])
        ext = sc.get("pad_x", 8.0)
        d01 = (pts[1] - pts[0]) / np.linalg.norm(pts[1] - pts[0])
        d43 = (pts[-1] - pts[-2]) / np.linalg.norm(pts[-1] - pts[-2])
        line = [pts[0] - ext * d01] + pts + [pts[-1] + ext * d43]
        dist, _ = polyline_plan(q, catmull_rom(line, n=12))
        plantar = T.smoothstep(-nrm[:, 2], *sc["plantar"]) * (1.0 - T.smoothstep(q[:, 2] - floor, sc["below"] - 4.0,
                                                                                 sc["below"]))
        g = sc["depth"] * np.exp(-0.5 * (dist / sc["sigma"]) ** 2) * plantar
        out -= g[:, None] * nrm
        rep["sulcus"] = {"line": [np.round(p[:2], 1).tolist() for p in pts], "max": round(float(g.max()), 2)}
    bb = cfg.get("ball_back") or {}
    if bb.get("depth"):
        heads = sorted((np.asarray(J[f"toe-{k}-1"], float) for k in (1, 2, 3, 4, 5)), key=lambda p: p[0])
        line = [h + np.array([0.0, bb["behind"], 0.0]) for h in heads]
        d01 = (line[1] - line[0]) / np.linalg.norm(line[1] - line[0])
        d43 = (line[-1] - line[-2]) / np.linalg.norm(line[-1] - line[-2])
        line = [line[0] - 20.0 * d01] + line + [line[-1] + 20.0 * d43]
        dist, _ = polyline_plan(q, catmull_rom(line, n=12))
        plantar = T.smoothstep(-nrm[:, 2], *bb["plantar"]) * (1.0 - T.smoothstep(q[:, 2] - floor, bb["below"] - 4.0,
                                                                                 bb["below"]))
        g = bb["depth"] * np.exp(-0.5 * (dist / bb["sigma"]) ** 2) * plantar * (1.0 - T.smoothstep(q[:, 0], *bb["lat_x"]))
        out -= g[:, None] * nrm
        rep["ball_back"] = {"max": round(float(g.max()), 2)}
    rep["faired_n"] = rep_fair
    pd = cfg.get("pads") or {}
    if pd.get("amp"):
        add = np.zeros(len(q))
        plantar = T.smoothstep(-nrm[:, 2], *pd["plantar"])
        for k in pd["toes"]:
            seg = segs[f"t{k}p"]
            t, u, h = seg.local(q)
            g = T.gauss(t - pd["at"] * seg.length, pd["sigma"] * seg.length)
            add = np.maximum(add, pd["amp"] * g * T.toe_weight(groups, k))
        add *= plantar
        out += add[:, None] * nrm
        rep["pads_max"] = round(float(add.max()), 2)
    if report is not None:
        report["sole"] = rep
    return out


# The anterior ankle crease (round 1's m26; spec 01 §3.2: one horizontal fold at the dorsiflexion line from (-30, -80,
# 84) to (+32, -76, 80), bowed 3 mm toward the toes, 0.4 mm deep and 1.2 wide, two or three fine lines 3-4 mm above
# it), on the front of the ankle where part 01's fillet now turns into the dorsum: a groove by height on the skin
# facing forward, its height falling `drop` mm at the middle of its span (the bow down the sloping front), the
# fainter lines above it shorter
# (the first build's 0.4 mm groove over x -30..32, sigma 0.55, read in clay as a hard ring round the ankle, a sock's
# top: shallower, softer and shorter now)
ANKLE_CREASE = {"z": [84.0, 80.0], "x": [-24.0, 26.0], "drop": 2.0, "depth": 0.2, "sigma": 0.8, "fade": 10.0,
                "front": [0.4, 0.75], "lines": [[3.6, 0.07, 0.6, 0.7], [7.4, 0.045, 0.55, 0.5]]}


def ankle_crease(q, nrm, P, report=None):
    """The anterior ankle crease (ANKLE_CREASE). Returns positions."""
    cfg = _cfg(P, "ankle_crease", ANKLE_CREASE)
    if not cfg.get("depth"):
        return q
    floor = float(q[:, 2].min())
    x, z = q[:, 0], q[:, 2] - floor
    x0, x1 = cfg["x"]
    xm, half = 0.5 * (x0 + x1), 0.5 * (x1 - x0)
    tx = np.clip((x - x0) / (x1 - x0), 0.0, 1.0)
    zc = cfg["z"][0] + (cfg["z"][1] - cfg["z"][0]) * tx - cfg["drop"] * np.clip(1.0 - ((x - xm) / half) ** 2, 0.0, 1.0)
    front = T.smoothstep(-nrm[:, 1], *cfg["front"]) * (q[:, 1] < -60.0)
    g = np.zeros(len(q))
    for dz, depth, sigma, span in [[0.0, cfg["depth"], cfg["sigma"], 1.0]] + list(cfg["lines"]):
        wx = smoother_window(x, xm - span * half - cfg["fade"], xm - span * half + cfg["fade"],
                             xm + span * half - cfg["fade"], xm + span * half + cfg["fade"])
        g = np.maximum(g, depth * np.exp(-0.5 * ((z - zc - dz) / sigma) ** 2) * wx)
    g *= front
    if report is not None:
        report["ankle_crease"] = {"max": round(float(g.max()), 2), "n": int((g > 0.02).sum())}
    return q - g[:, None] * nrm


# --------------------------------------------------------------------------- pass 2: the veins

# Round 1's blocking m1 and m3 (all three critics): no veins. Spec 01 §3.2 and §3.4: the dorsal venous arch across
# the dorsum at 55-65 % L, its tributaries from the webs, the great saphenous from its medial end in front of the
# medial malleolus (3-3.5 mm, 1 mm proud), Ø 2.5-3 mm, 0.7 mm proud, a grey-green tint. Each vein is a curve laid on
# the skin: its control points found on the skin ("top" x, y: the highest skin there; "med" / "lat" y, z: the most
# medial or lateral skin at that station and height), a Catmull-Rom curve through them, wiggled sideways a little
# (`wiggle_mm` at `wiggle_lambda` mm) and each sample set on the nearest skin's tangent plane. The skin rises along
# its normals by a soft cord, (1 - (d / r)^2)^2 of the distance to the curve (about 1.08 r across at half height),
# its height varying along the vein (`vary`, a slow wobble, and `bead`, the valves' beading every `bead_mm`), tapering
# at free ends, the veins joined by a p-norm of power `k` so a branch flows into its trunk. Foot.Vein, the tint's
# mask, is softer and wider (a Gaussian of `tint_sigma` r), as the colour of a vein spreads through the skin.
VEINS = {
    # (the first build's 6.5 mm wiggle, 8 mm beading and 5.5 mm radius wobble beat into a twisted rope in clay: the
    # meander is now slow, the beading faint and long, the section (1 - x^2)^3, softer at its shoulders)
    "seed": 23, "step_mm": 0.25, "wiggle_mm": [0.9, 0.12], "wiggle_lambda": [24.0, 11.0],
    "vary": 0.28, "vary_lambda": [30.0, 13.0], "bead": 0.06, "bead_mm": 13.0, "r_vary": 0.1,
    "r_lambda": [20.0, 9.0], "power": 3.0, "k": 5.0, "tint_sigma": 0.5,
    # each path's radius r: the section (1 - (d / r)^2)^power is about 0.91 r across at half height for power 3
    "paths": {
        # the arch and the great saphenous are one vein (the arch's medial end turns back along the medial side and
        # runs up in front of the malleolus): two paths meeting at a point made a corner, and with the oblique branch
        # a box, in the medial view. From the lateral marginal vein across the dorsum, round, and up the leg; `mul`
        # the height's and `rmul` the radius's share at each control point
        "arch_saphenous": {"pts": [["lat", -92.0, 29.0], ["lat", -110.0, 25.0], ["lat", -132.0, 26.0],
                                   ["lat", -152.0, 30.0], ["top", 35.0, -166.0], ["top", 23.0, -175.0],
                                   ["top", 9.0, -181.0], ["top", -5.0, -182.0], ["top", -19.0, -178.0],
                                   ["top", -30.0, -170.0], ["med", -154.0, 36.0], ["med", -133.0, 45.0],
                                   ["med", -112.0, 53.0], ["med", -94.0, 66.0], ["med", -82.0, 84.0],
                                   ["med", -76.0, 104.0], ["med", -72.0, 130.0], ["med", -70.0, 165.0],
                                   ["med", -69.0, 205.0]],
                           # (the lateral marginal vein at 0.45-0.65 read in V3 as a crisp ridge along the side)
                           "mul": [0.22, 0.28, 0.36, 0.52, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.15, 1.2, 1.25, 1.25,
                                   1.25, 1.25, 1.2, 1.1, 1.0],
                           "rmul": [0.75, 0.8, 0.85, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0, 1.05, 1.08, 1.1, 1.12, 1.12, 1.12,
                                    1.12, 1.12, 1.12, 1.12],
                           "amp": 0.76, "r": 3.3, "taper": [25.0, 25.0], "fade_z": [150.0, 205.0]},
        "t1": {"pts": [["top", -14.0, -219.0], ["top", -12.5, -206.0], ["top", -15.0, -193.0], ["top", -18.0, -178.5]],
               "amp": 0.45, "r": 2.7, "taper": [9.0, 0.0]},
        "t2": {"pts": [["top", 6.5, -222.0], ["top", 4.0, -209.0], ["top", 6.0, -196.0], ["top", 3.0, -182.5]],
               "amp": 0.4, "r": 2.6, "taper": [10.0, 0.0]},
        "t3": {"pts": [["top", 22.0, -216.0], ["top", 21.0, -202.0], ["top", 17.0, -189.0], ["top", 14.0, -180.5]],
               "amp": 0.35, "r": 2.5, "taper": [9.0, 0.0]},
        # (a straight diagonal in plan read as a ruled line: it bows now, and leaves the arch and meets the saphenous
        # along them rather than square)
        "oblique": {"pts": [["top", 19.0, -177.5], ["top", 13.0, -170.0], ["top", 8.0, -160.0], ["top", -2.0, -151.0],
                            ["top", -10.0, -144.0], ["top", -17.0, -134.0], ["top", -25.0, -122.0],
                            ["med", -104.0, 62.0], ["med", -96.0, 70.0]],
                    "amp": 0.45, "r": 2.8, "taper": [4.0, 6.0]},
    },
}


def _anchor(q, kind, a, b, floor):
    import macro as M
    if kind == "top":
        return M.skin_top(q, a, b, window_mm=0.8)
    sel = (np.abs(q[:, 1] - a) < 0.8) & (np.abs(q[:, 2] - (floor + b)) < 0.8)
    c = q[sel]
    return c[np.argmin(c[:, 0])] if kind == "med" else c[np.argmax(c[:, 0])]


def _vein_curve(q, nrm, kd, ids, pts3, cfg, seed):
    """A vein's samples on the skin (n, 3) and their arc lengths, from its anchors (Catmull-Rom in 3-D, wiggled,
    each sample set on the tangent plane of its nearest skin vertex)."""
    P_ = np.vstack([pts3[0], pts3, pts3[-1]])
    seg_len = np.linalg.norm(np.diff(pts3, axis=0), axis=1)
    out = []
    starts = []          # the sample index of each control point
    n_done = 0
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        n_s = max(4, int(seg_len[i - 1] / cfg["step_mm"]))
        t = np.linspace(0.0, 1.0, n_s, endpoint=False)[:, None]
        out.append(0.5 * (2.0 * p1 + (p2 - p0) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t * t
                          + (3.0 * p1 - p0 - 3.0 * p2 + p3) * t ** 3))
        starts.append(n_done)
        n_done += n_s
    out.append(P_[-2][None, :])
    starts.append(n_done)
    c = np.vstack(out)
    for _ in range(2):   # onto the skin, then wiggled in its tangent plane, then onto the skin again
        j, _d = _nearest(kd, c)
        v, n = q[ids[j]], nrm[ids[j]]
        c = c - np.einsum("ij,ij->i", c - v, n)[:, None] * n
        if _ == 0:
            tan = np.gradient(c, axis=0)
            tan /= np.maximum(np.linalg.norm(tan, axis=1), 1e-9)[:, None]
            side = np.cross(tan, n)
            side /= np.maximum(np.linalg.norm(side, axis=1), 1e-9)[:, None]
            s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))])
            ph = np.random.default_rng(seed).uniform(0.0, 2.0 * math.pi, 2)
            (a1, a2), (l1, l2) = cfg["wiggle_mm"], cfg["wiggle_lambda"]
            w = a1 * np.sin(2.0 * math.pi * s / l1 + ph[0]) + a2 * np.sin(2.0 * math.pi * s / l2 + ph[1])
            w *= T.smoothstep(s, 0.0, 4.0) * (1.0 - T.smoothstep(s, s[-1] - 4.0, s[-1]))   # the ends stay put
            c = c + w[:, None] * side
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))])
    return c, s, s[np.asarray(starts)]


def veins(q, nrm, P, report=None):
    """The dorsal veins (VEINS). Returns (positions, Foot.Vein's weights)."""
    cfg = _cfg(P, "veins", VEINS)
    paths = cfg.get("paths") or {}
    if not paths:
        return q, None
    floor = float(q[:, 2].min())
    anchors = {name: np.array([_anchor(q, *pt, floor) for pt in v["pts"]]) for name, v in paths.items()}
    allp = np.vstack(list(anchors.values()))
    lo, hi = allp.min(axis=0) - 12.0, allp.max(axis=0) + 12.0
    ids = np.nonzero(np.all((q > lo) & (q < hi), axis=1))[0]
    kd = _kdtree(q[ids])
    H = np.zeros(len(q))
    M_ = np.zeros(len(q))
    kk = cfg["k"]
    rep = {}
    for i, (name, v) in enumerate(sorted(paths.items())):
        c, s, s_pts = _vein_curve(q, nrm, kd, ids, anchors[name], cfg, cfg["seed"] + 7 * i)
        L = float(s[-1])
        mul = np.interp(s, s_pts, v.get("mul") or [1.0] * len(v["pts"]))
        t0, t1 = v.get("taper", [0.0, 0.0])
        taper = (T.smoothstep(s, 0.0, t0) if t0 > 0 else 1.0) * ((1.0 - T.smoothstep(s, L - t1, L)) if t1 > 0 else 1.0)
        amp = v["amp"] * mul * taper * (1.0 + cfg["vary"] * line_noise(s, cfg["seed"] + 11 * i, lams=cfg["vary_lambda"])) \
            * (1.0 + cfg["bead"] * np.sin(2.0 * math.pi * s / cfg["bead_mm"] + 1.7 * i))
        fz = v.get("fade_z")
        if fz:
            amp = amp * (1.0 - T.smoothstep(c[:, 2] - floor, fz[0], fz[1]))
        rmul = np.interp(s, s_pts, v.get("rmul") or [1.0] * len(v["pts"]))
        r = v["r"] * rmul * (1.0 + cfg["r_vary"] * line_noise(s, cfg["seed"] + 13 * i, lams=cfg["r_lambda"]))
        rmax = float(r.max())
        blo, bhi = c.min(axis=0) - rmax, c.max(axis=0) + rmax
        cand = np.nonzero(np.all((q > blo) & (q < bhi), axis=1))[0]
        j, d = _nearest(_kdtree(c), q[cand])
        x = d / r[j]
        h = amp[j] * np.clip(1.0 - x * x, 0.0, 1.0) ** cfg["power"]
        # the union with what the veins already raised, a p-norm (`k` its power): equal to the larger where the other
        # is nothing, smooth where both rise, a little fuller where a branch joins its trunk (2^(1/p))
        old = H[cand]
        H[cand] = (old ** kk + h ** kk) ** (1.0 / kk)
        tint = np.clip(amp[j] / 0.9, 0.0, 1.0) * np.exp(-0.5 * (d / (cfg["tint_sigma"] * r[j])) ** 2)
        M_[cand] = np.maximum(M_[cand], tint)
        rep[name] = {"length_mm": round(L, 1), "amp_max": round(float(amp.max()), 2), "n": int((h > 0.05).sum())}
    if report is not None:
        report["veins"] = rep
    return q + H[:, None] * nrm, np.clip(M_, 0.0, 1.0)


# --------------------------------------------------------------------------- pass 2: wear, age and tone

# Round 1's m4, m6, m11, m19, m26, m33, m34, m38: the foot read young, clean and unused; the heel callus a cream cap
# over the whole heel pad ending in a ruler-straight line (lookdev_p01's stand-in: everything behind y -38 between z
# 1 and 15). Spec 01 §3.4: callus 1 is a band 12-18 mm wide round the heel's posterior-lateral margin, z 0-12.
#  * heel: the band by the skin's own slope (`rim`: where the heel's normal turns from its plantar face, about 21-43
#    degrees, to its back, about 72-83, which on this 24 mm-radius heel pad is that 15 mm band), over a sector from
#    the medial-posterior round to the lateral side, its edges broken by a slow noise, patchy inside, and kept under
#    `scale` so the recipe's callus colour fades over most of the inner margin rather than at a line (the recipe
#    reaches full callus at 0.5) and its cracks thin out away from the rim;
#  * red (Hires.Wear x): pressure redness at the ball, the heel pad, toe 5's outer side over its PIP, the lateral 5th
#    MTP and the medial first MTP and hallux IP (boot rub), patchy;
#  * dry (y): slight dryness, scaling the shader draws as fine pale flakes, at the heel rim, the ball, toe 5's outer
#    side, the medial hallux and the sole's margins;
#  * tone (z, signed): the skin's regional unevenness, broad and slow (positive browner, negative paler and
#    yellower): the malleoli browner, the plantar margins paler and yellower, and everywhere a slow, isotropic
#    variation of up to +-0.45 in patches 25-45 mm across (blob_noise).
WEAR = {
    "heel": {"centre": [0.0, -32.0], "sector": [-78.0, -45.0, 85.0, 115.0], "rim": [0.12, 0.3, 0.72, 0.93],
             "z": [13.0, 20.0], "y_front": [-64.0, -50.0], "edge_noise": 0.07, "noise_mm": 9.0,
             "patch": [0.6, 1.0], "patch_mm": 5.0, "lateral": 0.25, "scale": 0.72, "seed": 41},
    "red": {"ball": [-6.0, -204.0, 40.0, 15.0, 0.75], "heel": [0.0, -34.0, 24.0, 0.5], "toe5": [7.5, 0.9],
            "mtp5": [50.0, -185.0, 6.0, 13.0, 0.55], "mtp1": [12.0, 0.45], "ip1": [-53.0, -250.0, 10.0, 8.0, 0.4],
            "patch_mm": 4.0, "seed": 43},
    "dry": {"heel_rim": [0.08, 0.25, 0.8, 0.95, 0.8], "ball": 0.5, "toe5": 0.6, "ip1": 0.45, "margin": 0.25,
            "patch_mm": 3.5, "seed": 47},
    "tone": {"broad": 0.45, "broad_mm": 15.0, "malleoli": 0.55, "margin": -0.6, "seed": 53},   # blobs of sigma 15
}


def wear_masks(ctx, q, nrm, groups, segs, P, rep):
    """Foot.Callus.Heel and Hires.Wear (red, dry, tone) on the finished skin (WEAR). Returns (heel, wear)."""
    import macro as M
    W = _cfg(P, "wear", WEAR)
    floor = float(q[:, 2].min())
    zr = q[:, 2] - floor
    nz = -nrm[:, 2]
    # ---- the heel callus band
    h = W["heel"]
    cx, cy = h["centre"]
    th = np.degrees(np.arctan2(q[:, 0] - cx, q[:, 1] - cy))      # 0 straight back, +90 lateral
    e = h["edge_noise"] * wave_noise(q, h["noise_mm"], h["seed"])
    r0, r1, r2, r3 = h["rim"]
    rim = T.smoothstep(nz + e, r0, r1) * (1.0 - T.smoothstep(nz - e, r2, r3))
    patch = h["patch"][0] + (h["patch"][1] - h["patch"][0]) * T.smoothstep(wave_noise(q, h["patch_mm"], h["seed"] + 1), -0.9, 0.9)
    side = (1.0 - h["lateral"]) + h["lateral"] * T.smoothstep(th, -20.0, 40.0)
    heel = h["scale"] * rim * T.window(th, *h["sector"]) * (1.0 - T.smoothstep(zr, *h["z"])) \
        * T.smoothstep(q[:, 1], *h["y_front"]) * patch * side
    # ---- pressure redness
    R = W["red"]
    pr = 0.5 + 0.5 * T.smoothstep(wave_noise(q, R["patch_mm"], R["seed"]), -1.0, 1.0)
    plantar = T.smoothstep(nz, 0.45, 0.8)
    bx, by_, brx, bry, ba = R["ball"]
    ball = np.exp(-0.5 * (((q[:, 0] - bx) / brx) ** 2 + ((q[:, 1] - by_) / bry) ** 2) * 2.2) * plantar
    hx, hy, hr, ha = R["heel"]
    heel_pad = (1.0 - T.smoothstep(np.hypot(q[:, 0] - hx, q[:, 1] - hy), 0.55 * hr, hr)) * plantar
    t5m = segs["t5m"]
    toe5 = M.sphere(q, M.skin_top(q, t5m.o[0], t5m.o[1]) + np.array([3.0, 0.0, -2.0]), R["toe5"][0]) \
        * T.smoothstep(nrm[:, 0], 0.1, 0.5) * T.toe_weight(groups, 5)
    mx, my, mz, mr, ma = R["mtp5"]
    mtp5 = M.sphere(q, np.array([mx, my, floor + mz]), mr) * T.smoothstep(nrm[:, 0], 0.1, 0.5)
    anchors = ctx.report.get("anchors") or {}
    c1 = np.asarray(anchors.get("mtp_prominence", [-52.0, -210.0, floor + 22.0]), float)
    mtp1 = M.sphere(q, c1, R["mtp1"][0]) * T.smoothstep(-nrm[:, 0], 0.2, 0.6)
    ix, iy, iz, ir, ia = R["ip1"]
    ip1 = M.sphere(q, np.array([ix, iy, floor + iz]), ir) * T.smoothstep(-nrm[:, 0], 0.2, 0.6)
    red = np.maximum.reduce([ba * ball, ha * heel_pad, R["toe5"][1] * toe5, ma * mtp5, R["mtp1"][1] * mtp1,
                             ia * ip1]) * pr
    # ---- dryness
    Dr = W["dry"]
    pd = 0.4 + 0.6 * T.smoothstep(wave_noise(q, Dr["patch_mm"], Dr["seed"]), -0.7, 1.0)
    a0, a1, a2, a3, aw = Dr["heel_rim"]
    rim_d = T.smoothstep(nz + e, a0, a1) * (1.0 - T.smoothstep(nz - e, a2, a3)) * T.window(th, *h["sector"]) \
        * (1.0 - T.smoothstep(zr, 18.0, 26.0)) * T.smoothstep(q[:, 1], -70.0, -55.0)
    margin = T.smoothstep(nz, 0.15, 0.35) * (1.0 - T.smoothstep(nz, 0.6, 0.85)) * (1.0 - T.smoothstep(zr, 12.0, 20.0)) \
        * T.smoothstep(-q[:, 1], -5.0, 5.0) * (1.0 - T.smoothstep(-q[:, 1], 195.0, 210.0))
    dry = np.maximum.reduce([aw * rim_d, Dr["ball"] * ball, Dr["toe5"] * toe5, Dr["ip1"] * ip1,
                             Dr["margin"] * margin]) * pd
    # ---- tone
    To = W["tone"]
    broad = To["broad"] * np.tanh(blob_noise(q, To["broad_mm"], To["seed"]))
    mal = np.zeros(len(q))
    for y_, z_ in ((-63.0, 89.0), (-55.0, 76.0)):
        sel = np.abs(q[:, 1] - y_) < 1.5
        zz = np.abs(q[:, 2] - (floor + z_)) < 1.5
        for pick in (np.argmin, np.argmax):
            c = q[sel & zz]
            if len(c):
                mal = np.maximum(mal, M.sphere(q, c[pick(c[:, 0])], 16.0))
    tone = np.clip(broad + To["malleoli"] * mal + To["margin"] * margin, -1.0, 1.0)
    rep["wear"] = {"heel_n": int((heel > 0.3).sum()), "red_n": int((red > 0.3).sum()), "dry_n": int((dry > 0.3).sum()),
                   "tone": [round(float(tone.min()), 2), round(float(tone.max()), 2)]}
    return np.clip(heel, 0.0, 1.0), np.stack([np.clip(red, 0.0, 1.0), np.clip(dry, 0.0, 1.0), tone], 1)
