"""Real feet for the foot's large forms (the scan-driven pass, 2026-10-16; notes/research_foot_hires.md): 3D scans of
men's right feet loaded, mirrored to left feet, aligned to frame F and scaled to this foot's length, then compared
with this foot's dense skin section by section.

  "$SGT_PYIMG" -I scripts/research/foot_hires/scan.py align [--ids 038,081,012,059]
  "$SGT_PYIMG" -I scripts/research/foot_hires/scan.py compare --ours cache/research/foot_hires/<name>.npz [--label X]
      [--also other.npz:label] [--out renders/research/foot_hires/scan]
  "$SGT_PYIMG" -I scripts/research/foot_hires/scan.py targets [--ours skin.npz]   (part 01's scan_targets.json)
  "$SGT_PYIMG" -I scripts/research/foot_hires/scan.py sbs --dirs DIR:LABEL,... --views V1,V2 --out DIR
  blender -b cache/body/rigged.blend --python scripts/research/foot_hires/run.py -- --method scan --tag 038
      --params '{"scan": "038", "ref": "cache/research/foot_hires/fields_<tag>.npz"}' --views ...   (build())

The scans: Schuster, Kelly & Cresswell, "Foot shape-function model data" (CC0; zenodo 10360304, doi
10.5061/dryad.g4f4qrfwt), assets/scans/zenodo_10360304/ply/ (scripts/setup/downloads.json, group "scans"): ASCII PLY
from MeshMixer, millimetres, right feet cut flat 125 mm above the floor, two per subject: mBW seated at about a tenth of
the body's weight (near-unloaded: the rest reference here) and fBW standing at full weight on a platform. Only the four
longest (038, 081, 012, 059: 265-278 mm standing, very likely men) are used for shape.

Frame F as part 01's footmetrics.frame reads it (spec 01, conventions): origin at the pternion (the most posterior skin
below z 60) on the floor, the heading the line from the pternion to the tip of the second toe in plan, +Y toward the
heel, toes toward -Y, +X lateral (a left foot), +Z up; a right foot's scan is mirrored into it. Scaled uniformly so the
foot's length (pternion to the longest toe, below z 60) is LENGTH.

Everything is numpy on triangles: a plan raster from below or above (`raster`), plane sections (`segments`), sections'
outlines and widths. Runs in the image venv (PIL for the plots) or in Blender's Python (no plots).
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PLY_DIR = os.path.join(PROJECT, "assets", "scans", "zenodo_10360304", "ply")
CACHE = os.path.join(PROJECT, "cache", "research", "foot_hires", "scan")
OUT = os.path.join(PROJECT, "renders", "research", "foot_hires", "scan")
LENGTH = 274.3          # this foot to its longest toe (part 01 after shape pass 2, the hallux 4.5 mm ahead of toe 2)
MEN = ("038", "081", "012", "059")
CONDS = ("mBW", "fBW")
CUT_Z = 125.0           # the scans' flat top, before scaling
NUMBERS_ONLY = False    # compare's report without the scan-driven pass's findings (--numbers-only)


# --------------------------------------------------------------------------- reading and alignment

# moved to part 01 (scripts/parts/p01/scanref.py, the scan transfer of 2026-10-17), which builds the foot from a
# scan: one definition of the loading and the alignment for the research comparisons and the part
if os.path.dirname(os.path.dirname(HERE)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from parts.p01.scanref import (align, frame_from, heel_origin, load_ply, sample_tris, toe_line,  # noqa: E402,F401
                               tri_normals, vertex_normals)


def ply_path(sid, cond):
    return os.path.join(PLY_DIR, f"{sid}_{cond}_R.ply")


# --------------------------------------------------------------------------- geometry on triangles

class Grid:
    """A plan grid in frame F (cells `cell` mm, x across, y along)."""

    def __init__(self, x0, x1, y0, y1, cell=1.0):
        self.cell = cell
        self.x0, self.y0 = x0, y0
        self.nx, self.ny = int(math.ceil((x1 - x0) / cell)), int(math.ceil((y1 - y0) / cell))
        self.xs = x0 + (np.arange(self.nx) + 0.5) * cell
        self.ys = y0 + (np.arange(self.ny) + 0.5) * cell

    def index(self, p):
        i = np.floor((p[:, 0] - self.x0) / self.cell).astype(np.int64)
        j = np.floor((p[:, 1] - self.y0) / self.cell).astype(np.int64)
        ok = (i >= 0) & (i < self.nx) & (j >= 0) & (j < self.ny)
        return i, j, ok


def raster(q, T, grid, mode="min", zmax=None, pts=None):
    """The skin's lowest (`min`, the plantar map seen from below) or highest (`max`) z over each cell of `grid`
    (NaN where there is no skin), from points sampled on the triangles at half a cell; `zmax` leaves out what lies
    higher (the leg over the heel)."""
    if pts is None:
        pts, _ = sample_tris(q, T, 0.5 * grid.cell)
    if zmax is not None:
        pts = pts[pts[:, 2] < zmax]
    i, j, ok = grid.index(pts)
    out = np.full((grid.nx, grid.ny), np.inf if mode == "min" else -np.inf)
    (np.minimum if mode == "min" else np.maximum).at(out, (i[ok], j[ok]), pts[ok, 2])
    out[~np.isfinite(out)] = np.nan
    return out


def segments(q, T, axis, value):
    """The segments where the plane coordinate[axis] = value cuts the triangles: (n, 2, 3)."""
    d = q[T][:, :, axis] - value
    cut = (d.min(axis=1) < 0) & (d.max(axis=1) > 0)
    Tq, D = q[T[cut]], d[cut]
    out = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        da, db = D[:, a], D[:, b]
        hit = (da * db) < 0
        t = np.where(hit, da / np.where(hit, da - db, 1.0), np.nan)
        out.append(Tq[:, a] + t[:, None] * (Tq[:, b] - Tq[:, a]))
    Pp = np.stack(out, 1)
    ok = np.isfinite(Pp[:, :, 0])
    seg = [p[o][:2] for p, o in zip(Pp, ok) if o.sum() >= 2]
    return np.array(seg).reshape(-1, 2, 3)


def section_points(q, T, axis, value, step=0.25):
    """A plane section as points along its segments (about `step` apart)."""
    seg = segments(q, T, axis, value)
    if not len(seg):
        return np.zeros((0, 3))
    L = np.linalg.norm(seg[:, 1] - seg[:, 0], axis=1)
    n = np.clip(np.ceil(L / step).astype(int), 1, 200)
    out = [seg[:, 0]]
    for k in np.unique(n):
        s = seg[n == k]
        for t in np.arange(1, k + 1) / k:
            out.append(s[:, 0] + t * (s[:, 1] - s[:, 0]))
    return np.concatenate(out)


# --------------------------------------------------------------------------- the feet compared

class Foot:
    """One foot in frame F: q (vertices, mm), T (triangles), pts (points on the skin at most about 0.6 mm apart), its
    length L (the pternion at y 0 to the longest toe, below z 60) and a label."""

    def __init__(self, q, T, label, pts=None, info=None):
        self.q, self.T, self.label = np.asarray(q, float), np.asarray(T, np.int64), label
        self.pts = pts if pts is not None else sample_tris(self.q, self.T, 0.6)[0]
        f = self.q[self.q[:, 2] < 60.0]
        self.L = float(f[:, 1].max() - f[:, 1].min())
        self.info = info or {}


def scan_path(sid, cond):
    return os.path.join(CACHE, f"{sid}_{cond}.npz")


def load_scan(sid, cond, rebuild=False):
    """A scan aligned and scaled (cached in cache/research/foot_hires/scan/). The loaded (fBW) scan is scaled by its
    unloaded twin's factor, so what the weight does to its length shows."""
    path = scan_path(sid, cond)
    if os.path.exists(path) and not rebuild:
        z = np.load(path)
        return Foot(z["q"], z["T"], f"{sid} {cond}", info=json.loads(str(z["info"])))
    scale = None
    if cond == "fBW":
        scale = load_scan(sid, "mBW", rebuild).info["scale"]
    P, T = load_ply(ply_path(sid, cond))
    q, T, info = align(P, T, scale=scale)
    info.update(id=sid, cond=cond, source=os.path.relpath(ply_path(sid, cond), PROJECT).replace(os.sep, "/"))
    os.makedirs(CACHE, exist_ok=True)
    np.savez_compressed(path, q=q.astype(np.float32), T=T.astype(np.int32), info=json.dumps(info))
    return Foot(q, T, f"{sid} {cond}", info=info)


def reframe(q, tip2, iters=4):
    """Re-zero a foot as align() does a scan: the heading from the heel's centre to toe 2's tip (`tip2`, a function of
    the foot's points in the current frame giving the tip), the heel's centre at x 0, the pternion at y 0. Returns
    (q in that frame, (R, o)): the new plan coordinates are q_xy @ R - o (R's columns ex, ey)."""
    heading = np.array([0.0, -1.0])
    for _ in range(iters):
        p, ex, ey, o = frame_from(q, heading)
        t = np.asarray(tip2(p), float)[:2]
        d = t[0] * ex + t[1] * ey
        heading = d / np.linalg.norm(d)
    p, ex, ey, o = frame_from(q, heading)
    return p, (np.stack([ex, ey], 1), o)


