# Can It Code? (YouTube) — what bears on Sgt. Alex Morgan

Read 2026-11-14 at Jeff's request, from the transcripts and descriptions. Channel: "Can It Code?"
(@CanItCode), an AI-only game-dev channel: the AI does the work, nobody animates or models by hand.

## How I Make Any Custom Human Animation With AI (7XuwPzNAYts, 2026-11-14)

- Same job for every source: the hero runs at the camera and goes into a two-fist attack.
- Rigging: by hand (hours), Mixamo or AccuRig (place a few markers, free), UniRig (open-source AI,
  bones and weights from the mesh, needs cleaning). Their own route goes the other way round: take
  the skeleton the motion tools use (Kimodo's, GEM-X's), lay the body onto it and copy weights over.
- The rest pose (T or A) differs between skeletons; retargeting must remove the rest-pose
  difference first or the arms land elsewhere.
- Root motion for attacks and jumps, in place for locomotion; blending between clips.
- Sources compared: Mixamo (2,000+ real mocap clips, free; their run "looks really good" because
  it is real), CMU (2,500 takes, free to use in games, not to sell the files), Unreal's Game
  Animation Sample (about 900, Unreal only), Rokoko (a few hundred free), Bandai Namco (3,000,
  research only), Cascadeur (AI-assisted, still for animators, paid to export).
- **Claude Opus 5.5 keying the run by script: "moves like a robot"**: even timing, no weight; the
  hip drop, shoulder turn and head bob of a real run are hard to write by hand.
- NVIDIA Kimodo (text to motion, trained on ~700 h of mocap): good walks and runs (they ship its
  run), weak on moves outside its data (the smash "has no hit in it").
- Their road for moves that exist nowhere: a picture of the hero in the start pose → a Kling video
  (one camera, no cuts, every beat written out) → NVIDIA GEM-X (video to 3D motion, 77 body and
  hand points, temporal) → retarget to their skeleton → fixes: pin the lowest foot to the floor
  each frame (GEM-X floated him 10 cm), smooth head and chest jitter.
- Advice: library if the move exists; Kimodo for variations; video + GEM-X only for moves that
  exist nowhere.

## Can Claude Fable 5.2 Beat 3D Generators? (UTffozEcD4U, 2026-11-12)

- Three models (Fable 5.2, Opus 5.5, GPT-6 Astra) building in headless Blender by script, render,
  look, fix (our exact loop), against three image-to-3D generators (Tripo, Meshy, Hunyuan3D via
  the Higgsfield MCP), same picture, same triangle budget, five rounds.
- Code wins on exact, thin, mechanical, articulated things: the fan's wire cage, the bicycle's
  chain and spokes, separate moving parts (blades, wheels), exact triangle counts, clean meshes.
- Generators win on soft and alive things and on surface realism: the car's dirt and seats, and
  "a dog in 3 minutes beats a dog in 100". The coding models' dogs were built as implicit maths
  (SDF) turned into a mesh, unprompted; good bodies, worse faces.
- Generators fuse everything into one block (wheels must be cut out after), melt thin parts, and
  missed triangle budgets.
- Cost: models $20–52 for five rounds; generators $1–2 per model, 3–10 minutes.
- Conclusion: hard and exact → code; soft and organic → generator; one Claude can do both.

Other related videos on the channel (titles only; transcripts not read): "This Is How to Make
Game Textures With AI" (_rMMP7GPgt4: shader-written bricks, Blender nodes, free libraries,
GPT-painted pictures made tileable, trim sheets, decals, parallax), "Stop Asking AI for Whole
Houses - Opus 5.5 + Tripo" (57QEdTgUC3c: a kit of 22 generated parts that snap together), "AI Can
Now Animate Any Monster. Opus 5.5 Built the Tool" (AS92HYsEBqo: video2rig, free on GitHub), "Free
Character Animations From One Sentence | NVIDIA Kimodo" (gv-HCDDV2gQ), "Can NVIDIA Replace Your
Game Animations?" (u-zCpmAkLBs), "I Tested 9 AI Video Models for Game Animation" (V6WqvqOZdiE).

## What I take from it for this project

1. **It confirms the foot's lesson.** Take 1 spent seventeen days modelling a foot by fields and a
   CC0 scan beat it everywhere but between the toes. His result says the same for any soft living
   form: for the head, hands and body, start from measured or generated geometry and transfer it
   onto MPFB's topology (as the foot's scan transfer did) rather than sculpting by code. Code stays
   right for the carbine, buckles, hardware, armour plates, stitches and webbing.
2. **A generator could give us the head likeness fast.** Hunyuan3D (open weights; the 2.x mini
   models may run on the 6 GB RTX 3050 with low-VRAM settings), Tripo or Meshy from
   `ref/crop_head_face.png` would give a first 3D head to transfer onto the MPFB head, then refine
   by the likeness loop. Same for gear we have only one view of (the pauldrons, the pouches) as a
   shape reference. Paid services (Higgsfield, Tripo, Meshy) need Jeff's account and money: his call.
3. **Choose the skeleton for retargeting now.** The game will want motion from Mixamo, Kimodo or
   GEM-X. MPFB's `default` rig maps to Godot's humanoid profile (take 1's spec 08 §3.6); the
   retarget must handle our rest pose (MPFB's A-pose) against the T-pose sources. Nothing to build
   now, but no choice in round 0 should make that harder.
4. **The hero pose is a single frame, not an animation**, so the "robot timing" problem does not
   apply. But a pose estimator could give it to us instead of hand fitting: GEM-X is video-based;
   single-image human mesh recovery (HMR 2.0 / 4DHumans, SMPLer-X, Multi-HMR) would give a 3D pose
   from the reference in one shot, and MediaPipe's pose landmarker gives 2D keypoints and rough 3D
   now. Round 0 starts with MediaPipe plus least squares through the matched camera; an HMR model
   is the upgrade if the fitted pose looks wrong from the side.
5. **Cloth folds** (the trousers' stack on the boots, sleeves) are the next soft thing where
   simulation or a generator should beat code.
