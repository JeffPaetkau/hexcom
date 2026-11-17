"""Shirt, round 1 blockout: a Crye G3 class combat shirt (snug knit torso tucked into the trousers, roomier
ripstop sleeves to hook-and-loop cuffs at the wrist) as an offset shell from the rest body, and a fleece
neck gaiter (280 mm tube, 3 mm wall) worn pushed down into three rolls. Notes: scripts/parts/shirt.md.

  "$SGT_BLENDER" -b --python scripts/parts/shirt.py [-- --no-render] [--no-sim]
  -> cache/parts/shirt.blend (Part.Shirt: Shirt.Shell, Shirt.Gaiter), cache/parts/shirt.json, renders/shirt/

Shell: the torso, neck and arm skin (legs, head and hands excluded by bone weight) copied and refined,
pushed out by an ease field (torso 5 mm, sleeves 10 to 14 mm tapering to 5 at the cuff, blended by the arm
bones' weights), capped across the armpit, each sleeve segment moved toward its sectional convex hull,
smoothed, cut at the collar line, the tucked hem and both wrists, pushed out to a minimum clearance.
Gaiter: rings round the neck axis from a seat ring on the clavicles to a saddle-shaped top (higher at the
back), each point a ray to the skin plus the shirt collar plus the rolls' profile.
Both bound to Morgan.Rig by weight transfer from Body.Mesh.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cloth as K  # noqa: E402
import common as C  # noqa: E402

PART, TAG = "Shirt", "shirt"
TORSO_EASE = 5.0
TUCK_EASE = 2.0      # under the trousers' waistband the knit is pressed to the skin (round 1: 3.5, it showed through)
# Sleeve ease (mm off the skin) by arm parameter (0 shoulder, 1 elbow, 2 wrist). Round 9 (critics m11, m17, m39:
# "painted on"): a G3-class sleeve is cut full, about 20-30 mm of ease on the upper arm where the reference's arm
# carries its bulk, 24 at the elbow; it then draws in to the cuff inside the glove. Round 2's was 12-19.
SLEEVE9 = [(0.0, 16.0), (0.3, 27.0), (0.7, 29.0), (0.95, 27.0), (1.1, 24.0), (1.35, 19.0), (1.5, 16.0), (1.72, 11.0),
           (1.84, 5.5), (2.0, 5.0)]    # the forearm as round 2's: it lies under the guards and the gauntlets
# Round 10 (m8, m2: "a wetsuit over bloated upper arms", the figure stockier than the lean drawn man): round 9's 27-29 mm
# all round read as inflation, not slack. The upper sleeve comes back to 20-21 mm and the slack is shown as folds
# instead (SLEEVE_FOLDS): a real sleeve's surplus lies in gathers above the crook, not in an even balloon.
SLEEVE = [(0.0, 14.0), (0.3, 20.0), (0.7, 21.0), (0.95, 21.0), (1.1, 21.0), (1.35, 18.0), (1.5, 16.0), (1.72, 11.0),
          (1.84, 5.5), (2.0, 5.0)]
# Round 10: the upper sleeve's gathers, displaced after the solve along the arm's radial direction. Ridges every `pitch`
# mm along the arm (arm parameter t_lo..t_hi, faded in over `fade_in` from the shoulder and out over `fade_out` into the
# elbow), each tilted round the arm (a ridge's position along the arm drifts by tilt x sin of the angle, plus two
# harmonics of wobble, so they read as diagonal, broken folds and not rings), crisp crests (a Gaussian `crest` wide in
# phase) on shallow troughs, the mean taken back out so the sleeve does not inflate; deepest on the crook side (amp_in),
# shallow on the outer arm under the armour (amp_out). Each side has its own phase so the arms differ.
SLEEVE_FOLDS = {"t": (0.28, 1.08), "fade_in": 0.18, "fade_out": 0.12, "pitch": 30.0, "tilt": 9.0,
                "wobble": ((2, 5.0), (3, 3.0)), "crest": 0.16, "amp_in": 4.2, "amp_out": 1.4,
                "phase": {"L": 0.1, "R": 0.55}}
# Round 9: the back spans the shoulder blades (m11: the scapulae showed through from behind): above the tuck and
# below the collar, behind the spine's line (y > BACK_SPAN["y0"]), each horizontal section moves out to its convex
# hull, plus a little ease, as a woven-backed shirt hangs from the shoulder blades.
ELBOW_RELAX = (0.70, 1.35, 40)    # round 9: arm-parameter band and Taubin passes that blend the two hulls at the elbow
BACK_SPAN9 = {"z": (1080.0, 1520.0), "y0": 15.0, "ease": 3.0, "ramp": 60.0, "smooth": 0}
# Round 10 (m8, m32: the back muscles show through from behind): the span starts lower (the lower back between the
# carrier and the waistband shows), with more ease, and the spanned back is relaxed (Taubin) so the lats and the spine's
# columns stop showing as relief; the tuck below 1060 is laid back on the skin as before.
# (first try from 1050 over 40: the spanned lower back stood 4.5 mm proud of the trousers' waistband, 84 vertices of
# the trousers inside the shirt in the pose; now from just over the waistband's top at the back, 1087)
BACK_SPAN = {"z": (1085.0, 1520.0), "y0": 15.0, "ease": 6.0, "ramp": 50.0, "smooth": 24}
# Round 9: the sleeves' folds from the cloth solver (cloth.simulate) on the rest body. A real sleeve is cut longer
# than the arm (it must reach the wrist with the arm straight and reaching) and the surplus bunches at the crook and
# stacks above the cuff. Here each sleeve is extended past its cuff by `lift` mm (rings along the forearm, flaring a
# little), and in the solve that end ring is held and pushed back up the forearm to the cuff line over the first
# frames, so the sleeve, `lift` longer than its span, buckles under a light gravity and self-collision; the torso is
# held. Gravity is low because the rest arm hangs differently from the hero pose's: the folds should come from the
# surplus, not from the rest pose's sag. The hands are left out of the colliders (the extension passes through them
# at the start).
SLEEVE_SIM = {"lift": 20.0, "rings": 4, "flare": 0.5, "frames": 50, "goal": 0.12, "spread": (0.35, 1.95), "keep_forearm": (1.15, 1.45),
              "cloth": {"gravity": 0.25, "bending": 0.35, "mass": 0.03, "tension": 60.0, "compression": 40.0,
                        "shear": 12.0, "friction": 15.0, "pin_stiffness": 1.0}}
COLLAR = {"co": (0.0, -60.0, 1542.0), "no": (0.0, -0.35, 1.0)}    # collar top: 1542 front, ~1584 back (under the gaiter)
HEM_Z = 930.0                                                     # tucked hem, inside the trousers
# Round 10: the solve's lift 26 -> 20. With the slimmer upper sleeve the 26 mm surplus gathered at the elbow instead
# (elbow ease median 28, round 9 20) and pushed the right sleeve 10 mm out through the elbow pad's lower strap.
CUFF_BEYOND_WRIST = 8.0                                           # the cuff edge past the wrist joint (mm)
# Round 4, the elbow in the pose (91 deg between the segments, 44 deg more flexion than the rest arm's bend). The
# sleeve took the skin's weights there (forearm 0.9 to 1.0 right past the joint), so the sleeve's inside at the
# crook, 19 mm off the skin, turned the full 44 deg with the forearm into the biceps: round 2/3's body-shirt clash
# (25 vertices, 8.3 mm; the notes called it the back of the elbow, but measured in rest it is the crook, the
# anterior side, cos -0.99 to the point of the elbow). A sleeve does not hinge at the joint: the cloth over the
# elbow is shared by both segments. So over ELBOW_BAND (arm parameter: 0 shoulder, 1 elbow, 2 wrist) the sleeve's
# arm weights pass smoothly from the upper arm to the forearm (elbow_blend) and the cloth at the crook turns about
# half the angle. Tried: (0.70, 1.35) 4.4 mm inside, (0.60, 1.45) 2.0, (0.50, 1.55) 0.3 (kept), (0.40, 1.60) 1.2.
# The outside of the sleeve then rides 17 mm over the olecranon (mean 20), so it needs no extra ease there (an
# 8 mm lobe was tried and dropped: it only bulked the elbow).
ELBOW_BAND = (0.50, 1.55)
ELBOW_FRONT = (0.0, 0.5)     # the blend acts on the crook side only: smoothstep of -cos to the point of the elbow
# The gaiter (round 2): a fleece cowl bunched round the neck. s = arc length along the skin's meridian, 0 at
# the ring h_ref up the neck axis (on the neck all round), + up. Triples are (front, side, back).
GAITER = {"h_c": 60.0, "h_ref": 100.0, "fan_deg": 70.0,      # fan centre for the skirt's rays; s origin
          # round 10 (m34: a smooth cone sitting low; the reference bunches up under the jaw): the top edge 14-16 mm
          # higher at the front and sides (round 9: 18, 40, 62), the rolls bigger and less even (below)
          "s_top": (33.0, 54.0, 68.0),                       # top edge: under the chin, behind the jaw, occiput
          "tilt_side": 12.0,                                 # top edge and folds higher on his left (drawn)
          "s_bot": (-120.0, -88.0, -48.0),                   # skirt edge: under the bag top, under the straps
          "base_neck": 11.0, "base_skirt": 10.0,             # shirt collar / shirt plus air under the fleece
          # folds: (depth below s_top, half-width, proud above the base)
          "rolls": [((9.0, 10.0, 10.0), 16.0, (30.0, 24.0, 16.0)),        # lip at the top edge
                    ((44.0, 47.0, 50.0), 32.0, (60.0, 44.0, 26.0)),       # main roll under the jaw
                    ((92.0, 90.0, 90.0), 26.0, (24.0, 18.0, 9.0))],       # lower roll falling over the collar
          "wobble": [(2, 0.30), (3, 0.20), (5, 0.10)],       # fold height variation round the neck (harmonic, amp)
          "pleat": (65.0, 14.0, 0.55),                       # crease on his left front: phi deg, width deg, depth
          "drape": 7.0,                                      # vertical drapes of the skirt over the chest
          "strap_clear": 4.0,                                # flat this far inside the strap's inner edge
          "smooth": 6, "nphi": 96, "ns": 64, "seed": 7, "wall": 3.0}
# The carrier's shoulder straps (carrier.py imports this): centre line |x| and pad width (mm). The gaiter is
# pressed flat under them.
STRAP = {"x": 140.0, "w": 64.0}
COLOURS = {"shirt": "#2c2927", "gaiter": "#383029"}   # the solid-view colours (round 1); Cycles uses MATERIALS
# Materials round (round 5, 2026-11-15): a G3-class combat shirt is FR jersey on the torso (under the carrier)
# and NYCO ripstop on the sleeves (faces outboard of the shoulder joints, sleeve_faces()); the gaiter fleece.
MATERIALS = {
    "Shirt.Mat.Shirt": ("Knit.Jersey.FR", "Shirt", {}),
    "Shirt.Mat.Sleeve": ("NYCO.Ripstop.Black", "Sleeve", {}),
    "Shirt.Mat.Gaiter": ("Fleece.Polyester", "Gaiter", {}),
}


def sleeve_faces(ob):
    """Material index 1 (the sleeve) on faces whose centre lies outboard of the shoulder joint (rest x)."""
    import bpy
    me = ob.data
    if len(me.materials) < 2:
        me.materials.append(C.flat_material("Shirt.Mat.Sleeve", COLOURS["shirt"], 0.8))
    xs = abs(float(C.bone_mm("upperarm01.L")[0])) - 15.0
    cen = np.zeros(len(me.polygons) * 3)
    me.polygons.foreach_get("center", cen)
    cen = cen.reshape(-1, 3) * 1000.0
    idx = (np.abs(cen[:, 0]) > xs).astype(np.int32)
    me.polygons.foreach_set("material_index", idx)
    me.update()
    return int(idx.sum())


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def arm_param(V, side):
    """0 at the shoulder joint, 1 at the elbow, 2 at the wrist, by projection on the nearer arm segment."""
    sh, el, wr = C.bone_mm(f"upperarm01.{side}"), C.bone_mm(f"lowerarm01.{side}"), C.bone_mm(f"wrist.{side}")
    out = np.zeros(len(V))
    best = np.full(len(V), 1e9)
    for k, (a, b) in enumerate(((sh, el), (el, wr))):
        d = b - a
        t = np.clip(((V - a) @ d) / (d @ d), -0.5, 1.2)
        dist = np.linalg.norm(V - (a + np.outer(np.clip(t, 0, 1), d)), axis=1)
        m = dist < best
        out[m] = k + t[m]
        best[m] = dist[m]
    return out


def elbow_back(side):
    """The elbow joint (rest mm) and the unit direction from it to the point of the elbow: the rest arm is bent
    45 deg, so the joint lies off the shoulder-wrist line on the extensor side."""
    sh, el, wr = C.bone_mm(f"upperarm01.{side}"), C.bone_mm(f"lowerarm01.{side}"), C.bone_mm(f"wrist.{side}")
    d = wr - sh
    back = el - (sh + d * (((el - sh) @ d) / (d @ d)))
    return el, back / np.linalg.norm(back)


def elbow_blend(shell):
    """Round 4: over ELBOW_BAND the sleeve's arm weights (upperarm*, lowerarm*) are re-shared by the arm parameter
    alone, the forearm's share a smoothstep across the band, each segment's groups keeping their own proportions;
    other bones' weights are untouched. Returns the number of vertices changed per side."""
    me = shell.data
    R = np.array([tuple(v.co) for v in me.vertices]) * 1000.0
    names = {g.index: g.name for g in shell.vertex_groups}
    out = {}
    a, b = ELBOW_BAND
    for side, sg in (("L", 1.0), ("R", -1.0)):
        m = np.nonzero(np.sign(R[:, 0]) == sg)[0]
        t = arm_param(R[m], side)
        el, back = elbow_back(side)
        rr = R[m] - el
        front = smoothstep(ELBOW_FRONT[0], ELBOW_FRONT[1], -(rr @ back) / np.maximum(np.linalg.norm(rr, axis=1), 1e-9))
        sel = (t > a - 0.05) & (t < b + 0.05) & (front > 0.0)
        n = 0
        for i, ti, fr in zip(m[sel], t[sel], front[sel]):
            v = me.vertices[int(i)]
            w = {names[e.group]: e.weight for e in v.groups}
            up = {k: x for k, x in w.items() if k.startswith("upperarm") and k.endswith(side)}
            lo = {k: x for k, x in w.items() if k.startswith("lowerarm") and k.endswith(side)}
            A = sum(up.values()) + sum(lo.values())
            if A < 0.3:          # the armpit and torso side of the band: not the sleeve over the joint
                continue
            su, sl_ = sum(up.values()), sum(lo.values())
            # the crook side takes the band's share; elsewhere the skin's (the forearm guard and the pauldron, rigid on
            # their bones, sit over the outer sleeve: blending there pushed the sleeve 4.9 mm out through the guard)
            fl = float(fr * smoothstep(a, b, ti) + (1.0 - fr) * (sl_ / A))
            new = {}
            for k, x in (up.items() if su > 1e-6 else [(f"upperarm02.{side}", 1.0)]):
                new[k] = (1 - fl) * A * x / (su if su > 1e-6 else 1.0)
            for k, x in (lo.items() if sl_ > 1e-6 else [(f"lowerarm01.{side}", 1.0)]):
                new[k] = fl * A * x / (sl_ if sl_ > 1e-6 else 1.0)
            for k, x in new.items():
                g = shell.vertex_groups.get(k) or shell.vertex_groups.new(name=k)
                if x > 1e-4:
                    g.add([int(i)], float(x), "REPLACE")
                elif k in w:
                    g.remove([int(i)])
            n += 1
        out[side] = n
    C.say(TAG, f"elbow weights re-shared over the band {ELBOW_BAND}: {out}")
    return out


