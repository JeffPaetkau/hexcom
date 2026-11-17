"""Trousers, round 9: Crye G3 class combat trousers cut as a garment and draped by Blender's cloth solver on the
rest body, with the knee-pad pockets, bellows thigh cargo pockets and calf pockets as sheets on it, a waistband,
and the lower legs bloused onto the boot tops. Notes: scripts/parts/trousers.md (section 8 for this method).

Round 10 (trousers.md section 10): the hem is no longer bloused. The lower legs fall in a tube round the real boots
(BootHulls, read from cache/parts/boots.blend) and are cut by a forward-tilted plane (HEM). The solve collides with the
boots' sections, with a firm goal on the seat's bridge over the cleft and stiffer bending (SIM10). The hem takes the boot
upper's weights (boot_weights). --blouse rebuilds round 9's bloused cuff.

  "$SGT_BLENDER" -b --python scripts/parts/trousers.py [-- --no-render] [--no-sim] [--blouse]
  -> cache/parts/trousers.blend (Part.Trousers: Trousers.Shell, Trousers.{L,R}.Pocket.*),
     cache/parts/trousers.json (measurements, ease, clearance), renders/trousers/*.png,
     cache/cloth/trousers_<hash>.npz (the solve, reused while its inputs are unchanged)

Method (round 9). (1) The cut, as a signed distance field (cut_field, CUT): per horizontal slice of the rest body,
the convex hull of the skin's section grown by the ease; above the crotch one hull round the whole section (the
seat spans the cleft), below it one per leg, the legs joined by a smooth union whose width is the gusset (the
crotch seam bridges the hollows about 25-40 mm under the perineum, not following it); hull points carried down the
back from the seat's crest and all round from the knee (the cloth falls instead of following the body in); toward
the hem the leg blends into the boot shaft's ellipse. Meshed by surface nets (cloth.surface_nets, 8 mm cells), cut
at the waist plane and well below the cuff, smoothed. (2) The drape (cloth.simulate, SIM): NYCO ripstop at a G3's
weight on the rest body and the boot shafts; the waistband held, the hips and seat on a soft goal, the legs free;
each leg's bottom ring held and pushed up to the cuff (BLOUSE), so the 75-85 mm of surplus length buckles and
collapses onto the boot top, differently on each leg. The solve is on the rest body and the result weight-bound,
not solved in the hero pose and baked: the one mesh then serves the hero pose and the walk alike, and the folds
that gravity and the blousing make in a standing man are the hero pose's too (he stands). (3) Pockets on a smoothed
copy of the drape; everything bound to Morgan.Rig by weight transfer from Body.Mesh, the shell's weights smoothed
round the seat and crotch so the gusset follows both legs' mean motion. Idempotent: it starts from base.blend every
time.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cloth as K  # noqa: E402
import common as C  # noqa: E402

PART, TAG = "Trousers", "trousers"

WAIST = {"co": (0.0, 0.0, 1072.0), "no": (0.0, -0.15, 1.0)}     # top edge: 1052 front, 1087 back
HEM = {"co": (0.0, 0.0, 152.0), "no": (0.0, 0.0, 1.0)}          # hem edge 24 mm below the boot rim (rest)
WAISTBAND_MM, WAISTBAND_PROUD = 45.0, 3.0
CROTCH_Z = 895.0           # the perineum (rest)
# Pockets as sheets lying on the shell (common.surface_patch), in leg coordinates: theta (deg, 0 = front,
# +90 = outside), z centre (mm, rest; "dz" from the knee joint), half arc width and half height (mm), depth
# (mm proud of the shell), edge (mm of rounding: small = boxy bellows). G3 class: knee pocket 175 x 225
# holding an AirFlex-class pad (about 16 thick); bellows thigh cargo 200 x 190 x 25 with a 70 mm flap that
# overhangs it; calf pocket 85 x 145 x 15 with a 45 flap.
POCKETS = {
    # round 10 (m28): the pocket's top stood 28 mm above round 10's smaller knee cap (cap 132 x 176, centre 12 below
    # the joint) as a plain black band; now 6 mm above the cap's top, the bottom where it was (the drawn dark rim
    # under the cap)
    "Knee": {"theta": 0.0, "dz": -19.0, "w": 88.0, "h": 101.0, "depth": 17.0, "edge": 26.0, "mat": "knee"},
    "Cargo": {"theta": 68.0, "z": 792.0, "w": 100.0, "h": 95.0, "depth": 22.0, "edge": 7.0, "tilt": -6.0},
    "CargoFlap": {"theta": 68.0, "z": 866.0, "w": 106.0, "h": 36.0, "depth": 27.0, "edge": 4.0, "tilt": -6.0},
    "Calf": {"theta": 96.0, "z": 335.0, "w": 42.0, "h": 72.0, "depth": 11.0, "edge": 5.0},
    "CalfFlap": {"theta": 96.0, "z": 394.0, "w": 46.0, "h": 23.0, "depth": 14.0, "edge": 3.5},
}
# Round 9: the cut as a signed distance field (cut_field), mm. Per slice the hull of the skin's section grown by the
# ease: above the crotch one hull round the whole section (whole_ease, more behind: seat_back), below it one per
# leg (leg_out outward, front and back; leg_in on the medial side), the two legs joined by a smooth union of width
# gusset_k (the gusset: the crotch seam bridges the hollows about 25-40 mm under the perineum instead of following
# it), blended into the whole section over `blend`. Hull points are carried down the back from the seat's crest
# (slope drape_seat: 0.18 mm in per mm down, from seat_carry_from; 0.3 left the buttocks' lower curve showing) and all round from the knee (drape_knee); below
# lower_from the leg blends into the boot shaft's ellipse + CUFF["over"] (+ flare going up). G3 class targets
# (take 1 spec 09 section 3.3): thigh 600-650 garment girth on a 546 thigh; knee about 500 for the shell; leg
# opening about 460.
CUT = {"cell": 8.0, "z_lo": 40.0, "z_hi": 1112.0,
       "whole_ease": [(1100, 9.0), (1045, 11.0), (990, 16.0), (930, 20.0)],
       "seat_back": 8.0, "seat_carry_from": 1000.0,
       "leg_out": [(940, 22.0), (860, 26.0), (700, 27.0), (560, 24.0), (470, 20.0), (380, 18.0)],
       "leg_in": [(940, 8.0), (880, 9.0), (800, 14.0), (650, 18.0), (540, 18.0), (440, 14.0)],
       "gusset_k": [(930, 60.0), (880, 56.0), (840, 40.0), (790, 0.0)],
       "blend": (CROTCH_Z - 45.0, CROTCH_Z + 35.0),
       "drape_seat": 0.18, "drape_knee": 0.12, "lower_from": 400.0, "lower_to": 240.0}
# The cuff: cut at z (rest; 16 mm under the boot's collar rim, outside the shaft), over the shaft's ellipse by
# `over` mm, the tube flaring by `flare` toward lower_from. Held there in the solve, as a G3's hem is drawn in
# round the boot top. Round 9's first evaluation had the hems 12-14 mm into the boot tongues and uppers in the pose
# (`over` 8 and proxies at the shaft's rim ellipse): now over 13, and the proxies grown by proxy_grow for the tongue
# and collar padding the ellipse leaves out.
CUFF = {"z": 160.0, "over": 13.0, "flare": 22.0, "proxy_grow": 5.0}
# Round 9's blousing (kept for --blouse): each leg cut long, down to cut_z, its bottom ring held and pushed up by
# lift[side] to the cuff, so the surplus buckled onto the boot top. Round 10's critics (m5, m18): it read as a gathered
# elastic cuff over bare boot shafts, the push crinkled the shins into even foil-like lumps, and the Godot export showed
# its spiky crown; the reference's legs fall over the boot tops.
BLOUSE = {"cut_z": 75.0, "lift": {"L": 75.0, "R": 85.0}, "seed": 9, "seed_mm": 4.0, "seed_below": 360.0}
# Round 10: a plain hem that falls over the boot. Below lower_from each leg blends into a tube round the REAL boot (the
# per-slice convex hull of boots.blend's upper, collar, tongue, hooks, laces, strap and buckle at that height and at the
# collar, plus `gap`; flaring by CUFF["flare"] going up), cut by a plane tilted forward: z_back at y +80 rising to
# z_front at y -70 (rest), so the hem covers the collar, its strap and the top hooks and rests on the laces at the front,
# as drawn. In the solve the hem ring carries only a soft goal (ring_goal) pushed up by lift[side]: the surplus folds
# into one or two loose rolls above it instead of a held, gathered cuff. The solve collides with the same boot hulls
# grown by `grow` (round 9 collided with elliptic stand-ins and left the hems 14 mm inside the real tongues and uppers).
# Leg opening: the boot's section at the collar is about 385 round; gap 12 gives the G3's 460. The first solve cut the hem at
# z_back 88, z_front 138: in the hero frame the shaft still showed from the hooks down at the front (rest hem front 141-151);
# now 76 / 118, so the front rests on the laces about 165 above the floor.
HEM = {"gap": 12.0, "z_back": 76.0, "z_front": 118.0, "y_back": 80.0, "y_front": -70.0, "ring_goal": 0.18,
       "lift": {"L": 30.0, "R": 38.0}, "grow": 2.5, "slab": 5.0, "step": 6.0, "z_collar": 168.0,
       "parts": ("Upper", "Collar", "Tongue", "Hooks", "Laces", "Strap", "Buckle", "Keepers", "Tacks", "Stays",
                 "Eyelets")}
# The solve (cloth.simulate): NYCO ripstop (cloth.RIPSTOP) on the rest body and the boot proxies. The vertex mass is
# set so the whole shell weighs about what a G3 pair does (0.6-0.7 kg over about 22k vertices); with cloth.RIPSTOP's
# 0.12 the first solve hung 2.6 kg from the waistband, which stretched the seat onto the buttocks and gathered the
# thighs like a skirt. The hips and seat carry a soft goal (seat_goal): the cut there is the shape the hip bones
# and the buttocks' crest hold out; below the crotch the cloth is free.
SIM = {"frames": 60, "seat_goal": 0.3, "cloth": {"mass": 0.03, "tension": 80.0, "compression": 60.0, "shear": 20.0,
                                                 "bending": 4.0}}
# Round 10 (m5: fine even lumps like wet paper; m19, m32: the seat clings and shows the cleft): NYCO ripstop is crisp,
# so the bending stiffness is tripled (fewer, larger folds); the seat's centre back (|x| < seat_x, from the crotch to
# the waistband) carries a firm goal on the cut, whose per-slice hull bridges the cleft: round 9's soft 0.3 let the
# bridged cloth sag back into it under gravity.
SIM10 = {"frames": 60, "seat_goal": 0.3, "cleft_goal": 0.85, "seat_x": 85.0,
         "cloth": {"mass": 0.03, "tension": 80.0, "compression": 60.0, "shear": 20.0, "bending": 12.0}}
COLOURS = {"camo": "#2a2723", "knee": "#232325"}   # the solid-view colours (round 1); Cycles uses MATERIALS
# Materials round (round 5, 2026-11-15): the library's recipes (scripts/lib/materials.py) per flat material:
# the shell the R002 camouflage print on NYCO ripstop, the knee-pad pockets black 500D Cordura. Dust is held on
# the cloth's sides too (up_low), by height zones (lower legs dusty, the seat least) and the left leg dustier.
MATERIALS = {
    # Round 9 (critics m16, m35, m19; measured on round 8's graded legs_knees crop under the trousers' mask: the
    # render's median luminance 1.25 x the reference's, b/g 0.96 against 0.86, saturation 0.24 against 0.32, and its
    # brightest tenth 1.8 x the reference's, the pale lower legs): darker and warmer charcoal, the dust as brown dirt
    # (thin #6e5f4f to crust #8f7a62) at half the amount instead of the hangar's pale grey film, the abraded edges
    # brownish; the weave photo's normal (Fabric061, its physical 64 mm tile, which lint holds) at a quarter of its
    # strength: it read as coarse burlap in the full view; the 6 mm ripstop grid carries the fine texture.
    # Round 10 (m20, m35, m44; round 9's median 0.45 x the reference with the brightest tenth matching). Measured in the
    # look loop on round 10's assembly (look_stats, graded legs_knees under the trousers' mask, ref / render): round 9's
    # table median 1.85, p90 1.34, p10 3.39, b/g 0.94 against 0.86. A lighter, warm charcoal base, the print's
    # spread at 0.8 of the painter's (was 2.0: the soft high-contrast pale blotches), the dust doubled (1.25) in broad
    # 170 mm drifts of a lighter tan (the reference's diffuse dust and grime, not printed blotches), and the 6 mm ripstop
    # grid at 5 mm and a quarter of its relief (the coarse grid). Variant C of the loop (#56534e, dust 1.8): median 1.09,
    # p90 0.87, chroma matched. On round 10's new cut (evened dust zones, legs falling straight, less self-shadow) the
    # first table (#53514d, dust 1.5) rendered too bright: legs_knees median 0.85, the hems over the boots 0.54; at
    # #4a4845 / 1.25 legs_knees 1.04, p90 1.40, b/g 0.95 against 0.86 (too cool), so the base is warmed to #4c4843.
    "Trousers.Mat.Camo": ("NYCO.Ripstop.Camo", "Camo",
                          {"albedo_hex": "#4c4843", "print__contrast": 0.8, "mottle__amount": 0.10,
                           "dust__amount": 1.25, "dust__noise_mm": 170.0, "dust__thin": "#85725a", "dust__thick": "#a08a6c",
                           "ripstop__grid_mm": 5.0, "ripstop__height_mm": 0.012, "ripstop__rough_add": -0.015,
                           "abrade__hex": "#57503f", "abrade__share": 0.32, "rub__hex": "#544c40",
                           "normal__strength": 0.06}),
    "Trousers.Mat.KneePocket": ("Cordura.500D.Black", "KneePocket",
                                {"wear": "cloth.thigh", "dust__amount": 0.8, "dust__up_low": -0.4,
                                 "dust__up_high": 0.9, "dust__up_power": 1.0}),
}


def dust_zones(ob):
    """The trousers' dust zones (wear preset cloth.thigh) from the rest heights, the left leg (+x) x1.0, the
    right x0.8 (as the left boot is the dustier)."""
    from lib import materials as M
    V = np.array([tuple(v.co) for v in ob.data.vertices]) * 1000.0
    z = V[:, 2]
    # round 10 (m44: the thighs near-black, the shins blotched): the zones evened out, thigh 0.45 -> 0.8, the right
    # leg 0.8 -> 0.9 of the left, so both legs read as one fabric from thigh to shin
    side = np.where(V[:, 0] > 0, 1.0, 0.9)
    s = lambda a, b: smoothstep(a, b, z)   # noqa: E731
    # (the preset's table weights the zones shin 1.0, knee 0.8, thigh 0.45, seat 0.25 and a mask cannot exceed 1, so
    # the evened profile is written as one mask on the shin's full weight)
    prof = np.maximum.reduce([1.0 - s(380.0, 560.0), 0.9 * s(380.0, 480.0) * (1.0 - s(560.0, 660.0)),
                              0.8 * s(560.0, 680.0) * (1.0 - s(820.0, 900.0)), 0.45 * s(820.0, 900.0)])
    zones = {"shin": prof * side}
    return M.wear_zones(ob, "cloth.thigh", zones)


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def interp(table, z):
    zs, vs = zip(*sorted(table))
    return np.interp(z, zs, vs)


def largest_piece(V, F):
    """The largest connected piece of a mesh (mm arrays)."""
    n = len(V)
    parent = np.arange(n)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for f in F:
        r0 = find(f[0])
        for v in f[1:]:
            r = find(v)
            if r != r0:
                parent[r] = r0
    roots = np.array([find(i) for i in range(n)])
    vals, cnt = np.unique(roots, return_counts=True)
    Vn, Fn, _ = C.submesh(V, F, roots == vals[np.argmax(cnt)])
    return Vn, Fn


def skin_edges(bd):
    """The skin's edges (mm endpoints), arms and head left out: plane sections of the body."""
    arm = C.weight_sum(bd, C.is_arm)
    head = C.weight_sum(bd, C.is_head)
    ok = bd["in_body"] & (arm < 0.05) & (head < 0.05)
    E = C.edges_of([f for f in bd["F"] if ok[list(f)].all()])
    V = bd["V"]
    return V[E[:, 0]], V[E[:, 1]]


