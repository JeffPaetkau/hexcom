"""The head, round 2: the face's shape fitted free-form on MPFB's topology from four views (scripts/parts/head.md §6).

Round 1's 81 MPFB face targets ran out (head.md §5): the landmarks wanted more than the sliders could give and the
face stayed broad and heavy. Round 2 keeps MPFB's head (topology, UVs, groups, weights, eyes, mouth, the round-1
targets underneath) and adds one corrective shape key, `head-shape`, a per-vertex displacement of the head solved
the way take 1's foot was transferred onto its scan (archive/v1 p01 transfer, now scripts/stages/foot/transfer.py):
a smooth displacement field on the mesh, data terms where something is measured, a bending energy everywhere else.

The measurements, all by "the same detector on both" (the reference and a render of the model through the same
camera are read by the same detector, so the detector's own bias cancels):
- hero: MediaPipe's face landmarks on ref/crop_head_face.png and on the posed model through the matched hero camera
  (the round-1 measure, with its exclusions: forehead rows at the hairline, the chin bottom on the under-chin
  shadow; plus the pose solve's hand-read nose tip, menton and right ear). A small nuisance head rotation and image
  shift stop the face from absorbing the pose's error. Authoritative: it is the view the model is judged in.
- gen/R001 (ChatGPT, request R001, the same man inferred from the reference): front, three-quarter from his left,
  true left profile. Each has its own unknown camera (a head rotation, a focal length and a principal point at a
  fixed 1.1 m, a long lens), solved with the shape. MediaPipe on each view and on the rest model rendered through
  that view's current camera; in the profile only the points the model shows to the camera, plus the profile's
  front silhouette (brow to throat) against the model's outline row by row. These give the depth one view cannot
  (nose, brow, lips, chin and jaw in profile; the cheek and jaw widths from the front). Weighted below the hero:
  the views are inferred, their angles approximate.

The field: a displacement U of the head region's skin (head-bone weight > 0.3), symmetric (each vertex paired with
its mirror; the face is fitted symmetric, take 1 spec 06 §2.5 row 14), held at zero on the neck ring where the
region meets the body, the skull top and the cranium under the hair held (stature and the hair cap), and smooth by
a bending energy |L U|^2 (uniform graph Laplacian). Gauss-Newton: cameras and the nuisance with U fixed, then U with
the cameras fixed (a sparse linear solve), a few times per round; each round re-renders and re-detects. The helper
geometry follows: eyes, teeth, tongue and joint cubes move rigidly with the skin around them, the other helpers per
vertex, so the eye bones and MHCLO assets that base.py fits from them follow the new face.

  "$SGT_PYIMG" -I scripts/parts/head_shape.py --fit [--rounds 3]
      the fit, developed on copies (cache/head_r2/): each round rebuilds a development base (base.py's main with
      head-shape.target added, written to cache/head_r2/dev_base.blend, never cache/stages/base.blend), exports and
      renders, detects, solves. Writes scripts/parts/head-shape.target (MPFB target format) and head_shape.json.
  "$SGT_PYIMG" -I scripts/parts/head_shape.py --check TAG [--blend FILE]
      the landmark residuals (hero, R001 views) of a base file, nothing fitted: cache/head_r2/check_TAG.json.
  "$SGT_BLENDER" -b --python scripts/parts/head_shape.py -- --build-dev TARGET OUT.blend
  "$SGT_BLENDER" -b --python scripts/parts/head_shape.py -- --export DIR BLEND CAMS.json

Wiring (base.py, after the face targets and before fit_height): apply(mpfb, body) below loads the target.

The hero pose used is the snapshot cache/head_r2/hero_pose_r1.json (round 1's committed pose, read through
pose.py's apply_hero_pose with path=), so the numbers do not move while the pose is being re-solved elsewhere.

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

SHAPE_NAME = "head-shape"
SHAPE_TARGET = os.path.join(HERE, SHAPE_NAME + ".target")      # MPFB target: the stem is the shape key's name
SHAPE_JSON = os.path.join(HERE, "head_shape.json")
WORK = os.path.join(PROJECT, "cache", "head_r2")
SNAP_BLEND = os.path.join(WORK, "base_snapshot.blend")           # round 1's base.blend, copied 2026-11-15
SNAP_JSON = os.path.join(WORK, "base_snapshot.json")
POSE_SNAP = os.path.join(WORK, "hero_pose_r1.json")              # round 1's committed hero pose
DEV_BLEND = os.path.join(WORK, "dev_base.blend")
DEV_JSON = os.path.join(WORK, "dev_base.json")
REF_CROP = os.path.join(PROJECT, "ref", "crop_head_face.png")
R001 = os.path.join(PROJECT, "gen", "R001")
VIEWS = {   # gen/R001 file, the camera's direction from the head (yaw from the front towards his left, degrees)
    "front": ("front.png", 0.0),
    "threequarter": ("threequarter_left.png", 30.0),     # asked for 45; it reads about 30 (the far eye whole)
    "profile": ("profile_left.png", 90.0),
}
# the head's rotation in each view (degrees about world x: nod, y: tilt, z: turn): priors. A profile's midline alone
# cannot tell its turn from the face's depth (the relief trades with the foreshortening), so the front and the
# profile, asked for and seen as square to the camera, hold their turn; the three-quarter finds its own.
ROT_PRIOR = {"front": (15.0, 5.0, 3.0), "threequarter": (15.0, 5.0, 15.0), "profile": (15.0, 5.0, 3.0)}
VIEW_PX = 1254                       # R001's images are 1254 square
VIEW_DIST = 1100.0                   # mm: a long lens at a head-and-shoulders distance
HEAD_C = np.array([0.0, -40.0, 1735.0])   # rest mm: the views' pivot, between the eyes and the ears

# weights (sigmas)
HERO_SIGMA_PX = 1.5                  # hero full-frame px (about 3 mm at the head)
VIEW_SIGMA_MM = 3.5                  # an R001 landmark, in mm at the head (inferred views, approximate angles)
EDGE_SIGMA_MM = 2.5                  # an R001 silhouette (profile, three-quarter), per row sample
HERO_SIL_SIGMA_PX = 1.0              # the hero's far-cheek silhouette, per row sample (full-frame px)
DEPTH_SIGMA_MM = 3.0                 # the relief from Depth Anything (front and three-quarter), per vertex
DEPTH_CLIP_MM = 5.0                  # a round's relief correction is clipped to this
DEPTH_VIEWS = ("front", "threequarter")
DA_DIR = os.path.join(PROJECT, "assets", "ai", "depth_anything_v2_small")
HAND_SIGMA = {"nose_tip": 1.0, "chin": 1.3, "ear_R": 1.6}     # hero px; round 1's sigmas / sqrt(weight 10)
BEND_SIGMA = 0.2                    # mm per vertex of |L U| (uniform Laplacian): the smoothness
TIKH_SIGMA = 12.0                    # mm: a weak pull of U towards zero (the back of the head)
CRANIUM_SIGMA = 1.5                  # mm: the skull under the hair (above the hairline, behind the face)
PIN_SIGMA = 0.05                     # mm: the neck ring
ROT_SIGMA_DEG, SHIFT_SIGMA_PX = 12.0, 4.0        # the hero nuisance, as round 1
TRICHION_Z = 1783.0                  # rest mm: the hairline (head.py HAIR)

FOREHEAD = {10, 338, 297, 332, 284, 251, 109, 67, 103, 54, 21, 162, 151, 108, 69, 104, 68, 71, 337, 299, 333,
            298, 301, 9, 107, 66, 105, 63, 70, 336, 296, 334, 293, 300}
CHIN_BOTTOM = {152, 148, 377, 176, 400, 149, 378}
JAW_OVAL = [356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132,
            93, 234, 127]
HAND = {"nose_tip": (815.0, 90.0), "chin": (816.0, 131.0), "ear_R": (762.0, 98.0)}
KEY = {"nose_tip": 1, "chin": 152, "eye_R_outer": 33, "eye_R_inner": 133, "eye_L_inner": 362, "eye_L_outer": 263,
       "mouth_R": 61, "mouth_L": 291, "subnasale": 2, "gonion_R": 172, "gonion_L": 397, "cheek_R": 234,
       "cheek_L": 454}
RIGID_HELPERS = ("helper-l-eye", "helper-r-eye", "helper-upper-teeth", "helper-lower-teeth", "helper-tongue")


def say(*a):
    print("[hshape]", *a, flush=True)


def in_blender():
    try:
        import bpy  # noqa: F401
        return True
    except ImportError:
        return False


# =========================================================================== wiring: base.py

def apply(mpfb, body, path=SHAPE_TARGET):
    """Load head-shape.target onto Body.Mesh at weight 1 (base.py: after the face targets, before fit_height, so
    the rig's joint cubes, the eye bones and the MHCLO assets follow). Returns the shape key, or None without the
    file or with SGT_BASE_NO_FACE."""
    if os.environ.get("SGT_BASE_NO_FACE") or not os.path.exists(path):
        return None
    return mpfb.targets.load_target(body, path, weight=1.0, name=SHAPE_NAME)


def write_target(D_mm, path=SHAPE_TARGET, note=""):
    """D_mm (n_verts, 3) world displacement in mm -> MPFB target lines `index x z -y` in decimetres (MPFB's
    scale_factor 0.1: TargetService._target_string_to_shape_key_info)."""
    lines = ["# head-shape: scripts/parts/head_shape.py (head round 2). " + note,
             "# MPFB target: index dx dz -dy in decimetres; the displacement of the round-1 face (head_fit.json)"]
    for i in np.where(np.linalg.norm(D_mm, axis=1) > 1e-3)[0]:
        dx, dy, dz = D_mm[i] / 100.0
        lines.append(f"{i} {dx:.6f} {dz:.6f} {-dy:.6f}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def read_target(n, path=SHAPE_TARGET):
    D = np.zeros((n, 3))
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.startswith("#") or not line.strip():
                continue
            i, a, b, c = line.split()
            D[int(i)] = (float(a) * 100.0, -float(c) * 100.0, float(b) * 100.0)
    return D


# =========================================================================== Blender side

def _argv():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def bl_build_dev(target, out_blend):
    """base.py's main, writing out_blend (and its json beside it), with `target` loaded after the face targets.
    base.py is not edited: its output paths and its Mpfb are patched in this process only."""
    import base as B
    B.OUT_DIR = os.path.dirname(out_blend)
    B.OUT_BLEND = out_blend
    B.OUT_JSON = os.path.splitext(out_blend)[0] + ".json"
    orig_ft = B.face_targets

    def ft():
        d = orig_ft()
        if target and os.path.exists(target):
            d[SHAPE_NAME] = 1.0
        return d
    B.face_targets = ft
    # round 2 (head_skin.LASHES_R2): the short lashes; base.py's ASSETS line to change when wired
    import head_skin
    B.ASSETS = tuple((s, head_skin.LASHES_R2, m, n) if s == "eyelashes" else (s, f, m, n) for s, f, m, n in B.ASSETS)
    Base = B.Mpfb

    class M(Base):
        def __init__(self):
            super().__init__()
            ts = self.targets

            class Proxy:
                def __getattr__(self, k):
                    return getattr(ts, k)

                def target_full_path(self, name):
                    return target if name == SHAPE_NAME else ts.target_full_path(name)
            self.targets = Proxy()
    B.Mpfb = M
    return B.main()


def _patch_common(blend):
    import common as C
    C.BASE_BLEND = blend
    j = os.path.splitext(blend)[0] + ".json"
    C.BASE_JSON = j if os.path.exists(j) else SNAP_JSON
    return C


def pose_hero(rig):
    import pose as P
    return P.apply_hero_pose(rig, path=POSE_SNAP)


def view_camera(cam_par):
    """(R rows: right, up, toward camera; centre; f; cx; cy) of a view's camera parameters."""
    yaw = math.radians(cam_par["yaw"])
    t = np.array([math.sin(yaw), -math.cos(yaw), 0.0])
    up = np.array([0.0, 0.0, 1.0])
    right = np.cross(up, t)
    Rb = np.stack([right, up, t])
    Rh = rotvec(np.radians(cam_par["rot"]))           # the head's rotation in the view (head frame, world axes)
    return Rb @ Rh, cam_par["f"], cam_par["cx"], cam_par["cy"]


def rotvec(w):
    th = float(np.linalg.norm(w))
    if th < 1e-12:
        return np.eye(3)
    k = np.asarray(w, float) / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K


def bl_view_render(sc, cam_par, path, size=VIEW_PX):
    """A rest-body render through a view's camera (Workbench material colours, transparent)."""
    import bpy
    import common as C
    from mathutils import Matrix
    R, f, cx, cy = view_camera(cam_par)
    ob = bpy.data.objects.get("HShape.Cam")
    if ob is None:
        ob = bpy.data.objects.new("HShape.Cam", bpy.data.cameras.new("HShape.Cam"))
        sc.collection.objects.link(ob)
    pos = (HEAD_C + R.T @ np.array([0.0, 0.0, VIEW_DIST])) / 1000.0
    M = np.eye(4)
    M[:3, :3] = R.T
    M[:3, 3] = pos
    ob.matrix_world = Matrix(M.tolist())
    c = ob.data
    c.type, c.sensor_fit, c.sensor_width = "PERSP", "HORIZONTAL", 36.0
    c.lens = f * 36.0 / size
    c.shift_x = (size / 2.0 - cx) / size
    c.shift_y = (cy - size / 2.0) / size
    c.clip_start, c.clip_end = 0.05, 20.0
    sc.camera = ob
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.render.use_border = False
    C._workbench(sc, "MATERIAL", transparent=True)
    return C._render(path)


def bl_export(out_dir, blend, cams_json):
    """Open a base file; renders: the rest body through each R001 view's current camera and the posed body
    through the hero camera (ref.head_face), Workbench, bald (the round-1 measure); arrays: the head region's
    rest and posed vertices, the hero pose's per-vertex skinning, the triangles, mirror pairs, the neck ring,
    the hand points, and every vertex's rest position and helper group (for extending the field)."""
    import bpy
    C = _patch_common(blend)
    body, rig = C.open_base()
    import head as H
    bd = C.body_data(body)
    region = H.head_region(bd)
    idx = np.where(region)[0]
    pos = {v: k for k, v in enumerate(idx)}
    V_rest = bd["V"][idx]
    sc = bpy.context.scene
    hide = [o for o in bpy.data.objects if o.name.startswith(("Part.", "Pose.", "Head."))]
    for o in hide:
        o.hide_render = True
    cams = json.load(open(cams_json)) if cams_json and os.path.exists(cams_json) else {}
    for v, par in cams.get("views", {}).items():
        bl_view_render(sc, par, os.path.join(out_dir, f"model_{v}.png"))
    # the hero pose and linear blend skinning per vertex (head.py bl_export, checked there to 0.0003 mm)
    pose_hero(rig)
    bones = {b.name for b in rig.data.bones if b.use_deform}
    Mb = {pb.name: np.array(pb.matrix) @ np.linalg.inv(np.array(pb.bone.matrix_local)) for pb in rig.pose.bones
          if pb.name in bones}
    A = np.zeros((len(idx), 3, 3))
    T = np.zeros((len(idx), 3))
    for k, vi in enumerate(idx):
        ws = [(bd["groups"][g][vi], g) for g in bones if g in bd["groups"] and bd["groups"][g][vi] > 0]
        s = sum(w for w, _ in ws)
        for w, g in ws:
            A[k] += w / s * Mb[g][:3, :3]
            T[k] += w / s * Mb[g][:3, 3] * 1000.0
    P0 = np.einsum("kij,kj->ki", A, V_rest) + T
    rset = set(idx.tolist())
    tris = []
    for f in bd["F"]:
        if all(v in rset for v in f):
            for j in range(1, len(f) - 1):
                tris.append((pos[f[0]], pos[f[j]], pos[f[j + 1]]))
    # the neck ring: region vertices with a skin neighbour outside the region
    ring = np.zeros(len(idx), bool)
    for f in bd["F"]:
        inr = [v in rset for v in f]
        if any(inr) and not all(inr):
            for v, a in zip(f, inr):
                if a and bd["in_body"][v]:
                    ring[pos[v]] = True
    E = set()
    for f in bd["F"]:
        if all(v in rset for v in f):
            for i in range(len(f)):
                a, b = pos[f[i]], pos[f[(i + 1) % len(f)]]
                E.add((min(a, b), max(a, b)))
    pivot = np.array(rig.matrix_world @ rig.pose.bones["head"].head) * 1000.0
    marks = C.base_json()["landmarks"]
    hand_ids = np.full((len(HAND), 64), -1, np.int64)
    for r, k in enumerate(HAND):
        if k == "ear_R":
            ids = [pos[v] for v in np.where((bd["groups"]["ears"] > 0.5) & region & (bd["V"][:, 0] < 0))[0]]
        else:
            ids = [int(np.argmin(np.linalg.norm(V_rest - np.array(marks[k]["rest_mm"]), axis=1)))]
        hand_ids[r, :len(ids[:64])] = ids[:64]
    mark_ids = np.array([int(np.argmin(np.linalg.norm(V_rest - np.array(marks[k]["rest_mm"]), axis=1)))
                         for k in ("chin", "nose_tip")])
    helper = np.full(len(bd["V"]), -1, np.int64)
    hnames = sorted(n for n in bd["names"] if n.startswith(("helper-", "joint-")))
    for j, n in enumerate(hnames):
        helper[bd["groups"][n] > 0.5] = j
    ears = bd["groups"]["ears"][idx] > 0.5
    np.savez_compressed(os.path.join(out_dir, "export.npz"), idx=idx, V_rest=V_rest, P0=P0, A=A,
                        tris=np.array(tris, np.int32), edges=np.array(sorted(E), np.int32), ring=ring, ears=ears,
                        pivot=pivot, hand_ids=hand_ids, mark_ids=mark_ids, V_all=bd["V"], in_body=bd["in_body"], helper=helper,
                        helper_names=np.array(hnames), N_rest=bd["N"][idx])
    C.render_hero([], "ref.head_face", os.path.join(out_dir, "model_hero.png"))
    say("export", json.dumps({"verts": int(len(idx)), "tris": len(tris), "ring": int(ring.sum()),
                              "views": list(cams.get("views", {}))}))


# =========================================================================== outside Blender: running Blender

def blender(args, blend=None, log=None):
    exe = os.environ.get("SGT_BLENDER")
    if not exe:
        raise SystemExit("SGT_BLENDER is not set: source cache/env.sh")
    cmd = [exe, "-b"] + ([blend] if blend else []) + ["--python"] + args
    t = time.perf_counter()
    r = subprocess.run(cmd, cwd=PROJECT, capture_output=True, text=True, errors="replace")
    if log:
        with open(log, "w", encoding="utf-8") as f:
            f.write(r.stdout + "\n" + r.stderr)
    for l in [l for l in r.stdout.splitlines() if l.startswith(("[hshape]", "Error", "Traceback"))][-8:]:
        print("   ", l[:300], flush=True)
    if r.returncode != 0 or "Traceback" in r.stdout + r.stderr:
        print(r.stdout[-4000:], r.stderr[-3000:])
        raise SystemExit(f"Blender failed: {' '.join(args)}")
    return time.perf_counter() - t


def build_dev(target, out_blend, tag):
    return blender([os.path.abspath(__file__), "--", "--build-dev", target or "", out_blend],
                   log=os.path.join(WORK, f"build_{tag}.log"))


def export(out_dir, blend, cams):
    os.makedirs(out_dir, exist_ok=True)
    cj = os.path.join(out_dir, "cams.json")
    with open(cj, "w") as f:
        json.dump(cams, f, indent=1)
    blender([os.path.abspath(__file__), "--", "--export", out_dir, blend, cj], log=os.path.join(out_dir, "export.log"))
    return dict(np.load(os.path.join(out_dir, "export.npz")))


# =========================================================================== detection

_DET = None


def mp_points(img):
    """MediaPipe FaceLandmarker (take 1's model) on an RGB array: 478 points in its pixels, or None."""
    global _DET
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
    if _DET is None:
        buf = open(os.path.join(PROJECT, "assets", "ai", "mediapipe", "face_landmarker.task"), "rb").read()
        _DET = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_buffer=buf), num_faces=1))
    arr = np.ascontiguousarray(img[..., :3].astype(np.uint8))
    res = _DET.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=arr))
    if not res.face_landmarks:
        return None
    h, w = arr.shape[:2]
    return np.array([(p.x * w, p.y * h) for p in res.face_landmarks[0]])


