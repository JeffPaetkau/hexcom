# Part 18 — Pipeline, tooling and evaluation harness

Status: draft 1 (spec writer), 2026-10-10, written under the **reality-wins** rule (`CLAUDE.md`, Source of truth) and Jeff's **scope decision of 2026-10-10** (`CLAUDE.md`, Scope): the deliverable is the unit model (soldier, clothing, armour, gear, carbine, rigged); the evaluation scene is only what changes the model's render (hero camera, key, cool side and world lights, a plain floor, the grade); the hangar set, floor joints, the floor-pool light, depth of field and haze are deferred and appear nowhere in this spec's build order or effort table; the pipeline ends in an export stage for game engines (Godot 4.7 .NET first). Owner files: `scripts/setup_session.sh`, `scripts/setup/*`, the core of `scripts/lib/` (§4.3), `scripts/server/*`, `scripts/tools/*`, `scripts/build_all.py`, `scripts/export/*`, `scripts/eval/metrics/*`, `scripts/eval/critic/*`, `.gitignore`, `.gitattributes`, the format of `notes/session_log.md` and `renders/eval/log.*`, and `deliver/manifest.json`. Collections `Parts`, `PartNN.<Name>`, `Character`, `Export.*`; object prefix `Export.*`.

Conventions (from `CLAUDE.md`): millimetres in this spec, metres in Blender; world origin on the floor midway between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT = viewer's right**; every left/right is the soldier's own. "The project directory" (`$PROJECT_DIR`) is `art/characters/sgt_morgan/` of the hexcom repository; the cloud working copy is `/home/user/sgt_morgan`. Every script resolves paths from its own location and never contains an absolute path. Reference pixels are full-image coordinates of `ref/reference_full.png` (1672 × 941, x right, y down); 1 px = 2.12 mm at the figure's depth.

**Provenance tags** on every number: **M** measured on this container on 2026-10-10 (Blender 4.5.14, 4 cores, idle box, load 0.3; probe scripts saved as `scripts/research/probe18_*.py`), **S** sourced (a published value or another note's measurement, cited), **D** taken from another spec (section cited), **E** estimated, with **[VERIFY]** where a test on the named machine settles it.

Sources read: `CLAUDE.md` (all), hexcom `summary.md` (budget rule, build gotchas, constants), `notes/session_log.md`; `notes/research_generators.md` §1 and §6; `notes/research_assets.md` §1, §6, §7 and the manifest itself; `notes/research_ai_helpers.md` §1–5, §8, §9; `notes/research_blender_capabilities.md` (summary, §1, §7, §10, recommendations); `notes/research_prototypes.md` §7–8; sections 9 and 10 of specs 01–15 and 17, plus spec 08 §3.3, §3.6, §6, §7.2, §7.6, spec 17 §2.2, §2.6, §4.3, §4.9, §4.13 and its scope note, spec 06 §4 steps 4–7 and §8; the existing `scripts/setup_session.sh`, `scripts/research/mpfb_setup_from_zero.sh`, `mpfb_install.py`, `build_manifest.py`; `game/project.godot` of hexcom; `ref/reference_full.png` and the rembg mask. Spec 16 (materials and textures) was written alongside this one; its §5.2–§5.6, §7.2, §9 and §10 were read before this draft was finished.

---

## 1. Purpose and acceptance

### 1.1 What this part is
The machinery that turns sixteen part specs into one rigged, exported model across many short sessions in ephemeral containers and on Jeff's Windows machine: the repository layout; the setup script that rebuilds the toolchain from nothing on Linux and in Git Bash; the shared Python library every part script imports; the standard shape of a part script; per-part caches and the `build_all.py` driver that assembles, fits, poses, simulates, bakes, evaluates and exports in order; the **fast feedback loop** (a persistent Blender server, Workbench form renders in about a second, contact sheets of many variants beside the reference crop, measurement from the mesh before any render, optimisers over MPFB targets and part parameters, a least-squares fit of MPFB target weights to the 3DDFA landmarks); the critic protocol and objective metrics that decide when a part is done; the evaluation log; the export stage (glTF 2.0, baked PBR textures, LODs, a Godot humanoid skeleton, the rules' 1.80 m scale); the git workflow and the session protocol; time budgets on 4 CPU cores and in the account's 5-hour API window; and the dependency graph and build order of parts 01–17. It builds no geometry of its own.

### 1.2 What "perfect" looks like
A fresh cloud container runs `bash scripts/setup_session.sh` and is ready in about 12 minutes, download-bound; a second run takes under 30 seconds and changes nothing. Jeff runs the same command in Git Bash on Windows and gets the same toolchain with his GPU. `python3 scripts/build_all.py --to export` rebuilds the whole unit model from scripts and downloads alone, resumes where it stopped after an interruption, skips every stage whose inputs did not change, and produces bit-identical meshes on a second run. An agent iterating on a part changes a parameter and sees twelve Workbench variants beside the reference crop in under 30 seconds, with every variant already measured (landmarks, girths, silhouette IoU) in milliseconds before anything is rendered; Cycles is touched only for acceptance. Nothing is called done without a render, a metrics JSON and three critic scores in the evaluation log. The exported glTF opens in Godot 4.7 as one skeleton whose humanoid bone map validates, at 1.80 m, facing −Z, with textures at the resolutions spec 16 sets. Nothing is lost when a container dies, and the repository never holds a file GitHub would refuse.

### 1.3 Verification views (the harness's own outputs; presets in `scripts/eval/presets/p18.json`)
All crops use the **equivalent crop camera** of §4.8.2 (same centre of projection as `Scene.Cam.Hero`, focal length scaled, lens shift), never a render border (decision D1, §2.4).

| View | What | Camera (preset, equivalent lens and shift) | Compared with | Pass |
|---|---|---|---|---|
| p18.V1 Variant sheet | 12 Workbench variants of one parameter sweep beside the reference crop, each labelled with its parameters and metrics | `ref.head_face`: crop (715,30)–(885,200) ×5 → lens 452.42 mm, shift (−0.2118, +2.0912), 850 × 850 | `ref/crop_head_face.png` | sheet built ≤ 30 s warm; the reference cell is byte-identical to the crop file; cells sorted by objective; labels legible at 100 % |
| p18.V2 Silhouette map | render alpha versus the reference rembg mask; true positive grey, false positive red, false negative cyan, the ±3 px don't-care band yellow, declared differences hatched | `ref.soldier_full`: (580,20)–(1020,935) ×1 → lens 174.80 mm, shift (−0.0818, −0.0159), 440 × 915 | `assets/ai/rembg_out/soldier_full_u2net_mask.png` resampled to ×1 | mesh-splat IoU (§4.8.4) and render-alpha IoU agree within 0.01; full-body IoU ≥ 0.90 at acceptance |
| p18.V3 Face landmarks | MediaPipe 478 landmarks of reference (red) and render (cyan), ratio table, pose gate | `ref.head_face` as V1 | `assets/ai/face_ref_landmarks.json` | pose within ±2° of (+14.6°, −9.9°, −1.2°); spec 06 §8.2-A ratios in tolerance; NME ≤ 0.04 |
| p18.V4 Critic pair | reference crop and render at identical size and scale side by side, plus onion (50 %) and difference images | any part preset that names a reference crop | that crop | the packet builder reproduces the crop exactly; render from the `eval` tier; no image over 2000 px on its long side |
| p18.V5 Export round trip | the re-imported glTF in Workbench through the hero camera scaled by s = 1800 / stature about the origin, over the source `form` render | `hero` full frame, camera position × s, lens 46 mm | the source model's `form` render | silhouette IoU ≥ 0.995; landmark error ≤ 2 px; rest height 1800 ± 2 mm; bone count as exported |
| p18.V6 Godot import | headless import report on the cloud; on Jeff's machine a screenshot from a camera converted to Godot's frame | Godot `Camera3D` at (0, 0.6 s, −4.5 s) m (s = export scale; (0, 0.582, −4.367) at s 0.97035), `rotation_degrees` (3.9, 180, 0), `keep_aspect` KEEP_WIDTH, `fov` 42.74° (46 mm on a 36 mm sensor), 1672 × 941 | p18.V5 | report: one `Skeleton3D`, humanoid `BoneMap` with no unmapped required bone, surfaces and materials as exported; screenshot silhouette IoU ≥ 0.98 against V5 |

### 1.4 Pass criteria a critic can score
1. **Setup.** From an empty container: ≤ 15 min wall; ≈ 1.7 GB downloaded without the AI helpers, ≈ 2.1 GB with them, ≈ 2.4 GB with Depth Anything (§3.3); a re-run ≤ 30 s with zero bytes downloaded; every download verified by size and SHA-256 (SHA-512 for Godot); `--check` passes (Blender version string, MPFB system assets installed, a Workbench render, PIL, a server ping).
2. **Windows.** The same script in Git Bash on Jeff's machine finishes with the same `--check` result, using his installed Blender 4.5 if present.
3. **Determinism.** Two `build_all.py --to assemble` runs give identical per-object mesh hashes (vertex coordinates rounded to 0.01 mm).
4. **Resumability.** Killing `build_all.py` in any stage and re-running finishes without redoing completed stages and without manual clean-up.
5. **Fast loop.** Warm server: ping ≤ 1 ms, parameter change plus landmark measurement ≤ 20 ms, one Workbench crop ≤ 2.5 s, silhouette IoU from the mesh ≤ 0.25 s at ×1; a 12-variant contact sheet ≤ 30 s.
6. **Measurement accuracy.** Girth of a 64-segment cylinder of radius 50 mm = 313.9 ± 0.1 mm; linear target model equals the depsgraph within 0.01 mm; projected landmarks agree with `world_to_camera_view` within 0.1 px.
7. **Optimisers.** CMA-ES solves 10-D Rosenbrock to 1e−6 in ≤ 6,000 evaluations; the bounded linear solve recovers known synthetic target weights within 1e−4.
8. **Critics.** Every round has three JSON results that validate against §8.1.4, from three lenses, scored on identical packets; pass = median overall ≥ 8, no blocking defect, every automatic metric in tolerance; never more than five rounds per part per milestone.
9. **Log.** Every evaluation event appears in `renders/eval/log.jsonl`; `log.md` regenerates from it; milestone images ≤ 400 KB each.
10. **Export.** glTF 2.0 validates (Khronos validator where available, no errors); reimport in Blender gives the exported bone count, morph targets and the `Hero.Pose` action; rest height 1800 ± 2 mm; faces −Z; Godot headless import report clean; texture resolutions as spec 16 sets; LOD triangle counts within §4.10.3.
11. **Repository.** No tracked file over 50 MB; nothing under `cache/` or `assets/` (except the two whitelisted JSON files) tracked; growth per milestone reported by `scripts/tools/repo_budget.py`.
12. **Sessions.** Every session starts with setup and the log, claims one task, ends with a commit, a push and a log entry; never more than two agents at once.

---

## 2. Reference observations

### 2.1 The reference as data for the harness (all measured with PIL on `ref/reference_full.png` and the rembg mask)

| Observation | Value | Use in the harness | Source |
|---|---|---|---|
| Image | 1672 × 941, 8-bit sRGB, no alpha | every comparison is in display space after AgX and the grade (spec 17 §5.6) | M |
| UI panels | tabs and title (0,0)–(466,196); item cards (44,196)–(412,760); BACK (35,848)–(189,899); UNIT STATS (1259,61)–(1637,374); CONFIRM (1325,841)–(1637,900) | `scripts/eval/ui_mask.json` (spec 17 owns it); masked in every metric | D 17 §2.6 |
| Figure bounding box (rembg, threshold 127, ×1) | (622, 20)–(978, 911), rifle and boots included | crop presets must contain it; IoU computed inside `ref.soldier_full` | M |
| Silhouette area at ×1 | 178,081 px (44.2 % of the 440 × 915 crop) | IoU denominator | M |
| ±3 px edge band | 24,587 px = 13.8 % of the silhouette | the don't-care band; without it a horizontal shift costs 0.016 IoU per pixel (1 px 0.984, 3 px 0.953; vertical 1 px 0.992) | M |
| rembg soft pixels (16–239) | 3.6 % of the ×2 mask | threshold at 127, never a soft blend | M (S: research E §5 gives 3.5 %) |
| rembg defects | ragged fringe at his right hip, x ≈ 170–250, y ≈ 900–1100 of the ×2 crop (full image ≈ (665–705, 470–570)) | hatched "unreliable" region in `declared_diffs.json`, excluded from IoU | S research E §5 |
| Background ring 6–30 px outside the silhouette | mean #4b4845, median #2f3334, but bimodal: **#202426 above the horizon (y < 616)**, **#8b7f73 on the floor (y ≥ 690)** | the flat backdrop behind transparent-film renders is #202426 (above the floor only; the floor plane is rendered, spec 17 scope note); a single mean colour would put a grey halo round the head | M |
| Crops (spec 17 `ref.*` presets) | soldier (580,20)–(1020,935) ×2; head (715,30)–(885,200) ×5; torso (630,140)–(990,490) ×3; arm R (600,170)–(770,490) ×3; arm L (850,170)–(1000,490) ×3; hands and rifle (630,230)–(950,570) ×3; belt and hips (630,410)–(990,630) ×3; legs and knees (630,550)–(990,830) ×3; boots (610,750)–(1010,935) ×3 | critic pairs and contact sheets use exactly these boxes and scales | D 17 §4.3 |
| Scale | 875 px from skull top (y 20) to right sole (y 895) = 1855 mm → 2.12 mm/px at the figure | 100 mm scale bar = 47.2 px on overlays | S consolidated, Agreed scale |
| MediaPipe on `crop_head_face.png` | head pose yaw +14.6°, pitch −9.9°, roll −1.2°; 13 ratios (face width/height 0.900, jaw/face 0.839, inner IPD/face 0.244, outer IPD/face 0.610, mouth/outer IPD 0.585, nose width/inner IPD 1.152, nose length/face height 0.235, eye–mouth 0.447, nose–chin 0.460, eye aspect 0.329, lip height/mouth 0.249, nose length/width 0.930); detection 0.38 s | pose gate and ratio targets (§8.2) | S research E §2 |
| 3DDFA_V2 | 68 landmarks with depth; pose yaw −15.2° (opposite sign convention), pitch −10.0°, roll −3.3°; generic identity | one-off sparse 3D targets (§4.8.6) | S research E §3 |
| Detector disagreement | MediaPipe versus 3DDFA on the same image: 1–4 % of face height | no ratio tolerance tighter than 3 % | S research E §3 |
| Depth Anything V2 Small | relative inverse depth; inside the mask 0.49–0.72 (p5–p95), background 0.26; rifle 0.661 in front of the chest 0.570 | ordinal layering checks only (§8.2) | S research E §4 |
| Named colour patches | P1 #e6bfac (778,70), P2 #d19b87 (792,100), P3 #897967 (800,220), P4 #333b47 (935,720); P5 floor pool is informational under the scope note | ΔE00 on the graded render (§8.2) | D 17 §2.2 |

### 2.2 What the reference can and cannot verify
The image is the authority for identity (face, hair, pose, colours, gear arrangement, emblem, wear) and nothing else. Under the reality-wins rule several parts **deliberately** depart from the drawn silhouette: the hips stand ≈ 55 px higher than drawn (spec 08 D1: hip joints at 963 mm rest, ANSUR femur), the belt sits ≈ 140 mm higher (spec 14 D1), the handguard ends 23.5 px past the drawn cap (spec 15 Q1), the eye fissure and alar base are human maxima rather than the drawn sizes (spec 06 decisions 1–2), and the right foot turns 85° rather than 90–100° (spec 08). A harness that scored these as errors would push every part back toward the drawing. Each such departure is therefore registered in **`scripts/eval/declared_diffs.json`** — `{id, owner_spec, decision, polygon_px, metric: "iou|landmark|patch", expected_delta}` — and the metrics report them separately ("declared") instead of counting them against the part. A part may add an entry only in the same commit as the spec decision that justifies it (CLAUDE.md rule 8).

