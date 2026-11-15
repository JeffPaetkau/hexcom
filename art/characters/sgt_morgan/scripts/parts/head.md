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
