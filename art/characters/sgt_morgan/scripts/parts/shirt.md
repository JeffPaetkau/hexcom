# Shirt (combat shirt and neck gaiter)

Build: `"$SGT_BLENDER" -b --python scripts/parts/shirt.py [-- --no-render]` (about 12 s with renders). Output:
`cache/parts/shirt.blend` (collection `Part.Shirt`: `Shirt.Shell`, `Shirt.Gaiter`), `cache/parts/shirt.json`,
`renders/shirt/*.png`.

## 1. What it is

**Shirt:** a Crye Precision G3 class combat shirt. Its construction is:
- an FR knit torso, worn tucked under the trousers and carrier;
- NYCO ripstop sleeves;
- a zipped mandarin collar;
- elbow-pad pockets;
- hook-and-loop cuffs.

**Gaiter:** a polyester fleece neck gaiter, about 280 mm long, 460 mm round and 3 mm thick. Pushed down, it buckles into three rolls. A thin 530 mm microfibre tube was rejected (take 1 D3).

Sources: take 1 `archive/v1/spec/10_combat_shirt_gaiter.md` §2 to §3 (G3 product description, ANSUR sleeve length; gaiter class and the buckling wavelength argument).

| Quantity | Real / source (mm) | Built, rest (mm) |
|---|---|---|
| Torso ease | snug knit, chest +40 | 5 mm offset; 2 mm where it is tucked (below z 1060, round 2: laid on the skin there) |
| Chest girth (garment) | body + about 40 | 1059 (convex hull at z 1360; body chest 993) |
| Sleeve ease | rib or ripstop upper arm 390 vs body 345 (about +7 offset); elbow 360; forearm 350 | round 2: 12 at the shoulder, 18 upper arm, 19 at the elbow, 16 forearm, 11 then 5.5 over the last 40 mm |
| Cuff | 215, closing to 200, ending inside the glove gauntlet | cut 8 mm past the wrist joint, 5 to 5.5 mm offset, inside the glove cuff (0 and 1 vertex uncovered in the pose) |
| Hem | tucked, at about h 850 | cut at z 930, inside the trousers |
| Collar | mandarin, 55 tall | the shell runs up the neck to a plane at 1542 front and about 1584 back (round 2, lowered 16 at the back to stay under the gaiter) |
| Gaiter | fleece tube 280 x 460, 3 thick, pushed down into a cowl | round 2: a cowl from the chin to under the bag top, 1471 to 1659 tall, 304 wide over the shoulders (skirt), its folds out to 120 in front of the neck axis; lip 26/20/16 proud (front/side/back), main roll 52/36/24, lower roll 18/14/8; wall 3; flat (11 mm over the skin) under the strap corridor |x| > 92 |

## 2. What the reference shows

Evidence: `ref/crop_torso_vest.png`, `ref/crop_arm_*`, `ref/zoom_shirt_*`, `ref/zoom_gaiter_rolls_x8.png`, spec 10 §2.
- A dark shirt, about #332f2d (the left sleeve median, cool-lit).
- The torso is almost entirely under the carrier.
- The sleeves show between the pauldrons and forearm guards, and fold at the elbows.
- A bulky dark brown gaiter, #373029, rolled in three lobes under the jaw, with its top edge higher at the back.

## 3. Departures and why

- **Rib-knit shoulder panels:** none yet. Take 1 kept them as "image wins, plausible"; they are a detail round.
- **Bicep pockets:** omitted (take 1 D6). Elbow-pad pockets are not modelled; the armour part's elbow caps sit outside.
- **Collar zip and placket:** not built; hidden by the gaiter and carrier.
- **Colours:** flat. Shirt #2c2927, gaiter #383029.
- **Gaiter shape (round 2):** procedural, not simulated. The drawn cowl is three or four large soft folds; a
  procedural fold field gives them exactly where the drawing has them, deterministically, in 3 s. A cloth
  simulation (a tube collided with the posed body and pushed down) is the round-3 route to real buckling detail.
