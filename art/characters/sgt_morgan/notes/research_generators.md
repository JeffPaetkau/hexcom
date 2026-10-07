# Research B — Character generators in Blender 4.5 headless (MPFB2, CharMorph)

Date: 2026-10-06. Blender 4.5.14 LTS, Linux, 4 CPU cores, no GPU. Everything below was run, not guessed.
Scripts: `scripts/research/mpfb_install.py`, `mpfb_build_v2.py`, `mpfb_rigify_test.py`, `mpfb_face_render.py`, `charmorph_test.py`,
`mpfb_setup_from_zero.sh`, `mpfb_inspect_blend.py`. Logs and renders: `renders/research/`.
Target/asset inventory: `notes/mpfb_targets_and_assets.txt` (1,534 lines).

## TL;DR / recommendation

* **MPFB 2.0.17 installs and runs fully headless in 4.5** (extension `bl_ext.user_default.mpfb`). Human creation,
  macro + detail targets, skin material, body parts, clothes, the "default" rig **and a full Rigify generate** all
  work from Python with no UI. Whole character build (no render) is **7.5 s**.
* **Reproducing the install from zero: ~600 MB download, ~3 min wall clock** (download at the measured 9 MB/s +
  7 s extraction + ~10 s Blender install). `scripts/research/mpfb_setup_from_zero.sh` does it idempotently.
* **Realism verdict (face closeups rendered and viewed, section 5): MPFB gives a correct, well-proportioned, riggable base
  head, but out of the box it is an obvious MakeHuman face** — flat 2 K painted skin with no pores/normal map (lit cheek `#ebd6cb`
  vs reference `#c5907d`), soft bone structure, cartoon procedural eyes, felt-cap hair and card eyebrows. Targets fix the
  proportions (every slider in the face analysis exists except brow-ridge protrusion and jaw width/angle); skin, lines, hair,
  stubble and eyes must be ours. CharMorph's default face is a little better (pore noise, textured iris) but still pale and
  generic, 5× slower to render, bald, and AGPL3.
* **CharMorph (MB-Lab successor) also loads in 4.5** as a *legacy* add-on (`bl_info` says Blender 3.3, last commit
  2024-10-10, no 4.x-format release, no `blender_manifest.toml`): enable 0.7 s, `mb_male` import 3.2 s, no errors.
  Its skin shader (`charmorph_skin_v2`, MB-Lab albedo/displacement/sebum maps) is more sophisticated than MPFB's
  default; its MB-Lab morph set is finer for faces (Cheeks_Zygom, Jaw_Prominence, Eyes_BagProminence, ...). But
  it is AGPL3 for the mb_male data, has a 734 MB data repo, and its Python API is UI-centric (operators driven by
  `window_manager.charmorph_ui`).
* **Plan recommendation:** use **MPFB** as the body generator (CC0 assets, clean service API, MakeHuman topology,
  built-in Rigify metarig and 930-bone generated rig, 2 s). Treat its face only as a base to be reshaped by
  targets + a projected/baked skin texture; do **not** use MakeHuman hair/beard/clothes assets for the final
  model (they are the main source of the "awful" look). Keep CharMorph as a fallback for a nicer skin shader.

---

## 1. Installing MPFB2 headless (verified)

### 1.1 Finding the package

```
curl -sS "https://extensions.blender.org/api/v1/extensions/?search=mpfb"
# -> id "mpfb", version "2.0.17", blender_version_min "4.2.0",
#    archive_size 45031536, archive_hash sha256:4f0a879d64a39bf646fbf5f53601ac678855da329d650617dca5737548239a87
#    archive_url:
https://extensions.blender.org/download/sha256:4f0a879d64a39bf646fbf5f53601ac678855da329d650617dca5737548239a87/add-on-mpfb-v2.0.17.zip
```
Local copy: `/home/user/sgt_morgan/assets/mpfb/add-on-mpfb-v2.0.17.zip` (45,031,536 bytes, zip test OK).
The full catalogue (`/api/v1/extensions/`, 1,485 entries) has no CharMorph, MB-Lab or MakeHuman entry; MPFB is the
only character generator on extensions.blender.org.

### 1.2 Install + enable (scripts/research/mpfb_install.py)

```python
# blender -b --python mpfb_install.py -- /home/user/sgt_morgan/assets/mpfb/add-on-mpfb-v2.0.17.zip
import bpy
bpy.context.preferences.system.use_online_access = True          # harmless; not needed for file install
bpy.ops.extensions.package_install_files(filepath=zip_path, repo="user_default",
                                         enable_on_install=True, overwrite=True)
bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")
bpy.ops.wm.save_userpref()
```
Result paths (Blender 4.5):
* extension code: `~/.config/blender/4.5/extensions/user_default/mpfb/` (84 MB unpacked, `blender_manifest.toml`
  id=mpfb version=2.0.17, build info 20260722)
