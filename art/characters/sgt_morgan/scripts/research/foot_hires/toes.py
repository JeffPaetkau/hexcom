"""The region's anatomy for the trial: toe segment frames from the joints, the target dimensions, and small
field helpers. Frame F millimetres throughout (left foot: +X lateral, toes toward -Y).

A segment frame has its origin at the proximal joint, `a` along the bone toward the next joint (or the
tip), `n` dorsal (the world's up made perpendicular to `a`, then rolled) and `b = n x a`, lateral. Points
are read as (t, u, h): along, across (lateral +) and up.
"""
import math

import numpy as np

# The trial's targets (mm). Spec 01 §3.3 for the nails and pulps, Jeff's X3 for the hallux breadth and the
# 1-2 gap (an indication, 2026-10-10); a key can be overridden from run.py's --params.
PARAMS = {
    "level": 5,           # Catmull-Clark level of the dense copy: 0.16-0.19 mm on the toes
    # method (a)'s large forms (macro.py), mm
    # round 2 (critic round 1's fixes): the pulps are grown as smooth unions with ellipsoids (macro.pulps:
    # radii along, across, up; `back` from the nose to the centre; the hallux's on the floor, toe 2's sunk
    # `sink` below its underside), so round 1's inflations (pulp, tip) and the spade are off
    "pulp1": 0.0, "pulp2": 0.0,          # round 1's pulp inflations (2.4, 1.4)
    "tip1": 0.0, "tip2": 0.0,            # round 1's noses carried forward (2.0, 1.0)
    # round 5 (critic round 4 m5: broad and flat): the hallux's pad a little narrower across (14.8 -> 14.2) and
    # taller (6.8 -> 7.4), the toe deeper by `deepen1_*` (macro.deepen)
    "pulp1_e": {"frame": "floor", "back": 14.3, "radii": [14.0, 14.2, 7.4], "lift": 0.15, "k": 2.5},
    "deepen1_up": 2.2, "deepen1_down": 0.6, "deepen1_tip": 0.45, "deepen1_floor": 0.6,
    "pulp2_e": {"frame": "seg", "back": 7.0, "radii": [7.5, 7.9, 4.6], "sink": 0.5, "k": 1.5},
    "lift1": 2.4, "lift2": 0.0,          # the distal dorsum raised toward the tip (the hallux's wedge)
    "crown1": 0.8, "crown2": 0.4,        # the dorsum over the nail raised along its midline
    "neck1": 0.35, "neck2": 0.3,         # the pad's sides pinched in at the flexion crease (round 3: 0.8, 0.5,
                                         # on the plantar face too: the hallux's V-notch)
    # round 4: the plantar flexion creases' stations in the toes' plan frames (macro.Plan: mm from the joint,
    # horizontally), so each lies under its joint: the hallux IP, toe 2's PIP and DIP
    "crease1_s": 1.0, "crease2p_s": 1.8, "crease2d_s": 0.8,
    # round 4: toe 2's plantar PIP fold (part 01's curl leaves a sharp kink of squeezed faces) rounded by a
    # closing of the underside along the toe, a Gaussian of this sigma (mm; macro.close_folds; 0 = off), the
    # squeezed band spread by `fold_close_relax` Laplacian passes, over the middle `fold_close_side` of the
    # toe's half-width, fading to its sides (sigma 2.0 with 900 passes left a faint rectangle at the edges)
    "fold_close_sigma": 2.6, "fold_close_relax": 400, "fold_close_side": 0.6,
    # round 5 (critic round 4 m4: a crisp seam still rings toe 2's underside). Sliced, the curled toe's steep distal
    # face met the proximal pad at an apex rounded over only 0.3-0.4 mm: the cuff's edge. The closing now blurs
    # 2.6 mm along the toe (1.6) over a wider window (`fold_close_win`, stations from the PIP), its soft-minimum knee
    # 0.3 mm (0.06 creased the crossing), and the plantar PIP crease lies just before the bend (1.8 mm past the joint
    # in plan; the apex is about 2 mm past it, as sliced), wider and shallower: at 0.18 mm on the bend it notched the
    # apex, a soft fold now rather than a groove beside an edge
    "fold_close_k": 0.3, "fold_close_win": (-8.0, -5.0, 6.5, 9.0),   # (pass 2: from -6, -3)
    "crease2p_d": 0.1, "crease2p_w": 1.1,
    "droop1": 3.0, "droop2": 1.2,        # the tips' dorsum turned down toward the nose ...
    "droop_reach1": 4.5, "droop_reach2": 3.5,   # ... over the stretch ahead of the free edge only (round 1: 9, 5.5)
    "square1": -0.15, "square2": -0.15,  # the distal sections' upper corners (share of their radius): round 1
                                         # pushed them out (0.07, 0.06), a flat top that buried a domed nail's edges
    "spade1": 0.0,                       # the hallux's end widened (share of its half-breadth; round 1 0.07)
    "web_sdf": 1,                        # the 1-2 web by a projected closing (method_fields.web_by_closing)
    "fair_dorsum": 250,                   # Taubin passes over the distal segments' dorsum before the nails
    "ip_shift": 3.0,                     # the hallux IP's creases this far distal of MakeHuman's joint cube
    "mtp_prom": 2.6, "mt_head": 0.8,     # the first MTP prominence (inner border) and the head's knuckle
    "ehl": 1.0, "edl": 0.6,              # the long extensor tendons onto the hallux and toe 2
    "web_fair": 0, "web_y": -229.0,      # Taubin passes over the 1-2 cleft's floor, behind y_F web_y
    "web_r": 2.4,                        # method (b): the closing's radius over the 1-2 cleft's floor
    "voxel": 0.2,                        # method (b): the field's voxel (mm)
    "crease_scale": 1.0,
    # nails: visible width and length (proximal fold to free-edge tip), free edge beyond the bed, plate
    # thickness at the root and at the free edge, transverse radius, the plate hidden under each lateral
    # fold and under the proximal fold, the pulp left beyond the free edge in plan
    # round 2: `radius` is the plate's least transverse curvature (round 1 allowed 26 mm), `level` the depth
    # below the crest that bounds the visible width (deeper, as the dorsum is now domed), `cuticle` the cuticle
    # line's rise toward the sides, `epo_*` the eponychium lying on the plate at the root, `lat_fade` the
    # lateral folds' fade (now to the bed's end), `bed_wave` and `edge_wave` the free edge's unevenness
    # round 3 (critic round 2's press-ons): `lift_root` sinks the plate under the dorsum at the proximal fold
    # (the fold's edge rounds down onto it over `epo_w`; no eponychium plateau, so `epo_lap`, `epo_h` and
    # `fold_back_*` are gone), `roll_k` the folds' roll, `fold_asym` / `fold_wobble` each lateral fold its own
    # height and unevenness; each nail its own plan: `plan` (v / L, share of the half-width), `asym`, `cuticle`,
    # `corner_prox`, per-side free-edge corners `corner_m` / `corner_l`, the cut `clip` (from that share of the
    # half-width, the medial and lateral slants in degrees), the bed's end an arc (`bed_arc`) under a thinner,
    # flat-cut free edge. The hallux's is a broad shovel, narrower at the root, the lateral side tucked under a
    # higher fold; toe 2's a short rounded D, its root a deep arc, its sides converging toward the cut
    # round 4 (critic round 3 m3, m16: still a press-on, a tile in an even gutter, its free edge acrylic; the nail
    # rebuilt as its anatomy has it): the plate bonded to its bed (`open_bed`: no underside over the bed, so no
    # second glass surface and no light piped to a bright rim); each lateral fold swallows the margin unevenly
    # (`cover_wobble` mm, its own wave per side, fading toward the tip with the folds) over a plate whose own edge
    # stays smooth (detail.Nail.half_plan), its height more uneven (`fold_wobble`), a steeper lip (`roll_k`,
    # `lat_width`: a crevice, not a gutter); the proximal fold a broad soft roll lying low on the plate
    # (`roll_k_prox`, `epo_w`), the cuticle drawn on the plate by the recipe; a thinner free edge, cut a little
    # less evenly; the folds marked as the bed group's soft margin (`fold_halo`), where the skin is smooth
    # round 5 (critic round 4 m2, m3, m15, m17, m18, m20, m25: four rounds at 4, every critic seeing a tile in an
    # even gutter with exposed, bevelled edges and a French tip whatever the shading): `continuous`, the nail and
    # its folds one surface (detail.py): the plate's visible top is the skin, turning down into the lateral
    # grooves over its last `edge_curl` mm by `edge_drop`; the lateral folds roll over it with a width that
    # varies along the nail (`lat_width_wobble`) and persist toward the bed's end (`lat_fade`); the proximal fold
    # a broader roll a little higher over the root; the free edge a separate sliver only (`fe_*`: thinner, its
    # start buried `fe_back` mm behind the bed's end, its sides thinner), narrower, its line and the bed's end
    # less even; the lunula (`lunula_mm` visible at the centre over `lunula_half`, strength `lunula_k`) and the
    # cuticle are shading zones (look.NAIL_LOOK); toe 2's free edge a little further back from its nose
    "nail1": {"width": 18.5, "length": 17.5, "free_edge": 0.7, "thick_root": 0.5, "thick_edge": 0.5,
              "radius": 11.0, "hidden_side": 1.1, "root": 4.5, "tip_margin": 3.0, "roll_deg": -5.0,
              "fold_prox": 0.22, "fold_lat": 0.45, "prox_width": 2.6, "lat_width": 1.6, "corner": 1.2,
              "level": 4.6, "cuticle": 1.9, "corner_prox": 3.8, "lift_root": -0.38, "lift_reach": 3.0,
              "epo_w": 1.4, "roll_k": 2.6, "roll_k_prox": 1.8, "fold_asym": 0.2, "fold_wobble": 0.35,
              "cover_wobble": 0.35, "open_bed": 1, "fold_halo": 0.42, "fold_halo_mm": 1.8,
              "plan": [[0.0, 0.92], [0.35, 0.97], [0.7, 1.0], [1.0, 1.0]], "asym": 0.04,
              "corner_m": 1.6, "corner_l": 1.3, "clip": [0.6, 6.0, 9.0], "bed_arc": 0.55,
              "lat_fade": (0.6, 1.1), "bed_wave": 0.15, "edge_wave": 0.07,
              "continuous": 1, "edge_curl": 1.4, "edge_drop": 0.22, "curl_floor": 0.2, "lat_width_wobble": 0.35,
              "tuck": 0.15, "lip_roll": 0.2, "lip_roll_prox": 0.1,
              "relax_iters": 3, "tuck_fair": 12, "front_fair": 20, "undercut": 0.3, "fe_thick": 0.4, "fe_back": 0.5, "fe_emerge": 0.012, "descend": (0.15, 0.9), "fe_side_thin": 0.4,
              "lunula_mm": 2.0, "lunula_half": 5.5, "lunula_k": 0.6, "root_dive": 0.0},
    "nail2": {"width": 10.5, "length": 10.0, "free_edge": 0.6, "thick_root": 0.36, "thick_edge": 0.36,
              "radius": 6.0, "hidden_side": 0.7, "root": 2.8, "tip_margin": 2.2, "roll_deg": 0.0,
              "fold_prox": 0.16, "fold_lat": 0.32, "prox_width": 1.6, "lat_width": 1.1, "corner": 1.7,
              "level": 3.0, "cuticle": 1.8, "corner_prox": 2.6, "lift_root": -0.26, "lift_reach": 2.0,
              "epo_w": 1.0, "roll_k": 2.4, "roll_k_prox": 1.8, "fold_asym": -0.1, "fold_wobble": 0.3,
              "cover_wobble": 0.22, "open_bed": 1, "fold_halo": 0.42, "fold_halo_mm": 1.2,
              "plan": [[0.0, 0.9], [0.3, 0.98], [0.6, 1.0], [1.0, 0.93]], "asym": -0.03,
              "corner_m": 1.9, "corner_l": 1.5, "clip": [0.5, 5.0, 9.0], "bed_arc": 0.35,
              "lat_fade": (0.6, 1.1), "bed_wave": 0.12, "edge_wave": 0.06,
              "continuous": 1, "edge_curl": 0.9, "edge_drop": 0.14, "curl_floor": 0.2, "lat_width_wobble": 0.3,
              "tuck": 0.12, "lip_roll": 0.2, "lip_roll_prox": 0.1,
              "relax_iters": 3, "tuck_fair": 12, "front_fair": 20, "undercut": 0.25, "fe_thick": 0.3, "fe_back": 0.4, "fe_emerge": 0.01, "descend": (0.12, 0.8), "fe_side_thin": 0.4,
              "lunula_mm": 0.5, "lunula_half": 2.8, "lunula_k": 0.25, "root_dive": 0.0},
    # round 5 (critic round 4 m26, m1): spec 01 §3.4's skin tints (method_fields.tint_masks, look.TINT) and the
    # toes' hair (hair.py)
    "tint": 1, "hair": 1,
    # round 5 (critic round 4 m4): Foot.Sole on toes 1-2 from the dense normals, diffused (method_fields.soften_sole)
    "toe_sole": 1, "toe_sole_smooth": 40,
    # round 5: folds of a few faces on toes 1-2 laid flat after the nails and creases (method_fields.untangle:
    # Laplacian passes over the folded faces and `untangle_rings` rings round them; round 4's m19 fleck)
    "untangle": 30, "untangle_rings": 4,
    # toe 2's outline in plan (round 3, critic round 2 m5: an even tube): the PIP knuckle, the middle phalanx's
    # waist, the DIP and the pulp's flare (mm sideways on the toe's sides; macro.toe2_outline). Round 4: in the
    # toe's plan frame (stations in mm from the PIP; the waist midway to the DIP by default), sideways, not
    # along the normals (round 3's waist folded the plantar skin under the PIP: the sleeve cuff)
    "t2_knuckle": 1.6, "t2_waist": -1.0, "t2_dip": 0.0, "t2_flare": 0.6, "t2_gap": 0.35,
    # round 5 (critic round 4 m4): the knuckle's share on toe 2's lower sides (seen from below the outline stepped
    # in at the PIP)
    "t2_knuckle_low": 0.3,
}

