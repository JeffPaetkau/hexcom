# Research E — CPU-feasible AI helpers for the likeness loop

Date: 2026-10-06. Machine: 4 cores, 15 GB RAM, no GPU, ~19 GB free disk. Everything below ran on
the CPU from one virtualenv, `assets/ai/venv` (system Python 3.13.16, 2.1 GB). The first attempt at
this task was cut off by an API limit after producing most artefacts; this note was written by
inspecting those artefacts and logs, re-rendering the meshes in Blender, and making one further
time-boxed attempt at TripoSR. All timings are wall-clock seconds; the CPU was shared with other
researchers' Blender jobs (load average 3–5 on 4 cores), so they are pessimistic by up to ~2×.

## TL;DR / recommendation

| Helper | Ran? | Runtime (CPU) | Disk | Verdict |
|---|---|---|---|---|
| MediaPipe FaceLandmarker (478 pts, pose, blendshapes) | yes, on `ref/crop_head_face.png` | 0.38 s incl. model load | 3.8 MB model + 38 MB in venv | **Integrate** — the primary likeness metric engine (landmark ratios, pose check, NME) |
| 3DDFA_V2 (BFM 3DMM, 38 365-vertex face) | yes, without its Cython extensions | 0.5 s load + 2.3 s infer | 155 MB repo (46 MB after trimming) | **Integrate once, as a 3D sparse target** (68 3D landmarks for nose projection / jaw plane). Not a shrinkwrap "truth": it is a generic 3DMM face |
| rembg `u2net` (ONNX) | yes, on `ref/crop_soldier_full.png` | 3.5 s wall (1.0 s session, 0.9 s for two inferences) | 176 MB model + ~280 MB in venv (onnxruntime, numba) | **Integrate** — reference silhouette matte for IoU; renders use Blender's own alpha |
| Depth Anything V2 Small (transformers) | yes, on `ref/crop_soldier_full.png` | 6.9 s wall (0.3 s load, 1.5 s infer at 1078×518) | 99 MB model + 885 MB in venv (torch, transformers) | **Integrate as a secondary metric** (relative depth/layering of gear); low weight |
| TripoSR (single image → mesh) | yes, on the 3rd attempt (shims in §6) | 65 s wall, 4.0 GB RSS | 1.7 GB (+1.0 GB bria-rmbg it pulled in) | **Drop**; a blobby 128³ figure with inflated depth; delete folder |
| SD-Turbo (txt2img/img2img) | downloaded only, never run | — | 2.5 GB | **Drop**; delete folder |
| MediaPipe selfie_multiclass segmenter | downloaded only | — | 16 MB | Drop (u2net is better for body + rifle); delete file |

