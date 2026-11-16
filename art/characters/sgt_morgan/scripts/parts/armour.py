"""Armour, round 10: the hard shells. Per side: a pauldron (a domed cap on a foam liner over a long outer upper-arm
plate on its own liner, held by a coyote webbing strap round the arm with a flat ladder-lock), a forearm guard (a
padded sleeve, two shingled dorsal shells tapering from below the elbow to the glove cuff, rolled rims, a rib and
grooves, foam under each, two straps with ladder-locks), an elbow pad (a domed cap on a neoprene base on the point of
the elbow, straps round the upper arm and the forearm), and a faceted hard-cap knee pad (a padded base filling the
dome, a domed cap with a patella dome on its central plate, a stepped frame with slots, strap with a ladder-lock and
a tan tail on the medial side, the red tab on the lateral facet). Left only: the emblem plate on the cap and the IR
strobe on the upper-arm plate. The arm straps and the guard shells are cleared of the posed sleeve (posed_clear).
Notes: scripts/parts/armour.md.

  "$SGT_BLENDER" -b --python scripts/parts/armour.py [-- --no-render]
  -> cache/parts/armour.blend (Part.Armour), cache/parts/armour.json, renders/armour/*.png

Method: each shell is a slab over a smooth surface around a limb: the clothed limb's outermost radius is
sampled by rays toward (or from) the limb axis (the shoulder cap by rays toward the shoulder joint), smoothed
so a rigid shell bridges the folds, kept outside the raw surface, and offset by the padding under the shell.
The forearm plates use a straight (ruled) surface instead: per angle round the forearm, the radius is a
straight line along the forearm fitted to the clothed samples and raised until no sample is outside it, so
a plate is a straight shell, not a cone that flares with the sleeve. Rims, ribs, grooves and frame steps are
a thickness field over each slab (gear_common.edge_profile). The shoulder cap also clears the carrier's
shoulder-strap pads (cache/parts/carrier.blend, when it exists).

Rigging: the pauldron pieces are skinned 100 % to one bone (cap, its foam, rivets, emblem, tier 2 and
strobe: upperarm01 (the cap is turned back at rest, CAP_FWD, so the pose's inward-turned upper arm brings it
to the outside of the shoulder; bound to shoulder01 it stood off the adducted arm like a wing); round 10: the
upper-arm strap (Tier3.Strap) by weights from the body, its ladder-lock mounted on the skin). Round 6: the guard plates, their foam and ladder-locks, the knee caps, tabs and ladder-locks
are MOUNTED on the skin at their centre (gear_common.mount_bind on Body.Mesh: the skin's weights there on every
vertex, one blended transform), so a knee cap follows the kneecap however the knee bends or the shin twists, and
a guard follows the forearm's twist. The guard sleeves and straps are bound by weights from the body with the
upper-arm bones folded into lowerarm01, so they move with the forearm and do not collapse into the elbow fold;
the elbow pad (cap and base) and its straps, the knee bases and straps by plain weights from the body.
Idempotent: it starts from base.blend every time.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gear_common as G  # noqa: E402
from lib import gear_hardware as GH  # noqa: E402

PART, TAG = "Armour", "armour"

COL = {"shell": "#7b7064", "knee": "#6a6158", "black": "#1d1c1b", "emblem": "#a9b3bd", "mark": "#e6ebef",
       "strobe": "#9fb0bf", "strobe_body": "#333537", "tan": "#8a7560", "metal": "#5b5a58",
       "silver": "#9a948c", "red": "#a0545c", "foam": "#2a2927", "band": "#4a4034"}   # solid-view colours; Cycles uses MATERIALS
# Materials round (round 5, 2026-11-15): FDE-moulded shells painted dark grey, worn through to the tan on the
# rims and in chips (the reference's knee caps and pauldrons), the knee caps the most worn; neoprene sleeves,
# bases and straps; the emblem plate brushed blue-grey anodised with R003's mark (UV.Decal, decal_uv()); the
# strobe's frosted lens; gunmetal rivets, a brighter cam buckle, a red TPR tab, coyote strap tails.
# Round 9 (critics r8 m6, m12, m3): the reference's plates MEASURED (ref/zoom_armour_*: medians over plate faces,
# sRGB): the right guard's lit plate #a99687 (r/g 1.13, b/g 0.90), the left guard's upper plate #89786b (1.14, 0.89),
# the right knee cap's frame #877665 (1.14, 0.86) and centre #4d443d (1.13, 0.90); only faces turned to the cool
# light read blue-grey (the left tier 2 #758598, 0.88 / 1.14; the left pauldron #595d68). So: worn tan-grey moulded
# shells, mid value, not black paint over bright steel; the blue-grey is the cool light on the same colour. Wear:
# a paler matte of the same tan on edges and corners (no bare metal), low contrast, dust and grime in recesses.
# Round 10 (critics r9 m2, m8, m25, m45, m48: "uniformly pale, clean plastic"; the drawn plates darker in places,
# scratched and grimed, with worn tan edges). The plates' MEDIAN was not the fault: under a shell-only mask the round-9
# plates measured Y 0.21 (arm_L), 0.24 (arm_R) graded, against the reference plates' 0.11-0.23 and 0.32 (§12). What
# was missing is texture-scale contrast: here a fine dark grime mottle (14 mm, toward #2e2b27 at 0.65), R005's
# scratches at 0.9 on a 90 mm tile with the bright ones up to 2 x, broad tan worn rims (#b09c7c over 4 mm), chips
# near the edges, more grime in the recesses, and a less glossy paint (roughness 0.36 -> 0.50, the "plastic" sheen)
ARMOUR_TAN = {"albedo_hex": "#6a655c", "rough": 0.50, "rough_span": 0.20,
              "mottle__hex": "#2e2b27", "mottle__amount": 0.65, "mottle__noise_mm": 14.0,
              "paint_image__saturation": 0.3, "paint_image__amount": 0.9, "paint_image__max": 2.0,
              "paint_image__tile_mm": 90.0,
              "substrate__f0": None, "substrate__hex": "#b09c7c", "substrate__rough": 0.65,
              "substrate__primer": 0.0, "chips__cover": 0.004, "chips__edge_cover": 0.05,
              "edge__band_mm": 4.0, "edge__noise_amount": 0.3,
              "dust__amount": 0.2, "rub__amount": 0.15, "grime__amount": 1.4, "grime__cavity": 1.2}
MATERIALS = {
    "Armour.Mat.Shell": ("Polymer.Painted.Armour", "Shell", dict(ARMOUR_TAN)),
    # the knee caps: a darker brown-grey centre, the raised frame worn to a paler tan (`paint_wear`)
    # round 10 (m14, m25, D21: glossy toy plastic with smeared highlights; the drawn caps matte with a tan rim): matte
    # (0.62), the centre a grimed brown-grey, the frame worn to tan (#a08a68) and broken by the paint left on it
    "Armour.Mat.Knee": ("Polymer.Painted.Armour", "Knee", dict(ARMOUR_TAN, **{"rub__amount": 0.0,
        "albedo_hex": "#746a5e", "mottle__hex": "#2e2a25", "mottle__amount": 0.6, "rough": 0.62,
        "edge__radius_mm": 1.2, "edge__width": 0.06,
        "chips__cover": 0.0, "chips__edge_cover": 0.0, "chips__noise_mm": 5.0, "dust__amount": 0.3,
        "frame__break": 0.35, "frame__noise_mm": 20.0,
        "substrate__hex": "#a08a68", "substrate__rough": 0.7})),
    "Armour.Mat.Black": ("Neoprene.Black", "Black", {}),
    "Armour.Mat.Emblem": ("Decal.Emblem", "Emblem", {}),
    "Armour.Mat.Foam": ("Foam.ClosedCell.Black", "Foam", {}),
    "Armour.Mat.Metal": ("Metal.Gunmetal", "Metal", {}),
    "Armour.Mat.Silver": ("Metal.Gunmetal", "Silver", {"f0": (0.42, 0.42, 0.43), "rough_range": (0.30, 0.42),
                                                       "aniso": 0.0}),
    "Armour.Mat.Red": ("Polymer.Black.Smooth", "Red", {"albedo_hex": "#7a3f42", "rough": 0.55}),
    "Armour.Mat.Strobe": ("Lens.Strobe.Polycarbonate", "Strobe", {}),
    "Armour.Mat.Tan": ("Webbing.Nylon.Coyote", "Tan", {}),
    # round 10: the upper-arm strap (was the pale moulded tier-3 band): coyote webbing, dirtied darker
    "Armour.Mat.Band": ("Webbing.Nylon.Coyote", "Band", {"albedo_hex": "#3d3329"}),
}


def frame_wear(ob, urange, v0, v1, nu, nv, hw_fn, inner=(9.0, 12.5)):
    """The knee cap's raised frame as the point attribute `paint_wear` (1 on the frame, 0 on the centre panel
    2 mm below it), from the slab's own grid parameters (gear_common.grid_points: rows v, columns u over
    urange(v); inner then outer surface): e = distance to the outline (knee_field's), worn where e < 9-12.5 mm."""
    W = []
    for j in range(nv + 1):
        v = v0 + (v1 - v0) * j / nv
        a, b = urange(v)
        for u in np.linspace(a, b, nu + 1):
            e = min(hw_fn(v) - abs(u), v - v0, v1 - v)
            W.append(1.0 - G.smoothstep(e, inner[0], inner[1]))
    W = np.array(W, np.float32)
    me = ob.data
    if len(me.vertices) != 2 * len(W):
        return None
    att = me.attributes.get("paint_wear") or me.attributes.new("paint_wear", "FLOAT", "POINT")
    att.data.foreach_set("value", np.concatenate([W, W]))
    return round(float(W.mean()), 3)


def posed_clear(objs, rig, unders, clear=1.0, iters=4, reach=30.0, cap=6.0, deep=12.0, log=None):
    """Round 10 (G1 D1, blocking: the right elbow pad's upper strap broke into floating pieces where it met the
    sleeve). A strap is a ring fitted to the REST sleeve; the round-9 sleeves have 27-29 mm of ease and simulated
    folds, and in the hero pose the sleeve and the strap deform differently, so the sleeve's folds came up through
    the strap in patches (the strap read as pieces). Here, in the hero pose, every strap vertex pair (inner face,
    outer face: gear_common.slab's layout) is tested against the posed surfaces it lies on (`unders`: the shirt's
    outer face, which is the shell without Solidify, as the clash test sees it, and any plate it crosses); where
    its inner face is less than `clear` mm outside, the pair is pushed out at rest along its own thickness
    direction by the shortfall, spread smoothly to its neighbours. Linear skinning is locally near-rigid, so a
    push at rest moves the posed strap by about the same. A vertex needing more than `deep` mm on the first pass lies
    in a fold the strap cannot bridge (the crease of the flexed elbow, where the strap's ends lie by design) and is
    left; no vertex moves more than `cap` mm in all. Then the rest pose again. Returns {name: max push mm}."""
    import bpy
    from mathutils import Vector
    C.apply_hero_pose(rig)
    out = {}
    try:
        Vs, Fs, n = [], [], 0
        for o in unders:
            V, F = C.evaluated_world_mm(o, disable=("SOLIDIFY", "SUBSURF", "BEVEL"))
            if not len(V) or not F:
                continue
            Vs.append(V)
            Fs += [tuple(i + n for i in f) for f in F]
            n += len(V)
        bvh = C.bvh_from(np.concatenate(Vs), Fs)
        for ob in objs:
            me = ob.data
            nv = len(me.vertices)
            half = nv // 2
            R0 = np.empty(nv * 3)
            me.vertices.foreach_get("co", R0)
            R0 = R0.reshape(-1, 3).copy()
            drest = R0[half:] - R0[:half]
            drest /= np.maximum(np.linalg.norm(drest, axis=1, keepdims=True), 1e-9)
            E = np.array([(e.vertices[0], e.vertices[1]) for e in me.edges if e.vertices[0] < half and e.vertices[1] < half])
            total = np.zeros(half)
            skip = np.zeros(half, bool)
            for _it in range(iters):
                Vp, _F = C.evaluated_world_mm(ob, disable=tuple(m.type for m in ob.modifiers if m.type != "ARMATURE"))
                if len(Vp) != nv:
                    break
                inner, outer = Vp[:half], Vp[half:]
                dpos = outer - inner
                dpos /= np.maximum(np.linalg.norm(dpos, axis=1, keepdims=True), 1e-9)
                need = np.zeros(half)
                for i in range(half):
                    loc, nrm, _idx, dist = bvh.find_nearest(Vector(inner[i]), reach)
                    if loc is None:
                        continue
                    nn = np.array(nrm)
                    if nn @ dpos[i] < 0:
                        nn = -nn
                    sd = float((inner[i] - np.array(loc)) @ nn)
                    need[i] = max(0.0, clear - sd)
                if _it == 0:
                    skip = need > deep
                need[skip] = 0.0
                need = np.minimum(need, cap - total)
                if need.max() < 0.1:
                    break
                if len(E):                      # spread each push to its neighbours, never below the raw need
                    sm = need.copy()
                    for _ in range(4):
                        acc = np.zeros(half)
                        deg = np.zeros(half)
                        np.add.at(acc, E[:, 0], sm[E[:, 1]])
                        np.add.at(acc, E[:, 1], sm[E[:, 0]])
                        np.add.at(deg, E[:, 0], 1)
                        np.add.at(deg, E[:, 1], 1)
                        sm = np.maximum(need, 0.85 * acc / np.maximum(deg, 1))
                    need = np.minimum(sm, cap - total)
                step = need[:, None] * drest * C.MM            # rest coordinates are metres
                R0[:half] += step
                R0[half:] += step
                total += need
                me.vertices.foreach_set("co", R0.ravel())
                me.update()
            out[ob.name] = round(float(total.max()), 1)
    finally:
        C.rest_pose(rig)
    if log:
        log("posed_clear (mm pushed out at rest):", json.dumps(out))
    return out


def decal_uv(ob, uv="UV.Decal"):
    """A 0-1 planar UV over a plate for a decal (R003's emblem): the plate's principal axes, v up (toward
    the plate's highest rest z), u to the right as seen from outside (away from the body's mid-line), so the
    image is never mirrored."""
    me = ob.data
    M = np.array(ob.matrix_world)
    V = np.array([tuple(v.co) for v in me.vertices]) @ M[:3, :3].T + M[:3, 3]
    c = V.mean(0)
    _, _, W = np.linalg.svd(V - c, full_matrices=False)
    a_len, n = W[0], W[2]
    if np.dot(c[:2], n[:2]) < 0:                      # the plate's normal out from the body (sideways at the shoulder)
        n = -n
    up = a_len if a_len[2] >= 0 else -a_len
    right = np.cross(up, n)
    P = V - c
    pu, pv = P @ right, P @ up
    u = (pu - pu.min()) / max(np.ptp(pu), 1e-9)
    v = (pv - pv.min()) / max(np.ptp(pv), 1e-9)
    lay = me.uv_layers.get(uv) or me.uv_layers.new(name=uv)
    lv = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    lay.data.foreach_set("uv", np.stack([u[lv], v[lv]], 1).astype(np.float32).ravel())
    return {"width_mm": round(float(np.ptp(pu)) * 1000.0, 1), "height_mm": round(float(np.ptp(pv)) * 1000.0, 1)}

# Pauldron (mm; frame A: around the shoulder joint and the upper-arm axis)
CAP_PAD = 7.0                 # round 6: shirt to the cap's inner face, filled by a 6 mm foam liner (12 mm with no
                              # liner read as a card standing off the shoulder over a dark gap)
CAP_FOAM = 6.0
CAP_T = 3.0
CAP_W_TOP, CAP_W_BOT = 150.0, 122.0
CAP_Q = (-40.0, 50.0)         # deg from the cap's centre direction: top flange .. bottom lip (round 6: the flange
                              # stops short of the carrier's strap pad, -54 lifted the whole cap over it)
CAP_SMOOTH = 10               # round 6: the cap field's smoothing (10 flattened the cup into a plank); round 10: 4 -> 10
                              # with the dome (CAP_DOME) carrying the curvature
CAP_LINK = 0.42               # rad above the cap's top edge: the webbing link up over the carrier's strap pad
CAP_UP = {"L": 1.3, "R": 1.0}  # the cap's centre: CAP_UP x up + down the arm (+ CAP_FWD x front), at rest.
                              # Round 10 (critics r9 m17, D7: the right cap perched flat and high by the collar, standing
                              # off the arm; the drawn one a curved shell low on the outer deltoid): R 1.3 -> 1.0
CAP_DOME = 9.0                # round 10 (m31): the cap domed this much (mm) over the fitted shoulder at its centre
CAP_FWD = {"L": -0.25, "R": 0.12}   # turned back at rest (round 1: 0.45 forward): the hero pose turns the upper arm
                              # in, so posed the cap faces out and up on the outside of the shoulder, as drawn.
                              # Round 9 (critics r8 m2, all three: the right cap "a fin" seen edge-on on the outside of
                              # the shoulder): the right cap turned forward (+0.30, was -0.25) so it caps the front of the
                              # deltoid and faces the camera as the drawn one does; the left one is unchanged
CAP_STRAP_CLEAR = 2.0         # over the carrier's shoulder-strap pads
EMBLEM_W, EMBLEM_H, EMBLEM_R = 58.0, 70.0, 10.0   # round 8 (m34): the drawn rounded-square emblem plate (was a 50 x 95 shield)
TIER2_S, TIER2_ARC = (78.0, 228.0), 112.0     # s along the arm below the joint; arc (mm) about the lateral line.
                              # Round 10 (m31, m8: the drawn upper arm carries a long second plate on its outer face, its
                              # lower half held by a dark strap; ours a short square plate and a pale ring): 76-166 x 140
                              # -> a long outer-arm plate 78-228 x 112 with chamfered lower corners
TIER2_CHAMFER = 16.0
TIER3_S, TIER3_DEG = (148.0, 186.0), 200.0    # round 10: the bicep band is now a 38 mm coyote webbing strap round the
                                              # arm and over tier 2 (Tier3.Strap), 0.4 mm over the sleeve: it bears on
                                              # the cloth instead of standing proud as a pale moulded ring (m8, m20);
                                              # across the plate's lower middle, as drawn, the plate showing below it
STRAP_DARK = "#4a4034"        # the strap's webbing, darker than the plates (the drawn band reads brown-grey)
SHELL_PAD = 4.5               # round 6: over a 4 mm foam liner (6 with no liner stood off as a card)
SHELL_FOAM = 4.0
# Forearm guard: d from the elbow axis (mm). Round 6: a gauntlet, not rings: one long shaped main shell over the
# outer half of the forearm from below the elbow (d 96) and a wrist plate under its lower lip to the glove cuff,
# over a padded sleeve; nothing above d 84, so nothing crosses the elbow crease; the elbow carries its own pad.
SLEEVE_D, SLEEVE_T = (84.0, 258.0), 2.5   # round 10: 4 -> 2.5 and the foam 4 -> 3 (critics r9 m4, m15, D5, D6:
                                          # the guards a cone or drum with air round the wrist: 9 mm of padding under
                                          # every plate; a real guard's liner is about 5-6 mm)
SLEEVE_FLEX_EXTRA = 40.0      # the sleeve's proximal edge 40 mm lower on the flexor side (clears the fold)
GUARD_FOAM = 3.0
# built distal first, the proximal plate laps over the next with a flared lip
# (name, d range, arc deg, wall, unused, edge curve mm: the proximal edge recedes this much at the plate's sides)
# round 9 (critics r8 m13, m25: from the hero camera the right guard read as a short cuff at the elbow, the forearm's
# camera-facing side bare under a long glove cuff): the arcs widened to 210 / 200 deg (160 / 150), so the shell wraps
# both sides of the forearm down to the (now 30 mm) glove cuff
# round 10 (m4, m13, m15, m27, D5, D6: a cone with a stack of wrist rings, a flared drum): two dorsal shells, as
# drawn (a long upper plate and a lower plate to the glove cuff, ref/zoom_armour_lguard_x10), each hugging the
# tapering forearm (StraightSurf hug: the line is the upper hull of the samples, not one raised over the fattest),
# on thinner padding, so the guard tapers from the elbow to the wrist; a third plate (tried first) read as rings
GUARD = [("Lower", (178.0, 256.0), 160.0, 2.5, "lowerarm02", 8.0),
         ("Main", (96.0, 186.0), 176.0, 3.0, "lowerarm01", 26.0)]
GUARD_ARC_R = {"Main": 172.0, "Lower": 160.0}   # the right arm (round 9: wider arcs put the main shell into the
                                                # carbine's stock, which lies along the right forearm)
GUARD_STRAP_W = 25.0
GUARD_STRAP_D = (128.0, 222.0)   # strap centres: on the upper and the lower shell
# Elbow pad (round 6; the reference has one on the left elbow, m22): a domed hard cap on the point of the elbow
# over a neoprene base, held by straps round the upper arm and the forearm; the cap rides the skin's weights there
ELBOW_PAD = {"w": 76.0, "h": 88.0, "pad": 5.0, "base_t": 4.0, "t": 3.0, "lat": 0.35, "strap_up": 52.0,
             "strap_dn": 74.0, "strap_w": 18.0, "dome": 13.0}
# round 9 (critics r8 m5, all three: "a thin disc edge-on off the elbow"): the cap and its padded base domed 13 mm over
# the point of the elbow (a moulded cup about 20 mm deep with the base), 76 x 88 (was 70 x 80, flat on the skin)
# Knee pad: unrolled octagon (u across, + lateral; v up), round 6: a faceted domed cap 150 x 164 (was 160 x 190
# in two lames, a tall flat plate whose upper lame gaped) with a flat central plate, on a padded base 12 larger
# Round 9 (critics r8 m3, all three: "soft black pillows"; ref/zoom_armour_rknee_x8): a tall faceted shield,
# 156 x 184 (take 1 measured 160 x 190), narrowing in steps to the bottom, crisp facets (softmin k 0.02, was 0.05)
# rising 26 mm to the central plate, a 12 mm tan frame standing 3.2 mm over the recessed centre (was 2), the black
# base showing 7 mm round it (was 12)
# Round 10 (critics r9 m14, m25, m37, D4, D21: oversized, boxy, glossy, smeared highlights; the drawn cap narrower,
# faceted, with a domed patella and a tan rim): 156 x 184 -> 132 x 176, the facets rising 18 mm (26) to the central
# plate with a 7 mm patella dome on it (KNEE_PATELLA), the side lift 16 -> 8 mm, crisper facets (k 0.012)
KNEE_HW, KNEE_HH = 66.0, 88.0
KNEE_BASE_T, KNEE_CAP_T, KNEE_DOME = 6.0, 4.5, 18.0
KNEE_K, KNEE_RECESS, KNEE_MB = 0.012, 3.0, 6.0
KNEE_PATELLA = 7.0            # round 10: a dome over the patella on the central plate (mm at its centre)
KNEE_FLAT = 8.0               # round 9: the sides lifted (u / hw)^2 x this off the knee pocket, so the cap is a flatter
                              # shell over a thicker foam base and stops wrapping the knee like a tube (the "pillow")
KNEE_FACET = (26.0, 24.0, 32.0)   # the facets' runs (mm) from the outline to the central plate: sides, top, bottom
KNEE_BASE_OFF = 1.6           # over the trousers' knee pocket
KNEE_DZ = -12.0               # cap centre relative to the knee joint (the pocket's centre)



def octagon_hw(v, hw=KNEE_HW, hh=KNEE_HH, lo=(32.0, 40.0), hi=(44.0, 20.0)):
    """Half width of the knee cap's octagon at height v (centre 0): bottom edge lo[0] wide rising over
    lo[1] to the full width, top edge hi[0] over hi[1]."""
    if v < -hh + lo[1]:
        t = (v + hh) / lo[1]
        return lo[0] + (hw - lo[0]) * max(0.0, min(1.0, t))
    if v > hh - hi[1]:
        t = (hh - v) / hi[1]
        return hi[0] + (hw - hi[0]) * max(0.0, min(1.0, t))
    return hw


Field, LimbSurf, numeric_normal = G.Field, G.LimbSurf, G.numeric_normal


class CapSurf:
    """The shoulder cap's surface: directions from the shoulder joint g, gnomonic about the centre direction
    c with e1 across (front-back) and e2 down the arm; P(p, q) = g + dir (R + off). Round 10: dome(p, q) mm is
    added to the radius (a domed shell rather than one that only follows the shoulder), and a ray that starts
    inside something (its hit at the ray's start, rmax) is dropped instead of read as a 240 mm radius."""

    def __init__(self, under, g, c, e1, e2, p_rng, q_rng, n=30, rmax=240.0, smooth=10, dome=None):
        self.g, self.c, self.e1, self.e2 = np.asarray(g, float), c, e1, e2
        ps = np.linspace(p_rng[0], p_rng[1], n)
        qs = np.linspace(q_rng[0], q_rng[1], n)
        raw = np.full((n, n), np.nan)
        for j, q in enumerate(qs):
            for i, p in enumerate(ps):
                dr = self.dirv(p, q)
                hit, _n = under.hit(self.g + dr * rmax, -dr, rmax)
                if hit is not None:
                    raw[j, i] = float(np.dot(hit - self.g, dr))
        raw[raw > rmax - 3.0] = np.nan
        self.raw = raw
        self.F = Field(raw, ps, qs, smooth)
        self.dome = dome

    def dirv(self, p, q):
        return G.unit(self.c + math.tan(p) * self.e1 + math.tan(q) * self.e2)

    def point(self, p, q, off):
        d = self.dome(p, q) if self.dome is not None else 0.0
        return self.g + self.dirv(p, q) * (self.F(p, q) + off + d)

    def surf(self, off):
        def f(u, v):
            p = self.point(u, v, off)
            n = numeric_normal(lambda uu, vv: self.point(uu, vv, off), u, v, self.dirv(u, v))
            return p, n
        return f


class StraightSurf:
    """A straight (ruled) shell surface round the forearm: for each angle theta (from e0 toward e1) the radius
    is a straight line in s, fitted to the outermost clothed samples over [s0, s1] and raised until no sample
    lies outside it; the line coefficients are smoothed round theta (and the bound re-applied). u is arc mm at
    the nominal radius r_nom, v = s."""

    def __init__(self, under, a, d, e0, e1, s0, s1, nth=72, ns=16, rmax=200.0, hug=False):
        self.a, self.d, self.e0, self.e1 = np.asarray(a, float), d, e0, e1
        ths = np.linspace(-math.pi, math.pi, nth, endpoint=False)
        ss = np.linspace(s0, s1, ns)
        raw = np.array([[G.limb_radius(under, a, d, e0, e1, s, t, rmax, True)[0] for t in ths] for s in ss])
        raw = G.fill_nan(raw)
        A = np.vstack([np.ones(ns), ss]).T
        coef, *_ = np.linalg.lstsq(A, raw, rcond=None)          # (2, nth)
        if hug:
            # round 10: per angle, the line of least area above every sample (the upper hull's edge over the middle
            # of the range), so a plate tapers with the forearm instead of keeping the least-squares slope raised
            # over the fattest sample (the round-9 guards stood off the wrist: "air round the glove cuff")
            sm = 0.5 * (s0 + s1)
            for j in range(nth):
                H = []
                for x, y in zip(ss, raw[:, j]):
                    while len(H) >= 2 and (H[-1][0] - H[-2][0]) * (y - H[-2][1]) - (H[-1][1] - H[-2][1]) * (x - H[-2][0]) >= 0:
                        H.pop()
                    H.append((x, y))
                for (x0, y0), (x1, y1) in zip(H[:-1], H[1:]):
                    if x0 <= sm <= x1:
                        k = (y1 - y0) / max(x1 - x0, 1e-9)
                        coef[:, j] = (y0 - k * x0, k)
                        break
        for _ in range(3):
            coef[0] += np.max(raw - A @ coef, axis=0)
            # smooth round theta (circular), slopes and intercepts alike
            coef = 0.5 * coef + 0.25 * (np.roll(coef, 1, 1) + np.roll(coef, -1, 1))
        coef[0] += np.maximum(0.0, np.max(raw - A @ coef, axis=0))
        self.ths, self.coef, self.s0, self.s1 = ths, coef, s0, s1
        self.r_nom = float(np.mean(A @ coef))

    def radius(self, th, s):
        th = (th + math.pi) % (2 * math.pi) - math.pi
        c0 = np.interp(th, np.append(self.ths, math.pi), np.append(self.coef[0], self.coef[0][0]))
        c1 = np.interp(th, np.append(self.ths, math.pi), np.append(self.coef[1], self.coef[1][0]))
        return c0 + c1 * s

    def dirv(self, th):
        return math.cos(th) * self.e0 + math.sin(th) * self.e1

    def point(self, th, s, off):
        return self.a + self.d * s + self.dirv(th) * (self.radius(th, s) + off)

    def surf(self, off):
        r = self.r_nom

        def f(u, v):
            p = self.point(u / r, v, off)
            n = numeric_normal(lambda uu, vv: self.point(uu / r, vv, off), u, v, self.dirv(u / r))
            return p, n
        return f


def plate_t(wall, half_u, v0, v1, rib=False, grooves=False, bead=0.9):
    """Thickness field of a moulded plate over (u arc mm in [-half_u, half_u], v in [v0, v1]): rolled rim bead
    all round; optionally a central rib (14 wide, 2.5 proud, 45 deg flanks, ends rounded 7 mm from the
    plate's ends) and two grooves 1.2 deep at +-22 mm."""
    def f(u, v):
        e = min(half_u - abs(u), v - v0, v1 - v)
        t = wall + G.edge_profile(e, bead)
        if rib:
            end = min(v - v0, v1 - v) - 8.0
            if end > 0:
                h = 2.5 * G.smoothstep(end, 0.0, 7.0)
                t += h * (1.0 - G.smoothstep(abs(u), 7.0, 9.5))
        if grooves:   # round 10: shallower, softer (1.2 deep over 1.2 mm walls read as edges: pale worn flutes)
            for g0 in (-22.0, 22.0):
                if min(v - v0, v1 - v) > 12.0:
                    t -= 0.8 * (1.0 - G.smoothstep(abs(u - g0), 1.5, 4.5))
        return t
    return f


def main(render=True):
    import bpy
    body, rig = C.open_base()
    bd = C.body_data(body)
    clothing = G.load_clothing(rig)
    under_a, note_a = G.clothing_under(bd, clothing, "arm")
    under_t, _note_t = G.clothing_under(bd, clothing, "torso")
    under_l, note_l = G.clothing_under(bd, clothing, "leg")
    under_fa = G.Under(list(under_a.layers) + ([(G.objects_bvh(list(clothing["gloves"].all_objects)), 0.8)]
                                               if "gloves" in clothing else []))
    # the carrier's shoulder-strap pads: the cap lies over them (as drawn), clear by CAP_STRAP_CLEAR
    strap_layer, note_c = [], "no carrier cache"
    carrier = None
    if os.path.exists(os.path.join(C.PARTS_DIR, "carrier.blend")):
        carrier = C.load_part("carrier", rig)
        straps = [o for o in carrier.all_objects if o.type == "MESH" and o.name.startswith("Carrier.Strap.")]
        if straps:
            strap_layer = [(G.objects_bvh(straps), CAP_STRAP_CLEAR - CAP_PAD)]
            note_c = f"cap clears {len(straps)} carrier strap objects by {CAP_STRAP_CLEAR} mm"
    G.say("arm surface:", note_a, "| leg surface:", note_l, "|", note_c)
    coll = C.part_collection(PART)
    M = {k: G.mat(f"Armour.Mat.{k.title().replace('_', '')}", v) for k, v in COL.items()}
    out = {"under": {"arm": note_a, "leg": note_l, "carrier": note_c}}
    rigid = []      # (object, bone)
    soft = []       # (object, collapse map or None)
    mounts = []     # round 6: (object, rest point mm): mounted on the skin there (gear_common.mount_bind on Body.Mesh)
    buckles = []    # round 10: (buckle, its strap's name, rest point mm, outward): moved with the strap by posed_clear

    for side, sgn in (("L", 1.0), ("R", -1.0)):
        S = {}
        gh = C.bone_mm(f"upperarm01.{side}")
        el = C.bone_mm(f"lowerarm01.{side}")
        wr = C.bone_mm(f"wrist.{side}")
        d_up, f_up, l_up = G.limb_frame(gh, el, side)

        # ------------------------------------------------ tiers 2 and 3 around the upper arm (first: the cap laps over)
        arm = LimbSurf(under_a, gh, d_up, l_up, f_up, (-math.pi, math.pi), (60.0, 280.0), nth=48, ns=24, iters=6,
                       outward=True)
        r2 = float(np.mean([arm.F(0.0, s) for s in TIER2_S])) + SHELL_PAD
        half2 = TIER2_ARC / 2.0
        t2_v0, t2_v1 = TIER2_S

        def hw2(v, h=half2):
            # round 10: the long outer-arm plate's lower corners chamfered TIER2_CHAMFER at 45 deg
            return h - max(0.0, TIER2_CHAMFER - (t2_v1 - v))

        def t2_field(u, v):
            e = min(hw2(v) - abs(u), v - t2_v0, t2_v1 - v)
            t = CAP_T + G.edge_profile(e, 0.9)
            # round 10: no recessed panel (round 2-9: 70 x 28, 1.5 deep): its rim's wear drew a pale square outline on
            # the plate, "a pale square patch" (critic m31), and ramped over 5 mm it still did
            # round 10: two vent slots 6 x 18 along the rear edge below the strap (the drawn plate's dark slots)
            ur = -hw2(v) + 11.0
            for vk in (t2_v0 + 118.0, t2_v0 + 140.0):            # below the strap
                if abs(u - ur) < 4.0 and abs(v - vk) < 10.0:
                    t -= 1.4 * (1.0 - G.smoothstep(abs(u - ur), 2.2, 3.4)) * (1.0 - G.smoothstep(abs(v - vk), 7.5, 9.5))
            return t
        ob = G.slab(f"Pauldron.{side}.Tier2.Plate", coll, arm.surf(SHELL_PAD, r0=r2), lambda v: (-hw2(v), hw2(v)),
                    t2_v0, t2_v1, CAP_T, M["shell"], nu=52, nv=72, bevel_mm=0.8, t_field_fn=t2_field)
        rigid.append((ob, f"upperarm01.{side}"))
        tier2 = ob
        # round 6: the foam liner under the plate (fills the stand-off)
        ob = G.slab(f"Pauldron.{side}.Tier2.Foam", coll, arm.surf(SHELL_PAD - SHELL_FOAM + 0.2, r0=r2),
                    lambda v: (-hw2(v) + 4.0, hw2(v) - 4.0), t2_v0 + 4.0, t2_v1 - 4.0, SHELL_FOAM - 0.4, M["foam"],
                    nu=24, nv=16, bevel_mm=1.0)
        rigid.append((ob, f"upperarm01.{side}"))
        h2r = half2 / r2
        # round 10: round 6's elastic strap round the inner arm at mid tier 2 is gone: the Tier3 strap below holds the
        # long plate (one ring fewer on the arm, critics r9 m8, m20)
        if side == "L":
            # IR strobe 30 x 45 x 18 on the plate's outer face, toward its rear edge (as drawn)
            th = -0.5 * half2 / r2
            sm = t2_v0 + 46.0
            p = arm.point(th, sm, SHELL_PAD + CAP_T + 0.4)
            n = arm.dirv(th)
            Ms = G.frame(p + n * 9.0, np.cross(d_up, n) * -1.0, n)
            Ms2 = np.eye(4)
            Ms2[:3, 0], Ms2[:3, 1], Ms2[:3, 2], Ms2[:3, 3] = Ms[:3, 0], -d_up, n, Ms[:3, 3]
            ob = G.rbox("Pauldron.L.Tier2.Strobe", coll, (30.0, 45.0, 18.0), Ms2, M["strobe"], bevel_mm=3.0)
            rigid.append((ob, "upperarm01.L"))
        # round 10 (critics r9 m8, m20: the pale moulded bicep bands were the brightest marks on the figure and stood
        # proud of the sleeve): a 38 mm coyote webbing strap round the arm, 0.4 mm over the sleeve, lifted over the
        # long tier-2 plate where it crosses it (the strap holds the plate, as drawn), soft-bound so it follows the
        # sleeve, then cleared of the posed sleeve (posed_clear)
        t3_v0, t3_v1 = TIER3_S
        over = SHELL_PAD + CAP_T + 0.9 + 0.5

        def st_lift(th, v):
            th = (th + math.pi) % (2 * math.pi) - math.pi
            a = hw2(v) / r2
            return 0.4 + over * G.smoothstep(a + 0.14 - abs(th), 0.0, 0.14)

        def st_point(th, v, off=0.0):
            return arm.point(th, v, st_lift(th, v) + off)

        def st_surf(u, v):
            return st_point(u, v), G.numeric_normal(lambda uu, vv: st_point(uu, vv), u, v, arm.dirv(u), h=0.01)
        if side == "R":
            # the right arm is pressed to the body in the hero pose: a full ring went 2-3 mm into the torso and the
            # shirt at the armpit (as round 9's tier-2 strap did), so the right strap leaves out the medial 100 deg
            # (its ends lie in the armpit's fold)
            ob = G.slab(f"Pauldron.{side}.Tier3.Strap", coll, st_surf, lambda v: (-(math.pi - 0.87), math.pi - 0.87),
                        t3_v0, t3_v1, 1.6, M["band"], nu=80, nv=5, bevel_mm=0.5)
        else:
            ob = G.slab(f"Pauldron.{side}.Tier3.Strap", coll, st_surf, None, t3_v0, t3_v1, 1.6, M["band"], nu=96, nv=5,
                        bevel_mm=0.5, closed_u=True)
        soft.append((ob, None))
        # the strap's flat ladder-lock on the front of the arm, in front of the plate (round 6's position)
        th_b = h2r + 0.32                                     # +theta is toward the front (e1 = f_up)
        sb = 0.5 * (t3_v0 + t3_v1)
        pb_ = st_point(th_b, sb, 1.6 + 0.3)
        nb = arm.dirv(th_b)
        ob = G.hw_object(f"Pauldron.{side}.Tier3.Buckle", coll, GH.ladder_lock(44.0, 26.0, 3.0, 2.6, 2),
                         G.frame(pb_ + nb * 1.3, -d_up, nb), M["metal"])
        buckles.append((ob, f"Pauldron.{side}.Tier3.Strap", pb_, nb))     # mounted on its strap after posed_clear
        S["tier2_radius_mm"] = round(r2, 1)

        # ------------------------------------------------ pauldron tier 1: the cap, on the outside of the shoulder
        up = np.array([0.0, 0.0, 1.0])
        c = G.unit(CAP_UP[side] * up + d_up + CAP_FWD[side] * f_up)     # over the deltoid, on the outside
        e1 = G.unit(f_up - c * np.dot(f_up, c))    # across: toward the front
        e2 = G.unit(d_up - c * np.dot(d_up, c))    # down the arm
        qa, qb = math.radians(CAP_Q[0]), math.radians(CAP_Q[1])
        pw = math.radians(60.0)
        under_cap = G.Under(list(under_a.layers) + list(under_t.layers) + strap_layer +
                            [(G.objects_bvh([tier2]), 1.5 - CAP_PAD)])
        qm, qh = 0.5 * (qa + qb), 0.5 * (qb - qa)

        def cap_dome(p, q, pw_=math.radians(40.0)):
            # round 10 (m31: "a domed shell"): CAP_DOME mm at the centre, 0 at the cap's outline
            x, y = min(1.0, abs(p) / pw_), min(1.0, abs(q - qm) / qh)
            return CAP_DOME * (1.0 - x * x) * (1.0 - y * y)
        cap = CapSurf(under_cap, gh, c, e1, e2, (-pw, pw), (qa - 0.05, qb + 0.05), smooth=CAP_SMOOTH, dome=cap_dome)
        S["cap_raw_mm"] = [round(float(x), 1) for x in np.nanpercentile(cap.raw, (0, 50, 100))]
        r_cap = float(np.nanmean(cap.F.R)) + CAP_PAD

        def cap_hw(q, r=r_cap):
            t = (q - qa) / (qb - qa)
            w = CAP_W_TOP + (CAP_W_BOT - CAP_W_TOP) * t
            ch = max(0.0, 28.0 - (qb - q) * r)           # lower corners chamfered 28 at 45 deg
            ct = max(0.0, 14.0 - (q - qa) * r)           # upper corners rounded off 14
            return (w / 2.0 - ch - ct) / r

        def cap_field(p, q, r=r_cap):
            e = min((cap_hw(q) - abs(p)) * r, (q - qa) * r, (qb - q) * r)
            return CAP_T + G.edge_profile(e, 1.1, 4.0, 2.0)
        ob = G.slab(f"Pauldron.{side}.Tier1.Cap", coll, cap.surf(CAP_PAD), lambda q: (-cap_hw(q), cap_hw(q)), qa, qb,
                    CAP_T, M["shell"], nu=60, nv=70, bevel_mm=0.8, t_field_fn=cap_field)
        rigid.append((ob, f"upperarm01.{side}"))
        # round 6: the foam liner under the cap
        ins = 5.0 / r_cap
        ob = G.slab(f"Pauldron.{side}.Tier1.Foam", coll, cap.surf(CAP_PAD - CAP_FOAM + 0.2),
                    lambda q: (-cap_hw(q) + ins, cap_hw(q) - ins), qa + ins, qb - ins, CAP_FOAM - 0.4, M["foam"],
                    nu=30, nv=30, bevel_mm=1.2)
        rigid.append((ob, f"upperarm01.{side}"))
        # round 9: the webbing link up over the strap pad is gone (critic r8 m31: it rose off the shoulder top as a
        # stray spike in the clay; the cap is rigid on the arm bone and needs no visible link)
        # two dome rivets (the drawn studs): on the top facet and low on the outer face
        for k, (pp, qq) in enumerate(((0.12, qa + 0.25 * (qb - qa)), (-0.06, qb - 16.0 / r_cap))):
            pt, nt = cap.surf(CAP_PAD + CAP_T + 0.1)(pp, qq)
            ob = G.hw_object(f"Pauldron.{side}.Tier1.Rivet.{k + 1}", coll, GH.rivet(7.0, 2.2), G.frame(pt, e1, nt),
                             M["metal"])
            rigid.append((ob, f"upperarm01.{side}"))
        S["cap_radius_mm"] = round(r_cap, 1)
        if side == "L":
            # the emblem: a rounded-square plate 1 mm proud on the cap's outer face, centred low on the cap.
            # Round 8 (critic m34): EMBLEM_W x EMBLEM_H with corners of EMBLEM_R, as drawn
            # (ref/zoom_armour_emblem_x16); it was a 50 x 95 shield tapering to a point, which with R003's
            # triangle outline read as "a pointed V or crown tab"
            qe = qa + (qb - qa) * 0.60
            r_emb = r_cap + CAP_PAD + CAP_T + 1.4      # the plate's own radius (round 8: r_cap made it 80 mm tall)
            he = 0.5 * EMBLEM_H / r_emb

            def emb_hw(q, r=r_cap, q0=qe - he, q1=qe + he, re=r_emb):
                d = min(q - q0, q1 - q) * re           # mm from the nearer end (top or bottom edge)
                k = EMBLEM_R - min(max(d, 0.0), EMBLEM_R)
                return (0.5 * EMBLEM_W - EMBLEM_R + float(np.sqrt(max(EMBLEM_R ** 2 - k ** 2, 0.0)))) / r
            ob = G.slab("Pauldron.L.Tier1.Emblem", coll, cap.surf(CAP_PAD + CAP_T + 1.4),
                        lambda q: (-emb_hw(q), emb_hw(q)), qe - he, qe + he, 1.0, M["emblem"], nu=10, nv=18,
                        bevel_mm=0.4)
            S["emblem_decal_uv"] = decal_uv(ob)
            rigid.append((ob, "upperarm01.L"))

        # ------------------------------------------------ forearm guard
        d_fa, f_fa, l_fa = G.limb_frame(el, wr, side)
        t_rad = G.unit(C.bone_mm(f"finger2-1.{side}") - C.bone_mm(f"finger5-1.{side}"))
        dors = np.cross(t_rad, d_fa) if side == "L" else np.cross(d_fa, t_rad)
        dors = G.unit(dors - d_fa * np.dot(dors, d_fa))
        e1f = G.unit(np.cross(d_fa, dors))
        fa = LimbSurf(under_fa, el, d_fa, dors, e1f, (-math.pi, math.pi), (40.0, 270.0), nth=48, ns=26, iters=4,
                      outward=True)
        sl_surf = fa.surf(0.5)

        def sleeve_surf(u, v):
            d0 = SLEEVE_D[0] + SLEEVE_FLEX_EXTRA * 0.5 * (1.0 - math.cos(u))     # dorsal 52 .. flexor 92
            return sl_surf(u, d0 + v * (SLEEVE_D[1] - d0))
        collapse = {f"upperarm01.{side}": f"lowerarm01.{side}", f"upperarm02.{side}": f"lowerarm01.{side}"}
        ob = G.slab(f"Guard.{side}.Sleeve", coll, sleeve_surf, None, 0.0, 1.0, SLEEVE_T, M["black"], nu=48, nv=20,
                    bevel_mm=1.0, closed_u=True)
        soft.append((ob, collapse))
        base_off = 0.5 + SLEEVE_T + GUARD_FOAM + 0.5
        built = {}          # name -> (StraightSurf, offset fn, wall, half arc mm, d range) of the plates built so far
        S["guard"] = {}
        for k, drng, arc, wall, bone, curve in GUARD:
            arc = GUARD_ARC_R.get(k, arc) if side == "R" else arc
            ss = StraightSurf(under_fa, el, d_fa, dors, e1f, drng[0] - 4.0, drng[1] + 4.0, hug=True)
            half = math.radians(arc / 2.0) * ss.r_nom
            # lap over the plate below (built before) with a flared lip: the plate keeps base_off and only its
            # distal end rises, over 10 mm, to clear the lower plate's outer face, bead and 0.7 mm
            lo, extra = drng[1], 0.0
            for (s2, off2, wall2, half2_, d2) in built.values():
                lo_, hi_ = max(drng[0], d2[0]), min(drng[1], d2[1])
                if hi_ <= lo_:
                    continue
                lo = min(lo, lo_)
                for sv in np.linspace(lo_, hi_, 6):
                    for u in np.linspace(-half2_, half2_, 25):
                        th = u / s2.r_nom
                        extra = max(extra, s2.radius(th, sv) + off2(sv) + wall2 + 0.9 + 0.7 - ss.radius(th, sv)
                                    - base_off)

            def offf(v, lo=lo, extra=extra):
                return base_off + extra * G.smoothstep(v, lo - 10.0, lo)

            def dmap(u, w, drng=drng, half=half, curve=curve):
                d0 = drng[0] + curve * (u / half) ** 2          # the elbow band's edge recedes at its sides
                return d0 + w * (drng[1] - d0)

            def psurf(u, w, ss=ss, offf=offf, dmap=dmap):
                r = ss.r_nom

                def f(uu, ww):
                    d = dmap(uu, ww)
                    return ss.point(uu / r, d, offf(d))
                return f(u, w), numeric_normal(f, u, w, ss.dirv(u / r), h=0.02)

            rib = k in ("Main", "Lower")
            tf = plate_t(wall, half, drng[0], drng[1], rib=rib, grooves=rib)

            def tfield(u, w, tf=tf, dmap=dmap, drng=drng, half=half, curve=curve):
                d0 = drng[0] + curve * (u / half) ** 2
                return tf(u, dmap(u, w) - d0 + drng[0])
            ob = G.slab(f"Guard.{side}.{k}", coll, psurf, lambda w, h=half: (-h, h), 0.0, 1.0, wall, M["shell"],
                        nu=max(40, int(2 * half / 2.2)), nv=max(10, int((drng[1] - drng[0]) / 2.2)), bevel_mm=0.7,
                        t_field_fn=tfield)
            mid = el + d_fa * (0.5 * (drng[0] + drng[1]))
            hit, _n = under_fa.hit(mid + dors * 200.0, -dors, 200.0)
            gpt = hit if hit is not None else mid
            mounts.append((ob, gpt))
            # foam under the plate: a dark step under its lip
            hf = half - 4.0

            def fsurf(u, w, ss=ss, dmap=dmap):
                r = ss.r_nom

                def f(uu, ww):
                    return ss.point(uu / r, dmap(uu, ww), base_off - GUARD_FOAM + 0.2)
                return f(u, w), numeric_normal(f, u, w, ss.dirv(u / r), h=0.02)
            ob = G.slab(f"Guard.{side}.{k}.Foam", coll, fsurf, lambda w, h=hf: (-h, h), 0.06, 0.94, GUARD_FOAM - 0.4,
                        M["foam"], nu=20, nv=6, bevel_mm=1.0)
            mounts.append((ob, gpt))
            built[k] = (ss, offf, wall, half, drng)
            S["guard"][k] = {"d": list(drng), "arc_deg": arc, "lip_lift_mm": round(extra, 1),
                             "r_nom": round(ss.r_nom, 1)}
        # the two straps: 25 mm webbing round the flexor side over the sleeve, below the elbow fold (the upper
        # one under the upper plate's edges, the lower one on the wrist band), each through a ladder-lock
        # riveted on the plate's edge
        for k, dm in (("Main", GUARD_STRAP_D[0]), ("Lower", GUARD_STRAP_D[1])):
            ss, offf, wall, half, drng = built[k]
            th_e = half / ss.r_nom
            ring = fa.surf(0.5 + SLEEVE_T + 0.3)
            ob = G.slab(f"Guard.{side}.Strap.{k}", coll, ring, lambda v, a=th_e: (a - 0.15, 2 * math.pi - a + 0.15),
                        dm - GUARD_STRAP_W / 2.0, dm + GUARD_STRAP_W / 2.0, 1.4, M["black"], nu=40, nv=4,
                        bevel_mm=0.4)
            soft.append((ob, collapse))
            r = ss.r_nom
            ul = half - 14.0

            def fo(uu, vv, ss=ss, offf=offf, wall=wall, r=r):
                return ss.point(uu / r, vv, offf(vv) + wall)
            pl = fo(ul, dm)
            nl = numeric_normal(fo, ul, dm, ss.dirv(ul / r))
            ob = G.hw_object(f"Guard.{side}.Strap.{k}.LadderLock", coll, GH.ladder_lock(32.0, 26.0, 3.0, 3.0, 2),
                             G.frame(pl + nl * 0.4, d_fa, nl), M["metal"])
            mounts.append((ob, pl))
        S["sleeve_d"] = [SLEEVE_D[0], SLEEVE_D[0] + SLEEVE_FLEX_EXTRA, SLEEVE_D[1]]

        # ------------------------------------------------ round 6: elbow pad (replaces round 1's fin and pad chips)
        E = ELBOW_PAD
        post = G.unit(-f_up + E["lat"] * l_up)               # the point of the elbow, a little to the outside
        post = G.unit(post - d_up * np.dot(post, d_up))
        e1e = G.unit(np.cross(d_up, post))
        under_e = G.Under(list(under_a.layers))
        ecap = CapSurf(under_e, el, post, e1e, d_up, (-1.05, 1.05), (-1.05, 1.05), n=28, smooth=4)
        r_e = float(np.nanmean(ecap.F.R))
        hw_e, hh_e = E["w"] / 2.0 / (r_e + E["pad"]), E["h"] / 2.0 / (r_e + E["pad"])

        def e_hw(q, hw=hw_e, hh=hh_e):
            t = abs(q) / hh
            return hw * math.sqrt(max(0.0, 1.0 - max(0.0, t - 0.55) ** 2 / 0.45 ** 2 * 0.6))

        def e_dome(p, q):
            rr = min(1.0, math.hypot(p / max(e_hw(q), 1e-6), q / hh_e))
            return E["dome"] * (1.0 - rr * rr) ** 0.7

        def e_surf(off, domed=True):
            def f(p, q):
                h = e_dome(p, q) if domed else 0.0
                pt = ecap.point(p, q, off + h)
                n = numeric_normal(lambda uu, vv: ecap.point(uu, vv, off + (e_dome(uu, vv) if domed else 0.0)), p, q,
                                   ecap.dirv(p, q))
                return pt, n
            return f

        def e_field(p, q, r=r_e + E["pad"]):
            e = min((e_hw(q) - abs(p)) * r, (hh_e - abs(q)) * r)
            return E["t"] + G.edge_profile(e, 1.0, 3.0, 1.5) - 1.2 * G.smoothstep(e, 10.0, 12.0)
        # soft-bound, both: a cap mounted as one piece on the elbow skin rotated with half the 107 deg fold and stood
        # off the flexed right elbow at its ends (first try of round 6); per-vertex weights let it wrap the point
        # round 9: the base is the foam under the dome: from the skin up to the cap's underside (no void)
        ob = G.slab(f"ElbowPad.{side}.Base", coll, e_surf(0.6, domed=False), lambda q: (-e_hw(q) - 0.08, e_hw(q) + 0.08),
                    -hh_e - 0.08, hh_e + 0.08, E["base_t"], M["black"], nu=20, nv=22, bevel_mm=1.5,
                    t_field_fn=lambda p, q: E["base_t"] + e_dome(p, q))
        soft.append((ob, None))
        ob = G.slab(f"ElbowPad.{side}.Cap", coll, e_surf(0.6 + E["base_t"] + 0.3), lambda q: (-e_hw(q), e_hw(q)),
                    -hh_e, hh_e, E["t"], M["shell"], nu=40, nv=44, bevel_mm=0.7, t_field_fn=e_field)
        soft.append((ob, None))
        # the straps: round the upper arm above the joint and round the forearm below it
        for nm_s, a0, dd, s_c, coll_map in (("Up", gh, d_up, float(np.dot(el - gh, d_up)) - E["strap_up"],
                                             {f"lowerarm01.{side}": f"upperarm02.{side}"}),
                                            ("Down", el, d_fa, E["strap_dn"],
                                             {f"upperarm01.{side}": f"lowerarm01.{side}", f"upperarm02.{side}": f"lowerarm01.{side}"})):
            fr = G.limb_frame(a0, a0 + dd * 100.0, side)
            ring = LimbSurf(under_a, a0, dd, fr[1], fr[2], (-math.pi, math.pi), (s_c - 16.0, s_c + 16.0), nth=48,
                            ns=6, iters=3, outward=True)
            # on the flexed right arm the upper strap leaves out the front of the elbow (the crease, where the biceps
            # meets the forearm: a full ring there went 13 mm into the shirt): it runs round the back and sides only
            # and its ends lie in the fold; on the left arm, whose front shows, it stays a full ring
            if nm_s == "Up" and side == "R":
                ob = G.slab(f"ElbowPad.{side}.Strap.{nm_s}", coll, ring.surf(0.6), lambda v: (math.pi - 2.2, math.pi + 2.2),
                            s_c - E["strap_w"] / 2.0, s_c + E["strap_w"] / 2.0, 1.6, M["black"], nu=40, nv=3,
                            bevel_mm=0.4)
            else:
                ob = G.slab(f"ElbowPad.{side}.Strap.{nm_s}", coll, ring.surf(0.6), lambda v: (-math.pi, math.pi),
                            s_c - E["strap_w"] / 2.0, s_c + E["strap_w"] / 2.0, 1.6, M["black"], nu=48, nv=3,
                            bevel_mm=0.4, closed_u=True)
            soft.append((ob, coll_map))
        S["elbow_pad_radius_mm"] = round(r_e, 1)

        # ------------------------------------------------ knee pad: padded base, domed main cap, upper lame
        kn = C.bone_mm(f"lowerleg01.{side}")
        top = C.bone_mm(f"upperleg02.{side}")
        bot = C.bone_mm(f"lowerleg02.{side}")
        d_k, f_k, l_k = G.limb_frame(top, bot, side)
        s_kn = float(np.dot(kn - top, d_k))
        leg = LimbSurf(under_l, top, d_k, f_k, l_k, (-1.6, 1.6), (s_kn - 150.0, s_kn + 150.0), nth=36, ns=30,
                       iters=6)
        r_k = float(leg.F(0.0, s_kn)) + 2.0
        sc = s_kn - KNEE_DZ     # v up = -s; the cap centre KNEE_DZ (negative = below) from the joint

        def dome(u, v):
            # round 6: a faceted dome: planar ramps from the outline up to a flat central plate (the drawn cap's
            # facets), the edges between facets softened over 3 mm
            es = max(0.0, octagon_hw(v) - abs(u)) / KNEE_FACET[0]
            et = max(0.0, KNEE_HH - v) / KNEE_FACET[1]
            eb = max(0.0, v + KNEE_HH) / KNEE_FACET[2]
            k = KNEE_K
            m = -k * math.log(math.exp(-es / k) + math.exp(-et / k) + math.exp(-eb / k) + math.exp(-1.0 / k))
            # round 10: the patella dome on the central plate (a rounded rise, 0 where the facets begin)
            pr = math.hypot(u / max(octagon_hw(v) - KNEE_FACET[0], 10.0), v / (KNEE_HH - 28.0))
            pat = KNEE_PATELLA * max(0.0, 1.0 - pr * pr) ** 1.5
            return KNEE_DOME * max(0.0, m) + pat + KNEE_FLAT * min(1.0, abs(u) / KNEE_HW) ** 2

        def kvs(off, domed=False):
            base_f = leg.surf(off, r0=r_k)

            def f(u, v):
                p, n = base_f(u, sc - v)
                if domed:
                    h = dome(u, v)
                    p = p + n * h
                    # normal of the domed surface, numerically
                    n = numeric_normal(lambda uu, vv: base_f(uu, sc - vv)[0] + base_f(uu, sc - vv)[1] * dome(uu, vv),
                                       u, v, n)
                return p, n
            return f

        def knee_field(v0, v1, wall, ridge=True):
            def f(u, v):
                e = min(octagon_hw(v) - abs(u), v - v0, v1 - v)
                t = wall + G.edge_profile(e, 1.2, 2.5, 1.5)
                t -= KNEE_RECESS * G.smoothstep(e, 11.0, 13.0)         # the centre panel, below the frame
                if ridge and e > 13.5:
                    t += 1.6 * (1.0 - G.smoothstep(abs(u), 4.0, 8.0))  # the moulded centre ridge
                # round 6: the frame's slots (the drawn dark holes): three a side, 18 x 5, 1.6 deep
                if 3.5 < e < 10.0 and abs(u) > octagon_hw(v) - 11.0:
                    for vk in (-40.0, -4.0, 32.0):
                        if abs(v - vk) < 9.0:
                            t -= 1.6 * (1.0 - G.smoothstep(abs(v - vk), 7.0, 9.0)) * G.smoothstep(e, 3.5, 5.0) * \
                                (1.0 - G.smoothstep(e, 8.0, 10.0))
                return t
            return f
        mb = KNEE_MB
        # round 6: the padded base fills the cap's dome (the foam a hard cap sits on), so the cap lies on it
        # round 9: built on the knee pocket itself with the dome as its thickness (the foam fills from the pocket up to
        # the cap, so the lifted sides never leave a gap under the base), easing off over the margin
        def base_t(u, v):
            hw = octagon_hw(max(-KNEE_HH, min(KNEE_HH, v)))
            uc = max(-hw, min(hw, u))
            vc = max(-KNEE_HH, min(KNEE_HH, v))
            out_ = max(abs(u) - hw, abs(v) - KNEE_HH, 0.0)
            return KNEE_BASE_T + dome(uc, vc) * (1.0 - 0.6 * G.smoothstep(out_, 0.0, mb))
        ob = G.slab(f"Kneepad.{side}.Base", coll, kvs(KNEE_BASE_OFF, False),
                    lambda v: (-octagon_hw(v) - mb, octagon_hw(v) + mb), -KNEE_HH - mb, KNEE_HH + mb, KNEE_BASE_T,
                    M["black"], nu=32, nv=34, bevel_mm=3.0, segments=3, t_field_fn=base_t)
        soft.append((ob, None))                    # padded neoprene: follows the knee pocket
        cap_off = KNEE_BASE_OFF + KNEE_BASE_T + 0.8
        v0m, v1m = -KNEE_HH, KNEE_HH
        ob = G.slab(f"Kneepad.{side}.Cap", coll, kvs(cap_off, True), lambda v: (-octagon_hw(v), octagon_hw(v)),
                    v0m, v1m, KNEE_CAP_T, M["knee"], nu=64, nv=60, bevel_mm=0.8,
                    t_field_fn=knee_field(v0m, v1m, KNEE_CAP_T))
        S["cap_frame_share"] = frame_wear(ob, lambda v: (-octagon_hw(v), octagon_hw(v)), v0m, v1m, 64, 60, octagon_hw)
        # round 6: the cap rides the skin's weights at the kneecap (rigid on the shin, the round-5 caps swung off the
        # pocket wherever the knee bent or the shin twisted against the thigh: the right one gaped at the outer knee)
        kpoint, _n = kvs(0.0)(0.0, 0.0)
        mounts.append((ob, kpoint))
        # red tab on the lateral side facet (v 10 in the cap's frame), lying on it
        pt, nt = kvs(cap_off + KNEE_CAP_T + 0.2, True)(KNEE_HW - 9.0, 12.0)
        ob = G.rbox(f"Kneepad.{side}.Tab", coll, (30.0, 14.0, 3.0), G.frame(pt + nt * 1.6, -d_k, nt), M["red"],
                    bevel_mm=1.2)
        mounts.append((ob, kpoint))
        # strap: 38 mm elastic round the back of the knee; ladder-lock and tan tail on the medial side
        ring = LimbSurf(under_l, top, d_k, f_k, l_k, (-math.pi, math.pi), (s_kn - 30.0, s_kn + 40.0), nth=60,
                        ns=8, iters=3)
        th0 = (KNEE_HW + 6.0) / r_k
        s_st = s_kn + 10.0
        ob = G.slab(f"Kneepad.{side}.Strap", coll, ring.surf(1.4), lambda v: (th0, 2 * math.pi - th0 - 0.30),
                    s_st - 19.0, s_st + 19.0, 2.0, M["black"], nu=30, nv=3, bevel_mm=0.5)
        soft.append((ob, None))
        thl = -(th0 + 0.42)          # round 10: on the strap's end (at -(th0 + 0.17) it hung in the gap past it: "floats")
        pl, nl = ring.surf(1.4 + 2.0 + 0.2)(thl, s_st)
        ob = G.hw_object(f"Kneepad.{side}.LadderLock", coll, GH.ladder_lock(50.0, 32.0, 4.0, 3.5, 2),
                         G.frame(pl + nl * 1.8, d_k, nl), M["metal"])
        mounts.append((ob, pl))      # round 6: on its strap (rigid on the shin it stood 6 mm off)
        ob = G.slab(f"Kneepad.{side}.Tail", coll, ring.surf(1.4 + 2.0 + 0.4), lambda v: (thl - 0.62, thl - 0.17),
                    s_st - 18.0, s_st + 18.0, 1.5, M["tan"], nu=10, nv=3, bevel_mm=0.4)
        soft.append((ob, None))
        S["knee_radius_mm"] = round(r_k, 1)
        S["knee_centre_z"] = round(float((top + d_k * sc)[2]), 1)
        out[side] = S

    if carrier is not None:
        for o in list(carrier.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(carrier)

    # ------------------------------------------------ bind
    for ob, bone in rigid:
        G.rigid_bind(ob, rig, bone)
    for ob, collapse in soft:
        G.soft_bind(ob, body, rig, collapse=collapse)
    # round 10 (G1 D1): the arm straps cleared of the posed sleeve (and the upper-arm strap of the posed tier-2 plate)
    sleeve = [o for k in ("shirt", "gloves") if k in clothing for o in clothing[k].all_objects if o.type == "MESH"]
    straps = [ob for ob, _c in soft if ".Strap" in ob.name and not ob.name.startswith("Kneepad.")]
    t2 = [o for o in coll.all_objects if o.name.endswith(".Tier2.Plate")]
    out["mounted"] = {ob.name: G.mount_bind(ob, rig, body, pt, k=8) for ob, pt in mounts}
    out["posed_clear"] = posed_clear([o for o in straps if ".Tier3." in o.name], rig, sleeve + t2, clear=0.8, log=G.say)
    out["posed_clear"].update(posed_clear([o for o in straps if ".Tier3." not in o.name], rig, sleeve, clear=0.8,
                                          log=G.say))
    # and the forearm guard's shells and their foam (mounted, so after mount_bind): in the hero pose the left sleeve
    # bunches at the wrist and stood 6-7 mm through the lower plate (round 9: through the wrist plate)
    plates = [o for o in coll.all_objects if o.name.startswith("Guard.") and o.name.split(".")[2] in ("Main", "Lower")
              and ".Strap" not in o.name]
    out["posed_clear"].update(posed_clear(plates, rig, sleeve, clear=0.8, log=G.say))
    # the upper-arm straps' ladder-locks follow their strap's push (left at the strap's rest place one went 3 mm into the
    # posed sleeve): each moved along its outward direction by the push of the strap's outer face under it (+ 0.8 mm for
    # the flat frame over the strap's curve), then mounted on the strap (its weights there), as the knee locks are
    for bk, sname, p0, n0 in buckles:
        st_ob = bpy.data.objects[sname]
        Vs = np.empty(len(st_ob.data.vertices) * 3)
        st_ob.data.vertices.foreach_get("co", Vs)
        Vs = Vs.reshape(-1, 3)[len(st_ob.data.vertices) // 2:] * 1000.0           # its outer face, mm
        k = int(np.argmin(np.linalg.norm(Vs - p0, axis=1)))
        dz = max(0.0, float((Vs[k] - p0) @ n0) + 0.3) + 0.8                       # p0 was 0.3 over the outer face
        if dz > 0.05:
            Vb = np.empty(len(bk.data.vertices) * 3)
            bk.data.vertices.foreach_get("co", Vb)
            bk.data.vertices.foreach_set("co", (Vb.reshape(-1, 3) + n0 * dz * C.MM).ravel())
            bk.data.update()
        out.setdefault("buckle_lift_mm", {})[bk.name] = round(dz, 1)
        out["mounted"][bk.name] = G.mount_bind(bk, rig, st_ob, p0 + n0 * dz, k=8)
    out["rigid"] = {ob.name: bone for ob, bone in rigid}
    out["soft"] = [ob.name for ob, _c in soft]
    G.say(json.dumps({k: v for k, v in out.items() if k in ("L", "R")}))
    out["materials"] = C.library_pass(coll, PART, MATERIALS, side_dust={"L": 1.0, "R": 0.85}, say_tag=TAG)
    if render:
        rep = G.finish_part(TAG, coll, body, rig, clothing, (0.0, 0.0, 1000.0), 1900.0,
                            ["ref.arm_R", "ref.arm_L", "ref.legs_knees", "ref.soldier_full"], extra=out)
        out["check"] = rep
        with open(os.path.join(C.PARTS_DIR, f"{TAG}.json"), "w") as f:
            json.dump(out, f, indent=1)
    else:
        C.save_part(TAG, coll, extra=out)
    return out


if __name__ == "__main__":
    main(render="--no-render" not in C._argv())
