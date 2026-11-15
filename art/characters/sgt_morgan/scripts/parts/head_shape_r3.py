"""The head, round 3: round 2's head-shape transfer with Hunyuan3D 2's mesh as a soft form prior (head.md §10).

Round 2 (head_shape.py) matched the head's outlines in four views but left the form inside them MPFB's: soft and
jowly. Round 3 keeps round 2's machinery and every one of its terms (hero and R001 landmarks, the hero and
three-quarter far-cheek silhouettes, the profile outline and features, the relief) and adds a prior from the
50-step multi-view Hunyuan3D 2 model run on gen/R001's front and left profile (scripts/parts/head_hy3d.md):

- several seeds (cache/hy3d/r3/*.glb and the probe's two plain-decoded ones), each aligned to MPFB's head on its own:
  MediaPipe on an orthographic front clay render of each (the same detector on both), scale from the eye-centre to
  menton distance, rotation and shift by a fixed-scale Procrustes fit on stable landmarks, then point-to-plane ICP
  (rigid) over the masked face;
- a mask on MPFB's head (built once, on round 2's face): the jaw line and its edge, under the jaw down to the neck
  crease, the cheek planes and the hollow under the cheekbones, the nasal bridge and tip, the brow ridge; zero on the
  eyes and lids, the lips and moustache, the ears, the forehead under the hair and the neck below the prior's cut;
- per round, each masked vertex's signed distance along its normal to each seed's surface, averaged over the seeds
  (their spread kept as an uncertainty) and lightly low-passed on the mesh graph;
- two terms in the solve, both on the band-passed offset (d less d diffused ~20 mm over the mask, so the prior asks
  for local forms and never for a broad narrowing): (1) the form: round 2's bending energy |L U|^2 becomes
  |L U - L D|^2 inside the mask, where D = m d n is the prior's displacement field, so the field takes the prior's
  local curvature (edges, creases, hollows); (2) a data term n.U = d (sigma 2.5 mm plus the seed spread, clipped at
  5 mm a round), which the outline and landmark terms outweigh where they see the surface;
- the R001 views' cameras are solved in round 0 and then held (MediaPipe's reading moves with the new shading).

Developed on copies (the pipeline's base.py is not touched): the development bases are built by base.py as committed
in COMMIT_BASE (round 2's base.py: stature 1835, no head-shape wiring), loaded under base.py's own path, with
head-shape(-r3).target added after the face targets exactly as head_shape.py's --build-dev does, so round 2's and
round 3's numbers come from the same harness and the same round-1 hero pose snapshot.

  "$SGT_PYIMG" -I scripts/parts/head_shape_r3.py --prior          # align the seeds, build the mask: cache/head_r3/prior.npz
  "$SGT_PYIMG" -I scripts/parts/head_shape_r3.py --fit [--rounds 3] # writes scripts/parts/head-shape-r3.target, head_shape_r3.json
  "$SGT_PYIMG" -I scripts/parts/head_shape_r3.py --check r2|r3     # the numbers, cameras re-solved (check_<tag>.json)
  "$SGT_PYIMG" -I scripts/parts/head_shape_r3.py --check-fixed r2|r3   # through round 2's cameras (checkfixed_<tag>.json)
  "$SGT_PYIMG" -I scripts/parts/head_shape_r3.py --render r2|r3    # clay + Cycles sheets into renders/head/r3/
  "$SGT_PYIMG" -I scripts/parts/head_shape_r3.py --sheets          # r2 | r3 side-by-side sheets

To switch the pipeline: copy head-shape-r3.target over head-shape.target (base.py's head_shape.apply loads that
file) and rebuild base, re-solve the pose and rebuild the parts, as head.md §6.6.

Left/right are the soldier's own; +X is his left, he faces -Y (CLAUDE.md).
"""
import argparse
import glob
import json
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

import head_shape as HS  # noqa: E402

COMMIT_BASE = "dca7a15"                 # base.py as committed before round 4's wiring (stature 1835)
WORK = os.path.join(PROJECT, "cache", "head_r3")
DEV_R2 = os.path.join(PROJECT, "cache", "stages", "head_dev_r2.blend")
DEV_R3 = os.path.join(PROJECT, "cache", "stages", "head_dev_r3.blend")
TARGET_R2 = HS.SHAPE_TARGET             # scripts/parts/head-shape.target (round 2)
TARGET_R3 = os.path.join(HERE, "head-shape-r3.target")
JSON_R3 = os.path.join(HERE, "head_shape_r3.json")
PRIOR = os.path.join(WORK, "prior.npz")
RENDERS = os.path.join(PROJECT, "renders", "head", "r3")
SEED_GLOBS = ("cache/hy3d/r3/mv50fv_own_s*.glb", "cache/hy3d/mv50_fl_o380.glb", "cache/hy3d/mv50_fl_o380_s7.glb")
SEED_SKIP = ("cache/hy3d/r3/mv50fv_own_s12345.glb", "cache/hy3d/r3/mv50fv_own_s7.glb")  # same latents as the plain ones

# the prior's weights
PRIOR_SIGMA_MM = 2.5                    # the data term n.U = d, per vertex (plus the seed spread)
PRIOR_CLIP_MM = 5.0                     # a round's correction is clipped to this
LAP_SIGMA = 0.2                         # mm: |L U - L D| inside the mask (round 2's bending sigma outside)
LOWPASS_STEPS = 2                       # diffusion steps on d before use (kills the stubble noise)
HIGHPASS_STEPS = 24                     # the data term uses d less d diffused this much (~20 mm): the prior asks for
                                        # local forms, never the broad cheek narrowing that fought the far-cheek outlines
