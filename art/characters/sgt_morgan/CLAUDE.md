# Sgt. Alex Morgan — project conventions

Goal: a photoreal, rigged Blender model of the soldier in `ref/reference_full.png`,
built entirely by scripts, generators, simulation and downloaded assets, verified by
rendering and looking. Read `spec/00_overview.md` first, then the spec for the part
you are working on.

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
6. **Large binaries are not committed.** `assets/` and `renders/` are gitignored except
   for `assets/manifest.json` and the latest `renders/eval/*.png`. The setup script
   re-downloads assets from the manifest.
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
