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
