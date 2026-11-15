"""Prototype 6: AR-15 lower receiver magwell + trigger guard, anodised hard-surface.
Technique under test: Boolean (EXACT) cutters -> Bevel (angle-limited, clamped, harden normals)
-> Weighted Normal on a smooth-shaded hull; lofted rounded-bar trigger guard; pins; mag-release
fence; anodised aluminium shader with Pointiness/AO edge wear exposing bare metal.
Local axes of the part: X = bore axis, muzzle at -X (front of magwell), Y across (receiver's RIGHT
side at -Y = camera side, where the mag release lives), Z up, magwell mouth at z = 0.
blender -b --python proto_magwell.py -- [samples] [resx]
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

HW = 0.014            # half width of the lower (28 mm)
RAKE = math.radians(4)

# ---------- hull: magwell (lofted, raked front) + receiver block + rear/grip boss ----------
def rect(x0, x1, z, hw=HW):
    return [Vector((x0, -hw, z)), Vector((x1, -hw, z)), Vector((x1, hw, z)), Vector((x0, hw, z))]
magwell = pc.loft("Mag.Well", [rect(-0.040, 0.034, 0.0), rect(-0.040 + 0.040 * math.tan(RAKE), 0.034, 0.040)], cap=True)
recv = pc.box("Mag.Receiver", (0.124, 2 * HW, 0.026), (0.020, 0, 0.053))
rear = pc.box("Mag.Rear", (0.016, 2 * HW, 0.016), (0.076, 0, 0.034))
# v1 used pc.join() (three overlapping closed shells in one mesh) and then cut: the EXACT difference on that
# multi-shell operand inverted in places (cutter volumes came out as solid, see proto_magwell_v1_joined.png).
# v2: make the hull one manifold solid first with UNION booleans, then cut.
hull = recv; hull.name = "Mag.Lower"
for part in (magwell, rear):
    pc.boolean(hull, part, op="UNION")

# cutters
mag_cut = pc.box("cut.mag", (0.062, 0.024, 0.090), (-0.003, 0, 0.034))
mag_cut.rotation_euler = (0, -RAKE, 0)
flare = pc.loft("cut.flare", [[Vector((x, y, -0.002)) for (x, y) in pc.rounded_rect_profile(0.070, 0.030, 0.004, 3)],
                              [Vector((x, y, 0.007)) for (x, y) in pc.rounded_rect_profile(0.062, 0.024, 0.003, 3)]], cap=True)
flare.location = (-0.003, 0, 0)
pockets = []
for sgn in (-1, 1):
    pk = pc.loft("cut.pocket", [[Vector((x, sgn * (HW - 0.001), z)) for (x, z) in pc.rounded_rect_profile(0.044, 0.022, 0.006, 4)],
                                [Vector((x, sgn * (HW + 0.004), z)) for (x, z) in pc.rounded_rect_profile(0.044, 0.022, 0.006, 4)]], cap=True)
    pk.location = (-0.002, 0, 0.020)
    pockets.append(pk)
ear_slot = pc.box("cut.ears", (0.018, 0.007, 0.018), (0.076, 0, 0.030))
for c in [mag_cut, flare, ear_slot] + pockets:
    pc.boolean(hull, c)
pc.add_bevel(hull, 0.0008, 3, angle_deg=30, clamp=True)
pc.add_weighted_normal(hull)

# ---------- trigger guard: rounded bar swept along a polyline in XZ ----------
path = [(0.0375, 0.041), (0.0385, 0.031), (0.0440, 0.0235), (0.0520, 0.0215), (0.0680, 0.0215), (0.0745, 0.0245), (0.0770, 0.030), (0.0770, 0.041)]
prof = pc.rounded_rect_profile(0.0065, 0.0045, 0.0015, 3)      # (across Y, along normal)
sections = []
for i, (x, z) in enumerate(path):
    p0 = Vector(path[max(0, i - 1)]); p1 = Vector(path[min(len(path) - 1, i + 1)])
    t = (p1 - p0).normalized()
    n = Vector((t.y, -t.x))                                     # in-plane normal (XZ)
    sec = [Vector((x + n.x * v, u, z + n.y * v)) for (u, v) in prof]
    sections.append(sec)
guard = pc.loft("Mag.TriggerGuard", sections, close_profile=True, cap=True)
pc.add_subsurf(guard, 1, 2)
pins = []
for (x, z, r, L) in ((0.0375, 0.037, 0.0015, 2 * HW + 0.0004), (0.0770, 0.034, 0.0015, 2 * HW + 0.0004),
                     (-0.034, 0.060, 0.0040, 2 * HW + 0.0030), (0.068, 0.060, 0.0040, 2 * HW + 0.0030)):
    pin = pc.cylinder(f"Mag.Pin", r, L, (x, 0, z), rot=(math.pi / 2, 0, 0), segs=24)
    pc.add_bevel(pin, 0.0004, 2, angle_deg=30)
    pins.append(pin)

# ---------- mag release: fence ring + button on the right side (-Y) ----------
fence = pc.box("Mag.Fence", (0.021, 0.0035, 0.017), (0.040, -HW - 0.00175, 0.050))
fence_cut = pc.box("cut.fence", (0.013, 0.008, 0.010), (0.040, -HW - 0.00175, 0.050))
pc.boolean(fence, fence_cut)
pc.add_bevel(fence, 0.0007, 3, angle_deg=30); pc.add_weighted_normal(fence)
button = pc.cylinder("Mag.Button", 0.0045, 0.0032, (0.040, -HW - 0.0014, 0.050), rot=(math.pi / 2, 0, 0), segs=32)
pc.add_bevel(button, 0.0006, 3, angle_deg=30)

# ---------- grip stub (polymer, context) ----------
grip = pc.box("Mag.Grip", (0.024, 0.026, 0.046), (0.078, 0, 0.004))
grip.rotation_euler = (0, math.radians(-22), 0)
pc.add_bevel(grip, 0.003, 4, angle_deg=30); pc.add_subsurf(grip, 1, 1)

# ---------- anodised aluminium ----------
def anodised_material(name, color=(0.022, 0.023, 0.025), rough=0.5, metallic=0.75, bare=(0.72, 0.73, 0.74)):
    mat, nodes, links, b = pc.base_material(name)
    tc = nodes.new("ShaderNodeTexCoord")
    b.inputs["Metallic"].default_value = metallic
    # edge wear: pointiness + AO, broken by noise -> bare aluminium
    wear = pc.edge_wear_mask(nodes, links, pointiness_mid=0.60, pointiness_width=0.10, ao_dist=0.003, noise_scale=600)
    # thinning of the anodise on flats: low-frequency blotches lift the colour towards grey
    tn = nodes.new("ShaderNodeTexNoise"); tn.inputs["Scale"].default_value = 35; tn.inputs["Detail"].default_value = 6
    links.new(tc.outputs["Object"], tn.inputs["Vector"])
    tr = nodes.new("ShaderNodeMapRange"); tr.inputs["From Min"].default_value = 0.58; tr.inputs["From Max"].default_value = 0.72
    tr.inputs["To Max"].default_value = 0.35
    links.new(tn.outputs["Fac"], tr.inputs["Value"])
    col = pc.mix_rgb(nodes, links, tr.outputs["Result"], color, (0.09, 0.092, 0.095))
    col = pc.mix_rgb(nodes, links, wear, col, bare)
    links.new(col, b.inputs["Base Color"])
    links.new(pc.mix_float(nodes, links, wear, rough, 0.32), b.inputs["Roughness"])
    links.new(pc.mix_float(nodes, links, wear, metallic, 1.0), b.inputs["Metallic"])
    # bead-blast micro grain
    gn = nodes.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = 4000; gn.inputs["Detail"].default_value = 2
    links.new(tc.outputs["Object"], gn.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.2; bump.inputs["Distance"].default_value = 0.00005
    links.new(gn.outputs["Fac"], bump.inputs["Height"]); links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat

ano = anodised_material("Mag.Anodised")
for o in [hull, guard, fence] + pins:
    o.data.materials.append(ano)
steel, nodes, links, b = pc.base_material("Mag.Steel")
b.inputs["Base Color"].default_value = (0.35, 0.35, 0.36, 1); b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.45
button.data.materials.append(pc.polymer_material("Mag.ButtonPoly", rough=0.5))
grip.data.materials.append(pc.polymer_material("Mag.GripPoly", rough=0.55))

t_build = time.time() - t0
objs = [hull, guard, fence, button] + pins
pc.report("Magwell", t_build, objs)
pc.report("Magwell hull only", t_build, [hull])

pc.key_light((0.02, -HW, 0.035), direction=(-0.8, -1, 0.9), dist=0.7, size=0.35)
pc.camera_fit(objs + [grip], direction=(-0.55, -1, 0.30), margin=0.72, lens=65)
pc.render(os.path.join(pc.OUT_DIR, "proto_magwell.png"), "magwell right 3/4")
pc.camera_fit([hull], direction=(-0.7, -0.9, -0.55), margin=0.55, lens=70, name="CamMouth")
pc.render(os.path.join(pc.OUT_DIR, "proto_magwell_mouth.png"), "magwell mouth from below")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(pc.OUT_DIR, "proto_magwell.blend"))
