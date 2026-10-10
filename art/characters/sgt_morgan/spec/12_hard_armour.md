# Part 12 — Hard armour: pauldrons, forearm guards, elbow caps, kneepad caps

Status: draft 1 (spec writer), 2026-10-07, written under the **reality-wins** rule (`CLAUDE.md`, Source of truth). Owner script: `scripts/parts/12_hard_armour.py` (plus `scripts/lib/armour.py` for the shell lofts, slot cutter, rim bead and rivet helpers, `scripts/lib/gear_hardware.py` for cam buckles and ladder-locks, `scripts/lib/mat_hard.py` for the worn-paint, brushed-metal and hardware shaders). Object prefixes `Pauldron.<L|R>.*`, `Guard.<L|R>.*`, `ElbowCap.<L|R>.*`, `Kneepad.<L|R>.*`; collection `Armour`; materials `Armour.Mat.*`; images `Armour.Img.*`.

Conventions (from `CLAUDE.md`): millimetres in this spec, metres in Blender; world frame **W** has its origin on the floor midway between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT = viewer's right**. Every "left/right" is the soldier's own. Four local frames are used, all written for the LEFT side; the right side is `mirror(X)` of every number unless a row says otherwise:

* **Frame A (upper arm)**: origin at the glenohumeral (GH) centre, rest W (+240, −20, 1452) (spec 04 §2.3 D3); +Z_A runs down the humerus to the elbow axis centre (340 mm, spec 05 §3.1), +X_A outboard (lateral), −Y_A anterior. A station **s %** is the fraction of the 340 mm humerus from the GH centre. Clock positions as in spec 05 (12 = anterior, 3 = lateral, 6 = posterior, 9 = medial, anatomical position).
* **Frame F (forearm)**: the empty `Arm.L.GuardFrame` of spec 05 (origin on the forearm axis at s 12 % = 32 mm distal of the elbow axis, +Y_F distal, −Z_F dorsal). Distances **d** are measured from the **elbow axis** along the forearm (so d = 32 at the frame origin); the forearm is 270 mm (spec 05 §3.3); clock positions 12 = flexor (anterior), 3 = radial, 6 = dorsal, 9 = ulnar.
* **Frame E (elbow)**: the empty `Arm.L.ElbowAnchor` (lateral epicondyle + 20 mm lateral, +Y_E distal).
* **Frame K (knee)**: origin at the knee axis centre, rest W (+93, 0, 523) (spec 08 §2.1; patella centre at Y −44), +Z_K up the shin, −Y_K anterior, +X_K lateral. Cap features are placed in the cap's **unrolled plane (u, v)**: u along the cap surface from its vertical centreline (+ lateral), v along the surface up from the cap's bottom edge.

Reference analysis: `notes/analysis_consolidated.md` §5 (Armour) and §9 disputes 10–11; `notes/analysis_gear_inventory.md` §5, §7, §13, §19–20. Research: `notes/research_prototypes.md` §3 (knee-pad cap prototype) and §8 (standard recipes), `notes/research_dimensions.md` §6–7 (buckles, pads), `notes/research_assets.md` (texture sets), `notes/research_blender_capabilities.md` §10 (baking). Zoom crops made for this spec: `ref/zoom_armour_{rpauldron_x8, lpauldron_x8, emblem_x16, strobe_x16, rguard_x10, lguard_x10, lelbow_x16, rknee_x8, lknee_x8, rknee_top_x16, lknee_tab_x16}.png` (made with `python3 -I` and PIL from `ref/reference_full.png`, Lanczos).

---

## 1. Purpose and acceptance

### 1.1 What this part is
Every rigid protective piece the soldier wears outside his clothing: two three-tier articulated shoulder guards ("pauldrons": cap plate, mid plate, bicep band) with their straps, links, rivets, the left one's shield-shaped emblem recess with its brushed-aluminium plate and white X-star mark, and the clip-on strobe on the left mid plate; two segmented forearm guards (elbow band, main plate, wrist band on a neoprene sleeve over foam pads, two 25 mm straps each with a cam buckle and a ladder-lock, the right one's smudged stencil, the left one's grey inset window); two small two-piece grey lateral elbow caps on 25 mm elastic; two hexagonal hard-cap kneepads (tan bevelled frame around a recessed pitted centre, vent slots, D-slot, moulded boss, side slot, red rubber tab, black neoprene base, rear 38 mm strap with a gunmetal ladder-lock). It owns the shared desert-tan worn-paint polymer material with its chipping, scratch and dust recipe, the brushed-plate, silver and gunmetal hardware materials, the decal masks (emblem, stencil), the attachment helpers that ride the deltoid, forearm, elbow and knee, and the stand-in proxies the cloth parts (specs 09, 10) collide with. It does **not** own the plate carrier and its shoulder straps (spec 13, which the pauldron tab hooks to), the shirt and trousers it sits on (specs 10, 09), the gloves (spec 11), the antenna behind the left shoulder (spec 13) or the body (specs 03–05).

### 1.2 What "perfect" looks like
At hero distance (46 mm lens at 4.5 m) the pauldrons read as one tan material on both shoulders — the left one blue-grey only because the cool left light falls on it — three stepped plates per shoulder with pale dust on their upper faces and bright worn bevels, a lighter blue-grey shield plate with a weathered white X-star on the left cap, a small pale strobe clipped to the left mid plate, black elastic and a glint of silver at each bicep band; the forearm guards as curved, segmented, grooved tan plates that pinch the sleeves and vanish under the glove gauntlets; the kneepads as heavy angular caps whose centres are flaked to dark substrate while their frames stay tan and dusty, a rose-red tab on the left cap's outer edge. In a 250 mm-wide closeup every plate has a visible 2.5–3.5 mm wall at its edge and slot cuts, a raised rim bead, an orange-peel paint surface with hairline scratches, chips with a lit paint step at every flake border, dust only in the up-facing texture, rivet heads with a 0.3 mm shadow ring, brushed-metal anisotropy on the emblem plate, a translucent lens on the strobe, strap ends folded and bar-tacked, buckles made of 3–4 mm stamped bars with worn bright edges, and nothing hovering, nothing intersecting the cloth under it. A critic who knows sport and military armour cannot name a dimension wrong by more than the tolerances of §8.3, cannot find a plate without a wall thickness, a slot without a floor shadow, a strap that goes nowhere, or a chip without an edge.

### 1.3 Closeup render views (definitions for the render harness, `scripts/eval/views.py`)
All positions in W (mm), 36 mm sensor, 2048² unless stated; "hero camera" = (0, −4500, 600), rotation (93.9°, 0, 0), 46 mm (consolidated §8). Hero-camera views are rendered full-frame, cropped to the stated box and upscaled ×3 Lanczos to match the crop files. Posed piece centres (§7.1) are read from the empties at run time; the numbers below are the expected values.

| View | Camera position | Target | Lens | Compared with | Checks |
|---|---|---|---|---|---|
| V1 `torso_ref` | hero camera | — | 46 | `ref/crop_torso_vest.png` = ×3 of (630,140)–(990,490) | both pauldrons in context: tiers, bands, emblem, strobe, tab to the strap, L/R colour under the two lights |
| V2 `arm_R_ref` | hero camera | — | 46 | `ref/crop_arm_right_viewerleft.png` = ×3 of (600,170)–(770,490) | right cap wedge, studs, slot, tier 2 recess, band + silver cam buckle, right forearm guard rings, grooves, stencil, buckle |
| V3 `arm_L_ref` | hero camera | — | 46 | `ref/crop_arm_left_viewerright.png` = ×3 of (850,170)–(1000,490) | left cap, emblem plate and X-star, strobe, tier 2 grille, left guard rib and window, ladder-lock, elbow cap fin and pad |
| V4 `legs_ref` | hero camera | — | 46 | `ref/crop_legs_knees.png` = ×3 of (630,550)–(990,830) | both kneepad caps: outline, frame/centre contrast, slots, tab, strap and buckle, cool/warm split |
| V5 `pauldron_L_close` | (+700, −450, 1600) | (+260, −30, 1435) | 85 | `ref/zoom_armour_lpauldron_x8.png` | tier geometry, rim beads, rivet, grille, strobe box and clip, band and elastic |
| V6 `pauldron_R_close` | (−700, −430, 1560) | (−237, −30, 1441) | 85 | `ref/zoom_armour_rpauldron_x8.png` | wedge facets, two studs with speculars, slot, tier 2 recess and outer slot, cam buckle |
| V7 `guard_R_close` | (−560, −620, 1420) | (−318, −60, 1190) | 85 | `ref/zoom_armour_rguard_x10.png` | three rings end-on, grooves, rib, stencil, cam buckle hook, neoprene step |
| V8 `guard_L_close` | (+640, −560, 1250) | (+212, −140, 1053) | 85 | `ref/zoom_armour_lguard_x10.png`, `ref/zoom_armour_lelbow_x16.png` | rib, window, lower band, ladder-lock strap, elbow cap fin + pad + elastic |
| V9 `knee_L_close` | (+420, −760, 700) | (+165, −200, 520) | 85 | `ref/zoom_armour_lknee_x8.png`, `ref/zoom_armour_lknee_tab_x16.png` | octagon outline, frame step, pitted centre, slots and holes, red tab, corner triangles |
| V10 `knee_R_close` | (−600, −500, 650) | (−180, −50, 525) | 85 | `ref/zoom_armour_rknee_x8.png`, `ref/zoom_armour_rknee_top_x16.png` | cap in 45° view: bulge, wall, top slots, D-slot, boss, bottom C-slot, strap + ladder-lock + tan tail |
| V11 `emblem_macro` | (+600, −300, 1480) | (+300, −60, 1430) | 100, DOF f/5.6 on the plate | `ref/zoom_armour_emblem_x16.png`, `ref/zoom_armour_strobe_x16.png` | shield recess, border groove, brushed anisotropy, X-star strokes and their abrasion, strobe lens |
| V12 `turntable_<piece>` | 4 views at 0/90/180/270° azimuth, 25° elevation, 600 mm radius, look-dev HDRI (§8.1) | piece centre | 60 | §3 tables | each piece alone: walls, slots, straps, hardware, wear distribution |

### 1.4 Pass criteria a critic can score (full list and metrics in §8.3)
1. `measure_armour()` (§8.2) reports every outer dimension of §3 within ±3 mm, every wall thickness within ±0.3 mm, every slot within ±1 mm, every hardware body within ±1 mm.
2. V1–V4 overlays: pauldron, guard and cap silhouettes inside their reference boxes with IoU ≥ 0.85 (caps), ≥ 0.80 (guards, pauldrons); the padded shoulder width at y 205 = 320 ± 6 px.
3. Same material both sides: in V1 the right cap's lit face median lies within ΔE 8 of #90877c and the left cap's within ΔE 8 of #828080; swapping the two lights in the test scene (§8.1) swaps the readings within ΔE 6 — the asymmetry is lighting, not albedo.
4. Emblem plate median within ΔE 8 of #aabacc, strobe lens within ΔE 8 of #afc1d3; both read as the two lightest objects on the figure after the face.
5. Every plate shows wall thickness at its edge and inside every slot (V5–V10); no plate reads as a zero-thickness shell.
6. Chips: 30–40 % of each kneepad centre panel flaked, 3–8 % of frames and pauldron faces, 10–15 % of the forearm-guard ribs; every chip border has a visible paint step (bump) in V9/V10; no soft blotches.
7. Dust only on faces whose normal has +Z ≥ 0.4; grime only in slots, grooves and the lower 20 mm of each kneepad; stencil smudged, 50–60 % legible.
8. Hardware: cam buckles and ladder-locks are frames of 3–4 mm bars with straps passing through, worn bright edges, correct count (2 cam buckles, 4 ladder-locks, 2 pauldron cam buckles); every strap end folded 15 mm and bar-tacked; no strap floating more than 0.5 mm off the surface it crosses.
9. Attachment: inner padding faces at the offsets of §7.2 (±0.5 mm) against the shirt and trousers; zero intersections in the flat variant (§8.4); in the hero pose the pauldrons ride the deltoid (cap tilts with 50 % of the arm swing), the guards follow 60 % of the forearm twist, the caps follow 70 % of the shin.
10. Free judgement (0–2): would a soldier who has worn Hatch, Alta or Crye hard armour accept these as real injection-moulded pieces, strapped on a real arm and knee?