# --------------------------------------------------------------------------- whole foot, pass 1 (2026-10-13)
# Toes 3-5 in the method (notes/research_foot_hires.md, "Whole foot, pass 1"). Spec 01 §3.3's nails (10 x 9, 9 x 8,
# 7 x 6; radii 5.5, 5, 4; folds 1.0 / 0.8 ... 0.8 / 0.6) on part 01's toes, which lean 0, 9 and 41 degrees laterally
# (measured: the nail beds' mean normals about the distal axes; part 01 rolls toe 4 by 10 and toe 5 by 40, so the
# fifth nail faces up and out). Each nail its own plan: toe 3 a short rounded square, toe 4 narrower at the root
# with its medial side under a higher fold (it leans toward toe 3), toe 5 small, thick and rounded, rolled out,
# its medial half under a puffy fold. The nails start 4-5 mm past the DIP (round 5's m13: toe 2's 8 mm of bare
# skin read finger-long). No lunula on toes 3-5 (spec 01 §3.3).
TOES = {  # distal segment, its group, the next group in, every group of the toe
    1: ("h2", "toe1-2.L", "toe1-1.L", ("toe1-1.L", "toe1-2.L")),
    2: ("t2d", "toe2-3.L", "toe2-2.L", ("toe2-1.L", "toe2-2.L", "toe2-3.L")),
    3: ("t3d", "toe3-3.L", "toe3-2.L", ("toe3-1.L", "toe3-2.L", "toe3-3.L")),
    4: ("t4d", "toe4-3.L", "toe4-2.L", ("toe4-1.L", "toe4-2.L", "toe4-3.L")),
    5: ("t5d", "toe5-3.L", "toe5-2.L", ("toe5-1.L", "toe5-2.L", "toe5-3.L")),
}


