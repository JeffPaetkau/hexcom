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

**Part 01, first pass (foot geometry), done** by a background agent; rebuilt, measured and
looked at here. S1 now loads the MPFB foot targets, solved by least squares through `linmodel`
(`scripts/parts/p01/fit_targets.py`); `scripts/parts/01_foot_ankle_sock.py` builds stages
sculpt, nails, masks, contact and frames (`Foot.Sculpt` and `Foot.Contact` on `Body.Mesh`, the
foot's vertex groups, ten nail plates, `Frame.Foot.L/R`); the sculpt's 32 amounts are fitted by
least squares (`p01/fit_sculpt.py`) into `p01/params.json`, not set by hand. 121 of 123 metrics
of spec 01 §8.2 pass (foot 282.0, ball 105.7, heel 72.1, bimalleolar 75.2, malleoli 77.1/87.6,
dorsum, arch, toe cascade, nails within 0.15 mm); three `--rebuild` runs give the same key and
the same twelve mesh hashes; a run is 4 s, 18 `form` views 13 s, a 2048² `eval` closeup 23 to
32 s. The renders read as an adult male foot (`renders/01_foot/sheets/`).

**Open from the foot pass.** (1) The heel-ankle girth is 335.7 against 353 +-6: this body's
shin front stands about 12 mm too far forward over the ankle, so the measure's front point lands
on the instep; that is spec 03's leg, not the foot. (2) MPFB's `vert-decr` foot target lowers
the ankle joint cube from 75 to 64 mm, so S2's ankle pivot sits below the malleoli; spec 08's
rig fit should place the ankle from the malleoli (the `foot.*` interface keys part 01 is to
publish). (3) The nail plates' free edges overhang the toe tips like a thin flake in 2048 px
closeups. (4) The sole view (V4) is unlit in the hero scene; it needs spec 17's LookDev scene.
(5) Library follow-ups part 01 worked around: spec 18 §4.13, "Left of W1 track a".

**Materials, first part (afternoon).** spec 16's library core (`scripts/lib/materials.py` and
`mat_catalogue`, `mat_core`, `mat_groups`, `mat_skin`, `mat_fabric`: recipes by name, the
`MG.Skin.Core`, `MG.Skin.Micro`, `MG.Tile.AntiRepeat`, `MG.Knit.Stitch` and `MG.Weather.Grime`
groups, lint) with the recipes part 01 needs (`Skin.Foot`, `Nail.Plate`, `Nail.FreeEdge`, the
sock knit and its reinforced heel and toe); spec 17's LookDev scene (`scripts/eval/lookdev.py`,
calibrated key 92 W, fill 32 W, rim 48 W; the rig turns with the camera so the sole is lit from
below); `scripts/eval/lookdev_p01.py` renders part 01 there with the recipes. Specs 16 §9 and 17
§4.8 carry the deviations (nail transmission, noise remapping, the knit's anti-repeat). The
foot reads as real skin; open: the mottling reads as freckles on the shin, the nail free edges
are uniformly white, the toes are barely redder than the dorsum, and part 01 has yet to publish
the masks and guides the skin reads (`Foot.SSSScale`, callus, tendons, veins, creases).

**The toes and the heel, with Jeff.** He found the toes too long, the heel too narrow, the
big toe too narrow and the lesser toes too straight, from the renders and his own reference
photos (kept in the ignored `cache/ref_feet/`). Part of what he saw was lens distortion: V1
put the toes 1.3 times nearer than the heel, so the part now judges proportions in `V1f`,
`V5f` and the square-on views. Variant sheets are in `renders/01_foot/sheets/` (`toes_`,
`heel_`, `hallux_variants.png`); the part 01 agent's code for them is uncommitted, waiting for
his pick of a big-toe row and a curl (recommended: X2c, the big toe 30 mm wide with a 4.5 mm
gap to toe 2 and the lesser toes curled 35 degrees) and of the heel (H1 provisional).

**Jeff's decisions, late afternoon.** The bare foot is to be photoreal, not because it is seen
but as practice for the much harder head ("if we can't get the foot right we have no hope"),
and because a barefoot loadout shot may come later. He locked X3 (big toe about 30 mm, toe 2 16,
a 4.5 mm gap between them, lesser toes curled 25 degrees, heel H1) as "an indication, not a
law": the numbers are a direction while nothing looks right yet. Two blind reviews he ran (one
ChatGPT, one fresh Claude) agree that the problems are structural, not proportional; they are
in `notes/review_2026-10-10_foot.md` and are the foot's work list. The lock is the default build
(spec 01 §0 row 16, §3.3, §10.2 Q3); everything passes but the heel-ankle girth (341, spec 03's
leg); `renders/01_foot/sheets/locked_variants.png`.

