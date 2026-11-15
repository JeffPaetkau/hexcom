# Round 0: the body and the pose

PLAN.md, take 2, round 0. These scripts build the rest body with its skeleton, solve the hero pose as
data, and render the evaluation. Every command runs from the project folder after `source cache/env.sh`.
They are headless and idempotent.

| Step | Command | Time (RTX 3050) | Outputs |
|---|---|---|---|
| keypoints (once) | `"$SGT_PYIMG" -I scripts/stages/keypoints.py` | 3 s | `scripts/stages/ref_keypoints.json` |
| 1 base | `"$SGT_BLENDER" -b --python scripts/stages/base.py` | 4 s | `cache/stages/base.blend`, `cache/stages/base.json` |
| 2 pose | `"$SGT_BLENDER" -b cache/stages/base.blend --python scripts/stages/pose.py -- --solve` | 19 s | `scripts/stages/hero_pose.json`, `cache/stages/pose.blend`, `cache/stages/pose_check.json` |
| 3 evaluate | `"$SGT_PYIMG" -I scripts/stages/eval_round0.py [--no-cycles]` | 12 s | `renders/round_00/*` |

`--solve` runs `pose_solve.py` (numpy and scipy, in `$SGT_PYIMG`) before it applies the pose. Without
`--solve`, pose.py applies the committed `hero_pose.json` as it is. The solver can also run on its own:
`"$SGT_PYIMG" -I scripts/stages/pose_solve.py` (8 to 16 s).

## 1. base.py: the body

- **MPFB 2.0.17**, created with take 1's macros (specs 03/04): gender 1, age 40 (macro 0.615), muscle
  0.70, weight 0.45, proportions 0.5, caucasian 1. The height macro is fitted to a **rest stature of
  1835 mm** (skull top to sole, barefoot) by take 1's bracketed Illinois search: macro 0.5834 gives
  1834.96 mm.
- **Body targets** for the drawing's lean V-taper and for real arm segments. Each one was measured
  before it was kept (`base.json` → `measure`):

  | target | weight | why |
  |---|---|---|
  | `torso-vshape-incr` | 0.50 | V-taper |
  | `measure-shoulder-dist-incr` | 0.20 | broader shoulders. 0.40 put the shoulder joints 432 mm apart, wider than the joints in the image |
  | `hip-scale-horiz-decr` | 0.15 | the drawing's narrow hips (MPFB's hip joints are 231 mm apart; a real man's about 176) |
  | `measure-waist-circ-decr` | 0.10 | lean waist |
  | `measure-upperarm-length-incr` | 1.00 | MPFB's default male has the elbow 268 mm below the shoulder joint; real is about 340. Now 338 |
  | `measure-neck-circ-incr` | 0.30 | thick, muscular neck |
  | `torso-muscle-pectoral-incr`, `l/r-upperarm-muscle-incr` | 0.30, 0.40 | muscular build |

  Result: chest girth 993 mm, waist 750, hips 979, neck 386, upper arm 318, forearm 247, thigh 546,
  calf 374. Shoulder joints 422 mm apart. Joint heights: hip 986, knee 533, ankle 75, shoulder joint
  1477, eye 1722 mm. Girths are the convex hull of an exact plane section, which is what a tape
  measure reads.
- **Placement** (CLAUDE.md rule 2). The lowest vertex is put on z 0 and the midpoint of the ankle joint
  cubes over the origin. The body faces -Y and +X is his left. The move is baked into the mesh, so the
  objects keep an identity matrix.
- **Rig**: MPFB's `default` skeleton (163 bones) with MPFB's own weights, named `Morgan.Rig`. The mesh is
  `Body.Mesh`. Both are in the collection `Body`, with the MHCLO assets `Body.Eyes` (high-poly,
  procedural material), `Body.Eyebrows` (eyebrow006) and `Body.Eyelashes` (eyelashes02). The skin is
  MPFB's default material. There is no hair and no clothing. (Round 1 changed the targets, the brows, the skin
  and the eye materials: see "Round 1" at the end.)
