"""Test 10: cheap headless probes asked for by the part specs ([VERIFY: research_blender_capabilities]).
(a) bundled procedural hair node assets: list node groups, append one with bpy.data.libraries.load
(b) Geometry Nodes Store Named Attribute -> modifier_apply -> float attribute still on the mesh and
    readable by the shader 'Attribute' node
(c) bpy.ops.object.bake headless (Cycles, DIFFUSE colour only, 512 px) timing
Run: blender -b --python scripts/research/test_10_probes.py
"""
import bpy, time, os, json

OUT = "/home/user/sgt_morgan/renders/research"
os.makedirs(OUT, exist_ok=True)
T = {}
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"

# ---------------------------------------------------------------- (a) hair node assets
HAIR_BLEND = "/opt/blender/blender-4.5.14-linux-x64/4.5/datafiles/assets/geometry_nodes/procedural_hair_node_assets.blend"
t0 = time.time()
with bpy.data.libraries.load(HAIR_BLEND, link=False) as (src, dst):
    T["a_groups_available"] = sorted(src.node_groups)
    dst.node_groups = [n for n in src.node_groups if n in ("Generate Hair Curves", "Hair Curves Noise",
                                                           "Set Hair Curve Profile", "Trim Hair Curves",
                                                           "Clump Hair Curves", "Interpolate Hair Curves")]
T["a_appended"] = [n.name for n in dst.node_groups if n is not None]
T["a_append_s"] = round(time.time() - t0, 2)
# can we put one on a Curves object as a modifier and set its inputs by identifier?
try:
    hc = bpy.data.hair_curves.new("Probe"); hc.add_curves([4] * 10)
    hco = bpy.data.objects.new("Probe", hc); sc.collection.objects.link(hco)
    ng = bpy.data.node_groups.get("Hair Curves Noise")
    m = hco.modifiers.new("Noise", "NODES"); m.node_group = ng
    T["a_noise_inputs"] = [(it.name, it.identifier, getattr(it, "default_value", None).__class__.__name__)
                           for it in ng.interface.items_tree if it.item_type == "SOCKET" and it.in_out == "INPUT"]
    dg = bpy.context.evaluated_depsgraph_get()
    T["a_noise_eval_points"] = len(hco.evaluated_get(dg).data.points)
except Exception as e:
    T["a_noise_err"] = repr(e)
print("[10a]", json.dumps({k: v for k, v in T.items() if k.startswith("a_")}), flush=True)

# ---------------------------------------------------------------- (b) GN named attribute survives apply
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.1, location=(0, 0, 0))
sph = bpy.context.active_object; sph.name = "AttrSphere"
ng = bpy.data.node_groups.new("StoreWear", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi = ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput")
store = ng.nodes.new("GeometryNodeStoreNamedAttribute")
store.data_type = "FLOAT"; store.domain = "POINT"; store.inputs["Name"].default_value = "wear"
pos = ng.nodes.new("GeometryNodeInputPosition")
sep = ng.nodes.new("ShaderNodeSeparateXYZ")
mr = ng.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.1; mr.inputs["From Max"].default_value = 0.1
ng.links.new(gi.outputs[0], store.inputs["Geometry"])
ng.links.new(pos.outputs[0], sep.inputs[0]); ng.links.new(sep.outputs["Z"], mr.inputs["Value"])
ng.links.new(mr.outputs["Result"], store.inputs["Value"])
ng.links.new(store.outputs[0], go.inputs[0])
m = sph.modifiers.new("GN", "NODES"); m.node_group = ng
with bpy.context.temp_override(object=sph, active_object=sph, selected_objects=[sph]):
    r = bpy.ops.object.modifier_apply(modifier="GN")
attr = sph.data.attributes.get("wear")
vals = [0.0] * len(sph.data.vertices)
if attr is not None:
    attr.data.foreach_get("value", vals)
T["b_apply"] = str(r); T["b_attr_present"] = attr is not None
T["b_attr_domain_type"] = (attr.domain, attr.data_type) if attr else None
T["b_attr_minmax"] = (round(min(vals), 3), round(max(vals), 3))
# shader side: Attribute node reads it
mat = bpy.data.materials.new("Wear"); mat.use_nodes = True
an = mat.node_tree.nodes.new("ShaderNodeAttribute"); an.attribute_name = "wear"; an.attribute_type = "GEOMETRY"
mat.node_tree.links.new(an.outputs["Fac"], mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"])
sph.data.materials.append(mat)
T["b_shader_attribute_node"] = an.bl_idname
print("[10b]", json.dumps({k: v for k, v in T.items() if k.startswith("b_")}), flush=True)

# ---------------------------------------------------------------- (c) headless bake
# needs: UVs, an image node selected+active in the material, object selected and active in the view layer
for o in bpy.context.view_layer.objects:
    o.select_set(False)
sph.select_set(True); bpy.context.view_layer.objects.active = sph
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(island_margin=0.02); bpy.ops.object.mode_set(mode="OBJECT")
img = bpy.data.images.new("WearBake", 512, 512, alpha=False)
tex = mat.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = img
for n in mat.node_tree.nodes:
    n.select = False
tex.select = True; mat.node_tree.nodes.active = tex
# drive base colour from the attribute so the bake has something to show
mat.node_tree.links.new(an.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
sc.cycles.samples = 4
sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False; sc.render.bake.use_pass_color = True
sc.render.bake.margin = 4
t0 = time.time()
try:
    r = bpy.ops.object.bake(type="DIFFUSE")
    T["c_bake"] = str(r)
except Exception as e:
    T["c_bake"] = repr(e)
T["c_bake_s"] = round(time.time() - t0, 1)
img.filepath_raw = f"{OUT}/t10_bake_wear.png"; img.file_format = "PNG"; img.save()
px = [0.0] * (512 * 512 * 4); img.pixels.foreach_get(px)
T["c_bake_px_minmax"] = (round(min(px[0::4]), 3), round(max(px[0::4]), 3))
print("[10c]", json.dumps({k: v for k, v in T.items() if k.startswith("c_")}), flush=True)
print("[T10_JSON] " + json.dumps(T))
