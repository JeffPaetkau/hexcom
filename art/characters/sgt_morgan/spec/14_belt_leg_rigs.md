# Part 14 — Belt, hip pouch and drop-leg rigs (rigger belt, cummerbund pistol-mag carrier, right twin-carrier leg platform, left two-cell leg platform)

Status: draft 1 (spec writer), 2026-10-07, written under the **reality-wins** rule (`CLAUDE.md`, Source of truth). Owner script: `scripts/parts/14_belt_leg_rigs.py` (plus the shared `scripts/lib/gear_webbing.py` for straps, PALS rows, bar tacks and stitches, `scripts/lib/gear_hardware.py` for the cobra buckle, ladder-locks, tri-glides, D-ring, screws and cord ends, `scripts/lib/mat_fabric.py` and `scripts/lib/mat_hard.py` for materials, `scripts/lib/decal.py` for stencil decals, `scripts/lib/measure.py` for the readback). Object prefix `Belt.*`, `RigR.*`, `RigL.*`, `PouchR.*`; collection `BeltRigs` with child collections `Belt`, `RigR`, `RigL`, `PouchR`, `BeltRigs.Stitches`.

Convention reminder (CLAUDE.md rules 1 and 2): every left/right below is the **soldier's own**; "viewer's left/right" is written out when the picture is meant. Spec units are **mm**; Blender units are metres. World frame: origin on the floor midway between the feet, +Z up, the character faces −Y, camera on −Y, **+X = his LEFT = viewer's right**. Reference pixel coordinates are full-image coordinates of `ref/reference_full.png` (1672 × 941); scale at the figure's depth **1 px = 2.12 mm** (4.72 px/cm, `analysis_consolidated.md` "Agreed scale"); height above the floor h = (895 − y) × 2.12 mm; lateral X = (x − 830) × 2.12 mm. The left leg stands ≈150 mm nearer the camera, so left-side pixels are ≈4 % larger (2.03 mm/px); the correction is ≤ 6 mm for everything in this part and is applied only where stated. "Z" below is a world height in the hero pose; "rest" is the A-pose deliverable.

Sources: `notes/analysis_consolidated.md` §1 (landmarks), §6 (Belt, Right side, Left side, Items NOT present, Weathering), §8 (camera, lights), §9 disputes 6, 9, 12; `notes/analysis_gear_inventory.md` §9–§11, §16–§20 and its errata; `notes/research_dimensions.md` §6 (buckles, pouches), §10 (belt), §13 (magazine); `notes/research_assets.md` (texture picks: `Plastic012B`, `Plastic018B`, `Fabric063`, `poly_wool_herringbone`, `Metal027`, `Metal038`, `Metal050C`, `Metal063`); `notes/research_prototypes.md` §1 (PALS), §2 (pouch and buckle), §8 (standard recipes); `notes/research_blender_capabilities.md` (render budget); `spec/03_leg_pelvis.md` §3.2–3.4 (pelvis and thigh dimensions), `spec/08_rig_pose.md` D1, D6, §7 attachment table rows "Belt and buckle (14)" and "Right drop-leg panel (14)", `spec/09_combat_trousers.md` §2.1, §4.9, §4.11, §7, §10.1 (strap footprints, belt loops, waistband). Own zooms made for this spec: `ref/zoom_belt14_rrig_grid_x6.png`, `ref/zoom_belt14_lrig_grid_x6.png`, `ref/zoom_belt14_upperpouch_grid_x8.png`, `ref/zoom_belt14_belt_grid_x6.png` (Lanczos zooms with full-image grid lines every 10 px) and the measurement script `ref/zoom_belt14_measure.py` (luminance profiles and edge finder used in §2); the earlier `ref/zoom_belt_*.png` set (×6–×12) was also read.

---

## 1. Purpose and acceptance

### 1.1 What this part is
Everything the soldier wears from the trouser waistband down to the lower thigh that is not clothing, armour or weapon: the black 1.75 in rigger belt with its quick-release buckle, D-ring, keeper and stitching; the two-cell polymer pistol-magazine carrier hanging from the plate carrier's cummerbund over his right flank; the right drop-leg platform with its hanger, two thigh straps, two open-top polymer rifle-magazine carriers, the two spare magazines in them, their shock-cord retention and cord tails; the left drop-leg platform with its hanger, one thigh strap, the olive Cordura frag-grenade pouch and the grey hard utility case in its elastic cradle; all hardware (ladder-locks, tri-glides, screws, snaps, latch, cord ends), stitching, bar tacks, binding tape, stencils, and weathering. Optional and off by default: a belt holster for the P9 at the small of the back (§4.12, open question §10.2). **Not** in this part: the trousers and their belt loops and compression footprints (spec 09, which owns the cloth deformation under our straps), the plate carrier and cummerbund (spec 13; we hang the pistol-mag carrier from it), the magazine mesh itself (spec 15 builds `Carbine.Magazine.PMAG30`; we instance it), the kneepad straps (spec 12).

### 1.2 What "perfect" looks like
At hero distance (reference camera, 46 mm at 4.5 m) the belt reads as a flat, dense, matte black webbing band of two sewn layers riding the trouser waistband, its buckle hidden behind the rifle magazine and a single bright D-ring glint at his right hip; on his right thigh two tall two-tone magazine carriers, dusty tan face plates on black bodies, stand proud of the camouflage with a black magazine base and a loop of shock cord above each, two flat black straps biting into the trousers with gunmetal frames at their inboard ends and two thin cord tails swinging below; on his left thigh an olive flap pouch and a grey hard case sit side by side in a black cradle above a single black strap; above the belt on his right flank the two-cell pistol-mag carrier hangs from the cummerbund. In a 300 mm-wide closeup every strap is a 38 mm herringbone webbing band 1.3 mm thick with a rounded selvedge and a folded, bar-tacked end; every ladder-lock is a 6 mm die-cast frame the strap really threads, its edges worn bright; the belt shows five rows of 3.5 mm stitches, the cobra buckle its two release tabs and adjuster bar; the face plates show four countersunk screws, one domed tension screw with a rubber washer, three slots with 1 mm radiused edges, a faint grey "5.56" stencil 60 % worn away, 2–6 mm paint chips on the edges exposing lighter polymer, dust in the slots; the Cordura shows a 0.5 mm yarn weave and 2 mm piping on every edge; nothing floats, nothing intersects, and a shooter would recognise every item as something he could buy.

### 1.3 Evaluation render views (all rendered by `scripts/parts/14_belt_leg_rigs.py --eval`, written to `renders/14_belt_leg_rigs/`)

Camera positions and targets are in mm, hero pose, world frame; they are nominal — the script places each camera relative to the anchor it reads back from the built meshes (§4.1) so a few millimetres of body change do not move the framing.

| View | Camera position | Target | Lens | Compared with | What it proves |
|---|---|---|---|---|---|
| V1 `hips_ref` | reference camera (0, −4500, 600), rot (93.9°, 0, 0) | — | 46 mm | `ref/crop_belt_hips.png` = ×3 of (630,410)–(990,630); render full frame, crop the same box, upscale ×3 Lanczos | arrangement, belt line, rig extents, strap heights, tone of plates and Cordura at the true scale; the belt row is expected to sit ≈ 65 px higher than drawn (§2.5 D1) |
| V2 `legs_ref` | reference camera | — | 46 mm | `ref/crop_legs_knees.png` = ×3 of (630,550)–(990,830) | lower straps against the knee-pocket top seam, carrier bottoms, cord tails, left strap and ladder-lock |
| V3 `rigR_close` | (−820, −560, 880) | `RigR.anchor` ≈ (−243, −74, 760) | 85 mm | `ref/zoom_belt14_rrig_grid_x6.png`, `ref/zoom_belt_rcarriers_x8.png`, `ref/zoom_belt_rstraps_x8.png` | plates, bodies, slots, screws, stencils, mags, shock cord, cord tails, strap bite, ladder-locks |
| V4 `rigL_close` | (+800, −450, 900) | `RigL.anchor` ≈ (+173, −50, 805) | 85 mm | `ref/zoom_belt14_lrig_grid_x6.png`, `ref/zoom_belt_lblock_x10.png`, `ref/zoom_belt_lblock_top_x12.png` | frag pouch flap, snap, PALS face, piping; hard case parting line, latch, elastic cradle; hanger; left strap |
| V5 `belt_front` | (−120, −900, 1000) | `Belt.anchor.CF` ≈ (−52, −123, 976) | 70 mm | `ref/zoom_belt14_belt_grid_x6.png`, `ref/zoom_belt_waistband_x8.png` (rifle hidden in this render) | buckle, D-ring, keeper, stitching rows, belt loops passing behind, 2 mm stand-off, waistband above |
| V6 `pouchR_close` | (−850, −450, 1050) | `PouchR.anchor` ≈ (−197, −41, 988) | 85 mm | `ref/zoom_belt14_upperpouch_grid_x8.png`, `ref/zoom_belt_upperpouch_x10.png` | two cells, tension screws, mag bases, clips to the cummerbund, relation to the belt behind |
| V7 `hardware_macro` | (−330, −500, 850) | `RigR.LadderLock.Upper` ≈ (−182, −115, 778) | 100 mm | `ref/zoom_belt_rstraps_x8.png` (frame at (728–740, 517–538)) | frame bars, strap threading, fold and bar tack, edge wear, webbing weave, selvedge |
| V8 `rear_check` | (0, +2200, 900) | (0, 0, 850) | 50 mm | — (no reference) | hangers and straps round the back of the thighs, belt tail, optional holster; no floating strap |

Lighting for all views: the consolidated KEY/COOL/WORLD rig of `analysis_lighting_camera_scene.md` §6.2 (Area 1.5 m at (−1.70, −2.00, 3.60) 800 W 4500 K; Area 3.0 m at (3.20, 0.60, 3.60) 600 W cool; world 0.05), AgX "Medium High Contrast", exposure 0; V3–V8 also render a "flat" variant (Workbench, matcap + cavity, or Cycles with world grey 0.18 and no key) for geometry inspection. Evaluation renders at 800 × 800, 48 spp adaptive, OIDN (≈ 30 s each, research C); V1/V2 at 1672 × 941, 64 spp (≈ 2–4 min).