def load_rgb(path, grey=0.22):
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, tuple(int(grey * 255) for _ in range(3)) + (255,))
    bg.alpha_composite(im)
    return np.array(bg.convert("RGB"))


def hero_points(png):
    """MediaPipe on an 850 x 850 ref.head_face image, in full-frame px."""
    from PIL import Image
    p = mp_points(load_rgb(png) if png.endswith("model_hero.png") else np.array(Image.open(png).convert("RGB")))
    return None if p is None else p / 5.0 + np.array([715.0, 30.0])


def profile_edge(png):
    """The profile's front silhouette: per image row, the first column (from the left, where the face points)
    that is not background. The background is read from the image's top corners."""
    from PIL import Image
    a = np.asarray(Image.open(png).convert("RGB"), float)
    bg = np.concatenate([a[:40, :40].reshape(-1, 3), a[:40, -40:].reshape(-1, 3)]).mean(0)
    fg = np.linalg.norm(a - bg, axis=2) > 28.0
    from scipy import ndimage
    fg = ndimage.binary_opening(fg, iterations=2)
    edge = np.full(a.shape[0], np.nan)
    for y in range(a.shape[0]):
        xs = np.where(fg[y])[0]
        if len(xs):
            edge[y] = xs[0]
    return edge


def model_edge(Vp_xy):
    """The model's front outline per image row (a 2 px band): the vertex with the least x."""
    rows = {}
    for k, (x, y) in enumerate(Vp_xy):
        r = int(round(y / 2.0))
        if r not in rows or x < Vp_xy[rows[r], 0]:
            rows[r] = k
    return np.array(sorted(rows.values()))


