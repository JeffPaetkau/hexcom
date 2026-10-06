"""Test 6: modifier-stack clothing from a body region, headless.
Body = elongated UV sphere ('upper arm/torso'). Duplicate a face region (z band) into a new mesh,
then Shrinkwrap(offset) -> Solidify -> Bevel -> Subdivision -> Displace(procedural wrinkles).
Run: blender -b --python test_06_modstack.py
"""
import bpy, bmesh, time, os, json, math
import mathutils

OUT = "/home/user/sgt_morgan/renders/research"
os.makedirs(OUT, exist_ok=True)
T = {}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.render.resolution_x = 1024; sc.render.resolution_y = 1024
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.25, 0.25, 0.28, 1)
for name, loc, e in (("Key", (0.6, -0.7, 0.9), 250), ("Fill", (-0.7, -0.4, 0.3), 60), ("Rim", (0.2, 0.8, 0.7), 200)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = e; ld.size = 0.6
    lo = bpy.data.objects.new(name, ld); lo.location = loc
    sc.collection.objects.link(lo)
    lo.rotation_euler = (mathutils.Vector((0, 0, 0.2)) - lo.location).to_track_quat('-Z', 'Y').to_euler()

# body
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=48, radius=0.1, location=(0, 0, 0.2))
body = bpy.context.active_object; body.name = "Body"
body.scale = (1, 0.8, 2.4); bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.shade_smooth()
skin = bpy.data.materials.new("Skin"); skin.use_nodes = True
skin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.78, 0.58, 0.48, 1)
body.data.materials.append(skin)

# duplicate region: faces whose center z in [0.05, 0.35] -> sleeve band
t0 = time.time()
bm = bmesh.new(); bm.from_mesh(body.data)
keep = [f for f in bm.faces if 0.05 <= f.calc_center_median().z <= 0.36]
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in set(keep)], context="FACES")
# the bmesh now has the band; copy to a new mesh
me = bpy.data.meshes.new("Sleeve"); bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
sleeve = bpy.data.objects.new("Sleeve", me)
sleeve.matrix_world = body.matrix_world.copy()
sc.collection.objects.link(sleeve)
T["region_faces"] = len(me.polygons)

# modifier stack
sw = sleeve.modifiers.new("Shrinkwrap", "SHRINKWRAP")
sw.target = body; sw.wrap_method = "NEAREST_SURFACEPOINT"; sw.offset = 0.012
so = sleeve.modifiers.new("Solidify", "SOLIDIFY")
so.thickness = 0.004; so.offset = 1.0; so.use_even_offset = True; so.use_rim = True
bv = sleeve.modifiers.new("Bevel", "BEVEL")
bv.width = 0.0015; bv.segments = 2; bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(40)
sd = sleeve.modifiers.new("Subd", "SUBSURF"); sd.levels = 2; sd.render_levels = 3
# procedural wrinkle displacement: Displace modifier with a Clouds texture, along normals
tex = bpy.data.textures.new("Wrinkles", "CLOUDS")
tex.noise_scale = 0.03; tex.noise_depth = 3; tex.noise_basis = "VORONOI_F2_F1"
dp = sleeve.modifiers.new("Wrinkle", "DISPLACE")
dp.texture = tex; dp.strength = 0.004; dp.mid_level = 0.5; dp.direction = "NORMAL"
dp.texture_coords = "LOCAL"
# second, larger-scale fold displacement with a stretched texture (horizontal folds)
tex2 = bpy.data.textures.new("Folds", "WOOD")
tex2.wood_type = "BANDNOISE"; tex2.noise_scale = 0.05; tex2.turbulence = 8
dp2 = sleeve.modifiers.new("Folds", "DISPLACE")
dp2.texture = tex2; dp2.strength = 0.003; dp2.mid_level = 0.5; dp2.direction = "NORMAL"
dp2.texture_coords = "LOCAL"
T["stack_setup_s"] = round(time.time() - t0, 2)

cloth = bpy.data.materials.new("Cloth"); cloth.use_nodes = True
p = cloth.node_tree.nodes["Principled BSDF"]
p.inputs["Base Color"].default_value = (0.3, 0.32, 0.2, 1)
p.inputs["Roughness"].default_value = 0.9
p.inputs["Sheen Weight"].default_value = 0.5
sleeve.data.materials.append(cloth)

dg = bpy.context.evaluated_depsgraph_get()
ev = sleeve.evaluated_get(dg); me_ev = ev.to_mesh()
T["evaluated_verts"] = len(me_ev.vertices); T["evaluated_faces"] = len(me_ev.polygons)
ev.to_mesh_clear()
print(f"[6] region faces={T['region_faces']} evaluated verts={T['evaluated_verts']} faces={T['evaluated_faces']}", flush=True)

cd = bpy.data.cameras.new("Cam"); cd.lens = 70
cam = bpy.data.objects.new("Cam", cd); cam.location = (0.28, -0.5, 0.35)
cam.rotation_euler = (mathutils.Vector((0, 0, 0.2)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.collection.objects.link(cam); sc.camera = cam
t0 = time.time()
sc.render.filepath = f"{OUT}/t06_modstack.png"
bpy.ops.render.render(write_still=True)
T["render_s"] = round(time.time() - t0, 1)

# apply the whole stack via operator with temp_override (headless) to check that works
t0 = time.time()
applied = []
for mod in list(sleeve.modifiers):
    try:
        with bpy.context.temp_override(object=sleeve, active_object=sleeve, selected_objects=[sleeve]):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        applied.append(mod.name)
    except Exception as e:
        applied.append(f"{mod.name}:FAILED {e!r}")
T["apply_stack_s"] = round(time.time() - t0, 2); T["applied"] = applied
T["final_verts"] = len(sleeve.data.vertices)
print("[6] applied:", applied, "final verts", T["final_verts"], flush=True)
bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/t06_modstack.blend")
print("[T06_JSON] " + json.dumps(T))
