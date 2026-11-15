# Part 06 — Head and face (likeness)

Status: draft 1 (spec writer), 2026-10-07, written under the **reality wins** rule (CLAUDE.md, Source of truth). Owner script: `scripts/parts/06_head_face.py` (plus the shared `scripts/lib/face_fit.py` (the likeness loop), `scripts/lib/face_landmarks.py` (landmark vertex ids, projection, detector wrappers), `scripts/lib/sculpt.py`, `scripts/lib/materials.py`, `scripts/lib/measure.py`, `scripts/lib/render_harness.py`). Object prefix `Head.*`; the head itself is the top of the shared MPFB body `Body.Mesh` (spec 04's name; the body is one mesh from the toes to the vertex — this spec owns every vertex above the hyoid join ring, rest h 1622, spec 04 §10.1).

Conventions (from `CLAUDE.md`): millimetres in this spec, metres in Blender; world origin on the floor midway between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT = viewer's right**. Every "left/right" is the soldier's own. All coordinates in §3 and §4 are **rest** world coordinates (A-pose, head heading −Y, no yaw) in mm; spec 04 D1 puts the rest skull top at 1877 and the posed figure 22 mm lower (knees flexed), so posed heights = rest − 22 before the head's own rotation (§7.3). Image coordinates are full-image pixels of `ref/reference_full.png` (1672 × 941), 1 px ≈ 2.1 mm at the head (consolidated "Agreed scale"); `ref/crop_head_face.png` is the ×5 crop with origin (715, 30).

Scope split with the neighbours: spec 04 owns everything below the hyoid ring and the `NeckTurn` corrective (this spec must **not** sculpt an SCM); spec 07 (hair) owns the scalp hair and the beard stubble strands; this spec owns the skull and face geometry, the facial shape keys, the eyes (with lashes), the brows (fibres included — they are fitted to lid and brow geometry built here), the teeth, tongue and mouth cavity, the ears, the face skin material and all its maps, and it **provides** spec 07 the stubble and scalp root maps and the follicle point cloud so that the pits in the skin and the hairs in them are the same points.

---

## 1. Purpose and acceptance

### 1.1 What this part is
The head of Sgt. Morgan from the hyoid join ring up: skull, face, ears, eyes, eyelids and lashes, brows, mouth interior, the facial expression and the head pose; the skin of the face with its colour zoning, pores, lines and beard shadow; and the measurement and fitting machinery (`face_fit.py`) that makes the face match the reference by numbers before anyone looks at it. It is the part the whole model is judged by: at native scale the head is 109 px tall and the viewer still has to recognise the man; at 4K the critic has to believe the skin.

### 1.2 What "perfect" looks like
Seen at the hero camera, the native-size head (109 px) reads as the same man as `ref/crop_head_face.png` in a side-by-side and in a mirrored pair: the same long square-oblong head with vertical sides, the same low heavy brow pressing on hooded, close-set, narrowed eyes, the same straight narrow-bridged nose with a broad base, the same thin pressed upper lip over a fuller lower lip, the same broad projecting square chin with a hint of a cleft, the same strong straight jaw with a masseter bulge and a clear gonial corner, the same thick neck, the same stern resolute set. Every landmark ratio in §8.2 is inside its tolerance, the pose gate passes, and the silhouette IoU is ≥ 0.95. At 4K a critic who knows faces sees skin, not plastic: pores of the right size in the right places (coarser on the nose, finer on the cheeks, none on the lids and lips), two shallow glabellar lines, one faint forehead crease, crow's feet, moderate nasolabial folds, a defined mentolabial sulcus, a redder nose tip, ears and cheeks, a greyer stubble-shadowed chin, a sheen only on the T-zone, light that bleeds red through the ear lobe and the nostril rims, eyes that are dark warm brown-grey with a strong limbal ring and a wet meniscus on both lid margins, a caruncle in the medial canthus, lashes that are short and dark, a lid margin with thickness, brows that are hair, and no waxy glow, no blue eyes, no uncanny symmetry, nothing that looks like MakeHuman.

### 1.3 Closeup render views (`scripts/lib/render_harness.py` presets `head_V1 … head_V6`; §8.1 defines the scenes)
The head is the one part the reference shows in full, so five of the six views are compared with reference crops. V1 is **the** acceptance view; V2 is checked against dimension tables and the 3DDFA side view; V3–V6 are look-development views at the hero light.

| View | Camera position (mm, world, posed) | Target | Lens / sensor / DOF | Compared with |
|---|---|---|---|---|
| V1 Hero face, native perspective | the hero camera **unchanged**: (0, −4500, 600), rotation (93.9°, 0, 0), 46 mm, sensor 36 mm; `render.use_border = True`, border (x 0.4276–0.5293, y 0.7875–0.9681) = full-image (715,30)–(885,200); resolution 1672 × 941 at `resolution_percentage` 500 with `use_crop_to_border` → an 850 × 850 output identical in framing to the crop; also rendered at 100 % (native 170 × 170 head crop) | — | as hero; f/1.5 DOF focus on the right cornea | `ref/crop_head_face.png` (×5) and the native crop at 1:1 and 50 % (the squint test, §8.2); landmark ratios, NME, silhouette IoU, ΔE colour points |
| V2 Mugshot pair (REST heading, no pose, no expression) | front: (0, −1300, 1757) looking +Y; profile: (−1300, −10, 1757) looking +X (his right side toward the camera) | (0, −60, 1757) | 85 mm; flat three-point look-dev light (spec 01 §8.1 scene) | §3.2 landmark table via `measure_head()` overlay (projected landmark vertices drawn as crosses on the render); the profile against `assets/ai/face_3ddfa_sideview.png` scaled to 237 mm head height |
| V3 Three-quarter from the hero direction, close | 900 mm from the right-eye corneal apex along the hero camera ray (direction from the eye to (0, −4500, 600)) | right corneal apex | 85 mm, f/4 focus on the cornea; hero lights | `ref/crop_head_face.png`, `ref/face_zooms/z_head_x8.png`; skin colour zoning, sheen, stubble shadow, under-jaw darkness |
| V4 Right eye macro | 350 mm along the same ray from the right corneal apex | right corneal apex | 100 mm, f/5.6; hero lights | `ref/face_zooms/g_eye_right_x20.png`, `ref/zoom_face_eyes_both_x16.png`: iris colour, limbal ring, catchlight position (794,77), lid coverage 20 %, medial-canthus shadow, hooded fold, lash length, wet line |
| V5 Nose–mouth–chin macro | 400 mm along the ray from the stomion | stomion | 100 mm, f/5.6; hero lights | `ref/face_zooms/g_nose_mouth_x14.png`, `ref/zoom_face_mouth_chin_x14.png`: nostril shape, columella show, philtrum ridges, lip thickness ratio 1 : 1.5, sulcus depth, cleft, stubble density gradient chin → cheek |
| V6 Right ear and temple macro | 400 mm from the tragion along the ray | right tragion | 100 mm, f/5.6; hero lights | `ref/face_zooms/g_ear_x16.png`, `g_temple_fade_x16.png`: helix roll, antihelix, concha depth, free lobe, red lobe transmission, the skin-fade zone (spec 07) |

Every view is rendered twice: once in the neutral look-dev scene (geometry judgement, Workbench matcap + cavity for the 5-second iteration loop, Cycles for the record) and once under the hero lights (colour). V1 is additionally rendered with `film_transparent` for the silhouette mask.

### 1.4 Pass criteria a critic can score (full list and numbers in §8.2–§8.3)
1. **Pose gate:** MediaPipe head pose of the V1 render within ±2° of the reference's (+14.6°, −9.9°, −1.2°; its own sign convention) — otherwise nothing else is scored.
2. **Landmark ratios:** every ratio in table §8.2-A inside its tolerance around the **adopted** target; weighted mean absolute delta ≤ 3 %; no identity ratio (eye spacing, fissure aspect, brow-to-lid, bigonial/bizygomatic, chin width) off by more than 5 %.
3. **NME** (Procrustes-aligned 468 MediaPipe landmarks, normalised by outer inter-ocular distance) ≤ 0.040 with the overruled landmarks (alae, exocanthi) at weight 0.5.
4. **Absolute dimensions** from `measure_head()` within tolerance of §3: breadths ±3 mm, heights ±3 mm, eye and nose features ±1.5 mm, ear ±2 mm.
5. **Silhouette IoU** (head + hair band vs the luminance > 45 reference mask) ≥ 0.95 ignoring a 3 px edge band; hair spikes are spec 07's (≥ 0.85 in y 14–48).
6. **Colour:** the 14 ΔE points of §8.2-C ≤ 6 each, ≤ 4 on the forehead, cheek and nose means; iris pixels contain zero blue-hue pixels (H in 180–260° with S > 0.15) in V1 and V4.
7. **Expression:** MediaPipe blendshapes of V1 within ±0.15 of the reference for browDown, eyeSquint, mouthPressLeft/Right, mouthShrugLower (0.58 in the reference).
8. **Squint test:** at native 170 × 170 and at 50 % of it, three of three reviewers (or the critic agent) pick the render as "the same man" against two decoys (the MPFB default head and the 3DDFA mesh render) in a blind triple.
9. **Flip test:** the mirrored render beside the mirrored reference shows no proportion error the unmirrored pair did not show.
10. **Skin at 4K (V3–V6):** pores visible and region-correct; glabellar lines, forehead crease, crow's feet, nasolabial folds, sulcus, cleft all present as relief; stubble shadow darkens the lit chin 30–35 % against the lit cheek even with the strands hidden; no SSS glow (the shadow side of the nose ≥ 1.5 stops darker than the lit side under the hero key); lid margins have a visible 2 mm thickness and a wet line; the ear lobe transmits red.
11. **Nothing MakeHuman:** no proxy hair cap, no alpha-card brows floating off the skin, no cartoon-blue procedural iris, no `middleage_caucasian_male` diffuse texture anywhere in the material.

---

## 2. Reference observations

### 2.1 Pose and camera (what must be reproduced before any likeness check)
| Item | Value | Evidence (consolidated §2 and §8, re-checked on `z_head_grid_x8.png`) |
|---|---|---|
| Head yaw | **+20° ±5° to his left**, world (nose toward viewer's right); ≈ +25° vs the chest (chest −5°) | right ear fully visible, left hidden; midline (815–816) right of the silhouette centre (799); near half-width 44 px vs far 29 px; detectors: MediaPipe +14.6°, 3DDFA −15.2° relative to the camera ray |
| Head pitch | ≈12° chin-up relative to the camera ray, of which ≈10° is the low camera → **head-vs-torso 3–5° chin-up** (adopt 5°, spec 04 §7.3 splits it neck02 −1°, neck03 −1°, head −3°) | both nostrils as dark holes (813,94)/(822,95); under-jaw plane visible y 128–135; ear top 7 px below the eye line |
| Roll | **0** | irises level at y 77; the 2 px drop of the far mouth corner is yaw perspective |
| Gaze | along the head axis **+4° further left, +2° up**, focused at distance; no sclera under the iris; upper lid covers the top 20 % of the iris | iris 1 px nasal of the fissure centre; catchlight at (794,77) on the right eye, lateral-upper of the pupil |
| Camera | (0, −4500, 600), 46 mm, pitch +3.9°; the face is seen from **≈13° below** (atan((1734 − 600)/4500) = 14.1° to the eye line) | consolidated §8 |
| Key / cool / world | key 4500 K from his right-front-above (az 40° toward −X, el 42°), cool side (0.55, 0.76, 1.0) from his left-behind (az 100°, el 35°), world 5 % | consolidated §8; calibration targets right temple (778,70) #e6bfac, right cheek (792,100) #d19b87, left forehead (835,52) #93878d, under-jaw (812,140) #110b06 |

### 2.2 Landmarks, colours and profiles (my re-sampling, 3 × 3 means; full landmark list in the consolidated §2)
Scale: IPD 32 px ≈ 66 mm, ear 28.5 px ≈ 61 mm → 2.06–2.14 mm/px; I use 2.1.

| Feature | Pixels / value | Reading for the build |
|---|---|---|
| Vertex / trichion / glabella / nasion | y 20 / (810,48) / (815,72) / (815,76) | upper third 24 px projected; forehead slopes back, the frontal boss highlight (818,58) #bd8a79 lum 150 |
| Brows: R inner/peak/tail, L inner/peak/tail | (809,72)/(796,70.5)/(786,73.5); (819,72)/(832,70.5)/(843,74) | straight, low, inner heads 10 px apart, peak at 60–65 %, slight lateral hook; R brow body #704c3b, L (shadow) #50382d |
| Eye row y 77, x 786 → 810 luminance | 102 84 71 63 80 100 107 **127 137** 94 67 64 55 44 54 86 60 46 66 87 106 97 106 110 126 | lateral canthus dark 63 (x 789), catchlight 137 at x 794, iris 44–67 (x 796–805), medial canthus shadow 46–66 (x 806–808): the medial third is in deep AO |
| Column x 800, y 68 → 84 luminance | 28 41 58 68 **49 30 29** 38 37 54 91 84 78 94 122 141 135 | brow 28–68 (y 68–71), hooded lid in shadow 30 (y 73–74), iris 37–54 (y 75–77), lower lid 78–94 (y 79–81), tear trough 122 (y 82), cheek 141: the brow-to-iris band is only 5 px (~10 mm) of dark |
| Iris R / L | (800,77) #543b32 lum 64; (832,77) #352726 | dark warm brown-grey, **not blue** (consolidated dispute #3) |
| Sclera R lateral / catchlight | (792,77) #826156; (794,77) #8d726b | sclera reads mid-grey-brown in this light: strong AO + skin bounce; never render it white |
| Nose: sidewall / dorsum / tip / columella / ala R / ala L / nostril | (809,84) #d6a08e lum 172; (815,84) #d29a86; (815,90) #c59180; (816,95) #704a3e; (806,93) #c28a77; (826,93) #916f66; (813,94) #3d1b12 | the dorsum is the brightest flat skin after the zygoma; the columella is in shadow but visible → tip rotated up by the view; ala L in the cool fill |
| Midline x 816, y 96 → 134 luminance | 83 74 75 86 65 62 **51** 55 76 113 **121** 92 **46 46** 83 **123** 112 87 60 **41** 46 37 40 53 78 98 **106** 96 91 91 80 60 54 48 54 55 50 35 28 | philtrum groove 51 (y 102), vermilion top 113–121 (y 105–106), stomion 46 (y 108–109), lower lip 123 (y 111), sulcus 41 (y 115–117), chin pad 106 (y 122), menton falls to 35 (y 133) |
| Lips | upper (816,107) #75453d; stomion #5e2c25; lower (818,112) #8d625b, highlight (820,112) #8f6862 | 3 : 4.5 px → **1 : 1.5** upper : lower; soft vermilion border; low saturation |
| Chin row y 124, x 800 → 832 luminance | 121 132 128 114 128 **154 161** 138 133 121 120 127 121 114 105 100 91 101 105 99 94 94 112 136 129 114 110 99 99 93 89 100 109 | lit pad x 805–828 (23 px, 48 mm projected); the two bright pixels x 805–806 are the right chin corner's highlight → a **squared** chin with a corner, not a dome |
| Cleft / sulcus / chin side | (816,121) #795546 lum 92 vs (816,123) 100 vs (808,124) 134 | the midline is 8 lum darker than its flanks over y 119–124: a faint vertical dimple, depth class "slight" |
| Cheek: zygoma / hollow / nasolabial / masseter / gonion / jawline | (780,88) #ecc3ad lum 202; (786,102) #c08c77 151; (803,104) #8d6454; (772,110) #b58873 144; (768,113) #9b7362; (780,120) #8f654e | 50-lum drop from the zygoma to the hollow 14 px below it = a real sub-zygomatic concavity; the masseter is lit (bulge) and the gonion darker (corner) |
| Ear R: helix / antihelix / concha / tragus / lobe / back edge | (762,92) #b6806a; (763,96) #8d503c; (766,98) #e4ac94 lum 183; (769,97) #c69878; (765,108) #d48b72; (754,95) #a66c5f | the concha is the brightest ear pixel (key shines into it: the ear stands off the skull); lobe is red-saturated: transmission |
| Forehead: boss / glabella / "11" line / between | (818,58) #bd8a79; (815,70) #ae7968; (813,64) #a17669 lum 128; (815,64) #b08477 lum 142 | the lines are 14 lum deep against 2 px flanks → shallow (0.3–0.4 mm) but 27 mm long |
| Temple R / fade skin / hairline | (782,72) #dbb49d; (770,66) #9c7c6b; (810,49) #ba8775 | temple hot spot = sheen; the fade zone is 50 % scalp (spec 07) |
| Crow's foot R | (787,79) #ae7d69 vs cheek #c5907d | 2–3 lines, shallow |
| Left side (cool fill) | cheek (842,92) #ae8e8c; forehead (835,60) #baacb5; jaw rim (843,110) #4b484a | same albedo under the cool light; the rim is grey-blue |
| Under-jaw / neck | (805,138) #100a04 lum 10; SCM (778,146) #af816c | the chin overhangs the neck: nothing lights the submental plane |

### 2.3 Detector readings already on disk (`assets/ai/`)
`face_ref_landmarks.json` (MediaPipe FaceLandmarker, 478 points on the ×5 crop; keys `landmarks_px_xyz`, `key_indices`, `ratios`, `head_pose_from_matrix`, `blendshapes`): ratios face_width/height 0.900, jaw/face 0.839, inner-IPD/face 0.244, outer-IPD/face 0.609, mouth/outer-IPD 0.585, nose width/inner-IPD 1.152, nose length/face height 0.235, eye-to-mouth 0.447, nose-to-chin 0.460, eye-to-chin 0.717, eye aspect 0.329, lip height/mouth width 0.249, nose length/width 0.930; blendshapes mouthShrugLower 0.58, eyeLookOutLeft 0.31, eyeSquintLeft 0.28. `face_3ddfa_lm68.json` (keys `landmarks68_px_xyz`, `pose_yaw_pitch_roll_deg`, `param62`) and `face_3ddfa_dense.obj` (38,365 verts, image-pixel units, generic identity). Two detectors disagree by 1–4 % of face height on the same image (research E §3): **nothing below 3 % is signal.**

### 2.4 Ambiguities
* The left (far) half of the face is in the cool fill; every left-side landmark carries ±2 px. The face is treated as symmetric (consolidated) with the small scripted asymmetries of §3.3 (reality: no face is symmetric; they stay below detector noise).
* Brow-to-lid distance 1.5–2 px (4 mm) is a projection of a 12° chin-up view plus hooding; the real distance cannot be 4 mm with an open eye (§2.5 row 4).
* Eye fissure 18 px (38 mm) and alar base 21 px (45 mm) are beyond human norms at this scale (Farkas male fissure 31.3 ± 1.3, alar 34.9 ± 2.1; research D §1f) — the generator drew large features on a small head (§2.5 rows 1–2).
* Pores and fine lines are below the 2.1 mm/px scale; the image constrains only *which* lines exist, not their depth.
* The neck's apparent 0.85–0.9 of the jaw width is read against a jaw inflated by the visible near ramus (§2.5 row 5).

### 2.5 Decisions — where the image and reality disagree (reality wins)
| # | Topic | Image / analysts | Reality (source) | Adopted | Consequence |
|---|---|---|---|---|---|
| 1 | Eye fissure length | 18 px ≈ 38 mm; intercanthal/fissure 0.78 | Farkas male 31.3 ± 1.3 mm; 38 is +5 SD | **33 mm** (+1.3 SD, "long eyes"); intercanthal **31** (−0.9 SD, close-set kept); biocular 97 | nose_width/inner-IPD and intercanthal/fissure ratios will deviate from the image by design (§8.2-A) |
| 2 | Alar base width | 21 px ≈ 45 mm, 1.5 × intercanthal | Farkas 34.9 ± 2.1; 45 is +5 SD | **39 mm** (+2 SD, still "broad") | alar/mouth 0.68 instead of 0.81 |
| 3 | Interpupillary | 32 ± 1 px ≈ 66 mm | ANSUR II tight mean 64.4, 95th 70 | **65 mm** | — |
| 4 | Brow (lower hair edge) to upper lid margin | ≈4 mm projected | 8–12 mm typical open-eye male; hooded low brow 6–7 | **7 mm** (low brow kept) | the hood and the 5° chin-up reproduce the 4 mm projection |
| 5 | Bigonial / bizygomatic | 74 / 74 px → 157 / 155 mm (consolidated; spec 04 uses bigonial 157) | ANSUR bizygomatic 142 mean, 153 95th; bigonial/bizygomatic 0.78 typ., 0.9 very square | bizygomatic **152**, bigonial **138** (ratio 0.91), head breadth 158 | spec 04's neck 135 becomes 0.98 of the jaw: recommend neck breadth **130** (§10.2 Q1) |
| 6 | Head height vertex–menton | 109 px ≈ 231 mm; spec 04 rest 1877 − 1640 = 237 | typical male ~232; ANSUR tragion–vertex 132 | **237** (spec 04's numbers kept for continuity; within norms) | — |
| 7 | Facial thirds | 29 / 30 / 41 % projected → 31 / 31 / 38 corrected | norm ≈ 33 / 33 / 33; a long lower third is common and identity-bearing | as corrected: **57 / 57 / 71 mm** (face height 185) | nose_to_chin ratio kept as the image's |
| 8 | Nose length nasion–subnasale | 21 px ≈ 45 projected, ~50 corrected | ANSUR nose length ≈ 52 male | **52** with protrusion 20 | — |
| 9 | Mouth width | 26 px, ≈58 corrected | Farkas 54.5 ± 3.0 | **57** | — |
| 10 | Chin pad width | 23 px ≈ 48 projected | squared chins 42–48 | **46** | — |
| 11 | Iris colour | "blue-grey" at thumbnail (pose note) | pixel sampling: zero blue-hue pixels | **#5b4a3e** body, limbal #3a2d26, fibres #6e6253 | upheld, not overruled |
| 12 | Ear vertical position | ear top 7 px below the eye line | standard: ear top at the brow line, tragion ≈ at the alar level | **standard placement**; the 12° pitch produces the drop | `ear-trans-down` stays 0 |
| 13 | Eyeball depth | "deep-set" | corneal apex normally ~16 mm in front of the lateral orbital rim; deep-set −3 to −4 | apex **4 mm behind** the glabella plane | `eye-push1/2-in` solved to it |
| 14 | Facial symmetry | symmetric | no real face is; asymmetries of 0.5–1.5 mm are universal | symmetric fit, then §3.3 asymmetries ≤ 1.5 mm | below detector noise |
| 15 | Pores, lines depth | unresolvable (high-pass 2.3 lum) | dermatology norms per region (§3.7) | §3.7 tables | — |
| 16 | Teeth | not visible | standard adult dentition with 40-year wear | §3.6 | — |
| 17 | Skin albedo | lit hexes | lit ≠ albedo | consolidated albedo recommendations (#b98670 base …) with the ΔE check under matched lights | — |
| 18 | Expression | stern-neutral, pressed lips, squint, mentalis shrug 0.58 | plausible | **as drawn** (§7.2) | — |
| 19 | Neck width vs jaw | 0.85–0.9 × jaw | ANSUR neck circ ≈ 410 → breadth ≈ 130 | neck 130 (spec 04 to confirm) | §10.2 |

---

## 3. Real-world reference

Tags: **M** measured on the reference (pixels × 2.1 mm, pitch-corrected where stated), **S** sourced (ANSUR II via research D §1f; Farkas norms via research D; ophthalmic and dental standard values, marked [S-std] — textbook constants, not re-looked-up here [VERIFY]), **E** estimated from anatomy for this build.

### 3.1 Skull and head
| Measure | Value (mm) | Tag | Note |
|---|---|---|---|
| Vertex height, rest / posed (before head rotation) | 1877 / 1855 | M (spec 04 D1) | image y 20 |
| Head length glabella → opisthocranion | 203 | S (ANSUR tight mean 203) | glabella Y −105 → occiput Y +98 |
| Head breadth (euryon–euryon) | 158 | S/E (ANSUR 154; +1 SD for the wide-skull read) | at (±79, +40, 1790) |
| Head circumference | 590 | S (581 mean; follows the breadth) | check with `measure_head()` |
| Tragion → vertex | 132 | S | tragion Z 1745 |
| Menton → nasion (face length) | 123 | S/M (ANSUR 126; image 120 corrected) | |
| Trichion → menton | 185 | M | thirds 57 / 57 / 71 |
| Bizygomatic | 152 | E (decision 5) | zygion (±76, −30, 1745) |
| Bigonial | 138 | E (decision 5) | gonion (±69, +20, 1678) |
| Minimum frontal breadth (frontotemporale) | 106 | E | vertical temple sides |
| Vertex → menton | 237 | M/spec 04 | |
| Forehead slope from the vertical | 12° | M (consolidated 10–15°) | |
| Mandibular plane angle (menton–gonion vs Frankfort) | 25° | S-std | gonion 38 above the menton level |
| Gonial angle | 118° | M (115–120) | |
| Neck breadth at the larynx (spec 04) | 130 proposed (04: 135) | E | §10.2 |

### 3.2 Landmark coordinates (rest, world, mm; X his left +, Y back +, Z up; face plane = glabella Y −105)
| Landmark | X | Y | Z | Tag | Derivation |
|---|---|---|---|---|---|
| Vertex | 0 | −10 | 1877 | M | spec 04 D1 |
| Opisthocranion | 0 | +98 | 1795 | S | head length 203 |
| Euryon L/R | ±79 | +40 | 1790 | S/E | breadth 158 |
| Frontotemporale L/R | ±53 | −60 | 1790 | E | |
| Trichion | 0 | −91 | 1825 | M | 57 above the glabella, 12° slope |
| Frontal boss L/R | ±25 | −97 | 1800 | M (818,58) | +3 proud of the slope |
| Glabella | 0 | −105 | 1768 | M | |
| Supraorbital ridge apex L/R | ±25 | −101 | 1771 | E | 4–5 proud of the forehead above it |
| Nasion (sellion) | 0 | −98 | 1763 | M/S | 7 behind the glabella |
| Brow inner head L/R (hair) | ±11 | −104 | 1770 | M | 22 apart |
| Brow peak L/R | ±38 | −96 | 1773 | M | 60–65 % out |
| Brow tail L/R | ±52 | −78 | 1766 | M | lateral hook down |
| Endocanthion L/R | ±15.5 | −92 | 1757 | M/S | intercanthal 31 |
| Exocanthion L/R | ±48.5 | −78 | 1759 | S/E | fissure 33, canthal tilt +4° |
| Pupil centre (corneal apex) L/R | ±32.5 | −101 | 1756 | M/S | IPD 65; apex 4 behind the glabella plane |
| Eyeball centre L/R | ±32.5 | −88 | 1756 | S-std | 13 behind the apex |
| Orbitale (infraorbital rim) L/R | ±32 | −80 | 1742 | E | |
| Zygion L/R | ±76 | −30 | 1745 | E | bizygomatic 152 |
| Malar eminence L/R | ±52 | −76 | 1740 | M (780,88) | the highlight |
| Sub-zygomatic hollow centre L/R | ±58 | −62 | 1716 | M (786,102) | −3 concavity |
| Rhinion (bony–cartilaginous junction, hump) | 0 | −124 | 1740 | M (y 86–88) | +1.5 hump |
| Pronasale | 0 | −138 | 1722 | M/S | protrusion 20 from the subnasale |
| Alare L/R | ±19.5 | −116 | 1716 | E (decision 2) | alar 39 |
| Alar-facial groove L/R | ±21 | −113 | 1710 | E | 1.5 deep |
| Subnasale | 0 | −118 | 1711 | M | |
| Columella lowest point | 0 | −128 | 1712 | E | 2 mm show below the alar rims |
| Labrale superius | 0 | −122 | 1693 | M | philtrum 18 |
| Philtral columns L/R | ±5.5 | −122 | 1700 | M | 11 apart, +1 relief |
| Stomion | 0 | −117 | 1687 | M | upper vermilion 6 |
| Cheilion L/R | ±28.5 | −104 | 1685 | M (decision 9) | mouth 57; corners 1.5 lower than the stomion |
| Labrale inferius | 0 | −120 | 1677.5 | M | lower vermilion 9.5 |
| Mentolabial sulcus | 0 | −111 | 1669 | M | 1.0 deep |
| Pogonion (chin pad) | 0 | −117 | 1655 | M | chin pad 46 wide |
| Chin corners L/R | ±23 | −108 | 1655 | M (805–828, y 124) | squared |
| Gnathion | 0 | −110 | 1645 | E | |
| Menton | 0 | −98 | 1640 | M | |
| Gonion L/R | ±69 | +20 | 1678 | E/M | 38 above the menton, 67 below the tragion |
| Masseter belly max L/R | ±66 | +4 | 1692 | M (772,110) | +4 relief when clenched +2 |
| Tragion L/R | ±74 | 0 | 1745 | S | |
| Superaurale L/R | ±78 | +12 | 1782 | M/S | ear 62 tall, axis 15° back |
| Subaurale (lobe bottom) L/R | ±76 | −2 | 1720 | M | free lobe |
| Postaurale L/R | ±84 | +36 | 1750 | M | ear breadth 36 |
| Mastoid L/R | ±72 | +15 | 1660 | spec 04 | |
| Skull base / neck axis top | 0 | −8 | 1650 | spec 04 | |
| Hyoid (join ring) | 0 | −72 | 1622 | spec 04 | blend band 1615–1630 |
| Nape hairline (midline) | 0 | +70 | 1665 | E | spec 04 wrote ≈1650; §10.2 |

Sanity: E-line (pronasale → pogonion) passes 6.5 mm in front of the upper lip and 3.4 mm in front of the lower (norms 4 ± 2 / 2 ± 2): a strong chin, as the picture says. Nasolabial angle 95°, nasofrontal 130°, cervicomental 105° (spec 04).

### 3.3 Soft-tissue features
| Feature | Dimensions (mm) | Tag | Note |
|---|---|---|---|
| Brow hair band | 9 tall at the body, 6 at the head, tapering to 1 at the tail; length 55 (inner head → tail); hairs 8–12 long, 0.08 dia, 350–450 per brow | M/E | dense; direction field: inner third up-and-out 60°, body lateral 0–10°, tail down-lateral 20° |
| Upper eyelid | tarsal plate 10 tall; lid margin 2.0 thick; crease 6 above the margin medially → 3 laterally; orbital skin overhang (hood) covers the crease on the lateral 50 %, 1.5 forward | S-std/M | the "hooded, deep-set" read |
| Lower eyelid | margin 1.5 thick; crease 4 below; tear trough from (±15, −92, 1750) to (±30, −80, 1742), 0.6 deep, 5 wide | S-std/M | darker albedo #9d7266 |
| Palpebral fissure | 33 × 9.2 (aspect 0.28); canthal tilt +4°; iris cover: upper 2.3 (20 %), lower 0.3 (touches the limbus) | M/decision 1 | |
| Nose | length 52, protrusion 20, bridge width at the nasion 15, mid-dorsum 17, lobule (tip) width 20, alar 39, alar thickness 4, nostrils 7 × 4 ovals at 30° from horizontal, columella 7 wide, septum 2 lower than the rims, dorsal hump +1.5 at the rhinion | M/S/E | straight dorsum, slightly rounded tip |
| Lips | width 57; upper vermilion 6 (thin), lower 9.5; Cupid's bow depth 1.5 (shallow), bow width 12; philtrum 18 long, columns 11 apart, +1 relief, groove −0.6; corners tucked 1.5 back and 1.5 below the stomion; lip line straight; vermilion border soft (no white roll ridge > 0.3) | M | pressed: lips 0.6 flatter in Y than relaxed |
| Chin | pad 46 wide × 15 tall; pogonion 2 behind the lower lip; cleft 0.8 deep × 2.5 wide × 8 tall at X 0.5 (left of centre by 0.5); corners rounded r 8 | M | |
| Jaw | body lower border straight gonion → menton; gonial corner r 10; masseter +4 relief, +2 more when clenched; mandibular angle 118° | M/E | |
| Cheeks | malar eminence +3; sub-zygomatic hollow −3 over r 16; buccal fat low (weight macro 0.45); nasolabial fold 1.0–1.2 deep, 5 wide, cheek side +0.8 | M/E | lean, 40-year face |
| Neck (interface) | breadth 130 at the larynx, SCM relief spec 04 | E | §10 |
| Scripted asymmetries (all ≤ 1.5) | right brow tail +1.0 Z; left fissure −0.4 in height; nose tip +0.8 X (toward his left; the image midline is 1 px left of centre); left cheilion −0.6 Z; right ear −1.0 Z; cleft +0.5 X | E (decision 14) | applied by `sculpt.py` after the symmetric fit |

### 3.4 Eyes (both; standard adult values [S-std] unless tagged)
| Component | Dimensions (mm) | Note |
|---|---|---|
| Globe | sphere r 12.0 (axial 24.0), equatorial 23.5 → scale Y 1.0, X/Z 0.98 | centre (±32.5, −88, 1756) |
| Cornea | chord 11.7, radius of curvature 7.8, sagittal depth 2.64, protrudes 1.1 beyond the globe sphere; thickness 0.55 centre, 0.7 edge | IOR 1.376 |
| Limbus transition | 1.0 wide blend band | sclera–cornea |
| Anterior chamber | iris plane 3.0 behind the corneal apex | |
| Iris | visible diameter 11.5; slightly conical, pupil edge 0.3 forward of the root; collarette ring at r 2.6 (45 %); 10–16 crypts between r 2.6 and 4.5; 180–220 radial fibres; 2–3 contraction furrows at r 4.2–5.2 | colour body #5b4a3e, collarette slightly warmer #6a5243, fibres #6e6253, crypts #3f322b |
| Limbal ring | 0.6 wide, #3a2d26, soft inner edge 0.3 | strong (identity cue) |
| Pupil | diameter 4.0 (range 3.5–4.5 in a dark hangar under a strong key), black #050404 with the retina not visible | centred 0.3 nasal of the iris centre (physiological) |
| Sclera | albedo #e6e0da, yellowing toward both canthi #d9c9b4 over the outer 3 mm; 6–10 conjunctival vessels 0.08 wide, #a6362e at 25 % opacity, radiating from the canthi, mostly hidden by the lids | SSS scale 0.002, roughness 0.25 |
| Tear film / wet line | meniscus 0.35 radius along both lid margins over the full fissure; glossy, IOR 1.33, roughness 0.05 | `Head.Eye.*.Wetline` |
| Caruncle | 5 × 3 × 2 mound in the medial canthus, #b0695c, 3–5 fine hairs 0.5 long [optional] | `Head.Eye.*.Caruncle` |
| Plica semilunaris | 2 wide crescent lateral to the caruncle, #d8bfb6 | part of the caruncle mesh |
| Occlusion shell | thin dark translucent shell under the lid margins, 1.5 deep, alpha 0.6 → 0 over 2 mm | classic AO fix for the medial-canthus darkness (x 806–808 lum 46–66) |
| Lashes, upper | 130 per lid, 8–10 long (lateral longest), 2–3 irregular rows over the anterior lid margin, curl 30° up, splay ±15°; root radius 0.06 → tip 0.02; colour #2a1a12; medial 5 mm lash-free | spec says "short": the curl keeps the projected length 3–4 |
| Lashes, lower | 65 per lid, 5–6 long, down-and-out 10°, one row | sparse |
| Eyelid skin | 1.0 thick (thinnest skin), no pores, fine 0.3-pitch crosshatch | albedo #a98078 (slightly violet-grey) |

### 3.5 Ears (right visible; left mirrored with the −1.0 Z asymmetry)
| Component | Dimensions (mm) | Tag |
|---|---|---|
| Ear height / breadth / protrusion (helix to mastoid skin) | 62 / 36 / 22 | M (61 × 36) / S (ANSUR 65 / 37 / 24) |
| Axis tilt from vertical (top back) | 15° | S-std |
| Helix | roll 5 wide, 3 thick, running from the crus (inside the concha) over the top and down to the lobe | S-std |
| Scapha | 6 wide groove inside the helix | |
| Antihelix | 4 wide ridge, superior and inferior crura (Y-fork) enclosing the triangular fossa 10 × 7 | |
| Concha | cymba 10 × 8 above the crus, cavum 16 × 14 below; depth 12 | M (concha brightest pixel: open to the key) |
| Tragus / antitragus / intertragic notch | 8 × 6 bump 4 proud / 6 × 5 / 5 wide | |
| External meatus | 7 × 5 oval at the front of the cavum, 8 deep then black (#050303) | |
| Lobe | 16 tall × 18 wide × 4 thick, free (unattached), soft | M (free) |
| Skin | thinner; SSS scale 0.006, radius (1.0, 0.25, 0.12); cartilage colour #c99a84 showing through the helix | M (lobe #d48b72 transmission) |

### 3.6 Teeth, gums, tongue, mouth cavity (hidden behind closed lips; built for the rig and any later open-mouth use)
| Item | Dimensions (mm) | Note |
|---|---|---|
| Dentition | 32 (third molars present, hidden) | MPFB `teeth_base` fitted, re-materialled |
| Upper central incisor crown | 10.5 tall × 8.5 wide × 7 thick; incisal edge flattened 0.5 (40-year wear, mamelons gone) | |
| Upper lateral / canine / premolars / molars | 9 × 6.5 / 10 × 7.5 / 8 × 7 / 7.5 × 10 | |
| Arch | intercanine 35, intermolar 55; overjet 2.5, overbite 2.5; Spee curve 1.5 | |
| Enamel colour | incisal third #e9e1d3 → gingival third #d9c7a9; embrasure stain #b89a7a at 20 % | SSS scale 0.002 |
| Gingiva | #b45e5e, scalloped free margin 2 tall, interdental papillae | roughness 0.35 |
| Tongue | 85 long × 50 wide × 20 thick at rest; dorsum #b86a6c, papillae 0.3 bump, median sulcus 1 deep; underside #c97b7d glossy | MPFB `tongue01` fitted |
| Mouth cavity | MakeHuman inner mouth bag [VERIFY it exists on the base mesh; else `Head.MouthBag`]; colour #3a1612, roughness 0.15 (saliva) | |

### 3.7 Skin: lines and pores
**Lines and folds** (each is a curve `Head.Curve.Wrinkle.<Name>.<Side>` on the surface; depth profile = Gaussian cross-section of the stated width with the stated depth; the cheek side of a fold rises by the stated bulge):

| Name | Path (rest, mm) | Length | Width | Depth | Bulge | Tag |
|---|---|---|---|---|---|---|
| Glabellar "11" L/R | (±4, −105, 1770) → (±6, −103, 1797) | 27 | 1.6 | 0.35 | 0 | M (x 813/817, y 58–71) |
| Forehead crease | (−45, −92, 1792) → (+20, −94, 1792), following the curvature | 65 | 2.0 | 0.25 | 0 | M (y 63–64, right half) |
| Crow's feet R ×3 (L ×3 mirrored) | from the exocanthion (±48.5, −78, 1759) back-down 12–15; the middle one horizontal, the others ±15° | 12–15 | 1.0 | 0.20 | 0 | M (786–789, 76–81) |
| Nasolabial L/R | alar-facial groove (±21, −113, 1710) → 6 lateral of the cheilion (±35, −100, 1680) | 32 | 5.0 | 1.1 | +0.8 | M (803,104) |
| Mentolabial sulcus | (−18, −110, 1670) → (0, −111, 1669) → (+18, −110, 1670) | 36 | 6.0 | 1.0 | 0 | M (lum 41) |
| Chin cleft | (0.5, −117, 1651) → (0.5, −116, 1659) | 8 | 2.5 | 0.8 | 0 | M (slight) |
| Tear trough L/R | (±15, −92, 1750) → (±30, −80, 1742) | 18 | 5.0 | 0.6 | 0 | M (y 82–83) |
| Lower lid crease L/R | 4 below the margin, full fissure length | 30 | 0.8 | 0.20 | 0 | E |
| Upper lid crease L/R | 6 above the margin medially → 3 laterally | 30 | 1.0 | 0.5 (geometry key `LidHood`) | — | M |
| Alar-facial groove L/R | around the alar base | 20 | 2.0 | 1.5 | 0 | S-std |
| Philtral columns ×2 | (±5.5, −122, 1711) → (±5.5, −122, 1693) | 18 | 3.0 | −1.0 (ridge) | — | M (lit band 813–819) |
| Lip lines | 14 per lip, radial, 2–4 long | — | 0.3 | 0.15 | 0 | E |
| Preauricular crease L/R | in front of the tragus, vertical | 20 | 1.0 | 0.4 | 0 | S-std |
| Horizontal neck creases | spec 04 §3.6 | — | — | — | — | interface |

**Pores and micro-relief by region** (density and size are dermatology norms for a 40-year-old male; Langer-line angle is the direction the micro-lines and the noise anisotropy follow, 0° = horizontal):

| Region | Pores /cm² | Pore dia (mm) | Pore depth (mm) | Follicle pits (stubble) /cm² | Micro-line cell (mm) | Langer angle | Tag |
|---|---|---|---|---|---|---|---|
| Forehead | 70 | 0.15–0.20 | 0.08 | 0 | 0.5 | 0° | E |
| Temples | 40 | 0.12 | 0.06 | 0 | 0.5 | 20° down-back | E |
| Nose dorsum | 90 | 0.20 | 0.10 | 0 | 0.4 | 90° | E |
| Nose tip and alae | 110 | 0.25–0.35 | 0.15 | 0 | 0.35 | radial | E |
| Cheeks (malar) | 50 | 0.12–0.18 | 0.08 | 10 (sparse zone) | 0.5 | 45° down-medial | E |
| Lower cheeks, jaw | 45 | 0.15 | 0.08 | 30 (medium) | 0.5 | 30° | E (density from the stubble map) |
| Chin, moustache, under-jaw | 60 | 0.20 | 0.10 | 45 (dense) | 0.45 | 90° | E |
| Eyelids | 0 | — | — | 0 | 0.3 | 0° | S-std |
| Lips | 0 (lip lines instead) | — | — | 0 | — | radial | S-std |
| Ears | 30 | 0.10 | 0.05 | 0 | 0.4 | — | E |
| Neck (spec 04) | 1 per 0.9 mm | — | — | fade to 0 at the hyoid | | | interface |

Follicle pits are 0.25 dia × 0.12 deep and sit **exactly** at the stubble root points (§4 step 14, shared with spec 07); on the chin 20–30 % of them carry a grey hair (spec 07) — the pit is the same.

### 3.8 Age and wear
38–42: full bone definition, early expression lines (§3.7), no sagging (jowl 0, nasojugal fold faint), no grey scalp hair, salt-and-pepper chin (spec 07), slight incisal wear, T-zone sheen, lightly wind-burnt right cheek (the lit one, +6 % redness), no moles, scars or freckles (consolidated — a local-contrast scan found none), no sun spots. Fitzpatrick II–III.

---
## 4. Geometry construction plan

Everything is a function in `scripts/parts/06_head_face.py` or the shared libraries; nothing is hand-sculpted or hand-painted. Steps 1–3 are the shared body pipeline (`scripts/lib/proportions.py`, run once by `build_all.py` for specs 03/04/05/06; this spec contributes the head rows); 4–16 are this part's own. Re-running the script deletes every `Head.*` object, image and material and rebuilds them; `Body.Mesh` keeps its other parts' shape keys untouched (this spec only adds/replaces keys named `Head.Key.*` and MPFB targets in its own list).

**Topology facts that drive the plan** (research B §5): the MakeHuman base has 8,428 body vertices of which 4,119 lie above z 1.60 and 2,963 in the front half of the head — half the mesh is in the head; clean all-quad loops around the eyes, lips and nostrils; separate fitted assets for eyes, lashes, brows, teeth, tongue. The 1,214 bundled targets include 27 head, 8 forehead, 6 eyebrow, 68 eye, 16 cheek, 42 nose, 44 mouth, 15 chin, 44 ear, 20 neck targets and 102 expression units (names in `notes/mpfb_targets_and_assets.txt`); **none** for the brow ridge, gonial angle/masseter, sub-zygomatic hollow, mentolabial depth or a hooded lid — those are scripted keys (step 8).

| Step | What | Tool / API | Parameters and names |
|---|---|---|---|
| 1 | Base human | `HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True, scale=0.1, macro_detail_dict=macro)` | macro: gender 1.0, **age 0.615** (40 y), muscle 0.70, weight 0.45, proportions 0.5, caucasian 1.0; height solved by spec 04 to rest vertex 1877 |
| 2 | Landmark vertex ids (once per topology, cached in `scripts/lib/face_landmark_ids.json`) | render the default head flat-lit frontal (EEVEE 512², 40 s, or Workbench) → `ai_face_landmarks.py` → for each of the 478 MediaPipe points cast a ray from the camera through the pixel onto `Body.Mesh` (`BVHTree.FromObject(..., depsgraph)`), store (face index, barycentric weights); the 30 manual landmarks of §3.2 are mapped to MediaPipe indices (glabella 9, nasion 168, pronasale 1, subnasale 2, stomion 13/14, menton 152, cheilion 61/291, exocanthion 33/263, endocanthion 133/362, alare 48/278, trichion 10; gonions and zygions by the `key_indices` the script wrote) | MakeHuman topology is fixed, so the ids hold for every target combination; `face_landmarks.landmark_xyz(obj, depsgraph)` returns them in world mm from the **evaluated** mesh (macro targets are shape keys — never read `obj.data.vertices`) |
| 3 | Start targets | `TargetService.bulk_load_targets(basemesh, [...])` with every target in table 4.1 at its start value (negative = load the `-decr`/opposite twin with a positive weight) | table 4.1 |
| 4 | Pose and camera for fitting | temporary copy of the hero camera (`Head.Cam.Fit`, border crop as V1); head pose applied on the rig **or**, before the rig exists, as a rotation of the head vertex block about the skull-base point (0, −8, 1650): Z +20°, then X −5° (chin up; facing −Y, a negative X rotation raises the chin); expression keys at §7.2 values | `face_fit.pose_head()`; the pose gate (MediaPipe on a render) must pass ±2° **before** any ratio is scored |
| 5 | **Inner fitting loop** (fast, no renders) | `face_fit.fit(basemesh, params=TABLE_4_1, targets=TABLE_8_2A + TABLE_3_2_ABS + THREE_D)` — damped least squares: residual r_i = w_i (m_i − t_i)/t_i over (a) the 2D ratios of §8.2-A computed from the **projected landmark vertices** through `Head.Cam.Fit`, (b) the absolute mm of §3.1–3.2 from the landmark vertices (breadths, heights, eye and nose features), (c) the 3DDFA depth residuals (step 6); regulariser λ = 0.1 toward the start values; Jacobian by finite differences Δ = 0.1 per target (set key value → `evaluated_depsgraph_get()` → read landmarks: ≈ 50 ms, 60 columns ≈ 3 s); Levenberg–Marquardt step with per-iteration clamp ±0.15 and bounds [−1, 1] ([0, 1] for one-sided targets); stop when the weighted mean |r| ≤ 3 % and max identity |r| ≤ 5 %, or after 30 iterations; log every iteration to `renders/06_head/fit_log.json` | per-ratio weights: ×2 on inner-IPD/face, eye aspect, brow-to-lid, bigonial/bizygomatic, chin width; ×0.5 on the 3D residuals; the measurement rule "adjust targets by a documented rule" **is** this: Δp = −(JᵀWJ + μI)⁻¹ JᵀW r, μ adaptive (×3 on a worse step, ÷2 on a better one) |
| 6 | 3DDFA sparse 3D target | load `assets/ai/face_3ddfa_lm68.json`; scale the 68 points to mm with the known crop scale (hair-top-to-menton 237 mm / its pixel span); Procrustes (similarity, no reflection) onto the mesh's matching landmark vertices using the stable set (exocanthi, endocanthi, nasion, subnasale, cheilions, menton); residuals used: pronasale depth (Y) relative to the exocanthion plane, malar depth, gonion Y, menton Y, jaw-plane angle; weight 0.5 | `face_fit.load_3ddfa()`; **no** dense shrinkwrap except optionally `Shrinkwrap` (`NEAREST_SURFACEPOINT`, vertex group `face_midband` nasion→upper lip, cheek→cheek, factor 0.3) to the aligned dense mesh — research E says the identity in it is generic; default OFF |
| 7 | **Outer gate** (renders) | Workbench matcap + cavity render of the posed head at the V1 border (5 s) [VERIFY MediaPipe detects a matcap head; fallback EEVEE with a flat #b98670 diffuse, 40 s; last resort Cycles 16 spp 425²] → `ai_face_landmarks.py` on it → compare with the reference ratios; **bias correction:** b_i = (detector ratio on the render) − (projected-vertex ratio on the same mesh); the corrected image target becomes t_i − b_i for the next inner loop; two outer iterations are normally enough | pass = §8.2-A within tolerance **and** NME ≤ 0.04; the gate also writes `renders/06_head/fit_overlay.png` (reference landmarks in red, render landmarks in cyan, ×5) |
| 8 | Scripted shape keys (features no target reaches) | `sculpt.soft_inflate/soft_line/soft_move` (spec 04's helpers: vertex-group-weighted offsets along the normal or a vector, radius r in mm, Gaussian falloff, Laplacian smooth 2 passes), each saved as its own shape key so the fit can re-weight it | `Head.Key.BrowRidge` +3.0 at (±25, −101, 1771) r 18, glabella +2.0 r 10; `Head.Key.SubzygHollow` −3.0 at (±58, −62, 1716) r 16; `Head.Key.MalarEminence` +2.0 at (±52, −76, 1740) r 12; `Head.Key.Masseter` +4.0 at (±66, +4, 1692) r 14 and the gonial corner +3.0 at (±69, +20, 1678) r 8; `Head.Key.ChinSquare` +2.5 at (±23, −108, 1655) r 9; `Head.Key.Sulcus` line −1.5 along the sulcus path r 7; `Head.Key.Cleft` −0.8 line r 1.5; `Head.Key.LidHood` move (±40, −92, 1764) r 7 by (0, −1.5, −1.0) (orbital skin forward and down over the lateral lid); `Head.Key.TearTrough` line −0.6 r 5; `Head.Key.NasalHump` +1.5 at (0, −124, 1740) r 5; `Head.Key.BridgeNarrow` −1.5 at (±8, −110, 1752) r 6; `Head.Key.AlarGroove` line −1.5 r 3; `Head.Key.Philtrum` two lines +1.0 r 2.5 and the groove −0.6; `Head.Key.LipPress` lips −0.6 in −Y, vermilion height ×0.92; `Head.Key.Asym` the §3.3 asymmetries; weights solved in a second inner-loop pass with the targets frozen |
| 9 | Head UV | copy the MakeHuman UV layer to `UV.Head`; select the head island (faces whose vertices are all above z 1.60 and in the MakeHuman `head` + `neck` vertex groups [VERIFY the island is already seamed from the body at the neck; if not, mark a seam on the hyoid ring and `uv.unwrap(method='ANGLE_BASED')` under a real selection]); scale the island about its centre to fill 0.02–0.98 of the UV square | ≈300 × 300 mm flattened at 4096 px → **≈13.6 px/mm (0.073 mm/px)**: pores of 0.15 mm are 2 px, the finest lip line 4 px |
| 10 | Subdivision for the head | `Body.Mesh` gets Subdivision (Catmull–Clark) viewport 1 / render 2 (spec 04's stack: Armature → Corrective Smooth → Subdivision); for the V3–V6 macros the harness raises render to 3 | face quads ≈ 4 mm at level 0 → 1 mm at level 2, 0.5 mm at level 3; `Displace` (step 13) sits **after** Subdivision |
| 11 | Eyes | delete MPFB `high-poly` eyes if present; build per side: `Head.Eye.<L/R>.Globe` UV sphere r 12.0, 64 × 32, scaled (0.98, 1.0, 0.98), front cap (within 5.85 mm of the axis) re-projected onto a sphere r 7.8 whose centre lies 4.2 behind the apex → cornea bulge 1.1 proud; split the cap faces off as `Head.Eye.<L/R>.Cornea` (Solidify 0.55 inward, rim off) and keep the globe closed behind it as the sclera; `Head.Eye.<L/R>.Iris` disc r 5.85 at 3.0 behind the apex, 96 × 12 ring segments, pupil hole r 2.0 (centre 0.3 nasal), outer ring raised 0.3 toward the cornea (conical); `Head.Eye.<L/R>.Wetline` a curve along each lid margin (sampled from the lid-margin edge loop, [VERIFY loop ids], offset 0.2 outward) with bevel r 0.35, 8 sides, as one object per eye; `Head.Eye.<L/R>.Caruncle` metaball-to-mesh or a UV sphere 5 × 3 × 2 at the endocanthion, Subdivision 2; `Head.Eye.<L/R>.Occluder` a copy of the lid-margin loops extruded 1.5 inward along the globe normal with a vertex-colour alpha ramp 0.6 → 0 | origin at the globe centre (±32.5, −88, 1756), +Y toward the back, parented to the eye bones (§7); Bevel none; all shaded smooth; ≈ 2,100 + 330 + 1,150 + 2 × 400 + 200 + 240 ≈ 4,800 faces per eye |
| 12 | Ears, teeth, tongue | ears are part of `Body.Mesh` (MakeHuman ears are well formed: rolled helix, lobe — research B §5), shaped by `l/r-ear-*` targets in table 4.1 and `measure_head()` checks (62 × 36 × 22); meatus: `Head.Key.EarCanal` −8 at the cavum front r 3.5 (a dark pit the shader paints black); teeth `HumanService.add_mhclo_asset(teeth_base, …)` then split into `Head.Teeth.Upper` / `Head.Teeth.Lower` by z of the occlusal plane, gums kept with each; `Head.Tongue` from `tongue01`; materials replaced (§5.7) | names `Head.Teeth.Upper`, `Head.Teeth.Lower`, `Head.Tongue`, `Head.MouthBag` (only if the base lacks one) |
| 13 | Lines, pores, follicles → maps | (a) curves `Head.Curve.Wrinkle.*` built as polylines from the §3.7 paths, each vertex snapped to the surface (`Shrinkwrap` apply, then `convert` to curve); (b) a temporary Geometry Nodes modifier on a level-3 copy `Head.Bake.Mesh` computing **Geometry Proximity** distance to each curve group and storing `wrinkle_dist_<name>`; the shader maps distance → Gaussian depth with the table's width/depth/bulge; (c) pores: Voronoi F1 (`SMOOTH_F1`, randomness 0.9) at the per-region cell size (§3.7, via the region mask), thresholded to the pore diameter, depth from the table; micro-lines: Voronoi `DISTANCE_TO_EDGE` 2 octaves (0.5 and 0.15 cells), 0.03 deep, with Mapping scale (1, 1.6) rotated by the Langer angle per region; (d) follicle pits at the stubble roots (step 14) via Geometry Proximity to the point cloud, 0.25 dia × 0.12; (e) bake `Head.Disp.exr` (4096², 32-bit float, mm/10 encoded as metres, mid 0.5) and `Head.Pores.exr` separately with Cycles **Emit** bakes under `UV.Head` (needs the real selection + active Image Texture node, research C §7 rules) | at render: `Head.Disp.exr` drives a `Displace` modifier (`texture_coords='UV'`, `uv_layer='UV.Head'`, `strength 0.004`, `mid_level 0.5` → ±2 mm range) on the level-2 mesh for the folds ≥ 0.5 mm, and the material's Bump (`displacement_method='BUMP'`, distance 0.3 mm) for pores and micro-lines; no adaptive displacement (research C §4: too expensive) |
| 14 | Stubble and scalp root points (for spec 07 and for step 13d) | GN `Distribute Points on Faces` (Poisson disc, `distance_min` per region 1.1–1.6 mm, density attribute = stubble density map §5.2 × 45/cm², seed 7) → `Head.Points.StubbleRoots` (positions, normals, region id, grey flag 0/1 drawn with the chin 25 % / moustache 10 % / cheeks 0 %) exported to `assets/build/head_stubble_roots.npy` and kept as a point cloud object; same for `Head.Points.ScalpRoots` with the hairline mask | ≈ 9,000 stubble roots, ≈ 60,000 scalp roots; spec 07 grows strands from exactly these |
| 15 | Brows and lashes | Curves objects (`bpy.data.hair_curves`, research C §3): `Head.Brow.<L/R>` 400 curves rooted on the brow band mask (density 350–450 per brow), 8–12 mm, 3 control points, root radius 0.04 mm → tip 0.015, direction field = §3.3 (inner third up-out 60°, body 0–10°, tail down 20°), lying 15° off the skin, 4 % random; `Head.Eye.<L/R>.Lashes.Upper` 130 curves along the anterior lid margin, 8–10 mm (lateral longest), curl 30° up, 2–3 staggered rows (root jitter ±0.4 mm across the margin), radius 0.06 → 0.02; `Head.Eye.<L/R>.Lashes.Lower` 65 curves 5–6 mm down-out; the medial 5 mm of each margin lash-free | `sc.cycles_curves.shape = "THICK"`; parented to the head / eyelid bones (§7); Principled Hair BSDF (§5.6) |
| 16 | Vellus | `Head.Vellus` 25,000 curves 0.5–1.2 mm, radius 0.012 mm, on the cheeks, forehead, nose sides and ears (none on the lids, lips, brows, stubble zones), lying along the Langer angle 15° off the surface | render only in V3–V6 (`Trim` to 0 by camera distance > 1.5 m) |

**Table 4.1 — MPFB targets, start values and roles** (names as in the inventory; weights are the start values of the fit, the fit may move them within the bounds; "solve" = free parameter; "fixed" = not in the fit):

| Group | Target(s) | Start | Bounds | Role / measure it serves |
|---|---|---|---|---|
| Skull | `head-square` 0.5; `head-rectangular` 0.3; (`head-oval` and `head-round` have no negative twin: left at 0, `square` and `rectangular` carry the shape); `head-scale-horiz-incr` 0.2; `head-scale-depth-incr` 0.1; `head-fat-decr` 0.3; `head-age-incr` 0.2; `head-back-scale-depth-incr` 0.1 | as listed | [0, 1] | head breadth 158, length 203, vertical sides, face_width/height |
| Forehead | `forehead-scale-vert-decr` 0.15; `forehead-nubian-incr` 0.15; `forehead-temple-decr` 0.1; `forehead-trans-backward` 0.1 | | [0, 0.6] | upper third 57, slope 12° |
| Brows | `eyebrows-trans-down` 0.4; `eyebrows-angle-down` 0.1; `eyebrows-trans-forward` 0.15 | | [0, 0.8] | brow-to-lid 7, brow Z |
| Eyes (l-/r- pairs, mirrored unless `Asym`) | `eye-scale-incr` 0.25; `eye-trans-in` 0.2; `eye-height1-decr` 0.3; `eye-height2-decr` 0.2; `eye-corner1-up` 0.1; `eye-bag-incr` 0.2; `eye-push1-in` 0.3; `eye-push2-in` 0.3; `eye-eyefold-down` 0.3; `eye-eyefold-concave` 0.2 | | [0, 0.8] | fissure 33 × 9.2, intercanthal 31, IPD 65, apex −4, hooded fold |
| Cheeks | `cheek-bones-incr` 0.5; `cheek-volume-decr` 0.35; `cheek-inner-decr` 0.2; `cheek-trans-up` 0.1 | | [0, 0.8] | malar +3, hollow −3, bizygomatic 152 |
| Nose | `nose-width1-decr` 0.3; `nose-width2-decr` 0.1; `nose-width3-incr` 0.25; `nose-point-width-incr` 0.1; `nose-hump-incr` 0.15; `nose-nostrils-width-incr` 0.2; `nose-nostrils-angle-up` 0.1; `nose-scale-vert-incr` 0.05; `nose-volume-incr` 0.1; `nose-septumangle-incr` 0.05 | | [0, 0.7] | bridge 15, alar 39, length 52, protrusion 20 |
| Mouth | `mouth-scale-horiz-incr` 0.15; `mouth-scale-vert-decr` 0.1; `mouth-upperlip-height-decr` 0.3; `mouth-lowerlip-height-incr` 0.15; `mouth-upperlip-volume-decr` 0.2; `mouth-lowerlip-volume-incr` 0.1; `mouth-cupidsbow-decr` 0.2; `mouth-cupidsbow-width-incr` 0.1; `mouth-philtrum-volume-incr` 0.2; `mouth-angles-down` 0.05; `mouth-dimples-in` 0.1; `mouth-laugh-lines-in` 0.15 | | [0, 0.7] | mouth 57, vermilion 6 / 9.5, philtrum 18 |
| Chin / jaw | `chin-width-incr` 0.4; `chin-height-incr` 0.25; `chin-prominent-incr` 0.4; `chin-jaw-drop-incr` 0.1; `chin-cleft-incr` 0.15; `chin-bones-incr` 0.3 | | [0, 0.9] | chin 46, pogonion Y −117, lower third 71, bigonial 138 (with `Head.Key.Masseter`) |
| Ears | `l/r-ear-lobe-incr` 0.2; `l/r-ear-flap-incr` 0.25; `l/r-ear-shape-square` 0.1; `l/r-ear-wing-incr` 0.1; `l/r-ear-scale-vert-*` solve; `l/r-ear-trans-down` **fixed 0** | | [0, 0.6] | 62 × 36 × 22 |
| Neck (shared with spec 04; this spec reads, 04 writes) | `neck-scale-horiz-incr`, `neck-scale-depth-incr`, `neck-double-decr`, `measure-neck-circ-*` | spec 04 | — | neck 130 / 135 (§10.2) |
| Expression units (`expression/units/caucasian/...` [VERIFY `target_full_path` resolves the subdirectory]) | `eyebrows-left-down`, `eyebrows-right-down` 0.25; `eye-left-slit`, `eye-right-slit` 0.25; `mouth-compression` 0.2 | §7.2 | fixed in the fit | the expression is part of the pose gate, not a fit parameter |

Poly budget (render level 2): head region of `Body.Mesh` ≈ 3,000 base quads → ≈ 48,000; eyes 2 × 4,800; teeth + gums ≈ 6,000; tongue ≈ 1,500; brows 800 curves, lashes 390 curves, vellus 25,000 curves (macros only). Nothing in the head exceeds 0.5 mm face size at level 3 for the macro views.

---

## 5. Materials and textures

### 5.1 UVs and texel density
`UV.Head` (step 9) at 4096² gives ≈ 13.6 px/mm over the face, 0.073 mm/px. All head maps are authored on `UV.Head`; the body's `Skin.Body` material (specs 01/03/04/05) keeps the MakeHuman UV. The two materials meet at the hyoid ring: `Skin.Head` is assigned to the faces above rest h 1622 and its masks feather to the `Skin.Body` neck values over the 1615–1630 band (spec 04's `Torso.Masks2.A` nape blend and `.B` stubble feather are read here through the shared `Skin.Base` node group [VERIFY its name in `scripts/lib/materials.py`]).

### 5.2 Maps (all generated by script, baked once the fit is final, re-baked on any geometry change; `assets/build/head/`)
| Image | Size / format | Channels | Made by |
|---|---|---|---|
| `Head.Albedo.png` | 4096² sRGB 8-bit | base colour after the §5.3 layer stack | Cycles Emit bake of the procedural layer tree (region masks → colours), plus the projected mid-frequency layer |
| `Head.Rough.png` | 4096² linear 8-bit | roughness | bake |
| `Head.Masks.png` | 4096² linear 8-bit | R redness (0–1), G stubble density (0–1 = 0–45 follicles/cm²; the §3.7 zones with 8 mm feathers; 0 above the tragus→cheilion line except 0.25 in the "sparse" band; 1.0 on the chin pad, soul patch, moustache, jawline, under-jaw; falls to 0 at the hyoid), B T-zone sheen (forehead boss, dorsum, tip, malar highlight), A thin-skin SSS multiplier (lids 0.8, lips 1.1, ears 1.5, nose tip 1.1, forehead 0.9) | bake from landmark-distance masks (`face_landmarks.region_mask(name)` builds each as a smooth distance field around the §3.2 points) |
| `Head.Masks2.png` | 4096² | R region id (16 levels: forehead, temple, lid, cheek, hollow, nose, lip, chin, jaw, ear, neck, scalp…), G brow density, B wrinkle proximity (0–1 over 3 mm, for roughness and colour in the creases), A scalp-skin fade (hairline mask for spec 07: 1 inside the hairline, 0.5 over the 6 mm fade band at the temples) | bake |
| `Head.Disp.exr` | 4096² 32-bit | folds ≥ 0.5 mm (nasolabial, sulcus, tear trough, alar groove, cleft, lid creases, glabellar, forehead crease) | step 13 |
| `Head.Pores.exr` | 4096² 32-bit | pores, micro-lines, follicle pits, lip lines | step 13 |
| `Head.Normal.png` | 4096² 16-bit | normal map baked from Disp + Pores on the level-3 mesh (for EEVEE, Workbench and the glTF export) | Cycles Normal bake |
| `Eye.Iris.png` | 2048² sRGB | iris colour (§5.6), polar-mapped | procedural bake |
| `Eye.Iris.Disp.exr` | 2048² | crypts and fibres relief 0.1–0.3 mm | bake |
| `Eye.Sclera.png` | 1024² | sclera colour with canthal yellowing and vessels | bake |

### 5.3 Albedo layer stack (sRGB hex targets; mixed in linear space; every layer is a mask × colour, no painting)
| Layer | Colour / value | Mask | Mix |
|---|---|---|---|
| L0 base | **#b98670** | all | 1.0 |
| L1 olive zones | #b5876e | forehead, chin pad, temples | 0.8 |
| L1 redness | **#c98272** | `Masks.R`: cheeks (malar + buccal, right cheek 1.0, left 0.85), nose tip and alae 1.0, dorsum 0.5, ear lobe and helix 1.0, chin corners 0.4 | 0.45 × mask |
| L1 under-eye | **#9d7266** | tear-trough band 5 mm, lower lid | 0.7 |
| L1 eyelids | #a98078 | upper and lower lid skin to the orbital rim | 0.6 |
| L1 lips | **#9a6a62**, border feather 1.5 mm; inner wet line #8a4f4a | vermilion mask | 1.0 |
| L1 ear cartilage | #c99a84 | helix, antihelix ridges | 0.3 |
| L1 nape / neck | #b07c66 → spec 04's neck values | `Masks2.A` and the hyoid blend | 1.0 |
| L2 projected mid-frequency | the reference projected from the hero camera (`Texture Coordinate → Window` onto `reference_full.png`, baked to `UV.Head`), divided by a white-diffuse irradiance bake of the same frame under the hero lights (albedo estimate), clamped 0.6–1.4 of L0+L1, blurred 3 mm, **right half only** (lit, lum 90–200), mirrored onto the left half through the UV symmetry [VERIFY MakeHuman's head UV is mirror-symmetric; else mirror in 3D by X] | lit-skin mask | 0.4 (the "who": mid-frequency colour zoning the hexes cannot carry) |
| L3 mottling | Noise 6 mm, ±4 % L*, hue ±3° toward red/yellow; Noise 1.5 mm ±2 % | skin | 1.0 |
| L4 stubble shadow | multiply luminance by **0.75** where `Masks.G` = 1 (dense), 0.87 medium, 0.95 sparse, with the hue pulled 30 % toward the hair colour #3b2a22 and saturation −15 %; plus follicle dots #6e5a52 r 0.12 mm at every stubble root (step 14) at 60 % | `Masks.G` | 1.0 — this carries the native-scale darkening (lit chin #815f53 vs cheek #c5907d = −35 %) when the strands (spec 07) are sub-pixel |
| L5 pore and crease darkening | −10 % L* inside pores, −6 % along `Masks2.B` creases | from the EXRs | 1.0 |
| L6 vessels | superficial temporal vein at the right temple from (−55, −40, 1770) up-back 40 mm, #a3807a at 10 %, 1.5 mm wide, 0.3 mm relief; nothing else (no broken capillaries) | curve mask | 0.1 |
| L7 wind-burn | right malar +6 % redness (lit cheek) | malar R | 1.0 |
| none | freckles, moles, scars, sun spots | — | 0 (consolidated) |

### 5.4 `Skin.Head` shader (Principled BSDF, Blender 4.5 sockets; values per region, blended by `Masks2.R` with 8–12 mm feathers)
Shared base: `subsurface_method = "RANDOM_WALK_SKIN"`, Subsurface Weight 1.0, Subsurface IOR 1.4, Anisotropy 0.8; IOR 1.40; Specular IOR Level 0.5; Specular Tint white; Sheen 0.04 (peach fuzz where vellus is not rendered), Sheen Roughness 0.5; `displacement_method = "BUMP"` (Bump node distance 0.3 mm from `Head.Pores.exr`, strength 0.6; `Head.Disp.exr` is the modifier); Normal from `Head.Normal.png` only in EEVEE/Workbench fallbacks.

| Region | Base colour (after §5.3) | Roughness | SSS Scale (m) | SSS Radius (R,G,B) | Coat / Coat rough | Notes |
|---|---|---|---|---|---|---|
| Forehead | #b5876e | 0.42 | 0.0035 | (1.0, 0.2, 0.1) | 0.10 / 0.30 | bone close under the skin; the boss carries the sheen |
| Temples | #b98670 | 0.46 | 0.0035 | same | 0.04 | vein L6 |
| Brow band skin | #b98670 | 0.50 | 0.0035 | same | 0 | under the brow hairs |
| Eyelids | #a98078 | 0.42 | 0.0028 | (1.0, 0.25, 0.12) | 0.06 / 0.25 | thin skin, no pores |
| Cheeks (malar) | #c0876f (L0 + redness) | 0.48 | 0.0040 | (1.0, 0.2, 0.1) | 0.05 / 0.35 | right cheek +wind-burn |
| Sub-zygomatic hollow | #b98670 | 0.50 | 0.0040 | same | 0 | matte |
| Nose dorsum / tip / alae | #c2866f / #c98272 / #c98272 | 0.38 / 0.40 / 0.44 | 0.0040 / 0.0045 / 0.0045 | (1.0, 0.22, 0.1) | 0.12 / 0.28 | the alar rims transmit red under the key |
| Lips | #9a6a62 | 0.45 (0.30 at the inner wet line) | 0.0045 | (1.0, 0.3, 0.15) | 0.08 / 0.2 | pressed, dry hangar: no gloss |
| Philtrum / upper lip skin (moustache zone) | L0 × stubble 0.87 | 0.52 | 0.0038 | (1.0, 0.2, 0.1) | 0 | |
| Chin pad / soul patch (dense stubble) | L0 × 0.75, greyed | 0.55 | 0.0040 | same | 0 | the salt-and-pepper chin |
| Jaw / lower cheek (medium stubble) | L0 × 0.87 | 0.53 | 0.0040 | same | 0 | |
| Under-jaw / submental | L0 × 0.75 → 1.0 at the hyoid | 0.52 | 0.0040 | same | 0 | spec 04 blend |
| Ears | #c2927c, lobe #c07b68 | 0.50 | 0.0060 | (1.0, 0.25, 0.12) | 0.03 | transmission is the look; meatus #050303 |
| Scalp (under hair, spec 07 shows it at the fade) | #b2826c | 0.50 | 0.0035 | same | 0 | `Masks2.A` |

Research C §8 measured that an SSS scale of 0.012 erases a 0.4 mm pore bump; the 0.0028–0.0060 above keep pores visible and cost ≈ 3× a plain surface. The hero key must leave the under-jaw at ≈ #110b06 (consolidated) — no SSS "glow" may lift it: check in V3.

### 5.5 Micro-normal recipe (the bump source, by region; all procedural, baked to `Head.Pores.exr`)
* **Pores:** Voronoi 3D `SMOOTH_F1`, smoothness 0.3, randomness 0.9, cell size = 1/√(density) from §3.7 (forehead 1.2 mm, cheeks 1.4, nose 1.0, tip 0.95, chin 1.3); pore = `F1 < pore_dia/2` with a 0.03 mm soft edge; depth per table; 15 % of pores doubled in size on the nose tip and alae (sebaceous), 8 % elsewhere.
* **Micro-lines (primary skin lines):** two Voronoi `DISTANCE_TO_EDGE` octaves (cells 0.5 and 0.15 mm), line width 0.04 mm, depth 0.03 and 0.015; Mapping scale (1, 1.6, 1) rotated by the Langer angle per region so the polygons are elongated along the lines; this is what gives the skin its anisotropic sheen under the key.
* **Follicle pits:** Geometry Proximity to `Head.Points.StubbleRoots`: pit = smoothstep(0.125 → 0.10 mm), depth 0.12 mm; in the pit centre the hair root (spec 07) sits.
* **Lip lines:** 14 per lip, radial from the stomion, Gaussian width 0.3, depth 0.15; the vermilion gets Noise 0.4 mm, 0.02 mm.
* **Eyelid crosshatch:** Voronoi `DISTANCE_TO_EDGE` 0.3 mm cells, 0.01 mm; no pores.
* **Ear:** pores 1.0 mm cells, 0.05 deep; the helix rim smoother (roughness −0.05).
* **Roughness coupling:** roughness +0.10 inside pores and pits, −0.06 on the micro-line ridges of the T-zone, +0.05 along creases (`Masks2.B`).

### 5.6 Eye materials
| Material | Nodes and values |
|---|---|
| `Eye.Cornea` | Glass-like Principled: Base Color white, Transmission 1.0, IOR 1.376, Roughness 0.0, Coat 0; `Light Path → Is Shadow Ray` mixes to Transparent so the cornea casts no black shadow on the iris; refraction is what sinks the iris 3 mm behind the apex and bends the limbal ring — never fake it with a flat eye |
| `Eye.Iris` | Base Color `Eye.Iris.png`: body **#5b4a3e**, collarette #6a5243, fibres #6e6253 (180–220 radial lines: Noise with Mapping scale (1, 60) in polar UV, contrast 0.6), crypts #3f322b (Voronoi F1 cells 0.9 mm, 10–16 kept by threshold between r 2.6 and 4.5), contraction furrows −0.02 × 3 rings, limbal ring #3a2d26 over the outer 0.6 mm with a 0.3 soft edge; Roughness 0.5; SSS off; Bump from `Eye.Iris.Disp.exr` 0.15 mm; pupil disc #050404 |
| `Eye.Sclera` | Base Color `Eye.Sclera.png` (#e6e0da, canthal #d9c9b4, vessels), Roughness 0.25, SSS Random Walk scale 0.002, radius (1.0, 0.4, 0.3), Coat 0.3 (the glossy conjunctiva), IOR 1.38 |
| `Eye.Wet` | Transmission 1.0, IOR 1.33, Roughness 0.05, Base Color white; it produces the second specular streak under the catchlight (the reference shows the catchlight at (794,77) **lateral-upper** of the pupil — the key is upper-left of the camera from his right) |
| `Eye.Caruncle` | #b0695c, Roughness 0.3, SSS scale 0.003, Coat 0.4 |
| `Eye.Occluder` | Transparent × Diffuse #1a0f0a mixed by the vertex alpha; shadow rays transparent |
| `Hair.Lash` / `Hair.Brow` | Principled Hair BSDF (Chiang), Melanin 0.95 / 0.85, Melanin Redness 0.3 / 0.45 (brows warm **#5a3d30** asset recolour target), Roughness 0.3, Radial Roughness 0.3, Coat 0.1, IOR 1.55, Random Color 0.1; brows get 5 % of strands at Melanin 0.6 (lighter tips) |

### 5.7 Teeth, gums, tongue, cavity
`Teeth.Enamel`: Base Color gradient incisal #e9e1d3 → gingival #d9c7a9 (by distance from the gum line), Roughness 0.25, SSS scale 0.002 radius (1.0, 0.8, 0.6), Coat 0.5 (saliva), IOR 1.6; embrasure stain #b89a7a 20 %. `Teeth.Gums`: #b45e5e, Roughness 0.35, SSS 0.003, Coat 0.3. `Tongue`: dorsum #b86a6c with papillae bump (Voronoi 0.6 mm, 0.3 deep), Roughness 0.3, Coat 0.5, SSS 0.004; underside #c97b7d. `MouthBag`: #3a1612, Roughness 0.15. None of this is visible in the hero frame; it exists so the jaw can open without showing a void.

### 5.8 Bake pipeline (`face_textures.py`, called by the part script after the fit is final)
1. Build `Head.Bake.Mesh` = evaluated `Body.Mesh` head island at level 3 (`object.convert` of a copy), `UV.Head` active.
2. For each map in §5.2: assemble the procedural node tree on a bake material, add the target Image Texture node (active), real selection (`view_layer.objects.active`, `select_set`), `bpy.ops.object.bake(type='EMIT', margin=16)`; EXRs as `float_buffer=True`.
3. `Head.Normal.png`: `bake(type='NORMAL')` from a level-3 copy displaced by the two EXRs (temporary Displace modifiers) onto the level-2 mesh.
4. Write all images to `assets/build/head/`, pack nothing in the .blend; the final `Skin.Head` material references the files. Time: ≈ 2–4 min CPU per 4K Emit bake on this box [VERIFY with the first run]; the whole set under 20 min, run once per geometry change, so the likeness loop itself never bakes.

---

## 6. Fibres, simulation or dynamics

No cloth and no dynamics in this part. Fibres built here: brows (2 × 400), upper lashes (2 × 130), lower lashes (2 × 65), vellus (25,000, macro views only) — parameters in §4 steps 15–16 and §5.6. Fibres **not** built here but seeded here: beard stubble (≈ 9,000 roots, 2.5–4 mm, chin/moustache 4, cheeks 2, 25 % grey on the chin and soul patch, 10 % on the moustache) and scalp hair (≈ 60,000 roots, 35–45 mm top → 1 mm fade) — spec 07 grows them from `Head.Points.StubbleRoots` / `Head.Points.ScalpRoots` with the grey flags and the direction fields this spec writes (stubble: along the Langer angle, 25° off the skin, chin downward; the hairline and fade masks in `Head.Masks2.A`). Brow and lash curves are static; they ride the lid and brow geometry through the Armature modifier on the Curves objects (`Surface` set to `Body.Mesh`, `surface_uv_map = 'UV.Head'`, so they follow shape keys too — research C §3 confirmed GN/Curves evaluate headless).

Eye wet line: the tear meniscus is geometry (step 11), not a simulation; it is rebuilt from the lid-margin loop whenever the lid keys change (a driver re-samples the curve on key change is unnecessary — the `Wetline` object is parented to the lid bones and gets the same shape keys through a `Surface Deform` bind to `Body.Mesh` [VERIFY bind works with shape keys active; fallback `Shrinkwrap` + `Smooth`]).

---

## 7. Rigging and attachment

### 7.1 Bones (MPFB `default` rig, MakeHuman naming, 163 bones; names to be dumped to `renders/06_head/bones.json` at step 1 and mapped through `scripts/lib/rig_names.py` roles) [VERIFY every name]
| Role | Expected bone | Head / tail (rest, mm) | Drives |
|---|---|---|---|
| HEAD | `head` | (0, −8, 1667) → (0, −10, 1877) | the skull, face, ears, upper teeth, brows, upper lashes, the eye bones' parent |
| JAW | `jaw` | (0, +10, 1700) (condyles ±55, +5, 1740 as the hinge axis) → menton | lower teeth, tongue root, the chin and lower lip weights; rotation 0 in the hero pose (lips closed), `JawClench` key driven by its −2° |
| EYE_L / EYE_R | `eye.L` / `eye.R` | the globe centres (±32.5, −88, 1756), length 12 | `Head.Eye.*` objects parented with `parent_set(type='BONE')` (real selection, research C §7); gaze via `Damped Track` to `Head.GazeTarget` |
| EYELID_UPPER/LOWER_L/R | `orbicularis03/04.L/R` or `levator*`-class face bones if present; else none | — | if present: Copy Rotation 0.2 from the eye bones for lid-follow; else the lid follows through the `eye-*-slit` keys only |
| TONGUE | `tongue00…` chain if present, else JAW | — | `Head.Tongue` |
| NECK_HIGH | `neck03` | spec 04 | the hyoid blend band weights are spec 04's |

If the `default` rig lacks eye bones [VERIFY], the script adds `eye.L/R` to the armature in Edit mode (real `mode_set`) parented to `head` and weights the eye objects 1.0 to them. The game export (`game_engine` rig, 53 bones) keeps `head`, `jaw`, `eye.L/R` and bakes every facial key into the mesh at its hero value.

### 7.2 Shape keys (on `Body.Mesh`; "hero value" is what the game export bakes in)
| Key | Source | Hero value | Note |
|---|---|---|---|
| MPFB targets of table 4.1 | targets | as fitted | identity |
| `Head.Key.*` of step 8 | scripted | as fitted (0.5–1.0) | identity |
| `Head.Key.Asym` | scripted | 1.0 | §3.3 |
| `Expr.BrowLower.L/R` = `eyebrows-left/right-down` | MPFB unit | **0.25** | corrugator; also deepens the glabellar lines via `Masks2.B` × key value in the Displace strength (driver) |
| `Expr.LidTighten.L/R` = `eye-left/right-slit` | MPFB unit | **0.25** | squint; fissure 9.2 → ≈ 8.5 mm |
| `Expr.LipsPress` = `mouth-compression` | MPFB unit | **0.20** | plus `Head.Key.LipPress` 1.0 |
| `Expr.Mentalis` | scripted: chin pad up 1.5 mm, sulcus −0.5, lower lip up 0.5 | **0.30** | MediaPipe's mouthShrugLower 0.58 on the reference; the "set jaw" read |
| `Expr.JawClench` | scripted: masseter +2 at (±66, +4, 1692) r 14, temporalis +1 at (±60, −20, 1800) r 15 | **0.10** | driven by the jaw bone's −2° (closed hard) |
| `Expr.MouthCornersDown` = `mouth-angles-down` extra | MPFB | 0.05 | stern |
| `Expr.Smile`, `Expr.MouthOpen`, `Expr.BrowRaise.L/R`, `Expr.Blink.L/R` (`eye-*-closure`) | MPFB units | 0 | game use later |
| `Head.Key.EarCanal` | scripted | 1.0 | |

### 7.3 Head pose (hero) and gaze
Spec 04 §7.3 distributes the turn: `neck01` yaw +3°, `neck02` +4°, `neck03` +5°, `head` +13° → **+20° world** (nose toward +X, his left); pitch `neck02` −1°, `neck03` −1°, `head` −3° → 5° chin-up; roll 0. This spec checks the result by MediaPipe on the V1 render (gate ±2° of the reference +14.6°, −9.9°, −1.2° in its convention) and may trim `head` by up to ±3° to pass the gate — any larger error is spec 04's and is reported, not hidden. Gaze: `Head.GazeTarget` empty at 25 m along the posed head axis rotated a further +4° about Z and +2° up; eye bones `Damped Track`; convergence at 25 m is 0.07°, i.e. parallel. Eye-bone roll 0.

### 7.4 Attachment and deformation order
`Body.Mesh` modifier order (shared, spec 04 §9.4): Armature → Corrective Smooth → Subdivision → **Displace (`Head.Disp.exr`, vertex group `head_disp`, fading to 0 over the hyoid band)**. Eyes, teeth, tongue, caruncles, occluders: bone-parented rigid. Wetlines: `Surface Deform` to `Body.Mesh`. Brows, lashes, vellus: Curves with `Surface = Body.Mesh` (they follow deformation natively). Weights: MakeHuman's imported head/jaw/eye weights (`import_weights=True`) are kept; the script checks that no vertex above the hyoid has weight on any bone below `neck03` and that the jaw's weights stop at the mandibular lower border + 10 mm (no chin skin pulled down by the neck).

---
## 8. Evaluation protocol

### 8.1 Render set (`scripts/eval/head_eval.py`, run by the part script at the end of every build)
Two scenes. **Look-dev:** spec 01 §8.1's neutral scene (grey floor, three soft area lights at 45° / −45° / rim, AgX Base Contrast) with Workbench (matcap + cavity, ≈ 5 s per view, the iteration renderer) and Cycles 48 spp for the record. **Hero:** the consolidated §8 camera and lights (key 800 W area 1.5 m at (−1.70, −2.00, 3.60) → (0, 0, 1.25) 4500 K; cool 600 W 3 m at (3.20, 0.60, 3.60); world 0.05; floor pool light-linked to the floor; AgX Medium High Contrast; compositor as consolidated), with `scene.render.use_persistent_data = True`, adaptive sampling 0.02, OIDN `RGB_ALBEDO_NORMAL`. Views V1–V6 of §1.3. Budget on this box (research C: ≈ 1–2 MP·spp/s, SSS ×3): V1 850² at 64 spp ≈ 3–5 min, each macro 1024² ≈ 6–10 min; the full hero set ≈ 40 min, so the Cycles set runs once per milestone and the Workbench set on every change. On Jeff's GPU machine the same set is under a minute. Outputs `renders/06_head/V1_hero_x5.png`, `V1_native.png`, `V1_alpha.png`, `V2_front.png`, `V2_profile.png`, `V3…V6_hero.png`, plus the overlays and the JSON report below; the latest V1 pair is copied to `renders/eval/06_head_V1.png` (committed).

### 8.2 Metrics (`scripts/eval/head_metrics.py` → `renders/06_head/metrics.json`; every number also printed as PASS/FAIL)

**A. Landmark ratios** (MediaPipe on the V1 ×5 render vs `assets/ai/face_ref_landmarks.json`; the same detector, the same crop framing; bias-corrected per §4 step 7). "Adopted target" is what the render must hit; where it differs from the image value the difference is a §2.5 decision, not an error.

| Ratio (MediaPipe `ratios` key or manual landmarks) | Image value | Adopted target | Tolerance | Weight |
|---|---|---|---|---|
| face_width_over_height | 0.900 | 0.900 | ±5 % | 1 |
| jaw_width_over_face_width | 0.839 | 0.860 | ±5 % | **2** |
| ipd_inner_over_face_width | 0.244 | 0.244 | ±4 % | **2** |
| ipd_outer_over_face_width | 0.609 | 0.590 | ±5 % | 1 |
| mouth_width_over_ipd_outer | 0.585 | 0.590 | ±5 % | 1 |
| nose_width_over_ipd_inner | 1.152 | **1.03** (alar 39, decision 2) | ±6 % | 1 |
| nose_length_over_face_height | 0.235 | 0.235 | ±5 % | 1 |
| eye_to_mouth_over_face_height | 0.447 | 0.447 | ±4 % | 1 |
| nose_to_chin_over_face_height | 0.460 | 0.460 | ±4 % | **2** (the long lower third) |
| eye_to_chin_over_face_height | 0.717 | 0.717 | ±4 % | 1 |
| eye_aspect_h_over_w | 0.329 | 0.329 | ±8 % | **2** (expression-dependent) |
| lip_height_over_mouth_width | 0.249 | 0.249 | ±8 % | 1 |
| nose_length_over_nose_width | 0.930 | **1.05** (decision 2) | ±6 % | 1 |
| intercanthal / fissure (manual, 133–362 / 33–133) | 0.78 | **0.94** (decision 1) | ±6 % | 1 |
| bigonial / bizygomatic (manual) | 1.0 proj. (0.9 corr.) | 0.91 | ±5 % | **2** |
| chin pad width / mouth width (manual, lit pad) | 0.88 | 0.81 | ±6 % | **2** |
| brow lower edge → upper lid margin (mm, projected) | ≈4 | ≈4 projected (7 true) | ±1.5 mm | **2** |
| canthal tilt (°) | +4 | +4 | ±2° | 1 |

Score: weighted mean absolute delta ≤ 3 % and no row outside its tolerance → PASS. Noise floor 1–4 % (research E §3): a row inside 3 % is not to be chased.

**B. Shape:** NME ≤ 0.040 (Procrustes-aligned 468 points, normalised by outer inter-ocular distance; alae and exocanthi weight 0.5); silhouette IoU ≥ 0.95 (V1 alpha vs reference mask lum > 45, 3 px edge band ignored; hair band separately for spec 07); pose gate ±2°; blendshapes browDown, eyeSquint, mouthPress, mouthShrugLower within ±0.15 of the reference's.

**C. Colour** (V1 ×5 hero render, 5 × 5 means at the reference pixels, converted to CIE Lab):

| Point | Reference hex | Tolerance ΔE |
|---|---|---|
| Forehead region mean (795–825, 52–66) | #b98879 | 4 |
| Right cheek region mean (782–800, 84–98) | #c5907d | 4 |
| Nose dorsum region mean | #d19a88 | 4 |
| Right temple hot spot (782,72) | #dbb49d | 6 |
| Zygoma highlight (780,88) | #ecc3ad | 6 (specular; position within 2 px) |
| Cheek hollow (786,102) | #c08c77 | 6 |
| Under-eye right (798,83) | #ac7c6d | 6 |
| Chin pad, stubbled (818,123) | #7e5d51 | 6 |
| Jaw region, medium stubble (772–790, 112–124) | #a97d66 | 6 |
| Upper / lower lip means | #7f574f / #8a5c55 | 6 |
| Ear lobe (765,108) | #d48b72 | 6 |
| Right iris mean | #5d3e34 | 6; **zero blue-hue pixels** |
| Left cheek, cool side (842,92) | #ae8e8c | 6 |
| Under-jaw (805,138) | #100a04 | 6 (lum ≤ 16) |

**D. Absolute geometry** (`measure_head()` on the rest mesh, landmark vertices): every §3.1–§3.5 value within tolerance (breadths/heights ±3, eye and nose ±1.5, ear ±2, lips ±0.8 mm); E-line distances 6.5 / 3.4 ± 1.5; iris cover 20 ± 5 %; pupil 4.0 ± 0.3.

**E. Texture:** high-pass (3 × 3) luminance texture on the V1 ×5 render in the chin, jaw and cheek regions = 4.7 / 5.2 / 2.4 ± 1.5 (face note §11); pore count on a 10 × 10 mm patch of V3 cheek = 50 ± 15, nose tip 110 ± 30 (counted by local-minimum detection on the Pores EXR rendering, not on the beauty).

### 8.3 Overlays and critic materials (written next to the metrics)
`fit_overlay.png` (landmarks red/cyan ×5), `onion_50.png` (50 % reference over V1), `edges.png` (Sobel, two colours), `flip_pair.png` (mirrored reference beside mirrored render), `squint_strip.png` (native 170 px, 85 px and ×5 for both), `triple_blind.png` (V1 native beside the MPFB-default and 3DDFA decoys in random order, key in the JSON), `profile_vs_3ddfa.png`.

Critic questions (answered yes/no with a note; three "no" on identity questions fails the build):
1. At native size and at 50 %, is this the same man as the reference (not "a soldier")?
2. Is the head a long square-oblong with vertical temple-to-jaw sides, or has it gone oval/round?
3. Do the brows press down on hooded, deep-set, narrowed, close-set eyes? Can you see too much upper lid or any sclera below the iris?
4. Is the nose straight with a narrow high bridge and a visibly broader base, with a slight hump, seen from 13° below with both nostrils?
5. Is the upper lip thin and pressed, the lower fuller, the philtrum long with visible columns?
6. Is the chin broad, square-cornered and projecting with a faint cleft and a defined sulcus — does it overhang the neck into a black shadow?
7. Is the jaw straight with a real gonial corner and a masseter, not a rounded MakeHuman jaw?
8. Are the eyes dark warm brown-grey with a strong limbal ring? Is the catchlight upper-lateral? Is the medial canthus dark? Is there a wet line?
9. Is the skin skin: pores where they belong, the 11 lines, the forehead crease, crow's feet, nasolabial folds; a greyer stubbled chin against a warm jaw; red at the nose tip, ears and cheeks; sheen only on the T-zone; no wax, no glow, no plastic?
10. Does the right ear show a rolled helix, a lit concha, a free lobe glowing red?
11. Is anything symmetric in a way a real face is not (identical crow's feet, mirrored pores, identical brows)?
12. Is anything from MakeHuman still visible (cap hair, card brows, cartoon iris, default skin)?

### 8.4 Failure modes and the fix each points to
| Symptom | Likely cause | Fix |
|---|---|---|
| Pose gate fails by > 2° | spec 04's neck split, or the camera | fix the rig pose / camera first; never tune the face against a wrong pose |
| Ratios pass, NME fails | cheek contour, lip shape or jaw line wrong between landmarks | raise the 3DDFA residual weight to 1.0; enable the mid-band Shrinkwrap at 0.3; add `Head.Key.*` detail |
| Eyes read too open / round | lid keys and `eye-height1-decr` fighting the `slit` expression; brow not low enough | re-solve with the expression ON (it is, by rule); check brow-to-lid 7 mm on the rest mesh |
| Eyes read blue or light | sclera too white, iris too light or saturated, missing limbal ring, missing occluder | check §5.6 values; iris mean must be ≈ #5d3e34 in V1 |
| Face reads MakeHuman-oval | `head-square/rectangular` under-weighted; the fit regulariser too strong | lower λ to 0.03; widen bounds |
| Waxy / glowing skin | SSS scale too large, Coat too high, key too strong | scale ≤ 0.0045 except ears; Coat ≤ 0.12; key calibration targets (consolidated §8) |
| Chin shadow not black | floor bounce or under fill on; SSS lifting | under fill OFF (consolidated dispute #9); check world 0.05 |
| Stubble zone not darker at native scale | relying on strands alone | L4 albedo darkening must carry it (0.75 dense) |
| Pores invisible | SSS smoothing, bump distance too small, 4K map undersampled | SSS scale per §5.4; Bump distance 0.3 mm; UV.Head fills the square |
| Detector cannot find a face on a matcap render | MediaPipe needs skin-like shading | EEVEE flat skin fallback (step 7) |
| Landmark vertex ids drift | somebody changed the base topology (asset masks, decimation) | ids are per topology; re-run step 2 |

---

## 9. Build order, effort and risks

### 9.1 Order
1. **S1 Harness (cloud, 1 session):** `face_landmarks.py` (ids, projection, detector wrappers), `measure_head()`, `Head.Cam.Fit` with the border crop, the pose gate, the metrics script with the §8.2 tables; prove the loop on the MPFB default head (expect every identity ratio to fail — that is the baseline).
2. **S2 Targets fit (cloud, 1–2 sessions):** table 4.1 start → inner loop → outer gate; expect PASS on 12 of 18 rows after two outer iterations; the misses are the brow ridge, jaw and hood (no targets) and go to S3.
3. **S3 Scripted keys (cloud, 1 session):** step 8 keys, second fit pass, the §3.3 asymmetries; V2 mugshots against the tables and the 3DDFA profile.
4. **S4 Eyes, ears, mouth (cloud, 1 session):** step 11–12 geometry with placeholder materials; V4/V6 Workbench checks.
5. **S5 Maps (cloud, 1–2 sessions):** curves, pores, follicles, bakes (§5.8), the projected albedo layer; V3/V5 at Cycles 32 spp to see them.
6. **S6 Shader look-dev (GPU machine, 2 sessions):** §5.4 per-region values against the §8.2-C colour points and the critic questions; brows, lashes, vellus; hand-off to spec 07 (roots, masks).
7. **S7 Critic rounds (both, ongoing):** V1 ×5 and native, triple-blind, flip; iterate S2/S3/S5 as the critic directs; commit `renders/eval/06_head_V1.png` at each milestone.

### 9.2 Effort
Code: ≈ 1,800 lines (fit 450, landmarks 300, textures 500, geometry 400, metrics 150). Compute per iteration: inner loop seconds; outer gate 5–45 s; Cycles V1 3–5 min CPU (seconds on GPU); full hero set 40 min CPU once per milestone; bakes 20 min once per geometry change.

### 9.3 Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The ratio fit converges but the face still "isn't him" (the ratios are necessary, not sufficient) | high | high | the projected mid-frequency albedo (L2), the scripted keys, the critic loop; accept "credible stern 40-year-old soldier with his proportions" as the floor (research B §5 realism budget) |
| MediaPipe bias between a render and a photo-like generation | medium | medium | bias correction (step 7); the projected-vertex ratios are the inner truth |
| MPFB target cross-talk (e.g. `chin-prominent` also lengthens the face) | high | low | the Jacobian captures it; the LM step handles coupling; clamp 0.15 |
| Expression units path (`units/caucasian/...`) does not resolve through `target_full_path` | medium | low | load by absolute file path under `data/targets/expression/units/caucasian/` |
| No eye/jaw bones in the `default` rig | low | medium | add bones in Edit mode (§7.1) |
| 4K Emit bakes slow or the bake selection rules bite headless | medium | low | research C §7 rules; bake at 2K first, 4K at milestones |
| SSS at 0.004 still erases pores at the V1 scale | low | low | pores are invisible at 2.1 mm/px anyway; they are for V3–V6 |
| UV.Head mirror symmetry assumption (L2 mirroring) | medium | low | mirror in 3D by X instead (bake from a mirrored projection) |
| Spec 04 keeps neck 135 with bigonial 138 → neck as wide as the jaw | medium | medium | §10.2 Q1 to the client; the V3 render shows it |
| CPU render budget stalls the look-dev | high | medium | look-dev on the GPU machine (CLAUDE.md "Where work runs"); cloud does geometry and metrics only |

---

## 10. Interfaces and open questions for the client

### 10.1 What neighbouring parts must provide or respect
| Part | This part provides | This part needs / the neighbour must respect |
|---|---|---|
| Torso and neck (04) | the chin projection (pogonion Y −117, menton (0, −98, 1640)) and the under-jaw plane (menton → hyoid, cervicomental 105°) that make the neck shadow; bigonial **138** at (±69, +20, 1678); gonion and mastoid positions; head rest heading −Y; the beard neckline fading to 0 at the hyoid ring (rest 1620 ± 5, image y 140–142 → posed 1598); the nape hairline at ≈ (0, +70, 1665) (04 wrote ≈1650 — reconcile at the critique pass); `Skin.Head` reads `Torso.Masks2.A/B` in the 1615–1630 band | the hyoid join ring (rest 1622, blend 1615–1630); the neck axis and the `NeckTurn` corrective (no SCM here); the neck split of the +20° / 5° head pose (§7.3); neck breadth **130** proposed instead of 135 (Q1); `neck-*` targets are 04's parameters, read-only here |
| Hair and stubble (07) | `Head.Points.StubbleRoots` (≈ 9,000, with grey flags and region ids) and `Head.Points.ScalpRoots` (≈ 60,000) as point clouds and `.npy`; `Head.Masks.G` stubble density, `Head.Masks2.A` hairline/fade and `.G` brow density; the follicle pits in `Head.Pores.exr` at exactly those roots; the skin colour under the hair (#b2826c scalp, L4 stubble shadow); the hairline polyline (trichion (0, −91, 1825), temple corners (±58, −62, 1822), sideburn end at the tragus level, nape 1665) | strands rooted only at the provided points; stubble 2.5–4 mm, 25 % grey on the chin/soul patch, 10 % moustache, 0 cheeks; the fade reaching skin at the ear-top level; silhouette spikes 8–10 (IoU ≥ 0.85 in y 14–48); no proxy hair cap, no card brows (brows are this spec's) |
| Rig and pose (08) | the facial key list (§7.2) with hero values; `Head.GazeTarget`; the eye/jaw bone roles; the ±3° head-trim allowance | `head` +13° within the +20° world total; `Corrective Smooth` before `Subdivision`; the game export bakes the hero expression and keeps `head`, `jaw`, `eye.L/R` |
| Shirt and gaiter (10) | the jaw's lower border polyline (gonion → menton) at rest and posed, the submental plane, the ear-lobe bottom (±76, −2, 1720 rest; posed 1659 at the right ear) | the gaiter's top roll stays **≥ 25 mm below the gonion** (posed gonion 1658; spec 04's `Torso.Ring.Gaiter.Top` back-left 1625 is 33 below — keep it) and ≥ 40 mm below the menton at the front (front roll 1574 vs menton 1618 ✓); the roll must not touch the stubble zone above the hyoid |
| Materials library (16) | `Skin.Head` and its nine maps, `Eye.*`, `Teeth.*`, `Tongue`, `Hair.Lash/Brow`, the region-mask builder `face_landmarks.region_mask()` | the shared `Skin.Base` group (name [VERIFY]), the hero light rig, AgX settings |
| Evaluation (17) | `head_metrics.py`, the §8.2 tables, the overlays, `renders/eval/06_head_V1.png` | the hero camera and lights exactly as consolidated §8; `rembg` mask of the reference (`assets/ai/rembg_out/soldier_full_u2net_mask.png`) |
| Game export (18) | the head at rest with keys baked; `Head.Normal.png` for engines without displacement | the export scale 1800 / 1877 (rest) — note the rules' eye height 1.65 of 1.80 (0.917) vs this body's 1734 / 1855 (0.935): the rules' man is the rules' man; nothing here changes for it |

### 10.2 Questions for the client
1. **Neck vs jaw.** Reality puts the bigonial at ≈138 mm, not the drawn 157; spec 04's neck breadth 135 would then be almost as wide as the jaw. Accept neck **130** (0.94 of the jaw, still thick) or keep 135?
2. **Eye and nose sizes.** Confirm decisions 1–2: fissure 33 mm and alar 39 mm (human maxima) instead of the drawn 38 / 45, accepting that the face reads a touch less "big-eyed" than the drawing at ×5 and identically at native scale.
3. **Likeness floor.** If the ratios all pass but the critic still says "not him", how many critic rounds before "credible stern soldier with his proportions" is accepted?
4. **Asymmetries.** Keep the ≤ 1.5 mm scripted asymmetries (realism) or build a perfectly symmetric face as the analysts read it?
5. **Teeth and tongue.** Build in full (hidden now, needed for any speech or open-mouth pose later) or a closed-mouth stub?
6. **Vellus.** Render the 25,000 vellus hairs in the macro views only (as specified) or also in the hero frame (invisible, costs render time)?
7. **Projected albedo.** Allow the 40 % mid-frequency layer projected from the AI image (it carries "who" but also the generator's lighting errors) or go fully procedural from the hex table?

### 10.3 Items tagged [VERIFY]
* MPFB `default` rig bone names (`head`, `jaw`, `eye.L/R`, lid/tongue bones) — dumped at step 1.
* `target_full_path()` resolution of `expression/units/caucasian/*` names.
* Whether the MakeHuman head UV island is seamed from the body and mirror-symmetric; the lid-margin edge-loop ids (found by geometry: the loops bounding the eye socket hole, nearest the globe).
* MediaPipe detection on a Workbench matcap render (fallbacks listed).
* Existence of the inner mouth bag on the base mesh.
* `Surface Deform` binding with shape keys active (wetlines).
* Emit-bake time at 4K on this box.
* The name of the shared skin node group (`Skin.Base`) and `Body.Mesh` as the final body name.
* All S-std constants (cornea 7.8 / 11.7 / 2.64, anterior chamber 3.0, iris 11.7, tooth crown sizes, Farkas norms) are textbook values quoted from memory and from research D's snippets, not re-looked-up here.
* The ANSUR bigonial breadth (not in research D's table; decision 5 uses the 0.78–0.9 ratio range).