def _nail(base, **kw):
    out = dict(base)
    out.update(kw)
    return out


PARAMS.update({
    "nail3": _nail(PARAMS["nail2"], width=9.6, length=9.4, free_edge=0.55, radius=5.5, hidden_side=0.6, root=2.5,
                   tip_margin=1.9, prox_width=1.4, lat_width=1.0, corner=1.5, level=2.8, cuticle=1.5, corner_prox=2.3,
                   lift_root=-0.24, epo_w=0.9, fold_prox=0.15, fold_lat=0.3, fold_asym=0.15, fold_wobble=0.3,
                   cover_wobble=0.2, fold_halo_mm=1.1, plan=[[0.0, 0.86], [0.35, 0.97], [0.7, 1.0], [1.0, 0.95]],
                   asym=0.05, corner_m=1.6, corner_l=1.9, clip=[0.5, 7.0, 6.0], bed_arc=0.3, edge_curl=0.85,
                   edge_drop=0.13, undercut=0.22, fe_thick=0.3, fe_back=0.4, lunula_mm=0.0, lunula_half=2.5,
                   lunula_k=0.0, roll_deg=0.0),
    "nail4": _nail(PARAMS["nail2"], width=8.6, length=8.4, free_edge=0.5, radius=5.0, hidden_side=0.55, root=2.3,
                   tip_margin=1.8, prox_width=1.3, lat_width=0.95, corner=1.4, level=2.6, cuticle=1.4, corner_prox=2.1,
                   lift_root=-0.22, epo_w=0.85, fold_prox=0.15, fold_lat=0.3, fold_asym=-0.18, fold_wobble=0.32,
                   cover_wobble=0.2, fold_halo_mm=1.0, plan=[[0.0, 0.82], [0.35, 0.96], [0.7, 1.0], [1.0, 0.92]],
                   asym=-0.06, corner_m=1.5, corner_l=1.7, clip=[0.45, 8.0, 7.0], bed_arc=0.3, edge_curl=0.8,
                   edge_drop=0.12, undercut=0.22, fe_thick=0.3, fe_back=0.4, lunula_mm=0.0, lunula_half=2.2,
                   lunula_k=0.0, roll_deg=-9.0),
    # toe 5: spec 01 §3.3's 7 x 6, 0.9 thick and slightly ridged at the free edge, radius 4, rolled out with its toe
    "nail5": _nail(PARAMS["nail2"], width=6.6, length=6.2, free_edge=0.45, radius=4.0, hidden_side=0.5, root=2.0,
                   tip_margin=1.6, prox_width=1.2, lat_width=0.9, corner=1.3, level=2.2, cuticle=1.1, corner_prox=1.8,
                   lift_root=-0.2, epo_w=0.8, fold_prox=0.16, fold_lat=0.36, fold_asym=-0.35, fold_wobble=0.35,
                   cover_wobble=0.25, fold_halo_mm=1.0, plan=[[0.0, 0.8], [0.4, 0.95], [0.75, 1.0], [1.0, 0.9]],
                   asym=-0.14, corner_m=1.4, corner_l=1.6, clip=[0.4, 10.0, 12.0], bed_arc=0.25, edge_curl=0.7,
                   edge_drop=0.12, undercut=0.2, fe_thick=0.42, fe_back=0.35, lunula_mm=0.0, lunula_half=2.0,
                   lunula_k=0.0, roll_deg=-38.0),
    # the lesser toes' pulps (macro.pulps), as toe 2's: ellipsoids under the curled distal phalanges
    "pulp3_e": {"frame": "seg", "back": 6.4, "radii": [6.8, 7.2, 4.3], "sink": 0.45, "k": 1.4},
    "pulp4_e": {"frame": "seg", "back": 6.0, "radii": [6.4, 6.8, 4.1], "sink": 0.45, "k": 1.4},
    "pulp5_e": {"frame": "seg", "back": 5.4, "radii": [6.0, 6.8, 4.2], "sink": 0.4, "k": 1.4},
    "droop3": 1.0, "droop4": 0.9, "droop5": 0.7, "droop_reach3": 3.2, "droop_reach4": 3.0, "droop_reach5": 2.6,
    "crown3": 0.3, "crown4": 0.25, "crown5": 0.0, "crown_len3": 9.4, "crown_len4": 8.4,
    "square3": -0.15, "square4": -0.15, "square5": -0.1,
    # toe 5's own form (macro.toe5_form): shorter and stouter, in its plan frame: the middle and distal segments
    # shortened by `toe5_short` mm toward the PIP, the distal half filled out by `toe5_girth` mm on its free
    # (lateral and dorsal) sides, never nearer toe 4 than `t2_gap`
    "toe5_short": 1.4, "toe5_girth": 0.6,
    # toe 2's plantar fold closing (macro.close_folds) on every curled lesser toe
    "fold_close_toes": [2, 3, 4, 5],
    # whole foot, pass 2: the underside the closing acts on is the lower part of each toe's section (shares of its
    # height), not the skin within 0.4-2 mm of the lowest in its cell, and the relaxation spans the toe's width: the
    # plantar PIP fold of the curled toes is a Z of overlapping skin, and the old gate left its upper layers standing
    # as a slit (the hairline cut across toes 3 and 4) and folded 41 face pairs on toe 4 (macro._close_fold)
    "fold_close_under": [0.3, 0.5], "fold_close_relax_side": 0,
    # ... and the relaxation solved to convergence (macro.harmonic) over the PIP's window and the toe's inner 0.8, the
    # window reaching 8 mm behind the joint: 400 Jacobi passes left the Z's layers packed into 0.7 mm, where laid on
    # the closed surface they overlapped (249 flipped pairs on toe 3); solved, toes 2-5 have none and no edge sharper
    # than 60 degrees but 9 on toe 4 (offline, scratch fold_lab on the stage's dense skin)
    "fold_close_harmonic": 1, "fold_close_harm_side": 0.8,
    # ... and the band where the closing gives way to the held sides faired (40 Taubin passes over 0.3-1.0 of the
    # half-width): at toe 4's medial base, where the Z stands 3 mm tall against toe 3, its partly laid layers stood up as
    # a knob 2 mm across (peak curvature 0.011, the dense skin's 0.003; faired 0.004); toes 2-5 have no flipped face and
    # no edge sharper than 60 degrees
    "fold_close_edge_fair": 40, "fold_close_edge_band": [0.3, 0.45, 0.9, 1.0],
    # the 2-3, 3-4 and 4-5 webs by one closing (method_fields.webs_lesser): the commissures where part 01 left
    # them (spec 01 §3.3, Jeff's direction: y -235, -231.1, -218), a smaller radius than the 1-2 web's (the
    # lesser toes touch), low on the toes, so the dorsal grooves between the proximal phalanges stay
    # (version 2: the first build's mask, 1.6 mm full and 3 mm of fade either side of each cleft, reached most of
    # each toe's underside, filled the plantar sulcus at the toes' bases and ended in seams across them)
    # whole foot, pass 2: OFF. The census (method_fields.FoldCensus, `debug_folds`) found this closing makes 10,731
    # of the 10,855 folded face pairs: between toes that touch (0.2-0.35 mm apart) a closing fills the slit itself,
    # its mask's fade along the toe caps the slit across (the critics' "ruler-straight hairline cut" across toes 3
    # and 4), and the projection lands both facing walls on the one filled surface, where they crumple (the dark
    # seams along the touching sides). The touching walls are now brought into contact instead (whole.toe_contact)
    # and the commissures are part 01's
    "webs_lesser": 0,
    # the long extensors moved out of the stage (whole.tendons, after the webs)
    "ehl": 0.0, "edl": 0.0,
})
# round 5's blocking m2 (no lunula reads on the hallux): a dull, paler half-moon about 3 mm deep at the centre over
# the middle 13 mm, 2 mm more of it under the fold (detail.Nail.nail_fields), stronger (look.NAIL_LOOK's colour
# and roughness); toe 2's stays faint
# (the first render: a band along the whole root, too white and too crisp; now a narrower, deeper, softer
# half-moon over the middle 60 % of the root)
PARAMS["nail1"].update(lunula_mm=3.4, lunula_half=5.4, lunula_k=0.85, lunula_hide=1.6)
PARAMS["nail2"].update(lunula_mm=0.7, lunula_half=3.0, lunula_k=0.35, lunula_hide=0.8)
# whole foot, pass 2: with the PIP fold closed (fold_close_harmonic) toe 2's plantar crease is a soft fold, as the
# lesser toes' (whole.PLANTAR_LESSER), a little before its old kink (round 5: 1.8 mm, 0.1 deep, sigma 1.1)
PARAMS.update({"crease2p_s": 1.2, "crease2p_d": 0.26, "crease2p_w": 0.7})


