# Sgt. Alex Morgan — Pose, Proportions and Body Type

**CONVENTION: all "left"/"right" below are the SOLDIER'S OWN left and right** (his left hand, his right shoulder). When the picture side is meant it is written "viewer's left" / "viewer's right". In the reference the soldier faces the camera, so his RIGHT side is on the VIEWER'S LEFT (small x) and his LEFT side is on the VIEWER'S RIGHT (large x).

Source: `/home/user/sgt_morgan/ref/reference_full.png` (1672 x 941). All pixel coordinates are in that FULL image, origin top-left, x to the right, y downward. Crop offsets (found by template matching, MSE < 4): `crop_soldier_full.png` = x2 of box (580,20)-(1020,935); `crop_head_face.png` = x5 of (715,30)-(885,200); `crop_torso_vest.png` = x3 of (630,140)-(990,490); `crop_hands_rifle.png` = x3 of (630,230)-(950,570); `crop_belt_hips.png` = x3 of (630,410)-(990,630); `crop_legs_knees.png` = x3 of (630,550)-(990,830); `crop_boots_feet.png` = x3 of (610,750)-(1010,935); `crop_arm_right_viewerleft.png` = x3 of (600,170)-(770,490); `crop_arm_left_viewerright.png` = x3 of (850,170)-(1000,490).

Method: landmarks read off ruler-gridded Lanczos zooms (x2–x7) of the full image and of the supplied crops, cross-checked with per-row luminance silhouette scans (legs/boots against the bright floor) and PIL colour sampling. Typical landmark uncertainty ±3 px (±0.6 cm) for hard edges, ±8 px for hidden/estimated joints (marked "est.").

---

## 1. Scale, camera and perspective

| Quantity | Value |
|---|---|
| Standing pixel height H_px (top of skull y=20 → his RIGHT sole y=895) | **875 px** |
| Including hair spikes (y=14) | 881 px |
| Pixels per cm | 4.78 (@183 cm) · **4.72 (@185.5 cm)** · 4.65 (@188 cm) |
| cm per pixel | 0.209 · **0.212** · 0.215 |
| Camera horizon (far hangar floor vanishing band) | y ≈ 580–610 → camera height ≈ **0.65–0.70 m** above floor |
| Camera distance / focal (from 12 px sole offset between the two feet) | ≈ 4.3–4.7 m, ≈ 2050 px focal ≈ 45–50 mm full-frame equivalent |
| Consequence | Face is viewed from ≈ 12–14° BELOW (nostrils and underside of jaw visible). Most of the "chin-up" look is camera angle, not head pitch. Vertical lines stay vertical (no camera tilt), so vertical ratios within one depth plane are preserved. |

The RIGHT foot (sole y=895) is the floor datum because it sits at roughly the body's depth; the LEFT foot (sole y=907) is 10–20 cm nearer the camera and is therefore drawn lower.

---

## 2. Vertical landmark table (FULL-image y)

"height /H" = height above the right sole divided by 875. cm columns assume 183 / 185.5 / 188 cm stature.

