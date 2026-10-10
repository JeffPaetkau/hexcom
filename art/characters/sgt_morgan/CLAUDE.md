# Sgt. Alex Morgan — project conventions

Goal: a photoreal, rigged Blender model of the soldier in `ref/reference_full.png`,
built entirely by scripts, generators, simulation and downloaded assets, verified by
rendering and looking. Read `spec/00_overview.md` first, then the spec for the part
you are working on.

## Scope (Jeff, 2026-10-10)

The deliverable now is the **unit model**: the soldier, his clothing, armour, gear and
carbine, rigged. Lighting, floor, background and lens effects matter only as far as they
change how the model renders, so the evaluation scene is a matched camera, the key, cool
side and world lights, a plain floor plane for contact shadows and bounce, and the colour
grade. The hangar set, floor joints, the floor-pool light, depth of field, haze and glare
are deferred. Once Jeff accepts the model, the scene is built in Blender and in several
game engines to compare results, so the model must export cleanly (glTF 2.0 with baked
textures, a skeleton that maps to Godot's humanoid profile) as well as render in Blender.

## Non-negotiable rules

1. **Left/right are the soldier's own.** "Left hand" is his left hand. Never use
   viewer-relative terms without saying "viewer's left".
2. **Units are metres in Blender, millimetres in specs.** Character origin is on the
   floor midway between the feet, +Z up, the character faces −Y (the camera sits on
   the −Y side), so +X is the SOLDIER'S LEFT (viewer's right). This matches
   `notes/analysis_consolidated.md`.
3. **Render and look before you claim anything.** Every part script ends by rendering
   the part in closeup from the views named in its spec into `renders/<part>/`, and
   you open the PNG with the Read tool and compare it with the reference crop before
   marking the step done. "It ran without errors" is not done.
4. **Scripts are idempotent and resumable.** Each `scripts/parts/<part>.py` can be run
   headlessly (`blender -b --python scripts/parts/<part>.py -- <args>`) on a fresh
   container after `scripts/setup_session.sh`, and re-running it replaces its own
   objects without touching other parts' objects. Objects, materials, collections and
   images are named `<Part>.<Component>` (e.g. `Boot.L.Sole.Lugs`).
5. **Nothing is hand-edited in a .blend.** The .blend is a build artifact. Fix the
   script, rebuild.
6. **Downloads and intermediates are not committed; deliverables are.** `assets/`,
   `renders/` and `cache/` are gitignored except for `assets/manifest.json` and the latest
   `renders/eval/*.png`; the setup script re-downloads assets from the manifest. The
   deliverables (`deliver/`: the .blend, the .glb and the baked textures) live in the
   repository and are committed at milestones only, never per iteration, because every
   committed version stays in the history. GitHub refuses files over 100 MB, so textures
   stay separate files rather than packed into the .blend; if `deliver/` grows past a few
   hundred MB, propose Git LFS to Jeff.
7. **Commit at every milestone.** The container is ephemeral; uncommitted work is lost.
8. **Specs are the source of truth.** If you deviate from a spec, update the spec in
   the same commit and explain why in the commit message.

## Layout

- `ref/` reference image and upscaled crops (read-only)
- `spec/` one Markdown spec per part, numbered in build order; `00_overview.md` holds
  strategy, breakdown tree, evaluation method, roadmap
- `notes/` analysis and research notes behind the specs
- `scripts/setup_session.sh` installs Blender, MPFB, and downloads assets
- `scripts/lib/` shared Python helpers (materials, bevel/subdiv utilities, render
  harness, measurement tools)
- `scripts/parts/` one build script per part
- `scripts/build_all.py` assembles the character from parts and poses it
- `scripts/eval/` reference-matched camera, lights, critic render sets, metrics
- `assets/` downloaded textures, HDRIs, MakeHuman data, AI models (gitignored)
- `renders/` outputs (gitignored except `renders/eval/`)

## Tooling facts

- Blender 4.5.14 LTS at `/usr/local/bin/blender`, headless only; bundled Python 3.11
  (numpy, no PIL). System `python3` is 3.13 with PIL and numpy; run it with `-I`.
- 4 CPU cores, 15 GB RAM, no GPU. Cycles CPU: budget minutes per evaluation render.
- Network: download.blender.org, ambientcg.com, polyhaven.com, MakeHuman asset
  servers, extensions.blender.org, PyPI, Hugging Face are reachable.
