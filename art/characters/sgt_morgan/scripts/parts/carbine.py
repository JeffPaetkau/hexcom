"""Carbine, take 2 round 1: a blockout of the soldier's M4-pattern carbine at real dimensions.

    "$SGT_BLENDER" -b --python scripts/parts/carbine.py [-- --no-render] [--keep-scene]

Builds every major component as its own object, `Carbine.<Component>`, in the collection `Part.Carbine`,
parented to one root empty `Carbine.Root`, saves `cache/parts/carbine.blend`, prints and writes the
measurements (`renders/carbine/measure.json`) and renders the round's views into `renders/carbine/`.
Notes, sources and decisions: `scripts/parts/carbine.md`.

Frame (the brief of round 1, shared with the pose agent): `Carbine.Root` sits on the bore axis directly above
the trigger face; local +X runs along the bore toward the muzzle, +Z up through the top rail, +Y to the gun's
LEFT (so -Y is the ejection-port side, the side the hero camera sees). Millimetres in this file, metres in
Blender. Take 1's rifle frame R (archive/v1/spec/15_carbine.md: origin bore x receiver front face, +Y muzzle,
+X gun's right) maps as  x = R.y + 122,  y = -R.x,  z = R.z  (the trigger face is at R.y = -122).

Hand empties (consumed by the pose solve): `Carbine.Grip.R` and `Carbine.Grip.L` sit at the centre of each
palm's contact with the gun. Their axes: local +Z = the palm normal pointing INTO the gun, local +X = across
the palm from the little finger toward the index finger, +Y = Z x X.

Idempotent: by default it starts from an empty factory scene (the .blend is this part's own cache); with
--keep-scene it removes only its own `Carbine.*` data and `Part.Carbine` and builds into the open file.
"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, geometry

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # scripts/
from lib import env  # noqa: E402
from lib import modifiers as MOD  # noqa: E402

MM = 0.001
PART = "Carbine"
COLL = "Part.Carbine"
OUT_DIR = env.path("renders", "carbine")
BLEND = env.path("cache", "parts", "carbine.blend")
REF_CROP = env.path("ref", "crop_hands_rifle.png")   # x3 crop of reference_full (630, 230)-(950, 570)
ICON_CROP = env.path("ref", "crop_icon_carbine.png")

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DO_RENDER = "--no-render" not in ARGS
KEEP_SCENE = "--keep-scene" in ARGS


def R(y):
    """Take 1's station along the bore (R.y, mm from the receiver's front face) in this frame's x."""
    return y + 122.0


# ============================================================================ dimensions (mm, this frame)
# Sources and reasoning: carbine.md §2. Stations along x (bore, muzzle +):
D = dict(
    butt_heel=R(-428.6), pad_toe=R(-401.0), stock_front=R(-248.7), tube_rear=R(-368.0),
    nut_rear=R(-220.6), nut_front=R(-210.2), endplate_front=R(-207.0),
    lower_rear=R(-207.0), upper_rear=R(-197.0), grip_front_top=R(-150.0), trigger=0.0,
    port_rear=R(-96.2), port_front=R(-20.0), magwell_rear=R(-88.0), magwell_front=R(-10.0),
    bolt_face=R(-12.2), receiver_face=R(0.0), hg_rear=R(0.5), hg_front=R(340.9),
    gas_block=(R(204.0), R(229.0)), barrel_step=R(191.0), barrel_journal=R(194.0),
    thread=R(381.5), a2_rear=R(382.7), crown=R(394.2), muzzle=R(427.2),
    rail_top=30.2, parting=-17.0,
)


# ============================================================================ small geometry kit
def _signed_volume(V, F):
    V = np.asarray(V, float)
    s = 0.0
    for f in F:
        a = V[f[0]]
        for i in range(1, len(f) - 1):
            s += np.dot(a, np.cross(V[f[i]], V[f[i + 1]]))
    return s / 6.0


class Geo:
    """Vertices (mm) and faces accumulated from closed primitives, each oriented outward on its own."""

    def __init__(self):
        self.V, self.F = [], []

    def add(self, V, F):
        V = np.asarray(V, float).reshape(-1, 3)
        F = [tuple(int(i) for i in f) for f in F]
        if _signed_volume(V, F) < 0:
            F = [f[::-1] for f in F]
        b = len(self.V)
        self.V.extend(V.tolist())
        self.F.extend(tuple(i + b for i in f) for f in F)
        return self

    def transformed(self, M):
        M = np.asarray(M, float)
        g = Geo()
        V = np.asarray(self.V, float)
        g.V = (V @ M[:3, :3].T + M[:3, 3]).tolist()
        g.F = list(self.F) if np.linalg.det(M[:3, :3]) > 0 else [f[::-1] for f in self.F]
        return g


def _tri_caps(loops2d):
    """Triangles over an outer loop with holes (2D), indices into the concatenated loops."""
    pts = [[Vector((a, b, 0.0)) for a, b in L] for L in loops2d]
    return geometry.tessellate_polygon(pts)


def _ccw(L):
    L = [tuple(p) for p in L]
    a = sum(L[i][0] * L[(i + 1) % len(L)][1] - L[(i + 1) % len(L)][0] * L[i][1] for i in range(len(L)))
    return L if a > 0 else L[::-1]


def prism(outline, c0, c1, plane="xz", holes=()):
    """An outline (outer loop + optional holes, 2D) extruded from c0 to c1 along the third axis.
    plane 'xz': (a, b) = (x, z), extruded along y; 'yz': along x; 'xy': along z."""
    loops = [_ccw(outline)] + [_ccw(h)[::-1] for h in holes]
    flat = [p for L in loops for p in L]
    n = len(flat)
    V2 = np.array(flat, float)
    V = np.vstack([np.c_[V2, np.full(n, c0)], np.c_[V2, np.full(n, c1)]])
    F = []
    off = 0
    for L in loops:
        k = len(L)
        for i in range(k):
            j = (i + 1) % k
            F.append((off + i, off + j, n + off + j, n + off + i))
        off += k
    for t in _tri_caps(loops):
        a, b, c = t
        p = V2[[a, b, c]]
        cw = (p[1, 0] - p[0, 0]) * (p[2, 1] - p[0, 1]) - (p[1, 1] - p[0, 1]) * (p[2, 0] - p[0, 0]) < 0
        F.append((a, b, c) if cw else (a, c, b))           # bottom cap clockwise (normal -c)
        F.append((n + a, n + c, n + b) if cw else (n + a, n + b, n + c))
    if plane == "xz":      # (a, b, c) -> (x, z, y)
        V = V[:, [0, 2, 1]]
    elif plane == "yz":    # (a, b, c) -> (y, z, x)
        V = V[:, [2, 0, 1]]
    return Geo().add(V, F)


def box(x0, x1, y0, y1, z0, z1):
    return prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, "xz")


