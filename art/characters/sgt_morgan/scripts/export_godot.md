# Godot export, first look (2026-11-15)

`scripts/export_godot.py` turns the assembled soldier into `game/characters/morgan/morgan.glb`
(gitignored) with a mocap walk and idle, for a first look at him moving in the game's environment
(`game/scenes/Morgan.tscn`; how to run it: `game/characters/morgan/README.md`). It is a quick,
honest look, not CLAUDE.md's export deliverable: that still wants proper texture sets, normal maps,
the Godot humanoid bone map and LODs.

## How to run

```bash
source cache/env.sh
"$SGT_BLENDER" -b --python scripts/export_godot.py -- --stage all --src cache/assembled_snapshot_godot.blend
```

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
- **Decimation** (collapse) to a budget per part: 103,805 triangles in all (body 16.0k, hair 3.0k,
  trousers 12.0k, shirt 9.0k, boots 10.6k from 329k, gloves 6.0k, carrier 14.3k, armour 10.5k from
  196k, belt 9.6k, carbine 12.8k). The boots and armour lose the most and it shows close up.
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
- **In place**, looped: the hips' drift over the cycle removed (their sway kept), the end-to-start
  mismatch spread over the cycle. Feet: the ground is pinned each frame to the sole point (boot heel
  or toe) that is still, and a sole point that is still moving fast but touches the ground is lifted
  1.2 cm clear with two-bone leg IK (7 foot-frames). The speed at which a planted foot stays still is
  measured, **1.31 m/s** at his own height (1.24 m/s once the game scales him), and written to
  `morgan_motion.json` for the game to move him at. Remaining slide of a planted heel or toe:
  **worst 4.8 cm, mean 2.5 cm** per contact. Before the foot clean-up it was 30 cm (the swing foot
  came down four frames early and skated).
- **Scale:** he stands 1.904 m in boots (1.844 m body, hair, a 35 mm sole); the showcase scales him
  to the rules' standing man, 1.80 m (0.945).

## What is wrong (first look, 2026-11-15)

Captures in `renders/godot/` (gitignored): `front`, `side`, `close`, `tactical`, `follow_turn`,
`idle_front` (.png), `walk_cycle_strip.png`, `walk_to_idle_strip.png`, and `morgan_follow.mp4` (one
41 s loop), `morgan_side.mp4`, `morgan_stop.mp4`.

- The carbine is carried by the pistol grip in the right hand, muzzle down, swinging with the arm;
  the left hand holds the hero pose's handguard grip around nothing. Plausible for a first look, not a
  carry anyone would choose; a proper fix is a low-ready or slung walk (the arms keyed, not mocap).
- The idle (77_02) stands with the head bowed, looking at the ground, feet a little wide.
- Skin shows through the shirt at the left shoulder and collar, where decimation pulled the shell
  inside the body. The boots (329k to 10.6k triangles) and armour (196k to 10.5k) are faceted close up.
- No normal maps: cloth and armour read flat; the garments catch a cool sky sheen in the shade.
- The turns are 1.4 m arcs walked with the straight cycle; his feet slide a little through them.
  Walk to idle is a 0.35 s crossfade with no stopping step, so he glides to a halt.
- The skeleton is exported as MPFB's 163 bones with their own names; no Godot humanoid bone map yet.
