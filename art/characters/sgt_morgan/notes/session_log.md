# Session log

Newest first. One entry per working session, a few lines each: what was done, what is
next, anything a fresh session must know.

## 2026-10-10 — hand-off: the vertical slice moves to Jeff's GPU workstation

**State.** All eighteen specs are written and pushed. The consistency ledger
(`notes/interface_ledger.md`: shared values and their owners, per-spec change lists, Jeff's
open questions) is being finished by the cloud session and will be pushed when done; pull
before starting the slice. Specs are revised just in time: each part's spec gets its ledger
changes applied when that part is built, because the slice will teach lessons that change the
later specs anyway.

**Workstation prerequisites.** Blender 4.5 LTS (4.5.14 matches the cloud), Git for Windows
(Git Bash), Python 3 with Pillow and numpy, Godot 4.7.2 for the import check. Git LFS is not
needed until the first texture bake (0.35 to 0.6 GB per bake, spec 18).

**First steps.**
1. Make `scripts/setup_session.sh` work in Git Bash on Windows as spec 18 section 4 describes:
   find or install Blender, install the MPFB2 extension and the MakeHuman packs
   (`notes/research_generators.md` section 6; on Windows the user extension folder is under
   `%APPDATA%/Blender Foundation/Blender/4.5/`), restore the textures and HDRIs from
   `assets/manifest.json` with `scripts/research/build_manifest.py --restore`.
2. Turn on the GPU for Cycles in a startup helper (OptiX for NVIDIA RTX, CUDA otherwise, HIP for
   AMD) and time `scripts/research/test_01_cycles_bench.py` against the cloud's numbers in
   `notes/research_blender_capabilities.md`.
3. Build the shared tooling from spec 18: `scripts/lib/`, the persistent Blender server, the
   measurement tools, the render harness with spec 17's camera presets, contact sheets.

**The vertical slice.** Foot, then sock, then boot, as Jeff first described: apply the ledger's
changes to specs 01 and 02 (and the shared values they take from 03, 08, 16 and 17), build
`scripts/parts/01_foot_ankle_sock.py` and `02_boots.py`, render against
`ref/crop_boots_feet.png`, run the critic rounds of spec 18, export the boots to glTF and check
the import in Godot. Record measured effort per step so the 35 to 90 window estimate can be
replaced by a real one.

**Commits.** Jeff asked for this work to live in the repository; commit and push at
milestones. Everything outside `art/` follows the game's own rule in `summary.md`.

**Starter prompt for the local session:** "Read art/characters/sgt_morgan/CLAUDE.md and the
newest entry of art/characters/sgt_morgan/notes/session_log.md, then begin the first steps
listed there. Work in art/characters/sgt_morgan."

## 2026-10-10 — cloud session (Opus)

Specs 06, 07, 08, 10, 11, 12, 13, 14 and 17 written under the reality-wins rule and pushed.
In progress: 15 carbine and 16 materials library (separate agents, two at a time); 18
pipeline queued. Spec 17 settles colour management (AgX, grade applied in numpy after the
view transform), a single neutral look-dev scene, and a JSON registry of named camera
presets. Open for Jeff from spec 17: physical or floor-only light pool, physical or soft
bokeh, floor joint layout, and where large deliverables (.blend, .glb, textures) live.
Jeff's scope decision: the unit model first; the scene only as far as it affects the
model's render; the scene is built later in Blender and several game engines; deliverables
live in the repo under deliver/, committed at milestones (CLAUDE.md, Scope and rule 6).
Spec 17 carries a scope note; spec 18 was briefed with it.
Spec 15 (carbine) builds one real configuration (BCM M4 upper and lower, 16 in government
barrel, mid-length gas, MCMR-13 handguard, MFT Minimalist stock, A2 birdcage, SureFire M300C,
Aimpoint T-2, PMAG GEN M3). It moved the grip frame and changed the handguard section, so
specs 05, 08 and 11 must be revised against it in the critique pass.
Jeff confirmed fictional "AR-12" markings on the carbine (spec 15, Q7).
Spec 16 (materials library) done: 85 materials and 48 cross-spec conflicts resolved; it
supersedes the material values in every part spec's section 5. Next: an interface ledger
(notes/interface_ledger.md) listing shared values, owners, per-spec changes and Jeff's open
questions, then revisions of the specs that need them.
Spec 18 (pipeline) done; all eighteen specs written. Fast-loop costs measured on this
machine: a persistent Blender server answers over a local socket in 0.08 ms, a shape-key
change plus a landmark read takes 10 ms, a zoomed-camera Workbench crop renders in 1.1 s
(15 s with render borders), MPFB targets are linear so optimiser steps and the 3DDFA
least-squares fit take microseconds, and a mesh silhouette takes 0.1 s. Its effort estimate
for the whole build is 35 to 90 five-hour API windows; it proposes a vertical slice first.
Next: critique and revise all specs (the six written before the rule first), overview
spec, fast-loop tooling.

## 2026-10-07 00:10 UTC — stopped at Jeff's request (API window nearly full)

Rule added after reading the drafts: **reality wins** over the AI-generated image where they
conflict (see CLAUDE.md, Source of truth). The critique pass must revise specs 01 to 05 and 09
against it; the writer prompts in `scripts/workflows/spec_writers.js` already carry it.

State: specs 01, 02, 03, 04, 05, 09 written (drafts, uncritiqued); all six research notes
done; everything pushed to hexcom master. Remaining specs to write: 06 head and face,
07 hair, 08 rig and pose, 10 shirt and gaiter, 11 gloves, 12 hard armour, 13 plate
carrier, 14 belt and leg rigs, 15 carbine, 16 materials library, 17 evaluation scene,
18 pipeline. Their prompts are in `scripts/workflows/spec_writers.js` (Workflow tool
script; run two agents at a time). After that: critique and revise pass, then
`spec/00_overview.md`, then the fast-loop tooling.

## 2026-10-06 — cloud session 1 (Fable)

Done: environment scouted; reference crops; five analyst notes plus a consolidated
reference analysis; research notes for dimensions (ANSUR II filtered to the soldier's
build) and generators (MPFB2 works headless, Rigify included); specs 01 (foot, ankle,
sock) and 09 (combat trousers) drafted; assets downloaded (textures, HDRIs, CC0 models,
MakeHuman packs, AI helpers) with a restore manifest; Workbench confirmed as the fast
headless form renderer (about 5 s). Spec document for Jeff:
https://claude.ai/code/artifact/e7f849ec-d7e4-4cfd-8fde-a85a6dc9c76e

In progress: a two-at-a-time workflow writing the remaining research notes (assets,
generators finish, Blender capabilities, AI helpers, prototypes) and the sixteen
remaining specs. The account's 5-hour API window is the limiting resource: keep at most
two agents running at once.

Next: critique and revise all specs (fidelity, feasibility, cross-spec interfaces),
then write spec/00_overview.md and start the fast-loop tooling (Blender server, metrics,
contact sheets). Render-heavy work waits for Jeff's GPU machine.
