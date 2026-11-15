# Part 07 — Hair and grooming (scalp hair, stubble, eyebrows, eyelashes)

Status: draft 1 (spec writer), 2026-10-07. Owner script: `scripts/parts/07_hair_grooming.py` (plus `scripts/lib/groom.py`: root sampler, guide and child generators, melanin calibration, `measure_groom()`). Object prefix `Hair.*`. Vertex groups and attributes on the body mesh `Hair.Region.*`. Materials `Hair.Mat.*`. Debug images `Hair.Map.*`.

Conventions (from `CLAUDE.md`): millimetres in this spec, metres in Blender; world origin on the floor midway between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT = viewer's right**. Every left/right is the soldier's own. "Toward his right" in the hair sweep means toward −X. In addition this spec uses a **head frame H**: origin at the midpoint of the two tragions, the Frankfort horizontal (tragion–orbitale) as the XY plane, +Z up, −Y forward (out of the face), +X his left. All groom coordinates, direction fields and camera positions below are in H unless marked world; the build reads the real landmark Empties `Head.Anchor.*` from spec 06 at run time and maps H onto them, so the numbers here are targets, not hard-coded positions.

Source-of-truth rule applied (CLAUDE.md, 2026-10-07): where the generated image contradicts reality, reality wins; the image is used for identity (style, sweep, spike silhouette, colour, stubble map, brow shape). Every such call is in the §2.4 decision table.

---

## 1. Purpose and acceptance

### 1.1 What this part is
Everything that grows out of Sgt. Morgan's head skin: the scalp hair (a short textured crop pushed up and toward his right, faded sides), the 3–4 mm beard stubble with its density and grey maps, the two eyebrows, the four eyelash rows, the vellus and the terminal hair decisions for the rest of the visible skin (the lit strip of his right neck), the materials of all of them, the surface masks the skin shader (spec 06) needs to show follicles and beard shadow where hair is too short to be a strand, the attachment of all strands to the head so they ride the rig, the level-of-detail sets that keep render time in budget, and the evaluation renders that are compared with `ref/crop_head_face.png`. It does not own the head mesh, the skin shader, the eyes, the ears or the gaiter; it owns the strands that touch them and the masks it hands over.

### 1.2 What "perfect" looks like
At 2048 px in the hero head crop a critic sees individual hairs, not a cap: a scissor-cut top of 35–45 mm strands separated by matte clay into eight to ten piecey spikes whose tips break the dark hangar as the reference's do, swept up and toward his right with the fringe lifted forward and up, the back-left splaying up and back; upper sides of 10–15 mm hair lying down and back; a skin-blended fade down the temples where scalp shows through 1–3 mm clipper-cut stubs and reaches bare skin at the top of the ear; a gently arched hairline with 2–5 mm baby hairs on its edge and no widow's peak; root colour a medium-dark warm brown whose lit tips go golden-brown under the key, with one strand in ten a shade lighter, no grey on the scalp. Below the nose a 3–4 mm trimmed stubble (longer and denser on the chin and moustache, thinner on the cheeks, bare above a tragus-to-mouth-corner line) in which the critic can pick out individual grey and white hairs on the chin and soul patch, fewer on the moustache, none on the cheeks, fading naturally under the jaw onto the neck with no shaved line. Dense, straight, low-set brows with squared inner heads and a lateral downward hook, every hair lying in the real directions, never a floating card. Short-looking dark lashes with a real 8–10 mm length hidden by the hooded lid. Nothing uniformly fuzzy, nothing wet, nothing symmetrical, nothing intersecting the skin, nothing floating above it.

### 1.3 Closeup render views (positions in frame H unless marked world; definitions for the render harness in §8.1)

| View | Camera position (mm) | Target (mm) | Lens / sensor / size | Compared with |
|---|---|---|---|---|
| V1 Hero head crop | **world** hero camera (0, −4500, 600), rotation (93.9°, 0, 0), 46 mm, render border x 725–895, y 0–170 of the 1672 × 941 frame, upscaled ×5 | — | 46 mm, 36 mm sensor; border output ≈ 170 × 170 px → compared at 850 × 850 | `ref/crop_head_face.png`, `ref/zoom_hair_spikes_silhouette_x10.png`, `ref/zoom_hair07_top_silhouette_x10.png`, `ref/zoom_hair_right_side_fade_x10.png`, `ref/zoom_hair_left_side_shadow_x10.png`; also rendered at 2048² with lens 368 mm from the same position (identical perspective, 8× the hero frame) for the critic |
| V2 Right profile | (−900, +10, +40) looking +X, camera up +Z | (0, +10, +40) | 100 mm, 2048² | no reference profile exists; compared with the §3.2 zone table (fade heights above the ear, sideburn end at the tragus, parietal blend, top length) and with `ref/zoom_hair07_rtemple_fade_x12.png` for the fade's skin fraction |
| V3 Top silhouette | (0, +20, +1000) looking −Z, camera up = −Y (forehead at the top of the frame), world background black, `film_transparent` | (0, +20, +120) | 85 mm, 2048² | §3.3 spike table (count 8–10, cluster positions, apex heights); the alpha is used for the spike count metric in §8.2 |
| V4 Stubble macro | (−300, −380, −60) | (−10, −90, −95) | 100 mm, 2048², DOF f/8 focused on the chin pad | `ref/zoom_face_mouth_chin_x14.png`, `ref/face_zooms/z_lowerface_contrast_x10.png`, `ref/zoom_hair07_stubble_contrast_x8.png` (density zones, grey hairs, neckline) |
| V5 Brow and lash macro (right eye) | (−120, −520, +60) | (−15, −100, +22) | 135 mm, 2048², DOF f/8 on the lash line | `ref/zoom_hair_brows_x12.png`, `ref/zoom_face_eyes_both_x16.png`, `ref/zoom_hair07_brows_lashes_x12.png` |
| V6 Nape and crown (assumption check) | (0, +900, +20) looking −Y | (0, +60, +30) | 100 mm, 2048² | no reference; §3.2 nape taper and §3.3 whorl position, critic judges plausibility only |

Each view is rendered under the hero lights (consolidated §8, AgX "Medium High Contrast") for colour, and under the neutral look-dev key of spec 01 §8.1 for form. Fast variants in Workbench (§8.1) for the loop.