# =========================================================================== geometry helpers

def raycast(o, d, P, tris):
    """Rays (o, d: (n, 3) or o (3,)) onto triangles: per ray (tri, bary (3,), t) or None."""
    a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    e1, e2 = b - a, c - a
    o = np.broadcast_to(o, d.shape)
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
        out.append((int(k), np.array([1 - u[k] - v[k], u[k], v[k]]), float(t[k])))
    return out


def tri_normals(P, tris):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def proj_view(X, par):
    """Rest points (n, 3) mm through a view's camera -> pixels (n, 2)."""
    R, f, cx, cy = view_camera(par)
    Q = (X - HEAD_C) @ R.T
    d = VIEW_DIST - Q[:, 2]
    return np.stack([cx + f * Q[:, 0] / d, cy - f * Q[:, 1] / d], 1)


def ray_view(xy, par):
    R, f, cx, cy = view_camera(par)
    o = HEAD_C + R.T @ np.array([0.0, 0.0, VIEW_DIST])
    dc = np.stack([(xy[:, 0] - cx) / f, -(xy[:, 1] - cy) / f, -np.ones(len(xy))], 1)
    d = dc @ R
    return o, d / np.linalg.norm(d, axis=1, keepdims=True)


def jac(fn, X, h=0.25):
    """Numerical Jacobian of a point projection fn: (n, 3) -> (n, 2), per point (n, 2, 3)."""
    J = np.zeros((len(X), 2, 3))
    for k in range(3):
        e = np.zeros(3)
        e[k] = h
        J[:, :, k] = (fn(X + e) - fn(X - e)) / (2 * h)
    return J


def hero_cam():
    from eval import camproj
    return camproj.HERO


def hero_proj(X):
    return hero_cam().project(X / 1000.0)


def mirror_pairs(V, tol=1.5):
    from scipy.spatial import cKDTree
    t = cKDTree(V)
    d, j = t.query(V * np.array([-1.0, 1.0, 1.0]))
    if np.percentile(d, 99) > tol:
        say(f"warning: mirror pairing 99th percentile {np.percentile(d, 99):.2f} mm")
    return j, d


# =========================================================================== the measurement

def correspondences(E, U, cams, rnd_dir, ref):
    """Detect on the round's renders, cast each model landmark onto the mesh. Returns per view a dict of
    landmark ids, triangle vertex ids, barycentrics and reference pixels (and the profile edge)."""
    P_rest = E["V_rest"]
    P_pose = E["P0"]
    tris = E["tris"]
    out = {}
    # hero
    mod = hero_points(os.path.join(rnd_dir, "model_hero.png"))
    if mod is None:
        raise SystemExit("MediaPipe found no face in the hero render")
    use = [i for i in range(468) if i not in FOREHEAD and i not in CHIN_BOTTOM]
    cam = hero_cam()
    o, d = cam.ray(mod[use])
    hits = raycast(o[0] * 1000.0, d, P_pose, tris)
    dep = np.array([h[2] for h in hits if h is not None])
    med = float(np.median(dep))
    L = [(i, tris[h[0]], h[1]) for i, h in zip(use, hits) if h is not None and h[2] <= med + 40.0]
    out["hero"] = {"ids": np.array([l[0] for l in L]), "vid": np.array([l[1] for l in L]),
                   "bar": np.array([l[2] for l in L]), "ref": ref["hero"][[l[0] for l in L]], "mod": mod}
    # the R001 views (rest mesh)
    tn = tri_normals(P_rest, tris)
    cen = P_rest[tris].mean(1)
    if float(np.mean(np.einsum("ij,ij->i", cen - P_rest.mean(0), tn))) < 0:      # wound inwards
        tn = -tn
    for v, par in cams["views"].items():
        if v == "profile":          # MediaPipe squashes a true profile (it reads it as ~50 degrees): silhouette only
            continue
        img = load_rgb(os.path.join(rnd_dir, f"model_{v}.png"))
        mod = mp_points(img)
        if mod is None:
            say(f"{v}: MediaPipe found no face in the model render; view skipped this round")
            continue
        use = [i for i in range(468) if i not in FOREHEAD]
        o, d = ray_view(mod[use], par)
        hits = raycast(o, d, P_rest, tris)
        L = []
        R, *_ = view_camera(par)
        tcam = R[2]                                  # towards the camera
        for i, h in zip(use, hits):
            if h is None:
                continue
            if float(tn[h[0]] @ tcam) < 0.05:      # MediaPipe guesses what the view hides
                continue
            L.append((i, tris[h[0]], h[1]))
        out[v] = {"ids": np.array([l[0] for l in L]), "vid": np.array([l[1] for l in L]),
                  "bar": np.array([l[2] for l in L]), "ref": ref[v][[l[0] for l in L]], "mod": mod}
    if "profile" in cams["views"] and ref.get("profile") is not None:
        out["profile"] = profile_corr(E, ref, out["hero"])
    for v in DEPTH_VIEWS:
        if v in cams["views"] and v in out and ref.get(v + "_da") is not None:
            img = load_rgb(os.path.join(rnd_dir, f"model_{v}.png"))
            d_mod = depth_map(img)
            vid, delta, dvec, rec, pix = depth_term(E, cams["views"][v], ref[v + "_da"], d_mod, ref[v], out[v]["mod"])
            out[v + "_depth"] = {"vid": vid, "delta": delta, "dir": dvec, "rec": rec}
            say(f"{v} relief: {rec}")
            depth_debug(os.path.join(rnd_dir, f"depth_{v}.png"), os.path.join(R001, VIEWS[v][0]), pix, delta)
    out["ref"] = ref
    return out


def depth_debug(out_png, ref_png, pix, delta):
    """The wanted depth change on the reference view: red where
    the face should go back (deeper), blue where it should come forward."""
    from PIL import Image, ImageDraw
    im = Image.open(ref_png).convert("RGB")
    d = ImageDraw.Draw(im)
    for (x, y), v in zip(pix, delta):
        k = float(np.clip(abs(v) / DEPTH_CLIP_MM, 0, 1))
        col = (255, int(255 * (1 - k)), int(255 * (1 - k))) if v > 0 else (int(255 * (1 - k)), int(255 * (1 - k)), 255)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=col)
    im.resize((627, 627)).save(out_png)


