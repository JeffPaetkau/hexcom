"""The head part, round 1 (PLAN.md, take 2): the face likeness by MPFB targets, the hair cap, the stubble and
the head's renders. Notes: scripts/parts/head.md.

Pipeline (which half lives where):
- The face is MPFB face/head targets on Body.Mesh, applied by scripts/stages/base.py from
  scripts/parts/head_fit.json, so the eye bones, the MHCLO eyes/brows/lashes and the landmarks pose.py fits
  all follow the fitted face, and every part built on base.blend sees it. This script writes that file.
- The hair cap and the stubble shell are this part's own objects (collection Part.Head), built on the rest
  body and bound to Morgan.Rig like the garments, cached in cache/parts/head.blend.

  "$SGT_PYIMG" -I scripts/parts/head.py --fit [--iters 3]
      the likeness fit: per iteration, base.py rebuilds the body with the current head_fit.json, Blender
      renders the posed head through the hero camera (preset ref.head_face) and exports the posed head mesh,
      the per-vertex skinning and every candidate target's displacement; MediaPipe's face landmarker reads
      the render and the reference crop; each model landmark is cast back onto the posed mesh; scipy's
      least_squares solves the target weights (plus a small nuisance head rotation, so the face does not
      absorb the pose's error) for the reprojected landmarks to land on the reference's. Writes
      scripts/parts/head_fit.json and cache/parts/head_fit/ (renders, landmarks, a log per iteration).
  "$SGT_PYIMG" -I scripts/parts/head.py --check [tag]
      the same measurement once, on the current base.blend and hero pose, no nuisance rotation: the
      landmark residual the round reports (cache/parts/head_fit/<tag>/check.json, renders/head/head_landmarks_<tag>.png).
  "$SGT_BLENDER" -b --python scripts/parts/head.py [-- --no-render] [--samples 64]
      builds Part.Head (Head.Hair, Head.Stubble), saves cache/parts/head.blend, renders renders/head/.

Left/right are the soldier's own; +X is his left, he faces -Y (CLAUDE.md).
"""
import argparse
import json
import math
import os
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

FIT_JSON = os.path.join(HERE, "head_fit.json")
WORK = os.path.join(PROJECT, "cache", "parts", "head_fit")
OUT = os.path.join(PROJECT, "renders", "head")
REF_CROP = os.path.join(PROJECT, "ref", "crop_head_face.png")
MP_MODEL = os.path.join(PROJECT, "assets", "ai", "mediapipe", "face_landmarker.task")
BOX, SCALE = (715, 30, 885, 200), 5          # ref.head_face: full-frame box and its scale (850 x 850)

# The candidate MPFB targets, one fit parameter each; a parameter may drive several targets with one weight
# (left and right together: the face is fitted symmetric, take 1 spec 06 §2.5 row 14). Bounds [0, 1].
# PRIOR: the weight each parameter is pulled towards (sigma PRIOR_SIGMA); zero unless the reference
# analysis (archive/v1/notes/analysis_face_grooming.md §10) gives a reason the landmarks cannot see.
_LR = lambda t: [f"l-{t}", f"r-{t}"]          # noqa: E731
PARAMS = [
    ("head-square", ["head-square"]), ("head-rectangular", ["head-rectangular"]), ("head-oval", ["head-oval"]),
    ("head-round", ["head-round"]), ("head-diamond", ["head-diamond"]), ("head-triangular", ["head-triangular"]),
    ("head-invertedtriangular", ["head-invertedtriangular"]),
    ("head-scale-horiz-incr", ["head-scale-horiz-incr"]), ("head-scale-horiz-decr", ["head-scale-horiz-decr"]),
    ("head-scale-vert-incr", ["head-scale-vert-incr"]), ("head-scale-vert-decr", ["head-scale-vert-decr"]),
    ("head-fat-decr", ["head-fat-decr"]), ("head-fat-incr", ["head-fat-incr"]), ("head-age-incr", ["head-age-incr"]),
    ("forehead-scale-vert-incr", ["forehead-scale-vert-incr"]), ("forehead-scale-vert-decr", ["forehead-scale-vert-decr"]),
    ("forehead-temple-decr", ["forehead-temple-decr"]), ("forehead-temple-incr", ["forehead-temple-incr"]),
    ("eyebrows-trans-down", ["eyebrows-trans-down"]), ("eyebrows-trans-up", ["eyebrows-trans-up"]),
    ("eyebrows-angle-down", ["eyebrows-angle-down"]), ("eyebrows-angle-up", ["eyebrows-angle-up"]),
    ("eye-scale-incr", _LR("eye-scale-incr")), ("eye-scale-decr", _LR("eye-scale-decr")),
    ("eye-trans-in", _LR("eye-trans-in")), ("eye-trans-out", _LR("eye-trans-out")),
    ("eye-trans-up", _LR("eye-trans-up")), ("eye-trans-down", _LR("eye-trans-down")),
    ("eye-height1-decr", _LR("eye-height1-decr")), ("eye-height1-incr", _LR("eye-height1-incr")),
    ("eye-height2-decr", _LR("eye-height2-decr")), ("eye-height2-incr", _LR("eye-height2-incr")),
    ("eye-corner1-up", _LR("eye-corner1-up")), ("eye-corner2-up", _LR("eye-corner2-up")),
    ("cheek-bones-incr", _LR("cheek-bones-incr")), ("cheek-bones-decr", _LR("cheek-bones-decr")),
    ("cheek-volume-decr", _LR("cheek-volume-decr")), ("cheek-volume-incr", _LR("cheek-volume-incr")),
    ("cheek-trans-up", _LR("cheek-trans-up")), ("cheek-trans-down", _LR("cheek-trans-down")),
    ("nose-scale-vert-incr", ["nose-scale-vert-incr"]), ("nose-scale-vert-decr", ["nose-scale-vert-decr"]),
    ("nose-scale-horiz-incr", ["nose-scale-horiz-incr"]), ("nose-scale-horiz-decr", ["nose-scale-horiz-decr"]),
    ("nose-trans-up", ["nose-trans-up"]), ("nose-trans-down", ["nose-trans-down"]),
    ("nose-width1-decr", ["nose-width1-decr"]), ("nose-width1-incr", ["nose-width1-incr"]),
    ("nose-width3-incr", ["nose-width3-incr"]), ("nose-width3-decr", ["nose-width3-decr"]),
    ("nose-point-width-incr", ["nose-point-width-incr"]), ("nose-point-width-decr", ["nose-point-width-decr"]),
    ("nose-scale-depth-incr", ["nose-scale-depth-incr"]), ("nose-scale-depth-decr", ["nose-scale-depth-decr"]),
    ("nose-hump-incr", ["nose-hump-incr"]), ("nose-flaring-incr", ["nose-flaring-incr"]),
    ("mouth-scale-horiz-incr", ["mouth-scale-horiz-incr"]), ("mouth-scale-horiz-decr", ["mouth-scale-horiz-decr"]),
    ("mouth-scale-vert-incr", ["mouth-scale-vert-incr"]), ("mouth-scale-vert-decr", ["mouth-scale-vert-decr"]),
    ("mouth-trans-up", ["mouth-trans-up"]), ("mouth-trans-down", ["mouth-trans-down"]),
    ("mouth-upperlip-height-decr", ["mouth-upperlip-height-decr"]), ("mouth-upperlip-height-incr", ["mouth-upperlip-height-incr"]),
    ("mouth-lowerlip-height-incr", ["mouth-lowerlip-height-incr"]), ("mouth-lowerlip-height-decr", ["mouth-lowerlip-height-decr"]),
    ("mouth-angles-down", ["mouth-angles-down"]), ("mouth-angles-up", ["mouth-angles-up"]),
    ("mouth-upperlip-volume-decr", ["mouth-upperlip-volume-decr"]), ("mouth-lowerlip-volume-incr", ["mouth-lowerlip-volume-incr"]),
    ("chin-width-incr", ["chin-width-incr"]), ("chin-width-decr", ["chin-width-decr"]),
    ("chin-height-incr", ["chin-height-incr"]), ("chin-height-decr", ["chin-height-decr"]),
    ("chin-prominent-incr", ["chin-prominent-incr"]), ("chin-prominent-decr", ["chin-prominent-decr"]),
    ("chin-jaw-drop-incr", ["chin-jaw-drop-incr"]), ("chin-jaw-drop-decr", ["chin-jaw-drop-decr"]),
    ("chin-bones-incr", ["chin-bones-incr"]), ("chin-bones-decr", ["chin-bones-decr"]),
    ("chin-cleft-incr", ["chin-cleft-incr"]),
    ("neck-scale-horiz-incr", ["neck-scale-horiz-incr"]),
]
# The landmarks see positions, not form: a round and a square head can put MediaPipe's points in the same
# places. The reference's shading does see form (analysis §4: a long rectangle, angular jaw, high cheekbones
# over hollow cheeks, low facial fat), so those analysis readings enter as priors with a tighter sigma, and the
# soft, round alternatives are held near zero. A first fit without them chose head-round 0.47 and
# cheek-volume-incr 0.43: a broad, soft face, the opposite of the drawing.
PRIOR = {"head-age-incr": 0.2, "chin-cleft-incr": 0.15, "head-fat-decr": 0.3, "cheek-volume-decr": 0.35,
         "chin-prominent-incr": 0.4, "nose-hump-incr": 0.15, "eyebrows-trans-down": 0.3,
         "head-square": 0.5, "head-rectangular": 0.3, "cheek-bones-incr": 0.5, "chin-bones-incr": 0.3,
         "chin-width-incr": 0.4}
