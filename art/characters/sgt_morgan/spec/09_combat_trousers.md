# Part 09 — Combat trousers (Crye G3/G4-class, dark 4-tone blotch camouflage)

Convention reminder (CLAUDE.md rule 1 and 2): every left/right below is the **soldier's own**; "viewer's left/right" is written out when the picture is meant. Spec units are **mm**; Blender units are metres. World frame: origin on the floor midway between the feet, +Z up, character faces −Y, camera on −Y, **+X = his LEFT = viewer's right**. Reference pixel coordinates are full-image coordinates of `ref/reference_full.png` (1672 × 941); scale at the figure's depth **1 px = 2.12 mm** (4.72 px/cm, `analysis_consolidated.md` "Agreed scale"); height above the floor h = (895 − y) × 2.12 mm; lateral X = (x − 830) × 2.12 mm. The left leg stands ≈150 mm nearer the camera, so its pixels are ≈4 % larger (4.9 px/cm); figures for the left leg are corrected where it matters.

Sources: `notes/analysis_consolidated.md` §1, §4, §6 (authoritative), `notes/analysis_gear_inventory.md` §9, §12, §13, §18, `notes/analysis_pose_proportions.md` §2–§6, `notes/analysis_lighting_camera_scene.md` §6 (evaluation camera/lights), `notes/mpfb_targets_and_assets.txt` (MPFB inventory), `notes/research_blender_capabilities.md` (header only at the time of writing — every performance figure below is tagged [VERIFY: research_blender_capabilities]). Own zoom crops made for this spec: `ref/zoom_trousers_*.png` (gridded ×3–×12 Lanczos zooms with full-image coordinates on the grid lines), `ref/zoom_camo_generated_tile_1m_v2.png` and `ref/zoom_camo_generated_at_refscale_v2.png` (output of the camo generator prototype `ref/zoom_camo_generator_prototype_v2.py`), `ref/zoom_trousers_blotch_stats.py` (the measurement script used in §2.6 and §8).

---

## 1. Purpose and acceptance

### 1.1 What this part is
The complete lower-body garment from the waistband (top edge 890 mm above the floor, just above the black rigger belt) to the loose cuffs stacked over the boot collars (cuff edge ≈190 mm above the floor): shell fabric, stretch panels, crotch gusset, waistband with belt loops and fly, front/back/cargo/calf pockets, the black knee-pad pockets ("knee sleeves") that hold the hard caps of spec 12, the reinforced shin panels, all seams, topstitching, bar tacks, hardware, the camouflage print, fabric micro-structure, wrinkles and weathering. **Not** in this part: the hard kneepad caps and their rear straps (spec 12), the belt (belt/load-bearing spec), the drop-leg platforms and their thigh straps (right and left rig specs), the boots and the combat shirt. This part must, however, provide the surfaces those parts sit on and react to them (compression bands, §4.9 and §7).

### 1.2 What "perfect" looks like
At hero distance (reference camera, 46 mm at 4.5 m) the trousers must read as heavy, matte, dusty NYCO ripstop in a near-black low-contrast blotch camouflage, hanging from a low-slung waist with a long torso above, a short thigh, black smoother knee pockets bulging over the caps, and cuffs piled in 2–3 fat rolls on the boot collars with every lace crossing still visible. In a 300 mm-wide closeup every seam is a double row of black stitches 6.4 mm apart at 3.6 mm pitch on a 1.2 mm ridge, the 6 mm ripstop grid is visible as a faint raised lattice catching the key light on fold crests, the camouflage blotches have 3–5 mm feathered edges and never repeat visibly, dust sits only on up-facing cloth, grime only at the cuffs, and the crotch gusset seams are whitened by abrasion.

### 1.3 Evaluation render views (all rendered by `scripts/parts/09_combat_trousers.py --eval`, written to `renders/09_combat_trousers/`)

| View | Camera position (m) | Target (m) | Lens | Compared with | What it proves |
|---|---|---|---|---|---|
| V1 `legs_ref` | reference camera (0.00, −4.50, 0.60), rot (93.9°, 0, 0) | — | 46 mm | `ref/crop_legs_knees.png` = ×3 of box (630,550)–(990,830); render full frame, crop the same box, upscale ×3 Lanczos | silhouette, knee pockets, articulation zone, shins, hem rolls at the true scale |
| V2 `hips_ref` | reference camera | — | 46 mm | `ref/crop_belt_hips.png` = ×3 of (630,410)–(990,630) | waistband, fly, crotch height, inner-thigh gap, gusset folds, strap compression |
| V3 `boots_ref` | reference camera | — | 46 mm | `ref/crop_boots_feet.png` = ×3 of (610,750)–(1010,935) | cuff edge height, roll count, lace visibility, cuff grime |
| V4 `knee_R_close` | (−0.62, −0.95, 0.72) | (−0.21, −0.03, 0.56) | 85 mm | `ref/zoom_trousers_rknee_sleeve_x5.png`, `zoom_trousers_rthigh_darts_x6.png` | knee pocket construction, pocket top seam/darts, strap compression roll, shin seam A |
| V5 `hem_R_close` | (−0.40, −0.85, 0.33) | (−0.20, −0.03, 0.23) | 85 mm | `ref/zoom_trousers_rhem_x8.png` | three rolls, hem topstitch, collar overlap, grime |
| V6 `crotch_close` | (0.00, −1.20, 0.52) | (−0.04, −0.02, 0.74) | 70 mm | `ref/zoom_trousers_gusset_x10_bright.png`, `crop_belt_hips.png` | gusset diamond, radial stress folds, stress whitening, fly bottom bar tack |
| V7 `calf_L_close` | (0.80, −0.75, 0.48) | (0.22, −0.12, 0.38) | 85 mm | `ref/zoom_trousers_lcalf_pocket_x12.png`, `zoom_trousers_lshin_pocket_x6.png` | calf pocket, piping, grommets, shin seams on the frontal leg, cool-light response |
| V8 `camo_macro` | (0.45, −0.55, 0.62) | (0.14, −0.12, 0.60) | 100 mm | `ref/zoom_trousers_camo_lthigh_plain_x8.png` and the generated tile | blotch size, tone set, edge softness, ripstop grid, weave roughness |

Lighting for all views: the consolidated KEY/COOL/WORLD rig of `analysis_lighting_camera_scene.md` §6.2, AgX "Medium High Contrast", exposure 0; V4–V8 additionally render a "flat" variant (world grey 0.18, no key) for geometry inspection.

