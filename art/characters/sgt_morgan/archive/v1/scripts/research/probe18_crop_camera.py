"""Probe for spec 18 §2.4 D1, D3 and §3.2: linear target model exactness, splat silhouette, equivalent crop camera
against render borders, Workbench anti-aliasing cost.
Run: blender -b --python scripts/research/probe18_crop_camera.py -- [out_dir] [mpfb_default.blend]
"""
import bpy, time, json, sys, os, math
import numpy as np

import pathlib
PROJECT = pathlib.Path(__file__).resolve().parents[2]
_args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = _args[0] if _args else str(PROJECT / "renders/research/probe18")
BLEND = _args[1] if len(_args) > 1 else str(PROJECT / "renders/research/mpfb_default.blend")   # made by mpfb_build_v2.py
os.makedirs(OUT, exist_ok=True)
R = {}
bpy.ops.wm.open_mainfile(filepath=BLEND)
base = bpy.data.objects["Human"]
kb = base.data.shape_keys.key_blocks
dg = bpy.context.evaluated_depsgraph_get()
n = len(base.data.vertices)

# (a) linear model exactness: modifiers off, random key weights, compare with the evaluated mesh
mods = [(m, m.show_viewport) for m in base.modifiers]
for m, _ in mods:
    m.show_viewport = False
R["keys"] = [(k.name, k.relative_key.name, k.vertex_group, k.mute, round(k.value, 4)) for k in kb]
basis = np.empty(n * 3, np.float32); kb[0].data.foreach_get("co", basis); basis = basis.reshape(-1, 3)
D = []
for k in kb[1:]:
    a = np.empty(n * 3, np.float32); k.data.foreach_get("co", a); D.append(a.reshape(-1, 3) - basis)
D = np.stack(D)
rng = np.random.default_rng(1)
errs = []
for trial in range(3):
    w = rng.uniform(0, 1, len(kb) - 1).astype(np.float32)
    for k, wi in zip(kb[1:], w):
        k.value = float(wi)
    dg.update()
    ev = base.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); ev.to_mesh_clear()
    pred = basis + np.tensordot(w, D, axes=1)
    errs.append(float(np.abs(pred - co.reshape(-1, 3)).max()) * 1e3)
R["linear_model_max_err_mm"] = [round(e, 5) for e in errs]
for k, (nm, rel, vg, mu, v) in zip(kb, R["keys"]):
    k.value = v
for m, s in mods:
    m.show_viewport = s
dg.update()

# body without the clothing masks, for a whole-figure silhouette: keep Armature + Hide helpers only
for m in base.modifiers:
    if m.name.startswith("Delete."):
        m.show_viewport = False
dg.update()
ev = base.evaluated_get(dg); me = ev.to_mesh()
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
me.calc_loop_triangles()
tris = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", tris); tris = tris.reshape(-1, 3)
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
ev.to_mesh_clear()
M = np.array(base.matrix_world)
co_w = (co @ M[:3, :3].T + M[:3, 3]).astype(np.float64)
R["body_eval_verts"] = int(co.shape[0]); R["body_tris"] = int(tris.shape[0])
R["body_stature_mm"] = round(float(co_w[:, 2].max() - co_w[:, 2].min()) * 1e3, 1)

TH = math.radians(3.9); F = 2136.4; C = np.array([0.0, -4.5, 0.6])
def project(P):
    d = (P[:, 1] - C[1]) * math.cos(TH) + (P[:, 2] - C[2]) * math.sin(TH)
    v = -(P[:, 1] - C[1]) * math.sin(TH) + (P[:, 2] - C[2]) * math.cos(TH)
    return np.stack([836 + F * (P[:, 0] - C[0]) / d, 470.5 - F * v / d], 1)

# (b) splat silhouette: barycentric lattice samples, count by projected area, then a 3x3 closing
_lat = {}
def lattice(L):
    if L not in _lat:
        i, j = np.mgrid[0:L + 1, 0:L + 1]
        sel = (i + j) <= L
        _lat[L] = np.stack([i[sel], j[sel]], 1) / max(L, 1)
    return _lat[L]

def splat(px, tris, W, H, scale=1.0, x0=0.0, y0=0.0):
    P = (px[tris] - np.array([x0, y0])) * scale
    e1 = P[:, 1] - P[:, 0]; e2 = P[:, 2] - P[:, 0]
    edge = np.maximum(np.linalg.norm(e1, axis=1), np.maximum(np.linalg.norm(e2, axis=1), np.linalg.norm(P[:, 2] - P[:, 1], axis=1)))
    L = np.clip(np.ceil(edge / 0.7).astype(int), 1, 512)       # lattice step <= 0.7 px along every edge
    mask = np.zeros((H, W), bool)
    for l in np.unique(L):
        sel = L == l
        ab = lattice(int(l))                                       # (m, 2) barycentric (a, b)
        S = P[sel, 0][:, None, :] + ab[None, :, 0:1] * e1[sel][:, None, :] + ab[None, :, 1:2] * e2[sel][:, None, :]
        X = S[..., 0].astype(np.int64); Y = S[..., 1].astype(np.int64)
        ok = (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
        mask[Y[ok], X[ok]] = True
    # 3x3 closing (dilate then erode) to fill sub-pixel cracks
    d = mask.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            d |= np.roll(np.roll(mask, dy, 0), dx, 1)
    e = d.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            e &= np.roll(np.roll(d, dy, 0), dx, 1)
    return e

t = time.time(); px = project(co_w); R["project_body_ms"] = round((time.time() - t) * 1e3, 2)
for name, args in (("full_x1", (1672, 941)), ("soldier_x1", (440, 915, 1.0, 580, 20)), ("soldier_x2", (880, 1830, 2.0, 580, 20))):
    t = time.time(); m = splat(px, tris, *args); R[f"splat_{name}_ms"] = round((time.time() - t) * 1e3, 1)
    if name == "full_x1":
        mfull = m
R["splat_full_px"] = int(mfull.sum())
np.save(os.path.join(OUT, "splat_full.npy"), mfull)

# girths on the whole body (tape = convex hull perimeter of the plane section)
def hull_perimeter(pts):
    pts = np.unique(np.round(pts, 6), axis=0)
    if len(pts) < 3:
        return 0.0
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]
    def half(P):
        h = []
        for p in P:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(p)
        return h
    Hh = np.array(half(pts)[:-1] + half(pts[::-1])[:-1])
    return float(np.linalg.norm(Hh - np.roll(Hh, -1, 0), axis=1).sum())
