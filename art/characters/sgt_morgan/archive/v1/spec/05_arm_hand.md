# Part 05 — Arms and hands (upper arm, elbow, forearm, wrist, hand; skin, hair, nails, the two grips, rig)

Status: draft 1 (spec writer), 2026-10-06. Owner script: `scripts/parts/05_arm_hand.py` (plus the shared `scripts/lib/sculpt.py`, `scripts/lib/measure.py`, `scripts/lib/corrective.py` from specs 01 and 03, and a new `scripts/lib/grip.py`). Object prefix `Arm.<L|R>.*`, `Hand.<L|R>.*`. Vertex groups `arm_*`, `hand_*`. Shape keys `Arm.Sculpt`, `Hand.Sculpt`, `Arm.Corr.*`, `Hand.Corr.*`.

Conventions (from `CLAUDE.md`): millimetres in this spec, metres in Blender; world frame **W**: origin on the floor midway between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT = viewer's right**. Every "left/right" is the soldier's own. Two local frames are used for the tables:

* **Hand frame H** (one per hand): origin at the centre of the carpus on the distal wrist crease; **d** = distal along the third metacarpal, **n** = dorsal (palm → back of the hand), **r** = radial (toward the thumb). Coordinates are written (r, d, n). Every hand table is for the **LEFT** hand; the right hand is `mirror(r)` unless a row says otherwise.
* **Segment stations**: a position along the upper arm or forearm is given as **s %** of the segment length from the proximal joint centre (glenohumeral centre, elbow axis), and around the segment as a **clock position in the anatomical position** (arm hanging, palm forward): 12 = anterior (flexor side), 3 = lateral (radial side of the forearm), 6 = posterior, 9 = medial (ulnar).
* **Joint angles** are anatomical: shoulder flexion (+ forward) / abduction (+ away from the trunk) / internal rotation (+); elbow flexion (0 = straight); forearm pronation (0 = thumb up, 90 = palm down); wrist flexion (+) / extension (−) and radial (+) / ulnar (−) deviation; finger MCP flexion and abduction (+ away from the middle finger), PIP, DIP; thumb CMC palmar abduction and flexion, MCP, IP. **The MPFB rest pose is not an A-pose with hanging arms** (measured in `renders/research/mpfb_default.blend`: upper arm abducted 41.3° from vertical, elbow already bent 45.7°, forearm pointing forward-down); so the pose is defined in §7.3 by **segment direction vectors in W**, and the anatomical angles are derived checks, not the inputs.

Facts tagged **[measured]** were read from the reference or from the research `.blend`; **[sourced]** come from `notes/research_dimensions.md` (ANSUR II "Tight" column, n = 30 men 1830–1870 mm, 82–85 kg, or a cited product page); **[estimated]** are anatomical estimates by the author. Anything that depends on a neighbour spec that does not yet exist carries `[VERIFY: <part>]`.

---

## 1. Purpose and acceptance

### 1.1 What this part is
Both arms from the glenohumeral joint centre to the fingertips: humerus segment with the distal half of the deltoid, elbow, forearm, wrist, hand with five fingers and ten nails; the skin of those regions (colour zoning, creases, veins, tendons, callus, friction ridges); the terminal and vellus hair of the arms and hands; the arm, wrist and finger bones of `Morgan.Rig` with their weights and twist split; the two hero grips (right hand on the pistol grip with the index finger extended along the receiver, left hand overhand C-clamp on the handguard); the corrective shape keys at the elbow, forearm, wrist and knuckles; and the attachment frames that the gloves, the sleeve cuffs, the forearm guards, the elbow caps and the rifle use. In the hero render **no skin of this part is visible**: the gloves cover the hands to 30 mm above the wrist, the sleeves cover the arms to the glove cuff, the forearm guards cover most of each forearm. The bare arm is built anyway because (a) the client requires it as the foundation of the method, (b) the glove is a 1.2 mm skin over this hand — every finger length, knuckle position and nail ridge of the glove is the hand's, (c) the forearm guard, sleeve cuff and elbow cap are sized from these girths, (d) the grips can only be right if the hand inside the glove is right, and (e) the hands are, with the face, the skin that any future closeup will show.

