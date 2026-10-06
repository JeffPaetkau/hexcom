"""Shared helpers for the technique prototypes (Task F).
Imported by proto_*.py which are run as:
    blender -b --python scripts/research/proto_xxx.py -- [samples] [resx]
Everything is metres. Cycles CPU, HDRI + key light, auto-framed camera.
"""
import bpy, bmesh, math, os, sys, time
from mathutils import Vector, Matrix

ROOT = "/home/user/sgt_morgan"
HDRI = os.path.join(ROOT, "assets/hdri/small_hangar_01_2k.hdr")
TEX = os.path.join(ROOT, "assets/textures")
OUT_DIR = os.path.join(ROOT, "renders/research")

def argv():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    samples = int(a[0]) if len(a) > 0 else 96
    resx = int(a[1]) if len(a) > 1 else 1024
    return samples, resx

def reset_scene(samples=96, resx=1024, resy=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = resx
    sc.render.resolution_y = resy or int(resx * 0.75)
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    sc.render.film_transparent = False
    return sc

def world_hdri(strength=1.0, rot_z=0.0):
    w = bpy.data.worlds.new("World"); bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree; nodes, links = nt.nodes, nt.links
    bg = nodes["Background"]; bg.inputs["Strength"].default_value = strength
    env = nodes.new("ShaderNodeTexEnvironment")
    if os.path.exists(HDRI):
        env.image = bpy.data.images.load(HDRI)
    tc = nodes.new("ShaderNodeTexCoord"); mp = nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, rot_z)
    links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    links.new(mp.outputs["Vector"], env.inputs["Vector"])
    links.new(env.outputs["Color"], bg.inputs["Color"])

def key_light(target, direction=(-1, -1, 1.5), dist=1.0, power=None, size=0.4, irradiance=3.0):
    """Area light aimed at target. Power is derived from a target irradiance at the target:
    for a Lambertian area emitter E ~= P / (pi * dist^2), so P = E * pi * dist^2.
    (A 40 W light at 0.6 m gives ~35 W/m^2 -> blows out dark fabrics; 3 W/m^2 is a sane key.)"""
    d = Vector(direction).normalized()
    if power is None:
        power = irradiance * math.pi * dist * dist
    ld = bpy.data.lights.new("Key", "AREA"); ld.energy = power; ld.size = size
    lo = bpy.data.objects.new("Key", ld); bpy.context.collection.objects.link(lo)
    lo.location = Vector(target) + d * dist
    lo.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    return lo

def scene_bounds(objs):
    pts = []
    for o in objs:
        if o.type not in {"MESH", "CURVE"}:
            continue
        for c in o.bound_box:
            pts.append(o.matrix_world @ Vector(c))
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi

def camera_fit(objs, direction=(0, -1, 0.4), margin=1.15, lens=60, name="Cam"):
    """Place a camera looking along -direction at the centre of objs, fitting their bounding sphere."""
    lo, hi = scene_bounds(objs)
    ctr = (lo + hi) * 0.5
    r = (hi - lo).length * 0.5
    cam = bpy.data.cameras.new(name); cam.lens = lens; cam.sensor_width = 36
    sc = bpy.context.scene
    aspect = sc.render.resolution_x / sc.render.resolution_y
    fov = 2 * math.atan(cam.sensor_width / (2 * lens))
    if aspect < 1:
        fov = 2 * math.atan(math.tan(fov / 2) * aspect)
    dist = r * margin / math.sin(fov / 2)
    d = Vector(direction).normalized()
    co = bpy.data.objects.new(name, cam); bpy.context.collection.objects.link(co)
    co.location = ctr + d * dist
    co.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    sc.camera = co
    cam.clip_start = 0.001; cam.clip_end = 100
    return co

