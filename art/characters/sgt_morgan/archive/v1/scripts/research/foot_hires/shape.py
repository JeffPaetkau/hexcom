"""The shape pass (2026-10-14): the foot's large forms measured on a saved skin, in frame F (mm: origin at the
pternion on the floor, +X lateral for the left foot, toes toward -Y), for renders/research/foot_hires/shape/.

  "$SGT_PYIMG" -I scripts/research/foot_hires/shape.py measure cache/research/foot_hires/<name>.npz [--out m.json]
  "$SGT_PYIMG" -I scripts/research/foot_hires/shape.py compare before.npz after.npz [--out c.json]

A skin is what run.py --save writes (cache/research/foot_hires/<method>[_<tag>].npz: the dense skin in world mm, frame
F, the toes' weights and the joints). Everything here is numpy on the vertices (the dense skin's spacing is 0.2-0.5 mm,
so a vertex band stands in for a section): the plan outline seen from above (Jeff, 2026-10-14: "from the top it looks
too long and too round at the same time"), the dorsum's sections, the toes in plan, the malleoli, the leg's sections
up to z 250, the heel and its projection behind the Achilles, the medial profile, the navicular, the 5th metatarsal
styloid and the MTP line. Runs in the image venv or in Blender's Python.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

STEP = 1.0   # mm: the outline's bins


# --------------------------------------------------------------------------- reading

def load(path):
    """{q (F mm), faces, toe_w (n x 5 or None), joints ({name: F mm} or None)} from a run.py --save file."""
    z = np.load(path)
    q = (z["skin_co"].astype(float) - z["F_o"]) @ z["F_R"]
    out = {"q": q, "faces": z["skin_faces"], "path": path,
           "toe_w": z["toe_w"].astype(float) if "toe_w" in z.files else None,
           "joints": {k: np.asarray(v, float) for k, v in json.loads(str(z["joints"])).items()} if "joints" in z.files else None}
    return out


def extent(q):
    """The foot's back (the pternion's y), its tip and its length, from the skin below z 60."""
    f = q[q[:, 2] < 60.0]
    y_back, y_tip = float(f[:, 1].max()), float(f[:, 1].min())
    return y_back, y_tip, y_back - y_tip


def _binned(v, key, lo, step, n, reduce):
    """Per-bin min or max of v over key's bins [lo + i step, lo + (i + 1) step)."""
    i = np.floor((key - lo) / step).astype(np.int64)
    ok = (i >= 0) & (i < n)
    out = np.full(n, np.inf if reduce == "min" else -np.inf)
    (np.minimum if reduce == "min" else np.maximum).at(out, i[ok], v[ok])
    out[~np.isfinite(out)] = np.nan
    return out


def hull_perimeter(P):
    """Perimeter of the convex hull of 2-D points (the tape girth, ANSUR's convention)."""
    P = np.unique(np.round(np.asarray(P, float), 3), axis=0)
    if len(P) < 3:
        return 0.0

    def half(points):
        h = []
        for p in points:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(p)
        return h

    lower, upper = half(P), half(P[::-1])
    H = np.array(lower[:-1] + upper[:-1])
    return float(np.linalg.norm(np.diff(np.vstack([H, H[:1]]), axis=0), axis=1).sum())


def _r(v, n=1):
    return None if v is None or (isinstance(v, float) and not np.isfinite(v)) else round(float(v), n)


# --------------------------------------------------------------------------- the plan outline