- **base.json** holds the macros, targets, stature, measurements, and every bone's rest head, tail and
  `matrix_local` (mm, rig space = world). It also holds the surface landmarks the pose fits, each tied
  rigidly to one bone: skull top, nose tip, chin, ears, pupils, the right pectoral, and per foot the
  heel, toe, 1st and 5th metatarsal heads.

## 2. pose_solve.py and pose.py: the hero pose

**Forward kinematics outside Blender.** The solver rebuilds MPFB's skeleton from the rest matrices,
posing each bone the way Blender does (`posed = posed_parent @ rest_parent⁻¹ @ rest @ basis`).
`pose_check.json` compares the result with Blender's own pose: they agree to 0.008 mm. The 79
parameters are:
- the pelvis rotation and position;
- five spine bones, three neck bones and the head (3 each);
- clavicles, shoulders, wrists, hips and ankles (3 each);
- elbow and knee hinges (flexion about the rest bend axis for the elbow and the lateral axis for the
  knee, plus a small twist);
- forearm pronation (on `lowerarm02`);
- the carbine (6).

They are fitted by `scipy.optimize.least_squares` (trf, bounded). Three starts all converge to the same
cost, so the solution is unique.

**Evidence**, each term divided by its sigma:
- **Reprojection through take 1's hero camera** (`scripts/eval/camproj.py`, used as is). The targets
  are in `TARGETS` in pose_solve.py, each with its source:
  - MediaPipe pose-landmarker heavy on the reference (`ref_keypoints.json`, 3 scales averaged);
  - take 1's hand-read landmarks;
  - for the eyes, nose, chin and right ear (skin), the hand reading, tight.

  Joint centres were chosen over outlines. MediaPipe reads the shoulder joints under the pauldrons;
  the hand reading of 675/935 is the pad edge. Elbows are the pad and cap moved 30 mm in. Knees fall
  between MediaPipe and the pad centres. The ankles sit 52 px above the soles: the ankle axis is 75 mm
  plus the footbed.
- **The carbine.** It starts from a two-pin solve: butt-pad centre (695, 268) at the carrier's depth,
  muzzle (903, 570), length 840 mm, right side to the camera. In the main solve it is free:
  - butt pin held to 4 px; muzzle only to 12 px;
  - butt pad 50 mm in front of the right pectoral's skin along the chest axis (shirt, pad, plate, bag);
  - roll prior 10°.

  The drawn carbine is shorter than a real one (77 cm projected). A real 840 mm gun held exactly on
  both pins points 25° at the camera and pulls the left hand far ahead of the drawn left forearm,
  which lies in the image plane.
- **Hands on the carbine.** The index and little-finger knuckles go to grip points in the carbine
  frame (6 mm), and the wrist loosely (30 mm). The palm centre must lie on the grip surface and face
  its axis, so the hand may roll on its knuckle line. The right hand is on the pistol grip, knuckles
  along a real grip raked 25°. The left hand is an overhand clamp over the handguard 170 mm ahead of
  the receiver face: palm on the top/left facet, fingers over the camera side to the underside, index
  nearest the receiver.
- **Feet on the boots' footbeds.** Heel seat 36 mm, ball seat 24 mm (Zephyr class, take 1 spec 02). Each
  foot point keeps its rest height above the sole. Headings are 85° to his right (right foot) and 17°
  to his left (left foot) of the camera axis (spec 08 D3).
- **Priors and limits:**
  - each joint stays near rest (spine 4°, neck 6°);
  - pelvis yaw -10 / pitch +2, chest yaw -5, head yaw +20 (world);
  - knees: flexion 17 and 9, facing 45° right and 12° left, never under 3° (no hyperextension);
  - elbows: flexion 97 and 55, range 10–145;
  - wrists: priors from the pose note, soft limits at flexion 70 / extension 60 and ulnar 30 / radial 20;
  - left foot about 150 mm nearer the camera;
  - centre of mass (Dempster shares plus the 3.4 kg carbine) over the feet, 55/45 to the right;
  - elbows and wrists kept outside the chest.

**Fingers** are set by curl tables, not fitted. Each phalanx turns about the axis that closes it toward
the palm.
- Right hand: middle, ring and little at 85/95/50; the index extended 30° along the receiver; the thumb
  around the back of the grip.
