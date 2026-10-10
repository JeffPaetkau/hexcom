# Part 03 — Leg and pelvis (thigh, knee, shank, pelvis; skin, hair, pose, rig)

Status: draft 1 (spec writer), 2026-10-06. Owner script: `scripts/parts/03_leg_pelvis.py` (plus `scripts/lib/sculpt.py`, `scripts/lib/measure.py` from spec 01, and new `scripts/lib/proportions.py`, `scripts/lib/corrective.py`, `scripts/lib/weights.py`). Object prefix `Leg.<L|R>.*`, `Pelvis.*`; shape keys `Leg.*`; vertex groups `Leg.*`, `Pelvis.*`.

Conventions (`CLAUDE.md`): millimetres in this spec, metres in Blender; world origin on the floor midway between the feet, +Z up, the character faces −Y (camera on −Y), **+X = the soldier's LEFT = viewer's right**. Every left/right is the soldier's own. Heights are written `h` (mm above the floor). Reference pixels are full-image coordinates of `ref/reference_full.png` (1672 × 941) at the agreed scale **2.119 mm/px** (4.72 px/cm), floor datum y = 895, lateral origin x = 830 (midway between the ankles 732 and 928), so `h = (895 − y) × 2.119` and `X = (x − 830) × 2.119`. Tables of leg anatomy are given for the **LEFT leg in the rest (A-)pose** in a leg frame **G**: origin at the left hip joint centre projected to the floor, X lateral (+ = lateral for the left leg), Y anterior = −, Z = h; the right leg is `mirror(X)`. Real-world numbers are ANSUR II "Tight" means (30 men 1830–1870 mm, 82–85 kg; `notes/research_dimensions.md` §1) scaled ×1.0049 to 1855 mm and marked **S** (sourced), **M** (measured in the image), or **E** (estimated, with the reasoning).

---

## 1. Purpose and acceptance

### 1.1 What this part is
Everything of the body between the sock cuff (z 300, where spec 01 stops) and the iliac crests (h 1031 in rest): the pelvis with its bony landmarks and gluteal mass, both thighs, both knees, both shanks down to the blend band with the foot part; the segment proportions (hip, crotch, knee heights) of the whole character; the skin material of the legs and pelvis; the leg hair; the leg and pelvis deformation bones, weights, twist split and corrective shape keys; the hero pose of the lower body (pelvis placement, hip, knee and shank angles); and the helper objects the trousers (spec 09), kneepads (spec 12), belt and drop-leg rigs, and boots attach to or must clear. In the hero render nothing of this skin is visible; it is built because the trousers are a cloth simulation over this body, the knee pockets and kneepad caps sit on these knees, the belt and thigh straps compress this flesh, the game rig bends here, and because the client requires every part to be right in itself.

### 1.2 What "perfect" looks like
A critic who knows legs, looking at a 2048 px bare-leg render, sees a lean 40-year-old athletic man of 1855 mm: a kneecap with a visible upper pole and apex, condyles wider than the patella, the patellar ligament as a flat band to a tibial tuberosity that is a bump, the sharp subcutaneous shin bone spiralling medially toward the ankle, a tibialis anterior cord lateral of it, a two-headed calf whose medial head sits lower, hamstring tendons framing a diamond popliteal fossa, a teardrop VMO above the medial knee, a flat lateral thigh under the iliotibial band, the sartorius groove from hip to inner knee, a trochanteric dimple, a gluteal fold that fades laterally, iliac crests you could rest your hands on; skin that is paler than the face, thicker and rougher over the knees, shinier over the shin, with sparse dark hair lying downward, and a green-grey saphenous vein tracing the inner shank. In the posed clothed render the trousers hang from a body whose knees are exactly under the kneepad caps and whose crotch sits exactly as high as the drawing's, with no limb intersecting cloth or gear. Nothing tubular, nothing symmetric to the millimetre, nothing waxy.

### 1.3 Closeup render views (definitions for the render harness in §8.1)
Rest-pose anatomy views use the look-dev scene A (spec 01 §8.1: neutral grey, three area lights, AgX Base Contrast). Posed views use the hero scene B. 2048² unless stated.

| View | Camera position (world, mm) | Target (mm) | Lens | Compared with |
|---|---|---|---|---|
| V1 `knee_front_L` (rest, bare) | (+95, −900, 520) | (+93, 0, 520) | 85 mm | §3.3 knee table; overlay of the left kneepad cap outline from `ref/zoom_leg03_lknee_x6.png` (862–940 × 610–700) scaled 2.119 mm/px and centred on the patella |
| V2 `knee_lateral_R` (rest, bare) | (−1000, −120, 520) looking +X | (−93, 0, 520) | 85 mm | §3.3 side profile: patella prominence, tuberosity, fibular head, popliteal tendons; `ref/zoom_leg03_rknee_x6.png` for the oblique cap footprint |
| V3 `pelvis_thighs_front` (rest, bare) | (0, −1700, 790) | (0, 0, 790) | 50 mm | §3.2 pelvis and §3.4 thigh tables: ASIS, inguinal groove, sartorius, rectus, VMO, trochanter hollow; envelope check against `ref/zoom_leg03_pelvis_thighs_x4.png` (crotch apex (810,535), hip width 350 at y 500) |
| V4 `shank_front_L` + `calf_back_L` (rest, bare) | (+100, −900, 330) and (+100, +900, 330) | (+100, 0, 330) | 85 mm | §3.5 shank table: tibial crest, tibialis anterior, calf heads, soleus, peroneals, saphenous vein |
| V5 `legs_hero_posed` | hero camera (0, −4500, 600), rot (93.9°, 0, 0), 1024 × 1536 | — | 46 mm | `ref/crop_legs_knees.png`, `ref/crop_belt_hips.png`: the bare posed body rendered with the trouser silhouette mask of the reference as an overlay; patella centres must land on the kneepad cap centres (727,657) / (901,655) ± 6 px; crotch and hip envelope inside the trouser silhouette |
| V6 `knee_skin_macro_R` (posed, hero lights) | 350 mm in front of the right patella along its facing direction (§7.4), 1024² | right patella centre | 100 mm, f/8 DOF | §5 skin tables: knee callus, transverse creases, follicle pits, hair, vein; no reference crop |

### 1.4 Pass criteria a critic can score (full list in §8.3)
1. Every height and girth in the automated `measure_leg()` report (§8.2) is within tolerance of §3: joint heights ±5 mm, landmark heights ±6 mm, girths ±8 mm, widths ±4 mm, bony prominences ±1 mm of their stated proudness.
2. Rest hip joint centres at h 851 ± 5, knee axes at 526 ± 4, patella centres 521 ± 4, perineum 801 ± 6, ankle axes 80 (foot spec). Posed hip centres 829 ± 8 and right/left patella centres at h 505/510 ± 8 (V5).
3. V5 overlay: the bare body silhouette lies inside the reference trouser silhouette everywhere by ≥ 12 mm, except under the three thigh straps and the belt where the clearance is 3 mm (the cloth is pulled to the body there).
4. Knee reads as patella + condyles + ligament + tuberosity + tendons (six distinct forms) in V1 and V2, not as a smooth hinge.
5. Shank shows the tibial crest as a ridge that catches the key light along its whole length and twists medially toward the ankle; calf max girth 390 ± 8 at h 365 ± 10; medial gastrocnemius head reaching 20 ± 5 mm lower than the lateral.
6. Thigh shows rectus femoris, vastus lateralis, VMO teardrop, sartorius groove and the flat IT-band strip as separate forms; adductor mass medial; hamstring mass posterior with two tendon cords at the knee.
7. Pelvis: ASIS, iliac crest, trochanteric depression, gluteal fold and sacral dimples (PSIS) all present; hip breadth 345 ± 5 at the trochanters; bicristale 281 ± 5.
8. Skin: legs paler and less red than the face (ΔL* +4 to +6 against the face swatch under scene A); knee skin darker and rougher (roughness 0.60 vs 0.48) with 3–5 transverse creases above the patella in extension; shin roughness 0.42 with a soft sheen; vein relief 0.6 mm and green-grey tint on the medial shank; no glow (shadow side ≥ 1.5 stops darker than the lit side).
9. Hair: 11,000–14,000 terminal hairs per leg, densest on the anterolateral shin, 30 % density in the sock band z 90–260, radius 0.03–0.04 mm, dark brown, lying distally; vellus hair present but only visible in rim light.
10. Pose: right knee flexion 15–20°, left 8–10°; right thigh facing 45 ± 5° to his right of the camera axis, right foot 90 ± 5°; left thigh 12 ± 5° to his left; pelvis yaw −10 ± 3°, pelvis centre at X −40 ± 10; no candy-wrapper collapse at the right hip (thigh girth at h 760 posed within 3 % of rest) and no knee volume loss > 4 % at 17°.
11. Game rig test: both knees flex 0 → 130° and both hips 0 → 90° flexion / 0 → 45° external rotation with the correctives driving; popliteal self-intersection ≤ 2 mm at 130°, calf-thigh contact bulge present at > 110°.

---

## 2. Reference observations

### 2.1 What the image shows about this part
The legs are inside loose camouflage trousers, the pelvis under the trousers, belt and two drop-leg rigs. The image constrains the body only through landmark heights, the clothed silhouette, the kneepad positions and the stance.

