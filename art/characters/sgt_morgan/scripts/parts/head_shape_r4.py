"""The head, round 4: the lower face and the jaw (head.md §11).

Rounds 2 and 3 (head_shape.py, head_shape_r3.py) matched the head's outlines in four views, but the jaw still rounds
softly into the neck: the head region ended at a pinned neck ring 45 mm under the menton at the front, and no term
saw the under-jaw. Round 4 continues round 3's transfer (every round-3 term but round 2's Depth Anything relief, which
pushed the nasal dorsum back against the profile outline; the Hunyuan prior remapped onto the new region) from
head-shape-r3.target, and adds:

1. **The region runs into the neck.** head.py's head region (head and neck bone weights > 0.3) plus the skin above
   z REGION_Z (rest, ~thyroid level and below: the ring moves from z 1531-1573 to ~1500, the sternal notch) inside
   |x| < REGION_X (the neck and its sides). The new ring is pinned as before; the bending energy blends the
   field into it. The back half of the new neck skin (behind y NAPE_Y) is held (sigma NAPE_SIGMA), so the nape and the
   gaiter's back stay; the helpers follow round 3's region only (extend_r4), so the neck joint cubes, the bones and
   the rig's weights are untouched (weights are per vertex: a shape key does not change them).
2. **Outlines that see the jaw.** The R001 profile's outline continued down the throat to below the laryngeal
   prominence (rows); the profile's under-chin line (columns: per column, the bottom of the projected mesh's covered
   interval that contains a point inside the chin, against the first background pixel under the chin); the R001
   front view's two side outlines from below the ear lobes to the gonion (below it R001's neck stands outside the jaw).
3. **The jaw as landmarks** (scripts/parts/head_jaw_marks.json, read by hand): the gonion and the mandible's lower
   border in the front and the profile, triangulated with the fitted R001 cameras (the two polylines matched by arc
   fraction, the closest point of each pair of rays; sigma grows with the rays' gap), and the under-jaw plane between
   the border and the profile's under-chin line (points interpolated between them, short of the chin-neck corner).
   Point-to-plane terms on the nearest vertex with a compatible normal.
4. **Soft tissue.** A sculpt prior on the total offset since round 3: the cheek below the zygoma (in front of the
   masseter) and the jowl (beside the chin, in front of the masseter, above the jaw border) sit in by HOLLOW_MM and
   JOWL_MM at their centres (Gaussian, sigma SCULPT_SIGMA per vertex); the masseter itself is left.
5. **Defects.** The jaw zone's bending relaxed (JAW_BEND, not on the midline); round 3's and 4's change smoothed at
   the mouth corners; the total change since round 1 smoothed near any triangle flipped against round 1's face; and,
   after the last round, the outer canthi made rigid (canthus_patch: round 2 had folded the lower lid's outer corner
   over and the socket lining showed red in the hero eye zoom).

Developed on copies with round 3's harness (base.py at dca7a15, stature 1835, round 1's hero pose snapshot):

  "$SGT_PYIMG" -I scripts/parts/head_shape_r4.py --fit [--rounds 3]   # head-shape-r4.target, head_shape_r4.json
  "$SGT_PYIMG" -I scripts/parts/head_shape_r4.py --check r2|r3|r4     # cameras re-solved per mesh (check_<tag>.json)
  "$SGT_PYIMG" -I scripts/parts/head_shape_r4.py --check-fixed r2|r3|r4   # through round 2's cameras
  "$SGT_PYIMG" -I scripts/parts/head_shape_r4.py --render r4 [--samples 64]  # renders/head/r4/
  "$SGT_PYIMG" -I scripts/parts/head_shape_r4.py --sheets             # r2 | r3 | r4 sheets

Left/right are the soldier's own; +X is his left, he faces -Y (CLAUDE.md).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
SCRIPTS = os.path.join(PROJECT, "scripts")
for p in (SCRIPTS, HERE, os.path.join(SCRIPTS, "stages")):
    if p not in sys.path:
        sys.path.insert(0, p)

import head_shape as HS  # noqa: E402
import head_shape_r3 as R3  # noqa: E402

WORK = os.path.join(PROJECT, "cache", "head_r4")
DEV_R2, DEV_R3 = R3.DEV_R2, R3.DEV_R3
DEV_R4 = os.path.join(PROJECT, "cache", "stages", "head_dev_r4.blend")
TARGET_R3 = R3.TARGET_R3
TARGET_R4 = os.path.join(HERE, "head-shape-r4.target")
JSON_R4 = os.path.join(HERE, "head_shape_r4.json")
MARKS = os.path.join(HERE, "head_jaw_marks.json")
RENDERS = os.path.join(PROJECT, "renders", "head", "r4")
PRIOR_EXPORT = os.path.join(R3.WORK, "prior", "export.npz")      # the region round 3's prior mask is indexed by
R3_CAMS = os.path.join(R3.WORK, "cams.json")                     # round 3's renders were framed through these
FIXED_CAMS = os.path.join(R3.WORK, "check_r2", "cams.json")      # round 2's cameras (round 3's "fixed" check)

E_ = os.environ.get
REGION_Z = float(E_("R4_REGION_Z", 1500.0))     # rest mm: the new region's floor (the ring), ~ the sternal notch
REGION_X = float(E_("R4_REGION_X", 120.0))     # |x| < this: the neck and its sides (75 left the ring running up the
                                                # side of the neck to z 1568 and the field kinked along it)
NAPE_Y, NAPE_SIGMA = -10.0, 1.0                 # the new neck skin behind this y is held (mm)
OUTLINE_SIGMA_MM = float(E_("R4_OUTLINE_SIGMA", 2.0))   # the new outline terms, per sample
COLUMN_SIGMA_MM = float(E_("R4_COLUMN_SIGMA", 1.5))     # the profile's under-chin line, per column sample
MARK_SIGMA_MM = float(E_("R4_MARK_SIGMA", 1.2))         # the jaw border and gonion points
UNDER_SIGMA_MM = float(E_("R4_UNDER_SIGMA", 1.5))       # the under-jaw plane points
HOLLOW_MM = float(E_("R4_HOLLOW_MM", 3.0))      # the sub-zygomatic hollow's depth at its centre (total since round 3)
JOWL_MM = float(E_("R4_JOWL_MM", 2.5))
SCULPT_SIGMA = float(E_("R4_SCULPT_SIGMA", 1.0))
HOLLOW_R, JOWL_R = 11.0, 10.0                   # mm: the Gaussians' radii
THROAT_ROWS = (962.0, 1086.0)                   # R001 profile rows: the throat, below the chin-neck corner to below the
                                                # prominence (the corner itself left to the bending: the rows and the
                                                # columns met on one midline vertex there and folded it)
UNDERCHIN_COLS = (296.0, 428.0)                 # profile columns: the under-chin line, chin to short of the corner (447)
JAW_BEND = float(E_("R4_JAW_BEND", 2.0))       # the bending sigma (and round 3's curvature sigma) in the jaw zone is
                                                # this times round 2's: the jaw edge and the under-jaw crease need curvature
JAW_PRIOR = float(E_("R4_JAW_PRIOR", 2.0))     # round 3's prior offset sigma in the jaw zone x this (no data there)
LID_R = 16.0                                    # mm: the skin within LID_R of each eyeball moves rigidly with it (total),
LID_SIGMA = float(E_("R4_LID_SIGMA", 0.0))      # at this sigma; 0 = off (tried at 0.3: the red lining stayed, the lids
                                                # moved up to 8 mm)
RELIEF = E_("R4_RELIEF", "0") == "1"            # round 2's Depth Anything relief: off (it pushed the nasal dorsum back
                                                # 2.3 mm a solve against the profile outline, round 2's noted bias)
CORNER_R, CORNER_SIGMA = 10.0, 0.05             # mm: round 3's and 4's change smoothed at the mouth corners
FOLD_R, FOLD_SIGMA = 8.0, 0.05                  # mm: round 2-4's total change smoothed within FOLD_R of any triangle
                                                # flipped against round 1's face, and of the inner canthi (round 2 folded
                                                # the lower inner lid over: the red socket lining in the hero eye zoom)
CANTHUS_R = (6.0, 22.0)                         # mm: round 2-4's total displacement made rigid within the first radius of
                                                # each outer canthus (MediaPipe 33 / 263), blended out by the second
                                                # (round 2 folded the lower lid's outer corner over: the red socket lining
                                                # in the hero eye zoom; head.md §10 called it the inner canthus)
OUTLINE_STEP = 6.0                              # px between the throat rows / under-chin columns (~2 mm: the neck's
                                                # edges are 5-10 mm; at 3 px the midline vertices took many samples each
                                                # and folded)
FRONT_ROWS = (740.0, 836.0)                     # R001 front rows: below the ear lobes to the gonion (below it R001's
                                                # neck stands 14 mm a side outside the jaw: not followed, see head.md)


def say(*a):
    print("[hshape-r4]", *a, flush=True)


# =========================================================================== Blender side

def bl_patch_region():
    import common as C
    import head as H

    def region(bd):
        V = bd["V"]
        old = bd["in_body"] & (C.weight_sum(bd, C.is_head) > 0.3)
        ext = bd["in_body"] & (V[:, 2] > REGION_Z) & (np.abs(V[:, 0]) < REGION_X) & (V[:, 1] > -140.0) & (V[:, 1] < 90.0)
        return old | ext
    H.head_region = region


def bl_export(out_dir, blend, cams_json):
    """head_shape.bl_export with the extended region, and the old region's flag (old.npz)."""
    bl_patch_region()
    HS.bl_export(out_dir, blend, cams_json)
    import common as C
    E = np.load(os.path.join(out_dir, "export.npz"))
    body = __import__("bpy").data.objects[C.BODY]
    bd = C.body_data(body)
    old = (C.weight_sum(bd, C.is_head) > 0.3)[E["idx"]]
    np.savez_compressed(os.path.join(out_dir, "old.npz"), old=old)


