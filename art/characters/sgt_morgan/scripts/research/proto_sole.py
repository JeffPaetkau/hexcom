"""Prototype 4: boot sole with lugs. Foot outline polygon -> lofted shell with bisected edge
loops -> toe spring / heel curvature applied per vertex -> array of chamfered lug boxes placed on
a herringbone grid, clipped to an inset outline, tilted to the local sole slope. Rubber shader.
Toe points -Y (character faces -Y). blender -b --python proto_sole.py -- [samples] [resx]
"""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import proto_common as pc

SAMPLES, RESX = pc.argv()
pc.reset_scene(SAMPLES, RESX)
pc.world_hdri(0.7, rot_z=math.radians(60))
t0 = time.time()

L = 0.305                          # sole length
# right foot outline: stations along length (0 = heel, 1 = toe) -> (lateral half width, medial half width)
# lateral = soldier's right side (-X for the right foot), medial = +X (big toe side)
stations = [
    (0.05, 0.034, 0.034), (0.10, 0.040, 0.040), (0.15, 0.040, 0.040),
    (0.25, 0.037, 0.038), (0.35, 0.036, 0.040), (0.45, 0.038, 0.045), (0.55, 0.043, 0.050),
    (0.65, 0.049, 0.054), (0.72, 0.052, 0.055), (0.80, 0.051, 0.054), (0.87, 0.046, 0.050),
    (0.93, 0.038, 0.042),
]
def outline(inset=0.0):
    pts = []
    y = lambda t: -(t - 0.5) * L          # heel at +Y, toe at -Y
    # medial side heel -> toe
    for t, lat, med in stations:
        pts.append(Vector((med - inset, y(t), 0)))
    # toe arc (medial -> lateral), x radius 40 mm, 21 mm long
    for a in (0.2, 0.4, 0.6, 0.8):
        pts.append(Vector((0.002 + (0.040 - inset) * math.cos(math.pi * a), y(0.93) - (0.021 - inset) * math.sin(math.pi * a), 0)))
    for t, lat, med in reversed(stations):
        pts.append(Vector((-(lat - inset), y(t), 0)))
    # heel arc (lateral -> medial), x radius 34 mm, 15 mm long
    for a in (0.2, 0.4, 0.6, 0.8):
        pts.append(Vector((-(0.034 - inset) * math.cos(math.pi * a), y(0.05) + (0.015 - inset) * math.sin(math.pi * a), 0)))
    return pts

def spring(y):
    """Vertical curvature of the sole: toe spring + slight heel lift (y: +heel ... -toe)."""
    t = 0.5 - y / L
    toe = 0.028 * max(0.0, (t - 0.68) / 0.32) ** 2
    heel = 0.006 * max(0.0, (0.12 - t) / 0.12) ** 2
    return toe + heel

def point_in_poly(p, poly):
    x, y = p.x, p.y
    inside = False
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a.y > y) != (b.y > y):
            xi = a.x + (y - a.y) * (b.x - a.x) / (b.y - a.y)
            if x < xi:
                inside = not inside
    return inside

# ---------- shell ----------
SOLE_T = 0.022
outer = outline(0.0)
bm = bmesh.new()
rings = []
for z, ins in ((0.0, 0.004), (0.004, 0.0), (SOLE_T - 0.003, 0.0), (SOLE_T, 0.002)):
    ring = [bm.verts.new((p.x, p.y, z)) for p in outline(ins)]
    rings.append(ring)
n = len(rings[0])
for a, b in zip(rings[:-1], rings[1:]):
    for i in range(n):
        bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# cut edge loops across the length so the ngon caps can bend
for k in range(1, 22):
    yy = -L / 2 + L * k / 22
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, yy, 0), plane_no=(0, 1, 0), dist=1e-6)
for v in bm.verts:
    v.co.z += spring(v.co.y)
shell = pc.new_mesh_obj("Sole.Shell", bm)
pc.add_bevel(shell, 0.0025, 3, angle_deg=40)