def section(Ea, Eb, z):
    """Points where the skin's edges cross the plane at height z (x, y in mm)."""
    za, zb = Ea[:, 2] - z, Eb[:, 2] - z
    m = (za * zb) < 0
    t = za[m] / (za[m] - zb[m])
    return Ea[m, :2] + t[:, None] * (Eb[m, :2] - Ea[m, :2])


def axis_xy(side, z):
    hip = C.bone_mm(f"upperleg01.{side}")
    return C.leg_axis_point(side, min(z, hip[2] - 1.0))[0][:2]


def leg_angles(P, a, side):
    """Angle round the leg axis a (deg, 0 = front, +90 = outward, -90 = medial) of 2-D points P."""
    sg = 1.0 if side == "L" else -1.0
    d = P - a
    return np.degrees(np.arctan2(d[:, 0] * sg, -d[:, 1]))


def carry(points, a0, a1, slope, dz):
    """The drape: hull points of the slice above carried down dz mm, moving toward the axis by slope x dz (cloth
    falls from a crest instead of following the body back in)."""
    if not len(points):
        return points
    d = points - a0
    r = np.linalg.norm(d, axis=1)
    rn = r - slope * dz
    keep = rn > 25.0
    return a1 + d[keep] * (rn[keep] / np.maximum(r[keep], 1e-9))[:, None]


