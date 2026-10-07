"""Render a proper face closeup from a saved MPFB build (.blend) — camera anchored on the EYES
object's evaluated world bounds (robust against the body's 'Delete.<asset>' MASK modifiers that
made the v1 face camera look at the crotch).
Usage: blender -b <build.blend> --python mpfb_face_render.py -- <out.png> [samples] [size] [view] [light_scale]
  view: 'threequarter' (default; camera on the soldier's RIGHT-front = -X, like ref/crop_head_face.png)
        or 'front'.
"""
import bpy, sys, os, time
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/home/user/sgt_morgan/renders/research/mpfb_v2_face.png"
SAMPLES = int(argv[1]) if len(argv) > 1 else 64
SIZE = int(argv[2]) if len(argv) > 2 else 1024
VIEW = argv[3] if len(argv) > 3 else "threequarter"
LIGHT_SCALE = float(argv[4]) if len(argv) > 4 else 1.0   # the saved lights were set for a full-body shot; 0.35 exposes a face correctly
T0 = time.time()

def eval_bounds(obj):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    ws = [ev.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return (Vector((min(w.x for w in ws), min(w.y for w in ws), min(w.z for w in ws))),
            Vector((max(w.x for w in ws), max(w.y for w in ws), max(w.z for w in ws))))

eyes = next((o for o in bpy.data.objects if o.type == 'MESH' and ('high-poly' in o.name or 'low-poly' in o.name or '.eyes' in o.name.lower())), None)
if eyes is None:
    raise SystemExit("no eyes object found; objects: %s" % [o.name for o in bpy.data.objects])
lo, hi = eval_bounds(eyes)
EYE_C = (lo + hi) * 0.5
print("eyes object:", eyes.name, "centre (world):", tuple(round(c, 3) for c in EYE_C))

scene = bpy.context.scene
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES; scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True; scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'

# re-aim the existing lights at the eyes (they were aimed at hgt*0.93 which is close, but be exact)
for o in bpy.data.objects:
    if o.type == 'LIGHT':
        o.rotation_euler = (EYE_C - o.location).to_track_quat('-Z', 'Y').to_euler()
        o.data.energy *= LIGHT_SCALE

cd = bpy.data.cameras.new("Cam.FaceClose"); cd.lens = 85; cd.sensor_width = 36
cam = bpy.data.objects.new("Cam.FaceClose", cd); scene.collection.objects.link(cam)
# character faces -Y. 0.6 m in front of the face; target slightly below the eyes (nose bridge).
offset = Vector((-0.20, -0.565, 0.03)) if VIEW == "threequarter" else Vector((0.0, -0.60, 0.03))
cam.location = EYE_C + offset
target = EYE_C + Vector((0, 0, -0.03))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
print("camera at", tuple(round(c, 3) for c in cam.location), "distance to eyes %.3f m" % (cam.location - EYE_C).length, "lens 85mm")
scene.camera = cam
scene.render.resolution_x = scene.render.resolution_y = SIZE; scene.render.resolution_percentage = 100
scene.render.filepath = OUT
t = time.time(); bpy.ops.render.render(write_still=True)
print("[TIMING] render %s %dx%d @%d spp (denoised): %.1fs" % (os.path.basename(OUT), SIZE, SIZE, SAMPLES, time.time() - t), flush=True)
print("[TIMING] TOTAL %.1fs" % (time.time() - T0))