---

## 2. Reference observations

### 2.1 Pixel observations (full-image coordinates, 1672 × 941; 2.12 mm/px at the figure; colours are 5 × 5 sRGB means sampled for this spec unless marked "analyst")

| Piece / feature | Pixels | Size (px → mm, projected) | Colour | Reading |
|---|---|---|---|---|
| R cap plate (tier 1) | x 668–718, y 190–240 | 50 × 50 → 105 × 105 | lit face #90877c (690,205) (analyst #a3998d), rim #c3b5a6 (672,222), underside #453d3b | angular wedge sloping down and outboard; seen nearly edge-on from the key side → appears small |
| R cap studs | (700,200), (683,228) | ≈ 3 px → 6–7 mm heads | #443e3a / #141311 cores with bluish-white speculars (analyst) | two dome rivet heads 36 mm apart, one on the top facet, one low on the outer face |
| R cap slot | (710,195) | 7 × 2 px → 15 × 4 | #362e29 | through-slot near the top inner corner: the webbing-tab exit |
| R tier 2 | x 655–700, y 245–285 | 45 × 40 → 95 × 85 | #665547 (678,265); recess #47413c, shadow #090605 | plate with a rectangular recessed panel; dark slot at its outer-lower edge (649–655, 272–280) |
| R tier 3 band | x 640–690, y 285–325 | 50 tall projected → 50 mm band on a tilted cylinder | #534c45 (665,305); buckle #98897b (644,309) | tan shell with a mid groove; black elastic; silver cam buckle at the outboard-anterior end |
| L cap plate | x 895–960, y 185–250 | 65 × 65 → 135 × 135 | #828080 (915,200), #45484c (925,235), rim #47413d (898,215) | the same cap seen frontally and nearer; cool-lit; tan rim where lit |
| L cap rivet | (905,205) | 4 px → 8 mm | #454038 | the top-facet stud of the right cap, mirrored |
| L cap lower dot | (943,243) | 2 px | near black | the low outer stud, mirrored |
| Emblem recess | x 932–957, y 195–240 | 25 × 45 → 52 × 95 | plate #aabacc (942,212), border #596472 (933,220), mark #b4c5d3 (944,218) → white | shield: straight top, sides converging to a rounded point; thin dark border; brushed plate, vertical brush, brighter at the top; X of two strokes + a short vertical spike below the crossing; strokes broken by wear |
| L tier 2 | x 912–960, y 252–290 | 48 × 38 → 100 × 80 | #545960 (930,270) | horizontal recess; three short vertical vent slots at the upper inner corner (≈ 913–922, 256–262); small dark window near the bottom inner corner (≈ 918–924, 286–290) |
| Strobe box | x 945–960, y 258–280 | 15 × 22 → 30 × 45 | face #afc1d3 (952,268), edge #a1b5cc, tan clip at its lower inboard corner | tilted ≈ 12° to the plate's vertical; flat translucent face, dark bevelled rim, tan bracket |
| L tier 3 band | x 905–965, y 290–335 | — | #1f2024 (935,310); slot #292a30 (935,320) | mostly in the plate's shadow; horizontal groove; ribbed knit yoke ends at it |
| R forearm guard | x 625–700, y 308–358 | 75 × 50 → 160 × 105 | lit #cdb8a6 (655,328), groove #796858 (665,345), stencil #a4907e (667,338), elbow band #a28e7c (632,330), buckle #baa18e (636,320), wrist band #847061 (692,340) | three rings seen end-on (the forearm points at the camera, 58° out of plane): elbow band with a silver cam-buckle hook at its outboard edge, main plate with two longitudinal grooves and a raised rib, wrist band under the glove cuff |
| L forearm guard | x 880–945, y 360–435 | 65 × 75 → 135 × 160 | upper #666265 (912,375), main #4c5059 (912,400), window #51565e (905,407), lower #4a5a6c (920,428), strap #383a3c (930,432) | the same guard seen from its dorsal side 13° out of plane: longitudinal rib, grey inset window, wrist band with a black strap and ladder-lock |
| L elbow cap | x 950–968, y 335–365 | 18 × 30 → 40 × 65 | fin #9aa8b5 (958,342), pad #515c67 (960,358), elastic #1d2125 (952,350) | slim bright fin above a square pad, on the lateral elbow; black elastic |
| R kneepad cap | x 695–760, y 615–700 | 65 × 85 → 135 × 180 | frame #5a514b (703,650) / #695f5a (710,640), centre #272420 (718,660), D-slot #4c3f33 (727,625), rect slot #726156 (705,622), boss #060808 (745,632), bottom slot #0c0b0d (740,690), strap #111011 (758,650) | hexagonal cap at 45°; wide bevelled frame; heavily flaked centre; rect slot and D-slot on the top frame, boss upper-medial, C-shaped slot lower-medial; black strap with gunmetal ladder-lock and a tan tail on the medial side |
| L kneepad cap | x 862–940, y 610–700 | 78 × 90 → 165 × 190 | frame #6e6763 (870,625) / lit tan #826e5b (872,640), centre #343432 (893,655), top slot #3f3935 (880,615), side slot #303131 (936,660), tab #695b5f (927,640) / #423f44 (928,648) | the same cap frontal: octagonal outline, double-step frame, long vent slot top-medial, two small holes top-lateral, rhombus slot on the lateral frame, rose-red tab on the lateral edge, bottom slot, triangular corner indents |