PRIOR_SIGMA = 0.5
PRIOR_SIGMA_BY = {"head-square": 0.3, "head-rectangular": 0.3, "cheek-bones-incr": 0.3, "cheek-volume-decr": 0.3,
                  "head-fat-decr": 0.3, "chin-bones-incr": 0.3,
                  "head-round": 0.2, "head-oval": 0.25, "cheek-volume-incr": 0.2, "head-fat-incr": 0.2,
                  "cheek-bones-decr": 0.2, "head-diamond": 0.25, "head-triangular": 0.25,
                  "head-invertedtriangular": 0.25}
SIGMA_PX = 2.0           # a landmark's sigma in full-frame px (the head is ~110 px; detectors disagree 1-4 %)
SKULL_SIGMA_MM = 1.0     # the skull top may not move (stature 1835 is fitted on it)
# The nuisance head rotation and image shift: loose, because pose.py --solve re-fits the head on the new face
# afterwards. With 6 degrees the fit pushed the nose up and the cheeks down to its bounds, standing in for the
# chin-up pitch (analysis §1: ~12 degrees chin-up to the camera ray) that the rotation prior withheld.
ROT_SIGMA_DEG, SHIFT_SIGMA_PX = 12.0, 4.0

# MediaPipe face-mesh indices. Iris points (468+) are not on the skin. The upper face oval and the forehead
# rows are at the reference's hairline, which the bald model does not have, so they are left out.
FOREHEAD = {10, 338, 297, 332, 284, 251, 109, 67, 103, 54, 21, 162, 151, 108, 69, 104, 68, 71, 337, 299, 333,
            298, 301, 9, 107, 66, 105, 63, 70, 336, 296, 334, 293, 300}
# The bottom of the chin outline: on the reference MediaPipe puts it on the under-chin shadow (y 135.8) where
# the hand reading puts the menton at y 131; on the model it sits 3 px above the menton vertex. That 8 px
# disagreement lengthened the lower face, so these points are left to the hand-read chin (HAND).
CHIN_BOTTOM = {152, 148, 377, 176, 400, 149, 378}
JAW_OVAL = [356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132,
            93, 234, 127]
# The pose solve's own hand-read head points (scripts/stages/pose_solve.py TARGETS: full-frame px, sigma) on the
# model points base.py's landmarks() defines: the nose tip and the menton are mesh vertices, the right ear is
# the centroid of the `ears` group's right half. The face fit uses them too (weighted HAND_WEIGHT), so the face
# it makes is one the pose solve will put in the same place: without them MediaPipe's chin (y 135.8, on the
# reference's under-chin shadow) lengthened the lower face by 13 mm and the re-solved pose then left the chin
# 7 px below the hand-read menton (y 131).
HAND = {"nose_tip": ((815.0, 90.0), 3.0), "chin": ((816.0, 131.0), 4.0), "ear_R": ((762.0, 98.0), 5.0)}
HAND_WEIGHT = {"nose_tip": 10.0, "chin": 10.0, "ear_R": 10.0}
# Tried and rejected (head.md): chin at 60 brought the re-solved menton to 4.8 px but drove chin-height-decr and
# chin-prominent-incr to their bounds and the pose cost up (41.4 against 40.5); MediaPipe reads the reference's
# lower face 2-5 px lower than the hand reading (mouth corners y 112 against 109-111, chin 135.8 against 131).
KEY = {"nose_tip": 1, "chin": 152, "eye_R_outer": 33, "eye_R_inner": 133, "eye_L_inner": 362, "eye_L_outer": 263,
       "mouth_R": 61, "mouth_L": 291, "subnasale": 2, "gonion_R": 172, "gonion_L": 397, "cheek_R": 234,
       "cheek_L": 454}


def say(*a):
    print("[head]", *a, flush=True)


def in_blender():
    try:
        import bpy  # noqa: F401
        return True
    except ImportError:
        return False


def _argv():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


# =========================================================================== Blender: the fit's export

def all_targets():
    return sorted({t for _, ts in PARAMS for t in ts})


def head_region(bd):
    import common as C
    return bd["in_body"] & (C.weight_sum(bd, C.is_head) > 0.3)