DETAIL_STEPS = 24                       # the curvature term likewise: local detail only
# the R001 views' cameras are solved in round 0 (on round 2's face) and then held: MediaPipe's reading of a view
# moves with the shading once hollows and edges appear, and re-solving the cameras on it turned the views
FREEZE_CAMS = os.environ.get("R3_FREEZE_CAMS", "1") == "1"
# trial overrides (environment): R3_PRIOR_SIGMA, R3_LAP_SIGMA, R3_DETAIL_STEPS, R3_HIGHPASS_STEPS, R3_FREEZE_CAMS
PRIOR_SIGMA_MM = float(os.environ.get("R3_PRIOR_SIGMA", PRIOR_SIGMA_MM))
LAP_SIGMA = float(os.environ.get("R3_LAP_SIGMA", LAP_SIGMA))
DETAIL_STEPS = int(os.environ.get("R3_DETAIL_STEPS", DETAIL_STEPS))
HIGHPASS_STEPS = int(os.environ.get("R3_HIGHPASS_STEPS", HIGHPASS_STEPS))

ALIGN_IDS = [168, 6, 197, 195, 5, 4, 1, 2, 164, 152, 199, 175, 33, 133, 362, 263, 61, 291, 50, 280, 205, 425,
             117, 346, 101, 330]    # inner points only: the face oval's depth is a grazing ray in a front view
EYE_R, EYE_L = [33, 133, 159, 145], [362, 263, 386, 374]


def say(*a):
    print("[hshape-r3]", *a, flush=True)


# =========================================================================== Blender side

