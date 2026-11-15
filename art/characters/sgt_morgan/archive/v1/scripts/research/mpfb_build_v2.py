"""Headless MPFB2 build v2: male, ~40 y, muscle 0.7, weight 0.45, 185 cm, caucasian;
face detail targets loaded the RIGHT way (load_target / bulk_load_targets), skin, rig,
bodyparts, stubble beard, cargo pants + t-shirt + boots; Cycles CPU renders.

Fixes vs v1: body height is measured BEFORE clothes are added (the clothes' 'Delete.*' mask
modifiers hide the lower body, which made v1 measure 0.83 m and aim the face camera at the
crotch). The face camera is anchored on the eyes object's world bounding box.

Usage:
  blender -b --python mpfb_build_v2.py -- [out_dir] [samples] [age_years] [skin_fragment]
"""
import bpy, sys, os, time, json
from mathutils import Vector

T_START = time.time()
def lap(msg, t=[time.time()]):
    now = time.time()
    print("[TIMING] %-48s +%6.1fs  (total %6.1fs)" % (msg, now - t[0], now - T_START), flush=True)
    t[0] = now

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/home/user/sgt_morgan/renders/research"
SAMPLES = int(argv[1]) if len(argv) > 1 else 64
AGE_YEARS = float(argv[2]) if len(argv) > 2 else 40.0
SKIN = argv[3] if len(argv) > 3 else "middleage_caucasian_male/middleage_caucasian_male.mhmat"
os.makedirs(OUT, exist_ok=True)

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
print("packs:", AssetService.get_pack_names())

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# MakeHuman age convention: macro 0.0 = 1 y, 0.1875 = 11 y, 0.5 = 25 y, 1.0 = 90 y
def age_years_to_macro(y):
    return 0.5 * (y - 1) / 24.0 if y <= 25 else 0.5 + 0.5 * (y - 25) / 65.0

macro = TargetService.get_default_macro_info_dict()
macro.update({"gender": 1.0, "age": age_years_to_macro(AGE_YEARS), "muscle": 0.7, "weight": 0.45,
              "proportions": 0.5, "height": 0.5, "cupsize": 0.5, "firmness": 0.5,
              "race": {"caucasian": 1.0, "asian": 0.0, "african": 0.0}})
print("macro:", json.dumps(macro))

basemesh = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                     feet_on_ground=True, scale=0.1, macro_detail_dict=macro)
basemesh.name = "Human"
lap("create_human")