def plan(q, L, y_back, y_tip, joints=None, z_cut=125.0):
    """The outline seen from above (the skin below z_cut, the leg above the malleoli left out): its medial and
    lateral extremes per 1 mm of length, the breadth at every 10 % of the length, the widest points, the lateral
    border against the straight chord from the heel (15 % L) to the 5th metatarsal head, the medial border against
    the chord from the heel to the 1st metatarsal head, and the styloid's bump on the lateral outline."""
    s = q[q[:, 2] < z_cut]
    lo = np.floor(y_tip) - 1.0
    n = int(np.ceil(y_back + 1.0 - lo))
    xmin = _binned(s[:, 0], s[:, 1], lo, STEP, n, "min")
    xmax = _binned(s[:, 0], s[:, 1], lo, STEP, n, "max")
    ys = lo + (np.arange(n) + 0.5) * STEP

    def at(arr, y):
        return float(np.interp(y, ys[np.isfinite(arr)], arr[np.isfinite(arr)]))

    out = {"z_cut": z_cut, "L": _r(L), "stations": []}
    for p in range(5, 100, 5):
        y = y_back - p / 100.0 * L
        a, b = at(xmin, y), at(xmax, y)
        out["stations"].append({"pct": p, "y": _r(y), "medial_x": _r(a), "lateral_x": _r(b), "breadth": _r(b - a),
                                "breadth_pct_L": _r(100.0 * (b - a) / L)})
    body = (ys < y_back - 0.30 * L) & (ys > y_back - 0.86 * L)
    br = xmax - xmin
    i = int(np.nanargmax(np.where(body, br, np.nan)))
    out["widest"] = {"y": _r(ys[i]), "pct": _r(100.0 * (y_back - ys[i]) / L), "breadth": _r(br[i])}
    il = int(np.nanargmax(np.where(body, xmax, np.nan)))
    im = int(np.nanargmin(np.where(body, xmin, np.nan)))
    out["lateral_most"] = {"y": _r(ys[il]), "pct": _r(100.0 * (y_back - ys[il]) / L), "x": _r(xmax[il])}
    out["medial_most"] = {"y": _r(ys[im]), "pct": _r(100.0 * (y_back - ys[im]) / L), "x": _r(xmin[im])}
    # the heads' corners: the lateral extreme within 15 mm of the 5th MTP joint, the medial within 15 mm of the 1st's
    y5 = float(joints["toe-5-1"][1]) if joints else y_back - 0.656 * L
    y1 = float(joints["toe-1-1"][1]) if joints else y_back - 0.745 * L
    near5 = np.abs(ys - y5) < 15.0
    near1 = np.abs(ys - y1) < 15.0
    i5 = int(np.nanargmax(np.where(near5, xmax, np.nan)))
    i1 = int(np.nanargmin(np.where(near1, xmin, np.nan)))
    out["mt5_corner"] = {"y": _r(ys[i5]), "pct": _r(100.0 * (y_back - ys[i5]) / L), "x": _r(xmax[i5])}
    out["mt1_corner"] = {"y": _r(ys[i1]), "pct": _r(100.0 * (y_back - ys[i1]) / L), "x": _r(xmin[i1])}
    out["ball_breadth_heads"] = _r(xmax[i5] - xmin[i1])
    # the lateral border against its chord from the heel to the 5th head (positive: bulging out past the chord)
    ya = y_back - 0.15 * L
    A, B = np.array([at(xmax, ya), ya]), np.array([xmax[i5], ys[i5]])
    span = (ys < y_back - 0.30 * L) & (ys > ys[i5])   # ahead of the malleoli (they stand off the heel's chord)
    chord = A[0] + (ys - ya) * (B[0] - A[0]) / (B[1] - ya)
    dev = np.where(span, xmax - chord, np.nan)
    j = int(np.nanargmax(dev))
    out["lateral_border"] = {"chord_from": [_r(A[0]), _r(A[1])], "chord_to": [_r(B[0]), _r(B[1])],
                             "max_bulge": _r(dev[j]), "max_bulge_y": _r(ys[j]),
                             "max_bulge_pct": _r(100.0 * (y_back - ys[j]) / L),
                             "bulge_at_pct": {str(p): _r(np.interp(y_back - p / 100.0 * L, ys[span], dev[span]))
                                              for p in (25, 35, 45, 55)}}
    # the outline's direction just behind the 5th head and just ahead of it (dx per mm of length, toward the toes):
    # a corner turns from outward-going to inward-going
    def slope(arr, y_from, y_to):
        m = (ys <= max(y_from, y_to)) & (ys >= min(y_from, y_to)) & np.isfinite(arr)
        return float(np.polyfit(-ys[m], arr[m], 1)[0]) if m.sum() > 3 else None
    out["lateral_border"]["slope_behind_head"] = _r(slope(xmax, ys[i5] + 35.0, ys[i5] + 5.0), 3)
    out["lateral_border"]["slope_ahead_of_head"] = _r(slope(xmax, ys[i5] - 3.0, ys[i5] - 25.0), 3)
    # the medial border against its chord from the heel to the 1st head (positive: dipping in, as from above along
    # the arch)
    A2, B2 = np.array([at(xmin, ya), ya]), np.array([xmin[i1], ys[i1]])
    span2 = (ys < y_back - 0.40 * L) & (ys > ys[i1])   # ahead of the navicular, as footmetrics.plan
    chord2 = A2[0] + (ys - ya) * (B2[0] - A2[0]) / (B2[1] - ya)
    dip = np.where(span2, xmin - chord2, np.nan)
    j2 = int(np.nanargmax(dip))
    out["medial_border"] = {"chord_from": [_r(A2[0]), _r(A2[1])], "chord_to": [_r(B2[0]), _r(B2[1])],
                            "max_dip": _r(dip[j2]), "max_dip_y": _r(ys[j2]),
                            "max_dip_pct": _r(100.0 * (y_back - ys[j2]) / L),
                            "slope_behind_head": _r(slope(xmin, ys[i1] + 35.0, ys[i1] + 5.0), 3)}
    # the styloid on the plan outline: the lateral outline's rise over a line fitted 9-25 mm either side of 53 % L
    yc = y_back - 0.53 * L
    fit = np.isfinite(xmax) & (np.abs(ys - yc) > 9.0) & (np.abs(ys - yc) < 25.0)
    k = np.polyfit(ys[fit], xmax[fit], 1)
    mid = np.isfinite(xmax) & (np.abs(ys - yc) <= 9.0)
    res = xmax[mid] - np.polyval(k, ys[mid])
    out["styloid_plan_bump"] = {"mm": _r(res.max(), 2), "y": _r(ys[mid][np.argmax(res)])}
    out["outline"] = {"y": ys.round(1).tolist(), "medial_x": [_r(v, 2) for v in xmin],
                      "lateral_x": [_r(v, 2) for v in xmax]}
    return out