# =========================================================================== outside Blender

def _blender(args, log):
    exe = os.environ.get("SGT_BLENDER")
    if not exe:
        raise SystemExit("SGT_BLENDER is not set: source cache/env.sh")
    t = time.perf_counter()
    r = subprocess.run([exe, "-b", "--python", os.path.abspath(__file__), "--"] + args, cwd=PROJECT,
                       capture_output=True, text=True, errors="replace")
    with open(log, "w", encoding="utf-8") as f:
        f.write(r.stdout + "\n" + r.stderr)
    for l in [l for l in r.stdout.splitlines() if l.startswith(("[hshape", "[head", "Error", "Traceback"))][-6:]:
        print("   ", l[:300], flush=True)
    if r.returncode != 0 or "Traceback" in r.stdout + r.stderr:
        print(r.stdout[-4000:], r.stderr[-3000:])
        raise SystemExit(f"Blender failed: {args[:2]}")
    return time.perf_counter() - t


def export(out_dir, blend, cams):
    """head_shape.export through this script's Blender side (the extended region); adds E['old']."""
    os.makedirs(out_dir, exist_ok=True)
    cj = os.path.join(out_dir, "cams.json")
    with open(cj, "w") as f:
        json.dump(cams, f, indent=1)
    _blender(["--export", out_dir, blend, cj], os.path.join(out_dir, "export.log"))
    E = dict(np.load(os.path.join(out_dir, "export.npz")))
    E["old"] = np.load(os.path.join(out_dir, "old.npz"))["old"]
    return E


def _patch():
    HS.WORK = WORK
    R3.WORK = WORK
    HS.export = export


def build_dev(target, out_blend, tag):
    os.makedirs(WORK, exist_ok=True)
    tdir = os.path.join(WORK, "target_" + tag)
    os.makedirs(tdir, exist_ok=True)
    shutil.copyfile(target, os.path.join(tdir, HS.SHAPE_NAME + ".target"))
    dt = _blender(["--build-dev", os.path.join(tdir, HS.SHAPE_NAME + ".target"), out_blend],
                  os.path.join(WORK, f"build_{tag}.log"))
    say(f"dev base {os.path.basename(out_blend)} built in {dt:.0f} s")


def remap_prior(E, prior):
    """Round 3's prior (mask indexed by its region) onto this export's region."""
    old_idx = np.load(PRIOR_EXPORT)["idx"]
    pos = {int(g): k for k, g in enumerate(old_idx)}
    m = np.zeros(len(E["idx"]))
    for k, g in enumerate(E["idx"]):
        j = pos.get(int(g))
        if j is not None:
            m[k] = prior["mask"][j]
    out = dict(prior)
    out["mask"] = m
    return out


# ---------------------------------------------------------------- reference outlines and the jaw marks

def _fg(png):
    from PIL import Image
    from scipy import ndimage
    a = np.asarray(Image.open(png).convert("RGB"), float)
    bg = np.concatenate([a[:40, :40].reshape(-1, 3), a[:40, -40:].reshape(-1, 3)]).mean(0)
    return ndimage.binary_opening(np.linalg.norm(a - bg, axis=2) > 28.0, iterations=2)


def ref_r4():
    """The new reference outlines: the profile's throat (rows: the first foreground column), its under-chin line
    (columns: the first background row below row 880), the front's two sides (rows: first and last foreground)."""
    out = {}
    fp = _fg(os.path.join(HS.R001, HS.VIEWS["profile"][0]))
    ys = np.arange(int(THROAT_ROWS[0]) - 6, int(THROAT_ROWS[1]) + 6)
    xs = np.array([np.where(fp[y])[0][0] for y in ys], float)
    out["throat"] = (ys.astype(float), xs)
    cols = np.arange(int(UNDERCHIN_COLS[0]) - 4, int(UNDERCHIN_COLS[1]) + 5)
    yc = []
    for x in cols:
        col = fp[880:1150, x]
        k = np.where(~col)[0]
        yc.append(880.0 + k[0] if len(k) else np.nan)
    out["underchin"] = (cols.astype(float), np.array(yc))
    ff = _fg(os.path.join(HS.R001, HS.VIEWS["front"][0]))
    ys = np.arange(int(FRONT_ROWS[0]) - 6, int(FRONT_ROWS[1]) + 6)
    out["front_R"] = (ys.astype(float), np.array([np.where(ff[y])[0][0] for y in ys], float))
    out["front_L"] = (ys.astype(float), np.array([np.where(ff[y])[0][-1] for y in ys], float))
    return out