| Landmark | y px | fraction from skull top | height /H | cm @183 | cm @185.5 | cm @188 | position / note |
|---|---|---|---|---|---|---|---|
| Top of hair spikes | 14 | −0.007 | 1.007 | 184.3 | 186.8 | 189.3 | tallest spike x≈812 |
| Top of skull (hair mass) | **20** | 0.000 | 1.000 | 183.0 | 185.5 | 188.0 | x≈808 |
| Hairline (forehead centre) | 47 | 0.031 | 0.969 | 177.4 | 179.8 | 182.2 | x≈808; temple hairline y≈50 at x≈785 |
| Brow line | 72 | 0.059 | 0.941 | 172.1 | 174.5 | 176.8 | x 790–840 |
| Eye line (pupils) | **78** | 0.066 | 0.934 | 170.9 | 173.2 | 175.5 | R pupil (800,79), L pupil (833,77); IPD 33 px |
| Nose tip | 97 | 0.088 | 0.912 | 166.9 | 169.2 | 171.5 | (819,97) |
| Mouth (lip line) | 109 | 0.102 | 0.898 | 164.4 | 166.6 | 168.9 | (818,109) |
| Chin bottom | **129** | 0.125 | 0.875 | 160.2 | 162.4 | 164.6 | (815,129) |
| Neck base / trapezius line (est., under gaiter) | 170 | 0.171 | 0.829 | 151.6 | 153.7 | 155.8 | gaiter top y≈128 |
| Shoulder line (acromion / pad tops) | **195** | 0.200 | 0.800 | 146.4 | 148.4 | 150.4 | L pad top y=183 (x≈920), R pad top y=192 (x≈665) |
| Shoulder joint centres (est.) | 200 | 0.206 | 0.794 | 145.4 | 147.3 | 149.3 | R (675,200), L (935,200) |
| Butt-stock top-rear corner | 243 | 0.255 | 0.745 | 136.4 | 138.2 | 140.1 | (706,243) |
| Nipple line (hidden, est. from anthropometry) | 252 | 0.265 | 0.735 | 134.5 | 136.3 | 138.2 | behind chest plate |
| Right elbow centre | 328 | 0.352 | 0.648 | 118.6 | 120.2 | 121.8 | (632,328); pad outer point (626,322) |
| Right wrist | 345 | 0.371 | 0.629 | 115.0 | 116.6 | 118.2 | (698,345) |
| Left elbow centre | 352 | 0.379 | 0.621 | 113.6 | 115.1 | 116.7 | (958,352) |
| Left wrist | 440 | 0.480 | 0.520 | 95.2 | 96.5 | 97.8 | (870,440) |
| Vest hem (bottom of mag pouches) | 460 | 0.503 | 0.497 | 91.0 | 92.2 | 93.5 | x 740–890 |
| Magazine bottom | 462 | 0.505 | 0.495 | 90.6 | 91.8 | 93.0 | (783,462) |
| Navel (hidden, est.) | 470 | 0.514 | 0.486 | 88.9 | 90.1 | 91.3 | just below vest hem |
| Waist belt (hidden under hem, est.) | 490 | 0.537 | 0.463 | 84.7 | 85.9 | 87.0 | drop-leg hangers start here |
| Hip joints / greater trochanter (est.) | **505** | 0.554 | 0.446 | 81.6 | 82.7 | 83.8 | R (768,505), L (862,505) |
| Upper thigh strap, right thigh | 523 | 0.575 | 0.425 | 77.8 | 78.9 | 79.9 | black strap y 512–535, x 710–800 |
| Crotch (trouser inseam apex) | **535** | 0.589 | 0.411 | 75.3 | 76.3 | 77.3 | (810,535) ±5 |
| Muzzle tip | 568 | 0.626 | 0.374 | 68.4 | 69.3 | 70.3 | (902,568) |
| Lower thigh strap, right thigh | 576 | 0.635 | 0.365 | 66.7 | 67.6 | 68.5 | y 565–588; left thigh strap y 560–590 |
| Right knee centre | **650** | 0.720 | 0.280 | 51.2 | 51.9 | 52.6 | (727,650); pad y 603–700 |
| Left knee centre | **657** | 0.728 | 0.272 | 49.8 | 50.5 | 51.1 | (890,657); pad y 617–700 |
| Boot collar top (both boots) | 795 | 0.886 | 0.114 | 20.9 | 21.2 | 21.5 | R x 716–767, L x 886–952 |
| Right ankle (malleolus) | **855** | 0.954 | 0.046 | 8.4 | 8.5 | 8.6 | (732,855) |
| Left ankle (malleolus) | 858 | 0.958 | 0.042 | 7.7 | 7.8 | 7.9 | (928,858) |
| Right sole (floor datum) | **895** | 1.000 | 0.000 | 0 | 0 | 0 | toe (631,884), heel (767,892) |
| Left sole (nearer camera) | 907 | 1.014 | −0.014 | — | — | — | heel (910,897), toe (950,907) |

## 3. Horizontal landmark table (FULL-image x)

| Landmark | x px, his RIGHT side (viewer's left) | x px, his LEFT side (viewer's right) | centre / width px | width cm @185.5 |
|---|---|---|---|---|
| Head: visible right ear outer → far left cheek (3/4 view), y≈88 | 762 | 850 | centre 806, width 88 | 18.7 |
| Face midline (nose/chin) | — | — | x 815–819 (shifted toward his left = head yaw) | — |
| Neck incl. gaiter, y≈150 | 772 | 852 | 80 | 17.0 |
| Shoulder outer points incl. pads, y≈205 | **640** | **962** | centre 801, width 322 | 68.3 |
| Shoulder outer points est. without pads (deltoid) | 655 | 950 | 295 | 62.5 |
| Shoulder joint centres | 675 | 935 | 260 | 55.1 |
| Chest incl. vest, y≈300 | 690 | 920 | 230 | 48.8 |
| Elbows | 632 | 958 | 326 | 69.1 |
| Wrists | 698 | 870 | — | — |
| Waist under vest hem, y≈470 | 745 | 890 | 145 | 30.7 |
| Hips, body only (excl. drop-leg pouches), y≈500 | **735** | **900** | centre 817, width 165 | 35.0 |
| Hips incl. drop-leg holster/pouch, y≈520 | 665 | 950 | 285 | 60.4 |
| Hip joints (est., ~20 cm apart) | 768 | 862 | 94 | 19.9 |
| Crotch | — | — | 810 | — |
| Knee centres | 727 | 890 | 163 apart | 34.6 |
| Ankle centres | **732** | **928** | 196 apart | 41.6 |
| Right foot toe / heel | toe 631, heel 767 | — | length 136 (profile) | 28.8 |
| Left foot toe / heel | — | toe 950, heel ≈910 | seen head-on, width 84 | 17.8 (incl. perspective) |

Body centre-line: head centre ≈806, shoulder midpoint 801, vest centre column ≈797, hip centre 817, crotch 810, stance midpoint 830. The figure is essentially frontal; pelvis/legs sit 10–15 px to the viewer's right of the shoulders because the LEFT hip/leg is rotated toward the camera.

---

## 4. Segment lengths, ratios and body type

Head unit = 109 px (skull top → chin).