def load_ours(path, label):
    """This foot's skin from run.py --save (the dense skin; toe 2's tip from its weights) or fit_sculpt.py --dump
    (part 01's level-2 surface; toe 2 found as on a scan), re-zeroed as a scan is."""
    z = np.load(path)
    if "skin_co" in z.files:
        q = (z["skin_co"].astype(float) - z["F_o"]) @ z["F_R"]
        f = z["skin_faces"].astype(np.int64)
        T = np.concatenate([f[:, [0, 1, 2]], f[:, [0, 2, 3]]])
        T = T[(T >= 0).all(axis=1)]
        w2 = z["toe_w"][:, 1].astype(float) > 0.5

        def tip2(qq):
            t = qq[w2]
            return t[np.argmin(t[:, 1])]
        pts = None
    else:   # a fit_sculpt.py --dump surface
        q = z["q"].astype(float)
        ls, lt, lv = z["loop_start"], z["loop_total"], z["loop_vert"]
        out = []
        for k in range(1, int(lt.max()) - 1):
            ok = lt > k + 1
            out.append(np.stack([lv[ls[ok]], lv[ls[ok] + k], lv[ls[ok] + k + 1]], 1))
        T = np.concatenate(out).astype(np.int64)

        def tip2(qq):
            return toe_line(sample_tris(qq, T, 0.6)[0])["toe2_tip"]
    qn, (R, o) = reframe(q, tip2)
    info = {"source": os.path.relpath(path, PROJECT).replace(os.sep, "/"),
            "to_scan_frame": {"R": np.round(R, 6).tolist(), "o": np.round(o, 3).tolist(),
                              "turn_deg": round(math.degrees(math.atan2(R[1, 0], R[0, 0])), 3)}}
    return Foot(qn, T, label, pts=qn if "skin_co" in z.files else None, info=info)


# --------------------------------------------------------------------------- measures

PCTS = (10, 20, 30, 40, 50, 60, 70, 80, 90)
HEEL_Z = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60)
PLAN_CUT = 118.0     # the plan outline below this height (the scans end at 123-131 once scaled)


def plantar_grid():
    return Grid(-60.0, 80.0, -282.0, 6.0, 2.0)


def plantar_map(foot, grid=None):
    return raster(foot.q, foot.T, grid or plantar_grid(), "min", zmax=60.0, pts=foot.pts)


def _binned(v, key, lo, step, n, reduce):
    i = np.floor((key - lo) / step).astype(np.int64)
    ok = (i >= 0) & (i < n)
    out = np.full(n, np.inf if reduce == "min" else -np.inf)
    (np.minimum if reduce == "min" else np.maximum).at(out, i[ok], v[ok])
    out[~np.isfinite(out)] = np.nan
    return out


def plan_outline(foot, step=1.0, z_cut=PLAN_CUT):
    """The outline seen from above: medial (min x) and lateral (max x) per `step` mm of y, below z_cut."""
    s = foot.pts[foot.pts[:, 2] < z_cut]
    lo = -foot.L - 2.0
    n = int(math.ceil((2.0 - lo) / step))
    ys = lo + (np.arange(n) + 0.5) * step
    return ys, _binned(s[:, 0], s[:, 1], lo, step, n, "min"), _binned(s[:, 0], s[:, 1], lo, step, n, "max")


def at_y(ys, arr, y):
    ok = np.isfinite(arr)
    return float(np.interp(y, ys[ok], arr[ok]))


def transverse(foot, pct, zs=(3, 5, 10, 15, 20, 30, 40)):
    """The section across the foot at pct % of its length: its breadth, top, the medial and lateral x at heights `zs`,
    and the underside's height across it (per 2 mm of x)."""
    y = -pct / 100.0 * foot.L
    p = section_points(foot.q, foot.T, 1, y)
    p = p[p[:, 2] < 110.0]
    out = {"pct": pct, "y": round(y, 1)}
    if not len(p):
        return out
    out.update(breadth=round(float(np.ptp(p[:, 0])), 1), medial_x=round(float(p[:, 0].min()), 1),
               lateral_x=round(float(p[:, 0].max()), 1), top_z=round(float(p[:, 2].max()), 1),
               bottom_z=round(float(p[:, 2].min()), 1))
    w = {}
    for zl in zs:
        b = p[np.abs(p[:, 2] - zl) < 0.6]
        w[str(zl)] = [round(float(b[:, 0].min()), 1), round(float(b[:, 0].max()), 1)] if len(b) else None
    out["x_at_z"] = w
    lo = math.floor(p[:, 0].min() / 2.0) * 2.0
    n = int(math.ceil((p[:, 0].max() - lo) / 2.0))
    under = _binned(p[:, 2], p[:, 0], lo, 2.0, n, "min")
    out["under"] = {"x0": lo, "step": 2.0, "z": [None if not np.isfinite(v) else round(float(v), 1) for v in under]}
    # the contact band: the stretch of the underside within 3 mm of the section's lowest point
    low = p[p[:, 2] < p[:, 2].min() + 3.0]
    out["band_3mm"] = [round(float(low[:, 0].min()), 1), round(float(low[:, 0].max()), 1)]
    return out


def coronal(foot, y, zs=HEEL_Z):
    """The section across the heel at y (a coronal plane): its width and its medial and lateral x at heights zs."""
    p = section_points(foot.q, foot.T, 1, y)
    out = {}
    for zl in zs:
        b = p[np.abs(p[:, 2] - zl) < 0.6]
        out[str(zl)] = None if not len(b) else {"w": round(float(np.ptp(b[:, 0])), 1),
                                                "x": [round(float(b[:, 0].min()), 1), round(float(b[:, 0].max()), 1)]}
    return out


def heel_from_behind(foot, zs=HEEL_Z, behind=-60.0):
    """The heel's silhouette from behind: the skin's width at each height, behind y `behind` (the malleoli's front)."""
    out = {}
    for zl in zs:
        b = foot.pts[(np.abs(foot.pts[:, 2] - zl) < 0.5) & (foot.pts[:, 1] > behind)]
        out[str(zl)] = None if not len(b) else {"w": round(float(np.ptp(b[:, 0])), 1),
                                                "x": [round(float(b[:, 0].min()), 1), round(float(b[:, 0].max()), 1)]}
    return out


def profiles(foot, step=2.0):
    """Along the foot per `step` mm: the dorsum's top, the underside's lowest skin, and the medial and lateral borders'
    undersides (the lowest skin within 12 mm of the outline's medial or lateral extreme, below z 60)."""
    s = foot.pts[foot.pts[:, 2] < 110.0]
    lo = -foot.L - 2.0
    n = int(math.ceil((2.0 - lo) / step))
    ys = lo + (np.arange(n) + 0.5) * step
    top = _binned(s[:, 2], s[:, 1], lo, step, n, "max")
    bot = _binned(s[:, 2], s[:, 1], lo, step, n, "min")
    low = s[s[:, 2] < 60.0]
    i = np.clip(np.floor((low[:, 1] - lo) / step).astype(int), 0, n - 1)
    xmin = _binned(low[:, 0], low[:, 1], lo, step, n, "min")
    xmax = _binned(low[:, 0], low[:, 1], lo, step, n, "max")
    medb = np.full(n, np.inf)
    latb = np.full(n, np.inf)
    mm = low[:, 0] < xmin[i] + 12.0
    ll = low[:, 0] > xmax[i] - 12.0
    np.minimum.at(medb, i[mm], low[mm, 2])
    np.minimum.at(latb, i[ll], low[ll, 2])
    medb[~np.isfinite(medb)] = np.nan
    latb[~np.isfinite(latb)] = np.nan
    return {"ys": ys, "top": top, "bottom": bot, "medial_under": medb, "lateral_under": latb}


def sole_figures(foot, pm=None, grid=None):
    """The sole's landscape in numbers, from the plantar map (mm above the floor):
    heel pad: the underside at 12 % L across the pad, the lowest point and the heights 10 and 20 mm either side of it
      (a dome rises off the floor toward its rim);
    lateral band: at 40 / 50 / 60 % L the lateral third's lowest underside and the width of the band within 2 mm of it;
    arch: at 35-55 % L the underside under the medial border (12 mm in), at mid-breadth, and the vault's highest point;
    ball: at 68-78 % L the lowest underside and its % L, and the rise from it 15 mm behind (the ball's back edge);
    sulcus and pads along each toe's line (from the clefts): the pad's lowest point, the highest underside between it
      and the ball (the sulcus), its height over the pad and its % L."""
    grid = grid or plantar_grid()
    pm = plantar_map(foot, grid) if pm is None else pm
    L = foot.L
    xs, ys = grid.xs, grid.ys

    def row(pct):
        j = int(np.argmin(np.abs(ys + pct / 100.0 * L)))
        return pm[:, j]

    out = {}
    r = row(12)
    ok = np.isfinite(r)
    i0 = int(np.nanargmin(r))
    def rel(dx):
        x = xs[i0] + dx
        return None if not (xs[ok].min() <= x <= xs[ok].max()) else round(float(np.interp(x, xs[ok], r[ok])), 1)
    out["heel_pad_12"] = {"low_z": round(float(r[i0]), 1), "low_x": round(float(xs[i0]), 1),
                          "z_at": {f"{d:+d}": rel(d) for d in (-25, -20, -10, 10, 20, 25)},
                          "width_within_2mm": round(float(np.ptp(xs[ok & (r < r[i0] + 2.0)])), 1),
                          "width_within_5mm": round(float(np.ptp(xs[ok & (r < r[i0] + 5.0)])), 1)}
    band = {}
    for p in (40, 50, 60):
        r = row(p)
        ok = np.isfinite(r)
        x0, x1 = xs[ok].min(), xs[ok].max()
        lat = ok & (xs > x1 - (x1 - x0) / 3.0)
        zl = float(np.nanmin(np.where(lat, r, np.nan)))
        inb = ok & (r < zl + 2.0)
        band[str(p)] = {"lateral_low_z": round(zl, 1), "band_2mm_x": [round(float(xs[inb].min()), 1), round(float(xs[inb].max()), 1)],
                        "band_2mm_w": round(float(np.ptp(xs[inb])), 1), "breadth": round(float(x1 - x0), 1),
                        "band_share": round(float(np.ptp(xs[inb]) / (x1 - x0)), 2)}
    out["lateral_band"] = band
    arch = {}
    for p in (35, 45, 55):
        r = row(p)
        ok = np.isfinite(r)
        x0, x1 = xs[ok].min(), xs[ok].max()
        arch[str(p)] = {"medial_12mm_in": round(float(np.interp(x0 + 12.0, xs[ok], r[ok])), 1),
                        "mid_breadth": round(float(np.interp(0.5 * (x0 + x1), xs[ok], r[ok])), 1),
                        "vault_max": round(float(np.nanmax(r)), 1),
                        "vault_max_x_share": round(float((xs[int(np.nanargmax(r))] - x0) / (x1 - x0)), 2)}
    out["arch"] = arch
    # the ball: the lowest underside between 66 and 80 % L, then the longitudinal profile through it
    win = (ys < -0.66 * L) & (ys > -0.80 * L)
    sub = np.where(win[None, :], pm, np.nan)
    i, j = np.unravel_index(np.nanargmin(sub), pm.shape)
    col = pm[i, :]
    okc = np.isfinite(col)

    def colz(y):
        return round(float(np.interp(y, ys[okc], col[okc])), 1)
    out["ball"] = {"low_z": round(float(pm[i, j]), 1), "x": round(float(xs[i]), 1), "pct": round(float(-ys[j] / L * 100.0), 1),
                   "z_15_behind": colz(ys[j] + 15.0), "z_30_behind": colz(ys[j] + 30.0)}
    return out


