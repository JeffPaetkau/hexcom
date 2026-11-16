"""Carbine, take 2 round 2: the soldier's M4-pattern carbine with the forms of the real parts.

    "$SGT_BLENDER" -b --python scripts/parts/carbine.py [-- --no-render] [--keep-scene]

Builds every component as its own object, `Carbine.<Component>`, in the collection `Part.Carbine`, parented
to one root empty `Carbine.Root`, saves `cache/parts/carbine.blend`, prints and writes the measurements
(`renders/carbine/measure.json`) and renders the round's views into `renders/carbine/`. Notes, sources and
decisions: `scripts/parts/carbine.md` (round 1 the blockout, round 2 the forged and moulded forms).

Frame (shared with the pose agent): `Carbine.Root` sits on the bore axis directly above the trigger face;
local +X runs along the bore toward the muzzle, +Z up through the top rail, +Y to the gun's LEFT (so -Y is
the ejection-port side, the side the hero camera sees). Millimetres in this file, metres in Blender. Take
1's rifle frame R (archive/v1/spec/15_carbine.md: origin bore x receiver front face, +Y muzzle, +X gun's
right) maps as  x = R.y + 122,  y = -R.x,  z = R.z  (the trigger face is at R.y = -122).

Hand empties (consumed by the pose solve): `Carbine.Grip.R` and `Carbine.Grip.L` sit at the centre of each
palm's contact with the gun. Their axes: local +Z = the palm normal pointing INTO the gun, local +X = across
the palm from the little finger toward the index finger, +Y = Z x X. Round 2 kept both where round 1 put
them (the grip's right face and the handguard's 10:30 bevel did not move); the script prints each one's
distance to the surface it rests on.

Construction (round 2): each part's hull is one manifold solid, built from closed primitives (prisms of
filleted outlines, lofts of rounded sections, lathes, convex hulls), joined by EXACT unions and cut by EXACT
differences, then smoothed by angle and finished with a Bevel and a Weighted Normal modifier. No Subdivision anywhere
(take 1: triangle fans under subdivision made Cycles renders take minutes); flat caps are n-gons.
Materials: the receivers, handguard, tube, light and optic use the library's `Metal.Gunmetal` recipe
re-tuned toward black hardcoat (dark F0, broad roughness, edges worn to bare aluminium); the stock, grip and
magazine use `Polymer.Black.Smooth` re-coloured; the rest stay flat colours (carbine.md §4).

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
from lib import materials as LIBMAT  # noqa: E402
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
    rail_top=30.2, rail_base=22.6, parting=-17.0,
)
UPPER_HW = 15.5      # upper receiver side walls (take 1 §3.2: 31.0 over the walls)
LOWER_HW = 15.0      # lower receiver fire-control pocket walls
MAGWELL_HW = 13.8    # magwell outer (27.6 wide); its lip flares 2.0 more
HG_AF, HG_ID = 38.1, 33.0   # MCMR-13: 1.50 in across the flats, 1.30 in inside


def lip_z(x):
    """The magwell's bottom lip, raked 6 deg: Z -76.5 at its front (R -10), -84.0 at its rear (R -88)."""
    return -76.5 + (x - D["magwell_front"]) * (7.5 / (D["magwell_front"] - D["magwell_rear"]))


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

    def add(self, V, F=None):
        if isinstance(V, Geo):
            V, F = V.V, V.F
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
    plane 'xz': (a, b) = (x, z), extruded along y; 'yz': (y, z) along x; 'xy': (x, y) along z.
    Without holes the caps are single n-gons; with holes they are triangulated."""
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
    if not holes:
        F.append(tuple(range(n))[::-1])
        F.append(tuple(n + i for i in range(n)))
    else:
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


def loft(rings, cap0=True, cap1=True):
    """Quads between successive rings of equal point count (each ring a closed loop of 3D points), n-gon
    caps at the ends."""
    Rg = [np.asarray(r, float) for r in rings]
    k = len(Rg[0])
    V = np.vstack(Rg)
    F = []
    for i in range(len(Rg) - 1):
        for j in range(k):
            j2 = (j + 1) % k
            F.append((i * k + j, i * k + j2, (i + 1) * k + j2, (i + 1) * k + j))
    if cap0:
        F.append(tuple(range(k))[::-1])
    if cap1:
        F.append(tuple((len(Rg) - 1) * k + j for j in range(k)))
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


def lathe_between(p0, p1, stations, seg=32):
    """lathe_x stations (distance from p0 along p0 -> p1, radius) placed on the segment p0 -> p1."""
    return lathe_x(stations, seg).transformed(frame_to(p0, p1))


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


def catmull(P, n=6):
    """Catmull-Rom through the 2D points P, n samples per span, ends included."""
    P = np.asarray(P, float)
    ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1])
    return np.array(out)


def fillet(poly, radii, n=6):
    """A closed 2D polygon with each corner rounded by its radius (a scalar or one per corner; 0 keeps the
    corner sharp), n points per arc; radii shrink where two corners would overlap."""
    P = [np.array(p, float) for p in poly]
    m = len(P)
    radii = [radii] * m if np.isscalar(radii) else list(radii)
    out = []
    for i in range(m):
        v, p, q, r = P[i], P[i - 1], P[(i + 1) % m], radii[i]
        if r <= 0:
            out.append(tuple(v))
            continue
        a, b = p - v, q - v
        la, lb = np.linalg.norm(a), np.linalg.norm(b)
        a, b = a / la, b / lb
        th = math.acos(float(np.clip(np.dot(a, b), -1.0, 1.0)))
        if th < 1e-3 or th > math.pi - 1e-3:
            out.append(tuple(v))
            continue
        d = r / math.tan(th / 2)
        dmax = 0.45 * min(la, lb)
        if d > dmax:
            d = dmax
            r = d * math.tan(th / 2)
        s, e = v + a * d, v + b * d
        bis = (a + b) / np.linalg.norm(a + b)
        c = v + bis * (r / math.sin(th / 2))
        a0 = math.atan2(s[1] - c[1], s[0] - c[0])
        a1 = math.atan2(e[1] - c[1], e[0] - c[0])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for t in np.linspace(0, 1, n):
            ang = a0 + da * t
            out.append((c[0] + r * math.cos(ang), c[1] + r * math.sin(ang)))
    return out


def rect_f(u0, u1, v0, v1, radii, n=6):
    """Rectangle [u0, u1] x [v0, v1] with filleted corners; radii in the order (u1, v0), (u1, v1), (u0, v1),
    (u0, v0); the same corner order every call, so rings made by it loft cleanly."""
    return fillet([(u1, v0), (u1, v1), (u0, v1), (u0, v0)], radii, n)


def resample(poly, m):
    """A closed polyline resampled to m points evenly spaced by arc length, from its first point."""
    P = np.asarray(poly, float)
    Q = np.vstack([P, P[:1]])
    seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    t = np.linspace(0, s[-1], m, endpoint=False)
    return np.c_[np.interp(t, s, Q[:, 0]), np.interp(t, s, Q[:, 1])]


def isect(p, d, q, e):
    """Intersection of the 2D lines p + s d and q + t e."""
    A = np.array([[d[0], -e[0]], [d[1], -e[1]]], float)
    s, _ = np.linalg.solve(A, np.subtract(q, p))
    return np.asarray(p, float) + s * np.asarray(d, float)


def hull(points):
    """Convex hull of 3D points (mm), coplanar triangles merged into n-gons."""
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    res = bmesh.ops.convex_hull(bm, input=list(bm.verts))
    junk = [g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)]
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), verts=list(bm.verts), edges=list(bm.edges))
    bm.verts.index_update()
    V = [tuple(v.co) for v in bm.verts]
    F = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return Geo().add(V, F)


def octagon(af, phase=math.pi / 8):
    """Regular octagon with the given across-flats, flats facing +-y and +-z (vertices at 22.5 + k 45 deg)."""
    rc = af / 2 / math.cos(math.pi / 8)
    return [(rc * math.cos(phase + k * math.pi / 4), rc * math.sin(phase + k * math.pi / 4)) for k in range(8)]


def rounded_rect(w, h, r, per=5, cx=0.0, cy=0.0):
    r = min(r, 0.5 * min(w, h) - 1e-3)
    out = []
    for sx, sy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        c = (cx + sx * (w / 2 - r), cy + sy * (h / 2 - r))
        for t in np.radians(a0 + np.linspace(0, 90, per)):
            out.append((c[0] + r * math.cos(t), c[1] + r * math.sin(t)))
    return out


def corner_cut(cx, cz, r, sx, sz, y0, y1, n=8):
    """Cutter (plane xz, extruded y0..y1) that rounds the corner (cx, cz) of a side profile with radius r;
    sx, sz = +-1 point from the profile's inside toward the corner."""
    c = (cx - sx * r, cz - sz * r)
    a0, a1 = math.atan2(0.0, sx), math.atan2(sz, 0.0)
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    pts = [(cx + sx * 2, cz + sz * 2), (cx + sx * 2, cz - sz * r)]
    pts += [(c[0] + r * math.cos(a0 + da * t), c[1] + r * math.sin(a0 + da * t)) for t in np.linspace(0, 1, n)]
    pts.append((cx - sx * r, cz + sz * 2))
    return prism(pts, y0, y1, "xz")


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