# --------------------------------------------------------------------------- shape pass 2 (2026-10-15)
# Jeff (2026-10-15): "I think toe 2 looks right; it is the big toe that is too long". Part 01 shortens the hallux by
# 1.5 mm in its proximal phalanx and 6 in its distal segment (fields.shorten_hallux: from the IP 36.2 -> 30.2 mm), so
# the nail shortens with the segment (x 0.834: 17.5 -> 14.6, its width kept) and the pulp's ellipsoid with it a little
# (it reached back to the IP otherwise; its front stays at the tip, so the pad stays round). Critic series foot_shape,
# round 1 (notes/critic/foot_shape_r1/tally.md): toe 2's knuckle beads and waist off (m14-m16: knobbly, waisted
# fingers; whole.toe_fill fills the waists of every lesser toe), the lesser pulps broader across and the tips turned
# down a little more (m16: tips angled down onto broad pulps), toe 5's nail rolled with part 01's 55 degree roll (m9,
# m18; part 01's beds now lean 58 degrees out, 42 before)
PARAMS["nail1"].update(length=14.6)
PARAMS["pulp1_e"] = dict(PARAMS["pulp1_e"], back=12.6, radii=[12.5, 14.2, 7.4])
PARAMS.update({"t2_knuckle": 0.5, "t2_waist": 0.0,
               "droop2": 1.5, "droop3": 1.3, "droop4": 1.2, "droop5": 0.9})