def _poly_dist(q, P):
    """Distance from 2D point q to polyline P (k, 2)."""
    best = 1e9
    for a, b in zip(P[:-1], P[1:]):
        ab = b - a
        t = np.clip(np.dot(q - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
        best = min(best, float(np.linalg.norm(a + t * ab - q)))
    return best


def triangulate_marks(cams, ref4):
    """The hand-read jaw marks -> rest 3D points (mm) through the current R001 cameras.
    Returns dict: border (k, 3) both sides, gonion (2, 3), under (m, 3) the under-jaw plane points, and a record."""
    J = json.load(open(MARKS))
    pf, pp = cams["views"]["front"], cams["views"]["profile"]
    M = np.array([-1.0, 1.0, 1.0])

    def resample(P, k):
        P = np.asarray(P, float)
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        u = np.linspace(0, s[-1], k)
        return np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], 1)

    def meet(xy_f, xy_p, mirror):
        """The closest point of a front ray and a profile ray (the front point mirrored onto his left for R)."""
        o1, d1 = HS.ray_view(np.array([xy_f], float), pf)
        o2, d2 = HS.ray_view(np.array([xy_p], float), pp)
        d1, d2 = d1[0], d2[0]
        if mirror:
            o1, d1 = o1 * M, d1 * M
        w = o1 - o2
        a, b, c, d, e = d1 @ d1, d1 @ d2, d2 @ d2, d1 @ w, d2 @ w
        den = a * c - b * b
        t1, t2 = (b * e - c * d) / den, (a * e - b * d) / den
        p1, p2 = o1 + t1 * d1, o2 + t2 * d2
        return 0.5 * (p1 + p2), float(np.linalg.norm(p1 - p2))
    # the border: both views' polylines from the gonion towards the chin, matched by arc fraction (x from the
    # front, y from the profile, z from both); the front's R side mirrored onto his left, then averaged
    K = 8
    pb = resample(J["profile"]["jaw_border"][::-1], K)          # the profile's runs chin -> gonion
    rec = {"border_ray_gap_mm": []}
    sides = []
    for side, mirror in (("jaw_border_L", False), ("jaw_border_R", True)):
        fb = resample(J["front"][side], K)
        pts = []
        for q_f, q_p in zip(fb, pb):
            X, gap = meet(q_f, q_p, mirror)
            pts.append(X)
            rec["border_ray_gap_mm"].append(round(gap, 1))
        sides.append(np.array(pts))
    Lp, Rp = sides
    avg = 0.5 * (Lp + Rp)                                       # both on his left now
    rec["border_LR_diff_mm"] = round(float(np.sqrt(np.mean(np.sum((Lp - Rp) ** 2, 1)))), 2)
    border = np.concatenate([avg, avg * M])
    gon = np.array([avg[0], avg[0] * M])
    # where the views disagree (the rays miss each other) the point is uncertain: sigma grows with half the gap
    gap = 0.5 * (np.array(rec["border_ray_gap_mm"][:K]) + np.array(rec["border_ray_gap_mm"][K:]))
    sig = np.sqrt(MARK_SIGMA_MM ** 2 + (gap / 3.0) ** 2)
    rec["border_sigma_mm"] = [round(float(x), 2) for x in sig]
    rec["gonion_rest_mm"] = [round(float(a), 1) for a in avg[0]]
    rec["border_rest_mm"] = [[round(float(c), 1) for c in X] for X in avg]
    # the under-chin line at the midline: profile rays onto x = 0
    cols, yc = ref4["underchin"]
    ok = ~np.isnan(yc)
    mid = []
    for x, y in zip(cols[ok][::15], yc[ok][::15]):
        o, d = HS.ray_view(np.array([[x, y]]), pp)
        t = -o[0] / d[0, 0]
        mid.append(o + t * d[0])
    mid = np.array(mid)
    # the under-jaw plane: between the midline under-chin line and the border at the same y, forward of the corner
    # the hand-read chin-neck corner on the midline: the under-jaw plane stops 12 mm in front of it (points nearer it
    # lifted the lateral under-chin right at the corner and dragged the throat's long triangles onto the midline)
    o, d = HS.ray_view(np.array([J["profile"]["cervicomental"]], float), pp)
    corner = o + (-o[0] / d[0, 0]) * d[0]
    rec["cervicomental_rest_mm"] = [round(float(c), 1) for c in corner]
    under = []
    for X in mid:
        if X[1] > min(avg[:, 1].max(), corner[1] - 12.0):
            continue
        k = np.argsort(np.abs(avg[:, 1] - X[1]))[:2]
        a, b = avg[k[0]], avg[k[1]]
        t = np.clip((X[1] - a[1]) / (b[1] - a[1]) if b[1] != a[1] else 0.0, 0, 1)
        B = a + t * (b - a)
        for s in (0.35, 0.7):
            P = np.array([s * B[0], X[1], (1 - s) * X[2] + s * B[2]])
            under += [P, P * np.array([-1.0, 1.0, 1.0])]
    rec["midline_underchin_rest_mm"] = [[round(float(c), 1) for c in X] for X in mid]
    rec["n_border"], rec["n_under"] = int(len(border)), int(len(under))
    return {"border": border, "gonion": gon, "under": np.array(under), "rec": rec,
            "border_sig": np.concatenate([sig, sig]), "gonion_sig": np.array([sig[0], sig[0]])}


def mark_corr(V, N, T, nexp, thr, maxd=18.0, below=12.0):
    """For each target point, the nearest vertex whose normal agrees with nexp (dot > thr), within maxd and no more
    than `below` mm under the target (a first version matched throat vertices to the under-jaw points near the
    chin-neck corner and pulled the front of the neck onto the midline)."""
    out = []
    for t, ne in zip(T, nexp):
        ok = np.where((N @ ne > thr) & (V[:, 2] > t[2] - below))[0]
        if not len(ok):
            out.append(-1)
            continue
        d = np.linalg.norm(V[ok] - t, axis=1)
        k = int(np.argmin(d))
        out.append(int(ok[k]) if d[k] < maxd else -1)
    return np.array(out)


def mark_terms(E, U, marks):
    """Point-to-plane residuals (mm) n.(V+U - T) for the border, gonion and under-jaw points; vertex ids, normals,
    the residuals and the sigma of each."""
    V = E["V_rest"] + U
    N = R3.vertex_normals(V, E["tris"])
    ids, Ts, sig, kind = [], [], [], []
    def lateral_down(T, a, b):
        return np.stack([np.sign(T[:, 0]) * a, np.zeros(len(T)), -b * np.ones(len(T))], 1)
    B, G, Un = marks["border"], marks["gonion"], marks["under"]
    for name, T, ne, thr, s in (("border", B, lateral_down(B, 0.6, 0.8), 0.0, marks["border_sig"]),
                                ("gonion", G, lateral_down(G, 0.8, 0.6), 0.0, marks["gonion_sig"]),
                                ("under", Un, np.tile([0.0, 0.0, -1.0], (len(Un), 1)), 0.2, np.full(len(Un), UNDER_SIGMA_MM))):
        if not len(T):
            continue
        v = mark_corr(V, N, T, ne, thr, below=6.0 if name == "under" else 12.0)
        for vi, t, si in zip(v, T, s):
            if vi >= 0:
                ids.append(vi)
                Ts.append(t)
                sig.append(si)
                kind.append(name)
    ids = np.array(ids, int)
    Ts = np.array(Ts)
    n = N[ids]
    r = np.einsum("ij,ij->i", V[ids] - Ts, n)
    return ids, n, r, np.array(sig), np.array(kind)


# ---------------------------------------------------------------- the new outline terms

def column_outline(xy, tris, cols, y_in, y_cap):
    """Per column x: starting at row y_in (inside the chin), the bottom of the projected mesh's covered interval
    containing it. Returns per column (a, b, t, x, y_bottom) for the edge crossing at the bottom, or None where the
    coverage does not contain y_in or runs past y_cap (the neck in front of that column: the rows term's job)."""
    A = xy[tris]
    xmin, xmax = A[:, :, 0].min(1), A[:, :, 0].max(1)
    out = []
    for x0, yi, yc in zip(cols, y_in, y_cap):
        k = np.where((xmin <= x0) & (xmax > x0))[0]
        if not len(k):
            out.append(None)
            continue
        iv = []
        for e0, e1 in ((0, 1), (1, 2), (2, 0)):
            pa, pb = A[k, e0], A[k, e1]
            cross = (pa[:, 0] - x0) * (pb[:, 0] - x0) <= 0
            dx = pb[:, 0] - pa[:, 0]
            t = np.where(np.abs(dx) > 1e-9, (x0 - pa[:, 0]) / np.where(np.abs(dx) > 1e-9, dx, 1.0), 0.0)
            y = pa[:, 1] + t * (pb[:, 1] - pa[:, 1])
            iv.append((cross & (np.abs(dx) > 1e-9), y, t, tris[k, e0], tris[k, e1]))
        lo = np.full(len(k), np.inf)
        hi = np.full(len(k), -np.inf)
        hab = np.zeros((len(k), 3))
        for ok, y, t, a, b in iv:
            lo = np.where(ok, np.minimum(lo, y), lo)
            upd = ok & (y > hi)
            hi = np.where(upd, y, hi)
            hab[upd] = np.stack([a[upd], b[upd], t[upd]], 1)
        good = np.isfinite(lo) & np.isfinite(hi)
        lo, hi, hab = lo[good], hi[good], hab[good]
        cur = None
        if np.any((lo <= yi) & (hi >= yi)):
            cur = yi
            while True:
                m = (lo <= cur + 0.05) & (hi > cur + 1e-6)
                if not m.any():
                    break
                j = np.where(m)[0][np.argmax(hi[m])]
                cur = hi[j]
                best = j
                if cur > yc:
                    break
        if cur is None or cur > yc or cur == yi:
            out.append(None)
            continue
        a, b, t = hab[best]
        out.append((int(a), int(b), float(t), float(x0), float(cur)))
    return out