def profile_corr(E, ref, hero):
    """What the profile terms need: the reference outline, its row window (MediaPipe's brow and chin rows, only as a
    window), the model's nasion (MediaPipe 168 in the hero view) and menton vertex."""
    k = list(hero["ids"]).index(168)
    return {"edge": ref["profile_edge"], "win_ref": (float(ref["profile"][168][1]), float(ref["profile"][152][1])),
            "nasion_vb": (hero["vid"][k], hero["bar"][k]), "menton_vid": int(E["mark_ids"][0])}


def edge_features(ys, xs, y_a, y_b):
    """Indices into (ys, xs) of a profile outline's glabella, nasion, pronasale and pogonion, searched between the
    rows y_a (above the brows) and y_b (the chin): the nose tip is the most forward point (least x: the face
    points to image left), the glabella the most forward point above it in the upper part, the nasion the
    deepest point between them, the pogonion the chin's most forward point in the lowest part."""
    m = np.where((ys >= y_a) & (ys <= y_b) & ~np.isnan(xs))[0]
    k = m[np.argmin(xs[m])]
    up = m[(ys[m] < y_a + 0.6 * (ys[k] - y_a))]
    gl = up[np.argmin(xs[up])]
    mid = m[(ys[m] > ys[gl]) & (ys[m] < ys[k])]
    nas = mid[np.argmax(xs[mid])]
    lo = m[ys[m] > ys[k] + 0.6 * (y_b - ys[k])]
    pog = lo[np.argmin(xs[lo])]
    return {"glabella": gl, "nasion": nas, "pronasale": k, "pogonion": pog}


def ref_profile(cp):
    """The reference profile's features and the outline's row window (brow to throat)."""
    edge = cp["edge"]
    y168, y152 = cp["win_ref"]
    y_a, y_b = y168 - 0.45 * (y152 - y168), y152 + 0.04 * (y152 - y168)
    ys = np.arange(len(edge), dtype=float)
    f = edge_features(ys, edge, y_a, y_b)
    return {k: np.array([edge[i], ys[i]]) for k, i in f.items()}, (y_a, y152 + 0.22 * (y152 - y168))


def outline(xy, edges, rows, side="min"):
    """The mesh's outline in an image: for each row, the crossing of a projected edge with the least x (side
    "min") or the greatest ("max"). Returns per row (a, b, t, y): the point (1 - t) P_a + t P_b, rows without a
    crossing dropped."""
    ya, yb = xy[edges[:, 0], 1], xy[edges[:, 1], 1]
    lo, hi = np.minimum(ya, yb), np.maximum(ya, yb)
    out = []
    for y0 in rows:
        k = np.where((lo <= y0) & (hi > y0))[0]
        if not len(k):
            continue
        t = (y0 - ya[k]) / np.where(yb[k] != ya[k], yb[k] - ya[k], 1.0)
        x = xy[edges[k, 0], 0] * (1 - t) + xy[edges[k, 1], 0] * t
        j = int(np.argmin(x)) if side == "min" else int(np.argmax(x))
        out.append((int(edges[k[j], 0]), int(edges[k[j], 1]), float(t[j]), float(y0)))
    return out


def profile_terms(E, U, par, cp):
    """The model's profile outline through the view's camera, rows every 3 px: the outline points in the
    reference's row window with their residual x - edge(y) and its gradient (on the point), and the four
    feature points with the reference's features. A point is (a, b, t) on an edge."""
    VU = E["V_rest"] + U
    xy = proj_view(VU, par)
    if "edges_face" not in E:
        e = E["edges"]
        E["edges_face"] = e[~(E["ears"][e[:, 0]] | E["ears"][e[:, 1]])]
    vid, bar = cp["nasion_vb"]
    yn = proj_view((bar @ VU[vid])[None], par)[0, 1]
    ym = xy[cp["menton_vid"], 1]
    feat_ref, (r_a, r_b) = ref_profile(cp)
    y_lo = min(r_a, yn - 0.5 * (ym - yn))
    y_hi = max(r_b, ym + 0.3 * (ym - yn))
    ol = outline(xy, E["edges_face"], np.arange(np.floor(y_lo), np.ceil(y_hi), 3.0))
    A_ = np.array([o[0] for o in ol])
    B_ = np.array([o[1] for o in ol])
    T_ = np.array([o[2] for o in ol])
    P = VU[A_] * (1 - T_[:, None]) + VU[B_] * T_[:, None]
    pxy = proj_view(P, par)
    fm = edge_features(pxy[:, 1], pxy[:, 0], yn - 0.45 * (ym - yn), ym + 0.04 * (ym - yn))
    feat = {k: ((int(A_[i]), int(B_[i]), float(T_[i])), feat_ref[k]) for k, i in fm.items()}
    edge = cp["edge"]
    ys = np.arange(len(edge), dtype=float)
    ok = ~np.isnan(edge)
    m = (pxy[:, 1] > r_a) & (pxy[:, 1] < r_b)
    sel = (A_[m], B_[m], T_[m])
    r = pxy[m, 0] - np.interp(pxy[m, 1], ys[ok], edge[ok])
    slope = np.gradient(np.interp(ys, ys[ok], edge[ok]))
    J = jac(lambda Y: proj_view(Y, par), P[m])
    g = J[:, 0, :] - np.interp(pxy[m, 1], ys, slope)[:, None] * J[:, 1, :]
    return sel, r, g, feat


def silhouette(P, proj, edges, rows, ref_ys, ref_xs, side):
    """An outline term: the mesh points P (n, 3) through proj, the outline on `side` at `rows`, against the
    reference outline x(y) (ref_ys increasing). Returns ((a, b, t) arrays, residual x - ref(y), gradient (k, 3))."""
    xy = proj(P)
    ol = outline(xy, edges, rows, side)
    A_ = np.array([o[0] for o in ol])
    B_ = np.array([o[1] for o in ol])
    T_ = np.array([o[2] for o in ol])
    Q = P[A_] * (1 - T_[:, None]) + P[B_] * T_[:, None]
    q = proj(Q)
    r = q[:, 0] - np.interp(q[:, 1], ref_ys, ref_xs)
    slope = np.gradient(ref_xs, ref_ys)
    J = jac(proj, Q)
    g = J[:, 0, :] - np.interp(q[:, 1], ref_ys, slope)[:, None] * J[:, 1, :]
    return (A_, B_, T_), r, g


def face_edges(E):
    if "edges_face" not in E:
        e = E["edges"]
        E["edges_face"] = e[~(E["ears"][e[:, 0]] | E["ears"][e[:, 1]])]
    return E["edges_face"]


def sil_threequarter(E, U, par, ref):
    """The three-quarter's far cheek (image left), brow to chin, on the rest mesh."""
    ys, xs, (y0, y1) = ref["threequarter_edge"]
    return silhouette(E["V_rest"] + U, lambda Y: proj_view(Y, par), face_edges(E), np.arange(y0, y1, 3.0), ys, xs, "min")


def sil_hero(E, U, nuis, ref):
    """The hero view's far cheek (viewer's right, his left) against the dark background, eye to jaw, posed."""
    ys, xs, (y0, y1) = ref["hero_edge"]
    Rn = rotvec(np.radians(nuis[:3]))
    piv = E["pivot"]
    PU = E["P0"] + np.einsum("kij,kj->ki", E["A"], U)
    return silhouette(PU, lambda X: hero_proj(piv + (X - piv) @ Rn.T) + nuis[3:5], face_edges(E),
                      np.arange(y0, y1, 0.6), ys, xs, "max")


def ref_edges(ref):
    """The reference outlines: the three-quarter's far cheek (first foreground pixel from the left against the
    grey background; rows from MediaPipe's brow to its chin) and the hero crop's far cheek (the last pixel from
    the right brighter than 70 in luminance, crop columns 425-700, rows 190-470 = full frame 68-124)."""
    from PIL import Image
    from scipy import ndimage
    out = {}
    p = os.path.join(R001, VIEWS["threequarter"][0])
    if os.path.exists(p) and ref.get("threequarter") is not None:
        a = np.asarray(Image.open(p).convert("RGB"), float)
        bg = np.concatenate([a[:40, :40].reshape(-1, 3), a[:40, -40:].reshape(-1, 3)]).mean(0)
        fg = ndimage.binary_opening(np.linalg.norm(a - bg, axis=2) > 28.0, iterations=2)
        y168, y152 = ref["threequarter"][168][1], ref["threequarter"][152][1]
        ys = np.arange(int(y168 - 0.2 * (y152 - y168)), int(y152) + 1)
        xs = np.array([np.where(fg[y])[0][0] if fg[y].any() else np.nan for y in ys], float)
        ok = ~np.isnan(xs)
        out["threequarter_edge"] = (ys[ok].astype(float), xs[ok], (float(ys[0]), float(ys[-1])))
    b = np.asarray(Image.open(REF_CROP).convert("RGB"), float)
    lum = b @ np.array([0.2126, 0.7152, 0.0722])
    fg = ndimage.binary_opening(lum > 70.0, iterations=2)
    ys, xs = [], []
    for y in range(190, 471):
        c = np.where(fg[y, 425:700])[0]
        if len(c):
            ys.append(30.0 + y / 5.0)
            xs.append(715.0 + (425 + c[-1] + 0.5) / 5.0)
    out["hero_edge"] = (np.array(ys), ndimage.median_filter(np.array(xs), 5), (68.0, 124.0))
    return out


