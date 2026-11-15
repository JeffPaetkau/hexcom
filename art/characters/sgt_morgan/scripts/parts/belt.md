# Belt

Build: `"$SGT_BLENDER" -b --python scripts/parts/belt.py [-- --no-render]` (about 25 s). Output:
`cache/parts/belt.blend` (collection `Part.Belt`), `cache/parts/belt.json`, `renders/belt/*.png`,
`renders/belt/belt_check.json`.

## 1. What it is (real identity and dimensions)

| Item | Built (mm) | Class / source |
|---|---|---|
| Rigger belt | 44.5 x 5.5, inner girth 987, top 3 mm under the trousers' waistband top (front z 1047), in the trousers' tilted waist plane | HSGI Cobra 1.75 in class (spec 14 §3.1) |
| Buckle | 38 x 10 x 58, 30 mm to his right of centre front | AustriAlpin Cobra FC45 (datasheet 58 x 38 x 10) |
| Hangers | 38 x 1.6 webbing, coyote (right), black (left) | spec 14 §3.2, D11 |
| Right platform | 150 x 205 x 8, top z 852 (rest), on the thigh at 28 deg from its front toward the outside | HSGI / Blackhawk Omega class leg rig (spec 14 §3.3) |
| Right thigh straps | 38 x 2 at z 785 and 682 | spec 14 D10 |
| Twin rifle-mag carriers | 76 x 42 x 140 black, tan plates 47 x 128 x 3, PMAG tops 66 x 25 standing 53 proud | HSGI polymer TACO class (spec 14 §3.4, D4, D5) |
| Left platform | 176 x 205 x 8, top z 866, at 58 deg; strap at z 684 | spec 14 §3.5 (widened for the case lying flat) |
| Frag pouch | 72 x 70 x 195 with a 50 mm flap, olive | vertical double M67 footprint (spec 14 §3.6) |
| Hard case | 98 x 62 x 191, lid against the platform | Pelican 1030 class (spec 14 §3.7) |
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
- **The hard case lies flat** (62 deep, 98 across) instead of standing out 98 from the thigh: standing out it made
  the left block twice as wide as drawn. The left platform is 176 wide to carry it beside the frag pouch.
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

## 5. Still wrong, ranked for round 2

1. **The left block is still wider and stands further from the hip than drawn**, and it is a pair of plain boxes.
2. **No ladder-locks, buckles, tri-glides, slots, shock cord or tails**; the carriers have no slots or screws; the
   belt has no stitch rows, D-ring or tail.
3. **The right carriers sit a little inboard of the drawn position** (the drawing puts them beside the thigh).
4. The hangers are straight strips; the holster and P9 are boxes; the holster's belt loop is missing.
5. The belt is hidden in the hero frame except at the flanks; its colour is unverified against the reference.

## 6. For integration

- Rebuilt on the base of 18:25; the trousers cache it fits is from 18:09. Rerun after the trousers.
