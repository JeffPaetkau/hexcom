# Session log

Newest first. One entry per working session, a few lines each: what was done, what is
next, anything a fresh session must know.

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