def underchin_terms(E, U, par, ref4):
    """The profile's under-chin line: residual y_model(x) - y_ref(x) per column and its gradient on the edge point."""
    cols, yc = ref4["underchin"]
    ok = ~np.isnan(yc)
    cs = np.arange(UNDERCHIN_COLS[0], UNDERCHIN_COLS[1] + 0.1, OUTLINE_STEP)
    yr = np.interp(cs, cols[ok], yc[ok])
    f = par["f"] / HS.VIEW_DIST
    VU = E["V_rest"] + U
    xy = HS.proj_view(VU, par)
    ol = [o for o in column_outline(xy, E["tris"], cs, yr - 8.0 * f, yr + 14.0 * f) if o is not None]
    if not ol:
        return (np.zeros(0, int), np.zeros(0, int), np.zeros(0)), np.zeros(0), np.zeros((0, 3))
    A_ = np.array([o[0] for o in ol])
    B_ = np.array([o[1] for o in ol])
    T_ = np.array([o[2] for o in ol])
    X0 = np.array([o[3] for o in ol])
    P = VU[A_] * (1 - T_[:, None]) + VU[B_] * T_[:, None]
    q = HS.proj_view(P, par)
    r = q[:, 1] - np.interp(q[:, 0], cols[ok], yc[ok])
    slope = np.gradient(np.interp(cols, cols[ok], yc[ok]), cols)
    J = HS.jac(lambda Y: HS.proj_view(Y, par), P)
    g = J[:, 1, :] - np.interp(q[:, 0], cols, slope)[:, None] * J[:, 0, :]
    return (A_, B_, T_), r, g


def throat_terms(E, U, par, ref4):
    ys, xs = ref4["throat"]
    return HS.silhouette(E["V_rest"] + U, lambda Y: HS.proj_view(Y, par), HS.face_edges(E),
                         np.arange(THROAT_ROWS[0], THROAT_ROWS[1], OUTLINE_STEP), ys, xs, "min")


def front_side_terms(E, U, par, ref4, side):
    ys, xs = ref4["front_R" if side == "min" else "front_L"]
    return HS.silhouette(E["V_rest"] + U, lambda Y: HS.proj_view(Y, par), HS.face_edges(E),
                         np.arange(FRONT_ROWS[0], FRONT_ROWS[1], 3.0), ys, xs, side)


# ---------------------------------------------------------------- the soft-tissue sculpt

def sculpt_field(E, V0, marks):
    """Per vertex of the region: the wanted normal offset since round 3 (mm, negative = in) and its weight.
    Centres on the rest surface: the hollow between the mouth corner and the tragus (45 % of the way, 8 mm up), the
    jowl between the mouth corner and the gonion (40 %, at the mouth corner height - 14 mm)."""
    V = V0
    # the mouth corners: the lateral-most front vertices of the lips band near the mouth's height; from MediaPipe's
    # 3D points on round 2's mesh (prior.npz L_mpfb, global rest mm), which round 3/4 moved by under 3 mm there
    L = np.load(R3.PRIOR)["L_mpfb"]
    mcR, sub = L[61], L[2]            # his right mouth corner, the subnasale
    # the hollow: lateral of the nasolabial fold, half way between the subnasale's and the mouth corner's heights,
    # 20 mm outside the mouth corner (under the zygoma, in front of the masseter); the jowl: 10 mm outside and 20 mm
    # below the mouth corner (above the jaw border, in front of the masseter)
    c_h = np.array([mcR[0] - 20.0, 0.0, 0.5 * (mcR[2] + sub[2])])
    c_j = np.array([mcR[0] - 10.0, 0.0, mcR[2] - 20.0])
    N = R3.vertex_normals(V, E["tris"])
    want = np.zeros(len(V))
    wt = np.zeros(len(V))
    rec = {}
    for name, c, h, rad in (("hollow", c_h, HOLLOW_MM, HOLLOW_R), ("jowl", c_j, JOWL_MM, JOWL_R)):
        for sgn in (-1.0, 1.0):            # his right, then his left (mirrored)
            cc = np.array([sgn * abs(c[0]), c[1], c[2]])
            # onto the surface: the most forward front-facing vertex within 4 mm of (x, z)
            ok = np.where((N[:, 1] < -0.2) & (np.hypot(V[:, 0] - cc[0], V[:, 2] - cc[2]) < 4.0))[0]
            v = ok[np.argmin(V[ok, 1])]
            d = np.linalg.norm(V - V[v], axis=1)
            # smooth in distance and in normal (a hard normal cut made a crease beside the nose in a first run)
            g = np.exp(-0.5 * (d / rad) ** 2) * (d < 2.5 * rad) * R3.ramp(N @ N[v], 0.3, 0.8)
            want = np.minimum(want, -h * g)
            wt = np.maximum(wt, g)
            if sgn < 0:
                rec[name] = [round(float(a), 1) for a in V[v]]
    Wn = R3.graph(len(V), E["edges"])
    want = R3.diffuse(Wn, want, np.ones(len(V)), 4)
    wt = R3.diffuse(Wn, wt, np.ones(len(V)), 4)
    wt[E["ring"]] = 0.0
    return want, wt, N, rec


def zones(E, D_total):
    """Per round: the jaw zone (0..1: below the mouth corners, forward of the ears, into the neck), the lid rings
    (region vertices within LID_R of each eyeball's centre), the mouth-corner zones, and the total displacement of the
    region since round 1 (the work target so far) and round 2's."""
    V = E["V_rest"]
    L = np.load(R3.PRIOR)["L_mpfb"]
    mcz = 0.5 * (L[61][2] + L[291][2])
    ear_front = float(np.percentile(V[E["ears"]][:, 1], 3))
    men_z = V[int(E["mark_ids"][0]), 2]
    jz = (1.0 - R3.ramp(V[:, 2], mcz - 20.0, mcz - 5.0)) * (1.0 - R3.ramp(V[:, 1], ear_front - 15.0, ear_front))
    jz *= R3.ramp(V[:, 2], men_z - 45.0, men_z - 25.0)     # the lower neck keeps round 2's smoothness down to the ring
    jz *= R3.ramp(np.abs(V[:, 0]), 6.0, 18.0)      # and the midline: the profile outlines pull only the midline
                                                    # vertices, which then sank alone into a keel-like crease
    names = list(E["helper_names"])
    lids = []
    for nm in ("helper-r-eye", "helper-l-eye"):
        j = names.index(nm)
        sel = (E["helper"] == j) & ~E["in_body"]
        c = E["V_all"][sel].mean(0)
        lids.append(np.where(np.linalg.norm(V - c, axis=1) < LID_R)[0])
    corners = np.where((np.linalg.norm(V - L[61], axis=1) < CORNER_R) | (np.linalg.norm(V - L[291], axis=1) < CORNER_R))[0]
    idx = E["idx"]
    H = D_total[idx].copy()
    flipped = flips(V - H, V, E["tris"])
    seeds = np.concatenate([V[np.unique(E["tris"][flipped])].reshape(-1, 3), L[[133, 362]]])
    from scipy.spatial import cKDTree
    d, _ = cKDTree(seeds).query(V)
    fold = np.where(d < FOLD_R)[0]
    return {"jaw_zone": jz, "lids": lids, "corners": corners, "hist": H, "fold": fold, "n_flipped": int(flipped.sum()),
            "hist_r2": HS.read_target(len(E["V_all"]), R3.TARGET_R2)[idx]}


def canthus_patch(D, E):
    """The total displacement (all vertices, mm) made a rigid translation near each outer canthus (the zone's core
    mean), so round 1's lower-lid corner, which has no fold, comes back translated. Returns D and a record."""
    L = np.load(R3.PRIOR)["L_mpfb"]
    V, sk = E["V_all"], E["in_body"]
    r0, r1 = CANTHUS_R
    rec = []
    for c in (L[33], L[263]):
        d = np.linalg.norm(V - c, axis=1)
        zone = sk & (d < r1)
        w = np.where(zone, 1.0 - R3.ramp(d, r0, r1), 0.0)
        m = D[zone & (d < r0)].mean(0)
        rec.append({"centre": [round(float(a), 1) for a in c], "core": int((zone & (d < r0)).sum()),
                    "max_change_mm": round(float(np.max(np.linalg.norm(w[:, None] * (m - D), axis=1))), 2)})
        D = D + w[:, None] * (m - D)
    return D, rec


def patch_main():
    """Apply canthus_patch to scripts/parts/head-shape-r4.target and rebuild the dev base."""
    E = dict(np.load(os.path.join(WORK, "round3", "export.npz")))
    D = HS.read_target(len(E["V_all"]), TARGET_R4)
    D, rec = canthus_patch(D, E)
    HS.write_target(D, TARGET_R4, note="head round 4 (head_shape_r4.py), outer canthi patched")
    js = json.load(open(JSON_R4))
    js["canthus_patch"] = rec
    with open(JSON_R4, "w", encoding="utf-8", newline="\n") as f:
        json.dump(js, f, indent=1, default=float)
    build_dev(TARGET_R4, DEV_R4, "patched")
    say("canthus patch", rec)


