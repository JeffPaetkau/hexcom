"""Import each Poly Haven glTF model headlessly and report dimensions / poly counts / materials.
blender -b --python gltf_import_test.py -- <models_root>
"""
import bpy, sys, os, time, glob
root = sys.argv[sys.argv.index("--") + 1]
for d in sorted(os.listdir(root)):
    g = glob.glob(os.path.join(root, d, "*.gltf"))
    if not g: continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    t0 = time.time()
    try:
        bpy.ops.import_scene.gltf(filepath=g[0])
    except Exception as e:
        print(f"IMPORT FAIL {d}: {e!r}"); continue
    dt = time.time() - t0
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    verts = sum(len(o.data.vertices) for o in meshes)
    xs, ys, zs = [], [], []
    for o in meshes:
        for v in o.bound_box:
            w = o.matrix_world @ __import__("mathutils").Vector(v); xs.append(w.x); ys.append(w.y); zs.append(w.z)
    dims = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) if xs else (0, 0, 0)
    mats = sorted({m.name for o in meshes for m in o.data.materials if m})
    imgs = sorted(i.name for i in bpy.data.images if i.name != "Render Result")
    print(f"IMPORT OK {d}: {dt:.1f}s objects={len(meshes)} verts={verts} tris={tris} "
          f"dims_m=({dims[0]:.3f},{dims[1]:.3f},{dims[2]:.3f}) materials={mats} images={imgs}")
