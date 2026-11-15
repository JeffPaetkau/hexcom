"""Trousers, round 2: Crye G3 class combat trousers as one offset shell from the rest body that hangs like
cloth (seat room, thigh and knee ease, the articulated knee's back folds and seam band), with the knee-pad
pockets, bellows thigh cargo pockets and calf pockets as sheets on it, a waistband, and the hems stacked
in soft irregular rolls over the boot collars. Notes: scripts/parts/trousers.md.

  "$SGT_BLENDER" -b --python scripts/parts/trousers.py [-- --no-render]
  -> cache/parts/trousers.blend (Part.Trousers: Trousers.Shell, Trousers.{L,R}.Pocket.*),
     cache/parts/trousers.json (measurements, clearance), renders/trousers/*.png

Method: the body's skin from just above the ankles to above the hips (arms and head excluded by bone
weight) is copied, each vertex pushed out along its normal by an ease field (mm, by height, more over the
seat), the push capped where the skin faces itself (the crotch). Then the cloth's hang, in three steps:
(1) above the crotch the whole section moves toward its convex hull (the seat spans the gluteal cleft);
(2) below it each leg's sections move toward their convex hulls (the cloth spans the hollows between the
muscles); (3) a drape envelope per leg: in cylindrical coordinates round the leg's bone chain, at every
angle except the inner thigh, the radius may fall going down the leg by no more than a cloth's slope (0.24
from the seat to the knee, 0.08 below it), so the cloth falls from the buttock's crest past the gluteal
fold and from the knee past the calf instead of following them. The knee gets the G3's back-of-knee folds
and the seam band above the knee panel as small radial reliefs. The lower legs take the hem stack: from
300 mm down the radius is the boot shaft's ellipse (common.BOOT) plus 8 mm of cloth plus three rolls whose
height, crest and size vary round the leg. The shell is cut at the waist plane and the hem plane, Taubin-
smoothed, and pushed out to a minimum clearance (more at the lower back for the tucked shirt tail). Bound to
Morgan.Rig by weight transfer from Body.Mesh, then the shell's weights are smoothed round the waist and
seat, so the outer layer does not pinch where the spine extends. Idempotent: it starts from base.blend
every time.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PART, TAG = "Trousers", "trousers"

# Ease (outward offset from the skin, mm) by rest height: snug waistband over the shirt, roomy G3 legs.
EASE_Z = [(1100, 9.0), (1040, 11.0), (960, 15.0), (880, 17.0), (700, 20.0), (540, 22.0), (400, 24.0), (300, 24.0),
          (100, 24.0)]
SEAT_EASE = 10.0           # more at the back from the waistband to under the seat (a G3's seat room)
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
# The hem stack over the boot (take 1 spec 09 section 2.1: crests at floor h 293 / 254 / 212, i.e. rest z
# 257 / 218 / 184 with the 36 mm heel seat): (crest z, size mm, sigma mm, phase); each roll's crest wanders
# 7 mm and its size about 25 % round the leg, as stacked cloth does.
ROLLS = [(257.0, 13.0, 11.0, 0.3), (218.0, 17.0, 10.0, 2.1), (184.0, 19.0, 9.0, 4.0)]
STACK_TOP = 300.0
DRAPE = {"upper": 0.24, "lower": 0.08, "inner_half_deg": 58.0}
KNEE_FOLDS = {"amp": 1.8, "pitch": 24.0, "half": 46.0, "seam_dz": 118.0, "seam": 1.8}
COLOURS = {"camo": "#2a2723", "knee": "#232325"}   # the solid-view colours (round 1); Cycles uses MATERIALS
# Materials round (round 5, 2026-11-15): the library's recipes (scripts/lib/materials.py) per flat material:
# the shell the R002 camouflage print on NYCO ripstop, the knee-pad pockets black 500D Cordura. Dust is held on
# the cloth's sides too (up_low), by height zones (lower legs dusty, the seat least) and the left leg dustier.
MATERIALS = {
    "Trousers.Mat.Camo": ("NYCO.Ripstop.Camo", "Camo", {}),
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
CONVEX_K = 0.9             # how far the leg shell moves out to its sectional convex hull (cloth spans hollows)


def ease_z(z):
    zs, es = zip(*sorted(EASE_Z))
    return np.interp(z, zs, es)


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def leg_cyl(V, side):
    """Cylindrical coordinates round the leg's bone chain: axis point per vertex (at its height), the angle
    (degrees, 0 = front, +90 = outward, -90 = medial) and the radius in the horizontal plane."""
    sg = 1.0 if side == "L" else -1.0
    hip = C.bone_mm(f"upperleg01.{side}")
    A = np.array([C.leg_axis_point(side, min(z, hip[2] - 1.0))[0] for z in V[:, 2]])
    d = V[:, :2] - A[:, :2]
    r = np.linalg.norm(d, axis=1)
    th = np.degrees(np.arctan2(d[:, 0] * sg, -d[:, 1]))
    return A, th, r, d / np.maximum(r, 1e-9)[:, None]


def drape(V1, sel, side, knee_z):
    """The drape envelope (module doc, step 3) on the selected vertices of one leg."""
    idx = np.nonzero(sel)[0]
    if not len(idx):
        return V1
    P = V1[idx]
    A, th, r, u = leg_cyl(P, side)
    z = P[:, 2]
    tb = np.arange(-180.0, 180.1, 10.0)
    zt = np.arange(z.max(), z.min() - 6.0, -6.0)                 # going down
    R = np.full((len(tb), len(zt)), np.nan)
    ti = np.clip(np.round((th + 180.0) / 10.0).astype(int), 0, len(tb) - 1)
    zi = np.clip(np.round((zt[0] - z) / 6.0).astype(int), 0, len(zt) - 1)
    for a, b, rr in zip(ti, zi, r):
        if np.isnan(R[a, b]) or rr > R[a, b]:
            R[a, b] = rr
    R[0] = np.where(np.isnan(R[0]), R[-1], R[0])                  # -180 and +180 are one column
    R[-1] = R[0]
    for a in range(len(tb)):
        col = R[a]
        ok = ~np.isnan(col)
        R[a] = np.interp(np.arange(len(zt)), np.nonzero(ok)[0], col[ok]) if ok.sum() >= 2 else 0.0
    # smooth round the leg (circular), so the 10 degree bins leave no vertical stripes
    k = np.exp(-0.5 * (np.arange(-3, 4) / 1.3) ** 2)
    k /= k.sum()
    Rc = R[:-1]
    R[:-1] = np.maximum(Rc * 0.0, sum(w * np.roll(Rc, sh, axis=0) for w, sh in zip(k, range(-3, 4))))
    R[-1] = R[0]
    D = R.copy()
    for b in range(1, len(zt)):
        slope = DRAPE["upper"] if zt[b] > knee_z + 20.0 else DRAPE["lower"]
        D[:, b] = np.maximum(R[:, b], D[:, b - 1] - slope * 6.0)
    ft = np.clip((th + 180.0) / 10.0, 0, len(tb) - 1.001)
    fz = np.clip((zt[0] - z) / 6.0, 0, len(zt) - 1.001)
    a0, b0 = ft.astype(int), fz.astype(int)
    wa, wb = ft - a0, fz - b0
    tgt = ((D[a0, b0] * (1 - wb) + D[a0, b0 + 1] * wb) * (1 - wa)
           + (D[a0 + 1, b0] * (1 - wb) + D[a0 + 1, b0 + 1] * wb) * wa)
    med = np.abs(((th + 90.0 + 180.0) % 360.0) - 180.0)          # degrees from the medial direction
    w = smoothstep(DRAPE["inner_half_deg"], DRAPE["inner_half_deg"] + 25.0, med)   # not the inner thigh
    rn = r + np.maximum(tgt - r, 0.0) * w
    V1 = V1.copy()
    V1[idx, :2] = A[:, :2] + u * rn[:, None]
    return V1


def subdivide_below(V, F, ex, z_low, z_knee_hi, z_knee_lo):
    """Split the edges of faces below z_low or in the knee band once (grid fill), carrying the extra
    per-vertex columns along (interpolated)."""
    import bmesh
    bm = C.arrays_to_bm(V, F)
    lay = [bm.verts.layers.float.new(f"x{k}") for k in range(ex.shape[1])]
    bm.verts.ensure_lookup_table()
    for i, v in enumerate(bm.verts):
        for k, Ly in enumerate(lay):
            v[Ly] = float(ex[i, k])
    zf = lambda f: [v.co.z for v in f.verts]
    faces = [f for f in bm.faces if min(zf(f)) < z_low or (z_knee_lo < min(zf(f)) and max(zf(f)) < z_knee_hi)]
    edges = list({e for f in faces for e in f.edges})
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
    bm.verts.index_update()
    V2, F2 = C.bm_to_arrays(bm)
    ex2 = np.array([[v[Ly] for Ly in lay] for v in bm.verts])
    bm.free()
    return V2, F2, ex2


def build(body, rig):
    bd = C.body_data(body)
    V0 = bd["V"]
    arm = C.weight_sum(bd, C.is_arm)
    head = C.weight_sum(bd, C.is_head)
    keep = bd["in_body"] & (arm < 0.05) & (head < 0.05) & (V0[:, 2] > 105.0) & (V0[:, 2] < 1130.0)
    V, F, idx = C.submesh(V0, F=bd["F"], keep=keep)
    bvh0 = C.skin_bvh(bd)
    V, F, N = C.refine_on_skin(V, F, bvh0, cuts=1)
    C.say(TAG, f"skin region: {len(V)} verts, {len(F)} faces (refined)")

    sgn = np.where(V[:, 0] >= 0, 1.0, -1.0)
    off = ease_z(V[:, 2])
    # seat room: more ease at the back from the waistband down past the gluteal fold
    behind_n = smoothstep(-0.1, 0.5, N[:, 1])                     # normals facing +Y (behind)
    off += SEAT_EASE * behind_n * smoothstep(740.0, 860.0, V[:, 2]) * (1 - smoothstep(1030.0, 1070.0, V[:, 2]))
    # waistband: a 45 mm band standing 3 mm proud at the top
    wn = np.array(WAIST["no"]) / np.linalg.norm(WAIST["no"])
    below_top = -((V - np.array(WAIST["co"])) @ wn)            # mm below the waist plane
    off += WAISTBAND_PROUD * (1 - smoothstep(WAISTBAND_MM - 6, WAISTBAND_MM + 2, below_top)) * (below_top > -20)

    off = C.limit_by_gap(V, N, off, bvh0, share=0.5, floor=1.5)
    E = C.edges_of(F)
    off = C.smooth_field(off, E, iters=6, lam=0.5)
    V1 = V + N * off[:, None]
    # (1) the seat: above the crotch the section spans the cleft
    # (the back only: in front the lower belly keeps round 1's snug waist, which the carrier's flap clears)
    seat = (V[:, 2] > CROTCH_Z + 8.0) & (V[:, 2] < 1040.0) & (V[:, 1] > -10.0)
    V1 = C.convexify_along(V1, seat, np.zeros(3), np.array([0.0, 0.0, 1.0]), slab=8.0, k=1.0, centre=np.zeros(2))
    seam = (V[:, 2] > CROTCH_Z - 10.0) & (V[:, 2] < CROTCH_Z + 40.0) & (V[:, 1] > 0.0)   # the back seam to the crotch
    V1 = C.convexify_along(V1, seam, np.zeros(3), np.array([0.0, 0.0, 1.0]), slab=8.0, k=1.0, centre=np.zeros(2))
    knee_z = C.bone_mm("lowerleg01.L")[2]
    for side, sg in (("L", 1.0), ("R", -1.0)):
        # (2) the legs hang: below the crotch each leg's shell moves out towards its sectional convex hull
        hip, ankle = C.bone_mm(f"upperleg01.{side}"), C.bone_mm(f"foot.{side}")
        sel = (sgn == sg) & (V[:, 2] < CROTCH_Z - 10.0)
        V1 = C.convexify_along(V1, sel, ankle, hip - ankle, slab=8.0, k=CONVEX_K)
        # (3) the drape envelope, from the seat's crest down
        sel = (sgn == sg) & (V[:, 2] < 1000.0)
        V1 = drape(V1, sel, side, knee_z)

    # cut the waist and the hem, smooth, push out to a minimum clearance
    V1, F1, ex = C.bisect(V1, F, WAIST["co"], WAIST["no"], keep="below", extra=off[:, None])
    V1, F1, ex = C.bisect(V1, F1, HEM["co"], HEM["no"], keep="above", extra=ex)
    # the lower legs and knees get finer faces (MPFB's shin faces are long) for the reliefs and the stack
    for _ in range(2):
        V1, F1, ex = subdivide_below(V1, F1, ex, STACK_TOP + 60.0, knee_z + 170.0, knee_z - 170.0)
    E1 = C.edges_of(F1)
    pin = C.boundary_verts(F1, len(V1))
    V1 = C.taubin(V1, E1, iters=26, lam=0.5, mu=-0.53, pin=pin)
    sgn1 = np.where(V1[:, 0] >= 0, 1.0, -1.0)
    # the knee: G3 back-of-knee folds and the seam band above the knee panel (radial reliefs)
    for side, sg in (("L", 1.0), ("R", -1.0)):
        sel = np.nonzero((sgn1 == sg) & (np.abs(V1[:, 2] - knee_z) < 160.0))[0]
        A, th, r, u = leg_cyl(V1[sel], side)
        rel = V1[sel, 2] - knee_z
        backw = smoothstep(130.0, 160.0, np.abs(th))
        win = np.clip(1 - (rel / KNEE_FOLDS["half"]) ** 2, 0, 1) ** 1.5
        folds = (KNEE_FOLDS["amp"] * np.sin(2 * np.pi * rel / KNEE_FOLDS["pitch"] + 0.6 * np.sin(np.radians(th) * 2))
                 * win * backw)
        frontw = smoothstep(110.0, 80.0, np.abs(th))
        seam = KNEE_FOLDS["seam"] * np.exp(-((rel - KNEE_FOLDS["seam_dz"]) / 3.0) ** 2) * frontw
        V1[sel, :2] = A[:, :2] + u * (r + folds + seam)[:, None]

    # lower legs: the hem stack over the boot shaft (ellipse centred on the leg's skin section)
    a_y, a_x = C.BOOT["shaft_rim_ab"]
    rim = C.BOOT["rim_z_rest"]
    low = V1[:, 2] < STACK_TOP + 40.0
    for s, sg in (("L", 1.0), ("R", -1.0)):
        sel = np.nonzero(low & (sgn1 == sg))[0]
        if not len(sel):
            continue
        sec = C.leg_section(bd, s, rim - 5.0, half=12.0)
        C.say(TAG, f"leg section {s} at rest z {rim - 5:.0f}: centre {sec['c'].round(1)}, half {sec['half'].round(1)}")
        c = sec["c"]
        for i in sel:
            z = V1[i, 2]
            r = V1[i, :2] - c
            rl = np.linalg.norm(r)
            if rl < 1e-6:
                continue
            u = r / rl
            th = math.atan2(u[0] * sg, -u[1])
            re = 1.0 / math.sqrt((u[0] / a_x) ** 2 + (u[1] / a_y) ** 2)
            stack = 0.0
            for zr, size, sig, ph in ROLLS:
                zc = zr + 9.0 * math.sin(th + ph) + 4.0 * math.sin(2 * th + 3.1 * ph)
                amp = size * (0.72 + 0.30 * math.sin(2 * th + 1.3 * ph) + 0.18 * math.sin(3 * th + ph * 2.7))
                stack += amp * math.exp(-0.5 * ((z - zc) / sig) ** 2)
            base = re + 8.0                                        # cloth over the shaft and its 10 mm collar
            want = base + stack
            if z < ROLLS[-1][0]:                                   # the hem edge rests open on the boot,
                want = max(want, base + 0.75 * ROLLS[-1][1])       # not gathered like a jogger's cuff
            blend = 1.0 - smoothstep(STACK_TOP - 20.0, STACK_TOP + 35.0, z)
            target = rl + (max(want, min(rl, base + 6.0)) - rl) * blend
            V1[i, :2] = c + u * max(target, base if z < STACK_TOP else 0.0)

    behind = smoothstep(20.0, 80.0, V1[:, 1])
    clear = (np.maximum(0.55 * ex[:, 0], 4.0) + 3.0 * (V1[:, 2] > 940.0)
             + 5.0 * behind * smoothstep(930.0, 960.0, V1[:, 2]))      # room for the tucked shirt tail
    V1 = C.push_out(V1, bvh0, clear)
    return V1, F1, ex, bd


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


def measure(ob, bd, ex):
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
            out[f"{label}_{s}_width_x_mm"] = round(float(np.ptp(P[:, 0])), 1)
            out[f"{label}_{s}_depth_y_mm"] = round(float(np.ptp(P[:, 1])), 1)
    out["waist_top_z_mm"] = [round(float(V[:, 2].max()), 1)]
    out["hem_z_min_mm"] = round(float(V[:, 2].min()), 1)
    out["outseam_rest_mm"] = round(float(V[:, 2].max() - V[:, 2].min()), 1)
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
    V, F, ex, bd = build(body, rig)
    mats = {"camo": C.flat_material("Trousers.Mat.Camo", COLOURS["camo"], 0.85),
            "knee": C.flat_material("Trousers.Mat.KneePocket", COLOURS["knee"], 0.6)}
    ob = C.mesh_object("Trousers.Shell", V, F, coll, mat=mats["camo"])
    ob["sgt_clay"] = (0.52, 0.48, 0.42)
    pk = pockets(V, F, coll, mats)
    for o in [ob] + pk:
        C.bind(o, body, rig)
        C.solidify(o, 1.5 if o is ob else 1.2, inward=True)
        C.subsurf(o, 1)
    Vr = np.array([tuple(v.co) for v in ob.data.vertices]) * 1000.0
    smooth_weights(ob, Vr[:, 2] > 860.0, iters=14)
    for o in [ob] + pk:
        dust_zones(o)
    lib = C.library_pass(coll, "Trousers", MATERIALS, say_tag=TAG)
    rest = C.clearance([ob] + pk, body, "rest")
    meas = measure(ob, bd, ex)
    meas["seat_standoff_mm"] = seat_standoff(ob, bd)
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