def flips(Va, Vb, T, deg=90.0):
    """Triangles whose normal turned more than deg between two positions of the mesh."""
    def nrm(V):
        x = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
        return x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)
    return np.einsum("ij,ij->i", nrm(Va), nrm(Vb)) < np.cos(np.radians(deg))


def sculpt_stats(E, U, ext):
    want, wt, N0, _ = ext["sculpt"]
    sel = wt > 0.5
    cur = np.einsum("ij,ij->i", E["V_rest"][sel] + U[sel] - ext["V0"][sel], N0[sel])
    return {"n": int(sel.sum()), "want_mean_mm": round(float(np.mean(want[sel])), 2), "got_mean_mm": round(float(np.mean(cur)), 2)}


# ---------------------------------------------------------------- the solve

def solve_U_r4(E, corr, cams, nuis, U0, maps, pf, ext):
    """head_shape_r3.solve_U_r3 plus round 4's terms (ext: ref4, marks, the sculpt, V0 = round 0's rest region)."""
    import scipy.sparse as sp
    import scipy.sparse.linalg as spl
    S, L3, _ = maps
    V, P0, A = E["V_rest"], E["P0"], E["A"]
    n = len(V)
    blocks, rhs = [], []

    def add(Jrows, r, sigma):
        blocks.append(Jrows / sigma)
        rhs.append(-r / sigma)
    Rn = HS.rotvec(np.radians(nuis[:3]))
    piv = E["pivot"]

    def hero_xy(X):
        return HS.hero_proj(piv + (X - piv) @ Rn.T) + nuis[3:5]
    c = corr["hero"]
    PU = P0 + np.einsum("kij,kj->ki", A, U0)
    X = np.einsum("lk,lki->li", c["bar"], PU[c["vid"]])
    J = HS.jac(hero_xy, X)
    r = (hero_xy(X) - c["ref"]).ravel()
    rows, cols, vals = [], [], []
    for l in range(len(X)):
        for k in range(3):
            v = c["vid"][l, k]
            JA = c["bar"][l, k] * J[l] @ A[v]
            for a in range(2):
                for b in range(3):
                    rows.append(2 * l + a)
                    cols.append(3 * v + b)
                    vals.append(JA[a, b])
    w = np.repeat(np.where(np.isin(c["ids"], HS.JAW_OVAL), 1.5, 1.0), 2)
    Jm = sp.csr_matrix((vals, (rows, cols)), shape=(2 * len(X), 3 * n))
    add(sp.diags(np.sqrt(w)) @ Jm, np.sqrt(w) * r, HS.HERO_SIGMA_PX)
    hid = E["hand_ids"]
    rows, cols, vals, rr = [], [], [], []
    for q, (k, xy) in enumerate(HS.HAND.items()):
        ids = hid[q][hid[q] >= 0]
        Xh = PU[ids].mean(0)
        Jh = HS.jac(hero_xy, Xh[None])[0]
        rr.extend(list((hero_xy(Xh[None])[0] - np.array(xy)) / HS.HAND_SIGMA[k]))
        for v in ids:
            JA = Jh @ A[v] / len(ids) / HS.HAND_SIGMA[k]
            for a in range(2):
                for b in range(3):
                    rows.append(2 * q + a)
                    cols.append(3 * v + b)
                    vals.append(JA[a, b])
    add(sp.csr_matrix((vals, (rows, cols)), shape=(2 * len(HS.HAND), 3 * n)), np.array(rr), 1.0)
    VU = V + U0
    for v, par in cams["views"].items():
        if v not in corr or v == "profile":
            continue
        c = corr[v]
        if not len(c["ids"]):
            continue
        X = np.einsum("lk,lki->li", c["bar"], VU[c["vid"]])
        fn = lambda Y, par=par: HS.proj_view(Y, par)        # noqa: E731
        J = HS.jac(fn, X)
        r = (fn(X) - c["ref"]).ravel()
        sig = HS.VIEW_SIGMA_MM * par["f"] / HS.VIEW_DIST
        rows, cols, vals = [], [], []
        for l in range(len(X)):
            for k in range(3):
                vv = c["vid"][l, k]
                for a in range(2):
                    for b in range(3):
                        rows.append(2 * l + a)
                        cols.append(3 * vv + b)
                        vals.append(c["bar"][l, k] * J[l, a, b])
        add(sp.csr_matrix((vals, (rows, cols)), shape=(2 * len(X), 3 * n)), r, sig)
    if "profile" in cams["views"] and "profile" in corr:
        par = cams["views"]["profile"]
        (sa, sb, st), r, g, feat = HS.profile_terms(E, U0, par, corr["profile"])
        k = len(r)
        rows = np.repeat(np.arange(k), 6)
        cols = np.concatenate([3 * sa[:, None] + np.arange(3), 3 * sb[:, None] + np.arange(3)], 1).ravel()
        vals = np.concatenate([g * (1 - st)[:, None], g * st[:, None]], 1).ravel()
        sig = HS.EDGE_SIGMA_MM * par["f"] / HS.VIEW_DIST
        add(sp.csr_matrix((vals, (rows, cols)), shape=(k, 3 * n)), r, sig)
        Pf = np.array([HS.pt(VU, feat[q][0]) for q in feat])
        fr = np.array([feat[q][1] for q in feat])
        J = HS.jac(lambda Y: HS.proj_view(Y, par), Pf)
        rows, cols, vals = [], [], []
        for l, q in enumerate(feat):
            a_, b_, t_ = feat[q][0]
            for vv, wv in ((a_, 1 - t_), (b_, t_)):
                for i_ in range(2):
                    for j_ in range(3):
                        rows.append(2 * l + i_)
                        cols.append(3 * vv + j_)
                        vals.append(wv * J[l, i_, j_])
        add(sp.csr_matrix((vals, (rows, cols)), shape=(2 * len(Pf), 3 * n)), (HS.proj_view(Pf, par) - fr).ravel(), sig)
    for v in HS.DEPTH_VIEWS:
        if v + "_depth" in corr:
            c = corr[v + "_depth"]
            vid, delta, dvec = c["vid"], c["delta"], c["dir"]
            cur = (U0[vid] @ dvec)
            rows = np.repeat(np.arange(len(vid)), 3)
            cols = (3 * vid[:, None] + np.arange(3)).ravel()
            add(sp.csr_matrix((np.tile(dvec, len(vid)), (rows, cols)), shape=(len(vid), 3 * n)), cur - delta, HS.DEPTH_SIGMA_MM)

    def add_sil(abt, r, g, sigma, posed):
        a_, b_, t_ = abt
        k = len(r)
        if not k:
            return
        if posed:
            ga = np.einsum("ki,kij->kj", g, A[a_]) * (1 - t_)[:, None]
            gb = np.einsum("ki,kij->kj", g, A[b_]) * t_[:, None]
        else:
            ga, gb = g * (1 - t_)[:, None], g * t_[:, None]
        rows = np.repeat(np.arange(k), 6)
        cols = np.concatenate([3 * a_[:, None] + np.arange(3), 3 * b_[:, None] + np.arange(3)], 1).ravel()
        add(sp.csr_matrix((np.concatenate([ga, gb], 1).ravel(), (rows, cols)), shape=(k, 3 * n)), r, sigma)
    ref = corr["ref"]
    if "hero_edge" in ref:
        abt, r, g = HS.sil_hero(E, U0, nuis, ref)
        add_sil(abt, r, g, HS.HERO_SIL_SIGMA_PX, True)
    if "threequarter_edge" in ref and "threequarter" in cams["views"]:
        par = cams["views"]["threequarter"]
        abt, r, g = HS.sil_threequarter(E, U0, par, ref)
        add_sil(abt, r, g, HS.EDGE_SIGMA_MM * par["f"] / HS.VIEW_DIST, False)
    # ---- round 4: the throat, the under-chin line, the front's sides
    ref4, marks = ext["ref4"], ext["marks"]
    pp, pfr = cams["views"]["profile"], cams["views"]["front"]
    abt, r, g = throat_terms(E, U0, pp, ref4)
    add_sil(abt, r, g, OUTLINE_SIGMA_MM * pp["f"] / HS.VIEW_DIST, False)
    abt, r, g = underchin_terms(E, U0, pp, ref4)
    add_sil(abt, r, g, COLUMN_SIGMA_MM * pp["f"] / HS.VIEW_DIST, False)
    for side in ("min", "max"):
        abt, r, g = front_side_terms(E, U0, pfr, ref4, side)
        add_sil(abt, r, g, OUTLINE_SIGMA_MM * pfr["f"] / HS.VIEW_DIST, False)
    # ---- the jaw marks (point to plane, mm)
    ids, nrm, r, sig, _ = mark_terms(E, U0, marks)
    if len(ids):
        rows = np.repeat(np.arange(len(ids)), 3)
        cols = (3 * ids[:, None] + np.arange(3)).ravel()
        add(sp.csr_matrix(((nrm / sig[:, None]).ravel(), (rows, cols)), shape=(len(ids), 3 * n)), r / sig, 1.0)
    # ---- the sculpt: n0 . (V + U - V0) = want, weighted by the Gaussian
    want, wt, N0, _ = ext["sculpt"]
    sel = np.where(wt > 0.08)[0]
    if len(sel):
        cur = np.einsum("ij,ij->i", V[sel] + U0[sel] - ext["V0"][sel], N0[sel])
        sg = SCULPT_SIGMA / np.sqrt(wt[sel])
        rows = np.repeat(np.arange(len(sel)), 3)
        cols = (3 * sel[:, None] + np.arange(3)).ravel()
        add(sp.csr_matrix(((N0[sel] / sg[:, None]).ravel(), (rows, cols)), shape=(len(sel), 3 * n)), (cur - want[sel]) / sg, 1.0)
    # ---- round 3's prior
    d, spread, wm, N, d_det = pf
    u0 = U0.ravel()
    D = (wm * d_det)[:, None] * N
    jz = ext["jaw_zone"]
    kb = 1.0 + (JAW_BEND - 1.0) * jz
    inv2 = ((1 - wm) / HS.BEND_SIGMA ** 2 + wm / R3.LAP_SIGMA ** 2) / kb ** 2
    Wr = sp.diags(np.repeat(np.sqrt(inv2), 3))
    add(Wr @ L3, Wr @ (L3 @ (u0 - D.ravel())), 1.0)
    sel = np.where(wm > 0.05)[0]
    cur = np.einsum("ij,ij->i", U0[sel], N[sel])
    tgt = np.clip(d[sel], -R3.PRIOR_CLIP_MM, R3.PRIOR_CLIP_MM)
    sig = np.sqrt(R3.PRIOR_SIGMA_MM ** 2 + spread[sel] ** 2) / np.sqrt(wm[sel]) * (1.0 + (JAW_PRIOR - 1.0) * jz[sel])
    rows = np.repeat(np.arange(len(sel)), 3)
    cols = (3 * sel[:, None] + np.arange(3)).ravel()
    Jp = sp.csr_matrix(((N[sel] / sig[:, None]).ravel(), (rows, cols)), shape=(len(sel), 3 * n))
    add(Jp, (cur - tgt) / sig, 1.0)
    # ---- the lids move rigidly with the eyeball: the total displacement since round 1 of the skin within LID_R
    # of each eyeball, less its mean (round 2 moved the lower inner lid off the eye: the socket lining showed red)
    H = ext["hist"]
    for ring_ids in (ext["lids"] if LID_SIGMA > 0 else []):
        k = len(ring_ids)
        if not k:
            continue
        M_ = sp.identity(k) - sp.csr_matrix(np.full((k, k), 1.0 / k))
        T_ = sp.csr_matrix((np.ones(k), (np.arange(k), ring_ids)), shape=(k, n))
        Op = sp.kron(M_ @ T_, sp.identity(3)).tocsr()
        add(Op, Op @ (H + U0).ravel(), LID_SIGMA)
    # ---- the mouth corners: round 3's and 4's change there smoothed (round 3 left a fold at the near corner)
    cz = ext["corners"]
    if len(cz):
        Sel = sp.csr_matrix((np.ones(3 * len(cz)), (np.arange(3 * len(cz)), (3 * cz[:, None] + np.arange(3)).ravel())),
                            shape=(3 * len(cz), 3 * n))
        Op = (Sel @ L3).tocsr()
        add(Op, Op @ (H - ext["hist_r2"] + U0).ravel(), CORNER_SIGMA)
    # ---- the folds: the total change since round 1 smoothed where a triangle has flipped and at the inner canthi
    fz = ext["fold"]
    if len(fz):
        Sel = sp.csr_matrix((np.ones(3 * len(fz)), (np.arange(3 * len(fz)), (3 * fz[:, None] + np.arange(3)).ravel())),
                            shape=(3 * len(fz), 3 * n))
        Op = (Sel @ L3).tocsr()
        add(Op, Op @ (H + U0).ravel(), FOLD_SIGMA)
    # ---- regularisation: round 2's, plus the nape held
    add(sp.identity(3 * n, format="csr"), u0, HS.TIKH_SIGMA)
    cran = np.where(((V[:, 2] > HS.TRICHION_Z) | ((V[:, 1] > -20.0) & (V[:, 2] > 1700.0))) & ~E["ears"])[0]
    s_ = (3 * cran[:, None] + np.arange(3)).ravel()
    add(sp.csr_matrix((np.ones(len(s_)), (np.arange(len(s_)), s_)), shape=(len(s_), 3 * n)), u0[s_], HS.CRANIUM_SIGMA)
    nape = np.where(~E["old"] & (V[:, 1] > NAPE_Y))[0]
    s_ = (3 * nape[:, None] + np.arange(3)).ravel()
    tot = (V + U0 - ext["V0"]).ravel()
    add(sp.csr_matrix((np.ones(len(s_)), (np.arange(len(s_)), s_)), shape=(len(s_), 3 * n)), tot[s_], NAPE_SIGMA)
    ring = np.where(E["ring"])[0]
    s_ = (3 * ring[:, None] + np.arange(3)).ravel()
    add(sp.csr_matrix((np.ones(len(s_)), (np.arange(len(s_)), s_)), shape=(len(s_), 3 * n)), tot[s_], HS.PIN_SIGMA)
    top = int(np.argmax(V[:, 2]))
    add(sp.csr_matrix(([1.0], ([0], [3 * top + 2])), shape=(1, 3 * n)), np.array([u0[3 * top + 2]]), 0.2)
    Jall = sp.vstack(blocks).tocsr() @ S
    b = np.concatenate(rhs)
    du = spl.spsolve((Jall.T @ Jall).tocsc(), Jall.T @ b)
    return U0 + (S @ du).reshape(-1, 3)


