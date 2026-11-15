# Belt

Build: `"$SGT_BLENDER" -b --python scripts/parts/belt.py [-- --no-render]` (about 25 s; round 2 about 40 s). Output:
`cache/parts/belt.blend` (collection `Part.Belt`), `cache/parts/belt.json`, `renders/belt/*.png`,
`renders/belt/belt_check.json`.

## 1. What it is (real identity and dimensions)

| Item | Built (mm) | Class / source |
|---|---|---|
| Rigger belt | 44.5 x 5.5, inner girth 987, top 3 mm under the trousers' waistband top (front z 1047), in the trousers' tilted waist plane | HSGI Cobra 1.75 in class (spec 14 §3.1) |
| Buckle | 38 x 10 x 58, 30 mm to his right of centre front | AustriAlpin Cobra FC45 (datasheet 58 x 38 x 10) |
| Hangers | 38 x 1.6 webbing, coyote (right), black (left) | spec 14 §3.2, D11 |
| Right platform | round 2: 158 x 180 x 8, corners r 15, a 12 mm bound edge, top z 832 (rest), 6 over the trousers, centred on the thigh 12 deg from its front toward the INSIDE (round 1: 28 deg outside) | HSGI / Blackhawk Omega class leg rig (spec 14 §3.3) |
| Right thigh straps | 38 x 2 at z 792 and 716 (round 2), 2.2 over the trousers; 50 x 32 x 3.5 ladder-locks on the running ends just inboard of the platform | spec 14 D10, §3.2 |
| Twin rifle-mag carriers | 76 x 42 x 140 black, body top 15 below the platform top; tan plates 47 x 128 x 3 with three 25 x 6 slots (45, 73, 101 below the top) on a 1.6 spacer; 8 mm dome tension screw; PMAG tops 66 x 25 standing 53 proud with a 70 x 29 floor plate; 4 mm shock-cord loop over each magazine; two cord tails 52 long with 8 x 16 tan cord ends under the outer carrier; both turned 65 % toward the platform's centre normal so they face one way | HSGI polymer TACO class (spec 14 §3.4, D4, D5) |
| Left platform | round 2: 132 x 200 x 8, top z 878, at 30 deg (round 1: 176 wide at 58 deg); strap at z 702 with its ladder-lock at the medial front (-30 deg) | spec 14 §3.5 |
| Frag pouch | 70 x 66 x 182, bevel 9, slightly tapered; an L flap (top 73 x 70 x 7, drop 48 down the face) with a 15.5 mm snap; two 25 mm webbing rows at 95 and 133 below the top; olive | vertical double M67 footprint (spec 14 §3.6) |
| Hard case | round 2: 52 x 46 x 178 (across, out, tall), a parting-line lip 4 mm round it 16 below its outer face, a 30 mm latch on its inboard side, two 25 mm black elastic cradle bands at 60 and 140 below its top | slim polymer utility case, sized to the drawn 51 mm cell (spec 14's Pelican 1030 at 98 x 62 made the block twice the drawn width) |
| Holster | 60 x 50 x 190, open mouth, 2.5 walls, at 122 deg round the belt toward his right rear | Safariland 6378 ALS class for a P226 |
| P9 | slide 196 x 34 x 30 muzzle down in the holster, grip 105 x 48 x 32 raked 14 deg rearward above the mouth | SIG P226 class (consolidated analysis: 196 x 140 x 38) |

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
- **The right rig sits on the front of the thigh, 12 deg toward the inside of its anatomical front** (round 2),
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