def bl_export(out_dir):
    """Open base.blend, export what the solver needs (npz) and render the posed head (ref.head_face)."""
    import bpy
    import common as C
    import base as B
    body, rig = C.open_base()
    mp = B.Mpfb()
    keys = body.data.shape_keys.key_blocks
    for t in all_targets():
        if t not in keys:
            path = mp.targets.target_full_path(t)
            if not path or os.path.basename(path).split(".")[0] != t:
                raise FileNotFoundError(f"MPFB has no target {t!r}")
            mp.targets.load_target(body, path, weight=0.0)
    keys = body.data.shape_keys.key_blocks
    bd = C.body_data(body)
    region = head_region(bd)
    idx = np.where(region)[0]
    n = len(body.data.vertices)

    def key_co(kb):
        a = np.empty(n * 3)
        kb.data.foreach_get("co", a)
        return a.reshape(-1, 3)
    D, W0 = [], []
    for t in all_targets():
        kb = keys[t]
        D.append((key_co(kb) - key_co(kb.relative_key))[idx] * 1000.0)
        W0.append(float(kb.value))
    D = np.array(D, np.float32)
    V_rest = bd["V"][idx]
    # the hero pose and linear blend skinning per vertex: posed = sum_b w_b M_b rest
    C.apply_hero_pose(rig)
    bones = {b.name for b in rig.data.bones if b.use_deform}
    M = {}
    for pb in rig.pose.bones:
        if pb.name in bones:
            M[pb.name] = np.array(pb.matrix) @ np.linalg.inv(np.array(pb.bone.matrix_local))
    A = np.zeros((len(idx), 3, 3))
    T = np.zeros((len(idx), 3))
    for k, vi in enumerate(idx):
        ws = [(bd["groups"][g][vi], g) for g in bones if g in bd["groups"] and bd["groups"][g][vi] > 0]
        s = sum(w for w, _ in ws)
        for w, g in ws:
            A[k] += w / s * M[g][:3, :3]
            T[k] += w / s * M[g][:3, 3] * 1000.0
    P0 = np.einsum("kij,kj->ki", A, V_rest) + T
    # check against Blender's own evaluated posed mesh (helpers masked off in body_data's way)
    mask = [m for m in body.modifiers if m.type == "MASK"]
    for m in mask:
        m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    for m in mask:
        m.show_viewport = True
    co = co.reshape(-1, 3)[idx] * 1000.0
    lbs_err = float(np.abs(co - P0).max())
    rset = set(idx.tolist())
    pos = {v: k for k, v in enumerate(idx)}
    tris = []
    for f in bd["F"]:
        if all(v in rset for v in f):
            for j in range(1, len(f) - 1):
                tris.append((pos[f[0]], pos[f[j]], pos[f[j + 1]]))
    head_b = rig.pose.bones["head"]
    pivot = np.array(rig.matrix_world @ head_b.head) * 1000.0
    top = int(np.argmax(V_rest[:, 2]))
    # the pose solve's model points (base.py landmarks(), on this body) as vertex sets of the head region
    marks = C.base_json()["landmarks"]          # rest positions, written by base.py with this body
    hand_ids = np.full((len(HAND), 64), -1, np.int64)
    for r, k in enumerate(HAND):
        if k == "ear_R":
            ears = bd["groups"]["ears"] > 0.5
            ids = [pos[v] for v in np.where(ears & region & (bd["V"][:, 0] < 0))[0]]
        else:
            ids = [int(np.argmin(np.linalg.norm(V_rest - np.array(marks[k]["rest_mm"]), axis=1)))]
        hand_ids[r, :len(ids[:64])] = ids[:64]
    np.savez_compressed(os.path.join(out_dir, "export.npz"), idx=idx, V_rest=V_rest, P0=co, A=A, D=D,
                        W0=np.array(W0), targets=np.array(all_targets()), tris=np.array(tris, np.int32),
                        pivot=pivot, top=top, hand_ids=hand_ids)
    # the posed head through the hero camera: Workbench, material colours (skin, brows, iris), on grey
    png = os.path.join(out_dir, "model_head.png")
    hide = [o for o in bpy.data.objects if o.name.startswith(("Part.", "Pose.", "Head."))]
    for o in hide:
        o.hide_render = True
    C.render_hero([], "ref.head_face", png)
    say("export", json.dumps({"verts": int(len(idx)), "tris": len(tris), "targets": len(W0), "lbs_err_mm": round(lbs_err, 4)}))
    return png


# =========================================================================== outside Blender: the fit

def blender(args, blend=None):
    exe = os.environ.get("SGT_BLENDER")
    if not exe:
        raise SystemExit("SGT_BLENDER is not set: source cache/env.sh")
    cmd = [exe, "-b"] + ([blend] if blend else []) + ["--python"] + args
    t = time.perf_counter()
    r = subprocess.run(cmd, cwd=PROJECT, capture_output=True, text=True, errors="replace")
    lines = [l for l in r.stdout.splitlines() if l.startswith(("[head]", "[base]", "[pose]", "[render]", "Error", "Traceback")) or "Error" in l]
    for l in lines[-12:]:
        print("   ", l[:300], flush=True)
    if r.returncode != 0 or "Traceback" in r.stdout + r.stderr:
        print(r.stdout[-4000:], r.stderr[-4000:])
        raise SystemExit(f"Blender failed: {' '.join(args)}")
    return time.perf_counter() - t


def composite_grey(png, out, grey=0.22):
    from PIL import Image
    im = Image.open(png).convert("RGBA")
    bg = Image.new("RGBA", im.size, tuple(int(grey * 255) for _ in range(3)) + (255,))
    bg.alpha_composite(im)
    bg.convert("RGB").save(out)
    return out


_DET = None


def mp_landmarks(png):
    """MediaPipe FaceLandmarker (the take 1 model) on an 850 x 850 crop: 478 points in FULL-frame px."""
    global _DET
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
    from PIL import Image
    if _DET is None:
        with open(MP_MODEL, "rb") as f:
            buf = f.read()
        _DET = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_buffer=buf), num_faces=1))
    arr = np.ascontiguousarray(np.array(Image.open(png).convert("RGB")))
    res = _DET.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=arr))
    if not res.face_landmarks:
        return None
    h, w = arr.shape[:2]
    pts = np.array([(p.x * w, p.y * h) for p in res.face_landmarks[0]])
    return pts / SCALE + np.array(BOX[:2], float)


def raycast(cam, xy, P, tris):
    """Cast the hero camera's rays through full-frame pixels xy onto the triangles (P mm, tris). Returns, per
    ray, (tri index, barycentric (u, v, w), depth mm) or None."""
    o, d = cam.ray(xy)
    o = o * 1000.0
    a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    e1, e2 = b - a, c - a
    out = []
    for oi, di in zip(o, d):
        pv = np.cross(di, e2)
        det = np.einsum("ij,ij->i", e1, pv)
        ok = np.abs(det) > 1e-9
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = oi - a
        u = np.einsum("ij,ij->i", tv, pv) * inv
        qv = np.cross(tv, e1)
        v = (qv @ di) * inv
        t = np.einsum("ij,ij->i", e2, qv) * inv
        hit = ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (t > 0)
        if not hit.any():
            out.append(None)
            continue
        k = np.where(hit)[0][np.argmin(t[hit])]
        out.append((int(k), (1 - u[k] - v[k], u[k], v[k]), float(t[k])))
    return out


def rot(rx, ry, rz):
    from eval import camproj
    return camproj.euler_xyz(rx, ry, rz)


