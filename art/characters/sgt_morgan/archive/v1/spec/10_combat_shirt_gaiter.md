# Part 10 — Combat shirt and neck gaiter (Crye G3-class combat shirt with rib-knit shoulder panels; Polartec-class fleece neck gaiter pushed into rolls)

Status: draft 1 (spec writer), 2026-10-07, written under the **reality wins** rule (CLAUDE.md, Source of truth). Owner script: `scripts/parts/10_combat_shirt_gaiter.py` (plus the shared `scripts/lib/cloth_tube.py`, `gn_stitches.py`, `gn_wrinkles.py` from spec 09, `scripts/lib/materials.py`, `scripts/lib/measure.py`). Object prefixes `Shirt.*`, `Gaiter.*`; collection `Part10.ShirtGaiter`.

Convention reminder (CLAUDE.md rules 1 and 2): every left/right below is the **soldier's own**; "viewer's left/right" is written out when the picture is meant. Spec units are **mm**; Blender units are metres. World frame W: origin on the floor midway between the feet, +Z up, the character faces −Y, the camera is on −Y, **+X = his LEFT = viewer's right**. Reference pixels are full-image coordinates of `ref/reference_full.png` (1672 × 941); scale at the figure's depth **1 px = 2.12 mm**; posed height above the floor h = (895 − y) × 2.12 mm; lateral X = (x − 830) × 2.12 mm. Arm stations use spec 05's frame: **s %** along the humerus from the glenohumeral (GH) centre (humerus 340 mm) or along the forearm from the elbow axis (270 mm), and a **clock** position in the anatomical position (12 anterior, 3 lateral, 6 posterior, 9 medial). Body heights are spec 04's (REST unless "posed").

Sources: `notes/analysis_consolidated.md` §1, §2, §4, §5, §6, §9 (authoritative); `notes/analysis_gear_inventory.md` §2.2, §3, §4–§7; `notes/analysis_pose_proportions.md` §2, §4, §6; `notes/analysis_face_grooming.md` §4 (neck, jaw shadow); `notes/research_dimensions.md` §1 (ANSUR II "Tight" column), §4–§5 (NYCO, Crye G3 shirt), §9 (gaiter); `notes/research_assets.md` (texture sets `cotton_jersey`, `knitted_fleece`, `denim_fabric_05`, `Fabric082A`); `notes/research_blender_capabilities.md` §2 (cloth), §3 (hair), §4 (adaptive displacement), §6 (modifier stack), §10 (probes), Recommendations; `notes/research_prototypes.md` §0 (sheen bleaches dark fabric), §1 and §8 (stitch recipes); `spec/04_torso_neck.md` §2.2, §3.2–§3.6, §4.9, §4.12, §10 (rings, anchors, stand-ins, the dressed silhouette rows); `spec/05_arm_hand.md` §2.1, §3.1–§3.3, §4.9 (girths, `Arm.*.CuffRing`, `Arm.*.SleeveCollider`); `spec/09_combat_trousers.md` §4.7, §10.1 (sim parameters, the tucked shirt). Own zooms made for this spec with PIL (gridded ×6–×10 Lanczos, full-image coordinates on the grid lines): `ref/zoom_gaiter_rolls_x8.png` (740–870 × 120–210), `ref/zoom_shirt_yoke_right_x10.png` (680–750 × 185–250), `ref/zoom_shirt_yoke_left_x10.png` (870–940 × 245–305), `ref/zoom_shirt_lsleeve_seam_x8.png` (900–975 × 250–345), `ref/zoom_shirt_lsleeve_ripstop_x8.png` (880–950 × 295–375), `ref/zoom_shirt_waistband_x6.png` (735–900 × 390–485), `ref/zoom_shirt_rforearm_inner_x8.png` (680–760 × 300–360), `ref/zoom_shirt_rupper_sleeve_x6.png` (640–720 × 230–330), `ref/zoom_shirt_lelbow_x8.png` (925–975 × 315–375); the measuring script is in the session scratchpad and is reproduced by `scripts/eval/measure_gaiter_rolls.py` (§8.3).

---

## 1. Purpose and acceptance

### 1.1 What this part is
Two garments. **The combat shirt**: the dark long-sleeve base layer worn under everything — a close-fitting flame-resistant knit torso tucked into the trousers (hem inside at h 850), a zipped mandarin collar entirely under the gaiter, rib-knit shoulder panels that wrap each shoulder and the upper arm down to a horizontal seam just above the elbow, NYCO ripstop lower sleeves with elbow-pad pockets and hook-and-loop cuffs that end inside the glove gauntlets; every seam, hem, coverstitch, bar tack, the zip and its placket, the knit and ripstop micro-structure, the drape folds, the compression under the carrier, straps, pauldron bands and forearm guards, and the weathering. **The neck gaiter**: a polyester fleece tube pushed down the neck into a tilted stack of three rolls and a flat band that fills the carrier's collar opening, sits over the shirt collar and under both shoulder straps, with its side seam, two hems, fibre nap, pilling and dust. **Not** in this part: the body (specs 03–05), the plate carrier and shoulder straps (spec 13), the pauldrons, elbow cap and forearm guards (spec 12), the gloves (spec 11), the trousers (spec 09). This part must, however, give those parts the surfaces they press on and must react to them (§4.9, §7).

