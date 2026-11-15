"""Headless MPFB2 smoke test: build a male human, add bodyparts/skin/rig/clothes, render.
Usage:
  blender -b --python mpfb_build_default.py -- [out_dir] [samples]
Writes mpfb_fullbody.png, mpfb_face.png, mpfb_default.blend into out_dir.
"""
import bpy, sys, os, time, math, json

T_START = time.time()
def lap(msg, t=[time.time()]):
    now = time.time()
    print("[TIMING] %-45s +%6.1fs  (total %6.1fs)" % (msg, now - t[0], now - T_START), flush=True)
    t[0] = now

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/home/user/sgt_morgan/renders/research"
SAMPLES = int(argv[1]) if len(argv) > 1 else 64
os.makedirs(OUT, exist_ok=True)

# --- make sure the extension is enabled in this session (userpref was saved, but be explicit)
import addon_utils
mod_name = "bl_ext.user_default.mpfb"
if mod_name not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=mod_name)
lap("addon enabled")

from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
from bl_ext.user_default.mpfb.services.assetservice import AssetService
from bl_ext.user_default.mpfb.services.locationservice import LocationService
from bl_ext.user_default.mpfb.services.objectservice import ObjectService
from bl_ext.user_default.mpfb.services.rigservice import RigService
from bl_ext.user_default.mpfb.entities.objectproperties import HumanObjectProperties

print("MPFB user data:", LocationService.get_user_data())
print("MPFB bundled data:", LocationService.get_mpfb_data())
print("system assets installed:", AssetService.system_assets_pack_is_installed(),
      AssetService.check_if_modern_makehuman_system_assets_installed())
print("packs:", AssetService.get_pack_names())

# --- clean scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# --- macro targets.  MakeHuman convention: age 0.0=1y, 0.1875=11y, 0.5=25y, 1.0=90y
def age_years_to_macro(y):
    if y <= 25:
        return 0.5 * (y - 1) / 24.0
    return 0.5 + 0.5 * (y - 25) / 65.0

macro = TargetService.get_default_macro_info_dict()
macro.update({
    "gender": 1.0,          # male
    "age": age_years_to_macro(32),
    "muscle": 0.7,
    "weight": 0.5,
    "proportions": 0.5,
    "height": 0.5,          # will be fitted to 185 cm below
    "cupsize": 0.5, "firmness": 0.5,
    "race": {"caucasian": 1.0, "asian": 0.0, "african": 0.0},
})
print("macro dict:", json.dumps(macro))

basemesh = HumanService.create_human(mask_helpers=True, detailed_helpers=True,
                                     extra_vertex_groups=True, feet_on_ground=True,
                                     scale=0.1, macro_detail_dict=macro)
basemesh.name = "Human"
lap("create_human (base mesh + macro targets)")