def solve(E, corr, ref_xy, weights, cam, nuisance=True):
    """Least squares on the parameter weights (and a nuisance head rotation about the posed head joint plus
    an image-plane shift, both small, when nuisance). corr: per landmark (vertex ids (3,), bary (3,)).
    Returns the fit dict."""
    from scipy.optimize import least_squares
    targets = list(E["targets"])
    tix = {t: i for i, t in enumerate(targets)}
    W0 = E["W0"]
    # parameter -> target matrix S (n_targets x n_params)
    S = np.zeros((len(targets), len(PARAMS)))
    for j, (_, ts) in enumerate(PARAMS):
        for t in ts:
            S[tix[t], j] = 1.0
    x0 = np.array([np.mean([W0[tix[t]] for t in ts]) for _, ts in PARAMS])
    prior = np.array([PRIOR.get(nm, 0.0) for nm, _ in PARAMS])
    psig = np.array([PRIOR_SIGMA_BY.get(nm, PRIOR_SIGMA) for nm, _ in PARAMS])
    vid = np.array([c[0] for c in corr])
    bar = np.array([c[1] for c in corr])
    A, D, P0 = E["A"], E["D"], E["P0"]
    # posed displacement per target at each landmark: sum_k bar_k A_vk D_t,vk -> (n_lm, n_targets, 3)
    Dp = np.einsum("lk,lkij,tlkj->lti", bar, A[vid], D[:, vid, :])
    X0 = np.einsum("lk,lki->li", bar, P0[vid])
    top = int(E["top"])
    Dtop = D[:, top, 2]
    pivot = E["pivot"]
    sw = np.sqrt(weights)
    npar = len(PARAMS)
    # hand points: mean of their vertices' posed positions and displacements
    hid = E["hand_ids"]
    HX0 = np.array([P0[r[r >= 0]].mean(0) for r in hid])
    HD = np.array([np.einsum("kij,tkj->ti", A[r[r >= 0]], D[:, r[r >= 0], :]) / (r >= 0).sum() for r in hid])
    Hxy = np.array([v[0] for v in HAND.values()])
    Hsig = np.array([v[1] / math.sqrt(HAND_WEIGHT[k]) for k, v in HAND.items()])

    def place(X, z):
        if nuisance:
            R = rot(*np.radians(z[npar:npar + 3]))
            X = pivot + (X - pivot) @ R.T
        xy = cam.project(X / 1000.0)
        if nuisance:
            xy = xy + z[npar + 3:npar + 5]
        return xy

    def model(z):
        x = z[:npar]
        dw = S @ (x - x0)
        X = X0 + np.einsum("lti,t->li", Dp, dw)
        return place(X, z), dw

    def hand(z, dw):
        return place(HX0 + np.einsum("lti,t->li", HD, dw), z)

    def res(z):
        xy, dw = model(z)
        r = ((xy - ref_xy) / SIGMA_PX * sw[:, None]).ravel()
        rh = ((hand(z, dw) - Hxy) / Hsig[:, None]).ravel()
        rp = (z[:npar] - prior) / psig
        rt = [float(Dtop @ dw) / SKULL_SIGMA_MM]
        extra = []
        if nuisance:
            extra = list(z[npar:npar + 3] / ROT_SIGMA_DEG) + list(z[npar + 3:npar + 5] / SHIFT_SIGMA_PX)
        return np.concatenate([r, rh, rp, rt, extra])

    z0 = np.concatenate([x0, np.zeros(5 if nuisance else 0)])
    lo = np.concatenate([np.zeros(npar), np.full(5 if nuisance else 0, -np.inf)])
    hi = np.concatenate([np.ones(npar), np.full(5 if nuisance else 0, np.inf)])
    xy0, _ = model(z0)
    sol = least_squares(res, np.clip(z0, lo, hi), bounds=(lo, hi), x_scale=1.0, method="trf", max_nfev=400)
    xy1, dw = model(sol.x)
    _, dw0 = model(z0)
    h0, h1 = hand(z0, dw0), hand(sol.x, dw)
    e0 = np.linalg.norm(xy0 - ref_xy, axis=1)
    e1 = np.linalg.norm(xy1 - ref_xy, axis=1)
    x = sol.x[:npar]
    tw = {t: round(float(W0[tix[t]] + dw[tix[t]]), 4) for t in targets}
    return {"params": {nm: round(float(v), 4) for (nm, _), v in zip(PARAMS, x)}, "targets": tw,
            "nuisance_rot_deg": [round(float(v), 2) for v in sol.x[npar:npar + 3]] if nuisance else None,
            "nuisance_shift_px": [round(float(v), 2) for v in sol.x[npar + 3:npar + 5]] if nuisance else None,
            "rms_px_before": round(float(np.sqrt(np.mean(e0 ** 2))), 3),
            "rms_px_after": round(float(np.sqrt(np.mean(e1 ** 2))), 3),
            "skull_top_dz_mm": round(float(Dtop @ dw), 2),
            "hand_px_before": {k: round(float(np.linalg.norm(h0[i] - Hxy[i])), 2) for i, k in enumerate(HAND)},
            "hand_px_after": {k: round(float(np.linalg.norm(h1[i] - Hxy[i])), 2) for i, k in enumerate(HAND)}, "cost": float(sol.cost), "status": int(sol.status),
            "xy_before": xy0, "xy_after": xy1}


def measure(it_dir, label):
    """Blender export + render, MediaPipe on the render and the reference, correspondences by raycast."""
    from eval import camproj
    os.makedirs(it_dir, exist_ok=True)
    blender([os.path.abspath(__file__), "--", "--export", it_dir])
    E = dict(np.load(os.path.join(it_dir, "export.npz")))
    model_png = composite_grey(os.path.join(it_dir, "model_head.png"), os.path.join(it_dir, "model_head_grey.png"))
    ref_xy = mp_landmarks(REF_CROP)
    mod_xy = mp_landmarks(model_png)
    if mod_xy is None:
        raise SystemExit(f"MediaPipe found no face in {model_png}")
    cam = camproj.HERO
    use = [i for i in range(468) if i not in FOREHEAD and i not in CHIN_BOTTOM]
    hits = raycast(cam, mod_xy[use], E["P0"], E["tris"])
    depths = np.array([h[2] for h in hits if h is not None])
    med = float(np.median(depths))
    corr, keep, w = [], [], []
    oval = set(JAW_OVAL)
    for i, h in zip(use, hits):
        if h is None or h[2] > med + 40.0:      # through the eye fissure or past the silhouette
            continue
        corr.append((E["tris"][h[0]], np.array(h[1])))
        keep.append(i)
        w.append(1.5 if i in oval else 1.0)
    say(f"{label}: {len(keep)} landmarks of {len(use)} cast onto the skin (median depth {med:.0f} mm)")
    return E, corr, np.array(keep), np.array(w), ref_xy, mod_xy


def overlay(png, ref_xy, mod_xy, keep, out, fitted=None):
    """The reference crop with the reference landmarks (red) and the model's (green; fitted: cyan)."""
    from PIL import Image, ImageDraw
    im = Image.open(REF_CROP).convert("RGB")
    mo = Image.open(png).convert("RGB").resize(im.size)
    sheet = Image.new("RGB", (im.width * 2 + 10, im.height), (20, 20, 20))
    d = ImageDraw.Draw(im)

    def c(p):
        return ((p[0] - BOX[0]) * SCALE, (p[1] - BOX[1]) * SCALE)
    for i in keep:
        a, b = c(ref_xy[i]), c(mod_xy[i])
        d.line([a, b], fill=(255, 255, 0), width=1)
        d.ellipse([a[0] - 3, a[1] - 3, a[0] + 3, a[1] + 3], fill=(255, 40, 40))
        d.ellipse([b[0] - 3, b[1] - 3, b[0] + 3, b[1] + 3], fill=(40, 255, 40))
    if fitted is not None:
        for p in fitted:
            q = c(p)
            d.ellipse([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], fill=(40, 220, 255))
    sheet.paste(im, (0, 0))
    sheet.paste(mo, (im.width + 10, 0))
    sheet.save(out)
    return out


def fit_main(iters, fresh=False):
    os.makedirs(WORK, exist_ok=True)
    if fresh and os.path.exists(FIT_JSON):
        os.remove(FIT_JSON)
    log = []
    for it in range(iters):
        t0 = time.perf_counter()
        blender([os.path.join(SCRIPTS, "stages", "base.py")])
        it_dir = os.path.join(WORK, f"iter{it}")
        E, corr, keep, w, ref_xy, mod_xy = measure(it_dir, f"iteration {it}")
        cam = __import__("eval.camproj", fromlist=["HERO"]).HERO
        fit = solve(E, corr, ref_xy[keep], w, cam)
        overlay(os.path.join(it_dir, "model_head_grey.png"), ref_xy, mod_xy, keep,
                os.path.join(it_dir, "landmarks.png"), fit["xy_after"])
        rec = {k: v for k, v in fit.items() if not k.startswith("xy_")}
        rec.update({"iteration": it, "landmarks": int(len(keep)), "seconds": round(time.perf_counter() - t0, 1)})
        log.append(rec)
        say(f"iteration {it}: rms {fit['rms_px_before']} -> {fit['rms_px_after']} px (model, full frame), "
            f"nuisance rot {fit['nuisance_rot_deg']} deg shift {fit['nuisance_shift_px']} px, skull top {fit['skull_top_dz_mm']} mm, "
            f"hand points {fit['hand_px_before']} -> {fit['hand_px_after']}")
        out = {"note": "MPFB face/head target weights for scripts/stages/base.py, fitted by scripts/parts/head.py --fit "
                       "(least squares on MediaPipe face landmarks through the hero camera; head.md)",
               "targets": {k: v for k, v in fit["targets"].items() if abs(v) >= 1e-3},
               "params": fit["params"], "prior": PRIOR, "prior_sigma": PRIOR_SIGMA, "prior_sigma_by": PRIOR_SIGMA_BY,
               "sigma_px": SIGMA_PX, "log": log}
        with open(FIT_JSON, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, indent=1)
    blender([os.path.join(SCRIPTS, "stages", "base.py")])
    return log