def dorsum_sections(q, L, y_back, pcts=(40, 50, 60, 70)):
    """Each section across the foot: the dorsal crest (its x and height), the top's height 15 and 30 mm either side of
    the crest (medial, lateral) and the drop at the section's sides: a dome falls off evenly, a real dorsum is a roof
    along the 2nd metatarsal, steep to the medial side, long and flat to the lateral border."""
    out = {}
    for p in pcts:
        y = y_back - p / 100.0 * L
        s = q[(np.abs(q[:, 1] - y) < 0.5) & (q[:, 2] < 150.0)]
        lo = np.floor(s[:, 0].min())
        n = int(np.ceil(s[:, 0].max() - lo)) + 1
        top = _binned(s[:, 2], s[:, 0], lo, 1.0, n, "max")
        xs = lo + np.arange(n) + 0.5
        ok = np.isfinite(top)
        i = int(np.nanargmax(top))
        xc, zc = xs[i], top[i]

        def h(dx):
            x = xc + dx
            return _r(np.interp(x, xs[ok], top[ok])) if xs[ok].min() <= x <= xs[ok].max() else None
        out[str(p)] = {"y": _r(y), "crest_x": _r(xc), "crest_z": _r(zc), "medial_edge_x": _r(s[:, 0].min()),
                       "lateral_edge_x": _r(s[:, 0].max()),
                       "z_at": {f"{d:+d}": h(d) for d in (-30, -15, 15, 30, 45)},
                       "lateral_drop_30": _r(zc - np.interp(xc + 30.0, xs[ok], top[ok])),
                       "medial_drop_30": _r(zc - np.interp(xc - 30.0, xs[ok], top[ok]))}
    return out


def toes(q, toe_w, joints, y_back):
    """Each toe in plan: its tip, its plan length from its MTP joint, its width and its top's height."""
    if toe_w is None:
        return {}
    out = {}
    for k in range(1, 6):
        t = q[toe_w[:, k - 1] > 0.5]
        if not len(t):
            continue
        d = {"tip_y": _r(t[:, 1].min()), "top_z": _r(t[:, 2].max()), "plan_width": _r(np.ptp(t[t[:, 1] < np.percentile(t[:, 1], 60), 0]))}
        if joints and f"toe-{k}-1" in joints:
            m = joints[f"toe-{k}-1"]
            d["mtp_y"] = _r(m[1])
            d["length_from_mtp_plan"] = _r(m[1] - t[:, 1].min())
        out[str(k)] = d
    return out


# --------------------------------------------------------------------------- the side forms

