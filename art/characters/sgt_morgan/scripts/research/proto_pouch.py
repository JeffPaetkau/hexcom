"""Prototype 2: single M4 magazine pouch. Rounded-box body (Bevel + Subdivision + soft Displace),
domed L-shaped lid flap, elastic retention band, bar-tacks, 25 mm side-release buckle, webbing.
Front faces -Y. blender -b --python proto_pouch.py -- [samples] [resx]
"""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import proto_common as pc

SAMPLES, RESX = pc.argv()
pc.reset_scene(SAMPLES, RESX)
pc.world_hdri(0.6, rot_z=math.radians(90))
t0 = time.time()

BW, BD, BH = 0.078, 0.042, 0.150     # body width, depth, height (m)

# ---------- body: cube -> Bevel -> Subsurf -> Displace(clouds) ----------
body = pc.box("Pouch.Body", (BW, BD, BH), (0, 0, BH / 2))
pc.add_bevel(body, 0.010, 3, angle_deg=30, harden=False)
pc.add_subsurf(body, 2, 3)
tex = bpy.data.textures.new("Pouch.Bulge", "CLOUDS"); tex.noise_scale = 0.06; tex.noise_depth = 1
disp = body.modifiers.new("Bulge", "DISPLACE"); disp.texture = tex; disp.strength = 0.004; disp.mid_level = 0.5
# slight inward squeeze below the elastic band: via a Lattice would be nicer; skipped for the prototype.

# ---------- lid flap: L-profile swept along X with a dome ----------
FLAP_W = BW + 0.006
FLAP_T = 0.0035
zt = BH + 0.002               # flap top surface
r = 0.010                     # front corner radius
cy, cz = -BD / 2 - 0.004 + r, zt - r      # arc centre (y, z)
yf = cy - r                   # flap front face y
prof = []                     # (y, z) centre-line: back hinge -> over the top -> corner arc -> down the front
y_back = BD / 2 - 0.004
for i in range(5):
    prof.append((y_back + (cy - y_back) * i / 4, zt))
for k in range(1, 6):
    a = math.pi / 2 - (math.pi / 2) * k / 5
    prof.append((cy - r * math.cos(a), cz + r * math.sin(a)))
for i in range(1, 9):         # down the front
    prof.append((yf, cz - 0.052 * i / 8))
NX = 16
sections = []
for (y, z) in prof:
    sec = []
    for i in range(NX + 1):
        x = -FLAP_W / 2 + FLAP_W * i / NX
        dome = 0.004 * (1 - (2 * x / FLAP_W) ** 2)        # 4 mm centre dome
        # dome pushes outward: up on the top, forward on the front
        along = len(sections) / (len(prof) - 1)
        up = dome * max(0.0, 1 - along * 1.6)
        fwd = dome * min(1.0, along * 1.6)
        sec.append(Vector((x, y - fwd, z + up)))
    sections.append(sec)
flap = pc.loft("Pouch.Flap", sections, close_profile=False)
pc.add_solidify(flap, FLAP_T, offset=-1.0)
pc.add_bevel(flap, 0.0012, 2, angle_deg=40)
pc.add_subsurf(flap, 1, 2)

# ---------- elastic retention band around the upper body ----------
band_prof = pc.rounded_rect_profile(BW + 0.006, BD + 0.006, 0.012, segs=5)
zb0, zb1 = BH * 0.52, BH * 0.52 + 0.022
secs = [[Vector((x, y, z)) for (x, y) in band_prof] for z in (zb0, zb0 + 0.004, zb1 - 0.004, zb1)]
# pinch the band slightly in the middle (elastic tension)
for s in secs[1:3]:
    for v in s:
        v.x *= 0.985; v.y *= 0.985
band = pc.loft("Pouch.Elastic", secs, close_profile=True)
pc.add_solidify(band, 0.0022, offset=1.0)
pc.add_bevel(band, 0.0006, 2, angle_deg=50)

# ---------- webbing straps: lid -> female buckle, body front -> male buckle ----------
WEB_W, WEB_T = 0.025, 0.0013
yfront = -BD / 2 - 0.0045
# female buckle sits on the body front at z = 0.075 -> strap from body (below) up into it
male_z = 0.060
fem_z = 0.090
strap_lid = pc.box("Pouch.Strap.Lid", (WEB_W, WEB_T, 0.030), (0, yfront - 0.004 - 0.004, cz - 0.052 - 0.012))
strap_body = pc.box("Pouch.Strap.Body", (WEB_W, WEB_T, 0.040), (0, yfront, male_z - 0.028))
for s in (strap_lid, strap_body):
    pc.add_bevel(s, 0.0005, 2)

