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

## Second pass (2026-11-14 evening): three more transcripts

### Crazy AI Animation Workflow - Opus 5.5 (evK-Y83Qlco)

- One roe deer, three tries. (1) Opus builds it in Blender from code (tubes, capsules, blended
  ellipsoids, 4 render-compare rounds, ~40 min), rigs 29 bones and keys a walk: silhouette close,
  face poor, motion blocky, bad weights. (2) A Tripo model from the same picture in a minute:
  "a huge difference" in face, fur and proportions; the coded walk still artificial. (3) Render
  the Tripo model exactly from the side on grey (a known camera), Seedance makes a 4 s video of
  that deer running (strict prompt: side view, camera follows, no cuts, four legs), then a script
  poses the skeleton frame by frame by analysis by synthesis: render, compare outline and legs
  with the video, nudge the bones, repeat (97 frames, ~30 min a clip). That one worked.
- Per-animal fixes: a 60 fps file with 24 fps motion; crossing thin legs lost track, so the AI
  marked the legs by hand-like annotation on the tricky frames; painted-on wings rebuilt as real
  geometry.
- **The failure that matters to us: a person lifting a stone.** From the camera the outline
  matched to the pixel, but in 3D the chest sank into the legs and the stone sat inside the body.
  One view cannot see depth; where arms reach toward the camera and hands hold an object, the
  guess goes wrong by centimetres and the object passes through the body. Filming from the side
  just moves the problem. Their fix: two (or more) synchronized views, as real mocap does.

### Is This Really AI? Insane Opus 5.5 GameDev Workflow (XqtnBlPJ6KE)

- Roles: Opus builds, GPT-6 Astra paints pictures (concepts, textures, decals, VFX sprites), Tripo
  makes small detailed props, the human directs and tests.
- Blockout first, then GPT paints the look **over the blockout render**: three looks, pick one.
- The same wall piece three ways: Tripo (fastest, looks great far away, wrong scale, an air
  conditioner a metre off the wall, everything baked into one texture, little control); Blender by
  code (perfect shapes, coded dirt "way too clean"); **Blender shapes + GPT-painted textures and
  dirt (the winner)**. Rule: structure in Blender, textures from GPT, Tripo for small details only.
- The Blender script measures GPT's drawing so parts land where it painted them. Textures: a one-
  metre patch painted by GPT, made seamless by a half-offset blend, height and roughness derived
  from it; dirt = whatever in GPT's drawing is darker than the clean wall, projected on.
- Tripo CLI for batches (18 props in ~10 min, six at a time, resumable); inputs are GPT pictures of
  each object from front, side and back. Faults: face budgets exceeded, models facing backwards
  (Opus checks each from four sides and fixes it).
- Quality tests that break the build on purpose (11 ways) to prove the checks catch it; a bot that
  walks every stair to prove reachability.
- Lighting iterated round by round against a GPT paint-over of a screenshot.
- Explosions: GPT sprites only grow and fade; a Seedance video cut into 64 frames moves for real.

### This Is How to Make Game Textures With AI (_rMMP7GPgt4)

- A texture is a set (colour, normal, roughness, height); UVs map it; walls in metric UVs;
  triplanar where UVs are bad.
- Four sources on one wall: a shader written from one prompt (never repeats, too clean), Blender
  nodes baked (the most computer-made look), Poly Haven (good, but everyone has it), **GPT-painted
  pictures made tileable by their tool** (his favourite): even out the lighting, snap joints to a
  grid, cut brick rows in the gaps so copies meet, overlap-and-cut for patternless plaster, derive
  height, normal and roughness from the joints.
- Hiding repeats: a big soft noise, a second scale, hex tiling (breaks joints on bricks).
- Wear where it really happens: a script finds edges (corners, window reveals) into a mask and the
  shader breaks the plaster there; trim sheets for long thin parts; decals placed by a script that
  knows where dirt goes (under sills and pipes, along the bottom). Interior mapping, parallax
  occlusion (and Crimson Desert's silhouette cut).

### What the second pass adds for this project

1. **Our pose is the stone-lifting case.** One drawn view, two hands on an object held toward the
   camera: round 1's clash report has the hands and stock 15-25 mm inside the carbine and the
   right forearm guard 33 mm inside the body. Priors helped, but the depth is a guess. The
   remedies, cheapest first: (a) hard contact constraints in the solve (palms on the grip surfaces,
   the stock on the carrier, no penetration), which round 2's hands-and-grip pass should add;
   (b) a silhouette term (render and compare outlines, as their deer fit did) on top of keypoints;
   (c) a second view: an image or video model asked to show the same soldier from the side or
   three-quarter (Seedance/Kling orbit, or a GPT image) would give depth to fit against, as their
   troll was filmed from two sides. (c) costs Jeff's accounts; it is not needed yet.
2. **Structure by code, surfaces from paintings.** For the soldier the equivalent is: our real-
   dimension geometry (rounds 1-2) plus painted surface detail: the camouflage print, fabric
   wear, mud, scuffs and the emblem as generated, tileable pictures and decals placed where wear
   really happens (edge masks from geometry, as take 1's materials library already does for
   leather). An image model is the missing tool here; Jeff has ChatGPT, so pictures could be made
   there and dropped into `assets/` when we reach the materials round.
3. **Generators for single organic props and the head.** Tripo-style image-to-3D from front, side
   and back pictures beats code for organic things (the deer's face), but gets scale and placement
   wrong and bakes everything into one texture. So: use it for shape (the head, perhaps the
   pauldrons or pouches as references), always re-measured, re-scaled and transferred onto our
   own topology and materials, never dropped in raw.
4. **A paint-over as the target.** For lighting and look, they iterate against a GPT paint-over of
   their own render. We have the reference already, but a paint-over of *our* render (same pose,
   our proportions) would be a fairer target where reality-wins makes us differ from the drawing.
5. **Tests that prove the checks work** (break it on purpose): worth doing for assemble.py's clash
   report and the critic tally, so a quiet check is not mistaken for a pass.
