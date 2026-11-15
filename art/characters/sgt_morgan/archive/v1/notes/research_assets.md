# Research A — PBR textures, HDRIs and CC0 models for Sgt. Alex Morgan

Date: 2026-10-06. Everything below was downloaded, verified and (where it matters) rendered or
imported headlessly on this container (Blender 4.5.14, system python3 3.13 with PIL). All assets
are CC0 1.0: no attribution is required, and derived textures can be redistributed. Reference
colours quoted as `#rrggbb` come from the master palette in `notes/analysis_gear_inventory.md` §0.1.

## TL;DR / recommendation

* **Use the manifest, not ad-hoc downloads.** `assets/manifest.json` (schema 2, 47 assets, 138
  files, 713 MB, ~1.1 GB on disk after zip extraction) lists every file with an exact URL, byte
  size and licence. `scripts/setup_session.sh` now restores it with
  `python3 -I scripts/research/build_manifest.py assets --restore` (idempotent, size-checked, extracts zips).
* **Primary picks** (all 2K, 2048 px, JPG, full PBR sets): Cordura → ambientCG `Fabric063`;
  ripstop/twill → Poly Haven `denim_fabric_05` + procedural ripstop grid; knit → `cotton_jersey`;
  fleece → `knitted_fleece`; leather → `Leather032`; rubber → `Rubber004`; polymer → `Plastic012B`
  (black) / `Plastic018B` (tinted tan); anodised/parkerised metal → `Metal038` (+ `Metal050C` for
  bare-metal edge wear); steel hardware → `Metal027` (black) / `Metal063` (bare); concrete floor →
  `concrete_floor_worn_001` colour + `cgbookcase_PolishedConcrete01` roughness/normal;
  HDRI → `empty_warehouse_01` at low strength, cool-tinted, for fill and reflections only.
* **Every texture needs a colour tint.** No CC0 set matches the reference albedo out of the box;
  the table in §4 gives the measured mean albedo of each set next to the palette target so the
  material library can hard-code the multiplier. Fabric sets are near-neutral greys by design.
* **No CC0 ripstop, camouflage, webbing or anodised-metal texture exists** on ambientCG, Poly Haven,
  cgbookcase or 3dtextures (ambientCG search returns 0 for all of those words). Ripstop grid,
  PALS webbing and the camo pattern must be procedural (see `ref/zoom_camo_generator_prototype_v2.py`
  and the `cordura_material()` wave-weave in `scripts/research/proto_common.py`).
* **Models are reference and blockout donors only.** Nothing imported goes into the final mesh
  except, optionally, TheBaseMesh `wellington_boot` as a boot last, `seatbelt_clip` /
  `watch_strap_buckle` as buckle blockouts, and Poly Haven `garden_gloves_01` as a glove shell start.
  The OpenGameArt M4A1 (nisu) is the carbine proportion reference; its FBX imports with no materials.

## 1. What was run (reproducible)

