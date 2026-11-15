# Armour

Build: `"$SGT_BLENDER" -b --python scripts/parts/armour.py [-- --no-render]` (about 100 s with renders; the round 2 plates use fine grids). Output:
`cache/parts/armour.blend` (collection `Part.Armour`), `cache/parts/armour.json`, `renders/armour/*.png`,
`renders/armour/armour_check.json`.

## 1. What it is (real identity and dimensions)

No issued military pauldron exists; the classes follow take 1's spec 12 §3.1.

| Piece | Built (mm) | Class / source |
|---|---|---|
| Pauldron tier 1, cap | round 2: 150 wide at the top, 122 at the lip, lower corners chamfered 28, upper corners rounded 14; spans 104 deg (-54..+50) about its centre direction at a mean radius of 86 from the shoulder joint (about 155 developed); wall 3 with a rolled rim bead 1.1 proud, 4 wide; two 7 mm dome rivets; inner face 12 over the shirt, 2 over the carrier's strap pads, 1.5 over tier 2 | sport shoulder cup (motocross / lacrosse class), spec 12 §3.2 |
| Tier 2, mid plate | 118 arc x 90 tall (round 2: s 76-166 below the joint, 12 higher, under the cap's lip), wall 3, rim bead 0.9, recessed panel 70 x 28 x 1.5 | spec 12 §3.2 (80 tall, arc 100) |
| Tier 3, bicep band | 200 deg x 48 tall (s 190-238), wall 2.5, rim bead 0.8, mid groove 1 deep; black elastic closing the medial 160 deg; silver cam buckle 30 x 36 x 7 with a 24 x 26 lever at the front end | spec 12 §3.2 (s 214-262 raised 24 so it clears the forearm guard at 102 deg elbow flexion) |
| Emblem (left) | shield 50 x 95, 1 mm plate 1.5 proud of the cap | drawn; US practice: unit insignia on the left |
| IR strobe (left) | 30 x 45 x 18 on tier 2's rear edge | Adventure Lights VIP class |
| Forearm guard | round 2: neoprene sleeve 3 mm, d 52-258 from the elbow (its proximal edge 40 lower on the flexor side, d 92); four straight plates, each lapping over the next with a flared lip: elbow band d 57-90 (170 deg, its edge receding 18 at the sides, lip +6), upper plate d 84-158 (196 deg, lip +7), lower plate d 150-228 (196 deg, lip +4), wrist band d 222-254 (226 deg); walls 2.5-3, rim beads 0.9, a 14 mm rib 2.5 proud and two 1.2 mm grooves on the upper and lower plates; 4 mm foam under each; inner faces 8 over the straight surface; straps 25 x 1.4 round the flexor side at d 100 and 238 with 32 x 26 ladder-locks | Hatch Centurion class riot guard, 220-260 long (spec 12 §3.3) |
| Elbow cap | fin 14 x 40 x 5 on the lateral epicondyle, pad 30 x 28 x 6 just below | drawn (spec 12 D6: no real product this small) |
| Knee pad | round 2: octagonal cap 160 x 190 in two lames (main v -95..48, upper lame v 36..95 over it), 3.5 wall, 20 mm dome over the patella, a 12 mm frame with a 1.2 rim bead and the centre panel 2 below it, a centre ridge on the main lame; padded base 7 thick, 12 larger all round; 38 mm strap round the back of the knee with a 50 x 32 ladder-lock and a tan tail on the medial side; red tab 30 x 14 x 3 on the lateral edge | Alta AltaFlex / Crye AirFlex class (Alta 229 x 165 x 38) |

Round 6 (section 9) supersedes this table for the forearm guards (two plates), the elbow (a pad, not the fin and
pad chips), the knee pads (one faceted cap 150 x 164) and the pauldron cap's pad (7 mm over a 6 mm foam liner).

## 2. What the reference shows (crop_arm_*, zoom_armour_*, crop_legs_knees)

Worn tan-grey moulded shells (the left side reads blue-grey under the cool light: one colour, spec 12 D1). The
cap is a bent plate over the front of the shoulder with the shield emblem; below it a plate with the strobe at
its rear edge; a tan band above the elbow; a small fin on the left elbow; segmented forearm guards from elbow to
glove cuff; external hexagonal knee caps on black bases, strap and buckle on the medial side.

## 3. Departures and why

- Tier 2 is 9 mm longer and 15 mm wider and tier 3 sits 24 mm higher than spec 12, see the table.
- The forearm guard's elbow band is 170 deg, not 230, with its proximal edge receding 18 mm at the sides, and the
  upper strap crosses the flexor side at d 100, not on the elbow band: at the hero pose's 107 deg elbow anything
  on the flexor side above d 90 meets the biceps.
- The forearm guard is four plates (spec 12: three): the main plate is split so the two halves can ride the two
  forearm bones (lowerarm01, lowerarm02) and the pronation twist opens a lap instead of bending a plate.
- The knee base is soft (neoprene, bound by weights to follow the knee pocket); only the cap is rigid.
- Round 2: the pauldron cap is turned back at rest (`CAP_FWD` -0.25, `CAP_UP` 1.3), because the hero pose turns
  the upper arms in (left about 40 deg): posed, its centre faces out, up and a little forward on the outside of
  each shoulder, as drawn. It is still rigid on upperarm01. Bound to shoulder01 (tried) it stayed at the rest
  pose's abduction and stood off the adducted arm like a wing.

## 4. Round 1 (2026-11-14)

- Every shell is a slab over a smooth radius field round a limb axis (`gear_common.LimbSurf`/`Field`): rays from
  the axis outward through the shirt and glove caches (walking through a garment's solidified thickness), the
  field smoothed and kept outside the raw surface. The cap is a gnomonic patch of rays from the shoulder joint.
  The knee pads use rays inward onto the trousers' knee pocket.
- Fitted to the shirt (sleeves) and glove caches and to the trousers cache with its knee pocket.
- Rigging, rigid pieces skinned 100 % to one bone (`gear_common.rigid_bind`): cap, emblem, tier 2 and strobe to
  `upperarm01`; tier 3 and its elastic to `upperarm02`; elbow band, main plate and foam to `lowerarm01`; wrist
  band to `lowerarm02` (so the pronation twist carries it); elbow fin to `upperarm02`, pad to `lowerarm01`; knee
  cap to `lowerleg01`. Soft (weights from the body): the guard sleeves, the knee bases and straps. The brief asked
  for bone parenting; single-bone skinning is the same motion, survives `common.save_part`/`load_part` (which
  only restores Armature modifiers and plain parents) and exports to glTF as skinning.
- Colours: shells #7b7064, knee cap #6a6158, black #1d1c1b, emblem #a9b3bd, strobe #9fb0bf.

Renders opened: `armour_rest_{front,side,threequarter}.png`, `armour_hero_arm_R_pair.png`,
`armour_hero_arm_L_pair.png`, `armour_hero_legs_knees_pair.png`, `renders/round_01/gear_hero*.png`.

Check (`armour_check.json`):
- rest: no overlap with body or clothing; gear/gear only at designed joints (cap lip over tier 2 66-68, tier 3
  band edge on its elastic 22, knee base under its strap 60, elbow pad on the sleeve 14-16, strobe on tier 2 20);
- posed: the right guard's sleeve and plates cross the shirt at the inner elbow (sleeve 558 shirt triangles, body
  96) because the elbow folds 102 deg; the carbine's stock crosses the right guard (sleeve 113, main plate 85) but
  reaches only 0.5-0.7 mm into it; the stock is 15 mm inside the right arm's skin itself (pose, not armour);
  main and wrist plates overlap 30-38 under pronation.

Round 1 still-wrong list (done in round 2 except the knee height):

1. **The forearm guards are fat cones**: their radius follows the clothed forearm near the elbow, so the elbow
   end flares; the drawn guard is a straighter, segmented sleeve with a longitudinal rib and grooves.
2. **The pauldron cap is too small and too close in the hero frame**: the drawn cap stands out further and
   covers more of the shoulder top; tier 2 is a curved strip, not the drawn plate with a recess and vents.
3. **No details**: rim beads, rivets, slots, the knee caps' frame steps and slots, buckles, ladder-locks, the
   red tab, the X-star on the emblem.
4. **Knee pads sit higher than drawn**: the drawn thighs are short (CLAUDE.md, accepted), so the overlay misses.
5. **Right elbow fold**: soft sleeve and shirt cross at 102 deg; needs corrective weights or a split sleeve.

## 5. Round 2 (2026-11-14)

Brief: straight segmented forearm guards starting 25 mm lower that clear the right elbow's ~100 deg fold; a
larger pauldron cap on the outside of the shoulder, over (and clear of) the carrier's strap pads; the next
level of form (rims, straps and buckles, the knee caps' real shape).

- **Forearm guards** (`StraightSurf`, `GUARD`): per angle round the forearm, the shell's radius is a straight
  line along the forearm fitted to the clothed samples (shirt sleeve, glove cuff) and raised until nothing is
  outside it, per plate. Four plates (elbow band, upper, lower, wrist band) built from the wrist up, each with a
  flared lip that laps over the plate below (lifts 4-7 mm only over the last 10 mm; laying each whole plate
  over the next stacked 25 mm at the elbow, the first try). The elbow band now starts at d 57 (round 1: 32),
  spans 170 deg with its edge receding 18 mm at the sides; the sleeve starts at d 52 on the back of the forearm
  and d 92 on the flexor side and is weighted with the upper-arm bones folded into lowerarm01, so it moves with
  the forearm and does not fold into the elbow; the upper strap crosses the flexor side at d 100, below the fold.
  Upper plate and elbow band on lowerarm01, lower plate and wrist band on lowerarm02. Rib, grooves, rim beads,
  foam step, two straps with ladder-locks (`lib.gear_hardware.ladder_lock` 32 x 26).
- **Pauldron cap**: 150 / 122 wide, 104 deg tall (-54..+50) about a centre `CAP_UP` 1.3 x up + down the arm,
  turned back (`CAP_FWD` -0.25): the hero pose turns both upper arms in (the left about 40 deg), so posed the cap
  faces out, up and a little forward on the outside of each shoulder (posed centre L about (0.65, -0.65, 0.4),
  R (-0.75, -0.4, 0.5)). It is fitted over the shirt (arm and torso regions), the carrier's `Carrier.Strap.*`
  objects (2 mm, from `cache/parts/carrier.blend`, so armour now builds after the carrier: `assemble.py` DEPS got
  "carrier" for armour) and tier 2 (1.5 mm). Rolled rim bead, two dome rivets, emblem as before. A try with the
  cap on shoulder01 left it at the rest pose's abduction, standing off the adducted arm like a wing.
- **Tiers 2 and 3**: tier 2 moved 12 mm up (s 76-166) under the cap's lip, rim bead and the recessed panel; tier 3
  rim bead, mid groove and a silver cam buckle at its front end.
- **Knee pads**: an articulated cap: main lame (v -95..48) with a 20 mm dome over the patella, a 12 mm stepped
  frame with a rim bead, the centre panel 2 mm down and a centre ridge; an upper lame (v 36..95) lapping over it;
  a 7 mm padded base; the strap's ladder-lock and tan tail on the medial side; the red tab on the lateral edge.
- New shared helpers in `gear_common.py` (appended, nothing else changed): `hw_object` (a gear_hardware piece as
  a world-space object with a flat material), `tube`, `edge_profile` (the rim-bead thickness field),
  `smoothstep`.

Renders opened: `renders/armour/armour_hero_{arm_L,arm_R,legs_knees,soldier_full}_pair.png` (three builds),
`armour_rest_threequarter.png`; round 2 assembly `arm_R_compare`, `arm_L_compare`, `legs_knees_compare`,
`torso_vest_compare`, `soldier_full_compare`, `belt_hips_compare` and `_overlay`, `turnaround.png`.

What they show: the left forearm guard now lies on the drawn guard (overlay) as four straight shingled shells
with ribs; the right guard, seen end-on, reads as the drawn stacked rings. The caps sit on the outside of the
shoulders: the left cap with its emblem where the drawn one is, the right one as an outboard wedge, close to the
image's edge-on view. The knee caps show the two lames and the frame at close range but read as flat tan plates at
full frame; the right one faces out with the turned-out right leg.

Clashes (`renders/round_02/clashes.md`, hero pose of 19:01): body-armour none (round 1: 32.9 mm at the right
elbow); carrier-armour none (1.1); trousers-armour none (1.0). Left: Guard.R.Elbow 11.9 mm inside the shirt at
the right elbow (-366, 60, 1286), where the shirt itself is 18.7 mm inside the body (the shirt's elbow pinch);
Guard.R.Lower 10.9 mm into the carbine's stock (the pose: the stock lies inside the right forearm).

## 6. Still wrong, ranked for round 3

1. **The right elbow**: the shirt's sleeve collapses into the 107 deg fold and the elbow band sits under its
   bulge (11.9 mm). Needs the pose/body corrective at the elbow (or shirt weights); then recheck the band.
2. **The pauldron caps are smooth cups, not the drawn bent plate**: the drawn cap has a flat outer face, a sharp
   30 mm bend to a short top flange and a strap tab slot; ours follows the shoulder's rounded field. A
   developable (two-facet) surface would read better. The links (elastic straps) between cap and tier 2 are
   missing; the cap and tier 2 ride one bone, so a link can now be rigid too.
3. **Knee caps read flat at full frame**: the dome is lost in the pocket's own curve; the drawn cap is a
   hexagon with a strong forward bulge (30 mm) and a dark recessed centre. Slots, holes and the boss are missing.
   The right knee cap faces out with the turned-out right leg (pose); the knee pads sit higher than drawn (the
   accepted thigh length).
4. **Forearm guards**: the elbow band is a plain ring; the drawn band has a cam buckle and hook; the left guard's
   grey window and the stencils are missing; colour is uniform (the materials round).
5. **Tier 2's vents and window, the strobe's clip, the X-star on the emblem** are still missing.

## 7. For integration

- The carbine's stock lies inside the right forearm (Guard.R.Lower 10.9 mm, the skin and shirt more): the pose
  re-solve should take it out; the guard then needs about 12 mm of the skin clear.
- `armour.py` reads `cache/parts/carrier.blend` (strap pads) and so must build after the carrier; DEPS updated.
- Built on the base of 19:00 and hero_pose.json of 19:01; the pose agent's re-solve (pose.py of 20:18) was not
  yet in the assembly. If the right elbow opens to 90-100 deg the guard only gets easier; if the right thigh
  turns in, the belt's right rig theta must follow (belt.md).

## 8. Round 5 (2026-11-15): materials

`MATERIALS` in armour.py (swapped by `common.library_pass`):
- **`Polymer.Painted.Armour`** (new, `painted` builder in `mat_hard.py`) on the pauldrons, guard plates and
  bands (`Shell`) and the knee caps (`Knee`). Reading of the reference (it supersedes spec 16's
  Polymer.Tan.Painted, D8): FDE-moulded shells field-painted a dark grey, worn back to the tan on the rims, in
  chips, and on the knee caps' raised frames. The paint (#454648) carries ChatGPT's R004 worn-paint swatch (made
  seamless, box-projected at 150 mm, 60 %: scratches, tan specks, uneven cover) and a 35 mm mottle. The rims are
  found by a Bevel node (2.5 mm; knee 3.5 mm) against the TRUE normal, because the plates' bevelled,
  weighted-normal edges already round the shading normal and the library's MG.Mask.EdgeBevel (which compares with
  it) saw nothing there. Chips are a noise above a 1.5 % cover (knee 4 %) gathered in patches; the substrate is
  tan #7a705e, 0.08 mm lower, rougher. The knee caps' frames are a point attribute `paint_wear` written from the
  slab's own grid (`frame_wear()`: 1 within 9-12.5 mm of the outline), worn at 0.9, broken by a 12 mm noise. Dust
  from preset `armour.top` (0.5; knee 0.6), grime in the slots.
- **Emblem: `Decal.Emblem`** (new, `decal` builder): a brushed blue-grey anodised plate (F0 0.14-0.19) with
  ChatGPT's R003 mask thresholded (0.30-0.42) as a light grey dielectric mark on `UV.Decal`, a planar 0-1 UV from
  the plate's principal axes (`decal_uv()`: v up, u to the right seen from outside, never mirrored); the emblem
  kept at its aspect at 92 % of the plate's width, its point 12 % above the plate's.
- **Strobe: `Lens.Strobe.Polycarbonate`** (frosted, transmission 0.35). Sleeves, bases, straps:
  `Neoprene.Black`; foam `Foam.ClosedCell.Black`; rivets `Metal.Gunmetal`; the cam buckle a brighter gunmetal;
  the red tab `Polymer.Black.Smooth` recoloured #7a3f42; the strap tails `Webbing.Nylon.Coyote`.
- `wear_dust_scale` 1.0 left, 0.85 right.

Renders opened: `renders/round_05/arm_L_compare.png` (the emblem reads: chevron and X on the blue-grey plate),
`arm_R_compare.png`, `legs_knees_compare.png`, `torso_vest_compare.png`.

Still wrong (materials):
1. The drawn plates read lighter and greyer on their worn faces, with broad pale rims; ours are darker with fine
   specks and narrow rims (a rim is only as wide as the bevel radius).
2. The R004 tan specks and the dust drift read as a fine speckle at hero scale; the reference's wear is coarser.
3. The emblem's outer triangle paints a light outline inside the plate's rim; on the drawn plate only the X and
   chevron are light. A mask without the outline (a follow-up request) would fix it.
4. The strobe is a frosted box: no body, no clip.

## 9. Round 6 (2026-11-15): form fixes after the first whole-soldier critic round

Critic items (notes/critic/soldier_r5/tally.md): m7/m10 pauldrons as flat cards standing off over dark gaps;
m17/m25/m28 forearm guards as telescoping rings crossing the right elbow crease; m22 the left elbow pad missing and
the left guard short of the wrist; m33/m2/m29 knee pads as tall flat plates, the right one standing off the outer
knee and gaping at the top; m36/m44 chips and silver clips hovering off the elbows and bands. Evidence: the
`ref/zoom_armour_*` and `zoom_arm_*` crops and take 1's spec 12 §2-§3 (cap seat on a 6 mm foam pad at shirt + 0.2;
guard plates over sleeve + foam; knee cap forward bulge 30, frame 12 with slots).

**Causes of the floating bits.**
- The elbow "chips" (m36) were round 1's lateral elbow fin and pad, rigid boxes seated 3 mm off the sleeve on two
  different bones: they hovered at every elbow angle. Replaced by a real elbow pad (below).
- The silver clips (m44) were the bicep bands' cam buckles, 3-4 mm off the band. Now a flat gunmetal ladder-lock
  (30 x 24 x 2.6) lying on the band's end, the elastic through it.
- The knee caps were rigid on `lowerleg01`: wherever the knee bent or the shin twisted against the thigh (the hero
  pose turns the right leg out), the cap swung off the trousers' knee pocket, and the separate upper lame flared off
  the thigh (the "empty scoop"). Now one cap, **mounted on the skin at the kneecap** (`gear_common.mount_bind` on
  Body.Mesh), so it seats on the kneecap whatever the leg's turn.

**What changed.**
- **Pauldrons**: the cap's pad 12 -> 7 mm, filled by a 6 mm foam liner (`Tier1.Foam`); its top flange stops at -40 deg
  (was -54: it reached over the carrier's strap pad and lifted the whole cap); the field smoothed 4 times (was 10:
  that flattened the cup into a plank); a 25 mm webbing link from the cap's top edge up over the strap pad
  (`Tier1.Link`). Tier 2: pad 6 -> 4.5 over a 4 mm foam liner, arc 118 -> 140 mm (wraps the deltoid), and a 20 mm
  elastic strap round the inner arm (`Tier2.Strap`).
- **Forearm guards, a gauntlet**: two plates instead of four rings: a long shaped main shell d 96-214 over the outer
  160 deg of the forearm, its proximal edge receding 30 mm at the sides (a rounded tongue toward the elbow), rib
  and grooves; a wrist plate d 204-258 (150 deg) under its lip down to the glove cuff; the sleeve 4 mm (was 3),
  from d 84 (124 on the flexor side), so nothing lies above d 84 and nothing crosses the elbow crease; straps at
  d 122 and 240. Plates, foam and ladder-locks mounted on the forearm's skin at their centres (they follow its
  twist).