def ground(z, size=3.0, color=(0.25, 0.25, 0.25)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    g = bpy.context.active_object; g.name = "Ground"
    m = bpy.data.materials.new("Ground"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = 0.8
    g.data.materials.append(m)
    return g

def poly_count(objs):
    """Evaluated (post-modifier) triangle/face counts."""
    dg = bpy.context.evaluated_depsgraph_get()
    faces = tris = 0
    for o in objs:
        if o.type not in {"MESH", "CURVE"}:
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        if me is None:
            continue
        faces += len(me.polygons)
        tris += sum(len(p.vertices) - 2 for p in me.polygons)
        ev.to_mesh_clear()
    return faces, tris

def render(path, label=""):
    t = time.time()
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    print(f"[proto] rendered {label} -> {path} in {dt:.1f}s")
    return dt

def report(name, t_build, objs, extra=""):
    f, t = poly_count(objs)
    print(f"[proto] {name}: build {t_build:.2f}s, evaluated faces={f} tris={t} {extra}")
    return f, t

# ---------- mesh helpers ----------

def new_mesh_obj(name, bm, smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    if smooth:
        me.shade_smooth()
    return o

def box(name, size, loc=(0, 0, 0), smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    return new_mesh_obj(name, bm, smooth)

def cylinder(name, radius, depth, loc=(0, 0, 0), rot=(0, 0, 0), segs=24, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=radius, radius2=radius, depth=depth)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rot[0], 3, 'X') @ Matrix.Rotation(rot[1], 3, 'Y') @ Matrix.Rotation(rot[2], 3, 'Z'), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    return new_mesh_obj(name, bm, smooth)

def add_bevel(o, width=0.002, segments=3, angle_deg=30, harden=True, clamp=True, profile=0.7):
    m = o.modifiers.new("Bevel", "BEVEL")
    m.width = width; m.segments = segments; m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle_deg); m.use_clamp_overlap = clamp
    m.harden_normals = harden; m.profile = profile
    m.miter_outer = "MITER_ARC"
    return m

def add_subsurf(o, levels=2, render_levels=None):
    m = o.modifiers.new("Subd", "SUBSURF")
    m.levels = levels; m.render_levels = render_levels if render_levels is not None else levels
    return m

def add_weighted_normal(o):
    m = o.modifiers.new("WN", "WEIGHTED_NORMAL"); m.keep_sharp = True
    return m

def add_solidify(o, thickness, offset=-1.0, even=True, rim=True):
    m = o.modifiers.new("Solid", "SOLIDIFY"); m.thickness = thickness; m.offset = offset
    m.use_even_offset = even; m.use_rim = rim
    return m

def smooth_by_angle(o, angle_deg=30):
    """4.1+ replacement for auto smooth: shade smooth + 'Smooth by Angle' modifier."""
    o.data.shade_smooth()
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], selected_editable_objects=[o]):
        try:
            bpy.ops.object.shade_auto_smooth(angle=math.radians(angle_deg))
            return True
        except Exception as e:
            print("[proto] shade_auto_smooth failed:", e)
            return False

def join(objs, name):
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name
    return objs[0]

def boolean(o, cutter, op="DIFFERENCE", solver="EXACT"):
    m = o.modifiers.new("Bool", "BOOLEAN"); m.object = cutter; m.operation = op; m.solver = solver
    cutter.hide_render = True; cutter.hide_viewport = True
    return m

# ---------- material helpers ----------

def find_tex(folder, *keys):
    d = os.path.join(TEX, folder)
    if not os.path.isdir(d):
        return None
    for f in sorted(os.listdir(d)):
        fl = f.lower()
        if fl.endswith((".jpg", ".png")) and all(k in fl for k in keys):
            return os.path.join(d, f)
    return None

def img_node(nodes, links, path, vec_out, noncolor=True):
    n = nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(path)
    if noncolor:
        n.image.colorspace_settings.name = "Non-Color"
    n.extension = "REPEAT"
    links.new(vec_out, n.inputs["Vector"])
    return n

def base_material(name):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree
    return mat, nt.nodes, nt.links, nt.nodes["Principled BSDF"]

