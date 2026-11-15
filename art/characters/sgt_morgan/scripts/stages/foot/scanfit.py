"""Part 01's large forms fitted to real feet (the scan-driven pass, 2026-10-16; spec 01 §3.1 note of that date).

The targets are sections of three men's unloaded foot scans (Schuster, Kelly & Cresswell, "Foot shape-function model
data", CC0, zenodo 10360304, doi 10.5061/dryad.g4f4qrfwt; subjects 038, 081 and 012 seated at about a tenth of their
weight), each mirrored to a left foot and scaled to this foot's length, averaged, and kept in scan_targets.json beside
this file (scripts/research/foot_hires/scan.py targets writes it; the scans themselves are not needed to build). The
same code reads them on the scans and on this foot, so a target and its measure share one definition:

  plan    the outline seen from above below z 50 (the malleoli left out): the medial and lateral x at PLAN_PCTS % L;
  heel    coronal sections 10, 20, 30 and 40 mm in front of the pternion: the medial and lateral x at HEEL_Z, the heel
          from behind as real heels are, a bell narrowing into the Achilles rather than a bulb on a neck;
  sole    the underside's height (the lowest skin over each 2 mm plan cell) across the foot at SOLE_PCTS % L, at the
          shares SOLE_U of the breadth from the medial border: the heel pad, the lateral band on the floor, the arch's
          hollow rising medially, the ball.

The frame is the scans': the long axis from the heel's centre (the middle of its breadth below z 40 at 15 % L) to the
tip of toe 2, the pternion at y 0, the floor at z 0 (`rezero`). fit_sculpt.py reads the measures on its prediction's
subdivided surface (the AnkleProbe) and adds `residuals` to its own; measure() reports the deviations.
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TARGETS = os.path.join(HERE, "scan_targets.json")
PLAN_PCTS = (10, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80)
PLAN_Z = 50.0
HEEL_Y = (-10, -20, -30, -40)
HEEL_Z = (10, 20, 30, 40, 50, 60)
SOLE_PCTS = (10, 16, 22, 28, 34, 40, 46, 52, 58, 64, 70, 76)
SOLE_U = (0.08, 0.2, 0.32, 0.44, 0.56, 0.68, 0.8, 0.92)
CELL = 2.0
TOL = {"plan": 1.5, "heel": 2.0, "sole": 1.2}   # mm: a residual's unit in the fit (and measure()'s report)
LENGTH = 274.3   # the stations are shares of this length from the pternion, whatever a surface's own reach: the scans
                 # are scaled to it, and the fit's level-2 surface ends 4 mm short of the dense skin's hallux pulp
FLOOR = (0.25, 0.25)   # the underside kept this far off the floor (mm) at rest, and the penalty's unit below it


def triangles(loop_start, loop_total, loop_vert):
    """Fan triangles of polygons given as loops."""
    ls, lt, lv = (np.asarray(a) for a in (loop_start, loop_total, loop_vert))
    out = []
    for k in range(1, int(lt.max()) - 1):
        ok = lt > k + 1
        out.append(np.stack([lv[ls[ok]], lv[ls[ok] + k], lv[ls[ok] + k + 1]], 1))
    return np.concatenate(out).astype(np.int64)


def sample_tris(q, T, step):
    """Points on every triangle no further than about `step` apart (a barycentric grid per triangle)."""
    e = np.stack([np.linalg.norm(q[T[:, a]] - q[T[:, b]], axis=1) for a, b in ((0, 1), (1, 2), (2, 0))], 1).max(1)
    n = np.clip(np.ceil(e / step).astype(int), 1, 40)
    pts = []
    for k in np.unique(n):
        sel = np.nonzero(n == k)[0]
        i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1), indexing="ij")
        keep = (i + j) <= k
        u, v = (i[keep] / k).astype(float), (j[keep] / k).astype(float)
        w = 1.0 - u - v
        A, B, C = q[T[sel, 0]], q[T[sel, 1]], q[T[sel, 2]]
        pts.append((A[:, None, :] * w[None, :, None] + B[:, None, :] * u[None, :, None]
                    + C[:, None, :] * v[None, :, None]).reshape(-1, 3))
    return np.concatenate(pts)


def section_points(q, T, axis, value, step=0.3):
    """The plane coordinate[axis] = value cut through the triangles, as points along its segments."""
    d = q[T][:, :, axis] - value
    cut = (d.min(axis=1) < 0) & (d.max(axis=1) > 0)
    Tq, D = q[T[cut]], d[cut]
    ends = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        da, db = D[:, a], D[:, b]
        hit = (da * db) < 0
        t = np.where(hit, da / np.where(hit, da - db, 1.0), np.nan)
        ends.append(Tq[:, a] + t[:, None] * (Tq[:, b] - Tq[:, a]))
    E = np.stack(ends, 1)
    ok = np.isfinite(E[:, :, 0])
    two = ok.sum(1) >= 2
    if not two.any():
        return np.zeros((0, 3))
    idx = np.argsort(~ok[two], axis=1, kind="stable")[:, :2]
    seg = np.take_along_axis(E[two], idx[:, :, None], axis=1)
    out = [seg[:, 0]]
    L = np.linalg.norm(seg[:, 1] - seg[:, 0], axis=1)
    n = np.clip(np.ceil(L / step).astype(int), 1, 100)
    for k in np.unique(n):
        s = seg[n == k]
        for t in np.arange(1, k + 1) / k:
            out.append(s[:, 0] + t * (s[:, 1] - s[:, 0]))
    return np.concatenate(out)


# --------------------------------------------------------------------------- the frame

def heel_origin(xy, z):
    """(the heel's centre x, the pternion's y) of plan points already turned to the heading (toes toward -y)."""
    low = z < 60.0
    y_pt = xy[low, 1].max()
    L = y_pt - xy[low, 1].min()
    band = (z < 40.0) & (np.abs(xy[:, 1] - (y_pt - 0.15 * L)) < 3.0)
    return np.array([0.5 * (xy[band, 0].min() + xy[band, 0].max()), y_pt])


def rezero(q, tip2, iters=4):
    """q (F-like coordinates, mm, z up from the floor) in the scans' frame: turned so the line from the heel's centre
    to toe 2's tip `tip2` (a point in q's coordinates) runs toward -y, the heel's centre at x 0, the pternion at y 0.
    Returns (q', (R, o)) with q'_xy = q_xy @ R - o."""
    q = np.asarray(q, float)
    tip = np.asarray(tip2, float)[:2]
    h = np.array([0.0, -1.0])
    for _ in range(iters):
        ey = -h
        ex = np.array([ey[1], -ey[0]])
        R = np.stack([ex, ey], 1)
        o = heel_origin(q[:, :2] @ R, q[:, 2])
        t = tip @ R - o
        d = t[0] * ex + t[1] * ey
        h = d / np.linalg.norm(d)
    ey = -h
    ex = np.array([ey[1], -ey[0]])
    R = np.stack([ex, ey], 1)
    o = heel_origin(q[:, :2] @ R, q[:, 2])
    out = q.copy()
    out[:, :2] = q[:, :2] @ R - o
    return out, (R, o)


# --------------------------------------------------------------------------- the measures

def measures(q, T, pts=None, L=LENGTH):
    """The plan, heel and sole measures of a foot already in the scans' frame (q, triangles T), the stations shares
    of L (None: the foot's own reach below z 60); with the lowest underside over the plantar cells ("floor")."""
    if pts is None:
        pts = sample_tris(q, T, 0.75)
    low = pts[pts[:, 2] < 60.0]
    reach = float(low[:, 1].max() - low[:, 1].min())
    L = reach if L is None else float(L)
    out = {"L": L, "reach": reach, "plan": {}, "heel": {}, "sole": {}}
    under = pts[pts[:, 2] < PLAN_Z]

    def outline(y):
        b = under[np.abs(under[:, 1] - y) < 0.75]
        return (float(b[:, 0].min()), float(b[:, 0].max())) if len(b) > 3 else (None, None)
    for p in PLAN_PCTS:
        out["plan"][str(p)] = list(outline(-p / 100.0 * L))
    for y in HEEL_Y:
        s = section_points(q, T, 1, float(y))
        for z in HEEL_Z:
            b = s[np.abs(s[:, 2] - z) < 0.75]
            out["heel"][f"{y},{z}"] = [float(b[:, 0].min()), float(b[:, 0].max())] if len(b) > 1 else [None, None]
    # the underside: the lowest skin over 2 mm cells, each station's row read across the outline at that y
    s60 = pts[pts[:, 2] < 60.0]
    x0, y0 = math.floor(s60[:, 0].min()) - CELL, math.floor(s60[:, 1].min()) - CELL
    nx = int(math.ceil((s60[:, 0].max() - x0) / CELL)) + 2
    ny = int(math.ceil((s60[:, 1].max() - y0) / CELL)) + 2
    i = ((s60[:, 0] - x0) / CELL).astype(int)
    j = ((s60[:, 1] - y0) / CELL).astype(int)
    Z = np.full((nx, ny), np.inf)
    np.minimum.at(Z, (i, j), s60[:, 2])
    xs = x0 + (np.arange(nx) + 0.5) * CELL
    out["floor"] = np.sort(Z[np.isfinite(Z)])[:24].tolist()   # the 24 lowest cells (the fit keeps them off the floor)
    for p in SOLE_PCTS:
        y = -p / 100.0 * L
        jj = int((y - y0) / CELL)
        row = Z[:, jj]
        ok = np.isfinite(row)
        a, b = outline(y)
        if a is None or ok.sum() < 3:
            out["sole"][str(p)] = [None] * len(SOLE_U)
            continue
        out["sole"][str(p)] = [float(np.interp(a + u * (b - a), xs[ok], row[ok])) for u in SOLE_U]
    return out


def flat(meas):
    """{name: value} of a measures() dict, the names residuals() and the targets use."""
    out = {}
    for p, (a, b) in meas["plan"].items():
        out[f"plan_med_{p}"], out[f"plan_lat_{p}"] = a, b
    for k, (a, b) in meas["heel"].items():
        y, z = k.split(",")
        out[f"heel_med_{-int(y)}_{z}"], out[f"heel_lat_{-int(y)}_{z}"] = a, b
    for p, zs in meas["sole"].items():
        for u, z in zip(SOLE_U, zs):
            out[f"sole_{p}_{int(round(u * 100)):02d}"] = z
    return out


def family(name):
    return name.split("_", 1)[0]


def load_targets(path=TARGETS):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def residuals(meas, targets, weight=None):
    """(ours - target) / tolerance for every target that both sides have, in a fixed order (targets["values"]'s); a
    missing measure counts 0 (a shape the sections cannot read is left to the other residuals). `weight` scales a
    family ({"sole": 0.5})."""
    v = flat(meas)
    out = []
    for name, t in sorted(targets["values"].items()):
        fam = family(name)
        x = v.get(name)
        w = (weight or {}).get(fam, 1.0)
        out.append(0.0 if (x is None or t is None) else w * (x - t) / TOL[fam])
    return np.array(out)


def floor_residuals(meas, n=24):
    """One-sided: the lowest underside cells below FLOOR[0] mm, in units of FLOOR[1] (a sole fitted to the scans'
    contact, 0-0.5 mm, must not sink through the floor at rest)."""
    z = list(meas.get("floor") or [])[:n]
    z += [FLOOR[0]] * (n - len(z))
    return np.minimum(np.array(z) - FLOOR[0], 0.0) / FLOOR[1]


def report(meas, targets):
    """Per family: the RMS and the largest deviation from the targets (mm), and where."""
    v = flat(meas)
    out = {}
    for fam in TOL:
        d = [(name, v[name] - t) for name, t in targets["values"].items()
             if family(name) == fam and v.get(name) is not None and t is not None]
        if not d:
            continue
        arr = np.array([x for _, x in d])
        k = int(np.argmax(np.abs(arr)))
        out[fam] = {"rms": round(float(np.sqrt(np.mean(arr ** 2))), 2), "max": round(float(arr[k]), 2), "at": d[k][0],
                    "n": len(d)}
    return out


# --------------------------------------------------------------------------- the part's own scalar targets on a scan

def heel_scalars(q, T, L):
    """Part 01's heel figures as footmetrics reads them, on any mesh in F-like coordinates: the calliper breadth
    within 60 mm of the pternion over z 4-44 (heel_breadth) and the widths across the line y = -0.15 L at z 10, 20
    and 30 (heel_width_z10...)."""
    out = {}
    lo, hi = np.inf, -np.inf
    for z in np.arange(4.0, 45.0, 4.0):
        s = section_points(q, T, 2, float(z))
        s = s[(s[:, 1] > -60.0) & (s[:, 1] < 5.0)]
        if len(s):
            lo, hi = min(lo, s[:, 0].min()), max(hi, s[:, 0].max())
    out["heel_breadth"] = float(hi - lo)
    for z in (10, 20, 30):
        s = section_points(q, T, 2, float(z), step=0.1)
        b = s[np.abs(s[:, 1] + 0.15 * L) < 0.15]
        out[f"heel_width_z{z}"] = float(np.ptp(b[:, 0])) if len(b) > 1 else None
    return out