| Observation | Pixels | Derived (mm) | Source |
|---|---|---|---|
| Right sole (floor datum) / left sole | y 895 / 907 | left foot 150 mm nearer the camera | consolidated "Agreed scale"; spec 01 |
| Right / left ankle (boot break) | (732, 855) / (928, 858) | ankle axis h 80 at X ∓208 | spec 01 §2 |
| Right / left knee ("knee centre" = kneepad centre) | (727, 650) / (890, 657) | h 519 / 504 at X −218 / +127 | consolidated vertical landmarks; §2.2 refines to the cap centres |
| Right kneepad cap | x 695–760, y 615–700 | 138 × 180 projected, centre (727.5, 657.5) → **h 503, X −217**; seen 45° oblique | consolidated §5; `ref/zoom_leg03_rknee_x6.png` |
| Left kneepad cap | x 862–940, y 610–700 | 165 × 190 projected (frontal), centre (901, 655) → **h 508, X +150**; the cap's centre is 23 mm lateral of the analysts' knee centre because the cap and pocket sit slightly lateral on the frontal knee | `ref/zoom_leg03_lknee_x6.png` |
| Crotch apex (trouser) | (810, 535) ± 5 | **h 763, X −42** | consolidated; spec 09 §2 confirms by brightened zoom |
| Hip joints (est., hidden) | y 505, x 768 / 862 | h 826; X −131 / +68 | consolidated (low confidence, ±8 px) |
| Belt | y 490–512 | h 858–812 (46 mm tall) | consolidated §6 |
| Trouser waistband top | y ≈ 475 | h 890 | spec 09 |
| Waist under the vest (body + shirt) | y 470, x 745–890 | 307 wide at h 900 | consolidated horizontal landmarks |
| Hips (clothed body, no rigs) | y 500, x 735–900 | 350 wide at h 837, centred X −27 | consolidated |
| Right thigh clothed | y 600, x 696–780 | 178 wide at h 625, centre X −195 | spec 09 §2 |
| Left thigh clothed | y 600, x 846–930 | 178 wide (≈171 corrected for the nearer depth), centre X +123 | spec 09 §2 |
| Inner-thigh gap | y 560: x 792–828; y 600: x 780–835 | 76 mm at h 710; 117 mm at h 625 | spec 09 §2 |
| Knee pocket top seam | R y 578–586, L y 575–585 | h 672–655 | spec 09 §2 |
| Knee pocket (black) | R x 690–770, y 603–712; L x 860–945, y 605–712 | h 619 → 388 | spec 09 §2 |
| Upper right thigh strap / lower right / lower left | y 520–536 / 565–588 / 560–580 | h 795–761 / 700–651 / 710–668 | consolidated §6, spec 09 |
| Boot collar top | y 795–800 | h 212–201 | consolidated |
| Stance | ankle-to-ankle 196 px, knee-to-knee 163 px, heel-to-heel 145 px | 416 / 346 / 308 | pose note §6 |
| Weight | centre-line x ≈ 812 between ankles 732 / 928 | 55 % right | pose note §6 |
| Pelvis / thigh / knee / foot rotations | — | pelvis yaw −10°; R hip flex −5, abd +14, ext-rot 45, R knee flex 15–20, tibial ext-rot 20, foot 90° to his right; L hip flex +8, abd +10, ext-rot 22, L knee flex 8–10, foot 15–20° to his left | consolidated §1 rotations; pose note §6 |

### 2.2 My own measurements and colours (`ref/zoom_leg03_*.png`, made with PIL from `reference_full.png`)
* **Cap centres, not analysts' knee centres, are the knee datum.** In `zoom_leg03_rknee_x6.png` the right cap spans y 615–700 (centre 657.5) and the pocket's top roll is at y 600–612; in `zoom_leg03_lknee_x6.png` the left cap spans 610–700 (centre 655). A hard cap sits centred on the patella (its foam pocket is symmetric about the kneecap), so the **posed patella centres are at h 503 (R) and 508 (L)** ± 8. The analysts' y 650 / 657 "knee centres" are 7 px (15 mm) above the cap centres on the right and coincide on the left; the difference is within their ±8 px but the cap centre is the thing a critic will overlay, so it is the datum.
* **Knee pocket roll above the cap** (y 600–612 R, 598–610 L) is 25 mm of bunched Cordura: the pocket top seam at h 665 is 140 mm above the knee axis, on the lower thigh where the vasti taper into the quadriceps tendon. The body there is 130 mm wide (lower-thigh girth 404); the pocket is 175 wide.
* **Thigh direction.** The right thigh's lit lateral strip (x 696–720, tan blotches) and shadowed medial half show the right leg turned ≈ 45° to his right; the strap ladder-locks at (733, 527) and (733, 567) sit on the front of the rotated thigh, i.e. 45° round from the camera-facing side. The left thigh is lit cool and flat: frontal.
* **Crotch.** The dark diamond at (780–840, 540–600) is background between the thighs (spec 09 §2.9). The inner-thigh gap of 76 mm at h 710 is cloth-to-cloth; with 16 mm of cloth and gap each side the bare inner thighs are ≈ 110 mm apart there, i.e. the thighs diverge from a perineum at X −42.
* **Pelvis shift.** CF seam x 810, crotch 810, face midline 817: the body midline is at X −40 ± 5 (55 % weight on the right foot). The hips' clothed centre X −27 at h 837 differs by 13 mm because the left drop-leg hanger and pouch widen the left side.
* **Colour samples** (5 × 5 means; matter only to the trousers, listed so the leg skin is never mistaken for them): R thigh front shadow (745,560) #191919; R thigh outer lit (705,575) #050403 (a near-black blotch); L thigh front cool (880,555) #3c4145; crotch apex (810,535) #1c2023 (background); R knee sleeve (760,660) #0f0e0f; L knee sleeve (868,665) #1a1a15; R shin (735,740) #1d1d1c; L shin (890,740) #302c29; L shin cool edge (930,720) #313840; floor beside the right knee (690,700) #202428.

### 2.3 Ambiguities and decisions
1. **Crotch height 0.41 H.** Trouser crotch apex at h 763 against an anatomical 902 (S). The knee (M 519 posed) matches ANSUR (526 rest), the ankle matches, so the whole shortfall is thigh length and the pelvis sits 100–140 mm lower than a real 1855 mm man's. Decision in §3.1: build as drawn with a kinematic closure (rest hip centre h 851, posed 829), not the normalised fallback. Reason: the visible evidence (crotch apex, belt at the trochanters, cap heights, inner-thigh gap) cannot be matched by a normal pelvis without a 140 mm drop-crotch, which the gusset folds in the image do not show.
2. **Hip joint lateral spacing.** Image estimate 199 (low confidence) vs anatomical 176 (E, Bell: 14 % of inter-ASIS medial to each ASIS, inter-ASIS 240). Adopt **176**; the posed hips then project at X −127 / +47 against the analysts' −131 / +68 — within their uncertainty.
3. **Knee facing.** Hip ext-rot 45° relative to a pelvis yawed −10° gives a thigh facing 55° to his right of the camera axis; the projected cap width (138 vs a 165 frontal cap) argues 40–45°. Adopt **45° world** for the right knee's facing direction and let the IK solve report the hip rotation (expected 35–40° relative to the pelvis); the foot heading stays 90°.
4. **Left knee lateral offset.** Cap centre X +150 vs the analysts' knee centre +127; the knee pocket is sewn slightly lateral on G3 trousers and the cap lies in it. Adopt the **patella at X +135 ± 8 posed**; the kneepad spec offsets the cap +15 lateral in the pocket.
5. **Genitals.** No bulge is visible (the fly region at (810, 500–535) is flat dark cloth). The base mesh keeps MakeHuman's smoothed groin; no genital asset. Client question §10.2.
6. **Leg skin tone.** Not visible. Decision: lighter and less ruddy than the face albedo #b98670 (face is wind-burnt; legs are always covered): base **#c39a80**, with regional tints §5.1.

---

## 3. Real-world reference

### 3.1 Segment proportions — the decision

> **2026-10-10, Jeff (spec 01 §10.2 Q7, Q9):** the figure matches the drawing. The rest stature is **1835 mm** barefoot (the drawn posed skull top 1855 above the floor, less the boots' 42 mm footbed lift, plus the pose's 22 mm), not 1855; ANSUR segment proportions still hold, scaled to 1835. The build follows the drawing's lean V-taper, not ANSUR's 83 kg man: girths are fitted to the drawing where it shows them, and the mass is an outcome. Revise this section's figures when part 03 is built.
ANSUR II Tight scaled to 1855 mm, against the drawing:

| Landmark (height above floor) | ANSUR Tight ×1.0049 (S) | Drawing (M, posed) | Adopted REST (this spec) | Adopted POSED (expected) |
|---|---|---|---|---|
| Stature | 1855 | 1855 | 1855 | — |
| Iliocristale (iliac crest top) | 1133 | hidden | **1031** | 1009 |
| ASIS | ≈1090 (E: crest −43) | hidden | **988** | 966 |
| Trochanterion (greater trochanter tip) | 963 | hidden | **861** | 839 |
| Hip joint centre (femoral head) | ≈953 (E: tip −10) | 826 ± 17 | **851** | **829** |
| Pubic symphysis top | ≈990 (E) | hidden | **888** | 866 |
| Buttock (max posterior point) | 944 | hidden | 842 | 820 |
| Perineum / body crotch | 902 | trouser apex 763 | **801** | **779** (trouser apex 763 = 16 mm drop) |
| Ischial tuberosity | ≈905 (E) | — | 805 | 783 |
| Gluteal fold (medial end) | ≈895 (E) | — | 795 | 773 |
| Knee flexion axis (lateral epicondyle) | 526 | — | **526** | R 516, L 519 |
| Patella centre (mid-patella) | 520 | cap centres 503 / 508 | **521** | **R 505, L 510** |
| Tibiale (joint line, medial tibial condyle) | 500 | — | 500 | — |
| Tibial tuberosity (centre) | ≈465 (E: joint line −35) | — | 465 | — |
| Fibular head (top) | ≈485 (E) | — | 485 | — |
| Calf maximum girth | ≈365 (E: 35 % down the shank) | — | 365 | — |
| Ankle axis (talocrural, spec 01) | 80 | 85 | **80** | 80 |

