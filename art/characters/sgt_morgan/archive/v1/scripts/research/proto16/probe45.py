import bpy, sys, os, numpy as np
out = sys.argv[sys.argv.index("--")+1]
sc = bpy.context.scene
print("BLENDER", bpy.app.version_string)
m = bpy.data.materials.new("Probe"); m.use_nodes = True
nt = m.node_tree; p = nt.nodes["Principled BSDF"]
print("PRINCIPLED_INPUTS", [i.name for i in p.inputs])
print("SSS_METHODS", [e.identifier for e in p.bl_rna.properties["subsurface_method"].enum_items])
print("DISTRIBUTIONS", [e.identifier for e in p.bl_rna.properties["distribution"].enum_items])
for t in ["ShaderNodeTexGabor","ShaderNodeBevel","ShaderNodeAmbientOcclusion","ShaderNodeTexNoise","ShaderNodeTexVoronoi","ShaderNodeTexWave","ShaderNodeAttribute","ShaderNodeTexWhiteNoise","ShaderNodeTexBrick"]:
    try:
        n = nt.nodes.new(t); print("NODE", t, "OK", [i.name for i in n.inputs])
        if t=="ShaderNodeTexNoise":
            print("  noise_type", [e.identifier for e in n.bl_rna.properties["noise_type"].enum_items], "dims", [e.identifier for e in n.bl_rna.properties["noise_dimensions"].enum_items], "normalize", hasattr(n,"normalize"))
        if t=="ShaderNodeTexVoronoi":
            print("  features", [e.identifier for e in n.bl_rna.properties["feature"].enum_items], "normalize", hasattr(n,"normalize"))
        if t=="ShaderNodeAttribute":
            print("  attribute_type", [e.identifier for e in n.bl_rna.properties["attribute_type"].enum_items])
        if t=="ShaderNodeTexGabor":
            print("  gabor_type", [e.identifier for e in n.bl_rna.properties["gabor_type"].enum_items])
    except Exception as e:
        print("NODE", t, "FAIL", e)
vs = sc.view_settings
print("VIEW_TRANSFORMS", [e.identifier for e in vs.bl_rna.properties["view_transform"].enum_items_static][:0])
vs.view_transform = "AgX"
try:
    print("LOOKS", [e.identifier for e in vs.bl_rna.properties["look"].enum_items])
except Exception as e:
    print("LOOKS_FAIL", e)
# --- bake test: emission linear 0.18 into an sRGB byte image, then into a float Non-Color image
bpy.ops.mesh.primitive_plane_add(size=1.0)
ob = bpy.context.active_object
ob.data.materials.append(m)
for n in list(nt.nodes):
    if n.type not in ("OUTPUT_MATERIAL",): nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.18, 0.18, 0.18, 1); em.inputs["Strength"].default_value = 1.0
nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 1
vs.view_transform = "AgX"; vs.look = "AgX - Medium High Contrast"
res = {}
for name, fb, cs in (("bake_srgb8", False, "sRGB"), ("bake_lin32", True, "Non-Color")):
    img = bpy.data.images.new(name, 64, 64, alpha=False, float_buffer=fb)
    img.colorspace_settings.name = cs
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    nt.nodes.active = tex; tex.select = True
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    sc.cycles.bake_type = "EMIT"
    bpy.ops.object.bake(type="EMIT", margin=2)
    px = np.array(img.pixels[:]).reshape(64,64,4)
    res[name] = px[32,32,:3]
    path = os.path.join(out, name + (".png" if not fb else ".exr"))
    img.filepath_raw = path; img.file_format = "PNG" if not fb else "OPEN_EXR"
    img.save()
    nt.nodes.remove(tex)
print("BAKE_PIXELS_IN_BLENDER", {k: [round(float(x),4) for x in v] for k,v in res.items()})
