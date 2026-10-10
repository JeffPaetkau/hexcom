# Part 16 — Materials and texture library

Status: draft 1 (spec writer), 2026-10-10, written under the **reality-wins** rule (`CLAUDE.md`, Source of truth) and under the client's scope note at the top of spec 17 (the deliverable now is the unit model). Owner modules: `scripts/lib/materials.py` (the only module part scripts import), with `mat_catalogue.py`, `mat_core.py`, `mat_groups.py`, `mat_skin.py`, `mat_fabric.py`, `mat_hard.py`, `mat_bake.py`, and the system-Python tools `scripts/lib/texmeasure.py` and `scripts/lib/decal.py` (§7). Prefixes: node groups `MG.*`, library test objects `Lib.*`, materials `<Part>.Mat.<Recipe>`, images `<Part>.<Side>.Img.<Map>`, export atlases `Export.<Atlas>.*`.

Conventions (from `CLAUDE.md`): millimetres in this spec, metres in Blender; world origin on the floor midway between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT = viewer's right**; every left/right is the soldier's own. Pixel coordinates are full-image pixels of `ref/reference_full.png` (1672 × 941). **Colour words, used exactly:** *albedo* = the Principled Base Color, written as an sRGB-encoded hex and converted to linear by the IEC 61966-2-1 transfer; *linear* = scene-linear Rec.709; *lit* or *display* = a reference pixel, i.e. sRGB after AgX "Medium High Contrast" and spec 17's grade; *F0* = a metal's normal-incidence reflectance (the Base Color of a metallic surface), always given linear. Y = Rec.709 luminance of linear values.

Sources read: `notes/analysis_consolidated.md` (Agreed scale, §2–§9); `notes/analysis_gear_inventory.md` §0.1 (master palette), §12–§14, §18; `notes/research_assets.md` (every section); `notes/research_prototypes.md` §0, §1–§8; `notes/research_blender_capabilities.md` §4, §8, §10, Recommendations; section 5 of specs 01–14 and 17, spec 17 §2.2, §2.7, §3.5, §4.8, §4.9, §5.5, §5.6, §8.2, §10.1 and its scope note; spec 15 in full (its §5 arrived while this spec was being finished and is reconciled in C36 and C42–C48); spec 08 §7.6 (game export). Evidence produced for this spec (all reproducible, scripts in `scripts/research/proto16/`): an FFT of every CC0 tile that a spec scales (`tile_fft.py`, `tile_axes.py`, §3.2); the inverse of spec 17's display chain applied to 48 reference hexes through Blender's own OCIO (`inv_display.py`, §2.2); a sheen-weight test under a single key and under an even environment (`sheen_test.py`, `sheen_env.py`, `sheen_analyse.py`, `ref/zoom_materials16_sheen_key.png`, `_sheen_env.png`, §2.5); a working prototype of the camouflage node group with its threshold calibration and blotch statistics against the reference (`camo_nodegroup.py`, `camo_field_stats.py`, `camo_stats.py`, `ref/zoom_materials16_camo_compare.png`, `_camo_refscale.png`, §4.6); and a probe of Blender 4.5.14's Principled sockets, node types and bake colour encoding (`probe45.py`, §5.6).

---

## 1. Purpose and acceptance

### 1.1 What this part is
The one material system of the model. It owns: the **catalogue** (one ID, one real-world identity and one recipe for every material on the character, about 85 IDs in §3); the **shared node groups** (skin core, weathering, camouflage, weaves, knits, grains, masks, anodising, paint; §4); the **texture-set registry** with tile scales measured from the files rather than assumed (§3.2); the **UV, texel-density and bake rules**, including the bake to glTF core channels for the game export (§5); the **colour-management rules** that tie albedo to spec 17's AgX pipeline (§5.6); the **Python API**, naming conventions and lint (§7); and the **swatch tests** that prove each recipe before a part uses it (§8). It builds no geometry and owns no object of the character. Every part script asks it for materials by catalogue ID; no part script creates a Principled BSDF of its own. Regional data that only one part can know (the face's redness map, the boot's polish zones, the trousers' panel offsets) stay with that part and are fed into the library's groups through documented inputs.

Owners stay owners: spec 06 owns the skin's regional albedos and its maps, spec 07 the hair materials and their melanin calibration, spec 09 the trouser panels and the camouflage colour targets, spec 15 the rifle's finish layout, spec 17 the floor, the look-dev scene and the display chain. The library owns how each material is built, its parameters where several parts share it, and every cross-part rule (§2.4).

### 1.2 What perfect looks like
A critic flicking through the swatch boards and the hero closeups cannot find two parts that use the same real material and render it differently except through dirt; cannot find a scale error at any distance (no corduroy Cordura, no wood-grain pouches, no rope laces, no orange-peel pebbles on boot leather, no ripstop lattice the size of a chessboard); finds dark gear dark without any surface reading as a hole; finds no fabric that turns pale or frosty when the cool side light grazes it; finds dust only where it settles, grime only where it collects, chips only where paint meets a knock, bright metal only where a strap or a hand rubs; finds the trouser camouflage indistinguishable in statistics from the reference's; and, in the game export, finds the baked glTF materials matching the Cycles look within the tolerances of §8.3. The code that does this is idempotent, linted and versioned: building a material twice gives the same node tree, and a lint run names every sheen, albedo, colour-space or projection rule a part broke.

### 1.3 Closeup render views (presets in `scripts/eval/presets/p16.json`, resolved by spec 17's `camera.py`; scene `LookDev` with AgX Base Contrast unless stated)

| View | Camera position (mm) | Target (mm) | Lens, size | Compared with | Scores |
|---|---|---|---|---|---|
| V1 Swatch board, one per recipe (`p16.V1.swatch`) | spec 17's swatch stage: (0, −600, 1000) | `LookDev.Swatch` at (−60, 0, 1000) beside `Cal.Card18` | 100 mm, 800 × 800 (0.27 mm/px) | the catalogue's albedo; the reference crop named in its §3 row | albedo read-back (scene-linear Diffuse Color pass and a Lambert check), sheen invariance (§8.3 M3) |
| V2 Macro (`p16.V2.macro`) | (0, −250, 1000) | swatch centre | 100 mm, f/8, 1024 × 1024 (0.088 mm/px) | §3.2 measured scale of the weave, knit, grain | FFT period of the rendered luminance within ±8 % of the catalogue's real scale |
| V3 Wear block (`p16.V3.wear`) | (+300, −420, 1180) | `Lib.Test.WearBlock` at (0, 0, 1000) | 85 mm, 1200 × 900 | `ref/zoom_armour_rknee_x8.png`, `zoom_armour_rguard_x10.png`, `zoom_vest_pals_buckle_clip.png`, `zoom_boots_left_toe_x8.png` | dust only on up-faces, edge wear 0.5–1.5 mm wide on 0.8 mm bevels, chips with a lit step, grime in the slot |
| V4 Hero-light patch (`p16.V4.patch_<id>`) | hero camera, cropped by border to the anchor's ±30 px | a 60 mm sphere and a 50 mm tile of the recipe at the owning part's anchor, posed to the anchor's normal | 46 mm hero camera, solved lights (spec 17 §8.2), `Hero` scene | the lit target hex at the anchor's pixel (§2.2) | ΔE00 after the grade |
| V5 Camouflage (`p16.V5.camo`) | orthographic bake of a 1.0 × 1.0 m swatch at 4.72 px/cm, plus spec 09's V1 | — | 472 × 472 bake; hero 1672 × 941 | `ref/crop_legs_knees.png`; spec 09 §2.3 statistics | blotch sizes, tone fractions, edge width, contrast (§4.6) |
| V6 Bake round trip (`p16.V6.bake_<atlas>`) | the owning part's V1 preset | as the part | as the part, `eval` tier | the same view rendered with the procedural materials | ΔE00 and roughness difference per pixel (§8.3 M7) |

### 1.4 Pass criteria a critic or a script can score (full metrics §8.3)
1. Every catalogue recipe builds in a fresh file, twice, with an identical node tree hash; `materials.lint()` reports no error on any part.
2. V1: the scene-linear albedo read back from the Diffuse Color pass equals the catalogue value within 2 % (dielectrics); no dielectric albedo below its class floor (§3.1).
3. V1 versus V4 sheen invariance: the ratio of each fabric's brightness with and without its sheen differs by no more than 10 % between LookDev and Hero lighting.
4. V2: the rendered weave, knit, grain or ripstop period is within ±8 % of §3.2's real value; no tile repeat is visible inside 300 mm.
5. V3: dust coverage ≥ 60 % on faces with n·Z > 0.7 at preset amount 1.0 and 0 % where n·Z < 0; edge-wear band 0.5–1.5 mm on 0.8 mm bevels; every chip shows a lit step on its upper edge.
6. V4: each recipe with a lit reference target lands within ΔE00 6 (fabrics, polymers, paint) or 8 (metals, lenses) after the grade, under the solved lights, or is reported to its owner with the residual (spec 17 §8.2 rule: lights are never moved to fit a material).
7. V5: light and dark blotch statistics inside spec 09's reference ranges (light median 16–25 mm, dark median 13–18 mm, maxima 42–62 mm), tone fractions 30/35/25/10 ± 2 %, median transition width 3–5 mm.
8. V6: baked glTF materials versus procedural render: median ΔE00 ≤ 3, 95th percentile ≤ 8, roughness difference ≤ 0.05 median.
9. Colour pipeline unit tests pass: hex→linear→hex round trip exact; a 0.18 emission bake stores 118 in an sRGB 8-bit image regardless of the view transform (§5.6).
10. Every image node in every material has the right colour space (colour maps sRGB, data maps Non-Color), and no curved surface samples a tiled map with Object or Generated coordinates.

---

## 2. Reference observations

### 2.1 What the image shows about materials
At 2.1 mm per pixel the reference shows colour, gloss and dirt, never structure: no yarn, no grain, no knit, no orange peel is resolvable anywhere (a 6 mm ripstop cell is 3 px; spec 10 D8). What it does show, and what therefore carries identity: a low-key figure in near-black textiles (shirt, gaiter, gloves, belt, boots), olive-brown Cordura on the chest, one family of worn desert-tan hard polymer on shoulders, forearms, knees and drop-leg plates, a dark low-contrast four-tone blotch camouflage on the trousers, small bright metal accents (silver studs with blue speculars, gunmetal adjusters with bright worn edges, a brass antenna), a black matte rifle with hand-painted tan stripes and a bronze muzzle, pale dust on everything that faces up, grime at the cuffs and pouch bottoms, chips to a dark substrate on the armour and the admin panel, a red rubber tab on the left kneepad, and a light blue-grey brushed emblem plate. Everything on his left reads grey-blue because of the cool side light, not because of the materials (consolidated dispute 11).

### 2.2 Lit targets and what they mean in scene-linear terms
The analysts' "albedo guesses" (gear note §0.1) are lit display values. To compare like with like, I inverted spec 17's display chain (AgX "Medium High Contrast" through the OCIO config bundled with Blender 4.5.14, then the inverse of the §5.6 grade) for every target, with Newton iteration on the 3-vector (`inv_display.py`; each result re-forwarded to within 0.5/255). The skin anchor fixes the scale. The right cheek P2 #d19b87 inverts to scene Y 0.432; spec 06's albedo there is #b98670, Y 0.285; so a surface facing the key as the cheek does receives **E ≈ 1.5** (scene radiance over albedo, in luminance). A front-facing surface (the thighs, the chest; cosine to the key ≈ 0.5 against the cheek's 0.84) receives **E ≈ 1.0**. The cool-lit side is left to spec 17's solve. Provisional albedo = scene ÷ E; the final value comes from the V4 patch test (§8.2). Values below scene 0.008 sit under the grade's black crush and cannot be inverted (spec 17 §5.6 step 3); their albedos come from real-world floors (§3.1).

| Material (ID, §3) | Reference pixel(s) | Lit hex | Scene-linear (R, G, B) | Y | Zone, E | Provisional albedo Y |
|---|---|---|---|---|---|---|
| `Skin.Head` (anchor) | P2 cheek (792,100) | #d19b87 | (0.836, 0.334, 0.216) | 0.432 | key 1.5 | 0.285 (spec 06) |
| `Skin.Head` | P1 temple (778,70) | #e6bfac | (1.52, 0.69, 0.43) | 0.849 | key, highlight | — |
| `NYCO.Ripstop.Camo` k-means tones (spec 09 §2.3) | lit thigh and shin windows | #141311 / #2f2c29 / #4d4842 / #7b736c | (0.025, 0.021, 0.015) / (0.055, 0.049, 0.040) / (0.101, 0.091, 0.077) / (0.199, 0.182, 0.164) | 0.022 / 0.050 / 0.092 / 0.184 | front 1.0 | 0.022 / 0.050 / 0.092 / 0.184 |
| `NYCO.Ripstop.Camo` mid | R-thigh box median | #262524 | (0.043, 0.040, 0.034) | 0.040 | front 1.0 | 0.040 |
| `Cordura.500D.OliveBrown` | box (800–850, 245–262) | #463e34 | (0.089, 0.076, 0.054) | 0.077 | front ≈ 1.2 | 0.065 |
| `Cordura.500D.OliveBrown` highlight | dust crest | #776958 | (0.190, 0.159, 0.116) | 0.163 | key, dust | — (dust) |
| `Cordura.1000D.OliveBrown` | pouch bodies | #363028 | (0.065, 0.055, 0.039) | 0.056 | front, under flaps | 0.055 |
| `Webbing.Nylon.OliveBrown` | PALS rows (y 240–265) | #625745 | (0.142, 0.121, 0.080) | 0.122 | key ≈ 1.5 | 0.081 |
| `Polymer.Tan.Painted` (admin panel) | P3 (800,220) | #897967 | (0.245, 0.201, 0.148) | 0.207 | key, tilted up ≈ 1.2 | 0.172 |
| `Polymer.Tan.Painted` (armour median) | box (630–700, 315–355) | #837163 | (0.225, 0.178, 0.139) | 0.185 | mixed ≈ 1.0 | 0.18 |
| `Polymer.Tan.Painted` lit | right guard (655,328) | #d1bbaa | (0.905, 0.636, 0.450) | 0.680 | key + dust | — (dust) |
| Kneepad frame / centre | (703,650) / (718,660) | #5f554f / #2a2620 | (0.135, 0.114, 0.100) / (0.049, 0.042, 0.029) | 0.118 / 0.043 | front 1.0 | 0.12 / 0.04 (chipped, grimy) |
| `Webbing.Nylon.Black` | belt box median | #22211f | (0.039, 0.036, 0.028) | 0.036 | front, dusty | 0.021 + dust |
| `Leather.Boot.FullGrain` | leather box median | #242322 | (0.041, 0.038, 0.032) | 0.038 | pool + key | 0.024 + dust |
| `Leather.Boot.FullGrain` dust | vamp highlight | #a19689 | (0.352, 0.313, 0.255) | 0.317 | — | (dust) |
| `Lace.Nylon.Black` | (935,850) | #4a473f | (0.094, 0.090, 0.072) | 0.090 | pool, dusty | 0.028 + dust + fuzz |
| `Knit.Glove.Honeycomb` / `Leather.Glove.Goat` | glove box median | #36322f | (0.065, 0.057, 0.048) | 0.058 | key ≈ 1.5 | 0.03–0.04 |
| `Knit.Jersey.FR` / `NYCO.Ripstop.Black` | left sleeve box median | #332f2d | (0.061, 0.053, 0.045) | 0.054 | cool (solved) | 0.021–0.05 |
| `Fleece.Polyester` | gaiter median | #373029 | (0.067, 0.055, 0.040) | 0.056 | key / shadow mix | 0.033 + dust |
| Dust on tan armour | highlights | #9a8d85 → #d2c5b5 | (0.317, 0.267, 0.242) → (0.942, 0.797, 0.586) | 0.28 → 0.81 | key | ramp (§4.2) |
| `Metal.Aluminium.Hardcoat.Black` | upper receiver median / lit edge | #413c3b / #686463 | (0.081, 0.071, 0.066) | 0.073 | — (specular) | V4 test |
| `Coating.Cerakote.BurntBronze` | bronze tube (874,554) | #5f4c3e | (0.137, 0.099, 0.069) | 0.105 | front 1.0 | 0.105 |
| `Paint.FDE.Brushed` | upper stripe (767,342) | #d4a271 | (0.875, 0.424, 0.111) | 0.497 | key 1.5 | 0.33 |
| `Metal.Brass.Aged` | antenna body (903,152) | #705e46 | (0.174, 0.136, 0.082) | 0.140 | — (specular) | V4 test |
| `Rubber.Red` | tab (927,640), cool-lit | #917a7b | (0.279, 0.195, 0.208) | 0.214 | cool | V4 test |
| `Metal.Aluminium.Anodised.ClearBrushed` | emblem (942,212), cool-lit | #b3c2d6 | (0.371, 0.691, 1.534) | 0.684 | cool, specular | V4 test |
| `Rubber.Outsole.Black` | sole median | #11100d | below the crush | — | — | floor 0.018 |
| Floor (spec 17) | P5 (830,885) | #c9baaa | (0.760, 0.617, 0.460) | 0.636 | pool (deferred) | spec 17 |

Reading: the provisional albedos agree with the specs' values to within the uncertainty of E for most materials (Cordura, armour tan, admin panel, boot leather, laces, gloves), which is reassuring. They disagree by a factor of 2–6 for the trousers' darkest tones and by a factor of 5 for the carrier's binding tape, because those specs read display hexes as albedos (§2.4 C3, C16).

### 2.3 Ambiguities and decisions (reality-wins rule)