| Step | Command (from `/home/user/sgt_morgan`) | Result / timing |
|---|---|---|
| ambientCG search | `python3 -I scripts/research/acg_search.py <out.json> ripstop nylon cordura camouflage webbing knit "leather black" rubber anodized "gun metal" polymer "painted metal"` | 0.5–1.5 s per query. ripstop/nylon/cordura/camouflage/webbing/knit/anodized/"gun metal"/polymer → **0 results**; "leather black" 10, rubber 4, "painted metal" 23. Fabrics were chosen by browsing the whole `Fabric` category instead. |
| Poly Haven listing | `https://api.polyhaven.com/assets?t=textures` (also `t=hdris`, `t=models`), then `/files/<id>` and `/info/<id>` | JSON; `/files` carries per-map `{"2k":{"jpg":{"url","size","md5"}}}`, `/info` carries authors, tags, `dimensions` (mm), `evs_cap`, `whitebalance`. |
| First download pass | `python3 -I scripts/research/download_assets.py assets` (schema-1 manifest; superseded) | Wrote `assets/textures/manifest.json` v1. Timings of that run were overwritten by the v2 build and are lost. |
| Manifest build + verify + contact sheet | `python3 -I scripts/research/build_manifest.py assets renders/research/texture_contact_sheet.png` | **20.0 s wall** (14.5 s script: ambientCG + Poly Haven API calls, PIL open of every map, 1870×2158 sheet with 31 colour tiles). 0 errors. |
| Restore dry run (all present) | `python3 -I scripts/research/build_manifest.py assets --restore` | 0.09 s, 0 downloads, 0 errors. |
| Restore proof on an empty root | subset manifest (8 assets covering every source: ambientCG zip, Poly Haven texture/HDRI/model, cgbookcase, OpenGameArt, TheBaseMesh, Google Drive) copied to a scratch `assets/`, same `--restore` | **23 files, 41.1 MB, 15.1 s, 0 errors**; sha256 of the re-downloaded `pouch_01.zip` (`ecdc3e6e…`) and `Fabric_Nylon_weave_001_normal.jpg` (`256ae929…`) equal the originals; zips extracted. Sequential, ~2.7 MB/s aggregate → full 713 MB restore ≈ 3–5 min. |
| Model import test | `blender -b --python scripts/research/model_import_test.py -- assets/models renders/research/model_import_test.json` (log `renders/research/model_import_test.log`) | 25 files (gltf/glb/fbx/obj), **all import, 2.8 s total**. Results in §5 and merged into each model's `import_test` field in the manifest. |
| HDRI previews | `blender -b --python scripts/research/hdri_preview.py -- assets/hdri renders/research/hdri` | Three 1024×512 AgX PNGs in `renders/research/hdri/`, ~5 s. |
| Material-ball render (earlier) | `blender -b --python scripts/research/matball_test.py -- assets renders/research/matball_test.png 64 1280` | `renders/research/matball_test.png`: all sets + HDRI load and render on Cycles CPU. |

`scripts/research/verify_textures.py` and `download_assets.py` are schema-1 tools superseded by
`build_manifest.py`; keep them only as history.

### URL and API snippets that work

```text
# ambientCG (CC0): API v2, then the 2K-JPG zip
https://ambientcg.com/api/v2/full_json?q=rubber&type=Material&limit=40&sort=Popular&include=downloadData,tagData,dimensionsData
https://ambientcg.com/api/v2/full_json?id=Fabric063,Metal038&include=downloadData,tagData,dimensionsData
  -> foundAssets[i].downloadFolders.default.downloadFiletypeCategories.zip.downloads[attribute=="2K-JPG"].downloadLink
  = https://ambientcg.com/get?file=Fabric063_2K-JPG.zip   (302 -> 200 application/zip, 33,153,803 B)
  zip holds *_Color/_NormalGL/_NormalDX/_Roughness/_Displacement(/_AmbientOcclusion/_Metalness/_Opacity).jpg,
  a 512 px preview PNG, and .blend/.mtlx/.usdc/.tres material files. tile size = dimensionX/Y (cm, 0 = unknown).

# Poly Haven (CC0): CDN paths are stable
https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/concrete_floor_worn_001/concrete_floor_worn_001_diff_2k.jpg
https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/empty_warehouse_01_2k.hdr          (6,581,920 B)
https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/service_pistol/service_pistol_1k.gltf  (+ "include" dict of .bin and textures/)
  maps fetched: Diffuse, nor_gl, Rough, Displacement, AO, arm (AO/rough/metal packed), Metal

# cgbookcase (CC0): b-cdn origin answers 403 without the Referer header
curl -H "Referer: https://www.cgbookcase.com/" https://cgbookcase-volume.b-cdn.net/t/PolishedConcrete01_MR_2K.zip   (14,325,870 B)

# OpenGameArt (CC0): plain file URLs
https://opengameart.org/sites/default/files/m4a1_0.zip  (3,631,284 B, nisu)   https://opengameart.org/sites/default/files/m4a1.zip  (716,723 B, MallNinjaMax)

# TheBaseMesh (CC0): the Wix *product page* embeds the hashed archive; the library page only lists its first 60
https://www.thebasemesh.com/product-page/pouch-01  ->  https://www.thebasemesh.com/_files/archives/b36d2d_bc758246f9c3478a87a2045bae3d04ce.zip
  (pouch_02 …83634159ebb545afb63f7707cc8df63e, safety_helmet …2be2c461ff2a4e49924c3591c8669168,
   wellington_boot …8c197c28bcf140fca9d9d7e45a9a2f69, seatbelt_clip …692f118fb7a84f218d98d11a5d99f7cd,
   watch_strap_buckle …64c19677f8534b8a9dfc35ad709a02dc) — all six re-downloaded and sha256-identical to the hand-fetched zips.

# 3dtextures.me (CC0): the Drive folder is JS-only, but single files download by id
https://drive.usercontent.google.com/download?id=1lgqC2teDhvncF-fyfd8ddEJQ0XVq89Gf&export=download&confirm=t   (basecolor, 202,412 B)
  7/7 ids verified by sha256 (ids are in build_manifest.py GDRIVE_FILES). drive.google.com/uc?export=download also
  worked today but returned HTTP 500 in the first session, so the manifest uses drive.usercontent.google.com.
```