### 1.4 Pass criteria (scored by the critic, each 0–2; part passes at ≥ 24/30 with no zero)
1. Arrangement (V1): belt, right twin carriers, left two-cell block and right flank pouch are all present on the correct sides, nothing else (no visible holster, no exposed grenade, no PALS on the belt).
2. Heights (V1/V2, §8.2 readback): strap centres Z 778 ± 8 (right upper), 676 ± 8 (right lower), 689 ± 8 (left); right platform top 875 ± 10; left platform top 920 ± 10; belt top 998 ± 10 posed.
3. Lateral extents (V1): right rig silhouette spans X −300 ± 25 to −185 ± 15 at Z 760; left block spans X +160 ± 20 to +250 ± 25 at Z 805; right flank pouch X −280 ± 20 to −195 ± 15 at Z 990.
4. Colour patches (§8.4): 12 named samples within ±10/255 per channel of the reference after grading (plates, bodies, straps, belt, Cordura, case, frames).
5. Hardware census (§8.5): 1 cobra buckle, 1 D-ring, 1 elastic keeper, 3 ladder-locks, 3 tri-glides, 2 shock-cord loops + 2 cord ends, 10 plate screws + 2 tension screws (right) and 4 + 2 (flank pouch), 1 snap, 1 latch, 2 elastic cradle bands, 2 hanger belt loops; every strap end folded 15 mm and bar-tacked; no strap floating more than 0.5 mm off the surface it crosses (flat variants).
6. Belt construction (V5): two layers, five stitch rows at 7.9 mm spacing with 3.5 mm pitch, rounded selvedge, cobra buckle 58 × 38 × 10 with both release tabs, 2.0 ± 0.5 mm stand-off from the trousers, belt loops visible passing behind.
7. Carrier construction (V3): plate 47 wide on a 76 body, 3 slots + 1 vertical cord slot, 4 corner screws + 1 tension screw, black magazine base 50 ± 5 mm proud with the shock-cord loop over it, cord tails 60 ± 10 long with cord ends.
8. Left block construction (V4): flap with snap, piping, PALS face on the pouch; parting-line rib, latch and two elastic bands on the case; case and pouch tops within 5 mm of each other.
9. Weathering: dust only where n·Z > 0.3 (plate tops, pouch flap, belt top edge), chips on convex edges only (pointiness mask), grime at carrier and pouch bottoms, no uniform dirt wash; stencils 40–70 % worn.
10. Webbing reads as herringbone webbing, not wood grain (research F §1 fault c): rib period 2.5 mm across the strap, no streaks longer than 8 mm.
11. Compression: the trousers under each strap are 3 mm off the body with a roll either side (spec 09 §4.9) and the strap's inner face touches the cloth; the belt's lower edge shows a 4 mm roll below it.
12. No intersection with the body, trousers, carrier, rifle or gloves in any view; rig test (§7.4): with the right knee flexed to 90° and the hip to 60° nothing penetrates the thigh by more than 2 mm.
13. Game export: the whole part ≤ 25 k triangles at LOD1 with the stitches dropped, every item a separate node so the loadout screen can toggle it (§10.3).
14. Critic's free judgement: "would a kit nerd name every item?" (0–2).
15. Critic's free judgement: "does the right rig look like it could be drawn from and the belt like it could hold it all?" (0–2).
Criteria 1, 2, 5 and 12 may not score 0.

---

## 2. Reference observations

### 2.1 Overall extents (measured on `reference_full.png`; left-side figures corrected ×0.96 where marked)