def check_main(tag="check"):
    """The landmark residual on the current base.blend and hero pose, nothing fitted."""
    from eval import camproj
    E, corr, keep, w, ref_xy, mod_xy = measure(os.path.join(WORK, tag), tag)
    e = np.linalg.norm(mod_xy[keep] - ref_xy[keep], axis=1)
    keyres = {k: round(float(np.linalg.norm(mod_xy[i] - ref_xy[i])), 2) for k, i in KEY.items()}
    os.makedirs(OUT, exist_ok=True)
    overlay(os.path.join(WORK, tag, "model_head_grey.png"), ref_xy, mod_xy, keep, os.path.join(OUT, f"head_landmarks_{tag}.png"))
    out = {"landmarks": int(len(keep)), "rms_px": round(float(np.sqrt(np.mean(e ** 2))), 3),
           "median_px": round(float(np.median(e)), 3), "max_px": round(float(e.max()), 2),
           "jaw_oval_rms_px": round(float(np.sqrt(np.mean(np.array([np.linalg.norm(mod_xy[i] - ref_xy[i]) for i in JAW_OVAL]) ** 2))), 3),
           "key_px": keyres, "note": "MediaPipe on the model's hero render vs on the reference crop, full-frame px"}
    with open(os.path.join(WORK, tag, "check.json"), "w") as f:
        json.dump(out, f, indent=1)
    say(tag, json.dumps(out))
    return out


# =========================================================================== entry

def main():
    if in_blender():
        a = _argv()
        if a and a[0] == "--export":
            bl_export(a[1])
            return 0
        return bl_build(a)
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--iters", type=int, default=3)
    ap.add_argument("--fresh", action="store_true", help="start from MPFB's default face (removes head_fit.json)")
    ap.add_argument("--check", default=None, const="check", nargs="?")
    args = ap.parse_args()
    if args.fit:
        fit_main(args.iters, args.fresh)
    if args.check:
        check_main(args.check)
    return 0


# =========================================================================== Blender: the part

HAIR_HEX = "#271b14"          # round 2: analysis §8 base #3a2a1e rendered at value 0.46 against the drawn 0.24 under the key
STUBBLE_HEX = "#3b2a22"       # analysis §9: the stubble hairs
HAIR = {                      # mm; analysis §8 (lengths), consolidated hairline, pose README (head top)
    # Hair 35-45 mm long stands at an angle, so the mass is thinner than the length: the drawn mass top is
    # about 4 px (~10-15 mm) over the scalp and the spike tips 6 px (~13 mm) higher. A first cap built with
    # the lengths as thickness (42 / 30) stood 49 mm over the skull: a pompadour helmet.
    # round 2: the mass a little lower (the spikes below carry the height the round-1 cap made with bulk)
    "top_front": 17.0,        # the lifted fringe at the front
    "top_back": 10.0,         # the crown
    "tufts": 60, "tuft_gap": 9.0,          # clumps on the top, at least this far apart (mm)
    "tuft_len": (7.0, 13.0), "tuft_r": (4.2, 6.5),   # clump length and root radius (mm): piecey clumps, not thorns
    "side": 2.5,              # the temple taper, 3 -> 1, skin-blended fade to the ear top
    "back_low": 7.0,          # the occipital taper, 8 at the bulge -> 1 at the nape
    "edge_fade": 9.0,         # thickness ramps from the hairline over this surface distance
    "trichion_z": 1783.0,     # the front hairline (reference: 24 px, ~50 mm above the glabella)
}
HEAD_CENTRE = np.array([0.0, -25.0, 1735.0])   # mm: between the ears, at about the ear top (rest)


def _surface_dist(V, E, seeds, cap=60.0):
    """Graph (edge-length) distance from the seed vertices, capped: a cheap surface distance."""
    import heapq
    n = len(V)
    L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    adj = [[] for _ in range(n)]
    for (a, b), l in zip(E, L):
        adj[a].append((b, l))
        adj[b].append((a, l))
    d = np.full(n, cap)
    h = []
    for s in np.where(seeds)[0]:
        d[s] = 0.0
        h.append((0.0, int(s)))
    heapq.heapify(h)
    while h:
        dist, u = heapq.heappop(h)
        if dist > d[u]:
            continue
        for v, l in adj[u]:
            nd = dist + l
            if nd < d[v]:
                d[v] = nd
                heapq.heappush(h, (nd, v))
    return d


def _smoothstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def relax_boundary(C, V, F, bvh, iters=40, pin_inner=8):
    """Straighten a submesh's staircase boundary (it follows MPFB's edges): smooth each boundary loop along
    itself, snap it back onto the skin, then relax the interior with the boundary pinned and snap again."""
    from mathutils import Vector
    V = np.array(V, float)
    loops = C.boundary_loops(F)
    for lp in loops:
        if len(lp) < 6:
            continue
        P = V[lp]
        for _ in range(iters):
            P = 0.5 * P + 0.25 * (np.roll(P, 1, 0) + np.roll(P, -1, 0))
        for k, i in enumerate(lp):
            loc = bvh.find_nearest(Vector(P[k]))[0]
            V[i] = np.array(loc) if loc is not None else P[k]
    E = C.edges_of(F)
    edge = C.boundary_verts(F, len(V))
    V = C.smooth_field(V, E, iters=pin_inner, lam=0.5, pin=edge)
    for i in range(len(V)):
        loc = bvh.find_nearest(Vector(V[i]))[0]
        if loc is not None:
            V[i] = np.array(loc)
    return V


def _tuft(base, direction, side, length, r0, rng, rings=5, segs=6):
    """A tapered, slightly flattened and bent clump of hair (a cone of quads ending in a point): base (3,) on the
    cap, direction (3,) unit, side (3,) unit across the sweep. Returns (V, F) local to the tuft."""
    d = np.asarray(direction, float)
    s = np.asarray(side, float)
    s = s - d * (s @ d)
    s /= np.linalg.norm(s) + 1e-9
    t = np.cross(d, s)
    bend = rng.uniform(0.3, 0.55)
    V, F = [], []
    for i in range(rings):
        u = i / (rings - 1)
        c = base + d * length * u + t * length * bend * u * u      # bows along the sweep's lean
        r = r0 * (1.0 - u) ** 1.2
        for j in range(segs):
            a = 2 * np.pi * j / segs
            V.append(c + s * np.cos(a) * r * 1.5 + t * np.sin(a) * r * 0.8)
    tip = base + d * length * 1.12 + t * length * bend * 1.25
    V.append(tip)
    for i in range(rings - 1):
        for j in range(segs):
            a, b = i * segs + j, i * segs + (j + 1) % segs
            F.append((a, b, b + segs, a + segs))
    k = len(V) - 1
    for j in range(segs):
        F.append(((rings - 1) * segs + j, (rings - 1) * segs + (j + 1) % segs, k))
    return np.array(V), F