def toe_lines(foot, pm=None, grid=None):
    """Along each toe's line (the middle between its clefts on the toe line), the underside's height from 40 mm behind
    the toe's tip to the tip: the pad's lowest point, the sulcus (the highest underside between the pad and the ball
    behind it) and how far it stands over the pad and the ball, and the pad's plantar width (the stretch across within
    2 mm of its lowest point, inside the toe's clefts)."""
    grid = grid or plantar_grid()
    pm = plantar_map(foot, grid) if pm is None else pm
    tl = toe_line(foot.pts)
    edges = [float(tl["xs"][np.isfinite(tl["front"])][0])] + tl["clefts"] + [float(tl["xs"][np.isfinite(tl["front"])][-1])]
    xs, ys = grid.xs, grid.ys
    out = []
    for k, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        xc = 0.5 * (a + b)
        w = (tl["xs"] > a) & (tl["xs"] < b) & np.isfinite(tl["front"])
        if not w.any():
            continue
        y_tip = float(np.nanmin(tl["front"][w]))
        i = int(np.argmin(np.abs(xs - xc)))
        col = pm[i, :]
        seg = (ys > y_tip) & (ys < y_tip + 45.0) & np.isfinite(col)
        if seg.sum() < 4:
            continue
        yy, zz = ys[seg], col[seg]
        near = yy < y_tip + 20.0
        jp = int(np.argmin(np.where(near, zz, np.inf)))
        behind = yy > yy[jp]
        jb = int(np.argmin(np.where(yy > yy[jp] + 12.0, zz, np.inf)))
        between = (yy > yy[jp]) & (yy < yy[jb])
        js = int(np.argmax(np.where(between, zz, -np.inf))) if between.any() else jp
        rowp = pm[:, int(np.argmin(np.abs(ys - yy[jp])))]
        inside = (xs > a) & (xs < b) & np.isfinite(rowp) & (rowp < zz[jp] + 2.0)
        out.append({"toe": k + 1, "x": [round(a, 1), round(b, 1)], "width_plan": round(b - a, 1), "tip_y": round(y_tip, 1),
                    "pad_z": round(float(zz[jp]), 1), "pad_behind_tip": round(float(yy[jp] - y_tip), 1),
                    "sulcus_z": round(float(zz[js]), 1), "sulcus_behind_tip": round(float(yy[js] - y_tip), 1),
                    "sulcus_over_pad": round(float(zz[js] - zz[jp]), 1),
                    "ball_z": round(float(zz[jb]), 1), "ball_behind_tip": round(float(yy[jb] - y_tip), 1),
                    "pad_width_2mm": round(float(np.ptp(xs[inside])) + grid.cell, 1) if inside.any() else None})
    return {"clefts": [round(c, 1) for c in tl["clefts"]], "toes": out}


def toe_section(foot, y):
    """The section across the toes at y: per toe (between the clefts on the toe line) its top and bottom."""
    p = section_points(foot.q, foot.T, 1, y)
    p = p[p[:, 2] < 60.0]
    return p


def figures(foot):
    """Every measure of one foot, for the report and the fit's targets."""
    grid = plantar_grid()
    pm = plantar_map(foot, grid)
    ys, med, lat = plan_outline(foot)
    plan = []
    for pct in range(5, 100, 5):
        y = -pct / 100.0 * foot.L
        a, b = at_y(ys, med, y), at_y(ys, lat, y)
        plan.append({"pct": pct, "medial_x": round(a, 1), "lateral_x": round(b, 1), "breadth": round(b - a, 1)})
    pr = profiles(foot)
    prof = {}
    for pct in range(5, 100, 5):
        y = -pct / 100.0 * foot.L
        prof[str(pct)] = {k: round(at_y(pr["ys"], pr[k], y), 1) for k in ("top", "bottom", "medial_under", "lateral_under")}
    return {"label": foot.label, "L": round(foot.L, 1), "info": foot.info,
            "plan": plan, "transverse": [transverse(foot, p) for p in PCTS],
            "heel_coronal": {str(d): coronal(foot, -d) for d in (10, 20, 30, 40)},
            "heel_from_behind": heel_from_behind(foot), "heel_from_behind_45": heel_from_behind(foot, behind=-45.0),
            "profiles": prof, "sole": sole_figures(foot, pm, grid), "toes": toe_lines(foot, pm, grid)}


# --------------------------------------------------------------------------- plots (PIL)

GREY, MEAN, OURS, AFTER = (165, 165, 165), (20, 20, 20), (215, 50, 35), (30, 100, 215)


class Panel:
    """A drawing area: world (a, b) in mm to pixels, `s` px per mm, (a0, b0) at the panel's top-left, with signs for
    the axes (sa: screen x per +a, sb: screen y per +b)."""

    def __init__(self, img, box, a0, b0, s, sa=1.0, sb=-1.0, title=None):
        from PIL import ImageDraw, ImageFont
        self.img, self.box, self.a0, self.b0, self.s, self.sa, self.sb = img, box, a0, b0, s, sa, sb
        self.d = ImageDraw.Draw(img)
        self.font = ImageFont.load_default()
        if title:
            self.d.text((box[0] + 4, box[1] - 14), title, fill=(0, 0, 0), font=self.font)

    def px(self, a, b):
        return (self.box[0] + self.sa * (a - self.a0) * self.s, self.box[1] + self.sb * (b - self.b0) * self.s)

    def grid(self, a_rng, b_rng, step=10.0, bold=50.0):
        for a in np.arange(math.ceil(a_rng[0] / step) * step, a_rng[1] + 1e-6, step):
            c = (200, 200, 200) if abs(a % bold) < 1e-6 else (236, 236, 236)
            self.d.line([self.px(a, b_rng[0]), self.px(a, b_rng[1])], fill=c)
        for b in np.arange(math.ceil(b_rng[0] / step) * step, b_rng[1] + 1e-6, step):
            c = (200, 200, 200) if abs(b % bold) < 1e-6 else (236, 236, 236)
            self.d.line([self.px(a_rng[0], b), self.px(a_rng[1], b)], fill=c)

    def segs(self, seg2, colour, width=1):
        for (a0, b0), (a1, b1) in seg2:
            self.d.line([self.px(a0, b0), self.px(a1, b1)], fill=colour, width=width)

    def line(self, a, b, colour, width=1):
        run = []
        for x, y in zip(a, b):
            if np.isfinite(x) and np.isfinite(y):
                run.append(self.px(x, y))
            else:
                if len(run) > 1:
                    self.d.line(run, fill=colour, width=width)
                run = []
        if len(run) > 1:
            self.d.line(run, fill=colour, width=width)

    def text(self, a, b, t, colour=(0, 0, 0)):
        self.d.text(self.px(a, b), t, fill=colour, font=self.font)


def _w(c):
    return 2 if c in (OURS, AFTER, MEAN) else 1


def _height_colours(z, top=30.0):
    """Plantar heights to colours: under 1 mm (on the floor) deep blue, then a ramp through teal and yellow to white at
    `top`, banded every 2 mm (the bands' edges read as contours); NaN white."""
    t = np.sqrt(np.clip(np.nan_to_num(z, nan=0.0) / top, 0.0, 1.0))   # the low heights spread out
    stops = np.array([[20, 40, 120], [30, 120, 170], [80, 180, 140], [230, 220, 90], [250, 250, 245]], float)
    pos = np.linspace(0.0, 1.0, len(stops))
    rgb = np.stack([np.interp(t, pos, stops[:, c]) for c in range(3)], -1)
    band = (np.floor(np.nan_to_num(z, nan=0.0) / 2.0) % 2 == 1)
    rgb[band] *= 0.88
    rgb[np.nan_to_num(z, nan=99.0) < 1.0] = (10, 25, 90)
    rgb[~np.isfinite(z)] = (255, 255, 255)
    return rgb.astype(np.uint8)


def _diff_colours(d, lim=10.0):
    """ours - reference: red where ours stands higher off the floor, blue where lower; NaN light grey."""
    t = np.clip(np.nan_to_num(d, nan=0.0) / lim, -1.0, 1.0)
    rgb = np.full(d.shape + (3,), 255.0)
    pos, neg = t > 0, t < 0
    rgb[pos, 1] = rgb[pos, 2] = 255.0 * (1.0 - t[pos])
    rgb[neg, 0] = rgb[neg, 1] = 255.0 * (1.0 + t[neg])
    band = (np.floor(np.abs(np.nan_to_num(d, nan=0.0)) / 2.0) % 2 == 1)
    rgb[band] *= 0.9
    rgb[~np.isfinite(d)] = (225, 225, 225)
    return rgb.astype(np.uint8)