def eval_bounds(obj):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    ws = [ev.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    lo = Vector((min(w.x for w in ws), min(w.y for w in ws), min(w.z for w in ws)))
    hi = Vector((max(w.x for w in ws), max(w.y for w in ws), max(w.z for w in ws)))
    return lo, hi

def body_height_m():
    lo, hi = eval_bounds(basemesh); return hi.z - lo.z

# --- fit height macro to 185 cm (two samples, linear; height macro is close to linear)
h0 = body_height_m()
HumanObjectProperties.set_value("height", 0.9, entity_reference=basemesh); TargetService.reapply_macro_details(basemesh)
h1 = body_height_m()
hm = max(0.0, min(1.0, 0.5 + (1.85 - h0) * 0.4 / (h1 - h0)))
HumanObjectProperties.set_value("height", hm, entity_reference=basemesh); TargetService.reapply_macro_details(basemesh)
print("height: macro0.5=%.1fcm macro0.9=%.1fcm -> macro %.3f = %.1f cm" % (h0 * 100, h1 * 100, hm, body_height_m() * 100))
lap("height fit")

# --- FACE / BODY DETAIL TARGETS. set_target_value only changes an EXISTING shape key, so a new
# target must first be loaded: load_target(obj, target_full_path(name), weight=w) or bulk_load_targets.
DETAIL_TARGETS = [  # (name = filename stem under data/targets/<cat>/, weight)
    ("chin-width-incr", 0.35), ("chin-prominent-incr", 0.3), ("chin-bones-incr", 0.4),
    ("head-square", 0.3), ("head-scale-depth-incr", 0.1),
    ("nose-width1-decr", 0.2), ("nose-hump-incr", 0.15), ("nose-point-width-decr", 0.15),
    ("l-cheek-bones-incr", 0.4), ("r-cheek-bones-incr", 0.4),
    ("l-cheek-inner-decr", 0.3), ("r-cheek-inner-decr", 0.3),
    ("l-eye-height2-decr", 0.2), ("r-eye-height2-decr", 0.2),
    ("mouth-scale-horiz-incr", 0.15), ("mouth-lowerlip-height-decr", 0.2),
    ("measure-shoulder-dist-incr", 0.3), ("measure-neck-circ-incr", 0.3),
]
loaded = 0
for name, w in DETAIL_TARGETS:
    p = TargetService.target_full_path(name)
    if p is None:
        print("!! no target file for", name); continue
    sk = TargetService.load_target(basemesh, p, weight=w)
    loaded += 1
    if loaded <= 3:
        print("loaded target", name, "->", p, "shape key", sk.name, sk.value)
print("detail targets loaded:", loaded, "/", len(DETAIL_TARGETS))
print("stack size:", len(TargetService.get_target_stack(basemesh)),
      "first non-macro:", [t for t in TargetService.get_target_stack(basemesh) if not t["target"].startswith("macrodetail")][:4])
# bulk API, as used by HumanService._load_targets when loading a saved human:
TargetService.bulk_load_targets(basemesh, [{"target": "forehead-scale-vert-decr", "value": 0.15},
                                           {"target": "l-ear-trans-backward", "value": 0.1}])
print("after bulk_load stack size:", len(TargetService.get_target_stack(basemesh)))
lap("detail targets (load_target / bulk_load_targets)")

# re-ground after detail targets (same as deserialize_from_dict does)
lo, hi = eval_bounds(basemesh)
basemesh.location.z -= lo.z
bpy.context.view_layer.update()
HGT = body_height_m()
print("final body height %.1f cm, grounded (min z %.4f)" % (HGT * 100, eval_bounds(basemesh)[0].z))

# --- skin
skin = AssetService.find_asset_absolute_path(SKIN, "skins")
print("skin mhmat:", skin)
HumanService.set_character_skin(skin, basemesh, skin_type="ENHANCED_SSS", material_instances=True)
lap("skin (ENHANCED_SSS)")

# --- rig
armature = HumanService.add_builtin_rig(basemesh, "default", import_weights=True)
print("rig:", armature.name, len(armature.data.bones), "bones")
lap("add_builtin_rig default")

def add_part(subdir, fragment, mat="MAKESKIN", subdiv=1):
    p = AssetService.find_asset_absolute_path(fragment, asset_subdir=subdir)
    if p is None:
        print("!! could not find", subdir, fragment); return None
    obj = HumanService.add_mhclo_asset(p, basemesh, asset_type=subdir, subdiv_levels=subdiv, material_type=mat)
    print("added", subdir, fragment, "->", obj.name)
    return obj

eyes = add_part("eyes", "high-poly/high-poly.mhclo", mat="PROCEDURAL_EYES")
add_part("eyebrows", "eyebrow006/eyebrow006.mhclo")
add_part("eyelashes", "eyelashes02/eyelashes02.mhclo")
add_part("teeth", "teeth_base/teeth_base.mhclo")
add_part("tongue", "tongue01/tongue01.mhclo")
add_part("hair", "short04/short04.mhclo")
lap("bodyparts")
add_part("clothes", "wdg_scruffy_beard/wdg_scruffy_beard.mhclo")  # stubble, from bodyparts05
add_part("clothes", "cortu_cargo_pants/cortu_cargo_pants.mhclo")   # pants01
add_part("clothes", "elvs_crude_t-shirt_male/elvs_crude_t-shirt_male.mhclo")  # shirts01
add_part("clothes", "culturalibre_male_boots/culturalibre_male_boots.mhclo")  # shoes01
lap("clothes")

print("objects:", [(o.name, o.type, len(o.data.vertices) if o.type == 'MESH' else '') for o in bpy.data.objects])

# --- anchors from the EYES object (robust: independent of the body's delete-masks)
elo, ehi = eval_bounds(eyes)
EYE_C = (elo + ehi) * 0.5
print("eyes centre (world):", tuple(round(c, 3) for c in EYE_C), "body height", round(HGT, 3))

# --- scene
scene = bpy.context.scene
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES; scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True; scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
world = scene.world or bpy.data.worlds.new("World"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.18, 0.19, 0.21, 1.0); bg.inputs[1].default_value = 0.6

def area_light(name, loc, target, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size; ld.color = color
    lo_ = bpy.data.objects.new(name, ld); scene.collection.objects.link(lo_); lo_.location = loc
    lo_.rotation_euler = (target - lo_.location).to_track_quat('-Z', 'Y').to_euler(); return lo_

# character faces -Y; camera/key on the -Y side
area_light("Key", EYE_C + Vector((-1.4, -1.6, 0.7)), EYE_C, 500, 1.0, (1.0, 0.95, 0.9))
area_light("Fill", EYE_C + Vector((2.0, -1.8, -0.1)), EYE_C, 150, 2.5, (0.85, 0.9, 1.0))
area_light("Rim", EYE_C + Vector((0.8, 2.2, 0.6)), EYE_C, 350, 0.8)

def make_cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    co = bpy.data.objects.new(name, cd); scene.collection.objects.link(co); co.location = loc
    co.rotation_euler = (target - co.location).to_track_quat('-Z', 'Y').to_euler(); return co

def render(cam, path, w, h):
    scene.camera = cam; scene.render.resolution_x = w; scene.render.resolution_y = h
    scene.render.resolution_percentage = 100; scene.render.filepath = path
    t = time.time(); bpy.ops.render.render(write_still=True)
    print("[TIMING] render %s %dx%d @%d spp: %.1fs" % (os.path.basename(path), w, h, SAMPLES, time.time() - t), flush=True)

cam_full = make_cam("Cam.Full", Vector((0.0, -5.0, HGT * 0.5)), Vector((0, 0, HGT * 0.5)), 50)
# 3/4 face view from the soldier's right-front (viewer's left), like the reference crop
cam_face = make_cam("Cam.Face", EYE_C + Vector((-0.22, -0.50, 0.02)), EYE_C + Vector((0, 0, -0.03)), 85)
lap("scene")
render(cam_full, os.path.join(OUT, "mpfb_v2_fullbody.png"), 900, 1600); lap("render fullbody")
render(cam_face, os.path.join(OUT, "mpfb_v2_face.png"), 1024, 1024); lap("render face")

blend = os.path.join(OUT, "mpfb_v2.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
print("saved", blend, "%.1f MB" % (os.path.getsize(blend) / 1e6))
print("[TIMING] TOTAL %.1fs" % (time.time() - T_START))
