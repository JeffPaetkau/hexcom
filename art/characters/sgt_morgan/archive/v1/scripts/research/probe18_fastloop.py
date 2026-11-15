"""Probe for spec 18 §3.2: cost of the fast-loop primitives on the MPFB default body.

Run: blender -b --python scripts/research/probe18_fastloop.py -- [out_dir] [mpfb_default.blend]
Measures: open_mainfile; shape-key change + depsgraph evaluation + vertex read-back;
building a linear target model from shape-key data and evaluating it in numpy;
projection through the hero camera; numpy silhouette rasterisation; girth slices;
Workbench matcap+cavity renders (cold and warm) at two reference borders.
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
t = time.time()
bpy.ops.wm.open_mainfile(filepath=BLEND)
R["open_mainfile_s"] = round(time.time() - t, 3)

meshes = [o for o in bpy.data.objects if o.type == "MESH"]
R["objects"] = [(o.name, o.type, [m.type for m in o.modifiers]) for o in bpy.data.objects][:40]
base = max(meshes, key=lambda o: (len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0, len(o.data.vertices)))
kb = base.data.shape_keys.key_blocks
R["base"] = {"name": base.name, "verts": len(base.data.vertices), "polys": len(base.data.polygons),
             "shape_keys": len(kb), "modifiers": [(m.name, m.type, m.show_viewport) for m in base.modifiers]}

dg = bpy.context.evaluated_depsgraph_get()

def read_eval(ob):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    me.loop_triangles.foreach_get  # touch
    ev.to_mesh_clear()
    return co.reshape(-1, 3)

# 1. depsgraph evaluation after a shape-key change
key = kb[min(1, len(kb) - 1)]
v0 = key.value
ts = []
for i in range(15):
    t = time.time()
    key.value = v0 + 0.01 * (i % 3)
    dg.update()
    co = read_eval(base)
    ts.append(time.time() - t)
key.value = v0
dg.update()
R["depsgraph_eval_ms"] = {"first": round(ts[0] * 1e3, 1), "median": round(float(np.median(ts[1:])) * 1e3, 1),
                          "n_out_verts": int(co.shape[0])}

# 1b. same with every modifier disabled in the viewport (pure shape-key mix)
saved = [(m, m.show_viewport) for m in base.modifiers]
for m, _ in saved:
    m.show_viewport = False
dg.update()
ts = []
for i in range(15):
    t = time.time()
    key.value = v0 + 0.01 * (i % 3)
    dg.update()
    co_nomod = read_eval(base)
    ts.append(time.time() - t)
key.value = v0
for m, s in saved:
    m.show_viewport = s
dg.update()
R["depsgraph_eval_nomod_ms"] = {"median": round(float(np.median(ts[1:])) * 1e3, 1), "n_out_verts": int(co_nomod.shape[0])}

# 2. linear target model: read every key's coordinates once, then evaluate in numpy
n = len(base.data.vertices)
t = time.time()
basis = np.empty(n * 3, np.float32); kb[0].data.foreach_get("co", basis); basis = basis.reshape(-1, 3)
deltas = []
for k in kb[1:]:
    a = np.empty(n * 3, np.float32); k.data.foreach_get("co", a)
    deltas.append(a.reshape(-1, 3) - basis)
D = np.stack(deltas) if deltas else np.zeros((0, n, 3), np.float32)
R["linear_model_build_s"] = round(time.time() - t, 3)
R["linear_model_keys"] = int(D.shape[0])
w = np.array([k.value for k in kb[1:]], np.float32)
lm_idx = np.linspace(0, n - 1, 120).astype(int)            # 120 stand-in landmark vertices
Dl = D[:, lm_idx, :].reshape(D.shape[0], -1)                # (K, 360)
t = time.time()
for i in range(1000):
    pred = basis[lm_idx].reshape(-1) + w @ Dl
R["linear_model_eval_us"] = round((time.time() - t) / 1000 * 1e6, 2)
# full-mesh evaluation in numpy, for comparison
t = time.time()
for i in range(10):
    full = basis + np.tensordot(w, D, axes=1)
R["linear_model_full_mesh_ms"] = round((time.time() - t) / 10 * 1e3, 2)
R["linear_vs_depsgraph_max_mm"] = round(float(np.abs(full - co_nomod[:n]).max()) * 1e3, 4) if co_nomod.shape[0] >= n else None

# 3. projection through the hero camera (spec 17 camproj)
TH = math.radians(3.9); F = 2136.4; C = np.array([0.0, -4.5, 0.6])
def project(P):
    d = (P[:, 1] - C[1]) * math.cos(TH) + (P[:, 2] - C[2]) * math.sin(TH)
    v = -(P[:, 1] - C[1]) * math.sin(TH) + (P[:, 2] - C[2]) * math.cos(TH)
    return np.stack([836 + F * (P[:, 0] - C[0]) / d, 470.5 - F * v / d], 1)

ev = base.evaluated_get(dg); me = ev.to_mesh()
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
me.calc_loop_triangles()
tris = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", tris); tris = tris.reshape(-1, 3)
ev.to_mesh_clear()
M = np.array(base.matrix_world)
co_w = co @ M[:3, :3].T + M[:3, 3]
t = time.time()
px = project(co_w.astype(np.float64))
R["project_ms"] = round((time.time() - t) * 1e3, 3)
R["n_tris"] = int(tris.shape[0])

def raster(px, tris, W, H, scale=1.0, x0=0.0, y0=0.0):
    P = (px[tris] - np.array([x0, y0])) * scale          # (T,3,2) in output pixels
    mn = np.floor(P.min(1)).astype(np.int64); mx = np.ceil(P.max(1)).astype(np.int64)
    size = np.maximum((mx - mn).max(1), 1)
    mask = np.zeros((H, W), bool)
    a, b, c = P[:, 0], P[:, 1], P[:, 2]
    k = 1
    while True:
        sel = (size <= k) & (size > k // 2) if k > 1 else (size <= 1)
        if sel.any():
            gy, gx = np.mgrid[0:k + 1, 0:k + 1]
            off = np.stack([gx.ravel(), gy.ravel()], 1) + 0.5          # pixel centres
            S = mn[sel][:, None, :] + off[None]                          # (Tb, m, 2)
            A, B, Cc = a[sel][:, None], b[sel][:, None], c[sel][:, None]
            def e(p, q):
                return (q[..., 0] - p[..., 0]) * (S[..., 1] - p[..., 1]) - (q[..., 1] - p[..., 1]) * (S[..., 0] - p[..., 0])
            e0, e1, e2 = e(A, B), e(B, Cc), e(Cc, A)
            ins = ((e0 >= 0) & (e1 >= 0) & (e2 >= 0)) | ((e0 <= 0) & (e1 <= 0) & (e2 <= 0))
            X = np.floor(S[..., 0]).astype(np.int64); Y = np.floor(S[..., 1]).astype(np.int64)
            ok = ins & (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
            mask[Y[ok], X[ok]] = True
        if k >= size.max():
            break
        k *= 2
    return mask

t = time.time(); m_full = raster(px, tris, 1672, 941); R["raster_full_frame_ms"] = round((time.time() - t) * 1e3, 1)
# the crop_soldier_full box (580,20)-(1020,935) at x2 = 880 x 1830
t = time.time(); m_crop = raster(px, tris, 880, 1830, scale=2.0, x0=580, y0=20); R["raster_soldier_crop_x2_ms"] = round((time.time() - t) * 1e3, 1)
R["silhouette_px_full"] = int(m_full.sum())
ys, xs = np.nonzero(m_full)
R["silhouette_bbox_full"] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if xs.size else None
sh = np.roll(m_crop, 3, axis=1)
t = time.time(); iou = (m_crop & sh).sum() / max((m_crop | sh).sum(), 1); R["iou_ms"] = round((time.time() - t) * 1e3, 2)
np.save(os.path.join(OUT, "mask_full.npy"), m_full)

# 4. girths: convex-hull perimeter of the plane section (tape-measure girth)
E = np.empty(len(base.data.edges) * 2, np.int32)
ev = base.evaluated_get(dg); me = ev.to_mesh(); E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2); ev.to_mesh_clear()

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
    H = np.array(half(pts)[:-1] + half(pts[::-1])[:-1])
    return float(np.linalg.norm(H - np.roll(H, -1, 0), axis=1).sum())

def girth(co_w, E, z, xsign=None):
    s = co_w[:, 2] - z
    cross = (s[E[:, 0]] * s[E[:, 1]]) < 0
    e = E[cross]
    tpar = s[e[:, 0]] / (s[e[:, 0]] - s[e[:, 1]])
    P = co_w[e[:, 0]] + (co_w[e[:, 1]] - co_w[e[:, 0]]) * tpar[:, None]
    if xsign is not None:
        P = P[np.sign(P[:, 0]) == xsign]
    return hull_perimeter(P[:, :2])

t = time.time()
g = {f"z{int(z*1000)}": round(girth(co_w, E, z) * 1e3, 1) for z in (1.00, 1.10, 1.25, 1.35)}
g["thigh_L_z700"] = round(girth(co_w, E, 0.70, xsign=1) * 1e3, 1)
R["girth_5_slices_ms"] = round((time.time() - t) * 1e3, 1)
R["girths_mm_mpfb_default"] = g
R["stature_mm_mpfb_default"] = round(float(co_w[:, 2].max() - co_w[:, 2].min()) * 1e3, 1)

# 5. Workbench form renders (matcap + cavity), hero camera, two borders
sc = bpy.context.scene
cam = bpy.data.cameras.new("Scene.Cam.Hero"); cob = bpy.data.objects.new("Scene.Cam.Hero", cam)
sc.collection.objects.link(cob); sc.camera = cob
cob.location = (0.0, -4.5, 0.6); cob.rotation_euler = (math.radians(93.9), 0.0, 0.0)
cam.lens = 46.0; cam.sensor_width = 36.0; cam.sensor_fit = "HORIZONTAL"
r = sc.render
r.engine = "BLENDER_WORKBENCH"
r.resolution_x, r.resolution_y = 1672, 941
sh = sc.display.shading
sh.light = "MATCAP"; sh.color_type = "SINGLE"; sh.show_cavity = True; sh.cavity_type = "BOTH"
sc.display.render_aa = "8"
r.image_settings.file_format = "PNG"
def border(x0, y0, x1, y1, scale):
    r.use_border = True; r.use_crop_to_border = True
    r.border_min_x, r.border_max_x = x0 / 1672, x1 / 1672
    r.border_min_y, r.border_max_y = (941 - y1) / 941, (941 - y0) / 941
    r.resolution_percentage = int(100 * scale)
wb = []
for i, (name, box, scale) in enumerate([("soldier_x2", (580, 20, 1020, 935), 2), ("soldier_x2", (580, 20, 1020, 935), 2),
                                        ("head_x5", (715, 30, 885, 200), 5), ("head_x5", (715, 30, 885, 200), 5),
                                        ("full_x1", (0, 0, 1672, 941), 1), ("soldier_x1", (580, 20, 1020, 935), 1)]):
    border(*box, scale)
    r.filepath = os.path.join(OUT, f"wb_{i}_{name}.png")
    t = time.time(); bpy.ops.render.render(write_still=True); wb.append((name, round(time.time() - t, 3)))
R["workbench_s"] = wb
r.use_border = False; r.resolution_percentage = 100

# 6. variant loop: 6 shape-key values -> render each (contact-sheet producer)
border(580, 20, 1020, 935, 1)
t = time.time()
for i in range(6):
    key.value = v0 + 0.1 * i
    r.filepath = os.path.join(OUT, f"var_{i}.png")
    bpy.ops.render.render(write_still=True)
key.value = v0
R["variants_6_workbench_s"] = round(time.time() - t, 2)

# 7. save a cache .blend and re-open it
p = os.path.join(OUT, "cache_probe.blend")
t = time.time(); bpy.ops.wm.save_as_mainfile(filepath=p, compress=False); R["save_blend_s"] = round(time.time() - t, 3)
R["blend_bytes"] = os.path.getsize(p)
t = time.time(); bpy.ops.wm.open_mainfile(filepath=p); R["reopen_blend_s"] = round(time.time() - t, 3)

with open(os.path.join(OUT, "probe_results.json"), "w") as f:
    json.dump(R, f, indent=1)
print("PROBE_RESULTS", json.dumps(R))