def lathe_x(stations, seg=32, cy=0.0, cz=0.0, loop=False):
    """Surface of revolution about the x axis (through (cy, cz)) of [(x, r)]: an open profile capped by
    n-gons at both ends, or a closed loop (torus topology; a part with a bore)."""
    P = np.asarray(stations, float)
    m = len(P)
    a = 2 * np.pi * (np.arange(seg) + 0.5) / seg
    V = np.array([(x, cy + r * math.cos(t), cz + r * math.sin(t)) for x, r in P for t in a])
    F = []
    rows = m if loop else m - 1
    for i in range(rows):
        i2 = (i + 1) % m
        for j in range(seg):
            j2 = (j + 1) % seg
            F.append((i * seg + j, i * seg + j2, i2 * seg + j2, i2 * seg + j))
    if not loop:
        F.append(tuple(range(seg))[::-1])
        F.append(tuple((m - 1) * seg + j for j in range(seg)))
    return Geo().add(V, F)


def frame_to(p0, p1, up=(0, 0, 1)):
    """4 x 4 that maps the local x axis onto p0 -> p1 (origin p0)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    x = (p1 - p0) / np.linalg.norm(p1 - p0)
    up = np.asarray(up, float)
    if abs(np.dot(up, x)) > 0.95:
        up = np.array([0.0, 1.0, 0.0])
    y = np.cross(up, x)
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, p0
    return M


def cylinder_between(p0, p1, r, seg=24):
    L = float(np.linalg.norm(np.subtract(p1, p0)))
    return lathe_x([(0, r), (L, r)], seg).transformed(frame_to(p0, p1))


def sweep(centres, normals, section, cap=True):
    """Rings of a 2D section (u along the in-plane normal, v along y) swept along a centreline in the x-z
    plane; convex section, n-gon caps."""
    k = len(section)
    V = []
    for c, n in zip(centres, normals):
        for u, v in section:
            V.append((c[0] + u * n[0], v, c[1] + u * n[1]))
    F = []
    for i in range(len(centres) - 1):
        for j in range(k):
            j2 = (j + 1) % k
            F.append((i * k + j, i * k + j2, (i + 1) * k + j2, (i + 1) * k + j))
    if cap:
        F.append(tuple(range(k))[::-1])
        F.append(tuple((len(centres) - 1) * k + j for j in range(k)))
    return Geo().add(V, F)


def octagon(af, phase=math.pi / 8):
    """Regular octagon with the given across-flats, flats facing +-y and +-z (vertices at 22.5 + k 45 deg)."""
    rc = af / 2 / math.cos(math.pi / 8)
    return [(rc * math.cos(phase + k * math.pi / 4), rc * math.sin(phase + k * math.pi / 4)) for k in range(8)]


def chamfered_rect(w, h, c):
    """Rectangle w x h centred on the origin with corners chamfered by c (8 points, CCW)."""
    a, b = w / 2, h / 2
    return [(a, -b + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, -b + c), (-a + c, -b), (a - c, -b)]


def rounded_rect(w, h, r, per=5, cx=0.0, cy=0.0):
    r = min(r, 0.5 * min(w, h) - 1e-3)
    out = []
    for sx, sy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        c = (cx + sx * (w / 2 - r), cy + sy * (h / 2 - r))
        for t in np.radians(a0 + np.linspace(0, 90, per)):
            out.append((c[0] + r * math.cos(t), c[1] + r * math.sin(t)))
    return out


# ============================================================================ scene plumbing
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


MATS = {}


def material(key, hexcol, rough=0.5, metal=0.0, coat=0.0):
    """`Carbine.Mat.<key>`: a flat Principled colour (sampled from the reference; carbine.md §4)."""
    name = f"{PART}.Mat.{key}"
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    rgb = hex_rgb(hexcol)
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Coat Weight"].default_value = coat
    m.diffuse_color = (*rgb, 1.0)
    m.roughness = rough
    m.metallic = metal
    m["hex"] = hexcol
    MATS[key] = m
    return m


def make_materials():
    # receivers: #413c3b / #403c39 (weapon analysis §3.15); handguard #393532 (warmer, dust)
    material("Anodised", "#3e3a38", 0.55, 0.3)
    material("Handguard", "#393532", 0.55, 0.3)
    material("Hardcoat", "#2c2a29", 0.35, 0.4)        # buffer tube, light, castle nut: semi-gloss
    material("Polymer", "#3d3733", 0.6)               # stock body
    material("PolymerDark", "#1f1d1c", 0.6)           # grip, trigger guard (icon grip #121415)
    material("Rubber", "#141211", 0.85)               # butt pad
    material("Magazine", "#423e3a", 0.6)
    material("MagBase", "#595452", 0.55)
    material("Steel", "#2f2e2e", 0.35, 0.8)           # bolt carrier, gas block, pins, QD sockets
    material("SteelBright", "#8a8a8a", 0.3, 1.0)      # mag release, polished parts
    material("Bronze", "#5f4c3e", 0.4, 0.8)           # burnt-bronze barrel and A2 (take 1 D3)
    material("FDE", "#b08a62", 0.7)                   # tan paint (#a68869 .. #d4a271 in the image)
    material("Lens", "#0e1418", 0.05, 0.0, 1.0)       # optic and light glass, dark, glossy


def clean_own():
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PART + "."):
            bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.name.startswith(PART + ".") and me.users == 0:
            bpy.data.meshes.remove(me)
    c = bpy.data.collections.get(COLL)
    if c:
        bpy.data.collections.remove(c)


def collection():
    c = bpy.data.collections.get(COLL)
    if c is None:
        c = bpy.data.collections.new(COLL)
        bpy.context.scene.collection.children.link(c)
    return c


ROOT = None
OBJS = {}


def obj(component, geo, mat, *, bevel=None, smooth=35.0, real=None, density=None, fill=1.0):
    """`Carbine.<component>` from a Geo (mm), parented to the root, with a material, an optional Bevel
    (width mm) and smoothing by angle. density (g/cm3) and fill (fraction of the blockout envelope that is
    material in the real part) feed the mass estimate."""
    name = f"{PART}.{component}"
    me = bpy.data.meshes.new(name)
    me.from_pydata((np.asarray(geo.V) * MM).tolist(), [], [list(f) for f in geo.F])
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection().objects.link(ob)
    ob.parent = ROOT
    me.materials.append(MATS[mat])
    if smooth:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(smooth))
    if bevel:
        MOD.bevel(ob, bevel, 2, 35.0, harden=True)
    if real:
        ob["real_part"] = real
    if density:
        ob["density"] = density
        ob["fill"] = fill
    OBJS[component] = ob
    return ob


def cutter(geo):
    me = bpy.data.meshes.new("Carbine.Tmp.Cutter")
    me.from_pydata((np.asarray(geo.V) * MM).tolist(), [], [list(f) for f in geo.F])
    me.validate()
    ob = bpy.data.objects.new("Carbine.Tmp.Cutter", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def boolean(ob, geo, op="DIFFERENCE"):
    """Apply an EXACT boolean of the closed Geo onto ob's mesh (modifiers above it stay)."""
    cut = cutter(geo)
    keep = [(m.name, m.show_viewport, m.show_render) for m in ob.modifiers]
    for m in ob.modifiers:
        m.show_viewport = m.show_render = False
    b = ob.modifiers.new("Bool", "BOOLEAN")
    b.operation, b.solver, b.object = op, "EXACT", cut
    b.use_self = True          # the operand is a union of overlapping primitives
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.remove(b)
    for name, v, r in keep:
        ob.modifiers[name].show_viewport, ob.modifiers[name].show_render = v, r
    old = ob.data
    ob.data = new
    new.name = old.name
    bpy.data.meshes.remove(old)
    cme = cut.data
    bpy.data.objects.remove(cut, do_unlink=True)
    bpy.data.meshes.remove(cme)
    return ob


