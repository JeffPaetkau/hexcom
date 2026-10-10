# Part 08 — Rig, pose and attachment

Status: draft 1 (spec writer), 2026-10-07, written under the **reality-wins** rule (`CLAUDE.md`, Source of truth). Owner scripts: `scripts/parts/08_rig_pose.py` (rig fit, rolls, helper bones, weights clean-up, diagnostics), `scripts/lib/rig.py` (`BONE_MAP`, anatomical frames, IK helpers, bake), `scripts/lib/pose.py` (the hero pose as data, `apply_pose()`), `scripts/lib/rifle_place.py`, `scripts/lib/corrective.py`, `scripts/lib/attach.py`, `scripts/eval/overlay.py`, `scripts/export_game.py`, and the `pose`, `simulate`, `bake` and `export` stages of `scripts/build_all.py`. Object prefix `Rig.*`, `IK.*`; the armature is `Morgan.Rig`, the body `Body.Mesh`, the hero action `Hero.Pose`.

Conventions (from `CLAUDE.md`): millimetres in this spec, metres in Blender; world frame **W**: origin on the floor midway between the feet, +Z up, the character faces −Y (camera at −Y), **+X = the soldier's LEFT = viewer's right**. Every "left/right" is the soldier's own. Pixel coordinates are FULL-image (1672 × 941). Angles follow the pose note's anatomical convention (flexion +, abduction +, internal rotation +) unless a table says "bone-local", in which case the canonical bone frame of §4.3 applies and the sign is given per side.

Sources read: `notes/analysis_consolidated.md` (Agreed scale, §1, §5, §6, §7, §8, §9), `notes/analysis_pose_proportions.md` §5–7 and errata, `notes/analysis_weapon.md` §1 and §6, `notes/analysis_gear_inventory.md` §1, `notes/research_generators.md` §2 (MPFB API, Rigify generation), `notes/research_blender_capabilities.md` §7 and recommendations, `notes/research_dimensions.md` §1, specs 01–05 and 09 (their §7 and §10), the MPFB rig definition `data/rigs/standard/rig.default.json` and the Rigify metarig `data/rigs/rigify/rig.human.json` (read on this machine), a headless MPFB run that dumped the rest rig (`scratchpad/bones_default.json`, numbers in §3.4), the glTF exporter's property list dumped from Blender 4.5.14 (§7.6), and the reference image with my own landmark overlays `ref/zoom_rig_landmarks_full.png`, `ref/zoom_rig_landmarks_x2.png`, `ref/zoom_rig_rhand_wrist_x4.png`.

---

## 1. Purpose and acceptance

### 1.1 What this part is
The skeleton that every other part skins to or hangs from; the canonical bone frames and the name map that the part scripts, the pose data and the game import all speak; the posing system (scripted IK with pole solving, FK tables, a contact solve for the fingers, a bake to FK); the hero pose itself as data (every joint of the analysis as a bone-space rotation, plus the pelvis placement and the rifle transform); the attachment rules for every piece of clothing, armour and gear; the corrective-shape-key mechanism and its drivers; the order in which fitting, posing, simulation and baking run; the verification renders and overlays that prove the posed figure sits on the analysts' landmarks; and the glTF export that the hexcom Godot project loads. It builds no skin, cloth or hardware of its own; it decides where everything stands.

### 1.2 What "perfect" looks like
Rendered from the reference camera in Workbench and blended 50 % over `reference_full.png`, the posed figure's skull top, pupils, shoulder joints, elbows, wrists, knees, ankles and soles sit on the analysts' pixels within the tolerances of §8.3; the rifle's butt pad and muzzle sit on theirs. A critic who knows anatomy sees a man standing, not a mannequin: weight on the rear right foot, the pelvis dropped and turned a little to his right, the chest unwound back toward the camera, the head turned 20° to his left with the neck sharing the turn over three segments, the right elbow pulled back and across, the left arm hanging to the handguard with a 55° elbow, both hands in contact with the rifle (no gap, no penetration), fingers wrapped in the ratios of spec 05, the right foot turned out to a near profile and the left pointing 15–17° left, both soles flat on the floor. No candy-wrapper twist at the forearms, thighs or neck; no collapsed elbow or knee; no shoulder that reads as dislocated. The same skeleton, rest-posed and scaled to 1.80 m, imports into Godot 4.7 as one Skeleton3D with 163 (+6) named bones, a humanoid bone map, four influences per vertex and the hero pose as a one-frame animation.

### 1.3 Closeup render views (render harness definitions in §8.1)
Camera positions in W (mm); 36 mm sensor; Workbench matcap + cavity for form, Cycles 48 spp for the hero-lit variant. Because this part owns placement, every view is also rendered as a **50 % overlay** on the reference crop named.

| View | Camera position | Target | Lens | Compared with | What it checks |
|---|---|---|---|---|---|
| V1 Full figure, reference camera | (0, −4500, 600), rotation (93.9°, 0, 0) | — | 46 mm, 1672 × 941 | `ref/reference_full.png`, `ref/zoom_rig_landmarks_full.png` | the landmark table §8.3; silhouette; stance |
| V2 Right arm and grip | (−900, −1800, 1350) | (−250, −280, 1180) | 85 mm, 1024² | `ref/crop_arm_right_viewerleft.png`, `ref/zoom_rig_rhand_wrist_x4.png`, `ref/zoom_arm_rhand_grip_x8.png` | elbow behind the body line, forearm toward the camera, wrist ext 12 / ulnar 10, index along the receiver, dorsum to camera |
| V3 Left arm and handguard clamp | (+950, −1700, 1150) | (+120, −430, 900) | 85 mm, 1024² | `ref/crop_arm_left_viewerright.png`, `ref/zoom_arm_lhand_clamp_x8.png` | 55° elbow, thumb across the rail, four fingertips under the handguard at 27 mm pitch |
| V4 Pelvis, hips, knees | (0, −2300, 650) | (0, 0, 650) | 60 mm, 1024 × 1280 | `ref/crop_legs_knees.png`, `ref/zoom_leg03_pelvis_thighs_x4.png` | pelvis yaw −10°, knee facings 45° R / 12° L, knee flexions 17 / 9, knee-to-knee 346 |
| V5 Feet and ankles, low | (0, −2000, 320) | (0, 0, 120) | 70 mm, 1024 × 768 | `ref/crop_boots_feet.png`, `ref/zoom_foot_soles_floor_x4.png` | right heading 85°, left 17°, soles flat, ankle-to-ankle 416, heel-to-heel 308 |
| V6 Head and neck turn | (−300, −1500, 1760) | (0, −60, 1720) | 85 mm, 1024² | `ref/crop_head_face.png` | head yaw +20° world, pitch −3°, the turn spread over neck01–03, no wrapper at the neck |
| V7 Rig diagnostics turntable | 8 views at 45°, (r = 3200, h = 1000) | (0, 0, 950) | 50 mm, 768 × 1024 | no reference | bones as octahedra, joint spheres, poles, per-bone weight heat maps (§5) |

### 1.4 Pass criteria a critic can score (full list and tolerances in §8.3)
1. V1 overlay: every landmark in §8.3 within tolerance; the only accepted miss is the hip row (reality-wins, §2.3 D1), reported but not scored.
2. Readback of every anatomical angle in §4.6 within ±5° of the table (±10° where the table says ~).
3. Both knees flex (17 ± 3 R, 9 ± 3 L) and face the stated directions ± 5°; neither hyperextends.
4. Both soles lie on z = 0 within 1 mm over the whole `Foot.Last` sole polygon; nothing hovers or sinks.
5. Right hand: palm and three curled fingers within 1 mm of `Rifle.Collider`, index pad within 1.5 mm of the receiver's right face, zero penetration deeper than 1 mm; left hand: thumb on the rail, four fingertips under the handguard, same tolerances.
6. Elbows land on their pixels (632, 328) ± 8 and (958, 352) ± 8 while bone lengths stay real (§3.1); the solved right shoulder extension lies in −8° to −25°.
7. Rifle: butt-pad centre (695, 268) ± 4 px, muzzle tip (903, 570) ± 4 px, right side facing the camera (roll about the bore within ±5° of §4.8); butt pad in contact with the carrier over the right pectoral (0–3 mm).
8. Twist zones (forearms, thighs, neck): no edge ring loses more than 25 % of its rest circumference; no face normal flips (candy-wrapper test, §8.2).
9. Weights: ≤ 4 influences per vertex, all normalised, no vertex with zero total weight; `Body.Mesh` deforms smoothly at the elbow at 97° and at the knee at 17°/90° (test poses, §8.2).
10. Export: `export/sgt_morgan.glb` reimports into a fresh Blender scene with the same bone count, the `Hero.Pose` animation and the corrective morph targets; height of the reimported rest mesh 1800 ± 2 mm; Godot's humanoid bone map validates with no unmapped required bone.

---

## 2. Reference observations

### 2.1 Landmarks the rig must hit (analysts' pixels, re-plotted on `ref/zoom_rig_landmarks_full.png`)
Camera model for hand-checking (the eval script uses `bpy_extras.object_utils.world_to_camera_view`, which includes the 3.9° pitch; the formula below ignores it and is good to ±3 px): with f_px = 2130, horizon y = 615, principal x = 836, D = 4500 + Y(mm): **px = 836 + 2130·X/D, py = 615 − 2130·(Z − 600)/D**.

| Landmark | Pixel (analysts) | Height / position implied | Rig element | Note |
|---|---|---|---|---|
| Skull top (hair mass) | (812, 20) | Z 1855 at Y ≈ −20 | `head` tail + scalp thickness | my projection of Z 1855 → y 21 |
| Pupils | (800, 77) / (832, 77) | Z 1740, IPD 66 mm | `eye.R/L` heads | projection of Z 1740 → y 75 |
| Chin | (816, 129) | Z 1620 | `jaw` tail region | closed mouth |
| Shoulder joints (GH) | (675, 200) / (935, 200) | Z 1476, X ∓ 290 / +261 (spec 04/05) | `upperarm01.R/L` heads | projection of Z 1476 → y 200; pads top y 195 |
| Right elbow | (632, 328) | lies 100–150 mm behind the shoulder plane (§2.3 D3) | `lowerarm01.R` head | measured ±3 px |
| Left elbow | (958, 352) | in the image plane, Y ≈ −110 | `lowerarm01.L` head | measured |
| Right wrist / glove cuff | (690–700, 325–350) | the wrist is to his right of the grip, level with the grip top | `wrist.R` head | see `ref/zoom_rig_rhand_wrist_x4.png`: the forearm arrives almost horizontal, the dorsum faces the camera |
| Left wrist / cuff | (865–885, 410–440) | above the handguard, Y ≈ −400 | `wrist.L` head | |
| Hip joints as drawn | (768, 505) / (862, 505) | Z 827 | — | **overruled**, §2.3 D1 |
| Hip joints, real | ≈ (776, 443) / (856, 443) | Z 963 rest, ≈ 945 posed | `upperleg01.R/L` heads | my projection; green crosses on the overlay |
| Crotch (trousers) | (810, 535) | Z 763 | spec 09 | the garment keeps the drawn crotch; the body's perineum is at Z ≈ 900 |
| Knees (pad centres) | (727, 650) / (890, 657) | knee axis Z 523 | `lowerleg01.R/L` heads | projection of Z 523 → y 651 |
| Ankles (boot break) | (732, 855) / (928, 858) | Z 80 at (−208, +75) / (+208, −75) | `foot.R/L` heads | projections (739, 857) / (936, 865) |
| Soles | y 895 / y 907 | Z 0 | `heel.R/L` | projections y 894 / y 904 |
| Butt-pad centre | (695, 268) | W (−288, −150, 1309) at D 4350 | `Rifle.Root` | contact with the carrier |
| Muzzle tip | (903, 570) | W (125, −549, 682) | `Rifle.Root` | 849 mm from the butt pad |
| Centre of mass (analysts) | (812, 430) | Z ≈ 980, over the right ankle's depth | readback metric | 55/45 right-heavy |