def build_shell(bd, bvh0, sim=True):
    V0 = bd["V"]
    leg = C.weight_sum(bd, lambda n: n.startswith(("upperleg", "lowerleg", "foot", "toe")))
    head = C.weight_sum(bd, lambda n: C.is_head(n) and not n.startswith("neck"))
    hand = C.weight_sum(bd, lambda n: n.startswith(("finger", "metacarpal")))
    keep = bd["in_body"] & ((leg < 0.5) | (V0[:, 2] > HEM_Z - 60)) & (head < 0.3) & (hand < 0.3) & (V0[:, 2] > HEM_Z - 120)
    V, F, _ = C.submesh(V0, bd["F"], keep)
    V, F, N = C.refine_on_skin(V, F, bvh0, cuts=1)
    C.say(TAG, f"shell region {len(V)} verts")
    # ease: torso, sleeves by arm parameter, blended by the arm bones' weights (nearest skin vertex)
    from mathutils.kdtree import KDTree
    kd = KDTree(len(V0))
    for i, v in enumerate(V0):
        kd.insert(v, i)
    kd.balance()
    near = np.array([kd.find(v)[1] for v in V])
    w_arm = C.weight_sum(bd, lambda n: n.startswith(("upperarm", "lowerarm", "wrist")))[near]
    w_arm = np.clip(w_arm * 1.3, 0, 1)
    off = TORSO_EASE - (TORSO_EASE - TUCK_EASE) * (1 - smoothstep(1060.0, 1100.0, V[:, 2]))  # pressed where tucked
    ps, pv = zip(*SLEEVE)
    for side, sg in (("L", 1.0), ("R", -1.0)):
        m = np.sign(V[:, 0]) == sg
        t = arm_param(V[m], side)
        sl = np.interp(t, ps, pv)
        off[m] = TORSO_EASE * (1 - w_arm[m]) + sl * w_arm[m]
    off = C.limit_by_gap(V, N, off, bvh0, share=0.5, floor=1.5)
    E = C.edges_of(F)
    off = C.smooth_field(off, E, iters=4)
    V1 = V + N * off[:, None]
    # sleeves hang: each segment toward its sectional convex hull
    for side, sg in (("L", 1.0), ("R", -1.0)):
        sh, el, wr = C.bone_mm(f"upperarm01.{side}"), C.bone_mm(f"lowerarm01.{side}"), C.bone_mm(f"wrist.{side}")
        m = np.sign(V[:, 0]) == sg
        t = np.zeros(len(V))
        t[m] = arm_param(V[m], side)
        for (a, b, lo, hi) in ((sh, el, 0.15, 1.0), (el, wr, 1.0, 1.72)):
            sel = m & (t >= lo) & (t < hi) & (w_arm > 0.7)
            V1 = C.convexify_along(V1, sel, a, b - a, slab=8.0, k=0.85)
    # round 9: the two segments' hulls met in a step at the elbow (the forearm's hull, which takes in the
    # olecranon, starts wider than the upper arm's ends: notes section 6 item 6); the sleeve is relaxed over the joint
    tt = np.full(len(V), -1.0)
    for side, sg in (("L", 1.0), ("R", -1.0)):
        m = np.sign(V[:, 0]) == sg
        tt[m] = arm_param(V[m], side)
    band = (tt > ELBOW_RELAX[0]) & (tt < ELBOW_RELAX[1]) & (w_arm > 0.7)
    V1 = C.taubin(V1, C.edges_of(F), iters=ELBOW_RELAX[2], lam=0.5, mu=-0.53, pin=~band)
    # round 9: the back spans the shoulder blades
    zb0, zb1 = BACK_SPAN["z"]
    back = (V[:, 1] > BACK_SPAN["y0"]) & (V[:, 2] > zb0) & (V[:, 2] < zb1) & (w_arm < 0.3)
    Vh = C.convexify_along(V1, back, np.zeros(3), np.array([0.0, 0.0, 1.0]), slab=8.0, k=1.0,
                           centre=np.array([0.0, 20.0]))
    grow = (Vh - V1)[:, :2]
    moved = np.linalg.norm(grow, axis=1) > 0.05
    wz = smoothstep(zb0, zb0 + BACK_SPAN["ramp"], V[:, 2]) * (1 - smoothstep(zb1 - 80.0, zb1, V[:, 2]))
    V1[:, :2] += grow * wz[:, None]
    if moved.any():
        dirn = grow[moved] / np.linalg.norm(grow[moved], axis=1)[:, None]
        V1[np.nonzero(moved)[0], :2] += dirn * (BACK_SPAN["ease"] * wz[moved])[:, None]
    if BACK_SPAN["smooth"]:
        relax = back & (wz > 0.05)
        V1 = C.taubin(V1, C.edges_of(F), iters=BACK_SPAN["smooth"], lam=0.5, mu=-0.53, pin=~relax)
    # cuts: collar line, tucked hem, wrists
    V1, F = C.bisect(V1, F, COLLAR["co"], COLLAR["no"], keep="below")
    V1, F = C.bisect(V1, F, (0, 0, HEM_Z), (0, 0, 1), keep="above")
    for side in ("L", "R"):
        el, wr = C.bone_mm(f"lowerarm01.{side}"), C.bone_mm(f"wrist.{side}")
        d = (wr - el) / np.linalg.norm(wr - el)
        V1, F = C.bisect(V1, F, wr + d * CUFF_BEYOND_WRIST, d, keep="below")
    # drop small islands left by the cuts (e.g. bits of hand) : keep the largest connected piece
    V1, F = largest_piece(V1, F)
    E = C.edges_of(F)
    pin = C.boundary_verts(F, len(V1))
    V1 = C.taubin(V1, E, iters=10, lam=0.5, mu=-0.53, pin=pin)
    V1 = C.push_out(V1, bvh0, np.where(V1[:, 2] < 1060.0, TUCK_EASE - 0.3, 3.0))
    if sim:
        V1, F = sleeve_solve(V1, F, bd, bvh0)
    V1 = sleeve_folds(V1, bd)
    # the tail under the trousers lies on the skin at TUCK_EASE (smoothing bridged the lumbar hollow, so the
    # trousers, which hug it, came through the shirt at the lower back: round 1's clash 13)
    w = 1.0 - smoothstep(1040.0, 1080.0, V1[:, 2])
    sel = w > 0
    d, n = C.signed_dist(V1[sel], bvh0)
    V1[sel] += n * ((TUCK_EASE - d) * w[sel])[:, None]
    return V1, F


