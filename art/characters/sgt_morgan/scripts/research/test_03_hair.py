"""Test 3: headless hair.
(a) legacy particle hair on a UV sphere scalp: 2000 parents, 20 interpolated children,
    length 0.03, clump + roughness, Principled Hair BSDF, Cycles strand render, closeup.
(b) new Curves hair (bpy.data.hair_curves) built from Python + conversion operator test.
Run: blender -b --python test_03_hair.py
"""
import bpy, sys, time, math, os, json, random
import mathutils

OUT = "/home/user/sgt_morgan/renders/research"
os.makedirs(OUT, exist_ok=True)
T = {}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 128
sc.cycles.use_denoising = True
sc.render.resolution_x = 1024
sc.render.resolution_y = 1024
# Cycles curve settings (4.x): scene.cycles_curves.shape = 'RIBBONS'|'THICK'
sc.cycles_curves.shape = "THICK"
sc.cycles_curves.subdivisions = 2
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.25, 0.25, 0.28, 1)
for name, loc, e in (("Key", (0.4, -0.5, 0.6), 60), ("Fill", (-0.5, -0.3, 0.3), 20), ("Rim", (0.1, 0.5, 0.5), 50)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = e; ld.size = 0.4
    lo = bpy.data.objects.new(name, ld); lo.location = loc
    sc.collection.objects.link(lo)
    lo.rotation_euler = (mathutils.Vector((0, 0, 0.1)) - lo.location).to_track_quat('-Z', 'Y').to_euler()

# scalp
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.1, location=(0, 0, 0))
scalp = bpy.context.active_object; scalp.name = "Scalp"
bpy.ops.object.shade_smooth()
skin = bpy.data.materials.new("Skin"); skin.use_nodes = True
skin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.55, 0.45, 1)
scalp.data.materials.append(skin)
# density group: upper hemisphere only
vg = scalp.vertex_groups.new(name="HairDensity")
vg.add([v.index for v in scalp.data.vertices if v.co.z > 0.01], 1.0, "REPLACE")

# hair material
hm = bpy.data.materials.new("Hair"); hm.use_nodes = True
nt = hm.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
ph = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
ph.parametrization = "MELANIN"
ph.inputs["Melanin"].default_value = 0.9
ph.inputs["Melanin Redness"].default_value = 0.3
ph.inputs["Roughness"].default_value = 0.3
ph.inputs["Radial Roughness"].default_value = 0.3
ph.inputs["Random Roughness"].default_value = 0.2
try:
    ph.model = "CHIANG"   # 'CHIANG' or 'HUANG' in 4.x
except Exception as e:
    print("hair model attr:", e)
nt.links.new(ph.outputs[0], out.inputs[0])
scalp.data.materials.append(hm)  # slot index 1

# ---------------------------------------------------------------- (a) particle hair
t0 = time.time()
pmod = scalp.modifiers.new("HairPS", "PARTICLE_SYSTEM")
psys = scalp.particle_systems[-1]
ps = psys.settings
ps.type = "HAIR"
ps.count = 2000
ps.hair_length = 0.03
ps.hair_step = 5
ps.use_advanced_hair = True
ps.child_type = "INTERPOLATED"
ps.child_percent = 20          # viewport children
ps.rendered_child_count = 20   # render children
ps.clump_factor = 0.6
ps.clump_shape = 0.2
ps.roughness_1 = 0.004
ps.roughness_1_size = 0.5
ps.roughness_endpoint = 0.002
ps.root_radius = 1.0
ps.tip_radius = 0.2
ps.radius_scale = 0.005        # m; 0.005*root_radius*... Cycles uses this as strand width scale
ps.use_close_tip = True
ps.material = 2                # second material slot (1-based)
psys.vertex_group_density = "HairDensity"
# force evaluation
sc.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
ev = scalp.evaluated_get(dg)
n_particles = len(ev.particle_systems[0].particles)
n_children = len(ev.particle_systems[0].child_particles)
T["a_setup_s"] = round(time.time() - t0, 2)
T["a_parents"] = n_particles
T["a_children"] = n_children
print(f"[3a] particle hair parents={n_particles} children={n_children} setup {T['a_setup_s']}s", flush=True)