- Left hand: all four fingers at 60–70/80–85/40–45; the thumb across the top.

**hero_pose.json** contains:
- `bones`: bone → local pose-basis quaternion (w, x, y, z), and `root_location`, the basis location of
  the `root` bone;
- `joints_world_mm`;
- `carbine_frame`, in this convention, which the carbine part shares:
  - origin on the bore directly above the trigger;
  - +X along the bore to the muzzle, +Z up through the rail, +Y to the gun's left;
  - `matrix_world` in rig space;
  - `parent_bone` `wrist.R`, with `matrix_in_parent_bone` relative to the posed `pose_bone.matrix`
    (origin at the bone's head, not Blender's tail-based bone parenting);
  - the stand-in's points;
  - `grip_points_mm` (pistol grip and handguard) and the hand targets in that frame;
- the per-joint residuals, readbacks and the solver status.

**Using the pose elsewhere:** `from pose import apply_hero_pose, add_carbine_proxy` (with
`scripts/stages` on `sys.path`). Then `apply_hero_pose(bpy.data.objects["Morgan.Rig"])`.
`add_carbine_proxy` makes `Pose.Carbine.Frame`, an empty bone-parented to `wrist.R`, and
`Pose.Carbine.Proxy`, a block M4 840 mm long built in that frame, in the collection `Pose`.

## 3. eval_round0.py: the evaluation

pose.blend is rendered through the hero camera and the ref.soldier_full crop (box 580,20,1020,935 at
×2), as Workbench clay and quick Cycles (32 spp). Lights come from scene.py at 0.3 of spec 17's energy.
It also renders:
- the posed body from front, both sides, both three-quarters and top;
- the hands close up (along the camera line and from the side);
- the rest pose from front and side.

`compare_soldier.png` places the reference, clay and Cycles side by side. `overlay_soldier.png` shows:
- the reference at 50 %;
- the render's silhouette edge (cyan);
- fitted joints (green) against their targets (red; the line is the residual);
- MediaPipe's raw points (yellow);
- the carbine stand-in points (magenta).

`joints_px.json` holds the projections measured in Blender and the floor and head-top checks.

## Results (2026-11-14)

Per-joint residuals (px, full frame):

| Joint | Residual | Joint | Residual |
|---|---|---|---|
| pupils R / L | 2.1 / 3.9 | knees R / L | 2.7 / 9.0 |
| nose tip | 3.7 | ankles R / L | 1.5 / 2.7 |
| chin | 1.6 | wrist R | 18.8 |
| right ear | 9.8 | wrist L | 2.2 |
| skull top | 6.5 | hips R / L | 20.1 / 18.0 |
| shoulder joints R / L | 6.9 / 6.9 | | |
| elbows R / L | 4.4 / 10.1 | | |

Carbine: butt pin 3 px, muzzle 17 px.

Readbacks:
- Pelvis yaw -11°, chest yaw -10.5°, head yaw +11.4° (world).
- Knees 17.5° (R) / 9.8° (L) flexed. Elbows 102° / 47°.
- Wrists, flexion / ulnar: R 28° / 26°, L -14° / -6°.
- Foot headings -83° / +16°. Feet flat on the footbeds within 1 mm.
- Centre of mass 17 mm right of the 55/45 point.

## Decisions and what is still wrong

- **The camera works, but the drawing's head and feet disagree with it by about 2 %.** Spec 17's camera
  agrees with Blender's projection to 0.0001 px (`camera.py --selftest`). The drawn soles (y 895 / 907)
  put the feet 50–200 mm behind the origin's floor line. The solve follows the feet, so the posed
  pelvis stands 176 mm behind the origin; the root's posed location is data, and the rest body is
  still centred.
- **The head top is short at that depth.** The scalp projects at y 29–30. The drawn hair mass is at
  y 20, so the scalp should be at about 24: 6 px, or about 15 mm, short. Pushing the body toward the
  camera fixes the head and moves the feet about 8 px low instead. The drawn 875 px figure is 1.9 m
  tall at the depth its feet put it.
