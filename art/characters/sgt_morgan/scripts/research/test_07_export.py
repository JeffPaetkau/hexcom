"""Test 7: export headless. Rigged, textured test asset -> glTF (GLB, textures packed) and FBX.
Builds: a subdivided cylinder 'limb' with a generated 1024px image texture (packed) and normal map,
a 2-bone armature with automatic weights (operator with temp_override), a shape key.
Run: blender -b --python test_07_export.py
"""
import bpy, time, os, json, math
import numpy as np

OUT = "/home/user/sgt_morgan/renders/research"
EXP = "/home/user/sgt_morgan/assets/blender_caps"
os.makedirs(OUT, exist_ok=True); os.makedirs(EXP, exist_ok=True)
T = {}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# mesh
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.06, depth=0.6, location=(0, 0, 0.3))
limb = bpy.context.active_object; limb.name = "Limb"
# add loop cuts along Z via subdivision of side faces: use bmesh subdivide edges
import bmesh
bm = bmesh.new(); bm.from_mesh(limb.data)
vertical = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.5]
bmesh.ops.subdivide_edges(bm, edges=vertical, cuts=11, use_grid_fill=True)
bm.to_mesh(limb.data); bm.free()
bpy.ops.object.shade_smooth()
# UVs. GOTCHA: object.mode_set ignores temp_override(object=...) in background mode; it needs the
# real view-layer active object. Set view_layer.objects.active and select the object instead.
def set_active(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob

set_active(limb)
bpy.ops.object.mode_set(mode="EDIT")
assert limb.mode == "EDIT", "mode_set EDIT failed on mesh"
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")
T["uv_layers"] = len(limb.data.uv_layers)

# generated textures (numpy -> image pixels), packed into the .blend so glTF embeds them
def make_image(name, size, fn):
    img = bpy.data.images.new(name, size, size, alpha=True)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    r, g, b = fn(xx, yy)
    px = np.ones((size, size, 4), np.float32)
    px[..., 0] = r; px[..., 1] = g; px[..., 2] = b
    img.pixels.foreach_set(px.ravel())
    img.pack()
    return img

t0 = time.time()
camo = make_image("LimbAlbedo", 1024, lambda x, y: (
    0.25 + 0.2 * (np.sin(x * 40) * np.cos(y * 23) > 0.2),
    0.28 + 0.15 * (np.sin(x * 17 + 1) * np.cos(y * 31) > 0.1),
    0.15 + 0.05 * (np.sin(x * 60) > 0)))
camo.colorspace_settings.name = "sRGB"
nrm = make_image("LimbNormal", 1024, lambda x, y: (
    0.5 + 0.08 * np.sin(x * 400), 0.5 + 0.08 * np.sin(y * 400), np.ones_like(x)))
nrm.colorspace_settings.name = "Non-Color"
T["texgen_s"] = round(time.time() - t0, 2)

mat = bpy.data.materials.new("LimbMat"); mat.use_nodes = True
nt = mat.node_tree; p = nt.nodes["Principled BSDF"]
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = camo
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = nrm
nm = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(ti.outputs["Color"], p.inputs["Base Color"])
nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
p.inputs["Roughness"].default_value = 0.8
limb.data.materials.append(mat)

# shape key
limb.shape_key_add(name="Basis")
sk = limb.shape_key_add(name="Bulge")
import mathutils
for i, v in enumerate(limb.data.vertices):
    if 0.2 < v.co.z < 0.4:
        radial = mathutils.Vector((v.co.x, v.co.y, 0.0)).normalized()
        sk.data[i].co = v.co + radial * 0.012
T["shape_keys"] = len(limb.data.shape_keys.key_blocks)

# armature with 2 bones
arm = bpy.data.armatures.new("Rig"); rig = bpy.data.objects.new("Rig", arm)
sc.collection.objects.link(rig)
# record the failing variant for the notes, then do it the working way
try:
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        r = bpy.ops.object.mode_set(mode="EDIT")
    T["mode_set_via_temp_override"] = f"{r} -> rig.mode={rig.mode} limb.mode={limb.mode} (view-layer active was limb)"
except Exception as e:
    T["mode_set_via_temp_override"] = repr(e)
print("[7] probe:", T["mode_set_via_temp_override"], flush=True)
if limb.mode != "OBJECT":   # the probe toggled the wrong object; undo it
    set_active(limb); bpy.ops.object.mode_set(mode="OBJECT")
set_active(rig)
bpy.ops.object.mode_set(mode="EDIT")
assert rig.mode == "EDIT", "mode_set EDIT failed on armature"
b1 = arm.edit_bones.new("upper"); b1.head = (0, 0, 0.0); b1.tail = (0, 0, 0.3)
b2 = arm.edit_bones.new("lower"); b2.head = (0, 0, 0.3); b2.tail = (0, 0, 0.6); b2.parent = b1; b2.use_connect = True
bpy.ops.object.mode_set(mode="OBJECT")
# automatic weights: parent_set with ARMATURE_AUTO needs both selected, rig active (real selection)
try:
    limb.select_set(True); rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    T["auto_weights_ok"] = True
    T["vgroups"] = [vg.name for vg in limb.vertex_groups]
except Exception as e:
    T["auto_weights_ok"] = False; T["auto_weights_err"] = repr(e)
print("[7] auto weights:", T.get("auto_weights_ok"), T.get("vgroups", T.get("auto_weights_err")), flush=True)

# simple pose animation (so FBX/glTF carry an action)
rig.animation_data_create()
pb = rig.pose.bones["lower"]
pb.rotation_mode = "XYZ"
pb.rotation_euler = (0, 0, 0); pb.keyframe_insert("rotation_euler", frame=1)
pb.rotation_euler = (math.radians(45), 0, 0); pb.keyframe_insert("rotation_euler", frame=24)
sc.frame_end = 24

# ---- glTF export (GLB, textures embedded) ----
t0 = time.time()
glb = f"{EXP}/t07_limb.glb"
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", export_apply=False,
                          export_image_format="AUTO", export_skins=True, export_morph=True,
                          export_animations=True, export_yup=True)