def pt(VU, abt):
    a, b, t = abt
    return VU[a] * (1 - t) + VU[b] * t


def fit_profile_cam(E, U, par, cp, iters=4):
    """The profile camera (head rotation, focal, principal point) on the outline and its four features."""
    from scipy.optimize import least_squares
    VU = E["V_rest"] + U
    edge = cp["edge"]
    ys = np.arange(len(edge), dtype=float)
    ok = ~np.isnan(edge)
    for _ in range(iters):
        sel, _, _, feat = profile_terms(E, U, par, cp)
        Ps = VU[sel[0]] * (1 - sel[2][:, None]) + VU[sel[1]] * sel[2][:, None]
        Pf = np.array([pt(VU, feat[k][0]) for k in feat])
        fr = np.array([feat[k][1] for k in feat])

        def res(z, Ps=Ps, Pf=Pf, fr=fr, par=par):
            p = dict(par, rot=list(z[:3]), f=z[3], cx=z[4], cy=z[5])
            xy = proj_view(Ps, p)
            re = (xy[:, 0] - np.interp(xy[:, 1], ys[ok], edge[ok])) / 4.0
            rf = (proj_view(Pf, p) - fr).ravel() / 3.0
            return np.concatenate([re, rf, z[:3] / np.array(ROT_PRIOR["profile"])])
        z0 = np.array(list(par["rot"]) + [par["f"], par["cx"], par["cy"]], float)
        s_ = least_squares(res, z0)
        par = dict(par, rot=[float(a) for a in s_.x[:3]], f=float(s_.x[3]), cx=float(s_.x[4]), cy=float(s_.x[5]))
    return par


_DA = None


def depth_map(img):
    """Depth Anything V2 Small (assets/ai/depth_anything_v2_small, Apache-2.0, CPU) on an RGB array: relative
    inverse depth at the image's size (larger is nearer)."""
    global _DA
    import torch
    from PIL import Image
    from transformers import AutoImageProcessor, AutoModelForDepthEstimation
    if _DA is None:
        _DA = (AutoImageProcessor.from_pretrained(DA_DIR), AutoModelForDepthEstimation.from_pretrained(DA_DIR).eval())
    proc, model = _DA
    inp = proc(images=Image.fromarray(np.ascontiguousarray(img[..., :3].astype(np.uint8))), return_tensors="pt")
    with torch.no_grad():
        out = model(**inp).predicted_depth
    pred = torch.nn.functional.interpolate(out[:, None], size=img.shape[:2], mode="bicubic", align_corners=False)
    return pred[0, 0].numpy()


def sample(img, xy):
    from scipy.ndimage import map_coordinates
    return map_coordinates(img, [xy[:, 1], xy[:, 0]], order=1, mode="nearest")


def depth_term(E, par, d_ref, d_mod, ref_pts, mod_pts):
    """The relief the same detector sees in the R001 view and in the model's render through that view's camera:
    for the face's visible vertices (inside both images' MediaPipe face hulls without the forehead rows and away
    from the eyes), each map is turned into millimetres by the affine fit to the model's true depth there, and
    the difference, less its best plane (what a small camera rotation would make), is the depth the vertex
    should gain. Returns (vertex ids, the depth change wanted mm, the depth direction (3,)), and a record."""
    from scipy.spatial import Delaunay
    V = E["V_rest"]
    R, f, cx, cy = view_camera(par)
    tcam = R[2]
    xy = proj_view(V, par)
    Q = (V - HEAD_C) @ R.T
    z = VIEW_DIST - Q[:, 2]
    N = E["N_rest"]
    cand = np.where((N @ tcam > 0.25) & ~E["ears"])[0]
    keep = [i for i in range(468) if i not in FOREHEAD]
    inside = (Delaunay(ref_pts[keep]).find_simplex(xy[cand]) >= 0) & (Delaunay(mod_pts[keep]).find_simplex(xy[cand]) >= 0)
    cand = cand[inside]
    eyes = np.concatenate([ref_pts[[33, 133, 159, 145]], ref_pts[[263, 362, 386, 374]]])
    eye_c = np.array([eyes[:4].mean(0), eyes[4:].mean(0)])
    eye_r = 0.75 * np.linalg.norm(ref_pts[33] - ref_pts[133])
    far = np.min(np.linalg.norm(xy[cand][:, None, :] - eye_c[None], axis=2), axis=1) > eye_r
    cand = cand[far]
    # visibility: the first hit of the ray towards the vertex is the vertex's own neighbourhood
    o, d = ray_view(xy[cand], par)
    hits = raycast(o, d, V, E["tris"])
    dist = np.linalg.norm(V[cand] - o, axis=1)
    vis = np.array([h is not None and h[2] > dist[k] - 1.5 for k, h in enumerate(hits)])
    cand = cand[vis]
    A = np.stack([sample(d_mod, xy[cand]), np.ones(len(cand))], 1)
    am = np.linalg.lstsq(A, z[cand], rcond=None)[0]
    B = np.stack([sample(d_ref, xy[cand]), np.ones(len(cand))], 1)
    ar = np.linalg.lstsq(B, z[cand], rcond=None)[0]
    zm, zr = A @ am, B @ ar
    delta = zr - zm
    P3 = np.stack([xy[cand, 0], xy[cand, 1], np.ones(len(cand))], 1)
    delta = delta - P3 @ np.linalg.lstsq(P3, delta, rcond=None)[0]
    rec = {"vertices": int(len(cand)), "model_fit_rms_mm": round(float(np.sqrt(np.mean((zm - z[cand]) ** 2))), 2),
           "ref_fit_rms_mm": round(float(np.sqrt(np.mean((zr - z[cand]) ** 2))), 2),
           "delta_rms_mm": round(float(np.sqrt(np.mean(delta ** 2))), 2)}
    return cand, np.clip(delta, -DEPTH_CLIP_MM, DEPTH_CLIP_MM), -tcam, rec, xy[cand]


def residual_stats(xy, ref, ids=None):
    e = np.linalg.norm(xy - ref, axis=1)
    out = {"n": int(len(e)), "rms_px": round(float(np.sqrt(np.mean(e ** 2))), 3), "median_px": round(float(np.median(e)), 3)}
    if ids is not None:
        jaw = [k for k, i in enumerate(ids) if i in set(JAW_OVAL)]
        if jaw:
            out["jaw_oval_rms_px"] = round(float(np.sqrt(np.mean(e[jaw] ** 2))), 3)
    return out


# =========================================================================== the solve

def build_maps(E):
    """Symmetric parametrisation S (3n x m) of U, the Laplacian, and the region masks."""
    import scipy.sparse as sp
    V = E["V_rest"]
    n = len(V)
    j, dist = mirror_pairs(V)
    mid = (np.abs(V[:, 0]) < 0.3) | (j == np.arange(n))
    rep = np.where((V[:, 0] <= 0) | mid)[0]               # his right side and the midline carry the unknowns
    col = {}
    rows, cols, vals = [], [], []
    m = 0
    for v in rep:
        comps = (1, 2) if mid[v] else (0, 1, 2)
        for c in comps:
            col[(v, c)] = m
            m += 1
    M = np.array([-1.0, 1.0, 1.0])
    for v in range(n):
        if (v, 0) in col or (v, 1) in col:
            src, sgn = v, np.ones(3)
        else:
            src, sgn = j[v], M
        for c in range(3):
            if (src, c) in col:
                rows.append(3 * v + c)
                cols.append(col[(src, c)])
                vals.append(sgn[c])
    S = sp.csr_matrix((vals, (rows, cols)), shape=(3 * n, m))
    e = E["edges"]
    W = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    deg = np.asarray(W.sum(1)).ravel()
    Lap = sp.identity(n) - sp.diags(1.0 / np.maximum(deg, 1)) @ W
    return S, sp.kron(Lap, sp.identity(3)).tocsr(), dist