- **Hips are 18–20 px above the drawn joints.** Reality wins: the drawing's thighs are 28 % short.
- **The right hand is on a real pistol grip, about 110 mm behind the drawn one.** The drawn right
  hand and magwell sit forward of where a real AR's grip is. So the wrist lands 19 px from the drawn
  cuff, and the wrist is bent (28° flexion, 26° ulnar). That is inside normal range but more than the
  pose note's 12° extension / 10° ulnar.
- **The left palm only partly faces the handguard.** It is 57° off; the fist still clamps it.
- **Fingers are curl tables, not a contact solve.** They interpenetrate the block stand-in a little.
- **The head yaw is 11.4°, not the analysts' 20 ± 5°.** The pupils and nose pixels on MPFB's default
  face want less yaw; the right ear (9.8 px) wants more. The likeness work (head part) should revisit
  it once the face is shaped.
- **The right ear residual is 9.8 px.** MPFB's default face is not his face.
- **Chest yaw is -10.5° against the analysts' -5°.** The shoulders' pixels pull it.
- **The chest reads soft.** At weight 0.45 MPFB's male pectorals look slightly rounded in clay; the
  body part should sculpt them. The carrier hides them in the hero frame.
- **The PLAN says "head turned to his right"; the image and the analysis say to his LEFT** (nose
  toward the viewer's right). The solve follows the image.
- **Feet hover 21–36 mm above the floor.** They stand on footbeds that the boots will supply.
- **The muzzle is 17 px off its pin.** This is the deliberate trade above: the drawn carbine is shorter
  than a real one.

## Round 1 (2026-11-14): the body and head parts changed base.py

Details are in `scripts/parts/body.md` and `head.md`. base.py now applies:
- the body part's chest, neck, arm and leg targets;
- the face targets that `scripts/parts/head.py --fit` writes to `scripts/parts/head_fit.json`;
- MPFB's middle-aged Caucasian male skin (ENHANCED_SSS, toned to `#ab7d71`);
- brown irises with an iris material slot for Workbench, and skin-coloured lash cards and dark brown brow
  cards in Workbench (they made the red rims);
- `eyebrow001` instead of `eyebrow006`;
- `--render` for the body's rest clay views.

base.json's neck girth is now a tape square to the neck axis under the larynx. The old horizontal plane
cut through the lengthened chin; it is kept as `neck_horizontal_old`.

Stature is 1835.02 mm. The body targets move no joint cube. What moved:
- the face targets moved the head joint 6.5 mm down, neck02 7.4 mm and neck03 3.6 mm;
- the height refit moved every other joint by about 0.9 mm (twist bones up to 2.0 mm).

`pose.py --solve` was re-run on the new body. Residuals, round 0 → round 1 (px):

| Joint | Residual | Joint | Residual |
|---|---|---|---|
| pupils R / L | 2.1 → 2.9 / 3.9 → 3.5 | knees R / L | 2.7 → 2.5 / 9.0 → 8.9 |
| nose tip | 3.7 → 3.8 | ankles R / L | 1.5 → 1.4 / 2.7 → 2.4 |
| chin | **1.6 → 6.4** | wrist R | 18.8 → 18.6 |
| right ear | 9.8 → 8.5 | wrist L | 2.2 → 2.3 |
| skull top | **6.5 → 7.9** | hips R / L | 20.1 → 20.6 / 18.0 → 18.6 |
| shoulder joints R / L | 6.9 → 7.5 / 6.9 → 7.4 | | |
| elbows R / L | 4.4 → 4.2 / 10.1 → 9.8 | | |

- Solver cost: 39.34 → 40.58.
- Head yaw: 11.4° → 8.6° (world).
- The figure stands 15 mm nearer the camera (pelvis y 176 → 161 mm).
- Elbows 103° / 48°, knees 17° / 10°.
- The carbine pins are unchanged.

The chin got worse because the fitted face's menton sits lower relative to the pupils. MediaPipe reads the
reference's chin 4.8 px lower than the hand reading (y 135.8 against 131); head.md §3 has the fits tried. The
body joints' residuals moved by at most 0.6 px. Every part that binds to the rig or reads hero_pose.json
needs a re-run.