def build_hair(C, bd, coll, seed=7):
    """Head.Hair: a round-1 cap. The scalp (MPFB's `scalp` group, plus the forehead above the reference's
    hairline, less the ears) is refined twice on the skin and pushed out by a thickness field: a lifted
    fringe and a thick textured top, a skin-close taper at the sides and the nape, a ramp at the hairline;
    piecey spikes on the top (the silhouette spikes the analysis calls a key likeness cue) lean up and to
    his right like the drawn sweep. Returns the object and its numbers."""
    V, F, g = bd["V"], bd["F"], bd["groups"]
    region = head_region(bd)
    d = V - HEAD_CENTRE
    keep = region & (g["ears"] < 0.3) & ((g["scalp"] > 0.5) | ((V[:, 2] >= HAIR["trichion_z"]) & (d[:, 1] < 0)))
    Vs, Fs, _ = C.submesh(V, F, keep)
    bvh = C.skin_bvh(bd)
    Vs, Fs, Ns = C.refine_on_skin(Vs, Fs, bvh, cuts=1)
    Vs, Fs, Ns = C.refine_on_skin(Vs, Fs, bvh, cuts=1)
    Vs = relax_boundary(C, Vs, Fs, bvh)
    Ns = C.vertex_normals(Vs, Fs)
    E = C.edges_of(Fs)
    d = Vs - HEAD_CENTRE
    az = np.degrees(np.arctan2(d[:, 0], -d[:, 1]))              # 0 front, +90 his left, -90 his right
    el = np.degrees(np.arctan2(d[:, 2], np.hypot(d[:, 0], d[:, 1])))
    aaz = np.abs(az)
    t_top = HAIR["top_back"] + (HAIR["top_front"] - HAIR["top_back"]) * np.clip(np.cos(np.radians(az)), 0, 1)
    t_low = HAIR["side"] + (HAIR["back_low"] - HAIR["side"]) * _smoothstep(95, 165, aaz)
    el_lo = 12.0 + 22.0 * np.abs(np.sin(np.radians(az)))           # the parietal ridge: higher at the sides
    s = _smoothstep(el_lo, el_lo + 28.0, el)
    edge = C.boundary_verts(Fs, len(Vs))
    dist = _surface_dist(Vs, E, edge)
    ramp = _smoothstep(0.0, HAIR["edge_fade"], dist)
    t = (t_low + (t_top - t_low) * s) * (0.15 + 0.85 * ramp)
    t[edge] = 0.4
    # direction: the normal, tilted up and forward on the top and fringe, towards his right (-X): the sweep
    sweep = np.array([-0.30, -0.35, 0.85])
    sweep /= np.linalg.norm(sweep)
    w = (s * 0.45)[:, None]
    D = Ns * (1 - w) + sweep * w
    D /= np.linalg.norm(D, axis=1, keepdims=True)
    P = Vs + D * t[:, None]
    # piecey clumps and spikes on the top: Gaussian bumps at random scalp points
    rng = np.random.default_rng(seed)
    top = np.where(s > 0.55)[0]
    spikes = []
    if len(top):
        for c in rng.choice(top, size=min(30, len(top)), replace=False):
            sig = rng.uniform(4.0, 7.0)
            hgt = rng.uniform(1.5, 4.5) * (0.7 + 0.3 * float(np.cos(np.radians(az[c]))))
            r = np.linalg.norm(Vs - Vs[c], axis=1)
            P += (D * (hgt * np.exp(-0.5 * (r / sig) ** 2) * s)[:, None])
    P = C.taubin(P, E, iters=2, pin=edge)
    P = C.push_out(P, bvh, np.maximum(0.4, 0.5 * t))
    # round 2: the silhouette spikes (analysis §8: 8-10 distinct spikes against the background; "a smooth hair cap
    # will fail"). Tapered clumps rooted in the cap's top, leaning with the sweep (up, forward, to his right),
    # longest at the front, none on the tapered sides: short and textured on top, shorter at the sides.
    Pn = C.vertex_normals(P, Fs)
    tops = np.where((s > 0.62) & ~edge)[0]
    order = rng.permutation(tops)
    roots = []
    for c in order:
        if all(np.linalg.norm(Vs[c] - Vs[q]) > HAIR["tuft_gap"] for q in roots):
            roots.append(c)
        if len(roots) >= HAIR["tufts"]:
            break
    Vt, Ft = [np.asarray(P)], [list(Fs)]
    nv = len(P)
    for c in roots:
        front = float(np.clip(np.cos(np.radians(az[c])), 0, 1))
        dvec = Pn[c] * 0.3 + sweep * 0.7 + rng.normal(0, 0.2, 3)          # lying with the sweep, tips lifting
        dvec /= np.linalg.norm(dvec)
        length = rng.uniform(*HAIR["tuft_len"]) * (0.75 + 0.45 * front) * s[c]
        r0 = rng.uniform(*HAIR["tuft_r"])
        side = np.cross(dvec, sweep) + rng.normal(0, 0.3, 3)
        tv, tf = _tuft(P[c] - dvec * 2.5, dvec, side, length, r0, rng)
        Vt.append(tv)
        Ft.append([tuple(i + nv for i in f) for f in tf])
        nv += len(tv)
        spikes.append(round(float(length), 1))
    P = np.concatenate(Vt)
    Fs = [f for fl in Ft for f in fl]
    mat = C.flat_material("Head.Mat.Hair", HAIR_HEX, rough=0.75, sheen=0.0)     # round 1 sheen 0.3 read tan
    ob = C.mesh_object("Head.Hair", P, Fs, coll, mat=mat)
    ob["sgt_clay"] = (0.30, 0.25, 0.21)
    C.subsurf(ob, 1)
    info = {"verts": int(len(P)), "thickness_mm": {"max": round(float(t.max()), 1), "top_median": round(float(np.median(t[s > 0.8])), 1),
            "side_median": round(float(np.median(t[(s < 0.1) & (aaz > 60) & (aaz < 120)])) if ((s < 0.1) & (aaz > 60) & (aaz < 120)).any() else 0.0, 1)},
            "spikes": len(spikes), "top_z_mm": round(float(P[:, 2].max()), 1), "skull_top_z_mm": round(float(V[region, 2].max()), 1),
            "front_hairline_z_mm": round(float(Vs[edge & (np.abs(Vs[:, 0]) < 15) & (Vs[:, 1] < -60), 2].min()), 1)
            if (edge & (np.abs(Vs[:, 0]) < 15) & (Vs[:, 1] < -60)).any() else None}
    return ob, info