# ---------- lugs ----------
LUG = (0.019, 0.012, 0.0075)      # x, y, height
bm = bmesh.new()
inner = outline(0.0065)
n_lugs = 0
row = 0
yy = -L / 2 + 0.012
while yy < L / 2 - 0.010:
    t = 0.5 - yy / L
    heel_zone = t < 0.33
    lx, ly, lh = (0.022, 0.014, 0.0085) if heel_zone else LUG
    pitch_x = lx + 0.006
    ang = math.radians(28) * (1 if row % 2 == 0 else -1)
    xoff = (pitch_x / 2) if row % 2 else 0.0
    xx = -0.06 + xoff
    while xx < 0.065:
        c = Vector((xx, yy, 0))
        rot = Matrix.Rotation(ang, 3, 'Z')
        corners = [c + rot @ Vector((sx * lx / 2, sy * ly / 2, 0)) for sx in (-1, 1) for sy in (-1, 1)]
        if all(point_in_poly(q, inner) for q in corners):
            # build each lug in its own bmesh, then merge (keeps vertex bookkeeping trivial)
            tbm = bmesh.new()
            vs = bmesh.ops.create_cube(tbm, size=1.0)["verts"]
            bmesh.ops.scale(tbm, vec=(lx, ly, lh), verts=vs)
            bmesh.ops.translate(tbm, vec=(0, 0, -lh / 2 + 0.0015), verts=vs)   # top sinks 1.5 mm into the shell
            zmin = min(v.co.z for v in tbm.verts)
            bot_edges = [e for e in tbm.edges if all(abs(v.co.z - zmin) < 1e-6 for v in e.verts)]
            bmesh.ops.bevel(tbm, geom=bot_edges, offset=0.0022, segments=2, profile=0.7, affect='EDGES')
            dz = (spring(yy + 0.001) - spring(yy - 0.001)) / 0.002
            tilt = Matrix.Rotation(-math.atan(dz), 3, 'X')
            bmesh.ops.rotate(tbm, cent=(0, 0, 0), matrix=tilt @ rot, verts=tbm.verts[:])
            bmesh.ops.translate(tbm, vec=(xx, yy, spring(yy)), verts=tbm.verts[:])
            tmp = bpy.data.meshes.new("tmp.lug"); tbm.to_mesh(tmp); tbm.free()
            bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
            n_lugs += 1
        xx += pitch_x
    yy += (ly + 0.008)
    row += 1
lugs = pc.new_mesh_obj("Sole.Lugs", bm)
print(f"[proto] lugs placed: {n_lugs}")

# ---------- rubber shader ----------
def rubber(name):
    mat, nodes, links, b = pc.base_material(name)
    tc = nodes.new("ShaderNodeTexCoord")
    base = (0.012, 0.012, 0.013)
    wear = pc.edge_wear_mask(nodes, links, pointiness_mid=0.6, pointiness_width=0.1, ao_dist=0.003, noise_scale=400)
    # dust/scuff: lighter grey-brown on worn edges
    col = pc.mix_rgb(nodes, links, wear, base, (0.16, 0.15, 0.13))
    # large-scale dirt variation
    dn = nodes.new("ShaderNodeTexNoise"); dn.inputs["Scale"].default_value = 30; dn.inputs["Detail"].default_value = 6
    links.new(tc.outputs["Object"], dn.inputs["Vector"])
    dr = nodes.new("ShaderNodeMapRange"); dr.inputs["From Min"].default_value = 0.55; dr.inputs["From Max"].default_value = 0.75
    dr.inputs["To Max"].default_value = 0.6
    links.new(dn.outputs["Fac"], dr.inputs["Value"])
    col = pc.mix_rgb(nodes, links, dr.outputs["Result"], col, (0.11, 0.095, 0.075))
    links.new(col, b.inputs["Base Color"])
    rn = nodes.new("ShaderNodeTexNoise"); rn.inputs["Scale"].default_value = 200; rn.inputs["Detail"].default_value = 3
    links.new(tc.outputs["Object"], rn.inputs["Vector"])
    rr = nodes.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.45; rr.inputs["To Max"].default_value = 0.7
    links.new(rn.outputs["Fac"], rr.inputs["Value"])
    links.new(pc.mix_float(nodes, links, wear, rr.outputs["Result"], 0.8), b.inputs["Roughness"])
    # micro grain (moulded rubber texture)
    gn = nodes.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = 2500; gn.inputs["Detail"].default_value = 2
    links.new(tc.outputs["Object"], gn.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.3; bump.inputs["Distance"].default_value = 0.00015
    links.new(gn.outputs["Fac"], bump.inputs["Height"]); links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat

rub = rubber("Sole.Rubber")
shell.data.materials.append(rub); lugs.data.materials.append(rub)

t_build = time.time() - t0
objs = [shell, lugs]
pc.report("Boot sole", t_build, objs, f"lugs={n_lugs}")

pc.key_light((0, 0, 0), direction=(-0.5, -1, -1.2), dist=0.9, size=0.5)
pc.camera_fit(objs, direction=(0.45, -0.5, -1), margin=0.95, lens=50)
pc.render(os.path.join(pc.OUT_DIR, "proto_sole_below.png"), "sole below")
pc.key_light((0, 0, 0), direction=(-0.5, -1, 1.2), dist=0.9, size=0.5)
pc.camera_fit(objs, direction=(1, -0.35, 0.12), margin=0.95, lens=50, name="CamSide")
pc.render(os.path.join(pc.OUT_DIR, "proto_sole_side.png"), "sole side")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(pc.OUT_DIR, "proto_sole.blend"))
