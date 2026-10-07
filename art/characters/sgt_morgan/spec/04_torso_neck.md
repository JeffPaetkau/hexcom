# Part 04 — Torso, shoulders and neck (ribcage, abdomen, spine, shoulder girdle, neck; skin, hair, pose, rig)

Status: draft 1 (spec writer), 2026-10-06. Owner script: `scripts/parts/04_torso_neck.py` (plus the shared `scripts/lib/proportions.py`, `scripts/lib/sculpt.py`, `scripts/lib/measure.py`, `scripts/lib/corrective.py`). Object prefix `Torso.*`, `Neck.*`; the body itself is the shared MPFB mesh `Body.Mesh` (spec 03's name; spec 01 calls it `Human` — [VERIFY: one name must win at the critique pass, this spec uses `Body.Mesh`]).

Conventions (from `CLAUDE.md`): millimetres in this spec, metres in Blender; world origin on the floor midway between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT = viewer's right**. Every "left/right" is the soldier's own. Heights are given in two columns throughout: **REST** (A-pose, legs straight) and **POSED** (the hero frame). The hero pose flexes the knees and abducts the thighs, which drops the pelvis by 22 mm (spec 03 §3.1: hip 851 rest → 829 posed), and the trunk rides on the pelvis, so for every trunk landmark **POSED = REST − 22** (`TRUNK_DROP_MM`, read at build time from spec 03's IK log, never hard-coded). Image coordinates are full-image pixels of `ref/reference_full.png` (1672 × 941; 4.72 px/cm = 2.12 mm/px at the figure, right sole y = 895 is h = 0).

---

## 1. Purpose and acceptance

### 1.1 What this part is
Everything of the bare body between the pelvis and the head: the lumbar flank from the iliac crest (rest h 1031, spec 03's top) up through the abdomen, ribcage, back, shoulder girdle (clavicles, scapulae, acromia, deltoid caps down to the axilla floor) and the whole neck up to the under-jaw plane at the hyoid (rest h 1622), where the face spec takes over. It owns the trunk's proportions (the long waist, the V-taper, the 625 mm bideltoid), the spine curvature, the posture of the hero pose (pelvis yaw −10°, chest yaw −5°, 3° thoracic extension, 2° lateral lean to his right, head 20° to his left), the skin of the torso and neck (colour by region, the untanned trunk against the weathered neck, the collar sun line, the nipples and the navel), the chest, axillary, shoulder and neck hair, the corrective shape keys at the shoulders and neck, the compression keys under the carrier, and the surfaces, rings and anchors that the gaiter, combat shirt, plate carrier, shoulder straps, pauldrons and antenna are fitted to. It does **not** own the arms below the deltoid (arm spec), the head and face above the hyoid (face spec), the scalp or beard (grooming spec), or any garment.

In the hero render the only bare skin of this part is a strip of the right side of the neck, roughly 45 mm tall and 110 mm wide, between the jaw shadow and the gaiter's top roll. Everything else is under the gaiter, the shirt and the carrier. It is built in full anyway because (a) the carrier, straps, pauldrons and gaiter only read as *worn* when they bite into and are shaped by a correct body, (b) the shirt and gaiter cloth simulations collide with this body, (c) the rig's spine, neck and clavicle bones live here, and (d) the client has asked for the foot method everywhere: detail after detail, nothing too small.

### 1.2 What "perfect" looks like
A critic who knows anatomy, looking at the bare torso at 2048 px, cannot name a girth or landmark height more than the §8.2 tolerance off the §3 tables; sees a 40-year-old mesomorph, not a bodybuilder and not a mannequin — pectorals that are thick but hang from a visible clavicle, a sternal notch deep enough to shadow, two SCM cords meeting at the notch, a laryngeal prominence with a thyroid notch, two or three soft horizontal neck creases, a trapezius slope that is a muscle and not a cone, scapular spines and an inferior angle that move when the right arm comes across the chest, a spinal furrow that is deep between the shoulder blades and shallow at the waist, a long lean waist that reads as a long lumbar spine rather than a stretched texture, a navel that is a 12 mm oval pit with a fold above it, rectus abdominis as a 2 + 2 relief and not a six-pack, moderate dark chest hair lying down and inward on the sternum, nipples that are oval and slightly down-pointing, pale untanned trunk skin against a ruddier, rougher nape and neck with a soft collar line between them. In the hero frame the lit neck strip matches `ref/zoom_torso_neck_gaiter_x8.png` in shape, the SCM ridge is where the picture has it, the under-jaw shadow is as black as the picture, and every garment edge (gaiter, strap, carrier top and hem, waistband) lands on the body at the pixel rows of §2.

### 1.3 Closeup render views (definitions for `scripts/eval/render_part04.py`, written to `renders/04_torso/`)
All bare-body views use the neutral look-dev scene of spec 01 §8.1 (grey backdrop, 45° key, soft fill) at 2048², 48 spp, OIDN, and are repeated once under the hero lights for colour. The dressed view V6 uses the reference camera exactly.

| View | Camera position (mm, world, REST body unless stated) | Target (mm) | Lens / sensor | Compared with |
|---|---|---|---|---|
| V1 Front torso | (0, −2300, 1300) | (0, 0, 1300) | 70 mm, 36 mm sensor | §3.3 trunk sections, §3.4 pectorals/abdomen, the §2.4 garment-edge overlay (rows drawn as lines at the posed heights) |
| V2 Back three-quarter | (−1300, +1900, 1500) | (0, +40, 1380) | 70 mm | §3.5 scapulae, spine furrow, erector columns, lats, PSIS dimples (spec 03) |
| V3 Shoulder girdle, high oblique | (+500, −1100, 2300) | (0, −20, 1480) | 60 mm | §3.5 clavicles, supraclavicular fossae, trapezius slope, deltoid caps; overlay of the pauldron cap boxes and strap paths from §2.4 |
| V4 Neck macro, posed head | (−420, −520, 1640) | (−10, −60, 1590) | 100 mm, DOF f/8 on the larynx | §3.6 neck table; `ref/zoom_torso_neck_gaiter_x8.png` for the SCM ridge, crease lines, stubble boundary (face spec) |
| V5 Flank and waist | (−1800, −900, 1150) | (0, 0, 1080) | 85 mm | §3.3 waist sections, the 10th rib → crest flank, navel, oblique mass, the crest from spec 03 |
| V6 Dressed hero check | hero camera (0, −4500, 600), rot (93.9°, 0, 0), 46 mm; crop to (690–1000) × (100–520) at ×3 | — | as hero | `ref/crop_torso_vest.png`, `ref/zoom_torso_neck_shoulders_x4.png`, `ref/zoom_torso_waist_band_x6.png`: with the gaiter, straps, carrier and pauldron **stand-ins** of §4.12 placed at the §2.4 heights, every garment edge within 3 px of the reference row; the lit neck strip within the §8.2 metrics |
| V7 Pose readback | V1 and V2 cameras with the POSED body (no garments) | — | — | §7.3 angles: the shoulder midpoint at X −58 ± 8, the right scapula 20 mm lateral of the left, the head 20° left |

### 1.4 Pass criteria a critic can score (full list in §8.3)
1. Every value in `measure_torso()` (§8.2) is within tolerance of §3: girths ±15 mm, breadths and depths ±8 mm, landmark heights ±5 mm, neck ±4 mm.
2. Bideltoid 625 ± 8 (rest), waist 310 ± 6 at rest h 1060, chest girth 1100 ± 20: the V-taper ratio shoulder-girth/waist-girth ≥ 1.55.
3. Neck breadth 135 ± 4 at the larynx level = 0.85–0.90 of the bigonial width that the face spec builds; SCM cords, larynx with thyroid notch, suprasternal notch ≥ 8 mm deep, two to three neck creases all visible in V4 as relief, not colour.
4. Clavicles read as 15 mm rods under the skin with a supraclavicular fossa behind them; the acromion is a flat shelf, the deltoid a cap that is widest 55–65 mm below it.
5. V2: scapular spines, inferior angles at the T7 level, a spinal furrow 15–20 mm deep between the blades, 6–8 mm at the waist; posed (V7) the right blade is 18–22 mm lateral of the left.
6. The long waist (crest → 10th rib 158 mm) shows no texture stretch, no faceting, no visible loop seam; the navel is a 12 × 9 mm pit with an upper fold.
7. Skin: trunk paler than the face by ΔL* +8 ± 2, nape darker and redder than the chest, a 20–30 mm soft collar line and no hard line; no waxy SSS (the shadow side of the neck under the hero key stays ≥ 1.5 stops darker than the lit side).
8. Hair: chest 1,800–2,600 terminal strands in the §6 map, axillae dense, shoulder caps sparse, none on the upper back; nothing pokes through garments in dressed renders.
9. V6: the gaiter top roll at the front centre at y 150–155, straps over the trapezius from y 160, carrier top at y 195–200, hem at y 395–400, waistband top at y 475 — all within 3 px; the lit neck fraction and the shadow edge within §8.2.
10. Correctives: with the right arm posed the pectoral does not fold through the deltoid, the axilla has a fold not a hole; with the head turned the right SCM stands out and the left neck skin shows compressed creases; no candy-wrapper twist at the neck.

---

## 2. Reference observations

### 2.1 What the image shows about this part

| Observation | Pixels | Derived for the body | Source |
|---|---|---|---|
| Skull top / chin (lit pad) / menton | y 20 / 129 / 131.5 | h 1855 / 1623 / 1618 posed | consolidated "Agreed scale", §2 |
| Gonions (jaw angles) | (768,113) / (842,112), 74 px apart | bigonial 157 mm → neck breadth 0.85–0.9 × = 133–141 mm | consolidated §2 |
| Visible neck skin | trapezoid: x 755–823 at y 130, 752–805 at y 154; lit (lum > 90) only on his right of x ≈ 800 | the strip is 45–50 mm tall at the front centre; the chin's shadow covers the centre and left | my runs (§2.2) |
| SCM ridge, right, lit | (778,146) #ae806b; neck right side (790,150) #bd8d76 | the right SCM is taut (it is the muscle that turns the face to the left) | face note §4, my sample |
| Under-jaw shadow | (805,138) #110a04, lum 11; centre (815,145) #0d0702 | nothing lights the neck from below; the chin projects strongly | lighting note §2.1 |
| Left neck, cool fill | (838,142) #33383c; (845,135) #494d56 | the cool side light wraps the left neck faintly | my sample |
| Gaiter top edge | centre front y 150–155 (x 790–810); his right side y 139–145 (x 752–760); his left/back y 125–130 (x 840–860) | the gaiter is pushed down at the front, rides up at the back-left; the larynx apex sits at the roll's edge, hidden | my zooms `ref/zoom_torso_neck_gaiter_x8.png` |
| Neck base / trapezius line (est.) | y 170 | h 1536 posed: the visual neck–shoulder junction on the front silhouette | pose note §2 |
| Shoulder line (pad tops) | y 195; L pad top 183 (x 920), R pad top 192 (x 665) | acromion ≈ y 192 ± 5 → h 1490 posed | consolidated §1 |
| Shoulder joint centres (analysts' est.) | (675,200) / (935,200) | 260 px = 551 mm apart, 10 mm below the pad tops — anatomically too wide and too high; see §2.3 decision D3 | pose note §3 |
| Shoulders bare (deltoid, est.) | x 655 / 950 | **295 px = 625 mm** bideltoid | consolidated disputes #16 |
| Chest incl. vest | y 300: x 690–920, 230 px | 488 mm dressed; the bare chest is under it | consolidated §1 |
| Waist under the vest hem | y 470: x 745–890, 145 px | **307 mm** at posed h 900 (the waistband) | consolidated §1 |
| Hips, body only | y 500: x 735–900, 165 px | 350 mm at posed h 837 (spec 03: trochanters 345) | consolidated §1 |
| Body centre-lines | head 806, shoulders 801–802, vest column 797, hips 817, crotch 810, stance midpoint 830 | shoulders at X −58 (relative to the stance midpoint), hips −28 (spec 03 pelvis −40): the trunk leans ≈ 2° to his right over the loaded right foot | pose note §3 |
| Pelvis / chest / head yaw | — | pelvis −10°, chest −5° world, head +20° world (+25° vs chest); thoracic extension 3°; shoulders "back and level" | consolidated §1, pose note §6 |
| Right clavicle | — | protraction +8°, elevation +2° (the arm across the chest) ; left −3° depressed | pose note §6 |
| Vest front bag | x 740–890, y 195–398 | top h 1483–1473 posed (≈ 20 mm below the clavicle), hem h 1053 | consolidated §6 |
| Admin panel / PALS / mag pouches / lower PALS | y 198–240 / 240–265 / 265–335 / 340–398 | h 1477–1388 / 1388–1335 / 1335–1187 / 1176–1053 posed | consolidated §6 |
| Shoulder straps | R x 725–760, L x 822–858, y 160–255; 35 px = 73 mm wide | centres ±104 mm about the vest column; over the trapezius from h 1557 down the chest to h 1356 | gear note §4.5 |
| Cummerbund | (840–900, 360–400) on his left; shadow under the right arm (700–740, 380–400) | h 1133–1049 visible; 3 PALS rows ≈ 130 tall → the band spans h ≈ 1050–1180 (the 10th rib at its top) | gear note §4.6 |
| Exposed shirt band | y 398–475, x 745–890 | 160 mm of shirt between the vest hem (1053) and the waistband top (890); lit right #5d574e (760,450), centre #2e2b29 (800,440), under the hem #403c38 (800,405), above the belt #1c1b19 (800,485) | my samples |
| Waistband / belt | y 475–490 / 490–512 | h 890–858 / 859–812 (spec 09, belt spec) | spec 09 §2.1 |
| Pauldron caps (tier 1) | R (668–718, 190–240); L (895–960, 185–250) | R: X −290…−184, h 1494–1388; L: X +191…+329, h 1504–1367 (posed) — they ride the deltoid cap, their inner edge 60–70 mm outboard of the GH centre | consolidated §5 |
| Antenna base | (898–912, 135–185) | X +197…+227, h 1611–1505; on the rear bag at the left trapezius, 5° back lean | consolidated §5 |
| Combat shirt yoke | fine vertical ribs ≈ 4 mm pitch under both pauldrons (690–740, 195–245) and (880–930, 255–300) | the shirt's shoulder yoke lies over the trapezius/deltoid; the body must give it a smooth convex bed | gear note §3 |

### 2.2 My own measurements (`ref/zoom_torso_*.png`, made with PIL from `reference_full.png`)
Zooms produced: `zoom_torso_neck_shoulders_x4.png` (690–1000 × 100–270), `zoom_torso_neck_gaiter_x8.png` (740–870 × 120–210), `zoom_torso_rtrap_strap_x8.png` (680–790 × 140–270), `zoom_torso_ltrap_rearbag_x8.png` (840–980 × 120–270), `zoom_torso_waist_band_x6.png` (720–920 × 380–520), `zoom_torso_flanks_x3.png` (660–960 × 200–480).

Warm-skin runs (R − B > 25 and lum > 40) down the neck: y 126–132: x 770–823 (53 px = 112 mm — this is the jaw's under-plane and the lit submental skin); y 136–142: 25–39 px (the lit right column only, 53–83 mm); y 144–148: 49–68 px (104–144 mm, the full lit neck width where the chin shadow has ended on the right); from y 150 the detector catches the gaiter's lit folds. Lit (lum > 90) skin per row: y 130 x 770–802; y 139 x 761–787; y 148 x 754–801; y 154 x 752–805; y 157 x 752–790 (the roll begins). Luminance down the x = 780 column: 60 at y 126 (jaw shadow edge), rising to 136–137 at y 134–140 (the SCM belly), a dip to 119–123 at y 141–147 (the groove between SCM and the clavicular head), 129–132 at y 148–150, then falling through 105 → 94 (y 152–159, the roll's upper face) to 37 at y 165 (the roll's shadow). The ROI (750–860) × (128–162) is 26.8 % lit (lum > 90) and 57.5 % above lum 45 — these two fractions are the hero-frame neck metric (§8.2).

Dressed silhouette (first/last column with lum > 45 in x 600–1000) by row, as targets for the garment specs and for the V6 overlay (mm at 2.12 mm/px): y 140: 625–857 (492); y 160: 627–910 (600); y 180: 624–923 (634); y 200: 624–944 (678); y 220: 627–950 (685); y 240: 626–952 (691); y 260: 627–949 (683); y 300: 632–955 (685); y 340: 622–960 (717, forearm guards enter); y 380: 649–949 (636); y 400: 649–930 (596); y 440: 648–984 (712, left forearm). The rows 160–300 are the pauldron/strap envelope: the bare body under them is 625 at the deltoids and 340 at the chest.

Shirt-yoke rib pitch under the right pauldron: 2 px ≈ 4 mm, vertical — the yoke panel is a flat-knit rib whose wales run down the shoulder; irrelevant to the body except that the rib must drape over a smooth trapezius–deltoid saddle.

### 2.3 Ambiguities and decisions
* **D1 — Rest stature.** The agreed 1855 mm is the height of the *posed* figure (skull top y 20 → sole y 895), measured with the knees flexed 17°/9° and the thighs abducted, which costs 22 mm (spec 03 §3.1). Spec 03 nevertheless uses 1855 as the rest stature with rest hip 851 and posed hip 829, which puts the posed skull top at 1833 (y 30, 10 px above the drawing's). **This spec keeps the trunk exactly as drawn in the pose** — rest = posed + 22 for every trunk landmark — so the rest stature measures **1877** (skull top), the height macro is solved to 1877, and the game export scales from the rest body. This is inside the analysts' stature range (1830–1880) and the only choice that puts the chin, shoulders, carrier, belt and crotch all on their pixel rows at once. Fallback (one constant, `STATURE_REST_MM`): 1855, accepting the head 10 px low. Spec 03's "stature 1855 rest / chin 1620 / shoulder 1521" text must be reconciled at the critique pass; its *mechanics* (crest 1031, hip 851, femur 325) are unchanged.
* **D2 — Where the long waist lives.** The analysts' "torso +13 %" is placed entirely between the 10th rib (rest 1189, ANSUR-scaled and left where a real ribcage is) and the iliac crest (rest 1031, spec 03): a 158 mm lumbar flank instead of ANSUR's 56. The ribcage is not stretched, the neck is lengthened only 28 mm (D4). The flank gets two extra edge rings (§4.4) so the navel and obliques have geometry.
* **D3 — Shoulder joint centres.** The pose note's (675,200)/(935,200) (551 mm apart, 10 mm below the pad tops) are not anatomical; the glenohumeral centre sits 40–50 mm below and 15–20 mm medial of the acromion tip. Adopted: **acromion tips X ±257, rest h 1512 (posed 1490, y 192); GH centres X ±240, Y −20, rest h 1452 (posed 1430, y 220)**. The arm spec re-derives its upper-arm vectors from these; the change against the pose note is ≤ 7° on the right arm, inside the stated ±5–10° bands, and makes the upper arm 345 mm (ANSUR 340 scaled).
* **D4 — Neck length.** Chin (lit pad) to shoulder line is 66 px = 140 mm in the drawing against 105–120 for the ANSUR body: the neck is 25–30 mm long. Adopted: menton (rest 1640) to suprasternale (rest 1507) = 133 mm; C7 at rest 1592; `neck-scale-vert-incr` + `measure-neck-height-incr` solved to it. The gaiter hides most of it, which is why this is cheap to get wrong and cheap to get right.
* **D5 — Trunk lean.** Shoulder midpoint x 801–802 vs stance midpoint 830 → X −58; pelvis centre −40 (spec 03). Adopted: a 2° lateral flexion of the lumbar spine to his right (`spine03` roll −2°), giving the shoulder midpoint X −58 ± 8 posed. The analysts' "level, roll 0" is kept for the shoulders themselves (acromia at equal height ± 3).
* **D6 — Navel.** The pose note's "navel est. y 470" is a placeholder ("just below the vest hem"). A navel sits a little above the crest in a long-waisted man; adopted rest h 1085 (posed 1063, y 393) — hidden under the vest hem, and that is where it should be.
* **D7 — What is visible is right-side neck only.** The whole bare-skin acceptance of this part in the hero frame is one lit trapezoid; the shadow edge and lit fraction (§2.2) are measured, everything else is built to the real-world tables and judged on bare renders.
* **D8 — Moles.** None on the face (face note). Default: none on the neck (visible); the realistic sparse set of §5.2 on the hidden trunk, switchable (`MOLES = True`). Client question §10.2.

---

## 3. Real-world reference

Tags: **M** measured from the reference, **S** sourced (ANSUR II "Tight" column, `notes/research_dimensions.md` §1, × 1.0049 to 1855 unless the drawing overrides), **E** estimated (anatomy texts / typical adult male values, no primary source on this machine).

### 3.1 Vertical landmarks (trunk; REST and POSED; the drawing's y for the posed value)

| Landmark | REST h | POSED h | y px | Tag | Note |
|---|---|---|---|---|---|
| Skull top (head spec) | 1877 | 1855 | 20 | M (D1) | head 232 tall (109 px) |
| Chin, lit pad / menton | 1645 / 1640 | 1623 / 1618 | 129 / 131.5 | M | face spec |
| Hyoid body (join line with the face spec) | 1622 | 1600 | 140 | E | 18 below the menton; the beard's neckline fades out here |
| Thyroid notch (top of the Adam's apple) | 1598 | 1576 | 151 | E | 24 below the hyoid |
| Laryngeal prominence, apex | 1592 | 1570 | 154 | E | at the gaiter's top edge → hidden |
| Cervicale (C7 spinous process) | 1592 | 1570 | — | S (acromion + 80) | the "vertebra prominens" bump |
| Cricoid arch | 1570 | 1548 | 165 | E | |
| Trapezius–neck junction (lateral neck base, front silhouette) | 1560 | 1538 | 170 | M | pose note's "neck base" |
| Acromion tip | **1512** | **1490** | 192 | M (D3) | the pads' tops 190–195 |
| Suprasternale (jugular notch) | 1507 | 1485 | 194 | S (acromion − 5) | the carrier's top edge is 15–20 below |
| Sternoclavicular joint (clavicle's sternal end) | 1495 | 1473 | 200 | E | |
| Glenohumeral joint centre | 1452 | 1430 | 220 | E (D3) | |
| Deltoid, widest point | 1455 | 1433 | 219 | E | bideltoid 625 here |
| Axilla floor (anterior fold apex) | 1395 | 1373 | 247 | S (acromion − 111 → 1401; lowered 6 for the arm pose) | |
| Nipple | 1360 | 1338 | 263 | S (acromion − 153) | pose note's 252 was ANSUR unshifted |
| Xiphoid tip / infrasternal angle | 1345 | 1323 | 270 | E (sternum 165 long) | |
| Scapula, inferior angle (T7) | 1365 | 1343 | — | E | |
| Costal margin, lowest lateral point (10th rib) | 1189 | 1167 | 344 | S (kept where the ribcage is) | the cummerbund's top edge |
| Navel | 1085 | 1063 | 393 | E (D6) | under the vest hem (398) |
| Waist, narrowest section | 1060 | 1038 | 405 | M + E | 310 breadth |
| Iliac crest, highest point (spec 03) | 1031 | 1009 | 419 | spec 03 | |
| Waistband top (spec 09) | — | 890 | 475 | spec 09 | body breadth 315 here |
| Trochanters (spec 03) | 861 | 839 | 499 | spec 03 | hips 345 |
| Hip joint centre (spec 03) | 851 | 829 | 505 | spec 03 | |

### 3.2 Breadths, depths and girths of the trunk (REST; the solver's targets)

| Measure | Value | ANSUR Tight | Tag | Where measured (`measure_torso`) |
|---|---|---|---|---|
| Bideltoid breadth | **625** | 506 | M | widest X extent in the band h 1430–1480 |
| Biacromial breadth (tip to tip) | 515 | 424 | E (bideltoid − 2 × 55 deltoid overhang) | acromion marker vertices |
| GH centre to GH centre | 480 | ≈ 390 | E (D3) | joint cubes `joint-r/l-shoulder` [VERIFY names] |
| Shoulder circumference (over the deltoids, h 1455) | 1400 | 1175 | E (ellipse 625 × 265, +2 %) | `slice_measure(1455)` |
| Chest breadth at the nipple (h 1360) | 340 | 290 | E (lean V-taper, 1.17 × ANSUR) | slice breadth |
| Chest depth at the nipple | 250 | 245 | S (+2 % for the lifted chest) | slice depth |
| Chest circumference (h 1360, under the arms) | **1100** | 1029 | E (chest/waist 1.25) | slice girth |
| Interscye (back width between the posterior axillary folds, h 1395) | 490 | 425 | E (× 1.15) | back-face X extent at the axilla |
| Underbust / 10th-rib girth (h 1189) | 960 | — | E | slice girth |
| Waist breadth, narrowest (h 1060) | **310** | 315 | M (307 at the waistband, 310 adopted) | slice breadth |
| Waist depth (h 1060) | 215 | 219 | S | slice depth |
| Waist circumference (h 1060) | **880** | 893 | E (ellipse 310 × 215 × 1.055) | slice girth; spec 09 wants 850–880 at h 890 |
| Body breadth at the waistband (posed h 890 = rest 912) | 315 | — | M (307) + E | slice breadth |
| Hip breadth / buttock girth | 345 / 999 | 343 / 994 | spec 03 | — |
| Waist back length (C7 → waist at the crest) | 561 | 490 | derived (1592 − 1031) | — |
| Chest front: suprasternale → xiphoid (sternum) | 162 | — | E | — |
| Body mass (for the SSS thickness proxy and the look) | 92 kg | 83.6 | consolidated 88–95 | — |

### 3.3 Trunk cross-sections (REST, mm; a = half-breadth lateral, b_f = front half-depth from the coronal plane Y0 of the hip centres, b_b = back half-depth; corners describe how rectangular the section is)

| h | Section | a | front Y | back Y | Girth | Shape | Tag |
|---|---|---|---|---|---|---|---|
| 1565 | mid-neck (larynx) | 67 | −77 (apex of the prominence; −70 beside it) | +55 | 410 | round-oval, flat at the back (nape) | M + E |
| 1512 | neck base (C7 → suprasternale) | 76 | −96 | +72 | 460 | oval, widening into the trapezius | E (ANSUR base 431 × 1.07) |
| 1455 | shoulders (deltoids) | 312 | −130 (anterior deltoid) | +135 (posterior deltoid) | 1400 | wide flat lozenge, the chest front at −118 between the deltoids | M + E |
| 1395 | axilla | 200 (lats' upper edge 245) | −125 | +122 | 1130 (incl. lats) | rounded rectangle | E |
| 1360 | nipple | 170 | −128 | +122 | 1100 | rounded rectangle, corners r 70 | E |
| 1300 | lower pec / 7th rib | 168 | −122 | +118 | 1060 | | E |
| 1250 | 8th rib | 165 | −118 | +114 | 1030 | | E |
| 1189 | 10th rib (costal margin) | 160 | −112 | +112 | 960 | the infrasternal angle 75° opens here | E |
| 1130 | upper flank | 156 | −108 | +110 | 905 | oval; erector columns at X ±35 proud +6 | E |
| 1085 | navel | 155 | −108 (navel pit −102) | +110 | 885 | | E |
| 1060 | narrowest waist | **155** | −105 | +110 | **880** | oval; the obliques flatten the sides | M + E |
| 1031 | crest (spec 03) | 150 soft (140 bone) | −102 | +112 | 870 | spec 03 owns below | spec 03 |
| 912 (posed 890) | waistband | 157 | −95 | +125 | 880 | flaring to the trochanters | M + spec 03 |

### 3.4 Front of the trunk — components (REST, left side listed where paired; right is the mirror unless §3.7 says otherwise)

| Component | Position (X, Y, Z) | Size / form | Relief | Tag |
|---|---|---|---|---|
| Suprasternal (jugular) notch | (0, −96, 1507) | U-notch 30 wide, 12 deep between the clavicular heads of the SCMs | 10–12 deep | E |
| Manubrium / sternal angle | (0, −104, 1507 → 1455); angle of Louis at (0, −112, 1457) | 50 tall, 55 wide; the angle is a 3 mm transverse ridge | +2 | E |
| Sternal body | (0, −118, 1455 → 1345) | 110 tall, 30–35 wide, flat; the pectoral gap 18–22 wide shows it | flush, 1 mm groove each side | E |
| Xiphoid | (0, −112, 1345) | 25 tall, soft hollow 20 Ø below it | −3 | E |
| Clavicle, sternal end | (+18, −98, 1495) | 22 Ø knob | +4 | E |
| Clavicle, shaft | S-curve: (+18, −98, 1495) → (+85, −112, 1498) convex forward → (+160, −95, 1503) → acromial end (+245, −45, 1512) concave forward | 165 long, 15 Ø medially → 12 × 20 flattened laterally | +2 to +3 rod relief under 3–4 mm skin; the whole length palpable | E (male 150–160 scaled for the 515 biacromial) |
| Supraclavicular fossa | behind the medial 2/3 of the clavicle, centre (+95, −80, 1525) | 90 × 35 triangle | −12 to −15 (lean man) | E |
| Infraclavicular fossa / deltopectoral triangle | (+185, −118, 1472) | 35 × 25 | −4; the cephalic vein runs in its groove down to the arm | E |
| Acromion | (+257, −30, 1512) | 45 × 35 flat shelf, 8 thick, pointing laterally and a little forward | flush shelf, a 2 mm step to the deltoid | E |
| Acromioclavicular joint | (+243, −40, 1511) | 10 mm bump | +2 | E |
| Deltoid, anterior head | origin along the lateral third of the clavicle; belly max at (+275, −95, 1440) | | +8 over the humeral head | E |
| Deltoid, lateral head | from the acromion; widest at (+312, −15, 1455) | the cap: 110 × 130 footprint | the 625 point | M |
| Deltoid, posterior head | from the scapular spine; max at (+280, +110, 1445) | | +6 | E |
| Deltoid insertion (tuberosity) | (+262, −10, 1310) — hand-over to the arm spec at h 1400 ± 20 | V-shaped tendon 25 wide | −2 groove either side | E |
| Pectoralis major, clavicular head | from the medial half of the clavicle to (+200, −120, 1400) | 60 tall band | +6 | E |
| Pectoralis major, sternal head | the mass; max thickness at (+110, −128, 1365) | 25 proud of the ribcage at muscle 0.7 | | E |
| Pectoral lower border (the pec line) | (+175, −100, 1385) axillary fold → (+120, −125, 1350) → (+22, −122, 1340) sternal | a 220 mm curve, slight overhang 3 mm, soft shadow line | −2 crease laterally fading medially | E |
| Anterior axillary fold | (+185, −95, 1395 → 1375) | the pec's lateral edge rolling over the humerus | | E |
| Nipple | (+115, −130, 1360), pointing 10° down and 15° outward | areola 26 Ø oval (28 × 24), nipple 9 Ø, 3 proud, with 8–10 Montgomery bumps 1 Ø | +3 / +0.5 | E (nipple spacing 230) |
| Rectus abdominis | from the 5th–7th costal cartilages to the pubis; two columns 65 wide each | relief 4–5 above the obliques at muscle 0.7, weight 0.45 | | E |
| Linea alba | (0, front, 1345 → 1085 navel → 920) | 8 wide groove above the navel, 4 wide below | −2 above the navel, −1 below | E |
| Tendinous intersections | at h 1300 (just below the xiphoid), 1230, 1160 (the pair above the navel); a faint 4th at 1100 | transverse grooves 60 long, slightly chevroned (medial ends 5 lower) | −2.5, −2.5, −2, −1 | E |
| Navel | (0, −102, 1085) | 12 tall × 9 wide oval pit, 7 deep, with an upper hood fold 14 wide overhanging 2 mm; the floor shows a 3 mm knot | −7 | E |
| Semilunar line | lateral border of the rectus, X ±70, 1345 → 960 | | −2 | E |
| External obliques | flank, from ribs 5–12 to the crest; the "digitations" interlock with serratus at (+160, −60, 1300 → 1200) | 3–4 visible serratus digitations 25 × 15 each | +3 | E |
| Costal arch (infrasternal angle) | from the xiphoid (0, −112, 1345) along ribs 7–10 to (+160, −60, 1189) | 75° included angle | +2 rim visible on inhale; at rest the arch is a soft 1.5 mm edge | E |
| Inguinal / crest region | spec 03 | | | — |

### 3.5 Back and shoulder girdle — components (REST)

| Component | Position (X, Y, Z) | Size / form | Relief | Tag |
|---|---|---|---|---|
| C7 spinous process (vertebra prominens) | (0, +72, 1592) | 14 mm bump | +4 (the most prominent neck bone) | E |
| T1 spinous | (0, +80, 1572) | | +2 | E |
| Nuchal furrow | (0, +52 → +72, 1660 → 1592) | the midline groove between the trapezius columns on the nape | −4 | E |
| Thoracic spinous processes T2–T12 | (0, +118 ± 4, 1550 → 1200), pitch 28–32 | the thoracic kyphosis apex at T7 (0, +122, 1365) | the spinous tips sit in the bottom of the furrow, each a 1.5 mm bump | E |
| Spinal furrow, thoracic | between the erector columns X ±45; deepest at T5–T8 | 90 wide | −15 to −20 (muscle 0.7) | E |
| Erector spinae columns, lumbar | X ±35, Y +112, 1200 → 1031 | 70 wide each | +6 over the lumbar fascia; the furrow −6 to −8 | E |
| Lumbar lordosis | apex at L3 (0, +98, 1100) — the spine's most anterior lumbar point; the lordotic curve 40–45° Cobb between T12 and S1 | — | — | E |
| Thoracic kyphosis | 28° Cobb T1–T12 (erect, "chest lifted" −3°) | | | E |
| Cervical lordosis | 25° Cobb C2–C7 | | | E |
| Scapula, superior angle | (+80, +100, 1515) | | hidden under the trapezius | E |
| Scapular spine | from the vertebral border (+80, +108, 1490) rising to the acromion (+257, −30, 1512); the spine's crest is a 10 mm ridge | 180 long | +3 to +5, the infraspinous fossa below it −3 | E |
| Scapula, vertebral (medial) border | X +80, from 1515 to 1365 | 150 long | +2 (the rhomboids pull it flat in a soldier's posture) | E |
| Scapula, inferior angle | (+80, +112, 1365) | | +3 (stands 3 mm off the ribs at rest; +8 when the arm is across the chest) | E |
| Scapula, size | 105 wide × 160 tall | | | E (male average 100 × 155) |
| Infraspinatus / teres | the fossa below the spine; teres major bulge at (+200, +90, 1395) | | +4 | E |
| Trapezius, upper fibres (the slope) | from the nuchal line / C7 down to the acromion and the lateral clavicle: the slope line (+78, +15, 1560) → (+257, −30, 1512), slope **18°** below horizontal, slightly convex (+4 at mid-slope) | the trap "shelf" 60 thick front-to-back at the neck base | | M (y 170 → 192) |
| Trapezius, middle and lower | the diamond to T12 (0, +115, 1200) | flat sheet, the medial edge visible as a faint 1 mm step at X ±25 | | E |
| Posterior axillary fold (lat + teres) | (+205, +75, 1395 → 1370) | | the lat's lateral edge: the V-taper's back silhouette from (+245, +40, 1395) to the crest (+150, +60, 1031) | E |
| Latissimus dorsi | widest at the axilla (interscye 490), tapering; the lumbar aponeurosis flat from 1200 down | | +6 over the lower ribs | E |
| PSIS dimples, sacral triangle | spec 03 | | | — |

### 3.6 Neck — components (REST; the head is in its rest heading −Y)

| Component | Position (X, Y, Z) | Size / form | Relief | Tag |
|---|---|---|---|---|
| Neck axis | from the suprasternale/C7 midpoint (0, −12, 1550) to the skull base (0, −8, 1650); tilted forward 8° (the cervical spine leans forward then curves back — lordosis 25°) | mid-neck section 135 × 132 | | E |
| Neck breadth / depth / girth at the larynx (h 1565) | 135 / 132 / 410 | | | M (0.86 × bigonial) |
| Neck base girth (h 1512) | 460 | | | E |
| Hyoid body | (0, −72, 1622) | 25 wide × 10 tall bar; the greater horns reach back to (±30, −45, 1625) | +2 under the submental skin; the submental–neck angle (cervicomental) 105° is set here with `neck-double-decr` | E |
| Thyrohyoid membrane | (0, −76, 1610) | soft 12 mm hollow | −2 | E |
| Thyroid cartilage (Adam's apple) | apex (0, −77, 1592); laminae 35 wide meeting at 90°; the thyroid notch 10 deep at the top (0, −74, 1598) | 40 tall | **+9** at the apex, fading over 25 mm each side; the notch a V | E (prominent in a lean 40-year-old man) |
| Cricoid | (0, −72, 1570) | 25 wide ring | +3 ring below a 4 mm cricothyroid dip | E |
| Trachea | (0, −66, 1560 → 1507), 20 Ø | 3 visible rings at 4.5 mm pitch when lit from the side | +1 each | E |
| Sternocleidomastoid, sternal head | from the manubrium (±14, −96, 1505) (the tendon, 10 wide, 30 long, cord-like) up and back to the mastoid (±72, +15, 1660, face spec) | 25–30 wide belly, max thickness at (±48, −45, 1585) | **+6** (rest); right side **+9** when the head is turned left (§7.5) | E; M for the right ridge at (778,146) |
| Sternocleidomastoid, clavicular head | from the medial clavicle (±40, −95, 1500), flat 25 wide, joins the sternal head at h 1555 | the gap between the heads = the lesser supraclavicular fossa (±28, −88, 1515), 15 × 20 | −3 | E |
| External jugular vein | from behind the jaw angle (±70, +5, 1650) crossing the SCM obliquely to (±95, −40, 1530) | 5 Ø | +1.2, blue-green tint 12 % | E |
| Carotid pulse groove | between the SCM's front edge and the larynx, (±32, −70, 1575) | 12 wide | −2 | E |
| Anterior neck creases | 2 to 3 horizontal lines: at h 1585 (full ring, dominant, 0.6 deep), 1605 (front half, 0.4 deep), 1560 (faint, 0.3) — relaxed on the lit right, compressed on the turned-to side (§7.5) | 0.5–0.8 wide | −0.3 to −0.6 | E (age 40) |
| Platysma | thin sheet; two faint vertical bands (±25, −72, 1560 → 1610) appear only with the jaw clenched 0.1 → amplitude 0.3 | | +0.3 | E |
| Trapezius anterior edge (neck side) | from the occiput down to the clavicle's lateral third; the posterior triangle between it and the SCM (±85, −20, 1560), 60 × 45 | | −4 | E |
| Nape | from the hairline (face/hair spec, ≈ h 1650 at the midline) down to C7; two trapezius columns X ±28 with the nuchal furrow between | sun-exposed, coarser, redder (§5.1) | | E |
| Submental skin / under-jaw plane | face spec above the hyoid line h 1622; blend band 1615–1630 | | | interface |

### 3.7 Asymmetries (the right is NOT a plain mirror)
Right-handed soldier, rifle on the right shoulder: right trapezius upper fibres +2 mm thicker, right deltoid +3 mm, right pectoral +2 mm, right scapula sits 4 mm lower and 6 mm more lateral at rest (dominant-arm droop); the left SCM is 1 mm thicker (habitual head turn to the left to look over the rifle? no — chosen simply so that the two cords are not identical); the navel is shifted 2 mm to his left; the right nipple sits 3 mm lower and 2 mm more lateral; the linea alba wanders 2 mm. All applied by `sculpt.py` after mirroring (spec 03 §4.5 pattern).

### 3.8 Skin and surface by region (albedo sRGB; the face base is #b98670, L* 60 — the trunk is paler because it never sees the sun)

| Region | Albedo | Roughness | SSS scale (m) | Coat | Micro-relief / notes | Tag |
|---|---|---|---|---|---|---|
| Neck, front and sides, above the collar line (weathered) | #b98670 → warm tint #c08a74 under the jaw where the stubble shadow is (face spec paints the stubble) | 0.46 | 0.0035 | 0.10 / 0.40 | fine pores 1 per 0.9 mm, the creases of §3.6; slight sheen on the SCM belly | consolidated |
| Nape and back of the neck (most sun-exposed skin of the body) | **#b07c66** (ΔL* −3 vs face, redder, +3 % saturation) | 0.52 | 0.0035 | 0.06 | coarser: pores 1 per 0.7 mm, 0.12 mm deep; cross-hatched skin lines 0.7 mm pitch; 2 % mottle (freckling is absent: Fitzpatrick II–III, no freckles on the face) | E |
| Collar sun line | gradient 20–30 mm wide from the neck colour to the trunk colour, following the shirt collar ring: front h 1500 (rest) rising to 1575 at the back, dipping 12 mm at the sternal notch (the zip collar's V) | — | — | — | a second, fainter line 15 mm lower (T-shirt crew neck from off-duty days, 30 % strength) | E |
| Chest (pectorals, sternum) | **#c9a58d** (L* 68) | 0.48 | 0.0042 | 0.08 | pores 1 per 1.3 mm; follicles with the hair; sternum slightly pinker #c99d88 (thin skin over bone) | E |
| Areola / nipple | #a8766a / #9a6660 | 0.55 / 0.60 | 0.0030 | 0.04 | Montgomery bumps 1 Ø +0.5 | E |
| Abdomen | #cca891 (palest), navel pit #a67b68 with AO | 0.50 | 0.0045 | 0.06 | linea alba slightly darker (#c39c86, +hair below the navel) | E |
| Flanks / obliques | #c8a289 | 0.50 | 0.0042 | 0.06 | | E |
| Axilla | #b89078 (greyer, darker; the hair's shadow) | 0.40 (moist) | 0.0030 | 0.14 | | E |
| Shoulder caps (deltoid) | #c4a088, 2 % redder on top (some sun through the shirt — negligible; keep) | 0.48 | 0.0040 | 0.08 | sparse terminal hair §6 | E |
| Upper back | **#c7a088**, 3 % more olive than the chest, with 4 % lightness mottling at 25 mm scale (the back is the most uneven skin of the trunk) | 0.52 | 0.0045 | 0.05 | pores 1 per 1.0 mm, 0.1 deep (the back's pores are the largest on the body); no acne scarring (default — client §10.2) | E |
| Lower back / lumbar | #c9a58d | 0.50 | 0.0045 | 0.06 | | E |
| Vein tint (EJV, cephalic in the deltopectoral groove, superficial chest veins near the clavicle 3 Ø) | 15 % toward #7d8b86 along the §3.6/3.4 tubes, 2 mm feather | — | — | — | | E |
| Moles (hidden trunk only, `MOLES = True`) | 8 flat 2–4 mm #6b4a3c: (+62, −118, 1392), (−140, −120, 1330), (+40, −105, 1240), (−25, +115, 1460), (+95, +110, 1300), (−160, +90, 1380), (+180, −30, 1450 on the deltoid top), (−70, +112, 1150); 1 raised 4 mm (+1.2) at (−110, +105, 1420) | 0.5 | — | — | none on the neck | E (D8) |

---

## 4. Geometry construction plan

Every step is a function in `scripts/parts/04_torso_neck.py` or the shared libraries; nothing is hand-sculpted. Order matters: steps 1–4 are the shared body pipeline (`scripts/lib/proportions.py`, run once by `build_all.py` for specs 03/04/05/06 together — this spec defines the trunk rows of its tables), steps 5–12 are this part's own.

### 4.1 Step 1 — Base human (`proportions.py::create_base()`, shared with spec 03 §4.1)
`HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True, scale=0.1, macro_detail_dict=macro)` with gender 1.0, age 0.615, **muscle 0.70, weight 0.45**, proportions 0.5, cupsize 0.5, firmness 0.5, caucasian 1.0; height solved by secant to `STATURE_REST_MM` = **1877** (D1; start 0.59, measure the evaluated mesh's highest `body` vertex, ≤ 5 iterations, ± 2). Keep the helper geometry visible until step 4 (the joint cubes are the measuring tape: `joint-neck`, `joint-head`, `joint-r/l-clavicle`, `joint-r/l-shoulder`, `joint-spine-1…4`, `joint-pelvis` [VERIFY: dump `basemesh.vertex_groups` names at run time and write them to `renders/04_torso/vgroups.txt`; the script maps roles through a `JOINT_MAP` dict]).

### 4.2 Step 2 — Trunk and neck targets with the measuring solver (`proportions.py::fit_trunk()`)
Loaded with `TargetService.load_target(basemesh, TargetService.target_full_path(name), weight=w)`; negative values are the `-decr` twin with a positive weight; `set_target_value` only after loading (research B pitfall). Per-unit gains are not documented [VERIFY: research_generators has no gain table] so every "solve" row is a damped secant (gain 0.7, ≤ 6 iterations, weights clamped to [0, 1]) against `measure_torso()` on the evaluated mesh; "fixed" rows are set once.

| Target (MPFB file stem) | Start | Mode | Drives | Metric |
|---|---|---|---|---|
| `torso-vshape-incr` | 0.55 | fixed | the V-taper's shoulder-to-waist shape | — |
| `torso-muscle-pectoral-incr` | 0.45 | fixed | pectoral mass 25 proud | — |
| `torso-muscle-dorsi-incr` | 0.50 | fixed | lat width (interscye 490) | — |
| `torso-scale-horiz-incr` | 0.30 | solve | chest breadth 340 at h 1360 | slice breadth |
| `torso-scale-depth-incr/decr` | 0.0 | solve | chest depth 250 | slice depth |
| `measure-bust-circ-incr/decr` | 0.2 | solve | chest girth 1100 | slice girth |
| `measure-underbust-circ-incr/decr` | 0.0 | solve | 10th-rib girth 960 | slice girth at the costal cubes' height |
| `measure-waist-circ-decr` | 0.35 | solve | waist girth 880, breadth 310 (breadth checked, girth solved) | slice at h 1060 after the remap (iterate once more after step 3) |
| `measure-frontchest-dist-incr` | 0.3 | solve | nipple spacing 230 | nipple marker vertices |
| `measure-shoulder-dist-incr` | 0.5 | solve | biacromial 515 | acromion marker vertices |
| `l-/r-upperarm-shoulder-muscle-incr` | 0.55 | solve | bideltoid 625 | band max X |
| `torso-trans-up/down`, `torso-scale-vert-incr` | 0 | not used | the long waist comes from the remap (D2), not from stretching the ribcage | — |
| `measure-napetowaist-dist-incr` | 0 | not used | same reason (spec 03 listed 0.3; drop it) | — |
| `stomach-tone-incr` | 0.4 | fixed | flat lean abdomen, 2 + 2 rectus | — |
| `stomach-navel-up/down`, `-in/out` | solve / 0.3 in | solve | navel at rest 1085 (after the remap) | navel marker |
| `neck-scale-horiz-incr` | 0.30 | solve | neck breadth 135 at the larynx | slice |
| `neck-scale-depth-incr` | 0.25 | solve | neck depth 132 | slice |
| `measure-neck-circ-incr` | 0.3 | solve | mid-neck girth 410, base 460 | slices |
| `neck-scale-vert-incr` + `measure-neck-height-incr` | 0.15 + 0.15 | solve (coupled with the height macro: two unknowns, two measures) | acromion rest 1512 with the skull top 1877 | acromion cubes, top vertex |
| `neck-double-decr` | 0.30 | fixed | cervicomental angle 105° | — |
| `neck-back-scale-depth-incr` | 0.15 | fixed | the thick nape / trapezius neck base | — |
| `neck-trans-forward/backward` | solve | solve | neck axis forward lean 8° (C7 at Y +72, hyoid at −72) | C7 and hyoid markers |
| `l-/r-upperarm-shoulder-muscle` (asym) | +0.03 right | fixed | §3.7 | — |

Markers: MakeHuman has no vertex-group markers for the acromion, nipple, navel or C7; the script finds them once on the base mesh by geometry (nipple = the local front-most vertex of the `breast` helper's footprint; navel = the `stomach` group's deepest front vertex; acromion = the highest vertex of the `shoulder` group's lateral third; C7 = the most posterior `neck` vertex at the lowest `neck` ring) and stores their indices in `assets/body/markers.json` [VERIFY after the first run, by rendering the marker spheres in V1/V2].

### 4.3 Step 3 — Bake, remap and re-loop (`proportions.py::bake_and_remap()`)
1. **Bake** every MPFB shape key into the mesh: `basemesh.shape_key_add(from_mix=True)` → move it to the Basis → remove all other keys. The MPFB keys are never needed again (the scripts rebuild from zero).
2. **Remap z** (the shared `Body.Proportion`, replacing spec 03's `Leg.Proportion` and taking over its knots): monotone piecewise-linear z′ = f(z) with knots (0 → 0), (80 → 80), (526 → 526), (h_hip → 851), (h_crest → 1031), **(h_rib10 → 1189)**, (1877 → 1877), where h_hip, h_crest and h_rib10 are measured on the baked mesh (hip and crest from the joint cubes, the 10th rib from the lowest lateral `torso` vertex ring at the costal margin, expected ≈ 1195). Above the 10th rib the remap is the identity — the ribcage, shoulders, neck and head are placed by step 2's solver and the height macro, not by stretching. Applied with numpy `foreach_set` to every vertex including the helpers so the rig fit follows. Expected: the flank (crest → 10th rib) stretches from ≈ 56 to 158 mm (×2.8); nothing else moves more than 3 mm.
3. **Re-loop the flank**: find the edge loops of the `body` region whose mean z lies between 1040 and 1180 (expected 2 rings); `bmesh.ops.subdivide_edgering(bm, edges=<the ring edges between consecutive flank loops>, cuts=2, interp_mode='LINEAR', smooth=0.0)` adds 2 rings per stretched band (4 new rings ≈ 2 × 150 verts), restoring ≈ 26–30 mm loop spacing. Helpers are left alone. Record the new vertex count. This is the one topology change to the MakeHuman body in the whole project; it happens before the rig fit, the UV layer is interpolated by the op, and spec 03's `Leg.*` keys are generated after it (spec 03 must run its sculpt after this step — see §10.1).
4. Re-measure `measure_torso()` and `measure_leg()`; rerun the waist/navel rows of step 2 if off by more than the tolerance (the baked mesh has no targets left, so these last corrections are done by `sculpt.py` in step 6, not by targets).

### 4.4 Step 4 — Rig fit (`HumanService.add_builtin_rig(basemesh, "default", import_weights=True)` → rename `Morgan.Rig`)
Then dump every bone's head/tail to `renders/04_torso/bones.json`. Expected trunk chain (MPFB `default`, MakeHuman naming, lowest first) [VERIFY the exact names and which end is `spine01`]: `spine05` (L5/S1, head at the pelvis centre h 900), `spine04` (L3), `spine03` (T12), `spine02` (T7), `spine01` (T1, tail at C7 1592), `neck01`, `neck02`, `neck03` (C7 → skull base, three bones of ≈ 25–30 mm), `head`, `clavicle.L/R` (sternal end (±18, −98, 1495) → acromial end (±245, −45, 1512)), `shoulder01.L/R` (MakeHuman's scapular link, acromion → GH centre), `upperarm01.L/R` (head = GH centre (±240, −20, 1452)), `breast.L/R` (nipple). `BONE_MAP` in `scripts/lib/rig_names.py` maps roles (`PELVIS, LUMBAR_LOW, LUMBAR_HIGH, THORACIC, UPPER_THORACIC, NECK_LOW/MID/HIGH, HEAD, CLAVICLE, SCAPULA, UPPERARM`) to whatever the dump says; every other spec uses the roles. If the fitted GH head is not within 6 mm of (±240, −20, 1452) the script moves it in Edit mode (real `select_set` + `mode_set`, research C §7) and re-parents the weights unchanged.

### 4.5 Step 5 — Vertex groups for the part (`weights.py::make_region_groups()`)
`Torso.Region` (body vertices with 1031 ≤ z_rest ≤ 1622, plus the deltoid caps out to X ±320 above h 1400), `Neck.Region` (z 1507 → 1622, within 90 mm of the neck axis), `Torso.Flank` (1031–1189), `Torso.Chest`, `Torso.Back` (Y > +40), `Torso.Shoulder.L/R` (deltoid + acromion), `Torso.Axilla.L/R`, `Torso.Nape`, `Torso.Collar` (the collar ring ±15 mm for the sun line), `Torso.Joints` (shoulder and neck bands for Corrective Smooth), `Torso.NoHair` (areolae, the collar line's upper 20 mm, the SCM fronts), and the garment bands of §10.1 (`Torso.Band.StrapL/R`, `Torso.Band.CarrierTop`, `Torso.Band.Cummerbund`, `Torso.Band.Gaiter`, `Torso.Band.Waistband`), all with a 6 mm linear falloff. Blend bands with the neighbours: face 1615–1630, arms 1380–1420 at the deltoid, legs 1020–1045 at the crest.

### 4.6 Step 6 — Layer A: landmark sculpt by script (`sculpt.py` `soft_inflate(centre, r, amount)`, `soft_move(centre, r, vector)`, `soft_line(p0, p1, r, amount)` — the last is new: a Gaussian tube along a polyline, needed for clavicles, SCMs, creases and the costal arch; all on shape key `Torso.Sculpt`, left side then `mirror_shape_key('X')` then the §3.7 asymmetries)
Order and parameters (mm), REST:
1. **Clavicles**: `soft_line` along the S-curve of §3.4 (4 points), r 9, +2.5; the sternal knob `soft_inflate` (±18, −98, 1495) r 8, +3; the supraclavicular fossa `soft_move` (±95, −80, 1525) r 28 by (0, +9, −3); the lesser fossa `soft_move` (±28, −88, 1515) r 9, (0, +3, 0); the deltopectoral groove `soft_move` (±185, −118, 1472) r 12, (0, +4, 0).
2. **Sternal notch and sternum**: `soft_move` (0, −96, 1507) r 14 by (0, +10, −2); the sternal angle `soft_line` (−20…+20, −112, 1457) r 5, +2; the sternal gap `soft_move` (0, −118, 1455→1345) as a line r 10, (0, +2, 0); the xiphoid hollow `soft_move` (0, −112, 1340) r 11, (0, +3, 0).
3. **Pectorals**: `soft_inflate` the sternal head belly (±110, −128, 1365) r 55, +5 (the targets gave 20 of the 25); the clavicular head band `soft_line` (±40, −110, 1480) → (±200, −120, 1400), r 22, +3; the pec line crease `soft_line` along the 220 mm curve, r 4, −1.5; the anterior axillary fold `soft_inflate` (±185, −95, 1385) r 14, +2.5.
4. **Nipples**: `soft_inflate` areola (±115, −130, 1360) r 13, +1; nipple r 4.5, +3 (then the direction tilt by `soft_move` the nipple tip (0 → −3 X outward, 0, −2)); Montgomery bumps are layer C.
5. **Deltoids and acromion**: `soft_inflate` the lateral cap (±312, −15, 1455) r 45, +4 (bideltoid trimmed to 625 ± 2 by measuring and rescaling the amount); anterior head (±275, −95, 1440) r 30, +3; posterior (±280, +110, 1445) r 28, +2; the acromion shelf `flatten_to_plane` (spec 01's op) on a 45 × 35 patch at (±257, −30, 1512), normal +Z, blend 0.6; the AC bump `soft_inflate` (±243, −40, 1511) r 6, +2; the insertion groove `soft_line` (±255, −25, 1330) → (±268, 0, 1300) r 6, −2 (hand-over to the arm spec).
6. **Trapezius slope**: `soft_line` from (±78, +15, 1560) to (±257, −30, 1512) r 35, +4 at mid-slope tapering to 0 at both ends (amount profile sin), then `soft_inflate` the trap shelf (±60, +30, 1570) r 30, +3; C7 `soft_inflate` (0, +72, 1592) r 8, +4; the nuchal furrow `soft_line` (0, +52, 1660) → (0, +72, 1592) r 7, −3.
7. **Scapulae**: spine `soft_line` (±80, +108, 1490) → (±257, −30, 1512) r 9, +4 (fading to 0 over the last 40 mm where it meets the acromion); medial border `soft_line` (±80, +100, 1515) → (±80, +112, 1365) r 7, +2; inferior angle `soft_inflate` (±80, +112, 1365) r 10, +3; infraspinous fossa `soft_move` (±150, +105, 1450) r 35, (0, −3, 0); teres bulge `soft_inflate` (±200, +90, 1395) r 18, +3.
8. **Spinal furrow and erectors**: furrow `soft_line` (0, +120, 1550) → (0, +122, 1365) → (0, +112, 1200) → (0, +110, 1031), r 22 thoracic / 16 lumbar, −6 thoracic / −3 lumbar (the targets gave the rest); erector columns `soft_line` (±38, +112, 1200) → (±35, +115, 1031), r 25, +4; spinous tips: 11 `soft_inflate` r 3, +1.2 along the thoracic line at 30 mm pitch.
9. **Lats and V-taper**: `soft_inflate` the lat's lateral wall (±230, +40, 1395) → (±165, +60, 1100) as a line r 40, amount +5 at the top → 0 at the bottom; posterior axillary fold `soft_inflate` (±205, +75, 1385) r 14, +2.5.
10. **Abdomen**: linea alba `soft_line` (0, −120, 1340) → (0, −102, 1085) r 5, −2 and (0, −100, 1080) → (0, −95, 930) r 4, −1; rectus columns `soft_line` (±33, −120, 1330) → (±32, −100, 960) r 24, +3; tendinous intersections `soft_line` (±5 → ±62, front, 1300 / 1230 / 1160 / 1100) r 4, −2.5 / −2.5 / −2 / −1 with the medial ends 5 mm lower; semilunar lines `soft_line` (±70, front, 1345 → 960) r 5, −2; navel: `soft_move` (0, −102, 1085) r 9 by (0, +7, 0), hood fold `soft_inflate` (0, −103, 1093) r 8, +2, then the knot `soft_inflate` (0, −106, 1083) r 2.5, +1.5; serratus digitations: 4 `soft_inflate` r 10, +2.5 at (±160, −60, 1300/1265/1230/1200) with (±150, −45, …) tails; costal arch `soft_line` (0, −112, 1345) → (±90, −95, 1260) → (±160, −60, 1189) r 7, +1.5.
11. **Neck**: SCM sternal head `soft_line` (±14, −96, 1505) → (±48, −45, 1585) → (±72, +15, 1660) r 13, +6 (tendon segment r 5, +3); clavicular head `soft_line` (±40, −95, 1500) → (±48, −60, 1555) r 10, +2; larynx: thyroid laminae `soft_inflate` (0, −77, 1592) r 17, +9 with the notch `soft_move` (0, −74, 1598) r 4, (0, +4, 0); cricoid `soft_inflate` (0, −72, 1570) r 10, +3, cricothyroid dip `soft_move` (0, −74, 1581) r 5, (0, +3, 0); trachea rings: 3 × `soft_line` half-rings r 2.5, +1 at 1540/1531/1522 (hidden by the gaiter, cheap); carotid groove `soft_line` (±32, −70, 1560) → (±30, −72, 1600) r 7, −2; posterior triangle `soft_move` (±85, −20, 1560) r 22, (0, +4, 0); hyoid `soft_line` (−12 → +12, −72, 1622) r 5, +2; the EJV `soft_line` r 2.5, +1.2 along §3.6; creases 3 × `soft_line` rings r 1.0, −0.6 / −0.4 / −0.3 (these are at the resolution limit of the base mesh and are duplicated in layer B).
12. **Measure again** (`measure_torso()`), trim the amounts where the girth drifted (deltoid, pec, lat) by one proportional pass.

### 4.7 Step 7 — Layer B: relief map (`Torso.Relief`, 4096² EXR, baked)
The same mechanism as spec 03 §4.6: a temporary emission material evaluates a 3D "landmark field" (sum of Gaussian tubes and spots defined by the §3 tables in object space) and is baked with `bpy.ops.object.bake(type='EMIT')` to MakeHuman's UVs (research C §10: works headless, 512² in 0.4 s; 4096² ≈ 25 s). It carries what the base mesh is too coarse to hold: the clavicle's exact 15 mm rod profile, the SCM tendon heads, the three neck creases (ring tubes r 0.8, depth 0.5), the thyroid notch V, the trachea rings, the EJV, the Montgomery bumps, the serratus and rectus edges, the spinous tips, the costal arch edge, and the moles' 0.3 mm rise. Used as `Bump` (distance 0.004) in `Skin.Body` and as the Workbench/LOD relief; on the hero surfaces (the neck strip) the same field also drives a `Displace` modifier (strength 1.0, midlevel 0.5, `vertex_group = Neck.Region`) so the SCM ridge and the creases are real silhouette at V4.

### 4.8 Step 8 — Compression shape keys (`Torso.Compress.Carrier`, `Torso.Compress.Straps`, `Torso.Compress.Cummerbund`; set to 1.0 by `build_all.py` before any cloth simulation, 0 on the bare renders)
Spec 03 §4.7 pattern. `Straps`: `soft_move` along the two strap paths (§10.1, 73 wide, over the trapezius from (±104, −70, 1557) back to (±115, +80, 1520) and forward down the chest to h 1356) inward by 3.5 mm (a 10 kg carrier on padded straps), with a 1.5 mm ridge (`soft_inflate` r 6) just outside each strap edge where the trapezius bulges; `Carrier`: the front bag's top edge presses the upper chest 1.5 mm at h 1470–1485; `Cummerbund`: the band h 1050–1180 pressed 2 mm, a 1 mm roll above its top edge. Weight-driven in animation by the carrier's presence flag (constant 1 in the game export).

### 4.9 Step 9 — Anchors and rings for the neighbours (`Torso.Anchor.*`, Empties and curve rings)
`Torso.Ring.NeckBase` (the ring at rest h 1507 front / 1560 back, girth 460 — the shirt collar and the gaiter's lower seat), `Torso.Ring.Collar` (the sun line and the mandarin collar top, h 1537 front / 1590 back), `Torso.Ring.Gaiter.Top` (posed geometry: front centre 1574, right side 1583, back-left 1625 — the roll's top edge as a tilted ring), `Torso.Ring.CarrierTop` (h 1470 posed at the chest front Y −118), `Torso.Ring.Hem` (h 1053), `Torso.Ring.Cummerbund.Top/Bottom` (1180 / 1050), `Torso.Ring.Waistband` (posed 890, from spec 03/09), `Torso.Curve.Strap.L/R` (the strap centre-lines over the body at body + 6), `Torso.Anchor.Pauldron.L/R` (Empties at the deltoid cap (±290, −20, 1460) with −Y along the cap's outward normal: the pauldron's tier-1 seat), `Torso.Anchor.Antenna` (Empty at (+212, +118, 1505) posed, rear bag surface, Z tilted 5° back), `Torso.Anchor.Acromion.L/R`, `Torso.Anchor.GH.L/R`, `Torso.Anchor.C7`, `Torso.Anchor.Suprasternale`, `Torso.Anchor.Nipple.L/R`, `Torso.Anchor.Navel`. All parented to the matching `Morgan.Rig` bone so they follow the pose.

### 4.10 Step 10 — Hair curves (`Torso.Hair.Chest`, `Torso.Hair.Abdomen`, `Torso.Hair.Axilla.L/R`, `Torso.Hair.Shoulder.L/R`, `Torso.Vellus`; only with `--hair`)
§6; the Curves system with the bundled node assets (research C §3, §10), roots placed by Python from the density map, radius attribute 0.035 mm (terminal) / 0.015 (vellus).

### 4.11 Step 11 — Topology and poly budget
MakeHuman body: 13,380 quads; the `Torso.Region` + `Neck.Region` ≈ 3,900 quads after the flank re-loop (+ ≈ 300). Loop spacing: neck 12–18 mm (adequate for the SCM/larynx with the relief map and displace), chest 20–28, flank 26–30 after step 3, back 25–30. The body's shared `Subdivision` modifier (spec 01: viewport 1, render **3**, `use_limit_surface`, quality 4) gives ≈ 250 k render quads for this region; the Displace of §4.7 sits after the Subdivision and only in `Neck.Region`. Modifier order on `Body.Mesh`: `Armature` → `Corrective Smooth` (factor 0.5, 5 iterations, `vertex_group = Body.Joints` = union of the parts' joint groups, `use_pin_boundary`) → `Subdivision` → `Displace (Neck.Relief)` → `Mask (Hide helpers)`. Object list added by this part: `Torso.Relief` (image), `Torso.Masks` (image), the anchors and rings (≈ 25 Empties/curves, no render geometry), the hair objects (render), `Torso.Markers` (debug spheres, hidden). No separate meshes: the torso is the body.

### 4.12 Step 12 — Stand-ins for the V6 dressed check (`Torso.StandIn.*`, built only by `--eval`, never exported)
So that this part can be checked against the dressed reference before the garment parts exist: `Torso.StandIn.Gaiter` (a cloth-free torus stack: three tori of tube radius 14/13/12 mm at the posed heights 1574/1552/1525 at the front centre, each tilted so the back-left is 40 mm higher than the front, major radius = neck-base radius + 10, material #373029 fleece from research A); `Torso.StandIn.Straps` (73 × 6 mm swept rectangles along `Torso.Curve.Strap.*`, #6d5f50 / #443d36); `Torso.StandIn.Carrier` (a 315 × 420 × 30 mm rounded box at Y −118 − 15 from h 1053 to 1470 posed, #463e34, with a 175 × 90 × 8 mm khaki panel at 1388–1477); `Torso.StandIn.Pauldron.L/R` (105 / 135 mm square plates 8 thick on the deltoid anchors, #837163); `Torso.StandIn.Shirt` (the body offset +1.5 mm from the crest to the hyoid, #332f2d); `Torso.StandIn.Waistband` (torus 45 tall at 845–890, #443d37). These are placeholders at the §2.4 heights, not the garments; their only job is to prove the body puts every edge on its pixel row.

---

## 5. Materials and textures

### 5.1 Skin — `Skin.Body` (shared with specs 01/03/05; one material, regional values via the colour attribute `skin_tint` and the baked `Torso.Masks.png`; node group `Skin.Base` [VERIFY its name in `scripts/lib/materials.py`, spec 01 §5.5])
Principled BSDF: `subsurface_method = "RANDOM_WALK_SKIN"`, Subsurface Weight 1.0, Radius (1.0, 0.2, 0.1), Scale per region (§3.8, 0.0030–0.0045 m; research C §8 showed 0.012 erases pores, 0.003–0.005 keeps them), IOR 1.4, Anisotropy 0.8; Specular IOR level 0.5; Sheen 0.05 white (peach fuzz where vellus is hidden); Coat per region with Coat Roughness 0.35–0.45; `displacement_method = "BUMP"` except `Neck.Region`'s Displace modifier (§4.7). Base colours, roughness, SSS scale and coat are the §3.8 table, blended by the masks with 8–15 mm feathers; the collar sun line is a `Map Range` of the signed distance to `Torso.Ring.Collar` (−15 → +15 mm) mixing the neck colour into the trunk colour, plus the 30 % secondary line 15 mm lower. Subdermal mottling: Noise scale 25 mm → ColorRamp ± 4 % lightness (± 6 % on the back), 2 % hue toward red on the nape and the SCMs, toward blue-green under the EJV and the chest veins. Micro-roughness: + 0.08 × follicle pits, + 0.06 on the nape, − 0.06 along veins; the areola + 0.07.

### 5.2 Masks (`Torso.Masks.png`, 4096², baked like the relief map)
R = terminal hair density (0–1 = 0–6 /cm²) from the §6 map; G = region id packed as 8 levels (neck / nape / chest / abdomen / flank / axilla / shoulder / back) for the `skin_tint` fallback; B = vein proximity (tubes r 2.5, feather 2); A = SSS thickness proxy (fat and muscle thickness table: neck 6 mm, clavicle 3, sternum 4, pec 25, abdomen 12, flank 10, scapular spine 3, erector 20 → normalised to 25 mm) multiplying the SSS scale. A second image `Torso.Masks2.png`: R = collar line signed distance, G = mole map (`MOLES`), B = stubble-boundary feather for the face spec's beard (1 at the hyoid, 0 at 1640), A = compression (the §4.8 bands, for a 2 % darkening under straps in bare renders — off by default).

### 5.3 Micro relief (layer C, shader bump, `Object` coordinates in metres so a Scale of 2500 = 0.4 mm cells)
Bump distance 0.001 m, strength 0.35, summed: (a) follicle pits Voronoi F1 at the regional pitch (neck 0.9 mm, nape 0.7, chest 1.3, back 1.0, abdomen 1.4), threshold 0.12, depth 0.08–0.12; (b) skin lines: two Wave textures at ± 35° to the local body axis, 0.5 mm pitch (0.7 on the nape), distortion 2, amplitude 0.03; (c) neck creases from the relief map × a Wave (1.2 mm pitch across the crease) 0.2 mm, deepened by the `NeckTwist` corrective on the compressed side; (d) Montgomery bumps: Voronoi scale 1 per 3 mm inside the areola mask, smooth 0.3, +0.5 mm; (e) orange-peel Noise scale 900, 0.02 everywhere; (f) `Torso.Relief.exr` as a second Bump (distance 0.004) for LOD. The pore bump survives the SSS at the §3.8 scales (research C §8).

### 5.4 Texture sets and texel density
No downloaded PBR set is used for skin (research A §4 has none; skin is procedural + baked masks). Baked maps are 4096² on MakeHuman's UVs: ≈ 2.4 px/mm [estimated; spec 01 measured the foot's share of the atlas, the torso's share is not measured — [VERIFY: `measure.py::uv_density(region)` at the first run]]. The hero frame needs 0.47 px/mm anywhere on the neck; V4 (100 mm lens at 0.52 m → ≈ 11 px/mm) is served by the resolution-independent layer C, and the relief EXR's 2–4 mm features are 5–10 px wide at 2.4 px/mm — enough. UVs: unchanged MakeHuman body map (the step 3 re-loop interpolates UVs); the only seams are MakeHuman's (down the back's midline and under the arms). The step 3 stretch of the flank is a 2.8× texel-density drop there (to ≈ 0.9 px/mm) — acceptable for the masks, invisible for the procedural layers; spec 09 covers it anyway.

### 5.5 Hex targets
Hero frame (posed, dressed with the stand-ins or the real garments, hero lights of the lighting note §6, AgX Base Contrast), 5 × 5 means at these reference pixels, tolerance ΔE76 < 8 (the camera-matched scene is calibrated on the face's temple #e6bfac and cheek #d19b87 first): (778,146) **#ae806b** (lit right SCM belly), (790,150) **#bd8d76** (neck right side, the brightest neck skin), (780,134) ≈ lum 136 (the SCM belly's peak), (780,144) ≈ lum 121 (the SCM–clavicular-head groove, 15 lum darker), (805,138) **#110a04** (under-jaw shadow, lum ≤ 16), (838,142) **#33383c** (left neck in cool fill, lum 45–65, blue-grey not brown), (845,135) **#494d56**. Bare look-dev scene A (spec 01 §8.1 key at 45°): the mid-chest renders within ΔE < 6 of **#dcc0a8** (the albedo #c9a58d lit as spec 01's foot dorsum calibration shows), the nape within ΔE < 6 of #c4917a, the abdomen ≤ #e0c6ae, the shadow side of the neck ≥ 1.5 stops below the lit side.

---

## 6. Fibres, simulation or dynamics

### 6.1 Hair (Curves objects; `--hair` only; hidden in every dressed render; not exported to the game)

| System | Zone (REST) | Density | Length | Direction / lie | Colour (melanin for the Principled Hair BSDF) | Count |
|---|---|---|---|---|---|---|
| `Torso.Hair.Chest` | sternal patch: an ellipse 90 wide × 150 tall centred (0, front, 1360), plus the two pectoral fields out to the areola (not on it) with density falling to 0 at X ±150; a thin bridge up to the suprasternal notch (0.5 /cm²) | 3.5 /cm² at the sternum, 2 /cm² on the pecs | 18–28 mm (sternum), 10–18 (pec) | down and inward toward the sternum, 20° off the surface, clumped 3–4 (`Clump Hair Curves` 0.4), 15 % curl (`Hair Curves Noise` 0.3 at 12 mm wavelength) | dark brown, melanin 0.75, redness 0.3, 8 % grey (melanin 0.05) matching the chin's grey cast at a lower rate | 1,800–2,600 |
| `Torso.Hair.Abdomen` | the linea alba band 15 wide from the navel to the pubis (spec 03 continues), plus a 25 wide fan above the navel to h 1140 | 4 /cm² below, 1.5 above | 15–22 | downward, flat | same | 300–500 |
| `Torso.Hair.Axilla.L/R` | the axillary fossa 60 × 90 mm centred (±195, −20, 1380) | 25 /cm² | 25–40 | radiating from the fossa floor, clumped 0.6, curl 40 % | melanin 0.8 | 900 each |
| `Torso.Hair.Shoulder.L/R` | deltoid cap and the lateral trapezius, within 70 mm of the acromion | 0.3 /cm² | 8–12 | lateral and down | melanin 0.7 | 60–90 each |
| `Torso.Hair.Nipple` | 6–10 hairs on the areola's rim | — | 10–15 | outward | — | 8 each |
| `Torso.Hair.Lumbar` (optional, `LUMBAR_TUFT`) | the sacral/lumbar midline 60 × 80 at h 1031–1110 | 1 /cm² | 10–15 | down | — | 50 |
| `Torso.Vellus` | the whole `Torso.Region` and `Neck.Region` except the palms-equivalent zones (areolae, the sun line's upper 20 mm handled by the face spec's stubble) | 20 /cm² | 1–2 | along the skin-line direction (the ± 35° field), 10° off the surface | melanin 0.05, radius 0.015 mm | ≈ 60,000 (render only for V4; `Trim` to 0 elsewhere by distance to the camera) |
| None | upper back, nape below the hairline (vellus only), the neck front (the beard's neckline is the face spec's and fades out at the hyoid) | | | | | |

Roots are placed by Poisson-disc sampling in the UV space weighted by `Torso.Masks.R` (`numpy`; 0.4 s for 3 k points), lifted 0.1 mm along the normal; `Set Hair Curve Profile` radius 0.035 mm root → 0.015 tip. Render: `sc.cycles_curves.shape = "THICK"`; cost ≈ 3× per 40 k strands in frame (research C §3) — the vellus is only turned on for V4 and a chest macro.

### 6.2 Simulation
None on the body. The body provides: `Body.Collider` (decimated copy, 6–8 k faces, Collision modifier `thickness_outer 0.002`, friction 8 — spec 09's object, extended upward to the hyoid here) for the gaiter and shirt cloth simulations; the `Torso.Compress.*` keys at 1.0 before any sim; the `Torso.Ring.*` seats for pinning rows (the gaiter's lower edge pins to `Torso.Ring.NeckBase` + 20 mm; the shirt's collar to `Torso.Ring.Collar`).

### 6.3 Dynamics in animation
Breathing: a shape key `Torso.Breathe` generated by `soft_inflate` of the ribcage band h 1189–1455 by +6 mm at the front and +3 at the sides with the sternum rising 4 mm and the abdomen −2 (diaphragmatic), driven by a sine of 0.25 Hz amplitude 0.6 in idle. Not used in the hero still.

---

## 7. Rigging and attachment

### 7.1 Bones (MPFB `default`, roles via `BONE_MAP`; positions REST, verified after step 4 and written to `bones.json`)

| Role | Expected bone | Head (X, Y, Z) | Tail | Carries |
|---|---|---|---|---|
| PELVIS | `spine05` (or `pelvis` root) | (0, +10, 900) | (0, +20, 1031) | spec 03 |
| LUMBAR_LOW | `spine04` | (0, +20, 1031) | (0, +40, 1130) | the long waist's lower half, flank skin |
| LUMBAR_HIGH | `spine03` | (0, +40, 1130) | (0, +60, 1230) | upper flank, 10th rib; the 2° lateral lean (D5) |
| THORACIC | `spine02` | (0, +60, 1230) | (0, +75, 1400) | ribcage (rigid), lats, lower trapezius; the carrier's rear bag parents here |
| UPPER_THORACIC | `spine01` | (0, +75, 1400) | (0, +72, 1592) C7 | upper ribcage, scapulae (with the clavicles), the carrier front/straps (gear note: "spine_02/03") |
| NECK_LOW / MID / HIGH | `neck01/02/03` | (0, +10, 1592) → (0, −5, 1617) → (0, −8, 1642) | (0, −8, 1667) skull base | the neck in three segments (yaw split §7.3), the gaiter |
| HEAD | `head` | (0, −8, 1667) | — | face spec |
| CLAVICLE.L/R | `clavicle.L/R` | (±18, −98, 1495) | (±245, −45, 1512) | clavicle skin, supraclavicular fossa, the strap seat, 50 % of the pauldron |
| SCAPULA.L/R | `shoulder01.L/R` | (±245, −45, 1512) | (±240, −20, 1452) | acromion, deltoid origin, scapula (via a `Copy Rotation` 0.5 from the upper arm's swing so the blade slides) |
| UPPERARM.L/R | `upperarm01.L/R` | (±240, −20, 1452) GH | arm spec | deltoid belly (60 %), pauldron (50 %) |
| BREAST.L/R | `breast.L/R` | (±115, −128, 1360) | — | pectoral jiggle 0; used as the nipple anchor |

Bone rolls: the spine chain's X axis lateral (+X) so +X rotation = flexion (nod forward); the clavicles' Y along the bone.

### 7.2 Weights (`weights.py`, numpy on MPFB's imported weights, normalised; ≤ 4 influences per vertex for glTF)
Neck: the three neck bones share the neck skin as three smoothstep bands of ≈ 38 mm each (1592–1630, 1620–1660, 1650–1690) so a 25° head turn spreads into ≈ 8° per segment with no candy-wrapper; the SCMs follow `neck02/03` 60 % and `head` 40 % at their upper third; the larynx 100 % `neck02`; the trapezius slope: `spine01` 60 %, `clavicle` 30 %, `neck01` 10 % (so a shrug lifts it with the clavicle); clavicle skin 70 % `clavicle`, 30 % `spine01`; deltoid: `upperarm01` 60 % / `shoulder01` 30 % / `clavicle` 10 % at the cap, grading to 90 % `upperarm01` at the insertion (the arm spec's hand-over); scapula region: `shoulder01` 50 %, `spine01` 50 % (with the Copy Rotation above the blade protracts with the arm); pectoral: `spine01` 80 %, `clavicle` 10 %, `upperarm01` 10 % at the axillary fold only; ribcage: `spine01/spine02` smoothstep over 1300–1420; flank: `spine02 → spine03 → spine04` ramps over 1031–1230 (the long lumbar region gets two bones so a side bend is a curve); the lower band 1020–1045 blends into spec 03's pelvis weights.

### 7.3 Pose (hero): FK from the analysts' table, then a readback
Applied after spec 03's IK closure has set the pelvis at (−40, 0, 829) with yaw −10°, pitch +2°, roll 0. Trunk rotations (bone local, relative to the parent): `spine04` yaw +2° (toward his left: the chest unwinds from the pelvis), pitch −1° (extension), roll **−2°** (D5: lateral flexion to his right); `spine03` yaw +2°, pitch −1°; `spine02` yaw +1°, pitch −1°; `spine01` yaw 0, pitch 0 — net chest yaw −5° world, extension 3°, the shoulder midpoint at X −58 ± 8 posed (readback metric); `clavicle.R` protraction +8° (the acromial end forward 22 mm), elevation +2°; `clavicle.L` elevation −3°; `shoulder01.L/R` follow their Copy Rotation; `neck01` yaw +3°, `neck02` +4°, `neck03` +5°, `head` +13° → head yaw +25° vs the chest, **+20° world** (consolidated); `neck02/03` pitch −1° each, `head` pitch −3° (chin up); roll 0. Readback (`measure_torso(posed=True)`): acromia at posed h 1490 ± 4, both within 3 mm of each other in Z; GH centres R (−298, −21, 1436), L (+182, −41, 1421) (X includes the pelvis's −40 and the lean) — these are what the arm spec aims its humeri from; the right scapula's inferior angle 20 ± 4 mm lateral of the left; the chin at posed 1623 ± 4 and x ≈ 815–817 in the hero frame (the face spec checks the face itself).

### 7.4 Attachment frames provided
`Torso.Anchor.*` and `Torso.Ring.*` (§4.9), `Torso.Curve.Strap.L/R`, `Body.Collider` trunk region, the `Torso.Compress.*` keys, `Torso.Masks2.B` (stubble boundary), the GH centres (arms), the hyoid ring (face), the crest ring (legs).

### 7.5 Corrective shape keys (generated, not sculpted: `corrective.py::make_corrective(mesh, rig, pose_dict, ops) → key + driver`, spec 03 §7.5's procedure: pose, evaluate, run the `soft_*` ops in posed space, inverse-skin to rest, store, drive)

| Key | Driver | Ops (posed space) | Purpose |
|---|---|---|---|
| `Torso.Corr.NeckTurn.L` | yaw of `head` relative to `spine01` (sum of the neck chain + head), 0 → 1 over 0°–30° to his left | right SCM `soft_line` along its posed line r 13, **+3** (the ridge the reference shows at (778,146)); right clavicular head +1; left SCM −1; the larynx `soft_move` (0, −77, 1570 posed) r 18 by (+4, 0, 0) (the larynx deviates toward the turn); creases: left side of the rings deepened −0.3 and pulled 2 mm closer together (`soft_move` the skin between creases 1 and 2 on the left, r 10, (0, 0, −1)); right side creases flattened +0.3; the left trapezius anterior edge +1.5; the skin over the right posterior triangle `soft_move` 2 mm forward (stretch) | the turned neck: taut on the right, folded on the left |
| `Torso.Corr.NeckTurn.R` | mirror, 0 → 1 over 0°–30° right | mirror | animation |
| `Torso.Corr.ArmAcross.R` | `upperarm01.R` internal rotation (twist) 0 → 1 over 0°–45° **and** abduction 0–20°, product of the two `SCRIPTED` variables | anterior deltoid `soft_inflate` (−275, −95, 1440 → posed) r 30, +4; lateral deltoid −2 (it flattens); the pec's clavicular head `soft_move` 3 mm laterally (stretch), its lower border `soft_inflate` the axillary fold r 14, +3 (the fold thickens as the arm comes across); the axilla floor `soft_move` (−195, −20, 1380) r 18, (0, 0, −4) (no hole); scapula: `soft_move` the whole blade region (−80…−180, +100, 1365–1515) by (−18, −8, 0) with a 40 mm feather, inferior angle `soft_inflate` +5 (winging); the posterior axillary fold `soft_move` (0, +3, 0) | the right arm on the pistol grip |
| `Torso.Corr.ArmAcross.L` | mirror | mirror | animation |
| `Torso.Corr.ArmHang.L` | `upperarm01.L` swing forward 0 → 1 over 0°–30° | anterior deltoid +1.5, the pec's clavicular head +1 | the left arm's +12° flexion (small; keeps the two shoulders from being mirror images) |
| `Torso.Corr.ArmRaise.L/R` | abduction 0 → 1 over 30°–90° | deltoid cap `soft_inflate` +5 at 90°; the acromion shelf `soft_move` (0, 0, +2); the axilla `soft_move` (0, 0, −8) and the lat's lateral wall +3; the scapula upward rotation: inferior angle `soft_move` (±25, 0, +15) | animation (not the hero) |
| `Torso.Corr.ClavProtract.R` | `clavicle.R` yaw 0 → 1 over 0°–15° | supraclavicular fossa `soft_move` (0, +4, 0) deepens; the sternoclavicular knob +1 | the right shoulder forward |
| `Torso.Corr.Shrug.L/R` | `clavicle` elevation 0 → 1 over 0°–25° | trap slope `soft_inflate` +6 at mid-slope; the neck base skin fold at the trap–neck junction −2 | animation |
| `Torso.Corr.SideBend.R/L` | `spine04 + spine03` roll 0 → 1 over 0°–25° | compressed flank: 2 skin folds (`soft_line` rings r 6, −3 at h 1100 and 1140 posed), obliques +3; stretched flank: −1 and the ribs' relief +1 | animation; at the hero's 2° it contributes 0.08 |
| `Torso.Corr.TrunkTwist.L/R` | yaw of `spine01` relative to `spine05` 0 → 1 over 0°–30° | the obliques' diagonal fibres: `soft_line` ×3 r 10, +1.5 on the shortened side; the opposite flank −1 | the hero's 5° gives 0.17 |
| `Torso.Corr.Flex` | `spine03 + spine02` pitch 0 → 1 over 20°–60° | abdominal fold rings at h 1085 and 1160 posed r 8, −4; the rectus columns +2 | animation (sitting / kneeling) |

Game export: drivers do not survive glTF; `build_all.py` bakes the hero values into `Torso.Corr.Hero` and keeps the driven keys as morph targets (`export_morph=True`), as spec 03.

---

## 8. Evaluation protocol

### 8.1 Renders
`scripts/eval/render_part04.py --views V1…V7 [--hero-lights] [--hair]` writes `renders/04_torso/<view>_<look>.png` at 2048² (V6 at the hero frame size 1672 × 941, cropped and ×3 up-scaled with PIL beside the matching reference zoom into `renders/04_torso/V6_compare.png`). Workbench matcap + cavity versions (≈ 5 s each, `CLAUDE.md`) of V1–V5 and V7 are rendered first for form checks; Cycles 48 spp, OIDN, `use_persistent_data` for the colour passes (≈ 30–40 s each; V4 with SSS and vellus ≈ 4–6 min — budget accordingly, research C). The script ends by opening every PNG with the Read tool (the rule in `CLAUDE.md` §3) and writing `renders/04_torso/report.md` with the metric tables below.

### 8.2 Metrics (`scripts/lib/measure.py::measure_torso(obj, posed=False) → JSON`, written to `renders/04_torso/measure_<rest|posed>.json`)
1. **Girth/breadth/depth slices** at rest h 1565, 1512, 1455, 1395, 1360, 1300, 1250, 1189, 1130, 1085, 1060, 1031, 912 (spec 01's `slice_measure`, convex-hull perimeter of the body section, lats and deltoids included where the slice meets them) against §3.3: girths ± 15, breadths/depths ± 8.
2. **Landmark heights** (marker vertices and joint cubes): acromia, suprasternale, GH centres, nipples, xiphoid, 10th rib, navel, crest, C7, hyoid against §3.1 ± 5; neck ± 4; left–right height difference of paired landmarks ≤ 3 at rest, and the §3.7 asymmetries present (right scapula 4 ± 2 lower, right nipple 3 ± 1 lower).
3. **Ratios**: bideltoid/waist breadth 2.0 ± 0.05; chest girth/waist girth 1.25 ± 0.03; shoulder girth/waist girth ≥ 1.55; neck breadth/bigonial 0.85–0.90 (the face spec supplies the bigonial).
4. **Trapezius slope angle** 18 ± 3° (line fit from the neck junction to the acromion on the back-view silhouette); **deltoid widest point** 55–65 mm below the acromion.
5. **Relief depths** (ray-cast difference between the sculpted and the pre-sculpt evaluated surfaces at the §3.4–3.6 points): spinal furrow −15…−20 thoracic, −6…−8 lumbar; suprasternal notch ≥ 10; larynx +8…+10; SCM +5…+7 (rest); clavicle rod +2…+3; navel −6…−8; creases −0.3…−0.8; each within ± 25 % of the table.
6. **Flank quality**: after step 3 the maximum edge length in `Torso.Flank` ≤ 34 mm and the ratio of adjacent loop spacings ≤ 1.5; UV texel density in the flank ≥ 0.8 px/mm.
7. **Posed readback** (§7.3): shoulder midpoint X −58 ± 8; acromia posed 1490 ± 4; head yaw 20 ± 3° world; right scapula lateral offset 20 ± 4; chin 1623 ± 4.
8. **Hero neck metrics** (V6, hero lights, the real or stand-in gaiter): in the ROI (750–860) × (128–162) the fraction of pixels with lum > 90 = **0.27 ± 0.05**, lum > 45 = **0.58 ± 0.06**; the lit-run (lum > 90) right edge at y 139 = x 787 ± 4 and at y 154 = x 805 ± 4 (the chin's shadow edge); the x = 780 column's luminance profile within ± 15 of §2.2's (peak 136 at y 134–140, groove 121 at y 141–147); the §5.5 hex targets.
9. **Garment-edge rows** (V6 with stand-ins): gaiter top centre y 150–155, straps from y 160 ± 3, carrier top y 195–200, hem y 395–400, waistband top y 475 ± 3, pad tops y 183/192 ± 4.
10. **Hair**: strand counts per system within the §6 ranges; zero roots inside `Torso.NoHair`; in dressed renders zero hair pixels (hair hidden).
11. **Export check**: ≤ 4 bone influences per vertex; no vertex of `Torso.Region` farther than 2 mm from the `Body.Collider` surface.

### 8.3 Critic questions (score 0–2 each, 30 max; ≥ 25 passes, no zero)
1. V1: Does the man read as a lean 40-year-old mesomorph of about 92 kg, broad-shouldered and long-waisted, and not as a bodybuilder, a mannequin or a generic MakeHuman?
2. V1: Clavicles as rods with a fossa behind, a real sternal notch, a sternal gap between the pecs, a pec line with a soft overhang?
3. V1: Nipples oval, slightly down-and-out, with a textured areola; placed 230 apart at the right height?
4. V1/V5: Abdomen as 2 + 2 relief with a linea alba, intersections slightly chevroned, a navel that is a pit with a hood — and no six-pack?
5. V5: The long flank reads as anatomy (obliques, erector columns, the costal arch above, the crest below), not as a stretched tube or a visible loop boundary?
6. V2: Scapular spines, inferior angles, a deep furrow between the blades and a shallow one at the waist, lats forming the V from the axilla to the crest?
7. V3: Trapezius slope a convex muscle at about 18°, acromion a shelf, deltoid a cap widest below the acromion, with the two shoulders not mirror images?
8. V4: Two SCM cords meeting at the notch, a larynx with a notch, cricoid dip, two or three creases, an EJV in relief, the carotid groove — all as relief catching the key, not as painted lines?
9. V4: Skin — pores at the right scale, the nape coarser and redder than the front, no waxy glow, the shadow side dark?
10. V1 vs V4: The collar sun line visible as a soft gradient, the trunk paler than the neck, nowhere a hard line?
11. V7: Posed — the right SCM standing out, the left neck folded, the right scapula slid out, the right anterior deltoid full, the axilla a fold; no candy-wrapper at the neck, no pec folding through the deltoid?
12. V6: Every garment edge on its reference row; the neck strip's shape, lit fraction and shadow edge matching the zoom?
13. V6: The under-jaw shadow as black as the picture (#110a04) with the lit SCM at #ae806b — i.e. does the neck sit the right distance under the chin for the key to miss it?
14. Hair (if rendered): chest hair lying down-and-in in clumps, dense axillae, sparse shoulders, bare back — believable for the stubbled face?
15. Overall: anything symmetric that should not be, anything copy-pasted, any mesh artefact after subdivision?

### 8.4 Failure modes and their fixes
* Measure targets saturate before the chest/waist ratio is reached → the residual goes into `Torso.Sculpt` (step 6 trim pass), never into `torso-scale-vert`.
* The height macro and the neck-length targets fight (the solver oscillates) → solve them as a 2 × 2 secant with damping 0.5; if still oscillating, fix `neck-scale-vert-incr` at 0.15 and let `measure-neck-height` carry the rest.
* Flank re-loop produces triangles or n-gons at the back midline seam → run `subdivide_edgering` per ring-pair and `bmesh.ops.join_triangles` after; if MakeHuman's flank rings are not closed loops, fall back to `bmesh.ops.subdivide_edges` with `use_grid_fill`.
* Rig fit after the re-loop drops the imported weights for the new vertices → `vertex_group_smooth` 2 iterations in the flank, then re-normalise.
* The gaiter stand-in hides more or less of the neck than the picture → the body is probably right and the gaiter's top ring is wrong: adjust `Torso.Ring.Gaiter.Top` first (it is a geometry fact of the garment), only then the neck length.
* Lit fraction too high (neck too bright) → the under-chin shadow is the chin's projection: check the head pitch (−3°) and the chin's forward projection (face spec) before touching the neck.
* Skin glow (SSS scale too large over the clavicle/sternum) → the thickness proxy caps the scale at 0.0028 over bone.
* Candy-wrapper neck → the three-band split in §7.2 is missing or the Corrective Smooth group excludes the neck.
* Pec folds through the deltoid at 45° internal rotation → `ArmAcross.R` amplitude +1 on the fold, or the pec's `upperarm01` 10 % weight is missing.
* Hair through the gaiter/shirt → hair hidden in dressed renders; roots never placed within 3 mm of a garment band.
* Workbench shows faceting on the neck creases → the creases are at the base-mesh limit: keep them in the relief map / Displace only (remove from `Torso.Sculpt`).

---

## 9. Build order, effort and risks

### 9.1 Dependencies
Spec 03 (crest 1031, hip 851, the pelvis weights; its sculpt must run **after** this part's step 3 re-loop), the face spec (the head's rest heading, the chin's projection, the bigonial 157, the beard's neckline fade at the hyoid, the hair's nape line), the arm spec (takes the GH centres, the deltoid hand-over at h 1400), spec 01's `sculpt.py`/`measure.py` helpers (`soft_inflate`, `soft_move`, `flatten_to_plane`, `slice_measure`; `soft_line` is added here), spec 03's `corrective.py` and `weights.py`, the materials library's `Skin.Base`, research A's fleece/knit sets for the stand-ins only.

### 9.2 Build order inside the script (idempotent; every step re-runs from the step-1 cache `assets/body/base.blend` when upstream is unchanged)
1. Base + solver (steps 1–2): ≈ 15 s (create 0.9 s, 6 secant passes × 20 targets × 0.5 s, measurements 2 s).
2. Bake + remap + re-loop (step 3): ≈ 2 s.
3. Rig fit + bone dump (step 4): ≈ 1 s. — shared pipeline ends; `assets/body/body_rigged.blend` cached.
4. Vertex groups (step 5): ≈ 1 s.
5. `Torso.Sculpt` (step 6, ≈ 70 ops on ≈ 4 k verts, numpy): ≈ 3 s; measure and trim: 2 s.
6. Relief and masks bakes (step 7, §5.2): ≈ 60 s at 4096².
7. Compression keys, anchors, rings (steps 8–9): ≈ 2 s.
8. Weights (§7.2), pose (§7.3), correctives (§7.5: 14 keys × pose-evaluate-inverse-skin ≈ 1 s each): ≈ 20 s.
9. Hair (`--hair`): ≈ 10 s to build; render cost separate.
10. Stand-ins and renders (`--eval`): Workbench set ≈ 40 s; Cycles set ≈ 5 min without V4's vellus, +5 min with it.
Total without renders ≈ 2 min; with the full render set ≈ 12 min on 4 cores.

### 9.3 Estimated script size and sessions
`04_torso_neck.py` ≈ 1,300 lines; `lib/proportions.py` additions (trunk table, solver, bake/remap/re-loop) ≈ 250; `lib/sculpt.py::soft_line` ≈ 40; `lib/measure.py::measure_torso` ≈ 280; `lib/rig_names.py` ≈ 60; `eval/render_part04.py` ≈ 300. Three working sessions: (1) pipeline + solver + remap + rig until §8.2 items 1–2 and 6 pass on Workbench renders; (2) sculpt, relief, masks, materials until V1–V5 pass with the critic; (3) pose, correctives, stand-ins, V6/V7 metrics, hair, critic round and fixes.

### 9.4 Risks and fallbacks

| Risk | Likelihood | Fallback |
|---|---|---|
| MPFB `default` rig bone names differ from the MakeHuman names assumed in §7.1 | medium | `BONE_MAP` from the run-time dump; nothing else references names |
| Measure targets' gains too small for bideltoid 625 (MakeHuman's shoulder targets are modest) | medium | `Torso.Sculpt` deltoid inflate carries up to +12 mm per side; beyond that a `Lattice` (4 × 2 × 3) scaled 1.06 in X over h 1380–1540, applied | 
| The flank re-loop breaks the MakeHuman UV layout or the helper joints | low | UVs are interpolated by the op; helpers are untouched; if seams tear, re-run without re-loop and put the navel into the relief map with doubled amplitude |
| Spec 03's sculpt runs before the re-loop and its vertex indices shift | medium | `build_all.py` order fixed: shared pipeline (03's targets + 04's targets → bake → remap → re-loop → rig) then every spec's sculpt; spec 03's step 5 must read the body after this |
| Neck too coarse (12–18 mm loops) for the SCM/larynx silhouette at V4 | medium | the Displace in `Neck.Region` from the relief map (§4.7); if still soft, a local `Subdivision` level 4 via a second body object `Neck.Hero` (duplicate of the neck faces, Shrinkwrapped, hero renders only) |
| D1 (rest 1877) rejected by the client | low | `STATURE_REST_MM = 1855`; all trunk REST heights shift −22 automatically (they are computed from the POSED table) |
| SSS render time for V4 with vellus (≈ 6 min) | certain | render V4 once per session; iterate on Workbench and the no-vellus Cycles pass |
| Gaiter stand-in misleads the V6 check | medium | the stand-in ring heights come straight from §2.1 pixel rows; when the real gaiter exists, V6 switches to it |
| Corrective inverse-skinning drifts at the clavicle (three bones blend) | medium | `make_corrective` already uses the blended inverse; cap the clavicle's weight share at 0.7 in the correctives' band |

---

## 10. Interfaces and open questions for the client

### 10.1 What neighbouring parts must provide or respect

| Part | This part provides | This part needs / the neighbour must respect |
|---|---|---|
| Legs and pelvis (03) | the shared remap `Body.Proportion` with the extra knot (10th rib → 1189) replacing `Leg.Proportion`'s top segment; the flank re-loop; `Torso.Ring.Waistband` (posed 890, breadth 315, depth 220); body breadth 345 at the trochanters respected; the `Torso.Corr.SideBend/TrunkTwist` keys | crest 1031 rest / 1009 posed, hip 851/829, pelvis centre (−40, 0, 829) yaw −10°; spec 03's sculpt runs after step 3; spec 03's text "stature 1855 rest, chin 1620, acromion 1521" to be reconciled with D1/D3 (its numbers become rest 1877 / 1645 / 1512) |
| Head and face | the hyoid join ring (rest 1622, blend 1615–1630), the neck axis (8° forward, C7 (0, +72, 1592)), neck breadth 135 = 0.86 × bigonial 157, `Torso.Masks2.B` stubble feather (1 at the hyoid → 0 at 1640), the nape colour #b07c66 up to the hairline, the `NeckTurn` corrective (the face spec must not add its own SCM) | the chin's projection and the under-jaw plane (they make the shadow that hides the neck), head rest heading −Y, the bigonial width, the beard's neckline ending at rest 1620 ± 5, the scalp's nape taper down to ≈ 1650 |
| Arms (05) | GH centres rest (±240, −20, 1452), posed R (−298, −21, 1436) / L (+182, −41, 1421); the deltoid down to the hand-over band 1380–1420 (the arm spec owns the humerus below, including the deltoid insertion groove's lower end); `Torso.Corr.ArmAcross/ArmHang/ArmRaise`; the axilla floor | upper-arm vectors re-derived from the GH centres (D3); the arm spec must not sculpt above h 1420; its sleeve spec gets the deltoid cap radius 110 × 130 |
| Plate carrier and straps | `Torso.Ring.CarrierTop` (posed 1470 at Y −118), `Torso.Ring.Hem` (1053), `Torso.Ring.Cummerbund.Top/Bottom` (1180/1050), `Torso.Curve.Strap.L/R` (73 wide at X ±104 front, ±115 back, inner surface body + 6 with `Torso.Compress.Straps` at 1.0), `Torso.Anchor.Antenna` (+212, +118, 1505 posed), the posed chest front at Y −118 … −130, the trunk's silhouette rows of §2.2 | the front bag 315 × 420 × 30 at body + 15 (over the shirt); straps parent `clavicle`/`spine01`, the bags `spine01/02`; the carrier top must sit 15–20 mm below the suprasternale (y 195–200) and the hem at y 395–400 |
| Neck gaiter (clothing) | `Torso.Ring.NeckBase` (seat, girth 460 + collar), `Torso.Ring.Gaiter.Top` (posed front 1574, right 1583, back-left 1625), `Body.Collider` to the hyoid, the neck's posed geometry with the `NeckTurn` key | the top roll must not rise above y 150 at the front centre nor below y 130 at the back-left; three to four rolls; it sits under both straps (straps cross it at y 190–200) |
| Combat shirt (clothing) | `Torso.Ring.Collar` (mandarin collar, front 1537 / back 1590 rest), the yoke saddle (trap–deltoid) smooth and convex, `Torso.Compress.*` | the shirt body at body + 1.5 (knit), the yoke ribs 4 mm pitch vertical over the shoulders, the collar entirely under the gaiter |
| Pauldrons (armour) | `Torso.Anchor.Pauldron.L/R` on the deltoid cap (±290, −20, 1460) with the cap's outward normal, 50 % clavicle / 50 % upper arm parenting; the cap radius 110 × 130 | tier 1 cap tops at y 183 (L) / 192 (R), inner edges 60–70 mm outboard of the GH centre |
| Rig / `build_all.py` | `BONE_MAP` roles, the neck three-band weight rule, the clavicle/scapula Copy Rotation, 14 driven correctives + `Torso.Corr.Hero`, `Torso.Breathe`, the FK trunk pose values of §7.3 | `Corrective Smooth` after `Armature`, before `Subdivision`; Preserve Volume on; the shared pipeline order of §9.4 |
| Materials library | `Skin.Body` trunk/neck regional values (§3.8), `Torso.Masks(.2).png`, `Torso.Relief.exr`, the collar sun-line node | `Skin.Base` group and the face albedo #b98670 |
| Eval | `measure_torso()`, the V6 stand-ins and the hero-neck metrics (§8.2 items 8–9), the dressed silhouette row table (§2.2) for the garment specs | the hero camera and lights (lighting note §6), spec 01's look-dev scene |

### 10.2 Questions for the client
1. **D1 — stature.** Confirm that the 1855 mm is the *posed* height (rest body 1877), so the chin, shoulders, carrier and belt all land on their pixel rows; or keep rest 1855 and accept the head 10 px low in the hero frame.
2. **D3 — shoulder joints.** Confirm the anatomical GH centres (±240, 1452 rest) over the analysts' wider, higher estimate; the arm spec follows.
3. **Moles and marks on the hidden trunk:** the realistic sparse set of §3.8 (default on, never on the neck) or none, as the face? Any scar or tattoo (none in the picture; none assumed)?
4. **Chest hair density:** moderate (§6, matching a dark-stubbled 40-year-old) or sparse/none? It is invisible in the hero frame either way.
5. **Bare-trunk deliverables:** turntables of the undressed body wanted (then hair and V1–V5 are deliverables), or internal evidence only?
6. **Trunk lean (D5):** a 2° lean to his right over the loaded foot, or strictly upright as the analysts wrote?
7. **Neck length (D4):** 133 mm menton-to-notch (as drawn, long) or the ANSUR 105 (the gaiter would then show 25 mm less neck above its roll — the picture argues for the long one)?
8. **Breathing key** in the game export, yes or no?

### 10.3 Items tagged [VERIFY]
* MPFB `default` rig trunk bone names and which end is `spine01`; `shoulder01` existence; `breast.L/R` (dumped at step 4).
* MakeHuman helper vertex-group names for the joint cubes (`joint-neck`, `joint-r-shoulder`, …) and the marker vertices found by geometry (rendered as spheres in the first V1/V2).
* Per-unit gains of every `measure-*`, `torso-*`, `neck-*` target (solved at run time).
* Whether MakeHuman's flank edge rings are closed loops for `subdivide_edgering`.
* The name of the shared skin node group (`Skin.Base`) and the final body object name (`Body.Mesh` vs `Human`).
* Texel density of MakeHuman's torso UVs at 4096² (≈ 2.4 px/mm assumed).
* All E-tagged anatomical positions (clavicle curve, scapula size, SCM path, larynx heights, crease heights, nipple spacing 230, interscye, shoulder girth 1400) — anatomy-text values, not measured on this soldier; they are checked only against the critic's eye and the §2 rows.
* The hero-neck metric tolerances (lit fraction ± 0.05) were set from one image; widen if the calibrated lights of the lighting note reproduce the face targets but not these.
