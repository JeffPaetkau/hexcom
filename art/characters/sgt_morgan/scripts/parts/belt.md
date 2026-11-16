# Belt

Build: `"$SGT_BLENDER" -b --python scripts/parts/belt.py [-- --no-render]` (about 25 s; round 2 about 40 s). Output:
`cache/parts/belt.blend` (collection `Part.Belt`), `cache/parts/belt.json`, `renders/belt/*.png`,
`renders/belt/belt_check.json`.

## 1. What it is (real identity and dimensions)

| Item | Built (mm) | Class / source |
|---|---|---|
| Rigger belt | round 9: a 50 x 9 padded battle-belt sleeve over the 44.5 x 5.5 rigger belt; round 10: cinched, each of its 5 rows on its own section's hull 0.6 over the trousers (inner girth 968; 1021 when every row took the widest), top 3 mm under the trousers' waistband top (front z 1047), in the trousers' tilted waist plane | HSGI Cobra 1.75 in class (spec 14 §3.1) |
| Buckle | 38 x 10 x 58, 30 mm to his right of centre front | AustriAlpin Cobra FC45 (datasheet 58 x 38 x 10) |
| Hangers | 38 x 1.6 webbing, coyote (right), black (left) | spec 14 §3.2, D11 |
| Right platform | round 10: 144 x 158 x 8 on the OUTER front of the thigh, 26 deg from its front toward the outside (round 2-9: 158 x 180 at 12 deg inside; round 1: 28 outside), corners r 15, a 12 mm bound edge, top z 832 (rest), 6 over the trousers; straps at z 796 and 728 | HSGI / Blackhawk Omega class leg rig (spec 14 §3.3) |
| Right thigh straps | 38 x 2 at z 792 and 716 (round 2), 2.2 over the trousers; 50 x 32 x 3.5 ladder-locks on the running ends just inboard of the platform | spec 14 D10, §3.2 |
| Twin rifle-mag carriers | round 10: Cordura bodies 68 x 34 x 122 (soft, `softgear.soft_pouch`: open top with a bound mouth, the magazine's 2 mm bulge, piped seams; charcoal 500D) at u -36 / +36; round 9: 70 x 36 x 122 polymer boxes, round 2: 76 x 42 x 140; body top 15 below the platform top; tan plates 47 x 128 x 3 with three 25 x 6 slots (45, 73, 101 below the top) on a 1.6 spacer; 8 mm dome tension screw; PMAG tops 66 x 25 standing 53 proud with a 70 x 29 floor plate; 4 mm shock-cord loop over each magazine; two cord tails 52 long with 8 x 16 tan cord ends under the outer carrier; both turned 65 % toward the platform's centre normal so they face one way | HSGI polymer TACO class (spec 14 §3.4, D4, D5) |
| Left platform | round 2: 132 x 200 x 8, top z 878, at 30 deg (round 1: 176 wide at 58 deg); strap at z 702 with its ladder-lock at the medial front (-30 deg) | spec 14 §3.5 |
| Left double mag pouch (round 6) | two flapped cells 64 x 38 x 172 side by side at u -34 / +34 on a 148 wide platform; round 10: soft Cordura round the magazine (3.5 mm bulge, rounded bottom), the flap draped over the magazine top and 48 down the front with a bound edge, a tab with a dark plate, two 25 mm webbing bands following the face (round 6-9: an L flap of two blocks, a snap, flat rows); olive | drawn tall double mag pouch (replaced round 2-5's frag pouch and hard case) |
| Right front hip pouch (round 6) | 70 x 36 x 118 flapped pouch on the belt at theta -62, hung tilted to the hip; round 10 soft, as the left cells, one band | drawn above the right thigh rig |
| Holster | 54 x 42 x 182 (round 9), open mouth, 2.5 walls; round 10: at 115 deg round the belt (122 before), hung 32 mm lower (a mid-ride drop), its back bent onto the hip within 34 mm (22); hung tilted to the hip, bound by weights | Safariland 6378 ALS class for a P226 |
| P9 | slide 196 x 34 x 30 muzzle down in the holster, grip 105 x 48 x 32 rearward above the mouth, raked 8 deg (14 before) and turned toward the body about the holster's axis until its middle and end lie nearest the hip (round 10: 30 deg, the search's limit) | SIG P226 class (consolidated analysis: 196 x 140 x 38) |

## 2. What the reference shows (crop_belt_hips, zoom_belt*_*)

The belt mostly hidden behind the magazine and the left hand; on the right thigh two tall black carriers with
tan face plates seen face-on, a tan hanger and two black straps with gunmetal ladder-locks across the front of the
thigh; on the left a narrow olive/grey block at the hip; no pistol or holster anywhere.

## 3. Departures and why

- **The P9 and holster are on the belt at the right rear hip, not on the thigh platform.** The brief asked for the
  holster on the thigh platform, where the image shows them; the image shows no holster or pistol (take 1's gear
  inventory and consolidated analysis say so too), and the right platform carries the two rifle-magazine carriers
  the image draws. A drop-leg holster would replace the carriers. The belt holster at the rear hip is hidden from
  the hero camera. If the P9 must show, decide which item it replaces; that is a question for Jeff.
- **Belt height**: at the real waist over the trousers' waistband (front top z 1047), not the drawn line 100 mm
  lower (take 1 D1; the drawn legs are short).
- **Platforms 25 mm shorter than spec 14 (205 vs 230)**: the 230 mm right platform at the drawn height met the
  knee pad's base in the pose; the platforms are also 20-30 mm lower than take 1's heights so their place on the
  thigh matches the drawing's relative to the knee.
- **The hard case is a slim 52 x 46 x 178 case**, not a Pelican 1030 (98 x 62 x 191): either way round the 1030
  made the left block twice as wide as drawn (round 1 laid it flat on a 176 mm platform). The drawn cell is 51 wide.
- **Superseded in round 10** (the rig is now on the outer front, 26 deg outside, as drawn; see §13). Rounds 2-9: **the right
  rig sat on the front of the thigh, 12 deg toward the inside of its anatomical front** (round 2),
  because the hero pose turns the right thigh out by 43 deg: posed, the platform faces the camera (33 deg off it),
  as drawn. In rest it looks too far inboard; a rig on the thigh's outside would face sideways in the hero frame.
  If the pose agent turns the thigh in, theta must follow (`PLATFORM['R']['theta']`).
- **The right hanger runs between the thigh and the magazines' tops** into the platform's top edge.

## 4. Round 1 (2026-11-14)

- Belt: a closed band from convex hulls of the trousers' waist sections in the trousers' waist plane (WAIST in
  trousers.py), the widest row used everywhere (a stiff belt). Thigh straps: closed bands from the clothed thigh
  (trousers with cargo pockets), rays from 140 mm out on the medial side and 220 laterally. Platforms: semi-rigid
  slabs over a heavily smoothed field round the thigh, clearing the trousers, pockets and straps. Items seated on
  the platform (`gear_common.seat`).
- Rigging: belt, buckle, hangers and thigh straps soft-bound by weights from the body; each platform with its
  carriers, magazines, pouch and case skinned rigidly to `upperleg02.<side>`; the holster and P9 rigidly to the
  bone that rules the hip under them (`pelvis.R`).
- Colours: belt #2a2724, platforms #24221f, straps #161515, polymer #24211e / tan #816f5f, PMAG #1e1d1c, frag
  #463e34, case #3a3e40, holster #1f1d1c, slide #4f5050, hangers #736054 / #1e1c1a.

Renders opened: `belt_rest_{back,threequarter}.png`, `belt_hero_belt_hips_pair.png`, `renders/round_01/gear_hero.png`.

Check (`belt_check.json`): none with the body, rest or posed. Small left-overs: right strap 2 touches the cargo
pocket's edge (8), the right hanger wraps the belt (21) and touches the carrier's back (6).

Round 1 still-wrong list (round 2 took items 1-3; item 3 was the wrong way round: the drawn carriers are on the thigh front):

1. **The left block is still wider and stands further from the hip than drawn**, and it is a pair of plain boxes.
2. **No ladder-locks, buckles, tri-glides, slots, shock cord or tails**; the carriers have no slots or screws; the
   belt has no stitch rows, D-ring or tail.
3. **The right carriers sit a little inboard of the drawn position** (the drawing puts them beside the thigh).
4. The hangers are straight strips; the holster and P9 are boxes; the holster's belt loop is missing.
5. The belt is hidden in the hero frame except at the flanks; its colour is unverified against the reference.

## 5. Round 2 (2026-11-14)

Brief: the leg rigs read as saddlebags: the right rig about 7 cm inboard and facing forward, the left block
narrower, the platforms hanging on their hangers on the thigh fronts/sides with the straps round the trousers;
better carriers and frag pouch; fix the cargo-pocket clashes (up to 3.4 mm); the holster stays.

- **Right rig**: platform 158 x 180, centred 12 deg inside the thigh's anatomical front (round 1: 28 deg
  outside; 40 deg is about 7 cm on this thigh). Measured first: in the hero pose the right thigh is turned out 43
  deg and stepped back, so at 28 deg the carriers faced 71 deg away from the camera; at -12 deg the platform
  faces it at about 33 deg. Carriers turned 65 % toward the platform's centre normal so both face one way; carrier
  bodies 15 below the platform top; straps at z 792 and 716 so they cross the carrier stack at about a third and
  three quarters of its height, as drawn. Platform top 832 (rest), 20 lower than round 1.
