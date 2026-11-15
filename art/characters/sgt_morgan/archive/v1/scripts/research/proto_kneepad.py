"""Prototype 3: hard polymer knee-pad cap. Lofted shell (angular/hex outline, spherical-ish
curvature, raised central ridge), edge lip via Solidify + Bevel, two straps with ladder-lock
buckles, worn-paint shader (noise + Pointiness masks exposing dark polymer).
Knee axis = X, cap faces -Y, Z up. blender -b --python proto_kneepad.py -- [samples] [resx]
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

R = 0.058            # knee radius around X axis
ZH = 0.062           # half height of cap
NZ, NA = 28, 36

def half_angle(z):
    """Hex-like outline: wide in the middle, narrower at the top and bottom edges."""
    t = abs(z) / ZH
    if t < 0.3:
        return math.radians(78)
    return math.radians(78 - (78 - 42) * (t - 0.3) / 0.7)

def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)

sections = []
for j in range(NZ + 1):
    z = -ZH + 2 * ZH * j / NZ
    ha = half_angle(z)
    # curvature in Z: the cap bulges forward at the centre height (knee cap), shallower sphere
    rz = R + 0.012 * (1 - (z / ZH) ** 2)
    sec = []
    for i in range(NA + 1):
        a = -ha + 2 * ha * i / NA
        # central ridge: raised plate band +-12 mm about the centre line, 3.5 mm high, soft shoulders
        ridge = 0.0035 * (1 - smoothstep(0.006, 0.014, abs(a) * rz)) * (1 - smoothstep(0.035, 0.055, abs(z)))
        # outer lip: last two rings/columns flare outward 1.5 mm
        rr = rz + ridge
        sec.append(Vector((rr * math.sin(a), -rr * math.cos(a), z)))
    sections.append(sec)
cap = pc.loft("Knee.Cap", sections, close_profile=False)
# edge lip: flare the boundary verts outward along their normal direction
me = cap.data
bm = bmesh.new(); bm.from_mesh(me)
for v in bm.verts:
    if v.is_boundary:
        v.co += v.normal * -0.0018 if v.normal.y > 0 else v.normal * 0.0018
bm.to_mesh(me); bm.free()
pc.add_solidify(cap, 0.0035, offset=1.0)           # thickness inward (+Y side is inside)
pc.add_bevel(cap, 0.0012, 3, angle_deg=35)
pc.add_subsurf(cap, 1, 2)

# ---------- straps (webbing around the back of the knee) + ladder-lock buckles ----------
straps, buckles = [], []
for zc in (0.036, -0.036):
    bm = bmesh.new()
    a0, a1 = math.radians(70), math.radians(290)
    n = 40
    rows = []
    for zz in (zc - 0.015, zc + 0.015):
        row = []
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            rr = R + 0.0045
            row.append(bm.verts.new((rr * math.sin(a), -rr * math.cos(a), zz)))
        rows.append(row)
    for i in range(n):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    s = pc.new_mesh_obj(f"Knee.Strap.{'U' if zc > 0 else 'L'}", bm)
    pc.add_solidify(s, 0.002, offset=1.0)
    pc.add_bevel(s, 0.0005, 2, angle_deg=50)
    straps.append(s)
    # buckle at the a0 end (soldier's +X side)
    bx, by = (R + 0.006) * math.sin(a0), -(R + 0.006) * math.cos(a0)
    bk = pc.box("Knee.Buckle", (0.010, 0.036, 0.034), (bx, by, zc))
    bk.rotation_euler = (0, 0, a0 - math.pi / 2)
    c1 = pc.box("cut1", (0.020, 0.028, 0.0045), (bx, by, zc + 0.008)); c1.rotation_euler = bk.rotation_euler
    c2 = pc.box("cut2", (0.020, 0.028, 0.0045), (bx, by, zc - 0.008)); c2.rotation_euler = bk.rotation_euler
    pc.boolean(bk, c1); pc.boolean(bk, c2)
    pc.add_bevel(bk, 0.0012, 3, angle_deg=30); pc.add_weighted_normal(bk)
    buckles.append(bk)

# context: the knee/pant leg as a dark fabric cylinder
leg = pc.cylinder("Knee.LegContext", R - 0.002, 0.30, (0, 0, 0), segs=48)
leg.data.materials.append(pc.cordura_material("Knee.Pant", (0.05, 0.048, 0.04), weave_scale=800, wear=False, rough=0.85))

# ---------- worn paint shader ----------
def worn_paint(name, paint=(0.27, 0.235, 0.165), polymer=(0.028, 0.028, 0.03)):
    mat, nodes, links, b = pc.base_material(name)
    tc = nodes.new("ShaderNodeTexCoord")
    # 1) edge wear from pointiness + AO
    edge = pc.edge_wear_mask(nodes, links, pointiness_mid=0.6, pointiness_width=0.1, ao_dist=0.004, noise_scale=250)
    # 2) scratches: stretched noise thresholded
    mp = nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 1, 14)
    links.new(tc.outputs["Object"], mp.inputs["Vector"])
    sn = nodes.new("ShaderNodeTexNoise"); sn.inputs["Scale"].default_value = 180; sn.inputs["Detail"].default_value = 3
    links.new(mp.outputs["Vector"], sn.inputs["Vector"])
    sth = nodes.new("ShaderNodeMapRange"); sth.inputs["From Min"].default_value = 0.66; sth.inputs["From Max"].default_value = 0.72
    links.new(sn.outputs["Fac"], sth.inputs["Value"])
    # 3) blotchy chipping
    cn = nodes.new("ShaderNodeTexNoise"); cn.inputs["Scale"].default_value = 40; cn.inputs["Detail"].default_value = 8; cn.inputs["Roughness"].default_value = 0.7
    links.new(tc.outputs["Object"], cn.inputs["Vector"])
    cth = nodes.new("ShaderNodeMapRange"); cth.inputs["From Min"].default_value = 0.62; cth.inputs["From Max"].default_value = 0.68
    links.new(cn.outputs["Fac"], cth.inputs["Value"])
    add1 = nodes.new("ShaderNodeMath"); add1.operation = "ADD"; links.new(edge, add1.inputs[0]); links.new(sth.outputs["Result"], add1.inputs[1])
    add2 = nodes.new("ShaderNodeMath"); add2.operation = "ADD"; links.new(add1.outputs[0], add2.inputs[0]); links.new(cth.outputs["Result"], add2.inputs[1])
    cl = nodes.new("ShaderNodeClamp"); links.new(add2.outputs[0], cl.inputs["Value"])
    wear = cl.outputs["Result"]
    # paint colour variation + grime (darker low down)
    gn = nodes.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = 25; gn.inputs["Detail"].default_value = 5
    links.new(tc.outputs["Object"], gn.inputs["Vector"])
    gr = nodes.new("ShaderNodeMapRange"); gr.inputs["From Min"].default_value = 0.35; gr.inputs["From Max"].default_value = 0.65
    gr.inputs["To Min"].default_value = 0.55; gr.inputs["To Max"].default_value = 1.1
    links.new(gn.outputs["Fac"], gr.inputs["Value"])
    pm = nodes.new("ShaderNodeMix"); pm.data_type = "RGBA"; pm.blend_type = "MULTIPLY"; pm.inputs["Factor"].default_value = 1
    pm.inputs[6].default_value = (*paint, 1); links.new(gr.outputs["Result"], pm.inputs[7])
    links.new(pc.mix_rgb(nodes, links, wear, pm.outputs[2], polymer), b.inputs["Base Color"])
    links.new(pc.mix_float(nodes, links, wear, 0.62, 0.38), b.inputs["Roughness"])
    # paint has a slight orange-peel; polymer smoother
    bn = nodes.new("ShaderNodeTexNoise"); bn.inputs["Scale"].default_value = 900; bn.inputs["Detail"].default_value = 2
    links.new(tc.outputs["Object"], bn.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25; bump.inputs["Distance"].default_value = 0.0002
    links.new(bn.outputs["Fac"], bump.inputs["Height"]); links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat

cap.data.materials.append(worn_paint("Knee.WornPaint"))
webm = pc.cordura_material("Knee.Webbing", (0.07, 0.065, 0.05), weave_scale=900, pointiness_mid=0.6)
for s in straps:
    s.data.materials.append(webm)
poly = pc.polymer_material("Knee.Acetal")
for bk in buckles:
    bk.data.materials.append(poly)

t_build = time.time() - t0
objs = [cap] + straps + buckles
pc.report("Knee pad", t_build, objs)

pc.key_light((0, -R, 0), direction=(-1, -1, 1.0), dist=0.8, size=0.4)
pc.camera_fit(objs + [leg], direction=(0.6, -1, 0.25), margin=0.62, lens=65)
pc.render(os.path.join(pc.OUT_DIR, "proto_kneepad.png"), "kneepad 3/4")
pc.camera_fit(objs + [leg], direction=(1, -0.15, 0.1), margin=0.62, lens=65, name="CamSide")
pc.render(os.path.join(pc.OUT_DIR, "proto_kneepad_side.png"), "kneepad side")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(pc.OUT_DIR, "proto_kneepad.blend"))
