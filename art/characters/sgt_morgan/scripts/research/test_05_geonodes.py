"""Test 5: Geometry Nodes from Python, headless.
(a) webbing strip: Curve to Mesh with a flat rectangular profile along a Bezier curve (belt-like)
(b) MOLLE grid: Grid -> Instance on Points of a 'loop' mesh (torus segment), Realize Instances
Confirm evaluation (vertex counts) and glTF export of the evaluated geometry.
Run: blender -b --python test_05_geonodes.py
"""
import bpy, time, os, json, math
import mathutils

OUT = "/home/user/sgt_morgan/renders/research"
os.makedirs(OUT, exist_ok=True)
T = {}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.render.resolution_x = 1280; sc.render.resolution_y = 720
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.3, 0.33, 1)
ld = bpy.data.lights.new("Key", "AREA"); ld.energy = 400; ld.size = 1.0
lo = bpy.data.objects.new("Key", ld); lo.location = (0.8, -0.8, 1.2)
lo.rotation_euler = (mathutils.Vector((0, 0, 0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
sc.collection.objects.link(lo)


def new_group(name):
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput")
    return ng, gi, go


# ------------------------------------------------ (a) webbing strip along a curve
# Bezier curve roughly a belt loop around a 'waist' ellipse
cu = bpy.data.curves.new("BeltPath", "CURVE"); cu.dimensions = "3D"
spl = cu.splines.new("BEZIER")
n = 8
spl.bezier_points.add(n - 1)
for i, bp in enumerate(spl.bezier_points):
    a = 2 * math.pi * i / n
    bp.co = (0.17 * math.cos(a), 0.12 * math.sin(a), 0.0)
    bp.handle_left_type = bp.handle_right_type = "AUTO"
spl.use_cyclic_u = True
belt_path = bpy.data.objects.new("BeltPath", cu); sc.collection.objects.link(belt_path)

ng, gi, go = new_group("WebbingStrip")
# interface inputs: width, thickness
sw = ng.interface.new_socket("Width", in_out="INPUT", socket_type="NodeSocketFloat"); sw.default_value = 0.05
st = ng.interface.new_socket("Thickness", in_out="INPUT", socket_type="NodeSocketFloat"); st.default_value = 0.003
resample = ng.nodes.new("GeometryNodeResampleCurve"); resample.inputs["Count"].default_value = 128
quad = ng.nodes.new("GeometryNodeCurvePrimitiveQuadrilateral"); quad.mode = "RECTANGLE"
c2m = ng.nodes.new("GeometryNodeCurveToMesh"); c2m.inputs["Fill Caps"].default_value = True
setshade = ng.nodes.new("GeometryNodeSetShadeSmooth"); setshade.inputs["Shade Smooth"].default_value = False
# webbing ribs: displace by sine along the curve? keep simple: add a 'Store Named Attribute' UV later
ng.links.new(gi.outputs["Geometry"], resample.inputs["Curve"])
ng.links.new(gi.outputs["Thickness"], quad.inputs["Width"])    # profile X = thickness (radial)
ng.links.new(gi.outputs["Width"], quad.inputs["Height"])       # profile Y = strap width (along curve normal)
ng.links.new(resample.outputs["Curve"], c2m.inputs["Curve"])
ng.links.new(quad.outputs["Curve"], c2m.inputs["Profile Curve"])
ng.links.new(c2m.outputs["Mesh"], setshade.inputs["Geometry"])
ng.links.new(setshade.outputs["Geometry"], go.inputs["Geometry"])
m = belt_path.modifiers.new("GN", "NODES"); m.node_group = ng
# socket identifiers for modifier inputs (e.g. 'Socket_2'); set via identifier
for item in ng.interface.items_tree:
    if item.item_type == "SOCKET" and item.in_out == "INPUT" and item.name == "Width":
        m[item.identifier] = 0.05
    if item.item_type == "SOCKET" and item.in_out == "INPUT" and item.name == "Thickness":
        m[item.identifier] = 0.0035
webmat = bpy.data.materials.new("Webbing"); webmat.use_nodes = True
webmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.22, 0.14, 1)
webmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
cu.materials.append(webmat)

dg = bpy.context.evaluated_depsgraph_get()
ev = belt_path.evaluated_get(dg)
me_ev = ev.to_mesh()
T["a_webbing_verts"] = len(me_ev.vertices); T["a_webbing_faces"] = len(me_ev.polygons)
ev.to_mesh_clear()
print(f"[5a] webbing strip evaluated: verts={T['a_webbing_verts']} faces={T['a_webbing_faces']}", flush=True)

# ------------------------------------------------ (b) MOLLE loop grid
# loop mesh: a flattened torus segment approximating a 1-inch webbing loop standing off a panel
bpy.ops.mesh.primitive_cube_add(size=1)
loop = bpy.context.active_object; loop.name = "MolleLoop"
loop.scale = (0.038, 0.004, 0.025)   # 38mm wide (1.5in), 4mm thick, 25mm tall (1in webbing)
bpy.ops.object.transform_apply(scale=True)
bev = loop.modifiers.new("Bevel", "BEVEL"); bev.width = 0.0015; bev.segments = 3
loop.hide_render = True; loop.hide_viewport = True
loop.data.materials.append(webmat)

# panel to carry the grid
bpy.ops.mesh.primitive_plane_add(size=1)
panel = bpy.context.active_object; panel.name = "MollePanel"
panel.scale = (0.24, 0.16, 1); bpy.ops.object.transform_apply(scale=True)
panel.rotation_euler = (math.radians(90), 0, 0)   # stand it up facing -Y
panel.location = (0.5, 0, 0)
pm = bpy.data.materials.new("Panel"); pm.use_nodes = True
pm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.27, 0.18, 1)
panel.data.materials.append(pm)

ng2, gi2, go2 = new_group("MolleGrid")
s_obj = ng2.interface.new_socket("Loop", in_out="INPUT", socket_type="NodeSocketObject")
grid = ng2.nodes.new("GeometryNodeMeshGrid")
grid.inputs["Size X"].default_value = 0.20; grid.inputs["Size Y"].default_value = 0.14
grid.inputs["Vertices X"].default_value = 5; grid.inputs["Vertices Y"].default_value = 4
objinfo = ng2.nodes.new("GeometryNodeObjectInfo"); objinfo.transform_space = "ORIGINAL"
iop = ng2.nodes.new("GeometryNodeInstanceOnPoints")
# offset loops off the panel surface a bit (+Z local before panel rotation)
translate = ng2.nodes.new("GeometryNodeTranslateInstances"); translate.inputs["Translation"].default_value = (0, 0, 0.004)
realize = ng2.nodes.new("GeometryNodeRealizeInstances")
join = ng2.nodes.new("GeometryNodeJoinGeometry")
ng2.links.new(gi2.outputs["Loop"], objinfo.inputs["Object"])
ng2.links.new(grid.outputs["Mesh"], iop.inputs["Points"])
ng2.links.new(objinfo.outputs["Geometry"], iop.inputs["Instance"])
# instances: rotate so loop's 25mm (Z) stands along panel Y? keep flat: loop lies on panel, thickness along panel normal
iop.inputs["Rotation"].default_value = (math.radians(90), 0, 0)  # loop thickness(Y) -> panel normal(Z)
ng2.links.new(iop.outputs["Instances"], translate.inputs["Instances"])
ng2.links.new(translate.outputs["Instances"], realize.inputs["Geometry"])
ng2.links.new(gi2.outputs["Geometry"], join.inputs["Geometry"])
ng2.links.new(realize.outputs["Geometry"], join.inputs["Geometry"])
ng2.links.new(join.outputs["Geometry"], go2.inputs["Geometry"])
m2 = panel.modifiers.new("GN", "NODES"); m2.node_group = ng2
m2[s_obj.identifier] = loop

dg = bpy.context.evaluated_depsgraph_get()
ev = panel.evaluated_get(dg)
me_ev = ev.to_mesh()
T["b_molle_verts"] = len(me_ev.vertices); T["b_molle_faces"] = len(me_ev.polygons)
ev.to_mesh_clear()
print(f"[5b] MOLLE grid evaluated: verts={T['b_molle_verts']} faces={T['b_molle_faces']} (expect 20 loops)", flush=True)

# camera
cd = bpy.data.cameras.new("Cam"); cd.lens = 50
cam = bpy.data.objects.new("Cam", cd); cam.location = (0.25, -0.9, 0.35)
cam.rotation_euler = (mathutils.Vector((0.25, 0, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.collection.objects.link(cam); sc.camera = cam
t0 = time.time()
sc.render.filepath = f"{OUT}/t05_geonodes.png"
bpy.ops.render.render(write_still=True)
T["render_s"] = round(time.time() - t0, 1)

# export evaluated geometry to glTF (apply modifiers) -- check GN result survives export
t0 = time.time()
gl = f"{OUT}/t05_geonodes.glb"
bpy.ops.export_scene.gltf(filepath=gl, export_format="GLB", export_apply=True, use_visible=True)
T["gltf_s"] = round(time.time() - t0, 1); T["gltf_bytes"] = os.path.getsize(gl)
print(f"[5] glTF export {T['gltf_s']}s {T['gltf_bytes']} bytes", flush=True)
bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/t05_geonodes.blend")
print("[T05_JSON] " + json.dumps(T))
