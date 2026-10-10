# Part 01 — Foot, ankle and sock

Status: draft 1 (spec writer), 2026-10-06; **revised 2026-10-10** against the reality-wins rule and the values shared with specs 02–04, 08 and 16–18 (§0). Owner script: `scripts/parts/01_foot_ankle_sock.py` (plus `scripts/lib/sculpt.py`; measurement primitives from spec 18's `scripts/lib/measure.py`). Object prefixes `Foot.<L|R>.*`, `Sock.<L|R>.*`, `Frame.Foot.<L|R>`; layers on `Body.Mesh` named `Foot.*`.

Conventions (from `CLAUDE.md`): millimetres in this spec, metres in Blender; world origin on the floor midway between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT = viewer's right**. Every "left/right" is the soldier's own. In addition this spec uses a **foot frame F** for each foot: origin at the pternion (most posterior heel point) projected onto the floor, +Z up, toes toward **−Y** (same heading as the character), so the toe tips sit at y ≈ −282 (−285 in the tables drafted before §0 item 1). For the LEFT foot the medial border is **−X** and the lateral border is **+X**; the right foot is the mirror (medial = +X). Every table below is written for the left foot in frame F; the right foot is `mirror(X)` unless a row says otherwise.

Research notes (`notes/research_*.md`) did not exist when this was written (checked at start and at the end). Facts that depend on them carry `[VERIFY: research_<topic>]`; the notes exist now, and §10.3 says which tags are settled.

## 0. Revision 2026-10-10: reality wins, shared values settled

Drafted before the reality-wins rule (`CLAUDE.md`, Source of truth) and before specs 08 and 16–18, this spec was revised just before part 01 is built, against that rule and against what it shares with specs 02, 03, 04, 08, 16, 17 and 18 (no interface ledger exists; each spec carries its own decisions). Where this list and older text disagree, the list wins; the sections it names were edited to match. "B" values were measured on `cache/body/rigged.blend` (the body of `build_all.py` S1–S2, specs 03/04's macros, rest stature 1855) on 2026-10-10.

| # | Change | Why | Specs touched |
|---|---|---|---|
| 1 | **ANSUR II "Tight"** (30 men 1830–1870 mm, 82–85 kg, × 1.0049 to 1855) replaces the stature-only group (n = 424): foot length **285 → 282**, heel breadth 74 → 71, bimalleolar 77 → 76, malleolus apexes 77 / 90 → 76 / 89, minimum ankle circumference 236 → 229, heel–ankle 357 → 353, ball 260 → 259; ball length 210 and breadth 105 stay (§3.1). §3.2–§3.4 positions stay as drafted for 285 mm; the build moves every point ahead of the MT-head line (y < −210) toward it by (282 − 210)/75 = 0.96 (hallux 75 → 72). | rule 1: "ANSUR II anthropometry for a 185 cm, 83 kg man" is the Tight column (`research_dimensions.md` §1); spec 08 §3.1 already uses 282 / 210 | 01. 01 owns the ankle circumference: spec 03 §3.5 and §4.2 quote 236 and take 229 when 03 is revised |
| 2 | **The man**: 1855 mm barefoot, 83 kg (was "185.5 cm, ≈ 92 kg mesomorph"); the body base fits the rest stature to 1855, not spec 04 D1's 1877. | `CLAUDE.md`; specs 03 §3.1, 08 §3.1, 18 D7 | 01; dated note in 04 (D1) |
| 3 | **Toe allowance 12 → 15 mm**, so the last stays 297 long (282 + 15). The last is built from the **rest** socked foot (toes flat, `Foot.Contact` at its loaded value) and carries its 12° toe spring itself; the posed foot is no longer used (old §7.4 added the pose's 10° toe extension to the last's own 12°). | boot fitting leaves 15–22 mm before the longest toe (`research_dimensions.md` §2, "Last vs foot"); one toe-spring number | 01 (§4.13, §7.4); spec 02's last length 297 unchanged |
| 4 | **In the hero pose the foot stands on the boot's footbed**, not the floor: plantar flexion 5.4° about the ball line, ball seat h 29, heel seat h 49 (spec 02 §4.1 step 2, §7.2), toes extended by the last's 12°; headings **85° right** (was 90°), **17° left** (was 15°); ankle axes (−208, +75) and (+208, −75) in plan, at h ≈ 122 rather than 80. | a foot inside a boot rests on its insole (spec 02); spec 08 owns the pose and its D3 sets 85° | 01 (§2.3, §7.3, §10.1); dated note in 08 (§4.6, §4.7 e, §10.1); Q7 |
| 5 | **Names**: the body is `Body.Mesh` and the rig `Morgan.Rig` (was `Human`). Layers this part puts on `Body.Mesh` carry its prefix: vertex groups `foot_*` → `Foot.*` (e.g. `Foot.Callus.Heel`), shape key `FootContact` → `Foot.Contact`, attributes `Foot.Tendon`, `Foot.Vein`, `Foot.Crease`; its own objects' groups (the sock's `sock_*`, the last's `last_*`) keep their names. Collection `Part01.FootAnkleSock` with children `Foot.Nails`, `Foot.Lasts`, `Foot.Guides`, `Sock.Pair`; prefixes `Foot.`, `Sock.`, `Frame.Foot.`; interface keys `foot.*`, `sock.*`. | spec 18 §4.4, §4.7 rule 2: `replace.body_layer()` finds a part's layers on the shared body by its capitalised prefix, so lower-case `foot_*` groups would never be cleaned on a re-run; `Frame.Foot.L/R` is spec 17's name | 01 (§4–§8, §10) |
| 6 | **Build stages**: the MPFB foot targets (§4.1) load in S1 `body.base` with the other detail targets, so the rig fit (S2) sees the final joint cubes. Part 01 runs in S3 on `cache/body/rigged.blend` and never edits `Morgan.Rig`: it publishes the §3.3 joint positions and the last markers as `foot.*` keys in `assets/interfaces.json`, and spec 08's S2 places the toe bones and adds `heel`, `ball` and `toes_master` from them, with spec 08's bone directions (heel → +Y 20, ball → +X 20). | a part writes only its own data (spec 18 §4.4); targets before the fit (spec 08 §4.1) | 01 (§4.1, §7.1); 08 §4.2 and §10.1 and 18 §4.6 already agree |
| 7 | **Materials from spec 16's library**, which supersedes §5's values (its C1, C27–C29, C32, C34, C39, §3.3.1, §10.1): `Body.Mat.Skin.Foot` (recipe `Skin.Foot` on `MG.Skin.Core`, was `Foot.Skin`), `Foot.Mat.Nail.Plate` / `.FreeEdge`, `Sock.Mat.Knit.Sock.WoolNylon(.Reinforced)`, `Hair.Body`; scatter radius (1.0, 0.2, 0.1) on dorsum and toes, (1.0, 0.45, 0.28) kept for sole and callus; skin sheen 0.04; vein tint 18 %; sock sheen 0.08 / 0.06, roughness 0.80 / 0.65; `knitted_fleece` at 230 mm; body hair melanin 0.75, redness 0.5; nail ridges 0.25 mm pitch. §5 keeps the regional data the library takes from this part. Until the library exists the first pass is judged on `form` renders with a placeholder skin. | one source for material values | 01 (§5, §6.1) |
| 8 | **Evaluation scene and harness**: "scene A" → spec 17's `LookDev` (AgX Base Contrast); "scene B" → its `Hero` scene; `scripts/eval/render_part01.py` → spec 17's `scripts/eval/render.py` with `scripts/eval/presets/p01.json` (owned here; it matches §1.3). The `Hero` lights are 3–5 × too bright until spec 17's calibration stage A, so colour judgements under them wait for it. | spec 17 §4.3, §4.14, §10.1; spec 18 §10.2 | 01 (§1.3, §8.1) |
| 9 | **One foot per closeup**: V2's camera looks across the other foot and both feet are one mesh, so the script makes `Foot.L.Isolate` and `Foot.R.Isolate` (render copies of one side's evaluated foot below z 300, `Subdivision` render 3) after saving its cache, so they never reach the cache or the assembly; the p01 presets hide `Body.Mesh` and the other side's `Foot.*` and `Sock.*`, and V6 hides the copies. The body's own `Subdivision` keeps spec 03's render level 2. | spec 17 §4.14 finding; old §4.8 (3) against spec 03 §4 (2) | 01 (§4.8, §8.1); `p01.json` (done) |
| 10 | **Render budgets on the GPU**: spec 17's tiers (`form`, `look`, `eval`, `final`) replace the CPU recipe (256 spp, ≤ 8 min a view, ≤ 2.5 h a set). Measured on the RTX 3050: `eval` hero frame 4 s, `form` crop 0.03–0.1 s warm; a 2048² closeup with SSS and hair is expected at 10–60 s, so a full set takes minutes. | the work runs on Jeff's workstation (spec 17 §4.14, spec 18 §4.13) | 01 (§8.1, §9.2) |
| 11 | **Measurement**: `scripts/lib/measure.py::measure_foot()` → part 01's own `measure()` in its script, returning spec 18's envelope and built on spec 18's primitives (`section`, `girth(kind='tape')` — ANSUR girths are tape, i.e. convex-hull, measures — `clearance`, `landmarks`); `sculpt.py` (owned here) drops `slice_measure` and gains a `falloff` argument ('smooth', or 'gauss' as specs 03 and 04 use it). MPFB detail targets are linear shape keys, so §4.1's fit is a bounded linear least squares through `linmodel` and `optim`, not a secant per target. | spec 18 D3, D14, §4.3, §4.8.4–4.8.5 | 01 (§4.1, §4.2, §8.2, §9.3) |
| 12 | **Proximity attributes on the closeup copies**: the tendon, vein and crease bands of §4.5 are written on the `Foot.<S>.Isolate` copies after their level-3 subdivision is applied. On `Body.Mesh` neither works: it has shape keys, so `modifier_apply` refuses the Geometry Nodes modifier, and its 5 mm vertex spacing cannot hold a 0.8 mm crease band. | Blender; `lib/ctx.py` `apply_modifier` | 01 (§4.5) |
| 13 | **Hair** follows specs 03 §4.10 and 04 §4.10: Curves objects `Foot.L.Hair`, `Foot.R.Hair`, built only with `--hair`; legacy particles are the fallback. **UV**: MakeHuman's `UVMap` is never edited; the bake fallback's foot tiles (§4.9) go into a second layer `Foot.UV`, made only if that fallback is needed. | one body-hair method; spec 16 §5.1 | 01 (§4.9, §4.12, §6.1) |
| 14 | **Markers and frames**: the last's `.Pternion`, `.Ball1`, `.Ball5` lie on its insole plane and are the three sole points spec 08 §4.7(e) aligns; `Frame.Foot.L/R` (frame F Empties) are made here for spec 17's presets. | spec 08 §10.1, §10.3; spec 17 §4.3 | 01 (§4.13, §4.14) |
| 15 | **The leg above the sock**: the old demand for a calf of 400–420 at z 330 is dropped; the sock wraps the leg the body has (B: 286 at z 260, 346 at z 330; ANSUR Tight calf maximum 384); spec 03 owns the leg. | ANSUR; spec 03 §3.5 | 01 (§10.1) |

New questions for Jeff from this revision: §10.2 Q7 (the boots lift the figure), Q8 (foot size) and Q9 (body mass, a finding of the body build).

---

## 1. Purpose and acceptance

### 1.1 What this part is
The bare foot and ankle of Sgt. Morgan from the toe tips to a cut line 260 mm above the floor (mid-calf, where the sock cuff ends), both sides; the ten toenails as separate shells; the terminal hair on the dorsum and toes; the skin material of the foot region; the military boot sock worn over it; the foot and toe deformation bones and their weights; and the **last** (the socked-foot envelope) that the boot part builds around. In the hero render every millimetre of this part is hidden by the sock, the boot and the trouser hem. It is built anyway because (a) the client requires it as the foundation of the method, (b) the boot's inner volume, toe-box shape, ankle break and collar height are all derived from this foot, (c) the rig's ankle and toe bones live here, and (d) it is the dress rehearsal for the visible skin (hands, face, neck) — every shader and sculpt-by-script helper written here is reused there.

### 1.2 What "perfect" looks like
A critic who knows feet, looking at a 2048 px closeup, cannot name a dimension that is wrong by more than the tolerance in §8.3, cannot find a symmetric or "copy-pasted" toe, sees ten nails with a nail fold, a lunula on the hallux, a free edge and a pink bed under a translucent plate, sees pale rough callus exactly where a boot-wearing 40-year-old man has it, sees sparse dark hair on the dorsum and a tuft on each big toe, sees the extensor tendons and dorsal veins as low relief (not painted lines), sees a heel that flattens under weight, and sees a sock whose knit, thickness, heel pocket, toe seam and rib are at the scale of a real boot sock. Nothing waxy, nothing like a mannequin.

### 1.3 Closeup render views (all in frame F of the LEFT foot; right foot mirrored; definitions for the render harness in §8.1)
The foot is not visible in the reference, so **no reference crop shows it**. Critics compare the anatomy views against the dimension tables in §3 (which carry their sources) and against real-world knowledge; the one image-constrained check is V6.

| View | Camera position (mm, frame F) | Target (mm) | Lens / sensor | Compared with |
|---|---|---|---|---|
| V1 Dorsal-oblique | (+230, −560, +420) | (0, −150, 40) | 60 mm, 36 mm sensor, 2048² | §3 tables (dorsum shape, tendons, veins, hair, toe splay) |
| V2 Medial | (−650, −140, +95) looking +X | (0, −140, 55) | 70 mm, 2048² | §3.2 arch, navicular, medial malleolus, hallux profile, callus on the hallux IP |
| V3 Lateral | (+650, −140, +95) looking −X | (0, −140, 55) | 70 mm, 2048² | §3.2 lateral malleolus, 5th MT base, 5th toe curl, lateral heel callus |
| V4 Plantar | (0, −140, −600) looking +Z, floor hidden | (0, −140, 0) | 50 mm, 2048² | §3.4 callus zones, ball crease, heel pad, friction ridges, toe pads |
| V5 Toe closeup | (−60, −600, +180) | (−30, −265, 15) | 100 mm, 2048², DOF f/8 focus on the hallux nail | §3.3 toe and nail tables, nail fold, lunula, free edge, hair tufts |
| V6 Ankle in boot envelope | world camera of the hero shot (0, −4500, 600), 46 mm, cropped to each boot | — | as hero | `ref/crop_boots_feet.png`, `ref/zoom_foot_right_boot_x6.png`, `ref/zoom_foot_left_boot_x6.png`: the socked-foot envelope + boot allowances must fall **inside** the boot silhouette from the reference (§8.2) |
| V7 Sock views | V1, V2, V4 repeated with `Sock.L.*` visible | — | — | §3.6 sock table: cuff rib, leg rib, heel pocket, toe seam, knit scale |

Each view is a preset of `scripts/eval/presets/p01.json` (`p01.V1`…`V5` with `.L`/`.R`, the right mirrored; `p01.V6.L/.R` = `p02.V2`/`p02.V1`; the ortho `p01.V1o`…`V4o` of §8.1), rendered by spec 17's `render.py` in `LookDev` and once more under the `Hero` lights for colour (§8.1); V1–V5 show one foot alone (§0 item 9).

### 1.4 Pass criteria a critic can score (full list in §8.3)
1. Every length in the part's automated `measure()` report (§8.2) is within tolerance of §3 (lengths ±3 mm, widths ±2 mm, heights ±2 mm, nails ±1 mm).
2. Toe order and relative lengths read as an "Egyptian" foot (hallux longest, 2nd 3–5 mm shorter, descending), with a 5th toe rotated 30–45° and tucked under the 4th.
3. Nails: ten shells, visible thickness at the free edge (1.0–1.2 mm hallux), nail fold rim, hallux lunula visible, pink bed through the plate, no floating or sunk nail.
4. Callus visible as paler, rougher, drier skin at the four zones in §3.4 and nowhere else; sole paler and yellower than the dorsum; toes and pressure zones pinker.
5. Hair: 90–160 terminal hairs per dorsum, 6–12 on each hallux, 0–3 on each 5th toe, radius 0.03–0.04 mm, dark brown, lying flat distally.
6. Tendons and veins read as relief (0.5–1.5 mm) that catches rim light, not as colour strokes.
7. Weight-bearing variant: heel pad spread ≥ 3 mm wider than the hanging variant, arch drop 2–3 mm, floor contact a flat patch (no hovering, no sinking).
8. Sock: thickness visible at the cuff edge (2.0–2.5 mm), 1×1 rib cuff, 2×2 rib leg, smooth reinforced heel and toe in a darker yarn, knit stitch pitch 1.5–1.8 mm, no toe gaps visible through the sock, no intersection with the skin or nails.
9. V6: the sock envelope plus boot allowances lies inside the reference boot silhouette for both feet within 5 px.
10. No waxy or glowing SSS on the toes (toe shadow side must stay darker than the lit side by ≥ 1.5 stops under the look-dev key).

---

## 2. Reference observations

### 2.1 What the image shows about this part
Nothing of the skin or sock is visible; the feet are inside 8-inch boots under loose trouser hems. The image constrains the foot indirectly through placement, size envelope and weight. All coordinates are full-image pixels (1672 × 941; 4.72 px/cm = 2.12 mm/px at the figure, `analysis_consolidated.md` "Agreed scale").

| Observation | Pixels | Derived for the foot | Source |
|---|---|---|---|
| Right sole (floor datum) / left sole | y = 895 / 907 | left foot 10–20 cm nearer the camera; adopt **150 mm** forward | consolidated §1, pose note §5 |
| Right / left ankle (boot break, malleolus level) | (732, 855) / (928, 858) | ankle 8.5 cm above the sole → the talocrural axis at ≈ 80 mm, consistent with ANSUR lateral malleolus 77 mm (§3) | consolidated vertical landmarks |
| Ankle-to-ankle | 196 px | **416 mm** lateral separation → rest ankles at world x = ±208 | pose §6 stance table |
| Heel-to-heel / toe-to-toe | 145 / 320 px | 308 / 678 mm — only consistent with the right foot in profile | pose §6 |
| Right foot toe → heel | x 631 → 767 (136 px) | 288 mm projected boot length; ≤ 20° out of plane → outsole 290–306 mm → **foot 275–290 mm = EU 44–45** | pose §5, my check |
| Right foot direction | toe at x 631 | toes point **≈ 90° to his right** (toward −X); medial (instep) side faces the camera | consolidated disputes #1 |
| Left foot direction | toe box x 940–950 vs ankle 928 | toes 15–20° to his left of the camera axis; adopt **15°** (my width check below suggests the low end) | pose §6 |
| Boot collar top | y 795–800 | 21 cm → sock cuff must end **above** this (260 mm) and below the trouser hem folds (y 760–810) | consolidated |
| Weight | body centre-line x ≈ 812 between ankles 732/928 | **≈ 55 % on the right (rear, turned-out) foot, 45 % on the left** | pose §6 |
| Contact shadows | true-black core under both soles, penumbra 3–6 cm | feet flat, full plantar contact; no heel lift, no toe lift | lighting §2.6 |
| Floor | sealed concrete, roughness 0.30 | the plantar skin never touches it (boots) — irrelevant to skin wear | lighting §3 |

### 2.2 My own measurements from the zoom crops (`ref/zoom_foot_*.png`, made with PIL from `reference_full.png`)
Silhouette runs (pixels darker than 110 against the lit floor) per row:

| Row y | Right boot dark run | Width px → mm | Left boot dark run | Width px → mm |
|---|---|---|---|---|
| 810 | 695–758 | 63 → 134 (shaft, medial view = front-to-back depth of the shaft) | 897–946 | 49 → 104 (shaft width at the ankle, head-on) |
| 830 | 690–756 | 66 → 140 | 898–960 (incl. lateral strap) | 62 → 131 |
| 855 | 676–760 | 84 → 178 (throat/instep break) | 901–953 | 52 → 110 |
| 880 | 631–764 | 133 → 282 (vamp + toe) | 899–973 | 74 → 157 (toe box seen 15° off-axis) |
| 895 | 630–763 | 133 → 282 (outsole) | 899–977 | 78 → 165 |
| 905 | 687–762 | — (reflection) | 903–977 | 74 (lug row) |

Reading: the right boot shaft is 134–140 mm deep front-to-back at the ankle and the left boot shaft 104 mm wide — a socked ankle (bimalleolar 77 mm + sock 4 mm + padded collar 2 × 10 mm ≈ 101 mm) fits exactly. The left toe-box projected width 157 mm is less than a 118 mm-wide, 310 mm-long boot would show at 20° yaw (≈ 200 mm), so the left foot yaw is nearer **10–15°**; adopted 15°. The medial side of the right boot shows the collar strap buckle at (745–760, 812–830) and the lace ladder at x 690–720 climbing from y 858 to 805 — the throat break (dorsiflexion crease of the boot) is at y ≈ 850–858, i.e. **≈ 85–95 mm above the sole**, which is where the anterior ankle crease of the foot must be (§3.2). [2026-10-10: not in a real boot. Standing on the footbed (§0 item 4) the foot's crease is at h ≈ 120; the drawn boot break is the image's, and reality wins.] Colour samples (5 × 5 means) only matter for the boot part: right collar strap #2c3238, left #322e2e, right quarter in shadow #0f1316, left vamp #4b413b, floor under the right sole #4f4a48, under the left #363433.

### 2.3 Ambiguities and decisions
| Ambiguity | Decision |
|---|---|
| Nothing of the foot is visible | Build a canonical, individual foot from anthropometry (§3) at the ANSUR size for this man (282 mm, EU 44–45; the boots' 275–290 range allows it), with asymmetries chosen by us (§3.3) — not a mirrored pair |
| Left foot yaw 10–20° | 17° to his left of the camera axis (spec 08 §4.6; this spec first said 15°); the right foot 85° to his right (spec 08 D3) |
| Depth offset 100–200 mm | 150 mm (left ankle at world y = −75, right at +75) |
| Weight split 50/50 … 58/42 | 55/45 (spec 08 D6): `Foot.Contact` shape key 1.0 on the right, 0.85 on the left |
| Sock colour (never visible) | coyote brown with charcoal heel/toe (§5.4) — matches the tan/black kit; client to confirm (§10) |
| Toes inside the boot | the foot stands on the boot's footbed, plantar-flexed 5.4° (spec 02 §7.2), with the toes extended by the last's 12° toe spring; toes 2–5 adducted together (§7.3) |

---

## 3. Real-world reference

Legend: **(M)** measured from the reference image, **(S)** sourced — ANSUR II "Tight" means (30 men 1830–1870 mm, 82–85 kg; `notes/research_dimensions.md` §1) × 1.0049 to 1855 mm, with the stature-only group of `assets/dimensions/ansur2_male.csv` (1830–1880 mm, n = 424, mean ± SD) in brackets for the spread, or the named note/file, **(B)** measured on `cache/body/rigged.blend` (spec 18 S1–S2: specs 03/04's macros, rest stature 1855, A-pose) on 2026-10-10 with numpy on the evaluated mesh (tape girths are convex-hull perimeters of plane sections; the left and right feet are mirror images), **(E)** estimated from anatomical ratios. Target values are the numbers the build must hit; they are chosen for the 1855 mm, 83 kg man of `CLAUDE.md` with 282 mm feet (EU 44–45).

### 3.1 Whole-foot dimensions
| Quantity | ANSUR Tight × 1.0049 (S) [stature-only mean ± SD] | Target (mm) | MPFB base at 1855 (B) | Correction needed |
|---|---|---|---|---|
| Foot length (pternion → longest toe tip) | 282.4 [283.2 ± 9.1] | **282** | 279.6 (long axis within 2° of −Y; the hallux and toe 2 reach equally far) | +0.9 %: `foot-scale-incr` (S1) |
| Ball-of-foot length (pternion → 1st MT head, medial) | 210.0 [209.9 ± 8.0] | **210** (74.5 % L) | ≈ 216 (MTP1 joint cube) | move the 1st MT head back ≈ 6 (§4.2 step 8) |
| Lateral ball length (pternion → 5th MT head) | — | **185** (65.6 %) (E) | 203 (MTP5 joint cube) | shorten 18: the MPFB 5th MT head sits too far forward |
| Foot breadth, horizontal (ball) | 104.5 [104.6 ± 5.0] | **105** | 102.7 | +2.3 |
| Heel breadth (standing) | 71.3 [74.1 ± 5.4] | **71** | 65.2 (widest section within 60 mm of the pternion, below z 45) | +6: sculpt (§4.2 step 3) |
| Bimalleolar breadth | 76.4 [77.4 ± 3.6] | **76** | 71.4 (band z 60–100 at the ankle) | malleoli +2.5 each side |
| Lateral malleolus height (apex) | 76.4 [76.6 ± 5.2] | **76** | not resolved as a bump (ankle joint cube at z 76.1) | sculpt |
| Medial malleolus height (apex) | — | **89** (E: +13 over lateral) | — | sculpt |
| Ankle circumference (minimum, above malleoli) | 229.1 [236.3 ± 13.8] | **229** at z ≈ 115–145 | 225.3 at z 142 (235 at z 115) | +4: `measure-ankle-circ-incr`, small (S1) |
| Heel–ankle (instep diagonal) circumference | 352.7 [357.0 ± 12.8] | **353** | 349 (plane through the pternion and the front of the ankle at z 85) | check after fit |
| Ball circumference | 259.3 [259.8 ± 11.8] | **259** | — (to be measured in the oblique MT-head plane, §8.2) | check after fit |
| Instep circumference (at 50 % L) | — | **263** (E) | — | — |
| Dorsum (instep) height at 50 % L | — | **66** (E: 0.23 L) | 71.2 | −5 |
| Dorsum height at 60 % L | — | **56** (E) | 62.8 | −7 |
| Dorsum height just behind the MT heads (70 % L) | — | **40** (E) | 47.9 | −8 (MPFB forefoot is puffy) |
| Medial arch clearance at 45 % L (standing) | — | **13** (E, normal arch) | ≈ 22 at 50 % | lower 7–9 |
| Navicular tuberosity height (standing) | — | **42** (E) | — | sculpt |
| Lateral border clearance at 50 % L | — | **4** (E) | ≈ 37 (lowest point of the lateral third of the section: the MPFB lateral midfoot is lifted) | flatten |
| Heel pad thickness unloaded / loaded | — | **19 / 15** (E) | — | `Foot.Contact` key |
| Pternion height (most posterior point) | — | **30** (E) | 45 | sculpt (§4.2 step 3) |
| Achilles insertion (upper edge of the calcaneal tuberosity) | — | **52** (E) | — | sculpt |
| Toe spring, barefoot standing | — | 0 (toes flat) | toe tips at z 12–15 (nail height) | ok |
| Ankle (talocrural) axis | — | **80** (specs 03, 08) | joint cube z 76.1, 64 mm ahead of the pternion | the rig's ankle; §3.2 |
| Knee height mid-patella (scale check only) | 519.5 [520.5 ± 16.9] | — | knee joint cube z 537 (spec 08's solver: axis 526) | the image gives 519 mm (y = 650) — the stature assumption is confirmed |

### 3.2 Skeleton (26 bones + 2 sesamoids) and the surface landmarks it makes
Coordinates are centres/apexes for the LEFT foot in frame F (mm). Mark: all (E) unless noted; the x/y placement follows the lengths in §3.1. The tables of §3.2–§3.4 were drafted for a 285 mm foot: the build moves every point ahead of the MT-head line (y < −210) toward it by the factor (L − 210)/75 = 0.96 for L = 282, so the toes shorten (hallux 75 → 72) and nothing behind the line moves (§0 item 1).

| Bone(s) | Count | Surface landmark it creates | Position (x, y, z) | Size / relief |
|---|---|---|---|---|
| Talus | 1 | ankle joint axis (through the malleolar tips); the dorsal talar neck under the anterior ankle crease | joint centre (0, −68, 80) | axis tilted 8° (lateral end lower and posterior) |
| Calcaneus | 1 | heel: pternion; calcaneal tuberosity / Achilles insertion; peroneal tubercle (lateral, small) | pternion (0, 0, 30); insertion (0, −6, 52); peroneal tubercle (+36, −60, 22) | heel plan radius 27; tuberosity 25 wide; tubercle 6 mm dome, 1 mm proud |
| Navicular | 1 | navicular tuberosity (medial) | (−40, −120, 42) | 12 mm dome, 2 mm proud |
| Cuboid | 1 | none distinct; lateral border fullness at 50 % L | (+42, −145, 20) | — |
| Cuneiforms (medial, intermediate, lateral) | 3 | instep crest: the dorsal high line runs from the ankle crease to the 1st–2nd MT bases | medial cuneiform dorsal point (−12, −140, 62) | the instep peak |
| Metatarsals 1–5 | 5 | 5th MT base (styloid) — sharp lateral bump; 1st MT head medial bulge (ball); dorsal MT shafts as five faint ridges with extensor tendons on top | 5th base (+50, −150, 18); 1st head medial point (−52, −210, 22) | styloid 8 mm, 2.5 mm proud; 1st head bulge radius 14 |
| Sesamoids (under the 1st MT head) | 2 | plantar pad under the hallux ball, firm | (−36/−26, −206, 0) | each 10 × 7 mm, flush |
| Hallux phalanges (proximal, distal) | 2 | IP joint knuckle, nail bed on the distal | see §3.3 | — |
| Toes 2–5 phalanges (P, M, D) | 12 | PIP knuckles (dorsal corns possible), DIP, nail beds | see §3.3 | — |
| **Soft-tissue landmarks** | | | | |
| Medial malleolus (tibia) | — | round dome | apex (−38, −73, 89) | 30 mm dome, 5 mm proud of the shin line; belongs to the SHIN for weighting |
| Lateral malleolus (fibula) | — | pointed, lower and further back | apex (+38, −60, 76) | 24 mm dome, 5 mm proud |
| Achilles tendon | — | cord from the calf to the insertion | at z 100: (0, +2, 100), 16 wide × 7 deep | retro-malleolar hollows either side 4 mm deep (the pre-Achilles fat pads) |
| Anterior ankle crease | — | one horizontal fold at the dorsiflexion line | from (−30, −80, 84) to (+32, −76, 80), bow 3 mm toward the toes | 0.4 mm deep, 1.2 mm wide, plus 2–3 fine parallel lines 3–4 mm apart above it |
| Extensor hallucis longus | — | cord to the hallux | from (−10, −90, 70) to (−38, −230, 24) | 5 wide, 1.5 proud with the toes extended |
| Extensor digitorum longus branches ×4 | — | fan to toes 2–5 | from (+5, −90, 68) fanning to the MTPs of toes 2–5 | 3.5 wide, 1.0 proud |
| Tibialis anterior | — | broad cord medial of the crease | from (−22, −75, 80) to (−30, −135, 55) | 9 wide, 1.5 proud |
| Dorsal venous arch + tributaries | — | arch across the dorsum at 55–65 % L, medial tributary to the great saphenous vein in front of the medial malleolus | arch from (−40, −165, 40) over (0, −175, 48) to (+42, −160, 30); great saphenous passes (−44, −80, 85) | Ø 2.5–3 mm, 0.7 mm proud; tint §5.2 |
| Toe webs (commissures) | — | web depth between toes | 1–2 (−30, −232, 10); 2–3 (−6, −236, 10); 3–4 (+14, −232, 9); 4–5 (+36, −224, 8) | — |

### 3.3 Toes and nails (the client's question: how big is the big toe)
Phalanx lengths follow published ratios for a 285 mm foot (the build shortens them by 0.96 for the 282 mm foot, §3.2); soft-tissue pulp adds 5–8 mm beyond the distal phalanx. MTP = metatarsophalangeal joint centre (metatarsal head centre), IP/PIP/DIP = interphalangeal joint centres, all in frame F for the LEFT foot.

| Toe | MTP (x, y, z) | Phalanx bone lengths P / M / D | PIP (IP) / DIP | Tip (pulp) | Toe length from MTP | Max width (at the pulp / IP) | Height at IP / at nail root | Axis (yaw, roll) |
|---|---|---|---|---|---|---|---|---|
| 1 Hallux | (−40, −210, 25) | 31 / — / 23 | IP (−42, −251, 22) | (−45, −285, 8) | **75** (62 visible from the plantar crease) | **26** | **22 / 19** | 8° lateral valgus; nail faces up, 5° medial |
| 2 | (−17, −217, 24) | 27 / 13 / 11 | (−16, −253, 20) / (−15, −266, 15) | (−14, −281, 7) | 64 | 17 | 16 / 13 | straight |
| 3 | (+3, −211, 22) | 25 / 11 / 10 | (+5, −244, 18) / (+6, −255, 14) | (+7, −270, 7) | 59 | 16 | 15 / 12 | 2° medial |
| 4 | (+22, −202, 20) | 23 / 10 / 10 | (+25, −233, 17) / (+27, −243, 13) | (+30, −258, 7) | 56 | 15 | 14 / 11 | 5° medial, 10° roll (under-rotated toward toe 3) |
| 5 | (+42, −185, 18) | 22 / 9 / 9 | (+46, −209, 15) / (+48, −217, 12) | (+50, −237, 7) | 52 | 14.5 | 13 / 11 | 12° medial, **35–40° roll** (nail faces up-and-lateral; tucks under toe 4) |

Relative tip positions (fraction of foot length): 100 / 98.5 / 95 / 90.5 / 83 %. MPFB base (B, bone tails at 1855): 100 / 100 / 96.2 / 90.4 / 85.8 %, with the MTP1 joint 216 mm and the MTP5 joint 203 mm from the pternion → the MT heads move back (§4.2 step 8) and each toe tip is then placed at its target fraction (§4.3 step 1): toe 2 ends 4 mm short of the hallux instead of level with it, toes 3–5 shorten by a few mm, and the hallux lengthens by about the 6 mm its MT head moved back.

Nails (plate = separate shell object; bed = existing mesh faces):

| Nail | Plate width × visible length | Thickness at the free edge | Free edge beyond the hyponychium | Transverse radius of curvature | Lunula | Nail fold | MPFB nail faces (B) |
|---|---|---|---|---|---|---|---|
| 1 | **17 × 16** | **1.1** | 1.5 (trimmed straight across, slightly rounded corners) | 11 mm | visible, 3.5 mm crescent | proximal fold 1.5 mm wide, 0.4 mm raised eponychium; lateral folds 1.0 mm | 16.8 × 19.0 — too long: scale 0.85 along the toe |
| 2 | 11 × 10 | 0.8 | 1.2 | 6 mm | faint | 1.0 / 0.8 | 10.8 × 9.8 ok |
| 3 | 10 × 9 | 0.7 | 1.0 | 5.5 mm | none | 1.0 / 0.8 | 10.3 × 9.1 ok |
| 4 | 9 × 8 | 0.7 | 1.0 | 5 mm | none | 0.9 / 0.7 | 9.0 × 6.3 — lengthen ×1.25 |
| 5 | 7 × 6 | 0.9 (thickened, slightly ridged) | 0.8 | 4 mm | none | 0.8 / 0.6 | 8.0 × 8.3 — shrink to 7 × 6 |

Asymmetries to build (so the pair is not a mirror): right 2nd toe 1.5 mm shorter than the left; left 5th toe rolled 40°, right 35°; left hallux valgus 10°, right 7°; right hallux nail with a 0.2 mm transverse ridge (old trauma line) 5 mm from the fold; left 4th toe PIP with a small 5 mm dorsal corn (callus, §3.4).

### 3.4 Skin: thickness, texture scale, colour zones, callus, hair, veins, creases
| Region | Epidermis / dermis thickness | Micro-relief | Colour (albedo, sRGB) | Notes |
|---|---|---|---|---|
| Dorsum, ankle, shin | 0.08–0.10 / 1.0–1.3 mm | polygonal network, cells 0.3–0.6 mm, lines 0.03 mm deep; follicle pits Ø 0.15 mm, 0.05 mm deep, 15–25 per cm² | **#b6886f** (body base #b98670 from the consolidated note, 2 % less red) | thin, mobile skin; veins and tendons show; slight oily sheen (coat 0.15) |
| Toes, dorsal distal and tips | 0.1 / 1.2 mm | finer cells 0.25–0.4 mm; 3–6 transverse wrinkles over each IP/PIP, 0.2 mm deep, 1 mm pitch | **#c48474** (redder, as the cheek SSS tone #c98272) | redness from capillaries; cooler blue-grey #a89a95 at 10 % on the hallux dorsum |
| Sole, arch (non-weight-bearing) | 0.4 / 2.0 mm | fine ridges 0.45 mm pitch, 0.02 mm deep | **#d8b798** (paler, yellower) | soft, slightly glossy (roughness 0.5) |
| Sole, heel centre and ball (weight-bearing) | 1.0–1.4 / 2.5 mm + fat pad 19 mm | friction ridges 0.45–0.5 mm pitch, 0.05 mm deep; ball crease (a deep curved fold under the MT heads from (−48, −200, 0) to (+50, −178, 0)), 1.5 mm wide, 0.8 mm deep | pressure pink **#d9a48e** blended 60 % into #d8b798 | compressed when standing |
| Toe pads (plantar) | 0.8 / 2.0 mm | friction ridges in whorls/loops 0.45 mm pitch, 0.06 mm deep | #d9a48e | digital flexion creases at the IP/PIP, 0.5 mm deep |
| **Callus 1 — heel rim** (posterior-lateral margin of the heel, a band 12–18 mm wide from (−25, −8) around to (+30, −30) at z 0–12) | +1.0–2.0 mm stratum corneum | crazing: polygonal plates 2–5 mm, fissures 0.3–0.8 mm wide, 0.3 mm deep; roughness 0.75 | **#e0cba8** core, edge #c9ad8a, fissure floors #b89a7e | dry, dusty-pale; the most visible callus |
| **Callus 2 — ball** under the 1st–2nd MT heads (ellipse 32 × 22 mm centred (−28, −208, 0)) | +0.8–1.5 mm | ridges flattened, roughness 0.65 | #e0cba8 at 70 % | smooth-edged |
| **Callus 3 — lateral 5th MTP** (circle Ø 18 mm at (+50, −185, 4), wrapping onto the lateral border) | +1.0 mm | roughness 0.7 | #e0cba8 at 80 % | boot-rub callus |
| **Callus 4 — medial hallux IP** ("pinch callus", 14 × 10 mm at (−53, −250, 10)) | +0.8 mm | roughness 0.7 | #e0cba8 at 60 %, yellower #e6d0a4 | from toe-off against the boot |
| Dorsal corn, left 4th toe PIP (5 mm) | +0.6 mm dome | roughness 0.75 | #e6d0a4 with a #c9ad8a ring | boot pressure, left foot only |
| Heel counter rub, Achilles at z 45–70 | — | smoother, roughness 0.4 | hyperpigmented #a67a66 at 40 % over an oval 22 × 30 mm | sock-and-boot friction |
| Hair — dorsum of the foot (area ≈ 65 cm²) | — | — | **#3a2a1e root → #5a4030 tip** (spec 16 `Hair.Body`); 4 % of strands grey #9a9088 | **2 ± 1 per cm² → 90–160 hairs**, length 6–10 mm (max 14), radius 0.035 mm root / 0.02 mm tip, lying flat toward the toes, 10–20° random yaw; density tapering to 0 at 55 % L and at the toes except the tufts |
| Hair — hallux tuft (proximal phalanx dorsum, 12 × 10 mm patch) | — | — | same | **8–12 hairs, 5–8 mm** |
| Hair — toes 2–4 | — | — | same | 2–4 hairs each, 3–6 mm, on the proximal phalanx |
| Hair — 5th toe | — | — | same | 0–3 hairs, 3 mm |
| Hair — sock band (z 90–260) | — | — | same | reduced to 30 % of the shin density (sock-line rubbing); the shin density itself belongs to the leg part |
| Veins — dorsal arch and tributaries | 0.7 mm proud | — | tint 18 % **#7d8b86** (grey-green, spec 16 C29) over the base along the vein mask, 4 mm wide, soft | great saphenous 3–3.5 mm Ø, 1.0 mm proud in front of the medial malleolus |
| Nail bed / plate / lunula / hyponychium | — | plate: fine longitudinal ridges at 0.25 mm pitch, 0.01 mm deep (spec 16 `Nail.Plate`) | bed **#d49a88**; plate **#e9dfd6** translucent (transmission 0.55); lunula **#efe4dc**; free edge **#ece6dd** (transmission 0.70); hyponychium #c99585; a faint under-edge grime line #6d5a4a at 25 % | nails trimmed straight, unpolished; roughness 0.15 plate / 0.25 free edge, coat 0.6 (spec 16 §3.3.1) |

### 3.5 Pose-dependent shape: weight-bearing and boot fit
| Effect | Magnitude | Where | Implemented as |
|---|---|---|---|
| Heel pad compression | 4 mm vertical, +3.5 mm width spread | heel contact ellipse 55 × 45 mm | shape key `Foot.Contact` (flatten z < 4 to z = 0 with 20 mm falloff, bulge the pad rim outward 3 mm) |
| Arch drop (navicular drop) | 2.5 mm | 35–55 % L medial | same key |
| Forefoot spread | +3 mm ball width, toe pads flatten 1.5 mm | MT heads and toe pads | same key |
| Foot lengthening | +2 mm | toe tips | same key |
| Toe spring inside the boot | MTP extension 12° (the last's toe spring, §4.13), IP flexion 0–3°; the whole foot plantar-flexed 5.4° on the footbed (spec 02 §7.2) | all toes | pose bones (§7.3) |
| Toes pressed together by the toe box | toes 2–5 adducted 2° each toward toe 2; 5th roll +5° | toes | pose bones |
| Sock compression | leg 1.6 mm, cuff 2.4 mm, sole under load 1.8 mm (from 3.0) | sock | Solidify thickness × vertex-group factor (§4.11) |

### 3.6 The military boot sock (real-world construction)
Model: mid-calf cushioned boot sock, merino-rich wool/nylon with 1–3 % elastane (`research_dimensions.md` §2 gives 80/19/1 for the Darn Tough T4033 [snippet]; the fibre split changes nothing visible), knitted on a 168-needle 4.5-inch cylinder (≈ 6 wales per cm on the leg, 8 courses per cm), e.g. the Darn Tough T4033 / Fox River 6074 class.

| Component | Dimension (worn, on this foot) | Construction | Thickness |
|---|---|---|---|
| Cuff (welt) | top at **z 260**, 32 mm tall | 1×1 rib, elasticated, folded double (welt) | 2.4 mm |
| Leg | z 90 → 228 | 2×2 rib, rib period 7.5 mm (ridge 3.5 mm wide, valley 4 mm), 0.6 mm relief | 1.6 mm |
| Ankle / instep | z 40 → 90 and over the dorsum | plain stockinette (V stitches 1.6 mm wide × 1.2 mm tall) with a 3 mm-wide elastic "arch band" of 1×1 rib around the midfoot at 45–55 % L | 1.6 mm |
| Heel pocket | turned heel, Y-shaped gore lines meeting at the pternion, gore 55 mm along each arm | smooth jersey, nylon-plated, **contrast dark yarn**, extends 25 mm up the Achilles and 45 mm under the heel | 2.2 mm (terry inside) |
| Sole | from the heel pocket to the toe seam | terry loops 1.2 mm inside, smooth outside | 3.0 mm unloaded → 1.8 mm under the foot |
| Toe cap | from the webs to the tips, 35 mm long | smooth jersey, contrast dark yarn, hand-linked flat toe seam across the top of the toes 1 mm proud | 2.2 mm |
| Toe seam | a ridge 1 mm × 1.5 mm from (−52, −255, 20) to (+50, −232, 14) across the dorsum of the toes | linked seam | — |
| Size stripe | 2 mm grey line 5 mm behind the toe seam | — | — |
| Colour | body **#5a4b3a** (coyote brown, slightly faded), heel/toe **#33302c**, stripe #7c6b58, sole grime #4b4035 blended 50 % under the foot and 30 % up the heel | — | — |
| Wear | pilling 10 % of the sole and heel (bobbles 1–2 mm), slight thinning at the heel pocket (thickness ×0.8), fuzz halo 0.5 mm | — | — |

---

## 4. Geometry construction plan

All steps are performed by `scripts/parts/01_foot_ankle_sock.py` (stage S3 of `build_all.py`) on `Body.Mesh` from `cache/body/rigged.blend` (the MPFB body at its final macro values and the foot targets of §4.1, rigged; spec 18 S1–S2; see §9 dependencies). The script is idempotent: it runs inside `replace.part_scope(PART)` and `replace.body_layer(PART)`, which delete its objects and data-blocks (prefixes `Foot.`, `Sock.`, `Frame.Foot.`) and its `Foot.*` layers on `Body.Mesh`, then rebuilds (§0 item 5). Everything below is bpy/bmesh; no operator needs a UI context except where noted (those use `bpy.ops` with a temporary `context.temp_override`, or the real selection for mode changes, `lib/ctx.py`).

### 4.0 Facts about the base mesh the plan relies on (B — measured on `cache/body/rigged.blend`, 2026-10-10)
* `Body.Mesh` has 19,158 vertices (13,380 in the `body` group; the rest are helper geometry masked by the `Hide helpers` MASK modifier, first in the stack, then `Armature`). The foot region (body vertices with z < 130 mm) has **1,105 vertices per foot, ≈ 1,095 faces, all quads**. No material is assigned (MPFB's skins are not used; spec 16 makes the materials). One UV layer, MakeHuman's `UVMap`. Shape keys: `Basis` and 13 MPFB macro keys (spec 04's full S1 bakes them into the basis).
* Toes are **already separate** (no webbing): per-toe vertex groups from the default rig weights (`toe1-1.L`, `toe1-2.L`, `toe2-1..3.L`, … `toe5-3.L`) occupy distinct x ranges; the hallux distal phalanx carries 130 vertices / 109 faces, each lesser toe ≈ 100 faces.
* **Toenails are the vertex group `toenails`** (135 vertices per foot; 10 nails × 20 quads, a 4 × 5 grid per nail, the faces whose vertices all lie in the group). The nail faces are flush with the skin — no plate thickness, no free edge, no fold.
* Vertex groups available: `body`, `toenails`, deform groups for all 14 toe bones + `foot.L/R`, `lowerleg02.L/R`, and MakeHuman "joint cube" groups `joint-l-ankle`, `joint-l-foot-1/2`, `joint-l-toe-N-M` (8 vertices each) whose centroids give the rest joint positions (world mm after S1's centring: ankle (200.6, 0.0, 76.1); MTP1 `joint-l-toe-1-1` (169.9, −152.4, 35.1); MTP5 (247.3, −139.7, 25.2)). Pternion at y +63.7, hallux tip at y −214.1: foot length 279.6 along the footprint's long axis at 1855.
* UV: the foot occupies **two islands** (dorsal with toes, plantar) in the body UV at u 0.198–0.635, v 0.010–0.169 (bottom strip of the atlas), **1.75 % of the 0–1 space**; at the 2048 px MakeHuman skins this is ≈ 10.7 px/cm (21.5 px/cm at 4096) — useless for closeups. The MakeHuman skin textures (all 2048², checked: `young_caucasian_male`, `middleage_caucasian_male`, …) paint the feet softly with blurry toes.
* Rig `default` (`Morgan.Rig`, 163 bones): `lowerleg02.L` → `foot.L` (ankle (200.6, 0, 76.1) → midfoot (200.9, −67.8, 39.4)) → 14 toe bones per foot whose heads sit at the MTP/PIP/DIP joint cubes. Bone names are the deform vertex-group names; `cache/body/bones.json` lists every head and tail.
* MPFB targets touching the foot (`notes/mpfb_targets_and_assets.txt` §feet): `l/r-foot-scale-incr/decr`, `l/r-foot-scale-horiz/vert/depth-incr/decr`, `l/r-foot-trans-*`, `measure-ankle-circ-incr/decr`. There is no toe, arch, malleolus or nail target — those are scripted edits.
* MPFB's own skin node group `Human.body` exposes `Pore scale 2500`, `Pore strength 0.2`, `SSS strength 0.2`, `SSS radius scale 0.1`, radii (1, 0.2, 0.1), `Roughness 0.45`, `Clearcoat 0.1/0.3` — a useful sanity scale (2500 /m = 0.4 mm cells) but we replace it for the foot (§5).

### 4.1 Step 1 — Fit with MPFB targets (in S1 `body.base`, before the rig fit; §0 item 6)
Inputs: `Body.Mesh` at the S1 macro values and stature, the dimension targets of §3.1. Method: MPFB detail targets are shape keys, so every measured length is an exact linear function of their weights (spec 18 D3); `linmodel` builds that model from the keys and `optim`'s bounded linear least squares solves the four weights below at once against the §3.1 targets, measured with `measure.py`'s primitives (§8.2); the depsgraph confirms the result. The weights are written to `scripts/parts/p01/params.json` and S1 loads them (`TargetService.load_target`) with the other detail targets, both feet alike:
1. `l-foot-scale-incr` / `r-foot-scale-incr` for foot length 282 ± 1 (B 279.6: a small weight, ≈ 0.1).
2. `*-foot-scale-horiz-incr` for ball width 105 ± 1 (B 102.7).
3. `*-foot-scale-vert-decr` toward the dorsum heights of §3.1 (B 5–8 mm high; what the target cannot reach, §4.2 step 4 sculpts).
4. `measure-ankle-circ-incr` for the minimum ankle circumference 229 ± 4 (B 225; this also thickens the distal shin, which spec 03 owns above z 300, §10).
5. Re-ground: S1 puts the lowest body vertex on z = 0 after all its targets (`build_all.py`).
Result: the S2 body carries the foot targets and the rig is fitted to the joint cubes they move. The edits of §4.2–4.4 are then made by this part on a **new shape key** `Foot.Sculpt`: `obj.shape_key_add(from_mix=False)` (a copy of the basis), the sculpt deltas computed on the evaluated mix and written as `basis + delta` into `key.data[i].co` — a key made `from_mix=True` would carry the macro keys' deltas a second time while they stay active (once spec 04's full S1 bakes the MPFB keys into the basis, the two are the same). Topology never changes in §4.1–4.3.

### 4.2 Step 2 — Landmark sculpt by script (`scripts/lib/sculpt.py`)
Helper API (pure Python over `key.data`, numpy for speed):
* `soft_move(verts, centre, radius, vector, falloff='smooth')` — displaces vertices within `radius` of `centre` by `vector × f(d/radius)`, f = smoothstep (1 − t)² (3 − 2(1 − t))… i.e. the standard sculpt-brush falloff; `falloff='gauss'` is the Gaussian specs 03 and 04 use, `'sharp'` = (1 − t)³.
* `soft_inflate(verts, centre, radius, amount, falloff='smooth')` — along per-vertex normals (recomputed from the evaluated mesh).
* `flatten_to_plane(verts, mask, plane_z, blend)` — projects vertices with `mask` weight onto z = plane_z, weight-blended.
* `laplacian_smooth(bm, vert_subset, iterations, factor)` — `bmesh.ops.smooth_vert` restricted to a subset.
* Measuring is not here: sections, widths and girths come from spec 18's `measure.py` (`section`, `girth(kind='tape')`), which the part's `measure()` (§8.2) also uses.
Landmark positions are given in frame F (§3.2) and transformed into world with the foot's frame transform (pternion position and heading read from the mesh: pternion = body vertex with max y and z < 60 in the foot region); the same transform places the `Frame.Foot.L/R` Empties of §4.14.

Edits in order (both feet; amounts in mm, from the B column of §3.1; all masks are also stored as vertex groups `Foot.<Name>` for §5):
1. **Malleoli**: `soft_inflate` medial apex (−38, −73, 89) r = 16, +2.5; lateral apex (+38, −60, 76) r = 13, +2.5 (B bimalleolar 71.4 → 76); then `soft_move` the ring just below each apex inward 1.5 mm to create the under-malleolar hollow.
2. **Retro-malleolar grooves and Achilles**: `soft_move` (±22, +4, 90) r = 12 by (0, +1, 0)·(−4) i.e. 4 mm toward −Y… (the hollows between the malleoli and the tendon); `soft_inflate` along the tendon line (0, +2, 60…130) r = 9, +2 (the cord).
3. **Heel**: `soft_move` pternion neighbourhood so the most posterior point sits at z = 30 (B 45) with plan radius 26, widening the heel 3 each side (B 65.2 → 71; `measure.section` at z 10/20/30 to confirm 66 / 70 / 71 width); `soft_inflate` the calcaneal tuberosity (0, −6, 52) r = 12, +1.5.
4. **Dorsum lowering**: `soft_move` down by what §4.1's `foot-scale-vert` weight left (B before it: 5 / 7 / 8 too high at 50 / 60 / 70 % L) along a strip 60 mm wide, with r = 25 — then `laplacian_smooth` 2 iterations at 0.3 on the dorsum.
5. **Instep crest**: `soft_inflate` along the line (−12, −140, 62) → (−6, −95, 76) r = 10, +1.5.
6. **Navicular tuberosity** (−40, −120, 42) r = 8, +2.0; **5th MT base** (+50, −150, 18) r = 6, +2.5 (sharper: falloff 'sharp' = (1 − t)³); **peroneal tubercle** (+36, −60, 22) r = 5, +1.0.
7. **Arch**: `flatten_to_plane` the lateral border 45–60 % L to z = 4 with blend 0.7 (fixes the lifted MPFB lateral midfoot, B ≈ 37); lower the medial arch toward 13 ± 2 at 45 % L (B ≈ 22 at 50 %), verified with `measure.section`.
8. **Ball**: `soft_inflate` 1st MT head medial (−52, −210, 22) r = 14, +2; `soft_move` the MT-head line back so the 1st head sits 210 from the pternion (B ≈ 216) and the 5th at 185 (B 203: (0, +18, 0) r = 18, and lateral +2), the toes travelling with their heads; recheck ball width 105 and ball-of-foot length 210.
9. **Tendons and veins — not sculpted here**: they are proximity attributes from curves (4.5) and become bump in the shader, which keeps the base mesh clean for subdivision.
10. **Smoothing pass**: `laplacian_smooth` 1 iteration at 0.2 over the whole foot except toes, nails and the landmarks (mask inverted) to remove any faceting introduced above.

### 4.3 Step 3 — Toe corrections (same helpers, per toe, in the toe's own axis frame built from the MTP → tip bone line)
1. **Lengths**, set by tip positions rather than fixed deltas: after step 8 of §4.2, move each toe's distal vertices along the toe axis (r = 25 falloff from the tip) until its tip lies at its §3.3 fraction of L = 282 (100 / 98.5 / 95 / 90.5 / 83 %; B before §4.2: 100 / 100 / 96.2 / 90.4 / 85.8 %); right foot toe 2 an extra −1.5 (asymmetry).
2. **Widths/heights**: scale cross-sections about the toe axis to the §3.3 maxima (hallux 26 wide × 22 high at the IP; measured with `measure.section` perpendicular to the toe axis at the IP and at 60 % of the distal phalanx); MPFB toes are near these — expect ±1 mm nudges.
3. **Joint definition**: `soft_inflate` each IP/PIP knuckle dorsally +0.8 (hallux +1.2), r = 5; `soft_move` the skin just distal of each knuckle down −0.4 (the dorsal wrinkle zone).
4. **Pulp shape**: `soft_inflate` the plantar pulp of each toe +1.0 (hallux +1.5) with the centre 3 mm behind the tip and 2 mm below the axis; flatten the plantar pulp of the hallux to z = 2 over 10 × 8 mm (it touches the floor when standing; the `Foot.Contact` key brings it to 0).
5. **Axes**: rotate toe vertices about the MTP: hallux 8° lateral (left 10°, right 7°); toe 4 roll 10°; toe 5 yaw 12° medial + roll 35° (left 40°) using a rigid rotation with r falloff only at the MTP ring (`soft_rotate(verts, pivot, axis, angle, mask)`). After this, check the 4–5 and 3–4 gaps ≥ 1.0 mm (toes must not intersect in rest).
6. **Nail bed preparation**: for each nail (the faces whose vertices all lie in the `toenails` group, split by toe through the toe groups), scale the nail-face patch in its own plane to the §3.3 width × length (hallux ×0.85 along the toe; toe 4 ×1.25; toe 5 to 7 × 6), then sink the patch 0.4 mm below the surrounding skin and raise the surrounding one-ring loop 0.4 mm proximally and 0.3 mm laterally (the eponychium and lateral folds). Store the nail patches as vertex groups `Foot.NailBed.<toe>`.

### 4.4 Step 4 — Nail plates: `Foot.L.Nail.1 … .5`, `Foot.R.Nail.1 … .5`
For each nail: `bmesh.ops.duplicate` the 20 nail-bed faces into a new mesh object; move it 0.35 mm along the nail normal (so the plate sits in the sunk bed, flush proximally); **extend the free edge**: `bmesh.ops.extrude_edge_only` on the distal boundary edge loop, translate the new loop by the free-edge length (§3.3: 1.5 mm hallux) along the toe axis and −0.3 mm in z (nails curve slightly down), then a second small extrusion of 0.3 mm with corner vertices pulled in 0.5 mm (rounded corners of a straight-cut nail). Add modifiers in this order: `Solidify` (thickness = §3.3 plate thickness, offset +1 so the bed face stays put, `use_rim` on, rim material = free-edge material, `use_even_offset`), `Bevel` (0.25 mm, 2 segments, angle limit 40° — rounds the free edge), `Subdivision` (levels 2, render 3). Give the proximal 2.5 mm of the plate a slight downward tilt (−0.3 mm) so it disappears under the eponychium ridge made in 4.3.6. Shade smooth; auto-smooth not needed (Blender 4.5 uses the `Smooth by Angle` modifier if desired — not required here). Parent: `Armature` modifier copying the body's deform groups is unnecessary — the plate rides a single bone: `obj.parent = rig; obj.parent_type = 'BONE'; obj.parent_bone = 'toe1-2.L'` etc. (distal phalanx bone), with the inverse matrix set so it stays in place. Poly budget: ≈ 60 base faces → 1k faces per nail at render subdivision.

### 4.5 Step 5 — Tendon, vein and crease guide curves → proximity attributes
Create Bezier curve objects (`bpy.data.curves.new(type='CURVE')`, 3D, bevel 0) from the polylines in §3.2 and §3.4: `Foot.L.Guide.Tendon.EHL`, `.Tendon.EDL.2…5`, `.Tendon.TA`, `.Vein.Arch`, `.Vein.Trib.1/2`, `.Vein.Saphenous`, `.Crease.Ankle`, `.Crease.Ankle.fine.1/2`, `.Crease.Ball`, `.Crease.Toe.<n>.<ip|pip|dip>` (dorsal and plantar), `.Crease.Heel.rim`. Then a **Geometry Nodes modifier** `Foot.GN.Proximity` on each closeup copy `Foot.<S>.Isolate` (§8.1), after the copy's level-3 subdivision is applied — not on `Body.Mesh`, which has shape keys (so `modifier_apply` refuses it) and vertices 5 mm apart (too coarse for a 0.8 mm crease band); the copy has neither problem (≈ 0.6 mm spacing). The group writes `Store Named Attribute` nodes: for each guide family, `Geometry Proximity` (target = joined curves, resampled to 1 mm) → distance → `Map Range` to a 0–1 band (tendon half-width 2.5 mm, vein 2 mm, crease 0.8 mm) → `Store Named Attribute` (float, point domain) as `Foot.Tendon`, `Foot.Vein`, `Foot.Crease`. The modifier is applied (`bpy.ops.object.modifier_apply` under a temp override) so the attributes become static mesh data that the shader reads with an `Attribute` node; the guide curves are moved to a hidden collection `Foot.Guides` and also parented to `foot.L`/toe bones for posing (not needed once applied; kept for rebuilds). Veins: additionally snap the curve to the surface + 0.5 mm (Shrinkwrap modifier on the curve, applied) so the proximity band is a thin surface ribbon.

### 4.6 Step 6 — Masks as vertex groups (functions of position/landmarks, written per vertex)
`Foot.Region` (the foot's faces below the MakeHuman ankle seam ring at z ≈ 130, one group for both feet; the material assignment and the closeup copies use it), `Foot.Callus.Heel`, `Foot.Callus.Ball`, `Foot.Callus.MTP5`, `Foot.Callus.Hallux`, `Foot.Corn.L4` (left only), `Foot.Rub.Achilles`, `Foot.Sole` (plantar: normal·(0,0,−1) > 0.5 and z < 12, feathered 6 mm), `Foot.Pressure` (heel centre ellipse + ball ellipse + toe pads), `Foot.ToeRed` (distal 60 % of each toe, 1.0 at the tips), `Foot.DorsumThin` (dorsum and ankle above z 20 excluding toes), `Foot.HairDensity` (§6), `Foot.SSSScale` (0.65 on the toes and the hallux to limit glow, 1.0 elsewhere, 0.7 on the sole), `Foot.ContactZone` (plantar vertices for the shape key), `Foot.PlantarContact` (z < 4 mm). Each mask is the smoothstep of a signed distance to the shapes in §3.4 with the feathers stated there. These groups double as bake sources (§5.6).

### 4.7 Step 7 — Shape key `Foot.Contact` (weight bearing)
On a copy of the evaluated coordinates: for vertices in `Foot.PlantarContact`, set z = 0 with `flatten_to_plane` blend = weight; `soft_inflate` the heel pad rim (ring at z 3–12 around the heel ellipse) outward +3.5; `soft_move` the medial arch 35–55 % L down 2.5 with r = 20; `soft_inflate` the ball rim +1.5; `soft_move` all toe tips −2 mm in y (lengthening). Store as shape key `Foot.Contact` (value set per foot in the pose: right 1.0, left 0.85). Heel pad vertical compression 4 mm is achieved because the rest heel pad is built 19 mm thick (pternion z 30, pad centre z −? — the rest sole is already at z 0; compression is expressed as the rim spread + flattened contact patch, which is what is visible).

### 4.8 Step 8 — Topology and subdivision
Keep the MakeHuman topology (all quads, loops already around each toe and across each joint — verified: the hallux distal has ≈ 11–16 vertices per 5 mm ring band). The body's own `Subdivision` (spec 03: viewport 1, render 2) is not this part's to change. The closeups render the `Foot.<S>.Isolate` copies (§8.1), whose `Subdivision` is Catmull–Clark render **3** (`use_limit_surface` on, `quality 4`; 1,095 → 70k quads per foot) so micro bump has geometry under it; in the hero frame the foot is inside a boot and level 2 is plenty. Micro-relief is **shader bump, not displacement** (§5.3); adaptive displacement is a documented fallback (§9). Nails 4.4; guide curves have no render geometry.

### 4.9 Step 9 — UV: give the feet their own tiles (only for the bake fallback of §5.6)
MakeHuman's `UVMap` is never edited (spec 16 §5.1; other parts' masks use it). If the fallback is needed, the tiles below are built in a second UV layer `Foot.UV` on `Body.Mesh` (under the part's prefix, so `replace.body_layer` removes it on a re-run), and "the existing islands" means that layer's copy of them. Using bmesh UV layer access: for the left-foot faces (all faces with every vertex in the foot region and in `body`) scale their existing two islands uniformly by **5.6** about their bbox centre and translate them into UDIM tile **1002** (u 1–2, v 0–1), packed side by side (dorsal island left, plantar island right; the islands keep MakeHuman's seams: one along the lateral border and one around the ankle ring at z ≈ 130 — the ankle seam is where the foot material blends into the body material, §5.5). Right foot → tile **1003**. Resulting density ≈ 120 px/cm (1.2 px/mm) at 4096² per tile, covering ≈ 55 % of the tile. The body skin material uses a UDIM image (`bpy.data.images.new` with `tiled=True`, `tiles.new(1002)`, `tiles.new(1003)`), or — simpler and chosen — the foot faces are assigned a **separate material slot** `Body.Mat.Skin.Foot` whose image nodes use plain 4096² images while their UVs live in the 1–2 range (image textures with `extension='REPEAT'` wrap the 1002 tile onto 0–1 transparently). The body material's UVs for all other faces are untouched.

### 4.10 Step 10 — Sock target proxy `Foot.L.SockTarget` (hidden)
Duplicate the evaluated foot + shin up to z = 300 into a new mesh (`Body.Mesh` evaluated via `evaluated_get(depsgraph).to_mesh()` restricted to the region), join the nail plates, then: `Remesh` (VOXEL, voxel size 2.5 mm) → `Smooth` (factor 1.0, 12 iterations, this fills the toe gaps the way a sock bridges them) → `Shrinkwrap` back to the original foot with `offset = 0` and `wrap_mode = 'OUTSIDE'` (so the proxy never sinks below the skin) → apply all. This is the surface the sock wraps; it is also the start of the **last** (4.13).

### 4.11 Step 11 — The sock `Sock.L.Body`
1. Base tube: `bmesh.ops.create_cone` (`segments 64`, radius 60 mm, depth 400 mm) is not a good start because of the right-angle turn at the heel; instead build an **L-shaped tube by lofting** 48 cross-section rings (circles of 48 vertices) along a centreline polyline: from the cuff (0, −40, 262) down the shin to the ankle (0, −50, 90), bending through the heel (0, −30, 45) and forward along the foot axis to the toe tips (0, −282, 12), with ring radii tapering 42 → 32 (ankle) → 45 (heel/instep) → 24 (toes), and a closed toe: cap the last ring with a fan to a centre vertex, then `bmesh.ops.triangulate`-free alternative — use a grid-fill cap (`bmesh.ops.grid_fill` after bisecting the last ring into two halves) to keep quads. Result ≈ 48 × 48 = 2.3k quads + cap.
2. `Shrinkwrap` to `Foot.L.SockTarget`, `wrap_method='NEAREST_SURFACEPOINT'`, `offset = 0.3 mm`, `wrap_mode='OUTSIDE'`; `Smooth` (0.5, 3 it); `Shrinkwrap` again (offset 0.3) — two passes stop the first pass's stretching; apply both so the base sock is static geometry hugging the socked foot.
3. Cuff welt: select the top 32 mm, `Solidify` is global so instead scale the cuff ring radii +1.5 % and add a second inward lip: extrude the top edge loop down 32 mm inside (the folded welt) — i.e. the cuff is double-layered geometry, which gives the visible rolled top edge (§8.3 failure mode "painted sock").
4. Vertex groups on the sock: `sock_cuff` (z > 228), `sock_leg` (90–228), `sock_heel` (Y-gore region: within 55 mm of the pternion along the gore arms, defined by two planes at ±45° through the pternion), `sock_toe` (y < −232 and the strip to the toe seam), `sock_sole` (normal·(0,0,−1) > 0.4), `sock_thickness` (factor: cuff 1.2, leg 0.8, heel 1.1, toe 1.1, sole 1.5 unloaded → the loaded factor 0.9 is used in the posed build), `sock_seam` (a 1.5 mm band along the toe-seam polyline from §3.6 via curve proximity, same GN trick as 4.5), `sock_grime`.
5. Modifiers (in order): `Armature` (weights transferred, §7) → `Shrinkwrap` to `Body.Mesh` (`OUTSIDE`, offset 1.0 mm — safety against skin poke-through after posing) → `Corrective Smooth` (factor 0.5, 5 it, `use_pin_boundary`) → `Solidify` (thickness **2.0 mm**, offset +1 outward, `vertex_group='sock_thickness'`, `thickness_vertex_group=0.0` so the factor scales fully, rim on) → `Subdivision` (viewport 1, render 2) → `Displace` (texture: procedural rib/knit baked into an image per §5.4, strength 0.6 mm, midlevel 0.5, direction NORMAL, UV coordinates) — the displace sits after the subdivision so the rib is real geometry at the silhouette.
6. UV for the sock: cylindrical unwrap along the centreline (`bmesh` computed: u = ring angle / 2π, v = arclength / total) so the knit's wales run along the sock and courses around it; aspect scaled so 1 UV unit in u = circumference (≈ 260 mm) and the knit texture repeats 260/1.6 ≈ 160 wales around (set per material via `Mapping` scale), see §5.4.
7. Poly budget: base 2.4k quads → solidified 4.8k + rims → render subdivision 2 → ≈ 77k faces per sock. Acceptable.

### 4.12 Step 12 — Hair emitters
No emitter geometry: the hair Curves `Foot.L.Hair` and `Foot.R.Hair` (§6.1, built only with `--hair`) are rooted on `Body.Mesh` by `Foot.HairDensity`. For the `sock` and `boot` build variants the density is multiplied by 0 above z = 15 mm (hair under the sock is invisible and only costs render time).

### 4.13 Step 13 — The last `Foot.L.Last` (interface object for the boot part)
From `Sock.L.Body` on the **rest** foot (toes flat, `Foot.Contact` at the loaded 1.0, the sock at its loaded thickness; §0 item 3): duplicate, `Smooth` (1.0, 6 it), then offset outward by allowance via `Shrinkwrap OUTSIDE` from the sock surface with a per-region offset implemented as `Displace` along normals with a vertex-group factor: toe box +15 mm in length (toe tips region; real boots leave 15–22, `research_dimensions.md` §2), +4 mm at the ball width, +2 mm over the instep, +1 mm at the heel sides, 0 at the heel back and sole (the insole plane is the sole). Length: 282 + 15 = 297, as spec 02 §3.1 takes it. Add toe spring: rotate the forefoot region (y < −210) about the MT-head line by 12° upward (the boot last's toe spring) with a 30 mm blend; the pose extends the toes by the same 12° (§7.3), so the foot follows its insole. Export as a hidden mesh object with the vertex groups `last_heel`, `last_ball`, `last_toe`, `last_instep`, `last_collar` (ring at z 210) and the marker empties `Foot.L.Last.Pternion`, `.Ball1`, `.Ball5`, `.ToeTip`, `.AnkleAxis.Medial/.Lateral`. `.Pternion`, `.Ball1` and `.Ball5` lie on the insole plane (z 0 of the last): they are the three sole points spec 08 §4.7(e) aligns to spec 02's footbed. The boot part shrinkwraps its liner to this and must never cut inside it (§10). The marker positions and the toe-joint positions of §3.3 (world mm, rest) are also published as `foot.L.*` / `foot.R.*` keys in `assets/interfaces.json` (spec 18 §4.3) for spec 08's rig fit.

### 4.14 Naming and collections
The part's declaration (spec 18 §4.4): `Part(id="01", name="foot_ankle_sock", prefixes=("Foot.", "Sock.", "Frame.Foot."), keys=("foot.", "sock."), needs={"08": "Morgan.Rig"}, provides=("Foot.L.Last", "Foot.R.Last", "Frame.Foot.L", "Frame.Foot.R"), presets="p01")`; it starts from `cache/body/rigged.blend` (S1–S2). Collection `Part01.FootAnkleSock` (the CLI's default) holding `Frame.Foot.L`, `Frame.Foot.R` (frame F Empties for spec 17's presets) and the child collections `Foot.Nails` (`Foot.L.Nail.1–5`, `Foot.R.Nail.1–5`), `Foot.Lasts` (hidden: `Foot.L.SockTarget`, `Foot.R.SockTarget`, `Foot.L.Last`, `Foot.R.Last` and the markers), `Foot.Guides` (hidden curves) and `Sock.Pair` (`Sock.L.Body`, `Sock.R.Body`); `Foot.L.Hair`, `Foot.R.Hair` with `--hair`. The closeup copies `Foot.<S>.Isolate` are made after the cache is saved and never enter it (§8.1). The foot skin itself is faces of `Body.Mesh` with material `Body.Mat.Skin.Foot`, vertex groups and attributes named `Foot.*`, shape keys `Foot.Sculpt` and `Foot.Contact`. Materials (spec 16 §7.1): `Body.Mat.Skin.Foot`, `Foot.Mat.Nail.Plate`, `Foot.Mat.Nail.FreeEdge`, `Body.Mat.Hair.Body`, `Sock.Mat.Knit.Sock.WoolNylon`, `Sock.Mat.Knit.Sock.WoolNylon.Reinforced`. Images: `Foot.L.Img.Masks` 4096² (if baked), `Sock.C.Img.RibDisp` 2048².

---

## 5. Materials and textures

**Spec 16's library supersedes the values of this section** (§0 item 7): the part assigns its materials by recipe through `lib/materials.py` (`M.assign(body, "Skin.Foot", part="Body", faces="Foot.Region")`, `"Nail.Plate"`, `"Nail.FreeEdge"`, `"Knit.Sock.WoolNylon"` and its `.Reinforced`, `"Hair.Body"`) and sets no Principled socket itself (spec 16 §7.3). What follows is the regional data the library takes from this part (spec 16 §3.3.1: "regional data owned by specs 01, 03–06"), already corrected where spec 16 resolved a conflict. Until the library exists the foot is judged on `form` renders, with a placeholder skin for any Cycles look.

Texture coordinates: `Object` coordinates in metres for every procedural layer (so a `Scale` of 2500 = 0.4 mm cells, like MPFB's pore scale); UVs only for the baked masks and the sock knit. All colours are albedo (sRGB hex, converted to linear by the colour picker — do not set them as linear).

### 5.1 `Body.Mat.Skin.Foot` (recipe `Skin.Foot` on `MG.Skin.Core`) — regional values
| Input | Dorsum / ankle (`Foot.DorsumThin`) | Sole (`Foot.Sole`) | Callus (`Foot.Callus.*`) | Toes (`Foot.ToeRed`) |
|---|---|---|---|---|
| Base Color | #b6886f × colour variation (5.2) | #d8b798 → pressure #d9a48e by `Foot.Pressure` | #e0cba8 (edge #c9ad8a), fissures #b89a7e | mix 60 % toward #c48474 at the tips |
| Subsurface Weight | 1.0 | 1.0 | 0.8 | 1.0 |
| Subsurface Method | Random Walk (Skin) | same | same | same |
| Subsurface Radius (m, relative) | (1.0, 0.2, 0.1) (spec 16 C28 core) | (1.0, 0.45, 0.28) (thick, yellow scatter) | (1.0, 0.45, 0.28) (C28) | (1.0, 0.2, 0.1) (C28) |
| Subsurface Scale | **0.0032** × `Foot.SSSScale` attribute | 0.0022 | 0.0015 | 0.0032 × 0.65 (the attribute) |
| Subsurface IOR / Anisotropy | 1.4 / 0.8 | 1.4 / 0.8 | 1.4 / 0.8 | 1.4 / 0.8 |
| Roughness | 0.42 ± 0.08 (noise, 3 mm) | 0.52 | 0.72 | 0.45 |
| IOR | 1.40 | 1.40 | 1.42 | 1.40 |
| Specular IOR Level | 0.5 | 0.5 | 0.4 | 0.5 |
| Coat Weight / Roughness | 0.15 / 0.25 (skin oil) | 0.0 | 0.0 | 0.12 / 0.3 |
| Sheen Weight / Tint | 0.04 / white (peach fuzz; spec 16 C29) | 0 | 0 | 0.04 |
| Normal | bump chain 5.3 | bump chain 5.3 (plantar) | bump chain 5.3 + fissures | bump chain 5.3 |

Blend logic: a `Mix` cascade driven by `Attribute` nodes reading the vertex groups (type `Geometry` → `Attribute` with the group name; vertex-group weights are readable as attributes in Cycles). Order: dorsum base → sole (by `Foot.Sole`) → pressure → toes → callus (callus last, on top) → corn → rub patch (`Foot.Rub.Achilles` tint #a67a66 at 0.4).

### 5.2 Colour variation layers (procedural, added under the masks)
1. Blotch: `Noise` scale 180 (≈ 5–6 mm), detail 3, roughness 0.5 → `Color Ramp` ±6 % value, ±4 % saturation (redder in valleys) — mottling.
2. Fine mottle: `Noise` scale 900 (1 mm), ±3 % value.
3. Follicle dots on the dorsum: `Voronoi` F1 smallest-distance, scale 2200, threshold 0.08 → darken 8 % and redden 5 % (the follicle shadow) masked by `Foot.DorsumThin`.
4. Vein tint: `Attribute Foot.Vein` → mix 18 % #7d8b86 (spec 16 C29); also Subsurface Radius ×1.2 (veins look bluish because of depth scatter).
5. Tendon: no colour change (only bump), except 3 % lighter on the ridge crest.
6. Crease darkening: `Attribute Foot.Crease` → multiply colour by 0.92 and roughness +0.1.
7. Dust/dry whitening on callus: `Noise` scale 400 → 10 % mix toward #ece0cf inside the callus masks.
8. Nail bed faces (the `toenails` group's faces, under the plates) use `Body.Mat.Skin.Foot` with base #d49a88, a hyponychium gradient to #c99585 in the distal 2 mm, and SSS scale 0.002.

### 5.3 Micro-normal recipe (bump chain; each `Bump` node's `Distance` in metres, `Strength` 1.0, chained through `Normal`)
| Layer | Texture | Scale (/m) | Mask | Bump distance | Notes |
|---|---|---|---|---|---|
| A Macro undulation | `Noise` detail 2 | 60 | all | 0.00030 | 15 mm soft lumps — breaks the CG smoothness |
| B Polygonal skin network | `Voronoi` distance-to-edge, randomness 0.9 | 2400 (dorsum) / 3000 (toes) | not sole | 0.00004 | 0.3–0.5 mm cells; invert so lines are grooves |
| C Follicle pits | `Voronoi` F1 distance, scale 2200, `Less Than` 0.09 | 2200 | `Foot.DorsumThin` | 0.00006 | Ø 0.15 mm pits |
| D Friction ridges | `Wave` bands, direction from a `Noise`-distorted `Mapping` (distortion 2.5), band period 0.45 mm → scale ≈ 2200 (wave scale is period-based: `Scale` 2.2 with `Object` coords in mm… use `Scale` 2200 with phase distortion 3.0) | 2200 | `Foot.Sole` + toe pads | 0.00005 | whorls appear from the distortion; ridge density higher on the pads |
| E Heel crazing | `Voronoi` distance-to-edge, scale 350, `Less Than` 0.06 (crack width 0.4 mm) | 350 | `Foot.Callus.Heel` | 0.00030 (grooves) | polygon plates 2–5 mm |
| F Tendons | `Attribute Foot.Tendon` smoothed (`Map Range` smootherstep) | — | — | 0.0015 (EHL/TA), 0.0010 (EDL) | positive = ridge |
| G Veins | `Attribute Foot.Vein` | — | — | 0.0007 (saphenous 0.0010) | |
| H Creases | `Attribute Foot.Crease` | — | — | −0.0004 (ankle), −0.0008 (ball), −0.0002 (toe wrinkles) | negative = groove |
| I Toe dorsal wrinkles | `Wave` bands perpendicular to each toe axis, period 1.0 mm, within 4 mm of each IP/PIP | 1000 | `Foot.Crease` toe bands | 0.00015 | 3–6 lines per joint |
| J Nail-plate ridges (nail material) | `Wave` along the toe axis, period 0.25 mm (spec 16 `Nail.Plate`) | 4000 | nail objects | 0.00001 | plus a 0.0002 transverse ridge on the right hallux (asymmetry) |

Scale note: Blender's `Bump Distance` is in object units; these are metres, so 0.00004 = 0.04 mm. The closeup copies keep `Subdivision` render level 3 (§4.8) so shading normals have geometry support; otherwise bump at 0.3 mm cells on 1,095 faces shows faceting at the silhouette.

### 5.4 Sock materials
`Sock.Mat.Knit.Sock.WoolNylon` (leg, cuff, sole outside) and `Sock.Mat.Knit.Sock.WoolNylon.Reinforced` (heel pocket, toe cap) — spec 16's recipe `Knit.Sock.WoolNylon` and its `.Reinforced`, same tree, different colour and gloss:

| Input | Body | Reinforced heel/toe |
|---|---|---|
| Base Color | #5a4b3a × yarn variation (`Noise` scale 3000, ±8 % value, 2 % hue) × grime (`foot`-style mask `sock_grime` → mix 50 % #4b4035 on the sole, 30 % heel) | #33302c × variation; nylon sheen |
| Roughness | 0.80 | 0.65 |
| Sheen Weight / Roughness / Tint | 0.08 / 0.5 / #8a7a66 (wool fuzz; spec 16 C1: above 0.08 a dark fabric's colour depends on the light) | 0.06 / 0.4 / #6a6660 |
| Subsurface | weight 0.3, radius (1, 0.8, 0.6), scale 0.001 | 0.15 |
| Normal | knit normal: Poly Haven `knitted_fleece_nor_gl_2k.jpg` (`assets/textures/knitted_fleece`), tiled at **230 mm** per repeat, which spec 16 measured (C34, §3.2) to give the 1.6 mm stitch (strength 0.6) + procedural stitch V's: `Brick` texture (brick width 1.6 mm, height 1.2 mm, offset 0.5, mortar 0.2 mm) → bump distance 0.00015 | same, mortar 0.15, smoother |
| Displacement (modifier image `Sock.C.Img.RibDisp`, baked from a procedural tree once per build) | leg: 2×2 rib — `Wave` bands around the circumference, period 7.5 mm (≈ 35 periods around a 260 mm circumference → `Scale` set so 35 repeats per u unit), amplitude 1.0 → Displace strength 0.6 mm; cuff: 1×1 rib period 3.6 mm, strength 0.4 mm; foot: 0 except the 3 mm arch band (1×1 rib, strength 0.3); toe seam `sock_seam` +1.0 mm ridge | none |
| Alpha / fuzz | optional: `Sock.L.Fuzz` particle hair, 0.4 mm long, 2,000 per sock, radius 0.01 mm, colour = body, only for V7 renders | — |
| Pilling | `Voronoi` F1 scale 600, `Less Than` 0.08 on `sock_sole` → bump +0.0004 and colour +5 % | — |

### 5.5 Seams and blending with neighbours
* The `Body.Mat.Skin.Foot` / `Body.Mat.Skin.Body` boundary is the MakeHuman ankle UV seam ring at z ≈ 130 mm. Both materials build on spec 16's `MG.Skin.Core` (C27), so they agree in base colour, roughness and SSS at the seam by construction; `Body.Mat.Skin.Foot` fades its own layers in with `Map Range` of z from 170 → 120 mm (1 at the foot, 0 at the shin).
* Nail plates meet the skin at the folds: the fold ridge (4.3.6) overlaps the plate by 1.5 mm — no visible gap in V5.
* Hair material: spec 16's `Hair.Body` (C32), one recipe for all the body hair: `Principled Hair BSDF` (Chiang), Melanin 0.75 (tip × 0.8), Melanin Redness 0.5, Roughness 0.35, Radial Roughness 0.3, Coat 0.05, Random Color 0.15; 4 % of strands grey (melanin 0.10).

### 5.6 Baking (optional performance path)
If the attribute-driven tree renders too slowly (on the GPU it is a matter of seconds, §8.1, so this is unlikely), bake the masks and the colour layers once per build into `Foot.L.Img.Masks` 4096² images on the `Foot.UV` tiles of §4.9 with `materials.bake_masks()` (spec 16 §5.3), then rebuild `Body.Mat.Skin.Foot` as an image-driven tree. Micro-normal layers stay procedural (texel density 1.2 px/mm is below the 0.3 mm cell size). The export's own bake is spec 16 §5.4's and needs none of this.

### 5.7 Texel density summary
| Surface | Approach | Effective detail |
|---|---|---|
| Foot skin colour | attributes + procedural (bake fallback 1.2 px/mm) | 0.4 mm macro features |
| Foot micro-normal | procedural, object space | 0.3 mm cells, 0.15 mm pits |
| Nails | procedural | 0.01 mm ridges at 0.25 mm pitch |
| Sock | knit image at 230 mm repeat (2048 px → 0.11 mm/px) + procedural brick | 1.6 mm stitches resolved with ≈ 14 px each |

---

## 6. Fibres, simulation or dynamics

### 6.1 Hair (terminal hair of the foot)
Built only with `--hair`, like the leg and trunk hair of specs 03 §4.10 and 04 §4.10, and with their method (§0 item 13): **hair Curves** objects `Foot.L.Hair` and `Foot.R.Hair` rooted on `Body.Mesh` (spec 07's `groom.py` helpers; Blender's procedural hair node assets), material `Hair.Body`; the counts, lengths, radii, density and direction below hold for either method. The legacy particle system described next is the **fallback**. Fallback: legacy particle hair on `Body.Mesh` (scriptable without UI: `mod = obj.modifiers.new('Foot.Hair', 'PARTICLE_SYSTEM')`, `ps = mod.particle_system; st = ps.settings`), one system per foot:
* `type='HAIR'`, `count` = **260** (both dorsum ≈ 125 + hallux tuft 10 + toes 2–4 3 each + 5th 1, times 2 feet… use one system per foot with count 130), `hair_length` 0.009 m, `emit_from='FACE'`, `use_emit_random` on, `vertex_group_density='Foot.HairDensity'` (painted per §3.4: 1.0 dorsum centre 20–55 % L, 0.4 at the ankle, 0 on the sole, tuft patches 1.0 on the proximal phalanges, 0 elsewhere), `vertex_group_length='Foot.HairLength'` (1.0 dorsum, 0.7 hallux, 0.5 toes 2–4, 0.3 toe 5), `hair_step 5`, `use_hair_bspline` on, `brownian_factor 0`, `child_type='NONE'` (explicit strands only — children make tufts look uniform), `root_radius` via `obj.data... ` — Cycles hair radius is set on the object: `ob.cycles_curves` is global; use `st.radius_scale = 0.0035` with `root_radius 1.0`, `tip_radius 0.5`, shape 0 → root Ø 0.07 mm, tip 0.035 mm; `use_close_tip` on. Direction: `normal_factor 0.3`, `tangent_factor 0.9`, `tangent_phase` random 0.2 and an `object_align_factor` of (0, −0.8, −0.3) so strands lie toward the toes (frame F) — set per foot in world axes after accounting for the rest heading. `kink='CURL'`, `kink_amplitude 0.0008`, `kink_frequency 1.5` for a slight bend. Seed differs per foot.
* The primary method's assets: Blender 4.5's bundled `datafiles/assets/geometry_nodes/procedural_hair_node_assets.blend` under the Blender install (groups such as *Generate Hair Curves*, *Hair Curves Noise*, *Set Hair Curve Profile*, *Trim Hair Curves*, appended with `bpy.data.libraries.load`; path found from `bpy.utils.system_resource('DATAFILES')`, not hard-coded). Hair curves give better root placement control (a density attribute) and are the method of the scalp (spec 07) and the body (specs 03, 04).
* Render: Cycles `scene.cycles.hair_shape='ROUND_RIBBONS'` → use `'ROUND'`-style 3D curves (`Curve subdivisions 3`) for closeups.

### 6.2 Cloth
**None required.** The sock is geometric (shrinkwrap + solidify + displace). Optional: a 24-frame cloth settle of the cuff only (pinned below z 230, quality 8, mass 0.1, stiffness tension 15 / compression 15 / shear 5 / bending 0.5, collision with `Body.Mesh` distance 1 mm) to slouch the welt — only for V7; never in the hero build.

### 6.3 Soft-body / dynamics
None. Weight bearing is the `Foot.Contact` shape key (§4.7).

---

## 7. Rigging and attachment

### 7.1 Bones (names are the MPFB `default` rig names so weights import directly; the rig part owns the controls)
| Bone | Head → tail (left, frame F → world via the foot transform) | Deforms | Purpose |
|---|---|---|---|
| `lowerleg02.L` | shin to the ankle axis centre (0, −68, 80) | yes | both malleoli stay with this bone |
| `foot.L` | (0, −68, 80) → (0, −140, 40) | yes | talus + calcaneus + midfoot; plantar/dorsiflexion and inversion/eversion |
| `toe1-1.L`, `toe1-2.L` | MTP (−40, −210, 25) → IP (−42, −251, 22) → tip (−45, −282, 10) | yes | hallux |
| `toeN-1/2/3.L` (N = 2…5) | MTP → PIP → DIP → tip per §3.3 | yes | lesser toes |
| `heel.L` (new, non-deform) | pternion floor (0, 0, 0) → +Y 20, i.e. (0, +20, 0) (spec 08 §4.2) | no | IK pivot / foot roll for the rig part |
| `toes_master.L` (new, non-deform) | (−40, −210, 25) → (+42, −185, 18) along the MT-head line | no | drives all `toeN-1.L` with `Copy Rotation` (local, 1.0) for the toe-spring pose |
| `ball.L` (new, non-deform marker) | 1st MT head medial point → +X 20 (spec 08 §4.2) | no | measurement/attachment for the last |
This part does not edit `Morgan.Rig` (§0 item 6). It publishes the joint positions after its sculpt — the §3.3 table (with the §3.2 forefoot scaling) transformed to world, rest pose, mm — as `foot.L.joint.<bone>.head` / `.tail` (and `.R`) keys in `assets/interfaces.json`, together with the `heel`, `ball` and `toes_master` positions; spec 08's S2 reads them, moves the foot and toe bones there, adds the three new bones and gives them its canonical rolls (spec 08 §4.3). Until the keys exist S2 uses MPFB's joint cubes, and publishing them marks S2 stale (spec 18 §4.3, `interfaces.py`), so one more S2 run closes the loop.

### 7.2 Weights (vertex groups on `Body.Mesh`; start from MPFB `import_weights=True`, then overwrite the foot region by rule, then `bpy.ops.object.vertex_group_smooth` 2 iterations at 0.5 restricted to the foot)
| Ring / region | `lowerleg02.L` | `foot.L` | toe bones |
|---|---|---|---|
| z ≥ 120 (shin) | 1.0 | 0 | 0 |
| z 100 | 0.90 | 0.10 | 0 |
| z 85 (through the ankle axis) | 0.60 | 0.40 | 0 |
| **malleoli apex regions** (r 16 / 13) | **0.85** | 0.15 | 0 |
| z 70 (below the axis, front and back) | 0.25 | 0.75 | 0 |
| Achilles cord z 60–100 | 0.5 → 0.1 (linear down) | 0.5 → 0.9 | 0 |
| z ≤ 55, heel, midfoot | 0 | 1.0 | 0 |
| MT shafts 60–70 % L | 0 | 1.0 | 0 |
| MTP ring (±6 mm around each MTP) | 0 | 0.5 | `toeN-1` 0.5 |
| proximal phalanx | 0 | 0 | `toeN-1` 1.0 |
| PIP ring | 0 | 0 | `toeN-1` 0.5 / `toeN-2` 0.5 |
| middle phalanx / DIP ring / distal | 0 | 0 | 1.0 / 0.5–0.5 / `toeN-3` 1.0 (hallux: `toe1-2` 1.0 distal of the IP ring) |
| Toe webs | 0 | 0.3 | adjacent `toeN-1` 0.35 each |
| Nail plates | parented to the distal bone (§4.4) | | |
Normalise all groups to 1.0 per vertex (`bpy.ops.object.vertex_group_normalize_all` with `lock_active=False`).

### 7.3 Pose of this part in the hero frame (spec 08 owns these values, §4.6–4.7; repeated so the foot build can self-test)
| Bone | Right foot | Left foot |
|---|---|---|
| `foot.*` placement (world) | ankle centre at (−208, +75) in plan; heading: toes toward −X, **85°** from −Y toward his right (spec 08 D3; this spec first said 90°); eversion 0 inside the boot (spec 08 §4.6: 3° barefoot) | ankle centre at (+208, −75) in plan; toes **17°** toward +X from −Y (spec 08 §4.6; first 15°) |
| `foot.*` on the footbed (§0 item 4) | the last's sole markers on spec 02's footbed: plantar flexion 5.4° about the ball line, ball seat h 29, heel seat h 49 (spec 02 §4.1 step 2, §7.2) → ankle axis at h ≈ 122 (80 barefoot) | same |
| `toes_master.*` | extension 12° (the last's toe spring, §4.13) | extension 12° |
| `toeN-2/3` | flexion 2° | flexion 2° |
| toes 2–5 adduction (toe box) | 2° each toward toe 2; toe 5 roll +5° | same |
| `Foot.Contact` | 1.0 (55 % load; spec 08 `Hero.Weight.R` 0.55) | 0.85 (45 % load) |
Check: the right boot's medial side faces the camera (a right foot turned 85° to the right still shows its instep), per consolidated disputes #1. Spec 08 §4.6 and §4.7(e) set the toes to 0 and the soles on z = 0; a dated note there (2026-10-10) records that with the boots on the footbed governs, and Q7 asks Jeff about the ≈ 42 mm the figure gains.

### 7.4 Attachment of the sock and the last
* `Sock.L.Body`: `Data Transfer` modifier from `Body.Mesh` (vertex data: `VGROUP_WEIGHTS`, `NEAREST_POLYINTERPOLATED`, all deform groups), applied → the same `Armature` modifier (`rig`), followed by the safety `Shrinkwrap OUTSIDE` to `Body.Mesh` (offset 1.0 mm) and `Corrective Smooth` (§4.11.5). Collisions with the body are therefore impossible by construction; with the nails (which sit inside the sock target) the margin is ≥ 0.3 + 1.0 mm.
* `Foot.L.Last`: not deformed by the rig; built from the **rest** socked foot with its own 12° toe spring (§4.13, §0 item 3) and parented to `foot.L` with `parent_type='BONE'`, so it moves with the foot when the pose places it on spec 02's footbed; spec 02 pitches its own copy 5.4° to build the boot (spec 02 §4.1 step 2).
* Hair: the Curves follow `Body.Mesh` through their surface binding (the particle fallback deforms with the mesh automatically).
* Guide curves: parented to `foot.L`/toe bones (they are only needed before the proximity attributes are applied).

---

## 8. Evaluation protocol

### 8.1 Render sets (spec 17's `scripts/eval/render.py` through the part's `--render`; presets `scripts/eval/presets/p01.json`; outputs `renders/01_foot/<preset>_<tier>.png` with a JSON sidecar, the variant in the file stem)
* Look-dev scene (anatomy and material): spec 17's `LookDev` (§4.8 there: 18 % grey cyclorama, white key, fill and rim scaled to the subject, AgX Base Contrast). Until `lookdev.py` exists, `form` renders run in the hero scene (Workbench ignores the lights) and Cycles tiers need `--scene hero`.
* Hero colour: spec 17's `Hero` scene (key and cool lights, world, plain floor, AgX Medium High Contrast and the display grade), with the foot at its hero position; cameras V1–V5 re-aimed at the posed foot. Its nominal lights are 3–5 × too bright until calibration stage A (spec 17 §4.14), so colour judgements here wait for it; form, nails and sock construction do not.
* Tiers (spec 17 §4.9) instead of a fixed recipe: `form` (Workbench matcap) for every geometry iteration; `look` (16 spp, 50 %) for shader work; `eval` (64 spp, adaptive 0.02, OIDN high, 2048² for V1–V5) for critic packets; `final` (512 spp) for acceptance. On the RTX 3050 (OptiX, OIDN on the GPU) an `eval` hero frame takes 4 s and a warm `form` crop 0.03–0.1 s; a 2048² closeup with random-walk SSS and hair is expected at 10–60 s [measure on the first run].
* **One foot per closeup** (§0 item 9): after saving its cache the script makes `Foot.L.Isolate` and `Foot.R.Isolate` — `bpy.data.meshes.new_from_object` of the evaluated `Body.Mesh` (vertex groups kept), cut to that side's `Foot.Region` plus the shin to z 300, with `Subdivision` render 3 applied and the §4.5 attributes written — and the V1–V5 and V1o–V4o presets hide `Body.Mesh` and the other side's `Foot.*` and `Sock.*` objects; V6 hides the copies. The copies are never saved into the part cache or assembled.
* Variants: `bare` (skin + nails + hair, both feet, hanging and `Foot.Contact`), `sock` (+ sock), `boot` (+ last visualised as a semi-transparent shell, for V6); the script shows and hides its own objects per variant before each preset.
* Measurement renders: `p01.V1o`…`V4o`, V1–V4 repeated with an **orthographic** camera, `ortho_scale 0.32 m` (6.4 px/mm at 2048), Workbench flat shading, white background, so the PIL overlay can draw a 10 mm grid and measure the silhouette.

### 8.2 Automated metrics (the part's `measure()` in its own script, spec 18 D14; each item in spec 18's envelope `{part, metric, value, target, tol, unit, pass, source}`, printed on the RESULT line, written to `renders/01_foot/measure.json` and compared with §3)
Uses spec 18's `measure.py` primitives on the evaluated mesh with `Foot.Contact` at the stated value — `section` (plane sections), `girth(kind='tape')` (convex-hull perimeters: ANSUR's tape girths), `clearance` (gaps and penetration), `landmarks`: foot length; ball-of-foot length; ball width at the MT-head line; heel width at 15 % L and z 10/20/30; bimalleolar breadth (max x extent of the ring z 70–95); malleolus apex heights (max local protrusion along ±x in z 60–100); min ankle circumference; ball, instep and heel–ankle circumferences; dorsum height at 50/60/70 % L; medial and lateral clearance at 45/50 % L; per-toe tip y (from bone tails + 6 mm pulp, and from the mesh); per-toe width/height at the IP; nail plate width/length/thickness (from the nail objects' bounds and Solidify thickness); gap between adjacent toes (min distance between toe vertex sets, must be ≥ 1.0 mm in rest, may be 0 in the boot pose); hair count per region (particle positions binned by vertex-group weight); sock thickness at 6 probe points (ray casts normal to the sock through the Solidify shell); last-vs-reference check for V6: project `Foot.*.Last` with the hero camera and compare its silhouette with the boot silhouette mask of the reference (dark runs of §2.2 dilated by 5 px; the last plus boot allowances must be inside).

Tolerances: lengths ±3 mm, widths ±2 mm, heights ±2 mm, circumferences ±6 mm, nails ±1 mm (thickness ±0.2), toe tips ±2 mm, hair counts within the §3.4 ranges, sock thickness ±0.3 mm, V6 containment 100 % of silhouette pixels with ≤ 5 px excursions.

### 8.3 Critic questions (score 1–10 each; the part passes at ≥ 7 on every question and ≥ 8 average)
1. Does the dorsal view read as one specific man's left foot (and the other as his right), not a mirrored pair? Name the asymmetries you can see.
2. Toe order: is the hallux the longest, the 2nd slightly shorter, 3rd–5th descending, the 5th curled under? Are the toes individually shaped (joint knuckles, pulp bulge, wrinkles)?
3. Nails: ten plates with thickness at the free edge, nail fold rim, lunula on the hallux, pink bed through the plate, nails trimmed straight? Any floating/sunk/missing nail?
4. Callus: pale, rough, dry skin at the heel rim, the ball, the lateral 5th MTP and the medial hallux IP — and nowhere else? Does it read as skin, not dirt?
5. Sole vs dorsum colour: sole paler/yellower with pink pressure zones; toes and tips pinker; veins faintly grey-green and in relief?
6. Tendons and veins: visible as relief catching the rim light in V1/V2, not as drawn lines? EHL to the hallux, the fan to toes 2–5, the saphenous vein in front of the medial malleolus?
7. Malleoli: medial higher and rounder, lateral lower, pointed and further back? Achilles cord with hollows either side? Anterior ankle crease at the right height?
8. Hair: sparse dark terminal hairs on the dorsum, a tuft on each big toe, almost none on the little toes; thin (not wires), lying toward the toes?
9. Skin material: SSS believable (toe shadow sides still dark), micro-relief visible in V5 (cells, pits, ridges on the pads), no plastic highlight, no waxiness?
10. Weight bearing: in the `Foot.Contact` render is the heel pad spread and the contact patch flat? Does the hanging foot look relaxed (arch higher, heel rounder)?
11. Sock: visibly thick at the cuff, rolled welt, 1×1 cuff rib and 2×2 leg rib at the right pitch, smooth darker heel pocket with gore lines, darker toe cap with a linked seam ridge, stitch scale ≈ 1.6 mm, slight grime on the sole, no toe gaps or skin poking through?
12. V6: does the socked foot's envelope plus boot allowance, standing on spec 02's footbed, sit inside the reference boot silhouette on both feet, at the right heights (the foot's ankle crease at h ≈ 120 — the drawn break at 85–95 mm is the image's, §2.2 — collar 210 mm)?

### 8.4 Known failure modes to check for
Waxy/glowing toes (SSS scale too high on thin parts — the `Foot.SSSScale` attribute must be present); "sausage toes" with no knuckles; identical mirrored feet; nails flush with the skin or without a free edge; nail plates clipping through the eponychium; callus reading as grime because its roughness or colour is wrong; veins painted but not bumped; faceting at the silhouette (subdivision level too low for the bump scale); a visible colour/roughness step at the ankle material seam; hair strands too thick (radius > 0.05 mm) or too long (> 14 mm), hair on the sole, hair standing up like bristles; the sock looking painted (no thickness at the welt), knit too coarse ("chunky sweater", stitch > 2.5 mm) or too fine (invisible), rib pitch wrong, sock bridging toes with sharp creases (SockTarget not smooth enough), sock intersecting the skin after posing (safety Shrinkwrap missing), sock colour too saturated; the last cutting inside the reference boot silhouette (foot too big) or leaving > 8 mm slack (foot too small); the right foot rotated the wrong way (lateral side to the camera — wrong); toe spring not applied (toes flat inside a boot with a 12° last spring would intersect the insole).

---

## 9. Build order, effort and risks

### 9.1 Dependencies
* **Needs before start:** `Body.Mesh` and `Morgan.Rig` from `cache/body/rigged.blend` (`build_all.py` S1–S2: specs 03/04's macros, rest stature 1855, re-grounded and centred between the ankles, MPFB's `default` rig and weights; with §4.1's foot targets once `p01/params.json` holds them); spec 17's `render.py`, `camera.py`, `p01.json` and `LookDev` (soft: the hero scene until `LookDev` exists); spec 16's recipes `Skin.Foot`, `Nail.*`, `Knit.Sock.*`, `Hair.Body` (soft: a placeholder skin until the library exists); spec 18's `measure.py` primitives (and `linmodel`, `optim` for §4.1); spec 08's pose values (§7.3).
* **Provides to others:** `Foot.*.Last` + markers (boot part, spec 08's foot alignment), the `foot.*` joint and marker keys in `assets/interfaces.json` (spec 08's S2 places the toe bones and adds `heel`, `ball`, `toes_master` from them), the weight table (rig part), `Frame.Foot.L/R` (spec 17's presets), the sock top height 260 mm and thickness (trouser part — irrelevant visually but the hem fold simulation must collide with the boot, not the sock), the `sculpt.py` helpers and the skin bump/SSS layer recipe (hands, face, neck parts), `Foot.HairDensity` conventions (body hair part).

### 9.2 Order inside the script (Jeff's workstation, RTX 3050)
1. Foot targets (§4.1) — solved once through `linmodel` (milliseconds) and written to `p01/params.json`; S1 loads them, so the script itself starts on the fitted body.
2. Landmark sculpt + toes (§4.2–4.3), masks (§4.6), `Foot.Contact` (§4.7) — numpy, seconds.
3. Nails (§4.4) — seconds.
4. Guides (§4.5) — seconds; their attributes are written on the closeup copies in step 9.
5. Materials (§5) — seconds (the `Foot.UV` retile of §4.9 only if the bake fallback is needed).
6. Hair (§6.1, `--hair` only) — seconds.
7. Sock target, sock, last (§4.10–4.13) — remesh/smooth ≈ 20 s each foot.
8. Weights (§7.2) and the `foot.*` interface keys (§7.1) — seconds; save the part cache.
9. Measurements (§8.2) and, with `--render`, the closeup copies and the render set (§8.1): 5 views × 2 sides × 2 variants × 2 looks ≈ 40 `eval` renders at 10–60 s ≈ 10–40 min on the GPU, the full set only at milestones; every iteration before that uses `--quality form` (seconds for the whole set).

### 9.3 Estimated size
`01_foot_ankle_sock.py` ≈ 1,400–1,800 lines (its `measure()` ≈ 300 of them); `lib/sculpt.py` ≈ 350; no render script (spec 17's harness and `p01.json`). Three to four working sessions: (1) fit + sculpt + measure loop until §8.2 passes, (2) nails, masks, materials, hair until V5 passes, (3) sock + last + V6/V7, (4) critic round and fixes.

### 9.4 Risks and fallbacks
| Risk | Likelihood | Fallback |
|---|---|---|
| MPFB foot targets have coupled effects (length also changes height/width) or cannot reach 282 mm | low (B is 279.6) | finish the fit with `soft_move` scaling of the whole foot region about the ankle (a uniform scale of foot vertices below z 120 with a 30 mm blend into the shin) |
| MPFB's forefoot proportions: MT heads 6–18 mm too far forward, toes 2–5 as long as the hallux | certain (B) | §4.2 step 8 moves the MT-head line, §4.3 step 1 sets every tip by position |
| Shape keys from MPFB macro + our `Foot.Sculpt` key interact when the body part later changes macro values | medium | the foot script is re-run after any body change (it is cheap; S1–S2 changes mark S3 stale); `Foot.Sculpt` holds deltas over the basis (§4.1) |
| Procedural attribute-heavy shader too slow with SSS random walk | low on the GPU | bake masks (§5.6); reduce SSS to `Christensen-Burley` for look-dev iterations only |
| Bump at 0.3 mm cells aliases/facets | medium | raise the closeup copies' subdivision to 4 (§8.1), or enable Cycles experimental adaptive subdivision with true displacement for layers A/E/F/G (dicing rate 1 px) |
| Hair curves API/asset names differ in 4.5.14 | low | legacy particle hair is the fallback (fully scriptable; verified API) |
| Sock Shrinkwrap pinches between toes or at the heel | medium | increase SockTarget smoothing (20 iterations) or voxel size 3.5 mm; add a `Smooth` pass before Solidify |
| Nail plate clipping through the fold after posing | low | nails are bone-parented to the distal phalanx, which carries the fold vertices at weight 1.0 — they move together |
| Toe intersections in the boot pose | medium | `measure()` reports toe gaps; reduce adduction per toe until gaps ≥ 0 |
| The last does not fit the reference boot silhouette (V6) | medium | adjust the allowances (toe box 15 within the real 15–22 mm) before touching the foot; the foot size is fixed by anthropometry |
| ANSUR means are for US Army 2012; the client's soldier may be imagined with bigger feet | low | all macro numbers are constants at the top of the script; 285 or EU 45 (≈ 292 mm) is a one-line change (Q8) |

---

## 10. Interfaces and open questions

### 10.1 What neighbouring parts must provide or respect
| Part | Must provide | Must respect |
|---|---|---|
| Body / skin (base mesh; specs 03, 04 and `build_all.py` S1–S2) | `Body.Mesh` at 1855 mm with `Morgan.Rig` and MPFB's weights (`cache/body/rigged.blend`), the foot targets of §4.1 loaded in S1; the ankle UV seam kept as MakeHuman's; the leg above z 300 as spec 03 builds it (the sock wraps whatever is there: B 286 at z 260, 346 at z 330) | not to re-UV, re-topologise or sculpt below z 300 mm; not to touch the `Foot.*` layers or the `toenails` group; the `Foot.Contact` and `Foot.Sculpt` shape keys |
| Materials (spec 16) | `Skin.Foot` on `MG.Skin.Core` (shared with `Skin.Body`, so the ankle seam matches), `Nail.Plate`, `Nail.FreeEdge`, `Knit.Sock.WoolNylon(.Reinforced)`, `Hair.Body` | the regional data of §5 |
| Leg / trousers | shin hair density tapering to 30 % under the sock band (z 90–260) if the leg is ever shown bare; the minimum ankle circumference (229) is this part's, through S1 | the sock cuff at z 260 (the hem folds at z 200–230 lie on the boot collar, not on the sock) |
| Boot | builds its liner/insole around `Foot.*.Last` (297 long: 282 + 15); the insole plane is z = 0 of the last (sole thickness is added below); toe spring 12°; pitches its own copy 5.4° about the ball line (spec 02 §4.1 step 2); ankle axis markers used for the boot's flex crease; collar at z 210; takes the sock thickness (1.8 mm loaded) into account only through the last | never cuts inside the last; reports its inner clearance in its own eval |
| Rig (spec 08) | keeps MPFB bone names; places the foot and toe bones from the `foot.*` interface keys and adds `heel.*` (→ +Y 20), `toes_master.*`, `ball.*` (→ +X 20) in S2; IK pivot at `heel.*`; `toes_master` → MTP bones Copy Rotation | the weight table §7.2 (malleoli on the shin) |
| Pose (spec 08) | applies §7.3: ankle axes (−208, +75) / (+208, −75) in plan, on the footbed at h ≈ 122; headings 85° right / 17° left; plantar flexion 5.4°; toes 12°; `Foot.Contact` 1.0 / 0.85 | the right boot's medial side faces the camera |
| Evaluation (spec 17) | `LookDev`, `Hero`, `render.py`, `camera.py` (presets with `sides`, `mirror_x`, `ortho`, `hide`), `sheet.py`; it needs `Frame.Foot.L/R` from here | — |
| Hands / face | reuse `sculpt.py`, the bump chain and SSS values through spec 16's `MG.Skin.Micro` (hands: scale 0.0028; thinner skin on the fingers → `sss_scale` 0.7) | — |

### 10.2 Questions for the client
1. Sock colour: coyote brown with charcoal heel/toe (chosen) or black / foliage green? It is never visible, so this only matters if a "kit laid out" or barefoot/socked variant render is ever wanted.
2. Nail grooming: trimmed straight and short (military, chosen) or longer/neglected? Any nail trauma (a blackened toenail is common in soldiers) — we have put only a faint ridge on the right hallux.
3. Should the barefoot and socked variants be deliverables (turntables, closeups) or internal evidence only? This decides whether the sock fuzz and cloth cuff settle (§6.2) are built.
4. Weight distribution 55/45 right-heavy — confirm, or 50/50? (Spec 08 D6 adopts 55/45; default kept.)
5. Does the client want the toes animatable (keeps the 14 toe bones per foot in the final rig) or a single toe bone per foot for the final deliverable (we build all 28 either way)? (Now spec 08 Q3: the full 171-bone skeleton or the 61-bone lean merge.)
6. Superseded by Q8.

Added by the revision of 2026-10-10 (each with the default the build follows until Jeff answers):
7. **The boots lift the figure.** Standing on real boots' footbeds (heel seat 49 mm, ball seat 29), the hero figure is ≈ 42 mm taller than barefoot: the ankle axes at h ≈ 122 instead of 80 and, for a 1855 mm man, the skull top ≈ 9 px above the drawn y 20. Accept this as a declared difference in the overlay (**default**: reality wins, the man is `CLAUDE.md`'s 185 cm), or build a 1835 mm man so that the drawn skull top holds in boots?
8. **Foot size.** 282 mm (ANSUR Tight mean for this man, EU 44–45) replaces the 285 (EU 44.5) chosen from the boots; the boots' 288 mm projected length allows either. **Default 282**; 285 is a one-line change.
9. **Body mass (a finding of the body build).** At specs 03/04's macros (weight 0.45, muscle 0.70) and 1855 mm, the MPFB body holds 72.7 L, ≈ 75 kg at 1.03 kg/L, with a chest of 971 mm and a waist of 821 at the navel against the ANSUR 83 kg man's 1034 and 897; the weight macro alone reaches only ≈ 80 kg at 0.65. **Default**: keep 03/04's macros (the foot does not depend on them) and settle the trunk when specs 03 and 04 are revised: the ANSUR 83 kg man (a fuller trunk) or the drawing's lean V-taper?

### 10.3 Items tagged for research (status 2026-10-10)
* `[VERIFY: research_generators]` — per-unit gain of `l/r-foot-scale-*` and `measure-ankle-circ-*` targets: **settled** — detail targets are linear shape keys, so `linmodel` gives exact gains (spec 18 D3). MPFB does not re-fit bones after target changes; S2 re-runs `add_builtin_rig` (spec 08 §4.1).
* `[VERIFY: research_blender_capabilities]` — headless hair-curves node assets (names, append path), particle hair + Cycles curve rendering headless, `bpy.ops.object.bake` headless timings: open, checked when the script is written. `Store Named Attribute` → `modifier_apply` works only on a mesh without shape keys, hence the closeup copies (§4.5).
* `[VERIFY: research_prototypes]` — SSS random-walk render time per 2048² view: now on the GPU, measured on the first `eval` set; whether adaptive subdivision is viable.
* `[VERIFY: research_assets]` — the `knitted_fleece` texture's real stitch size: **settled** by spec 16's FFT (230 mm tile for a 1.6 mm stitch, C34); whether a finer knit texture (ambientCG `Fabric0xx` knit) is available.
* `[VERIFY: research_dimensions]` — ANSUR II: **settled** — the Tight column of `notes/research_dimensions.md` §1 is the reference (§3.1); the nail, phalanx, skin-thickness and hair figures are from anatomical ratios (the note found no open source for them).