def edge_wear_mask(nodes, links, pointiness_mid=0.55, pointiness_width=0.08, ao_dist=0.01, noise_scale=400, noise_detail=4):
    """Returns a socket: 0..1 wear mask = convex edges (pointiness) + broken up by noise + not in cavities (AO).
    Pointiness is Cycles-only and depends on mesh density (needs the subdivided/bevelled geometry)."""
    geo = nodes.new("ShaderNodeNewGeometry")
    ramp = nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = pointiness_mid - pointiness_width / 2
    ramp.inputs["From Max"].default_value = pointiness_mid + pointiness_width / 2
    links.new(geo.outputs["Pointiness"], ramp.inputs["Value"])
    noise = nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = noise_detail; noise.inputs["Roughness"].default_value = 0.6
    nr = nodes.new("ShaderNodeMapRange"); nr.inputs["From Min"].default_value = 0.35; nr.inputs["From Max"].default_value = 0.65
    links.new(noise.outputs["Fac"], nr.inputs["Value"])
    mul = nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    links.new(ramp.outputs["Result"], mul.inputs[0]); links.new(nr.outputs["Result"], mul.inputs[1])
    ao = nodes.new("ShaderNodeAmbientOcclusion"); ao.inputs["Distance"].default_value = ao_dist; ao.samples = 8
    aomul = nodes.new("ShaderNodeMath"); aomul.operation = "MULTIPLY"
    links.new(mul.outputs[0], aomul.inputs[0]); links.new(ao.outputs["AO"], aomul.inputs[1])
    clampn = nodes.new("ShaderNodeClamp")
    links.new(aomul.outputs[0], clampn.inputs["Value"])
    return clampn.outputs["Result"]

def mix_rgb(nodes, links, fac_socket, a_socket_or_color, b_socket_or_color):
    mix = nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MIX"
    if fac_socket is not None:
        links.new(fac_socket, mix.inputs["Factor"])
    for idx, v in ((6, a_socket_or_color), (7, b_socket_or_color)):
        if hasattr(v, "node"):
            links.new(v, mix.inputs[idx])
        else:
            mix.inputs[idx].default_value = (*v, 1.0) if len(v) == 3 else v
    return mix.outputs[2]

def mix_float(nodes, links, fac_socket, a, b):
    mix = nodes.new("ShaderNodeMix"); mix.data_type = "FLOAT"
    links.new(fac_socket, mix.inputs["Factor"])
    for idx, v in ((2, a), (3, b)):
        if hasattr(v, "node"):
            links.new(v, mix.inputs[idx])
        else:
            mix.inputs[idx].default_value = v
    return mix.outputs[0]

def fabric_weave_normal(nodes, links, vec_socket, scale=1200.0, strength=0.5, distance=0.0003):
    """Procedural plain-weave height -> Bump normal. Two orthogonal wave textures (over/under ridges)."""
    w1 = nodes.new("ShaderNodeTexWave"); w1.wave_type = "BANDS"; w1.bands_direction = "X"
    w1.wave_profile = "SIN"; w1.inputs["Scale"].default_value = scale; w1.inputs["Distortion"].default_value = 1.5
    w1.inputs["Detail"].default_value = 2
    w2 = nodes.new("ShaderNodeTexWave"); w2.wave_type = "BANDS"; w2.bands_direction = "Y"
    w2.wave_profile = "SIN"; w2.inputs["Scale"].default_value = scale; w2.inputs["Distortion"].default_value = 1.5
    w2.inputs["Detail"].default_value = 2
    links.new(vec_socket, w1.inputs["Vector"]); links.new(vec_socket, w2.inputs["Vector"])
    mx = nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY"
    links.new(w1.outputs["Fac"], mx.inputs[0]); links.new(w2.outputs["Fac"], mx.inputs[1])
    # add fine fibre noise
    n = nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale * 3; n.inputs["Detail"].default_value = 3
    links.new(vec_socket, n.inputs["Vector"])
    add = nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; add.inputs[1].default_value = 0.8
    links.new(mx.outputs[0], add.inputs[0]); links.new(n.outputs["Fac"], add.inputs[2])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance
    links.new(add.outputs[0], bump.inputs["Height"])
    return bump, mx.outputs[0]


