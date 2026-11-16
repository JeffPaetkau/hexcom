# Godot export, first look (2026-11-15)

`scripts/export_godot.py` turns the assembled soldier into `game/characters/morgan/morgan.glb`
(gitignored) with a mocap walk and idle, for a first look at him moving in the game's environment
(`game/scenes/Morgan.tscn`; how to run it: `game/characters/morgan/README.md`). It is a quick,
honest look, not CLAUDE.md's export deliverable: that still wants proper texture sets, normal maps,
the Godot humanoid bone map and LODs.

## How to run

```bash
source cache/env.sh
"$SGT_BLENDER" -b --python scripts/export_godot.py -- --stage all --src cache/assembled_snapshot_godot_r9.blend
```

Then, from `game/`: delete the old extracted textures (`characters/morgan/morgan_Morgan*.png` and their `.import`
files, gitignored) so nothing stale survives, `dotnet build Hexcom.Game.csproj`, `"$GODOT" --headless --path .
--import` (it reports "Unrecognized UID" once for each deleted texture; harmless), then capture (README). The
import re-creates `.uid` files beside some committed scripts and shaders; they are not committed, so delete them.

`--src` defaults to `cache/assembled.blend`; give a copy when other agents are rebuilding (the first
look was made from `cache/assembled_snapshot_godot.blend`, the 14:14 build of 2026-11-15). Keep the
copy inside `cache/` or let the script re-resolve its relative image paths (it does, against `cache/`;
a copy elsewhere baked the MPFB skin magenta before that fix). `--stage mesh` (about 18 to 22 minutes on the
RTX 3050, almost all of it Cycles bakes) writes `cache/godot/morgan_mesh.blend` and
`mesh_report.json`; `--stage anim` (about a minute) retargets, exports the .glb and writes
`morgan_motion.json` beside it. It only reads the assembled .blend; it never runs assemble.py.

## Mesh and materials: what is simplified

- **Rest pose** (MPFB's A-pose), all parts, the rig (163 bones, all exported), the carbine.
- **Dropped:** the bare feet's nails and the socks (inside the boots), the eyebrow and eyelash
  cards (alpha cards; no alpha here), the boots' stitches and tacks (they exist only through a
  geometry-nodes modifier), the scene's camera, lights and floor.
- **Modifiers:** Subdivision, Solidify, Bevel, Weighted Normal and Geometry Nodes removed; Mask
  applied; the Armature modifier kept. So garments are single-sided shells (the materials are
  double-sided) and hard edges are unbevelled.
- **Carbine:** its objects (children of Carbine.Root, bone-parented to wrist.R) are skinned 100 % to
  wrist.R. In the rest pose and in the walk it stays where the hero pose's right-hand grip puts it,
  so he carries it by the pistol grip, muzzle down, swinging with the arm.
- **Decimation** (collapse) to a budget per part, one ratio per part, but no object of 300 or more triangles
  below `FLOOR_TRIS` (150; since round 9: one ratio took the 492-triangle kneepad straps to 23 triangles, and
  the crushed band fell inside the roomier round-9 trousers, a jagged ledge behind each knee; the elbow-pad
  and forearm-guard straps went the same way). Round 9: 111,582 triangles in all (body 16.0k, hair 3.0k,
  trousers 12.0k from 64.6k, shirt 9.0k, boots 11.6k from 329k, gloves 8.6k, carrier 14.5k, armour 14.3k
  from 207k, belt 9.8k, carbine 12.9k); the floor costs about 6k over the budgets. The boots and armour
  lose the most and it shows close up.
- **Materials:** each part gets one new UV map (Smart UV Project over all its objects together)
  and its own node trees baked through it with Cycles: every BSDF (also inside node groups) is
  swapped for an Emission of its Base Color, Roughness or Metallic input and baked as EMIT, so the
  camouflage print, the attribute masks, image textures and mix shaders come through. Base colour
  2048 px for the body and trousers, 512 for the hair, 1024 for the rest; roughness and metallic
  packed into one glTF metallicRoughness image. One Principled material per part, double-sided.
  Not carried: normal and bump detail, subsurface, the eyes' gloss and refraction, alpha, sheen,
  the stubble's shading beyond its colour.
- **Joined** into one skinned mesh per part, `Morgan.<Part>`: ten meshes, ten materials.

## Motion

