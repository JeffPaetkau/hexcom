# Head (head shape, face likeness, eyes, hair, stubble)

## Pipeline

The head is split over two scripts.

**The face is MPFB face/head targets on `Body.Mesh`.** `scripts/parts/head.py --fit` fits them and writes them to `scripts/parts/head_fit.json`; `scripts/stages/base.py` applies them like the body targets. This keeps the pipeline clean:
- the eye bones, the MHCLO eyes/brows/lashes and the landmarks `pose.py` fits all follow the face;
- every part built on base.blend sees the same face;
- there is no second copy of the head.

**The hair cap and the stubble are this part's own objects.** They are `Head.Hair` and `Head.Stubble` in `Part.Head`, built on the rest body, bound to `Morgan.Rig` like the garments, and cached in `cache/parts/head.blend` (+ `head.json`).

Commands:

```
"$SGT_PYIMG" -I scripts/parts/head.py --fit --fresh --iters 4   # ~80 s: the likeness fit, then base.py
"$SGT_BLENDER" -b cache/stages/base.blend --python scripts/stages/pose.py -- --solve
"$SGT_PYIMG" -I scripts/parts/head.py --check after              # ~15 s: landmark residual, no nuisance
"$SGT_BLENDER" -b --python scripts/parts/head.py [-- --no-render] [--samples 64]   # ~25 s: the part + renders
```

The skin tone, the eye materials and the eyebrow asset (`eyebrow001`) are set in base.py; body.md §3 covers the eyes.

Round 2 (§6) adds a third piece: `scripts/parts/head_shape.py` fits a free-form corrective, `scripts/parts/head-shape.target`
(MPFB target format, loaded by base.py after head_fit.json's targets), and `scripts/parts/head_skin.py` holds the skin,
stubble and eye material changes for base.py to call. Until they are wired (§6.6), both are applied to development copies:

```
"$SGT_PYIMG" -I scripts/parts/head_shape.py --fit --rounds 3        # ~110 s: writes head-shape.target, head_shape.json
"$SGT_PYIMG" -I scripts/parts/head_shape.py --check after --blend cache/head_r2/dev_base.blend   # the numbers
"$SGT_BLENDER" -b --python scripts/parts/head.py -- --dev --prefix head_r2_ --samples 64          # ~75 s: part + renders
```

Rounds 3 and 4 of the shape (§10, §11) are developed beside it on copies and write their own targets
(`head-shape-r3.target`, `head-shape-r4.target`); switching is a copy over `head-shape.target` (§11.6).

## 1. What it is

The face of a 38 to 42-year-old Caucasian man. The real-world numbers are take 1's (spec 06 §2.5 and §3, where the image was overruled by norms):
- interpupillary 65 mm;
- eye fissure 33;
- alar base 39;
- mouth 57;
- bizygomatic 152, bigonial 138;
- vertex to menton 237.

The hair is a short textured crop: the top 35 to 45 mm long, the sides tapered from 3 to 1 mm into the skin at the ear top. The stubble is 3 to 5 days old, 2.5 to 4 mm long.

## 2. What the reference shows

Evidence:
- `ref/crop_head_face.png`, `ref/face_zooms/`;
- take 1's `archive/v1/notes/analysis_face_grooming.md` and `archive/v1/spec/06_head_face.md` §2–§3;
- MediaPipe's 478 landmarks (re-run here on the crop with take 1's model).

What the image shows:
- **Pose.** Head yaw about 20° to his left (nose toward the viewer's right), about 12° chin-up to the camera ray.
- **Face shape.** A long, rectangular face with vertical temple-to-jaw sides. The jaw is strong and angular (gonial angle about 118°). The chin is broad and square. The lower third is long.
- **Cheeks and brows.** High cheekbones over hollow cheeks. Low, straight, dense brows. Hooded, deep-set eyes. Dark warm brown-grey irises.
- **Nose and mouth.** A straight nose with a broad base. A thin upper lip.
- **Hair.** Medium-dark brown, piecey and swept up and to his right, with a fade at the sides.
- **Stubble.** Dense on the chin, moustache, jawline and under the jaw; medium on the lower cheeks; greyer on the chin.
- **Skin.** Light-medium; lit cheek `#c6907e`, forehead `#ba897a` (3 × 3 region means re-sampled here).

## 3. Round 1 (2026-11-14)

### The likeness fit (head.py --fit)

Each iteration does the following.

1. **Rebuild the body.** base.py rebuilds the body with the current head_fit.json.
2. **Export and render (Blender).** Blender exports:
   - the posed head region (4361 vertices, head-weighted skin);
   - each vertex's linear-blend-skinning matrix from the hero pose (checked against Blender's own evaluated mesh: 0.0003 mm);
   - the displacement of each of 100 MPFB targets.

   It also renders the posed head through the hero camera (preset `ref.head_face`, Workbench, material colours).
3. **Detect landmarks.** MediaPipe's face landmarker reads that render and the reference crop.
4. **Find the correspondences.** Each model landmark is cast back through the hero camera onto the posed mesh (triangle + barycentric).
5. **Leave out unreliable points:**
   - the iris points;
   - the forehead rows and upper face oval, which sit at the reference's hairline (the bald model has none);
   - hits more than 40 mm behind the median depth (through the eye fissures);
   - the bottom of the chin outline (see below).
6. **Solve.** `scipy.optimize.least_squares` solves 81 parameters:
   - each is one MPFB target, or left and right together (the face is fitted symmetric), bounded to [0, 1];
   - plus a nuisance head rotation (σ 12°) and image shift (σ 4 px), so the face does not absorb the pose's error.

The residuals are:
- **Landmarks.** Each landmark's reprojection, σ 2 px (full frame; the jaw oval weighted 1.5).
- **Hand-read points.** The pose solve's own hand-read head points: nose tip, menton and right ear, at their pose_solve.py sigmas and weight 10. They are measured on the same model points base.py's `landmarks()` defines, so the face the fit makes is one the pose solve will put in the same place.
- **Priors.** The analysis's form readings (§4, §10) as priors, because landmarks see positions, not form. `head-square` 0.5, `head-rectangular` 0.3, `cheek-bones-incr` 0.5, `cheek-volume-decr` 0.35, `chin-width-incr` 0.4 (σ 0.3). The soft alternatives (`head-round`, `cheek-volume-incr`, `head-fat-incr`) are held near zero (σ 0.2).
- **The skull top.** It may not move (σ 1 mm), so the stature fit is untouched.

Fits tried, in order (each a fresh 4-iteration fit, then pose.py --solve):

| Fit | Change | Result |
|---|---|---|
| 1 | no form priors | head-round 0.47, cheek-volume-incr 0.43: a broad soft face, the opposite of the drawing. Rejected |
| 2 | form priors; nuisance rotation σ 6° | the nose went up and longer to its bounds. Rotation σ raised to 12°: no change, so it is data, not a stand-in for pitch |
| A | + the pose's hand points at weight 10 | re-solved pose: menton 6.9 px off (round 0: 1.6), cost 40.90 |
| **B (kept)** | A without MediaPipe's chin-bottom points | menton 6.4 px, cost 40.55, ear 8.5 (was 9.8) |
| C | B with the menton at weight 60 | menton 4.8 px, but chin-height-decr and chin-prominent-incr at their bounds, skull top 10.2 px, ear 10.7, cost 41.36. Rejected |

The chin-bottom points (152, 148, 377, 176, 400, 149, 378) are left out because MediaPipe and the hand reading disagree by 8 px about the chin:
- On the reference MediaPipe puts the chin outline on the under-chin shadow (y 135.8); the hand reading puts the menton at y 131.
- On the model MediaPipe sits 3 px above the menton vertex.

The weights fit B chose (≥ 0.25):

| Weight | Targets |
|---|---|
| at the bound (1.0) | nose-scale-vert-incr, nose-trans-up, cheek-trans-down (0.99) |
| 0.68 to 0.87 | chin-prominent-incr 0.87, nose-scale-horiz-incr 0.71, nose-scale-depth-incr 0.68 |
| 0.45 to 0.50 | head-scale-vert-incr 0.50, chin-width-incr 0.48, mouth-scale-vert-decr 0.48, head-scale-horiz-incr 0.48, cheek-bones-incr 0.46, eyebrows-angle-up 0.45, head-square 0.45 |
| 0.25 to 0.34 | eye-trans-down 0.34, eye-height2-incr 0.33, forehead-scale-vert-decr 0.28, eye-trans-in 0.28, chin-height-decr 0.28, eyebrows-trans-up 0.25 |

All 60 nonzero targets are in head_fit.json.

The landmark residual, MediaPipe on the posed model's hero render against MediaPipe on the reference (full-frame px, no nuisance; `cache/parts/head_fit/{before,after}/check.json`, `renders/head/head_landmarks_{before,after}.png`):

| | MPFB default face (round 0 pose) | Round 1 face (re-solved pose) |
|---|---|---|
| RMS, about 400 landmarks | 3.12 | 1.88 |
| Median | 2.24 | 1.23 |
| Jaw oval RMS | 7.51 | 4.63 |
| Chin / nose tip / subnasale | 6.67 / 2.97 / 1.99 | 1.93 / 2.52 / 1.13 |
| Mouth corners R / L | 2.36 / 3.37 | 0.70 / 1.76 |
| Gonion R / L | 6.99 / 8.23 | 3.41 / 4.84 |
| Cheek R / L | 8.31 / 7.58 | 5.09 / 8.11 |

The fit's nuisance terms stayed large: −7.5° pitch (chin up), +6.1° yaw to his left, and (−5.8, +6.7) px. The re-solved pose does not reproduce them: head yaw 8.6° against round 0's 11.4° and the drawing's ~20°; see §5.

### Hair (Head.Hair)

The cap is built as follows.
- **Region.** MPFB's `scalp` group, plus the forehead above the hairline z 1783 (the reference's trichion, about 50 mm above the glabella), less the ears.
- **Refine.** Refined twice on the skin (5765 vertices). The staircase boundary is relaxed along itself and snapped back to the skin.
- **Thickness.** Pushed out by a thickness field:
  - 24 mm at the front fringe, 14 at the crown;
  - 2.5 at the temples and 7 at the occiput below the parietal ridge;
  - ramping in over 9 mm from the hairline.
- **Sweep.** Tilted up, forward and toward his right on the top.
- **Spikes.** 46 Gaussian clumps (σ 4–7.5 mm, 3–9 mm high).
- **Finish.** Taubin-smoothed, pushed out of the skin, Subdivision 1.
- **Material.** Flat `#3a2a1e` (analysis §8 base).

The top stands at z 1862, 27 mm over the skull top. The first cap used the hair lengths as thickness (42 / 30 mm) and stood 49 mm over: a pompadour helmet. Hair 35 to 45 mm long lies at an angle; the drawn mass is about 10 to 15 mm over the scalp and the spike tips about 13 mm higher.

### Stubble (Head.Stubble)

The density field follows analysis §9:
- **Dense:** the chin and soul patch, the moustache, and under the jaw down to 24 mm below the menton, in front of the ears.
- **Medium (0.6):** below the line from the tragus to the mouth corner.
- **Zero:** on the lips, above the line, and on the neck.

It is Laplacian-smoothed. The shell is the skin where the density is above 0.08, its boundary loop relaxed, and the shell offset 0.8 mm. There are two materials:
- In Workbench their viewport colours are the skin darkened 55 % / 28 % toward `#3b2a22`.
- In Cycles the stubble colour is mixed over a transparent BSDF by the `stubble_density` attribute × 0.6.