def cordura_material(name, color=(0.115, 0.105, 0.062), weave_scale=1000.0, wear=True, pointiness_mid=0.62, wear_tint=None, rough=0.72):
    """Procedural Cordura/webbing: plain-weave bump, colour variation, Pointiness/AO edge wear, sheen."""
    mat, nodes, links, b = base_material(name)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Sheen Weight"].default_value = 0.35
    b.inputs["Sheen Roughness"].default_value = 0.6
    tc = nodes.new("ShaderNodeTexCoord")
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60; nz.inputs["Detail"].default_value = 6
    links.new(tc.outputs["Object"], nz.inputs["Vector"])
    var = nodes.new("ShaderNodeMapRange"); var.inputs["From Min"].default_value = 0.3; var.inputs["From Max"].default_value = 0.7
    var.inputs["To Min"].default_value = 0.75; var.inputs["To Max"].default_value = 1.15
    links.new(nz.outputs["Fac"], var.inputs["Value"])
    col = nodes.new("ShaderNodeMix"); col.data_type = "RGBA"; col.blend_type = "MULTIPLY"; col.inputs["Factor"].default_value = 1
    col.inputs[6].default_value = (*color, 1)
    links.new(var.outputs["Result"], col.inputs[7])
    out_col = col.outputs[2]
    if wear:
        wm = edge_wear_mask(nodes, links, pointiness_mid=pointiness_mid, pointiness_width=0.12, ao_dist=0.004, noise_scale=300)
        wt = wear_tint or (color[0] * 1.9 + 0.15, color[1] * 1.9 + 0.14, color[2] * 1.7 + 0.12)
        out_col = mix_rgb(nodes, links, wm, out_col, wt)
        links.new(mix_float(nodes, links, wm, rough, rough - 0.17), b.inputs["Roughness"])
    links.new(out_col, b.inputs["Base Color"])
    bump, _ = fabric_weave_normal(nodes, links, tc.outputs["Object"], scale=weave_scale, strength=0.6, distance=0.0002)
    links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat


def polymer_material(name, color=(0.02, 0.02, 0.022), rough=0.4, wear=True, wear_color=(0.18, 0.18, 0.19), micro=True):
    """Black acetal/nylon hardware: micro-grain bump, light pointiness edge wear."""
    mat, nodes, links, b = base_material(name)
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    tc = nodes.new("ShaderNodeTexCoord")
    if wear:
        wm = edge_wear_mask(nodes, links, pointiness_mid=0.66, pointiness_width=0.1, ao_dist=0.003, noise_scale=500)
        links.new(mix_rgb(nodes, links, wm, color, wear_color), b.inputs["Base Color"])
        links.new(mix_float(nodes, links, wm, rough, rough + 0.25), b.inputs["Roughness"])
    if micro:
        n = nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 3000; n.inputs["Detail"].default_value = 2
        links.new(tc.outputs["Object"], n.inputs["Vector"])
        bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.15; bump.inputs["Distance"].default_value = 0.0001
        links.new(n.outputs["Fac"], bump.inputs["Height"]); links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat


def thread_material(name="Thread", color=(0.20, 0.17, 0.10)):
    mat, nodes, links, b = base_material(name)
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = 0.6
    b.inputs["Sheen Weight"].default_value = 0.5
    return mat


def bartack(bm, centre, axis_long, axis_zig, length=0.012, width=0.003, pitch=0.0013, r=0.00035):
    """Zigzag bar-tack made of thread cylinders in bmesh. axis_long: direction of the tack, axis_zig: across."""
    al = Vector(axis_long).normalized(); az = Vector(axis_zig).normalized()
    n = max(3, int(length / pitch))
    c = Vector(centre)
    for j in range(n):
        s = -length / 2 + length * j / (n - 1)
        side = 1 if j % 2 == 0 else -1
        p0 = c + al * s - az * (width / 2) * side
        p1 = c + al * (s + pitch) + az * (width / 2) * side
        d = p1 - p0
        cyl = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r, depth=d.length)
        rot = d.normalized().to_track_quat("Z", "Y").to_matrix()
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=cyl["verts"])
        bmesh.ops.translate(bm, vec=(p0 + p1) * 0.5, verts=cyl["verts"])
    return n


def rounded_rect_profile(w, h, r, segs=4):
    """2D points (x, y) of a rounded rectangle centred on origin, CCW."""
    pts = []
    cx, cy = w / 2 - r, h / 2 - r
    corners = [(cx, cy, 0), (-cx, cy, math.pi / 2), (-cx, -cy, math.pi), (cx, -cy, 3 * math.pi / 2)]
    for ox, oy, a0 in corners:
        for k in range(segs + 1):
            a = a0 + (math.pi / 2) * k / segs
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def loft(name, sections, close_profile=True, cap=False, smooth=True):
    """sections: list of lists of Vector (same length). Builds a quad-strip skin."""
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in sec] for sec in sections]
    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        rng = range(n) if close_profile else range(n - 1)
        for i in rng:
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap and close_profile:
        bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_mesh_obj(name, bm, smooth)