**Next** (no new work was started after this point; Jeff stopped for the week's budget):
1. The method trial is done (`notes/research_foot_hires.md`, code in
   `scripts/research/foot_hires/`, renders under `renders/research/foot_hires/`, which are not
   committed and rebuild in about 144 s): the chosen method is a dense copy of the foot
   (subdivided to about 0.17 mm on the toes) shaped by fields, with OpenVDB distance-field
   closing only where surfaces must merge (the webs). On the big toe it sets the nail into the
   toe under its folds, gives the tips a pulp, adds the first MTP prominence and the extensor
   tendon, and keeps MakeHuman's topology, UVs, groups and weights. Still wrong: the IP creases
   read as three parallel grooves, the nail ridges are too regular, a sawtooth at the free
   edge's corner, plantar creases as hard lines, toe 2 a little tubular, toes 3 to 5 untouched.
2. Build spec 18 §8.1's critic loop (`scripts/eval/critic/`: packet, prompts C1 to C3, schema,
   tally), adding a free-form ranked list like Jeff's two reviews, and for hidden parts with no
   reference crop, Jeff's photos (`cache/ref_feet/`, never committed) as C1's anchor. The
   critics are fresh agents spawned by the orchestrating session, one at a time.
3. **Done (evening): the critic loop and its first round.** `scripts/eval/critic/` (packet, prompts
   C1 to C3, schema with a ranked free-form list, tally; runbook in spec 18 §8.1). Round 1 on the
   trial (`notes/critic/foot_hires_r1/`: the three results, `tally.md`, the brief): FAIL, all three
   critics 4/10, 10 blocking, 42 merged items. Blocking, from all three: torn geometry at both
   distal corners of the big-toe nail (sawtooth) and deep in the 1-2 web; the big toe a wedge in
   profile (15.6 mm deep at the nail root against 19, no pulp ahead of or below the free edge).
   Major: the nails read as press-on tiles (flat, a thick white root edge, no eponychium, cuticle
   or lunula, an even French tip); the pulps are blocks from below, not oval domes. Fix these on
   the trial region and run round 2 (`packet.py --previous` turns round 1's defects into claims)
   before taking the method to the whole foot. **Round 2 (late evening)**: the fixes (cause of the
   torn corners: a skin-cutting gate that switched on and off between neighbouring vertices; of
   the torn web: a projection that stopped vertices part-way inside the closed surface; the big
   toe now 19.0 mm deep at the nail root) took the blocking defects from 10 to 0; scores 4, 4, 5,
   still FAIL (`notes/critic/foot_hires_r2/`). All three critics now lead with the nails: still
   press-ons (a template rounded rectangle in an even channel with a raised rim), an opaque cream
   French-tip free edge, highlights combed into regular streaks, no pink bed or lunula seen
   through the plate; then toe 2, an even sausage with no knuckle, waist or pulp flare. Next:
   the nail as geometry and shading together (no channel or rim; a clear plate over a pink bed;
   a thin, translucent, straight-cut free edge; faint broken ridges), toe 2's form, round 3.
   **Round 3 (Monday 12 October)**: the fixes (per-nail outlines, after finding that a width
   setting with inverted bounds had made every nail one scaled template; the plate under the
   folds; a straight-cut edge; a clear plate and a lunula by recipe override; a knuckle, waist
   and flare on toe 2) scored 4, 4, 4, FAIL, 2 blocking, and only 1 or 2 of round 2's 28 claims
   confirmed fixed (`notes/critic/foot_hires_r3/`). The packet was not stale: the changes are
   too subtle to read at the packet's scale (no visible lunula, the plate still milky, its
   outline still a rim; compare `renders/research/foot_hires/fields_r3/zooms/`). Blocking: no
   lunula or plate zoning; a crisp ledge ringing the underside of toe 2 like a sleeve cuff (from
   the new knuckle and waist fields). New and broad: every skin surface wears one crisp Voronoi
   crackle, read as crazed porcelain (spec 16's `MG.Skin.Micro`, a library fix). Lessons: a fix
   agent's report claimed more than its renders show, so check each fix in the critics' own
   views at packet scale (or with one critic) before a full round; three rounds of nail tweaks
   have stalled at 4, so the next attempt should rebuild the nail from its anatomy (matrix
   under the proximal fold, the bed, the onychodermal band, the lateral grooves) against close
   photographs, not adjust the current one. Order for the next run: the toe 2 ledge, the skin
   micro-relief in the library, the nail rebuild, then round 4. **Round 4 (Monday evening)**:
   toe 2's cuff fixed at its cause (features placed along tilted bone axes landed 3 to 8 mm
   toward the heel on the underside), `MG.Skin.Micro` rebuilt in the library (soft directional
   grooves, depth by region; the crackle is gone), the nail rebuilt (plate bonded to the bed,
   lunula, onychodermal band, ivory edge). Changes now read at packet scale. Scores 4, 4, 4,
   FAIL; blocking 1 (bald toes: no hair built); merged items 36 to 30; 9 or 10 of round 3's 30
   claims confirmed fixed (`notes/critic/foot_hires_r4/`). The plateau at 4 across four rounds,
   while the defects fall, points at the nail's construction: every round the critics see a
   tile in an even gutter with exposed edges and a French-manicure tip, whatever the shading.
   Next: model the nail and its folds as one continuous surface (the lateral folds as real
   overhanging lips over the plate's margins, the proximal fold over the root, no separate
   plate edge to see), soften the lunula's edge and drop the white stripe; give the big toe
   its depth (21 mm at the IP for a 31 mm width reads flat); the seam under toe 2; capillary
   colour on knuckles and tips; the toe hair (spec 01 §6.1); then round 5, the last before
   spec 18's escalation rule sends the region to Jeff. **Round 5 (Monday night)**: the nail
   is now the skin's own surface shaded by masks, with only the free edge a separate sliver; the
   big toe 25.1 mm deep at the IP (was 22.3); toe 2's seam softened; capillary colour; toe hair
   (10 curves on the big toe, 3 on toe 2). Scores 5, 5, 4: the first rise above 4; still FAIL,
   2 blocking (no extensor tendon on the big toe; no lunula reads), 31 merged items
   (`notes/critic/foot_hires_r5/`). **Escalated to Jeff** (spec 18 §8.1.5: five rounds): nobody
   iterates on this region until he answers. The question: accept the method at this level
   (median 5, the structural faults gone) and take it to the whole foot, where the open items
   (a thin, even outline still read round the nail, the cream free-edge band, a lunula that does
   not read, stamped knuckle creases, friction ridges as straight stripes instead of whorls,
   the extensor tendons) are worked as part of the whole-foot pass with its own round count;
   or keep iterating on the region; or step back to the foot's purpose (practice for the head)
   and move on. Recommended: the first.
   working down the reviews' list (nail integration, toe cross-sections and joints, webs, the
   forefoot's structure, the dorsum's tendons and veins, the first MTP prominence).
4. Then the sock and the last (part 01 §4.10 to §4.13), the `foot.*` interface keys, and spec
   02's boot.
Starter prompt: "Read art/characters/sgt_morgan/CLAUDE.md and the newest entry of
art/characters/sgt_morgan/notes/session_log.md, then continue with the next steps listed
there. Work in art/characters/sgt_morgan."

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