def solve_U(E, corr, cams, nuis, U0, maps):
    """One linear solve for the total displacement U (n, 3) with the cameras and the hero nuisance fixed.
    Every data term is linearised about U0."""
    import scipy.sparse as sp
    import scipy.sparse.linalg as spl
    S, L3, _ = maps
    V, P0, A = E["V_rest"], E["P0"], E["A"]
    n = len(V)
    blocks, rhs = [], []

    def add(Jrows, r, sigma):
        """Jrows: sparse (k x 3n) on U, r: (k,) the current residual (model - target)."""
        blocks.append(Jrows / sigma)
        rhs.append(-r / sigma)
    Rn = rotvec(np.radians(nuis[:3]))
    piv = E["pivot"]

    def hero_xy(X):
        return hero_proj(piv + (X - piv) @ Rn.T) + nuis[3:5]
    # hero landmarks (posed): X = sum b (P0 + A U)
    c = corr["hero"]
    PU = P0 + np.einsum("kij,kj->ki", A, U0)
    X = np.einsum("lk,lki->li", c["bar"], PU[c["vid"]])
    J = jac(hero_xy, X)
    r = (hero_xy(X) - c["ref"]).ravel()
    rows, cols, vals = [], [], []
    for l in range(len(X)):
        for k in range(3):
            v = c["vid"][l, k]
            JA = c["bar"][l, k] * J[l] @ A[v]                # (2, 3)
            for a in range(2):
                for b in range(3):
                    rows.append(2 * l + a)
                    cols.append(3 * v + b)
                    vals.append(JA[a, b])
    w = np.repeat(np.where(np.isin(c["ids"], JAW_OVAL), 1.5, 1.0), 2)
    Jm = sp.csr_matrix((vals, (rows, cols)), shape=(2 * len(X), 3 * n))
    add(sp.diags(np.sqrt(w)) @ Jm, np.sqrt(w) * r, HERO_SIGMA_PX)
    # hero hand points: the mean of their vertices
    hid = E["hand_ids"]
    rows, cols, vals, rr = [], [], [], []
    for q, (k, xy) in enumerate(HAND.items()):
        ids = hid[q][hid[q] >= 0]
        Xh = PU[ids].mean(0)
        Jh = jac(hero_xy, Xh[None])[0]
        rr.extend(list((hero_xy(Xh[None])[0] - np.array(xy)) / HAND_SIGMA[k]))
        for v in ids:
            JA = Jh @ A[v] / len(ids) / HAND_SIGMA[k]
            for a in range(2):
                for b in range(3):
                    rows.append(2 * q + a)
                    cols.append(3 * v + b)
                    vals.append(JA[a, b])
    add(sp.csr_matrix((vals, (rows, cols)), shape=(2 * len(HAND), 3 * n)), np.array(rr), 1.0)
    # the R001 views (rest): X = sum b (V + U)
    VU = V + U0
    for v, par in cams["views"].items():
        if v not in corr or v == "profile":
            continue
        c = corr[v]
        if not len(c["ids"]):
            continue
        X = np.einsum("lk,lki->li", c["bar"], VU[c["vid"]])
        fn = lambda Y, par=par: proj_view(Y, par)        # noqa: E731
        J = jac(fn, X)
        r = (fn(X) - c["ref"]).ravel()
        sig = VIEW_SIGMA_MM * par["f"] / VIEW_DIST     # px per mm at the head
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
    # the profile silhouette, brow to throat: r = x(P) - edge(y(P)) at the model's outline vertices, and its
    # four features (glabella, nasion, nose tip, chin) as points
    if "profile" in cams["views"] and "profile" in corr:
        par = cams["views"]["profile"]
        (sa, sb, st), r, g, feat = profile_terms(E, U0, par, corr["profile"])
        k = len(r)
        rows = np.repeat(np.arange(k), 6)
        cols = np.concatenate([3 * sa[:, None] + np.arange(3), 3 * sb[:, None] + np.arange(3)], 1).ravel()
        vals = np.concatenate([g * (1 - st)[:, None], g * st[:, None]], 1).ravel()
        sig = EDGE_SIGMA_MM * par["f"] / VIEW_DIST
        add(sp.csr_matrix((vals, (rows, cols)), shape=(k, 3 * n)), r, sig)
        Pf = np.array([pt(VU, feat[q][0]) for q in feat])
        fr = np.array([feat[q][1] for q in feat])
        J = jac(lambda Y: proj_view(Y, par), Pf)
        rows, cols, vals = [], [], []
        for l, q in enumerate(feat):
            a_, b_, t_ = feat[q][0]
            for vv, wv in ((a_, 1 - t_), (b_, t_)):
                for i_ in range(2):
                    for j_ in range(3):
                        rows.append(2 * l + i_)
                        cols.append(3 * vv + j_)
                        vals.append(wv * J[l, i_, j_])
        add(sp.csr_matrix((vals, (rows, cols)), shape=(2 * len(Pf), 3 * n)), (proj_view(Pf, par) - fr).ravel(), sig)
    # the relief (rest): the depth direction's component of U at each vertex
    for v in DEPTH_VIEWS:
        if v + "_depth" in corr:
            c = corr[v + "_depth"]
            vid, delta, dvec = c["vid"], c["delta"], c["dir"]
            cur = (U0[vid] @ dvec)                   # what U0 already gave towards it this round
            rows = np.repeat(np.arange(len(vid)), 3)
            cols = (3 * vid[:, None] + np.arange(3)).ravel()
            add(sp.csr_matrix((np.tile(dvec, len(vid)), (rows, cols)), shape=(len(vid), 3 * n)), cur - delta, DEPTH_SIGMA_MM)
    # the silhouettes: the hero's far cheek (posed) and the three-quarter's far cheek (rest)
    def add_sil(abt, r, g, sigma, posed):
        a_, b_, t_ = abt
        k = len(r)
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
        abt, r, g = sil_hero(E, U0, nuis, ref)
        add_sil(abt, r, g, HERO_SIL_SIGMA_PX, True)
    if "threequarter_edge" in ref and "threequarter" in cams["views"]:
        par = cams["views"]["threequarter"]
        abt, r, g = sil_threequarter(E, U0, par, ref)
        add_sil(abt, r, g, EDGE_SIGMA_MM * par["f"] / VIEW_DIST, False)
    # regularisation on the total U: bending, a weak Tikhonov, the cranium, the neck ring, the skull top
    u0 = U0.ravel()
    add(L3, L3 @ u0, BEND_SIGMA)
    add(sp.identity(3 * n, format="csr"), u0, TIKH_SIGMA)
    cran = np.where(((V[:, 2] > TRICHION_Z) | ((V[:, 1] > -20.0) & (V[:, 2] > 1700.0))) & ~E["ears"])[0]
    sel = (3 * cran[:, None] + np.arange(3)).ravel()
    Sel = sp.csr_matrix((np.ones(len(sel)), (np.arange(len(sel)), sel)), shape=(len(sel), 3 * n))
    add(Sel, u0[sel], CRANIUM_SIGMA)
    ring = np.where(E["ring"])[0]
    sel = (3 * ring[:, None] + np.arange(3)).ravel()
    Sel = sp.csr_matrix((np.ones(len(sel)), (np.arange(len(sel)), sel)), shape=(len(sel), 3 * n))
    add(Sel, u0[sel], PIN_SIGMA)
    top = int(np.argmax(V[:, 2]))
    add(sp.csr_matrix(([1.0], ([0], [3 * top + 2])), shape=(1, 3 * n)), np.array([u0[3 * top + 2]]), 0.2)
    Jall = sp.vstack(blocks).tocsr() @ S
    b = np.concatenate(rhs)
    du = spl.spsolve((Jall.T @ Jall).tocsc(), Jall.T @ b)
    return U0 + (S @ du).reshape(-1, 3)


def solve_cams(E, corr, cams, nuis, U):
    """Each view's camera (head rotation, focal, principal point) and the hero nuisance, U fixed."""
    from scipy.optimize import least_squares
    V, P0, A = E["V_rest"], E["P0"], E["A"]
    VU = V + U
    PU = P0 + np.einsum("kij,kj->ki", A, U)
    out = {"views": {}}
    for v, par in cams["views"].items():
        if v == "profile":
            out["views"][v] = fit_profile_cam(E, U, par, corr["profile"], iters=2) if "profile" in corr else par
            continue
        if v not in corr or len(corr[v]["ids"]) < 20:
            out["views"][v] = par
            continue
        c = corr[v]
        X = np.einsum("lk,lki->li", c["bar"], VU[c["vid"]])

        def res(z, par=par):
            p = dict(par, rot=list(z[:3]), f=z[3], cx=z[4], cy=z[5])
            return np.concatenate([(proj_view(X, p) - c["ref"]).ravel() / 3.0, z[:3] / np.array(ROT_PRIOR[v])])
        z0 = np.array(list(par["rot"]) + [par["f"], par["cx"], par["cy"]], float)
        s = least_squares(res, z0)
        out["views"][v] = dict(par, rot=[float(a) for a in s.x[:3]], f=float(s.x[3]), cx=float(s.x[4]), cy=float(s.x[5]))
    c = corr["hero"]
    X = np.einsum("lk,lki->li", c["bar"], PU[c["vid"]])
    piv = E["pivot"]

    def res_h(z):
        Rn = rotvec(np.radians(z[:3]))
        xy = hero_proj(piv + (X - piv) @ Rn.T) + z[3:5]
        return np.concatenate([((xy - c["ref"]) / HERO_SIGMA_PX).ravel(), z[:3] / ROT_SIGMA_DEG, z[3:5] / SHIFT_SIGMA_PX])
    s = least_squares(res_h, nuis)
    return out, s.x