- **The gaiter is flat under the carrier's straps** (`STRAP` in shirt.py, which carrier.py imports): in the drawing
  the straps lie on top of it, so the fleece there is pressed to the collar.

## 4. Round 1 (2026-11-14)

### Shell
1. Torso, neck and arm skin is copied (legs below the hem, head and hands excluded by bone weight), and refined.
2. Each vertex is pushed out by an ease field. The torso and sleeve eases are blended by each vertex's arm-bone weight, so the shoulder joins smoothly. Sleeve ease follows an arm parameter: 0 at the shoulder joint, 1 at the elbow, 2 at the wrist.
3. The push is capped across the armpits.
4. The upper arm and forearm sections move 85 % of the way to their convex hull.
5. The shell is cut at the collar line, the hem and both wrists, reduced to its largest connected piece, smoothed, and pushed out to at least 3 mm.

### Gaiter
1. Rings round a neck axis run from (0, 12, 1488) to the neck03 joint, from a seat ring to a saddle-shaped top.
2. Each point is a ray to the skin, plus 11 mm (shirt collar and air), plus the three rolls' cos² lobes, plus a 2 mm band at the bottom.
3. The rings are Taubin-smoothed and pushed out to 10 mm from the skin.

### Thickness and rigging
- Solidify 1.2 mm (shirt) and 3 mm (gaiter, non-even offset); Subdivision 1.
- Weights by Data Transfer from Body.Mesh; Armature modifier on Morgan.Rig.

### Clearance from the skin
- Rest: shell minimum 1.5 mm, gaiter 10 mm, 0 inside.
- Hero pose: gaiter 8.9 mm and 0 inside. The shell has 71 vertices inside, to -15.7 mm, all at the back of the right elbow (see §5).

### Layering in the pose
- Sleeve ends inside the glove cuffs: 0 of 330 (left) and 1 of 322 (right) uncovered.
- Collar under the gaiter: 13 of 287 uncovered, at the back of the neck.
- Shirt tail under the trousers: 19 of 822 uncovered, at the lower back.

### Renders looked at
- `shirt_rest_front`, `_side`, `_threequarter`: a snug long-sleeved shirt with roomier sleeves narrowing to the cuffs, and the gaiter in three rolls.
- `shirt_hero_torso_vest_pair`: the gaiter sits where the drawn one does but is smaller and lower. The torso is right for something the carrier will cover; the knit shows the pectorals through, which the carrier hides.
- `shirt_hero_arm_R_pair` and `shirt_hero_arm_L_pair`: the sleeves follow the drawn arms. They are a little slimmer than the drawn sleeves, which also carry the pauldron and guard bulk.
- `shirt_hero_soldier_full_pair`.

Earlier failures, now fixed:
- The gaiter's Solidify exploded until its rings were smoothed and the offset made non-even.
- The first sleeves were too slim.
- The first gaiter was too small.

## 5. Round 2 (2026-11-14): the gaiter as a cowl

### Gaiter (rebuilt)
1. **The skin under it, on a coherent grid.** For each of 96 meridians round the neck axis (from (0, 12, 1488)
   toward neck03), the same rays: a fan from the axis point 60 mm up (70 degrees below the horizontal up to it, landing
   on the chest, trapezius and upper back), then horizontal rays climbing the axis. The grid is Taubin-smoothed
   before anything is built on it; round 2's first try cast rays per meridian with their own arc lengths and the
   neighbouring meridians disagreed, so the folds came out crumpled.
2. **Arc length s along each meridian**, 0 at the ring 100 mm up the axis, + up. Each meridian runs from the skirt
   edge s_bot (front -120: under the bag top; side -88: under the straps; back -48: under the rear bag) to the
   top edge s_top (front 18: under the chin; side 40: behind the jaw, 12 higher on his left as drawn; back 62).
