"""Prototype 1: MOLLE/PALS panel. 200 x 150 mm Cordura panel, 4 rows of 25 mm webbing,
bar-tacked every 38 mm, sag between stitches, running edge stitch geometry, weave normal,
Pointiness/AO edge wear. Panel lies in the XZ plane, front faces -Y (camera side).
blender -b --python proto_molle.py -- [samples] [resx]
"""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import proto_common as pc

SAMPLES, RESX = pc.argv()
pc.reset_scene(SAMPLES, RESX)
pc.world_hdri(0.6, rot_z=math.radians(90))
t0 = time.time()

W, H = 0.20, 0.15          # panel size
WEB_H = 0.025              # webbing height
PITCH = 0.035              # row pitch (centres)
STITCH = 0.038             # bar-tack spacing
X0, X1 = 0.005, 0.195      # webbing span -> 6 bar-tacks at 0.005 + k*0.038
SAG = 0.0035               # max lift between stitches
WEB_T = 0.0013             # webbing thickness
ROWS = [0.0225 + i * PITCH for i in range(4)]

def sag_at(x):
    t = ((x - X0) % STITCH) / STITCH
    return SAG * math.sin(math.pi * t) ** 0.8   # flatter top than pure sine

# ---------- panel ----------
bm = bmesh.new()
nx, nz = 40, 30
grid = bmesh.ops.create_grid(bm, x_segments=nx, y_segments=nz, size=0.5)
uv = bm.loops.layers.uv.new("UVMap")
for v in bm.verts:
    x, z = (v.co.x + 0.5) * W, (v.co.y + 0.5) * H
    v.co = Vector((x, 0.0, z))
for f in bm.faces:
    for l in f.loops:
        l[uv].uv = (l.vert.co.x / W, l.vert.co.z / H)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:               # make front face -Y
    if f.normal.y > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces); break
panel = pc.new_mesh_obj("Molle.Panel", bm)
pc.add_solidify(panel, 0.0015, offset=1.0)   # thickness goes to +Y (behind)
pc.add_bevel(panel, 0.0006, 2)

# ---------- webbing rows (one object, dense in X for sag) ----------
bm = bmesh.new()
uv = bm.loops.layers.uv.new("UVMap")
NSEG = 190
for zc in ROWS:
    rows_v = []
    for j in range(7):
        zz = zc - WEB_H / 2 + WEB_H * j / 6
        edge_curl = 0.0004 * (1 - (abs(j - 3) / 3) ** 2)   # middle lifts slightly more than edges
        row = []
        for i in range(NSEG + 1):
            x = X0 + (X1 - X0) * i / NSEG
            y = -(sag_at(x) + edge_curl * (sag_at(x) / SAG)) - 0.0002
            row.append(bm.verts.new((x, y, zz)))
        rows_v.append(row)
    for j in range(6):
        for i in range(NSEG):
            f = bm.faces.new((rows_v[j][i], rows_v[j][i + 1], rows_v[j + 1][i + 1], rows_v[j + 1][i]))
            for l in f.loops:
                l[uv].uv = (l.vert.co.x / 0.025, (l.vert.co.z - zc) / WEB_H + 0.5)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    if f.normal.y > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces); break
web = pc.new_mesh_obj("Molle.Webbing", bm)
pc.add_solidify(web, WEB_T, offset=1.0)
pc.add_bevel(web, 0.0005, 2, angle_deg=60)

# ---------- stitches: bar-tacks + running edge stitch, thread cylinders ----------
bm = bmesh.new()
THREAD_R = 0.00035
def thread(p0, p1):
    d = Vector(p1) - Vector(p0)
    L = d.length
    cyl = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=THREAD_R, radius2=THREAD_R, depth=L)
    verts = cyl["verts"]
    rot = d.normalized().to_track_quat("Z", "Y").to_matrix()
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=verts)
    bmesh.ops.translate(bm, vec=(Vector(p0) + Vector(p1)) * 0.5, verts=verts)
n_thread = 0
for zc in ROWS:
    # bar-tacks: zigzag of horizontal thread passes 3 mm wide, 22 mm tall, 1.3 mm pitch
    for k in range(6):
        x = X0 + k * STITCH
        yfront = -0.0002 - WEB_T - 0.0002
        nz = 17
        for j in range(nz):
            zz = zc - 0.011 + 0.022 * j / (nz - 1)
            dx = 0.0015 if j % 2 == 0 else -0.0015
            thread((x - dx, yfront, zz), (x + dx, yfront, zz + 0.0013)); n_thread += 1
    # running stitch along top and bottom edges: 2.2 mm stitch, 0.8 mm gap, 1.8 mm inside the edge
    for zz in (zc - WEB_H / 2 + 0.0018, zc + WEB_H / 2 - 0.0018):
        x = X0 + 0.003
        while x + 0.0022 < X1 - 0.002:
            y0 = -(sag_at(x)) - WEB_T - 0.0005
            y1 = -(sag_at(x + 0.0022)) - WEB_T - 0.0005
            thread((x, y0, zz), (x + 0.0022, y1, zz)); n_thread += 1
            x += 0.0030