for _k, _across in ((2, 8.6), (3, 8.0), (4, 7.6), (5, 7.3)):
    _e = dict(PARAMS[f"pulp{_k}_e"])
    _e["radii"] = [_e["radii"][0], _across, _e["radii"][2]]
    PARAMS[f"pulp{_k}_e"] = _e
PARAMS["nail5"].update(roll_deg=-54.0)


def toe_weight(groups, k):
    return np.clip(sum(groups[g] for g in TOES[k][3]), 0.0, 1.0)


def toes_weight(groups, ks=(1, 2, 3, 4, 5)):
    return np.clip(sum(toe_weight(groups, k) for k in ks), 0.0, 1.0)


def rolled(seg, deg):
    """A copy of a segment frame turned about its axis (positive toward medial, as detail.Nail's roll_deg)."""
    import copy
    out = copy.copy(seg)
    if deg:
        out.n = rotate(seg.n, seg.a, deg)
        out.b = np.cross(out.n, out.a)
    return out


class Seg:
    """A toe segment's frame in F."""

    def __init__(self, origin, end, roll_deg=0.0, up=(0.0, 0.0, 1.0)):
        self.o = np.asarray(origin, float)
        d = np.asarray(end, float) - self.o
        self.length = float(np.linalg.norm(d))
        a = d / self.length
        up = np.asarray(up, float)
        n = up - (up @ a) * a
        n /= np.linalg.norm(n)
        if roll_deg:
            n = rotate(n, a, roll_deg)
        self.a, self.n = a, n
        self.b = np.cross(n, a)   # lateral for the left foot (checked by the caller's sign test)
        if self.b[0] < 0.0:
            raise ValueError("segment frame: b is not lateral (+x); the frame assumes the left foot")

    def local(self, q):
        d = np.asarray(q, float) - self.o
        return d @ self.a, d @ self.b, d @ self.n

    def point(self, t, u, h):
        return self.o + np.multiply.outer(t, self.a) + np.multiply.outer(u, self.b) + np.multiply.outer(h, self.n)

    def vec(self, da, db, dn):
        return np.multiply.outer(da, self.a) + np.multiply.outer(db, self.b) + np.multiply.outer(dn, self.n)


