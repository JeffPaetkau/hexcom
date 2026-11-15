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

## Round 2 (2026-11-14/15): the hold as contact, fitted fingers, a face term

Round 1's hold was a single-view fit (notes/research_canitcode.md, "What the second pass adds", point 1): it
reprojected well and was wrong in depth by centimetres, with the hands, the stock and the forearm inside the
carbine and the carrier. Round 2 adds the real surfaces to the solve.

### The surfaces (pose_contact.py, Blender) and how the solver reads them

`"$SGT_BLENDER" -b cache/stages/base.blend --python scripts/stages/pose_contact.py -- --export` (20 s) writes
`cache/stages/contact.npz`. `pose.py --solve` runs it first when a part cache, base.blend, pose_contact.py or
face_targets.json is newer than it (`--export` forces it: the carrier is sampled in the current pose).
- **The carbine** (`cache/parts/carbine.blend`, every `Carbine.*` mesh, all closed): inside/outside voxels at
  1 mm in the carbine frame (Carbine.Root's space), by ray parity along x, y and z (majority of three).
- **The carrier** (posed in the current hero pose, world, 1.5 mm voxels), with the posed matrix of `spine02`
  at export; the solver carries the field rigidly with spine02 (the bag's weights are spine02/03/04/01).
- **The surfaces that touch them**, as point sets skinned exactly as Blender skins them (rest vertices, the
  part's own top-4 bone weights, linear blend): the glove shells with their knuckle guards and PIP pads (the
  hands' outer surface, 1.8 mm over the skin), the shirt sleeves, the forearm guards, the hand skin (finger
  self-contact) and the 831 face vertices `face_targets.json` names.
- In the solver (`Contact`) the voxels become signed distance fields (mm, negative inside): Euclidean
  distance transforms; the carbine's hollows filled first (per slice across the bore, slots closed 4 mm, holes
  filled: the handguard's bore would otherwise read as outside) and the trigger guard's opening made a
  keep-out block (`TRIGGER_KEEPOUT_XZ`, a side-view polygon +-13 mm wide: no finger may enter the guard);
  smoothed one voxel; looked up trilinearly in float64. Built once into `cache/stages/contact_sdf.npz` (40 s).

Checked against round 2's clash report on the round-1 pose: glove R in the carbine 15.6 mm (clash report
15.7), glove L 7.1 (7.5), glove R in the bag 14.6 (15.4), sleeve in the stock 13.2 (13.4), guard 10.0 (9.6).
The carbine's surface samples found the receiver 22-26 mm into pouch 1 where the clash test, which tests the
carbine's coarse vertices only, said 14.

### The new terms (CONTACT, FINGER, PLACE in pose_solve.py)

| Term | What | Sigma |
|---|---|---|
| non-penetration | every glove point outside the carbine by 0.5 mm, sleeve and guard points by 1 mm; gloves, the forearm and upper-arm sleeve and guard points outside the carrier by 0.5 mm; the carbine's rear-half surface samples outside the carrier by 2 mm; a smooth hinge (softplus, 0.25 mm) per point | 0.5 mm |
| palm on its grip | the mean distance of the 12 palm-side glove points (wrist, metacarpals, thumb base) nearest the gun: 0.8 mm | 1 mm |
| butt on the carrier | the mean distance of the butt pad's 8 rear-face points nearest the carrier: 3 mm by the field (replaces round 0's "50 mm in front of the pectoral") | 0.8 mm |
| face | MediaPipe's 399 face landmarks on the reference against the same mesh points on the model (face_targets.json, from head.py's correspondences), weighted as 20 points at 2 px | 8.9 px each |
| hand targets | wrist and index/little knuckles to the placed hand (below) | 12 / 6 mm |
| right elbow prior | 88 deg (round 1: 97) | 10 deg |
| left foot heading | 5 deg (round 1: 17: the boots owner projected the drawn toe) | 6 deg |

Dropped while contact is on: round 0's palm-on-a-cylinder radius and palm-facing terms (the real grip decides).

### The order (solve())

1. Round 1's objective (keypoints and priors; three starts, 8 s).
2. **The right hand placed on the grip** (`place_hand`): the palm, the thenar and the first 90 mm of the forearm
   as one rigid body, turned about the grip's axis (-45 to +30 deg) and slid along it (-10 to +10 mm) from 18
   starts, then fitted (6 dof) to touch the grip without entering the gun or the carrier, the knuckle line kept
   along the grip at its design distance and height (the grasp). The result is the target the arm reaches for.
   Why: from round 1's pose the hand straddles the grip's tang and the stock's front strut (thenar and wrist
   12-15 mm inside) and every whole-body descent stalled there (the wrist jammed at 38 deg ulnar).