- **Elbow pads, both arms** (the reference has one on the left, m22): a domed cap 70 x 80 (3 mm wall, rim bead,
  recessed centre) on a 4 mm neoprene base, centred on the point of the elbow a little to the outside, with
  18 mm straps round the upper arm 52 mm above the joint (on the flexed right arm only round the back and sides,
  its ends in the fold) and round the forearm 74 mm below it. Cap and base are
  soft-bound (per-vertex weights): mounted as one piece the first try rotated with half the right elbow's 107 deg
  fold and stood off it at both ends.
- **Knee pads**: a faceted dome 150 x 164 (was 160 x 190 in two lames): planar facets (sides, top, bottom) rising
  22 mm to a flat central plate, the 12 mm frame with its rim bead, the centre panel 2 mm down with the ridge, three
  18 x 5 slots a side in the frame; the padded base follows the dome (the foam a hard cap sits on), so the cap lies
  on it; the red tab lies on the lateral facet; the ladder-lock lies on the strap and is mounted on it.

Materials: new objects use existing slots (foam liners `Armour.Mat.Foam`, link and straps `Armour.Mat.Black`, the
ladder-lock `Armour.Mat.Metal`, the elbow cap `Armour.Mat.Shell`); `Armour.Mat.Silver` is now unused. **MATERIALS
table not edited.**

