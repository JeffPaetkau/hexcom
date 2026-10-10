# Part 17 — Evaluation scene: camera, lights, floor, background, grading, presets

Status: draft 1 (spec writer), 2026-10-10, written under the **reality-wins** rule (`CLAUDE.md`, Source of truth). Owner scripts in `scripts/eval/`: `scene.py` (the hero scene), `camproj.py` (camera maths, no `bpy`), `camera.py` (hero camera and the preset registry), `lookdev.py` (neutral scene, turntables, swatch stage), `render.py` (render harness), `colour.py` (colour maths, AgX through OCIO), `grade.py` (display-referred grade), `overlay.py` (PIL overlays and metrics), `calibrate.py` (light solve), `masks.py`, `deliver.py`. Data: `scripts/eval/presets/*.json`, `patches.json`, `landmarks.json`, `ui_mask.json`, `set.json`. Object prefixes `Scene.*`, `Set.*`, `Cal.*`, `LookDev.*`.

> **Scope note (Jeff, 2026-10-10); it overrides the rest of this spec where they differ.** The deliverable now is the unit model, and this scene matters only as far as it changes how the model renders. **Built now:** the hero camera and the preset registry (§2.1, §3.1, §4.3); the key, cool side and world lights with light groups (§2.2, §3.2, §4.4, §4.10); a plain floor plane with the concrete material's reflectance for contact shadows, boot reflections and bounce (§3.4, §5.1, without joints); colour management and the grade without fog glow or haze (§5.6); the UI mask, masks and overlay (§2.6, §4.11, §4.12); calibration on patches P1 to P4 (§4.7, §8.2); the look-dev scene (§4.8); render tiers (§4.9); deliverables (§4.13). **Deferred** to the scene phase that follows acceptance of the model: the hangar stand-in set and its emitters (§2.4, §3.3, §4.6, §5.2, §5.3); floor joints, trench and grating (§4.5); the floor-pool spot (patch P5 becomes informational); depth of field and bokeh; fog glow and haze. Hero renders use a transparent film composited over a flat backdrop at the mean colour of the reference background around the figure, measured once by `overlay.py`. Depth of field is off: at f/1.5 focused at 4.5 m the blur anywhere on the figure is about one pixel or less, so it only ever affected the background. **Answers to §10.2:** deliverables live in the repository under `deliver/`, committed at milestones; the pool, bokeh, joint-layout and glare questions are deferred with their features.

Conventions (from `CLAUDE.md`): millimetres in this spec except where a table says metres (scene layout is given in metres because the set spans 30 m); world origin on the floor midway between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT = viewer's right**. In object names the Side field is the soldier's own: `L` = his left (+X), `R` = his right (−X), `C` = central. Pixel coordinates are full-reference pixels of `ref/reference_full.png` (1672 × 941, x right, y down). "Scene-linear" means Linear Rec.709 radiance before the view transform; "display" means sRGB-encoded values after AgX "Medium High Contrast" **and** the grade of §5.6, i.e. what the reference shows. Every hex in this spec is a display value unless marked "albedo" or "linear".

---

## 1. Purpose and acceptance

### 1.1 What this part is
The evaluation scene is the measuring instrument of the whole project: every other part is judged by rendering it here and comparing it with the reference. It consists of:
1. **Hero scene** (`Hero`): the reference camera solved by the analysts, four physical lights, a dim cool world, a polished-concrete floor with its joints and trench drain, a stand-in hangar set at the measured positions with emissive lamps sized for their bokeh, mist haze and bloom in the compositor, AgX "Medium High Contrast", and a display-referred grade.
2. **Look-dev scene** (`LookDev`): a neutral grey studio (desaturated `autoshop_01`, an 18 % grey cyclorama, neutral white key, fill and rim), an 85 mm turntable, a swatch stage that reads back albedo, and a calibration rig (18 % card, grey ball, chrome ball, ColorChecker Classic).
3. **Camera preset registry** that every part spec names its closeup views in (`camera.py`, `presets/*.json`), including the eight reference-crop presets.
4. **Verification overlay and metrics** (`overlay.py`), reference and render masks (`masks.py`), and the **light calibration** (`calibrate.py`) against named colour patches.
5. **Deliverables**: packed `.blend`, presentation glTF, final renders; the game export itself is spec 08 §7.6 and is only checked here.

Not in scope: any part of the character; the game glTF export (spec 08); the materials library (spec 16), whose albedos this scene reads back.

### 1.2 What perfect looks like
A critic flicking between the graded hero render and the reference at 100 % finds the same framing, the same warm key from his right-front-above, the same steel-blue wrap down his left side, the same crushed blacks, warm highlights and teal shadows, the same sheen and warm pool on the concrete with the boots mirrored dimly in it, and the same hangar behind him melting into bokeh at the same distances. The only differences they can find are the ones declared in §2.7: a soft physical shadow of his body on the floor to the viewer's right of the legs, hard-edged physical bokeh discs, and the hips 55 px higher than drawn (spec 08 D1). In the look-dev scene a grey ball renders neutral, the ColorChecker reads its published values, and a material placed on the swatch stage reports its albedo within 2 %. Every part spec names a preset and gets identical pixels every time.

### 1.3 Closeup render views of the scene itself (definitions in §4.3 and `presets/p17.json`)

| View | Camera | Target | Lens / output | Compared with | What it proves |
|---|---|---|---|---|---|
| S1 `p17.V1.hero_full` | hero: (0, −4500, 600), rotation (93.9°, 0, 0) | — | 46 mm, 36 mm sensor, f/1.5 focused on `Scene.Cam.Focus` (0, 0, 1300); 1672 × 941 | `ref/reference_full.png`, UI masked (§2.6) | framing, light directions, grading statistics, set composition (§1.4 items 1–8) |
| S2 `p17.V2.floor_feet` | hero, border (610,750)–(1010,935), `resolution_percentage` 300 | — | as hero; 1200 × 555 | `ref/crop_boots_feet.png` | pool shape and colour, contact cores, boot reflection smudges, seams, the start of the physical key shadow |
| S3 `p17.V3.bg_left` | hero, border (412,380)–(640,760), 200 % | — | as hero; 456 × 760 | the same box of the reference ×2 | crate stack, helmets 60 ± 4 px wide, racks, pillar lamp blob, CoC 8 px at 10 m |
| S4 `p17.V4.bg_right` | hero, border (960,0)–(1672,760), 100 % | — | as hero; 712 × 760 | the same box, UI masked | hull belly line, lamp blobs and FWHM, stair strips, orange lamp glow, floor streak |
| S5 `p17.V5.face_light` | hero, border (715,30)–(885,200), 500 % | — | as hero; 850 × 850 | `ref/crop_head_face.png` | patch ΔE, nose shadow toward his left, cool left cheek, black under-jaw |
| S6 `p17.V6.lookdev_rig` | LookDev (0, −1300, 1000) | (0, 0, 1000) | 85 mm, f/8, 1600 × 1200 | ColorChecker values (§3.5) | neutrality of the look-dev light, chart ΔE, chrome-ball light map |

S1–S5 render the full character (or, before it exists, `Cal.Proxy`, §4.7); S2–S5 are borders of the S1 camera, so they need no extra camera and match the crops pixel for pixel.