def empty(component, loc, X=None, Z=None, size=30.0, kind="ARROWS"):
    ob = bpy.data.objects.new(f"{PART}.{component}", None)
    ob.empty_display_type = kind
    ob.empty_display_size = size * MM
    collection().objects.link(ob)
    if ROOT is not None:
        ob.parent = ROOT
    M = Matrix.Identity(4)
    if X is not None:
        X, Z = Vector(X).normalized(), Vector(Z).normalized()
        Y = Z.cross(X)
        M = Matrix((X, Y, Z)).transposed().to_4x4()
    M.translation = Vector(loc) * MM
    ob.matrix_basis = M
    OBJS[component] = ob
    return ob


# ============================================================================ the build
def rail(x0, x1, base_z, top=D["rail_top"]):
    """MIL-STD-1913 rail: a 15.67 mm neck/spine up to 3.0 below the top, and the dovetail teeth (21.2 top,
    45 deg flanks to the 15.67 neck) on a 10.01 pitch with 5.23 slots, the first tooth flush with x0."""
    g = Geo()
    neck, topw, slot_d, pitch, slot = 15.67, 21.2, 3.0, 10.01, 5.23
    g.add(*_vf(box(x0, x1, -neck / 2, neck / 2, base_z, top - slot_d)))
    tooth = [(-neck / 2, top - slot_d), (neck / 2, top - slot_d), (neck / 2, top - 2.77), (topw / 2, top - 0.5),
             (topw / 2 - 0.5, top), (-topw / 2 + 0.5, top), (-topw / 2, top - 0.5), (-neck / 2, top - 2.77)]
    x = x0
    n = 0
    while x + (pitch - slot) <= x1 + 1e-6:
        g.add(*_vf(prism(tooth, x, x + pitch - slot, "yz")))
        x += pitch
        n += 1
    return g, n


def _vf(geo):
    return geo.V, geo.F