3. **Reach**: the body solve with the carbine's non-penetration off, so the arm can get there (it must pass
   through the gun to); then on, stiffening (sigma 2 mm, then 0.5).
4. **Fingers** (`fit_fingers`, each hand): per finger the MCP flexion and spread, PIP and DIP flexion (the
   thumb: two axes at its base), 20 per hand, from up to six starts (the last fit, the tables, nearly open,
   half closed, the thumb lifted either way). Terms: every finger glove point outside the gun (0.5 mm); each
   phalanx's palm-side glove touching it (mean of its 4 nearest, 0.6 mm; sigma 2 mm, 3 for the right index,
   2 for the right thumb); the gloves outside the other fingers' skin (each phalanx a cylinder about its bone,
   radius the 80th percentile of its skin, no tighter than the rest pose allows) and, for middle and distal
   phalanges, outside the palm's skin; the right index above the lower's bottom at the trigger (z -52 in the
   gun frame: trigger discipline, along the receiver); priors to the curl tables (30 deg; the thumb 15),
   spread 4 deg, DIP 0.7 PIP, neighbouring fingers curl alike (15 deg).
5. The body again with the whole glove (fingers fixed), the fingers again, twice.

`--continue-from <npz>` runs only fingers, one whole-glove body pass, fingers, from a saved solver state
(`cache/stages/pose_x_pass1.npz` is written by every full solve); `--refit-fingers` only the fingers.

A full solve takes about 25 minutes (round 1: 15 s): each body pass is a bounded trust-region least squares
over 79 parameters and about 42 000 residuals, Jacobian by finite differences (diff_step 1e-5).

Lessons now in the code: map_coordinates returns the grid's type, and float32 rounding swamped the finite
differences (the first solves stalled at cost 5000); a voxel distance field's gradient jumps from cell to
cell (smoothed); a stiff penetration penalty from a deeply penetrating start traps the hand (placement,
reach, then stiffening); a nearest-vertex sign between fingers is wrong (cylinders instead); a finger fitted
from the tables, already inside the gun, is pushed out the wrong side (starts from open).

### Changes during the round

- The trigger-guard keep-out: the first fits curled the right middle finger into the opening, onto the
  guard's thin rear leg, which no glove point was inside (clash: guard 6.5 mm in the glove, 4.6 in the skin).