### 1.4 Pass criteria a critic or script can score
1. **Camera maths.** `camproj.project()` and Blender's `world_to_camera_view` agree within 0.1 px on 20 test points; the horizon of a rendered test grid lies at y 616.1 ± 0.5; family-B floor seams are level within 0.1°; the landing lamp (1.5, 7.0, 1.7 m) projects to (1113.5, 412.2) ± 0.5.
2. **Landmarks.** Spec 08 §8.3 passes on S1 (scene-side duty: never move the camera).
3. **Patches.** The five named patches (P1–P5, §2.2) on the graded S1 within their ΔE00 tolerance, with the light solution inside the §4.4 bounds.
4. **Grading statistics** on the UI-masked S1: median luminance 41 ± 4, 1st percentile ≤ 3, 99th 212 ± 8, pixels ≤ 5 between 1.5 and 3.5 %, saturation median 0.20 ± 0.03, shadow-band mean B − R = +3.3 ± 1.5, highlight-band R − B = +24 ± 6.
5. **Floor.** Family-B seams at y 854 / 802 / 769 / 746 ± 4 px; seam S1 through (400,866)–(616,836) ± 6 px; trench grate box IoU ≥ 0.6 with (1100–1262, 805–837); floor patches F1–F3 within ΔE00 6; the warm pool's half-brightness radius 0.6–0.7 m.
6. **Background.** Every emitter blob centroid within 8 px (Z < 13 m) or 12 px (farther) of the reference; blob FWHM within 3 px; helmet width 60 ± 4 px; hull belly edge at y 560–580 across x 1000–1400; far floor line y 690 ± 6.
7. **Depth of field.** Edge-spread width of the crate-stack top edge 8 ± 1.5 px; Laplacian variance of face, chest, hands and boots ≥ 0.6 × the reference's (§8.3).
8. **Physical shadow present** (the client's ruling): mean floor luminance inside the key-shadow mask ≤ 0.8 × the same pixels in the `noshadow` diagnostic.
9. **Look-dev.** Grey ball |a*|, |b*| ≤ 1.0; chart median ΔE00 ≤ 2, max ≤ 4 (linear-normalised, §8.3); swatch read-back of `Cal.Mat.Grey18` 0.180 ± 0.004.
10. **Reproducibility.** The same preset rendered twice is bit-identical on the CPU (fixed seed); on the GPU within 1/255 on under 2 % of pixels (§4.14); `camera.py --lint` resolves every preset in the registry.
11. **Time** on this box (4 cores, shared): S1 at the `eval` tier ≤ 4 min; the `cal` render ≤ 7 min; S6 ≤ 90 s.

---

## 2. Reference observations

### 2.1 Camera (adopted from consolidated §8, checked with the exact pitched projection)
Camera at (0, −4.50, 0.60) m, rotation (93.9°, 0, 0), 46 mm on a 36 mm horizontal sensor, 1672 × 941, no shift, f/1.5. Focal length in pixels f = 46 / 36 × 1672 = **2136.4**; principal point (836, 470.5); horizon y = 470.5 + f·tan 3.9° = **616.1**. The analysts' depth map used the level-camera approximation Z = 1278/(y − 615); this spec uses the exact projection (`camproj.py`, §4.3), which differs by up to 10 px near the feet:

| Image row y (centre column) | Floor Y (m) | Camera distance (m) | Note |
|---|---|---|---|
| 941 | −0.49 | 4.01 | bottom of frame |
| 925 | −0.29 | 4.21 | pool centre row |
| **905** | **0.00** | 4.50 | the floor under the origin (not 895) |
| 895 | +0.16 | 4.66 | drawn right sole |
| 850 | +1.05 | 5.55 | — |
| 808 | +2.25 | 6.75 | — |
| 780 | +3.40 | 7.90 | — |
| 746 | +5.46 | 9.96 | crate-stack floor line ≈ 750 |
| 720 | +7.94 | 12.44 | — |
| 690 | +12.98 | 17.48 | far floor line (base of the far crate rows) |
| 680 | +15.71 | 20.21 | — |

Verification targets drawn by the overlay (§4.12): skull top y 20; his right sole y 895, left 907; pupils (800,77) and (832,77); stance centre x 830 (midpoint of the ankles 732/928); horizon 616; far floor line 690. A 1855 mm head at Y −50 projects its crown to y 22, so the scene and spec 08's expectations agree.

### 2.2 Light evidence and calibration patches (5 × 5 means re-sampled for this spec; sd = mean per-channel standard deviation in the window)

| ID | Patch | Pixel | Hex | Lum | sd | Role in this scene |
|---|---|---|---|---|---|---|
| **P1** | his right temple (named) | (778,70) | **#e6bfac** | 198 | 10.9 | acceptance; key highlight, on a gradient |
| **P2** | his right cheek (named) | (792,100) | **#d19b87** | 165 | 3.7 | acceptance and key anchor |
| **P3** | admin panel top (named) | (800,220) | **#897967** | 123 | 12.0 | acceptance; checks spec 13's tan polymer under the key |
| **P4** | his left shin (named) | (935,720) | **#333b47** | 58 | 6.9 | acceptance; cool light on spec 09's cloth |
| **P5** | floor pool between the feet (named) | (830,885) | **#c9baaa** | 188 | 16.5 | acceptance; pool spot and floor albedo; scored on the `refmatch` render because the physical key shadow of his right shin falls on this point (world (−0.01, +0.32), D1) |
| A1 | right cheek, flat | (792,103) | #d29e89 | 168 | 2.6 | solve: key power and CCT |
| A2 | right temple, flat | (776,79) | #e9c4ac | 202 | 3.6 | solve: key |
| A3 | left forehead | (826,51) | #a37c77 | 132 | 3.6 | solve: cool (with key spill) |
| A4 | left cheek | (833,91) | #997777 | 126 | 6.3 | solve: cool |
| A5 | under the jaw | (817,140) | #0f0805 | 9 | 1.9 | solve: world |
| A6 | right shin, unlit | (759,725) | #0e0e0e | 14 | 1.0 | check: world on spec 09 cloth |
| F1 | floor, pool front | (828,934) | #ccb6a0 | 185 | 2.6 | solve: pool power |
| F2 | floor, pool edge (viewer's left) | (576,930) | #7c6f61 | 113 | 2.0 | solve: pool falloff and floor albedo |
| F3 | floor, cool slab | (1300,918) | #353b42 | 58 | 0.3 | solve: floor albedo |
| F4 | floor streak (far panel reflection) | (1115,735) | #98b0c5 | 172 | 20.4 | check: floor roughness, far panel strength |
| C1 | admin panel, flat | (804,219) | #857663 | 119 | 2.5 | check (spec 13) |
| C2 | left shin, flat | (928,722) | #32383f | 55 | 3.4 | check (spec 09) |
| C3 | right thigh, unlit | (760,560) | #110f0e | 15 | 7.1 | check |

The analysts' left forehead (835,52) and left cheek (840,100) straddle edges (sd 52 and 32); A3 and A4 replace them for solving. Light directions (consolidated §8): key azimuth 40° toward −X, elevation 42°, 4500 K; cool azimuth 100° toward +X (10° behind the shoulder plane), elevation 35°, linear (0.55, 0.76, 1.00); ambient ≈ 5 % of the key; nose shadow falls toward his left; his right ear fully lit; no hard rim.

### 2.3 Floor (seams fitted with the exact projection)
* **Family B** (parallel to X): the measured seams at y 852 / 801–808 / 772–776 / 746 fit **Y = 0.95 + 1.5 k m** (projecting to y 854 / 802 / 769 / 746).
* **Family A** (at 55° to X in plan): seam S1 runs through world (−1.05, 0.70) and (−0.60, 1.40) (57°); the grating strip S3 through (0.74, 1.56)–(1.32, 2.40) (55.5°); S1b (−0.17, 2.54)–(0.19, 3.16) (60°). The family is irregular (generator wobble); lines are laid at 55° with an X-intercept pitch of 1.5 m (1.229 m perpendicular) phased through S1, each jittered ±0.10 m by seed.
* **Trench grate** image box (1100–1262, 805–837), centre (1181, 821) → world (+1.01, +1.83), long axis along family A.
* Colours: cool slab #353b42 (sd 0.3); seam #464548 at (1180,806); grate #646870; mottled patches #817976 / #625e5b; streak #98b0c5–#bccfde; pool #ccb6a0 (front), #d9c6b4 (between the feet, the brightest floor), #7c6f61 at the pool edge.
* The dark smudges under the boots inside the pool (lum 50–80) are glossy reflections of the boots (lighting note §2.6), and the contact cores under the soles are 0–8.

### 2.4 Background inventory, converted to world metres and re-projected
Camera-relative Z of the lighting note becomes world Y = Z − 4.5. Every row was re-projected with `camproj` to check it lands on its image blob. **Emitter sizes** follow D4: the visible blob is the emitter convolved with the defocus disc, so the in-focus emitter is (blob − CoC) px wide, converted at its depth.

| Element | Image evidence | World placement (m) | Size (m) | Re-projected centre |
|---|---|---|---|---|
| Crate stack (his right) | x 412–600, floor line y ≈ 750 | front at Y 5.0, X −3.50…−1.05; tiers 0–0.70, 0.70–1.15 | cases 1.10 × 0.60 × 0.70 and 0.80 × 0.50 × 0.45 | crate top y 492 (ref ≈ 497) |
| Helmets (4 visible) | x 413–600, tops y 445 | X −1.80, −1.55, −1.30, −1.10 on the upper tier, Y 5.2 | 0.28 L × 0.23 W × 0.21 H | top y 445; width 63 px |
| Racks with hanging gear | x 430–640, y 100–450 | X −2.2…−1.0, Y 6.5–7.4, H 0–3.5 | bay 1.2 × 0.9 m | — |
| Pillar + warm lamp | lamp (547–574, 99–120) | pillar centre (−1.55, 7.5), lamp at H 3.45 | pillar 0.40 × 0.40; lamp emitter 0.10 × 0.07 | (564, 115) |
| Steel columns | x 600–700, y 0–450 | (−1.00, 6.0), (−0.75, 9.0) | HEA 300 | — |
| Dropship hull (his left) | nose x ≈ 1000, belly y 560–580 | nose (0.85, 6.5), axis 48° to X, length 9.3 m, belly H 0.8, top 4.8 | 3.5 W × 4.0 H | belly at nose y 576 |
| Landing light (hull) | (1099–1127, 406–420), 29 × 15 px | (1.50, 7.00, 1.70) | 0.11 × 0.03 | (1114, 412) |
| Warm hull lamp | (1064–1087, 360–371) | (1.30, 7.00, 1.95) | 0.075 × 0.015 | (1076, 366) |
| Upper window | (1144–1207, 202–229) | (2.10, 8.50, 3.05) | 0.33 × 0.11 | (1178, 222) |
| Mid hull lamp | (1482–1493, 379–393) | (4.60, 10.50, 2.20) | 0.02 × 0.03 | (1488, 389) |
| Edge lamp | (1653–1671, 164–185) | (7.00, 13.50, 4.30) | 0.06 × 0.085 | (1657, 181) |
| Boarding stair | x 1420–1660, y 470–700 | base front centre (4.55, 10.4, 0), run azimuth 40° from +X toward +Y, pitch 40°, 15 risers to H 3.0 | 1.2 wide | in-frame part rises to H ≈ 1.7 (D15) |
| Stair base lamps | (1509–1545, 670–683), (1448–1468, 673–682) | (4.85, 10.5, 0.18), (4.40, 10.5, 0.18) | 0.19 × 0.02, 0.07 × 0.01 | (1530, 676) |
| Orange tube lamp | (1336–1393, 549–562) | (3.70, 10.50, 1.00) | 0.34 × Ø0.03 | (1363, 559) |
| Dark red case | x 1620–1672, y 620–800 | (2.85, 2.40, 0), H 0–0.60 | 0.55 × 0.45 × 0.60 | cut by the frame edge |
| Far crate rows | x 950–1300, y 580–700 | front at Y 12.5, second row 13.4; X −0.9…+3.7; H 0–1.6 | 1.2 × 1.0 × 1.0–1.2 | base y 692 |
| Far frosted panel | (1105–1131, 533–573) | (2.25, 12.45, **1.10**) (D14) | 0.13 × 0.24 | (1119, 553) |
| Far vertical strips (3) | (1227–1240, 606–644) | (3.20, 12.45, 0.40 / 0.53 / 0.66) | 0.025 × 0.08 each | (1233, 625) |
| Ceiling lamps | (1114–1127, 58–74), 14 × 17 px | grid X {−5.3, −1.3, 2.7, 6.7} × Y {3.5, 7.5, 11.5, 15.5}, H 5.8 | emitter sphere r 0.03 in a Ø0.25 housing | (1120, 68) for (2.7, 15.5) |
| Ceiling batten | (1586–1672+, 18–40) | (7.5, 14.8, 6.0), along X | 1.30 × Ø0.05 | — |
| Helmet visor glow | (492,450), 6 × 6 px | top front of helmet 2: (−1.55, 5.10, 1.35) | 0.06 × 0.012 strip | (496, 451) |
| Far wall (hazy) | #4f5455 at (1050,560) | Y 16.0, X −12…+18, H 0–9 | — | base y 679 (hidden by crates) |
| Ceiling, trusses | top strip, #121619 at (1000,40) | ceiling H 9.0; trusses at Y 4, 8, 12, 15.5, chords H 6.2 / 7.8 | chords 0.20 box | — |

### 2.5 Grading statistics (UI-masked as §2.6; 71.7 % of the frame)
Luminance percentiles 0.1 %: 0, 1 %: 1.6, 5 %: 9.0, 25 %: 22.6, **50 %: 40.8**, 75 %: 64.1, 95 %: 144, **99 %: 212.1**, 99.9 %: 241.2; **2.53 % of pixels ≤ 5**; 0.002 % ≥ 250 (lamp cores clip at 240–246). Band means: shadows (< 40, 49 % of pixels) **(20.9, 23.0, 24.2)**; low-mids (54.2, 56.0, 58.1); mids (113.4, 109.8, 108.1); highlights (> 160, 3.7 %) **(205.1, 193.7, 181.2)**. Saturation (max − min)/max: median **0.20**, 95th percentile 0.41. Figure box (620–1000 × 150–900): median 48, 99th 220. Bloom radial profile of the orange lamp from its peak at (1370,559): 248, 200 (r 4), 174 (8), 125 (12), 100 (16), 84 (20), 67 (24), 51 (30), 34 (38); ceiling lamp FWHM ≈ 14 px. No vignette, grain or chromatic aberration.

### 2.6 UI mask (measured from the panel borders; `scripts/eval/ui_mask.json`, inclusive boxes)
Tabs and title (0,0)–(466,196); item cards (44,196)–(412,760); BACK (35,848)–(189,899); UNIT STATS (1259,61)–(1637,374); CONFIRM LOADOUT (1325,841)–(1637,900). A second mask, `shadow_key`, marks the floor that the physical key shadow darkens (D1): computed per render as (noshadow − physical)/noshadow > 0.10; fallback polygon (740,912), (1000,912), (1250,880), (1480,830), (1460,795), (1200,820), (980,850), (760,880), following the shadow centreline from the feet (850,905) through (1088,865) to the head's shadow at (1399,816).

### 2.7 Ambiguities and decisions (reality-wins rule)

| # | Topic | Image / analysts | Decision and reason |
|---|---|---|---|
| D1 | Body shadow on the floor | none visible; analysts: shadow-link the key off the floor, or raise it to 55° | **Physical shadow** (client, 2026-10-07): one key, no shadow linking in hero renders. The soft shadow runs from the feet toward (1400, 816). Floor comparisons skip `shadow_key`; the two-key `refmatch` trick (§4.10) exists only as a diagnostic. |
| D2 | Floor pool | a spot light-linked to the floor only, at (−0.90, −2.40, 4.20) | A real fixture lights everything in its beam. A 150 mm Fresnel spot, **not light-linked**, moved steeper to (−0.77, −1.69, 4.38) so the shin fronts receive ≈ 0.4 of its floor irradiance (0.57 from the analysts' position); boot toe caps and trouser-hem tops get warm light, as the reference shows. `--pool-link` remains a diagnostic. |
| D3 | Bokeh | soft Gaussian-like game discs, 14–19 px blobs | **Physical thin lens**: f/1.5, round aperture, hard-edged discs; CoC 8.0 px at 10 m, 11.3 at 20 m, 14.6 at infinity. Blobs are compared by FWHM, not by edge profile. |
| D4 | Lamp sizes | 0.4 × 0.4 m ceiling lamps, 0.22 × 0.1 m landing light | The in-focus emitter must be smaller than (blob − CoC); sizes recomputed in §2.4 (the ceiling lamp is a 60 mm source, not 400 mm). |
| D5 | Camera form | pitched 93.9° or level + shift_y −0.087, "identical" | They differ by 4 px at the feet; the **pitched** camera is canonical (every spec uses it). The 50 mm variant is kept only as `hero.alt50` for sensitivity checks. |
| D6 | Floor depth map | Z = 1278/(y − 615) | Exact pitched projection (§2.1); the floor under the origin is y 905. |
| D7 | Compositor grade | lift, gain, saturation and a black curve in Blender's compositor | The compositor runs on scene-linear data before AgX; a curve at linear 0.02 would crush everything below display 23/255. The measured grade is display-referred, so `grade.py` applies it after AgX (§5.6). Only bloom and haze, which are optical, stay in the compositor. |
| D8 | Floor albedo | #4a4b4e (linear 0.07) | Real dark, soiled, sealed concrete is 0.08–0.20; solved by calibration in [0.06, 0.30] starting at 0.12. |
| D9 | Floor joints | a sheared 1.5 m grid, seams 15–20 mm | Kept as drawn (a decorative saw-cut layout is plausible) but built as real joints: 6 mm saw cut, dark polyurea filler 3 mm below the surface, 2–5 mm spalled arrises giving the 12–16 mm visible band. |
| D10 | Haze | volume density 0.004 or depth fog | Mist-pass fog in the compositor (deterministic, free on CPU); a homogeneous volume only on the GPU machine. |
| D11 | Ambient | dark industrial HDRI at 5 % | `empty_warehouse_01`, tinted cool, Mapping rotation Z −80° (puts its brightest windows behind-right at azimuth +45°); the set's walls and ceiling are invisible to diffuse rays so the world stays the single ambient control. |
| D12 | Calibration patches | 5 × 5 means at the analysts' pixels | The five named patches are the acceptance set; the solve uses the flatter anchors A1–A6, F1–F3, sampled at points projected from the model (§7.2), so a real-proportion body does not sample the wrong pixel. |
| D13 | Look-dev definition | five different "scene A" descriptions (specs 01, 03, 06, 11, 12) | One canonical `LookDev` (§4.8), AgX **Base Contrast** for material judgement; spec 01's "Medium High Contrast" for scene A is superseded. |
| D14 | Far frosted panel height | H 1.4 m | Its blob centre re-projects to **H 1.10 m** (the 1.4 was its top). |
| D15 | Boarding stair | 3 m tall, 35–40°, X 4.25–5.7 | The in-frame part rises only to ≈ 1.7 m; a run receding at 40° from +X makes the pitch 40°, inside OSHA 1910.25's 30–50°. |

---

## 3. Real-world reference

The scene is a photographic set, so "reality" means real optics, real light fixtures with real colour temperatures, a real concrete floor and real-sized props. Marks: **M** measured (from the image or on this machine), **S** sourced (standard or published data), **E** estimated.

### 3.1 Camera and lens (thin lens, Cycles' ideal camera)

| Quantity | Value | Mark |
|---|---|---|
| Sensor | 36.00 × 20.26 mm (horizontal fit; 1672 × 941 px = 46.44 px/mm) | M |
| Focal length | 46.0 mm → f = 2136.4 px; HFOV 42.8°, VFOV 24.9° | M (analysts) |
| Aperture | f/1.5 → entrance pupil 30.7 mm, round (blades 0); a valid lens (a 40–50 mm f/1.4 full-frame prime stopped to f/1.5 has a 27–33 mm pupil) | M / S |
| Focus | `Scene.Cam.Focus` at (0, 0, 1300) → 4537 mm along the optical axis | M |
| Circle of confusion (0.0215 mm per px) | 4.0 m: 2.0 px; 5.3 m: 2.1; 6.5 m: 4.4; 10 m: 8.0; 15 m: 10.2; 20 m: 11.3; infinity: 14.6 | computed |
| Depth of field for CoC ≤ 2 px (0.043 mm) | 3.99–5.26 m: the whole figure, the pool and the near floor are sharp | computed |
| Clip | 0.05–120 m | E |
| Distortion, vignette, chromatic aberration, grain | none (reference: vignette ≤ 0.15 EV, no CA) | M |
| Look-dev camera | 85 mm on the same 36 mm sensor (a portrait prime), f/8 for macro presets | S |

### 3.2 Light sources as real fixtures

| Light | Real fixture class | Emitting size (mm) | Colour | Placement | Mark |
|---|---|---|---|---|---|
| Key | large square soft source: LED panel behind a diffusion frame ("book light" / 150 cm softbox class) | 1500 × 1500 | bi-colour LED at **4500 K** (±300) | 3.5 m from the chest at az −40°, el 42° | M (direction), S (fixture class) |
| Cool side | overhead diffusion frame (10 × 10 ft butterfly class) lit by daylight LEDs through ½ CTB | 3000 × 3000 | linear (0.55, 0.76, 1.00), a ≈ 12 000 K look | 4.0 m at az +100°, el 35° | M / S |
| Floor pool | 150 mm (6 in) LED Fresnel spot, flood 26°, hung from a truss | lens Ø150 | 4500 K | 4.4 m up, el 72° from the pool centre | M (pool), S (fixture), D2 |
| Kicker (off) | 1 m soft panel | 1000 × 1000 | as cool | (1.80, 3.00, 3.80) | E |
| Under fill (off) | 1 m bounce card, floor level | 1000 × 1000 | 4500 K | (−0.30, −1.00, 0.05) facing up | E |
| Ceiling high-bays | compact LED downlight; bare 60 mm source in a Ø250 × 120 housing | Ø60 | 6500–7500 K (#e4f2fa core) | H 5.8 on a 4 m grid | M (blob), E |
| Orange tube | amber LED tube lamp on a post | 340 × Ø30 | 2600 K | H 1.0 | M / E |
| Pillar lamp | wall lamp | 100 × 70 | 4000 K (#f4f3ee) | H 3.45 | M |
| Stair strips | 10 mm LED strip along both stringer tops | 10 × run | 8000 K look (#9caec2–#c4dae7) | — | M |
| Far frosted panel | frosted LED panel | 130 × 240 | cool (#aec7d7) | H 1.10 | M |

### 3.3 Hangar architecture and props

| Item | Real class | Dimensions (mm) | Mark |
|---|---|---|---|
| Hangar | aircraft maintenance hangar, clear span | 30 000 modelled of a ≈ 40 000 × 40 000 × 10 000 interior | E |
| Floor slab | ground-bearing industrial slab | 200 thick | S (typical) |
| Contraction joint | saw cut at ¼ depth, semi-rigid polyurea filler (traffic-bearing practice per ACI 302.1R) | 6 wide × 50 deep; filler 3 below surface; arris spalls 2–5 | S [VERIFY ACI clause] |
| Trench drain | EN 1433 class F900 slotted grate (airside load class), galvanised steel | clear width 300, 2 sections × 800, frame angles 40 × 40 × 4, channel 250 deep, slots 12 × 100 at 25 pitch | S (class), E (size) |
| Columns | HEA 300 rolled section | 290 deep × 300 wide, flange 14, web 8.5 | S (EN 10365) |
| Pallet racking | upright frames and box beams | uprights 90 × 70, frame depth 900, beam levels 1500 / 2500 / 3500 | E |
| Transit cases | rotomoulded military transit case | lower 1100 × 600 × 700, upper 800 × 500 × 450; corner radius 25; latch 60 × 20 × 80 | E [VERIFY against a real case range] |
| Ballistic helmets | ACH / FAST-class shell | 280 long × 230 wide × 190 high; NVG shroud 70 × 25 × 40; side rails 120 × 20 × 10 | E [VERIFY] |
| Red case | rolling tool cabinet | 550 × 450 × 600, radius 20 | E |
| Boarding stair | mobile maintenance stair; OSHA 1910.25: angle 30–50°, riser 152–241, tread depth ≥ 241, width ≥ 559, handrail 762–965 | width 1200, 15 risers × 200, going 240, pitch 40°, handrail 900, open grating treads 40 thick | S (OSHA), E |
| Dropship | fictional; stand-in from the image | 9300 long × 3500 wide × 4000 high, belly at 800; landing gear Ø220 struts, Ø600 × 300 wheels | M (image) |

### 3.4 Floor: polished concrete

| Property | Value | Mark |
|---|---|---|
| Finish | ground and polished, honed to semi-polished (400–800 grit resin), penetrating lithium-silicate densifier plus a topical guard | S [VERIFY CPAA level names] |
| Albedo (diffuse, linear) | new grey concrete 0.25–0.35; soiled hangar floor 0.12–0.20; dark integrally pigmented 0.08–0.12 → solved in [0.06, 0.30] from 0.12, slightly cool (0.96, 1.00, 1.05) | S / E |
| Roughness (GGX) | 0.30 mean, range 0.22–0.45; lamp reflections stretch ≈ 2.5× into vertical streaks | M |
| IOR | 1.50 | S |
| Coat (guard) | weight 0.10, roughness 0.20, IOR 1.5 | E |
| Slabs | decorative saw-cut grid: family B parallel to X at 1.5 m pitch, family A at 55° to X, 1.5 m X-pitch (D9) | M |
| Joint filler | dark grey polyurea, albedo #222326 (linear 0.016) | M (analysts) / E |
| Wear | tug and tyre marks along Y, oil stains 0.2–0.6 m, dust in joints and near walls, mopped smoother bands | E |

### 3.5 Colour standards

* **sRGB** (IEC 61966-2-1): decode c ≤ 0.04045 → c/12.92, else ((c + 0.055)/1.055)^2.4.
* **AgX in Blender 4.5.14** (OCIO config bundled with this build, measured on this machine through `PyOpenColorIO`; display sRGB):

| Scene-linear grey | 0.003 | 0.005 | 0.01 | 0.02 | 0.03 | 0.05 | 0.08 | 0.12 | 0.18 | 0.25 | 0.35 | 0.5 | 0.7 | 1.0 | 1.5 | 2.0 | 4.0 | 8.0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| "AgX - Medium High Contrast" (/255) | 1 | 3 | 10 | 23 | 33 | 49 | 70 | 92 | 118 | 139 | 160 | 178 | 194 | 208 | 221 | 229 | 244 | 255 |
| "AgX - Base Contrast" (/255) | 5 | 9 | 18 | 32 | 42 | 58 | 76 | 96 | 118 | 136 | 153 | 170 | 184 | 197 | 209 | 217 | 233 | 245 |

  The reference median of 41/255 therefore sits near scene-linear 0.04 before the grade; lamp cores at 240–246 are ≈ 3.5–5 scene-linear after defocus.
* **CIEDE2000** for every colour tolerance (D65, 2° observer; implemented in `colour.py`, unit-tested against Sharma, Wu and Dalal's published test pairs).
* **ColorChecker Classic** (24 patches, 40 × 40 mm on a 279.4 × 215.9 mm card; sRGB D65 values as commonly published from BabelColor's averages) [VERIFY against the BabelColor sheet when the chart texture is built]:

| Row | Patches 1–6 |
|---|---|
| 1 | dark skin #735244, light skin #c29682, blue sky #627a9d, foliage #576c43, blue flower #8580b1, bluish green #67bdaa |
| 2 | orange #d67e2c, purplish blue #505ba6, moderate red #c15a63, purple #5e3c6c, yellow green #9dbc40, orange yellow #e0a32e |
| 3 | blue #383d96, green #469449, red #af363c, yellow #e7c71f, magenta #bb5695, cyan #0885a1 |
| 4 | white 9.5 #f3f3f2, neutral 8 #c8c8c8, neutral 6.5 #a0a0a0, neutral 5 #7a7a79, neutral 3.5 #555555, black 2 #343434 |

---

## 4. Geometry construction plan

### 4.1 Files, scenes, collections, naming
* One build product, `cache/scene_eval.blend` (gitignored), made by `blender -b --python scripts/eval/scene.py -- --build [--character cache/character_hero.blend | --proxy]`. It holds two Blender scenes, `Hero` and `LookDev`, which both link the same `Character` collection (linked from spec 18's `build_all.py` output for evaluation; appended and made local only by `deliver.py`).
* `Hero` collections: `Scene.Cam`, `Scene.Light`, `Scene.Floor`, `Scene.Set` (children `Scene.Set.Shell`, `Scene.Set.Props`, `Scene.Set.Emit`), `Scene.Cal` (hidden in renders except S6 and the probe), `Character`. `LookDev`: `LookDev.Stage`, `LookDev.Light`, `LookDev.Cal`, `LookDev.Turntable`.
* Names follow `Part.Side.Component` with Side L/R/C as in the header: `Scene.Light.R.Key`, `Scene.Floor.L.Trench.Grate`, `Set.R.Stack.Case.03`, `Set.L.Ship.Lamp.Landing`. Materials `<prefix>.Mat.<Name>`, images `<prefix>.Img.<Name>`, worlds `Scene.World.Hangar`, `LookDev.World.Studio`.
* Units metric, scale 1.0, metres. Set objects have their origin at the base centre on the floor and rotate only about Z; emitters have their origin at the emitting surface's centre. `scene.py` is idempotent: it deletes and rebuilds everything with its prefixes and never touches `Character`.
* The set is data, not code: `scripts/eval/set.json` lists every element (builder, parameters, location, rotation, material, visibility class), so a placement fix is a one-line data change.

### 4.2 Build order (`scene.py --build`, ≈ 25 s without the character)

| # | Step | Tool / API | Output |
|---|---|---|---|
| 1 | Units, scenes, collections, view layer, light groups (§4.10) | `bpy.data.scenes.new`, `view_layer.lightgroups.add` | empty `Hero`, `LookDev` |
| 2 | Hero camera and focus Empty | `camera.hero_camera()` (§4.3) | `Scene.Cam.Hero`, `Scene.Cam.Focus` |
| 3 | Floor slab with the trench cut | `bmesh.ops.create_cube` scaled, Boolean `DIFFERENCE` solver `EXACT`, applied under `temp_override` | `Scene.Floor.C.Slab` |
| 4 | Trench channel, grate, frame angles | bmesh extrusions, Solidify | `Scene.Floor.L.Trench.*` |
| 5 | Lights and targets | `bpy.data.lights.new`, Track To (`TRACK_NEGATIVE_Z`, `UP_Y`) | `Scene.Light.*` |
| 6 | World | node tree (§5.4) | `Scene.World.Hangar` |
| 7 | Set from `set.json` | builders in `scene.py` (§4.6): bmesh, Bevel, Array, Curve bevel, Subdivision | `Set.*` |
| 8 | Emitters | emissive meshes (§5.3) | `Set.*.Lamp.*` |
| 9 | Compositor (haze, bloom) and colour management | `scene.node_tree` (§5.6) | — |
| 10 | Calibration rig, proxy (if `--proxy`) | §4.7 | `Cal.*` |
| 11 | LookDev scene | §4.8 | `LookDev.*` |
| 12 | Self-tests: camera maths, linking, emitter re-projection | `camera.py --selftest`, `scene.py --selftest` | `renders/eval/selftest_*.png`, log |
| 13 | Save | `wm.save_as_mainfile(compress=True, relative_remap=True)` | `cache/scene_eval.blend` |

### 4.3 Hero camera and the preset registry (`camproj.py`, `camera.py`)
**Hero camera** (the single source; no other script may create it):
```python
cam = bpy.data.cameras.new('Scene.Cam.Hero'); ob = bpy.data.objects.new('Scene.Cam.Hero', cam)
ob.location = (0.0, -4.50, 0.60); ob.rotation_euler = (radians(93.9), 0.0, 0.0)
cam.lens = 46.0; cam.sensor_width = 36.0; cam.sensor_fit = 'HORIZONTAL'
cam.shift_x = cam.shift_y = 0.0; cam.clip_start, cam.clip_end = 0.05, 120.0
cam.dof.use_dof = True; cam.dof.focus_object = focus_empty      # 'Scene.Cam.Focus' at (0, 0, 1.30)
cam.dof.aperture_fstop = 1.5; cam.dof.aperture_blades = 0; cam.dof.aperture_ratio = 1.0
scene.render.resolution_x, scene.render.resolution_y, scene.render.pixel_aspect_x = 1672, 941, 1.0
```
**Projection** (`camproj.py`, pure Python, used by `overlay.py` and the metrics without Blender): with θ = 3.9°, f = 2136.4, C = (0, −4.5, 0.6): d = (Y − C_y) cos θ + (Z − C_z) sin θ; v = −(Y − C_y) sin θ + (Z − C_z) cos θ; x = 836 + f (X − C_x)/d; y = 470.5 − f v/d. These are continuous coordinates; a PIL pixel index p has its centre at p + 0.5, and every comparison with a reference pixel adds that half pixel. `floor_point(x, y)` inverts the projection onto Z = 0. Self-test: 20 points through `bpy_extras.object_utils.world_to_camera_view` agree within 0.1 px.

**Render borders**: a box (x0, y0)–(x1, y1) of the reference (x1, y1 exclusive) is `border_min_x = x0/1672`, `border_max_x = x1/1672`, `border_min_y = (941 − y1)/941`, `border_max_y = (941 − y0)/941`, `use_border = use_crop_to_border = True`, `resolution_percentage = 100 × scale`. Cycles renders only the border, so a ×5 head crop costs 850 × 850 pixels, not the full frame.

**Preset schema** (`scripts/eval/presets/pNN.json`, one file per part; ids are `pNN.Vk`, with the spec's label as an alias):
```json
{"id": "p02.V4", "label": "lace_close", "scene": "lookdev|hero|form",
 "camera": {"type": "look_at|hero|ray|turntable|ortho",
            "frame": "W|Frame.Boot.L|<any object>", "mirror_x": false,
            "pos_mm": [0, -620, 330], "target_mm": [0, -130, 150], "up": [0, 0, 1],
            "lens_mm": 85, "sensor_mm": 36, "ortho_scale_mm": null,
            "anchor": null, "distance_mm": null, "n": null, "elev_deg": null},
 "dof": {"fstop": 8, "focus": "target|<object>|[x, y, z]"},
 "render": {"res": [2048, 2048], "border_px": null, "scale": 1, "tier": "eval", "film_transparent": false},
 "compare": ["ref/zoom_boots_left_laces_x10.png"], "owner": "02"}
```
Types: `hero` uses `Scene.Cam.Hero` unchanged (with an optional border and scale); `look_at` places one reusable camera `Scene.Cam.Preset` at `pos` looking at `target` with `up` (needed for the straight-down and straight-up views of specs 02 V3 and 07 V3); `ray` places the camera `distance_mm` from `anchor` along the anchor's ray to the hero camera (spec 06 V3–V6); `turntable` expands into `n` views (§4.8); `ortho` sets `type = 'ORTHO'` with `ortho_scale` (spec 01's measurement renders). Positions are in the named frame: the resolver multiplies by that object's `matrix_world`, mirrors X first if `mirror_x` (specs 01 and 02 mirror the left-side views for the right side), and fails loudly if the frame object is missing.

**Shared reference-crop presets** (`presets/ref.json`, hero camera, DOF on; the boxes reproduce the crop files exactly):

| Preset | Border (px) | Scale | Output | Matches |
|---|---|---|---|---|
| `ref.full` | full frame | 1 | 1672 × 941 | `reference_full.png` |
| `ref.soldier_full` | (580,20)–(1020,935) | 2 | 880 × 1830 | `crop_soldier_full.png` |
| `ref.head_face` | (715,30)–(885,200) | 5 | 850 × 850 | `crop_head_face.png` |
| `ref.torso_vest` | (630,140)–(990,490) | 3 | 1080 × 1050 | `crop_torso_vest.png` |
| `ref.arm_R` | (600,170)–(770,490) | 3 | 510 × 960 | `crop_arm_right_viewerleft.png` |
| `ref.arm_L` | (850,170)–(1000,490) | 3 | 450 × 960 | `crop_arm_left_viewerright.png` |
| `ref.hands_rifle` | (630,230)–(950,570) | 3 | 960 × 1020 | `crop_hands_rifle.png` |
| `ref.belt_hips` | (630,410)–(990,630) | 3 | 1080 × 660 | `crop_belt_hips.png` |
| `ref.legs_knees` | (630,550)–(990,830) | 3 | 1080 × 840 | `crop_legs_knees.png` |
| `ref.boots_feet` | (610,750)–(1010,935) | 3 | 1200 × 555 | `crop_boots_feet.png` |
| `hero.alt50` | full frame, camera (0, −4.91, 0.59), 50 mm, f/1.6 | 1 | 1672 × 941 | sensitivity only (D5) |

Part views whose box is identical to a crop file (05 V6, 06 V1, 09 V1–V3, 10 V1–V4, 11 V6, 12 V1–V4, 13 V1, 14 V1–V2) are stored as aliases of the matching `ref.*` preset; views with their own box (02 V1 (610,750)–(790,935), 02 V2 (860,750)–(1010,935), 04 V6 (690,100)–(1000,520), 07 V1 (725,0)–(895,170)) are `hero` presets with that border. Spec 03 V5's "hero camera at 1024 × 1536" cannot change the aspect without changing the framing and must be restated as a border (§10.1).

**Catalogue of part presets** (98 views; each part writes its own JSON from its §1.3 when it is built; `camera.py --lint` checks every id resolves):

| Spec | Views | Frame objects the part must create | Special types |
|---|---|---|---|
| 01 foot | V1–V7 | `Frame.Foot.L/R` (frame F) | `mirror_x`, `ortho` measurement variants, floor hidden for V4 |
| 02 boots | V1–V7 | `Frame.Boot.L/R` (frame B) | V3 looking +Z (`up` = +Y) |
| 03 legs | V1–V6 | W | V6 placed along the patella facing direction (`look_at` from data) |
| 04 torso | V1–V7 | W | V6 hero border (690,100)–(1000,520) ×3 |
| 05 arms | V1–V7 | `Frame.Hand.L/R` (frame H) | V6 = `ref.arm_R` + `ref.arm_L` |
| 06 head | V1–V6 | `Head.Anchor.*` | V3–V6 `ray` |
| 07 hair | V1–V6 | `Frame.Head` (spec 07's head frame; named apart from the hand frame) | V1 border (725,0)–(895,170) ×5; V3 `up` = −Y, `film_transparent` |
| 08 rig | V1–V7 | W | V7 `turntable` n 8, radius 3200, height 1000, 50 mm |
| 09 trousers | V1–V8 | W | V1–V3 = `ref.legs_knees`, `ref.belt_hips`, `ref.boots_feet` |
| 10 shirt | V1–V8 | W | V1–V4 = `ref.torso_vest`, `ref.head_face`, `ref.arm_R`, `ref.arm_L` |
| 11 gloves | V1–V7 | `Frame.Hand.L/R` | V1–V2 shared with spec 05 |
| 12 armour | V1–V12 | piece Empties | V12 `turntable` n 4, el 25°, radius 600, 60 mm, `orbit_camera` |
| 13 carrier | V1–V9 | W (targets relative to `Carrier.Root`) | V9 `turntable` n 4, el 25°, radius 700, 60 mm |
| 14 belt | V1–V8 | `RigR.anchor`, `RigL.anchor`, `PouchR.anchor`, `Belt.anchor.CF` | anchored targets |
| 17 scene | S1–S6, `p17.V7.probe` | — | §1.3 |

### 4.4 Lights (all `normalize = True`, `use_shadow = True`, MIS on; aimed by Track To at Empties `<light>.Target`)

| Object | Type, size | Location (m) | Target (m) | Colour | Nominal power | Calibration bounds | Group |
|---|---|---|---|---|---|---|---|
| `Scene.Light.R.Key` | AREA SQUARE 1.50 m, spread 180° | (−1.70, −2.00, 3.60) | (0, 0, 1.25) | `use_temperature`, 4500 K | 800 W | 400–1600 W; 4200–4800 K; spread 60–180° (a grid) | key |
| `Scene.Light.L.Cool` | AREA SQUARE 3.00 m | (3.20, 0.60, 3.60) | (0, 0, 1.00) | colour (0.55, 0.76, 1.00) | 600 W | 300–1200 W; each channel ±10 % | cool |
| `Scene.Light.R.Pool` | SPOT, radius 0.075 m, `spot_size` 26°, `spot_blend` 0.80, `use_soft_falloff` | (−0.77, −1.69, 4.38) | (−0.17, −0.40, 0.00) | 4500 K | 500 W | 100–1500 W; 3500–5000 K | pool |
| `Scene.Light.L.Kicker` | AREA SQUARE 1.0 m | (1.80, 3.00, 3.80) | (0, 0, 1.00) | as cool | 0 (off) | 0 to 12 % of the key's irradiance at the chest | kick |
| `Scene.Light.C.UnderFill` | AREA SQUARE 1.0 m, facing +Z (rot X 180°) | (−0.30, −1.00, 0.05) | — | 4500 K | 0 (off) | 0 to 8 %; must keep A5 ≤ #12100c | under |

The positions come from light = chest + d (sin φ cos e, −cos φ cos e, sin e) with chest (0, 0, 1.30): key φ −40°, e 42°, d 3.5; cool φ +100°, e 35°, d 4.0 (consolidated §8). The pool is placed at elevation 72° and azimuth 25° toward −X from its target at 4.6 m (D2). Irradiance check at the chest after calibration: key : cool : world ≈ 1.3 : 1 : 0.05.

### 4.5 Floor, joints and trench
* `Scene.Floor.C.Slab`: box 30.0 × 30.0 × 0.20 m, top face at Z 0, centred at (3.0, 1.0, −0.10) (X −12…+18, Y −14…+16). One material; no UVs (world-space mapping, §5.1); ≈ 40 faces after the Boolean.
* Trench cutter: box 0.30 × 1.60 × 0.30 m at (1.01, 1.83, −0.10), rotation Z 55° (long axis along family A). `Scene.Floor.L.Trench.Channel`: a U-section of 5 mm galvanised sheet, 300 inner width, 250 deep, along the cutter. `Scene.Floor.L.Trench.Frame.A/B`: 40 × 40 × 4 mm angles along both long edges, top flush with Z 0. `Scene.Floor.L.Trench.Grate.01/02`: two 0.298 × 0.796 × 0.025 m plates (Solidify), top 2 mm below Z 0, 4 mm gap between them; slots 12 × 100 mm at 25 mm pitch in rows 120 mm apart are cut in the shader (§5.1), so the dark channel shows through.
* Joints and slabs are shader features, not geometry (each joint is 2–3 px wide at the feet; bump catches the grazing light at the scales the presets reach): family B at Y = 0.95 + 1.5 k; family A at 55° through (−1.05, 0.70) with X-pitch 1.5 m and a per-line seeded jitter ±0.10 m; each line's width = 6 mm core + 0–5 mm spall on each side from a 40 mm noise.

### 4.6 Stand-in set (`set.json` → builders; ≤ 80 k triangles and ≤ 150 objects in all)

| Element (objects) | Builder and tools | Dimensions and detail | Placement (§2.4) |
|---|---|---|---|
| Far wall `Set.C.Shell.FarWall` | plane | 30 × 9 m; trapezoidal cladding as shader bump (200 mm pitch, 35 mm rib) | Y 16.0 |
| Side walls `Set.R/L.Shell.Wall`, ceiling `Set.C.Shell.Ceiling` | planes | dark; reflections only | X −12 / +18; H 9.0 |
| Trusses `Set.C.Shell.Truss.01–04` | `build_truss`: two 0.20 m box chords + Ø100 diagonals every 1.6 m (Array) | span X −12…+18, chords at H 6.2 and 7.8 | Y 4, 8, 12, 15.5 |
| Transit cases `Set.R.Stack.Case.01–07` | `build_case`: box, Bevel 25 mm (3 segments), lid groove (inset band 10 mm, 4 mm deep at 70 % height), 2 latches 60 × 20 × 80, 2 side handles (torus halves), label plate 100 × 140 × 1, corner bumpers | lower tier 1.10 × 0.60 × 0.70 (×3 visible + 1 behind the UI), upper tier 0.80 × 0.50 × 0.45 (×3) | front Y 5.0, X −3.50…−1.05 |
| Helmets `Set.R.Stack.Helmet.01–06` | `build_helmet`: UV sphere 32 × 16 scaled (0.140, 0.115, 0.190) m, cut below Z 0, high-cut ear notches (Boolean), NVG shroud 70 × 25 × 40, two rails 120 × 20 × 10, Subdivision 1, Bevel 2 mm; ≈ 2.5 k tris | colours black, grey with visor strip, olive-gold, tan | X −1.80, −1.55, −1.30, −1.10 (+2 behind the UI) on the upper tier, yaw ±25° |
| Racks `Set.R.Rack.*` | `build_rack`: 90 × 70 uprights, 100 × 50 box beams at 1.5 / 2.5 / 3.5 m, diagonal braces; 8 hanging vests and uniforms `Set.R.Rack.Gear.01–08` (rounded boxes 0.45 × 0.12 × 0.60, Displace 30 mm noise, on hooks) | 2 bays of 1.2 m, depth 0.9 | X −2.2…−1.0, Y 6.5–7.4 |
| Pillar `Set.R.Pillar` + `Set.R.Pillar.Lamp` | box 0.40 × 0.40 × 9.0 m; lamp housing 160 × 120 × 90 with the emitter on its −Y face | — | (−1.55, 7.5); lamp H 3.45 |
| Columns `Set.R.Column.01–02` | `build_ibeam` HEA 300 (flanges 300 × 14, web 8.5) | 9.0 m | (−1.00, 6.0), (−0.75, 9.0) |
| Hull `Set.L.Ship.Hull` | `build_hull`: six chamfered-octagon sections bridged along the axis (`bmesh.ops.bridge_loops`): s 0 m 1.6 × 1.8 (nose face, centre H 1.9), 1.2 m 2.8 × 3.2, 2.5–8.0 m 3.5 × 4.0 (belly H 0.8, top 4.8), 9.3 m 3.2 × 3.6; Bevel 40 mm; four inset side panels (inset 50 mm, depth 30 mm); belly gear bay (inset 1.4 × 0.9, depth 0.25); ≈ 8 k tris | panel seams in the shader | nose (0.85, 6.5), axis 48° |
| Landing gear `Set.L.Ship.Gear.F/M` | Ø220 struts, Ø600 × 300 wheels, a 0.5 m skid plate | — | at s 2.0 and 6.5 m along the axis |
| Stair `Set.L.Stair.*` | `build_stair`: two C-channel stringers 250 × 60, 15 grating treads 1200 × 240 × 40, posts every 1.0 m, Ø40 rails at 900 (Curve bevel), LED strips `Set.L.Stair.Strip.A/B` (12 × 6 mm emissive along each stringer top), base lamps `Set.L.Stair.BaseLamp.A/B`, four Ø200 casters | 15 risers × 200, going 240, pitch 40°, width 1200 | base front centre (4.55, 10.4, 0), run azimuth 40° |
| Orange tube `Set.L.TubeLamp` | Ø40 post 1.0 m + 340 × Ø30 tube emitter | — | (3.70, 10.50, 1.00) |
| Red case `Set.L.RedCase` | rounded box radius 20, three drawer grooves, a handle | 0.55 × 0.45 × 0.60 | (2.85, 2.40, 0) |
| Far crates `Set.C.FarCrates.01–10` | boxes Bevel 15 mm, yaw ±5° | 1.2 × 1.0 × 1.0–1.2, some stacked to 1.6 m | rows at Y 12.5 and 13.4, X −0.9…+3.7 |
| Ceiling lamps `Set.C.CeilingLamp.01–16` | housing cylinder Ø250 × 120 + emitter sphere r 30 mm below | — | §2.4 grid, H 5.8 |
| Batten, edge lamp, far panel, far strips, hull lamps, window | emitter planes or tubes with dark housings | sizes in §2.4 | §2.4 |

**Ray visibility classes** (`visible_*` object properties):

| Class | camera | diffuse | glossy | transmission | volume | shadow |
|---|---|---|---|---|---|---|
| Shell (walls, ceiling, trusses) | yes | **no** | yes | yes | no | **no** |
| Props (cases, hull, stair, crates…) | yes | yes | yes | yes | yes | yes |
| Emitters | yes | yes | yes | yes | yes | **no** |
| Floor and trench | yes | yes | yes | yes | yes | yes |

Hiding the shell from diffuse rays lets the world act as the ambient control (D11); it cannot change any shadow on the figure because the shell casts none.

### 4.7 Calibration rig, anchors and proxy
* `Cal.Card18` (100 × 150 mm, Lambertian 0.18), `Cal.BallGrey` (Ø100, 0.18 matte), `Cal.BallChrome` (Ø100, metallic), `Cal.Chart` (ColorChecker card 279.4 × 215.9 × 2 mm, 24 patches of 40 mm with 4 mm black gaps, colours from §3.5). In `LookDev` they sit on a stand at (0, 0, 1.00); in `Hero` the balls form `Cal.Probe` at the chest position (0, −0.40, 1.30), used only by `p17.V7.probe` with `Character` hidden.
* **Anchors** for the figure patches are Empties `Cal.Anchor.<ID>` (P1–P4, A1–A6, C1–C3), created by the owning parts at the semantic location of each patch on the evaluated surface, 1 mm out along the normal, parented to the nearest deforming bone: spec 06 owns P1, P2, A1–A5 (temple, cheek, forehead and under-jaw points); spec 13 owns P3 and C1 (admin panel top face, 15 mm below its upper edge, 10 mm toward his left of its centre); spec 09 owns P4, A6, C2, C3 (lateral left shin 280 mm above the floor at the outer seam; right shin front 300 mm up; right thigh front 560 mm up). Floor patches are fixed world points from `camproj.floor_point()`: P5 (−0.01, +0.32, 0), F1 (−0.01, −0.41, 0), F2 (−0.50, −0.36, 0), F3 (+0.92, −0.20, 0), F4 (+1.41, +6.33, 0).
* `Cal.Proxy` (`--proxy`, before the character exists): the MPFB default male (research B) at the origin in the closest available pose, with spec 06's skin albedo on the head and a Lambertian 0.05 grey on the rest; only P1, P2, A1–A5 are scored with it.

### 4.8 Look-dev scene (`lookdev.py`)
* `LookDev.Stage.Cyc`: an 18 % grey cyclorama: floor from Y −3.0 to +1.0, a 1.0 m cove radius (16 segments), wall at Y +2.0 up to Z 4.0, extruded 6.0 m along X; Subdivision 1.
* `LookDev.Rig`: an Empty at the subject centre that carries the three lights; its scale s = (subject bounding-sphere radius)/0.5 m and the light powers are multiplied by s², so irradiance at the subject is the same for a 100 mm swatch (s 0.2, key at 0.6 m, as spec 11 asked) and the full figure (s ≈ 2, key at 6 m).
* Lights, all pure white (`use_temperature` off, colour (1, 1, 1)) so a neutral albedo renders neutral: `LookDev.Light.R.Key` AREA 1.0 m at azimuth 35° toward −X, elevation 45°, distance 3.0 m (× s); `LookDev.Light.L.Fill` AREA 1.5 m at azimuth 60° toward +X, elevation 20°, 3.5 m, one quarter of the key's irradiance; `LookDev.Light.C.Rim` AREA 0.5 × 2.0 m at azimuth 160°, elevation 30°, 3.0 m, half the key. The key is calibrated so `Cal.Card18` facing it reads scene-linear 0.180 ± 0.002.
* `LookDev.Turntable`: an Empty at the origin; `rotate_subject` mode (default) parents the subject to it and rotates it 360°/n per frame under fixed lights; `orbit_camera` mode (specs 12, 13) moves the camera and the light rig together. Camera `LookDev.Cam`: 85 mm, distance = 1.15 × (bounding-sphere radius)/tan(VFOV/2); full figure: 1080 × 1350 portrait, VFOV 29.6°, distance 4.04 m, target (0, 0, 0.93), elevation 10°, 8 views.
* `LookDev.Swatch`: a 100 × 100 mm plane at (−0.06, 0, 1.00) beside `Cal.Card18` at (+0.06, 0, 1.00), both facing the camera at (0, −0.60, 1.00), 100 mm lens, the key 45° off-axis so no specular peak reaches the camera.

### 4.9 Render tiers (`render.py --tier`; time budgets from research C: ≈ 1 MP·spp/s shared, 2 idle)

| Tier | Engine | Resolution | Samples | Adaptive | Denoise | Passes | Budget here |
|---|---|---|---|---|---|---|---|
| `form` | Workbench: `MATCAP` `clay_studio.exr`, `color_type 'SINGLE'` 0.8, cavity `BOTH` ridge/valley 1.0, no shadows, `render_aa '8'` | preset | — | — | — | Combined | ≈ 5 s with start-up |
| `look` | Cycles | 50 % | 16 | 0.05 | OIDN `FAST` | Combined | 10–25 s |
| `eval` | Cycles | 100 % | 64 (min 16) | 0.02 | OIDN `HIGH`, prefilter `ACCURATE`, albedo + normal | Combined, Mist, Z, Cryptomatte object and material (depth 6), Object Index | S1 2–4 min; 800² closeup 20–40 s; ×5 head crop with skin SSS 4–8 min |
| `cal` | Cycles | 100 % | 128 fixed | off | Combined only; `denoising_store_passes` on | eval passes + 8 light groups + Diffuse/Glossy Color | 4–7 min |
| `final` | Cycles | 200 % (3344 × 1882) or 3840 × 2160 | 512 (min 64) | 0.005 | OIDN `HIGH` | as eval | GPU machine 2–5 min; on this box 40–90 min, avoid |

Common Cycles settings: device CPU; `threads_mode 'FIXED'`, `threads 3` while another agent shares the box (`SGT_THREADS`), else `'AUTO'`; one render at a time; `use_light_tree True`; `seed 17`, `use_animated_seed False`; Blackman-Harris filter 1.5 px; `sample_clamp_direct 0`, `sample_clamp_indirect 5` (10 for `final`); bounces total 12, diffuse 4, glossy 4, transmission 12, volume 0 (2 with volume haze), transparent 32; caustics reflective and refractive off, `blur_glossy 1.0` (spec 06 may switch on MNEE with `is_caustics_light` on key and cool); `use_persistent_data True` when a script renders several presets; path guiding off pending a test (§10.2 Q7); `film_exposure 1.0`. Outputs: 16-bit PNG after the view transform, plus multilayer EXR (half for `eval`, float for `cal`, ZIP), named `renders/<part>/<preset>_<tier>.{png,exr}` with a JSON sidecar (preset, tier, seed, samples, wall time, Blender build hash, git commit, light-solution id).

### 4.10 Light groups, light linking and shadow linking (`scene.py`)
Light groups (one render gives every light's contribution separately; superposition is exact in RGB rendering):
```python
vl = hero.view_layers[0]
for g in ('key', 'cool', 'pool', 'kick', 'under', 'world', 'set', 'char'):
    if g not in vl.lightgroups: vl.lightgroups.add(name=g)
bpy.data.objects['Scene.Light.R.Key'].lightgroup = 'key'      # ... one line per light
hero.world.lightgroup = 'world'
for o in set_emitters: o.lightgroup = 'set'                   # character emissives (strobe) -> 'char'
```
Check on every `cal` render: Σ groups equals the noisy Combined within 1 % per channel at the patches (an emitter left without a group breaks the solve).

Linking helper (Blender 4.5: the per-item `light_linking` states are index-parallel to `collection.objects` and `collection.children`; they support no name lookup and no back-reference):
```python
def link_set(name, objs=(), colls=(), state='INCLUDE'):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)   # not linked to the scene
    for o in objs:
        if o.name not in c.objects: c.objects.link(o)
        c.collection_objects[list(c.objects).index(o)].light_linking.link_state = state
    for ch in colls:
        if ch.name not in c.children: c.children.link(ch)
        c.collection_children[list(c.children).index(ch)].light_linking.link_state = state
    return c
```
Uses (none of them in a hero render):
1. `--pool-link` diagnostic: `pool.light_linking.receiver_collection = link_set('Link.Pool.FloorOnly', objs=[slab])` reproduces the analysts' floor-only pool for an A/B picture.
2. `refmatch` render for P5 and for floor-only calibration (the only use of shadow linking): the key is split so the floor is lit without the character's key shadow while the figure keeps every self-shadow:
```python
kf = key.copy(); kf.name = 'Scene.Light.R.Key.FloorOnly'; hero.collection.objects.link(kf)   # shares key.data
key.light_linking.receiver_collection = link_set('Link.Key.NotFloor', objs=[slab], state='EXCLUDE')
kf.light_linking.receiver_collection = link_set('Link.Key.FloorOnly', objs=[slab], state='INCLUDE')
kf.light_linking.blocker_collection = link_set('Link.Key.NoCharShadow', colls=[char_coll], state='EXCLUDE')
```
3. `noshadow` diagnostic for criterion 8 and the `shadow_key` mask: as `refmatch` with every light split the same way.

`scene.py --selftest-linking` renders a 64 × 64 cube-over-plane scene for each variant at 16 spp and asserts the shadow under the cube is present (physical), absent (`refmatch` floor) and the cube's own shading unchanged (difference < 1 %), because the INCLUDE/EXCLUDE semantics of a collection holding only excluded items is easy to get wrong.

### 4.11 Masks (`masks.py`)
* **Render masks** from the `eval` EXR's Cryptomatte object layers (read with OpenImageIO inside Blender's Python, which ships it): one 8-bit PNG per object-name pattern, e.g. `Boot.*`, `Trousers.*`; Object Index as a fallback.
* **Reference masks** in `ref/masks/` from recipes in `ref/masks/recipes.json`: `soldier_full` from the existing rembg u2net matte (`assets/ai/rembg_out/soldier_full_u2net_mask.png`, pasted back at (580,20) scale ½); part masks as a polygon ∩ luminance/colour threshold − exclusions (spec 02's boot recipe: lum < 110 inside the boot boxes, minus the reflection below y 896/908 and the cuff above y 806; spec 09's trousers fallback; spec 12 supplies its armour polygons). Masks are generated once, committed (small PNGs), and drawn by the overlay.

### 4.12 Verification overlay (`overlay.py`, system `python3 -I`, PIL + numpy)
Inputs: a graded render, the reference, a preset (to map border and scale), `landmarks.json` (spec 08 §8.3 targets and tolerances, plus the §2.1 guide lines), optional measured landmarks from `rig_metrics.py`, `patches.json`, `ui_mask.json`, masks. Outputs per preset, in `renders/<part>/overlay/`:
* `_blend50.png` (50 % mix), `_diff.png` (|render − reference| × 4, UI hatched grey), `_edges.png` (reference Sobel edges in cyan on the render, render edges in magenta on the reference), `_swipe.png` (left half render, right half reference, white split line; a second with a horizontal split), `_flicker.gif` (two frames, 500 ms each).
* `_targets.png`: horizontal guides at y 20 (skull top), 77 (eyes), 616 (horizon, dashed grey), 690 (far floor line, grey), 895 and 907 (soles); the vertical stance line x 830 with a ±6 px band; every spec-08 landmark as a white cross with a 1 px black outline and its tolerance circle; measured positions as dots coloured by side (his right #ff5a3c, his left #3cff8a, centre #ffd23c, matching spec 08's diagnostics) with yellow error vectors and pixel labels; patch boxes labelled with ΔE00 (green ≤ tolerance, red above); a 100 mm scale bar at the figure's depth (47.2 px); masks hatched. Drawn at the preset's scale with `ImageFont.load_default(size=14 × scale)`.
* `_report.json`: landmark errors, patch ΔE00 and ΔL*, grading statistics (§2.5 definitions), floor and background checks, pass or fail per §1.4 item.

### 4.13 Deliverables and export (`deliver.py`)
* **Packed .blend**: append and make `Character` local, `bpy.ops.file.make_paths_relative()`, `bpy.ops.file.pack_all()`, save `deliver/sgt_morgan_eval_<date>.blend` with `compress=True` (expect 0.6–1.5 GB with 4K floor maps and hair curves). Not committed; where it lives is §10.2 Q5.
* **Game glTF**: spec 08 §7.6 owns `export/sgt_morgan.glb` (wrapper `Export.Root` rotated Z 180°, scale **1800/1855 = 0.97035**, Y-up, 4 influences, morph targets, `export_apply False`). `deliver.py` only re-imports it into an empty scene and checks: rest height 1800 ± 2 mm; the figure faces glTF −Z; the bone count; and that the hero pose, rendered through the hero camera scaled by 0.97035 about the origin, overlays S1 within 2 px (proving export and scene agree).
* **Presentation glTF** `export/sgt_morgan_presentation.glb`: the posed hero as static meshes (modifiers applied, no rig), plus with `--with-set` the floor and stand-in set, the hero camera and the key, cool and pool lights: `export_scene.gltf(export_format='GLB', use_selection=True, export_yup=True, export_apply=True, export_cameras=True, export_lights=True, export_import_convert_lighting_mode='SPEC', export_image_format='AUTO', export_jpeg_quality=90, export_draco_mesh_compression_enable=False, export_materials='EXPORT')` under the same 0.97035 wrapper, for viewing in a glTF viewer or Godot.
* **Renders** in `deliver/renders/`: `hero_1672x941.png` (graded) and its ungraded twin; `hero_3344x1882.png`; `hero_3840x2160.png` (same horizontal field of view; vertical 0.05 % wider, 0.5 px at 941); `compare_hero.png` (reference | render side by side, same size) and `_flicker.gif`; the ten `ref.*` crops; the look-dev turntable (8 views and a contact sheet); `calibration.png` (patch boxes with ΔE) and `calibration.json`; `render_report.json`. The latest `renders/eval/*.png` are committed (CLAUDE.md rule 6).

---

### 4.14 First build on Jeff's workstation (2026-10-10): what changed, what was found

Built under the scope note: `camproj.py`, `camera.py`, `render.py`, `scene.py`, `grade.py` (+ `grade.json`), a minimal `masks.py` (+ `ui_mask.json`), the registry `presets/ref.json`, `p17.json`, `p01.json`, `p02.json` (50 presets), and spec 18's `scripts/tools/sheet.py`. Every script also runs from a plain Python and relaunches itself in Blender (`python scripts/eval/render.py --preset ref.boots_feet --tier eval`).

**Checked.** `camproj` agrees with Blender's own projection within 0.0006 px (hero, crops, look-at cameras); the equivalent crop camera matches the render-border path (IoU 1.0000, centroids within 0.005 px); the in-Blender grade equals the same grade in numpy on the 16-bit file; `camera.py --lint` is clean; the scene rebuilds idempotently. On a stand-in MPFB human (1.729 m, A-pose) the floor contact lands on the reference's sole rows (toes y ≈ 912 against 895/907) and the figure is centred on x 836.

**Timings (RTX 3050, OptiX, OIDN on the GPU).** `form` 0.9 s for the first render in a process, then 0.03–0.05 s per crop; `look` 0.9–1.1 s; `eval` hero 1672 × 941 at 64 spp 3.95 s (≈ 5.3 s with the 16-bit PNG, EXR and grade), boots crop 3.7–3.9 s; `cal` 450 × 555 2.4 s; a whole command ≈ 3.2 s (`form`) to 7.7 s (`eval`) including Blender's start.

**Deviations from §4.**
1. Crops and other non-hero views use a second camera, `Scene.Cam.Preset`; `Scene.Cam.Hero` is never changed.
2. Depth of field is off for every hero preset, the `ref.*` crops included (scope note). If it returns, the crop camera scales the f-number by the lens ratio to keep the aperture.
3. Hero renders are transparent, graded, then laid over a flat backdrop (31.4, 32.6, 32.1), measured by `grade.py --measure-backdrop` on strips beside the figure above the horizon.
4. The `form` tier uses the Standard view transform, hides the floor and keeps a transparent background; `--aa FXAA` for sweeps.
5. Files: `<preset>_<tier>.png` is the graded 8-bit image, with `_ungraded.png` (16-bit), `.exr` and `.json` beside it, in `renders/<NN_part>/` (`renders/17_scene/` for this spec's own and the `ref.*` presets).
6. Only the key, cool and world light groups exist; the kicker and under fill (both 0 W here) are not built.
7. The floor is a plain 30 m plane with uniform §3.4 values; no maps, no slab.
8. Registry keys added: `alias`, `sides` (`{side}`/`{other}`), `hide`, `mask`, `form`, `note`. `p01.json` and `p02.json` were written ahead of their parts; each part still owns and revises its own file. `p01.V6` points at `p02.V1`/`V2` at ×3; `p01.V7` is a visibility variant, not a preset; `p01.V1o`–`V4o` add spec 01's ortho measurement views; `hero.alt50` is a look-at preset; the `p17.V7` probe framing is provisional; turntables orbit the camera only.
9. Look-dev presets render in the hero scene for `form`; Cycles tiers refuse until `--scene hero` is given. Reference crops are cut with PIL's LANCZOS filter, which reproduces `ref/crop_*.png` pixel for pixel.
10. `masks.py` covers the boot masks, the UI mask and the full-figure mask from the rembg matte, which is not yet on the workstation (so full-figure presets have no cyan edge); scratch masks go to `cache/masks/`, nothing to `ref/masks/` yet.

**Findings.**
* **The nominal lights are 3–5 × too bright.** Floor patches read F3 163 (reference 53), F2 185 (124), far floor 104 (37); lit skin comes out near white. Calibration (§8.2) will have to take the key below its 400 W lower bound (a rough estimate is 250–400 W for the cheek patch), so the §4.4 bounds are provisional until stage A runs. Not tuned now: stage A needs a real head, and nothing in the foot and boot work depends on absolute exposure.
* **GPU renders are not bit-identical.** Two `eval` renders on OptiX differ by 1/255 in 1.7 % of pixels, so item 10 of §1.4 holds on the CPU only; on the GPU, reproducibility means within 1/255 on under 2 % of pixels, and determinism checks that need bit identity render on the CPU (`SGT_DEVICE=CPU`).
* **Medial views look across the other foot.** Spec 01 V2 and spec 02 V7 put the camera beyond the other foot or boot. `p02.V7` hides the other boot; `p01.V2` cannot, both feet being one body mesh, so part 01 must isolate the foot it renders (a mask or a temporary split).
* The stand-in is the MPFB default with gender 1.0, ankles at ±0.198 m, moved +0.0149 m in Y to centre them; skin colour above the neck, 0.05 grey below, no subsurface.

**Left under the scope note.** The LookDev scene and its S6 view; `colour.py` and `calibrate.py` (floor stage B, light stage A, anchors, `lights_solution.json`); `overlay.py` (landmarks, patches, grading statistics); Cryptomatte render masks, `recipes.json` and the committed `ref/masks`; the light-linking diagnostics, `--assert-hero` and `scene.py --selftest`; the §5.1 floor maps; `render.py --part` writing overlays and a sheet itself; `deliver.py`.

## 5. Materials and textures

### 5.1 Floor `Scene.Mat.Floor.Concrete` (Principled BSDF; world-space mapping, no UVs)
* **Coordinates**: Geometry → Position (world). Sheared slab coordinates a = ((X + 1.05) − (Y − 0.70)·cot 55°)/1.5 (family A index, cot 55° = 0.7002) and b = (Y − 0.95)/1.5 (family B index); per-line jitter ±0.10 m added to a by line index from a White Noise of round(a).
* **Slab identity**: White Noise Texture (2D) of (floor a, floor b) → five randoms per slab: texture offset (0–3 m in X and Y), rotation (0/90/180/270°), tone × (0.96 + 0.08 r), roughness offset ±0.02. Every slab reads as its own pour and the 3 m texture never visibly repeats; the joints hide the discontinuities, as on a real floor.
* **Joint mask**: perpendicular distance to the nearest line, d_A = (0.5 − |frac(a) − 0.5|) × 1.229 m and d_B = (0.5 − |frac(b) − 0.5|) × 1.5 m; m = 1 − smoothstep(3 mm, 3 mm + spall, min(d_A, d_B)), spall 0–5 mm from a Noise of 40 mm scale.
* **Base Color**: `concrete_floor_worn_001` diffuse (Poly Haven, **4K** added to the manifest; 2K fallback), sRGB, sampled at the slab-transformed coordinates / 3.0 m → × tint (0.96, 1.00, 1.05) → × k_f (albedo scale; start 1.33, which brings the map's linear mean 0.09 to 0.12; solved in [0.67, 3.3] so the albedo stays in [0.06, 0.30]) → × mottle (Noise 4D, scale 1/1.0 m, detail 3, mapped 0.85–1.15) → × slab tone → joints mixed to filler #222326 by m → stains: oil (Voronoi F1, cells 0.4 m, threshold 0.15, colour × 0.70), tug marks (Noise stretched 20 : 1 along Y, × 0.85), dust (Noise 2 m × 1.10, stronger within 1 m of the walls and inside joints).
* **Roughness**: `cgbookcase_PolishedConcrete01` roughness (Non-Color, mean 0.13) → Map Range 0.0–0.5 → 0.22–0.45; + slab offset; oil −0.08, tug marks −0.05, mopped bands −0.04 (Wave 0.6 m, 20 % coverage), dust +0.12; joints 0.70.
* **Normal**: PolishedConcrete01 normal (DirectX: green inverted with Separate/Combine Color) at strength 0.15 → Bump (Noise 600 /m, distance 0.3 mm, strength 0.05) → Bump (height −3 mm × m, the joint profile, strength 1.0).
* **Principled**: IOR 1.50, Specular IOR Level 0.5, Coat Weight 0.10, Coat Roughness 0.20, Coat IOR 1.50, Metallic 0, Sheen 0, Subsurface 0.
* **Texel density**: 4K over 3 m = 0.73 mm/texel, matching S2's 0.7 mm/px at the feet; the hero frame needs 2.1 mm/px horizontally.
* **Grate** `Scene.Mat.Floor.Grate`: galvanised steel, Metallic 1.0, Base linear (0.55, 0.56, 0.57), Roughness 0.45 ± 0.10 (Noise), dust mixed in at 30 % on top faces; slot mask (12 × 100 mm, 25 mm pitch across the width, rows every 120 mm) drives a Mix Shader to Transparent BSDF so the dark channel shows. **Channel** `Scene.Mat.Floor.Channel`: albedo 0.02, roughness 0.8. **Frame angles**: as the grate without slots.

### 5.2 Set materials (Principled; start albedos are refined by calibration stage C, §8.2)

| Material | Objects | Start albedo | Roughness / metallic | Detail | Reference display target |
|---|---|---|---|---|---|
| `Set.Mat.Case.Dark` / `.Grey` | transit cases | #2c2f33 / #4a4743 | 0.55 / 0 | `Plastic012B` normal 0.3, dust on top faces | #404a53, #151b20 / #45413d |
| `Set.Mat.Label` | label plates | #c8c8c8 | 0.6 / 0 | worn-edge mask, faint text bars | #3d474e blurred |
| `Set.Mat.Helmet.Black/Grey/Olive/Tan` | helmets | #1d1c1a / #3a3c3e / #5b4a33 / #3f3629 | 0.45 / 0 | matte polyurea paint, edge scuffs | #22211f, #b4b8bc visor, #68543a, #483e2f |
| `Set.Mat.Steel.Dark` | racks, columns, trusses, stringers | #1e2124 | 0.50 / 0.3 | painted steel | #1a1a1a, #141b1d |
| `Set.Mat.Cloth.Gear` | hanging gear | #3a342a | 0.85 / 0 | — | #262219, #5a5144 lit |
| `Set.Mat.Pillar` | pillar | #4d463a | 0.70 / 0 | — | #5a5144 lit, #161614 |
| `Set.Mat.Hull` | hull, gear | #30343b | 0.45 / 0 | panel seams from a Brick Texture (1.2 × 0.6 m panels, 8 mm seams, colour × 0.5, bump −4 mm), grime gradient to the belly × 0.7 | #363737 upper, #1b1f28, #242627, nose #121619, belly #13171a |
| `Set.Mat.Stair.Tread` | treads, casters | #2a2b2f | 0.50 / 0.5 | open grating mask | #222328 |
| `Set.Mat.RedCase` | red case | #4a1a1a | 0.40 / 0 | powder coat | #443031 lit, #0f0707 shadow |
| `Set.Mat.Crate.Far` | far crates | #3b3f42 | 0.60 / 0 | — | #3b3f42, #1b2126 |
| `Set.Mat.Wall` | far and side walls | #4a4f52 | 0.70 / 0 | cladding bump; albedo × 1.0 below H 2.5 m falling to × 0.25 above H 5 m (soot and the shadow of the trusses), the two ends fitted separately in stage C | #4f5455 hazy at (1050,560); top of frame #121619 at (1000,40) |
| `Set.Mat.Ceiling` | ceiling | #15181b | 0.70 / 0 | — | #121619 at (1000,40) |

### 5.3 Emitters (Emission shader; colour normalised to max channel 1; Strength = in-focus scene-linear radiance)
Start strengths follow from the bokeh rule: a source s px wide under a c px defocus disc peaks at ≈ L·min(1, s/c) per axis, so L ≈ peak/(min(1, s_x/c)·min(1, s_y/c)), with the peak taken from the reference display value through `display_to_scene` (§5.6). Stage D (§8.2) refines each one.

| Object | Colour | s (px) / CoC (px) | Start strength | Reference peak / halo |
|---|---|---|---|---|
| `Set.C.CeilingLamp.*` | 7000 K | 6 × 6 / 11.3 | 10 | #e4f2fa / #bad8eb |
| `Set.L.CeilingTube`, `Set.L.EdgeLamp` | 7000 K | 7 × 10 / 10.9 | 5 | #e2edf2 / #c8d9e7 |
| `Set.L.Ship.Lamp.Landing` | 6500 K | 20 × 6 / 9.0 | 6 | #f2f2f2 / #dfe2e5 |
| `Set.L.Ship.Lamp.Warm` | 3500 K | 14 × 3 / 9.0 | 9 | #faecc8 / #eed1a3 |
| `Set.L.Ship.Window` | 4200 K | 54 × 18 / 9.6 | 1.7 | #e4d4c2 / #d0c0af |
| `Set.L.Ship.Lamp.Mid` | 7500 K | 3 × 4 / 10.2 | 35 | #edf6fb / #c0dced |
| `Set.L.Stair.Strip.A/B` | linear (0.62, 0.78, 1.00) | 1.7 wide / 10.2 | 5 | #c4dae7 / #9caec2 |
| `Set.L.Stair.BaseLamp.A/B` | 7500 K | 27 × 3 / 10.2 | 14 | #eff4fb / #c1dfef |
| `Set.L.TubeLamp` | 2600 K | 48 × 4 / 10.2 | 11 | core #f9f6f3, halo #f1e6d7, floor reflection #ead3b8 |
| `Set.R.Pillar.Lamp` | 4000 K | 18 × 12 / 9.1 | 3.8 | #f4f3ee / #eae1d3 |
| `Set.L.FarPanel` | linear (0.70, 0.85, 1.00) | 16 × 30 / 10.7 | 0.9 | #aec7d7 / #9fb6c8; floor streak F4 #98b0c5 |
| `Set.L.FarStrip.01–03` | 7500 K | 3 × 10 / 10.7 | 5.5 | #c5dbea |
| `Set.R.Stack.Helmet.02` visor | linear (0.80, 0.88, 1.00) | 13 × 3 / 7.6 | 2 | #b4b8bc |

### 5.4 Worlds
* **Hero** `Scene.World.Hangar`: Texture Coordinate (Generated) → Mapping (`POINT`, rotation Z −80°) → Environment Texture `assets/hdri/empty_warehouse_01_2k.hdr` (Linear interpolation, Equirectangular) → Mix Color `MULTIPLY` factor 1.0 with (0.60, 0.75, 1.00) → Background, strength 0.05 (solved 0.02–0.20) → World Output. Measured on the file: solid-angle mean luminance 0.775, peak 508, mean colour (1.00, 0.95, 0.87), brightest azimuth −35° unrotated (atan2(y, x) in Cycles' equirectangular convention), so −80° moves it to +45°, behind-right of the figure (+X, +Y). `cycles.sampling_method 'AUTOMATIC'`, `sample_map_resolution 1024`; `cycles_visibility.camera = False` (the set fills the frame; a gap renders black and shows up in the diff), diffuse, glossy, transmission and scatter on; light group `world`. Mist: `mist_settings.start 5.0`, `depth 15.0`, `falloff 'LINEAR'`.
* **Fallback** `--world gradient` (the lighting note's procedural sky): zenith (0.010, 0.020, 0.035), horizon (0.004, 0.006, 0.008), ground (0.012, 0.010, 0.008), strength 1.0.
* **LookDev** `LookDev.World.Studio`: `assets/hdri/autoshop_01_2k.hdr` (mean colour (0.91, 1.00, 0.95), brightest azimuth −19°) → Hue/Saturation/Value with Saturation 0.0 (the "grey studio HDRI") → Background strength 0.30, set so the shadow side of `Cal.BallGrey` reads 1/8 of its key side ± 20 %; Mapping rotation Z +106° puts its brightest region on the key side (azimuth −125°). The sign of both rotations is confirmed by the chrome ball in S6 and `p17.V7.probe`, not assumed.

### 5.5 Calibration and look-dev materials

| Material | Settings |
|---|---|
| `Cal.Mat.Grey18` (card) | Base linear 0.18, Roughness 1.0, Specular IOR Level 0.0 (pure Lambert, so the read-back is exact) |
| `Cal.Mat.GreyBall` | Base 0.18, Roughness 0.6, IOR 1.5 (a painted ball; shows a soft highlight) |
| `Cal.Mat.Chrome` | Metallic 1.0, Base linear 0.62, Roughness 0.02 |
| `Cal.Mat.Chart` | Base from `Cal.Img.Chart` (1100 × 850 px drawn by `lookdev.py` from §3.5, sRGB), Roughness 0.85, Specular IOR Level 0.3 |
| `LookDev.Mat.Cyc` | Base 0.18, Roughness 0.9, Specular IOR Level 0.25 |

### 5.6 Colour management, compositor and grade
* **View**: Hero `view_transform 'AgX'`, `look 'AgX - Medium High Contrast'` (the exact enum string in 4.5), exposure 0.0, gamma 1.0, `use_curve_mapping False`, `use_white_balance False`, display `'sRGB'`, `render.dither_intensity 0`. LookDev: `'AgX - Base Contrast'`. Never `'Standard'`.
* **Compositor** (scene-linear; `scene.use_nodes`, `scene.node_tree` in 4.5): Render Layers Image → Mix (`MIX`, factor = Mist × 0.40 through a Math `MULTIPLY`) with fog colour ≈ linear (0.043, 0.051, 0.060), computed at build time as `display_to_scene('#2c3238')` → Glare (`glare_type 'FOG_GLOW'`, `quality 'HIGH'`; sockets: Highlights Threshold 2.0, Highlights Smoothness 0.25, Strength 0.10, Size 0.06, Saturation 1.0, Tint white) → Composite. 4.5 turned the Glare settings into sockets with a relative Size [VERIFY its scale]; Strength and Size are therefore tuned on renders (§8.2 stage D) against the orange-lamp profile of §2.5, with `use_crop_to_border False` so a border render keeps the full canvas the glare is computed on.
* **Display grade** (`grade.py`, numpy; input D = the 16-bit PNG after AgX, 0–1; parameters in `grade.json`):
  1. Lift and gain in Blender's own LGG form, on display values: x = ((D − 1)(2 − lift) + 1) × gain, lift (0.985, 1.000, 1.025), gain (1.035, 1.000, 0.960), clamped to [0, 1].
  2. Saturation about Rec.709 luma: Y = 0.2126 R + 0.7152 G + 0.0722 B; x = Y + 0.92 (x − Y).
  3. Black crush: x = clamp((x − 0.02)/0.98, 0, 1).
  4. Quantise to 8 bits, round half up, no dither.
  The ungraded PNG is kept beside the graded one; only graded images are compared with the reference.
* **`colour.py`**: sRGB transfer; Lab (D65); CIEDE2000 (unit test: Sharma, Wu and Dalal's 34 pairs to 1e−4); `scene_to_display(rgb)` = OCIO processor ('Linear Rec.709' → display 'sRGB', view 'AgX', look override) then the grade; `display_to_scene(hex)` = Newton iteration on the 3-vector with a finite-difference Jacobian (≤ 20 steps, display tolerance 1e−4), valid for display values 3–250 (it clamps and warns outside). Inside Blender's Python it uses `PyOpenColorIO` directly; `colour.py --bake-lut` writes a 65³ LUT of the whole chain on a log2 shaper (−12 … +5 stops around 0.18) to `cache/agx_mhc_grade_65.npy` for system Python.

---

## 6. Fibres, simulation or dynamics
* Nothing is simulated in this part; the character's hair and cloth arrive baked (spec 18 order: simulate → bake → attach → render).
* **Haze**: the mist fog of §5.6 by default. `--haze volume` (GPU machine only) replaces it with a Principled Volume in a 30 × 30 × 9 m box `Set.C.Haze`: density 0.004 m⁻¹, anisotropy 0.3, colour (0.70, 0.80, 1.00), volume bounces 2. The two must agree on the hazy wall at (1050,560) within ΔE00 4 and on the far crates (#3b3f42) within ΔE00 6, otherwise the mist parameters are refitted to the volume render.
* **Optics** are render-time only: thin-lens depth of field (§3.1), glare (§5.6).
* **Turntable**: `LookDev.Turntable` rotation Z keyed at 360°·(frame − 1)/n with `LINEAR` interpolation, frames 1…n; the render harness renders frames, not an animation.
* Motion blur off, frame 1, seed 17, `use_animated_seed False`: every render is reproducible bit for bit on CPU OIDN.

---

## 7. Rigging and attachment
* **The character** arrives as the collection `Character` in `cache/character_hero.blend` (spec 18), already posed (spec 08 `Hero.Pose` baked), origin at the floor between the feet, facing −Y. `scene.py` links it into `Hero` and `LookDev` without moving it; nothing in the scene is parented to the character and no light follows it. A character that arrives offset is a spec 08 or spec 18 bug and fails the landmark overlay rather than being nudged here.
* **Frames and anchors read from the character** (owned by the parts, consumed here): `Frame.Foot.L/R` (01), `Frame.Boot.L/R` (02), `Frame.Hand.L/R` (05, 11), `Frame.Head` (07), `Head.Anchor.*` (06), `Carrier.Root` (13), `RigR.anchor`, `RigL.anchor`, `PouchR.anchor`, `Belt.anchor.CF` (14), and the patch anchors `Cal.Anchor.<ID>` of §4.7 (bone-parented, so they follow the hero pose). A missing patch anchor falls back to the reference pixel and is reported as "unanchored".
* **Focus**: `Scene.Cam.Focus` is a free Empty at (0, 0, 1.30); presets may focus on a character object instead (e.g. spec 06 on the right cornea).
* **Turntable subject**: a collection instance of `Character` (or of one part's sub-collection) parented to `LookDev.Turntable`, so no mesh data is duplicated.
* **Lights** sit in world space with Track To constraints on Empties in `Scene.Light`; the light rig of `LookDev` is parented to `LookDev.Rig` and scales with the subject (§4.8).

---

## 8. Evaluation protocol

### 8.1 Renders
* `scene.py --selftest` (≈ 1 min, character hidden): camera maths (§1.4 item 1) with a rendered 0.5 m floor test grid at the `look` tier; linking variants (§4.10; the semantics were confirmed on 4.5.14 with a 64 × 64 test while writing this spec: an EXCLUDE-only receiver collection removes the key from the floor alone, an EXCLUDE-only blocker collection removes the character's shadow while the character's own shading is unchanged); emitter re-projection (blob centroids of an emitters-only `look` render against §2.4).
* Scene acceptance: S1–S5 at `eval`, the `refmatch` and `noshadow` diagnostics of S1 at `eval`, S6 and `p17.V7.probe` (grey and chrome balls at the chest, character hidden) at `eval`; all through `grade.py` and `overlay.py`. With the full character S1 takes 2–4 min, S5 4–8 min (skin SSS), the rest under 1 min each; ≈ 15 min in all, run one at a time.
* Part renders: `render.py --part NN --tier form|eval` renders every preset of `presets/pNN.json`, writes overlays for the presets that name a reference crop, and a contact sheet `renders/<part>/sheet_<tier>.png`.

### 8.2 Calibration (`calibrate.py`; lights and floor are tuned, part materials never are)
* **Stage D, emitters** (no character needed): one `cal --set` render with one light group per emitter (≈ 20 groups) and `Character` hidden. Per emitter: peak (largest 3 × 3 mean within ±6 px of the expected centroid) and FWHM against the reference. Strength ← strength × (reference peak / rendered peak) in scene-linear (through `display_to_scene`); an FWHM error over 3 px resizes the emitter by the difference converted at its depth. Two iterations. Glare Strength and Size are then fitted on the orange lamp's radial profile (§2.5) by a 3 × 3 grid (Strength 0.05/0.10/0.20 × Size 0.04/0.06/0.09) of border renders (1300,500)–(1440,620) without crop, ≈ 15 s each.
* **Stage B, floor** (needs the floor; the proxy suffices): unknowns floor albedo scale k_f, pool power and pool CCT; targets F1, F2, F3 on the physical render and P5 on the `refmatch` render. Secant updates on two border renders per iteration (the S2 border and (1250,880)–(1350,940)), at most five iterations (≈ 3 min). Then F4: if the streak misses by more than ΔE00 8, shift the roughness map range by ±0.05 and repeat stage D for `Set.L.FarPanel` once.
* **Stage A, lights** (needs the head, or `Cal.Proxy`): one `cal` render. Each light-group pass is sampled with 5 × 5 means at the projected anchors A1–A5 (and P1, P2, P4 for the report). Unknowns: key power and CCT, cool power and a per-channel tint (±10 %), world strength, kicker and under-fill powers (≥ 0, within §4.4 bounds). Model: linear patch value = Σ_i g_i(θ) ⊙ L_i, where a CCT change is the per-channel ratio blackbody(T)/blackbody(4500 K) (exact in RGB rendering); haze from the Mist pass (≈ 0 on the figure); display = `scene_to_display`. Objective Σ w_p ΔE00² with w_p = 1/(1 + sd_p/4); Gauss–Newton in log-parameters with clamped bounds, ≤ 30 iterations, under 2 s. Output `scripts/eval/lights_solution.json` (versioned id, residual table), applied with `scene.py --apply-solution`.
* **Stage C, set albedos**: from an `eval` S1, for each set object (Cryptomatte mask ∩ not UI ∩ not `shadow_key`) the ratio of reference to render mean in scene-linear sets an albedo multiplier, clamped to ×[0.33, 3] per step and to albedo [0.01, 0.60]; two iterations. Emitters are excluded.
* **Stage E, grade** (only if §1.4 item 4 still fails after A–D): lift, gain and black point may move by up to ±50 % of their values to fit the band means; any change is logged in `grade.json`.
* **Order**: D → B → A → C → B again → acceptance renders. Stage A is re-run whenever a skin, cloth or carrier albedo changes. A patch that cannot be met inside the light bounds is reported against the material's owner (spec 06, 09 or 13) instead of pushing a light out of bounds; that is the guard against "brighter light × darker albedo" degeneracy, and the key is anchored on skin whose albedo spec 06 takes from real measurements.

### 8.3 Metrics (`overlay.py`, `calibrate.py`; all written to `renders/eval/p17_report.json`)

| Metric | Method | Pass |
|---|---|---|
| Camera self-test | `camproj` vs `world_to_camera_view`; grid horizon and seam slopes | §1.4 item 1 |
| Named patches | 5 × 5 mean at the anchor's projection (render) and at the pixel (reference), graded 8-bit, ΔE00 and ΔL* | P1 ≤ 5, P2 ≤ 3, P3 ≤ 5, P4 ≤ 4, P5 ≤ 6 (on `refmatch`); \|ΔL*\| ≤ 4 |
| Solve anchors | A1–A5 after stage A | ΔE00 ≤ 4 each |
| Material checks | A6, C1, C2, C3 | reported to specs 09 and 13 (their own tolerances) |
| Grading statistics | §2.5 definitions on the UI-masked frame | §1.4 item 4 |
| Floor seams | column-wise luminance minima, line fit | §1.4 item 5 |
| Pool radius | radial luminance profile about F1, half maximum → metres via `floor_point` | 0.6–0.7 m |
| Emitter blobs | lum > 150 connected components: centroid, FWHM along x and y, peak colour | §1.4 item 6; peak ΔE00 ≤ 6 |
| Helmets, belly, far floor line | edge widths at y 460; vertical-gradient maximum in x 1000–1400; floor/crate boundary at x 1000–1300 | §1.4 item 6 |
| Depth of field | 10–90 % edge rise across the crate-stack top (x 450–590, y 480–505); Laplacian variance in face (770–860 × 40–140), chest (760–840 × 210–300), right glove (690–752 × 325–400), boots (680–770 and 895–980 × 800–900) | 8 ± 1.5 px; ≥ 0.6 × reference |
| Physical shadow | mean floor luminance in `shadow_key`, physical / `noshadow` | ≤ 0.8 |
| Look-dev neutrality | mean a*, b* of the grey ball's lit hemisphere | \|a*\|, \|b*\| ≤ 1.0 |
| Chart | each patch normalised by the 18 % card (patch / card × 0.18, linear) → sRGB → ΔE00 against §3.5 | median ≤ 2, max ≤ 4 |
| Swatch read-back | `Cal.Mat.Grey18` on the swatch stage | 0.180 ± 0.004 |
| Reproducibility | the same preset twice, byte compare | identical |
| Time | JSON sidecars | §1.4 item 11 |

### 8.4 Critic questions (yes or no, with the view named)
1. S1 flicker: does anything jump between render and reference other than the declared deviations (the shadow wedge to the viewer's right of the legs, the higher hips, harder bokeh edges)?
2. S5: is the brightest skin on his right temple and brow, the nose shadow falling toward his left onto the upper lip, his right ear fully lit, his left cheek a cool grey, and the under-jaw black?
3. S1: does the steel-blue light wrap his whole left side from the pauldron to the shin, with no hard terminator and no hot rim?
4. S2: is the floor between and in front of the boots a warm pool, each boot mirrored as a soft dark smudge, a black contact line under each sole, and do the joints read as cut lines rather than painted ones?
5. S1 and S2: does the body shadow read as a natural soft shadow from a large source above his right shoulder, densest at the feet and fading with distance?
6. S3: are the helmets the right size, the crate stack the right height, and the background exactly as soft as the reference (no sharper, no blurrier)?
7. S4: are the hull, stair strips, orange lamp and far panel where the reference has them, with blobs of the same size and colour, and a cool streak on the floor below the far panel?
8. S1: are the blacks deep rather than milky, the highlights warm, the shadows faintly teal, the frame low-key overall?
9. S6: is the grey ball neutral, do the three look-dev lights appear in the chrome ball where expected, does the chart look right?
10. Any part preset: does it frame what its spec says, and does it render identically twice?

### 8.5 Failure modes and fixes

| Symptom | Cause | Fix |
|---|---|---|
| Every landmark off by the same offset | a second camera built elsewhere, or the half-pixel convention missed | only `camera.py` builds it; +0.5 rule (§4.3) |
| Horizon not at y 616 | degrees passed as radians, `sensor_fit 'AUTO'` | self-test |
| No floor shadow at all | a diagnostic's linking left on; `visible_shadow` off on a part | `scene.py --assert-hero` fails if any light has a linking collection |
| Pool burns the boot tops | spot too shallow, or its power solved from P5 on the physical render | D2 position; P5 only on `refmatch` |
| Face right but frame milky | world too strong or the grade skipped | A5, A6; `grade.py` in the chain |
| Face too warm or too cool at a bound | CCT bound reached: a skin albedo problem | report to spec 06; do not widen the bound |
| Lamp blobs too big | emitter sized as the blob instead of blob − CoC | §2.4 rule |
| Set element at the wrong place | camera-relative Z used as world Y | world Y = Z − 4.5 |
| Bloom on everything | threshold applied to display values | Highlights Threshold 2.0 in scene-linear |
| Haze fringe around the figure | mist of mixed pixels at the defocus boundary | accept ≤ 1 px; volume haze on the GPU machine |
| Fireflies on the floor | glossy paths to small emitters | clamp indirect 5, light tree on |
| Light groups do not sum to Combined | an emitter without a group (e.g. a part's strobe) | sum check; assign `char` |
| Grey ball tinted in look-dev | temperature left on, HDRI not desaturated | §4.8, §5.4 |
| Swatch albedo high on a glossy material | specular reaching the camera | key 45° off-axis; also report the Diffuse Color pass |
| Renders far over budget | two renders in parallel, SSS or hair dominating | one at a time, `threads 3`, tiers |

---

## 9. Build order, effort and risks

| # | Step | Tool | Run time | Authoring | Risk |
|---|---|---|---|---|---|
| 1 | `camproj.py`, `camera.py`, hero camera, self-test | maths, `bpy_extras` | 5 s | 3 h | low |
| 2 | Preset schema, resolver, `ref.json`, `p17.json`, lint | json, `mathutils` | 1 s | 5 h | medium: frames come from many parts |
| 3 | Floor, trench, floor shader (slab ids, joints, wear) | bmesh, Boolean, nodes | 10 s | 6 h | medium: node maths |
| 4 | Lights, world, light groups, linking self-test | `bpy` | 20 s | 4 h | low (semantics already confirmed) |
| 5 | Set builders, `set.json`, emitters, re-projection test | bmesh, modifiers | 15 s | 10 h | low |
| 6 | Compositor, `colour.py`, `grade.py`, LUT bake | OCIO, numpy | 2 s | 5 h | medium: 4.5 Glare sockets |
| 7 | `render.py` tiers and sidecars | `bpy` | — | 3 h | low |
| 8 | `overlay.py`, `masks.py` | PIL, OpenImageIO | 5 s per image | 6 h | low |
| 9 | LookDev scene, turntable, swatch stage, chart texture | `bpy`, PIL | 30 s | 4 h | low |
| 10 | `calibrate.py` stages A–E | numpy, OCIO | 10–20 min of renders | 8 h | high: reference inconsistencies |
| 11 | `deliver.py`, export checks, presentation glTF | glTF exporter | 2–5 min | 4 h | low |

Total ≈ 58 h of authoring. Milestones to commit: after 4 (camera, lights and floor rendering with the self-tests), after 8 (S1 with `Cal.Proxy` and its overlay), after 10 (calibrated scene), after 11 (deliverables). The scene can be built and calibrated for emitters, floor and set before any character part exists; stage A waits for spec 06.

Risks beyond the table: (1) the reference is internally inconsistent (a pool that would light the boots, a floor bright where a body shadow must fall), so some patches may be unreachable inside physical bounds; the report says so instead of bending the physics; (2) Blender 4.5's Glare node Size semantics are unverified, hence fitting by renders; (3) CPU contention with other agents makes the `cal` render 1.5–2× slower; run calibration alone or on the GPU machine (same seed, same results within noise); (4) the HDRI rotation signs are confirmed by the chrome ball, not by reasoning; (5) the stand-in hull may look crude in S4; it is 9–11 px out of focus, and Geometry Nodes greebles are added only if a critic asks.

---

## 10. Interfaces and open questions for the client

### 10.1 What each part gets from this scene, and what this scene needs from it

| Part | Spec 17 provides | Spec 17 needs |
|---|---|---|
| 01 Foot | `LookDev` (replaces "scene A"), presets with `mirror_x` and `ortho`, the hero lights | `Frame.Foot.L/R` |
| 02 Boots | `ref.boots_feet`, the floor and its boot reflections, `masks.py` recipes | `Frame.Boot.L/R`; the boot mask recipe already in spec 02 §8 |
| 03 Leg, 04 Torso, 10 Shirt | presets, `ref.*` aliases, `LookDev` | — |
| 05 Arms, 11 Gloves | presets in frame H, overlay hooks for the finger finders | `Frame.Hand.L/R` |
| 06 Head | `ref.head_face`, `ray` presets, the MNEE switch, S5, light solution | `Head.Anchor.*`; `Cal.Anchor.P1, P2, A1–A5`; final skin albedos |
| 07 Hair | presets with `up` and `film_transparent` | its head frame as `Frame.Head` |
| 08 Rig | `camera.py`, `landmarks.json` from its §8.3, the overlay | `rig_metrics.py` writing measured landmarks as `{name: [x, y]}` |
| 09 Trousers | `ref.legs_knees`, `ref.belt_hips`, `ref.boots_feet`; P4, A6, C2, C3 results | `Cal.Anchor.P4, A6, C2, C3`; its trouser mask recipe |
| 12 Armour | `turntable` in `orbit_camera` mode, `masks.py` | the armour polygons for `ref/masks/armour_*.png` |
| 13 Carrier | P3 and C1 results | `Cal.Anchor.P3, C1`; `Carrier.Root` |
| 14 Belt and rigs | anchored presets | its anchors (suggest renaming to `Belt.R.Rig.Anchor` style) |
| 15 Carbine | its presets; the receiver highlight (760,330) #9e8976 as a key check | `Cal.Anchor.RifleSpec` |
| 16 Materials | the swatch stage and albedo read-back | material names and their albedo targets |
| 18 Pipeline | `scene.py`, `render.py`, tiers, `deliver.py` | `cache/character_hero.blend` with a `Character` collection at the origin |
| hexcom game | the presentation glTF and renders; the scale check of `export/sgt_morgan.glb` | — (the game export is spec 08 §7.6) |

Corrections for the critique pass: spec 01 §8.1 "scene A" and every reference to it (03, 04, 05, 06, 07, 11, 12) → `LookDev` with AgX Base Contrast (D13); spec 06's `scripts/lib/render_harness.py` → a shim importing `scripts/eval/render.py`; spec 12's `scripts/eval/views.py` → `presets/p12.json`; spec 07's head-frame Empty → `Frame.Head`; any spec using the analysts' depth map (feet at y 895 = 4.5 m) → §2.1's exact table; spec 03 V5 → a hero border instead of a 1024 × 1536 hero camera; spec 14's anchor names → the naming convention. Repository: add `cache/` and `deliver/` to `.gitignore` (they hold the built scene and the deliverables).

### 10.2 Questions for the client
1. **Floor pool (D2).** The physical spot also lights the boot tops and trouser hems warm. Keep it physical, or prefer the analysts' floor-only pool to keep the boots exactly as drawn?
2. **Bokeh (D3).** Physical hard-edged discs, or emulate the game's soft discs in the compositor (not physical)?
3. **Floor joints (D9).** Keep the drawn sheared 1.5 m decorative saw-cut grid, or a structural orthogonal grid at 4.5–6 m?
4. **Background detail.** Blocking-level stand-ins as specified (everything is 8–15 px out of focus), or modelled set pieces?
5. **Storage.** Where should the 0.6–1.5 GB packed `.blend` and the 4K renders live: Git LFS, a GitHub release, a shared drive?
6. **Finals.** Are 3344 × 1882 and 3840 × 2160 at 512 spp on the GPU machine the right deliverables?
7. **Path guiding.** Cycles' CPU-only path guiding may cut noise in the dark set; worth a measured test on this box?
8. **UI.** Should one deliverable composite the render under loadout-screen panels? The reference's UI was drawn by the image generator, not taken from hexcom.
9. **Game scale.** The scene renders the modelled 1855 mm man; the export scales by 0.97035 to 1.80 m, putting the eye at 1688 mm against the rules' 1650 (spec 08 Q2). Confirm.