def view_errors(E, corr, cams, nuis, U):
    """Per-view landmark residuals (px of that view and mm at the head) for the current U, cameras, nuisance."""
    V, P0, A = E["V_rest"], E["P0"], E["A"]
    out = {}
    PU = P0 + np.einsum("kij,kj->ki", A, U)
    c = corr["hero"]
    X = np.einsum("lk,lki->li", c["bar"], PU[c["vid"]])
    piv = E["pivot"]
    Rn = rotvec(np.radians(nuis[:3]))
    out["hero_with_nuisance"] = residual_stats(hero_proj(piv + (X - piv) @ Rn.T) + nuis[3:5], c["ref"], c["ids"])
    out["hero_no_nuisance"] = residual_stats(hero_proj(X), c["ref"], c["ids"])
    for v, par in cams["views"].items():
        if v not in corr or v == "profile":
            continue
        c = corr[v]
        X = np.einsum("lk,lki->li", c["bar"], (V + U)[c["vid"]])
        st = residual_stats(proj_view(X, par), c["ref"], c["ids"])
        st["rms_mm"] = round(st["rms_px"] * VIEW_DIST / par["f"], 2)
        out[v] = st
    ref = corr["ref"]
    if "hero_edge" in ref:
        _, r, _ = sil_hero(E, U, nuis, ref)
        out["hero_silhouette"] = {"n": int(len(r)), "rms_px": round(float(np.sqrt(np.mean(r ** 2))), 3),
                                  "mean_px": round(float(np.mean(r)), 3)}
    if "threequarter_edge" in ref and "threequarter" in cams["views"]:
        par = cams["views"]["threequarter"]
        _, r, _ = sil_threequarter(E, U, par, ref)
        mm = VIEW_DIST / par["f"]
        out["threequarter_silhouette"] = {"n": int(len(r)), "rms_mm": round(float(np.sqrt(np.mean(r ** 2))) * mm, 2),
                                          "mean_mm": round(float(np.mean(r)) * mm, 2)}
    if "profile" in corr and "profile" in cams["views"]:
        par = cams["views"]["profile"]
        sel, r, _, feat = profile_terms(E, U, par, corr["profile"])
        mm = VIEW_DIST / par["f"]
        fe = {k: round(float(np.linalg.norm(proj_view(pt(V + U, abt)[None], par)[0] - xy)) * mm, 2) for k, (abt, xy) in feat.items()}
        out["profile"] = {"n": int(len(r)), "rms_mm": round(float(np.sqrt(np.mean(r ** 2))) * mm, 2), "features_mm": fe}
    return out


def extend(E, U):
    """The skin field U on the region -> a displacement of every vertex of Body.Mesh (mm): the region's skin
    as solved; helper vertices by inverse distance from the 8 nearest region skin vertices, fading out
    beyond 25 mm from the skin; the eyes, teeth, tongue and joint cubes rigidly (their group's mean)."""
    from scipy.spatial import cKDTree
    Vall, idx = E["V_all"], E["idx"]
    D = np.zeros_like(Vall)
    D[idx] = U
    tree = cKDTree(E["V_rest"])
    others = np.where(~E["in_body"])[0]
    d, j = tree.query(Vall[others], k=8)
    w = 1.0 / np.maximum(d, 0.5) ** 2
    Dh = np.einsum("nk,nki->ni", w, U[j]) / w.sum(1, keepdims=True)
    fade = np.clip(1.0 - (d[:, 0] - 25.0) / 25.0, 0.0, 1.0)
    D[others] = Dh * fade[:, None]
    names = list(E["helper_names"])
    for gi, nm in enumerate(names):
        if nm in RIGID_HELPERS or nm.startswith("joint-"):
            sel = np.where(E["helper"] == gi)[0]
            sel = sel[~E["in_body"][sel]]
            if len(sel):
                D[sel] = D[sel].mean(0)
    return D


# =========================================================================== reference data and cameras

def reference():
    from PIL import Image
    ref = {"hero": hero_points(REF_CROP)}
    for v, (fn, _) in VIEWS.items():
        p = os.path.join(R001, fn)
        if os.path.exists(p):
            ref[v] = mp_points(np.array(Image.open(p).convert("RGB")))
    if os.path.exists(os.path.join(R001, VIEWS["profile"][0])):
        ref["profile_edge"] = profile_edge(os.path.join(R001, VIEWS["profile"][0]))
    ref.update(ref_edges(ref))
    for v in DEPTH_VIEWS:
        p = os.path.join(R001, VIEWS[v][0])
        if os.path.exists(p) and os.path.isdir(DA_DIR):
            ref[v + "_da"] = depth_map(np.array(Image.open(p).convert("RGB")))
    return ref


INIT_IDS = {"front": [1, 168, 6, 2, 0, 17, 199, 33, 133, 362, 263, 61, 291, 234, 454, 172, 397],
            "threequarter": [1, 168, 6, 2, 0, 17, 199, 33, 133, 362, 263, 61, 291, 454, 397],
            "profile": [1, 168, 6, 197, 195, 5, 4, 2, 0, 13, 17, 18, 200, 199]}


def initial_cams(E, ref, hero):
    """Start each view's camera from its yaw and solve the head rotation, focal and principal point on a few
    stable landmarks (the midline in profile), their model points taken from the hero view's correspondences."""
    from scipy.optimize import least_squares
    V = E["V_rest"]
    pts = {int(i): np.einsum("k,ki->i", b, V[vid]) for i, vid, b in zip(hero["ids"], hero["vid"], hero["bar"])}
    # the far side (his left) is hidden in the hero view: mirror MediaPipe's right-side points
    for l, r in {263: 33, 362: 133, 291: 61, 454: 234, 397: 172}.items():
        if l not in pts and r in pts:
            pts[l] = pts[r] * np.array([-1.0, 1.0, 1.0])
    cams = {"views": {}}
    for v, (_, yaw) in VIEWS.items():
        if v not in ref or ref[v] is None or v == "profile":
            continue
        ids = [i for i in INIT_IDS[v] if i in pts]
        X = np.array([pts[i] for i in ids])
        par = {"yaw": yaw, "rot": [0.0, 0.0, 0.0], "f": 5000.0, "cx": VIEW_PX / 2, "cy": VIEW_PX / 2}

        def res(z, par=par, X=X, ids=ids, v=v):
            p = dict(par, rot=list(z[:3]), f=z[3], cx=z[4], cy=z[5])
            return np.concatenate([(proj_view(X, p) - ref[v][ids]).ravel(), z[:3] / np.array(ROT_PRIOR[v])])
        s = least_squares(res, np.array([0, 0, 0, 5000.0, VIEW_PX / 2, VIEW_PX / 2]))
        cams["views"][v] = dict(par, rot=[float(a) for a in s.x[:3]], f=float(s.x[3]), cx=float(s.x[4]), cy=float(s.x[5]))
        say(f"initial camera {v}: {len(ids)} points, rot {np.round(s.x[:3], 1)} f {s.x[3]:.0f} px, "
            f"rms {np.sqrt(np.mean(s.fun[:-3] ** 2)):.1f} px")
    if ref.get("profile") is not None and "front" in cams["views"]:
        cp = profile_corr(E, ref, hero)
        par = {"yaw": 90.0, "rot": [cams["views"]["front"]["rot"][0], 0.0, 0.0], "f": cams["views"]["front"]["f"],
               "cx": VIEW_PX / 2, "cy": VIEW_PX / 2}
        U0 = np.zeros_like(V)
        _, _, _, feat = profile_terms(E, U0, par, cp)
        abt, xy = feat["pronasale"]                 # the model's nose tip on the reference's, then the outline fit
        d = xy - proj_view(pt(V, abt)[None], par)[0]
        par["cx"] += float(d[0])
        par["cy"] += float(d[1])
        par = fit_profile_cam(E, U0, par, cp)
        cams["views"]["profile"] = par
        sel, r, _, feat = profile_terms(E, U0, par, cp)
        say(f"initial camera profile: outline {len(r)} rows, rot {np.round(par['rot'], 1)} f {par['f']:.0f} px, "
            f"rms {np.sqrt(np.mean(r ** 2)):.1f} px")
    return cams


def refresh(rdir, blend, cams, ref, nuis):
    """Export and detect; solve the cameras on that (U = 0); export and detect again through the new cameras,
    so the model is rendered as each view sees it."""
    E = export(rdir, blend, cams)
    corr = correspondences(E, None, cams, rdir, ref)
    U = np.zeros_like(E["V_rest"])
    for _ in range(2):
        cams, nuis = solve_cams(E, corr, cams, nuis, U)
    E = export(rdir, blend, cams)
    corr = correspondences(E, None, cams, rdir, ref)
    return E, corr, cams, nuis


# =========================================================================== the fit