def sleeve_solve(V, F, bd, bvh0):
    """Round 9: the sleeves buckled by the cloth solver (SLEEVE_SIM): each cuff extended along the forearm by `lift`,
    the extension's end ring held and pushed back to the cuff line, the torso (little arm weight) held, the sleeve
    free. Returns V, F (the extension stays: it is the sleeve's end after the push)."""
    from mathutils.kdtree import KDTree
    g = SLEEVE_SIM
    V0 = bd["V"]
    V = np.array(V, float)
    F = list(F)
    n0, nf0 = len(V), len(F)
    Vpre = V.copy()
    move = []
    ends = []
    for loop in C.boundary_loops(F):
        P = V[loop]
        cz = P.mean(0)
        for side in ("L", "R"):
            el, wr = C.bone_mm(f"lowerarm01.{side}"), C.bone_mm(f"wrist.{side}")
            if np.linalg.norm(cz - wr) > 45.0:
                continue
            d = (wr - el) / np.linalg.norm(wr - el)
            step = g["lift"] / g["rings"]
            prev = list(loop)
            for k in range(1, g["rings"] + 1):
                rad = P - cz
                rad -= np.outer(rad @ d, d)
                rn = rad / np.maximum(np.linalg.norm(rad, axis=1), 1e-9)[:, None]
                Q = P + d * step * k + rn * g["flare"] * k
                ids = list(range(len(V), len(V) + len(Q)))
                V = np.vstack([V, Q])
                m = len(loop)
                for j in range(m):
                    a, b = prev[j], prev[(j + 1) % m]
                    F.append((a, b, ids[(j + 1) % m], ids[j]))
                prev = ids
            ends.append((prev, -d * g["lift"]))
    # face orientation of the added rings follows the loop's order; make them agree with their neighbours
    import bmesh
    bm = C.arrays_to_bm(V, F)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    V, F = C.bm_to_arrays(bm)
    bm.free()
    kd = KDTree(len(V0))
    for i, v in enumerate(V0):
        kd.insert(v, i)
    kd.balance()
    near = np.array([kd.find(v)[1] for v in V[:n0]])
    w_arm = np.ones(len(V))
    w_arm[:n0] = C.weight_sum(bd, lambda n: n.startswith(("upperarm", "lowerarm", "wrist")))[near]
    pin = np.where(w_arm > 0.5, 0.0, 1.0)
    mv = np.zeros_like(V)
    for ids, dv in ends:
        pin[ids] = 1.0
        mv[ids] = dv
    for side, sg in (("L", 1.0), ("R", -1.0)):
        m = np.nonzero((np.sign(V[:n0, 0]) == sg) & (w_arm[:n0] > 0.5))[0]
        t = arm_param(V[m], side)
        pin[m[t < 0.12]] = 1.0
        pin[m[(t >= 0.12) & (t < 0.22)]] = 0.4                       # the shoulder seam eases in
        # the surplus spread along the sleeve: a weak goal on every sleeve vertex whose target slides toward the
        # shoulder by the share of `lift` its arm parameter has passed (the first try, the end ring alone, slid the
        # whole forearm tube up the arm and telescoped it into one ring at the elbow)
        sh, el, wr = C.bone_mm(f"upperarm01.{side}"), C.bone_mm(f"lowerarm01.{side}"), C.bone_mm(f"wrist.{side}")
        d1, d2 = (el - sh) / np.linalg.norm(el - sh), (wr - el) / np.linalg.norm(wr - el)
        free = (t >= 0.22)
        frac = smoothstep(g["spread"][0], g["spread"][1], t)
        dirs = np.where((t < 1.0)[:, None], d1[None], d2[None])
        mv[m[free]] = -dirs[free] * (g["lift"] * frac[free])[:, None]
        pin[m[free]] = g["goal"]
    for ids, dv in ends:                                          # the extension: all of the lift
        ring_all = [i for i in range(n0, len(V)) if np.linalg.norm(V[i] - V[ids[0]]) < 80.0]
        pin[ring_all] = np.maximum(pin[ring_all], g["goal"])
        mv[ring_all] = dv
        pin[ids] = 1.0
    hand = C.weight_sum(bd, C.is_hand)
    skinF = [f for f in bd["F"] if bd["in_body"][list(f)].all() and (hand[list(f)] < 0.5).all()]
    Vs = K.simulate("shirt_sleeves", V, F, colliders=[(V0, skinF)], pin=pin, move=mv, frames=g["frames"],
                    cloth=g["cloth"], self_group=(pin < 0.5).astype(float))
    C.say(TAG, f"sleeve solve: {len(ends)} cuffs extended {g['lift']:.0f} mm and pushed back; {int((pin < 0.5).sum())} "
               f"free vertices; moved median {np.median(np.linalg.norm(Vs - V, axis=1)[pin < 0.5]):.1f} mm")
    # the forearm keeps its cut shape (round 9's first evaluation: the bunched forearm and cuff ballooned over the
    # forearm guards, 25 mm, and over the glove gauntlets, which must cover the cuff): the solved folds are kept from
    # the shoulder to the elbow, blended back to the unsolved sleeve over keep_forearm, and the extension is dropped
    Vs = Vs[:n0].copy()
    F = F[:nf0]
    for side, sg in (("L", 1.0), ("R", -1.0)):
        m = np.nonzero((np.sign(Vpre[:, 0]) == sg) & (w_arm[:n0] > 0.5))[0]
        t = arm_param(Vpre[m], side)
        k = smoothstep(g["keep_forearm"][0], g["keep_forearm"][1], t)
        Vs[m] = Vs[m] * (1 - k)[:, None] + Vpre[m] * k[:, None]
    return C.push_out(Vs, bvh0, np.where(Vs[:, 2] < 1060.0, TUCK_EASE - 0.3, 3.0)), F