Total AI footprint today: 8.4 GB in `assets/ai/` (7.4 GB from the first attempt + 1.0 GB `bria-rmbg-2.0.onnx` that TripoSR's `rembg.new_session()` pulled in today) + 48 KB HF cache. After the deletions in §9 it is
≈2.6 GB (venv 2.1 GB + models 0.5 GB), and the venv could be rebuilt in ~95 s from PyPI.

## 1. Environment and install (what was actually done)

`assets/ai/install_log.txt` records four timed `pip` stages starting 15:26:51 UTC and finishing
15:28:24 (93 s total): MediaPipe 18.8 s, rembg 23.3 s, torch-cpu 32.8 s, transformers 17.3 s.
`sd_turbo/download_log.txt`: diffusers installed in 9 s, 2.5 GB of SD-Turbo weights in 80 s.
`triposr/install_log.txt`: deps (trimesh, xatlas, omegaconf, einops) 5 s, torchmcubes build FAILED
(`pip._vendor.pyproject_hooks._impl.BackendUnavailable: Cannot import 'scikit_build_core.build'` —
it was built with `--no-build-isolation` and `scikit-build-core` was not installed), 1.68 GB
`model.ckpt` in 58 s.

The exact shell lines were not logged; the following reproduces the venv as it exists
(`pip list` in the venv confirms every version):

```bash
python3 -m venv /home/user/sgt_morgan/assets/ai/venv
V=/home/user/sgt_morgan/assets/ai/venv/bin/python
$V -m pip install -q mediapipe==0.10.35 opencv-python-headless pillow        # 18.8 s
$V -m pip install -q rembg==2.0.85 onnxruntime==1.30.0                          # 23.3 s (pulls pymatting, numba, llvmlite, scikit-image, scipy)
$V -m pip install -q torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cpu   # 32.8 s
$V -m pip install -q transformers==5.18.0 accelerate safetensors              # 17.3 s
$V -m pip install -q diffusers==0.41.0                                        #  9 s   (SD-Turbo only — not needed)
$V -m pip install -q trimesh xatlas omegaconf einops                          #  5 s   (TripoSR only — not needed)
```

Model downloads (all verified reachable with HEAD requests on 2026-10-06; sizes are on-disk bytes):

```bash
A=/home/user/sgt_morgan/assets/ai
curl -L -o $A/mediapipe/face_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task   # 3 758 596 B
curl -L -o $A/mediapipe/canonical_face_model.obj \
  https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/mediapipe/modules/face_geometry/data/canonical_face_model.obj  # 46 KB (triangulation of the 468 pts)
curl -L -o $A/rembg_models/models/u2net/u2net.onnx \
  https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx                                # 175 997 641 B; set U2NET_HOME=$A/rembg_models
$V -c "from huggingface_hub import snapshot_download as s; s('depth-anything/Depth-Anything-V2-Small-hf', local_dir='$A/depth_anything_v2_small')"  # 99 173 660 B safetensors + 2 json
git clone https://github.com/cleardusk/3DDFA_V2.git $A/3ddfa_v2/repo       # commit 1b6c676 (2022-01-23); weights/mb1_120x120.pth 13.8 MB and configs/bfm_noneck_v3.pkl 24.4 MB are IN the repo
# not recommended (see §6, §7):
# https://huggingface.co/stabilityai/TripoSR  (model.ckpt 1 677 246 742 B + config.yaml); https://github.com/VAST-AI-Research/TripoSR.git commit 107cefd
# https://huggingface.co/stabilityai/sd-turbo fp16 variant (unet 1.73 GB, text_encoder 681 MB, vae 167 MB)
```

Rules that held: run the venv Python with `-I`; keep the cwd outside the downloaded repos and put
them on `sys.path` from the script (`ai_3ddfa_run.py` does this). The rembg CLI does not work under
Python 3.13 (incomplete optional deps) — the Python API does.

## 2. MediaPipe FaceLandmarker — ran, works, fast

Script: `scripts/research/ai_face_landmarks.py <image> <out_prefix>`. Run on
`ref/crop_head_face.png` (850×850). Outputs in `assets/ai/`: `face_ref_landmarks.json` (78 KB:
478 normalised + pixel landmarks, 52 blendshapes, 4×4 head matrix, 13 likeness ratios),
`face_ref_overlay.png`, `face_ref_mesh.obj` (468 vertices / 898 triangles, canonical tessellation).

Facts from the JSON: detection + model load **0.38 s**. Head pose from the transformation matrix:
yaw **+14.6°**, pitch −9.9°, roll −1.2° (MediaPipe's sign convention; the magnitude agrees with the
manual estimate of 12–22° toward the soldier's left in `notes/analysis_face_grooming.md` §1 and
with 3DDFA's −15.2°, which uses the opposite sign). Ratios (reference values for the likeness
checklist): face_width/height 0.900, jaw/face width 0.839, inner-IPD/face width 0.244,
outer-IPD/face width 0.610, mouth/outer-IPD 0.585, nose width/inner-IPD 1.152, nose length/face
height 0.235, eye-to-mouth/face height 0.447, nose-to-chin/face height 0.460, eye aspect 0.329,
lip height/mouth width 0.249, nose length/width 0.930. Top blendshapes: mouthShrugLower 0.58,
eyeLookOutLeft 0.31, eyeSquintLeft 0.28 — i.e. a slight pressed-lip set and a squint, both visible
in the reference. Landmarks pixel bbox x 268–637, y 120–529 (forehead point 10 sits on the
hairline, the chin point 152 on the menton; the contour follows the jaw closely in the overlay).

Blender render of the 468-vertex mesh (`renders/research/ai/face_mediapipe_clay_{front,threequarter,profile}.png`,
29 s for three Cycles views at 32 samples): a lumpy, low-resolution shell — the nose is a blob,
there are no eye sockets. **Not a shrinkwrap target**; it is a 2D (plus weak-z) measurement tool.

## 3. 3DDFA_V2 — ran without Cython; usable as a sparse 3D target only

Script: `scripts/research/ai_3ddfa_run.py <image> <out_prefix> --mp-json face_ref_landmarks.json`
(MobileNet-V1 120×120 config `mb1_120x120`, 62 params = 12 pose + 40 shape + 10 expression). The
FaceBoxes/Sim3DR Cython extensions were never built: the face box comes from the MediaPipe
landmark bbox and the overlay/side view are OpenCV point splats. Model load **0.50 s**, inference +
dense and sparse reconstruction **2.33 s**. Outputs: `face_3ddfa_dense.obj` (3.25 MB, 38 365
vertices / 76 073 triangles, image-pixel units with y flipped up and z toward the camera, vertex
colours sampled from the image), `face_3ddfa_lm68.json` (68 landmarks with z, pose, all 62
params), `face_3ddfa_overlay.png`, `face_3ddfa_sideview.png`. Pose yaw −15.2°, pitch −10.0°,
roll −3.3°. Dense mesh covers x 235–638, y 63–553 px; depth range 370 px (0.76 of the 490 px
brow-to-chin span — a touch deep, as BFM "noneck" masks wrap to the ear line).

Agreement with MediaPipe (2D, as % of the 407 px forehead-to-chin height): chin 4.0 %, nose tip
3.6 %, eye outer corners 1.1 % / 3.0 %, mouth corners 1.0 % / 3.5 %, nose alae 4.5 % / 7.0 %
(3DDFA puts the nostril wings wider). So **two independent detectors disagree by 1–4 % of face
height on the same image**; any likeness metric below ~3 % is inside the noise.

What the renders show (`renders/research/ai/face_3ddfa_{vcol,clay}_{front,threequarter,profile}.png`,
59 s for six views): a smooth, plausible face with the correct turn, a nose with the right
projection, a lip line and a chin that match the reference silhouette in profile, and a jagged
"noneck" boundary. The forehead stops at the hairline; there are no ears, skull, neck or eyeballs;
the eyes are closed shells. Identity is generic: 40 BFM shape coefficients regressed from a
120×120 crop give "a lean 35-year-old male face", not Morgan's long rectangular head, his heavy
brow-to-lid distance or his chin width (compare `ref/crop_head_face.png`). On the overlay the near
(soldier's right, viewer's left) jaw contour sits ≈10 px inside the real cheek edge.

Judgement: **do not shrinkwrap the MPFB head to it** except, optionally, at low influence in the
mid-face band (nasion to upper lip, cheek to cheek) after rigid + scale alignment. Its real value
is the 68 landmark positions **with depth**: after aligning the mesh to metres (known head height
≈ 230 mm hair-top to menton from `analysis_consolidated.md`) and to the MPFB head via Procrustes
on the stable points (eye corners, nasion, subnasale, mouth corners, menton), it gives nose
projection, cheekbone depth and jaw-plane angle that no 2D method gives. Use those as sparse
3D targets for the MPFB target search (nose-point, cheek, jaw and chin targets), with the 2D
ratio table as the hard constraint.

## 4. Depth Anything V2 Small — ran

Script: `scripts/research/ai_depth.py <image> <out_prefix>` (HF `AutoModelForDepthEstimation`,
torch CPU, 4 threads). Run on `ref/crop_soldier_full.png` (880×1830). Outputs `assets/ai/
soldier_full_depth16.png` (16-bit, relative inverse depth, larger = nearer) and
`soldier_full_depth_vis.png` (inferno preview). The script prints its timings to stdout, which
the interrupted run did not capture; re-run today on an idle CPU: **load 0.3 s, inference +
bicubic resize 1.5 s, 6.9 s wall** including the torch/transformers import; input tensor
1×3×1078×518 (the processor keeps the aspect, short side 518), raw prediction 1078×518 upsampled
to 880×1830.

What it gives: a clean, confident separation of soldier from hangar; the rifle reads in front of
the vest (0.661 vs 0.570 normalised at the receiver vs chest), pouches proud of the trousers
(0.606), feet nearer than the head (0.656 vs 0.512) because the camera looks slightly down.
Inside the rembg mask the values span 0.49–0.72 (5th–95th percentile) against a background mean of
0.26. It is **relative, affine-ambiguous and not metric**; it cannot measure limb thickness, but
it does encode layering (what is in front of what) and the broad convexity of the torso.

## 5. rembg u2net — ran

Script: `U2NET_HOME=assets/ai/rembg_models venv/bin/python -I scripts/research/ai_rembg.py <image> <out_prefix> [model]`
(Python API; `remove()` twice, once with `only_mask=True`). Run on `ref/crop_soldier_full.png`.
Re-timed today: **session load 1.0 s, two inferences 0.9 s, 3.5 s wall.** Always pass the model
name explicitly: in rembg 2.0.85 `new_session()` with no argument defaults to `bria-rmbg` and
downloads a 1.02 GB `bria-rmbg-2.0.onnx` (TripoSR's `run.py` did exactly that today).
Outputs `assets/ai/rembg_out/soldier_full_u2net_cutout.png` (RGBA, 1.34 MB) and
`soldier_full_u2net_mask.png` (L, 84 KB). Mask facts: foreground 44.2 % of the frame (threshold
127), soft pixels (16–239) 3.5 %, bbox x 84–796, y 0–1783. The silhouette includes the rifle and
the dark boots against the dark floor (where a luminance threshold fails); the only defects are
ragged fringes at the soldier's right hip (viewer's left, x≈170–250, y≈900–1100, the pouch
straps) and the arm–torso gaps being only partly opened. Good enough for an IoU metric with a
±3 px "don't care" band at the edge.

## 6. TripoSR — ran on the third attempt; verdict: drop

Installed: repo at `assets/ai/triposr/repo` (commit 107cefd), `model.ckpt` 1.68 GB + `config.yaml`
from `stabilityai/TripoSR`, `torchmcubes_src` clone (build failed, see §1). Three attempts today,
each ≤ 1 min, all from `scratchpad/tsr_shim/run_tsr.py` which puts the repo on `sys.path` and runs
`run.py` via `runpy` with `--pretrained-model-name-or-path assets/ai/triposr --mc-resolution 128
--chunk-size 8192 --model-save-format obj` on the rembg cutout:

1. `torchmcubes` missing → replaced with a 10-line shim over `skimage.measure.marching_cubes`
   (reverse the vertex axis order to mimic torchmcubes, which TripoSR then undoes with `[2,1,0]`).
2. `ModuleNotFoundError: moderngl` (only needed by `--bake-texture`) → stubbed.
3. `RuntimeError: Error(s) in loading state_dict for TSR` — the 2024 checkpoint names the DINO ViT
   weights `image_tokenizer.model.encoder.layer.N.attention.attention.query` but transformers
   5.18 builds `image_tokenizer.model.layers.N.attention.q_proj` (likewise key/value/o_proj,
   `intermediate.dense`→`mlp.fc1`, `output.dense`→`mlp.fc2`). Remapped the keys in the shim.

**Attempt 3 ran to completion: 65.4 s wall, peak RSS 4.0 GB** (log kept at
`assets/ai/triposr_out/run.log`): model init 14.6 s (the DINO `config.json` is fetched from
`facebook/dino-vitb16` on the Hub — 48 KB, the weights are inside `model.ckpt`), image
preprocessing 41.4 s of which ~40 s was rembg downloading `bria-rmbg-2.0.onnx` (1.02 GB) because
`run.py` calls `rembg.new_session()` with no model name, transformer forward **7.7 s**, marching
cubes at 128³ via the skimage shim **1.7 s**, OBJ export 0.03 s. Output
`assets/ai/triposr_out/soldier_full_triposr_mc128.obj`: 8 253 vertices / 16 518 triangles with
vertex colours, 845 KB; the 512² padded input is `input_512.png`.

Blender renders (`renders/research/ai/body_triposr_{vcol,clay}_{front,threequarter,profile}.png`,
20 s): the figure is recognisable — head, torso, two legs, the rifle arm — but it is a melted
blob with no gear, hands or face; the legs splay, the vertex colours are grey mush. Bounding box
in TripoSR's unit frame 1.035 × 0.530 × 0.421 (height : width : depth = 1 : 0.51 : 0.41), i.e.
the body depth is ≈0.75 m at a 1.83 m height — more than twice the real ≈0.30–0.35 m of chest
plus rifle. The reference tables already give every proportion to ±1 cm; this gives them to ±15 cm.
Note also that TripoSR writes height along the OBJ z axis, so with Blender's default OBJ import
(forward −Z, up Y) the figure lies along −Y.

A single-image 128³ marching-cubes blob of a 1.8 m figure cannot tell us anything
the measured landmark tables in `notes/analysis_consolidated.md` and MPFB's parametric body do not
already say more precisely, and the 1.7 GB checkpoint + a pinned `transformers<5` would be a
permanent maintenance cost in `setup_session.sh`. **Delete `assets/ai/triposr` and
`assets/ai/rembg_models/models/bria-rmbg`.** (`ai_triposr_run.py` and the shim stay in
`scripts/research/` as a record of how it was made to run.)

## 7. SD-Turbo — downloaded only; drop

`assets/ai/sd_turbo/` holds the fp16 `stabilityai/sd-turbo` pipeline (unet 1.73 GB, text encoder
681 MB, VAE 167 MB, scheduler/tokenizer; `model_index.json` says `StableDiffusionPipeline`,
diffusers 0.41.0 installed). It was never run. It was downloaded as a possible source of extra
"reference" views or texture detail, and that is exactly why it should not be used: 1–4-step SD
txt2img/img2img does not hold a specific identity, there is no ControlNet or IP-Adapter on disk,
and anything it produced would be invented evidence that the specs would then try to match.
Procedural/scanned textures from ambientCG and Poly Haven already cover the materials. On CPU a
512² single step would be roughly 15–30 s with ~6 GB RAM (fp16 weights are upcast to fp32 on CPU);
not measured. **Delete `assets/ai/sd_turbo` (2.5 GB) and `pip uninstall diffusers`.**

## 8. How to wire the keepers into the likeness loop

The loop is: build head → render with the matched camera and pose → measure → adjust targets →
repeat. Everything below is CPU-cheap (< 5 s per render) so it can run inside the eval harness
(`scripts/eval/`), and all of it compares a *render* to the *reference* with the same tool, so
detector bias cancels to first order.

1. **Pose gate (MediaPipe).** Before any ratio is scored, the render's head yaw/pitch/roll from
   `facial_transformation_matrixes` must be within ±2° of the reference (+14.6°, −9.9°, −1.2°).
   Fail the gate → fix the camera/rig, do not tune the face.
2. **Landmark ratio score (MediaPipe, primary).** The 13 ratios in `ai_face_landmarks.py` plus the
   30-landmark table in `analysis_face_grooming.md` §2–3 (re-expressed with MediaPipe indices where
   possible). Report per-ratio delta in %, accept |delta| ≤ 5 % per ratio and mean absolute
   delta ≤ 3 %, double weight on eye spacing, fissure width, brow-to-lid, bigonial/bizygomatic and
   chin width. Noise floor measured today: 1–4 % between detectors, so do not chase below 3 %.
3. **NME (MediaPipe, secondary).** Procrustes-align the 468 render landmarks to the reference and
   report RMS error normalised by outer inter-ocular distance; target < 0.04. This catches shape
   errors the ratio table misses (cheek contour, lip shape) and is the standard face-alignment
   metric so its scale is interpretable.
4. **Blendshape sanity (MediaPipe).** mouthShrugLower / eyeSquint / browDown of the render within
   ±0.15 of the reference — the expression is part of the likeness and must be in the rig pose.
5. **Silhouette IoU (rembg once, Blender alpha per render).** Compute the reference mask once from
   `rembg_out/soldier_full_u2net_mask.png` (and a head crop from a luminance threshold > 45, as
   §11 of the face note describes — the hangar is dark); render with `film_transparent` and take the
   alpha. IoU ≥ 0.95 head, ≥ 0.90 full body, ≥ 0.85 for the hair-spike band; ignore a 3 px edge band.
   Per-part IoU inside each `ref/crop_*.png` rectangle gives the part scripts a pass/fail.
6. **Relative depth (Depth Anything, tertiary).** Run the same model on the render; inside the mask
   fit scale-and-shift to the reference (least squares) and report RMSE (MiDaS-style
   scale-and-shift-invariant error), plus ordinal checks (rifle in front of vest, pouches proud of
   trousers, far shoulder behind near shoulder). Weight it low; it is a layering check, not a
   measurement.
7. **3DDFA (one-off, build time).** Align the 68 3D landmarks to the MPFB head and use the depth
   coordinates of nose tip, alae, cheekbones, gonions and menton as sparse 3D targets for the
   target search; optionally a low-weight shrinkwrap in the mid-face. Re-running it on renders is
   not useful — it will regress every render to the same generic face.

Needed in `setup_session.sh` / `assets/manifest.json` (none of the AI assets is in the manifest yet):
the venv recipe in §1 minus the two "not needed" lines, plus `face_landmarker.task`,
`canonical_face_model.obj`, `u2net.onnx`, and the Depth-Anything folder (total ≈ 280 MB of models,
≈ 2 min of downloads). 3DDFA is a one-off; keep the trimmed repo but it need not be in the manifest.

## 9. Disk: what to keep and what to delete

| Path | Size | Action |
|---|---|---|
| `assets/ai/sd_turbo/` | 2.5 GB | delete |
| `assets/ai/triposr/` | 1.7 GB | delete (repo, ckpt, torchmcubes_src) |
| `assets/ai/venv/` | 2.1 GB | keep; optionally `pip uninstall diffusers accelerate trimesh xatlas` (~80 MB). The duplicate `opencv-contrib-python` next to `opencv-python-headless` is ~200 MB and `numba`+`llvmlite` (206 MB, pulled by rembg's pymatting) are unused, but removing them risks breaking rembg/mediapipe imports — leave them |
| `assets/ai/3ddfa_v2/repo/{.git,examples,docs}` | 75 + 19 + 15 MB | delete → repo shrinks from 155 MB to ~46 MB |
| `assets/ai/rembg_models/models/u2net/` | 168 MB | keep |
| `assets/ai/rembg_models/models/bria-rmbg/` | 1.0 GB | delete (pulled in by TripoSR's run.py today; untested) |
| `assets/ai/triposr_out/` | 2 MB | keep as evidence or delete with the rest |
| `assets/ai/depth_anything_v2_small/` | 95 MB | keep |
| `assets/ai/mediapipe/selfie_multiclass_256x256.tflite` | 16 MB | delete (unused) |
| `assets/ai/mediapipe/face_landmarker.task`, `canonical_face_model.obj` | 3.8 MB | keep |
| `~/.cache/huggingface` | 48 KB | ignore |

Freed: ≈ 5.3 GB (free disk 19 GB → ≈ 24 GB).

## 10. Files written by this research

- `scripts/research/ai_face_landmarks.py`, `ai_3ddfa_run.py`, `ai_depth.py`, `ai_rembg.py`,
  `ai_render_obj.py` (Blender: `blender -b --python scripts/research/ai_render_obj.py -- <obj> <out_prefix> [samples]`;
  it normalises any mesh to 0.25 m and renders front / three-quarter / profile, clay and vertex-colour)
- `assets/ai/face_ref_*.{json,obj,png}`, `face_3ddfa_*.{obj,json,png}`, `soldier_full_depth16.png`,
  `soldier_full_depth_vis.png`, `rembg_out/soldier_full_u2net_{cutout,mask}.png`
- `renders/research/ai/face_3ddfa_{vcol,clay}_{front,threequarter,profile}.png`,
  `face_mediapipe_clay_{front,threequarter,profile}.png` (rendered today, 640², Cycles CPU 32 spp)
- `scripts/research/ai_triposr_run.py` + `ai_triposr_torchmcubes_shim.py` (research record only),
  `assets/ai/triposr_out/{soldier_full_triposr_mc128.obj,input_512.png,run.log}`,
  `renders/research/ai/body_triposr_{vcol,clay}_{front,threequarter,profile}.png`