class BootHulls:
    """Round 10: the real boots as horizontal sections, read from cache/parts/boots.blend in the rest frame (the boots
    are rigid on the foot bones, saved with their rest transform): per side, the convex hull of the listed objects'
    vertices within HEM["slab"] of each height, every HEM["step"] mm. at(side, z) gives the section at z (the top one
    above the boot); mesh() a closed collision loft of them grown by HEM["grow"]. The loaded data are removed again,
    so nothing of the boots is saved with the trousers."""

    def __init__(self):
        import bpy
        path = os.path.join(C.PARTS_DIR, "boots.blend")
        want = {f"Boot.{s}.{n}" for s in ("L", "R") for n in HEM["parts"]}
        kinds = ("objects", "meshes", "materials", "node_groups", "images", "textures", "curves")
        before = {k: set(getattr(bpy.data, k).keys()) for k in kinds}
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n in want]
        pts = {"L": [], "R": []}
        self.upper = {}            # side -> (rest points mm, {group name: weights}) of the boot's upper (skin-bound)
        for ob in dst.objects:
            if ob is None or ob.type != "MESH" or not len(ob.data.vertices):
                continue
            M = np.array(ob.matrix_basis)
            co = np.empty(len(ob.data.vertices) * 3)
            ob.data.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            W = (co @ M[:3, :3].T + M[:3, 3]) * 1000.0
            pts[ob.name.split(".")[1]].append(W)
            if ob.name.endswith(".Upper"):
                names = {g.index: g.name for g in ob.vertex_groups}
                keep = np.nonzero(W[:, 2] > 60.0)[0][::3]          # the shaft, thinned
                wts = {}
                for j, i in enumerate(keep):
                    for e in ob.data.vertices[int(i)].groups:
                        wts.setdefault(names[e.group], np.zeros(len(keep)))[j] = e.weight
                self.upper[ob.name.split(".")[1]] = (W[keep], wts)
        for k in kinds:                                  # objects first, then the data they used
            coll = getattr(bpy.data, k)
            for name in set(coll.keys()) - before[k]:
                if coll.get(name) is not None:
                    coll.remove(coll[name])
        self.secs = {}
        for s in ("L", "R"):
            P = np.vstack(pts[s])
            zs, hs = [], []
            for z in np.arange(30.0, P[:, 2].max() + 0.1, HEM["step"]):
                m = np.abs(P[:, 2] - z) < HEM["slab"]
                if m.sum() >= 20:
                    zs.append(z)
                    hs.append(C.hull2d(P[m, :2]))
            self.secs[s] = (np.array(zs), hs)
        C.say(TAG, "boot hulls: " + ", ".join(f"{s} {len(self.secs[s][1])} sections z {self.secs[s][0][0]:.0f}-"
                                               f"{self.secs[s][0][-1]:.0f}" for s in ("L", "R")))

    def top(self, side):
        return float(self.secs[side][0][-1])

    def at(self, side, z):
        zs, hs = self.secs[side]
        return hs[int(np.argmin(np.abs(zs - min(z, zs[-1]))))]

    @staticmethod
    def radial(H, c, n=64):
        """The convex polygon H as n points by angle round c (distance from c along each ray)."""
        A, B = H, np.roll(H, -1, 0)
        E = B - A
        out = []
        for t in 2 * np.pi * np.arange(n) / n:
            u = np.array([np.cos(t), np.sin(t)])
            den = u[0] * E[:, 1] - u[1] * E[:, 0]
            W = A - c
            with np.errstate(divide="ignore", invalid="ignore"):
                tt = (W[:, 0] * E[:, 1] - W[:, 1] * E[:, 0]) / den
                ss = (W[:, 0] * u[1] - W[:, 1] * u[0]) / den
            ok = (np.abs(den) > 1e-9) & (tt > 0) & (ss >= -1e-6) & (ss <= 1 + 1e-6)
            out.append(tt[ok].min() if ok.any() else 0.0)
        return np.array(out)

    def mesh(self, z_lo=40.0):
        """Closed collision lofts of both boots (mm), the sections grown by HEM["grow"], capped over the top."""
        V, F = [], []
        n = 64
        th = 2 * np.pi * np.arange(n) / n
        U = np.column_stack([np.cos(th), np.sin(th)])
        for s in ("L", "R"):
            zs, hs = self.secs[s]
            rings = []
            for z, H in zip(zs, hs):
                if z < z_lo:
                    continue
                c = H.mean(0)
                r = self.radial(H, c, n) + HEM["grow"]
                rings.append((z, c, r))
            z, c, r = rings[-1]
            rings += [(z + 4.0, c, r * 0.72), (z + 6.0, c, r * 0.3)]
            ids = []
            for z, c, r in rings:
                ids.append(len(V))
                V.extend([(c[0] + r[i] * U[i, 0], c[1] + r[i] * U[i, 1], z) for i in range(n)])
            for r0, r1 in zip(ids[:-1], ids[1:]):
                for i in range(n):
                    j = (i + 1) % n
                    F.append((r0 + i, r0 + j, r1 + j, r1 + i))      # outward, as round 9's proxies
        return np.array(V), F

    def inside(self, V, margin=0.0):
        """Per vertex (mm): how far inside the grown boot sections it lies (> 0 inside), 0 above the boots."""
        out = np.zeros(len(V))
        for s, sg in (("L", 1.0), ("R", -1.0)):
            zs, hs = self.secs[s]
            m = np.nonzero((np.sign(V[:, 0]) == sg) & (V[:, 2] <= zs[-1]) & (V[:, 2] >= zs[0]))[0]
            for i in m:
                d = K.convex_sd(V[i:i + 1, :2], self.at(s, V[i, 2]))[0]
                out[i] = max(0.0, -(d - HEM["grow"] - margin))
        return out