T["glb_s"] = round(time.time() - t0, 2); T["glb_bytes"] = os.path.getsize(glb)
print(f"[7] GLB {T['glb_bytes']} bytes in {T['glb_s']}s", flush=True)

# glTF separate with textures as files
t0 = time.time()
gltf = f"{EXP}/t07_limb_separate.gltf"
bpy.ops.export_scene.gltf(filepath=gltf, export_format="GLTF_SEPARATE", export_apply=False, export_texture_dir="tex")
T["gltf_sep_s"] = round(time.time() - t0, 2)
T["gltf_sep_files"] = sorted(os.listdir(EXP)) + (sorted(os.listdir(f"{EXP}/tex")) if os.path.isdir(f"{EXP}/tex") else [])

# ---- FBX export ----
t0 = time.time()
fbx = f"{EXP}/t07_limb.fbx"
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=False, path_mode="COPY", embed_textures=True,
                         add_leaf_bones=False, bake_anim=True, mesh_smooth_type="FACE")
T["fbx_s"] = round(time.time() - t0, 2); T["fbx_bytes"] = os.path.getsize(fbx)
print(f"[7] FBX {T['fbx_bytes']} bytes in {T['fbx_s']}s", flush=True)

# ---- re-import GLB to verify round trip ----
t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs = {o.name: o.type for o in bpy.data.objects}
T["reimport"] = {"objects": objs, "images": [i.name for i in bpy.data.images], "actions": [a.name for a in bpy.data.actions],
                 "shape_keys": [k.name for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys for k in o.data.shape_keys.key_blocks]}
T["reimport_s"] = round(time.time() - t0, 2)
print("[7] reimport:", T["reimport"], flush=True)
# quick render of reimported asset for the eyeball check
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 32; sc.cycles.use_denoising = True
sc.render.resolution_x = 640; sc.render.resolution_y = 800
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.3, 0.3, 1)
import mathutils
ld = bpy.data.lights.new("Key", "AREA"); ld.energy = 300; ld.size = 1
lo = bpy.data.objects.new("Key", ld); lo.location = (0.8, -0.8, 1.0)
lo.rotation_euler = (mathutils.Vector((0, 0.3, 0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
sc.collection.objects.link(lo)
cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); cam.location = (0.5, -1.0, 0.5)
cam.rotation_euler = (mathutils.Vector((0, 0.3, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.collection.objects.link(cam); sc.camera = cam
sc.frame_set(24)
sc.render.filepath = f"{OUT}/t07_export_reimport.png"
bpy.ops.render.render(write_still=True)
print("[T07_JSON] " + json.dumps(T))