3. **The folds** are cos² lobes along s on top of the collar allowance (11 on the neck, 10 on the chest): a lip at
   the top edge, the main roll under the jaw (52 proud at the front), a lower roll falling over the collar, soft
   vertical drapes in the front skirt. Their heights vary round the neck (harmonics 2, 3, 5 at 24/14/7 %), their
   positions wander (+-7 and +-4 mm, harmonics 2 and 3), and a crease on his left front (65 degrees) cuts them by
   55 %, so the rolls read as one bunched tube, not as rings.
4. **The folds bulge away from the neck axis**, not along the skin normal: the normals converge in the hollow where
   the neck meets the shoulders, and 50 mm along them folded the surface through itself (the crumpled look of the
   first tries).
5. **Pressed flat under the straps:** wherever a gaiter point would lie outboard of |x| 92 (the strap's inner edge
   less 4 mm, blended over 12 mm), the folds are taken out and the fleece lies at the collar allowance; the straps
   lie on that.
6. Taubin-smoothed, pushed out to 9 mm from the skin; Solidify 3 (non-even), Subdivision 1; weights from the body.

### Shirt
- Tail: below z 1060 the shell is laid on the skin at 2 mm (smoothing had bridged the lumbar hollow, and the
  trousers, which hug it, came through: round 1's clash 13).
- Sleeves: 4 mm more ease on the upper arm, 2 at the shoulder (the drawn sleeves are fuller).
- Collar lowered at the back (1584 instead of 1600) so it stays under the gaiter when the head turns.

### Clearance and checks
- Gaiter: rest 9.0 mm from the skin, hero pose 8.4, nothing inside. Shell: rest 1.5 minimum; in the pose 92 vertices
  inside the arm at the back of the right elbow, as in round 1 (the pose's elbow pinch, unchanged).
- The "gaiter over shell" layering number printed by the script (-49 rest) is a false alarm of the open-shell
  test at the collar's top edge (the gaiter lies above the edge, whose nearest face points the other way); the
  assembly's clash test, which ignores boundary faces, finds no shirt-gaiter clash.

### Renders looked at
- `renders/shirt/shirt_rest_{front,side,threequarter}.png`: a cowl bunched round the neck, the skirt flat over the
  collar to the shoulders.
- Dev loop (scratch, not kept): the gaiter alone with the carrier and head caches, rest views and the hero head
  crop beside the reference, after each change.
- `renders/round_02/head_face_compare.png`, `torso_vest_compare.png`, `turnaround.png` (see carrier.md §6 for the
  integration).

## 6. Still wrong, ranked for round 3

1. **The cowl is still tidier than drawn.** The drawn one is looser: deeper, more irregular folds, the main roll
   overhanging the one below it (a profile curve can bulge but not overhang), and a softer, heavier drape at the
   front into the bag top. A short cloth simulation from this shape (gravity, body collision, pinned skirt) is the
   next step; bake the result and transfer weights as now.
2. **Strap pads and the shirt in the pose:** the pads sink 4 to 7 mm into the shirt and gaiter over the shoulders in
   the hero pose only (skinning; carrier.md §7).
3. **Right elbow in the pose:** round 4 (§7) found it was the crook, not the back, and fixed it by sharing the
   sleeve's weights across the joint.
4. **No folds in the shirt itself:** elbow bunching, the drape under the pauldrons, blousing above the waistband.
5. **No rib shoulder panels, back seam, cuff tab or collar detail; no knit, ripstop or fleece materials.**
6. The sleeve still shows a soft step at the elbow where the upper-arm and forearm sections are made convex
   separately.

## 7. Round 4 (2026-11-15): the right elbow

**What it was.** Rounds 1-3 reported shirt vertices up to 8.3 mm inside the body "at the back of the right elbow" in the
hero pose (91° between the segments; the rest arm is already bent 45°, so the pose adds 44° of flexion). Measured in rest
coordinates, the offending vertices sit at the **crook** (antecubital side, cos −0.99 to the point of the elbow), just
past the joint (arm parameter 1.11-1.18), 19 mm off the skin, with the skin's own weights (forearm 0.90-0.99). A sleeve
skinned like that hinges at the joint: its inside at the crook turns the full 44° with the forearm into the biceps. The
olecranon was never the problem: the sleeve rides 17 mm over it (mean 20) in the pose.

**Fix** (`elbow_blend`, `ELBOW_BAND`, `ELBOW_FRONT`): after `common.bind`, on the crook side of the sleeve and over the
arm parameter band 0.50-1.55 (mid upper arm to a third down the forearm), the sleeve's arm weights (upperarm*, lowerarm*)
are re-shared by the arm parameter, the forearm's share a smoothstep across the band, each segment's groups keeping their
proportions; other bones untouched; vertices with less than 0.3 arm weight (the armpit, the torso) are left. The crook
side is a smoothstep of −cos to the point of the elbow (0 to 0.5): the outer sleeve keeps the skin's weights, because the
forearm guard and the pauldron, rigid on their bones, sit over it (a first version blended all round and pushed the sleeve
4.9 mm out through `Guard.R.Sleeve` and 3.8 mm through the pauldron's lowest tier in the assembly). The cloth at the crook
then turns about half the angle, as a real sleeve's does.

Bands tried, right elbow (vertices more than 0.5 mm inside the posed body / max depth), at round 3's pose (91°), all
round: none 17 / 8.3 mm; 0.70-1.35 21 / 4.4; 0.60-1.45 6 / 2.0; 0.50-1.55 1 / 0.3; 0.40-1.60 1 / 1.2. At round 4's
re-solved pose (96°), crook side only, with the guard and pauldron tested too: **0.50-1.55: 15 / 3.1, armour clear
(kept)**; 0.45-1.45 32 / 9.9; 0.55-1.60 22 / 6.0 and the guard 3.4; 0.60-1.50 13 / 5.9 and the guard 4.7; 0.50-1.80
91 / 9.9 (the forearm's inside then lags into the forearm). An extra 8 mm of ease over the olecranon (the brief's
suggestion) was tried and dropped: it changed nothing at the crook and only bulked the elbow. The left elbow (44°) was
already clear and stays so. Linear blend skinning cannot do better at a 96° elbow with a 19 mm sleeve: the next step is a
corrective (a shape key driven by the elbow angle, or a baked pose correction), not more weight sharing.

**Still inside in the pose:** the front of the right armpit (anterior axillary fold, arm parameter 0.15-0.26, 14 mm
off the skin, upperarm01/02 and spine01 weights): 17-18 vertices to 7.4-8.1 mm, where the arm swings forward and in to
hold the carbine and the sleeve's root folds into the chest. The same kind of fix (sharing the shoulder's weights with
the clavicle and spine over a band) is the next step; it was not in this round's brief.

## 8. Round 5 (2026-11-15): materials

`MATERIALS` in shirt.py (swapped by `common.library_pass`):
- **Torso: `Knit.Jersey.FR`** (new; cotton_jersey's normal at 264 mm), **sleeves: `NYCO.Ripstop.Black`** (new;
  Fabric061 at 64 mm and the 6 mm ripstop grid): a G3-class shirt is FR jersey under the carrier and ripstop on
  the arms. `sleeve_faces()` puts the faces whose centre lies outboard of the shoulder joint (rest x) on the
  sleeve slot. Both at #252525 (just above §3.1's floor for black textiles), sheen 0.04, light dust (0.25).
- **Gaiter: `Fleece.Polyester`** (new; knitted_fleece at 230 mm with its ±6 % luminance high-pass, sheen 0.10,
  dust 0.7 from preset `fleece.toproll`, which carries the lit folds).
- `wear_dust_scale` 1.0 right, 0.9 left.

Renders opened: `renders/round_05/torso_vest_compare.png`, `arm_L_compare.png`, `soldier_full_compare.png`.

Still wrong (materials): the shirt renders brighter than the reference's median (ratio 0.78) although the albedo
is at the textile floor: the dust and sheen lift it and the warm key browns it (session log); the sleeve has no
elbow wear, no seams or panels to break it up; the sleeve/torso split is a plane, not the real raglan seam.

## 10. Round 8 (2026-11-15): the look (critics m9, m50, m48)

- **Near-black, neutral** (m9, m50): the shirt read brown-grey under spec 17's 4500 K key; with the evaluation
  light corrected (scene.py, key 5800 K) the same black reads neutral. Jersey and ripstop #252525 -> #272727 (the
  graded median sat at ratio 1.17 against the reference; now about 1.1), dust 0.25-0.3 -> 0.15 (it greyed the black).
- **Matte** (m48): ripstop roughness 0.70 -> 0.82, specular 0.30, sheen 0.03; jersey 0.86, sheen 0.03.
- **Wear** on the sleeves (`mat_groups.abrasion`): a 6 mm band along the sleeve's own edges (cuffs, panel edges:
  `edge_near`) toward #3c3c3b, and rubbing where the armour's straps and bands lie on the sleeve (contact AO).