| # | Topic | Image or analysts | Reality | Decision |
|---|---|---|---|---|
| D1 | What a hex means | analysts' "albedo guesses" are lit values | albedo is a reflectance; the hero chain is AgX MHC plus a black crush | Library albedos come from the inverse chain ÷ zone irradiance (§2.2) or from real reflectance data, and are proved by the V4 patch test, never read off the reference |
| D2 | How black is black | trouser near-black #0a0b08, carrier "binding" #0f0b09, lugs #010101 | dyed black synthetics reflect 2–4 %, black leather 2–4 %, carbon-black rubber and plastic 1.5–3 % [estimated from typical measured reflectances; VERIFY with one spectro reading if Jeff has gear to hand] | Class floors (§3.1): textiles Y ≥ 0.018, leather ≥ 0.020, rubber ≥ 0.018, plastic ≥ 0.015, paint ≥ 0.020. Pure black in the reference is the grade's crush acting on these, not a material |
| D3 | Camouflage contrast | four lit tones whose scene-linear ratio is 1 : 2.3 : 4.3 : 8.5 | a printed camouflage has fixed dye reflectances; the ratio is the identity | Ratios locked from the reference (§2.2), absolute level set by one calibration scalar (§4.6). Spec 09's tones (ratio 1 : 2.9 : 9 : 24) rejected |
| D4 | Camouflage edges | soft, 3–5 mm, no step sharper than 4 mm | MultiCam-family patterns are designed with graded transitions; a rotary-screen print renders a gradient as broken ink on the yarns, not as a blur | Soft edges realised as a 0.45 mm print grain dithering a 3–6 mm band (§4.6): soft at the hero's 2.1 mm/px, ink-on-yarn at 0.09 mm/px |
| D5 | Fabric sheen | fold crests catch light; the gaiter's rim glows | Blender 4.5's microfibre sheen redistributes light: measured −29 % (single key) to +25 % (even environment) at weight 0.35 on a dark albedo (§2.5) | Sheen 0.04–0.08 on dark fabrics, 0.10 on thread, loop pile and fleece; nothing above 0.12. Crest highlights come from the crest mask (§4.5), the gaiter's glow from fuzz curves (§6) |
| D6 | Micro scale | unresolved | real constructions (§3.2) | Every weave, knit, grain and ripstop is set from a real product's construction and the tile's measured period |
| D7 | Ripstop weave | "diagonal micro-weave" at ×5 of a ×3 crop | NYCO ripstop is a plain weave with doubled yarns at intervals | Plain weave plus grid; twill sources (`denim_fabric_05`) rejected for ripstop |
| D8 | Tan armour chipping | dark chips on tan, worst at the kneepad centres | moulded black or grey polymer field-painted with aerosol tan chips to its own colour; moulded-in-colour tan scuffs lighter | Two recipes: `Polymer.Tan.Painted` (armour, admin panel; dark chips, 1 mm orange peel) and `Polymer.Tan.Moulded` (drop-leg face plates; stress-whitened scuffs) |
| D9 | Black rifle finish | "anodised grey, edges 1–1.5 stops lighter" | MIL-A-8625 Type III Class 2: a dyed porous Al₂O₃ layer (n ≈ 1.65) over aluminium, worn to bare metal on edges | `MG.Anodise`: metal base tinted by the dye, clear coat at IOR 1.65; the prototypes' "metallic 0.75, base 0.022" replaced |
| D10 | Barrel colour | glossy blued top rod plus bronze tubes | one barrel; spec 15 D3: Cerakote H-148 Burnt Bronze over the barrel and A2 | `Coating.Cerakote.BurntBronze` (a pigmented ceramic-polymer coating, near-dielectric); "blued steel" is kept for the socket screws and QD inserts, pins and the nitrided gas block being phosphate (spec 15 §5.1) |
| D11 | Bolt glint | "bright bolt carrier #8a8a8a" | spec 15: manganese-phosphate carrier with polished bearing bands | `Metal.Steel.Phosphate` with a polish mask to `Metal.Steel.Polished` ("bright bolt steel") on bands, bolt face and touched steel |
| D12 | Dust | highlights #9a8d85–#d2c5b5 on tan, #a19689 on boots, #776958 on Cordura | dry mineral dust reflects roughly 0.25–0.55 [estimated]; it reads paler where it is thicker | One dust layer with an albedo ramp #9a8d85 (thin film) → #d2c5b5 (crust) by thickness; per-material amount presets reach each lit highlight (§4.10) |
| D13 | Grey-blue left side | left pauldron, guard and kneepad read grey-blue | one paint job | Same tan everywhere; the left elbow cap alone is grey polymer (the vest icon shows it grey in neutral light) |
| D14 | Laces | lit #4a473f / #41362d | round black braided nylon | Black (Y 0.028), greyed by dust on up-facing segments and by fuzz; the reference brightness is dust plus the floor pool |
| D15 | Boot leather grain | unresolved | full-grain bovine boot leather has 0.5–1.5 mm grain cells [estimated] | `Leather032`'s 5.8 mm cells (measured at its native tile) scaled to 1.0 mm |
| D16 | Look and view | specs 01–14 name "scene A" and different AgX looks | spec 17 D13 | `LookDev` with AgX Base Contrast for material judgement; `Hero` with AgX MHC and the display grade for targets |

### 2.4 Cross-spec conflicts resolved
Each row is now one name and one recipe. The owning spec must update its §5 in the critique pass (§10.1 lists the edits).