def boot_weights(ob, boots, above=40.0, below=5.0):
    """Round 10: the hem rides on the boot. The first assembly of the new hem had 51 shell vertices up to 23.8 mm inside
    the left boot's lacing in the hero pose: the boot's shaft takes its weights from the skin under it, the hem (12-20 mm
    outside it) from the nearest skin, which is higher up the shin, so the posed ankle moved the two apart. Below the boot
    top the shell takes the weights of the nearest vertex of the boot's upper, blended back to its own over `below` under
    to `above` mm over the boot top. Returns the number of vertices changed."""
    from mathutils.kdtree import KDTree
    me = ob.data
    n = len(me.vertices)
    R = np.array([tuple(v.co) for v in me.vertices]) * 1000.0
    names = [g.name for g in ob.vertex_groups]
    W = np.zeros((n, len(names)))
    for v in me.vertices:
        for e in v.groups:
            W[v.index, e.group] = e.weight
    changed = 0
    for s, sg in (("L", 1.0), ("R", -1.0)):
        if s not in boots.upper:
            continue
        P, wts = boots.upper[s]
        top = boots.top(s)
        f = smoothstep(top + above, top - below, R[:, 2]) * (np.sign(R[:, 0]) == sg)
        idx = np.nonzero(f > 1e-3)[0]
        if not len(idx):
            continue
        kd = KDTree(len(P))
        for i, p in enumerate(P):
            kd.insert(p, i)
        kd.balance()
        near = np.array([kd.find(R[i])[1] for i in idx])
        for g in wts:
            if g not in names:
                ob.vertex_groups.new(name=g)
                names.append(g)
                W = np.hstack([W, np.zeros((n, 1))])
        Wb = np.zeros((len(idx), len(names)))
        for g, col in wts.items():
            Wb[:, names.index(g)] = col[near]
        sb = Wb.sum(1, keepdims=True)
        Wb = np.where(sb > 1e-6, Wb / np.maximum(sb, 1e-6), W[idx])
        W[idx] = W[idx] * (1 - f[idx])[:, None] + Wb * f[idx][:, None]
        changed += len(idx)
    for j, nm in enumerate(names):
        g = ob.vertex_groups[nm]
        g.remove(list(range(n)))
        nz = np.nonzero(W[:, j] > 1e-4)[0]
        q = np.round(W[nz, j], 3)
        for val in np.unique(q):
            g.add(nz[q == val].tolist(), float(val), "REPLACE")
    return changed