def malleoli(q):
    """Each malleolus's apex: the most prominent local peak of the ankle's side profile (the extreme x of 1 mm
    horizontal bands, y -120 to -20) between z 50 and 120, refined by a parabola; its y where the extreme x peaks
    along the length at that height; its prominence over the leg above it (the least extent up to 60 mm higher) and
    over the hollow just under it."""
    out = {}
    zs = np.arange(50.0, 160.0, 1.0)
    band = q[(q[:, 1] > -120.0) & (q[:, 1] < -20.0) & (q[:, 2] > 45.0) & (q[:, 2] < 165.0)]
    for side, sgn in (("medial", -1.0), ("lateral", 1.0)):
        prof = _binned(sgn * band[:, 0], band[:, 2], 49.5, 1.0, len(zs), "max")
        best = None
        for i in range(1, len(zs) - 1):
            if zs[i] > 120.0 or not np.isfinite(prof[i - 1:i + 2]).all():
                continue
            if prof[i] >= prof[i - 1] and prof[i] > prof[i + 1]:
                prom = prof[i] - max(np.nanmin(prof[:i + 1]), np.nanmin(prof[i:i + 60]))
                if best is None or prom > best[0]:
                    best = (prom, i)
        if best is None:
            out[side] = None
            continue
        i = best[1]
        a, b, c = prof[i - 1], prof[i], prof[i + 1]
        den = a - 2.0 * b + c
        t = 0.5 * (a - c) / den if den else 0.0
        z_ap, x_ap = zs[i] + t, b - 0.25 * (a - c) * t
        sl = band[np.abs(band[:, 2] - z_ap) < 1.5]
        ys = np.arange(-120.0, -20.0, 1.0)
        py = _binned(sgn * sl[:, 0], sl[:, 1], -120.0, 1.0, len(ys), "max")
        j = int(np.nanargmax(py))
        if 0 < j < len(ys) - 1 and np.isfinite(py[j - 1:j + 2]).all():
            a, b, c = py[j - 1], py[j], py[j + 1]
            den = a - 2.0 * b + c
            tt = 0.5 * (a - c) / den if den else 0.0
        else:
            tt = 0.0
        y_ap = ys[j] + 0.5 + tt
        above = prof[(zs > z_ap + 10.0) & (zs < z_ap + 60.0)]
        below = prof[(zs < z_ap - 6.0) & (zs > z_ap - 20.0)]
        out[side] = {"x": _r(sgn * x_ap), "y": _r(y_ap), "z": _r(z_ap),
                     "prominence_over_leg_above": _r(x_ap - np.nanmin(above)),
                     "leg_above_least_z": _r(zs[(zs > z_ap + 10.0) & (zs < z_ap + 60.0)][int(np.nanargmin(above))]),
                     "prominence_over_hollow_below": _r(x_ap - np.nanmin(below)) if len(below) else None}
    if out.get("medial") and out.get("lateral"):
        out["bimalleolar"] = _r(out["lateral"]["x"] - out["medial"]["x"])
    return out


def leg_sections(q, zs=tuple(range(60, 260, 10))):
    """Horizontal sections of the ankle and leg: tape girth (convex hull), breadth (x) and depth (y), and the least
    girth between z 100 and 224 (ANSUR's minimum ankle circumference), at 1 mm."""
    def sec(z):
        s = q[np.abs(q[:, 2] - z) < 0.4]
        s = s[s[:, 1] > -170.0] if z < 100 else s
        if len(s) < 20:
            return None
        return {"z": z, "girth": _r(hull_perimeter(s[:, :2])), "breadth": _r(np.ptp(s[:, 0])), "depth": _r(np.ptp(s[:, 1])),
                "x": [_r(s[:, 0].min()), _r(s[:, 0].max())], "y": [_r(s[:, 1].min()), _r(s[:, 1].max())]}
    out = {"sections": [sec(float(z)) for z in zs]}
    fine = [sec(float(z)) for z in np.arange(100.0, 225.0, 2.0)]
    fine = [f for f in fine if f]
    m = min(fine, key=lambda f: f["girth"])
    out["min_girth"] = m
    return out