**Renders opened** (renders/round_06/): `arm_R_compare`, `arm_L_compare`, `arm_R/L_parts`, `legs_knees_compare`,
`hands_rifle_cycles`, `soldier_full_compare`, `turnaround`. What they show, honestly:
- The pauldron caps now hug the deltoid as curved cups over their foam (no dark gap), the left with its emblem; the
  mid plates wrap the arm; the bicep bands carry a dark ladder-lock instead of the silver block.
- The left forearm guard runs from below the elbow to the glove cuff as a long shell with a rounded tongue toward
  the elbow and a wrist plate under its lip; the elbow pad shows as a dark oval cap on the outside of the elbow,
  edge-on, close to the drawn one.
- The right forearm guard, seen nearly end-on, still reads as a broad cuff in two stacked segments: two plates are
  better than four rings, but from this camera any shell round the forearm shows its two edges.
- The knee caps read as faceted domed caps with a central plate, the right one seated on the knee and facing his
  right with the turned-out leg (m16, the pose's). They still look a little pillow-like (rounded dome, soft facets).
- The arms carry many bands (tier 2 strap, tier 3 band, the elbow straps): busy in the parts colours, nearly
  invisible black on black in Cycles.

**Stand-off check** (`renders/round_06/standoff.md`): no armour object flagged (round 5: both pauldron caps and mid
plates, both knee caps, the left knee lame and both elbow pads).

**Clashes** (`renders/round_06/clashes.md`): `Guard.R.Wrist.Foam` 5 mm into the right glove's cuff shell and 3 mm into
the shirt (the wrist plate laps over the cuff and its foam lies inside the cuff shell; hidden); the carbine's stock
0.7 mm into the right guard's sleeve. The first try's full elbow straps went 13-15 mm into the shirt at the flexed
right elbow; the right upper strap now leaves out the crease (its ends lie in the fold).

## 10. Still wrong, ranked for round 7

1. **The right forearm guard from the hero camera** still reads as a cuff of rings; a more sculpted main shell
   (a raised spine, a flared lower edge, an asymmetric outline) and a single strap would help more than plate count.
2. **Knee caps**: facets too soft (the softmin blend, k 0.05) and the dome too round; the drawn cap has crisp
   bevelled facets, slots and a D-slot, and a darker pitted centre. Size 150 x 164 against take 1's measured
   160 x 190 (the critics read the old 190 as too tall; revisit once the pose turns the right leg in).
3. **Bands on the arms**: the tier 2 strap and the elbow straps add rings; consider black elastic hidden under the
   plates and keep the bicep band as the only visible ring.
4. The elbow pad is soft-bound: it follows the skin, so the cap bends a little over the flexed right elbow.
5. Tier 2's vents, the strobe's clip and the emblem's outer outline are as round 5 left them.
