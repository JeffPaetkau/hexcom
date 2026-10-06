"""Prototype 5: 10-eyelet boot lace routing. Two Bezier ends criss-crossing through alternating
eyelets, round bevel, dips behind the eyelet plane at each eyelet, alternating over/under lift at
the crossings, procedural braid bump via curve UVs (use_uv_as_generated). Metal grommets + a dark
leather stay/tongue for context. Faces -Y. blender -b --python proto_lace.py -- [samples] [resx]
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

N = 5                   # eyelet pairs -> 10 eyelets
PITCH = 0.022
TILT = 0.35             # dy/dz of the lacing plane (leans back going up)
def surf_y(z):
    return -0.050 + TILT * z
nrm = Vector((0, -1, TILT)).normalized()   # outward normal of the lacing plane
nrm = Vector((0, -1, -TILT)); nrm.normalize()
# check: plane direction along z is (0, TILT, 1); normal must be perpendicular: (0,-1,TILT).(0,TILT,1)=0 -> ok
nrm = Vector((0, -1, TILT)).normalized()

eyelets = {}
for i in range(N):
    z = 0.010 + i * PITCH
    hx = 0.017 + 0.0045 * i
    eyelets[("L", i)] = Vector((-hx, surf_y(z), z))    # soldier's... just two sides, -X and +X
    eyelets[("R", i)] = Vector((hx, surf_y(z), z))

# ---------- context: stays + tongue (dark leather) ----------
ctx = []
for sgn in (-1, 1):
    bm = bmesh.new()
    pts = []
    for i in range(N + 1):
        z = -0.004 + i * PITCH
        hx = 0.017 + 0.0045 * i
        pts.append((Vector((sgn * (hx - 0.010), surf_y(z), z)), Vector((sgn * (hx + 0.022), surf_y(z) + 0.004, z))))
    rows = [(bm.verts.new(a), bm.verts.new(b)) for a, b in pts]
    for (a0, b0), (a1, b1) in zip(rows[:-1], rows[1:]):
        bm.faces.new((a0, b0, b1, a1) if sgn > 0 else (a0, a1, b1, b0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.y > 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces); break
    stay = pc.new_mesh_obj(f"Lace.Stay.{'L' if sgn < 0 else 'R'}", bm)
    pc.add_solidify(stay, 0.0028, offset=1.0); pc.add_bevel(stay, 0.001, 2, angle_deg=40); ctx.append(stay)
bm = bmesh.new()
rows = []
for i in range(N + 1):
    z = -0.004 + i * PITCH
    rows.append([bm.verts.new((x, surf_y(z) + 0.0045 + 0.002 * (1 - (x / 0.045) ** 2), z)) for x in (-0.045, -0.02, 0, 0.02, 0.045)])
for a, b in zip(rows[:-1], rows[1:]):
    for k in range(4):
        bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    if f.normal.y > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces); break
tongue = pc.new_mesh_obj("Lace.Tongue", bm)
pc.add_solidify(tongue, 0.004, offset=1.0); pc.add_subsurf(tongue, 1, 2); ctx.append(tongue)

# ---------- eyelets: metal grommets ----------
bm = bmesh.new()
for k, p in eyelets.items():
    tor = bmesh.ops.create_cone(bm, cap_ends=False, segments=20, radius1=0.0038, radius2=0.0038, depth=0.0001)
    # a proper torus:
    bmesh.ops.delete(bm, geom=tor["verts"], context="VERTS")
    ring = []
    for a in range(20):
        th = 2 * math.pi * a / 20
        for b in range(10):
            ph = 2 * math.pi * b / 10
            r = 0.0033 + 0.0012 * math.cos(ph)
            ring.append(bm.verts.new((r * math.cos(th), 0.0012 * math.sin(ph), r * math.sin(th))))
    for a in range(20):
        for b in range(10):
            v0 = ring[a * 10 + b]; v1 = ring[a * 10 + (b + 1) % 10]
            v2 = ring[((a + 1) % 20) * 10 + (b + 1) % 10]; v3 = ring[((a + 1) % 20) * 10 + b]
            bm.faces.new((v0, v1, v2, v3))
    rot = nrm.to_track_quat("-Y", "Z").to_matrix()
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=ring)
    bmesh.ops.translate(bm, vec=p - nrm * 0.0005, verts=ring)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
grommets = pc.new_mesh_obj("Lace.Grommets", bm)

# ---------- lace curves ----------
def lace_end(name, seq, over_parity):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = 0.0019; cu.bevel_resolution = 6; cu.resolution_u = 16
    cu.use_fill_caps = True; cu.use_uv_as_generated = True
    sp = cu.splines.new("BEZIER")
    pts = []
    for idx, key in enumerate(seq):
        p = eyelets[key]
        pts.append(p + nrm * -0.0035)                      # lace sits 3.5 mm behind the grommet face (inside)
        if idx + 1 < len(seq):
            q = eyelets[seq[idx + 1]]
            mid = (p + q) / 2
            on_top = (idx % 2 == over_parity)
            pts.append(mid + nrm * (0.0062 if on_top else 0.0024))   # crossing: one strand rides over the other
    # top: free end hangs down to the side
    last = eyelets[seq[-1]]
    side = 1 if last.x > 0 else -1
    pts.append(last + nrm * 0.004 + Vector((side * 0.012, 0, 0.010)))
    pts.append(last + nrm * 0.012 + Vector((side * 0.030, -0.01, -0.030)))
    pts.append(last + nrm * 0.010 + Vector((side * 0.034, -0.012, -0.075)))
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
        bp.radius = 1.0
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o)
    return o

seqA = [("L", 0), ("R", 1), ("L", 2), ("R", 3), ("L", 4)]
seqB = [("R", 0), ("L", 1), ("R", 2), ("L", 3), ("R", 4)]
laceA = lace_end("Lace.A", seqA, 0)
laceB = lace_end("Lace.B", seqB, 1)

# ---------- materials ----------
def braid_material(name, color=(0.06, 0.055, 0.05), repeats_along=170.0, around=3.0):
    """Braid from curve UVs: u = along (0..1 over the whole lace), v = around (0..1)."""
    mat, nodes, links, b = pc.base_material(name)
    b.inputs["Roughness"].default_value = 0.7; b.inputs["Sheen Weight"].default_value = 0.4
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(tc.outputs["UV"], sep.inputs["Vector"])
    def ma(op, a, bval=None):
        n = nodes.new("ShaderNodeMath"); n.operation = op
        links.new(a, n.inputs[0]) if hasattr(a, "node") else n.inputs[0].__setattr__("default_value", a)
        if bval is not None:
            links.new(bval, n.inputs[1]) if hasattr(bval, "node") else n.inputs[1].__setattr__("default_value", bval)
        return n.outputs[0]
    u = ma("MULTIPLY", sep.outputs["X"], repeats_along)
    v = ma("MULTIPLY", sep.outputs["Y"], around)
    d1 = ma("PINGPONG", ma("ADD", u, v), 0.5)          # triangle waves of period 1 along the two diagonals
    d2 = ma("PINGPONG", ma("SUBTRACT", u, v), 0.5)
    h = ma("MAXIMUM", d1, d2)                           # diamond/braid ridges
    h = ma("POWER", h, 1.6)
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.8; bump.inputs["Distance"].default_value = 0.0004
    links.new(h, bump.inputs["Height"]); links.new(bump.outputs["Normal"], b.inputs["Normal"])
    # darker in the braid grooves, slight colour variation per strand
    col = pc.mix_rgb(nodes, links, h, (color[0] * 0.5, color[1] * 0.5, color[2] * 0.5), color)
    links.new(col, b.inputs["Base Color"])
    return mat

lm = braid_material("Lace.Braid")
laceA.data.materials.append(lm); laceB.data.materials.append(lm)
gm, nodes, links, b = pc.base_material("Lace.Grommet")
b.inputs["Base Color"].default_value = (0.35, 0.33, 0.30, 1); b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.35
grommets.data.materials.append(gm)
leather, nodes, links, b = pc.base_material("Lace.Leather")
b.inputs["Base Color"].default_value = (0.045, 0.035, 0.028, 1); b.inputs["Roughness"].default_value = 0.5
tc = nodes.new("ShaderNodeTexCoord"); n = nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 500; n.inputs["Detail"].default_value = 4
links.new(tc.outputs["Object"], n.inputs["Vector"])
bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.0002
links.new(n.outputs["Fac"], bump.inputs["Height"]); links.new(bump.outputs["Normal"], b.inputs["Normal"])
for o in ctx:
    o.data.materials.append(leather)

t_build = time.time() - t0
objs = [laceA, laceB, grommets]
pc.report("Laces", t_build, objs)

pc.key_light((0, -0.05, 0.05), direction=(-0.7, -1, 0.8), dist=0.6, size=0.3)
pc.camera_fit(objs + ctx, direction=(0.45, -1, 0.45), margin=0.7, lens=70)
pc.render(os.path.join(pc.OUT_DIR, "proto_lace.png"), "lace")
pc.camera_fit([grommets], direction=(0.3, -1, 0.3), margin=0.35, lens=85, name="CamDetail")
pc.render(os.path.join(pc.OUT_DIR, "proto_lace_detail.png"), "lace detail")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(pc.OUT_DIR, "proto_lace.blend"))