def fit_main(rounds=3, inner=4):
    os.makedirs(WORK, exist_ok=True)
    t_all = time.perf_counter()
    ref = reference()
    say("reference views:", [k for k in ref if ref[k] is not None])
    cams_path = os.path.join(WORK, "cams.json")
    target = os.path.join(WORK, SHAPE_NAME + ".target")
    if os.path.exists(target):
        os.remove(target)
    log = []
    D_total = None
    cams = None
    for rnd in range(rounds):
        t0 = time.perf_counter()
        rdir = os.path.join(WORK, f"round{rnd}")
        os.makedirs(rdir, exist_ok=True)
        build_dev(target if rnd else None, DEV_BLEND, f"round{rnd}")
        if cams is None:
            E = export(rdir, DEV_BLEND, {"views": {}})
            cams = initial_cams(E, ref, correspondences(E, None, {"views": {}}, rdir, ref)["hero"])
            nuis = np.zeros(5)
        E, corr, cams, nuis = refresh(rdir, DEV_BLEND, cams, ref, nuis)
        if D_total is None:
            D_total = np.zeros_like(E["V_all"])
        maps = build_maps(E)
        U = np.zeros_like(E["V_rest"])
        before = view_errors(E, corr, cams, nuis, U)
        for k in range(inner):
            cams, nuis = solve_cams(E, corr, cams, nuis, U)
            U = solve_U(E, corr, cams, nuis, U, maps)
        cams, nuis = solve_cams(E, corr, cams, nuis, U)
        after = view_errors(E, corr, cams, nuis, U)
        D_total = D_total + extend(E, U)
        write_target(D_total, target, note=f"round {rnd}")
        with open(cams_path, "w") as f:
            json.dump(cams, f, indent=1)
        un = np.linalg.norm(U, axis=1)
        rec = {"round": rnd, "before": before, "after": after, "nuisance": [round(float(a), 2) for a in nuis],
               "cams": cams, "U_mm": {"max": round(float(un.max()), 2), "p95": round(float(np.percentile(un, 95)), 2),
                                      "median": round(float(np.median(un)), 2)},
               "landmarks": {k: int(len(corr[k]["ids"])) for k in ("hero", *cams["views"]) if k in corr and "ids" in corr[k]},
               "seconds": round(time.perf_counter() - t0, 1)}
        log.append(rec)
        say(f"round {rnd}: U max {rec['U_mm']['max']} p95 {rec['U_mm']['p95']} mm; hero rms "
            f"{before['hero_with_nuisance']['rms_px']} -> {after['hero_with_nuisance']['rms_px']} px; "
            + "; ".join(f"{v} {before[v]['rms_mm']} -> {after[v]['rms_mm']} mm" for v in cams["views"] if v in before and v != "profile")
            + (f"; profile outline {before['profile']['rms_mm']} -> {after['profile']['rms_mm']} mm "
               f"features {after['profile']['features_mm']}" if "profile" in after else "")
            + "; silhouettes hero " + str(before.get("hero_silhouette")) + " -> " + str(after.get("hero_silhouette"))
            + ", 3q " + str(before.get("threequarter_silhouette")) + " -> " + str(after.get("threequarter_silhouette")))
        with open(os.path.join(WORK, "fit_log.json"), "w") as f:
            json.dump(log, f, indent=1, default=float)
    # the deliverable: the target and its record
    import shutil
    shutil.copyfile(target, SHAPE_TARGET)
    build_dev(SHAPE_TARGET, DEV_BLEND, "final")
    rec = {"note": "Head round 2: the head-shape corrective, scripts/parts/head_shape.py --fit (head.md §6). Applied by "
                   "base.py after head_fit.json's targets (head_shape.apply).",
           "target": os.path.relpath(SHAPE_TARGET, PROJECT).replace("\\", "/"),
           "displacement_mm": {"max": round(float(np.linalg.norm(D_total, axis=1).max()), 2)},
           "sigmas": {"hero_px": HERO_SIGMA_PX, "view_mm": VIEW_SIGMA_MM, "edge_mm": EDGE_SIGMA_MM, "bend": BEND_SIGMA,
                      "tikhonov_mm": TIKH_SIGMA, "cranium_mm": CRANIUM_SIGMA},
           "pose": "cache/head_r2/hero_pose_r1.json (round 1's committed hero pose)",
           "cams": cams, "log": log, "seconds": round(time.perf_counter() - t_all, 1)}
    with open(SHAPE_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=1, default=float)
    return log


def check_main(tag, blend):
    """Landmark residuals of a base file, nothing fitted: the hero (as head.py --check: MediaPipe on the posed
    model's render against MediaPipe on the reference, no nuisance) and, with the fit's cameras re-solved for
    this mesh alone (the shape cannot move), the R001 views."""
    ref = reference()
    rdir = os.path.join(WORK, f"check_{tag}")
    cams_path = os.path.join(WORK, "cams.json")
    E = export(rdir, blend, {"views": {}})
    cams = initial_cams(E, ref, correspondences(E, None, {"views": {}}, rdir, ref)["hero"])
    nuis = np.zeros(5)
    E, corr, cams, nuis = refresh(rdir, blend, cams, ref, nuis)
    U = np.zeros_like(E["V_rest"])
    for _ in range(2):
        cams, nuis = solve_cams(E, corr, cams, nuis, U)
    out = view_errors(E, corr, cams, nuis, U)
    c = corr["hero"]
    keyres = {}
    for k, i in KEY.items():
        if i in set(c["ids"]):
            keyres[k] = round(float(np.linalg.norm(c["mod"][i] - ref["hero"][i])), 2)
    out["hero_key_px"] = keyres
    e = np.linalg.norm(c["mod"][c["ids"]] - c["ref"], axis=1)
    out["hero_detector"] = {"n": int(len(e)), "rms_px": round(float(np.sqrt(np.mean(e ** 2))), 3),
                            "median_px": round(float(np.median(e)), 3),
                            "jaw_oval_rms_px": round(float(np.sqrt(np.mean(np.array([np.linalg.norm(c["mod"][i] - ref["hero"][i]) for i in JAW_OVAL]) ** 2))), 3)}
    for v in cams["views"]:
        if v in corr and v != "profile":
            c = corr[v]
            e = np.linalg.norm(c["mod"][c["ids"]] - c["ref"], axis=1)
            out[v + "_detector"] = {"n": int(len(e)), "rms_mm": round(float(np.sqrt(np.mean(e ** 2))) * VIEW_DIST / cams["views"][v]["f"], 2)}
    out["dims_mm"] = dims(E)
    out["note"] = ("hero_detector: MediaPipe on the posed model's hero render vs on ref/crop_head_face.png (full-frame px, "
                   "no nuisance; round 1's measure). <view>_detector: MediaPipe on the rest model through the view's "
                   "fitted camera vs on gen/R001 (mm at the head). profile_edge: the model's front outline vs the "
                   "profile's silhouette, brow to throat.")
    with open(os.path.join(WORK, f"check_{tag}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    overlays(corr, ref, rdir, cams, tag)
    say(tag, json.dumps({k: out[k] for k in out if k not in ("note",)}))
    return out


def dims(E):
    """A few rest head breadths and heights (mm, skin without the ears), against take 1's spec 06 §2.5/§3.1 figures:
    the widest breadth in front of the ears between the eyes and the ear lobes (~bizygomatic), the breadth 38 mm
    above the menton behind the mouth (~bigonial), vertex to menton, and how far the nose stands in front of the
    face's widest section."""
    V = E["V_rest"][~E["ears"]]
    chin = E["V_rest"][int(E["mark_ids"][0])]
    nose = E["V_rest"][int(E["mark_ids"][1])]
    top = V[np.argmax(V[:, 2])]

    def width(z, ymax, ymin=-400.0):
        s = V[(np.abs(V[:, 2] - z) < 2.5) & (V[:, 1] < ymax) & (V[:, 1] > ymin)]
        return round(float(np.ptp(s[:, 0])), 1) if len(s) else None
    zyg = max((width(z, chin[1] + 120.0) or 0, z) for z in np.arange(nose[2] + 10, nose[2] + 70, 2.0))
    return {"vertex_to_menton": round(float(top[2] - chin[2]), 1), "menton_z": round(float(chin[2]), 1),
            "bizygomatic_like": zyg[0], "at_z": zyg[1],
            "width_menton+38": width(chin[2] + 38.0, chin[1] + 120.0),
            "width_menton+20": width(chin[2] + 20.0, chin[1] + 120.0),
            "nose_tip_y": round(float(nose[1]), 1), "menton_y": round(float(chin[1]), 1),
            "spec06": {"vertex_to_menton": 237, "bizygomatic": 152, "bigonial": 138}}


def overlays(corr, ref, rdir, cams, tag):
    """renders/head/head_r2_landmarks_<tag>_<view>.png: the reference with MediaPipe's points (red: reference,
    green: model) beside the model render."""
    from PIL import Image, ImageDraw
    out = os.path.join(PROJECT, "renders", "head")
    os.makedirs(out, exist_ok=True)
    pairs = [("hero", REF_CROP, os.path.join(rdir, "model_hero.png"), lambda p: (p - np.array([715.0, 30.0])) * 5.0)]
    for v in cams["views"]:
        if v != "profile":
            pairs.append((v, os.path.join(R001, VIEWS[v][0]), os.path.join(rdir, f"model_{v}.png"), lambda p: p))
    for v, rp, mp_, tf in pairs:
        if v not in corr:
            continue
        im = Image.open(rp).convert("RGB")
        mo = Image.fromarray(load_rgb(mp_)).resize(im.size)
        d = ImageDraw.Draw(im)
        c = corr[v]
        for i in c["ids"]:
            a, b = tf(ref[v][i]), tf(c["mod"][i])
            d.line([tuple(a), tuple(b)], fill=(255, 255, 0), width=1)
            d.ellipse([a[0] - 3, a[1] - 3, a[0] + 3, a[1] + 3], fill=(255, 40, 40))
            d.ellipse([b[0] - 3, b[1] - 3, b[0] + 3, b[1] + 3], fill=(40, 255, 40))
        sheet = Image.new("RGB", (im.width * 2 + 10, im.height), (20, 20, 20))
        sheet.paste(im, (0, 0))
        sheet.paste(mo, (im.width + 10, 0))
        if sheet.width > 1700:
            sheet = sheet.resize((1700, int(sheet.height * 1700 / sheet.width)))
        sheet.save(os.path.join(out, f"head_r2_landmarks_{tag}_{v}.png"))


# =========================================================================== entry

def main():
    if in_blender():
        a = _argv()
        if a and a[0] == "--build-dev":
            return bl_build_dev(a[1] or None, a[2])
        if a and a[0] == "--export":
            bl_export(a[1], a[2], a[3])
            return 0
        raise SystemExit("head_shape.py in Blender: --build-dev TARGET OUT | --export DIR BLEND CAMS")
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--check", default=None)
    ap.add_argument("--blend", default=None)
    args = ap.parse_args()
    if args.fit:
        fit_main(args.rounds)
    if args.check:
        check_main(args.check, args.blend or DEV_BLEND)
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
        os._exit(rc or 0)
    sys.exit(main())