### 2.3 Hidden surfaces
Most of the model (the feet, socks, the skin under the clothes, the carrier's back, the radio) has no reference at all. For those, the reference of the critic packet is the spec's own §3 dimension tables and, where the spec names one, a real product photograph that Jeff supplies; the automatic metrics are the part's `measure()` report against those tables (§8.2, part measurements).

### 2.4 Decisions (pipeline), including where an earlier "as drawn" choice is overruled

| # | Topic | Earlier choice or default | Decision and reason |
|---|---|---|---|
| D1 | Crop renders | spec 17 §4.3 render borders with `resolution_percentage` = 100 × scale | **Equivalent crop camera** (lens × W/w, shift in units of the crop width under horizontal sensor fit). Measured: Workbench head ×5 1.27 s against 14.9 s with a border (the border path renders the whole enlarged frame); soldier ×2 2.5 s against 4.1 s; framing identical within 0.2 px (IoU 0.997–0.999); the border path also lost a pixel column to rounding. Spec 17's `camera.py` implements both; presets default to the equivalent camera. |
| D2 | Order of checks | critics on every round | **Metrics before critics**: a round whose automatic metrics fail is not sent to critics (saves API budget and critic attention). |
| D3 | Target-space evaluation | depsgraph per evaluation (spec 06: ≈ 50 ms) | **Linear target model**: MPFB targets are shape keys relative to Basis, so landmark positions are an exact linear function of target weights (measured: max error 0.0005 mm over three random weight sets; 5.4 µs per evaluation of 120 landmarks). The depsgraph (10.6 ms measured with Armature and Mask modifiers) confirms each accepted step. |
| D4 | Server transport | — | JSON lines over TCP on 127.0.0.1 (ping 0.08 ms measured); a file-queue transport with the same messages for any machine where a listening socket is refused. |
| D5 | Part caches | specs name `builds/`, `assets/body/`, `assets/cache/`, `assets/generated/` | **Everything rebuildable lives in `cache/`** (gitignored): `cache/parts/NN_name.blend` written with `bpy.data.libraries.write` (only the part's data-blocks), `cache/body/*.blend`, `cache/generated/NN/`, `cache/sim/`. The other paths are renamed in the critique pass (§10.2). |
| D6 | Caches across machines | — | Not transferred. Jeff's machine rebuilds from scripts (the whole chain is minutes of CPU, §9.4); only the repository crosses. |
| D7 | Export scale | 1800 / 1855 = 0.97035 (specs 08, 15, 17) versus 1800 / 1877 (spec 06, from spec 04's rest stature 1877) | **Computed at export** as 1800 / (measured rest stature of `Body.Mesh` in mm), never a constant. Whichever of spec 04's D1 or the brief's 1855 wins the critique pass, the game man is 1.80 m. [2026-10-10, Jeff: the rest stature is 1835 mm, so the figure in boots matches the drawing (spec 01 §10.2 Q7); s = 1800 / 1835 ≈ 0.981, still measured, not typed.] |
| D8 | Game file format | spec 08 `export/sgt_morgan.glb` with embedded textures | **glTF separate** (`.gltf` + `.bin` + external PNG/JPEG textures in `deliver/textures/`), because GitHub refuses files over 100 MB and Jeff asked for textures as separate files; a `.glb` is built on demand for engines that want one and is not committed. |
| D9 | Interfaces between parts | `assets/interfaces.json` (specs 10, 13, 15) under an ignored folder | Keep the path and **whitelist it** in `.gitignore`: it is the contract between parts and must survive containers and show in diffs. |
| D10 | `deliver/` | spec 17 §10.1: add `deliver/` to `.gitignore` | **Tracked** (CLAUDE.md rule 6 and the scope decision): committed at milestones; only `deliver/tmp/` is ignored. Spec 17's packed 0.6–1.5 GB `.blend` is not a deliverable; the deliverable `.blend` references external textures. |
| D11 | Full-figure overlay tolerance | consolidated analysis "as drawn" thighs (28 % short) and hip height y 452 | **Overruled** by the reality-wins rule (ANSUR segment lengths, spec 08 D1). The harness scores the legs against spec 08's landmark table with the declared-difference polygons of §2.2, not against the drawn joints; the full-figure IoU threshold 0.90 already allows for it. |
| D12 | Committed evaluation images | `renders/eval/*.png` | JPEG q88, ≤ 1600 px on the long side, ≤ 400 KB, overwritten in place at milestones only; the full-resolution PNGs stay in ignored folders. A 1 MB PNG per part per milestone would add ≈ 0.5 GB to the history over the project. |
| D13 | Interpreter for setup tooling | system `python3` (Linux only) | `scripts/setup/fetch.py` runs on system Python 3 on Linux and on **Blender's bundled Python 3.11** on Windows (it has `ssl`, `hashlib`, `zipfile`, `venv`, `ensurepip`; M on Linux), so Jeff needs no separate Python for setup. |
| D14 | Measurement code | `measure_<part>()` spread over `scripts/lib/measure.py` and `scripts/eval/measure_*.py` | One core module `scripts/lib/measure.py` (primitives, §4.8.4) owned here; each part's `measure()` lives in its own part script and returns JSON in a fixed envelope. |

---

## 3. Real-world reference

The "real-world reference" of a pipeline is its toolchain, the machines it runs on, the formats it must emit and the budgets it lives inside. Every number below is what the setup script verifies or what the time budgets of §9 are built from.

### 3.1 Toolchain components (sizes and hashes verified on 2026-10-10)

| Component | Version | Source | Bytes | Checksum | Installed to | Tag |
|---|---|---|---|---|---|---|
| Blender, Linux | 4.5.14 LTS (hash 62c1db4208e8) | `https://download.blender.org/release/Blender4.5/blender-4.5.14-linux-x64.tar.xz` | 378,045,212 | sha256 `9ba871ff2ecd36526b77432745980b7e6664ecd0c7ca11c48849073dcfe06da3` | `/opt/blender/` as root, else `~/.local/opt/`; ≈ 1.2 GB unpacked | S (release `.sha256` file) |
| Blender, Windows | 4.5.14 LTS | `…/Blender4.5/blender-4.5.14-windows-x64.zip` | 398,661,046 | sha256 `b9533d2397ac1984db4466fb23a7a4649391cca93f6e84209f9bcc60d071c8b9` | an installed 4.5 is used first; else `%LOCALAPPDATA%\sgt_morgan\` | S |
| MPFB extension | 2.0.17 | `https://extensions.blender.org/download/sha256:4f0a…7a87/add-on-mpfb-v2.0.17.zip` | 45,031,536 | sha256 `4f0a879d64a39bf646fbf5f53601ac678855da329d650617dca5737548239a87` | Blender user extensions `user_default/mpfb` (84 MB) | S, M (hash recomputed) |
| MakeHuman packs (11) | CC0 | `https://files.makehumancommunity.org/asset_packs/<p>/<p>_cc0.zip` (mirror `files2.`) | 553,102,867 in total | sha256 per pack, §4.2.3 | MPFB user data dir (≈ 620 MB extracted) | S sizes (research B §1.3), M hashes |
| Texture, HDRI and model manifest | schema 2 | `assets/manifest.json` (ambientCG, Poly Haven, cgbookcase, OpenGameArt, TheBaseMesh, 3dtextures) | 713,082,513 (47 assets, 138 files) | md5 on 104 files, sha256 on 6, size only on 28 → sha256 recorded once (§4.2.3) | `assets/textures/`, `assets/hdri/`, `assets/models/` (≈ 1.1 GB with extractions) | M (manifest read) |
| AI helper venv | Python 3.13 (Linux), 3.11 (Windows) | PyPI: mediapipe 0.10.35, opencv-python-headless, pillow 12.3.0, numpy 2.5.3, rembg 2.0.85, onnxruntime 1.30.0 (pulls scipy 1.18.1, numba); `--with-depth`: torch 2.14.1+cpu, torchvision 0.29.1+cpu, transformers 5.18.0, safetensors 0.8.0 | ≈ 230 MB of wheels, ≈ 420 MB more with depth | pip hashes are not pinned (wheel availability differs by platform); versions pinned | `assets/ai/venv/` (2.1 GB with torch) | M (`pip list` in the existing venv), E (wheel sizes) |
| MediaPipe FaceLandmarker | float16/1 | `https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task` | 3,758,596 | sha256 `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff` | `assets/ai/mediapipe/` | M |
| Canonical face mesh | — | `https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/mediapipe/modules/face_geometry/data/canonical_face_model.obj` | 45,999 | sha256 `8bac80443397e113f41a8b565ea72c59390bc031d9defab289dba7bc0c54e618` | same | M (the URL tracks master: the hash guards against drift) |
| rembg u2net | v0.0.0 release | `https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx` | 175,997,641 | sha256 `8d10d2f3bb75ae3b6d527c77944fc5e7dcd94b29809d47a739a7a728a912b491` | `assets/ai/rembg_models/models/u2net/` (`U2NET_HOME`) | M |
| Depth Anything V2 Small | HF `depth-anything/Depth-Anything-V2-Small-hf` | `…/resolve/main/model.safetensors`, `config.json`, `preprocessor_config.json` | 99,173,660 + 950 + 775 | sha256 `3152477ce0d8d6978d76b995120de97cb5b928701fd0f817769f59e249a16b70` (model) | `assets/ai/depth_anything_v2_small/` | M |
| 3DDFA_V2 | commit 1b6c676 | `https://github.com/cleardusk/3DDFA_V2.git` (weights in the repo) | ≈ 46 MB after trimming `.git`, `examples`, `docs` | git commit | `assets/ai/3ddfa_v2/repo/`, one-off (`--with-3ddfa`) | S research E §1, §9 |
| Godot, Linux (import checks) | 4.7.2-stable | `https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64.zip` | 77,860,424 | sha512 `9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65` | `cache/tools/godot/` | S (release `SHA512-SUMS.txt`) |
| Godot, Windows | 4.7.2 .NET | Jeff's WinGet install `Godot_v4.7.2-stable_mono_win64_console` (`GodotEngine.GodotEngine.Mono`) | — | — | detected, never downloaded | S hexcom `summary.md` |
| git-lfs | 3.4.1 | preinstalled on the cloud image | — | — | — | M |

The packs' individual hashes are in §4.2.3. TripoSR and SD-Turbo are not installed (research E §6–7: dropped); the MediaPipe selfie segmenter and `bria-rmbg` are deleted by `--prune` (research E §9).

### 3.2 Measured costs on this container (the numbers the fast loop is designed around)
Probes: `scripts/research/probe18_fastloop.py` and `probe18_crop_camera.py` (Blender) and `probe18_server.py` with `probe18_client.py` (server and system-Python client), on `renders/research/mpfb_default.blend` (MPFB human: 19,158 vertices with helpers, 13,380 after `Hide helpers`, 26,756 triangles; 8 macro shape keys; Armature and Mask modifiers).

| Operation | Cost | Notes | Tag |
|---|---|---|---|
| Blender cold start, user preferences (MPFB enabled) | 2.24 s | `blender -b --python-expr pass` | M |
| Blender cold start, `--factory-startup` | 0.44 s | MPFB initialisation costs ≈ 1.8 s | M |
| Open the 3.4 MB MPFB file | 0.45 s | compressed | M |
| Save / re-open an 11.6 MB uncompressed cache `.blend` | 0.019 s / 0.042 s | caches are saved uncompressed | M |
| Shape-key change + depsgraph update + read all evaluated vertices | 10.6 ms median (34 ms first) | with Armature and three Mask modifiers, 8,428 output vertices | M |
| Same with modifiers off | 1.8 ms | 19,158 vertices | M |
| Linear target model: build | 2 ms per shape key | `foreach_get` of each key's coordinates | M |
| Linear target model: 120 landmarks | 5.4 µs per evaluation | exact: max error 0.00024–0.00048 mm over three random weight sets | M |
| Linear target model: whole mesh in numpy | 1.24 ms | 19,158 × 3 | M |
| Projection of 13,380 vertices through the hero camera | 0.27–0.30 ms | spec 17 `camproj` formulas | M |
| Silhouette from the mesh (numpy splat + 3 × 3 closing) | 105 ms soldier crop ×1 (440 × 915); 227 ms full frame; 447 ms soldier ×2 | 26,756 triangles; an edge-function rasteriser took 469–878 ms | M |
| IoU of two masks | 1.7 ms | 880 × 1830 | M |
| Girth (plane section, convex-hull tape) | ≈ 0.9 ms per slice | MPFB default male: thigh 485 mm at z 700, calf 361 mm at z 350 | M |
| Workbench, first render in a process | 4.3–8.0 s | shader compilation; the server renders a warm-up frame at start | M |
| Workbench warm, equivalent crop camera | 0.7–2.3 s at 0.4–0.7 MP (head ×5 850²: 0.72–1.27 s; soldier ×1 440 × 915: 0.77–2.3 s over four runs); 1.6 s full frame with AA 8; 2.5 s soldier ×2 | AA: OFF/FXAA 1.02 s, 5 → 1.32 s, 8 → 1.16 s, 16 → 1.88 s on the soldier ×1 | M |
| Workbench with a render border at ×5 | 14.9 s (25.3 s cold) | the enlarged full frame is rendered, then cropped (D1) | M |
| Six Workbench variants in one process | 13.4 s (2.2 s each, border path) | the equivalent camera brings this to ≈ 7 s | M, E |
| Server round trip (TCP JSON line, 127.0.0.1) | ping 0.08 ms; set key + measure 200 landmarks 9.8 ms; Workbench soldier ×1 1.2–2.3 s warm | listening ≈ 1.3 s after launch with the MPFB file open; the first render adds 4–8 s | M |
| Cycles CPU throughput | ≈ 1 MP·spp/s shared, ≈ 2 idle; SSS ≈ 3×, hair ≈ 3× per 40 k strands, adaptive displacement 3–5× | research C recommendations | S |
| Cycles part closeup 800 × 800, 48–64 spp | 20–60 s | research C, prototypes §7 | S |
| Cloth: 3.1 k-vertex tube, 60 frames | 10.4 s | trousers 13.7 k vertices, 100 frames: 1–2 min (spec 09 budgets 2–4 min) | S, D 09 |
| `object.bake` 512², 4 spp | 0.4 s | bake cost ≈ render cost at the texel count | S |
| glTF export of a small rig / reimport | 0.32 s / 0.2 s | research C §7 | S |
| MPFB character build, no render | 7.5 s | research B | S |

On Jeff's workstation (Windows 11, 8 threads, NVIDIA GeForce RTX 3050 6 GB, Cycles on OptiX; measured 2026-10-10 with two agents working beside it, so a little noisy):

| Operation | Cost | Notes | Tag |
|---|---|---|---|
| Cycles test 1 (`test_01_cycles_bench.py`, 1920 × 1080, OIDN) | 4.1 s at 32 spp, 11.4 s at 128, 40.6 s at 512 | ≈ 0.076 s per sample, ≈ 27 MP·spp/s; the cloud took 68–91 s at 32 spp and never finished 128 | M |
| The same with OIDN on the CPU (Blender's default) | 15.3 s at 32 spp | the denoiser alone ≈ 11 s; `lib/env.py` `use_device()` puts it on the GPU | M |
| The same on the CPU, 8 threads | 45.4 s at 32 spp | | M |
| A re-render with `render.use_persistent_data` | 2.6 s against 3.2 s (32 spp, no denoiser) | keeps the scene on the device between renders in one process | M |
| 960 × 540, 32 spp, GPU denoiser, persistent data | 0.75 s | the size of most closeups | M |
| First Cycles render in a process | + ≈ 2 s | kernel load (smoke test: 4.3 s cold, 2.1 s warm, 480², 32 spp) | M |
| Workbench 480², MPFB human; MPFB enable; `create_human` | 1.3–1.8 s; 0.1 s; 0.4–0.5 s | `scripts/setup/smoke.py` | M |

### 3.3 Setup time and bytes (from the component sizes; downloads at the measured 9 MB/s for large files, 2.7 MB/s aggregate for the manifest's many small files)

| Step | Download | Disk after | Time | Tag |
|---|---|---|---|---|
| Blender 4.5.14 (Linux) | 378 MB | 1.2 GB (archive deleted after extraction) | 45 s + 30 s extraction | S size, E time |
| MPFB + 11 packs | 598 MB | 573 MB zips kept + 620 MB data + 84 MB extension | 70–120 s + 7 s unzip + 10 s install | S research B §6 |
| Manifest restore | 713 MB | ≈ 1.1 GB | 3–5 min sequential; ≈ 2 min with 4 parallel downloads | S research A §1, E |
| AI keepers (venv + MediaPipe + u2net) | ≈ 410 MB | ≈ 1.4 GB | ≈ 60 s pip + 25 s models | S research E §1, E |
| Depth Anything (`--with-depth`) | ≈ 320 MB | ≈ 1.0 GB | ≈ 50 s pip + 12 s model | S, E |
| Godot 4.7.2 headless (`--with-godot`) | 78 MB | 180 MB | 10 s | S |
| Smoke test (`--check`) | — | — | ≈ 12 s | E |
| **Total, default (`--ai`)** | **≈ 2.1 GB** | **≈ 5.0 GB** | **≈ 10–14 min** | E |
| Re-run with everything present | 0 | — | ≤ 30 s (hash checks are skipped for files whose size and mtime match the `.ok` stamp) | E |

Free disk on the cloud box is ≈ 21 GB (M, `df`), so a full setup plus caches (≈ 2 GB, §4.5) and renders fits with room for the second agent.

### 3.4 Formats and engine facts the export must satisfy

| Item | Fact | Tag |
|---|---|---|
| glTF 2.0 frame | metres, right-handed, +Y up; an asset's front faces +Z | S (Khronos glTF 2.0 §3.4) |
| Character facing in Godot | the hexcom convention is model forward = Godot −Z, so the export wrapper turns the character 180° about Blender Z before the Y-up conversion | D 08 §7.6, S summary.md |
| Skinning | `JOINTS_0`/`WEIGHTS_0`, 4 influences per set, normalised; inverse bind matrices from the rest pose | S glTF 2.0 |
| PBR textures | `baseColorTexture` sRGB; `metallicRoughnessTexture` linear, roughness in G, metalness in B; `occlusionTexture` R; `normalTexture` tangent space, +X right, +Y up (OpenGL convention), +Z toward the viewer; `emissiveTexture` sRGB; PNG or JPEG | S glTF 2.0 §3.9 |
| Blender exporter | `export_apply=False` keeps shape keys; modifiers are applied per shape key beforehand (spec 08 `apply_modifiers_keep_shapes`); `export_format='GLTF_SEPARATE'` writes `.gltf`, `.bin` and image files; property names verified on 4.5.14 | D 08 §3.3, §7.6 |
| Godot 4.7 import | glTF via the scene importer; `Skeleton3D` from the skin; humanoid retarget through a `BoneMap` with `SkeletonProfileHumanoid` (56 profile bones); automatic LOD generation on import (`meshes/generate_lods`); shadow meshes; 8-weight import only with the importer's 8-weight option | S Godot 4.x docs, D 08 §3.3 [VERIFY 4.7 option names] |
| Godot headless import | `godot --headless --path <project> --import` imports and quits (4.3 and later) | S Godot docs [VERIFY on 4.7.2] |
| hexcom rules | standing man 1.80 m with the eye at 1.65 m; crouch 1.25 / 1.10; prone 0.45 / 0.35; one world unit = one metre | S summary.md |
| GitHub | files over 100 MB are refused, over 50 MB warned; repositories should stay under 1 GB (5 GB at most); Git LFS stores large files outside the history with plan-dependent storage and bandwidth quotas | S docs.github.com [VERIFY Jeff's LFS quota] |
| Current repository | hexcom `.git` 90 MB; the project's `ref/` alone is 80 MB (209 tracked files) | M |

### 3.5 Budgets that are not technical

| Budget | Value | Consequence | Tag |
|---|---|---|---|
| API window | 5-hour session windows inside Jeff's Claude Max 5x weekly limit, shared with his own work; about 20 % must remain on Monday morning; weekends are the project's window | plan work in window-sized tasks (§9.5) | S summary.md |
| Concurrency | at most two agents at once | two parallel tracks in the build order (§9.2); critics run one at a time (§8.1.6) | S session_log.md |
| Context cost | 82–93 % of usage ran above 150 k context; short fresh sessions are far cheaper per unit of work | one task per session; restart rather than continue past a few jobs; keep docs short | S summary.md |
| Measuring cost | read the usage meter before and after one job, then extrapolate | `scripts/tools/meter.sh` wraps the `HEXCOM_USAGE_URL` call where the token exists (Jeff's machine; never committed) | S summary.md |
| CPU | 4 cores shared by both agents | one Cycles render at a time; `threads 3` while the other agent works (spec 17 §4.9) | S research C, D 17 |

---

## 4. Construction plan (the pipeline, in build order)

### 4.1 Repository layout (`$PROJECT_DIR` = `art/characters/sgt_morgan/` in hexcom; T = tracked, I = ignored)

```
CLAUDE.md                       T  conventions; read first
.gitignore  .gitattributes      T  §4.1.1, §4.1.2
ref/                            T  reference, crops, zooms (read-only; new zooms only when a spec cites them)
spec/                           T  00_overview.md, 01–18 part specs
notes/                          T  analysis and research notes; session_log.md (newest first)
assets/                         I  downloads: textures/ hdri/ models/ mpfb/ ai/ dimensions/
assets/manifest.json            T  texture, HDRI and model manifest (research A; sha256 added, §4.2.3)
assets/interfaces.json          T  the contract between parts (D9, §4.3)
scripts/setup_session.sh        T  §4.2.2
scripts/setup/                  T  fetch.py, downloads.json, mpfb_install.py, smoke.py,
                                   requirements-ai.txt, requirements-depth.txt
scripts/lib/                    T  shared Blender-side modules (bpy + numpy only), §4.3
scripts/parts/                  T  NN_name.py, one per part; pNN/ for part-private modules and params.json
scripts/server/                 T  blender_server.py (runs inside Blender), protocol.py
scripts/tools/                  T  bl.py (server client and CLI), sheet.py, imgdiff.py, repo_budget.py,
                                   meter.sh, make_rigify.py (spec 08)
scripts/eval/                   T  spec 17's scene, camera, render, colour, grade, overlay, masks, calibrate,
                                   deliver; presets/*.json; patches.json, landmarks.json, ui_mask.json,
                                   declared_diffs.json; metrics/ and critic/ (this spec, §8)
scripts/export/                 T  export_game.py (spec 08 §7.6, moved here), bake_atlases.py, lod.py,
                                   hair_cards.py, validate.py, godot_check/ (a tiny GDScript project)
scripts/build_all.py            T  §4.6
scripts/research/               T  research and probe scripts (history; not imported by the build)
scripts/workflows/              T  Workflow scripts that run agents two at a time
cache/                          I  everything rebuildable: blender_user/, env.json, env.sh, parts/, body/,
                                   sim/, generated/, bake/, server/, stamps/, tools/, build_state.json
renders/                        I  per-part outputs, opt/ logs, critic packets
renders/eval/log.md, log.jsonl  T  the evaluation log (§8.3)
renders/eval/NN_*.jpg           T  milestone images only (D12)
deliver/                        T  deliverables, committed at milestones (§4.10.2); deliver/tmp/ is I
```

#### 4.1.1 `.gitignore` (replaces the present file)
```
# downloads are restored by scripts/setup_session.sh
assets/*
!assets/manifest.json
!assets/interfaces.json
!assets/README.md
# everything rebuildable (per-part caches, Blender user resources, bakes, server state)
cache/
# renders: only the evaluation log and the milestone images are kept
renders/*
!renders/eval/
renders/eval/*
!renders/eval/log.md
!renders/eval/log.jsonl
!renders/eval/*.jpg
# deliverables are tracked; scratch output is not
deliver/tmp/
*.blend1
*.blend2
__pycache__/
*.pyc
.venv/
```

#### 4.1.2 `.gitattributes` (new)
```
* text=auto eol=lf
*.sh  text eol=lf
*.py  text eol=lf
*.png -text
*.jpg -text
*.exr -text
*.blend -text
*.glb -text
*.bin -text
*.npz -text
```
LF everywhere keeps `setup_session.sh` runnable in Git Bash (a CRLF checkout breaks bash on `\r`). Git LFS patterns are added to this file only after Jeff agrees (§4.10.4).

### 4.2 Setup (`scripts/setup_session.sh` and `scripts/setup/`)

#### 4.2.1 Behaviour
* One command on both platforms; idempotent; resumable (`curl -C -`, size check, then hash); every download verified (SHA-256; SHA-512 for Godot); nothing written outside the project directory except Blender itself (`/opt/blender` on the cloud, `%LOCALAPPDATA%\sgt_morgan` on Windows when no Blender 4.5 is installed).
* **Blender's user resources are redirected** with `BLENDER_USER_RESOURCES=cache/blender_user` for every pipeline call (M: MPFB 2.0.17 installs there in 2.8 s, and its user data directory becomes `cache/blender_user/extensions/.user/user_default/mpfb/data`). Jeff's own Blender preferences and add-ons are never touched, and deleting `cache/` is a clean slate.
* Options: `--no-ai`, `--with-depth`, `--with-3ddfa`, `--with-godot`, `--no-assets`, `--prune` (deletes research leftovers, research E §9), `--check` (smoke test). Default = Blender + MPFB + packs + manifest + AI keepers.
* Writes `cache/env.json` and `cache/env.sh` (Blender path, user-resources path, the image-tools Python, the AI venv Python, Godot path, OS, thread count), which every launcher reads (`scripts/lib/env.py`, `scripts/tools/bl.py`).

#### 4.2.2 `scripts/setup_session.sh`
The script is the authority; it was listed here in full until the first Windows run (2026-10-10) changed it, and a second copy would only drift. Its steps, in order:
1. **Blender 4.5.14.** `SGT_BLENDER` if set. Linux: `/opt/blender` as root, else `~/.local/opt`, downloaded and verified (§3.1) if absent. Windows: the installed `C:\Program Files\Blender Foundation\Blender 4.5\blender.exe` first, else a portable copy in `%LOCALAPPDATA%\sgt_morgan` from the verified zip. Another 4.5 patch release is accepted with a warning; the project was measured on 4.5.14.
2. **The setup Python**: `python3` on Linux, Blender's bundled Python on Windows (standard library only, D13).
3. **The Cycles device**: `scripts/setup/gpu_probe.py` asks Cycles for OptiX, CUDA, HIP, oneAPI and Metal devices in that order; the first back end with a GPU (else CPU) goes into `cache/env.json` as `device`. `lib/env.py` `use_device(scene)` applies it, `SGT_DEVICE` overrides it.
4. **MPFB 2.0.17 and the 11 packs**: `fetch.py list --group mpfb`, then `mpfb_install.py`, run without `--factory-startup` because it saves preferences (the project's own, in `cache/blender_user`).
5. **The manifest** (`--no-assets` skips): `fetch.py manifest`.
6. **AI helpers** (`--no-ai` skips): the venv from `requirements-ai.txt` (and `requirements-depth.txt` with `--with-depth`), the models of `downloads.json` groups `ai` (and `depth`), 3DDFA with `--with-3ddfa`.
7. **The image-tools Python** (PIL and numpy): `python3` if it has both, else the AI venv, else a project `.venv`.
8. **Godot 4.7.2** with `--with-godot`: downloaded on Linux; on Windows Jeff's WinGet install is found, never downloaded.
9. `--prune`; then `fetch.py env` writes `cache/env.json` and `cache/env.sh`; then `--check`: `scripts/setup/smoke.py` (an MPFB human, one Workbench and one Cycles render, timings in `cache/stamps/smoke.json`), `bl.py selftest` once `scripts/tools/bl.py` exists, and the AI imports.

First run on Jeff's machine (2026-10-10, `--with-godot --check`): 469 s, most of it the downloads (MPFB and packs 598 MB at 0.4–4 MB/s from the MakeHuman server, the manifest 713 MB, the venv wheels); the MPFB install 16 s; the smoke test 8 s (Workbench 1.3–1.8 s, Cycles OptiX 32 spp at 480 px 2.1 s warm, 4.3 s with the first kernel load). A re-run with everything present: 33 s, including the 180 MB of AI models the first run missed (§4.2.4, `GROUPS`). Disk: `assets/` 2.6 GB (venv 0.73 GB, textures 1.1 GB, MPFB zips 0.57 GB), `cache/blender_user` 0.70 GB.

Every other entry point starts with `source cache/env.sh` (bash) or `lib/env.py` (Python), which export `BLENDER_USER_RESOURCES`; an agent who runs Blender by hand uses `scripts/tools/bl.py blender -- <args>` so the redirect is never forgotten.

#### 4.2.3 `scripts/setup/fetch.py` and `scripts/setup/downloads.json`
`fetch.py` is standard-library only (so it runs on Blender's Python on Windows, D13) and has three subcommands. `list` downloads the entries of `downloads.json` for the named groups, four at a time, resumable (HTTP Range), verified by size and SHA-256 (or SHA-512), extracting zips with path-traversal checks into `dest` and writing a stamp `cache/stamps/<sha12>.ok` holding size and mtime so that re-runs skip hashing. `manifest` does the same for `assets/manifest.json` (it replaces `build_manifest.py --restore`, which stays as the manifest builder): md5 where Poly Haven published one, sha256 elsewhere; `--record-hashes` computes sha256 for the 28 files that have only a size (the ambientCG zips and the cgbookcase and OpenGameArt archives) once, from the verified copy on this box, and writes manifest schema 3, which is committed. `env` writes `cache/env.json` and `cache/env.sh`. TLS uses the platform store (Windows) or `SSL_CERT_FILE` when set (the cloud proxy's CA bundle).

`downloads.json` entries (`{group, url, mirror, bytes, sha256|sha512, dest, extract}`):

| Group | File | Bytes | sha256 |
|---|---|---|---|
| mpfb | `add-on-mpfb-v2.0.17.zip` | 45,031,536 | `4f0a879d64a39bf646fbf5f53601ac678855da329d650617dca5737548239a87` |
| mpfb | `makehuman_system_assets_cc0.zip` | 280,737,770 | `b542127a8e25547c7c29c19f2d1d2adb9a664c80396ecd694095dbc8028a0107` |
| mpfb | `skins02_cc0.zip` | 76,112,708 | `1613f1ef3afca53094511d26620ed7cf1d2dedc29ed3d384d60bdebe250698ae` |
| mpfb | `shoes01_cc0.zip` | 82,953,569 | `ded3f70428505eabbf1f6d7b5f61196a7366ef20757103d276ad0ed336c35ada` |
| mpfb | `shirts01_cc0.zip` | 24,479,483 | `a5a723b0e84a109bb190fcfeac7f1de4138d875da3e30fe5b3340eac9f38bcd3` |
| mpfb | `hats02_cc0.zip` | 24,018,546 | `838b9b51ba31d27f21198ad4506eb9b23e1c03eb246fe68f26da99e26b40e1aa` |
| mpfb | `pants01_cc0.zip` | 21,908,723 | `e4e0ec60db34f279be291a83cfd7b342a7c5cf09bb7676682a5f39f4f6ac4ad9` |
| mpfb | `equipment01_cc0.zip` | 18,111,388 | `d8afa9d98c52f0a5e92a0d3e9f691f5699dd878499d9f6681740d38ca2640236` |
| mpfb | `eyebrows01_cc0.zip` | 11,477,790 | `5425891dce613bef85c7117f7843cd49d57d1fb28127e76d77d2a2eaccb4fe78` |
| mpfb | `bodyparts05_cc0.zip` | 6,616,507 | `262bba42246f85b2a91f493dd920296b258a3b4544eb495c91c4d08e57c528fd` |
| mpfb | `eyelashes01_cc0.zip` | 3,493,692 | `b7b5eb97cfb930d93e8c067885801443bcab2dcbbe6c2c2cfff7ad87992077e8` |
| mpfb | `gloves01_cc0.zip` | 3,192,691 | `ecdaee1d02749d17352791d415cb622a883350cc8a4b90eda3725aef35d9afb2` |
| ai | `face_landmarker.task` | 3,758,596 | `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff` |
| ai | `canonical_face_model.obj` | 45,999 | `8bac80443397e113f41a8b565ea72c59390bc031d9defab289dba7bc0c54e618` |
| ai | `u2net.onnx` | 175,997,641 | `8d10d2f3bb75ae3b6d527c77944fc5e7dcd94b29809d47a739a7a728a912b491` |
| depth | `model.safetensors` (+ `config.json` 950 B, `preprocessor_config.json` 775 B) | 99,173,660 | `3152477ce0d8d6978d76b995120de97cb5b928701fd0f817769f59e249a16b70` |
| godot | `Godot_v4.7.2-stable_linux.x86_64.zip` | 77,860,424 | sha512 `9aa00f7a…ed54c65` (§3.1) |

Pack hashes were computed on this box from the copies whose sizes research B verified against the server (M). `requirements-ai.txt`: `mediapipe==0.10.35`, `opencv-python-headless`, `pillow==12.3.0`, `numpy`, `rembg==2.0.85`, `onnxruntime==1.30.0`. `requirements-depth.txt`: `--index-url https://download.pytorch.org/whl/cpu`, `--extra-index-url https://pypi.org/simple`, `torch==2.14.1`, `torchvision==0.29.1`, `transformers==5.18.0`, `safetensors`, `accelerate` (research E §1, minus the dropped `diffusers`, `trimesh`, `xatlas`).

`mpfb_install.py` (Blender side, replacing the research copy): installs the extension with `bpy.ops.extensions.package_install_files(repo="user_default", enable_on_install=True)` if `blender_manifest.toml` is absent, enables `bl_ext.user_default.mpfb`, saves preferences (inside `cache/blender_user`), extracts each pack zip into `LocationService.get_user_data()` unless `packs/<name>.json` exists, and writes a report with `AssetService.system_assets_pack_is_installed()` and the pack names; non-zero exit on failure.

#### 4.2.4 Windows notes (Git Bash), verified on Jeff's machine on 2026-10-10
Windows 11, Git Bash, Blender 4.5.14 (MSI install), NVIDIA GeForce RTX 3050 6 GB.
* **Blender**: the MSI install was 4.5.0; Jeff chose to upgrade it rather than keep a portable copy beside it. The 4.5.14 MSI from download.blender.org (359,874,560 bytes, sha256 `5e04b3f587250d611bdd40d41fd9e3f75207a44e7d554d495dfe81ff6345937c`, from the release's `.sha256` file) upgrades an installed 4.5 in place (`msiexec /i … /passive`, one UAC prompt). `winget upgrade` would jump to the newest series (5.2.2 that day), not the newest 4.5.
* **Line endings**: Git for Windows sets `core.autocrlf=true` in its system config, so without `.gitattributes` every text file checks out with CRLF and bash stops on `\r`. The project's `.gitattributes` (§4.1.2) forces LF; a checkout made before it existed keeps its CRLF files until they are deleted and checked out again (only clean files: `git status` first).
* **Logs**: `tee /dev/stderr` reopens the file that stdout and stderr are redirected to and truncates it; the script captures the probe's output in a variable instead.
* `python3` on a stock Windows is the Microsoft Store alias and fails; the setup Python is Blender's (3.11.15, OpenSSL 3.1.8, which reads the Windows certificate store), and the image-tools Python is the AI venv.
* Paths handed to `blender.exe`, `tar.exe` or Python are converted with `cygpath -w`; paths inside the scripts are POSIX.
* Long paths: `LongPathsEnabled` is 1 on Jeff's machine; MPFB's data extracts under `cache\blender_user\extensions\.user\user_default\mpfb\data` without trouble from `E:\hexcom`.
* **GPU**: the probe finds OptiX and CUDA on the RTX 3050 and records OptiX. Scripts call `lib/env.py` `use_device(scene)`, which enables the GPUs of that back end and leaves the CPU out; `SGT_DEVICE` (`OPTIX`, `CUDA`, `HIP`, `ONEAPI`, `METAL` or `CPU`) overrides it.
* **Denoiser**: Blender's default runs OIDN on the CPU even in a GPU render; on the RTX 3050 that was 11 of the 15 s of test 1's 1080p 32-spp frame. `use_device()` sets `denoising_use_gpu`, which brings the frame to 4.1 s (§3.2, last table).
* **AI venv**: made by Blender's Python 3.11.15; the pinned `win_amd64` wheels installed (mediapipe 0.10.35, onnxruntime 1.30.0, rembg 2.0.85, pillow 12.3.0; numpy resolved to 2.4.6, scipy 1.17.1, numba 0.68.0), 0.73 GB.
* **`GROUPS` is a bash built-in** (the user's group ids, an array that ignores assignment): the script as first specified set `GROUPS=ai`, so its first run fetched no AI models and still exited 0 (`197121: 0 of 0 files verified`). The variable is `AI_GROUPS`.

### 4.3 The shared library (`scripts/lib/`)
Blender-side modules import only `bpy`, `bmesh`, `mathutils` and `numpy` (Blender 4.5 ships numpy 1.26.4, M). System-Python tools (PIL) live in `scripts/tools/` and `scripts/eval/` (spec 16's `texmeasure.py` and `decal.py` are the two exceptions it names). Every module has a `selftest()` run by `python scripts/tools/bl.py selftest --lib`.

| Module | Owner | Contents (signatures in mm unless stated) |
|---|---|---|
| `env.py` | 18 | project paths, `env.json`, `blender_cmd(args)` (sets `BLENDER_USER_RESOURCES`), `threads()` (`SGT_THREADS`), `device()`, the `sys.path` bootstrap |
| `cli.py` | 18 | the standard part interface of §4.4: `main(PART, build, measure)`; the `RESULT {json}` line; exit codes |
| `naming.py` | 18 | `name(part, side, *components)`; validation regex `^[A-Z][A-Za-z0-9]*(\.(L\|R\|C))?(\.[A-Za-z0-9_]+)*$`; `mirror_name()`; collection names `PartNN.<Name>` |
| `replace.py` | 18 | `part_scope(PART)` (deletes the part's objects, meshes, curves, materials, images and node groups by collection and prefix, then `orphans_purge(do_recursive=True)`); `new_object(name, data, coll)` refusing names outside the part's prefixes; `body_layer(PART)` (removes the part's own shape keys, vertex groups and attributes on `Body.Mesh` before re-adding) |
| `ctx.py` | 18 | research C's context rules: `set_active(ob)`, `mode(ob, 'EDIT')` as a context manager using real selection, `override(**kw)`, `apply_modifier(ob, name)` capturing names first |
| `modifiers.py` | 18 | `bevel(ob, width, segments, angle_deg, profile, harden)`, `subdiv(ob, levels, render_levels)`, `solidify(ob, thickness, offset, even, rim)` with the bounding-box assertion of the prototype trap, `weighted_normal`, `displace`, `shrinkwrap`, `smooth_by_angle`, `apply_keep_shapes(ob)` (spec 08's `apply_modifiers_keep_shapes`, moved here) |
| `sweep.py` | 18 | straps and laces: `surface_path(target, points, standoff, step)` (BVH projection), `rmf_frames(path)` (rotation-minimising), `strip(path, width, thickness, quads_across, twist_deg, sag, seed)`, `tube(path, radius, sides)`, `fold_end(strip, length)`, `thread(path, hardware, slots)` |
| `boolean.py` | 18 | `difference/union(target, cutters, solver='EXACT')` one cutter at a time, `assert_manifold`, `volume`, expected-volume check ±2 %, `dissolve_degenerate`; spec 15's `hardsurf.py` builds on it |
| `uv.py` | 18 | `unwrap(ob, seams)`, `texel_density(ob, px) → px/mm per island`, `normalise_density(objs, px_per_mm)`, `pack(objs, size, margin_px)`, overlap check; densities from spec 16 §5.2 |
| `cache.py` | 18 | content keys, `save_part(PART)` via `bpy.data.libraries.write`, `load_part(PART, link)`, layer caches (`.npz`), atomic writes, the build journal |
| `params.py` | 18 | parameter registry: adapters for shape keys, MPFB macro and detail targets, modifier properties, Geometry Nodes inputs by identifier, transforms, part constants; `snapshot()` and `restore()` |
| `measure.py` | 18 | measurement primitives (§4.8.4) |
| `linmodel.py` | 18 | the linear target model (§4.8.4, §4.8.6) |
| `optim.py` | 18 | coordinate descent, CMA-ES, Levenberg–Marquardt, bounded linear least squares (§4.8.5) |
| `interfaces.py` | 18 | `assets/interfaces.json`: each part writes only keys under its own prefix (`torso.*`, `carrier.*`, `rifle.*`); readers declare the keys they read, so a change marks the readers stale |
| `log.py` | 18 | JSON-lines logs, timers |
| `render.py` | 17 | shim re-exporting `scripts/eval/render.py` and `camera.py` (spec 06's `render_harness.py` is an alias for one release) |
| `materials.py` and `mat_*.py` | 16 | the only material API parts import (spec 16 §7.2) |
| `sculpt.py` | 01 | `soft_inflate`, `soft_move`, `flatten_to_plane`, `soft_line` (04) |
| `proportions.py` | 03, 04 | the proportion solver, remap and re-loop |
| `corrective.py`, `weights.py` | 03 (08 owns the driver convention) | corrective keys, twist ramps |
| `rig.py`, `pose.py`, `rifle_place.py`, `attach.py` | 08 | `BONE_MAP` (absorbs `rig_names.py` of 04 and 06), frames, IK, bake, attachment |
| `grip.py` | 05 | hand frames, finger contact solve |
| `face_fit.py`, `face_landmarks.py` | 06 | the likeness loop; landmark vertex ids |
| `groom.py` | 07 | hair curves |
| `cloth_tube.py`, `camo_gen.py`, `gn_wrinkles.py`, `gn_stitches.py` | 09 | cloth helpers; `gn_stitches.py` absorbs spec 11's `stitch.py` |
| `gear_webbing.py`, `gear_hardware.py`, `gear_pouch.py` | 13 (shared by 02, 11, 12, 14, 15) | webbing, PALS, hardware, pouches |
| `armour.py` | 12 | shell lofts, slots, rims, rivets |
| `hardsurf.py`, `lathe.py`, `rail1913.py`, `mlok.py` | 15 | hard-surface helpers |
| `decal.py` | 16 (absorbs spec 12's `decals.py`) | stencil and decal masks with PIL |

Part-private modules move out of `lib/`: spec 02's `boot_*.py` and `measure_boot.py` become `scripts/parts/p02/`, spec 11's `glove_pattern.py` becomes `scripts/parts/p11/` (§10.2).

### 4.4 The part script standard (`scripts/parts/NN_name.py`)
```python
"""Part 02 — Boots. Spec: spec/02_boots.md. Builds Boot.L/R.* in collection Part02.Boots."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))   # scripts/
from lib import cli, replace, cache, measure, materials
from lib.cli import Part

PART = Part(
    id="02", name="boots", collection="Part02.Boots", prefixes=("Boot.",),
    needs={"01": "Foot.L.Last", "08": "Morgan.Rig", "17": "camera"},     # hard: must exist
    proxies={"01": "stand_in_last"},                                      # soft: a proxy may stand in
    provides=("Boot.L.ShaftProxy", "Boot.R.ShaftProxy"),
    stages=("last", "sole", "lugs", "upper", "overlays", "collar", "hardware", "strap",
            "laces", "stitches", "materials", "masks", "mirror", "weights", "proxy"),
    presets="p02", params="scripts/parts/p02/params.json")

def build(ctx, args):            # called by the CLI below, by build_all.py and by the server
    with replace.part_scope(PART) as scope:
        for stage in ctx.stages(args):   # honours --stage, --rebuild and the cache journal
            STAGES[stage](scope, ctx.params, args)
    cache.save_part(PART)

def measure(ctx, args) -> dict:  # fast, no render; tolerances from spec 02 §8.2
    return {"collar_h_mm": ..., "rim_ellipse_mm": [...], "lug_coverage": ...}

if __name__ == "__main__":
    cli.main(PART, build, measure)
```

| Argument | Meaning |
|---|---|
| `--rebuild` | ignore the part cache and rebuild every stage |
| `--stage S` / `--stage S1..S2` | run one stage or a range (earlier stages come from the cache) |
| `--render` | render the views after building |
| `--views V1,V4` | preset ids or labels from `presets/pNN.json` (default: all of the part's views) |
| `--quality form\|look\|eval\|cal\|final` | spec 17's render tier (default `form`) |
| `--params FILE\|JSON` | override parameters (merged over `pNN/params.json`) |
| `--seed N` | default 17 |
| `--proxy 01,13` | force stand-ins for the named dependencies |
| `--check` | build and measure, assert tolerances, save nothing |
| `--from-cache` | load `cache/parts/NN_name.blend` and only render or measure |
| `--json` | print `RESULT {...}` (status, timings, cache key, outputs, metrics) as the last line |

Rules: run as `blender -b --python-exit-code 1 --python scripts/parts/NN_name.py -- <args>` (the `--` separates Blender's arguments); exit 0 pass, 2 a tolerance failed, 3 a hard dependency is missing, 4 a Blender or Python error; every random draw takes `args.seed`; a script writes only inside its collection, under its prefixes, into `cache/parts/`, `cache/generated/NN/` and `renders/NN_name/`, and into its own keys of `assets/interfaces.json`; it never hand-edits a `.blend` (rule 5); the result of an optimiser is written back into `pNN/params.json` and committed, so the optimum becomes code.

### 4.5 Caches (`cache/`, all rebuildable, D5)

| Cache | Written by | Holds | Consumers | Size (E) |
|---|---|---|---|---|
| `cache/body/base.blend` | stage S1 | MPFB human after the proportion solve, remap and re-loop (specs 03, 04) | S2 | 15 MB |
| `cache/body/rigged.blend` + `bones.json` | S2 | `Body.Mesh` + `Morgan.Rig` after the rig fit (spec 08 steps 1–4) | every body and garment part | 20 MB |
| `cache/parts/NN_name.blend` + `.key.json` | each part | only the part's data-blocks, written with `bpy.data.libraries.write(path, datablocks, path_remap='RELATIVE_ALL', compress=False)` | assembly, neighbours, the server | 5–60 MB each |
| `cache/parts/NN_name.layer.npz` | body-region parts 01, 03, 04, 05, 06 (and 07's attributes) | the part's shape-key deltas, vertex-group weights and attributes on `Body.Mesh`, keyed by the body's topology hash (vertex count + sha256 of the face index array) | `cache.layer_apply()` re-applies a layer in milliseconds | 1–10 MB each |
| `cache/sim/NN_<garment>.blend` | S7 | simulated garments after `modifier_apply` | S8 | 10–30 MB |
| `cache/character_rest.blend`, `cache/character_hero.blend` | S11 | the `Character` collection, rest-posed skinned and hero-posed | spec 17 (`scene.py` links the hero), export | 150–400 MB |
| `cache/generated/NN/` | parts | generated textures and masks (camo tile, honeycomb, decal masks, emblem) — replaces `assets/generated/` | parts, export | 50–200 MB |
| `cache/bake/<Atlas>_<Channel>.png` | S13 | export bakes (spec 16 §5.4) — replaces `assets/build/bake/` | export | ≈ 600 MB |
| `cache/server/` | the server | state files, snapshots, logs | `bl.py` | small |
| `cache/build_state.json` | `build_all.py` | the journal | `build_all.py` | small |

**Cache key** (`cache.key()`): sha256 over the part script, every module under `scripts/` that the last build imported (the list is recorded in `.key.json`), the canonical JSON of its parameters, the seed, the keys of its hard dependencies (a proxy contributes `proxy:<name>@<version>`), the manifest entries it read, the Blender version and the MPFB version. A part is stale when the recomputed key differs from the stored one; `build_all.py --dry-run` prints the reason (which input changed).

### 4.6 `scripts/build_all.py` — assemble, fit, pose, simulate, bake, evaluate, export

| Stage | Specs | Does | Output | Time on 4 cores |
|---|---|---|---|---|
| S0 `env` | 18 | checks `cache/env.json`, versions, free disk ≥ 5 GB | — | 2 s |
| S1 `body.base` | 03, 04 | MPFB human, macro and detail targets, proportion solver, bake, remap, flank re-loop | `cache/body/base.blend` | ≈ 20 s (D 04 §9.2) |
| S2 `rig.fit` | 08 (05 joint fix, 03 patella) | rig fit, added bones, rolls, weight clean-up, `bones.json` | `cache/body/rigged.blend` | ≈ 5 s (D 08 §9) |
| S3 `body.regions` | 04 → 03 → 01 → 05 → 06 | region sculpts, relief and mask bakes, nails, eyes, teeth, the foot last | layer caches + part blends | ≈ 2 min + bakes (06: 20 min per geometry change) |
| S4 `parts.rest` | 15 (frames first), 02, 13, 12, 14, 11, 10, 09, 07 | every part built on the rest body (garment tubes and lofts, shells, hardware, groom) | `cache/parts/*` | ≈ 15 min + mask bakes |
| S5 `weights.rest` | 08 §6 step 2 | weight transfer for skinned garments, overrides, `finalize_weights` | in place | ≈ 30 s |
| S6 `pose` | 08 §4.7–4.9 | rifle two-pin solve against `Vest.Collider`, arm IK, finger contact solve, bake to `Hero.Pose` | `cache/body/posed.blend` | ≈ 10 s |
| S7 `simulate` | 09, 10 | trousers (100 frames), sleeves, gaiter relax; stability checks | `cache/sim/*.blend` | ≈ 5 min (D 09, 10) |
| S8 `bake.cloth` | 08 §6 step 5 | apply, detail passes, `SurfaceDeform` binds to `Body.Mesh.Posed` | in place | ≈ 30 s |
| S9 `attach` | 08 §7, 11, 12, 13, 14 | gear on the posed body, compressions, glove push-out, strap bite checks | in place | ≈ 30 s |
| S10 `materials` | 16 | recipes assigned, `materials.lint()`, wear masks | in place | 1–3 min |
| S11 `assemble` | 18 | `Character` collection; hero and rest assemblies | `cache/character_{hero,rest}.blend` | ≈ 20 s |
| S12 `evaluate` | 17, 18 | links the character into spec 17's scene; renders the requested parts' presets at the requested tier; metrics; packets | `renders/` | `form`: ≈ 2 min for all parts; `eval`: per part, §9.4 |
| S13 `export` | 08 §7.6, 16 §5.4, 18 §4.10 | export copies, atlas bakes, LODs, glTF, validation | `deliver/` (staged in `cache/deliver_stage/`) | 15–30 min + bakes (1.5–2 h CPU, minutes on the GPU) |

From an empty cache to `--to assemble`: ≈ 25 min of CPU plus the one-off bakes (E, from the specs' own run times). Flags: `--from S`, `--to S`, `--only S`, `--parts 02,09`, `--force`, `--dry-run`, `--proxy-missing` (use declared proxies for absent dependencies and say so in the log), `--jobs 1|2` (independent parts of S3 and S4 in two processes; never while the other agent renders), `--quality` (S12 tier), `--server NAME` (run stages inside a warm server instead of fresh processes).

**Built so far (2026-10-10), in cut-down form:** S0, S1 and S2. S1 sets MPFB's macros from specs 03 and 04, fits the height macro to the rest stature 1855 mm (measured 1855.2), re-grounds the lowest vertex at z 0 and centres the ankle joints on the origin, facing −Y; no proportion solver, remap or re-loop yet, so the hip joint stands at 998 against 963 and the knee at 537 against 526. S2 adds MPFB's `default` rig (163 bones) with its own weights, the armature modifier after the helper mask; no added bones, rolls or weight clean-up yet. S0 to S2 take 5.3 s; a re-run with nothing changed skips both in 0.6 s. Every later stage exits 5, "not built yet". MPFB's head bone ends at z 1862, above the skull, where spec 08 §4.1 expects 1835 (spec 08's own §3.4 dump shows MPFB's value); settle it when the rig fit is built.

Process model: each stage runs in a fresh Blender process that opens the previous stage's output (`blender -b <input> --python-exit-code 1 --python scripts/build_all.py -- --exec S`); a cold start costs 2.2 s and an open 0.05–0.5 s (M), which buys isolation from memory growth and from a crash in one part.

### 4.7 Idempotency and resumability rules
1. A part script deletes and recreates only its own data-blocks (`replace.part_scope`); running it twice gives the same objects with the same names and the same mesh hash.
2. Layers on the shared `Body.Mesh` are removed by prefix before they are re-added (`replace.body_layer`); MPFB's own groups and keys are never touched.
3. Every write is atomic: write `*.tmp`, then `os.replace`. A killed process leaves either the old file or the new one.
4. The journal records `running` before a stage and `done` with its outputs after; a stage found `running` is re-run from its input cache.
5. A missing hard dependency is exit 3 with the missing name, never a silent default; a soft dependency uses its declared proxy and the log and the RESULT line say "proxy".
6. Seeds: one `--seed` (default 17) feeds every random generator; Cycles `seed 17`, `use_animated_seed False` (spec 17).
7. Cloth is stepped frame by frame in one process with fixed substeps (research C §2), so a re-run reproduces the drape.
8. Determinism is tested: `build_all.py --verify` rebuilds into a scratch cache and compares mesh hashes (coordinates rounded to 0.01 mm) object by object.
9. Nothing outside `cache/`, `renders/`, `deliver/` and the part's own keys of `assets/interfaces.json` is written by a build.
10. Parameters changed by an optimiser or a session are written to `scripts/parts/pNN/params.json` and committed with the script; the `.blend` is never the record.

### 4.8 The fast feedback loop

#### 4.8.1 The persistent Blender server (`scripts/server/blender_server.py`, client `scripts/tools/bl.py`)
* **Start**: `python3 -I scripts/tools/bl.py start --name a --blend cache/body/rigged.blend [--parts 05,15]` launches `blender -b <blend> --python scripts/server/blender_server.py -- --name a --port 0` with `BLENDER_USER_RESOURCES` set, waits for the `LISTENING <port>` line (≈ 1.3 s after launch with the MPFB file open, M), renders one Workbench warm-up frame (the first render costs 4–8 s of shader compilation, M), and writes `cache/server/a.json` (pid, port, token, started, blend). One server per agent; names `a` and `b` for the two agents.
* **Transport**: JSON lines over TCP on 127.0.0.1 (ping 0.08 ms, M). A request is `{"id", "token", "cmd", "args"}`, a reply `{"id", "ok", "result" | "error", "ms"}`. With `--transport files` the same messages go through `cache/server/a/in/*.json` → `out/*.json` polled every 20 ms, for machines where a listening socket is refused.
* **Commands**

| Command | Does | Typical cost |
|---|---|---|
| `ping`, `status` | liveness; memory, loaded parts, object counts, uptime | < 1 ms |
| `load {part, link}` | appends or links `cache/parts/NN_name.blend`; applies layer caches | 0.05–1 s |
| `build {part, stage, params}` | `importlib.reload` of every changed module under `scripts/` (by mtime), then the part's `build()` in the live session | stage-dependent; seconds for most |
| `set {name: value}` / `get [names]` | the parameter registry (`lib/params.py`) | < 1 ms (+ depsgraph on the next measure) |
| `measure {part \| fn, args}` | the part's `measure()` or a `lib/measure.py` primitive | 1–20 ms |
| `silhouette {preset, objects}` | mesh splat and IoU against the reference mask | 0.1–0.45 s |
| `render {preset, tier, out}` | spec 17 `render.py` with the equivalent crop camera | `form` 0.7–2.5 s warm |
| `variants {base, list \| grid, measure, render}` | for each variant: set, measure, optionally render, restore; returns metrics and file names | n × (measure + render) |
| `optimise {method, params, bounds, objective, budget}` | runs §4.8.5 in the session; streams progress lines | seconds to minutes |
| `snapshot` / `restore {k}` | saves the session to `cache/server/a_snap_k.blend`, re-opens it | 0.02 s / 0.05 s for 12 MB (M) |
| `save {part}` | `cache.save_part()` | < 1 s |
| `exec {code}` | runs a Python snippet in the session (debugging only; logged; requires the token) | — |
| `shutdown` | clean exit | — |

* **Hygiene**: after each `build`, `orphans_purge`; the server restarts itself after 200 builds or when its resident memory passes 5 GB (two servers fit in 15 GB with Cycles headroom); a crash is recovered by `bl.py` restarting from the last snapshot. The server is single-threaded: Blender operators run on its main thread, so commands queue rather than overlap.

#### 4.8.2 Workbench form renders and the equivalent crop camera
Form checks use spec 17's `form` tier: Workbench, `MATCAP` `clay_studio.exr`, single colour 0.8, cavity `BOTH` (ridge and valley 1.0), no shadows; anti-aliasing `FXAA` for variant sweeps (1.02 s) and `8` for critic packets (1.16 s) (M, soldier ×1). For a crop (x0, y0)–(x1, y1) of the 1672 × 941 hero frame at scale s, with w = x1 − x0 and h = y1 − y0, the camera keeps `Scene.Cam.Hero`'s position and rotation and sets

lens′ = 46 mm × 1672 / w; shift_x = ((x0 + x1)/2 − 836) / w; shift_y = (470.5 − (y0 + y1)/2) / w; resolution (w·s, h·s); `sensor_fit 'HORIZONTAL'`, sensor 36 mm.

Under horizontal sensor fit Blender's shift unit is the frame width even when the crop is taller than wide (M on the 440 × 915 soldier crop: alignment within 0.2 px, IoU 0.999 against the border render). `camera.py` (spec 17) adds this as the default resolution path for `hero` presets with a box; the border path remains for comparison.

#### 4.8.3 Contact sheets (`scripts/tools/sheet.py`, image-tools Python with PIL)
Input: the preset's reference crop (cut from `reference_full.png` at the preset's box and scale, so it always matches the render size), a list of variant images with their parameter deltas and metrics (`variants` output). Output: `renders/NN_name/sheets/<run>.png` and `.json`: cell 1 the reference with a cyan frame, then the variants sorted by the objective, each labelled with its parameter deltas (`jaw-scale-vert +0.08`) and up to three metrics (`IoU 0.913 · lm 3.1 px · ΔE 4.2`), the reference silhouette edge drawn 1 px cyan over every variant, cells downscaled to at most 420 px, sheet at most 2400 px wide (the Read tool shows it whole). A second mode writes a `pair` (reference | render) and an `onion` (50 %) for one variant. Cost ≈ 0.5 s for 12 cells (E).

#### 4.8.4 Measurement before rendering (`scripts/lib/measure.py`, `scripts/lib/linmodel.py`)

| Primitive | Returns | Cost | Tag |
|---|---|---|---|
| `landmarks(ob, spec)` | named points (vertex ids, vertex-group centroids or barycentric points) on the evaluated mesh, mm | 10.6 ms through the depsgraph | M |
| `linmodel.predict(w)` | the same landmarks for a vector of target weights | 5.4 µs (120 landmarks) | M |
| `project(points, preset)` | pixel coordinates through the hero or a crop camera | 0.3 ms per 13 k points | M |
| `girth(ob, plane, around, kind='tape'\|'loop')` | the section loop that encloses `around` (loops chained through face adjacency); `tape` = convex-hull perimeter (what a tape measure reads, the ANSUR convention), `loop` = true perimeter | ≈ 1 ms per slice | M (tape) |
| `section(ob, plane)` | section polygons for comparison with a spec's profile table | ≈ 1 ms | E |
| `clearance(a, b, max_mm)` | minimum gap and the count of interpenetrating vertices (`BVHTree.FromObject`, `find_nearest`, `overlap`) | 5–50 ms | E |
| `silhouette(objects, preset)` | boolean mask by splatting barycentric lattice samples of every projected triangle (step ≤ 0.7 px) and a 3 × 3 closing | 105 ms soldier ×1, 227 ms full frame | M |
| `iou(mask, ref, band=3, declared=True)` | IoU outside the ±3 px band and the declared-difference polygons; also precision and recall | 1.7 ms | M |
| `stature(ob)`, `bbox(ob)` | rest stature for the export scale (D7) | < 1 ms | E |

Every part's `measure()` returns the envelope `{"part", "metric", "value", "target", "tol", "unit", "pass", "source": "spec NN §x"}` per item, so the log and the critics read every part the same way. The linear target model is built once per session from the MPFB shape keys (2 ms per key, M) and is exact for detail targets; MPFB macro sliders are not linear in their slider values (each slider blends corner targets), so the model treats macro values as fixed during a fit and re-linearises after any macro change [VERIFY the cost of `reapply_macro_details` per call].

#### 4.8.5 Optimisers (`scripts/lib/optim.py`, numpy only, run inside Blender)

| Method | Use | Defaults | Budget |
|---|---|---|---|
| Coordinate descent | ≤ 8 smooth parameters (a part's dimension knobs) | cyclic, golden-section line search inside each parameter's bounds; stop when a cycle improves the objective by < 1e−4 or after 30 cycles | mesh-only objective: ≤ 2,000 evaluations |
| CMA-ES | 5–60 parameters, non-smooth objectives (silhouette IoU, combined scores), MPFB target searches | (μ/μ_w, λ) after Hansen's tutorial (arXiv 1604.00772); λ = 4 + ⌊3 ln n⌋; parameters normalised to [0, 1]; σ₀ = 0.25; bounds by reflection; seeded | mesh-only: ≤ 2,000; with a Workbench render per evaluation: ≤ 60 |
| Levenberg–Marquardt | residual fits (landmarks, girths) | Δp = −(JᵀWJ + μI)⁻¹JᵀWr; J exact from `linmodel` or by finite differences (Δ 0.1); μ ×3 on a worse step, ÷2 on a better; clamp ±0.15 per step; bounds by clamping | ≤ 30 iterations (spec 06's inner loop) |
| Bounded linear least squares | anything `linmodel` expresses exactly | min ‖W(Jw − b)‖² + λ‖w − w₀‖² subject to lo ≤ w ≤ hi; projected gradient with exact line search, then an active-set polish | milliseconds |

Objectives are named callables registered by the part (`scripts/parts/pNN/objectives.py`): f = Σ wₖ (rₖ / tolₖ)² over residuals whose targets and tolerances come from the spec tables, plus penalties for hard constraints (for example 100 × (gap / 1 mm)² for any interpenetration). Every evaluation is logged to `renders/NN_name/opt/<run>.jsonl`; the best parameters go to `pNN/params.json`; an `opt` event goes to the evaluation log. Rules: an optimiser never renders Cycles; Workbench in the loop only under CMA-ES with ≤ 60 evaluations; a result that moves a parameter to its bound is reported, not accepted silently.

Self-tests (§1.4 item 7): CMA-ES on 10-D Rosenbrock to 1e−6 within 6,000 evaluations; the bounded solver recovers synthetic weights (random J of 204 × 60, known w) to 1e−4; LM converges on a known 3-parameter similarity transform.

#### 4.8.6 Least-squares fit of MPFB target weights to the 3DDFA landmarks
The fit that seeds spec 06's likeness loop (research E §8 item 7, spec 06 §4 step 6):
1. **Data**: `assets/ai/face_3ddfa_lm68.json` (68 points with depth, image pixels of the ×5 crop) and the 68 ↔ MPFB vertex table owned by spec 06's `face_landmarks.py` (built once by running the detector on a frontal `form` render of the default head and casting each landmark's ray to the nearest visible vertex; frozen in `scripts/lib/data/lm68_mpfb.json`).
2. **Scale**: pixels to mm with the known span hair-top to menton (237 mm, spec 06).
3. **Model**: in the head's rest frame, p(w) = p₀ + J w for the landmark vertices, with w the 40–60 detail targets of spec 06 table 4.1; J exact from the shape keys (§4.8.4).
4. **Alternate** three to five times: (a) similarity alignment (Umeyama, no reflection) of the 3DDFA points onto p(w) using the stable set (exocanthi, endocanthi, nasion, subnasale, cheilions, menton); (b) bounded linear least squares for w with weights 1.0 on eyes, nose and mouth, 0.5 on depth (3DDFA's identity is a generic BFM face) and 0.5 on the jaw contour (the 68-point contour is view-dependent), λ = 0.1 toward the start values, bounds [−1, 1] ([0, 1] for one-sided targets). Each solve is 204 residuals by ≤ 60 unknowns: milliseconds.
5. **Hand-off**: w becomes the start of spec 06's Levenberg–Marquardt inner loop on the MediaPipe ratios; the depsgraph confirms (10 ms) and the outer gate renders the head crop in Workbench (≈ 1.3 s at ×5, M) and runs MediaPipe on it (0.4 s, S). No dense shrinkwrap to the 3DDFA mesh (research E).

#### 4.8.7 Cycles is for acceptance only
`look` (16 spp, 50 %) may be used to see a shader during look-development; `eval` renders feed critic packets and per-part acceptance; `cal` is spec 17's light calibration; `final` runs only on the GPU machine. No Cycles render inside an optimiser, a variant sweep or a contact sheet of form variants. One Cycles render at a time on the cloud box, `threads 3` while the other agent works (spec 17 §4.9).

#### 4.8.8 One loop, end to end (the spec 06 jaw, as an example)
`bl.py start --blend cache/body/rigged.blend --parts 06` (≈ 1.3 s, plus the 4–8 s warm-up render once per session) → `optimise {cmaes, 6 jaw targets, objective: projected-landmark ratios + head silhouette IoU, budget 300}` (300 × ≈ 0.12 s ≈ 40 s) → `variants {the best 12}` with `form` renders of `ref.head_face` (12 × 1.3 s ≈ 16 s) → `sheet.py` (0.5 s) → the agent reads the sheet → MediaPipe gate on the chosen variant (1.7 s) → `pNN/params.json` updated. Under a minute of compute per look, against 3–5 min for one CPU Cycles head render.

### 4.9 Where work runs, and the hand-off

| Work | Cloud (Linux, 4 cores, no GPU) | Jeff's Windows machine (GPU) |
|---|---|---|
| Setup, shared library, server, metrics, optimisers, critic tooling, export code | yes | runs them |
| Body fit, rig, pose, landmark and girth loops, Workbench loops | yes | yes |
| Hard-surface parts (02, 12, 13, 14, 15), garment construction, cloth sims (minutes) | yes | yes |
| Cycles `eval` closeups ≤ 0.6 MP (20–60 s) | yes, one at a time | seconds |
| Head and hand closeups with SSS (4–8 min CPU), hair calibration (8–15 min per render), the full-figure `eval` (2–4 min) | only when nothing else needs the box | **preferred** |
| Spec 17 `cal` calibration, `final` renders, export bakes (1.5–2 h CPU) | avoid | **yes** |
| Godot import check | headless import report | the visual check in the hexcom project (.NET) |
| Rigify artist rig (spec 08, optional) | — | yes |

The repository is the only hand-off: scripts, specs, `pNN/params.json`, `assets/interfaces.json`, the evaluation log, milestone images and, at milestones, `deliver/`. Caches never travel (D6); the GPU session runs `setup_session.sh` and `build_all.py --to assemble` (≈ 15 min + 25 min, §3.3 and §4.6) before its first render. A GPU session ends like any other: commit, push, log entry. Render scripts pick the device from `SGT_DEVICE`; results that depend on it (noise, not geometry) are tagged with the device in their sidecar.

### 4.10 The export stage (S13; `scripts/export/`)
The pipeline ends here once Jeff accepts the model. Spec 08 §7.6 owns the skeleton and the exporter call, spec 16 §5.4 the atlases and the bake procedure; this section joins them into one stage, adds LODs, hair cards, validation and the delivery layout.

#### 4.10.1 Steps
1. **Export copies** from `cache/character_rest.blend` into `Export.Character` (and `Export.Rifle`): `Body.Mesh` with the helper geometry deleted (spec 08); body faces hidden under opaque garments deleted when all of their sample points are covered within 15 mm along the normal in both the rest and the hero pose (E; avoids poke-through and saves ≈ 40 % of the body); garments as their rest-posed skinned variants (spec 08 §6 step 7); gear, armour plates and hardware as rigid children of their bones (they become children of the joint nodes in glTF and `BoneAttachment3D`-like children in Godot); hair as cards (§6.2); no scaffolding (`Rig.Diag.*`, `IK.*`, `Cal.*`, `Frame.*`).
2. **Modifiers** applied per shape key (`modifiers.apply_keep_shapes`, Subdivision level 1 at LOD0), Armature left as the only modifier; correctives exported as morph targets with `Corr.Hero` holding the hero values (spec 08 §4.10).
3. **UVs**: the `UV.Atlas` layer of spec 16 §5.1, packed per atlas; `uv.texel_density()` checked against spec 16's §5.4 column (fail if any island is below 70 % of its atlas's figure).
4. **Bakes**: `mat_bake.bake_atlas()` for the eleven atlases (five 4096², five 2048², one 1024²), channels `BaseColor`, `ORM`, `Normal` (spec 16 §5.4), into `cache/bake/`; on the GPU machine unless the cloud box is otherwise idle.
5. **LODs**: LOD0 is the export mesh. LOD1 and LOD2 are `Decimate` (collapse) copies with a protection vertex group (face, hands, emblem, magazine lips at weight 1.0), shape keys reduced to the baked `Corr.Hero`; stitch and lace geometry dropped below LOD0 (their bake carries them); budgets in §4.10.3. Godot also generates its own LODs on import; ours exist for engines that do not and for the tactical camera if Godot's are judged too coarse.
6. **Wrapper**: `Export.Root` rotated 180° about Z and scaled by s = 1800 / measured rest stature (D7), transforms applied to the copies and the armature (spec 08 §7.6 step 2).
7. **Write**: `bpy.ops.export_scene.gltf` with spec 08's option list and `export_format='GLTF_SEPARATE'`, `export_texture_dir='textures'`, per asset and LOD: `deliver/gltf/sgt_morgan.gltf` (+ `.bin`), `sgt_morgan_lod1.gltf`, `sgt_morgan_lod2.gltf`, `rifle_ar12.gltf` (spec 15), sharing `deliver/gltf/textures/`. Loadout-slot children are named `Slot.Primary`, `Slot.Secondary`, `Slot.Armor`, `Slot.Utility` (spec 14 §10.1: the right carriers with the PRIMARY's magazines, `PouchR.*` with SECONDARY, `RigL.Frag.*` with UTILITY; the carrier with ARMOR) so the loadout screen can show or hide them.
8. **Side files**: `deliver/godot/bone_map.json` (spec 08 §3.6, the Godot humanoid column), `deliver/godot/import_options.json` (the `.import` settings of §4.10.5), `deliver/reports/export_report.json` (triangles per object and LOD, bones, materials, texture sizes, scale, stature, hashes), `deliver/reports/pose_report.json` (spec 08).
9. **Validate** (§4.10.5); only a passing export is copied from `cache/deliver_stage/` into `deliver/` and only at a milestone (CLAUDE.md rule 6).

#### 4.10.2 Deliverable layout (`deliver/`, tracked at milestones)
```
deliver/manifest.json               every file: path, bytes, sha256, source commit, Blender build
deliver/blend/sgt_morgan.blend      the rigged, posed master, linking deliver/blend/parts/*.blend; textures external
deliver/blend/parts/NN_name.blend   one per part, each < 95 MB (compress=True)
deliver/gltf/sgt_morgan.gltf .bin   LOD0, skinned, 1.80 m, faces −Z
deliver/gltf/sgt_morgan_lod1.gltf .bin, sgt_morgan_lod2.gltf .bin
deliver/gltf/rifle_ar12.gltf .bin
deliver/gltf/textures/<Atlas>_<Channel>.png|.jpg
deliver/godot/bone_map.json, import_options.json
deliver/renders/                    spec 17 §4.13 under the scope note (hero 1672 × 941 graded and ungraded, the ten ref.* crops, compare and flicker, look-dev turntable sheet)
deliver/reports/                    export_report.json, pose_report.json, metrics.json, critics.json
```
A `.glb` for an engine that prefers one is built on demand (`export_game.py --glb`) into `deliver/tmp/` and not committed (D8). FBX for an engine whose glTF path is weak is likewise on demand (Blender's FBX exporter works headless, research C §7).

#### 4.10.3 Budgets (proposed; specs 02, 11, 13, 14, 15 and 16 set the per-part figures)

| Item | LOD0 | LOD1 | LOD2 | Source |
|---|---|---|---|---|
| Character triangles (without rifle) | ≤ 150 k | ≤ 50 k | ≤ 15 k | E (a hero character for a close loadout camera; spec 14 asks ≤ 25 k for the belt rigs at LOD1, spec 11 12 k for the gloves) |
| Rifle triangles | ≤ 20 k | ≤ 6 k | ≤ 2 k | D 15 §10.1 (LOD2 E) |
| Bones | 171 (spec 08 §7.2); `--lean` 61 | same skeleton | same skeleton | D 08 |
| Influences per vertex | 4 | 4 | 4 | D 08 |
| Materials | 11 atlases (spec 16) | 11 | ≤ 4 (atlases merged at 1K) | D 16, E |
| Textures | 5 × 4096², 5 × 2048², 1 × 1024²; `BaseColor` and `ORM` 8-bit, `Normal` 8-bit (16-bit for the head in Blender; 8-bit in the glTF, §10.3) | shared | 1K copies | D 16 §5.4 |
| Texture bytes per version | ≈ 570 MB all PNG; ≈ 350 MB with `BaseColor` as JPEG q92 4:4:4 (`ORM` and `Normal` stay PNG: JPEG's colour transform and subsampling would bleed the packed channels into each other) | — | — | E |

#### 4.10.4 Repository size and Git LFS
A single milestone of textures is 0.35–0.6 GB and every re-bake adds as much again to the history; the master `.blend` set adds 0.1–0.3 GB. That is past the "few hundred MB" Jeff named, so **this spec proposes Git LFS for `deliver/**/*.{png,jpg,bin,blend}` before the first export milestone** (the `.gltf` JSON stays in git). `git-lfs` 3.4.1 is on the cloud image; cloud sessions clone with `GIT_LFS_SKIP_SMUDGE=1` (they never need the deliverables, which saves the account's LFS bandwidth); Jeff's machine fetches them. Until Jeff decides, `deliver/` holds only the reports and the glTF JSON, and the binaries wait in `cache/deliver_stage/` (§10.3 Q1). `scripts/tools/repo_budget.py` refuses a commit with any file over 50 MB and reports the growth of `.git` per session.

#### 4.10.5 Validation (`scripts/export/validate.py`; p18.V5 and V6)
1. Blender reimport in an empty scene: bone count, morph targets, the `Hero.Pose` action, no vertex with zero total weight, rest height 1800 ± 2 mm, facing −Z (the nose tip has the most negative Z among head vertices), triangle counts within §4.10.3.
2. p18.V5 overlay: the reimported model rendered through the scaled hero camera against the source `form` render (IoU ≥ 0.995, landmarks ≤ 2 px).
3. Khronos glTF Validator (`gltf_validator`, run when available): no errors [VERIFY the binary's release name before scripting it].
4. Godot headless import: copy the glTF set into `scripts/export/godot_check/model/` (a GDScript-only Godot 4.7 project, so the standard build suffices), run `godot --headless --path scripts/export/godot_check --import`, then `godot --headless --path scripts/export/godot_check --script res://check.gd`, which loads the scene and prints JSON: one `Skeleton3D`, its bone count, the `BoneMap` applied with `SkeletonProfileHumanoid` and the list of unmapped profile bones (must exclude every required one), mesh and surface counts, materials, the AABB height (1.800 ± 0.002 m). Import options (`import_options.json`): `nodes/root_type Node3D`, `meshes/ensure_tangents true`, `meshes/generate_lods true`, `meshes/create_shadow_meshes true`, `skins/use_named_skins true`, `animation/import true`, the `BoneMap` on the skeleton subresource with the humanoid profile [VERIFY the 4.7 key names when the template is first written].
5. On Jeff's machine at a milestone: the same import into the hexcom .NET project and a screenshot from the p18.V6 camera.

### 4.11 Git workflow
* **Master only, no branches** (repository convention); commits by agents at every milestone (CLAUDE.md rule 7) and before any session ends; push at the end of every session and after milestones; `git pull --rebase` before a push; never a force push.
* **Stage explicit paths** (`git add spec/18_*.md scripts/lib/measure.py`), never `git add -A`: two agents may share a working copy, and each commits only what it changed. A commit takes `cache/git.lock` (`flock`) so two agents never interleave `add` and `commit`.
* **Messages say why**, in British spelling, first line `Sgt. Alex Morgan: <what changed>` as in the history, then the reason and any spec deviation (rule 8), then the attribution lines the session supplies.
* **Ignored**: `assets/*` except the two whitelisted JSON files and the README; `cache/`; `renders/*` except the evaluation log and the milestone JPEGs; `.venv/`; `*.blend1`, `*.blend2`; `deliver/tmp/` (§4.1.1).
* **Renders stay small** (D12): milestone images JPEG q88, ≤ 1600 px, ≤ 400 KB, at most three per part (`renders/eval/NN_<part>_<preset>.jpg`, overwritten in place); full-resolution PNGs and critic packets stay in `renders/` (ignored); `ref/` zooms are committed only when a spec cites them.
* **Deliverables**: at milestones only, through `deliver/manifest.json`; never a file over 95 MB; LFS as §4.10.4.
* **When**: a milestone is any state a spec names as one (for example spec 08's rigged rest body, posed hero, export round trip), a passing critic round, a passing `build_all.py --verify`, or the end of a session.

### 4.12 Session protocol
**Start** (≈ 5 min of agent time, mostly reading):
1. `bash scripts/setup_session.sh` (≤ 30 s when nothing is missing).
2. Read `notes/session_log.md` (newest entry first), `spec/00_overview.md` once it exists, and the spec of the part to be worked on (Grep and offset reads, not whole files).
3. Read the usage meter where the token exists (`scripts/tools/meter.sh`; Jeff's machine) and note it.
4. Pick the next task: the first row of the §9.2 wave table whose prerequisites are done and which is not claimed in the log's **In progress** list; add a claim line (`- 2026-10-11 09:40 agent a: 05 arm and hand, stage 1–2 (cloud)`); with two agents the orchestrator assigns the pair.
5. Start the server for that part (`bl.py start`) if the task is iterative.

**End** (whatever happened):
1. Run the part's `--check` and the metrics of whatever changed; log the evaluation events.
2. Update the spec in the same commit if the work deviated from it (rule 8); update `pNN/params.json`.
3. Commit (explicit paths) and push; stop the server (`bl.py stop`).
4. Append the session-log entry: date, machine (cloud or GPU), agent, model; what was done; what is next; anything a fresh session must know; the meter reading before and after; remove the claim line.

**Within a session**: one task per agent, sized to fit one API window (§9.5); restart rather than continue past two or three jobs (long contexts dominate cost); background long renders and wait with Monitor, never by polling in a loop; never run two Cycles renders at once on the cloud box.

---

### 4.13 First build on Jeff's workstation (2026-10-10): the library core, the server and `bl.py`

Built: `scripts/lib/` `__init__`, `naming`, `log`, `ctx`, `replace`, `cache`, `params`, `interfaces`, `cli` (with `env` from the setup), `scripts/server/protocol.py` and `blender_server.py`, `scripts/tools/bl.py`; 3,453 lines. `bl.py selftest` (run by `setup_session.sh --check`) passes in ≈ 3 s: start, ping, set and get, a Workbench render, snapshot and restore, a scratch part built through the server (fresh-cache hit on the second build, module reload, a tolerance failure, save and load), refusals of a bad token, of `measure` and of an exec'd `sys.exit`, stop. `bl.py selftest --lib` runs the nine module self-tests inside the server (all pass; `replace` on a real MPFB human, whose own 9 shape keys and 152 vertex groups are left alone; `cli` launches a real part script in a second Blender and reads exit 2 and its RESULT line).

**Measured on the RTX 3050 (against §3.2 and §4.8.1).** Launch to listening 1.1–1.6 s (≈ 1.3); the warm-up render 0.9–1.2 s (4–8 s); ping 0.15–0.22 ms (0.08 ms; 0.015 ms inside the server, the rest is Windows loopback); set and get 1.1–1.3 ms; a shape key set plus 200 evaluated vertices read 7.4–9.9 ms (9.8 ms); Workbench warm, soldier ×1 440 × 915 with FXAA 0.055–0.075 s (1.2–2.3 s), head ×5 850² 0.08–0.10 s (0.72–1.27 s); snapshot / restore 5 / 27 ms for 5.5 MB; one `bl.py` command from the shell ≈ 0.2 s. Blender's cold start here is 1.5–2.5 s with or without `--factory-startup`. §1.4 item 5 is met.

**Deviations from §4.3–§4.8.**
1. **Cache key**: the module list is the import closure of the part script, found from its import statements, not the modules the last build happened to import; the same key comes out in a fresh process and in the server and can be checked before building. Imports made through `importlib` are not seen. Sources are hashed with LF line endings, so Git's line-ending setting cannot change a key. A proxy enters as `proxy:<name>` (a version, if any, is part of the name). The mesh hash is world-space vertices rounded to 0.01 mm plus the face topology, recorded per object in the part's `.key.json`.
2. **Run modes**: without `--rebuild`, a part with an up-to-date cache is loaded, not rebuilt. `--stage` starts from the saved cache and marks the result partial; partial caches and those saved by the server's `save` never count as up to date. Exit 2 applies in every mode (`--check` only adds "save nothing"); a bad argument exits 4, not argparse's 2. On Windows Blender prints its banner after the RESULT line, so readers take the last line starting with `RESULT `.
3. **`Part` record additions**: `keys` (interface-key prefixes, by default the object prefixes with the first letter lowered: `Carrier.` → `carrier.`), `script`, and defaults for the collection, presets and params file.
4. **Dependencies** resolve in order: present in the session; else the dependency's part cache linked read-only under a `Parts` collection; else its declared stand-in; else exit 3. Loading a part's own cache refills its collection and maps the cache's copies of other parts' data (`Morgan.Rig.001`) back onto the session's own.
5. **Naming**: names ending in Blender's `.001`-style suffix are refused, and prefixes must start with a capital, so they can never match MPFB's lower-case names. `Scope.clear(prefix)` lets a stage replace only its own objects.
6. **Parameters** are addressed as strings, `key:`, `mod:`, `gn:`, `xf:` and `const:`; registered names carry a unit factor (mm to m); a shape key's slider range is widened to take the value (Blender otherwise clamps it silently); Geometry Nodes inputs are set by identifier or unique name and the object is tagged for update. The functions are `read`/`write`, so the module does not shadow Python's `set`.
7. **`assets/interfaces.json`** is a flat, sorted map of values only, floats rounded to 0.1 µm, rewritten only when a value changes. A reader that lists its keys gets exit 3 for a missing one; a reader that gives fallbacks gets them with a `[FALLBACK]` warning. Writes to it and to the build journal take a lock file.
8. **Server**: an extra `selftest` command; `render` with a preset calls spec 17's `render.py` `render_preset()` (without one, a plain Workbench render of the scene camera); before a build it reloads changed modules and the modules that import them, and re-imports part scripts. It advises a restart after 200 builds or 5 GB rather than restarting itself, and has no crash recovery yet; TCP only (no file-queue transport); the token travels in an environment variable and `bl.py` reads the port from the server's log; every request but `ping` and `status` is logged to `cache/server/<name>.jsonl`.

The render hooks rely on spec 17's `render_preset(preset, tier, aa, out_dir, stem)` and `camera.load_registry().owner_ids(id)`; a change to either needs `cmd_render` in the server and `_render` in `cli.py` changed with it.

**Left of W1 track a.** `measure.py`, `linmodel.py` and `optim.py` with their self-tests, wired to the server's `measure`, `silhouette`, `variants` and `optimise`; the per-region layer caches and `layer_apply`; the MPFB macro adapter in `params`; the file-queue transport, automatic restart and crash recovery; `bl.py lint-part`; `build_all.py` (its journal exists as `cache.Journal`); a first run on Linux.

## 5. Materials and textures (the pipeline's side; the recipes are spec 16's)

### 5.1 Contract with the materials library
* Part scripts import only `lib/materials.py` (spec 16 §7.2); recipes are named `<Part>.Mat.<Recipe>`, images `<Part>.<Side>.Img.<Map>`, node groups `MG.*`, export atlases `Export.<Atlas>.*`; texture sets are addressed by manifest id (`Leather032`), never by a path.
* `materials.ensure_groups()` runs at the start of every build process and server session; `materials.lint()` runs at the end of every part build, and under `--check` a lint error fails the part (exit 2); S10 runs it over the whole assembly; `mat_bake.bake_atlas()` runs in S13 before the glTF is written (spec 16 §10.1).
* Library versions: a node group carries its version in a custom property; a part cache records the versions it used, so a library change marks exactly the parts that use the changed group stale (§4.5 key).

### 5.2 Where images live
| Kind | Format | Location | Tracked |
|---|---|---|---|
| CC0 texture sets, HDRIs | as downloaded (2K JPG) | `assets/textures/`, `assets/hdri/` | no (manifest is) |
| Generated textures and masks (camo tile, honeycomb, decals, emblem) | 16-bit PNG Non-Color for masks, 8-bit sRGB for colour (spec 16 §5.3, §5.5) | `cache/generated/NN/` | no (the generators are) |
| Per-part wear masks (`<Part>.<Side>.Img.Wear`, `.Wear2`) | 16-bit PNG RGBA, Non-Color | `cache/generated/NN/` | no |
| Export bakes | 8-bit PNG (`BaseColor` may be JPEG q92 4:4:4 at delivery) | `cache/bake/`, then `deliver/gltf/textures/` | at milestones |
| Critic packets, sheets, overlays | 8-bit PNG, display-referred | `renders/NN_name/` | no |
| Milestone images | JPEG q88 ≤ 1600 px | `renders/eval/` | yes |

### 5.3 Colour management in the harness
Every comparison with the reference is made in display space after AgX "Medium High Contrast" and spec 17's grade, because that is what the reference pixels are; read-backs of albedo and bake checks use scene-linear EXR passes (spec 16 §5.6); the export carries sRGB base colours and linear data with no grade (the grade is the loadout screen's look, not the asset's). Metrics that compare colours use CIEDE2000 from spec 17's `colour.py`.

### 5.4 Texel density
`uv.texel_density()` reports px/mm per UV island for the render UVs (spec 16 §5.2: hero wear masks 4–8 px/mm, skin per the owners) and for `UV.Atlas` (spec 16 §5.4: 1.2–8.8 px/mm by atlas). The export stage fails an island below 70 % of its atlas's figure; the critic packet of a part includes the density table when any island is below target.

---

## 6. Fibres, simulation or dynamics (the pipeline's side)

### 6.1 Simulations in the build
* Cloth runs only in stage S7, on the posed collider, frame-stepped in one process with fixed substeps (deterministic, research C §2): trousers (spec 09), sleeves and the gaiter relax (spec 10). The fast loop never simulates, except the gaiter relax (seconds).
* A simulation's cache key includes the hashes of its colliders: the posed `Body.Collider`, `Boot.L/R.ShaftProxy` (02), `Kneepad.L/R.CapProxy` (12), `Vest.Collider` (13), the strap bands (14). A collider that changes beyond its tolerance (spec 09: boot collar ± 5 mm) re-runs the simulation (≈ 5 min) on the next build.
* The specs' automatic stability checks (09 §9.3, 10 §9.3) gate the stage; a failure triggers the spec's own fallback (re-try at higher quality, then the parametric fallback) and is logged with the reason.

### 6.2 Hair for the export (owned here, as spec 07 §10.1 hands it over)
Curves do not export to glTF. `scripts/export/hair_cards.py` builds cards from spec 07's `Hair.Export.ClumpAxes` (90 curves): for each clump axis, two or three ribbons (Curve to Mesh, flat profile 12–18 mm wide, eight segments, tapering to 30 % at the tip) layered 1.5 mm apart and oriented so the ribbon contains the axis and the local scalp tangent; plus a scalp cap shell 2 mm off the hair region carrying the short-hair and fade albedo; ≈ 2 k triangles in all (spec 07's figure). The cards take their own strip of the `Export.Hair` atlas (2048², alpha MASK 0.5, spec 16 §5.4) and are baked selected-to-active from the groom converted to a temporary mesh (Curve to Mesh with a three-vertex circle at the strands' radius) [VERIFY whether Cycles can use the Curves object directly as the bake source]. Stubble and brows are baked into `Export.Head`'s base colour (from `Hair.Masks.R` and the brow strands); lashes become two small cards per eye. Spec 07 Q3 asks Jeff whether cards or a textured scalp cap; cards are the default.

### 6.3 No dynamics in the export
The game receives the rest-posed skinned garments (spec 08 §6 step 7); the hero drape exists only in the `.blend` and in a separate posed reference file. Nothing simulates in Godot.

---

## 7. Rigging and attachment (the pipeline's side; the rig is spec 08's)

### 7.1 Assembly
`Character` holds child collections `Body` (`Body.Mesh`, `Morgan.Rig`, eyes, teeth, nails), `Hair` (07), `Garments` (09, 10, the socks of 01), `Footwear` (02), `Hands` (11), `Armour` (12), `Carrier` (13), `BeltRigs` (14) and `Weapon` (15). S11 appends every part's cache into the assembly (export and hero files are self-contained); spec 17's `scene.py` links `Character` from `cache/character_hero.blend` so a scene rebuild never copies the model.

### 7.2 Attachment checks (S9)
Every object under `Character` must be exactly one of: the armature; `Body.Mesh`; bone-parented (BONE); skinned by an Armature modifier whose weights sum to 1 with ≤ 4 influences (SKIN); or `SurfaceDeform`-bound to `Body.Mesh.Posed` (SURF, hero only, with a SKIN twin for export) — spec 08 §7's methods. Anything else fails the stage with the object's name. Interpenetration between neighbouring layers is measured with `measure.clearance()` at the hero pose (tolerance: 0 penetrating vertices outside the declared compression zones such as strap bites).

### 7.3 The export skeleton
Spec 08 decides: the MPFB `default` deform rig, 171 bones (or the 61-bone `--lean` merge), the MakeHuman A-pose as bind pose until Jeff answers spec 08 Q4, `Hero.Pose` as a one-frame animation, correctives as morph targets, `godot_bone_map.json` from spec 08 §3.6 (written to `deliver/godot/bone_map.json`), the rifle bone-parented to `wrist.R` and imported in Godot as a `BoneAttachment3D` child (spec 08 Q5). The pipeline adds the loadout-slot nodes of §4.10.1 step 7 and checks that every required `SkeletonProfileHumanoid` bone is mapped (§4.10.5).

### 7.4 Scale
s = 1800 / measured rest stature (D7). The rules' eye height is 1650 mm while this body's eye scales to ≈ 1683–1688 mm (spec 08 Q2, spec 17 Q9); the export does not distort proportions to meet it. The answer to that question changes s only, which is one number in `export_report.json`.

---

## 8. Evaluation protocol

### 8.1 The critic protocol

#### 8.1.1 Three critics, three lenses
| Critic | Lens | Asks | Looks at first |
|---|---|---|---|
| C1 Fidelity | the reference | Is this the man and the kit in the picture: shape, proportion, placement, colour, wear, identity? Are the declared differences the only differences? | `pair`, `onion`, `diff`, the overlay |
| C2 Reality | the real world | Would a specialist in this anatomy or this kit accept it: dimensions against the spec's §3 tables (with the `measure` report), construction (seams, stitches, hardware, materials), mechanical plausibility, the reality-wins decisions kept? Anything copied from the drawing that cannot exist? | the zooms, `measure.json`, the spec tables in the brief |
| C3 Craft | computer graphics | Shading artefacts, stretching, faceting, intersections, texture scale and tiling, texel density, noise, waxy or plastic skin, silhouette breaks, "MakeHuman look", consistency of light | the zooms at ×2–×4, the native pair |

#### 8.1.2 The packet (`scripts/eval/critic/packet.py` → `renders/NN_name/critic/r<k>/`)
* `pair_<preset>.png`: reference crop on the left, render on the right, identical size and scale (the crop is cut from `reference_full.png` at the preset's box and scale), long side ≤ 2000 px; for a view with no reference (hidden parts) the render alone.
* `onion_<preset>.png` (50 % blend), `diff_<preset>.png` (|ΔL\*| heat map 0–30), `overlay_<preset>.png` (spec 17's landmarks, patches and silhouette edges).
* `zoom_<preset>_<region>.png`: ×2–×4 crops of the regions the spec's §1.3 names.
* `metrics.json` (automatic metrics with pass flags, §8.2) and `measure.json` (the part's envelope).
* `brief.md`, generated (never written by hand): the spec's "What perfect looks like", pass criteria and critic questions extracted by heading; the declared differences that apply; the previous round's defects as a list of claims to verify (id, location, one line), never their scores.
* File names carry no version words ("fixed", "v3"); left is always the reference.

#### 8.1.3 The critic agent
A fresh sub-agent per critic per round, with only the packet: no build logs, no earlier rounds' reasoning, no other critic's result. Model: Opus by default; at the acceptance milestone of the face (spec 06 V1) the identity question may use the strongest model Jeff budgets for. Instructions (`scripts/eval/critic/prompts/C1.md`, `C2.md`, `C3.md`): open every image with the Read tool before scoring; score every spec question and an overall from 1 to 10 with the anchors below; give each defect a location (preset and pixel box) and a severity; never propose relaxing a tolerance; answer with JSON only.

Anchors: **1** the two rejected builds ("awful"); **3** the right object, crude; **5** right shape and colour, obviously computer-made; **7** convincing at native size, flaws visible in the zooms; **8** a professional would ship it with minor notes; **9** hard to tell from a photograph of the real thing at the zoom; **10** indistinguishable. Severity: **blocking** (wrong identity, a dimension outside tolerance, visible interpenetration or tearing, a required component missing, a reality-wins decision broken); **major** (a flaw visible at native size); **minor** (visible only in a zoom).

#### 8.1.4 Score schema (`scripts/eval/critic/schema.json`, JSON Schema 2020-12)
```json
{"type": "object",
 "required": ["part", "round", "critic", "lens", "model", "packet_sha", "questions", "overall", "defects", "pass"],
 "properties": {
  "part": {"type": "string", "pattern": "^(0[1-9]|1[0-8])$"},
  "round": {"type": "integer", "minimum": 1, "maximum": 5},
  "critic": {"enum": ["C1", "C2", "C3"]},
  "lens": {"enum": ["fidelity", "reality", "craft"]},
  "model": {"type": "string"},
  "packet_sha": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
  "questions": {"type": "array", "items": {"type": "object", "required": ["id", "score", "note"],
    "properties": {"id": {"type": "string"}, "score": {"type": "integer", "minimum": 1, "maximum": 10},
                   "note": {"type": "string", "maxLength": 400}}}},
  "overall": {"type": "integer", "minimum": 1, "maximum": 10},
  "defects": {"type": "array", "items": {"type": "object", "required": ["id", "severity", "preset", "box_px", "what"],
    "properties": {"id": {"type": "string"}, "severity": {"enum": ["blocking", "major", "minor"]},
                   "preset": {"type": "string"},
                   "box_px": {"type": "array", "items": {"type": "integer"}, "minItems": 4, "maxItems": 4},
                   "what": {"type": "string", "maxLength": 300}, "fix": {"type": "string", "maxLength": 300},
                   "spec_ref": {"type": "string"}}}},
  "verified_claims": {"type": "array", "items": {"type": "object", "required": ["id", "fixed"],
    "properties": {"id": {"type": "string"}, "fixed": {"type": "boolean"}}}},
  "pass": {"type": "boolean"},
  "confidence": {"type": "number", "minimum": 0, "maximum": 1}}}
```
`scripts/eval/critic/tally.py` validates each result, rejects an invalid one (the critic is asked once more), and computes the round's outcome.

#### 8.1.5 Pass rule and rounds
1. **Metrics first** (D2): if any automatic metric of §8.2 fails, the round is not sent to the critics.
2. **Pass** = median of the three overall scores ≥ 8 **and** no blocking defect from any critic **and** every automatic metric in tolerance.
3. **At most five rounds** per part per milestone. After a fifth failure the part stops: an `escalation` event in the log with the best round's packet and the open defects, and a question to Jeff in the session-log entry; nobody iterates on it until he answers.
4. **Disagreement**: if the three overall scores span four points or more, the round is repeated once with the same packet and fresh critic instances; a second spread goes to Jeff.
5. **Regression**: a passed part whose dependencies change re-runs its metrics automatically (S12); critics only at the next milestone.

#### 8.1.6 Cost and sequencing
Critics run one at a time behind `cache/locks/critic.lock`, so that with two workers no more than two agents are ever active (a worker waiting on its critic is idle). A round is three critic calls, ≈ 6–10 min of wall time and roughly 15–25 k input tokens per critic (eight to twelve images and the brief, E). Packets are built from `eval`-tier renders; the full-figure and face acceptance rounds use GPU renders.

### 8.2 Objective metrics

| Metric | Tool | Threshold | Source |
|---|---|---|---|
| Face pose gate | MediaPipe FaceLandmarker on the head crop | yaw, pitch, roll within ±2° of (+14.6°, −9.9°, −1.2°) before any ratio is scored | research E §8, spec 06 |
| Face ratios | the 13 MediaPipe ratios and spec 06's §8.2-A table | each \|Δ\| ≤ 5 %, mean ≤ 3 %; double weight on eye spacing, fissure, brow-to-lid, bigonial/bizygomatic, chin width; nothing below the 3 % noise floor is chased | research E §8, spec 06 |
| Face NME | Procrustes-aligned 468 landmarks, RMS / outer inter-ocular distance | ≤ 0.04 | research E §8 |
| Expression | MediaPipe blendshapes (mouthShrugLower, eyeSquint, browDown) | within ±0.15 of the reference | research E §8 |
| 3D face targets | 3DDFA 68 points | build-time only (§4.8.6); never re-run on renders | research E §3 |
| Silhouette IoU | rembg u2net mask of the reference against render alpha (`film_transparent`) or the mesh splat | full body ≥ 0.90; head ≥ 0.95 (head mask from luminance > 45 in the head crop); hair-spike band ≥ 0.85; per-part IoU in each crop ≥ the part's own threshold; ±3 px band and declared differences excluded | research E §8, specs |
| Colour patches | ΔE00 of 5 × 5 means at the anchors' projections, graded `eval` render against the reference | spec 17 P1 ≤ 5, P2 ≤ 3, P3 ≤ 5, P4 ≤ 4, \|ΔL\*\| ≤ 4; owner patches in `patches.json` (default ≤ 5 fabric and polymer, ≤ 3 skin) | D 17 §8 |
| Landmarks | spec 08 `landmarks.json` and `rig_metrics.py` | each within its tolerance (for example GripFrame (724, 368) ± 6 px) | D 08, 15 |
| Layering | Depth Anything V2 on render and reference; scale and shift fitted inside the mask | ordinal checks hold (rifle before vest, pouches proud of trousers, far shoulder behind near); RMSE reported, low weight | research E §8 |
| Part measurements | each part's `measure()` envelope | every item within the spec's tolerance | specs §8 |
| Export | §4.10.5 | as listed | §4.10.5 |

The server renders; the client (image-tools Python, or the AI venv for MediaPipe and Depth Anything) computes. The reference-side values are computed once and cached in `cache/generated/18/ref_metrics.json`.

### 8.3 The evaluation log
* **`renders/eval/log.jsonl`** (tracked): one JSON object per event, ≤ 2 KB; details stay in the packet folder. Keys: `ts`, `session`, `agent`, `machine`, `commit`, `part`, `event` (`metrics`, `opt`, `critic`, `acceptance`, `escalation`, `export`), `round`, `tier`, `presets`, `metrics` (summary: IoU, max ΔE00, max landmark px, part pass count), `critics` (per critic: lens, overall, blocking, majors, minors), `median`, `pass`, `decision`, `next`, `packet`. Example:
```json
{"ts":"2026-10-14T10:32:05Z","session":"cloud-07","agent":"a","machine":"cloud","commit":"3f2c1aa","part":"13","event":"critic","round":2,"tier":"eval","presets":["ref.torso_vest","p13.V4"],"metrics":{"iou":0.934,"de00_max":4.1,"lm_px_max":3.0,"measure_pass":"41/41"},"critics":[{"lens":"fidelity","overall":8,"blocking":0,"majors":1,"minors":3},{"lens":"reality","overall":7,"blocking":0,"majors":2,"minors":1},{"lens":"craft","overall":8,"blocking":0,"majors":0,"minors":4}],"median":8,"pass":true,"decision":"accept","next":"export atlas check","packet":"renders/13_plate_carrier/critic/r2/"}
```
* **`renders/eval/log.md`** (tracked), regenerated by `tally.py` from the JSON lines and never edited by hand: a summary table across parts (status PASS, IN PROGRESS or ESCALATED; rounds used; last date; median), then per part a table of rounds (date, round, tier, IoU, max ΔE00, max landmark px, C1/C2/C3, median, blocking, result) and its open defects, five at most, by severity.
* **Milestone images** `renders/eval/NN_<part>_<preset>.jpg`: the `pair` images of the passing round (D12).

### 8.4 Self-tests of the harness (`bl.py selftest`; at session start whenever `scripts/lib`, `scripts/server` or `scripts/eval` changed)
1. `camproj` against `world_to_camera_view`: ≤ 0.1 px (spec 17).
2. Equivalent crop camera against a border render: IoU ≥ 0.995, centroid ≤ 0.3 px (M: 0.997–0.999, 0.04–0.2 px).
3. Girth of a 64-segment cylinder r 50 mm: 313.9 ± 0.1 mm; IoU of the reference mask with itself: 1.
4. Mesh splat against Workbench alpha on the MPFB default body: IoU ≥ 0.98 [E threshold, to confirm on first run].
5. `linmodel` against the depsgraph: ≤ 0.01 mm (M: 0.0005 mm).
6. Optimiser benchmarks of §4.8.5.
7. MediaPipe on `ref/crop_head_face.png` reproduces the stored ratios within 0.001 (guards against a library update changing the targets).
8. A critic-result fixture validates against the schema; `tally.py` reproduces a known `log.md`.
9. `build_all.py --verify` on the body stages (S1–S2) gives identical mesh hashes.

### 8.5 Failure modes and responses
| Failure | Symptom | Response |
|---|---|---|
| Metrics pass, critics keep failing | the spec's numbers are necessary but not sufficient (spec 06 names this for the face) | escalate after round 5 with the defects; propose a new metric for what the critics see |
| Critics pass, a metric fails | the eye was satisfied, the numbers were not | never accepted; fix it, or record a declared difference with a spec decision |
| Non-determinism | `--verify` hash mismatch on an object | the build fails naming the object; find the unseeded draw or the order-dependent loop |
| Stale cache used | a dependency missing from the key | `--verify` catches it; add the import to the key's module list |
| Server memory growth or crash | resident memory rising, no reply | automatic restart from the last snapshot; restart every 200 builds |
| Detector bias on matcap renders | ratios differ between Workbench and Cycles | spec 06's bias correction (detector minus projected-vertex ratio); fallback renders as spec 06 §4 step 7 |
| rembg defects | the ragged right hip | the region is declared unreliable and excluded |
| Render over budget | a round takes over 15 min of CPU | lower tier for iteration; acceptance on the GPU machine |
| Two agents in the same file | merge conflict | claims in the session log, explicit staging, the later agent rebases |
| API window runs out mid-task | the agent stops | commits at milestones inside the task; the log's claim line marks the task interrupted and the next session resumes from the journal |
| Critic anchoring | scores track the previous round | fresh instances, anonymised packets, only claims carried forward |
| The drawing pulling parts back to "as drawn" | a reality-wins part scored down for matching reality | the declared-difference register (§2.2) |

---

## 9. Build order, effort and risks

### 9.1 Dependency graph (from the specs' own sections 9 and 10)
**Hard** = the data must exist; **soft** = a declared proxy stands in until the real thing exists (§4.4 `proxies`). Every mutual dependency between parts is broken by a proxy and closed by the second pass of wave W8.

| Part | Hard prerequisites | Soft (proxy) | Provides early | Gates |
|---|---|---|---|---|
| 01 Foot, sock | S1–S2 (body, rig fit) | 16 skin core; 17 LookDev | `Foot.L/R.Last` + markers, `sculpt.py`, `measure` habits | 02; 08's foot bones and flat-foot alignment |
| 02 Boots | S2 (`foot`, `ball` bones) | 01 last (stand-in last, 02 §4.1); 13 gear libraries; 09 `gn_stitches` | `Boot.L/R.ShaftProxy` | 09 hem simulation |
| 03 Leg, pelvis | S1 (shared with 04), S2 | 16 | knee anchors, `Body.Collider` legs, `BeltRing`, `corrective.py`, `weights.py` | 09, 12 kneepads, 14 |
| 04 Torso, neck | S1, S2 | 06 chin values, 05 GH hand-over (both as numbers in the specs) | rings, anchors, stand-ins, `NeckTurn` | 06 neck ring, 10, 12, 13 |
| 05 Arm, hand | S1–S2; **15 frames (stage 2)** | 11 glove shell for V7; 16 | `GloveLast`, `SleeveCollider`, `CuffRing`, `GuardFrame`, `ElbowAnchor`, `grip.py` | 08 pose, 10 sleeves, 11, 12 guards |
| 06 Head, face | S1–S2; AI helpers; 3DDFA landmarks | 07 masks; 16 skin; 17 camera | `Head.Anchor.*`, root points, masks, calibration anchors | 07; 10 jaw line; 17 calibration stage A |
| 07 Hair | 06 anchors, UVs, masks; 08 head pose | 10 gaiter (cull) | `Hair.Masks`, `Hair.Export.ClumpAxes` | 06 final look; export hair cards |
| 08 Rig, pose | fit: S1; pose: 05 palm frames and `grip.py`, **15 frames and pins**, 01 last soles, 06 anchors | 13 `Vest.Collider` (a box) | `BONE_MAP`, `bones.json`, `Hero.Pose`, attachment rules, export call | every posed part: 07, 09, 10, 11, 12, 13, 14; export |
| 09 Trousers | 08 pose (posed body, collider); 03 anchors | 02 shaft proxy; 12 cap proxy; 14 strap heights | waistband, knee pockets, cloth helpers | 14 belt; 12 kneepads (final); 02 and 10 reuse its helpers |
| 10 Shirt, gaiter | 04 rings; 05 colliders; 08 pose | 09 helpers (code); 11, 12, 13 stand-in sizes; 16 | shirt bands, gaiter | 12 bands; 13 offsets; 07 cull |
| 11 Gloves | 05 `GloveLast`, `grip.py`; 08 pose | 15 `Rifle.Collider` (A2 box); 16 | glove shells, gauntlet ring | 12 wrist band (soft) |
| 12 Hard armour | 03, 04, 05 anchors; 08 rig | 10 bands; 09 pocket; 13 strap hook; 11 gauntlet; 16 | `Kneepad.L/R.CapProxy`, `mat_hard` recipes, decals | 09 (re-sim) |
| 13 Plate carrier | 04 rings, curves, collider; 08 bone names | 10 offsets; 12 tab; 15 proxy; 16; 17 | `Vest.Collider`, `Carrier.Grid.json`, gear libraries | 08 rifle solve (real collider), 14, 12 |
| 14 Belt, leg rigs | 09 waistband (moved, 14 D1); 03 crest and hips; the gear libraries (code) | 13 cummerbund; 15 magazine; 16 | loadout-slot nodes | export |
| 15 Carbine | none for geometry; 16 `mat_hard` and 17 swatches for materials | 13 collider (placement) | frames, pins, proxy, collider (stage 2); PMAG object | 05 grip, 08 pose, 11, 13, 14 |
| 16 Materials | 17 LookDev (swatches, step 9); export meshes (step 11); 17 light solve (step 12) | — | the library (steps 1–8, 10 need nothing) | every part's look; export bakes |
| 17 Scene (scope) | none for camera, lights, floor, grade; 06 skin for calibration stage A | `Cal.Proxy` | `camera.py`, presets, `render.py`, overlay, LookDev | every evaluation |
| 18 Pipeline | — | — | setup, library core, server, measurement, optimisers, `build_all.py`, metrics, critics | everything; export needs every part |

```mermaid
flowchart LR
  P18[18 tooling] --> S17[17 camera, render, LookDev]
  P18 --> BODY[S1-S2: 03+04 body, 08 rig fit]
  S17 --> M16[16 library]
  W15[15 carbine frames] --> A05[05 arms, grip]
  BODY --> F01[01 foot, last] & L03[03 legs] & T04[04 torso] & A05 & H06[06 face]
  F01 --> B02[02 boots]
  A05 & W15 & F01 & H06 --> POSE[08 pose]
  C13[13 carrier] -. Vest.Collider .-> POSE
  POSE --> T09[09 trousers] & S10[10 shirt, gaiter] & G11[11 gloves] & K12[12 armour] & C13
  B02 -. ShaftProxy .-> T09
  K12 -. CapProxy .-> T09
  S10 --> K12
  T09 --> Y14[14 belt, rigs]
  C13 --> Y14
  H06 --> H07[07 hair]
  S10 -. gaiter .-> H07
  Y14 & G11 & K12 & H07 & M16 & B02 & L03 & T04 --> EXP[S13 export]
```

**What can run in parallel**: the tooling (18), the scene core (17) and the library core (16 steps 1–8, 10) need no part; the carbine (15) needs no body; after S1–S2, the face (06), the arms (05), the foot and boots (01, 02) and the legs and torso sculpts (03, 04) are independent of each other; the carrier (13) and the armour libraries and hardware (12 stages 1–3) can start on stand-ins. **What gates**: S1–S2 gate every body part; 15's frames gate 05's grip and 08's pose; 08's pose gates every simulation and placement; 09 gates 14; 10 gates 12's bands; 13 gates 14's cummerbund and the final rifle solve; 06 gates 07 and the light calibration; 16's bakes gate the export; the export needs everything. The longest chain is 18 → S1–S2 → 05 (with 15's frames) → 08 pose → 09 → 14 → second pass → export; the face (06 → 07 → calibration) runs beside it and gates acceptance, not the other parts.

### 9.2 Build order: waves for two agents
Excluded by the scope decision: the hangar set, floor joints, the floor-pool light, depth of field, haze and glare.

| Wave | Track a | Track b | Where | Done when |
|---|---|---|---|---|
| W0 | critique pass of 01–05 and 09 under the reality rule; revise 05, 08 and 11 against 15 (§10.2 row 1) | `spec/00_overview.md`; critique of 06–17 against each other (§10.2) | cloud | the §10.2 list is closed in the specs |
| W1 | 18 core: setup scripts, `env`, `cli`, `naming`, `replace`, `ctx`, `cache`, `params`, server and `bl.py`, `measure`, `linmodel`, `optim`, `sheet.py`, self-tests | 17 under the scope note: `camproj`, `camera` with the equivalent crop camera, presets, tiers, overlay, masks, LookDev; then 16 steps 1–8 and 10 | cloud | §1.4 items 1, 5, 6, 7; LookDev renders |
| W2 | S1–S2: the shared body pipeline (03, 04) and 08's rig fit → milestone "rigged rest body" | 15 stages 1–2 (helpers, frames, pins, proxy, collider) → `assets/interfaces.json` `rifle.*`; then 15's body stages | cloud | `bones.json`; frames published |
| W3 | 06 S1–S3: harness, the 3DDFA seed (§4.8.6), the LM fit, scripted keys | 05: arm fit, hands, grip on 15's frames | cloud | face ratios in tolerance on Workbench; grip contact report |
| W4 | 04 and 03 sculpts and correctives | 01 foot, sock, last → 02 boots | cloud | part metrics; first critic rounds |
| W5 | 08 pose with a `Vest.Collider` box → milestone "posed hero" | 13 carrier (gear libraries first) → the real `Vest.Collider` | cloud | spec 08's overlay in tolerance |
| W6 | 09 trousers (with 02's shaft proxy and 12's cap proxy v0) → 14 belt and leg rigs | 10 shirt and gaiter → 12 armour → 11 gloves | cloud | part metrics; critic rounds |
| W7 | GPU: 06 S5–S6 skin look-dev, 07 hair, 17 calibration (stage A after 06), 16 steps 9 and 12, acceptance renders | cloud: 16 step 11 code, the export stage code, the Godot check project | GPU + cloud | P1–P4 in tolerance; the face round passes |
| W8 | second pass with real neighbours: 08 rifle re-solve against the real `Vest.Collider`, 09 re-simulated with the real caps and boots, 10 against `Vest.Collider`, 12 final; full-figure acceptance on the GPU | export: atlas bakes (GPU), LODs, glTF, validation, Godot import → milestone in `deliver/` | both | §1.4 item 10; Jeff accepts |

Pairing rule: never two render-heavy tasks at once on the cloud box; pair a render-heavy task with a code-heavy one. A **vertical slice** is recommended inside W2–W6: body, rig, pose, carbine, trousers, boots and the export stage end to end at low fidelity first, so the pipeline is proven before the long tail (§10.3 Q5).

### 9.3 Effort

| Part | Authoring (the spec's own figure, else E) | Code (lines) | Full build on 4 cores | Evaluation round | Where |
|---|---|---|---|---|---|
| 01 | 3–4 sessions (E 28 h) | ≈ 2,500 | ≈ 2 min | `--quick` 15 min; full set ≤ 2.5 h | cloud; SSS closeups GPU |
| 02 | E 20 h | ≈ 1,900 | 9 min (1 min `--fast`) | ≈ 5 min | cloud |
| 03 | 36 h | E 1,800 | ≈ 1 min | 6–9 min | cloud |
| 04 | 3 sessions (E 30 h) | ≈ 2,230 | ≈ 2 min | Workbench 40 s; Cycles 5–10 min | cloud |
| 05 | 4–5 sessions (E 40 h) | ≈ 3,350 | E 2 min | ≈ 4 min per hero view | cloud; SSS on GPU |
| 06 | 6–8 sessions incl. 2 on the GPU (E 55 h) | ≈ 1,800 | inner loop seconds; bakes 20 min | V1 3–5 min CPU; hero set 40 min CPU | cloud + GPU |
| 07 | E 16 h | ≈ 1,100 | ≈ 4 min (< 30 s without calibration) | 8–15 min per Cycles render on CPU | GPU preferred |
| 08 | 45 h | E 2,500 | < 4 min incl. export | 60 s Workbench | cloud |
| 09 | E 30 h | ≈ 2,850 | ≈ 10 min | ≈ 12 min | cloud |
| 10 | 3 sessions (E 28 h) | ≈ 1,700 | 3–4 min | 13–17 min | cloud |
| 11 | 31 h | E 1,800 | E 1 min | ≈ 6 min | cloud + GPU round |
| 12 | 37 h + 2 h GPU | E 2,000 | E 1 min | E 10 min | cloud |
| 13 | 4 sessions (E 32 h) | ≈ 2,450 | 25 s + 2 min bakes | ≤ 10 min | cloud |
| 14 | 20 h | E 1,500 | E 1 min | ≈ 15 min | cloud |
| 15 | 50 h | E 3,000 | E 1 min + export 8 min | ≈ 30 min Cycles | cloud |
| 16 | 69 h | E 3,000 | swatches 25–80 min; export bakes 1.5–2 h CPU | V4 ≈ 30 min | cloud + GPU bakes |
| 17 (scope) | 41 h of its 58 (floor shader trimmed, set builders deferred, grade without glare or haze, calibration on P1–P4) | E 2,500 | 30 s | S1 2–4 min; `cal` 4–7 min | cloud + GPU |
| 18 | E 80 h (setup 5, library core 15, server and client 8, measure and linmodel 10, optim 8, sheets 3, `build_all` and caches 12, metrics 8, critic tooling 6, export 15) | E 4,000 | — | — | cloud |
| W0 spec work | E 15 h | — | — | — | cloud |
| **Total** | **≈ 700 h as written** | **≈ 41,000** | ≈ 25 min to `assemble` | | |

The specs' hours read as human-equivalent effort. A session-based estimate: ≈ 1,000 tested lines per agent session (E) gives ≈ 41 build sessions, plus ≈ 30 look-development, critic and integration sessions, ≈ 70 sessions, i.e. ≈ 35 five-hour windows with two agents; the hour figures give ≈ 90 windows. **Measure after W1** (meter readings per finished task, summary.md's rule) and re-plan from the measured rate.

### 9.4 Time budgets on 4 CPU cores (per render and per part)

| Operation | Budget | Tag |
|---|---|---|
| Fast-loop iteration (measure, optimise, 12 Workbench variants, sheet) | ≤ 1 min of compute | M (components) |
| Workbench crop, warm / first in a process | 0.7–2.5 s / 4–8 s | M |
| Silhouette from the mesh | 0.1–0.45 s | M |
| `look` tier | 10–25 s | D 17 |
| `eval` closeup 800², 48–64 spp | 20–60 s | S research C |
| Head ×5 with SSS (`eval`) | 4–8 min CPU, seconds on the GPU | D 17 |
| Full figure S1 (`eval`) | 2–4 min CPU | D 17 |
| `cal` render | 4–7 min | D 17 |
| `final` | GPU only (40–90 min on this box) | D 17 |
| Export bakes, all atlases | 1.5–2 h CPU, minutes on the GPU | D 16 |
| One part's evaluation round (renders) | ≤ 15 min CPU (≤ 30 min for 15 and the full figure) | E |
| One critic round | 6–10 min wall | E |
| Rebuild from an empty cache to `assemble` | ≈ 25 min CPU | E from §4.6 |
| Setup from empty | 10–14 min | E from §3.3 |

With two agents on the box: one Cycles render at a time behind `cache/locks/cycles.lock`, `threads 3`; the other agent stays on Workbench and measurement.

### 9.5 Working inside the 5-hour API window
* Two agents per window, never a third; critics run inside a worker's turn, one at a time (§8.1.6).
* One task per agent per window, sized from §9.3 to about three and a half hours of work, with commits at the milestones inside it so an exhausted window loses nothing.
* The orchestrator is a Workflow script (`scripts/workflows/`) that launches the pair of the current wave, waits, and records which tasks finished; the next pair starts in the next window.
* Read the meter before and after the first pair of a weekend and extrapolate; stop at the next commit when the week approaches the floor (about 20 % left for Monday morning, summary.md).
* Long renders run in the background and are waited on with Monitor, not by polling; GPU work is batched for Jeff's sessions.

### 9.6 Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| The total effort outruns the account's windows | high | the vertical slice first; measure the rate after W1; drop optional work (Rigify rig, `final` 4K renders, vellus hair) before core parts |
| A Windows step fails in Git Bash (paths, venv from Blender's Python, wheels for 3.11) | medium | the `[VERIFY]` list of §4.2.4 is the first GPU session's task; `SGT_BLENDER` and an existing Python override every guess |
| Spec cross-talk keeps moving interfaces (hip height, grip frame, waistband, cummerbund) | high | W0 closes §10.2 before building; `assets/interfaces.json` makes every later change visible and marks its readers stale |
| MediaPipe misreads Workbench matcap heads | medium | spec 06's bias correction and its fallbacks (EEVEE flat, Cycles 16 spp) |
| Silhouette splat disagrees with real renders (thin straps, hair) | medium | self-test 4; the render-alpha IoU is the acceptance number, the splat the optimiser's |
| Deliverables exceed what git should hold | certain without LFS | §4.10.4; Jeff decides before the first export milestone |
| Two agents corrupt each other's work in one working copy | low | claims, explicit staging, `git.lock`, part-scoped writes |
| Godot 4.7 import option names differ from 4.x documentation | medium | the GDScript check reports what it finds; the template is written from the first successful import |
| Critic scores drift between models or rounds | medium | fixed anchors, three lenses, median, metrics gate, five-round cap |

---

## 10. Interfaces and open questions for the client

### 10.1 What every part gives the pipeline, and gets from it
**Gives** (checked by `bl.py lint-part NN`): a `PART` declaration (id, collection, prefixes, hard needs, proxies, provides, stages, presets, params); `build(ctx, args)` and `measure(ctx, args)` with the envelope of §4.8.4; the standard command line (§4.4); `scripts/eval/presets/pNN.json` (spec 17's schema, crop presets on the equivalent camera); `scripts/parts/pNN/params.json` and, where it optimises, `objectives.py`; its proxies as cheap stand-ins built in its first stage; its keys in `assets/interfaces.json`; its declared differences (with the spec decision); its patches in `patches.json`; for body-region parts, layer caches. **Gets**: setup, caches and keys, the server and the client, measurement primitives, the linear target model, optimisers, contact sheets, the critic packet and protocol, the metrics, the log, the assembly, the export.

Special items: spec 07 hands over `Hair.Export.ClumpAxes` (cards are built here, §6.2); spec 08 owns the export call and the bone map, run by S13 (`scripts/export_game.py` moves to `scripts/export/`); spec 15 provides `Rifle.*` as its own glTF and the PMAG as a reusable object in its cache; spec 16 provides `ensure_groups()`, `lint()` and `bake_atlas()`; spec 17 provides the scene, the presets, `render.py`, the overlay and LookDev, and consumes `cache/character_hero.blend`.

### 10.2 Changes for the critique pass (W0)

| Spec(s) | Change | Why |
|---|---|---|
| **05, 08, 11 against 15** | **05**: `Rifle.GripFrame` (0, −169.0, −94.8) (was (0, −194, −76)); `HandguardFrame` station 170 mm (05 wrote 198; 08 and 15 agree on 170); handguard section 38.1 × 49.3 mm (was 45 × 55); grip 102 tall, rake 25°, top 55 × 30.5, finger nub at 22; anchors `IndexFace`, `ThumbRail`, `FingerFacet`; re-run the grip solve. **08**: pins butt (0, −415, −46) and muzzle (0, 427.2, 0), distance 843.5 (was 849); mass 3.3 kg (was 3.6); frame check GripFrame (724, 368) ± 6 and HandguardFrame (840, 467); re-solve the two-pin placement and the arms. **11**: the handguard is the MCMR-13 section (38.1 × 49.3) with Ø 10 lightening holes at 26 mm (15 Q2 default), not the octagonal 45 × 55 with Ø 13–15 holes; `Rifle.Collider` contact groups at ≤ 0.3 mm; nothing under the handguard between Y 125 and 260 but those holes | spec 15 (2026-10-10) moved the grip frame and changed the handguard section; every grip number in these specs is parametrised on the frames, so the change is data, but the solves must be re-run and the texts corrected before W3 |
| 01 | `Human` → `Body.Mesh`; "scene A" → `LookDev` (17); `render_harness.py` → the `lib/render.py` shim | one body name; spec 17's scene |
| 02 | `builds/02_boots.blend` → `cache/parts/02_boots.blend`; `boot_*.py` and `measure_boot.py` → `scripts/parts/p02/` | D5; part-private code out of `lib/` |
| 03, 04, 08, 09, 14 | propagate spec 08 D1 (hips 963 rest) and spec 14 D1 (waistband top Z 1013 posed); spec 04's rest stature 1877 versus the brief's 1855 is settled once, and the export scale is computed either way (D7) | the reality-wins proportions |
| 04, 06, 07 | neck breadth (06 asks 130 against 04's 135); nape hairline 1665 (06) against ≈ 1650 (04); `Torso.Masks2.B` redefined per 07 | spec 06 §10.1, spec 07 §10.1 |
| 04, 08 | `assets/body/base.blend`, `body_rigged.blend`, `markers.json` → `cache/body/` | D5 |
| 06 | the inner loop's Jacobian comes from `linmodel` (exact, µs) instead of finite differences through the depsgraph (≈ 50 ms per column); the 3DDFA seed of §4.8.6 starts it | D3 |
| 08 | `export/` → `deliver/gltf/`; `.glb` with embedded textures → glTF separate with external textures; scale 0.9704 → computed (D7); `godot_bone_map.json` → `deliver/godot/bone_map.json` | D7, D8, Jeff's scope decision |
| 09, 11, 12, 14, 15 | `assets/generated/…` → `cache/generated/NN/` | D5 |
| 11 | `stitch.py` → `gn_stitches.py`; `glove_pattern.py` → `scripts/parts/p11/` | one stitch library |
| 12 | `decals.py` → `decal.py` (spec 16 agrees); `scripts/eval/views.py` → `presets/p12.json` (17) | one decal module; one preset registry |
| 13 | `assets/cache/13/` → `cache/generated/13/` | D5 |
| 15 | `export/rifle_ar12.glb` → `deliver/gltf/rifle_ar12.gltf`; LOD0 ≤ 20 k and LOD1 ≤ 6 k adopted (§4.10.3) | D8 |
| 16 | `assets/build/` → `cache/bake/` and `assets/generated/` → `cache/generated/` (both stay out of git, as 16 requires); textures external in `deliver/gltf/textures/`, not embedded in a GLB; `ORM` never as JPEG (its packed channels would bleed); the head's 16-bit normal stays in the Blender master, the glTF gets 8-bit | D5, D8, §4.10.3 |
| 17 | crop presets default to the equivalent crop camera (D1); `deliver/` is tracked, not ignored (D10); the packed 0.6–1.5 GB `.blend` is not a deliverable; flat backdrop #202426 above the floor (§2.1) | measured here; CLAUDE.md rule 6 |
| 10, 13, 15 | `assets/interfaces.json` is whitelisted in `.gitignore` and written through `lib/interfaces.py` with per-part key ownership | D9 |
| all | the `PART` declaration, the standard command line, the `measure()` envelope, presets, `params.json`, declared differences | §4.4, §10.1 |

### 10.3 Questions for the client
1. **Large files.** The first export milestone brings ≈ 0.35–0.6 GB of textures and 0.1–0.3 GB of `.blend`, and every re-bake adds as much to the history. Git LFS for `deliver/**/*.{png,jpg,bin,blend}` (proposed; cloud sessions skip downloading them), GitHub release assets per milestone, or a shared drive?
2. **Your Windows machine.** Is Blender 4.5 installed, and where? Which GPU (NVIDIA means OptiX)? Is a Python installed (otherwise the setup uses Blender's own)? May the setup keep ≈ 5 GB of ignored downloads and caches inside your hexcom checkout, and may it enable `core.longpaths`?
3. **Order.** A vertical slice first (body, rig, pose, carbine, trousers, boots, export, at modest fidelity, so the whole pipeline is proven early), or part by part in spec order?
4. **Game budgets.** 150 k / 50 k / 15 k triangles for the character's three LODs plus 20 k / 6 k / 2 k for the rifle, 171 bones (or the 61-bone lean skeleton, spec 08 Q3), eleven materials (spec 16 Q1 asks about a lighter tactical-view atlas set). Acceptable, or is the tactical camera served by Godot's own LODs?
5. **Other engines.** After Godot, which engines are to be compared (Unity, Unreal)? That decides whether an FBX export is ever needed.
6. **Escalation.** After five failed critic rounds on a part, should the agent stop and ask you (default) or accept the best round and move on?
7. **Usage meter.** Can cloud sessions read the usage meter (the token lives only in your `.claude/settings.local.json`), or should agent pairs run only when you can watch the meter?

The eye-height and scale question is already with you as spec 08 Q2 and spec 17 Q9; the pipeline computes the scale from the measured stature, so the answer changes one number.

### 10.4 Items to verify
* Godot 4.7.2: `--headless --import` behaviour, the `.import` option keys, `SkeletonProfileHumanoid` bone names and the 8-weight option.
* Windows (first GPU session): a venv created by Blender's Python; `win_amd64` cp311 wheels for mediapipe 0.10.35 and onnxruntime 1.30.0; `System32\tar.exe` on the Blender zip; the WinGet path of Godot; `cygpath` hand-offs.
* The Khronos glTF Validator release binary and its name.
* The cost of MPFB's `reapply_macro_details` per call (macro-slider optimisation).
* Whether Cycles bakes from a Curves object as a selected-to-active source (hair cards).
* The splat-against-alpha IoU threshold of self-test 4 (0.98).
* Jeff's Git LFS storage and bandwidth quota.
* Wheel sizes in §3.1 and the setup totals in §3.3 (measure on the first fresh container).
