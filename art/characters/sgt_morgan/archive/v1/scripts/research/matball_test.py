"""Blender headless material-ball test: prove the downloaded PBR sets + HDRI load and render on CPU.
blender -b --python matball_test.py -- <assets_root> <out_png> [samples] [res_x]
"""
import bpy, sys, os, time, math

argv = sys.argv[sys.argv.index("--") + 1:]
ROOT, OUT = argv[0], argv[1]
SAMPLES = int(argv[2]) if len(argv) > 2 else 64
RESX = int(argv[3]) if len(argv) > 3 else 1280
TEX = os.path.join(ROOT, "textures")

def find(folder, *keys):
    for f in sorted(os.listdir(folder)):
        fl = f.lower()
        if fl.endswith((".jpg", ".png")) and all(k in fl for k in keys):
            return os.path.join(folder, f)
    return None

def maps_for(aid):
    d = os.path.join(TEX, aid)
    return {
        "color": find(d, "_color") or find(d, "_diff"),
        "normal": find(d, "normalgl") or find(d, "nor_gl"),
        "rough": find(d, "rough"),
        "disp": find(d, "displacement") or find(d, "_disp"),
        "ao": find(d, "ambientocclusion") or find(d, "_ao_"),
        "metal": find(d, "metalness") or find(d, "_metal_"),
        "arm": find(d, "_arm_"),
    }

def pbr_material(name, aid, scale=1.0, tint=None, metallic=None, rough_mul=1.0, bump=0.3):
    m = maps_for(aid)
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; nodes, links = nt.nodes, nt.links
    bsdf = nodes["Principled BSDF"]
    tc = nodes.new("ShaderNodeTexCoord"); mp = nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    links.new(tc.outputs["UV"], mp.inputs["Vector"])
    def img(path, noncolor):
        n = nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(path)
        if noncolor: n.image.colorspace_settings.name = "Non-Color"
        links.new(mp.outputs["Vector"], n.inputs["Vector"]); return n
    if m["color"]:
        c = img(m["color"], False)
        if tint:
            mix = nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0; mix.inputs[7].default_value = (*tint, 1.0)
            links.new(c.outputs["Color"], mix.inputs[6]); links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        else:
            links.new(c.outputs["Color"], bsdf.inputs["Base Color"])
    if m["arm"] and not m["rough"]:
        a = img(m["arm"], True); sep = nodes.new("ShaderNodeSeparateColor")
        links.new(a.outputs["Color"], sep.inputs["Color"]); links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        if metallic is None: links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
    elif m["rough"]:
        r = img(m["rough"], True)
        if rough_mul != 1.0:
            mth = nodes.new("ShaderNodeMath"); mth.operation = "MULTIPLY"; mth.inputs[1].default_value = rough_mul
            links.new(r.outputs["Color"], mth.inputs[0]); links.new(mth.outputs[0], bsdf.inputs["Roughness"])
        else:
            links.new(r.outputs["Color"], bsdf.inputs["Roughness"])
    if metallic is not None:
        bsdf.inputs["Metallic"].default_value = metallic
    elif m["metal"]:
        links.new(img(m["metal"], True).outputs["Color"], bsdf.inputs["Metallic"])
    if m["normal"]:
        nm = nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.0
        links.new(img(m["normal"], True).outputs["Color"], nm.inputs["Color"])
        if m["disp"] and bump > 0:
            bp = nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.002
            links.new(img(m["disp"], True).outputs["Color"], bp.inputs["Height"]); links.new(nm.outputs["Normal"], bp.inputs["Normal"])
            links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
        else:
            links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"
scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.render.resolution_x = RESX; scene.render.resolution_y = int(RESX * 9 / 16); scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"