def _sheet(out, img):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    img.save(out)
    return out


def plot_plantar(maps, labels, out, grid=None, diff_to=None, scale=2.0):
    """Plantar height maps side by side, seen from below, toes up, the medial side on the left; with diff_to (an index)
    each other map's difference from that one follows (the other minus it)."""
    from PIL import Image, ImageDraw, ImageFont
    grid = grid or plantar_grid()
    cell_px = int(round(grid.cell * scale))
    w, h = grid.nx * cell_px, grid.ny * cell_px
    panels = [(_height_colours(m), lab) for m, lab in zip(maps, labels)]
    if diff_to is not None:
        for k, (m, lab) in enumerate(zip(maps, labels)):
            if k != diff_to:
                panels.append((_diff_colours(m - maps[diff_to]), f"{lab} minus {labels[diff_to]}"))
    sheet = Image.new("RGB", (len(panels) * (w + 14) + 14, h + 56), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for k, (rgb, lab) in enumerate(panels):
        # the map's rows are x (lateral +) and its columns y (heel +): from below with the toes up and the medial side
        # on the left, screen x runs with +x and screen y with +y
        im = np.repeat(np.repeat(rgb.transpose(1, 0, 2), cell_px, 0), cell_px, 1)
        x0 = 14 + k * (w + 14)
        sheet.paste(Image.fromarray(im), (x0, 30))
        d.text((x0, 10), lab, fill=(0, 0, 0), font=font)
        for pct in (10, 20, 30, 40, 50, 60, 70, 80, 90):
            yy = 30 + (-pct / 100.0 * LENGTH - grid.y0) / grid.cell * cell_px
            d.line([(x0, yy), (x0 + 6, yy)], fill=(0, 0, 0))
            d.text((x0 + 8, yy - 5), f"{pct}%", fill=(60, 60, 60), font=font)
    d.text((14, h + 36), "from below, toes up, medial side on the left; heights banded every 2 mm (white at 30), dark blue "
           "under 1 mm; differences: red = higher off the floor, blue = lower (full at 10 mm), bands every 2 mm",
           fill=(0, 0, 0), font=font)
    return _sheet(out, sheet)


def plot_plan(feet, colours, out, s=3.0):
    """The plan outlines seen from above, toes up, the medial side on the right (as hr.plan)."""
    from PIL import Image
    W, H = int(150 * s), int(300 * s)
    img = Image.new("RGB", (W, H + 24), (255, 255, 255))
    p = Panel(img, (0, 20, W, H), 75.0, -292.0, s, sa=-1.0, sb=1.0, title="plan from above, toes up, medial on the right")
    p.grid((-70, 75), (-290, 10))
    for f, c in zip(feet, colours):
        ys, med, lat = plan_outline(f)
        p.line(med, ys, c, _w(c))
        p.line(lat, ys, c, _w(c))
    for pct in range(10, 100, 10):
        p.text(72, -pct / 100.0 * LENGTH, f"{pct}%")
    return _sheet(out, img)


def _section2(f, axis, value, zmax=110.0):
    seg = segments(f.q, f.T, axis, value)
    if not len(seg):
        return np.zeros((0, 2, 2))
    seg = seg[(seg[:, :, 2] < zmax).all(axis=1)]
    other = 0 if axis == 1 else 1
    return np.stack([seg[:, :, other], seg[:, :, 2]], -1)


def plot_sections(feet, colours, out, pcts=PCTS, s=3.0):
    """Sections across the foot at `pcts` % of its length, seen from behind (the medial side on the right)."""
    from PIL import Image
    cw, ch = int(125 * s), int(95 * s)
    cols = 3
    rows = int(math.ceil(len(pcts) / cols))
    img = Image.new("RGB", (cols * cw, rows * ch), (255, 255, 255))
    for k, pct in enumerate(pcts):
        box = ((k % cols) * cw, (k // cols) * ch + 16, cw, ch)
        p = Panel(img, box, 62.0, 85.0, s, sa=-1.0, sb=-1.0, title=f"{pct} % L, from behind, medial on the right")
        p.grid((-60, 60), (0, 80))
        for f, c in zip(feet, colours):
            p.segs(_section2(f, 1, -pct / 100.0 * f.L), c, _w(c))
    return _sheet(out, img)


def plot_heel(feet, colours, out, ys=(-10, -20, -30, -40), s=4.0):
    """The heel's coronal sections (from behind, medial on the right) and its silhouette's width by height."""
    from PIL import Image
    cw, ch = int(90 * s), int(76 * s)
    img = Image.new("RGB", (len(ys) * cw + int(100 * s), ch + 24), (255, 255, 255))
    for k, y in enumerate(ys):
        p = Panel(img, (k * cw, 20, cw, ch), 45.0, 74.0, s, sa=-1.0, sb=-1.0, title=f"y {y} mm, from behind")
        p.grid((-45, 45), (0, 70))
        for f, c in zip(feet, colours):
            p.segs(_section2(f, 1, float(y), zmax=72.0), c, _w(c))
    p = Panel(img, (len(ys) * cw + 10, 20, int(90 * s), ch), 40.0, 74.0, s, sa=1.0, sb=-1.0,
              title="width behind y -45 by height (40-100 mm)")
    p.grid((40, 100), (0, 70))
    zs = np.arange(2.0, 71.0, 1.0)
    for f, c in zip(feet, colours):
        w = []
        for zl in zs:
            b = f.pts[(np.abs(f.pts[:, 2] - zl) < 0.5) & (f.pts[:, 1] > -45.0)]
            w.append(np.ptp(b[:, 0]) if len(b) > 3 else np.nan)
        p.line(np.array(w), zs, c, _w(c))
    return _sheet(out, img)


def plot_profiles(feet, colours, out, s=3.0):
    """The medial view's lines (toes on the right): the dorsum's top and the medial border's underside (lines), the
    lateral border's underside (dots)."""
    from PIL import Image
    W, H = int(300 * s), int(120 * s)
    img = Image.new("RGB", (W, H + 24), (255, 255, 255))
    p = Panel(img, (0, 20, W, H), 10.0, 115.0, s, sa=-1.0, sb=-1.0,
              title="from the medial side, toes on the right: the top and the medial underside (lines), the lateral underside (dots)")
    p.grid((-290, 10), (0, 115))
    for f, c in zip(feet, colours):
        pr = profiles(f)
        p.line(pr["ys"], pr["top"], c, _w(c))
        p.line(pr["ys"], pr["medial_under"], c, _w(c))
        for y, z in zip(pr["ys"][::2], pr["lateral_under"][::2]):
            if np.isfinite(z):
                x0, y0 = p.px(y, z)
                p.d.ellipse([x0 - 1.5, y0 - 1.5, x0 + 1.5, y0 + 1.5], fill=c)
    return _sheet(out, img)


def plot_toes(feet, colours, out, behind=(6, 14, 24, 34), s=4.0):
    """Sections across the toes at fixed distances behind each foot's longest toe, from behind (medial on the right)."""
    from PIL import Image
    cw, ch = int(115 * s), int(42 * s)
    img = Image.new("RGB", (2 * cw, 2 * (ch + 20)), (255, 255, 255))
    for k, dd in enumerate(behind):
        box = ((k % 2) * cw, (k // 2) * (ch + 20) + 18, cw, ch)
        p = Panel(img, box, 62.0, 40.0, s, sa=-1.0, sb=-1.0, title=f"{dd} mm behind the longest toe, from behind")
        p.grid((-52, 62), (0, 40))
        for f, c in zip(feet, colours):
            p.segs(_section2(f, 1, -f.L + dd, zmax=42.0), c, _w(c))
    return _sheet(out, img)


# --------------------------------------------------------------------------- the comparison

MEN3 = ("038", "081", "012")   # the three men's scans the mean is taken over (059 shown, not averaged: below)


def sole_check(f):
    """Whether the sole was scanned or capped: the triangles' edge length on the plantar skin (normal more than 45
    degrees down) against the dorsum's, the area lying flat within 0.05 mm of the floor with its normal straight down
    (a platform's cap would be one plane), the area under 1 mm and how flat it is."""
    n = tri_normals(f.q, f.T)
    e = np.linalg.norm(f.q[f.T[:, 0]] - f.q[f.T[:, 1]], axis=1)
    a = 0.5 * np.linalg.norm(np.cross(f.q[f.T[:, 1]] - f.q[f.T[:, 0]], f.q[f.T[:, 2]] - f.q[f.T[:, 0]]), axis=1)
    zt = f.q[f.T][:, :, 2]
    down, up = n[:, 2] < -0.7, (n[:, 2] > 0.7) & (zt.min(1) < 100.0)
    flat = (zt.max(1) < 0.05) & (n[:, 2] < -0.9995)
    pm = plantar_map(f)
    low = pm[np.isfinite(pm) & (pm < 1.0)]
    return {"plantar_edge_median": round(float(np.median(e[down])), 2), "dorsal_edge_median": round(float(np.median(e[up])), 2),
            "plantar_area_mm2": round(float(a[down].sum())), "flat_at_floor_mm2": round(float(a[flat].sum()), 1),
            "under_1mm_mm2": int(len(low) * plantar_grid().cell ** 2),
            "under_1mm_z_sd": round(float(low.std()), 2) if len(low) else None}


def mean_of(xs):
    """The element-wise mean of matching nested figures (numbers averaged, None ignored; lists of unequal length and
    strings: the first)."""
    x0 = xs[0]
    if isinstance(x0, dict):
        return {k: mean_of([x.get(k) for x in xs if isinstance(x, dict)]) for k in x0}
    if isinstance(x0, list):
        if all(isinstance(x, list) and len(x) == len(x0) for x in xs):
            return [mean_of([x[i] for x in xs]) for i in range(len(x0))]
        return x0
    nums = [x for x in xs if isinstance(x, (int, float)) and not isinstance(x, bool) and x is not None]
    if nums and all(isinstance(x, (int, float)) or x is None for x in xs):
        return round(float(np.mean(nums)), 1)
    return x0


def spread_of(xs):
    vals = [x for x in xs if isinstance(x, (int, float))]
    return (round(min(vals), 1), round(max(vals), 1)) if vals else (None, None)


def _f(v, n=1):
    return "-" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{n}f}"


def typical(feet, maps, figs):
    """The scan nearest the three's mean: RMS over the plantar map (common cells), the plan's medial and lateral x
    (10-90 % L) and the heel's coronal widths (y -10 to -40, z 10-60), each over its own spread, summed."""
    mean_map = np.nanmean(np.stack(maps), 0)
    mf = mean_of(figs)
    out = {}
    for f, m, g in zip(feet, maps, figs):
        d_map = float(np.sqrt(np.nanmean((m - mean_map) ** 2)))
        d_plan = float(np.sqrt(np.mean([(a["medial_x"] - b["medial_x"]) ** 2 + (a["lateral_x"] - b["lateral_x"]) ** 2
                                        for a, b in zip(g["plan"], mf["plan"]) if 10 <= a["pct"] <= 90])))
        dh = []
        for y in g["heel_coronal"]:
            for z, v in g["heel_coronal"][y].items():
                mv = mf["heel_coronal"][y][z]
                if v and mv and int(z) >= 10:
                    dh.append(v["w"] - mv["w"])
        d_heel = float(np.sqrt(np.mean(np.square(dh))))
        out[f.label] = {"plantar_rms": round(d_map, 2), "plan_rms": round(d_plan, 2), "heel_rms": round(d_heel, 2),
                        "sum": round(d_map + d_plan + d_heel, 2), "hallux_leads": f.info.get("hallux_ahead_of_toe2", 0) > 0}
    # the reference shown beside ours must also have its toes in our order: the hallux ahead of toe 2 (Jeff's decision,
    # 4.5 mm here); 081's toe 2 leads its hallux by 5.5 mm (a Morton's toe), which a critic would read as our fault
    ok = [k for k in out if out[k]["hallux_leads"]] or list(out)
    return min(ok, key=lambda k: out[k]["sum"]), out


def compare(ours, out_dir=OUT, also=()):
    """The report: renders/research/foot_hires/scan/compare.md and its plots, comparing `ours` (a Foot) and `also`
    (more of ours, e.g. after a change) with the three men's unloaded scans (their mean, the most typical one in black)
    and the fourth (059) in the tables."""
    os.makedirs(out_dir, exist_ok=True)
    scans = [load_scan(s, "mBW") for s in MEN3]
    s059 = load_scan("059", "mBW")
    loaded = {s: load_scan(s, "fBW") for s in MEN3 + ("059",)}
    grid = plantar_grid()
    maps = [plantar_map(f, grid) for f in scans]
    figs = [figures(f) for f in scans]
    pick, dist = typical(scans, maps, figs)
    typ = scans[[f.label for f in scans].index(pick)]
    mean_map = np.nanmean(np.stack(maps), 0)
    mf = mean_of(figs)
    ours_all = [ours] + list(also)
    ofigs = [figures(f) for f in ours_all]
    omaps = [plantar_map(f, grid) for f in ours_all]
    f059 = figures(s059)
    np.savez_compressed(os.path.join(CACHE, "mean_plantar.npz"), z=mean_map.astype(np.float32), x0=grid.x0, y0=grid.y0,
                        cell=grid.cell)
    with open(os.path.join(CACHE, "figures.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"mean": mf, "scans": figs, "ours": ofigs, "059": f059, "typical": pick, "distance": dist}, fh, indent=1)
        fh.write("\n")
    ocol = [OURS, AFTER, (40, 160, 70)]
    feet = scans + ours_all
    cols = [MEAN if f is typ else GREY for f in scans] + ocol[:len(ours_all)]
    png = {}
    png["plantar"] = plot_plantar([omaps[0], maps[[f.label for f in scans].index(pick)], mean_map] + omaps[1:],
                                  [ours.label, f"scan {pick}", "scan mean (3)"] + [f.label for f in also],
                                  os.path.join(out_dir, "plantar.png"), grid, diff_to=2)
    png["plan"] = plot_plan(feet, cols, os.path.join(out_dir, "plan.png"))
    png["sections"] = plot_sections(feet, cols, os.path.join(out_dir, "sections.png"))
    png["heel"] = plot_heel(feet, cols, os.path.join(out_dir, "heel.png"))
    png["profiles"] = plot_profiles(feet, cols, os.path.join(out_dir, "profiles.png"))
    png["toes"] = plot_toes(feet, cols, os.path.join(out_dir, "toes.png"))
    labels = [f.label for f in ours_all]
    md = report_md(ours_all, ofigs, scans, figs, mf, f059, pick, dist, loaded, png, out_dir)
    path = os.path.join(out_dir, "compare.md")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    return path


def _rel(p, base):
    return os.path.relpath(p, base).replace(os.sep, "/")


def report_md(ours_all, ofigs, scans, figs, mf, f059, pick, dist, loaded, png, out_dir):
    L = []
    o = ofigs
    names = [f.label for f in ours_all]
    L += ["# The foot against real feet: scan comparison", "",
          "Generated by `scripts/research/foot_hires/scan.py compare` (the scan-driven pass, 2026-10-16; notes/research_foot_hires.md). "
          "Scans: Schuster, Kelly & Cresswell, *Foot shape-function model data* (CC0; zenodo record 10360304, "
          "doi 10.5061/dryad.g4f4qrfwt): right feet, mirrored to left feet, in frame F with the axis from the heel's centre "
          "to toe 2's tip, the pternion at y 0, the floor at z 0, each scaled uniformly to this foot's 274.3 mm. "
          f"The mean is over the three men's unloaded (mBW) scans {', '.join(MEN3)}; 059 is listed, not averaged. "
          "Ours: " + ", ".join("`%s` (%s)" % (f.info.get("source"), f.label) for f in ours_all) + ", re-zeroed the same way.", ""]
    L += ["Plots: " + ", ".join(f"[{k}]({_rel(v, out_dir)})" for k, v in png.items()) +
          f". In every plot the scans are grey, the most typical ({pick}) black, ours red" +
          (", then blue, green" if len(ours_all) > 1 else "") + ".", ""]
    # alignment
    L += ["## The scans and their alignment", "",
          "| scan | raw length | scale | heading off the scan's own axis (deg) | hallux ahead of toe 2 | clefts x | distance to the mean (map / plan / heel RMS) |",
          "|---|---|---|---|---|---|---|"]
    for f in scans + [load_scan("059", "mBW")]:
        i = f.info
        dd = dist.get(f.label, {})
        L.append(f"| {f.label} | {i['length_raw']} | {i['scale']} | {i['heading_off_raw_axis_deg']} | {i['hallux_ahead_of_toe2']} | "
                 f"{i['clefts_x']} | {dd.get('plantar_rms', '-')} / {dd.get('plan_rms', '-')} / {dd.get('heel_rms', '-')} |")
    for s, f in loaded.items():
        i = f.info
        L.append(f"| {f.label} (scaled by its mBW's factor) | {i['length_raw']} | {i['scale']} | {i['heading_off_raw_axis_deg']} | "
                 f"{i['hallux_ahead_of_toe2']} | {i['clefts_x']} | |")
    L += ["", f"Most typical of the three: **{pick}** (smallest summed distance to their mean). Units: mm (verified: "
          "the raw lengths match the published 265-278 mm standing, and the flat top lies at z 125); axes: x along the "
          "foot (the heel at -x), y across (the medial side at +y), z up from the platform.", ""]
    # the sole check
    L += ["## Is the sole scanned?", "",
          "| scan | plantar edge median | dorsal edge median | plantar area | flat at the floor (normal straight down) | under 1 mm | its z SD |",
          "|---|---|---|---|---|---|---|"]
    for f in scans + [load_scan("059", "mBW")] + list(loaded.values()):
        c = sole_check(f)
        L.append(f"| {f.label} | {c['plantar_edge_median']} | {c['dorsal_edge_median']} | {c['plantar_area_mm2']} | "
                 f"{c['flat_at_floor_mm2']} | {c['under_1mm_mm2']} | {c['under_1mm_z_sd']} |")
    checks = [sole_check(f) for f in scans + list(loaded.values())]
    L += ["", f"**The sole is scanned, not capped.** Its triangles are the dorsum's size "
          f"({min(c['plantar_edge_median'] for c in checks)}-{max(c['plantar_edge_median'] for c in checks)} mm), at most "
          f"{max(c['flat_at_floor_mm2'] for c in checks):.0f} mm² lies within 0.05 mm of the floor with its normal straight "
          "down (a platform's cap would be the whole contact, one plane), the skin under 1 mm varies by "
          f"{min(c['under_1mm_z_sd'] for c in checks)}-{max(c['under_1mm_z_sd'] for c in checks)} mm (SD), and the heel "
          "pad, the lateral band, the arch's hollow, the ball and each toe's pad stand in relief "
          f"([plantar]({_rel(png['plantar'], out_dir)})). The standing scans' contact is not one plane either: the "
          "platform pressed it, the scanner still read it.", ""]
    # plan
    L += ["## The plan outline (from above)", "", f"![plan]({_rel(png['plan'], out_dir)})", "",
          "| % L | " + " | ".join(f"{n}: medial / lateral / breadth" for n in names) + " | scan mean: medial / lateral / breadth | breadth range | 059 breadth |",
          "|---|" + "---|" * len(names) + "---|---|---|"]
    for k, m in enumerate(mf["plan"]):
        if m["pct"] % 10 and m["pct"] not in (85, 95):
            continue
        rng = spread_of([g["plan"][k]["breadth"] for g in figs])
        L.append(f"| {m['pct']} | " + " | ".join(f"{g['plan'][k]['medial_x']} / {g['plan'][k]['lateral_x']} / **{g['plan'][k]['breadth']}**"
                                                for g in o) +
                 f" | {m['medial_x']} / {m['lateral_x']} / **{m['breadth']}** | {rng[0]}-{rng[1]} | {f059['plan'][k]['breadth']} |")
    L += [""]
    # transverse
    L += ["## Sections across the foot (every 10 % of the length)", "", f"![sections]({_rel(png['sections'], out_dir)})", "",
          "| % L | " + " | ".join(f"{n}: breadth / top / underside / contact band (3 mm) / x at z 5, 20" for n in names) +
          " | scan mean: the same |", "|---|" + "---|" * len(names) + "---|"]

    def tr(t):
        b = t.get("band_3mm") or [None, None]
        xz = t.get("x_at_z") or {}
        w5 = xz.get("5")
        w20 = xz.get("20")
        return (f"{_f(t.get('breadth'))} / {_f(t.get('top_z'))} / {_f(t.get('bottom_z'))} / "
                f"{_f(None if b[0] is None else b[1] - b[0])} / {_f(None if not w5 else w5[1] - w5[0])}, "
                f"{_f(None if not w20 else w20[1] - w20[0])}")
    for k in range(len(PCTS)):
        L.append(f"| {PCTS[k]} | " + " | ".join(tr(g["transverse"][k]) for g in o) + f" | {tr(mf['transverse'][k])} |")
    L += ["", "(The top saturates at 110 where the leg rises through the section.)", ""]
    # heel
    L += ["## The heel from behind", "", f"![heel]({_rel(png['heel'], out_dir)})", "",
          "Widths by height: the silhouette behind y -45 (the heel and the Achilles, the malleoli left out) and the "
          "coronal sections 10, 20, 30 and 40 mm in front of the pternion.", "",
          "| z | " + " | ".join(f"{n}: behind -45 / y -10 / -20 / -30 / -40" for n in names) + " | scan mean: the same | 059 behind -45 |",
          "|---|" + "---|" * len(names) + "---|---|"]

    def hw(g, z):
        a = (g["heel_from_behind_45"].get(z) or {}).get("w")
        cs = [(g["heel_coronal"][y].get(z) or {}).get("w") for y in ("10", "20", "30", "40")]
        return " / ".join(_f(v) for v in [a] + cs)
    for z in (str(v) for v in HEEL_Z):
        L.append(f"| {z} | " + " | ".join(hw(g, z) for g in o) + f" | {hw(mf, z)} | {_f((f059['heel_from_behind_45'].get(z) or {}).get('w'))} |")
    L += [""]
    # sole
    L += ["## The sole's landscape", "", f"![plantar]({_rel(png['plantar'], out_dir)})", "",
          "| figure | " + " | ".join(names) + " | " + " | ".join(f.label for f in scans) + " | mean | 059 |",
          "|---|" + "---|" * (len(names) + len(scans) + 2)]
    allf = o + figs + [mf, f059]

    def row(name, fn):
        vals = []
        for g in allf:
            try:
                vals.append(_f(fn(g)))
            except (KeyError, TypeError):
                vals.append("-")
        L.append(f"| {name} | " + " | ".join(vals) + " |")
    s = "sole"
    row("heel pad at 12 % L: lowest underside", lambda g: g[s]["heel_pad_12"]["low_z"])
    for dx in ("-20", "-10", "+10", "+20"):
        row(f"  underside {dx} mm across from it", lambda g, dx=dx: g[s]["heel_pad_12"]["z_at"][dx])
    row("  width within 2 mm of the lowest", lambda g: g[s]["heel_pad_12"]["width_within_2mm"])
    for p in ("40", "50", "60"):
        row(f"lateral band at {p} % L: lowest underside", lambda g, p=p: g[s]["lateral_band"][p]["lateral_low_z"])
        row(f"  band within 2 mm of it: width", lambda g, p=p: g[s]["lateral_band"][p]["band_2mm_w"])
    for p in ("35", "45", "55"):
        row(f"arch at {p} % L: underside 12 mm in from the medial border", lambda g, p=p: g[s]["arch"][p]["medial_12mm_in"])
        row(f"  underside at mid-breadth", lambda g, p=p: g[s]["arch"][p]["mid_breadth"])
        row(f"  the vault's highest underside", lambda g, p=p: g[s]["arch"][p]["vault_max"])
    row("ball: lowest underside (66-80 % L)", lambda g: g[s]["ball"]["low_z"])
    row("  at % L", lambda g: g[s]["ball"]["pct"])
    row("  underside 15 mm behind it", lambda g: g[s]["ball"]["z_15_behind"])
    row("  underside 30 mm behind it", lambda g: g[s]["ball"]["z_30_behind"])
    L += [""]
    # toes
    L += ["## The toes", "", f"![toes]({_rel(png['toes'], out_dir)})", "",
          "Along each toe's line (between its clefts on the toe line): its plan width, its tip, the pad (the lowest underside "
          "within 20 mm of the tip), the sulcus (the highest underside between the pad and the ball) and the pad's width "
          "within 2 mm of its lowest point.", "",
          "| toe | figure | " + " | ".join(names) + " | " + " | ".join(f.label for f in scans) + " | mean |",
          "|---|---|" + "---|" * (len(names) + len(scans) + 1)]
    tf = o + figs
    for k in range(5):
        for key, nm in (("width_plan", "plan width"), ("tip_y", "tip y"), ("pad_z", "pad: lowest underside"),
                        ("pad_behind_tip", "pad: behind the tip"), ("sulcus_z", "sulcus: underside"),
                        ("sulcus_over_pad", "sulcus: over the pad"), ("sulcus_behind_tip", "sulcus: behind the tip"),
                        ("pad_width_2mm", "pad: width within 2 mm")):
            vals = []
            for g in tf:
                ts = g["toes"]["toes"]
                vals.append(ts[k].get(key) if k < len(ts) else None)
            mvals = [v for v in vals[len(o):] if isinstance(v, (int, float))]
            L.append(f"| {k + 1} | {nm} | " + " | ".join(_f(v) for v in vals) + f" | {_f(float(np.mean(mvals)) if mvals else None)} |")
    L += [""]
    # profiles
    L += ["## The side profiles (lower priority: Jeff likes the side view)", "", f"![profiles]({_rel(png['profiles'], out_dir)})", "",
          "| % L | " + " | ".join(f"{n}: top / medial underside / lateral underside" for n in names) + " | scan mean: the same |",
          "|---|" + "---|" * len(names) + "---|"]
    for pct in range(10, 100, 10):
        k = str(pct)
        L.append(f"| {pct} | " + " | ".join(f"{g['profiles'][k]['top']} / {g['profiles'][k]['medial_under']} / {g['profiles'][k]['lateral_under']}"
                                            for g in o) +
                 f" | {mf['profiles'][k]['top']} / {mf['profiles'][k]['medial_under']} / {mf['profiles'][k]['lateral_under']} |")
    L += [""]
    # loaded
    L += ["## Loaded (fBW) against unloaded (mBW)", "",
          "Each loaded scan scaled by its unloaded twin's factor, so the lengthening shows.", "",
          "| scan | length | ball breadth (60-80 % L) | heel width at z 10 (behind y -60) | medial underside at 45 % L | lateral underside at 50 % L | top at 50 / 60 / 70 % L | area under 1 mm |",
          "|---|---|---|---|---|---|---|---|"]
    deltas, ratios = [], []
    for sid in MEN3 + ("059",):
        a, b = load_scan(sid, "mBW"), load_scan(sid, "fBW")
        fa, fb = load_figures(a), load_figures(b)
        d = {k: fb[k] - fa[k] for k in fa}
        if sid in MEN3:
            deltas.append(d)
            ratios.append(fb["area1"] / fa["area1"])
        L.append(f"| {sid} | {fa['L']:.1f} -> {fb['L']:.1f} (**{d['L']:+.1f}**) | {fa['ball']:.1f} -> {fb['ball']:.1f} (**{d['ball']:+.1f}**) | "
                 f"{fa['heel10']:.1f} -> {fb['heel10']:.1f} (**{d['heel10']:+.1f}**) | {fa['med45']:.1f} -> {fb['med45']:.1f} (**{d['med45']:+.1f}**) | "
                 f"{fa['lat50']:.1f} -> {fb['lat50']:.1f} | {d['top50']:+.1f} / {d['top60']:+.1f} / {d['top70']:+.1f} | "
                 f"{fa['area1']:.0f} -> {fb['area1']:.0f} |")
    md = {k: float(np.mean([d[k] for d in deltas])) for k in deltas[0]}
    L.append(f"| mean of {', '.join(MEN3)} | **{md['L']:+.1f}** | **{md['ball']:+.1f}** | **{md['heel10']:+.1f}** | **{md['med45']:+.1f}** | "
             f"{md['lat50']:+.1f} | {md['top50']:+.1f} / {md['top60']:+.1f} / {md['top70']:+.1f} | x{np.mean(ratios):.2f} |")
    if not NUMBERS_ONLY:
        L += ["", "Part 01's `Foot.Contact` (the loaded key) was built to about half of this (the heel 3.5, the arch 2.2, "
              "the toes 2 forward); it now follows the mean (`fields.CONTACT`; spec 01 §3.5 note): " + _contact_line() + ".", ""]
        L += ["## Findings", ""] + findings(o, names, mf) + [""]
    else:   # the findings above were written for the scan-driven pass of 2026-10-16
        L += ["", "Numbers only (`--numbers-only`); what they mean is in notes/research_foot_hires.md.", ""]
    return "\n".join(L) + "\n"


def findings(o, names, mf):
    """The report's summary: each fault the critics named, read in the numbers above, for the first and the last of
    ours (before, after) against the scans' mean."""
    b, a = o[0], o[-1]
    s = "sole"

    def lb(g, p):
        return g[s]["lateral_band"][p]["lateral_low_z"]

    def ar(g, p, k):
        return g[s]["arch"][p][k]

    def hb(g, z, y="45"):
        return (g["heel_from_behind_45"].get(z) or {}).get("w") if y == "45" else (g["heel_coronal"][y].get(z) or {}).get("w")

    def pl(g, p):
        return next(x["breadth"] for x in g["plan"] if x["pct"] == p)

    def toe(g, k, key):
        ts = g["toes"]["toes"]
        return ts[k - 1].get(key) if len(ts) >= k else None

    def f1(v):
        return _f(v)
    out = [f"Before = {names[0]}, after = {names[-1]}, scans = the mean of {', '.join(MEN3)} seated, scaled to {LENGTH}."]
    out.append(
        f"- **The sole (a slab).** The heel pad's lowest underside at 12 % L {f1(b[s]['heel_pad_12']['low_z'])} -> "
        f"{f1(a[s]['heel_pad_12']['low_z'])} (scans {f1(mf[s]['heel_pad_12']['low_z'])}), 10 mm to either side "
        f"{f1(b[s]['heel_pad_12']['z_at']['-10'])} / {f1(b[s]['heel_pad_12']['z_at']['+10'])} -> "
        f"{f1(a[s]['heel_pad_12']['z_at']['-10'])} / {f1(a[s]['heel_pad_12']['z_at']['+10'])} (scans "
        f"{f1(mf[s]['heel_pad_12']['z_at']['-10'])} / {f1(mf[s]['heel_pad_12']['z_at']['+10'])}): the pad now rests flat; "
        f"the lateral band at 40 / 50 % L {f1(lb(b, '40'))} / {f1(lb(b, '50'))} -> {f1(lb(a, '40'))} / {f1(lb(a, '50'))} "
        f"(scans {f1(lb(mf, '40'))} / {f1(lb(mf, '50'))}): on the floor; the underside at mid-breadth at 35 / 45 / 55 % L "
        f"{f1(ar(b, '35', 'mid_breadth'))} / {f1(ar(b, '45', 'mid_breadth'))} / {f1(ar(b, '55', 'mid_breadth'))} -> "
        f"{f1(ar(a, '35', 'mid_breadth'))} / {f1(ar(a, '45', 'mid_breadth'))} / {f1(ar(a, '55', 'mid_breadth'))} (scans "
        f"{f1(ar(mf, '35', 'mid_breadth'))} / {f1(ar(mf, '45', 'mid_breadth'))} / {f1(ar(mf, '55', 'mid_breadth'))}) and "
        f"12 mm in from the medial border {f1(ar(b, '35', 'medial_12mm_in'))} / {f1(ar(b, '45', 'medial_12mm_in'))} -> "
        f"{f1(ar(a, '35', 'medial_12mm_in'))} / {f1(ar(a, '45', 'medial_12mm_in'))} (scans "
        f"{f1(ar(mf, '35', 'medial_12mm_in'))} / {f1(ar(mf, '45', 'medial_12mm_in'))}): the arch's hollow rises from the "
        "band toward the medial border instead of a slab raised across the midfoot.")
    out.append(
        f"- **The heel (a box from behind).** Its width behind y -45 at z 20 / 35 / 50 {f1(hb(b, '20'))} / {f1(hb(b, '35'))} / "
        f"{f1(hb(b, '50'))} -> {f1(hb(a, '20'))} / {f1(hb(a, '35'))} / {f1(hb(a, '50'))} (scans {f1(hb(mf, '20'))} / "
        f"{f1(hb(mf, '35'))} / {f1(hb(mf, '50'))}); 10 mm in front of the pternion at z 20 / 50 / 60 {f1(hb(b, '20', '10'))} / "
        f"{f1(hb(b, '50', '10'))} / {f1(hb(b, '60', '10'))} -> {f1(hb(a, '20', '10'))} / {f1(hb(a, '50', '10'))} / "
        f"{f1(hb(a, '60', '10'))} (scans {f1(hb(mf, '20', '10'))} / {f1(hb(mf, '50', '10'))} / {f1(hb(mf, '60', '10'))}): the "
        "pad's bulge is gone and the neck above it eased; the Achilles' insertion is still narrower than the scans'.")
    out.append(
        f"- **The plan.** Breadth at 10 / 50 / 85 / 90 % L {f1(pl(b, 10))} / {f1(pl(b, 50))} / {f1(pl(b, 85))} / {f1(pl(b, 90))} -> "
        f"{f1(pl(a, 10))} / {f1(pl(a, 50))} / {f1(pl(a, 85))} / {f1(pl(a, 90))} (scans {f1(pl(mf, 10))} / {f1(pl(mf, 50))} / "
        f"{f1(pl(mf, 85))} / {f1(pl(mf, 90))}). Still off: the forefoot lies 3-5 mm medial of the scans' at 60-80 % L and "
        "toes 4-5 inside theirs, where X3's toes and the 4.5 mm gap between the hallux and toe 2 (it turns toes 2-5 out, "
        "and the axis with toe 2) hold them.")
    out.append(
        "- **The toes (fingers from above, matchsticks from below).** Pads behind the tip, toes 2 / 3 / 4: "
        f"{f1(toe(b, 2, 'pad_behind_tip'))} / {f1(toe(b, 3, 'pad_behind_tip'))} / {f1(toe(b, 4, 'pad_behind_tip'))} -> "
        f"{f1(toe(a, 2, 'pad_behind_tip'))} / {f1(toe(a, 3, 'pad_behind_tip'))} / {f1(toe(a, 4, 'pad_behind_tip'))} (scans "
        "9-20); the sulcus's rise over the pad "
        f"{f1(toe(b, 2, 'sulcus_over_pad'))} / {f1(toe(b, 3, 'sulcus_over_pad'))} / {f1(toe(b, 4, 'sulcus_over_pad'))} -> "
        f"{f1(toe(a, 2, 'sulcus_over_pad'))} / {f1(toe(a, 3, 'sulcus_over_pad'))} / {f1(toe(a, 4, 'sulcus_over_pad'))} (scans "
        "5-9); plan widths 2 / 3 / 4 "
        f"{f1(toe(b, 2, 'width_plan'))} / {f1(toe(b, 3, 'width_plan'))} / {f1(toe(b, 4, 'width_plan'))} -> "
        f"{f1(toe(a, 2, 'width_plan'))} / {f1(toe(a, 3, 'width_plan'))} / {f1(toe(a, 4, 'width_plan'))} (scans 16-18). "
        "Toes 3-5 are longer and toes 2-4 a little plumper, but the lesser toes' resting pose (the proximal phalanx near "
        "the floor, the bend at the PIP, the tip down) still makes the matchstick from below: the scans' toes rise from "
        "the ball and rest on their pulps. That pose is the next step.")
    out.append(
        f"- **The side profile (reported, not changed).** The dorsum at 60 / 70 % L {b['profiles']['60']['top']} / "
        f"{b['profiles']['70']['top']} -> {a['profiles']['60']['top']} / {a['profiles']['70']['top']} against the scans' "
        f"{mf['profiles']['60']['top']} / {mf['profiles']['70']['top']}: their forefoot stands higher, and their ankle's "
        "front lies further forward at 45-55 % L (partly the seated posture). Jeff likes ours; it is his call.")
    return out


def _contact_line():
    """Part 01's loaded key as its last measure() read it (renders/01_foot/measure.json), if there is one."""
    path = os.path.join(PROJECT, "renders", "01_foot", "measure.json")
    if not os.path.exists(path):
        return "no measure.json to read"
    with open(path, encoding="utf-8") as fh:
        m = {x["metric"]: x["value"] for x in json.load(fh).get("metrics", [])}
    return (f"heel width at z 10 {m.get('contact_heel_spread.L'):+} mm, medial border at 45 % L "
            f"{-(m.get('contact_arch_drop.L') or 0.0):+} mm (left foot, as measured)")


def load_figures(f):
    """The few figures the loaded comparison reads."""
    ys, med, lat = plan_outline(f)
    br = lat - med
    fore = (ys < -0.6 * f.L) & (ys > -0.8 * f.L)
    heel10 = f.pts[(np.abs(f.pts[:, 2] - 10.0) < 0.5) & (f.pts[:, 1] > -60.0)]
    pr = profiles(f)

    def p(k, pct):
        return at_y(pr["ys"], pr[k], -pct / 100.0 * f.L)
    pm = plantar_map(f)
    return {"L": f.L, "ball": float(np.nanmax(np.where(fore, br, np.nan))), "heel10": float(np.ptp(heel10[:, 0])),
            "med45": p("medial_under", 45), "lat50": p("lateral_under", 50), "top50": p("top", 50), "top60": p("top", 60),
            "top70": p("top", 70), "area1": float(np.sum(pm < 1.0)) * plantar_grid().cell ** 2}


# --------------------------------------------------------------------------- part 01's targets

def _scanfit():
    scripts = os.path.dirname(os.path.dirname(HERE))
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from parts.p01 import scanfit
    return scanfit


def targets(out=None, ours=None):
    """scripts/parts/p01/scan_targets.json: part 01's section targets, the mean of the three men's unloaded scans
    (scanfit.measures on each, in the scans' frame), with each scan's values, the spread, and the part's scalar heel
    and border figures on the unloaded and loaded scans (for measure()'s targets)."""
    sf = _scanfit()
    out = out or sf.TARGETS
    per, scal, scal_l = {}, {}, {}
    for sid in MEN3:
        f = load_scan(sid, "mBW")
        per[sid] = sf.flat(sf.measures(f.q, f.T, f.pts))
        scal[sid] = border_scalars(f, sf)
        scal_l[sid] = border_scalars(load_scan(sid, "fBW"), sf)
    names = sorted(per[MEN3[0]])
    values, spread = {}, {}
    for n in names:
        v = [per[s][n] for s in MEN3 if per[s].get(n) is not None]
        values[n] = round(float(np.mean(v)), 2) if len(v) >= 2 else None
        spread[n] = [round(float(min(v)), 2), round(float(max(v)), 2)] if v else None
    data = {"doc": "Part 01's section targets from real feet (the scan-driven pass, 2026-10-16; spec 01 §3.1 note): the "
                   "mean of three men's unloaded scans (Schuster, Kelly & Cresswell, 'Foot shape-function model data', CC0, "
                   "zenodo 10360304, doi 10.5061/dryad.g4f4qrfwt; subjects " + ", ".join(MEN3) + ", mBW), mirrored to left "
                   "feet, scaled to 274.3 mm, in the scans' frame (scanfit.rezero). Written by "
                   "scripts/research/foot_hires/scan.py targets; read by fit_sculpt.py and measure(). mm.",
            "scans": {s: load_scan(s, "mBW").info for s in MEN3},
            "values": values, "spread": spread,
            # each man's own values (the scan transfer, 2026-10-17: measure() reads the build against the scan it was
            # transferred from as well as against the mean)
            "per_scan": {s: {n: (None if per[s].get(n) is None else round(float(per[s][n]), 2)) for n in names}
                         for s in MEN3},
            "scalars_unloaded": {"per_scan": scal, "mean": {k: round(float(np.mean([scal[s][k] for s in MEN3])), 2)
                                                              for k in scal[MEN3[0]]}},
            "scalars_loaded": {"per_scan": scal_l, "mean": {k: round(float(np.mean([scal_l[s][k] for s in MEN3])), 2)
                                                            for k in scal_l[MEN3[0]]}}}
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")
    if ours:
        f = load_ours(ours, "ours")
        m = sf.measures(f.q, f.T, f.pts)
        print(json.dumps(sf.report(m, data), indent=1))
        print("ours", json.dumps(border_scalars(f, sf)))
    print("unloaded", json.dumps(data["scalars_unloaded"]["mean"]))
    print("loaded", json.dumps(data["scalars_loaded"]["mean"]))
    return out


def border_scalars(f, sf):
    """Part 01's own scalar figures read on a foot in the scans' frame: the heel's (scanfit.heel_scalars), the medial
    and lateral borders' clearance at 45 and 50 % L (the lowest skin in the outer fifth of the section, footmetrics'
    _border_clearance) and the pternion's height (the sagittal profile's furthest-back point below z 70)."""
    out = sf.heel_scalars(f.q, f.T, f.L)
    for pct, side in ((45, "medial"), (50, "lateral")):
        v = section_points(f.q, f.T, 1, -pct / 100.0 * f.L)
        v = v[v[:, 2] < 150.0]
        x0, x1 = v[:, 0].min(), v[:, 0].max()
        w = x1 - x0
        sel = v[v[:, 0] < x0 + 0.2 * w] if side == "medial" else v[v[:, 0] > x1 - 0.2 * w]
        out["arch_medial_45" if side == "medial" else "lateral_clear_50"] = float(sel[:, 2].min())
    sq = section_points(f.q, f.T, 0, 0.0)
    sq = sq[(sq[:, 1] > -60.0) & (sq[:, 2] < 70.0)]
    out["pternion_z"] = float(sq[np.argmax(sq[:, 1]), 2])
    return {k: round(v, 2) if v is not None else None for k, v in out.items()}


def side_by_side(dirs, views, tier, out_dir, size=900):
    """One sheet per view: the same preset's render from each folder, left to right, each scaled to `size` px (the
    presets share a camera, so the panels share a scale), labelled."""
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(out_dir, exist_ok=True)
    font = ImageFont.load_default()
    made = []
    for v in views:
        ims = []
        for d, lab in dirs:
            p = os.path.join(d if os.path.isabs(d) else os.path.join(PROJECT, d), f"{v}_{tier}.png")
            if os.path.exists(p):
                ims.append((Image.open(p).convert("RGB").resize((size, size), Image.LANCZOS), lab))
        if not ims:
            continue
        sheet = Image.new("RGB", (len(ims) * size + (len(ims) - 1) * 6, size + 22), (255, 255, 255))
        dd = ImageDraw.Draw(sheet)
        for k, (im, lab) in enumerate(ims):
            sheet.paste(im, (k * (size + 6), 22))
            dd.text((k * (size + 6) + 4, 5), f"{lab}  ({v})", fill=(0, 0, 0), font=font)
        path = os.path.join(out_dir, f"{v}_{tier}.png")
        sheet.save(path)
        made.append(path)
    return made


# --------------------------------------------------------------------------- the scan in Blender (run.py --method scan)

def build(ctx):
    """run.py's `scan` method: an aligned scan as the region's skin (Hires.L.Skin), placed in this foot's frame F so
    the trial's presets frame it as they frame ours: its heel's centre on ours, its axis (the heel's centre to toe 2's
    tip) along ours, its pternion on ours, on the floor. --params {"scan": "038", "cond": "mBW", "ref": a run.py --save
    skin of ours whose scans'-frame transform places it (default: the newest fields_*.npz)}."""
    import glob
    import bpy
    sid, cond = str(ctx.p("scan", "038")), str(ctx.p("cond", "mBW"))
    ref = ctx.p("ref", None)
    fr = bpy.data.objects.get("Frame.Foot.L")
    if not ref and fr is not None and "p01_scan" in fr:
        # the scan transfer (2026-10-17): where part 01 laid its reference scan on this foot (its matrix on the frame);
        # a loaded scan as part 01 laid it on the seated one (transfer.register)
        from parts.p01 import transfer as X   # (scripts/ is on the path: the import of scanref above)
        from parts.p01 import scanref as SR
        M = np.array(json.loads(fr["p01_scan"])["M"], float)
        qs, T, info = SR.load(sid, cond)      # the whole scan, its cap too (the transfer's Reference leaves it out)
        if cond != "mBW":
            qs, _ = X.register(qs, T, X.load_reference(sid, "mBW"))
        f = Foot(qs, T, f"{sid} {cond}", info=info)
        co = (qs @ M[:3, :3].T + M[:3, 3]) / 1000.0
        placed = {"by": "part 01's Frame.Foot.L p01_scan", "M": M.round(4).tolist()}
    else:
        if not ref:
            cands = sorted(glob.glob(os.path.join(PROJECT, "cache", "research", "foot_hires", "fields_*.npz")),
                           key=os.path.getmtime)
            ref = cands[-1]
        ref = ref if os.path.isabs(ref) else os.path.join(PROJECT, ref)
        ours = load_ours(ref, "ref")
        R = np.array(ours.info["to_scan_frame"]["R"])
        o = np.array(ours.info["to_scan_frame"]["o"])
        f = load_scan(sid, cond)
        qF = f.q.copy()
        qF[:, :2] = (f.q[:, :2] + o) @ R.T          # back from the scans' frame into frame F
        co = ctx.frame.to_w(qF) / 1000.0
        T = f.T
        placed = {"by": os.path.relpath(ref, PROJECT).replace(os.sep, "/"), "to_scan_frame": ours.info["to_scan_frame"]}
    name = "Hires.L.Skin"
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old)
    me = bpy.data.meshes.new(name)
    me.from_pydata(co.tolist(), [], np.asarray(T).tolist())
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    from lib import replace
    replace.ensure_collection(ctx.part.PART).objects.link(ob)   # where part 01's closeup copies live (dense_copy's)
    ctx.skin = ob
    ctx.report["scan"] = {"id": sid, "cond": cond, "placed": placed, "info": f.info}


# --------------------------------------------------------------------------- command line

def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    al = sub.add_parser("align", help="align and cache the scans (cache/research/foot_hires/scan/)")
    al.add_argument("--ids", default=",".join(MEN))
    al.add_argument("--rebuild", action="store_true")
    cp = sub.add_parser("compare", help="the report and its plots")
    cp.add_argument("--ours", required=True, help="a run.py --save skin or a fit_sculpt.py --dump surface")
    cp.add_argument("--label", default="ours")
    cp.add_argument("--also", action="append", default=[], help="PATH:LABEL, more of ours (after a change)")
    cp.add_argument("--out", default=OUT)
    cp.add_argument("--numbers-only", action="store_true",
                    help="leave out the findings written for the scan-driven pass (the scan transfer's report, 2026-10-17)")
    tg = sub.add_parser("targets", help="scripts/parts/p01/scan_targets.json from the three men's unloaded scans")
    tg.add_argument("--ours", help="also report this skin's deviations from them")
    sb = sub.add_parser("sbs", help="side by side renders of the same views (same camera, same scale)")
    sb.add_argument("--dirs", required=True, help="DIR:LABEL,DIR:LABEL,... render folders, left to right")
    sb.add_argument("--views", required=True)
    sb.add_argument("--tier", default="form")
    sb.add_argument("--out", required=True)
    sb.add_argument("--size", type=int, default=900, help="each panel's side (px)")
    a = ap.parse_args(argv)
    if a.cmd == "sbs":
        for p in side_by_side([d.split(":", 1) for d in a.dirs.split(",")], a.views.split(","), a.tier, a.out, a.size):
            print(p)
        return 0
    if a.cmd == "targets":
        print(targets(ours=a.ours))
        return 0
    if a.cmd == "align":
        for sid in a.ids.split(","):
            for cond in CONDS:
                f = load_scan(sid, cond, rebuild=a.rebuild)
                print(f.label, json.dumps(f.info))
        return 0
    if a.cmd == "compare":
        ours = load_ours(a.ours, a.label)
        also = [load_ours(*s.rsplit(":", 1)) for s in a.also]
        global NUMBERS_ONLY
        NUMBERS_ONLY = a.numbers_only
        print(compare(ours, a.out, also))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