### 2.2 Rifle placement derived from the two pins (my computation, §4.8 has the full transform)
Pinning the butt-pad centre at pixel (695, 268) and depth 4350 mm (0–3 mm off the carrier's right pectoral) and the muzzle tip at (903, 570), with the real butt-to-muzzle length 849 mm, puts the muzzle 400 mm nearer the camera than the butt; the bore direction is **(0.441, −0.468, −0.766)**: 50.0° below horizontal, 43.3° to his left of the camera axis (analysts: 50° / 50° ± 5). The rifle's right face normal, perpendicularised to the bore and aimed at the camera, is (−0.271, −0.883, 0.384); the rifle's up is (0.856, −0.038, 0.516), i.e. up and toward his left as the analysts read. With the weapon note's build frame (origin at the bolt face on the bore at the receiver face, +Y to the muzzle, +X to the rifle's right, +Z up), the receiver face sits at **W (−67, −346, 1014)** → pixel (802, 403), which is where the picture shows the handguard's rear end (793, 402). The spec-05 `Rifle.GripFrame` (front strap, 45 mm below the grip top) lands at W (−217, −252, 1124) → pixel (727, 352), inside the right-hand box and on the index MCP (727, 355). The spec-05 `Rifle.HandguardFrame` at 198 mm projects to (847, 477); the picture's left palm centre (840, 460) and thumb (850, 445) correspond to **170 ± 15 mm** from the receiver face. The drawn magazine baseplate (748, 455) is ≈ 100 mm nearer the body than a real magazine perpendicular to this bore (706, 431); the drawn castle nut (748, 300) and ejection port (790, 375) are 25–30 px aft of the real positions because the drawn receiver is 12 % oversize (weapon note §1).

### 2.3 Ambiguities and decisions (reality wins where the image contradicts itself or anatomy)
| # | Topic | Image says | Reality says | Decision | Consequence |
|---|---|---|---|---|---|
| D1 | Hip-joint height | hips at y 505 → Z 827; thigh 325 mm (74 % of real); torso 13 % long | ANSUR Tight (§3.1): trochanterion 963, femur segment 437, knee axis 526 | **Real.** Hip centres at Z 963 rest (posed ≈ 945, pelvis dropped by abduction and stance). Overrules consolidated §1 and spec 03's `FEMUR_MM = 325` / rest hip 851 | the overlay deviates in the hip row (≈ 55 px) and nowhere else; spec 09 keeps the drawn trouser crotch at Z 763 as a dropped-crotch cut; specs 03/04 must undo the 102 mm torso stretch in the critique pass |
| D2 | Right humerus | elbow at (632, 328) with the GH at (675, 200): 14 % short at −8° extension | humerus 340, forearm 270 | **Real lengths; the elbow pixel wins over the inferred −8°.** The IK pole is solved so the elbow projects onto (632, 328) ± 8; the shoulder extension that results (−15° to −25°) is accepted, as spec 05 §2.3(a) already allows | the right shoulder reads pulled back; the pauldron tier 3 and bicep band follow the humerus |
| D3 | Right foot turn-out | toe 85–100° to his right | hip external rotation ≤ 45° with a 17° knee, tibial rotation ≤ 20°, subtalar abduction ≤ 10°, pelvis −10° → 85° maximum | **85°** (the analysts' lower bound) | spec 02's "90° + 15–20° toe-away" becomes 85° + 15° toe-away; the medial boot still faces the camera |
| D4 | Rifle internal landmarks | receiver 12 % oversize, rail 10 cm above the bore, mag 100 mm too near the body | real AR-15 dimensions (weapon note §2, §6) | pins at the butt pad and muzzle; everything between follows the real geometry | castle nut / ejection port / mag base deviate 25–50 px from the drawing; not scored |
| D5 | Left-hand station on the handguard | palm centre (840, 460), thumb (850, 445) → 170 ± 15 mm from the receiver face | spec 05 chose 198 mm | **170 mm**; `Rifle.HandguardFrame` moves to Y 170 (interface change to specs 05 and 15, §10) | hand 28 mm nearer the receiver than spec 05 drew; projections match the picture |
| D6 | Weight 55/45 | body centre-line x ≈ 812 between the ankles 732/928 | lever rule 58/42; a shifted pelvis of 20–40 mm does it | pelvis centre X **−30 ± 10**; COM ground projection checked by readback, target 55 ± 5 % on the right | spec 03 used −40; within tolerance |
| D7 | Shoulder joint heights | GH at y 200 both sides | ANSUR acromial 1524, GH ≈ 48 below → 1476 | **1476 ± 10** (spec 05); spec 04's 1452 is 24 mm low and flagged | the posed GH centres differ by lean and protraction, not by rest height |
| D8 | Chest/pelvis yaw | pelvis −10°, chest −5° world, head +20° world | plausible (lumbar rotation 5°, thoracic 5°, cervical 25° all within range) | as analysed | — |
| D9 | Knee flexions | R 15–20°, L 8–10° | standing relaxed knees 5–20° | R 17°, L 9° | the pelvis height solve targets these |
| D10 | Rest pose of the deliverable | — | MakeHuman rest is an A-pose with ≈ 40° arm abduction and bent elbows (§3.4) | keep MPFB's rest as the bind pose; Godot's humanoid import normalises silhouette (§7.6) | a clean T-pose rest is an open question (§10.2 Q4) |

---

## 3. Real-world reference

Status marks: **M** measured on this machine (MPFB dump, pixel work), **S** sourced (ANSUR II Tight column via `research_dimensions.md`; MPFB/Rigify JSON; Blender 4.5 API dump), **E** estimated (anatomy texts from memory, tagged [VERIFY] where a number matters).

### 3.1 Segment lengths and joint-centre heights for a 1855 mm man (ANSUR Tight × 1.005; joint centres from landmark offsets)
| Segment / joint | Value (mm) | Status | Derivation |
|---|---|---|---|
| Stature | 1855 | S (analysis) | 875 px at 4.72 px/cm |
| Eye height standing | 1740 | S | 1732 × 1.005; pupils y 77 |
| Cervicale (C7) | 1604 | S | 1596 × 1.005 |
| Acromial height | 1524 | S | 1516 × 1.005 |
| GH (shoulder joint) centre height | **1476 ± 10** | E | acromion − 48 (humeral head centre sits 40–55 mm below the acromion) |
| GH centre lateral offset | ±275 (bare), posed R −290 / L +261 | S/E | biacromial 424 × 1.005 → half 213, plus 60 lateral for the humeral head; posed values from specs 04/05 |
| Upper arm, GH centre → elbow axis | **340 ± 10** | E | Winter 0.186 H = 345; ANSUR acromion–radiale 353 − 48 + 10 = 315 as the lower bound; spec 05 uses 340 |
| Forearm, elbow axis → wrist axis | **272 ± 8** | S/E | radiale–stylion 281 × 1.005 = 282, radiale 10 above the axis; Winter 0.146 H = 271 |
| Hand, wrist axis → MCP3 | 100 | S | palm length 120 − 20 (crease to axis) |
| Hand length / breadth | 202 / 91 | S | |
| Iliocristale (crest) | 1134 | S | |
| Trochanterion | 963 | S | |
| Hip joint centre height | **963 ± 10** | E | the femoral head centre lies at the trochanter tip's level within ±5 mm |
| Hip centre spacing | 176 ± 8 | E | adult male inter-hip-joint 170–185 [VERIFY]; spec 03 uses ±88 |
| Thigh, hip centre → knee axis | **437 ± 8** | S | 963 − 526 |
| Knee axis height (lateral epicondyle) | 526 | S | 523 × 1.005; the joint centre ≈ 10 below the epicondyle → 516 posed R (spec 03) |
| Shank, knee axis → ankle axis | **446 ± 6** | S | 526 − 80 |
| Ankle (talocrural) axis height | 80 | S/E | lateral malleolus 76, medial ≈ 90; the axis passes just distal to the malleolar tips |
| Foot length / ball length | 282 / 210 | S | |
| Crotch height (perineum) | 902 | S | |

### 3.2 Joint ranges of motion used as IK limits and sanity bounds (AAOS / Norkin & White normal values, from memory — E [VERIFY]; they only clamp the solver, the hero pose uses a fraction of each)
| Joint | Flexion / extension | Abduction / adduction | Internal / external rotation | Hero pose uses |
|---|---|---|---|---|
| Lumbar + thoracic (sum) | 60 / 25 | lateral 25 each side | 30 each side | ext 3, lat 2, yaw 5 |
| Cervical (neck + head) | 50 / 60 | lateral 45 | 80 each side | yaw 25, ext 5 |
| Shoulder (GH) | 180 / 60 | 180 / 30 | 70 / 90 | R flex −15…−25, abd 20, int 45; L flex 12, abd 8, int 20 |
| Elbow | 150 / 0 (hinge) | — | pronation 80 / supination 80 (forearm) | R 97, pron 70; L 55, pron 40 |
| Wrist | 80 / 70 | radial 20 / ulnar 30 | — | R ext 12 ulnar 10; L flex 10 radial 10 |
| Finger MCP / PIP / DIP | 90 / 100 / 70 (MCP hyperext 30) | MCP ±20 | — | tables A/B of spec 05 §7.3 |
| Thumb CMC | palmar abd 45, radial abd 60, flex 15 | — | opposition | R palmar 30; L radial 50 |
| Hip | 120 / 30 | 45 / 30 | 45 / 45 | R flex −5, abd 14, ext 45; L flex 8, abd 10, ext 22 |
| Knee | 135 / 0 (hinge; tibial rotation 20–30 when flexed) | — | — | R 17 + tibial ext 20; L 9 + tibial ext 5 |
| Ankle | dorsi 20 / plantar 50 | inversion 35 / eversion 15 (subtalar) | abd/add 10 | both plantigrade; R eversion 3, abd 10 |

### 3.3 Standards the export must satisfy
| Standard | Requirement | Status |
|---|---|---|
| glTF 2.0 skinning | 4 joints/weights per vertex per set (JOINTS_0/WEIGHTS_0), normalised; inverse bind matrices from the rest pose; Y-up, metres | S (spec) |
| Blender 4.5.14 glTF exporter | `export_influence_nb` default 4, `export_all_influences False`, `export_skins True`, `export_rest_position_armature True`, `export_def_bones False`, `export_morph True`, `export_animation_mode 'ACTIONS'`, `export_apply False` (applying modifiers drops shape keys) — property names verified on this machine | M |
| Godot 4.7.2 glTF import | Skeleton3D from the skin; bone names kept; humanoid retargeting through `SkeletonProfileHumanoid` with a `BoneMap` (56 profile bones: Root, Hips, Spine, Chest, UpperChest, Neck, Head, LeftEye, RightEye, Jaw, L/R Shoulder, UpperArm, LowerArm, Hand, Thumb Metacarpal/Proximal/Distal, Index/Middle/Ring/Little Proximal/Intermediate/Distal, UpperLeg, LowerLeg, Foot, Toes) [VERIFY against the 4.7 docs; stable since 4.0]; 8 bone weights only if the mesh is imported with the 8-weight flag [VERIFY] | E |
| hexcom rules (`summary.md` constants) | standing man 1.80 m, eye 1.65 m; crouch 1.25 / 1.10; prone 0.45 / 0.35; Godot 4.7.2 .NET; model forward is Godot −Z | S |
| Scale | export scale 1800 / 1855 = **0.9704**; eye height after scaling 1688 mm (rules say 1650, §10.2 Q2) | M |

### 3.4 The MPFB `default` rig as it comes (headless dump at the spec-03 macros, height macro 0.583 → body 1834 mm; multiply by 1.0114 for 1855 before any detail targets) — **M**
163 bones, all `use_deform True`, none connected; placement by MakeHuman joint cubes (`joint-*` helper vertex groups) or mean/vertex strategies; weights imported from `weights.default.json` (291 vertex groups on the mesh including helpers). Influences per vertex before clean-up: 3 → 1553 verts, 4 → 6369, 5 → 4216, 6 → 2371, 7 → 1927, 8 → 1268, 9 → 651, 10 → 737, 11 → 66: **60 % of vertices exceed four influences** (mostly face and hand), so §4.4's limit-and-normalise step is mandatory.

| Chain | Bones (head → tail, W mm at 1834) | Length | Note |
|---|---|---|---|
| Pelvis | `root` (0, 62, 984) → (0, −8, 998); `pelvis.L/R` (0, −8, 998) → (±115, 3, 985); `spine05` (0, −8, 998) → (0, 25, 1087) | 71 / 117 / 94 | `root` is a short bone from behind the sacrum to the pelvis centre: it is the pelvis control, its head the pivot (70 mm behind the hip line, anatomically sensible) |
| Spine | `spine04` → (0, 16, 1159); `spine03` → (0, 29, 1224); `spine02` → (0, 50, 1368); `spine01` → (0, −14, 1584) | 73 / 66 / 146 / 225 | roll 0 everywhere: local X = world X, so +X = flexion already |
| Neck, head | `neck01` → (0, −20, 1603); `neck02` → (3, −33, 1649); `neck03` → (0, −45, 1681); `head` → (0, −46, 1841) | 20 / 48 / 35 / 160 | three neck bones for the yaw split |
| Shoulder | `clavicle.L` (24, −30, 1505) → (118, −27, 1523); `shoulder01.L` → (192, −19, 1476); `upperarm01.L` → (240, −22, 1415); `upperarm02.L` → (370, −22, 1276) | 95 / 88 / 78 / 191 | GH at 1476 (0.805 H, matches §3.1); **GH → elbow only 268 mm** (real 340): spec 05's `measure-upperarm-length` targets and joint-cube fix must run before the rig fit |
| Forearm, hand | `lowerarm01.L` → (438, −120, 1215); `lowerarm02.L` → (505, −213, 1147); `wrist.L` → (517, −244, 1131); `metacarpal2.L` → (554, −302, 1093); `finger3-1/2/3.L` 38 / 30 / 30 | 134 / 133 / 37 / 78 | elbow → wrist 267 (real 272, fine); MCP too distal (spec 05 §4.2) |
| Leg | `upperleg01.L` (115, 3, 985) → (126, −20, 892); `upperleg02.L` → (158, −31, 532); `lowerleg01.L` → (177, −24, 311); `lowerleg02.L` → (199, −12, 75); `foot.L` → (199, −79, 39) | 97 / 361 / 223 / 237 / 76 | hip 985 → 996 at 1855 (real 963, 3 % long); knee 532 → 538 (real 526); the 01/02 split is a twist helper, not a joint |
| Toes | `toe1-1/1-2`, `toe2…5-1/2/3` from the MTP cubes | 20–34 | spec 01 re-places them |
| Face | `jaw`, `special01…06`, `levator02–06`, `oris01–07`, `oculi01/02`, `orbicularis03/04`, `risorius02/03`, `temporalis01/02`, `tongue00–07`, `eye.L/R` (head (30, −133, 1721)) | — | 60 face bones; kept for the game, driven by nothing in the hero (spec 06 uses shape keys) |
| Breast | `breast.L/R` (0, 50, 1368) → (±102, −144, 1351) | 220 | deform weight set to 0 on a male (§4.4) |

Rest orientation facts that matter: the arm hangs at ≈ 40° abduction with the elbow bent ≈ 45° and the hand forward (MakeHuman's rest), so **anatomical angles cannot be typed as bone-local Euler values without the frame construction of §4.3**; the leg bones' X axes are already lateral (roll ≈ 0); `foot` points forward-down (its Z is dorsal-ish, (−0.07, 0.48, −0.88)).

### 3.5 Rifle contact geometry (real AR-15 pattern; weapon note §2/§6 for the rest)
| Feature | Value (mm) | Status | Use |
|---|---|---|---|
| Pistol grip height (front strap) | 102–110 | E (Magpul MOE / A2 class) [VERIFY spec 15] | three fingers at 21 mm gloved + index clearance |
| Grip angle from the receiver's vertical | 25 ± 5 | E | `Rifle.GripFrame` tilt |
| Grip width / depth | 32 / 48 | E | palm wrap |
| Grip front strap top in the build frame | (0, −175, −35) | E | the grip's nose just behind the trigger guard (lower receiver rear at −205) |
| `Rifle.GripFrame` (spec 05): front strap 45 mm below the top | (0, −194, −76), −Y out of the front strap, +Z up the grip | E | right palm's MC-head line 20 mm below the grip top on its left face |
| Trigger face from the back strap | 65–70 | E | the extended index sits above the trigger guard, tip 25 mm short of the mag release at (28, −120, −20) |
| Handguard across flats | 38 × 45 (slim M-LOK) | S (weapon note: real 45–55, drawn 59) | left-hand C-clamp closure |
| `Rifle.HandguardFrame` | (0, **170**, 0), +Y to the muzzle, +Z to the rail; top-left facet at (−22, 170, +24) | M/E (D5) | left palm |
| Butt pad centre; muzzle device end | (0, −415, 0 bore / −45 pad centre); (0, 434, 0) | S | the two placement pins |

### 3.6 Bone naming map (`scripts/lib/rig.py::BONE_MAP`, role → MPFB `default` → Rigify DEF (generated from `rigify.human`) → Godot humanoid)
Rigify DEF names are those Rigify generates from the metarig bone names dumped from `rig.human.json` (`spine`…`spine.006`, `shoulder.L`, `upper_arm.L`, `forearm.L`, `hand.L`, `palm.01–04.L`, `f_index/middle/ring/pinky.01–03.L`, `thumb.01–03.L`, `thigh.L`, `shin.L`, `foot.L`, `toe.L`, `heel.02.L`, face bones); the `.001` suffix is the twist half Rigify adds to limb segments [VERIFY by dumping after one generation].

| Role | MPFB `default` | Rigify DEF | Godot humanoid | Notes |
|---|---|---|---|---|
| ROOT (pelvis control) | `root` | `DEF-spine` (hips) / control `torso` | `Hips` | location + rotation of the whole body |
| PELVIS_HALF | `pelvis.L/R` | `DEF-pelvis.L/R` | — | hip-centre carriers, not animated |
| SPINE_LOW … UPPER | `spine05`, `spine04`, `spine03`, `spine02`, `spine01` | `DEF-spine.001 … .003` (`spine.004` is the neck base) | `Spine` ← spine05+04, `Chest` ← spine03, `UpperChest` ← spine02+01 | Godot has three trunk bones; the map lists spine04 as Spine, spine03 Chest, spine01 UpperChest; spine05/02 unmapped (keep their rest) |
| NECK_LOW/MID/HIGH | `neck01`, `neck02`, `neck03` | `DEF-spine.004`, `.005` | `Neck` ← neck02 | neck01/03 unmapped |
| HEAD | `head` | `DEF-spine.006` | `Head` | hair, brows, lashes parent here |
| JAW, EYES | `jaw`, `eye.L/R` | `DEF-jaw`, `DEF-eye.L/R` | `Jaw`, `LeftEye`/`RightEye` | |
| CLAVICLE | `clavicle.L/R` | `DEF-shoulder.L/R` | `LeftShoulder`/`RightShoulder` | |
| SCAPULA_CAP | `shoulder01.L/R` | — (Rigify has `DEF-shoulder-helper`) | — | Copy Rotation 0.35 of the upper arm's swing |
| UPPERARM, UPPERARM_TWIST | `upperarm01.L/R`, `upperarm02.L/R` | `DEF-upper_arm.L/R`, `DEF-upper_arm.L/R.001` | `LeftUpperArm` ← upperarm01 | 02 unmapped (twist helper) |
| FOREARM, FOREARM_TWIST | `lowerarm01.L/R`, `lowerarm02.L/R` | `DEF-forearm.L/R`, `.001` | `LeftLowerArm` ← lowerarm01 | |
| HAND | `wrist.L/R` | `DEF-hand.L/R` | `LeftHand` | |
| METACARPALS 2–5 | `metacarpal1…4.L/R` | `DEF-palm.01…04.L/R` | — | Godot's ThumbMetacarpal is the only metacarpal in the profile |
| THUMB | `finger1-1/1-2/1-3` | `DEF-thumb.01/02/03` | `LeftThumbMetacarpal/Proximal/Distal` | |
| INDEX … LITTLE | `finger2-1/2/3` … `finger5-1/2/3` | `DEF-f_index/middle/ring/pinky.01/02/03` | `LeftIndexProximal/Intermediate/Distal` … `LeftLittle…` | |
| THIGH, THIGH_TWIST | `upperleg01.L/R`, `upperleg02.L/R` | `DEF-thigh.L/R`, `.001` | `LeftUpperLeg` ← upperleg01 | |
| SHIN, SHIN_TWIST | `lowerleg01.L/R`, `lowerleg02.L/R` | `DEF-shin.L/R`, `.001` | `LeftLowerLeg` ← lowerleg01 | |
| FOOT | `foot.L/R` | `DEF-foot.L/R` | `LeftFoot` | |
| TOES | `toe1-1 … toe5-3`; `toes_master.L/R` (added, non-deform) | `DEF-toe.L/R` | `LeftToes` ← toes_master | |
| HEEL, BALL, PATELLA | `heel.L/R`, `ball.L/R` (spec 01), `patella.L/R` (spec 03) | `heel.02.L/R` (metarig only) | — | added bones; non-deform except patella |
| BREAST | `breast.L/R` | `DEF-breast.L/R` | — | weights zeroed |

---

## 4. Geometry construction plan

Everything is executed by `scripts/parts/08_rig_pose.py` and the `pose`/`simulate`/`bake`/`export` stages of `scripts/build_all.py`, headless, with helpers in `scripts/lib/rig.py`, `pose.py`, `rifle_place.py`, `corrective.py`, `attach.py`. Context rule from research C §7: `temp_override` for object-level operators; **real selection** (`select_set` + `view_layer.objects.active`) for `object.mode_set`, `object.parent_set`, `pose.visual_transform_apply`, `pose.armature_apply`, `object.vertex_group_*`. Idempotence: the script deletes every object named `IK.*`, `Rig.Diag.*`, the action `Hero.Pose` and the bones it added before rebuilding; it never deletes bones MPFB created.

### 4.1 Step 1 — Rig fit (`rig.py::fit_rig(basemesh)`), after every body target of specs 03–06 is loaded
`HumanService.add_builtin_rig(basemesh, "default", import_weights=True)` → rename the armature `Morgan.Rig`, the mesh stays `Body.Mesh`; both at the world origin (MPFB moves the armature, not the mesh — set `rig.location = (0,0,0)` and verify `basemesh.matrix_world` is identity). Then `rig.py::dump_bones(rig, "renders/08_rig/bones.json")`: head, tail, length, `matrix_local` axes for all 163 bones. Verify against the expectations (±5 mm unless stated): `upperleg01.L/R` heads (±88, Y0, **963**); `lowerleg01.L/R` heads Z 526 ± 4; `foot.L/R` heads Z 80 ± 3; `upperarm01.L/R` heads (±275, Y0 − 20, 1476 ± 10); `lowerarm01.L/R` heads 340 ± 3 from the GH; `wrist.L/R` heads 272 ± 3 from the elbow; `head` tail Z 1835 ± 5 (skull top less scalp); `eye.L/R` heads Z 1740 ± 3, X ±33. A miss means the body targets are wrong, not the rig: the script raises with the offending bone and stops. Re-run the fit whenever targets change (`add_builtin_rig` is idempotent: it rebuilds from the joint cubes).

### 4.2 Step 2 — Added bones (edit mode with the real selection)
| Bone | Head → tail (W, rest) | Parent | Deform | Owner / purpose |
|---|---|---|---|---|
| `heel.L/R` | pternion on the floor (±208 in the stance build; in rest ±100, 0, 0) → +Y 20 | `foot.L/R` | no | spec 01; IK pivot and foot-roll point; the sole datum for the flat-foot check |
| `ball.L/R` | 1st MT head medial point → +X 20 | `foot.L/R` | no | spec 01; measurement marker for the last and boot |
| `toes_master.L/R` | MTP line (±40, −210, 25) → along the MT-head line | `foot.L/R` | no | spec 01; `Copy Rotation` (local, 1.0) onto every `toeN-1`; toe spring |
| `patella.L/R` | patella centre (±93, −44, 521) → −Y 20 | `upperleg02.L/R` | yes | spec 03; `Copy Rotation` 0.5 from `lowerleg01`, X only, local |
| `Rig.Marker.COM` | computed each pose | `root` | no | readback marker only, not exported |

No IK helper bones: IK targets and poles are **Empties** (§4.5), deleted after the bake so the export carries no rigging scaffolding.

### 4.3 Step 3 — Canonical bone frames (`rig.py::canonical_rolls(rig)`)
Purpose: make "bone-local" mean the same thing on every bone so the pose table (§4.6) can be written and read. In edit mode, for each bone, `edit_bone.align_roll(v)` with v the bone's **anterior/dorsal reference direction**, so that after the roll: local **Y** runs head → tail along the segment; local **Z** points to the anterior/dorsal side; local **X = Y × Z** is the flexion axis. Then **+X rotation = flexion** (nod forward for the spine and neck, thigh/arm swinging forward, elbow and knee bending, finger curling; for the foot +X = dorsiflexion); **rotation about Y = twist** (axial rotation); **rotation about Z = ab/adduction** (lateral swing). Signs of twist and Z-swing differ per side and are given per side in §4.6.

| Bones | v (anterior/dorsal reference) |
|---|---|
| `root`, `spine05…01`, `neck01…03`, `head`, `jaw` | world −Y (forward) |
| `clavicle.L/R`, `shoulder01.L/R` | world −Y |
| `upperarm01/02`, `lowerarm01/02` | world −Y in the rest pose (the arm hangs; anterior = forward) |
| `wrist`, `metacarpal1–4`, `finger*` | the hand's **palmar** normal (so +X = finger flexion toward the palm); computed as the normal of the plane through the wrist head, MCP2 and MCP5, pointing palmar |
| `pelvis.L/R` | world −Y |
| `upperleg01/02`, `lowerleg01/02`, `patella` | world −Y |
| `foot`, `heel`, `ball`, `toes_master`, `toe*` | world +Z (dorsal) |
| face bones, `eye`, `tongue*`, `breast` | left as MPFB made them (not posed by this part) |

Rolls change nothing visible: the rest pose is the identity, vertex weights are untouched. The anatomical frame of a bone is **A_b = rest world matrix after rolling**. `rig.py::anatomical_to_pose(bone, flex, abd_signed, twist)` builds the pose as a swing-then-twist quaternion in A_b: `q = q_z(abd) ⊗ q_x(flex) ⊗ q_y(twist)` applied in the bone's rest frame, then `pose_bone.rotation_mode = 'QUATERNION'` and `pose_bone.rotation_quaternion = q` (the rest-relative local rotation is exactly the rotation in A_b because Blender's pose-bone rotation is expressed in the bone's rest frame). For IK-solved bones the stored value is whatever the bake produces and the anatomical numbers are **derived** for reporting with `Quaternion.to_swing_twist('Y')` (mathutils): twist = the Y twist, flexion = the swing's X component, abduction = its Z component.

### 4.4 Step 4 — Weights clean-up (`rig.py::finalize_weights(mesh)`), run LAST after the part scripts' weight rules (specs 01 §7.2, 03 §7.2, 04 §7.2, 05 §7.2)
1. `breast.L/R` groups → 0 (male chest: the pectoral is on `spine01/02`).
2. The helper vertices (`HelperGeometry`, `JointCubes`) keep their own weights; they are masked, never exported (`Hide helpers` MASK stays first in the stack; the game export deletes them, §7.6).
3. `bpy.ops.object.vertex_group_limit_total(group_select_mode='BONE_DEFORM', limit=4)` with the real selection, then `vertex_group_normalize_all(group_select_mode='BONE_DEFORM', lock_active=False)`; verify numerically (numpy over `v.groups`): every body vertex has 1–4 influences with Σw = 1 ± 1e-4; any vertex with Σw = 0 is reported with its index and nearest bone and fixed by assigning 1.0 to that bone.
4. Twist ramps (the parts own the numbers; this step checks them): along each `*01/*02` pair the weight of the 02 bone must be monotonic in the segment parameter s (spec 05: humeral twist 0.35 at s 10 % → 1.0 at 60 %; pronation 0 → 0.6 at 50 %, 1.0 beyond; spec 03: thigh 60/40 linear, shank 50/50). The check samples 20 rings per segment and fails if any ring's mean 02-weight decreases by more than 0.05.
5. `Armature` modifier on `Body.Mesh`: object `Morgan.Rig`, `use_deform_preserve_volume = True`, first in the stack after the MASK; the parts place `Corrective Smooth` (`rest_source 'ORCO'`, factor 0.5, iterations 5, restricted to their joint groups) directly after it, before `Subdivision`.

### 4.5 Step 5 — Posing scaffolding (Empties, constraints; `pose.py::build_scaffold()`)
Empties (`empty_display_type 'ARROWS'`, size 0.05) in a collection `Rig.Scaffold`, hidden in renders except V7:

| Empty | Position (W, mm) / orientation | Role |
|---|---|---|
| `IK.Target.Foot.R` / `.L` | ankle axis R (−208, +75, 80), L (+208, −75, 80); rotation = the foot heading (R 85° toward his right about Z, L 17° toward his left) | IK target of `lowerleg02.R/L` (`use_tail True`) |
| `IK.Pole.Knee.R` / `.L` | knee position + 400 mm along the facing: R (−0.707, −0.707, 0), L (+0.208, −0.978, 0) | pole targets; `pole_angle` solved (§4.7) |
| `IK.Target.Hand.R` / `.L` | copies of `Hand.R/L.PalmFrame` moved to the wrist axis (−100 mm along the hand's long axis from the MC-head line) | IK target of `lowerarm02.R/L`; `wrist.*` gets `Copy Rotation` from the PalmFrame |
| `IK.Pole.Elbow.R` / `.L` | expected elbow + 400 mm along the arm plane's outward normal: R start (−382, +70, 1201) → outward (−0.8, +0.5, 0); L start (+310, −110, 1151) → (+0.9, −0.4, 0) | pole targets; `pole_angle` scanned to put the elbow on its pixel (§4.7) |
| `Rifle.Root` (object, owned by spec 15) | §4.8 | master of the grip and handguard frames |
| `Rifle.GripFrame`, `Rifle.HandguardFrame`, `Rifle.Collider` | children of `Rifle.Root` at the §3.5 offsets | hand placement and contact solve |
| `Rig.Floor` (plane 3 × 3 m at z 0) | — | collider for the flat-foot check and the trouser hem |

IK constraint parameters (`pose_bone.constraints.new('IK')`): legs on `lowerleg02.*`: `target` the foot Empty, `pole_target` the knee Empty, `chain_count 4` (upperleg01 → lowerleg02), `use_tail True`, `use_stretch False`, `iterations 500`. Per-bone IK locks so the 01/02 helper splits never bend: `upperleg02.*`: `lock_ik_x/y/z True`; `lowerleg01.*` (knee hinge): `use_ik_limit_x True, ik_min_x 0°, ik_max_x 150°, lock_ik_y True, lock_ik_z True`; `lowerleg02.*`: all three locked (the ankle is set afterwards, §4.7 step e); `upperleg01.*` (hip): limits X −30…+120°, Y ±50° (twist), Z −30…+45° (sign per side), `ik_stiffness 0`. Arms on `lowerarm02.*`: `chain_count 4` (upperarm01 → lowerarm02); `upperarm02.*` locked; `lowerarm01.*` hinge X 0…150°, Y/Z locked; `lowerarm02.*` locked (pronation is set before the solve and survives the lock); `upperarm01.*` limits X −60…+180°, Y ±90°, Z −30…+180°. Twists on locked axes are set **before** the solve (`lowerleg01.R` Y = tibial external 20°, `.L` 5°; `lowerarm02.R` Y = pronation 70°, `.L` 40°; `lowerarm01` 30 % of each) and keep their values through it.

### 4.6 Step 6 — The hero pose as data (`pose.py::HERO`)
All angles in degrees; "world" means measured against the camera axis; "local" means the canonical frame of §4.3 (X flex, Y twist, Z lateral swing). Rest reference for the anatomical angles: anatomical neutral (arms hanging, palms to the thighs, legs straight, feet forward) — **not** MakeHuman's rest; the conversion is §4.3's. Items marked IK are solved and the values are expected readbacks.

**Pelvis and trunk (FK)**
| Bone | Anatomical | Bone-local (X flex, Y twist, Z lateral) | Evidence |
|---|---|---|---|
| `root` location | pelvis centre at W (**−30**, 0, Z solved ≈ 945; expected 935–950) | `location` = posed − rest (rest head (0, 63, 995) at 1855) | D1, D6; the 1-D height solve of §4.7 (b) |
| `root` rotation | yaw −10° (to his right), pitch +2° anterior tilt, roll 0 | `root` points forward (its local Y is the body's forward axis), so its local frame is not the spine convention; set it **in world space** as the matrix Rz(−10°)·Rx(+2°) about its head via `pose_bone.matrix` (local readback ≈ (+2, 0, −10) in XZY order) | consolidated §1 |
| `spine05` | 0 (sacrum rigid with the pelvis) | (0, 0, 0) | — |
| `spine04` | yaw +2 (unwinds toward his left), extension 1, right lateral flexion 2 | (−1, +2, −2) | spec 04 §7.3 D5 |
| `spine03` | yaw +2, extension 1 | (−1, +2, 0) | |
| `spine02` | yaw +1, extension 1 | (−1, +1, 0) | |
| `spine01` | 0 | (0, 0, 0) | net chest yaw −5 world, extension 3 |
| `clavicle.R` | protraction 8 (acromial end forward 22 mm), elevation 2 | (+8, 0, **−2**) — for the right clavicle +Z is depression | pose note; spec 04 |
| `clavicle.L` | elevation −3 (depressed, the arm hangs) | (0, 0, **−3**) — for the left clavicle +Z is elevation | |
| `shoulder01.L/R` | follow: `Copy Rotation` from `upperarm01` (swing only via `use_x/use_z`, local space) influence **0.35** (2:1 scapulohumeral rhythm) | — | spec 04 said 0.5; flagged |
| `neck01` / `neck02` / `neck03` | yaw +3 / +4 / +5; extension 0 / 1 / 1 | (0, +3, 0) / (−1, +4, 0) / (−1, +5, 0) | yaw split, spec 04 §7.2 |
| `head` | yaw +13 (→ +25 vs chest, **+20 world**), extension 3 (chin up), roll 0 to −2 | (−3, +13, 0) | consolidated §2; spec 07 interface |
| `eye.L/R` | 4° further left, 3° up | set as a `Track To` on `Rig.Marker.Gaze` at W (+2200, −6000, 2000) [E] | pose note §5 |
| `jaw` | closed | (0, 0, 0) | |

**Right arm (IK + FK)**
| Bone | Anatomical | Bone-local / mechanism | Evidence |
|---|---|---|---|
| `upperarm01.R` | flexion **−15** (accepted −8 to −25), abduction **+20**, internal rotation **+45** (35 % of the twist here) | IK readback; twist split by weights not by bone (both 01 and 02 receive the same quaternion from the solve; the skin ramp does the splitting) | D2, spec 05 §7.3 |
| `upperarm02.R` | rigid with 01 | locked | |
| `lowerarm01.R` | elbow flexion **97**; carries 30 % pronation | hinge from IK; Y = +21 (30 % of 70; for the right forearm +Y is pronation) | |
| `lowerarm02.R` | pronation **70** | Y = +70, locked in IK | |
| `wrist.R` | extension 12, ulnar deviation 10 | `Copy Rotation` from `Hand.R.PalmFrame`; expected local (−12, 0, −10) | spec 05 §4.8 |
| fingers R | Table A of spec 05 §7.3 (thumb CMC palmar abd 30 flex 15 MCP 30 IP 25; index 5/5/0 abd +8; middle 85/95/50; ring 85/95/50 abd −3; little 80/90/45 abd −6) | local X per phalanx = flexion; Z = abduction; then the contact solve (±12° cap) | spec 05 |

**Left arm (IK + FK)**
| Bone | Anatomical | Bone-local / mechanism |
|---|---|---|
| `upperarm01.L` | flexion **+12**, abduction **+8**, internal rotation **+20** | IK readback |
| `lowerarm01.L` | elbow flexion **55**; Y = −12 (30 % of 40; for the left forearm pronation is −Y) | hinge |
| `lowerarm02.L` | pronation **40** | Y = −40, locked |
| `wrist.L` | flexion 10, radial deviation 10 | from `Hand.L.PalmFrame`; expected local (+10, 0, +10) |
| fingers L | Table B of spec 05 §7.3 (thumb CMC radial abd 50, MCP 10, IP 15 across the rail; index 60/85/45 +6; middle 62/85/45 +2; ring 65/85/45 −2; little 70/80/40 −6) | FK then contact solve |

**Legs (IK + FK)**
| Bone | Anatomical | Bone-local / mechanism | Evidence |
|---|---|---|---|
| `upperleg01.R` | flexion **−5**, abduction **+14**, external rotation **45** (relative to the yawed pelvis) | IK swing; twist set explicitly after the solve so the knee faces 45° right of the camera axis: for the right thigh external rotation is **+Y** | D3; spec 03 §7.3 |
| `upperleg02.R` | rigid | locked | |
| `lowerleg01.R` | knee flexion **17**, tibial external rotation 20 | hinge X from IK; Y = **+20** (right shank: external = +Y) set before | |
| `lowerleg02.R` | rigid | locked | |
| `foot.R` | plantigrade: sole on z = 0; heading **85°** to his right; eversion 3 (0 inside the boot) | set by matrix after IK (§4.7 e); expected ankle readback within ±10° of neutral | D3 |
| `upperleg01.L` | flexion **+8**, abduction **+10**, external rotation **22** | IK; external = **−Y** on the left | |
| `lowerleg01.L` | knee flexion **9**, tibial external 5 | hinge; Y = **−5** | |
| `foot.L` | plantigrade; heading **17°** to his left (15–20); 150 mm forward of the right (Y −75 vs +75) | matrix after IK | consolidated §1 |
| `toes_master.*`, `toe*` | 0 (flat inside the boots; the boot's toe spring is the boot's) | (0, 0, 0) | spec 01/02 |
| `patella.*` | follow (Copy Rotation 0.5) | — | spec 03 |

**Stance readback targets (W, mm):** ankle-to-ankle 416, heel-to-heel 308 ± 10, toe-to-toe 678 ± 15 (right toe at X ≈ −420 in profile), knee-to-knee 346 ± 10 (knee axis centres), hip-to-hip 176, pelvis centre X −30 ± 10, COM ground projection at 55 ± 5 % toward the right ankle (computed from the evaluated meshes' volumes with the rifle at 3.6 kg and the gear masses of spec 13/14, or the body alone if they are absent — report both).

### 4.7 Step 7 — Posing procedure (`build_all.py::pose()` → `pose.py::apply_pose(HERO)`), in order
(a) **Reset**: all pose bones to identity; delete `IK.*`; `scene.frame_set(1)`; action `Hero.Pose` created empty.
(b) **Pelvis**: `root` world rotation Rz(−10°)·Rx(+2°) about its head; location X −30, Y 0, Z from the height solve: golden-section search on Z ∈ [900, 980] (8 iterations, 1 mm resolution) minimising (flexR − 17)² + (flexL − 9)² where the flexions are the knee readbacks after step (d) at that height — the legs are re-solved inside the loop (each IK evaluation is a `view_layer.update()`, milliseconds).
(c) **Trunk, neck, head, clavicles, eyes**: FK values of §4.6 via `anatomical_to_pose`; `view_layer.update()`.
(d) **Legs**: twists set on the locked axes; IK constraints added with the §4.5 parameters; `pole_angle` solved per leg by scanning −180…180° in 2° steps and picking the angle minimising |knee facing − target| (facing = the knee bone's local −Z... i.e. the shin's anterior axis projected on XY); then a 0.25° refinement; residual (`lowerleg02` tail − target) must be < 0.5 mm.
(e) **Feet**: `foot.R/L` world matrix = heading rotation about Z (R 85° toward −X, L 17° toward +X) × the rotation that puts the `Foot.Last` sole plane (three vertices: pternion, 1st and 5th MT heads of the last from spec 01) on z = 0; set with `pose_bone.matrix = ...` after `view_layer.update()` of the parents; check every sole vertex |z| < 1 mm; `toes_master` 0.
(f) **Rifle**: `rifle_place.py::place(rifle_root)` (§4.8): either the fixed matrix or the two-pin solve against the live camera and `Vest.Collider`; outputs `Rifle.Root.matrix_world`, the frames follow as children.
(g) **Hands and arms**: `Hand.R/L.PalmFrame` from the rifle frames (spec 05 §4.8 steps 1 and 4); `IK.Target.Hand.*` = PalmFrame moved 100 mm proximal along the palm's long axis; pronations set on the locked axes; IK added; `pole_angle` scanned in 2° steps minimising the **pixel error** of the elbow (`lowerarm01` head projected with `world_to_camera_view` against (632, 328) R / (958, 352) L), tie-break toward the pole positions of §4.5; `wrist.*` `Copy Rotation` (world → world) from the PalmFrame. Readback: right shoulder extension must fall in −8…−25°, left flexion 7…17°; elbow flexions 97 ± 5 / 55 ± 5; else the script reports which constraint failed and keeps the elbow pixel (D2).
(h) **Fingers**: FK tables then `grip.py::close_finger()` (spec 05) against `Rifle.Collider`; the thumbs as spec 05 says; the index on the receiver's right face.
(i) **Readback and bake**: with the real selection of `Morgan.Rig` and all bones selected, `bpy.ops.pose.visual_transform_apply()`; remove every IK and Copy constraint this stage added (the part-owned `Copy Rotation` on `shoulder01`, `patella`, `toes_master` stay); `keyframe_insert` on `rotation_quaternion` (and `location` of `root`) for every pose bone at frame 1 of `Hero.Pose`; frame 0 holds the identity (rest). Write `renders/08_rig/pose_report.json`: per bone the quaternion, the derived anatomical angles, the segment directions, the stance numbers, the landmark pixel errors (§8.2), the COM.
(j) **Correctives**: drivers evaluate automatically; `Hero.Compress` custom property on `Morgan.Rig` set to 1.0 (drives the strap/belt compression keys of specs 03/04/09; 0 in the game rest).
(k) **Renders** V1–V7 (§8.1).

### 4.8 Step 8 — Rifle master transform (`rifle_place.py`)
Nominal (from §2.2; the solve re-derives it from the live camera and `Vest.Collider`, and must reproduce these within 5 mm / 1°):
* `Rifle.Root` origin (bolt face on the bore at the receiver face) at **W (−67, −346, 1014)**.
* Axes in W: rifle +X (right side) **(−0.271, −0.883, 0.384)**, +Y (to the muzzle) **(0.441, −0.468, −0.766)**, +Z (up, rail) **(0.856, −0.038, 0.516)**; as Blender XYZ Euler **(−56.0°, −22.6°, −107.0°)**; as a quaternion (w, x, y, z) **(0.4408, −0.4127, 0.2678, −0.7508)**. Build it as `Matrix((X, Y, Z)).transposed().to_4x4()` with the translation — do not type the Euler.
* Pins: butt-pad centre (0, −415, −45) → W (−288, −150, 1309) → px (695, 268); muzzle device end (0, 434, 0) → W (125, −549, 682) → px (903, 571).
* Solve: with the camera from spec 17 (`scripts/eval/camera.py`), ray-cast the two pixels; the butt pad's depth is fixed by contact (nearest point of `Vest.Collider` on the right pectoral patch X −120…−220, Z 1280…1340, plus 0–3 mm); the muzzle depth follows from the 849 mm length (closed form, two solutions — take the one with the muzzle nearer the camera); roll about the bore so the right-face normal has zero component along (bore × camera direction); verify the frames' pixels: `Rifle.GripFrame` → (727, 352) ± 6, `Rifle.HandguardFrame` → (840, 467) ± 8.
* The rifle is **master**: both hands are IK-targeted to its frames. After the bake the rifle object is **bone-parented to `wrist.R`** (`parent_type 'BONE'`, `matrix_parent_inverse` set so nothing moves) so that the game sees one hierarchy; in Godot the weapon is a `BoneAttachment3D` on `wrist.R` (interface §10).

### 4.9 Finger controls (non-exported convenience; `pose.py::finger_props()`)
Custom properties on `wrist.L/R`: `curl_thumb`, `curl_index`, `curl_middle`, `curl_ring`, `curl_little` (0…1), `spread` (−1…1). Drivers (`SCRIPTED`, variables of type `SINGLE_PROP`) on each phalanx's local X: MCP = 90·curl, PIP = 100·curl, DIP = 60·curl (ratio 1 : 1.1 : 0.6 as spec 05's contact solve); thumb CMC flex 15·curl, MCP 40·curl, IP 50·curl; Z abduction = spread × (+8, +3, −3, −8) for index…little. The hero contact solve writes final values straight into the bones **and** sets the properties to the equivalent curls, then mutes the drivers (`driver.mute = True`) so the baked pose is literal. Drivers are stripped on export (glTF has none); the morph targets carry the correctives instead.

### 4.10 Corrective shape keys — mechanism, inventory, driving angles (`corrective.py`)
`make_corrective(mesh, rig, pose_dict, ops, name, driver)`: pose the rig to `pose_dict`; evaluate `Body.Mesh` (Armature + Corrective Smooth only); run the part's `soft_*` ops in posed space; **inverse-skin** every edited vertex to rest with the blended inverse matrix `inv(Σ_i w_i M_i)` (numpy over the ≤ 4 influences); store as a shape key; add the driver. Driver convention: `SCRIPTED` expression over `TRANSFORMS` variables on the named bone, `transform_space 'LOCAL_SPACE'`, `rotation_mode 'SWING_TWIST_Y'` so `ROT_Y` is the twist and `ROT_X`/`ROT_Z` the swing components, mapped with `smoothstep((a − a0)/(a1 − a0))` and `hold` beyond a1. Inventory this part guarantees exists and drives (the ops live in the parts):

| Key (per side) | Driver bone, channel | 0 → 1 over | Owner |
|---|---|---|---|
| `Leg.Corr.KneeFlex90`, `.KneeFlex130` | `lowerleg01` ROT_X | 30→90°; 100→130° | spec 03 |
| `Leg.Corr.HipFlex`, `.HipAbd`, `.HipExtRot` | `upperleg01` ROT_X; ROT_Z; ROT_Y | 30→90; 0→25; 0→45 | spec 03 |
| `Torso.Corr.NeckTurn.L/R` | sum of `neck01–03` + `head` ROT_Y (four variables) | 0→30 | spec 04 |
| `Torso.Corr.ArmAcross.L/R` | `upperarm01` ROT_Y × ROT_Z product | 0→45 and 0→20 | spec 04 |
| `Torso.Corr.Shrug`, `.Breathe` (if spec 04 keeps them) | `clavicle` ROT_Z; `Hero.Breath` prop | 0→15; 0→1 | spec 04 |
| `Arm.Corr.ElbowFlex90/130`, `.Pronate`, `.ShoulderAbd/Flex` | `lowerarm01` ROT_X; `lowerarm02` ROT_Y; `upperarm01` ROT_Z/ROT_X | spec 05 table | spec 05 |
| `Hand.Corr.Grip.R`, `.Clamp.L`, finger `MCP/PIP` keys (36) | phalanx ROT_X | 0→90 | spec 05 |
| `Foot.Corr.WeightBearing` | `Hero.Weight.R/L` props (0.55 / 0.45) | — | spec 01 |
| `Leg.Compress.Straps/Belt`, `Torso.Compress.*` | `Hero.Compress` prop | 0→1 | specs 03/04 |

Export: the glTF exporter drops drivers, so `export_game.py` writes the hero values of every driven key into one `Corr.Hero` morph target and exports the individual keys as morph targets with weight 0 (`export_morph True`); Godot's animation can drive them if the game ever poses beyond the hero.

### 4.11 Topology and budget
This part adds no render geometry. Diagnostics (V7 only): `Rig.Diag.Joint.<bone>` icospheres (subdiv 2, 320 tris, radius 12 mm) at 40 joint centres; `Rig.Diag.Pole.*` lines (curves); the armature drawn as `display_type 'OCTAHEDRAL'`. Scaffold objects live in `Rig.Scaffold`, excluded from `Export.*` collections.

---

## 5. Materials and textures

The rig carries no textures. Diagnostic materials for V7 and the overlay pass: `Rig.Mat.Joint.R` emission **#ff5a3c** (his right), `Rig.Mat.Joint.L` emission **#3cff8a** (his left) — the colour code is the soldier's own side, stated in the V7 caption; `Rig.Mat.Pole` emission #ffd23c; `Rig.Mat.Target` emission #3ca0ff. Weight heat maps: a Geometry Nodes modifier `Rig.GN.WeightViz` (added for V7 only) reads the named vertex group chosen by a string input, stores it as a colour attribute through a blue → cyan → yellow → red ramp (0, 0.25, 0.6, 1.0), and `Rig.Mat.WeightViz` shows it unlit; one V7 sheet per limb bone pair (`upperarm01/02.L`, `lowerarm01/02.L`, `upperleg01/02.L`, `lowerleg01/02.L`, `neck01/02/03`). Overlay compositing (PIL, `scripts/eval/overlay.py`): reference converted to luminance, render in colour, blended 50/50, the landmark crosses drawn in #ffd23c and the rig's projected joints in #3ca0ff with a line between each pair; a second image with the reference at 100 % and only the projected bones as a stick figure. All overlays saved under `renders/08_rig/` and the latest V1 copy in `renders/eval/08_rig_overlay.png`.

---

## 6. Fibres, simulation and dynamics

No fibres or dynamics belong to this part; it fixes the **order** in which the other parts' simulations run, because cloth must be simulated on a posed collider and skinned garments must be weighted on a rest body:

1. **Fit in rest** (A-pose, MPFB rest): body targets, rig fit, every garment's tube or shell built around `Body.Mesh` in rest (specs 09, 10, 11, 13, 14), gear blockouts placed on their rest anchors.
2. **Weights in rest**: garments that are skinned (shirt, gloves, socks, boots, trousers' game variant) take `DataTransfer VGROUP_WEIGHTS` from `Body.Mesh` (nearest face interpolated), then the parts' overrides, then `finalize_weights`.
3. **Pose** (§4.7) on frame 1 of `Hero.Pose`; the rig's own transition rest → hero is keyed over frames 1–30 (linear quaternion interpolation) purely to give the cloth solver a moving collider.
4. **Simulate**: `Body.Collider` (decimated posed body, `Collision` modifier, thickness 3 mm) follows the Armature over frames 1–30; cloth on the trousers (spec 09), the gaiter (spec 10), the shirt (spec 10) runs frames 1–60 (30 to arrive, 30 to settle) with `scene.frame_set` stepping (deterministic, research C §2); straps shrink over frames 30–60 to bite (spec 09 §6.3).
5. **Bake**: `modifier_apply` the Cloth at frame 60 under `temp_override(object=…)` → static posed garment meshes; Shrinkwrap/Solidify/Displace detail passes; **the hero garments are then bound by `SurfaceDeform` to `Body.Mesh.Posed`** (so small pose nudges of a few degrees follow without re-simulation, spec 09 §7), not by the Armature.
6. **Attach** gear (§7) on the posed body, compress straps (`Hero.Compress` = 1).
7. **Render** the evaluation set; **export** (§7.6) from the rest-posed skinned variants (the game needs skinned garments, not posed statics): the trousers/shirt/gaiter export their rest tubes with transferred weights; the hero drape is a second, hero-only asset.

Hair (specs 03, 05, 07) follows the body through surface attachment (`Deform Curves on Surface`) or bone parenting to `head`; nothing simulates.

---

## 7. Rigging and attachment

### 7.1 Attachment rules per object (`attach.py`), chosen by how the real item is held on the body
Methods: **BONE** = `parent_type 'BONE'` to one bone (rigid, exact, export-safe as a child of the armature; Godot: `BoneAttachment3D`); **SKIN** = Armature modifier with transferred/authored weights (deforms; exports as a skinned mesh); **SURF** = `SurfaceDeform` bound to a named skinned mesh (hero only; export baked as SKIN via weight transfer); **COPY** = `Copy Transforms` from an Empty that is itself bone-parented (used when a part needs a stable frame to build on before the bone exists).

| Object (spec) | Real attachment | Method | Bone(s) / weights | Strap compression and notes |
|---|---|---|---|---|
| Pauldron tiers 1–2 (12) | ride the deltoid, hung from the carrier strap by a webbing tab | SKIN, rigid groups | tier 1–2: `upperarm01` 0.5 / `clavicle` 0.3 / `shoulder01` 0.2 (uniform over the plate) | the tab's `Copy Location` to `Torso.Curve.Strap.*`; tier 3 bicep band SKIN `upperarm02` 1.0; `Arm.Compress.BicepBand` −1.5 mm under the 50 mm band |
| Antenna / cylinder (12/13) | bolted to the rear plate bag | BONE | `spine01` (upper thoracic, with the carrier's rear bag) | 5° backward lean preserved in the parent inverse |
| Forearm guards (12) | strapped to the forearm over the sleeve | SKIN, rigid | plates `lowerarm02` 1.0 (wrist band), main plate `lowerarm02` 0.7 / `lowerarm01` 0.3, elbow band `lowerarm01` 1.0 | `Arm.Compress.Guard` −1.5 mm under each 25 mm strap; the guard rotates with pronation because `lowerarm02` carries it |
| Elbow cap, left (and mirrored right) (12) | elastic over the lateral epicondyle | SKIN | `lowerarm01` 0.6 / `upperarm02` 0.4 | sits 20 mm lateral of the epicondyle via `Arm.*.ElbowAnchor` |
| Kneepad caps (12) | in the trouser knee sleeve, rear strap through the popliteal band | SKIN, rigid | `lowerleg01` 0.7 / `upperleg02` 0.3 over the cap; strap SKIN with the trousers' weights | cap centred on `Leg.*.KneeAnchor`; +15 mm lateral on the left (spec 03) |
| Plate carrier front bag, admin panel, pouches (13) | rigid armour plate against the chest | SKIN, nearly rigid | `spine01` 0.85 / `spine02` 0.15 over the bag; pouches follow the bag's weights (DataTransfer) | `Torso.Compress.Carrier` −4 mm under the bag footprint |
| Carrier rear bag, cummerbund (13) | plate on the back; elastic band round the waist | SKIN | rear `spine01/02` 0.6/0.4; cummerbund `spine03` 0.5 / `spine02` 0.3 / `spine04` 0.2 | the cummerbund flexes with the flank |
| Shoulder straps and ladder-locks (13) | over the trapezius | SURF to `Body.Mesh.Posed` (hero); SKIN transfer for export | from the body: `clavicle`/`spine01`/`neck01` mix | `Torso.Compress.Strap` −3 mm under the 70 mm pads |
| Belt and buckle (14) | on the trouser waistband | SKIN, rigid ring | `root` 1.0 (whole ring; it rides the pelvis) | `Leg.Compress.Belt` −3 mm (spec 03); hangs 2 mm off the trousers |
| Right drop-leg panel, twin carriers (14) | hanger strap from the belt, two thigh straps | SKIN | panel and tubes `upperleg02.R` 0.8 / `upperleg01.R` 0.2 (rigid), hanger strap graded `root` 1.0 at the belt → `upperleg01.R` 1.0 at the panel top | `Leg.Compress.Straps` −2 mm under the 38 mm straps (spec 03 §4.7); ladder-locks 45° round the front |
| Left drop-leg block and strap (14) | as right, one thigh strap | SKIN | `upperleg02.L` 0.8 / `upperleg01.L` 0.2 | |
| Upper right two-cell pouch (14) | on the carrier's lower side PALS | SKIN with the cummerbund's weights | `spine03/02` | |
| Gloves (11) | worn | SKIN | hand/finger weights copied from `Body.Mesh` (`DataTransfer`, nearest face), ≤ 4 influences | built on `Hand.*.GloveLast`; the hero keys baked |
| Combat shirt, gaiter (10) | worn; simulated in the hero | SURF (hero) / SKIN (export) | body weights transferred | the gaiter's top ring follows `neck02` 0.6 / `head` 0.4 |
| Trousers (09) | worn; simulated | SURF (hero) / SKIN (export) | spec 09 §7 bands | |
| Socks, foot (01) | skin | SKIN | spec 01 §7.2 | |
| Boots (02) | laced | SKIN by rule (no auto-weights) | `foot`, `lowerleg02` ramp (spec 02 §7.1); laces and hardware SURF to `Boot.*.Upper` | |
| Hair, brows, lashes (07) | scalp | BONE | `head` | |
| Stubble (07) | skin | GN `Deform Curves on Surface` on `Body.Mesh` | — | |
| Eyes, teeth, tongue (06) | — | BONE `eye.L/R`, `jaw`/`head` | | |
| Rifle (15) | held | BONE `wrist.R` after the bake (§4.8) | — | master during the solve |
| Emblem plate, clip-on box, rivets, studs (12) | screwed to the pauldron | parented to the pauldron object (`parent_set OBJECT`, keep transform) | — | the pauldron's weights carry them |

Rule for strap compression: every strap, belt or band that bites into flesh or cloth has a vertex-group footprint on the surface below it (`*.Compress.*` keys owned by the surface's part), driven by the rig's `Hero.Compress` property (1 in the hero, 0 in the game rest), magnitude = the real indentation (−1.5 mm for a 25 mm strap on a hard guard, −2 mm for a 38 mm thigh strap on trousers, −3 mm for a belt or 70 mm pad on cloth over flesh, −4 mm for the plate bag), with a +0.8 to +1 mm bulge ridge 6–8 mm outside each edge.

### 7.2 Export bone set and the game rig
Exported: all 163 MPFB bones + `heel`, `ball`, `toes_master`, `patella` (×2 each) = **171 bones**; `Rig.Marker.*` deleted before export. Non-deform helpers (`heel`, `ball`, `toes_master`) are harmless in Godot. If the client prefers a lean game skeleton (§10.2 Q3), `export_game.py --lean` re-parents the face bones' weights onto `head`, merges the `*02` twist bones into `*01`, drops the metacarpals onto `wrist`, giving 61 bones — a weight-merge script, not a different rig.

### 7.3 Rigify as an optional artist rig (not in the pipeline's critical path)
Rigify generation works headless (research B §2): `HumanService.add_builtin_rig(basemesh, "rigify.human", import_weights=True)` → 185-bone metarig on the same joint cubes → `bpy.ops.pose.rigify_generate()` → `Human.rigify`, 930 bones in 2.1 s. Decision: **the deform/export skeleton is the MPFB `default` rig; Rigify is generated only on request for Jeff's interactive GPU session** (`scripts/tools/make_rigify.py`): it writes `Hero.Pose` onto the Rigify controls through `BONE_MAP` (IK hands/feet from the baked wrist/ankle matrices, torso/neck/head FK), so Jeff can nudge the pose by hand; `read_rigify.py` reads the DEF bones back into the `default` rig's pose and the pipeline continues from there. Reasons for not making Rigify the deliverable: the six finished specs are written on the `default` names; 163 deform bones with imported weights versus 930 of which ≈ 160 deform and the rest are controls Godot cannot use; glTF export of Rigify needs `export_def_bones` and loses nothing we need but adds a bone-name translation to every part; scripted IK is a 40-line function here and needs no control bones.

### 7.4 Hero-pose transition and additional poses
`Hero.Pose` holds frame 0 = rest, frame 1 = hero (and frames 1–30 as the cloth-solver ramp in the simulation scene only). The hexcom rules' crouch (eye 1.10 / body 1.25) and prone (0.35 / 0.45) poses are **out of scope** for the build but the IK limits, hinge locks and the KneeFlex130/HipFlex correctives are kept so `pose.py` can take a `CROUCH` or `PRONE` dict later (§10.2 Q6).

### 7.5 Verification of the posed rig (also §8)
After the bake the script projects every bone head/tail with `world_to_camera_view` using the spec-17 camera and compares with §8.3; renders V1 as a 50 % overlay; writes the pixel-error table into `pose_report.json`; fails the stage if any scored landmark exceeds its tolerance.

### 7.6 glTF export requirements (`scripts/export_game.py`; property names verified against Blender 4.5.14)
1. Build the `Export.*` collection from the rest-posed skinned variants: `Body.Mesh` (helpers deleted for real: `bmesh` delete of the `HelperGeometry` and `JointCubes` groups on a copy, so the MASK modifier is not needed), skinned garments, gear, boots, gloves, hair as curves converted to cards or omitted [VERIFY: Godot hair strategy, spec 07]; `Subdivision` set to level 1 and applied **per shape key** with `export_prep.py::apply_modifiers_keep_shapes()` (duplicate per key, apply, rejoin as shapes — the exporter's `export_apply` would drop shape keys); `Corrective Smooth` and `Displace` applied the same way; Armature left as the only modifier.
2. Wrapper: duplicate everything under `Export.Root` (Empty, rotation Z 180° so the character faces Godot's −Z, scale **0.9704**); `transform_apply(location, rotation, scale)` on the duplicates and on the armature data (`pose.armature_apply` is not needed — rest stays rest; the applied object transform rescales the bones).
3. `bpy.ops.export_scene.gltf(filepath="export/sgt_morgan.glb", export_format='GLB', use_selection=True, export_apply=False, export_yup=True, export_skins=True, export_influence_nb=4, export_all_influences=False, export_def_bones=False, export_rest_position_armature=True, export_hierarchy_flatten_bones=False, export_armature_object_remove=False, export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True, export_frame_step=1, export_optimize_animation_size=True, export_reset_pose_bones=True, export_morph=True, export_morph_normal=True, export_morph_tangent=False, export_tangents=True, export_texcoords=True, export_normals=True, export_materials='EXPORT', export_image_format='AUTO', export_vertex_color='MATERIAL', export_attributes=False)` under `temp_override(selected_objects=…)` (the exporters honour it, research C §7).
4. Also write `export/sgt_morgan_hero.glb` (the posed hero statics, no skin, for reference) and `export/godot_bone_map.json` (the §3.6 Godot column) plus `export/pose_report.json`.
5. Reimport test in a fresh scene (`import_scene.gltf`): bone count 171, action `Hero.Pose` present, morph targets present, rest height 1800 ± 2, forward axis check (the nose tip's X/Z in glTF space), no vertex with zero weights (the importer would log it).

---

## 8. Evaluation protocol

### 8.1 Renders (`scripts/eval/render_rig.py`, Workbench matcap + cavity for all views, 5 s each; V1–V3 additionally Cycles 48 spp under the spec-17 lights for the critic round)
V1–V7 as §1.3, each written to `renders/08_rig/V<n>_<variant>.png` with variants `form` (Workbench), `overlay50` (PIL blend with the named reference crop, both scaled to the crop's resolution), `sticks` (reference + projected bones) and, for V7, `weights_<bone>`. `scene.render.use_persistent_data = True`; the camera objects come from `scripts/eval/camera.py` (the spec-17 hero camera plus the six closeups defined here).

### 8.2 Metrics (`scripts/eval/rig_metrics.py`, all numeric, written to `pose_report.json`)
* **Landmark pixel errors**: projected bone points vs §8.3 (Euclidean px); the hip row reported with the expected deviation.
* **Angle readbacks**: every §4.6 anatomical value derived by swing-twist decomposition; deltas to the table.
* **Lengths**: GH–elbow, elbow–wrist, hip–knee, knee–ankle from the posed bone heads vs §3.1 (they must not change with pose — a change means stretch or a broken parent).
* **Stance**: the §4.6 readback targets; sole-plane error (max |z| over the `Foot.Last` sole vertices); heading angles from the `foot` bone's Y projected on XY.
* **Contacts**: BVH nearest distances (`mathutils.bvhtree.BVHTree.FromObject`) from each finger-pulp centroid and the palm patch to `Rifle.Collider`; penetration depth by signed distance (ray-cast parity); butt pad to `Vest.Collider`.
* **Candy-wrapper test**: for each twist zone (forearm s 20–90 %, thigh 20–80 %, neck) take 12 edge rings of the evaluated mesh, compare each ring's circumference and area with rest; fail if any ring loses > 25 % circumference or any face normal flips against the rest normal (dot < 0).
* **Deformation test poses** (not the hero): elbow 0/45/90/130, knee 0/45/90/130, hip flex 90, shoulder abd 90, head yaw ±60 — the same ring test plus a self-intersection count (`bmesh.ops` intersect on the evaluated mesh, count faces) which must be 0 at ≤ 90° and ≤ 20 faces at 130°.
* **Weights**: influence histogram after clean-up (must be 1–4), Σw bounds, zero-weight vertices.
* **COM**: volume-weighted centroid of the evaluated meshes (masses: body 83 kg uniform by volume, rifle 3.6 kg, carrier + plates 9 kg, belt rig 3 kg, boots 1.4 kg each) and its floor projection's fraction toward the right ankle.
* **Export round-trip**: §7.6 step 5 numbers.

### 8.3 Scored landmarks and tolerances (V1, reference camera)
| Landmark | Reference px | Rig element | Tolerance | Expected from the real-proportion model |
|---|---|---|---|---|
| Skull top | (812, 20) | `head` tail + 12 mm scalp/hair | ±4 px | y 21 |
| Pupils | (800, 77) / (832, 77) | `eye.R/L` heads | ±3 px each | y 75 → head pitch/height tune ±1° |
| Shoulder joints | (675, 200) / (935, 200) | `upperarm01.R/L` heads | ±6 px | y 200 |
| Elbows | (632, 328) / (958, 352) | `lowerarm01.R/L` heads | ±8 px | pole solve |
| Wrists | (698, 345) / (870, 440) | `wrist.R/L` heads | ±8 px | from the rifle frames |
| Knees (pad centres) | (727, 650) / (890, 657) | `lowerleg01.R/L` heads + 25 mm anterior (pad) | ±5 px | y 651 |
| Ankles | (732, 855) / (928, 858) | `foot.R/L` heads | ±8 px | (739, 857) / (936, 865) |
| Soles | y 895 / y 907 | `heel.R/L` | ±3 px | y 894 / y 904 |
| Butt pad, muzzle | (695, 268) / (903, 570) | rifle pins | ±4 px | exact by construction |
| Hips (not scored) | (768, 505) / (862, 505) drawn | `upperleg01.*` heads | report | ≈ (776, 452) / (856, 452): the accepted D1 deviation |

### 8.4 Critic questions (answered yes/no with the view)
1. V1: does he stand with his weight on the rear right foot, or does he float between both? 2. V1/V4: is the pelvis turned to his right and the chest unwound toward the camera, with the head turned further left — three different yaws visible? 3. V2: does the right forearm come toward the camera almost horizontally with the dorsum of the hand facing us, the index straight along the receiver, the elbow pulled back? 4. V3: does the left arm hang with a 125° included elbow, the thumb across the rail and four fingertips stacked under the handguard? 5. V2/V3: is the rifle at 50° down and 43° left, butt on the right pectoral, right side to the camera, with no gap between the hands and the gun? 6. V4: do the knees face 45° right and 12° left with the right one visibly bent and the left nearly straight? 7. V5: is the right foot in near profile (85°) with its instep to us and the left foot 15–20° left, 15 cm forward, both flat? 8. V6: does the neck turn read as a spiral over three segments, the right sternocleidomastoid taut, with no pinch at the gaiter line? 9. V7: do the twist heat maps grade smoothly along forearms and thighs with no island of a single bone? 10. V1 overlay: does the only miss sit in the hips (higher than drawn), with the knees, feet, shoulders and head on their marks?

### 8.5 Failure modes and the fix
| Symptom | Cause | Fix |
|---|---|---|
| Rig fit lands bones away from §4.1 expectations | body targets wrong or joint cubes not re-grounded | the script stops; fix the part's targets; `deserialize_from_dict` re-grounding (research B) |
| IK bends at the 01/02 split | IK locks not set on the `*02` bone | §4.5 locks; test pose set |
| Knee or elbow flips backward | pole angle wrong by 180° | the pole scan picks the minimum; add the hinge limit 0…150 |
| Pelvis height solve oscillates | both legs cannot meet their knee targets at one height | report; relax L flexion to 5–15; never stretch (`use_stretch False`) |
| Right elbow cannot reach (632, 328) | real humerus + fixed wrist | accept −25° extension; if still > 8 px, move the wrist 10 mm up the grip (spec 05 allows ±4° about the grip axis), report |
| Feet hover or sink | foot matrix set before the parents updated | `view_layer.update()` before setting `pose_bone.matrix`; verify the sole plane |
| Candy wrapper at the forearm | twist ramp not monotonic / 02 weights too low near the wrist | §4.4 step 4 check; spec 05 ramp |
| Shoulder reads dislocated | `shoulder01` Copy Rotation influence too high or wrong axes | 0.35, swing only |
| Face deforms when the head turns | face bones carry > 4 influences and the limit step dropped the wrong one | run the limit step with `BONE_DEFORM` after zeroing `breast`; check the histogram |
| Garments lag or tear after a pose nudge | SurfaceDeform bound before the final body stack | rebind after the parts' stacks are final; bigger nudges re-simulate |
| glTF export has no shape keys | `export_apply True` or modifiers still on the mesh | §7.6 step 1 bake, `export_apply False` |
| Godot imports the model facing +Z | wrapper rotation missing | `Export.Root` Z 180° applied |
| Reimported height ≠ 1800 | scale applied to the armature object but not the data, or vice versa | apply on both duplicates; test step 5 |

---

## 9. Build order, effort and risks

| # | Step | Tool | Run time | Author effort | Risk |
|---|---|---|---|---|---|
| 1 | `fit_rig`, `dump_bones`, expectation check | MPFB `add_builtin_rig` | 1 s | 2 h | low |
| 2 | Added bones (heel, ball, toes_master, patella) | edit-bone API, real selection | 1 s | 1 h | low |
| 3 | Canonical rolls, `anatomical_to_pose`, swing-twist readback | mathutils | 0.5 s | 4 h | medium (sign conventions — unit-test with single-axis poses) |
| 4 | Weights clean-up and ramp checks | `vertex_group_limit_total`, numpy | 2 s | 2 h | low |
| 5 | Scaffold, IK locks/limits, pole scans | constraints API | 2 s | 4 h | medium |
| 6 | Pelvis height solve, feet flattening | numpy, `pose_bone.matrix` | 1 s | 3 h | medium |
| 7 | `rifle_place.py` two-pin solve | ray casts, BVH | 0.5 s | 3 h | medium (depends on spec 15's frames) |
| 8 | Hand frames, arm IK, finger contact solve (with spec 05) | BVH, constraints | 3 s | with spec 05 | high: three constraints meet here (pixels, bone lengths, grip) |
| 9 | Bake, `Hero.Pose`, `pose_report.json` | `visual_transform_apply`, keyframes | 1 s | 2 h | low |
| 10 | `corrective.py` mechanism + driver convention | shape keys, drivers | 1 s/key | 4 h | medium (inverse skinning precision) |
| 11 | `attach.py` rules and compression property | parenting, DataTransfer, SurfaceDeform | 5 s | 4 h | low |
| 12 | Renders V1–V7, overlays, metrics | Workbench, PIL | 60 s | 4 h | low |
| 13 | `export_game.py`, round-trip test | glTF exporter, per-key apply | 60–120 s | 6 h | medium (shape-key bake, Godot check needs Jeff's machine) |
| 14 | Optional Rigify artist rig | `rigify_generate`, BONE_MAP | 3 s | 4 h | low |

Total: ≈ 45 h of authoring, under 4 minutes of runtime for a full rig + pose + export. Milestones to commit: after 4 (rigged rest body with `bones.json`), after 9 (posed hero with the overlay passing), after 13 (export round-trip).

Risks beyond the table: (1) the **reality-wins hip height** changes specs 03/04/09 numerics (the torso stretch, the hip-band weights, the trouser rise table) — the critique pass must propagate it before any part is built on the rig; (2) **spec 15** must supply the frames at the §3.5 offsets or the hand solve has nothing to grip — blockout rifle from the weapon note's dimensions until then; (3) the MakeHuman **rest arm pose** (40° abduction, bent elbow) may make Godot's humanoid retarget look odd without a T-pose rest (§10.2 Q4); (4) four influences may be too few for the face if the game ever animates it — Godot's 8-weight import is the fallback [VERIFY]; (5) the two-bone split per segment means Godot's humanoid map leaves the `*02` bones unmapped; retargeted animations will not twist them (acceptable for a turn-based game; the lean export merges them).

---

## 10. Interfaces and open questions for the client

### 10.1 What each other part needs from the rig, and what the rig needs from it
| Part | The rig provides | The rig needs |
|---|---|---|
| 01 Foot, ankle, sock | `foot`, `lowerleg02`, toe bones at the §4.1 heights; `heel/ball/toes_master` created here from spec 01's positions; hero ankle axes (±208, ∓75, 80); feet flat; headings **85° R** (was 90), 17° L; `Hero.Weight.R/L` = 0.55/0.45 | `Foot.Last` sole vertices (pternion, MT1, MT5 heads) for the flat-foot alignment |
| 02 Boots | `BONE_MAP` names; the shaft weight ramp is spec 02's; heading change to 85° + 15° toe-away | `Boot.*.Upper` for the SurfaceDeform of laces/hardware |
| 03 Leg and pelvis | hip centres **Z 963 rest** (D1 overrules 851/829); pelvis centre (−30, 0, ≈945) yaw −10 pitch +2; knee flexions 17/9; facings 45° R / 12° L; `patella` constraint; the IK closure now lives here (§4.7 b–e), spec 03's §7.3 becomes a call to it; corrective driver convention | `FEMUR_MM` → 437 and the thigh/hip targets re-solved; `Leg.*.KneeAnchor`, `Leg.Compress.*` keys; twist ramps 60/40, 50/50 |
| 04 Torso and neck | trunk/neck/head FK values (§4.6); GH height **1476** (not 1452); `shoulder01` influence 0.35 (not 0.5) | the torso stretch of 102 mm removed (D1); `Torso.Compress.*`; neck bands |
| 05 Arms and hands | arm IK with the elbow-pixel pole solve; `Rifle.HandguardFrame` at **170 mm** (not 198); accepted right-shoulder extension −8…−25; finger props; Tables A/B consumed as data | `Hand.*.PalmFrame` construction, `grip.py::close_finger()`, the hand joint-cube fix before the rig fit, twist ramps |
| 06 Head and face | `head`, `jaw`, `eye.*` bones; head yaw +20 world, pitch −3; gaze marker | `Head.Anchor.*` Empties bone-parented to `head` |
| 07 Hair and grooming | `head` bone exposed for `parent_type BONE`; its hero pose | nothing |
| 09 Trousers | posed bone chain (hip 945, knee 516/519, ankle 80), `Body.Mesh.Posed`, `Body.Collider`, `Hero.Compress`; the simulate/bake order of §6 | the rest tube built on the rest body; weight transfer for export |
| 10 Shirt, gaiter | as 09; `neck02`/`head` mix for the gaiter top | — |
| 11 Gloves | hand weights by transfer; `Hand.*.GloveLast` is spec 05's | — |
| 12 Hard armour | attachment table §7.1; `Arm.*.GuardFrame`, `Arm.*.ElbowAnchor`, `Leg.*.KneeAnchor`, `Torso.Anchor.*` | plates with the compression footprints named |
| 13 Plate carrier | `spine01/02/03` weights; `Torso.Curve.Strap.*`; `Vest.Collider` **needed by the rifle solve** (butt contact) | the carrier's right-pectoral surface at X −120…−220, Z 1280…1340 |
| 14 Belt, drop-leg rigs | `root` for the belt ring; thigh weights; hanger grading | strap footprints at spec 03/09's heights |
| 15 Carbine | `Rifle.Root` transform (§4.8); the two pins; parent to `wrist.R` after the bake | `Rifle.GripFrame` (0, −194, −76), `Rifle.HandguardFrame` (0, 170, 0), `Rifle.Collider`, real OAL 849 from the pad to the muzzle device end |
| 16 Materials | nothing | diagnostic materials are this part's |
| 17 Evaluation scene | V1–V7 definitions, the overlay tool, `rig_metrics.py` | `camera.py` (hero camera (0, −4500, 600), 46 mm, rot (93.9°, 0, 0)), lights |
| 18 Pipeline | the stage order fit → weights → pose → simulate → bake → attach → render → export | `build_all.py` scaffolding, caching of `assets/body/body_rigged.blend` after step 4 |
| hexcom game | `export/sgt_morgan.glb` (171 bones, 4 influences, `Hero.Pose`, morph targets, 1.80 m, faces −Z), `export/godot_bone_map.json` | confirmation of the import settings (§10.2 Q2, Q4, Q5) |

### 10.2 Questions for the client
1. **Hip height (reality wins):** confirm hips at 963 mm (posed ≈ 945, pixel y ≈ 452) and a trouser crotch kept at the drawn 763 as a dropped-crotch cut — the full-figure overlay will show the hips 55 px higher than the picture. The alternative (drawn hips) keeps the overlay but puts a 74 % femur in the game asset.
2. **Game scale and eye height:** scaling to 1.80 m puts the eye at 1.688 m; the rules say 1.65. Accept 1.688, or scale to 1.767 m (eye 1.65), or move the rules' constant?
3. **Game skeleton:** full 171 bones (face bones, metacarpals, twist helpers) or the lean 61-bone merge?
4. **Rest pose for Godot:** keep MakeHuman's A-pose with bent elbows as the bind pose (Godot's humanoid "fix silhouette" normalises it) or re-bind to a clean T/A-pose (an extra bake step with the shape keys re-skinned)?
5. **Weapon in game:** rifle as a `BoneAttachment3D` child of `wrist.R` with the hero hand pose baked (recommended), or a separate asset with its own socket?
6. **Future poses:** should the build deliver crouch (1.25/1.10) and prone (0.45/0.35) poses now (two more pose dicts, corrective checks at knee 130) or only keep the capability?
7. **Right foot 85° instead of 90–100°:** accept the anatomical maximum, or allow a 95° foot by letting the hip exceed its normal range (it will look forced)?
8. **Rigify artist rig** for Jeff's GPU session: build the optional tool (4 h) or pose by editing `pose.py` only?

### 10.3 Items tagged [VERIFY]
* Hip joint centre spacing 176 (170–185 adult male), GH centre 48 below the acromion, functional humerus 340 vs 315 — anatomy references not opened; measured by the overlay at build (elbow and shoulder pixels decide).
* AAOS ranges of motion in §3.2 (from memory).
* Rigify DEF bone names after generation (`.001` twist halves; `DEF-spine.004/.005` as the neck); dump once.
* Godot 4.7 `SkeletonProfileHumanoid` bone names and the 8-bone-weight import flag; whether "fix silhouette" copes with the MakeHuman rest.
* Blender 4.5 glTF `export_apply` dropping shape keys (the per-key bake sidesteps it either way).
* Pistol grip dimensions and the trigger-guard position in spec 15's build frame; the handguard across-flats.
* `root` bone head position after targets (the dump at 1834 mm gives (0, 62, 984)); whether MPFB's fit keeps `root` behind the pelvis joint when the pelvis targets change.
* Spec 01's `Foot.Last` sole vertex names for the flat-foot alignment.