| Segment | px | /H | heads | cm @183 | cm @185.5 | cm @188 | standard adult male (comparison) |
|---|---|---|---|---|---|---|---|
| Head height (skull → chin) | 109 | 0.125 | 1.00 | 22.8 | 23.1 | 23.4 | 23–24 ✔ |
| Head incl. hair spikes | 115 | 0.131 | 1.06 | 24.1 | 24.4 | 24.7 | — |
| Face (hairline → chin) | 82 | 0.094 | 0.75 | 17.1 | 17.4 | 17.6 | 18–19 ✔ (slightly high hairline) |
| Forehead (hairline → brow) | 25 | 0.029 | 0.23 | 5.2 | 5.3 | 5.4 | ≈ 6 |
| Brow → nose tip | 25 | 0.029 | 0.23 | 5.2 | 5.3 | 5.4 | ≈ 6 |
| Nose tip → chin | 32 | 0.037 | 0.29 | 6.7 | 6.8 | 6.9 | ≈ 6.5 (long lower face, strong jaw) |
| Neck (chin → shoulder line) | 66 | 0.075 | 0.61 | 13.8 | 14.0 | 14.2 | 10–12 → slightly long neck (gaiter hides it) |
| Shoulder line → nipple (est.) | 57 | 0.065 | 0.52 | 11.9 | 12.1 | 12.2 | — |
| Shoulder line → crotch | 340 | 0.389 | 3.12 | 71.1 | 72.1 | 73.1 | ≈ 66 (0.35 H) → **long torso** |
| Chin → crotch (torso incl. neck) | 406 | 0.464 | 3.72 | 84.9 | 86.1 | 87.2 | ≈ 76 (0.41 H) → **+13 %** |
| Hip joint → knee (thigh, est.) | 145 | 0.166 | 1.33 | 30.3 | 30.7 | 31.2 | ≈ 42–45 (0.245 H) → **short thigh** |
| Crotch → knee | 115 | 0.131 | 1.06 | 24.1 | 24.4 | 24.7 | ≈ 34 |
| Knee → ankle (shank) | 205 | 0.234 | 1.88 | 42.9 | 43.5 | 44.0 | 42–45 ✔ |
| Ankle → sole | 40 | 0.046 | 0.37 | 8.4 | 8.5 | 8.6 | 7–8 ✔ |
| Knee → sole | 245 | 0.280 | 2.25 | 51.2 | 51.9 | 52.6 | 50–53 ✔ |
| Crotch → sole (leg incl. foot) | 360 | 0.411 | 3.30 | 75.3 | 76.3 | 77.3 | ≈ 86 (0.47 H) → **−12 %** |
| Upper arm (shoulder → elbow, L, near in-plane) | 152 | 0.174 | 1.39 | 31.8 | 32.2 | 32.7 | 33–36 ✔ |
| Forearm (elbow → wrist, L, near in-plane) | 124 | 0.142 | 1.14 | 26.0 | 26.4 | 26.7 | 26–28 ✔ |
| Hand (wrist → extended index tip, R, foreshortened) | 76 | — | — | — | 16.0 (true ≈ 19–20) | — | 19–20 |
| Boot length (R, profile, slight foreshortening) | 136 | — | — | — | 28.8 (true ≈ 30–31) | — | EU 44–45 boot |

### Key ratios
* **Head : body = 1 : 8.0** (875/109 = 8.03; 8.1 with hair). Heroic 8-head canon, not the realistic 7.5. Eye line 0.934 H, chin 0.875 H, shoulder line 0.80 H and knee 0.28 H all match a real 185 cm male — upper body and lower legs are anatomically normal.
* **Shoulder breadth : hip breadth = 322 : 165 = 1.95** including shoulder pads; ≈ 1.8 (295:165) without pads. Standard male ≈ 1.35–1.4. Strong V-taper: bare bideltoid ≈ 62 cm (~25 % broader than average), hips 35 cm (average).
* **Waist : hips = 145 : 165 = 0.88**; waist breadth 30.7 cm — lean, athletic.
* **Crotch height is only 0.41 H** (standard 0.47) while the knee is at the standard 0.28 H → the whole shortfall is in the thigh (hip→knee ≈ 31 cm instead of ≈ 43). Torso (chin→crotch) is ≈ 13 % longer than standard. **This is a real property of the drawing** (probable generator artefact, amplified by baggy low-hanging tactical trousers and a long plate carrier whose hem reaches y=460 ≈ 92 cm above the floor).
* Limb thickness: upper arm (sleeve + plates) ≈ 12.7 cm diameter, forearm ≈ 11 cm, wrist ≈ 7.4 cm, thigh (trousers) ≈ 17–19 cm, knee pad ≈ 12 cm wide, calf (trousers) ≈ 15 cm, trouser cuff ≈ 11 cm, boot shaft ≈ 14 cm. Underlying body: muscular-athletic mesomorph, roughly 88–95 kg at 185 cm; not bodybuilder-bulky — the bulk is armour.

### Recommendation for the modeller (flagged decision)
Build the body as drawn for silhouette fidelity but keep joints placeable:
1. Keep head (23 cm), shoulder height (148 cm), chin (162 cm), knee (52 cm) and ankle (8.5 cm) heights exactly as measured.
2. Put hip joints at y≈505 (≈83 cm above floor), i.e. a long torso and a 31 cm femur. If the rigger rejects a femur that short, the compromise is hip joints at y≈480 (88 cm, femur 36 cm) with the trouser crotch seam still modelled hanging low at y≈535 and the vest hem at y≈460 — this keeps the drawn silhouette while giving a more deformable thigh. Do NOT lengthen the legs to the standard 0.47 H: the whole lower half of the reference would be off.
3. Shoulder pads add ≈ 13 px (3 cm) per side; model the bare deltoid outer surface at x≈655 / x≈950.

