"""Import every downloaded model (Poly Haven .gltf, TheBaseMesh .glb/.fbx/.obj) headlessly and report
import time, object/vert/tri counts, world-space bounding box in metres, materials and images.
Usage:  blender -b --python model_import_test.py -- <models_root> [out_json]
Run from OUTSIDE the models folder; paths are passed as arguments only.
"""
import bpy, sys, os, time, glob, json
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
root = argv[0]
out_json = argv[1] if len(argv) > 1 else None

files = []
for dirpath, _, names in os.walk(root):
    for n in sorted(names):
        if n.lower().endswith((".gltf", ".glb", ".fbx", ".obj")):
            files.append(os.path.join(dirpath, n))

report = []
for path in sorted(files):
    rel = os.path.relpath(path, root)
    ext = os.path.splitext(path)[1].lower()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    t0 = time.time()
    try:
        if ext in (".gltf", ".glb"):
            bpy.ops.import_scene.gltf(filepath=path)
        elif ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=path)
        elif ext == ".obj":
            bpy.ops.wm.obj_import(filepath=path)
    except Exception as e:
        print(f"IMPORT FAIL {rel}: {e!r}", flush=True)
        report.append({"file": rel, "ok": False, "error": repr(e)}); continue
    dt = time.time() - t0
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    verts = sum(len(o.data.vertices) for o in meshes)
    quads = sum(sum(1 for p in o.data.polygons if len(p.vertices) == 4) for o in meshes)
    ngons = sum(sum(1 for p in o.data.polygons if len(p.vertices) > 4) for o in meshes)
    xs, ys, zs = [], [], []
    for o in meshes:
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v); xs.append(w.x); ys.append(w.y); zs.append(w.z)
    dims = [round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3), round(max(zs) - min(zs), 3)] if xs else [0, 0, 0]
    mats = sorted({m.name for o in meshes for m in o.data.materials if m})
    imgs = sorted(i.name for i in bpy.data.images if i.name != "Render Result")
    uv = all(len(o.data.uv_layers) > 0 for o in meshes) if meshes else False
    r = {"file": rel, "ok": True, "seconds": round(dt, 2), "objects": len(meshes), "verts": verts, "tris": tris,
         "quads": quads, "ngons": ngons, "dims_m": dims, "has_uv": uv, "materials": mats, "images": imgs}
    report.append(r)
    print(f"IMPORT OK {rel}: {dt:.1f}s objs={len(meshes)} verts={verts} tris={tris} quads={quads} ngons={ngons} "
          f"dims_m={dims} uv={uv} mats={mats} imgs={imgs}", flush=True)

if out_json:
    with open(out_json, "w") as f:
        json.dump(report, f, indent=1)
    print("wrote", out_json)
