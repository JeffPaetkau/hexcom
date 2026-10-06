"""Install CharMorph (legacy add-on, bl_info blender 3.3) into Blender 4.5 headless, import its
default male (mb_male) and render the face.
Usage: blender -b --python charmorph_test.py -- <charmorph_src_dir> <out_dir> [samples] [render:0|1]
"""
import bpy, sys, os, time, traceback, shutil
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = argv[0]
OUT = argv[1]
SAMPLES = int(argv[2]) if len(argv) > 2 else 32
DO_RENDER = (argv[3] == "1") if len(argv) > 3 else True
os.makedirs(OUT, exist_ok=True)
T0 = time.time()

addons_dir = bpy.utils.user_resource('SCRIPTS', path="addons", create=True)
dst = os.path.join(addons_dir, "CharMorph")
print("legacy addons dir:", addons_dir)
if not os.path.exists(dst):
    os.symlink(SRC, dst)   # symlink so the 734 MB data dir is not copied
    print("symlinked", SRC, "->", dst)
# make Blender see the new module (the addons dir may have been created just now -> not on sys.path yet)
bpy.utils.refresh_script_paths()
if addons_dir not in sys.path:
    sys.path.append(addons_dir)
import addon_utils
addon_utils.modules_refresh()

try:
    bpy.ops.preferences.addon_enable(module="CharMorph")
    print("CharMorph enabled; registered modules with charmorph:", [a.module for a in bpy.context.preferences.addons if "harmorph" in a.module.lower()])
except Exception:
    print("!! addon_enable failed:"); traceback.print_exc(); sys.exit(1)
print("[TIMING] enable %.1fs" % (time.time() - T0))

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

try:
    from CharMorph.lib.charlib import library
    print("library chars:", list(library.chars.keys()))
    ui = bpy.context.window_manager.charmorph_ui
    ui.base_model = "mb_male"
    print("ui props: use_sk=%s import_morphs=%s alt_topo=%s" % (ui.use_sk, ui.import_morphs, ui.alt_topo))
    t = time.time()
    res = bpy.ops.charmorph.import_char()
    print("import_char ->", res, "%.1fs" % (time.time() - t))
except Exception:
    print("!! import_char failed:"); traceback.print_exc()

objs = [(o.name, o.type, len(o.data.vertices) if o.type == 'MESH' else '') for o in bpy.data.objects]
print("objects:", objs)
char = next((o for o in bpy.data.objects if o.type == 'MESH' and ('mb_male' in o.name or 'male' in o.name.lower())), None)
if char is None:
    char = next((o for o in bpy.data.objects if o.type == 'MESH'), None)
print("char:", char.name if char else None,
      "shape keys:", len(char.data.shape_keys.key_blocks) if char and char.data.shape_keys else 0,
      "materials:", [m.name for m in char.data.materials] if char else None)

# try a couple of morphs through the morpher API
try:
    from CharMorph import common
    m = common.manager.morpher
    print("morpher:", type(m).__name__, "L1 (type) choices:", getattr(m.core, "L1", None) if hasattr(m, "core") else None)
    l2 = getattr(m.core, "morphs_l2", [])
    names = [getattr(x, "name", str(x)) for x in (l2 if isinstance(l2, (list, tuple)) else list(l2.keys()))]
    print("L2 morph count:", len(names), "sample:", names[:20])
    print("core attrs:", [a for a in dir(m.core) if not a.startswith("_")][:40])
except Exception:
    print("!! morpher introspection failed:"); traceback.print_exc()

if char is not None and DO_RENDER:
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ev = char.evaluated_get(dg); me = ev.to_mesh()
    ws = [ev.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear()
    zmin = min(w.z for w in ws); zmax = max(w.z for w in ws)
    ymin = min(w.y for w in ws)
    print("char bounds z[%.3f, %.3f] height %.3f m, ymin %.3f" % (zmin, zmax, zmax - zmin, ymin))
    head = Vector((0, 0, zmin + (zmax - zmin) * 0.93))
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True; scene.cycles.use_adaptive_sampling = True
    scene.view_settings.view_transform = 'AgX'
    world = scene.world or bpy.data.worlds.new("World"); scene.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.19, 0.21, 1); world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    def light(name, loc, e, s):
        ld = bpy.data.lights.new(name, 'AREA'); ld.energy = e; ld.size = s
        lo = bpy.data.objects.new(name, ld); scene.collection.objects.link(lo); lo.location = loc
        lo.rotation_euler = (head - lo.location).to_track_quat('-Z', 'Y').to_euler()
    light("Key", head + Vector((-1.4, -1.6, 0.7)), 500, 1.0); light("Fill", head + Vector((2.0, -1.8, -0.1)), 150, 2.5); light("Rim", head + Vector((0.8, 2.2, 0.6)), 350, 0.8)
    cd = bpy.data.cameras.new("Cam"); cd.lens = 85
    cam = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(cam)
    cam.location = head + Vector((-0.22, -0.55, 0.0))
    cam.rotation_euler = (head - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.render.filepath = os.path.join(OUT, "charmorph_face.png")
    t = time.time(); bpy.ops.render.render(write_still=True)
    print("[TIMING] render charmorph_face.png @%d spp: %.1fs" % (SAMPLES, time.time() - t))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "charmorph_test.blend"), compress=True)
print("[TIMING] TOTAL %.1fs" % (time.time() - T0))