def extend_r4(E, U):
    """head_shape.extend with the helpers following round 3's region only (the neck joint cubes stay)."""
    Vall, idx = E["V_all"], E["idx"]
    D = np.zeros_like(Vall)
    D[idx] = U
    Eo = dict(E)
    Eo["V_rest"] = E["V_rest"][E["old"]]
    Do = HS.extend({**Eo, "idx": idx[E["old"]]}, U[E["old"]])
    others = ~E["in_body"]
    D[others] = Do[others]
    return D


# ---------------------------------------------------------------- numbers

def r4_errors(E, cams, U, ref4, marks):
    """Round 4's own numbers (mm at the head): the throat, the under-chin line, the front's sides, the jaw marks."""
    out = {}
    pp, pfr = cams["views"]["profile"], cams["views"]["front"]
    mm = HS.VIEW_DIST / pp["f"]
    _, r, _ = throat_terms(E, U, pp, ref4)
    out["profile_throat"] = {"n": int(len(r)), "rms_mm": round(float(np.sqrt(np.mean(r ** 2))) * mm, 2), "mean_mm": round(float(np.mean(r)) * mm, 2)}
    _, r, _ = underchin_terms(E, U, pp, ref4)
    nc = len(np.arange(UNDERCHIN_COLS[0], UNDERCHIN_COLS[1] + 0.1, OUTLINE_STEP))
    out["profile_underchin"] = {"n": int(len(r)), "of": nc,
                                "rms_mm": round(float(np.sqrt(np.mean(r ** 2))) * mm, 2) if len(r) else None,
                                "mean_mm": round(float(np.mean(r)) * mm, 2) if len(r) else None}
    mmf = HS.VIEW_DIST / pfr["f"]
    # the front's half-width error per row (model - R001, + = wider; the common shift, which a symmetric field
    # cannot change, removed) from the two side outlines
    sides = {}
    for side in ("min", "max"):
        (a, b, t), r, _ = front_side_terms(E, U, pfr, ref4, side)
        P = (E["V_rest"] + U)[a] * (1 - t[:, None]) + (E["V_rest"] + U)[b] * t[:, None]
        sides[side] = (HS.proj_view(P, pfr)[:, 1], r)
    ys = np.arange(FRONT_ROWS[0], FRONT_ROWS[1], 3.0)
    rl = np.interp(ys, *sides["min"])
    rr = np.interp(ys, *sides["max"])
    hw = 0.5 * (rr - rl) * mmf
    out["front_halfwidth"] = {"n": int(len(ys)), "rms_mm": round(float(np.sqrt(np.mean(hw ** 2))), 2),
                              "mean_mm": round(float(np.mean(hw)), 2), "shift_mm": round(float(np.mean(0.5 * (rr + rl)) * mmf), 2)}
    ids, _, r, _, kind = mark_terms(E, U, marks)
    for k in ("border", "gonion", "under"):
        m = kind == k
        if m.any():
            out["marks_" + k] = {"n": int(m.sum()), "rms_mm": round(float(np.sqrt(np.mean(r[m] ** 2))), 2),
                                 "mean_mm": round(float(np.mean(r[m])), 2)}
    out["neck_girth_mm"] = girths(E, U)
    return out