### 1.2 What "perfect" looks like
A critic who knows hands, at a 2048 px closeup of the bare hand, cannot name a dimension wrong by more than the tolerances in §8.2; sees five fingers of correct relative length (middle, then ring ≈ index, little reaching the ring's DIP crease, thumb tip reaching the index PIP when adducted), oval not round in section, each with one palmar crease at the MCP, two at the PIP, one at the DIP, dorsal knuckle wrinkles over the PIP, loose knuckle pads over the MCP; sees ten nails with a nail fold, a visible free edge of about 1 mm (a soldier's, not a model's), a lunula on the thumb and index, pink bed through a translucent plate and a transverse curve that wraps the fingertip; sees the four extensor tendons and the dorsal venous arch as relief that catches light, not as painted lines; sees a thenar eminence, a hollow palm, the three palmar creases and friction ridges that are only visible at macro scale; sees callus where a rifleman has it (the heads of metacarpals 2–5 on both palms, the web between the right thumb and index); sees sparse dark hair on the forearm's extensor side, a few hairs on each proximal phalanx, nothing on the palm. In the hero pose the right index finger lies dead straight along the lower receiver with the pad touching it, the three curled fingers close on the grip without a gap or a poke-through, the left thumb lies across the top rail and exactly four fingertips show under the handguard at the reference's pixels; the elbows land where the picture has them; nothing twists like a candy wrapper at the wrist; the elbow neither collapses nor balloons; no finger passes through another or through the rifle. Nothing waxy, nothing like a mannequin, nothing like a mitten.

### 1.3 Closeup render views (definitions for the render harness in §8.1)
Views V3–V5 are look-dev views of the bare limb in a neutral scene (hand frame H aligned to W: r → +X, d → −Y, n → +Z; the limb in the anatomical position). V1, V2, V6 and V7 are hero-scene views (hero lights, hero pose, rifle and gloves visible).

| View | Camera position (mm) | Target (mm) | Lens / sensor | Compared with |
|---|---|---|---|---|
| V1 Right-hand grip | W (−620, −1500, 1320) | W (−200, −250, 1130) (right hand centre) | 85 mm, 36 mm sensor, 2048² | `ref/crop_hands_rifle.png`, `ref/zoom_arm_rhand_grip_x8.png`: index straight along the receiver, three curled fingers, knuckle plate facing camera, thumb hidden |
| V2 Left-hand C-clamp | W (+320, −1400, 1080) | W (+60, −330, 920) (left hand centre) | 85 mm, 2048² | `ref/zoom_arm_lhand_clamp_x8.png`: thumb across the top rail, four fingertips under the lower facets at 26–28 mm pitch, cuff at the wrist |
| V3 Bare hand dorsal | H (+60, −420, +380) | H (0, 100, 5) | 70 mm, 2048² | §3.4–3.6 tables: knuckle heights, tendons, veins, nails, hair tufts, finger taper |
| V4 Bare hand palmar | H (−40, −420, −380) | H (0, 95, −8) | 70 mm, 2048² | §3.5 creases, thenar/hypothenar, callus zones, friction ridges (DOF f/8 on the index pulp) |
| V5 Forearm and elbow | W-rest, camera 700 mm lateral-anterior of the left elbow, 60 mm | elbow axis centre | 60 mm, 2048² | §3.2–3.3: epicondyles, olecranon, cubital fossa, brachioradialis, ulna ridge, cephalic vein, hair |
| V6 Hero arms | hero camera W (0, −4500, 600), 46 mm, cropped to the boxes (600,170)–(770,490) and (850,170)–(1000,490) | — | as hero | `ref/crop_arm_right_viewerleft.png`, `ref/crop_arm_left_viewerright.png`: elbow and wrist pixels, sleeve/guard/glove silhouette, finger pixels (§8.2 overlay) |
| V7 Glove fit | V1 and V2 repeated with `Glove.*` at 50 % alpha and the skin visible | — | — | clearance map: skin to glove inner surface 0.8–3 mm everywhere, no poke-through |

### 1.4 Pass criteria a critic can score (full list in §8.3)
1. `measure_arm()` and `measure_hand()` (§8.2) within tolerance of §3: segment lengths ±3 mm, girths ±5 mm, finger segment lengths ±1.5 mm, finger widths ±1 mm, nail dimensions ±0.7 mm.
2. Finger order and relative lengths: middle longest; ring within ±2 mm of the index; little tip at 80–90 % of the ring's length; thumb tip at the index PIP level when the thumb lies along the hand.
3. Fingers oval in section (width : thickness 1.15–1.25 at the proximal phalanx), each with its crease set; ten nails with fold, free edge, transverse curvature, no floating or sunk nail.
4. Tendons and veins as relief (0.8–1.5 mm) under rim light; no painted lines.
5. Callus visible as paler, rougher, slightly yellow skin at the §3.6 zones and nowhere else; palm paler and pinker than the dorsum; knuckles darker and redder.
6. Hair: forearm extensor side 8–14 terminal hairs per cm², 6–10 per proximal phalanx (index to ring), none on the palm or middle/distal phalanges; radius 0.03–0.04 mm, dark brown.
7. Right grip: index finger straightness ≤ 8° total flexion over the three joints, pad within 1.5 mm of the receiver's right face; middle, ring and little pulps within 1 mm of the grip, penetration ≤ 0.3 mm; thumb pulp on the grip's left face.
8. Left grip: thumb crossing the top rail at reference pixel (850,445) ± 4 px; four fingertips at (806,458) (812,470) (820,483) (828,495) ± 4 px each; no fifth tip, no palm visible below the handguard.
9. V6 overlay: right elbow at (632,328) ± 6 px, left elbow at (958,352) ± 6 px, right wrist (698,345) ± 5, left wrist (870,440) ± 5; the gloved silhouette IoU against the glove masks ≥ 0.85.
10. Deformation: wrist circumference change under 70° pronation ≤ 4 %; elbow crease forms at 90° flexion with no self-intersection; knuckle MC heads become more prominent (+2 mm) when the fingers flex 85°.
11. No waxy or glowing SSS on the fingers: finger shadow side ≥ 1.5 stops darker than the lit side under the look-dev key.

---

## 2. Reference observations

### 2.1 What the image shows about this part
All coordinates are full-image pixels (1672 × 941). Scale at the figure's plane 4.72 px/cm = 2.12 mm/px (consolidated "Agreed scale"); **the hands are 200–300 mm nearer the camera than the body plane, so at their depth the scale is ≈ 5.0 px/cm (camera distance 4.5 m, lighting analyst)**. Pixel → W: X = (px − 812) × 2.12 × f, Z = (895 − py) × 2.12, with f = 1.0 at the body plane and 1.06 at the hands.

| Observation | Pixels | Derived for this part | Source |
|---|---|---|---|
| Shoulder joint centres | R (675,200), L (935,200) | GH centres hero ≈ W (−290, —, 1472) and (+261, —, 1472); rest symmetric at **±272** (bare bideltoid 625 mm minus 40 mm per side) | consolidated §1; my derivation |
| Right elbow / left elbow | (632,328) / (958,352) | W (−382, Y_e, 1201) / (+310, Y_e, 1151); the right elbow pixel is the forearm guard's elbow band, the joint is inside it | consolidated vertical landmarks |
| Right wrist / left wrist | (698,345) / (870,440) | W (−242, —, 1165) / (+123, —, 964) at f 1.06 | pose note §2 |
| Upper arm, left (near in-plane) | 154 px shoulder → elbow | 326 mm projected → with a 340 mm humerus the arm is 16° out of plane (forward) ✓ flexion +12 | pose note §4, my check |
| Upper arm, right | 294 mm projected (106 lateral, 274 drop) | 30° out of plane for a 340 mm humerus — **more than the −8° flexion in the pose note; see §2.3 (a)** | my check |
| Forearm, right | 68 px (144 mm) elbow → wrist | 58° out of plane → forearm points at the camera; the wrist is ≈ 230 mm nearer the camera than the elbow | pose note §6 |
| Forearm, left | 124 px (263 mm) | 13° out of plane; the hand is 60 mm nearer than the elbow | pose note §6 |
| Right hand box | 690–752 × 325–400 | 62 px → 124 mm (gloved hand seen obliquely from the dorsum, ulnar border to the index DP) | consolidated "Hands" |
| Left hand box | 803–882 × 420–497 | 79 × 77 px ≈ 158 × 154 mm (thumb across, fingertips under) | consolidated "Hands" |
| Right index finger | MCP (727,355) → tip (750,398), 49 px | 98 mm projected for a gloved index of ≈ 100 mm from the MCP axis → the finger lies almost in the image plane, pointing down-right (toward the muzzle) | pose note §7 |
| Index finger width | bright + shadow runs 9–10 px at rows 370–385 on `zoom_arm_rhand_grip_x8` | ≈ 19–20 mm gloved (bare 18 + 2 × 1.2 mm glove) ✓ | my measurement |
| Right curled fingers | PP from (712,370) (704,380) (697,388), running down-right | middle, ring, little MCPs 8–9 px apart = 17–18 mm pitch at the knuckles (gloved, adducted) | pose note §7 |
| Left fingertips | (806,458) (812,470) (820,483) (828,495) | 12.3 px pitch = 24.5 mm in the image along the handguard; the handguard's image-plane shortening is 0.904 → **true pitch ≈ 27 mm → fingers abducted ≈ 4° apart** | my measurement |
| Left fingertip pads | bright runs 17–30 px wide at rows 452–480 | 35–60 mm of each finger shows beyond the handguard's lower facet: the DP and half the MP | my measurement |
| Left thumb | "MCP" (880,428) → tip (846,447), 39 px = 78 mm | too long for a gloved thumb from the MCP axis (≈ 68 mm): the proximal point is the thenar bulge over the CMC; the MCP sits at ≈ (866,436). See §2.3 (c) | my check |
| Glove cuffs | R (690–700, 325–350) under the guard's wrist band; L (865–885, 410–440) #444d5e neoprene with a tab | gauntlet 30 mm tall over the wrist; the sleeve enters the cuff | gear §8 |
| Forearm guards | R x 625–700 (150 mm along the forearm, 85–115 mm tall); L x 875–949 at rows 365–433 | the guard spans the forearm from 30 mm below the elbow axis to the wrist; its inner diameter is this part's forearm girth + 8 mm sleeve/foam | gear §7, my measurement |
| Left elbow cap | (950–968, 335–365) | lateral epicondyle region; 40 × 65 mm cap on the lateral elbow | gear §7.3 |
| Upper arm, clothed | ≈ 127 mm diameter (399 mm circumference) incl. sleeve and bicep band | bare ≈ **350–360 mm** at the band level (s 30–40 %) after subtracting 2 × (1.5 mm shirt + 5 mm band) | pose note §4; my derivation |
| Forearm, clothed | ≈ 110 mm diameter | the guard, not the arm: bare forearm max 300 mm (ANSUR flexed 305) | pose note §4 |
| Wrist, clothed | ≈ 74 mm diameter | the glove cuff + guard band: bare wrist 179 mm circumference, 62 × 42 mm | pose note §4 |

### 2.2 My own colour samples (5 × 5 means, `scripts/.../sample.py` on `reference_full.png`) [measured]
These are lit sRGB values; the glove and sleeve albedos belong to their specs, but the hand's silhouette and shading are judged against them in V1/V2/V6.

| Point | px | Hex | Point | px | Hex |
|---|---|---|---|---|---|
| R glove dorsum centre | (712,345) | #514e4c | L thumb across the rail | (860,436) | #554d4d |
| R knuckle plate, index MCP | (727,352) | #4f4947 | L thumb tip | (848,446) | #5e524f |
| R knuckle plate, middle | (716,358) | #4e4846 | L glove dorsum (in the rifle's shadow) | (848,440) | #0d0e0d |
| R knuckle, ring | (707,366) | #443c38 | L glove cuff neoprene | (872,432) | #444d5e |
| R knuckle, little (dusty) | (699,374) | #594e4a | L cuff tab | (880,425) | #242225 |
| R index proximal phalanx | (735,368) | #4a4542 | L fingertip index | (806,458) | #534b46 |
| R index middle phalanx | (742,382) | #221f1e | L fingertip middle | (812,470) | #342c28 |
| R index tip | (749,395) | #0a0a08 | L fingertip ring | (820,483) | #21201e |
| R middle finger PP | (722,378) | #1c1c1c | L fingertip little | (828,495) | #221f1e |
| R glove cuff | (696,330) | #524138 | L glove rim light | (866,444) | #272c35 |
| R forearm guard, wrist band | (692,340) | #847061 | L forearm guard main | (912,400) | #4c5059 |
| R forearm guard, main lit | (658,328) | #d5c0ad | L guard upper / lower band | (912,375) / (920,428) | #666265 / #4a5a6c |
| R guard groove / elbow band / cam buckle | (665,345) / (632,330) / (636,320) | #796858 / #a28e7c / #baa18e | L guard inset window / ladder-lock | (905,407) / (930,430) | #51565e / #343537 |
| R upper arm sleeve lit / shadow | (690,280) / (660,300) | #232121 / #292323 | L upper arm sleeve / seam rim | (930,300) / (945,300) | #665d58 / #74879a |
| — | | | L elbow bunch / cap fin / cap pad | (950,345) / (958,342) / (960,358) | #20252b / #9aa8b5 / #515c67 |

Reading: the right knuckle plate is lit from the key (upper viewer's-left) with dust on the ulnar knuckles; the right index finger darkens from #4a4542 at the PP to #0a0a08 at the tip because it passes into the receiver's shadow — the finger is **in contact** with the receiver (a gap would show a lit sliver). The left glove's back is almost black because the handguard shades it; its fingertips are lit by the key from below-left of the handguard, brightest on the index (#534b46) and darkening ulnar-wards — the fingertips step away from the key as they go down the handguard, so they are stacked in depth as well as along the bore.

### 2.3 Ambiguities and decisions
(a) **Right humerus foreshortening.** With a 340 mm humerus and the elbow pixel at (632,328), the elbow lies 30° out of the image plane; the pose note's −8° extension puts it only 8° out. Either the drawing's humerus is 14 % short (the AI image is inconsistent elsewhere, weapon §1.1) or the right shoulder is extended −15° to −20° and protracted. **Decision: real bone lengths; the arm is solved by IK with the elbow pole 70 ± 50 mm behind the shoulder plane (Y_e ≈ +70) and the hand on the grip; accept a right-shoulder extension anywhere in −8° to −20°, and require the elbow to land at (632,328) ± 6 px in the V6 overlay.** Report the solved angles. If both cannot be met, the elbow pixel wins over the −8° (the pixel is measured, the angle was inferred).
(b) **Right thumb.** Hidden behind the grip. Decision: wrapped around the grip's left face and back strap, pulp on the left face at the upper third of the grip, tip at the level of the selector boss (gear-side view consistent with a normal pistol-grip hold).
(c) **Left thumb proximal point.** (880,428) is the thenar bulge; the MCP axis is at ≈ (866,436) and the thumb from there to the tip (846,447) measures 46 px ≈ 95 mm projected — still longer than a gloved thumb (68 mm from MCP to tip) unless the thumb is seen along with the thenar; **decision: the thumb crosses the rail perpendicular to the bore with the IP at the rail's near edge and the pad folded 15° over the right side of the rail; the x8 zoom's bright stud at (850,445) is the glove's thumb-tip reinforcement, used as the registration mark.**
(d) **Finger spread on the handguard.** Fingertip pitch 27 mm means the fingers are splayed ≈ 4° each, not stacked tight. Adopted (index +6°, middle +2°, ring −2°, little −6° abduction).
(e) **Right fingers on the grip.** Knuckle pitch 17–18 mm (adducted, tight) and MCP 85 / PIP 95 / DIP 50 from the pose note are kept; the little finger closes 5° less and its MCP sits 4 mm proximal because the grip's front strap is 102 mm tall and the three fingers (3 × 21 mm gloved) plus the index clearance use 85 mm of it, leaving the little finger half on the grip's flared base.
(f) **Index finger height.** The finger's pad lies on the lower receiver's right face above the trigger guard; its MCP is 7 mm higher (dorsal) than the middle MCP because the index is extended while the others flex — this drops the knuckle plate's index boss toward the camera, which the x8 zoom shows (index boss lit brightest).
(g) **Elbow caps.** Only the left is visible. Consolidated says mirror to the right (best) or omit; this part provides the anchor on both elbows and leaves the choice to the armour spec.
(h) **Glove cuff height.** The right cuff is hidden under the guard's wrist band at (692,340); the left cuff shows 30 px (≈ 60 mm) of neoprene between the glove and the guard. Decision: the gauntlet ends 30 mm proximal of the wrist crease on both hands; the sleeve enters it.

---

## 3. Real-world reference

### 3.1 Segment lengths and heights (1855 mm man; the ANSUR Tight column is for 1846 mm, scaled ×1.005)
| Dimension | Value (mm) | Status | Note |
|---|---|---|---|
| Acromial height (rest, standing) | 1523 | sourced (ANSUR 1516 × 1.005) | the torso spec owns the acromion |
| Glenohumeral centre height (rest) | **1475** | estimated (acromion − 48) | matches the picture's 1472 |
| GH centre lateral offset (rest) | **±272** | estimated | §2.1 |
| Acromion → radiale | 351 | sourced | |
| **GH centre → elbow axis (humerus)** | **340** | estimated from 351 − 48 + 37 (radiale sits 37 mm below the GH-to-axis line at the lateral epicondyle) | Winter 0.186 × 1855 = 345; adopt 340 |
| Radiale → stylion | 281 | sourced | |
| **Elbow axis → wrist axis (forearm)** | **270** | estimated (281 − 11, stylion is distal of the axis) | Winter 0.146 × 1855 = 271 |
| Forearm–hand length (elbow to middle tip) | 502 × 1.005 = 505 | sourced | check: 270 + 201 + 30 (carpus offset) ≈ 501 ✓ |
| Hand length (stylion → middle tip) | **201** | sourced | the stylion is 8 mm proximal of the distal wrist crease → crease → tip 193 |
| Palm length (stylion → middle proximal digital crease) | **120** | sourced | crease → MCP3 axis at d 95; digital crease at d 112 |
| Hand breadth (metacarpal heads) | **91** | sourced | |
| Hand breadth including the adducted thumb | 108 | estimated | |
| Hand circumference (metacarpal) | 218 | sourced | → hand thickness at the MC heads 28 |
| Elbow rest height (sitting) / wrist height (standing, arms down) | 250 / 887 | sourced | consistency check of the arm length only |
| Span fingertip to fingertip | 1897 | sourced | consistency check only: with the GH centres at ±272 and the chain 340 + 270 + 193 (wrist axis → middle tip) per side this man's span is ≈ 2 × 272 + 2 × 803 = **2150**, 13 % over ANSUR, which is the drawing's heroic shoulder breadth (bideltoid 625 vs ANSUR 506, biacromial ≈ 530 vs 424), not a long arm — the left upper arm's 326 mm projection confirms the 340 mm humerus (§2.1). Keep the arm lengths, let the torso spec own the breadth |

### 3.2 Upper arm (GH centre → elbow axis = 340; s % from the GH centre)
| Station s | Girth (mm) | Section w × t (mm) | Feature | Status |
|---|---|---|---|---|
| 10 % (axilla level, z ≈ 1440) | 372 | 118 × 112 | deltoid wraps anterior/lateral/posterior; the torso spec owns the axilla fold; blend band s 5–15 % | estimated |
| 30 % (bicep band level, z ≈ 1375) | **358** | 115 × 108 | deltoid insertion V at 3 o'clock; biceps rising at 12; long head of triceps at 7 | estimated from the picture (§2.1) |
| 45 % (biceps belly) | **350** relaxed / 372 flexed | 112 × 105 | biceps peak at 12, 14 mm proud of the humeral line; triceps lateral head at 5, long head at 7; the medial bicipital groove at 10 (neurovascular bundle, 6 mm deep) | ANSUR flexed 342 [sourced]; +9 % for a 90 kg mesomorph [estimated] |
| 65 % | 318 | 103 × 95 | biceps tapering to its tendon; brachialis showing at 2 and 10 as a flat bulge either side of the biceps | estimated |
| 85 % | 290 | 95 × 88 | triceps aponeurosis flat at 6; brachioradialis origin at 3 | estimated |
| 97 % (epicondyles) | **285** | biepicondylar breadth **72**, depth 70 | medial epicondyle 9 o'clock, 5 mm proud, 3 mm more posterior than the lateral; lateral epicondyle 3 o'clock, 3 mm proud | estimated (male biepicondylar 68–72) |

Shape notes: the deltoid insertion is a flat V on the lateral face at s 30–40 %; the biceps belly centre is at s 45 %, 12 o'clock, and migrates proximally 25 mm under 90° flexion (corrective §7.5); the medial face is flatter and paler (never sees sun, no hair). Elbow: olecranon apex at 6 o'clock, 22 mm posterior of the axis, with 15 × 20 mm of loose, darker, wrinkled skin (the olecranon bursa skin) that smooths out at 90° flexion; the cubital fossa is a triangle 30 mm wide at the crease, 40 mm long, 6 mm deep at full extension, bounded by the brachioradialis (lateral) and pronator teres (medial), with the biceps tendon (8 mm wide) and the lacertus fibrosus running into it; the anterior elbow crease sits 12 mm proximal of the axis and is 45 mm long; the carrying angle is 11° (forearm deviates laterally in extension and supination).

### 3.3 Forearm (elbow axis → wrist axis = 270; s % from the elbow axis)
| Station s | Girth (mm) | Section w × t | Feature | Status |
|---|---|---|---|---|
| 5 % | 285 | 92 × 88 | radial head palpable at 3 o'clock; ulna ridge begins at 6–7 | estimated |
| **25 % (maximum)** | **300** | 100 × 85 (wide in the frontal plane) | brachioradialis belly at 1–2 o'clock (the "mobile wad"), extensor mass 3–5, flexor mass 9–12; ulna's subcutaneous border a sharp 2 mm ridge at 7 from the olecranon to the ulnar styloid | ANSUR flexed 305 [sourced], relaxed −2 % |
| 50 % | 262 | 88 × 72 | muscle bellies becoming tendons on the flexor side; the cephalic vein 3–4 mm diameter runs at 2 o'clock | estimated |
| 75 % | 215 | 70 × 55 | FCR and palmaris longus tendons visible at 12 (palmaris present — 85 % of people [estimated]); ECU at 7; EPL/EPB rise toward the snuffbox | estimated |
| 100 % (wrist axis) | **179** | **62 × 42** | radial styloid at 3 o'clock, 8 mm distal of the ulnar styloid; ulnar styloid at 7–8, 6 mm proud (prominent on a lean man); Lister's tubercle dorsal-radial 3 mm proud; dorsal wrist 3 transverse creases on flexion, palmar 2 wrist creases at d 0 and d −10 | ANSUR 179 [sourced] |

Pronation geometry: in the hero pose the right forearm is pronated 70° and the left 40°. The radius crosses the ulna; the dorsal forearm flattens, the ulna ridge stays fixed, the flexor mass rotates toward the ulnar side and the brachioradialis stays lateral (it inserts at the radial styloid, which moves). Skin twist is 0 at the elbow, 30 % of the pronation at s 50 %, 100 % at the wrist (the twist split in §7.2).

### 3.4 Hand — skeleton landmarks in frame H (left hand; fingers straight, each splayed by its rest angle) [estimated, consistent with ANSUR hand length 201, palm 120, breadth 91 and Greiner's finger lengths]
| Landmark | (r, d, n) mm | Landmark | (r, d, n) mm |
|---|---|---|---|
| Radial styloid tip | (+33, −8, −2) | Ulnar styloid tip | (−30, −12, +6) |
| Lister's tubercle | (+8, −2, +18) | Pisiform (palmar-ulnar) | (−28, +6, −14) |
| CMC1 (trapezium–MC1) | (+30, 24, −10) | Hook of hamate | (−20, 25, −14) |
| MCP1 (thumb) | (+60, 56, −22) | IP1 | (+81, 78, −30) |
| Thumb tip (pulp apex) | (+99, 97, −36) | Thumb nail centre | (+93, 92, −26) |
| MCP2 axis | (+25, 93, +3) | MCP3 axis | (+3, 95, +5) |
| MCP4 axis | (−17, 88, +3) | MCP5 axis | (−36, 79, −1) |
| PIP2 | (+29, 133, +2) | DIP2 / tip2 | (+32, 157, +1) / (+34, 181, −1) |
| PIP3 | (+3, 139, +4) | DIP3 / tip3 | (+3, 166, +3) / (+3, 192, +1) |
| PIP4 | (−20, 129, +2) | DIP4 / tip4 | (−22, 155, +1) / (−24, 180, −1) |
| PIP5 | (−41, 113, −2) | DIP5 / tip5 | (−44, 133, −3) / (−47, 156, −5) |
| Dorsal knuckle apex (each MCP) | axis + (0, +3, +7) | Thenar apex | (+42, 50, −22) |
| Hypothenar apex | (−38, 45, −14) | Palm hollow centre | (+2, 60, −8), 6 mm deep |

Derived joint-centre segment lengths (mm): thumb MC1 45 / PP 31 / DP+pulp 27; index MC 68 / PP 40 / MP 24 / DP+pulp 24; middle 65 / 44 / 27 / 26; ring 60 / 41 / 26 / 25; little 54 / 34 / 20 / 23. Rest splay: index +6°, middle 0°, ring −4°, little −8° (in the palm plane), thumb 40° palmar abduction, 25° radial. Hand thickness at the MC3 head 28 (dorsal apex n +12 to palmar pad n −16); at the mid-palm 40 (thenar); carpus 42 at the wrist. Hand breadth 91 from r +43 (index MC head radial border) to r −48 (little MC head ulnar border).

### 3.5 Finger sections, pads, creases and nails [estimated from male ring sizes and the author's anatomy; nails measured against a 201 mm hand]
| Digit | PP mid w × t | MP mid w × t | DP (nail level) w × t | Pulp width | Nail L × W, curvature R | Lunula | Creases (palmar) |
|---|---|---|---|---|---|---|---|
| Thumb | 24 × 20 | — | 21 × 15 | 19 | **16 × 14**, R 9 | 5 mm | MCP 1 crease at d 12 from the axis; IP 2 creases ±2 |
| Index | 20 × 17 | 18 × 15 | 16 × 12 | 15 | 13 × 11, R 6.5 | 3 mm | MCP 1 at +17; PIP 2 at ±2.5; DIP 1 |
| Middle | 21 × 18 | 19 × 16 | 17 × 13 | 16 | 14 × 12, R 7 | 2 mm | same |
| Ring | 20 × 17 | 18 × 15 | 16 × 12 | 15 | 13 × 11, R 6.5 | 1 mm | same |
| Little | 17 × 15 | 15 × 13 | 14 × 11 | 13 | 10 × 9, R 5.5 | none | same |

Nail plate 0.5 mm (thumb 0.6), free edge **1.0 mm** (kept short), nail fold 1.0 mm rim 0.4 mm proud, lateral folds 0.6 mm; the plate begins at 50 % of the DP length and is set 0.4 mm below the surrounding skin; the plate's longitudinal curvature radius ≈ 25 mm (slightly domed); hyponychium pink #c98a7c under the plate; bed through the plate #d4a090; free edge #e9e2d8 translucent. Dorsal skin: PIP dorsum carries 8–12 transverse wrinkles over a 14 mm zone (depth 0.15 mm, pitch 1.2 mm) that stretch flat at 90° flexion; MCP dorsum carries a loose knuckle pad with 3–5 oblique wrinkles when extended; DIP dorsum 3–4 fine wrinkles. Palmar creases: distal palmar crease from (−46, 72) curving distally to (+12, 92), 65 mm long, 0.5 mm deep, 1.5 mm wide; proximal palmar crease from (+5, 85) to the radial border (+44, 58); thenar crease arcing from (+40, 68) round the thenar to (+18, 6); wrist creases at d 0 and d −10 across the full breadth, 0.3 mm; palmar digital creases one per MCP (web level), PIP double, DIP single, 0.3 mm deep. The interdigital webs sit at 45 % of the PP length from the MCP axis (d ≈ 110–113 between index/middle/ring, d 100 ring/little); the first web (thumb–index) is a 50 mm-wide fold from MCP1 to MCP2 with a 25 mm crease at 60° to d.

### 3.6 Skin, callus, veins, tendons and hair by region (the body skin is `Skin.Body`, spec 03 §5.1; face albedo #b98670)
| Region | Albedo | Roughness | SSS scale (m) | Relief / notes | Status |
|---|---|---|---|---|---|
| Upper arm lateral/posterior | #bd8f76 (lightly tanned) | 0.48 | 0.0038 | deltoid V, biceps/triceps grooves (layer A) | estimated |
| Upper arm medial | #cba48c, 2 % cooler | 0.46 | 0.0040 | no hair, visible basilic vein haze | estimated |
| Elbow (olecranon skin) | **#a97a66**, 5 % greyer | 0.66 | 0.0025 | dry, rough, wrinkled 15 × 20 mm; dark lines in the wrinkles | estimated |
| Forearm extensor (dorsal) | #b5836c (tanned) | 0.50 | 0.0035 | hair; cephalic vein +1.0 mm, 3.5 mm wide | estimated |
| Forearm flexor (volar) | #c9a088 (pale) | 0.44 | 0.0035 | FCR/PL tendons +1.2 mm near the wrist; veins 2.5 mm +0.8 mm | estimated |
| Hand dorsum | **#bf8f78** (lives in a glove — a shade paler than the forearm) | 0.50 | 0.0030 | 4 EDC tendons +1.0 mm when extended; dorsal venous arch +1.2 mm; metacarpal veins +0.8 | estimated |
| Knuckles (MCP, PIP dorsum) | #a97765, redder | 0.62 | 0.0025 | thick, wrinkled | estimated |
| Fingers, dorsal | #b98670 | 0.52 | 0.0028 × 0.7 on the DP (thin) | hair tufts on the PP | spec 01 §10 asks for `sss_scale` 0.7 on fingers |
| Fingers, palmar / pulp | #d4a690, pink #d19a86 at the pulp | 0.55 | 0.0030 | friction ridges 0.45 mm pitch, 0.05 mm | estimated |
| Palm | **#d9b09c** (no melanin, pink-yellow) | 0.58 | 0.0032 | creases; ridges 0.5 mm pitch | estimated |
| Callus: MC heads 2–5 (palmar, both hands) | #ddc0a8, 6 % yellower | 0.72 | 0.0025 | 4 ovals 14 × 10 mm at d 100–112, 0.3 mm proud, flaky | estimated (rifle/pull-up callus) |
| Callus: right first web (grip) | #d8baa2 | 0.70 | — | 20 × 12 mm on the web's palmar face | estimated |
| Callus: right index DP radial pad (trigger) | faint, #d6b09a | 0.65 | — | 8 × 6 mm | estimated |
| Nails | see §3.5 | 0.15 plate | — | `Hand.Nail.Plate`, `Hand.Nail.FreeEdge` from spec 01 | |

Veins (dorsum of the hand, all +1.0–1.3 mm relief, 2.5–3 mm wide, soft 2 mm edges, 18 % tint toward #7d8b86 as spec 03): dorsal venous arch convex distally from (−40, 58) through (0, 72) to (+34, 62); dorsal metacarpal veins in the 2nd, 3rd and 4th intermetacarpal spaces from the arch to d 85; cephalic vein leaving the arch at the radial side (+36, 40) over the snuffbox up the radial forearm at 2 o'clock to the cubital fossa; basilic from (−36, 45) up the ulnar-dorsal forearm at 8 o'clock, crossing to the medial elbow; median cubital vein across the fossa from lateral-distal to medial-proximal, 4 mm wide. Tendons: EDC 2–5 radiating from (0, 10, +18) to each MCP, 3 mm wide, +1.0 mm extended / +0.3 flexed; EIP beside EDC2; EPL from Lister's tubercle to the thumb MCP forming the snuffbox's dorsal border with EPB/APL on the radial side (snuffbox a 20 × 12 mm hollow 3 mm deep, visible when the thumb extends); FCR and PL at the volar wrist, 5 and 3 mm wide, +1.2 mm; ECU at the ulnar wrist +0.6.

Hair (terminal; density per cm², length, lie): forearm extensor side (clock 12–6 through 3) **12/cm² at s 20–60 %**, 8 at s 5–20 %, 6 at s 60–90 %, 2 at the wrist; forearm flexor side 1/cm² at s 0–30 %, 0 beyond; upper arm lateral/posterior 3/cm², medial 0; hand dorsum 4/cm² over the metacarpals (d 20–85), 1 distal of the knuckles; proximal phalanges: thumb 10 hairs, index 8, middle 10, ring 9, little 3; none on the middle and distal phalanges, palm or fingers' palmar side. Length 12–25 mm forearm (longest at s 30–50 %), 10–15 upper arm, 6–12 hand and fingers; direction distal with 20° ulnar drift on the forearm, distal-radial on the hand dorsum, distal on the phalanges; radius 0.035 mm root, 0.015 tip; colour root #3a2a1e, tip #5a4030, 20 % of forearm strands sun-lightened to #6a4a30. Vellus 1–2 mm, radius 0.008, 60/cm² on the flexor forearm and the fingers' dorsum (look-dev only).

### 3.7 Gloves (why the hand drives them) [sourced: Mechanix M-Pact size chart, `research_dimensions.md` §8]
Size **Large**: finger length band 138–145 (middle finger from the palm crease to the tip incl. ease), palm circumference 85–98 (around the MC heads, inches × 10 → 216–249 mm; our 218 ✓). Material thicknesses the glove spec must respect over this hand: back stretch knit **1.2 mm**, palm synthetic leather **0.9 mm** + 1.0 mm palm foam (padded M-Pact palm), fingertip reinforcement +0.6 mm, TPR knuckle plate 95 × 35 × 6 mm spanning the four MCP bosses (plate sits on the dorsal knuckle apexes + 2 mm foam), TPR finger-joint pads 14 × 10 × 3 mm over each PIP dorsum, neoprene gauntlet 30 mm tall × 3 mm, hook-and-loop tab. Ease: 1.0–3.0 mm air gap on the dorsum, 0.5–1.5 on the palm, 0 at the pulps (gloves fit snug). The gloved finger therefore measures bare + 2.4 (knit) to + 3.0 mm, e.g. index PP 20 → **22.5 gloved**, middle finger length 97 → **≈ 102 gloved from the MCP axis**.

### 3.8 Rifle contact surfaces this part grips (values from the weapon analysis; the weapon spec owns them) [VERIFY: weapon spec]
| Surface | Dimensions | What touches it |
|---|---|---|
| A2-type pistol grip | 102 mm tall, 32 mm wide, 55 mm front-to-back at the top tapering to 45 at the base, front strap with a finger shelf 22 mm from the top (A2 "nub"), raked 25° back from the receiver normal; serrated sides | right palm (thenar on the left face, hypothenar on the back strap), middle/ring/little pulps on the front strap and left face, thumb pulp on the left face upper third |
| Lower receiver right face above the trigger guard / magwell | flat, 80 mm long from the grip boss to the magwell front; mag-release button Ø 8 mm at (764,384) | right index finger radial pad and PP side, pointing at the muzzle, tip 25 mm short of and 15 mm below the button |
| Handguard | octagonal 45 wide × 55 tall incl. rail, 330 long; the hand at 60 % toward the muzzle (198 mm from the receiver face), lower facets with Ø 13–15 mm holes at 26 mm pitch | left palm on the top-left facets, four fingers wrapping the right and lower-right facets, tips under the lower facet; thumb across the top rail (rail 21 mm wide, slots 5.2 mm at 10 mm pitch) |

---

## 4. Geometry construction plan

Shared steps 1–3 of spec 03 (`proportions.py::create_base()`, `fit_proportions()`, the rig fit) run first; this part never re-topologises or re-UVs the base mesh. All sculpting is by `scripts/lib/sculpt.py` (`soft_inflate(centre, r, amount)`, `soft_move(centre, r, vector)`, `flatten_to_plane`, Gaussian falloff, on a named shape key) and all relief by baked maps and procedural bump. Headless rules from `research_blender_capabilities.md`: real `select_set` + `view_layer.objects.active` before `mode_set`/`parent_set`; `temp_override` for `modifier_apply`, `object.bake` with an active Image Texture node.

### 4.1 Step 1 — Arm and hand proportion targets (`proportions.py::fit_arms()`), measured by `measure.py::measure_arm()` / `measure_hand()` (§8.2)
`TargetService.load_target(basemesh, TargetService.target_full_path(name), weight=w)`; negative values use the `-decr` twin. Names confirmed in `notes/mpfb_targets_and_assets.txt` (arms 50, hands 22).

| Target | Start weight | Purpose | Measured by |
|---|---|---|---|
| `measure-upperarm-length-incr/decr` | solve | GH → elbow 340 | `upperarm01.L` head → `lowerarm01.L` head (joint cubes) |
| `measure-lowerarm-length-incr/decr` | solve | elbow → wrist 270 | `lowerarm01.L` head → `wrist.L` head |
| `measure-upperarm-circ-incr/decr` | solve | 350 at s 45 % | `slice_measure` perpendicular to the humeral axis |
| `measure-wrist-circ-incr/decr` | solve | 179 at the wrist axis | `slice_measure` |
| `l-/r-upperarm-muscle-incr` | 0.55 | biceps/triceps definition | visual + girth table |
| `l-/r-upperarm-shoulder-muscle-incr` | 0.35 | deltoid mass (the torso spec may raise it) | bideltoid 625 |
| `l-/r-upperarm-fat-decr`, `l-/r-lowerarm-fat-decr` | 0.30 | lean arms | |
| `l-/r-lowerarm-muscle-incr` | 0.55 | brachioradialis, extensor and flexor masses | forearm max 300 |
| `l-/r-lowerarm-scale-horiz-incr` | 0.15 | forearm wider in the frontal plane than deep (100 × 85) | section ratio |
| `l-/r-hand-scale-incr/decr` | solve | hand length 193 crease → tip | `measure_hand()` |
| `l-/r-hand-fingers-length-incr/decr` | solve | middle finger 97 from the MCP axis | |
| `l-/r-hand-fingers-diameter-incr/decr` | solve | index PP width 20 | |
| `l-/r-hand-fingers-distance-incr/decr` | solve | rest splay index +6° … little −8° | finger axis angles |
| `l-/r-hand-trans-in/out` | 0 | not used (wrist position is the bones') | |

Solver: secant, ≤ 6 iterations per "solve" row, weights clamped to [0, 1]; log every measured value. The hand fit runs **after** the arm fit because `hand-scale` moves the wrist mass slightly.

### 4.2 Step 2 — Joint re-placement before the rig fit (`rigfix.py::fix_hand_joints()`)
MPFB's default rig places the MCP joints too far distally: in the research blend `metacarpal2.L` is 79.2 mm and `finger3-1.L` 38.8 mm where anatomy wants MC3 65 and PP3 44 [measured]. MPFB fits bones to the `JointCubes` helper vertices (`joint-l-finger-2-1 … 2-4`, four per finger: MCP, PIP, DIP, tip). Procedure: (1) on the evaluated mesh, find each dorsal knuckle apex as the local maximum of the dorsal surface along the finger ray (numpy on the `hand_knuckle_N` region), (2) build shape key `Hand.JointFix` that moves each MCP joint cube to apex + (0, −3, −7) in H (the axis is 7 mm palmar and 3 mm proximal of the apex), each PIP/DIP cube to the dorsal joint crease centre − 5 mm palmar, each tip cube to the pulp apex, the thumb CMC cube to (+30, 24, −10), (3) check the resulting segment ratios against §3.4 (index 40 : 24 : 24, etc.; tolerance 1.5 mm) and move the mesh's knuckles with `l-hand-fingers-length` if the mesh, not the cubes, is off, (4) then `HumanService.add_builtin_rig(basemesh, "default", import_weights=True)` (spec 03 step 3 renames it `Morgan.Rig`). Verify after the fit: `wrist.L` head = the wrist axis (`measure_hand()` origin ± 2 mm), `finger3-1.L` head at MCP3 ± 1.5 mm, bone lengths per §3.4 ± 1.5 mm. The same fix is applied to the elbow cube (the axis is 10 mm anterior of the olecranon apex and midway between the epicondyles) and the GH cube (48 mm below the acromion, 20 mm anterior of the deltoid's lateral apex).

### 4.3 Step 3 — Vertex groups (`weights.py::make_arm_groups()`), rest-space distance fields in numpy
Upper arm (left; mirrored): `arm_L_deltoid` (s 0–40 %, clock 11–7 through 3), `arm_L_biceps` (s 25–75 %, 10–2), `arm_L_triceps` (s 20–85 %, 4–8), `arm_L_brachialis` (s 55–85 %, 1–3 and 9–11), `arm_L_epicondyle_med/lat`, `arm_L_olecranon` (ellipse 22 × 28 at 6 o'clock), `arm_L_fossa` (triangle 30 × 40 at 12), `arm_L_elbowcrease`, `arm_L_blend_axilla` (s 5–15 % linear). Forearm: `arm_L_brachioradialis` (s 5–55 %, 1–2), `arm_L_extensors` (3–5), `arm_L_flexors` (9–12), `arm_L_ulna_ridge` (tube r 6 along the ridge polyline 7 o'clock), `arm_L_styloid_rad/uln`, `arm_L_lister`, `arm_L_snuffbox`, `arm_L_vein_cephalic/basilic/cubital` (tubes r 2.5–3), `arm_L_tendon_FCR/PL/ECU` (tubes r 2), `arm_L_wristband` (s 90–100 %), `arm_L_cuffband` (wrist −30 … 0 for the glove gauntlet). Hand: `hand_L_dorsum`, `hand_L_palm`, `hand_L_thenar` (ellipse 45 × 30 at the apex), `hand_L_hypothenar` (40 × 22), `hand_L_hollow` (r 25), `hand_L_knuckle_2..5` (r 9 at each dorsal apex), `hand_L_pip_2..5`, `hand_L_dip_2..5`, `hand_L_web_1..4`, `hand_L_finger_N_PP/MP/DP` (per phalanx from the bone weights > 0.5), `hand_L_pulp_1..5` (r 7 at the pulp apex), `hand_L_nail_1..5` (faces of slot `Human.fingernails` grouped by finger — the slot exists [measured]), `hand_L_crease_distal/proximal/thenar/wrist`, `hand_L_digital_crease_N`, `hand_L_vein_arch/mc2/mc3/mc4` (tubes r 1.5), `hand_L_tendon_edc2..5/eip/epl` (tubes r 1.5), `hand_L_callus_mc` (4 ovals), `hand_R_callus_web`, `hand_R_callus_trigger`, `arm_L_hairdensity` and `hand_L_hairdensity` (float weights = §3.6 density / 12).

### 4.4 Step 4 — Layer A sculpt (`Arm.Sculpt`, `Hand.Sculpt`; left side then `mirror_shape_key(key, 'X')`; right-hand asymmetries at the end)
Base-mesh spacing on the arm is 20–30 mm, on the hand 6–10 mm, on the fingers 4–6 mm along and 5–7 mm around (1,629 vertices / 1,614 quads per hand in the body group [measured]) so radii below are ≥ 6 mm on the arm and ≥ 3 mm on the hand; smaller features live in layers B and C. Order: volumes first, hollows last. Upper arm (frame: station s, clock, radial offset):
1. Deltoid distal half: `soft_inflate` (s 25 %, 3 o'clock) r 40, +4; insertion V: two `soft_move` r 14 by 1.5 mm inward along the V's edges at s 35–42 %.
2. Biceps: `soft_inflate` (s 45 %, 12) r 45, +7; its medial edge sharpened by `soft_move` (s 45 %, 10) r 12 by 2 mm inward (bicipital groove); triceps lateral head (s 50 %, 5) r 40, +4; long head (s 40 %, 7) r 38, +3; triceps tendon flat: `flatten_to_plane` over s 70–95 % at 6, blend 0.6; brachialis (s 70 %, 2) and (s 70 %, 10) r 22, +2.
3. Elbow: medial epicondyle `soft_inflate` (s 97 %, 9) r 10, +4; lateral (s 97 %, 3) r 9, +2.5; olecranon (axis + 22 mm posterior) r 12, +4; cubital fossa `soft_move` (s 95 %, 12) r 18 by 4 mm inward; biceps tendon `soft_inflate` 3 stations r 5, +2 along the tendon line; carrying angle: rotate the forearm vertex set 11° about the elbow axis' anterior-posterior line (applied as a rigid transform in the shape key, not a bone roll, so the rest stays MPFB's).
Forearm:
4. Brachioradialis `soft_inflate` (s 20 %, 1.5) r 30, +5 tapering to (s 50 %) r 18, +2; extensor mass (s 25 %, 4) r 30, +4; flexor mass (s 25 %, 10.5) r 32, +4; ulna ridge: 9 `soft_inflate` r 5, +1.2 along the ridge polyline from the olecranon to the ulnar styloid, flanked by `soft_move` r 8 by 0.8 mm inward on both sides (the ridge reads as a crease on a lean arm); dorsal forearm flatten s 40–80 % (`flatten_to_plane`, blend 0.4).
5. Wrist: radial styloid `soft_inflate` r 7, +2.5; ulnar styloid r 6, +3.5; Lister's tubercle r 4, +1.5; wrist section to 62 × 42 by `slice_measure` feedback (scale the wrist ring anisotropically about the axis if the base is rounder than 1.4 : 1 — MPFB's wrist is nearly round [VERIFY]); FCR/PL tendon cords 3 stations r 3.5, +1.2 each at s 80–100 %.
Hand:
6. Knuckles: `soft_inflate` each MC head dorsal apex r 9: MC3 +3.0, MC2 +2.5, MC4 +2.5, MC5 +2.0; intermetacarpal valleys `soft_move` r 5 by 0.8 mm palmar along the lines between apexes; dorsum between the arch and the knuckles flatten (blend 0.3).
7. Palm: thenar `soft_inflate` (+42, 50, −22) r 22, +4; hypothenar (−38, 45, −14) r 20, +3; palm hollow `soft_move` (+2, 60, −8) r 25 by 2.5 mm dorsal; heel of the hand (0, 8, −16) r 18, +1.5; MC-head pads on the palm (one per finger at d 100, n −15) r 7, +1.5 (these also carry the callus).
8. Fingers: section to the §3.5 w × t by anisotropic scaling of each phalanx ring set about its bone axis (width in the palm plane, thickness normal to it; MPFB fingers are rounder than 1.2 : 1 [VERIFY at build]); taper check PP → DP; pulp `soft_inflate` each DP (3 mm proximal of the tip, 2 mm palmar) r 6, +1.0 (thumb +1.5); PIP dorsal knuckle r 5, +0.9; DIP dorsal r 4, +0.5; palmar PIP flatten (the finger's palmar face is flatter than its dorsal); webs: `soft_move` each web's lowest point to 45 % of the PP from the MCP axis (MPFB's webs are deep [VERIFY]), the first web to a 50 mm fold with `soft_move` of its palmar face 2 mm inward along the crease line.
9. Thumb: CMC saddle `soft_move` (+30, 24, −10) r 10 by 1.5 mm; thenar blend; the thumb's rest 40° palmar abduction / 25° radial comes from the bones (step 2), not the sculpt.
10. Nail-bed preparation as spec 01 §4.2 step 6: scale each `hand_L_nail_N` patch in its own plane to §3.5 L × W, give it the transverse curvature R (project the patch onto a cylinder of radius R about the DP axis offset dorsally), sink 0.4 mm, raise the one-ring fold loop 0.4 mm proximally and 0.3 mm laterally; store `hand_nailbed_N`.
11. Right-hand/arm asymmetries: right forearm max +4 mm girth (dominant arm), right biceps +3 mm, right MC heads +0.3 mm, right thenar +0.5 mm, right index DP pad 0.5 mm flatter (trigger finger), left little finger 1 mm shorter.
Check after this step with `measure_arm()`/`measure_hand()` and Workbench matcap views (5 s each; `scripts/eval/look.py`).

### 4.5 Step 5 — Layer B relief map (`Arm.Relief.exr` 4096², baked as spec 03 §4.6)
Geometry-Nodes `Arm.ReliefBake` on `Arm.BakeProxy` (Subdivision 3 applied): `Geometry Proximity` to curves made from the polylines (`Arm.L.Curve.Cephalic`, `.Basilic`, `.MedianCubital`, `.UlnaRidge`, `.FCR`, `.PL`, `.ECU`, `Hand.L.Curve.VenousArch`, `.DMV2/3/4`, `.EDC2..5`, `.EIP`, `.EPL`, `.DistalCrease`, `.ProximalCrease`, `.ThenarCrease`, `.WristCrease1/2`, `.DigitalCrease2..5`, `.PIPCrease2..5a/b`, `.DIPCrease2..5`, `.ThumbMCPCrease`, `.ThumbIPCrease a/b`, `.ElbowCrease`, `.FirstWebCrease`) → relief(d) = amplitude × smoothstep(1 − d/width): veins +1.2/3.0 (hand), +1.0/3.5 (forearm), +0.8/2.5 (metacarpal veins); tendons +1.0/3.0 (EDC, scaled by (1 − finger flexion) at render through the mask, §5.2), +1.2/4 (FCR/PL), +0.6/3 (ECU); creases −0.5/1.5 (palmar, distal/proximal/thenar), −0.3/1.2 (wrist, digital, DIP), −0.4/1.4 (PIP pair), −0.6/2.0 (elbow crease), −0.4/2.5 (first web); snuffbox −3/12; nail fold +0.4/1.0 around each `hand_nailbed_N`. Bake `EMIT` to `Arm.Relief.exr` (mm/4 + 0.5), margin 16 px. Used as a `Displace` (UV, strength 0.004 m, mid 0.5, groups `arm_*` ∪ `hand_*`) after `Subdivision` and as a Bump input (§5.3).

### 4.6 Step 6 — Nails (`Hand.L.Nail.1–5`, `Hand.R.Nail.1–5`)
As spec 01: duplicate the `hand_nailbed_N` faces into a separate object, extrude the distal loop 1.0 mm along the DP axis for the free edge, `Solidify` 0.5 mm (thumb 0.6) outward, `Bevel` 0.15 mm on the free-edge rim, `Subdivision` 2; parent to `fingerN-3.L` (`parent_set(type='BONE')` with the real selection); materials `Hand.Nail.Plate` (the plate) and `Hand.Nail.FreeEdge` (the extruded strip) from `materials.py` (shared with spec 01's `Foot.Nail.*`, thickness parameters changed). The nail bed under the plate keeps `Skin.Body` with the `hand_nailbed_N` mask driving the bed colour (§5.1).

### 4.7 Step 7 — Topology fixes on the hand (bmesh, before any sculpt that depends on them; all idempotent via vertex-group membership)
MPFB's hand (1,614 quads) deforms acceptably to 60° but pinches at 85–95° at the MCP and PIP with one edge ring per joint [estimated from the ring spacing; VERIFY at build]. Fix: `bmesh.ops.subdivide_edges` on the edge rings 4 mm proximal and 4 mm distal of each MCP, PIP and DIP axis (the ring is selected as the edge loop crossing the joint plane; `bmesh.ops.subdivide_edges(cuts=1, use_grid_fill=True)` on the loop's radial edges), giving two extra loops per joint = 14 joints × 2 × ≈ 12 verts ≈ 340 vertices per hand; the new vertices inherit weights by `Data Transfer` (nearest face interpolated) from the unmodified copy and shape keys by the same transfer, so the fix can run before or after the sculpt. Other fixes: (a) the fingernail faces are flat on MPFB — step 4.10 curves them; (b) the fingertip has a pole on the pulp apex — leave it, it is hidden under the pulp inflate; (c) MPFB's thumb points too far along d in rest — the CMC cube fix in step 2 gives it 40° palmar abduction; (d) the palm is flat — step 4.7 hollows it. The `Hide helpers` MASK modifier stays (helpers carry the joint cubes).

### 4.8 Step 8 — Hero poses (`grip.py`), run by `build_all.py` after the rifle is placed
Inputs: `Rifle.GripFrame` (empty: origin at the grip's front strap 45 mm below its top, −Y of the empty pointing out of the front strap, +Z up the grip) and `Rifle.HandguardFrame` (origin on the bore axis 198 mm from the receiver face, +Y along the bore toward the muzzle, +Z toward the top rail) from the weapon spec [VERIFY], `Rifle.Collider` (the rifle's evaluated mesh for `BVHTree.FromObject`).
1. Place `Hand.R.PalmFrame` on the grip: the palm's MC-head pad line (d 100) 20 mm below the grip's top on its left face; the hand's n axis = the grip's left-face normal rotated 10° toward the back strap; wrist extension 12°, ulnar deviation 10° applied as the wrist bone's local rotation.
2. Set the finger FK angles of §7.3 table A (right) / B (left).
3. **Contact solve** per finger (`grip.py::close_finger()`): increase MCP, PIP and DIP flexion in the ratio 1 : 1.1 : 0.6 from the table values until the pulp's `hand_pulp_N` centroid is within 1.0 mm of `Rifle.Collider` (nearest-point query), then back off 0.3 mm; abort and warn if any finger needs more than ±12° from the table (the table came from the picture; a big residual means the rifle or the hand frame is wrong). The right index finger is **excluded** from the solve: it is set straight (MCP 5 / PIP 5 / DIP 0, abduction +8) and the hand frame is rotated about the grip axis (±4°) until the index pad's radial side is within 1.5 mm of the receiver's right face.
4. Left hand: `Hand.L.PalmFrame` on the handguard's top-left facet with the MC-head line parallel to the bore at 198 mm; thumb set across the rail (CMC abduction 50, flexion 0, MCP 10, IP 15) and its pulp solved to the rail's top within 1 mm; fingers closed by the contact solve with abductions +6/+2/−2/−6 so the fingertips land under the lower-right facet at a 27 mm pitch; wrist flexion 10, radial 10.
5. Arms: `IK` constraints on `lowerarm02.L/R` (chain 2, target = the hand frame, pole = `Arm.R.ElbowPole` at W (−382, +70, 1201) and `Arm.L.ElbowPole` at (+310, −110, 1151) from §2.1), `Copy Rotation` of the wrist to the palm frame; shoulder (`shoulder01`, `clavicle`) rotations from the pose note (R protraction +8, elevation +2; L 0) applied before the IK so the GH centres sit at (−290, −10, 1472) / (+261, −20, 1472). Pronation: twist of `lowerarm02` = 70° (R) / 40° (L), `lowerarm01` = 30 % of it (§7.2). Humeral internal rotation = the IK result's twist, checked against +45 (R) / +20 (L) ± 10.
6. Readback: bake the result to FK (`pose.visual_transform_apply` with the real selection, then remove the IK constraints or set influence 0) into action `Hero.Pose`, frame 1; store the solved anatomical angles in `renders/05_arm_hand/pose_report.json`; render V1, V2, V6.

### 4.9 Step 9 — Helper surfaces and frames for the neighbours
`Hand.L/R.PalmFrame` (above); `Hand.L/R.GloveLast` (a copy of the evaluated hand with the `Hand.Corr.*` keys at the hero values, offset 1.0 mm dorsal / 0.5 palmar / 0 at the pulps along the normals — the glove spec builds its shell on this); `Arm.L/R.CuffRing` (curve: the wrist circumference at d −30, 185 mm); `Arm.L/R.GuardFrame` (empty on the forearm axis at s 12 % with +Y distal, −Z dorsal; the forearm guard spec reads the girths at s 12/40/90 % from `measure_arm()`); `Arm.L/R.ElbowAnchor` (empty at the lateral epicondyle + 20 mm lateral, +Y distal, for the elbow cap); `Arm.L/R.SleeveCollider` (the arm + 3 mm, for the shirt-sleeve cloth); `Body.Collider` arm region.

### 4.10 Step 10 — Hair curves (`Arm.L/R.Hair`, `Hand.L/R.Hair`, `Arm.*.Vellus`; only with `--hair`)
Built as spec 03 §4.10 with `bpy.data.hair_curves.new()` and the bundled Interpolate/Noise/Trim node groups: roots scattered by `*_hairdensity` weights (Poisson disc, min spacing 1.5 mm), 6 points per strand, length from §3.6 with ±20 % jitter, direction field = the segment's distal axis rotated 20° ulnar on the forearm, with 15° random yaw and a 25° droop; radius attribute 0.035 → 0.015; ≈ 4,000 strands per forearm, 600 per upper arm, 280 per hand (240 dorsum + 40 on the proximal phalanges), vellus 20,000 per arm at radius 0.008 (look-dev only). Material `Hair.Body` (Principled Hair BSDF, melanin 0.75, redness 0.3, tint lighten 20 % of strands). `hc.surface` = `Body.Mesh` so the hair follows the rig.

### 4.11 Poly budget and object list
| Object | Verts / quads (per side) | Modifiers | Render subdivision |
|---|---|---|---|
| `Body.Mesh` arm + hand region (shared) | upper arm ≈ 370, forearm ≈ 360, hand 1,629 + 340 (joint loops) → ≈ 2,700 verts | Armature → Corrective Smooth → Subdivision → Displace (relief) | 2 (≈ 43 k quads per arm); hand closeups 3 (≈ 125 k) |
| `Hand.*.Nail.1–5` | 5 × ≈ 60 → 300 | Solidify, Bevel, Subdivision | 2 |
| `Arm.*.Hair`, `Hand.*.Hair` | ≈ 4,900 curves × 6 pts | GN (Interpolate off), Trim | — |
| `Arm.*.Vellus` | 20,000 × 4 pts | — (look-dev only) | — |
| `Hand.*.GloveLast`, `Arm.*.SleeveCollider` | copies, hidden | — | — |
| Empties: `Hand.*.PalmFrame`, `Arm.*.GuardFrame`, `Arm.*.ElbowAnchor`, `Arm.*.ElbowPole`; curves: `Arm.*.CuffRing`, `Arm.*.Curve.*`, `Hand.*.Curve.*` | — | — | — |
Collection `Part05.ArmHand` (sub-collections `Part05.Nails`, `Part05.Hair`, `Part05.Guides`). Images: `Arm.Relief.exr` 4096², `Arm.Masks.png` 4096². Materials: `Skin.Body` (shared; regional values below), `Hand.Nail.Plate`, `Hand.Nail.FreeEdge`, `Hair.Body`.

---

## 5. Materials and textures

### 5.1 Skin (`Skin.Body`, spec 03 §5.1; the shared node group is spec 01's [VERIFY its name in `scripts/lib/materials.py`])
Regional albedo, roughness, SSS scale and coat from §3.6 are written into the colour attribute `skin_tint` (per vertex, from the groups of §4.3 blended over 6 mm) and refined by `Arm.Masks.png`. Common values: `subsurface_method = "RANDOM_WALK_SKIN"`, Subsurface Weight 1.0, Radius (1.0, 0.2, 0.1), IOR 1.4, Anisotropy 0.8; Specular IOR level 0.5; Coat 0.08 (0.04 on the knuckles and the olecranon skin, which are dry), Sheen 0.05. SSS scale 0.0038 upper arm → 0.0030 hand → 0.0021 fingertips (0.0030 × 0.7, spec 01's request). Palm: Base Colour #d9b09c with a Noise (scale 25 mm) ±3 % lightness and the callus ovals mixed in at 1.0 (#ddc0a8, roughness 0.72, SSS scale 0.0025). Nail bed under the plate: the `hand_nailbed_N` mask mixes #d4a090 (bed) with a lunula ellipse (#e8d6cc, size per §3.5) and a 1.5 mm hyponychium band #c98a7c at the free-edge end. Subdermal mottling: Noise 30 mm → ±4 % lightness, 3 % hue toward blue-green on the dorsum and forearm (vein haze), 3 % toward red on the knuckles and pulps.

### 5.2 Masks (`Arm.Masks.png`, baked like the relief)
R = hair density (0–1 = 0–12/cm²); G = callus + knuckle mask (callus ovals 1.0, knuckle skin 0.6, olecranon skin 0.7, feather 4 mm); B = vein proximity (tubes r 2, feather 2) — also tints; A = tendon visibility weight (EDC tubes 1.0) **multiplied at render by (1 − MCP flexion/90°) through a driver on a Value node per finger**, so the extensor tendons flatten on the curled fingers and stay on the extended right index. A second image `Arm.Masks2.png`: R = friction-ridge mask (pulps 1.0, palm 0.8, feather 3), G = palm/dorsum blend (1 palm, 0 dorsum, 4 mm feather at the borders), B = SSS thickness proxy (fat table normalised to 12 mm), A unused.

### 5.3 Micro relief (layer C, shader bump; `displacement_method = "BUMP"`, distance 0.001 m, strength 0.35, inputs summed)
(a) Follicle pits: Voronoi F1 in Object coordinates, 1 per 1.4 mm on the forearm extensor side, 1 per 2.0 mm elsewhere, none where mask2.G = 1 (palm), depth 0.08 mm; (b) skin lines: two Wave textures at ±35° to the segment axis, 0.5 mm pitch, distortion 2, amplitude 0.03 mm; on the hand dorsum a third Wave at 90° gives the diamond pattern (0.4 mm pitch); (c) knuckle wrinkles: mask G × Wave bands across the finger axis, 1.2 mm pitch on the PIP zone, 2.5 mm on the MCP pad, 0.15 mm, scaled by (1 − flexion) via the same driver as 5.2; (d) friction ridges: mask2.R × Wave `RINGS` centred on each pulp apex (Object coordinates offset per finger through a per-finger Value node set by the script), 0.45 mm pitch, distortion 3.0 and a Noise warp 0.6 mm so each finger reads as a loop or whorl, amplitude 0.05 mm; on the palm Wave `BANDS` following the crease directions, 0.5 mm pitch, 0.04 mm; (e) callus flakes: Voronoi (smooth 0) 1 per 0.8 mm, 0.05 mm, inside mask G callus; (f) `Arm.Relief.exr` as a second Bump (distance 0.004) so Workbench and glTF LOD1 keep the tendons and creases; (g) orange-peel Noise scale 900, 0.02 mm everywhere. Roughness = regional base + 0.08 × (a) + 0.15 × callus − 0.06 × vein + 0.05 × ridges (ridge crests are matter than the furrows).

### 5.4 Texture sets and texel density
No downloaded PBR set is used for skin (research_assets §4 has none). Baked maps 4096² on MakeHuman's UVs: the hand island is small — estimated 7 % of the UV square for both hands → ≈ 1.6 px/mm on the hand, 2.4 px/mm on the arm [estimated; VERIFY by measuring the island area in `uv_layers.active`]. That is enough for veins, creases and callus (features ≥ 1.5 mm); everything finer (ridges, pits, wrinkles) is procedural and resolution-independent, which is why V3/V4 at 15 px/mm still hold. UVs unchanged (MakeHuman's; the seam runs along the ulnar border of the hand and the medial arm — check the `Displace` for a seam step and raise the bake margin to 24 px if it shows). Nails: `Hand.Nail.Plate` — Base #e9dfd6, Transmission 0.55, Roughness 0.15, IOR 1.5, Coat 0.6; fine longitudinal ridges by Wave bands 0.25 mm pitch, 0.01 mm bump; `Hand.Nail.FreeEdge` — #ece6dd, Transmission 0.7, Roughness 0.25.

### 5.5 Hex targets
No skin shows in the reference, so the skin passes against look-dev swatches under scene A's calibrated key (spec 01 §8.1): dorsum of the hand must read within ΔE76 < 6 of **#d4a88c** (albedo #bf8f78 lit as the foot's dorsum calibrates), palm within ΔE < 6 of #ecc8b2, knuckles #c09080, forearm extensor #cfa088, fingertip pulp #e1b4a2, nail plate highlight ≤ #f6efe8 with the bed #d9a896 through it. Under the hero lights the only hex targets this part answers to are the gloved silhouettes and the finger pixels (§8.2), not colours; the glove spec owns #514e4c / #534b46 etc. from §2.2.

---

## 6. Fibres, simulation or dynamics
* **Terminal hair**: `Arm.*.Hair`, `Hand.*.Hair` as §4.10; counts ≈ 4,900 per arm; roots on the evaluated surface at Subdivision 1; the curves follow the body through `hc.surface` + `surface_uv_coordinate`; no simulation. Hidden under the sleeves and gloves in the hero render — built with `--hair` for the look-dev views only.
* **Vellus**: 20,000 per arm, look-dev only, off by default.
* **No cloth, no soft body**: the hand's pulp compression against the grip is modelled by the contact solve (−0.3 mm back-off) and the `Hand.Corr.Grip.R` key (§7.5), not by simulation. The glove spec may run a cloth pass on its shell over `Hand.*.GloveLast`.
* **Nails** are rigid shells parented to the DP bones.

---

## 7. Rigging and attachment

### 7.1 Bones (MPFB `default` rig, verified after step 2; names fixed, positions re-measured at build)
Chain per side: `clavicle.L` → `shoulder01.L` → `upperarm01.L` (deltoid section, 77 mm in the research blend) → `upperarm02.L` → `lowerarm01.L` → `lowerarm02.L` → `wrist.L` → {`metacarpal1..4.L` → `finger2-1..5-1.L` → `finger*-2.L` → `finger*-3.L`}; thumb `finger1-1.L` (the thumb's metacarpal, from the wrist) → `finger1-2.L` (PP) → `finger1-3.L` (DP) [measured chain]. Required rest positions after the fit (left; W, Y_0 = the rest coronal plane of the fit): `upperarm01.L` head = GH (+272, Y_0 − 20, 1475) ± 5; `lowerarm01.L` head = elbow axis centre, 340 ± 3 from the GH along the rest arm direction; `wrist.L` head = wrist axis, 270 ± 3 from the elbow; `finger3-1.L` head = MCP3 at H (+3, 95, +5) ± 1.5; bone lengths per §3.4 ± 1.5; `finger1-1.L` head at the CMC (+30, 24, −10) ± 2. Added bones: none required; optional `Arm.L.ElbowPole`/`Arm.R.ElbowPole` are empties.

### 7.2 Weights (`weights.py::fix_arm_weights()`)
Start from MPFB's imported weights; then (a) **twist split**: humeral rotation 35 % on `upperarm01`, 100 % on `upperarm02` — implemented by re-weighting the upper-arm skin linearly from 0.35 at s 10 % to 1.0 at s 60 % toward `upperarm02`; pronation 30 % on `lowerarm01` (0 at the elbow → 0.6 at s 50 %) and 100 % on `lowerarm02` (s 50–100 %), so the wrist skin turns fully and the elbow skin not at all; (b) the elbow: `upperarm02`/`lowerarm01` blend over 40 mm (s 90–100 % of the humerus to s 0–10 % of the forearm), olecranon skin 70 % forearm; (c) the wrist: `lowerarm02`/`wrist` blend over 20 mm; metacarpals 2–3 are rigid with `wrist` (0.9) — the real CMC2/3 joints barely move — while metacarpals 4–5 keep 30 % mobility (the palm cups); (d) fingers: each phalanx ring set 1.0 to its bone, joint rings 50/50 with a 6 mm blend (the extra loops of §4.7 give the blend room); (e) the thumb CMC: `finger1-1` 0.8 over the thenar with 0.2 `wrist`, so the thenar moves with the thumb; (f) nails: 1.0 to their DP bone (parented objects anyway); (g) normalise, limit to 4 influences per vertex (game export). `Corrective Smooth` (factor 0.5, 5 iterations, `use_pin_boundary`) after `Armature`, before `Subdivision`; Preserve Volume on.

### 7.3 Pose definition (hero): segment directions in W, then the derived anatomical angles
Segment unit vectors (W) from the §2.1 positions, to be refined by the IK (§4.8); the rifle's frames are the authority for the hands [VERIFY: weapon spec].

| Segment | From → to (W, mm) | Direction | Derived angles (anatomical, ±5°) |
|---|---|---|---|
| R upper arm | GH (−290, −10, 1472) → elbow (−382, +70, 1201) | (−0.31, +0.27, −0.91) | shoulder flexion **−15** (−8 to −20 accepted, §2.3 a), abduction **+20**, internal rotation **+45** (from the forearm plane) |
| R forearm | elbow → wrist (−242, −200, 1165) | (+0.46, −0.88, −0.12) | elbow flexion **97**; pronation **70** |
| R hand | wrist → MCP3 | along the grip's rake | wrist extension 12, ulnar deviation 10 |
| L upper arm | GH (+261, −20, 1472) → elbow (+310, −110, 1151) | (+0.15, −0.27, −0.95) | flexion **+12**, abduction **+8**, internal rotation **+20** |
| L forearm | elbow → wrist (+123, −170, 964) | (−0.71, −0.23, −0.67) | elbow flexion **55**; pronation **40** |
| L hand | wrist → MCP3 | parallel to the bore (0.49, −0.42, −0.76) | wrist flexion 10, radial deviation 10 |

**Table A — right hand on the pistol grip** (flexion °; abduction + = away from the middle finger)
| Digit | CMC / MCP | PIP | DIP | Abduction | Contact |
|---|---|---|---|---|---|
| Thumb | CMC palmar abd 30, flex 15; MCP 30 | IP 25 | — | — | pulp on the grip's left face, upper third; tip at the selector level |
| Index | MCP **5** | **5** | **0** | +8 | radial pad and PP side along the lower receiver's right face, pointing at the muzzle; tip 25 mm short of the mag-release button |
| Middle | 85 | 95 | 50 | 0 | pulp on the front strap under the finger shelf |
| Ring | 85 | 95 | 50 | −3 | pulp on the front strap |
| Little | 80 | 90 | 45 | −6 | pulp half on the grip's flared base, MCP 4 mm proximal |
Wrist extension 12, ulnar 10; pronation 70. The contact solve may move each flexion by ≤ ±12°.

**Table B — left hand overhand C-clamp on the handguard**
| Digit | CMC / MCP | PIP | DIP | Abduction | Contact |
|---|---|---|---|---|---|
| Thumb | CMC radial abd 50, flex 0; MCP 10 | IP 15 | — | — | lies across the top rail perpendicular to the bore, pad folded 15° over the rail's right edge, tip at pixel (846,447) |
| Index | 60 | 85 | 45 | +6 | nearest the receiver; pulp on the lower-right facet, tip visible at (806,458) |
| Middle | 62 | 85 | 45 | +2 | tip at (812,470) |
| Ring | 65 | 85 | 45 | −2 | tip at (820,483) |
| Little | 70 | 80 | 40 | −6 | tip at (828,495) |
Wrist flexion 10, radial 10; pronation 40; palm on the top-left facets at 198 mm from the receiver face; fingertip pitch 27 mm along the bore.

### 7.4 Game rig
Export keeps the full MPFB chain (19 bones per hand incl. metacarpals; 163 bones total). The glTF exporter drops drivers, so `build_all.py` bakes the hero key values into one `Arm.Corr.Hero` morph target and exports the driven keys as morph targets (`export_morph=True`), as spec 03 does. If the client wants a lean game hand (§10.2 Q7), the `game_engine` MPFB rig (no metacarpals) is a one-line change in step 2 and the weights of §7.2 (c) collapse onto `wrist`.

### 7.5 Corrective shape keys (generated by `corrective.py::make_corrective(mesh, rig, pose_dict, ops)` as spec 03 §7.5: pose, edit in posed space with `soft_*`, inverse-skin to rest, driver on the bone's swing/twist)
| Key | Driver | Ops (left; mirrored for right) | Purpose |
|---|---|---|---|
| `Arm.Corr.ElbowFlex90.L` | `lowerarm01.L` swing X, 0 → 1 over 30°–90°, hold | biceps `soft_inflate` (s 45 %, 12) r 40, +6 and shift its centre 25 mm proximal (`soft_move` r 45 by 25 mm along the humerus); cubital fossa `soft_move` 4 mm inward r 20 (the crease closes); olecranon `soft_inflate` +2 (skin tightens over the point), olecranon wrinkles flatten (mask G × (1 − key)); brachioradialis +2; triceps tendon stretch: `soft_move` (s 85 %, 6) r 18 by 2 mm inward | elbow at the hero 97° / 55° |
| `Arm.Corr.ElbowFlex130.L` | 1 over 100°–130° | forearm–biceps contact bulge: flexor mass +4 r 35 and biceps +3; fossa skin folds (two `soft_move` ridges +1.5 r 6 across the crease) | reload / carry poses |
| `Arm.Corr.Pronation.L` | `lowerarm02.L` twist Y, 0 → 1 over 0°–80° | dorsal forearm flatten `flatten_to_plane` s 40–90 % blend 0.5; flexor mass `soft_move` 4 mm toward the ulnar side r 35; ulna ridge re-sharpen +0.8; radial styloid moves with `lowerarm02` (weights) and the skin fold at the distal radio-ulnar joint +1.0 r 8; wrist section restored to 62 × 42 by an anisotropic correction of the wrist ring (counteracts the twist thinning: candy-wrapper fix) | hero 70° / 40° |
| `Arm.Corr.WristExt.L` | `wrist.L` swing X (−), 1 over −20° | dorsal wrist 3 transverse folds `soft_inflate` r 4, +0.8 at d −4, −10, −16; palmar wrist skin stretch `soft_move` 1 mm inward r 15; EDC tendons +0.5 (mask A boost via driver) | right hand |
| `Arm.Corr.WristFlex.L` | swing X (+), 1 over 25° | palmar wrist 2 folds +0.8; dorsal skin stretch; FCR/PL relax (relief ×0.5 via mask) | left hand |
| `Arm.Corr.WristDev.L` | swing Z, ±1 over ±15° | ulnar styloid prominence +1.5 (ulnar), radial styloid +1 (radial); the heel of the hand shifts 1.5 mm | both hands |
| `Hand.Corr.FingerFlex.N.L` (N = 2..5) | `fingerN-1.L` swing X, 1 over 0°–85° | MC head dorsal apex +2.0 r 8 (the knuckle sharpens); MCP dorsal pad flattens (`soft_move` 0.8 mm inward r 7); PIP dorsal skin smooth (wrinkle mask → 0 via driver) and PIP knuckle +0.6; palmar digital crease deepens −0.3 (mask boost); pulp `soft_inflate` +0.5 (pressed against the grip) | curled fingers of both grips |
| `Hand.Corr.ThumbOpp.L` | `finger1-1.L` swing, 1 over 40° | thenar `soft_inflate` +2 r 20 and the first-web fold `soft_move` 3 mm palmar r 10 (the web closes); snuffbox fills (−3 → 0 via mask) | right thumb round the grip |
| `Hand.Corr.ThumbAbd.L` | swing (radial), 1 over 50° | first web stretches flat (crease relief → 0), thenar flattens −1, EPL/EPB tendons +1.0 (snuffbox opens) | left thumb across the rail |
| `Hand.Corr.Grip.R` (hero-only, value 1.0 in `Hero.Pose`) | constant | palm hollow fills (+2.5 r 25 reversing step 4.7), hypothenar presses flat against the back strap (−1.5), MC-head pads flatten −0.8, pulp of the middle/ring/little flatten 0.6 on the contact face | the pressed hand |
| `Hand.Corr.Clamp.L` (hero-only) | constant | palm's top-left-facet contact flattens the MC-head pads −0.8 and the thenar −1.0; fingertips flatten 0.5 on the lower facet | the clamped hand |
| mirrors `.R` of all driven keys | | | |

Expected totals: 16 driven keys per side + 2 hero keys. Each is generated in ≤ 2 s; the script verifies that every driven key reads 0 in the rest pose.

### 7.6 Attachments provided to other parts
`Hand.L/R.PalmFrame`, `Hand.L/R.GloveLast`, `Arm.L/R.CuffRing`, `Arm.L/R.GuardFrame` + the girths at s 12/40/90 %, `Arm.L/R.ElbowAnchor`, `Arm.L/R.SleeveCollider`, `Body.Collider` arm region, the `Hand.Corr.Grip.R`/`Clamp.L` keys (set to 1 by `build_all.py` in the hero pose), `pose_report.json` (solved angles), the `*_hairdensity` convention.

---

## 8. Evaluation protocol

### 8.1 Renders (`scripts/eval/render_part05.py`, the shared harness)
Look-dev scene A (spec 01 §8.1: neutral grey backdrop, calibrated key 45° + fill + rim, AgX Base Contrast) for V3, V4, V5 at 2048², 64 spp, OIDN, persistent data; Workbench matcap + cavity "look" renders (480 × 720, 5 s) of the same views after every sculpt step; hero scene B (lights and camera from the lighting spec; rifle, gloves and sleeves visible) for V1, V2 (85 mm, 2048², 64 spp) and V6 (the hero camera, 1024 × 1536, 64 spp, cropped). V7 is V1/V2 with the glove shell at 50 % alpha and a clearance false-colour pass (distance from `Hand.*.GloveLast` to the glove's inner surface mapped 0 → red, 1–3 mm → green, > 4 mm → blue). Budget: 3–4 min per Cycles view on this box (SSS on the hands ≈ 3×); V6 ≈ 4 min; the whole set ≈ 25 min, so the script renders the look-dev set only with `--full`.

### 8.2 Metrics (`measure.py::measure_arm(side)`, `measure_hand(side)`, `grip.py::contact_report()`, `eval/overlay.py`)
* `measure_arm()`: GH, elbow and wrist axis positions from the bones; humerus and forearm lengths; girths at the §3.2/3.3 stations by `slice_measure` perpendicular to each segment axis; biepicondylar breadth; wrist w × t; olecranon protrusion; carrying angle. Tolerances: lengths ±3, girths ±5, breadths ±2.
* `measure_hand()`: frame H from the wrist axis and MCP3; the 20 landmarks of §3.4 (from the bones and the `hand_*` region centroids) ± 1.5 mm; phalanx lengths ± 1.5; finger w × t at each phalanx mid ± 1; hand breadth 91 ± 2, thickness 28 ± 2; thenar/hypothenar heights ± 1.5; palm hollow depth 6 ± 1.5; nail L × W ± 0.7, free edge 1.0 ± 0.3, plate thickness; crease positions ± 2; vein and tendon relief (height of the relief map along each polyline) ± 0.3.
* `contact_report()` (hero pose): per finger the pulp-to-rifle distance (target 0–1.0 mm), the maximum penetration of any hand vertex into `Rifle.Collider` (≤ 0.3 mm), the right index finger's total flexion (≤ 8°) and its pad distance to the receiver (≤ 1.5 mm), the left thumb's pulp distance to the rail (≤ 1 mm), finger–finger minimum distance (≥ 0.5 mm), glove-to-skin clearance statistics from V7.
* `overlay.py`: hero render over `reference_full.png` at ×4 in the two arm boxes and the hand boxes; reports the pixel error of the elbow (the sleeve/guard silhouette's outer point), wrist (cuff centre), the right index tip, the left thumb tip and the four left fingertips (centroids of the glove's fingertip blobs, found as local luminance maxima under the handguard) against §1.4; IoU of the gloved-hand silhouette masks (threshold on luminance against the dark vest) ≥ 0.85; Sobel edge overlays in two colours for the critic.
* Deformation checks: wrist circumference at 0° and 70° pronation (change ≤ 4 %); elbow section area at 0°, 97°, 130° (change ≤ 8 %); no self-intersection in the fossa at 130° (`BVHTree` self-overlap count = 0); finger segment length drift under flexion ≤ 1 %.

### 8.3 Critic questions (score 0–2 each; 32 max; ≥ 26 passes)
1. Are the five fingers in the right length order with the little finger reaching the ring's DIP crease? 2. Are the fingers oval, tapering, with the pulp fuller than the dorsum? 3. Do the knuckles read as bone under skin (MC3 highest), with valleys between? 4. Are there dorsal wrinkles over the PIP and loose pads over the MCP, flattening where the finger is bent? 5. Do the nails have a fold, a free edge, a transverse curve, a lunula on the thumb, pink through the plate — and no floating or sunk plate? 6. Do the tendons and veins read as relief, strongest on the extended index, weakest on the curled fingers? 7. Does the palm have a thenar, a hypothenar, a hollow, three creases and callus at the MC heads only? 8. Is the palm paler and pinker, the knuckles redder, the elbow skin darker and rougher? 9. Are friction ridges visible only at macro scale and only on the pulps and palm? 10. Is the forearm wider than deep, with the ulna ridge, brachioradialis and the cephalic vein on a lean arm? 11. Does the elbow show epicondyles, an olecranon and a fossa, and does it bend to 97° without collapse or ballooning? 12. Does the forearm pronate without a candy-wrapper wrist? 13. Right grip: index dead straight along the receiver, pad touching, three fingers closed on the grip without gaps or poke-through, thumb round the far side? 14. Left grip: thumb across the rail, exactly four fingertips under the handguard at the reference pixels, splayed 27 mm? 15. Do the elbows and wrists land on the reference pixels in V6? 16. Is the hair sparse, dark, lying distal, absent on the palm — and is there nothing waxy, glowing or mannequin-like anywhere?

### 8.4 Failure modes and their fixes
| Symptom | Likely cause | Fix |
|---|---|---|
| Mitten look (fingers fused, no webs, round sections) | MPFB finger shape untouched | step 4.4 (8): anisotropic section, web depth, pulp inflate; check `hand-fingers-diameter` did not overshoot |
| Knuckle pinch at 85–95° flexion | single joint ring | §4.7 loops; raise `Corrective Smooth` iterations to 8 for the hand only via the `hand_*` group |
| Candy-wrapper wrist under 70° pronation | twist all on `lowerarm02` with a hard weight edge | §7.2 (a) linear twist ramp; `Arm.Corr.Pronation` wrist-ring correction |
| Elbow balloon or crease self-intersection | Preserve Volume + large blend | narrow the blend to 30 mm, raise `ElbowFlex90` fossa inward move to 5 mm |
| Index finger sliding through the receiver / floating | rifle placed after the hand or the hand frame's roll wrong | run `grip.py` after `Rifle.*` frames exist; the ±4° roll search in step 4.8 (3) |
| Fingertips not at the reference pixels | handguard 60 % station or the hand's bore-position wrong | move `Hand.L.PalmFrame` along the bore (±15 mm) before changing the finger angles; the weapon spec's handguard length is the authority |
| Right elbow 20 px too high or too far lateral | the pole target or the −8° assumption | §2.3 (a): move `Arm.R.ElbowPole` back (+Y) in 30 mm steps; the elbow pixel wins |
| Waxy fingers | SSS scale too large on the DP | 0.0021 on the DPs (mask2.B), roughness ≥ 0.52 |
| Nails glow or look painted | plate transmission without a bed colour under it | keep the bed mask (§5.1) and the 0.5 mm plate; no emission anywhere |
| Veins read as painted lines | relief bump too weak or tint too strong | relief ×1.2 (max 1.5 mm), tint 18 % → 12 % |
| Hair on the palm or fingertips | density group bleed through the Subdivision | bake the density to the mask after Subdivision 1; clamp mask R to 0 inside `hand_palm` |
| UV seam step in the Displace along the ulnar border | bake margin | margin 24 px; `Displace` strength on the seam ring ×0 via a `arm_seamguard` group |

---

## 9. Build order, effort and risks
1. `fit_arms()` + `fix_hand_joints()` + rig fit; `measure_arm()`/`measure_hand()` pass on lengths (day 1 morning).
2. Groups, layer A sculpt, topology loops; matcap look renders until the §3 tables pass (day 1–2).
3. Relief curves and bake, nails, masks, materials; V3–V5 under scene A; critic round 1 on the bare hand (day 2–3).
4. Weights and twist split, correctives (16 + 2 per side), deformation checks (day 3).
5. `grip.py`: frames, finger FK tables, contact solve, IK, readback; V1/V2/V6 with the rifle and glove blockouts; overlay pass (day 4). This step depends on the weapon spec's frames and on the glove spec's shell for V7; without them it runs against a blockout rifle built from §3.8 dimensions.
6. Hair and vellus, final look-dev renders, critic round 2; commit (day 4–5).

Estimated code: `05_arm_hand.py` ≈ 1,800–2,200 lines; `lib/grip.py` ≈ 450; additions to `sculpt.py`/`measure.py`/`weights.py`/`corrective.py` ≈ 500; `eval/render_part05.py` + `overlay.py` ≈ 400. Four to five working sessions.

Risks: (1) **MPFB finger topology** may not survive the anisotropic section and the web moves without shading artefacts — mitigation: do the loops first, test at Subdivision 2 with a matcap, and keep the section change ≤ 15 %; (2) **the right arm's foreshortening** (§2.3 a) may force a shoulder extension the torso spec dislikes — report the solved angle, let the torso spec move the GH by ≤ 15 mm; (3) **the rifle spec's grip and handguard frames** may differ from §3.8 — every grip number is parametrised on the frames, not on absolute positions; (4) **render cost**: SSS hands + hair + the rifle in V1/V2 ≈ 4 min each; keep the hero set to V1, V2, V6; (5) the `Hand.JointFix` cube move might not be honoured by MPFB's rig fit if it reads cube positions from the Basis rather than the evaluated mesh [VERIFY at step 2]; fallback: edit `edit_bones` after the fit with the real selection (research C §7) and re-transfer the finger weights by bone-distance; (6) the glove's knuckle plate may need the MC heads 1–2 mm higher than anatomy to read in the hero frame — the glove spec decides, this part provides `GloveLast` with the hero keys baked.

---

## 10. Interfaces and open questions for the client

### 10.1 What neighbouring parts must provide or respect
| Part | This part provides | This part needs / the neighbour must respect |
|---|---|---|
| Gloves (spec number per `00_overview.md` [VERIFY]) | `Hand.L/R.GloveLast` (hand + 1.0 dorsal / 0.5 palmar / 0 pulp allowance, hero keys baked), finger axes and knuckle apexes (`measure_hand()` JSON), the gauntlet band d −30 … 0, `Arm.*.CuffRing` 185 mm; the glove colours sampled in §2.2 | shell thickness 1.2 back / 0.9 + 1.0 palm / +0.6 fingertips; knuckle plate 95 × 35 × 6 on the apexes + 2 mm; joint pads over the PIPs; `Surface Deform` or `Data Transfer` of weights from `Body.Mesh`, never its own rig; the gloved index must still read ≈ 20 mm wide (§2.1) |
| Combat shirt sleeves and cuffs | `Arm.*.SleeveCollider` (arm + 3 mm), the girth tables §3.2/3.3, the cuff entering the gauntlet at d −30 (sleeve end at d −35, 190 mm circumference), the raised seam line of the left upper arm (s 25–95 %, 3 o'clock) | the sleeve's cloth sim collides with the collider, not with the skin; sleeve ease ≥ 15 mm circumference over the biceps at s 45 % flexed (372) |
| Forearm guards | `Arm.*.GuardFrame`, girths at s 12 % (290), 40 % (285), 90 % (195) over the sleeve (+6 mm), the guard span s 12–95 % | the guard's inner sleeve 3 mm neoprene + 25 mm straps; the right guard's wrist band meets the glove cuff at d −30; the guard must not interpenetrate the pronated forearm (`Arm.Corr.Pronation` is on) |
| Elbow caps | `Arm.*.ElbowAnchor` (lateral epicondyle + 20 mm) on both elbows; the olecranon position for the strap | left cap built; right mirrored or omitted (consolidated §5); elastic 25 mm around the elbow crease |
| Pauldron tier 3 / bicep band | girth at s 30 % (358 bare, 364 over the shirt) | band 50 mm tall, cam buckle at 9 o'clock on the right |
| Rifle (weapon spec) | the hand frames' required placement: grip top 20 mm above the MC-head line, handguard station 198 mm; `contact_report()`; the hands' envelopes (`GloveLast`) as the rifle's exclusion zones (no accessory under the handguard — weapon §3.10) | `Rifle.GripFrame`, `Rifle.HandguardFrame`, `Rifle.Collider`; the grip's A2 dimensions §3.8; the rifle is placed before `grip.py` runs |
| Torso / shoulder | the deltoid's distal half and the blend band s 5–15 %; GH centres (±272, −20, 1475) rest; the solved shoulder angles | the torso owns the acromion, the deltoid's proximal half, the axilla fold and the pectoral; it may move the GH by ≤ 15 mm if it tells this part |
| Rig / `build_all.py` | the 19-bone hand chains verified, the twist ramps, 36 driven correctives, `Hero.Pose` arm/hand channels, the IK closure procedure and pole empties | MPFB default names kept; `Corrective Smooth` after `Armature`; the rifle before the hands; `Hand.Corr.Grip.R`/`Clamp.L` = 1 in the hero |
| Materials library | `Skin.Body` regional values §3.6, `Arm.Masks.png`, `Arm.Masks2.png`, `Arm.Relief.exr`, `Hand.Nail.*` | the shared skin node group from spec 01; base #b98670 at the face; the leg's #c39a80; the hand dorsum #bf8f78 |
| Foot spec 01 | the per-finger `sss_scale` 0.7 it asked for | its `sculpt.py`/`measure.py` signatures and bump chain |
| Eval | `overlay.py` (finger-pixel finder), `contact_report()` | hero camera (0, −4500, 600), 46 mm, rot (93.9°, 0, 0); scene A swatches |

### 10.2 Questions for the client
1. **Right index finger**: fully straight (as the picture and this spec) or a natural 10–15° slight flexion at the PIP that most shooters show when indexing? Default straight.
2. **Right shoulder**: accept a solved extension of −15° to −20° (the elbow pixel) rather than the pose note's −8°? Default: the pixel wins.
3. **Callus level**: rifleman's (MC-head ovals, right web, faint trigger pad — this spec) or heavier (climber's/lifter's torn callus)? Default rifleman's.
4. **Nails**: 1.0 mm free edge, clean (field-trimmed) or with grime under the edge? Default clean, 1.0 mm.
5. **Palmaris longus** present (85 % of people) and the little-finger slight ulnar curve (clinodactyly) absent — confirm. No ring, watch, bracelet or tattoo on either arm — confirm (nothing shows; gloves and sleeves cover everything).
6. **Hand dominance**: right (the trigger hand) — forearm +4 mm, biceps +3 mm. Confirm.
7. **Game rig**: keep the metacarpal bones (19 per hand) or export the lean `game_engine` hand (15)? Default keep.
8. **Bare-arm deliverables**: are turntables/closeups of the bare hands wanted (then hair, nails and V3–V5 are deliverables), or internal evidence only?
9. **Left-hand finger splay** 4° (fingertip pitch 27 mm, as measured) rather than a tight stack — confirm from the x8 zoom.

### 10.3 Items tagged [VERIFY]
* MPFB rig fit reading moved joint cubes (`Hand.JointFix`); fallback in §9 risk 5.
* Vertex spacing on the arm (20–30 mm) and the hand (4–10 mm); finger section ratio and web depth of the MPFB hand; the wrist's roundness.
* Hand UV island share (≈ 7 %) and texel density (1.6 px/mm at 4K).
* Name of spec 01's shared skin node group; `sculpt.py`/`measure.py`/`corrective.py` signatures used as specs 01 and 03 describe them.
* Weapon spec: grip dimensions (A2 102 mm tall, rake 25°), handguard section 45 × 55 and the 198 mm station, the frames `Rifle.GripFrame`/`HandguardFrame`/`Collider`; the depth (Y) of the grip and handguard, which fixes the hands' Y and therefore the elbows' Y (§2.3 a).
* Torso spec: GH rest centres (±272, −20, 1475), acromion 1523, bideltoid 625.
* Glove spec: thicknesses (1.2 / 0.9 + 1.0 / +0.6) and the knuckle plate 95 × 35 × 6 — from the M-Pact product page and the picture, not measured on a real glove.
* All phalanx lengths, finger widths, nail sizes, crease positions, vein/tendon relief and hair densities are anatomical estimates consistent with ANSUR hand length 201, palm 120, breadth 91 and Greiner's finger lengths; no direct source carries them.
* Biceps relaxed 350 / flexed 372 and the forearm 300 for a 90 kg mesomorph (ANSUR Tight 342 / 305 at 83.6 kg).
