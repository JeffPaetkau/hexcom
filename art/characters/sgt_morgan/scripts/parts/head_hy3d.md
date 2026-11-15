# Head: Hunyuan3D 2 probe (2026-11-15)

Question (head.md §8): can Hunyuan3D 2 (Tencent's open-weight image-to-3D, shape only) run on the RTX 3050 and
turn gen/R001's views into a head shape good enough to carve what the MPFB fit lacks (the jaw line, the cheek
hollows, the nose, the lips)?

**Verdict.**
- **It runs, comfortably.** With CPU offload it uses 2.3-3.3 GiB of torch VRAM; the whole card peaks at 3.8-5.0 GB,
  about 1.2 GB of which is the desktop. One shape takes:
  - 13-29 s with the turbo models (5 steps, FlashVDM decoder);
  - 340-406 s with the 50-step multi-view model, where the plain volume decoder takes most of the time.
- **Use only the 50-step multi-view model, `Hunyuan3D-2mv`.** It gives a lean male head with these features:
  - the right silhouette (front width within 1-2 %, profile outline 4-6.5 mm rms against R001);
  - a square jaw with a real mandible edge and a crease into the neck;
  - a straight nose with a defined tip, and a squared chin.
- **It does not give a likeness by itself.** The eyes are blank slits. The stubble comes out as surface noise. The
  lips are generic and change from seed to seed. The cheek hollows are faint planes at most. The chin sits 2-7 mm
  behind R001's profile.
- **Seed noise is about the size of the detail we want.** Two seeds differ by 2.0 mm rms over the face (95th
  percentile 4 mm), about the depth of the hollows wanted (3 mm).
- **The turbo multi-view model is worse.** Its faces are puffy and pursed, and two seeds differ by 3.7 mm rms
  (95th percentile 7 mm).
- **The single-image `Hunyuan3D-2mini` is not usable.** From the front view alone it guesses the depth: the profile
  comes out 16 mm too shallow. From the hero crop it builds the collar into the neck.

**Recommendation.** Use the 50-step mv mesh as a **soft form prior** inside round 2's transfer. Average several
seeds. Let it act only where the outlines are blind (mandible edge, submental plane, cheek planes, nose dorsum), and
keep round 2's outline and landmark terms as the hard constraints (§6). Do not use it as a scan to snap onto. It is
not the likeness fix on its own. It is better evidence for the jaw and under-jaw than Depth Anything was, and about
as weak for the cheeks.

## 1. Licence (Tencent Hunyuan 3D 2.0 Community License Agreement)

Read from the repository's `LICENSE` (commit below). These terms matter for a private game made in Canada:

- **Territory**: "worldwide, excluding the European Union, United Kingdom and South Korea". Canada is inside it.
  Using, distributing or deploying the model outside the Territory is unlicensed, so a team member or contractor in
  the EU, UK or Korea could not run it.
- **Commercial use is allowed** royalty-free. A licence must be requested from Tencent only above 1 million monthly
  active users across everything made available by or for you, measured in the preceding calendar month.
- **Outputs**: "Tencent claims no rights in Outputs You generate". You are responsible for their use.
- **Acceptable Use Policy (Exhibit A), the two items that touch this project**:
  - Item 19, "For military purposes". A game character dressed as a soldier is entertainment, not a military
    purpose, so I read it as not forbidding this use. Jeff should confirm. It would matter if the model were ever
    sold to a defence customer, for example as a training simulation.
  - Item 12: content placed in a public context must be identified "expressly and conspicuously" as machine
    generated. What reaches the game is MPFB's mesh, displaced by a field fitted partly to a Hunyuan output. To be
    safe, credit it in the game's credits or notes ("head shape guided by Tencent Hunyuan3D 2"). That costs nothing.
- **Section 5(b)**: outputs must not be used to improve any other AI model. Fitting a shape key is not training a
  model. Do not feed these meshes into a model's training.