def heel(q, L, y_back):
    """The heel: its width at 15 % L by height, its greatest width behind y -60 by height, and its back: the
    posterior profile along the Achilles' line (the skin within 4 mm of the heel's centre plane) and how far the
    heel stands behind the Achilles above it."""
    out = {}
    y15 = y_back - 0.15 * L
    rows = []
    for z in range(4, 72, 4):
        b = q[(np.abs(q[:, 2] - z) < 0.4) & (q[:, 1] > -60.0)]
        at15 = b[np.abs(b[:, 1] - y15) < 0.6]
        rows.append({"z": z, "width_15pct": _r(np.ptp(at15[:, 0])) if len(at15) > 3 else None,
                     "width_max_behind_60": _r(np.ptp(b[:, 0])) if len(b) > 3 else None})
    out["widths"] = rows
    low = q[(q[:, 2] > 15.0) & (q[:, 2] < 35.0) & (q[:, 1] > -50.0) & (q[:, 1] < -15.0)]
    xc = 0.5 * (low[:, 0].min() + low[:, 0].max())
    back = q[np.abs(q[:, 0] - xc) < 4.0]
    zs = np.arange(0.0, 220.0, 2.0)
    prof = _binned(back[:, 1], back[:, 2], -1.0, 2.0, len(zs), "max")
    zz = zs + 0.0
    i_pt = int(np.nanargmax(np.where(zz < 70.0, prof, np.nan)))
    above = (zz > zz[i_pt] + 20.0) & (zz < 160.0)
    i_ach = int(np.nanargmin(np.where(above, prof, np.nan)))
    out["centre_x"] = _r(xc)
    out["pternion"] = {"z": _r(zz[i_pt]), "y": _r(prof[i_pt])}
    out["achilles_least"] = {"z": _r(zz[i_ach]), "y": _r(prof[i_ach])}
    out["projection_behind_achilles"] = _r(prof[i_pt] - prof[i_ach])
    out["posterior_profile"] = {str(int(z)): _r(prof[k]) for k, z in enumerate(zz) if int(z) % 10 == 0}
    return out


def medial_profile(q, L, y_back):
    """The medial view's outline (the skin projected on the sagittal plane): the dorsum's height along the length,
    the shin's front by height, and the turn between them."""
    out = {}
    lo = -300.0
    n = 360
    top = _binned(q[:, 2], q[:, 1], lo, 1.0, n, "max")
    ys = lo + np.arange(n) + 0.5
    zs = np.arange(0.0, 300.0, 1.0)
    front = _binned(q[:, 1], q[:, 2], 0.0, 1.0, len(zs), "min")
    out["dorsum"] = {str(p): _r(np.interp(y_back - p / 100.0 * L, ys[np.isfinite(top)], top[np.isfinite(top)]))
                     for p in (40, 45, 50, 55, 60, 65, 70, 75, 80)}
    out["shin_front_y"] = {str(z): _r(front[z]) for z in (100, 120, 150, 200, 250)}
    return out


def bumps(q, L, y_back):
    """The navicular tuberosity on the medial wall and the 5th metatarsal styloid on the lateral one: each the local
    rise of its side's profile (extreme x of the skin at the landmark's height band, by length) over a line fitted
    either side of it."""
    out = {}
    for name, sgn, (z0, z1), (ya, yb) in (("navicular", -1.0, (34.0, 50.0), (-160.0, -80.0)),
                                          ("styloid", 1.0, (8.0, 28.0), (-200.0, -110.0))):
        s = q[(q[:, 2] > z0) & (q[:, 2] < z1) & (q[:, 1] > ya) & (q[:, 1] < yb)]
        ys = np.arange(ya, yb, 1.0)
        prof = _binned(sgn * s[:, 0], s[:, 1], ya, 1.0, len(ys), "max")
        ok = np.isfinite(prof)
        best = None
        for c in np.arange(ya + 20.0, yb - 20.0, 1.0):
            fit = ok & (np.abs(ys - c) > 8.0) & (np.abs(ys - c) < 22.0)
            mid = ok & (np.abs(ys - c) <= 5.0)
            if fit.sum() < 10 or not mid.any():
                continue
            k = np.polyfit(ys[fit], prof[fit], 1)
            r = float((prof[mid] - np.polyval(k, ys[mid])).max())
            if best is None or r > best[0]:
                best = (r, c, float(prof[mid].max()))
        out[name] = {"bump_mm": _r(best[0], 2), "y": _r(best[1]), "x": _r(sgn * best[2]), "z_band": [z0, z1]} if best else None
    return out