def cut_field(bd, boots=None):
    """The trousers' cut as a signed distance field (mm, negative inside the cloth's outer surface) on a regular
    grid (module doc). Returns field, origin, cell. With boots (a BootHulls, round 10) the lower legs blend into a
    tube round the real boots (HEM) instead of round 9's elliptic shaft."""
    Ea, Eb = skin_edges(bd)
    h = CUT["cell"]
    (xs, ys, zs), origin = K.grid((-330.0, -230.0, CUT["z_lo"]), (330.0, 250.0, CUT["z_hi"]), h)
    GX, GY = np.meshgrid(xs, ys, indexing="ij")
    P2 = np.column_stack([GX.ravel(), GY.ravel()])
    field = np.empty((len(xs), len(ys), len(zs)))
    knee_z = C.bone_mm("lowerleg01.L")[2]
    b_lo, b_hi = CUT["blend"]
    a_y, a_x = C.BOOT["shaft_rim_ab"]
    rim = C.BOOT["rim_z_rest"]
    sec_c = {s: C.leg_section(bd, s, rim - 5.0, half=12.0)["c"] for s in ("L", "R")}
    ax_rim = {s: axis_xy(s, rim - 5.0) for s in ("L", "R")}
    car = {"W": np.zeros((0, 2)), "L": np.zeros((0, 2)), "R": np.zeros((0, 2))}
    prev_a = {"L": axis_xy("L", zs[-1]), "R": axis_xy("R", zs[-1]), "W": np.zeros(2)}
    dW = None
    for k in range(len(zs) - 1, -1, -1):           # top down, so the drape carries
        z = zs[k]
        S = section(Ea, Eb, z)
        a = {"L": axis_xy("L", z), "R": axis_xy("R", z), "W": np.zeros(2)}
        if z >= b_lo:
            car["W"] = carry(car["W"], prev_a["W"], a["W"], CUT["drape_seat"], h)
            Hw = C.hull2d(np.vstack([S, car["W"]]))
            back = smoothstep(-20.0, 60.0, P2[:, 1])
            e = (interp(CUT["whole_ease"], z)
                 + CUT["seat_back"] * back * smoothstep(860.0, 900.0, z) * (1 - smoothstep(1030.0, 1070.0, z)))
            dW = K.convex_sd(P2, Hw) - e
            if z <= CUT["seat_carry_from"]:
                car["W"] = Hw[Hw[:, 1] > 10.0]          # the back half of the seat's hull falls on down
        if z <= b_hi:
            dl = {}
            for s, sg in (("L", 1.0), ("R", -1.0)):
                mine = S[(S[:, 0] * sg) > 0]
                cw = car["W"][(car["W"][:, 0] * sg) > -8.0] if z >= b_lo - 3 * h else np.zeros((0, 2))
                slope = CUT["drape_seat"] if z > knee_z + 60.0 else CUT["drape_knee"]
                car[s] = carry(car[s], prev_a[s], a[s], slope, h)
                pts = np.vstack([mine, car[s], cw])
                if len(pts) < 3:
                    dl[s] = np.full(len(P2), 1e3)
                    continue
                H = C.hull2d(pts)
                th = leg_angles(P2, a[s], s)
                med = np.abs(((th + 90.0 + 180.0) % 360.0) - 180.0)       # degrees from medial
                w_in = smoothstep(70.0, 20.0, med)
                e = interp(CUT["leg_out"], z) * (1 - w_in) + interp(CUT["leg_in"], z) * w_in
                d = K.convex_sd(P2, H) - e
                if z < CUT["lower_from"] and boots is not None:
                    # round 10: the tube round the real boot at this height and at the collar, plus the gap, flaring
                    # going up; below the collar it takes in the laces' slope too (the hem plane cuts it there)
                    zc = min(HEM["z_collar"], boots.top(s))
                    Hb = boots.at(s, zc) if z >= zc else C.hull2d(np.vstack([boots.at(s, zc), boots.at(s, z)]))
                    de = K.convex_sd(P2, Hb) - (HEM["gap"] + CUFF["flare"] * smoothstep(zc, CUT["lower_from"], z))
                    w = smoothstep(CUT["lower_from"], CUT["lower_to"], z)
                    d = d * (1 - w) + de * w
                elif z < CUT["lower_from"]:
                    c = sec_c[s] + (a[s] - ax_rim[s])
                    q = P2 - c
                    r = np.linalg.norm(q, axis=1)
                    u = q / np.maximum(r, 1e-9)[:, None]
                    re = 1.0 / np.sqrt((u[:, 0] / a_x) ** 2 + (u[:, 1] / a_y) ** 2)
                    de = r - (re + CUFF["over"] + CUFF["flare"] * smoothstep(CUFF["z"], CUT["lower_from"], z))
                    w = smoothstep(CUT["lower_from"], CUT["lower_to"], z)
                    d = d * (1 - w) + de * w
                dl[s] = d
                thH = leg_angles(H, a[s], s)
                if z > knee_z + 60.0:
                    car[s] = H[np.abs(thH) > 100.0]       # behind the thigh, from the seat down
                elif z < knee_z + 40.0:
                    car[s] = H                            # all round, from the knee down
            fl = K.smin(dl["L"], dl["R"], interp(CUT["gusset_k"], z))
            t = smoothstep(b_lo, b_hi, z)
            f = fl if z < b_lo else (fl * (1 - t) + dW * t)
        else:
            f = dW
        field[:, :, k] = f.reshape(len(xs), len(ys))
        prev_a = a
    return field, origin, h


def boot_proxy(bd):
    """Collision proxies of the boots in the rest frame: the shaft as an elliptic tube (common.BOOT, centred on the
    leg's section at the rim) from the ankle to the collar, closed over the top by an inward ring."""
    a_y, a_x = C.BOOT["shaft_rim_ab"]
    rim = C.BOOT["rim_z_rest"]
    V, F = [], []
    n = 48
    for s in ("L", "R"):
        c0 = C.leg_section(bd, s, rim - 5.0, half=12.0)["c"]
        a_r = axis_xy(s, rim - 5.0)
        rings = []
        for z, sc in [(z, 1.0) for z in np.arange(40.0, rim + 0.1, 12.0)] + [(rim + 4.0, 0.72)]:
            c = c0 + (axis_xy(s, z) - a_r)
            base = len(V)
            for i in range(n):
                t = 2 * np.pi * i / n
                g_ = CUFF["proxy_grow"] if sc == 1.0 else 0.0
                V.append((c[0] + (a_x + g_) * sc * np.sin(t), c[1] - (a_y + g_) * sc * np.cos(t), z))
            rings.append(base)
        for r0, r1 in zip(rings[:-1], rings[1:]):
            for i in range(n):
                j = (i + 1) % n
                F.append((r0 + i, r0 + j, r1 + j, r1 + i))
    return np.array(V), F


def hem_plane():
    """Round 10: the hem's cut plane (rest mm), tilted forward: z_back at y_back rising to z_front at y_front."""
    dy, dz = HEM["y_front"] - HEM["y_back"], HEM["z_front"] - HEM["z_back"]
    no = np.array([0.0, -dz, dy]) * (-1.0 if dy < 0 else 1.0)
    no /= np.linalg.norm(no)
    return (0.0, HEM["y_back"], HEM["z_back"]), tuple(no)