## 2. Manifest fixes made in this pass

* **Location.** The v2 manifest was being written to `assets/textures/manifest.json`, which
  `.gitignore` ignores; `CLAUDE.md` and `.gitignore` expect `assets/manifest.json`. `build_manifest.py`
  now writes `assets/manifest.json`; the stale copy was deleted.
* **No more `manual: true` entries.** The 3dtextures set (7 files) and the six TheBaseMesh zips
  had `url: null`; direct URLs were recovered as above, so every one of the 138 file entries now has
  `url` and `bytes` (Poly Haven files also `md5`, TheBaseMesh zips `sha256`), and all 47 assets have
  `license` + `license_url`. Checked programmatically: 0 missing.
* **Import-test results merged.** If `renders/research/model_import_test.json` exists, each model
  entry gets `import_test` (objects, verts, tris, quads, ngons, dims_m, has_uv, materials, images).
* `scripts/setup_session.sh`: the asset TODO is replaced by the restore call.
* Manifest fields per asset: `id, kind (texture|hdri|model), need, status (primary|alt|rejected),
  note, source, source_page, license, license_url, resolution, tile_cm, folder, files[], maps{}`
  (per-file kind/px/mode), `map_kinds, resolution_px, total_bytes`.

## 3. Contact sheet judgement against the reference

Looked at `renders/research/texture_contact_sheet.png` (each tile: whole tile squashed on top,
whole tile + 25 % crop below) next to `ref/crop_torso_vest.png`, `crop_boots_feet.png`,
`crop_legs_knees.png`, `crop_hands_rifle.png` and `crop_background_hangar.png`.

* **Vest Cordura** (ref: olive-brown #463E34 = 70,62,52 with dust on ridges, matte, weave invisible at
  reference scale, visible in closeups). `Fabric063` mean albedo (73,69,62), roughness 0.83, 40 cm
  seamless procedural tile: closest in colour and the only dark tight weave; tint ×(1.0,0.92,0.85)
  to lose the grey-green. `Fabric061`/`Fabric066` are the same weave family in light grey (141 and
  131 mean) — better as normal/roughness donors for 500D pouch fabric, tinted. `book_pattern`
  (68,63,22) is already olive but strongly yellow and is a book-cloth weave. `Fabric048` rejected
  (white quilted squares). The 3dtextures weave is 1K, saturated orange, chunky — normal map only.
