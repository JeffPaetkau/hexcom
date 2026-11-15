"""Trousers, round 1 blockout: Crye G3 class combat trousers as one offset shell from the rest body, with
the knee-pad pockets, thigh cargo pockets and calf pockets as volumes in the offset field, a waistband,
and the hems stacked in three rolls over the boot collars. Notes: scripts/parts/trousers.md.

  "$SGT_BLENDER" -b --python scripts/parts/trousers.py [-- --no-render]
  -> cache/parts/trousers.blend (Part.Trousers: Trousers.Shell), cache/parts/trousers.json (measurements),
     renders/trousers/*.png

Method: the body's skin from just above the ankles to above the hips (arms and head excluded by bone
weight) is copied, each vertex pushed out along its normal by an ease field (mm, by height and by the
pockets' pillow shapes in leg coordinates), the push capped where the skin faces itself (the crotch),
smoothed (Taubin), cut by the waist plane and the hem plane, pushed out again to a minimum clearance,
and the lower legs widened radially so the hem encloses the boot shaft (common.BOOT). Bound to Morgan.Rig
by weight transfer from Body.Mesh. Idempotent: it starts from base.blend every time.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PART, TAG = "Trousers", "trousers"

# Ease (outward offset from the skin, mm) by rest height: snug waistband over the shirt, roomy G3 legs.
EASE_Z = [(1100, 9.0), (1040, 11.0), (960, 14.0), (880, 16.0), (700, 19.0), (540, 21.0), (400, 24.0), (300, 24.0),
          (100, 24.0)]
WAIST = {"co": (0.0, 0.0, 1072.0), "no": (0.0, -0.15, 1.0)}     # top edge: 1052 front, 1087 back
HEM = {"co": (0.0, 0.0, 152.0), "no": (0.0, 0.0, 1.0)}          # hem edge 24 mm below the boot rim (rest)
WAISTBAND_MM, WAISTBAND_PROUD = 45.0, 3.0
# Pockets as sheets lying on the shell (common.surface_patch), in leg coordinates: theta (deg, 0 = front,
# +90 = outside), z centre (mm, rest; "dz" from the knee joint), half arc width and half height (mm), depth
# (mm proud of the shell). G3 class: knee pocket 175 x 225 holding an AirFlex-class pad (about 16 thick);
# bellows thigh cargo 200 x 190 x 25 (filled 18) with a 70 mm flap; calf pocket 85 x 145 x 15 with a 45 flap.
POCKETS = {
    "Knee": {"theta": 0.0, "dz": -8.0, "w": 88.0, "h": 112.0, "depth": 17.0, "edge": 34.0, "mat": "knee"},
    "Cargo": {"theta": 68.0, "z": 792.0, "w": 100.0, "h": 95.0, "depth": 18.0, "edge": 12.0, "tilt": -6.0},
    "CargoFlap": {"theta": 68.0, "z": 862.0, "w": 104.0, "h": 33.0, "depth": 22.0, "edge": 6.0, "tilt": -6.0},
    "Calf": {"theta": 96.0, "z": 335.0, "w": 42.0, "h": 72.0, "depth": 10.0, "edge": 8.0},
    "CalfFlap": {"theta": 96.0, "z": 392.0, "w": 45.0, "h": 22.0, "depth": 12.0, "edge": 5.0},
}
# The hem stack over the boot: three rolls (crests at floor h 293 / 254 / 212, take 1 spec 09 §2.1) in the
# rest frame (floor minus the heel seat), proud of the boot shaft ellipse + 5 mm of cloth.
ROLLS = [(257.0, 8.0), (218.0, 12.0), (184.0, 13.0)]
ROLL_SIGMA = 9.0
COLOURS = {"camo": "#2a2723", "knee": "#232325"}
CONVEX_K = 0.85            # how far the leg shell moves out to its sectional convex hull (cloth spans hollows)
def ease_z(z):
    zs, es = zip(*sorted(EASE_Z))
    return np.interp(z, zs, es)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def build(body, rig):
    bd = C.body_data(body)
    V0, N0 = bd["V"], bd["N"]
    arm = C.weight_sum(bd, C.is_arm)
    head = C.weight_sum(bd, C.is_head)
    keep = bd["in_body"] & (arm < 0.05) & (head < 0.05) & (V0[:, 2] > 105.0) & (V0[:, 2] < 1130.0)
    V, F, idx = C.submesh(V0, F=bd["F"], keep=keep)
    bvh0 = C.skin_bvh(bd)
    V, F, N = C.refine_on_skin(V, F, bvh0, cuts=1)
    C.say(TAG, f"skin region: {len(V)} verts, {len(F)} faces (refined)")

    sgn = np.where(V[:, 0] >= 0, 1.0, -1.0)
    off = ease_z(V[:, 2])
    # waistband: a 45 mm band standing 3 mm proud at the top
    wn = np.array(WAIST["no"]) / np.linalg.norm(WAIST["no"])
    below_top = -((V - np.array(WAIST["co"])) @ wn)            # mm below the waist plane
    off += WAISTBAND_PROUD * (1 - smoothstep(WAISTBAND_MM - 6, WAISTBAND_MM + 2, below_top)) * (below_top > -20)

    off = C.limit_by_gap(V, N, off, bvh0, share=0.5, floor=1.5)
    E = C.edges_of(F)
    off = C.smooth_field(off, E, iters=6, lam=0.5)
    V1 = V + N * off[:, None]
    # the legs hang: below the crotch each leg's shell moves out towards its sectional convex hull
    for side, sg in (("L", 1.0), ("R", -1.0)):
        hip, ankle = C.bone_mm(f"upperleg01.{side}"), C.bone_mm(f"foot.{side}")
        sel = (sgn == sg) & (V[:, 2] < 880.0)
        V1 = C.convexify_along(V1, sel, ankle, hip - ankle, slab=8.0, k=CONVEX_K)

    # lower legs: enclose the boot shaft (ellipse centred on the leg's skin section) plus the hem stack
    a_y, a_x = C.BOOT["shaft_rim_ab"]
    rim = C.BOOT["rim_z_rest"]
    low = V1[:, 2] < 340.0
    for s, sg in (("L", 1.0), ("R", -1.0)):
        sel = np.nonzero(low & (sgn == sg))[0]
        if not len(sel):
            continue
        sec = C.leg_section(bd, s, rim - 5.0, half=12.0)
        C.say(TAG, f"leg section {s} at rest z {rim - 5:.0f}: centre {sec['c'].round(1)}, half {sec['half'].round(1)}")
        for i in sel:
            z = V[i, 2]
            c = sec["c"]
            r = V1[i, :2] - c
            rl = np.linalg.norm(r)
            if rl < 1e-6:
                continue
            u = r / rl
            # ellipse radius in the direction u (x side half-axis a_x, y front-back half-axis a_y)
            re = 1.0 / math.sqrt((u[0] / a_x) ** 2 + (u[1] / a_y) ** 2)
            stack = sum(pr * math.exp(-0.5 * ((z - zr) / ROLL_SIGMA) ** 2) for zr, pr in ROLLS)
            base = 8.0 if z <= rim + 12 else 8.0 * (1 - smoothstep(rim + 12, 330.0, z))   # clears the 10 mm collar roll
            want = re + base + stack
            blend = 1.0 - smoothstep(290.0, 340.0, z)
            if rl < want:
                V1[i, :2] = c + u * (rl + (want - rl) * blend)

    # cut the waist and the hem, smooth, push out to a minimum clearance
    V1, F1, ex = C.bisect(V1, F, WAIST["co"], WAIST["no"], keep="below",
                          extra=off[:, None])
    V1, F1, ex = C.bisect(V1, F1, HEM["co"], HEM["no"], keep="above", extra=ex)
    E1 = C.edges_of(F1)
    pin = C.boundary_verts(F1, len(V1))
    V1 = C.taubin(V1, E1, iters=12, lam=0.5, mu=-0.53, pin=pin)
    clear = np.maximum(0.55 * ex[:, 0], 4.0) + 3.0 * (V1[:, 2] > 940.0)    # room for the tucked shirt
    V1 = C.push_out(V1, bvh0, clear)
    return V1, F1, ex, bd


def measure(ob, bd, ex):
    """Garment girths at a few heights (rest), the outseam and the stack."""
    V, F = C.evaluated_world_mm(ob)
    out = {}
    for s, sg in (("L", 1.0), ("R", -1.0)):
        for label, z in (("thigh", 820.0), ("knee", C.bone_mm(f"lowerleg01.{s}")[2] - 8), ("calf", 420.0),
                         ("hem_stack", 200.0)):
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
            out[f"{label}_{s}_width_x_mm"] = round(float(P[:, 0].ptp()), 1)
            out[f"{label}_{s}_depth_y_mm"] = round(float(P[:, 1].ptp()), 1)
    out["waist_top_z_mm"] = [round(float(V[:, 2].max()), 1)]
    out["hem_z_min_mm"] = round(float(V[:, 2].min()), 1)
    out["outseam_rest_mm"] = round(float(V[:, 2].max() - V[:, 2].min()), 1)
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
                                   p["depth"], edge=p["edge"], tilt=p.get("tilt", 0.0) * (1 if side == "L" else 1),
                                   nu=24, nv=24)
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
    rest = C.clearance([ob] + pk, body, "rest")
    meas = measure(ob, bd, ex)
    C.say(TAG, meas)
    used = C.apply_hero_pose(rig)
    posed = C.clearance([ob] + pk, body, "hero pose")
    C.rest_pose(rig)
    C.save_part(TAG, coll, {"measure_rest_mm": meas, "clearance_rest": rest, "clearance_posed": posed,
                            "pose": used, "verts": len(V)})
    if "--no-render" not in args:
        C.render_part(TAG, coll, (0, 0, 600), 1250, crops=("ref.legs_knees", "ref.soldier_full"))


if __name__ == "__main__":
    main()