def girths(E, U):
    """Neck girths (rest, mm): the convex hull perimeter of the region's surface cut by the plane z = menton + dz,
    behind the chin (y > menton y + 20) and inside |x| < 85."""
    from scipy.spatial import ConvexHull
    V = E["V_rest"] + U
    men = V[int(E["mark_ids"][0])]
    e = E["edges"]
    out = {}
    for dz in (-20, -35, -50, -65, -80):
        z = men[2] + dz
        a, b = V[e[:, 0]], V[e[:, 1]]
        c = (a[:, 2] - z) * (b[:, 2] - z) < 0
        t = (z - a[c, 2]) / (b[c, 2] - a[c, 2])
        P = a[c] + t[:, None] * (b[c] - a[c])
        P = P[(P[:, 1] > men[1] + 20.0) & (np.abs(P[:, 0]) < 85.0)][:, :2]
        out[f"menton{dz}"] = round(float(ConvexHull(P).area), 1) if len(P) > 5 else None
    return out


# =========================================================================== the fit

def fit_main(rounds=3, inner=4):
    _patch()
    os.makedirs(WORK, exist_ok=True)
    prior0 = dict(np.load(R3.PRIOR))
    t_all = time.perf_counter()
    ref = HS.reference()
    ref4 = ref_r4()
    work_target = os.path.join(WORK, "head-shape-r4.target")
    shutil.copyfile(TARGET_R3, work_target)
    log = []
    D_total, cams, V0, marks = None, None, None, None
    for rnd in range(rounds):
        t0 = time.perf_counter()
        rdir = os.path.join(WORK, f"round{rnd}")
        os.makedirs(rdir, exist_ok=True)
        if rnd == 0 and os.path.exists(DEV_R3):
            blend = DEV_R3
        else:
            build_dev(work_target, DEV_R4, f"round{rnd}")
            blend = DEV_R4
        if cams is None:
            E = export(rdir, blend, {"views": {}})
            cams = HS.initial_cams(E, ref, HS.correspondences(E, None, {"views": {}}, rdir, ref)["hero"])
            nuis = np.zeros(5)
        E = export(rdir, blend, cams)
        corr = HS.correspondences(E, None, cams, rdir, ref)
        if not RELIEF:
            corr = {k: v for k, v in corr.items() if not k.endswith("_depth")}
        if rnd == 0:
            for _ in range(2):
                cams, nuis = HS.solve_cams(E, corr, cams, nuis, np.zeros_like(E["V_rest"]))
            E = export(rdir, blend, cams)
            corr = HS.correspondences(E, None, cams, rdir, ref)
            if not RELIEF:
                corr = {k: v for k, v in corr.items() if not k.endswith("_depth")}
            marks = triangulate_marks(cams, ref4)
            say("jaw marks", json.dumps(marks["rec"]))
            V0 = E["V_rest"].copy()
            sculpt = sculpt_field(E, V0, marks)
            say("sculpt centres", sculpt[3])
        if D_total is None:
            D_total = HS.read_target(len(E["V_all"]), TARGET_R3)
        maps = HS.build_maps(E)
        pf = R3.prior_field(E, remap_prior(E, prior0))
        ext = {"ref4": ref4, "marks": marks, "sculpt": sculpt, "V0": V0, **zones(E, D_total)}
        U = np.zeros_like(E["V_rest"])
        before = HS.view_errors(E, corr, cams, nuis, U)
        before.update(r4_errors(E, cams, U, ref4, marks))
        before["sculpt"] = sculpt_stats(E, U, ext)
        say("zones: jaw", int((ext["jaw_zone"] > 0.5).sum()), "corners", len(ext["corners"]), "flipped", ext["n_flipped"],
            "fold zone", len(ext["fold"]))
        for k in range(inner):
            _, nuis = HS.solve_cams(E, corr, cams, nuis, U)
            U = solve_U_r4(E, corr, cams, nuis, U, maps, pf, ext)
        _, nuis = HS.solve_cams(E, corr, cams, nuis, U)
        after = HS.view_errors(E, corr, cams, nuis, U)
        after.update(r4_errors(E, cams, U, ref4, marks))
        after["sculpt"] = sculpt_stats(E, U, ext)
        after["flipped_vs_r1"] = int(flips(E["V_rest"] - ext["hist"], E["V_rest"] + U, E["tris"]).sum())
        D_total = D_total + extend_r4(E, U)
        HS.write_target(D_total, work_target, note=f"head round 4 (head_shape_r4.py: the jaw, the region into the neck), round {rnd}")
        with open(os.path.join(WORK, "cams.json"), "w") as f:
            json.dump(cams, f, indent=1)
        un = np.linalg.norm(U, axis=1)
        rec = {"round": rnd, "before": before, "after": after, "nuisance": [round(float(a), 2) for a in nuis],
               "U_mm": {"max": round(float(un.max()), 2), "p95": round(float(np.percentile(un, 95)), 2)},
               "seconds": round(time.perf_counter() - t0, 1)}
        log.append(rec)
        keys = ("hero_with_nuisance", "hero_silhouette", "threequarter_silhouette", "profile", "profile_throat",
                "profile_underchin", "front_halfwidth", "marks_border", "marks_gonion", "marks_under",
                "front", "threequarter", "neck_girth_mm", "sculpt", "flipped_vs_r1")
        say(f"round {rnd}: U max {rec['U_mm']['max']} p95 {rec['U_mm']['p95']}")
        for k in keys:
            say(f"   {k}: {json.dumps(before.get(k))} -> {json.dumps(after.get(k))}")
        with open(os.path.join(WORK, "fit_log.json"), "w") as f:
            json.dump(log, f, indent=1, default=float)
    D_total, canthus = canthus_patch(D_total, E)
    HS.write_target(D_total, TARGET_R4, note="head round 4 (head_shape_r4.py: the jaw, the region into the neck), outer canthi patched")
    build_dev(TARGET_R4, DEV_R4, "final")
    D3 = HS.read_target(len(E["V_all"]), TARGET_R3)
    dd = np.linalg.norm(D_total - D3, axis=1)
    rec = {"note": "Head round 4: head-shape-r4.target, scripts/parts/head_shape_r4.py --fit (head.md §11): round 3's "
                   "transfer continued with the region into the neck, the jaw outlines and the hand-read jaw marks "
                   "(head_jaw_marks.json), and the soft-tissue sculpt. To use it, copy it over head-shape.target.",
           "target": os.path.relpath(TARGET_R4, PROJECT).replace("\\", "/"),
           "starts_from": os.path.relpath(TARGET_R3, PROJECT).replace("\\", "/"),
           "displacement_mm": {"max": round(float(np.linalg.norm(D_total, axis=1).max()), 2),
                               "change_from_r3_max": round(float(dd.max()), 2),
                               "change_from_r3_p95": round(float(np.percentile(dd[dd > 1e-3], 95)), 2)},
           "settings": {"region_z": REGION_Z, "region_x": REGION_X, "nape_y": NAPE_Y, "nape_sigma": NAPE_SIGMA,
                        "outline_sigma_mm": OUTLINE_SIGMA_MM, "column_sigma_mm": COLUMN_SIGMA_MM,
                        "mark_sigma_mm": MARK_SIGMA_MM, "under_sigma_mm": UNDER_SIGMA_MM, "hollow_mm": HOLLOW_MM,
                        "jowl_mm": JOWL_MM, "sculpt_sigma": SCULPT_SIGMA, "jaw_bend": JAW_BEND, "jaw_prior": JAW_PRIOR,
                        "lid_r": LID_R, "lid_sigma": LID_SIGMA, "relief": RELIEF, "corner_r": CORNER_R, "corner_sigma": CORNER_SIGMA,
                        "fold_r": FOLD_R, "fold_sigma": FOLD_SIGMA, "outline_step_px": OUTLINE_STEP},
           "marks": marks["rec"], "sculpt_centres": sculpt[3], "canthus_patch": canthus,
           "base": f"scripts/stages/base.py at {R3.COMMIT_BASE} (stature 1835), pose cache/head_r2/hero_pose_r1.json",
           "cams": cams, "log": log, "seconds": round(time.perf_counter() - t_all, 1)}
    with open(JSON_R4, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=1, default=float)
    return log


