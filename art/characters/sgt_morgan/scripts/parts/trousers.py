"""Trousers, round 9: Crye G3 class combat trousers cut as a garment and draped by Blender's cloth solver on the
rest body, with the knee-pad pockets, bellows thigh cargo pockets and calf pockets as sheets on it, a waistband,
and the lower legs bloused onto the boot tops. Notes: scripts/parts/trousers.md (section 8 for this method).

  "$SGT_BLENDER" -b --python scripts/parts/trousers.py [-- --no-render] [--no-sim]
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
    "Knee": {"theta": 0.0, "dz": -8.0, "w": 88.0, "h": 112.0, "depth": 17.0, "edge": 26.0, "mat": "knee"},
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
# The blousing: each leg is cut long, down to cut_z (inside the boot's height, outside its shaft), and in the solve its
# bottom ring is held and pushed up by lift[side] over the first 25 frames to the cuff (L 150, R 160), so the lower
# leg, 75-85 mm longer than its final span, buckles under gravity and self-collision and collapses onto the boot top
# (critics m21, m42); the start carries smooth radial bumps of seed_mm below seed_below, so the two stacks differ.
BLOUSE = {"cut_z": 75.0, "lift": {"L": 75.0, "R": 85.0}, "seed": 9, "seed_mm": 4.0, "seed_below": 360.0}
# The solve (cloth.simulate): NYCO ripstop (cloth.RIPSTOP) on the rest body and the boot proxies. The vertex mass is
# set so the whole shell weighs about what a G3 pair does (0.6-0.7 kg over about 22k vertices); with cloth.RIPSTOP's
# 0.12 the first solve hung 2.6 kg from the waistband, which stretched the seat onto the buttocks and gathered the
# thighs like a skirt. The hips and seat carry a soft goal (seat_goal): the cut there is the shape the hip bones
# and the buttocks' crest hold out; below the crotch the cloth is free.
SIM = {"frames": 60, "seat_goal": 0.3, "cloth": {"mass": 0.03, "tension": 80.0, "compression": 60.0, "shear": 20.0,
                                                 "bending": 4.0}}
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
    "Trousers.Mat.Camo": ("NYCO.Ripstop.Camo", "Camo",
                          {"albedo_hex": "#43403b", "dust__amount": 0.6, "abrade__hex": "#57503f", "abrade__share": 0.32,
                           "rub__hex": "#544c40", "normal__strength": 0.06}),
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
    side = np.where(V[:, 0] > 0, 1.0, 0.8)
    s = lambda a, b: smoothstep(a, b, z)   # noqa: E731
    zones = {"shin": (1.0 - s(380.0, 560.0)) * side, "knee": s(380.0, 480.0) * (1.0 - s(560.0, 660.0)) * side,
             "thigh": s(560.0, 680.0) * (1.0 - s(820.0, 900.0)) * side, "seat": s(820.0, 900.0) * side}
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


def cut_field(bd):
    """The trousers' cut as a signed distance field (mm, negative inside the cloth's outer surface) on a regular
    grid (module doc). Returns field, origin, cell."""
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
                if z < CUT["lower_from"]:
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


def build(body, rig, sim=True):
    """Round 9 (module doc): the cut as a field, meshed, then draped by the cloth solver on the rest body.
    Returns the draped shell (V, F), the cut before the drape, and the body data."""
    bd = C.body_data(body)
    bvh0 = C.skin_bvh(bd)
    field, origin, h = cut_field(bd)
    V, F = K.surface_nets(field, origin, h)
    C.say(TAG, f"cut: {len(V)} verts, {len(F)} quads from the field {field.shape}, cell {h} mm")
    V, F = C.bisect(V, F, WAIST["co"], WAIST["no"], keep="below")
    V, F = C.bisect(V, F, (0.0, 0.0, BLOUSE["cut_z"]), (0.0, 0.0, 1.0), keep="above")
    V, F = largest_piece(V, F)
    E = C.edges_of(F)
    V = C.taubin(V, E, iters=12, lam=0.5, mu=-0.53, pin=C.boundary_verts(F, len(V)))
    V = C.push_out(V, bvh0, 4.0)
    Vcut = V.copy()
    if not sim:
        return V, F, Vcut, bd
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
    return Vs, F, Vcut, bd


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
    V, F, Vcut, bd = build(body, rig, sim="--no-sim" not in args)
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
    for o in [ob] + pk:
        dust_zones(o)
    lib = C.library_pass(coll, "Trousers", MATERIALS, say_tag=TAG)
    rest = C.clearance([ob] + pk, body, "rest")
    meas = measure(ob, bd)
    meas["seat_standoff_mm"] = seat_standoff(ob, bd)
    meas["ease_mm"] = ease_report(ob, bd)
    C.say(TAG, meas)
    used = C.apply_hero_pose(rig)
    posed = C.clearance([ob] + pk, body, "hero pose")
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