Look-loop renders opened (`renders/look/M1`..`M6`): `sheet_torso_vest_graded`, `sheet_arm_L_graded`.

Still wrong: no elbow wear or seams to break up the sleeve; the drawn sleeve shows fold highlights and a ripstop
sheen we do not have at this roughness.

## 11. Round 9 (2026-11-15): sleeves with ease and folds, the back off the shoulder blades (critics m11, m17, m39)

- **Ease** (`SLEEVE`): 16 at the shoulder, 27-29 on the upper arm, 24 at the elbow (round 2: 12-19), then round 2's
  forearm (16 mid forearm, 5.5 at the cuff): a G3-class sleeve is cut full, and the reference's upper arms carry bulk;
  the forearm lies under the guards and the gauntlets (a fuller forearm put the cuff over the gloves: below).
- **The elbow step** (section 6 item 6): the upper-arm and forearm hulls met in a step; the sleeve is relaxed over arm
  parameter 0.70-1.35 (`ELBOW_RELAX`, 40 Taubin passes) before the cuts.
- **The back** (`BACK_SPAN`): above the tuck and below the collar, behind y 15, each section moves out to its convex hull
  plus 3 mm, so the shirt hangs from the shoulder blades instead of showing them.
- **Folds by the cloth solver** (`sleeve_solve`, `SLEEVE_SIM`, `scripts/parts/cloth.py`): each cuff is extended 26 mm along
  the forearm (four rings), and in the solve the extension's end ring is held and pushed back to the cuff line while
  every sleeve vertex carries a weak goal (0.12) whose target slides toward the shoulder by the share of the surplus its
  arm parameter has passed; torso held, shoulder seam half held; colliders the rest skin without the hands; gravity 0.25
  (the rest arm hangs differently from the hero pose's), bending 0.35, friction 15. After the solve the forearm is
  blended back to the unsolved sleeve over arm parameter 1.15-1.45 and the extension dropped, so the solved bunching is
  kept from the shoulder to the elbow only. About 45 s, cached in `cache/cloth/shirt_sleeves_<hash>.npz`; `--no-sim`
  builds without it.
  - Tried: springs' rest lengths from a longer shape key (no effect in Blender 4.5); the end ring alone pushed back 44
    and 34 mm (the forearm tube slid up the arm and telescoped into one ring at the elbow); bending 1.5 (one balloon);
    the whole sleeve solved (round 9's first evaluation: the bunched forearm and cuff came out over the forearm guards,
    256 guard vertices to 24.9 mm inside the sleeve, and over the glove gauntlets, 110 vertices to 24.9 mm).
  - Result, honestly: the surplus gathers as a soft fullness above the elbow with one or two broad folds and a ridge at
    the crook, not the reference's several crisp compression folds; the forearm is the smooth cut tube.

**Girths and ease** (rest, his left arm; girth = hull of the section across the segment; ease p10 / median / p90 mm):

| | Round 9 | Round 8 |
|---|---|---|
| Upper arm girth (mid humerus) | 468 | 423 |
| Elbow girth (body 260) | 427 | 390 |
| Mid-forearm girth | 274 | 272 |
| Upper arm ease | 24 / 28 / 29 | 17 / 18 / 18 |
| Elbow ease | 11 / 20 / 32 | 18 / 20 / 23 |
| Forearm ease | 15 / 16 / 17 | 15 / 16 / 16 |
| Upper back ease (z 1300-1450, abs(x) < 140) | 7 / 9 / 19 | 5 / 5 / 6 |

Chest girth (hull, z 1360) 1060 (1048); waist 818 (780). Clearance: rest minimum 1.4 mm, nothing inside; hero pose 44
vertices inside, to 16.5 mm, at the right armpit (posed (-248, 137, 1440); round 8: 23 to 14 mm there), the round-4
problem (section 7), a little worse with the fuller upper sleeve.

Renders opened: `renders/shirt/shirt_rest_threequarter.png` and `shirt_hero_arm_L_pair.png` after each solve, and the
`--no-sim` build (which showed the elbow step was the hulls', not the solver's).

**Round 9's evaluation** (`renders/round_09/`: `soldier_full_compare`, `torso_vest_compare`, `turnaround`): the upper arms
now carry the bulk the reference shows and the back no longer shows the shoulder blades; the sleeves are still smooth
at hero scale (the bunching above the elbow is soft and mostly under the armour's bands), so m17 "no folds at elbow or
shoulder" is only partly answered. Clashes back to round 8's after the forearm fix: gloves in shirt 3 vertices (round 8:
3), shirt-armour 476 to 6.7 mm (232 to 4.1; the guards' foam on the fuller elbow end), body-shirt 33 to 16.5 at the right
armpit (14 to 14.1). Next: the elbow-crook folds by a pose-driven corrective (solve the sleeve once in the hero arm pose
and store the difference as a shape key on the elbow angle), and the armpit (section 7).

## 12. Round 10 (2026-11-16): slack instead of inflation, the back, the gaiter (critics m8, m2, m32, m30, m34)

**Sleeves** (m8: "a wetsuit over bloated upper arms"; m2: stockier than the lean drawn man).
- Round 9's 27-29 mm of even ease read as inflation. `SLEEVE` now runs 14 at the shoulder, 20-21 on the upper arm and 21 at
  the elbow (round 9's table is kept as `SLEEVE9`).
- The slack is shown as gathers instead (`SLEEVE_FOLDS`, `sleeve_folds()`, after the solve). Ridges run every 30 mm along
  the upper arm, tilted round it (9 mm drift with the angle, plus two harmonics of wobble), with Gaussian crests and the
  mean taken back out so they do not inflate. They are 4.2 mm deep at the crook and 1.4 on the outer arm under the armour,
  faded in from the shoulder (arm parameter 0.28-0.46) and out into the elbow (0.96-1.08). The two arms are phased
  differently.
- The solve's lift is 26 -> 20 mm. With the slimmer upper sleeve the 26 mm surplus gathered at the elbow instead and pushed
  the right sleeve 10 mm out through the elbow pad's lower strap (`ElbowPad.R.Strap.Down` in the shirt, 44 vertices,
  10.1 mm). At 20 it is gone.
- Ease (rest, his left arm, shell to skin, p10 / median / p90 mm; new `sleeve_measure`). Round 9's figures from section 11
  are in brackets:
  - upper arm 12 / 18 / 24 (24 / 28 / 29);
  - elbow 23 / 30 / 37 (11 / 20 / 32);
  - forearm 15 / 16 / 17 (15 / 16 / 17).
  - The elbow band measured here (arm parameter 0.96-1.04, all round) takes in the bunching at the crook, so the two
    rounds' elbow figures are not quite the same measure.
- The girths `sleeve_measure` prints (upper arm 466, forearm 335) are NOT comparable with section 11's 468 / 274. Its
  selection (within 85 mm of the bone axis) still takes in torso vertices beside the hanging rest arm; fix it before using
  it.

**m30, the left elbow's "hard horizontal ridges"**: in `renders/round_10/arm_L_parts.png` these are the armour's elbow-pad
straps (`ElbowPad.L.Strap.Up` / `.Down`), black like the sleeve, not the sleeve. It is the armour's to fix (a lighter or
thinner strap, or one that sinks into the cloth). The sleeve under them folds softly.

**The back** (m8, m32: the back muscles show through). `BACK_SPAN`:
- the hull span starts at z 1085, just over the trousers' waistband top at the back, ramped over 50 mm (was 1080 over 60);
- ease 3 -> 6 mm;
- the spanned back is relaxed with 24 Taubin passes, so the lats and the spine's columns stop showing as relief;
- the tuck below 1060 is laid on the skin as before.
- A first try from 1050 stood 4.5 mm proud of the trousers' waistband: 84 vertices of the trousers inside the shirt in the
  pose. That clash is gone now.
- Ease (rest, |x| < 140, behind): upper back z 1300-1450 9 / 12 / 22 (round 9: 7 / 9 / 19); lower back z 1090-1200
  6 / 18 / 23.
- The scratch back view shows the lower back between the carrier and the belt smooth; the spine's groove is gone.

**The gaiter** (m34: a smooth cone sitting low; the reference bunches up under the jaw).
- The top edge is higher: front, side and back 18 / 40 / 62 -> 33 / 54 / 68 mm of arc above the neck's base ring.
- The rolls are bigger: lip 26 / 20 / 16 -> 30 / 24 / 16; main roll 52 / 36 / 24 -> 60 / 44 / 26 and 30 -> 32 wide; lower
  roll 18 / 14 / 8 -> 24 / 18 / 9.
- The rolls are less even: wobble harmonics 0.24 / 0.14 / 0.07 -> 0.30 / 0.20 / 0.10.
- Height 1473-1666 (1473-1660). Clearance to the skin: 9.0 rest, 7.9 posed, nothing inside.

**Integration** (scratch assembly, `clash_report` / `standoff_report`; round 10 in brackets):
- body-shirt: 49 vertices to 14.6 mm at the right armpit's front, (-250, 137, 1440) (33 to 16.5). The round-4 problem
  (section 7); the count rose with the slimmer sleeve root.
- shirt-carrier: the gaiter in the strap pads 6.7 (6.4) and the right pad in the gaiter 8.0 (7.8), both the carrier's.
  - A new flag, `Carrier.Front.Bag` in `Shirt.Shell`, 44 vertices to 23.3 at (-5, -71, 1318), is false: the bag's inner
    face lies 20-23 mm OUTSIDE the posed shirt there (signed distance +23.3 to the shirt, +29 to the skin). Round 10's
    assembled file has the same geometry at that spot.
- shirt-armour: 101 to 1.9 (97 to 2.6).
- shirt-gloves: 3 to 20.9 (the same).
- shirt-trousers: none.
- The carrier and armour rebuilt on the new shirt.

**Renders opened**:
- `renders/shirt/shirt_hero_arm_L_pair.png`, `shirt_hero_torso_vest_pair.png`;
- the scratch turnarounds;
- `renders/look/tr10_new`, `tr10_final`: `sheet_arm_L_graded`, `sheet_arm_R_graded`, `sheet_torso_vest_graded`,
  `head_face_cycles` (the head there is the head agent's work in progress).

What they show: the upper sleeves are slimmer, and the gaiter rises to the jaw in a bunched roll. The new gathers do NOT
read at hero scale: 2.5 mm crests on matte near-black cloth under the armour bands.

## 13. Still wrong, ranked for round 11

1. **The sleeves still read smooth.** The gathers need 2-3 x the depth, or real buckling from a hero-arm solve (a pose
   corrective; section 11's plan). The sleeves also need the ripstop's sheen on the crests to show them.
2. **The right armpit in the pose** (49 to 14.6 mm): share the shoulder's weights with the clavicle and spine (section 7).
3. **The torso front** is still shrink-wrapped over the pectorals and abdomen (hidden by the carrier, but not in the
   turnaround's sides).
4. **The gaiter** is a procedural profile. It is higher and fuller now, but its rolls do not overhang or fold over each other
   as the drawn fleece does.
5. The sleeve girth measure (section 12) takes in torso vertices.