### 1.4 Pass criteria (scored by the critic, each 0–2; part passes at ≥ 22/28 with no zero)
1. Silhouette IoU of the trouser mask in V1 against the reference mask ≥ 0.90 (mask method §8.2).
2. Cuff edge height 180–205 mm on both legs in V3; exactly 2 or 3 roll crests per leg between 205 and 300 mm (crest counting §8.3); the laces of both boots fully visible.
3. Crotch apex height 755–775 mm, inner-thigh gap at h = 710 mm between 60 and 90 mm wide (V2).
4. Knee pockets read black-grey (#1c1c1e–#2f3033 after grading) and smoother than the camo; caps of spec 12 sit inside with no z-fighting (V1, V4).
5. Camo statistics on the lit left thigh of V1 (script §8.4): equivalent blotch diameter median 15–30 mm, max 40–65 mm, local contrast 95–140 %, four tone clusters each within ΔE76 < 10 of the targets in §5.2.
6. Colour patches (§8.5): 10 named pixels within ±10/255 per channel of the reference.
7. Closeup construction (V4–V7): double-needle rows at 6.4 ± 0.5 mm, pitch 3.6 ± 0.3 mm, bar tacks present at all pocket corners and belt loops, ripstop grid pitch 6.0 ± 0.3 mm, no floating stitches, no texture repeat visible within one leg.
8. Weathering placement: dust only where n·Z > 0.25, grime band below 320 mm, whitening within 15 mm of gusset seams; no uniform "dirt wash".
9. No intersection with the body, boots, belt, straps or kneepad caps in any view (flat variants).
10. Critic's free judgement: "would a Crye wearer recognise the garment?" (0–2).
Criteria 1–3 and 9 may not score 0.

---

## 2. Reference observations

### 2.1 Overall extents (measured)

| Feature | Pixels (x, y) | World (mm) | Note |
|---|---|---|---|
| Waistband top edge | y ≈ 475, x 745–890 | h 890 | lighter band #443d37 (750,482) / #3c3b3c (860,482); below the exposed shirt band (398→475) |
| Belt (other spec) | y 490–512 | h 859–812 | covers the waistband's lower 2/3 |
| Fly / centre-front line | x ≈ 810, y 475–535 | X −42 | darker vertical #1e1c1a (810,500); fabric either side #010000 / #211e18 — the pelvis is yawed −10° so CF projects 7 px left of the hip centre (817) |
| Hip joints (body) | y 505 | h 827 | consolidated decision: build as drawn (fallback 480) |
| Crotch apex | (810, 535) ± 5 | X −42, h 763 | legs separate here; **the dark blue-grey diamond (780–840 × 540–600, #21282e) below it is the hangar BACKGROUND seen between the thighs, not the gusset** (own x10 brightened zoom `zoom_trousers_gusset_x10_bright.png`: flat cool gradient continuous with the hull; see §2.9) |
| Inner-thigh gap | y 560: x 792–828 ; y 600: x 780–835 | 76 mm ; 117 mm | widening toward the knees |
| Right thigh width at y 600 | x 696–780 | 178 mm | includes drape folds |
| Left thigh width at y 600 | x 846–930 | 178 px-scale / ≈171 corrected | — |
| Upper right thigh strap (rig spec) | y 520–536, x 710–800 | h 795–761 | compresses our fabric |
| Lower right thigh strap | y 565–588, ladder-lock (733,567) | h 700–651 | — |
| Lower left thigh strap | y 560–580, x 830–900, buckle (840,570) | h 710–668 | — |
| Knee-pocket top seam / "dart band" | R (700–780, 578–586); L (830–920, 575–585) | h 672–655 | dark 7–8 px band = 15–17 mm; see §2.4 |
| Gathered articulation zone | R y 586–603; L y 585–605 | h 655–619 | 17–20 px = 36–42 mm tall, lit tan, 4 vertical ridges at ≈6 px (13 mm) pitch |
| Knee pocket (black sleeve) | R x 690–770, y 603–712 ; L x 860–945, y 605–712 | R 170 × 231 mm ; L 180 × 227 (corr. 173 × 218) | #252527 (770,660), #2f3033 lit, #191a17 lower |
| Kneepad caps (spec 12) | R 695–760 × 615–700 ; L 862–940 × 610–700 | — | inside the pockets |
| Knee centres | R (727,650) ; L (890,657) | R X −218, h 519 ; L X +127, h 505 | — |
| Knee pocket bottom edge | y 700–712, shallow U | h 413–388 | lower on the lateral side |
| Shin width at y 740 | R x 697–772 ; L 876–966 incl. pocket | R 159 mm ; L ≈185 (≈160 without pocket) | — |
| Right shin vertical seam A (lit ridge) | x 718–722, y 712–790 | — | own zoom `zoom_trousers_rknee_lower_x10_bright.png`; the analysts' x 735–745 is the shadow ridge of a fold / seam B (§2.5) |
| Left calf pocket panel | x 925–965, y 690–760 | 85 × 148 mm (corr. 82 × 142) | cool-lit #20252d–#35393d, median #35393d, p95 #7c7e87; bright piping on its outer (his-left) edge x 945–952 |
| Two dark dots on the piping | (947,724), (948,729) | 5 mm each, 10 mm apart | grommet pair or snap caps (§2.5 decision) |
| Hem roll crests | R y 757 / 775 / 795 ; L 755 / 775 / 795 | h 293 / 254 / 212 | 3 rolls, 25–35 mm tall each, protruding 8–17 mm |
| Cuff edge | y 803–810 | h 195–180 (mean 191) | 10–25 mm below the boot collar top (y 795–800, h 212–201) |
| Cuff visible width | R x 699–763 ; L 890–952 | 136 mm ; 131 (corr. 127) | stacked, over a 140 mm boot shaft |

### 2.2 Colour samples (own 5×5 means, lit = as rendered in the reference)

| Area | px | Hex | Reading |
|---|---|---|---|
| R thigh lit, tan blotch | (705,590) | #6e5e4c | key at grazing incidence on T3 tone + dust |
| R thigh lit, olive blotch | (720,600) | #47413a | T2 |
| R thigh shadow | (760,600) | #111111 | ambient on T0/T1 |
| L thigh lit (cool) | (880,600) / (900,595) / (925,600) | #38322c / #363836 / #242a2f | cool side light turns T2 neutral-grey |
| R knee-pocket top seam | (740,582) | #302b26 | — |
| L knee-pocket top seam | (870,580) | #4a4036 | catches the key |
| Knee pocket R / L | (770,660) / (855,660) | #2f3033 / #242423 | black Cordura, slight sheen |
| Knee pocket lower R / L | (740,705) / (895,705) | #191a17 / #121311 | — |
| R shin lateral panel lit | (710,730) | #463e34 | — |
| R shin seam A / dark face | (740,740) / (765,740) | #1d1d1b / #2e3032 | — |
| L shin lit / calf pocket / piping / cool edge | (905,740) / (940,720) / (928,730) / (950,760) | #3c3730 / #20252d / #2c3039 / #3f4851 | piping and pocket read blue because of the cool light, not because they are blue |
| R hem crest / fold shadow / cuff | (715,775) / (740,785) / (720,800) | #4c3d2d / #080807 / #050604 | warm sheen on crests; cuff in shadow |
| L hem crest / fold shadow / cuff | (905,775) / (930,790) / (920,800) | #373129 / #322d27 / #2e2a24 | — |
| Box: R thigh below seam (695–780 × 585–615) | — | median #272422, p5 #0b0a0a, p95 #857061 | lum p5/50/95 = 10/37/115 |
| Box: L thigh below seam (850–925 × 585–615) | — | median #3e3c38, p5 #0a0c0c, p95 #6d696e | 12/60/105 |
| Box: R shin (700–770 × 700–790) | — | median #1e1e1c, p95 #60564d | 7/30/87 |
| Box: L shin (880–960 × 700–790) | — | median #2d2b29, p95 #5c595e | 10/44/90 |
| Box: hem stacks R / L | — | medians #23221f / #262421, p95 #7f7267 / #6e6662 | 3/34/115 ; 3/36/103 |
| Box: waistband (760–890 × 470–490) | — | median #181715, p95 #5a5758 | — |

Consolidated camo class targets (`analysis_consolidated.md` §4): near-black #0a0b08, charcoal-brown #171513 / #262524, olive-brown #322e29 / #3e3a35, tan #615348 / #534c3f / #685d53; knee sleeves #252527; cuffs #171514 / #25221b. These are lit values; §5.2 derives albedos.

### 2.3 Camouflage pattern (own measurement)
Method (`ref/zoom_trousers_blotch_stats.py`): luminance of each lit window high-passed with a 12 px Gaussian, thresholded at the 70th/30th percentiles, connected components ≥ 10 px, equivalent diameter in mm at 2.12 mm/px.

| Window | Light blotches: eq. diameter mm p25/50/75/max | Dark blotches | Local contrast (p90−p10)/mean |
|---|---|---|---|
| R thigh (695–785 × 580–615) | 12 / 16 / 30 / 53 | 8 / 16 / 26 / 51 | 134 % |
| L thigh (850–930 × 580–615) | 13 / 18 / 34 / 47 | 11 / 14 / 15 / 61 | 117 % |
| R shin (700–770 × 705–790) | 21 / 25 / 32 / 50 | 10 / 18 / 25 / 57 | 123 % |
| L shin (880–935 × 705–790) | 11 / 20 / 28 / 48 | 10 / 13 / 33 / 42 | 101 % |

Four-tone k-means on the lit thigh and shin pixels: #141311 (32 %), #2f2c29 (39 %), #4d4842 (23 %), #7b736c (6 %). Blotch bounding boxes are slightly wider than tall (w/h 1.0–1.6) on the thighs (fabric stretched around the leg). Edges are soft: no step sharper than 2 px (4 mm) anywhere. Blotches of 40–60 mm exist but are rarer than the analysts' "3–8 cm" suggests; the mid-scale 15–30 mm islands dominate the texture. **Decision:** a two-scale pattern — a few 40–80 mm zones plus many 15–35 mm islands and a sparse 5–10 mm speckle — with tone fractions 30/35/25/10 % (near-black / charcoal / olive-brown / tan). The pattern is our own CC0-safe design in the MultiCam Black / A-TACS LE family, not a copy (open question §10.3).

### 2.4 Construction cues, and what I decided where the image is ambiguous
* **Knee-pocket top seam vs "dart band".** The 15 mm dark band sits directly under the lower thigh straps (R h 700–651, band h 672–655). It could be the strap's shadow plus a compression ridge, or a real horizontal seam. Decision: model a real horizontal seam (the top of the knee pocket's articulation panel) at h 665 with three tucks per side, AND let the strap compress the cloth 10 mm above it. Both effects are then present whichever the generator meant.
* **Gusset.** The analysts called the dark diamond (780–840 × 540–600) the gusset; the brightened zoom shows a flat blue-grey gradient identical to the hull behind the figure and continuous with the floor lower down: it is negative space. The true gusset is the shadowed fabric at (790–830, 515–540). The radiating "stress folds" are real: diagonal pleats on both inner thighs at (786–800, 535–560) and (828–845, 548–575). Decision: diamond gusset 200 × 120 mm in 4-way stretch, apex at h 763, folds as in §6.3.
* **Shin seams.** The right shin (leg rotated 45° to his right) shows a lit lateral strip x 697–720 and a bright vertical ridge at x 718–722 (seam A); a softer ridge at x 735–750 (seam B). On the frontal left shin, vertical edges appear at x ≈ 890 and x ≈ 928–932. Both legs are explained by a centre-front shin panel 90 mm wide with seams at ±45 mm from centre-front (on the rotated right leg they project at ≈ −26 px and +8 px from the shin centre 734 → 708/742; measured 720/745 ± 5; on the frontal left leg at ±21 px around 912 → 891/933; measured ≈890/930). Decision: centre-front reinforced shin panel 90 mm wide, two vertical felled seams, full length from the knee-pocket bottom to the hem.
* **Calf pocket.** Visible only on the left leg (lateral, x 925–965). A slim vertical pocket lateral to the lateral shin seam, piped along its outer edge; the two dark dots at (947,724)/(948,729) are 5 mm, 10 mm apart — too close for two snaps. Decision: two #00 (5 mm) black grommets carrying a short loop of 3 mm shock cord (zip-pull keeper); alternative (if the client prefers): no grommets, hook-and-loop flap only. Mirror the pocket to the right leg (faces away from the camera there; its side gusset is the lit strip at x 697–716 on the right shin — consistent).
* **Cargo pockets.** Nothing visible; the drop-leg rigs cover the lateral thighs. Decision: model standard bellows cargo pockets (§3.3) under the rigs, low-poly, so that any view that is not the hero view is still right.
* **Hems.** No drawcord, no elastic, no blousing strap: a plain 20 mm hem whose excess length stacks on the boot. Real G3 hems have a drawcord; we follow the picture (open question §10.3).
* **Belt loops.** Dark vertical bars at x ≈ 805 and 850 (y 475–495). x 805 is only 10 mm from CF — that is the fly topstitch shadow, not a loop. x 850 is 85 mm from CF — a front loop. Decision: 7 loops at CF ± 80, side seams, CB ± 90, CB (§3.4).
* **Waistband visibility.** The lighter band at y 475–490 is the waistband's top 15 mm above the belt; the shirt is tucked (decision; open question §10.3).

### 2.5 Pose-dependent facts the drape must reproduce
Right leg: hip flex −5°, abduction +14°, external rotation 45°, knee flex 15–20°, foot in profile toe to his right (consolidated §1). The right trouser leg is therefore seen 45° off-front: its lateral half is key-lit (tan blotches read strongly at x 696–720), its medial half falls into shadow; the knee pocket is seen obliquely (170 mm wide). Left leg: hip flex +8°, abduction 10°, external rotation 22°, knee flex 8–10°, foot forward; the left trouser leg is frontal and cool-lit from his left; it is ≈150 mm nearer the camera. Pelvis yaw −10°. Weight 55/45 right-heavy: the right leg's cloth hangs straighter and the left (forward) leg's hem rolls lean forward over the instep.

---

## 3. Real-world reference

### 3.1 Garment (sourced: Crye Precision G3/G4 Combat Pant product descriptions, general knowledge; dimensional values for size 34R are estimated from standard military pattern blocks — [VERIFY: research_dimensions] for any figure marked E)

| Item | Value | Tag |
|---|---|---|
| Shell fabric | NYCO 50/50 nylon-cotton ripstop, 230 g/m² (6.8 oz/yd²), thickness 0.50 mm | sourced (fabric class), E (thickness) |
| Ripstop grid pitch | 6.0 mm, reinforcement yarn pairs 0.5 mm wide; ground plain weave ≈ 40 ends/cm × 20 picks/cm (yarn pitch ≈ 0.25 mm warp / 0.5 mm weft) | brief (6 mm), E |
| Stretch panels | nylon/elastane 4-way stretch woven (Tweave Durastretch class), 240 g/m², matte, no grid, 0.55 mm | sourced (class), E |
| Knee-pocket fabric | 500D Cordura nylon, black, 270 g/m², 0.60 mm, PU-coated inner face | sourced, E |
| Hook-and-loop | 25 mm black (knee pocket top, waist adjusters, pocket flaps) | sourced |
| Zip | YKK #5 coil, 180 mm, black tape 32 mm, black metal slider with 25 mm pull | sourced (#5), E |
| Waist button | 17 mm tack button, black-oxide brass, with 4 mm shank | E |
| Thread | Tex 70 bonded nylon, black, Ø 0.33 mm (topstitching, felling); Tex 45 for pocket bags | sourced (Tex 70 standard), E |
| Stitch pitch | 7 spi = 3.6 mm (visible rows); bar tacks 10 × 2.5 mm, 28 stitches, 42 stitches at belt loops | sourced |
| Double-needle gauge | 1/4 in = 6.4 mm | sourced |
| Seam allowances | 10 mm general; 15 mm on felled seams; 25 mm hem allowance (20 mm finished hem) | sourced (standard) |
| Weight of the finished garment | ≈ 900 g | E |

### 3.2 Pattern pieces (finished dimensions for THIS body; measured values from §2.1, estimates E)

| # | Piece | Count | Finished size (mm) | Fabric | Tag |
|---|---|---|---|---|---|
| P1 | Front thigh panel (waist to knee-pocket top seam) | 2 | 330 tall at CF (rise 240 incl. curve) … 410 at side; width 300 at hip, 260 at knee seam | shell | measured heights, E widths |
| P2 | Back thigh panel with yoke seam 90 mm below the waistband | 2 | 420 tall at CB; width 320 at hip, 280 at knee seam | shell | E |
| P3 | Articulation panel above the knee pocket (3 tucks each side) | 2 | 42 tall × 260 wide (stretch), gathered from 320 | stretch | measured height |
| P4 | Knee pocket front (pad pocket) | 2 | 175 wide × 225 tall (R 170 × 231 proj.), top opening with 25 mm hook-and-loop flap, 30 mm deep when loaded | Cordura | measured |
| P5 | Knee pocket side gussets | 4 | 225 × 25 | Cordura | E |
| P6 | Popliteal (back of knee) stretch panel | 2 | 120 tall × 180 wide | stretch | E |
| P7 | Centre-front shin panel (reinforced, double layer) | 2 | 90 wide × 320 tall (knee pocket bottom h 400 → hem h 80 unstacked) | shell ×2 | measured width (±45 mm seams) |
| P8 | Lateral shin panel | 2 | 170 wide at top, 160 at hem × 320 tall | shell | E |
| P9 | Medial shin panel | 2 | 180 → 160 wide × 320 tall | shell | E |
| P10 | Crotch gusset diamond | 1 | 200 long (front-to-back) × 120 wide | stretch | E |
| P11 | Waistband, two-ply with interfacing | 1 | 45 tall × 880 circumference + 40 underlap; curved (contour) band | shell | measured height |
| P12 | Fly front facing (J-stitch 35 mm from CF) and fly shield | 1 + 1 | 180 × 50; shield 180 × 45 | shell | sourced (#5 zip 180) |
| P13 | Belt loops | 7 | 12 wide × 60 long, two-ply folded (1.4 mm thick) | shell | E (count) |
| P14 | Front slash hand pockets (bag + facing) | 2 | opening 160 along a 60°-off-vertical line from the waistband; bag 280 deep | shell + pocketing | E |
| P15 | Back pockets with flaps | 2 | 150 wide × 160 deep; flap 60 tall, hook-and-loop | shell | E (hidden) |
| P16 | Thigh cargo pockets, bellows | 2 | 200 wide × 190 tall × 25 deep; flap 70 tall with 2 × 50 mm hook-and-loop; centre pleat 40 | shell | E (hidden under rigs) |
| P17 | Calf pockets, slim, piped | 2 | 85 wide × 145 tall × 15 deep; flap 45 tall; 3 mm cord piping on the lateral edge; 2 grommets #00 | shell + grosgrain | measured w/h |
| P18 | Hem facing | 2 | 20 tall × 460 circumference | shell | E |

### 3.3 Body measurements driving the pattern (measured from the figure; ease E)

| Quantity | Body | Garment (with ease) | Tag |
|---|---|---|---|
| Waist circumference at h 890 (width 310 mm under the vest) | ≈ 850 | 880 | measured width, E depth |
| Hip circumference at h 827 (width 350) | ≈ 1000 | 1040 | measured width |
| Thigh circumference at crotch level (width 178) | ≈ 560 | 600 | measured width |
| Knee circumference at the cap (pocket width 175) | ≈ 410 | 500 incl. pocket bulk | measured |
| Calf (width 160) | ≈ 420 | 480 | measured |
| Leg opening (visible stacked width 131–136 over a 140 mm boot shaft) | — | 460 (flat 230) | E from the stack |
| Vertical waist-top → crotch | 127 (60 px) | 127 | measured — short, as drawn |
| Front rise along the curve / back rise | — | 240 / 330 | E |
| Visible outseam (waist top h 890 → cuff edge h 191) | 699 | — | measured |
| Pattern outseam (unstacked) / inseam | — | 810 / 680 (≈110 mm absorbed by three rolls) | E from roll heights |
| Knee-pocket centre height R / L | 519 / 505 | pocket spans h 619 → 400 | measured |

### 3.4 Hardware and small parts

| Part | Count | Size (mm) | Material / finish | Where |
|---|---|---|---|---|
| Tack button | 1 | Ø 17, 3 thick, 4 shank | brass, black oxide, matte | waistband CF, 15 below the top edge, hidden by the belt |
| Zip slider + pull | 1 | 12 × 20 slider; pull 25 × 6 | zinc, black | fly, hidden |
| Belt loops | 7 | 12 × 60 | shell, 2-ply | CF ± 80, side seams, CB ± 90, CB |
| Bar tacks | 38 | 10 × 2.5 (belt loops 12 × 3) | Tex 70 black | loop ends (14), pocket corners (16), fly bottom (1), knee-pocket corners (4), calf-pocket flaps (2), gusset points (1 each end) |
| Grommets #00 | 4 | Ø 5 outer, Ø 3 hole | brass, black | calf pockets (2 each) |
| Shock-cord loop | 2 | Ø 3, 50 long | black elastic | through the grommets |
| Hook-and-loop | — | 25 wide | black | knee-pocket tops (175), waist adjusters (2 × 60), cargo and calf flaps |
| Drain grommet | 2 | Ø 5 | brass, black | cargo pocket bottoms (hidden) |

### 3.5 How the real garment wears
Dust settles on the thigh tops and the knee-pocket tops; cuffs pick up floor grime and darken; the gusset and inner-thigh seams whiten where the ripstop abrades (lighter yarn cores exposed along seam ridges); knee-pocket Cordura polishes to a sheen and scuffs pale grey; fold crests of NYCO show a faint satin highlight; colours fade 5–10 % on sun-facing panels (thigh fronts) relative to the inner thighs; stitching stays black but frays white at bar tack ends.

---

## 4. Geometry construction plan

Everything below is executed by `scripts/parts/09_combat_trousers.py` (headless Blender 4.5, bmesh/bpy/geometry nodes) with helpers in `scripts/lib/cloth_tube.py`, `scripts/lib/camo_gen.py` (system python3 -I, numpy + PIL, called via subprocess) and `scripts/lib/gn_stitches.py`. Object naming follows `Trousers.<Side>.<Component>`; everything lives in collection `Trousers`. The script deletes all objects, meshes, node groups, images and materials whose names start with `Trousers.` before rebuilding (rule 4). Two modes: `--mode posed` (hero deliverable, default) and `--mode rest` (rig deliverable, §7).

### 4.1 Construction decision (hybrid) and justification
Options weighed: (a) flat sewn panels with sewing springs simulated onto the posed body; (b) body-derived Shrinkwrap + Solidify + procedural wrinkle displacement, no simulation; (c) hybrid: a pre-shaped, body-derived two-leg tube with the real panel/seam topology, a short pinned cloth **settle** simulation in the posed state to obtain the drape, hem stacking and crotch tension, Shrinkwrap only for the bands under belt and straps, then geometry-nodes wrinkle displacement for everything the 10 mm sim mesh cannot resolve.
Decision: **(c) hybrid.** (a) is the most physically faithful but on 4 CPU cores with a 12 k-vertex garment, sewing-spring assembly over a posed body (deep hip rotation, abducted legs, drop-leg straps in the way) is the most failure-prone step in Blender cloth: panels tangle, springs overshoot, and results differ between runs if any collider moves — unacceptable for an idempotent build. (b) cannot produce the two facts that define the reference silhouette, the fat hem rolls and the inner-thigh tension folds, without hand-tuned fold profiles that will read as fake in the closeups. (c) gets the drape from physics where physics is cheap and reliable (a tube already around the body, pinned at the waist, falling 110 mm onto a boot), and keeps everything else deterministic. Fallback (if the sim fails the stability checks in §9.3): option (b) with the parametric hem-roll profile of §4.13.

### 4.2 Inputs expected from other parts (see §10.1)
`Body.Mesh.Posed` (MPFB base mesh, posed, ≈ 13 k quads, with vertex groups), `Body.Collider` (decimated copy, 6–8 k faces), armature `Morgan.Rig` (MPFB **default** rig names: `pelvis.L/R`, `upperleg01/02.L/R`, `lowerleg01/02.L/R`, `foot.L/R`, `spine01` — the inventory lists the bundled rigs `default`, `rigify.human` [VERIFY: body spec for the final choice]; the script carries a `BONE_MAP` dict), Empties `Body.Empty.Crotch` (X −0.042, Y −0.02, Z 0.763), `Body.Empty.Knee.R/L`, `Body.Empty.Ankle.R/L`, `Kneepad.R/L.CapProxy` (ellipsoid 170 × 200 × 28 mm, from spec 12 or generated here as a stand-in), `Boot.R/L.ShaftProxy` (cylinder Ø 140 mm from h 60 to h 205 with a 20 mm rounded top rim and a 35°-sloped instep wedge toward −Y, friction material), `Belt.Proxy` (torus band h 812–859 at body + 6 mm), `Strap.R.Upper/Lower.Proxy`, `Strap.L.Lower.Proxy` (bands 33 mm tall). If a provider object is missing the script builds the stand-in and tags the render "STAND-IN" in the file name.

### 4.3 Step 1 — leg axes and section table (bmesh helper `cloth_tube.leg_axis`)
For each leg read the posed bone chain head/tail positions: hip joint (`upperleg01` head), knee (`lowerleg01` head), ankle (`foot` head). Build a polyline with 3 segments and sample stations every 10 mm along it from h 890 (waist) to h 80 (unstacked cuff, 110 mm below the final stacked cuff edge so that 110 mm of excess forms the rolls), refined to 6 mm spacing between h 720 and h 600 (knee-pocket top + articulation) and between h 320 and h 80 (hem). Section orientation: perpendicular to the local axis, slerped over ±40 mm around the knee. The pelvis stations (h 890 → 763) follow the vertical through the hip-joint midpoint (X −0.03), offset −10 mm in Y (the trousers hang slightly forward of the hip line because the belly pushes the waistband).

Section ellipses (semi-axes a = lateral, b = sagittal, in mm; a 10 % forward bias means the centre shifts toward −Y) — all stations are first fitted to `Body.Collider` by casting 64 rays from the station centre and taking body radius + ease, then clamped to these minima so the garment never reads skin-tight:

| Station h (mm) | Zone | Min a / b | Ease over body | Loop verts |
|---|---|---|---|---|
| 890 (waist top) | waistband | 150 / 115 | +5 (two-ply band) | 128 (pelvis) |
| 859–812 | under belt | 152 / 118 | +5 | 128 |
| 800 | hip | 170 / 130 | +20 | 128 |
| 763 (crotch apex) | split | — | — | 2 × 64 begins |
| 740 | upper thigh | 96 / 90 | +22 | 64 |
| 795–761 (R) | under upper strap | body + 3 | +3 (Shrinkwrap band) | 64 |
| 700–651 (R), 710–668 (L) | under lower straps | body + 3 | +3 | 64 |
| 672–655 | knee-pocket top seam | 88 / 84 | +18 | 64 |
| 619–400 | knee pocket | 90 / 82 front +28 over the cap | +16 lateral, cap proxy in front | 64 |
| 400–320 | upper shin | 82 / 76 | +18 | 64 |
| 320–80 | lower shin to cuff | 80 → 73 / 74 → 70 | +18 → +14 | 64 |

### 4.4 Step 2 — tube mesh (`cloth_tube.build_two_leg_tube`)
1. For each leg create the 64-vertex loops at every station (bmesh.verts.new), connect consecutive loops with quads (bmesh.ops.bridge_loops per pair, or direct face creation). Vertex 0 of each loop is at centre-front (−Y), index increases toward his left (+X) viewed from above, so angular index ↔ panel position is fixed: inseam at index 32 ± 2 (medial), outseam at 0 ± 32 … (lateral = index 48 for the left leg, 16 for the right leg; the helper mirrors indices for the right leg so that "lateral" is always one named constant).
2. Extend both leg tubes upward from the crotch to the waist as separate 64-loops (h 763 → 890), their inner halves overlapping in the pelvis; delete the medial faces of both tubes above h 775 (indices 24–40), then bridge the two front cut edges (front rise seam, 11 loops) and the two back cut edges (back rise seam) with `bmesh.ops.bridge_loops`. The result is one 128-vertex pelvis loop at the waist and a diamond hole at the crotch.
3. Fill the diamond with the gusset: `bmesh.ops.grid_fill` on the 4 boundary edges (span 6 × 10) → 60 quads; tag them `Panel=Gusset`.
4. Mark panel membership and seams as integer/boolean attributes at creation (`panel_id` int on faces; `seam` bool on edges) using the station height and angular index tables of §3.2: front rise (index 0 column, h 890 → 763), back rise (index 32 column of the pelvis), yoke seam (h 800, back half), inseam (medial column, crotch → cuff), outseam (lateral column), knee-pocket top seam (h 665 ring, front 2/3), knee-pocket bottom (h 400 ring, front 2/3, dipping 12 mm on the lateral side), pocket side seams (the two columns at ±87 mm from CF, h 665 → 400), shin seams A/B (columns at ±45 mm from CF, h 400 → 80), popliteal panel seams (back third, h 580 and h 460), hem fold line (h 100 ring), waistband seam (h 845 ring), articulation seam (h 620 ring = pocket top).
5. Waistband: duplicate the top 5 loops (h 890 → 845) outward by 1.5 mm as a second ply (Solidify later gives both plies thickness) — implemented as a separate object `Trousers.Waistband` with its own Solidify 1.5 mm, parented and Surface-Deformed to the trousers after the sim (§4.11) so the sim mesh stays single-layer.
6. Resulting object `Trousers.Sim` (mode posed) — budget: pelvis 128 × 13 loops + 2 legs × 64 × 92 loops + gusset ≈ **13.5 k quads, 13.7 k verts**, all quads, no poles except 8 at the bridge corners; origin at (0, 0, 0), +Z up.
7. UVs: `UV_Real` — per panel, U = arc length around the loop from the panel's first seam (metres), V = station arc length from the waist (metres), 1 UV unit = 1 m, each panel offset by a random (seeded) translation of 0.2–0.8 m so the camouflage differs across every seam; `UV_Atlas` — the same islands packed into UDIM 1001 (right leg + right pelvis half) and 1002 (left) at 4096 px each ≈ 0.27 mm/texel on a 2.2 m² garment (`bpy.ops.uv.pack_islands` with margin 0.01 after `uv.seams_from_islands` from the `seam` attribute).

### 4.5 Step 3 — vertex groups (parametric, before the sim)
`Trousers.Pin` (top 3 loops, weight 1.0; loop 4–5 weight 0.5), `Trousers.Belt` (h 812–859, 1.0), `Trousers.StrapBand.R.Upper` (h 761–795), `.R.Lower` (651–700), `.L.Lower` (668–710) each with a 6 mm linear falloff, `Trousers.Gusset` (gusset + 30 mm ring, 1.0 → 0), `Trousers.KneePocket.R/L` (pocket faces), `Trousers.Articulation.R/L` (h 619–665 front 2/3), `Trousers.Popliteal.R/L` (back third h 460–580), `Trousers.Shin.R/L`, `Trousers.Hem.R/L` (h 80–300, 1.0 below 200 fading to 0 at 300), `Trousers.Shrink` (gusset 1.0, strap bands 0.8, hem 0.3, elsewhere 0), `Trousers.NoSelfCol` (pinned waistband only), `Trousers.DustUp`, `Trousers.Grime` (h < 320: 1 → 0 at 320), `Trousers.Whitening` (within 15 mm of gusset seams and the inseam's top 150 mm).

### 4.6 Step 4 — colliders
`Body.Collider`: Collision modifier, `thickness_outer 0.002`, `thickness_inner 0.002`, `cloth_friction 8`, `use_culling True`. `Boot.R/L.ShaftProxy`: `thickness_outer 0.003`, **`cloth_friction 30`** (so the hem grips the collar and stacks instead of sliding), the rounded top rim is essential (a sharp rim slices the cloth). `Kneepad.R/L.CapProxy`: friction 10. Belt and strap proxies are **not** colliders (a 6 mm gap between body and strap would jitter); their effect comes from the shrink group and the post-sim Shrinkwrap bands (§4.8).

### 4.7 Step 5 — cloth settle simulation (`bpy.types.ClothModifier`, property names as in the API)
Scene: 25 fps, frames 1–100, gravity (0, 0, −9.81). On `Trousers.Sim`:

| Group | Property | Value | Why |
|---|---|---|---|
| Physical | `settings.quality` | 8 steps | stability with 10 mm quads [VERIFY: research_blender_capabilities] |
| | `settings.mass` | 0.35 (kg per vertex, Blender convention) | heavy NYCO drape; cotton preset 0.3, denim 1.0 |
| | `settings.air_damping` | 1.0 (keyframed to 3.0 at frame 70) | kill residual swing before applying |
| Stiffness | `tension_stiffness` / `compression_stiffness` | 30 / 30 | between cotton (15) and denim (40) |
| | `shear_stiffness` | 15 | ripstop resists shear less than denim |
| | `bending_stiffness` | 2.0 (hem group 3.0 via `vertex_group_bending`, max 3.0) | fat rolls rather than crinkles |
| | `bending_model` | 'ANGULAR' | — |
| Damping | `tension_damping` / `compression_damping` / `shear_damping` | 5 / 5 / 5 | — |
| | `bending_damping` | 0.5 | — |
| Internal springs / pressure / sewing | off | — | pre-shaped tube, not sewn flat panels |
| Shape | `vertex_group_mass` (pin) | `Trousers.Pin`, `pin_stiffness 1.0` | waistband fixed to the body |
| | `vertex_group_shrink` | `Trousers.Shrink` | — |
| | `shrink_min` / `shrink_max` | 0.0 / keyframed 0.0 → 0.12 over frames 40–70 | gusset and strap bands tighten, pulling the radial crotch folds and squeezing the bands |
| Collisions | `collision_settings.collision_quality` | 4 | — |
| | `distance_min` | 0.003 | cloth-body gap |
| | `impulse_clamp` | 0 | — |
| | `use_self_collision` | True (frames 1–20 off via keyframe to let the tube settle) | folds must not interpenetrate |
| | `self_distance_min` / `self_friction` | 0.0025 / 5 | — |
| | `vertex_group_self_collisions` | inverse of `Trousers.NoSelfCol` | — |
| | `friction` | 10 (body), boot friction 30 (on the collider) | — |

Timeline: frames 1–40 drop and settle (the hem falls ≈110 mm onto the collar/instep and begins to pile); 40–70 shrink ramp (gusset tension folds, strap bands); 70–100 damped settle. The script steps `scene.frame_set` 1 → 100 (point cache in memory), checks stability (§9.3), then applies the modifier at frame 100 (`bpy.ops.object.modifier_apply` on an evaluated copy → `Trousers.Base`). Expected cost: 13.7 k verts × 100 frames ≈ 2–4 min on 4 cores [VERIFY: research_blender_capabilities]. Determinism: identical inputs on the same Blender build give identical results; the script writes a SHA-1 of the resulting vertex array to `renders/09_combat_trousers/sim_hash.txt` for regression.

### 4.8 Step 6 — band fitting (Shrinkwrap, deterministic)
On `Trousers.Base`: three Shrinkwrap modifiers (`wrap_method 'NEAREST_SURFACEPOINT'`, `wrap_mode 'OUTSIDE_SURFACE'`, `offset 0.003`, target `Body.Collider`), each limited by `vertex_group` = `Trousers.Belt`, `Trousers.StrapBand.R.Upper`, `.R.Lower`/`.L.Lower` (the last two are one modifier with a merged group). Applied in place. Result: the cloth under the belt and straps is pulled to body + 3 mm; the sim has already bulged the cloth above and below the bands.

### 4.9 Step 7 — modifier stack of the final object `Trousers.Main` (kept live, order matters)
1. `Subdivision` level 1 (Catmull-Clark, `use_limit_surface True`) → 54 k quads (edge ≈ 5 mm).
2. `GeometryNodes` **`Trousers.GN.Wrinkles`** — Set Position along normals with the zone fields of §6.3 (uses the attributes/vertex groups, Empties and noise). Needs the 5 mm mesh to resolve 13–25 mm wavelengths.
3. `Solidify`: thickness 0.0006 (0.6 mm fabric; 1.2 mm on `Trousers.Shin` and the knee pockets via `vertex_group` + `thickness_vertex_group 0.5`), `offset −1` (thickness inward), `use_even_offset True`, `use_rim True`, `use_quality_normals True`.
4. `Subdivision` level 1 (render 1, viewport 0) → ≈ 430 k faces incl. rim.
5. `GeometryNodes` **`Trousers.GN.Details`** — seam ridges (+1.2 mm normal displacement within 4 mm of `seam` edges, with a 0.4 mm valley at the stitch rows), stitch instancing (§4.10), ripstop is NOT geometry (shader, §5.4).
6. `DataTransfer` (custom normals from `Trousers.Base` smoothed) — only if the Subdivision shows faceting at the hem rim.
7. Mode rest only: `Armature`. Mode posed: `SurfaceDeform` (§7).

### 4.10 Step 8 — stitches, bar tacks, ridges (`gn_stitches.py`, node group `Trousers.GN.Details`)
* Seam curves: `Mesh to Curve` with selection = `seam` edge attribute (carried through the subdivisions as an edge attribute; the helper re-tags the subdivided edges by proximity to the original seam edges), `Resample Curve` length 3.6 mm (`pitch`), `Instance on Points` of `Trousers.StitchMesh` (a capsule 2.6 mm long × 0.33 mm Ø, 6 segments × 4 rings = 48 tris) aligned to the curve tangent (`Align Rotation to Vector`), surface normal from `Sample Nearest Surface` keeps the stitch lying flat 0.15 mm above the ridge; `Random Value` ±6° yaw and ±0.1 mm offset per stitch so the rows are not machine-perfect.
* Double-needle rows: the same curve offset by ±3.2 mm along (normal × tangent) → two rows 6.4 mm apart on felled seams (inseam, outseam, rise seams, yoke, shin seams A/B, knee-pocket perimeter). Single rows: hem (1 row at 18 mm above the edge), waistband (1.5 mm from the top edge and 1.5 mm from the bottom edge), pocket flaps (1.5 mm edge-stitch), fly J-stitch (one row 35 mm from CF, curving to the fly bottom), gusset perimeter (double row).
* Bar tacks: `Trousers.BarTackMesh` (10 × 2.5 × 0.6 mm block of 14 parallel 0.33 mm threads, 160 tris) instanced at the 38 points of §3.4, each located by (station h, angular index) → world via `Sample Index` on the evaluated mesh.
* Ridge displacement: for every vertex, distance to the nearest seam edge d (via `Geometry Proximity` against the seam-edge curve) → offset = 1.2 mm × smoothstep(4 mm → 0, d) − 0.4 mm × gaussian(d − 3.2 mm, σ 0.4 mm) (stitch valley) along the normal.
* Budget: total visible seam length ≈ 14 m (both legs) → 14 000 / 3.6 ≈ 3 900 stitches per row; with double rows on 60 % of it ≈ 6 200 instances × 48 tris ≈ 0.30 M tris, realized at render time only (`Realize Instances` behind a `Switch` driven by a scene property `trousers_lod` so hero-distance renders can use the shader-bump stitches of §5.6 instead).

### 4.11 Step 9 — attached components (separate objects, all bound to `Trousers.Main` with `SurfaceDeform` after the sim so they follow the drape)

| Object | Construction | Size / position | Budget |
|---|---|---|---|
| `Trousers.Waistband` | duplicate of the top 5 loops offset 1.5 mm, Solidify 1.5 mm, rim; top edge rounded by Bevel 0.8 mm (2 segments) | h 845–890 all round | 1.3 k |
| `Trousers.Fly` | planar strip 50 × 180 mm on the CF left side (his left overlaps his right), Solidify 1.0 mm, J-stitch via `GN.Details` row; zipper teeth hidden under the lap (not built); fly bottom bar tack at h 735 | CF, h 735–885 | 0.6 k |
| `Trousers.BeltLoop.00…06` | bmesh box 12 × 60 × 1.4 mm bent to the waistband curvature (Simple Deform BEND 25°), Bevel 0.3 mm; bar tacks at both ends; sewn 3 mm below the waistband top and at h 845 | CF ± 80, side seams, CB ± 90, CB | 7 × 0.4 k |
| `Trousers.Button` | cylinder Ø 17 × 3 mm, dome top (Bevel 1.5 mm, 4 seg), 4 mm shank | CF, h 875 | 0.5 k |
| `Trousers.R/L.HandPocket` | opening slit cut by `bmesh.ops.bisect_edges` along the P14 line + bound edge (3 mm Solidify strip), bag not built (dark interior face flagged `Panel=PocketInside`, material §5.7) | from waistband at X ± 120 down 160 mm at 60° | 0.3 k each |
| `Trousers.R/L.CargoPocket` | box 200 × 190 × 25 mm with a 40 mm centre pleat (two folds), flap 200 × 70 × 1.2 mm with 10 mm Bevel on the lower corners; 2 hook-and-loop squares as colour patches; bar tacks at 4 corners; Shrinkwrap (PROJECT, negative Y of local) onto `Trousers.Main` with offset 0 so the back face sits on the thigh | lateral thigh, top edge at h 740, under the drop-leg rigs | 1.2 k each |
| `Trousers.R/L.BackPocket` | flap-covered patch 150 × 160 × 1.2 mm | back thigh, top at h 760 | 0.4 k each |
| `Trousers.R/L.CalfPocket` | box 85 × 145 × 15 mm, lateral edge piped: piping = curve bevel Ø 3 mm along the lateral edge (`Trousers.L.CalfPocket.Piping`), flap 85 × 45 mm, two grommets (torus Ø 5 outer, 1 mm tube) at h 356 and h 345 on the piping, shock-cord loop (curve bevel Ø 3, 50 mm) | lateral shin, top at h 435 immediately below the knee pocket, lateral to shin seam A | 1.5 k each |
| `Trousers.R/L.KneePocketFlap` | 175 × 30 × 1.2 mm flap over the pocket top, hook-and-loop strip | h 619–649, under the cap's top slots | 0.3 k each |
| `Trousers.R/L.HemFacing` | the lowest 20 mm of the main mesh is tagged; `GN.Details` adds the fold-line ridge and the single topstitch row; no separate object | h 80–100 (unstacked) | — |

### 4.12 Step 10 — where the pieces join
Attached objects use `SurfaceDeform` (`target Trousers.Main`, bind at build time, `falloff 4`, `strength 1`). Their contact edges are placed 0.3 mm proud of the trouser surface so the Solidify rim never z-fights; the pockets' back faces are deleted (`Panel=Hidden`). Belt loops pass under the belt (other spec) — the belt spec must leave 1.6 mm for them (§10.1).

### 4.13 Fallback (no simulation) — only if §9.3 fails twice
`Trousers.Sim` → Shrinkwrap whole garment to `Body.Collider` (`OUTSIDE_SURFACE`, offset per zone from the ease table: 0.018 thigh, 0.016 knee, 0.014 shin), Smooth (factor 0.5, 10 iterations) to remove body detail, Solidify as above, then `GN.Wrinkles` with the extra `hem_rolls` field: for each leg a parametric stack of three toroidal rolls at h 212/254/293 with major radius = shin radius + 12 mm and tube radii 16/15/14 mm, blended with a smoothstep over 10 mm, plus a 20 mm cuff flare at h 191, and the gusset fan of §6.3 at full strength. Cheap (seconds) but the rolls look designed; mark the renders "FALLBACK".

### 4.14 Topology targets and poly budget summary

| Object | Faces (base / render) | Topology notes |
|---|---|---|
| `Trousers.Main` | 13.5 k / ≈ 430 k after 2 subdivisions + solidify | all quads; edge loops at every seam ring and column; 6 mm loops at knee and hem; 8 poles at the rise bridges only |
| Stitches + bar tacks | — / 0.30 M tris (LOD-switched) | instances |
| Attached objects | 11 k / 45 k | quads, bevelled edges |
| Total | ≈ 25 k / ≈ 0.78 M | memory ≈ 1.2 GB in Cycles [VERIFY: research_blender_capabilities] |

---

## 5. Materials and textures

All materials are Principled BSDF node trees built by `scripts/lib/materials.py` helpers; CC0 maps come from `assets/textures/` (already downloaded per `assets/textures/manifest.json`): `Fabric061` (rough synthetic weave, 40 cm tile, 2K, Color/Normal/Roughness/AO/Displacement), `Fabric082A` (fine smooth woven, 2K) as alternative, `Fabric048` (polyester vest weave, 40 cm) for the Cordura knee pockets, `SurfaceImperfections015` (dust) and `SurfaceImperfections017` (dirt) as grunge masks. Colour management: AgX, so all hex albedos below are sRGB values to be fed through the sRGB → linear conversion of the image node / `Hex → linear` helper.

### 5.1 Material list

| Material | Applies to | Base recipe |
|---|---|---|
| `Trousers.Mat.Shell` | all shell panels (P1, P2, P7–P9, P11–P18, loops, flaps) | camo albedo × weave × weathering; Roughness 0.62 base; Sheen 0.35 / Sheen Roughness 0.4 / Sheen Tint 0.6; Specular IOR level 0.45; Subsurface 0 |
| `Trousers.Mat.Stretch` | P3 articulation, P6 popliteal, P10 gusset | same camo UV but 15 % darker, no ripstop grid, finer weave (Fabric082A normal at 10 mm tile, strength 0.4); Roughness 0.70; Sheen 0.2 |
| `Trousers.Mat.Cordura` | knee pockets P4/P5, flap | albedo #1c1c1e; Fabric048 normal (tile 12 mm, strength 0.6) + roughness map remapped 0.45–0.65; Sheen 0.5 (Cordura's satin look); edge scuffs §5.5 |
| `Trousers.Mat.Piping` | calf-pocket piping, hook-and-loop edge binding | albedo #2e3136, Roughness 0.32, anisotropic 0.3 along the cord (tangent from the curve); this is what reads #7c7e87 in the cool light |
| `Trousers.Mat.Thread` | stitches, bar tacks | albedo #141311, Roughness 0.38, Sheen 0.3; frayed ends +15 % lighter via `Random Value` per instance |
| `Trousers.Mat.HookLoop` | hook-and-loop patches | albedo #161616, Roughness 0.85, bump from a 1 mm noise (loop pile) |
| `Trousers.Mat.Metal` | button, grommets, zipper pull | Metallic 1, albedo #1c1a18 (black oxide), Roughness 0.35, edge wear to #8c8578 by Pointiness > 0.6 |
| `Trousers.Mat.ShockCord` | grommet loop | albedo #121212, Roughness 0.7, fine weave bump 0.5 mm pitch |
| `Trousers.Mat.PocketInside` | pocket interiors | albedo #0a0a09, Roughness 0.9 |

### 5.2 Camouflage generator (primary: image tile generated by numpy; verified prototype `ref/zoom_camo_generator_prototype_v2.py`)
Generated by `scripts/lib/camo_gen.py` with system `python3 -I` (numpy + PIL) at build time, cached in `assets/generated/Trousers.Camo.4096.png` (seed 7, 4096 × 4096 px covering exactly **1.0 m × 1.0 m**, seamless), plus a `Trousers.CamoToneID.png` (tone index 0–3 as grey levels) for verification and for the stress-whitening mask.

| Stage | Recipe (all lengths real-world mm; px = mm × N/1000) | Purpose |
|---|---|---|
| Macro field M | tileable spectral-synthesis fBm: 2 octaves, base wavelength 220 mm, persistence 0.5, log-normal band width 0.45 | splits the cloth into large darker/lighter zones (the "background" of MultiCam-type patterns) |
| Blotch field B | fBm 3 octaves, base wavelength 95 mm, persistence 0.45; domain-warped by a 25 mm noise with 6 mm amplitude (and its 1/3-tile-shifted copy for the other axis) | the 15–50 mm islands with organic outlines |
| Speckle S | fBm 2 octaves, base wavelength 14 mm | sparse small islands |
| Combined F | F = 0.55 B + 0.35 M + 0.10 S, then Gaussian-blurred σ = 3 mm before thresholding | the pre-blur removes granularity; v1 without it read as granite |
| Tone thresholds | quantiles of F at 0.30 / 0.65 / 0.90 → tone id 0/1/2/3 | fractions 30 / 35 / 25 / 10 % exactly |
| Soft edges | each tone's binary mask Gaussian-blurred σ = 2.5 mm, re-normalised, used as mix weights | 3–5 mm feather; no edge sharper than the reference |
| Albedo tones (sRGB) | T0 **#0c0c0a**, T1 **#1c1a17**, T2 **#36322c**, T3 **#5e5246** | lit under the key these render ≈ #0a0b08 / #171513–#262524 / #322e29–#3e3a35 / #615348–#685d53 (the consolidated lit samples); the cool-lit left leg must give #38322c / #363836 at (880,600)/(900,595) |
| Per-tone roughness | T0 0.66, T1 0.64, T2 0.60, T3 0.58 (dye load lowers the pile sheen) | subtle |

Prototype result at 1024 px (`zoom_camo_generated_at_refscale_v2.png`, downsampled to 4.72 px/cm and measured with the same script as the reference): light-blotch median 20–27 mm, p75 22–47, max 42–62; dark median 16–26, max 43–56; local contrast 105–130 % — inside the reference ranges of §2.3 (median 14–25 / max 42–61 / contrast 101–134 %). Tone fractions 29/35/26/10.

Mapping: image node, `UV_Real`, Box projection off (UV), extension REPEAT, interpolation Cubic. Because each panel's UV island is offset by a seeded random vector (§4.4), the pattern breaks at every seam exactly as a cut-and-sewn garment does; both legs use different offsets (never mirror).

Fallback / alternative (shader-only, no image): Voronoi `SMOOTH_F1` scale 14 per metre (cells ≈ 70 mm), randomness 1.0, smoothness 0.35, vector pre-warped by Noise (scale 40, detail 3) × 0.006 m, Color output → Color Ramp (CONSTANT, stops 0.30/0.65/0.90 → T0…T3) mixed with the same over a second Voronoi offset by (0.37, 0.61) using Voronoi `Distance to Edge` < 0.003 as a soft-edge mask (Map Range 0–0.003 → 1–0, smoothstep). Cheaper to tweak, harder to verify; use only if the image route fails.

### 5.3 Weave and ripstop (procedural, in `Trousers.Mat.Shell`)
* Ripstop grid: `UV_Real` × 1000 → Separate XYZ; gridU = smoothstep(0.42, 0.46, |frac(u/6 mm) − 0.5|), gridV likewise; grid = max(gridU, gridV) → bump +0.08 mm (Bump node strength 0.35, distance 0.0001) and roughness −0.05 along the grid (the doubled yarns are smoother and catch the key: this is the "faint lattice on the fold crests").
* Ground weave: `Fabric061` NormalGL (strength 0.5) and Roughness (Map Range 0.3–1.0 → 0.55–0.70) tiled at **50 mm** via `UV_Real` × 20, anti-tiled by blending two copies rotated 90° with a 300 mm noise mask (Mix factor noise, 0.3–0.7) — tile size chosen so that the weave texel is 0.024 mm (2048 px / 50 mm) and the ripstop grid stays procedural (no visible repeat at V8). AO map used at 0.3 as a multiplier on the albedo (yarn shadowing).
* Texel density: camo 0.24 mm/texel (4096 px / m), weave 0.024 mm/texel, baked masks 0.27 mm/texel on `UV_Atlas` — adequate for V8 (100 mm lens at 0.6 m ⇒ ≈ 0.09 mm/px on the 150 mm patch: the weave resolves, the camo edges are soft by design).

### 5.4 Fabric micro-wrinkle bump
A fine wrinkle normal from two layered Noise textures (scale 180 and 450 per metre, detail 2, roughness 0.5) through a Bump node (strength 0.15, distance 0.0004) multiplied by (1 − `seam` proximity) so seams stay crisp. This gives the 3–8 mm crumple the displacement does not carry.

### 5.5 Weathering masks (baked once to `UV_Atlas` 2K per UDIM by `bpy.ops.object.bake` type EMIT from helper materials, then used as image masks; the bake set is: `AO` (cycles, 64 samples), `Pointiness` (Geometry node → EMIT), `UpFacing` (normal·Z), `HeightBand` (world Z), `GussetDist`)

| Effect | Mask | Colour / shading change | Target values |
|---|---|---|---|
| Dust on upper thighs and knee-pocket tops | UpFacing (smoothstep 0.25 → 0.6) × HeightBand (h > 450) × `SurfaceImperfections015` Color (tile 65 cm, UV_Real, Map Range 0.4–0.9 → 0–1) × 0.35 | mix albedo toward **#8a7d70** by mask × 0.4; Roughness +0.08 | lit R thigh tan highlights #857061 (p95), #6e5e4c at (705,590) |
| Cuff grime | HeightBand (h < 320 → 1 at 200) × `SurfaceImperfections017` Opacity (tile 40 cm) × 0.6 + a 0.3 uniform base below h 230 | mix toward **#0e0d0b** by mask × 0.5; Roughness +0.1; speckles of #3a342c at 10 % (floor dust kicked up) | R cuff #050604 (720,800), L cuff #2e2a24 (920,800); hem medians #23221f / #262421 |
| Stress whitening at the gusset | GussetDist (1 within 6 mm of gusset seams and the top 150 mm of the inseams, → 0 at 15 mm) × Pointiness (> 0.5) × noise (scale 300/m) | mix toward **#4a443c** by mask × 0.45 (abraded yarn cores), Roughness +0.05, Sheen +0.2 | visible in V6 as pale seam ridges |
| Fold-crest sheen and wear | Pointiness remapped 0.52–0.62 → 0–1 | Roughness −0.10, albedo +12 % value | hem crests #4c3d2d / #373129 under the key |
| Knee-pocket scuffs | Pointiness on the Cordura × `SurfaceImperfections017` Color | streaks of **#4a4b4e** at 20 %, Roughness −0.15 (polished) | pocket p95 ≈ #3a3b3e |
| Panel fade | `panel_id` ∈ {front thigh, shin CF} → 1 | albedo +6 % value | subtle |
| Hidden interiors | PocketInside | #0a0a09 | — |

### 5.6 Shader-level stitches (LOD for hero distance)
When `trousers_lod == 0` the GN stitches are switched off and the seam rows are drawn in the shader: distance-to-seam field baked as `SeamDist` (mm) on `UV_Atlas`; rows at 3.2 mm either side, dashes via frac(seam arc length / 3.6 mm) < 0.7, colour `Trousers.Mat.Thread`, bump −0.2 mm. Identical gauge and pitch to the geometry stitches so the two LODs match.

### 5.7 Colour targets to hit after grading (reference pixels; render V1 and read 5×5 means)
(705,590) #6e5e4c · (760,600) #111111 · (880,600) #38322c · (925,600) #242a2f · (770,660) #2f3033 · (855,660) #242423 · (710,730) #463e34 · (905,740) #3c3730 · (940,720) #20252d · (715,775) #4c3d2d · (920,800) #2e2a24 · (760,730) #151517 (the WORLD-only calibration pixel from the lighting note). Tolerance ±10/255 per channel; failing pixels name the zone to tune (albedo tone, dust amount, grime amount, roughness).

---

## 6. Fibres, simulation or dynamics

### 6.1 Fibres
No particle hair. Fuzz along silhouettes comes from the Sheen layer (§5.1); frayed bar-tack ends are a per-instance lighter colour, not geometry.

### 6.2 Simulation
The settle simulation of §4.7 is the only dynamic step and is applied (baked into `Trousers.Base`); nothing stays dynamic in the delivered scene.

### 6.3 Wrinkle recipe by zone (`Trousers.GN.Wrinkles`, displacement d along the vertex normal, metres; all noises `Noise Texture` 4D with W = seed; masks are the vertex groups of §4.5 sampled as attributes; the sim already supplies the large drape, these are the secondary and tertiary folds)

| Zone | Field | Amplitude | Wavelength / count | Direction and extent | Mask |
|---|---|---|---|---|---|
| Crotch stress folds | fan of n = 6 folds per side radiating from `Body.Empty.Crotch`: θ = atan2 in the frontal plane of (p − apex); d = A·exp(−r/0.16)·sin(6θ + 2.0·noise(p, scale 8))·(0.6 + 0.4 noise(scale 30)) | A = 6 mm at r = 0, 4 mm at r = 100 mm | 6 folds over 180°, each 25–40 mm wide | from the apex 120–200 mm up the inner thighs and 60 mm up the front rise; stronger toward the abducted right leg (×1.3 for X < apex) | `Gusset` ∪ inner-thigh ring (angular index 24–40, h 600–790) |
| Knee articulation (above the pocket) | vertical ridges: d = A·sin(2π u/13 mm + noise)·window(h 619 → 665) | A = 2.5 mm | pitch 13 mm, 4–5 ridges visible on the front third | front 2/3 of the leg; ridges vertical (along the leg) | `Articulation.R/L` |
| Knee pocket over the cap | the cap proxy bulge is already in the sim; add 2 horizontal tension creases at the pocket's top corners: d = −2 mm Gaussian σ 6 mm at the corners | −2 mm | 2 per pocket | pocket corners (angular ±87 mm, h 640) | `KneePocket` |
| Popliteal folds (back of the knee) | horizontal rolls: d = A·cos(2π (h − h_knee)/32 mm)·exp(−|h − h_knee|/60 mm) × flex factor (R 1.0 for 17°, L 0.5 for 9°) | A = 6 mm (R), 3 mm (L) | pitch 32 mm, 2–3 rolls | back third of the leg | `Popliteal.R/L` |
| Hem stacking (secondary) | accordion on the sim rolls: d = 1.5 mm·sin(2π h/10 mm)·noise(scale 60) + diagonal twist creases d = 2 mm·sin(2π (u − 0.7 h)/45 mm) | 1.5 / 2 mm | pitch 10 mm / 45 mm | whole hem band; twist runs from the viewer-left down to the right on the right leg (reference `zoom_trousers_rhem_x8.png`) | `Hem.R/L` |
| Strap compression | rolls 18 mm above and below each strap edge: d = 5 mm·exp(−((h − h_edge ∓ 18 mm)/9 mm)²)·(0.5 + 0.5 noise(scale 20) around the circumference; stronger on the front/lateral slack side) | 5 mm | 1 roll each side of each strap | around the thigh; zero under the strap (Shrinkwrap band) | `StrapBand.*` dilated by 30 mm |
| Belt compression | same profile below the belt only, A 4 mm; the shirt covers above | 4 mm | 1 roll | around the hips below h 812 | `Belt` dilated downward 30 mm |
| Thigh drape | long diagonal pleats d = 4 mm·sin(2π (u·1.0 + h·0.8)/55 mm)·noise(scale 6) | 4 mm (fades to 1 mm at the knee) | pitch 55 mm | inner/back thigh, from the hip to the pocket seam | thigh ring minus the strap bands |
| Global crumple | noise(scale 90/m) − 0.5 | ±1.5 mm | ≈ 11 mm | everywhere except the knee pockets | 1 − `KneePocket` |

Implementation: one node group with the ten fields summed, each multiplied by its mask attribute and a per-zone `Float` input (so the critic loop can turn zones up/down from the command line: `--wrinkle crotch=0.8 hem=1.2`), feeding `Set Position` offset = Normal × d. Seam edges are damped ×0.3 within 4 mm (the ridge stays straight).

---

## 7. Rigging and attachment

### 7.1 Mode posed (hero)
`Trousers.Main` is parented to `Morgan.Rig` (object parent, no armature deformation) and carries a `SurfaceDeform` modifier bound to `Body.Mesh.Posed` (bind at build, `falloff 4`): if the body spec nudges the pose by a few degrees the trousers follow without re-simulation; larger pose changes require a rebuild (`--mode posed` re-runs the sim, 5 min). Attached components are Surface-Deformed to `Trousers.Main` (§4.11).

### 7.2 Mode rest (animation-ready deliverable, same script, `--mode rest`)
The tube is built around the rest body (`Body.Mesh` in A-pose: hip joints as decided by the body spec, legs straight), the sim runs 1–60 frames (settle only, shrink 0 → 0.08 on the straps), then: `DataTransfer` from `Body.Mesh` → `Trousers.Rest`, data type `VGROUP_WEIGHTS`, `vert_mapping 'POLYINTERP_NEAREST'`, all groups, applied; weights cleaned (`bpy.ops.object.vertex_group_clean` limit 0.01) and smoothed 3 iterations on the thigh/shin boundary; `Armature` modifier (`use_deform_preserve_volume True`). Bone influence table:

| Band (h) | Bones (MPFB default names; Rigify DEF- in `BONE_MAP`) | Notes |
|---|---|---|
| Waistband, pelvis to crotch | `pelvis.L/R` 70 %, `spine01` 30 % | the waistband must not follow the thighs |
| Gusset | `pelvis.L/R` 50/50 blended with `upperleg01.L/R` 20 % each | stays centred when one leg abducts |
| Thigh to the knee-pocket top | `upperleg01/02` | transferred from the body |
| Knee pocket | `upperleg02` 40 % / `lowerleg01` 60 % at the cap centre, graded ±100 mm | the cap of spec 12 is parented 30/70 the other way — keep the pocket slightly thigh-biased so it slides over the cap on flexion |
| Shin to the hem | `lowerleg01/02` | — |
| Hem rolls (lowest 120 mm) | `lowerleg02` 85 % / `foot` 15 % | rolls must not rotate with the foot |

Attached components receive the same weights by Data Transfer from `Trousers.Rest`; belt loops and the button are 100 % `pelvis`/`spine01`.

### 7.3 Collisions with neighbours at build time
Body and boots are colliders (§4.6); kneepad caps are colliders (stand-in ellipsoids if spec 12 is not built yet); the belt and straps compress through the shrink group and the Shrinkwrap bands. After the build the script runs an intersection test (`bmesh` BVH overlap between `Trousers.Main` evaluated and `Body.Collider`, `Boot.*.ShaftProxy`, `Kneepad.*.CapProxy`): any overlap > 1 mm is a failure listed in the log.

### 7.4 How the belt and the drop-leg straps compress the fabric
The fabric under the belt (h 812–859) and under the three thigh straps sits at body + 3 mm (Shrinkwrap band) while the free cloth sits at body + 14–22 mm; the sim's shrink ramp pulls the fabric into the bands so bulges form 18 mm above and below each strap (§6.3). The belt/strap specs must place their inner surfaces at body + 3.5 mm so they visibly bite into the cloth (a strap floating above the roll is the most common tell of a bad composite). The hanger strap from the belt to the right rig (reference (690–700, 505)) crosses the waistband and the hip pocket; it does not compress — it lies 1 mm proud.

---

## 8. Evaluation protocol

### 8.1 Renders
`--eval` renders V1–V8 (§1.3) at 1672 × 941 (V1–V3) and 1600 × 1200 (V4–V8), Cycles CPU 256 samples + OpenImageDenoise, AgX Medium High Contrast, to `renders/09_combat_trousers/V<n>_<name>.png`; plus flat-lit variants `V<n>_flat.png`; plus a `V1_overlay.png` (render crop and reference crop side by side with a 50 % difference blend in the middle) and `V1_edges.png` (Canny edges of render over reference in two colours). Every run also writes `eval.json` with the metrics below. The author opens every PNG with the Read tool and compares it with the named reference crop before declaring the step done (CLAUDE.md rule 3).

### 8.2 Silhouette metric
Trouser mask in the render: render a second pass with `Trousers.*` objects as holdout/ID (Cryptomatte or an emission-white override), threshold → mask M_r. Reference mask M_ref: the pre-made mask `ref/masks/trousers.png` produced by the segmentation model listed in `notes/research_ai_helpers.md` [VERIFY: research_ai_helpers], falling back to a hand-thresholded luminance/colour mask of the legs between y 475 and 810 excluding boots and kneepad caps (the script ships this fallback). IoU(M_r, M_ref) in the box (630,470)–(990,815) ≥ 0.90. Also report the width of each leg at y = 600, 700, 740, 780, 800 against §2.1 (tolerance ±6 px).

### 8.3 Hem-roll crest count
Along the vertical lines x = 730 (right leg) and x = 920 (left leg), between y 745 and 812 in the V1 render, high-pass luminance (σ 2 px), count maxima with prominence > 12 levels spaced ≥ 8 px: expected 2–3 per leg; report crest y positions against 757/775/795. Cuff edge: lowest row where the trouser mask ends at x 700–760 and 890–950: expected y 803–810.

### 8.4 Camouflage statistics
Run `ref/zoom_trousers_blotch_stats.py` logic on the V1 render windows (695–785 × 580–615), (850–930 × 580–615), (700–770 × 705–790), (880–935 × 705–790): light/dark equivalent diameters (median 15–30 mm, p75 20–40, max 40–65), local contrast 95–140 %, four k-means tones within ΔE76 < 10 of the lit targets (#141311, #2f2c29, #4d4842, #7b736c). Also check no repeat: autocorrelation of the V8 render has no secondary peak > 0.3 within 150 mm.

### 8.5 Colour patches
The 12 pixels of §5.7, 5×5 means, ±10/255.

### 8.6 Construction checks (closeups V4–V7, measured on the flat variants)
Stitch row spacing and pitch measured by the script from the `GN.Details` output directly (distance between the two instanced rows along 20 sampled seam points: 6.4 ± 0.3 mm; pitch 3.6 ± 0.2 mm) and visually confirmed in V4/V5. Ripstop pitch from V8 (FFT peak of the lit patch at 6.0 ± 0.3 mm). Bar-tack count 38. Grommets 2 per calf pocket. Belt loops 7 (count instances). Hem topstitch at 18 ± 1 mm above the edge (V5).

### 8.7 Questions the critic must answer (yes/no, with the view that proves it)
1. V3: Do the cuffs sit ON the boot collars in heavy rolls, untucked, with every lace crossing visible and no drawcord? 2. V2: Is the crotch low and shadowed with folds radiating into the inner thighs, and is the space between the thighs rendered as background (not a blue-grey cloth diamond)? 3. V1/V4: Are the knee pockets black, smoother, slightly shiny Cordura clearly distinct from the camo, with the caps inside and the pocket top seam/tucks above them? 4. V1: Does the camo read as low-contrast dark blotches with soft edges — never digital, never "leopard"? 5. V4/V7: Are seams double rows with a ridge, at the positions of §2.4 (shin seams at ±45 mm, knee-pocket perimeter, calf pocket piped)? 6. V8: Is the ripstop grid visible on crests and invisible in shadow? 7. V1–V3: Is dust only on top surfaces, grime only at the cuffs, whitening only at the gusset? 8. V2/V4: Do the straps and belt bite into the cloth with rolls above and below? 9. Flat views: any poke-through, floating stitch, z-fight, or visible texture tile? 10. Overall: heavy NYCO or thin spandex?

### 8.8 Known failure modes to check for
Hem slides into the boot (tucked look) → raise boot friction/`Hem` shrink; hem forms one big sausage instead of 2–3 rolls → lower bending to 1.5, lengthen the leg by 20 mm; cloth tunnels through the body at the buttocks/knees → `distance_min` 0.004, quality 10; "wet rag" over-wrinkling → halve the global crumple and thigh drape; smooth tube with no folds → sim did not run (check cache) or shrink ramp missing; visible camo repeat along a leg → UV_Real offsets not applied; mirrored camo between legs; camo too contrasty (tan > 12 % or T3 lighter than #5e5246); the inner-thigh gap filled with cloth (gusset too low); stitches floating (instance normal offset > 0.3 mm) or sunk; knee pocket z-fighting with the cap (pocket inner surface must be cap + 2 mm); cuffs covering the boot speed hooks (cuff edge must stay ≥ 180 mm above the floor); strap rolls present but strap floating above them; shin seams drawn vertical on the rotated right leg at the wrong projected position (check 720/745 ± 6 px).

---

## 9. Build order, effort and risks

### 9.1 Dependencies
Needs first: body (posed + rest meshes, collider, rig, Empties); pose script (`build_all.py` pose stage) so the posed body exists; kneepad cap proxies (spec 12) — stand-ins acceptable; boot shaft proxies (boot spec) — stand-ins acceptable but the final boot collar height/radius must match within 5 mm or the hem will be re-simulated; belt and strap proxies — only their heights/radii are needed (§4.2). Provides to others: the surfaces for the belt, straps, kneepad caps and the boot collar overlap (§10.1).

### 9.2 Build order inside the script (idempotent, ≈ 10 min total on 4 cores [VERIFY: research_blender_capabilities])
1. Clean `Trousers.*` (1 s). 2. Generate/load the camo tile (numpy, 4096²: ≈ 40 s first run, cached). 3. Leg axes + section table + tube (bmesh, 3 s). 4. Attributes, vertex groups, UVs, pack (10 s). 5. Colliders and stand-ins (2 s). 6. Settle sim 100 frames (2–4 min). 7. Stability check; apply; Shrinkwrap bands (5 s). 8. Modifier stack, GN groups (5 s). 9. Attached components (5 s). 10. Materials, bake masks (AO 64 spp + 4 EMIT bakes at 2K × 2 UDIM: ≈ 3 min). 11. Intersection test (10 s). 12. `--eval` renders: V1–V3 share one full-frame render (≈ 4 min at 256 spp with the whole character; ≈ 1.5 min with trousers + stand-ins only), V4–V8 ≈ 1.5 min each → ≈ 12 min; metrics 20 s. Commit after step 11 and after a passing eval (rule 7).

### 9.3 Stability checks on the sim (automatic)
Reject and fall back (§4.13) if: any vertex moves > 50 mm between frames 90 and 100; max |velocity| at frame 100 > 0.05 m/s; bounding box of the hem below h 60 or above h 330; overlap with `Body.Collider` > 1 mm on > 20 vertices; NaNs. First retry with quality 10 and `distance_min` 0.004 before falling back.

### 9.4 Estimated script size
`scripts/parts/09_combat_trousers.py` ≈ 1 400 lines; `scripts/lib/cloth_tube.py` ≈ 400 (axis, sections, tube, attributes, UVs); `scripts/lib/camo_gen.py` ≈ 150 (the prototype is 90 lines); `scripts/lib/gn_stitches.py` ≈ 350 (node-group builder for ridges, stitches, bar tacks, LOD switch); `scripts/lib/gn_wrinkles.py` ≈ 300; eval helpers ≈ 250 shared with other cloth parts (gaiter, shirt). Total ≈ 2 850 lines.

### 9.5 Risks and fallbacks

| Risk | Likelihood | Mitigation / fallback |
|---|---|---|
| Cloth sim unstable or slow with self-collision on 4 cores | medium | staged self-collision (off until frame 20), quality 8 → 10, mesh at 10 mm not finer; fallback §4.13 |
| Hem does not stack (slides or sausages) | medium | boot friction 30, rounded rim, 110 mm excess, hem bending 3.0; tune `--hem_excess`; fallback parametric rolls |
| Crotch folds too weak/strong | medium | shrink ramp 0.08–0.15; `--wrinkle crotch=` multiplier; check V6 |
| Camo not matching | low (prototype verified) | thresholds/wavelengths are command-line parameters; §8.4 metrics tell which to move |
| Texture tiling visible | low | per-panel UV offsets; anti-tiling blend for the weave |
| Render cost of geometry stitches | medium | LOD switch to shader stitches at hero distance; realize only in V4–V7 |
| Body spec changes the hip-joint height (505 vs 480) | medium | the tube reads the posed bones; only the rise table changes; crotch stays at h 763 by design |
| Boot collar height changes | medium | re-run step 6 (5 min) — the hem height is an input |
| MPFB clothes proxy (`cortu_cargo_pants.mhclo`, in the inventory) tempting as a shortcut | — | not used: wrong topology, no seams, low density; may serve as a sanity check of fit only |

---

## 10. Interfaces and open questions

### 10.1 What neighbouring parts must provide or respect
* **Body:** `Body.Mesh.Posed`, `Body.Mesh` (rest), `Body.Collider`, the rig with `BONE_MAP`-able names, Empties `Body.Empty.Crotch/Knee.R/L/Ankle.R/L`; the body's thigh circumference at h 740 must be 540–580 mm and the knee 400–420 mm (the ease table assumes it); hip joints at h 827 (fallback 880) — the trouser crotch stays at h 763 either way.
* **Kneepads (spec 12):** caps 170 × 200 mm, bulge 28 mm, centred at knee centre + 15 mm up, inside our pockets whose inner surface is cap + 2 mm; the pad's rear strap crosses our pocket at h 530–550 — strap inner surface at pocket outer + 0 mm; cap top slots visible above our pocket flap (flap top at h 649). Provide `Kneepad.R/L.CapProxy` before our sim or accept our stand-in.
* **Boots:** collar top at h 201–212, shaft Ø 140 mm, padded collar rounded ≥ 10 mm; our cuff overlaps the collar by 10–25 mm and must leave the speed hooks (h ≤ 185) exposed; boots must not add geometry above h 212 at radius > 75 mm. Provide `Boot.R/L.ShaftProxy` (with instep wedge) early.
* **Belt:** sits on `Trousers.Waistband` outer surface (body + 6.5 mm incl. the two plies) between h 812 and 859, 45 mm tall; leave 1.6 mm under it for the 7 belt loops at the positions of §3.4; the hidden buckle is behind the magazine; the hanger straps cross our waistband 1 mm proud.
* **Drop-leg rigs/straps:** right straps at h 761–795 and 651–700, left at 668–710, 33 mm tall, inner surface at body + 3.5 mm (bite into our bands); the right twin carriers sit on our lateral thigh over the cargo pocket (pocket back face deleted; carriers may touch cloth); the left block likewise.
* **Combat shirt:** tucked into the trousers (our decision) — the shirt hem ends inside at h 850; the exposed shirt band is h 890 → 1050 between our waistband and the vest hem.
* **Rifle/hands:** the handguard passes 200 mm in front of the left hip, the magazine 150 mm in front of the lower abdomen — no contact with the trousers; the muzzle is 250–350 mm in front of the left thigh.
* **Lighting/eval:** the reference camera and light rig of the lighting note are used unchanged; the WORLD-only pixel (760,730) ≈ #151517 is on OUR shin — the trousers' albedo and roughness are therefore part of the lighting calibration and must be finished before the final light calibration.

### 10.2 What this part provides
Objects `Trousers.Main` (+ attached), `Trousers.Rest` (mode rest), vertex groups listed in §4.5 (for strap/belt specs to sample compression bands), the camo tile `assets/generated/Trousers.Camo.4096.png` (reusable by nobody else — the shirt and vest are plain), the generic cloth helpers (`cloth_tube`, `gn_stitches`, `gn_wrinkles`) for the gaiter and shirt specs, and the measurement script for camo statistics.

### 10.3 Open questions for the client
1. **Camouflage identity:** our own CC0-safe 4-tone pattern in the MultiCam Black family (recommended, verified statistically against the reference) — or an attempt to reproduce the real MultiCam Black / A-TACS LE print, which are proprietary designs?
2. **Hem:** follow the picture (plain loose hem, no drawcord) or add the real G3's internal drawcord and keep it hidden inside the stack?
3. **Shirt tucked** (our reading of the lighter waistband band at y 475–490) or untucked over the waistband?
4. **Cargo pockets** under the drop-leg rigs: model (default, low-poly, invisible in the hero view) or omit?
5. **Calf-pocket hardware:** two 5 mm grommets with a shock-cord keeper (our reading of the dots at (947,724)/(948,729)) or plain hook-and-loop with no hardware?
6. **Thread colour:** black (recommended for a black-family camo) or coyote brown for a visible contrast in closeups?
7. **Hip-joint height:** the body decision (505 vs 480) changes the trouser rise only; confirm the trousers may keep the crotch at h 763 in both cases.
8. **Dust level:** the lit right thigh highlights (#857061 p95) imply a visible dust film; keep at the reference level or clean the garment slightly for a "fresh issue" look?