* **Ripstop / twill** (ref base layer #332F2D, trouser camo mid #262524 with pale tan blotches).
  `denim_fabric_05` (102,100,100) is a neutral grey twill, 27 cm tile; darken ×0.45 and overlay a
  procedural ripstop grid (no CC0 ripstop exists). `denim_fabric_06` (28,34,44) is dark but
  blue-shifted; `Fabric082A` (181,183,184) is a fine smooth weave for the sleeves.
* **Knit** (combat-shirt torso). `cotton_jersey` (194,170,156): beige jersey knit; tint to #332F2D.
  Its normal map carries the knit columns the reference shows under the carrier.
* **Fleece** (gaiter #373029, soft, low sheen). `knitted_fleece` (85,75,62), rough 0.62, is the
  right structure and nearly the right colour (×0.7). `polar_fleece` (208,173,132) cream, alt.
* **Leather** (boots #242322 creased, dusty, satin; gloves #36322F). `Leather032` (28,28,28),
  rough 0.65, 45 cm tile: black scratched grain, matches the boot uppers in `crop_boots_feet.png`
  once dust (SurfaceImperfections015) is added at the toe and welt. `Leather037` (99,55,40) brown
  full-grain photo set — glove palms/fingers, tinted dark.
* **Rubber** (soles #11100D). `Rubber004` (41,43,49), rough 0.59, 75 cm tile: fine grain, right
  look for sole sidewalls; lugs are geometry (`proto_sole.py`).
* **Polymer** (black #1C1C1E buckles/pouch bodies; khaki #7E715F admin panel; tan #837163 plates
  with pale edge wear in `crop_legs_knees.png`). `Plastic012B` (43,41,39), rough 0.45, black with
  fine scratches — use as is. `Plastic018B` (119,119,119) grey dirty scratched — tint to tan for
  pauldrons/kneepad frames, and let the scratch roughness read as edge wear.
* **Anodised / parkerised metal** (rifle receiver and rail: dark grey matte with brightened worn
  edges and brass accents in `crop_hands_rifle.png`). `Metal038` (95,97,97) with metalness map,
  roughness 0.37 — too glossy for a parkerised finish, remap to 0.5–0.65 and darken ×0.5.
  `Metal050C` (244,246,245 = bare-metal F0, rough 0.24) is the edge-wear layer driven by pointiness.
  `Metal046B` (62,62,63) dirty black is an alternative base. `Metal063` (110,109,106, rough 0.13) is
  the aged glossy steel for bare parts.
* **Steel hardware** (ladder locks, eyelets, rivets #140F06 / #322D29, antenna base #757D83).
  `Metal027` (45,44,52), rough 0.65, black powder-coat — buckles, eyelets, belt hardware;
  `Metal063` for bright steel; `blue_metal_plate` only as a scratch/chipped-paint mask source.
* **Grunge masks.** `SurfaceImperfections015` (dust, with opacity) is the universal dust layer;
  `017` (dirt speckle) for boots and lower trousers.
* **Concrete floor** (ref: dark blue-grey polished slab with crisp boot reflections and warm key
  light pooling at the feet, panel seams). `concrete_floor_worn_001` (85,86,84), rough 0.54, 3 m
  tile: right colour and wear scale. The reflections need a lower, more varied roughness: blend the
  `cgbookcase_PolishedConcrete01` roughness (mean 0.13) and normal under it. `hangar_concrete_floor`
  (51,47,44) is darker and more scuffed — alternative if the floor must read almost black.
  `smooth_concrete_floor` is orange-brown and `Concrete048` beige and too clean: both rejected in practice.
* **HDRI** (ref: large hangar, cold white cove lights and blue ambient, dark walls). None of the
  three is the hangar. `empty_warehouse_01` (16 EV, fluorescent tubes + daylight, concrete) has the
  right light *type*; `small_hangar_01` (12 EV) is daylight through windows and far too warm/bright;
  `autoshop_01` (8 EV) is a clean white garage, useful only as a neutral studio. Use
  `empty_warehouse_01` at strength 0.3–0.5 with a cool tint for fill/reflections, hide it from
  camera, and build key/rim with area lights per `notes/analysis_lighting_camera_scene.md`.

## 4. Material-need → asset table

Resolution is the map size in px (ambientCG also ships a 512 px preview PNG, not a map). "arm" is
Poly Haven's packed AO/roughness/metal JPG. Licence is CC0 1.0 for every row (ambientCG
docs.ambientcg.com/license, Poly Haven polyhaven.com/license, cgbookcase cgbookcase.com/about,
3dtextures 3dtextures.me/about). Mean albedo is the sRGB mean of the colour map; the target is the
palette value the material should be tinted towards.

| Need (ref target albedo) | Primary asset (source) | Res / tile | Maps | Mean albedo → tint | Alternatives |
|---|---|---|---|---|---|
| Cordura 1000D/500D, vest, pouches, straps (#463E34) | `Fabric063` (ambientCG, procedural) | 2048², 40 cm | Color, NormalGL/DX, Rough, Disp, AO | (73,69,62) → ×(1.0,0.92,0.85) | `Fabric061`, `Fabric066` (grey, tint), `book_pattern` (PH, olive), `3dtextures_Fabric_Nylon_Weave_001` (1K, normal only) |
| Webbing 25 mm straps, PALS (#22211F) | `poly_wool_herringbone` (Poly Haven) | 2048×2091, 27 cm → tile at 2.5 cm | Diffuse, nor_gl, Rough, Disp, AO, arm, Metal | (120,117,112) → ×0.2 | procedural herringbone |
| Ripstop / twill: trousers, shirt sleeves (#332F2D, camo mid #262524) | `denim_fabric_05` (Poly Haven) + procedural ripstop grid | 2048×2058, 27 cm | Diffuse, nor_gl, Rough, Disp, AO, arm, Metal | (102,100,100) → ×0.45 | `denim_fabric_06` (dark, blue), `Fabric082A` (fine weave) |
| Knit jersey: combat-shirt torso (#332F2D) | `cotton_jersey` (Poly Haven) | 2048×2050, 26.4 cm | Diffuse, nor_gl, Rough, Disp, AO, arm, Metal | (194,170,156) → ×0.26 | — |
| Fleece: neck gaiter (#373029) | `knitted_fleece` (Poly Haven) | 2048×2079, 26.6 cm | Diffuse, nor_gl, Rough, Disp, AO, arm, Metal | (85,75,62) → ×0.7 | `polar_fleece` (cream) |
| Leather: boot uppers (#242322), gloves (#36322F) | `Leather032` (ambientCG, procedural) | 2048², 45 cm | Color, NormalGL/DX, Rough, Disp | (28,28,28) → ×1.3 | `Leather037` (multi-angle photo, brown; gloves) |
| Rubber: soles, grips, antenna cap (#11100D) | `Rubber004` (ambientCG) | 2048², 75 cm | Color, NormalGL/DX, Rough, Disp | (41,43,49) → ×0.4 | — |
| Polymer black: mags, buckles, pouch bodies (#1C1C1E) | `Plastic012B` (ambientCG) | 2048² | Color, NormalGL/DX, Rough, Disp | (43,41,39) → ×0.6 | — |
| Polymer tan/khaki: pauldrons, guards, kneepad frames, admin panel (#837163 / #7E715F) | `Plastic018B` (ambientCG) | 2048² | Color, NormalGL/DX, Rough, Disp | (119,119,119) → ×(1.1,0.95,0.83) | `Plastic012B` + tint |
| Anodised / parkerised metal: receiver, rail, barrel | `Metal038` (ambientCG) + `Metal050C` edge wear | 2048² | Color, NormalGL/DX, Rough, Disp, Metalness | (95,97,97) → ×0.5, rough remap 0.5–0.65 | `Metal046B`, `Metal063` |
| Steel hardware: buckles, eyelets, rivets, antenna base | `Metal027` (ambientCG, black powder-coat) | 2048² | Color, NormalGL/DX, Rough, Disp, Metalness | (45,44,52) as is | `Metal063` (bare, rough 0.13), `blue_metal_plate` (PH, chip mask) |
| Dust / dirt overlays | `SurfaceImperfections015` (ambientCG) | 2048², 65 cm | Color, NormalGL/DX, Rough, Disp, **Opacity** | mask only | `SurfaceImperfections017` (speckle) |
| Concrete floor, polished, dusty | `concrete_floor_worn_001` (Poly Haven) colour + `cgbookcase_PolishedConcrete01` rough/normal | 2048², 3 m / 2K PNG | Diffuse, nor_gl, Rough, Disp, AO, arm / BaseColor, Height, Normal(DX), Roughness | (85,86,84) → ×0.6, cool tint | `hangar_concrete_floor`, `smooth_concrete_floor`, `Concrete048` |
| HDRI environment | `empty_warehouse_01` (Poly Haven, 16 EV, WB 5900 K) | 2048×1024 .hdr, 6.6 MB | — | strength 0.3–0.5, cool tint, camera-invisible | `small_hangar_01` (12 EV), `autoshop_01` (8 EV) |

Texel density: 2K at a 40 cm tile is 0.2 mm/px, finer than the 2.1 mm/px of the reference; at a
27 cm tile 0.13 mm/px. 2K is enough for every closeup view in the specs; the only candidate for 4K
is the floor if a low camera sees it large (3 m tile at 2K = 1.5 mm/px). Poly Haven also serves 4K/8K
by swapping `2k` for `4k`/`8k` in the URL; ambientCG has `4K-JPG` download attributes.

## 5. Models

All imported headlessly (`model_import_test.py`, Blender 4.5.14, all 25 files OK, 2.8 s total);
dims are world-space bounding boxes in metres (x, y, z as imported).

| Asset (source, licence) | Geometry | Dims (m) | Materials / textures | Quality | How to use |
|---|---|---|---|---|---|
| `oga_m4a1_nisu` (OpenGameArt, CC0, author nisu) | FBX, 13 objects, 5,159 verts, 9,236 tris (3,450 quads, 43 ngons), UV'd | 0.064 × 0.859 × 0.266 | **none on import** — 2K PNGs `M4A1_Base_Color/_Normal/_Roughness/_Metallic/_Height.png` must be wired by hand | Mid-poly, clean proportions, stock extended | Carbine scale and silhouette reference for the AR-12 blockout; the reference carbine's slotted handguard and stock differ, so remodel rather than reuse |
| `oga_m4a1_lowpoly_mallninjamax` (OpenGameArt, CC0) | FBX + .blend, 2 objects, 167 tris | 0.062 × 0.84 × 0.309 | `M4` with hand-painted `M4diffuse.png` | Very low poly | Silhouette only; can be dropped |
| `bolt_action_rifle_7_62` (Poly Haven, CC0, Mateusz Sadek) | glTF, 7 objects, 19,272 verts, 19,985 tris, all tris | 1.231 × 0.067 × 0.205 | 3 materials, 1K diff/nor_gl/arm (+ accessories set, glass) | Scan-quality photoreal | Material reference for parkerised steel vs wood, sling swivels, scope rings; not the carbine |
| `service_pistol` (Poly Haven, CC0, Mateusz Sadek) | glTF, 11 objects, 28,177 verts, 27,548 tris | 0.302 × 0.032 × 0.281 | 1 material, 1K diff/nor_gl/arm | Photoreal vintage semi-auto | Pistol grip/slide proportion and metal-wear reference only; the loadout icon shows a modern P226-like pistol and the figure carries none |
| `rubber_boots` (Poly Haven, CC0) | glTF, 4 objects, 30,308 verts, 56,128 tris | 0.891 (pair) × 0.266 × 0.373 | `rubber_boots` + `rubber_boots_dirty` variants, 1K | Photoreal wellington | Foot-last volume and sole-edge reference; too smooth-shelled to be the lace-up boot base |
| `garden_gloves_01` (Poly Haven, CC0, Satyaki Mandal) | glTF, 1 object, 3,975 verts, 6,822 tris | 0.227 × 0.299 × 0.076 | 1 material, 1K diff/nor_gl/rough | Photoreal fabric glove pair | Starting shell for the tactical gloves over MPFB hands (retopo needed: tris, one object for both gloves) |
| `old_military_crate` (Poly Haven, CC0, Jack Mava) | glTF, 10 objects, 16,634 verts, 20,952 tris | 1.815 × 0.979 × 0.301 | 1 material, 1K | Photoreal | Hangar set dressing behind the figure |
| `thebasemesh_wellington_boot` (TheBaseMesh, CC0) | obj/fbx 832 verts, 830 quads (glb is triangulated: 1,201 verts) | 0.134 × 0.381 × 0.407 | none, UV'd | Clean quad base mesh | Boot last to start the upper from (rescale to spec; prefer .obj/.fbx to keep quads) |
| `thebasemesh_pouch_01` / `pouch_02` | 410 / 400 quads | 0.066 × 0.068 × 0.010 / 0.069 × 0.090 × 0.010 | none | Flat quad pouch blanks, tiny as shipped | Rescale to pouch spec, use as cloth-sim or sculpt start |
| `thebasemesh_seatbelt_clip` | 200 quads | 0.037 × 0.059 × 0.002 | none | Clean | Side-release buckle blockout (thicken) |
| `thebasemesh_watch_strap_buckle` | 987 quads | 0.023 × 0.080 × 0.006 | none | Clean | Ladder-lock / strap buckle blockout |
| `thebasemesh_safety_helmet` | 766 quads | 0.221 × 0.280 × 0.172 | none | Clean | Not needed (no head gear in the reference) |

TheBaseMesh glb files carry split normals/UV seams, so their vertex counts exceed the obj/fbx
counts while triangle counts match; import the `.obj` to keep quads. Poly Haven glTF models are
triangulated by export — fine for reference, not for subdivision.

## 6. What failed and why

* ambientCG search is tag-based and knows none of ripstop, nylon, cordura, camouflage, webbing,
  knit, anodized, "gun metal", polymer → the Fabric category was browsed instead and the
  procedural `Fabric0xx` weaves chosen visually; `Fabric048` turned out to be quilted squares.
* 3dtextures' Google Drive folder is JavaScript-only and `uc?export=download` gave HTTP 500 in the
  first session; fixed by extracting per-file ids from the saved folder HTML and using
  `drive.usercontent.google.com/download?id=…&confirm=t`.
* TheBaseMesh library page is a Wix repeater that lists only its first 60 archives; the per-product
  pages embed the archive URL — all six recovered and hash-verified.
* cgbookcase's CDN returns 403 without a `Referer: https://www.cgbookcase.com/` header; the
  manifest stores the header per file.
* The OpenGameArt M4A1 FBX arrives without materials; textures must be assigned by script.
* The first-pass timings of the real downloads were lost when the v2 manifest overwrote the v1
  one; the 41 MB subset restore (15.1 s) is the measured proxy.

## 7. Files

* `assets/manifest.json` — the manifest (committed; 126 KB).
* `scripts/research/build_manifest.py` — build / verify / restore; `acg_search.py` — ambientCG query helper;
  `model_import_test.py` — headless import census; `hdri_preview.py` — AgX previews of .hdr files;
  `matball_test.py` — Cycles material-ball smoke test; `download_assets.py`, `verify_textures.py` — superseded v1.
* `renders/research/texture_contact_sheet.png`, `renders/research/hdri/*_preview.png`,
  `renders/research/matball_test.png`, `renders/research/model_import_test.{log,json}`.
* `assets/textures/<id>/`, `assets/hdri/`, `assets/models/<id>/` — gitignored, restored by the setup script.