def sleeve_folds(V, bd):
    """Round 10 (SLEEVE_FOLDS): the upper sleeve's gathers as a radial displacement (see SLEEVE_FOLDS)."""
    g = SLEEVE_FOLDS
    V = np.array(V, float)
    near_arm = C.weight_sum(bd, lambda n: n.startswith(("upperarm", "lowerarm")))
    from mathutils.kdtree import KDTree
    kd = KDTree(len(bd["V"]))
    for i, v in enumerate(bd["V"]):
        kd.insert(v, i)
    kd.balance()
    w_arm = np.array([near_arm[kd.find(v)[1]] for v in V])
    t_lo, t_hi = g["t"]
    for side, sg in (("L", 1.0), ("R", -1.0)):
        m = np.nonzero((np.sign(V[:, 0]) == sg) & (w_arm > 0.5))[0]
        t = arm_param(V[m], side)
        sh, el = C.bone_mm(f"upperarm01.{side}"), C.bone_mm(f"lowerarm01.{side}")
        d = (el - sh) / np.linalg.norm(el - sh)
        L = float(np.linalg.norm(el - sh))
        rr = V[m] - (sh + np.outer(np.clip((V[m] - sh) @ d, 0, L), d))
        rad = rr / np.maximum(np.linalg.norm(rr, axis=1), 1e-9)[:, None]
        _el, back = elbow_back(side)
        bperp = back - d * (back @ d)
        bperp /= np.linalg.norm(bperp)
        ax2 = np.cross(d, bperp)
        ang = np.arctan2(rad @ ax2, rad @ bperp)             # 0 at the point of the elbow, pi at the crook
        inner = 0.5 - 0.5 * np.cos(ang)                       # 1 at the crook
        s = t * L                                             # mm along the upper arm
        s = s + g["tilt"] * np.sin(ang) + sum(a * np.sin(k * ang + 1.7 * k + 3.1 * g["phase"][side])
                                              for k, a in g["wobble"])
        ph = (s / g["pitch"] + g["phase"][side]) % 1.0
        crest = np.exp(-0.5 * ((ph - 0.5) / g["crest"]) ** 2)
        crest -= g["crest"] * np.sqrt(2 * np.pi)              # the profile's mean over a period: no net inflation
        env = smoothstep(t_lo, t_lo + g["fade_in"], t) * (1 - smoothstep(t_hi - g["fade_out"], t_hi, t))
        amp = g["amp_out"] + (g["amp_in"] - g["amp_out"]) * inner
        V[m] += rad * (amp * env * crest)[:, None]
    return V