def girth(z, xsign=None):
    s = co_w[:, 2] - z
    e = E[(s[E[:, 0]] * s[E[:, 1]]) < 0]
    t_ = s[e[:, 0]] / (s[e[:, 0]] - s[e[:, 1]])
    P = co_w[e[:, 0]] + (co_w[e[:, 1]] - co_w[e[:, 0]]) * t_[:, None]
    if xsign is not None:
        P = P[np.sign(P[:, 0]) == xsign]
    return hull_perimeter(P[:, :2])
t = time.time()
R["girths_mm"] = {"chest_z1300": round(girth(1.30) * 1e3, 1), "waist_z1050": round(girth(1.05) * 1e3, 1),
                  "thigh_L_z0700": round(girth(0.70, 1) * 1e3, 1), "calf_L_z0350": round(girth(0.35, 1) * 1e3, 1)}
R["girth_4_slices_ms"] = round((time.time() - t) * 1e3, 2)
for m in base.modifiers:
    m.show_viewport = True
dg.update()

# (c) equivalent crop camera versus render border, Workbench, head box (715,30)-(885,200) at x2
sc = bpy.context.scene; r = sc.render
cam = bpy.data.cameras.new("Scene.Cam.Hero"); cob = bpy.data.objects.new("Scene.Cam.Hero", cam)
sc.collection.objects.link(cob); sc.camera = cob
cob.location = (0.0, -4.5, 0.6); cob.rotation_euler = (math.radians(93.9), 0.0, 0.0)
cam.lens = 46.0; cam.sensor_width = 36.0; cam.sensor_fit = "HORIZONTAL"
r.engine = "BLENDER_WORKBENCH"; r.image_settings.file_format = "PNG"
shd = sc.display.shading; shd.light = "MATCAP"; shd.color_type = "SINGLE"; shd.show_cavity = True; shd.cavity_type = "BOTH"
def hero_reset():
    cam.lens = 46.0; cam.shift_x = cam.shift_y = 0.0
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1672, 941, 100; r.use_border = False
def set_border(x0, y0, x1, y1, s):
    hero_reset(); r.use_border = True; r.use_crop_to_border = True
    r.border_min_x, r.border_max_x = x0 / 1672, x1 / 1672
    r.border_min_y, r.border_max_y = (941 - y1) / 941, (941 - y0) / 941
    r.resolution_percentage = int(100 * s)
def set_equiv(x0, y0, x1, y1, s):
    hero_reset()
    w, h = x1 - x0, y1 - y0
    cam.lens = 46.0 * 1672 / w                     # same pixel pitch on a 36 mm sensor, horizontal fit
    unit = w                                       # HORIZONTAL fit: shift is in units of the render width
    cam.shift_x = ((x0 + x1) / 2 - 836) / unit
    cam.shift_y = (470.5 - (y0 + y1) / 2) / unit
    r.resolution_x, r.resolution_y = int(round(w * s)), int(round(h * s))
timing = {}
def render(path):
    r.filepath = path; t = time.time(); bpy.ops.render.render(write_still=True); return round(time.time() - t, 3)
sc.display.render_aa = "8"
render(os.path.join(OUT, "warmup.png"))
set_border(715, 30, 885, 200, 2); timing["head_border_x2_aa8"] = render(os.path.join(OUT, "head_border_x2.png"))
set_equiv(715, 30, 885, 200, 2); timing["head_equiv_x2_aa8"] = render(os.path.join(OUT, "head_equiv_x2.png"))
set_equiv(715, 30, 885, 200, 5); timing["head_equiv_x5_aa8"] = render(os.path.join(OUT, "head_equiv_x5.png"))
set_equiv(580, 20, 1020, 935, 2); timing["soldier_equiv_x2_aa8"] = render(os.path.join(OUT, "soldier_equiv_x2.png"))
set_border(580, 20, 1020, 935, 2); timing["soldier_border_x2_aa8"] = render(os.path.join(OUT, "soldier_border_x2.png"))
for aa in ("OFF", "FXAA", "5", "8", "16"):
    sc.display.render_aa = aa
    set_equiv(580, 20, 1020, 935, 1); timing[f"soldier_equiv_x1_aa{aa}"] = render(os.path.join(OUT, f"soldier_equiv_x1_{aa}.png"))
sc.display.render_aa = "8"
hero_reset(); timing["full_x1_aa8"] = render(os.path.join(OUT, "full_x1.png"))
R["workbench_s"] = timing
with open(os.path.join(OUT, "probe2_results.json"), "w") as f:
    json.dump(R, f, indent=1)
print("PROBE2", json.dumps(R))