def _load_base_r2era():
    """base.py as committed in COMMIT_BASE, loaded as the module `base` under base.py's own path (its PROJECT and
    output paths resolve as usual; head_shape.bl_build_dev then patches its outputs and targets)."""
    import types
    src = subprocess.run(["git", "show", f"{COMMIT_BASE}:./scripts/stages/base.py"], cwd=PROJECT, capture_output=True,
                         text=True, encoding="utf-8").stdout
    if "def main" not in src:
        raise SystemExit(f"git show {COMMIT_BASE}:scripts/stages/base.py failed")
    mod = types.ModuleType("base")
    mod.__file__ = os.path.join(SCRIPTS, "stages", "base.py")
    sys.modules["base"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def bl_build_dev(target, out_blend):
    _load_base_r2era()
    return HS.bl_build_dev(target, out_blend)


def bl_prior_render(out_dir, export_npz, glbs):
    """Orthographic front clay renders (Workbench, 1024 px) of MPFB's head region (from export.npz) and of each
    Hunyuan mesh (glTF import: Z up, facing -Y), and each mesh's vertices and triangles in Blender's frame."""
    import bpy
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light, sh.color_type, sh.single_color = "STUDIO", "SINGLE", (0.8, 0.78, 0.75)
    sh.show_cavity, sh.cavity_type, sh.show_specular_highlight = True, "BOTH", False
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = 1024
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGBA"
    sc.view_settings.view_transform = "Standard"
    cam = bpy.data.objects.new("R3.Cam", bpy.data.cameras.new("R3.Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    meta = {}

    def shoot(ob, name, V, frac_top=None):
        lo, hi = V.min(0), V.max(0)
        c = (lo + hi) / 2
        ext = float(max(hi - lo))
        if frac_top is not None:          # MPFB's region runs down the neck: frame the skull top to below the chin
            ext = frac_top
            c[2] = hi[2] - ext / 2
        S = ext * 1.18
        cam.data.ortho_scale = S
        cam.location = (c[0], c[1] - ext * 3, c[2])
        cam.rotation_euler = (np.pi / 2, 0, 0)
        cam.data.clip_end = ext * 10
        sc.render.filepath = os.path.join(out_dir, f"{name}_front.png")
        bpy.ops.render.render(write_still=True)
        meta[name] = {"cx": float(c[0]), "cz": float(c[2]), "S": S, "px": 1024}

    # MPFB (mm -> m)
    E = np.load(export_npz)
    V = E["V_rest"] / 1000.0
    me = bpy.data.meshes.new("R3.MPFB")
    me.from_pydata(V.tolist(), [], E["tris"].tolist())
    me.shade_smooth()
    ob = bpy.data.objects.new("R3.MPFB", me)
    sc.collection.objects.link(ob)
    shoot(ob, "mpfb", V, frac_top=0.32)          # 320 mm
    bpy.data.objects.remove(ob, do_unlink=True)
    for g in glbs:
        name = os.path.splitext(os.path.basename(g))[0]
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(PROJECT, g))
        new = [o for o in bpy.data.objects if o not in before]
        obm = [o for o in new if o.type == "MESH"][0]
        dg = bpy.context.evaluated_depsgraph_get()
        m = obm.evaluated_get(dg).to_mesh()
        mw = np.array(obm.matrix_world)
        Vh = np.array([v.co[:] for v in m.vertices])
        Vh = Vh @ mw[:3, :3].T + mw[:3, 3]
        m.calc_loop_triangles()
        F = np.array([t.vertices[:] for t in m.loop_triangles], np.int32)
        obm.evaluated_get(dg).to_mesh_clear()
        for p in obm.data.polygons:
            p.use_smooth = True
        obm.data.materials.clear()
        np.savez_compressed(os.path.join(out_dir, f"{name}_mesh.npz"), V=Vh.astype(np.float32), F=F)
        shoot(obm, name, Vh)
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)
    with open(os.path.join(out_dir, "prior_render.json"), "w") as f:
        json.dump(meta, f, indent=1)
    say("prior renders", list(meta))


def bl_render_dev(blend, prefix, samples):
    """head.py's --dev build and renders on `blend`, into renders/head/r3/ (the part cache in cache/head_r3/)."""
    import head as H
    HS.WORK = WORK
    HS.DEV_BLEND = blend
    HS.DEV_JSON = os.path.splitext(blend)[0] + ".json"
    H.OUT = RENDERS
    os.makedirs(RENDERS, exist_ok=True)
    return H.bl_build(["--dev", "--prefix", prefix, "--samples", str(samples)])


# =========================================================================== outside Blender

def blender(args, log):
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


def build_dev(target, out_blend, tag):
    os.makedirs(WORK, exist_ok=True)
    if target and os.path.basename(target) != HS.SHAPE_NAME + ".target":
        # base.py checks that a target file's stem is its name: load a copy named head-shape.target
        import shutil
        tdir = os.path.join(WORK, "target_" + tag)
        os.makedirs(tdir, exist_ok=True)
        shutil.copyfile(target, os.path.join(tdir, HS.SHAPE_NAME + ".target"))
        target = os.path.join(tdir, HS.SHAPE_NAME + ".target")
    dt = blender(["--build-dev", target or "", out_blend], os.path.join(WORK, f"build_{tag}.log"))
    say(f"dev base {os.path.basename(out_blend)} built in {dt:.0f} s")


def seeds():
    out = []
    for g in SEED_GLOBS:
        out += sorted(os.path.relpath(p, PROJECT).replace("\\", "/") for p in glob.glob(os.path.join(PROJECT, g)))
    return [s for s in out if s not in SEED_SKIP]


def vertex_normals(V, tris):
    n = np.cross(V[tris[:, 1]] - V[tris[:, 0]], V[tris[:, 2]] - V[tris[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, tris[:, k], n)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    if float(np.mean(np.einsum("ij,ij->i", V - V.mean(0), N))) < 0:
        N = -N
    return N


def sample_surface(V, F, n, rng):
    """Area-weighted points on a triangle mesh, with the triangles' normals."""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    cr = np.cross(b - a, c - a)
    area = np.linalg.norm(cr, axis=1)
    k = rng.choice(len(F), n, p=area / area.sum())
    u, v = rng.random(n), rng.random(n)
    flip = u + v > 1
    u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
    P = a[k] + u[:, None] * (b[k] - a[k]) + v[:, None] * (c[k] - a[k])
    N = cr[k] / np.maximum(area[k], 1e-12)[:, None]
    return P, N


def detect_3d(png, meta, V, F=None, tris_ray=None):
    """MediaPipe on an orthographic front render -> 3D points: (x, z) from the pixel, y from the front-most surface
    at that (x, z) (a ray for the sparse MPFB mesh, the nearest dense vertices for a Hunyuan mesh)."""
    pts = HS.mp_points(HS.load_rgb(png))
    if pts is None:
        raise SystemExit(f"MediaPipe found no face in {png}")
    s = meta["S"] / meta["px"]
    x = meta["cx"] + (pts[:, 0] - meta["px"] / 2) * s
    z = meta["cz"] - (pts[:, 1] - meta["px"] / 2) * s
    X = np.full((len(pts), 3), np.nan)
    if tris_ray is not None:
        o = np.stack([x, np.full_like(x, V[:, 1].min() - 1.0), z], 1)
        d = np.tile([0.0, 1.0, 0.0], (len(pts), 1))
        for i, h in enumerate(HS.raycast(o, d, V, tris_ray)):
            if h is not None:
                X[i] = (V[tris_ray[h[0]]] * h[1][:, None]).sum(0)
    else:
        from scipy.spatial import cKDTree
        t = cKDTree(V[:, [0, 2]])
        for i, ids in enumerate(t.query_ball_point(np.stack([x, z], 1), r=2.0 * s)):
            if ids:
                X[i] = V[ids[int(np.argmin(V[ids, 1]))]]
    return X, pts


def eye_chin(X):
    eye = 0.5 * (np.nanmean(X[EYE_R], 0) + np.nanmean(X[EYE_L], 0))
    return eye, X[152]


def procrustes_fixed_scale(A, B, s):
    """R, t minimising |s R A + t - B| (rows are points)."""
    ca, cb = A.mean(0), B.mean(0)
    H = (s * (A - ca)).T @ (B - cb)
    U, _, Vt = np.linalg.svd(H)
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    R = Vt.T @ D @ U.T
    return R, cb - s * R @ ca


def graph(n, edges):
    import scipy.sparse as sp
    W = sp.coo_matrix((np.ones(2 * len(edges)), (np.r_[edges[:, 0], edges[:, 1]], np.r_[edges[:, 1], edges[:, 0]])),
                      shape=(n, n)).tocsr()
    deg = np.asarray(W.sum(1)).ravel()
    return sp.diags(1.0 / np.maximum(deg, 1)) @ W


def diffuse(Wn, f, w, steps):
    """Weighted diffusion on the mesh graph: smooth f where w > 0 (num/den), `steps` half-steps."""
    if steps <= 0:
        return f.copy()
    num = f * w[:, None] if f.ndim == 2 else f * w
    den = w.copy()
    for _ in range(steps):
        num = 0.5 * num + 0.5 * (Wn @ num)
        den = 0.5 * den + 0.5 * (Wn @ den)
    dd = np.maximum(den, 1e-9)
    return num / (dd[:, None] if f.ndim == 2 else dd)


def ramp(x, a, b):
    """0 at x <= a, 1 at x >= b, smooth between."""
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def build_mask(E, L):
    """The prior's mask on MPFB's head region (0..1), from MediaPipe's 3D points L (mm) on the same mesh."""
    V = E["V_rest"]
    eyeR, eyeL = np.nanmean(L[EYE_R], 0), np.nanmean(L[EYE_L], 0)
    eye_z = 0.5 * (eyeR[2] + eyeL[2])
    men = L[152]
    ear = V[E["ears"]]
    ear_front_y = float(np.percentile(ear[:, 1], 3))
    m = np.ones(len(V))
    m *= ramp(V[:, 2], men[2] - 36.0, men[2] - 24.0)              # down to the neck crease, above the prior's cut
    m *= 1 - ramp(V[:, 2], eye_z + 30.0, eye_z + 40.0)           # up to the brow ridge, not the forehead
    m *= 1 - ramp(V[:, 1], ear_front_y - 12.0, ear_front_y - 2.0)  # forward of the ears
    m[E["ears"]] = 0.0
    # the eyes, the lids and the sides of the bridge between the eyes: the prior's eyes sit wider apart than MPFB's
    # (MediaPipe's eye width / nasion-menton 0.86 against 0.73), so near them its forms land on MPFB's canthi
    for e in (eyeR, eyeL):
        r = np.sqrt(((V[:, 0] - e[0]) / 26.0) ** 2 + ((V[:, 2] - e[2]) / 17.0) ** 2 + ((V[:, 1] - e[1]) / 28.0) ** 2)
        m *= ramp(r, 1.0, 1.6)
    # the lips and the moustache: from the subnasale down to below the lower lip, the mouth's width + 5 mm
    mc = 0.5 * (L[61] + L[291])
    a = 0.5 * abs(L[291][0] - L[61][0]) + 5.0
    top, bot = L[2][2] - 1.0, L[17][2] - 3.0
    zc, b = 0.5 * (top + bot), 0.5 * (top - bot)
    r = np.sqrt(((V[:, 0] - mc[0]) / a) ** 2 + ((V[:, 2] - zc) / b) ** 2)
    m *= np.where(V[:, 1] < mc[1] + 25.0, ramp(r, 1.0, 1.35), 1.0)
    Wn = graph(len(V), E["edges"])
    m = diffuse(Wn, m, np.ones(len(V)), 3)
    m[E["ears"]] = 0.0
    m[E["ring"]] = 0.0
    return np.clip(m, 0.0, 1.0)


def prior_main():
    """Align each seed to round 2's head and build the mask: cache/head_r3/prior.npz."""
    os.makedirs(WORK, exist_ok=True)
    if not os.path.exists(DEV_R2):
        build_dev(TARGET_R2, DEV_R2, "r2")
    rdir = os.path.join(WORK, "prior")
    E = HS.export(rdir, DEV_R2, {"views": {}})
    S = seeds()
    say("seeds:", S)
    blender(["--prior-render", rdir, os.path.join(rdir, "export.npz")] + S, os.path.join(rdir, "prior_render.log"))
    meta = json.load(open(os.path.join(rdir, "prior_render.json")))
    Vm, tris = E["V_rest"], E["tris"]
    Lm, _ = detect_3d(os.path.join(rdir, "mpfb_front.png"), {**meta["mpfb"], "cx": meta["mpfb"]["cx"] * 1000,
                                                               "cz": meta["mpfb"]["cz"] * 1000, "S": meta["mpfb"]["S"] * 1000},
                      Vm, tris_ray=tris)
    mask = build_mask(E, Lm)
    Nm = vertex_normals(Vm, tris)
    em, cm = eye_chin(Lm)
    rng = np.random.default_rng(0)
    from scipy.spatial import cKDTree
    out = {"mask": mask, "L_mpfb": Lm, "seeds": np.array(S)}
    rec = {"seeds": {}}
    sel = np.where(mask > 0.3)[0]
    for k, g in enumerate(S):
        name = os.path.splitext(os.path.basename(g))[0]
        M = np.load(os.path.join(rdir, f"{name}_mesh.npz"))
        Vh, Fh = M["V"].astype(float), M["F"]
        Lh, _ = detect_3d(os.path.join(rdir, f"{name}_front.png"), meta[name], Vh)
        eh, ch = eye_chin(Lh)
        s_eye_chin = float(np.linalg.norm(em - cm) / np.linalg.norm(eh - ch))
        ok = [i for i in ALIGN_IDS if np.all(np.isfinite(Lh[i])) and np.all(np.isfinite(Lm[i]))]
        # the scale: MediaPipe on the blank-eyed Hunyuan clay reads its face 15-20 % shorter than wide against
        # R001 and MPFB (eye width / nasion-menton 0.86 against 0.73), so the eye-chin distance alone is biased.
        # Start from the frontal-plane (x, z) similarity of the inner points; the scaled ICP below settles it.
        A2, B2 = Lh[ok][:, [0, 2]], Lm[ok][:, [0, 2]]
        s = float(np.sqrt(((B2 - B2.mean(0)) ** 2).sum() / ((A2 - A2.mean(0)) ** 2).sum()))
        s_init = s
        R, t = procrustes_fixed_scale(Lh[ok], Lm[ok], s)
        lm_rms = float(np.sqrt(np.mean(np.sum((s * Lh[ok] @ R.T + t - Lm[ok]) ** 2, 1))))
        Vh = s * Vh @ R.T + t
        # crop to the head region's box (+20 mm) and sample the surface densely (~0.25 mm spacing)
        lo, hi = Vm.min(0) - 20.0, Vm.max(0) + 20.0
        keepf = np.all((Vh[Fh].min(1) > lo) & (Vh[Fh].max(1) < hi), 1)
        P, N = sample_surface(Vh, Fh[keepf], 2_500_000, rng)
        zcut = float(Vh[:, 2].min())                     # the input's neck cut
        good = P[:, 2] > zcut + 6.0
        P, N = P[good], N[good]
        tree = cKDTree(P)
        # point-to-plane ICP over the masked face (trimmed, the threshold tightening), a similarity: the MPFB points
        # move as X' = c + k Rt (X - c) + tt, then the prior gets the inverse
        X = Vm[sel]
        cc = X.mean(0)
        Rt, tt, kk = np.eye(3), np.zeros(3), 1.0
        for it in range(25):
            Xc = cc + kk * (X - cc) @ Rt.T + tt
            d, j = tree.query(Xc)
            Q, Nq = P[j], N[j]
            r = np.einsum("ij,ij->i", Xc - Q, Nq)
            thr = max(4.0, 12.0 - it)
            w = (np.abs(r) < thr) & (np.einsum("ij,ij->i", Nq, Nm[sel] @ Rt.T) > 0.5)
            Y = Xc[w] - cc
            A = np.concatenate([np.cross(Y, Nq[w]), Nq[w], np.einsum("ij,ij->i", Y, Nq[w])[:, None]], 1)
            A *= np.sqrt(mask[sel][w])[:, None]
            bb = -r[w] * np.sqrt(mask[sel][w])
            x = np.linalg.lstsq(A, bb, rcond=None)[0]
            dR = HS.rotvec(x[:3])
            Rt, tt, kk = dR @ Rt, (1 + x[6]) * dR @ tt + x[3:6], kk * (1 + x[6])
        # apply the inverse of the MPFB-side motion to the prior (the prior moves, MPFB stays)
        P = cc + ((P - cc - tt) @ Rt) / kk
        N = N @ Rt
        tree = cKDTree(P)
        d, j = tree.query(Vm[sel])
        r = np.einsum("ij,ij->i", P[j] - Vm[sel], Nm[sel])
        cv = np.array([Rt[2, 1] - Rt[1, 2], Rt[0, 2] - Rt[2, 0], Rt[1, 0] - Rt[0, 1]]) / 2
        ang = float(np.degrees(np.arcsin(min(1.0, np.linalg.norm(cv)))))
        rec["seeds"][name] = {"scale_eye_chin_mm_per_unit": round(s_eye_chin, 2), "scale_init": round(s_init, 2),
                              "scale_final": round(s_init / kk, 2), "landmarks": len(ok), "landmark_rms_mm": round(lm_rms, 2),
                              "icp_rot_deg": round(ang, 2), "icp_shift_mm": [round(float(a), 2) for a in tt],
                              "icp_inliers": int(w.sum()),
                              "masked_offset_mm": {"mean": round(float(np.mean(r)), 2), "rms": round(float(np.sqrt(np.mean(r ** 2))), 2)}}
        say(name, json.dumps(rec["seeds"][name]))
        out[f"P{k}"] = P.astype(np.float32)
        out[f"N{k}"] = N.astype(np.float32)
    # the seeds' spread over the mask after alignment (each seed's offsets against the others' mean)
    offs = np.array([prior_offsets_seed(Vm[sel], Nm[sel], out[f"P{k}"], out[f"N{k}"]) for k in range(len(S))])
    good = np.all(np.isfinite(offs), 0)
    rec["spread_rms_mm"] = round(float(np.sqrt(np.mean(np.var(offs[:, good], 0)))), 2)
    rec["mean_offset_rms_mm"] = round(float(np.sqrt(np.mean(np.mean(offs[:, good], 0) ** 2))), 2)
    rec["mask"] = {"vertices_over_0.5": int((mask > 0.5).sum()), "region": int(len(mask))}
    say("spread", rec["spread_rms_mm"], "mm; the mean seed's offset from round 2 over the mask", rec["mean_offset_rms_mm"], "mm")
    np.savez_compressed(PRIOR, **out)
    with open(os.path.join(WORK, "prior.json"), "w") as f:
        json.dump(rec, f, indent=1)
    mask_debug(rdir, meta, E, mask)
    return rec


def prior_offsets_seed(X, Nx, P, N, max_mm=10.0):
    """Signed distance along each vertex normal to one seed's surface (nearest dense sample), nan where unreliable."""
    from scipy.spatial import cKDTree
    t = cKDTree(P)
    d, j = t.query(X)
    v = P[j] - X
    r = np.einsum("ij,ij->i", v, Nx)
    lat = np.linalg.norm(v - r[:, None] * Nx, axis=1)
    ok = (np.abs(r) < max_mm) & (np.einsum("ij,ij->i", N[j], Nx) > 0.6) & (lat < 4.0)
    return np.where(ok, r, np.nan)


_TREES = {}


def prior_field(E, prior):
    """Per round: the mean seed offset d (n,), its spread (n,), the weight (mask x coverage) (n,)."""
    V, tris = E["V_rest"], E["tris"]
    N = vertex_normals(V, tris)
    mask = prior["mask"]
    k = len(prior["seeds"])
    sel = np.where(mask > 0.02)[0]
    offs = np.full((k, len(V)), np.nan)
    for s in range(k):
        offs[s, sel] = prior_offsets_seed(V[sel], N[sel], prior[f"P{s}"], prior[f"N{s}"])
    cnt = np.sum(np.isfinite(offs), 0)
    d = np.where(cnt > 0, np.nanmean(np.where(np.isfinite(offs), offs, np.nan), 0) if k else 0.0, 0.0)
    d = np.nan_to_num(d)
    spread = np.nan_to_num(np.nanstd(offs, 0)) if k > 1 else np.zeros(len(V))
    cover = (cnt >= max(1, (k + 1) // 2)).astype(float)
    w = mask * cover
    Wn = graph(len(V), E["edges"])
    d_lp = diffuse(Wn, d, w, LOWPASS_STEPS)
    if HIGHPASS_STEPS:
        d_lp = d_lp - diffuse(Wn, d_lp, w, HIGHPASS_STEPS)
    d_lp = np.where(w > 1e-6, d_lp, 0.0)
    # the curvature term's field: the prior's local detail only (d less its broad shape), so the broad cheek and
    # face shape stay the outlines' and the prior adds the edges, creases and hollows
    d_det = d_lp - diffuse(Wn, d_lp, w, DETAIL_STEPS) if DETAIL_STEPS else d_lp
    d_det = np.where(w > 1e-6, d_det, 0.0)
    return d_lp, spread, w, N, d_det


def solve_U_r3(E, corr, cams, nuis, U0, maps, pf):
    """head_shape.solve_U with the prior: the bending target L D inside the mask and the data term n.U = d."""
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
    # ---- the prior
    d, spread, wm, N, d_det = pf
    u0 = U0.ravel()
    D = (wm * d_det)[:, None] * N                                     # the prior's displacement field, faded by the mask
    inv2 = (1 - wm) / HS.BEND_SIGMA ** 2 + wm / LAP_SIGMA ** 2      # per vertex 1/sigma^2 of the bending rows
    Wr = sp.diags(np.repeat(np.sqrt(inv2), 3))
    add(Wr @ L3, Wr @ (L3 @ (u0 - D.ravel())), 1.0)
    sel = np.where(wm > 0.05)[0]
    cur = np.einsum("ij,ij->i", U0[sel], N[sel])
    tgt = np.clip(d[sel], -PRIOR_CLIP_MM, PRIOR_CLIP_MM)
    sig = np.sqrt(PRIOR_SIGMA_MM ** 2 + spread[sel] ** 2) / np.sqrt(wm[sel])
    rows = np.repeat(np.arange(len(sel)), 3)
    cols = (3 * sel[:, None] + np.arange(3)).ravel()
    Jp = sp.csr_matrix(((N[sel] / sig[:, None]).ravel(), (rows, cols)), shape=(len(sel), 3 * n))
    add(Jp, (cur - tgt) / sig, 1.0)
    # ---- round 2's remaining regularisation
    add(sp.identity(3 * n, format="csr"), u0, HS.TIKH_SIGMA)
    cran = np.where(((V[:, 2] > HS.TRICHION_Z) | ((V[:, 1] > -20.0) & (V[:, 2] > 1700.0))) & ~E["ears"])[0]
    s_ = (3 * cran[:, None] + np.arange(3)).ravel()
    add(sp.csr_matrix((np.ones(len(s_)), (np.arange(len(s_)), s_)), shape=(len(s_), 3 * n)), u0[s_], HS.CRANIUM_SIGMA)
    ring = np.where(E["ring"])[0]
    s_ = (3 * ring[:, None] + np.arange(3)).ravel()
    add(sp.csr_matrix((np.ones(len(s_)), (np.arange(len(s_)), s_)), shape=(len(s_), 3 * n)), u0[s_], HS.PIN_SIGMA)
    top = int(np.argmax(V[:, 2]))
    add(sp.csr_matrix(([1.0], ([0], [3 * top + 2])), shape=(1, 3 * n)), np.array([u0[3 * top + 2]]), 0.2)
    Jall = sp.vstack(blocks).tocsr() @ S
    b = np.concatenate(rhs)
    du = spl.spsolve((Jall.T @ Jall).tocsc(), Jall.T @ b)
    return U0 + (S @ du).reshape(-1, 3)


def prior_stats(pf, U):
    d, spread, wm, N = pf[:4]
    sel = wm > 0.5
    r = d[sel] - np.einsum("ij,ij->i", U[sel], N[sel])
    return {"n": int(sel.sum()), "rms_mm": round(float(np.sqrt(np.mean(r ** 2))), 2), "mean_mm": round(float(np.mean(r)), 2),
            "spread_rms_mm": round(float(np.sqrt(np.mean(spread[sel] ** 2))), 2)}


def _patch_hs():
    HS.WORK = WORK


def fit_main(rounds=3, inner=4):
    _patch_hs()
    os.makedirs(WORK, exist_ok=True)
    prior = dict(np.load(PRIOR))
    t_all = time.perf_counter()
    ref = HS.reference()
    work_target = os.path.join(WORK, "head-shape-r3.target")
    import shutil
    shutil.copyfile(TARGET_R2, work_target)
    log = []
    D_total, cams = None, None
    for rnd in range(rounds):
        t0 = time.perf_counter()
        rdir = os.path.join(WORK, f"round{rnd}")
        os.makedirs(rdir, exist_ok=True)
        if rnd == 0 and os.path.exists(DEV_R2):
            blend = DEV_R2
        else:
            build_dev(work_target, DEV_R3, f"round{rnd}")
            blend = DEV_R3
        if cams is None:
            E = HS.export(rdir, blend, {"views": {}})
            cams = HS.initial_cams(E, ref, HS.correspondences(E, None, {"views": {}}, rdir, ref)["hero"])
            nuis = np.zeros(5)
        # head_shape.refresh, recording the new mesh's errors through the previous round's cameras first
        E = HS.export(rdir, blend, cams)
        corr = HS.correspondences(E, None, cams, rdir, ref)
        before_old_cams = HS.view_errors(E, corr, cams, nuis, np.zeros_like(E["V_rest"])) if rnd else None
        if rnd == 0 or not FREEZE_CAMS:
            for _ in range(2):
                cams, nuis = HS.solve_cams(E, corr, cams, nuis, np.zeros_like(E["V_rest"]))
            E = HS.export(rdir, blend, cams)
            corr = HS.correspondences(E, None, cams, rdir, ref)
        if D_total is None:
            D_total = HS.read_target(len(E["V_all"]), TARGET_R2)
        maps = HS.build_maps(E)
        pf = prior_field(E, prior)
        U = np.zeros_like(E["V_rest"])
        before = HS.view_errors(E, corr, cams, nuis, U)
        before["prior"] = prior_stats(pf, U)
        def solve_cams(U):
            c2, n2 = HS.solve_cams(E, corr, cams, nuis, U)
            return (cams if rnd and FREEZE_CAMS else c2), n2       # frozen: only the hero nuisance moves
        for k in range(inner):
            cams, nuis = solve_cams(U)
            U = solve_U_r3(E, corr, cams, nuis, U, maps, pf)
        cams, nuis = solve_cams(U)
        after = HS.view_errors(E, corr, cams, nuis, U)
        after["prior"] = prior_stats(pf, U)
        D_total = D_total + HS.extend(E, U)
        HS.write_target(D_total, work_target, note=f"head round 3 (head_shape_r3.py, Hunyuan3D 2 form prior), round {rnd}")
        with open(os.path.join(WORK, "cams.json"), "w") as f:
            json.dump(cams, f, indent=1)
        un = np.linalg.norm(U, axis=1)
        rec = {"round": rnd, "before_old_cams": before_old_cams, "before": before, "after": after, "cams": cams, "nuisance": [round(float(a), 2) for a in nuis],
               "U_mm": {"max": round(float(un.max()), 2), "p95": round(float(np.percentile(un, 95)), 2)},
               "seconds": round(time.perf_counter() - t0, 1)}
        log.append(rec)
        if before_old_cams:
            say(f"round {rnd} through round {rnd - 1}'s cameras: " + json.dumps({k: before_old_cams.get(k) for k in
                ("front", "threequarter", "threequarter_silhouette", "hero_silhouette", "profile")}, default=str))
        say(f"round {rnd}: U max {rec['U_mm']['max']} p95 {rec['U_mm']['p95']} mm; prior {before['prior']} -> {after['prior']}; "
            f"hero {before['hero_with_nuisance']['rms_px']} -> {after['hero_with_nuisance']['rms_px']} px; "
            + "; ".join(f"{v} {before[v]['rms_mm']} -> {after[v]['rms_mm']} mm" for v in cams["views"] if v in before and v != "profile")
            + (f"; profile {before['profile']['rms_mm']} -> {after['profile']['rms_mm']} mm" if "profile" in after else "")
            + f"; sil hero {before.get('hero_silhouette')} -> {after.get('hero_silhouette')}"
            + f", 3q {before.get('threequarter_silhouette')} -> {after.get('threequarter_silhouette')}")
        with open(os.path.join(WORK, "fit_log.json"), "w") as f:
            json.dump(log, f, indent=1, default=float)
    shutil.copyfile(work_target, TARGET_R3)
    build_dev(TARGET_R3, DEV_R3, "final")
    D2 = HS.read_target(len(E["V_all"]), TARGET_R2)
    dd = np.linalg.norm(D_total - D2, axis=1)
    rec = {"note": "Head round 3: head-shape-r3.target, scripts/parts/head_shape_r3.py --fit (head.md §10): round 2's "
                   "transfer continued with the Hunyuan3D 2 (mv 50-step) form prior. To use it, copy it over "
                   "head-shape.target.",
           "target": os.path.relpath(TARGET_R3, PROJECT).replace("\\", "/"),
           "starts_from": os.path.relpath(TARGET_R2, PROJECT).replace("\\", "/"),
           "seeds": [str(s) for s in prior["seeds"]],
           "displacement_mm": {"max": round(float(np.linalg.norm(D_total, axis=1).max()), 2),
                               "change_from_r2_max": round(float(dd.max()), 2),
                               "change_from_r2_p95": round(float(np.percentile(dd[dd > 1e-3], 95)), 2)},
           "sigmas": {"prior_mm": PRIOR_SIGMA_MM, "prior_clip_mm": PRIOR_CLIP_MM, "lap_mm": LAP_SIGMA,
                      "bend_mm": HS.BEND_SIGMA, "lowpass_steps": LOWPASS_STEPS, "highpass_steps": HIGHPASS_STEPS,
                      "detail_steps": DETAIL_STEPS, "freeze_cams": FREEZE_CAMS},
           "base": f"scripts/stages/base.py at {COMMIT_BASE} (stature 1835), pose cache/head_r2/hero_pose_r1.json",
           "cams": cams, "log": log, "seconds": round(time.perf_counter() - t_all, 1)}
    with open(JSON_R3, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=1, default=float)
    return log


def _overlays(corr, ref, rdir, cams, tag):
    from PIL import Image, ImageDraw
    os.makedirs(RENDERS, exist_ok=True)
    pairs = [("hero", HS.REF_CROP, os.path.join(rdir, "model_hero.png"), lambda p: (p - np.array([715.0, 30.0])) * 5.0)]
    for v in cams["views"]:
        if v != "profile":
            pairs.append((v, os.path.join(HS.R001, HS.VIEWS[v][0]), os.path.join(rdir, f"model_{v}.png"), lambda p: p))
    for v, rp, mp_, tf in pairs:
        if v not in corr:
            continue
        im = Image.open(rp).convert("RGB")
        mo = Image.fromarray(HS.load_rgb(mp_)).resize(im.size)
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
        sheet.save(os.path.join(RENDERS, f"landmarks_{tag}_{v}.png"))


def check_main(tag):
    _patch_hs()
    HS.overlays = _overlays
    blend = {"r2": DEV_R2, "r3": DEV_R3}.get(tag, tag)
    if tag == "r2" and not os.path.exists(DEV_R2):
        build_dev(TARGET_R2, DEV_R2, "r2")
    out = HS.check_main(tag, blend)
    if os.path.exists(PRIOR):
        prior = dict(np.load(PRIOR))
        E = dict(np.load(os.path.join(WORK, f"check_{tag}", "export.npz")))
        pf = prior_field(E, prior)
        out["prior"] = prior_stats(pf, np.zeros_like(E["V_rest"]))
        with open(os.path.join(WORK, f"check_{tag}.json"), "w") as f:
            json.dump(out, f, indent=1, default=float)
        say(tag, "prior", out["prior"])
    return out


def check_fixed_main(tag, cams_json):
    """The outline and landmark numbers of a dev base through given cameras (round 2's, as its check solved them),
    only the hero nuisance re-solved: what the shape change does with the views held (check_main re-solves every
    camera on MediaPipe, whose reading moves with the shading)."""
    _patch_hs()
    blend = {"r2": DEV_R2, "r3": DEV_R3}.get(tag, tag)
    ref = HS.reference()
    cams = json.load(open(cams_json))
    rdir = os.path.join(WORK, f"checkfixed_{tag}")
    E = HS.export(rdir, blend, cams)
    corr = HS.correspondences(E, None, cams, rdir, ref)
    U = np.zeros_like(E["V_rest"])
    nuis = np.zeros(5)
    for _ in range(2):
        _, nuis = HS.solve_cams(E, corr, cams, nuis, U)
    out = HS.view_errors(E, corr, cams, nuis, U)
    out["dims_mm"] = HS.dims(E)
    out["cams"] = os.path.relpath(cams_json, PROJECT).replace("\\", "/")
    if os.path.exists(PRIOR):
        out["prior"] = prior_stats(prior_field(E, dict(np.load(PRIOR))), U)
    with open(os.path.join(WORK, f"checkfixed_{tag}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    say("fixed cameras", tag, json.dumps(out, default=float))
    return out


def render_main(tag, samples):
    blend = {"r2": DEV_R2, "r3": DEV_R3}[tag]
    dt = blender(["--render-dev", blend, f"{tag}_", str(samples)], os.path.join(WORK, f"render_{tag}.log"))
    say(f"renders {tag} in {dt:.0f} s")


def mask_debug(rdir, meta, E, mask):
    """renders/head/r3/prior_mask.png: the mask on MPFB's front render (red = 1)."""
    from PIL import Image, ImageDraw
    os.makedirs(RENDERS, exist_ok=True)
    m = meta["mpfb"]
    im = Image.open(os.path.join(rdir, "mpfb_front.png")).convert("RGBA")
    bg = Image.new("RGBA", im.size, (60, 60, 60, 255))
    bg.alpha_composite(im)
    d = ImageDraw.Draw(bg)
    V = E["V_rest"]
    N = vertex_normals(V, E["tris"])
    s = m["px"] / (m["S"] * 1000)
    for v in np.where(N[:, 1] < -0.1)[0]:
        x = (V[v, 0] - m["cx"] * 1000) * s + m["px"] / 2
        y = m["px"] / 2 - (V[v, 2] - m["cz"] * 1000) * s
        k = float(mask[v])
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(int(255 * k), int(80 * (1 - k)), int(255 * (1 - k)), 255))
    bg.convert("RGB").save(os.path.join(RENDERS, "prior_mask.png"))


def sheets_main():
    """r2 | r3 sheets of the rest views and the hero (clay and Cycles), with the references."""
    from PIL import Image
    os.makedirs(RENDERS, exist_ok=True)

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
    for mode in ("clay", "cycles"):
        for v in ("front", "side", "side_L", "threequarter"):
            a, b = os.path.join(RENDERS, f"r2_rest_{v}_{mode}.png"), os.path.join(RENDERS, f"r3_rest_{v}_{mode}.png")
            if os.path.exists(a) and os.path.exists(b):
                p = os.path.join(RENDERS, f"cmp_rest_{v}_{mode}.png")
                row([a, b]).save(p)
                made.append(p)
    for k in ("hero_head_face", "hero_head_face_cycles"):
        a, b = os.path.join(RENDERS, f"r2_{k}.png"), os.path.join(RENDERS, f"r3_{k}.png")
        if os.path.exists(a) and os.path.exists(b):
            p = os.path.join(RENDERS, f"cmp_{k}.png")
            row([HS.REF_CROP, a, b]).save(p)
            made.append(p)
    for v in ("front", "threequarter", "profile"):
        a, b = os.path.join(RENDERS, f"r2_r001_{v}.png"), os.path.join(RENDERS, f"r3_r001_{v}.png")
        if os.path.exists(a) and os.path.exists(b):
            p = os.path.join(RENDERS, f"cmp_r001_{v}.png")
            row([os.path.join(HS.R001, HS.VIEWS[v][0]), a, b]).save(p)
            made.append(p)
    say("sheets", [os.path.basename(p) for p in made])


def main():
    if HS.in_blender():
        a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        if a and a[0] == "--build-dev":
            return bl_build_dev(a[1] or None, a[2])
        if a and a[0] == "--prior-render":
            bl_prior_render(a[1], a[2], a[3:])
            return 0
        if a and a[0] == "--render-dev":
            return bl_render_dev(a[1], a[2], int(a[3]))
        raise SystemExit("head_shape_r3.py in Blender: --build-dev | --prior-render | --render-dev")
    ap = argparse.ArgumentParser()
    ap.add_argument("--prior", action="store_true")
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--check", default=None)
    ap.add_argument("--check-fixed", default=None, help="r2|r3: through round 2's cameras (cache/head_r3/check_r2/cams.json)")
    ap.add_argument("--render", default=None)
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--sheets", action="store_true")
    args = ap.parse_args()
    if args.prior:
        prior_main()
    if args.fit:
        fit_main(args.rounds)
    if args.check:
        check_main(args.check)
    if args.check_fixed:
        check_fixed_main(args.check_fixed, os.path.join(WORK, "check_r2", "cams.json"))
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