# ---------- side-release buckle (25 mm) ----------
def female(loc):
    f = pc.box("Pouch.Buckle.F", (0.0335, 0.0085, 0.030), loc)
    slot = pc.box("cut.slot", (0.0265, 0.006, 0.040), loc)                 # through slot (open top and bottom)
    winL = pc.box("cut.winL", (0.006, 0.012, 0.010), (loc[0] - 0.0155, loc[1], loc[2] + 0.002))
    winR = pc.box("cut.winR", (0.006, 0.012, 0.010), (loc[0] + 0.0155, loc[1], loc[2] + 0.002))
    bar = pc.box("cut.bar", (0.030, 0.012, 0.004), (loc[0], loc[1], loc[2] + 0.009))  # webbing bar slot
    for c in (slot, winL, winR, bar):
        pc.boolean(f, c)
    pc.add_bevel(f, 0.0012, 3, angle_deg=30)
    pc.add_weighted_normal(f)
    return f

def male(loc):
    parts = []
    cross = pc.box("Pouch.Buckle.M", (0.030, 0.006, 0.007), (loc[0], loc[1], loc[2] + 0.016))
    tongue = pc.box("m.tongue", (0.007, 0.0045, 0.030), (loc[0], loc[1], loc[2]))
    parts = [cross, tongue]
    for sgn in (-1, 1):
        p = pc.box("m.prong", (0.0045, 0.005, 0.032), (loc[0] + sgn * 0.012, loc[1], loc[2] + 0.001))
        p.rotation_euler = (0, sgn * math.radians(-3), 0)
        parts.append(p)
        hook = pc.box("m.hook", (0.0035, 0.005, 0.007), (loc[0] + sgn * 0.0155, loc[1], loc[2] - 0.008))
        parts.append(hook)
    for p in parts[1:]:
        p.select_set(False)
    m = pc.join(parts, "Pouch.Buckle.M")
    pc.add_bevel(m, 0.0008, 2, angle_deg=30)
    pc.add_weighted_normal(m)
    return m

fem = female((0, yfront - 0.0045, fem_z - 0.012))
mal = male((0, yfront - 0.0045, fem_z - 0.012 - 0.004))

# ---------- bar-tacks: elastic band anchors, strap roots, flap hinge ----------
bm = bmesh.new()
n = 0
for sgn in (-1, 1):
    n += pc.bartack(bm, (sgn * (BW / 2 + 0.002), yfront + 0.004, (zb0 + zb1) / 2), (0, 0, 1), (0, 1, 0), length=0.016)
n += pc.bartack(bm, (0, yfront - 0.002, male_z - 0.044), (1, 0, 0), (0, 0, 1), length=0.018)
n += pc.bartack(bm, (0, yfront - 0.0045 - 0.004 - 0.002, cz - 0.052 - 0.004), (1, 0, 0), (0, 0, 1), length=0.018)
tacks = pc.new_mesh_obj("Pouch.Bartacks", bm)
print(f"[proto] bartack threads: {n}")

# ---------- materials ----------
OLIVE = (0.115, 0.105, 0.062)
cord = pc.cordura_material("Pouch.Cordura", OLIVE, weave_scale=1200)
webm = pc.cordura_material("Pouch.Webbing", (0.125, 0.112, 0.066), weave_scale=900, pointiness_mid=0.6)
elast = pc.cordura_material("Pouch.ElasticMat", (0.05, 0.05, 0.045), weave_scale=700, wear=False, rough=0.85)
poly = pc.polymer_material("Pouch.Acetal")
body.data.materials.append(cord); flap.data.materials.append(cord)
band.data.materials.append(elast)
for s in (strap_lid, strap_body):
    s.data.materials.append(webm)
fem.data.materials.append(poly); mal.data.materials.append(poly)
tacks.data.materials.append(pc.thread_material("Pouch.Thread"))

t_build = time.time() - t0
objs = [body, flap, band, strap_lid, strap_body, fem, mal, tacks]
pc.report("Mag pouch", t_build, objs)

pc.ground(0.0)
pc.key_light((0, 0, 0.08), direction=(-1, -1, 1.2), dist=0.7, size=0.35)
pc.camera_fit(objs, direction=(0.55, -1, 0.35), margin=0.8, lens=65)
pc.render(os.path.join(pc.OUT_DIR, "proto_pouch.png"), "pouch")
pc.camera_fit([fem, mal], direction=(0.4, -1, 0.3), margin=0.9, lens=85, name="CamBuckle")
pc.render(os.path.join(pc.OUT_DIR, "proto_pouch_buckle.png"), "pouch buckle detail")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(pc.OUT_DIR, "proto_pouch.blend"))