def build():
    global ROOT
    ROOT = bpy.data.objects.new(f"{PART}.Root", None)
    ROOT.empty_display_type = "ARROWS"
    ROOT.empty_display_size = 0.1
    collection().objects.link(ROOT)
    report = {}

    # ---------------------------------------------------------------- upper receiver (BCM M4 forged flat-top)
    hw = 14.5   # half width of the side walls (E)
    up_top = 20.0
    sec = [(-hw, D["parting"]), (hw, D["parting"]), (hw, 12.0), (hw - 4.0, up_top), (-hw + 4.0, up_top), (-hw, 12.0)]
    g = prism(sec, D["upper_rear"], D["receiver_face"], "yz")
    # front receiver ring (barrel-nut seat) and the takedown/pivot lugs are hidden; forward-assist housing:
    fa0, fa1 = np.array([R(-96), -13.0, 5.0]), np.array([R(-140), -22.0, 7.0])
    upper = obj("Upper", g, "Anodised", bevel=1.0, real="BCM M4 forged flat-top upper (mil-spec)",
                density=2.81, fill=0.45)
    # ejection port opening (76.2 x 20.3, Y -96.2..-20.0, Z -8.6..+11.7), cut through the right wall
    boolean(upper, box(D["port_rear"], D["port_front"], -hw - 3, -4.0, -8.6, 11.7))
    obj("Upper.ForwardAssist", Geo().add(*_vf(cylinder_between(fa0, fa1, 9.5)))
        .add(*_vf(cylinder_between(fa1, fa1 + (fa1 - fa0) / np.linalg.norm(fa1 - fa0) * 12.0, 7.0))),
        "Anodised", real="M4 forward assist, round button", density=2.81, fill=0.6)
    obj("Upper.Deflector", prism([(R(-96), -hw + 0.5), (R(-117), -hw + 0.5), (R(-108), -23.0), (R(-99), -21.0)],
                                 8.0, 22.0, "xy"), "Anodised", bevel=0.8, density=2.81)
    # dust cover, open: 78.7 x 23.4 x 1.6 hanging from its hinge rod at the port's lower edge
    obj("Upper.DustCover", box(D["port_rear"] - 1.2, D["port_front"] + 1.3, -hw - 3.3, -hw - 1.7, -12.0 - 23.4, -12.0),
        "Anodised", bevel=0.5, real="ejection-port cover, open", density=7.85)
    obj("BoltCarrier", lathe_x([(R(-120), 12.65), (R(-26), 12.65)], 32), "Steel",
        real="M16-profile bolt carrier (seen through the port)", density=7.85, fill=0.7)
    # charging handle: T-handle behind the upper over the buffer tower, latch on the LEFT (+y)
    g = box(R(-208), R(-197.5), -14.5, 14.5, 15.0, 25.0)
    g.add(*_vf(box(R(-209), R(-196), 14.0, 22.0, 16.0, 23.5)))
    obj("ChargingHandle", g, "Anodised", bevel=0.8, real="mil-spec charging handle, left latch", density=2.81)
    g, n_up = rail(D["upper_rear"] + 0.5, D["receiver_face"] - 1.5, up_top - 0.5)
    obj("Upper.Rail", g, "Anodised", bevel=0.3, smooth=None, real="MIL-STD-1913 receiver rail", density=2.81)

    # ---------------------------------------------------------------- lower receiver (BCM M4 forged lower)
    lw = 13.0
    g = prism([(D["magwell_rear"], D["parting"]), (D["lower_rear"], D["parting"]), (D["lower_rear"], -27.4),
               (D["grip_front_top"], -54.0), (D["magwell_rear"], -54.0)], -lw, lw, "xz")
    g.add(*_vf(lathe_x([(D["lower_rear"], 17.8), (D["upper_rear"] + 2.0, 17.8)], 32)))          # buffer tower
    g.add(*_vf(box(D["lower_rear"], D["upper_rear"] + 2.0, -17.0, 17.0, -27.4, 0.0)))
    mw = 15.0
    g.add(*_vf(prism([(D["magwell_front"], D["parting"]), (D["magwell_rear"], D["parting"]),
                      (D["magwell_rear"], -84.0), (D["magwell_front"], -76.5)], -mw, mw, "xz")))
    g.add(*_vf(prism([(D["magwell_front"] + 1.5, -66.0), (D["magwell_rear"] - 1.5, -73.5),
                      (D["magwell_rear"] - 1.5, -84.0), (D["magwell_front"] + 1.5, -76.5)], -mw - 1.5, mw + 1.5, "xz")))
    lower = obj("Lower", g, "Anodised", bevel=1.0, real="BCM M4 forged lower (mil-spec)", density=2.81, fill=0.4)
    # magwell opening 67 x 23, open at the bottom (the magazine enters it)
    boolean(lower, box(R(-83.5), R(-16.5), -11.5, 11.5, -95.0, -30.0))
    # trigger guard: U of a 6.5 x 4.5 bar under the lower, opening ~60 x 30
    tg = [(R(-86), -54.0), (R(-86), -92.0), (R(-152), -92.0), (R(-152), -54.0),
          (R(-147.5), -54.0), (R(-147.5), -87.5), (R(-90.5), -87.5), (R(-90.5), -54.0)]
    obj("TriggerGuard", prism(tg, -3.25, 3.25, "xz"), "PolymerDark", bevel=1.2, real="mil-spec trigger guard",
        density=2.7)
    trig = [(-3.0, -53.0), (4.0, -53.0), (3.0, -63.0), (1.0, -72.0), (-3.5, -80.0), (-5.0, -79.0), (-2.0, -70.0),
            (-0.5, -62.0)]
    obj("Trigger", prism(trig, -3.2, 3.2, "xz"), "Steel", bevel=0.4, real="mil-spec trigger", density=7.85)
    obj("MagRelease", lathe_x([(0, 4.75), (2.5, 4.75)], 24).transformed(
        frame_to((R(-74), -lw - 0.5, -38.0), (R(-74), -lw - 3.0, -38.0))), "SteelBright",
        real="mag-release button, right side", density=7.85)
    obj("BoltCatch", box(R(-96), R(-72), lw - 0.5, lw + 3.0, -27.0, -16.0), "Anodised", bevel=0.6, density=7.85)
    g = cylinder_between((R(-150), lw - 0.5, -30.0), (R(-150), lw + 2.5, -30.0), 4.75)
    g.add(*_vf(box(R(-150) - 3.5, R(-150) + 22.0, lw + 1.0, lw + 3.5, -33.5, -26.5)))
    obj("Selector", g, "Anodised", bevel=0.5, real="safety selector, left", density=7.85)

    # ---------------------------------------------------------------- pistol grip (USGI A2)
    rake = math.radians(25.0)
    axis_up = np.array([math.sin(rake), math.cos(rake)])           # (x, z), grip axis toward the receiver
    fwd = np.array([math.cos(rake), -math.sin(rake)])              # front strap direction
    front_top = np.array([D["grip_front_top"], -54.0])
    top_c = front_top - 25.0 * fwd + 6.0 * axis_up                 # top section 55 deep; 6 mm into the lower
    L = 102.0 + 6.0
    stations = []   # (t along the axis from the top, depth, width, front bulge)
    for t, d, w, nub in ((0, 50, 30.0, 0), (18, 49, 30.0, 0), (28, 47, 29.5, 3.5), (38, 46, 29.0, 0),
                         (70, 44, 28.5, 0), (L - 4, 42, 27.5, 0), (L, 40, 25.5, 0)):
        stations.append((t, d, w, nub))
    V, F = [], []
    ring = None
    for k, (t, d, w, nub) in enumerate(stations):
        c = top_c - t * axis_up
        pts = rounded_rect(d, w, 9.0, 5)
        cur = []
        for u, v in pts:
            p = c + (u + (nub if u > 0 else 0)) * fwd
            cur.append(len(V))
            V.append((p[0], v, p[1]))
        if ring is not None:
            for j in range(len(cur)):
                j2 = (j + 1) % len(cur)
                F.append((ring[j], ring[j2], cur[j2], cur[j]))
        else:
            F.append(tuple(cur)[::-1])
        ring = cur
    F.append(tuple(ring))
    obj("Grip", Geo().add(V, F), "PolymerDark", bevel=1.0, smooth=50.0, real="USGI A2 pistol grip",
        density=1.15, fill=0.45)

    # ---------------------------------------------------------------- receiver extension, castle nut, end plate
    obj("BufferTube", lathe_x([(D["lower_rear"] + 20, 14.58), (D["tube_rear"], 14.58)], 32), "Hardcoat",
        real="mil-spec carbine receiver extension, OD 1.148 in", density=2.81, fill=0.25)
    obj("CastleNut", lathe_x([(D["nut_rear"], 18.0), (D["nut_front"], 18.0)], 32), "Hardcoat", bevel=0.6,
        real="mil-spec castle nut", density=7.85, fill=0.5)
    g = lathe_x([(D["nut_front"], 19.0), (D["endplate_front"], 19.0)], 32)
    g.add(*_vf(box(D["nut_front"], D["endplate_front"], -8.0, 8.0, -32.0, -10.0)))
    g.add(*_vf(cylinder_between((D["nut_front"] - 2.0, -9.0, -26.0), (D["nut_front"] - 2.0, 9.0, -26.0), 8.0)))
    obj("Sling.EndPlate", g, "Steel", bevel=0.5, real="QD end plate (sling socket each side)", density=7.85, fill=0.8)

    # ---------------------------------------------------------------- stock (MFT BATTLELINK Minimalist, pos. 3)
    heel = np.array([D["butt_heel"], 18.0])
    toe = np.array([D["pad_toe"], -110.0])
    dvec = (toe - heel) / np.linalg.norm(toe - heel)
    nrm = np.array([-dvec[1], dvec[0]]) if (-dvec[1]) > 0 else np.array([dvec[1], -dvec[0]])   # forward

    def xr(z, inset=8.0):   # x of the frame's rear edge at height z (pad front face + inset)
        t = (z - heel[1]) / dvec[1]
        return heel[0] + t * dvec[0] + inset * nrm[0]

    sx0 = D["stock_front"]
    outer = [(sx0, 6.0), (xr(6.0), 6.0), (xr(-110.0), -110.0), (xr(-110.0) + 22, -110.0), (sx0 - 30, -97.0),
             (sx0, -92.0)]
    window = [(sx0 - 33, -28.0), (xr(-28.0, 24.0), -28.0), (xr(-86.0, 22.0), -86.0), (xr(-86.0, 22.0) + 16, -93.0),
              (sx0 - 44, -80.0), (sx0 - 36, -70.0)]
    sw = 17.0
    g = prism(outer, -sw, sw, "xz", holes=[window])
    g.add(*_vf(lathe_x([(sx0, 18.3), (xr(10.0, 6.0), 18.3)], 32)))          # tube housing over the extension
    stock = obj("Stock", g, "Polymer", bevel=2.0, smooth=40.0, real="MFT BATTLELINK Minimalist (mil-spec), pos 3 of 6",
                density=1.15, fill=0.45)
    pad = [tuple(heel), tuple(toe), tuple(toe + 8.0 * nrm), tuple(heel + 8.0 * nrm)]
    obj("Stock.ButtPad", prism(pad, -22.25, 22.25, "xz"), "Rubber", bevel=2.5, smooth=40.0,
        real="rubberised butt pad, 12 deg rake", density=1.1)
    obj("Sling.Stock.QD", cylinder_between((sx0 - 18, -sw + 0.5, -60.0), (sx0 - 18, -sw - 1.5, -60.0), 7.0),
        "Steel", real="QD socket, stock front lug (right)", density=7.85)
    report["stock_rake_deg"] = round(math.degrees(math.atan2(abs(toe[0] - heel[0]), abs(toe[1] - heel[1]))), 1)

    # ---------------------------------------------------------------- barrel, gas, muzzle device
    st = [(D["bolt_face"], 12.5), (R(14.0), 12.5), (R(14.0), 8.55), (R(60.0), 7.95), (D["barrel_step"], 7.95),
          (D["barrel_journal"], 9.525), (D["thread"], 9.525), (D["thread"], 6.35), (D["crown"], 6.35)]
    obj("Barrel", lathe_x(st, 32), "Bronze", real="16 in government-profile barrel, mid-length gas",
        density=7.85, fill=0.93)
    g = lathe_x([(D["gas_block"][0], 13.5), (D["gas_block"][1], 13.5)], 32)
    g.add(*_vf(box(D["gas_block"][0], D["gas_block"][1], -6.0, 6.0, 0.0, 16.0)))
    obj("GasBlock", g, "Steel", bevel=0.6, real="0.750 in low-profile gas block", density=7.85, fill=0.8)
    obj("GasTube", lathe_x([(D["receiver_face"] - 10, 2.29), (D["gas_block"][0] + 10, 2.29)], 12, cz=10.7),
        "Steel", real="mid-length gas tube", density=7.85, fill=0.4)
    a2 = [(D["a2_rear"] - 1.2, 10.9), (D["muzzle"], 10.9), (D["muzzle"], 7.6), (R(405.0), 7.6), (R(405.0), 3.4),
          (D["a2_rear"] - 1.2, 6.4)]
    muzzle = obj("Muzzle", lathe_x(a2, 32, loop=True), "Bronze", real="A2 birdcage flash hider (burnt bronze)",
                 density=7.85)
    cuts = Geo()
    for ang in (0, 60, 120, -60, -120):       # five slots, the bottom sector closed
        a = math.radians(ang)
        M = np.eye(4)
        M[:3, :3] = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
        cuts.add(*_vf(box(R(406.5), R(424.5), -1.3, 1.3, 5.0, 14.0).transformed(M)))
    boolean(muzzle, cuts)

    # ---------------------------------------------------------------- handguard (BCM MCMR-13, octagon 38.1 AF)
    af, idf = 38.1, 33.0
    rows = [(D["hg_rear"], af + 1.6), (D["hg_rear"] + 10.0, af + 1.6), (D["hg_rear"] + 10.0, af),
            (D["hg_front"] - 2.0, af), (D["hg_front"], af - 4.0)]
    V, F = [], []
    for x, a in rows:
        for y, z in octagon(a):
            V.append((x, y, z))
    inner0 = len(V)
    for x in (D["hg_rear"], D["hg_front"]):
        for y, z in octagon(idf):
            V.append((x, y, z))
    for i in range(len(rows) - 1):
        for j in range(8):
            j2 = (j + 1) % 8
            F.append((i * 8 + j, i * 8 + j2, (i + 1) * 8 + j2, (i + 1) * 8 + j))
    for j in range(8):    # inner wall, rear and front annuli
        j2 = (j + 1) % 8
        F.append((inner0 + 8 + j, inner0 + 8 + j2, inner0 + j2, inner0 + j))
        F.append((inner0 + j, inner0 + j2, j2, j))
        last = (len(rows) - 1) * 8
        F.append((last + j, last + j2, inner0 + 8 + j2, inner0 + 8 + j))
    g = Geo().add(V, F)
    rg, n_hg = rail(D["hg_rear"] + 1.0, D["hg_front"] - 0.5, af / 2 - 1.0)
    g.add(*_vf(rg))
    hg = obj("Handguard", g, "Handguard", bevel=0.6, smooth=None, real="BCM MCMR-13 M-LOK free-float handguard",
             density=2.7, fill=1.0)
    cuts = Geo()
    slots = [R(14 + 40 * k) for k in range(8)]
    for x in slots:               # M-LOK 32 x 7 at 3, 6 and 9 o'clock
        cuts.add(*_vf(box(x, x + 32.0, -af / 2 - 3, -af / 2 + 3.5, -3.5, 3.5)))       # 3 o'clock (right, -y)
        cuts.add(*_vf(box(x, x + 32.0, af / 2 - 3.5, af / 2 + 3, -3.5, 3.5)))         # 9 o'clock (left)
        cuts.add(*_vf(box(x, x + 32.0, -3.5, 3.5, -af / 2 - 3, -af / 2 + 3.5)))       # 6 o'clock
    holes = [R(105 + 26 * k) for k in range(7)]
    for x in holes:               # lightening holes, 10 mm, on the 4:30 and 7:30 bevels
        for s in (-1, 1):
            n = np.array([0.0, s * 0.7071, -0.7071])
            c = np.array([x, 0.0, 0.0])
            cuts.add(*_vf(cylinder_between(c + 14.0 * n, c + 23.0 * n, 5.0, 20)))
    boolean(hg, cuts)
    obj("Sling.Handguard.QD", cylinder_between((R(270), af / 2 - 0.5, 0.0), (R(270), af / 2 + 1.5, 0.0), 7.0),
        "Steel", real="M-LOK QD socket, left side", density=7.85)

    # ---------------------------------------------------------------- weapon light (SureFire M300C) + offset mount
    ly, lz = -32.0, 16.0
    light = [(R(10), 11.0), (R(12), 12.0), (R(34), 12.0), (R(34), 11.0), (R(76), 11.0), (R(90), 14.3),
             (R(113.2), 14.3), (R(114), 13.5)]
    obj("Light", lathe_x(light, 32, cy=ly, cz=lz), "Hardcoat", real="SureFire M300C Mini Scout light",
        density=2.7, fill=0.55)
    obj("Light.Lens", lathe_x([(R(113.6), 12.0), (R(114.2), 12.0)], 32, cy=ly, cz=lz), "Lens", density=2.5)
    mount = [(-af / 2 + 0.5, -9.0), (-af / 2 - 4.5, -9.0), (ly - 3.0, lz - 10.0), (ly + 4.0, lz - 9.0),
             (-af / 2 + 0.5, 4.0)]
    obj("Light.Mount", prism(mount, R(16), R(44), "yz"), "Anodised", bevel=0.8,
        real="Arisaka Offset Scout Mount, M-LOK, first 3 o'clock slot", density=2.7)

    # ---------------------------------------------------------------- optic (Aimpoint Micro T-2 on LRP + 39 mm)
    oz = D["rail_top"] + 39.0
    ox0, ox1 = R(-174), R(-106)
    g = lathe_x([(ox0, 14.0), (ox0 + 4, 15.0), (ox1 - 12, 15.0), (ox1 - 8, 16.5), (ox1, 16.5)], 32, cz=oz)
    obj("Optic", g, "Hardcoat", real="Aimpoint Micro T-2", density=2.7, fill=0.5)
    g = cylinder_between(((ox0 + ox1) / 2 + 4, 0, oz + 13.0), ((ox0 + ox1) / 2 + 4, 0, oz + 21.0), 6.5)
    g.add(*_vf(cylinder_between(((ox0 + ox1) / 2 + 4, -13.0, oz), ((ox0 + ox1) / 2 + 4, -21.0, oz), 6.5)))
    obj("Optic.Turrets", g, "Hardcoat", density=2.7)
    for nm, x in (("Optic.Lens.Rear", ox0 + 0.6), ("Optic.Lens.Front", ox1 - 1.0)):
        obj(nm, lathe_x([(x - 0.4, 12.0), (x + 0.4, 12.0)], 32, cz=oz), "Lens", density=2.5)
    mx0, mx1 = R(-160), R(-118)
    g = box(mx0, mx1, -16.0, 16.0, D["rail_top"] - 2.0, D["rail_top"] + 7.0)
    g.add(*_vf(prism([(-11, D["rail_top"] + 6.0), (11, D["rail_top"] + 6.0), (8, oz - 13.0), (-8, oz - 13.0)],
                     mx0 + 3, mx1 - 3, "yz")))
    g.add(*_vf(box(mx0 + 8, mx1 - 8, -21.0, -16.0, D["rail_top"] - 1.0, D["rail_top"] + 6.0)))   # LRP lever
    obj("Optic.Mount", g, "Anodised", bevel=0.8, real="Aimpoint LRP mount + 39 mm spacer", density=2.7, fill=0.7)

    # ---------------------------------------------------------------- magazine (PMAG 30 GEN M3, constant curve)
    mx, mtop, straight, arc, Rc = R(-49.0), -14.5, 76.0, 108.5, 400.0
    cs, ns = [], []
    for z in np.linspace(mtop, mtop - straight, 8):
        cs.append((mx, z))
        ns.append((1.0, 0.0))
    th_end = arc / Rc
    for th in np.linspace(0, th_end, 13)[1:]:
        cs.append((mx + Rc - Rc * math.cos(th), mtop - straight - Rc * math.sin(th)))
        ns.append((math.cos(th), math.sin(th)))
    body = sweep(cs, ns, [(u, v) for u, v in chamfered_rect(64.0, 22.0, 2.5)])
    ribs = Geo()
    k0 = 9
    for u in (-16.0, 0.0, 16.0):
        for s in (-1, 1):
            sect = [(u - 1.2, s * 10.5), (u + 1.2, s * 10.5), (u + 1.2, s * 11.8), (u - 1.2, s * 11.8)]
            ribs.add(*_vf(sweep(cs[k0:-1], ns[k0:-1], sect)))
    body.add(*_vf(ribs))
    obj("Magazine", body, "Magazine", bevel=0.6, smooth=40.0, real="Magpul PMAG 30 AR/M4 GEN M3",
        density=1.3, fill=0.25)
    c, n = np.array(cs[-1]), np.array(ns[-1])
    t = np.array([n[1], -n[0]])         # tangent (down along the spine)
    fp = sweep([tuple(c), tuple(c + 6.0 * t)], [tuple(n), tuple(n)], rounded_rect(66.6, 24.6, 5.0, 4))
    obj("Magazine.Floorplate", fp, "MagBase", bevel=0.8, real="PMAG flared floorplate", density=1.3, fill=0.6)
    report["mag_floor_tilt_deg"] = round(math.degrees(th_end), 1)

    # ---------------------------------------------------------------- tan paint (the drawing's FDE accents)
    def patch(nm, x0, x1, z0, z1, y, side=-1):
        return obj(f"Paint.{nm}", box(x0, x1, y, y + side * 0.4, z0, z1), "FDE", smooth=None, density=1.2)
    patch("StockStripe", R(-370), R(-300), -26.0, -20.0, -sw)
    patch("StockLug", sx0 - 33, sx0 - 3, -88.0, -32.0, -sw - 0.05)
    patch("UpperStripe", R(-196), R(-152), 8.0, 18.0, -hw)
    patch("LowerMark", R(-55), R(-48), -48.0, -20.0, -mw)
    patch("MagwellFront", R(-16), R(-10.5), -50.0, -36.0, -mw)
    hgf = -af / 2
    patch("HandguardA", R(56), R(76), -7.5, 7.0, hgf)
    patch("HandguardB", R(80), R(96), -7.5, 6.0, hgf)

    # ---------------------------------------------------------------- hand empties
    # right palm on the A2 grip's right side, 48 mm down the axis from the receiver (index on the trigger)
    p = top_c - 54.0 * axis_up - 4.0 * fwd
    empty("Grip.R", (p[0], -15.0, p[1]), X=(axis_up[0], 0, axis_up[1]), Z=(0, 1, 0))
    # left hand overhand on the handguard (reference: back of the hand over the rail, fingers down the right
    # face, tips under the 4:30 bevel): palm centre over the 11 o'clock side, at take 1's station R.y 170
    d11 = np.array([0.0, 0.5, 0.866])
    q = np.array([R(170.0), 0.0, 0.0]) + 20.3 * d11
    empty("Grip.L", tuple(q), X=(-1, 0, 0), Z=tuple(-d11))
    report["rail_slots"] = {"receiver_teeth": n_up, "handguard_teeth": n_hg}
    return report