def lib_material(key, recipe, hexcol, **overrides):
    """`Carbine.Mat.<key>` from the materials library (scripts/lib/materials.py) with overrides, the key as
    the library's variant (round 5: the library names it `<Part>.Mat.<Variant>` itself, so one recipe serves
    several finishes and lint checks the name). hexcol is the solid-view colour (the Workbench ortho views)."""
    m = LIBMAT.get(recipe, PART, key, **overrides)
    m.diffuse_color = (*hex_rgb(hexcol), 1.0)
    m["hex"] = hexcol
    MATS[key] = m
    return m


ALU_F0 = (0.62, 0.62, 0.63)   # bare 6061/7075 under worn hardcoat, darkened by grime (aluminium F0 0.91)


def make_materials():
    # Round 5 (materials round): round 2's recipes tuned darker and more neutral toward the reference (the hero
    # render's carbine read warm and a stop bright: median (80, 62, 46) against (58, 54, 52)), the dust lighter,
    # and the remaining flat colours moved onto library recipes with a little honest wear (edges, chips on the
    # brushed FDE, soot-dark bronze).
    # Type III hardcoat anodise (receivers, handguard): read as a near-black metal with a broad sheen;
    # edges worn to bare aluminium. The reference reads #413c3b lit (weapon analysis §3.15).
    # round 8: the hero frame's median (with the evaluation light corrected) put the carbine at half the
    # reference's luminance: the hardcoat's F0 0.060 -> 0.080 (still a near-black metal), the polymers lighter
    # (0.095 overshot in the round-8 pose: median ratio 0.66)
    # round 9 (critics r8 m27, m38: "one flat dark grey, no edge wear"; m28: the handguard top "zebra stripes"): the
    # receivers' worn edges wider and greyer (ref/zoom_carbine15_whole_bright_x3: light wear on every edge), more dust;
    # the handguard's rail teeth were the zebra: each 1913 tooth's two edges worn to bright aluminium over a flat,
    # glossy top that mirrored the key, so the handguard's edge wear is now faint and darker and its finish rougher
    lib_material("Anodised", "Metal.Gunmetal", "#3e3a38", f0=(0.080, 0.080, 0.082), rough_range=(0.46, 0.62),
                 aniso=0.0, edge__f0=(0.40, 0.40, 0.41), edge__rough=0.40, edge__amount=0.5, edge__radius_mm=0.6,
                 dust__amount=0.3, grime__amount=0.45)
    # (a sharper edge mask, width 0.03, made the upper's integral rail teeth silver stripes and still found no
    # wear on the receivers' long edges: the metal builder's mask compares with the shading normal, which the
    # weighted-normal receivers already round; the edge wear the reference shows needs the library's edge_true)
    lib_material("Handguard", "Metal.Gunmetal", "#393532", f0=(0.075, 0.075, 0.077), rough_range=(0.58, 0.72),
                 aniso=0.0, edge__f0=(0.24, 0.24, 0.25), edge__rough=0.45, edge__amount=0.18, edge__radius_mm=0.25,
                 dust__amount=0.3, grime__amount=0.45)
    # semi-gloss hardcoat: buffer tube, castle nut, light, optic
    lib_material("Hardcoat", "Metal.Gunmetal", "#2c2a29", f0=(0.060, 0.060, 0.061), rough_range=(0.32, 0.44),
                 aniso=0.0, edge__f0=ALU_F0, edge__rough=0.28, edge__amount=0.45, dust__amount=0.05,
                 grime__amount=0.25)
    # glass-filled nylon / polymer: stock, grip and trigger guard, magazine (Stealth Gray PMAG)
    lib_material("Polymer", "Polymer.Black.Smooth", "#3d3733", albedo_hex="#333231", rough=0.52,
                 rough_span=0.14, dust__amount=0.12)
    lib_material("PolymerDark", "Polymer.Black.Smooth", "#1f1d1c", albedo_hex="#2a2a29", rough=0.48,
                 rough_span=0.12, dust__amount=0.08)
    lib_material("Magazine", "Polymer.Black.Smooth", "#423e3a", albedo_hex="#434240", rough=0.56,
                 rough_span=0.14, dust__amount=0.15)
    lib_material("Rubber", "Rubber.Moulded.Black", "#141211", rough=0.78, rough_range=(0.72, 0.85))   # butt pad
    lib_material("MagBase", "Polymer.Black.Smooth", "#4a4644", albedo_hex="#33312f", rough=0.6, dust__amount=0.2)
    lib_material("Steel", "Metal.Steel.Phosphate", "#2f2e2e")                    # bolt carrier, gas block, pins
    lib_material("SteelBright", "Metal.Gunmetal", "#8a8a8a", f0=(0.45, 0.45, 0.46), rough_range=(0.28, 0.38),
                 aniso=0.0)                                                         # mag release, polished parts
    # round 8 (critic m5): the barrel and the A2 were Burnt Bronze Cerakote (take 1 D3) and read as bare copper
    # against the black gun; the reference's muzzle is dark like the rest of it. Now manganese-phosphate steel
    # (the barrel) and black-phosphate steel (the flash hider, sooty, its tines' edges worn to grey steel)
    lib_material("Barrel", "Metal.Steel.Phosphate", "#2f2e2e", f0=(0.055, 0.055, 0.057), rough_range=(0.50, 0.62),
                 edge__amount=0.45, grime__amount=0.5)
    lib_material("Muzzle", "Metal.Steel.Phosphate", "#262626", f0=(0.045, 0.045, 0.046), rough_range=(0.55, 0.68),
                 edge__amount=0.55, edge__radius_mm=0.6, grime__amount=0.8, grime__oil=0.6)
    # round 9 (critic r8 m27: "missing the tan accents"): the tan lighter, as the drawn accents read (#9f8060 lit)
    lib_material("FDE", "Paint.FDE.Brushed", "#9a8263", albedo_hex="#9a8263",
                 mottle__hex="#a8916f")
    lib_material("Lens", "Glass.Optic.Coated", "#0e1418")                        # optic and light glass


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


def smooth(ob, angle):
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=math.radians(angle))