### 1.2 What "perfect" looks like
At the hero distance (46 mm lens at 4.5 m) the shirt reads as a dark warm-grey (#332f2d median) knit that hugs the trunk and bloused slightly above the waistband, with shoulders that read *ribbed* under the pauldrons, upper sleeves bitten by the tan bicep bands, lower sleeves of matte ripstop folding at the elbows and pinched by the forearm-guard straps, cuffs vanishing into the glove gauntlets without a gap; the gaiter reads as a soft, fuzzy, dusty olive-brown fleece in three fat rolls, the top roll turned down and resting against the jaw shadow on his right, the stack higher at the back-left with a vertical pleat descending there, the straps crossing its lowest roll. In a 250 mm-wide closeup every rib of the shoulder panel is a 4.2 mm wale with a 0.6 mm valley, every knit stitch of the torso a 1.0 × 0.8 mm loop, the ripstop a 6.35 mm lattice of 0.4 mm yarns catching the key on fold crests, every seam a double row of black stitches with a visible flat-felled ridge, the elbow pocket's top seam with its hook-and-loop closure, the cuff tab's stitch box, and the gaiter's rolls a true bellows with a 9 mm fold radius on the turned-down top hem, a flatlock side seam at the back-left, 12 mm coverstitched hems, a 1–2 mm fibre nap that glows on the rim-lit edges and pills on the top roll, dust only on up-facing fleece and on the shoulder ribs, sweat-darkening only where the gaiter meets the carrier.

### 1.3 Evaluation render views (rendered by `scripts/parts/10_combat_shirt_gaiter.py --eval`, written to `renders/10_combat_shirt_gaiter/`)

| View | Camera position (m, W) | Target (m) | Lens | Compared with | What it proves |
|---|---|---|---|---|---|
| V1 `torso_ref` | hero camera (0.00, −4.50, 0.60), rot (93.9°, 0, 0) | — | 46 mm | `ref/crop_torso_vest.png` = ×3 of (630,140)–(990,490); render full frame, crop the same box, upscale ×3 Lanczos | sleeves, shoulder panels, exposed band, gaiter in context with the carrier/pauldron stand-ins |
| V2 `gaiter_ref` | hero camera | — | 46 mm | `ref/crop_head_face.png` = ×5 of (715,30)–(885,200) (its lower 40 %); `ref/zoom_gaiter_rolls_x8.png` = ×8 of (740,120)–(870,210) | top-edge saddle, roll count and rows, crevice shadows, strap crossing, left pleat |
| V3 `arm_R_ref` | hero camera | — | 46 mm | `ref/crop_arm_right_viewerleft.png` = ×3 of (600,170)–(770,490) | right shoulder ribs under the pauldron, band bite, sleeve between band and guard, cuff under the guard's wrist band |
| V4 `arm_L_ref` | hero camera | — | 46 mm | `ref/crop_arm_left_viewerright.png` = ×3 of (850,170)–(1000,490) | left ribs between tiers 2–3, the back-seam ridge (925→955, 260→330), elbow bunch, ripstop lower sleeve, cuff into the gauntlet |
| V5 `gaiter_close` | (−0.30, −0.78, 1.66) | (0.00, −0.09, 1.53) | 85 mm, f/5.6 on the top roll | `zoom_gaiter_rolls_x8.png`, `zoom_torso_neck_gaiter_x8.png` | bellows profile, fold radii, hem coverstitch, side seam, nap, pilling, dust |
| V6 `shoulder_R_close` | (−0.78, −0.62, 1.74) | (−0.29, −0.04, 1.46) | 85 mm | `zoom_shirt_yoke_right_x10.png`, `zoom_torso_rtrap_strap_x8.png` | rib wales 4.2 mm, panel seams, strap compression, armscye coverstitch (pauldron stand-in toggled off for the "flat" variant) |
| V7 `elbow_L_close` | (0.96, −0.58, 1.22) | (0.31, −0.06, 1.16) | 85 mm | `zoom_shirt_lsleeve_seam_x8.png`, `zoom_shirt_lsleeve_ripstop_x8.png`, `zoom_shirt_lelbow_x8.png` | back-seam ridge, panel/ripstop junction seam, elbow pocket top seam and closure, elbow compression folds, ripstop lattice, cuff tab, guard-strap pinch |
| V8 `knit_macro` | (0.12, −0.42, 0.98) | (−0.02, −0.14, 0.96) | 100 mm, f/8 | own tile renders (§5.2) and `zoom_shirt_waistband_x6.png` | jersey loops, coverstitch hem, blousing fold above the waistband, dust/sheen behaviour |

Lighting for all views: the KEY/COOL/WORLD rig of `analysis_lighting_camera_scene.md` §6.2 (KEY area 1.5 m at (−1.70, −2.00, 3.60) 4500 K 800 W; COOL area 3.0 m at (3.20, 0.60, 3.60) (0.55, 0.76, 1.00) 600 W; WORLD 0.05–0.10), AgX "Medium High Contrast", exposure 0; V5–V8 additionally render a "flat" variant (world grey 0.18, no key, Workbench matcap + cavity for geometry inspection, ≈ 5 s each).

### 1.4 Pass criteria (scored by the critic, each 0–2; the part passes at ≥ 24/30 with no zero)
1. **Garment-edge rows (V1, V2)**: gaiter top edge at the front centre (x 790–810) y 152–156, at his right side (x 755) y 139–146, at his left-front (x 825) y 136–143, at the back-left (x 845–850) y 124–130; crevice rows at x 800: 164–166, 177–179, 187–189; the straps cross the gaiter from y 160 ± 3; the shirt's exposed band between y 398 and 475 with no skin or body showing; all within 3 px.
2. **Roll count and profile (V2, V5, §8.3)**: exactly three outward lobes plus one flat band between the top edge and the carrier top at every column 760 ≤ x ≤ 820; lobe heights 42 ± 6 / 28 ± 5 / 20 ± 4 mm measured on the flat variant of V5; the top roll is a turned-down double layer with a fold radius 8–10 mm; the vertical pleat on his left present between x 835 and 850, 12–16 mm wide.
3. **Silhouette (V1, V3, V4)**: the dressed silhouette rows of spec 04 §2.2 (y 160: 627–910; y 200: 624–944; y 260: 627–949; y 300: 632–955; y 400: 649–930) reproduced within 4 px with the stand-ins; the sleeve silhouette between the pauldron band and the forearm guard within 3 px of the arm crops; glove-cuff/sleeve junction shows no gap (no skin pixel) on either wrist.
4. **Shoulder ribs (V3, V6)**: wales 4.2 ± 0.3 mm pitch, 0.5–0.7 mm relief, running from the collar seam over the shoulder and down the deltoid; visible as texture in V3 at (690–740, 195–245) (high-pass 3 × 3 energy 4–7 lum units, reference 5.1); no ribs anywhere below the panel seam.
5. **Ripstop lattice (V7)**: 6.35 ± 0.2 mm grid, 0.4 mm yarns, oriented along the sleeve axis, 0.06–0.10 mm bump; no visible tile repeat along one sleeve.
6. **Seams and stitches (V6, V7, V8)**: flat-felled seams 7.0 ± 0.5 mm wide, 1.2 ± 0.2 mm proud, two needle rows 6.4 ± 0.4 mm apart at 3.6 ± 0.3 mm pitch on the ripstop; coverstitch rows 5.6 ± 0.4 mm apart at 2.5 ± 0.3 mm pitch on the knits and on the gaiter hems; bar tacks at the elbow pocket corners and the cuff tabs; no floating stitch (every thread cylinder sunk 0.15 mm into cloth).
7. **Colour patches (§8.5)**: 14 named pixels within ±10/255 per channel of the reference after the lighting calibration; the gaiter's lit-fold-to-crevice ratio (760,155)/(835,160) ≥ 12 : 1 in luminance; the knit's crest sheen never exceeds lum 130 anywhere in V1.
8. **Fibre and surface (V5, V8)**: the gaiter's rim-lit edge (850,140) shows a soft 1–2 mm bright fringe (nap), no hard edge; pilling dots 1–2 mm present on the top roll only; the knit reads matte with a soft specular (roughness 0.75–0.85), the ripstop slightly crisper (0.65–0.72).
9. **Weathering placement**: dust only where n·Z > 0.3 (top roll's upper face, shoulder ribs' top faces, cuff tops); sweat band only within 15 mm above the carrier top on the gaiter and 10 mm of the collar seam; abrasion lightening only in 5 mm rings at the hard-part edges (bands, guard bands, cap seats); no uniform dirt wash.
10. **No intersection** with the body, carrier, straps, pauldrons, guards, gloves, trousers or gaiter/shirt with each other in any view (flat variants); the gaiter's inner surface clears the neck by 1–5 mm everywhere except the seat; critic's free judgement "would a Crye wearer recognise the shirt, would anyone recognise a fleece gaiter?" (0–2).
Criteria 1, 2, 3 and 10 may not score 0.

---

## 2. Reference observations

### 2.1 Extents (measured on `reference_full.png`, own 5 × 5 means and luminance profiles unless credited)

| Feature | Pixels (x, y) | World (mm, posed) | Note |
|---|---|---|---|
| Gaiter visible span | x 745–855, y 125–192 | X −180…+53, h 1632–1490 | consolidated §4 says y 128–200; 200 is the strap/carrier crossing, the fabric continues under them |
| Gaiter top edge, front centre | (790–810, 152–156) | h 1569 | luminance at x 800 drops 96 → 60 between y 153 and 157 (`col 800` profile); above it is lit neck skin, not fleece (spec 04 §2.2 confirms lit skin to y 154) |
| Gaiter top edge, his right side | (752–762, 139–147) | h 1586 | x 775 column: skin 150–160 lum to y 146, 113 at 148, 82 at 150 → edge y 147 |
| Gaiter top edge, his left-front | (820–830, 136–143) | h 1600 | x 825: shadow skin to y 134, fleece from y ≈ 140 |
| Gaiter top edge, back-left | (840–852, 124–130) | h 1632 | x 845: lit rim at y 125–126 (lum 74–98) — the stack rides up 60 mm at the back-left |
| Roll 1 (top roll), lit face | right: y 148–162 (crest ≈ 158–160); centre: shadowed under-face y 156–165 | lobe 42 mm tall on the right | x 775: lum 93–106 at y 158–162 |
| Crevice 1 | x 775: y 170; x 800: y 165; x 825: y 157 | — | lum 12–15 at x 800, 15 at x 775, 19 at x 825: the fold line rises 13 px toward his left over 50 px (≈ 15° tilt) |
| Roll 2 | x 775: lit 173–177 (crest 176); x 800: lit 167–172 (crest 170) | lobe 28 mm | lum 84–102 at the crests |
| Crevice 2 | x 775: 180–181; x 800: 177–178; x 825: 171–174 | — | lum 3–10 at x 800 (the deepest shadow on the figure's upper half after the under-jaw) |
| Roll 3 | x 775: crest 185–186; x 800: 181–184 (lum 29, in the chin/strap shadow) | lobe 20 mm | — |
| Crevice 3 / flat band | x 775: 188–189 then band 190–193; x 800: 188 then band 189–191 | band 6–8 mm | carrier top at y 192 (x 800) / strap at y 194 (x 775) |
| Vertical pleat, his left | x 835–850, y 128 → 186, leaning ≈ 10° (top further left) | 12–16 mm wide, 6–9 mm deep | x 845 profile alternates 18/42/17/81 lum between y 145 and 165: a shaded groove beside lit fabric |
| Right shoulder strap crossing | x 725–760 from y 160 | — | the strap lies over rolls 2–3 and the band on his right; left strap x 822–858 from y 160 with the elastic keeper (805–830, 150–175) over roll 1's left end |
| Shirt shoulder panel, right | ribbed texture at (690–740, 195–245) | h 1484–1376 = s 2–34 % of the right humerus | under and below the tier-1 cap; fine vertical texture; broad diagonal drape ridges 5–6 px (≈ 12 mm) apart (`zoom_shirt_yoke_right_x10.png`) |
| Shirt shoulder panel, left | ribbed texture at (880–930, 255–300) | h 1357–1261 = s 39–67 % | between tier 2 and tier 3; smooth luminance gradient 7 → 94 across x 880–935 (cool-lit), no resolvable period |
| Back-seam ridge, left sleeve | from (925,260) to (955,330) | h 1346 → 1198 = s 42 → 86 %; ridge rim lit cool #74879a at (945,300) | a raised line with fabric pulling across it; rows 295/310/325 show crest luminance 86–135 on a 2–3 px wide line |
| Ripstop "diagonal micro-weave", left sleeve | (885–945, 300–370) per the analysts | — | **not resolvable at 2.12 mm/px** (a 6.35 mm grid is 3 px); the analysts saw it on a ×3 crop at ×5 → interpolation texture. Kept as a reality fact, not an image fact |
| Left elbow bunch | (935–965, 320–360) | h 1219–1134 | 3–4 compression folds under and around the lateral elbow cap (950–968, 335–365) |
| Right upper sleeve between tier 3 and the guard | (640–700, 285–330) | — | dark (#242222 / #2a2323), diagonal folds running down toward the inner elbow (`zoom_shirt_rupper_sleeve_x6.png`) |
| Right cuff / glove junction | (700–712, 333–345) | — | #41362f: the ripstop cuff disappearing under the guard's wrist band; no skin |
| Left cuff / glove junction | (865–885, 410–440) | — | neoprene gauntlet #444d5e; the sleeve enters it; 60 mm of gauntlet shows between glove and guard |
| Exposed shirt band | x 745–890, y 398–475 | h 1053 → 890 | **mostly occluded**: the rifle magazine (725–775 × 405–458), the receiver and the left glove (803–882 × 420–497) cover most of it; true shirt pixels: (790–800, 400–420), (855–890, 398–420), (745–760, 460–475) |
| Waistband top (spec 09) | y ≈ 475 | h 890 | the shirt is tucked (spec 09 §2.4) |

### 2.2 Colour samples (own 5 × 5 means, lit as rendered; the consolidated point samples in brackets where they differ)

| Area | px | Hex | Reading |
|---|---|---|---|
| Gaiter box median (750–850 × 135–195) | — | **#373029** (mean #443931) | the matte base in mixed light |
| Gaiter roll 1, lit face, his right | (760,155) | #7e6d62 | brightest fleece; key-lit upper face |
| Gaiter roll 2, lit, right | (760,170) | #5c5048 (#74675e point) | — |
| Gaiter roll 2 crest, centre | (800,170) | #524a41 | — |
| Gaiter band under the carrier edge | (815,195) | #685846 (#6c5946) | lit by the key through the collar opening |
| Gaiter band, centre, shadow | (800,190) | #29211a | — |
| Gaiter crevice 2 | (835,160) | #060705 | the darkest fabric pixel; (815,165) #0a0704 consolidated |
| Gaiter roll 3 right | (780,185) | #3c342b | half shadow |
| Gaiter top edge, back-left, cool rim | (850,140) | #4e565c | the cool side light wraps the nap |
| Gaiter under the chin | (820,135) | #1d1410 | fleece in the chin's shadow |
| "Warm top highlight" (790,140) #6d4e39 of the gear note | (790,140) | #6d4e39 | **this is neck skin in the shadow's penumbra, not fleece** (edge at y 152–156); dropped as a gaiter target |
| Shirt, left sleeve box median (885–925 × 300–370) | — | **#332f2d** | the reference "median" of the shirt (cool-lit side) |
| Shirt right panel under the cap | (700,210) | #473d3b | key-lit rib panel; the gear note's #49433e box (695–730, 275–310) is partly the tier-3 band |
| Shirt right upper sleeve lit / shadow | (690,280) / (660,300) | #242222 / #292323 | — |
| Shirt right panel deep shadow | (705,300) | #060503 | under the stock |
| Shirt left panel, cool-lit | (905,270) / (915,285) / (925,295) | #595047 / #403b34 / #504d4a | between tiers 2 and 3 |
| Shirt left back-seam rim | (945,300) | #74879b | cool rim on the ridge crest; (930,300) #675d58 beside it |
| Shirt left lower sleeve | (910,330) / (900,350) / (920,345) | #241f1e / #48423e / #3b3a3b | ripstop, folds |
| Shirt left elbow bunch | (950,345) | #21262c | — |
| Shirt right cuff at the guard | (700,335) | #41362f | — |
| Exposed band, true shirt pixels | (795,410) / (870,405) / (750,468) | #3a3532 / #29292c / #06080a | the band is dark; "(760,450) #5d574e" of spec 04 is the magazine body |
| Exposed band, above the belt | (800,485) | #1c1b19 | shirt in the magazine's shadow |

### 2.3 Construction cues, and what I decided where the image is ambiguous or contradicts reality

Every decision below follows the precedence of CLAUDE.md (real product and its published dimensions → the image where plausible and identity-carrying → the analysts' resolutions).

| # | Issue | Image says | Reality says | Decision |
|---|---|---|---|---|
| D1 | Gaiter top edge "y 128" and "top roll touches the jaw shadow at y ≈ 130" (gear §2.2, consolidated §4) | one row for the whole top | a tube pushed down a turned head sits lower at the front (chin, gravity) and higher at the back; the measured edge is a saddle: 155 front, 147 right, 140 left-front, 125 back-left | **Saddle top ring** (§3.3), matching spec 04's `Torso.Ring.Gaiter.Top` (1574 / 1583 / 1625) within 5 mm; the roll touches the jaw shadow only at the back-left |
| D2 | Gaiter extent "y 128–200" | fabric ends at 200 | the carrier and straps cover it; the fleece continues to its seat on the clavicles/trapezius | model the full tube to the seat ring (front 1487, side 1512, back 1540 rest) |
| D3 | Gaiter material "fleece or jersey", Buff-type tube 530 × 225 in `research_dimensions` §9 | broad soft rolls, no sheen, pilling | a 530 mm microfibre Buff folds into many thin crinkles, never three fat rolls; a 280 mm, 3 mm polyester fleece gaiter (US-issue "Neck Gaiter, Fleece" / Polartec 200 class) buckles into exactly this bellows (wavelength ≈ 3.4 √(R t) ≈ 50 mm for R 75, t 3) | **fleece gaiter 280 × 460 circumference × 3.0 thick** (§3.3); the Buff dimension is rejected |
| D4 | Shirt identity | "soft knit torso, ripstop sleeves, ribbed/quilted shoulder yoke" | Crye G3 Combat Shirt: FR knit torso, NYCO sleeves, zip mandarin collar, bicep pockets, elbow-pad pockets, hook-and-loop cuffs; **its shoulders are NYCO, it has no rib panel** | G3 construction and the ANSUR/Crye size dimensions are the source of truth for everything the image does not show (collar, zip, placket, cuffs, elbow pockets, seam types). The **rib-knit shoulder panel is kept** (physically plausible: 2 × 2 rib shoulder panels exist on several combat shirts [VERIFY: name one in the critique pass]; it carries identity on both shoulders). Recorded as "image wins, plausible" |
| D5 | Where the rib panel ends | ribs visible at s 2–34 % (right) and s 39–67 % (left); ripstop folds below tier 3 | a panel seam must be horizontal around the arm | **panel seam at s 62 % (210 mm below the acromion)**, hidden under the tier-3 bands on both arms; ripstop below it |
| D6 | G3 bicep pockets (130 × 150 loop field with pen pocket) | plain ribbed surface between tiers 2 and 3 where the pocket would be | the G3 has them | **omitted** (a loop-field pocket on a rib-knit panel is not a real construction and the image shows none); client question §10.3 |
| D7 | "Raised seam down the outside of the left upper arm" | diagonal ridge (925,260)→(955,330) | a two-piece sleeve's **back seam** runs from the posterior armscye to the lateral elbow; with the left arm internally rotated 20° and seen from the front-left it projects on the lateral silhouette exactly there | the ridge **is the back seam** (flat-felled on the ripstop, coverstitched on the rib panel), continuous through the panel seam; its visible pull is the tier-3 band's compression (§6.3) |
| D8 | "Ripstop micro-grid visible on the left sleeve" | diagonal texture at ×5 of a ×3 crop | unresolvable at 3 px per cell | ripstop grid 6.35 mm along the sleeve axis as a reality fact; the sleeve's 45° angle in the image makes any grid read diagonal |
| D9 | "Another seam along the inner right forearm beside the forearm guard" (gear §3) | a light line at (700–712, 333–345) | that is the cuff hem meeting the guard's wrist band | **cuff hem + hook-and-loop tab**, not an extra seam |
| D10 | Exposed shirt band colour "#5d574e lit right (760,450)" (spec 04) | — | (760,450) is on the rifle magazine (consolidated dispute #7: magazine x 725–775 at y 430–458) | shirt band targets re-sampled (§2.2); the knit's lit colour is calibrated on the right shoulder panel and the left sleeve |
| D11 | Shoulder-panel "quilted" vs "ribbed" | fine vertical texture plus 12 mm diagonal ridges | quilting makes square or diamond cells, not parallel wales; the 12 mm ridges follow the drape direction, not a quilt grid | **2 × 2 rib knit, 4.2 mm wale pitch, no foam**; the 12 mm ridges are drape folds from the strap/cap pull (§6.3) |
| D12 | Elbow pads | external grey two-piece cap on the left lateral elbow (spec 12) | the G3's elbow-pad pocket is internal (for AirFlex pads) | **pocket modelled, empty**; the external cap sits on the pocket's outer face; client question §10.3 |
| D13 | Shirt hem | lighter band at y 475–490 | G3 shirts are worn tucked under a belt and carrier | **tucked**, hem at h 850 inside the trousers (spec 09 §10.1) |
| D14 | Neck length 133 mm as drawn vs ANSUR 105 (spec 04 D4) | long neck | — | the gaiter is built to spec 04's rings; if the critique pass shortens the neck, only the seat ring moves (the saddle top ring stays, §10.3) |
| D15 | Short thighs / drawn hip height (consolidated §1) | — | ANSUR segment lengths (CLAUDE.md rule 3) | affects this part only through the waistband height h 890 (unchanged in spec 09); noted for completeness — overruling the "as drawn" thighs changes nothing here |

### 2.4 Pose-dependent facts the garments must reproduce
* Head yaw +20° to his left (neck carries ≈ 12°): the gaiter's stack is compressed at the front-right (chin side) and stretched open at the back-left — hence the saddle and the left pleat. The right SCM is taut under the top roll.
* The carrier top (h 1470 at Y −118) and the straps (73 mm wide, inner surface body + 6 with the shirt under) press rolls 2–3 and the band flat on both sides from y 160 down; between the straps (x 760–822) the stack hangs free to the carrier edge.
* Right arm: shoulder flex −8 / abd +20 / int-rot +45, elbow 97°, pronation 70°. The sleeve compresses at the anterior elbow (inner) into 4–5 folds, stretches over the olecranon, and is pinched at s 58–83 % by the tier-3 band and at the forearm by the guard's elbow-end and wrist bands.
* Left arm: flex +12 / abd +8 / int-rot +20, elbow 55°, pronation 40°. Fewer, longer folds; the back seam shows on the lateral silhouette; the elbow bunch is 3–4 folds beside the lateral cap.
* Torso: pelvis yaw −10°, chest −5°, 3° extension: the knit's blousing above the waistband is deeper on his right-front (the chest leans back), and the carrier's hem shadow falls on it.

---

## 3. Real-world reference

Status tags: **M** measured on the reference, **S** sourced (`research_dimensions.md`, product pages), **E** estimated from pattern practice and the sourced body (flag [VERIFY] where a product sheet would settle it).

### 3.1 The combat shirt — identity and components (Crye Precision G3 Combat Shirt, size MD/LG Long, chest 1029–1067 band → S; our body chest 1100 rest incl. the V-taper → MD-Long with a snug fit)

| Component | Material | Thickness (mm) | Construction | Tag |
|---|---|---|---|---|
| Torso (front, back, side panels) | FR wicking jersey knit (DRIFIRE-class, 60/40 modacrylic/FR rayon), ≈ 200 g/m² | **1.0** (0.9–1.1) | single jersey, 28-gauge: wale pitch **1.0**, course pitch **0.8**; coverstitched seams | S (fabric) / E (gauge) |
| Collar | same knit, two plies with a 0.3 mm interfacing | 2.3 | mandarin stand collar **55** tall, 12 mm topstitch, zipped to the top | E |
| Front zip + placket | #5 coil zip, black, 180 long, tape 2 × 13 wide, chain 6 wide, slider 25 × 12 × 6; inner placket 30 wide knit, 2 plies | zip 2.5 (chain), placket 2.0 | zip from the collar top (h 1592 rest) down to h 1412; placket behind | E [VERIFY: G3 zip length] |
| Shoulder/upper-arm panels (L, R) | 2 × 2 rib knit, same FR yarn, ≈ 320 g/m² | **2.2** (rib relief 0.6 on top) | wales **4.2** pitch (two knit, two purl; each wale 1.05 wide), courses 1.1; runs collar → down the deltoid; coverstitched to the torso and to the ripstop | image + E (D4, D11) |
| Lower sleeves (L, R) | 50/50 NYCO ripstop 224 g/m², MIL-DTL-44436 class 10 | **0.45** | two-piece sleeve (upper/back seam, under seam), flat-felled; ripstop grid **6.35** with 0.4 mm doubled yarns; weave 32 × 30 threads/cm | S (fabric, grid class) / E (threads) |
| Elbow-pad pocket (L, R) | NYCO outer + knit inner | 0.45 + 1.0 | pocket **200 tall × 150 wide**, top opening with a 25 mm hook-and-loop strip, bar-tacked corners; centred 10 mm below the elbow axis, over the olecranon | E (research_dimensions "~200 × 150" [uncited]) |
| Cuff (L, R) | NYCO, 2 plies + 1 ply facing | 1.4 at the hem | hemmed cuff **215** circumference, 30 tall band, **hook-and-loop tab** 25 wide × 60 long on the ulnar side closing to 200; bar tacks at the tab root | S (G3 "adjustable cuffs") / E (dims) |
| Hem | knit, 20 mm turned hem, coverstitched | 2.0 | **1000** circumference at h 850 (tucked) | E |
| Thread | black polyester core-spun Tex 40 (needle Ø 0.3) on the ripstop; Tex 27 (Ø 0.25) wooly nylon on the knits | — | — | E (spec 09 chose black) |
| Labels | one 40 × 25 woven label inside the collar back; 20 × 15 care label at the left hem | 0.3 | hidden; LOD 2 only | E |

### 3.2 Shirt pattern — finished dimensions for THIS body (rest pose, spec 04/05 girths; ease E)

| Measure | Body (mm) | Ease | Garment (mm) | Where measured |
|---|---|---|---|---|
| Chest circumference | 1100 (h 1360) | +40 | **1140** | `slice_measure(1360)` of `Shirt.Torso` |
| Underbust / 10th rib | 960 (h 1189) | +50 | 1010 | — |
| Waist | 880 (h 1060) | +60 | **940** | the knit blouses here |
| Hem (tucked) | — | — | 1000 at h 850 | inside the trousers |
| Back length, collar seam (C7, 1592) → hem (850) | — | — | **742** | + collar 55 = 797 to the collar top |
| Shoulder (collar seam → sleeve head seam over the acromion) | biacromial 515 → half 257 minus the collar half-width 70 | +0 | 187 along the surface | the rib panel owns this length |
| Armscye circumference | — | — | **520** (E; = 0.47 × chest) | the rib panel is sewn into it |
| Rib panel lower seam (circumference around the upper arm at s 62 %) | bare 350–360 (spec 05 s 30–40 %) → 345 at s 62 % | +45 | **390** | hidden under the tier-3 band |
| Lower sleeve at the elbow (s 100 %) | 300 (E, from spec 05 §3.2 table) | +60 | **360** | pocket zone |
| Forearm max (forearm s 25 %) | 310 (flexed 305 S) | +40 | **350** | — |
| Forearm at the guard's wrist band (s 90 %) | 200 (E) | +25 | 225 | — |
| Cuff | wrist 179 (S) | +36 → tab closes to +21 | **215 → 200** | `Arm.*.CuffRing` is 185 at wrist −30 (spec 05): the cuff sits 15 mm proud of it, inside the gauntlet |
| Sleeve length, shoulder point → cuff edge (outseam) | sleeve outseam 623 (S, ANSUR Tight) | — | **625** | the cuff ends 25 mm beyond the wrist axis, inside the 30 mm gauntlet |
| Sleeve length, spine → wrist | 928 (S) | — | 930 check | — |
| Elbow pocket top seam | — | — | humerus **s 82 %** (60 above the elbow axis) | pocket bottom 140 below the axis (forearm s 52 %) |
| Rib panel seam | — | — | humerus **s 62 %** | 210 below the acromion |
| Back seam path | — | — | posterior armscye (clock 6 at the sleeve head) → clock 5 at s 50 % → lateral olecranon (clock 4 at s 100 %) → ulnar wrist (clock 7–8 at the cuff) | the ridge of D7 |
| Under seam path | — | — | anterior armscye low point (clock 9–10) → medial elbow (clock 9) → radial wrist (clock 2–3) | hidden |

### 3.3 The neck gaiter — identity and components (polyester fleece neck gaiter, US-issue "Neck Gaiter, Fleece" / Polartec 200 class; dimensions E, bracketed by the products of that class [VERIFY: a published spec sheet])

| Component | Dimension (mm) | Material / construction | Tag |
|---|---|---|---|
| Tube, flat | **280 long × 230 wide** (circumference **460**, rest) | double-face polyester microfleece 200–230 g/m², 4-way stretch ≥ 40 %; brushed nap both faces | E |
| Wall thickness | **3.0** (2.5–3.5) | fibre pile ≈ 1.0 each face over a 1.0 knit core | E |
| Side seam | one, flatlock (6 mm wide, 2 needle rows 4.8 apart, looper web between), running the full 280 | placed at the back-left (clock position 5 o'clock seen from above, i.e. X +70, Y +60 at the neck) where the pleat forms | E |
| Top and bottom hems | **12** turned once, coverstitched: two needle rows 5.6 apart, pitch 2.5 | the top hem is the outer edge of roll 1 after it is turned down | E |
| Label | 25 × 15 woven, inside at the bottom hem beside the seam | hidden | E |
| Nap | fibres 15–20 µm, pile 1.0–1.5 mm, ≈ 150–250 fibre tips/mm² | renders as a soft rim fringe and velvety sheen | E |
| Pilling | balls 1–2 mm Ø, 0.3–0.5 proud, density 1 per 40 mm² on the top roll's outer face, 1 per 400 mm² elsewhere | from chin stubble abrasion and washing | E |

### 3.4 Gaiter — as worn (posed geometry; REST rings from spec 04 §4.9; M where a pixel row is cited)

| Quantity | Value (mm) | Source |
|---|---|---|
| Seat ring (bottom hem) | `Torso.Ring.NeckBase` 20 mm down: front **1487**, sides 1512, back **1540** (rest); girth there 470 (neck base 460 + collar 2 × 2.3 + 5 air) | spec 04 §10 |
| Top ring (saddle) | front centre **1569** (y 155), right side **1586** (y 147), left-front 1600 (y 140), back-left **1632** (y 125); spec 04's 1574/1583/1625 lie within 5–7 mm | M |
| Stack height, top edge → seat | front 82, right 86, back-left 92 | derived |
| Roll 1 (turned-down top hem, double layer) | lobe height **42** (centre 36 where the chin pushes it), proud **22** beyond the stack's mean wall, fold radius **9** at the top, hem edge inside at the lobe's bottom | M (y 147→170 at x 775) |
| Crevice 1 | depth −4 (wall touches the layer beneath), row y 170 / 165 / 157 at x 775 / 800 / 825 | M |
| Roll 2 (bellows lobe, single layer) | lobe height **28**, proud **16**, fold radius 6 at the crest | M (y 170→181) |
| Crevice 2 | depth −4, y 181 / 178 / 172 | M |
| Roll 3 | lobe height **20**, proud **12** | M (y 181→189) |
| Band | **8** tall, proud 3 (flat fabric compressed under the straps/carrier), then the hidden single wall down to the seat (≈ 10–15 further) | M |
| Tilt of the crevice rings | 15° rising toward his left in the image plane ≈ a ring tilted about the camera axis by 15° and about the lateral axis so the back is 50 higher | M (D1) |
| Left pleat | centred at the side seam (clock 5), **14** wide, 8 deep at the top edge tapering to 2 at roll 3, leaning 10° (top toward the back) | M |
| Mean outer diameter of the stack at roll 1 | **233** laterally (x 745–855) = neck 135 + 2 × (3 collar + 5 air + 42 … no: 2 × (wall 3 + air 6 + lobe 22 + hem ply 6)) → 209–235 depending on the roll's air | M, consistency |
| Fabric budget (tube length 280) | roll 1 turned hem 2 × 42 = 84; bellows arc rolls 2–3 ≈ 56 + 42; band 8; wall to the seat 30; slack inside the top roll 60 → **280** | derived (buckling wavelength 3.4 √(75 × 3) = 51 → three lobes in 90 mm: consistent) |

### 3.5 How the real garments wear
* **Shirt:** dust settles on up-facing rib crests (shoulders) and cuff tops; fold crests of the knit develop a faint sheen and 8–12 % lightening (fibre abrasion); the ripstop fades 5 % on crests; black thread goes grey-brown (#3a3430) where sun-struck; 5 mm wide rings of fuzzed, lighter fabric where the pauldron bands, guard bands and glove gauntlets rub; sweat darkening (−15 % value, +0.05 roughness → actually −0.05: damp knit is smoother) along the collar seam and under the carrier straps; no tears, no holes, no fading of the camo (none to fade).
* **Gaiter:** pilling on the top roll's outer face (chin stubble), nap flattened and darker where the straps press (−10 % value, roughness −0.05), dust on the top roll's upper face (+ #9a8d85 at 20 % mix), sweat/dirt band at the lowest visible 15 mm above the carrier (−12 % value), the hems' coverstitch slightly wavy (fleece stretches), 2–3 stray fibres standing 3–4 mm proud on the rim-lit edge.

---

## 4. Geometry construction plan

### 4.1 Construction decisions and justification (`research_blender_capabilities.md`)
* **Shirt torso and shoulder panels: modifier stack, no simulation.** The knit is tight (ease 40–60 on a 1100 chest) and compressed by the carrier, cummerbund, straps and belt: a sim would add nothing but risk. Body-derived offsets by zone (Shrinkwrap + weighted Displace), Solidify, seams as geometry, ribs as geometry on a subdivided panel, wrinkles by `gn_wrinkles` (t06: a six-modifier stack of this kind applies in 0.37 s and renders in 20 s).
* **Lower sleeves: cloth simulation on an animated arm, then baked to a static mesh.** Elbow folds and the pinch under the guard bands are the one thing displacement does badly. The sleeve is a pre-shaped tube pinned at its top seam ring and at the cuff ring; the arm (collider) moves from rest to the hero pose over 40 frames; the slack folds where a real sleeve folds (t02: 3 k verts × 60 frames in 10 s; `scene.frame_set` stepping is deterministic; `modifier_apply` under `temp_override` works). Fallback: `gn_wrinkles` recipe only (§4.13).
* **Gaiter: lofted bellows (deterministic) + 12-frame cloth relax + displacement; the push-down sim is a GPU-session experiment.** A tube under axial compression buckles unpredictably (diamond modes) and the research's lesson is "folds form only where something forces them"; the measured roll rows are facts we can loft exactly. A short pinned relax with self-collision breaks the loft's symmetry. Adaptive displacement (t04, ≈ 4 min per surface) is **not** used; the fold geometry is real mesh, micro-structure is bump, nap is hair curves only in closeups (t03: 3 000 curves build in 0.03 s; cost ∝ strands × pixel coverage).

### 4.2 Inputs expected from other parts (see §10.1)
`Body.Mesh` (rest) and `Body.Mesh.Posed`, `Body.Collider` (spec 09's, extended to the hyoid by spec 04), `Morgan.Rig`, the rings `Torso.Ring.NeckBase`, `Torso.Ring.Collar`, `Torso.Ring.Gaiter.Top`, `Torso.Ring.CarrierTop`, `Torso.Ring.Hem`, `Torso.Ring.Waistband`, curves `Torso.Curve.Strap.L/R`, anchors `Torso.Anchor.Acromion.L/R`, `Torso.Anchor.GH.L/R`, `Torso.Anchor.C7`, `Torso.Anchor.Suprasternale`; `Arm.L/R.SleeveCollider` (arm + 3 mm), `Arm.L/R.CuffRing` (185 at wrist −30), `Arm.L/R.GuardFrame`, `Arm.L/R.ElbowAnchor`, the `measure_arm()` girth table; the `Torso.Compress.*` keys at 1.0; stand-ins (spec 04 §4.12 `Torso.StandIn.*`) or the real carrier, straps, pauldrons, guards and gloves as colliders.

### 4.3 Step 1 — zone masks on the body (`shirt_zones.py`, numpy on the rest mesh, stored as vertex groups on `Body.Mesh` and copied to the shirt)
`Shirt.Zone.Torso` (hyoid-collar ring down to h 830; X within the trunk), `Shirt.Zone.Collar` (ring `Torso.Ring.Collar` ± 30), `Shirt.Zone.Panel.L/R` (from the collar seam over the acromion and the deltoid to humerus s 62 %, bounded by the armscye curve: a plane through the anterior/posterior axillary folds tilted 15°), `Shirt.Zone.Sleeve.L/R` (s 62 % → wrist + 25), `Shirt.Zone.ElbowPocket.L/R` (s 82 % → forearm s 52 %, clock 3–9 through 6), `Shirt.Zone.Cuff.L/R` (wrist −5 → +25), `Shirt.Zone.Hem` (h 830–870). Compression bands (weights 1 inside, 6 mm falloff): `Shirt.Band.CarrierFront` (the bag footprint 315 × 420 at Y −118), `Shirt.Band.CarrierBack`, `Shirt.Band.Cummerbund` (h 1050–1180), `Shirt.Band.Strap.L/R` (73 wide along `Torso.Curve.Strap.*`), `Shirt.Band.Belt` (h 812–859), `Shirt.Band.Tier3.L/R` (upper arm s 58–83 %, 50 tall), `Shirt.Band.GuardElbow.L/R` (forearm s 10–22 %), `Shirt.Band.GuardWrist.L/R` (s 86–96 %), `Shirt.Band.Gauntlet.L/R` (wrist −5 → +25), `Shirt.Band.CapSeat.L/R` (the pauldron tier-1 footprint 110 × 130 on the deltoid). Wrinkle masks: `Shirt.Wr.ElbowInner.L/R` (clock 10–2, s 80–100 % humerus + forearm 0–20 %), `Shirt.Wr.ElbowOuter.L/R`, `Shirt.Wr.Blouse` (h 870–960 front), `Shirt.Wr.PanelPull.L/R` (from the cap seat toward the back seam), `Shirt.Wr.Axilla.L/R`.

### 4.4 Step 2 — offset table (per zone; offset = distance of the garment's inner surface from the body surface along the body normal; the garment's outer surface = inner + thickness)

| Zone | Inner offset (mm) | Thickness | Outer surface at | Why |
|---|---|---|---|---|
| Torso, free knit | 2.0 | 1.0 | body + 3.0 | snug jersey |
| Torso under the carrier bags / cummerbund / belt / straps | 0.3 | 1.0 (compressed to 0.8) | body + 1.1–1.3 | spec 04's `Torso.Band.*` and spec 09's belt assume body + 1.5 for the shirt |
| Collar | 1.5 | 2.3 | body + 3.8 | the gaiter's inner wall sits ≥ 5 beyond it |
| Shoulder panel, free | 1.5 | 2.2 (+0.6 rib relief) | body + 3.7 (crests 4.3) | spec 04 §10: "shirt body at body + 1.5" is the panel's inner offset |
| Panel under the tier-1 cap seat and the tier-3 band | 0.5 | 1.8 | body + 2.3 | the pauldron spec seats the cap at body + 2.5, the band's inner face at body + 2.5 |
| Lower sleeve, free (pre-sim shape) | 6–25 (from the ease table §3.2, interpolated by station) | 0.45 | tube radius from the garment circumference | the sim relaxes it |
| Sleeve under the guard's elbow-end / wrist bands | 1.0 | 0.45 | body + 1.45 | the guard's neoprene sleeve (3 mm) sits on it → guard inner face at body + 1.5, plates at body + 4.5 |
| Cuff inside the gauntlet | 1.0 | 1.4 | body + 2.4 | gauntlet inner face at body + 3.5 (spec 11 must respect) |
| Elbow pocket | as the sleeve + 0 | 1.45 (two plies) | — | — |

### 4.5 Step 3 — `Shirt.Torso` and `Shirt.Panel.L/R` (bmesh + modifiers; names captured before any `modifier_apply`, research §6 gotcha)
1. Copy the faces of `Body.Mesh` in `Shirt.Zone.Torso ∪ Collar ∪ Panel.*` with bmesh into `Shirt.Torso.Base` (≈ 4 800 quads at the body's 20–30 mm spacing); `bmesh.ops.subdivide_edges` ×1 → ≈ 19 k quads (≈ 10 mm); delete the arm faces below s 62 %; cut the torso at h 830 (`bmesh.ops.bisect_plane`), keep the hem loop.
2. `Shrinkwrap` (target `Body.Collider`, `NEAREST_SURFACEPOINT`, `OUTSIDE_SURFACE`, `offset 0.002`) → `Displace` "ZoneOffset" (`direction NORMAL`, `texture_coords UV` on a baked 512² zone-offset image from the table in §4.4, strength 0.004, mid 0.5; or a GN `Set Position` reading the `Shirt.Band.*` groups: offset = 2.0 − 1.7 × max(band weights)) → apply both.
3. Collar: extrude the collar ring upward 55 along the neck axis (`bmesh.ops.extrude_edge_only`, 5 rings), flare 3° outward; split the front centre for the zip (two edge loops 6 mm apart, 180 long from the collar top down); `Shirt.Collar` stays part of `Shirt.Torso` (one object) but has its own material slot.
4. Rib panels: separate the `Shirt.Zone.Panel.*` faces into `Shirt.L.Panel`, `Shirt.R.Panel`; UV-unwrap each panel with the U axis along the wale direction (collar seam → down the deltoid: `bpy.ops.uv.unwrap` after marking the seams at the panel boundary, then rotate the island so the mean collar-to-deltoid vector is +U); `Subdivision` 2 (≈ 2.5 mm) → GN `Shirt.GN.Ribs`: displacement along the normal = 0.3 mm × (1 + cos(2π U_mm / 4.2)) × (1 − band weights × 0.7) (ribs flatten under the cap and band) with a 0.35 mm half-depth valley; wale edges rounded by a `Smooth` 0.2 — apply (t06 route). Panel seam ring at s 62 % kept as a closed loop (`Shirt.Ring.Panel.L/R`).
5. `Solidify` on `Shirt.Torso` (thickness 0.001, `offset +1`, `use_even_offset`, `use_rim`, `thickness_vertex_group` = `Shirt.Band.*` union with factor 0.8) and on the panels (0.0022, same options) → keep live until §4.11.
6. Hem: the hem loop at h 850 is extruded inward 20 and folded up (a 2-ply turned hem, `bmesh.ops.extrude_edge_only` twice, 1.0 mm apart) — hidden inside the trousers, 36 quads, LOD 2.

### 4.6 Step 4 — lower sleeves `Shirt.L.Sleeve`, `Shirt.R.Sleeve` (`cloth_tube.build_tube` from spec 09, then cloth)
1. Axis: the arm's segment vectors in **REST** (MPFB rest, spec 05 §7.3 vectors) from the panel seam ring (s 62 %) through the elbow axis to wrist + 25. Section table along the axis (mm): s 62 % 390; s 82 % (pocket top) 370; s 100 % elbow 360; forearm s 25 % 350; s 52 % (pocket bottom) 330; s 75 % 290; s 90 % 225 + 20 (pre-sim slack); cuff 215. Sections are ellipses whose axis ratio follows the arm's section (spec 05 §3.2–3.3), rotated with the clock frame.
2. Mesh: 64 around × 72 along (quads 5.5–6 mm) = 4 608 quads per sleeve; the cuff is a separate 30 mm band (64 × 5) with the 2-ply hem (`Solidify` 1.4 later) and a `Shirt.L.CuffTab` strip 25 × 60 × 1.2 (bmesh plane, 6 × 14 quads, hook-and-loop material) bar-tacked at the ulnar cuff.
3. Pattern seams as vertex groups on the tube: `Shirt.Seam.Back.L` (the path of §3.2 interpolated by clock position per station), `Shirt.Seam.Under.L`, `Shirt.Seam.PocketTop.L` (ring at s 82 %, clock 2–10 through 6, i.e. the back 2/3), `Shirt.Seam.PocketBottom.L`, `Shirt.Seam.PocketSides.L`, `Shirt.Seam.Cuff.L`, `Shirt.Seam.Panel.L` (top ring). Pocket: duplicate the faces of `Shirt.Zone.ElbowPocket` into `Shirt.L.ElbowPocket` (outer ply, offset +1.0, 320 quads) with its top edge free (the opening) and a 25 × 150 hook-and-loop strip inside the opening; the sleeve under it is the inner ply.
4. Pin groups: `Shirt.Pin.Top.L` (the panel seam ring, follows `Shirt.L.Panel` through a `Surface Deform` bind done before the sim so the ring rides the panel's posed position), `Shirt.Pin.Cuff.L` (the cuff ring, parented to the `wrist.L` bone through a hook: `Hook` modifier to an Empty `Shirt.L.CuffHook` parented to the bone, `vertex_indices_set` on the ring, falloff 0).
5. Colliders: `Arm.L.SleeveCollider` (arm + 3 mm; `Collision` modifier `thickness_outer 0.002`, `cloth_friction 8`), the glove gauntlet stand-in (a 30 mm cylinder at wrist −30…0, r = wrist r + 3.5), the forearm guard stand-in (two bands 25 wide, inner radius body + 1.5, at forearm s 10–22 % and s 86–96 %, present from frame 1 so the sleeve settles under them), the tier-3 band stand-in (50 wide at humerus s 58–83 %, inner body + 2.5, on the panel, i.e. above our sleeve — it pins the panel seam neighbourhood only).
6. Cloth (`Shirt.L.Sleeve` → `bpy.types.ClothModifier`, 25 fps, frames 1–60; the arm's rig moves rest → hero pose over frames 5–45 with `Body.Collider`/`Arm.L.SleeveCollider` following through their Armature modifiers):

| Group | Property | Value | Why |
|---|---|---|---|
| Physical | `quality` | 8 | 6 mm quads |
| | `mass` | 0.20 | 224 g/m² ripstop (0.3 is cotton) |
| | `air_damping` | 1.0 → 3.0 at frame 48 | settle |
| Stiffness | `tension_stiffness` / `compression_stiffness` | 25 / 25 | NYCO between cotton 15 and denim 40 |
| | `shear_stiffness` | 10 | ripstop shears easily |
| | `bending_stiffness` | 0.8 (pocket zone 1.6 via `vertex_group_bending`, max 1.6) | crisp 8–15 mm folds, two plies at the pocket |
| | `bending_model` | 'ANGULAR' | — |
| Damping | `tension_damping` / `compression_damping` / `shear_damping` / `bending_damping` | 5 / 5 / 5 / 0.5 | — |
| Shape | `vertex_group_mass` (pin) | `Shirt.Pin.Top.L ∪ Shirt.Pin.Cuff.L`, `pin_stiffness 1.0` | the seam ring and the cuff hold |
| | `vertex_group_shrink` / `shrink_min` / `shrink_max` | `Shirt.Shrink.Guards.L` (the two guard bands) / 0 / 0.0 → 0.10 over frames 30–45 | the guard straps cinch the sleeve |
| Collisions | `collision_quality` | 4 | — |
| | `distance_min` | 0.003 | ≥ 3 mm at 6 mm quads (research) |
| | `use_self_collision` / `self_distance_min` / `self_friction` | True from frame 10 / 0.003 / 5 | the inner-elbow folds stack without passing through each other |
| | `friction` (collider) | 8 (arm), 20 (gauntlet and guard bands) | the cuff stays in the gauntlet |

Timeline: frames 1–5 settle on the straight arm; 5–45 the rig poses the arm (`Morgan.Rig` action `Hero.Pose` scaled: `pose.bones[...].rotation_quaternion` keyframes interpolated by `scene.frame_set`); 30–45 shrink ramp; 45–60 damped settle. Step `scene.frame_set` 1 → 60, run the stability checks (§9.3), apply at frame 60 (`modifier_apply` under `temp_override(object=ob, active_object=ob, selected_objects=[ob])`, or `meshes.new_from_object(ob.evaluated_get(dg))`) → `Shirt.L.Sleeve.Base` (static, in the hero pose). Cost: 2 × 4.6 k verts × 60 frames ≈ 15–30 s (research cost model 0.15–0.35 s/frame per 3 k verts).
7. Right sleeve identically with `Hero.Pose` right-arm channels (elbow 97°, pronation 70°; the pre-sim slack at the inner elbow is increased +10 mm because the fold mass is larger).

### 4.7 Step 5 — seams, stitches, hems, zip (`gn_stitches.py` node group `Shirt.GN.Details`, from spec 09 §4.10 and the prototype recipe of `research_prototypes.md` §8)
* **Flat-felled seams (ripstop)**: along each `Shirt.Seam.*` path on the sleeves, a felled strip 7.0 wide: the cloth is raised 1.2 mm over a 7 mm band with a 0.3 mm step at both edges (GN proximity to the seam curve → displacement profile `smoothstep` + step), two running stitch rows 6.4 apart (needle Ø 0.3 → thread cylinders r 0.30, 6-sided, length 2.8, gap 0.8 → pitch 3.6, sunk 0.15 into the cloth, thread albedo 0.12, roughness 0.6, sheen 0.1). Bobbin side not modelled (inside).
* **Coverstitch (knits, gaiter hems, the panel-to-ripstop junction, the collar)**: two needle rows 5.6 apart, pitch 2.5, same cylinder recipe with r 0.25; a looper zigzag between the rows on the inside is omitted (hidden) except on the gaiter's top hem where the hem edge faces outward on the turned-down roll: there the looper web is a 0.25 mm zigzag of pitch 2.5 between the rows (visible in V5).
* **Bar tacks**: 3 wide × 12 long, 1.3 pitch zigzag, at the elbow pocket's four corners, the cuff tab root (2), the hem vent (none), the collar's zip top (2).
* **Zip**: `Shirt.Zip` — tape 2 × 13 wide × 0.8 thick (bmesh strips following the collar's front-centre split), coil chain 6 wide × 2.5 proud as an `Array` of 3.2 mm tooth pairs (a 1 × 3.2 × 2.5 rounded box, 56 pairs) along a `Curve` modifier on the split's centre line, slider 25 × 12 × 6 with a 20 × 8 pull hanging down at the collar top (h 1592 rest), zipped fully closed; **entirely under the gaiter**; LOD 1 keeps tape + chain as one strip with a normal map.
* **Rib panel junction**: at `Shirt.Ring.Panel.*` the ripstop's top edge is turned under 10 and coverstitched to the rib (two rows), 1.0 proud — the seam the tier-3 band sits on.
* **Hook-and-loop**: the cuff tab's hook face (25 × 50) and the pocket closure's loop strip are flat strips with the `Shirt.Mat.HookLoop` material (loop: 1 mm Voronoi bump, hook: 0.8 mm grid of 0.3 mm hooks as bump).
* Stitches are emitted as separate objects `Shirt.Stitches` and `Shirt.Bartacks` (droppable for LOD and form checks). Count: seam length ≈ 2 × (back 640 + under 620 + pocket 700 + cuff 215 + panel ring 390) + collar/torso coverstitch 2 600 + hems 1 000 ≈ 8.7 m → ≈ 2 400 ripstop stitches + 2 000 coverstitches ≈ 4 400 cylinders × 12 tris ≈ 53 k tris.

### 4.8 Step 6 — assemble `Shirt.Main` (modifier stack kept live until the rig bind, order matters)
`Shirt.Torso` (+ collar, hem) joined with `Shirt.L/R.Panel` (after their rib GN is applied) and `Shirt.L/R.Sleeve.Base`, `Shirt.L/R.ElbowPocket`, `Shirt.L/R.Cuff`, `Shirt.L/R.CuffTab` by `bpy.ops.object.join` into **`Shirt.Main`** with material slots per component; the panel/sleeve junction rings are merged by `bmesh.ops.remove_doubles` (dist 0.5 mm) so the surface is watertight across the seam before the seam GN raises the ridge. Stack on `Shirt.Main`: `Solidify` (per-slot thickness via `thickness_vertex_group`: knit 1.0, rib 2.2, ripstop 0.45, cuff 1.4) → `Bevel` (0.3 mm, 2 segments, angle 60°, on the hem and collar rims only via a weight) → `Subdivision` (render 1, viewport 0; the sleeves are already 6 mm) → `Displace` "Micro" (legacy CLOUDS, Voronoi F2−F1, noise 25 mm, strength 0.8 mm along normals, only `Shirt.Zone.Sleeve`: ripstop puckers) → GN `Shirt.GN.Wrinkles` (§6.3) → GN `Shirt.GN.Details` (seam ridges; stitches to their own objects) → `Data Transfer` (weights, §7) → `Armature`. Apply everything above the Armature once the critic has passed the form (CLAUDE.md rule 4: the script rebuilds from scratch anyway).

### 4.9 Step 7 — `Gaiter.Main` (lofted bellows, `cloth_tube.loft_profile` + relax)
1. **Centre curve**: the neck axis of spec 04 (suprasternale/C7 midpoint (0, −12, 1550) → skull base (0, −8, 1650) rest, 8° forward tilt), posed by the `neck01–03` bones (the gaiter is built on the **posed** body because its shape is pose-specific; the rest-mode deliverable is the same mesh weight-bound, §7.2).
2. **Profile** (radius offset r(z) from the posed neck/collar outer surface, in mm, z measured down from the saddle top ring): hem fold 0 → +9 (quarter circle, r 9) → outer face of roll 1 from +22 at z 9 to +18 at z 36 → inward fold into crevice 1 at z 42 (r = +4, the wall sits on the layer below) → roll 2 crest +16 at z 56 → crevice 2 +4 at z 70 → roll 3 crest +12 at z 80 → crevice 3 +4 at z 90 → band +3 from z 90 to 98 → single wall +5 (collar + air) down to the seat ring → bottom hem (12 turned in, 2 plies, 6 mm fold radius) lying on the trapezius/clavicles. Roll 1 is a **double layer**: the loft produces the outer ply; the inner ply (the hem's return) is a second loft from the fold at z 0 down to z 42 at r = +10 … +13, both plies 3.0 thick by `Solidify`.
3. **Saddle and tilt**: each profile station's z is offset by the saddle function Δz(θ) interpolated from the four measured top-edge heights (front 0, right −17, left-front −31, back-left −63 relative to the front, i.e. higher at the back) with a cosine blend; the crevices follow the same function at 70 % amplitude (the stack is compressed at the front, so the lobes are shorter there: roll 1 36 at the front centre vs 42 at the right).
4. **Left pleat**: a longitudinal depression centred at the side seam (θ = 5 o'clock from above, X +70, Y +60), width 14 mm (±7, cosine), depth 8 at z 0 → 2 at z 80, leaning 10° toward the back as it descends; added to r(θ, z) before lofting.
5. **Mesh**: 128 around × 48 profile stations (quads 3.5–5.5 mm) = 6 144 quads outer ply + 128 × 10 inner ply + hems; `Solidify` 0.003 (even, rim) → **12.5 k faces**; `Subdivision` render 1.
6. **Relax**: `Cloth` 12 frames, gravity (0,0,−9.81), `mass 0.25`, tension/compression 20, shear 8, bending 1.2 (fleece is floppy but thick), pin `Gaiter.Pin` = the seat ring and the top hem fold ring, self-collision 3.0 mm, colliders `Body.Collider` (neck), the shirt collar, the carrier top + straps stand-ins (so rolls 2–3 and the band are pressed flat by the straps on both sides: the stand-ins descend from body + 40 to their final seat over frames 2–10); apply at frame 12 → `Gaiter.Base`. Purpose: break the loft's perfect roundness by 1–3 mm, pull the lobes down slightly under gravity, seat the band under the straps. Expected 6 k verts × 12 frames ≈ 5 s.
7. **Side seam** `Gaiter.Seam`: flatlock strip 6 wide, 0.6 proud, two coverstitch rows 4.8 apart along the pleat's centre line from the top hem to the bottom hem, with the looper web between (visible on the pleat's rim in V2/V5). **Hems**: 12 mm bands with two rows 5.6 apart (top hem on the outer face of roll 1 at z 30–42; bottom hem hidden).
8. **Pills** `Gaiter.Pills`: GN `Distribute Points on Faces` (density 1/40 mm² on the top roll's outer face, 1/400 mm² elsewhere, seed 7) → instanced icospheres r 0.5–1.0 (random), sunk 50 %, fleece material; ≈ 350 instances.
9. **Stray fibres** (closeups only): 40 curves 3–4 mm long, radius 0.012, on the rim-lit edge (θ facing +X), random lean.

### 4.10 Step 8 — nap `Gaiter.Fuzz` (closeups only, `--fuzz`)
`bpy.data.hair_curves.new`, 80 000 curves × 4 points on `Gaiter.Base` (surface attachment via the research's `Attach Hair Curves to Surface` node), length 1.0–1.6 mm (random), radius 0.010 root → 0.004 tip (`radius` attribute), lean 35–65° off the normal in random azimuth, `Hair Curves Noise` (`Input_3` 0.3, scale 0.4 mm), density 0.2/mm² (an eighth of real pile — enough for the fringe at 85 mm), density × 0.3 under the straps and in the crevices (flattened nap). Material: Principled Hair BSDF (Chiang) melanin 0.65, melanin redness 0.4, tint toward #373029, roughness 0.5. Render cost: the gaiter fills ≈ 40 % of V5 at 800² → ≈ 60–90 s extra at 48 spp (research: 40 k thick strands ≈ 3× a plain surface; ours are thin and short). Off in V1–V4 (the gaiter is 110 × 72 px there; the sheen term carries the look).

### 4.11 Step 9 — joins and contacts
* Shirt collar ↔ gaiter: the gaiter's inner wall at collar outer + 5 ± 3 everywhere; its seat (bottom hem) on the trapezius/clavicles at body + 3.8 (over the shirt knit) with the hem's 2 plies.
* Panel ↔ pauldron: the tier-1 cap seat (110 × 130 on the deltoid) gets `Shirt.Band.CapSeat` offset 0.5 → the pauldron spec seats the cap's inner padding at body + 2.5; the webbing tab from under tier 1 to the strap passes over our panel at panel + 0.
* Sleeve ↔ guards: bands at body + 1.5 (inner neoprene face); our fabric bulges to body + 8–12 within 20 mm above and below each band (sim output; checked §8.6).
* Cuff ↔ gauntlet: our cuff outer at body + 2.4 inside the gauntlet (inner face body + 3.5), overlapping 25 mm; no skin visible between them from any angle.
* Shirt ↔ trousers: hem at h 850 inside; the knit above the waistband blouses to body + 6–9 (`Shirt.Wr.Blouse`) and sits under the carrier's hem shadow.
* Gaiter ↔ straps: the straps' inner face at gaiter band + 0 (the relax presses the band to body + 3.8 + 6 = the straps' inner face at body + 9.8 there; spec 13 must place the straps at body + 10 over the gaiter and body + 6 elsewhere — interface §10.1).

### 4.12 Fallback (no simulation) — only if §9.3 fails twice
Sleeves built by the modifier route of §4.5 with the §4.4 free offsets and the full `Shirt.GN.Wrinkles` recipe (§6.3) including the elbow fold rings as explicit displacement; the guard-band pinch by two Shrinkwrap modifiers limited to the band groups (spec 09 §4.8 method). Expect a 1-point loss on criterion 3 and 6 (folds too regular).

### 4.13 Topology targets and poly budget

| Object | Base faces | Render (Subd 1) | Notes |
|---|---|---|---|
| `Shirt.Main` torso + collar + hem | 19 500 quads | 78 k | 10 mm quads; collar 5 rings |
| `Shirt.Main` panels L/R | 2 × 9 800 (after Subd 2 for the ribs, applied) | 2 × 39 k | ribs are real geometry (0.6 mm) |
| `Shirt.Main` sleeves L/R + pockets + cuffs + tabs | 2 × 5 300 | 2 × 21 k | 6 mm quads from the sim |
| `Shirt.Zip` | 1 200 tris | — | hidden |
| `Shirt.Stitches`, `Shirt.Bartacks` | 53 k tris | — | droppable |
| `Gaiter.Main` | 12 500 faces (two plies, solidified) | 50 k | 3.5–5.5 mm quads |
| `Gaiter.Seam`, `Gaiter.Hems` stitches | 6 k tris | — | — |
| `Gaiter.Pills` | 350 × 80 tris = 28 k | — | closeups only |
| `Gaiter.Fuzz` | 80 k curves × 4 pts | — | `--fuzz` only |
| **Total render, hero** | ≈ 260 k faces + 60 k stitch tris | | export LOD1: Subd 0, stitches off → ≈ 70 k faces |

Origins: `Shirt.Main` and `Gaiter.Main` at the world origin (the character frame), `Shirt.Zip` at the collar top centre, hooks/empties at their bones. Collection `Part10.ShirtGaiter` with sub-collections `Part10.Stitches`, `Part10.Fuzz`, `Part10.Sim` (pre-sim tubes and colliders, hidden). Images: `Shirt.Masks.png` 4096² (two UDIMs), `Shirt.ZoneOffset.png` 512², `Gaiter.Masks.png` 2048². Materials: `Shirt.Mat.Knit`, `Shirt.Mat.Rib`, `Shirt.Mat.Ripstop`, `Shirt.Mat.HookLoop`, `Shirt.Mat.Zip`, `Thread.Black` (shared), `Gaiter.Mat.Fleece`, `Gaiter.Mat.Fuzz`.

---

## 5. Materials and textures

### 5.1 Material list (Principled BSDF, Blender 4.5; colours are **albedo** sRGB hex with linear RGB in brackets; targets in §5.6 are lit pixels)

| Material | Base Colour | Rough | Spec IOR level | Sheen weight / rough / tint | Normal / bump sources | Notes |
|---|---|---|---|---|---|---|
| `Shirt.Mat.Knit` (torso, collar) | **#2c2826** (0.025, 0.021, 0.019) | 0.80 ± 0.04 (Noise 40 mm) | 0.35 | **0.18 / 0.45 / base × 1.3** (research F §0: untinted sheen bleaches dark fabric; sheen ≤ 0.2) | `cotton_jersey` nor_gl tiled so the wale pitch = 1.0 mm (tile 26.4 cm → scale factor measured by `measure_tile_pitch()` [VERIFY: count the tile's columns by FFT on download]), strength 0.6; AO × 0.3 into base | roughness −0.05 in sweat bands |
| `Shirt.Mat.Rib` (shoulder panels) | #2e2a28 (0.028, 0.023, 0.021) | 0.82 | 0.35 | 0.20 / 0.45 / base × 1.3 | ribs are geometry; micro: Wave texture along V (courses) 1.1 mm, bump 0.05 mm; `cotton_jersey` nor at 0.3 for the yarn | dust mask lightens crests |
| `Shirt.Mat.Ripstop` (lower sleeves, pockets, cuffs) | **#2a2725** (0.023, 0.020, 0.018) | 0.68 ± 0.04 | 0.45 | 0.10 / 0.35 / base × 1.2 | procedural ripstop (§5.3) bump 0.08 mm + `denim_fabric_05` nor_gl (dark-tinted twill, 27 cm tile at 0.5 scale) 0.4 + Displace "Micro" puckers | crest fade +5 % |
| `Shirt.Mat.HookLoop` | loop #262321, hook #2a2622 | 0.9 / 0.6 | 0.3 | 0.3 / 0.5 (loop) | loop: Voronoi 1 mm bump 0.4; hook: grid 0.8 mm bump 0.3 | — |
| `Shirt.Mat.Zip` | tape #262321; coil #1a1a1a nylon (rough 0.45, coat 0.2); slider #2b2b2d metallic 1.0 rough 0.35 | — | — | — | — | hidden |
| `Thread.Black` (shared with spec 09) | #1f1c1a (0.013, 0.011, 0.010); sun-struck #3a3430 by mask | 0.6 | 0.4 | 0.1 | — | thread cylinders |
| `Gaiter.Mat.Fleece` | **#3a3129** (0.043, 0.030, 0.021) | 0.78 ± 0.05 (Noise 15 mm) | 0.30 | **0.28 / 0.55 / base × 1.4** (the velvet term; calibrated so (760,155) hits #7e6d62 and (835,160) stays ≤ #0a0806) | `knitted_fleece` (26.6 cm tile → scaled so its knit cells are 1.6 mm) nor_gl 0.5, Rough map 0.5 mix; micro Noise 0.6 mm bump 0.03 | sweat band −12 % value; strap-pressed nap −10 % value, rough −0.05 |
| `Gaiter.Mat.Fuzz` | Principled Hair (Chiang) melanin 0.65 redness 0.4 | 0.5 | — | — | — | curves only |

Displacement method on all fabric materials `BUMP` (research §4: true displacement only where a silhouette must break — none here; the rolls and ribs are mesh).

### 5.2 Knit micro-structure (`Shirt.Mat.Knit`)
`cotton_jersey` (Poly Haven, 2048 × 2050, 26.4 cm tile, albedo (194,170,156)): its Diffuse is **not** used for colour (tinted base instead); nor_gl drives the loops; AO darkens the inter-loop valleys (mix 0.3 into base). The tile is scaled so one wale = 1.0 mm (28-gauge jersey) — the scale is computed at material build by `measure_tile_pitch(image, axis)` (FFT peak of the normal map's x-component along U) and stored in `assets/manifest.json`; expected scale ≈ 0.26 m per tile × (measured wales per tile / 264). The exposed band in V1 is 18 × 36 px: there the knit shows only as roughness; in V8 (0.42 m, 100 mm) each loop is ≈ 4 px — the test in §8.6. Anisotropy: knit wales give a faint vertical specular streak — `anisotropic 0.25`, rotation along V.

### 5.3 Ripstop lattice (procedural, `Shirt.Mat.Ripstop`)
In UV space of each sleeve (U along the sleeve axis, texel density §5.5): grid(u, v) = max(pulse(u mod 6.35, width 0.4), pulse(v mod 6.35, width 0.4)) → bump 0.08 mm (the doubled yarn is proud), plus the base weave: two Wave textures (warp along U, weft along V) at 0.31 mm pitch (32 threads/cm) × 0.33 mm, amplitude 0.02 mm, distortion 1.2; roughness −0.04 on the grid yarns (they are smoother, crest-polished). A Noise (3 mm, 0.15) warps the grid 0.1 mm so no two cells are identical. The grid runs along the sleeve axis (warp along the sleeve, as cut) — on the left sleeve at 45° in the image it reads diagonal (D8). Crest fade: `Pointiness` → +5 % value.

### 5.4 Rib panel (`Shirt.Mat.Rib`) and fleece (`Gaiter.Mat.Fleece`) micro-structure
Rib: wales are mesh (§4.5 step 4); the yarn structure on the wale faces is `cotton_jersey` nor at 0.3 plus the course Wave (1.1 mm, bump 0.05). Fleece: `knitted_fleece` (Poly Haven, 2048 × 2079, 26.6 cm, albedo (85,75,62) — "right structure and nearly the right colour ×0.7", research A): its nor_gl at 0.5 gives the pile's clumping; its Rough map is mixed 0.5 with 0.78; the Diffuse is replaced by the tinted base but its luminance variation (high-pass, ±6 %) is multiplied into the base for the pile mottling. Pills are geometry (§4.9 step 8); the nap's velvet behaviour is the Sheen term in hero views and curves in V5.

### 5.5 UVs and texel density
* `Shirt.Main`: UDIM 1001 torso + collar + hem (surface ≈ 0.62 m² → 2048² → **2.6 px/mm**), 1002 panels + sleeves + pockets + cuffs (≈ 0.55 m² → 2048² → 2.8 px/mm). Masks only (dust, sweat, abrasion, crest fade, zone id) — micro-structure is tiled procedurally at its own density (jersey 7.8 px/mm, fleece 7.7, denim 7.6), so 2.6 px/mm is enough. Sleeves unwrapped as cylinders split along the under seam (U along the axis).
* `Gaiter.Main`: one 2048² (0.13 m² outer + inner ply → **5.7 px/mm**), unwrapped as a cylinder split at the side seam, V down the profile (the wave of the rolls is in 3D, not in UV).

### 5.6 Weathering masks (`Shirt.Masks.png`, `Gaiter.Masks.png`, baked once by `bpy.ops.object.bake` type EMIT from helper materials, research §10c: ≤ 1 min at 2–4 k)
R = **dust** (n·Z > 0.3 → smoothstep × AO⁻¹, × 1.0 on the shoulder ribs' crests, × 0.8 on the gaiter top roll's upper face, × 0.4 cuff tops, 0 elsewhere; dust colour #9a8d85 mixed at R × 0.35), G = **sweat/grime** (gaiter: 15 mm band above the carrier top + under the straps; shirt: collar seam ± 10, under the straps, the exposed band's lower 20 mm; value −12 … −15 %), B = **abrasion** (5 mm rings at the band/guard/cap edges and the gauntlet rim: +15 % value, roughness +0.1, nap flattened), A = **crest fade** (Pointiness > 0.55 on the knits and ripstop: +8 … 12 % value, sheen +0.05). Baked on the posed mesh (the bands are pose-dependent). No uniform wash anywhere.

### 5.7 Colour targets to hit after grading (reference pixels; render V1/V2 and read 5 × 5 means; tolerance ±10/255 per channel)
Gaiter: (760,155) **#7e6d62**; (760,170) #5c5048; (800,170) #524a41; (815,195) #685846; (780,185) #3c342b; (835,160) ≤ #0a0806; (850,140) #4e565c (cool rim with nap); (820,135) #1d1410. Shirt: left sleeve box (885–925 × 300–370) median **#332f2d** ± 8; (700,210) #473d3b; (690,280) #242222; (905,270) #595047; (925,295) #504d4a; (945,300) #74879b (seam rim); (910,330) #241f1e; (900,350) #48423e; (795,410) #3a3532; (800,485) #1c1b19. The lighting calibration order of `analysis_lighting_camera_scene.md` §6.6 applies (skin first, then the carrier, then us).

---

## 6. Fibres, simulation or dynamics

### 6.1 Fibres
`Gaiter.Fuzz` (§4.10) and the 40 stray fibres; nothing on the shirt (jersey and ripstop have no visible pile; the knit's sheen term carries the fibre scatter).

### 6.2 Simulation
Lower sleeves: 60-frame cloth on the posing arm (§4.6). Gaiter: 12-frame relax (§4.9). Both deterministic (`scene.frame_set` stepping), both baked to static meshes; SHA-1 of the vertex arrays written to `renders/10_combat_shirt_gaiter/sim_hash.txt`. Push-down gaiter experiment (GPU session, `--gaiter-sim`): a straight 280 × 460 tube (128 × 56 quads) seeded with a 4 mm sinusoidal radius modulation at the intended lobe heights, bottom ring pinned to the seat, top ring in the pin group driven by a shape key "Pushed" (top ring down 150, keyframed 0 → 1 over frames 1–50), self-collision 3 mm, collar collider; accept only if the result has exactly three lobes within 6 mm of §3.4 — otherwise the loft stays.

### 6.3 Wrinkle recipe by zone (`Shirt.GN.Wrinkles`, displacement d along the normal in mm; masks are the vertex groups of §4.3 sampled as attributes; noises are `Noise Texture` 4D with W = seed; the sim supplies the primary elbow folds — these are secondary and tertiary)

| Zone (mask) | Primary form | Secondary (d) | Tertiary (d) |
|---|---|---|---|
| Torso, free knit (`Shirt.Zone.Torso` minus bands) | smooth | none | Noise 60 mm × 0.4 (knit sag) |
| Blousing above the waistband (`Shirt.Wr.Blouse`) | one horizontal roll 25 tall, +6 at h 905 (front), +4 at the sides, fading at the back; deeper on his right-front (×1.3) | 4 diagonal gathers from the belt toward the carrier hem, 12 mm wide, +1.5, pitch 35 | Noise 20 mm × 0.3 |
| Under the carrier bags / straps / belt (`Shirt.Band.*`) | flat (compressed) | a +1.0 bulge ridge 6 mm wide just outside every band edge (`Proximity` to the band border) | — |
| Shoulder panels, free (`Shirt.Zone.Panel`) | ribs (mesh) | 3–4 drape ridges from the cap seat's lower edge toward the back seam, 12 mm pitch, +1.2, following the pull direction (`Shirt.Wr.PanelPull`): the "12 mm diagonal ridges" of §2.1 | Noise 15 mm × 0.2 |
| Axilla (`Shirt.Wr.Axilla`) | 3 radial folds from the armpit, +2.0, 15 wide, 60 long | — | — |
| Inner elbow (`Shirt.Wr.ElbowInner`), after the sim | the sim's folds; if fewer than 4 crests at 8–15 mm pitch on the right / 3 at 10–18 on the left (§8.6), add Wave `BANDS` across the arm axis, pitch 12 (R) / 15 (L), +2.5, masked to clock 10–2 | Noise 8 mm × 0.4 across the fold crests | — |
| Outer elbow / pocket (`Shirt.Wr.ElbowOuter`) | stretched: d −0.5 (taut), pocket plies pressed | the pocket's top opening gapes 2 mm at its centre (+2 on the outer ply's top edge) | — |
| Under and beside the guard bands | the sim's pinch (bulges to body + 8–12 within 20 mm) | a crisp +0.8 ridge where the band edge cuts the fabric | — |
| Cuff inside the gauntlet | flat | 2 small gathers (+0.8) at the tab | — |
| Gaiter rolls | mesh + relax | Noise 30 mm × 1.0 on the lobes (fleece lumps), none in the crevices | Noise 6 mm × 0.25 |

---

## 7. Rigging and attachment

### 7.1 Weight transfer
`Shirt.Main`: `Data Transfer` modifier (`object = Body.Mesh.Posed` for the sleeves built in the hero pose, `Body.Mesh` for the torso built at rest — the script builds the torso at rest and poses it through the rig, the sleeves in pose and binds them to the posed body), `use_vert_data`, `data_types_verts = {'VGROUP_WEIGHTS'}`, `vert_mapping = 'POLYINTERP_NEAREST'`, `layers_vgroup_select_src = 'ALL'`, `mix_mode 'REPLACE'`; apply; then `Armature` (`Morgan.Rig`, `use_deform_preserve_volume`). Bone set: spine01–03, neck01, clavicle.L/R, shoulder01, upperarm01/02 (twist split per spec 05 §7.2: upperarm01 carries 30 % of the humeral rotation), lowerarm01/02 (forearm twist 30 % / 100 % at the wrist), wrist.L/R for the cuffs. Normalise, clip ≤ 4 influences, `Smooth` 2 iterations on the sleeve/panel junction ring so the seam does not tear when the arm rotates. The stitches objects get a `Surface Deform` to `Shirt.Main` instead of weights.

### 7.2 Gaiter
`Gaiter.Main` weights are written procedurally (no transfer, the neck's weights would twist it): w(neck01) = 1 − t, w(neck02) = t for t = (z − seat)/(top − seat) clamped 0–0.6 on the lower stack; the top roll gets neck02 0.5 / neck03 0.5; head 0. Posed mode (hero): built posed, bound in place (`Armature` with the rig in the hero pose → `bpy.ops.object.parent_set` is not used; the modifier's rest state is set by `armature.pose_position = 'REST'` toggling with the research's `view_layer` selection rules, i.e. the script sets the rig to REST, applies a `Corrective` shape key, returns to POSE — simpler: bind in pose with `Armature.use_deform_preserve_volume` and store the pose as the mesh's rest via `Apply Pose as Rest` only on a duplicate rig for the rest-mode export). Rest-mode deliverable (`--mode rest`): the posed gaiter mesh is un-posed through the inverse bone transforms (a `Data Transfer`-free numpy step: v_rest = Σ w_b M_b⁻¹ v_posed) so the stack stays a stack when the character stands straight; folds that only exist because of the head turn (the left pleat) remain baked, accepted.

### 7.3 Collisions with neighbours at build time
Order in `build_all.py`: body → trousers → **shirt torso and panels** → **sleeves (sim with guard/gauntlet stand-ins)** → **gaiter (relax with carrier/strap stand-ins)** → carrier and straps (spec 13 reads `Shirt.Main` as its inner surface) → pauldrons/guards/cap (spec 12 reads our bands) → gloves (spec 11 reads `Shirt.*.Cuff`). The flat V-variants of §8.1 check interpenetration with `bmesh` ray tests between our outer surface and every neighbour's inner surface (§8.7).

### 7.4 Deformation checks (rest-mode)
Arm from the hero pose to hanging: the sleeve must not pass through the panel seam or the glove cuff; elbow at 0°: folds flatten (the sim's folds are baked — in rest mode the elbow zone keeps 50 % of the fold relief; accepted for the animation-ready LOD, noted §10.3).

---

## 8. Evaluation protocol

### 8.1 Renders
`scripts/parts/10_combat_shirt_gaiter.py --eval` renders V1–V4 at 1024 × 1536 (hero frame, 64 spp adaptive 0.02, OIDN, ≈ 2–4 min each, research budget) and crops/upscales to the reference crops; V5–V8 at 800² 48 spp (20–40 s each) plus Workbench flat variants (5 s each). `--look` renders the 480 × 720 16 spp preset for geometry checks. Contact sheet `renders/10_combat_shirt_gaiter/sheet.png` (render | reference | 50 % blend | Sobel overlay) per view.

### 8.2 Garment-edge rows and silhouette
On V1/V2 (hero frame): for columns x ∈ {755, 775, 800, 825, 845} find the first row where the pixel class changes from skin (R − B > 25, lum > 40) to fabric; compare with §2.1 (±3 px). Dressed-silhouette rows (spec 04 §2.2 table) with the stand-ins: first/last column with lum > 45 at y 160, 200, 260, 300, 400 (±4 px). Arm crops: IoU of the sleeve+guard+glove mask (lum < 60 and not skin) against the reference's within the boxes (600,170)–(770,490) and (850,170)–(1000,490) ≥ 0.88.

### 8.3 Roll profile (`scripts/eval/measure_gaiter_rolls.py`)
Luminance profiles down the columns x 775, 800, 825 of V2 (hero light): local minima below lum 25 = crevices, local maxima = crests; require three crevices per column within ±3 px of §2.1 and monotone rising rows toward his left (tilt 12–18°). On the flat V5 variant: fit the silhouette of the stack seen from his right (camera (−0.9, −0.1, 1.55), 85 mm) and measure lobe heights 42 ± 6 / 28 ± 5 / 20 ± 4 and proudness 22 ± 4 / 16 ± 3 / 12 ± 3 mm at the front-right.

### 8.4 Micro-structure statistics
V3 high-pass 3 × 3 energy in (690–740, 195–245): 4–7 lum units (reference 5.1); V6: FFT of the rib panel's luminance along the wale-normal direction peaks at 4.2 ± 0.3 mm; V7: FFT of the ripstop zone peaks at 6.35 ± 0.2 mm in two orthogonal directions; V8: knit wale pitch 1.0 ± 0.15 mm (FFT), coverstitch row spacing 5.6 ± 0.4.

### 8.5 Colour patches
§5.7's 18 pixels, 5 × 5 means, ±10/255 per channel; the gaiter contrast ratio lum(760,155)/lum(835,160) ≥ 12; the shirt's maximum luminance in V1 within the shirt mask ≤ 130 (no bleached sheen); the gaiter's lit-fraction in the ROI (750–860) × (128–162) (spec 04 §8.2 metric 8) stays 0.27 ± 0.05 with the real gaiter in place.

### 8.6 Construction checks (closeups V5–V8, measured on the flat variants with `measure.py` ray grids)
Seam width 7.0 ± 0.5 and ridge height 1.2 ± 0.2 on three sampled sleeve seams; stitch rows 6.4 ± 0.4 apart, pitch 3.6 ± 0.3 (ripstop) and 5.6 / 2.5 (coverstitch); stitch cylinders sunk 0.10–0.20; elbow crests: right ≥ 4 at 8–15 mm pitch, left ≥ 3 at 10–18 (ray-cast height profile along the anterior elbow line); guard-band pinch: fabric height body + 1.45 ± 0.3 under the bands and ≥ body + 8 within 20 mm beside them; cuff inside the gauntlet by 20–30 mm; gaiter wall 3.0 ± 0.2, fold radius of the top hem 8–10, the inner ply present under roll 1, hems 12 ± 1 with two rows; side seam at the pleat; 300–400 pills on the top roll only.

### 8.7 Questions the critic must answer (yes/no, with the view that proves it)
1. Three fat fleece rolls and a band, not a stack of tori, not crinkles? (V2, V5) 2. Is the top edge a saddle — lowest at the front centre, highest back-left — and does it kiss the jaw shadow only there? (V2) 3. Do the straps visibly press the lowest roll flat on both sides while the centre hangs free? (V1, V2) 4. Does the gaiter's rim glow softly on the cool side (nap), and is the crevice between rolls 2 and 3 near black? (V2, V5) 5. Do the shoulders read ribbed under the pauldrons, with no ribs below the band? (V3, V4, V6) 6. Is the diagonal ridge on the left upper arm a seam that continues to the elbow, with fabric pulling across it? (V4, V7) 7. Are the inner-elbow folds right-arm-heavy (tighter elbow) and does the outer elbow stretch over a pocket? (V3, V7) 8. Does each sleeve vanish into its gauntlet with no gap, and do the guard bands pinch the fabric? (V3, V4, V7) 9. Is the exposed band dark knit that blouses above the waistband with the carrier's shadow on it, and is nothing of the body visible there? (V1, V8) 10. Would a Crye wearer recognise the shirt, would anyone recognise a fleece gaiter? 11. Is there anywhere a seam, stitch, rib or pill floats off the cloth or repeats visibly? (V5–V8)

### 8.8 Known failure modes to check for
Rolls as separate tori with visible gaps or a sawtooth profile (loft without the inner ply or without the relax); the top edge a flat ring (no saddle) hiding the lit neck strip or exposing the larynx; sheen bleaching the fleece or knit to grey (research F §0 — check the max-luminance criterion first); fuzz curves poking through the carrier; the rib wale direction wrong (horizontal) or ribs continuing onto the ripstop; the ripstop grid at 45° in UV instead of along the sleeve; sleeve sim exploding at the inner elbow (self-collision distance below 3 mm) or the cuff slipping out of the gauntlet (friction too low); stitches floating after the Armature (bind the stitch objects with `Surface Deform` **after** all other modifiers); the exposed band reading lighter than #3a3532 (that pixel was the magazine); the gaiter's inner wall intersecting the SCM when the head turns in rest-mode tests; the tier-3 band seam showing because the panel seam sits above the band (keep it at s 62 %, under the band's s 58–83 %).

---

## 9. Build order, effort and risks

### 9.1 Dependencies
Spec 04's rings/anchors/stand-ins and `Body.Collider` to the hyoid; spec 05's `Arm.*.SleeveCollider`, `Arm.*.CuffRing`, `Arm.*.GuardFrame`, `measure_arm()`; spec 09's `cloth_tube`, `gn_stitches`, `gn_wrinkles` helpers and the waistband ring; the materials library (`Thread.Black`, `measure_tile_pitch`); research A's texture sets `cotton_jersey`, `knitted_fleece`, `denim_fabric_05` in the manifest; spec 12/13/11 stand-in dimensions (bands, straps, gauntlet) — ours in §4.6/§4.9 until theirs exist.

### 9.2 Build order inside the script (idempotent; every step deletes and recreates its own objects by name)
1. Zone masks and bands (numpy, 2 s). 2. Torso + collar + hem, zone offsets, Solidify (5 s). 3. Panels: separate, UV, Subd 2, rib GN, apply (10 s). 4. Sleeve tubes, pin/seam groups, colliders and stand-ins (3 s). 5. Sleeve sims L and R on the posing arm, stability checks, apply (30–60 s). 6. Join `Shirt.Main`, seams/stitches GN, zip, tabs (10 s). 7. Gaiter loft with saddle and pleat, Solidify, relax 12 frames, apply, seam, hems, pills (15 s). 8. Masks bake (4 EMIT bakes at 2 k–4 k, ≈ 60 s). 9. Materials (1 s). 10. Weights, Armature, Surface Deform for stitches (5 s). 11. `--eval` renders: Workbench set ≈ 1 min; Cycles V1–V4 ≈ 10–14 min; V5–V8 ≈ 3 min (+ 1.5 min with `--fuzz`). Whole build without renders ≈ 3–4 min on 4 cores.

### 9.3 Stability checks on the sims (automatic, abort → fallback §4.12)
Per frame: max vertex speed < 2 m/s; no vertex nearer than 1.0 mm to the collider's surface after frame 50 (sleeves) / frame 10 (gaiter); max edge stretch < 15 %; final: cuff ring still inside the gauntlet stand-in (all ring vertices r < gauntlet r − 1 mm); elbow crest count per §8.6; gaiter: three lobes ± 6 mm, no lobe inverted.

### 9.4 Estimated script size
`10_combat_shirt_gaiter.py` ≈ 1 100 lines; `lib/cloth_tube.py` additions (`loft_profile`, saddle/pleat functions) ≈ 150; `lib/gn_stitches.py` additions (coverstitch, flatlock web, bar tack params) ≈ 80; `eval/measure_gaiter_rolls.py` ≈ 120; `eval/render_part10.py` ≈ 250. Three working sessions: (1) torso, panels, gaiter loft to the §8.2–8.3 metrics on Workbench; (2) sleeve sims, seams, stitches, materials, V5–V8 with the critic; (3) weights, rest mode, hero V1–V4 with stand-ins, colour calibration, critic round and fixes.

### 9.5 Risks and fallbacks

| Risk | Likelihood | Mitigation / fallback |
|---|---|---|
| The rib panel reads as corduroy (too deep) or vanishes (too shallow) at hero scale | medium | relief 0.6 is a starting value; tune 0.4–0.8 against the V3 high-pass metric; ribs are mesh so this is a GN parameter |
| Sleeve sim leaves too few elbow folds (sleeve too tight) or a sagging bag (too loose) | medium | ease table ±20 mm per station is a parameter; §6.3 adds explicit folds if the count is short; fallback §4.12 |
| Gaiter loft looks mechanical | medium | the relax, the Noise lumps, the saddle and pleat, the pills and the nap each break symmetry; if the critic still sees tori, run the push-down experiment on the GPU machine |
| Sheen bleaches the dark fabrics | high (seen in research F) | sheen ≤ 0.28, tinted; the ≤ 130 lum criterion catches it |
| Fuzz render cost in closeups | low | 80 k short thin curves; halve density if V5 exceeds 3 min |
| Neighbour parts' real dimensions differ from our stand-ins (straps, bands, gauntlet) | high | all stand-in dimensions are in one table (§4.6 step 5, §4.9 step 6) read from `assets/interfaces.json` once the owning specs publish theirs; re-run the sims (≈ 1 min) |
| Weight transfer twists the sleeve/panel junction | low | smoothing on the ring; the twist split follows spec 05 |
| Neck length changes in the critique pass (D14) | medium | only the seat ring moves; the saddle top ring is a pixel fact |

---

## 10. Interfaces and open questions

### 10.1 What neighbouring parts must provide or respect
* **Body (specs 03–05):** rings/anchors listed in §4.2; `Body.Collider` watertight from the hyoid to the crest; `Arm.*.SleeveCollider` = arm + 3 mm; neck girth 410 at the larynx and 460 at the base (our gaiter's inner wall is collar + 5); upper arm girth 345 ± 10 at s 62 %, forearm 310 ± 10 at s 25 %, wrist 179 ± 5 (the ease table assumes them).
* **Pauldrons (spec 12):** tier-1 cap's inner padding seats at **body + 2.5** on `Shirt.Band.CapSeat` (we are compressed to +2.3 there); tier-3 band 50 tall at humerus **s 58–83 %**, inner face body + 2.5, covering our panel seam at s 62 %; the band may bite 1 mm into our rib geometry (we flatten the ribs 70 % under it). **Lateral elbow cap:** sits on our elbow pocket's outer ply at pocket + 0; its elastic crosses the inner elbow over our folds (inner face at body + 6 there).
* **Forearm guards (spec 12):** elbow-end band at forearm **s 10–22 %**, wrist band at **s 86–96 %**, inner neoprene face at **body + 1.5**, plates at body + 4.5; our fabric is at body + 1.45 under the bands and bulges to body + 8–12 within 20 mm beside them — the guard's main plate must clear body + 12 along its edges or sit on the bulge (preferred: its padded sleeve absorbs it).
* **Gloves (spec 11):** gauntlet 30 tall from wrist −5 to −35 (i.e. 25 mm of our cuff inside), inner face at **body + 3.5**, outer at + 6.5; our cuff circumference 200 (closed tab) — the gauntlet's inner circumference ≥ 215 at the wrist.
* **Plate carrier and straps (spec 13):** front bag inner face at body + 1.3 (our compressed knit) → the bag's outer face at body + 31; straps' inner face at **body + 6** over the trunk and **body + 10** where they cross the gaiter's band (x 725–760 and 822–858 from y 160); the carrier's top edge at h 1470 posed must hide our gaiter's seat (lowest visible fleece ≈ h 1481); the cummerbund at body + 1.3 + its own thickness.
* **Trousers (spec 09):** our hem at h 850 inside; our knit at body + 1.3 under the waistband (spec 09 assumed +1.5; within tolerance) and the belt.
* **Face/head (spec 06), hair (07):** the chin's shadow falls on our top roll — nothing of ours above y 152 at x 790–810; the beard's neckline fades at the hyoid (1622 rest), 50 mm above our top edge at the front; no hair roots within 3 mm of our top ring (spec 04 §9).
* **Lighting/eval:** our albedos are part of the lighting calibration after the skin and the carrier; the gaiter's lit fraction metric of spec 04 §8.2 is re-run with the real gaiter.

### 10.2 What this part provides
`Shirt.Main`, `Shirt.Stitches`, `Shirt.Bartacks`, `Shirt.Zip`, `Gaiter.Main`, `Gaiter.Seam`, `Gaiter.Pills`, `Gaiter.Fuzz` (optional), `Shirt.Rest`/`Gaiter.Rest` (mode rest); vertex groups `Shirt.Band.*`, `Shirt.Zone.*`, `Shirt.Seam.*`, `Gaiter.Pin`, `Gaiter.Band` for the armour/carrier/glove specs to sample; the interface table `assets/interfaces.json` entries `shirt.*` and `gaiter.*` (offsets of §4.4, §4.11); helpers `cloth_tube.loft_profile`, coverstitch/flatlock recipes in `gn_stitches`, `measure_tile_pitch`, `measure_gaiter_rolls.py`.

### 10.3 Open questions for the client
1. **Rib shoulder panels** (as drawn, D4/D11) or a faithful Crye G3 (NYCO shoulders, bicep pockets with loop fields)? We recommend the panels: they carry identity on both shoulders and are physically plausible.
2. **Bicep pockets** omitted (D6) — restore them on the ripstop zone below the band (invisible under the pauldron tiers) for completeness?
3. **Elbow pads**: empty internal pockets with the external grey cap (as drawn, D12), or drop the external cap and put AirFlex pads inside the pockets (reality)? This decides spec 12's cap.
4. **Shirt tucked** (D13, consistent with spec 09 §10.3 question 3) — confirm.
5. **Gaiter construction**: deterministic loft (recommended, matches the measured rows) or the push-down simulation (truer physics, uncontrolled result) as the hero asset?
6. **Fuzz**: curves in closeups only (recommended) or always on (≈ +60–90 s per closeup, negligible at hero scale but exported geometry grows by 320 k points)?
7. **Thread colour**: black on both garments (recommended) or tan contrast on the ripstop?
8. **Dust level**: the reference shows a light dust film on the top roll and shoulders; keep, or a cleaner "fresh issue" look?
9. **Rest-mode folds**: keep the baked elbow folds at 50 % in the animation-ready export, or ship a second, straight-arm sleeve bake for games that re-pose the arm?
10. **Neck length** (D14, spec 04 question 7): the gaiter is built to the long neck as drawn; if the ANSUR neck is chosen, we move the seat ring up 28 mm and the stack shows 28 mm less — acceptable?