def build(body, rig, sim=True, blouse=False):
    """Round 10 (module doc, HEM): the cut as a field with the lower legs round the real boots, meshed, cut at the
    waist and the tilted hem plane, then draped by the cloth solver on the rest body and the boots (round 9's
    blousing with blouse=True). Returns the draped shell (V, F), the cut before the drape, the body data and the
    boot hulls."""
    bd = C.body_data(body)
    bvh0 = C.skin_bvh(bd)
    boots = None if blouse else BootHulls()
    field, origin, h = cut_field(bd, boots)
    V, F = K.surface_nets(field, origin, h)
    C.say(TAG, f"cut: {len(V)} verts, {len(F)} quads from the field {field.shape}, cell {h} mm")
    V, F = C.bisect(V, F, WAIST["co"], WAIST["no"], keep="below")
    if blouse:
        V, F = C.bisect(V, F, (0.0, 0.0, BLOUSE["cut_z"]), (0.0, 0.0, 1.0), keep="above")
    else:
        co, no = hem_plane()
        V, F = C.bisect(V, F, co, no, keep="above")
    V, F = largest_piece(V, F)
    E = C.edges_of(F)
    V = C.taubin(V, E, iters=12, lam=0.5, mu=-0.53, pin=C.boundary_verts(F, len(V)))
    V = C.push_out(V, bvh0, 4.0)
    Vcut = V.copy()
    if not sim:
        return V, F, Vcut, bd, boots
    if not blouse:
        return drape10(V, F, E, bd, bvh0, boots) + (Vcut, bd, boots)
    # the solve: the waistband held, the hips and seat on a soft goal, the bottom ring held and pushed up to the cuff
    # (BLOUSE), from an uneven start per leg
    wn = np.array(WAIST["no"]) / np.linalg.norm(WAIST["no"])
    below_top = -((V - np.array(WAIST["co"])) @ wn)
    ring = V[:, 2] < BLOUSE["cut_z"] + 6.0
    pin = np.maximum(1.0 - smoothstep(22.0, 40.0, below_top), ring.astype(float))
    pin = np.maximum(pin, SIM["seat_goal"] * smoothstep(CROTCH_Z - 20.0, CROTCH_Z + 40.0, V[:, 2]))
    move = np.zeros_like(V)
    rng = np.random.default_rng(BLOUSE["seed"])
    noise = C.smooth_field(rng.normal(0.0, 1.0, len(V)), E, iters=5, lam=0.5)
    noise /= max(np.abs(noise).max(), 1e-9)
    for s, sg in (("L", 1.0), ("R", -1.0)):
        side = np.sign(V[:, 0]) == sg
        move[ring & side, 2] = BLOUSE["lift"][s]
        for i in np.nonzero(side & ~ring & (V[:, 2] < BLOUSE["seed_below"]))[0]:
            a = axis_xy(s, V[i, 2])
            d = V[i, :2] - a
            V[i, :2] += d / max(np.linalg.norm(d), 1e-9) * noise[i] * BLOUSE["seed_mm"]
    Vb, Fb = boot_proxy(bd)
    skinF = [f for f in bd["F"] if bd["in_body"][list(f)].all()]
    Vs = K.simulate("trousers", V, F, colliders=[(bd["V"], skinF), (Vb, Fb)], pin=pin, move=move,
                    frames=SIM["frames"], cloth=SIM["cloth"], self_group=(V[:, 2] < 560.0).astype(float))
    behind = smoothstep(20.0, 80.0, Vs[:, 1])
    clear = 3.0 + 1.0 * (Vs[:, 2] > 940.0) + 4.0 * behind * smoothstep(930.0, 960.0, Vs[:, 2])   # the shirt tail
    Vs = C.push_out(Vs, bvh0, clear)
    return Vs, F, Vcut, bd, None


def drape10(V, F, E, bd, bvh0, boots):
    """Round 10's solve (SIM10, HEM): the waistband held, the hips and seat on a soft goal, the seat's centre back on
    a firm one (the cut's bridge over the cleft), the hem ring on a weak goal pushed up by lift[side] (one or two loose
    rolls, the legs differing), the legs otherwise free; colliders the rest skin and the real boots' lofts. Returns
    (V, F) after clearing the skin and the boots."""
    wn = np.array(WAIST["no"]) / np.linalg.norm(WAIST["no"])
    below_top = -((V - np.array(WAIST["co"])) @ wn)
    pin = 1.0 - smoothstep(22.0, 40.0, below_top)
    pin = np.maximum(pin, SIM10["seat_goal"] * smoothstep(CROTCH_Z - 20.0, CROTCH_Z + 40.0, V[:, 2]))
    cleft = (SIM10["cleft_goal"] * smoothstep(20.0, 70.0, V[:, 1])
             * (1.0 - smoothstep(SIM10["seat_x"] - 25.0, SIM10["seat_x"], np.abs(V[:, 0])))
             * smoothstep(CROTCH_Z - 30.0, CROTCH_Z + 10.0, V[:, 2]))
    pin = np.maximum(pin, cleft)
    co, no = hem_plane()
    above_hem = (V - np.array(co)) @ np.array(no)
    ring = (above_hem < 6.0) & (V[:, 2] < 300.0)
    move = np.zeros_like(V)
    for s, sg in (("L", 1.0), ("R", -1.0)):
        move[ring & (np.sign(V[:, 0]) == sg), 2] = HEM["lift"][s]
    pin[ring] = np.maximum(pin[ring], HEM["ring_goal"])
    Vb, Fb = boots.mesh()
    skinF = [f for f in bd["F"] if bd["in_body"][list(f)].all()]
    C.say(TAG, f"solve: {int(ring.sum())} hem-ring vertices, {int((cleft > 0.5).sum())} on the seat's firm goal")
    Vs = K.simulate("trousers", V, F, colliders=[(bd["V"], skinF), (Vb, Fb)], pin=pin, move=move,
                    frames=SIM10["frames"], cloth=SIM10["cloth"], self_group=(V[:, 2] < 560.0).astype(float))
    behind = smoothstep(20.0, 80.0, Vs[:, 1])
    clear = 3.0 + 1.0 * (Vs[:, 2] > 940.0) + 4.0 * behind * smoothstep(930.0, 960.0, Vs[:, 2])   # the shirt tail
    # the boots first, the skin last: at the heel the body pokes through the boot's counter (the boots' own body-boots
    # clash), and pushing out of the boot after the skin left two hem vertices 28 mm inside the right heel
    Vs = C.push_out(Vs, C.bvh_from(Vb, Fb), 1.5)
    Vs = C.push_out(Vs, bvh0, clear)
    return Vs, F