def mtp(q, L, y_back, joints):
    """The metatarsal heads: the joint centres' line and the surface bulges the calliper finds (spec 01 §3.1)."""
    out = {}
    if joints:
        a, b = joints["toe-1-1"], joints["toe-5-1"]
        out["mtp1_joint"] = [_r(v) for v in a]
        out["mtp5_joint"] = [_r(v) for v in b]
        out["line_angle_deg"] = _r(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
    low = q[(q[:, 2] > 6.0) & (q[:, 2] < 41.0)]
    m = low[(low[:, 1] > y_back - 0.86 * L) & (low[:, 1] < y_back - 0.55 * L)]
    i = int(np.argmin(m[:, 0]))
    lat = low[(low[:, 1] > y_back - 0.78 * L) & (low[:, 1] < y_back - 0.60 * L)]
    j = int(np.argmax(lat[:, 0]))
    out["ball_length_medial"] = _r(y_back - m[i, 1])
    out["ball_length_lateral"] = _r(y_back - lat[j, 1])
    out["medial_bulge"] = [_r(v) for v in m[i]]
    out["lateral_bulge"] = [_r(v) for v in lat[j]]
    out["ball_breadth"] = _r(lat[j, 0] - m[i, 0])
    return out


def measure(path):
    d = load(path)
    q = d["q"]
    y_back, y_tip, L = extent(q)
    out = {"file": os.path.relpath(path).replace(os.sep, "/"), "foot_length": _r(L), "y_back": _r(y_back, 2),
           "floor_z": _r(q[:, 2].min(), 2)}
    out["plan"] = plan(q, L, y_back, y_tip, d["joints"])
    out["dorsum_sections"] = dorsum_sections(q, L, y_back)
    out["toes"] = toes(q, d["toe_w"], d["joints"], y_back)
    out["malleoli"] = malleoli(q)
    out["leg"] = leg_sections(q)
    out["heel"] = heel(q, L, y_back)
    out["medial_profile"] = medial_profile(q, L, y_back)
    out["bumps"] = bumps(q, L, y_back)
    out["mtp"] = mtp(q, L, y_back, d["joints"])
    return out


# --------------------------------------------------------------------------- the report's tables

# reference breadths of the plan outline at 10 % steps (D: spec 01 §3.1-§3.2's landmarks and ANSUR's ball and heel
# breadths with the plan rules: widest across the heads, the lateral border straight, the midfoot ~0.86 of the ball;
# 10 % L from the heel H1 Jeff chose, round behind 10 % L and 74 at its widest)
PLAN_REF = {10: (64, 72), 20: (72, 78), 30: (72, 80), 40: (80, 87), 50: (87, 93), 60: (93, 100), 70: (97, 104),
            80: (86, 96), 90: (55, 66)}


def _mark(v, lo, hi):
    if v is None:
        return "unknown"
    return "ok" if lo <= v <= hi else "off"


def tables(before, after):
    """Markdown tables of the measures that matter for the report, before and after (two measure() dicts)."""
    out = []
    sb = {s["pct"]: s for s in before["plan"]["stations"]}
    sa = {s["pct"]: s for s in after["plan"]["stations"]}
    out.append("| % L | before: medial / lateral x | breadth | after: medial / lateral x | breadth | reference breadth (D) | after |")
    out.append("|---|---|---|---|---|---|---|")
    for p in (10, 20, 30, 40, 50, 60, 70, 80, 90):
        b, a = sb[p], sa[p]
        lo, hi = PLAN_REF[p]
        out.append(f"| {p} | {b['medial_x']} / {b['lateral_x']} | {b['breadth']} | {a['medial_x']} / {a['lateral_x']} | "
                   f"{a['breadth']} | {lo}-{hi} | {_mark(a['breadth'], lo, hi)} |")
    out.append("")
    pb, pa = before["plan"], after["plan"]
    rows = [
        ("widest station (% L)", pb["widest"]["pct"], pa["widest"]["pct"], "60-76 (the heads)", 60, 76),
        ("widest breadth", pb["widest"]["breadth"], pa["widest"]["breadth"], "the ball", None, None),
        ("lateral-most point (% L)", pb["lateral_most"]["pct"], pa["lateral_most"]["pct"], "~64-67 (5th head, 65.6)", 62, 69),
        ("medial-most point (% L)", pb["medial_most"]["pct"], pa["medial_most"]["pct"], "~72-76 (1st head, 74.5)", 71, 77),
        ("ball breadth between the heads' corners", pb["ball_breadth_heads"], pa["ball_breadth_heads"], "104.5 +-2 (ANSUR)", 102.5, 106.5),
        ("midfoot / ball (50 % L over the heads)", round(sb[50]["breadth"] / pb["ball_breadth_heads"], 3),
         round(sa[50]["breadth"] / pa["ball_breadth_heads"], 3), "0.82-0.92 (D)", 0.82, 0.92),
        ("lateral border: max bulge off the heel-5th head chord", pb["lateral_border"]["max_bulge"],
         pa["lateral_border"]["max_bulge"], "<= 3 (D: straight)", -9, 3),
        ("  where (% L)", pb["lateral_border"]["max_bulge_pct"], pa["lateral_border"]["max_bulge_pct"], "", None, None),
        ("lateral outline's slope behind / ahead of the 5th head", f"{pb['lateral_border']['slope_behind_head']} / "
         f"{pb['lateral_border']['slope_ahead_of_head']}", f"{pa['lateral_border']['slope_behind_head']} / "
         f"{pa['lateral_border']['slope_ahead_of_head']}", "+ / - (a corner)", None, None),
        ("medial border: max dip inside the heel-1st head chord", pb["medial_border"]["max_dip"], pa["medial_border"]["max_dip"],
         "2-7 (D)", 2, 7),
        ("  where (% L)", pb["medial_border"]["max_dip_pct"], pa["medial_border"]["max_dip_pct"], "40-65 (D)", 40, 65),
        ("styloid bump on the plan outline", pb["styloid_plan_bump"]["mm"], pa["styloid_plan_bump"]["mm"], "1.5-3 (spec 2.5)", 1.5, 3.5),
    ]
    out.append("| plan measure | before | after | reference | after |")
    out.append("|---|---|---|---|---|")
    for name, b, a, ref, lo, hi in rows:
        mark = "" if lo is None else _mark(a if isinstance(a, (int, float)) else None, lo, hi)
        out.append(f"| {name} | {b} | {a} | {ref} | {mark} |")
    return "\n".join(out)


# --------------------------------------------------------------------------- plots

def load_any(path):
    """(q F mm, triangles) from a run.py --save skin or a fit_sculpt.py --dump surface."""
    z = np.load(path)
    if "skin_co" in z.files:
        q = (z["skin_co"].astype(float) - z["F_o"]) @ z["F_R"]
        f = z["skin_faces"].astype(np.int64)
        tris = np.concatenate([f[:, [0, 1, 2]], f[:, [0, 2, 3]]])
        tris = tris[(tris >= 0).all(axis=1)]
    else:
        q = z["q"].astype(float)
        ls, lt, lv = z["loop_start"], z["loop_total"], z["loop_vert"]
        out = []
        for k in range(1, int(lt.max()) - 1):
            ok = lt > k + 1
            out.append(np.stack([lv[ls[ok]], lv[ls[ok] + k], lv[ls[ok] + k + 1]], 1))
        tris = np.concatenate(out).astype(np.int64)
    return q, tris


def plane_segments(q, tris, axis, value):
    """The segments where the plane coordinate[axis] = value cuts the triangles: (n, 2, 3)."""
    d = q[tris][:, :, axis] - value
    s = np.sign(d)
    cut = (s.min(axis=1) < 0) & (s.max(axis=1) > 0)
    T, D = q[tris[cut]], d[cut]
    pts = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        da, db = D[:, a], D[:, b]
        hit = (da * db) < 0
        t = np.where(hit, da / np.where(hit, da - db, 1.0), np.nan)
        pts.append(T[:, a] + t[:, None] * (T[:, b] - T[:, a]))
    P = np.stack(pts, 1)
    seg = np.array([p[np.isfinite(p[:, 0])][:2] for p in P if np.isfinite(p[:, 0]).sum() >= 2])
    return seg.reshape(-1, 2, 3)


def plot(paths, labels, out, z_cut=125.0, pcts=(40, 50, 60, 70)):
    """One sheet: the plan silhouettes seen from above (below z_cut) outlined over each other, and the sections
    across the foot at pcts of the length, each skin in its own colour (the first in grey, filled)."""
    from PIL import Image, ImageDraw, ImageFont
    colours = [(150, 150, 150), (220, 60, 40), (40, 110, 220), (40, 170, 70), (200, 140, 20)]
    s = 3.0   # px per mm
    W, H = int(200 * s), int(310 * s)
    plan_img = Image.new("RGB", (W, H), (255, 255, 255))
    secs = Image.new("RGB", (int(130 * s) * 2, int(100 * s) * 2), (255, 255, 255))
    font = ImageFont.load_default()
    dp, ds = ImageDraw.Draw(plan_img), ImageDraw.Draw(secs)

    def to_plan(x, y):   # toes up, medial on the right, as hr.plan
        return (W / 2 - (x - 6.0) * s, (y + 300.0) * s)
    for gx in range(-90, 100, 10):
        dp.line([to_plan(gx, -300), to_plan(gx, 10)], fill=(235, 235, 235))
    for gy in range(-300, 11, 10):
        dp.line([to_plan(-90, gy), to_plan(100, gy)], fill=(235, 235, 235) if gy % 50 else (205, 205, 205))
    for i, (path, lab) in enumerate(zip(paths, labels)):
        q, tris = load_any(path)
        y_back, y_tip, L = extent(q)
        c = colours[i % len(colours)]
        low = tris[(q[tris][:, :, 2] < z_cut).all(axis=1)]
        mask = Image.new("L", (W, H), 0)
        dm = ImageDraw.Draw(mask)
        for t in q[low][:, :, :2]:
            dm.polygon([to_plan(*p) for p in t], fill=255)
        m = np.asarray(mask) > 0
        edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
        px = np.asarray(plan_img).copy()
        if i == 0:
            px[m] = (225, 225, 225)
        for dy in (0, 1):
            for dx in (0, 1):
                px[np.roll(np.roll(edge, dy, 0), dx, 1)] = c
        plan_img = Image.fromarray(px)
        dp = ImageDraw.Draw(plan_img)
        dp.text((8, 8 + 14 * i), f"{lab}  L {L:.1f}", fill=c, font=font)
        for j, p in enumerate(pcts):
            y = y_back - p / 100.0 * L
            ox, oy = (j % 2) * 130 * s, (j // 2) * 100 * s
            for sg in plane_segments(q, tris, 1, y):
                if (sg[:, 2] > 110.0).any():
                    continue
                a, b = sg[:, [0, 2]]
                ds.line([(ox + (65 - (a[0] - 6.0)) * s, oy + (90 - a[1]) * s),
                         (ox + (65 - (b[0] - 6.0)) * s, oy + (90 - b[1]) * s)], fill=c, width=2)
            if i == 0:
                ds.text((ox + 6, oy + 6), f"{p} % L (seen from the toes, medial on the right)", fill=(0, 0, 0), font=font)
                for gz in range(0, 101, 10):
                    ds.line([(ox, oy + (90 - gz) * s), (ox + 130 * s, oy + (90 - gz) * s)], fill=(238, 238, 238))
    sheet = Image.new("RGB", (W + secs.width + 20, max(H, secs.height)), (255, 255, 255))
    sheet.paste(plan_img, (0, 0))
    sheet.paste(secs, (W + 20, 0))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out)
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("npz")
    m.add_argument("--out")
    c = sub.add_parser("compare")
    c.add_argument("before")
    c.add_argument("after")
    c.add_argument("--out")
    pl = sub.add_parser("plot")
    pl.add_argument("npz", nargs="+")
    pl.add_argument("--labels")
    pl.add_argument("--out", required=True)
    tb = sub.add_parser("tables", help="markdown tables from two measure JSONs (before, after)")
    tb.add_argument("before")
    tb.add_argument("after")
    a = ap.parse_args(argv)
    if a.cmd == "tables":
        with open(a.before, encoding="utf-8") as f:
            b = json.load(f)
        with open(a.after, encoding="utf-8") as f:
            c = json.load(f)
        print(tables(b, c))
        return 0
    if a.cmd == "plot":
        labels = a.labels.split(",") if a.labels else [os.path.basename(p) for p in a.npz]
        print(plot(a.npz, labels, a.out))
        return 0
    if a.cmd == "measure":
        res = measure(a.npz)
    else:
        res = {"before": measure(a.before), "after": measure(a.after)}
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, indent=1)
            f.write("\n")
    short = {k: v for k, v in (res.items() if a.cmd == "measure" else res["after"].items())}
    short.get("plan", {}).pop("outline", None)
    print(json.dumps(short, indent=1)[:20000])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