* **MPFB user data (where asset packs go):** `~/.config/blender/4.5/extensions/.user/user_default/mpfb/data/`
  (= `LocationService.get_user_data()`); subdirs `clothes eyebrows eyelashes eyes hair packs proxymeshes skins
  teeth tongue` (+ `targets/custom` for your own targets)
* MPFB config/logs: `~/.config/blender/4.5/mpfb/{config,logs}`
* `userpref.blend` keeps it enabled, but every headless script should still do
  `bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")` defensively (0.0 s when already on).
Alternative without the operator: unzip the archive into `~/.config/blender/4.5/extensions/user_default/mpfb/`
(the zip root *is* the add-on folder) and run `addon_enable` — same result.

### 1.3 MakeHuman asset packs (verified URLs and sizes)

MPFB 2.0.17 has **no built-in downloader**; its UI only links to
`http://static.makehumancommunity.org/assets/assetpacks.html`. Each pack page links to
`https://files.makehumancommunity.org/asset_packs/<pack>/<pack>_cc0.zip` (mirror: `https://files2.makehumancommunity.org/...`).
All zips have `packs/<pack>.json` plus `skins/ eyes/ clothes/ ...` at the root, so **`unzip -o pack.zip -d $USERDATA`**
installs them (this is what MPFB's `AssetService.fix_and_extract_asset_pack_zip(zip, userdata)` does too).
`AssetService.check_asset_pack_zip(zip)` returns None when the zip is valid.

Installed now (HEAD Content-Length verified == local size, 2026-10-06):

| pack | bytes | contents relevant to us |
|---|---:|---|
| makehuman_system_assets | 280,737,770 | base skins (young/middleage/old × caucasian/asian/african × m/f), eyes (high-poly, low-poly), 12 eyebrows, 3 eyelashes, teeth, tongue, 10 hair (short01-04, bob, long, ponytail...), proxies, worksuit/casualsuits, shoes01-06 |
| skins02 | 76,112,708 | 20 extra male skins (mindfront_*, toigo_*, jartur69_*, ken1138_*...) |
| bodyparts05 | 6,616,507 | beards/moustaches (`wdg_scruffy_beard`, `rehmanpolanski_beard_viking`, `grinsegold_beard_sigmund_wip`, `culturalibre_faun_beard`) |
| eyebrows01 | 11,477,790 | `mindfront_eyebrows_01..14` |
| eyelashes01 | 3,493,692 | eyelashes01-03 (+6 more variants) |
| pants01 | 21,908,723 | `cortu_cargo_pants`, jeans shorts, harem, wool pants |
| shirts01 | 24,479,483 | crude t-shirt, polo, tucked t-shirt, fisherman sweater, tops |
| shoes01 | 82,953,569 | `culturalibre_male_boots`, hero boots 1-5, ankle boots, flats |
| gloves01 | 3,192,691 | `toigo_gloves_short/medium/long`, `culturalibre_hero-heroine_gloves_1-5`, MMA gloves |
| hats02 | 24,018,546 | helmets (`mrgreaterthan_m1_helmet`, motorcycle, warrior, templar, corinthian), fedoras |
| equipment01 | 18,111,388 | weapons/tools (crude sword, dagger, war hammer, bow, kalistick, sceptre) |
| **total** | **553,102,867** | **598,134,403 with the add-on zip; 620 MB extracted** |

Other packs that exist (200 OK, not downloaded): system_clothes_materials01 48.2 MB, system_hair_materials01 86.8 MB,
skins01 (female) 104.2 MB, skins03 136.8 MB, hair01 227.8 MB, bodyparts04 (nails) 4.6 MB, hats01 6.6 MB,
suits01 42.6 MB, suits02 192.5 MB, underwear04 5.6 MB, glasses01 5.8 MB, masks01 4.3 MB,
realistic deformation target packs: arms01 0.21 MB, cheek01 0.35 MB, ears01 0.57 MB, hands01 0.18 MB, nose01 1.3 MB,
poses01 1.2 MB. **404** (listed on the site but no `_cc0.zip`): hair02/03, pants02/03, shirts02/03, shoes02/03,
hats03/04, suits03, equipment02/03, underwear03, masks02, faceunits01, visemes01 (these are CC-BY packs named
`<pack>_cc-by.zip`, not checked).

### 1.4 Reproduce from zero: time and bytes

```
bash scripts/research/mpfb_setup_from_zero.sh      # idempotent; re-run skips complete files
```
Measured components: download 9 MB/s on a 24 MB file (1.8 MB/s on a 3 MB one, latency-bound) -> 598 MB ≈ 70–120 s;
`unzip` of the 280 MB system pack 6.7 s wall (287 MB on disk); extension install + userpref save ≈ 10 s of Blender
start-up. **Budget 3 minutes and 600 MB of downloads, 700 MB of disk** (plus Blender itself, 2 min, already in
`setup_session.sh`). Verification at the end prints `system assets installed: True` and the 11 pack names.

---

## 2. MPFB Python API that works (scripts/research/mpfb_build_v2.py, log mpfb_v2_build.log)

```python
import bpy
bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")
from bl_ext.user_default.mpfb.services.humanservice  import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
from bl_ext.user_default.mpfb.services.assetservice  import AssetService
from bl_ext.user_default.mpfb.services.locationservice import LocationService
from bl_ext.user_default.mpfb.entities.objectproperties import HumanObjectProperties

# --- macro targets. MakeHuman age macro: 0.0=1y, 0.1875=11y, 0.5=25y, 1.0=90y  (40 y -> 0.615)
macro = TargetService.get_default_macro_info_dict()
macro.update({"gender": 1.0, "age": 0.5 + 0.5*(40-25)/65, "muscle": 0.7, "weight": 0.45,
              "proportions": 0.5, "height": 0.5, "cupsize": 0.5, "firmness": 0.5,
              "race": {"caucasian": 1.0, "asian": 0.0, "african": 0.0}})
basemesh = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                     feet_on_ground=True, scale=0.1, macro_detail_dict=macro)   # 0.9 s
# scale=0.1 -> metres (MakeHuman is in decimetres). Mesh: 19,158 verts incl. helpers; 'Hide helpers' MASK
# modifier leaves the 'body' group (8,428 verts). Faces -Y, origin between the feet. 13,380 body polys (quads).

# change a macro later:
HumanObjectProperties.set_value("height", 0.579, entity_reference=basemesh)
TargetService.reapply_macro_details(basemesh)
# height macro is ~linear: 0.5 -> 174.0 cm, 0.9 -> 229.4 cm, so 185 cm ≈ 0.58 (measure the EVALUATED mesh:
# macro targets are shape keys, obj.data.vertices never changes).

# --- detail targets (face, measurements). NAME = file stem under data/targets/<cat>/, no category prefix.
for name, w in [("chin-width-incr", .35), ("chin-prominent-incr", .3), ("head-square", .3),
                ("nose-width1-decr", .2), ("l-cheek-bones-incr", .4), ("r-cheek-bones-incr", .4),
                ("measure-shoulder-dist-incr", .3), ("measure-neck-circ-incr", .3)]:
    TargetService.load_target(basemesh, TargetService.target_full_path(name), weight=w)
TargetService.bulk_load_targets(basemesh, [{"target": "forehead-scale-vert-decr", "value": 0.15}])
TargetService.set_target_value(basemesh, "chin-width-incr", 0.5)    # only CHANGES a loaded key
TargetService.get_target_stack(basemesh)   # [{'target': ..., 'value': ...}] (macro names are $-encoded)
# Pitfalls found: v1 used "nose/nose-width-incr" -> "Did not find matching target"; and set_target_value
# on a not-yet-loaded target is a silent no-op. There is no 'nose-width-incr': it is nose-width1/2/3-incr.
# Negative values: load the *-decr twin with a positive weight (MakeHuman convention).

# --- skin (mhmat from any pack). skin_type: "ENHANCED_SSS" | "ENHANCED" | "MAKESKIN" | "GAMEENGINE" | "LAYERED"
skin = AssetService.find_asset_absolute_path("middleage_caucasian_male/middleage_caucasian_male.mhmat", "skins")
HumanService.set_character_skin(skin, basemesh, skin_type="ENHANCED_SSS", material_instances=True)  # 1.9 s

# --- rig. builtin names: cmu_mb, default, default_no_toes, game_engine, game_engine_with_breast, mixamo,
#     mixamo_unity, openpose; rigify.human, rigify.human_toes (need bpy.ops.preferences.addon_enable(module="rigify"))
rig = HumanService.add_builtin_rig(basemesh, "default", import_weights=True)   # 163 bones, 0.7 s; parents mesh

# --- body parts and clothes (same call; asset_type is the subdir). material_type "MAKESKIN" or "PROCEDURAL_EYES"
def add(subdir, frag, mat="MAKESKIN"):
    p = AssetService.find_asset_absolute_path(frag, asset_subdir=subdir)
    return HumanService.add_mhclo_asset(p, basemesh, asset_type=subdir, subdiv_levels=1, material_type=mat)
eyes = add("eyes", "high-poly/high-poly.mhclo", "PROCEDURAL_EYES")
add("eyebrows", "eyebrow006/eyebrow006.mhclo"); add("eyelashes", "eyelashes02/eyelashes02.mhclo")
add("teeth", "teeth_base/teeth_base.mhclo");    add("tongue", "tongue01/tongue01.mhclo")
add("hair", "short04/short04.mhclo")
add("clothes", "cortu_cargo_pants/cortu_cargo_pants.mhclo")   # adds 'Delete.<asset>' MASK modifier on the body
```
Objects are named `Human.<asset>` and parented to `Human.rig`; each gets Armature + Subdivision modifiers and is
fitted to the current shape (MPFB refits clothes to targets automatically; `HumanService.refit(obj)` otherwise).

**Rigify (scripts/research/mpfb_rigify_test.py, log mpfb_rigify_test.log):**
```python
bpy.ops.preferences.addon_enable(module="rigify")
metarig = HumanService.add_builtin_rig(basemesh, "rigify.human", import_weights=True)   # 185 bones, 1.6 s
bpy.context.view_layer.objects.active = metarig; metarig.select_set(True)
bpy.ops.pose.rigify_generate()        # {'FINISHED'} in 2.1 s -> 'Human.rigify', 930 bones (IK/FK, torso, tweaks)
```
Total script 6.1 s. (After generating, point the Armature modifiers at `Human.rigify`; MPFB's UI operator does that,
`RigService.ensure_armature_modifier(obj, rig)` exists.)

**Timings (4 cores):** create_human 0.9 s, height fit 0.6 s, 20 detail targets 0.5 s, skin 1.9 s, rig 0.7 s,
6 body parts 0.8 s, 4 clothes 2.0 s = **7.5 s to a dressed, rigged human**. Cycles CPU 64 spp + OIDN denoise:
full body 900×1600 = 179 s (25 s in v1 with fewer assets and no beard; this run competed with a CharMorph import);
face 1024×1024 ≈ 15 s/sample ⇒ ~16 min at 64 spp (ENHANCED_SSS skin + hair + beard transparency are expensive —
for iteration use 16–32 spp or 512², and prefer EEVEE for layout checks).

**Known 4.5 noise:** `PROCEDURAL_EYES` logs `[ERROR] nodeservice: Found an input name which didn't exist as socket:
Scale/Exponent/Smoothness/W` for Vector Math / Voronoi nodes (4.x socket renames). The eye material still renders
(blue iris visible in both renders); treat as cosmetic.

**Camera placement gotcha (why v1's "face" render showed trousers):** once clothes are added, the body mesh carries
`Delete.<asset>` MASK modifiers, so the evaluated body spans only the uncovered region (z 0.996–1.828 in v1). Measure
height **before** adding clothes, or anchor on another object (v2 anchors cameras on the eyes object's evaluated
bounds: centre (0.000, −0.139, 1.717) for a 182.4 cm body).

Bugs/limits noticed: `HumanService.add_builtin_rig` keeps the mesh at origin and moves the armature; detail targets
loaded after `create_human` require re-grounding (`deserialize_from_dict` does this with `ObjectService.get_lowest_point`).
`cortu_cargo_pants` (pants01) imports with only 211 verts and renders with alpha holes on the thighs (skin visible);
`wdg_scruffy_beard` is a chunky polygon beard, not stubble; `short04` hair is a flat cap mesh.

## 3. Target inventory (dumped to notes/mpfb_targets_and_assets.txt)

Bundled targets, 1,214 files in 24 categories (counts): arms 50, asym 62, breast 228, buttocks 2, **cheek 16,
chin 15, ears 44, eyebrows 6, eyes 68, forehead 8, head 27, mouth 44, neck 20, nose 42**, expression 102, feet 30,
genitals 6, hands 22, hip 14, legs 58, macrodetails 348 (99 race-gender-age + universal muscle/weight/height
combos), pelvis 4, stomach 8, torso 34. Measurement targets (20 pairs): measure-{ankle,bust,calf,hips,knee,neck,
thigh,underbust,upperarm,waist,wrist}-circ, -{frontchest,napetowaist,shoulder,waisttohip}-dist,
-{lowerarm,upperarm}-length, -{lowerleg,upperleg,neck}-height, each `-decr/-incr`.
Face examples: `chin-{bones,cleft,height,jaw-drop,prognathism,prominent,width}-{decr,incr}`, `chin-triangle`;
`head-{age,fat,scale-depth/horiz/vert,back-scale-depth,trans-*}`, `head-{oval,round,square,rectangular,triangular,
invertedtriangular,diamond}`; `nose-{base,compression,curve,flaring,greek,hump,nostrils-angle,nostrils-width,
point,point-width,scale-*,septumangle,trans-*,volume,width1,width2,width3}`; `l-/r-cheek-{bones,inner,trans-down/
up,volume}`; `l-/r-eye-{bag-decr/incr/in/out,corner1/2-*,eyefold-*,height1/2/3-*,push1/2-*,scale-*,trans-*}`;
`mouth-{angles,cupidsbow,dimples,laugh-lines,lowerlip-*,upperlip-*,philtrum-*,scale-*,trans-*}`; `l-/r-ear-*`;
`forehead-{nubian,scale-vert,temple,trans-*}`; `eyebrows-{angle,trans-*}`. Extra realistic deformation packs exist
online (cheek01, nose01, ears01, arms01, hands01 — 2.6 MB total) and install into `targets/` via the same unzip.

Installed assets: 36 skins, 11 eyes, 26 eyebrows, 9 eyelashes, 6 teeth, 1 tongue, 10 hair, 85 clothes (incl. 4 beards,
8 gloves, ~25 shoes/boots, 7 helmets, weapons), 0 proxymeshes in packs list (system proxies live under
`proxymeshes/`, 7 dirs: female_generic, male_generic, ... ).

## 4. CharMorph (MB-Lab successor) in Blender 4.5

Facts: GitHub `Upliner/CharMorph` HEAD ec5e13d (2024-10-10 "Some compatibility issues"), `bl_info` version 0.3.5,
`"blender": (3, 3, 0)`; **no `blender_manifest.toml`, no 4.x release** — it is a legacy add-on. Data lives in the
submodule `Upliner/CharMorph-db` (HEAD a8512ac, 2023-12-11; 734 MB checkout, no LFS). The GitHub REST API and
releases HTML are blocked by this container's proxy (the `gh` CLI too), but anonymous `git clone` and
`raw.githubusercontent.com` work:
```
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/Upliner/charmorph   /home/user/sgt_morgan/assets/charmorph/CharMorph       # 1.3 MB, 2 s
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/Upliner/CharMorph-db /home/user/sgt_morgan/assets/charmorph/CharMorph/data  # 734 MB, 36 s
```
Install = symlink/copy the folder to `~/.config/blender/4.5/scripts/addons/CharMorph`, then
`bpy.utils.refresh_script_paths(); bpy.ops.preferences.addon_enable(module="CharMorph")`
(first attempt failed with "No module named 'CharMorph'" only because the freshly created `scripts/addons` dir was
not on `sys.path`). Result: **enable 0.7 s, no exceptions**; the addon_updater writes a settings JSON. Import:
```python
ui = bpy.context.window_manager.charmorph_ui
ui.base_model = "mb_male"            # library.chars: antonia, mb_female, mb_male, reom
bpy.ops.charmorph.import_char()      # {'FINISHED'} 3.2 s -> object 'mb_male', 17,996 verts, materials
# charmorph_skin_v2, charmorph_censor, MBlab_eyelash, MBlab_pupil, MBlab_human_eyes, charmorph_cornea,
# charmorph_iris, MBLab_tongue, MBlab_human_teeth, charmorph_nails_v2 (eyes/teeth/tongue are part of the mesh)
from CharMorph import common; m = common.manager.morpher   # m.core: L1 'Caucasian', L2 morphs via m.core.morphs_l2
```
Morph data: `characters/mb_male/morphs/L1/{African,Asian,Caucasian,Latin,Anime,Dwarf,Elf}.npy`,
`L2_packed/*.npz` (MB-Lab names such as Cheeks_Zygom, Chin_Prominence, Jaw_ScaleX, Eyes_BagProminence,
Nose_*, Mouth_*, Head_CraniumDolichocephalic — listed in `morphs_meta.yaml` with age/mass/tone coefficients).
Rigging: `config.yaml` armature types `tweaked` (Rigify metarig from `shared_lib.blend`), muscles, original, gaming.
Licence: mb_male data is **AGPL3** (MB-Lab), textures `assets/albedo.png, displacement.png, sebum.png, ...`.
Face render: `renders/research/charmorph_face.png` (768², Cycles 32 spp denoised, **132.5 s** — the `charmorph_skin_v2` shader
costs ~3× MPFB's ENHANCED_SSS per sample); scene saved as `charmorph_test.blend`. Default `mb_male` is 183.3 cm, faces −Y,
feet on z≈0, 207 L2 morphs (`common.manager.morpher.core.morphs_l2` is a *list* of morph objects, not a dict). Judgement in section 5.

## 5. Realism judgement (renders looked at with the Read tool, beside ref/crop_head_face.png)

Renders used (all Cycles CPU, OIDN denoised, AgX Medium High Contrast, 85 mm lens 0.60 m from the eye centre, 3/4 view from
the soldier's right-front like the reference crop):

| file | what | cost |
|---|---|---|
| `renders/research/mpfb_v2_face.png` | MPFB **macro-only default male** from `mpfb_default.blend` (gender 1, age 0.554 ≈ 32 y, muscle 0.7, weight 0.5, caucasian; the v1 detail targets never loaded, so the mesh has only Basis + 8 macro keys), `middleage_caucasian_male` ENHANCED_SSS skin, `high-poly` PROCEDURAL_EYES, `eyebrow001`, `eyelashes02`, `short02` hair, worksuit. Lights ×0.35 (`mpfb_face_render.py ... threequarter 0.35`). | 1024², 64 spp: **93 s** |
| `renders/research/mpfb_v2_face_hot.png` | same frame with the full-body lights (×1.0): skin clips to #fdf1ea — kept to show that the paleness below is albedo, not only exposure | 78 s |
| `renders/research/charmorph_face.png` | CharMorph default `mb_male` (bald, no morphs), `charmorph_skin_v2` | 768², 32 spp: **132.5 s** (≈5× MPFB per sample-pixel) |
| `renders/research/mpfb_v2_fullbody.png` | the v2 dressed build (detail targets, `wdg_scruffy_beard`, `short04`, cargo pants, t-shirt, boots) | 900×1600, 64 spp: 179 s |

**Verdict: neither generator produces a photoreal face out of the box; MPFB gives a correct, cleanly-topologised, riggable head that is
a *shape* starting point only. Everything the reference reads as "real" — skin, hair, stubble, eyes, bone definition, lines —
has to be added by us.** Concretely, from the renders:

*What MPFB's default already does well*
* Proportions and anatomy are plausible: eye spacing, nose length, ear shape (rolled helix, lobe), philtrum and vermilion
  border, neck/shoulder join. No shading artefacts, no pinching, clean all-quad topology; **4,119 of the 8,428 body vertices sit
  above z = 1.60 (2,963 in the front half of the head)**, i.e. half of the base mesh's resolution is in the head, so one Subdivision
  level + displacement is enough for closeups. Eyes, lashes, brows, teeth and tongue are separate fitted objects, so each can be
  replaced without touching the body. The ENHANCED_SSS skin does give soft lit/shadow terminators and red bleed at the ear and nostril.
* The full-body silhouette (`mpfb_v2_fullbody.png`) with muscle 0.7 / 182 cm is already in the reference's athletic range; the
  measurement targets (shoulder-dist, neck-circ...) move the right things.

*What reads as "MakeHuman" (and why it cannot be fixed by sliders)*
* **Skin.** The face is a flat ivory with no pores, no colour zoning, no beard shadow and a uniform waxy sheen. Measured lit cheek
  `#ebd6cb` (std 5) vs reference `#c5907d` (std 10); forehead `#ebd6cc` vs `#b98879`: ~30% too bright, far too desaturated, pink
  instead of warm tan. The `middleage_caucasian_male.mhmat` still binds `young_lightskinned_male_diffuse.png` (2048² for the *whole
  body*; the face gets ~500 px ≈ 0.3 mm/px) plus `sss.png` — there is no normal/displacement/roughness map at all. CharMorph's
  `charmorph_skin_v2` is better (visible pore noise, lip texture, proper limbal ring, mesh brows and lashes) but is also pale (`#f3e0d7`),
  5× slower, AGPL3 and welded into one 18k-vert mesh with the eyes and teeth.
* **Bone structure.** Brow ridge weak (no supraorbital shadow pocket), cheekbones flat with no sub-zygomatic hollow, jaw narrow and
  rounded with no gonial angle or masseter, chin small and soft, neck thin, no nasolabial fold, mentolabial sulcus shallow. The
  reference is a long square-oblong face with a strong straight jaw, projecting broad chin and a neck 0.85–0.9 of the jaw width.
* **Eyes.** PROCEDURAL_EYES gives a saturated cartoon-blue radial iris with no limbal ring and a too-white sclera; the fissures are
  too round and open, the upper-lid fold too shallow for the deep-set, narrowed look of the reference.
* **Hair / brows.** `short02` is a 1,755-vert cap with a painted 2 K diffuse (felt helmet, no hairline fade, wrong style); `eyebrow001`
  is a 124-vert alpha card that floats slightly off the skin. `wdg_scruffy_beard` in the v2 build is a chunky polygon beard, not
  2–4 mm stubble. These assets are the single biggest source of the "awful" look and must not be in the final model.
* **Lines.** No glabellar "11" lines, forehead crease, crow's feet or lip lines — all part of the stern 40-y read.

*Where MPFB targets WILL get us (verified to exist in the 1,214-target inventory; names are the file stems)*
* Skull/jaw/chin: `head-square`, `head-rectangular`, `head-scale-horiz-incr`, `head-fat-decr`, `head-age-incr`,
  `forehead-scale-vert-decr`, `forehead-nubian-incr`, `forehead-temple-decr`, `chin-width-incr`, `chin-height-incr`,
  `chin-prominent-incr`, `chin-bones-incr`, `chin-jaw-drop-incr`, `chin-cleft-incr`.
* Eyes/brows: `eyebrows-trans-down`, `eyebrows-angle-down`, `l/r-eye-push1-in`, `l/r-eye-push2-in` (deep-set), `l/r-eye-height1-decr`
  (narrowed), `l/r-eye-scale-incr`, `l/r-eye-trans-in`, `l/r-eye-bag-incr`, `l/r-eye-corner1-up`.
* Cheeks/nose/mouth/neck/ears: `l/r-cheek-bones-incr`, `l/r-cheek-volume-decr`, `nose-width1-decr`, `nose-width3-incr`, `nose-hump-incr`,
  `nose-nostrils-width-incr`, `mouth-scale-horiz-incr`, `mouth-upperlip-height-decr`, `mouth-philtrum-volume-incr`,
  `mouth-laugh-lines-incr`, `neck-scale-horiz-incr`, `neck-scale-depth-incr`, `neck-double-decr`, `l/r-ear-lobe-incr`, `l/r-ear-flap-incr`.
  Together these cover every ratio in the likeness checklist of `analysis_face_grooming.md` §3 and the slider list in its §10, so the
  expectation is a *recognisably lean, square-jawed, deep-eyed 40-year-old silhouette* after one targets pass (0.5 s to load 20 targets,
  so an automated fit against the landmark table is cheap). Set the age macro to ≈0.58 (40 y) but expect it to add cheek sag that
  `head-age` + `cheek-volume-decr` must counter.

*What needs custom shape keys (no MPFB target exists — checked)*
* Brow-ridge protrusion (`eyebrows-protrude` and `forehead-bulge` from §10 do **not** exist), gonial angle / jaw width / masseter bulge
  (no `jaw-*` category; `chin-jaw-drop` and `chin-bones` are the nearest), sternocleidomastoid ridge, mentolabial-sulcus depth, a sharp
  sub-zygomatic hollow. Make them as scripted targets (vertex-group-weighted offsets along normals, Laplacian-smoothed) saved to
  `data/targets/custom/*.target` or as plain shape keys in the build script. Expression (brow-lower 0.25, lid-tightener 0.25,
  lips-pressed 0.2) can come from MPFB's 102 `expression/` targets or the rig's face bones.

*What needs displacement / textures / grooms (not geometry)*
* **Albedo:** a custom 4 K face texture with colour zoning (warm tan base ≈ `#c5907d` lit → albedo ≈ `#9a6f5e`, red nose/ears/cheeks,
  blue-grey beard-shadow map from §9, darker under-eyes), either painted procedurally in UV space by script or projected from the
  reference via landmarks (see the AI-helpers note). MakeHuman's UV layout is fixed and sane, so a projected texture survives retargeting.
* **Displacement/normal:** multi-scale pore noise (0.3–1 mm), the two glabellar lines (~27 mm), one forehead crease, nasolabial and
  mentolabial creases, lip wrinkles — as a 4 K displacement baked onto the subdivided face (adaptive displacement tested in Research A).
* **Grooms:** hair (short textured crop, faded temples), 2–4 mm stubble with the §9 density map and ~25% grey on the chin, and brows as
  Blender hair curves — never MakeHuman proxy hair/beard cards.
* **Eyes:** replace PROCEDURAL_EYES with a textured iris (hazel `#5b4a3e`, strong limbal ring), darker sclera, wet-line mesh kept.
* **Shader:** keep MPFB's ENHANCED_SSS node group as the base (it is cheap: 1.4 µs per sample-pixel here) but feed it the new albedo,
  roughness and normal maps; add a thin specular coat for the sheen. CharMorph's shader is a reference for the look, not a dependency.

*Realism budget.* Targets alone: convincing head shape, still obviously CG. Targets + custom shape keys + textures + displacement: a
credible stern soldier in a 1024² eval render at 64 spp within ~2 min CPU. A true likeness of the reference face is not promised by any
of this — the ratios can be matched, the "who" depends on the projected albedo and on the groom.

## 6. Exact install commands and timings for scripts/setup_session.sh

Everything below was run on this container (Blender 4.5.14, 4 cores, 15 GB RAM). Replace the `TODO(research): MPFB2`
line in `scripts/setup_session.sh` with the first block; the rest are the manual equivalents and the smoke tests.

```bash
# --- MPFB2 2.0.17 + 11 MakeHuman CC0 asset packs. 598,134,403 bytes download, ~700 MB on disk after unzip.
#     Measured: downloads 9 MB/s (70-120 s for 598 MB), unzip of the 280 MB system pack 6.7 s, extension install +
#     userpref save ~10 s of Blender start-up, verification ~5 s  =>  budget 3 min. Idempotent: re-runs skip complete files.
bash "$PROJECT_DIR/scripts/research/mpfb_setup_from_zero.sh" "$PROJECT_DIR/assets/mpfb"
```

What that script does, as the individual commands (all verified 2026-10-06):
```bash
ASSET_DIR="$PROJECT_DIR/assets/mpfb"; mkdir -p "$ASSET_DIR/packs"
# 1. extension zip (45,031,536 bytes, sha256 4f0a879d64a39bf646fbf5f53601ac678855da329d650617dca5737548239a87)
curl -sS -L --retry 4 -C - -o "$ASSET_DIR/add-on-mpfb-v2.0.17.zip" \
  "https://extensions.blender.org/download/sha256:4f0a879d64a39bf646fbf5f53601ac678855da329d650617dca5737548239a87/add-on-mpfb-v2.0.17.zip"
# 2. install + enable + save prefs (~10 s). Result: ~/.config/blender/4.5/extensions/user_default/mpfb/ (84 MB)
blender -b --python "$PROJECT_DIR/scripts/research/mpfb_install.py" -- "$ASSET_DIR/add-on-mpfb-v2.0.17.zip"
# 3. asset packs -> MPFB user data dir (= LocationService.get_user_data())
USERDATA="$HOME/.config/blender/4.5/extensions/.user/user_default/mpfb/data"; mkdir -p "$USERDATA"
for p in makehuman_system_assets skins02 bodyparts05 eyebrows01 eyelashes01 pants01 shirts01 shoes01 gloves01 hats02 equipment01; do
  curl -sS -L --retry 4 -C - -o "$ASSET_DIR/packs/${p}_cc0.zip" "https://files.makehumancommunity.org/asset_packs/$p/${p}_cc0.zip"
  unzip -q -o "$ASSET_DIR/packs/${p}_cc0.zip" -d "$USERDATA"      # zip root holds packs/ skins/ eyes/ clothes/ ...
done
# 4. verify (prints 'system assets installed: True' and the 11 pack names)
blender -b --python-expr "import bpy; bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.assetservice import AssetService
print('system assets installed:', AssetService.system_assets_pack_is_installed()); print('packs:', AssetService.get_pack_names())"
```

Smoke tests after setup (timings measured here):
```bash
blender -b --python scripts/research/mpfb_rigify_test.py            # human + rigify.human metarig + rigify_generate: 6.1 s, 930 bones
blender -b --python scripts/research/mpfb_build_v2.py -- renders/research 16   # dressed+rigged human 7.5 s (measured); full-body render 900x1600 took 179 s @64 spp, so expect ~45 s @16 spp (not measured)
blender -b renders/research/mpfb_default.blend --python scripts/research/mpfb_face_render.py -- /tmp/face.png 64 1024 threequarter 0.35
#   ^ face closeup 1024^2 @64 spp denoised: 78-79 s (no beard); the v2 build WITH the polygon beard + hair cards took ~14 min for the same frame
```

Optional CharMorph fallback (not needed for the build; AGPL3 data):
```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/Upliner/charmorph   "$PROJECT_DIR/assets/charmorph/CharMorph"        # 1.3 MB, 2 s
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/Upliner/CharMorph-db "$PROJECT_DIR/assets/charmorph/CharMorph/data"   # 734 MB, 36 s
mkdir -p ~/.config/blender/4.5/scripts/addons && ln -sfn "$PROJECT_DIR/assets/charmorph/CharMorph" ~/.config/blender/4.5/scripts/addons/CharMorph
blender -b --python scripts/research/charmorph_test.py -- "$PROJECT_DIR/assets/charmorph/CharMorph" renders/research 32 1   # enable 0.7 s, import 3.2 s, face render see section 5
```
Disk after everything: `assets/mpfb` 573 MB (zips), MPFB user data ~620 MB, CharMorph 735 MB; Blender itself 1.2 GB.