def seat_concavity(V, z_list=(1040.0, 1000.0, 960.0, 920.0, 890.0)):
    """Round 10 (m19, m32): how deep the cloth dips into the cleft from behind, per height (mm). For the shell's
    vertices in a 10 mm slab, in the slab's own frame (the principal axis of the section, so the posed pelvis's yaw
    does not matter), the back profile (the furthest back point per 12 mm across, within 110 mm of the middle) is
    compared with its upper convex hull; the largest gap within 60 mm of the middle is the dip. 0 = bridged.
    (Per 12 mm across, from the back half of the slab.)"""
    out = {}
    for z in z_list:
        P = V[np.abs(V[:, 2] - z) < 5.0][:, :2]
        if len(P) < 30:
            continue
        c = P.mean(0)
        Q = P - c
        w, U = np.linalg.eigh(Q.T @ Q)
        ax = U[:, 1]                       # across the hips
        bk = np.array([-ax[1], ax[0]])
        if bk[1] < 0:
            bk = -bk                       # toward +y, behind
        u, b = Q @ ax, Q @ bk
        u, b = u[b > 0], b[b > 0]          # the back half only (an 8 mm mesh leaves some narrow bins without a back point)
        bins = np.arange(-108.0, 108.1, 12.0)
        xs, ys = [], []
        for lo, hi in zip(bins[:-1], bins[1:]):
            m = (u >= lo) & (u < hi)
            if m.any():
                xs.append((lo + hi) / 2)
                ys.append(b[m].max())
        xs, ys = np.array(xs), np.array(ys)
        if len(xs) < 8:
            continue
        H = C.hull2d(np.column_stack([xs, ys]))
        top = []
        for x in xs:                       # the upper hull's height at x
            best = -1e9
            for a_, b_ in zip(H, np.roll(H, -1, 0)):
                if min(a_[0], b_[0]) - 1e-6 <= x <= max(a_[0], b_[0]) + 1e-6 and abs(b_[0] - a_[0]) > 1e-9:
                    best = max(best, a_[1] + (b_[1] - a_[1]) * (x - a_[0]) / (b_[0] - a_[0]))
            top.append(best)
        gap = np.array(top) - ys
        mid = np.abs(xs) < 60.0
        out[f"z{int(z)}"] = round(float(gap[mid].max()), 1)
    return out


def smooth_weights(ob, select, iters=12, lam=0.5):
    """Laplacian smoothing of an object's vertex-group weights over its edges, on the selected vertices
    (a mask by rest position), renormalised: an outer layer then follows the body's mean motion instead of
    pinching into every crease the skin's own weights make."""
    me = ob.data
    n = len(me.vertices)
    names = [g.name for g in ob.vertex_groups]
    W = np.zeros((n, len(names)), np.float32)
    for v in me.vertices:
        for e in v.groups:
            W[v.index, e.group] = e.weight
    E = np.array([tuple(e.vertices) for e in me.edges], int)
    sel = np.asarray(select, bool)
    W = C.smooth_field(W, E, iters=iters, lam=lam, pin=~sel)
    s = W.sum(1, keepdims=True)
    W = np.where(s > 1e-6, W / np.maximum(s, 1e-6), W)
    for j, nm in enumerate(names):
        g = ob.vertex_groups[nm]
        g.remove(list(range(n)))
        col = W[:, j]
        nz = np.nonzero(col > 1e-4)[0]
        if not len(nz):
            continue
        q = np.round(col[nz], 3)
        for val in np.unique(q):
            g.add(nz[q == val].tolist(), float(val), "REPLACE")


def measure(ob, bd):
    """Garment girths at a few heights (rest), the outseam and the stack."""
    V, F = C.evaluated_world_mm(ob)
    out = {}
    for s, sg in (("L", 1.0), ("R", -1.0)):
        for label, z in (("thigh", 820.0), ("knee", C.bone_mm(f"lowerleg01.{s}")[2] - 8), ("calf", 420.0),
                         ("hem_stack", 218.0)):
            sel = (np.abs(V[:, 2] - z) < 4.0) & (np.sign(V[:, 0]) == sg)
            P = V[sel][:, :2]
            if len(P) < 8:
                continue
            c = P.mean(0)
            ang = np.arctan2(P[:, 1] - c[1], P[:, 0] - c[0])
            o = np.argsort(ang)
            Q = P[o]
            per = float(np.linalg.norm(np.diff(np.vstack([Q, Q[:1]]), axis=0), axis=1).sum())
            out[f"{label}_{s}_girth_mm"] = round(per, 1)
            H = C.hull2d(P)      # round 9: the tape-measure girth (the folds' perimeter is in the line above)
            out[f"{label}_{s}_girth_hull_mm"] = round(float(np.linalg.norm(np.diff(np.vstack([H, H[:1]]), axis=0),
                                                                           axis=1).sum()), 1)
            out[f"{label}_{s}_width_x_mm"] = round(float(np.ptp(P[:, 0])), 1)
            out[f"{label}_{s}_depth_y_mm"] = round(float(np.ptp(P[:, 1])), 1)
    out["waist_top_z_mm"] = [round(float(V[:, 2].max()), 1)]
    out["hem_z_min_mm"] = round(float(V[:, 2].min()), 1)
    out["outseam_rest_mm"] = round(float(V[:, 2].max() - V[:, 2].min()), 1)
    return out


def ease_report(ob, bd):
    """Ease made visible (rest): the shell's distance from the skin (mm), median and 10th-90th percentiles, by
    band (seat and hips, thigh, knee, calf, the blousing above the cuff), front and back halves of the leg."""
    V, F = C.evaluated_world_mm(ob)
    d, _n = C.signed_dist(V, C.skin_bvh(bd))
    out = {}
    knee = C.bone_mm("lowerleg01.L")[2]
    for label, lo, hi in (("hips", 930, 1040), ("seat_crotch", 860, 930), ("thigh", 640, 820),
                          ("knee", knee - 60, knee + 60), ("calf", 300, 440), ("blouse", 165, 300)):
        for half, m in (("front", V[:, 1] < 0), ("back", V[:, 1] >= 0)):
            sel = (V[:, 2] >= lo) & (V[:, 2] < hi) & m & (d < 200)
            if sel.sum() > 10:
                q = np.percentile(d[sel], [10, 50, 90])
                out[f"{label}_{half}"] = [round(float(x), 1) for x in q]
    return out


