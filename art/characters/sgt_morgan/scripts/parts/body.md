# Body (the base mesh: skin, anatomy, hands, feet, neck)

The body is not a part script. It is `scripts/stages/base.py` → `cache/stages/base.blend` (`Body.Mesh`, `Morgan.Rig`,
`Body.Eyes`, `Body.Eyebrows`, `Body.Eyelashes` in collection `Body`). Every part builds on it, so a change here means
re-running `pose.py --solve` and every part script after it.

Build: `"$SGT_BLENDER" -b --python scripts/stages/base.py -- --render` (about 8 s with renders). Output:
`cache/stages/base.json` (targets, measurements, skin, landmarks, bones) and `renders/body/body_rest_*.png`,
`body_chest_rest_*.png`. Round 0's views are kept as `body_before_rest_*.png` and `body_before_chest_rest_*.png`.

## 1. What it is

A lean, fit, muscular 40-year-old man:
- rest stature 1835 mm barefoot (CLAUDE.md, Jeff 2026-10-10);
- the drawing's V-taper;
- ANSUR II segment lengths.

It is MPFB 2.0.17's male (macros in base.py) with MPFB's `default` skeleton and weights. Real-world yardsticks are ANSUR II male means:
- neck about 397 mm under the larynx;
- biceps about 340 relaxed;
- forearm about 290;
- calf about 385;
- chest about 1000 for this build.

## 2. What the reference shows

- Almost no skin: the face (head part), the neck above the gaiter, and nothing else. The chest, arms and legs are under the shirt, carrier, sleeves, gloves, trousers and boots.
- What the clothes still show is the build:
  - a broad, muscular chest and shoulders under the carrier;
  - thick trapezius running into a thick neck (`ref/zoom_torso_neck_shoulders_x4.png`);
  - muscular forearms that fill the sleeves and guards.

## 3. Round 1 (2026-11-14)

### The chest

Round 0's chest read soft and female in clay: rounded mounds peaking at the nipple with a sagging underside. Under the 5 mm shirt they showed as breasts.

Five rounds of variants were rendered, front, side and three-quarter, with a side profile through the nipple column (x ±95 mm). They tried:
- the pectoral muscle;
- `breast-point` and `breast-volume`;
- `breast-trans-up`;
- `measure-bust-circ`;
- the nipple targets;
- `torso-muscle-dorsi`;
- `torso-scale-depth`.

Kept:
- `torso-muscle-pectoral-incr` 0.3 → 0.7: the pectoral carries the shape.
- `breast-trans-up` 0.5: the mass moves up, so the profile's apex goes from z 1360 to z 1400.
- `measure-bust-circ-decr` 0.3: the fullness goes.
- `nipple-size-decr` 0.6 and `nipple-point-decr` 0.3.
- `torso-muscle-dorsi-incr` 0.5: puts the girth back.

Rejected:
- `measure-bust-circ-decr` 0.6 alone. It flattened the chest but took the girth from 993 to 904 (a skinny man) and the breadth from 366 to 332.
- `torso-scale-depth`. It moved a spine joint cube by 3.7 mm.

Result: a pectoral plate sloping from the clavicle, its lower edge a 15 mm step back to the ribcage over 20 mm. The chest girth is 990 (round 0: 993).

### The rest of the body, measured against a lean muscular man

| Girth (tape = convex hull of a plane section), mm | Round 0 | Round 1 | Target used to set it | Target |
|---|---|---|---|---|
| Neck, square to the neck axis under the larynx | 405 | 409 | 0.1 | `measure-neck-circ-incr` |
| Chest | 993 | 990 | pectoral, bust, dorsi | see above |
| Waist (minimum) | 750 | 751 | | |
| Hip | 979 | 996 | follows the thigh muscle | |
| Upper arm | 318 | 338 | 0.4 → 0.7 | `l/r-upperarm-muscle-incr` |
| Forearm | 247 | 275 | 0.6 | `l/r-lowerarm-muscle-incr` |
| Thigh | 546 | 554 | 0.4 | `l/r-upperleg-muscle-incr` |
| Calf | 374 | 388 | 0.15 | `l/r-lowerleg-muscle-incr` |

Notes on the table:
- **Forearm.** Round 0's forearm (247) was below ANSUR's 5th percentile; that was the clearest miss.
- **Neck.** The measure itself changed. Round 0's horizontal plane midway between neck02 and neck03 cut through the chin once the fitted face lengthened the jaw: it read 466. It is kept in base.json as `neck_horizontal_old`.
  - The fitted face widens the upper neck by about 15 mm on its own, so the neck target dropped from 0.3 to 0.1.
  - A first try at 0.7 gave 440.