- **Distribution**: we do not redistribute the weights or code. If we ever did, the Notice file and the licence
  text would go with them. Hosting a public service with the model needs a provider disclosure (Section 3(e)).
- **Other terms**: Hong Kong law governs. The licence ends if you sue Tencent over IP in the model.

Nothing here forbids the use. No account was needed, and nothing was paid (PLAN.md decision 4).

## 2. What was installed (for scripts/setup later; setup itself is not edited)

| What | Source | Where | Size | sha256 |
|---|---|---|---|---|
| Code | `https://github.com/Tencent-Hunyuan/Hunyuan3D-2` (git clone --depth 1), commit `f8db63096c8282cb27354314d896feba5ba6ff8a` (2025-10-28) | `assets/ai/hunyuan3d/code/` | | |
| mv turbo DiT (+ DINOv2-giant conditioner, VAE) | `https://huggingface.co/tencent/Hunyuan3D-2mv/resolve/main/hunyuan3d-dit-v2-mv-turbo/model.fp16.safetensors` | `assets/ai/hunyuan3d/models/tencent/Hunyuan3D-2mv/hunyuan3d-dit-v2-mv-turbo/` | 4 930 777 530 | `172d7a989b99f66af760da0080d8c6f6350c72609536cf0c55b87a4afa574e45` |
| its config | `.../hunyuan3d-dit-v2-mv-turbo/config.yaml` | same | 1 667 | `4d9d7b21dd0669efd0a8da6024ecce28619b45a4ca5f3ea1394a54b3d38698f5` |
| **mv 50-step DiT (the useful one)** | `https://huggingface.co/tencent/Hunyuan3D-2mv/resolve/main/hunyuan3d-dit-v2-mv/model.fp16.safetensors` | `.../Hunyuan3D-2mv/hunyuan3d-dit-v2-mv/` | 4 928 151 562 | `d36f5881bcdc56726b73e517cd444c13c60732431622da7268145355c8d38e9c` |
| its config | `.../hunyuan3d-dit-v2-mv/config.yaml` | same | 1 608 | `315fd5bf601d1d103130b9fda202f1bd28eda495e68ed1621bc823d5519c5e5b` |
| turbo VAE (FlashVDM, used by the mv turbo) | `https://huggingface.co/tencent/Hunyuan3D-2/resolve/main/hunyuan3d-vae-v2-0-turbo/model.fp16.safetensors` | `.../Hunyuan3D-2/hunyuan3d-vae-v2-0-turbo/` | 407 410 402 | `66b7af697118db2de00c22f63a385c75f9049709739281971837af9e4ce31cb4` |
| its config | `.../hunyuan3d-vae-v2-0-turbo/config.yaml` | same | 336 | `91355c5acc412149996d19dbe46040d10fab888efd8bb910c76bad3a550f6ceb` |
| mini turbo DiT | `https://huggingface.co/tencent/Hunyuan3D-2mini/resolve/main/hunyuan3d-dit-v2-mini-turbo/model.fp16.safetensors` | `.../Hunyuan3D-2mini/hunyuan3d-dit-v2-mini-turbo/` | 3 822 584 202 | `bdbcef30dd0149a281e17d5b5b1fdad1122c904e098a42f3100e04e03c247bc4` |
| its config | `.../hunyuan3d-dit-v2-mini-turbo/config.yaml` | same | 1 664 | `be28205844da01bd5d3c5ba5160f5886fb9765d542483f9d12bda8f17324db5e` |
| mini turbo VAE | `https://huggingface.co/tencent/Hunyuan3D-2mini/resolve/main/hunyuan3d-vae-v2-mini-turbo/model.fp16.safetensors` | `.../Hunyuan3D-2mini/hunyuan3d-vae-v2-mini-turbo/` | 407 410 402 | `5dcaca67a8da9e7079fb7b55714a572d0651ac95983bb43099913feaf6738f94` |
| its config | `.../hunyuan3d-vae-v2-mini-turbo/config.yaml` | same | 335 | `75315e176c36b290b317f187a46adc08f01a7193836f8e77767eec76e868d2ab` |