**Decision.** Rest femur (hip centre to knee axis) **325 mm**, 74 % of the anatomical 437; shank (knee axis to ankle axis) **446 mm** as ANSUR; rest hip joint centres at h 851 ± 5, X ±88; rest perineum 801. This is "build as drawn" (consolidated §1): the posed hip lands at 829 against the analysts' 826 ± 17 estimate. The value 325 rather than the naive 826 − 519 = 307 comes from the pose closure: with the right thigh abducted 16° and the knee flexed 17° the shank's vertical drop is 436 and the thigh's 311, so the posed hip is 829 only if the rest femur is 325 (§7.3 verifies this numerically before anything is built; if the solve disagrees by > 6 mm the femur constant `FEMUR_MM` is re-solved, never the knee or ankle). The torso above the crest is made longer by the same 102 mm (torso spec) so the stature, shoulder (1521) and chin heights stay as measured. The fallback `HIP_H_REST = 880` (femur 354) is kept as a one-line parameter for the rigger; it is not the default.

How the base mesh gets there (§4.2): MPFB macro targets set the overall body; `measure-upperleg-height-decr`, `upperlegs-height-decr`, `hip-trans-down`, `measure-waisttohip-dist-incr` and `measure-napetowaist-dist-incr` move the pelvis down and lengthen the torso; the residual is closed by a scripted piecewise-linear z-remap shape key `Leg.Proportion` (numpy on the evaluated coordinates, identical for body and helper geometry so the rig fit follows). Per-unit gains of the measure targets are unknown [VERIFY: research_generators has no gain table]; the script measures and iterates (secant, ≤ 6 passes).

### 3.2 Pelvis (rest, world frame, pelvis centred at X 0; left side listed, right mirrored)

| Landmark / component | Position (X, Y, Z) mm | Size / form | Proud or deep | Tag |
|---|---|---|---|---|
| Iliac crest, highest point | (+140, +10, 1031) | ridge 20 wide, from ASIS to PSIS, convex laterally | palpable ridge 2 mm under thin flank fat | S (bicristale 281) / E (Y) |
| ASIS | (+120, −72, 988) | blunt point 15 mm | 3 mm | E (inter-ASIS 240 = bicristale − 41) |
| PSIS (sacral dimple) | (+42, +85, 1000) | dimple 12 mm Ø | 3 mm deep | E (typical 80–90 mm apart) |
| Pubic symphysis, top edge | (0, −85, 888) | horizontal 40 wide | flush, under the mons fat | E |
| Pubic tubercle | (+22, −84, 884) | 8 mm | 1.5 mm | E |
| Greater trochanter, tip | (+165, 0, 861) | 35 × 45 mm | the soft lateral point is at (+172, +5, 845) → hip breadth 345 | S (hip breadth) / E (bone) |
| Trochanteric depression | (+166, +14, 850) | 35 mm Ø hollow behind and below the tip | 4 mm deep (lean man, gluteus medius above it) | E |
| Ischial tuberosity | (+55, +40, 805) | 30 × 40 mm, covered by glute max in standing | not visible standing | E |
| Coccyx tip | (0, +62, 872) | — | in the natal cleft | E |
| Buttock, max posterior | (+85, +148, 842) | — | buttock depth 233 from the pubic front at −85 | S |
| Gluteal fold | medial end (+35, +120, 795) → lateral end (+120, +105, 812) | crease 110 long | 3 mm deep medially fading to 0 laterally | E |
| Natal cleft | (0, +100 → +140, 790 → 900) | — | 12 mm deep at the top | E |
| Inguinal groove | ASIS (+120, −72, 988) → pubic tubercle (+22, −84, 884) | straight line | 2 mm deep, 8 wide | E |
| Mons / lower abdomen front | (0, −95, 920) | — | flush | E |
| Pelvic tilt | anterior tilt 12° (ASIS 157 mm in front of and 12 mm below the PSIS) | baked into the base mesh; the pose adds +2° | — | E |
| Bicristale breadth | 281 | — | — | S |
| Hip breadth (soft, trochanters) | 345 | — | — | S |
| Buttock circumference (at h 842) | 999 | — | — | S |
| Waist circumference at the crest | ≈ 880 (E: ANSUR waist 893 is at the navel, ours is above the crest) | — | — | E |

Note on the belt: posed, the belt (h 812–859) wraps the trochanters (839) and the pubic symphysis top (866) sits 7 mm above the belt's upper edge — the trousers are worn low on the hips. The ASIS (966) is 76 mm above the waistband top (890).

### 3.3 Knee (left, leg frame G: X lateral+, Y anterior−, Z = h; hip centre at (88, 0, 851), knee axis at (93, 0, 526), ankle axis at (100, 0, 80))

| Structure | Position / extent (mm) | Dimensions | Relief | Tag |
|---|---|---|---|---|
| Femoral condyles (soft) | axis (93, 0, 526); bicondylar width 96 | medial condyle 2 mm lower and 6 mm further back than the lateral | define the knee's width | S (knee width E from lower-thigh girth 404 → Ø 129 incl. muscle; bone 85) |
| Medial epicondyle | (93 − 48, +2, 525) | 20 mm | 2.5 mm | E |
| Lateral epicondyle | (93 + 48, −2, 527) | 18 mm | 2.0 mm | S (ANSUR height) |
| Patella | centre (93, −44, 521); anterior face at Y −55 | 45 wide × 50 tall × 22 thick; base (upper pole) at 546, apex at 496 | 8 mm proud of the condyle plane; its outline readable, lateral facet larger | E (adult male patella 40–47 × 45–55 × 20–25) |
| Quadriceps tendon | (93, −50, 546 → 600) | 30 wide × 54 long × 6 thick | 2 mm ridge above the patella base | E |
| Patellar ligament | (93 + 3, −50, 496 → 465) | 25 wide × 45 long × 5 thick | flat band 2 mm proud; the two infrapatellar fat pads bulge 3 mm either side at h 490 | E |
| Tibial tuberosity | centre (95, −46, 465) | 22 wide × 28 tall | 4 mm bump, the lowest point of the "kneeling triangle" | E |
| Tibial plateau / joint line | h 500 | medial condyle flare at (93 − 44, −5, 500) | 1.5 mm shelf | S (tibiale) |
| Fibular head | (93 + 42, +12, 485) top | 20 × 22 | 3 mm | E |
| Gerdy's tubercle (IT band insertion) | (93 + 35, −25, 490) | 12 | 1.5 mm | E |
| Popliteal fossa | centre (93, +52, 530) | diamond 60 wide × 90 tall | 6 mm deep in extension, 10 mm at 17° flexion | E |
| Biceps femoris tendon (lateral border) | (93 + 35, +45, 560) → fibular head | cord 12 wide | 3 mm | E |
| Semitendinosus tendon (medial border) | (93 − 32, +50, 560) → (93 − 40, +15, 500) | cord 8 wide | 3 mm | E |
| Semimembranosus | just lateral-deep of semitendinosus | 20 wide | 1.5 mm | E |
| Gastrocnemius heads (upper edge) | lateral (93 + 25, +45, 505), medial (93 − 28, +48, 500) | — | start the calf below the fossa | E |
| VMO (vastus medialis obliquus) | teardrop centre (93 − 40, −35, 575), apex at h 540 beside the medial patella | 55 wide × 70 tall | 7 mm proud | E |
| Vastus lateralis lower edge | (93 + 50, −20, 565) | fades into the IT band | 4 mm | E |
| Knee circumference at the patella centre | 390 | — | — | E (ANSUR has none; lower thigh 404 above it) |
| Knee circumference at the joint line | 380 | — | — | E |
| Knee front patch the cap sits on (through the pocket) | 96 wide × 60 tall at h 491–551 | transverse radius ≈ 55, vertical radius ≈ 90; the pocket adds 28 mm | → `Leg.L.KneeFootprint` §4.9 | E |
| Transverse skin creases (extension only) | h 548–572, 3–5 lines | 4–6 mm apart, 30–45 mm long, 0.3 mm deep | flatten at > 30° flexion (driver §7.5) | E |

Right knee: mirror, posed facing 45° to his right; its patella centre lands at (X −217, h 505) in world; left patella at (+135, 510).

### 3.4 Thigh (left, frame G)

| Structure | Centre / line (mm) | Size | Relief / role | Tag |
|---|---|---|---|---|
| Femur, mechanical axis | (88, 0, 851) → (93, 0, 526), 325 long | — | the thigh's core; shaft bows 4 mm anterior at mid-length | decision §3.1 |
| Upper thigh circumference (gluteal fold level, h 795) | 603 | Ø ≈ 192 | — | S |
| Mid-thigh circumference (h 660) | 540 | — | — | E (linear taper) |
| Lower thigh circumference (h 600, 75 above the patella) | 404 | Ø ≈ 129 | the knee-pocket top seam (h 665) sits where the girth is ≈ 460 | S |
| Thigh clearance (seated thickness) | 176 | — | AP depth of the thigh at h 795 ≈ 175 | S |
| Rectus femoris | belly (90, −62, 700), from (88, −60, 820) to the quadriceps tendon at 600 | 55 wide at h 700, tapering to 30 | 6 mm proud of the vasti; the "central ridge" of the front thigh | E |
| Vastus lateralis | belly (88 + 75, −10, 650) | 90 wide × 250 tall (h 800 → 560) | the lateral bulge, 8 mm beyond the IT band plane | E |
| Vastus medialis (long head) | (88 − 55, −30, 700) | 70 wide × 200 tall | 4 mm | E |
| VMO | see §3.3 | | | |
| Sartorius | groove from the ASIS (88 + 32, −72, 988) spiralling medially to (93 − 45, −10, 520) | 10 wide | 2 mm deep groove between quads and adductors (lean man) | E |
| Adductor mass (longus, magnus, gracilis) | (88 − 65, 0, 760) | 110 tall × 90 wide | 6 mm; makes the inner-thigh contour from the perineum to the VMO | E |
| Gracilis tendon | (93 − 40, +20, 560 → 500) | 6 wide | 1.5 mm | E |
| Hamstrings (biceps femoris long head, semitendinosus, semimembranosus) | from the ischial tuberosity (88 − 33, +40, 805) to the knee tendons | 120 wide at h 700 | 5 mm posterior bulge, the "back of the thigh" | E |
| Iliotibial band | flat strip from (88 + 78, +5, 845) to Gerdy's tubercle | 35 wide | 1 mm recessed versus vastus lateralis | E |
| Tensor fasciae latae | (88 + 70, −45, 900) | 40 wide × 90 tall | 4 mm | E |
| Gluteus medius | (88 + 60, +20, 920) | 70 × 80 | 3 mm | E |
| Gluteus maximus | (88 − 10, +85, 860) | — | the buttock; max posterior +148 (§3.2) | S |
| Great saphenous vein (thigh part) | from the medial knee (93 − 50, +5, 530) up the medial thigh to the saphenous opening (88 − 60, −70, 830) | Ø 4 mm | 0.5 mm relief, tint §5.2; fades under thigh fat above h 700 | E |
| Hip crease (inguinal) | §3.2 | | forms a fold only at flexion > 45° (corrective §7.5) | E |