### 1.4 Pass criteria a critic can score (full list in §8.3)
1. V3 / V1 alpha: **8 to 10** silhouette spikes above the hair mass with ≥ 1 px prominence at hero scale (the detector of §8.2 run on the render), the tallest cluster within 8 mm of the drawn apex (image x 812, y 12), and the lateral right-front cluster (image x 760–764) present as a spike leaning to his right.
2. Length gradient read from the curves data: top zone mean 38–42 mm, p95 ≤ 46 mm; upper-sides 10–15 mm; temple band 1.5–3 mm; ear-top band ≤ 0.6 mm; nape 8 → 1 mm (§3.2 table, ±15 %).
3. Fade: in V1 the right temple ROI (image 757–772 × 62–78) has mean luminance 103–123 and mean colour within ΔE76 < 10 of #856856 (≈ 50 % scalp showing); no visible step in hair length anywhere on the sides (a critic cannot point to a clipper line).
4. Colour: in V1 the hair-top ROI (775–840 × 22–40) mean within ΔE < 8 of #352922 with luminance percentiles p5/p50/p95 within ±12 of 9/36/102; lit fringe ROI (775–800 × 30–46) within ΔE < 10 of #4c372b; lit tips visibly golden-brown (p95 pixels hue 20–35°, saturation ≥ 0.3), no orange, no black-cap pixels below lum 6 inside the mass except in cast shadow.
5. Sweep direction: ≥ 70 % of top-zone strands have a tangent component toward −X (his right) at mid-length; the fringe lifts forward (−Y) and up; a mirrored groom fails.
6. Hairline: gently arched through the trichion, temple corners 15–18 mm back from the trichion's frontal plane and ≈ 13 mm lower, no peak, no recession beyond Norwood II; baby-hair band 3–4 mm wide with 2–5 mm hairs; no bald gap between hairline and hair.
7. Stubble: zone densities as §3.4 (dense chin/moustache/jaw/under-jaw, medium lower cheek, sparse upper cheek, bare above the line) measured per zone from the curve roots within ±15 %; lengths 3.5–4.0 mm chin and moustache, 2.5–3.0 mm cheeks; in V4 individual grey hairs are countable on the chin (20–30 % of chin strands, 8–12 % moustache, 0 % cheeks); the neckline is a gradient over ≥ 25 mm, not a line.
8. Chin-pad ROI (808–826 × 116–128) in V1 within ΔE < 10 of #78574a and 30–40 % darker in luminance than the bare upper-cheek ROI (782–796 × 92–100); the moustache ROI within ΔE < 10 of #714f44; the medium-stubble lower cheek shows high-pass texture ≥ 2× the bare cheek's (analyst's 5.2 vs 2.3).
9. Brows: body 8–9 mm tall, inner heads squared and 20–22 mm apart, straight body with the peak at 60–65 % of the span and a tail hooking 3–4 mm downward; mean colour in V1 within ΔE < 10 of #674435 (right, lit) and #432f26 (left, shadow); no card edge, no gap to the skin, hairs visibly individual at V5.
10. Lashes: upper 100–140 per eye in 4–5 rows, 8–10 mm long with a 25–35° lift, lower 50–70 at 5–7 mm; at hero scale they read as a dark 1 px lash line (#3b2219 ± ΔE 12 at image (799,73)), never as doll lashes.
11. Strand thickness: at V1 ×8 (2048²) single strands are 1–3 px wide; no "spaghetti" (> 4 px) and no sparkle (isolated 1-px bright specks > 3 % of hair pixels after denoise).
12. No strand root more than 0.3 mm off the skin surface; no strand passing through the skin, ear or gaiter; nothing of the MakeHuman proxy hair, brow or lash assets present in the file.

---

## 2. Reference observations

All coordinates are full-image pixels of `ref/reference_full.png` (1672 × 941; 2.12 mm/px at the figure, ≈ 2.1 mm/px at the head, consolidated "Agreed scale"). The head is yawed ≈ 20° to his left, pitched ≈ 12° chin-up relative to the camera ray, seen from ≈ 13° below, so his right side (viewer's left) is the exposed side and the left side is in the cool fill.

### 2.1 What the image shows (from the analyses, checked on the zooms)

| Observation | Pixels | Derived (mm) | Source |
|---|---|---|---|
| Hair mass top / spike tips | y = 20 / y = 12–14 at x 812–814 | mass 59 mm above the trichion (includes the skull dome), spike tips 72 mm | consolidated §3, disputes #2; my scan below |
| Hairline centre (trichion) | (810, 48) | forehead fully exposed, fringe lifted | consolidated §2 |
| Temple corners of the hairline | (779, 50–52) and (838, 50–52) | gently arched, no widow's peak, no recession | face note §8 |
| Right temple fade zone | (757–775, 55–75) mean #7c6150, lum 103 | ≈ 50 % scalp showing; hair 1–3 mm | face note §8 |
| Sideburn end | y ≈ 92 (tragus level) | 18 mm below the ear top, 9 mm above the tragion | face note §8 |
| Right ear | top 83.5, bottom 112, front 770, back 753 | 61 × 36 mm, bare, no hair over it | consolidated §2 |
| Hair colour percentiles (762–845 × 28–50) | p5 #1e1816, p25 #37261e, p50 #4f483a, p75 #907060, p95 #bd8871 | lit values under a 4500 K key; albedo root #3a2a1e, tip #8a6549, 10 % of strands #a07a5e | face note §8 |
| Stubble zones | dense (806–828 × 114–130) #815f53; moustache (806–826 × 99–106) #745147; jaw (772–790 × 112–124) #a97d66; bare cheek #c5907d | 2.5–4 mm, salt-and-pepper chin | face note §9 |
| Brows | right inner/peak/tail (809,72)/(796,70.5)/(786,73.5); left (819,72)/(832,70.5)/(843,74); body 3.5–4.5 px | 8–9 mm thick, inner heads 10 px = 21 mm apart, lit #654233, shadow #4a3228 | face note §5 |
| Lash line | (799,73) #3b2219, ≈ 1 px | reads 3–4 mm; see decision D6 | face note §5 |
| Not present | helmet, cap, headset, eyewear, face paint; right ear bare; no grey in the scalp hair | — | consolidated §3 |

### 2.2 My own measurements (`ref/zoom_hair07_measure.py` and `ref/zoom_hair07_measure2.py`, run with `python3 -I <script> ref/reference_full.png ref`; zooms written to `ref/zoom_hair07_*.png`)

**Silhouette top per column** (first row from y = 8 with luminance > 28; background is lum 9–12): the hair mass rises from y 37 at x 765 to y 24 at x 781, to 20 at x 787–791, 15–16 at x 799–810, the apex **y 12 at x 812–813**, back to 16–18 at x 816–826, 21–23 at x 827–835, 28–30 at x 837–843, and ends at x 846. A separate cluster at **x 760–764 tops out at y 24** while its neighbours at x 759 / 765 are at y 44 / 37: a spike 13 px (27 mm) proud of the side, leaning out to his right at the right-front corner.

**Spike count.** With a 3–4 px window and ≥ 1 px prominence the detector finds **9** spikes: x 761 (y 24, prominence 13), 792 (18, 1), 799 (15, 1), 806 (14, 2), 812 (12, 4), 825 (15, 2), 832 (22, 1), 836 (20, 4), 842 (29, 1). At ≥ 2 px prominence, 5 remain (761, 806, 812, 825, 836). The analysts' "8–10" is confirmed at the 1 px level; the five strong ones are the ones a thumbnail shows. Acceptance uses the same detector (§8.2).

**Hair-mass outline per row** (lum > 28, x 740–870): y 14 → 806–815 (9 px); y 16 → 799–826; y 20 → 787–836 (49 px); y 24 → 760–836 (76 px, the lateral cluster arrives); y 30 → 760–843 (83); y 40 → 762–844 (82); y 50–58 → 755–845 (90 px = 190 mm, the skull plus 10–15 mm of side hair on each side; ANSUR head breadth 154 mm + 2 × 12 mm of hair + the 20° yaw's foreshortening of the depth into width is consistent).

**Hairline per column** (first row with R > 150 and R − B > 40 from y 30): x 780 → 47, 785 → 51, 790 → 44, 795 → 42, 800–805 → 41, 810 → 42, 815–820 → 44, 825 → 46; x 770–775 → 63 (the temple hair over the fade). The arch's lowest skin row is 41 at x 800–805 (the lifted fringe casts no shadow there); the trichion at (810, 48) in the analyst's table is the hair's edge, mine is the skin's — a 3–4 mm baby-hair band lies between.

**Zone colours (means, luminance percentiles p5/25/50/75/95):**

| Zone (px) | Mean | Lum percentiles | Reading |
|---|---|---|---|
| Hair top mass 775–840 × 22–40 | #352922 | 9 / 20 / 36 / 64 / 102 | dark mass with lit tips |
| Fringe, lit 775–800 × 30–46 | #4c372b | 9 / 24 / 56 / 89 / 133 | the key hits the fringe tips |
| Right upper side 762–778 × 48–60 | #564134 | 23 / 50 / 68 / 88 / 120 | 10–15 mm hair, lit |
| Right temple fade 757–772 × 62–78 | #856856 | 82 / 101 / 113 / 122 / 135 | ≈ 50 % skin |
| Right fade at ear top 755–768 × 78–86 | #896755 | 39 / 96 / 108 / 127 / 172 | skin dominant, hair < 1 mm |
| Skin, right temple 776–784 × 66–76 | #dfb8a4 | 138 / 187 / 201 / 208 / 214 | key-lit bare skin |
| Left side, shadow 838–848 × 44–60 | #3c3636 | 13 / 22 / 52 / 78 / 114 | cool fill; neutral grey-brown |
| Left temple 840–848 × 60–75 | #4d4a4c | 10 / 15 / 93 / 123 / 147 | fade in blue fill |
| Right brow body 790–805 × 69–73 | #674435 | 42 / 57 / 76 / 97 / 114 | |
| Left brow body 822–838 × 69–73 | #432f26 | 30 / 39 / 47 / 61 / 83 | |
| Forehead above the brow 790–806 × 60–66 | #b68a7a | 90 / 140 / 156 / 168 / 173 | |
| Chin pad 808–826 × 116–128 | #78574a | 48 / 81 / 97 / 112 / 136 | dense stubble, part grey |
| Soul patch 811–821 × 112–118 | #634036 | 39 / 49 / 64 / 93 / 124 | densest |
| Moustache 806–826 × 100–106 | #714f44 | 56 / 68 / 86 / 105 / 125 | in nose shadow too |
| Right jaw 774–790 × 112–124 | #a67b65 | 102 / 122 / 135 / 146 / 158 | dense, lit |
| Right cheek mid (medium) 782–796 × 104–112 | #c0927c | 132 / 145 / 157 / 171 / 179 | 2 % darker than bare, textured |
| Right cheek upper (bare) 782–796 × 92–100 | #c6907c | 143 / 151 / 159 / 164 / 169 | smooth |
| Under-jaw neck 782–810 × 130–140 | #453024 | 11 / 27 / 47 / 75 / 118 | stubble in shadow |
| Neck below 790–810 × 142–150 | #6e4e3e | 20 / 39 / 89 / 125 / 155 | gaiter roll begins |

**Fade column scans** (luminance down x = 760 / 764 / 768 / 772 from y 56 to 96): hair-dominated (lum 72–104) down to y 60–64, then a mixed band 87–131 from y 64 to 84, then skin-dominated (143–212) below y 88 at x 764–772 — a 20–24 px (42–50 mm) blend from "hair" to "skin", with the ear top at y 83.5. The blend is smooth: no two adjacent 4-px rows differ by more than 45 luminance except at the ear's own shadow.

**Brow thickness per column** (rows with lum < 110 between y 64 and 80): the right brow body occupies 4 rows at x 786–788, 10–11 at 790–794, 14–15 at 796–806 (that count includes the deep-set orbit's shadow under the brow, so the brow body itself is the analysts' 3.5–4.5 px), 8 at x 810 and 5 at 812; the left brow the mirror from x 818 to 838. The inner heads at x 809–812 and 818–820 are 4–5 rows tall and nearly vertical.

**What the strand-contrast zoom shows** (`ref/zoom_hair07_strands_contrast_x8.png`, `ref/face_zooms/z_hair_contrast_x10.png`): individual lit clumps 2–4 px wide (4–8 mm) separated by dark gaps; the front third leans to his right at 45–60° from the scalp; the crown clumps point up; the back-left ones lean back; the sides are flat and dark. The clumps have light tips and dark roots: product-separated hair lit from above-right-front.

### 2.3 Ambiguities
* The hair top above y 20 is partly transparent (lum 20–40 between spikes): a volume of separated strands, not a solid. The IoU metric therefore uses a luminance threshold of 28 for both reference and render.
* The left side (x 838–848) is in the cool fill and its hair reads neutral grey (#3c3636): this is lighting, not grey hair. Hue checks are done only on the right side.
* The sideburn's exact bottom is uncertain by ±4 px (the ear's own shadow); adopted tragus level.
* The stubble's lower boundary is hidden by the gaiter roll from y ≈ 150; what is visible fades to the roll. See D11.
* Nape, crown whorl, back of the head: not visible. Assumed in §3.2–3.3, judged for plausibility only.

### 2.4 Decisions — reality versus the image

| # | Topic | Image says | Reality says | Decision |
|---|---|---|---|---|
| D1 | Stubble length | 2.5–4 mm, uniform-trimmed look | Beard grows 0.27–0.38 mm/day (sourced, [VERIFY]); a "3–5 day" stubble is 1–2 mm. A 3–4 mm length is 8–12 days' growth or a trimmer kept at a 3–4 mm guard | **Trimmer-maintained stubble: 3.0 mm guard on cheeks and jaw, 4.0 mm on chin and moustache** (both are standard trimmer guard settings). The face note's "3–5 day" label is dropped; the lengths stand |
| D2 | Top length | 35–45 mm, fringe longest | A scissor-cut textured crop: 1.5 in (38 mm) front, 1.25 in (32 mm) crown is the standard barber instruction | **Fringe 42–46, mid-top 38–42, crown 33–37** (§3.2). Consistent, keep as drawn |
| D3 | Fade | Skin at the ear top, 50 % scalp at 1–3 mm up the temple, blend into 10–15 mm sides | A "mid skin fade": open blade (0.4–0.5 mm) at the ear top, #0.5 (1.5 mm) and #1 (3 mm) up the temple, scissor-over-comb blend at the parietal ridge (Wahl guard chart: #0.5 = 1.5 mm, #1 = 3 mm, #2 = 6 mm, #3 = 10 mm, #4 = 13 mm — sourced [VERIFY]) | **Build the fade as a real clipper fade** with the guard heights of §3.2 and blunt-cut tips; the image's 42–50 mm blend length is consistent and kept |
| D4 | Spike count | 8–10 silhouette spikes (9 by my detector) | Clay-styled 40 mm hair separates into clumps 4–8 mm wide; a 150 mm-wide top gives 10–25 clumps, of which 6–12 break the silhouette | **8–10 silhouette spikes accepted**; the groom defines 9 primary clusters at the drawn positions (§3.3) and 60–80 secondary clumps |
| D5 | Hair colour | lit p5–p95 #1e1816–#bd8871 | Medium-dark brown eumelanin hair; the golden lit tips are the 4500 K key on brown, not blond hair | Albedo root #3a2a1e, tip #8a6549, 10 % strands #a07a5e as the face note; calibrated by swatch render (§5.1), not by eye |
| D6 | Eyelash length | lash line reads 3–4 mm | Adult upper lashes are 8–12 mm, 90–160 per lid in 5–6 rows; lower 6–8 mm, 70–80 (sourced [VERIFY]). The hooded lid and the 13° low camera hide the roots and foreshorten the lashes | **Real lengths (upper 8–10 mm, lower 5–7 mm)**, overruling the face note's 3–4 mm. The projected look must still match: checked in V1 |
| D7 | Brow colour vs hair | brows cooler and darker than the lit hair | Brows are normally darker than scalp hair (coarser, more eumelanin) | Keep #5a3d30 albedo (melanin 0.78) |
| D8 | Hairline | no recession, no peak at age 38–42 | Norwood I–II is common at 40; a perfectly even arch is not | Keep the drawn arch (identity) but add real irregularity: 1–2 mm jitter, 3–4 mm baby-hair band, temple corners softened over 8 mm |
| D9 | Scalp grey | none | At 40, roughly half of Europeans show some grey at the temples (the "50/50/50" rule of thumb, [VERIFY]) | **None on the scalp** (identity cue, image is plausible); 20–30 % on the chin as drawn; 8–12 % moustache; 0 % cheeks |
| D10 | Hair density | n/a (the image cannot show it) | 150–250 follicles/cm², mean ≈ 200 for brown European hair, ≈ 100 000 scalp hairs; shaft 50–100 µm, mean ≈ 70 µm (sourced [VERIFY]) | Fade and nape at **real density** (short strands are cheap). Top and upper sides at **55 % of real density with 1.3 × real radius** (§4.6) to stay in render budget; a `--full-density` flag builds 100 % for the GPU machine. This is a budget compromise, not an overrule of reality, and it must be invisible at V1 |
| D11 | Stubble neckline | fades under the jaw to y 140–142; everything lower is under the gaiter | An untrimmed neck carries stubble down to the laryngeal prominence and below; a trimmed one has a line at the hyoid | **Natural neckline**: 100 % density on the under-jaw plane, 60 % at the hyoid (z 1622 world rest), 0 % at the laryngeal prominence (z 1590), as a 30 mm gradient. The visible 45 mm strip of neck shows the top of this gradient (§3.4) |
| D12 | Nape and crown | not visible | A skin fade continues round the back to a natural (unlined) nape; a clockwise whorl sits 20–30 mm anterior to the lambda, slightly off-centre | Assumed per §3.2–3.3, tagged estimated; V6 is a plausibility check only |
| D13 | Side hair over the ear | nothing touches the ear | The fade clears the ear by definition | 0.3–0.5 mm "skin" hair within 10 mm above the ear's attachment; the ear itself bare except 3–6 vellus/terminal hairs on the tragus, which at 40 is realistic and invisible at hero scale |
| D14 | Vellus hair | invisible | Every face has 0.2–1 mm vellus (peach fuzz) that catches rim light | Not built as strands (cost, invisible at V1); represented by Sheen 0.05 in the skin shader (spec 06 interface) |

---

## 3. Real-world reference

Each number is tagged **M** (measured from the image), **S** (sourced: published anthropometry or product data), **E** (estimated by me). Anthropometry is ANSUR II means for the 185 cm / 83 kg body (`notes/research_dimensions.md` §1f).

### 3.1 Head landmarks the groom hangs on (frame H, mm)

| Landmark | X | Y | Z | Tag | Note |
|---|---|---|---|---|---|
| Tragion L / R | ±72 | 0 | 0 | S (head breadth 154 at the euryon; bitragion ≈ 144) | frame origin is their midpoint |
| Superaurale (ear top) L / R | ±74 | −2 | +27 | E (ear length 65 S; the tragion is ≈ 42 % down the ear) | fade reaches skin here |
| Ear attachment, front edge | ±70 | −12 | 0 … +22 | E | sideburn strip lies 0–15 mm in front of it |
| Orbitale L / R | ±32 | −80 | 0 | S (defines the plane) | |
| Sellion | 0 | −100 | +20 | E | |
| Glabella | 0 | −102 | +30 | E | brow ridge |
| Brow medial head L / R | ±11 | −98 | +41 | M/E (10 px apart, 4 mm above the lid margin + the ridge) | low-set |
| Brow peak L / R | ±38 | −88 | +46 | M/E | 60–65 % along the span |
| Brow tail L / R | ±58 | −70 | +40 | M/E | hooks 3–4 mm down |
| Upper lid margin, central | ±32 | −92 | +23 | E | lash roots |
| Lower lid margin, central | ±32 | −92 | +12 | E | |
| Trichion | 0 | −88 | +92 | E (hairline height 60–65 above the glabella) | hairline centre |
| Hairline temple corners L / R | ±58 | −62 | +78 | M/E (image 779/838 at y 50–52) | soft corners |
| Vertex | 0 | +5 | +132 | S (tragion → top of head 132) | |
| Euryon L / R | ±77 | +15 | +50 | S (breadth 154) | widest point |
| Parietal ridge (temporal line) L / R | ±70 | +10 | +78 | E | where the side becomes the top |
| Opisthocranion | 0 | +101 | +35 | S (head length 203) | back of the head |
| Lambda | 0 | +75 | +95 | E | |
| Crown whorl | +15 | +50 | +118 | E (D12) | clockwise from above |
| Inion | 0 | +95 | −5 | E | |
| Nape hairline, midline | 0 | +80 | −45 | E | natural, faded |
| Pronasale | 0 | −125 | −20 | E | |
| Subnasale | 0 | −105 | −35 | E | moustache top |
| Stomion | 0 | −98 | −60 | E | |
| Mentolabial sulcus | 0 | −96 | −75 | M/E | soul patch |
| Menton | 0 | −85 | −105 | S (menton–sellion 126) | |
| Gonion L / R | ±60 | +15 | −65 | E (bigonial ≈ 120) | jawline |
| Hyoid (world rest z 1622, spec 04) | 0 | −60 | −120 | E | neckline 60 % |
| Laryngeal prominence (world rest 1592) | 0 | −62 | −150 | E | neckline 0 % |

The build does not trust this table: `groom.py::head_frame()` reads `Head.Anchor.Tragion.L/R`, `Head.Anchor.Orbitale.L/R`, `Head.Anchor.Trichion`, `Head.Anchor.Vertex`, `Head.Anchor.Glabella`, `Head.Anchor.Menton`, `Head.Anchor.Gonion.L/R`, `Head.Anchor.Superaurale.L/R`, `Head.Anchor.Brow.*`, `Head.Anchor.LidMargin.*` (spec 06 interface, §10.1) and solves a similarity transform from this table to the real Empties (least squares over the eleven shared points), then expresses every zone below in the fitted frame.

### 3.2 Scalp hair: real lengths by zone (the barber's plan)

| Zone | Where (frame H) | Length root→tip | Cut | Lie / lift from the scalp | Tag |
|---|---|---|---|---|---|
| Z1 Fringe / quiff | within 40 mm behind the frontal hairline, |X| < 55 | **42–46 mm** (p50 44) | scissor, point-cut tips | lifted 55–65°, swept forward-up and to his right | M/E (D2) |
| Z2 Mid-top | from Z1 back to 25 mm in front of the whorl, |X| < 60 | **38–42** | scissor, point-cut | 70–80°, lean to his right 15–25° | E |
| Z3 Crown | 25 mm around the whorl and back to the lambda | **33–37** | scissor | 55–65°, radiating from the whorl; back-left quadrant leans back-up | E |
| Z4 Upper sides (parietal) | from the temporal line (Z +78) up to Z +100 | **10 → 15** (bottom → top) | scissor-over-comb blend | 20–30°, lying down and back toward the ear | M (face note 10–15) |
| Z5a Blend band | Z +80 → +95 on the sides, Y +40 → +95 round the back | **3 → 10** | #1 to scissor | 30–40° | E |
| Z5b Temple / side #1 band | Z +45 → +80 | **1.5 → 3.0** | #0.5 → #1 guard, blunt tips | 40–55° (short hair stands) | M (50 % scalp zone) |
| Z5c Skin band | Z +27 → +45 | **0.4 → 1.5** | open blade | 50–60° | M/E (D3) |
| Z5d Over the ear | within 10 mm of the ear attachment | **0.3–0.5** | foil / open blade | — | E (D13) |
| Z6 Sideburn strip | 0–15 mm in front of the ear, Z +8 → +27 | **0.4–0.8** | open blade; ends at Z +8 (tragus level) | downward | M |
| Z7 Occipital | Y > +60, Z 0 → +80 | **8 → 1** (top → bottom) | taper | 30–40°, downward | E (D12) |
| Z8 Nape | Z −45 → 0 at the midline, following the natural hairline | **1 → 0.4** | open blade, no line | downward | E |
| Baby-hair band | 3–4 mm band along the whole frontal and temple hairline | **2–5** | natural | 15–25°, forward and down | E (D8) |

Hair facts used (all sourced from general dermatology references, [VERIFY] against a cited text in the critique pass): density 150–250 follicles/cm², adopted **200/cm² (175 on the crown, 220 at the occiput)**; shaft diameter 50–100 µm, adopted **70 µm** (radius 0.035); European cross-section ellipticity 1.2–1.4; growth 0.35 mm/day; hairs emerge in follicular units of 1–3; the scalp area from the hairline to the nape above the ear level is ≈ **600 cm²** (head circumference 581 mm, S), of which the top zones Z1–Z3 are ≈ 230 cm², Z4–Z5 ≈ 220 cm² and Z6–Z8 ≈ 150 cm².

### 3.3 The spikes: nine primary clusters (frame H, apex positions estimated from the image columns at 2.1 mm/px, depth guessed; the acceptance test is the rendered silhouette, not these numbers)

| Cluster | Image x (top y) | Root centre X, Y, Z | Apex X, Y, Z | Strands | Apex radius | Role | Tag |
|---|---|---|---|---|---|---|---|
| C1 | 761 (24) | −55, −45, +105 | −82, −62, +128 | 220 | 2.5 | the lateral right-front spike leaning out to his right 27 mm proud of the side | M/E |
| C2 | 792 (18) | −32, −60, +118 | −48, −78, +150 | 300 | 2.5 | fringe, forward-up-right | M/E |
| C3 | 799 (15) | −18, −55, +124 | −28, −70, +160 | 320 | 2.0 | fringe | M/E |
| C4 | 806 (14) | −6, −40, +128 | −14, −50, +166 | 350 | 2.0 | front-top | M/E |
| C5 | 812 (12) | +6, −20, +131 | −2, −26, **+172** | 400 | 2.0 | the tallest, near the vertex | M/E |
| C6 | 825 (15) | +24, −10, +128 | +22, −6, +165 | 320 | 2.0 | top, nearly vertical | M/E |
| C7 | 832 (22) | +38, +15, +122 | +44, +28, +155 | 260 | 2.5 | back-left, leaning back | M/E |
| C8 | 836 (20) | +46, +35, +115 | +58, +52, +148 | 240 | 2.5 | back-left, up-back | M/E |
| C9 | 842 (29) | +55, +50, +105 | +70, +68, +130 | 200 | 3.0 | back-left splay | M/E |

Cluster bases are 12–16 mm in radius at the scalp; the clump factor rises from 0.35 at the root to 0.85 at the tip so each reads as a point. Between the primaries, 60–80 **secondary clumps** of 40–120 strands, 6–8 mm base radius, clump 0.5, lift 35–45°, make the "piecey" texture; 5 % of top strands are left unclumped with extra noise as flyaways. Crown whorl: strands within 25 mm of (+15, +50, +118) have their lie rotated to follow a clockwise spiral (viewed from above) before the sweep is applied.

### 3.4 Beard stubble: zones, densities, lengths, grey

| Zone | Boundary (frame H) | Density /cm² | Length | Grey fraction | Tag |
|---|---|---|---|---|---|
| S1 Chin pad and soul patch | from the mentolabial sulcus down over the chin to the under-jaw plane, |X| < 28 | **55** | 3.8–4.0 | **25 % (20–30)** | M (image), E (density) |
| S2 Moustache | subnasale to the vermilion border, |X| < 26, with a 3 mm bare philtrum groove at 60 % density | **55** | 3.6–4.0 | **10 % (8–12)** | M/E |
| S3 Jawline band | 18 mm either side of the mandibular border from the gonion to the chin | **50** | 3.0 | 3 % | M/E |
| S4 Under-jaw plane | the submandibular surface from the border to the hyoid | **50 → 30** (hyoid) | 3.0 | 5 % | M/E (D11) |
| S5 Neck gradient | hyoid → laryngeal prominence | 30 → 0 | 3.0 | 5 % | E (D11) |
| S6 Lower cheek | below the tragus → mouth-corner line, above S3 | **28** | 2.6–3.0 | 0 % | M (medium) |
| S7 Upper cheek | between that line and a line 8 mm below the zygomatic arch | **10 → 0** | 2.5 | 0 % | M (sparse) |
| S8 Lip margins | 2 mm band around the vermilion | 15 | 2.5 | 0 % | E |
| Bare | cheekbones, under-eyes, nose, forehead, cheek hollow centre, lips, ear | 0 | — | — | M |

Beard facts (sourced from general references, [VERIFY]): facial hair 5 000–25 000 hairs, mean density 25–65/cm² with the chin and upper lip densest; shaft 90–130 µm, more elliptical than scalp hair, often kinked at 20–40° within the first 3 mm; growth 0.27–0.38 mm/day. Adopted radius **0.055 mm root, blunt trimmer-cut tip at 0.050** (trimmed hair is not tapered). Total over ≈ 260 cm² ≈ **11 500 strands**. Zone boundaries are feathered 6–10 mm (density is a smooth field, never a region edge).

### 3.5 Eyebrows

| Quantity | Value | Tag |
|---|---|---|
| Span along the arc, medial head → tail tip | 55–60 | M/E (image 26–30 px foreshortened) |
| Body height (thickness) | **8–9**; medial head 9–10 (squared, slightly vertical hairs); tail 2–3 | M |
| Inner heads apart | **20–22** (10 px) | M |
| Vertical position | lower edge **4 mm above the upper lid margin** at the medial head; brow sits on the ridge | M (consolidated: "4 mm above the lid margin") |
| Shape | straight body; peak at 60–65 % of the span; tail hooks down 3–4 mm beyond the orbital rim | M |
| Hair count | 300–450 per brow (S, "250–500" [VERIFY]); built as **650 strands** per brow (the extra are 4–6 mm fine hairs filling the body's density so no skin shows through at V5) | S/E |
| Length | medial head 9–11, body 8–9, tail 6–7; 10 % of body hairs 11–12 (untrimmed male brow) | S/E |
| Radius | 0.040 root → 0.015 tip, natural taper (uncut) | S/E |
| Directions | medial head: up and lateral, 60–75° from horizontal; body: lateral, 5–15° above horizontal, lying 10–20° off the skin; tail: lateral-down −15 to −25°; the lower-edge hairs angle up and the upper-edge hairs angle down so the edges interlock (real herringbone closure) | S/E (face note §5 directions) |
| Colour | albedo **#5a3d30**, melanin 0.78, redness 0.30; 4 % of hairs lighter (#7a5a48); none grey | M |

### 3.6 Eyelashes

| Quantity | Upper lid | Lower lid | Tag |
|---|---|---|---|
| Count per eye | **120** (S 90–160) | **60** (S 70–80; reduced because the lower lashes "read very sparse" and at 6 mm half of them are under the fissure's shadow) | S/E (D6) |
| Rows | 4–5 rows within a 0.8 mm band on the margin | 2–3 rows, 0.5 mm band | S |
| Length | central 9–10, medial 6–7, lateral 8 | central 6–7, ends 4–5 | S (D6) |
| Curve | lifts 25–35° from the lid plane, radius of curvature ≈ 10 mm, no upward curl beyond 45° | lifts downward 15–25° | S/E |
| Radius | 0.050 root → 0.010 tip | 0.040 → 0.010 | S/E |
| Colour | melanin 1.0 (albedo ≈ #2a1b14) | same | M (#3b2219 lash line) |
| Lash-line skin | the lid margin's skin is darkened by the roots: mask A in `Hair.Masks` (§5.4) for spec 06 | | |

### 3.7 Body and other hair visible in the hero frame
None. Hands are gloved, arms sleeved, neck below the stubble gradient is under the gaiter, chest under the shirt. Chest, axillary, shoulder and abdominal hair belong to spec 04 §6.1. The only skin this part adds strands to outside the head is the **top 30 mm of the neck** (stubble gradient S4–S5). Vellus hair everywhere: not built (D14).

---

## 4. Geometry construction plan

### 4.0 Facts the plan relies on
* Blender 4.5 `Curves` objects (`bpy.data.hair_curves.new`) build from Python in milliseconds, honour a per-point `radius` attribute in Cycles, accept Geometry Nodes modifiers headless, and render with `scene.cycles_curves.shape = "THICK"`, `subdivisions = 2` (research C §3, §10a). Legacy particle hair also works but is only the fallback.
* The bundled `procedural_hair_node_assets.blend` appends headless; inputs are set by socket identifier, enumerated at run time (research C §10a). Only `Hair Curves Noise`, `Shrinkwrap Hair Curves` and `Smooth Hair Curves` are used; interpolation, clumping and trimming are done in numpy for determinism (§4.5–4.6).
* The head mesh is the MPFB body (`Body.Mesh`, spec 06 refines the head region) with UV map `UVMap`; the eyelids, lips and ears are part of it; eyes are separate (`Eye.L/R`).
* MakeHuman proxies `eyebrow0xx`, `eyelashes0x`, `short0x`, `wdg_scruffy_beard` are never loaded; if the MPFB build left any, step 1 deletes them (research B §5: "the single biggest source of the awful look").

### 4.1 Step 1 — Read the head, build frame H, clean up
`groom.py::head_frame()` reads the `Head.Anchor.*` Empties, solves the similarity transform (§3.1), and returns `H_to_world` and `world_to_H` matrices plus the head mesh's face centroids, normals, areas and UVs in H (numpy arrays from `mesh.polygons.foreach_get`). Delete any object whose name starts with `Hair.` (idempotence) and any MakeHuman hair/brow/lash proxy. Record the posed-vs-rest state: the groom is built on the **rest** mesh (armature modifier disabled during the build) and attached (§7).

### 4.2 Step 2 — Regions as vertex groups and per-face fields (`Hair.Region.*`)
Written per vertex from H coordinates and landmark distances, each with a 6–10 mm linear feather: `Hair.Region.Scalp` (inside the hairline curve of §4.3, above the ear and nape lines), `Hair.Region.Scalp.Top` (Z1–Z3), `Hair.Region.Scalp.Sides` (Z4–Z5), `Hair.Region.Scalp.Back` (Z7–Z8), `Hair.Region.Beard` (S1–S8 union), `Hair.Region.Brow.L/R` (the brow shape of §3.5 as a 2D polygon in the local brow plane, 1.5 mm feather), `Hair.Region.LidMargin.L/R.Upper/Lower` (0.8 / 0.5 mm bands along the margin curves), `Hair.Region.NoHair` (ears except the tragus, lips, nostrils, eyes). Per-face float fields (named attributes on the mesh, FACE domain, and mirrored into `Hair.Map.*.png` debug images through a UV rasteriser in numpy): `hair_density` (/cm², §3.2 and §3.4 values blended), `hair_length_mm`, `hair_lift_deg`, `hair_dir` (FLOAT_VECTOR, the unit lie direction in H, §4.4), `hair_grey` (0–1), `hair_zone` (int id). Each field is a smooth function: zone values blended with `smoothstep` over the feather distance, plus 8 % low-frequency noise (Perlin at 25 mm) so no zone reads uniform.

### 4.3 Step 3 — Hairline, ear and nape boundary curves
`Hair.Curve.Hairline` (a Bezier in H through the trichion (0, −88, +92), the two temple corners (±58, −62, +78), down the temple line (±70, −35, +45) to the sideburn bottom (±72, −14, +8); jittered ±1.5 mm at 12 mm wavelength and ±0.5 mm at 3 mm for D8). `Hair.Curve.Ear.L/R` (the ear attachment outline offset 10 mm, from spec 06's ear loop). `Hair.Curve.Nape` through (0, +80, −45), (±35, +72, −30), (±60, +50, −5) joining the ear curves. The scalp region is everything above/behind these curves, tested by signed distance on the mesh surface (geodesic approximated by Euclidean on the fitted frame; adequate at this feather size).

### 4.4 Step 4 — Direction, lift and length fields (`groom.py::scalp_fields()`)
For a root at p (H) with normal n: the **lie direction** d is the unit tangent of the blend of (a) a radial field from the whorl (clockwise spiral: radial vector rotated −20° about n), weight 1 within 25 mm of the whorl decaying to 0 at 60 mm; (b) the zone sweep: Z1 (−0.60, −0.50, +0.60), Z2 (−0.40, 0, +0.90), Z3 back-left quadrant (+0.30, +0.60, +0.70), Z3 elsewhere (−0.20, +0.40, +0.90), Z4/Z5 sides (0, +0.60, −0.80) projected onto the tangent plane, Z6 sideburn (0, 0, −1), Z7/Z8 (0, +0.2, −1); (c) 10 % per-root random rotation (±12°). The **lift** α is the zone value of §3.2 ± 8° per root. The initial strand direction is cos α · d + sin α · n. **Length** L is the zone value with a per-root spread of ±8 % (scissor cut) or ±4 % (clipper cut), and a 3 % population of 1.4 × L "stragglers" only in Z1–Z3.

### 4.5 Step 5 — Guides (`Hair.Scalp.Guides`, hidden)
Poisson-disc sample **1 400 guide roots** on the Z1–Z4 faces (minimum spacing 9 mm top, 12 mm sides) with `groom.py::sample_roots(faces, density_field, min_dist, seed)`: area- and density-weighted face selection, uniform barycentric point, grid-based rejection. Each guide is a 12-point polyline: start at the root along the initial direction; integrate with a "product curve": curvature toward d (the sweep) increasing with arc length so a 44 mm fringe guide leaves at 60° and ends at 40° to the scalp; gravity term 0 (product holds); cluster attraction: for every guide within a primary cluster's base radius, blend its tip toward the cluster apex with weight `0.85 · t^1.6` (t = normalised arc length) and intermediate points by the same law — this gives converging spikes; secondary clumps are 60–80 random attractors (6–8 mm base, apex at 0.9 × local length along the local initial direction) with weight 0.5 · t^1.4. Resample each guide to 8 points by Catmull-Rom. Store as a Curves object `Hair.Scalp.Guides` with `surface = Body.Mesh` for inspection in the Workbench look render; it does not render in Cycles.

### 4.6 Step 6 — Long hair children (`Hair.Scalp.Long`)
Roots: sample **48 000** roots on Z1–Z4 (density field × 0.55, D10; `--full-density` → 88 000), minimum spacing 0.9 mm. For each root find the 3 nearest guides (KD-tree, `scipy` is not available in Blender's Python — use a numpy grid bucket search), weights by inverse distance² normalised. Child curve = Σ wᵢ · (guideᵢ − guideᵢ.root) + root, then **clump** toward the nearest guide: child(t) ← lerp(child(t), guide_nearest(t) + root offset × (1 − t), c(t)) with c(t) = c_root + (c_tip − c_root) · t^1.5, c_root 0.35, c_tip 0.85 in primary clusters, 0.5 in secondary, 0.2 outside; **length** trimmed to the child's own L (resample to 8 points over L); **flyaways**: 5 % of children skip the clump and get noise amplitude × 3. **Radius** attribute: root 0.045 mm → 0.038 at 70 % → point-cut taper to 0.012 at the tip (scissor top, Z1–Z3); Z4 blunt: 0.040 → 0.034. Write `position` (flat), `radius` (POINT), `surface_uv_coordinate` (CURVE, the root's UV, needed by §7), `hair_zone` (CURVE int), `hair_lightness` (CURVE float: 0.10 of curves get 1.0, the rest 0.0, for the 10 % lighter strands), `hair_root_normal`. Then GN modifiers: `Hair Curves Noise` (Factor 0.12, Scale 6 mm, Shape 0.6, Seed from `--seed`, Preserve Length on), `Shrinkwrap Hair Curves` to `Body.Mesh` with 0.4 mm offset (lifts any point that sank into the scalp; [VERIFY: socket identifiers]), `Smooth Hair Curves` iterations 1 (flyaways excluded by the `hair_zone` selection). 48 000 × 8 = 384 000 points.

### 4.7 Step 7 — Short hair (`Hair.Scalp.Short`)
Roots on Z5–Z8 and the baby-hair band at the **real** density (200/cm², 220 occiput; ≈ 36 000 fade/sides + 12 000 occipital/nape + 1 500 baby hairs). Strand = 3 points (root, mid, tip) along cos α · d + sin α · n with the lift of §3.2 and a 10° random cone; length from the field (0.3 → 10 mm); **blunt** radius 0.035 → 0.030 (clipper cut); baby hairs tapered 0.030 → 0.010. No clumping, noise factor 0.05. 49 500 × 3 ≈ 150 000 points. The 0.3–0.5 mm "skin" band exists for V2 only; at V1 it is sub-pixel and the skin shader's mask G (§5.4) carries its look.

### 4.8 Step 8 — Stubble (`Hair.Stubble`)
Roots on `Hair.Region.Beard` at the §3.4 densities (feathered field), minimum spacing 0.8 mm, ≈ **11 500** roots. Lie direction field: cheeks down-and-back toward the gonion (0, +0.5, −0.85 in H, projected); chin straight down (0, 0, −1) with ±15° fan from the midline; under-jaw and neck down and slightly outward; moustache from the philtrum outward-down (±0.7, 0, −0.7) and the lip margin radial. Lift 25–40° (3–4 mm trimmed hair stands) ± 10°. Strand = 4 points: a slight bow (sagitta 0.25 mm) toward d, length by zone ±6 %, radius 0.055 → 0.050 blunt. Attribute `hair_grey` (CURVE float 0/1) drawn per strand against the zone's grey fraction with a 3 mm-correlated noise so grey hairs cluster slightly as real ones do. Modifiers: `Hair Curves Noise` 0.04 at 2 mm (the kink), `Shrinkwrap Hair Curves` 0.2 mm. 46 000 points.

### 4.9 Step 9 — Eyebrows (`Hair.Brow.L`, `Hair.Brow.R`)
Define each brow in a local plane: origin at the medial head, u along the arc through the peak to the tail (a quadratic Bezier through §3.1's three points, 57 mm long), v perpendicular on the skin. Roots: 650 per brow by stratified sampling of the shape polygon (height profile h(u): 9.5 at u 0–6, 8.5 at u 6–38, tapering to 2.5 at u 57), 1 mm minimum spacing in the body, 0.6 mm at the head. Each strand's direction: angle θ(u, v) in the brow plane = 70° − 60° · smoothstep(u/15) for the head, then 10° in the body, then −20° in the tail, plus an edge-interlock term: +12° for roots in the lower 30 % of the height, −12° in the upper 30 %; off-skin lift 12–20°; length by §3.5 ± 10 %; 5 points with a gentle curve (sagitta 0.4 mm) that follows the skin (shrinkwrap 0.25 mm). Radius 0.040 → 0.015. Not mirrored: the two brows are sampled with different seeds (asymmetry); the left brow's tail is 1 mm longer (image: tail at x 843 vs 786 after yaw correction — within noise, tagged E). Attribute `hair_lightness` for the 4 % lighter hairs.

### 4.10 Step 10 — Eyelashes (`Hair.Lash.L.Upper`, `Hair.Lash.L.Lower`, `Hair.Lash.R.*`)
Roots along the lid-margin curves (`Head.Curve.LidMargin.*` from spec 06, or the vertex loop of the margin): upper 120 roots in 4–5 rows jittered across a 0.8 mm band, spacing along the margin denser centrally (a raised-cosine density, 1.7× centre vs ends); lower 60 roots in 2–3 rows. Strand = 6 points along a circular arc of radius 10 mm: leaves the margin perpendicular to the lid plane tilted outward 10°, curving up 25–35° (upper) or down 15–25° (lower); length §3.6; radius 0.050 → 0.010. The medial 15 % of each margin has 40 % density and 6–7 mm lashes. Hidden-root rule: the root sits 0.2 mm inside the margin so no strand floats (shrinkwrap off, `surface_uv_coordinate` set for §7).

### 4.11 Step 11 — LOD sets and visibility
Every Curves object carries a custom property `hair_lod`: `Hair.Scalp.Long` (hero), `Hair.Scalp.Long.LOD1` (every 4th curve, radius × 2.0, for full-body evaluation renders), `Hair.Scalp.Short.LOD1` (every 3rd, radius × 1.7), `Hair.Stubble.LOD1` (every 2nd, radius × 1.4); brows and lashes have no LOD (tiny). `scripts/eval` selects by property: `--lod hero|eval`. Collections: `Hair` (render) with children `Hair.Scalp`, `Hair.Face`; `Hair.Debug` (guides, markers, maps) excluded from render.

### 4.12 Topology and budget (hero set)

| Object | Curves | Points/curve | Points | Radius root → tip (mm) | Cut |
|---|---|---|---|---|---|
| `Hair.Scalp.Guides` (hidden) | 1 400 | 8 | 11 200 | — | — |
| `Hair.Scalp.Long` | 48 000 (88 000 full) | 8 | 384 000 | 0.045 → 0.012 | point-cut |
| `Hair.Scalp.Short` | 49 500 | 3 | 148 500 | 0.035 → 0.030 (baby 0.030 → 0.010) | blunt |
| `Hair.Stubble` | 11 500 | 4 | 46 000 | 0.055 → 0.050 | blunt |
| `Hair.Brow.L/R` | 2 × 650 | 5 | 6 500 | 0.040 → 0.015 | natural |
| `Hair.Lash.*` | 2 × (120 + 60) | 6 | 2 160 | 0.050 → 0.010 | natural |
| **Total rendered** | **≈ 110 900** | | **≈ 587 000** | | |

Cycles curve settings: `shape THICK`, `subdivisions 2` (hero), `RIBBON` + `subdivisions 1` for the eval LOD. Memory is trivial (< 60 MB). Origins: every Curves object's origin at the head frame origin (the tragion midpoint) in world, orientation identity; the data are in world coordinates at rest.

### 4.13 Naming
Objects as in the table; materials `Hair.Mat.Scalp`, `Hair.Mat.Stubble`, `Hair.Mat.Brow`, `Hair.Mat.Lash`; node groups `Hair.NG.Noise`, `Hair.NG.Shrinkwrap`, `Hair.NG.Deform`; images `Hair.Map.Density`, `Hair.Map.Length`, `Hair.Map.Dir`, `Hair.Map.Grey`, `Hair.Masks` (§5.4); curves `Hair.Curve.Hairline`, `Hair.Curve.Nape`, `Hair.Curve.Ear.L/R`; Empties `Hair.Anchor.Whorl`, `Hair.Anchor.Cluster.1–9`.

---

## 5. Materials and textures

### 5.1 `Hair.Mat.Scalp` — Principled Hair BSDF (Cycles, `model = CHIANG`, `parametrization = MELANIN`)

| Input | Value | Note |
|---|---|---|
| Melanin | **0.62** base; × (1 − 0.40 · smoothstep(0.55, 1.0, Intercept)) toward the tip; × 0.52 for `hair_lightness = 1` strands; + Hair Info Random mapped to ±0.06 | root ≈ #3a2a1e, tip ≈ #8a6549, 10 % strands ≈ #a07a5e after calibration |
| Melanin Redness | 0.45 base, 0.60 at the tip and on light strands | warm brown, golden tips |
| Tint | #ffffff | |
| Roughness | **0.32** (clean hair 0.20–0.25; matte clay raises it) | low-moderate sheen, no wet look |
| Radial Roughness | 0.30 | |
| Coat | 0.05 | clay, not pomade |
| IOR | 1.55 | |
| Offset | 2° | cuticle tilt |
| Random Color | 0.08 | per-strand |
| Random Roughness | 0.20 | |
| Model | Chiang (cost); `--huang` switches to Huang with Aspect Ratio 0.80 for the elliptical European cross-section [VERIFY render cost] | |

Hair Info `Intercept` drives the tip lightening; `Random` the per-strand variation; `hair_lightness` is read with an Attribute node (`attribute_type = GEOMETRY`). **Calibration, not eye-balling:** `groom.py::calibrate_melanin(material, target_hex, swatch)` renders a 30 × 30 mm pelt swatch (8 000 strands, 40 mm, same lift as Z2) under the spec 01 look-dev key at 400 px, 32 spp, and bisects the base melanin until the swatch's mid-tone (p50) matches the target (#4f483a lit mid for the scalp, the hero-light check in §8.2 then confirms the ROI means). Expected result 0.55–0.70.

### 5.2 `Hair.Mat.Stubble`
Melanin **0.80**, redness 0.30 (albedo ≈ #3b2a22); `hair_grey = 1` strands: melanin **0.03**, redness 0.5, Tint #d8d0c4 (grey hair is not white: a little yellow); Roughness 0.40 (coarse beard hair, no product), Radial 0.35, Coat 0, Random Color 0.10. No tip lightening (blunt, trimmed). A 2-level ramp on Random gives 15 % of non-grey strands melanin 0.65 (brown-red glints seen in the lit jaw).

### 5.3 `Hair.Mat.Brow` and `Hair.Mat.Lash`
Brow: melanin 0.78, redness 0.30, Roughness 0.30, Coat 0.15 (natural sebum sheen), tip lightening 0.15 only; `hair_lightness` strands melanin 0.55. Lash: melanin 1.0, redness 0.2, Roughness 0.25, Coat 0.2, no variation.

### 5.4 `Hair.Masks` — what the skin shader (spec 06) must consume
A 2048² RGBA image on the head's UV tile (texel density ≥ 3 px/mm over the head island; rasterised by numpy from the per-face fields and the strand roots): **R** = stubble follicle density 0–1 (1 = 55/cm²) for the beard shadow: spec 06 multiplies skin albedo by lerp(1, 0.78, R) toward a cooler hue (#8a6a60 at R 1 under the lit jaw) and adds follicle dots — Voronoi F1 at pitch 1.35 mm (55/cm²) → 1.9 mm (28/cm²), dot radius 0.09 mm, darkening 0.35, bump −0.03 mm; **G** = fade scalp-visibility: the fraction of skin covered by hair shorter than 1.5 mm (0 at the ear top, 0.5 at the #0.5 band, 1 where hair ≥ 3 mm) → spec 06 tints the scalp under the fade with a blue-grey "shaved" cast lerp(skin, #a8847a, 0.35 · (1 − G)) plus follicle dots at pitch 0.7 mm (200/cm²), and keeps the skin's SSS radius 20 % lower there (thin scalp over bone); **B** = grey fraction (debug/colour checks); **A** = lash-line and brow-root darkening (0.6 within 0.6 mm of the lid margins, 0.3 under the brows) and a 0.15 darkening along the hairline's baby-hair band. Written as `Hair.Masks.png` (16-bit) next to the .blend and re-generated on every build.

### 5.5 Texel density and UVs
No image textures are sampled on the strands (all procedural). `Hair.Masks` and the `Hair.Map.*` debug images sit on the head UV island owned by spec 06; this part requires the island to be ≥ 1 024 px across at 2048² (≥ 3.4 px/mm) and non-overlapping over the scalp, face and upper neck (§10.1).

### 5.6 Hex targets (lit, hero lights, for §8.2) 
Hair top mass #352922, fringe #4c372b, right upper side #564134, right temple fade #856856, left side (fill) #3c3636, brows #674435 / #432f26, chin pad #78574a, soul patch #634036, moustache #714f44, right jaw #a67b65, lash line #3b2219, hair top shadow #30241c, hair highlight mean #aa7e6e.

---

## 6. Fibres, simulation or dynamics
Everything in this part is fibre; the construction is §4. **System choice** (research C recommendations): the new **Curves** system for every element — scalp long, scalp short, stubble, brows, lashes — because roots, directions, lengths, radii and per-curve attributes are set exactly from Python and GN modifiers evaluate headless. Legacy particle hair is used only as a **fallback** if the numpy interpolation of §4.6 proves visually inferior: `Hair.Scalp.Guides` becomes a particle system's parents (1 400 hair particles, 8 segments, `child_type INTERPOLATED`, 34 children, clump 0.6 with `clump_shape 0.3`, `roughness_2 0.15` at `roughness_2_size 0.8`, `kink NO`, `radius_scale 1.0e-4`, `root_radius 1.0`, `tip_radius 0.25`), converted with `bpy.ops.curves.convert_from_particle_system()` under `temp_override` (proven headless, research C §3c) so the rest of the pipeline is unchanged. No cloth, no soft body, no dynamics: the hair is product-set and the pose is static; the strands are rigidly attached (§7). Vellus: none (D14). Render dynamics: `use_persistent_data = True` across the six views.

---

## 7. Rigging and attachment
* **Scalp, brows, lashes** ride the skull: each Curves object is parented to `Morgan.Rig` bone `head` (`parent_type = BONE`, matrix_parent_inverse set so the rest build stays in place). The skull does not deform, so this is exact, cheap and export-safe.
* **Stubble** must follow the jaw, cheeks and neck when the face has expression keys (brow-lower, lid-tightener, lips-pressed, jaw-clench of consolidated §2) and when the neck twists 20°: a GN modifier `Hair.NG.Deform` with the built-in **Deform Curves on Surface** node; requirements: `curves.surface = Body.Mesh`, `surface_uv_map = "UVMap"`, the `surface_uv_coordinate` attribute written per curve in §4.8, and a `rest_position` attribute on `Body.Mesh` stored by a Geometry Nodes modifier (`Store Named Attribute rest_position = Position`) placed **first** in the body's modifier stack, before `Armature` (spec 04 §4 stack order becomes: `RestPosition` → `Armature` → `Corrective Smooth` → `Subdivision` → …). [VERIFY: Deform Curves on Surface evaluates headless with a subdivided surface; if the subdivision changes the UV-to-surface mapping, attach to a hidden un-subdivided copy `Hair.Surface` driven by the same armature instead.] Fallback: parent the stubble to `head` as well; the jaw is clenched shut in the hero pose and the error is < 1 mm.
* The neck part of the stubble gradient (S4–S5, below the under-jaw plane) uses the same surface deform, which also follows spec 04's `NeckTwist` corrective.
* Nothing in this part adds bones. The head bone's pose in the hero frame: yaw +20° about world Z (toward his left), pitch 3–5° chin-up relative to the chest (consolidated §2), supplied by spec 08.
* Collision with the gaiter: the stubble's lowest roots (laryngeal prominence) are 15–25 mm below the gaiter's top roll (`Torso.Ring.Gaiter.Top`, front centre posed z 1574, spec 04); strands there are inside the gaiter and are **culled** (`hair_zone` selection → delete) within 2 mm of the gaiter's inner surface when the gaiter exists, to avoid poke-through.

---

## 8. Evaluation protocol

### 8.1 Render sets (`scripts/eval/render_part07.py` → `renders/07_hair/<view>_<look>_<lod>.png`)
* **Look preset (10 s):** Workbench, 720 × 720, matcap + cavity, hair displayed as strands, `Hair.Debug` on: V1, V2, V3; plus `Hair.Map.*` as vertex-colour views (Workbench `color_type VERTEX` on a copy of the head with the fields baked to a colour attribute `Hair.Debug.Color`) to inspect zones before any Cycles render.
* **Form (CPU here):** Cycles 1024², 64 spp, adaptive 0.02, OIDN, spec 01 look-dev key, `Hair.Scalp.Long` hero set: V1–V6. Budget 8–15 min each on this box (head closeup with Random Walk skin ≈ 6–10 min, +50 % for 110 k thick strands; research C). Run one at a time.
* **Colour (hero lights):** V1 at the hero frame (border render, 64 spp) ≈ 1 min; V1 ×8 at 2048², 128 spp, and V4/V5 at 2048² only on the GPU machine (seconds there), or overnight here.
* **Silhouette:** V1 and V3 with `film_transparent`, world black, the alpha saved.
* Contact sheet `renders/07_hair/contact_<seed>.png` of 6 seeds × V3 in Workbench (1 min) for choosing the spike seed before the Cycles run.

### 8.2 Automated metrics (`groom.py::measure_groom() → renders/07_hair/measure.json`)
1. **Counts and densities** per zone from the curve roots (roots / zone area in cm²) against §3.2 and §3.4, ±15 %.
2. **Lengths** per zone (mean, p5, p95) from the point data against §3.2, ±15 %; stubble 3.0 / 4.0 ± 0.3.
3. **Sweep**: fraction of Z1–Z3 strands with mid-length tangent X-component < −0.2 (toward his right) ≥ 0.70; Z1 mean tangent Y-component < −0.3 (forward).
4. **Spike count**: run the §2.2 detector (same code, `measure.py::silhouette_peaks(alpha, win=4, prom=1)`) on the V1 hero-frame alpha upscaled to the reference's pixel grid: expect **8–10**; apex column within ±4 px of 812; lateral cluster present (a peak with prominence ≥ 8 px at x 755–768).
5. **Silhouette IoU** of the head crop against the reference mask (luminance > 28 inside 745–865 × 8–60): ≥ 0.85 for the spike band (y 8–40), ≥ 0.92 for the hair mass (research E §8 item 5).
6. **Colour ROIs** (hero lights, 5 × 5 means or region means at the §2.2 rectangles): ΔE76 < 8 for the hair top mass, < 10 for fringe, upper side, temple fade, brows, chin, soul patch, moustache, jaw; temple-fade luminance 103–123; chin / bare-cheek luminance ratio 0.60–0.70; medium-cheek high-pass (3 px Gaussian high-pass std) ≥ 2 × bare cheek's.
7. **Grey fractions** from `hair_grey`: chin 0.20–0.30, moustache 0.08–0.12, cheeks 0.
8. **Root distance** to the surface (nearest-point query) ≤ 0.3 mm for 99.9 % of roots; **penetration**: fraction of non-root points inside the head mesh < 0.1 %.
9. **Thickness at V1 ×8**: median width of connected bright strand segments 1–3 px; sparkle fraction < 3 %.
10. **Brow geometry** from roots: height profile ±1 mm of §3.5, head separation 20–22 mm, tail drop 3–4 mm; **lash** counts and length percentiles against §3.6.

### 8.3 Critic questions (score 1–10 each; the part passes at ≥ 7 on every question and ≥ 8 average)
1. Count the spikes breaking the silhouette in V1/V3: 8–10, with the tallest near the vertex and one leaning out to his right at the front corner?
2. Does the top read as 35–45 mm hair pushed up and toward his right with a forward-up fringe, or as a cap, a brush, or a mirror image?
3. Is the length gradient believable from top (40) to upper side (10–15) to temple (1–3) to skin at the ear — with no visible clipper step?
4. At the right temple, does scalp show through about half and half, with the skin reading faintly blue-grey where shaved?
5. Is the hairline a soft arch with baby hairs, no peak, no recession, no gap?
6. Colour: medium-dark warm brown roots, golden-brown lit tips, no orange, no black helmet, no grey on the scalp, a few lighter strands?
7. Product: separated matte clumps, dark roots and lit tips, no wet shine, no uniform fuzz?
8. Stubble zones: dense chin/moustache/jaw, medium lower cheek, sparse upper cheek, bare cheekbones; does the chin read salt-and-pepper with countable grey hairs and the cheeks not?
9. Does the stubble end naturally under the jaw onto the neck (no shaved line), at 3–4 mm (not a beard, not a shadow)?
10. Brows: dense, straight, low-set, squared inner heads 2 cm apart, a lateral downward hook, individual hairs in the right directions — nothing floats?
11. Lashes: present, dark, short-looking; not doll lashes, not missing?
12. Any strand through the skin, ear or gaiter; any root floating; any strand thicker than a real hair at V1 ×8?

### 8.4 Known failure modes
Cap/helmet look (density too even, clump 0, no flyaways); spaghetti (radius > 0.08 mm — the research test's 5 mm); sparkle (radius < 0.03 at 64 spp without OIDN); mirrored sweep (toward +X); spikes seed-dependent (fixed by the cluster table; vary only the secondaries); spike apexes merging into a comb (cluster base radius too large or apexes too close); fade with a visible step (zone values not feathered); bald patches in Z5 (Poisson spacing > hair length); roots floating after the Subdivision changes the surface (attach to the evaluated mesh or shrinkwrap 0.4 mm); stubble reading as dirt at hero scale (the mask R in the skin shader is what shows at 120 px head height — if the skin shader ignores it the stubble vanishes in eval renders); grey strands too white or too many (Tint, fractions); brows too thick (the orbit shadow was mis-read as brow); lashes curling up like a doll (lift > 45°); lashes invisible (roots below the margin); Deform Curves on Surface silently doing nothing (missing `rest_position` or `surface_uv_coordinate`); GN socket identifiers wrong (set by identifier, enumerate at run time); MakeHuman proxies left in the file.

---

## 9. Build order, effort and risks

### 9.1 Dependencies
Spec 06 (head mesh with the `Head.Anchor.*` Empties, UV island, lid-margin curves or loops, ear loops, skin shader consuming `Hair.Masks`); spec 04 (`Body.Mesh` modifier stack accepting a `RestPosition` GN modifier first; `Torso.Ring.Gaiter.Top`); spec 08 (head bone pose); spec 10 (gaiter geometry for the cull); spec 17 (hero camera and lights, `scripts/eval`). The part can be developed on the spec 06 head alone with the gaiter absent (then the neck gradient is fully visible in V4 and simply judged against §3.4).

### 9.2 Order inside the script (runtime on 4 cores)
1. Head frame, cleanup (1 s). 2. Regions, fields, boundary curves, debug maps (5–8 s numpy; the UV rasteriser 3 s). 3. Guides (0.5 s). 4. Long children: root sampling 48 k (1 s), interpolation and clumping (2 s), Curves write (0.3 s). 5. Short strands (1 s). 6. Stubble (1 s). 7. Brows, lashes (0.5 s). 8. GN modifiers append + evaluate (1–3 s). 9. Materials and calibration swatch (the swatch render 20–40 s × 4–6 bisection steps ≈ 3 min; cached by target hex in `renders/07_hair/calib.json`). 10. `Hair.Masks` (3 s). 11. Attach to the rig (1 s). 12. Workbench look set (30 s). 13. `measure_groom()` (5 s). 14. Cycles form/colour renders (8–15 min each on this box, run with `--render cycles`; otherwise skipped). Build without renders: **≈ 4 min** including calibration; **< 30 s** with `--no-calib`.

### 9.3 Estimated size
`scripts/parts/07_hair_grooming.py` ≈ 500 lines; `scripts/lib/groom.py` ≈ 600 lines (frame fit, fields, Poisson sampler, guide integrator, interpolation/clump, Curves writer, GN helper, calibration, measure). Data: ≈ 590 k curve points (≈ 15 MB in the .blend), `Hair.Masks.png` 2048² 16-bit (≈ 12 MB, gitignored, regenerated).

### 9.4 Risks and fallbacks

| Risk | Likelihood | Fallback |
|---|---|---|
| The spike silhouette does not match at 8–10 after clustering | medium | tune the §3.3 table (apex heights, base radii) — it is data, not code; contact sheet of seeds for the secondaries |
| Numpy interpolation looks worse than Blender's interpolated children | low–medium | §6 particle fallback + convert |
| `Shrinkwrap Hair Curves` / `Interpolate` socket names differ | medium | enumerate identifiers at run time; shrinkwrap can be done in numpy against the mesh (nearest point) |
| Deform Curves on Surface fails headless or with Subdivision | medium | parent stubble to `head`; error < 1 mm in the hero pose |
| CPU render time for V1 ×8 at 2048² | high here | 1024² 64 spp here; 2048² on the GPU machine; eval LOD for full-body renders |
| Melanin calibration converges to a value whose hero-frame ROI is still off (lighting mismatch) | medium | calibrate under the hero lights directly (same bisection, longer render), then check the look-dev swatch only for sanity |
| Hair reads too dark against the dark hangar (lost silhouette) | medium | the key hits the tips; verify the fringe p95 ≥ 120; add the optional cool kicker (consolidated §8, ≤ 12 % of key) only if the reference's faint rim justifies it |
| Stubble invisible at eval scale | high if spec 06 ignores mask R | spec 06 must consume `Hair.Masks.R` (interface) |
| Brows mis-shaped by a wrong brow-ridge landmark | medium | brows defined relative to `Head.Anchor.Brow.*` which spec 06 places from the image landmarks; re-fit per build |

---

## 10. Interfaces and open questions

### 10.1 What neighbouring parts must provide or respect
* **Spec 06 (head and face)** provides: `Head.Anchor.{Tragion,Orbitale,Superaurale,Gonion}.L/R`, `Head.Anchor.{Trichion,Glabella,Sellion,Vertex,Menton,Opisthocranion}`, `Head.Anchor.Brow.{Head,Peak,Tail}.L/R`, `Head.Curve.LidMargin.{Upper,Lower}.L/R` (or named vertex loops), the ear attachment loops, a non-overlapping head UV island ≥ 1 024 px across at 2048², and the hairline position (trichion 60–65 mm above the glabella, temple corners per §3.1). Its skin shader must read `Hair.Masks` (§5.4): beard shadow and follicle dots from R, shaved-scalp tint and follicles from G, lash-line/brow-root darkening from A; Sheen 0.05 for vellus (D14). It must **not** load MakeHuman hair, eyebrow or eyelash proxies, nor paint brows or stubble into the albedo (they would double up).
* **Spec 04 (torso and neck)** accepts a `RestPosition` GN modifier at the top of `Body.Mesh`'s stack and provides `Torso.Ring.Gaiter.Top`; its `Torso.Masks2.B` "stubble-boundary feather (1 at the hyoid, 0 at 1640)" should be dropped or redefined to match D11 (100 % at the under-jaw plane 1640, 60 % at the hyoid 1622, 0 % at the laryngeal prominence 1590) so the two parts agree.
* **Spec 08 (rig and pose)** poses the `head` bone (yaw +20°, pitch 3–5°) and exposes it for `parent_type BONE`.
* **Spec 10 (shirt and gaiter)** provides the gaiter mesh for the stubble cull; the gaiter's top roll must not intersect the stubble roots above z 1590.
* **Spec 17 (evaluation scene)** provides the hero camera, lights, AgX look and the border-render helper used by V1.
* **Spec 18 (pipeline / game export):** Curves do not export to glTF. Recommended: generate `Hair.Cards` by script — 60–90 quad ribbons along the primary and secondary clump axes (Curve to Mesh with a 12–18 mm wide flat profile) plus a scalp cap at 2 mm offset, bake `Hair.Scalp.Long` alpha/colour/normal onto them (Cycles bake, research C §10c), and a stubble/brow/lash bake into the face albedo (R mask tint plus baked lash strips). Owned by spec 18; this part exports the clump axes as `Hair.Export.ClumpAxes` (a Curves object of 90 curves) to make that possible.

### 10.2 Questions for the client
1. Grey on the chin at 20–30 % (image and age agree) — confirm this salt-and-pepper read is wanted as an identity cue, and that the scalp stays grey-free.
2. Nape and crown are unseen: is the assumed natural (unlined) nape and a clockwise whorl acceptable, or is a blocked/rounded neckline preferred?
3. Game export: hair cards baked from the groom (recommended, ≈ 2 k tris) or a textured scalp cap only? Should stubble, brows and lashes be baked into the face albedo for the game?
4. Density compromise D10 (55 % on top with 1.3 × radius for CPU budget): acceptable for acceptance renders made on the GPU machine, or should those always use `--full-density`?
5. Product finish: matte clay (Roughness 0.32, Coat 0.05) as read, or a touch more sheen?

### 10.3 Items tagged [VERIFY]
Published values for scalp density (150–250/cm²), shaft diameter (70 µm), beard density (25–65/cm²) and growth rates, lash and brow counts, the Wahl guard-to-mm chart, and the "50/50/50" grey rule (§2.4, §3.2–3.6); `Shrinkwrap Hair Curves` / `Smooth Hair Curves` socket identifiers; Deform Curves on Surface headless with Subdivision; Huang model render cost; Workbench strand display of Curves objects headless.
