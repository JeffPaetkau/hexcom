"""Test 8: shader-based skin on a sphere, headless closeup.
Principled BSDF, subsurface Random Walk (Skin), procedural micro-normal (high-frequency noise -> Bump),
pore-scale roughness variation, 3-point area lights.
Run: blender -b --python test_08_skin.py
"""
import bpy, time, os, json, math
import mathutils

OUT = "/home/user/sgt_morgan/renders/research"
os.makedirs(OUT, exist_ok=True)
T = {}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = 48; sc.cycles.use_denoising = True   # 96 spp took 428 s on the loaded box; 48 is enough with OIDN
sc.cycles.denoiser = "OPENIMAGEDENOISE"; sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
sc.render.resolution_x = 640; sc.render.resolution_y = 640
sc.view_settings.view_transform = "AgX"
# 4.5 look enum: 'None', 'AgX - Punchy', 'AgX - Greyscale', 'AgX - Very High Contrast', 'AgX - High Contrast',
# 'AgX - Medium High Contrast', 'AgX - Base Contrast', 'AgX - Medium Low Contrast', 'AgX - Low Contrast',
# 'AgX - Very Low Contrast'  (there is no 'AgX - Medium Contrast')
sc.view_settings.look = "AgX - Medium High Contrast"
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.12, 0.12, 0.14, 1)
# first run used 80/20/90 W at ~1 m on a 100 mm sphere: blown out to white. ~1-2 W/m^2 at the subject is right.
for name, loc, e, col in (("Key", (0.5, -0.6, 0.6), 12, (1, 0.95, 0.9)),
                          ("Fill", (-0.7, -0.5, 0.2), 3, (0.85, 0.9, 1)),
                          ("Rim", (0.3, 0.7, 0.5), 12, (1, 1, 1))):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = e; ld.size = 0.5; ld.color = col
    lo = bpy.data.objects.new(name, ld); lo.location = loc
    sc.collection.objects.link(lo)
    lo.rotation_euler = (mathutils.Vector((0, 0, 0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()

bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=0.1, location=(0, 0, 0))
head = bpy.context.active_object; head.name = "SkinSphere"
bpy.ops.object.shade_smooth()
sd = head.modifiers.new("Subd", "SUBSURF"); sd.levels = 1; sd.render_levels = 2

mat = bpy.data.materials.new("Skin"); mat.use_nodes = True
nt = mat.node_tree; p = nt.nodes["Principled BSDF"]
# subsurface
p.subsurface_method = "RANDOM_WALK_SKIN"        # 4.x: 'BURLEY', 'RANDOM_WALK', 'RANDOM_WALK_SKIN'
p.inputs["Base Color"].default_value = (0.80, 0.56, 0.47, 1)
p.inputs["Subsurface Weight"].default_value = 1.0
p.inputs["Subsurface Radius"].default_value = (1.0, 0.2, 0.1)
p.inputs["Subsurface Scale"].default_value = 0.012   # metres: radius * scale -> ~1.2cm red
p.inputs["Subsurface IOR"].default_value = 1.4
p.inputs["Subsurface Anisotropy"].default_value = 0.8
p.inputs["Roughness"].default_value = 0.45
p.inputs["Specular IOR Level"].default_value = 0.5
p.inputs["IOR"].default_value = 1.45
p.inputs["Coat Weight"].default_value = 0.15      # thin oily layer
p.inputs["Coat Roughness"].default_value = 0.25
# colour variation: mottling via noise -> mix with slightly redder tone
tc = nt.nodes.new("ShaderNodeTexCoord")
mott = nt.nodes.new("ShaderNodeTexNoise"); mott.inputs["Scale"].default_value = 60; mott.inputs["Detail"].default_value = 4
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.4; ramp.color_ramp.elements[0].color = (0.70, 0.42, 0.38, 1)
ramp.color_ramp.elements[1].position = 0.6; ramp.color_ramp.elements[1].color = (0.82, 0.60, 0.50, 1)
nt.links.new(tc.outputs["Object"], mott.inputs["Vector"])
nt.links.new(mott.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
# micro-normal: two noise octaves (pores ~ 0.3mm) -> bump
pores = nt.nodes.new("ShaderNodeTexNoise"); pores.inputs["Scale"].default_value = 900; pores.inputs["Detail"].default_value = 2; pores.inputs["Roughness"].default_value = 0.5
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 700; vor.feature = "F1"
mix = nt.nodes.new("ShaderNodeMath"); mix.operation = "MULTIPLY_ADD"; mix.inputs[1].default_value = 0.6
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25; bump.inputs["Distance"].default_value = 0.0004
nt.links.new(tc.outputs["Object"], pores.inputs["Vector"]); nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
nt.links.new(pores.outputs["Fac"], mix.inputs[0]); nt.links.new(vor.outputs["Distance"], mix.inputs[2])
nt.links.new(mix.outputs[0], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])
# roughness variation
rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["From Min"].default_value = 0; rr.inputs["From Max"].default_value = 1
rr.inputs["To Min"].default_value = 0.35; rr.inputs["To Max"].default_value = 0.6
nt.links.new(mix.outputs[0], rr.inputs["Value"]); nt.links.new(rr.outputs["Result"], p.inputs["Roughness"])
head.data.materials.append(mat)

cd = bpy.data.cameras.new("Cam"); cd.lens = 85
cam = bpy.data.objects.new("Cam", cd); cam.location = (0.2, -0.48, 0.14)   # sphere fills ~90% of the frame
cam.rotation_euler = (mathutils.Vector((0, 0, 0.01)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.collection.objects.link(cam); sc.camera = cam
# DOF for realism
cd.dof.use_dof = False   # f/4 at 0.3 m blurred the whole sphere in the first run; judge SSS sharp

t0 = time.time()
sc.render.filepath = f"{OUT}/t08_skin_sss.png"
bpy.ops.render.render(write_still=True)
T["render_s"] = round(time.time() - t0, 1)
print(f"[8] skin render {T['render_s']}s", flush=True)

# comparison: SSS off (plain diffuse) to confirm the SSS actually shows
p.inputs["Subsurface Weight"].default_value = 0.0
t0 = time.time()
sc.render.filepath = f"{OUT}/t08_skin_nosss.png"
bpy.ops.render.render(write_still=True)
T["render_nosss_s"] = round(time.time() - t0, 1)
bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/t08_skin.blend")
print("[T08_JSON] " + json.dumps(T))