- **Carriers**: tan face plates with three slots (`lib.gear_hardware.grid_solid`) on a spacer, a dome tension
  screw, PMAG with a floor plate, a shock-cord loop over each magazine, two cord tails with tan cord ends under
  the outer carrier.
- **Left block**: platform 132 wide (round 1: 176) at 30 deg (round 1: 58); a vertical double frag pouch 70 x 66 x
  182 with an L flap, snap and two webbing rows, beside a slim 52 x 46 x 178 hard case with a lip, latch and two
  elastic bands. In the overlay it now spans the drawn block's place, about 28 mm wider on the outside and 10 mm higher.
- **Straps and platforms**: 50 x 32 ladder-locks on the straps (right: just inboard of the platform; left: medial
  front); the platforms have rounded corners and a rolled bound edge. The straps are now fitted to this leg's
  trousers, pockets and skin only (round 1's medial rays met the other thigh and made a spike near the crotch,
  visible once the straps moved up); strap lift 2.2, platform lift 6 over the trousers and pockets.
- Holster: seated 2.5 mm off the trousers (was 0.6). It and the P9 are unchanged otherwise.

Renders opened: `renders/belt/belt_hero_belt_hips_pair.png` (four builds), round 2 assembly `belt_hips_compare`,
`belt_hips_overlay`, `soldier_full_compare`, `arm_R_compare`, `turnaround.png`.