### 3.5 Shank (left, frame G; the foot spec owns z < 300; blend band 300–340)

| Structure | Line / centre (mm) | Size | Relief | Tag |
|---|---|---|---|---|
| Tibia, anteromedial subcutaneous face | from the tuberosity (95, −46, 465) to the medial malleolus region (100 − 39, −73, 90, spec 01) | face 30 wide at the top, 20 at z 300 | flat, 0.5 mm below the skin plane of the crest | E |
| Tibial crest (anterior border) | (96, −44, 455) → (90, −40, 300) → spirals medially to (82, −40, 150) | sharp ridge | 1.0 mm ridge, catches light along its length | E |
| Tibialis anterior | belly (93 + 22, −36, 440) → tendon (93 + 8, −46, 200) | 40 wide at h 420, 15 at 250 | 4 mm proud at the belly, 1.5 at the tendon | E (spec 01 continues the tendon to the foot) |
| Extensor digitorum longus / peroneus tertius | lateral of tibialis anterior, (93 + 40, −25, 400 → 150) | 25 wide | 2 mm | E |
| Peroneus longus / brevis | lateral, from the fibular head (93 + 42, +12, 485) to the lateral malleolus (100 + 39, −60, 77) | 28 wide | 2.5 mm; the lateral shank's convex line | E |
| Gastrocnemius, medial head | belly (93 − 25, +42, 390); lower edge h 300 | 70 wide × 190 tall | the bigger head, 10 mm beyond the soleus | E |
| Gastrocnemius, lateral head | belly (93 + 22, +38, 400); lower edge h 320 | 60 wide × 170 tall | 8 mm | E |
| Soleus | flanks either side of the Achilles from h 330 down to 180 | — | 3 mm; makes the calf's lower taper | E |
| Achilles tendon | from h 300 (hand-over to spec 01 at z 100: 16 × 7 cord) | 14 wide at z 300 | 2 mm cord | spec 01 |
| Great saphenous vein (shank part) | from in front of the medial malleolus (spec 01) up behind the medial tibial border (100 − 42, −10, 150) → (93 − 45, +5, 480) | Ø 3–3.5 mm | 0.7 mm relief, tint §5.2 | E |
| Calf maximum circumference | 390 at h 365 | — | — | S (386) → 390 rounded with muscle 0.7 |
| Circumference at h 440 (below the tuberosity) | 370 | | | E |
| Circumference at h 330 (foot-spec sock interface) | 385 | | spec 01 asked 400–420; see §10.1 | E |
| Circumference at h 300 (hand-over) | 365 | | | E |
| Circumference at h 260 (sock cuff) | 335 | | | E |
| Circumference at h 210 (boot collar top) | 290 | | | E |
| Minimum circumference at h 115 | 236 | | spec 01 | S |
| Shank length (knee axis → ankle axis) | 446 | | | S |

### 3.6 Skin, hair and surface (sourced where a figure exists, else E)

