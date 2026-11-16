# Gloves

Build: `"$SGT_BLENDER" -b --python scripts/parts/gloves.py [-- --no-render]` (about 10 s with renders). Output:
`cache/parts/gloves.blend` (collection `Part.Gloves`: `Glove.{L,R}.Shell`, `.Knuckle`, `.Pad.{2,3,4,5}`),
`cache/parts/gloves.json`, `renders/gloves/*.png`.

## 1. What it is

**Identity:** hard-knuckle tactical gloves, Mechanix M-Pact class (take 1 D1 chose a hybrid with an Oakley SI Assault pattern). The construction is:
- stretch knit back;
- synthetic leather or goatskin palm;
- a one-piece moulded TPR knuckle guard with ribbed bosses;
- TPR pads over the PIP joints;
- a neoprene cuff closing with a hook-and-loop tab.

Size L for a 218 mm palm girth. Sources: take 1 `archive/v1/spec/11_gloves.md` §2 to §3 (M-Pact 3 guard envelope 95 x 35 x 6 from research §8; cuff about 45 to 50; hand dimensions from ANSUR via spec 05).

| Quantity | Real / source (mm) | Built (mm) |
|---|---|---|
| Glove over the hand | knit 1.2 + air 1.0 dorsal, about 0.5 palmar | 1.8 offset all round (capped between the fingers by the gap test), Solidify 1.0 |
| Knuckle guard | 95 x 35 x 6, one piece, over the MCP heads | 92 x 34, 4.5 thick + 2 mm bosses over each knuckle, centred 16 mm behind the joint centres |
| PIP pads | one per finger, over the PIP | 18 x 16 x 2.5 on fingers 2 to 5 |
| Cuff | neoprene 3.0, about 45 to 50 beyond the wrist, over the shirt cuff | 50 mm proximal of the wrist joint, 11 mm offset (shirt sleeve + 3.5 air + 3 neoprene) |
| Knuckle breadth (this body) | ANSUR hand breadth 91 | MCP-to-MCP joint centres 74 |

## 2. What the reference shows

Evidence: `ref/crop_hands_rifle.png`, `ref/zoom_glove_*`, spec 11 §2.
- Black gloves.
- On the right hand, a ribbed raised knuckle plate with four bosses (dusty), plus lit PIP pads; the index finger is extended along the receiver.
- On the left glove, the hand is overhand on the handguard, the thumb across the rail, and about 28 mm of neoprene cuff shows below the forearm guard.

## 3. Departures and why

- **Knuckle guard:** a smooth plate with four bosses. It has no ribs yet; the detail rounds add them.
- **Palm:** not separately modelled. The palm leather, heel patch and fingertip caps are detail and material rounds.
- **Cuff tab and pull:** not built.
- **Colours:** flat. Knit #1e1c1b, cuff #1b1c1e, guard #2f2c2a, pads #2a2826.

## 4. Round 1 (2026-11-14)

### Method
1. The hand skin plus the forearm to 70 mm behind the wrist is copied, cut there, and refined.
2. Each vertex is pushed out 1.8 mm on the hand, ramping to 11 mm over the cuff. The push is capped where fingers face each other.
3. The shell is de-spiked (`common.despike`), lightly smoothed, and cut 50 mm proximal of the wrist.
4. The faces proximal of the wrist get the cuff material.
5. The guard and pads are sheets laid on the glove shell. Rays are cast down the back of the hand onto it, in a hand frame: x across the knuckles, y along the fingers, z out of the back of the hand (checked against the thumb).

### Rigging
Everything takes weights from Body.Mesh (Data Transfer, nearest face interpolated) and has an Armature modifier on Morgan.Rig. The fingers bend with the curls.

