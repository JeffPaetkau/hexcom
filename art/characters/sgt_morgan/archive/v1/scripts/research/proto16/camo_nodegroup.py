"""Prototype of MG.Camo.Blotch4 (spec 16 §4.6). Bakes: field F (float), albedo at ref scale, macro.
Usage: blender -b --factory-startup --python camo_ng.py -- <outdir> <stage> [t1 t2 t3]
stage 'field' -> F_1m.exr (1 m at 1024 px) ; stage 'albedo' -> camo_ref.png (1 m at 472 px), camo_2m.png, camo_macro.png"""
import bpy, sys, os, json, numpy as np
argv = sys.argv[sys.argv.index("--")+1:]
out, stage = argv[0], argv[1]
T = [float(x) for x in argv[2:5]] if len(argv) >= 5 else [0.45, 0.52, 0.58]
P = json.load(open(os.path.join(out, "camo_params.json")))
def srgb2lin(h):
    c = [int(h[i:i+2], 16)/255 for i in (1,3,5)]
    return [x/12.92 if x <= 0.04045 else ((x+0.055)/1.055)**2.4 for x in c] + [1.0]
def sock(ng, name, kind, io, default=None):
    s = ng.interface.new_socket(name=name, in_out=io, socket_type=kind)
    if default is not None and io == 'INPUT': s.default_value = default
    return s
def build_group():
    ng = bpy.data.node_groups.new("MG.Camo.Blotch4", "ShaderNodeTree")
    sock(ng, "Vector", "NodeSocketVector", "INPUT")
    sock(ng, "Seed", "NodeSocketFloat", "INPUT", 7.0)
    for i, h in enumerate(P["tones"]): sock(ng, f"T{i}", "NodeSocketColor", "INPUT", srgb2lin(h))
    for i, t in enumerate(T): sock(ng, f"Cut{i+1}", "NodeSocketFloat", "INPUT", t)
    sock(ng, "Edge", "NodeSocketFloat", "INPUT", P["edge"])
    sock(ng, "Dither", "NodeSocketFloat", "INPUT", P["dither"])
    sock(ng, "Color", "NodeSocketColor", "OUTPUT"); sock(ng, "Field", "NodeSocketFloat", "OUTPUT"); sock(ng, "Tone", "NodeSocketFloat", "OUTPUT")
    N, L = ng.nodes, ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    def noise(vec, scale, detail, rough, wofs, dims="4D"):
        n = N.new("ShaderNodeTexNoise"); n.noise_dimensions = dims; n.noise_type = "FBM"; n.normalize = True
        n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough; n.inputs["Lacunarity"].default_value = 2.0
        L.new(vec, n.inputs["Vector"])
        if dims == "4D":
            a = N.new("ShaderNodeMath"); a.operation = "ADD"; a.inputs[1].default_value = wofs
            L.new(gi.outputs["Seed"], a.inputs[0]); L.new(a.outputs[0], n.inputs["W"])
        return n
    def math(op, a, b=None, v=None):
        m = N.new("ShaderNodeMath"); m.operation = op
        (L.new(a, m.inputs[0]) if not isinstance(a, (int, float)) else m.inputs[0].__setattr__("default_value", a))
        if b is not None:
            (L.new(b, m.inputs[1]) if not isinstance(b, (int, float)) else m.inputs[1].__setattr__("default_value", b))
        return m.outputs[0]
    V = gi.outputs["Vector"]
    # domain warp: colour noise (3 channels) centred, x 2*amp metres
    w = noise(V, 1000/P["warp_mm"], 2.0, 0.5, 11.3)
    sub = N.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    L.new(w.outputs["Color"], sub.inputs[0])
    sc = N.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs["Scale"].default_value = 2*P["warp_amp_mm"]/1000
    L.new(sub.outputs[0], sc.inputs[0])
    add = N.new("ShaderNodeVectorMath"); add.operation = "ADD"; L.new(V, add.inputs[0]); L.new(sc.outputs[0], add.inputs[1])
    Vw = add.outputs[0]
    B = noise(Vw, 1000/P["blotch_mm"], P["blotch_detail"], P["blotch_rough"], 1.7)
    M = noise(V, 1000/P["macro_mm"], 1.0, 0.5, 3.1)
    S = noise(Vw, 1000/P["speck_mm"], 1.0, 0.5, 5.3)
    F = math("ADD", math("ADD", math("MULTIPLY", B.outputs["Fac"], P["wB"]), math("MULTIPLY", M.outputs["Fac"], P["wM"])), math("MULTIPLY", S.outputs["Fac"], P["wS"]))
    # print grain (ink on yarn): 3D noise at yarn scale, centred, x Dither
    G = noise(V, 1000/P["grain_mm"], 0.0, 0.5, 0.0, dims="3D")
    Gc = math("MULTIPLY", math("SUBTRACT", G.outputs["Fac"], 0.5), gi.outputs["Dither"])
    Fd = math("ADD", F, Gc)
    col = gi.outputs["T0"]; tone = None
    for k in (1, 2, 3):
        mr = N.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"
        L.new(Fd, mr.inputs["Value"])
        lo = math("SUBTRACT", gi.outputs[f"Cut{k}"], gi.outputs["Edge"]); hi = math("ADD", gi.outputs[f"Cut{k}"], gi.outputs["Edge"])
        L.new(lo, mr.inputs["From Min"]); L.new(hi, mr.inputs["From Max"])
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MIX"
        L.new(mr.outputs["Result"], mx.inputs["Factor"])
        L.new(col, [s for s in mx.inputs if s.name == "A" and s.type == "RGBA"][0])
        L.new(gi.outputs[f"T{k}"], [s for s in mx.inputs if s.name == "B" and s.type == "RGBA"][0])
        col = [s for s in mx.outputs if s.type == "RGBA"][0]
        tone = mr.outputs["Result"] if tone is None else math("ADD", tone, mr.outputs["Result"])
    L.new(col, go.inputs["Color"]); L.new(F, go.inputs["Field"]); L.new(tone, go.inputs["Tone"])
    return ng