# ============================================================================ measurements
def mesh_world_mm(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    M = np.array(ROOT.matrix_world.inverted() @ ob.matrix_world)
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    oe.to_mesh_clear()
    return co / MM


def volume_cm3(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    v = abs(bm.calc_volume(signed=True))
    bm.free()
    return v * 1e6


def measure(extra):
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    parts = {}
    for k, ob in OBJS.items():
        if ob.type != "MESH":
            continue
        co = mesh_world_mm(ob)
        lo, hi = np.minimum(lo, co.min(0)), np.maximum(hi, co.max(0))
        parts[k] = (co.min(0), co.max(0))
    nb = lambda keys: (np.min([parts[k][0] for k in keys], 0), np.max([parts[k][1] for k in keys], 0))  # noqa: E731
    no_optic = [k for k in parts if not k.startswith("Optic")]
    gun = [k for k in no_optic if not k.startswith("Magazine")]
    b = parts["Barrel"]
    mass, solid = {}, 0.0
    for k, ob in OBJS.items():
        if ob.type == "MESH" and "density" in ob:
            v = volume_cm3(ob)
            m_solid = v * ob["density"]
            solid += m_solid
            mass[k] = (round(v, 1), round(m_solid), round(m_solid * ob["fill"]))
    est = sum(m[2] for m in mass.values())
    rounds = 30 * 12.0     # 30 x M855 ball, 12.0 g each
    out = {
        "overall_length_mm": round(hi[0] - lo[0], 1),
        "butt_heel_x": round(lo[0], 1), "muzzle_x": round(hi[0], 1),
        "barrel_length_bolt_face_to_crown_mm": round(b[1][0] - b[0][0], 1),
        "barrel_ahead_of_handguard_mm": round(parts["Muzzle"][1][0] - parts["Handguard"][1][0], 1),
        "height_overall_mm (optic top to floorplate)": round(hi[2] - lo[2], 1),
        "height_without_optic_mm": round(nb(no_optic)[1][2] - nb(no_optic)[0][2], 1),
        "height_without_optic_or_mag_mm (rail top to grip)": round(nb(gun)[1][2] - nb(gun)[0][2], 1),
        "width_overall_mm": round(hi[1] - lo[1], 1),
        "length_of_pull_mm (trigger to pad centre)": round(0.0 - (D["butt_heel"] + D["pad_toe"]) / 2, 1),
        "mass_solid_blockout_g": round(solid),
        "mass_estimate_g (fill factors, empty magazine)": round(est),
        "mass_estimate_loaded_g": round(est + rounds),
        "mass_by_part (cm3, solid g, estimate g)": mass,
    }
    out.update(extra)
    return out


# ============================================================================ renders
def look_at(cam, pos, target, up=(0, 0, 1)):
    pos, target = Vector(pos) * MM, Vector(target) * MM
    d = (target - pos).normalized()
    q = d.to_track_quat("-Z", "Y")
    cam.matrix_world = q.to_matrix().to_4x4()
    cam.location = pos


def render_rig():
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new("Carbine.Aux.Cam")
    cam = bpy.data.objects.new("Carbine.Aux.Cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_data.sensor_width = 36.0
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.clip_start = 0.01
    cam_data.clip_end = 100
    if sc.world is None:
        sc.world = bpy.data.worlds.new("Carbine.Aux.World")
    sc.world.use_nodes = True
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    return cam


def workbench(sc, colour="MATERIAL", bg=(0.82, 0.82, 0.8)):
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = colour
    sh.single_color = (0.72, 0.70, 0.66)
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.cavity_ridge_factor = 1.0
    sh.cavity_valley_factor = 1.0
    sh.show_object_outline = True
    sh.object_outline_color = (0.0, 0.0, 0.0)
    sh.show_specular_highlight = True
    sc.display.render_aa = "16"
    sc.world.color = bg
    sc.render.film_transparent = False


def scale_bar(origin, along, across, name="Carbine.Aux.Bar"):
    """A 100 mm bar of ten 10 mm black/white cells with end ticks (mm), in the plane of along/across."""
    o, a, c = np.array(origin, float), np.array(along, float), np.array(across, float)
    mk = {}
    for col, hexc in (("B", "#000000"), ("W", "#ffffff")):
        m = bpy.data.materials.get(f"Carbine.Aux.{col}") or bpy.data.materials.new(f"Carbine.Aux.{col}")
        m.diffuse_color = (*hex_rgb(hexc), 1.0)
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*hex_rgb(hexc), 1.0)
        mk[col] = m
    obs = []
    for i in range(10):
        p0 = o + 10.0 * i * a
        quad = [p0, p0 + 10 * a, p0 + 10 * a + 4 * c, p0 + 4 * c]
        me = bpy.data.meshes.new(f"{name}.{i}")
        me.from_pydata([(np.asarray(q) * MM).tolist() for q in quad], [], [[0, 1, 2, 3]])
        me.materials.append(mk["B" if i % 2 == 0 else "W"])
        ob = bpy.data.objects.new(f"{name}.{i}", me)
        bpy.context.scene.collection.objects.link(ob)
        obs.append(ob)
    for i, x in enumerate((0.0, 100.0)):
        p0 = o + x * a - 0.6 * a
        quad = [p0 - 3 * c, p0 + 1.2 * a - 3 * c, p0 + 1.2 * a + 7 * c, p0 + 7 * c]
        me = bpy.data.meshes.new(f"{name}.T{i}")
        me.from_pydata([(np.asarray(q) * MM).tolist() for q in quad], [], [[0, 1, 2, 3]])
        me.materials.append(mk["B"])
        ob = bpy.data.objects.new(f"{name}.T{i}", me)
        bpy.context.scene.collection.objects.link(ob)
        obs.append(ob)
    txt = bpy.data.curves.new(f"{name}.Txt", "FONT")
    txt.body = "100 mm"
    txt.size = 9 * MM
    to = bpy.data.objects.new(f"{name}.Txt", txt)
    to.data.materials.append(mk["B"])
    M = np.eye(4)
    nrm = np.cross(a, c)
    M[:3, 0], M[:3, 1], M[:3, 2] = a, c, nrm
    M[:3, 3] = (o + 105 * a) * MM
    to.matrix_world = Matrix(M.tolist())
    bpy.context.scene.collection.objects.link(to)
    obs.append(to)
    return obs


def remove(obs):
    for ob in obs:
        bpy.data.objects.remove(ob, do_unlink=True)


def render(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if sc.render.film_transparent else "RGB"
    bpy.ops.render.render(write_still=True)
    print(f"[carbine] wrote {path}", flush=True)


def cycles(sc, samples=96):
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.max_bounces = 6
    print("[carbine] cycles device:", env.use_device(sc), flush=True)


def studio_lights(target=(120, 0, -30), key_dir=(0.3, -1.0, 0.8)):
    obs = []
    t = Vector(target) * MM

    def area(name, d, power, size, colour):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.size, ld.color = power, size, colour
        ob = bpy.data.objects.new(name, ld)
        bpy.context.scene.collection.objects.link(ob)
        pos = t + Vector(d).normalized() * 1.6
        ob.location = pos
        ob.rotation_euler = (t - pos).to_track_quat("-Z", "Y").to_euler()
        obs.append(ob)
    area("Carbine.Aux.Key", key_dir, 45.0, 1.2, (1.0, 0.95, 0.88))
    area("Carbine.Aux.Fill", (-0.6, -0.8, 0.2), 12.0, 2.0, (0.9, 0.95, 1.0))
    area("Carbine.Aux.Rim", (0.2, 1.0, 0.6), 40.0, 1.0, (0.75, 0.85, 1.0))
    return obs


def world_colour(sc, rgb, strength=1.0):
    nt = sc.world.node_tree
    bg = nt.nodes.get("Background")
    bg.inputs["Color"].default_value = (*rgb, 1.0)
    bg.inputs["Strength"].default_value = strength


def image_np(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)


def save_np(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new("Carbine.Aux.Sheet", w, h, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(arr, np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    print(f"[carbine] wrote {path}", flush=True)


# Hero placement estimate (take 1, spec 08 §4.8 solve, before the pose agent's own): rifle frame R in the
# character frame W (mm), and the reference camera of analysis_consolidated §8.
HERO_O = np.array([-67.0, -346.0, 1014.0])
HERO_RX = np.array([-0.271, -0.883, 0.384])
HERO_RY = np.array([0.441, -0.468, -0.766])
HERO_RZ = np.array([0.856, -0.038, 0.516])
CROP = (630, 230, 950, 570)   # crop_hands_rifle.png, x3


def hero_root_matrix():
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2] = HERO_RY, -HERO_RX, HERO_RZ      # this frame's X, Y, Z in W
    M[:3, 3] = (HERO_O + (-122.0) * HERO_RY) * MM
    return Matrix(M.tolist())


def renders(meas):
    os.makedirs(OUT_DIR, exist_ok=True)
    sc = bpy.context.scene
    cam = render_rig()
    cd = cam.data
    cx = (meas["butt_heel_x"] + meas["muzzle_x"]) / 2

    # left side (the gun's left, +Y), orthographic, 100 mm bar
    workbench(sc, "MATERIAL")
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 2400, 960, 100
    cd.type, cd.ortho_scale = "ORTHO", 0.95
    look_at(cam, (cx, 1500, -62), (cx, 0, -62))
    bar = scale_bar((cx + 420, 30, -235), (-1, 0, 0), (0, 0, 1))   # along -X so the label reads from +Y
    render(os.path.join(OUT_DIR, "carbine_left_ortho.png"))
    remove(bar)

    # right side (the reference's side), orthographic, bar; compared with the icon crop
    look_at(cam, (cx, -1500, -62), (cx, 0, -62))
    bar = scale_bar((cx - 420, -30, -235), (1, 0, 0), (0, 0, 1))
    render(os.path.join(OUT_DIR, "carbine_right_ortho.png"))
    remove(bar)

    # top, orthographic (muzzle to the right, the gun's left at the top of the frame)
    sc.render.resolution_y = 640
    look_at(cam, (cx, 0, 1500), (cx, 0, 0))
    cam.matrix_world = Matrix(((1, 0, 0, cx * MM), (0, 1, 0, 0), (0, 0, 1, 1.5), (0, 0, 0, 1)))
    bar = scale_bar((cx - 420, -110, 120), (1, 0, 0), (0, 1, 0))
    render(os.path.join(OUT_DIR, "carbine_top_ortho.png"))
    remove(bar)

    # three-quarter views from the right-front-above (the reference side)
    sc.render.resolution_x, sc.render.resolution_y = 2000, 1250
    cd.type, cd.lens = "PERSP", 50.0
    tgt = (cx, 0, -40)
    look_at(cam, (cx + 480, -1250, 400), tgt)
    workbench(sc, "SINGLE", bg=(0.86, 0.86, 0.84))
    render(os.path.join(OUT_DIR, "carbine_34_clay.png"))
    cycles(sc, 128)
    world_colour(sc, (0.18, 0.18, 0.19), 0.6)
    lights = studio_lights(tgt)
    render(os.path.join(OUT_DIR, "carbine_34_cycles.png"))
    remove(lights)

    # hero direction: the carbine at take 1's solved placement, the reference camera, the crop region only
    ROOT.matrix_world = hero_root_matrix()
    bpy.context.view_layer.update()
    cam.matrix_world = Matrix.Identity(4)
    cam.location = (0.0, -4.5, 0.6)
    cam.rotation_euler = (math.radians(93.9), 0.0, 0.0)
    cd.lens = 46.0
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1672, 941, 300
    x0, y0, x1, y1 = CROP
    sc.render.use_border, sc.render.use_crop_to_border = True, True
    sc.render.border_min_x, sc.render.border_max_x = x0 / 1672, x1 / 1672
    sc.render.border_min_y, sc.render.border_max_y = 1 - y1 / 941, 1 - y0 / 941
    sc.render.film_transparent = True
    world_colour(sc, (0.25, 0.25, 0.27), 0.5)
    # reference light (analysis_consolidated §8, simplified): warm key from the camera's upper left, cool rim
    # from his left (viewer's right) and behind
    hero_t = (0, -300, 900)
    lights = studio_lights(hero_t, key_dir=(-0.6, -1.0, 0.7))
    hero_png = os.path.join(OUT_DIR, "carbine_hero_render.png")
    render(hero_png)
    remove(lights)
    sc.render.use_border = False
    sc.render.film_transparent = False
    ROOT.matrix_world = Matrix.Identity(4)

    ref = image_np(REF_CROP)
    rnd = image_np(hero_png)
    h, w = min(ref.shape[0], rnd.shape[0]), min(ref.shape[1], rnd.shape[1])
    ref, rnd = ref[-h:, :w], rnd[-h:, :w]     # images load bottom-up; align top rows
    a = rnd[..., 3:4]
    solo = rnd[..., :3] * a + 0.12 * (1 - a)
    over = rnd[..., :3] * a * 0.65 + ref[..., :3] * (1 - 0.65 * a)
    gap = np.ones((h, 12, 3), np.float32)
    sheet = np.concatenate([ref[..., :3], gap, solo, gap, over], 1)
    sheet = np.concatenate([sheet, np.ones((h, sheet.shape[1], 1), np.float32)], 2)
    save_np(sheet, os.path.join(OUT_DIR, "carbine_hero_vs_ref.png"))

    remove([cam])


# ============================================================================ main
def main():
    if KEEP_SCENE:
        clean_own()
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    make_materials()
    extra = build()
    bpy.context.view_layer.update()
    meas = measure(extra)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "measure.json"), "w") as f:
        json.dump(meas, f, indent=1, default=float)
    print("[carbine] measurements:")
    for k, v in meas.items():
        if k != "mass_by_part (cm3, solid g, estimate g)":
            print(f"  {k}: {v}")
    for k, v in meas["mass_by_part (cm3, solid g, estimate g)"].items():
        print(f"    {k:24s} {v}")
    if not KEEP_SCENE:
        os.makedirs(os.path.dirname(BLEND), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
        print(f"[carbine] saved {BLEND}", flush=True)
    if DO_RENDER:
        renders(meas)


main()
