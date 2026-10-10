# Part 13 — Plate carrier (JPC-class, olive-brown 500D) and back-mounted radio with antenna

Convention reminder (CLAUDE.md rules 1 and 2): every left/right below is the **soldier's own**; "viewer's left/right" is written out when the picture is meant. Spec units are **mm**; Blender units are metres. World frame: origin on the floor midway between the feet, +Z up, the character faces −Y, the camera is on −Y, **+X = his LEFT = viewer's right**. Reference pixel coordinates are full-image coordinates of `ref/reference_full.png` (1672 × 941); scale at the figure's depth **1 px = 2.12 mm** (4.72 px/cm, `analysis_consolidated.md` "Agreed scale"); height above the floor h = (895 − y) × 2.12 mm; lateral X = (x − 830) × 2.12 mm. The carrier's front face is ≈ 130 mm nearer the camera than the body's mid-depth plane, so its pixels are ≈ 3 % larger than the agreed scale; the rear bag and the antenna are ≈ 300 mm further, ≈ 7 % smaller (1 px ≈ 2.28 mm there). Both corrections are applied where they change a number.

Sources: `notes/analysis_consolidated.md` "Agreed scale", §1 (landmarks, rotations), §4 (clothing layers), §5 (cylinder/antenna, pauldron tabs), **§6 (load-bearing gear — read line by line)**, §9 disputes 1, 6, 8, 9, 15, 16; `notes/analysis_gear_inventory.md` §4 (4.1–4.7), §6, §19, §20 and its Errata; `notes/analysis_pose_proportions.md` §2, §6 (chest yaw, strap positions); `notes/analysis_lighting_camera_scene.md` §6 (camera and lights); `notes/research_dimensions.md` §1 (ANSUR trunk), §6 (SAPI/ESAPI plates, JPC sizes, PALS, pouches, buckles, hook-and-loop); `notes/research_prototypes.md` §1 (MOLLE panel prototype), §2 (mag pouch prototype), §8 (standard recipes: webbing strips, PALS rows, pouch bodies, buckles and ladder-locks, polymer caps); `notes/research_assets.md` §3 and the texture table (`Fabric063`, `poly_wool_herringbone`, `Plastic012B`, `Plastic018B`, `Metal027`, `Metal063`, `Rubber004`, `SurfaceImperfections015`); `notes/research_blender_capabilities.md` §5 (Geometry Nodes webbing), §6 (modifier stack), §10 (baking), Recommendations (render budget, context overrides); `spec/04_torso_neck.md` §3.1–§3.3, §3.5, §4.9 (rings, anchors, stand-ins), §10; `spec/10_combat_shirt_gaiter.md` §10.1 (offsets we must respect); `spec/12_hard_armour.md` §1.1, §4.7, decision D14 (pauldron tabs); `spec/08_rig_pose.md` §4.8 (rifle butt contact, `Vest.Collider`), the weight table rows "Plate carrier", "Carrier rear bag, cummerbund", "Antenna". Own zoom crops made for this spec with PIL (`python3 -I`, Lanczos, magenta grid every 10 px with full-image coordinates on the 50 px lines): `ref/zoom_carrier13_{whole_x4, panel_x10, pals_upper_x8, pouches_x8, lower_front_x6, strap_right_x10, strap_left_x10, antenna_x14, left_side_x8, cummerbund_left_x10, under_right_arm_x10}.png`, plus the gear analyst's ungridded `ref/zoom_vest_*.png`. The measuring script (luminance profiles and 5 × 5 colour means quoted in §2) is reproduced by `scripts/eval/measure_carrier.py` (§8).

**Source of truth (CLAUDE.md, "reality wins").** The drawing's carrier is identity-bearing in its arrangement (hard khaki panel high on the chest, a row of closed-flap pouches, stacked frames on the straps, a brass antenna behind the left shoulder, olive-brown over a black shirt), but its construction details are at a scale no real PALS grid can have (rows 11 mm tall on 28 mm pitch under the panel, pouches 60 mm wide, three adjusters stacked on one strap). Every dimension below therefore comes from the closest real product — a **Crye JPC-class carrier, size Large, with a SAPI/ESAPI Large plate, MIL-spec PALS, MIL-W-43668 Type III webbing, ITW Nexus-class hardware, a Harris AN/PRC-152-class handheld radio in a Tactical Tailor Fight Light-class pouch** — and the picture is used only for arrangement, colour, wear and the few details that carry identity. Every overrule is in the table of §2.4.

---

## 1. Purpose and acceptance

### 1.1 What this part is
Everything the soldier wears over the combat shirt (spec 10) and under the pauldrons (spec 12) to carry his plates and his front-line load: the **front plate bag** with its plate, top-loading plate pocket, bound edges, PALS grid (7 rows × 8 columns), lower **front flap**, **hard admin panel** (the khaki "electronics panel" riveted high on the chest), the unmated **side-release buckle** and the **knife pocket clip** on the first PALS row, **four closed-flap single rifle-magazine pouches** (three visible, one behind the rifle) with their flaps, pull strips, slide-lock plate, bindings, hook-and-loop, MOLLE straps and drain grommets; the two **padded shoulder straps** with their 38 mm webbing, gunmetal ladder-lock adjusters, sewn webbing keeper loops, elastic keepers and loose tails, and the webbing loops the pauldron tabs hook into; the **rear plate bag** with its plate, PALS grid and two wrapped **side wings**; the **cummerbund** (three PALS rows, ribbed 3D-mesh padding, 20 mm thick) and its front-flap closure; the **radio pouch** on the rear-left wing with a PRC-152-class radio body inside it and the **antenna assembly** (steel connector segment, brass sleeve with ring groove, black rubber-booted tip) rising behind the left shoulder; the small **left side pouch** on the cummerbund's forward column; all stitching, bar-tacks, bindings, grommets and labels; the materials (500D and 1000D Cordura, Type III webbing, binding tape, acetal, black-oxide steel, brass, rubber, khaki polymer) and their weathering. It also owns `Vest.Collider`, the stand-in that the rifle solve (spec 08 §4.8) and the pauldron tabs (spec 12) attach to. It does **not** own the belt, the upper-right two-cell pouch or the drop-leg rigs (spec 14, which hangs the upper-right pouch from our cummerbund's right-front column), the pauldrons, forearm guards or their tabs (spec 12), the shirt or gaiter under it (spec 10), the rifle that rests on it (spec 15) or the body (specs 03–05).

### 1.2 What "perfect" looks like
At hero distance (46 mm at 4.5 m) the carrier reads as a heavy, matte, slightly dusty olive-brown Cordura rig worn high and tight over a black knit shirt: a canted khaki hard panel at the collarbones with two bright studs, a dark label and a slot; seven even rows of webbing with their sag shadows; a row of fat closed-flap mag pouches whose bottoms vanish into shadow above two more rows and a black-bound hem; two padded straps crossing the gaiter's lower edge, each with a stack of three rectangular frames and a loose tail; the brass-and-steel antenna with its black cap standing just behind the left shoulder; a black-olive padded cummerbund showing at the left flank under the pouches. In a 300 mm-wide closeup every webbing strip is 25 mm wide and 1.3 mm thick with a rounded selvedge and a 2.5 mm herringbone rib, sags 3–4 mm between bar-tacks 38 mm apart, each bar-tack a 3 × 22 mm zigzag of 0.3 mm thread sunk into the cloth, each running stitch 3.6 mm long; the 500D weave is a 0.7 mm basket visible only on fold crests; every edge is bound in 12.5 mm black tape with a topstitch 2 mm inside it; the pouch flaps have a bound rim, a 25 mm pull strip and a 16 mm slide-lock plate, a black-oxide grommet at each bottom; the panel's chamfer, rivet shadows and chipped paint read as injection-moulded polymer bolted through fabric; the ladder-locks are 6 mm stamped frames with worn bright edges and webbing truly passing through them; the antenna's brass has a machined ring groove and anisotropic highlights, its cap a soft rubber sheen; nothing floats, nothing intersects the shirt, gaiter, pauldrons or rifle. A critic who has worn a JPC cannot name a dimension wrong by more than the tolerances of §8.6, cannot find a strap that goes nowhere, a pouch that could not hold a magazine, or a buckle with nothing through it.

### 1.3 Evaluation render views (rendered by `scripts/parts/13_plate_carrier.py --eval`, written to `renders/13_plate_carrier/`)

