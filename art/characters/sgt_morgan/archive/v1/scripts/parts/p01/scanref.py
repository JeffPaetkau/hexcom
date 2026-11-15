"""Real feet as part 01's reference surface (the scan transfer, 2026-10-17; spec 01 §0 note of that date).

The scans: Schuster, Kelly & Cresswell, "Foot shape-function model data" (CC0; zenodo 10360304, doi
10.5061/dryad.g4f4qrfwt), assets/scans/zenodo_10360304/ply/ (scripts/setup/downloads.json, group "scans"): ASCII PLY
from MeshMixer, millimetres, right feet cut flat 125 mm above the floor, two per subject: mBW seated at about a tenth
of the body's weight (near-unloaded: the rest shape) and fBW standing at full weight on a platform.

Loading and alignment moved here from scripts/research/foot_hires/scan.py (the scan-driven pass, 2026-10-16), which
now imports them, so the research comparisons and the part's transfer share one definition. Frame (the scans' frame,
scanfit.rezero's): the axis from the heel's centre (the middle of its breadth below z 40 at 15 % L) to the tip of toe
2, toes toward -y, +x lateral for a left foot, the pternion at y 0, the floor at z 0; a right foot's scan is mirrored
into it (its triangles' winding reversed), and scaled uniformly so its length (pternion to the longest toe, below z
60) is LENGTH. Numpy only: runs in Blender's Python and in the image venv.
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PLY_REL = "scans/zenodo_10360304/ply"     # under assets/
PLY_DIR = os.path.join(PROJECT, "assets", *PLY_REL.split("/"))
CACHE = os.path.join(PROJECT, "cache", "parts", "p01_scans")
LENGTH = 274.3          # this foot to its longest toe (part 01 after shape pass 2)
CUT_Z = 125.0           # the scans' flat top, before scaling


# --------------------------------------------------------------------------- reading

def load_ply(path):
    """(P (n, 3) mm, T (m, 3) triangles) from an ASCII PLY (MeshMixer's: x y z nx ny nz r g b a; faces of 3)."""
    with open(path, "rb") as f:
        nv = nf = 0
        nprops = 0
        in_vertex = False
        while True:
            line = f.readline().decode("ascii", "replace").strip()
            if line.startswith("format") and "ascii" not in line:
                raise ValueError(f"{path}: only ASCII PLY is read here")
            if line.startswith("element vertex"):
                nv, in_vertex = int(line.split()[-1]), True
            elif line.startswith("element face"):
                nf, in_vertex = int(line.split()[-1]), False
            elif line.startswith("property") and in_vertex:
                nprops += 1
            elif line == "end_header":
                break
        V = np.loadtxt(f, max_rows=nv, ndmin=2)
        Fc = np.loadtxt(f, max_rows=nf, dtype=np.int64, ndmin=2)
    if V.shape != (nv, nprops) or (Fc[:, 0] != 3).any():
        raise ValueError(f"{path}: unexpected layout {V.shape} / faces of {np.unique(Fc[:, 0])}")
    return V[:, :3].astype(float), Fc[:, 1:4].copy()


def ply_rel(sid, cond):
    """A scan's path under assets/ (for lib/cache.asset, which puts the file's hash in a build's key)."""
    return f"{PLY_REL}/{sid}_{cond}_R.ply"


def ply_path(sid, cond):
    return os.path.join(PROJECT, "assets", *ply_rel(sid, cond).split("/"))


def tri_normals(q, T):
    n = np.cross(q[T[:, 1]] - q[T[:, 0]], q[T[:, 2]] - q[T[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]


def vertex_normals(q, T):
    fn = np.cross(q[T[:, 1]] - q[T[:, 0]], q[T[:, 2]] - q[T[:, 0]])
    n = np.zeros_like(q)
    for c in range(3):
        np.add.at(n, T[:, c], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]


def sample_tris(q, T, step):
    """Points on every triangle no further than about `step` apart (a barycentric grid per triangle, finer on the
    larger ones), with the triangle's index: (points (k, 3), tri (k,))."""
    e = np.stack([np.linalg.norm(q[T[:, a]] - q[T[:, b]], axis=1) for a, b in ((0, 1), (1, 2), (2, 0))], 1).max(1)
    n = np.clip(np.ceil(e / step).astype(int), 1, 40)
    pts, ids = [], []
    for k in np.unique(n):
        sel = np.nonzero(n == k)[0]
        i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1), indexing="ij")
        keep = (i + j) <= k
        u, v = (i[keep] / k).astype(float), (j[keep] / k).astype(float)
        w = 1.0 - u - v
        A, B, Cc = q[T[sel, 0]], q[T[sel, 1]], q[T[sel, 2]]
        p = A[:, None, :] * w[None, :, None] + B[:, None, :] * u[None, :, None] + Cc[:, None, :] * v[None, :, None]
        pts.append(p.reshape(-1, 3))
        ids.append(np.repeat(sel, len(u)))
    return np.concatenate(pts), np.concatenate(ids)


# --------------------------------------------------------------------------- the toes and the frame

def toe_line(pts, zmax=40.0, step=1.0, prom=1.0):
    """The toes along the front of a foot in F (toes toward -y), from points on its skin: per `step` mm of x, the
    anterior outline (the most forward skin below zmax) and the pad profile (the lowest skin 2-14 mm behind that
    front, where a toe's pulp rests and a cleft between two toes stands high). The clefts are the pad profile's local
    maxima standing `prom` mm over the lower neighbouring pad and 0.3 over the higher (a raised toe 2, as on subject
    081, stands nearly as high as the 2-3 cleft), at least 8 mm apart; the toes the stretches between them, medial
    first (the hallux need not be the longest toe: 081's toe 2 leads it by 6 mm). Each toe's tip is the centre of the
    stretch of its front within 0.5 mm of its most forward point (a toe's front is flat across).
    Returns {hallux_tip, toe2_tip, tips, clefts (x), xs, front, pad}."""
    s = pts[pts[:, 2] < zmax]
    fore = s[s[:, 1] < s[:, 1].min() + 70.0]
    lo, hi = np.floor(fore[:, 0].min()), np.ceil(fore[:, 0].max()) + step
    xs = np.arange(lo, hi, step) + 0.5 * step
    i = np.clip(((fore[:, 0] - lo) / step).astype(int), 0, len(xs) - 1)
    front = np.full(len(xs), np.inf)
    np.minimum.at(front, i, fore[:, 1])
    pad = np.full(len(xs), np.inf)
    rel = fore[:, 1] - front[i]
    band = (rel > 2.0) & (rel < 14.0)
    np.minimum.at(pad, i[band], fore[band, 2])
    front[~np.isfinite(front)] = np.nan
    pad[~np.isfinite(pad)] = np.nan
    okp = np.isfinite(pad)
    pads = np.convolve(np.pad(np.interp(xs, xs[okp], pad[okp]), 1, mode="edge"), np.ones(3) / 3.0, mode="valid")
    cand = []
    for j in range(2, len(xs) - 2):
        if pads[j] >= pads[j - 1] and pads[j] > pads[j + 1]:
            left = pads[max(0, j - 12):j].min()
            right = pads[j + 1:j + 13].min()
            hi_side, lo_side = max(pads[j] - left, pads[j] - right), min(pads[j] - left, pads[j] - right)
            if hi_side >= prom and lo_side >= 0.25:
                cand.append((float(pads[j]), j))
    clefts = []
    for v, j in sorted(cand, reverse=True):   # the highest first; one within 8 mm of a kept cleft is dropped
        if all(abs(xs[j] - c) >= 10.0 for c in clefts):
            clefts.append(float(xs[j]))
    clefts.sort()
    edges = [float(xs[np.isfinite(front)][0]) - 0.5] + clefts + [float(xs[np.isfinite(front)][-1]) + 0.5]
    # a stretch medial of the first cleft narrower than 12 mm is the hallux's own side, not a toe
    while len(edges) > 2 and edges[1] - edges[0] < 12.0:
        edges.pop(1)
        clefts.pop(0)
    tp = []
    for a, b in zip(edges[:-1], edges[1:]):
        w = (xs > a + 1.0) & (xs < b - 1.0) & np.isfinite(front)
        if not w.any():
            continue
        y0 = float(np.nanmin(front[w]))
        tp.append([float(xs[w & (front < y0 + 0.5)].mean()), y0])
    return {"hallux_tip": tp[0], "toe2_tip": tp[1] if len(tp) > 1 else tp[0], "tips": tp, "clefts": clefts,
            "xs": xs, "front": front, "pad": pad}


def heel_origin(rot, z):
    """In plan coordinates already turned to the heading (toes toward -y): the origin of the frame, (the heel's centre
    x, the pternion's y): the pternion is the most posterior point below z 60, the heel's centre the middle of its
    breadth below z 40 at 15 % of the length (the axis runs through the heel's centre, not through the pternion,
    which on a flat-backed heel can lie off to one side)."""
    low = z < 60.0
    y_pt = rot[low, 1].max()
    L = y_pt - rot[low, 1].min()
    band = (z < 40.0) & (np.abs(rot[:, 1] - (y_pt - 0.15 * L)) < 3.0)
    return np.array([0.5 * (rot[band, 0].min() + rot[band, 0].max()), y_pt])


def frame_from(q, heading_xy):
    """Plan coordinates turned so `heading_xy` (toward the toes) is -y, x = y cross z (lateral for a left foot), the
    heel's centre at x 0 and the pternion at y 0 (heel_origin). Returns (p, ex, ey, origin in the turned plan)."""
    h = np.asarray(heading_xy, float) / np.linalg.norm(heading_xy)
    ey = -h
    ex = np.array([ey[1], -ey[0]])
    p = np.stack([q[:, :2] @ ex, q[:, :2] @ ey, q[:, 2]], 1)
    o = heel_origin(p[:, :2], p[:, 2])
    p[:, :2] -= o
    return p, ex, ey, o


def align(P, T, length=LENGTH, iters=6, scale=None):
    """A right foot's scan (raw axes: the long axis along x, z up from the floor) in frame F as a left foot, scaled
    uniformly about the pternion on the floor to `length` (or by `scale`: a loaded scan by its unloaded twin's factor,
    so the load's lengthening shows). Returns (q, T, info)."""
    P = np.asarray(P, float).copy()
    floor = float(P[:, 2].min())
    P[:, 2] -= floor
    cap = P[P[:, 2] > P[:, 2].max() - 2.0]
    heel_raw = -1.0 if cap[:, 0].mean() < P[:, 0].mean() else 1.0   # the leg's cut lies over the heel
    # the medial side: under the midfoot its border stands well off the floor (the arch)
    mid = P[np.abs(P[:, 0] - (P[:, 0].min() + P[:, 0].max()) / 2.0) < 15.0]
    yl, yh = mid[:, 1].min(), mid[:, 1].max()
    medial_raw = 1.0 if mid[mid[:, 1] > yh - 12.0, 2].min() > mid[mid[:, 1] < yl + 12.0, 2].min() else -1.0
    # a left foot's frame: x lateral (= -medial), y toward the heel; for a right foot's scan that is a reflection,
    # so the triangles' winding is reversed with it
    M = np.array([[0.0, -medial_raw, 0.0], [heel_raw, 0.0, 0.0], [0.0, 0.0, 1.0]])
    q = P @ M.T
    mirrored = bool(np.linalg.det(M) < 0)
    T = T[:, ::-1].copy() if mirrored else np.asarray(T).copy()
    # the toes are found once along the scan's own long axis (the authors' alignment, within a few degrees of the
    # heading); then the heading is iterated with every toe's tip tracked as the most forward skin within 6 mm across
    # of where it was (finding the toes afresh in each frame let one misread cleft swing the heading by 8 degrees)
    pts_raw, _ = sample_tris(q, T, 0.6)
    heading = np.array([0.0, -1.0])
    tips_raw = clefts_raw = None

    def in_frame(hd):
        ey = -hd
        ex = np.array([ey[1], -ey[0]])
        rot = np.stack([q[:, :2] @ ex, q[:, :2] @ ey], 1)
        pt = heel_origin(rot, q[:, 2])
        pp = np.stack([pts_raw[:, :2] @ ex - pt[0], pts_raw[:, :2] @ ey - pt[1], pts_raw[:, 2]], 1)
        return ex, ey, pt, pp

    def track(pp, ex, pt):
        out = []
        for tr in tips_raw:
            s2 = pp[(pp[:, 2] < 40.0) & (np.abs(pp[:, 0] - (tr @ ex - pt[0])) < 6.0)]
            y2 = s2[:, 1].min()
            out.append(np.array([s2[s2[:, 1] < y2 + 0.5, 0].mean(), y2]))
        return out

    for it in range(iters + 1):
        ex, ey, pt, pp = in_frame(heading)
        if tips_raw is None:
            tl = toe_line(pp)
            tp = [np.array(t) for t in tl["tips"]]
            clefts_raw = [(c + pt[0]) * ex + (tl["front"][np.argmin(np.abs(tl["xs"] - c))] + pt[1]) * ey
                          for c in tl["clefts"]]
        else:
            tp = track(pp, ex, pt)
        tips_raw = [(t[0] + pt[0]) * ex + (t[1] + pt[1]) * ey for t in tp[:2]]   # the hallux and toe 2
        t2 = tp[1] if len(tp) > 1 else tp[0]
        d = t2[0] * ex + t2[1] * ey          # toe 2's tip from the heel's centre, in the unturned plan
        new = d / np.linalg.norm(d)
        moved = math.degrees(math.acos(float(np.clip(new @ heading, -1.0, 1.0))))
        heading = new
        if moved < 0.01:
            break
    ex, ey, pt, pp = in_frame(heading)
    tp = track(pp, ex, pt)
    p = frame_from(q, heading)[0]
    f = p[p[:, 2] < 60.0]
    L0 = float(f[:, 1].max() - f[:, 1].min())
    s = length / L0 if scale is None else float(scale)
    p = p * s
    tp = [t * s for t in tp]
    clefts = sorted(float(((c @ ex) - pt[0]) * s) for c in clefts_raw)
    info = {"length_raw": round(L0, 2), "scale": round(s, 5), "length": round(L0 * s, 2), "heel_raw_x": heel_raw,
            "medial_raw_y": medial_raw, "mirrored": mirrored, "floor_raw": round(floor, 3),
            "heading_raw": np.round(heading, 5).tolist(),
            "heading_off_raw_axis_deg": round(math.degrees(math.atan2(heading[0], -heading[1])), 2),
            "hallux_tip": np.round(tp[0], 1).tolist(), "toe2_tip": np.round(tp[1], 1).tolist(),
            "hallux_ahead_of_toe2": round(float(tp[1][1] - tp[0][1]), 2), "clefts_x": np.round(clefts, 1).tolist(),
            "cut_z": round(CUT_Z * s, 2)}
    return p, T, info


# --------------------------------------------------------------------------- the part's reference

def _sha(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(sid, cond="mBW", path=None):
    """A scan aligned and scaled as above, (q, T, info), cached under cache/parts/p01_scans/ by the PLY's sha256; a
    loaded (fBW) scan takes its unloaded twin's scale. `path` overrides where the PLY is read (lib/cache.asset's)."""
    path = path or ply_path(sid, cond)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{os.path.relpath(path, PROJECT)}: the scans are not here; fetch them with "
                                "scripts/setup/fetch.py (downloads.json group 'scans')")
    sha = _sha(path)
    cpath = os.path.join(CACHE, f"{sid}_{cond}.npz")
    if os.path.exists(cpath):
        z = np.load(cpath)
        info = json.loads(str(z["info"]))
        if info.get("sha256") == sha:
            return z["q"].astype(float), z["T"].astype(np.int64), info
    scale = load(sid, "mBW")[2]["scale"] if cond == "fBW" else None
    P, T = load_ply(path)
    q, T, info = align(P, T, scale=scale)
    info.update(id=sid, cond=cond, sha256=sha, source=f"assets/{ply_rel(sid, cond)}")
    os.makedirs(CACHE, exist_ok=True)
    np.savez_compressed(cpath, q=q, T=T.astype(np.int32), info=json.dumps(info))
    return q, T.astype(np.int64), info