- **Hashes**: every weight hash matches Hugging Face's LFS id for the file. The full list is in
  `assets/ai/hunyuan3d/sha256.txt`.
- **Layout**: the folders follow the code's own `HY3DGEN_MODELS/<repo>/<subfolder>/` layout, so with
  `HY3DGEN_MODELS=assets/ai/hunyuan3d/models` and `HF_HUB_OFFLINE=1` nothing is fetched at run time.
- **Total download**: 14.5 GB of weights.
- **For setup, only two entries are worth keeping**: the mv 50-step DiT, and the code at that commit. The mv
  50-step model carries its own VAE inside the checkpoint, so it needs no separate VAE.

**The venv, `cache/venv_hy3d`.**
- Built from Blender's bundled Python 3.11.15, the same base as `assets/ai/venv`.
- torch 2.14.1+cu130 and torchvision 0.29.1+cu130, from `https://download.pytorch.org/whl/cu130`. The driver is
  610.88 (CUDA 13.3).
- From PyPI: transformers **4.57.6**, diffusers **0.35.2**, huggingface_hub 0.36.2, accelerate 1.15.0, einops,
  omegaconf, pyyaml, tqdm, safetensors, trimesh 5.2.1, pymeshlab, scikit-image 0.26, opencv-python-headless.
- The full freeze is in `cache/hy3d/pip_freeze.txt`.

**Two version pins are required.**
- **transformers below 5.** transformers 5 renamed DINOv2's attention modules (`attention.attention.query` became
  `attention.q_proj`), so the checkpoint's conditioner keys no longer load.
- **diffusers below 0.36.** diffusers 0.43 wants huggingface_hub 1.x, which transformers 4.57 refuses.

No CUDA extensions were built: no custom_rasterizer and no texture stage.

## 3. Scripts and settings (probe tools, in `cache/hy3d/`, not pipeline code)

- **`prep_inputs.py`** (AI venv) prepares the inputs:
  - rembg u2net mattes; the neck is cut 0.22 × (nasion to menton) below the chin, above the T-shirt;
  - each view is scaled to nasion-menton = 330 px, nasion at row 400 on a 1024² RGBA canvas;
  - two 1/255-alpha pixels pin every view's bbox to rows 20 and 804. Hunyuan's `recenter()` rescales each view by
    its own bbox, and without the pins the hair would set the scale per view;
  - the anchors are MediaPipe 168 and 152 for front and three-quarter; for the profile, the silhouette's deepest
    brow-nose point and the chin-to-under-chin turn.
  - The R001 views measured 444 / 429 / 436 px nasion to menton before scaling, consistent within 3 %.
  - The inputs are `cache/hy3d/inputs/{front,left,tq,hero}.png`; the sheet is `inputs_sheet.png`.
- **View mapping.** The multi-view model's `left` is the view with the nose to the viewer's left, as in its own
  examples. That is exactly R001's `profile_left.png`, so **no mirroring for `left`**. The model has no
  three-quarter slot, so `threequarter_left.png` cannot be used. One variant adds the profile **mirrored** as
  `right` (`right_mirror.png`), which assumes the face is symmetric.
- **`run_hy3d.py`** (cache/venv_hy3d) runs the model:
  - `--model mv|mv50|mini`, `--jobs` (several runs per process), fp16;
  - offload is accelerate's `cpu_offload_with_hook`, chained by hand: conditioner, then DiT, then VAE, one on the
    GPU at a time. The pipeline's own `enable_model_cpu_offload` fails because the class lacks diffusers'
    `.components`. `pipe.device` is set to cuda afterwards, because `__call__` creates its latents on it;
  - turbo runs use FlashVDM (`mc`), 5 steps; mv50 runs use 50 steps; guidance 5, octree 256 or 380, 8000 chunks;
  - FloaterRemover and DegenerateFaceRemover clean the result;
  - each run writes `<mesh>.json` (times, VRAM) and `<mesh>_smi.log` (nvidia-smi every 0.5 s).