| Feature | Pixels (x, y) | Drawn world (mm) | Note |
|---|---|---|---|
| Belt, visible | y 490–512; x 700–760 and 850–880 | h 859–812 (45 tall) | centre hidden behind the rifle magazine (x 765–800) and the left glove; `zoom_belt14_belt_grid_x6.png` |
| Trouser waistband above the belt | y 475–490 | h 890–859 | lighter band #443d37 (750,482), #3c3b3c (860,482) |
| Buckle | hidden, x 765–800 | X −138 to −64 | analysts: flat cobra, offset to his right |
| Bright glint on the belt | (750,500) | X −170, h 837 | 3 × 2 px; own 5 × 5 mean #221f1e (the glint is a 1-px highlight, lum spike 153 at (705,502) is a second one) |
| Right hanger from the belt | x 700–716, y 470–500 | X −276 to −242 | **tan**, not black: #736054 at (695,505), lum 98–132 in col 705 y 476–492; a lighter X-shaped mark at (705–712, 480–490) = box-X stitch (own reading, `zoom_belt_rhanger_x12.png`) |
| Right twin carriers, total | x 662–735, y 485–603 | X −356 to −201; h 869–619 (250 tall, 155 wide) | edge finder y 515: 662/665 (outer plate edge), 689/690 (outer body edge), 696–703 (inner plate edge), 730/732 (inner body edge) |
| Outer carrier (further from the body) | x 662–700; tan plate 665–690; top y 485, bottom 602 | plate 53 wide of a 80 body | a dark cap above the plate y 485–500 (col 680: lum 146 spike at 485 then 7–18 until 506): read as the black magazine top or body rim above the plate |
| Inner carrier | x 700–735; tan plate 703–725; top y 500, bottom 603 | plate 47 wide of a 74 body | vertical slot 50 × 6 px-scale near the top (shock-cord exit), a round rivet/screw at (712,515) |
| Slots on the plates | 3 per plate, horizontal, ≈ 12 × 3 px | 25 × 6 | at y ≈ 520, 548, 575 on the inner plate (col 718 dips) |
| Upper right thigh strap | y 517–538, x 735–800 | h 801–757 (centre 779), 44 tall incl. shadow | flat black; ladder-lock frame x 728–740, y 517–538 #35322d |
| Lower right thigh strap | y 558–582 (shadow to 588), x 735–800 | h 714–663 (centre 689 incl. shadow; strap body ≈ 676) | frame x 728–740, y 557–580 #191818 |
| Cord tails below the outer carrier | x 668–682, y 600–625 | 6–8 px wide = 13–17 mm; 25 px = 53 long | two thin dark cords ending in tan tips (#1b1a18 body, tips lum 25 but warm) — **not** 38 mm webbing tails |
| Right flank pouch (above the belt) | x 682–722, y 395–470 | X −314 to −229; h 1060–900 (85 × 160) | two cells: lit plates x 685–697 and 699–708 at y 410–440 (Urow 410/440), black body and shadow to 722; studs at (700,420) and (712,420) |
| Left block, total | x 905–960, y 462–560 | X +159 to +276 (corr. +152 to +264); h 918–710 (corr. 903–704); 115 × 208 | `zoom_belt14_lrig_grid_x6.png` |
| Left inner cell (olive pouch) | x 905–935 | 64 wide (corr. 61) | flap y 462–480 with a square-looking metal fastener at (930,478) #474946; face below #495056 cool-lit / #342b1f warm |
| Left outer cell (grey case) | x 935–960 | 53 wide (corr. 51) | parting-line rib x 935–940 (#222421 at (940,520)); light edge 955–960; horizontal dark band across at y 505–515 (elastic); latch region (958,520) |
| Left thigh strap | y 560–580, x 830–900 | h 710–668 (centre 689), X 0 to +148 | #312d2a lit, #111314 shadow; small frame at x 838–852, y 560–580 → X +21 |
| Left hanger | x 905–915, y 480–500 | X +159 to +180 | dark, behind the pouch block |
| Dark item behind the block | (900–915, 540–560) | — | the platform's lower corner and the strap's tri-glide (decision §2.4) |

### 2.2 Colour samples (own 5 × 5 means, lit = as rendered in the reference)

| Area | px | Hex | Lum | Reading |
|---|---|---|---|---|
| Belt, lit top | (710,500) | #4e4239 | 66 | dusty black webbing catching the key |
| Belt, median | (735,505) | #322e2a | 46 | — (analysts' median #22211f stands for the shaded run) |
| Belt, his left side | (862,500) / (876,502) | #5b5859 / #0a0b0a | 89 / 10 | cool-lit top edge / shadow |
| Right hanger | (695,505) | #736054 | 98 | coyote-tan webbing in key light |
| Inner plate, shadowed | (720,540) / (722,520) | #2b2824 / #363231 | 39 / 50 | tan plate in the thigh's shadow |
| Plate highlights (analysts) | — | #816f5f, #786756, #6f6251 | — | the identity tan: FDE polymer under 4500 K |
| Outer body, lit | (666,560) | #5a4f4a | 80 | black polymer with dust, grazing key |
| Body, shadow / gap | (730,545) / (700,560) | #46403a / #100f0d | 63 / 14 | — |
| Carrier bottom | (680,596) | #141312 | 18 | grime |
| Upper strap | (760,528) / (790,530) | #131313 / #000000 | 19 / 0 | black webbing; highlight #393632 (analysts) |
| Ladder-lock, upper / lower | (733,527) / (733,567) | #35322d / #191818 | 49 / 24 | gunmetal; bright worn edge pixels to #4c4943 |
| Cord tails | (675,590) / (678,603) | #181511 / #1b1a18 | 20 / 25 | black cord; tips slightly warm (brass-finish ends) |
| Flank pouch plates | (688,430) | #6d5c4a | 91 | tan |
| Flank pouch studs | (700,420) | #534940 | 73 | silver stud, dulled |
| Flank pouch body / elastic | (702,450) / (700,455) | #393129 / #2d2620 | 49 / 38 | black polymer; the "elastic strip" is the shadowed gap between cells |
| Frag pouch face | (920,500) / (915,530) | #495056 / #342b1f | 79 / 41 | olive Cordura lit cool from his left; warm where the key reaches |
| Frag pouch top / fastener | (925,470) / (930,478) | #545653 / #474946 | 84 / 71 | flap top, nickel snap |
| Hard case | (948,505) / (955,490) / (948,555) | #363a3b / #383d3d / #47484a | 57 / 59 / 72 | grey polymer, cool-lit; brighter near the bottom = the lit lower edge |
| Case rib / latch | (940,520) / (958,520) | #222421 / #34393b | 34 / 55 | parting line in shadow; latch |
| Left strap / frame | (865,570) / (840,570) | #312d2a / #2b2621 | 45 / 37 | — |
| Trousers next to the straps | (770,545) / (870,590) | #0d0e0c / #4c423b | 12 / 67 | for the compression-roll contrast check |

### 2.3 What the picture shows that is physically wrong or self-contradictory
* **The belt sits below the hip joints.** Drawn belt h 812–859 against drawn hip joints at 827 and real hip joints at Z 945 posed (spec 08 D1). A belt 100 mm below the trochanters holds nothing up. Consequence of the thigh-length fix: the belt and waistband must rise to the real pelvis (§2.5 D1).
* **The right carriers are drawn beside the thigh yet seen face-on.** Their faces span X −356 to −201 while the clothed thigh at that height spans X −284 to −106; face-on plates cannot be 70 mm outside the leg that carries them. Under the pose of spec 08 (right thigh facing 45° to his right) a platform on the thigh's anterior-lateral quadrant is seen at 55° — the plates foreshorten to ≈ 125–140 mm total width, close to the drawn 155 mm (§2.5 D3).
* **The carriers are too tall to be real.** 250 mm of tan plate for a 190 mm magazine, with no magazine visible. No open-top carrier hides the whole magazine (it could not be drawn). The drawn dark cap above the outer plate is consistent with a black magazine protruding (§2.5 D4).
* **The flank pouch hangs in mid-air** between the vest hem (h 1050) and the belt (859) with 190 mm of shirt between; with the real belt line the gap is ≈ 50 mm and the pouch overlaps the belt (§2.5 D6).
* **The left block cells are 208 mm tall but only 61 and 51 mm wide** — a frag pouch for one M67 is ≈ 115 tall and ≥ 70 wide; a 51 × 208 hard box is nothing on the market. Real items of these proportions exist (vertical double frag pouch; a micro hard case stood on end seen from its narrow side) and are used (§2.5 D7, D8).
* **Hanger colour**: the analysts read it black; the pixels are tan with a box-X stitch (§2.1). Keep tan — it is what the picture shows and coyote hanger straps are sold.
* **The "silver snaps" on the flank pouch** on a polymer carrier are tension screws, not snaps; polymer carriers have no flaps (§2.5 D9).

### 2.4 Ambiguities and decisions (image-level)
* **Belt buckle type and position.** Hidden. Decision: AustriAlpin COBRA FC45 (the research's measured datasheet item) centred 30 mm to his right of the trouser centre front, as the analysts guessed "slightly to his right"; the rifle magazine hides it in V1 either way.
* **The glint at (750,500).** A metal keeper or a D-ring edge. Decision: the HSGI-class rigger belt's stainless **D-ring**, 100 mm to his right of the buckle, lying flat; seen edge-on it is a 4.5 mm bright bar — the size of the glint.
* **Right carrier identity.** Twin open-top rifle-mag carriers (analysts' best read; the loadout card shows a carbine and the figure carries one magazine in the rifle, so two spares on the leg is the obvious kit). Alternatives (tourniquet/flashlight tubes, 40 mm tubes) rejected: nothing else is drawn to carry rifle magazines.
* **Cord tails.** Thin (13–17 mm projected), ending in tan tips: the carriers' shock-cord excess with metal cord ends, not webbing (webbing would be 38 mm). Hung from the outer carrier's lower cord slots.
* **Left inner cell.** Frag pouch, as adopted in dispute 12. Vertical double-M67 footprint (§3.6) because of its height; the single flap and one snap as drawn.
* **Left outer cell.** Hard polymer case with hinged lid, parting line and latch; adopted as a micro hard case (§3.7) stood on end in an elastic cradle; the horizontal dark band across it at y 505–515 is the upper cradle band.
* **"Dark item behind" at (900–915, 540–560).** The left platform's lower inboard corner and the strap tri-glide; no extra item.
* **Ladder-lock of the left strap at X +21** (medial-front of the left thigh) rather than at the platform edge as on the right: the left strap's adjuster sits on the running end at the front. Kept as drawn; both arrangements are sold.
* **Stencil marks** on the plates: 2–3 small light marks per plate. Decision: a "5.56" calibre stencil and a 6-character lot code in 5 mm grey stencil letters, 40–70 % worn, plus a moulded 12 × 6 mm maker's mark; the image shows marks, not legible text, and legible real-looking marks are what the critic will accept.

### 2.5 Reality-wins decisions (the record required by the client's rule; "image" = as drawn, "reality" = product or anatomy)

| # | Item | Image | Reality | Decision | Consequence |
|---|---|---|---|---|---|
| D1 | Belt height | h 812–859, below the hip joints (827 drawn, 945 real) | a rigger belt on mid-rise combat trousers rides between the trochanters (Z 955 posed) and the iliac crest (1031 rest / 1013 posed, spec 03) | **Belt top Z 998 posed (1016 rest), bottom 953.5; waistband top 1013 posed (1031 rest)**; overrules consolidated §6 "y 490–512" and spec 09's waistband at 890 | the belt row moves ≈ 65 px up in the V1 overlay; the exposed shirt band between vest hem (1050) and belt shrinks from 190 to ≈ 50 mm; spec 09 must move its waistband and `Trousers.Belt` group (§10.1) |
| D2 | Rig heights | right platform h 875–625, straps 801–757 / 714–663, left block 918–710, strap 710–668 | a drop-leg platform rides mid-thigh with 75–250 mm of hanger below the belt; the drawn heights are on the thigh in both anatomies | **keep the drawn heights** (right platform top 875, straps centred 778 / 676, left platform top 920, strap 689) | hangers become 77 mm (right) and 33 mm (left) long instead of 50 and 20: more realistic; spec 09's strap footprints are unchanged |
| D3 | Right rig placement | beside the thigh, face-on | on the thigh's surface; a 150 mm platform wraps 86° of a Ø 200 thigh | **platform centred at thigh azimuth +10° lateral of the thigh's front (world 55° to his right)**; carriers 42 mm proud | projected width 125–140 mm vs drawn 155; rig spans X ≈ −300 to −185 vs drawn −356 to −201 |
| D4 | Carrier height and magazines | 250 mm plates, no magazine | open-top carriers are 120–150 mm tall and show 40–60 mm of magazine | **body 140 tall, PMAG 30 (190) inserted → 53 mm black magazine top proud, shock cord over it** | silhouette 193 mm per carrier + platform margin; black mag tops are new in the picture |
| D5 | Carrier width | plates 47–53 of 74–80 bodies | a STANAG carrier broad-side is 76 ± 4 wide | **76 wide, 42 deep, plate 47 wide** | matches the drawn widths |
| D6 | Flank pouch mounting and size | 85 × 160, floating above the belt | double pistol-mag polymer carrier 100 × 105 × 38 holding two 125 mm P226 magazines, hung from the cummerbund's lowest PALS rows | **as reality, top Z 1040, bottom 935, mag tops 1063 under the hem; passes in front of the belt** | the pouch overlaps the belt on the flank; mag bases visible |
| D7 | Frag pouch | 61 × 208 olive flap pouch | single-M67 pouch 115 × 70 × 65; vertical double 195 × 72 × 70 | **vertical double-frag footprint 72 × 70 × 195 + flap, one flap, one snap, empty** (no grenade shown, consolidated §6) | 11 mm wider than drawn |
| D8 | Hard case | 51 × 208 grey box, rib, latch | micro hard case 191 × 98 × 62 (Pelican 1030 class [VERIFY]) stood on end, narrow side to the camera | **as reality, in two 25 mm elastic bands** | 11 mm wider, 17 mm shorter than drawn |
| D9 | Flank pouch "snaps" and "elastic" | silver snaps on lids, elastic strip | polymer carriers have tension screws and no lids | **tension screws Ø 8; the "strip" is the gap between cells** | — |
| D10 | Thigh strap width | 33–44 tall incl. shadow | 1.5 in (38 mm) webbing is the drop-leg standard | **38 mm** | — |
| D11 | Hanger colour | analysts: black; pixels: tan with box-X | both sold | **coyote tan 38 mm with box-X stitch (right); black (left, in shadow, unreadable)** | — |
| D12 | Pistol and holster | none visible; loadout card lists a P9 | a pistol-mag carrier without a pistol is odd but worn (hidden holsters exist) | **no holster by default; optional small-of-back holster object, off** | open question §10.2 |

---

## 3. Real-world reference

Each number is marked **M** (measured on the image), **S** (sourced: research D or a datasheet named there) or **E** (estimated from a product class; tagged [VERIFY] where a datasheet should be fetched before the build).

### 3.1 Rigger belt — HSGI Cobra 1.75 in rigger belt class with AustriAlpin COBRA FC45

| Component | Dimension (mm) | Mark | Construction / material |
|---|---|---|---|
| Webbing width | 44.5 (1.75 in) | S | Type 13 nylon webbing, 7000 lb class |
| Layers / thickness | 2 × 2.5–3.0 → 5.5 total | S | two plies sewn face to face; selvedge radius 1.5 |
| Stitch rows | 5 rows, spacing 7.9 (at 6.5, 14.4, 22.25, 30.1, 38.0 from the top edge) | S (5 rows) / E (positions) | #138 bonded nylon, pitch 3.5 (7 spi), thread Ø 0.5 |
| Inner circumference | 960 (size L 36–38 in = 914–965) | S (size) / E (fit) | over the trouser waistband: body ≈ 905 at the belt line + shirt + waistband |
| Cobra FC45 buckle | 58 across × 38 along × 10 thick; 45 mm webbing slot; 41 g | S (AustriAlpin datasheet) | aluminium, black anodised; male with two spring tabs, female frame with adjuster bar; tab windows 14 × 6 |
| D-ring | 50 × 32 outside, 4.5 wire | E | stainless, flat on the belt 100 to his right of the buckle, held in a 25 mm webbing tab sewn between the plies |
| Elastic keeper | 45 × 20 × 1.5 | E | black knitted elastic loop over the belt tail beside the buckle |
| Belt tail | 120 beyond the female frame | E | passes under the keeper, lies on the belt |
| Interior | hook-and-loop field 38 wide along the inside | S | mates with the trouser waistband's loop (hidden; modelled as a 2 mm bump on the inside only) |
| Mass | 0.30 kg incl. buckle | E | — |

### 3.2 Webbing and strap hardware (shared with specs 12 and 13 through `gear_hardware.py`)

| Item | Dimension (mm) | Mark | Notes |
|---|---|---|---|
| 38 mm webbing (thigh straps, hangers) | 38 wide × 1.3 thick; herringbone rib period 2.5 across, 1.6 along | E (research D: no datasheet) | MIL-W-17337 class; black (straps), coyote (right hanger) |
| 25 mm webbing (PALS on the platforms and pouch face, D-ring tab, binding) | 25 × 1.3 | S (width) / E (thickness) | black |
| Ladder-lock, 38 mm | 50 wide × 32 long × 6 thick; bars 4 × 3.5; two slots 40 × 5 | E [VERIFY: ITW/AustriAlpin metal ladder-lock datasheet] | zinc die-cast, black oxide "gunmetal", edges worn bright |
| Tri-glide, 38 mm | 50 × 31 × 4; bars 4 | E | acetal black (hangers) |
| Cord lock / cord end | Ø 8 × 18 cylinder, 2 mm wall, Ø 4.5 bore | E | aluminium, brass-anodised (the "tan tips") |
| Shock cord | Ø 4, black | E | polyester sheath over rubber core; 1 mm knit texture |
| Hanger belt loop | 38 webbing folded into a 60 × 40 sleeve over the belt, hook-and-loop closed | E | one per rig; tri-glide 50 mm below the belt |
| Bar tack | 10 × 2.5 (38 mm straps: 12 × 3); 28–42 stitches | S (spec 09 convention) | black Tex 70 |
| Box-X stitch (hanger ends) | 30 × 30 square with both diagonals | E | 3.5 mm pitch |

### 3.3 Right drop-leg platform — HSGI Leg Rig V2 / Blackhawk Omega Elite class [VERIFY both]

| Component | Dimension (mm) | Mark | Construction |
|---|---|---|---|
| Panel | 150 wide × 230 tall × 8 thick; corner radius 15 | E (M for the drawn 155 × 250 envelope) | laminate: 500D Cordura 1.0 / HDPE sheet 2.0 / Cordura 1.0 / closed-cell foam 4.0 on the leg side; edges bound with 25 mm tape folded to 12 |
| PALS on the face | 3 rows of 25 mm webbing, row pitch 38, first row 40 below the top edge; bar-tack columns every 38 (4 columns at 18, 56, 94, 132 from the inboard edge) | S (PALS) | sag 3 mm between tacks |
| Strap slots | 4 of 40 × 8, 12 from each side edge, centred on the strap heights (97 and 199 below the top edge) | E | bound with 12 mm tape |
| Hanger slots | 2 of 40 × 8 at the top edge, 55 and 95 from the inboard edge | E | hanger exits the top |
| Curvature | bent round the clothed thigh, radius 100 at Z 760 (86° of arc for the 150 chord) | E (spec 03 thigh girth 603 at the fold, ≈ 560 at Z 760 → r 89 + cloth 8 + 3 stand-off) | — |
| Thigh straps | 2 × 38 mm, length round the clothed thigh 600 at Z 778 (girth 560 + cloth) and 580 at 676, plus 90 of running end | E | each: fixed end sewn into the outboard slot with a box-X; running end through the inboard slot, through the ladder-lock sewn on the inboard tab, folded back 15 and bar-tacked |
| Hanger | coyote 38 webbing from the belt loop (Z 953) to the panel top (875), 77 visible + 60 inside the panel sleeve; tri-glide at Z 920 | E | box-X at the panel |
| Mass | 0.35 kg | E | — |

### 3.4 Open-top polymer rifle-magazine carriers — HSGI Polymer TACO / Blade-Tech Signature AR class, two-tone [VERIFY]

| Component | Dimension (mm) | Mark | Construction |
|---|---|---|---|
| Body (black) | 76 wide × 42 deep × 140 tall; wall 3; corner radius 6 outside, 3 inside; floor 3 with a Ø 8 drain hole | E (M: 74–80 wide) | moulded polymer, matte, fine grain |
| Face plate (tan FDE) | 47 wide × 128 tall × 3 thick; corner radius 5; stands 1.5 proud of the body on a 1.5 spacer rim | M (47–53 wide) / E | polymer; screwed to the body |
| Plate screws | 4 × Ø 5 countersunk pan heads, 6 from each plate edge | E | stainless, dulled; Torx T10 recess 2.5 across |
| Tension screw | 1 × Ø 8 domed head, 25 below the plate top on the centreline, with a Ø 10 × 2 rubber washer | M (712,515) / E | stainless, bright |
| Slots | 3 horizontal through both plate and body: 25 × 6, ends radius 3, at 45, 73, 101 below the plate top; 1 vertical cord slot 18 × 6 centred 12 below the plate top | M (3 per plate) / E | 1 mm edge radius |
| Cord lacing slots | 2 × 6 × 4 at the body's bottom rim (inner and outer side), 2 at the top rim | E | shock cord threads bottom → up the sides → loop over the mag top |
| Shock cord | Ø 4, loop 50 above the body top over the magazine spine; tails 60 ± 10 from the outer carrier's bottom slots with cord ends | M (tails 53) / E | — |
| Magazine (instance of spec 15's `Carbine.Magazine.PMAG30`) | 190 × 66 × 25; inserted base-down so 53 protrude | S (190 × 66; research D's 22 thick is [VERIFY] — 25 used) | black polymer, floor plate ribs, witness-hole slits |
| Mounting clips | 2 MOLLE-Lok-class polymer clips per carrier, 25 × 70 × 5, through the panel's PALS rows 1 and 2 | E | hidden behind the carrier |
| Pitch between carriers | 78 (2 mm gap) | M | — |
| Stencils | "5.56" 5 mm high stencil font, 60 % worn, 10 below the tension screw; lot code "L3-0412" 4 mm, 20 above the plate bottom; moulded maker mark 12 × 6 raised 0.3 at the plate's bottom-right | E | grey #9a948a on tan |
| Mass | 0.10 kg each empty; magazine 0.50 kg loaded | S (PMAG 146 g empty / 503 g loaded) | — |

### 3.5 Left drop-leg platform
As §3.3 but **150 wide × 260 tall** (top Z 920, bottom 660), one strap slot pair at 231 below the top edge (strap centre Z 689), 2 hanger slots; hanger black 38 webbing, 33 visible (Z 953 → 920). The strap's ladder-lock sits on the running end at the medial front (X +28, Z 689); the fixed end is sewn into the outboard slot. Mass 0.35 kg. [VERIFY: a 260 mm panel is at the long end of the product class; Tactical Tailor's leg rig is 9 in = 229 — accept the extra 30 mm or move the strap up 30 mm, open question §10.2.]

### 3.6 Frag-grenade pouch — vertical double-M67 footprint (Condor MA14 / Tactical Tailor vertical frag class)

| Component | Dimension (mm) | Mark | Construction |
|---|---|---|---|
| Body | 72 wide × 70 deep × 195 tall; corner radius 10 | S (Condor double frag 152 × 57 × 51 is too small for two Ø 64 M67; sized to two 64 × 90 grenades + 3 mm walls) / E | 500D Cordura olive-brown (#463e34 class), 2 mm piping on all vertical edges and the bottom, drain grommet Ø 8 at the bottom |
| Flap | 72 wide × 65 long over the top and 45 down the face, 15 side gussets; L-profile with a 4 mm dome | E | Cordura, 3.5 mm thick (two plies + stiffener), 12 mm binding tape on the rim |
| Snap | line-24 "Pull-the-Dot" cap Ø 15.5, nickel, on the flap 15 above its lower edge; socket on the face | M (930,478) / E | round; the drawn square glint is 3 px |
| Face | 2 PALS rows of 25 mm webbing at 38 pitch (first row 95 below the top), 2 bar-tack columns at 17 and 55 from the inboard edge → vertical "ribs" | M (ribbed face) / E | black webbing |
| Contents | none visible (consolidated §6); the body is stuffed round two hidden cylinders Ø 64 × 90 so its bulge is right | — | the cylinders are collision proxies only |
| Mounting | 2 MALICE-class clips 25 × 100 through platform rows 1–3 | E | hidden |
| Mass | 0.15 kg + 0.80 kg contents assumed | E | — |

### 3.7 Hard utility case — Pelican 1030 Micro Case class [VERIFY: 7.50 × 3.87 × 2.43 in exterior from memory of the catalogue]

| Component | Dimension (mm) | Mark | Construction |
|---|---|---|---|
| Exterior | 191 long × 98 wide × 62 deep; base 42 of the depth, lid 20; corner radius 8; wall 3 | E [VERIFY] | polycarbonate, grey (#363a3b lit), fine matte texture |
| Parting line | 6 wide × 1.5 proud lip round the lid, running vertically down the camera-facing 62 mm side | M (940,520) | — |
| Latch | 30 × 16 × 8 polymer snap latch with a Ø 4 stainless pin, centred on the front long edge (mid-height, Z 815) | M (958,520) / E | — |
| Hinge | 2 knuckles 25 × 8 × 8 with a Ø 3 pin on the rear long edge | E | hidden from the camera |
| Lanyard eye | 6 × 4 slot through a 10 × 8 lug at the bottom end | E | — |
| Orientation | long axis vertical; lid facing his left (+X, outboard); 62 mm side toward the camera; latch toward −Y | M (rib and latch visible from the camera) | — |
| Cradle | 2 black 25 mm knitted elastic bands 2.2 thick round the case at 65 and 150 below its top, bar-tacked to the platform face; a 72 × 100 Cordura back pad under the case | M (band at y 505–515) / E | — |
| Mass | 0.25 kg + 0.30 contents | E | — |

### 3.8 Pistol-magazine carrier on the right flank — Blade-Tech Double Mag / HSGI Double Pistol TACO polymer class [VERIFY]

| Component | Dimension (mm) | Mark | Construction |
|---|---|---|---|
| Body | 100 wide × 38 deep × 105 tall, two cells 46 wide with a 8 mm centre web; wall 3; floor 3 | M (85 drawn, foreshortened) / E | black polymer |
| Face plates | 2 × 40 wide × 95 tall × 3, 1.5 proud | M (lit plates 12–18 projected) / E | tan FDE polymer; 2 corner screws each (Ø 5) + 1 tension screw Ø 8 at 20 below the top |
| Slots | 1 horizontal 20 × 5 per plate at 55 below the top | E | — |
| Magazines | 2 × P226 15-round 9 mm, 125 × 36 × 16, base plates proud 23 | E [VERIFY] | black steel body, polymer base plate |
| Mounting | 2 MALICE-class clips 25 × 76 × 5 engaging the cummerbund's lowest two PALS rows (spec 13; nominal Z 1070 and 1108) | E | the clips pass behind the vest hem |
| Mass | 0.12 kg + 2 × 0.23 | E | — |

### 3.9 Optional holster (off by default) — Safariland 6378 ALS-class belt holster for a P226, 190 × 90 × 60 [E], on the belt at his right-rear (azimuth 135° from CF), hangs 2 mm off the trousers, hidden in V1. Built only with `--with-holster` (§4.12, §10.2).

### 3.10 Wear (what reality and the picture agree on)
Dust on every upward-facing surface, heaviest on the tan plates (highlights to #d2c5b5 per consolidated §6 weathering), medium on the frag pouch flap and belt top edge, light on black polymer. Paint chips 2–6 mm on the plate edges and slot edges, exposing lighter polymer (#8a7a68 under tan, #5a5553 under black). Grime at the carrier bottoms, pouch bottom, case bottom end, strap tails. Webbing fuzzed at the fold edges (roughness 0.9 band 2 mm wide). Ladder-lock bars and the cobra's tabs worn bright where the strap runs. Stencils 40–70 % abraded. No tears, no mud.

---

## 4. Geometry construction plan

Everything below is executed by `scripts/parts/14_belt_leg_rigs.py` in headless Blender 4.5 with bmesh/bpy, modifiers and geometry nodes. The script first deletes every object, material and image whose name starts with `Belt.`, `RigR.`, `RigL.` or `PouchR.` (rule 4), reads the body, trouser and rig state (`Body.Mesh.Posed`, `Trousers.Main`, `Morgan.Rig`, and `Carrier.Cummerbund` if present), computes anchors (§4.1), builds in the order of §9, parents and weights (§7), writes `cache/14_belt_leg_rigs.blend`, renders §1.3, writes `renders/14_belt_leg_rigs/readback.json` (§8). Shared recipes come from research F §8 (webbing strip, PALS generator, pouch body, buckle booleans) and are not re-described where identical. Polymer parts use Bevel + Subdivision with crease control, booleans are `EXACT` on single manifold boxes, then Bevel 1.0 / 3 segments and Weighted Normal (research F §2). All stitches live in `BeltRigs.Stitches` as 6-sided thread cylinders r 0.35 sunk 0.15 into the cloth so they can be hidden for LOD and form checks.

### 4.1 Anchors (read back at build time, nominal values listed)
`anchor_ring(z)`: the trouser waistband's outer surface ring at height z, as a 72-point closed polyline sampled from `Trousers.Main` by ray-casting outward from the pelvis centre (−30, +10, z) (spec 08 D6 pelvis X −30); the belt follows it at +2.0 mm. `anchor_thigh(side, z, azimuth)`: the clothed thigh surface point at height z and azimuth about the thigh axis (hip centre → knee centre from `Morgan.Rig`; right hip (−118, 0, 945) → knee (−218, −17, 519); left (+58, 0, 945) → (+127, −20, 505)), azimuth 0 = the thigh's own front (the knee-facing direction: 45° to his right for the right leg, 12° to his left for the left), positive = lateral. Nominal anchors: `Belt.anchor.CF` (−52, −123, 976); `Belt.anchor.Buckle` 30 mm to his right along the ring (−80, −118, 976); `Belt.anchor.Dring` 100 further (−175, −70, 976); `RigR.anchor` = `anchor_thigh(R, 760, +10°)` ≈ (−243, −74, 760) with outward normal (−0.82, −0.57, 0); `RigL.anchor` = `anchor_thigh(L, 805, +53°)` ≈ (+173, −50, 805), normal (+0.91, −0.42, 0); `PouchR.anchor` = the cummerbund (or body + 12) surface at Z 988, azimuth 65° to his right of forward about the pelvis centre ≈ (−197, −41, 988), normal (−0.91, −0.42, 0). Every anchor is written to the readback for the evaluation cameras.

### 4.2 Belt (`Belt.*`, collection `Belt`)

| Step | Object | Method (API) | Parameters | Polys |
|---|---|---|---|---|
| B1 | `Belt.Ring` | ring polyline from `anchor_ring(975.75)` offset +2.0 along the outward normal; sweep a 44.5 × 5.5 rounded-rectangle profile (corner r 1.5, 8 verts per corner) along it with bmesh (`bmesh.ops.extrude_edge_only` per segment), 288 segments; UV u = arc length, v across | top edge Z 998, bottom 953.5 (posed); the ring is open at the buckle: a 58 mm gap centred on `Belt.anchor.Buckle` | 9 k |
| B2 | `Belt.StitchRows` | 5 running-stitch rows on the outer face only (GN: `gn_stitches.py`, 2.2 stitch / 1.3 gap = 3.5 pitch), at 6.5, 14.4, 22.25, 30.1, 38.0 from the top edge | thread r 0.25 | 5 × 270 × 2 × 6 ≈ 16 k (hidden at LOD1) |
| B3 | `Belt.Buckle.Female` | box 58 × 38 × 10 (bevel r 2 / 3 seg) minus webbing slot 46 × 6 through along the belt, minus two tab windows 14 × 6 on the long sides, minus an adjuster bar slot 46 × 4 (EXACT booleans), Bevel 0.8 / 3, Weighted Normal | centred on `Belt.anchor.Buckle`, long axis along the belt, lying flat on the belt plane; the belt's female end enters 20 mm into the frame | 2.4 k |
| B4 | `Belt.Buckle.Male` | cross-bar 46 × 8 × 6 + two spring arms 30 × 6 × 4 with 8 × 5 tabs that sit in the windows, Bevel 0.5 / 2; joined into the female at engagement offset 0 | the belt's male end sewn round the cross-bar (B6) | 1.6 k |
| B5 | `Belt.Tail` | sweep of the same 44.5 × 2.75 single-ply profile, 120 long from the female's adjuster bar, lying on the belt's outer face toward his right (+0.5 mm), ends heat-cut (flat, 0.3 radius) | passes under `Belt.Keeper` | 0.8 k |
| B6 | `Belt.Keeper` | rounded-rect loft (research F §8 elastic band) 46 × 21 inside, 1.5 thick, ribbed bump across | 12 mm to his right of the female frame | 0.4 k |
| B7 | `Belt.Dring` | torus-like D: half-ring r 16 outer + straight bar, wire Ø 4.5 (curve with bevel depth 2.25, 12 sides) | lying flat on the belt at `Belt.anchor.Dring`, straight bar sewn between the plies under a 25 × 50 webbing tab (`Belt.DringTab`, strip recipe) with 2 bar tacks | 0.9 k |
| B8 | `Belt.Loops.Gap` | none — a check: for each `Trousers.BeltLoop.00…06` confirm the loop passes in the 2.0 mm stand-off (loop 1.4 thick) with ≥ 0.3 clearance both sides; raise the belt locally by Displace with a vertex group `Belt.OverLoop` (0.6 mm bump, 20 mm falloff) where it crosses a loop | 7 bumps | — |
| B9 | `Belt.HangerLoop.R` / `.L` | 38 × 1.3 strip folded into a 60 × 40 sleeve round the belt at the hanger azimuths (55° right / 65° left of forward about the pelvis centre), hook-and-loop closed on the outside (2 mm flat pad), box-X at the fold | sleeve inner = belt + 0.3 | 2 × 1.2 k |

Origin of every belt object at `Belt.anchor.CF` projected to Z 975.75; orientation: +Y along the belt's tangent at CF.

### 4.3 Right platform (`RigR.Panel.*`)

| Step | Object | Method | Parameters | Polys |
|---|---|---|---|---|
| P1 | `RigR.Panel.Core` | bmesh grid 150 × 230 (30 × 46 quads), bent to radius 100 about the thigh axis (Simple Deform BEND 86° about the axis through `RigR.anchor` along the thigh), corner radius 15 (bmesh bevel on the 4 corner verts, 6 segments), Solidify 8.0 (offset −1: thickness toward the leg), Bevel 2.0 / 3 on the rim | centre `RigR.anchor` + 4.0 along the normal (so the leg-side foam face is 3 mm off the trousers); top edge Z 875 | 3.5 k |
| P2 | `RigR.Panel.Binding` | 12 mm wide × 1.0 thick strip along the rim on the front face and the edge (L section), strip recipe | — | 1.8 k |
| P3 | `RigR.Panel.Slots` | EXACT boolean of 4 strap slots 40 × 8 (r 4 ends) at (u ±63, z −97) and (u ±63, z −199) from the top-centre, 2 hanger slots 40 × 8 at (u −20, z −6) and (u +20, z −6) through the top edge; slot binding as 12 mm strips inside each slot | — | +1.2 k |
| P4 | `RigR.Panel.PALS` | PALS generator (research F §8): 3 rows of 25 mm webbing at z −40, −78, −116 from the top edge, sag 3, bar-tack columns at u −57, −19, +19, +57; emits `RigR.Panel.Webbing`, `RigR.Panel.Bartacks`, `RigR.Panel.Stitches` | sag ±20 % random, seed 14 | 2.4 k + 12 tacks (≈ 7 k thread) |
| P5 | `RigR.Hanger` | 38 × 1.3 strip (coyote) from `Belt.HangerLoop.R`'s bottom (Z 953) down the thigh surface + 6 mm to the top hanger slot (Z 875), through it, 60 mm down the panel's back, box-X 30 × 30 at the end; `RigR.Hanger.Triglide` (3.2 frame) at Z 920 with the strap doubled through it | strap sag 2 mm, roll 0.5° | 1.5 k + 0.6 k |

### 4.4 Rifle-magazine carriers (`RigR.Carrier.Inner`, `RigR.Carrier.Outer`; inner = nearer the body, u −39; outer u +39)

| Step | Object | Method | Parameters | Polys |
|---|---|---|---|---|
| C1 | `RigR.Carrier.<i>.Body` | box 76 × 42 × 140 (outer), Bevel 6 / 3 on vertical edges and 3 / 2 on the top rim, hollowed by boolean of a 70 × 36 × 137 box (bevel 3 / 2) from the top; floor drain hole Ø 8; 2 + 2 cord slots 6 × 4 at the rims (EXACT); Subdivision 1 (render 2) with edge creases 0.8 on the rims | body back face on the PALS webbing (panel face + 1.3 + 0.3); bottom Z 705, top 845; axis parallel to the thigh | 4 k |
| C2 | `RigR.Carrier.<i>.Plate` | box 47 × 3 × 128, Bevel 5 / 3 on the face corners, 0.6 / 2 on the face edges; EXACT boolean of 3 slots 25 × 6 (r 3) at 45/73/101 below the plate top and a vertical cord slot 18 × 6 centred 12 below the top; the same slots are cut through the body behind (shared cutter objects, `RigR.Cutter.*`, deleted after apply) | plate stands 1.5 proud on a 1.5 spacer rim (a 44 × 1.5 × 125 inset box) | 2.2 k |
| C3 | `RigR.Carrier.<i>.Screws` | 4 countersunk pan heads Ø 5 × 1.2 dome with a T10 recess (6-point star boolean 2.5 across, 0.8 deep), at 6 from each plate edge; `.TensionScrew` Ø 8 × 2.5 dome + Ø 10 × 2 rubber washer under it at 25 below the plate top | sunk 0.3 into the plate | 5 × 0.4 k |
| C4 | `RigR.Carrier.<i>.Mag` | instance (linked data) of `Carbine.Magazine.PMAG30` from spec 15's cache; if absent, a placeholder box 66 × 25 × 190 with Bevel 4 / 3 and the warning logged | inserted base-down, spine toward the thigh, floor plate on the carrier floor; 53 proud; rotated 2° inward (real mags lean) | instance |
| C5 | `RigR.Carrier.<i>.Cord` | curve: from the inner bottom cord slot up the body's inboard side (between plate and body, in the 1.5 gap), through the top rim slot, over the mag spine 50 above the body top as a 25 mm-wide loop, down the outboard side, out of the bottom outboard slot; Bevel depth 2.0 (Ø 4), 10 sides; knit bump 1 mm | for the outer carrier the two cord ends continue 60 ± 10 below the body with `RigR.CordEnd.0/1` (Ø 8 × 18 cylinders, 1 chamfer) hanging on a −Z catenary with 15° random swing; the inner carrier's ends are cut flush with a 15 mm tail | 2 × 1.5 k + 2 × 0.3 k |
| C6 | `RigR.Carrier.<i>.Clips` | 2 boxes 25 × 5 × 70 behind each carrier through PALS rows 1–2 (hidden) | — | 2 × 0.1 k |
| C7 | `RigR.Carrier.<i>.Decal` | stencil decal (§5.5): a 47 × 128 UV island on the plate receives `BeltRigs.Decal.Plate<i>.png` | — | — |

### 4.5 Right thigh straps and ladder-locks

| Step | Object | Method | Parameters | Polys |
|---|---|---|---|---|
| S1 | `RigR.Strap.Upper` | path: from the panel's outboard slot (u +63, Z 778), through the panel (8 mm), round the clothed thigh at Z 778 following `anchor_thigh(R, 778, θ)` for θ from +55° lateral round the back to −45° medial, sampled on the trousers' *compressed* surface (spec 09 pulls the cloth to body + 3 under the band, so the strap's inner face touches the cloth there with 0 stand-off), then to the inboard slot (u −63); strip recipe 38 × 1.3, segment every 1 mm; running end exits the inboard slot, passes through `RigR.LadderLock.Upper`, folds back 15 with a bar tack, free end 60 lying along the strap toward the back | top edge Z 797, bottom 759 | 2.6 k |
| S2 | `RigR.Strap.Lower` | as S1 at Z 676 (657–695) | — | 2.6 k |
| S3 | `RigR.LadderLock.Upper/Lower` | frame 50 × 32 × 6: loft two rounded rectangles (outer 50 × 32 r 4, inner 42 × 24 r 2), Solidify 6, Bevel 0.8 / 3; centre bar 4 × 3.5 × 42 with a 15° tooth face; strap threads over the bar (S1/S2 paths pass through the two slots, 40 × 5) | sewn to a 38 × 30 webbing tab at the panel's inboard edge, Z 778 / 676; frame plane tangent to the thigh | 2 × 1.2 k |
| S4 | `RigR.Strap.Tabs` | 2 fixed-end tabs: strap folded through the outboard slot and sewn with a box-X on the panel back (hidden) | — | 0.4 k |
| S5 | bar tacks | 12 × 3 on the running-end folds (2), on the lock tabs (4), on the hanger (2 + box-X) | thread r 0.35 | ≈ 3 k thread |

### 4.6 Left platform (`RigL.Panel.*`) — as §4.3 with: grid 150 × 260 (30 × 52 quads), top edge Z 920, bottom 660, bend radius 103 about the left thigh axis at `RigL.anchor` azimuth +53°; one strap slot pair at z −231 from the top (strap centre Z 689); 3 PALS rows at −40, −78, −116 and a 4th at −154; hanger black 38 strip from `Belt.HangerLoop.L` (Z 953) to the top slots (Z 920), 33 visible, tri-glide at Z 940 (partly under the belt's shadow). Left strap `RigL.Strap` at Z 689 (670–708) as S1 but the ladder-lock `RigL.LadderLock` sits on the running end at `anchor_thigh(L, 689, −30°)` ≈ (+28, −95, 689), medial front, frame plane tangent to the thigh; the fixed end at the outboard slot, the running end from the inboard slot wraps the back of the thigh (behind, azimuth +90 → 180 → −90) and threads the lock from the medial side; fold 15, bar tack, 60 free end lying toward the crotch.

### 4.7 Frag pouch (`RigL.Frag.*`, at panel u −36, top Z 912)

| Step | Object | Method | Parameters | Polys |
|---|---|---|---|---|
| F1 | `RigL.Frag.Body` | pouch body recipe: box 72 × 70 × 195 → Bevel 10 / 3 → Subsurf 2 (render 3) → Displace (Clouds 60 mm, 3 mm) for the Cordura bulge; two hidden cylinders Ø 64 × 90 (`RigL.Frag.Proxy.0/1`, non-rendering) stacked inside so a second Displace (vertex-weight proximity to the proxies, 2 mm) presses the cloth over them | back face on the PALS webbing + 0.3; bottom Z 717 | 6 k |
| F2 | `RigL.Frag.Piping` | 2 mm piping tube (curve, bevel depth 1.0) along the 4 vertical edges and the bottom rectangle | — | 1.5 k |
| F3 | `RigL.Frag.Flap` | L-profile loft 17 × 17 sections: 72 wide, 65 over the top, 45 down the face, 15 side gussets as a second loft, 4 mm centre dome, Solidify 3.5, Bevel 1.2 / 2, Subsurf 1; `RigL.Frag.FlapBinding` 12 mm tape strip along the rim | hinge is a continuation of the back panel (research F §2 fault e) | 2.5 k |
| F4 | `RigL.Frag.Snap.Cap` / `.Socket` | cap: cylinder Ø 15.5 × 2 with a 1 mm dome and a 0.4 rim groove; socket Ø 12 × 1.5 on the face under it (hidden when closed) | cap centre 15 above the flap's lower edge | 0.6 k |
| F5 | `RigL.Frag.PALS` | PALS generator on the face: 2 rows at −95 and −133 from the top, columns at u −19, +19 (bar tacks 10 × 2.5) | — | 1 k + 4 tacks |
| F6 | `RigL.Frag.Grommet` | Ø 8 brass eyelet at the bottom centre | — | 0.2 k |
| F7 | `RigL.Frag.Clips` | 2 hidden MALICE boxes 25 × 5 × 100 | — | 0.1 k |

### 4.8 Hard case and cradle (`RigL.Case.*`, at panel u +42, top Z 910)

| Step | Object | Method | Parameters | Polys |
|---|---|---|---|---|
| H1 | `RigL.Case.Base` | box 191 (vertical) × 98 (along the camera axis, Y) × 42 (along the platform normal, outboard), Bevel 8 / 4 on the long edges, 3 / 2 on the ends; parting-line lip: a 6 × 1.5 rim boolean-unioned round the open (outboard) face | the base's inboard face sits on a 72 × 100 Cordura pad on the panel; its bottom end at Z 719; the 62 × 191 side toward −Y faces the camera; the open face toward +X (outboard) receives the lid | 2.5 k |
| H2 | `RigL.Case.Lid` | box 191 × 98 × 20 (outboard of the base), same bevels, closed on the base with a 0.5 mm gap at the parting line; 2 hinge knuckles 25 × 8 × 8 with a Ø 3 pin on the +Y (rear) long edge, hidden from the camera | total depth 42 + 20 = 62 along the platform normal | 1.8 k |
| H3 | `RigL.Case.Latch` | 30 × 16 × 8 box, Bevel 1.5 / 3, a 20 × 2 finger groove, Ø 4 stainless pin through, on the −Y long edge at mid-height (Z 815) | — | 0.6 k |
| H4 | `RigL.Case.Eye` | 10 × 8 × 4 lug with a 6 × 4 slot at the bottom end | — | 0.2 k |
| H5 | `RigL.Case.Band.Upper/Lower` | 25 mm knitted elastic (band recipe: rounded-rect loft following the case section + 2.2, pinched 1.5 %, ribbed bump 1 mm) at 65 and 150 below the case top, ends bar-tacked to the panel face (2 tacks each, 12 × 3) | — | 2 × 0.8 k |
| H6 | `RigL.Case.Pad` | 72 × 100 × 3 Cordura pad under the case's back on the PALS | — | 0.3 k |

Orientation summary for the critic (because it is easy to get wrong): stand the case on its bottom end; its lid faces outboard along the platform normal (toward his left-front), hinge along the rear (+Y) long edge, latch on the front (−Y) long edge facing the camera, the parting line runs vertically down the camera-facing side 20 mm from the lid face. In V4 the camera therefore sees the 62 × 191 side with a vertical lip and a latch in the middle, and the lid's 98 mm face in steep foreshortening beyond it — as the picture shows.

### 4.9 Flank pistol-magazine carrier (`PouchR.*`)

| Step | Object | Method | Parameters | Polys |
|---|---|---|---|---|
| Q1 | `PouchR.Body` | box 100 × 38 × 105, Bevel 5 / 3 vertical edges, hollowed by 2 cells 40 × 32 × 102 (bevel 2) from the top with an 8 mm centre web; floor drain Ø 6 per cell; Subsurf 1 with creases | back face on the cummerbund surface + 0.3 (or body + 12.3 if spec 13 is absent); top Z 1040, bottom 935; axis vertical | 3 k |
| Q2 | `PouchR.Plate.0/1` | boxes 40 × 3 × 95, Bevel 4 / 3, 1.5 proud on spacer rims; 1 slot 20 × 5 at 55 below the top (EXACT) | centred on each cell | 2 × 1 k |
| Q3 | `PouchR.Screws` | 2 corner screws Ø 5 per plate (top corners) + 1 tension screw Ø 8 with washer at 20 below the top per plate | — | 6 × 0.4 k |
| Q4 | `PouchR.Mag.0/1` | box 36 × 16 × 125 with Bevel 3 / 3, a 36 × 18 × 6 base plate (bevel 1), 6 witness holes Ø 3 on the spine (boolean) | inserted base-down, 23 proud, tops Z 1063 (under the vest hem, Z 1050, with 13 mm overlap accepted — the hem hangs outboard of the mag tops by the cummerbund thickness) | 2 × 0.8 k |
| Q5 | `PouchR.Clips` | 2 boxes 25 × 5 × 76 behind the body rising to Z 1115, hidden behind the vest hem | — | 0.1 k |
| Q6 | `PouchR.Decal` | stencil decal: lot code only, 4 mm, on plate 0 | — | — |

### 4.10 Stitches, bar tacks and box-X stitches
Generated last by `gn_stitches.py` into `BeltRigs.Stitches` (one mesh per parent object, named `<Parent>.Stitches`): belt rows (B2), every strap edge (running stitch 2.2/1.3 at 1.8 inside both selvedges — real webbing has none; **skip** on webbing, keep on the belt because its two plies are sewn), PALS bar tacks, strap-fold bar tacks (12 × 3, 42 stitches), box-X stitches on the hangers and fixed ends. Thread r 0.35, 6 sides, sunk 0.15; count ≈ 1,100 segments ≈ 20 k tris total (research F: 896 segments took 3.3 s; well within budget).

### 4.11 Topology and poly budget

| Group | Evaluated tris (render) | LOD1 tris (game, stitches off, Subsurf off) |
|---|---|---|
| Belt + buckle + D-ring + keeper + loops | 32 k (16 k of it stitches) | 4.5 k |
| Right platform + hanger + PALS | 22 k | 3.5 k |
| 2 carriers + plates + screws + cords + ends | 38 k (+ 2 mag instances ≈ 6 k) | 6 k (+ mags) |
| 2 right straps + 2 ladder-locks + tabs | 14 k | 2.5 k |
| Left platform + hanger + strap + lock | 20 k | 3 k |
| Frag pouch | 24 k | 3 k |
| Hard case + cradle | 14 k | 2 k |
| Flank carrier + mags | 14 k | 2.5 k |
| **Total** | **≈ 184 k** | **≈ 27 k → trim the carriers' Subsurf to reach ≤ 25 k** |

Origins: every object's origin at its own anchor (panel centre, carrier bottom-centre, strap start, buckle centre); orientation +Z up, local −Y toward the surface normal's camera-facing projection, so that `Part.Side.Component` objects can be mirrored by negating X for the game's left-handed variant if ever needed. Joins: nothing is joined except the cutter cleanup; the carriers, plates and screws stay separate objects for material assignment and LOD.

### 4.12 Optional holster (`Belt.Holster`, `--with-holster` only)
Box-loft 190 × 90 × 60 with a muzzle taper (7 sections), Bevel 6 / 3, a 40 × 25 ALS hood lump, a belt loop 60 × 50 × 4 over the belt at azimuth 135° (his right-rear); black polymer; hangs 2 mm off the trousers; weights `root`. No pistol inside unless spec 15's `Pistol.P226` exists (then instanced, grip up and rearward).

---

## 5. Materials and textures

All materials via `mat_fabric.py` / `mat_hard.py` (spec 16 library); albedo given linear (sRGB hex target under the §1.3 lighting in brackets). Texel density 2048 px per 0.5 m (≈ 4 px/mm) on everything the V3–V7 cameras see; 1024 per 0.5 m on the panel backs and clips. UVs: belt and straps unwrapped as straight strips (u along the strap, v across; weave aligned); plates and bodies box-projected per object with seams on the back edges; pouch body cylindrical from the back; case by its 6 faces. No image repeats visibly within one object: every tiled map is offset per object by a hash of the name.

### 5.1 Material table

| Material | Base colour (linear) [hex target lit] | Roughness | Metallic | Normal / bump | Extras |
|---|---|---|---|---|---|
| `BeltRigs.Webbing.Black` (belt, straps, PALS, binding) | (0.018, 0.017, 0.016) [#22211f median, #393632 highlight] | 0.72 base, 0.9 at fold edges | 0 | `poly_wool_herringbone` normal tiled so one rib = 2.5 mm across, wave distortion 2 (research F §1 fault c fix) | Sheen 0.08, sheen tint 0.5; fuzz mask at selvedges 2 mm |
| `BeltRigs.Webbing.Coyote` (right hanger) | (0.19, 0.135, 0.085) [#736054] | 0.72 | 0 | same | — |
| `BeltRigs.Elastic` (keeper, cradle bands) | (0.012, 0.012, 0.012) | 0.85 | 0 | ribbed wave 1 mm across | no wear |
| `BeltRigs.Polymer.Black` (bodies, platform face binding core, clips, latch, flank body) | (0.022, 0.021, 0.020) [#2a2622 body, #46403a lit] | 0.45 ± 0.05 grain | 0 | `Plastic012B` normal + roughness (1 mm scratches), 12 cm tile | Coat 0.05; edge wear → (0.09, 0.085, 0.082) by pointiness mask |
| `BeltRigs.Polymer.Tan` (face plates) | (0.20, 0.155, 0.115) [#816f5f highlight, #4c4034 mid] | 0.5 | 0 | `Plastic018B` tinted, 12 cm tile | chips → (0.26, 0.21, 0.165) exposed polymer; dust layer §5.3; stencil decal §5.5 |
| `BeltRigs.Polymer.CaseGrey` | (0.085, 0.092, 0.092) [#363a3b] | 0.55 | 0 | fine stipple (Noise scale 1500/m, 0.15 mm) | parting lip roughness 0.4 |
| `BeltRigs.Cordura.Olive` (frag pouch, pads) | (0.07, 0.062, 0.047) [#463e34 under key; reads #495056 under the cool side light — do not tint blue] | 0.83 | 0 | `Fabric063` normal at a 15 mm tile (yarn 0.5 mm; research F §1 fault b) | Sheen 0.06; dust on the flap top |
| `BeltRigs.Cordura.Black` (platform faces, binding, flap binding) | (0.016, 0.016, 0.015) | 0.83 | 0 | same 15 mm | — |
| `BeltRigs.Metal.Gunmetal` (ladder-locks, cobra buckle) | (0.10, 0.10, 0.10) [#35322d; worn edges #4c4943] | 0.45 base, 0.25 on wear | 1.0 | `Metal038` + `Metal050C` edge layer by pointiness ≥ 0.6 | anisotropy 0.3 along the bar |
| `BeltRigs.Metal.Stainless` (D-ring, screws, snap cap, latch pin, tension screws) | (0.62, 0.62, 0.60) | 0.3 | 1.0 | `Metal063` | smudge mask (Noise) 0.1–0.5 roughness |
| `BeltRigs.Metal.BrassAno` (cord ends, grommet) | (0.45, 0.33, 0.17) | 0.4 | 1.0 | — | — |
| `BeltRigs.Rubber` (tension-screw washers, mag floor plates if placeholder) | (0.02, 0.02, 0.02) | 0.9 | 0 | — | — |
| `BeltRigs.ShockCord` | (0.012, 0.012, 0.012) | 0.8 | 0 | knit wave 1 mm along | — |
| `BeltRigs.Thread` (stitches) | (0.13, 0.13, 0.125) | 0.6 | 0 | — | sheen 0.1 (research F §1 fault e) |
| `BeltRigs.Velcro` (hanger-loop closures) | (0.02, 0.02, 0.02) | 0.95 | 0 | hook stipple bump 0.5 mm | — |

### 5.2 Maps and texture sets
Downloaded (manifest, research A): `Plastic012B` 2K (Color, NormalGL, Roughness), `Plastic018B` 2K, `Fabric063` 2K (NormalGL, Roughness, AO), `poly_wool_herringbone` 2K (nor_gl, rough), `Metal038` 2K (Color, NormalGL, Roughness, Metalness), `Metal050C` 2K, `Metal063` 2K, `SurfaceImperfections015` (dust). Generated by the script with `python3 -I` + PIL + numpy into `assets/generated/14/`: `decal_plate_inner.png`, `decal_plate_outer.png`, `decal_flank.png` (1024 × 2048, RGBA, §5.5); `wear_mask_<object>.png` only if the pointiness bake (`object.bake`, research C §10, 0.4 s at 512²) is chosen over live pointiness for the game export.

### 5.3 Weathering masks (procedural, shared node group `BeltRigs.Wear`)
* **Dust**: factor = smoothstep(0.3, 0.8, n·Z) × (0.6 + 0.4 Noise(scale 40/m)) × AO⁻¹ clamp; mixes toward (0.55, 0.49, 0.42) [#d2c5b5 on the plate tops], strength 0.55 on tan plates and the flap, 0.35 on the belt's top edge, 0.2 on black polymer, 0 on hardware undersides.
* **Chips**: Pointiness (Geometry node) remapped 0.55–0.75 × Voronoi(F1, scale 600/m) threshold 0.35 → sharp mask; 2–6 mm cells; exposes the "exposed polymer" colour and roughness 0.6; density highest on plate and slot edges, zero on the case (new-looking item) and 20 % on the carrier bodies.
* **Grime**: Z-gradient from each object's bottom (0 → 1 over 30 mm) × Noise(scale 80/m) → darken ×0.45 and roughness +0.1; on carrier bottoms, pouch bottom, case bottom end, cord tails, strap free ends.
* **Edge wear on metal**: pointiness ≥ 0.6 → `Metal050C` bare layer, roughness 0.25, at ladder-lock bars (and a stroke mask along the bar where the strap runs), cobra tabs, D-ring where it touches the belt.
* **Fabric fuzz**: distance to the strip's selvedge < 2 mm → roughness 0.9, sheen 0.15.

### 5.4 Hex targets after grading (checked in §8.4; AgX Medium High Contrast, the §1.3 rig)
Plate top lit #816f5f ± 10; plate mid #4c4034; body lit #46403a; body shadow #2a2622; gap #100f0d; strap #131313 (highlight crest #393632); ladder-lock face #35322d, worn edge #4c4943; belt lit top #4e4239, median #22211f, shadow #090908; hanger #736054; frag face (cool) #495056, (warm) #342b1f; case #363a3b, lit edge #47484a; cord #181511; flank plate #6d5c4a.

### 5.5 Stencil decals (`scripts/lib/decal.py`, no painting)
PIL renders white-on-transparent text in a stencil face (DejaVu Sans Bold with 1.2 px bridges cut by a mask, or the bundled `Bfont` if DejaVu is absent) at 20 px/mm: "5.56" (5 mm cap height), lot code "L3-0412" (4 mm), on the outer plate also "NSN 8465" (3 mm). The alpha is eroded by a Noise threshold (seed per plate) to leave 30–60 % of the ink, with a 0.3 mm feather. In the shader the decal image (UV island of the plate, placed by the script) mixes base colour toward (0.36, 0.34, 0.31) [#9a948a] and roughness toward 0.62. The moulded maker's mark is a 12 × 6 mm raised 0.3 mm text (Text object → mesh → Shrinkwrap → joined into the plate before Bevel), not a decal.

---

## 6. Fibres, simulation or dynamics

* **No cloth simulation in this part.** Straps are swept along surfaces read back from the finished trousers; the frag pouch's softness is a Displace over proxies; the belt follows the waistband ring. This keeps the build deterministic (rule 4) and fast (< 10 s build, research F numbers).
* **Strap bite** is owned by spec 09 (its `Trousers.StrapBand.R.Upper` 761–795, `.R.Lower` 651–700, `.L.Lower` 668–710 and `Trousers.Belt` groups shrink the cloth to body + 3 and raise 5 mm rolls either side). This part guarantees: strap inner face = the trousers' *pulled-in* surface, read back after spec 09's Shrinkwrap (so the script must run after 09 in `build_all.py`); belt inner face = waistband + 2.0. If the trousers are rebuilt without the bands (`--no-compress`), the script Shrinkwraps the strap paths to the actual cloth instead and logs "straps not biting".
* **Cord tails swing**: a static catenary with a per-cord random 15° swing seed; in the game rest pose they hang straight down. No physics.
* **Hair / fibres**: none. Webbing fuzz is roughness and sheen, not geometry (research F §8 "fabric weave by bump, never geometry").
* **Magazine rattle, strap stretch**: none; the rig (§7) handles pose changes.

---

## 7. Rigging and attachment

### 7.1 Parenting and weights (MPFB default names; Rigify `DEF-` names through spec 08's `BONE_MAP`)

| Objects | Bones and weights | Notes |
|---|---|---|
| `Belt.*` (ring, buckle, tail, keeper, D-ring, hanger loops, optional holster) | `root` 1.0 (rigid ring; spec 08 attachment table "Belt and buckle (14)") | the belt rides the pelvis; the `Hero.Compress` property drives spec 03/09's `Leg.Compress.Belt` (−3 mm) and the trousers' belt roll, not anything here |
| `RigR.Hanger`, `RigR.Hanger.Triglide` | graded along the strap: `root` 1.0 at the belt → `upperleg01.R` 1.0 at the panel top (linear over the visible 77 mm) | spec 08 "hanger strap graded" |
| `RigR.Panel.*`, `RigR.Carrier.*`, `RigR.LadderLock.*`, cords, cord ends | `upperleg02.R` 0.8 / `upperleg01.R` 0.2 (rigid, one weight for the whole rig) | spec 08 row "Right drop-leg panel, twin carriers (14)" |
| `RigR.Strap.Upper/Lower` | rigid with the panel for the 150 mm on the panel; round the thigh: `upperleg01.R`/`upperleg02.R` transferred from `Body.Mesh` by Data Transfer (`POLYINTERP_NEAREST`) so the strap follows the thigh's twist | no vertex may lose > 25 % of its ring circumference in the twist test (spec 08 criterion 8) |
| `RigL.*` | mirror of the above with `.L` bones; `RigL.LadderLock` on the strap follows the strap's weights | — |
| `PouchR.*` | the cummerbund weights of spec 08: `spine03` 0.5 / `spine02` 0.3 / `spine04` 0.2 | flexes with the flank; if spec 13 later exposes a `Carrier.Cummerbund` surface the pouch is Surface-Deformed to it instead (flag `--pouch-surface-deform`) |
| `Carbine.Magazine.PMAG30` instances in the carriers | the carriers' weights (object parent to `RigR.Carrier.<i>.Body`) | — |

### 7.2 Modes
`--mode posed` (hero): anchors from `Body.Mesh.Posed` / `Trousers.Main`; objects parented to `Morgan.Rig` with Armature modifiers carrying the weights above (`use_deform_preserve_volume` off — hard parts must not bulge). `--mode rest` (game deliverable): the same build on the A-pose body and `Trousers.Rest`; weights as above; everything exported as separate glTF nodes named as the objects (criterion 13), the stitch meshes excluded, Subsurf levels 0.

### 7.3 `Hero.Compress`
Not driven here; this part's straps sit at the compressed heights and the readback (§8.3) confirms the bite exists.

### 7.4 Rig test (run in `--mode rest` after weighting)
Pose `upperleg01.R` to 60° flexion and `lowerleg01.R` to 90°, then 45° hip abduction: report the maximum penetration of `RigR.*` into `Body.Mesh` (BVH overlap, §8.6) — target ≤ 2 mm (the panel foam compresses); the hanger must stay taut (length change ≤ 15 %); the belt must not move relative to the pelvis bone (0 mm by construction). Repeat for the left.

---

## 8. Evaluation protocol

### 8.1 Renders
§1.3 views to `renders/14_belt_leg_rigs/V1_hips_ref.png` … `V8_rear_check.png`, each lit and flat; V1/V2 also as `*_overlay.png` (50 % blend over the reference crop, upscaled ×3) and `*_sidebyside.png`. Render settings per research C recommendations (adaptive 0.02, OIDN RGB_ALBEDO_NORMAL, persistent data). A 10-second Workbench "look" set (`--look`) at 480 × 720 renders V3, V4, V6 for geometry iteration.

### 8.2 Height and extent readback (`scripts/lib/measure.py::measure_rigs()` → `readback.json`)
From the evaluated meshes: belt top/bottom Z at CF, at his right hip (azimuth 90°) and at his left hip; strap centre Z at the inboard slot and at the back of the thigh (both must be within 3 mm — straps are level); platform top/bottom Z; carrier top/bottom Z and magazine protrusion; rig X extents at the anchor heights (criterion 3); hanger visible lengths; belt stand-off (mean and max distance from the belt's inner face to `Trousers.Main` over the ring, excluding ±15 mm round each belt loop); clearance of the panels' foam face to the trousers (3 ± 1 mm). Tolerances in §1.4 criterion 2.

### 8.3 Bite check
Along each strap's centreline at 36 azimuths: distance from the strap's inner face to `Trousers.Main` must be 0 ± 0.3 mm (touching), and the cloth 20 mm above and below the strap edge must be ≥ 3 mm further out than under it (the roll exists). Reported per strap; failure → "straps not biting" and criterion 11 scores 0.

### 8.4 Colour patches
Sample 5 × 5 means in V1 (graded) at the pixel positions of §2.2 after aligning the render to the reference by the two ladder-lock centroids (the belt row is expected to differ by D1, so the alignment uses the rig, not the belt); report ΔRGB per patch and ΔE76; criterion 4 passes at ≤ 10/255 per channel on 12 of 14 patches.

### 8.5 Hardware census
`bpy.data.objects` filtered by prefix: counts of `*.LadderLock*`, `*.Triglide*`, `*.Screw*`, `*.CordEnd*`, `Belt.Buckle.*`, `Belt.Dring`, `Belt.Keeper`, `*.Snap*`, `*.Latch`, `*.Band.*`, `Belt.HangerLoop.*`, `*.Bartacks` vertex counts (one bar tack = 42 × 2 × 6 verts); every strap object must have exactly one `fold` attribute marking a 15 mm fold with a bar tack within 5 mm of it.

### 8.6 Intersections
BVH overlap (`mathutils.bvhtree.BVHTree.FromObject` on the evaluated depsgraph) of every rig object against `Body.Mesh.Posed`, `Trousers.Main`, `Carrier.*` (if present), `Carbine.*` and `Glove.*`: list pairs with penetration > 0.3 mm (0 allowed between hard parts and cloth except the straps' deliberate 0 ± 0.3 contact). Float check: for every strap and the belt, the maximum distance from the inner face to the surface it crosses ≤ 0.5 mm except at the slots and across the belt loops.

### 8.7 Overlays and silhouettes
V1 overlay with the rig masks drawn from the reference (`ref/zoom_belt14_masks.json`: polygons for the right rig, left block, flank pouch, belt run, traced by the script from the §2.1 boxes); report the IoU of each rendered item's mask with the reference polygon **and** the centroid offset — IoU for the right rig is expected around 0.6–0.7 because of D3/D4 (narrower, black mag tops), and the criterion is the centroid (±25 mm) and the heights, not the IoU.

### 8.8 Critic questions (answered looking at V1–V8 and the overlays; each 0–2)
1. Does the belt read as a dense two-ply webbing belt with a quick-release buckle, not a leather strap or a flat ribbon?
2. Are the right carriers obviously magazine carriers with magazines in them, two-tone, slotted and screwed, standing on a platform strapped to the thigh?
3. Do the straps bite into the cloth and go all the way round, with hardware that threads the strap?
4. Is the left block a flap pouch and a hard case in a cradle, clearly two different materials?
5. Does the flank pouch hang from the vest and pass in front of the belt?
6. Is dust up, grime down, chips on edges only, stencils half gone?
7. Does the webbing look like webbing (herringbone, rounded selvedge) rather than wood or plastic?
8. Does anything float, clip, or z-fight?
9. Is every item on the correct side of the body?
10. Would a kit nerd name every item?

### 8.9 Failure modes to look for (with the fix)
Straps lying in the air 5–10 mm off the thigh at the back (anchor sampling missed the cloth → raise the azimuth sample count to 72); strap cutting through the cloth on the medial side where spec 09's band is thinner (lower the strap's inner face by 0.5 mm there, not globally); carriers hitting the thigh at 90° knee flexion (platform too low — allowed fix: raise the whole right rig ≤ 15 mm, log it); the belt not following the pelvis yaw (ring sampled from the body not the trousers → wrong object); **left/right swap** (the twin carriers on his left — the readback asserts `RigR.anchor.x < 0`); holster visible (`--with-holster` left on); stencils crisp and bright (erosion too weak); polymer glossy like wet plastic (roughness < 0.4, coat > 0.1); webbing wood-grain streaks (distortion missing); plates z-fighting with bodies (spacer rim missing, plate not 1.5 proud); the shock cord sinking into the plate (curve offset < 2 mm); mag tops poking through the vest hem (Z 1063 vs hem 1050 — if spec 13's hem is lower than 1050 the flank carrier drops by the difference); the D-ring glint missing in V1 (ring edge-on at the wrong azimuth — it must sit at X −175 ± 10).

---

## 9. Build order, effort and risks

| # | Step | Tool | Time (build / render) | Depends on |
|---|---|---|---|---|
| 1 | `gear_hardware.py`: cobra buckle, metal ladder-lock 38, tri-glide 38, D-ring, screws (countersunk, domed, washer), cord end, snap cap, latch — each a function returning an object, unit-tested by rendering a hardware contact sheet | bmesh + EXACT booleans + Bevel + Weighted Normal | 2 h coding / 40 s | research F §2, §8; shared with specs 12, 13 |
| 2 | `gear_webbing.py` extensions: strip along a sampled surface path at a given stand-off, fold + bar tack at the end, box-X, hanger sleeve, PALS generator reuse | bmesh, GN stitches | 2 h / 20 s | research F §1 |
| 3 | Anchors (§4.1) and the belt (§4.2) incl. loop check B8 | ray-casts on `Trousers.Main`, sweep, booleans | 1.5 h / V5 30 s | spec 09 built with the new waistband (D1) |
| 4 | Right platform (§4.3) + hanger | grid, Simple Deform, Solidify, Bevel, PALS | 1 h / V3 flat 10 s | 3 |
| 5 | Carriers, plates, screws, slots, cords, mags (§4.4) | boxes, EXACT booleans, Subsurf, curves, instances | 2 h / V3 30 s | 1, 4, spec 15 mag (placeholder otherwise) |
| 6 | Right straps + ladder-locks (§4.5), bite check (§8.3) | strip on path, lock threading | 1.5 h / V7 30 s | 2, 4, spec 09 bands |
| 7 | Left platform, strap, lock (§4.6) | as 4, 6 | 0.5 h / V4 flat 10 s | 2, 3 |
| 8 | Frag pouch (§4.7) | pouch recipe, lofts, PALS, snap | 1.5 h / V4 30 s | 1, 7 |
| 9 | Hard case + cradle (§4.8) | boxes, bevels, lip union, bands | 1 h / V4 30 s | 7 |
| 10 | Flank carrier (§4.9) | as 5 | 1 h / V6 30 s | 1, spec 13 PALS rows (nominal otherwise) |
| 11 | Materials (§5), wear node group, decals (§5.5) | shader nodes, PIL decals | 2 h / V3, V4, V6 lit 30 s each | assets manifest |
| 12 | Stitches pass (§4.10) | GN | 0.5 h / — | 3–10 |
| 13 | Rigging (§7), rig test (§7.4), rest-mode export | Data Transfer, Armature, glTF | 1.5 h / V8 30 s | spec 08 rig |
| 14 | Evaluation set (§8), readback, overlays, critic round | Cycles V1–V8 | 0.5 h / 8–12 min | all |
| | **Total** | | **≈ 20 h over two sessions**, renders ≈ 15 min per full round | |

Order rationale: hardware first because every later step threads a strap through it and its contact sheet settles the metal look early; belt before rigs because the hangers start on it; right rig before left because it has every construction type (platform, carrier, strap, lock, cord) and the left reuses them; materials before stitches so the thread colour is judged against finished cloth.

Risks:

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Spec 09's waistband not yet moved to Z 1013 when this part is built → belt built on cloth that is not there | high until the critique pass | the belt floats or sits on the hips | the script asserts the trousers' top edge Z ≥ 1005 and otherwise builds the belt on `Body.Mesh` + 4 mm with a warning; §10.1 |
| The cummerbund (spec 13) absent or at a different hem height | medium | flank carrier floats or clips the vest | anchor falls back to body + 12; clips extend to Z 1115 so a hem anywhere 1040–1110 hides them |
| EXACT booleans on bevelled boxes leaving non-manifold slivers (seen in research F magwell v1) | medium | shading artefacts on plates | cut before Bevel, on a single manifold box, then `bmesh.ops.dissolve_degenerate` and a manifold assert |
| Straps sampled on the uncompressed cloth → float by 3 mm | medium | criterion 11 fails | run order enforced in `build_all.py`; bite check aborts with a clear message |
| Thigh twist in the rig test flips normals on the strap ring | low | export artefacts | Data Transfer weights + the 25 % ring test |
| Product dimensions tagged [VERIFY] (case, ladder-lock, carrier class, pistol mag) wrong by > 10 % | medium | look still fine; the "kit nerd" criterion weakens | fetch datasheets in step 1 (network open) and update §3 in the same commit |
| Render time of V3/V4 with 180 k tris and thread geometry | low | slower iteration | `--look` Workbench loop; stitches hidden for form checks |

---

## 10. Interfaces and open questions for the client

### 10.1 Interfaces (what this spec asks of or gives to other parts)
* **Spec 03 (pelvis)**: iliac crest Z 1031 rest / hip centres 963 rest (D1 of spec 08) are the belt's datum; if those move, `BELT_TOP_Z = crest − 15` follows automatically.
* **Spec 09 (trousers)**: (a) move the waistband top to **Z 1013 posed / 1031 rest** and `Trousers.Belt` to Z 953.5–998 (this spec's D1); the rise becomes 250 mm to the kept crotch at 763 — a dropped-crotch cut, consistent with spec 08's note; (b) keep the belt loops 12 × 60 × 1.4 and the 1.6 mm clearance — the belt stands 2.0 off and bumps 0.6 over each loop; (c) strap footprints unchanged: 761–795, 651–700, 668–710; (d) the belt's lower edge wants a 4 mm roll below Z 953 (spec 09 §4.9 "Belt compression" moves up with the band).
* **Spec 08 (rig)**: bone weights as its attachment table; this part reads `BONE_MAP`; adds nothing to `Hero.Compress`.
* **Spec 12 (armour)**: shares `gear_hardware.py` (ladder-lock 38 here vs 25 there: one function with a width parameter) and `gear_webbing.py`.
* **Spec 13 (plate carrier)**: the flank carrier's clips need the cummerbund's lowest two PALS rows at his right flank azimuth 65°, nominal Z 1070 / 1108, and a hem at Z 1050; please expose `Carrier.Cummerbund` as a mesh for the pouch's Surface Deform.
* **Spec 15 (carbine)**: please build the magazine as a reusable object `Carbine.Magazine.PMAG30` (190 × 66 × 25, origin at the floor plate centre, +Z toward the feed lips) in its own cache so this part can instance two.
* **Spec 16 (materials)**: the §5.1 materials go into the library under the `BeltRigs.` names; `BeltRigs.Wear` is the shared wear node group.
* **Spec 17 (evaluation scene)**: V1/V2 cameras and lights are the shared ones; this part adds the rig-mask polygons `ref/zoom_belt14_masks.json`.
* **Game (hexcom loadout)**: export the rigs as separate nodes — `RigL.Frag.*` is the visual of the UTILITY slot (Frag Grenade), `PouchR.*` belongs with the SECONDARY slot (P9), the right carriers with the PRIMARY's spare magazines — so the loadout screen can show or hide them per slot.

### 10.2 Open questions for the client (with the default taken)
1. **Belt height.** Reality puts the belt at the pelvis (top Z 998), 140 mm above the drawing, and shrinks the exposed shirt between vest and belt from 190 to ≈ 50 mm; the long-waisted look of the picture goes. Default: reality (D1). Alternative: lower the vest hem too — that is spec 13's call, not ours.
2. **Pistol.** The picture shows a pistol-mag carrier and no pistol. Default: keep the carrier with magazines, no holster. Alternatives: `--with-holster` (hidden small-of-back holster, §4.12), or drop the carrier because the P9 is not carried.
3. **Visible magazines.** Real open-top carriers show 50 mm of black magazine; the picture shows none. Default: show them (D4). Alternative: flap-top pouches — different item, less faithful.
4. **Right carrier identity.** Twin rifle-mag carriers (default) vs tourniquet/flashlight holders. Changes nothing but the contents and the stencil.
5. **Left outer cell.** Pelican-1030-class hard case (default) vs a hard-shell radio holder (taller, 229 mm, would match the drawn height better but has no hinged lid).
6. **Left platform length.** 260 mm (to carry the strap at the drawn height) vs a 230 mm panel with the strap raised 30 mm. Default: 260.
7. **Hanger colour.** Coyote right / black left as read (default) or both black as the analysts wrote.
8. **Frag pouch contents.** Empty bulge over two hidden cylinders (default; nothing exposed per consolidated §6) vs one grenade's outline only.

### 10.3 Export notes
LOD1 ≤ 25 k tris (trim the carriers' Subsurf first, then the belt profile to 6 corner verts); textures: the decals and the baked wear masks only, everything else procedural → bake to 2K per material group if the game needs images (`object.bake`, research C §10). Node names = object names; one glTF per rig group.