def sleeve_measure(shell, bd):
    """Round 10: his left sleeve's girths (hull of the section across the segment) and ease (shell to skin, p10 /
    median / p90 mm) at mid humerus, the elbow and mid forearm, and the back's ease; rest."""
    V, _ = C.evaluated_world_mm(shell)
    d_skin, _n = C.signed_dist(V, C.skin_bvh(bd))
    out = {}
    sh, el, wr = C.bone_mm("upperarm01.L"), C.bone_mm("lowerarm01.L"), C.bone_mm("wrist.L")
    m = V[:, 0] > 0
    t = np.full(len(V), -9.0)
    t[m] = arm_param(V[m], "L")
    for label, t0, a, b in (("upper_arm", 0.5, sh, el), ("elbow", 1.0, sh, el), ("forearm", 1.5, el, wr)):
        d = (b - a) / np.linalg.norm(b - a)
        ax_d = np.linalg.norm((V - a) - np.outer((V - a) @ d, d), axis=1)
        sel = (np.abs(t - t0) < 0.04) & (ax_d < 85.0)          # the sleeve, not the torso beside it
        if sel.sum() < 8:
            continue
        P = V[sel] - (V[sel] @ d)[:, None] * d[None]
        e1 = np.cross(d, [0.0, 0.0, 1.0])
        if np.linalg.norm(e1) < 1e-6:
            e1 = np.cross(d, [1.0, 0.0, 0.0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(d, e1)
        H = C.hull2d(np.column_stack([P @ e1, P @ e2]))
        out[f"{label}_girth_mm"] = round(float(np.linalg.norm(np.diff(np.vstack([H, H[:1]]), axis=0), axis=1).sum()), 1)
        out[f"{label}_ease_mm"] = [round(float(x), 1) for x in np.percentile(d_skin[sel], [10, 50, 90])]
    for label, lo, hi in (("upper_back", 1300.0, 1450.0), ("lower_back", 1090.0, 1200.0)):
        sel = (V[:, 2] > lo) & (V[:, 2] < hi) & (np.abs(V[:, 0]) < 140) & (V[:, 1] > 0)
        out[f"{label}_ease_mm"] = [round(float(x), 1) for x in np.percentile(d_skin[sel], [10, 50, 90])]
    return out


def largest_piece(V, F):
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
    big = vals[np.argmax(cnt)]
    keep = roots == big
    Vn, Fn, _ = C.submesh(V, F, keep)
    return Vn, Fn


def _ray_profile(bvh, A, d, e, h_c, h_ref, fan_deg, h_max, step=1.5):
    """The skin under one meridian of the gaiter, bottom to top: hits of a fan of rays from the neck axis
    point A + d h_c swept from fan_deg below the horizontal up to it (they land on the chest, trapezius or
    upper back), then of horizontal rays from points climbing the axis to h_max (they land on the neck).
    Returns (points, normals, index of the first ray at or above h_ref)."""
    from mathutils import Vector
    P, N = [], []
    C0 = A + d * h_c
    for el in np.arange(-fan_deg, 0.0, 1.0):
        a = math.radians(el)
        dr = math.cos(a) * e + math.sin(a) * d
        hit = bvh.ray_cast(Vector(C0), Vector(dr), 400.0)
        if hit[0] is not None:
            P.append(np.array(hit[0]))
            N.append(np.array(hit[1]))
    k0 = None
    for h in np.arange(h_c, h_max, step):
        if k0 is None and h >= h_ref:
            k0 = len(P)
        hit = bvh.ray_cast(Vector(A + d * h), Vector(e), 200.0)
        if hit[0] is not None:
            P.append(np.array(hit[0]))
            N.append(np.array(hit[1]))
    P, N = np.array(P), np.array(N)
    N = N * np.sign(np.sum(N * (P - (A + d * h_c)), axis=1))[:, None]       # outward
    return P, N, k0


def _arclen_resample(P, N, k0, s_new):
    """Resample a polyline (and its normals) at arc lengths s_new measured from point k0 (+ toward the end)."""
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    s -= s[k0]
    s_new = np.clip(s_new, s[0], s[-1])
    Q = np.column_stack([np.interp(s_new, s, P[:, i]) for i in range(3)])
    M = np.column_stack([np.interp(s_new, s, N[:, i]) for i in range(3)])
    return Q, M / np.linalg.norm(M, axis=1)[:, None]


def _bump(s, c, w):
    """cos^2 lobe of half-width w at c (1 at c, 0 beyond)."""
    t = np.clip(np.abs(s - c) / w, 0.0, 1.0)
    return np.cos(t * math.pi / 2.0) ** 2


def _by_phi(phi, front, side, back):
    """A value that runs front (phi 0) -> side (+-90) -> back (180), smoothly."""
    c = math.cos(phi)
    return side + (front - side) * c if c >= 0 else side + (back - side) * (-c)


def build_gaiter(bvh0):
    """The cowl: for each meridian round the neck axis, the skin's profile from the shoulders up the neck
    (_ray_profile), resampled by arc length s (0 at the neck base ring, + up), pushed out along the skin
    normal by the collar allowance plus the folds: a lip at the top edge, the big main roll under the jaw
    that sags at the front, a lower roll, and a skirt that lies flat over the collar onto the chest,
    trapezius and upper back. The fold heights and depths vary round the neck (low harmonics, a pleat on
    his left), so the rolls read as one bunched tube, not as rings. Where the carrier's shoulder straps
    will lie (|x| inside STRAP's corridor) the gaiter is pressed flat to the collar allowance."""
    g = GAITER
    A = np.array([0.0, 12.0, 1488.0])                    # neck base centre (between the clavicles' ends)
    B = C.bone_mm("neck03")
    d = (B - A) / np.linalg.norm(B - A)
    ef = np.array([0.0, -1.0, 0.0]) - d * (-d[1])
    ef /= np.linalg.norm(ef)
    es = np.cross(d, ef)
    if es[0] < 0:
        es = -es                                          # phi +90 = his left (+X)
    nphi, ns = g["nphi"], g["ns"]
    rng = np.random.default_rng(g["seed"])
    ph_off = rng.uniform(0, 2 * math.pi, 6)
    x_in = STRAP["x"] - STRAP["w"] / 2.0 - g["strap_clear"]
    PH = 2 * math.pi * np.arange(nphi) / nphi
    # 1. the skin under the gaiter on a grid that is coherent round the neck: the same rays (fan angle, then
    #    height up the axis) for every meridian, smoothed, so neighbouring meridians do not disagree
    from mathutils import Vector
    C0 = A + d * g["h_c"]
    us = [("fan", el) for el in np.arange(-g["fan_deg"], 0.0, 1.0)] + [("h", h) for h in np.arange(g["h_c"], 200.0, 1.5)]
    k_ref = next(k for k, (t, v) in enumerate(us) if t == "h" and v >= g["h_ref"])
    R = np.full((len(us), nphi), np.nan)
    for i, phi in enumerate(PH):
        e = math.cos(phi) * ef + math.sin(phi) * es
        for k, (t, v) in enumerate(us):
            if t == "fan":
                a_ = math.radians(v)
                o, dr = C0, math.cos(a_) * e + math.sin(a_) * d
            else:
                o, dr = A + d * v, e
            hit = bvh0.ray_cast(Vector(o), Vector(dr), 400.0)
            if hit[0] is not None:
                R[k, i] = hit[3]
    for k in range(len(us)):                       # fill misses from the meridian neighbours
        row = R[k]
        if np.isnan(row).any() and not np.isnan(row).all():
            ok = ~np.isnan(row)
            row[~ok] = np.interp(np.nonzero(~ok)[0], np.nonzero(ok)[0], row[ok], period=nphi)
    G = np.zeros((len(us), nphi, 3))
    for i, phi in enumerate(PH):
        e = math.cos(phi) * ef + math.sin(phi) * es
        for k, (t, v) in enumerate(us):
            if t == "fan":
                a_ = math.radians(v)
                G[k, i] = C0 + (math.cos(a_) * e + math.sin(a_) * d) * R[k, i]
            else:
                G[k, i] = A + d * v + e * R[k, i]
    Fg = [(k * nphi + i, k * nphi + (i + 1) % nphi, (k + 1) * nphi + (i + 1) % nphi, (k + 1) * nphi + i)
          for k in range(len(us) - 1) for i in range(nphi)]
    G = C.taubin(G.reshape(-1, 3), C.edges_of(Fg), iters=15, lam=0.5, mu=-0.53).reshape(len(us), nphi, 3)
    # 2. arc length along each smoothed meridian (0 at h_ref), resampled at the gaiter's own rows
    S = np.zeros((ns, nphi))
    Q = np.zeros((ns, nphi, 3))
    for i, phi in enumerate(PH):
        P = G[:, i]
        sl = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        sl -= sl[k_ref]
        s_top = _by_phi(phi, *g["s_top"]) + g["tilt_side"] * math.sin(phi)
        s_bot = max(_by_phi(phi, *g["s_bot"]), sl[0])
        S[:, i] = np.linspace(s_bot, s_top, ns)
        Q[:, i] = np.column_stack([np.interp(S[:, i], sl, P[:, j]) for j in range(3)])
    F = []
    for j in range(ns - 1):
        for i in range(nphi):
            a, b = j * nphi + i, j * nphi + (i + 1) % nphi
            F.append((a, b, b + nphi, a + nphi))
    E = C.edges_of(F)
    Qf = C.taubin(Q.reshape(-1, 3), E, iters=6, lam=0.5, mu=-0.53).reshape(ns, nphi, 3)
    du = np.roll(Qf, -1, 1) - np.roll(Qf, 1, 1)
    dv = np.gradient(Qf, axis=0)
    M = np.cross(dv, du)
    rad = Qf - (A + np.outer(((Qf.reshape(-1, 3) - A) @ d), d).reshape(ns, nphi, 3))
    M *= np.sign(np.sum(M * rad, axis=2))[..., None]
    M /= np.linalg.norm(M, axis=2)[..., None]
    OFF = np.zeros((ns, nphi))
    BASE = np.zeros((ns, nphi))
    for i, phi in enumerate(PH):
        s = S[:, i]
        s_top, s_bot = s[-1], s[0]
        # collar allowance: the shirt over the chest, its collar plus air on the neck
        base = g["base_skirt"] + (g["base_neck"] - g["base_skirt"]) * smoothstep(-20.0, 10.0, s)
        wob = 1.0 + sum(a * math.sin(k * phi + ph_off[j]) for j, (k, a) in enumerate(g["wobble"]))
        pleat = 1.0 - g["pleat"][2] * math.exp(-0.5 * ((math.degrees(phi) - g["pleat"][0] + 180) % 360 - 180) ** 2
                                               / g["pleat"][1] ** 2)
        lift = 7.0 * math.sin(2 * phi + ph_off[4]) + 4.0 * math.sin(3 * phi + ph_off[5])   # folds wander up and down
        off = base.copy()
        for (dc, w, amp) in g["rolls"]:
            dcv = _by_phi(phi, *dc)
            off += _by_phi(phi, *amp) * wob * pleat * _bump(s, s_top - dcv + lift, w)
        # the skirt's soft drapes over the chest (front half only)
        fr = max(math.cos(phi), 0.0) ** 1.5
        sk = 1.0 - smoothstep(s_top - 95.0, s_top - 70.0, s)
        off += g["drape"] * fr * sk * (0.5 + 0.5 * math.cos(5 * phi + ph_off[5])) * smoothstep(s_bot, s_bot + 25.0, s)
        # the bottom edge thins out where it tucks under the carrier
        off -= (off - g["base_skirt"]) * (1 - smoothstep(s_bot, s_bot + 18.0, s))
        OFF[:, i], BASE[:, i] = off, base
    # the folds bulge away from the neck axis (a bunched tube), not along the skin normal: normals converge in
    # the hollow where the neck meets the shoulders and 50 mm along them would fold the surface through itself
    Dr = rad / np.linalg.norm(rad, axis=2)[..., None]
    Dr = 0.35 * M + Dr
    Dr /= np.linalg.norm(Dr, axis=2)[..., None]

    def place(off):
        return Qf + M * BASE[..., None] + Dr * (off - BASE)[..., None]
    V = place(OFF)
    # pressed flat under the shoulder straps: nothing outboard of the strap's inner edge stands proud
    k = np.clip((np.abs(V[..., 0]) - (x_in - 12.0)) / 12.0, 0.0, 1.0)
    k = k * k * (3 - 2 * k)
    OFF = BASE + (OFF - BASE) * (1 - k)
    V = place(OFF)
    Vf = V.reshape(-1, 3)
    f = F[len(F) // 2]
    nrm = np.cross(Vf[f[1]] - Vf[f[0]], Vf[f[3]] - Vf[f[0]])
    c = Vf[f[0]] - (A + d * ((Vf[f[0]] - A) @ d))
    if nrm @ c < 0:
        F = [tuple(reversed(q)) for q in F]
    Vf = C.taubin(Vf, E, iters=g["smooth"], lam=0.5, mu=-0.53)
    Vf = C.push_out(Vf, bvh0, g["base_skirt"] - 1.0)
    return Vf, F


def measure(shell, gaiter):
    V, _ = C.evaluated_world_mm(shell)
    out = {}
    for label, z in (("chest", 1360.0), ("waist", 1180.0)):
        sel = (np.abs(V[:, 2] - z) < 4.0) & (np.abs(V[:, 0]) < 190)
        P = V[sel][:, :2]
        if len(P) > 8:
            H = C.hull2d(P)
            out[f"{label}_girth_hull_mm"] = round(float(np.linalg.norm(np.diff(np.vstack([H, H[:1]]), axis=0), axis=1).sum()), 1)
    Vg, _ = C.evaluated_world_mm(gaiter)
    out["gaiter_height_front_back_mm"] = [round(float(Vg[:, 2].min()), 1), round(float(Vg[:, 2].max()), 1)]
    out["gaiter_width_x_mm"] = round(float(Vg[:, 0].ptp()), 1)
    return out


def main():
    import bpy
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    body, rig = C.open_base()
    coll = C.part_collection(PART)
    bd = C.body_data(body)
    bvh0 = C.skin_bvh(bd)
    Vs, Fs = build_shell(bd, bvh0, sim="--no-sim" not in args)
    shell = C.mesh_object("Shirt.Shell", Vs, Fs, coll, mat=C.flat_material("Shirt.Mat.Shirt", COLOURS["shirt"], 0.85))
    shell["sgt_clay"] = (0.44, 0.47, 0.52)
    Vg, Fg = build_gaiter(bvh0)
    gaiter = C.mesh_object("Shirt.Gaiter", Vg, Fg, coll, mat=C.flat_material("Shirt.Mat.Gaiter", COLOURS["gaiter"], 0.95, 0.4))
    gaiter["sgt_clay"] = (0.52, 0.47, 0.42)
    for o, th in ((shell, 1.2), (gaiter, GAITER["wall"])):
        C.bind(o, body, rig)
        if o is shell:
            elbow_blend(shell)
        m = C.solidify(o, th, inward=True)
        if o is gaiter:
            m.use_even_offset = False
        C.subsurf(o, 1)
    n_sleeve = sleeve_faces(shell)
    lib = C.library_pass(coll, "Shirt", MATERIALS, side_dust={"L": 0.9, "R": 1.0}, say_tag=TAG)
    lib["sleeve_faces"] = n_sleeve
    rest = C.clearance([shell, gaiter], body, "rest")
    lay_rest = C.clearance_between(gaiter, shell, "rest")
    meas = measure(shell, gaiter)
    meas.update(sleeve_measure(shell, bd))
    C.say(TAG, json.dumps(meas))
    used = C.apply_hero_pose(rig)
    posed = C.clearance([shell, gaiter], body, "hero pose")
    lay_pose = C.clearance_between(gaiter, shell, "hero pose")
    C.rest_pose(rig)
    C.save_part(TAG, coll, {"measure_mm": meas, "clearance_rest": rest, "clearance_posed": posed,
                            "gaiter_over_shirt": {"rest": lay_rest, "posed": lay_pose}, "pose": used,
                            "materials": lib})
    if "--no-render" not in args:
        C.render_part(TAG, coll, (0, -40, 1260), (1400, 900), crops=("ref.torso_vest", "ref.arm_R", "ref.arm_L", "ref.soldier_full"))


if __name__ == "__main__":
    main()