- **`render_hy3d.py`** (Blender, Workbench clay with cavity, orthographic, transparent, 1024²) renders `front`,
  `left`, `right`, `tq` (32°, R001's solved turn), `tq45`, and an `_axes` mode. The meshes come out facing −Y after
  glTF import, so no yaw is needed. The single-image meshes from the hero and three-quarter crops were turned by
  −20° and +32°.
- **`compare.py`** (AI venv) makes the sheets and the numbers:
  - sheets: R001 | clay | 50 % blend | silhouettes (R001 red, mesh green, nasion and menton lines blue);
  - the render is scaled to the input's silhouette height and placed on its bbox, as Hunyuan framed it;
  - the profile outline is measured from the brow (row 330) to just above the menton (row 722), with outline
    features at the brow, nose, lips and chin;
  - front widths are taken at three rows;
  - mm assume nasion to menton = 123 mm (ANSUR II menton-sellion, male mean), because R001 carries no scale of its
    own.
- **`seed_spread.py`** (cache/venv_hy3d) measures the face-region surface distance between two meshes in the shared
  normalised frame (no alignment).

## 4. Runs (cache/hy3d/*.glb; the mesh unit is about 143 mm)

| Mesh | Model, views | Load | Gen | Torch peak | Card peak (start) | Faces |
|---|---|---|---|---|---|---|
| mv_fl_o256 | mv turbo, front+left, octree 256 | 34 s (4.5 min cold) | 29 s | 2.33 GiB | 3.78 GB (1.23) | 0.54 M |
| mv_fl_o380 | mv turbo, front+left, 380 | | 18 s | 2.92 | 4.38 | 1.24 M |
| mv_flr_o380 | mv turbo, front+left+mirrored right | | 20 s | 2.98 | 4.46 | 1.26 M |
| mv_fl_o380_s7 | mv turbo, front+left, seed 7 | | 17 s | 2.92 | 4.38 | 1.27 M |
| **mv50_fl_o380** | mv 50-step, front+left | 112 s | 406 s | 2.58 | 4.40 | 1.18 M |
| **mv50_fl_o380_s7** | mv 50-step, seed 7 | | 338 s | 3.19 | 4.70 | 1.18 M |
| **mv50_flr_o380** | mv 50-step, front+left+mirrored right | | 391 s | 3.31 | 4.98 | 1.21 M |
| mini_front_o380 | mini turbo, front.png only | 180 s | 16 s | 2.41 | 3.83 | 0.92 M |
| mini_hero_o380 | mini turbo, ref/crop_head_face.png | | 13 s | 3.00 | 4.45 | 1.23 M |
| mini_tq_o380 | mini turbo, threequarter_left.png | | 17 s | 3.00 | 5.45* | 1.04 M |

- **The asterisk**: another agent's `assemble.py --round 3` was running alongside. The "start" column includes
  memory still held from earlier jobs in the same process.
- **No out-of-memory at any setting.** The DINOv2-giant conditioner (2.2 GB fp16) and the DiT (~2.3 GB) never sit
  on the card together.
- **Where the time goes in mv50**: its plain volume decoder, 6914 chunks at octree 380. It would drop to seconds
  with the turbo FlashVDM VAE swapped in (`enable_flashvdm`), which has not been tried with the 50-step DiT.

## 5. Results

Renders are in `renders/head/hy3d/`. Every sheet below was opened and looked at; each single-view PNG appears tiled
in a sheet.

**`mv_fl_o256_axes_sheet.png`, the turbo model at 6 azimuths.**
- A complete head: skull, ears with inner detail, a neck stump, and the hair as a lumpy volume.
- The face looks forward (−Y).

**`mv_fl_o380_vs_r001.png`, `mv_fl_o380_face4.png`, `mv_fl_o380_s7_face4.png`, `mv_flr_o380_face4.png` (turbo).**
- The outlines are good in all three views.
- The face is wrong: swollen squinting eyes, a pursed and distorted mouth, nostril holes, lumpy cheeks. It reads
  like a puffy boxer, not the lean man.
- Seeds change the mouth and nose outright.

**`mv50_fl_o380_vs_r001.png`, `mv50_fl_o380_face4.png`, `mv50_fl_o380_s7_face4.png`, `mv50_flr_o380_vs_r001.png`,
`mv50_flr_o380_face4.png` (50-step).** A clear step up. Against the questions asked:

| | Present? |
|---|---|
| Long lean face | Yes, narrower and longer than MPFB's round-2 head (`renders/head/head_r2_rest_*_clay.png`); front widths 187-189 mm at eye level (ears included) against R001's 185, 131-136 at the mouth and jaw against 135 |
| Square jaw line, mandible edge | **Yes**: a defined lower border of the mandible, a gonial corner and a shadowed crease into the neck in the three-quarter and profile renders. This is what MPFB lacks most |
| Cheek hollows | Weak: a flat plane below the zygoma and a nasolabial fold, no real hollow. Seeds differ here |
| Straight nose | Yes: a straight dorsum and a defined tip, narrower than MPFB's fleshy tip |
| Lips | Generic, thin-ish; the moustache region is noisy. Not trustworthy |
| Eyes | Blank lidless slits (expected: the eyes are not a shape the model can see) |
| Profile | Close but retruded: see the numbers |

**`mini_front_o380_vs_r001.png`, `mini_face4_all.png` (single image).**
- From the front alone, the head is far too shallow front to back, and the face is a generic frowning mask with
  vertical streak artefacts.
- The hero-crop mesh includes the collar as a ring.
- The three-quarter mesh is a broad frog-like face, with a floating ear fragment.

**Profile outline against R001** (brow to row 722; + means the mesh lies behind R001's outline), from
`cache/hy3d/*_cmp.json`:

| Mesh | rms | mean | glabella | nasion | nose tip | subnasale | upper lip | lower lip | pogonion |
|---|---|---|---|---|---|---|---|---|---|
| mv_fl_o380 | 5.3 | +4.4 | +1.9 | −0.8 | +5.6 | +1.9 | +4.5 | +7.5 | +3.0 |
| mv_fl_o380_s7 | 3.7 | +2.3 | −0.8 | −2.2 | +3.4 | +4.5 | +4.1 | +5.2 | +1.1 |
| mv_flr_o380 | 4.9 | +2.7 | +0.4 | −3.7 | +4.1 | −1.5 | +1.1 | +6.7 | +3.0 |
| mv50_fl_o380 | 6.5 | +4.9 | +4.1 | −0.8 | +1.5 | +4.1 | +7.1 | +7.5 | +7.1 |
| mv50_fl_o380_s7 | 5.2 | +1.3 | −2.6 | −4.9 | −0.4 | −0.4 | +1.9 | +3.4 | +6.0 |
| **mv50_flr_o380** | **4.1** | −0.1 | −1.9 | −7.1 | −3.0 | +0.8 | +1.9 | +3.4 | +2.2 |
| mini_front_o380 | 17.8 | +16.3 | +10 | +8 | +14 | +19 | +21 | +21 | +26 |

- **The comparison baseline**: round 2's MPFB head fits this outline to 1.90 mm (head.md §6.3). That was a fit to
  this very data with its camera solved, so it is not a like-for-like comparison, but the order is clear: Hunyuan's
  profile is a looser match than the current model.
- **The systematic error**: lips and chin sit 2-7 mm too far back, and the nasion is too deep with the mirrored
  view.
- **A failed alternative measure**: a two-point (nasion-pogonion) similarity fit instead of the bbox framing did not
  lower the residual (5-10 mm), so the error is shape, not framing.

**Spread over the face, brow to menton, forward-facing** (`seed_spread.py`, no alignment):

| Pair | rms | median | p95 |
|---|---|---|---|
| mv50 seed 12345 vs seed 7 | 2.0 mm | 1.5 | 4.1 |
| mv turbo seed 12345 vs seed 7 | 3.7 | 2.7 | 7.2 |
| mv50 front+left vs + mirrored right | 3.3 | 3.1 | 5.0 |
| mv50 vs mv turbo (same seed) | 4.5 | 2.1 | 10.4 |
| mv turbo octree 256 vs 380 (same latents) | 3.3 | 2.9 | 5.2 |

The last row is mostly a rigid offset between the two marching-cubes grids, so it is not shape. An ICP-aligned
spread would be a little lower throughout.

## 6. How the mesh would go onto MPFB's head (round 3, if Jeff wants it)

The same machinery as round 2's `head_shape.py`, which was itself take 1's foot transfer
(`scripts/stages/foot/transfer.py`): one smooth displacement field on MPFB's own head vertices, so the topology, UVs,
groups, weights, helpers and MHCLO assets are untouched. The result is a new or updated `head-shape.target`, loaded
by base.py exactly as §6.6 describes.

1. **Make a prior, not a scan.**
   - Generate 4-6 seeds of `mv50` with front + left; add mirrored right only if its deeper nasion is accepted.
   - Align them to each other by ICP and average them as signed-distance fields (or average point-to-mesh offsets
     on one of them). Averaging cancels some of the 2 mm seed noise.
   - Swap in the turbo VAE's FlashVDM decoder to cut the 6-minute decode, after checking that it changes nothing
     visible.
2. **Mask the prior.** Use only the regions the outlines cannot see:
   - the mandible's lower border, the gonial corner and the submental plane down to the neck crease;
   - the cheek planes below the zygoma; the nasal dorsum and alae; the chin's front.
   - Exclude the eyes and lids, the lips and moustache, the hair (everything above the hairline, which Hunyuan
     makes as a solid volume), the ears and the neck cut.
3. **Align the prior to MPFB's head** with a similarity transform (scale free). Fit it on landmarks found by the same
   detector on both: MediaPipe on a front render of each, plus the profile outline features (glabella, nasion,
   pronasale, pogonion) on a side render of each. Then refine by ICP over the masked region.
4. **Add the data term.** For each masked MPFB skin vertex, take the signed distance along its normal to the
   prior's surface:
   - sigma about 2.5-3 mm (the seed spread);
   - a Huber loss, clipped at 5 mm a round like the relief term;
   - weighted below the outline and landmark terms, which stay exactly as in round 2;
   - the bending energy, the symmetry, the held skull top and cranium, and the zero neck ring all stay.
5. **Check it like round 2.**
   - The hero and R001 numbers (§6.3) must not get worse; the profile outline is the one that can.
   - Render `head_r2_`-style clay and Cycles sheets and look for a jaw edge, a neck crease and a narrower nose tip.
   - The cheeks will probably still want the explicit sub-zygomatic sculpt (§7 item 1, spec 06 §3.3), because the
     prior is weak there.

**Cost.** About 30-40 min of GPU time for six 50-step seeds, or a few minutes with FlashVDM. The transfer is a new
term in `head_shape.py` (not written: this probe changes no pipeline code). Setup would fetch one 4.9 GB checkpoint
and the code, and build the cu130 venv with the two pins above.

## 7. What was not done

- The 50-step model with the FlashVDM turbo VAE was not tried.
- Higher guidance was not tried.
- No back view: ChatGPT could make one (R004). It would mostly help the skull, not the face.
- No ICP-aligned spread.
- No transfer onto MPFB; nothing in `scripts/stages/`, base.py or assemble.py was touched, and nothing was
  committed.