### Clearance from the skin
- Rest: shell minimum 1.1 mm, 0 inside.
- Hero pose: the guard and pads stay 1.4 to 2.0 mm clear.
- The shells have 498 (left) and 476 (right) vertices inside the skin, at most 1.85 and 1.95 mm deep. Checked by bone: all are on the curled fingers, where fingertips press into the palm and fingers press into each other. This comes from round 0's finger-curl tables (85 to 95° on the ring and little fingers), not the glove's fit.

### Layering
The shirt sleeve ends are inside the cuffs: 0 and 1 of about 325 outward-facing sleeve vertices uncovered.

### Renders looked at
- `gloves_rest_dorsal_L` (back of the left hand): the guard sits across the knuckles, pads on the PIPs, the cuff is a thick band.
- `gloves_rest_front`, `_side`, `_threequarter`.
- `gloves_hero_hands_rifle_pair`: both gloves in the drawn places; the right index is extended as drawn. Without the carbine, the left hand floats where the handguard will be.
- `gloves_hero_soldier_full_pair`.

Two failures were fixed:
- A 30 mm spike at a fingertip, from even-offset Solidify; `common.solidify` now defaults to non-even.
- The guard first sat over the finger bases.

## 5. Round 2 (2026-11-14/15, with the pose's round 2)

The gloves went into the pose solve rather than the other way round: the glove shells, knuckle guards and PIP
pads are the hands' outer surface in `scripts/stages/pose_solve.py` (skinned with these objects' own weights,
`pose_contact.py --export`). The solver keeps every glove point at least 0.5 mm outside the carbine and the
carrier, puts the palm on its grip, and fits the fingers (replacing round 0's curl tables) so each phalanx
touches the grip and no glove enters another finger's or the palm's skin (scripts/stages/README.md, "Round 2").

**gloves.py is unchanged.** With the fitted fingers the shell no longer needed an offset or a corrective:

| Check (hero pose) | Round 1 | Round 2 |
|---|---:|---:|
| Glove.L.Shell inside the skin (gloves.json clearance_posed) | 498 verts, 1.85 mm | 9 verts, 1.48 mm |
| Glove.R.Shell inside the skin | 476 verts, 1.95 mm | 18 verts, 1.10 mm |
| knuckle guards and pads, minimum clearance | 1.4 to 2.0 mm | 1.79 to 2.12 mm |
| clash report body-gloves | 2657 verts, 2.1 mm | 18 verts, 1.5 mm |
| clash report gloves-carbine | 3592 verts, 24.9 mm | 42 verts, 1.0 mm (the handguard in the left glove) |
| clash report gloves-carrier | 472 verts, 15.4 mm | none |
| clash report shirt-gloves (a cuff vertex in the sleeve) | 4 verts, 24.5 mm | none |

The remaining shell vertices inside the skin sit at flexed finger joints, where the 1.8 mm offset is
squeezed by the bend (left at [-14, -391, 955], right at [-198, -184, 1092] mm). Real gloves compress there.

Renders opened: `renders/pose/pose_hands_sheet.png` (each hand from the camera, the gun's two sides, above and
in front), `renders/round_02/hands_rifle_compare.png`, `arm_R_compare.png`, `arm_L_compare.png`.
- The gloves follow the hands onto the grip and the handguard; the right index lies along the receiver.
- **A light flap at the left glove's thumb web** in the camera view: the shell folds where the thumb is
  abducted and extended (about -28 deg flexion and -19 deg spread at its base), and its inner face shows.

## 6. Still wrong, ranked for round 3

1. **The thumb-web fold** (§5): smooth the shell's weights across the thumb web (a few rings of weight
   smoothing between `finger1-1` and `metacarpal1`), or a corrective for thumb abduction.