def evaluated_z_range(obj):
    """(zmin, zmax) in world space of the depsgraph-evaluated mesh. NOTE: macro targets are
    shape keys, so obj.data.vertices (the basis) never changes -- always measure evaluated.
    The 'Hide helpers' MASK modifier leaves only the 'body' group, so this is body height."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    zs = [(ev.matrix_world @ v.co).z for v in me.vertices]
    ev.to_mesh_clear()
    return min(zs), max(zs)

def body_height_m(obj):
    zmin, zmax = evaluated_z_range(obj)
    return zmax - zmin

# fit height macro to 185 cm with two samples + linear interpolation
h0 = body_height_m(basemesh); print("height macro 0.5 ->  %.1f cm" % (h0 * 100))
HumanObjectProperties.set_value("height", 0.9, entity_reference=basemesh)
TargetService.reapply_macro_details(basemesh)
h1 = body_height_m(basemesh); print("height macro 0.9 ->  %.1f cm" % (h1 * 100))
target = 1.85
hm = 0.5 + (target - h0) * (0.9 - 0.5) / (h1 - h0) if abs(h1 - h0) > 1e-6 else 0.9
hm = max(0.0, min(1.0, hm))
HumanObjectProperties.set_value("height", hm, entity_reference=basemesh)
TargetService.reapply_macro_details(basemesh)
print("height macro %.3f -> %.1f cm (target 185)" % (hm, body_height_m(basemesh) * 100))
# re-ground feet (evaluated mesh)
low, _ = evaluated_z_range(basemesh)
basemesh.location.z -= low
print("re-grounded by %.4f m" % low)
lap("height fitting")

print("macro targets now:", TargetService.get_current_macro_targets(basemesh))
print("target stack size:", len(TargetService.get_target_stack(basemesh)))

# --- example of a face detail target (non-macro) so we prove the API
face_targets_to_try = ["nose/nose-width-decr|incr", "chin/chin-width-decr|incr", "cheek/l-cheek-bones-decr|incr"]
for tn in face_targets_to_try:
    try:
        p = TargetService.target_full_path(tn.replace("-decr|incr", "-incr"))
        print("target path", tn, "->", p)
    except Exception as e:
        print("target_full_path failed", tn, e)
try:
    TargetService.set_target_value(basemesh, "chin-width-incr", 0.4)
    TargetService.set_target_value(basemesh, "nose-width-incr", 0.3)
    print("set detail targets OK; stack:", len(TargetService.get_target_stack(basemesh)))
except Exception as e:
    print("set_target_value failed:", repr(e))
lap("detail targets")

# --- skin
skin = AssetService.find_asset_absolute_path("young_caucasian_male/young_caucasian_male.mhmat", "skins")
if not skin:
    skin = AssetService.find_asset_absolute_path("young_caucasian_male.mhmat", "skins")
print("skin mhmat:", skin)
HumanService.set_character_skin(skin, basemesh, skin_type="ENHANCED_SSS", material_instances=True)
lap("skin material (ENHANCED_SSS)")

# --- rig (standard "default" rig; "rigify.human" needs the rigify addon enabled)
armature = HumanService.add_builtin_rig(basemesh, "default", import_weights=True)
print("rig:", armature, len(armature.data.bones) if armature else None, "bones")
lap("add_builtin_rig(default)")

# --- bodyparts
def add_part(subdir, fragment, mat="MAKESKIN", subdiv=1):
    p = AssetService.find_asset_absolute_path(fragment, asset_subdir=subdir)
    if p is None:
        print("!! could not find", subdir, fragment); return None
    obj = HumanService.add_mhclo_asset(p, basemesh, asset_type=subdir, subdiv_levels=subdiv, material_type=mat)
    print("added", subdir, fragment, "->", obj.name if obj else None)
    return obj

eyes = add_part("eyes", "high-poly/high-poly.mhclo", mat="PROCEDURAL_EYES")
add_part("eyebrows", "eyebrow001/eyebrow001.mhclo")
add_part("eyelashes", "eyelashes02/eyelashes02.mhclo")
add_part("teeth", "teeth_base/teeth_base.mhclo")
add_part("tongue", "tongue01/tongue01.mhclo")
add_part("hair", "short02/short02.mhclo")
lap("bodyparts (eyes, brows, lashes, teeth, tongue, hair)")

# --- clothes
add_part("clothes", "male_worksuit01/male_worksuit01.mhclo")
add_part("clothes", "culturalibre_male_boots/culturalibre_male_boots.mhclo")
lap("clothes (worksuit + boots)")

print("objects:", [(o.name, o.type, len(o.data.vertices) if o.type == 'MESH' else '') for o in bpy.data.objects])

# --- scene / lights / world
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.cycles.use_adaptive_sampling = True
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
world = bpy.data.worlds.new("World") if scene.world is None else scene.world
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.18, 0.19, 0.21, 1.0)
bg.inputs[1].default_value = 0.6

def area_light(name, loc, target, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size; ld.color = color
    lo = bpy.data.objects.new(name, ld); scene.collection.objects.link(lo); lo.location = loc
    d = (target - lo.location); lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return lo

from mathutils import Vector
hgt = body_height_m(basemesh)
head = Vector((0, 0, hgt * 0.93))
# MakeHuman base mesh faces -Y, so "front" lights/camera sit at negative Y
area_light("Key", Vector((-1.6, -2.2, 2.4)), head, 600, 1.2, (1.0, 0.95, 0.9))
area_light("Fill", Vector((2.2, -2.0, 1.6)), head, 200, 2.5, (0.85, 0.9, 1.0))
area_light("Rim", Vector((0.8, 2.5, 2.3)), head, 400, 0.8)

def make_cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    co = bpy.data.objects.new(name, cd); scene.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (target - co.location).to_track_quat('-Z', 'Y').to_euler()
    return co

def render(cam, path, w, h):
    scene.camera = cam
    scene.render.resolution_x = w; scene.render.resolution_y = h; scene.render.resolution_percentage = 100
    scene.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print("[TIMING] render %s %dx%d @%d spp: %.1fs" % (os.path.basename(path), w, h, SAMPLES, time.time() - t), flush=True)

cam_full = make_cam("Cam.Full", Vector((0.0, -5.2, hgt * 0.5)), Vector((0, 0, hgt * 0.5)), 50)
cam_face = make_cam("Cam.Face", Vector((0.12, -0.62, hgt * 0.925)), Vector((0, 0, hgt * 0.925)), 85)

lap("scene setup")
render(cam_full, os.path.join(OUT, "mpfb_fullbody.png"), 900, 1600)
lap("render fullbody")
render(cam_face, os.path.join(OUT, "mpfb_face.png"), 1024, 1024)
lap("render face")

blend = os.path.join(OUT, "mpfb_default.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
print("saved", blend, "%.1f MB" % (os.path.getsize(blend) / 1e6))
lap("save blend")
print("[TIMING] TOTAL %.1fs" % (time.time() - T_START))