def seat_standoff(ob, bd):
    """Distance from the skin to the trousers straight behind, over the seat (rest): ease made visible."""
    from mathutils import Vector
    V, F = C.evaluated_world_mm(ob)
    bvh = C.bvh_from(V, F)
    skin = bd["V"][bd["in_body"]]
    out = {}
    for z in (980.0, 930.0, 880.0, 840.0, 800.0, 760.0):
        for side, x in (("L", 70.0), ("R", -70.0)):
            m = (np.abs(skin[:, 2] - z) < 6) & (np.abs(skin[:, 0] - x) < 15)
            if not m.any():
                continue
            p = skin[m][np.argmax(skin[m][:, 1])]
            hit = bvh.ray_cast(Vector(p), Vector((0.0, 1.0, 0.0)), 200.0)
            if hit[0] is not None:
                out[f"{side}_z{int(z)}"] = round(hit[3], 1)
    return out


def pockets(shell_V, shell_F, coll, mats):
    """The knee, cargo and calf pockets of both legs as sheets on the rest shell."""
    bvh = C.bvh_from(shell_V, shell_F)
    knee_z = C.bone_mm("lowerleg01.L")[2]
    obs = []
    for side in ("L", "R"):
        for name, p in POCKETS.items():
            zc = knee_z + p["dz"] if "dz" in p else p["z"]
            V, F = C.surface_patch(bvh, lambda z, s=side: C.leg_frame(s, z), p["theta"], zc, p["w"], p["h"],
                                   p["depth"], edge=p["edge"], tilt=p.get("tilt", 0.0), nu=28, nv=28)
            mat = mats[p.get("mat", "camo")]
            ob = C.mesh_object(f"Trousers.{side}.Pocket.{name}", V, F, coll, mat=mat)
            ob["sgt_clay"] = (0.42, 0.40, 0.37) if p.get("mat") == "knee" else (0.50, 0.46, 0.40)
            obs.append(ob)
    return obs


def main():
    import bpy
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    body, rig = C.open_base()
    coll = C.part_collection(PART)
    V, F, Vcut, bd, boots = build(body, rig, sim="--no-sim" not in args, blouse="--blouse" in args)
    mats = {"camo": C.flat_material("Trousers.Mat.Camo", COLOURS["camo"], 0.85),
            "knee": C.flat_material("Trousers.Mat.KneePocket", COLOURS["knee"], 0.6)}
    ob = C.mesh_object("Trousers.Shell", V, F, coll, mat=mats["camo"])
    ob["sgt_clay"] = (0.52, 0.48, 0.42)
    # round 9: the pockets lie on a smoothed copy of the draped shell (a bellows pocket is a stiff panel; laid on the
    # folds it crumpled with them)
    Vsm = C.taubin(V, C.edges_of(F), iters=40, lam=0.5, mu=-0.53, pin=C.boundary_verts(F, len(V)))
    pk = pockets(Vsm, F, coll, mats)
    for o in [ob] + pk:
        C.bind(o, body, rig)
        C.solidify(o, 1.5 if o is ob else 1.2, inward=True)
        C.subsurf(o, 1)
    Vr = np.array([tuple(v.co) for v in ob.data.vertices]) * 1000.0
    # the seat, and (round 9) the gusset between the legs, which takes both thighs' mean motion
    smooth_weights(ob, (Vr[:, 2] > 860.0) | ((Vr[:, 2] > 740.0) & (np.abs(Vr[:, 0]) < 70.0)), iters=14)
    # round 10 (m19, m32): 26 more passes over the seat behind only, so its cloth takes the pelvis's and both thighs' mean
    # motion over a wider band and the posed hips do not fold it into the cleft (all 40 passes over the whole hips also
    # moved the front waistband's weights, which the carrier's front flap and bag copy, and put the bag into the shirt)
    smooth_weights(ob, (Vr[:, 2] > 860.0) & (Vr[:, 2] < 1070.0) & (Vr[:, 1] > 20.0), iters=26)
    if boots is not None:
        C.say(TAG, f"hem weights from the boots' uppers: {boot_weights(ob, boots)} vertices")
    for o in [ob] + pk:
        dust_zones(o)
    lib = C.library_pass(coll, "Trousers", MATERIALS, say_tag=TAG)
    rest = C.clearance([ob] + pk, body, "rest")
    meas = measure(ob, bd)
    meas["seat_standoff_mm"] = seat_standoff(ob, bd)
    meas["ease_mm"] = ease_report(ob, bd)
    Vrest, Frest = C.evaluated_world_mm(ob)
    meas["seat_concavity_mm"] = seat_concavity(Vrest)
    if boots is not None:
        # round 10: the hem against the real boots (rest): how far the shell lies inside their sections, and where the
        # hem edge ends up at the front and back of each leg
        dep = boots.inside(Vrest)
        bnd = C.boundary_verts(Frest, len(Vrest))
        hem = bnd & (Vrest[:, 2] < 400.0)
        meas["hem_in_boots_mm"] = {"inside": int((dep > 0.5).sum()), "max": round(float(dep.max()), 1)}
        for s, sg in (("L", 1.0), ("R", -1.0)):
            m = hem & (np.sign(Vrest[:, 0]) == sg)
            if m.any():
                P = Vrest[m]
                meas[f"hem_{s}_z_front_back_mm"] = [round(float(P[np.argmin(P[:, 1]), 2]), 1),
                                                    round(float(P[np.argmax(P[:, 1]), 2]), 1)]
                meas[f"hem_{s}_girth_mm"] = round(float(np.linalg.norm(np.diff(
                    np.vstack([C.hull2d(P[:, :2]), C.hull2d(P[:, :2])[:1]]), axis=0), axis=1).sum()), 1)
    C.say(TAG, meas)
    used = C.apply_hero_pose(rig)
    posed = C.clearance([ob] + pk, body, "hero pose")
    Vpose, _ = C.evaluated_world_mm(ob)
    meas["seat_concavity_posed_mm"] = seat_concavity(Vpose)
    C.say(TAG, {"seat_concavity_mm": meas["seat_concavity_mm"], "posed": meas["seat_concavity_posed_mm"]})
    C.rest_pose(rig)
    C.save_part(TAG, coll, {"measure_rest_mm": meas, "clearance_rest": rest, "clearance_posed": posed,
                            "pose": used, "verts": len(V), "materials": lib})
    if "--no-render" not in args:
        C.render_part(TAG, coll, (0, 0, 600), 1250, crops=("ref.legs_knees", "ref.soldier_full"))
        C.rest_pose(bpy.data.objects[C.RIG])
        C.render_view(TAG, [coll], "rest_back", (0, 4000, 600), (0, 0, 600), 1250)
        C.render_view(TAG, [coll], "rest_hem_side", (-4000, 0, 250), (-200, 0, 250), 380)


if __name__ == "__main__":
    main()