- **Breadths.** Bideltoid (A-pose) 605 → 612, chest breadth 366 → 372, chest depth 240 → 236.

Stature is 1835.02 mm (height macro 0.58267).

### Joints

None of the body targets above moves a joint cube (checked: 0.0 mm). What moved:
- **The face targets (head part)** moved the head joint 6.5 mm down, neck02 7.4 mm and neck03 3.6 mm.
- **The height refit** moved every other joint by about 0.9 mm.
- **Twist bones.** The twist bones (upperarm02, lowerarm02, upperleg02) are placed from vertex centroids and moved 1.3 to 2.0 mm.

`pose.py --solve` was re-run. The residuals are in `scripts/stages/README.md`, "Round 1".

### Materials and eyes

- **Skin.** MPFB's middle-aged Caucasian male texture, as an ENHANCED_SSS material (`Body.Skin`; round 0 had no material at all). It is toned by a measured multiply to the albedo `#ab7d71`; see head.md for the calibration.
- **Eyes, the red rims.** The red rims in Workbench were the eyelash and eyebrow cards drawn solid in their red-brown viewport colour (`#320704`). Workbench ignores the alpha textures.
  - The lash cards' viewport colour is now the skin's, so they vanish in Workbench.
  - The brows are dark brown.
- **Eyes, the iris.** MPFB's EnhancedEye drew blue irises in Cycles and plain white eyes in Workbench.
  - Iris colours are now `#5b4a3e` / `#3a2d26` (analysis §5: dark warm brown-grey), with an off-white `#d9d0c8` sclera.
  - A second material slot (`Body.Eyes.Iris`, a copy with the same node settings, so Cycles is unchanged) holds the faces within 34° of each eye's forward axis. Its viewport colour is the iris brown.
  - Workbench now shows brown irises on off-white.

### Renders looked at

- **`body_rest_*` against `body_before_rest_*`.** A more muscular man: thicker forearms and upper arms, a male chest. The proportions and stance are the same.
- **`body_chest_rest_*` against `body_before_chest_rest_*`.** Male pectorals with a defined lower edge. The side view is a plate, not a mound.
  - The nipple reads as a small pit in clay; that comes from `nipple-point-decr`.
- **`renders/round_01/clothing_hero.png`.** Under the tight round-1 shirt the chest now reads as male pectorals. The nipples are small bumps, not breasts. No skin pokes through.
- **`renders/head/head_hero_soldier_full_cycles_pair.png`.** The posed body in Cycles. The skin reads too orange (head.md §5).

### The clothing after the body change

The four scripts were re-run unchanged:
- `renders/round_01/clothing_hero.json` against round 0's body: the trousers, boots and gaiter still have 0 vertices inside the skin.
- The shirt shell's known spot at the back of the right elbow grew from 71 vertices inside (−15.7 mm) to 91 (−14.6 mm), because the upper arm is 20 mm thicker. The armour's elbow cap covers it; it is not visible from the hero camera.
- The gloves have 503 / 483 vertices inside the curled fingers. That is unchanged (round 0's curl tables).
- The layering counts are the same: boot collars 144, sleeve ends 0 / 1, shirt tail 20 (was 19), collar 13.
- Not re-run here: the carrier, armour, belt (the gear agent) and the carbine. They build on base.blend and hero_pose.json, so they need a re-run.

## 4. Still wrong, ranked for round 2

1. **The pectoral's lower outer edge is still slightly rounded,** and `nipple-point-decr` leaves a pit. A measured corrective shape would fix both: flatten the plate, crease the lower border, sharpen the axillary fold. MPFB's targets are at their useful limit here.
2. **No trapezius.** MPFB has no trapezius target. The drawn neck-to-shoulder slope is heavier, though it is mostly under the gaiter and carrier straps.
3. **Skin in Cycles is orange and saturated** (ENHANCED_SSS's red subsurface under the 4500 K key). See head.md.
4. **The right elbow's skin stretches under linear skinning** at 103° (the shirt clearance above). This calls for a corrective shape key or a better weight at the olecranon.
5. **Hands and feet are untouched.** MPFB's defaults: the fingers are curl tables, so the gloves press into the palms. The feet are covered by the boots.
6. **No abdominal or oblique definition, and no veins.** These are invisible under the gear, so they are low priority.