### 2.2 What the zooms add (my readings)
* The right cap's "wedge" and the left cap's "rounded plate" are one shape: a plate bent over the shoulder with a 30 mm-radius bend between a short near-horizontal inner flange and a long outer face; the key light rakes the right one's bend edge-on and makes it look faceted. Both show the pale rim bead all round.
* The left tier 2's three vent slots and bottom window are not visible on the right tier 2 (in shadow, 95° turned) — one design, mirrored.
* The strobe's face is uniform and lighter than anything else on the figure; its lower inboard corner shows a tan triangle — a moulded clip bracket, not fabric.
* The forearm guard's "grooves" run along the forearm axis (in the image they run elbow → wrist); the rib is longitudinal too. The right guard's elbow band shows a raised lip and the buckle's hook as a bright 4 px (8 mm) tongue.
* The kneepad frame has two steps: an outer rounded lip and, 7 mm inside it, a 45° wall down to the centre panel — the centre is a second hexagon.
* The red tab is a rounded-ended vertical tab on the lateral edge of the left cap, ≈ 30 mm long, protruding beyond the frame.
* The kneepad strap/buckle is on the **medial** side of both knees (right cap: viewer's right edge = his left = medial; left cap: "inner side" per the analyst).

### 2.3 Ambiguities and decisions (reality wins; "as drawn" is kept only where plausible and identity-bearing)

| # | Topic | As drawn / as analysed | Reality | Decision |
|---|---|---|---|---|
| D1 | Pauldron colour L vs R | left grey-blue, right tan; consolidated: same tan, lighting | one product is one colour | **Same `Armour.Mat.TanPolymer` on all pieces**; the test scene (§8.1) must reproduce the grey-blue by light alone |
| D2 | Pauldron size | R 105 × 105, L 135 × 135 projected | a pair is one size | **One cap 125 × 130 mm, mirrored**; the difference is distance and angle (verified by the V1 overlay) |
| D3 | Emblem and strobe | left only | unit insignia is worn on the left shoulder (US practice); one IR strobe per soldier | **As drawn: left only** |
| D4 | Emblem mark | X-star as rendered (consolidated #2) vs the UI faction logo | — | **X-star**, client question §10.3 |
| D5 | Elbow cap | left visible, right hidden; consolidated: mirror (best) or omit | pads come in pairs | **Mirrored to the right** (hidden behind the stock; costs nothing) |
| D6 | Elbow cap size 40 × 65 | implausibly small for a protective elbow cap (real 100–180 mm) | — | **Kept as drawn** (identity; physically possible as a lateral epicondyle guard); client question §10.3 |
| D7 | Kneepad slot pattern | R and L differ (rect+D top slots vs long slot + holes) | handed pair (strap on the medial side of both) is mirrored, so its slots mirror too | **Left cap is the master; right = mirror(u)**; the right's drawn slots are within 10 mm of the mirrored positions at 45° and are not scored |
| D8 | Red tab | left cap only | a pair carries the same tab | **Both caps, lateral side**; on the right knee (externally rotated 45°) it faces away from the camera, consistent with the image |
| D9 | "Square bolt" on the right cap | bolt head | a bolt through a knee cap is not real; caps are riveted/overmoulded at the edge | **Moulded square boss 7 × 7 × 1.5**, no grommets (none drawn) |
| D10 | Kneepad in the "knee sleeve" | spec 09 puts the cap inside its pocket (inner = cap + 2) | the image shows a bare cap on a black base: an external pad (Alta/Hatch/AirFlex Field class) strapped over the knee pocket | **External pad**: cap on a 4 mm neoprene base sitting on the pocket's outer face; spec 09 keeps its pocket as the bed (§10.1) |
| D11 | Forearm guard length | R box 160 × 105 and L 135 × 160 projected | the forearm is 270 mm; sport guards 220–260 long | **225 mm (d 32–257)**, derived from the forearm, not from the boxes |
| D12 | Tier 3 band height/station | "≈ 50 mm" at y 285–325 (85 px projected incl. the ellipse) | — | **50 mm tall, s 63–77 %** (just above the elbow, where the ribbed yoke ends); spec 10's s 58–83 % is corrected (§10.1) |
| D13 | Grey inset window | left guard only | an accessory (ID window) need not be paired | **Left only, as drawn** |
| D14 | Pauldron tiers' link | "elastic/rivets on the inner side" | lame armour hangs lower plates from the upper by riveted straps | **Two 25 mm elastic links per shoulder, riveted (the studs), 20 mm exposed** |
| D15 | Thigh shortness (consolidated §1) | as drawn | ANSUR | irrelevant to this part except that the knee axis is Z 523 (spec 08), which the drawn knee pixels already match |

---

## 3. Real-world reference

### 3.1 Identity of each piece and the product class built to
| Piece | Closest real class | Why | Status |
|---|---|---|---|
| Pauldrons | Injection-moulded sport shoulder armour (motocross / MTB body-armour shoulder cups, lacrosse shoulder caps with floating bicep guards) in the construction of a medieval spaulder: lames hung from each other on riveted straps | No issued military pauldron exists; sport armour gives shell thickness, rim beads, rivet and strap practice; the lame construction gives the three-tier articulation drawn | class estimated |
| Forearm guards | Riot-control forearm protector of the Hatch Centurion type: hard polycarbonate/PP plates on a padded neoprene sleeve, two straps, buckles [VERIFY: Hatch CF2500 dimensions] | Segmented plates, sleeve and strap layout match the drawing | class estimated; length range sourced (research D §7: 220–260 long, 130–195 wide, 10–16 thick) |
| Kneepad caps | Hard-cap tactical knee pad: Crye AirFlex Combat (one size, flexible TPU cap, no dims published, sourced), Alta AltaFlex 229 × 165 × 38 with 12.7 mm foam (sourced), Hatch XTAK | Hexagonal cap over a black base with a rear strap is exactly this class | sourced sizes; our cap width 160 sits between Alta's 165 and the drawn 135–165 |
| Elbow caps | No real product at 40 × 65 mm; nearest is a lateral epicondyle guard. Built as drawn (D6) | identity | estimated |
| Hardware | ITW/Nexus-class acetal and stamped-steel buckles; semi-tubular dome rivets; MIL-W-17337-class 25 mm webbing; 38 mm knitted elastic | research D §6 (no buckle dims published; typical values uncited) | estimated |
| Strobe | Compact personal IR/visible strobe of the Adventure Lights VIP / Guardian class, ≈ 48 × 32 × 20 mm, translucent polycarbonate case on a clip [VERIFY] | the drawn 30 × 45 pale box with a tan clip | estimated |
| Shell material | Injection-moulded PP/PE or PC, 2.5–3.5 mm, painted desert tan (FS 33446-class) over a dark grey-brown substrate | the chips show the dark substrate, so painted not pigmented | estimated |

### 3.2 Pauldron (left; right mirrored). Frame A unless stated

**Tier 1 — cap plate `Pauldron.L.Tier1.Cap`** (developed, i.e. measured along the surface)
| Quantity | Value (mm) | Status |
|---|---|---|
| Developed height, inner edge → bottom lip | **130** | measured (L 135 projected, R 105 edge-on) |
| Width (anterior–posterior) at the bend / at the bottom lip | **125 / 100** (trapezoid; the two lower corners chamfered 25 at 45°) | measured (L 135 incl. perspective) |
| Inner flange | 15 long, tilted 10° below horizontal toward the neck, top edge straight | estimated |
| Bend | radius 30, through 65° | estimated from the L/R appearance (§2.2) |
| Outer face | 70 long, 70° below horizontal, slightly convex (R 400 in the A-P direction) | estimated |
| Bottom lip | 11 long, turned inward 15° | estimated |
| Corner radii (plan) | 12 | estimated |
| Wall thickness | **3.0** | estimated (sport shell) |
| Rim bead | 5 wide, 1.2 proud, outer radius 1.0, inner blend 2.0; all round | measured (3 px pale rim) |
| Webbing-tab slot | 16 × 5 through, 8 from the inner edge, 20 from the anterior edge; floor edges radius 1 | measured (710,195) |
| Stud 1 (dome rivet) | head Ø 7.0, 2.2 proud, on the inner flange/bend 30 from the inner edge, 12 anterior of centre | measured |
| Stud 2 (dome rivet) | head Ø 7.0, 2.2 proud, on the outer face 14 above the bottom lip, 8 posterior of centre | measured |
| Seat | inner padding (6 mm closed-cell foam, `Pauldron.L.Tier1.Pad`, 20 mm ring inside the rim) at **shirt + 0.2 = body + 2.5** on `Shirt.Band.CapSeat` (spec 10 §10.1) | interface |
| Position | inner edge 60 outboard of the GH centre (X_A +60), bend crest over the acromion–deltoid saddle (X_A +95, s 8 %), bottom lip at s 25 % (85 below the GH), plate centred at Y_A −10 | measured (spec 04 §2.4 boxes) |

**Emblem recess `Pauldron.L.Tier1.EmblemRecess` + plate `Pauldron.L.Tier1.EmblemPlate` (left only)**
| Quantity | Value (mm) | Status |
|---|---|---|
| Outline | shield: straight top 50 wide; sides converge 8° for 70; bottom a rounded point, radius 18; total **95 tall** | measured (25 × 45 px) |
| Position | vertical centreline 8 anterior of the cap centre; top 12 below the bend start (so it spans the bend's lower half and the outer face) | measured |
| Recess depth / border groove | 1.5 deep; groove 1.5 wide × 1.0 deep around the plate, floor radius 0.5 | estimated ("thin dark border" 1 px) |
| Plate | 1.0 thick 5052-class aluminium, brushed vertically (Ra 0.4–0.8 µm equivalent), bent to the cap curvature, face 0.5 below the cap face, 4 countersunk Ø 2 blind rivets at the corners (flush, visible as 0.1 mm rings) | estimated |
| X-star mark | white paint 25 tall: long stroke (−8, +13) → (+7, −11), short stroke (+9, +10) → (−6, −8), both 2.4 wide, square ends; spike (0, −3) → (0, −12), 1.8 wide; coordinates in plate mm, origin at the plate's vertical centreline, 55 % up from the bottom point; 35 % of the paint abraded | measured (12 px tall), abrasion estimated |

**Tier 2 — mid plate `Pauldron.L.Tier2.Plate`**
| Quantity | Value (mm) | Status |
|---|---|---|
| Extent | s 28–52 % (95–177 below the GH), **80 tall**; arc 100 (≈ 95° at the inner radius) centred at 3 o'clock, i.e. the lateral face | measured |
| Inner radius | upper-arm half-section at s 40 % (girth 352 → r 56) + shirt 1.5 + 6 mm pad = **63.5** at the pad face, plate inner 69.5, outer **72.5** | derived (spec 05 §3.2) |
| Wall / rim bead | 3.0 / 4 wide, 1.0 proud, radius 0.8 | estimated |
| Recessed panel | 70 × 28, 1.5 deep, corner radius 4, centred 32 below the top edge | measured |
| Vent grille | 3 through-slots 3 × 9 at 6 pitch, upper inner corner (12 from the top, 10 from the posterior edge) | measured (L) |
| Rivet | dome Ø 7, 2.2 proud, 12 from the top, 14 from the anterior edge | measured (L) |
| Strap-exit slot | 12 × 5 through, 8 above the bottom edge at the anterior corner | measured (R) |
| Bottom window | 8 × 6 through, 6 above the bottom edge, posterior third | measured (L) |
| Overlap | top edge 10 under tier 1's bottom lip (lame rule: upper over lower); hung by two links | construction |

**Strobe `Pauldron.L.Tier2.Strobe.{Body,Lens,Clip}` (left only)**: box 45 tall × 30 wide × 18 deep, corner radius 3, walls 1.5; front 36 × 24 lens 2 thick in a 1.5 mm dark bevelled rim; body dark grey polymer; rotated 12° (top toward anterior) on the plate's outer face, lower edge 14 above the plate's bottom, centred 60 % of the arc toward anterior; clip = tan plate 34 × 20 × 3 behind the box with a 10 × 3 hook that engages the plate's recessed-panel edge (status: box measured, construction estimated).

**Tier 3 — bicep band `Pauldron.L.Tier3.{Shell,Elastic,CamBuckle,Keeper}`**
| Quantity | Value (mm) | Status |
|---|---|---|
| Station / height | s 63–77 % (214–262 below the GH), **50 tall** | measured (D12) |
| Shell arc | 200° centred at 3 o'clock (lateral), i.e. from 11:40 to 6:20; inner radius = half-section at s 70 % (girth 310 → r 49.3) + 1.5 + 2.5 pad = **53.3**; wall 2.5 | derived |
| Shell detail | mid-height groove 2 × 1 (the "horizontal slot"); rim bead 3 wide 0.8 proud; two strap slots 40 × 4 at 8 mm from each shell end | measured |
| Elastic | 38 wide × 1.8 black knitted elastic across the medial 160°, sewn through the posterior slot, free end through the cam buckle | estimated |
| Cam buckle | silver, 36 × 30 × 11 frame, 25 mm bar gap, lever 24 × 14 × 3 with a 1 mm serrated edge; riveted to the shell's anterior end; strap keeper 25 × 12 webbing loop beside it | estimated (research D: no published dims) |

**Links and tab**: `Pauldron.L.Link.Ant/Post` 25 × 1.5 black elastic, 20 exposed between tier 1's lip and tier 2's top at 30 % and 70 % of the arc, each end under a stud/rivet; `Pauldron.L.Tier1.Tab` 25 × 1.3 black webbing, 60 long, from under the inner flange through the tab slot to the shoulder strap of spec 13, 25 × 20 hook-and-loop end (status estimated).

### 3.3 Forearm guard (left; right mirrored). Frame F, d from the elbow axis
| Component | d range | Arc / width | Thickness | Detail | Status |
|---|---|---|---|---|---|
| `Guard.L.Sleeve` neoprene | 27–262 (s 10–97 %) | full tube | 3.0; inner at **body + 1.5** | 10 mm bound edges 1.0 proud; seam at 12 o'clock, 2 mm flatlock | estimated |
| `Guard.L.Foam.{Elbow,Main,Wrist}` EVA | plate outline − 3 | plate arc − 6° | 4.0 (inner +4.5, outer +8.5) | dark grey, visible as a step under each plate lip | estimated |
| `Guard.L.Plate.Elbow` | **32–66** (34 long) | 230° centred at 6 o'clock | 2.5 | rim bead 3/0.8; cam buckle (silver, as §3.2) riveted at the 3 o'clock end; strap slot 27 × 4 at the 9 o'clock end; keeper loop beside the buckle | measured R (625–645) |
| `Guard.L.Plate.Main` | **62–224** (162 long) | 200° centred at 6 o'clock | 3.0 | two longitudinal grooves 3 wide × 1.2 deep at ±22 arc from 6 o'clock, d 74–212, rounded ends; central rib 14 wide × 2.5 proud, d 70–216, 45° flanks, ends radius 7; rim bead 3/0.8; edge chamfer 1.0; proximal edge 4 under the elbow band's lip, distal edge 4 over the wrist band | measured ("two grooves", "raised rib") |
| Stencil (R only visible; both guards) | centred d 150 | between the rib and the radial groove (4–5 o'clock) | decal | 32 × 15 block, 3 glyphs 9 tall, 2 stroke, stencil bridges, smudged (§5.6) | measured (660–675 × 335–342) |
| `Guard.L.Window` (left only) | d 175–195 | ulnar side, 7:30 | recess 1.0; insert 0.8 | 10 × 20 rounded-rect, grey polymer insert, face 0.2 below the plate | measured (905,407) |
| `Guard.L.Plate.Wrist` | **220–257** (37 long) | 230° centred at 6 o'clock | 2.5 | rim bead 3/0.8; ladder-lock (gunmetal 38 × 32 × 6) riveted at 3 o'clock; strap slot 27 × 4 at 9 o'clock; distal edge meets the glove gauntlet (spec 11) at d 257 = wrist −13 | measured L (420–435) |
| `Guard.L.Strap.{Elbow,Wrist}` | at the band centres | 25 × 1.3 black webbing | — | from the 9 o'clock slot across the flexor side over the sleeve to the buckle; tail 40 folded, bar-tacked | estimated |
| Plate inner surface | — | — | — | **body + 8.5** everywhere (over sleeve 3 + foam 4); outer +11.0/+11.5 | interface (§10.1) |
| Forearm girths used | s 12 / 40 / 90 % | 290 / 285 / 195 over the sleeve (spec 05 §10) | — | sections are ellipses 100 × 85 at s 25 % → 62 × 42 at the wrist (spec 05 §3.3) | sourced/derived |

### 3.4 Lateral elbow cap (both sides, D5). Frame E
| Component | Size (mm) | Position | Status |
|---|---|---|---|
| `ElbowCap.L.Fin` | lens 40 tall × 14 wide × 2.5, ridge 3 proud along its axis, pointed ends radius 2 | centre 16 proximal of the elbow axis, 22 lateral of the epicondyle (= anchor + 2) | measured (950–965, 335–350) |
| `ElbowCap.L.Pad` | rounded square 30 × 28 × 2.5, corner radius 6, dome +3 | centre 16 distal of the axis, same lateral offset; gap to the fin 4 | measured (952–968, 350–365) |
| `ElbowCap.L.Backing` | 1.5 neoprene, 50 × 80, radius 10 | under both, on the shirt's elbow pocket outer ply + 0 (spec 10 §10.1) | estimated |
| `ElbowCap.L.Elastic` | 25 × 1.5 black, one turn around the elbow at the axis, inner face body + 6 over the inner-elbow folds (spec 10) | sewn to the backing's medial edges | estimated |

### 3.5 Kneepad (left is the master; right = mirror(u), D7). Frame K and unrolled (u, v)
**Cap `Kneepad.L.Cap`**
| Quantity | Value (mm) | Status |
|---|---|---|
| Outline (unrolled), octagon, corner radii 6 | bottom edge u ±62.8 at v 0; lower chamfers 30 long at 55° to (±80, 24.6); vertical sides to (±80, 164.6); upper chamfers 35 at 45° to (±55.3, 189.3); top edge 110.6 wide → **160 wide × 190 tall** | measured (L 165 × 190) |
| Wrap | 150° around the knee axis; the cap's unrolled u maps to arc length at radius 78 (= knee half-breadth 52 [estimated from ANSUR knee breadth ≈ 104] + trousers/pocket 6 + base 4 + bulge) | estimated |
| Side profile | inner surface on the base at v 10–30 and v 160–180 (contact bands); forward bulge **30** at v 95 (over the patella); upper third tilted 15° back over the thigh, lower third 12° back over the shin | measured (bulge "≈ 2 cm" projected at 45°) |
| Wall | **3.5** | prototype |
| Frame | 12 wide: outer lip bead radius 2.5 (1.8 flare, as the prototype), flat 7, inner 45° wall 2.0 down to the centre | measured (6 px) |
| Centre panel | frame outline offset −12; recessed **2.0**; pitted (displacement noise 0.3 mm, Voronoi flakes §5.4) | measured |
| S1 long vent slot | 18 × 4 rounded ends, centre (−40, 182) on the top frame (medial) | measured (880,615) |
| S4 D-slot | 10 × 8, flat side down, centre (+15, 184) | measured (727,625 on R, mirrored) |
| S5 corner slot | 8 × 4, centre (−72, 170) at the medial upper chamfer | measured (695–697, 616–621 on R) |
| H1, H2 drain holes | Ø 3.5 at (+33, 178), (+42, 165) | measured |
| S2 side slot | rhombus 12 × 6, centre (+72, 95) on the lateral frame | measured (936,660) |
| S3 bottom slot | 12 × 5, centre (+10, 12) on the bottom frame | measured (895,690) |
| S6 C-slot | 12 × 8 C-shape (strap keeper), centre (−60, 20) medial lower chamfer | measured (740,690 on R) |
| B1 boss | square 7 × 7 × 1.5 proud, chamfer 0.6, centre (−45, 160) | measured (745,632 on R) |
| N1–N3 corner indents | equilateral triangles side 6, 0.8 deep, at the lateral upper chamfer, medial lower chamfer, lateral lower chamfer | measured |
| T1 red tab `Kneepad.L.Tab` | 10 wide × 30 long × 3, rounded end r 5, rooted under the lateral frame at v 115–145, protruding 6 beyond the frame edge, rose-red rubber | measured (925–930, 636–652) |
| Strap slot (hidden) | 40 × 5 at (−75, 95) under the medial lip, for the ladder-lock's anchor loop | construction |

**Base, strap, buckle**
| Component | Size (mm) | Status |
|---|---|---|
| `Kneepad.L.Base` | 4.0 black neoprene, outline = cap outline + 12 margin (184 × 214), corner radii 15, bound edge 8 wide 0.8 proud; inner face on the knee pocket's outer surface + 0 (D10) | estimated (Alta 12.7 foam is inside the cap; the visible margin is the thin flange) |
| `Kneepad.L.Strap` | 38 × 1.8 black elastic, sewn to the base's lateral edge at v 85–125, around the back of the knee at h 530–550 (spec 09 §10.1), through the ladder-lock on the medial side; tail 50 of **tan 38 mm webbing** sewn to the elastic end (the "brass-tan tab" at (750–760, 652–662)), folded 15, bar-tacked | measured (20 px tall) |
| `Kneepad.L.LadderLock` | gunmetal 52 × 44 × 6, two 3.5 mm bars, 40 mm slots; on the medial frame at v 95, riveted through the hidden slot | estimated (38 mm size of the 25 mm 38 × 32 × 6 typical) |
| `Kneepad.L.CapProxy` | one manifold hull: base + cap union, Subsurf 0, for cloth collision (spec 09) | interface |

### 3.6 Hardware and material standards (all pieces)
| Item | Dimensions (mm) | Material / finish | Status |
|---|---|---|---|
| Dome rivet (studs, rivets) | head Ø 7.0, height 2.2, shank Ø 3 (hidden) | nickel-plated steel, polished | estimated |
| Cam buckle 25 mm | 36 × 30 × 11, bars 3, lever 24 × 14 × 3 | zinc-plated stamped steel, bright | estimated |
| Ladder-lock 25 mm | 38 × 32 × 6, bars 3.5, two slots 27 × 4.5 | gunmetal acetal/steel, worn edges | research D "typical" (uncited) |
| Ladder-lock 38 mm | 52 × 44 × 6, bars 3.5, two slots 40 × 4.5 | as above | estimated |
| Webbing 25 mm | 25 × 1.3, herringbone 2.5 rib | black polyester | prototype recipe |
| Elastic 38 / 25 mm | × 1.8 / 1.5, 1.0 rib pitch | black knitted | estimated |
| Neoprene | 3.0 (sleeves), 4.0 (knee base), 1.5 (elbow backing) | black, nylon-faced | estimated |
| Foam | 4.0 (guards), 6.0 (pauldron pad) | closed-cell EVA, dark grey | estimated |
| Paint | 60–80 µm desert tan over dark grey-brown substrate | matte polyurethane | estimated |
| Stitch | 2.2 stitch / 0.8 gap, thread r 0.3, bar tacks 3 × 12 at 1.3 pitch | black bonded nylon | prototype recipe |

### 3.7 Wear and dirt (where, how much)
Dust (pale, #d2c5b5 class) on every face with normal·Z ≥ 0.4: pauldron inner flanges and bends (heaviest), tier 2 top rims, guard dorsal faces, kneepad upper chamfers and the top of each frame. Paint chips 2–8 mm exposing #2e2b27–#453d3b: 30–40 % of each kneepad centre panel (worst on the figure), 10–15 % along the guard ribs and groove edges, 5–8 % on the pauldron rim beads and corner chamfers, 3–5 % on flat faces. Hairline scratches 0.2–0.5 mm wide, 10–60 mm long, mostly along the limb axis on the guards (sleeve rub) and radial on the caps. Soot/grime streaks diagonally across the right guard's main plate (two streaks 5–8 wide, #3a332e), grime pooled in every slot and groove, and in the lower 20 mm of the kneepads. Scuffs across the emblem plate (3–4 bright scratches, the X-star's paint abraded along them). Hardware: silver buckles clean (the blue speculars are the cool light), gunmetal ladder-locks worn bright on their bar edges. Strap webbing fuzzed 5 % lighter along edges.

---

## 4. Geometry construction plan

All geometry is built by `scripts/parts/12_hard_armour.py` from the posed body (`Body.Mesh.Posed`), the rig `Morgan.Rig`, the anchors of specs 04/05/08/09/10 and the `measure_arm()` girth table; the script also builds the LEFT-side pieces in rest pose, mirrors them with `bmesh.ops.mirror` across X (for the right side, un-mirroring the asymmetric accessories: no emblem, no strobe, no window), then attaches each piece to its helper bone (§7) so the hero pose carries it. Rule from `research_prototypes.md` §6/§8: **every boolean operand is one manifold solid**; slots are cut **before** the rim bevel and Subsurf; chips and grime are shader, never geometry; stitches are geometry (thread cylinders) within 0.6 m of a closeup camera. Helpers in `scripts/lib/armour.py`:

* `loft_shell(sections, closed=False)` — `bmesh` grid from N section polylines (each a list of 3D points), quads between consecutive sections, `bmesh.ops.remove_doubles` 0.05 mm. Used for every plate.
* `outline_patch(outline_2d, cell=3.0)` — fills a 2D outline (list of (u, v) with corner radii resolved to 6 points per radius) with a quad-dominant grid (`bmesh.ops.create_grid` clipped by `bmesh.ops.bisect_plane` along each outline edge, outside faces deleted, boundary snapped), then maps (u, v) onto a developable surface by a supplied `surface(u, v) → (x, y, z)` function. Used for the cap plates with curved outlines (tier 1, kneepad).
* `rim_bead(bm, boundary_edges, width, proud, r_out, r_in)` — inset the boundary (`bmesh.ops.inset_region` by `width`), lift the inset ring by `proud` along the normals, bevel the two ring edges (`bmesh.ops.bevel`, `r_out` 3 segments, `r_in` 2 segments).
* `cut_slots(obj, slots)` — for each slot a rounded-rectangle or D or rhombus cutter solid (`bmesh` extrude of the 2D outline through the wall ± 2 mm), Boolean DIFFERENCE **EXACT**, cutter deleted; cut floors get a 0.5 mm bevel in the following bevel pass by edge weight.
* `rivet(pos, normal, d_head=7.0, h=2.2)` — UV sphere cap (16 × 6) scaled to a dome plus a 0.3 mm shadow-gap ring (a torus r_major d/2, r_minor 0.3 sunk 0.2) so the head reads as a separate part.
* `cam_buckle(size)`, `ladder_lock(size)` in `gear_hardware.py` — frames lofted from two rounded rectangles (bar section 3–3.5 mm, prototype §3 (d)), the cam lever a chamfered plate on a Ø 3 pin; strap passes through.
* `strap(path, width, thickness, fold_ends=15, twist_deg=0.4)` — dense strip (1 mm segments, 6 quads across), Solidify, bevel 0.6/3, bar-tack and running-stitch objects (prototype §8 webbing recipe).
* `finish_shell(obj, bevel=1.2, segments=5, angle=35, subsurf=(1, 2))` — Solidify (thickness per table, `offset −1` so the lofted surface is the OUTER face, `use_even_offset`, `use_rim`), Bevel (`limit_method 'ANGLE'` 35°, plus `WEIGHT` on slot floors), Weighted Normal, Subdivision viewport 1 / render 2; shade smooth with auto-smooth 40°.

Poly budget (evaluated at render Subsurf): pauldron set per side ≈ 26 k tris, forearm guard per side ≈ 20 k, kneepad per side ≈ 19 k, elbow cap ≈ 3 k; total ≈ 136 k. Game LOD (`export_game.py`): Subsurf 0, bevels kept ≈ 45 k; stitches dropped.

### 4.1 Pauldron tier 1 cap — `Pauldron.L.Tier1.*`
1. **Surface function.** In frame A define the cap's developed coordinate (p, q): p along the profile from the inner edge (0) to the bottom lip (130), q anterior–posterior from the centreline. The profile curve `C(p)` in the X_A–Z_A plane: p 0–15 flange (direction 10° below +X_A), p 15–49 arc of radius 30 turning 65° downward, p 49–119 straight at 70° below +X_A with a 400 mm-radius convexity in q, p 119–130 lip turned 15° inward. Place C so that the bend crest sits over the acromion–deltoid saddle: `Torso.Anchor.Acromion.L` + (18 outboard, 0, −6) in A, i.e. X_A ≈ +95 at s 8 %. Surface(p, q) = C(p) + q·Ŷ_A + convexity.
2. **Outline (p, q).** Trapezoid: q = ±62.5 for p 0–85, then chamfer at 45° to q = ±50 at p 119, lip to p 130; all corners radius 12 (6 points per corner). `outline_patch(cell 3.0)` → ≈ 1,900 quads mapped by Surface. Object `Pauldron.L.Tier1.Cap`, origin at the bend crest.
3. **Clearance check.** `BVHTree.FromObject(shirt stand-in or Shirt.Main)`: the cap's inner face (surface − 3.0 − 6.0 pad) must be ≥ 2.5 mm from the body everywhere under the 20 mm pad ring and ≥ 6 mm elsewhere; if not, push the whole cap outboard along X_A in 0.5 mm steps (log the shift; expected 0–3 mm).
4. **Slots and recess, before bevels.** `cut_slots`: tab slot 16 × 5 at (p 8–13, q −20). Left only: the shield recess — build the shield outline (top 50 wide at p 61, sides converging 8° for 70 mm, rounded point r 18 at p 156 → clipped to p ≤ 119, i.e. the point lands 11 above the lip; total 95) as a cutter extruded 1.5 mm into the surface (Boolean DIFFERENCE, EXACT), and a second cutter for the border groove (shield outline ±0.75, extruded 1.0 below the recess floor → `Pauldron.L.Tier1.EmblemRecess` is a face-set, not an object). Right side: skip.
5. **Rim bead.** `rim_bead(width 5, proud 1.2, r_out 1.0, r_in 2.0)` on the outer boundary (the slot and recess boundaries are excluded by selecting only the original outline edges).
6. **Studs.** `rivet()` at (p 30, q +12) and (p 105, q −8), normals from the surface; objects `Pauldron.L.Tier1.Stud1/2`, material SilverSteel.
7. **Finish.** `finish_shell(thickness 3.0, bevel 1.2/5)`. Expected 9 k tris at render.
8. **Emblem plate (left).** `outline_patch` of the shield outline −0.75 (the groove's inner wall) mapped by Surface at depth −1.5 + 1.0 (its face 0.5 below the cap face); Solidify 1.0 inward; four Ø 2 flush rivets as 0.1 mm-deep rings (shader only — a 0.3 mm ring in the normal map). Object `Pauldron.L.Tier1.EmblemPlate`, material BrushedAlu with the X-star decal (§5.5). UV: planar from the plate's (p, q), 1,024² island.
9. **Pad.** `Pauldron.L.Tier1.Pad`: the cap inner face offset −6.0 (Solidify of a copy, no bevel), trimmed to the 20 mm ring + two 30 × 40 patches at the links; material Foam; it hides the body–cap gap in low views.
10. **Tab.** `strap()` from (p 5, q −20) through the slot to the shoulder-strap anchor `Carrier.Strap.L.PauldronHook` (spec 13; stand-in: a point 40 inboard of the inner edge on the strap path), 25 × 1.3, 60 long, hook-and-loop end 25 × 20 as a 1.5 mm rounded patch; `Pauldron.L.Tier1.Tab`, material Webbing.

### 4.2 Pauldron tier 2 — `Pauldron.L.Tier2.*`
1. **Section.** Upper-arm ellipse at s 40 % from `measure_arm()` (112 × 105 → semi-axes 56 × 52.5), offset +9.5 (shirt 1.5 + pad 6 + 2 clearance) → plate inner; outer +3.0. `loft_shell` of 9 rings (s 28 → 52 %, each ring 24 points over the 100 mm arc centred at 3 o'clock, ±47.5°), with the top and bottom edges straight in s. Object `Pauldron.L.Tier2.Plate`, origin on the arm axis at s 40 %.
2. **Recessed panel.** Cutter: 70 × 28 rounded rect (r 4) following the arc, extruded 1.5 into the surface, Boolean DIFFERENCE EXACT; the floor edges get bevel weight 1 (0.5 mm).
3. **Slots.** `cut_slots`: three 3 × 9 vent slots at 6 pitch (upper posterior corner), strap-exit slot 12 × 5 (anterior bottom), window 8 × 6 (posterior bottom).
4. **Rim bead** 4 / 1.0 / 0.8 on the outline; **rivet** Ø 7 at the top anterior corner (12, 14); **finish_shell** (3.0, bevel 1.0/5). ≈ 6 k tris.
5. **Pad** `Pauldron.L.Tier2.Pad`: inner face offset −6, full outline minus 4; Foam.
6. **Links.** Two `strap()` elastics 25 × 1.5, 20 exposed, from under tier 1's lip (p 118) to tier 2's top edge, at 30 % and 70 % of the arc; ends disappear 8 mm under each plate; material Elastic.
7. **Strobe (left).** `Pauldron.L.Tier2.Strobe.Body`: rounded box 45 × 30 × 18 (r 3) with a 1.5 mm inset front rim; `Strobe.Lens`: 36 × 24 × 2 rounded plate (r 2) set 0.5 below the rim, a 0.4 mm micro-bevel; `Strobe.Clip`: tan plate 34 × 20 × 3 + hook 10 × 3 × 6 under the panel edge. Placed on the plate's outer face with its back 1 mm off the surface (clip bridging), rotated 12° about the surface normal (top toward anterior), lower edge 14 above the plate's bottom edge, centred at 60 % of the arc toward anterior. Bevel 0.6/3 on the body, Subsurf 1. ≈ 1.5 k tris.

### 4.3 Pauldron tier 3 band — `Pauldron.L.Tier3.*`
1. **Shell.** Upper-arm ellipse at s 70 % (girth 310 → semi-axes 50 × 46 [estimated from spec 05's 65 % section 103 × 95 scaled]) offset +4.0 (shirt 1.5 + pad 2.5) → inner; +2.5 wall. `loft_shell` of 5 rings (s 63 → 77 %), each 40 points over 200° centred at 3 o'clock (from 11:40 to 6:20). Groove: Boolean DIFFERENCE of a 2 × 1 torus-sector cutter at mid height. Strap slots 40 × 4 at 8 from each end (cut_slots). Rim bead 3 / 0.8 / 0.8; finish_shell (2.5, bevel 1.0/4). Object `Pauldron.L.Tier3.Shell`. ≈ 3 k tris.
2. **Elastic.** `strap()` 38 × 1.8 around the medial 160°, inner face at shirt + 0 (compressing the rib panel — spec 10 flattens its ribs 70 % under the band), sewn through the posterior slot (end hidden), free end passing the anterior slot into the cam buckle with a 30 mm tail hanging down-anterior; `Pauldron.L.Tier3.Elastic`, material Elastic (ribs along the strap).
3. **Cam buckle.** `cam_buckle(36 × 30 × 11)` riveted (two Ø 4 rivets) to the shell's anterior end, lever toward anterior-inferior; `Pauldron.L.Tier3.CamBuckle`, SilverSteel; keeper loop `Pauldron.L.Tier3.Keeper` 25 × 12 webbing.
4. **Pad** `Pauldron.L.Tier3.Pad` 2.5 foam under the shell.

### 4.4 Forearm guard — `Guard.L.*`
1. **Axis and sections.** From `Arm.L.GuardFrame` and `measure_arm()`: ellipse sections at d = 27, 32, 50, 66, 80, 100, 120, 140, 160, 180, 200, 220, 240, 257, 262 (girths interpolated through 290 @ s 12 %, 285 @ 40 %, 195 @ 90 %, aspect from spec 05 §3.3: 1.18 at s 25 % → 1.48 at the wrist). The dorsal (6 o'clock) direction is taken from the frame's −Z_F; **pronation twist** is applied per station (0 at the elbow, 30 % of the forearm's pronation at s 50 %, 100 % at the wrist, spec 05 §3.3) so the sleeve's seam and the plates' 6 o'clock follow the skin.
2. **Sleeve.** `loft_shell` closed tube, 48 points per ring, inner = body + 1.5 → object `Guard.L.Sleeve`; Solidify 3.0 outward; bound edges = rim_bead 10 / 1.0 / 1.5 at d 27 and 262; flatlock seam at 12 o'clock as a 2 mm-wide 0.4 mm ridge (Displace by a UV mask, §5.7). ≈ 2 k tris. Material Neoprene.
3. **Foam pads.** For each plate: the plate's inner outline offset −3 mm and −6° of arc, lofted at body + 4.5, Solidify 4.0 outward; `Guard.L.Foam.{Elbow,Main,Wrist}`; material Foam. ≈ 1.5 k.
4. **Elbow band.** `loft_shell` of 4 rings (d 32, 44, 56, 66), 30 points over 230° centred at 6 o'clock, at body + 8.5; cut_slots: strap slot 27 × 4 at the 9 o'clock end (6 from the end); rim bead 3 / 0.8 / 0.8; finish_shell (2.5, bevel 1.0/4). `Guard.L.Plate.Elbow`. Cam buckle `Guard.L.CamBuckle` riveted at the 3 o'clock end, lever pointing distal (the bright 8 mm hook of the image is the lever tip), keeper `Guard.L.Keeper`.
5. **Main plate.** `loft_shell` of 14 rings (d 62 → 224), 36 points over 200° at body + 8.5. **Rib**: before Solidify, lift the 14 mm-wide strip of vertices along 6 o'clock by +2.5 with 45° flanks (vertex displacement along the ring normals, smoothstep over 3 mm each side), tapering to 0 within 7 mm of d 70 and d 216. **Grooves**: Boolean DIFFERENCE of two rounded-end cutter bars 3 × 1.2 × 138 at ±22 mm arc from 6 o'clock (d 74–212). **Window (left only)**: cutter 10 × 20 (r 2) 1.0 deep at 7:30, d 175–195; insert `Guard.L.Window` 0.8 thick, GreyPolymer. Edge chamfer 1.0 (bevel weight on the outline edges), rim bead 3 / 0.8 / 0.8, finish_shell (3.0, bevel 1.0/5). `Guard.L.Plate.Main`. ≈ 8 k tris. Overlap: proximal edge at d 62 sits 4 under the elbow band's lip (band outer −2.5 → the main plate's proximal 4 mm is at body + 6 and rises to + 8.5 by d 70: a 2.5 mm ramp built into ring 1–2); distal edge over the wrist band (wrist band's proximal ring at body + 5.5 → +8.5 by d 228).
6. **Wrist band.** As the elbow band: rings d 220, 232, 245, 257; 230°; slot 27 × 4 at 9 o'clock; ladder-lock `Guard.L.LadderLock` (gunmetal 38 × 32 × 6) riveted at 3 o'clock, bars across the limb. `Guard.L.Plate.Wrist`.
7. **Straps.** `strap()` × 2, 25 × 1.3, path: out of the 9 o'clock slot, across the flexor side on the sleeve (sleeve outer + 0, sampled from the sleeve mesh at 1 mm), into the buckle / ladder-lock, tail 40 folded 15 and bar-tacked; 0.4° twist; `Guard.L.Strap.Elbow/Wrist`, Webbing; stitches `Guard.L.Stitches`.
8. **Stencil UV.** Mark the main plate's stencil quad (32 × 15 at d 134–166, 4:30 o'clock) as a UV island of 256² in the guard's atlas for the decal (§5.6).
9. **Right guard.** Mirror; delete `Guard.R.Window` (D13); keep the stencil on both (the left's is on its radial side, invisible in the hero view).

### 4.5 Lateral elbow cap — `ElbowCap.L.*`
1. From `Arm.L.ElbowAnchor`: backing `ElbowCap.L.Backing` = `outline_patch` 50 × 80 (r 10) mapped onto the shirt's elbow-pocket surface (Shrinkwrap PROJECT along −X_E onto `Shirt.Main` or the arm + 3 stand-in), Solidify 1.5 outward, Neoprene.
2. Fin: lens outline (two arcs, 40 × 14) mapped onto the backing's outer face at +16 proximal; vertices lifted along the normal by a ridge function (3 mm at the axis, 0 at the edges); Solidify 2.5 outward; bevel 0.6/3; `ElbowCap.L.Fin`, GreyPolymer.
3. Pad: rounded square 30 × 28 (r 6) at −16 (distal), dome +3 (cosine), Solidify 2.5, bevel 0.8/3; `ElbowCap.L.Pad`.
4. Elastic: `strap()` 25 × 1.5 one turn around the elbow at the axis, from the backing's anterior edge to its posterior edge across the inner elbow at body + 6 (spec 10), with a 1 mm sink into the backing at the sewn edges; `ElbowCap.L.Elastic`.
5. Mirror to the right (D5). ≈ 3 k tris each.

### 4.6 Kneepad — `Kneepad.L.*`
1. **Base.** From `Trousers.L.KneePocket` outer surface (or spec 09's stand-in ellipsoid): `outline_patch` of the base outline (cap outline + 12, r 15) in (u, v), mapped onto the pocket surface by wrapping u as arc length around the knee axis at the pocket radius and v along the pocket; Solidify 4.0 outward; rim_bead 8 / 0.8 / 1.5 (bound edge); `Kneepad.L.Base`, Neoprene. ≈ 2 k.
2. **Cap surface.** `outline_patch(cap octagon, cell 3.0)` ≈ 3,000 quads mapped by `Surface_K(u, v)`: around the knee axis u → angle θ = u / 78 (150° total at the sides), radius r(v) = base outer radius + bulge(v) where bulge = 30·smoothstep profile peaking at v 95 (the prototype's "forward bulge +12 at mid height" scaled to 30), plus the tilts (upper third 15° back, lower third 12° back) as a v-dependent Y_K offset; so the inner surface touches the base at v 10–30 and 160–180 and stands up to 30 proud at the patella.
3. **Frame and centre.** `rim_bead(width 12 → split: lip bead 2.5 radius flare 1.8 (prototype), flat 7, inner wall)`: inset 12, drop the inset region by 2.0 along −normal with a 45° wall (the inset ring is bevelled 2 segments over 2 mm). The centre panel's vertices get a displacement noise (scale 8 mm, ±0.3 mm) baked into the mesh (`bmesh` vertex offsets) so the pitting is geometry at the silhouette and shader within.
4. **Cut-outs.** `cut_slots` S1 (18 × 4 rounded), S4 (D 10 × 8), S5 (8 × 4), H1/H2 (Ø 3.5), S2 (rhombus 12 × 6), S3 (12 × 5), S6 (C 12 × 8: a 12 × 8 rounded rect minus a 6 × 4 bridge), hidden strap slot 40 × 5 at (−75, 95); corner indents N1–N3 (triangle cutters 0.8 deep); boss B1 as a separate chamfered 7 × 7 × 1.5 box object `Kneepad.L.Boss` fused by Boolean UNION before the bevel pass.
5. **Finish.** finish_shell (3.5, bevel 1.2/5 at 35°, slot floors 0.5). `Kneepad.L.Cap`. ≈ 14 k tris at render (prototype: 11 k + cut-outs).
6. **Tab.** `Kneepad.L.Tab`: 10 × 30 × 3 rounded tab (r 5 end), rooted 8 under the lateral frame lip at v 115–145 (the root fused into the cap by a 0.5 mm overlap, no boolean), protruding 6; bevel 0.8/3; RedRubber.
7. **Strap and buckle.** `ladder_lock(52 × 44 × 6)` on the medial frame at v 95, bars along v, riveted (2 × Ø 4) through the hidden slot; `strap()` 38 × 1.8 Elastic from the base's lateral edge (sewn, 15 mm overlap) around the back of the knee at h 530–550 following the trousers' outer surface + 0 (sampled from `Trousers.Main` or the leg stand-in) into the ladder-lock; tan webbing tail `Kneepad.L.StrapTail` 38 × 1.3 × 50 sewn to the elastic end, folded 15, bar-tacked; stitches `Kneepad.L.Stitches`.
8. **Proxy.** `Kneepad.L.CapProxy`: Boolean UNION of base and cap copies (EXACT, both manifold), Subsurf 0, no bevel — the collider spec 09 simulates against (inner face = pocket outer + 0, so the pocket must be simulated **before** our base is placed, then our base sits on it; §10.1).
9. **Right kneepad.** Mirror(u) of the whole assembly: strap/buckle medial, tab lateral (D7, D8).

### 4.7 Join, naming, collections, origins
All objects in collection `Armour`, sub-collections `Armour.Pauldron.L/R`, `Armour.Guard.L/R`, `Armour.ElbowCap.L/R`, `Armour.Kneepad.L/R`. Origins: pauldron tiers at the arm axis at their station; guards at `Arm.*.GuardFrame`; elbow caps at `Arm.*.ElbowAnchor`; kneepads at the knee axis centre. Nothing is joined into one mesh (separate parts read as separate parts; each keeps its own bevel); hardware parented to its plate. Idempotence: the script deletes every object, material and image with these prefixes before rebuilding, and the right-side rebuild never touches `Armour.*.L`.

### 4.8 Topology notes
Lofts are quad grids (rings × stations), so Subsurf behaves; booleans are applied (`modifier_apply` under `temp_override`) and followed by `bmesh.ops.dissolve_limit` 2° on the flat faces only (not within 3 mm of a cut) to limit the long triangles the EXACT solver leaves; Weighted Normal after the bevel keeps the flats flat. Walls are always Solidify of the outer surface (`offset −1`) so measured outer dimensions are exact. The stencil, window, recess and emblem islands are UV-unwrapped from their (p, q)/(d, θ)/(u, v) parametrisation directly (no `uv.unwrap` operator needed); the rest of each piece uses `bpy.ops.uv.smart_project` (angle 50°, margin 0.004) for the baked wear masks.

---

## 5. Materials and textures

Colour management AgX (as every spec); hex values are sRGB albedo targets fed through the sRGB → linear helper. All materials are node trees built by `scripts/lib/mat_hard.py`; CC0 sets from `assets/textures/` per `notes/research_assets.md`: `Plastic018B` (grey dirty scratched plastic — micro normal/roughness only, colour discarded), `SurfaceImperfections015` (dust, with opacity), `SurfaceImperfections017` (speckle grime), `Metal063` (bare steel), `Metal027` (black powder-coat), `blue_metal_plate` (chip-shape mask alternative). Wear masks are **baked** per piece to `Armour.Img.Wear.<Piece>` (2,048², EMIT bake of the combined mask, research C §10c; Pointiness is Cycles-only and density-dependent) so Cycles, EEVEE/Workbench and the glTF export agree.

### 5.1 Texel density and UV sets
| Set | Pieces | Image | Density | Notes |
|---|---|---|---|---|
| `Armour.UV.Pauldron.L/R` | the three tiers + strobe clip | wear 2,048² | ≈ 6 px/mm (atlas ≈ 0.12 m² developed) | smart-project islands; emblem plate and recess islands pinned from (p, q) |
| `Armour.UV.Guard.L/R` | three plates | wear 2,048², stencil 256² island | ≈ 7 px/mm | plates unwrapped from (d, θ) directly — rectangular islands |
| `Armour.UV.Kneepad.L/R` | cap | wear 2,048² | ≈ 8 px/mm (0.06 m²) | (u, v) parametrisation |
| hardware, tab, elbow caps | — | shared 1,024² | ≈ 10 px/mm | smart-project |
| `Armour.Img.Emblem.Mask` | emblem plate | 512² (plate 50 × 95 → 5 px/mm) | generated (§5.5) | |
| `Armour.Img.Stencil.Mask` | guards | 512² | generated (§5.6) | |
Micro-detail (orange peel, brushing, weave) is procedural and resolution-independent; only the wear and decal masks are images, so a 100 mm lens at 0.4 m (V11) still shows crisp paint steps.

### 5.2 `Armour.Mat.TanPolymer` — the shared worn tan paint (pauldron tiers, guard plates, kneepad cap, strobe clip, strap tails' tan webbing uses `Webbing` tinted instead)
| Layer | Node recipe | Values |
|---|---|---|
| Paint base colour | RGB → Mix (dust) | albedo **#837163** (linear 0.229, 0.166, 0.126); per-piece multiplier: pauldrons 1.0, guards 1.0, kneepad frames 0.92, kneepad centres 0.85 (older, dirtier paint); Hue/Sat jitter ±2 % by Object Info random |
| Paint roughness | base 0.55; Plastic018B roughness map (tile 60 mm, remapped 0.45–0.65) × 0.5 + 0.5 | matte PU |
| Orange peel | Noise scale 900 (≈ 1 mm cells) → Bump strength 0.2, distance 0.2 mm | prototype §8 |
| Micro scratches | Plastic018B normal (tile 60 mm, strength 0.35) + anisotropic noise (Mapping scale 1, 1, 14 along the limb axis via the UV's v, noise 180, threshold 0.66–0.72) → roughness +0.15 and colour +6 % | prototype |
| Chip mask `M_chip` | Voronoi F1 distance (scale 120/m on the caps' centres → flakes 5–8 mm; 220/m elsewhere → 2–4 mm), hard threshold **0.52–0.56** on the kneepad centres (30–40 % coverage), 0.80 on frames and plate faces (3–5 %), 0.72 along ribs/groove edges via the baked edge mask; multiplied by `Armour.Img.Wear` (edge mask 0.6 + AO 0.2 + noise 0.2) | prototype §3 (b) |
| Chip edge | `M_chip` → Bump (distance 0.12 mm, strength 1.0) so every flake border catches light; inside the chip the paint layer's bump is replaced by the substrate's | required by §1.4 (6) |
| Substrate | base colour **#2e2b27 → #453d3b** (noise-blended, linear 0.027–0.054), roughness 0.38, specular 0.5 | consolidated §5 |
| Dust | `SurfaceImperfections015` colour × opacity (tile 650 mm, 2 octaves of UV offset), gated by (normal·Z)² remapped 0.4 → 1, plus a 0.5 mm noise; mix to **#d2c5b5** at up to 55 % (pauldron bends, kneepad upper chamfers), 25 % elsewhere; dust raises roughness to 0.8 | consolidated weathering |
| Grime | `SurfaceImperfections017` × (1 − AO) × slot/groove cavity (baked AO, threshold 0.6) → darken 40 % toward #1a1612; kneepad lower 20 mm gradient 0 → 30 % | §3.7 |
| Soot streaks (right guard) | two hand-placed stroke masks in the stencil/wear UV (procedural: Gaussian lines 6 wide, 60 long, at 35° to d) → #3a332e at 60 % | gear §7.2 |
| Hex targets (hero light) | right cap lit face #90877c ± ΔE 8; right guard lit #cdb8a6; left cap #828080 (cool); kneepad R frame #5a514b / centre #272420; L frame lit #826e5b / centre #343432 | §2.1 |

### 5.3 Other materials
| Material | Principled values | Detail |
|---|---|---|
| `Armour.Mat.BrushedAlu` (emblem plate) | base #b8bcc0 (lin 0.48), metallic 1.0, roughness 0.32, **anisotropic 0.6, rotation along the plate's v (vertical)**, tangent from UV | brushing: anisotropic noise (Mapping 1, 40, 1) → roughness ±0.08 and bump 0.05 mm; 3–4 bright diagonal scratch lines (Gaussian 0.4 mm wide) → roughness 0.15; dust 10 % on the upper third; X-star layer §5.5; hero target #aabacc, highlight #bfcedc |
| `Armour.Mat.SilverSteel` (studs, rivets, cam buckles) | base #c9c9c6, metallic 1, roughness 0.22, coat 0 | Metal063 roughness (tile 20 mm) × 0.5; fingerprints none; **no paint** — the blue speculars in the image are the cool light |
| `Armour.Mat.Gunmetal` (ladder-locks, strobe rim) | Metal027 base #3c3d45, metallic 0.9, roughness 0.45 | Bevel-node edge mask (radius 0.8 mm, 4 samples) → bare steel #9a9a98 roughness 0.25 on bar edges (worn bright) |
| `Armour.Mat.GreyPolymer` (elbow caps, guard window insert) | base #7b818a (lin 0.19), roughness 0.5, specular 0.5 | orange peel as TanPolymer; 2 % chips; hero targets fin #9aa8b5 / pad #515c67 under the cool light |
| `Armour.Mat.StrobeLens` | base #9aa7b3, **transmission 0.35**, roughness 0.30, IOR 1.58 (polycarbonate), thin-walled off | faint internal frosted volume (Volume Scatter density 40) so it reads translucent; optional `Emission` input 0 (game variant 2.0 for a flash); target #afc1d3 |
| `Armour.Mat.StrobeBody` | base #2a2c30, roughness 0.5 | fine texture noise 2500 |
| `Armour.Mat.Neoprene` (sleeves, base, backing) | base #141416, roughness 0.75, sheen 0.2 | nylon-face weave bump: noise 2500 at 0.08 mm + Box-projected Plastic012B normal 0.2 (never Object coordinates on curved parts — prototype (e)) |
| `Armour.Mat.Foam` | base #2b2b2b, roughness 0.9 | cell noise 1800, 0.1 mm bump |
| `Armour.Mat.Webbing` | `cordura_material(#22211f, weave 1000, rough 0.7, sheen 0.06)` with UV u along the strap, herringbone rib 2.5 mm; tan variant #8a7050 for the kneepad strap tails | prototype §8 |
| `Armour.Mat.Elastic` | base #1a1a1a, roughness 0.8, sheen 0.15 | 1.0 mm rib pitch across the strap width (wave texture → bump 0.15 mm), 5 % lighter fuzz on edges |
| `Armour.Mat.RedRubber` (kneepad tab) | base **#8a4a4c** (lin 0.25, 0.07, 0.07), roughness 0.6, subsurface 0.05 radius 1 mm | dust 15 % on top; hero target #695b5f under the cool light (verify by the light-swap test: must read red under the key) |
| `Armour.Mat.Thread` | reuse `Thread.Black` from the materials library | |

### 5.4 Chip-mask recipe in full (shared, parameters per region)
`Voronoi(F1, smoothness 0, randomness 0.9, scale S)` → `distance` → `Map Range(threshold T ± 0.01 → 0/1)` → × `Wear.R` (baked: `Pointiness` remapped 0.45–0.65 × 0.6 + `AO`(inverted, distance 6 mm) × 0.2 + `Noise 60` × 0.2) → `M_chip`. Regions by a vertex-colour attribute `ArmourRegion` (R = centre panel 1, frame 0.3, rib/groove edge 0.6): S = 120 (centres) / 220 (rest); T = 0.54 / 0.80 / 0.72. Two further masks: `M_scratch` (anisotropic noise, §5.2) and `M_dust` ((normal·Z)² gate × SurfaceImperfections015). Composition: colour = mix(mix(paint, substrate, M_chip), dust, M_dust × (1 − M_chip)); roughness likewise; normal = paint orange-peel + M_chip-step bump + substrate micro-bump inside chips. The baked `Armour.Img.Wear.<Piece>` is the product `Wear.R`; when present the shader reads it instead of Pointiness/AO.

### 5.5 Emblem decal (`Armour.Img.Emblem.Mask`, generated by `scripts/lib/decals.py` with system `python3 -I` + PIL; the 50 × 95 plate is drawn at 5.1 px/mm = 256 × 486 px and saved padded to 512²)
1. Draw on a black canvas: the three strokes of §3.2 as white polygons (long stroke 2.4 wide, short stroke 2.4, spike 1.8), square ends.
2. Weather: multiply by a Perlin-like noise (PIL: sum of three blurred random-noise octaves, 4/8/16 px) thresholded so 35 % of the stroke area drops out, biased toward the stroke edges (erode 1 px then re-add 50 % of the eroded band at random); add 3 scratch lines (the same as the plate's scratches, aligned via the shared (p, q) UV) that cut the paint.
3. Blur 0.6 px, save as `assets/generated/emblem_mask.png`; the shader uses it as the mix factor between BrushedAlu and a white paint layer (base #e8ecee, roughness 0.5, bump 0.06 mm step at the mask edge so the paint has thickness).
4. Pass criterion: in V11 the mark reads as a 25 mm-tall white X with a short tail, broken, not a clean vector logo.

### 5.6 Stencil decal (`Armour.Img.Stencil.Mask`, 512², PIL)
Three glyphs in a stencil face (DejaVu Sans Bold with 1.2 mm bridges cut by hand-placed rectangles; client to supply the text, §10.3 — placeholder "7 2 A" chosen because the drawn block is three glyph-widths wide), cap height 9 mm, stroke 2 mm, kerning 1.5 mm → block 32 × 15. Smudge: motion blur 6 px along the stencil's d direction (a soldier's sleeve rubs along the arm), multiply by noise so 45 % drops out, then a second faint offset ghost (the stencil slipped) at 15 % opacity. Shader: mix to black paint (#141210, roughness 0.5, no bump: stencil paint is thin) with the mask × (1 − M_chip).

### 5.7 Geometry-driven texture features
Sleeve seam ridge (0.4 mm, Displace by a UV strip mask), bound edges (geometry bead), strap ribs (bump), rivet shadow rings (geometry), window insert gap 0.2 mm (geometry), slot floors (geometry + baked AO grime). Nothing of the chips, scratches or dust is geometry except the kneepad centres' 0.3 mm pitting (vertex noise, §4.6 step 3) which the silhouette needs.

---

## 6. Fibres, simulation or dynamics

No hair, no particles. No cloth simulation is needed for these pieces: every plate is rigid, every strap follows a sampled surface path (§4). Two small dynamic details:

1. **Strap sag.** `strap()` applies the prototype's random sag (±20 % of a 1.5 mm nominal) and 0.3–0.5° roll to every webbing/elastic span longer than 60 mm (the kneepad rear strap, the guard flexor straps, the pauldron elastic), so no strap is a perfect arc.
2. **Elastic stretch rendering.** Elastic spans are drawn 4 % narrower than their nominal width over their free length (38 → 36.5 mm; 25 → 24 mm) and full width at the sewn ends — the look of a tensioned elastic.

The neoprene sleeves and base are **not** simulated; they are offset surfaces of the arm/pocket (they would be in reality: neoprene is form-fitting). The cloth parts that *are* simulated (spec 09 trousers, spec 10 shirt) need our stand-ins before their sims run: `Armour.StandIn.CapSeat.L/R` (110 × 130 patch at body + 2.5), `Armour.StandIn.Tier3.L/R` (50-tall band, inner body + 2.5 at s 63–77 %), `Armour.StandIn.GuardBand.L/R` × 2 (bands 34/37 wide, inner body + 1.5 at d 32–66 and 220–257), `Kneepad.L/R.CapProxy`; the script writes them first (cheap primitives) and replaces them with the real pieces at the end; `build_all.py` runs the stand-in stage before the cloth sims.

---

## 7. Rigging and attachment

### 7.1 Helper bones (added to `Morgan.Rig` by `scripts/lib/rig.py::add_armour_helpers()`, MPFB `default` names per spec 08 §3.6; non-deform except where stated)
| Bone | Head → tail (rest, left) | Parent | Constraints | Carries |
|---|---|---|---|---|
| `pauldron.L` | GH centre (+240, −20, 1452) → +Z_A 100 | `clavicle.L` | **Copy Rotation `upperarm01.L` influence 0.5**, world space; Copy Location `upperarm01.L` 1.0 | `Pauldron.L.Tier1.*` (cap, pad, studs, emblem, tab root) |
| `pauldron_mid.L` | arm axis s 28 % → s 52 % | `upperarm01.L` | Copy Rotation `pauldron.L` 0.25 (so tier 2 follows the cap a little, lame-style) | `Pauldron.L.Tier2.*`, links' lower ends |
| (none) | — | `upperarm01.L` | — | `Pauldron.L.Tier3.*` parented rigidly to `upperarm01.L` (above the twist helper `upperarm02`, so pronation does not twist the band) |
| `guard.L` | forearm axis d 32 → d 257 | `lowerarm01.L` | Copy Rotation `lowerarm02.L` 0.6 (the guard follows 60 % of the forearm twist, the mean of the skin's 30 % at mid-forearm and 100 % at the wrist) | all `Guard.L.Plate.*`, foam, hardware, straps |
| `elbowcap.L` | elbow axis centre → +20 lateral | `upperarm01.L` | Copy Rotation `lowerarm01.L` 0.5 | `ElbowCap.L.*` |
| `kneepad.L` | knee axis centre (+93, 0, 523) → −Y_K 40 | `lowerleg01.L` | Copy Rotation `upperleg02.L` **0.3**, X only, local (the patella bone of spec 08 uses 0.5; the cap sits lower, so 30/70 as spec 09 §7 expects) | `Kneepad.L.Cap`, boss, tab, ladder-lock, strap medial end |

Hard pieces are parented with `parent_type 'BONE'` (rigid, weight 1.0 to one bone: no deformation, no candy-wrapper). Soft pieces are skinned: `Guard.L.Sleeve` and `Guard.L.Foam.*` take their weights by **Data Transfer** (vertex groups, nearest face interpolated) from `Body.Mesh` (`lowerarm01/02.L`, `wrist.L`), `Kneepad.L.Base` and `Kneepad.L.Strap` from `Body.Mesh` (`upperleg02.L`/`lowerleg01.L`), `ElbowCap.L.Backing/Elastic` from the arm, the pauldron links and elastic from `upperarm01.L` with a 0.25 blend to `pauldron.L` at their upper ends, the webbing tab 100 % `pauldron.L`. Weights are capped at 4 influences (Godot export, spec 08).

### 7.2 Surface offsets (inner faces, mm above the body surface `Body.Mesh.Posed`)
| Piece | Inner face | Against | Reference |
|---|---|---|---|
| Pauldron tier 1 pad (20 mm ring) | **+2.5** (= shirt panel +2.3 + 0.2) | `Shirt.Band.CapSeat` | spec 10 §10.1 |
| Tier 1 cap elsewhere | ≥ +6 (stands off the deltoid dome) | — | §4.1 step 3 |
| Tier 2 pad / plate | +3.5 / +9.5 | shirt panel | derived |
| Tier 3 shell pad | **+2.5**; elastic at shirt + 0 (rib panel flattened 70 %) | `Shirt.Band.Tier3` | spec 10 |
| Guard sleeve / foam / plates | **+1.5 / +4.5 / +8.5** | `Shirt.Band.GuardElbow/GuardWrist` (sleeve at +1.45 under the bands, bulging +8–12 beside them → the foam absorbs the bulge) | spec 10 §10.1 (updated numbers, §10.1) |
| Elbow cap backing | shirt elbow pocket outer ply + 0; elastic body + 6 at the inner elbow | spec 10 | |
| Kneepad base | trousers knee pocket outer + 0 | `Trousers.L.KneePocket` | spec 09 (D10) |
| Kneepad strap | trousers outer + 0 at h 530–550 behind the knee | spec 09 | |

### 7.3 Pose behaviour
In the hero pose: right pauldron on the pulled-back right humerus (spec 08 D2: extension −15 to −25°) — the cap tilts back half as much as the arm, its anterior edge rises, which matches the right cap reading as a wedge from the key side; left pauldron near rest. Right guard pronated 70° × 0.6 = 42° about the forearm, left 40° × 0.6 = 24°. Kneepads follow 70 % of the shin: right knee flexed 15–20°, left 8–10°; the cap's top edge therefore moves back over the thigh by 0.3 × flexion, keeping the cap on the patella. The flat variant for intersection testing (§8.4) is the rest pose with all helper influences at their rest values.

### 7.4 Game export
Pieces export with the body in `export_game.py` (spec 08): rigid pieces as separate meshes skinned 100 % to their deform parent (`upperarm01`, `lowerarm01`, `lowerleg01` for the helper-bone pieces, since the helpers are non-deform: the export bakes the helper's rest offset into the mesh and accepts the loss of the 50 %/60 %/30 % blends — a visible but minor simplification, flagged in §10.3), baked wear images at 1,024², decals merged into the albedo; Subsurf 0, bevels kept. Scaled with the body to 1.80 m.

---

## 8. Evaluation protocol

### 8.1 Render sets (`scripts/eval/armour_eval.py`, Cycles CPU, OIDN, adaptive 0.02)
* **Hero set**: V1–V4 at 1,024 × 1,536 full frame, 64 spp, hero lights (consolidated §8: key warm from his right-front-above, cool left fill, rim), cropped and ×3 upscaled to the crop files; ≈ 2–4 min each.
* **Closeup set**: V5–V11 at 1,024², 64 spp, hero lights, ≈ 40–60 s each.
* **Look-dev set**: V12 turntables (4 × 800² at 48 spp) under `empty_warehouse_01` HDRI at 0.6 strength + a neutral 5,600 K key; shows true albedo and form.
* **Light-swap test**: V1 rendered a second time with the key and fill positions mirrored across X; the left cap must then read tan (#90877c class) and the right grey-blue (#828080 class). Proves D1.
* **Workbench form set**: every closeup view also in Workbench (matcap + cavity, 5 s) for geometry iteration before any Cycles render (`CLAUDE.md`, Where work runs).

### 8.2 Automated measurements (`scripts/lib/measure.py::measure_armour()`, written to `renders/12_hard_armour/measure.json`)
For each object: oriented bounding box in its local frame (outer dims), wall thickness by ray-casting the inner face against the outer (median and min of 200 rays), slot sizes by projecting slot-boundary loops to the local plane, rim bead height by the profile at 8 stations, rivet head diameters, strap width/thickness at 10 stations, hardware OBBs; the inner-face offset to the body/cloth by nearest-point distance (median, min, max) for each contact band of §7.2; plate overlap depths (tier 1/2, elbow band/main, main/wrist). Mask IoU: Cryptomatte object masks of each piece group in V1–V4 versus the reference boxes of §2.1 (polygon masks drawn from the zoom crops into `ref/masks/armour_<piece>.png` by thresholding the zoom's luminance/colour against the surrounding cloth, shipped with the script) → IoU per piece. Colour: median sRGB in 9 × 9 windows at the §2.1 sample pixels of the rendered V1–V4 versus the table, ΔE2000. Padded shoulder width at y 205 from the V1 silhouette.

### 8.3 Pass thresholds
| Metric | Threshold |
|---|---|
| Outer dims (every table in §3) | ±3 mm; cap/plate developed heights ±3; hardware ±1 |
| Wall thickness | 3.0 ± 0.3, 2.5 ± 0.3, 3.5 ± 0.3; min never < 2.0 (a thin spot at a boolean) |
| Slots | ±1 mm; every slot has a visible floor/wall in Workbench cavity |
| Rim beads | 1.2 ± 0.3 / 1.0 ± 0.3 / 0.8 ± 0.3 proud |
| Offsets | contact bands median within ±0.5 of §7.2; min ≥ 0 (no penetration) |
| IoU | kneepad caps ≥ 0.85; forearm guards ≥ 0.80; pauldron groups ≥ 0.80; padded shoulder width 320 ± 6 px |
| Colour | ΔE ≤ 8 at every §2.1 sample; light-swap test ΔE ≤ 6 between swapped readings |
| Chip coverage | kneepad centre 30–40 %, frames 3–8 %, ribs 10–15 % (measured from the rendered `M_chip` AOV in V9/V10/V7) |
| Dust | mean dust-mask value on faces with normal·Z < 0.2 ≤ 0.05 |
| Hardware count | 2 pauldron cam buckles, 2 guard cam buckles, 2 guard ladder-locks, 2 kneepad ladder-locks, 4 pauldron studs, 2 tier 2 rivets, 2 tabs, **1** strobe, 1 emblem plate, 1 window, 2 red tabs |
| Intersections (§8.4) | 0 overlaps > 0.3 mm |
| Render time | hero set ≤ 4 min/view shared, closeups ≤ 60 s |

### 8.4 Intersection test
Flat variant (rest pose, helpers at rest): `bmesh` BVH overlap of every `Armour.*` evaluated mesh against `Body.Collider`, `Shirt.Main` (or `Torso.StandIn.*` + `Arm.*.SleeveCollider`), `Trousers.Main` (or the leg stand-in), `Glove.*` (or the gauntlet stand-in), `Carrier.*` (or spec 13's stand-in), and against each other (plates vs straps, straps vs buckles). Any overlap > 0.3 mm is listed with the pair and the deepest point; the script fails on plate–body overlap and warns on strap–strap.

### 8.5 Critic questions (score 0–2 each, from the renders only)
1. V1: do both shoulders read as the *same* tan armour, the left merely in blue light? 2. V2/V6: does the right cap read as a bent plate with a dusty bend crest and two tiny bright studs, not a flat tan patch? 3. V3/V11: is the emblem a lighter brushed metal plate inset in a shield recess with a visible border groove, carrying a broken white X-star about 25 mm tall? 4. V3/V5: does the strobe read as a translucent pale box clipped on, lighter than the plate, with a tan clip? 5. V2/V7: do the forearm guards read as three curved plates in a row — band, grooved main plate with a rib, wrist band — pinching the sleeve, with a silver buckle hook at the elbow end? 6. V4/V9/V10: are the kneepad frames tan and the centres flaked dark, with every slot showing depth, the red tab visible on the left, strap and gunmetal buckle on the medial side? 7. V7/V9: does every chip have an edge, every scratch a direction, and dust sit only on top? 8. V8: is the elbow cap a grey fin above a square pad on black elastic, small, on the outer elbow? 9. V12: can you find a zero-thickness edge, a floating strap, a strap that ends nowhere, a buckle without a strap through it, a rivet without a shadow ring? (2 = none found) 10. Would someone who has worn hard knee and forearm protection accept these as real injection-moulded, strapped-on gear?

### 8.6 Failure modes and their fixes
Left pauldron renders tan not grey-blue → the cool fill is too weak or warm (fix the eval scene, not the albedo); right cap reads flat → bend radius too large or key angle wrong, check the crest dust; emblem plate reads white or chrome → roughness < 0.25 or missing anisotropy; X-star reads as a clean vector → abrasion step skipped; strobe reads opaque white → transmission off or no volume; chips read as soft blotches → Voronoi smoothness > 0 or missing step bump; chip coverage uniform across frame and centre → `ArmourRegion` attribute not written; Pointiness mask smears on flat faces → wear mask not baked, or boolean left long triangles (dissolve pass skipped); plates show no wall → Solidify offset wrong sign (surface became the inner face) or thickness applied in metres; slot floors z-fight → cutter not through-wall; strap floats → path sampled from the stand-in while the real cloth differs: re-sample after the cloth stage; strap reads as a flat ribbon → Solidify/bevel/twist missing; ladder-lock a grey brick → built as a slotted block instead of a bar frame; neoprene shows stripes → Object-coordinate texture on a curved part (use UV/Box); kneepad base visible as a thick slab → base > 4 mm or margin > 12; cap intersects the pocket → the pocket was simulated after our base was placed, or `CapProxy` not passed to spec 09; pauldron cap pierces the carrier strap → the tab anchor/strap path from spec 13 moved: re-run the clearance step; guard plates buried in the sleeve bulge → spec 10's sleeve not simulated with our bands present; everything looks pink-cream → albedo in sRGB fed as linear (prototype (a)).

---

## 9. Build order, effort and risks

### 9.1 Order (`scripts/parts/12_hard_armour.py --stage <n>`, each stage idempotent and renderable alone in Workbench)
| # | Stage | What is produced | Effort (cloud) | Depends on |
|---|---|---|---|---|
| 1 | `stand_ins` | the §6 proxies on the posed body; `Kneepad.*.CapProxy` v0 (ellipsoid 165 × 195 × 30) | 1 h | body posed, anchors |
| 2 | `lib` | `armour.py` helpers (`loft_shell`, `outline_patch`, `rim_bead`, `cut_slots`, `rivet`, `finish_shell`) with unit renders of a test plate with every feature | 4 h | prototypes §3, §8 |
| 3 | `hardware` | `cam_buckle`, `ladder_lock` (25/38), rivet, strap ends in `gear_hardware.py`; Workbench macro renders | 3 h | — |
| 4 | `kneepad` | cap, base, tab, strap, buckle (left), mirror, `CapProxy` v1; V9/V10 Workbench | 4 h | 1–3, trousers pocket surface or stand-in |
| 5 | `guard` | sleeve, foam, three plates, window, straps, hardware; V7/V8 | 5 h | 1–3, `Arm.*.GuardFrame`, `measure_arm()` |
| 6 | `pauldron` | tier 1 with recess/plate/studs/tab, tier 2 with slots/rivet/strobe, tier 3 with elastic/buckle, links; V5/V6 | 7 h | 1–3, acromion anchors, strap anchor (spec 13 or stand-in) |
| 7 | `elbowcap` | fin, pad, backing, elastic, mirror; V8 | 1.5 h | elbow anchor, shirt pocket surface |
| 8 | `materials` | `mat_hard.py`: TanPolymer with region attribute, BrushedAlu, hardware, lens, neoprene, elastic, rubber; decals via `decals.py`; wear bakes | 6 h | 4–7 geometry final |
| 9 | `rig` | helper bones, parenting, Data Transfer weights, pose test, flat variant | 2 h | spec 08 rig |
| 10 | `eval` | `measure_armour()`, masks, IoU, colour, light-swap, critic sheet | 4 h | 1–9 |
| | **Total** | | **≈ 37 h** cloud; Cycles beauty passes on the GPU machine ≈ 2 h | |

### 9.2 Risks
| Risk | Likelihood | Mitigation |
|---|---|---|
| EXACT booleans on lofted shells leave long triangles / fail on near-tangent cutters (kneepad corner indents, groove bars on a curved plate) | medium | cut before Solidify on the single-sided surface where possible (grooves, recess) and extrude the cutter ≥ 2 mm beyond both faces; fall back to `FAST` for shallow recesses; dissolve pass; unit test in stage 2 |
| Cap-to-body clearance differs between rest and hero pose (deltoid bulges under the pulled-back right arm) | medium | clearance check runs in both poses; cap may shift 0–3 mm outboard; pad hides the gap |
| Spec 09's pocket vs our external pad (D10) | medium | interface change requested in §10.1; until then our base sits on the stand-in pocket surface and the pocket is re-simulated with `CapProxy` v1 |
| Spec 10's sleeve bulge beside the guard bands buries the main plate's edges | medium | foam at +4.5–8.5 absorbs the bulge; if the bulge exceeds +12 the script raises the foam to 5 mm and logs it |
| Pointiness unreliable (prototype) | high → handled | Bevel-node mask for metal, baked wear images for polymer |
| Strobe lens volume slows Cycles | low | 2 cm³ of volume; cap volume steps at 8 |
| Right pauldron's read depends on the right humerus solve (spec 08 D2) | medium | the V2 overlay tolerance accepts the IoU 0.80; the cap is rigid to `pauldron.R`, so it follows whatever the IK decides |
| Emblem geometry recess on a doubly-curved cap distorts the shield outline | low | the recess is cut in (p, q) space and mapped, so its developed size is exact; the projected shape in V3 is compared, not the developed one |
| Hardware poly count (4 cam buckles, 4 ladder-locks with Subsurf) | low | ≈ 2.5 k each; Subsurf 1 only |

---

## 10. Interfaces and open questions for the client

### 10.1 What neighbouring parts must provide or respect
* **Body/arm (specs 04, 05, 08):** `Torso.Anchor.Acromion.L/R`, `Torso.Anchor.GH.L/R`, `Arm.L/R.GuardFrame`, `Arm.L/R.ElbowAnchor`, `measure_arm()` girths at s 12/40/90 % and the upper-arm sections at s 40/70 %, `Body.Mesh.Posed`, `Body.Collider`, `Morgan.Rig` with `clavicle`, `upperarm01/02`, `lowerarm01/02`, `upperleg02`, `lowerleg01` (MPFB `default` names); permission to add the six non-deform helper bones of §7.1 (spec 08 to list them in `BONE_MAP` as `PAULDRON`, `PAULDRON_MID`, `GUARD`, `ELBOWCAP`, `KNEEPAD`).
* **Shirt (spec 10):** `Shirt.Main` posed, bands `Shirt.Band.CapSeat/Tier3/GuardElbow/GuardWrist`, the elbow pocket outer ply. **Corrections requested:** tier 3 band at humerus **s 63–77 %** (not 58–83); forearm guard inner faces: sleeve **+1.5**, foam **+4.5**, plates **+8.5** (not 4.5); the wrist band spans **d 220–257 = s 81–95 %** (not 86–96); the sleeve bulge beside the bands may reach +12 (absorbed by our foam).
* **Trousers (spec 09):** `Trousers.L/R.KneePocket` outer surface after its sim; **correction requested (D10):** the kneepad is an external pad on the pocket, so the pocket's inner surface is no longer "cap + 2"; simulate the pocket against `Kneepad.*.CapProxy` as an *outer* collider placed at pocket + 0 (our base) — i.e. the pocket is simulated first with the leg only, then our base is wrapped onto it, then (optionally) a second short sim settles the pocket under our strap. Cap size for the proxy: **160 × 190 × 30 bulge** on a 184 × 214 × 4 base, centred at the knee axis + 15 up (not 170 × 200 × 28). Strap at h 530–550 behind the knee, trousers outer + 0.
* **Carrier (spec 13):** the shoulder-strap anchor `Carrier.Strap.L/R.PauldronHook` (a point on the strap's outer face 40 mm inboard of the pauldron's inner edge at s 0–5 %) for our 60 mm webbing tab; the straps must leave the 125 × 15 inner flange of each cap clear; the antenna behind the left shoulder must clear the left cap's posterior edge by ≥ 10 mm.
* **Gloves (spec 11):** gauntlet top at wrist −30; our wrist band ends at d 257 = wrist −13, so the band overlaps the gauntlet by 17 mm on the outside (band over gauntlet, as drawn at (692,340)); the gauntlet's outer surface at the wrist must be ≤ body + 8 there.
* **Materials library (spec 16):** `Thread.Black`, `cordura_material`, the hex → linear helper, `SurfaceImperfections015/017` loaders; we provide `mat_hard.py` recipes (TanPolymer, BrushedAlu, SilverSteel, Gunmetal, GreyPolymer) to it.
* **Evaluation scene (spec 17):** hero lights with the cool left fill strong enough for the light-swap test; the `ref/masks/armour_*.png` masks.

### 10.2 What this part provides
`Armour.StandIn.*` proxies (stage 1) and `Kneepad.L/R.CapProxy`; the final meshes and helper bones; `mat_hard.py`; `decals.py` (PIL mask generator, reusable for any stencil or patch); `measure_armour()`; the baked wear images `Armour.Img.Wear.*`; the `ArmourRegion` attribute convention for region-dependent wear.

### 10.3 Open questions for the client
1. **Emblem**: keep the rendered X-star (D4, recommended: it is what the picture shows and it is unique to the character) or replace it with the game's faction logo (the downward shield/arrowhead of the UI header)? If the latter, supply it as SVG; the decal pipeline is unchanged.
2. **Stencil text** on the forearm guards: three glyphs — what should they read (name initials, number)? Placeholder "7 2 A", smudged 45 %.
3. **Elbow caps**: mirrored pair as drawn (D5/D6, recommended, cheap), or omit the external caps entirely and rely on spec 10's internal pads (reality-pure)?
4. **Strobe**: static translucent lens (recommended) or an emissive variant for the game (a 2.0-emission flash material swap exists either way)?
5. **Game export of the 50/60/30 % helper blends**: accept the simplification of §7.4 (rigid to the deform parent) or add the six helper bones as deform bones to the export skeleton (costs six bones, keeps the behaviour)?
6. **Kneepad construction** (D10): external pad on the knee pocket as recommended, or cap inside the pocket as spec 09 first assumed (then the black surround becomes the pocket fabric and our base disappears)? Visually near-identical at hero distance; the external pad is the real product.