---

## 5. Pose overview

Relaxed "patrol / stock-on-chest" carry: standing nearly square to the camera, weight on both nearly straight legs, rifle held diagonally across the front of the body (butt against the right pectoral, muzzle down toward the left knee), right hand on the pistol grip with the index finger straight along the receiver, left hand wrapped over the handguard. Head turned toward his LEFT (nose toward the viewer's right) looking into the middle distance. Left foot forward and pointed at the camera, right foot turned out to a near-full side profile.

Rotation directions in words (independent of sign convention):
* Pelvis: turned ≈ 10° toward his RIGHT (his LEFT hip is nearer the camera).
* Chest: ≈ 5° toward his RIGHT (left shoulder marginally nearer camera; chest plate reads almost frontal).
* Head: turned ≈ 22° toward his LEFT relative to the camera axis → ≈ 27° relative to the chest, ≈ 32° relative to the pelvis. Chin level to very slightly raised. Roll ≈ 0 (pupils (800,79) and (833,77): 2 px ≈ 2°, negligible).
* Gaze: straight out of the head (irises centred in the lids), perhaps 3–5° further left and up.

## 6. Joint-angle table (rig-ready)

Frame: Blender, +Z up; rest pose faces −Y (toward the camera at −Y); +X is the character's LEFT. Angles are rotations of each bone relative to a standard **A-pose rest** (arms hanging ~15° from the torso, palms toward the thighs, legs straight, feet forward), given in anatomical terms:

* **Pitch** = rotation about the lateral (X) axis: + = flexion / bend or nod forward; for shoulder and hip, + = limb swings forward (toward camera).
* **Yaw** = rotation about the vertical (Z) axis, or about the bone's long axis for limbs (= internal/external rotation): + = turn toward his LEFT; for limbs + = internal rotation.
* **Roll** = rotation about the forward (Y) axis: + = tilt toward his LEFT; for limbs = abduction (+ = away from the body midline).

All values ±5° unless stated; items marked ~ are ±10°.

| Bone | Pitch (flex+ / ext−) | Yaw (turn-left+ / int-rot+) | Roll (tilt-left+ / abd+) | Evidence / note |
|---|---|---|---|---|
| Root / pelvis | +2 (slight anterior tilt) | **−10** (turned to his right; left hip to camera) | 0 (iliac crests level, y≈490 both sides) | Left foot forward, right foot turned out, drop-leg pouches at equal height |
| Spine lower (lumbar) | −2 (slight extension) | +3 | 0 | Upright, proud posture |
| Spine upper (thoracic / chest) | −3 (chest lifted) | +2 (net chest yaw ≈ −5 world) | 0 | Chest plate near frontal, centre x≈797 |
| Neck | −2 | +12 | 0 | Gaiter hides it; carries part of the head turn |
| Head | **−3** (chin up; most of the visible "up" is camera angle) | **+15** (net head yaw ≈ +22 world, +27 vs chest) | 0 to −2 | Right ear fully visible, left ear hidden; nose tip x=819 vs eye midpoint 816.5 |
| Eyes | +3 up | +4 further left | — | irises centred |
| R clavicle | protraction +8 (shoulder reaches forward) | — | elevation +2 | R shoulder slightly forward vs L |
| R shoulder (upper arm) | **−8** (elbow slightly behind body line) | **+45** internal rotation (forearm swings across the body) | **+20** abduction (elbow 43 px lateral over 128 px drop = 18° in-plane) | Upper-arm vector (675,200)→(632,328) |
| R elbow | **flex 95–100** | — | — | Forearm (632,328)→(698,345) nearly horizontal in image, strongly foreshortened (68 px vs ~125 true) → forearm points toward camera and medially |
| R forearm | pronation ~70 (back of hand faces camera / up-left) | | | |
| R wrist | extension +12, ulnar deviation +10 | | | Hand drops onto a grip that points down-left |
| L clavicle | 0 | — | −3 (slightly depressed; arm hangs) | |
| L shoulder (upper arm) | **+12** (elbow a little in front of body line) | +20 internal rotation | **+8** abduction (elbow 23 px lateral over 152 px) | Upper arm (935,200)→(958,352), almost in image plane (154 px ≈ 32.6 cm true) |
| L elbow | **flex 55** (included angle ≈ 125°) | — | — | Forearm (958,352)→(870,440) at 45° down-medial, 124 px ≈ full length → in plane |
| L forearm | pronation ~40 (semi-prone, thumb up) | | | |
| L wrist | flexion +10, radial deviation +10 | | | Aligns palm to the 57° handguard |
| R hip | **−5** (leg slightly behind pelvis) | **−45** external rotation (knee pad faces ~45° to his right) | **+14** abduction (thigh (768,505)→(727,650) leans 16° out) | |
| R knee | **flex 15–20** | tibial external rotation ~ −20 | — | Shank vertical in frontal plane while the thigh leans out → bend lies mostly in the rotated sagittal plane; trousers bunch above the pad |
| R ankle | 0 (plantigrade) | foot further ext. rot. ~ −20 | eversion ~+3 | Foot flat, full contact |
| R foot direction | — | **toe points 85–100° to his right of the camera axis** (near pure profile; toe at x=631) = 75–90° out from pelvis-forward | — | Boot length 136 px vs ~145 true → ≤ 20° out of image plane; toe y 884 vs heel y 892 is mostly toe-spring |
| L hip | **+8** (leg slightly forward: foot 10–20 cm nearer camera) | **−22** external rotation | **+10** abduction (thigh (862,505)→(890,657) leans 10° out) | |
| L knee | **flex 8–10** | 0 | — | Thigh and shank collinear in frontal plane (10° and 11°); pad faces camera |
| L ankle | 0 | — | 0 | Foot flat; sole slopes heel y 897 → toe y 907 from perspective only |
| L foot direction | — | **toe points 15–20° to his left of the camera axis** ≈ 25–30° out from pelvis-forward | — | Toe box x≈940–950 vs ankle x 928 |

### Stance numbers
| Quantity | px | cm @185.5 |
|---|---|---|
| Ankle-to-ankle lateral separation | 196 | **41.6** |
| Heel-to-heel | 145 | 30.8 |
| Toe-to-toe (R toe x631 ↔ L toe x950) | 320 | 67.8 |
| Depth offset (L foot nearer camera) | 12 px sole offset | **10–20 cm forward** |
| Knee-to-knee | 163 | 34.6 |
| Hip-joint-to-hip-joint (est.) | 94 | 19.9 |

Stance width ≈ 0.75× padded shoulder width, ≈ 1.2× hip width — a stable, slightly open stance.

### Weight distribution and centre of mass
* Both knees nearly straight; pelvis not visibly shifted; body centre-line x≈812 sits between ankles at 732 and 928 → lever rule gives **≈ 58 % on the RIGHT (side-turned, rear) foot, ≈ 42 % on the LEFT (forward) foot**. Call it 55/45 right-heavy; a 50/50 pose also reads correctly.
* Whole-body COM ≈ (812, 430) in the image ≈ 98 cm above the floor (0.53 H), a little in front of the hip joints, pulled forward and up by the plate carrier and the 3–4 kg rifle held in front of the chest. Ground projection of the COM ≈ x 812, roughly at the right ankle's depth, inside the support polygon, slightly toward the right foot and toward the heels.
* Posture: spine erect with 2–3° thoracic extension (chest open), shoulders back and level (right pad top is 9 px lower only because that pad is smaller/tilted), head carried high.

---

## 7. Hands and rifle

### Rifle placement (AR-12 carbine, assume ≈ 85 cm overall with collapsed stock)
| Feature | Image coords | Height above floor (cm) | Note |
|---|---|---|---|
| Butt-plate top-rear corner | (706, 243) | 138 | Over the RIGHT pectoral, 10 cm below the acromion line, 14 cm medial of the shoulder-pad outer edge (x 640), just medial/below the vest's right shoulder strap (x 740–760) |
| Butt-plate toe | (683, 296) | 127 | Butt plate 61 px ≈ 13 cm tall in projection, raked (not perpendicular to the bore) |
| Stock cheek-rest top edge | (706,243)→(745,300) | — | 55.6° below horizontal = stock axis |
| Receiver / pistol-grip region | (735–770, 330–400) | 105–120 | Grip itself hidden behind the right hand at ≈ (735–748, 385–410) |
| Magazine | (762–795, 365–462), bottom (783,462) | 92 at bottom | Hangs down-left (toward his right hip), perpendicular to the bore in the image plane |
| Handguard | (790,400) → (870,515) | 105 → 80 | M-LOK-style slots visible; left hand at its mid-point |
| Visible barrel / muzzle device | (862,510) → **(902,568)** | 69 at tip | Barrel direction 55.8° below horizontal |
| Bore axis (butt centre (695,268) → muzzle (902,568)) | 364 px projected = 77 cm | — | **57° below horizontal toward his LEFT in the image plane**; projected 77 cm vs ≈ 85 cm true → **muzzle ≈ 25° toward the camera (out of the image plane)** |

Muzzle direction as angles (camera axis = forward): **pitch ≈ 50° downward, azimuth ≈ 50° to his LEFT of the camera axis** (≈ 55° left of chest-forward, ≈ 60° left of pelvis-forward). Unit vector in Blender world terms (character faces −Y, +X = his left, +Z up): ≈ (+0.49, −0.42, −0.76).

Cant: the rifle's own "up" (top rail / optic side) points up-and-to-his-left in the image, perpendicular to the bore within the image plane; the magazine points down-and-to-his-right. Hence the **rifle's RIGHT side (ejection-port side) faces the camera squarely**.

Distance from body (from arm foreshortening and overlaps): butt plate in CONTACT with the vest over the right pectoral (0–3 cm); receiver/grip ≈ 12–15 cm in front of the chest plate at sternum/upper-abdomen height; magazine bottom ≈ 15 cm in front of the lower abdomen at vest-hem height; handguard mid ≈ 20 cm in front of the left hip; muzzle ≈ 25–35 cm in front of the left thigh, laterally at the thigh's outer edge (x 902 vs thigh 848–930), 69 cm above the floor (≈ 12 cm above the left knee-pad top).

### Right hand — pistol grip
* Hand occupies (690–752, 325–400); wrist/glove cuff at (690–700, 325–350); the forearm arrives from the viewer's left (his right elbow at (632,328)), nearly horizontal and pointing toward the camera.
* Back of the hand (dorsum; hard knuckle plate at 700–725 × 335–365) faces the camera and up-left; the palm wraps the grip's front/his-right face.
* **Index finger fully extended** (trigger discipline): from the MCP knuckle (727,355) to the fingertip (750,398), straight, lying along the right side of the lower receiver / magazine well above the trigger guard, pointing toward the muzzle (down-right in the image). ≈ 50 px foreshortened.
* **Middle, ring, little fingers curled around the front of the grip**: proximal phalanges run down-right from knuckles at ≈ (712,370), (704,380), (697,388); tips wrap behind the grip (hidden). Approx. flexion MCP 85°, PIP 95°, DIP 50°; little finger slightly less.
* **Thumb**: hidden on the far (his-left) side of the grip, wrapped around the back strap, tip roughly at receiver height behind the selector area.
* Wrist: extension ≈ 12°, ulnar deviation ≈ 10°; forearm pronated ≈ 70°.

### Left hand — handguard (overhand wrap, thumb across the top)
* Hand occupies (803–882, 420–497); wrist/cuff at (865–885, 410–440); the forearm arrives from the upper right (his left elbow at (958,352)) at 45°.
* Palm lies on the HIS-LEFT / top face of the handguard (the face pointing up-right in the image), about 60 % of the way from receiver to muzzle, centred ≈ (840, 460).
* **Thumb** draped **across the top of the handguard**, perpendicular to the bore, from MCP ≈ (880,428) to tip ≈ (846,447) (bright glove stud at (850,445)); it does not point along the bore.
* **Four fingers wrapped around to the underside** (his-right / lower-left face): four rounded fingertips visible to the camera, stacked along the handguard at ≈ (806,458), (812,470), (820,483), (828,495) — index uppermost (nearest the receiver), little finger lowest. Flexion ≈ MCP 60°, PIP 85°, DIP 45° (handguard cross-section ≈ 4 cm; fingers close most of the way round).
* Wrist ≈ 10° flexion + 10° radial deviation; forearm semi-pronated (≈ 40°).
* Low confidence: a black sling/strap appears to leave the handguard rear toward the vest's left side at ≈ (850–880, 395–430).

---

## 8. Reference colour samples (PIL, 5×5 mean unless noted; FULL-image coordinates)

| Sample | (x,y) | hex |
|---|---|---|
| Skin, forehead (lit) | (812,60) | #b38475 |
| Skin, his right cheek (warm key side) | (780,100) | #c8927b |
| Skin, his left cheek (cool fill side) | (835,95) | #a48c8f |
| Beard stubble, chin | (815,120) | #6f4c3c |
| Hair, top | (805,30) | #19120d |
| Iris, his left eye (3×3) | (833,78) | #463435 (reads blue-grey in context) |
| Neck gaiter | (800,150) | #7c5646 |
| Vest chest plate | (795,230) | #362b1f |
| Left shoulder pad, lit face | (940,215) | #a6b5c6 |
| Upper-arm sleeve, left | (925,285) | #665d55 |
| Glove, back of right hand | (715,350) | #595552 |
| Glove, left fingertips (shadow) | (815,470) | #1f1b18 |
| Buttstock cheek rest | (725,270) | #908b8b |
| Handguard | (835,450) | #464140 |
| Thigh strap (black webbing) | (750,520) | #1b1a18 |
| Trousers, right thigh (shadow) | (760,600) | #111111 |
| Right knee pad | (722,640) | #32312b |
| Trousers, left calf | (915,760) | #2c2925 |
| Right boot upper | (720,830) | #241f1b |
| Right boot toe cap | (650,870) | #37332f |
| Boot sole edge | (700,890) | #1b1f25 |
| Floor, lit, beside right foot | (600,880) | #988a7c |
| Floor, bright, between feet | (830,880) | #d8c5b2 |
| Floor, contact shadow under right boot | (700,905) | #504a48 |
| Background wall behind head | (740,60) | #111516 |

Lighting note relevant to the pose: key light from the viewer's upper-left / his right-front (right cheek warmer and brighter); cool blue rim/fill from his left (shoulder pad #a6b5c6). Contact shadows directly under both soles confirm flat, full-contact feet.

---

## 9. JSON — key numbers

```json
{
  "convention": "soldier's own left/right; image coords in reference_full.png (1672x941), x right, y down",
  "scale": {
    "H_px_skull_to_right_sole": 875,
    "H_px_incl_hair": 881,
    "skull_top_y": 20, "hair_tip_y": 14, "floor_datum_y_right_sole": 895, "left_sole_y": 907,
    "px_per_cm": {"183": 4.78, "185.5": 4.72, "188": 4.65},
    "head_height_px": 109, "heads_tall": 8.03,
    "camera": {"horizon_y": 595, "height_m": 0.67, "distance_m": 4.5, "focal_px": 2050, "face_viewed_from_below_deg": 13}
  },
  "vertical_landmarks_y": {
    "hair_tip": 14, "skull_top": 20, "hairline": 47, "brow": 72, "eye_line": 78, "nose_tip": 97, "mouth": 109, "chin": 129,
    "neck_base_est": 170, "shoulder_line": 195, "shoulder_joints": 200, "nipple_est": 252,
    "elbow_R": 328, "elbow_L": 352, "wrist_R": 345, "wrist_L": 440,
    "vest_hem": 460, "navel_est": 470, "belt_est": 490, "hip_joints_est": 505, "crotch": 535,
    "knee_R": 650, "knee_L": 657, "boot_collar": 795, "ankle_R": 855, "ankle_L": 858, "sole_R": 895, "sole_L": 907
  },
  "horizontal_landmarks_x": {
    "head_centre": 806, "face_midline": 817, "ear_R_outer": 762, "cheek_L_outer": 850,
    "shoulder_outer_R_pad": 640, "shoulder_outer_L_pad": 962, "shoulder_outer_R_deltoid_est": 655, "shoulder_outer_L_deltoid_est": 950,
    "shoulder_joint_R": 675, "shoulder_joint_L": 935,
    "elbow_R": 632, "elbow_L": 958, "wrist_R": 698, "wrist_L": 870,
    "hip_outer_R": 735, "hip_outer_L": 900, "hip_joint_R": 768, "hip_joint_L": 862, "crotch": 810,
    "knee_R": 727, "knee_L": 890, "ankle_R": 732, "ankle_L": 928,
    "toe_R": 631, "heel_R": 767, "toe_L": 950, "heel_L": 910
  },
  "ratios_of_H": {
    "head": 0.125, "eye_line_height": 0.934, "chin_height": 0.875, "shoulder_height": 0.800,
    "nipple_height_est": 0.735, "navel_height_est": 0.486, "hip_joint_height_est": 0.446, "crotch_height": 0.411,
    "knee_height": 0.280, "ankle_height": 0.046,
    "shoulder_breadth_padded": 0.368, "shoulder_breadth_deltoid_est": 0.337, "hip_breadth": 0.189, "waist_breadth": 0.166,
    "shoulder_to_hip_breadth_padded": 1.95, "shoulder_to_hip_breadth_unpadded": 1.79
  },
  "segments_cm_at_185_5": {
    "head": 23.1, "face_hairline_to_chin": 17.4, "neck": 14.0, "shoulder_to_crotch": 72.1, "chin_to_crotch": 86.1,
    "thigh_hip_to_knee": 30.7, "shank_knee_to_ankle": 43.5, "ankle_to_sole": 8.5, "knee_height": 51.9, "crotch_height": 76.3,
    "upper_arm": 32.2, "forearm": 26.4, "hand_true_est": 19.5, "foot_true_est": 30.5,
    "bideltoid_padded": 68.3, "bideltoid_unpadded_est": 62.5, "chest_with_vest": 48.8, "waist": 30.7, "hips": 35.0,
    "upper_arm_dia": 12.7, "forearm_dia": 11.0, "wrist_dia": 7.4, "thigh_dia_trousers": 18.0, "knee_pad_width": 11.8, "calf_dia_trousers": 15.4, "cuff_dia": 10.8
  },
  "anthropometric_flags": {
    "torso_vs_standard_pct": 13, "crotch_height_vs_standard_pct": -12, "thigh_vs_standard_pct": -28,
    "note": "upper body and shank normal; thigh short / torso long as drawn; see section 4 recommendation"
  },
  "pose_deg": {
    "frame": "Blender: +Z up, rest faces -Y (camera at -Y), +X = his left. pitch+ = flex forward, yaw+ = turn to his left / internal rot, roll+ = tilt to his left / abduction. Relative to A-pose rest.",
    "pelvis": {"pitch": 2, "yaw": -10, "roll": 0},
    "spine_lower": {"pitch": -2, "yaw": 3, "roll": 0},
    "spine_upper": {"pitch": -3, "yaw": 2, "roll": 0},
    "neck": {"pitch": -2, "yaw": 12, "roll": 0},
    "head": {"pitch": -3, "yaw": 15, "roll": -1, "world_yaw_total": 22},
    "eyes": {"pitch_up": 3, "yaw_left": 4},
    "clavicle_R": {"protraction": 8, "elevation": 2},
    "clavicle_L": {"protraction": 0, "elevation": -3},
    "shoulder_R": {"flexion": -8, "abduction": 20, "internal_rotation": 45},
    "elbow_R": {"flexion": 97},
    "forearm_R": {"pronation": 70},
    "wrist_R": {"extension": 12, "ulnar_deviation": 10},
    "shoulder_L": {"flexion": 12, "abduction": 8, "internal_rotation": 20},
    "elbow_L": {"flexion": 55},
    "forearm_L": {"pronation": 40},
    "wrist_L": {"flexion": 10, "radial_deviation": 10},
    "hip_R": {"flexion": -5, "abduction": 14, "external_rotation": 45},
    "knee_R": {"flexion": 17, "tibial_external_rotation": 20},
    "ankle_R": {"dorsiflexion": 0, "eversion": 3, "foot_external_rotation": 20},
    "foot_R_toe_direction_deg_from_camera_axis_to_his_right": 92,
    "hip_L": {"flexion": 8, "abduction": 10, "external_rotation": 22},
    "knee_L": {"flexion": 9},
    "ankle_L": {"dorsiflexion": 0, "eversion": 0},
    "foot_L_toe_direction_deg_from_camera_axis_to_his_left": 17,
    "fingers_R": {"index": "extended along receiver", "middle_ring_little_MCP_PIP_DIP": [85, 95, 50], "thumb": "wrapped behind grip, hidden"},
    "fingers_L": {"all_four_MCP_PIP_DIP": [60, 85, 45], "thumb": "across top of handguard, perpendicular to bore"}
  },
  "stance": {
    "ankle_to_ankle_cm": 41.6, "heel_to_heel_cm": 30.8, "toe_to_toe_cm": 67.8, "left_foot_forward_cm": 15, "knee_to_knee_cm": 34.6,
    "weight_right_pct": 55, "weight_left_pct": 45,
    "com_image_xy": [812, 430], "com_height_cm": 98
  },
  "rifle": {
    "butt_top_rear_xy": [706, 243], "butt_toe_xy": [683, 296], "grip_centre_xy_est": [742, 395], "mag_bottom_xy": [783, 462],
    "handguard_from_to": [[790, 400], [870, 515]], "muzzle_xy": [902, 568],
    "bore_angle_in_image_deg_below_horizontal_toward_his_left": 57,
    "muzzle_out_of_plane_toward_camera_deg": 25,
    "muzzle_pitch_down_deg": 50, "muzzle_azimuth_left_of_camera_axis_deg": 50,
    "muzzle_dir_blender_xyz": [0.49, -0.42, -0.76],
    "projected_length_px": 364, "projected_length_cm": 77, "assumed_true_length_cm": 85,
    "butt_height_cm": 138, "muzzle_height_cm": 69,
    "butt_to_chest_cm": 1, "grip_to_chest_cm": 13, "muzzle_to_thigh_cm": 30,
    "cant": "ejection-port (right) side faces camera; rifle 'up' points up-and-to-his-left, perpendicular to bore in image plane",
    "right_hand": "pistol grip, index extended, dorsum to camera",
    "left_hand": "handguard mid, palm on his-left/top face, thumb across top, fingers wrap to underside, fingertips visible"
  }
}
```

---

## 10. Confidence and open questions
* High confidence (±3 px): hair/skull top, eyes, nose, chin, shoulder-pad extents, elbows, wrists, knee pads, boot outlines, soles, rifle butt and muzzle.
* Medium (±8 px): crotch apex (dark fold vs background; read as (810,535) in a brightened x7 zoom), shoulder joint centres under pads, left heel (hidden behind the toe).
* Low / inferred: nipple line, navel, waist belt, hip-joint height (all hidden under the plate carrier or trousers), depth offsets (from foreshortening and the 12 px sole offset), out-of-plane angles (±10°).
* Decision needed upstream: follow the drawn long-torso / short-thigh proportions (recommended, §4) or normalise the thigh. Everything else in the figure is anatomically standard at 8 heads tall.

---

## Errata (consolidator)

Corrections after cross-checking against the other analyst notes and re-sampling `reference_full.png`. The body of this file is unchanged; `analysis_consolidated.md` carries the agreed values.

1. **§2 / §9 "Vest hem (bottom of mag pouches) y=460 ≈ 92 cm" and §4 "a long plate carrier whose hem reaches y=460".** Wrong object. Luminance profiles show the front mag-pouch bottoms at y≈334 and the plate carrier's bound hem at y≈395–400 (≈105 cm above the floor); ≈19 cm of trousers/shirt are exposed between the hem and the belt (y≈490). y≈460 is the bottom of the RIFLE magazine. The long-torso / short-thigh conclusion is unaffected (it rests on the crotch and knee landmarks).
2. **§7 "Magazine (762–795, 365–462), bottom (783,462)".** x-range wrong: that box is the lower receiver/magwell. The magazine spans x≈725–775, y≈400–462 — magwell top (770,405), baseplate centre (748,455), outer corner (731,445) (weapon note; confirmed by luminance scan at y=430–458, no magazine pixels at x>780).
3. **§8 colour table — four mislabelled samples.** (805,30) "Hair, top #19120d" is the dark background/gap above the hair spikes (lum 11; the hair mass starts at y≈16–20); use the face note's hair percentiles (shadow #30241c, mid #614d42, highlight #aa7e6e). (725,270) "Buttstock cheek rest #908b8b" is the specular on the exposed buffer tube (re-sampled #aba6a6, lum 204); the stock body is #3d3733, lit cheek #5e4f44 at (725,290). (795,230) "Vest chest plate #362b1f" is the dark slot/recess at the admin panel's lower edge; the panel median is #7e715f (highlight #a09486), the vest Cordura #463e34. (940,215) "Left shoulder pad, lit face #a6b5c6" is the EMBLEM PLATE on the left pauldron (#97a6b9 re-sampled; gear note #b3c2d6 at (942,212)); the pauldron body itself reads #767475 / #464a4f there.
4. **§8 Iris "(reads blue-grey in context)".** Withdrawn. Both irises contain zero blue-hue pixels (right mean #5d3e34, left #493735, R/B 1.4–1.8). They are dark warm brown-grey; see the face note §5 (albedo #5b4a3e). Do not model blue eyes.
5. **§7 "Low confidence: a black sling/strap ... at (850–880, 395–430)".** Not a sling — the weapon analyst's zooms identify the left glove's gauntlet cuff and the vest's dark side. No sling is present.
6. **§2 Eye line y=78, IPD 33 px.** Face note reads y=77, IPD 31 px (iris centres (800,77) / (831,77)). Consolidated: IPD 32 ±1 px, eye line y≈77.
7. **§5 Head yaw ≈22° world.** Face note reads ≈17° (12–22). Consolidated ≈20° ±5° to his left relative to the camera axis.
8. **§1 Camera (horizon 580–610, height 0.65–0.70 m).** The lighting note's fuller solution (horizon ≈615, range 585–650; height 0.60 m, range 0.54–0.67; 46 mm at 4.5 m; pitch +3.9°) is adopted; the two are compatible.