def stubble_density(C, bd, marks):
    """Per-vertex stubble density (0..1) on the head (analysis §9): dense on the chin, the soul patch, the
    moustache, along the jawline and under the jaw; medium on the lower cheeks below the line from the
    tragus to the mouth corner; bare above it, on the lips, the nose and the neck below the jaw."""
    V, g, N = bd["V"], bd["groups"], bd["N"]
    region = head_region(bd) & (g["ears"] < 0.3)
    lips = g["lips"] > 0.3
    L = V[lips & region]
    lip_top, lip_bot = L[:, 2].max(), L[:, 2].min()
    mouth_hw = np.abs(L[:, 0]).max()
    nose = np.array(marks["nose_tip"]["rest_mm"])
    chin = np.array(marks["chin"]["rest_mm"])
    subnasale_z = nose[2] - 14.0
    dens = np.zeros(len(V))
    for side, ear in ((-1, "ear_R"), (1, "ear_L")):
        T = np.array(marks[ear]["rest_mm"]) + np.array([0.0, 0.0, -12.0])      # the tragus, about
        M = np.array([side * mouth_hw, L[np.argmax(np.abs(L[:, 0]))][1], (lip_top + lip_bot) / 2])
        sel = region & (V[:, 0] * side > 0)
        # height above the tragus -> mouth-corner line, in the side view (y, z)
        tline = np.clip((V[:, 1] - T[1]) / (M[1] - T[1]), -0.3, 1.3)
        zline = T[2] + tline * (M[2] - T[2])
        below = _smoothstep(4.0, -6.0, V[:, 2] - zline)                  # 1 below the line
        front = _smoothstep(T[1] + 12.0, T[1] - 4.0, V[:, 1])            # in front of the ear
        dens = np.where(sel, np.maximum(dens, 0.6 * below * front), dens)
    # dense: chin and soul patch, moustache, under the jaw (normals facing down), the jawline
    chin_zone = (V[:, 2] < lip_bot - 2.0) & (np.abs(V[:, 0]) < mouth_hw + 6.0) & (V[:, 1] < chin[1] + 30.0)
    moust = (V[:, 2] > lip_top + 1.0) & (V[:, 2] < subnasale_z - 1.0) & (np.abs(V[:, 0]) < mouth_hw + 4.0) & (V[:, 1] < nose[1] + 45.0)
    ear_y = min(marks["ear_R"]["rest_mm"][1], marks["ear_L"]["rest_mm"][1])
    under = (N[:, 2] < -0.35) & (V[:, 2] > chin[2] - 24.0) & (V[:, 2] < lip_bot) & (V[:, 1] < ear_y - 5.0)
    dense = region & (chin_zone | moust | under)
    dens = np.where(dense, 1.0, dens)
    dens[lips] = 0.0
    dens[V[:, 2] < chin[2] - 28.0] = 0.0
    dens[V[:, 1] > ear_y + 8.0] = 0.0
    dens[~region] = 0.0
    return dens