- The carbine 2 mm off the carrier, the butt aiming at 3 mm by the field: the carrier's 1.5 mm field,
  smoothed, rounds the bag's bound corners (clash: the pad 2.8 mm into the bag's top-right corner where the
  field said 1.3 mm clear). After: 1.7 mm (the bag's PALS against the stock).
- The committed body comes by continuation (`--continue-from`): a fresh full solve after the keep-out change
  fell into a minimum with the left glove 5.5 mm in the handguard, while the earlier body was clean. Chain:
  the full solve of 2026-11-14 21:43 (`cache/stages/pose_x_try4.npz`) -> continued with the keep-out and the
  thumb prior (`pose_x_r2a.npz`) -> continued with the carrier margins (hero_pose.json, 2026-11-15 09:21).
- The carbine was rebuilt by its owner during the round (new stock); contact.npz was exported on the carbine
  of 21:00 and the carrier of 20:21.
- The session was cut overnight and resumed on the same base (stature 1835; PLAN.md's 1844 not applied).

### Residuals, round 1 -> round 2 (px, full frame)

"Keypoints only" is round 1's objective on today's inputs (the left foot heading now 5): the starting point.

| Joint | Round 1 | Keypoints only | Round 2 | Joint | Round 1 | Keypoints only | Round 2 |
|---|---:|---:|---:|---|---:|---:|---:|
| pupil R | 2.9 | 2.9 | 2.6 | wrist R | 18.6 | 18.3 | 13.9 |
| pupil L | 3.5 | 3.5 | 2.8 | wrist L | 2.3 | 2.4 | **20.5** |
| nose tip | 3.8 | 3.8 | 4.6 | hip R | 20.6 | 20.7 | 18.0 |
| chin | 6.4 | 6.4 | 7.4 | hip L | 18.6 | 18.7 | 15.2 |
| right ear | 8.5 | 8.5 | 4.2 | knee R | 2.5 | 2.5 | 4.0 |
| skull top | 7.9 | 7.9 | **13.9** | knee L | 8.9 | 8.5 | 8.7 |
| shoulder R | 7.5 | 8.1 | 12.1 | ankle R | 1.4 | 1.5 | 2.2 |
| shoulder L | 7.4 | 7.2 | 12.2 | ankle L | 2.4 | 2.2 | 2.6 |
| elbow R | 4.2 | 4.2 | **12.7** | butt pin | 3 | | 10.1 |
| elbow L | 9.8 | 10.1 | **15.2** | muzzle pin | 17 | | 17.1 |

- Where reality forced it: the arms (the right hand turned about 30 deg about the grip, the left hand moved
  17-19 mm off its design place onto the real handguard), the carbine (butt pin 10 px: the butt now rests on
  the bag instead of 26 mm in front of it), the skull top (the face term tilts the head 3.7 deg chin-up).
- The face: MediaPipe's 399 landmarks 1.88 px RMS in round 1, **1.05 px** now; the right ear 8.5 -> 4.2 px.
- Cost 65.3 (keypoints only: 41.2).

Readbacks: elbows R **91.4** (round 1: 102.7) / L 44.8 deg; wrists (flexion / deviation) R 17.4 / 30.5 (at
the soft ulnar limit), L 7.2 / -9.8; head yaw **13.7** (round 1: 8.6), pitch -0.7 (round 1: +3.0), roll -1.0;
chest yaw -8.4, pitch 10.4; pelvis yaw -9.9; knees 19.7 / 9.5; foot headings R -82.6, **L 4.8** (round 1:
16.2); carbine roll -24 deg (prior 0, sigma 10); skull top z 1836.6 mm. Blender vs the solver: 0.008 mm
(pose_check.json, fingers included).

### Contact (the solver's fields, mm; negative = inside)

| Surface pair | Keypoints only | Round 2 |
|---|---:|---:|
| right glove in the carbine | -14.1 | -0.11 |
| left glove in the carbine | -6.6 | +0.42 |
| right glove in the carrier | -13.7 | +78 |
| right sleeve / guard in the carbine | -6.7 / -9.7 | +12.2 / +7.4 |
| carbine in the carrier | -21.8 | +0.68 |
| butt pad to the carrier (mean of 8 nearest) | +26.4 | +1.0 |
| right / left palm to its grip (mean of 12 nearest) | -10.6 / -6.1 | +0.99 / +0.22 |
| fingers' gloves to the other fingers' skin, R / L | | +0.17 / +0.51 |
| each right phalanx to the gun (the index along the receiver: 5.2 and 0.8) | | 0.4 to 1.9 |
| each left phalanx to the gun (index and middle proximal 5.6 / 7.4) | | 0.7 to 7.4 |

The right index lies along the receiver, its lowest glove point at z -52.9 in the gun frame (the lower's bottom
at the trigger is -54): trigger discipline, as drawn. No finger enters the trigger guard. Fitted finger angles
are in hero_pose.json `fingers`; the curl tables (`CURLS`) are now the starting point and a weak prior.

### The clash report (renders/round_02/clashes.md: vertices more than 0.5 mm inside)

| Pair | Round-1 pose | Round 2 |
|---|---:|---:|
| gloves-carbine | 3592 verts, 24.9 mm | 42, **1.0** (handguard in the left glove) |
| body-carbine | 1850, 17.6 | **none** |
| carrier-carbine | 706, 14.1 (charging handle in pouch 1) | 52, **1.7** (PALS against the stock) |
| gloves-carrier / body-carrier | 472 / 160, 15.4 | **none** |
| armour-carbine | 81, 9.6 | **none** |
| shirt-carbine | 94, 22.9 | **none** |
| body-gloves | 2657, 2.1 | 18, **1.5** (gloves over flexed joints) |
| body-armour (guard at the right elbow) | 247, 32.9 | **none** (the armour's round-2 guard and the 91 deg elbow) |
| body-shirt (right elbow) | 84, 18.7 | 25, 8.3 |
| shirt-gloves (a cuff vertex) | 4, 24.5 | **none** |

The target (no hand, carbine or arm penetration beyond 2 mm) is met. Over 2 mm, other owners: the carrier's
flap in the trousers' waistband (12.8, skinning), the feet in the boot soles (designed), the shirt at the right
elbow (8.3).

### Renders looked at

`renders/round_02/hands_rifle_compare.png`, `torso_vest_compare.png`, `arm_R_compare.png`, `arm_L_compare.png`,
`head_face_compare.png`, `soldier_full_compare.png` and `_overlay.png`, `turnaround.png`, and
`renders/pose/pose_hands_sheet.png` (each hand along the camera line, from the gun's right and left, from
above and from the front: `pose_contact.py --render-hands`).
- The silhouette still lies on the drawn figure; the left boot's toe now lands on the drawn one.
- Right hand: on the grip, the index straight along the receiver as drawn, middle to little fingers round the
  grip's front. But it is turned about 30 deg about the grip from the drawn one: the camera sees the thumb side
  and the top of the hand more than the knuckle guard, and the thumb lies along the receiver's left side.
- Left hand: overhand on the handguard, palm on top, fingers down its right side; less closed than drawn (index
  and little finger nearly straight), the thumb along the top toward the muzzle. A small light flap shows at
  the left glove's thumb web (gloves.md).
- Head: turned to his left 13.7 deg; the drawing reads about 20. The carbine shows more of its top than drawn.

### The right elbow

The prior went from 97 to 88 deg (sigma 10); the solve took 91.4 with the hand on the grip and the butt on the
carrier, so it is kept. The forearm guard no longer enters the body. The shirt still does: 25 vertices to
8.3 mm at the back of the elbow (round 1: 18.7). The shirt's owner should add ease at the olecranon (or the
body a corrective); the pose cannot open the elbow further without pulling the hand off the grip.

### Still wrong, for the next round

1. **The stock's front strut** (carbine): it hangs to z -96 only 30-35 mm behind the grip's back strap, where
   the hand's web and the wrist go. So the right hand is turned 30 deg about the grip (the wrist passes to the
   right of the strut) and the drawn knuckles-to-camera hold cannot be reached. A real MFT Minimalist at
   position 3 is a tube housing with one diagonal strut to the toe and leaves that space. Carbine owner: check
   the stock's front against the real part; then re-solve, and the hand can turn back toward the drawing.
2. **Fresh full solves are fragile**: the right hand needs place_hand, and the left can still land 5.5 mm in
   the handguard; the committed pose came by continuation. Next: a placement for the left hand that includes
   the fingers (a rigid palm-only placement did not clear the overhand clamp), or multi-start contact passes.
3. **Head yaw 13.7, not about 20**: MPFB's face under the face term prefers it, and the skull top rose to
   13.9 px. After the head part's new face, rebuild face_targets.json (`pose_solve.py --face-targets`).
4. **The carbine's roll** (24 deg against a 10 deg sigma) and the butt pin 10 px.
5. **The left fingers** are less closed than drawn: the curl priors are weak on purpose. A grasp prior (the
   fingertips under the handguard's 4:30 bevel, as carbine.md's grip point says) would bring them round.
6. **Solve time** about 25 minutes; an analytic Jacobian (the skinning and the field lookups) would cut it.
7. The carrier field rides spine02 rigidly; after a large chest change re-export (`pose.py --solve --export`).
   assemble.py re-solves only when base.json or pose_solve.py is newer than hero_pose.json, not when a part
   cache the contact data reads changes: re-solve by hand after a carbine, carrier, glove or armour rebuild.
8. The stature becomes 1844 mm at the next base rebuild (PLAN.md Decisions, Q13), not applied here; with the
   33 mm footbed it names, HEEL_SEAT/BALL_SEAT (36/24 here) change and the pose needs a full re-solve.

### Files

- `pose_solve.py`: Contact, place_hand, fit_fingers, the face term, the staged solve, `--face-targets`,
  `--continue-from`, `--refit-fingers`, `--no-contact`.
- `pose_contact.py` (new): the Blender side (`--export`, `--render-hands`).
- `pose.py`: `--solve` refreshes contact.npz first, in a subprocess. pose.py does not import pose_contact:
  the parts import pose.py, and assemble.py counts every module they import as an input of every part.
- `face_targets.json` (new, data): 399 landmarks on 831 vertices.
- `hero_pose.json`: the pose, with `stages` (keypoints-only and final contact numbers), `fingers` (angles and
  contact per phalanx) and `residual_terms`.
- Caches: `cache/stages/contact.npz`, `contact_sdf.npz` (274 MB, float32 fields), `pose_x_*.npz` (solver states).

## Round 3 (2026-11-15): the foot in base.py, re-solve by signature, toes in the boot

- **base.py** applies take 1's foot after the rig (`apply_foot()` -> `scripts/stages/foot.py`, see
  `scripts/parts/body.md` §6): MPFB foot targets, the scan transfer (`Foot.Sculpt`), nails, masks, `Foot.Contact`.
  No bone moves (163 bones identical to 0.0 mm); the feet's landmarks change; barefoot stature 1836.5 (1835.0
  before the foot: the scan's heel pad at z -1.5).
- **Re-solve only when the solve's inputs change.** `pose.base_signature()` hashes base.json's bones (to 0.01 mm)
  and its landmarks except the feet's; `pose.py --solve` writes it to `hero_pose_basis.json`; `assemble.py`
  (`pose_needs_solve()`) re-solves when it differs or when pose_solve.py is newer than hero_pose.json, else it
  re-applies hero_pose.json (prints which). Without the basis file it falls back to the old timestamp rule.
- **Toes**: `apply_hero_pose` turns the proximal toe bones up 12 degrees at the MTP joints (`TOE_SPRING_DEG`, the
  boots' last's toe spring); `check()` skips the toes. The solved bones are untouched.
