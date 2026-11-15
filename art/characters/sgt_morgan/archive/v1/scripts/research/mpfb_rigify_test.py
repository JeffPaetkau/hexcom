"""Test MPFB + Rigify headless: create human, add 'rigify.human' metarig, generate the rig.
Usage: blender -b --python mpfb_rigify_test.py -- <out_dir>
"""
import bpy, sys, os, time, traceback
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/home/user/sgt_morgan/renders/research"
T0 = time.time()
for m in ("bl_ext.user_default.mpfb", "rigify"):
    if m not in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_enable(module=m)
print("rigify enabled:", "rigify" in bpy.context.preferences.addons)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.systemservice import SystemService
from bl_ext.user_default.mpfb.services.rigservice import RigService
print("SystemService.check_for_rigify():", SystemService.check_for_rigify())
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
basemesh = HumanService.create_human()
basemesh.name = "Human"
t = time.time()
metarig = HumanService.add_builtin_rig(basemesh, "rigify.human", import_weights=True)
print("metarig:", metarig.name, len(metarig.data.bones), "bones, %.1fs" % (time.time() - t))
# generate
t = time.time()
try:
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = metarig
    metarig.select_set(True)
    res = bpy.ops.pose.rigify_generate()
    print("rigify_generate ->", res, "%.1fs" % (time.time() - t))
    rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    print("armatures:", [(o.name, len(o.data.bones)) for o in rigs])
    # MPFB helper that re-targets the mesh to the generated rig (if present)
    for fn in ("ensure_armature_modifier",):
        print("RigService has", fn, hasattr(RigService, fn))
    gen = next((o for o in rigs if o.name != metarig.name), None)
    if gen:
        print("generated rig:", gen.name, len(gen.data.bones), "bones; sample control bones:",
              [b.name for b in gen.data.bones if not b.name.startswith(("DEF-", "MCH-", "ORG-"))][:15])
except Exception:
    print("!! rigify_generate failed:"); traceback.print_exc()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "mpfb_rigify_test.blend"), compress=True)
print("[TIMING] TOTAL %.1fs" % (time.time() - T0))