stitch = pc.new_mesh_obj("Molle.Stitches", bm)
print(f"[proto] thread segments: {n_thread}")

# ---------- materials ----------
def cordura(name, color, use_texture=True, weave_scale=1400.0):
    mat, nodes, links, b = pc.base_material(name)
    b.inputs["Roughness"].default_value = 0.72
    b.inputs["Sheen Weight"].default_value = 0.35
    b.inputs["Sheen Roughness"].default_value = 0.6
    tc = nodes.new("ShaderNodeTexCoord")
    wear = pc.edge_wear_mask(nodes, links, pointiness_mid=0.62, pointiness_width=0.12, ao_dist=0.004, noise_scale=300)
    # dirt/variation on base colour
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60; nz.inputs["Detail"].default_value = 6
    links.new(tc.outputs["Object"], nz.inputs["Vector"])
    var = nodes.new("ShaderNodeMapRange"); var.inputs["From Min"].default_value = 0.3; var.inputs["From Max"].default_value = 0.7
    var.inputs["To Min"].default_value = 0.75; var.inputs["To Max"].default_value = 1.15
    links.new(nz.outputs["Fac"], var.inputs["Value"])
    col = nodes.new("ShaderNodeMix"); col.data_type = "RGBA"; col.blend_type = "MULTIPLY"; col.inputs["Factor"].default_value = 1
    col.inputs[6].default_value = (*color, 1)
    links.new(var.outputs["Result"], col.inputs[7])
    worn = pc.mix_rgb(nodes, links, wear, col.outputs[2], (color[0] * 1.9 + 0.15, color[1] * 1.9 + 0.14, color[2] * 1.7 + 0.12))
    links.new(worn, b.inputs["Base Color"])
    rough = pc.mix_float(nodes, links, wear, 0.72, 0.55)
    links.new(rough, b.inputs["Roughness"])
    normal_path = pc.find_tex("3dtextures_Fabric_Nylon_Weave_001", "normal")
    if use_texture and normal_path:
        mp = nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (5, 3.75, 1)   # tile = 40 mm
        links.new(tc.outputs["UV"], mp.inputs["Vector"])
        n = pc.img_node(nodes, links, normal_path, mp.outputs["Vector"])
        nm = nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.2
        links.new(n.outputs["Color"], nm.inputs["Color"])
        links.new(nm.outputs["Normal"], b.inputs["Normal"])
        mat["weave"] = "texture 3dtextures nylon normal, 40 mm tile"
    else:
        bump, _ = pc.fabric_weave_normal(nodes, links, tc.outputs["Object"], scale=weave_scale, strength=0.6, distance=0.0002)
        links.new(bump.outputs["Normal"], b.inputs["Normal"])
        mat["weave"] = f"procedural wave x wave, scale {weave_scale}"
    return mat

OLIVE = (0.115, 0.105, 0.062)
panel.data.materials.append(cordura("Molle.Cordura.Tex", OLIVE, use_texture=True))
web.data.materials.append(cordura("Molle.Webbing.Proc", (0.125, 0.112, 0.066), use_texture=False, weave_scale=1000.0))
thr, nodes, links, b = pc.base_material("Molle.Thread")
b.inputs["Base Color"].default_value = (0.20, 0.17, 0.10, 1); b.inputs["Roughness"].default_value = 0.6
b.inputs["Sheen Weight"].default_value = 0.5
stitch.data.materials.append(thr)

t_build = time.time() - t0
objs = [panel, web, stitch]
pc.report("MOLLE panel", t_build, objs)

# ---------- camera + light: closeup on two rows ----------
pc.key_light((0.1, 0, 0.075), direction=(-0.6, -1, 0.9), dist=0.6, power=40, size=0.3)
pc.camera_fit(objs, direction=(0.25, -1, 0.35), margin=0.75, lens=70)
pc.render(os.path.join(pc.OUT_DIR, "proto_molle.png"), "molle")
# very tight detail crop
pc.camera_fit([web], direction=(0.35, -1, 0.25), margin=0.22, lens=85, name="CamDetail")
pc.render(os.path.join(pc.OUT_DIR, "proto_molle_detail.png"), "molle detail")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(pc.OUT_DIR, "proto_molle.blend"))