2. **The glove follows the bare hand too closely.** It shows the fingernails' shape and the knuckle creases, and has no fingertip ease (+2.5 at each tip), no seams and no fourchettes. A glove-specific smoothing or a sculpted glove last would fix it.
3. **Knuckle guard:** it needs its moulded ribs (3 per boss at 7 mm pitch), the webs between the bosses, and to follow the knuckle arc better. Round 4: with the carbine's real stock the right hand turned back (§7), so the guard faces the camera more.
4. **Cuff:** no closure tab, pull or binding. It is a uniform ring.
5. **No leather, knit or neoprene materials**, and no dust on the up-facing bosses.
6. If gloves.py changes the shell, re-run the pose's contact export and solve (the hands' outer surface is
   this shell): `pose.py --solve --export`, or `pose_solve.py --continue-from cache/stages/pose_x_pass1.npz`.

## 7. Round 4 (2026-11-15): the grasp, on the new base

gloves.py is unchanged; the gloves were rebuilt on the 1844 mm base (their weights from the new body) and are again the
hands' outer surface in the pose solve. Two pose changes act on them (scripts/stages/README.md, "Round 4"):
- **The carbine's stock** (carbine.md §8) no longer hangs behind the grip, so place_hand starts the right hand at a turn
  of −15 deg about the grip (round 2: −30): the knuckle guard and the back of the hand face the camera more.
- **A grasp term** (pose_solve.py `GRASP`) holds the fingertips where the reference has them. Right: middle, ring and
  little tips on the grip's far side (met: y +14.9 / +18.9 / +8.7 mm in the gun frame), the thumb tip on the far side
  below the receiver (y +32, z −46: met), the index straight along the receiver. Left: the tips under the handguard
  (not met: they reach the corner under its right face, y −16 to −21, z −24 to −29, and the little finger stays on the
  face; the hand would have to sit lower and further right, which the body solve did not do).

Clearance in the pose and the clashes are in `renders/round_04/clashes.md` (the round's numbers, gloves.json's
clearance block is from the pre-solve pose).

## 8. Round 5 (2026-11-15): materials

`MATERIALS` in gloves.py (swapped by `common.library_pass`):
- **Back: `Knit.Glove.Honeycomb`** (new; cotton_jersey at 115 mm as the floor of the knit; no embossed honeycomb
  yet), **palm: `Leather.Glove.Goat`** (new; synthetic leather, Leather037's pebble at 41 mm, roughness 0.52):
  `palm_faces()` moves the shell's knit faces whose outward normal looks out of the palm side (against the hand
  frame's z by more than 0.25; winding found from the shell's centroid) to a third slot, so the palm and the
  finger fronts are leather.
- **Cuff: `Neoprene.Black`** (new), **knuckle guard and PIP pads: `TPR.Glove.Black`** (new; polymer builder,
  dusty crests: dust 0.8, pads 0.5).
- The right hand (on the grip, knuckles up) dust x1.0, the left x0.7.

Renders opened: `renders/round_05/hands_rifle_compare.png`, `torso_vest_compare.png`. Values sit near the
reference's (median ratio 0.91).

Still wrong (materials): no honeycomb emboss, no seams or stitch rows, the palm/back split is by normal, not by
the real pattern pieces; the guard's ribs (geometry) are missing so its dust has little to settle on.

## 9. Round 6 (2026-11-15): an M-Pact-class form

Critics m20, m31, m51 (notes/critic/soldier_r5/tally.md): glossy mannequin hands with no panels, knuckle guard
segments, palm reinforcement or cuff closure; blockier and more padded than a bare-hand shell.