cd = bpy.data.cameras.new("Cam"); cd.lens = 85
cam = bpy.data.objects.new("Cam", cd); cam.location = (0.22, -0.32, 0.22)
cam.rotation_euler = (mathutils.Vector((0, 0, 0.04)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.collection.objects.link(cam); sc.camera = cam

t0 = time.time()
sc.render.filepath = f"{OUT}/t03_hair_particles.png"
bpy.ops.render.render(write_still=True)
T["a_render_s"] = round(time.time() - t0, 1)
print(f"[3a] render {T['a_render_s']}s", flush=True)

# ---------------------------------------------------------------- (b) Curves hair from Python
t0 = time.time()
hc = bpy.data.hair_curves.new("HairCurves")
N = 3000
PTS = 6
hc.add_curves([PTS] * N)
random.seed(1)
# positions: sample upper hemisphere of scalp, grow outward with slight droop
pos = []
for i in range(N):
    # uniform-ish on hemisphere
    u = random.random(); v = random.random()
    theta = math.acos(1 - u * 0.9)       # 0..~84deg from +Z
    phi = 2 * math.pi * v
    n = mathutils.Vector((math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)))
    root = n * 0.1
    for k in range(PTS):
        t = k / (PTS - 1)
        p = root + n * (0.03 * t) + mathutils.Vector((0, 0, -0.012)) * t * t  # droop
        pos.extend(p[:])
hc.points.foreach_set("position", pos)
hc.surface = scalp
# radius attribute (optional)
if "radius" not in hc.attributes:
    hc.attributes.new("radius", "FLOAT", "POINT")
radii = []
for i in range(N):
    for k in range(PTS):
        radii.append(0.0006 * (1 - 0.8 * k / (PTS - 1)))
hc.attributes["radius"].data.foreach_set("value", radii)
hc.materials.append(hm)
hco = bpy.data.objects.new("HairCurves", hc)
sc.collection.objects.link(hco)
hco.parent = scalp
T["b_build_s"] = round(time.time() - t0, 2)
T["b_curves"] = len(hc.curves); T["b_points"] = len(hc.points)
print(f"[3b] Curves hair built: {len(hc.curves)} curves, {len(hc.points)} points in {T['b_build_s']}s", flush=True)

# hide particle hair for the second render
pmod.show_render = False
t0 = time.time()
sc.render.filepath = f"{OUT}/t03_hair_curves.png"
bpy.ops.render.render(write_still=True)
T["b_render_s"] = round(time.time() - t0, 1)
print(f"[3b] render {T['b_render_s']}s", flush=True)

# (c) operator: convert particle system -> Curves (needs context override)
pmod.show_render = True
try:
    with bpy.context.temp_override(object=scalp, active_object=scalp, selected_objects=[scalp]):
        r = bpy.ops.curves.convert_from_particle_system()
    conv = [o for o in sc.objects if o.type == "CURVES" and o is not hco]
    T["c_convert_ok"] = True
    T["c_convert_info"] = f"{r} -> {[(o.name, len(o.data.curves)) for o in conv]}"
except Exception as e:
    T["c_convert_ok"] = False
    T["c_convert_info"] = repr(e)
print("[3c] convert_from_particle_system:", T["c_convert_ok"], T["c_convert_info"], flush=True)

# (d) Geometry-nodes hair modifier on Curves object: can we add a node group programmatically?
try:
    ng = bpy.data.node_groups.new("HairFrizz", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput")
    setpos = ng.nodes.new("GeometryNodeSetPosition")
    noise = ng.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 200.0
    sub = ng.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    scale = ng.nodes.new("ShaderNodeVectorMath"); scale.operation = "SCALE"; scale.inputs["Scale"].default_value = 0.004
    spl = ng.nodes.new("GeometryNodeSplineParameter")
    mul = ng.nodes.new("ShaderNodeVectorMath"); mul.operation = "SCALE"
    ng.links.new(gi.outputs[0], setpos.inputs["Geometry"])
    ng.links.new(noise.outputs["Color"], sub.inputs[0])
    ng.links.new(sub.outputs[0], scale.inputs[0])
    ng.links.new(scale.outputs[0], mul.inputs[0])
    ng.links.new(spl.outputs["Factor"], mul.inputs["Scale"])
    ng.links.new(mul.outputs[0], setpos.inputs["Offset"])
    ng.links.new(setpos.outputs[0], go.inputs[0])
    gm = hco.modifiers.new("Frizz", "NODES"); gm.node_group = ng
    dg = bpy.context.evaluated_depsgraph_get()
    T["d_gn_on_curves_ok"] = True
    T["d_gn_points"] = len(hco.evaluated_get(dg).data.points)
except Exception as e:
    T["d_gn_on_curves_ok"] = False; T["d_gn_info"] = repr(e)
print("[3d] GN frizz on Curves:", T.get("d_gn_on_curves_ok"), T.get("d_gn_points", T.get("d_gn_info")), flush=True)

bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/t03_hair.blend")
print("[T03_JSON] " + json.dumps(T))