# =========================================================================== checks, renders, sheets

BLENDS = {"r2": DEV_R2, "r3": DEV_R3, "r4": DEV_R4}


def _extras(tag, E, cams, rdir):
    ref4 = ref_r4()
    marks = triangulate_marks(cams, ref4)
    out = r4_errors(E, cams, np.zeros_like(E["V_rest"]), ref4, marks)
    out["marks_rec"] = marks["rec"]
    return out


def check_main(tag):
    """Round 2's check (cameras re-solved per mesh on MediaPipe) through the extended region, plus round 4's numbers."""
    _patch()
    HS.overlays = R3._overlays
    R3.RENDERS = RENDERS
    out = HS.check_main(tag, BLENDS[tag])
    rdir = os.path.join(WORK, f"check_{tag}")
    E = dict(np.load(os.path.join(rdir, "export.npz")))
    E["old"] = np.load(os.path.join(rdir, "old.npz"))["old"]
    cams = json.load(open(os.path.join(rdir, "cams.json")))
    out.update(_extras(tag, E, cams, rdir))
    with open(os.path.join(WORK, f"check_{tag}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    say(tag, json.dumps({k: out[k] for k in out if k.startswith(("profile", "front_halfwidth", "marks_", "neck", "hero_s", "threeq"))}, default=float))
    return out


def check_fixed_main(tag):
    """Through round 2's cameras (round 3's fixed check), only the hero nuisance re-solved."""
    _patch()
    ref = HS.reference()
    cams = json.load(open(FIXED_CAMS))
    rdir = os.path.join(WORK, f"checkfixed_{tag}")
    E = export(rdir, BLENDS[tag], cams)
    corr = HS.correspondences(E, None, cams, rdir, ref)
    U = np.zeros_like(E["V_rest"])
    nuis = np.zeros(5)
    for _ in range(2):
        _, nuis = HS.solve_cams(E, corr, cams, nuis, U)
    out = HS.view_errors(E, corr, cams, nuis, U)
    out["dims_mm"] = HS.dims(E)
    out.update(_extras(tag, E, cams, rdir))
    out["cams"] = os.path.relpath(FIXED_CAMS, PROJECT).replace("\\", "/")
    with open(os.path.join(WORK, f"checkfixed_{tag}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    say("fixed", tag, json.dumps(out, default=float))
    return out


def bl_render_dev(blend, prefix, samples):
    import head as H
    rc = os.path.join(WORK, "render_cams")
    HS.WORK = rc
    HS.DEV_BLEND = blend
    HS.DEV_JSON = os.path.splitext(blend)[0] + ".json"
    H.OUT = RENDERS
    os.makedirs(RENDERS, exist_ok=True)
    return H.bl_build(["--dev", "--prefix", prefix, "--samples", str(samples)])


def render_main(tag, samples):
    rc = os.path.join(WORK, "render_cams")
    os.makedirs(rc, exist_ok=True)
    shutil.copyfile(R3_CAMS, os.path.join(rc, "cams.json"))      # round 3's renders' framing
    dt = _blender(["--render-dev", BLENDS[tag], f"{tag}_", str(samples)], os.path.join(WORK, f"render_{tag}.log"))
    say(f"renders {tag} in {dt:.0f} s")


def sheets_main():
    """r2 | r3 | r4 sheets (r2 and r3 from renders/head/r3/), the references first where there is one."""
    from PIL import Image
    os.makedirs(RENDERS, exist_ok=True)
    r3dir = R3.RENDERS

    def row(paths, h=700):
        ims = []
        for p in paths:
            im = Image.open(p).convert("RGB")
            ims.append(im.resize((int(im.width * h / im.height), h)))
        W = sum(i.width for i in ims) + 10 * (len(ims) - 1)
        s = Image.new("RGB", (W, h), (20, 20, 20))
        x = 0
        for i in ims:
            s.paste(i, (x, 0))
            x += i.width + 10
        return s
    made = []
    trip = lambda k: [os.path.join(r3dir, f"r2_{k}.png"), os.path.join(r3dir, f"r3_{k}.png"), os.path.join(RENDERS, f"r4_{k}.png")]  # noqa: E731
    for mode in ("clay", "cycles"):
        for v in ("front", "side", "side_L", "threequarter"):
            ps = trip(f"rest_{v}_{mode}")
            if all(os.path.exists(p) for p in ps):
                p = os.path.join(RENDERS, f"cmp_rest_{v}_{mode}.png")
                row(ps).save(p)
                made.append(p)
    for k in ("hero_head_face", "hero_head_face_cycles"):
        ps = trip(k)
        if all(os.path.exists(p) for p in ps):
            p = os.path.join(RENDERS, f"cmp_{k}.png")
            row([HS.REF_CROP] + ps).save(p)
            made.append(p)
    for v in ("front", "threequarter", "profile"):
        ps = trip(f"r001_{v}")
        if all(os.path.exists(p) for p in ps):
            p = os.path.join(RENDERS, f"cmp_r001_{v}.png")
            row([os.path.join(HS.R001, HS.VIEWS[v][0])] + ps).save(p)
            made.append(p)
    for z in ("g_jaw_x10", "g_eye_right_x20", "g_nose_mouth_x14", "z_head_x8"):
        ps = [os.path.join(r3dir, f"r3_zoom_{z}_sheet.png"), os.path.join(RENDERS, f"r4_zoom_{z}_sheet.png")]
        if all(os.path.exists(p) for p in ps):
            p = os.path.join(RENDERS, f"cmp_zoom_{z}.png")
            row(ps, h=400).save(p)
            made.append(p)
    say("sheets", [os.path.basename(p) for p in made])


def main():
    if HS.in_blender():
        a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        if a and a[0] == "--build-dev":
            return R3.bl_build_dev(a[1] or None, a[2])
        if a and a[0] == "--export":
            bl_export(a[1], a[2], a[3])
            return 0
        if a and a[0] == "--render-dev":
            return bl_render_dev(a[1], a[2], int(a[3]))
        raise SystemExit("head_shape_r4.py in Blender: --build-dev | --export | --render-dev")
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--check", default=None)
    ap.add_argument("--check-fixed", default=None)
    ap.add_argument("--render", default=None)
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--sheets", action="store_true")
    ap.add_argument("--patch-canthus", action="store_true", help="apply the outer-canthus patch to head-shape-r4.target")
    args = ap.parse_args()
    if args.patch_canthus:
        patch_main()
    if args.fit:
        fit_main(args.rounds)
    if args.check:
        for t in args.check.split(","):
            check_main(t)
    if args.check_fixed:
        for t in args.check_fixed.split(","):
            check_fixed_main(t)
    if args.render:
        render_main(args.render, args.samples)
    if args.sheets:
        sheets_main()
    return 0


if __name__ == "__main__":
    if HS.in_blender():
        try:
            rc = main()
        except Exception:
            import traceback
            traceback.print_exc()
            rc = 1
        sys.stdout.flush()
        os._exit(rc or 0)
    sys.exit(main())