World positions in metres, posed; `Carrier.Root` (the sternum's front surface, §4.1) is at W ≈ (−0.05, −0.13, 1.30) and every target below is given relative to the world so the harness needs no part knowledge. Lighting for all views: the KEY/COOL/WORLD rig of `analysis_lighting_camera_scene.md` §6.2, AgX "Medium High Contrast", exposure 0; V2–V8 additionally render a "flat" variant (world grey 0.18, no key, Workbench matcap + cavity for the geometry checks of §8.6).

| View | Camera position (m) | Target (m) | Lens | Compared with | What it proves |
|---|---|---|---|---|---|
| V1 `torso_ref` | hero camera (0.00, −4.50, 0.60), rot (93.9°, 0, 0) | — | 46 mm | `ref/crop_torso_vest.png` = ×3 of (630,140)–(990,490); render full frame, crop the same box, upscale ×3 Lanczos | whole carrier at true scale: top edge, panel, rows, pouch row, hem, straps, cummerbund, antenna, colours under both lights |
| V2 `panel_close` | (−0.14, −1.00, 1.50) | (−0.11, −0.17, 1.43) | 85 mm | `ref/zoom_carrier13_panel_x10.png`, `ref/zoom_vest_admin_panel.png` | panel cant, 8 mm proudness, chamfer, studs, label plate, slot, corner rivet, boss, lower recess, chips; the SR buckle and knife clip below it; row 1 under the panel edge |
| V3 `pouches_close` | (0.05, −1.05, 1.30) | (−0.01, −0.21, 1.25) | 85 mm | `ref/zoom_carrier13_pouches_x8.png`, `ref/zoom_vest_mag_pouches.png` | four pouches (one behind the rifle stand-in), 70 mm bodies, 6 mm gaps, flaps, pull strips, slide-lock, bindings, grommets, dust on flap tops, grime at the bottoms, the lower rows and hem |
| V4 `strap_R_close` | (−0.45, −0.85, 1.72) | (−0.16, −0.10, 1.50) | 85 mm | `ref/zoom_carrier13_strap_right_x10.png`, `ref/zoom_vest_strap_right.png` | pad width and thickness, 38 mm webbing, ladder-lock, two keeper loops, loose tail, elastic keeper, crossing of the gaiter's edge, pauldron tab loop, row 1 root |
| V5 `strap_L_close` | (+0.40, −0.85, 1.72) | (+0.06, −0.10, 1.50) | 85 mm | `ref/zoom_carrier13_strap_left_x10.png`, `ref/zoom_vest_strap_left.png` | the mirror of V4 under the cool light; rear bag edge behind the trapezius; side pouch and left flank |
| V6 `antenna_close` | (+0.55, −0.45, 1.80) | (+0.16, +0.10, 1.56) | 100 mm | `ref/zoom_carrier13_antenna_x14.png`, `ref/zoom_vest_antenna.png` | cap, brass sleeve, ring groove, steel segment, 5° lean, 30 mm diameter, disappearance behind the strap and pauldron |
| V7 `cummerbund_L_close` | (+0.75, −0.65, 1.20) | (+0.17, −0.05, 1.12) | 85 mm | `ref/zoom_carrier13_cummerbund_left_x10.png`, `ref/zoom_vest_left_side_cummerbund.png` | 150 mm band, 20 mm thickness, three rows, ribbed padding at the edges, tuck under the front flap, hem binding |
| V8 `rear` | (+0.30, +2.20, 1.45) | (−0.05, +0.15, 1.30) | 50 mm | no reference (plausibility only; §8.7 Q12) | rear bag, wings, straps' rear roots and ladder-lock tails, radio pouch, antenna base, cummerbund's rear attachment |
| V9 `turntable_<piece>` | 4 views at 0/90/180/270° azimuth, 25° elevation, 700 mm radius, look-dev HDRI | piece centre | 60 mm | §3 tables | each sub-assembly alone (pouch, panel, strap, radio+antenna, buckle set): walls, thicknesses, hardware, wear distribution |

### 1.4 Pass criteria (scored by the critic, each 0–2; the part passes at ≥ 26/32 with no zero)
1. V1 overlay: carrier top edge within y 193–200, hem within y 394–402, pouch bottoms (shadow onset) within y 345–352, the two lit lower rows' centres within ±3 px of y 358 and 380; mask IoU of the carrier (front bag + pouches + straps, luminance-and-hue mask of §8.2) against the reference mask ≥ 0.88.
2. PALS pitch measured on V1 by autocorrelation of the luminance profile at x 855–875, y 340–400 (§8.3): 22 ± 2 px (= 47 ± 4 mm; the real 50.8 mm foreshortened by the chest's lean); row count below the pouches exactly 2.
3. Pouch row: exactly 3 pouch bodies visible between x 785 and 890 in V1, body widths 32 ± 3 px, gaps 2–4 px, one flap plate on the centre pouch; the fourth pouch's flap edge visible above the magwell at x 760–790 within ±4 px.
4. Straps: both pads 33–37 px wide in V1, three frames per strap at y 165–185 / 200–215 / 232–250 (±5 px), a tail visible on the right strap; no strap pixel over the gaiter above y 185.
5. Antenna: visible from y 135 ± 3 to y 185 ± 4 at x 898–912 ± 3, three tones in order cap/brass/steel (hue test §8.5), lean 3–8° backward.
6. Colour patches (§8.5): 16 named pixels within ±10/255 per channel of the reference after grading; Cordura median in the lit box (800–850, 245–262) within ΔE76 < 8 of #463e34.
7. Closeup construction (V2–V7 flat variants, `measure_carrier.py` ray grids, §8.6): webbing 25 ± 0.5 wide and 1.3 ± 0.2 thick, sag 3.5 ± 1.0, bar-tack pitch 38 ± 1 along rows, row pitch 50.8 ± 1, binding 12.5 ± 1 each side, pouch bodies 70 ± 2 × 160 ± 3 × 40 ± 3, gaps 6 ± 1, panel 175 ± 2 × 90 ± 2, 8 ± 1 proud, cant 2.6 ± 1°, pad 70 ± 2 wide 8 ± 1 thick, ladder-lock 52 × 44 × 6 ± 1, antenna Ø 30 ± 1 / cap Ø 32, stitch pitch 3.6 ± 0.3, no floating stitch.
8. Hardware truth: every ladder-lock and buckle has webbing passing through its slots (ray test §8.6), every strap end is folded 15 mm and bar-tacked, no strap hovers more than 0.5 mm off the surface it crosses.
9. Weathering placement: dust only where n·Z > 0.3 (flap tops, pad tops, panel top face, row crests), grime only within 25 mm of the hem and pouch bottoms, bright wear only on hardware edges and binding corners; no uniform "dirt wash" (§8.4 masks).
10. No intersection with the body, shirt, gaiter, pauldrons, rifle or arms in any view (boolean-intersect volume 0 mm³ in the flat variants; §8.6).
11. Rear view (V8): a JPC wearer recognises a rear plate bag, straps that return to it, a cummerbund that attaches to the wings and a radio that could be reached by the left hand (free judgement 0–2).
12. Critic's free judgement: "would a soldier who has worn a JPC accept this as his kit?" (0–2).
13. Game export (§7.4): the carrier, pouches and radio import into Godot as rigid children of the spine bones with ≤ 4 influences per vertex and no vertex moving > 3 mm relative to its plate under the hero pose (0–2).
14. Idempotence: the script rebuilt twice in one Blender process yields identical object counts and names, and `renders/13_plate_carrier/V1` differs by < 0.5 % RMS (0–2).
15. Build time within §9.4 budgets (0–2).
16. Stitches hidden (`--lod game`): the render differs from the full one only on the thread pixels (mask diff < 2 % of the carrier's pixels) (0–2).
Criteria 1, 3, 7, 8 and 10 may not score 0.

---

## 2. Reference observations

### 2.1 Extents (own measurements on `reference_full.png`, 5 × 5 means and luminance profiles; the analysts' values in brackets where they differ)

| Feature | Pixels (x, y) | World (mm) | Note |
|---|---|---|---|
| Front bag, top edge (bound) | y 195–198, x 740–890 | h 1478–1475 | 15–20 below the suprasternale (y 194, h 1485); hidden by the panel across x 745–828 and by the straps at 725–760 / 822–858 |
| Front bag, lateral edges | x 740 (his right) / 890 (his left) | X −191 / +127; width 150 px → 318 raw, **309 corrected** for the nearer depth | the bag's centre column is x 815 (X −32), not the panel's 786 |
| Front bag + flap, hem (bound) | y 395–400 | h 1060–1050 | dispute 6 adopted; a very dark band y 392–410 is the hem's shadow on the shirt |
| Exposed shirt band between hem and belt | y 400–490 | 190 tall | the carrier rides high (consolidated §6) |
| Admin panel | x 745–828, y 198–240 | 176 × 89 raw → 171 × 86 corrected; built **175 × 90** | his-right end 4 px higher: cant 2.6° (right end up) |
| Panel centre vs bag centre | x 786 vs 815 | 61 to his right | off-centre as drawn — identity, kept (D5) |
| Panel studs (vertical pair) | (752,208), (752,221) | panel u 15, v 21 and 49; Ø 3 px → 6 mm | lit #969491 / #908476 with blue-white speculars |
| Panel label plate | (770–795, 203–210) | u 53–106, v 11–26 → 53 × 15 | #766f6c median, dark grey |
| Panel horizontal slot | (768–790, 224–230) | u 49–96, v 55–68 → 47 × 13 | #74675e rim, dark floor |
| Panel his-left lower rivet | (818,231) | u 155, v 70; Ø 5 | #4f483f (in shade) |
| Panel raised square boss | (805–825, 205–235) | u 128–170, v 15–78 | faint; built 42 × 42 × 1.0 at u 128–170, v 22–64 |
| Panel lower-edge recess | y 236–240 along the bottom | 6 × 4 rebate | #2e2519 (795,230) analyst; #6d625b at (795,236) is the lit lip |
| PALS row 1 (under the panel) | y 240–252 lit webbing (x 770: 244–248 bright, 249–256 gap) | h 1389–1364 | the panel's lower edge covers the row's upper half |
| PALS row 2 (flap-top row) | y 257–265 (x 770: 257–261 mid) | h 1352–1336 | hidden by the pouch flaps from y 265 |
| Drawn upper-row pitch | 13 px | 28 mm | **impossible** for 25 mm webbing — overruled (D1) |
| Female SR buckle | (745–765, 243–265) | X_bag −158…−117, h 1380–1333; 42 × 47 drawn → built 33.5 × 30 × 8.5 on a 50 mm stub | #766958 lit face (dusted black acetal) |
| Black clip with silver pin | (800–815, 243–258) | 32 × 32 drawn; built 15 × 32 clip, Ø 4 screw | #564835 / pin #5f513d |
| Pouch flaps, top edges | y 265 | h 1336 | flap #5b5041 (830,272) |
| Pouch bodies (lit) | x 790–815 / 818–846 / 850–882; bodies to y ≈ 334 | widths 53 / 59 / 68 raw | bodies #16110c (R, in the rifle's shadow), #2f2c27 (centre), #302b27 (L) |
| Pouch bottoms | luminance at x 860: lit to 334, **black 336–349 (lum 1–7)**, lit webbing from 350 | bottoms at y 349 → h **1158**; pouch 1336 → 1158 = **178 tall** | matches a real 7 in single M4 pouch exactly (§3.4) |
| Pouch gaps | x 815–818, 846–850 | 3–4 px → 6–8 mm | #31261d in the gaps |
| Centre pouch's square plate | (826–834, 296–304) | 16 × 16 | #362f28 |
| Fourth pouch (inferred) | x 755–790 | X_bag −159…−85 | behind the receiver/magwell; its flap edge may show at y 265–275 |
| Lower lit rows A / B | y 350–366 / 372–388 at x 860–875 (centres 358 / 380) | h 1139 / 1092; **pitch 22 px = 47 mm** | consistent with 50.8 foreshortened by the lean (D1) |
| Hem binding | y 392–400, lum 20 | h 1066–1050 | #2a2826 at (820,396) |
| Right strap (pad) | x 725–760, y 160–255 | 35 px → 74 raw (built 70); centre X −187 | median #6d5f50, highlight #b4a697, shadow #0c0804; tail #22190e (745,170) |
| Right strap frames | y 165–185, 200–215, 232–250 | h 1548–1505, 1473–1441, 1405–1367 | (742,175) #33291e, (742,208) #b9a99a (bright specular), (742,240) #4e4133 |
| Left strap (pad) | x 822–858, y 160–255 | 36 px; centre X +21 | median #443d36, highlight #958a7f; cool side |
| Left strap frames | large (835–860, 165–185); small y ≈ 205, 240 | large 53 × 42; built ladder-lock 52 × 44 | #695d54 (845,175), #544a47 (840,205) |
| Elastic keeper (left) | (805–830, 150–175) | 25 wide | #3e3831 |
| Strap pair, midpoint and spacing | midpoint x 791, spacing 98 px | 208 mm; midpoint 51 to his right of the bag's centre | AI inconsistency — built symmetric at ±110 about the sternum (D6) |
| Rear bag edge visible | (890–930, 165–195) | behind the left trapezius | #62666e (910,180), cool-lit |
| Left side panel | x 862–885, y 220–290 | near-black | #070808 (872,250) |
| Small left side pouch | (875–895, 265–295) | 42 × 64 raw | #27211a (885,280); built 50 × 70 × 30 (D9) |
| Cummerbund, left flank | (840–900, 360–400) | h 1134–1050 visible; webbing band y 370–385 | #17130d median, rib #4b423a (890,375), slot #28231e |
| Cummerbund, under the right arm | (700–740, 380–400) | | #131211 (720,390) |
| Antenna cap | x 895–912, y 135–148 | Ø 17 px → **Ø 39 raw at the agreed scale, Ø 36 at its depth**; built cap Ø 32, body Ø 30 (D11) | #121618 (904,140) |
| Antenna brass body | y 148–170; ring groove y ≈ 152 | 50 mm visible; built sleeve 55 | #665a4c (903,152) → specular #a8a28e (905,158), #7e6f58 (903,165) |
| Antenna steel segment | y 170–185 (bright sliver x 908–913 runs y 150–185) | 34 mm visible | #777f85 (908,172), #717176 (909,178) |
| Antenna axis | x 905 at y 140 → 903 at y 185 | lean ≈ 5° back (reads as 2.5° in-plane) | world X ≈ **+157** at its depth (2.28 mm/px) |

### 2.2 Colour samples (own 5 × 5 means, lit as rendered; the consolidated samples in brackets where they differ)

| Area | px | Hex | Reading |
|---|---|---|---|
| Cordura, lit, beside the panel | (790,200) | #82705f | the brightest fabric on the carrier, key-lit and dusted |
| Cordura, lit webbing row 1 | (800,258) | #524637 [#625745] | olive-brown, dust on the crest |
| Cordura, bag median (box 800–850, 245–262) | — | **#463e34** | the material target |
| Cordura, shade under the rifle | (760,380) | #242221 | |
| Cordura, deep shadow (left flank) | (870,250) | #090b0b [#0f0b09] | |
| Panel face, lit | (805,215) | #867761 [#7e715f median] | khaki polymer, dusted |
| Panel label plate | (782,206) | #766f6c | neutral dark grey |
| Panel stud, upper | (752,208) | #969491 | silver with blue-white specular |
| Pouch flap top | (830,272) | #5b5041 [#574d3e] | dust on the up-facing flap |
| Pouch body, centre | (832,310) | #2f2c27 [#363028] | 1000D body, darker than the bag |
| Pouch bottom shadow | (832,340) | #060606 | occlusion, not paint |
| Right strap pad, lit | (742,195) → use the box median | #6d5f50 | olive webbing over black pad; the (742,195) point is the gap between frames (#0d0a07) |
| Left strap pad | (840,230) | #51463b [#443d36] | cool side |
| Rear bag (cool) | (910,180) | #62666e | the olive reads blue-grey under the cool light — same material |
| Cummerbund webbing | (890,375) | #4b423a | |
| Antenna brass | (903,152) / spec (905,158) | #665a4c / #a8a28e | brass under warm key: low saturation because the key is 4500 K, not a yellow paint |
| Antenna steel | (908,172) | #777f85 | cool-lit bare steel |
| Antenna cap | (904,140) | #121618 | rubber, cool rim |
| Hem shadow on the shirt | (820,420) | #54504b | the shirt, lit — not ours; the hem's cast shadow is the band above it |

### 2.3 Construction cues read from the zooms (my readings)
* **Panel.** In `zoom_carrier13_panel_x10` the panel is a shallow tray: a 4–5 px (≈ 9 mm) chamfered rim all round, a flat field, the label plate as a darker inset with a 1 px lighter rim (a recessed label, not a sticker), the slot as a dark pill with a lit lower lip, the two studs as domes with the key's specular at upper-left and a soft shadow ring; the his-left field is plainer with a faint lighter square (the boss); the bottom edge shows a 2 px dark line under a lit lip — an undercut/rebate. The panel sits on the fabric with a 1–2 px shadow under its lower edge: 6–8 mm proud. The top edge is flush with the bag's bound edge and tilts: right end 4 px higher.
* **Row 1 and its passengers.** Under the panel's lower edge a lit webbing row runs from the SR buckle at the his-right end to the left strap; the buckle is a dark rectangle with two lit windows (female half, the through-slot facing down), on a short stub that hangs from the bag's top corner. The clip at 800–815 is a flat black bar with a lighter rounded end and a bright dot at its lower end — a pocket clip with a screw, hooked over the webbing.
* **Pouches.** `zoom_carrier13_pouches_x8`: each pouch is a stuffed box with a soft horizontal bulge at mid-height (a magazine inside), a flap whose front face is lighter (up-tilted) with a vertical 25 mm strip down its centre ending in a tab; the centre pouch's strip carries a square plate at the flap edge; the bodies show 1–2 px vertical lit lines at their outer edges (piped/bound vertical seams) and a faint horizontal line 10 px below the flap (the flap's hinge seam on the back panel). Bottoms end in black — the row of pouch bottoms is lit from above and occluded below.
* **Lower front.** Two lit rows at y 350–366 and 372–388 at x 850–890 (partly hidden by the handguard and light from x 800–845); row A is brighter at its upper edge (sag crest), both have 1 px dark seams at their bar-tack columns ≈ every 18 px (38 mm) — four bar-tack shadows visible between x 850 and 890 (851, 869, 887): **the drawn column pitch is real** (18 px = 38 mm).
* **Straps.** Right: in `zoom_carrier13_strap_right_x10` the three frames are light olive rectangles (webbing, not metal) with a dark slot between their upper and lower bars; the bottom frame is the darkest; between the frames the pad's black base shows (#0d0a07) with the olive webbing narrower than the pad; a loose tail of darker webbing (#22190e) folds down from the top frame to the second. The brightest point (742,208) is a specular on the middle frame's lower bar — a metal bar reads here. Left: a large light frame (53 × 42 px) with the strap clearly passing through and a bright edge (metal ladder-lock), two smaller frames below, a black band crossing at (805–830, 150–175) over the gaiter's lower edge (the elastic keeper), and the frames' lit edges are blue-white (cool light on metal).
* **Antenna.** `zoom_carrier13_antenna_x14`: a domed black cap wider than the body (overhang 1 px each side → Ø cap ≈ body + 2 mm), a brass cylinder with a lighter ring just under the cap and a dark ring groove at y ≈ 152, a bright vertical steel sliver along the right edge from y 150 to 185 (a specular on a steel tube seen past the brass's edge, i.e. the brass is a sleeve over a longer steel tube, or the steel is a second segment with the specular continuing up it), the body passing behind the strap and the pauldron cap at y 185. Lean to his right/back ≈ 2.5° in-plane.
* **Left flank.** `zoom_carrier13_left_side_x8`: between the pouch row's left edge (x 882) and the arm (x 905) the carrier's side is almost black with a horizontal lit band at y 275–300 — the small side pouch or the cummerbund's forward end; below (y 300–360) the shirt; `cummerbund_left_x10`: a 20 mm-thick dark olive band with a lit webbing row at y 370–385 and ribs at its upper edge, tucking under the hem at x 850.

### 2.4 Ambiguities and decisions (reality wins; the drawing is kept only where plausible and identity-bearing)

| # | Topic | As drawn / analysts | Reality (closest product) | Decision |
|---|---|---|---|---|
| D1 | PALS row pitch | 2 rows in 25 px under the panel (28 mm pitch, 11 mm webbing); the brief's "38 mm pitch" is the **column** pitch | MIL-spec PALS: 25 mm (1 in) Type III webbing, bar-tacks every 38 mm (1.5 in), rows "1 in apart" → **row pitch 50.8 mm**; cross-checks: Esstac Tall 133 = 3 rows, BFG triple 140 = 3 rows (`research_dimensions` §6); the drawing's own lower rows measure 47 mm | **Row pitch 50.8, column pitch 38, webbing 25 × 1.3**; the two rows under the panel become row 1 half-covered by the panel and row 2 at the flap tops; `pals_rows()` takes `row_pitch` as a parameter in case a physical check says 38 [VERIFY on a real carrier] |
| D2 | Carrier size and plate | front bag 320 × 430 | JPC Large fits chest 41–45 in; our chest girth 1100 (43.3 in) → **Large**; SAPI/ESAPI Large plate 267 × 337 × ≤ 25.4, shooter's cut, multi-curve R457 × R254; bag = plate + 25 per side → **317 × 365**; plus a **front flap 59** → total 424 | Bag 320 × 365, flap to h 1054 (the drawn hem); plate top at h 1465 (10 below the bag's top edge), 20 below the suprasternale — correctly worn |
| D3 | Pouch size and count | 3 visible × 60 × 150, 6 mm gaps (+1 inferred) | single closed-flap 5.56 pouch (Eagle/Tactical Tailor class) 83 × 178 × 38; a STANAG mag is 190 long, 57 wide, 24 thick; **four 2-column pouches fill the 8 columns exactly** (4 × 76 = 304) | **4 pouches, bodies 70 × 160 × 40, flaps to 178 overall, 6 mm gaps on the 76 mm column pitch**; the measured drawn height (265 → 349 incl. the black bottoms) is already 178 — the analysts' 150 stopped at the lit part |
| D4 | Pouch contents | all look full | a soldier with two spare mags in his drop-leg carriers and four on the chest carries 7 (1 in the rifle): plausible | all four stuffed (mag bulge 4 mm), none empty |
| D5 | Panel identity and position | 175 × 90 × 6–8 khaki hard polymer, canted 2.6°, 61 mm to his right of the bag centre | no issue hard "admin panel" exists; closest: a chest-mounted hard phone/GPS case lid (Juggernaut.Case IMPCT-class, 165 × 85 × 20) or a hard placard; the studs/label/slot are a device lid's features | **Keep as drawn (identity): 175 × 90 × 8 injection-moulded khaki polymer tray with the details of §3.5**, screwed through the bag's loop field; cant and offset kept |
| D6 | Shoulder strap positions | drawn pair centred 51 mm right of the bag, spacing 208 | straps leave the bag's top edge ≈ 40 in from its edges, symmetric | **Symmetric at ±110 from the sternum** (inner edge 75, outer 145); the V1 overlay will deviate up to 25 px on the right strap — accepted |
| D7 | Three stacked frames per strap | right: "three gunmetal ladder-locks"; left: "one large tri-glide + two smaller" | one adjuster per strap is physics; JPC listing: "webbing loops on shoulder straps"; the frames at h 1473–1441 and 1405–1367 are below the bag's top edge, i.e. on the front bag's strap root | **Per strap: one gunmetal 38 mm ladder-lock at the pad's end (h 1548–1505), two sewn 38 mm webbing keeper loops on the bag's strap root (h 1473–1441, 1405–1367), the adjuster's loose tail folded down through the keepers and under a black elastic keeper**; the right's bright middle frame = the keeper's metal slide bar (a 38 mm wire keeper), kept as a specular source |
| D8 | SR buckle and the "clip" | female 25 mm SR unmated; black clip with silver pin (knife clip vs male buckle half) | an unmated female SR at a bag's top corner is the placard buckle of a JPC-class front; a male half with a "pin" does not exist; a folding knife's pocket clip hooked on PALS webbing is common | **Female SR (33.5 × 30 × 8.5) on a 50 mm stub at the his-right top corner of row 1, unmated; its left counterpart hidden behind the left strap root. The clip is a folding knife's deep-carry pocket clip (15 × 32 × 2, Ø 4 screw) with a 110 × 30 × 15 handle hidden behind pouch 2's flap** (D8 open question 3) |
| D9 | Left side panel and small pouch | near-black panel with a PALS row and a small olive/grey pouch (875–895, 265–295) | the carrier's left flank is the cummerbund's front end + the bag's bound edge; a small GP/compass pouch on the cummerbund's forward column is plausible | **Build `Carrier.L.SidePouch` 50 × 70 × 30 (flap, 25 mm webbing tab) on the cummerbund's forward-left column, rows 1190–1139**, default ON; the "panel" is the bag's edge and cummerbund in shadow, not a separate part |
| D10 | Cummerbund rows and height | 3 PALS rows, 20 thick, visible 1134–1050 | JPC/6094-class cummerbund 3 rows = 150 tall; spec 04 placed `Torso.Ring.Cummerbund.Top/Bottom` at 1180/1050 | **3 rows, 150 × 20, h 1050–1200, rows at 1088/1139/1190 aligned with the front bag's rows**; spec 04's top ring moves 1180 → 1200 [cross-spec] |
| D11 | Antenna identity and size | Ø 30 brass + steel cylinder, 105 visible, black cap; radio antenna base (best) vs flare | a PRC-152's antenna port is a TNC (Ø 15); a Ø 30 brass sleeve is an **antenna base adapter / relocation mount** class part; a 40 mm flare is Ø 40 and has no cap | **Radio antenna assembly: steel TNC/connector segment Ø 26, brass adapter sleeve Ø 30 × 55 with a 1.5 mm ring groove, black rubber-booted stubby tip Ø 32 × 24 dome**; drawn Ø 36–39 overruled to 30/32 (the drawing's 17 px includes the specular bloom) |
| D12 | Where the radio is | "mounted on the rear plate bag / upper back"; spec 04 anchor at W (+212, +118, 1505) | the antenna pixel x 905 at its depth is W X ≈ +157; a flat rear bag's left edge is at X ≈ +113 (sternum −47 + 160); a radio on the rear bag's **left wing** (wrapped 40° round the back-left corner of the torso) puts the antenna at +150…+160 and keeps a PRC-152 pouch (229 tall) reachable by the left hand | **Radio pouch on the rear bag's left wing, angled 40°, top at h 1420, antenna base centre at W (+158, +102, 1420) rising to the cap top at 1610 with a 5° backward lean**; spec 04's anchor should move to (+158, +102, 1505) [cross-spec, §10.3] |
| D13 | Pouch-bottom shadow band (336–356) | "shadow" (consolidated) | it is the pouches' lower 26 mm in the shadow of their own bulge and of the rifle | pouches reach 1158 (D3); the band is reproduced by geometry, not by a painted gradient |
| D14 | Rear bag | invisible from the front | JPC rear: same bag as the front without the flap; straps root into it with ladder-locks; cummerbund attaches inside its side flaps | Rear bag 320 × 365 + two 60 mm wrapped wings; PALS 7 × 8; `V8` is plausibility-only |
| D15 | Colour vs the loadout icon | icon grey-khaki carrier | the figure is authoritative (consolidated §6) | olive-brown #463e34 albedo (0.07, 0.06, 0.045) |
| D16 | Carrier top edge height | spec 10 asks for 1470 posed to hide the gaiter's seat (lowest fleece 1481); the drawing's bound edge is 1475–1478 | a plate worn at the jugular notch | **Top edge 1475**, panel top 1473; the gaiter's seat ring must be at ≤ 1480 at the front (spec 10 §10.1 confirms 1481 lowest visible) |
| D17 | Thighs/legs short (consolidated §1) | — | not our part; the carrier's hem-to-belt band (190) is fixed by the hem (1054) and the belt (spec 14): with ANSUR legs the belt moves, not our hem | no change here; noted for spec 14 |

---

## 3. Real-world reference

Tags: **M** measured on the reference, **S** sourced (`research_dimensions.md` §6 unless another note is named), **E** estimated from the product class, **[VERIFY]** where a published sheet should replace the estimate.

### 3.1 Identity and component list
A **jumpable-plate-carrier-class rig, size Large** (Crye JPC 2.0 / LBT 6094-slick class): front and rear 500D Cordura plate bags with top-loading plate pockets, PALS fields on both bags, 25 mm bound edges, two padded shoulder straps with front adjusters, a three-row padded PALS cummerbund closing under a front flap, a hard chest panel (D5) and a row of four closed-flap single-magazine pouches; a **PRC-152-class handheld radio** (72 × 236 × 44 body [S: 2.0 × 9.3 × 1.7 in, Harris datasheet class — VERIFY]) in a **Fight Light-class radio pouch** (229 × 76 × 57, S) on the rear-left wing, with a brass antenna base adapter and a rubber stubby tip. Weights (for spec 08's COM): carrier 0.5 kg (S, JPC "just over one pound") + 2 ESAPI-L plates 2 × 2.9 kg [S: ESAPI L ≈ 6.4 lb — VERIFY] + 4 loaded mags 4 × 0.5 + pouches/panel 0.6 + radio 1.1 (S class) ≈ **9.0 kg**, centre of mass 60 mm in front of the spine at h 1300.

### 3.2 Plates and plate bags

| Component | Dimension (mm) | Tag | Note |
|---|---|---|---|
| ESAPI Large plate, outline | 267 × 337 (10.5 × 13.25 in) | S | shooter's cut: top corners clipped 57 at 45° (S, "50–65") |
| Plate thickness | 25 (max 25.4) | S | edges rounded r 6; 2 mm nylon wrap; the bag's foam adds 4 |
| Plate curvature | longitudinal R 457, latitudinal R 254 (multi-curve) | S | sagitta over 267 wide = 36 mm; over 337 tall = 32 mm |
| Front bag outline | 320 wide × 365 tall; top corners clipped 60 at 45° following the plate; bottom corners r 20 | E (plate + 25 per side) | drawn 309–318 wide |
| Front bag build-up (inner → outer) | shirt contact 0 → back panel 500D 0.6 + PU 0.1 → 6 mm closed-cell foam (compressed to 4) → plate pocket wall 0.6 → plate 25 → front wall 0.6 → front face loop/PALS layer 1.3 | E | **outer face at body + 31** (spec 10 §10.1 wants exactly this) |
| Plate pocket flap | top-loading, 40 tall × 300 wide, hook-and-loop 25 × 280 inside, bound edge; a horizontal topstitch 40 below the bag's top edge | E | mostly hidden by the panel; visible at x 828–890 |
| Front flap ("MOLLE flap") | 300 wide × 59 tall below the bag, 500D over 1000D, bound; carries PALS row 7; inner face loop field 150 × 50 for the cummerbund ends | E (JPC class) | hem at h 1054 = `Torso.Ring.Hem` 1053 |
| Rear bag outline | 320 × 365, same cuts; no flap | E | |
| Rear bag side wings | 2 × (60 wide × 200 tall) from h 1420 to 1220, wrapping 40° forward round the torso's rear corners; PALS 1 column × 4 rows (1393…1241) | E (AVS/6094 class) | the radio pouch and the cummerbund's rear ends attach here |
| Edge binding (all free edges) | 25 mm nylon binding tape folded → 12.5 visible each side, 0.8 thick, 1 mm grosgrain rib; topstitch 2 inside the tape | S (MIL-T-5038 class widths) / E | black #0f0b09 |
| Drain grommets | #0 spur grommets, hole Ø 6.4, flange Ø 11, black oxide; 2 per bag at the pocket's bottom corners (X ±120, 12 above the pocket bottom) | S (#0 size) | hidden by pouches on the front; visible on the rear |
| Loop field under the panel | 180 × 95 hook-side on the panel's back, loop on the bag | S (A-A-55126, 2.0 hook / 2.5 loop) | not visible (D5: the panel is also screwed) |
| Bag PALS field | 7 rows (centres h 1393, 1343, 1292, 1241, 1190, 1139, 1088) × 8 cells (bar-tack columns at X_c −152, −114, −76, −38, 0, +38, +76, +114, +152) | D1 | row 7 is on the front flap; rows 3–5 hidden behind the pouches |

### 3.3 PALS webbing, stitching and thread

| Item | Value | Tag |
|---|---|---|
| Webbing | MIL-W-43668 Type III nylon, 25.4 wide, **1.3 thick**, selvedge rounded r 0.6; herringbone rib period 2.5 across, 1.2 along | S (type) / E (thickness 1.0–1.5) |
| Sag | 3.5 mm at mid-cell for a cell carrying nothing (webbing length = cell + 2–3 mm ease), ±20 % per cell random, 0.5 mm Z jitter, 0.3–0.5° roll | E (`research_prototypes` §1, §8) |
| Bar-tack | 3 wide × 22 long (1/8 × 7/8 in class), 42 stitches = 21 zigzag passes at 1.05 pitch, thread Ø 0.30; one at every column line across the full webbing height; the end tacks 6 in from the webbing ends | S (class) / E |
| Running stitch | 3.6 pitch (7 spi), 2.2 stitch / 1.4 gap on the visible side, 2 inside each webbing edge **and** along both edges of every binding tape | E (matches spec 09's 3.6) |
| Thread | Tex 70 (#69) bonded nylon, Ø 0.30, colour matched: olive-brown (0.10, 0.085, 0.06 linear) on Cordura, black (0.03) on binding and webbing-to-pad seams | S (class) |
| Webbing length per cell | 38 + 3 = 41 (sagging) | E |
| Columns per bag row | 8 cells, 9 bar-tack lines; the end lines 8 in from the bag's bound edge | E |
| Cummerbund rows | 3 rows × 6 cells each side (flank) + 4 cells (rear wing continuity) | E |

### 3.4 Magazine pouches (four identical, pouch 3 carries the slide-lock plate)

| Component | Dimension (mm) | Tag | Note |
|---|---|---|---|
| Body (outer) | 70 wide × 160 tall × 40 deep; vertical edges r 8 (bevel 8/3 → Subsurf); bottom edges r 6 | E (class 83 × 178 × 38 incl. flap; 70 = 2 columns − 6 gap) | STANAG mag 57 × 24 × 190 inside, standing 30 proud of the body top |
| Walls | 1000D Cordura 0.9 + PU 0.1; black 2 mm piping cord in the 4 vertical seams and the bottom perimeter (black #0f0b09, Ø 2 welt) | E | the lit vertical lines of §2.3 |
| Back panel | 70 × 196 (160 body + 36 extension carrying the flap hinge and the MOLLE straps); hinge seam 10 below the body top (topstitch across) | E | |
| Flap | 70 wide; 18 rise at the back + 40 over the top + 45 down the front = 103 developed; 1000D doubled 2.4 thick + 12 mm black binding on its three free edges; centre dome 4 (stuffed look) | E | front edge at h 1273 (y ≈ 294) |
| Pull strip | 25 mm webbing down the flap's centre from the hinge over the top to 30 below the flap edge, folded double (pull tab 25 × 30 × 2.6), bar-tacked at the flap edge and at the top | E | the "vertical centre strip" |
| Slide-lock plate (pouch 3 only) | 16 × 16 × 3 black acetal, chamfer 0.8, two 3 × 26 slots for the strip, sits at the flap edge | E (D3) | drawn (826–834, 296–304) |
| Closure | hook 25 × 40 on the body front 15 below the body top (under the flap), loop 25 × 40 on the flap's inside | S (widths) | hidden; modelled as flat 2 mm pads for the closeup turntable |
| Drain grommet | #0, hole Ø 6.4, flange Ø 11, black oxide, bottom centre | S | one per pouch |
| MOLLE straps | 2 × 25 mm webbing, 160 long, sewn to the back panel at the top, woven through bag rows 2, 3, 4 and the pouch's own rows (two 25 mm rows on the back at 1292 and 1241), ends tucked (no snaps) | E | hidden except 2 × (25 × 12) stubs above the hinge |
| Gaps | 6 between bodies, bodies centred at X_c −114, −38, +38, +114 | D3 | pouch 1 (X_c −149…−79) behind the rifle |
| Vertical placement | body top h 1318, body bottom 1158, flap top 1336, flap edge 1273 | M + D3 | |
| Stuffed shape | mag bulge +4 at mid-height on the front, sides pinched −2 at the elastic-free waist; top corners rounded by the flap | E | Displace Clouds 60 mm / 3 mm + the bulge |

### 3.5 Hard admin panel (D5; coordinates u to his left, v down, from the panel's his-right top corner, before the cant)

| Feature | Dimension (mm) | Tag |
|---|---|---|
| Tray outline | 175 × 90, corners r 6; 8 proud (lid 6 + 2 standoff), wall 2.5 | M / E |
| Perimeter chamfer | 45° × 5 on the top edge of the rim, rim face 9 wide | M (4–5 px) |
| Field | flat, 0.3 orange-peel texture (bump), paint khaki over dark grey substrate | E |
| Studs (LED/rivet domes) | Ø 6 domes 2.2 high, polished stainless, at (15, 21) and (15, 49); a 0.3 shadow ring | M |
| Label plate | 53 × 15 recessed 0.6, dark grey anodised, 0.5 mm lighter rim, 3 lines of 1.2 mm engraved text (illegible, bump only) at (53–106, 11–26) | M / E |
| Horizontal slot | 47 × 13 pill, 4 deep, floor dark, lower lip lit, at (49–96, 55–68) | M |
| Corner rivet | Ø 5 dome 1.5 high, stainless, at (155, 70) | M |
| Raised boss | 42 × 42 × 1.0 at (128–170, 22–64), edge r 1 | M (faint) |
| Lower-edge rebate | 6 wide × 4 deep undercut along the bottom edge (the "dark recess") | M |
| Fixings | 4 × M4 button screws Ø 7 heads at the corners (10, 10), (165, 10), (10, 80), (165, 80) — the his-left lower one is the drawn corner rivet | E |
| Cant | 2.6° (his-right end up) about the panel's centre; placement: centre at X_c −61, top edge 1473 (right corner), the bag's top edge 1475 | M |
| Chipping | 2–8 mm chips on the chamfer and the rim corners exposing #2e2b27–#453d3b; scratches along the field diagonals | consolidated weathering |

### 3.6 Hardware

| Item | Dimension (mm) | Material / finish | Tag |
|---|---|---|---|
| Ladder-lock, 38 mm (2, strap adjusters) | 52 × 44 outer, bars 4 wide × 6 thick, two slots 40 × 5, centre bar with a 1 mm grip rib | black-oxide stamped steel, worn bright edges | E (spec 12 used the same) |
| Keeper loop (4, straps) | 38 mm webbing 25 long sewn across the strap root, bar-tacked both ends; a 38 × 8 × 2 steel slide bar under the middle one (right strap) | webbing + steel | D7 |
| Elastic keeper (2) | 25 wide × 2 thick, 70 circumference, ribbed 1 mm | black elastic | E |
| Side-release buckle, 25 mm (1 visible female + 1 hidden) | female 33.5 × 30 × 8.5 (through-slot, two side windows, bar slot); stub webbing 25 × 50 × 1.3 | black acetal, dusted | S (prototype) |
| Knife pocket clip | 15 × 32 × 2, hooked end r 3, screw head Ø 4 at the lower end; handle 110 × 30 × 15 hidden behind pouch 2's flap | black-oxide spring steel / Torx screw bright | E |
| Grommets | #0 (hole 6.4, flange 11), 6 total | black oxide brass | S |
| Panel screws | 4 × Ø 7 button heads | stainless, dusted | E |
| Slide-lock plate | 16 × 16 × 3 | black acetal | E |
| Hook-and-loop fields | hook 2.0, loop 2.5 thick | black | S |
| Radio pouch bungee | Ø 4 shock cord, 2 × 60 long, with a 10 × 20 cord lock | black | E |

### 3.7 Shoulder straps (each)

| Component | Dimension (mm) | Tag |
|---|---|---|
| Pad | 70 wide × 8 thick (6 closed-cell foam + 2 × 1 fabric: 500D top, 3D mesh underside), 230 long from the rear bag's top edge over the shoulder to its front end at h 1548; edges bound 12.5 black; rounded ends r 20 | S ("~75 wide, 6–10 pad") / E |
| Webbing | 38 mm Type III, 1.5 thick, sewn down the pad's centre (two running stitches 2 in from its edges), continuing 60 beyond the pad's front end into the ladder-lock | E |
| Front strap root | on the front bag: 38 mm webbing 110 long from the bag's top edge (sewn into the plate pocket flap seam) up to the ladder-lock; two keeper loops at h 1473–1441 and 1405–1367 (on the root, i.e. on the bag face beside the panel) | D7 |
| Adjuster | ladder-lock at h 1548–1505 (centre 1527), the webbing from the root passes up through it; loose tail 120 long folds down the outside through both keepers and under the elastic keeper; tail end folded 15 and bar-tacked | D7 |
| Rear root | 38 mm webbing into the rear bag's top edge with a second ladder-lock (rear adjustment, visible only in V8) | E |
| Pauldron tab loop | 25 mm webbing loop 30 long on the pad's lateral edge at h 1440 (spec 12 D14 tab hooks here: drawn (720–730, 215–230) right, (885–895, 205–220) left) | spec 12 |
| Centre-line | ±110 from the sternum, path = `Torso.Curve.Strap.L/R` (body + 6 over the trunk, + 10 over the gaiter band) | D6 / spec 10 |
| Hydration/cable loops | none (the keepers do this job) | — |

### 3.8 Cummerbund

| Component | Dimension (mm) | Tag |
|---|---|---|
| Band | 150 tall × 20 thick (2 × 500D 0.6 + 6 mm foam + 12 mm 3D spacer mesh toward the body, compressed to 20), length 2 × 480 (each side from the rear wing to the front centre overlap) | E (JPC/6094 class, "125–150") |
| PALS | 3 rows centred h 1088, 1139, 1190; 6 cells per flank + 2 on the wing | D10 |
| Edges | bound 12.5 black; the top and bottom edges show the spacer mesh as 4 mm ribs (bump + 1 mm edge geometry) | M (ribs) |
| Front closure | both ends 150 × 120 hook under the front flap's loop field; the flap's lower edge covers them; a 38 mm elastic section 80 long per side behind the pouches (stretch) | E |
| Rear attachment | ends sewn into the rear wings (hidden) | E |
| Body offset | inner face at body + 1.3 (shirt) + 2 ease; outer face + 23 | spec 10 |
| Left side pouch | 50 × 70 × 30, flap with 25 mm tab, on the forward-left column, rows 1190–1139, top at h 1210 | D9 |

### 3.9 Radio, radio pouch and antenna

| Component | Dimension (mm) | Tag |
|---|---|---|
| Radio body (hidden) | 72 × 44 × 236 (with battery), top face: antenna TNC Ø 15 × 18 at the his-left front corner, volume and channel knobs Ø 18 × 12, a 6 × 12 PTT, a 60 × 25 display on the front (hidden) | S class [VERIFY] |
| Pouch | 76 wide × 57 deep × 229 tall, 1000D with a Hypalon top collar 30 tall, bungee closure Ø 4 over the radio's shoulders; bottom grommet; 2 × MOLLE straps (3 rows) | S |
| Placement | on the rear bag's left wing, angled 40° about Z from the back plane (its outer face turned toward his left and to the rear, i.e. toward the camera's left-rear), centre W (+158, +100, 1305), top at 1420 | D12 |
| Antenna assembly, from the radio top | TNC connector Ø 15 × 18 (hidden) → **steel connector segment Ø 26 × 60** (bare steel, brushed; 1440 → 1500, visible from 1505) → **brass adapter sleeve Ø 30 × 55** (1500 → 1555; ring groove 1.5 wide × 0.8 deep at 1540; chamfer 1 at both ends; machined, light anisotropy) → **rubber boot Ø 32 × 24**: cylinder 10 + hemispherical dome r 16 (1555 → 1579 → cap top at **1610** including a 31 mm whip stub inside the boot cylinder — see note) | D11 / M |
| Antenna total | from the pouch top 1420 to the cap top 1610 = 190 (85 hidden below the strap/pauldron at 1505) | M |
| Lean | 5° backward (+Y) about the base, in the YZ plane; 0° lateral | M (consolidated) |
| Visible colours | cap #121618, brass #665a4c → #a8a28e, steel #777f85 | M |

Note on the tip: a real stubby antenna is longer; the drawing shows the cap only 24 mm tall. Build the boot as a 24 mm dome (identity) and let the brass sleeve carry the length; the client may lengthen the stub (§10.3 Q7).

### 3.10 Fabrics and their micro-structure

| Fabric | Construction | Thickness | Weave scale | Weight | Tag |
|---|---|---|---|---|---|
| 500D Cordura (bags, straps, cummerbund faces) | plain/basket weave, ≈ 35 × 32 yarns per inch → yarn pitch 0.73 × 0.79; PU-coated back | 0.6 | 1370 per metre (u), 1270 (v) | ≈ 240 g/m² (7 oz) | E [VERIFY: Cordura data sheet] |
| 1000D Cordura (pouches, radio pouch, flap reinforcement) | plain weave, ≈ 27 × 27 → pitch 0.94 | 0.9 | 1060 per metre | ≈ 370 g/m² (11 oz) | E [VERIFY] |
| Type III webbing | 2/2 twill (herringbone appearance), rib 2.5 across | 1.3 (25 mm), 1.5 (38 mm) | rib period 2.5 | — | E |
| Binding tape | grosgrain, rib 1.0 along | 0.8 | 1.0 | — | E |
| 3D spacer mesh (pad undersides, cummerbund edges) | hex cell 4 pitch, 6–12 thick | — | 4 | — | E |
| Hypalon (radio pouch collar) | smooth rubberised | 1.2 | none (rough 0.55) | — | E |

### 3.11 How the real kit wears (for §5.6)
Dust settles on every up-facing fabric crest (webbing sag crests, flap tops, pad tops, the panel's top face and its rim), lightening #463e34 toward #776958; it does not stick to vertical Cordura. Grime collects where hands and the rifle rub: the pouch fronts' lower 30 mm, the hem, the right strap's lower half (rifle stock), the panel's edges (hands) — darkening toward #1a1810 and raising the sheen slightly. Binding tape frays and lightens at corners (a 10 % lift at pointiness > 0.6). Webbing edges fuzz and lighten where pouches have been moved (rows 2–4). Hardware: black oxide wears to bright steel on ladder-lock bars where the webbing runs (roughness 0.45 → 0.25, metallic colour 0.10 → 0.60), rivet domes stay bright with a blue-white key specular. The panel's khaki paint chips at the chamfer corners and the slot's lower lip (2–8 mm flakes to dark substrate), the field is scratched diagonally. Brass tarnishes to a dull olive-brown (#665a4c) except where handled (the groove's shoulders, #a8a28e specular). Nothing is torn, no loose threads longer than 5 mm.

---

## 4. Geometry construction plan

All steps are in `scripts/parts/13_plate_carrier.py`, using `scripts/lib/gear_webbing.py` (`strip`, `pals_rows`, `bartack`, `running_stitch`, `binding`), `scripts/lib/gear_hardware.py` (`ladder_lock`, `sr_buckle`, `grommet`, `screw_head`, `pocket_clip`), `scripts/lib/gear_pouch.py` (`mag_pouch_single`, `flap`, `pull_strip`, `radio_pouch`), `scripts/lib/mat_fabric.py`, `scripts/lib/mat_hard.py`, `scripts/lib/measure.py` and the recipes of `research_prototypes.md` §8. Everything is bmesh/bpy procedural with modifiers; no sculpting, no painting. Names follow `Carrier.<Side>.<Component>`; collection `Carrier` with sub-collections `Carrier.Front`, `Carrier.Rear`, `Carrier.Strap.L/R`, `Carrier.Cummerbund`, `Carrier.Pouch.1–4`, `Carrier.Panel`, `Carrier.Hardware`, `Radio`. The script deletes every object, material, image and node group whose name starts with `Carrier.`, `Radio.` or `Vest.` before rebuilding and never touches other parts' objects (CLAUDE.md rule 4).

### 4.1 Step 0 — frames, inputs and the carrier's own coordinate system
* Read `assets/interfaces.json`: `torso.ring.CarrierTop` (h 1470, Y −118), `torso.ring.Hem` (1053), `torso.ring.Cummerbund.Top/Bottom`, `torso.curve.Strap.L/R`, `torso.anchor.Suprasternale`, `torso.anchor.Antenna`, `shirt.offset.trunk` (1.3), `shirt.offset.gaiterBand` (10), spec 12's `armour.pauldron.tab.L/R`. Missing entries fall back to the numbers in this spec and are logged as `[FALLBACK]`.
* **`Carrier.Root`** (Empty, arrows): at the sternum's front surface in the posed body, X_c = X of `Torso.Anchor.Suprasternale` (expected −47 ± 10), Y_c = the shirt's front surface at h 1300 (expected −0.130 m), Z = 1300; rotation = the chest's posed yaw (−5°) and extension (−3°) read from `DEF-spine.003`/`spine01` so that the bag's grid is square to the plate, not to the world. All front-bag coordinates below are in this frame (X_c lateral, +X_c = his left; d = outward from the chest along −Y_c; h = world height).
* Body surface sampler `body_surface(x, h, side)`: ray-casts `Body.Collider` (spec 04) + `shirt.offset` along the local normal; used for the straps, the cummerbund and the rear bag.
* Units: metres in Blender; every constant below is written in mm in the script's `DIMS` dict and converted once.

### 4.2 Step 1 — plates `Carrier.Front.Plate`, `Carrier.Rear.Plate`
bmesh grid 28 × 36 over 267 × 337; Z-displacement from the two radii (sphere-free torus-like surface: `d = R_lon − sqrt(R_lon² − v²) + R_lat − sqrt(R_lat² − u²)`); shooter's cut by `bmesh.ops.bisect_plane` at the two top corners (57 at 45°), bottom corners rounded r 15 by `bmesh.ops.bevel` on the two vertices (segments 4); Solidify 25 (offset −1: the outer face stays exact), Bevel 6 / 3 segments at 60°, shade smooth. The plate is a hidden render object (`hide_render = True`) but drives the bag's shape and `Vest.Collider`. The rear plate is the mirror (curvature inward toward the back), rotated so its concave face follows the back's lateral curvature at h 1300 (torso §3.3: half-breadth 168, back Y +118). ≈ 2.2 k tris each.

### 4.3 Step 2 — bags `Carrier.Front.Bag`, `Carrier.Rear.Bag`
1. Outer surface: Shrinkwrap a 40 × 46 grid (320 × 365) onto the plate's outer face with `offset` 0.0025 (0.6 wall + 1.3 face layers + 0.6 pocket wall) — `NEAREST_SURFACEPOINT`, then **apply**; the margin ring outside the plate (25 wide) is lofted down to the inner-face level with a quarter-round (`bmesh.ops.inset_region` 25 + translate inward 29 + `smooth_vert` 2 iterations) so the bag has the soft rolled edge of a stuffed bag, not a plate's hard edge.
2. Inner surface: `Solidify` thickness 31 (offset −1), `use_even_offset`, rim on; the inner face is later flattened against the chest by a Shrinkwrap to `Body.Collider` + 1.3 (`PROJECT`, negative direction, only the inner-face vertex group `Carrier.Front.Inner`) so the bag meets the shirt everywhere (`Torso.Compress.Carrier` −4 is already in the body).
3. `Bevel` 3 / 2 at the rim edges, `Subdivision` viewport 1 / render 2 (`use_limit_surface`), `Displace` (Clouds 90 mm, strength 1.5 mm, vertex group = outer face minus 20 mm margin) for the gentle quilting bulge between the PALS rows.
4. Front flap `Carrier.Front.Flap`: a 300 × 59 strip lofted from the bag's bottom edge (continuous normal), 2 × 1000D + 500D = 2.6 thick (Solidify), with a 6 mm forward bow at its centre (the cummerbund ends under it), bevel 1 / 2.
5. Plate pocket flap seam: a `running_stitch` line 40 below the top edge across 300 (visible beside the panel) and a 0.4 mm ridge (Displace by a stencil image is not needed: a 1-segment loop cut + 0.4 offset of the ring).
6. **Binding** on every free edge: `gear_webbing.binding(edge_loop, width 12.5, thickness 0.8)` = a curve from the boundary loop, Bevel object = a U-profile (12.5 + 0.8 + 12.5 developed, inner radius 0.4) sampled every 2 mm, converted to mesh, `Shrinkwrap` to the bag's faces to seat both lips; two `running_stitch` rows 2 inside each lip. Objects `Carrier.Front.Binding`, `Carrier.Front.BindingStitch`.
7. Grommets: `grommet(6.4, 11)` ×2 per bag at X_c ±120, 12 above the pocket bottom (hidden by pouches on the front).
8. Rear bag: identical minus the flap, plus `Carrier.Rear.Wing.L/R` — two 60 × 200 panels (500D over 1000D, 3.0 thick) lofted from the rear bag's lateral edges forward and wrapped 40° round the body's rear corners at h 1220–1420 (path sampled with `body_surface` at + 6 + the cummerbund's 20 beneath their lower 60 mm), bound edges, 1 PALS column × 4 rows.
Topology: quad grids throughout so Subdivision behaves; bag ≈ 6 k faces before subdivision, 24 k tris at render.

### 4.4 Step 3 — PALS fields `Carrier.Front.Webbing`, `.Stitches`, `.Bartacks` (and `.Rear.*`, `.Cummerbund.*`)
`gear_webbing.pals_rows(surface, rows_h=[1393,1343,1292,1241,1190,1139,1088], col_x=[−152…+152 step 38], width 25, thickness 1.3, sag 3.5, sag_jitter 0.2, z_jitter 0.5, roll_jitter 0.4°)`: for each row, one dense strip mesh along the surface (segment every 1 mm, 6 quads across) with analytic sag `3.5 · sin(πt)^0.8` between bar-tack lines, lifted along the surface normal; `Solidify` 1.3 (offset +1, even, rim), `Bevel` 0.6 / 3 / profile 0.5 at 60°, shade smooth; UV `u` along the strip (metres), `v` across (0–1), so the herringbone rib is driven by UV. Row 1 is clipped to the panel's footprint (the webbing runs under the panel: keep the geometry, the panel occludes it). Rows 3–5 behind the pouches are generated (they show in the 6 mm gaps and in the pouch-row shadow) but their stitches are skipped (`lod`). Bar-tacks: `bartack(3 × 22, passes 21, r 0.3, sink 0.15)` at every column line of every row (front 7 × 9 = 63, rear 7 × 9 = 63 + wings 8, cummerbund 3 × 7 × 2 = 42). Running stitches: 2 inside each webbing edge, 3.6 pitch, r 0.3, sunk 0.15, as 6-sided cylinders in one mesh per bag. Three objects per field so the game LOD drops `.Stitches` and `.Bartacks`. Count: ≈ 180 cells → 180 strips ≈ 50 k tris; bar-tacks 176 × 21 × 12 ≈ 44 k tris; running stitches ≈ 180 × 2 × 11 × 12 ≈ 48 k tris. `pals_rows` writes each cell's centre and normal into `Carrier.Grid.json` for the pouch and buckle placement.

### 4.5 Step 4 — hard admin panel `Carrier.Panel.*`
1. `Carrier.Panel.Tray`: rounded-rect 175 × 90 r 6 extruded 8, `inset` 9 on the top face then the rim's outer top edge chamfered 45° × 5 by `bmesh.ops.bevel` (1 segment, profile 0.5, then `Bevel` modifier 0.6 / 3 on the remaining edges for the moulded look); the field recessed 1.0 below the rim top (a tray). Lower-edge rebate: boolean DIFFERENCE with a 175 × 6 × 4 box along the bottom edge's underside. Label recess 53 × 15 × 0.6 and slot 47 × 13 × 4 (pill: box ∪ two cylinders) as EXACT booleans before the bevel; boss 42 × 42 × 1 as a UNION. `Weighted Normal`. ≈ 5 k tris.
2. `Carrier.Panel.Label`: 52 × 14 × 0.5 plate in the recess, anodised dark grey, text as a bump image generated by PIL (`Carrier.Panel.LabelBump.png`, 512 × 128, three lines of random 6-pt glyphs blurred 0.6 px).
3. `Carrier.Panel.Stud.1/2`: `screw_head(Ø 6, dome 2.2)` stainless; `Carrier.Panel.Screw.1–4`: `screw_head(Ø 7, button 1.8)`, the his-left lower one at (155, 70) = the drawn rivet.
4. Placement: parent all to `Carrier.Panel.Frame` (Empty) at X_c −61, h 1428 (centre), on the bag face (d = bag outer + 0 → the tray's underside is Shrinkwrapped to the bag face, `NEAREST_SURFACEPOINT`, applied, so the 8 mm proudness is measured from the fabric), rotated 2.6° about d (his-right end up), 1.5° about X_c (top leaning back to follow the plate's curvature). The bag face under the tray is flattened by a `Shrinkwrap` of the bag's vertices inside the footprint toward the tray's underside (vertex group `Carrier.Front.PanelBed`), so fabric and polymer meet with no gap.

### 4.6 Step 5 — buckle, clip and strap roots on row 1
* `Carrier.Front.SR.R` = `sr_buckle(25, 'female', 33.5 × 30 × 8.5)` (EXACT booleans on one manifold box: through-slot, two windows, bar slot; Bevel 1.0 / 3 at 30°, Weighted Normal); stub `strip(25 × 50 × 1.3)` from the bag's top edge at X_c −138 down through the buckle's bar slot and folded back 15, bar-tacked; the buckle hangs 25 below the top edge against row 1 at X_c −158…−117, h 1380–1333, rotated 6° about d (it hangs). The left mate `Carrier.Front.SR.L` sits behind the left strap root (X_c +138), unmated too.
* `Carrier.Front.KnifeClip`: `pocket_clip(15 × 32 × 2, hook r 3)` hooked over row 1's upper edge at X_c −26, the clip on the outside, the screw head Ø 4 at its lower end (bright steel); `Carrier.Front.KnifeHandle` 110 × 30 × 15 rounded box behind the webbing and pouch 2's flap, black polymer, visible only in the gap between pouches 1 and 2 (3 mm).
* Strap roots `Carrier.Strap.R.Root`, `.L.Root`: 38 mm × 1.5 webbing strips from the plate pocket flap seam (h 1435, under the bag's top edge) at X_c ∓110 rising to h 1560 along `Torso.Curve.Strap.*` offset +31 at the bag (they lie on the bag face) then + 6 over the body; two keeper loops `Carrier.Strap.*.Keeper.1/2` = `strip(38 × 25 × 1.3)` wrapped round the root (circumference 2 × (38 + 1.5) + 2 × 1.3) at h 1473–1441 and 1405–1367, bar-tacked to the bag at both ends; `Carrier.Strap.R.KeeperBar` 38 × 8 × 2 steel bar under keeper 1 of the right strap (the drawn bright bar).

### 4.7 Step 6 — shoulder straps `Carrier.Strap.L/R.*`
1. Path: `Torso.Curve.Strap.L/R` re-sampled every 2 mm from the front bag's top edge (h 1475) over the trapezius slope (18°, spec 04 §3.5) to the rear bag's top edge; offsets: + 31 while over the bag faces (fading over 15 mm), + 6 over the trunk, **+ 10 across the gaiter band** (spec 10: x 725–760 / 822–858 from y 160 = h 1558 down to the bag), + 6 over the back.
2. `Carrier.Strap.*.Pad`: sweep of a 70 × 8 rounded-rect profile (r 4 top corners, r 2 bottom) along the path from h 1548 at the front (the pad's front end, rounded r 20 in plan by scaling the last 20 mm of profiles) to the rear bag's top edge; the pad is a quad grid (35 across × 1 per 2 mm), Solidify not needed (the profile is closed), Bevel 1 / 2, Subdivision render 1; `Displace` Clouds 40 mm / 0.6 mm for the foam's unevenness; bound edges (12.5) as in §4.3 step 6; two running stitches 2 inside the bindings.
3. `Carrier.Strap.*.Webbing` 38 × 1.5 strip down the pad's centre for the pad's whole length plus 60 beyond its front end, with two running stitches 2 inside its edges over the pad; the webbing is one continuous strip in the model, written as an explicit path so that the ladder-lock has webbing in both slots (criterion 8): bag top edge (the root of §4.6, sewn into the pocket-flap seam at h 1435) → up the bag face and over the body → **up through the ladder-lock's lower slot, over the centre bar, down through its upper slot** (this fold is what the adjuster grips) → the strip then turns back **up** along the pad's centre to the rear bag; the free tail is the strip's excess beyond the fold: 120 long, running **down** the outside of the root through keeper 1 and keeper 2 (between the keeper and the root), ending under the elastic keeper, folded 15 and bar-tacked. On the pad the strip carries two running stitches 2 inside its edges; over the body and on the tail it is unstitched.
4. `Carrier.Strap.*.LadderLock` = `ladder_lock(52 × 44 × 6, bars 4, slots 40 × 5)` at h 1527 centre, perpendicular to the path, rotated 3° (it tips when loaded); gunmetal with bar wear.
5. `Carrier.Strap.*.Elastic`: 25 × 2 ribbed band round the root + tail at h 1565 (left strap; drawn (805–830, 150–175)) and 1560 (right, hidden behind the tail fold), circumference 2 × (38 + 1.5 + 1.5) + 4.
6. `Carrier.Strap.*.TabLoop`: `strip(25 × 30)` loop on the pad's lateral edge at h 1440, standing 8 proud, bar-tacked; spec 12's pauldron tab hooks here.
7. Rear ends: `Carrier.Strap.*.RearLock` ladder-lock 52 × 44 × 6 at the rear bag's top edge, the pad's webbing through it, 60 mm tail folded into a keeper; visible in V8 only.
Per strap ≈ 9 k tris plus stitches 6 k.

### 4.8 Step 7 — magazine pouches `Carrier.Pouch.1–4.*`
`gear_pouch.mag_pouch_single(width 70, height 160, depth 40, flap=(18, 40, 45), strip 25, plate=False)` placed at the grid cells (X_c −114, −38, +38, +114; body top h 1318) with its back panel Shrinkwrapped to the bag's outer face + the webbing's 1.3 (the pouch rides on rows 2–4):
1. Body: box 70 × 160 × 40 → `Bevel` 8 / 3 on the vertical edges and 6 / 3 on the bottom edges → `Subdivision` 2 (render 3) → `Displace` Clouds 60 mm / 3 mm (cloth bulge) → mag bulge: a Lattice 2 × 2 × 4 scaled +4 at the front mid-height, −2 at the sides (the stuffed look); corner bevel below the Subsurf so the box keeps its sewn crease. Vertex groups `Front`, `Side.L/R`, `Back`, `Bottom`, `Top` for the UV seams and the masks.
2. Piping `Carrier.Pouch.n.Piping`: curves along the 4 vertical edges and the bottom perimeter, Bevel depth 1.0 (Ø 2), black; sunk 0.6 into the body.
3. Back panel extension 70 × 36 × 1 from the body top up to h 1336+, continuous with the flap (no floating hinge: prototype fault e), hinge topstitch across at h 1326.
4. Flap `Carrier.Pouch.n.Flap`: L-profile loft 17 × 17 sections (rise 18, top 40, front 45), 4 mm centre dome, `Solidify` 2.4, `Bevel` 1.2 / 2, `Subdivision` 1; binding 12 on the three free edges (as §4.3 step 6, width 12, thickness 0.8); the flap's front edge sits 2 mm proud of the body front (it covers a mag that stands 30 above the body and the hook pad).
5. Pull strip `Carrier.Pouch.n.Strip`: 25 × 1.3 strip from the hinge over the flap to 30 below its edge, folded double for the tab (2.6 thick, rounded end r 4), bar-tacked at the hinge and at the flap edge, running stitches along both edges over the flap. Pouch 3 only: `Carrier.Pouch.3.Plate` = 16 × 16 × 3 acetal plate with two 3 × 26 slots (EXACT boolean), the strip threaded through both slots (the strip path is split at the plate).
6. MOLLE strap stubs `Carrier.Pouch.n.Molle.1/2`: 25 × 12 × 1.3 visible stubs above the hinge where the straps enter bag row 2 (X ±19 from the pouch centre); the full straps are not modelled (hidden).
7. Grommet at the bottom centre, hook pad 25 × 40 × 2 on the body front (hidden under the flap; rendered in turntables).
8. Pouch 1 (behind the rifle): built identically; the rifle stand-in `Rifle.StandIn` (spec 15's proxy or a 60 × 30 × 300 box at the magwell) is loaded for the eval only.
≈ 8 k tris per pouch at render (prototype 7.1 k), 32 k for four.

### 4.9 Step 8 — cummerbund `Carrier.Cummerbund.*`
1. Path: for each side, sample `body_surface` at h 1125 (the band's centre) every 2 mm from the rear wing's forward edge (azimuth ≈ 130° from the front centre) round the flank to X_c ∓100 at the front (under the flap), offset + 3.3 (shirt + ease); the band's upper and lower edges follow the body at h 1200 and 1050 so the band twists with the flank (torso §3.3: half-breadth 160 at 1189, 155 at 1085).
2. `Carrier.Cummerbund.L/R.Band`: loft of a 150 × 20 rounded-rect profile (r 4) along the path, 75 × N quads, `Bevel` 1 / 2, `Subdivision` render 1, `Displace` Clouds 50 mm / 1 mm; the inner 12 mm of the profile's top and bottom faces carry the spacer-mesh rib bump (§5.4), the outer face is 500D.
3. PALS: `pals_rows(band outer face, rows_h=[1190,1139,1088], 6 cells per side from the front end backward, + 2 on the wing)` with the same strip/stitch recipe (§4.4).
4. Bindings 12.5 top and bottom edges; the front ends run 120 past X_c ∓100 toward the centre (the two ends overlap under the flap) and carry hook fields 2 thick (hidden); an 80 mm section of each band at azimuth 95–110° (under the armpit, hidden on both sides) is `Carrier.Cummerbund.*.Elastic` (38 × 2 ribbed, 3 bands) in place of the padded profile. The lit band at (850–900, 370–385) on the left is PALS webbing on the padded section, not the elastic.
5. `Carrier.L.SidePouch`: `gear_pouch.small_pouch(50 × 70 × 30, flap 20, tab 25)` on the left band's forward column at rows 1190–1139, top at 1210 (the flap's hinge above the band's top edge, as a real pouch's back panel does).
6. Under the right arm the band is in the rifle stock's shadow; nothing special.
≈ 10 k tris + stitches.

### 4.10 Step 9 — radio pouch, radio and antenna `Radio.*`
1. `Radio.Body` (hidden, `hide_render` unless `--turntable`): 72 × 44 × 236 rounded box r 4, top face with the TNC Ø 15 × 18 at (+20, −10) from the top centre, two knobs Ø 18 × 12 at (−18, 0) and (0, +12), a PTT 6 × 12; black polymer.
2. `Radio.Pouch`: 76 × 57 × 229 body (same recipe as §4.8 step 1 with bevel 6, Subsurf 2), 1000D; Hypalon collar: the top 30 of the body with a separate smooth material and a 2 mm rolled edge; bungee `Radio.Bungee`: two curves Ø 4 from the collar's front grommets up over the radio's shoulders to a `Radio.CordLock` 10 × 20 × 8 at the back; MOLLE strap stubs; grommet at the bottom. Parent to `Radio.Frame` (Empty) at W (+158, +100, 1305) rotated 40° about Z (outer face toward the camera's left-rear), the pouch's back Shrinkwrapped to the wing + 1.3.
3. Antenna `Radio.Antenna.Steel` cylinder Ø 26 × 60 (48 segments, cap top, Bevel 0.5 / 2), `Radio.Antenna.Brass` Ø 30 × 55 with a 1 mm chamfer each end and the ring groove (a 1.5 × 0.8 revolve profile: the profile curve is `[(13,0),(15,1),(15,14.2),(14.2,15),(14.2,16.5),(15,17.3),(15,54),(13,55)]` lathed), `Radio.Antenna.Cap` Ø 32: cylinder 10 + hemisphere r 16 (`bmesh.ops.create_uvsphere` 32 × 16 bisected), Bevel 0.3 at the cylinder's lower edge; all three on `Radio.Antenna.Frame` at the pouch top's TNC position W (+158, +102, 1420), tilted 5° about X toward +Y; the steel starts at 1440 (the 20 mm below is the TNC, hidden in the collar). ≈ 3 k tris.
4. Shadow-casting check: the antenna must be occluded below h 1505 by the left strap pad and pauldron cap in V1 (criterion 5); the script ray-casts from the camera to the antenna axis at h 1495 and 1515 and asserts hit/miss.

### 4.11 Step 10 — `Vest.Collider`, joins, origins
* `Vest.Collider`: Boolean UNION (EXACT, all manifold) of the front bag's outer shell (no PALS), the four pouches' bodies and flaps, the panel tray and the strap pads, decimated to ≤ 8 k faces (`Decimate` collapse 0.3), no bevel, `hide_render`; it carries the vertex group `Vest.RightPectoral` (faces with X −120…−220, Z 1280…1340 in world) for spec 08's rifle solve, and `Collision` modifier (`thickness_outer` 0.002) for spec 10's cloth if the shirt is re-simulated with the carrier on.
* Nothing is joined into one mesh except the stitch classes (one `.Stitches` and one `.Bartacks` object per field). Origins: bags and panel at `Carrier.Root`; pouches at their own back-panel top centre; straps at their front ladder-lock; cummerbund bands at their front end; radio parts at `Radio.Frame`; antenna at its base.
* All hardware parented to the fabric object it sits on; all fabric objects parented to `Carrier.Root` (front, straps, pouches, panel) or `Carrier.RearRoot` (rear bag, wings, radio) or `Carrier.CummerbundRoot.L/R`.

### 4.12 Topology notes and poly budget

| Object group | Base faces | Render tris (Subsurf, bevel) | Game LOD tris |
|---|---|---|---|
| Front bag + flap + bindings | 6.5 k | 26 k | 6 k |
| Rear bag + wings + bindings | 7 k | 28 k | 6 k |
| Panel + label + 6 screws/studs | 5 k | 9 k | 3 k |
| 4 mag pouches (body, flap, piping, strip, plate, stubs, grommet) | 4 × 3 k | 32 k | 4 × 1.2 k |
| 2 straps (pad, webbing, locks, keepers, elastic, tab loop) | 2 × 4 k | 18 k | 2 × 1.5 k |
| Cummerbund 2 bands + side pouch | 6 k | 14 k | 3 k |
| SR buckles, clip, handle | 3 k | 5 k | 1.5 k |
| Radio pouch, bungee, antenna | 4 k | 9 k | 2.5 k |
| PALS webbing (≈ 180 cells) | 180 × 6 × 41 = 44 k | 50 k | 50 k (strips kept; sag is the look) |
| Bar-tacks (176) | — | 44 k | 0 |
| Running stitches (webbing + bindings + flaps) | — | 60 k | 0 |
| `Vest.Collider` | 8 k | hidden | hidden |
| **Total** | | **≈ 295 k** | **≈ 85 k** |

Quad grids everywhere Subdivision is used; booleans applied under `temp_override` and followed by `dissolve_limit` 2° on flats away from cuts (spec 12 §4.8 recipe); Weighted Normal after bevels on hardware. UVs: bags, straps and cummerbund unwrapped from their grid parametrisation (u along the strip or across the bag, metres, so texel density is uniform); pouches `smart_project` per vertex group with seams on the piping; hardware `smart_project` 50°; webbing by construction.

---

## 5. Materials and textures

### 5.1 Material list (Principled BSDF, Blender 4.5; colours are **albedo** sRGB hex with linear RGB in brackets; the targets of §5.7 are lit pixels). Sheen is capped per `research_prototypes` §0: 0.06 on Cordura and webbing, 0.10 on thread, never above 0.15 on anything dark.

| Material | Objects | Base colour | Rough | Sheen | Spec IOR lvl | Normal / bump | Notes |
|---|---|---|---|---|---|---|---|
| `Carrier.Mat.Cordura500` | bags, flap, wings, pad tops, cummerbund faces, side pouch | #463e34 (0.070, 0.055, 0.040) | 0.78 | 0.06 (tint white) | 0.35 | `Fabric063` NormalGL tiled 13 mm (yarn 0.73) ×0.6 + procedural basket (Wave × Wave, scale 1370/1270 per m, distortion 0.4, bump 0.35) | `Fabric063` Color is **not** used (grey-green); roughness map ×0.9 + 0.1 |
| `Carrier.Mat.Cordura1000` | pouch bodies, flaps, radio pouch, flap reinforcement | #332d26 (0.040, 0.032, 0.023) | 0.80 | 0.06 | 0.35 | same, tiled 17 mm (yarn 0.94), bump 0.45 | reference bodies #363028 lit → albedo darker than the bag |
| `Carrier.Mat.Webbing` | PALS strips, strap webbing, keepers, stubs, pull strips, bungee sleeves | #4a4033 (0.072, 0.054, 0.036) | 0.72 | 0.06 | 0.35 | `poly_wool_herringbone` nor_gl tiled 2.5 mm across (u), 1.2 along (v) ×0.5 + Wave rib (period 2.5 mm, distortion 2) bump 0.3 | lit target #625745; edge fuzz mask lightens ×1.25 at pointiness > 0.6 |
| `Carrier.Mat.Binding` | all bindings, flap rims | #0f0b09 (0.004, 0.0025, 0.002) | 0.70 | 0.05 | 0.3 | Wave grosgrain 1.0 mm along, bump 0.25 | corner wear lightens to #2a2420 |
| `Carrier.Mat.Thread` | stitches, bar-tacks on Cordura | (0.10, 0.085, 0.060) | 0.60 | 0.10 | 0.4 | none (6-sided cylinders) | black thread variant (0.030) on bindings/pads |
| `Carrier.Mat.PadMesh` | pad undersides, cummerbund edge ribs, Hypalon collar (variant) | #1a1917 (0.011) | 0.85 | 0.0 | 0.3 | hex spacer-mesh bump 4 mm cell, 0.6 depth | Hypalon variant: rough 0.55, bump 0 |
| `Carrier.Mat.Elastic` | elastic keepers, cummerbund elastic | #141312 (0.007) | 0.85 | 0.0 | 0.3 | Wave 1 mm bands across, bump 0.4 | no wear |
| `Carrier.Mat.KhakiPolymer` | panel tray (paint layer) | #7e715f (0.21, 0.165, 0.115) | 0.52 | 0.0 | 0.5 | orange-peel Noise 3000/m, bump 0.08; `Plastic018B` roughness as scratch mask ×0.3 | chips to `Carrier.Mat.Substrate` by the §5.6 mask (spec 12's worn-paint recipe) |
| `Carrier.Mat.Substrate` | under chips | #352f2b (0.036, 0.029, 0.025) | 0.45 | 0 | 0.5 | — | dark grey-brown polymer |
| `Carrier.Mat.BlackAcetal` | SR buckles, slide-lock plate, cord lock, knife handle, radio body | #1c1c1e (0.012) | 0.40 | 0 | 0.5 | `Plastic012B` normal 0.3 + micro grain Noise 3000 | pointiness mid 0.66 lightens edges to 0.03 (prototype `polymer_material()`) |
| `Carrier.Mat.Gunmetal` | ladder-locks, keeper bar, grommets, knife clip | metallic 1.0, colour (0.10, 0.10, 0.11) | 0.45 | 0 | — | `Metal027` normal 0.4 | wear: colour → (0.60, 0.60, 0.62), rough → 0.25 where the webbing runs (bars) and at pointiness > 0.7 |
| `Carrier.Mat.Stainless` | panel studs, screws, clip screw | metallic 1.0, (0.70, 0.70, 0.72) | 0.22 | 0 | — | — | blue-white speculars come from the COOL light; dust 0.15 on up-faces |
| `Carrier.Mat.Anodised` | label plate | metallic 0.9, (0.18, 0.18, 0.19) | 0.38 | 0 | — | engraved text bump image `Carrier.Panel.LabelBump.png` 0.5 | |
| `Radio.Mat.Brass` | brass sleeve | metallic 1.0, (0.55, 0.42, 0.22) tarnished: mix 60 % with (0.30, 0.25, 0.17) by a Noise 400/m mask | 0.38 / 0.22 at the groove shoulders | 0 | — | anisotropic 0.5 along the lathe axis (Anisotropic Rotation 0.25), fine turning-mark bump (Wave 0.2 mm) 0.15 | lit target #665a4c → specular #a8a28e |
| `Radio.Mat.Steel` | steel segment | metallic 1.0, (0.56, 0.58, 0.60) | 0.30 | 0 | — | anisotropic 0.4 | lit target #777f85 |
| `Radio.Mat.Rubber` | antenna cap | #15181b (0.008, 0.010, 0.012) | 0.62 | 0.02 | 0.4 | `Rubber004` normal 0.3 | target #121618 |

### 5.2 Weave micro-structure
500D: two orthogonal `Wave Texture` (bands, sine, scale 1370 and 1270 per metre in the strip/bag UV space, distortion 0.4, detail 2) multiplied, then `Map Range` to a 0.35 bump height blended 50/50 with `Fabric063` NormalGL tiled at 13 mm (its own 5–8 mm twill is too coarse alone, prototype §1 fault b); the basket shows only on fold crests and in the closeups. 1000D the same at 1060 per metre and 17 mm tile. Webbing: the Wave rib at 2.5 mm across with `distortion 2`, plus a second Wave at 1.2 mm along at 30 % (the twill diagonal), per prototype faults c/d; UV `u` runs along the strip so the rib is always across it. Projection: UV on every curved body (never Object coordinates on pouches — prototype fault a).

### 5.3 Texel density and UV layout
Hero target 40 px/mm on everything within 0.6 m of the hero camera's chest framing (the front bag, pouches, panel, straps): the normal tiles are 2048 px over 13–17 mm (≈ 130 px/mm) so density is not the limit; the baked masks (§5.6) are 4096² over the front assembly's UV atlas (≈ 320 × 430 + pouches + straps laid out in 4 islands → ≈ 6 px/mm, enough for 2–8 mm chips and dust gradients). Rear bag, wings, cummerbund, radio: one 2048² mask atlas (≈ 3 px/mm). Game export: the same atlases downsampled to 2048 / 1024.

### 5.4 Rib and mesh structures (geometry + bump)
Cummerbund edges and pad undersides: hex spacer-mesh bump (Voronoi F1 smooth, scale 250/m, ×0.6 depth) plus a 1 mm geometric step at the fabric/mesh boundary (the profile's inner 12 mm is 1 mm lower). The "ribbed padding" the analysts saw at the cummerbund's top edge is this mesh seen edge-on.

### 5.5 Decals and small images
`Carrier.Panel.LabelBump.png` (512 × 128) generated by PIL at build: three lines of pseudo-text (random glyphs from DejaVu Sans Mono 11 pt, blurred 0.6 px), used as a 0.5 mm bump only (illegible by design, no real markings). Radio pouch: a 20 × 8 woven label stub at its side seam (geometry, `Carrier.Mat.Binding`). No flags, name tapes or unit markings (consolidated §6 "not present").

### 5.6 Weathering masks (`Carrier.Masks.png` 4096², `Carrier.Masks2.png` 2048² for the rear set; baked once by `bpy.ops.object.bake` type EMIT from helper materials, research §10c)
* **R = dust**: `max(0, n·Z)` smoothstep 0.3→0.8 × (1 − AO) × `SurfaceImperfections015` tiled 300 mm; applied as a Mix to colour toward #8a7d6a (0.26, 0.21, 0.15) at 0–0.45 and roughness +0.1. Strongest on flap tops, pad tops, panel rim, webbing sag crests, cap of the antenna (0.1 only).
* **G = grime**: Z-gradient from the hem (h 1054 → 1130: 1 → 0) and from each pouch's bottom (0–30 mm: 0.8 → 0) × Noise 80/m, plus a 0.5 band on the right strap's lower half and the panel's rim (hands/stock); mixes colour toward #1a1810 ×0.6 and lowers roughness by 0.08.
* **B = edge wear**: pointiness (`Geometry → Pointiness`, Map Range 0.55→0.75) × Noise 600/m; on bindings lightens to #2a2420, on webbing ×1.25 lighter and roughness +0.05 (fuzz), on gunmetal the bare-metal mix, on the panel the chip mask threshold 0.66–0.72 (spec 12's recipe: Noise 180/m stretched 1,1,14 for scratches, blotch Noise 60/m for flakes 2–8 mm, a 0.15 mm lit paint step by bump at the mask edge).
* **A = stress whitening**: on webbing where pouches sit (rows 2–4, cells 1–8) 0.3; on the pull strips' tabs 0.5.
Hex targets after grading on V1: dust highlights on Cordura #776958, flap tops #574d3e–#5b5041, panel lit #867761 with chips #2e2b27–#453d3b, grime at pouch bottoms #030303–#0a0a0a (occlusion does most of it), ladder-lock bars bright #b9a99a at the specular.

### 5.7 Colour targets to hit after grading (reference pixels; render V1, read 5 × 5 means; tolerance ±10/255 per channel)
(790,200) #82705f Cordura beside the panel · (800,258) #524637 row 1 crest · box (800–850, 245–262) median #463e34 · (760,380) #242221 Cordura in the rifle's shade · (805,215) #867761 panel · (782,206) #766f6c label · (752,208) #969491 stud · (830,272) #5b5041 flap top · (832,310) #2f2c27 pouch body · (866,310) #302b27 pouch 4 body · (832,340) #060606 pouch bottom · (742,208) #b9a99a keeper bar specular · (840,230) #51463b left pad · (910,180) #62666e rear bag (cool) · (890,375) #4b423a cummerbund webbing · (904,140) #121618 cap · (903,152) #665a4c brass · (908,172) #777f85 steel.

---

## 6. Fibres, simulation or dynamics

### 6.1 Fibres
None as curves at hero scale. Webbing-edge fuzz and binding fray are shader (B mask). Optional `--fuzz`: 2 000 hair curves (radius 0.03 mm, length 1.5 mm, `Carrier.Mat.Webbing` colour) on the binding corners and webbing ends for V2–V5 closeups only, built with `bpy.data.hair_curves` + `Generate Hair Curves` restricted to the B-mask > 0.6 (research §3/§10a); ≈ +40 s per closeup. Not exported.

### 6.2 Simulation
None. The carrier is a stiff, plate-backed object: every surface is placed deterministically on `Body.Collider` + the shirt's offsets (Shrinkwrap), and the straps and cummerbund follow sampled body paths. The only soft behaviour — the shirt bunching above the hem and under the straps — belongs to spec 10, which may re-run its sim against `Vest.Collider` (`Collision` modifier provided, §4.11). The pouches' cloth bulge is Displace + Lattice (prototype §2, convincing). Reason for no cloth sim here (research §2): a 20-layer stuffed bag behaves as a solid, and a sim would only add non-determinism to a part whose every dimension is fixed by the grid.

### 6.3 Dynamics in animation (game)
Rigid follow of the spine bones (§7). Optional "slight lag" cannot be produced procedurally by the stock rig without a jiggle add-on; the Wiggle 2 add-on is **not** installed [VERIFY availability on Jeff's machine]; default = static blend of two bones (§7.1), which gives the "rigid-ish with slight lag" look in posed stills and a believable follow in animation.

---

## 7. Rigging and attachment

### 7.1 Bones and weights (spec 08's table, rows "Plate carrier", "Carrier rear bag, cummerbund", "Antenna"; MakeHuman bone names of spec 08; Rigify DEF- names in the export map)

| Object group | Method | Weights |
|---|---|---|
| Front bag, flap, panel, SR buckles, clip, pouches 1–4, strap roots | SKIN, nearly rigid | `spine01` 0.85 / `spine02` 0.15, uniform; pouches and panel take the bag's weights by `Data Transfer` (nearest face, vertex groups) so they move as one slab; `Torso.Compress.Carrier` −4 mm is already on the body |
| Shoulder strap pads, webbing, ladder-locks, keepers, elastic, tab loops | SKIN, graded | front third `spine01` 1.0; over the shoulder `clavicle.L/R` 0.6 / `spine01` 0.4 (the pad rides the trapezius); rear third `spine01` 0.7 / `spine02` 0.3; hardware rigid to the nearest strap vertex's weights |
| Rear bag, wings, rear strap locks, radio pouch, radio | SKIN | `spine01` 0.6 / `spine02` 0.4 uniform |
| Antenna (3 parts) | BONE parent to `spine01` | 5° lean preserved in the parent inverse |
| Cummerbund bands, side pouch | SKIN, graded along the band | rear end `spine02` 0.6 / `spine03` 0.4 → flank `spine03` 0.5 / `spine02` 0.3 / `spine04` 0.2 → front end `spine01` 0.3 / `spine02` 0.4 / `spine03` 0.3 (it must meet the front flap) |
| `Vest.Collider` | SKIN | as the front bag |
| Stitches, bar-tacks | `Data Transfer` from their fabric object | ≤ 4 influences per vertex |

### 7.2 Attachment to the neighbours
* **Shirt (spec 10):** the bag's inner face at body + 1.3 (Shrinkwrap), the straps at + 6 / + 10 over the gaiter band, the cummerbund at + 3.3; the carrier's top edge at 1475 hides the gaiter's seat (≤ 1480).
* **Pauldrons (spec 12):** `Carrier.Strap.L/R.TabLoop` at h 1440 on the pads' lateral edges is the hook point of the pauldron tabs; the pads' lateral edge at ±145 clears the tier-1 caps' medial edges (right cap medial edge x 718 → X −237 vs our pad outer edge X −47−145 = −192: 45 mm clear; left cap medial edge x 895 → +138 vs our +98: 40 mm clear).
* **Rifle (spec 08 §4.8, spec 15):** `Vest.Collider.RightPectoral` is the contact patch for the butt pad (0–3 mm); the handguard's light passes 20–40 mm in front of rows 6–7 (no contact).
* **Spec 14 (belt and rigs):** the upper-right two-cell pouch hangs from our cummerbund's right-front cells 1–2 (rows 1139/1088) via its own MALICE clips; we export those cells' centres and normals in `Carrier.Grid.json`.
* **Spec 04:** we read `Torso.Ring.*`, `Torso.Curve.Strap.*`, `Torso.Anchor.Suprasternale`; we ask for `Torso.Anchor.Antenna` → (+158, +102, 1505) and `Torso.Ring.Cummerbund.Top` → 1200 (§10.3).

### 7.3 Deformation checks (rest-mode and hero pose)
`measure.py`: (a) no vertex of the front assembly moves > 3 mm relative to `Carrier.Front.Plate` between rest and hero pose; (b) the strap pads keep ≥ 4 mm clearance to the gaiter's surface and ≤ 1 mm hover over the trapezius along their centre-lines (ray grid every 10 mm); (c) the cummerbund's inner face stays within 2–6 mm of `Body.Collider` round the whole flank in both poses; (d) the antenna stays within 0.5° of its 5° lean relative to the rear bag.

### 7.4 Export
glTF with the body (spec 18): `--lod game` hides `.Stitches`/`.Bartacks`, keeps webbing strips, bakes the §5.6 masks into 2048² colour/roughness/normal sets per atlas (bake type COMBINED for colour with lights off, ROUGHNESS, NORMAL), applies modifiers (names captured first; research §6 gotcha), scales ×0.9704 (1855 → 1800). Humanoid retarget: carrier groups map to Chest/UpperChest/Spine per spec 08 §3's table.

---

## 8. Evaluation protocol

### 8.1 Renders
V1–V9 of §1.3 at 1024 × 1024 (V1 full frame 1672 × 941), Cycles 64 spp adaptive 0.02, OIDN `RGB_ALBEDO_NORMAL`, `use_persistent_data`; flat variants in Workbench (matcap + cavity, 5 s each) for §8.6; `--look` preset 480 × 720 / 16 spp for the fast loop. Budget: V1 2–4 min, closeups 25–45 s each, turntables 4 × 20 s per piece (research Recommendations).

### 8.2 Silhouette and edge rows (`scripts/eval/measure_carrier.py --rows`)
Mask = pixels in the torso box (630–990 × 140–490) whose luminance is 10–140 and whose hue is olive-brown (H 25–50°, S > 0.12) or whose position is inside the known hardware boxes; the same on the reference; report IoU and the row positions by luminance profiles at x 770, 800, 860, 875 (top edge = first row with lum > 60 below the gaiter; hem = last row with lum < 25 before the shirt's lum > 40; pouch bottoms = onset of lum < 10 under the lit bodies; lower rows = the two lum maxima between the pouch bottoms and the hem). Targets in §1.4 criterion 1.

### 8.3 PALS pitch (`--pitch`)
Autocorrelation of the vertical luminance profile at x 855–875 averaged, y 340–400: first non-zero peak at 22 ± 2 px. Column pitch: horizontal profile at y 358, x 800–890: minima (bar-tack shadows) every 18 ± 1 px.

### 8.4 Weathering placement (`--masks`)
Render the §5.6 mask channels as emission (R, G, B) from the hero camera; assert R (dust) > 0.3 only where the normal AOV's Z > 0.3; G (grime) only within the hem band and the pouch bottoms (world Z < 1130 or within 30 mm above a pouch bottom); B on edges only (pointiness AOV > 0.5). Report the fraction of violating pixels (pass < 2 %).

### 8.5 Colour patches and the antenna hue test (`--colour`)
5 × 5 means at the §5.7 pixels after the AgX grading; the antenna column x 903–908: hue of rows 135–148 within 20° of blue-grey and lum < 40 (cap), rows 150–168 hue 30–50° (brass) with a specular ≥ 150 lum somewhere in them, rows 170–185 hue 200–230° and lum 100–130 (steel).

### 8.6 Construction checks (flat variants, `measure.py` ray grids and mesh queries)
Webbing width/thickness (ray pairs across a strip at 5 cells), sag (max normal offset mid-cell − at the bar-tack), bar-tack footprint (bounding box of the thread mesh per tack), row/column pitch from `Carrier.Grid.json` against the mesh, binding width (ray across an edge), pouch body dimensions (bounding boxes before Displace), gaps (nearest-point distances between adjacent pouch bodies at mid-height), panel dimensions, proudness (ray from the panel field to the bag face) and cant (plane fit), pad width/thickness, ladder-lock bounding box, antenna diameters (cross-section fits), stitch pitch (mean distance between consecutive stitch cylinders). **Hardware truth**: for each ladder-lock/buckle slot, a ray along the slot's axis must hit `Carrier.Strap.*.Webbing` or the stub inside the slot's volume; strap ends: every webbing strip's end faces must be within 0.5 mm of another webbing face (folded) and have a bar-tack within 20 mm. **Hover**: webbing/pad vertices' distance to the surface they cross ≤ 0.5 mm (except designed sag). **Intersection**: Boolean INTERSECT volume of each of our render objects with `Body.Collider`, `Shirt.Main`, `Gaiter.Main`, `Armour.Pauldron.*`, the rifle proxy and `Arm.*` meshes = 0 mm³ (tolerance 50 mm³ for the shrinkwrapped inner faces).

### 8.7 Questions the critic must answer (yes/no, with the view that proves it)
1. V1: does the carrier sit high and tight with the top edge just under the gaiter and the hem well above the belt, as in the picture? 2. V1: do the three visible pouches and the fourth's edge sit where the reference's do, with the bottoms vanishing into shadow? 3. V2: does the panel read as a moulded polymer tray bolted through fabric — chamfer, recessed label, slot with a floor, domed studs with shadow rings, a chipped rim? 4. V3: could each pouch hold a 30-round magazine (height, width, flap overlap), and are the flaps' pull strips and the one slide-lock plate convincing? 5. V3/V2: is every webbing row 25 mm wide with real sag, bar-tacks at 38 mm and running stitches, nothing painted on? 6. V4/V5: does each strap have exactly one adjuster with webbing in both slots, a tail that goes somewhere, two keepers and an elastic keeper, and does the pad cross the gaiter's edge without cutting into it? 7. V6: cap/brass/steel in order, Ø 30, a ring groove, a 5° lean, hidden below the strap? 8. V7: a 150 × 20 padded cummerbund with three rows, ribbed edges, tucked under the flap? 9. V8: would a JPC wearer recognise the rear — bag, wings, strap returns, radio pouch? 10. All: is dust only on top faces and grime only at the bottoms? 11. All: any floating stitch, hovering strap, or intersection with the shirt, gaiter, pauldrons, rifle or arms? 12. Free: is this his kit?

### 8.8 Known failure modes to check for
Webbing reading as wood grain (projection/distortion wrong, §5.2); the Cordura rendering khaki-light (sheen > 0.06 or albedo > 0.08); PALS rows at 38 pitch looking like corrugation (D1 wrong way); pouch gaps closing under Displace (clamp the Lattice); the panel floating on the quilted bag (PanelBed shrinkwrap missing); strap pads cutting the gaiter (offset + 10 band not applied); ladder-locks with no webbing through them (path order wrong); the antenna visible below the pauldron or in front of the strap (depth wrong); the rear bag's wings intersecting the lats in the pose; stitch tri count exploding (> 120 k: lower the rows' stitch LOD behind pouches); the cool light turning the whole left half blue-grey beyond #62666e (world strength too high); bar-tacks as bright beads (not sunk 0.15).

---

## 9. Build order, effort and risks

### 9.1 Dependencies
Specs 03–05 (`Body.Collider`, `Torso.Ring.*`, `Torso.Curve.Strap.*`, anchors), spec 10 (`Shirt.Main` offsets; the shirt may be re-simulated after us against `Vest.Collider`), spec 12 (tab positions; it hooks to our `TabLoop`), spec 08 (bone names, `Vest.Collider` consumer), spec 17 (camera/lights), `scripts/lib/gear_*.py` (shared with specs 12, 14, 15 — written once, here first because this part uses every recipe).

### 9.2 Build order inside the script (idempotent; each step deletes and recreates its own objects by name)
0 frames and inputs (0.2 s) → 1 plates (0.3 s) → 2 bags, flap, wings, bindings, grommets (2 s) → 3 PALS fields front/rear/cummerbund (strips 1 s; bar-tacks + stitches ≈ 8 s — the prototype made 896 thread cylinders in 3.3 s; we make ≈ 7 000) → 4 panel (1 s, EXACT booleans) → 5 buckles, clip, roots, keepers (1 s) → 6 straps (2 s) → 7 pouches ×4 (0.5 s) → 8 cummerbund + side pouch (2 s) → 9 radio, pouch, antenna (0.5 s) → 10 `Vest.Collider` (EXACT union of 10 manifolds ≈ 3 s) → 11 materials and node groups (0.5 s) → 12 mask bakes (2 × ≤ 60 s, research §10c; cached in `assets/cache/13/` by content hash) → 13 rig binding and Data Transfer (1 s) → 14 measurements (§8.6, 5 s) → 15 renders (`--look` 10 s; `--eval` ≈ 8 min total). Whole build without renders ≈ 25 s + bakes 2 min on first run.

### 9.3 Stability and sanity checks (automatic; failures abort with the step named)
Every boolean result must be manifold (`bmesh` `is_manifold` on all edges) and within 2 % of the expected volume; `pals_rows` asserts that every cell's four corners lie on the surface within 0.3 mm; the strap path must never come closer than 4 mm to `Gaiter.Main`; `Vest.Collider.RightPectoral` must contain ≥ 50 faces; the antenna occlusion test (§4.10 step 4) must pass.

### 9.4 Estimated script size and effort
`13_plate_carrier.py` ≈ 1 100 lines; `gear_webbing.py` ≈ 450, `gear_hardware.py` ≈ 350, `gear_pouch.py` ≈ 300 (shared); `measure_carrier.py` ≈ 250. Effort: 2 sessions for the libraries and the front assembly to a passing V1–V3, 1 session for straps, cummerbund, rear and radio (V4–V8), 1 session of critic rounds. Budgets: build ≤ 40 s, bakes ≤ 3 min, `--eval` ≤ 10 min.

### 9.5 Risks and fallbacks
1. **Row pitch dispute (D1).** If the client or a physical check says 38 mm, re-run with `row_pitch=38`: 9 rows fit the bag, pouches become 4 rows tall; everything else is unchanged. Low effort.
2. **Thread tri count** (≈ 100 k). Fallback: stitches only on rows 1–2, 6–7, straps and flaps; bump stitches elsewhere (research §8).
3. **Strap/gaiter clash** in the pose (the gaiter's rolls are higher on the back-left). Fallback: sample the strap path from the built `Gaiter.Main` instead of the ring offsets; last resort raise the pad's front end 10 mm.
4. **Cummerbund intersecting the lats/arms** under the arm pose (right arm abducted 20°, elbow back). Fallback: clip the band's top to 1180 under the right arm only (spec 04's original ring).
5. **Panel identity** (D5): if the client wants a real product, swap §4.5 for a Juggernaut-class case lid (165 × 85 × 20) — same frame, different tray.
6. **Antenna placement vs spec 04's anchor** (D12): the overlay decides; if the body's sternum X differs from −47 by > 15 mm, the radio frame follows `Carrier.Root` and the pixel test (§8.5) re-fits the lateral offset.
7. **Sheen bleaching** (prototype §0): keep the §5.1 caps; the calibration render of spec 17 confirms #463e34 before any other tuning.
8. **Boolean failures** on the SR buckle/ladder-lock (prototype §4: EXACT on a single manifold box is fine; unions of several boxes failed) — build each cutter as one manifold, cut one at a time.

---

## 10. Interfaces and open questions for the client

### 10.1 What this part needs from its neighbours
`Body.Collider` (trunk, hyoid to crest); `Torso.Ring.CarrierTop` (1470–1475), `Torso.Ring.Hem` (1053), `Torso.Ring.Cummerbund.Top/Bottom` (**1200**/1050 — change requested), `Torso.Curve.Strap.L/R` at body + 6; `Torso.Anchor.Suprasternale`, `Torso.Anchor.Antenna` (**move to (+158, +102, 1505)** — the present (+212, +118, 1505) projects 24 px outboard of the drawn cylinder); `shirt.offset.trunk` 1.3 and `shirt.offset.gaiterBand` 10 (spec 10 §10.1); spec 12's tab geometry (25 mm webbing tab, 20 exposed) to size `TabLoop`; the bone names `spine01–04`, `clavicle.L/R` (spec 08); the hero camera and lights (spec 17); the rifle proxy for V3 (spec 15 or a box).

### 10.2 What this part provides
Objects of §4; `Vest.Collider` with `Vest.RightPectoral` and a `Collision` modifier; `Carrier.Strap.L/R.TabLoop`; `Carrier.Grid.json` (every PALS cell's centre, normal and occupancy for specs 14 and 15); `assets/interfaces.json` entries `carrier.*` (top edge 1475, hem 1054, bag outer face = body + 31, strap offsets, cummerbund outer = body + 23, pouch front plane, radio frame, antenna axis); helpers `gear_webbing`, `gear_hardware`, `gear_pouch`, `measure_carrier.py`; the mass table of §3.1 for spec 08's COM; the mask atlases.

### 10.3 Open questions for the client
1. **PALS row pitch**: we build the MIL-spec 50.8 mm (the drawing's own lower rows measure 47); confirm, or ask for 38 (both are one parameter).
2. **Carrier size**: JPC-class Large with ESAPI-L plates (chest 43 in); Medium would narrow the bag to 290 and leave the pouch row 3 columns + gaps — confirm Large.
3. **The black clip with the silver pin** on row 1: folding-knife pocket clip (built) or the hanging male half of a second placard buckle (no pin)? If a knife, it has a hidden 110 mm handle behind pouch 2's flap.
4. **The hard admin panel**: keep the drawn fantasy tray (identity, built) or replace it with a real chest-mounted hard case lid (Juggernaut class, thicker)?
5. **Strap frames**: one ladder-lock + two webbing keepers per strap (built, reality) — or three ladder-locks as drawn (we advise against: it is not a thing)?
6. **Radio**: PRC-152-class in a Fight Light-class pouch on the rear-left wing (built); alternatives are a brass 40 mm flare or a chem-light tube clipped to the back — the antenna read is the analysts' and ours.
7. **Antenna tip**: the drawn cap is 24 mm tall; a real stubby antenna would add 60–120 mm of black whip above the brass. Keep the short cap (identity) or lengthen?
8. **Small left side pouch** (D9): default ON (50 × 70 × 30) — or off, leaving the flank bare?
9. **Fourth pouch** behind the rifle: built full (the loadout icon supports it); confirm, and confirm all four are loaded (7 mags with the drop-leg pair).
10. **Cummerbund** 3 rows / 150 tall (spec 04's ring moves 20 mm up) — or 2 rows / 130 as spec 04 drew it?
11. **Colour**: the figure's olive-brown (#463e34) over the icon's grey-khaki — confirm; and the dust level (light film on tops, as drawn) — confirm.
12. **Stitch geometry** on every row (≈ 100 k tris, hidden in the game LOD) — or only on the rows within 0.6 m of the hero camera?
13. **Placard buckle**: leave the female SR unmated and visible (as drawn) or hide it behind the panel (cleaner, less faithful)?
14. **Rear view**: no reference exists; do you want a second reference image of the back, or shall V8 stay plausibility-only?
