"""Test 4: Cycles adaptive subdivision (experimental) + procedural noise true displacement, headless.
Run: blender -b --python test_04_displacement.py
"""
import bpy, time, os, json, math
import mathutils

OUT = "/home/user/sgt_morgan/renders/research"
os.makedirs(OUT, exist_ok=True)
T = {}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.feature_set = "EXPERIMENTAL"
sc.cycles.samples = 64
sc.cycles.use_denoising = True
sc.cycles.dicing_rate = 1.0            # render dicing rate (pixels per micropolygon edge)
sc.cycles.preview_dicing_rate = 8
sc.cycles.max_subdivisions = 10
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.3, 0.35, 1)

ld = bpy.data.lights.new("Key", "AREA"); ld.energy = 1500; ld.size = 1.0
lo = bpy.data.objects.new("Key", ld); lo.location = (2, -1.5, 2.5)
lo.rotation_euler = (mathutils.Vector((0, 0, 0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
sc.collection.objects.link(lo)
ld2 = bpy.data.lights.new("Rim", "AREA"); ld2.energy = 600; ld2.size = 2.0
lo2 = bpy.data.objects.new("Rim", ld2); lo2.location = (-1.5, 2, 1.5)
lo2.rotation_euler = (mathutils.Vector((0, 0, 0)) - lo2.location).to_track_quat('-Z', 'Y').to_euler()
sc.collection.objects.link(lo2)

bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
plane = bpy.context.active_object; plane.name = "DispPlane"
# adaptive subdivision: Subsurf must be LAST modifier, object-level cycles flag
sub = plane.modifiers.new("Subd", "SUBSURF")
sub.subdivision_type = "SIMPLE"
sub.levels = 2
sub.render_levels = 2
plane.cycles.use_adaptive_subdivision = True
plane.cycles.dicing_rate = 1.0

mat = bpy.data.materials.new("Disp"); mat.use_nodes = True
# displacement method moved to Material in 4.1+ ('BUMP','DISPLACEMENT','BOTH')
for target in (mat, getattr(mat, "cycles", None)):
    if target is not None and hasattr(target, "displacement_method"):
        try:
            target.displacement_method = "DISPLACEMENT"
            T.setdefault("displacement_method_attr", []).append(type(target).__name__)
        except Exception as e:
            print("displacement_method set failed on", type(target).__name__, e)
nt = mat.node_tree
p = nt.nodes["Principled BSDF"]; outn = nt.nodes["Material Output"]
p.inputs["Base Color"].default_value = (0.45, 0.42, 0.3, 1)
p.inputs["Roughness"].default_value = 0.6
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 6.0
noise.inputs["Detail"].default_value = 8.0
noise.inputs["Roughness"].default_value = 0.6
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 3.0
mixn = nt.nodes.new("ShaderNodeMath"); mixn.operation = "MULTIPLY_ADD"
disp = nt.nodes.new("ShaderNodeDisplacement")
disp.inputs["Midlevel"].default_value = 0.5
disp.inputs["Scale"].default_value = 0.12
nt.links.new(noise.outputs["Fac"], mixn.inputs[0])
mixn.inputs[1].default_value = 0.7
nt.links.new(vor.outputs["Distance"], mixn.inputs[2])
nt.links.new(mixn.outputs[0], disp.inputs["Height"])
nt.links.new(disp.outputs[0], outn.inputs["Displacement"])
plane.data.materials.append(mat)

cd = bpy.data.cameras.new("Cam"); cd.lens = 35
cam = bpy.data.objects.new("Cam", cd); cam.location = (1.6, -2.2, 1.3)
cam.rotation_euler = (mathutils.Vector((0, 0, 0.05)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.collection.objects.link(cam); sc.camera = cam

# base mesh check: 1 quad plane, 2 levels simple subsurf = 16 faces before dicing
t0 = time.time()
sc.render.filepath = f"{OUT}/t04_disp_adaptive.png"
bpy.ops.render.render(write_still=True)
T["adaptive_render_s"] = round(time.time() - t0, 1)
print(f"[4] adaptive displacement render {T['adaptive_render_s']}s", flush=True)

# Comparison: same material, non-adaptive, fixed render_levels=6 (4096 faces) -> shows how coarse it gets
plane.cycles.use_adaptive_subdivision = False
sub.render_levels = 6
t0 = time.time()
sc.render.filepath = f"{OUT}/t04_disp_fixed_lvl6.png"
bpy.ops.render.render(write_still=True)
T["fixed6_render_s"] = round(time.time() - t0, 1)
print(f"[4] fixed subsurf 6 render {T['fixed6_render_s']}s", flush=True)

# Bump-only (no geometry displacement) for comparison of silhouette
for target in (mat, getattr(mat, "cycles", None)):
    if target is not None and hasattr(target, "displacement_method"):
        target.displacement_method = "BUMP"
t0 = time.time()
sc.render.filepath = f"{OUT}/t04_disp_bumponly.png"
bpy.ops.render.render(write_still=True)
T["bump_render_s"] = round(time.time() - t0, 1)
print("[T04_JSON] " + json.dumps(T))