# world HDRI
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
wn = world.node_tree.nodes; wl = world.node_tree.links
env = wn.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(ROOT, "hdri", "empty_warehouse_01_2k.hdr"))
bg = wn["Background"]; bg.inputs["Strength"].default_value = 1.0
wl.new(env.outputs["Color"], bg.inputs["Color"])
wmap = wn.new("ShaderNodeMapping"); wtc = wn.new("ShaderNodeTexCoord")
wmap.inputs["Rotation"].default_value = (0, 0, math.radians(90))
wl.new(wtc.outputs["Generated"], wmap.inputs["Vector"]); wl.new(wmap.outputs["Vector"], env.inputs["Vector"])

# floor
bpy.ops.mesh.primitive_plane_add(size=6); floor = bpy.context.object; floor.name = "Floor"
floor.data.materials.append(pbr_material("Floor.Concrete", "hangar_concrete_floor", scale=3.0, rough_mul=0.6, bump=0.1))

# material balls (id, label, kwargs)
balls = [
    ("Fabric048", dict(scale=6, tint=(0.35, 0.30, 0.22))),          # cordura tinted olive-brown
    ("Fabric061", dict(scale=6, tint=(0.33, 0.29, 0.22))),
    ("denim_fabric_06", dict(scale=5, tint=(0.25, 0.22, 0.20))),    # dark twill
    ("knitted_fleece", dict(scale=4, tint=(0.45, 0.40, 0.33))),     # gaiter
    ("Leather037", dict(scale=3, tint=(0.18, 0.17, 0.16))),         # black boot leather
    ("Leather032", dict(scale=3)),
    ("Rubber004", dict(scale=3)),
    ("Metal046B", dict(scale=2, metallic=1.0)),                     # dark rifle metal
    ("Metal050C", dict(scale=2, metallic=1.0)),
    ("Metal063", dict(scale=2)),
    ("Plastic012B", dict(scale=3, metallic=0.0)),
    ("Plastic018B", dict(scale=3, metallic=0.0, tint=(0.55, 0.45, 0.35))),  # tan polymer
    ("Metal027", dict(scale=2)),
    ("blue_metal_plate", dict(scale=1)),
    ("book_pattern", dict(scale=6)),
    ("polar_fleece", dict(scale=4, tint=(0.4, 0.37, 0.3))),
]
cols = 8
for i, (aid, kw) in enumerate(balls):
    r, c = divmod(i, cols)
    x = (c - (cols - 1) / 2) * 0.55; y = -r * 0.6 + 0.3
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, segments=64, ring_count=32, location=(x, y, 0.22))
    ob = bpy.context.object; ob.name = "Ball." + aid
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(pbr_material("Mat." + aid, aid, **kw))

# camera + key light (warm key upper-left like the reference)
cam_data = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_data); scene.collection.objects.link(cam)
cam.location = (0, -3.2, 1.6); cam.rotation_euler = (math.radians(66), 0, 0); cam_data.lens = 50
scene.camera = cam
key = bpy.data.lights.new("Key", "AREA"); key.energy = 400; key.size = 1.0; key.color = (1.0, 0.85, 0.65)
ko = bpy.data.objects.new("Key", key); scene.collection.objects.link(ko)
ko.location = (-2.5, -2.0, 2.5); ko.rotation_euler = (math.radians(50), 0, math.radians(-50))
rim = bpy.data.lights.new("Rim", "AREA"); rim.energy = 250; rim.size = 2.0; rim.color = (0.6, 0.75, 1.0)
ro = bpy.data.objects.new("Rim", rim); scene.collection.objects.link(ro)
ro.location = (2.5, 2.0, 2.0); ro.rotation_euler = (math.radians(-55), 0, math.radians(130))

t_setup = time.time() - t0
scene.render.image_settings.file_format = "PNG"; scene.render.filepath = OUT
t1 = time.time(); bpy.ops.render.render(write_still=True); t_render = time.time() - t1
print(f"MATBALL setup {t_setup:.1f}s render {t_render:.1f}s samples={SAMPLES} res={RESX}x{scene.render.resolution_y} -> {OUT}")