def build_stubble(C, bd, coll, marks):
    """Head.Stubble: a shell 0.8 mm off the skin where the density is above 0.08, with two materials by
    density (dense / medium) whose viewport colours are the skin darkened by the stubble (what Workbench
    shows); in Cycles both mix the stubble colour over a transparent BSDF by the density attribute, so the
    edges fade. No strands yet."""
    import bpy
    E = C.edges_of(bd["F"])
    dens = stubble_density(C, bd, marks)
    dens = np.clip(C.smooth_field(dens, E, iters=6, lam=0.5), 0, 1)
    dens[bd["groups"]["lips"] > 0.3] = 0.0
    keep = dens > 0.08
    Vs, Fs, used = C.submesh(bd["V"], bd["F"], keep)
    ds = dens[used]
    # the boundary loop only: relaxing the interior slides vertices across the skin's facets and the shell's
    # chords then dip under it (skin showed through in spots)
    Vs = relax_boundary(C, Vs, Fs, C.skin_bvh(bd), iters=25, pin_inner=0)
    Ns = C.vertex_normals(Vs, Fs)
    P = C.push_out(Vs + Ns * 0.8, C.skin_bvh(bd), 0.6)
    import base as B
    skin = np.array(C.hex_rgb(B.SKIN_ALBEDO))
    hair = np.array(C.hex_rgb(STUBBLE_HEX))
    mats = []
    for nm, cover in (("Head.Mat.Stubble.Dense", 0.55), ("Head.Mat.Stubble.Medium", 0.28)):
        m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = (*hair, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.75
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "stubble_density"
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 0.6
        nt.links.new(attr.outputs["Fac"], mul.inputs[0])
        nt.links.new(mul.outputs[0], mix.inputs["Fac"])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(bsdf.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        if hasattr(m, "blend_method"):
            m.blend_method = "HASHED"
        m.diffuse_color = (*(skin * (1 - cover) + hair * cover), 1.0)
        m["sgt_hex"] = STUBBLE_HEX
        mats.append(m)
    fd = np.array([ds[list(f)].mean() for f in Fs])
    ob = C.mesh_object("Head.Stubble", P, Fs, coll, mats=mats, face_mat=(fd < 0.5).astype(int))
    at = ob.data.attributes.new("stubble_density", "FLOAT", "POINT")
    at.data.foreach_set("value", ds.astype(np.float32))
    ob["sgt_clay"] = (0.55, 0.48, 0.43)
    return ob, {"verts": int(len(P)), "dense_faces": int((fd >= 0.5).sum()), "medium_faces": int((fd < 0.5).sum())}


# ----------------------------------------------------------------------------- renders

HEAD_T = np.array([0.0, -30.0, 1738.0])          # rest view target (mm)
# round 2: both profiles (side = from his right, side_L = from his left) and the three-quarter from his front-right
HEAD_VIEWS = {"front": (np.array([0.0, -1.0, 0.0]), 330.0), "side": (np.array([-1.0, 0.0, 0.0]), 330.0),
              "side_L": (np.array([1.0, 0.0, 0.0]), 330.0),
              "threequarter": (np.array([-0.64, -0.75, 0.12]), None)}
# the reference's face zooms (archive/v1/notes/analysis_face_grooming.md §12): full-frame box and scale
ZOOMS = {"z_head_x8": ((745, 30, 865, 150), 8), "g_eye_right_x20": ((784, 66, 812, 88), 20),
         "g_nose_mouth_x14": ((796, 84, 840, 134), 14), "g_jaw_x10": ((755, 95, 860, 140), 10)}


def _clay_colours(coll):
    import bpy
    import common as C
    ob = bpy.data.objects.get
    ob(C.BODY).color = (*C.SKIN_CLAY, 1.0)
    for n, c in (("Body.Eyes", (0.85, 0.83, 0.8)), ("Body.Eyebrows", (0.32, 0.27, 0.24)), ("Body.Eyelashes", (0.55, 0.47, 0.42))):
        if ob(n):
            ob(n).color = (*c, 1.0)
    for o in coll.all_objects:
        o.color = (*(o.get("sgt_clay") or (0.45, 0.47, 0.5)), 1.0)


def render_rest_head(coll, samples, prefix="head_"):
    """renders/head/<prefix>rest_{front,side,side_L,threequarter}_{clay,cycles}.png on the rest body."""
    import bpy
    import common as C
    from eval import render as R
    sc = bpy.context.scene
    restore = C.visible_only([coll])
    cam = C._aux_camera()
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 900, 1000, 100
    out = []
    for mode in ("clay", "cycles"):
        if mode == "clay":
            C._workbench(sc, "OBJECT", bg=(0.86, 0.86, 0.84))
            _clay_colours(coll)
        else:
            _eval_lights(sc)
            R._set_tier(sc, "look", samples=samples)
            sc.render.film_transparent = False
            from eval import scene as escene
            escene.colour_management(sc)
            sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGB"
        for v, (dv, ortho) in HEAD_VIEWS.items():
            if ortho:
                cam.data.type, cam.data.ortho_scale = "ORTHO", ortho * C.MM
                C._look(cam, HEAD_T + dv * 3000.0, HEAD_T)
            else:
                cam.data.type, cam.data.lens = "PERSP", 85.0
                C._look(cam, HEAD_T + dv * 1250.0, HEAD_T)
            cam.data.sensor_fit = "AUTO"
            out.append(C._render(os.path.join(OUT, f"{prefix}rest_{v}_{mode}.png")))
    restore()
    return out


def _eval_lights(sc):
    """Round 0's evaluation lights (scripts/eval/scene.py, at 0.3 of spec 17's energy) and world, once."""
    import bpy
    from eval import scene as escene
    if not any(o.type == "LIGHT" and o.name.startswith("Scene.") for o in bpy.data.objects):
        for L in escene.build_lights(sc):
            L.data.energy *= 0.3
        escene.build_world(sc, "hdri")


def render_hero_cycles(coll, preset, path, samples):
    """The posed body and head through the hero camera (scripts/eval/camera.py preset), Cycles with round 0's
    evaluation lights (scene.py at 0.3 of spec 17's energy) and world; transparent film."""
    import bpy
    import common as C
    from eval import camera, render as R, scene as escene
    sc = bpy.context.scene
    restore = C.visible_only([coll])
    if bpy.data.objects.get("Scene.Cam.Hero") is None:
        camera.hero_camera(sc)
    _eval_lights(sc)
    escene.colour_management(sc)
    camera.apply(camera.load_registry().get(preset), sc, percent=100)
    R._set_tier(sc, "look", samples=samples)
    sc.render.film_transparent = True
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGBA"
    C._render(path)
    restore()
    return path


def sheet3(ref_png, render_png, out_png, bg=(0.16, 0.16, 0.17)):
    """[reference | render on a flat background | render over the reference at 50 %] (common.pair_sheet's layout
    with an even overlay)."""
    import common as C
    ref = C._load_px(ref_png)
    rnd = C._load_px(render_png)
    h, w = rnd.shape[:2]
    if ref.shape[:2] != (h, w):
        ref = C._fit(ref, h, w)
    a = rnd[..., 3:4]
    solo = rnd[..., :3] * a + np.array(bg) * (1 - a)
    over = 0.5 * solo + 0.5 * ref[..., :3]
    gap = np.ones((h, 10, 3), np.float32)
    s = np.concatenate([ref[..., :3], gap, solo, gap, over], 1)
    C._save_px(np.concatenate([s, np.ones((h, s.shape[1], 1), np.float32)], 2), out_png)
    return out_png


def render_zooms(coll, samples, prefix):
    """The reference's face zooms (ZOOMS) through the hero camera, Cycles, each beside its reference zoom."""
    import bpy
    import common as C
    from eval import camera, render as R, scene as escene
    sc = bpy.context.scene
    restore = C.visible_only([coll])
    _eval_lights(sc)
    escene.colour_management(sc)
    out = []
    for name, (box, scale) in ZOOMS.items():
        camera.apply({"camera": {"type": "hero"}, "render": {"border_px": list(box), "scale": scale}}, sc, percent=100)
        R._set_tier(sc, "look", samples=samples)
        sc.render.film_transparent = True
        sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGBA"
        p = C._render(os.path.join(OUT, f"{prefix}zoom_{name}.png"))
        out.append(sheet3(os.path.join(PROJECT, "ref", "face_zooms", name + ".png"), p,
                          os.path.join(OUT, f"{prefix}zoom_{name}_sheet.png")))
    restore()
    return out


def render_views_r001(coll, samples, prefix):
    """The rest head through head_shape.py's fitted cameras of gen/R001's views (cache/head_r2/cams.json), Cycles,
    beside each view."""
    import bpy
    import common as C
    import head_shape as HS
    from eval import render as R, scene as escene
    cams = os.path.join(HS.WORK, "cams.json")
    if not os.path.exists(cams):
        return []
    sc = bpy.context.scene
    restore = C.visible_only([coll])
    _eval_lights(sc)
    out = []
    for v, par in json.load(open(cams))["views"].items():
        HS.bl_view_render(sc, par, os.path.join(OUT, f"{prefix}r001_{v}.png"))
        R._set_tier(sc, "look", samples=samples)
        escene.colour_management(sc)
        sc.render.film_transparent = True
        sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGBA"
        p = C._render(os.path.join(OUT, f"{prefix}r001_{v}.png"))
        out.append(sheet3(os.path.join(HS.R001, HS.VIEWS[v][0]), p, os.path.join(OUT, f"{prefix}r001_{v}_sheet.png")))
    restore()
    return out


def _dev_mode(C):
    """--dev: work on head_shape.py's development base (cache/head_r2/dev_base.blend, with the head-shape target),
    the round-1 hero pose snapshot, the part cache in cache/head_r2/ (never cache/parts/head.blend while the
    pose is being re-solved), and head_skin.py's skin, stubble and eyes applied to the body in this session."""
    import head_shape as HS
    C.BASE_BLEND, C.BASE_JSON = HS.DEV_BLEND, HS.DEV_JSON
    C.PARTS_DIR = HS.WORK
    C.apply_hero_pose = lambda rig: (HS.pose_hero(rig), "cache/head_r2/hero_pose_r1.json")[1]


def bl_build(argv):
    import bpy
    import common as C
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--dev", action="store_true", help="head_shape.py's development base and caches (round 2)")
    ap.add_argument("--prefix", default="head_")
    args = ap.parse_args(argv)
    if args.dev:
        _dev_mode(C)
    t0 = time.perf_counter()
    body, rig = C.open_base()
    bd = C.body_data(body)
    marks = C.base_json()["landmarks"]
    coll = C.part_collection("Head")
    hair, hinfo = build_hair(C, bd, coll)
    C.bind(hair, body, rig)
    rest_clear = C.clearance([hair], body, "rest")
    fit = json.load(open(FIT_JSON)) if os.path.exists(FIT_JSON) else {}
    extra = {"part": "head", "hair": hinfo, "stubble": "a shading of the skin (head_skin.py), no shell",
             "clearance_rest": rest_clear,
             "face_targets": len(fit.get("targets", {})), "face_fit": "scripts/parts/head_fit.json",
             "face_shape": "scripts/parts/head-shape.target (head_shape.py)", "base": C.BASE_BLEND}
    C.save_part("head", coll, extra)
    if "Stubble.Mix" not in bpy.data.node_groups.get("Body.Skin.Group", bpy.data.node_groups[0]).nodes:
        # round 2: the skin, the stubble (a shading of the skin) and the eyes are head_skin.py's, applied by base.py
        # once wired; until then here, for this part's renders only (the body is not saved). After save_part: its
        # library write dropped the packed stubble mask's pixels when applied before it.
        import head_skin
        extra["skin_applied_here"] = head_skin.apply(body, marks, bpy.data.objects.get("Body.Eyes"))
    if not args.no_render:
        os.makedirs(OUT, exist_ok=True)
        pre = args.prefix
        render_rest_head(coll, args.samples, pre)
        render_views_r001(coll, args.samples, pre)
        used = C.apply_hero_pose(rig)
        extra["clearance_posed"] = C.clearance([hair], body, "posed")
        C.render_hero([coll], "ref.head_face", os.path.join(OUT, f"{pre}hero_head_face.png"))
        sheet3(REF_CROP, os.path.join(OUT, f"{pre}hero_head_face.png"), os.path.join(OUT, f"{pre}hero_head_face_pair.png"))
        render_hero_cycles(coll, "ref.head_face", os.path.join(OUT, f"{pre}hero_head_face_cycles.png"), args.samples)
        sheet3(REF_CROP, os.path.join(OUT, f"{pre}hero_head_face_cycles.png"), os.path.join(OUT, f"{pre}hero_head_face_cycles_pair.png"))
        render_zooms(coll, args.samples, pre)
        render_hero_cycles(coll, "ref.soldier_full", os.path.join(OUT, f"{pre}hero_soldier_full_cycles.png"), args.samples)
        C.pair_sheet(os.path.join(PROJECT, "ref", "crop_soldier_full.png"), os.path.join(OUT, f"{pre}hero_soldier_full_cycles.png"),
                     os.path.join(OUT, f"{pre}hero_soldier_full_cycles_pair.png"))
        extra["pose"] = used
    extra["seconds"] = round(time.perf_counter() - t0, 1)
    with open(os.path.join(C.PARTS_DIR, "head.json"), "w") as f:
        json.dump(extra, f, indent=1, default=str)
    say(json.dumps({k: extra[k] for k in ("hair", "seconds")}))
    return 0


if __name__ == "__main__":
    if in_blender():
        try:
            rc = main()
        except Exception:
            import traceback
            traceback.print_exc()
            rc = 1
        sys.stdout.flush()
        os._exit(rc)
    sys.exit(main())