- **Source:** the CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu; free for any use,
  games included), Bruce Hahne's MotionBuilder-friendly BVH conversion (frame 1 of each file is an
  added T-pose), mirrored at github.com/meshula/cmu-mocap; the script downloads the two clips into
  `assets/mocap/cmu/`. Walk: **35_01** ("walk"), one gait cycle (120 fps frames 131 to 266, 1.13 s,
  34 frames at 30 fps). Idle: **77_02** ("standing"), the quietest 6 s window (frames 134 to 854).
- **Retarget** by a bone map (MAP in the script): for each mapped bone the source joint's world
  rotation change from its T-pose is applied on top of the target's rest. The limbs' rests are first
  swung onto the T-pose's bone directions (this removes the A-pose against T-pose difference); the
  trunk, neck and head are not, because the two skeletons put those joints at different places (CMU's
  Neck sits on Spine1, a zero-length segment; aligning them bent him over at the waist). Hips
  translation scaled by leg length (0.060 m per BVH unit). Twist bones, toes and the face follow
  their parents; the fingers hold the hero pose's grip all the time.
- **Feet** (round 2, Jeff: "his foot angles while walking are really messed up"). The foot copied
  the CMU foot's rotation, and the CMU ankle-to-ball segment's roll and yaw do not carry over to
  MPFB's foot: the left boot toed in about 25 degrees (its toe 10 cm inside its heel), the swinging
  boots rolled onto their edges (seen from behind, the sole faced sideways) and the stance foot sat
  heel-down, so the feet scissored across the midline. Now `fix_feet` re-aims each foot from its
  boot's sole: the ankle and the sole's heel-to-toe tilt stay from the mocap (clamped to -65..+30
  degrees), the roll is zero, the heading is the pelvis's turned out 6 degrees, and a stance foot's
  small tilt is eased flat. Result: toes forward, soles flat at contact, the feet on two tracks about
  12 cm apart. The idle gets the same treatment.
- **In place**, looped: the hips' drift over the cycle removed (their sway kept), the end-to-start
  mismatch spread over the cycle. Feet on the ground: pinned each frame to the sole point (boot heel
  or toe) that is still, and a sole point that is still moving fast but touches the ground is lifted
  1.2 cm clear with two-bone leg IK (7 foot-frames). The speed at which a planted foot stays still is
  measured, **1.28 m/s** at his own height (1.21 m/s once the game scales him), and written to
  `morgan_motion.json` for the game to move him at. Remaining slide of a planted heel or toe:
  **worst 4.8 cm, mean 3.3 cm** per contact (before any clean-up it was 30 cm: the swing foot came
  down four frames early and skated).
- **Intro poses:** `Rest` (the rest pose, every bone at rest, soles lifted onto the ground) and `Hero`
  (the hero pose read from the Morgan.Rig of the assembled .blend the mesh was built from, which
  assemble.py posed with pose.py's `apply_hero_pose` and on which it placed the carbine, so the grip
  matches that build even after hero_pose.json moves on, as it did at 15:48 for round 7; without that
  .blend it calls `apply_hero_pose` itself; grounded on the lowest sole point), each a static
  two-frame action. The carbine stays skinned to wrist.R, so it is
  in both hands in Hero, exactly as assembled, and in the right hand in Rest and the walk.
- Every action keys the same bones (the map, the fingers and every bone the hero pose moves), so
  Godot's crossfades never leave a bone holding another action's pose.
- **Scale:** he stands 1.904 m in boots (1.844 m body, hair, a 35 mm sole); the showcase scales him
  to the rules' standing man, 1.80 m (0.945).

## What is wrong (round 2, 2026-11-15)

Captures in `renders/godot/` (gitignored): `front`, `side`, `tactical`, `feet_side_a/b`,
`feet_front_a/b`, `hero_three`, `hero_close` (.png), `intro_strip.png`, and `morgan_intro.mp4` (rest,
hero pose, step off; a fixed three-quarter camera), `morgan_intro_gamecamera.mp4` (the same with the
game camera as an ordinary run opens it), `morgan_feet_side.mp4`, `morgan_follow.mp4` (intro and one
loop).

- In the rest pose the carbine sticks out sideways from the A-posed right hand (it is skinned to the
  wrist); it swings into both hands as he moves into the hero pose, and back into the right hand,
  muzzle down, as he steps off. The walk carries it by the pistol grip; the left hand keeps the hero
  pose's handguard grip around nothing. A low-ready or slung walk would need the arms keyed.