def obj(component, geo, mat, *, bevel=None, segs=2, smooth_deg=35.0, real=None, density=None, fill=1.0):
    """`Carbine.<component>` from a Geo (mm), parented to the root, with a material, an optional Bevel
    (width mm) and smoothing by angle. density (g/cm3) and fill (fraction of the closed volume that is
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
    if smooth_deg:
        smooth(ob, smooth_deg)
    if bevel:
        MOD.bevel(ob, bevel, segs, 35.0)
        MOD.weighted_normal(ob, 50, keep_sharp=True)
    if real:
        ob["real_part"] = real
    if density:
        ob["density"] = density
        ob["fill"] = fill
    OBJS[component] = ob
    return ob


def finish(ob, bevel=None, segs=2, smooth_deg=35.0, angle=35.0):
    """After the booleans: smooth by angle, add the Bevel and a Weighted Normal (face area, keep sharp), so
    the large flat n-gons of the boolean results shade flat."""
    smooth(ob, smooth_deg)
    if bevel:
        MOD.bevel(ob, bevel, segs, angle)
    MOD.weighted_normal(ob, 50, keep_sharp=True)
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


def union(ob, *geos):
    for g in geos:
        boolean(ob, g, "UNION")
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


# ============================================================================ the parts
def rail_section(top, bottom, spine_hw=None):
    """MIL-STD-1913 cross-section in (y, z), CCW: 21.2 top with 0.5 chamfers, 45 deg flanks in to the 15.67
    neck, 45 deg out again to the 21.2 base 7.6 below the top; then down to `bottom` (straight at the base
    width, or at spine_hw for a handguard's spine)."""
    rs = [(10.1, top), (10.6, top - 0.5), (7.835, top - 3.265), (7.835, top - 4.4), (10.6, top - 7.165),
          (10.6, top - 7.6)]
    if spine_hw:
        rs += [(spine_hw, top - 7.6), (spine_hw, bottom)]
    else:
        rs += [(10.6, bottom)]
    return rs[::-1] + [(-y, z) for y, z in rs]


def rail_slots(x0R, x1R, top, joint_at_front):
    """Recoil-slot cutters (5.23 wide, 3.0 deep, 10.01 pitch) on one phase for both rails: slot centres at
    R.y = -0.5 + 10.01 k, so the joint between the receiver and handguard rails falls inside one slot
    (take 1 §4.4). Returns (cutter, slot count)."""
    g, n = Geo(), 0
    for k in range(-30, 40):
        c = -0.5 + 10.01 * k
        a, b = c - 2.615, c + 2.615
        if joint_at_front:
            ok = a >= x0R + 3.0 and a < x1R
        else:
            ok = b > x0R and b <= x1R - 3.0
        if ok:
            g.add(box(R(a), R(b), -12.0, 12.0, top - 3.0, top + 2.0))
            n += 1
    return g, n


def build_upper(report):
    hw = UPPER_HW
    deck = 11.3
    sec = [(-hw, -17.0), (hw, -17.0), (hw, 13.0), (13.4, 17.6), (deck, 19.6), (deck, D["rail_base"]),
           (-deck, D["rail_base"]), (-deck, 19.6), (-13.4, 17.6), (-hw, 13.0)]
    up = obj("Upper", prism(sec, D["upper_rear"], D["receiver_face"], "yz"), "Anodised",
             real="BCM M4 forged flat-top upper (mil-spec)", density=2.81, fill=0.75)
    # the integral receiver rail
    rail = prism(rail_section(D["rail_top"], D["rail_base"] - 0.6), R(-196.5), R(-1.5), "yz")
    # forward-assist housing: a teardrop boss that rises out of the right wall behind the port (the front
    # buried in the wall), 13 deg out from the bore in plan; rear end R -141, 15.5 proud of the wall
    A = np.array([R(-99.0), -12.0, 5.5])
    B = np.array([R(-141.0), -21.5, 6.3])
    ax = (B - A) / np.linalg.norm(B - A)
    e1 = np.cross(ax, [0, 0, 1.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(e1, ax)
    rings = []
    for t, r in ((0.0, 2.5), (0.07, 4.8), (0.16, 6.9), (0.28, 8.5), (0.42, 9.4), (0.55, 9.5), (1.0, 9.5)):
        c = A + t * (B - A)
        rings.append([c + r * (math.cos(a) * e1 + math.sin(a) * e2) for a in np.linspace(0, 2 * np.pi, 28,
                                                                                      endpoint=False)])
    fa = loft(rings)
    # brass deflector: a wedge behind the port's top rear corner, its striking face ~40 deg to the bore
    defl = hull([(R(-96.5), -14.6, 9.0), (R(-96.5), -14.6, 20.5), (R(-125.0), -14.6, 7.0), (R(-125.0), -14.6, 22.0),
                 (R(-111.5), -24.5, 11.5), (R(-111.5), -24.5, 17.0), (R(-118.0), -21.0, 20.5)])
    # dust-cover hinge bosses under the port
    bosses = Geo().add(box(R(-18.4), R(-13.0), -18.9, -14.6, -14.6, -9.0)).add(
        box(R(-103.6), R(-98.0), -18.9, -14.6, -14.6, -9.0))
    union(up, rail, fa, defl, bosses)
    slots, n_up = rail_slots(-196.5, -1.5, D["rail_top"], joint_at_front=True)
    cut = Geo()
    cut.add(lathe_x([(D["upper_rear"] - 2.0, 12.8), (R(-14.0), 12.8)], 40))                 # carrier bore
    cut.add(prism(rounded_rect(D["port_front"] - D["port_rear"], 20.3, 3.0, 5,
                               (D["port_front"] + D["port_rear"]) / 2, 1.55), -hw - 12.0, -4.0, "xz"))  # port
    cut.add(corner_cut(D["receiver_face"], -17.0, 7.0, 1, -1, -hw - 1, hw + 1))             # front lower corner
    cut.add(cylinder_between(A + 0.42 * (B - A), B + 0.5 * ax, 7.2, 24))                           # FA plunger bore
    cut.add(cylinder_between((R(-104), -17.2, -11.6), (R(-12), -17.2, -11.6), 1.25, 12))  # hinge-rod hole
    cut.add(slots)
    boolean(up, cut)
    finish(up, 0.6, 2)
    report["rail_slots_receiver"] = n_up

    # forward-assist button (M4 round button with its grooved face), 11 mm behind the housing
    obj("Upper.ForwardAssist", lathe_between(B - 3.0 * ax, B + 11.0 * ax,
                                             [(0, 7.0), (12.0, 7.0), (13.0, 6.7), (13.7, 6.0), (13.7, 4.7),
                                              (13.2, 4.3), (13.7, 3.8), (13.7, 2.3), (13.3, 1.9)]),
        "Steel", smooth_deg=40, real="M4 forward assist, round button", density=7.85, fill=0.8)
    # bolt carrier seen through the port: forward-assist serrations on its right side, bolt head ahead
    bc = obj("BoltCarrier", lathe_x([(R(-120), 12.6), (R(-27), 12.6), (R(-26), 9.0), (R(-12.4), 9.0)], 40), "Steel",
             real="M16-profile bolt carrier (seen through the port)", density=7.85, fill=0.6)
    serr = Geo()
    for k in range(14):
        x = R(-92.0) + 1.6 * k
        serr.add(box(x, x + 0.8, -13.6, -11.9, -3.5, 3.5))
    serr.add(box(R(-60.0), R(-30.0), -13.6, -11.6, -4.5, 4.5))                    # ejection relief cut
    boolean(bc, serr)
    finish(bc, None, smooth_deg=40)
    obj("Upper.HingeRod", cylinder_between((R(-103.5), -17.2, -11.6), (R(-12.5), -17.2, -11.6), 1.2, 12), "Steel",
        smooth_deg=40, density=7.85)
    # dust cover, open: 78.7 x 23.4 x 1.6 sheet hanging from its rod, the inside (latch bump) now outward
    plate = fillet([(D["port_rear"] - 1.3, -35.4), (D["port_front"] + 1.2, -35.4), (D["port_front"] + 1.2, -12.0),
                    (D["port_rear"] - 1.3, -12.0)], [2.0, 2.0, 0, 0], 4)
    cov = obj("Upper.DustCover", prism(plate, -18.0, -16.4, "xz"), "Anodised",
              real="ejection-port cover, open on its hinge rod", density=7.85)
    curl = Geo().add(cylinder_between((R(-97.3), -17.2, -11.6), (R(-62.0), -17.2, -11.6), 1.9, 16))
    curl.add(cylinder_between((R(-52.0), -17.2, -11.6), (R(-19.0), -17.2, -11.6), 1.9, 16))
    union(cov, curl, box(R(-34.0), R(-27.0), -19.4, -17.6, -31.0, -26.5))            # latch bump
    boolean(cov, cylinder_between((R(-104), -17.2, -11.6), (R(-12), -17.2, -11.6), 1.25, 12))
    finish(cov, 0.4, 2)
    # mil-spec charging handle: the T behind the receiver, latch on the LEFT
    t = rect_f(R(-208.0), R(-197.4), -14.5, 14.5, [0, 0, 4.0, 4.0], 5)
    ch = obj("ChargingHandle", prism(t, 13.0, 24.0, "xy"), "Anodised", real="mil-spec charging handle, left latch",
             density=2.81)
    union(ch, prism(rect_f(R(-209.0), R(-198.5), 12.0, 19.5, [1.5, 3.0, 3.0, 0], 4), 15.0, 22.5, "xy"))
    grooves = Geo()
    for k in range(5):
        y = 13.5 + 1.25 * k
        grooves.add(box(R(-210.0), R(-205.0), y, y + 0.6, 21.8, 23.0))
    boolean(ch, grooves)
    finish(ch, 0.5, 2)
    return A, B


def build_lower():
    hw, mw = LOWER_HW, MAGWELL_HW
    body = prism([(R(-86.0), -17.0), (D["lower_rear"], -17.0), (D["lower_rear"], -27.4), (D["grip_front_top"], -54.0),
                  (R(-86.0), -54.0)], -hw, hw, "xz")
    low = obj("Lower", body, "Anodised", real="BCM M4 forged lower (mil-spec)", density=2.81, fill=0.55)
    # receiver-extension boss (the rear tower), flat on top under the charging handle
    boss = lathe_x([(D["upper_rear"] - 0.2, 17.8), (D["lower_rear"], 17.8)], 40)
    # magwell: rounded front corners (r 7), flared lip all round, rounded lip edge
    x0, x1 = D["magwell_rear"], D["magwell_front"]

    def mw_ring(z_of, ex_f, ex_r, ex_s, rf=7.0, rr=3.0):
        pts = rect_f(x0 - ex_r, x1 + ex_f, -mw - ex_s, mw + ex_s, [rf + ex_s, rf + ex_s, rr, rr], 6)
        return [(x, y, z_of(x)) for x, y in pts]
    rings = [mw_ring(lambda x: -17.0, 0, 0, 0),
             mw_ring(lambda x: lip_z(x) + 10.0, 0, 0, 0),
             mw_ring(lambda x: lip_z(x) + 4.0, 1.6, 0.6, 1.1),
             mw_ring(lambda x: lip_z(x) + 1.3, 3.0, 1.0, 2.0),
             mw_ring(lambda x: lip_z(x), 2.4, 0.5, 1.4)]
    magwell = loft(rings)
    pivot = cylinder_between((R(-13.0), -mw, -24.0), (R(-13.0), mw, -24.0), 9.0, 32)
    ears = Geo().add(box(R(-94.5), R(-84.0), -6.2, -3.35, -62.5, -52.0)).add(box(R(-94.5), R(-84.0), 3.35, 6.2,
                                                                                -62.5, -52.0))
    # mag-release fence: a raised arc round the button's rear and lower sides (right side)
    bx, bz = R(-74.0), -38.0
    arc = [(bx + 8.6 * math.cos(a), bz + 8.6 * math.sin(a)) for a in np.radians(np.linspace(160, 340, 13))]
    arc += [(bx + 6.2 * math.cos(a), bz + 6.2 * math.sin(a)) for a in np.radians(np.linspace(340, 160, 13))]
    fence = prism(arc, -mw + 0.8, -mw - 2.2, "xz")
    # left side: bolt-catch boss over the magwell's rear, selector boss
    bcb = prism(rect_f(R(-98.0), R(-77.0), -32.0, -17.5, [3, 0, 0, 3], 4), mw - 0.8, mw + 2.0, "xz")
    selb = cylinder_between((R(-150.0), hw - 0.6, -30.0), (R(-150.0), hw + 1.2, -30.0), 7.5, 32)
    union(low, boss, magwell, pivot, ears, fence, bcb, selb)
    cut = Geo()
    cut.add(box(R(-24.0), R(0.0), -20.0, 20.0, -17.0, 40.0))                         # pivot lobe at the parting line
    cut.add(box(D["lower_rear"] - 2.0, D["upper_rear"] + 0.5, -20.0, 20.0, 11.6, 30.0))   # ... tower top flat
    xm = R(-49.0)

    def op_ring(z_of, ex):
        pts = rect_f(xm - 33.5 - ex, xm + 33.5 + ex, -11.5 - ex, 11.5 + ex, 2.0 + ex, 4)
        return [(x, y, z_of(x)) for x, y in pts]
    cut.add(loft([op_ring(lambda x: -10.0, 0), op_ring(lambda x: lip_z(x) + 4.0, 0),
                  op_ring(lambda x: lip_z(x) - 1.0, 2.2)]))                          # opening and inner flare
    cut.add(lathe_x([(D["upper_rear"] + 1.0, 14.65), (D["lower_rear"] - 1.0, 14.65)], 40))   # extension bore
    cut.add(box(R(-144.0), R(-98.0), -4.25, 4.25, -60.0, -30.0))                    # trigger slot
    boolean(low, cut)
    finish(low, 0.7, 2)

    # small parts
    def pin_head(nm, x, z, r, side, face, proud, dome=True):
        y0 = side * face
        st = [(0, r), (0.5 + proud * 0.5, r), (0.5 + proud, r * 0.72)] if dome else [(0, r), (0.5 + proud, r)]
        obj(nm, lathe_between((x, y0 - side * 0.5, z), (x, y0 + side * proud, z), st, 24),
            "Steel", smooth_deg=40, density=7.85)
    pin_head("Lower.PinPivot", R(-13.0), -24.0, 4.75, -1, mw, 1.5)
    pin_head("Lower.PinTakedown", R(-183.0), -24.0, 4.75, -1, hw, 1.5)
    pin_head("Lower.PinPivot.L", R(-13.0), -24.0, 3.2, 1, mw, 0.3, dome=False)
    pin_head("Lower.PinTakedown.L", R(-183.0), -24.0, 3.2, 1, hw, 0.3, dome=False)
    for nm, x, z in (("Hammer", R(-100.0), -36.0), ("Trigger", R(-121.0), -44.0)):
        obj(f"Lower.Pin{nm}", cylinder_between((x, -hw - 0.3, z), (x, hw + 0.3, z), 1.95, 16), "Steel",
            smooth_deg=40, density=7.85)
    obj("Lower.SelectorEnd", cylinder_between((R(-150.0), -hw + 0.5, -30.0), (R(-150.0), -hw - 0.4, -30.0), 3.6, 24),
        "Steel", smooth_deg=40, density=7.85)
    obj("MagRelease", lathe_between((bx, -mw + 1.0, bz), (bx, -mw - 3.6, bz),
                                    [(0, 4.75), (3.6, 4.75), (4.4, 4.2), (4.6, 2.5)], 24),
        "SteelBright", smooth_deg=40, real="mag-release button in its fence, right side", density=7.85)
    # bolt catch (left): pivot boss at the top, ribbed paddle below
    bc = fillet([(R(-80.0), -18.5), (R(-80.0), -27.0), (R(-86.0), -38.5), (R(-97.0), -38.5), (R(-97.0), -33.0),
                 (R(-88.0), -26.0), (R(-88.0), -18.5)], [3, 2, 2, 2, 1, 2, 3], 4)
    bco = obj("BoltCatch", prism(bc, mw + 1.5, mw + 4.6, "xz"), "Anodised", real="bolt catch, left", density=7.85)
    ribs = Geo()
    for k in range(4):
        x = R(-96.0) + 2.2 * k
        ribs.add(box(x, x + 1.0, mw + 4.0, mw + 5.5, -39.0, -33.0))
    boolean(bco, ribs)
    finish(bco, 0.4, 2)
    # selector lever (left), on SAFE: the lever points forward along the bore
    lev = fillet([(R(-150.0) - 4.0, -26.0), (R(-150.0) + 22.0, -27.6), (R(-150.0) + 24.5, -30.0),
                  (R(-150.0) + 22.0, -32.4), (R(-150.0) - 4.0, -34.0), (R(-150.0) - 6.0, -30.0)],
                 [2, 2, 2, 2, 2, 2], 4)
    sel = obj("Selector", prism(lev, hw + 1.0, hw + 4.4, "xz"), "Anodised", real="safety selector, left", density=7.85)
    union(sel, cylinder_between((R(-150.0), hw + 0.6, -30.0), (R(-150.0), hw + 4.6, -30.0), 4.9, 24))
    finish(sel, 0.5, 2)
    # trigger (mil-spec curved blade) and trigger guard (a 6.5 x 4.5 bar)
    trig = [(-3.0, -50.0), (4.0, -50.0), (3.2, -61.0), (1.6, -70.0), (-2.2, -78.5), (-4.6, -80.0), (-5.4, -78.6),
            (-2.4, -70.0), (-0.8, -61.0)]
    obj("Trigger", prism(trig, -3.2, 3.2, "xz"), "Steel", bevel=0.4, real="mil-spec trigger", density=7.85)
    path = catmull([(R(-89.5), -55.0), (R(-90.5), -68.0), (R(-94.5), -81.0), (R(-102.0), -86.0),
                    (R(-122.0), -86.6), (R(-140.0), -85.4), (R(-148.0), -80.5), (R(-152.5), -71.0),
                    (R(-156.0), -61.0)], 6)
    tang = np.gradient(path, axis=0)
    tang /= np.linalg.norm(tang, axis=1)[:, None]
    nrm = np.c_[-tang[:, 1], tang[:, 0]]
    obj("TriggerGuard", sweep(path, nrm, rounded_rect(5.5, 6.5, 1.8, 3)), "PolymerDark", smooth_deg=50,
        real="mil-spec trigger guard", density=2.7)
    obj("TriggerGuard.Pin", cylinder_between((R(-89.5), -6.6, -57.5), (R(-89.5), 6.6, -57.5), 1.6, 12), "Steel",
        smooth_deg=40, density=7.85)


def grip_frame():
    rake = math.radians(25.0)
    axis_up = np.array([math.sin(rake), math.cos(rake)])           # (x, z), grip axis toward the receiver
    fwd = np.array([math.cos(rake), -math.sin(rake)])              # front strap direction
    front_top = np.array([D["grip_front_top"], -54.0])
    top_c = front_top - 25.0 * fwd + 6.0 * axis_up                 # top section centre, 6 mm into the lower
    return axis_up, fwd, top_c


def build_grip():
    """USGI A2: straight back strap rising into a beavertail under the lower's tang, a finger groove and the
    A2 nub on the front strap, flat checkered sides, round straps, hollow open bottom."""
    axis_up, fwd, top_c = grip_frame()
    # (t down the axis from the top section, front strap u, back strap u, half width)
    st = [(0, 25.0, -27.0, 15.0), (6, 25.0, -34.0, 15.0), (10, 24.8, -30.5, 15.0), (16, 24.3, -27.0, 14.95),
          (24, 23.8, -25.6, 14.9), (32, 24.0, -25.1, 14.8), (39, 25.6, -24.8, 14.7), (45, 26.8, -24.7, 14.6),
          (51, 25.2, -24.8, 14.5), (58, 23.9, -24.9, 14.4), (70, 23.5, -24.7, 14.15), (84, 23.0, -24.1, 13.85),
          (96, 22.2, -23.1, 13.4), (104, 21.4, -22.1, 12.9), (108, 19.9, -20.5, 11.5),
          (108, 17.2, -17.8, 9.4), (86, 17.2, -17.8, 9.4)]
    rings = []
    for t, uf, ub, h in st:
        c = top_c - t * axis_up
        rf = min(h * 0.92, 13.0)
        sec = rect_f(ub, uf, -h, h, [rf, rf, 8.0, 8.0], 7)
        rings.append([(c[0] + u * fwd[0], v, c[1] + u * fwd[1]) for u, v in sec])
    obj("Grip", loft(rings), "PolymerDark", smooth_deg=55, real="USGI A2 pistol grip", density=1.15, fill=0.85)
    return axis_up, fwd, top_c


def build_stock_and_tube(report):
    obj("BufferTube", lathe_x([(D["lower_rear"] + 20, 14.58), (D["tube_rear"] + 1.5, 14.58),
                               (D["tube_rear"], 13.2)], 40), "Hardcoat",
        real="mil-spec carbine receiver extension, OD 1.148 in", density=2.81, fill=0.25)
    obj("BufferTube.Rib", box(R(-222.0), D["tube_rear"] + 2, -3.25, 3.25, -16.9, -12.5), "Hardcoat", bevel=0.4,
        density=2.81, fill=0.5)
    nut = obj("CastleNut", lathe_x([(D["nut_front"], 17.2), (D["nut_front"] - 0.8, 18.0), (D["nut_rear"] + 0.8, 18.0),
                                    (D["nut_rear"], 17.2)], 48), "Hardcoat",
              real="mil-spec castle nut", density=7.85, fill=0.35)
    notches = Geo()
    for a in (90, 210, 330):
        M = np.eye(4)
        t = math.radians(a - 90)
        M[:3, :3] = np.array([[1, 0, 0], [0, math.cos(t), -math.sin(t)], [0, math.sin(t), math.cos(t)]])
        notches.add(box(D["nut_rear"] - 1, D["nut_rear"] + 3.2, -2.4, 2.4, 14.8, 20.0).transformed(M))
    boolean(nut, notches)
    finish(nut, 0.4, 2)
    g = lathe_x([(D["nut_front"], 19.0), (D["endplate_front"], 19.0)], 40)
    g.add(box(D["nut_front"], D["endplate_front"], -6.5, 6.5, -32.0, -12.0))
    g.add(cylinder_between((D["nut_front"] - 1.6, -9.0, -26.0), (D["nut_front"] - 1.6, 9.0, -26.0), 8.0, 24))
    ep = obj("Sling.EndPlate", g, "Steel", real="QD end plate (sling socket each side)", density=7.85, fill=0.8)
    boolean(ep, lathe_x([(D["nut_front"] + 1, 14.65), (D["endplate_front"] - 1, 14.65)], 40)
            .add(cylinder_between((D["nut_front"] - 1.6, -10.0, -26.0), (D["nut_front"] - 1.6, 10.0, -26.0), 4.75, 16)))
    finish(ep, 0.5, 2)

    # MFT BATTLELINK Minimalist, position 3 of 6 (round 4, checked against the real part): 7.08 x 5.22 x 1.75 in
    # (180 x 133 x 44.5 mm), a moulded skeleton of three members: the tube housing on top, the rear post widening to
    # the angled pad, and ONE diagonal strut from the toe forward and up to a junction under the housing's front,
    # which carries the latch and the ambidextrous QD socket ("forward/bottom portion"). Under the housing's front
    # the stock is open: the space behind the A2 grip, where the firing hand's web and wrist go. Round 2's outline
    # had a bottom rail from the toe to a front lug hanging to z -96 only 30-35 mm behind the grip's back strap (a
    # fixed-stock shape, not the Minimalist's), which turned the posed right hand 30 deg on the grip.
    heel = np.array([D["butt_heel"], 18.0])
    toe = np.array([D["pad_toe"], -110.0])
    dvec = (toe - heel) / np.linalg.norm(toe - heel)
    nrm = np.array([-dvec[1], dvec[0]]) if (-dvec[1]) > 0 else np.array([dvec[1], -dvec[0]])   # forward

    def xr(z, inset=8.0):   # x of the line parallel to the pad's front face, `inset` mm forward of the pad face
        t = (z - heel[1]) / dvec[1]
        return heel[0] + t * dvec[0] + inset * nrm[0]

    sx0 = D["stock_front"]
    A = np.array([xr(-110.0) + 30.0, -110.0])        # the strut leaves the toe block here (its lower edge)
    B = np.array([sx0 - 34.0, -44.0])                # and meets the front junction's underside here
    J_BOT = -44.0                                    # the junction's lowest point (z, mm below the bore)
    outline = fillet([(sx0 - 14.0, 6.0), (xr(6.0), 6.0), (xr(-110.0), -110.0), tuple(A), tuple(B),
                      (sx0 - 14.0, J_BOT + 4.0)], [0, 0, 5.0, 9.0, 8.0, 0], 6)
    sd = (B - A) / np.linalg.norm(B - A)
    up_n = np.array([-sd[1], sd[0]]) if sd[0] > 0 else np.array([sd[1], -sd[0]])
    Ap = A + 14.0 * up_n                             # the strut's upper edge (14 mm thick across)
    post_p, post_d = (xr(0.0, 24.0), 0.0), dvec      # the rear post's front edge
    W1 = isect(Ap, sd, (0.0, -24.0), (1.0, 0.0))     # under the housing, at the strut
    W2 = isect(post_p, post_d, (0.0, -24.0), (1.0, 0.0))
    W3 = isect(post_p, post_d, (0.0, -82.0), (1.0, 0.0))   # the toe block below z -82 stays solid
    W4 = isect(Ap, sd, (0.0, -82.0), (1.0, 0.0))
    window = fillet([tuple(W1), tuple(W2), tuple(W3), tuple(W4)], [6.0, 9.0, 8.0, 8.0], 6)
    plate = prism(outline, -8.0, 8.0, "xz", holes=[window])
    hs = rect_f(-17.0, 17.0, -18.5, 18.5, 13.0, 6)          # tube housing section (y, z)
    x_end = xr(-18.5, 10.0)
    housing = loft([[(sx0, 0.9 * y, 0.9 * z) for y, z in hs], [(sx0 - 3.0, y, z) for y, z in hs],
                    [(x_end, y, z) for y, z in hs]])
    rear = [[(xr(-110.0, 8.0), -21.0, -110.0), (xr(-110.0, 8.0), 21.0, -110.0), (xr(16.0, 8.0), 21.0, 16.0),
             (xr(16.0, 8.0), -21.0, 16.0)],
            [(xr(-110.0, 30.0), -8.5, -110.0), (xr(-110.0, 30.0), 8.5, -110.0), (xr(16.0, 30.0), 8.5, 16.0),
             (xr(16.0, 30.0), -8.5, 16.0)]]
    # the front junction under the housing: latch and QD boss, 22 wide, down to J_BOT
    lug = prism(fillet([(sx0 - 40.0, -15.0), (sx0 - 40.0, J_BOT + 2.0), (sx0 - 22.0, J_BOT), (sx0 - 3.0, J_BOT + 7.0),
                        (sx0, -15.0)], [0, 5.0, 6.0, 5.0, 0], 5), -11.0, 11.0, "xz")
    stock = obj("Stock", housing, "Polymer", real="MFT BATTLELINK Minimalist (mil-spec), pos 3 of 6",
                density=1.15, fill=0.9)
    union(stock, plate, loft(rear), lug)
    cut = Geo()
    cut.add(lathe_x([(sx0 + 1.0, 14.9), (x_end - 6.0, 14.9)], 40))                     # tube channel
    cut.add(box(x_end - 6.0, sx0 + 1.0, -3.7, 3.7, -17.6, -10.0))                       # its rib slot
    QD = (sx0 - 20.0, J_BOT + 13.0)                                                       # the QD socket's axis (x, z)
    cut.add(cylinder_between((QD[0], -14.0, QD[1]), (QD[0], 14.0, QD[1]), 4.75, 20))     # through-bore, both sides
    cut.add(prism(rect_f(xr(-100.0, 26.0), xr(-100.0, 26.0) + 24.0, -102.0, -95.0, 3.0, 4), -30.0, 30.0, "xz"))  # sling slot
    boolean(stock, cut)
    finish(stock, 1.4, 2)
    pad = [tuple(heel), tuple(toe), tuple(toe + 8.0 * nrm), tuple(heel + 8.0 * nrm)]
    padg = prism(pad, -22.25, 22.25, "xz")
    po = obj("Stock.ButtPad", padg, "Rubber", real="rubberised butt pad, 12 deg rake", density=1.1)
    grooves = Geo()
    for k in range(6):
        z = -95.0 + 19.0 * k
        p0 = heel + (z - heel[1]) / dvec[1] * dvec
        q = [p0 - 0.75 * dvec - 3.0 * nrm, p0 + 0.75 * dvec - 3.0 * nrm, p0 + 0.75 * dvec + 0.8 * nrm,
             p0 - 0.75 * dvec + 0.8 * nrm]
        grooves.add(prism([tuple(v) for v in q], -30, 30, "xz"))
    boolean(po, grooves)
    finish(po, 2.0, 3, smooth_deg=40)
    for sy in (-1.0, 1.0):
        nm = "Sling.Stock.QD" if sy < 0 else "Sling.Stock.QD.L"
        cup = obj(nm, cylinder_between((QD[0], sy * 10.5, QD[1]), (QD[0], sy * 12.2, QD[1]), 6.5, 24), "Steel",
                  smooth_deg=40, real=f"QD socket cup, stock front junction ({'right' if sy < 0 else 'left'})", density=7.85)
        boolean(cup, cylinder_between((QD[0], sy * 9.0, QD[1]), (QD[0], sy * 14.0, QD[1]), 4.75, 20))
    report["stock_qd_xz_mm"] = [round(QD[0], 1), round(QD[1], 1)]
    report["stock_front_junction_bottom_z_mm"] = J_BOT
    report["stock_rake_deg"] = round(math.degrees(math.atan2(abs(toe[0] - heel[0]), abs(toe[1] - heel[1]))), 1)
    return sx0


def build_barrel():
    st = [(D["bolt_face"], 12.5), (R(14.0), 12.5), (R(14.0), 8.55), (R(60.0), 7.95), (D["barrel_step"], 7.95),
          (D["barrel_journal"], 9.525), (D["thread"], 9.525), (D["thread"], 6.35), (D["crown"], 6.35)]
    obj("Barrel", lathe_x(st, 40), "Barrel", real="16 in government-profile barrel, mid-length gas",
        density=7.85, fill=0.93)
    gb = obj("GasBlock", lathe_x([(D["gas_block"][0], 13.5), (D["gas_block"][1], 13.5)], 40), "Steel",
             real="0.750 in low-profile gas block", density=7.85, fill=0.8)
    union(gb, box(D["gas_block"][0], D["gas_block"][1], -6.0, 6.0, 0.0, 16.0))
    finish(gb, 0.6, 2)
    obj("GasTube", lathe_x([(D["receiver_face"] - 10, 2.29), (D["gas_block"][0] + 10, 2.29)], 12, cz=10.7),
        "Steel", real="mid-length gas tube", density=7.85, fill=0.4)
    a2 = [(D["a2_rear"] - 1.2, 10.4), (D["a2_rear"] - 0.6, 10.9), (D["muzzle"] - 0.6, 10.9), (D["muzzle"], 10.3),
          (D["muzzle"], 7.6), (R(405.0), 7.6), (R(405.0), 3.4), (D["a2_rear"] - 1.2, 6.4)]
    muzzle = obj("Muzzle", lathe_x(a2, 40, loop=True), "Muzzle", real="A2 birdcage flash hider (black phosphate)",
                 density=7.85)
    cuts = Geo()
    for ang in (0, 60, 120, -60, -120):       # five slots with rounded ends, the bottom sector closed
        a = math.radians(ang)
        M = np.eye(4)
        M[:3, :3] = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
        cuts.add(prism(rounded_rect(18.0, 2.6, 1.25, 4, R(412.2), 0.0), 5.0, 14.0, "xy").transformed(M))
    cuts.add(box(D["a2_rear"] - 2, D["a2_rear"] + 14.5, -20, -9.52, -20, 20))           # wrench flats
    cuts.add(box(D["a2_rear"] - 2, D["a2_rear"] + 14.5, 9.52, 20, -20, 20))
    boolean(muzzle, cuts)
    finish(muzzle, 0.3, 2)


def build_handguard(report):
    af, idf = HG_AF, HG_ID
    rows = [(D["hg_rear"], af + 1.6), (D["hg_rear"] + 10.0, af + 1.6), (D["hg_rear"] + 10.6, af),
            (D["hg_front"] - 2.4, af), (D["hg_front"], af - 4.0)]
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
    last = (len(rows) - 1) * 8
    for j in range(8):    # inner wall, rear and front annuli
        j2 = (j + 1) % 8
        F.append((inner0 + 8 + j, inner0 + 8 + j2, inner0 + j2, inner0 + j))
        F.append((inner0 + j, inner0 + j2, j2, j))
        F.append((last + j, last + j2, inner0 + 8 + j2, inner0 + 8 + j))
    hg = obj("Handguard", Geo().add(V, F), "Handguard", real="BCM MCMR-13 M-LOK free-float handguard",
             density=2.7, fill=1.0)
    union(hg, prism(rail_section(D["rail_top"], af / 2 - 0.5, spine_hw=7.835), D["hg_rear"] + 0.0,
                    D["hg_front"] - 0.6, "yz"))
    slots, n_hg = rail_slots(0.5, 340.9, D["rail_top"], joint_at_front=False)
    cuts = Geo().add(slots)
    mlok_r = Geo()
    for k in range(8):                       # M-LOK 32 x 7 at 3, 6 and 9 o'clock, 40 mm pitch
        xc = R(30.0 + 40.0 * k)
        sl = rounded_rect(32.0, 7.0, 2.4, 5, xc, 0.0)
        mlok_r.add(prism(sl, -af / 2 - 3.0, -af / 2 + 3.6, "xz"))
        cuts.add(prism(sl, af / 2 - 3.6, af / 2 + 3.0, "xz"))
        cuts.add(prism(sl, -af / 2 - 3.0, -af / 2 + 3.6, "xy"))
    cuts.add(mlok_r)
    for k in range(7):                       # lightening holes, 10 mm, on the 4:30 and 7:30 bevels
        x = R(105.0 + 26.0 * k)
        for s in (-1, 1):
            n = np.array([0.0, s * 0.7071, -0.7071])
            c = np.array([x, 0.0, 0.0])
            cuts.add(cylinder_between(c + 14.0 * n, c + 23.0 * n, 5.0, 24))
    for s in (-1, 1):                        # clamp-screw counterbores on the rear collar's lower bevels
        n = np.array([0.0, s * 0.7071, -0.7071])
        c = np.array([R(5.5), 0.0, 0.0])
        cuts.add(cylinder_between(c + 18.4 * n, c + 21.5 * n, 3.9, 20))
    boolean(hg, cuts)
    finish(hg, 0.5, 2)
    for s, nm in ((-1, "R"), (1, "L")):
        n = np.array([0.0, s * 0.7071, -0.7071])
        c = np.array([R(5.5), 0.0, 0.0])
        sc = obj(f"Handguard.ClampScrew.{nm}", lathe_between(c + 18.0 * n, c + 20.2 * n,
                                                             [(0, 3.5), (2.2, 3.5)], 20), "Steel",
                 smooth_deg=40, density=7.85)
        boolean(sc, cylinder_between(c + 19.4 * n, c + 21.0 * n, 1.5, 6))           # hex socket
        finish(sc, 0.25, 1, smooth_deg=40)
    obj("Sling.Handguard.QD", lathe_between((R(270), af / 2 - 0.5, 0.0), (R(270), af / 2 + 1.6, 0.0),
                                            [(0, 7.0), (1.6, 7.0), (2.1, 6.4), (2.1, 4.75), (0.5, 4.75)],
                                            24), "Steel", smooth_deg=40, real="M-LOK QD socket, left side",
        density=7.85)
    report["rail_slots_handguard"] = n_hg
    return mlok_r


def build_light():
    ly, lz = -32.0, 16.0
    st = [(R(9.4), 6.4), (R(10.6), 6.6), (R(10.6), 9.6), (R(11.6), 11.4), (R(12.6), 12.0)]
    x = R(13.0)
    while x + 1.6 <= R(29.0):                # Z68 tail cap knurl as grooves
        st += [(x, 12.0), (x + 0.5, 11.5), (x + 1.1, 11.5), (x + 1.6, 12.0)]
        x += 1.6
    st += [(R(30.2), 12.0), (R(30.8), 11.2), (R(76.0), 11.0), (R(77.0), 11.4), (R(89.0), 14.0), (R(90.0), 14.3),
           (R(99.0), 14.3), (R(99.4), 13.9), (R(100.2), 13.9), (R(100.6), 14.3), (R(113.2), 14.3), (R(114.0), 13.5),
           (R(114.0), 12.4), (R(112.6), 12.4)]
    obj("Light", lathe_x(st, 40, cy=ly, cz=lz), "Hardcoat", smooth_deg=40, real="SureFire M300C Mini Scout light",
        density=2.7, fill=0.55)
    obj("Light.Lens", lathe_x([(R(112.4), 12.4), (R(112.9), 12.4)], 40, cy=ly, cz=lz), "Lens", density=2.5)
    obj("Light.Shroud", Geo().add(box(R(8.4), R(12.0), ly - 3.2, ly + 3.2, lz + 7.2, lz + 11.4))
        .add(box(R(8.4), R(12.0), ly - 3.2, ly + 3.2, lz - 11.4, lz - 7.2)), "Hardcoat", bevel=0.6,
        real="Z68 tail-cap shroud", density=2.7)
    af = HG_AF
    mount = fillet([(-af / 2 + 0.5, -9.5), (-af / 2 - 4.5, -9.5), (ly - 2.0, lz - 10.6), (ly + 6.0, lz - 9.4),
                    (-af / 2 + 0.5, 4.5)], [0, 2.0, 2.5, 2.5, 0], 4)
    m = obj("Light.Mount", prism(mount, R(16), R(44), "yz"), "Anodised",
            real="Arisaka Offset Scout Mount, M-LOK, first 3 o'clock slot", density=2.7)
    boolean(m, Geo().add(cylinder_between((R(22.0), -af / 2 - 6, 0.0), (R(22.0), -af / 2 - 3.6, 0.0), 2.4, 12))
            .add(cylinder_between((R(38.0), -af / 2 - 6, 0.0), (R(38.0), -af / 2 - 3.6, 0.0), 2.4, 12)))
    finish(m, 0.7, 2)


def build_optic():
    oz = D["rail_top"] + 39.0
    ox0, ox1 = R(-174), R(-106)
    st = [(ox0 + 1.6, 11.0), (ox0, 12.2), (ox0, 13.4), (ox0 + 1.4, 14.6), (ox0 + 12.0, 14.6), (ox0 + 14.0, 15.3),
          (ox1 - 16.0, 15.3), (ox1 - 14.0, 16.2), (ox1 - 1.2, 16.2), (ox1, 15.4), (ox1, 12.6), (ox1 - 2.6, 11.4)]
    body = obj("Optic", lathe_x(st, 48, cz=oz), "Hardcoat", real="Aimpoint Micro T-2", density=2.7, fill=0.5)
    xm = (ox0 + ox1) / 2 + 3.0
    union(body, prism(rect_f(xm - 10.0, xm + 10.0, -9.0, 9.0, 3.0, 4), oz + 8.0, oz + 15.0, "xy"),   # turret block
          prism(rect_f(xm - 10.0, xm + 10.0, oz - 9.0, oz + 9.0, 3.0, 4), -16.5, -9.0, "xz"),
          prism(rect_f(ox0 + 8.0, ox1 - 14.0, -13.5, 13.5, 2.0, 3), oz - 15.0, oz - 7.0, "xy"))     # base
    finish(body, 0.5, 2)
    turret = [(0, 6.6), (5.8, 6.6), (6.3, 6.0), (8.6, 6.0), (9.0, 5.4)]
    g = lathe_between((xm, 0, oz + 13.0), (xm, 0, oz + 23.0), turret, 32)
    g.add(lathe_between((xm, -13.0, oz), (xm, -23.0, oz), turret, 32))
    obj("Optic.Turrets", g, "Hardcoat", smooth_deg=40, density=2.7)
    for nm, x in (("Optic.Lens.Rear", ox0 + 1.4), ("Optic.Lens.Front", ox1 - 2.4)):
        obj(nm, lathe_x([(x - 0.4, 11.4), (x + 0.4, 11.4)], 40, cz=oz), "Lens", density=2.5)
    # Aimpoint LRP with the 39 mm spacer: rail clamp, riser with a lightening window, throw lever (left)
    mx0, mx1 = R(-160), R(-118)
    rt = D["rail_top"]
    mo = obj("Optic.Mount", prism(rect_f(mx0, mx1, -13.0, 13.0, 2.5, 3), rt - 5.0, rt + 5.0, "xy"), "Anodised",
             real="Aimpoint LRP mount + 39 mm spacer", density=2.7, fill=0.7)
    riser = fillet([(mx0 + 2.0, rt + 4.0), (mx1 - 2.0, rt + 4.0), (mx1 - 6.0, oz - 13.0), (mx0 + 6.0, oz - 13.0)],
                   [0, 0, 3.0, 3.0], 4)
    union(mo, prism(riser, -10.5, 10.5, "xz"),
          cylinder_between(((mx0 + mx1) / 2, 12.0, rt), ((mx0 + mx1) / 2, 15.5, rt), 5.0, 24))
    cut = Geo().add(prism(rect_f(mx0 + 10.0, mx1 - 10.0, rt + 9.0, oz - 19.0, 3.0, 4), -12.0, 12.0, "xz"))
    cut.add(box(mx0 - 1, mx1 + 1, -10.7, 10.7, rt - 6.0, rt - 0.2))                    # rail channel (clears the teeth)
    boolean(mo, cut)
    finish(mo, 0.6, 2)
    lev = fillet([((mx0 + mx1) / 2 - 4.0, rt - 2.5), (mx0 - 6.0, rt - 1.5), (mx0 - 8.0, rt + 2.0),
                  (mx0 - 5.0, rt + 4.0), ((mx0 + mx1) / 2 + 4.0, rt + 3.5)], [2, 2, 2, 2, 2], 4)
    obj("Optic.Lever", prism(lev, 15.0, 18.6, "xz"), "Anodised", bevel=0.5, real="LRP throw lever", density=2.7)


def build_magazine(report):
    """PMAG 30 GEN M3: straight 63 x 21.4 inside the magwell, a stepped body 66 x 22.1 below it on a
    constant R 400 curve, three low ribs a side on the lower body (lofted into the section, tapering out at
    both ends), a flared floorplate with its front lip."""
    mx, mtop, Rc, arc = R(-49.0), -14.5, 400.0, 106.0
    straight_z = [-14.5, -30.0, -50.0, -70.0, -84.0, -87.6, -90.5]
    dims = [(63.0, 21.4)] * 5 + [(65.0, 21.9), (66.0, 22.1)]
    cs, ns, ds = [], [], []
    for z, d in zip(straight_z, dims):
        cs.append((mx, z))
        ns.append((1.0, 0.0))
        ds.append(d)
    th_end = arc / Rc
    narc = 14
    for th in np.linspace(0, th_end, narc + 1)[1:]:
        cs.append((mx + Rc - Rc * math.cos(th), straight_z[-1] - Rc * math.sin(th)))
        ns.append((math.cos(th), math.sin(th)))
        ds.append((66.0, 22.1))
    nr = len(cs)
    w_rib = np.zeros(nr)
    k0 = len(straight_z)
    w_rib[k0 + 1:nr - 1] = 1.0
    w_rib[k0] = 0.35
    w_rib[nr - 2] = 0.5
    rings = []
    for (c, n, (dd, ww), wr) in zip(cs, ns, ds, w_rib):
        sec = resample(rect_f(-dd / 2, dd / 2, -ww / 2, ww / 2, [4.5, 4.5, 2.0, 2.0], 8), 240)
        u, v = sec[:, 0], sec[:, 1]
        side = np.abs(v) > ww / 2 - 0.3
        bump = np.zeros_like(u)
        for uc in (-16.0, 0.0, 16.0):
            bump = np.maximum(bump, np.clip((1.2 + 0.5 - np.abs(u - uc)) / 0.5, 0, 1))
        v = v + np.sign(v) * side * 0.8 * wr * bump
        rings.append([(c[0] + uu * n[0], vv, c[1] + uu * n[1]) for uu, vv in zip(u, v)])
    obj("Magazine", loft(rings), "Magazine", smooth_deg=40, real="Magpul PMAG 30 AR/M4 GEN M3",
        density=1.3, fill=0.2)
    c, n = np.array(cs[-1]), np.array(ns[-1])
    t = np.array([n[1], -n[0]])         # tangent (down along the spine)
    fr = []
    for s, dd, ww, sh in ((-0.4, 66.4, 22.5, 0.6), (1.0, 68.8, 24.8, 1.0), (5.0, 68.8, 24.8, 1.0),
                          (6.0, 67.2, 23.2, 1.0)):
        sec = rect_f(-dd / 2 + sh - 0.6, dd / 2 + sh, -ww / 2, ww / 2, [7.0, 7.0, 3.5, 3.5], 6)
        p = c + s * t
        fr.append([(p[0] + uu * n[0], vv, p[1] + uu * n[1]) for uu, vv in sec])
    obj("Magazine.Floorplate", loft(fr), "MagBase", smooth_deg=40, real="PMAG flared floorplate", density=1.3,
        fill=0.6)
    report["mag_floor_tilt_deg"] = round(math.degrees(th_end), 1)


def build_paint(sx0, mlok_r):
    def patch(nm, x0, x1, z0, z1, y, side=-1, cut=None, holes=()):
        g = prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y, y + side * 0.4, "xz", holes=holes)
        ob = obj(f"Paint.{nm}", g, "FDE", smooth_deg=None, density=1.2)
        if cut is not None:
            boolean(ob, cut)
        return ob
    patch("StockStripe", R(-372), R(-302), -4.0, 3.0, -17.0)
    # the drawn tan frame round the stock's front sling point: on the real stock's front junction (round 4), its hole
    # round the QD cup
    qx, qz = sx0 - 20.0, -31.0
    patch("StockLug", sx0 - 35.0, sx0 - 5.0, -40.0, -19.0, -11.0,
          holes=[[(qx - 7.5, qz - 7.5), (qx + 7.5, qz - 7.5), (qx + 7.5, qz + 7.5), (qx - 7.5, qz + 7.5)]])
    patch("UpperStripe", R(-195), R(-157), 2.0, 12.6, -UPPER_HW)
    patch("LowerMark", R(-56), R(-49), -50.0, -38.0, -MAGWELL_HW)
    patch("MagwellFront", R(-25), R(-19), -52.0, -38.0, -MAGWELL_HW)
    hgf = -HG_AF / 2
    patch("HandguardA", R(56), R(76), -7.5, 7.0, hgf, cut=mlok_r)
    patch("HandguardB", R(80), R(96), -7.5, 6.0, hgf, cut=mlok_r)


def build():
    global ROOT
    ROOT = bpy.data.objects.new(f"{PART}.Root", None)
    ROOT.empty_display_type = "ARROWS"
    ROOT.empty_display_size = 0.1
    collection().objects.link(ROOT)
    report = {}
    build_upper(report)
    build_lower()
    axis_up, fwd, top_c = build_grip()
    sx0 = build_stock_and_tube(report)
    build_barrel()
    mlok_r = build_handguard(report)
    build_light()
    build_optic()
    build_magazine(report)
    build_paint(sx0, mlok_r)

    # hand empties (unchanged from round 1: the surfaces under them did not move)
    # right palm on the A2 grip's right side, 54 mm down the axis from the top section (index on the trigger)
    p = top_c - 54.0 * axis_up - 4.0 * fwd
    empty("Grip.R", (p[0], -15.0, p[1]), X=(axis_up[0], 0, axis_up[1]), Z=(0, 1, 0))
    # left hand overhand on the handguard (reference: back of the hand over the rail, fingers down the right
    # face, tips under the 4:30 bevel): palm centre over the 11 o'clock side, at take 1's station R.y 170
    d11 = np.array([0.0, 0.5, 0.866])
    q = np.array([R(170.0), 0.0, 0.0]) + 20.3 * d11
    empty("Grip.L", tuple(q), X=(-1, 0, 0), Z=tuple(-d11))
    report["grip_empty_gap_mm"] = {"Grip.R": surface_gap("Grip.R", "Grip"),
                                   "Grip.L": surface_gap("Grip.L", "Handguard")}
    return report


def surface_gap(empty_name, target):
    """Distance (mm) from a hand empty to the nearest point of the evaluated target mesh."""
    from mathutils.bvhtree import BVHTree
    bpy.context.view_layer.update()
    ob = OBJS[target]
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(ob, dg)
    p = OBJS[empty_name].matrix_basis.translation
    hit = tree.find_nearest(Vector(p))
    return round((hit[0] - Vector(p)).length / MM, 2) if hit[0] is not None else None


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


def topology(ob):
    """Faces, triangles after evaluation (render mesh), and the non-manifold edge count of the base mesh."""
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    oe.to_mesh_clear()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    return len(ob.data.polygons), tris, nm


def measure(extra):
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    parts = {}
    topo = {}
    for k, ob in OBJS.items():
        if ob.type != "MESH":
            continue
        co = mesh_world_mm(ob)
        lo, hi = np.minimum(lo, co.min(0)), np.maximum(hi, co.max(0))
        parts[k] = (co.min(0), co.max(0))
        topo[k] = topology(ob)
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
        "width_receiver_with_forward_assist_mm": round(parts["Upper"][1][1] - parts["Upper"][0][1], 1),
        "length_of_pull_mm (trigger to pad centre)": round(0.0 - (D["butt_heel"] + D["pad_toe"]) / 2, 1),
        "mass_solid_closed_volumes_g": round(solid),
        "mass_estimate_g (fill factors, empty magazine)": round(est),
        "mass_estimate_loaded_g": round(est + rounds),
        "triangles_rendered_total": int(sum(t[1] for t in topo.values())),
        "non_manifold_edges": {k: t[2] for k, t in topo.items() if t[2]},
        "topology (faces, rendered tris, non-manifold edges)": topo,
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


def studio_lights(target=(120, 0, -30), key_dir=(0.3, -1.0, 0.8), rim_dir=(0.2, 1.0, 0.6)):
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
    area("Carbine.Aux.Fill", (-0.6, -0.8 if key_dir[1] < 0 else 0.8, 0.2), 12.0, 2.0, (0.9, 0.95, 1.0))
    area("Carbine.Aux.Rim", rim_dir, 40.0, 1.0, (0.75, 0.85, 1.0))
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

    # right side (the reference's side), orthographic, bar
    look_at(cam, (cx, -1500, -62), (cx, 0, -62))
    bar = scale_bar((cx - 420, -30, -235), (1, 0, 0), (0, 0, 1))
    render(os.path.join(OUT_DIR, "carbine_right_ortho.png"))
    remove(bar)

    # top, orthographic (muzzle to the right, the gun's left at the top of the frame)
    sc.render.resolution_y = 640
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

    # receiver closeups from both sides: clay (form) and Cycles (finish)
    sc.render.resolution_x, sc.render.resolution_y = 1800, 1200
    cd.lens = 70.0
    for side, pos, key, rim in (("R", (70, -560, 150), (0.3, -1.0, 0.8), (0.2, 1.0, 0.6)),
                                ("L", (-30, 560, 150), (-0.3, 1.0, 0.8), (0.2, -1.0, 0.6))):
        tg = (15, 0, -32)
        look_at(cam, pos, tg)
        workbench(sc, "SINGLE", bg=(0.86, 0.86, 0.84))
        render(os.path.join(OUT_DIR, f"carbine_receiver_{side}_clay.png"))
        cycles(sc, 128)
        world_colour(sc, (0.18, 0.18, 0.19), 0.6)
        lights = studio_lights(tg, key, rim)
        render(os.path.join(OUT_DIR, f"carbine_receiver_{side}_cycles.png"))
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
        if k not in ("mass_by_part (cm3, solid g, estimate g)", "topology (faces, rendered tris, non-manifold edges)"):
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
