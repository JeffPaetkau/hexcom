# Session log

Newest first. One entry per working session, a few lines each: what was done, what is
next, anything a fresh session must know.

## 2026-10-10 — first local session on Jeff's workstation (Opus): setup and GPU

**Done.** Hand-off steps 1 and 2. Jeff's Blender MSI install upgraded in place from 4.5.0
to 4.5.14 LTS at his word (the same build the cloud measured). `scripts/setup_session.sh` runs
in Git Bash; the new `scripts/setup/` holds `fetch.py` (verified, resumable downloads, the
manifest restore and `--record-hashes`, the env record), `downloads.json`, `mpfb_install.py`,
`gpu_probe.py`, `smoke.py` and the requirements. First run 469 s, a re-run 33 s; MPFB 2.0.17
and the 11 packs live in `cache/blender_user` (Jeff's own Blender is untouched); the 137
manifest files verify, and the manifest is now schema 3 with sha256 for the 27 that had only a
size. `scripts/lib/env.py` records the Cycles device (OptiX on the RTX 3050, `SGT_DEVICE`
overrides) and `use_device()` also puts the OIDN denoiser on the GPU, which Blender leaves on
the CPU by default: test 1 at 1080p went from 15.3 s to 4.1 s at 32 spp (40.6 s at 512); the
cloud took 68 to 91 s at 32 spp. Spec 18 §3.2, §4.2.2 and §4.2.4 record it all.

**Know this.** Git for Windows checks text out with CRLF (`core.autocrlf=true`), which breaks
bash; this folder's `.gitattributes` now forces LF. Bash's `GROUPS` is a built-in, so the
spec's `GROUPS=ai` silently fetched nothing; it is `AI_GROUPS` now. Run Blender with
`source cache/env.sh` first (it sets `BLENDER_USER_RESOURCES`), or through `lib/env.py`.

**Step 3, first part, done** by two background agents, reviewed and run here: spec 17's
render harness (camproj, camera with the equivalent crop camera, the preset registry with
ref, p17, p01 and p02 presets, render tiers, the in-scope scene, the grade, minimal masks) and
spec 18's `sheet.py` (spec 17 §4.14); spec 18's library core, the Blender server and `bl.py`
(spec 18 §4.13). `setup_session.sh --check` now ends with `bl.py selftest`; `bl.py selftest
--lib` runs the nine module self-tests in the server. On the RTX 3050 a warm Workbench crop
is 0.03 to 0.10 s and an `eval` hero frame 4 s. Review fixed one bug (later renders in a
process denoised on the CPU). Found: spec 17's nominal lights render 3 to 5 times too bright
(calibration will settle it; nothing in the foot or boot form work depends on it); GPU renders
agree within 1/255, not bit for bit; spec 01's medial view must isolate the foot. Cost: the two
agents and this session took the week from 57 to 59 percent.

**Later the same day, toward the foot.** Spec 01 revised under the reality-wins rule and
against the values it shares (its new §0 lists fifteen decisions: ANSUR "Tight" figures, foot
282 mm; a 1855 mm, 83 kg man; the body is `Body.Mesh`, the rig `Morgan.Rig`; in the hero pose
the feet stand on the boots' footbeds; materials from spec 16; spec 17's harness and presets;
one-foot render copies for the closeups), with dated notes in specs 04 and 08. Jeff answered
its questions (§10.2): Q7 the figure matches the drawing, so the rest stature is **1835 mm**
barefoot (in boots the footbeds add 42 mm and the pose costs 22, putting the skull top on the
drawn line; at rest, barefoot, it measures 9 px below it, as it should); Q8 the foot stays
282 mm; Q9 the build follows the drawing's lean V-taper, not ANSUR's 83 kg. CLAUDE.md records
it; specs 01, 03, 04, 08 and 18 carry dated notes; the others are corrected when their part is
built. `scripts/build_all.py` builds S0 to S2 in cut-down form (spec 18 §4.6 note):
`cache/body/rigged.blend` is the 1835 mm MPFB male with the default rig, the start for part 01. `measure.py`, `linmodel.py` and `optim.py` are built and wired into the server (spec 18 §4.13, second part); review fixed a Windows lock race in `cache.locked()` that killed about one contended writer in twenty.

**Next.** `scripts/parts/01_foot_ankle_sock.py` on `cache/body/rigged.blend`, as revised
spec 01 lays out (its §0, §4, §9.2): foot first (the MPFB foot targets in S1 by a linear
least-squares fit, the landmark sculpt with `lib/sculpt.py`, toes, nails), judged on `form`
renders with a placeholder skin, since spec 16's `materials.py` does not exist yet; then the
sock and the last; then spec 02 and the boot. Starter prompt: "Read art/characters/sgt_morgan/CLAUDE.md
and the newest entry of art/characters/sgt_morgan/notes/session_log.md, then continue with the
next steps listed there. Work in art/characters/sgt_morgan."

**The ledger will not come.** The cloud session is archived (Jeff, 2026-10-10) and never pushed
`notes/interface_ledger.md`. Its job is done here instead, one part at a time: before a part
is built, its spec is revised against the reality-wins rule and against the values it shares
with other specs (each spec's §10, spec 18 §10.2, spec 16's material resolutions, which
override every part's §5), and the decisions are written into the specs themselves.

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