Fixed during the round:
- A first version relaxed the interior too; the shell's chords then dipped under the skin, which showed through in spots.
- A first "under the jaw" zone ran down the neck to the clavicles.

### Skin tone

base.py tones MPFB's texture by a measured multiply: the albedo divided by the texture's mean over the face. The face texture mean was `#e6beae`; the linear tone is (0.61, 0.46, 0.38) for `#b98670`.

The analysis's albedo `#b98670`, rendered through the hero camera under the evaluation lights (scene.py at 0.3), came out brighter and more orange than the reference. Render/reference linear ratios, averaged over the lit cheek, forehead and nose: R 0.83, G 0.84, B 1.01. The albedo became `#ab7d71`.

### Clearance

- **Hair, rest:** 0.4 mm minimum, 0 inside.
- **Stubble, rest:** 0.47 mm minimum, 0 inside.
- **Posed:** hair 0.26, stubble 0.47, 0 inside.

### Renders looked at (renders/head/)

**`head_landmarks_before.png`, `head_landmarks_after.png`.** The reference with MediaPipe's points on it (red: reference, green: model) beside the model render.
- Before: the model's jaw and chin points sit inside the reference's (6 to 8 px).
- After: they mostly coincide. The far (viewer's right) cheek is still off.

**`head_rest_{front,side,threequarter}_clay.png` and `head_before_rest_*.png`.**
- The face is now broader and squarer, with a stronger chin and a bigger nose. The cap has a reasonable short-crop silhouette: volume on top, a lifted front, tight sides and a fade into the skin. The stubble zone looks right.
- Honestly, it reads as a broad, heavy face, not the drawing's lean long one.
- The round 0 "before" side and three-quarter views were framed off-centre by common.render_rest_views; the head views here use their own cameras.

**`head_rest_*_cycles.png`.** The same views in Cycles (64 spp, the evaluation lights).
- The hair reads medium brown; the eyes dark.
- The skin is too orange and saturated.
- The stubble shows only as a faint darkening with a visible edge.

**`head_hero_head_face_pair.png` (Workbench) and `head_hero_head_face_cycles_pair.png`.** Through the hero camera beside `ref/crop_head_face.png`.
- The placement and size match.
- The model's head is turned less to his left and is less chin-up than the drawing.
- The face is wider at the cheeks and softer at the jaw.
- The brows are heavy dark bars in Workbench.

**`head_hero_soldier_full_pair.png`, `head_hero_soldier_full_cycles_pair.png`.** The whole posed body with the head part through the hero camera (`ref.soldier_full`).
- It matches round 0's pose with the new head.
- The skin is orange in Cycles.

## 4. Departures and why

- **Symmetric face.** Fitted symmetric (spec 06 §2.5 row 14); the small real asymmetries come later.
- **The eye fissures and alar base** were not forced to the image's oversized 38 / 45 mm (spec 06 §2.5 rows 1–2). The fit only moves MPFB's eye and nose targets, inside their ranges.
- **The ears are not fitted.** MediaPipe has no ear points. The ear enters only through the pose's hand-read ear centre (8.5 px residual).
- **The eyebrows are MPFB's `eyebrow001`** (straight, medium-thick; analysis §5, "dense straight brows") instead of round 0's thin arched `eyebrow006`. They are cards, not strands.

## 5. Still wrong, ranked for round 2

1. **The head's pose is not the drawing's.** The re-solved head yaw is 8.6° (drawing ~20°, round 0 11.4°) and less chin-up. The face fit's nuisance terms say the face wants +6° more yaw, 7.5° more chin-up and a 6 to 7 px shift.
   - The pose solve's head is driven by a few hand-read points (pupils, nose tip, menton, ear, skull top). Those disagree with MediaPipe's 400 points by 2 to 5 px in the lower face.
   - Fix: give pose_solve.py the head.py correspondences as a head term (a pose-part change), or let the head part own the head-bone rotation.
2. **The face reads broad and soft, not lean, long and angular.**
   - MPFB's targets are exhausted where the fit wanted more: nose-scale-vert-incr, nose-trans-up and cheek-trans-down sit at 1.0.
   - The fit chose head-scale-horiz-incr 0.48 and chin-prominent-incr 0.87.
   - The landmarks do not see the cheek hollow or the jaw's angularity, so these come only from priors.
   - Next: a measured corrective from take 1's 3DDFA mesh (`ref/ai/face_ref_mesh.obj`) or a generated head, with a silhouette/shading term, not landmarks alone.
3. **The menton is 6.4 px off the hand-read point** in the re-solved pose (round 0: 1.6). This is the 8 px detector disagreement above. Somebody should decide which reading of the chin is right; the reference's chin underside is in shadow against the gaiter.
4. **The skin in Cycles is orange and saturated.** The SSS of MPFB's ENHANCED_SSS material under the 4500 K key; the albedo calibration only fixed the mean. Lower the SSS weight or radius, then re-calibrate against the same three regions.
5. **The hair is a smooth helmet with bumps.**
   - No individual spikes stand out in the silhouette (the analysis counts 8 to 10).
   - The fade at the sides is a uniform thin shell, not a skin-blended gradient.
   - The fringe sweep is weak.
   - Round 2: hair curves (PLAN), or at least alpha-carded clumps along the silhouette.
6. **The stubble is a tint.** It has a hard edge in Workbench and is barely visible in Cycles. There is no greyer chin and no texture. Round 2: a density-mapped short-strand system or a baked albedo/normal layer.
7. **The eyes read dark in Cycles** (the sclera barely visible) and the lids are not hooded. The brows are heavy bars in Workbench, and the brow targets went up (eyebrows-trans-up 0.25) against the analysis's "very low brows".
8. **Expression is not modelled.** Brow-lower, lid-tightener and pressed lips (analysis §7, spec 06 §7.2) are absent; the model is neutral.

## 6. Round 2 (2026-11-15): the shape from four views, transferred onto MPFB's head

### 6.1 Method

The face targets stay (head_fit.json). On top of them, one corrective shape key, `head-shape`: a per-vertex displacement
of the head region (4361 skin vertices, head-bone weight > 0.3) solved the way take 1's foot was transferred onto its
scan (`scripts/stages/foot/transfer.py`): a smooth displacement field on MPFB's own topology, data terms where something is
measured, a bending energy |L U|² everywhere else. Topology, UVs, groups and weights are untouched. The field is
symmetric (mirror pairs) and zero on the neck ring; the skull top and the cranium under the hair are held (stature, hair
cap). The helper geometry follows (eyes, teeth, tongue and joint cubes rigidly with the skin around them, the other
helpers per vertex), so the eye bones and the MHCLO eyes, brows and lashes that base.py fits from them follow the face.

Every measurement is "the same detector on both": the reference and a render of the model through the same camera.

| View | Source | Terms (sigma) |
|---|---|---|
| hero | `ref/crop_head_face.png`, matched hero camera, posed | MediaPipe landmarks (1.5 px, jaw oval x1.5) with round 1's exclusions and a nuisance head rotation and shift; the pose solve's hand points (nose tip, menton, right ear); **the far-cheek silhouette** against the dark background, rows 68-124 (1.0 px) |
| front | `gen/R001/front.png` (ChatGPT, R001), own camera solved | MediaPipe landmarks (3.5 mm); **relief** from Depth Anything V2 Small (3 mm) |
| three-quarter | `gen/R001/threequarter_left.png` | MediaPipe landmarks (3.5 mm); **far-cheek silhouette** against the grey background, brow to chin (2.5 mm); relief (3 mm) |
| profile | `gen/R001/profile_left.png` | **the front silhouette**, brow to throat (2.5 mm), and four outline features: glabella, nasion, nose tip, pogonion. No MediaPipe: it squashes a true profile (it read it as 51.7°) |

The R001 views' cameras (head rotation, focal length, principal point at a fixed 1.1 m, a long lens) are solved with
the shape. The front and the profile hold their turn (sigma 3°: a profile's midline alone cannot tell its turn from the
face's depth); the three-quarter finds its own (32°; it was asked for 45). The relief term: Depth Anything on the R001
photo and on the model's render through the fitted camera, each map turned into millimetres by an affine fit to the
model's true depth over the visible face (forehead rows and eyes left out); the difference less its best plane is the
depth each vertex should gain (clipped at 5 mm a round). Gauss-Newton: cameras and nuisance with U fixed, then U with the
cameras fixed (one sparse solve), four times per round; three rounds, each re-rendering and re-detecting (110 s).

The silhouettes were added after a first run: MediaPipe's regression is prior-heavy and reads two different faces
alike, so the landmark residuals alone were already small (front 1.6 mm, three-quarter 2.0 mm) while the face still
read heavy. Outlines are model-free.

### 6.2 Sources checked

- **3DDFA (take 1)**: only its 40 shape and 10 expression parameters and 68 landmarks are in `ref/ai/`
  (`face_3ddfa_lm68.json`); the BFM basis and the dense mesh are not in the repository, and take 1 called the fit
  generic. `ref/ai/face_ref_mesh.obj` is MediaPipe's 468-point mesh with MediaPipe's generic depth. Neither was used.
- **FLAME-class fits (DECA, EMOCA, SMIRK)**: the FLAME model needs an account, so they are ruled out by the brief.
- **gen/R001** arrived during the round (front, three-quarter, profile; inferred by ChatGPT, angles approximate) and
  carries the depth: the profile outline and the three-quarter's far cheek.
- **Depth Anything V2 Small** (Apache-2.0): installed through setup's existing `--with-depth` route (torch 2.14.1 CPU and
  transformers 5.18.0 into `assets/ai/venv`; weights in `assets/ai/depth_anything_v2_small/`, the two config hashes now
  added to `scripts/setup/downloads.json`). Its fit to the model's own true depth leaves 3.3-5.5 mm rms, so its relief
  is weak evidence: weighted at 3 mm; §7 item 1 says where it disagrees with the outlines.

### 6.3 Numbers (`cache/head_r2/check_{before,after}.json`)

Before = round 1's base (`cache/head_r2/base_snapshot.blend`); after = the same with head-shape.target. Both through
round 1's committed hero pose (`cache/head_r2/hero_pose_r1.json`), the R001 cameras re-solved for each mesh alone.

| | Before (round 1) | After (round 2) |
|---|---|---|
| Hero, MediaPipe RMS, no nuisance (round 1's measure), ~400 points | 1.88 px | **1.64 px** |
| Hero, median / jaw oval | 1.23 / 4.63 px | 1.02 / 4.67 px |
| Hero, with the nuisance rotation and shift | 0.77 px | 0.60 px |
| Hero far-cheek silhouette, 94 rows | 1.35 px | **0.80 px** |
| Front landmarks (R001) | 1.59 mm | **1.04 mm** |
| Three-quarter landmarks | 1.52 mm | 1.17 mm |
| Three-quarter far-cheek silhouette | 1.68 mm | **1.02 mm** |
| Profile outline, brow to throat, 222 rows | 4.41 mm | **1.90 mm** |
| Profile features glabella / nasion / nose tip / pogonion | 4.9 / 4.4 / 2.4 / 3.5 mm | 0.9 / 5.3 / 3.8 / 2.5 mm |
| Relief (Depth Anything difference), front / three-quarter, during the fit | 4.5 / 9.4 mm | 3.6 / 4.5 mm |

The hero's key points (px): nose tip 2.52 → 2.89, eye outer R 2.05 → 1.23, mouth R 0.70 → 0.26, gonion L 4.84 → 5.31.
The shape (rest): vertex to menton 245.8 → 250.9 mm (longer: the menton 5 mm lower), the breadth 38 mm above the
menton 137.4 → 133.7 and 20 mm above it 124.3 → 122.9 (a narrower lower jaw), the nose tip 3.7 mm back, the menton 4.5 mm
back. Largest displacement 10.4 mm; 95 % of the face moved under 3 mm a round.

### 6.4 Materials

`head_skin.py` (for base.py; applied by head.py --dev until wired):
- **Skin**: SSS weight 0.2 → 0.06, radius scale 0.1 → 0.05, radii (1, 0.2, 0.1) → (1, 0.35, 0.2), albedo #ab7d71 → #a5746f
  (pinker). Hero crop against the reference (hue / saturation): cheek 20.3 / 0.33 → 18.3 / 0.34 (ref 16.2 / 0.35),
  forehead 20.9 / 0.39 → 19.6 / 0.25 (ref 17.3 / 0.34), nose 17.6 / 0.38 → 15.9 / 0.41 (ref 15.5 / 0.36), chin
  19.4 / 0.60 → 20.6 / 0.41 (ref 16.1 / 0.36). The point under the zygoma is still 0.56 against 0.38: the model has no
  hollow there, so the point sits on a lit bulge's terminator.
- **Stubble**: no shell. A UV mask (`Body.StubbleMask`, 2048², packed; R density, G grey) from head.py's density map,
  fading over ~15 mm, drives a mix in the skin group's colour chain: dots (0.9 mm noise) darken it towards #2c1f18,
  greyed up to 45 % on the chin, roughness +0.25. Per-vertex attributes were tried first: Cycles read them as 0 inside
  MPFB's skin group. A generated image went black after a render-engine switch, so the mask goes through a PNG and is
  packed.
- **Eyes**: the black eyes were EnhancedEye's cornea shell, a refracting glass (transmission 1, IOR 1.33) over the whole
  eye: no direct light reaches the sclera and iris without caustics. Now a dark glossy veil (transmission 0, alpha 0.25,
  colour black, roughness 0.02); sclera #e6e0da, iris #6a5646 / #3f322a. Short lashes (`eyelashes01` instead of
  base.py's long, curled `eyelashes02`).
- **Hair** (head.py): the cap a little lower (top 24 → 17 mm at the front, 14 → 10 at the crown) and darker (#3a2a1e
  rendered at value 0.46 against the drawn 0.24; now #271b14, no sheen), with 60 tapered, bent clumps on the top leaning
  with the sweep (7-13 mm, roots 4.2-6.5 mm), none on the sides. The stubble shell is gone from Part.Head.

### 6.5 Renders looked at (renders/head/, prefix `head_r2_`)

- `rest_{front,side,side_L,threequarter}_{clay,cycles}.png` beside round 1's: the stubble's hard edge is gone; the chin
  and moustache carry a soft dark stubble in Cycles; the eyes show sclera and a dark iris; the skin is a little less
  orange. The face is longer and a little narrower at the jaw. **Honestly, it still reads broad and soft**: jowly below
  the cheekbones, a fleshy rounded nose tip, thick lips, a soft under-jaw running into the neck with no jaw line.
- `r001_{front,threequarter,profile}_sheet.png` (R001 | model | 50 %): the outlines now lie on R001's (the profile, the
  three-quarter's far cheek, the front's face width), which is what the numbers say. The difference is inside the
  outline: the photo has hollow cheeks, a defined mandible edge and a crease under the jaw where the model is full.
- `hero_head_face_pair.png`, `hero_head_face_cycles_pair.png` (reference | model | 50 %): size and placement match;
  the head is still turned less to his left and less chin-up than the drawing (the pose, §7 item 2); the far cheek now
  meets the drawn outline.
- `zoom_{z_head_x8,g_eye_right_x20,g_nose_mouth_x14,g_jaw_x10}_sheet.png`: the eye has a sclera and a catchlight; the
  stubble reads on the chin and upper lip; the jaw zoom shows the model's soft, round jaw against the drawn angle.
- The hair clumps break the cap's silhouette but read as thorns, not piecey hair.
- `head_r2_landmarks_after_{hero,front,threequarter}.png`: MediaPipe's points, reference red, model green.

### 6.6 Wiring (done in round 4, §9)

In `scripts/stages/base.py`:
1. After the face-target loop (before `fit_height`): `import head_shape; head_shape.apply(mpfb, body)` (with the parts
   directory on `sys.path`). It loads `scripts/parts/head-shape.target` as the shape key `head-shape` at weight 1, before
   the rig, so the joint cubes, eye bones and MHCLO assets follow.
2. In `ASSETS`, the eyelashes `eyelashes01/eyelashes01.mhclo` (`head_skin.LASHES_R2`).
3. After `marks = landmarks(body, rig)`: `skin["head_r2"] = head_skin.apply(body, marks, get("Body.Eyes"))`. It retunes
   Body.Skin (the tone from #ab7d71 to #a5746f), packs the stubble mask and fixes the eyes.
4. Rebuild base, re-solve the pose (the menton moved 5 mm down and back; the hand-read chin target in pose_solve.py may
   want a look), rebuild the head part (`head.py` without `--dev`; it skips head_skin when the skin group already has
   `Stubble.Mix`), and every part built on base.blend.

head-shape.target is a displacement of the round-1 face: if head_fit.json is refitted, re-run `head_shape.py --fit`.

## 7. Still wrong, ranked for round 3

1. **The face still reads broad and soft** although its outlines now match the four views to 1-2 mm: the form inside
   the outline is still MPFB's. Jowls under the cheekbones where the drawing and R001 have hollows; no mandible edge or
   crease between jaw and neck (the submental plane runs straight into the throat); a fleshy, rounded nose tip; thick
   lips. The bending energy (0.2 mm) smooths what the data cannot see, and the relief term is too noisy to carve hollows.
   Its remaining requests (the nose 3-5 mm deeper, the bearded chin forward) contradict the profile outline, so they
   look like Depth Anything's bias on the photo. Next: a shading term (render against reference under matched light:
   the hollows and the jaw edge show as shading), a better normal estimator than relative depth, or explicit local
   targets (spec 06 §3.3: sub-zygomatic hollow −3 mm over r 16, jaw corner r 10, vermilion 6 / 9.5 mm) as a sculpt on
   top of the transfer.
2. **The head's pose** (round 1 §5 item 1): yaw and chin-up are still less than drawn; the hero nuisance wants about
   +6° of yaw and 7° chin-up. The pose agent's face term should settle it; then re-check the hero numbers.
3. **Hair**: the clumps read as thorns and the cap as a helmet. Strands (hair curves with clumping) come next.
4. **Skin**: hue 18-20° against the drawing's 16-17°, and the cool side stays warm (the evaluation lights, not the
   skin). No pores or lines beyond MPFB's texture.
5. **The profile nasion** is 5.3 mm off: MPFB's nasion sits higher and shallower than R001's, and the bending holds the brow.
6. **R001 is inferred**: its three-quarter came out at 32°, not the 45 asked, and its proportions are ChatGPT's reading
   of the same drawing. It is guidance, not truth (weighted below the hero).
7. **Expression** is still neutral (round 1 §5 item 8).

## 8. Note for round 3 (Claude, 2026-11-15)

Round 2's outlines match to 1-2 mm in four views, but the face still reads soft and jowly next
to the drawing and R001: the shape inside the outline is what is wrong, and neither landmarks nor
outlines nor the noisy depth estimate can carve it. The candidate that fits "free, local, open"
(PLAN.md decision 4) is **Hunyuan3D 2 (mini or multi-view `2mv`)**, open weights, which turns one
or several pictures into a 3D shape; the multi-view model takes front, left and back views, and
R001 supplies front and left profile (and ChatGPT can make a back view on request). Shape-only
generation in low-VRAM mode is reported to fit in about 5-6 GB, so it may run on the RTX 3050;
check the licence terms before relying on it. Its head mesh would then be transferred onto MPFB's
head exactly as round 2's shape key and take 1's foot scan were, keeping MPFB's topology, UVs and
weights, with the fit to the four views as the check. If it does not run here, the fallback is a
shading term or targeted local sculpting of the jaw line, cheek hollows, nose tip and lips.

## 9. Round 4 (2026-11-15): round 2 wired into base.py, the stature 1844

**Wired** as §6.6 says (`scripts/stages/base.py`): `head_shape.apply(mpfb, body)` after the face-target loop and before
`fit_height` (the key `head-shape` at 1.0, recorded in base.json's `face_targets`); `eyelashes01` in `ASSETS`;
`head_skin.apply(body, marks, Body.Eyes)` after `landmarks()` (base.json `skin.head_r2`: the skin retune to #a5746f, the
packed stubble mask, the eyes). head.py's own round-2 skin step now skips (the skin group carries `Stubble.Mix`), and
`head.py` (no `--dev`) builds the part on base.blend. The rest stature became 1844 mm in the same rebuild (PLAN.md
Decisions 3): height macro 0.58965, skull top 1844.06 mm over the rest floor (1845.6 to the heel pad's lowest vertex,
as round 3's 1835.0 / 1836.5).

**Face targets for the pose.** `head.py --check r4pre` on the new base through round 3's pose (MediaPipe RMS 4.14 px,
most of it the 9 mm taller body under an old pose), then `pose_solve.build_face_targets("r4pre")`: face_targets.json now
holds 397 landmarks on 833 vertices of the round-2 face (round 2's file was built on the round-1 face). The pose was
re-solved on it (scripts/stages/README.md, "Round 4").

The hair cap (`Head.Hair`) has one vertex 1.97 mm inside the skin at rest on the new head (posed numbers in
head.json); round 1's cap rules still hold elsewhere.

## 10. Head shape round 3 (2026-11-15): Hunyuan3D 2 as a form prior (not wired)

Developed beside round 4's wiring, on copies: `scripts/parts/head_shape_r3.py` writes `scripts/parts/head-shape-r3.target`
(+ `head_shape_r3.json`); `head-shape.target` (round 2, loaded by base.py) is untouched. The probe is `head_hy3d.md`;
its §8 has the FlashVDM result and what setup must download.

```
"$SGT_PYIMG" -I scripts/parts/head_shape_r3.py --prior            # ~3 min: align the seeds, the mask (cache/head_r3/prior.npz)
"$SGT_PYIMG" -I scripts/parts/head_shape_r3.py --fit --rounds 3   # ~160 s: head-shape-r3.target, head_shape_r3.json
"$SGT_PYIMG" -I scripts/parts/head_shape_r3.py --check r3 --check-fixed r3   # the numbers (cache/head_r3/)
"$SGT_PYIMG" -I scripts/parts/head_shape_r3.py --render r3 --sheets          # ~60 s: renders/head/r3/
```

### 10.1 Method

Round 2's transfer (§6) continued for three more rounds from round 2's target, every round-2 term unchanged (hero
landmarks with the nuisance, the hand points, the hero and three-quarter far-cheek silhouettes, the R001 landmarks,
the profile outline and features, the relief, bending, the held cranium, skull top and neck ring), plus a prior:

1. **Six seeds** of the 50-step multi-view model on R001's front + left profile: the probe's seeds 12345 and 7 (plain
   decoder) and seeds 1-4 with the FlashVDM decoder (`cache/hy3d/r3/`, 165 s each; same-latent difference 0.16 mm).
2. **Alignment, each seed on its own**, to round 2's MPFB head. MediaPipe on an orthographic front clay render of each
   (`cache/head_r3/prior/*_front.png`), 3D points by casting back onto each mesh. The brief's eye-to-chin scale did not
   hold: on the blank-eyed Hunyuan clay MediaPipe reads eye width / (168-152) as 0.86 and mouth / (168-152) as 0.53,
   against 0.73 / 0.43 on R001, on its Hunyuan input and on MPFB, so one distance gave 168-177 mm/unit and a face 6-8
   mm too wide at the eyes. Used instead: a frontal-plane (x, z) similarity of 26 inner landmarks to start (the face
   oval left out: its depth is a grazing ray), then a **scaled point-to-plane ICP** over the masked face (trimmed 12 ->
   4 mm). Final scales 172.5-175.1 mm/unit, rotations 0.9-5.7°. On the midline the aligned prior's pronasale,
   subnasale, labiomental fold, pogonion and menton sit within 0-4 mm of MPFB's heights.
3. **Mask** (`renders/head/r3/prior_mask.png`, 1050 of 4361 vertices over 0.5): the face from 24-36 mm below the menton
   (just above the prior's neck cut) to 30-40 mm above the eyes, forward of the ears. Zero on ellipsoids round each eye
   (26 x 17 mm, ramp to 1.6x: the lids and the sides of the bridge; Hunyuan's eyes sit wider apart, and a first,
   smaller exclusion opened the inner canthus and widened the bridge), on the lips and moustache (subnasale to below
   the lower lip, the mouth's width + 5 mm), the ears and the neck ring.
4. **Per round**: each masked vertex's signed distance along its normal to each seed (nearest of 2.5 M surface
   samples; rejected beyond 10 mm, 4 mm sideways or a normal mismatch), averaged over the seeds (their spread after
   alignment: 1.0 mm rms), lightly low-passed, then **band-passed** (less its own diffusion over ~20 mm), so the prior
   asks for local forms and never for a broad change of the cheek's width.
5. **Two terms**: inside the mask round 2's bending |L U|² becomes |L U − L D|² (D = mask × d × normal, sigma 0.2 mm),
   so the field takes the prior's local curvature; and n·U = d (sigma 2.5 mm plus the seed spread, clipped 5 mm).
6. **The R001 cameras are held after round 0.** Re-solved each round, MediaPipe's reading of the views moved with the
   new shading, the cameras turned, and the three-quarter far cheek drifted 1.0 -> 2.6 mm over three rounds while the
   same mesh through the previous round's cameras measured 1.25. Holding them stops the drift.

Variants (three rounds each): **A** curvature at ~12 mm detail, offset term σ 3 mm not band-passed, cameras re-solved:
3q silhouette 2.6 mm. **B** σ 2, four rounds: the most change (prior residual 1.85 -> 0.99 mm) but the inner lower lid
opened, the bridge between the eyes widened and a notch formed at the glabella. **C** B's settings with the larger
eye exclusion, three rounds: clean, but the hero far cheek moved about 1 mm inside the drawn line (silhouette 0.80 ->
1.31 px) and the three-quarter's 1.03 -> 1.73 mm (kept in `cache/head_r3/variantC/`, renders in
`renders/head/r3/variantC/`). **D (delivered)**: C plus the band-pass on the offset term; the script's defaults.

### 10.2 Numbers (round 2 against round 3, D)

Both dev bases built by base.py as of dca7a15 (stature 1835, `cache/stages/head_dev_r{2,3}.blend`) through round 1's
pose snapshot, as round 2's own check; this harness reproduces §6.3's round-2 numbers. "Check" re-solves every view's
camera on MediaPipe for each mesh alone (round 2's measure); "fixed" holds round 2's cameras (only the hero nuisance
re-solved), which separates the shape change from MediaPipe's camera drift.

| | R2 check | **R3 check** | R2 fixed | **R3 fixed** |
|---|---|---|---|---|
| Hero MediaPipe RMS, no nuisance, px | 1.64 | 1.68 | 1.64 | 1.68 |
| Hero jaw oval, px | 4.67 | 4.51 | 4.18 | 3.39 |
| Hero with nuisance, px | 0.60 | 0.66 | 0.60 | 0.66 |
| **Hero far-cheek silhouette**, px (mean) | 0.80 (−0.13) | **1.21 (−0.30)** | 0.80 | 1.21 |
| Front landmarks (R001), mm | 1.04 | 1.37 | 1.12 | 1.55 |
| Three-quarter landmarks, mm | 1.18 | 1.53 | 1.18 | 1.57 |
| **Three-quarter far-cheek silhouette**, mm (mean) | 1.04 (0.69) | 2.07 (1.56) | 1.03 (0.68) | **1.30 (0.20)** |
| **Profile outline**, mm | 1.90 | 1.65 | 1.96 | 1.76 |
| Profile glabella / nasion / pronasale / pogonion, mm | 0.9 / 5.3 / 3.8 / 2.5 | 4.1 / 3.1 / 1.6 / 2.1 | 0.3 / 4.7 / 3.5 / 2.5 | 4.4 / 3.3 / 1.4 / 2.2 |
| Prior residual over the mask (band-passed), mm | 0.98 | 0.59 | | |

- Hero key points (px): nose tip 2.89 -> 2.89, mouth R 0.26 -> 1.51, gonion L 5.31 -> 5.52, the rest within 0.3.
- Shape (rest): breadth 38 mm above the menton 133.7 -> 138.1 mm (the prior's squarer, wider jaw angle), 20 mm above
  122.9 -> 122.3; nose tip 1.4 mm forward, menton 3.2 mm back; vertex to menton 250.9 -> 249.9. Change from round 2:
  max 9.4 mm, 95th percentile 4.4 mm.
- So: the profile improves (the prior's bigger, straighter nose agrees with R001's outline; the glabella feature gets
  worse, the nasion better), the hero jaw oval improves, and the far cheeks lose a little: the hero's by 0.4 px rms
  (~0.6 mm inside the drawn line on average), the three-quarter's by 0.3 mm with the cameras held (1 mm with them
  re-solved: MediaPipe's drift). The R001 landmark residuals rise 0.2-0.4 mm.

### 10.3 Renders looked at (`renders/head/r3/`; `r2_*` and `r3_*` from the same harness, `cmp_*` side by side)

- `cmp_rest_{front,side,side_L,threequarter}_{clay,cycles}.png`, `crop_r{2,3}_front_clay.png`: r3 has a straighter,
  narrower, more projecting nasal dorsum with defined alae, a cheek plane under the zygoma and a nasolabial fold, a
  little more brow ridge, a squarer lower jaw in the three-quarter. **It is a modest change, not the fix**: the jaw
  still rounds softly into the neck, there is no crease under the jaw, and the face still reads broad and fleshy in the
  front Cycles view.
- `cmp_hero_head_face_cycles.png` (reference | r2 | r3): the nose reads straighter and the cheek flatter; the jowls and
  the soft fullness under the jaw that make the face read heavy are still there. Placement unchanged.
- `cmp_r001_{front,threequarter,profile}.png` (R001 | r2 | r3): the profile nose is closer to R001's prominent straight
  nose; chin and under-jaw are still fuller than R001's sharp jaw line and receding neck.
- `r3_zoom_g_jaw_x10_sheet.png`: the jaw is still round against the drawn angle; a small dark fold at the near mouth
  corner is new in r3. `r3_zoom_g_eye_right_x20_sheet.png`: the red interior blob at the inner canthus is already in
  round 2 (`r2_zoom_g_eye_right_x20_sheet.png`), a little larger in r3.
- Diagnostics: `dbg_detect.png` (MediaPipe on the MPFB and Hunyuan clay), `dbg_prior_d_{front,side}.png` (the prior's
  offset from round 2, before band-passing), `landmarks_r2_*.png`.

### 10.4 Switching the pipeline to it

1. `cp scripts/parts/head-shape-r3.target scripts/parts/head-shape.target` (base.py's `head_shape.apply` loads that
   path; like round 2's, the file displaces the round-1 face before the height fit, so it carries to the 1844 base).
2. As §9: rebuild base, `head.py --check` on it and `pose_solve.build_face_targets(...)` (face_targets.json is built on
   round 2's face, and the face moved up to 9 mm), re-solve the pose, rebuild the head and the parts built on
   base.blend, then `assemble.py`.
3. To go back: `git checkout scripts/parts/head-shape.target`.

My recommendation is to wait: the gain (nose, cheek planes) is small against a 0.4 px loss on the hero's far cheek,
and item 1 below is where the heavy read comes from.

### 10.5 Still wrong, ranked for round 4

1. **The jaw and under-jaw are still soft; the face still reads heavy.** The prior's under-jaw surface sits 10-12 mm
   higher than MPFB's at the throat (sections through the aligned prior), but the head region ends at the neck ring
   (z 1531-1570, pinned) and Hunyuan's mesh stops at its neck cut 25-30 mm under the menton, so the crease has 20-30 mm
   to form in and the mask fades out exactly there. Next: let the field run into the neck (a region past the head-bone
   weights, the ring pinned lower), and extend the R001 profile outline below the throat row it stops at now.
2. **The prior's broad shape disagrees with R001's three-quarter.** Hunyuan's cheek fronts sit 3-6 mm behind MPFB's
   and its jaw angle 4-6 mm wider; R001's three-quarter far cheek says the cheek is fuller. Only the band-passed prior
   is used. Which is right is a question about R001 (ChatGPT's inference) as much as the model; a back view or a
   second three-quarter for Hunyuan (R004) would help.
3. **MediaPipe moves with shading.** Once hollows appear its landmarks on the same face shift 0.2-0.4 mm and the R001
   cameras turn with them. The cameras are held now; the landmark terms still chase the shading. A shading-insensitive
   measure (outlines, or landmarks on flat normal renders) would be steadier.
4. **The hero's far cheek is ~0.6 mm inside the drawn line on average** (silhouette 0.80 -> 1.21 px).
5. **The inner canthus shows a red interior blob** (round 2 already; larger in r3); r3 adds a small fold at the near
   mouth corner. Eye and mouth details, which stay MPFB's.
6. Round 2's §7 items 2-7 stand: the head pose, hair, skin, the nasion (now 3.1-3.3 mm, was 4.7-5.3), R001 as
   inferred, expression.

## 11. Head shape round 4 (2026-11-15): the jaw and the neck (not wired)

Developed on copies like round 3: `scripts/parts/head_shape_r4.py` writes `scripts/parts/head-shape-r4.target` (+
`head_shape_r4.json`), starting from `head-shape-r3.target`; `head-shape.target` (round 2, loaded by base.py) is
untouched. The hand-read jaw marks are `scripts/parts/head_jaw_marks.json`. Same harness as rounds 2-3 (base.py at
dca7a15, stature 1835, round 1's hero pose snapshot), dev base `cache/stages/head_dev_r4.blend`, work in `cache/head_r4/`.

```
"$SGT_PYIMG" -I scripts/parts/head_shape_r4.py --fit --rounds 4          # ~15 min: head-shape-r4.target (canthi patched)
"$SGT_PYIMG" -I scripts/parts/head_shape_r4.py --check r2,r3,r4 --check-fixed r2,r3,r4   # the numbers below
"$SGT_PYIMG" -I scripts/parts/head_shape_r4.py --render r4 --sheets      # ~60 s: renders/head/r4/ (r2 | r3 | r4 sheets)
"$SGT_PYIMG" -I scripts/parts/head_shape_r4.py --patch-canthus           # the outer-canthus patch alone (the fit does it)
```

### 11.1 Method

Round 3's transfer continued for four rounds with every round-3 term (hero landmarks and nuisance, hand points, hero
and three-quarter far-cheek outlines, R001 landmarks, profile outline and features, the Hunyuan prior with its mask
remapped onto the new region, bending, cranium, skull top), except the relief, plus:

1. **The region runs into the neck.** head.py's region (head and neck weights > 0.3) plus the skin above z 1500 (rest,
   about the sternal notch) inside |x| < 120. The pinned ring moves from z 1531-1573 (45 mm under the menton at the
   front) to z ~1500. The new skin behind y -10 (the nape) is held (1 mm); the helpers follow round 3's region only,
   so the neck joint cubes and bones do not move; weights are per vertex and a shape key does not touch them.
2. **Outlines that see the jaw** (R001 through the cameras solved on round 3's face in round 0, then held): the
   profile outline continued down the throat to below the laryngeal prominence (rows 962-1086, every 6 px); the
   profile's under-chin line as columns (296-428: per column, the bottom of the projected mesh's covered interval
   containing a point inside the chin, against the first background pixel below it); the front's two side outlines
   from below the ear lobes to the gonion (rows 740-836; scored as half-width, the common shift removed). Below the
   gonion R001's neck stands about 14 mm a side outside the jaw; following it would put the neck girth near 480 mm
   (a tape girth), so it is not used.
3. **The jaw as landmarks** (`head_jaw_marks.json`, read by hand on 10-20 px grids and drawn back on the images to
   check). MediaPipe marks no gonion or under-jaw plane, so: the gonion and the mandible's lower border in the front
   (both sides, read separately) and in the profile, triangulated by matching the two polylines by arc fraction and
   taking the closest point of each front ray and profile ray (the front's R side mirrored onto his left, then
   averaged). The rays miss each other by 0.5-3 mm near the chin and 12-20 mm at the gonion: the front puts the jaw
   angle lower than the profile does. So each point's sigma is sqrt(1.2² + (gap/3)²): 1.3 mm at the chin, 7 mm at the
   gonion. Gonion triangulated at (±73, -36, 1636): 51 mm over the menton, 97 mm behind it. Plus **the under-jaw
   plane**: points between the profile's midline under-chin line (z ~1583.5 from the chin back to the corner) and
   the border at the same y, at 35 % and 70 % of the way, stopping 12 mm in front of the hand-read chin-neck corner.
   Point-to-plane terms on the nearest vertex with a compatible normal, no more than 6-12 mm below the target.
4. **Soft tissue:** a sculpt prior on the total offset since round 3: the cheek under the zygoma (20 mm outside the
   mouth corner, half way between mouth and subnasale, r 11 mm, -3 mm) and the jowl (10 mm outside and 20 mm below
   the mouth corner, r 10 mm, -2.5 mm) sit in; the masseter is left. It reached -1.0 of the -1.5 mm mean wanted (the
   hero and three-quarter outlines hold the cheek).
5. **Freedom where the jaw needs it:** the bending sigma (and round 3's curvature sigma) x2 in the jaw zone (below the
   mouth corners, in front of the ears, down to 25-45 mm under the menton, not within 6-18 mm of the midline) and
   round 3's prior offset sigma x2 there (the prior has no data under the chin).
6. **Defect terms:** round 3's and 4's change smoothed at the mouth corners (L of the change since round 2, 0.05 mm);
   the total change since round 1 smoothed within 8 mm of any triangle flipped against round 1's face (recomputed each
   round); and after the last round **the outer canthi patched**: round 2-4's total displacement made a rigid
   translation within 6 mm of MediaPipe 33 / 263, blended out by 22 mm.

What was tried and dropped (each a full fit, kept in `cache/head_r4/v1`-`v7`, renders `renders/head/r4/v1`-`v5`):
- **v1** (bending everywhere, three rounds): the marks moved 7.6 -> 6.2 mm; the jaw barely changed.
- **v2**: the jaw formed, but:
  - a hard groove ran round the nose from the canthus to the mouth corner. **The relief term** (Depth Anything) pushed
    the nasal dorsum back 2.3 mm a solve (found by switching the term groups off one at a time); round 2 had already
    noted its nose requests as the estimator's bias. The relief is off in round 4, and the profile features then fell
    under 2 mm.
  - a hard normal cut in the first sculpt also creased the side of the nose.
- **v3:** the region's side boundary (|x| < 75) ran up the neck to z 1568 and the field kinked along it, so |x| < 120.
- **v4-v6:** midline folds at the glabella, under the chin and at the chin-neck corner (a dihedral of 31° -> 157-174°).
  The profile outlines pull only midline vertices; with relaxed bending the midline sank alone, and the throat rows at
  3 px gave each long neck edge many samples. So: the midline keeps round 2's stiffness, 6 px samples, the under-jaw
  points stop short of the corner, and the corner itself is left to the bending.
- **Lid rings** (16 mm round each eyeball moving rigidly): did not touch the defect and moved the lids up to 8 mm; off.

### 11.2 The red blob was the outer canthus, not the inner one

Ray-casting the hero camera through the zoom's pixels on each dev base:
- Back-facing skin hits (the socket lining seen through the lower lid): round 1's face 0, round 2 29, round 3 59,
  round 4 before the patch 68. Mapped to vertices they sit at x ±46, beside MediaPipe 33/263: the **outer** corner of
  the lower lid. The head is turned, so the right eye's outer corner is on the viewer's left of the zoom, and §10.3
  mislabelled it.
- Round 2's field folded that corner over: triangles there flip against round 1's face.
- The patch restores round 1's corner, translated: 0 hits. Max change 8.9 mm on lining vertices.

### 11.3 Numbers (`cache/head_r4/check_{r2,r3,r4}.json`, `checkfixed_*.json`)

All three dev bases through the round-4 harness (the extended region), so r2 and r3 differ slightly from §6.3 / §10.2
where the region matters. "Check" re-solves every R001 camera on MediaPipe per mesh; "fixed" holds round 2's cameras.

| | R2 check | R3 check | **R4 check** | R2 fixed | R3 fixed | **R4 fixed** |
|---|---|---|---|---|---|---|
| Hero MediaPipe RMS, no nuisance, px | 1.64 | 1.68 | 1.71 | | | |
| Hero jaw oval (detector), px | 4.67 | 4.51 | **4.43** | | | |
| Hero with nuisance, px | 0.60 | 0.66 | 0.76 | 0.60 | 0.66 | 0.76 |
| Hero far-cheek silhouette rms (mean), px | 0.80 (-0.13) | 1.21 (-0.30) | 1.08 (+0.27) | same | | |
| Front landmarks, mm | 1.04 | 1.37 | 1.09 | 1.12 | 1.55 | 1.32 |
| Front half-width, ear lobe to gonion, mm | 2.28 | 1.06 | 1.34 | 2.28 | 0.93 | 1.69 |
| Three-quarter landmarks, mm | 1.18 | 1.51 | 1.62 | 1.18 | 1.57 | 2.05 |
| Three-quarter far-cheek silhouette rms (mean), mm | 1.09 (0.75) | 2.05 (1.55) | 1.60 (0.90) | 1.03 (0.68) | 1.30 (0.20) | 1.43 (0.24) |
| Profile outline, brow to throat, mm | 1.90 | 1.74 | **1.12** | 1.96 | 1.76 | 2.38 |
| Profile glabella / nasion / pronasale / pogonion, mm | 0.9 / 5.3 / 3.8 / 2.5 | 5.7 / 3.7 / 1.2 / 1.8 | 2.5 / 2.2 / 0.7 / 2.2 | 0.3 / 4.7 / 3.5 / 2.5 | 4.4 / 3.3 / 1.4 / 2.2 | 3.2 / 1.4 / 2.0 / 0.9 |
| Profile throat (rows 962-1086), mm | 2.09 | 2.39 | 2.11 | 2.09 | 2.32 | 1.98 |
| Profile under-chin line, mm | 0.74 | 0.53 | 0.73 | 0.74 | 0.58 | 1.43 |
| **Jaw border marks** rms (mean, + = model below/outside), mm | 8.38 (6.15) | 7.59 (4.90) | **3.59 (2.60)** | 8.38 (6.15) | 8.55 (6.24) | **4.35 (3.37)** |
| **Gonion** (- = model inside), mm | -4.8 | -6.5 | **-2.2** | -4.8 | -5.2 | -2.1 |
| **Under-jaw plane** rms (mean), mm | 4.55 (4.08) | 4.54 (3.91) | **1.16 (1.03)** | 4.55 (4.08) | 4.72 (3.95) | **0.95 (0.53)** |
| Neck girth at menton -35 / -50 / -65 (hull of the slice, not a tape), mm | 523 / 512 / 567 | 517 / 507 / 558 | 522 / 511 / 565 | | | |
| Breadth 38 / 20 mm above the menton, mm | 133.7 / 122.9 | 138.1 / 122.3 | 139.1 / 125.0 | | | |
| Bizygomatic-like / vertex-menton, mm | 170.0 / 250.9 | 170.1 / 249.9 | 173.0 / 250.7 | | | |
| Triangles flipped against round 1's face | 8 | 50 | 12 | | | |

- Hero key points (px, r2 -> r4): nose tip 2.89 -> 2.86, mouth R 0.26 -> 0.85, gonion L 5.31 -> 5.37, eye R outer
  1.23 -> 1.53; the rest within 0.2.
- So round 4 does what the brief asked where it is measured: the jaw border, gonion and under-jaw plane move 3-6 mm
  towards R001's, and the profile outline improves (with its cameras re-solved; held at round 2's it is worse, 2.38 mm,
  so part of that number is camera).
- It costs:
  - the hero landmarks 0.07 px rms (0.16 with the nuisance);
  - the hero far cheek, which now sits 0.27 px outside the drawn line (round 2: 0.13 inside);
  - the three-quarter landmarks and far cheek 0.4-0.5 mm (the cheek is 1 mm outside R001's far cheek on average);
  - 5 mm of breadth at the jaw angle (the gonion follows R001's wider jaw: 139 against spec 06's 138 bigonial) and
    3 mm at the cheekbones.
- The neck girth is unchanged (±1 mm).

### 11.4 Renders looked at (`renders/head/r4/`, sheets `cmp_*` are r2 | r3 | r4, the reference first where there is one)

- `cmp_rest_side_L_clay.png`, `cmp_r001_profile.png`:
  - the mandible's lower border now runs as a visible line from the chin up to an angle below the ear, with a crease
    under it and the neck set back. r2 and r3 slope from the chin straight into the neck.
  - Still softer than R001, whose throat recedes further and whose jaw angle is sharper.
- `cmp_rest_threequarter_{clay,cycles}.png`: the clearest gain; a jaw edge from chin to angle and a flatter cheek under
  the zygoma. The face reads leaner.
- `cmp_rest_front_{clay,cycles}.png`, `cmp_r001_front.png`:
  - leaner, with the jaw corners showing and less fullness under the cheekbones.
  - A faint vertical crease remains at the bottom of the throat (the chin-neck corner on the midline, one edge at
    103°).
  - The lower face is a little wider at the angle.
- `cmp_hero_head_face_cycles.png`, `cmp_hero_head_face.png` (reference | r2 | r3 | r4):
  - the jowl and the soft fullness under the chin are much reduced and the far jaw has an edge.
  - It is still a fuller, rounder face than the drawing's: the drawing's cheeks hollow more, its chin is narrower and
    more pointed in this view, and its jaw line is higher on the near side.
  - Placement unchanged.
- `cmp_zoom_g_eye_right_x20.png`: no red lining at the corner of the eye (round 3: a red blob).
- `cmp_zoom_g_jaw_x10.png`: round 3's fold at the near mouth corner is gone; the chin is squarer.
- `landmarks_r{2,3,4}_*.png`: MediaPipe's points, reference red, model green.

### 11.5 Recommendation

Switch to round 4. It is the first round that changes the read of the lower face: a jaw line, a jaw angle and an
under-jaw plane, in every view that shows them. It removes round 2's and 3's eye-corner defect and round 3's
mouth-corner fold, and keeps round 3's better nose and profile. The losses are a few tenths of a px in the hero and
about half a mm in the R001 three-quarter. The open question is the wider jaw angle: it follows R001 (ChatGPT's
reading) more than the drawing, which is narrower at the angle in the hero view.

### 11.6 Switching the pipeline to it

1. `cp scripts/parts/head-shape-r4.target scripts/parts/head-shape.target`. base.py's `head_shape.apply` loads that
   path. The file is the displacement of the round-1 face (it includes rounds 2 and 3), applied before `fit_height`,
   so it carries to the 1844 base.
2. The target now also moves neck skin down to z ~1500 (the throat and the front and sides of the neck; the nape is
   held). The rig's weights and joint cubes are unchanged. **Rebuild every part built on base.blend, the shirt's
   neck gaiter above all**, so it fits the new neck.
3. Then as §9:
   - rebuild base;
   - run `head.py --check` and `pose_solve.build_face_targets(...)` (the face moved up to 9 mm);
   - re-solve the pose;
   - rebuild the head part;
   - then `assemble.py`.
4. To go back: `git checkout scripts/parts/head-shape.target`.

### 11.7 Still wrong, ranked for round 5

1. **The face is still fuller than the drawing's in the hero view.** The cheeks under the zygoma hollow less (the
   sculpt reached -1 of -1.5 mm; the outlines hold it), the chin is broader in that view, and the near jaw line sits
   lower than drawn. The hero view has no jaw-line term: the camera looks up at the chin, so the drawn dark band under
   the jaw is the under-jaw plane itself. `head_jaw_marks.json` records its top and bottom edges in crop pixels; a
   hero jaw-line term needs the model's occluding contour there.
2. **The jaw angle's height disagrees between R001's front and profile by 12-20 mm** (the rays miss). The gonion is
   weighted down, but R001 is ChatGPT's inference; a second opinion (a generated three-quarter from his right, or a
   Hunyuan run with a back view) would settle where the angle is.
3. **A faint midline crease at the chin-neck corner** (one edge 31° -> 103°) and small notches at both mouth corners
   (MPFB's corner geometry under the field). Under the gaiter the crease is hidden in the hero.
4. **R001 camera dependence:** with round 2's cameras held the profile outline reads 2.38 mm (re-solved 1.12). The
   cameras were re-solved once on round 3's face; landmarks on flat normal renders would steady them (§10.5 item 3).
5. The relief (Depth Anything) is off; it fought the profile on the nose. A better normal estimator could come back
   as a shading term.
6. 12 triangles still flip against round 1's face (r2 8, r3 50): the inner canthus (as round 2), the alar crease and
   the mouth corner. None shows in the renders looked at.
7. Round 2's §7 items 2-7 stand: the head pose, hair, skin, R001 as inferred, expression.

## 12. Round 7 (2026-11-15): round 4 switched in

Done as §11.6 (scripts/stages/README.md, "Round 7", has the pose side):
- `head-shape-r4.target` copied over `head-shape.target`; base rebuilt (`base.py`, 20 s): stature 1844.07 mm (height
  macro 0.58965, unchanged), every body and limb bone unchanged to 0.01 mm; the face bones moved (tongue / special04
  10.6 mm, levator02 7.4, temporalis 6.0-6.5); the solved landmarks moved: nose tip 3.4 mm back, chin 1.8 mm back,
  pupils 0.4-0.6 mm, ears 0.4 mm. The pose signature changed, so the pose was re-solved.
- Every part built on base.blend rebuilt (trousers, shirt, boots, gloves, carrier, armour, belt, head). The gaiter fits
  the new neck: 9.0 mm off the skin at rest, 7.8 in the old hero pose, nothing inside (shirt log).
- `head.py --check r7pre` (the new base through round 4's pose): MediaPipe RMS **1.28 px** (median 1.13, max 3.65), jaw
  oval 2.34 px; key points nose tip 1.44, chin 0.66, gonions 1.65 / 1.76, cheeks 3.3 / 4.3 px.
- `pose_solve.build_face_targets("r7pre")`: face_targets.json now 402 landmarks on 843 vertices.

**The head's yaw** (critic m15: "the head faces the camera"; the drawing reads about 20 deg, a critic said 30). On this
face, with the body held at round 4's pose and only the neck and head free (`cache/r7/`, scratch), the face term alone
wants **18.2 deg** of yaw at 1.02 px RMS; round 4's 14.9 was held there by the hand-read pupils, nose tip, menton and
above all the skull-top pixel (a guess through the hair, 12-17 px off). The face term does not want the chin up: its
pitch stays at 0.5 to -1 deg against a prior of -6. So the solve now down-weights the hand points the face term
duplicates (`FACE_SUPERSEDES`). The re-solved pose: head yaw **17.5 deg** (round 4: 14.9), pitch -1.0, roll -2.5; the
face term's MediaPipe RMS **0.85 px** (round 4: 0.99); right ear 2.7 px, chin 8.3, skull top 17.3 (down-weighted).
In the hero render it still reads closer to frontal than the drawing (stages README, round 7); a face nearer the
drawing's (§11.7 item 1) is what would let the face term turn it further.

The hair cap: `Head.Hair` one vertex 0.2 mm inside the skin at rest (round 4: 1.97).

## 13. Round 10 (2026-11-16): the skin, the eyes, the hair; shape round 5 (not wired)

Critics, round 9: "a waxy, pink, uniform mannequin: dark empty sockets, no stubble, no skin breakup" (m7, the worst item
on the figure); the hair "a hard-edged dark cap" with a straight high hairline (m9, m22, m52); the head turned too little
(m19, m24); and §11.7 item 1. Take 1 never built a head (specs 06 and 07 are plans). This round builds from its zone
tables (spec 07 §3.2-§3.4: hair lengths, stubble densities), its direction field (§4.4), its hair materials (§5.1-§5.2)
and the analysis's colours (analysis §5-§9).

### 13.1 What the part is now

`head_build.py` builds the part on the rest body; `"$SGT_PYIMG" -I scripts/assemble.py --rebuild head` rebuilds it
alone (82 s). It is a script of its own, and `head.py` is left as committed, because base.py imports head_skin.py,
which imports head.py: an edit to head.py (or to anything it imports) makes assemble.py call base.blend stale, and a
base rebuild rebuilds every part. assemble.py builds the head item from head_build.py when it exists.

| Object | What | By |
|---|---|---|
| `Head.Mat.Skin` (in `cache/parts/head_look.blend`) | the skin, put on Body.Mesh at assembly | `head_look.py` |
| `Head.Eyes`, `Head.Eyes.Wet` | the eyeballs (Body.Eyes' mesh and weights, new materials) and their wet shell | `head_look.py` |
| `Head.Tearline` | a wet tube on the lower lid margin | `head_look.py` |
| `Head.Hair`, `Head.Brows`, `Head.Lashes` | Blender hair curves (Curves objects), riding the head bone | `head_groom.py` |
| `Head.Stubble` | about 16 000 three-sided mesh strands, skinned | `head_groom.py` |
| `Head.Hair.Proxy` | a 1 392-triangle mesh of the hair for engines, hidden from Cycles | `head_groom.py` |

**How it reaches the soldier without touching base.py.** The skin and the eyes live on base.blend's objects, and the
base was not to be rebuilt. So `assemble.py` now calls `head_look.on_assemble(body, rig, Part.Head)` after loading the
parts. assemble.py is not an input of any part, so nothing went stale. The hook:
- appends `Head.Mat.Skin` from `cache/parts/head_look.blend` and puts it in Body.Mesh's slot;
- hides `Body.Eyes`, `Body.Eyebrows` and `Body.Eyelashes` (the part carries its own);
- parents the curves to the head bone with the bone's rest inverse (`ob["sgt_bone"]`).

Objects carry `ob["sgt_role"]`: `render` (stubble, tear line, wet shell, the curves: Cycles only, and left out of
assemble's clash and stand-off reports) or `export` (the proxy). base.py's round-2 skin (`head_skin.py`) is still built
into base.blend; it no longer shows. Rounds 1-2's cap (`head.py build_hair`, and `head.py`'s own `bl_build`) is no
longer what the pipeline builds.

**The loop.** `scripts/tools/head_look_loop.py` rebuilds the part in memory on a copy of `cache/assembled.blend` and
renders the hero head crop, graded, beside the reference: about 100 s to build and 35 s a crop. `--r5` puts shape round
5 on the copy first. A base-only look (body and head alone through the hero pose) takes 50-110 s and gave the same skin
numbers to within 2 %, so most of the tuning ran there (`renders/head/r10/v1`-`v6`).

### 13.2 Skin (`head_look.py`)

- **One Principled BSDF** with random-walk (skin) subsurface.
  - First tried at real mean free paths (3.67 / 1.37 / 0.68 mm, weight 1): the lit skin matched, but every half-lit zone
    went orange (jaw saturation 0.56 against the drawing's 0.38), as rounds 1 and 2 found.
  - Kept: weight 0.5, radii 2.0 / 0.9 / 0.6 mm, IOR 1.4.
- **Albedo**: MPFB's diffuse times a tone, (0.557, 0.354, 0.291) linear, calibrated on the lit cheek and nose (§13.6).
- **Three mask textures** (2048², MPFB's UVs, packed; the head gets only 1.66 px/mm there). They are rasterised from
  per-vertex zone fields, placed by MediaPipe's landmarks on the model (`scripts/stages/face_targets.json`):
  - A: stubble density, grey share, the hair's cover of the scalp;
  - B: redness (nose tip and alae, cheeks, ears), oil (forehead centre, dorsum, nose tip, zygoma), pale (forehead);
  - C: under-eye, lips, and a **wrinkle height map**: 15 lines drawn in UV space as Gaussian grooves (three forehead
    creases 0.14-0.24 mm deep, the glabellar pair 0.42, three crow's feet a side, the lower-lid crease, the nasolabial
    folds 0.5).
- **Colour chain**: a 10 mm mottle (redder or yellower, ±8 %); then each zone as a multiply (red 1.07 / 0.86 / 0.84,
  under-eye 0.86 / 0.76 / 0.78, lips desaturated, the beard shadow 0.76 / 0.86 / 0.98, darker and bluer, the scalp
  under hair 0.50 / 0.46 / 0.46); then the stubs as 0.8 mm dots of hair colour, greyed 45 % on the chin.
- **Roughness** 0.44; -0.18 on the oil zone (0.26 on the T-zone), +0.16 under stubble, -0.10 on the lips, ±0.09 noise.
- **Normal**: the wrinkle map, a 2.5 mm mottle (0.35 mm high), Voronoi pores at 0.4 mm (0.12 mm high). Procedural, in
  object space.
- Every tunable is a named node (`Skin.<key>`). Nothing downloaded, nothing paid, no image requests.

### 13.3 Eyes (`head_look.py`)

- **Why the sockets were black.** Three causes:
  - round 2's black veil (alpha 0.25) over the whole eye;
  - base.py's lash and brow cards;
  - above all, geometry. The brow's lower edge stands 11 mm in front of the lid plane, and the key comes from 37° up and
    56° to his right (measured in the head's frame). The brow's shadow therefore reaches 8 mm down, to the pupil, and
    the upper lid faces away from the light. This is the face's shape (§13.5's hood) and the scene's light, not a
    material. **Corrected in §13.9**: it is not a cast shadow at all but a shelf under the brow's ridge, and the
    `orbit` field there, not the hood, removes it.
- **The ball** (`Head.Mat.Eye`): iris, limbal ring, pupil and sclera from one radial ramp on a new UV map (`IrisUV`,
  planar about the iris axis, so it survives export).
  - Iris 12.2 mm: grey-hazel #5b4a3e, #7a6a55 round the pupil, limbal ring #2a201b, radial fibres. Analysis §5 found not
    one blue pixel in the drawing's irises; they read light through the cornea's reflection, and so do these.
  - Sclera #b9aea8, reddening to #96766e at the canthi, with faint veins.
  - The iris axis is base.py's pupil mark. `gaze_deg` (8° to his right, 14° down) turns the iris on the ball so that it
    sits in the fissure: MPFB's iris centre is 2.7 mm above the fissure's middle, and with the head turned 17° to his
    left a straight-ahead iris leaves a wide white on the camera's side. At 9° down and 4° left (a2-a5) the eyes read
    rolled up and away. The eye bones stay unposed.
- **The wet shell** (`Head.Mat.Cornea` on MPFB's outer layer, the object `Head.Eyes.Wet`): a sharp glossy by Fresnel
  (IOR 1.376) over transparent, and transparent to shadow rays, so light reaches the iris and the cornea reflects.
- **The tear line**: a 0.42 mm wet tube along the lower lid's margin. The margin is the zero crossing of the skin's
  signed distance to the eye shell (`lid_lines`: 28-33 crossings a lid). The same crossing is the check that **the lids
  meet the eyeball**: the skin crosses the shell all the way round, so there is no gap to close.
- **Lashes and brows** are curves. `Head.Lashes`: 95 upper and 34 lower a lid, on the same lid lines. `Head.Brows`: 950
  a side, 5-8.5 mm, on a band from 0.7 below to 0.15 above MediaPipe's lower brow row (the drawn brows are low-set), each
  point kept clear of the convex ridge. MPFB's cards are hidden.

### 13.4 Hair (`head_groom.py`): what was chosen and why

**Blender's hair curves (Curves objects), generated strand by strand in numpy.** Not particle hair, and not an
interactive geometry-nodes groom: the build stays a script, every strand is a function of fields on the scalp, and
Cycles renders them with the Principled Hair BSDF.

**For glTF, a mesh proxy** (`Head.Hair.Proxy`): a thin cap over the haired scalp plus one flat tapered blade per clump
along its guide, 1 392 triangles (export_godot's budget for the hair is 3 000). A mesh and not alpha cards, because the
exporter bakes base colour, roughness and metallic only; cards would export as opaque ribbons until it bakes alpha.
`export_godot.py` now drops curves and `render` objects and takes `export` ones. **That change was not run this
round**: the assembled file has not been rebuilt with the new part.

- **Roots**: 64 400 strands by a density field.
  - In front: a soft, arched hairline 44 mm above the glabella, 7 mm lower at |x| 58, thinned 88 % at the temple
    corners (the drawing's bare temple).
  - Sides and back: MPFB's scalp group.
  - 70 roots/cm² on top, 110 on the sides; thicker strands stand in for the real 200.
- **Length**: top 27-36 mm (median 29.5), upper sides to 10, a fade to 0.6 mm at the ear top and the nape (side median
  2.4); 23 800 strands are under 6 mm. The analysis's 35-45 mm stood 49 mm over the skull in round 1.
- **Lie**: swept up, forward and to his right on top (spec 07 §4.4's vectors), back-left strands up and back, the sides
  down and back; lift 28° at the sides to 58° on top.
- **Clumps**: 173 centres 10.5 mm apart on the top. Each strand leans to its centre's guide by 0.92 t^1.3, so clumps end
  in points; 14 % of the guides are 1.35 times as long and steeper (25 spikes); 5 % of strands are flyaways.
- **Colour**: melanin 0.76, redness 0.05, tips 30 % lighter. Redness 0.28-0.55 rendered ginger.
- **Stubble** is a mesh: three-sided strands 2.4-3.9 mm long, 0.07 mm in radius, weights from the body. A mesh because
  the jaw and under-jaw blend into the neck bones and curves cannot be skinned. 30 /cm² at full density, 2.3 times that
  on the moustache and chin pad; 16 % grey, on the chin.

### 13.5 Shape round 5 (`head_shape_r5.py`, `head-shape-r5.target`, `head_shape_r5.json`; not wired)

Not a fit: explicit displacement fields on round 4's face, symmetric, skin vertices only. Seven at first (1 588
vertices moved, at most 6.7 mm, no triangle flipped against round 4), the table and numbers below; §13.9 adds two
(`orbit`, `canthus`) and has the final numbers. No helper geometry and no joint cube moves, so the rig, the eye bones and
the MHCLO fits come out unchanged. Developed in memory as a shape key on an opened base.blend; `head-shape.target` and
base.py are untouched.

```
"$SGT_BLENDER" -b --python scripts/parts/head_shape_r5.py -- --measure --write   # the numbers below, the target
```

| Field | What | Largest move |
|---|---|---|
| hood | the skin between brow and upper lid comes forward (analysis §5: hooded), strongest laterally | 4.5 mm |
| lid | the upper lid margin comes down over the eyeball | 0.3 mm |
| hollow | the cheek under the zygoma sits in along the normal (sigma 13 mm) | 3.2 mm |
| chin | the chin narrows (x scaled 16 % towards the midline) | 4.9 mm |
| jaw | the mandible's lower border, chin to angle, rises 4 mm and tucks in 3 | 4.8 mm |
| taper | the lower cheek and jaw come in towards the midline | 2.4 mm |
| crease | round 4's hard groove from beside the nose to the mouth corner, relaxed | 3.7 mm |

Measured on `cache/stages/base.blend` through the current hero pose (`cache/head_r5/measure.json`):

| | Round 4 | Round 5 |
|---|---|---|
| Hero far-cheek outline, rms (mean; + = outside the drawn line), 94 rows | 1.16 (+0.59) px | **1.03 (+0.41) px** |
| The same, rows 110-124 (mouth to chin) | +1.17 px | **+0.54 px** |
| The same, rows 68-82 / 82-96 / 96-110 | +0.61 / +0.21 / +0.37 px | +0.62 / +0.21 / +0.27 px |
| Face landmarks at fixed mesh points (face_targets.json), rms | 0.87 px | 0.83 px |
| Breadth 38 / 20 / 10 mm above the menton, in front of the ears | 139.5 / 102.8 / 101.9 mm | **131.7 / 98.7 / 100.5 mm** |
| Head yaw now / the yaw a rigid head turn on the landmarks asks for | 17.45° / 17.49° | 17.45° / **17.44°** |

- The far-cheek measure is `head_shape.sil_hero`'s (the reference's last pixel brighter than 70 from the right). On this
  pose it reads round 4 at 1.16 px; §11.3's harness (round 1's pose) read 1.08. The breadths are this script's own
  slices, not §11.3's.
- **The yaw.** Round 7's question, asked the same way of both faces: hold the body and turn the head rigidly about the
  head bone to best fit the 402 landmarks. Round 4 asks for +0.03° over the solved 17.45°; round 5 for -0.01°. So the
  face term would **not** turn the head further with this shape. (Round 7's 18.2° was measured from round 4's pose at
  14.9°; the solve has since taken it.) The correspondences are fixed mesh points, not a fresh MediaPipe detection, and
  the sculpt hardly moves them. The turn the critics miss will not come from the face term.
- **The near jaw line.** A hero jaw-line measure was tried: the first under-jaw face (normal turned down) in each of
  head_jaw_marks.json's eight columns. It scatters ±3 px between neighbouring marks on both faces (means +0.5 and
  +1.0 px) and does not resolve a 4 mm change. It is in measure.json and is not evidence; the jaw is judged by eye below.

### 13.6 Numbers and renders looked at

Region means in the graded hero crop against `ref/crop_head_face.png` (hex, HSV saturation; boxes from analysis §7's
table). Round 10 is `renders/round_10/head_face_cycles.png` (the old part); "new" is `renders/head/r10/a2_r4face/`
(the new part on round 4's face, in the assembled scene).

| Region | Reference | Round 10 | New |
|---|---|---|---|
| Forehead | #b88878, 0.35 | #bd9184, 0.30 | #c58b74, 0.41 |
| Near cheek, lit | #c58f7d, 0.36 | #c7a69c, 0.22 | #cc9684, 0.35 |
| Nose dorsum | #cd9480, 0.37 | #ca9d92, 0.28 | #d29986, 0.36 |
| Chin pad (stubble) | #78584c, 0.37 | #81665f, 0.26 | #7b5042, 0.47 |
| Moustache | #735146, 0.39 | #93746d, 0.26 | #8e6051, 0.43 |
| Near jaw (stubble, half lit) | #a87d66, 0.39 | #8c5a4a, 0.47 | #a16145, 0.57 |
| Under the eye | #a17265, 0.37 | #a66d5d, 0.44 | #aa6046, 0.59 |
| Ear | #c78772, 0.43 | #9f695a, 0.43 | #ac684f, 0.54 |
| Temple fade (hair over scalp) | #7b604f | #443630 | #855742 |
| Hair top | #543c32, 0.41 | #443935, 0.21 | #512c1f, 0.62 |

So: the lit skin's colour is on the drawing (it was 0.14 short of its saturation); the stubble zones are as dark as
drawn on the chin and still light on the moustache; the fade reads as hair over scalp instead of a dark cap; and every
half-lit zone (near jaw, under-eye, ear) is over-saturated by 0.1-0.2, as is the hair top.

Renders opened (`renders/head/r10/`):
- `v1`-`v6/hero_head_face_pair.png` (base-only looks; reference | model | 50 %): the steps. v1 the skin alone on a bald
  head, the orbit a black band; v2 the first groom, with the export proxy showing by mistake; v3-v6 the tuning.
- `v6/zoom_g_eye_right_x20_sheet.png`: the brow is strands along the ridge; the iris, grey sclera and tear line show;
  the upper lid under the brow is in deep orange shadow; no key highlight on the cornea (the brow shadows it).
- `v6/zoom_g_jaw_x10_sheet.png`: the stubble reads as hairs with a greyer chin; the lips are fuller and pinker than
  drawn; the moustache is thinner than drawn.
- `a1/head_face_pair.png`: the first look in the assembled scene (gaiter and carrier on); the same skin numbers as the
  base-only look.
- `a2_r4face/head_face_pair.png`, `a4_r4face/head_face_pair.png`: the new part on round 4's face, which is what a
  re-assembly gives now. Both have the earlier gaze (4° to his left; a2 9° down, a4 14°); neither is the final part.
- `a3_r5face/`, `a5_r5face/` and `a6_r5face/` (`head_face_pair.png`, `zoom_*_pair.png`; a3 also
  `soldier_full_pair.png`): the same on the first round-5 sculpt. a6 has the final gaze (§13.3); a2-a5 differ from it
  only in the gaze and the brow's tail. **The final part and sculpt are `a7_r5face/` (§13.9).**
- `a6_r5face/zoom_z_head_x8_pair.png`: the irises sit nearer the middle of each fissure than in a5; a white still
  shows under them from the low camera.

What they show, honestly:
- It no longer reads as a mannequin: skin with a lit, slightly oily forehead and nose, a beard shadow with real stubs,
  brows of hair, eyes with an iris, short lifted hair with a soft hairline, a bare temple and a fade.
- **The eyes are still the weakest thing.** The band between brow and eye is a dark, saturated shadow, taller than the
  drawn brow by about 4 mm, and the eyes sit in it. The hood made the lid visible; it did not light it.
- The hair is lifted and piecey in the fringe but smoother and more orange in the key than the drawing's, which has
  chunkier, darker separations.
- Round 5 against round 4 at hero scale is a small change: a narrower chin and lower cheek, a softer nose-side crease.
  The face is still fuller and squarer below the cheekbones than the drawing's, and the near jaw angle still sits low.

### 13.7 Switching the pipeline to round 5

Cheaper than §11.6, because no bone, helper or joint cube moves:

1. `cp scripts/parts/head-shape-r5.target scripts/parts/head-shape.target`. The file is the displacement of the
   round-1 face (round 4's plus the sculpt), as base.py's `head_shape.apply` expects.
2. Rebuild the base (`"$SGT_PYIMG" -I scripts/assemble.py --rebuild base`, 20 s). Check in `cache/stages/base.json`
   that the stature is still 1844.07 mm and the bones are unchanged; the pose should not need a re-solve
   (`pose_needs_solve` will say). The solved landmarks (pupils, nose tip, chin) should move under 0.5 mm.
3. Every part goes stale by the base's date. Only the head depends on the face's skin, and the sculpt stops above the
   neck, so the gaiter is not affected; but assemble.py will rebuild them all (`--rebuild` with no names).
4. Optional, for the next pose solve: `head.py --check r10` on the new base and
   `pose_solve.build_face_targets("r10")`. The zone masks and brows read `face_targets.json`; the sculpt moves its
   points little (0.87 -> 0.83 px), so they work unrefreshed.
5. `assemble.py --round N`. Compare `head_face_compare.png` with `renders/head/r10/a7_r5face/head_face_pair.png`.
6. To go back: `git checkout scripts/parts/head-shape.target`.

### 13.8 Still wrong, ranked for round 11

1. **The orbit and the gaze** (see §13.9: the band was a shelf in the shape, fixed in round 5). The irises still sit high in the fissure with a white under them (a6); the lids are
   wider open than the drawn, narrowed eyes (aspect 0.28). The brow shadows the whole upper lid and the eye under the scene's key (§13.3). The shape can go
   further (a shallower orbit, a lower brow ridge: the drawing's brows sit about 4 mm nearer the eyes), or the
   evaluation light can gain a fill; the drawing has one. The shadow is also too saturated: skin albedo inter-reflected
   in a hollow, not subsurface (weight 0.35 and 0.5 gave the same 0.60).
2. **Half-lit skin is over-saturated** (near jaw 0.57 against 0.39, ear 0.54 against 0.43). The same cause; a cooler,
   stronger fill or a less saturated albedo with a redder subsurface colour would address it.
3. **The face below the cheekbones** is still fuller and squarer than drawn, the near jaw angle low, the lips full and
   pink where the drawing's are thin and pressed (no lip sculpt this round), the expression neutral.
4. **The head's turn and the level chin** (m19, m24) are untouched: the pose was not re-solved, and §13.5 shows the
   face term will not turn it. It needs a pose decision (a yaw prior from the drawing's ~20°, a chin-up prior).
5. **Hair**: the top reads smoother than the drawing's clumps at hero scale and orange in the key; the hairline's
   baby hairs are sparse; the crown and back were not looked at (no rear render this round).
6. **The moustache** is lighter than drawn (#8e6051 against #735146).
7. **Export is untested**: the proxy, the `sgt_role` handling in export_godot.py, the bake of `Head.Mat.Skin` (object-
   space procedural detail bakes in the rest pose; the wet shell and the curves are dropped). The proxy's blade roots
   were lifted 2.5 mm after 130 of its vertices sat up to 1.35 mm inside the skin; `cache/parts/head.json` has the
   current clearance.
8. `scripts/tools/look_loop.py`'s part mask colours meshes only: hair curves keep their own colour in its mask pass.
9. The wrinkle map is 1.66 px/mm: the lines are soft at zoom. A head-only UV tile or a 4096² mask would sharpen them.
10. §11.7 items 2-6 stand (R001's jaw angle, the chin-neck crease, camera dependence, the relief term, 12 flips).

### 13.9 Follow-up (2026-11-16): the band between brow and eye was geometry, and the crown

The coordinator, on `a6_r5face/head_face_pair.png`: the band between the brows and the eyes is a hard-edged, saturated
strip from temple to temple that reads as goggles, not as a soft shadow. §13.3 and §13.8 item 1 called it the brow's
shadow under the key. That was wrong, and the toggles show it.

**The toggles** (`renders/head/r10/band/`, the base and the cached part through the hero pose, one change each;
`sheet.png` has them side by side):

| Toggle | Band |
|---|---|
| A as built | there |
| B no brows, lashes, wet shell, tear line, stubble or hair | there: not the strands, not the shell |
| C a plain grey diffuse on the body (no textures, no subsurface, no bump) | there, as a grey strip with the same edges: not a mask zone, not the material |
| D the body casts no shadows | **there, unchanged: not a cast shadow** |
| E the eyeballs hidden too | there |
| G the body subdivided twice | there: not a shadow-terminator artefact of the coarse mesh |
| W Workbench clay | a ledge: the brow's lower edge is a sharp ridge with a flat underside running back to the lid |

So it is **the face's shape, in rounds 1-4, already in base.blend** (round 9 shows the same band under the old skin).
- The brow's lower edge is a crisp ridge standing 10 mm proud of the lid and only 6 mm above it. Its underside is a
  flat shelf turned down and away from both lights, so it is unlit whatever casts shadows; its crisp top edge is the
  ridge and its crisp bottom edge the lid's crease.
- Lateral of each eye, round 4 left the orbital rim crumpled: 6-7 mm edges folded 50-70° (the ragged dark marks at the
  brow's tail), and round 4's outer-canthus patch left 0.4-1.5 mm edges folded 90-120° at the corner of the eye.
- The saturation was the skin's albedo: matched on the lit cheek, where AgX desaturates, it was too saturated for the
  half-light, where skin is lit mostly by skin.
- Round 5's first `hood` field (§13.5) sat on the ridge, not under it, and did not change this.

**The fix** is in the shape, so it is in `head-shape-r5.target` and shows only once round 5 is wired (§13.7). Round 4's
face, which a re-assembly gives today, keeps the band.
- `orbit` (new field in `head_shape_r5.py`): 30 passes of position relaxing between the brow's top and the lid (the
  lid margin held over the eye; lateral of the outer canthus the mask runs down past the eye's level, over the rim).
  The ridge rounds off and the shelf becomes a slope. Largest move 9.4 mm, 490 vertices.
- `canthus` (new field): 16 passes within 5 mm of each outer canthus. Largest move 2.7 mm.
- Folds lateral of the eye (edges over 35°, |x| > 54): 14 on round 4, 7 on round 5; the worst 71° -> 60°.
- The skin's tone 25 % less saturated: (0.557, 0.354, 0.291) -> (0.516, 0.364, 0.316).

**Round 5's numbers again** (`cache/head_r5/measure.json`; the table in §13.5 is the first sculpt's): 2 162 vertices
moved, at most 6.7 mm, no triangle flipped. Hero far-cheek outline 1.16 (+0.59) -> **0.89 (+0.27) px**; by band 68-82 /
82-96 / 96-110 / 110-124: +0.61 / +0.21 / +0.37 / +1.17 -> **+0.17 / +0.09 / +0.27 / +0.54**. Landmarks 0.87 -> 0.83
px. Yaw the landmarks ask for: 17.43° against the solved 17.45°, so still no further turn from the face term.

**The crown** (the coordinator: a smooth orange-brown patch where the strands thin to the scalp). The top had 70
roots/cm² and the scalp under hair was only shaded to half the skin's colour, so the scalp showed between the clumps
in the key. Now 105 roots/cm² on top, the scalp under hair at 0.30 / 0.27 / 0.27 of the skin, and melanin 0.76 -> 0.88.

**Renders opened** (`renders/head/r10/`):
- `band/sheet.png`, `band/sheet_r5.png`, `band/sheet_r5b.png`, `band/r5_C_grey_no_fuzz.png`: the toggles; on round 5 in
  grey the strip is gone and the orbit shades softly; thin crease lines remain at the lateral rim.
- `a7_r5face/head_face_pair.png` (**the final part on round 5**, in the assembled scene): no strip. The brows read as
  brows with a soft shadow under them; both eyes show iris and sclera; the hair is dark brown to the top with no
  orange patch.
- `a7_r5face/zoom_g_eye_right_x20_pair.png`: brow strands over a rounded ridge, the upper lid visible and softly
  shaded, a catchlight on the cornea, lashes on the lid.

Region means in `a7_r5face` (hex, saturation; the reference in §13.6): near cheek #c79481, 0.35; nose #cf9a88, 0.34;
chin stubble #785144; moustache #8a6053; near jaw 0.55; under-eye 0.54; ear 0.52; temple fade #7d5543; hair top
#341e17, 0.55.

**Still wrong after it**, replacing §13.8 items 1, 2 and 5:
1. The brows now sit higher and more arched than the drawn low, straight ones, and a few inner strands fan upward.
   The eyes read a little wide; the drawn ones are narrowed.
2. Half-lit skin is still over-saturated, less than before (near jaw 0.55, under-eye 0.54 against 0.39 and 0.37).
   What is left is the light: the drawing's shadow side is filled cool (far cheek #aa8e8e, saturation 0.16). A
   **proposal, not made**: in `scripts/eval/scene.py` raise the cool side light or the world by about a third, or add
   a low frontal fill. It affects every part, so it is the coordinator's call.
3. The hair top is now darker than drawn (#341e17, value 0.21, against #543c32, 0.33); melanin about 0.82 would sit
   between. Not re-rendered.
4. Thin crease lines remain at the lateral orbital rim in the grey render (7 edges over 35°).
5. Nothing here was seen on round 4's face after the tone and hair changes: the cached part is built on it, but the
   last look on it (a4) predates them.
