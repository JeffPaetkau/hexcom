"""Blender headless: import an OBJ (with optional vertex colors), render front and 3/4 and profile
views with Cycles CPU, grey clay + vertex-color variants.

blender -b --python ai_render_obj.py -- <obj> <out_prefix> [samples]
"""
import bpy, sys, math, os
argv = sys.argv[sys.argv.index("--") + 1:]
obj_path, out_prefix = argv[0], argv[1]
samples = int(argv[2]) if len(argv) > 2 else 32

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = samples
scene.cycles.use_denoising = True
scene.render.resolution_x = 640
scene.render.resolution_y = 640
scene.render.film_transparent = False
scene.view_settings.view_transform = "Standard"

bpy.ops.wm.obj_import(filepath=obj_path, forward_axis="NEGATIVE_Z", up_axis="Y")
ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
# normalize: center and scale to ~0.25 m head
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
ob.location = (0, 0, 0)
d = max(ob.dimensions)
s = 0.25 / d
ob.scale = (s, s, s)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.shade_smooth()
has_vcol = len(ob.data.color_attributes) > 0

def make_mat(use_vcol):
    m = bpy.data.materials.new("M")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.55
    if use_vcol and has_vcol:
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = ob.data.color_attributes[0].name
        nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (0.6, 0.6, 0.6, 1)
    return m

# world light
w = bpy.data.worlds.new("W"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.35, 0.38, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
# key light
bpy.ops.object.light_add(type="AREA", location=(0.5, -0.8, 0.6))
key = bpy.context.object; key.data.energy = 60; key.data.size = 0.6
key.rotation_euler = (math.radians(55), 0, math.radians(32))

cam_data = bpy.data.cameras.new("C"); cam_data.lens = 85
cam = bpy.data.objects.new("Cam", cam_data); scene.collection.objects.link(cam); scene.camera = cam

views = {"front": 0.0, "threequarter": math.radians(40), "profile": math.radians(90)}
for variant in (["vcol", "clay"] if has_vcol else ["clay"]):
    ob.data.materials.clear()
    ob.data.materials.append(make_mat(variant == "vcol"))
    for name, ang in views.items():
        r = 0.9
        cam.location = (r * math.sin(ang), -r * math.cos(ang), 0.02)
        cam.rotation_euler = (math.radians(89), 0, ang)
        scene.render.filepath = f"{out_prefix}_{variant}_{name}.png"
        bpy.ops.render.render(write_still=True)
        print("wrote", scene.render.filepath)