def rotate(v, axis, deg):
    """Rodrigues: v turned about a unit axis by deg (right hand)."""
    k = np.asarray(axis, float) / np.linalg.norm(axis)
    th = math.radians(deg)
    v = np.asarray(v, float)
    return v * math.cos(th) + np.cross(k, v) * math.sin(th) + k * (k @ v) * (1.0 - math.cos(th))


def segments(J):
    """The toes' segment frames from the joints (common.joints): the hallux's proximal and distal (h1, h2),
    each lesser toe's three (t<k>p, t<k>m, t<k>d; whole foot, pass 1)."""
    out = {"h1": Seg(J["toe-1-1"], J["toe-1-2"]), "h2": Seg(J["toe-1-2"], J["toe-1-3"])}
    for k in (2, 3, 4, 5):
        for i, nm in enumerate("pmd", start=1):
            out[f"t{k}{nm}"] = Seg(J[f"toe-{k}-{i}"], J[f"toe-{k}-{i + 1}"])
    return out


def merged(params):
    """PARAMS with overrides: a key's dict is merged one level deep."""
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in PARAMS.items()}
    for k, v in (params or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


# --------------------------------------------------------------------------- 1-D profiles

def smoothstep(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def window(x, a0, a1, b1, b0):
    """0 outside [a0, b0], 1 inside [a1, b1], smooth between."""
    return smoothstep(x, a0, a1) * (1.0 - smoothstep(x, b1, b0))


def gauss(x, sigma):
    return np.exp(-0.5 * (np.asarray(x, float) / sigma) ** 2)


def roll(x):
    """A quarter circle from (0, 0) to (1, 1): vertical at 0, flat at 1 (a fold's lip rising from the plate)."""
    x = np.clip(np.asarray(x, float), 0.0, 1.0)
    return np.sqrt(np.maximum(1.0 - (1.0 - x) ** 2, 0.0))