| # | Topic | What the specs said | Resolution | Why |
|---|---|---|---|---|
| C1 | Sheen on dark fabric | 01 sock 0.6 / 0.3; 09 shell 0.35, stretch 0.2, Cordura 0.5, thread 0.3; 10 knit 0.18, rib 0.20, fleece 0.28, hook/loop 0.3; 12 neoprene 0.2, elastic 0.15; 14 fuzz 0.15; 02, 11, 13 ≤ 0.12 | 0.04–0.08 on dark textiles, 0.10 on thread, loop pile and fleece, lint error above 0.12 | §2.5: above 0.08 the colour depends on the light by more than ±10 %, so no albedo calibration transfers |
| C2 | Camouflage generator | 09: numpy image primary, Voronoi shader fallback | `MG.Camo.Blotch4` shader group primary, prototyped and verified (§4.6); the numpy tile retired to research | resolution-free, no tiling, one source for render and bake, matches the reference statistics |
| C3 | Camouflage tones | 09: #0c0c0a, #1c1a17, #36322c, #5e5246 | #292924, #423f39, #5b554c, #847464 (start), ratios locked, one scalar calibrated | 09's darkest tone (Y 0.0037) renders to display 0 under the crush where the reference shows 20/255 |
| C4 | Ripstop pitch | 09: 6.0 mm; 10: 6.35 mm | 6.0 mm on both garments [VERIFY against a NYCO swatch or the MIL-DTL-44436 construction table] | one fabric; a parachute ripstop standard (PIA, ≥ 4.5 repeats per inch, ≤ 5.6 mm) and the common "quarter-inch" description bracket it |
| C5 | Ripstop ground weave | 09: `Fabric061` at 50 mm; 10: `denim_fabric_05` (twill) | procedural plain weave 0.25 × 0.50 mm (`MG.Weave.Plain`) plus `Fabric061` at 64 mm as irregularity | ripstop is plain weave (D7); `Fabric061`'s measured period at 64 mm is one 0.5 mm warp pair |
| C6 | Stretch panel weave | 09: `Fabric082A` at a 10 mm tile | 200 mm tile | measured 800–850 periods per tile; at 10 mm the yarns would be 0.012 mm |
| C7 | Cordura weave tile | 13: `Fabric063` at 13 / 17 mm; 14: at 15 mm; 02: at 100 mm | 156 mm (500D), 190 mm (1000D) | `Fabric063`'s yarn is 8 px of 2048 (measured, §3.2); the 12–15 mm advice in research F §1 was for the 3dtextures map |
| C8 | Knee-pocket Cordura | 09: `Fabric048` normal, sheen 0.5 | `Cordura.500D.Black` | `Fabric048` is the rejected quilted-squares set (research A §3) |
| C9 | Black Cordura albedo | 09 #1c1c1e; 02 #292725; 14 (0.016) | #282624, Y 0.020 | one fabric, class floor |
| C10 | 1000D against 500D | 13: #332d26 (Y 0.027) against #463e34 | 1000D = 0.85 × 500D | same dye standard; only the coarser texture's self-shadowing differs |
| C11 | Olive-brown Cordura | 13: "(0.070, 0.055, 0.040)" labelled #463e34 (which decodes to (0.061, 0.048, 0.034)); 14: (0.07, 0.062, 0.047) | #50473c = (0.080, 0.063, 0.045), Y 0.065, used by 13 and 14 | §2.2 inverse; the hex was a lit median, and the two specs' linears disagreed with it and with each other |
| C12 | Black webbing | 02 0.020; 11 0.030; 12 #22211f; 14 0.018 | #292725, Y 0.021 | one webbing |
| C13 | Webbing weave tile | 13, 14: "`poly_wool_herringbone` tiled 2.5 mm across" | tile 280 mm across `u` | the tile holds 112 herringbone periods (measured); 2.5 mm is the period, not the tile |
| C14 | Coyote webbing | 12: #8a7050; 14: (0.19, 0.135, 0.085) | #826c51 | one Coyote Brown 498 webbing |
| C15 | Thread | 02 0.020; 09 #141311, rough 0.38, sheen 0.3; 10 #1f1c1a; 11 and 14 0.13; 13 (0.10, 0.085, 0.06) and black 0.030 | `Thread.Bonded.Black` #24211e and `Thread.Bonded.OliveBrown` #5b4f40, rough 0.55, sheen 0.10 | thread is dyed to match the cloth; 0.13 is light grey and would draw white stitches on black gear |
| C16 | Binding tape | 13: #0f0b09 (Y 0.004); 11: (0.030), rib 0.5 mm; 13: rib 1.0 mm; 14: webbing | `Binding.Grosgrain.Black` #2a2826, rib 0.6 mm | #0f0b09 is the Cordura's shadow sample in the analysis, not a binding colour |
| C17 | Elastic | 11 0.026, sheen 0.05; 12 #1a1a1a, sheen 0.15; 13 #141312; 14 0.012 | `Elastic.Woven.Black` #262423, rough 0.82, sheen 0.06, rib 1.0 mm | one material |
| C18 | Neoprene and foam | 11 / 12 differ in sheen (0.06 / 0.2) and albedo | one recipe each (§3.3) | one material |
| C19 | Gunmetal | 02 (0.10, 0.095, 0.09) r 0.42; 09 black oxide 0.011 metallic; 12 `Metal027` #3c3d45 metallic 0.9; 13, 14 (0.10) r 0.45 | `Metal.Gunmetal` F0 (0.10, 0.10, 0.105), metallic 1, r 0.45; worn edges F0 (0.56, 0.57, 0.58), r 0.25 | an F0 of 0.011 is below any metal; black oxide over steel |
| C20 | Bright hardware | 12 #c9c9c6 r 0.22; 13 (0.70, 0.70, 0.72) r 0.22; 14 (0.62, 0.62, 0.60) r 0.3 | `Metal.Nickel` (rivets, studs, snaps, cam buckles) F0 (0.66, 0.61, 0.53); `Metal.Stainless` (screws, D-rings, pins) F0 (0.60, 0.59, 0.57) | two real platings; neither is brighter than its metal allows |
| C21 | Tan polymer | 12 #837163; 13 #7e715f; 14 (0.20, 0.155, 0.115) | `Polymer.Tan.Painted` #837163 (13's panel with tint (0.92, 1.0, 0.92)); `Polymer.Tan.Moulded` #7c6e5f | D8 |
| C22 | Chip substrate | 12 #2e2b27 → #453d3b; 13 #352f2b; 14 lighter (0.26, 0.21, 0.165) | painted: 12's range; moulded: 14's lighter scuff | D8 |
| C23 | Edge-wear source | `Pointiness` in 09, 12 (baked), 13, 14; Bevel node in 02 and research F | Bevel-node mask on hard surfaces, GN crest attribute on cloth, `Pointiness` only on dense sim meshes, never on boolean meshes (lint) | research F §6: `Pointiness` smears across boolean faces and vanishes on sparse lofts |
| C24 | Wear image packing | 02 (R dust, G scuff, B grime, A polish); 10 (R dust, G sweat, B abrasion, A crest); 11 (R dust, G polish, B grime, A abrasion); 13 (R dust, G grime, B edge, A stress) | `Img.Wear`: R dust, G grime, B edge/abrasion, A polish; `Img.Wear2`: R crest, G stress-whitening, B sweat/oil, A zone id | one reader in `MG.Weather.*` |
| C25 | Dust colour | 02 #9a8e82; 09 #8a7d70; 10 #9a8d85; 11 (0.42, 0.37, 0.33); 12 #d2c5b5; 13 #8a7d6a; 14 (0.55, 0.49, 0.42) | one ramp #9a8d85 → #d2c5b5 (D12), per-material amount presets (§4.10) | one hangar, one dust |
| C26 | Grime colour | 02 (0.12, 0.10, 0.08); 09 #0e0d0b; 12 #1a1612; 13 #1a1810 | oily grime #1a1612, dry dirt #3a342c, soot (0.012, 0.011, 0.010) #1d1b19 (spec 15's carbon), chosen by an `oil` input | one group |
| C27 | Skin group | 01, 03, 04, 05, 06: "`Skin.Base` [VERIFY its name]"; 01 `Foot.Skin` | `MG.Skin.Core`; materials `Body.Mat.Skin.Head`, `.Skin.Body`, `.Skin.Foot` | §4.1 |
| C28 | Skin scatter radius | 01: (1.0, 0.35, 0.18); 03–06: (1.0, 0.2, 0.1) | core (1.0, 0.2, 0.1); sole and callus (1.0, 0.45, 0.28), eyelids and ears (1.0, 0.25, 0.12) as region data | majority, regions kept |
| C29 | Skin sheen and vein tint | sheen 0.05 (01, 03–05) / 0.04 (06); vein 15–20 % | sheen 0.04, roughness 0.5, white; vein 18 % toward #7d8b86 | small, unified |
| C30 | Brow and lash | 06: melanin 0.85 / 0.95, redness 0.45 / 0.3; 07: 0.78 / 1.0, 0.30 / 0.2 | spec 07's values, calibrated by `calibrate_melanin` to #5a3d30 | 07 owns hair |
| C31 | Stubble mask | 06: `Head.Masks.G` 1 = 45 /cm², ×0.75 / 0.87 / 0.95; 07: `Hair.Masks.R` 1 = 55 /cm², lerp 0.78 | 07's mask (1 = 55 /cm²) drives 06's skin: albedo × (1 − 0.25 R^0.8); 06's `Masks.G` dropped | one density field; the curve reproduces 06's three classes |
| C32 | Body hair | 01 `Foot.Hair` melanin 0.8, redness 0.6; 05 root #3a2a1e, tip #5a4030 | `Hair.Body` melanin 0.75, redness 0.5, tip × 0.8 | one man's body hair |
| C33 | Leather grain tiles | 02 `Leather032` at 250 mm; 11 `Leather037` at 60 mm | 80 mm (1.0 mm cells); 41 mm (0.6 mm cells) | measured 78 and 68 cells per tile; 02's tile gave 3.2 mm pebbles |
| C34 | Knit tiles | 01 `knitted_fleece` at 90 mm; 10 jersey "wale 1.0 mm [VERIFY]" | 230 mm (1.6 mm stitch); `cotton_jersey` at its native 264 mm (0.69 mm course) | measured periods |
| C35 | Black rubber | 02 outsole 0.012; 13 cap ≈ 0.010; 14 0.02, r 0.9 | outsole 0.018, rand and moulded 0.020 | class floor |
| C36 | Black hardcoat | research F: metallic 0.75, base 0.022; 15: `Rifle.Mat.Anodised` (0.024, 0.022, 0.021), metallic 0.75, rough 0.48, and `Hardcoat.Gloss` (0.018), metallic 0.60 | `MG.Anodise` (D9) for both, `.Gloss` with spec 15's roughness per object | physics of the oxide; spec 15's look targets unchanged |
| C37 | Module names | 09 `materials.py`; 11, 14 `mat_fabric.py` / `mat_hard.py`; 12, 15 `mat_hard.py`, 15 group `Wear.EdgeBevel`; 12 `decals.py`; 14, 15 `decal.py` | `materials.py` is the API; `mat_*.py` keep their names inside it; `MG.Mask.EdgeBevel` (= 15's group); `decal.py` | §7 |
| C38 | UV map names | 09 `UV_Real`, `UV_Atlas`; 02 `UV_Atlas`, `UV_Grain`; 06 `UV.Head` | `UV.Real`, `UV.Atlas`, `UV.Head`; `UV_Grain` retired (Box projection or `UV.Real`) | one spelling, the one spec 17's naming uses |
| C39 | Material names | `<Part>.Mat.<Name>` (02, 09–13); `BeltRigs.Webbing.Black` (14); `Skin.Head`, `Eye.Cornea` (06); `Foot.Skin`, `Sock.Knit` (01) | `<Part>.Mat.<Recipe>` everywhere (§7.1) | one rule |
| C40 | View and look | 02 "AgX MHC" for scene A; 04 "AgX Base Contrast" for the hero frame; 09 "AgX" | spec 17 §5.6 | D16 |
| C41 | Hidden interiors | 09 `PocketInside` #0a0a09 | `Fabric.BackFace` (parent albedo × 0.8, rough + 0.05) | a pocket is the cloth's own back; AO does the darkening |
| C42 | Rifle material names | 15: `Rifle.Mat.Anodised`, `.Hardcoat.Gloss`, `.Steel.Phosphate`, `.Steel.Blued`, `.Cerakote.Bronze`, `.Polymer.Black`, `.Polymer.Grey`, `.Rubber`, `.Paint.FDE`, `.Glass` | `Rifle.Mat.<ID>` with §3.3's IDs (`Metal.Aluminium.Hardcoat.Black(.Gloss)`, `Metal.Steel.Phosphate`, `Metal.Steel.Blued`, `Coating.Cerakote.BurntBronze`, `Polymer.Black.Textured`, `Polymer.Grey.PMAG`, `Rubber.Moulded.Black`, `Paint.FDE.Brushed`, `Glass.Optic.Coated`); `Rifle.Mat.Emissive.Blue` stays spec 15's own (off by default) | C39 |
| C43 | Worn aluminium | 15: bare 7075/6061 (0.60, 0.59, 0.57), rough 0.30 | F0 (0.91, 0.92, 0.92), rough 0.35, with a residual oxide coat 0.3 | aluminium's F0 is about 0.91; the residual oxide and the abrasion give the "grey-silver" spec 15 wants; checked at (772,352) #686463 in V4 |
| C44 | Phosphate | 15: base (0.040, 0.040, 0.042), metallic 0.85, rough 0.55 | metallic 0.3, base (0.060, 0.062, 0.060), oil coat 0.2; spec 15's part list kept (pins, roll pins, set screws, gas block move from `Steel.Blued` to `Phosphate`) | a manganese-phosphate layer is a non-metallic crystal film over steel, matte and dark, with an oil sheen |
| C45 | Burnt bronze | 16 draft: (0.14, 0.10, 0.07), metallic 0.15, rough 0.48; 15: (0.135, 0.082, 0.050), metallic 0.45, rough 0.38 | spec 15's values [VERIFY on an H-148 swatch] | 15 owns the rifle look and calibrates it against #5f4c3e–#6a5344 |
| C46 | Optic coating | 16 draft: one 120 nm MgF₂ film; 15: 300 nm front (blue-green), 520 nm rear (amber) | spec 15's films | the reference's "faint blue lens"; multi-layer coatings show such colours |
| C47 | Black textured polymer | 16 draft: 0.017 for all black polymer; 15: stock and grip (0.030, 0.028, 0.026) | textured glass-filled nylon (0.030, 0.028, 0.026); smooth acetal stays (0.017) | glass fibres at a textured surface scatter more light than smooth acetal |
| C48 | Rifle bake and wear | 15: bakes the Diffuse Color pass; its own 4096 + 2048 sheets; groups `Wear.EdgeBevel`, `Wear.Touch`, `Wear.Chips`, `Wear.Dust`, `Wear.Grime`, `Wear.Carbon`, `Wear.Scuff`, `Wear.Brass` | library socket-rerouting bake (§5.4; the Diffuse Color pass is black on metals); atlases `Export.Rifle` 4096 and `Export.RifleKit` 2048 as spec 15 laid them out; groups → `MG.Mask.EdgeBevel`, `MG.GN.Touch`, `MG.Weather.Chips`, `MG.Weather.Dust` (with spec 15's object-up term), `MG.Weather.Grime` (with its source-based soot), scuffs; `Wear.Brass` stays a rifle-local layer | one bake path and one set of groups |

### 2.5 The sheen measurement behind C1 and D5
Twelve spheres of albedo (0.040, 0.035, 0.027), roughness 0.78, Specular IOR Level 0.35, sheen roughness 0.5, sheen weight 0 / 0.04 / 0.08 / 0.12 / 0.20 / 0.35, once with a white sheen tint and once with a beige tint, rendered under one 1 m area key at 45° and again under an even grey world (`sheen_test.py`, `sheen_env.py`; 48 spp, 7.7 s each). Mean scene-linear luminance relative to sheen 0:

| Sheen weight | 0.04 | 0.08 | 0.12 | 0.20 | 0.35 |
|---|---|---|---|---|---|
| Key, white tint: disc / front core | 0.96 / 0.93 | 0.90 / 0.84 | 0.82 / 0.75 | 0.76 / 0.66 | 0.71 / 0.58 |
| Even world, white tint: disc | 0.97 | 0.99 | 1.02 | 1.07 | 1.25 |
| Even world, tinted: disc / lit rim | 1.00 / 0.98 | 1.05 / 1.07 | 1.10 / 1.17 | 1.22 / 1.37 | 1.54 / 1.75 |

The 4.5 sheen layer takes energy from the front and gives it to grazing angles, and a white tint draws a frosty rim on the lit edge (`ref/zoom_materials16_sheen_key.png`). Under the hangar HDRI of research F it read as "bleaching". Either way the effect depends on the light by tens of percent above 0.08, and the hero's cool side light grazes every fabric on his left. Hence the cap.

---

## 3. Real-world reference: the catalogue

Marks: **M** measured (on this machine, from the files or the image), **S** sourced (a standard, a manufacturer or a retailer's published data), **E** estimated (reasoned from S or M values; the reasoning is given). Catalogue IDs are `Family.Variant[.Sub]`; the material datablock a part receives is `<Part>.Mat.<ID>` (§7.1).

### 3.1 Class rules (every recipe obeys its class; `materials.lint()` enforces the numbers)

| Class | Albedo Y floor – ceiling | Roughness | IOR (Specular IOR Level) | Sheen | Notes |
|---|---|---|---|---|---|
| Black dyed synthetics and blends (nylon, polyester, NYCO, knits, webbing, tape) | 0.018 – 0.040 | 0.60 – 0.90 | 1.53 (0.30 – 0.45) | 0.04 – 0.08; thread, loop pile, fleece 0.10; max 0.12 | sheen tint = base lifted 25 % toward white; sheen roughness 0.5 – 0.6 [E: from §2.5] |
| Coloured textiles (olive-brown, coyote, camo tones) | 0.020 – 0.25 | 0.62 – 0.85 | 1.53 (0.35 – 0.45) | as above | |
| Finished leather | 0.020 – 0.06 (black) | 0.35 – 0.80 | 1.50 (0.5) | 0 – 0.04 | coat ≤ 0.15 on polished zones only |
| Carbon-black rubber, TPR, neoprene, foam | 0.018 – 0.030 | 0.45 – 0.90 | 1.52 (0.5) | ≤ 0.06 | |
| Moulded plastics, black and grey | 0.015 – 0.25 | 0.35 – 0.60 | 1.48 – 1.58 (0.5) | 0 | no orange peel unless painted |
| Paint (aerosol, brushed, stencil) | 0.020 – 0.85 | 0.50 – 0.70 | 1.50 (0.5) | 0 | orange peel 0.5 – 1.0 mm wavelength, 3 – 6 % slope |
| Skin | regional, 0.28 – 0.42 | 0.38 – 0.72 | 1.40 (0.5) | 0.04 | Random Walk (Skin) SSS, scale 0.0015 – 0.006 m |
| Bare and plated metals | F0 from the table in §3.4 | 0.15 – 0.60 | — (metallic 1) | 0 | never a metallic F0 below 0.05 |
| Anodic and conversion coatings | metal F0 × dye², coat IOR 1.65 | 0.30 – 0.62 | coat 1.65 | 0 | `MG.Anodise` (§4.8) |
| Glass and clear polymer | — | 0.00 – 0.30 | 1.52 glass, 1.49 PMMA, 1.58 PC, 1.376 cornea | 0 | |

Bumps are physical throughout (§4.0): Bump `Distance` is the real relief height in metres and `Strength` is 1.0, except for photographed normal maps whose strength is listed.

### 3.2 Texture-set registry: measured periods and the tile each must be scaled to (M, `tile_fft.py`, `tile_axes.py`: Hann-windowed FFT of each Displacement map, 2048 px)

| Asset (`assets/textures/…`) | Native tile (manifest) | Measured period at native size | Real feature it stands for | **Tile to use** | Maps used | Used by |
|---|---|---|---|---|---|---|
| `Fabric063` (ambientCG) | 400 mm | yarn 8 px = 1.56 mm; basket pair 16 px = 3.12 mm (128 pairs per tile) | 500D yarn pitch 0.61 mm; 1000D 0.74 mm (§3.4) | **156 mm** (500D), **190 mm** (1000D) | NormalGL ×0.6, Roughness ×0.9 + 0.1, AO ×0.3; Color never (grey-green) | all Cordura |
| `Fabric061` | 400 mm | 16 px = 3.12 mm on both axes | one NYCO warp pair, 0.50 mm | **64 mm** | NormalGL ×0.25 (yarn irregularity), Roughness | NYCO ripstop |
| `Fabric082A` | unknown | 2.4 – 2.6 px | stretch-woven yarn 0.24 mm | **200 mm** | NormalGL ×0.4 | NYCO stretch panels |
| `cotton_jersey` (Poly Haven) | 264 mm | course 5.4 px = 0.69 mm | FR jersey course 0.7 mm | **264 mm** (native) | nor_gl ×0.6, rough, AO ×0.3 | jersey, rib face, glove-knit cell floors (scaled to 0.3 mm loops: 115 mm) |
| `knitted_fleece` | 266 mm | 13.6 – 14.7 px = 1.76 – 1.91 mm | fleece clump and sock stitch 1.6 mm | **230 mm** | nor_gl ×0.5, rough ×0.5, diffuse luminance high-pass ±6 % | fleece, sock |
| `poly_wool_herringbone` | 270 mm | across: 18.3 px = 2.41 mm; twill 6.6 px = 0.87 mm | webbing herringbone 2.5 mm across the strap | **280 mm across `u`** | nor_gl ×0.5, rough | all webbing |
| `Leather032` | 450 mm | cells 25 – 40 px = 5.6 – 8.8 mm (78 per tile) | boot grain 1.0 mm | **80 mm** | NormalGL ×0.35, Roughness → 0.40 – 0.75, Color ×1.3 desaturated as a 10 % multiply | boot leather |
| `Leather037` | unknown | cells 27 – 32 px (68 per tile) | goat pebble 0.6 mm | **41 mm** | NormalGL, Roughness | glove leather |
| `Rubber004` | 750 mm | 21 px = 7.7 mm blotches | mould and abrasion irregularity 0.5 mm | **50 mm** | NormalGL ×0.3 | rubber sidewalls, cap, pad |
| `Plastic012B` | unknown | 3.5 – 4.0 px | moulding micro-scratches 0.2 mm | **100 mm** | NormalGL ×0.3, Roughness | black polymer |
| `Plastic018B` | unknown | 3.8 – 4.3 px | paint micro-scratches 0.12 mm | **60 mm** | NormalGL ×0.35, Roughness as scratch mask | tan paint |
| `Metal027` | unknown | 9 – 10 per tile (mottle only) | oxide mottle | **60 mm** | Roughness ×0.5 | gunmetal |
| `Metal063` | unknown | — | handling smudge | **20 mm** | Roughness ×0.5 | nickel, stainless |
| `SurfaceImperfections015` | 650 mm | — | dust drifts | **300 – 650 mm** | Opacity, Color | `MG.Weather.Dust` |
| `SurfaceImperfections017` | 400 mm | — | dirt speckle | **200 – 400 mm** | Opacity | `MG.Weather.Grime` |
| `concrete_floor_worn_001`, `cgbookcase_PolishedConcrete01` | 3 m | — | slab | spec 17 §5.1 | as spec 17 | floor |

Not used, with reasons: `denim_fabric_05/06` (twill; ripstop is plain weave, D7), `Fabric048` (quilted squares), `Fabric066`, `book_pattern`, `polar_fleece` (wrong structure or colour), the 3dtextures nylon weave (1K, its measured period is 1.4 px: JPEG-level noise, unusable as a weave), `Metal046B` (replaced by `MG.Anodise`; `Metal038`'s normal survives only as spec 15's ×0.15 micro-structure on the hardcoat), `blue_metal_plate` (chip shapes now come from `MG.Weather.Chips`). Every tiled map is sampled through `MG.Tile.AntiRepeat` (§4.8). Each asset's measured period is stored in `mat_catalogue.TILE_PERIODS` so the tile follows from the real feature, not from a hard-coded number: `tile_mm = periods_per_tile × real_feature_mm`.

### 3.3 The catalogue (start values; owners may refine after V4 with a spec update)
Columns: **ID** — **real identity → used by** (spec: objects) — **albedo or F0** (sRGB hex; linear; Y) and the **lit target** (reference pixel) — **roughness** — **other Principled values** — **maps, tile, UV, texel density** — **procedural layers and wear preset** (§4). "td" is the texel density of the part's mask or bake atlas; tiled detail is resolution-free.

#### 3.3.1 Skin and nails (regional data owned by specs 01, 03–06; core by the library)

| ID | Identity → used by | Albedo; lit target | Rough | Other | Maps, UV, td | Layers |
|---|---|---|---|---|---|---|
| `Skin.Head` | face, ears, scalp, upper neck of a 40-year-old Fitzpatrick II–III man → 06 (`Body.Mat.Skin.Head`, faces above rest h 1622) | base #b98670 (0.485, 0.238, 0.162; Y 0.285), regional table 06 §5.4; lit P1 #e6bfac (778,70), P2 #d19b87 (792,100), under-jaw #110b06 (812,140) | 0.38 – 0.55 by region | IOR 1.40, spec 0.5; SSS Random Walk (Skin), weight 1, radius (1.0, 0.2, 0.1) [lids, ears (1.0, 0.25, 0.12)], scale 0.0028 – 0.0060 m, SSS IOR 1.4, anisotropy 0.8; coat 0 – 0.12 / 0.20 – 0.35; sheen 0.04 / 0.5 white | spec 06 maps on `UV.Head` 4096² (13.6 px/mm): Albedo, Rough, Masks, Masks2, Pores.exr, Disp.exr, Normal | `MG.Skin.Core` + `MG.Skin.Micro` (pores by region, micro-lines, lip lines); stubble darkening from `Hair.Masks.R` (C31); no dust on the face |
| `Skin.Body` | trunk, arms, legs → 03, 04, 05 (`Body.Mat.Skin.Body`) | chest #c9a58d (Y 0.413), abdomen #cca891, nape #b07c66, thigh #c39a80 (0.363), hand dorsum #bf8f78 (0.321), palm #d9b09c; no lit target (hidden), look-dev targets in 03–05 §5.5 | 0.40 – 0.72 | as `Skin.Head`; SSS scale 0.0021 – 0.0045 | MakeHuman UV; `Leg.Masks`, `Torso.Masks(2)`, `Arm.Masks(2)` 4096² (≈ 2.4 px/mm, hand ≈ 1.6) + relief EXRs | `MG.Skin.Micro` layer C (follicle pits, skin lines, creases, friction ridges, callus flakes); vein tint 18 % → #7d8b86 |
| `Skin.Foot` | foot below the ankle seam ring → 01 (`Body.Mat.Skin.Foot`, was `Foot.Skin`) | dorsum #b6886f (Y 0.287), sole #d8b798, callus #e0cba8, toes → #c48474 | 0.42 – 0.72 | sole and callus SSS radius (1.0, 0.45, 0.28), scale 0.0015 – 0.0032 | attributes + procedural; bake fallback 4096² (1.2 px/mm) | spec 01 §5.2 – 5.3 layers through `MG.Skin.Micro` |
| `Nail.Plate` / `Nail.FreeEdge` | finger and toe nails → 01, 05 | #e9dfd6 / #ece6dd; bed #d4a090 – #d49a88 below | 0.15 / 0.25 | IOR 1.5, transmission 0.55 / 0.70, coat 0.6 | procedural | longitudinal ridges 0.25 mm pitch (0.01 mm), hallux transverse ridge (01) |

#### 3.3.2 Hair and fibres (spec 07 owns the melanin calibration; Principled Hair BSDF, Chiang)

| ID | Used by | Parametrisation | Values | Target |
|---|---|---|---|---|
| `Hair.Scalp` | 07 | melanin | melanin 0.62 (tip × 0.60 over the last 45 %, light strands × 0.52, ±0.06 random), redness 0.45 → 0.60 at tips, roughness 0.32, radial 0.30, coat 0.05, IOR 1.55, offset 2°, random colour 0.08, random roughness 0.20 | lit p50 #4f483a; albedo root #3a2a1e, tip #8a6549 |
| `Hair.Stubble` | 07 | melanin | 0.80, redness 0.30; grey strands 0.03 with tint #d8d0c4 (20 – 30 % on chin and soul patch); roughness 0.40, radial 0.35, coat 0 | chin #78574a, soul patch #634036 |
| `Hair.Brow` / `Hair.Lash` | 06 consumes, 07 owns (C30) | melanin | brow 0.78, redness 0.30, rough 0.30, coat 0.15, light strands 0.55; lash 1.0, redness 0.2, rough 0.25, coat 0.2 | brow recolour #5a3d30 |
| `Hair.Body` | forearms, shins, foot dorsum, chest, toes → 01, 03, 04, 05 (C32) | melanin | 0.75 (tip × 0.8; 20 % of forearm strands × 0.7 sun-lightened; 4 % grey at 0.10), redness 0.50, rough 0.35, radial 0.30, coat 0.05, random colour 0.15 | root #3a2a1e, tip #5a4030 |
| `Fibre.Fleece` | gaiter nap curves → 10 (was `Gaiter.Mat.Fuzz`, melanin 0.65) | direct colouring | colour = `Fleece.Polyester` albedo, roughness 0.55, radial 0.50, IOR 1.54, coat 0 | gaiter rim fringe (850,140) |

A dyed polyester fibre has no melanin; direct colouring reproduces the dye and keeps the fibre in step with the cloth it grows from.

#### 3.3.3 Eyes and mouth (spec 06 owns; listed so the catalogue is complete)
`Eye.Cornea` (transmission 1, IOR 1.376, roughness 0, shadow rays transparent); `Eye.Iris` (`Eye.Iris.png`, body #5b4a3e, collarette #6a5243, fibres #6e6253, crypts #3f322b, limbal ring #3a2d26, roughness 0.5, bump 0.15 mm); `Eye.Sclera` (#e6e0da, canthal #d9c9b4, roughness 0.25, SSS 0.002, coat 0.3, IOR 1.38); `Eye.Wet` (transmission 1, IOR 1.336 [tear film; spec 06 wrote 1.33], roughness 0.05); `Eye.Caruncle` (#b0695c, roughness 0.3, SSS 0.003, coat 0.4); `Eye.Occluder` (transparent × #1a0f0a by vertex alpha); `Teeth.Enamel` (#e9e1d3 → #d9c7a9, roughness 0.25, SSS 0.002, coat 0.5, IOR 1.62 [enamel; spec 06 wrote 1.6]); `Teeth.Gums` (#b45e5e); `Mouth.Tongue` (#b86a6c, papillae 0.6 mm); `Mouth.Bag` (#3a1612). Materials are `Eye.Mat.Cornea`, `Mouth.Mat.Teeth.Enamel` and so on (§7.1).

#### 3.3.4 Textiles

| ID | Identity → used by | Albedo; lit target | Rough | Other | Maps, UV, td | Layers and wear |
|---|---|---|---|---|---|---|
| `NYCO.Ripstop.Camo` | Crye G3-class 50/50 NYCO ripstop, 230 g/m², 0.50 mm → 09 shell panels, loops, flaps | `MG.Camo.Blotch4` tones T0 #292924 / T1 #423f39 / T2 #5b554c / T3 #847464 (Y 0.022 / 0.050 / 0.092 / 0.184), fractions 30/35/25/10 %; lit #262524 (R-thigh median), #6e5e4c (705,590), #38322c (880,600) | 0.70; ±0.02 by tone (darker rougher) | IOR 1.53, spec 0.45, sheen 0.06 / 0.5 / base + 25 %, SSS 0 | camo procedural on `UV.Real` (per-panel island offsets, seed 7); `Fabric061` at 64 mm; `Trousers.C.Img.Wear(2)` 2048² per UDIM (≈ 3.7 px/mm) | `MG.Weave.Ripstop` (plain 0.25 × 0.50 mm, grid 6.0 mm, doubled yarn 0.5 mm, +0.08 mm, rough −0.05 on grid); crest; stress whitening at the gusset (→ #4a443c); dust and cuff grime from preset `cloth.thigh`; panel fade +6 % on thigh fronts |
| `NYCO.Stretch.Camo` | 4-way stretch woven (nylon/elastane), printed → 09 articulation, popliteal, gusset | camo × 0.85 (synthetic stretch takes the print darker) | 0.70 | as above | `Fabric082A` at 200 mm ×0.4; no grid | as above |
| `NYCO.Ripstop.Black` | Crye G3 shirt sleeves (NYCO) → 10 lower sleeves, pockets, cuffs | #2a2725 (0.023, 0.020, 0.019; Y 0.021); lit sleeve box #332f2d (885–925, 300–370) | 0.68 ± 0.04 (noise 40 mm) | IOR 1.53, spec 0.45, sheen 0.06 | `MG.Weave.Ripstop`; `UV.Real`, `u` along the sleeve axis; `Shirt.C.Img.Wear(2)` 2048² per UDIM (2.6 – 2.8 px/mm) | crest +5 %; dust `cloth.shoulder`; Displace puckers (10) |
| `Knit.Jersey.FR` | Crye G3 torso flame-resistant jersey → 10 torso, collar | #2c2826 (Y 0.022) | 0.80 ± 0.04 | spec 0.35, sheen 0.06, anisotropic 0.25 along wales | `cotton_jersey` at 264 mm ×0.6, AO ×0.3 into base; masks as above | sweat band −12 % (`Wear2.B`); crest; compression darkening under straps |
| `Knit.Rib.2x2` | 2 × 2 rib shoulder panels, wale 4.2 mm (geometry) → 10 | #2e2a28 (Y 0.024); lit right shoulder #49433e | 0.82 | spec 0.35, sheen 0.06 | `cotton_jersey` ×0.3 + course Wave 1.1 mm (0.05 mm) | dust on rib crests `cloth.shoulder` |
| `Fleece.Polyester` | 100-weight polyester microfleece tube → 10 gaiter | #3a3129 (0.042, 0.031, 0.022; Y 0.033); lit fold #7e6d62 (760,155), median #373029, shadow ≤ #0a0806 (835,160) | 0.78 ± 0.05 | spec 0.30, sheen 0.10 / 0.6 / base + 25 % | `knitted_fleece` at 230 mm; `Gaiter.C.Img.Wear(2)` 2048² (5.7 px/mm) | dust `fleece.toproll` carries the lit fold (the target is reached by dust, not sheen); sweat −12 %; strap-pressed nap −10 %; nap = `Fibre.Fleece` curves (§6) |
| `Knit.Sock.WoolNylon` (+`.Reinforced`) | merino/nylon cushion boot sock → 01 | #5a4b3a (Y 0.075); reinforced #33302c (Y 0.030); hidden | 0.80 / 0.65 | sheen 0.08 / 0.06; SSS 0.3, radius (1, 0.8, 0.6), scale 0.001 | `knitted_fleece` at 230 mm + `Brick` stitch 1.6 × 1.2 mm; rib displacement baked (01) | grime on the sole 50 %, heel 30 %; pilling on the sole |
| `Cordura.500D.OliveBrown` | Cordura 500D nylon 6.6, PU-coated back, 237 g/m², 0.38 mm → 13 bag, flap, wings, pad tops, cummerbund faces, side pouch; 14 frag pouch | **#50473c** (0.080, 0.063, 0.045; Y 0.065); lit #463e34 box (800–850, 245–262), dust #776958, (790,200) #82705f | 0.78 (0.74 – 0.82 by map) | IOR 1.53, spec 0.35, sheen 0.06 / 0.5 | `Fabric063` at 156 mm + `MG.Weave.Basket` 0.61 mm; per-panel UV, warp along `u`; `Carrier.C.Img.Wear` 4096² (≈ 6 px/mm front set) | dust and pouch-bottom grime from preset `cordura.top` (flap tops #574d3e – #5b5041 lit); edge fuzz at bindings |
| `Cordura.1000D.OliveBrown` | Cordura 1000D, 373 g/m² → 13 pouch bodies, flaps, radio pouch | #4a4137 = 0.85 × 500D (Y 0.055); lit pouch bodies #363028, (832,310) #2f2c27 | 0.80 | as 500D | `Fabric063` at 190 mm | as 500D |
| `Cordura.500D.Black` | Cordura 500D black → 09 knee pockets; 02 collar roll, gussets (`Nylon.Boot.Collar` = this, padded); 14 platform faces | #282624 (Y 0.020); lit knee sleeve #252527 (770,660), boot collar #1f1b17 (725,805) | 0.80; polished 0.62 | spec 0.35, sheen 0.06 | `Fabric063` at 156 mm | knee-pocket polish (`Wear.A` → rough 0.62) and scuffs #4a4b4e 20 %; boot collar dust 0.6 on the roll top |
| `Webbing.Nylon.Black` | MIL-W-17337 / MIL-W-43668-class nylon webbing 25 mm × 1.3 mm; rigger belt 45 mm two-ply → 14 belt, thigh straps, belt PALS; 02 collar strap, pull loop; 11 pull loop; 12 armour straps | #292725 (Y 0.021); lit belt median #22211f, highlight #393632, strap (750,820) #393e47 cool | 0.72; 0.90 at fold edges | spec 0.35, sheen 0.06 | `poly_wool_herringbone` at 280 mm across `u` ×0.5; strip UV, `u` along the strap; ≈ 4 px/mm masks | `MG.Weave.Herringbone` (rib 2.5 mm, distortion 2, twill 1.2 mm at 30 %); selvedge fuzz 2 mm (+10 % value, rough 0.9); dust on top edges |
| `Webbing.Nylon.OliveBrown` | carrier webbing dyed to match → 13 PALS strips, straps, keepers, stubs, pull strips, bungee sleeves | #574c3d (0.096, 0.072, 0.046; Y 0.075); lit #625745 (rows y 240 – 265), (890,375) #4b423a | 0.72 | as above | as above | edge fuzz ×1.25; stress whitening 0.3 under loaded rows 2 – 4 (`Wear2.G`) |
| `Webbing.Nylon.Coyote` | Coyote Brown 498 webbing → 14 right hanger; 12 kneepad strap tails | #826c51 (0.222, 0.149, 0.083; Y 0.159); lit hanger #736054 | 0.72 | as above | as above | dust |
| `Binding.Grosgrain.Black` | nylon grosgrain binding tape 19 – 25 mm, folded → 13 all bindings and flap rims; 11 cuff binding; 09 hook-and-loop edge binding | #2a2826 (Y 0.021) | 0.60 | spec 0.40, sheen 0.06 | strip UV | `MG.Weave.Grosgrain` (rib 0.6 mm across, 0.05 mm); corner wear → #3a3430 (`Wear.B`) |
| `Elastic.Woven.Black` | woven polyester/rubber elastic → 11 wrist band; 12 bicep strap; 13 keepers, cummerbund elastic; 14 keeper, cradle bands | #262423 (Y 0.018) | 0.82 | sheen 0.06 | strip UV | rib Wave 1.0 mm across (0.15 mm); edge fuzz +5 %; no other wear |
| `Cord.Braided.Black` | braided polyester shock cord Ø 3 mm → 09 grommet loop; 14 bungee | #262423 | 0.75 | sheen 0.08 | curve UV | `MG.Braid` (0.5 mm repeat, 3 around); dust on tops |
| `HookLoop.Hook.Black` / `HookLoop.Loop.Black` | nylon hook (monofilament) and loop (brushed) tape → 09, 10, 11, 14 | hook #2a2622, loop #282523 | 0.55 / 0.88 | sheen 0 / 0.10 | UV | hook: Voronoi F1 0.35 mm cells, 0.30 mm; loop: Voronoi 1.0 mm + Noise 0.3 mm, 0.40 mm; lint and fluff caught in the loop (dust 0.3) |
| `Thread.Bonded.Black` | bonded nylon Tex 70, Ø 0.35 mm cylinders sunk 0.15 mm → every black or camo item: 02, 09, 10, 11, 12, 14 | #24211e (Y 0.016) | 0.55 | spec 0.5, sheen 0.10 | — | sun-greyed → #3a3430 by up-mask × 0.6; frayed bar-tack ends +15 % |
| `Thread.Bonded.OliveBrown` | the same thread dyed to the Cordura → 13 | #5b4f40 (Y 0.083) | 0.55 | sheen 0.10 | — | as above |
| `Lace.Nylon.Black` | round braided boot lace Ø 4.0 mm → 02 | #302f2b (0.030, 0.028, 0.024; Y 0.028); lit #4a473f (935,850), #41362d (915,840) | 0.72 | sheen 0.10 / 0.5 | curve UV | `MG.Braid` (0.7 mm repeat, 3 around, 0.15 mm, groove × 0.8); dust 0.3 on up-facing segments; aglets `Polymer.Black.Smooth` |
| `Neoprene.Black` | SCR neoprene with nylon-jersey faces → 11 gauntlet; 12 sleeves, bases, backing | #262526 (Y 0.019); lit cuff shadow #2c2a2b (872,425), cool #444d5c (868,434) | 0.78 | sheen 0.06 | UV or Box, never Object | tricot face Wave 0.3 mm (0.08 mm); light dust |
| `Foam.ClosedCell.Black` | EVA / PE foam → 11 visible foam edge; 12 pads | #2a2a29 (Y 0.023) | 0.90 | — | — | cell Voronoi 0.3 mm (0.1 mm) |
| `SpacerMesh.Black` | 3-D spacer mesh → 13 pad undersides, cummerbund edge ribs | #262523 (Y 0.019) | 0.85 | — | UV | hex Voronoi 4 mm cells, 0.6 mm; Hypalon variant rough 0.55, flat |
| `Knit.Glove.Honeycomb` | M-Pact-class stretch knit, embossed honeycomb → 11 back, fourchettes, thumb back | (0.036, 0.033, 0.030) #353330 (Y 0.033); lit dorsum #57504b (698,345) | 0.72 floor / 0.62 walls | sheen 0.06 | spec 11 generated honeycomb tile (2.4 mm cells) + `cotton_jersey` at 115 mm in the floors | dust R 1.0 / L 0.7 (25 % on knit); pilling on knuckle webs |
| `Fabric.BackFace` | the reverse of any cloth → 09 pocket interiors, 02 hidden linings | parent albedo × 0.8 | parent + 0.05 | parent | parent | none |

#### 3.3.5 Leather, rubber, TPR

| ID | Identity → used by | Albedo; lit target | Rough | Other | Maps, UV, td | Layers and wear |
|---|---|---|---|---|---|---|
| `Leather.Boot.FullGrain` | Lowa Zephyr-class black full-grain bovine upper → 02 vamp, quarters, stays, counter, tongue face, keepers | (0.026, 0.024, 0.022) #2d2b29 (Y 0.024); lit R vamp #2f2c27 (690,855), R quarter #101115 (740,840), L lateral #3e444e (955,840), dust highlight #a19689 | 0.50; polish 0.36, dust 0.78 | IOR 1.50, spec 0.5, coat 0.12 / 0.30 on polish zones | `Leather032` at 80 mm (1.0 mm cells); `UV.Atlas` both boots in one 2048² (≈ 6 px/mm), grain through `UV.Real` | crease crests +0.012 albedo, +0.1 rough; polish (`Wear.A`); scuff streaks (anisotropic noise 1 : 1 : 14, 6 %); dust and height-band grime from preset `boot.toe` (side factor L 1.0 / R 0.7) |
| `Leather.Glove.Goat` | goatskin palm 0.9 mm → 11 palm, palm thumb, heel patch | (0.028, 0.025, 0.023) #2f2c2a (Y 0.025); lit polished pads #3d3836 | 0.50 (crest 0.44, floor 0.58); polish 0.28 – 0.32 | coat 0.08 / 0.25 on polish | `Leather037` at 41 mm (0.6 mm) | compression creases 1.5 mm; polish `Wear.A`; grime in the grip zones |
| `Rubber.Outsole.Black` | Vibram-class carbon-black rubber → 02 outsole, lugs, teeth | 0.018 #242424; lit lugs #010101 (crushed), edge #202227 (720,890) | 0.50 – 0.70 (noise 17 mm) | IOR 1.52, spec 0.5 | `Rubber004` at 50 mm ×0.3 on the sidewall; micro grain Noise 0.15 mm | lug tops (n·−Z > 0.7) → albedo 0.14, rough 0.75; sides stay black |
| `Rubber.Rand.Black` | rubber rand, toe bumper, lip → 02 | 0.020 #272727; lit bumper top dust #423c36, L bumper spec #4a5363 | 0.48 bumper / 0.55 rand | as above | as above | scuff (`Wear.B`) and dust masks |
| `EVA.Midsole.BlueGrey` | moulded PU midsole, painted edge → 02 | (0.020, 0.022, 0.027) #27292e; lit #333a48 (700,880) | 0.30 (0.26 – 0.36) | spec 0.6 | — | cell bump 0.08 mm; grime 30 % |
| `Rubber.Moulded.Black` | moulded rubber → 13 antenna cap; 14 tension-screw washers; 15 butt pad, light button | #262729 (Y 0.020); lit cap #121618 (904,140) | 0.62 (cap), 0.78 (butt pad, light button; spec 15), 0.85 (washers) | IOR 1.52; sheen 0.03 on the pad | `Rubber004` at 50 mm ×0.3 | butt pad dust grey with a clean crescent (15) |
| `Rubber.Red` | red TPR / silicone pull tab → 12 left kneepad | #8a4a4c (0.254, 0.068, 0.072; Y 0.108); lit #917a7b (927,640) cool | 0.60 | subsurface 0.05, radius 1 mm | — | dust 15 % on top |
| `TPR.Glove.Black` | thermoplastic rubber knuckle plate and pads → 11 | (0.022, 0.021, 0.020) #292827 (Y 0.021); lit boss #4f4a47 (727,352), dusty crest #9c908a (709,353) | 0.56 + grain Noise 0.05 mm (±0.06) | spec 0.45 | spec 11 UV atlas (≈ 8 px/mm) | dust crests × 1.6 (R 1.0 / L 0.7); scuffs → 0.40 and +15 % grey |

#### 3.3.6 Polymers and paints

| ID | Identity → used by | Albedo; lit target | Rough | Other | Maps, UV, td | Layers and wear |
|---|---|---|---|---|---|---|
| `Polymer.Black.Smooth` | POM acetal / PA moulding (ITW Nexus-class buckles) → 13 SR buckles, slide-lock, cord lock, knife handle, radio body; 14 clips, latch; 12 strobe body; 02 aglets | #232325 (Y 0.017); lit buckle #1c1c1e (710,525), edge #3c3d45 | 0.40 | IOR 1.48, spec 0.5 | `Plastic012B` at 100 mm; Box projection, blend 0.2 | `MG.Mask.EdgeBevel` → +0.012 albedo, +0.08 rough (abraded); dust 0.2 |
| `Polymer.Black.Textured` | glass-filled nylon with a moulded texture → 14 carrier bodies, platform core; 15 stock, stock latch, A2 grip | (0.030, 0.028, 0.026) #302f2d (Y 0.028; spec 15's value, C47); lit stock #3d3733 median, cheek #5e4f44, butt #141211 | 0.55 | IOR 1.53, spec 0.5 | stipple Noise 0.15 mm (0.01 mm) + `Plastic012B` ×0.2; grip checkering and side pebble per spec 15 | scuff streaks → (0.10, 0.09, 0.085), rough 0.42, anisotropic 1 : 1 : 14 (15); dust in recesses |
| `Polymer.Grey.Light` | moulded grey polymer elbow cap → 12 left elbow cap (mirrored right), guard window insert | #7b818a (Y 0.217); lit fin #9aa8b5, pad #515c67 (cool) | 0.50 | IOR 1.50 | moulded micro-texture | moulded in colour, so scuffs lighten (no chips; 12's 2 % chips dropped) |
| `Polymer.Grey.Case` | ABS rigid utility case → 14 left hip box | (0.085, 0.092, 0.092) #525656 (Y 0.091); lit #363a3b (948,505), top #4e504d | 0.55; parting lip 0.40 | IOR 1.53 | stipple Noise 0.15 mm | none (a newer item) |
| `Polymer.Grey.PMAG` | Magpul PMAG 30 GEN M3, Stealth Gray → 15 magazine body and floorplate | (0.075, 0.072, 0.068) #4d4c4a (Y 0.072; spec 15); lit median #423e3a, ribs #625a56, floorplate #595452 | 0.60 | IOR 1.53 | spec 15's diamond texture panels (1.5 mm) and dot matrix (0.8 mm) | rib-crest and floorplate-flare scuffs → (0.15, 0.14, 0.13), rough 0.45 |
| `Polymer.Tan.Painted` | black moulded polymer field-painted with matte aerosol tan (D8) → 12 pauldron tiers, guard plates, kneepad frames and centres, strobe clip; 13 admin panel tray (tint (0.92, 1.0, 0.92)) | #837163 (0.227, 0.165, 0.125; Y 0.175); per piece ×1.0 pauldrons and guards, ×0.92 kneepad frames, ×0.85 kneepad centres; lit right cap #90877c, right guard #d1bbaa (655,328), panel P3 #897967 (800,220), R kneepad frame #5f554f (703,650) | 0.55 (0.45 – 0.65 by `Plastic018B`) | IOR 1.50, spec 0.5 | `Plastic018B` at 60 mm; per-piece `Armour.<Side>.Img.Wear` 2048² (6 – 8 px/mm) | `MG.Paint.OrangePeel` (1.0 mm, 4 % slope); scratches (anisotropic noise along the limb); `MG.Weather.Chips` presets `paint.centre` (30 – 40 %), `paint.frame` (3 – 5 %), `paint.rib` (along ribs); substrate #2e2b27 → #453d3b, rough 0.38; dust `armour.top` up to 55 %; grime in slots; soot streaks on the right guard (#3a332e at 60 %); stencil decal |
| `Polymer.Tan.Moulded` | moulded-in-colour FDE polymer face plates → 14 drop-leg face plates, flank plate | (0.200, 0.155, 0.115) #7c6e5f (Y 0.162); lit highlight #816f5f, (690,540) #4c4034 | 0.50 | IOR 1.50 | `Plastic018B` tinted at 120 mm | scuffs → (0.26, 0.21, 0.165) stress-whitened, rough 0.60; dust 0.55; stencils |
| `Paint.FDE.Brushed` | hand-applied flat dark earth enamel over hardcoat, tape-masked → 15 patches P1–P6 | #b8905f (0.479, 0.279, 0.114; Y 0.310); lit upper stripe #d4a271 (767,342), stock stripe #a68869, stock frame #bf9c70 | 0.62 | IOR 1.50 | patch masks of spec 15 §5.4 (projected along ±X) | brush streaks along each patch (±0.04 value, anisotropic 1 : 1 : 10, spec 15) with Gabor relief 0.004 mm; orange peel ±0.006 mm; masked-edge ridge 0.03 mm; chips `paint.overcoat` (Voronoi 400 m⁻¹, Tₑ ≈ 0.62 ≈ 25 %, × `touch`) to the material beneath, Step 0.08 mm (brushed enamel is thicker than aerosol) |
| `Paint.Stencil.Black` / `Paint.Stencil.Light` / `Paint.Emblem.White` | thin sprayed stencil paints and the emblem's white mark → 12 guards, 14 plates, 12 emblem | black #2b2927 (Y 0.022; 12's #141210 raised to the floor), light #9a948a, white #e8ecee | 0.50 / 0.62 / 0.50 | — | decal masks from `decal.py` (§4.9) | eroded 30 – 60 %; white mark with a 0.06 mm step |

#### 3.3.7 Metals and coatings

| ID | Identity → used by | F0 or albedo; lit target | Rough | Other | Maps | Layers and wear |
|---|---|---|---|---|---|---|
| `Metal.Gunmetal` | black-oxide / phosphated stamped steel → 13 ladder-locks, tri-glides, keeper bars, grommets; 14 ladder-locks, cobra buckle; 02 eyelets, speed hooks, collar buckle; 09 button, grommets, zip pull; 12 ladder-locks, strobe rim | F0 (0.100, 0.100, 0.105) #59595b; lit eyelet #37302c (706,816), keeper specular #b9a99a (742,208), ladder-lock #4c4943 (733,527) | 0.45 (0.38 – 0.52) | metallic 1; anisotropy 0.3 along bars | `Metal027` at 60 mm | `MG.Mask.EdgeBevel` (0.8 mm) → bare steel F0 (0.56, 0.57, 0.58), rough 0.25; a strap-run stroke on each bar |
| `Metal.Nickel` | nickel-plated steel or brass → 12 rivets, studs, cam buckles; 13 panel studs; 14 snaps | F0 (0.66, 0.61, 0.53) #d4cdc0 [S: published F0 tables; VERIFY]; lit stud #969491 (752,208) | 0.25 | metallic 1 | `Metal063` at 20 mm ×0.5 | handling smudge ±0.1; dust 0.15 up-faces; the blue speculars are the cool light |
| `Metal.Stainless` | 304 stainless → 13 screws; 14 D-ring, screws, latch pin, tension screws | F0 (0.60, 0.59, 0.57) [E: between Fe, Cr and Ni] | 0.28 | metallic 1 | `Metal063` at 20 mm | smudge |
| `Metal.Steel.Turned` ("steel") | turned or ground carbon steel → 13 antenna lower segment; bare edges of every steel part | F0 (0.56, 0.57, 0.58) [S]; lit #777f85 (908,172) | 0.30 | metallic 1, anisotropic 0.4 along the lathe axis | — | turning marks Wave 0.2 mm (0.002 mm) |
| `Metal.Steel.Polished` ("bright bolt steel") | steel polished by use → 15 carrier bearing bands, bolt face, trigger face, mag release, takedown-pin heads | F0 (0.56, 0.57, 0.58); lit glint (793,384) | 0.15 | anisotropic 0.5 along the wear | — | carbon at the carrier's front |
| `Metal.Steel.Phosphate` | manganese phosphate, oiled → 15 bolt-carrier body, barrel nut, castle nut, end plate, pins, roll pins, set screws, gas block (nitride), grip screw | base (0.060, 0.062, 0.060), metallic 0.3 (C44) | 0.62 | coat 0.2 (oil film), coat rough 0.30, coat IOR 1.47 | — | crystal Noise 0.03 mm; polish mask (`touch` and spec 15's list) → `Metal.Steel.Polished` |
| `Metal.Steel.Blued` ("blued steel") | hot-blued or black-oxide steel → 15 socket screws (handguard clamp, light mount), QD inserts | F0 (0.060, 0.065, 0.075) #45484d; Specular Tint (0.6, 0.7, 1.0) for the blue grazing reflection (spec 15) | 0.30 | metallic 1 | — | Bevel edge → `Metal.Steel.Turned` on screw heads |
| `Metal.Aluminium.Hardcoat.Black` (+ `.Gloss`) | 7075-T6 / 6061-T6, bead-blasted, MIL-A-8625 Type III Class 2 black → 15 upper, lower, rails, handguard, trigger guard, light and optic mounts; `.Gloss` on the receiver extension, light body and head, optic body | `MG.Anodise` dye black: base (0.025, 0.025, 0.027), metallic 1; lit upper #413c3b median, lit edge #686463, handguard #393532, light #302f30, tube highlight #b5b0b1 | base 0.55, coat 0.45; `.Gloss` coat 0.32 tube / 0.40 light / 0.36 optic | coat weight 1.0, coat IOR 1.65 | `Metal038` NormalGL ×0.15 as micro-structure (15) | bead-blast Noise 0.05 mm (0.002 mm); thinning to grey 0.09 over 35 mm noise, 0 – 35 %; `MG.Mask.EdgeBevel` (0.8 mm) × `touch` → bare aluminium F0 (0.91, 0.92, 0.92), rough 0.35, residual oxide coat 0.3 (C43), half strength on `.Gloss`; etched markings (0.20, 0.20, 0.19), rough 0.60 (15 §4.16); dust in slots and holes; carbon in the port |
| `Metal.Aluminium.Anodised.Grey` | grey-dyed anodise → 13 label plate | base (0.18, 0.18, 0.19) #767679; lit (782,206) #766f6c | 0.38; coat 0.30 | coat 1.0 / 1.65 | 13's label bump image | edge Bevel → bare Al |
| `Metal.Aluminium.Anodised.ClearBrushed` | brushed 5052, clear anodise → 12 emblem plate | base (0.50, 0.51, 0.52) #bcbdbf; lit (942,212) #b3c2d6 cool, highlight #bfcedc | 0.32; coat 0.20 | anisotropic 0.6, rotation along the plate's `v`; coat 1.0 / 1.65 | 512² emblem mask | brushing: Gabor 2D anisotropy 1.0 along `v`, 0.05 mm → rough ±0.08, 0.001 mm relief; 3 – 4 diagonal scratches (rough 0.15); white mark decal; dust 10 % on the upper third |
| `Metal.Aluminium.Anodised.Gold` | gold-dyed anodise → 14 keeper-tail tips, cord ends, grommet | base (0.45, 0.33, 0.17) #b39b73 | 0.40; coat 0.35 | coat 1.0 / 1.65 | — | edge Bevel → bare Al |
| `Metal.Brass.Aged` | turned brass, tarnished → 13 antenna sleeve | base (0.55, 0.42, 0.22) mixed 60 % with tarnish (0.30, 0.25, 0.17) by Noise 2.5 mm; lit #705e46 (903,152), specular #d3caaf | 0.38; 0.22 on the groove shoulders | metallic 1, anisotropic 0.5 along the axis | — | turning marks Wave 0.2 mm |
| `Coating.Cerakote.BurntBronze` | Cerakote H-148 Burnt Bronze ceramic-polymer film ≈ 25 µm → 15 barrel, A2 flash hider, crush washer | base (0.135, 0.082, 0.050) #67513f (Y 0.091), metallic 0.45 (spec 15, C45) [VERIFY against an H-148 swatch]; lit (874,554) #5f4c3e to #6a5344 | 0.38 | IOR 1.50, spec 0.5 | — | metallic flake (Voronoi 0.08 mm, roughness ±0.06); soot (0.012, 0.011, 0.010) #1d1b19, rough 0.85, from spec 15's sources (A2 slots, front ring, last 10 mm of barrel); edge wear to phosphate on the A2's flats and front ring |

#### 3.3.8 Lenses, glass and scene

| ID | Identity → used by | Values |
|---|---|---|
| `Lens.Strobe.Polycarbonate` | frosted PC dome of the IR strobe → 12 | base #9aa7b3, transmission 0.35, roughness 0.30, IOR 1.58, Volume Scatter density 40 m⁻¹; emission 0 (game flash variant 2.0); lit #afc1d3 (952,268) |
| `Glass.Optic.Coated` | T-2 objective and ocular, light window (15) | transmission 1.0, IOR 1.52, roughness 0.02; front lens Thin Film 300 nm at IOR 1.38 (blue-green reflex), rear lens 520 nm (amber), as spec 15 sets them (C46); the consolidated analysis's "faint blue lens" is the front film |
| `Glass.Light.TIR` | M300C total-internal-reflection optic (15) | PMMA, transmission 1.0, IOR 1.49, roughness 0.05; the reflector behind it is vacuum-metallised aluminium, F0 (0.91, 0.92, 0.92), roughness 0.05 (the bare-aluminium layer of `MG.Anodise` with Dye 1 and no coat) |
| `Scene.Concrete.Polished` | spec 17 `Scene.Mat.Floor.Concrete` | owned by spec 17 §5.1 (a plain floor plane now, per the scope note); the library only registers the ID |

### 3.4 Real constructions behind the scales and values

| Item | Value | Mark and reasoning |
|---|---|---|
| Cordura 500D | 237 g/m² (7 oz/yd², coated), 0.38 mm thick | S: Rocky Woods 500D coated Cordura listing |
| Cordura 500D yarn pitch | 0.61 mm: 16.4 threads per 10 mm each way | E: 500 den = 0.0556 g/m; ≈ 200 g/m² of nylon ÷ 0.0556 g/m = 3600 m/m² of yarn, ÷ 2 directions, crimp 10 % → 1640 yarns/m |
| Cordura 1000D | 373 g/m² (11 oz/yd²); pitch 0.74 mm: 13.5 threads per 10 mm | S (class weight) / E (same mass balance) |
| NYCO ripstop | 224 – 230 g/m² (6.6 – 6.8 oz/yd²), 0.50 mm; ≈ 40 ends × 20 picks per 10 mm (0.25 × 0.50 mm) | S: `research_dimensions` §5 (weight); E: spec 09 §3 (count) |
| Ripstop interval | 6.0 mm, doubled yarns 0.5 mm | E (C4); one ripstop cloth standard requires ≥ 4.5 repeats per inch (≤ 5.64 mm) [S: PIA ripstop specification, via search] |
| 4-way stretch woven | ≈ 0.24 mm yarn: 42 threads per 10 mm | E |
| FR jersey | course 0.69 mm (14.5 courses per 10 mm), wale ≈ 0.9 mm (11 wales per 10 mm) | M (tile) / E (28 gauge) |
| 2 × 2 rib | wale 4.2 mm, course 1.1 mm | spec 10 (image + E) |
| Microfleece | pile 1 – 2 mm, clumps 1.6 mm | spec 10 / E |
| Webbing | 25.4 × 1.3 mm; herringbone period 2.5 mm across, twill 1.2 mm | E (research F §1, specs 13, 14) [VERIFY on a MIL-W-43668 macro photograph] |
| Grosgrain binding | 19 – 25 mm folded, rib 0.6 mm | E |
| Thread | bonded nylon Tex 70, Ø 0.35 mm, stitch 2.2 – 3.6 mm | research F §8, spec 09 |
| Boot lace | Ø 4.0 mm, braid diamond 0.7 mm | spec 02, research F §5 |
| Boot leather grain | cells 0.5 – 1.5 mm, pores 0.05 – 0.10 mm | E |
| Goat leather grain | pebble 0.6 mm, pore rows 0.25 mm | spec 11 |
| Aerosol paint orange peel | wavelength 0.5 – 1.0 mm, height 2 – 10 µm, visible slope 3 – 6 % | E (automotive "short-wave" orange-peel range) |
| Moulded polymer texture | VDI 3400 Ref 24 – 33 (Ra 1.6 – 4.5 µm): reads as roughness 0.45 – 0.60, no visible relief | S (VDI 3400 scale) / E (mapping to GGX roughness) |
| Type III hardcoat | oxide 25 – 50 µm, n ≈ 1.65, bead-blast Ra 1 – 3 µm | S (MIL-A-8625 class), E |
| Cerakote H-series film | ≈ 25 µm | S (manufacturer's typical film build) |
| Metal F0 (linear) | iron and carbon steel (0.56, 0.57, 0.58); aluminium (0.91, 0.92, 0.92); nickel (0.66, 0.61, 0.53); brass (0.91, 0.78, 0.42) clean; chromium (0.55, 0.56, 0.55) | S: Hoffman's physically based shading course tables [VERIFY each against `physicallybased.info` when the library is coded] |
| Dielectric F0 | nylon / polyester / cotton n 1.53 → 4.4 %; acetal 1.48 → 3.7 %; PC 1.58 → 5.1 %; Al₂O₃ 1.65 → 6.0 %; skin 1.40 → 2.8 %; cornea 1.376 → 2.5 %; tear film 1.336 → 2.1 % | S (refractive indices) / computed |
| Dust | dry mineral dust Y ≈ 0.25 – 0.55, paler as it thickens | E (D12) |
| Black dyed textiles, leather, rubber, plastics | Y ≈ 0.015 – 0.04 | E (D2) |

---

## 4. Node-group library (`mat_groups.py`; the construction plan of this part)

### 4.0 Rules for every group
* Names `MG.<Family>.<Name>` (shader) and `MG.GN.<Name>` (geometry nodes). Each group carries `ng["lib_version"]` and `ng["recipe_hash"]`; `materials.ensure_groups()` rebuilds a group whose hash differs and leaves it alone otherwise (§7.4).
* Lengths at the group interface are **millimetres** (converted to metres inside by one Math node), colours are linear, factors are 0–1. Coordinates come in as metres: `UV.Real` for cloth and straps, Object coordinates for smooth noise on hard parts, Box projection (blend 0.2) for tiled maps on hard parts. Object or Generated coordinates never feed a tiled map on a curved surface (research F §3 e; lint rule L7).
* Every group that adds relief outputs a **height in metres**, not a normal. The material sums heights where they share a scale and chains at most three `Bump` nodes (`Distance` 1.0, `Strength` 1.0, each feeding the next one's `Normal`), so relief is physical (§3.1).
* Every group has a `LOD` input: 0 for Cycles renders (all layers), 1 for export bakes (layers finer than 2 texels drop out and add their slope variance to roughness, §5.4 step 5).
* Mask sources: each weathering group takes an optional `Mask` input (−1 = unused). The material builder wires it to an image channel (`<Part>.<Side>.Img.Wear`, §5.3), to a mesh attribute (`wear_*`, §7.1) or leaves it, in which case the group computes the mask from geometry in the shader. The composition order inside every material is fixed: base → print (camouflage, decals) → crest → stress whitening → chips → edge wear → polish → grime → **dust last**.

### 4.1 `MG.Skin.Core` and `MG.Skin.Micro`
`MG.Skin.Core` wraps one Principled BSDF with the constants of §3.3.1 (method Random Walk (Skin), SSS weight 1, SSS IOR 1.4, anisotropy 0.8, IOR 1.40, Specular IOR Level 0.5, sheen 0.04 / 0.5 white) and exposes only what varies by region: Base Color, Roughness, SSS Scale, SSS Radius, Coat Weight, Coat Roughness, Normal. Parts drive those sockets from their own maps and attributes (`skin_tint`, the `Masks` images), so one core serves `Skin.Head`, `Skin.Body` and `Skin.Foot`. `MG.Skin.Micro` outputs a height from five switchable layers whose sizes are inputs: pores (Voronoi `SMOOTH_F1`, cell 0.9–1.4 mm by region, pore radius input, depth 0.05–0.12 mm), primary lines (Voronoi `DISTANCE_TO_EDGE`, 0.5 and 0.15 mm cells, width 0.04 mm, depth 0.03 / 0.015 mm, Mapping stretched 1.6 along the Langer angle input), follicle pits (Voronoi F1 below a threshold, 0.08–0.12 mm deep), friction ridges (Wave `RINGS` or `BANDS`, 0.45–0.5 mm pitch, 0.05 mm), and an orange-peel Noise (1.1 mm, 0.02 mm). The specs' per-region values plug in unchanged; only their bump convention changes to physical heights.

### 4.2 `MG.Weather.Dust` (normal-Z up, plus occlusion, plus large noise; #9a8d85 → #d2c5b5)
Inputs: Base Color, Base Roughness, Base Specular, Amount (preset, §4.10), Up Low 0.25, Up High 0.85, Up Power 2.0, AO Distance mm 15, Noise mm 300, Tile mm 650, Side (object property `wear_dust_scale`, default 1), Edge (from `MG.Mask.EdgeBevel`, default 0), Thin #9a8d85, Thick #d2c5b5, Mask (−1), LOD. Outputs: Color, Roughness, Specular, Coverage, Height, Bump Damp.
1. `Geometry` → `True Normal` → `Separate XYZ` → Z. Optional object-up term (spec 15's rifle, which gathers dust in storage as well as in the hero pose): Z′ = mix(Z, dot(True Normal, object +Z), Local Up), Local Up 0.6 on the rifle, 0 elsewhere.
2. `Map Range` (SMOOTHSTEP) Z from [Up Low, Up High] to [0, 1] → `Math POWER` Up Power → **Up**. True normal, not the bumped one, so weave and grain do not speckle the dust.
3. `Ambient Occlusion` (Distance = AO Distance, samples 8, Only Local off) → `AO` output → `Math SUBTRACT` from 1 → **Occ** (0 open, 1 sheltered). In export mode (LOD 1) the baked AO image replaces the node.
4. **Geo** = Up × (0.7 + 0.6 Occ) × (1 − 0.6 Edge): ledges and inside corners on top faces hold more dust, rubbed edges less.
5. `Noise Texture` 3D on Object coordinates × (1000 / Noise mm), Detail 3, Roughness 0.55 → `Map Range` 0.35–0.65 → **N1**; `MG.Tile.AntiRepeat` of `SurfaceImperfections015_Opacity` at Tile mm (Box projection on hard parts, `UV.Real` on cloth) → **N2**; **N** = 0.6 N1 + 0.4 N2.
6. **Coverage** c = clamp(Geo × N × Amount × Side), or, when Mask ≥ 0, c = clamp(Mask × N × Amount × Side).
7. Thickness t = c². Dust colour = `Mix` (Thin, Thick, t): a thin film reads #9a8d85 against the dark gear, a crust reaches #d2c5b5.
8. Color = `Mix` (Base, Dust colour, c). Roughness = mix(Base Roughness, 0.88, c). Specular = Base Specular × (1 − 0.5 c).
9. Bump Damp = 1 − 0.7 c, which the material multiplies into the weave or grain height (dust fills the relief). Height = c × 0.01 mm × Voronoi F1 (0.05 mm cells): a faint grit that shows only in macro views.
10. The material also scales its Coat and Sheen by (1 − c). Dust never changes Metallic: on metal it is a layer, so the material mixes a dielectric BSDF over the metal by c instead (`mat_hard.dust_over_metal()`).

### 4.3 `MG.Weather.Grime` (inverted Z, plus cavity, plus streaks)
Inputs: Base Color, Base Roughness, Amount, Oil (0 dry … 1 oily), Band Low mm, Band High mm (height above the floor), Bottom (attribute `wear_bottom`, 1 within 30 mm of an object's lowest point), Cavity Weight 0.6, Streak Amount, Streak Length mm 55, Streak Width mm 4, Dry #3a342c, Oily #1a1612, Mask (−1). Outputs: Color, Roughness, Grime.
1. True Normal Z → `Map Range` (SMOOTHSTEP) from [0.2, −0.9] to [0, 1] → **Down** (faces that look at the floor collect splash and handling dirt).
2. `Ambient Occlusion` (Distance 4 mm) → 1 − AO → `Map Range` 0.4–0.9 → **Cav**.
3. `Geometry Position` Z × 1000 → `Map Range` (SMOOTHSTEP) from [Band High, Band Low] to [0, 1] → **Band** (cuffs: 320 → 200 mm; boots: 60 → 20 mm).
4. **Streaks**: Object coordinates → `Mapping` scale (1000 / Width, 1000 / Width, 1000 / Length) so features run along world Z → `Noise` Detail 2 → `Map Range` 0.55–0.75 → × (1 − |Z|) (vertical faces only) × Streak Amount.
5. g = clamp(Amount × max(Cav × Cavity Weight, 0.5 Down, Band, Bottom) × `Map Range`(Noise 80 mm, 0.6–1.0) + Streaks), or Mask × Amount when given.
6. Grime colour = mix(Dry, Oily, Oil). Color = Base × mix(1, 0.45, g), then `Mix` toward Grime colour by 0.3 g (darkens and browns rather than painting a flat colour).
7. Roughness = Base Roughness + g × mix(+0.10, −0.08, Oil): dry dirt is matte, oily grime is slicker.
8. **Soot** is the same group with Oily = soot (0.012, 0.011, 0.010), Oil 0.3, and either streaks along the rub direction (the right forearm guard's diagonal streaks, spec 12: Mapping rotated 35° to the guard axis) or **sources** (spec 15's `Wear.Carbon`): up to eight source points with an axis each, read from the attribute `soot` that `MG.GN.Touch` writes from Empties named `<Part>.Src.*` (a cone of 15° and 25 mm forward of each A2 slot, a ring at the A2's front, the port's rear edge, the deflector face, the bolt face).

### 4.4 Edge wear and chips
**`MG.Mask.EdgeBevel`** (spec 15's `Wear.EdgeBevel`): Inputs Radius mm 0.8, Width 0.08, Noise mm 0.6, Noise Amount 0.5, Zone (attribute `wear_zone` or `Wear.B`, default 1). Output Edge.
1. `Bevel` (Radius = mm / 1000, Samples 4) → shading normal of a virtually rounded edge.
2. `Vector Math DOT` with `Geometry` True Normal → `Math SUBTRACT` from 1 → **d** (0 on flats, rising on edges).
3. `Map Range` (SMOOTHSTEP) d from [0, Width] to [0, 1].
4. × `Map Range`(`Noise` at Noise mm, 0.3–1.0) × Noise Amount + (1 − Noise Amount), then × Zone.
This is a shading-point mask with no mesh dependence (research F §6: about 10 % render time), so it works on boolean hard surfaces where `Pointiness` fails; in export mode the baked `Wear.B` replaces it. It applies to metal, polymer, paint and leather; on cloth the crest attribute plays the same role (§4.5).

**`MG.GN.Touch`** (spec 15's `Wear.Touch`, also useful for the gloves and straps): a geometry-nodes group that reads the Empties `<Part>.Touch.*` (each with a radius of 25–40 mm) and writes the point attribute `touch` = clamp(Σ smoothstep(r, 0, distance)); likewise `soot` from `<Part>.Src.*`. Materials read `touch` to raise edge wear × 1.8, chipping × 2 and polish on steel, exactly as spec 15 §5.3 lists its contact anchors.

**`MG.Weather.Edge`** mixes a worn surface over the base by Edge × Amount: Inputs Base (Color, Roughness, Metallic, Coat), Worn (Color or F0, Roughness, Metallic, Coat), Edge, Amount. Gunmetal → bare steel; hardcoat → bare aluminium (coat to 0); black polymer → +0.012 albedo and +0.08 roughness; leather → polish.

**`MG.Weather.Chips`** (the hard-edged variant that exposes the substrate):
Inputs: Scale (cells per metre: 120 kneepad centres for 5–8 mm flakes, 220 frames, ribs and panel faces for 2–4 mm, 400 rifle paint for 2.5 mm cells as spec 15 sets them), Thresholds at mean wear T_centre 0.48, T_rib 0.65, T_frame 0.71, T_paint 0.55 (rifle; Tₑ ≈ 0.62 at w 0.5, spec 15's ≈ 25 %), Edge (from `MG.Mask.EdgeBevel`, radius 1.2 mm on armour), Region (attribute `wear_region`: centre 1.0, rib 0.6, frame 0.3), Paint (Color, Roughness, Height), Substrate Low #2e2b27, Substrate High #453d3b, Substrate Roughness 0.38, Step mm 0.05, Mask (−1). Outputs: Color, Roughness, Height, Chip.
1. `Voronoi` 3D F1, Randomness 0.9, Smoothness 0, on Object coordinates × Scale → Distance **v**.
2. Ragged outline: v + 0.08 × (`Noise` 8 mm − 0.5) and the minimum with a second Voronoi at 3 × Scale (sub-flakes) → **v′**.
3. Threshold: T = `Color Ramp` (CONSTANT) of Region with stops 0.3 → T_frame, 0.6 → T_rib, 1.0 → T_centre; wear w = 0.6 Edge + 0.2 Occ + 0.2 `Noise` (60 m⁻¹), or the baked `Wear.B` when Mask ≥ 0; Tₑ = T + 0.15 (1 − w). Chips gather on knocked edges and sheltered rims and thin out on open faces.
4. Chip = `Map Range` (LINEAR) v′ from [Tₑ, Tₑ + 0.01] to [0, 1]: the regions far from every Voronoi feature point, i.e. irregular star-shaped flakes along the cell network, with a 0.1–0.2 mm edge. Coverage against threshold, simulated for Blender's jittered 3D Voronoi (randomness 0.9) on a surface slice: d > 0.54 covers 42 %, > 0.60 29 %, > 0.65 19 %, > 0.72 9 %, > 0.80 3 %. With w = 0.5 the thresholds above therefore give about 38 % on kneepad centres, 9 % along ribs, 4 % on frames (spec 12's 30–40 %, ribs, 3–5 %) and 23 % on the rifle's paint (spec 15's 20–30 %); M5 measures it on the wear block.
5. Substrate colour = `Mix`(Low, High, `Noise` 5 mm); Color = `Mix`(Paint Color, Substrate, Chip); Roughness = mix(Paint Roughness, Substrate Roughness, Chip).
6. Height = Paint Height × (1 − Chip) + Step × (1 − Chip): the paint stands 0.05 mm proud of the substrate (aerosol dry film 25–50 µm), so every flake's upper rim catches the key (research F §3 b).
7. Chip feeds `MG.Weather.Dust` as +20 % dust inside flakes (the step traps it).
For moulded-in-colour polymer (`Polymer.Tan.Moulded`, `Polymer.Grey.Light`) the same group runs with Substrate = the stress-whitened colour (§4.5) and Step 0: a scuff, not a flake.

### 4.5 Fabric: crest sheen and stress whitening
**`MG.GN.Crest`** (geometry nodes, run by the part after simulation or posing): for each point, convexity = dot(N, P − mean of edge-neighbour positions) ÷ mean edge length (`Edges of Vertex`, `Evaluate at Index`, `Accumulate Field`), `Blur Attribute` (2 iterations), `Map Range` from [0.02, 0.15] to [0, 1] → stored as point float `crest`. It works on sparse and dense meshes alike; `Pointiness` is accepted only on dense sim meshes (≥ 1 vertex per 5 mm), never on booleans (lint L8).

**`MG.Fabric.Crest`** ("fabric sheen on fold crests"): Inputs Crest (attribute `crest`, `Wear2.R`, or Pointiness remapped 0.52–0.62), Base Color, Base Roughness, Base Sheen, Amount. Outputs Color, Roughness, Sheen.
1. c = Crest × `Map Range`(`Noise` 20 mm, 0.6–1.0) × Amount.
2. `Separate Color` HSV → V × (1 + 0.10 c), S × (1 − 0.10 c) → `Combine Color`: abraded fibre tips are paler and greyer (the analysis's crest highlights #6f6760–#7f7165 on the shirt).
3. Roughness − 0.08 c (crushed, polished fibres reflect more coherently).
4. Sheen + 0.03 c, clamped to the class cap 0.12. The lift comes mostly from steps 2 and 3, so it does not depend on the light (§2.5).

**`MG.Fabric.StressWhite`**: Inputs Stress (attribute `stress` from the part: distance to the gusset seams and the top 150 mm of the inseams for spec 09, loaded PALS rows for spec 13, bend lines for moulded polymer), Base Color, Whitened Color (camo #4a443c; generic = Base with V × 1.35 and S × 0.6; moulded tan (0.26, 0.21, 0.165)), Amount, Noise mm 3.3. Outputs Color, Roughness, Sheen.
1. w = Stress × `Map Range`(`Noise` at Noise mm, 0.4–1.0) × Amount × (Crest × 0.5 + 0.5) (whitening shows on the proud yarns).
2. Color = `Mix`(Base, Whitened, w); Roughness + 0.05 w; Sheen + 0.02 w (exposed fibre cores).

**`MG.Polish`**: Inputs Polish (`Wear.A` or attribute `polish`), Base Roughness, Polished Roughness (leather 0.28–0.36, Cordura 0.62, steel 0.15), Coat (leather 0.08–0.12), Color Shift (glove dye wears to (0.045, 0.040, 0.037)). Outputs Roughness, Coat, Color. A plain mix by Polish × `Map Range`(`Noise` 4 mm, 0.3–1.0).

### 4.6 `MG.Camo.Blotch4` — the camouflage generator (prototyped, calibrated and measured for this spec)
Inputs: Vector (`UV.Real`, metres), Seed 7.0, T0 … T3 (linear colours), Cut1 / Cut2 / Cut3, Edge, Dither, Level 1.0, LOD. Outputs: Color, Field, Tone (0–3 continuous), Rough Offset.
1. **Warp**: `Noise Texture` 4D FBM, normalize on, W = Seed + 11.3, Vector = V, Scale 40 m⁻¹ (25 mm), Detail 2, Roughness 0.5 → `Color` − (0.5, 0.5, 0.5) → × 0.012 m (±6 mm) → `Vector Math ADD` V → **Vw**.
2. **Blotch B**: Noise 4D FBM, W = Seed + 1.7, Vector = Vw, Scale 12.5 m⁻¹ (80 mm), Detail 2, Roughness 0.45.
3. **Macro M**: Noise 4D FBM, W = Seed + 3.1, Vector = V (unwarped), Scale 4.545 m⁻¹ (220 mm), Detail 1, Roughness 0.5.
4. **Speckle S**: Noise 4D FBM, W = Seed + 5.3, Vector = Vw, Scale 71.4 m⁻¹ (14 mm), Detail 1, Roughness 0.5.
5. **Field** F = 0.60 B + 0.25 M + 0.15 S (Math MULTIPLY and ADD). Measured over 4 m²: mean 0.4996, σ 0.0556.
6. **Print grain**: Noise 3D, Vector = V, Scale 2222 m⁻¹ (0.45 mm, one yarn crown), Detail 0 → − 0.5 → × Dither → added to F → **Fd**. At LOD 1 Dither is replaced by an equal widening of Edge, since a sub-texel dither cannot be baked.
7. For k = 1, 2, 3: `Map Range` (SMOOTHSTEP) Fd from [Cutₖ − Edge, Cutₖ + Edge] to [0, 1] → **sₖ**.
8. Color = Mix(Mix(Mix(T0, T1, s1), T2, s2), T3, s3) × Level (three `Mix` RGBA nodes and one scale). This is exactly a four-colour ramp with soft stops; read as a `Color Ramp` (EASE) on Fd it has stops at 0.4657 #292924, 0.4737 #423f39, 0.5178 #423f39, 0.5258 #5b554c, 0.5679 #5b554c and 0.5759 #847464. The Mix chain is used instead because the cuts and the edge must be group inputs, which ramp stops cannot be.
9. Tone = s1 + s2 + s3; Rough Offset = 0.02 × (1.5 − Tone) / 1.5 (darker dye loads are marginally rougher).

Calibrated values (stored in `mat_catalogue.CAMO`; `materials.camo_calibrate()` recomputes them whenever steps 1–5 change): **Cut1 0.4697, Cut2 0.5218, Cut3 0.5719** (the 30th, 65th and 90th percentiles of F, from a 2 × 2 m Emit bake at 2048², 0.98 mm per texel); median |∇F| at the cuts **0.0045 per mm** (p25–p75 0.0029–0.0064); **Edge 0.004, Dither 0.010** give a transition (Dither + 2 Edge) ÷ |∇F| of **4.0 mm** median (2.8–6.2 mm p25–p75). That is soft at the hero's 2.1 mm per pixel and, at 0.09 mm per pixel, a broken band of ink on the yarn crowns rather than a blur (D4). Voronoi is not used: its cells are convex and near-uniform in size, while the reference's blotch sizes are skewed (p75/p50 ≈ 1.3–1.9), and the noise sum reproduces that skew (measured 1.6–1.9). Trousers use Seed 7 with the per-panel island offsets of spec 09 §4.4, so the pattern breaks at every seam as a cut-and-sewn garment does; the left and right legs are never mirrored.

**Verification against the reference** (V5; `camo_stats.py` applies spec 09 §2.3's exact method: luminance high-passed by a 12 px Gaussian, blobs above the 70th and below the 30th percentile, connected components of 10 px or more, equivalent diameters at 2.12 mm/px; sixteen random 90 × 35 and 70 × 85 px windows of a 1 × 1 m bake at 4.72 px/cm). The "display" row passes the albedo through spec 17's AgX Medium High Contrast table and black crush at E = 1.0:

| | Light blotches p25 / p50 / p75 / max (mm) | Dark blotches | Contrast (p90 − p10)/mean | Tone fractions |
|---|---|---|---|---|
| Reference, four windows (spec 09 §2.3) | 11–21 / 16–25 / 28–34 / 47–53 | 8–11 / 13–18 / 15–33 / 42–61 | 101–134 % (draped, folds and dust included) | k-means 32 / 39 / 23 / 6 |
| Prototype, albedo | 13 / 18 / 34 / 61 | 12 / 18 / 29 / 62 | 53 % | 30 / 35 / 24 / 10 |
| Prototype, display (E 1.0) | 11 / 18 / 31 / 59 | 12 / 18 / 28 / 56 | 83 % | — |

Quartiles, medians and fractions land inside the reference ranges; the largest light blotch (59–61 mm) is 6–8 mm above the reference's 47–53 mm, drawn from only four windows; if spec 09's hero windows confirm it, the macro weight drops from 0.25 to 0.20 and the cuts are recalibrated. The flat swatch's contrast is lower because a flat swatch has no folds, creases or dust, which the draped hero render adds (spec 09 V1 is therefore the contrast test, 101–134 %; the flat swatch must read 60–90 %). Side by side, the bake reads as the same family as the reference legs (`ref/zoom_materials16_camo_compare.png`: reference thighs | bake at reference scale | 100 mm macro). The prototype took 7 s for the 2048² field bake and 16 s for the four colour bakes.

**Tones.** T0 #292924, T1 #423f39, T2 #5b554c, T3 #847464: spec 09's hues at the luminances of the reference's k-means tones inverted through the display chain at E = 1 (Y 0.022 / 0.050 / 0.092 / 0.184, ratio 1 : 2.3 : 4.3 : 8.5). The ratio is locked; the absolute level is the `Level` scalar, fitted once against spec 09's §5.7 targets after spec 17's stage A light solve, and then frozen.

### 4.7 Weaves, knits and braids (heights in metres; all on `UV.Real` or curve UV)
* **`MG.Weave.Plain`** (pitch U, pitch V, crown height): column i = floor(u / pU), row j = floor(v / pV), fu and fv their fractions; the warp is on top where (i + j) is even. Height = warp ? sin(π fu)^0.6 × (0.7 + 0.3 sin(π fv)) : sin(π fv)^0.6 × (0.7 + 0.3 sin(π fu)), × crown height, with ±15 % per-yarn thickness jitter from `White Noise` of i and of j. NYCO: 0.25 × 0.50 mm, crown 0.03 mm.
* **`MG.Weave.Ripstop`** = Plain + grid: gU = `Map Range`(SMOOTHSTEP) |frac(u / G) − 0.5| from [0.42, 0.46] to [0, 1], gV likewise, grid = max(gU, gV) with G = 6.0 mm (the band is the 0.5 mm doubled yarn); height + 0.08 mm × grid; Roughness − 0.05 × grid; a `Noise` (3 mm) warps u and v by ±0.1 mm so no two cells match.
* **`MG.Weave.Basket`** (Cordura): two orthogonal `Wave` BANDS (sine) at the yarn pitch (0.61 / 0.74 mm), Distortion 0.4, multiplied → `Map Range` → crown 0.04 mm; it adds regularity in V2 macros on top of `Fabric063`.
* **`MG.Weave.Herringbone`** (webbing): s = sign(frac(u / P) − 0.5) with P = 2.5 mm across the strap; `Wave` BANDS along the direction (u + s v) at 1.2 mm, Distortion 2, Detail 2 (research F §1 c) → twill lines that reverse every half period; height 0.05 mm; plus the photographed map at 280 mm.
* **`MG.Weave.Grosgrain`**: `Wave` BANDS across the tape, 0.6 mm, sine, 0.05 mm.
* **`MG.Braid`** (laces, shock cord): u = arc length ÷ repeat (0.7 mm laces, 0.5 mm cord), v = curve UV × 3 around; height = max(pingpong(u + v), pingpong(u − v))^1.6 × 0.15 mm; groove darkening × 0.8 (research F §5).
* **`MG.Knit.Stitch`** (procedural fallback for `cotton_jersey` and the sock): `Brick Texture` with brick width = wale, row height = course, offset 0.5, mortar 0.15 × wale; height 0.04 mm.

### 4.8 `MG.Anodise`, `MG.Paint.OrangePeel`, `MG.Tile.AntiRepeat`
* **`MG.Anodise`** (D9): Inputs Dye (linear; black (0.16, 0.16, 0.165) so Dye² × Al F0 ≈ (0.025, 0.025, 0.027); grey 0.44; clear 0.74; gold (0.70, 0.60, 0.43)), Base Roughness, Coat Roughness, Edge, Bare Roughness 0.32. Outputs into the Principled: Base Color = Dye² × (0.91, 0.92, 0.92), Metallic 1, Roughness, Coat Weight 1.0, Coat IOR 1.65, Coat Roughness, and through `MG.Weather.Edge` bare aluminium (Base (0.91, 0.92, 0.92), Coat 0) where the oxide is worn through. Optional thinning: Dye → Dye + (0.30 − Dye) × 0.35 × `Map Range`(`Noise` 35 mm, 0.5–0.8) (research F §6's low-frequency greying).
* **`MG.Paint.OrangePeel`**: `Noise` 3D Object coordinates at 1.0 mm, Detail 1 → height ± 0.006 mm (Bump distance 1, a slope of about 4 %) plus a 5 mm long-wave Noise at ± 0.008 mm. (Spec 12 and research F used "distance 0.2 mm, strength 0.2", roughly a 10 % slope, more than real aerosol paint shows; the library states it physically.)
* **`MG.Tile.AntiRepeat`**: samples an image at Vector ÷ Tile and again rotated 90° and offset by (0.37, 0.61) tile, blending them by `Map Range`(`Noise` at 3 × Tile, 0.3–0.7, SMOOTHSTEP). For normal maps the second sample's tangent XY is rotated by −90° before the blend and the result is renormalised before the `Normal Map` node. No tiled map in the library is sampled any other way.

### 4.9 Decals (`scripts/lib/decal.py`, system Python with PIL and numpy)
One module for specs 12, 14 and 15 (C37): `stencil(text, font, cap_mm, px_per_mm, bridges_mm, erosion, seed) -> RGBA`, `emblem_xstar(plate_mm, strokes, erosion, seed)`, `label_bump(lines, size_px)`, `weather(mask, keep=0.3–0.6, feather_mm, motion_px, ghost)`. Output to `assets/generated/<part>/decal_<name>.png`; the material reads them through `MG.Decal` (a mix by the mask with its own colour, roughness and a step height: emblem white 0.06 mm, stencil paint 0, label bump 0.5 mm for the engraved plate), multiplied by (1 − Chip) so paint lost with a chip takes the stencil with it.

### 4.10 Wear presets (`mat_catalogue.WEAR_PRESETS`; amounts are the inputs of §4.2–§4.5)

| Preset | Dust (Amount, specifics) | Grime | Edge, chips, crest, polish | Used by |
|---|---|---|---|---|
| `armour.top` | 0.55 on bends and upper chamfers, 0.25 elsewhere | slots: Cavity 0.6, Oil 0.3; kneepad lower 20 mm gradient to 30 % | EdgeBevel 1.2 mm; chips `paint.centre` (120 m⁻¹, T 0.48), `paint.frame` (220, 0.71), `paint.rib` (220, 0.65); scratches 1 : 1 : 14 | 12 |
| `panel` | 0.30 on the panel rim | rim band 0.5 (hands and stock) | chips 220 m⁻¹, T 0.60 (about 15–20 % with the edge bias) | 13 admin panel |
| `cordura.top` | 0.35 on flap tops, pad tops, webbing sag crests | pouch bottoms 0–30 mm at 0.8; carrier hem 1054 → 1130 mm | crest 0.6; binding corner wear | 13, 14 frag pouch |
| `cloth.thigh` | 0.40 where Z > 450 mm and up-facing | cuff band 320 → 200 mm, 0.6, Oil 0.2, speckle #3a342c at 10 % | crest 0.7; stress whitening at the gusset 0.45 | 09 |
| `cloth.shoulder` | 0.35 on rib crests and shoulder tops; 0.4 on cuff tops | sweat under straps (`Wear2.B`) | crest 0.6 | 10 shirt |
| `fleece.toproll` | 0.45 × the top roll's upper face | sweat band 15 mm above the carrier | crest 0.5 | 10 gaiter |
| `boot.toe` | zone weights toe 1.0, vamp 0.8, collar top 0.6, bumper top 0.9, quarters 0.15, shaft sides 0.05, laces 0.3; Side L 1.0 / R 0.7 | Band 60 → 20 mm: rand 0.6, sidewall 0.6, midsole 0.3, lower quarters 0.4 | scuff streaks 6 %; polish on counter and lateral quarter; lug-top wear | 02 |
| `glove.crest` | plate crests 0.55, knit 0.25, leather 0.10; Side R 1.0 / L 0.7 | grip zones, Oil 0.6 | polish pulps and pads; TPR scuffs | 11 |
| `belt.kit` | tan plates and flap 0.55, belt top edge 0.35, black polymer 0.20, hardware undersides 0 | object bottoms 0–30 mm, × 0.45 | moulded scuffs (stress-whitened); case none | 14 |
| `metal.hardware` | 0.15 on up-faces | Cavity 0.5 | EdgeBevel 0.8 mm → bare steel; strap-run stroke on bars | 02, 09, 12, 13, 14 |
| `rifle` | warm dust in slots, holes and notches (Cavity-weighted 0.3), up-faces 0.2 | soot at the A2 and port | EdgeBevel 0.8 mm × `touch` (spec 15's anchors); FDE chips `paint.overcoat` (400 m⁻¹, T 0.55 → Tₑ ≈ 0.62, about 25 %, per-patch targets of spec 15 §5.4, × `touch`); polish on spec 15's list; dust Local Up 0.6 | 15 |
| `none` | 0 | 0 | 0 | skin, eyes, hidden parts |

---

## 5. Materials and textures: UVs, texel density, masks, baking and colour management

### 5.1 UV conventions (C38)
| UV map | Scale | Who makes it | What samples it |
|---|---|---|---|
| `UV.Real` | metric: 1.0 = 1 m; islands at real size, never normalised; per-panel seeded offsets so prints break at seams | cloth and strap parts (09, 10, 13, 14, 02 collar and straps, 11 knit) | weaves, knits, camouflage, photographed fabric tiles, dust tiles on cloth |
| `UV.Atlas` | 0–1, islands packed with `bpy.ops.uv.pack_islands` after `average_islands_scale`, margin 8 px at 2K and 16 px at 4K | every part that bakes masks or exports | `Img.Wear`, `Img.Wear2`, decals, every export bake |
| `UV.Head` | spec 06's head unwrap | spec 06 | head maps, `Hair.Masks` |
| `UVMap` | MakeHuman's body map | MPFB | body skin masks |
| curve UV | `u` along the curve, `v` around | laces, cords (02, 09, 14) | `MG.Braid` |

Hard parts without `UV.Real` sample tiled maps by Box projection (Object space, blend 0.2) and smooth noises by Object coordinates. A strip (webbing, binding, elastic) is always unwrapped straight with `u` along it, so herringbone and grosgrain run the right way on every strap.

### 5.2 Texel density
| Content | Target | Reason |
|---|---|---|
| Tiled micro-detail (weave, knit, grain, ripstop, brushing) | resolution-free procedurals or tiles ≥ 13 px/mm (`Fabric063` at 156 mm is 13 px/mm; `Leather032` at 80 mm 26 px/mm; `cotton_jersey` 7.8 px/mm) | V2 resolves 0.088 mm/px; the one exception is `cotton_jersey`, whose 0.69 mm course is still 5 texels |
| Wear masks for renders | 4–8 px/mm on hero parts (armour, carrier front, gloves, rifle, boots), 2–4 px/mm elsewhere | a 2 mm chip edge needs 4 texels or more, and dust gradients far fewer |
| Skin | head 13.6 px/mm (06), body 2.4 px/mm (03, 04), hand ≈ 1.6 px/mm (05) | owners' figures; micro-relief is procedural |
| Export bakes | §5.4 table, 1.2–9 px/mm | the game camera, plus hero turntables of the export |

### 5.3 Mask images (`<Part>.<Side>.Img.Wear` and `.Wear2`; Side `C` when both sides share one atlas)
`Wear`: R dust, G grime, B edge and abrasion, A polish. `Wear2`: R crest, G stress whitening, B sweat or oil, A zone id (8 levels). Both are Non-Color and 16-bit PNG. A part chooses one of three sources per channel: (a) live shader nodes (the default: nothing to bake, follows any geometry change); (b) mesh attributes (`wear_*`, computed in GN or numpy, good for low-frequency zones); (c) a baked image (needed only when a part wants painted zones or a fixed result for EEVEE and Workbench). Images are made by `materials.bake_masks(objects, part, size)`: a temporary Emission material that outputs each channel's mask graph, `bpy.ops.object.bake(type='EMIT', margin=16, margin_type='EXTEND')` into a float image, then packed to RGBA with numpy (0.4 s at 512² measured by research C §10c; 10–30 s at 4K). The export bake (§5.4) always bakes the final look, whatever the source.

### 5.4 Texture baking for the glTF export
**Atlas decision.** One glTF material per atlas, grouped by camera importance and by what moves together, so the game draws 12 materials. A 4K map goes to the hero parts that fill the frame or carry identity; everything else gets 2K. Surface areas are estimates (E); px/mm = √(N² × 0.7 packing ÷ area).

| Atlas | Contents | Size | Area (m²) | px/mm | Alpha |
|---|---|---|---|---|---|
| `Export.Head` | head skin, ears, upper neck (`UV.Head`) | 4096 | 0.15 | 8.8 | — |
| `Export.Eyes` | iris, sclera, caruncle; cornea as a separate primitive | 1024 | — | — | cornea BLEND 0.1 |
| `Export.Hair` | hair cards (spec 07 or 18 decides cards against strands) | 2048 | — | — | MASK 0.5 |
| `Export.Body` | body skin (hidden faces may be deleted on export) | 2048 | 1.9 | 1.2 | — |
| `Export.Garments` | trousers, shirt, gaiter | 4096 | 2.7 | 2.1 | — |
| `Export.Carrier` | carrier, pouches, straps, radio, antenna | 4096 | 1.2 | 3.1 | — |
| `Export.Armour` | pauldrons, forearm guards, elbow caps, kneepads, their straps | 4096 | 0.45 | 5.1 | — |
| `Export.Rifle` | receivers, handguard, stock, barrel and A2 (spec 15's LOD0 sheet) | 4096 | 0.13 | ≈ 9 (spec 15) | — |
| `Export.RifleKit` | magazine, light, optic | 2048 | 0.05 | 7.7 | lens BLEND |
| `Export.Hands` | gloves | 2048 | 0.12 | 4.9 | — |
| `Export.Boots` | boots, laces, socks (hidden) | 2048 | 0.30 | 3.1 | — |
| `Export.Belt` | belt, leg rigs, hip pouches, hard case | 2048 | 0.50 | 2.4 | — |

**Channels per atlas**: `BaseColor` (sRGB, 8-bit; alpha only where the table says), `ORM` (R occlusion, G roughness, B metallic; Non-Color, 8-bit), `Normal` (tangent space, OpenGL +Y as glTF requires, Non-Color, 8-bit; 16-bit for `Export.Head`). Files `export/textures/<Atlas>_<Channel>.png`, embedded by spec 08 §7.6's exporter call.

**Mapping the Principled model onto glTF core** (each recipe's `export` field in the catalogue):

| Library feature | glTF core result |
|---|---|
| dielectric (cloth, polymer, paint, leather, rubber) | BaseColor = albedo, metallic 0, roughness |
| metal | BaseColor = F0, metallic 1, roughness |
| `MG.Anodise` black (hardcoat) | dielectric: BaseColor (0.030, 0.030, 0.032), metallic 0, roughness = mean of base and coat roughness. A dark dielectric shows the oxide's white specular, which core glTF cannot draw over a dark metal |
| `MG.Anodise` grey, clear, gold | metallic 1, BaseColor = Dye² × Al F0, roughness = mean |
| phosphate (metallic 0.3 + oil coat) | metallic 0.3, roughness 0.50 |
| Coat on leather and skin | roughness = mix(roughness, coat roughness, coat weight × 0.5) |
| Sheen ≤ 0.12 | dropped (under 10 %, §2.5) |
| Skin SSS | BaseColor = albedo; the game import may enable Godot's subsurface scattering on `Export.Head` (§10.3 Q6) |
| Transmission | cornea BLEND alpha 0.1 at roughness 0.05; strobe lens opaque #9aa7b3 at 0.30; nails opaque |
| Sub-texel relief | not in the normal map; folded into roughness (step 5) |

**Procedure** (`mat_bake.bake_atlas(atlas, objects, size)`, Cycles CPU here or GPU on Jeff's machine; one Blender process, one bake at a time):
1. Targets are the export meshes of spec 08 §7.6 step 1 (Subdivision level 1 applied per shape key); sources are the render meshes (render-level Subdivision, Displace, cloth relief) as applied copies. Where source and target are the same mesh the bake is direct; elsewhere selected-to-active with cage extrusion 2 mm and maximum ray distance 4 mm.
2. `materials.set_lod(materials, 1)` switches every group to bake mode; `UV.Atlas` is the active render UV.
3. **Base colour**: for each material, the link into the Principled's `Base Color` is re-routed for the duration of the bake into an `Emission` shader (strength 1); metals emit their F0. Then `bpy.ops.object.bake(type='EMIT', margin=16 (4K) or 8 (2K), margin_type='EXTEND')` into an 8-bit sRGB image at 16 samples. Cycles writes scene-linear values encoded to the image's colour space with no view transform: a 0.18 emission stores 118 (§5.6, measured).
4. **Roughness** and **metallic**: the same re-routing of their sockets, baked to float Non-Color images.
5. **Folding**: layers below 2 texels (`lod_min_px`) contribute their slope variance σ² to roughness by r′ = √(r² + 0.5 σ²) (a Toksvig-style approximation [E]); σ² per layer is precomputed in the catalogue from each layer's height and period (σ ≈ 2π × height ÷ period).
6. **Occlusion**: `bake(type='AO')`, 64 samples, distance 50 mm, into ORM.R.
7. **Normal**: `bake(type='NORMAL', normal_space='TANGENT', normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z')` at 8 samples; it includes the shading bump of the layers kept at LOD 1.
8. Pack ORM with numpy in Blender's Python; save with `image.save()` (never `save_render()`, which applies the view transform).
9. Build `Export.<Atlas>.Mat` (one Principled, three image nodes, a `Normal Map` node) and assign it to the export copies; restore every re-routed link and set LOD back to 0.
10. Verify with V6 (§8.3 M7).

**Cost.** One 4K channel at 16 samples is 268 MP·spp, about 2–5 min here at 1–2 MP·spp/s (research C) with these shaders; five 4K atlases × four channels plus seven smaller atlases come to roughly 1.5–2 h on this box and minutes on the GPU machine. Bakes run once per milestone, preferably on the GPU machine; bake images are build artefacts (`assets/build/bake/`, gitignored).

### 5.5 Texture formats and colour spaces
Colour maps (CC0 Color or Diffuse, generated camo previews, decals, BaseColor bakes) are sRGB; normals, roughness, metalness, AO, displacement, opacity, every mask and every EXR are Non-Color. CC0 normals are the OpenGL variants (`NormalGL`, `nor_gl`); the only DirectX map in the project is `cgbookcase_PolishedConcrete01`, whose green is inverted by spec 17. Interpolation Cubic for normals and masks, Linear for colour, Closest never. Generated textures go to `assets/generated/<part>/`, bakes to `assets/build/`, neither committed (CLAUDE.md rule 6); the generators are committed.

### 5.6 Colour management (AgX)
* **Working space**: Blender 4.5's scene-linear Rec.709. A catalogue hex is an sRGB-encoded albedo; `materials.hex_to_linear()` applies the IEC 61966-2-1 decode (c ≤ 0.04045 → c / 12.92, else ((c + 0.055) / 1.055)^2.4) and every Principled colour is set from that; nobody types linear values for a hex by eye.
* **View**: spec 17 §5.6 governs. Hero: `view_transform 'AgX'`, look `'AgX - Medium High Contrast'`, then spec 17's display grade (lift, gain, saturation 0.92, black crush) in `grade.py`. LookDev: `'AgX - Base Contrast'`. Never `'Standard'`, and never "Medium Contrast", which does not exist in 4.5 (research C §8). Material judgements (V1–V3) use LookDev; lit targets (V4) use Hero plus the grade.
* **Read-backs** (swatch albedo, bake checks) are made on scene-linear EXR passes (Diffuse Color, Combined), never on the AgX PNG.
* **Bakes** ignore the view transform. Verified on 4.5.14 with AgX MHC active: an Emission of 0.18 baked into an 8-bit sRGB image stored 0.4627 (PNG 118, the sRGB encoding of 0.18) and into a float Non-Color image 0.1800 (`probe45.py`).
* **Inverse chain**: spec 17's `colour.py` (`display_to_scene`, OCIO plus the inverse grade) is the only converter from reference hexes to scene-linear; §2.2's table was made with the same chain (`inv_display.py`).
* **Game**: the glTF carries sRGB base colours and linear data. Godot's renderer should use its AgX tonemapper (added in Godot 4.4 [VERIFY on 4.7.2]) so that the game's highlight roll-off resembles Blender's base AgX. The hero grade is a look for the loadout screen, not part of the asset.

---

## 6. Fibres, simulation or dynamics
The library simulates nothing. It provides two geometry-node tools and the fibre materials:
* **`MG.GN.Fuzz`** scatters short fibres on a surface: Inputs Density (per mm²), Length mm (min, max), Radius mm, Curl, Lie (0 upright … 1 lying along a direction attribute), Seed, Material. It uses `Distribute Points on Faces` (Poisson), `Instance on Points` of a 3-point curve, `Realize Instances`, `Set Curve Radius`, with `Fibre.*` or the parent fabric's recipe as a Principled Hair (direct colouring) material. Users: the gaiter nap (spec 10 sets density, 1–2 mm length; it carries the rim glow that sheen no longer fakes), the sock fuzz (01, V7 only), hook-and-loop pile (11, optional), webbing selvedge fuzz (closeups only). Hair-rendering cost is about 3× per research C §3, so fuzz is off in `form` and `look` tiers and limited to silhouettes in the hero (`only_silhouette` mask from the facing ratio, 0.2 > |N·V|).
* **`MG.GN.Crest`** (§4.5) runs after cloth simulation and posing (spec 18's order, as spec 17 §6 states it: simulate → bake → attach → render), because crests depend on the final drape; it is also baked to `Wear2.R` for export.
* Hair materials (`Hair.*`) follow spec 07's grooms and melanin calibration; the library supplies only the BSDF settings of §3.3.2 and the direct-colouring rule for dyed fibres.

---

## 7. Attachment: how parts use the library (naming and the Python modules)

### 7.1 Naming conventions (C39)
| Thing | Pattern | Examples |
|---|---|---|
| Catalogue ID (recipe) | `Family.Variant[.Sub]` | `Cordura.500D.OliveBrown`, `Metal.Aluminium.Hardcoat.Black`, `Skin.Head` |
| Material datablock | `<Part>.Mat.<ID>`, dropping a leading word equal to `<Part>` | `Carrier.Mat.Cordura.500D.OliveBrown`, `Boot.Mat.Leather.Boot.FullGrain`, `Body.Mat.Skin.Head`, `Eye.Mat.Cornea` |
| Part prefixes | the object prefixes of the parts | `Body`, `Hair`, `Eye`, `Mouth`, `Sock`, `Boot`, `Trousers`, `Shirt`, `Gaiter`, `Glove`, `Armour`, `Carrier`, `Radio`, `Belt` (spec 14's `BeltRigs` renamed, as spec 17 §10.1 suggests), `Rifle`, `Scene`, `Lib` |
| Node groups | `MG.<Family>.<Name>`, `MG.GN.<Name>` | `MG.Weather.Dust`, `MG.Mask.EdgeBevel`, `MG.GN.Crest` |
| Images | `<Part>.<Side>.Img.<Map>` | `Armour.L.Img.Wear`, `Boot.C.Img.Wear`, `Export.Rifle.Img.ORM` |
| Mesh attributes | lower-case words | `crest`, `stress`, `polish`, `touch`, `soot`, `wear_zone`, `wear_region`, `wear_bottom`, `wear_dust`, `skin_tint`, `panel_id` |
| Object custom properties | lower-case words | `wear_dust_scale` (side factor), `wear_seed`, `tint` (RGB multiplier), `camo_seed` |
| Material custom properties | written by the library | `recipe`, `recipe_hash`, `lib_version`, `overrides` (JSON) |

One material per (part, recipe): left and right objects share it and differ through `wear_dust_scale`, `wear_seed` and their own atlas islands. The Cryptomatte material pass therefore separates parts as well as materials, which spec 17's calibration reports rely on.

### 7.2 Module layout and signatures (`scripts/lib/`; Blender-side modules import `bpy`, the two tools do not)
```python
# materials.py — the only module part scripts import (re-exports the rest)
LIB_VERSION: str                                   # "16.1"; bump on any recipe change
def hex_to_linear(h: str) -> tuple[float, float, float]
def linear_to_hex(rgb: tuple[float, float, float]) -> str
def recipe(id: str) -> "Recipe"                    # catalogue lookup (KeyError lists close matches)
def ensure_groups(names: list[str] | None = None) -> dict[str, bpy.types.NodeTree]
def get(id: str, part: str, **overrides) -> bpy.types.Material          # idempotent create-or-update
def assign(obj: bpy.types.Object, id: str, part: str | None = None,
           faces: list[int] | str | None = None, **overrides) -> bpy.types.Material
                                                   # faces: indices, a boolean face attribute or a vertex group
def set_wear_source(mat: bpy.types.Material, channel: str,
                    source: str, image: bpy.types.Image | None = None,
                    attribute: str | None = None) -> None   # source: 'procedural' | 'attribute' | 'image'
def apply_wear_preset(mat: bpy.types.Material, preset: str | dict) -> None
def set_lod(mats: list[bpy.types.Material], lod: int) -> None
def camo_calibrate(seed: float = 7.0, size_m: float = 2.0, px: int = 2048) -> dict   # cuts, |grad F|, width
def bake_masks(objects: list[bpy.types.Object], part: str, size: int = 2048,
               channels: str = "RGBA", wear2: bool = False) -> dict[str, str]          # paths
def bake_atlas(atlas: str, objects: list[bpy.types.Object], size: int,
               samples: int = 16, use_cage: bool = True) -> dict[str, str]            # §5.4
def swatch(id: str, out_dir: str, views: tuple[str, ...] = ("V1", "V2", "V3"),
           tier: str = "look") -> dict[str, str]                                       # §8.2
def lint(scope: str = "all") -> list["LintIssue"]                                       # §7.5

# mat_catalogue.py — pure data, importable by system Python
CATALOGUE: dict[str, dict]        # ID -> {identity, users, albedo_hex | f0, rough, ior, spec, metal,
                                  #        coat, sheen, sss, maps, uv, layers, wear, export, owner, marks}
CLASS_RULES: dict[str, dict]      # §3.1
TILE_PERIODS: dict[str, dict]     # §3.2 measured periods per asset and axis
WEAR_PRESETS: dict[str, dict]     # §4.10
CAMO: dict                        # §4.6 parameters, cuts, tones, level
ATLASES: dict[str, dict]          # §5.4

# mat_core.py — node-building helpers (no recipes)
class NodeBuilder:                # wraps a node tree; deterministic node names and locations
    def __init__(self, tree: bpy.types.NodeTree): ...
    def node(self, type: str, name: str | None = None, **props) -> bpy.types.Node
    def link(self, out, inp) -> None
    def math(self, op: str, a, b=None) -> bpy.types.NodeSocket
    def mix_rgb(self, fac, a, b, blend: str = "MIX") -> bpy.types.NodeSocket
    def map_range(self, x, a0, a1, b0=0.0, b1=1.0, interp: str = "LINEAR") -> bpy.types.NodeSocket
    def group(self, name: str, **inputs) -> bpy.types.Node
def principled(mat: bpy.types.Material, **values) -> bpy.types.Node   # socket names checked against 4.5
def group_interface(ng: bpy.types.NodeTree, inputs: list[tuple], outputs: list[tuple]) -> None
def tree_hash(tree: bpy.types.NodeTree) -> str

# mat_groups.py — builders of every MG.* group in §4
def build_all() -> None;  def build(name: str) -> bpy.types.NodeTree

# mat_skin.py, mat_fabric.py, mat_hard.py — one builder per recipe family
def build_material(mat: bpy.types.Material, rec: dict, part: str, overrides: dict) -> None

# mat_bake.py
def reroute_for_bake(mat: bpy.types.Material, socket: str) -> "Restore"
def bake_channel(objects, image: bpy.types.Image, kind: str, samples: int, margin: int) -> None
def pack_orm(ao: bpy.types.Image, rough: bpy.types.Image, metal: bpy.types.Image,
             out: str) -> bpy.types.Image
def export_material(atlas: str, images: dict[str, bpy.types.Image]) -> bpy.types.Material

# texmeasure.py (system Python, numpy + PIL)
def tile_periods(path: str, tile_mm: float | None = None) -> dict   # FFT peaks per axis (§3.2)
def blotch_stats(png: str, mm_per_px: float = 2.12, windows: int = 16, seed: int = 3) -> dict  # §4.6
# decal.py (system Python): stencil(), emblem_xstar(), label_bump(), weather() — §4.9
```

### 7.3 How a part uses it
```python
from lib import materials as M
M.ensure_groups()
shell = M.assign(trousers, "NYCO.Ripstop.Camo", part="Trousers", faces="shell")
M.assign(trousers, "NYCO.Stretch.Camo", part="Trousers", faces="stretch")
M.apply_wear_preset(shell, "cloth.thigh")
M.set_wear_source(shell, "crest", "attribute", attribute="crest")   # after MG.GN.Crest
for ob in (strap_l, strap_r):
    M.assign(ob, "Webbing.Nylon.Black", part="Belt")
    ob["wear_dust_scale"] = 1.0 if ob.name.startswith("Belt.L") else 0.7
```
No part script sets a Principled socket, creates a texture node or names a material by hand; if it needs a variant, it adds a catalogue entry (one line, through a spec update).

### 7.4 Idempotency and versioning
`get()` computes the recipe hash (catalogue entry plus overrides plus `LIB_VERSION`) and rebuilds the node tree only when the stored hash differs; otherwise it returns the existing material untouched. Building twice gives byte-identical trees (`tree_hash`), which §8.1 tests. Groups are shared across materials and rebuilt in place, so a group fix reaches every part on its next run. The library never deletes a material or image it did not create (it checks `lib_version`).

### 7.5 Lint (`materials.lint()`; run by every part script after building and by the critique pass)
Errors: L1 a Principled BSDF not built by the library; L2 a dielectric albedo outside its class floor or ceiling (§3.1); L3 sheen above 0.12, or above 0.08 on a dark fabric other than thread, loop pile and fleece (0.10); L4 an image node with the wrong colour space; L5 a missing CC0 file (with the manifest's restore command); L6 a tile scale that disagrees with `TILE_PERIODS` by more than 8 %; L7 Object or Generated coordinates feeding a tiled map on a non-planar mesh; L8 `Pointiness` on a mesh with boolean modifiers or with fewer than one vertex per 5 mm; L9 a camouflage whose parameter hash does not match its stored cuts; L10 a material name that breaks §7.1. Warnings: W1 an F0 not in §3.4's table; W2 a Bump node with Strength ≠ 1 on a procedural height; W3 more than three chained Bump nodes; W4 a part's mask image below §5.2's density.

---

## 8. Evaluation protocol

### 8.1 Unit and lint tests (no render; `scripts/tests/test_materials.py` under Blender's Python, `test_matdata.py` under system Python)
T1 hex → linear → hex is exact for every catalogue hex and 1,000 random ones. T2 the catalogue validates against its schema and §3.1's class rules. T3 every recipe builds twice in a fresh file with an identical `tree_hash`. T4 every `MG.*` group builds and exposes exactly the sockets §4 lists. T5 every Principled socket name used exists in 4.5.14 (the list `probe45.py` printed). T6 the bake-encoding probe: 0.18 → 118 in an sRGB byte image and 0.1800 in a float Non-Color image, with AgX MHC active. T7 `texmeasure.tile_periods()` reproduces §3.2's periods within 2 % from the files. T8 `camo_calibrate()` reproduces the cuts within 0.002. T9 `lint()` reports nothing on the `Lib.Test.*` objects and on every part after its build.

### 8.2 Renders (presets in `p16.json`; one Blender process, one render at a time, `threads 3` while another agent shares the box)
* **V1–V3 boards**, per recipe, `look` tier (V1 800² at 16 spp ≈ 10 s; V2 1024² at 32 spp ≈ 30 s; V3 1200 × 900 at 32 spp with the Bevel and AO nodes ≈ 30 s). Montaged by PIL into `renders/16_materials/sheet_<family>.png` with the catalogue values printed under each tile and, where one exists, the reference crop beside it. The whole catalogue is about 80 min here and a few minutes on the GPU machine; a part re-runs only its own families.
* **`Lib.Test.WearBlock`** (built by `materials.test_objects()`): an 80 × 60 × 40 mm box with 0.8 mm three-segment bevels and a 30 × 10 × 5 mm slot on top, a Ø 30 × 60 mm cylinder, and a 120 × 80 mm cloth sheet with a sine fold of 20 mm radius, at (0, 0, 1000). Its masks are written as Cycles shader AOVs (`dust`, `grime`, `edge`, `chip`, `crest`) for M5.
* **V4 patch tests** after spec 17's stage A: `eval` tier border renders of ±30 px around each anchor (20–40 s each), graded by `grade.py`, compared at the anchor pixel.
* **V5**: `camo_calibrate()` plus a 472² colour bake (≈ 20 s) and `texmeasure.blotch_stats()`; then spec 09's V1 windows in the hero render.
* **V6**: each atlas's owning-part V1 preset at `eval`, once with the procedural materials and once with `Export.*`, with a `roughness` AOV in both.

### 8.3 Metrics (`renders/16_materials/report.json`)

| ID | Metric | Method | Pass |
|---|---|---|---|
| M1 | Albedo read-back | mean of the Diffuse Color pass over the swatch's central 60 % against the catalogue's linear value (dielectrics); for metals a Glossy Color pass against F0 | ±2 % (dielectric), ±5 % (metal) |
| M2 | Class rules | `lint()` | no errors |
| M3 | Sheen invariance | per fabric, swatch brightness with sheen ÷ without, in LookDev and in Hero | the two ratios within 10 % of each other |
| M4 | Micro scale | FFT of V2's luminance, dominant period against §3.2 / §3.4 | ±8 % |
| M5 | Wear placement | AOVs on the wear block: dust coverage on faces with n·Z > 0.7 and on faces with n·Z < 0; edge-band width on a probe line across the 0.8 mm bevel; chip fraction on a centre-preset face | ≥ 60 % and 0 %; 0.5–1.5 mm; 30–40 % |
| M6 | Lit targets | V4 ΔE00 at each §2.2 / §3.3 target pixel | ≤ 6 (fabric, polymer, paint, leather, rubber), ≤ 8 (metal, lens); else reported to the owner with the residual |
| M7 | Bake round trip | V6 per-pixel ΔE00 (graded) and roughness-AOV difference over the part's mask | median ΔE00 ≤ 3, p95 ≤ 8; median \|Δr\| ≤ 0.05 |
| M8 | Camouflage | §4.6 table | sizes inside the reference ranges; fractions ±2 %; flat contrast 60–90 %; hero windows 101–134 % (spec 09) |
| M9 | Reproducibility | the same V1 twice (seed 17) and `tree_hash` twice | byte-identical |

### 8.4 Critic questions (yes or no, view named)
1. V1: does any black material read as a hole, or any dark fabric as pale or frosty on its lit rim?
2. V2: is the Cordura a fine basket of about 0.6 mm yarns (not corduroy, not wood grain), the ripstop a 6 mm lattice on a fine plain weave, the boot leather a 1 mm grain, the webbing a 2.5 mm herringbone, the jersey a 0.7 mm knit?
3. V3: is dust only on top and thicker in sheltered corners; edge wear only on edges and thin; are the paint chips flakes with a lit rim over a dark substrate, and the moulded tan scuffed rather than chipped?
4. V4: on the same material, does his left side read grey-blue and his right warm tan purely by light, as in the reference?
5. V5: is the camouflage the reference's family (soft-edged, dark, four tones, blotches mostly 15–35 mm), never digital, never leopard, with no visible repeat on a leg?
6. V6: at hero distance, can you tell the baked export from the procedural render?
7. Anywhere: is a tile repeat visible within 300 mm?
8. Do the belt webbing, a boot strap and an armour strap look like the same webbing under the same light?

### 8.5 Failure modes and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| Dark fabric pale, or a frosty rim under the cool light | sheen above 0.08, white sheen tint | §3.1 cap; tint = base + 25 % |
| Cordura reads as corduroy or wood grain | `Fabric063` tiled too large, Object coordinates on a curved pouch, wave Distortion ≥ 1.5 | 156 mm tile on `UV.Real`; Distortion 0.3–0.5 |
| Cordura reads smooth plastic | `Fabric063` tiled at 13–17 mm (yarns 0.05 mm) | §3.2 |
| Flakes with no edge | Step 0, or a Bump strength below 1 | Step 0.05 mm, Strength 1 |
| Edge wear smeared across a face | `Pointiness` on a boolean mesh | `MG.Mask.EdgeBevel` (L8) |
| Dust speckled like the weave | the bumped normal fed the Up term | True Normal (§4.2 step 1) |
| Black islands in the camouflage | T0 below the class floor, or `Level` fitted against an unsolved light | locked ratios; refit `Level` after stage A |
| Camouflage looks like granite | Detail too high, Dither too strong | Detail 2 / 1, Dither 0.010 |
| Baked colours brighter or contrastier than the render | `save_render()` applied AgX, or an image tagged with the wrong colour space | `image.save()`; L4 |
| Baked normal map lit from below | DirectX green | `normal_g='POS_Y'` |
| Bump shimmer at hero distance | sub-pixel layers at low sample counts | LOD gating; `eval` tier spp |
| Seams in bakes | margin too small | 16 px at 4K, `EXTEND` |
| Swatch albedo high on glossy materials | specular reaching the camera | spec 17's 45° key; read the Diffuse Color pass |
| A metal renders black | an albedo typed as F0 (spec 09's 0.011) | §3.4 F0 table, W1 |
| Left and right copies differ | two materials, or overrides on one side | one material per part; `wear_dust_scale` |

---

## 9. Build order, effort and risks

| # | Step | Tool | Run time | Authoring | Risk |
|---|---|---|---|---|---|
| 1 | `mat_catalogue.py` from §3 and §4.10; tests T1, T2 | Python | — | 5 h | low |
| 2 | `mat_core.py`: `NodeBuilder`, `principled()`, `tree_hash`; T3, T5 | bpy | 1 s | 4 h | low |
| 3 | `texmeasure.py` (ports `proto16/tile_fft.py`, `camo_stats.py`); `TILE_PERIODS`; T7 | numpy, PIL | 10 s | 2 h | low |
| 4 | Masks and weathering groups: EdgeBevel, Dust, Grime, Edge, Chips, Crest, StressWhite, Polish, OrangePeel, AntiRepeat, Anodise, Decal; T4 | bpy nodes | 2 s | 12 h | medium: many sockets |
| 5 | Weaves, knits, braid | bpy nodes | — | 5 h | low |
| 6 | `MG.Camo.Blotch4` (ports `proto16/camo_nodegroup.py`), `camo_calibrate()`, V5; T8 | bpy, bake | 30 s | 3 h | low (prototyped) |
| 7 | Recipe builders: fabric (≈ 30), hard (≈ 30), skin core, hair settings | bpy | 2 s | 14 h | medium |
| 8 | `MG.GN.Crest`, `MG.GN.Fuzz`, `MG.GN.Touch` | geometry nodes | 1–5 s | 5 h | low |
| 9 | Test objects, `swatch()`, V1–V3 boards (needs spec 17's LookDev) | Cycles | 25–80 min | 5 h | low |
| 10 | `lint()` and T9 | bpy | 1 s | 3 h | low |
| 11 | `bake_masks()`, `bake_atlas()`, export materials, V6 | Cycles bake | 1.5–2 h here | 9 h | medium: cages, folding |
| 12 | V4 patch tests after spec 17 stage A; residual report to owners | Cycles | ≈ 30 min | 3 h | high: depends on the light solve |

Total ≈ 70 h of authoring. Milestones to commit: after 6 (groups and the verified camouflage), after 9 (swatch boards), after 11 (export bakes), after 12 (calibrated). Steps 1–8 and 10 need no other part and can start now; 9 needs spec 17's LookDev; 11 needs the parts' export meshes (spec 08 §7.6); 12 needs the light solve.

Risks: (1) **Albedo before the light solve.** Provisional albedos (§2.2) carry the uncertainty of the zone irradiance, perhaps ±30 %; V4 and the owners' acceptance close it, and spec 17's rule that lights never move to fit a material keeps the solve honest. (2) **The physical bump convention** changes the numbers in specs 01 and 03–06 (they quoted strength-scaled values); until they are updated, W2 flags every mismatch. (3) **Shader cost**: Bevel and AO nodes add 10–20 % in Cycles; the bake removes them for the export. (4) **Bake time on CPU**: about 2 h per full export here; run it on the GPU machine. (5) **Godot drift**: glTF core has no sheen, coat or SSS, and Godot's AgX differs from Blender's; Q6. (6) **[VERIFY] values**: the ripstop interval, metal F0s, black floors, H-148's pigment and the Godot AgX version; each is isolated in one catalogue field, so a correction is one line. (7) **Late arrivals**: spec 15's §5 arrived while this spec was being finished and is reconciled (C36, C42–C48); spec 18 does not exist yet, so the bake and lint hooks of §10.1 are requests to it.

---

## 10. Interfaces and open questions for the client

### 10.1 Edits each spec makes in the critique pass (from §2.4)

| Spec | Edits |
|---|---|
| 01 | `Foot.Skin` → `Body.Mat.Skin.Foot` on `MG.Skin.Core`; sock sheen 0.6 / 0.3 → 0.08 / 0.06; `knitted_fleece` tile 90 → 230 mm; `Foot.Hair` → `Hair.Body`; "scene A" → `LookDev` |
| 02 | names per §7.1; `Leather032` 250 → 80 mm; `Fabric063` on the collar 100 → 156 mm; outsole albedo 0.012 → 0.018; mask packing (scuff → B, grime → G); dust ramp; `UV_Grain` retired; eyelets and buckles → `Metal.Gunmetal` |
| 03, 04, 05 | `Skin.Body` on `MG.Skin.Core`; physical bump heights; skin sheen 0.04; vein tint 18 %; `LookDev`; 04's hero look → spec 17 |
| 06 | `Body.Mat.Skin.Head`; `Head.Masks.G` replaced by `Hair.Masks.R` with albedo × (1 − 0.25 R^0.8); brow and lash values from spec 07; tear film IOR 1.336, enamel 1.62 |
| 07 | add `Hair.Body`; own the stubble-density mask (1 = 55 /cm²) |
| 08 | the game export assigns the `Export.*` materials of §5.4 before `export_scene.gltf` |
| 09 | `MG.Camo.Blotch4` replaces the numpy tile; tones and `Level` (§4.6); sheen 0.35 / 0.2 / 0.5 / 0.3 → 0.06 / 0.06 / 0.06 / 0.10; `Fabric082A` 200 mm; `Fabric061` 64 mm; knee pockets `Cordura.500D.Black`; thread, gunmetal, shock cord, hook-and-loop, piping cover → library IDs; `PocketInside` → `Fabric.BackFace`; `UV.Real`, `UV.Atlas`; mask packing |
| 10 | sheen 0.18 / 0.20 / 0.10 / 0.28 → 0.06 / 0.06 / 0.06 / 0.10, the gaiter fold reached by dust; ripstop 6.35 → 6.0 mm on `MG.Weave.Ripstop` with `Fabric061` (not `denim_fabric_05`); `Gaiter.Mat.Fuzz` → `Fibre.Fleece` (direct colouring); `Thread.Bonded.Black`; mask packing (sweat → `Wear2.B`, crest → `Wear2.R`) |
| 11 | module names (§7.2); `Leather037` 60 → 41 mm; thread → `Thread.Bonded.Black`; mask packing (polish → A, abrasion → B) |
| 12 | sheen on neoprene and elastic → 0.06; elbow cap moulded (no chips); stencil black raised to #2b2927; orange peel stated physically; `decals.py` → `decal.py`; wear masks from `MG.Mask.EdgeBevel` and AO, not `Pointiness` |
| 13 | `Fabric063` 13 / 17 → 156 / 190 mm; Cordura #50473c, 1000D = 0.85 ×; binding → `Binding.Grosgrain.Black`; webbing tile 280 mm; thread colours; stainless split into `Metal.Nickel` and `Metal.Stainless`; label plate on `MG.Anodise`; mask packing (stress → `Wear2.G`) |
| 14 | prefix `BeltRigs` → `Belt`; webbing tile; olive Cordura → `Cordura.500D.OliveBrown`; thread 0.13 → black; coyote webbing #826c51; `BrassAno` → `Metal.Aluminium.Anodised.Gold`; chips from `MG.Mask.EdgeBevel` |
| 15 | material names per C42; hardcoat on `MG.Anodise` (C36) with worn aluminium at F0 0.91 (C43); phosphate as a non-metallic film (C44); its bronze, glass films and black-polymer values adopted (C45–C47); bake through `bake_atlas()` into `Export.Rifle` and `Export.RifleKit`, its `Wear.*` groups replaced by the library's (C48), `Wear.Brass` kept local |
| 17 | provides the swatch stage, the `Hero` lights for V4 and `colour.py`; registers `Scene.Concrete.Polished`; receives V4 residuals for its report |
| 18 | runs `ensure_groups()` first, `lint()` after each part, `bake_atlas()` per §5.4 before the export; keeps `assets/generated/` and `assets/build/` out of git |

### 10.2 What the library needs from the parts
Each part provides `UV.Real` (if it uses tiled cloth or strap detail) and `UV.Atlas`; the attributes its presets read (`crest` from `MG.GN.Crest`, `touch` and `soot` from `MG.GN.Touch`, `stress`, `wear_zone`, `wear_region`, `wear_bottom`, `polish`); the object properties `wear_dust_scale` and `wear_seed`; its spec 17 anchors for the V4 patch tests; and, for the bake, its export meshes and surface area (`measure.py`). In return it gets every material by ID, the masks, the swatch boards and its export atlas.

### 10.3 Questions for the client
1. **Game texture budget.** The plan is 12 glTF materials (five 4K atlases, six 2K, one 1K): roughly 300–450 MB of PNG inside the GLB (a third of that with JPEG base colour and ORM, which glTF allows) and about 440 MB of video memory once Godot compresses it to BPTC with mipmaps. Keep it for the loadout screen and hero turntables, and add a tactical-view export packed into one 4K and one 2K atlas (about 85 MB of video memory)?
2. **Camouflage.** The pattern is our own, generated in the MultiCam Black / A-TACS LE family and matched to the reference's statistics. Confirm, or name a real pattern to emulate (spec 09 asked the same).
3. **Named colourways.** Should the carrier be a named real colour (Ranger Green, Coyote Brown 498)? The library keeps the image's olive-brown either way; a name only fixes the hue if the light solve leaves it ambiguous.
4. **One real measurement.** A phone photograph of black webbing, black Cordura and a black boot beside a white sheet and a grey card, in daylight, would pin the black floors of §3.1, which are the least certain numbers in the catalogue.
5. **Rifle finishes.** Keep Cerakote H-148 Burnt Bronze for the barrel and a brushed FDE enamel for the stripes, or another real finish?
6. **Godot materials.** Enable Godot's subsurface scattering on the head and its AgX tonemapper in the game's environment through an import script, or keep the export strictly glTF core?
7. **Fibre fuzz.** The gaiter nap as curves costs hair-render time (about 3× on the gaiter). Hero renders on the GPU machine only, or never?