- Jeff's workstation (Windows 11, Git Bash): Blender 4.5.14 LTS at `C:\Program Files\Blender
  Foundation\Blender 4.5\blender.exe`, 8 threads, NVIDIA RTX 3050 6 GB (Cycles on OptiX, OIDN
  on the GPU). After `bash scripts/setup_session.sh`, `source cache/env.sh` gives `$SGT_BLENDER`,
  `BLENDER_USER_RESOURCES` (the project's own MPFB) and `$SGT_PYIMG` (the AI venv, the Python
  with PIL; `python3` there is a Store stub). Python code uses `scripts/lib/env.py`; the fast
  loop is `scripts/tools/bl.py` (spec 18 §4.13), renders `scripts/eval/render.py` (spec 17 §4.14).

## Where work runs

- **Cloud sessions (Linux, 4 CPU cores, no GPU):** analysis, research, specs, shared
  tooling and the materials library, hard-surface parts, metric and optimiser code,
  low-resolution checks. Form checks use the Workbench engine (matcap + cavity), which
  renders headless here in about 5 s including start-up; EEVEE takes 40 s on software
  GL and is not worth it here. Cycles is for acceptance renders only.
- **Local session on Jeff's Windows machine (GPU):** the face likeness loop, hair
  grooming, cloth simulation, beauty renders and critic rounds. Cycles previews there
  take under a second and EEVEE runs live.
- The repository is the hand-off between the two. `scripts/setup_session.sh` must work
  on both Linux and Windows (Git Bash); keep paths relative to the project directory.
- Tighten the loop before iterating on form: keep one Blender process alive, cache each
  part in its own .blend, render contact sheets of many variants per look, and measure
  (landmarks, girths, silhouettes) before rendering at all.

## Session protocol

Start: `bash scripts/setup_session.sh`, read `notes/session_log.md`, pick the next item.
End: commit, push, append what was done and what is next to `notes/session_log.md`.

## Source of truth: reality wins

The reference image was generated by ChatGPT and contradicts itself and the real world in
places (three muzzle tubes, a rail 10 cm above the bore, a light straddling the receiver
joint, no body shadow, thighs 28 percent short). Jeff's rule, 2026-10-07: **where the image
is inconsistent with itself or with reality, reality wins.** Precedence:

1. **Real-world identity and its published dimensions.** For every part, name the closest
   real product or anatomical standard (AR-15/M4-pattern carbine with a 16 in government
   barrel and a 13 in handguard; STANAG magazine; Lowa Zephyr class boot; Crye G3 class
   trousers and AirFlex class kneepads; Mechanix M-Pact class gloves; JPC class carrier with
   a MIL-spec PALS grid; ANSUR II anthropometry for the segment proportions and the feet)
   and build to it.
2. **The image, where it is internally consistent and physically plausible**, for everything
   that carries identity: the face, hair and stubble, pose, colours, gear arrangement,
   emblem, wear and dirt.
3. **The consolidated analysis's dispute resolutions**, re-decided against rule 1 where they
   chose "as drawn" (notably the hip-joint height: use ANSUR segment lengths, not the drawn
   0.41 crotch height; the full-figure overlay will therefore deviate in the legs, and that
   is accepted).

Specs written before this rule (01 to 05, 09) are revised against it in the critique pass.

**The man's height and build follow the drawing** (Jeff, 2026-10-10, spec 01 §10.2 Q7 to
Q9). Rest stature **1835 mm** barefoot: in the hero pose, in boots, the skull top meets the
drawn line 1855 mm above the floor (the footbeds add 42, the pose costs 22). The build is the
drawing's lean V-taper, not ANSUR's 83 kg man; the mass is an outcome. The feet keep their
ANSUR size (282 mm). Specs still citing 1855, 1877 or 83 kg are corrected when their part is
built.

## Paths

Specs, notes and research scripts written in cloud sessions refer to `/home/user/sgt_morgan/...`;
read that as this folder (`art/characters/sgt_morgan/` in the hexcom repository). Paths under
`assets/ai/` in the notes have copies of the small results in `ref/ai/` (the face landmarks
and meshes extracted from the reference). New scripts take paths relative to this folder and
must run on both Linux and Windows.