**The rule kept: the palm and the finger fronts stay where round 5's shell was** (the hands are solved against the
carbine with this shell as their surface; scripts/stages/README.md). The bulk goes on the back:
- **Padded back**: the shell's ease grows 1.6 mm on the back of the hand and 1.0 mm on the backs of the fingers
  (`BACK_PAD`, ramped by the skin normal against the hand frame's z from 0.15 to 0.55, nothing on the cuff).
- **Panels as seams**: 0.35 mm grooves along the fingers' sides where the back meets the palm (the fourchettes) and
  a panel seam across the back 22 mm behind the knuckle guard (`SIDE_SEAM`).
- **Knuckle guard in segments**: a domed boss over each knuckle (3.2 high, r 11.5), a 1.4 mm groove between bosses,
  three moulded ribs across each boss at 7 mm pitch (`GUARD_SEG`); 92 x 34 as before.
- **Finger knuckle pads**: the PIP pads 19 x 18 x 3.0 (were 18 x 16 x 2.5) with ribs at 6 mm.
- **Palm reinforcement**: `Glove.{L,R}.PalmPatch`, a 60 x 48 synthetic-leather patch on the palm heel, a sheet
  0.15-0.35 mm over the shell with a 0.6 mm outward Solidify: the palm front moves out by under 1 mm there only.
- **Cuff closure**: `Glove.{L,R}.CuffTab`, a 30 x 44 x 2.2 hook-and-loop tab on the back of the cuff, its pull end
  raised 1.75 mm.

Materials: the patch uses `Glove.Mat.Palm`, the tab `Glove.Mat.Cuff` (existing slots; **MATERIALS table not
edited**).

**The pose is not re-solved.** gloves.md §6 item 6 still applies: the pose agent should re-export the contact
surface and re-solve when convenient; the fronts moved under 1 mm, so the grip holds as it is (clashes below).

**Renders opened** (renders/round_06/): `hands_rifle_cycles`, `hands_rifle_clay`, `arm_R_compare`, `arm_L_compare`.
At hero distance the right glove now shows a segmented knuckle guard with distinct bosses and the PIP pads; the left
glove, overhand on the handguard, shows its knuckle plate and finger pads. They read as padded tactical gloves rather
than bare-hand casts, but still smooth: no visible honeycomb, stitching or fourchette seams at this scale.

**Clashes** (`renders/round_06/clashes.md`): gloves-carbine 37 vertices, 1.4 mm (the handguard in the left glove, as
round 4/5: 1.0-1.4); body-gloves 28 vertices, 1.6 mm (flexed finger joints); the right forearm guard's wrist foam 5 mm
inside the right cuff shell (the guard laps over the cuff). Pose clearances (gloves.json): the shells 14 / 18 vertices
inside the skin, at most 1.25 mm (round 4: 9 / 18, 1.48).

## 10. Still wrong, ranked for round 7

1. Seams and stitching as geometry or normal detail (the grooves are 0.35 mm, invisible at hero distance); the
   knit back's honeycomb; the guard's edges could stand prouder.
2. The thumb-web fold (section 6 item 1) and fingertip ease are unchanged.
3. Re-export the contact surface and re-solve the pose with the new shell when the pose agent next solves.

## 11. Round 8 (2026-11-15): the look (critics m9, m48)

- **Black, neutral, slightly lighter** (the graded median was 1.30 x too dark with the light corrected): knit back
  #282624 -> #31302f, matte (roughness 0.84, specular 0.32); synthetic-leather palm #2a2826 -> #302f2e with a
  leather's soft gloss (roughness 0.52 -> 0.44) and its edges abraded toward #4a4846 (a 4 mm `edge_near` band);
  the TPR guard and pads satin (0.50) with greyer worn crests (edge albedo +0.06). Graded median ratio now 1.15.

Look-loop renders opened: `renders/look/M*/sheet_hands_rifle_graded`, `sheet_torso_vest_graded`.

Still wrong: the drawn gloves carry grey worn highlights on the knuckles and finger pads; ours are clean black.

## 11. Round 7 (2026-11-15, the pose agent)

Section 10 item 3 done: the contact surface was re-exported from the round-6 shell (after the head round-4 rebuild) and
the pose re-solved on it (scripts/stages/README.md, "Round 7"). Gloves in the carbine by the solver: right -0.32 mm,
left -0.38 mm; by the clash test the handguard is 5.5 mm into the left glove (99 vertices), where the solver's smoothed
field under-reads the slotted wall (README round 7, item 2). The left hand is fitted with a new arm-and-fingers placement
but its fingertips still stop at the lower edge of the near face instead of curling under it.