ng = build_group()
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.render.threads_mode = "FIXED"; sc.render.threads = 3
def plane(size_m, name):
    bpy.ops.mesh.primitive_plane_add(size=1.0); ob = bpy.context.active_object; ob.name = name
    ob["size_m"] = size_m
    return ob
def material(ob, output, vec_scale=1.0, vec_offset=(0, 0, 0)):
    m = bpy.data.materials.new(ob.name + ".Mat"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL": nt.nodes.remove(n)
    uv = nt.nodes.new("ShaderNodeUVMap")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Location"].default_value = vec_offset
    mp.inputs["Scale"].default_value = (ob["size_m"][0], ob["size_m"][1], 1.0)
    nt.links.new(uv.outputs[0], mp.inputs["Vector"])
    g = nt.nodes.new("ShaderNodeGroup"); g.node_tree = ng
    nt.links.new(mp.outputs[0], g.inputs["Vector"])
    em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(g.outputs[output], em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    ob.data.materials.append(m); return m
def bake(ob, m, w, h, fb, cs, path, samples):
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False, float_buffer=fb)
    img.colorspace_settings.name = cs
    tex = m.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = img
    m.node_tree.nodes.active = tex; tex.select = True
    for o in bpy.context.view_layer.objects: o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    sc.cycles.samples = samples
    bpy.ops.object.bake(type="EMIT", margin=0)
    img.filepath_raw = path; img.file_format = "OPEN_EXR" if fb else "PNG"; img.save()
    print("BAKED", path)
import time; t0 = time.time()
if stage == "field":
    ob = plane((2.0, 2.0), "FieldPlane"); m = material(ob, "Field")
    bake(ob, m, 2048, 2048, True, "Non-Color", os.path.join(out, "F_2m.exr"), 1)
else:
    ob = plane((1.0, 1.0), "RefPlane"); m = material(ob, "Color")
    bake(ob, m, 472, 472, False, "sRGB", os.path.join(out, "camo_ref.png"), 32)
    ob2 = plane((2.0, 2.0), "BigPlane"); m2 = material(ob2, "Color", vec_offset=(3.0, 0, 0))
    bake(ob2, m2, 1024, 1024, False, "sRGB", os.path.join(out, "camo_2m.png"), 16)
    ob3 = plane((0.1, 0.1), "MacroPlane"); m3 = material(ob3, "Color", vec_offset=(0.30, 0.40, 0))
    bake(ob3, m3, 800, 800, False, "sRGB", os.path.join(out, "camo_macro.png"), 4)
    ob4 = plane((1.0, 1.0), "TonePlane"); m4 = material(ob4, "Tone")
    bake(ob4, m4, 472, 472, True, "Non-Color", os.path.join(out, "tone_ref.exr"), 16)
print("TIME", round(time.time()-t0, 1))