What they show: the right carriers now face the camera side by side with their tan slotted plates, within about
10-35 px (x3 crop, under 25 mm) of the drawn carriers left and right; they sit about 40 mm higher than drawn (the
accepted longer thigh) and the drawn straps cross them lower. The left block now reads as a narrow pouch-and-case
block at the drawn place. The straps lie across the thigh front with their ladder-locks.

Clashes (`renders/round_02/clashes.md`): trousers-belt max 2.1 mm (round 1: 3.4): the left cargo pocket's flap
2.1 mm into the left platform's inner edge at (103, -94, 897), the holster 2.0 mm into the right cargo flap, the
straps 0.8-1.5 mm in or under the cargo pockets' edges, the right hanger 1.2 mm at the belt. None with the body,
carrier, armour or carbine.

## 6. Still wrong, ranked for round 3

1. **The carriers sit high on the stack**: the drawn upper strap crosses the carriers a third of the way down and
   the drawn carriers' bottoms are about 40 mm lower; moving the platform down meets the knee pad's base in the
   pose. A 20-30 mm drop and a shorter hanger is the next try once the pose's leg settles.
2. **The right rig's place depends on the pose's turned-out right thigh (43 deg)**: if the pose re-solve turns
   the thigh in, theta (-12) must move back toward the outside or the rig will face inward.
