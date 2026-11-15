# Sgt. Alex Morgan, take 2: breadth first

Jeff, 2026-11-14: take 1 went part by part and spent three weeks on a foot. Take 2 builds the
whole soldier at low fidelity first, then raises every part together, one round at a time, going
deeper only where the evaluation says a part is worst.

## Kept from take 1

1. **The reference image**, `ref/reference_full.png`, and its crops in `ref/`.
2. **Reality wins** (`CLAUDE.md`): where the image contradicts itself or the real world, the real
   product or anatomy wins; the image governs identity (face, pose, colours, arrangement, wear).
3. **Keep diving down in detail until it is right.** No part is ever "done" by declaration; it is
   done when it survives the evaluation at the scale it is seen.
4. **The work, evaluate, repeat cycle**: build, render, look (and the blind critics), fix, again.

## Changed

Breadth before depth. Every round touches every part, so the soldier always exists as a whole,
the integration problems (interpenetration, proportions, how parts read together in the hero
frame) show up in round 1 instead of month 3, and effort goes where the whole picture is weakest.

## The stages

**Round 0: the body and the pose.**
1. Base: an MPFB (MakeHuman) male, rest stature 1835 mm barefoot, the drawing's lean V-taper,
   40 years old, with MPFB's `default` skeleton (163 bones, fingers; take 1's spec 08 maps it to
   Godot's humanoid profile) and MPFB's own weights. Skin: MPFB's default skin for now.
2. Pose: the hero pose of the reference (stance, weight and lean as the image shows them;
   both hands on the carbine, head turned slightly to his left), solved so that the posed body, seen
   through the matched hero camera, lies on the reference's joints and silhouette. Posed through
   the skeleton, so the rest-pose model stays the deliverable and the pose is data.
3. Evaluation: the hero frame rendered (Workbench clay and a quick Cycles), the reference beside
   it and overlaid (edges and joint marks), plus the posed body's measurements.

**Round 1 onward: every part, one round each, in parallel (two agents at a time).**
Part owners (each a fresh sub-agent with a brief per round):

| Part | Covers |
|---|---|
| body | skin, anatomy, hands, feet, neck (what shows: face aside, very little) |
| head | head shape, face likeness, ears, eyes, teeth, hair, stubble |
| trousers | combat trousers with knee-pad pockets |
| shirt | combat shirt, sleeves, the neck gaiter |
| boots | the pair of boots |
| gloves | the pair of gloves |
| carrier | plate carrier, pouches, radio and antenna, shoulder straps |
| armour | shoulder pauldrons, forearm guards, elbow and knee caps |
| belt | belt, leg rigs, holster, sidearm |
| carbine | the AR-pattern carbine and its sling |

Round 1 is a blockout: each part as simple geometry at its real dimensions and real position on
the body, with a flat colour from the reference, rigged so the hero pose carries it. Later rounds
raise form, then materials, then detail, but the order is set by the evaluation, not by this table.

Each round: **work** (each part's agent, against its reference crops and real-world evidence),
**evaluate** (the hero frame and the crops, the full-figure overlay, and blind critics on the
parts that changed), **integrate** (all parts in one scene: clashes, gaps, layering order, the
silhouette as a whole), then **choose** the next round's brief per part, worst first.

## Rules for a part

- One build script per part, `scripts/parts/<part>.py`, building `<Part>.*` objects into the
  collection `Part.<Part>` on the **rest** body, then binding to `Morgan.Rig` (garments by weight
  transfer from the body, hard gear parented to a bone), so the hero pose applies to it. It saves
  `cache/parts/<part>.blend`. Re-running replaces only its own objects.
- `scripts/assemble.py` loads the rigged body and every part's cache, applies the hero pose, and
  renders the evaluation set into `renders/round_NN/`.
- Each part keeps a short `parts/<part>.md` (in `scripts/parts/`): what it is (the real-world
  identity and dimensions), what the reference shows, what was done each round, what is still
  wrong. That replaces take 1's long specs. Take 1's specs (`archive/v1/spec/`) are evidence to
  read, not plans to follow.
- Render and look before claiming anything. A round's result is a picture.
- **Start from take 1's work on the part** (Jeff, 2026-11-14, on the foot and boots): before a
  part's round, read what take 1 did for it in `archive/v1/` (its spec's §0 decisions, §2-§3
  evidence and §4 plan, its code, its critic rounds and session-log entries) and reuse what
  worked. Breadth first changes the order of the work, not the value of what was learned.

## Tools carried forward from take 1

`scripts/setup_session.sh` and `scripts/setup/` (Blender 4.5, MPFB, assets, the AI venv);
`scripts/lib/` (env, cache, the materials library, sweep, stitches, webbing, hardware, measure,
optimisers); `scripts/eval/` (the matched hero camera, the scene and lights, the render tiers, the
grade, the blind critic loop in `eval/critic/`); `scripts/tools/` (the Blender server client
`bl.py`, `sheet.py`). Their docstrings cite take 1's specs, now under `archive/v1/spec/`.

## Later (noted, not scheduled)

- Generators and scans for soft, living forms (head likeness, hands, cloth folds): take 1's foot
  showed a real scan beats hand modelling; Can It Code?'s comparison (2026-11-12) found 3D
  generators beat code for soft organic shapes and code wins for exact hard parts. See
  `notes/research_canitcode.md`.
- Animation for the game: retarget library or generated motion (Mixamo, Kimodo, GEM-X from a
  generated video) onto `Morgan.Rig`; this is why the skeleton is chosen in round 0 with retargeting
  in mind.

## Decisions (Jeff delegated 1-3 to judgement, 2026-11-14; 4 is his)

1. **Plate height: as drawn**, the plate top about 60 mm below the sternal notch. A plate riding a
   little low is common in real wear, so the image is plausible and governs the arrangement.
2. **The P9 holster stays hidden at the right rear hip.** The image shows no pistol and the right
   leg rig carries magazine carriers; a hip holster is a real, common carry.
3. **Boot questions (take 1's spec 02 §10.3):** Q13 the rest stature becomes **1844 mm**, so the
   posed skull top still meets the drawn line on the real 33 mm footbed (Jeff's rule: height
   follows the drawing; round 0 also found the head projecting low). Apply it at the next base
   rebuild, then re-solve the pose. Q14 smooth full-grain leather (the drawing's highlights);
   Q15 Cordura shaft panels (the real Zephyr Hi); Q16 the buckle at φ 150°, posterior-lateral,
   where real cuff straps put it; Q17 no Sketchfab downloads, the build goes without reference
   boot scans; Q18 the boot stays rigid on the foot bones; Q19 no anchor photographs. Earlier
   defaults stand: our own chevron-and-block lugs (Q3), a plain toe-bumper oval (Q6), dust as
   pictured with the left boot dustier (Q7), hidden parts kept low-poly (Q9), mesh laces (Q12).
4. **Nothing paid** (Jeff). No Tripo, Meshy, Higgsfield or paid image models, and no paid tiers.
   Free, local, open tools only: open-weight models that run on the RTX 3050 (e.g. a Hunyuan3D 2
   mini variant, if it fits in 6 GB), CC0 or CC-BY data already reachable, and our own code.