| Item | Value | Tag |
|---|---|---|
| Epidermis + dermis thickness: thigh / shin / knee / popliteal / buttock | 1.8 / 1.3 / 2.6 (thickened) / 1.0 / 2.2 mm | E (dermis 1–3 mm, thickest over pressure areas) |
| Subcutaneous fat: anterior thigh / lateral thigh / calf / shin / knee / buttock | 8 / 10 / 7 / 2 / 3 / 18 mm (lean, weight macro 0.45) | E |
| Terminal hair density: anterolateral shin / medial shin / calf / anterior thigh / lateral thigh / medial & posterior thigh / buttock | 12 / 6 / 4 / 5 / 3 / 1.5 / 0.5 per cm² | E (male lower leg 5–20/cm² reported ranges) |
| Terminal hair length: shin / calf / thigh | 12–22 / 10–18 / 8–16 mm | E |
| Terminal hair shaft radius / colour | 0.030–0.040 mm; melanin 0.75, redness 0.3 (dark brown #2a1b12 equivalent) | E; hair matches the head's dark brown (face note) |
| Hair direction | shin: distal and 15° lateral; calf: distal; thigh: distal and 10° medial; all lying within 20° of the skin | E |
| Vellus hair | 30/cm² everywhere, 1.5–2.5 mm, radius 0.012, pale #c8b4a0 | E |
| Follicle pits | 1 per terminal hair plus 1.6 mm mean spacing on the thigh (Voronoi), 0.08 mm deep, 0.35 mm Ø | E |
| Skin lines (micro cross-hatch) | 0.4–0.6 mm pitch, 0.03 mm deep, two directions at ±35° to the limb axis | E |
| Knee creases (extension) | 3–5 transverse, 4–6 mm apart, 0.3 mm deep, above the patella; a fainter set below the patella across the ligament | E |
| Knee callus ("kneeling patch") | 40 × 35 mm over the lower patella and tuberosity; roughness 0.65, paler and greyer #c2a08c, flaking micro bump 0.05 mm | E (boot-wearing, kneeling soldier) |
| Sock-band hair wear | density × 0.3 at z 90–260, hairs there shorter (× 0.6) | spec 01 request |
| Moles | default none (client question §10.2); if enabled 2 per leg, 2–4 mm, #6b4a3a, flat, seeded positions | — |
| Scars | default none; optional 1 pale healed abrasion 12 × 6 mm on the right lower patella (#d8bca8, roughness 0.5, 0.1 mm recess) | client question |

---

## 4. Geometry construction plan

All edits are scripted on the MPFB base mesh `Body.Mesh` (13,380 body quads; the legs and pelvis region holds ≈ 4,000 of them [VERIFY: count the vertices with z between 0.30 and 1.03 after `create_human`]) with render-time `Subdivision` level 2 (viewport 1), as spec 01 prescribes. Topology below z 300 and above the crest is not touched; the UV map stays MakeHuman's. Three relief layers: **A** base-mesh soft sculpt (shape keys, features ≥ 15 mm), **B** mid-frequency displacement map baked from landmark curves (1–8 mm features), **C** shader bump (sub-millimetre).

### 4.1 Step 1 — Base human (MPFB, `scripts/lib/proportions.py::create_base()`)
`HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True, scale=0.1, macro_detail_dict=macro)` with macro: gender 1.0, age 0.615 (40 y), muscle **0.70**, weight **0.45**, proportions 0.5, height solved (start 0.583 for 1855; measure the evaluated mesh, secant to 1855 ± 2), cupsize 0.5, firmness 0.5, race caucasian 1.0 (consolidated §2 start values). Record `Body.Mesh` with the helper geometry visible (helpers carry the joint cubes the rig fit reads).

### 4.2 Step 2 — Proportion targets and the z-remap (`proportions.py::fit_proportions()`)
Load with `TargetService.load_target(basemesh, TargetService.target_full_path(name), weight=w)` (names are file stems; negative values are the `-decr` twin with a positive weight):

| Target | Start weight | Purpose | Measured by |
|---|---|---|---|
| `measure-upperleg-height-decr` | 0.8 | shorten the thigh | knee-axis cube to hip cube distance (helper joints) |
| `upperlegs-height-decr` | 0.5 | same, second lever | — |
| `hip-trans-down` | 0.6 | drop the pelvis | crest and trochanter heights |
| `measure-waisttohip-dist-incr` | 0.7 | lengthen the lower torso to keep the stature | stature |
| `measure-napetowaist-dist-incr` | 0.3 | upper torso share of the lengthening | stature, acromion 1521 (torso spec) |
| `measure-lowerleg-height-incr/decr` | solve | shank 446 | knee cube → ankle cube |
| `measure-thigh-circ-incr/decr` | solve | 603 at h 795 | `slice_measure` |
| `measure-knee-circ-incr/decr` | solve | 390 at the patella | — |
| `measure-calf-circ-incr/decr` | solve | 390 at h 365 | — |
| `measure-ankle-circ-incr/decr` | solve (spec 01 owns the final value) | 236 at z 115 | — |
| `measure-hips-circ-incr/decr` | solve | 999 at h 842 | — |
| `l-/r-upperleg-muscle-incr` | 0.35 | quads/hamstring definition | visual |
| `l-/r-lowerleg-muscle-incr` | 0.4 | calf and tibialis definition | visual |
| `l-/r-upperleg-fat-decr`, `l-/r-lowerleg-fat-decr` | 0.25 | lean legs | — |
| `buttocks-volume-incr` | 0.2 | athletic glutes | buttock depth 233 |
| `pelvis-tone-incr` | 0.3 | firm pelvis | — |
| `l-/r-leg-valgus-incr` | 0.1 | slight knee-in (Q-angle) | knee X ±93 vs hip ±88 / ankle ±100 |

Solver: for the six "solve" rows run up to 6 secant iterations each against `measure_leg()` (§8.2) on the evaluated mesh; clamp weights to [0, 1]. Then measure the hip joint centre (mean of the hip joint-cube vertices), knee axis (knee cubes), ankle (ankle cubes), perineum (lowest vertex of the groin loop) and crest (highest crest vertex). If the hip centre is not at 851 ± 3 or the knee axis not at 526 ± 2, build shape key `Leg.Proportion`: a monotone piecewise-linear remap z' = f(z) with knots (0 → 0), (80 → 80), (526 → 526), (h_hip_measured → 851), (h_crest_measured → 1031), (1855 → 1855), applied with numpy to the shape-key coordinates of every vertex including helpers (`basemesh.data.shape_keys.key_blocks["Leg.Proportion"].data.foreach_set`), weight 1.0. Expected residual ≤ 40 mm. Log the final heights.

### 4.3 Step 3 — Rig fit (`HumanService.add_builtin_rig(basemesh, "default", import_weights=True)` → rename armature `Morgan.Rig`)
Added only after step 2 so the joint cubes are in their final place [VERIFY: whether MPFB refits bones on later target changes; we refit regardless by re-running this step]. Verify `upperleg01.L` head = (+88, Y0, 851) ± 5, `lowerleg01.L` head = (+93, Y0, 526) ± 4, `foot.L` head z 80 ± 3 (Y0 = the rest coronal plane the fit produces; record it). Bone names used below are MPFB default: `pelvis.L/R`, `upperleg01/02.L/R`, `lowerleg01/02.L/R`, `foot.L/R`, `spine01`.

### 4.4 Step 4 — Vertex groups for the part (`weights.py::make_region_groups()`)
Built from rest-space distance fields (numpy) so they survive any topology-preserving step: `Leg.L.Thigh` (z 530–851 within 120 mm of the femur axis), `Leg.L.Knee` (z 460–600), `Leg.L.Patella` (ellipse 45 × 50 at (93, −44, 521), falloff 6 mm), `Leg.L.Shank` (z 300–526), `Leg.L.Shin` (within 22 mm of the tibial crest line), `Leg.L.Calf`, `Leg.L.Popliteal` (diamond 60 × 90 at (93, +52, 530)), `Leg.L.VMO`, `Leg.L.ITBand`, `Leg.L.Sartorius` (tube r 8 along the groove line), `Leg.L.Vein` (tube r 3 along the saphenous polyline), `Leg.L.Blend300` (z 300–340 linear), `Pelvis.Crest` (z 1000–1031), `Pelvis.Glute.L/R`, `Pelvis.Groin`, `Leg.L.StrapBand.Upper` (h 761–795, right only), `Leg.R.StrapBand.Lower` (651–700), `Leg.L.StrapBand.Lower` (668–710), `Pelvis.BeltBand` (h 812–859), `Leg.L.HairDensity` (float weights from the §3.6 density table divided by 12), `Leg.L.KneeCallus`. These drive the sculpt ops, the baked masks, the hair and the compressions.

### 4.5 Step 5 — Layer A sculpt (`sculpt.py` `soft_inflate(centre, r, amount)` and `soft_move(centre, r, vector)` from spec 01, Gaussian falloff; all on shape key `Leg.Sculpt`, left leg then mirrored by `mirror_shape_key(key, axis='X')` with the right leg given the asymmetries listed)
Order matters (volumes first, hollows last). Left leg, frame G:
1. **Pelvis bones:** `soft_inflate` ASIS (+120, −72, 988) r 14, +3; crest ridge: 9 inflates r 12, +2 along the crest arc from the ASIS to the PSIS; PSIS dimples `soft_move` (+42, +85, 1000) r 10 by (0, −3, 0); trochanter `soft_inflate` (+165, 0, 861) r 22, +4; trochanteric depression `soft_move` (+166, +14, 850) r 18 by (−4, 0, 0).
2. **Glutes:** `soft_inflate` (+85, +148, 842) r 70, +5 (reach buttock depth 233); gluteal fold: `soft_move` along the fold line (6 stations) r 10 by (0, −3 → 0, 0) medial → lateral; natal cleft `soft_move` (0, +130, 850) r 12 by (0, −8, 0).
3. **Thigh masses:** rectus belly (90, −62, 700) r 35, +6; vastus lateralis (163, −10, 650) r 50, +8; vastus medialis (33, −30, 700) r 35, +4; VMO (53, −35, 575) r 28, +7; adductors (23, 0, 760) r 45, +6; hamstrings (85, +90, 700) r 55, +5; TFL (158, −45, 900) r 25, +4; glute med (148, +20, 920) r 35, +3; IT band strip: 6 `soft_move` r 14 by (−1, 0, 0) along the strip; sartorius groove: 9 `soft_move` r 9 by 2 mm inward along the local normal.
4. **Knee block:** patella `soft_inflate` (93, −48, 521) r 24, +8; then shape its poles with `soft_move` (93, −52, 546) r 8 by (0, +2, 0) and apex (93, −52, 496) r 7 by (0, +2, 0); medial condyle (45, +2, 525) r 22, +2.5; lateral condyle (141, −2, 527) r 20, +2; quadriceps tendon (93, −50, 573) r 12, +2; patellar ligament (96, −50, 480) r 11, +2; fat pads (78, −47, 490) and (114, −47, 490) r 9, +3; tibial tuberosity (95, −46, 465) r 12, +4; fibular head (135, +12, 485) r 11, +3; Gerdy (128, −25, 490) r 7, +1.5; popliteal fossa `soft_move` (93, +52, 530) r 30 by (0, −6, 0); biceps tendon cord 4 inflates r 7, +3 from (128, +45, 560) to (135, +14, 490); semitendinosus 4 inflates r 5, +3 from (61, +50, 560) to (53, +15, 500).
5. **Shank:** tibialis anterior 5 inflates r 18 → 8, +4 → +1.5 along its line; peroneals 5 inflates r 14, +2.5; EDL 4 inflates r 12, +2; medial gastrocnemius (68, +42, 390) r 40, +10; lateral gastrocnemius (115, +38, 400) r 34, +8; soleus flanks (70, +40, 260) and (118, +38, 270) r 25, +3; tibial face flatten: 8 `soft_move` r 12 by 0.5 mm inward along the face; tibial crest 10 inflates r 6, +1.0 along the crest polyline.
6. **Blend:** multiply all deltas in `Leg.L.Blend300` by the group weight (0 at z 300, 1 at 340) so spec 01's geometry is untouched; same at the crest (`Pelvis.Crest` 1 → 0 toward z 1031) for the torso spec.
7. **Right-leg asymmetries** (no two limbs are identical): right vastus lateralis +0.5 mm more, right calf max 2 mm lower (h 363), right patella 1 mm wider, right tibial tuberosity +0.5 mm, left VMO +0.5 mm.

The base mesh's vertex spacing on the leg is ≈ 20–35 mm [VERIFY], so every radius above is ≥ 6 mm and features under 12 mm live in layers B and C. Check after this step by `measure_leg()` and the Workbench matcap views (5 s each).

### 4.6 Step 6 — Layer B relief map (`Leg.Relief`, 4096² EXR, baked)
Build a Geometry Nodes modifier `Leg.ReliefBake` on a copy `Leg.BakeProxy` (Subdivision 3 applied): `Store Named Attribute` floats from `Geometry Proximity` to curve objects created from the landmark polylines (`Leg.L.Curve.TibialCrest`, `.Sartorius`, `.Vein`, `.BicepsTendon`, `.SemiTendon`, `.PatellarLigament`, `.InguinalGroove`, `.GlutealFold`, and the knee crease set as 4 short curves at h 548–572): relief(d) = amplitude × smoothstep(1 − d/width) with the amplitudes/widths of §3.3–3.5 (crest +1.0/8; vein +0.7/4 (shank) and +0.5/5 (thigh); tendons +3/10; ligament +2/14; sartorius −2/10; inguinal −2/8; gluteal fold −3/10 → 0; knee creases −0.3/1.5). Apply the GN modifier (`modifier_apply` under `temp_override`), feed the attribute through an Emission shader (`Attribute` node → Emission) and bake (`bpy.ops.object.bake(type='EMIT')` with the real selection and an active Image Texture node, 4096², margin 16 px; t10 proved `object.bake` headless) into `Leg.Relief.exr`. Texel density on MakeHuman's UVs ≈ 2.4 px/mm at 4K [estimated: ~2.1 m² of skin over ~70 % of the square; VERIFY by measuring the leg UV island area]. The map is used twice: a `Displace` modifier on `Body.Mesh` after `Subdivision` (UV coords, strength 0.004 m, mid-level 0.5 — the EXR stores mm/4 + 0.5 — limited to `Leg.L.*` ∪ `Pelvis.*` groups) and as a Bump input in the shader (§5.3) so Workbench and glTF LOD1 still show the relief.

### 4.7 Step 7 — Compression shape keys (`Leg.Compress.Straps`, `Leg.Compress.Belt`)
`Leg.Compress.Straps`: −2.0 mm along the normal inside each `StrapBand` group with a +0.8 mm bulge ridge 6 mm outside each band edge (the flesh displaced by a 38 mm nylon strap pulled hand-tight); `Leg.Compress.Belt`: −3 mm inside `Pelvis.BeltBand` over the glute and flank, 0 over the trochanter bone, +1 mm bulge above (h 859–870). Values 1.0 in the hero pose, 0 in the game rest (drivers off; the trousers' Shrinkwrap bands in spec 09 pull the cloth to body + 3 mm regardless).

### 4.8 Step 8 — Patella bones and knee anchors
Add to `Morgan.Rig` (edit mode with the real selection, research C §7): `patella.L/R`, head at the patella centre (93, −44, 521), tail +20 mm along −Y, parent `upperleg02.L/R` (keep offset), constraint `Copy Rotation` from `lowerleg01.L/R`, influence 0.5, local space, X axis only → the kneecap follows half the flexion and slides distally ≈ 0.45 mm per degree (real patellar tracking ≈ 0.5 mm/°). Empties `Leg.L.KneeAnchor` / `Leg.R.KneeAnchor` parented to `patella.*`: location = patella centre + 28 mm along −Y (pocket foam + cap stand-off), rotation = knee-facing frame (−Y of the empty = the thigh facing direction). Spec 12 parents the caps here; spec 09 reads the knee pocket centre from here.

### 4.9 Step 9 — Helper surfaces for the neighbours
`Leg.L.KneeFootprint` / `Leg.R.KneeFootprint`: a 160 × 190 mm patch of the posed knee surface (duplicate of the evaluated body faces inside an ellipse around the patella, `Shrinkwrap` to the posed body, `Solidify` 28 mm outward, top face only kept): the surface the kneepad spec moulds the cap's foam to. `Body.Collider` (spec 09 names it): decimated copy of the posed body (6–8 k faces, `Decimate` ratio 0.45 planar) — this part owns its leg/pelvis region; the torso spec owns the rest. `Leg.L.StrapRing.Upper/Lower`, `Leg.R.StrapRing.Lower`: 64-vertex loops (`bmesh` circles projected onto the posed body at the strap band mid-heights, offset 1.5 mm) that the drop-leg rig spec threads its straps along. `Pelvis.BeltRing`: the loop at h 835 posed, offset by the trouser cloth (3 mm) + 2 mm for the belt's inner face.

### 4.10 Step 10 — Hair curves (`Leg.L.Hair`, `Leg.R.Hair`, `Leg.*.Vellus`; only built with `--hair`)
Python-built `bpy.data.hair_curves`: roots by rejection sampling faces of the evaluated rest body weighted by face area × `Leg.*.HairDensity` (target counts: shin+calf ≈ 7,000, thigh ≈ 5,500, glute ≈ 500 → 13,000 per leg ± 10 %), 6 points per strand, length from the §3.6 table × uniform(0.7, 1.3), direction = surface tangent toward −Z rotated by the regional angle, lifted 12° off the skin at the root and lying flat by the third point, curvature radius 25 ± 10 mm, 0.5 mm random tip jitter; radius attribute 0.035 → 0.012 mm root → tip. Vellus: 60,000 per leg, 2 mm, radius 0.012. Material: Principled Hair BSDF (Chiang), melanin 0.75, melanin redness 0.3, roughness 0.3, radial roughness 0.3, coat 0.1; vellus melanin 0.15. `scene.cycles_curves.shape = "THICK"`. Surface-attached to `Body.Mesh` (`surface` + `surface_uv_map`) so they follow the Armature deformation. Cost: build < 1 s; render +30–60 s per bare view (research C §3). Hidden in every clothed render and never exported to the game.

### 4.11 Poly budget and object list

| Object | Faces (base / render) | Notes |
|---|---|---|
| `Body.Mesh` leg + pelvis region | ≈ 4,000 quads / ≈ 64,000 at Subdivision 2 | shared body object; this part's data are shape keys `Leg.Proportion`, `Leg.Sculpt`, `Leg.Compress.*`, `Leg.Corr.*` and groups `Leg.*`, `Pelvis.*` |
| `Leg.L/R.KneeFootprint` | ≈ 400 each | helper, not rendered |
| `Body.Collider` | 6–8 k | cloth collision (spec 09) |
| `Leg.*.StrapRing.*`, `Pelvis.BeltRing` | 64 verts each, no faces | guides |
| `Leg.L/R.Curve.*` (11 curves per leg) | — | relief bake inputs, hidden |
| `Leg.L/R.Hair`, `Leg.L/R.Vellus` | 13 k + 60 k strands | bare renders only |
| `Leg.Relief.exr` (image) | 4096², 1 channel | packed |
| `Leg.Masks.png` (image) | 4096² RGBA | R hair density, G knee callus/crease, B vein, A SSS thickness |

Origin and orientation: everything inherits `Body.Mesh`'s origin (0, 0, 0) and world axes; helper empties carry their own frames (§4.8).

---

## 5. Materials and textures

### 5.1 Skin — Principled BSDF (one material `Skin.Body` shared with the torso and arms; regional values through the colour attribute `skin_tint` and the baked `Leg.Masks.png`; the node group is spec 01's shared skin group [VERIFY its name in `scripts/lib/materials.py`])

| Region | Base colour (albedo) | Roughness | SSS scale (m) | Coat | Notes |
|---|---|---|---|---|---|
| Thigh, anterior/lateral | **#c39a80** | 0.48 | 0.0040 | 0.08 / rough 0.45 | 8 mm fat → larger scatter |
| Thigh, medial/posterior | #c9a28a (paler) | 0.46 | 0.0040 | 0.08 | sparser hair, less sun ever |
| Knee (patella, tuberosity) | **#b58a70** darker, 4 % greyer | 0.60 | 0.0028 | 0.04 | thick skin; callus patch #c2a08c, roughness 0.65 |
| Popliteal | #cfa892 | 0.44 | 0.0032 | 0.10 | thin skin, slight sheen |
| Shin (over the tibia) | #bf967c | **0.42** | 0.0025 | 0.14 / rough 0.35 | tight shiny skin over bone |
| Calf | #c39a80 | 0.48 | 0.0038 | 0.08 | |
| Gluteal | #c7a08c, 3 % cooler | 0.50 | 0.0045 | 0.06 | 18 mm fat |
| Groin/pubic | #c0947c | 0.52 | 0.0035 | 0.04 | |
| Vein tint (mask B) | 18 % mix toward #7d8b86 | — | — | — | 4 mm band, soft 2 mm edges |

Common: `subsurface_method = "RANDOM_WALK_SKIN"`, Subsurface Weight 1.0, Radius (1.0, 0.2, 0.1), IOR 1.4, Anisotropy 0.8 (research C §8); Specular IOR level 0.5 (IOR 1.4); Sheen 0.05 tint white (peach fuzz approximation where vellus is hidden). Subdermal mottling: Noise scale 30 mm → ColorRamp ±4 % lightness, 3 % hue toward blue-green on the thigh (visible veins' diffuse haze), 2 % toward red on the knee and shin. Skin colour contrast check against the face: the leg base is L* 66 vs the face albedo #b98670 L* 60 (ΔL* +6, ΔC −3).

### 5.2 Masks (`Leg.Masks.png`, baked like the relief map)
R = hair density (0–1 = 0–12/cm²), with the sock band ×0.3 at z 90–260 and ×0 under the foot spec's z < 90; G = knee mask: callus ellipse 40 × 35 at the lower patella (1.0) + crease lines (0.6) + a 15 mm feather; B = vein proximity (saphenous tube r 2, feather 2); A = SSS thickness proxy (fat table §3.6 normalised to 20 mm) → multiplies the SSS scale.

### 5.3 Micro relief (layer C, shader bump; `displacement_method = "BUMP"`)
Bump distance 0.001 m, strength 0.35, inputs summed: (a) follicle pits: Voronoi F1 (scale 1 per 1.6 mm on the thigh, 1 per 1.2 mm on the shin; via Object coords scaled, not UV, to avoid seams), threshold 0.12 → pit depth 0.08 mm; (b) skin lines: two Wave textures at ±35° to the limb axis, 0.5 mm pitch, distortion 2, amplitude 0.03 mm; (c) knee creases from mask G × Wave (2.5 mm pitch along the limb axis) 0.3 mm; (d) callus flakes: Voronoi (smooth 0) scale 1 per 0.8 mm, 0.05 mm, inside the callus ellipse; (e) `Leg.Relief.exr` as a second Bump (distance 0.004) so Workbench/LOD shows the tendons; (f) orange-peel noise scale 900, 0.02 mm everywhere. Roughness = regional base + 0.08 × (a) pits + 0.15 × callus mask − 0.06 × vein mask.

### 5.4 Texture sets and texel density
No downloaded PBR set is used for skin (`research_assets.md` §4 has none; all skin is procedural + baked masks). Baked maps are 4096² on MakeHuman's UVs (≈ 2.4 px/mm [estimated]); the hero render needs ≈ 0.5 px/mm for any visible skin and a 2048² macro view (V6, 100 mm lens, 350 mm distance → ≈ 15 px/mm at the patella) is served by the procedural layer C, which is resolution-independent. UVs: unchanged MakeHuman body map; the seam down the inner leg is MakeHuman's.

### 5.5 Hex targets
Nothing in the reference shows skin here, so colour acceptance is against look-dev swatches: under scene A's key at 45°, the rendered mid-thigh must read within ΔE76 < 6 of **#d8b49a** (the albedo #c39a80 lit by the calibrated key as spec 01's foot renders show for the dorsum), knee within ΔE < 6 of #c7a088, shin highlight ≤ #f0dccc. Under scene B the legs are never visible; the only hex targets this part answers to are the knee-pocket positions (§8.2 overlay), not colours.

---

## 6. Fibres, simulation or dynamics
* **Hair:** §4.10 (Curves objects, Principled Hair BSDF); no simulation; hair follows the Armature through surface attachment.
* **No cloth here.** The trousers' simulation (spec 09) collides with `Body.Collider`, which this part produces for the leg/pelvis region in the hero pose; the collider must have `Collision` thickness_outer 0.002 (spec 09 §6).
* **Soft-tissue dynamics:** none at render time; the strap/belt compressions are static shape keys (§4.7). Jiggle is not wanted for a standing pose.
* **Corrective deformation:** a `Corrective Smooth` modifier (`rest_source 'ORCO'`, factor 0.5, iterations 5, `use_only_smooth` off, `use_pin_boundary` on, restricted to the vertex group `Leg.Joints` = knee ± 60 mm ∪ hip ± 70 mm) after the `Armature` modifier (Preserve Volume on) and before `Subdivision`, plus the driven shape keys of §7.5.

---

## 7. Rigging and attachment

### 7.1 Bones (MPFB default rig, verified positions after step 3)

| Bone | Head (rest, world, left) | Tail | Role |
|---|---|---|---|
| `pelvis.L/R` | (±0, Y0, 900) [VERIFY MPFB's pelvis bone head] | hip centre | pelvis halves (MPFB default) |
| `upperleg01.L` | (+88, Y0, 851) | mid-thigh (+90, Y0, 689) | hip swing + 60 % of the twist |
| `upperleg02.L` | (+90, Y0, 689) | knee axis (+93, Y0, 526) | 40 % of the thigh twist |
| `lowerleg01.L` | (+93, Y0, 526) | (+96, Y0, 303) | knee flexion + 50 % tibial rotation |
| `lowerleg02.L` | (+96, Y0, 303) | ankle axis (+100, Y0, 80) | 50 % tibial rotation; malleoli weighted here (spec 01) |
| `patella.L` (new) | (+93, Y0 − 44, 521) | (+93, Y0 − 64, 521) | kneecap tracking, §4.8 |
| `foot.L` | spec 01 | | |

Rest Y0 is the fit's coronal plane; log it. Bone rolls: X axis of every leg bone lateral (+X for the left) so that +X rotation = flexion.

### 7.2 Weights (`weights.py`)
Start from MPFB's imported weights, then (numpy on `vertex_groups` weights, normalised per vertex): knee band z 466–586: smoothstep blend from `upperleg02` (1.0 at 586) to `lowerleg01` (1.0 at 466); `Leg.L.Patella` vertices: 0.7 `patella.L`, 0.3 the blend; hip band z 790–900: smoothstep from `upperleg01` (1.0 at 790) to `pelvis` (1.0 at 900), glutes 0.85 pelvis; thigh twist: `upperleg01` vs `upperleg02` weights follow a linear ramp along the femur so a twist spreads evenly; shank twist ramp likewise `lowerleg01` → `lowerleg02` between z 526 and 80; the malleoli regions stay on `lowerleg02` (spec 01 §7.2). Export check: ≤ 4 influences per vertex (glTF).

### 7.3 Pose (hero): IK closure, then FK readback
Inputs (world, posed): pelvis centre (−40, 0, 829) yaw −10° (turned to his right), pitch +2° anterior, roll 0 → hip centres R (−126.7, +15.3, 829), L (+46.7, −15.3, 829). Ankle axes from spec 01: R (−208, +75, 80), L (+208, −75, 80). Knee facing directions: R 45° to his right of the camera axis (unit vector (−0.707, −0.707, 0)), L 12° to his left ((+0.208, −0.978, 0)). Method: two-bone IK (`IK` constraint on `lowerleg02`, chain_count 4 over upperleg01→lowerleg02, pole targets 400 mm out along the facing directions, `pole_angle` solved so the knee axis is perpendicular to the facing), then `bpy.ops.pose.visual_transform_apply` and the constraints removed; the twist about each limb's long axis is set explicitly afterwards (hip external rotation such that the thigh faces the stated direction; tibial rotation R 20° / L 5°; foot headings 90° right / 15° left from spec 01). Then read back and check against the analysts (±5°, consolidated §1): expected R hip flex −5, abd 16, ext-rot 35–40 (relative to the yawed pelvis), R knee flex 17; L hip flex +8, abd 14, ext-rot 22, L knee flex 9. Expected posed heights: R knee axis 516, L 519, hip 829 — these are what `FEMUR_MM = 325` was derived from (§3.1); if the IK leaves the hips > 6 mm from 829 the script re-solves the femur (`proportions.py::solve_femur()`) and rebuilds from step 2.

### 7.4 Knee-facing frames
`Leg.R.KneeAnchor` −Y = (−0.707, −0.707, 0), `Leg.L.KneeAnchor` −Y = (+0.208, −0.978, 0); both Z = world Z rotated by the knee flexion so the cap tilts with the shank's upper third (right 8°, left 4° back from vertical). The V6 macro camera sits 350 mm from the right patella along +(0.707, 0.707, 0) at the patella height.

### 7.5 Corrective shape keys (generated, not sculpted: `corrective.py::make_corrective(mesh, rig, pose_dict, ops) → key + driver`)
Procedure: pose the rig; take the evaluated (Armature + Corrective Smooth) vertex positions; run the listed `soft_*` ops in posed space; inverse-skin the edited positions to rest with the per-vertex blended inverse matrices (numpy: `inv(Σ w_i M_i)`), store as a shape key, add a driver (`SCRIPTED`, variables of type `TRANSFORMS` on the bone with rotation mode `SWING_TWIST_X`/`_Y`).

| Key | Driver | Ops (left; mirrored for right) | Purpose |
|---|---|---|---|
| `Leg.Corr.KneeFlex90.L` | `lowerleg01.L` rot X, 0 → 1 over 30°–90°, hold | patella `soft_move` −Y 3 mm and −Z 8 mm; popliteal `soft_move` (0, +8, 0) r 35 (fossa fills); condyle front `soft_inflate` (93, −45, 500) r 22, +3; knee creases flatten (drives mask G × (1 − key)) | kneecap and fossa at bent knee |
| `Leg.Corr.KneeFlex130.L` | 1 over 100°–130° | calf–thigh contact bulge: `soft_inflate` calf (68, +42, 390) r 45, +6 and hamstring (85, +90, 700) r 45, +5; `soft_move` popliteal skin outward 4 mm | deep squat |
| `Leg.Corr.HipFlex.L` | `upperleg01.L` swing X, 0 → 1 over 30°–90° | inguinal fold `soft_move` along the groove 6 mm inward; TFL/rectus `soft_inflate` r 30, +4; glute flatten −4 | sitting / kneeling |
| `Leg.Corr.HipExtRot.R` | `upperleg01.R` twist Y, 0 → 1 over 0°–45° | trochanteric depression moves posteriorly 15 mm (two moves); glute med `soft_inflate` +2; adductor fold at the perineum `soft_move` 3 mm | hero pose right leg |
| `Leg.Corr.HipAbd.L/R` | swing Z, 0 → 1 over 0°–25° | lateral hip `soft_inflate` (172, 5, 845) r 25, +2; medial groin `soft_move` −2 | stance |
| `Leg.Corr.KneeFlex90.R`, `.HipFlex.R`, `.HipExtRot.L`, `.KneeFlex130.R` | mirrors | — | |

Game export: drivers do not survive glTF; the script bakes the hero-pose key values into a `Leg.Corr.Hero` morph target and keeps the eight driven keys as morph targets for the engine to drive (`export_morph=True`).

### 7.6 Attachments provided to other parts
`Leg.L/R.KneeAnchor` (kneepads), `Leg.*.KneeFootprint` (kneepad foam), `Leg.*.StrapRing.*` and `Pelvis.BeltRing` (drop-leg rigs and belt), `Body.Collider` leg region (trousers), `patella.L/R` bones (trousers' knee pocket follows them through the body's deformation), the `Leg.Compress.*` keys (set to 1.0 by `build_all.py` before the cloth simulation).

---

## 8. Evaluation protocol

### 8.1 Renders
Workbench form set (`renders/03_leg_pelvis/form_*.png`, ≈ 5 s each): V1–V4 in matcap + cavity (ridge/valley), rest pose, bare, 1024². Cycles set (`renders/03_leg_pelvis/*.png`): V1–V4 in scene A at 48 spp 1024² (≈ 40 s each), V5 in scene B at 64 spp 1024 × 1536 with the trousers hidden and the overlay composited by PIL (≈ 2–4 min), V6 at 48 spp 1024² with hair (≈ 90 s). Contact sheet `renders/03_leg_pelvis/sheet.png` with the reference crops beside V1, V2, V3, V5.

### 8.2 Metrics (`measure.py::measure_leg()`, extending spec 01's `slice_measure`)
Reported for each leg and the pelvis in rest and in the hero pose: joint heights from bone heads (hip, knee, ankle); perineum (lowest groin vertex), crest (highest `Pelvis.Crest` vertex), ASIS (local −Y max in the ASIS group), trochanter (|X| max at z 830–870); girths by bisect planes at h 795, 660, 600, 521, 500, 440, 365, 330, 300, 260, 210, 115; knee width (X extent at 526), patella prominence (−Y extent of `Leg.*.Patella` minus the condyle plane), tibial tuberosity prominence, calf max height (argmax girth over z 300–450), medial vs lateral gastrocnemius lower edge heights (curvature minima along the posterior silhouette), popliteal depth (Y at the fossa centre vs the tendon line), hip breadth, bicristale, buttock depth; hair count per region (roots binned by group weight); strand radius statistics. **Overlay** for V5: render the posed bare body silhouette with the hero camera; the reference trouser silhouette mask = dark runs of `reference_full.png` (luminance < 70 against the lit floor; where the hangar background is also dark use the analysts' x-ranges of §2.1) dilated 2 px; report the minimum signed clearance (mm at the figure's depth, 2.119 mm/px) per height band, and the projected patella centres against the cap centres (727.5, 657.5) / (901, 655). Pose readback (§7.3) in degrees with the analysts' values beside.

### 8.3 Critic questions (score 0–2 each, 24 max; ≥ 20 passes)
1. Is this a lean, athletic 40-year-old man's leg, or a mannequin's tube?
2. Does the knee show patella, condyles, ligament, tuberosity and two hamstring tendons as separate forms?
3. Does the kneecap have an upper pole and an apex, and sit proud of the condyles by about 8 mm?
4. Does the shin bone read as a sharp edge spiralling medially toward the ankle, with tibialis anterior lateral of it?
5. Two calf heads, the medial lower and larger; a soleus taper; Achilles cord continuing into spec 01's ankle?
6. Rectus femoris ridge, VMO teardrop, vastus lateralis bulge, flat IT-band strip, sartorius groove: all present and in the right places?
7. Pelvis: ASIS, crest, trochanter dimple, gluteal fold, sacral dimples — a real pelvis under the skin?
8. Are the hips, crotch and knees where the drawing puts them (V5 overlay within tolerance) and does the body stay inside the trousers?
9. Knee skin darker and rougher than the thigh, with transverse creases; shin shinier; popliteal paler?
10. Hair sparse, dark, lying down the leg, thinned in the sock band; vellus only in rim light; no "fur"?
11. The saphenous vein as faint green-grey relief on the inner shank, not a drawn line?
12. In the hero pose, no candy-wrapper at the right hip, no volume loss at the knees, the kneecaps facing the stated directions?

### 8.4 Failure modes and their fixes
* Measure targets saturate before the thigh is short enough → the z-remap residual grows beyond 40 mm and stretches the lower torso's texture; fix by sharing the remap with the torso spec's `Torso.Proportion` so the stretch is spread over the whole trunk.
* Rig fit puts the knee head at the base mesh's knee cube, not at our axis, after the remap → refit the rig after the remap (step 3 always follows step 2).
* IK closure fails (leg too short: a straight leg of 325 + 446 cannot reach a hip–ankle distance > 771) → the solver flags it and re-solves `FEMUR_MM`; never move the ankles or knees.
* Base-mesh density too low for the patella block (one vertex ring over the kneecap) → the `Leg.Proportion`/`Leg.Sculpt` keys are kept, and the patella/tuberosity amplitudes are moved into the relief map (layer B) with doubled amplitude.
* Corrective Smooth bleeding into the foot spec's ankle → the `Leg.Joints` group ends at z 400.
* Hair roots on the sock band or under the trousers' Shrinkwrap bands poking through cloth → hair is hidden in clothed renders; for the game nothing is exported.
* Skin glow (SSS scale too large on the shin) → the mask A thickness term caps the scale at 0.0025 over bone.

---

## 9. Build order, effort and risks

| # | Step | Tool | Run time | Dev effort | Risk |
|---|---|---|---|---|---|
| 1 | Base human + height solve | MPFB `create_human`, `reapply_macro_details` | 2 s | 0.5 h | low |
| 2 | Proportion targets + z-remap + measurements | `TargetService`, numpy, `measure_leg` | 5 s | 4 h (solver, measurement rig) | **high**: unknown target gains; the remap is the safety net |
| 3 | Rig fit + rename + verification | `add_builtin_rig` | 1 s | 0.5 h | medium: refit behaviour [VERIFY] |
| 4 | Region vertex groups | numpy distance fields | 1 s | 2 h | low |
| 5 | Layer A sculpt (≈ 110 ops) | `sculpt.py` | 2 s | 5 h (tuning against V1–V4 Workbench) | medium: base density |
| 6 | Landmark curves, GN proximity, bake relief + masks | GN, `object.bake` | 20 s | 4 h | medium: bake context (t10 proved it) |
| 7 | Compression keys | numpy on groups | 1 s | 1 h | low |
| 8 | Patella bones, anchors | edit-bone API with real selection | 1 s | 1.5 h | low |
| 9 | Helper surfaces, collider | bmesh, Shrinkwrap, Decimate | 3 s | 2 h | low |
| 10 | Hair | `hair_curves` API | 1 s build, +60 s render | 2 h | low |
| 11 | Weights | numpy | 1 s | 2 h | medium: twist ramps vs MPFB weights |
| 12 | Pose: IK closure, readback, femur re-solve | IK constraints, `visual_transform_apply` | 2 s | 3 h | medium |
| 13 | Correctives (8 keys) | `corrective.py` | 10 s | 5 h | **high**: inverse skinning numerics; validate on a bent tube first (research C §7 limb) |
| 14 | Renders, metrics, overlay, sheet | Workbench, Cycles, PIL | 6–9 min | 3 h | low |

Total: ≈ 36 h of script writing and tuning; a full rebuild runs in ≈ 1 min plus 6–9 min of renders. Order of value: 1–3 and 12 first (they fix the interfaces every other lower-body part depends on: hip, crotch, knee heights and the knee anchors), then 5–6 (form), then 10, 13, 14.

---

## 10. Interfaces and open questions for the client

### 10.1 What neighbouring parts must provide or respect

| Part | This part provides | This part needs / the neighbour must respect |
|---|---|---|
| Foot, ankle, sock (01) | shank girths 365 at z 300, 335 at z 260, 290 at z 210 (table §3.5); hair density tapering to 30 % in z 90–260 as asked; `lowerleg02` twist ramp ending at the ankle | spec 01's "calf 400–420 at z 330" is **not** met: this body measures 385 there (ANSUR 386); the sock is knitted stretch and spec 01 should relax its number. Nothing below z 300 is touched here. Ankle axes (±208, ∓75, 80) are taken as given. |
| Combat trousers (09) | posed hips 829, perineum 779 (trouser apex 763 = 16 mm drop, inside spec 09's 755–775 window); knee axes R 516 / L 519 and patella centres R (−217, 505) / L (+135, 510); **knee articulation (pocket top seam) at h 665 = 140 mm above the knee axis, where the body girth is 460**; knee pocket span h 619 → 388 centred 10 mm below the patella; `Body.Collider` leg/pelvis region; `Leg.Compress.*` keys; `patella.*` bones; strap-band groups at the same heights spec 09 uses (R upper 761–795, R lower 651–700, L lower 668–710); belt band 812–859 | spec 09's hip joint "h 827" becomes 829 (within its tolerance); its crotch frame X −42 is kept (pelvis centre −40) |
| Kneepads (12) | `Leg.L/R.KneeAnchor` (patella + 28 mm along the facing), `Leg.*.KneeFootprint`, cap centres to hit (727.5, 657.5) / (901, 655), the knee-facing directions 45° right / 12° left, the knee front radii 55 (transverse) × 90 (vertical) | cap centred on the anchor, +15 mm lateral on the left; rear strap passes through the popliteal band h 500–525 over the trousers |
| Belt / drop-leg rigs | `Pelvis.BeltRing` (h 835 posed, trousers + 2 mm), `Leg.*.StrapRing.*`; the compressions under straps (body −2 mm) | straps 38 mm wide, hand-tight, ladder-locks on the thigh front 45° round on the right |
| Boots | ankle axis height 80, collar at z 210 is spec 01's/the boot's; the shank circumference 290 at 210 is the inside of the collar's padding allowance | — |
| Torso | iliac crest at h 1031 rest, pelvis top ring, `Pelvis.*` groups, the z-remap `Leg.Proportion` (the torso above the crest is stretched by 102 mm so acromion 1521 and chin 1620 stay) | the torso spec owns everything above the crest and bridges a 176 mm flank from the 10th rib (1189) to the crest; it may take over part of the remap (§8.4) |
| Rig / `build_all.py` | bone verification, `patella.*`, twist split rule (60/40 thigh, 50/50 shank), the 8 driven correctives, the IK closure procedure | MPFB default bone names kept; `Corrective Smooth` placed after `Armature`, before `Subdivision`; Preserve Volume on |
| Materials library | `Skin.Body` regional values (§5.1), `Leg.Masks.png`, `Leg.Relief.exr` | the shared skin node group from spec 01 and its base colour #b98670 for the face; legs use #c39a80 |
| Eval | V5 overlay tool (silhouette mask + clearance report), `measure_leg()` | hero camera (0, −4500, 600), 46 mm, rot (93.9°, 0, 0) |

### 10.2 Questions for the client
1. **Proportions:** confirm "build as drawn" — rest hip joints at 851 mm (posed 829), femur 325 mm (74 % of a real one), long torso above — rather than the normalised fallback (hip 880). The silhouette matches the picture either way only with the first; the second deforms better in deep squats.
2. **Moles and scars on the legs:** none (as the face), or a realistic 2 small moles per leg and a healed kneeling abrasion on the right knee? Default none.
3. **Bare-leg deliverables:** are turntables or closeups of the bare legs wanted (then hair and the V1–V4/V6 renders are deliverables), or internal evidence only?
4. **Knee facing:** 45° to his right for the right knee (our read) versus the analysts' 55° — confirm from the kneepad's projected width.
5. **Game rig:** keep `patella.L/R` and the eight corrective morph targets in the export, or a plain 4-bone leg?
6. **Groin:** no genital bulge modelled under the trousers (nothing shows in the picture) — confirm.
7. **Weight 55/45 right-heavy** (pelvis shifted 40 mm to his right) — confirm, as spec 01 also asks.

### 10.3 Items tagged [VERIFY]
* Per-unit mm gains of `measure-upperleg-height`, `upperlegs-height`, `hip-trans-down`, `measure-*-circ` targets (research_generators lists them, not their gains) — measured by the solver at run time.
* Whether MPFB refits the default rig after later target changes; we refit regardless.
* Vertex count and spacing of the base mesh over the leg and pelvis (≈ 4,000 quads, 20–35 mm assumed).
* Name of spec 01's shared skin node group and `sculpt.py`/`measure.py` function signatures (`soft_inflate(centre, r, amount)`, `soft_move(centre, r, vector)`, `slice_measure`) — used as spec 01 describes them.
* MakeHuman UV coverage of the legs (texel density ≈ 2.4 px/mm at 4K assumed).
* MPFB `pelvis.L/R` bone head positions.
* ASIS, PSIS, patella, tuberosity, fibular head and hair-density figures are anatomical estimates (E); ANSUR II carries no direct value for them.