- The move from rest to hero pose is a straight crossfade of bone rotations (1.5 s): no weight shift.
- The idle (77_02) stands with the head bowed, looking at the ground.
- Skin shows through the shirt at the left shoulder and collar, where decimation pulled the shell
  inside the body. The boots (329k to 10.6k triangles) and armour (196k to 10.5k) are faceted close up.
- No normal maps: cloth and armour read flat; the garments catch a cool sky sheen in the shade.
- The turns are 1.4 m arcs walked with the straight cycle; his feet slide a little through them.
  Walk to idle is a 0.35 s crossfade with no stopping step, so he glides to a halt.
- The skeleton is exported as MPFB's 163 bones with their own names; no Godot humanoid bone map yet.
- Round 8's .glb was `cache/assembled_snapshot_godot_r8.blend` (commit 8a905e9: head round 4, round 7's pose, round 8's materials), 103,828 triangles; the earlier captures (no suffix) are the 14:14 build, the `_r8` ones that one.

## Round 9 (2026-11-15, evening)

The current .glb is round 9: `cache/assembled_snapshot_godot_r9.blend`, a copy of the 18:48 `cache/assembled.blend`
(commits ae0ea44 to 04d9736: the hard kit, the cloth-simulated trousers and upper sleeves, the carrier's bulk),
111,582 triangles, 28.4 MB. The trousers and shirt need nothing new from the exporter: the cloth solve is baked
into their meshes at rest and they are bound by weights (Armature, Solidify, Subdivision, as before). Walk:
planted-foot speed 1.282 m/s, slide worst 4.9 cm, mean 3.9 cm (round 8: 4.8 and 3.3; round 9's boots, from which the soles' contact points are read, changed).
The export's 12 glTF warnings are round 8's (two meshes "not valid", more than four joint influences, extra image
nodes).

Captures in `renders/godot/`, all `_r9.png`: `rest_front`, `rest_three` (rest pose), `hero_three`, `hero_close`
(hero pose), `front`, `walk_side_a`, `walk_side_b`, `feet_side_a`..`e`, `feet_front`, `feet_front_b` (walk),
`feet_rest`, `feet_hero`, `behind`. `--at` is not frame-exact (two runs at `--at 9.2` landed about 0.15 s apart in
the cycle), so name a walk capture by what it shows, not by its time.

What was checked beyond the pictures (Workbench renders of `cache/godot/morgan_anim.blend` with each part a flat
colour, the body red, from four sides at walk frames 4, 12 and 28):
- **The knees do not come through the trousers**: no skin anywhere on the legs in any walk frame, front, side or
  back, including the swing leg at full flexion (`feet_side_d`). The cloth folds at the back of the bent knee
  by skinning alone and looks acceptable at game distance. A nearest-surface count reports body vertices
  "outside" the trousers at the crotch and seat (up to 5 cm), but the renders show none: the test is fooled
  where the gusset bridges the legs.
- **Fixed in the exporter: the kneepad straps.** With one decimation ratio for the armour (0.048) each
  492-triangle kneepad strap became 23 triangles, a crumpled band that dropped inside the roomier round-9
  trousers and showed as a jagged ledge behind each knee, at rest too. The floor (above) keeps them at 150;
  they now wrap the leg cleanly, standing and walking. The elbow-pad and forearm-guard straps had the same
  treatment and are fixed the same way.

What is wrong, and whose it is:
- **The blousing (trousers.py).** Over the boot collars the stacked hem reads in the game as a ragged crown of
  thin, spiky flaps rather than a soft roll, worst from the side (`feet_side_b`, `feet_side_e`). The flaps are in
  the part's own cloth-solve mesh (`Trousers.Shell` at rest, without modifiers, has them); in Blender the
  Solidify and Subdivision modifiers round them off, and the export, which drops both, shows them as they are.
  Not an exporter fault; trousers.md section 9 already plans to free the cuff ring after the push.
- **Skin at both shoulder tops** (the shirt and body near the collar; `hero_close`, red in the Workbench front
  view at rest and in the walk): as in round 8, now on both sides; decimation of `Shirt.Shell` (20.8k to 5.7k)
  against the body's 16k. Exporter territory (a later fix: shrink the body under the shirt, or delete the covered
  body faces before decimation).
- The belt's thigh-rig straps (5184 triangles each, ratio 0.18) come out lumpy in the Workbench views; at game
  distance they read as webbing. The boots (329k to 11.6k) are still faceted close up.
- Everything else in the round-2 list above still stands (carbine in the rest pose, the crossfade into the hero
  pose, the idle's bowed head, no normal maps, the turns).