3. **Forms are still boxes underneath**: the carriers are solid (not open-top shells), no PALS on the platforms,
   no binding on the pouch, the flap is two blocks, the case has no hinge; the hangers are straight strips with no
   tri-glide or box-X; the belt has no D-ring, keeper or tail (hidden in the hero frame anyway).
4. **The holster and P9** are boxes; the holster's belt loop is missing (hidden in the hero frame).
5. Colour unverified against the reference (the materials round).

## 7. For integration

- Built on the trousers of 19:51 and hero_pose.json of 19:01; the pose agent's re-solve was not in the assembly.
- The holster touches the right cargo pocket's flap in the pose (the flap swings with the leg; the holster rides
  the pelvis): 2 mm.

## 8. Round 5 (2026-11-15): materials

`MATERIALS` in belt.py (swapped by `common.library_pass`): `Webbing.Nylon.Black` on the belt, straps and black
hangers, `Webbing.Nylon.Coyote` (new) on the tan hanger, `Cordura.500D.Black` on the platforms, all with preset
`belt.kit` and dust 0.5; `Polymer.Black.Textured` (new) on the carrier bodies, holster, PMAGs (#2e2d2b), the case
(#34383a) and frames; the magazine carriers' tan plates `Polymer.Tan.Moulded` (new; moulded-in-colour FDE,
#3e382f, stress-whitened edges); `Cordura.500D.OliveBrown` on the frag pouch; `Metal.Gunmetal` on the buckle,
slide and hardware (a brighter F0 on the steel). The left rig dust x1.0, the right x0.8.

Renders opened: `renders/round_05/belt_hips_compare.png`, `soldier_full_compare.png`, `legs_knees_compare.png`.

Still wrong: the median over the belt's mask reads brighter than the reference (ratio 0.57) even after darkening
the tan plates and the dust; most of that mask lies where the drawn rigs are not (the rigs' placement differs,
§5), so it is not a material number to chase. The drawn carriers' tan accents are small edges and flaps, ours
whole plates.

## 9. Round 6 (2026-11-15): form fixes after the first whole-soldier critic round

Critic items (notes/critic/soldier_r5/tally.md): m1/m30 the rear pouch hinged into the air, m35 the stiff rods,
m37 the empty sliders, m27 the right rig's identity, m32 the missing right-front hip pouch, m41 the left hip block.

**The bugs and their causes.**
- **The rear hip pouch was the holster with the P9** (m1, m30). It was seated 2.5 mm off a flat plane through the
  belt AND the cargo pocket below it, standing straight down: on the curved hip it touched one point (the pocket's
  edge) and stood 6-10 mm off the belt at rest; posed, the pocket follows the turned-out thigh and the holster,
  rigid on `pelvis.R`, was left in the air. Now `hang_frame()` tilts it so its back lies on the belt at the top AND
  on the hip 150 mm lower, seated 1 mm off (HOLSTER_GAP), and it and the P9 are **mounted on the belt**
  (`gear_common.mount_bind`: every vertex takes the belt's weights averaged at the mount point, so the rigid item
  moves as one blended transform with the belt under it).
- **The rods** (m35) were the outer carrier's two shock-cord tails, 52 mm tubes hanging straight. Now 19 mm soft
  tails that droop back onto the platform's face, with 12 mm cord ends.
- **The sliders** (m37) were the thigh straps' ladder-locks, their centre 5 mm out (3-4 mm off the strap) with no
  strap through them, rigid on the thigh bone while the straps followed the skin. Now they lie on the strap
  (centre LOCK_T / 2 out), are mounted on their strap, and the strap's running end climbs over the centre bar and
  runs on 70 mm as a doubled tail (`Belt.Rig.{R,L}.Strap.N.Tail`).
- The buckle (soft-bound, sheared 4 mm off the belt by per-vertex weights) is mounted on the belt.

**Identity of the right thigh rig (m27): it stays two rifle-magazine carriers.** C1 read a drop-leg holster
platform. Looked again at `ref/zoom_belt_rcarriers_x8`, `zoom_belt_right_x6`, `zoom_belt14_rrig_grid_x6` and the
full crop: two separate narrow units side by side, each with its own tan face plate (slot and keyhole) and its own
magazine-shaped top, one strap set across both, a cord tail below the outer one; no trigger-guard bulge, no single
wide shell, no pistol grip or hood. Take 1's analysis (two carriers) holds; the critic's reading is not supported.

**Added and changed.**
- m32: `Belt.Pouch.RF`, a flapped Cordura pouch 70 x 36 x 118 hanging from the belt at theta -62 (right front hip,
  above the thigh rig), hung by `hang_frame()`, mounted on the belt (`flapped_pouch()`: body, L flap, snap, a
  webbing row).
- m41: the left platform's frag pouch and hard case are replaced by the drawn **double rifle-mag pouch**: two
  flapped olive cells 64 x 38 x 172 side by side (`Belt.Rig.L.MagPouch.{1,2}`, platform 148 wide). The cells use
  the existing `Belt.Mat.Frag` slot (olive Cordura); the Case slots are now unused. **MATERIALS table not edited.**
  The drawn second cell reads darker grey-olive (a look item).

**Renders opened** (renders/round_06/): `belt_hips_compare`, `soldier_full_compare`, `hands_rifle_cycles`,
`turnaround` (the side and back views), `legs_knees_compare`. What they show:
- The left hip now reads as the drawn double pouch: two tall flapped cells with snaps and webbing rows.
- The cord tails are short soft cords curling under the outer carrier back onto the platform, with their tan ends.
- The ladder-locks lie on the thigh straps; the running ends over them are faint at hero distance (same colour).
- The right front hip pouch shows on the belt above the right rig, at the drawn place.
- **The holster at the right rear hip still reads as standing off in the side views** (turnaround side_R and side_L):
  its top leans out with the P9's raked grip above it. Better than round 5 (it no longer floats free: its nearest
  distance to anything went from over 5 mm to touching), not solved.

**Stand-off check** (`renders/round_06/standoff.md`, flagged belt objects): `Belt.Holster` (median gap 6.8 mm over its
back), `Belt.P9` (5.1), `Belt.Pouch.RF` (6.8) and its webbing row, the two cord tails and cord ends (their droop under
the carrier is in the air). The platforms (6 mm lift by design), hangers, shock cords and spare PMAGs are listed as
designed gaps with their reasons. On round 5 it flags the holster and P9 (floating, over 5 mm from anything), the
tails, the three ladder-locks (3-4 mm off their straps), the frag pouch's flap and the hard case's lip and latch.

**Clashes** (`renders/round_06/clashes.md`): trousers-belt 1.8 mm (the left cargo flap at the platform's inner edge, as
round 2). The first try of the right front pouch (mounted on the belt) went 15 mm into the trousers where the posed hip
swells; bound by weights it no longer clashes.

## 10. Still wrong, ranked for round 7

1. **The holster** leans off the hip in the side views: a real paddle or belt-loop holster is drawn into the hip by the
   belt; give it a contoured back (cast onto the hip) instead of a flat box, and a belt loop over the belt.
2. **The right rig's place** still follows the pose's turned-out right thigh (theta -12); when the pose agent turns
   the leg in (m16), theta must move back toward the outside (`PLATFORM['R']['theta']`).
3. The right front pouch is a plain flapped box; the drawn one has a tan face and a dark side (a look item too).
4. Forms are still boxes underneath (carriers solid, no PALS on the platforms, hangers straight strips).

## 11. Round 8 (2026-11-15): the look

No belt geometry or table change. Through the library: `Polymer.Black.Textured` #272624 -> #262625 at roughness 0.48
(satin) with scuffed edges; the olive frag/mag-pouch cells (`Cordura.500D.OliveBrown`) the lighter olive-coyote
with the carrier's edge abrasion; the coyote webbing unchanged. The belt's graded median reads 0.70 of the
reference (ours brighter), most of its mask lying where the drawn rigs are not (§8); not chased.

## 12. Round 9 (2026-11-15): the battle belt, the carriers, the holster (critics r8 m36, m22, m10, m32)

- **Battle belt** (m36, "a narrow flat strap"): `BELT_W, BELT_T` 44.5 x 5.5 -> **50 x 9**, a padded 2 in sleeve over the
  1.75 in rigger belt (HSGI Sure-Grip / BFG class). Inner girth 1021 mm (987), front top z 1047 as before.
- **Thigh mag carriers** (m22, "oversized clean boxes"): `MAG_CARRIER` 76 x 42 x 140 -> **70 x 36 x 122** (a STANAG
  TACO), `MAG_PLATE` 47 x 3 x 128 -> 44 x 3 x 110, slots 39 / 63 / 87 below its top (45 / 73 / 101). Materials:
  `Belt.Mat.PolyBlack` dust 0.2 -> 0.5 with paler scuffed edges (edge albedo +0.08, width 0.14); the tan plates
  `#3e382f` -> `#554a3b` with edge albedo +0.07.
- **Holster** (m10, m32: it jutted off the rear hip): `HOLSTER` 60 x 50 x 190 -> 54 x 42 x 182, and `conform_back()`
  bends its back half onto the real surfaces under it (belt, trousers with pockets) by rays along its outward axis
  (reach 22 mm, 1 mm gap, fading to nothing at its mid-plane), as a moulded kydex holster sits on the hip.

**Renders opened**: `renders/belt/` (the part's own pairs) and in-memory hero crops `belt_hips`, `hands_rifle`,
`turn_side_R` (scratch, not a round). The carriers are visibly slimmer with their tan slotted plates; the belt itself is
hidden in the hero frame (magazine and left hand), so m36 can only be judged in the turnaround. In the side view the
holster still leans off the rear hip with the P9's raked grip above it (the critics' "L-shaped item"): smaller, not solved.

Stand-off (in-memory, after the refit to the round-9 trousers): flagged `Belt.Belt` 7.0 mm median (the stiff band takes
the waist's widest row everywhere, so with 9 mm it stands off where the waist narrows), `Belt.Pouch.RF` 6.3 (round 8:
7.5), the outer carrier's two cord tails and cord ends 26-37 mm (as since round 6: they droop under the carrier). The
holster and P9 are no longer flagged. Clashes: trousers-belt 35 vertices, 1.7 mm (round 8: 38, 1.6), the straps at the
cargo pockets' edges.

Still wrong: the holster in the side views; the battle belt has no PALS, binding or inner/outer split; the cord tails;
the belt should be fitted per row instead of the widest row everywhere.

## 13. Round 10 (2026-11-15): a cinched belt, the right rig on the outer thigh, soft pouches, the holster (G1 D12, D14; m5, m23, m28)

- **Belt, fitted per section** (G1 D14, round 9's stand-off 7.0-7.4 mm: "a rigid hoop standing off at the back").
  - Each of the band's 5 rows lies on its own section's convex hull, 0.6 mm over the trousers (`BELT_LIFT`; 1.0 over the
    widest row before).
  - Across the band the rows are eased a quarter of the way toward their mean, but never inside their own hull: a 50 mm
    padded sleeve does not crease to every section.
  - The rows sit 0 to 13 mm inside the widest one (median per row). Inner girth 968 (1021).
  - `belt_point` follows the middle row.
- **Right leg rig on the outer thigh** (m23, D12: "two thick square boxes on a large flat backing on the front of the
  thigh").
  - The platform sits 26 deg from the thigh's front toward the outside (12 deg inside before). It is narrower and shorter:
    144 x 158 (158 x 180). The straps are at z 796 and 728.
  - In the hero frame the rig now stands at the silhouette's edge where the drawn carriers are, seen obliquely. The
    `belt_hips` overlay puts it on the drawn carriers.
  - §3's round-2 reasoning (the thigh turned out 43 deg, so a rig on the outside faces sideways) held for the face but not
    for the place. The drawing shows them at the edge.
- **Right carriers in Cordura** (m28: "hard grey plastic, unlike the olive fabric pouches"). The real HSGI TACO is a nylon
  pouch round a polymer insert.
  - The bodies are soft, from `softgear.soft_pouch`: open top with a bound mouth, the magazine's 2 mm bulge, piped seams,
    68 x 34 x 122 at u -36 / +36. They are charcoal 500D: `Belt.Mat.CarrierBody`, Cordura.500D.Black at #383632, dust 0.8,
    inside the lint's textile_black band.
  - The tan slotted plates, spacers, screws, PMAGs and shock cords stay, moved out over the bulge.
- **Left double mag pouch and right-front hip pouch**, now soft (`soft_flapped`):
  - bodies round their magazines, 3.5 mm bulge, rounded bottoms;
  - flaps crowned 5 mm and draped 48 mm (40 on the hip pouch), with a bound edge, piped seams and a tab with a dark plate;
  - webbing bands that follow the face (`softgear.face_band`).
  The flat snap, the block flaps and the flat rows are gone. The tab plates were gunmetal at first and read as bright white
  squares in the hero frame; they are now the black strap material.
- **Holster** (m5: "its top angled ~40 deg off the body, like an open lid"):
  - The angled top was the P9's grip. It was laid along the belt's tangent, raked 14 deg, at belt-top height, where the
    lumbar curve leaves the back 40 mm and more away.
  - The holster now hangs 32 mm lower (`HOLSTER_DROP`, a mid-ride drop), so the grip lies beside the belt.
  - It moved from 122 to 115 deg round the belt, where the hip is flatter, and its back may bend 34 mm onto the hip
    (`HOLSTER_REACH`; 22).
  - The grip is raked 8 deg (`P9_RAKE`) and turned toward the body about the holster's axis. The search
    (`GRIP_CLEAR`, nearest-surface distance at the grip's middle and end) stops at its 30 deg limit, with the grip's end
    about 26 mm off the hip.

**Checks** (the in-memory assembly of 21:20 described in carrier.md §12, belt cache of 21:07; the final rebuild at 21:23
changed only the left pouches' tab-plate material):

| Check | Round 9 | Round 10 | What |
|---|---|---|---|
| trousers-belt | 60 verts, 2.6 mm | 53 verts, 2.6 mm | the left cargo flap at the platform's inner edge, as since round 2 |
| body-belt | none | none | |
| belt-carbine | none | none | |
| belt-carrier | none | none | |

Stand-off, round 9 -> round 10:
- Gone: `Belt.Belt` (7.4).
- `Belt.Holster` is not flagged. `Belt.P9` is new at 15.5: the grip's end, 26 mm off the hip.
- New: the soft carriers `Belt.Rig.R.Carrier.1/.2` at 12.1 and 16.3, `Belt.Rig.L.MagPouch.2` at 9.6 and `Belt.Pouch.RF` at
  7.8. These are rounded sides and bottoms facing the skin over the platform's edge, an artefact of the heuristic on
  rounded bodies; their backs lie on the platform and belt (contact 0.01-0.33).
- Worse: the outer carrier's cord tails 26-37 -> 46-53. With the rig turned out they hang free below the carrier, as the
  drawn tails do.

**Colour** (look_stats, belt_hips, eroded mask, graded): the belt's median Y fell from 0.0179 (equal to the reference's)
to 0.0120 against 0.0195. The mask moved with the rig, and the carriers are now fabric, not scuffed satin polymer. Not
chased further.

Renders opened:
- the part's own `renders/belt/belt_hero_belt_hips_pair.png`;
- in `renders/scratch_r10cb/{c2,final}/`: `belt_hips_cycles`, `soldier_full_cycles`, `turn_side_R`, `turn_back`,
  `close_holster`, `close_belt_back`, `close_rig_R`;
- `renders/look/r10cb_final/sheet_belt_hips_graded.png`.

**Still wrong, for round 11:**
1. In the side view the holstered P9 still reads as an L. The grip is a straight 105 mm block running rearward past the
   buttock, and it stops at the turn search's 30 deg limit. Options for Jeff:
   - a hood over the grip's front (an ALS hood);
   - the holster further forward;
   - the P9 left out, since the image shows none (Decision 2).
2. The carriers and pouches are darker and plainer than drawn. The drawn right carriers have grey worn highlights; the left
   cells' drawn tan accents are not built.
3. The cord tails hang free (flagged).
4. The battle belt still has no PALS, binding or inner/outer split.
