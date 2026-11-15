# Part 02 — Boots (8-inch-class black leather and nylon tactical boots, laced, with ankle strap)

Status: draft 1 (spec writer), 2026-10-06; **revised 2026-10-27** against the reality-wins rule, part 01's scan transfer and the values shared with specs 01, 08, 09, 14 and 16–18 (§0). Owner script: `scripts/parts/02_boots.py` with its private modules in `scripts/parts/p02/` (`last.py`, `sole.py`, `upper.py`, `hardware.py`, `laces.py`, `wear.py`, `scanref.py`, `params.json`; spec 18 §4.3, §10.2; they replace the `scripts/lib/boot_*.py` and `measure_boot.py` first planned here) and its own `measure()`. It uses spec 18's `scripts/lib/` and spec 16's materials library, and builds to spec 18 §4.3's signatures the shared modules it needs that nobody has built yet (`modifiers.py`, `sweep.py`, `uv.py`; spec 09's `gn_stitches.py`; spec 13's `gear_webbing.py`, `gear_hardware.py`; §9.1). Object prefixes `Boot.<L|R>.*` and `Frame.Boot.<L|R>`, collection `Part02.Boots`.

Conventions (from `CLAUDE.md`): millimetres in this spec, metres in Blender; world origin on the floor midway between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT = viewer's right**. Every "left/right" is the soldier's own. This spec uses the **boot frame B** of each boot, identical to spec 01's foot frame F: origin at the pternion of the last (`Foot.L.Last.Pternion`) projected onto the floor, +Z up, toes toward **−Y**, so `h` below is height above the floor and `y` runs from 0 at the heel to about −289 at the last's toe (−297 in the text drafted before §0 item 1). For the LEFT boot the medial side is **−X** and the lateral side is **+X**; the RIGHT boot is `mirror(X)` of the left and is placed by the pose. Every table is written for the left boot in frame B unless a row says otherwise. The shaft azimuth φ is measured from the front (−Y) toward lateral (+X): φ = 0° toe side, 90° lateral, 180° heel.

Sources: `notes/analysis_consolidated.md` §1, §4 (Boots row), §6 weathering, §8 floor and camera; `notes/analysis_gear_inventory.md` §14 and errata 3; `notes/analysis_pose_proportions.md` §5–6; `notes/research_dimensions.md` §1e, §2; `notes/research_assets.md` §3–5; `notes/research_prototypes.md` §4, §5, §8; `notes/research_blender_capabilities.md` recommendations; `spec/01_foot_ankle_sock.md` §4.13 and §10 (the last); `spec/09_combat_trousers.md` §10.1 (what the trousers expect of us). Facts I could not source carry `[VERIFY]` or an **E** (estimated) tag.

## 0. Revision 2026-10-27: reality wins, shared values settled

Drafted before the reality-wins rule (`CLAUDE.md`, Source of truth), before specs 08 and 16–18, and before part 01 transferred the foot's large forms from a real scan, this spec was revised just before part 02 is built, against that rule (the closest real product is a **Lowa Zephyr class boot**) and against what it shares with specs 01, 08, 09, 14, 16, 17 and 18. Where this list and older text disagree, the list wins; the sections it names were edited to match, mostly by dated notes beside the old text. Spec 14 shares nothing with the boots (its rigs end at the thighs). Sources (URLs in §10.4): **S1** a retailer's data for the LOWA Zephyr MK2 GTX HI; **S2**, **S3** two retailers' data for the Zephyr (MK2) GTX MID; **S4** RunRepeat's cut-open lab test of the Zephyr GTX Mid; **S5** a draft Indian standard for tactical boots; **S6** LOWA's size table; **S7** a lace-length chart; **S8** a speed-hook listing.

| # | Change | Why | Specs touched |
|---|---|---|---|
| 1 | **The real boot is a Zephyr MK2 GTX Hi class boot** (was "a Belleville Khyber / C312 body on a Zephyr-style sole"): shaft **210 mm outside, 175 inside** (S1), so the drawn rim (208–212, §2.1) is that boot's and the rim heights 212 / 206 / 218 / 222 stand (the "6.5-inch, not 8-inch" doubt of §2.4 item 6 and §10.3 Q2 close); a DuraPU double-density midsole on a MONOWRAP frame, a rubber outsole, closed hooks, a lace garage, a rear grip loop (S1, S2); mass **≈ 0.63 kg a boot** (a Hi listing in the search results gives 625 g [VERIFY]; S2–S4 560–601 g for the Mid), not 0.9. The foot is 274.3 (spec 01 §0, 2026-10-17) and the last 289.3 (+ 15), so the outsole is **297** (was 305) and every length derived from 297 or 305 follows; LOWA size EU 43.5 / UK 9 (S6). | rule 1; spec 01's shorter big toe and scan transfer (this spec's 2026-10-15 note in §4.1 asked for it) | 02 (§2.4, §3, §4.1–4.3); dated note in 08 (§8.2's boot mass) |
| 2 | **Footbed and sole stack from the real boot**: heel seat **49 → 36**, ball seat **29 → 24** (S4: heel stack 36.3 and forefoot 23.7 with a 3.7 mm insole, drop 12.6; S1–S3: outside less inside shaft height is 35 on both the Hi and the Mid). The pitch is no longer typed: the last turns heel-up about the line through its `.Ball1` and `.Ball5` (oblique, not y −210) until the seats hold, **≈ 4–4.5°** on this last (5.4° before). Lugs **7–8 → 4.5–5** (S4 4.7), outsole base 5 → 2.5 (2.3), insole 3.7, tongue 6 → 12 at the top (S4 14.0). The visible sidewall bands stay the drawing's (the stripe, the rand, 49 to the rand top at the heel): the PU frame and rand rise 7–13 mm above the footbed around the foot, as the MONOWRAP frame does. The boots then lift the figure **≈ 33 mm, not 42** (`CLAUDE.md`'s "the footbeds add 42"; Q13). | rule 1: the drawing cannot show where the footbed lies inside; the lab figures can | 02 (§1.4, §3.1, §3.3, §4.1–4.3, §7.2, §8.3); dated note in 08 (§4.6, §4.7 e); spec 01 §0 item 4 and §7.3 repeat spec 08's values and follow its note; Q13 |
| 3 | **The boot rides `foot.*`.** It is built in frame B on the floor with the seated last inside, then moved by the rigid transform that carries its seated last back onto `Foot.L.Last` at rest (so in the rest pose it sinks and tilts heel-down under the flat foot) and bound there. The hero pose sets `foot.*` so the boot's ground markers (`Boot.L/R.Marker.Ground.*`) lie on z 0 at the headings: the plantar flexion (≈ 4–4.5°) and the ankle height (≈ 113) are readbacks. The forefoot is rigid on `foot.*`: the old weights on `ball.*` cannot work (spec 08 makes `ball.*` non-deforming), and weights on the toe bones would add the hero's 12° toe extension to the toe spring the box already has. | the old §7 left the boot either floating and pitched toe-down in the hero pose or the rest foot through its sole | 02 (§4.14, §7); dated note in 08 (§4.7 e, §7.1); Q18 |
| 4 | **Panels and leather.** The Zephyr Hi's layout: leather overlays (toe box and vamp, heel counter, lace stays, backstrap, keepers) over **Cordura 500D shaft panels** (above the counter and behind the stays, up to the collar) with the padded Cordura collar (S1: 80 % leather, 20 % textile; S5 puts nylon at the ankle and quarter as well). The leather keeps the drawing's **smooth full-grain finish** (broad specular highlights on both toe boxes, lit crease crests; nothing in the drawing reads as nap) at **2.0 mm** (S5: 2.0 ± 0.2), not the Zephyr's 1.4–1.6 mm suede (S3). | rule 1 where the drawing is ambiguous (§2.4 item 7 read polished leather from one cool sample at the counter's edge), rule 2 where it is clear (the finish) | 02 (§2.4, §3.2, §4.4–4.5, §5); spec 16's user lists for `Leather.Boot.FullGrain` and `Cordura.500D.Black` follow (its values stand); Q14, Q15 |
| 5 | **Hero headings 85° right and 17° left** (spec 08 D3, §4.6; were "90° + 15–20° toe-away" and 15°; D3's leftover "+ 15° toe-away" is no number the pose applies). At 85° the right boot's rear silhouette point lies 3° medial of the back, so a buckle at φ 150° hides behind the shaft; it would have to stand at φ ≥ 170°, beside the Achilles, to poke out 4 mm as drawn. **The buckle stays at φ 150°**, off the Achilles where real cuff straps put their hardware, and the drawn box behind the right heel becomes a declared difference. The left boot's lateral silhouette point lies at φ ≈ 70°, so the keepers move from φ ±78° to **±72°** and the lateral keeper and folded tail still stand out there. | spec 08 owns the pose; a drawn detail the real pose cannot show gives way | 02 (§1.4 item 5, §2.4 item 3, §3.4, §4.8, §4.10, §7.3, §10.1); Q16 |
| 6 | **The boot is built on the real last.** Spec 01's `Foot.L.Last` (being built now: 289.3 long, toe spring 12° about the metatarsal heads, collar at z 210, markers `.Pternion`, `.Ball1`, `.Ball5`, `.ToeTip`, `.AnkleAxis.*`) carries scan 038's instep, about 20 mm higher over the midfoot than the stand-in stations assumed (spec 01 §3.1 note: dorsum 75 / 60 at 60 / 70 % L against 56 / 40 estimated), and its square toe line (the hallux 1.9 mm ahead of toe 2). So the throat, the eyelet ladder, the flex line and the shaft are placed from the built upper and the last's markers, not at fixed coordinates: E1 lands at about h 85–95 (drawn 80), and the drawn heights become checks with a declared deviation. The stand-in station table serves pipeline smoke tests only. | spec 01 owns the foot and the last; the foot must fit inside | 02 (§1.4, §4.1, §4.2, §4.4, §4.8); spec 01's V6 (its §8.3 Q12: the last inside the drawn boot) is the first check of the vamp line (§9.4) |
| 7 | **Materials from spec 16's library**, which supersedes §5's values (its C9, C12, C15, C19, C24, C25, C33, C35, C38, C39 and its §10.1 list for 02): `Boot.Mat.<ID>` names; `Leather032` at 80 mm (1.0 mm grain cells; the 0.4–0.8 mm here was a guess); `Fabric063` at 156 mm; outsole albedo 0.018, rand 0.020; `Img.Wear` packed R dust, G grime, B edge and scuff, A polish; one dust ramp (#9a8d85 → #d2c5b5) through the preset `boot.toe`; `UV.Real` and `UV.Atlas` (`UV_Grain` retired); eyelets, hooks and buckle `Metal.Gunmetal`; aglets `Polymer.Black.Smooth`; thread `Thread.Bonded.Black` (Ø 0.35). §5 keeps the regional data the library takes from this part. **None of the boot's recipes is built yet** (§5 note). | one source for material values | 02 (§1.2, §1.4, §3.4, §5) |
| 8 | **Evaluation through spec 17's harness and `p02.json`** (owned here). Every closeup shows one boot and nothing else: the other boot stands 200 mm away in rest, inside V3's and V6's frames, and the rest body's foot stands through the seated boot, so V1–V9 hide the other boot, `Body.Mesh`, `Foot.*` and `Sock.*`. **V8 (lateral three-quarter) and V9 (rear) are added**, whole-boot form views at a natural perspective: part 01's rounds judged large forms in whole views (its V1f, V5f, V8), and no view here showed the lateral side or the heel from behind. The part renders copies, at spec 08's hero transforms for V1–V2 and in frame B on the floor for V3–V9, made after the cache is saved and never cached (as part 01's closeup copies). Critic rounds follow spec 18's protocol (three lenses scoring 1–10; pass at a median of 8 with nothing blocking; metrics first). | spec 17 §4.14 (V7 already hid the other boot); spec 18 §1.4 item 8, D2; spec 01 §0 item 9 | 02 (§1.3, §1.4, §8); `p02.json` (done) |
| 9 | **Against the mechanical look.** The foot's critics found modelled parts crisp and mechanical beside scanned forms, and large forms set by scalar targets wrong where real geometry existed (`notes/critic/foot_shape_r1` … `r3b`, `notes/research_foot_hires.md`). §4.15 sets the rules for the boot (real geometry first; wear, creasing and deformation where the boot flexes and rubs; no even, gridded or symmetric detail; a pair that is not a mirror image) and §3.6 lists licensed scans of comparable boots (CC BY; not downloaded, and Sketchfab needs a login, so Jeff fetches them). Default: the Garmont T8 scan drives the shaft, collar, instep and toe-box sections and the worn Danner TFX scan the crease statistics, as the foot's scans did. | the lessons of part 01's ten critic rounds | 02 (§1.2, §3.5, §3.6, §4.4, §4.11, §4.14, §4.15, §8); Q17 |
| 10 | **Pipeline**: spec 18's part standard (`Part(id="02", …)` of its §4.4, with `prefixes=("Boot.", "Frame.Boot.")`), private modules in `scripts/parts/p02/`, the cache `cache/parts/02_boots.blend` (was `builds/02_boots.blend`), `measure()` returning spec 18's envelope on its `measure.py` primitives. The shared modules the boot needs and nobody has built (`modifiers.py`, `sweep.py`, `uv.py`, `gn_stitches.py`, `gear_webbing.py`, `gear_hardware.py`) are built here to spec 18 §4.3's signatures; the effort is re-estimated (§9.3). | spec 18 §4.3–§4.5, §10.2 | 02 (§4, §8.3, §9) |
| 11 | **The trousers stack on the collars** (spec 09 §2.4: a plain hem, neither tucked nor bloused), so the collar is a friction-30 collider with a rounded rim (§7.4, unchanged). The rim is an ellipse 138 × 106 (385 round), not spec 09's Ø 140 stand-in (440), and the lower hook H1 spans h 185–196, so the cuff edge must stay at h ≥ 192 where it crosses H1 (spec 09 says "speed hooks (h ≤ 185) exposed"). | spec 09 owns the cuff and its stand-in proxy | 02 (§10.1); dated note in 09 (§10.1) |
| 12 | **A pair, not a mirror image**: the right boot is the left's mirror in pattern and hardware only, mirrored about x = 0 so that it stands on the right rest foot (not about its own frame); creases, lace tension and crossings, the tongue's drift, wear and dust take seeds of their own (the drawn left boot is dustier, and no two worn boots match). | spec 01 §8.3 Q1's rule for the feet; §4.15 | 02 (§4.14, §6) |

*2026-10-27, the last's toe room follows reality (spec 01 §0 item 3 and §4.13 notes; Jeff: "Reality").* Item 1's last of 289.3 (the foot's stated 274.3 + 15) left only about 9.7 mm before the standing foot's toe and 7 before the socked one, where real boots leave 15–22. Spec 01 now measures the 15 mm toe allowance from the **standing, socked toe** (`Foot.Contact` loaded, the sock's 0.3 mm gap and 2.2 mm toe ahead of it), so `Foot.L.Last` is **297.1 mm** long (`Foot.R.Last` 297.0), the other allowances (ball +4, instep +2, heel sides +2, heel back 0) and the 12° toe spring unchanged. With this spec's +5 at the toe and +3 at the heel the outsole is about **305 mm** (was 297), as this spec had it before item 1. Every figure here derived from the 289.3 last or the 297 outsole (§2.4 item 9's projection, §1.4 criterion 1's note, §3.1's outsole row and stations, the size EU 43.5 / UK 9) follows when part 02 is built; nothing else in this spec is changed yet.

Questions this revision raised are §10.3 Q13–Q19, each with the default the build follows until Jeff answers; Q1–Q12 carry their status.

---

## 1. Purpose and acceptance

### 1.1 What this part is
Both boots complete: outsole with lugs, midsole, rand and toe bumper; the leather upper (vamp, toe-cap seam, quarters, heel counter, lace stays), the padded nylon collar with its binding and Achilles notch, the gusseted padded tongue with lace keeper, the heel pull loop; all hardware (5 pairs of round gunmetal eyelets, 2 pairs of speed hooks, the 15 mm ankle strap with its buckle and keepers); the round laces with their exact routing, knot and tucked bow; every stitch row; the lining and footbed (built low-poly because they are inside); materials for black full-grain leather, two rubbers, EVA midsole, Cordura, webbing, braided lace, gunmetal and thread; dust, scuff, grime and polish masks; and the armature binding. **Not** in this part: the foot and sock (spec 01), the trouser hems that lie on the collars (spec 09), the floor and lights (eval part); but we provide the collar geometry spec 09 drapes onto (`Boot.L/R.ShaftProxy`, §10).

### 1.2 What "perfect" looks like
At the hero camera the two boots read as heavy, dusty, well-worn black leather boots with chunky two-tone soles: the right one in medial profile with its lace ladder climbing the instep, the strap band across the ankle and a small buckle poking out behind the heel; the left one head-on with seven lace crossings, two pale hooks on each side, a scuffed rubber toe bumper with a raised lip, and a row of dark lug teeth under the toe. The midsole band catches the hangar's cool light as a blue-grey stripe over a black outsole; dust sits only on the toe boxes, vamps and collar tops; the quarters are polished dark and reflect the cool side light. In a 300 mm-wide closeup every element is a real object: a 0.4 mm black thread at 3.4 mm pitch in two rows along every seam, pebbled leather grain of 0.4–0.8 mm with four flex creases across the vamp, eyelet flanges 0.7 mm proud with a worn bright rim, the lace braid at 0.7 mm, a rubber grain on the lugs with grey-worn tops and black sides, 0.4 mm sipes across each lug top, and a bow tucked behind the tongue. Nothing is a painted line; nothing is a smooth sock-like shell.

*2026-10-27 (§0 items 4, 7, 9).* The grain is about 1.0 mm (spec 16 D15), the thread 0.35 mm (`Thread.Bonded.Black`), the shaft above the counter Cordura with a fine 0.6 mm basket; the vamp carries two or three dominant flex folds along the metatarsal-head line with finer wrinkles beside them, not four even creases. The boots are a worn pair that has taken this man's feet: the vamp bulges a little over the first and fifth metatarsal heads, the creases, the lace crossings and the tongue's drift differ between left and right, the edges and lug corners are rounded by wear where they touch the ground and each other, and no row of anything reads as stamped from one template. Next to the real scanned boot of §3.6, in clay, a critic cannot tell which of the two large forms was modelled.

### 1.3 Evaluation render views (rendered by `scripts/parts/02_boots.py --eval`, written to `renders/02_boots/`)
V1–V2 use the hero camera and lights; V3–V7 the neutral look-dev scene A of spec 01 §8.1 plus one pass under the hero lights. Closeup cameras are in frame B of the left boot; for the right boot they are mirrored in X. All 2048² unless stated; Cycles 48 spp OIDN here, 256 spp on the GPU machine.

| View | Camera (mm) | Target (mm) | Lens | Compared with | What it checks |
|---|---|---|---|---|---|
| V1 `ref_right_medial` | hero camera world (0, −4500, 600), rot (93.9°, 0, 0) | — | 46 mm, render border on the box (610,750)–(790,935), crop and ×3 Lanczos | `ref/crop_boots_feet.png` (left half), `ref/zoom_boots_right_x6.png`, `zoom_boots_right_sole_x8.png` | silhouette, collar height, lace ladder, strap band, buckle behind the heel, sole stack, midsole stripe, toe spring, floor reflection smudge |
| V2 `ref_left_frontal` | hero camera | — | 46 mm, border (860,750)–(1010,935) ×3 | `zoom_boots_left_x6.png`, `zoom_boots_left_laces_x10.png`, `zoom_boots_left_bumper_x12.png` | lace crossings count, hooks, toe bumper lip and emboss, toe lug row, dust on the vamp, lateral strap keeper |
| V3 `sole_below` | (0, −150, −700) looking +Z, floor hidden | (0, −150, 0) | 50 mm | §3.3 lug tables (no reference view exists) | lug plan: chevrons, pitch, coverage, heel breast, arch, siping, perimeter teeth, outline stations |
| V4 `lace_close` | (0, −620, 330) | (0, −130, 150) | 85 mm | `zoom_boots_left_laces_x10.png`, `zoom_boots_left_eyelets_x10.png` | routing, over/under at crossings, under-stay dives, hook wraps, knot and tucked bow, eyelet flanges, stay stitch rows, tongue |
| V5 `strap_buckle_close` | (+420, +300, 230) | (+45, −30, 158) | 100 mm | `zoom_boots_right_strap_x12.png`, `zoom_boots_left_strap_x12.png` | strap width, keepers, buckle, tail, the dent the strap makes in the padding, heel counter seam |
| V6 `toe_bumper_close` | (−120, −700, 160) | (−5, −290, 55) | 100 mm | `zoom_boots_left_bumper_x12.png`, `zoom_boots_left_toe_x8.png` | bumper height profile, lip, oval emboss, scuffs, toe-cap seam, dust gradient, rand groove |
| V7 `medial_profile` | (−900, −150, 60) looking +X, elevation 0° | (0, −150, 60) | 85 mm | `zoom_boots_right_sole_x8.png`, `zoom_boots_right_heel_x10.png`, `zoom_boots_right_panels_x8.png` | outsole/midsole/rand stack heights, heel breast, toe spring, lug fringe, panel seams of the quarter and counter |
| V8 `lateral_34` (2026-10-27) | (+620, −620, 300) | (0, −140, 105) | 70 mm | `zoom_boots_left_x6.png` (its lateral half); the reference scan in the same frame (§3.6), if fetched | the whole boot's large forms at a natural perspective: proportions, toe spring, toe-box dome, shaft taper and lean, the lateral quarter's Cordura panel, keeper and folded tail, counter, crease and wear distribution |
| V9 `rear` (2026-10-27) | (0, +800, 140) | (0, −60, 110) | 100 mm | no drawn view; the reference scan (§3.6), if fetched | the heel and shaft from behind: the counter's bell over the heel (not a box), the shaft's taper into the collar, Achilles notch, backstrap, pull loop, buckle at φ 150°, heel-strike wear on the lateral back edge |

*2026-10-27 (§0 item 8).* The views render copies made after the cache is saved, never cached: V1–V2 with both boots placed at spec 08's hero transforms (heading 85° right, 17° left, ankles (−208, +75) and (+208, −75) in plan, outsole ground markers on z 0), V3–V9 with one boot in frame B on the floor, the cameras mirrored in X for the right boot. Every view hides the other boot (V3–V9), `Body.Mesh`, `Foot.*` and `Sock.*`: the boots stand 200 mm apart in rest, so the other one enters V3's and V6's frames, and the bound boots sit under the rest feet (§7.1). V8 and V9 are form views for the large forms, judged in clay (`form`) beside the scan; V1–V7 also run at `eval`. Presets: `scripts/eval/presets/p02.json`; tiers and scenes per spec 17 §4.9 (`LookDev` for V3–V9, `Hero` for V1–V2).

### 1.4 Pass criteria (scored by the critic, each 0–2; the part passes at ≥ 24/30 with no zero)
*2026-10-27 (§0 item 8).* The measurable items (1–3, 5–10, 12–15) are `measure()` metrics and image checks in spec 18's envelope, run before any critic sees the round; the critics score §8.5's questions under spec 18's protocol (three lenses, 1–10, pass at a median of 8 with nothing blocking). The 0–2 tally is retired. Items 3, 5, 6, 7 and 11 changed on this date (dated notes in them).
1. V1: right boot collar top at image y 795 ± 3, sole at y 895 ± 2, toe tip x 631 ± 4, heel back x 767 ± 4; silhouette IoU ≥ 0.90 against the reference boot mask (§8.2). *2026-10-27:* the 297 mm boot at the 85° heading projects ≈ 140 px against the drawn 136, so each end may stand ≈ 2 px beyond the drawn one; the vamp line follows the real instep (§0 item 6), so if spec 01's V6 shows the last above the drawn vamp the IoU is read with the vamp band declared (§9.4).
2. V2: left boot silhouette IoU ≥ 0.88; lug teeth visible along the toe front between y 898 and 910.
3. Hardware count and placement: 5 round eyelets + 2 hooks per side; on the right boot the gunmetal ID mask shows rings at y 857 / 847 / 837 / 827 / 816 and hooks at 806 / 798 (± 3 px). *2026-10-27 (§0 item 6):* the hooks ± 3 px; the eyelets follow the throat on the real last, so E1–E3 are reported against these rows and may stand up to 7 px higher (a declared difference: the scan's instep is higher than the drawn boot's), E4–E5 ± 4 px.
4. Laces: 7 crossings on the left boot in V2, over/under alternation visible in V4, a knot at the top centre, no lace intersecting tongue, stays or hooks (BVH test), no floating lace (every crossing within 1.5 mm of the tongue or the other strand).
5. Strap: band 15 ± 2 mm wide at h 150–165; the buckle protrudes behind the right boot's heel silhouette at (757–762, 814–828) ± 3 px; the lateral keeper and tail protrude beyond the left boot's lateral silhouette at (955–962, 822–834) ± 3 px. *2026-10-27 (§0 item 5):* the buckle stands at φ 150° and does not show behind the right heel at the 85° heading (declared; Q16); the keeper and tail at φ 72° still protrude on the left boot at (955–962, 822–834) ± 3 px.
6. Sole stack measured on the mesh and in V7: heel 48 ± 3 (floor to midsole top), forefoot 24 ± 3, toe spring 15 ± 3 at the tip, heel block 68 ± 4 long. *2026-10-27 (§0 item 2):* footbed seats **36 ± 1.5** at the heel and **24 ± 1.5** under the metatarsal heads (the real boot); visible stack from the floor to the rand top at the heel 49 ± 3 and to the stripe's foot at the ball 23 ± 3 (the drawing); toe spring 15 ± 3; heel block 68 ± 4.
7. Lugs: heights 8.0 ± 0.5 (heel, perimeter), 7.0 ± 0.5 (forefoot chevrons), 4.0 ± 0.5 (arch); chevron row pitch 15 ± 1; plan coverage 55–65 %; perimeter teeth wrap 3 ± 0.5 mm up the sidewall; two sipes per lug top. *2026-10-27 (§0 item 2):* heights **5.0 ± 0.5** (heel, perimeter), **4.5 ± 0.5** (forefoot), **3.0 ± 0.5** (arch), the real sole's 4.7 (S4); the rest stands.
8. Midsole stripe: in V1 the 5 × 5 mean at (700,880) is within ΔE 12 of #333a48 and is cooler than the outsole edge at (720,890) by B − R ≥ +10; the stripe is 7–8 mm tall at the forefoot and 26–30 at the heel.
9. Toe bumper: lip and oval emboss visible in V6; top edge at h 76 ± 4 at the centre front falling to the rand (h 12 above the midsole) by s = 120 mm from the tip; scuffs on the front third only.
10. Dust: (640,870) ≥ #3a352f, (915,870) within ΔE 15 of #6c5943; shaft sides stay ≤ #30302e; dust confined to faces with N·Z > 0.3.
11. Leather: grain resolvable in V4/V6 (cells 0.4–0.8 mm), 4 flex creases across the vamp, 2–3 ankle-break creases per side; the specular highlight on the toe box covers ≤ 25 % of its area (no plastic look); the right quarter reads cool and dark (#101115 ± ΔE 12 at (740,840)). *2026-10-27 (§0 items 4, 7, 9):* cells ≈ 1.0 mm; two or three dominant flex folds with finer wrinkles along the metatarsal-head line, their spacings and depths not equal (coefficient of variation ≥ 0.2) and different between the boots; 2–3 ankle-break folds per side; (740,840) is now the counter's top edge or the Cordura just above it, the target unchanged.
12. Stitching: every seam of §4.9 carries its rows at 3.4 ± 0.3 mm pitch, thread black, rows 1.5 / 5.5 mm from seam edges and 2 / 7 mm from the throat edge on the stays.
13. Collar: roll 22 ± 2 tall × 10 ± 1 thick, rim at h 212 ± 3 at the sides, notch at 206 ± 3, stay tops 218 ± 3, tongue top 222 ± 3; the trouser proxy cuff ring (Ø 146 at h 191) sits on the collar without intersection.
14. Clearance: `Foot.L.Last` lies ≥ 0.5 mm inside the lining everywhere; no vertex below z = −0.2 mm; no intersection between any two `Boot.*` objects except at designed contacts (BVH overlap report).
15. Floor reflection: with the eval floor (roughness 0.30), the smudge under each boot in V1/V2 has median luminance 45–85.

---

## 2. Reference observations

All coordinates are full-image pixels of `ref/reference_full.png` (1672 × 941). Scale at the right boot 4.72 px/cm (2.12 mm/px); the left boot is ≈ 150 mm nearer the camera, so its scale is ≈ 4.88 px/cm (2.05 mm/px). Colours are 5 × 5 means I sampled with PIL (`scratchpad/boot_sample.py`); zooms I made are `ref/zoom_boots_right_soleedge_x8.png`, `zoom_boots_left_soleedge_x8.png`, `zoom_boots_left_strap_x12.png`, `zoom_boots_right_strap_x12.png`, `zoom_boots_right_eyelets_x10.png`, `zoom_boots_left_eyelets_x10.png`, `zoom_boots_both_grid_x3.png`, and the ×3-gain `zoom_boots_right_bright3_x8.png` / `zoom_boots_left_bright3_x8.png`.

### 2.1 Extents (measured)
| Observation | Pixels | Derived | Note |
|---|---|---|---|
| Right boot toe tip / heel back | x 631 (y 862–886) / x 764–767 (y 862–895) | 136 px → 288 mm projected | the outsole is 305 mm; 305 × cos 19° = 288, so the right foot is turned ≈ 15–20° out of the image plane (pose note allows 85–100°); toe pointing slightly away from the camera is adopted (§2.4) |
| Right boot collar top / sole | y 795–800 / 895 | 98 px → **208 mm** | rim set at **h 212** (sides) |
| Left boot collar top / sole | y 798–800 / 907 | 108 px → 221 mm at the near scale | the generator drew the near boot 6 % tall; we keep one height for both |
| Right ankle (malleolus, boot break) | (732, 855) | h 85 | spec 01 puts the talocrural axis at z 80 |
| Lowest visible lace crossing, right boot | (690, 858) | h 78, 56 % of the length from the heel | E1 at h 80, y −168 |
| Right lace ladder | x 690–720, y 805–860 | the medial stay seen obliquely | eyelets at y ≈ 858, 848, 838, 828, 818, 808 + top at ≈ 800 (gear note §14) |
| Left eyelet columns | medial x ≈ 905–908, lateral x ≈ 944–950; y 866, 856, 845, 834, 822, 810, 800 | pitch 11.3 px → 23 mm vertical | 7 positions; the top two are open hooks |
| Left throat gap (tongue visible between stays) | x 912–942 at y 840 | 30 px → 61 mm projected incl. laces | tongue exposure 30 → 44 mm plus stays |
| Right shaft depth (front-back) at y 810 / 830 | 695–758 / 690–756 | 134 / 140 mm | shaft ellipse a = 68–69 |
| Left shaft width at y 810 (no strap) | 897–946 | 49 px → 100 mm | shaft ellipse b = 52–53 |
| Strap band, right medial quarter | x 745–757, y 817–823 (lit 58–72 lum) | **7 px → 15 mm** | confirms the analysts' 15 mm; centre h 158 |
| Buckle protrusion, right boot rear silhouette | x 757–762, y 814–828 | 25 mm tall, 5–6 mm proud | lum 115–163 against a 180–220 floor |
| Protrusion, left boot lateral silhouette | x 955–962, y 822–834 | 22–25 mm tall, 8–10 mm proud | the dark run at x 957 is y 823–833 |
| Heel stack (floor to rand top) right boot | y 872–895 at x 760 | 23 px → **49 mm** | incl. lugs 8 |
| Forefoot stack right boot | y 884–895 at x 680 | 11 px → 23 mm | incl. lugs 7 |
| Sole bottom at the toe vs heel | y 886 vs 895 | 9 px → 19 mm | toe spring plus the toe being ≈ 100 mm further from the camera (floor line rises 6 px); adopted **toe spring 15 mm** |
| Midsole blue band | B − R > 6 at y 880–884 (x 670–700), rising to 865–876 at x 740–760 | 7–8 mm forefoot, ≈ 26 heel | semi-gloss band reflecting the cool light |
| Heel breast (notch in the lug line) | x ≈ 735 | heel block 32 px → **68 mm** | |
| Side lug teeth, right boot | dark teardrops at x ≈ 683, 698, 712, 727, 741, 757 | pitch 14.5 px → 31 mm | heel/waist perimeter blocks 22 long + 8 gap |
| Toe lug teeth, left boot | pale-tipped dashes at x ≈ 905, 912, 918, 925 (y 898–908) | 6–7 px → 13–15 mm | forefoot pitch 15 |
| Toe bumper top edge, left boot | y 871 (x 915–970), lip highlight 2 px | h 74 | lip 2.5 mm, emboss at (950,878) ≈ 12 × 6 mm |
| Left toe-box width at the lug row | 899–977 at y 905 | 78 px → 160 mm projected | 305 long × 118 wide boot at 15° yaw projects ≈ 118 cos 15° + 120 sin 15° ≈ 145 + perspective → consistent |
| Trouser cuff edge over the collar | R y 803–810, L y 803–810 | h 180–195 (R) | our top hook (h 206) is half hidden, the lower hook (189) exposed — as in the picture |

### 2.2 Colour samples (own 5 × 5 means; lit = as rendered)
| Element | Pixel | Hex | Reading |
|---|---|---|---|
| R toe bumper top (dusty) / front / underside | (640,870) / (636,882) / (650,888) | #423c36 / #1a1911 / #050404 | dust on top, black in shadow |
| R vamp dusty top / mid | (660,860) / (690,855) | #3e372e / #2f2c27 | medium dust |
| R leather highlight (flex crest) | (670,850) | #5c4e3d | warm key on dusty crease crests |
| R quarter medial (cool reflection) / shadow | (740,840) / (755,860) | #101115 / #1f1f21 | polished dark leather reflecting the cool side |
| R collar nylon / collar top | (725,805) / (740,798) | #1f1b17 / #121311 | matte |
| R strap webbing / buckle | (750,820) / (757,822) | #393e47 / #3c3937 | webbing picks up the cool light |
| R eyelet 1 / eyelet 2 | (706,816) / (713,826) | #322d28 / #1f1b16 | gunmetal, worn rim |
| R lace lit / dark; tongue | (700,812) / (705,835); (720,815) | #1a1511 / #2b2824; #171412 | |
| R rand / midsole / outsole edge / lug | (700,878) / (700,880) / (720,890) / (700,895) | #272c36 / #333a48 / #202227 / #3d3e41 | the stripe is the bluest element of the boot |
| R heel side / heel rand top | (760,885) / (762,872) | #303436 / #313841 | |
| L toe bumper lit / specular / dark | (915,885) / (955,872) / (935,892) | #5d4b36 / #4a5363 / #2c2722 | warm dust on the medial half, cool specular on the lateral |
| L vamp dusty / vamp | (915,870) / (925,862) | #6c5943 / #4d4132 | heaviest dust of either boot |
| L quarter lateral / medial | (955,840) / (905,830) | #3e444e / #272017 | cool-lit vs warm shadow |
| L collar / collar lateral | (920,805) / (950,805) | #14120d / #2e3439 | |
| L lace / lace 2 / eyelet shadow / hook | (935,850) / (915,840) / (927,812) / (905,818) | #3d3933 / #3e352d / #161616 / #463828 | laces are a faded charcoal, not pure black |
| L strap / buckle-keeper edge | (958,828) / (960,832) | #322f2f / #635a53 | |
| L outsole / lug / medial lug lit / midsole lit edge / sole front | (930,905) / (960,905) / (905,903) / (895,895) / (935,898) | #010101 / #020202 / #3d3227 / #9b8975 / #0a0a08 | the medial sole edge catches the key with dust |
| Floor beside R boot / between feet / R reflection / L reflection | (790,900) / (830,885) / (720,915) / (930,925) | #d8c4b1 / #c9baaa / #343435 / #3b3937 | smudges lum ≈ 52–58 |
| Trouser cuff R / L | (720,800) / (920,800) | #050604 / #2e2a24 | |

### 2.3 Construction cues read from the zooms
* **Right quarter (`zoom_boots_right_panels_x8.png`):** a long lit curved ridge from (720,836) to (760,856) — the heel-counter overlay's top edge; short scalloped ridges at (655–690, 848–868) — the toe-cap seam and flex creases; a lit edge at (690–710, 840–852) — the vamp/stay corner at E1. Three to four horizontal creases cross the vamp between x 650 and 700.
* **Left stays (`zoom_boots_left_eyelets_x10.png`):** the medial stay at x 897–912, y 805–840 reads as a leather tab with two openings (the hooks seen from the front) and a bright dot at (906,818); the lateral column shows bright flange rims at (948,812), (949,822), (947,836), (946,846), (944,858). Between the stays the laces cross with one strand visibly riding over the other; at the top (915–935, 800–808) a small knot-like bulge sits where the bow is tucked.
* **Soles:** the outsole edge is black and matte, the band above it semi-gloss blue-grey, the rand black and matte again; at the toe the rand swells into the bumper. The lug teeth along the edge are rounded and darker than the sidewall; the left boot's toe row shows lug tops lit pale (dust) with black gaps.
* **Bumper (`zoom_boots_left_bumper_x12.png`):** a raised horizontal lip across the front from (912,872) to (968,870) with rounded ends; a small oval mark 12 × 6 mm at (950,878); the surface below the lip is smoother and more specular than the leather above.
* **Collar:** a soft roll about 14 px (30 mm) tall under the cuff with a matte surface; no visible pull loop (hidden by the hem).

### 2.4 Ambiguities and decisions
1. **Eyelet count 7 vs 8.** Both analysts read 7 pairs on the right boot and "7–8" on the left; my column scans find 7 positions on both. **Decision: 7 pairs — 5 round eyelets + 2 speed hooks.**
2. **Which side of the right boot is visible.** The right foot is turned ≈ 90° to his right; a right foot turned outward shows its inside. **Medial.** The errata of the gear note already corrected this.
3. **Buckle side.** The right boot shows a 25 mm-tall box behind the heel; the left boot shows a 22–25 mm protrusion on the lateral silhouette. With the left foot yawed 15° to his left, its lateral silhouette point lies at φ ≈ 75°, and with the right foot turned 90° + 15–20° (toe away from the camera) its rear silhouette point lies at φ ≈ 160–165°. One buckle cannot sit at both places, so the pair is read as a real mirror pair with **the buckle at φ 150° (posterior-lateral)** — it pokes out behind the right heel as seen — **and the strap's lateral keeper with the folded tail at φ 78°**, which is what protrudes on the left boot. If the pose part turns the right toe toward the camera instead, the buckle hides behind the right shaft; flagged in §10.3. *2026-10-27 (§0 item 5):* it does: spec 08 turns the right foot 85° (toe 5° toward the camera) and the left 17°, so the right boot's rear silhouette point lies at φ ≈ 183° and the left boot's lateral one at φ ≈ 70°. The buckle stays at φ 150° (real cuff straps keep their buckles on the outer side, off the Achilles; E, e.g. the buckled cuffs of the French Army's BMJA "Rangers") and hides; the keepers move to φ ±72°. The drawn box behind the right heel is a declared difference (Q16).
4. **Lug pitch 15 vs 31 mm.** The side teeth on the right boot are 31 mm apart, the toe teeth on the left 13–15. **Decision: forefoot chevron rows at 15 mm pitch; heel and waist perimeter blocks 22 mm long at 30 mm pitch.**
5. **The blue midsole band** is not blue pigment: a cool reflection on a semi-gloss dark grey EVA sidewall. **Decision:** midsole base near-black with a slight blue bias and roughness 0.30, so it reflects the cool side light and the lamps the way the floor does.
6. **Height.** Measured 208 (right) to 221 (left, perspective-inflated). **Decision h 212 at the rim sides**, the same for both boots. This is a 6.5-inch shaft above the footbed (163 mm), not a true 8-inch (203) — the analysts' "8-inch class" names the style, not the height. Open question §10.3. *2026-10-27 (§0 item 1):* settled by the real boot: the Zephyr MK2 GTX Hi's shaft is 210 mm outside and 175 inside (S1), so the drawn rim is that boot's; with the real heel seat of 36 the rim stands 176 above the footbed, as its 175.
7. **Quarters: leather or nylon.** The right quarter's cool, mirror-like reflection (#101115) and scuff highlights read as polished leather, not Cordura. **Leather quarters, Cordura only on the collar roll and the tongue gussets.** *2026-10-27 (§0 item 4), reversed:* the sample at (740,840) is h ≈ 116, on the heel counter's top edge (§2.3: its ridge runs (720,836)–(760,856), h 125 → 83), so it says the counter is polished, not what the shaft above it is; the real boot puts Cordura there (S1, S5). The shaft panels above the counter and behind the stays are **Cordura 500D**; the counter, stays, vamp and toe box stay leather (Q15).
8. **Toe bumper emboss.** An oval mark, no legible logo. **Plain embossed oval 12 × 6 × 0.8 mm.**
9. **Right boot length.** 136 px projected is 288 mm, too short for a boot over a 285 mm foot; the foot is 15–20° out of plane. **Outsole 305 mm**, heading handled by the pose part. *2026-10-27 (§0 items 1, 5):* the foot is 274.3 and the last 289.3, so the outsole is **297**; at spec 08's 85° heading it projects ≈ 296 (140 px), 4 px longer than drawn, inside criterion 1's tolerance. The 15–20° out of plane is not needed any more.
10. **Generator inconsistencies we do not copy:** the left boot's lace diagonals have unequal angles and the medial stay looks solid; the two boots differ in apparent height by 6 %; the right boot's lace ladder shows no hook shapes. We build one consistent real lacing on a mirror pair.

---

## 3. Real-world reference

Class: Belleville Khyber / C312-type "8-inch" tactical boot body with a Lowa Zephyr/Salomon Quest 4D-style injected two-density sole and rubber toe bumper (research_dimensions §2). Sizes: foot 285 mm (spec 01, EU 44.5) → last 297 (toe allowance 12), Mondopoint 285–290, EU 45. Tags: **M** measured from the image, **S** sourced (research notes, with the cited page), **E** estimated.

*2026-10-27 (§0 items 1, 2, 4).* **Class: a LOWA Zephyr MK2 GTX Hi TF class boot** (`CLAUDE.md`, rule 1): a 210 mm (outside) lightweight tactical boot with a leather-and-Cordura upper, a DuraPU double-density midsole on a MONOWRAP frame, a rubber outsole, closed hooks, a lace garage and a rear grip loop (S1–S4). It is built to that boot's construction and published dimensions, with the drawing's identity where the drawing is clear: the smooth full-grain finish, the cuff strap and buckle, the rubber toe bumper with its lip, five eyelets and two open hooks, the colours, wear and dust. No brand marks or trade dress (§10.3 Q1, answered). Sizes: foot **274.3** (spec 01, the scan) → last **289.3** (toe allowance 15, spec 01 §0 item 3) → LOWA EU 43.5 / UK 9 (S6: Mondopoint 26.5 at EU 42, 27.7 at EU 44). **S** now also marks the sources S1–S8 of §0 (URLs in §10.4); **D** marks values derived at build time from the last.

### 3.1 Overall and sole stack
| Item | Value (mm) | Tag | Basis |
|---|---|---|---|
| Outsole length (toe bumper tip → heel back) | ~~305 (y −299 … +6)~~ **297** (y −292 … +5; 2026-10-27) | D/M | the last 289.3 + 5 toe + 3 heel; projects ≈ 296 at the 85° heading against the drawn 288 (§2.4 item 9) |
| Outsole width at the ball / waist (y −110) / heel (y −40) | ~~118 / 80 / 84~~ **D** (2026-10-27): the last's insole outline + 3.5 upper + 3 sidewall (§4.2), expected ≈ 116 / 80 / 82 | D/E | scan 038's heel is 67.9 broad (spec 01 §3.1 note), not ANSUR's 71–73; the ball line is the oblique `.Ball1`–`.Ball5`, not y −210 |
| Boot height, floor → collar rim sides / Achilles notch / stay tops / tongue top | **212 / 206 / 218 / 222** | M/S | §2.1; S1: 210 outside, 175 inside (2026-10-27) |
| Heel stack floor → midsole top (incl. lugs 8, outsole base 5, midsole 28) | ~~41, + board 3 + footbed 5 → heel seat 49~~ | — | replaced by the two rows below (2026-10-27, §0 item 2) |
| **Heel seat**: floor → footbed top at the heel seat point (30 mm ahead of the pternion) = lugs 5 + outsole 2.5 + PU midsole 22.3 + lasting board 2.5 + insole 3.7 | **36** | S | S4: heel stack 36.3 with the insole (lugs 4.7, outsole 2.3, insole 3.7); S1–S3: outside less inside shaft height 35 |
| Visible heel stack: floor → rand top at the heel | **49** | M | 23 px at x 760 (§2.1): the PU frame and rand stand 13 above the seat around the heel, as the MONOWRAP frame does |
| Forefoot stack at the ball (lugs 7, base 5, midsole 10) | ~~22, + board 3 + footbed 4 → ball seat 29~~ | — | replaced by the two rows below (2026-10-27) |
| **Ball seat**: floor → footbed top under the metatarsal heads = lugs 4.5 + outsole 2.5 + midsole 10.8 + board 2.5 + insole 3.7 | **24** | S | S4: forefoot stack 23.7 |
| Visible forefoot stack: floor → the stripe's foot at the ball | **23** | M | 11 px at x 680 (§2.1); the stripe and rand above it rise 7–19 above the seat (re-measure the bands at build: §2.1's heel rows disagree, the stripe reaching y 865 at x 740–760 while the rand top is y 872 at x 760) |
| Heel pitch (heel seat − ball seat) | ~~20 → 5.4° over the 210 mm ball-of-foot length~~ **drop 12** (2026-10-27) → the last turns heel-up about its `.Ball1`–`.Ball5` line until the seats hold, ≈ 4–4.5° on this last (D, §4.1 step 2) | S | S4: drop 12.6 (the 20 here was an estimate) |
| Toe spring at the tip (lug tips above the floor) | **15**, starting at the ball line y −210 (2026-10-27: at the `.Ball1`–`.Ball5` line; the last's own 12° raises its tip ≈ 16, consistent) | M | 19 px read incl. depth effect |
| Heel rocker | rearmost 20 mm of the heel bevelled up 3 mm | E | |
| Heel block length (heel breast to heel back) | **68** | M | x 735 → 767 |
| Shaft outer section (a front-back × b side) at h 110 / 158 / 212 | 128 × 100 / 136 × 104 / **138 × 106** | M | §2.1; rim inner opening 118 × 86 |
| Rim circumference (outer, h 212) | **385** (Ramanujan on 69 × 53) | M | spec 09 assumed Ø 140 = 440: see §10.1 |
| Shaft centre | x 0, y −66 at h ≥ 110 (vertical shin, plantigrade ankle) | E | ankle axis at (0, −68, 80) in spec 01 |
| *2026-10-27:* shaft centre | the centroids of the last's own sections at h 110–212 (the scan's ankle and spec 03's leg), expected within 8 mm of (0, −66) | D | §4.1 step 4 |
| Mass (reference only) | ~~≈ 900 g per boot~~ **≈ 630 g per boot** (2026-10-27) | S/E | 625 g for the MK2 GTX Hi in a search result [VERIFY]; S2–S4 560–601 g (the Mid), and a Hi weighs a little more; the Belleville-class 0.9–1.1 kg was the wrong boot |
| *2026-10-27:* internal toe box at the hallux (width × height) | report against the real boot's 73.2 × 27.2 (S4); ours follows the last | S/D | the scan's broad hallux may exceed it; reported, not a target |

### 3.2 Upper components
| Component | Dimensions (mm) | Material / construction | Tag |
|---|---|---|---|
| Vamp | one piece from the toe to the throat (E1 at y −168), down to the vamp/quarter seam: a curve from the stay corners (±26, −168, 80) back and down to the rand at (±56, −120, 22) | full-grain cowhide **2.2** thick, pebbled "pull-up" finish; lined 1.5 | S (leather 1.8–2.2 typical [VERIFY]) |
| *2026-10-27 (§0 items 4, 6)* | the vamp's throat corners and seam curve are placed on the built upper from the throat's lowest point (§4.8), not at these coordinates | **smooth full-grain 2.0** (S5: 2.0 ± 0.2 for tactical uppers; the Zephyr's own suede is 1.4–1.6, S3), the drawing's finish, waxed and worn; lined 1.5 (membrane laminate and mesh) | S |
| Toe-cap seam | across the vamp at y −200 at the centre, swinging back to y −190 at the rand; double row, 4 mm apart | no separate cap: a stitched reinforcing seam over the bumper line | M/E (scalloped ridges §2.3) |
| Quarters (medial, lateral) | from the vamp seam to the back seam, up to the collar; height at the back 212 − 41 = 171 above the midsole | leather 2.2, lined; the upper 90 mm padded 6 mm (ankle padding) | E |
| *2026-10-27 (§0 item 4):* quarters | leather only below the counter's top edge and the stays' back edges; above and behind them **Cordura 500D shaft panels** to the collar, their edges under the leather overlays (leather edges over textile, 2 stitch rows) | Cordura 500D (0.38 mm, spec 16 §3.4) laminated to 1.5 lining, the upper 90 mm over 6 mm foam (ankle padding) | S1 (80 % leather, 20 % textile), S5 |
| Heel counter overlay | rounded trapezoid: base 2 × 60 wide along the rand (y −80 … +6 each side), top 2 × 35 wide at h 100; internal stiffener 1.2 thermoplastic | leather 2.0 over the quarters, double row perimeter stitch | M (ridge §2.3) |
| Back seam and backstrap | centre back vertical seam from the rand to the collar; backstrap tape 10 wide, 2 rows | leather tape 1.5 | E |
| Lace stays (eyelet facings) | strips **22** wide from E1 to the stay top, eyelet centres 11 from the throat edge; throat gap 30 at E1 → 44 at H2 | leather 2.0 doubled over the quarter edge (4.4 total), 2 rows at 2 and 7 from the edge | M/E |
| Padded collar | roll **22 tall × 10 thick** around the rim, Achilles notch 40 wide × 6 deep at φ 180°, scallop rising 6 mm at the stay tops; binding tape 12 wide folded over the rim | Cordura 1000D 0.6 over 8 mm PU foam; binding Type III nylon | E (Belleville "padded collar" S) |
| Tongue | 54 wide at E1 → 68 at the top, top at h 222, 6 thick (2 leather + 3 foam + 1 lining), corners rounded r 10; keeper loop 12 × 25 at h 150 on the centre line | leather face, Cordura gussets (bellows) 1.0 thick from the tongue edges to the stays' inner edges, fully gusseted to H1 | S ("gusseted tongue to top hook", research §2) |
| *2026-10-27:* tongue thickness | **12** over its upper half (above E3), tapering to 5 at E1 (S4: 14.0 at the thickest on the Mid); the keeper loop is the lace garage (S1) | as above | S |
| Heel pull loop | webbing 20 wide × 1.3 thick, 50 showing, folded, bar-tacked 20 × 4 at the back of the rim | nylon webbing | E (hidden by the hem) |
| Lining | 1.5 thick polyester mesh on all inner faces; footbed 5 (heel) → 4 (ball) EVA; lasting board 3 | | E |
| *2026-10-27:* insole and board | removable insole **3.7** (S4; ≈ 90 % PU, 9 % PA, S1), lasting board **2.5** (E) | | S/E |
| Rand | black rubber strip **12 tall × 2.5 thick** on the upper just above the midsole, moulding groove 0.6 wide 2 below its top edge | cemented | M (black band above the stripe) |
| Toe bumper | rubber 3.0 thick; height above the midsole top 34 at the centre front (h 76 at the tip, with toe spring) → 26 at s 40 → 18 at s 80 → 12 (= rand) at s 120 along the outline from the tip; raised lip 2.5 tall × 2 wide along its upper edge; embossed oval 12 × 6 × 0.8 centred 10 below the lip at the front | moulded, satin finish | M |

### 3.3 Sole components and lugs
| Component | Dimensions (mm) | Tag | Basis |
|---|---|---|---|
| Outsole base (carrier for the lugs) | 5 thick, sidewall 6 visible, outline = §4.3 stations | E | |
| Midsole | EVA, 10 at the ball → 28 at the heel, sidewall visible 8 → 26; a 0.5 groove between midsole and outsole and another between midsole and rand | M/E | Vibram 360 Force full sole 9.6 (research §2) for the outsole class |
| Forefoot lugs | chevron (V) pointing toward the toe: two arms 19 × 9 at ±30° from the transverse axis joined at the apex; height **7**; rows at **15** pitch from y −195 to y −290; 2 chevrons per row (medial, lateral) at x = ±28, plus half-chevrons at the outline | S/M | prototype recipe (research_prototypes §8), toe teeth pitch §2.1 |
| Heel lugs | blocks 22 × 14 × **8**, 2 columns (x ±18) × 3 rows at 22 + 8 gap = 30 pitch from y −62 back to +2; the front row's leading face is the heel breast at y −62 (a 10 mm vertical step down from the arch) | M | heel block 68 long |
| Arch (waist) lugs | 4 transverse bars 60 × 8 × **4**, pitch 15, y −80 … −125; raised 3–4 above the ground plane | E | arch cut-out visible as the notch at x 735 |
| Perimeter teeth | blocks 14 long × 10 deep × 8 tall every 15 (forefoot) / 30 (waist, heel) along the outline, outer face flush with the sidewall and extended **3 up the sidewall** (the "tread wraps round" look) | M | teardrop teeth §2.1 |
| Lug geometry details | draft 8° on all lug sides; top edge chamfer 1.5 × 45°; bottom fillet 2.2 / 2 segments where the lug meets the base; sunk 1.5 into the base; **2 sipes per lug top, 0.4 wide × 1.5 deep**, across the arm; 1° random tilt per lug; tops worn grey | S/E | prototype §4 (e) |
| Coverage | 55–65 % of the plan area inside a 6 mm inset outline | S | prototype §4 (a) |
| Lug count | ≈ 24 chevrons (48 arms) + 4 bars + 6 heel blocks + ≈ 34 perimeter teeth ≈ 100 lugs | E | |

*2026-10-27 (§0 item 2), the real sole.* The outsole is a rubber cup **2.5** thick under the midsole (S4: 2.3 without the lugs) whose sidewall wraps up the PU to the stripe's foot (h 23 at the ball); the lugs stand **4.5** (forefoot chevrons), **5.0** (heel blocks, perimeter teeth) and **3.0** (arch bars) (S4: lug depth 4.7), sipes 1.2 deep; the rest of the lug plan (pitches, coverage, draft, chamfers, the heel breast) stands. The midsole is **DuraPU, double density** (S1, S2; spec 16's `EVA.Midsole.BlueGrey` is that PU, named for the class), 10.8 thick under the metatarsal heads and 22.3 at the heel seat; its MONOWRAP frame rises around the foot as the drawn stripe (8 at the ball, ≈ 26 at the heel). The real X-TRAC MILITARY sole has a smooth "rope arch" for fast roping (S1); our arch bars stand in for it (Q3). The lug corners and the heel's lateral back edge are worn (§4.15), never factory-sharp.

### 3.4 Hardware, laces and strap
| Item | Dimensions (mm) | Tag | Basis |
|---|---|---|---|
| Round eyelets (5 pairs) | flange Ø **10.0**, hole Ø 5.5, flange 0.8 thick with a rounded rim r 1.0, barrel Ø 7 through 4.4 leather + 1.5 lining, rolled over a hidden Ø 10 washer; flange 0.7 proud of the stay's outer face | E | "gunmetal eyelets" M; boot eyelet sizes [VERIFY] |
| Speed hooks (2 pairs) | base plate 14 (along the stay) × 16 × 1.2 with r 1.5 corners; hook from Ø 2.5 wire: rises 7 from the plate's throat edge, bends over 180° (outer r 4.5) back toward the stay, opening upward and outward, gap 5; two dome rivets Ø 3 × 0.8 proud at the plate's outer corners | E | "closed hooks" Lowa (research §2) |
| Laces | round braided polyester, Ø **4.0** (flattens to 3.2 × 4.6 at eyelets and hooks), length **1500** (59 in), aglets 20 long × Ø 4.5; braid diamond 0.7 along the lace | S/E | Ø 4 mil-spec (research §2); 7 pairs → 1500 (research gives 1600–1830 for 8–10 pairs) |
| Lace colour | lit #4a473f / #41362d, albedo sRGB **#333129** (linear 0.030, 0.028, 0.024) | M | task colour #4a473f is the lit value |
| Ankle strap | webbing **15 wide × 1.5 thick**, one turn around the shaft at h 150–165 (centre 158), 1 mm proud of the quarters, denting the ankle padding 1 mm; free tail 35 beyond the buckle, end folded 10 and bar-tacked | M | 7 px band §2.1 |
| Buckle | gunmetal ladder-lock: frame 18 (along the strap) × 24 (tall) × 7 proud, bar 3 thick, 1.5 mm radius edges; at φ **150°**, h 158 | M/E | 25 mm box behind the right heel |
| Strap keepers (2) | leather loops 18 wide × 12 tall × 2 thick standing 5 off the quarter, box-stitched; at φ 78° (lateral, with the folded tail passing through, 8 proud in all) and φ −78° (medial) | M/E | left lateral protrusion 8–10 |
| Thread | bonded nylon Tex 90, Ø **0.40**, black (#0e0d0c lit), pitch **3.4** (7.5 spi); bar-tacks 1.3 pitch zigzag; collar binding 1 straight row 2 below the rim + 1 zigzag 2 wide | S | prototype §8 stitch recipe; 7–8 spi typical [VERIFY] |

*2026-10-27.* **Laces:** 1500 stands (S7: 140–160 cm for boots with 7–8 pairs; the hooks lengthen the path). **Hooks:** riveted speed hooks are about a 10 mm cap on a 6 mm post with a 3 mm opening for 3 mm laces (S8); ours are plate-mounted like LOWA's (S1) and open 5 for the 4 mm lace, so the table stands. **Thread:** `Thread.Bonded.Black`, Tex 70, Ø **0.35** sunk 0.15 (spec 16 C15), pitch 3.4 kept (E). **Buckle** at φ 150° (§0 item 5); **keepers** at φ **±72°** (were ±78°). The real Zephyr has no ankle strap: the strap, buckle and keepers are the drawing's identity (rule 2), built as a real cuff strap would be.

### 3.5 How these boots wear (what the masks reproduce)
Dust settles on the toe boxes, vamp tops and the collar roll (pale warm film, lit highlights #a19689–#a6998e, heaviest on the forward left boot); the toe bumper fronts scuff pale grey in short streaks along the boot axis; the quarters and heel counters polish to a dark semi-gloss from trouser rub and brushing, with cool reflections; the rand and midsole pick up floor grime (brown-grey speckle) low down, yet the midsole stripe stays clean enough to reflect; the lug tops wear grey and smooth while the lug sides stay black; eyelet flanges and hook lips brighten to bare steel on their rims; the laces fade to charcoal and fuzz slightly, darker where they pass through eyelets; leather creases whiten faintly on their crests (the #5c4e3d highlight).

*2026-10-27 (§0 items 9, 12), how a worn boot deforms, which the masks alone cannot give.* The vamp folds where the foot bends, along the metatarsal-head line, two or three deep folds and a field of fine ones, the lateral end usually deeper; the toe box ahead of them stays domed (a thermoplastic toe puff) but sinks a little behind the bumper's lip; the upper bulges over the first and fifth metatarsal heads and the instep, having taken the foot's shape; the shaft front folds at the ankle break in two or three curved folds, the Cordura in softer, wider wrinkles; the collar slumps and creases at the back over the Achilles; the counter keeps its bell; the heel wears on its lateral back edge (heel strike), the lugs round over and the forefoot's lugs wear lower under the ball; leather edges and the bumper's lip scuff where the boot meets the ground and the other boot (the medial ball and toe sides), not evenly; dust lies in the creases' valleys and along the welt and seams as well as on up-faces, and wears off the crests; lace crossings sit a few mm off centre, the tongue drifts lateral, the strands twist and flatten. Each of these differs between the left boot and the right.

### 3.6 Reference geometry: licensed scans of comparable boots (2026-10-27; candidates, nothing downloaded)

The foot's large forms only came right when a real scan drove them (spec 01 §0, 2026-10-16 and 10-17); the boot has the same risk in its shaft, collar, instep and toe box, and its creases. Scans of comparable boots exist under CC BY 4.0 (Sketchfab's "CC Attribution": credit the author with the title, link and licence; commercial use and derivatives allowed). Sizes are the archives Sketchfab lists (`api.sketchfab.com/v3/models/<uid>`, read 2026-10-27). Sketchfab downloads need a logged-in account, so Jeff fetches them by hand into the git-ignored `assets/scans/boots/<uid>/`, and their sha256 and credits go into `assets/manifest.json` and `deliver/` as the foot scans' did.

| # | Scan (author) | Model page | Licence | Size | What it is | Use here |
|---|---|---|---|---|---|---|
| R1 | Garmont T8 Tactical Boot Scan (xyzworkshopAU, 2024) | https://sketchfab.com/models/215e852679b24b06ab129a58e4e982ab | CC BY | 433,524 faces, no textures; glTF 8.1 MB, source 69.1 MB | an 8-inch suede-and-Cordura tactical boot on a rubber sole, the Zephyr Hi's closest rival; scale, wear and laces not stated | **primary form reference**: shaft sections h 60–210, collar profile, instep line, toe-box plan and dome, counter bell, outsole sidewall |
| R2 | "Boot!" (ReferenceLibrary, 2016) | https://sketchfab.com/models/7b2edc8d8a4d404bbe6ec15ced8e71fb | CC BY | 508,454 faces, 4K texture; glTF 22.7 MB, source 27.8 MB | a Danner TFX tactical boot worn for two years, EinScan Pro quick scan; one boot; units not stated | **crease and wear reference**: vamp folds along the flex line, ankle-break folds, collar slump, toe sag, worn edges (positions, spacings, depths, profiles) |
| R3 | Magnum Elite Spider 8.0 boots Photogrammetry (Nick G. Gizelis, 2017) | https://sketchfab.com/models/7193384f38024ffd839f0198d9c9d705 | CC BY | 249,838 faces, 4K maps; glb 38.1 MB, glTF 30.7 MB, source 13.6 MB | an 8-inch black leather-and-nylon tactical boot; Photoscan trial, remeshed in ZBrush, maps baked | second form check in black leather and nylon; its remesh softens detail, so forms only |
| R4 | Old Lowa Gore-Tex Boot (inciprocal, 2021) | https://sketchfab.com/models/417531d1bfcd4fc39f9cedbc1c85963e | CC BY | 19,900 faces + 2K PBR maps (lossless JPEG, 245 µm a texel); glTF 17.8 MB, source 36.3 MB | a worn LOWA Tibet GTX, all smooth leather, Vibram sole; OBJ in metres, 299 × 111 × 219 mm, one boot | **scale and leather reference**: a real LOWA last at known size, close to ours (297 × ≈ 116 × 212); smooth-leather creases and grain in its maps |
| R5 | Vietnam Army Jungle Boot (Colin.Greenall) | https://sketchfab.com/models/181859d1476a4e1f8d688499dbd06f66 | CC BY | 185,522 faces, 4K; glTF 13.9 MB, source 13.3 MB | a worn, laced pair of US jungle boots (canvas shaft) | secondary: how a worn pair differs left to right; lace sag and crossings |

Not used: "Military Boots" (hefferanr.uni, CC BY-NC-SA: non-commercial), "Palladium leather boots scan" (Sketchfab Free Standard), "Military Boot low poly" (Gulgolet, 616 faces), and the paid scanned combat boots on RenderHub; searches of Poly Haven and of the Smithsonian's CC0 3D highlights found no comparable boot (a full search of 3d.si.edu with the CC0 filter is still to do).

**How they would be used (default, Q17).** As section references, as part 01 used its scans before the transfer: each scan aligned in frame B (heel back at y 0, sole plane on z 0, toe on −Y), scaled uniformly to our outsole length (297), read in the same sections as our boot (the shaft at h 60–210 every 15 mm, the collar, the instep line, the toe box's plan and height at 5 stations ahead of the metatarsal heads, the counter's coronal sections), and our upper's large forms fitted to them where they disagree, under the hard rule that the shell stays ≥ 3.5 mm outside the last (the foot must fit; the scan's foot was another man's). R2's folds are measured, not copied: their positions relative to its flex line, count, spacing, depth and profile become the statistics of `Boot.GN.Creases` (§4.4 step 5). A direct surface transfer (part 01's 2026-10-17 method) is the follow-up only if the fitted forms still read wrong, because panels, seams and hardware must then be laid on the transferred shell. In the critic packets the scan, in the same clay and camera, is the left half of the V7–V9 pairs (spec 18's `--ref`), as the foot's scan was.

---

## 4. Geometry construction plan

All steps run headless from `scripts/parts/02_boots.py`; every object is created with `bmesh`/`bpy` under `temp_override` and named `Boot.L.<Component>`; the right boot is produced at the end by mirroring the whole `Boot.L.*` set (§4.14). Numbers are mm in this text and metres in the code (`MM = 0.001`). Orientation: frame B, built at the rest-pose position of the left foot (translation only, from `Foot.L.Last.Pternion`). *2026-10-27:* the stages are spec 18 §4.4's (`last`, `sole`, `lugs`, `upper`, `overlays`, `collar`, `hardware`, `strap`, `laces`, `stitches`, `materials`, `masks`, `mirror`, `weights`, `proxy`), each resumable from the cache; after `mirror`, the `weights` stage moves both boots under the rest feet and binds them (§7.1), and the render copies of §1.3 are made from the frame-B state. Every number below that §0 replaced carries a dated note; §4.15 governs how all detail is laid out.

### 4.1 Step 1 — the last and its conditioning (`boot_last.py`)
1. Load `Foot.L.Last` (spec 01 §4.13: socked foot + allowances, toe box +12, ball +4, instep +2, heel sides +1, toe spring 12° about the MT line, vertex groups `last_heel/ball/toe/instep/collar`, markers `.Pternion`, `.Ball1`, `.Ball5`, `.ToeTip`, `.AnkleAxis.Medial/Lateral`). If absent, build the **stand-in last** by lofting the station table below (`bmesh.ops.create_circle` rings swept along y, 32 verts per ring, `bridge_loops`) and tag every render "STAND-IN".
2. **Heel pitch:** rotate the last about the ball line (axis X through (0, −210, 0)) by +5.4° so the heel seat rises 20 mm, then translate +Z so the ball seat sits at h 29 and the heel seat at h 49. Record the transformed markers as empties `Boot.L.Marker.*`. *2026-10-27 (§0 item 2), replaced:* **seat the last on the real footbed**: turn it heel-up about the line through its `.Ball1` and `.Ball5` (both on its insole plane; the line is oblique, medial forward) until its insole plane stands 12 mm higher at the heel seat point (30 mm ahead of `.Pternion`) than on that line, then lift it until the line sits at h 24 and the heel seat point at h 36. The angle is read back and reported (≈ 4–4.5° on this last). Record `Boot.L.Marker.Pternion`, `.Ball1`, `.Ball5`, `.ToeTip` (the seated last's), and the outsole's ground markers `Boot.L.Marker.Ground.Heel`, `.Ground.Ball1`, `.Ground.Ball5` (on z 0 under those points), which the hero pose puts on the floor (§7.1).
3. Remesh for a clean shell: `Remesh` modifier `VOXEL`, `voxel_size 0.004`, `use_smooth_shade`, apply → ≈ 6 k quads/tris; `Smooth` modifier factor 1.0, 4 iterations, apply. Store as hidden `Boot.L.LastShell`.
4. Extend the shaft: the last ends at its collar ring (z 210 in the foot frame → h ≈ 230 after the pitch... clipped): delete everything above h 222 and above h 110 replace the leg by the **shaft ellipse loft** of §3.1 (rings every 10 mm from h 110 to h 222, 48 verts, centre (0, −66), semi-axes interpolated 64/50 → 69/53, minus the shell allowance 3.7 so the loft is the INNER surface), bridged to the last's ring at h 110 with `bmesh.ops.bridge_loops`. This is `Boot.L.Inner`: the lining surface. *2026-10-27 (§0 items 6, 9):* the seated last's collar (z 210) stands at h ≈ 245, so the cut at h 222 lies inside it; the rings' centres follow the last's own section centroids at each height, the shell allowance is 3.5 (2.0 leather + 1.5 lining), and each ring must clear the last by ≥ 4 mm at every azimuth (the padding's room; where the ellipse does not, it grows there). With R1 in (§3.6) the rings take R1's section shapes, scaled to the drawn rim's 138 × 106 at h 212, instead of ellipses.

Stand-in last stations (y, medial half-width −x, lateral half-width +x, dorsum height above the insole):
| y | −x | +x | z top | | y | −x | +x | z top |
|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 60 (heel back, rounded r 30) | | −170 | 50 | 55 | 52 |
| −20 | 34 | 36 | 75 | | −210 | 56 | 54 | 42 (ball) |
| −50 | 37 | 40 | 88 (ankle front at −80: 95) | | −240 | 56 | 49 | 34 |
| −90 | 36 | 40 | 72 | | −270 | 50 | 40 | 28 |
| −130 | 40 | 46 | 62 | | −297 | 12 | 10 | 18 (tip, centred x −6) |

*2026-10-15, the last's length follows the foot (to revisit when part 02 is built; nothing else here is changed yet).* Jeff shortened the big toe ("I think toe 2 looks right; it is the big toe that is too long"; spec 01 §0, §3.1, §3.3 notes of this date), so the foot is about 275 mm to its longest toe, not 282. The toe allowance stays 15 mm (spec 01 §0 item 3), so `Foot.L.Last` will come out about 289–291 long instead of 297: this table's −297 tip, the outsole's 305 (§3.1) and every length here derived from 297 follow the last spec 01 builds, and are re-derived when this part is built.

*2026-10-27, revisited (§0 items 1, 6).* The foot is 274.3 (scan 038, transferred) and the last 289.3; the outsole is 297 (§3.1). This station table described a generic 297 mm last with a low instep and a pointed toe; the real last's instep stands about 20 mm higher over the midfoot and its toe line is square. It is kept only for pipeline smoke tests when part 01's cache is absent (`--proxy 01`, renders tagged STAND-IN, never sent to critics, scaled in y by 289.3 / 297); every form judgement waits for the real last. Step 1's `Foot.L.Last` is part 01's `scripts/parts/p01/last.py` (being built now): membrane-smoothed socked foot, insole plane flat from the heel seat to the toe, toe box stretched 15 mm, toe spring 12° about the metatarsal heads' line, collar ring at z 210, markers as listed.

### 4.2 Step 2 — sole outline and lofts (`boot_sole.py`)
1. **Plantar outline** = the last's insole outline (section of `Boot.L.Inner` at z = seat height, 48 points) offset outward by 3.7 (upper) + 3 (sidewall) at the sides, 5 at the toe, 3 at the heel, resampled to 96 points with 12 points on each arc (prototype §4 (c)). Fallback stations (ground-contact outline, lug tips):

| y | −x | +x | | y | −x | +x |
|---|---|---|---|---|---|---|
| +6 | 0 | 0 (centre of the heel arc, r 42) | | −185 | 52 | 58 (5th MT head) |
| 0 | 28 | 28 | | −210 | 60 | 57 |
| −20 | 38 | 40 | | −240 | 60 | 52 |
| −40 | 40 | 44 | | −265 | 54 | 44 |
| −70 | 38 | 43 | | −285 | 40 | 30 |
| −110 | 36 | 44 | | −299 | 8 | 4 (tip, centred x −6) |
| −150 | 42 | 50 | | | | |

2. **Three lofts**, each 4 rings (bottom inset 1.5, top inset 0.5 mm) bridged, closed with `bmesh.ops.contextual_create`, bisected every 14 mm along y (`bisect_plane`) so the profile can bend: `Boot.L.Sole.Outsole` (bottom z = lug height: 8 heel, 7 forefoot, 4 arch → top +5), `Boot.L.Sole.Midsole` (top at the board plane: 22 at the ball → 41 at the heel; the top surface is the lasting board, planar in the heel and sloping linearly to the ball), `Boot.L.Sole.Board` (3 thick, hidden). Per-vertex profile: `z += toe_spring(y) = 15·smoothstep(0, 1, (−210 − y)/89)` for y < −210; heel rocker `z += 3·smoothstep(0,1,(y + 14)/20)` for y > −14.
3. Bevel 2.5 mm / 3 segments / 40° on the outsole and midsole shells; `Subdivision` 1 (render 2); the 0.5 mm grooves between layers come from the insets (the layers do not touch: 0.5 mm gaps).
4. **Heel breast:** at y −62 the outsole bottom steps from the arch level (z 4) down to the heel level (z 8 lug bottoms) over a 10 mm vertical face; realised by giving the outsole loft two extra rings at y −62 ± 0.5 with different bottom z.
5. UVs: `Smart UV Project` on each shell; the sidewall band also gets `UV_Side` by cylindrical projection along the outline for the rubber grain stripes.

*2026-10-27 (§0 items 1, 2, 7).* The upper's offset is 3.5 (not 3.7); the fallback stations were for the 305 mm outsole (scale y by 297 / 305 if ever used). The layers: `Outsole` bottoms at the lug heights 5 (heel), 4.5 (forefoot), 3 (arch), its base 2.5 thick and its sidewall wrapping the midsole to the stripe's foot; `Midsole` top (the board plane) at 17.8 under the metatarsal heads → 29.8 at the heel seat, its sidewall rising as the MONOWRAP frame to the drawn stripe's top; `Board` 2.5; the insole 3.7 is `Boot.L.Footbed` (§4.7). Toe spring starts at the `.Ball1`–`.Ball5` line, not at y −210, and the heel breast and rocker follow the last's heel. UV maps per spec 16 §5.2: `UV.Real` on the sidewalls (rubber grain at real scale), Box projection on the hard parts; `UV_Side` and `UV_Grain` are retired.

### 4.3 Step 3 — lugs (`boot_sole.py: place_lugs`)
1. One **grooved box primitive** per lug type is built once with bmesh: box L × W × H, top face subdivided 1 × 5 along L, the 2nd and 4th strips pushed down 1.5 mm (the sipes, 0.4 wide: strips are made 0.4 by `bmesh.ops.subdivide_edges` with `edge_percents`), side faces drafted 8° (`bmesh.ops.scale` of the top loop 0.86), top edges bevelled 1.5 (`bmesh.ops.bevel` on the top loop, 2 segments), bottom extended 1.5 below z 0 (sunk).
2. Chevrons: two arm boxes 19 × 9 × 7 rotated ±30°, merged with `bmesh.ops.remove_doubles` at the apex; the apex points to −Y. Heel blocks 22 × 14 × 8; arch bars 60 × 8 × 4; perimeter teeth 14 × 10 × 8 with the outer face extruded 3 mm up the sidewall (`extrude_face_region` + translate +Z, then shrinkwrapped to the sidewall by `Shrinkwrap NEAREST_SURFACEPOINT` with offset 0).
3. **Placement grid** (plan coordinates): forefoot rows y = −195 − 15k, k = 0…6, chevron centres at x = ±28 (clipped by point-in-polygon against the outline inset 6 mm; a half-chevron is kept if ≥ 55 % of its footprint is inside); arch bars at y −80, −95, −110, −125 centred x +4; heel blocks at x ±18, y −56, −26, +4 (clipped to the heel arc); perimeter teeth at arc-length stations along the outline inset 5 mm, pitch 15 for s within the forefoot (y < −150), 30 elsewhere, oriented tangent to the outline. Each lug is tilted to the local base slope (sampled normal of the outsole bottom) and rotated by a seeded random ±1°.
4. Merge all lugs into `Boot.L.Sole.Lugs` (one mesh, no boolean — they are sunk 1.5 into the base, prototype §4); shade smooth with auto-smooth 40° via `Smooth by Angle` modifier. Assert plan coverage 55–65 % (rasterise lug tops vs the inset outline in numpy) and lug tip heights (ray-cast the tips: within ±0.3 of the design height).
5. Poly cost: ≈ 100 lugs × 90 faces ≈ 9 k faces per boot.

*2026-10-27 (§0 items 2, 9).* Lug heights 4.5 (chevrons), 5 (heel blocks, perimeter teeth), 3 (arch bars), sipes 1.2 deep (§3.3 note). The moulded pattern is regular, as a real mould is; what is not regular is wear (§4.15): each lug's top edge rounds by a wear depth drawn from a field (heaviest on the heel's lateral back quarter and under the ball, light in the arch, 0.3–1.5 mm), a few corners are chipped (seeded, ≤ 3 % of lugs), and small stones and packed dust sit in a few grooves (V3). The ±1° tilt jitter stays; the coverage and height asserts read the unworn design heights.

### 4.4 Step 4 — the upper shell and the throat (`boot_upper.py`)
1. `Boot.L.Upper` = duplicate of `Boot.L.Inner`; delete the plantar faces (below the board plane) and the faces inside the throat region (step 3); add thickness per region with `Displace` along normals using vertex-group `shell_offset` weights: vamp and quarters **3.7** (2.2 leather + 1.5 lining), ankle-padding band h 120–200 at φ 60–300° **9.7**, collar band h 200–222 **12** (the roll is a separate object, this is its base), so the outer surface equals the last plus the real build-up. Apply. *2026-10-27 (§0 item 4):* vamp, counter zone and stays 3.5 (2.0 leather + 1.5 lining); the Cordura shaft panels 1.9 (0.4 Cordura + 1.5 lining), 7.9 over the ankle padding; Step 3's Solidify is 2.0 on leather and 0.4 on the Cordura faces (a vertex-group factor).
2. **Throat opening:** remove faces whose centre satisfies |x| < w(h) and lies on the front (φ within ±40°) for h between 80 and 222, with w(h) = 15 + 7·(h − 80)/126 (the tongue exposure half-width). Edge clean-up: `bmesh.ops.dissolve_degenerate`, then the boundary loop is smoothed (`smooth_vert` on boundary verts, 3 iterations) and projected back onto the displaced shell so the throat edge is a fair curve from E1 (y −168, h 80) to the stay tops (h 218).
3. `Solidify` thickness 2.2, **offset −1** (the face normals point outward; the leather grows inward, prototype §0 warning), `use_rim`, `use_even_offset`; the rim at the throat is the quarter's cut edge under the stays (hidden by them except at the top).
4. `Bevel` 0.8 / 2 segments on the rim edges; `Subdivision` 2 (render 2 — the shell is ≈ 6 k quads, so ≈ 190 k faces after Solidify + 2 levels).
5. **Flex creases** (`Displace` with a parametric image or a GN field; GN chosen, node group `Boot.GN.Creases`): d(p) along the normal, sum of (a) four vamp creases: centres y_k = −158 − 14k (k = 0…3), amplitude A_k = −2.5·(1 − 0.2k) mm (grooves) with a 1 mm positive ridge each side, Gaussian width 4 along y, modulated by `Noise(scale 40) ∈ [0.6, 1]`, limited to the vamp between x ±55 and h < 120, fading to 0 at the rand; (b) ankle-break creases: 3 horizontal grooves at h 92, 104, 116, amplitude −1.8, width 3, on the quarter fronts within φ ±70° excluding the stays; (c) leather sag: `Noise(scale 6, detail 2)` × 0.6 mm everywhere on the quarters. Seam edges are damped ×0.2 within 4 mm (seam ridges stay straight).
   *2026-10-27 (§0 item 9, §4.15), replaced:* the four creases at fixed y with equal widths and a linear amplitude ramp are what the foot's critics called mechanical. `Boot.GN.Creases` now lays **folds where the vamp bends**: along the metatarsal-head line (`Boot.L.Marker.Ball1`–`.Ball5` projected onto the vamp, oblique), between the toe puff's back edge and the throat, **two or three dominant folds** (depth 1.5–2.5, spacing 9–16 drawn per fold, each a curve wandering ±3 mm that reaches the rand on one side and fades before it on the other, sometimes forking) and a field of **finer wrinkles** (0.3–0.6) between and beside them. The profile is a fold, not a Gaussian: a narrow valley 1.5–2 wide between broad rounded shoulders, the toe-side shoulder higher (the leather buckles forward). **Ankle-break folds**, 2–3 a side on the shaft front just above the strap, curved and deeper laterally; on the Cordura panels softer, wider wrinkles (pitch 4–8, depth 0.5–1). Leather sag 0.3–0.6 at low frequency; the upper bulges 0.5–1.5 over the first and fifth metatarsal heads (the last already carries the foot's form; this is the leather having stretched there). Counts, spacings, depths and paths take each boot's own seed and, with R2 in (§3.6), R2's measured statistics. The field is stored as the point attribute `crease` for spec 16's crest whitening.
6. Vertex groups written parametrically: `zone_vamp`, `zone_quarter_M/L`, `zone_counter`, `zone_stay_M/L`, `zone_collar`, `zone_ankle_pad`, `zone_toebox` (y < −230), `zone_dust_up`, `zone_scuff_front` (y < −260, h < 90), `zone_grime_low` (h < 60), `zone_polish` (quarters and counter, h 40–150), `strap_dent` (band h 150–165). *2026-10-27:* plus `zone_cordura` (the shaft panels, §3.2) and `zone_flex` (the fold band about the metatarsal-head line); `zone_polish` falls on the counter and the leather below it, and on the Cordura as spec 16's polished Cordura (roughness 0.62).

### 4.5 Step 5 — panel overlays: stays, heel counter, backstrap, toe-cap seam
Overlays are separate meshes shrinkwrapped onto `Boot.L.Upper` so their edges read as real leather edges with thickness.
1. **Stays** `Boot.L.Stay.M/L`: a strip mesh 22 wide along the throat edge polyline (sampled every 2 mm from E1 to the stay top, 10 quads across), `Shrinkwrap` (`NEAREST_SURFACEPOINT`, offset 0.3) onto the upper, `Solidify` 2.0 **offset +1** (outward; assert that the evaluated bounding box grew away from the shaft centre), `Bevel` 0.6 / 2, `Subdivision` 1. The inner edge overhangs the throat cut by 1 mm. Eyelet holes are not cut (the eyelet barrel covers them); hook plates sit on top.
2. **Heel counter** `Boot.L.Counter`: planar outline (rounded trapezoid, §3.2) drawn in the (arc-length around the heel, h) chart and mapped onto the upper by `Shrinkwrap PROJECT` along the local normal, offset 0.3, `Solidify` 2.0 outward, `Bevel` 0.6 / 2, `Subdivision` 1.
3. **Backstrap** `Boot.L.Backstrap`: 10 wide strip from the counter top (h 100) to the rim at φ 180°, same stack, 1.5 thick.
4. **Toe-cap seam, vamp/quarter seams**: no overlay; they are seam curves (§4.9) carrying a 0.8 mm ridge and the stitch rows. The vamp/quarter seam curve: from (±26, −168, 80) through (±50, −150, 55) to (±56, −120, 22) and down to the rand.
5. **Ankle padding dent:** the strap band compresses the padded quarter by 1 mm: GN `Boot.GN.Creases` adds d = −1.0·smoothstep over the `strap_dent` group (h 150–165, soft 2 mm edges) for φ outside the stays.
6. *2026-10-27 (§0 item 4):* **Cordura shaft panels.** The counter's top edge, the stays' back edges and the backstrap bound the `zone_cordura` faces of `Boot.L.Upper`, which take `Cordura.500D.Black` and the thinner build-up of §4.4; the leather overlays' edges lie on the Cordura with their thickness and two stitch rows (§4.9: the counter perimeter and stay rows already carry them). The Cordura meets the collar binding at the rim.

### 4.6 Step 6 — rand and toe bumper (`boot_upper.py: rand_bumper`)
1. Sample the upper's outer surface along the outline just above the midsole top (the junction line J at the board plane + 0.5). Build a strip mesh from J upward with a height profile: rand 12 everywhere, plus the bumper profile h_b(s) = 12 + 22·smoothstep(1 − s/120) for s (arc length from the toe tip along the outline) < 120, giving 34 at the tip (sidewalls of the strip follow the upper by `Shrinkwrap NEAREST_SURFACEPOINT` offset 0.3). `Solidify` 2.5 (rand) outward with a vertex-group thickness factor rising to 3.0 on the bumper; `Bevel` 0.8 / 3 on the top edge; `Subdivision` 1.
2. **Lip:** the top boundary loop of the bumper region (s < 120) is extruded 2.5 outward and 2.0 up as a rounded bead (extrude + `bevel` 1.0 / 3 on the new edges), fading to nothing at s 120 (scale factor smoothstep).
3. **Moulding groove:** a 0.6 wide × 0.4 deep groove 2 mm below the top edge of the rand/bumper, made by a GN displacement band (not geometry cut).
4. **Emboss:** an oval 12 × 6 at the centre front 10 below the lip, raised 0.8 — a separate oval disc mesh (24 verts) shrinkwrapped onto the bumper with offset 0.8, `Solidify` 0.8 inward, `Bevel` 0.3; object `Boot.L.Bumper.Emboss`.
5. Join rand, bumper and lip into `Boot.L.Rand`; the bumper gets its own material slot (same rubber, scuff mask active).

### 4.7 Step 7 — collar roll, tongue, gussets, pull loop
1. **Collar roll** `Boot.L.Collar`: a `Curve` object (poly spline, 96 points) following the rim at h 212 (sides), lowered 6 over a 40 mm span at φ 180° (notch), raised 6 at the stay tops (φ ±28°); the curve ends at the stays. Bevel: custom profile object — an ellipse 22 × 10 (`bevel_object` = a closed curve) so the roll is 22 tall × 10 thick, its inner face tangent to the shaft; converted to mesh, `Subdivision` 1. Binding: a 12 mm strip over the rim (`Boot.L.Collar.Binding`), Solidify 0.8, with the straight and zigzag stitch rows (§4.9).
2. **Tongue** `Boot.L.Tongue`: grid 12 × 40 lofted between the throat edges at the tongue plane (3 mm behind the stays' inner faces), width 54 at E1 → 68 at h 222, corners r 10; bowed forward 4 mm at mid-height (the padding bulge); `Solidify` 6.0 outward (*2026-10-27:* 12 above E3 tapering to 5 at E1 through a vertex-group factor, §3.2; the tongue drifts 2–5 mm toward the lateral side and twists 2–4°, per boot), `Bevel` 2.0 / 3 on the rim, `Subdivision` 1. Keeper loop: webbing strip 12 × 25 at h 150, 1.3 thick, 4 off the tongue, bar-tacked.
3. **Gussets** `Boot.L.Gusset.M/L`: triangular sheets from the tongue edges to the stays' inner edges from E1 to H1, 1.0 thick, folded once (a Z-fold of 8 mm so they do not stretch flat), mostly hidden.
4. **Pull loop** `Boot.L.PullLoop`: webbing 20 × 1.3, a 50 mm loop standing 25 above the rim at φ 180° folded 15 under the binding, bar-tack 20 × 4 (`gear_webbing.py`). Hidden by the trouser hem in the hero view; built because the client wants every component.
5. **Footbed and lining** `Boot.L.Footbed` (plate following the insole outline, 5 → 4 thick, top at the seat heights, `Bevel` 2; *2026-10-27:* 3.7 thick, its top at the seats 36 / 24, §3.1) and the lining = the inner Solidify faces of the upper (material slot `Boot.Mat.Lining` assigned to the inner faces by `use_rim_only=False` plus a material index set on the inner shell via `Solidify.material_offset 1`).

### 4.8 Step 8 — eyelets, hooks, buckle, keepers (`boot_hardware.py`)
Positions (left boot, frame B; mirror x for the other stay). Eyelet axis = stay surface normal at the point; flange 0.7 proud of the stay's outer face.

| Point | x (± for M/L) | y | h | Type | Note |
|---|---|---|---|---|---|
| E1 | 26.0 | −168 | 80 | round eyelet | lowest, at the vamp point |
| E2 | 27.0 | −160 | 101 | round eyelet | |
| E3 | 28.5 | −152 | 123 | round eyelet | |
| E4 | 30.0 | −145 | 145 | round eyelet | |
| E5 | 31.5 | −139 | 167 | round eyelet | |
| H1 | 32.5 | −134 | 189 | speed hook | on the collar band |
| H2 | 33.0 | −131 | 206 | speed hook | 12 below the stay top |

Pitch along the stay 23.5 ± 1 (E1–E5), 23 (E5–H1), 17.5 (H1–H2, the short top gap seen in the picture). Image check (right boot, y = 895 − 0.472 h): E1 857, E2 847, E3 837, E4 827, E5 816, H1 806, H2 798 — against the analysts' 858/848/838/828/818/808 and the top pair at ≈ 800.

*2026-10-27 (§0 item 6).* The table's positions are the drawing's, and they assumed the stand-in's low instep. On the real last they are placed on the built upper: **E1** at the throat's lowest point (the throat cut of §4.4 step 2 is laid on the real instep, so its foot lands near y −170 at h ≈ 85–95); **H2** 12 below the stay top and **H1** 17.5 below H2, as drawn (they are set by the rim, which is the real boot's); **E2–E5** evenly along the stay between E1 and H1 − 23 (a die punches the holes, so the pitch is regular; each eyelet sits within ±0.3 mm of its hole and its flange is seated a little unevenly, ±3° of tilt), on the eyelet line 11 mm in from the throat edge. The table above becomes the check of §1.4 item 3. Keepers (item 4 below) stand at φ **±72°** (§0 item 5).
1. **Eyelet** = torus (24 × 10, major r 3.9, minor r 1.0) + barrel cylinder Ø 7 × 7 long (24 segments) + inner washer torus (hidden): ≈ 300 faces; material `Boot.Mat.Gunmetal`. The stay surface under the eyelet is not cut; the barrel is just sunk. The lace passes through the hole (Ø 5.5 > 4 mm lace).
2. **Speed hook** = plate (rounded rectangle 14 × 16 × 1.2, `Bevel` 0.4) + hook swept from a Bezier (points: plate inner edge at h+0 → up 7 → over 180° at outer r 4.5 toward the stay → down 2; `bevel_depth 1.25`, resolution 8, fill caps) + 2 dome rivets (UV sphere r 1.5 cut at the equator): ≈ 560 faces. Orientation: the hook's opening faces +Z and tilts 20° outward.
3. **Buckle** at φ 150°, h 158: ladder-lock frame 18 × 24 × 7 from a loft of two rounded rectangles, `Solidify` 3.0, centre bar 3 × 15, `Bevel` 0.8 / 3; the strap passes through both slots (§4.10). Material gunmetal with worn edges.
4. **Keepers** at φ ±78°, h 150–166: leather loops 18 × 12 × 2 standing 5 off the quarter (a U-shaped strip, `Solidify` 2, `Bevel` 0.5), box-stitched 15 × 10 with an X (bar-tack recipe).
5. All hardware objects are bound to `Boot.L.Upper` with `SurfaceDeform` (bind after the upper's stack is final, `falloff 4`) so the armature carries them.

### 4.9 Step 9 — seams, ridges and stitch rows (`gn_stitches.py`, node group `Boot.GN.Stitches`)
Seam curves are poly splines sampled every 2 mm, shrinkwrapped to the surfaces they belong to with offset 0.3 (`Shrinkwrap` on a curve-to-mesh copy). The node group adds (a) a ridge 0.8 mm tall × 2.5 wide along felled seams (displacement band), (b) thread as 6-sided cylinders r 0.20 sunk 0.1 into the leather, stitch 2.6 long / 0.8 gap = **3.4 pitch**, each stitch bowed 0.15 mm outward, (c) bar-tacks as 1.3 pitch zigzags. Thread material `Boot.Mat.Thread`. `--lod bump` replaces (b) by the shader-level stitch bump of spec 09 §5.6.

*2026-10-27, as built in `scripts/lib/` (spec 09 §4.10, spec 13 §3.3, §3.6 notes).* The shared modules differ from this step and from §4.8 item 2 in four places, each chosen by rendering on a stand-in boot (`renders/lib_gear/`): two node groups, `Boot.GN.Stitches` (thread instanced on a carrier mesh with one edge per stitch, which a SurfaceDeform can carry) and `Boot.GN.SeamRidge`, but the felled ridge is swept geometry (`gn_stitches.welt()`), because as displacement it rendered as a sawtooth band; bar-tacks at **0.6** pitch, not 1.3, which reads as a zigzag rather than a tack; the speed-hook plate **12 × 13 × 1**, crowned, with r 3 corners (`gear_hardware.speed_hook`), not 14 × 16 × 1.2 with r 1.5, which read as a tag screwed on beside the hook; straps built solid by `sweep.strip`, not by `Solidify`. Part 02 confirms or revises each against the real boots when it is built.

| Seam | Path | Rows | Offset from edge | Length (mm, E) |
|---|---|---|---|---|
| Vamp / quarter seam (×2) | (±26,−168,80) → (±50,−150,55) → (±56,−120,22) → rand | 2, felled ridge | 1.5 and 5.5 | 2 × 95 |
| Toe-cap seam | across the vamp at y −200 (centre) → y −190 at the rand both sides | 2 | 1.5 and 5.5 | 150 |
| Stay rows (×2 stays) | along each stay from E1 to the stay top | 2 | 2 and 7 from the throat edge | 2 × 150 |
| Heel counter perimeter | the trapezoid outline | 2 | 1.5 and 5.5 | 310 |
| Back seam + backstrap | φ 180° from the rand to the rim | 1 + 2 | centre; 1.5 each side of the 10 mm tape | 170 + 2 × 170 |
| Collar binding | around the rim | 1 straight + 1 zigzag 2 wide | 2 below the rim; zigzag at 6 | 2 × 385 |
| Rand top edge | none (cemented) | — | — | — |
| Tongue perimeter | around the tongue face | 1 | 2 | 330 |
| Gusset to stay / tongue | hidden | 1 | 1.5 | 2 × 2 × 130 |
| Strap keepers (×2), tongue keeper, pull loop, strap tail | box stitch 15 × 10 with X; bar-tacks 20 × 4 (loop), 12 × 4 (tail) | bar-tack | — | — |
| Total thread | | | | ≈ 2.9 m → ≈ 850 stitches ≈ 10 k faces |

### 4.10 Step 10 — ankle strap (`gear_webbing.py`)
Path: the real strap cannot pass over the lace stays, so it is a three-quarter ring: anchored under the medial stay's outer stitch line at φ −32°, around the medial quarter, the heel and the lateral quarter to the ladder-lock at φ 150°, then the free tail runs forward through the lateral keeper at φ 78° and ends 35 mm beyond it, folded 10 and bar-tacked. *2026-10-27 (§0 item 5):* the keepers stand at φ ±72° and the tail ends 35 beyond the lateral one; the strap is pulled snug, so it sits 0.3–0.8 mm deeper in the padding over the Achilles side than at the front (where it tucks under the stays), and its tail curls 1–2 mm off the keeper's face. The ring is sampled every 1 mm at h 158 (≈ 300 points), offset +1.0 mm from the quarter's outer surface (0 mm where it tucks under the stay edges, 1 mm proud over the counter and backstrap). Strip 15 wide × 6 quads across, `Solidify` 1.5 (+1 outward, bounding-box assert), `Bevel` 0.6 / 3 at 60°; herringbone webbing material; the tail is a second 35 mm strip lying on the first through the keeper. Z-jitter 0.3 mm and 0.4° roll for realism (prototype §8).

### 4.11 Step 11 — laces (`boot_laces.py`)
Two Bezier curves per boot, `Boot.L.Lace.A` (the end that starts at E1 medial) and `Boot.L.Lace.B` (E1 lateral), `bevel_depth 2.0`, `bevel_resolution 6`, `resolution_u 16`, `use_fill_caps`; point radius 0.8 at eyelets/hooks (flattened cord) and 1.0 elsewhere; the braid, colour and sheen from `Boot.Mat.Lace`. The curve's own `UVMap` drives the braid (prototype §5: `use_uv_as_generated` no longer exists in 4.5).
Routing (criss-cross, Ian's method; coordinates from the table of §4.8; "inside" = 3.5 mm behind the stay's outer face, "outside" = lace radius above it):
1. **Bottom bar:** A and B start as one lace: a straight bar across the throat between E1-M and E1-L on the INSIDE (under both stays, over the tongue), visible in the throat gap.
2. Both ends emerge **inside → out** through E1 (control points: inside at E1 − 3.5 n, outside at E1 + 2.0 n, tangent along the eyelet axis).
3. **Diagonal k (k = 1…4):** the end leaving E_k on side S crosses the throat to the opposite stay, rising one pitch: control point at the crossing centre (x 0, the midpoint of E_k and E_{k+1} in y, h) lifted **6.0** mm above the tongue plane for the strand that is OVER and **2.4** for the strand UNDER (A is over on odd k, B on even k); then it dives under the opposite stay's inner edge (a point 1.5 mm below the stay's inner face at x = ±w(h)) and emerges **inside → out** through E_{k+1} on that side.
4. **Diagonal 5 (E5 → H1):** crosses as above but does not dive: it arrives at the hook from below on the outside, wraps the hook post 180° (points at the post's bottom, outer side, top; radius 0.8), and leaves upward for diagonal 6.
5. **Diagonal 6 (H1 → H2):** crosses to the opposite H2, wraps it the same way.
6. **Knot:** above H2 the two ends meet at the centre (0, −128, 210): a reef-knot body approximated by two interlocking half-tori (major r 4, minor r 2, 12 × 8 each) joined into `Boot.L.Lace.Knot`, 14 × 10 × 8 overall, sitting against the tongue top.
7. **Bow tucked:** from the knot, each end forms a loop (ear) 30 mm long folded DOWN behind the tongue top (between tongue and collar, visible only from above) and continues as a 60 mm tail running down inside the shaft between the tongue and the medial/lateral collar; aglets (cylinders Ø 4.5 × 20, `Boot.Mat.Gunmetal` dulled) at the tail ends. Lace length check by `curve.calc_length()` on both ends + knot ≈ 1450–1550; assert.
*2026-10-27 (§4.15).* The routing above is exact; a laced boot is not. Each boot's seed sets: crossing centres 1–4 mm off the throat's centre line (alternating sides, not a zigzag of fixed amplitude); the tension tighter at the ankle (H1–E4: strands straight, cord flattened 3.0 × 4.8) and slacker lower (E1–E3: 1–2 mm of sag between crossings, cord round); the lace's own twist along each strand (the braid's diamonds turn 0–180° between eyelets); the bar at E1 slightly bowed; the knot a little off centre and tilted; the two tails of unequal length (60 ± 15). Nothing here changes the over/under order or the crossing count of §1.4 item 4.
8. Collision pass: for every crossing, ray-test the two strands; if closer than 0.3 mm lift the over strand by the deficit. Ray-test every segment against the tongue, stays and hooks (BVH) and report any penetration > 0.2 mm as a failure.
9. Export only: `Convert to mesh` on a copy (`Boot.L.Lace.A.Mesh`), ≈ 6 k faces per end.

### 4.12 Step 12 — joins and contacts
| Pair | Contact rule |
|---|---|
| Upper ↔ midsole | the upper's outer surface meets the midsole top 0.5 inside the sidewall; the rand covers the junction (rand bottom edge 0.3 below the midsole top so no gap shows) |
| Midsole ↔ outsole | 0.5 groove (inset difference), both bevelled |
| Lugs ↔ outsole | sunk 1.5, no boolean |
| Stays / counter / backstrap ↔ upper | 0.3 proud via Shrinkwrap offset; their rims are the leather edges |
| Collar roll ↔ upper | tangent at h 200–212, roll overhangs the rim inward by 2 |
| Tongue ↔ stays | tongue 3 behind the stays' inner faces; gussets close the gap |
| Hardware ↔ stays | flanges 0.7 proud; plates 0 proud on the collar band |
| Strap ↔ quarters | 1.0 proud; dent 1.0 in the padding; ends tucked under the stays' outer stitch line (0.5 overlap, hidden) |
| Laces ↔ eyelets | through the holes, radius 0.8 → 3.2 mm cord in a 5.5 hole |
| Footbed ↔ last | the last's plantar surface rests on the footbed top (0 gap, hidden) |

### 4.13 Topology targets and poly budget (per boot, render evaluation)
| Object | Base | Evaluated | Notes |
|---|---|---|---|
| `Boot.L.Upper` | ≈ 6 k (remeshed quads/tris) | ≈ 190 k (Solidify, Subsurf 2) | all seams on the surface via GN; no poles matter after remesh |
| `Boot.L.Sole.Outsole` / `.Midsole` / `.Board` | 1.2 k / 1.2 k / 0.4 k | 14 k | 96-point outline × 4 rings, bisected every 14 mm |
| `Boot.L.Sole.Lugs` | 9 k | 9 k | ≈ 100 lugs |
| `Boot.L.Rand` (+ emboss) | 2.4 k | 10 k | |
| `Boot.L.Stay.M/L`, `.Counter`, `.Backstrap` | 2.6 k | 12 k | |
| `Boot.L.Collar` (+ binding) | 1.8 k | 7 k | |
| `Boot.L.Tongue`, `.Gusset.M/L`, `.PullLoop`, `.Footbed` | 1.6 k | 6 k | |
| Eyelets 10, hooks 4, buckle, keepers 2, aglets 2 | 6.2 k | 6.2 k | |
| `Boot.L.Strap` (+ tail) | 2.6 k | 2.6 k | |
| `Boot.L.Lace.A/B/Knot` | curves | ≈ 13 k | |
| Stitches | — | ≈ 10 k | `--lod bump` drops them |
| **Total** | | **≈ 280 k faces per boot, 560 k the pair** | within the 2–4 min evaluation render budget (research_blender_capabilities) |

### 4.14 Step 14 — the right boot and naming
After the left boot's stacks are applied where required (the Shrinkwrap/Solidify stacks stay live, GN stays live), the whole `Boot.L.*` set is duplicated, mirrored in X about the boot frame origin (`Mirror` modifier is NOT used — a true duplicate with `scale.x = −1` applied, normals recalculated outward with `bmesh.ops.recalc_face_normals`, curve handles mirrored), renamed `Boot.R.*`, and its `SurfaceDeform` bindings redone. Collections: `Part02.Boots` → `Boot.L`, `Boot.R`, `Boot.Guides` (seam curves, lace guides, markers, cutters; excluded from render). Materials `Boot.Mat.*` are shared; images `Boot.L.Mask.*` / `Boot.R.Mask.*` are per side (the dust differs: the left boot is dustier, §5.5).

*2026-10-27 (§0 items 3, 8, 10, 12).* **Mirror about x = 0** (the world YZ plane), not about the boot frame's origin, so `Boot.R.*` stands on the right rest foot; frame-B copies for the right boot's closeups are mirrored in X as the presets expect. **Only the pattern and the hardware are mirrored**: after mirroring, the right boot re-runs the seeded stages with its own seed (seed + 1): the creases and bulges (§4.4 step 5), the lace crossings, tension and tails (§4.11 note), the tongue's drift, the lug wear, the strap's seat, and its wear masks (side factor 0.7 against the left's 1.0, spec 16's `boot.toe`). Then the `weights` stage moves each boot under its rest foot and binds it (§7.1). Names: images `Boot.L.Img.Wear`, `Boot.R.Img.Wear` (spec 16 §7.1, C24), materials `Boot.Mat.<ID>`; frames `Frame.Boot.L/R` (frame B Empties, children of the render copies, for spec 17's presets); the `Part` record declares `prefixes=("Boot.", "Frame.Boot.")`, `needs={"01": "Foot.L.Last", "08": "Morgan.Rig", "17": "camera"}`, `proxies={"01": "stand_in_last"}`, `provides=("Boot.L.ShaftProxy", "Boot.R.ShaftProxy", "Frame.Boot.L", "Frame.Boot.R")`, `presets="p02"`, `params="scripts/parts/p02/params.json"` (spec 18 §4.4). The cache is `cache/parts/02_boots.blend`.

### 4.15 Against the mechanical look (2026-10-27, §0 item 9)
The foot's ten critic rounds taught two things (`notes/critic/foot_*`, `notes/research_foot_hires.md`): modelled parts read crisp, even and mechanical next to scanned, organic forms; and large forms set by scalar targets (a girth, a width, an ellipse) read wrong wherever real geometry was available, however well the numbers were met. A manufactured boot is regular where it is made (a moulded sole, a die-punched eyelet row, machine stitching) and irregular everywhere it is used. The rules:

1. **Real geometry first.** The inside is the real last (spec 01, scan 038); the large outer forms (shaft sections, collar, instep, toe-box dome, counter bell, sole sidewall) come from the real boot's published dimensions (§3) and, once fetched, from R1's sections (§3.6), not from ellipses and smoothsteps. A scalar target is a check on a form, never its only source.
2. **Deformation where the boot flexes and loads.** Folds along the flex line and at the ankle break (§4.4 step 5), bulges over the metatarsal heads, the collar's slump at the back, the toe box's slight sink behind the lip, the strap's bite into the padding, the shaft's lean following the shin. The rest of the upper keeps the leather's stiffness: no noise-wobble over the whole surface.
3. **Wear where it touches.** Lug tops and edges by load (heel strike laterally, the ball, toe-off), the bumper's lip and the toe's front, the medial ball and toe sides (the other boot), the collar top (the trouser hem), the hook lips and eyelet rims (the lace), the strap's edges at the keepers. Dust lies in valleys, seams and the welt, and on up-faces, and wears off crests; grime collects low. These are fields of geometry and use, not of a uniform noise.
4. **No stamped rows.** Anything made by hand or by use varies: fold spacings and depths (coefficient of variation ≥ 0.2), lace crossings and sag, the tongue's drift, stitch rows that follow the leather's pull (±0.3 mm wander, a few stitches sunk deeper), each eyelet's seat. What a machine makes stays regular (the lug pattern, the hole pitch, the stitch pitch), but even those wear unevenly.
5. **Edges are rounded.** No visible edge sharper than r 0.5 mm; worn leather edges and lug corners r 1–2. A crisp bevel is a mould edge, and moulds' edges wear.
6. **A pair, not a mirror** (§4.14): the critic must find differences between the boots beyond the drawn dust.
7. **Judge in clay, beside real geometry.** Every form iteration is judged first in `form` renders of V7–V9 beside R1 (or R2) in the same clay and camera, as the foot's were beside scan 038, before any material is set; `measure()` reports the section deviations from R1 (§8.3).

---

## 5. Materials and textures

Principled BSDF (Blender 4.5) values are linear; hex values are the sRGB equivalent of the base colour, and the "target" column is the reference pixel the graded render must hit (AgX, "AgX - Medium High Contrast", the hero lights). Before shading anything the swatch procedure of research_prototypes §0 is run (four spheres at albedo 0.012 / 0.03 / 0.06 / 0.25 under the hero lights) and the results written to `renders/02_boots/swatch.png`, so nobody mistakes a grey render for a bright material again.

*2026-10-27 (§0 items 4, 7): spec 16 supersedes this section's values.* The part asks the library for materials by catalogue ID (`materials.get(ID)`, assigned as `Boot.Mat.<ID>`) and creates no Principled BSDF of its own; what stays here is the regional data the library takes from this part (the zones, the side factor, the targets of §5.6, the crease attribute). The boot's recipes, as `scripts/lib/mat_catalogue.py` holds them today (`LIB_VERSION` 16.1): **built** are only `Skin.Foot`, `Nail.Plate`, `Nail.FreeEdge` and `Knit.Sock.WoolNylon(.Reinforced)`; **every recipe below is `PLANNED`** (asking for it raises "not built yet"), so part 02 builds them in spec 16's family modules (`mat_hard.py`, `mat_fabric.py`) before its look stage:

| This section's material | Library ID (spec 16 §3.3) | Family module, status | Groups it needs (spec 16 §4; built?) | Assets (in `assets/manifest.json`) |
|---|---|---|---|---|
| `Boot.Mat.Leather` (vamp, toe box, counter, stays, backstrap, keepers, tongue face) | `Leather.Boot.FullGrain` (smooth; Q14) | `mat_hard`, planned | `MG.Polish`, `MG.Mask.EdgeBevel`, `MG.Weather.Dust` (no); `MG.Weather.Grime`, `MG.Tile.AntiRepeat` (yes) | `Leather032` at 80 mm |
| suede (only if Jeff picks the Zephyr's finish, Q14) | none: would need a new `Leather.Boot.Suede` (nap, no coat, sheen 0.04–0.08, the dust held in the nap) | — | as above + `MG.GN.Fuzz` for silhouettes | none yet (an ambientCG suede set would be added) |
| Cordura shaft panels, collar roll, gussets | `Cordura.500D.Black` (polished 0.62 on the counter's rub zone) | `mat_fabric`, planned | `MG.Weave.Basket` (no) | `Fabric063` at 156 mm |
| `Boot.Mat.Rubber.Outsole` | `Rubber.Outsole.Black` (albedo 0.018) | `mat_hard`, planned | lug-top wear in-shader; `MG.Weather.Dust` (no) | `Rubber004` at 50 mm |
| `Boot.Mat.Rubber.Rand` (rand, bumper, lip, emboss) | `Rubber.Rand.Black` (0.020) | `mat_hard`, planned | `MG.Mask.EdgeBevel` (no) | `Rubber004` |
| `Boot.Mat.Midsole` | `EVA.Midsole.BlueGrey` (the PU, roughness 0.30) | `mat_hard`, planned | `MG.Weather.Grime` (yes) | — |
| `Boot.Mat.Webbing` (strap, tail, pull loop, lace garage) | `Webbing.Nylon.Black` | `mat_fabric`, planned | `MG.Weave.Herringbone` (no) | `poly_wool_herringbone` at 280 mm across `u` |
| `Boot.Mat.Lace` | `Lace.Nylon.Black` | `mat_fabric`, planned | `MG.Braid` (no) | — |
| aglets | `Polymer.Black.Smooth` | `mat_hard`, planned | `MG.Mask.EdgeBevel` (no) | `Plastic012B` |
| `Boot.Mat.Gunmetal` (eyelets, hooks, rivets, buckle) | `Metal.Gunmetal` (F0 0.10, rough 0.45; worn edges bare steel) | `mat_hard`, planned | `MG.Mask.EdgeBevel`, `MG.Weather.Edge` (no) | `Metal027` at 60 mm |
| `Boot.Mat.Thread` | `Thread.Bonded.Black` | `mat_fabric`, planned | — | — |
| `Boot.Mat.Lining` / `.Footbed` (hidden) | `Fabric.BackFace` (lining), `Foam.ClosedCell.Black` (footbed, padding edges) | `mat_fabric`, planned | — | — |

Wear (spec 16 §4.10, §5.3): the preset `boot.toe` exists as data; `set_wear_source` and `bake_masks` are not built (they raise `NotBuilt`), so the first look pass uses live shader masks (source (a)) and bakes only for the export. Dust, scuff and polish follow §4.15 item 3 as well as the zone weights below. The texture, density and mask tables of §5.1–§5.5 are read with spec 16's corrections: `Leather032` at 80 mm (not 250), `Fabric063` at 156 mm (not 100), albedos at the class floors (outsole 0.018, rand 0.020, Cordura #282624, webbing #292725, thread #24211e), `Img.Wear` packing R dust, G grime, B edge and scuff, A polish, `UV.Real` / `UV.Atlas`, one atlas `Export.Boots` 2048² (3.1 px/mm) for the game.

### 5.1 Material list
| Material | Base colour (linear → sRGB) | Rough | Other | Textures | Targets |
|---|---|---|---|---|---|
| `Boot.Mat.Leather` (vamp, quarters, stays, counter, tongue face, keepers) | (0.026, 0.024, 0.022) → #2d2b29 | 0.50 base; map 0.36 (polish) … 0.78 (dust) | Specular IOR level 0.5, Coat 0.12 (coat rough 0.30) on `zone_polish` only; Sheen 0; Bump from `Leather032_NormalGL` (strength 0.35) + creases from geometry | `Leather032` Color (×1.3, desaturated 50 %) as a 10 % multiply only, Roughness map remapped 0.4–0.75, NormalGL; tile **250 mm** (grain cells 0.4–0.8 mm [VERIFY: measure the texture's cell size]) | R vamp #2f2c27 (690,855), R quarter #101115 (740,840), L quarter lateral #3e444e (955,840), L medial #272017 (905,830) |
| `Boot.Mat.Rubber.Outsole` (outsole base, lugs, perimeter teeth) | 0.012 → #1d1d1d | noise 0.50–0.70 | micro grain bump `Noise(scale 2500)` 0.15 mm; lug tops → wear (§5.5) | `Rubber004` NormalGL at 150 mm tile on the sidewall (`UV_Side`) | lug #010101–#3d3e41, outsole edge #202227 (720,890) |
| `Boot.Mat.Rubber.Rand` (rand, bumper, lip, emboss) | 0.015 → #212121 | 0.48 (bumper), 0.55 (rand) | scuff and dust masks | same grain | R bumper #1a1911 front, #423c36 top (dust), L bumper spec #4a5363 (955,872) |
| `Boot.Mat.Midsole` | (0.020, 0.022, 0.027) → #282a2f | **0.30** (map 0.26–0.36) | Specular IOR level 0.6; this is the stripe that reflects the cool lamps; grime only 30 % | fine EVA cell bump `Noise(scale 1200)` 0.08 mm | **#333a48 at (700,880)**, #313841 (762,872) |
| `Boot.Mat.Cordura` (collar roll, binding, gussets) | (0.022, 0.020, 0.018) → #292725 | 0.78 | **Sheen 0.06**, sheen rough 0.5 (prototype §0: never 1.0) | `Fabric063` NormalGL + Rough at 100 mm tile; weave bump 0.6 | R collar #1f1b17 (725,805), L collar lateral #2e3439 |
| `Boot.Mat.Webbing` (strap, tail, pull loop, tongue keeper) | 0.020 → #262626 | 0.70 | Sheen 0.06; herringbone weave bump (wave × wave, rib 2.5 mm along `u`) | procedural | strap #393e47 (750,820) under the cool light |
| `Boot.Mat.Lace` | (0.030, 0.028, 0.024) → #333129 | 0.72 | Sheen 0.10, sheen rough 0.5; braid bump: `max(pingpong(u+v), pingpong(u−v))^1.6`, one repeat per **0.7 mm** of lace, 3 around, Bump 0.15 mm strength 0.5, groove darkening ×0.8; dust 0.3 on up-facing segments | curve UV | #4a473f (935,850), #41362d (915,840), dark #1a1511 |
| `Boot.Mat.Gunmetal` (eyelets, hooks, rivets, buckle, aglets) | (0.10, 0.095, 0.09) → #5b595a | 0.42 | Metallic 1.0; rim wear via `ShaderNodeBevel` (r 0.8, 4 samples) dotted with the true normal → base 0.55, rough 0.28 on edges (prototype §8 "wear masks"); aglets rough 0.6 | `Metal027` Rough as micro variation | eyelet #322d28 (706,816), #37302c |
| `Boot.Mat.Thread` | 0.020 → #262626 | 0.60 | Sheen 0.10 | — | reads as black lines with a faint sheen |
| `Boot.Mat.Lining` / `Boot.Mat.Footbed` | 0.06 grey / 0.03 | 0.9 / 0.7 | — | mesh bump (`Voronoi` 1.2 mm) | invisible in the hero view |

### 5.2 UVs and texel density
* `UV_Atlas` (per boot, one 2048² here, 4096² on the GPU machine): the upper is unwrapped with the panel seam curves as UV seams (edges within 1 mm of a seam curve are marked seam by script, then `bpy.ops.uv.unwrap` with `temp_override` and the object active in edit mode, `margin 0.003`), overlays, collar, tongue and rand with `Smart UV Project` (angle 66°). The boot's outer surface ≈ 0.12 m² → **≈ 6 px/mm at 2048², 12 px/mm at 4096²**; the hero closeups need ≥ 8 px/mm for the 0.4 mm grain, which the tiled grain textures provide (`Leather032` at 250 mm → 8.2 px/mm; `Rubber004` at 150 → 13.6; `Fabric063` at 100 → 20).
* Tiled grain maps use `Box` projection from Object coordinates (blend 0.2) on the hard parts and `UV_Grain` (the atlas scaled ×4) on the leather so the grain does not swim across seams.
* The lace braid, webbing weave and rubber micro grain are procedural (no image).

### 5.3 Leather detail stack (in `Boot.Mat.Leather`)
1. Grain: `Leather032_NormalGL` strength 0.35 (cells 0.4–0.8 mm) + `Noise(scale 900)` 0.03 mm for pore scatter.
2. Flex creases and sag: geometry (§4.4 step 5); crest whitening: the GN writes the crease field to an attribute `crease`; the shader lifts the albedo by +0.012 and roughness +0.1 where `crease > 0.5` (the #5c4e3d crests).
3. Polish: `zone_polish` × `Noise(scale 4)` ∈ [0.3, 1] → roughness toward 0.36, Coat 0.12; strongest on the heel counter and the lateral quarter.
4. Scuff lines on the quarters: `Noise` with anisotropic `Mapping` (1, 1, 14) thresholded 0.66–0.72 → roughness 0.8 and albedo +0.01, 6 % coverage.
5. Dust (§5.5) last, over everything.

### 5.4 Rubber detail stack
Outsole/lugs: albedo 0.012; roughness `Noise(scale 60)` remapped 0.50–0.70; lug tops (`N·−Z > 0.7`) → albedo 0.14, roughness 0.75 (worn and dusty), sides stay black (prototype §4 (b)); sipes darken ×0.6 inside the groove (AO does this naturally); sidewall grain from `Rubber004` normal. Rand/bumper: as above with roughness 0.48–0.55 and the scuff mask (§5.5). Midsole: cell bump only, roughness 0.30 so it reflects.

### 5.5 Weathering masks (baked once per boot to `Boot.<L|R>.Mask.Weather` RGBA 2048² by `bpy.ops.object.bake` type EMIT from helper materials; R dust, G scuff, B grime, A polish; also `Boot.<L|R>.Mask.AO`)
| Mask | Field | Effect | Reference |
|---|---|---|---|
| **Dust** (R) | `smoothstep(0.3, 0.9, N·Z)` × `SurfaceImperfections015` Opacity (tile 300 mm) × zone weight (toe box 1.0, vamp 0.8, collar roll top 0.6, bumper top 0.9, quarters 0.15, shaft sides 0.05, lace up-facing 0.3) × side factor (**L 1.0, R 0.7** — the forward left boot is dustier in the picture) | mix albedo toward dust (0.32, 0.27, 0.23) → #9a8e82 by mask × 0.55; roughness +0.25 × mask; Coat × (1 − mask) | R toe top #423c36, L vamp #6c5943 lit, highlights #a19689 |
| **Scuff** (G) | `zone_scuff_front` × streak noise (`Mapping` 1, 1, 10 along the boot axis, threshold 0.6) + Pointiness-free edge mask from the bake AO inverted on the bumper lip | albedo toward pale grey (0.18, 0.17, 0.16) × mask; roughness 0.8; bump −0.1 mm | bumper fronts, lip |
| **Grime** (B) | `HeightBand(h < 60 → 1 at 20)` × `SurfaceImperfections017` Opacity (tile 200 mm) × material weight (rand 0.6, outsole sidewall 0.6, midsole **0.3**, lower quarters 0.4) | albedo toward brown-grey (0.12, 0.10, 0.08) × mask × 0.5; roughness +0.2 × mask (midsole +0.08 only) | R heel side #303436, L medial sole edge #9b8975 (lit dust) |
| **Polish** (A) | `zone_polish` × `Noise(scale 4)` | §5.3 step 3 | R quarter #101115 |
| **Lug wear** | `N·−Z > 0.7` on `Boot.Mat.Rubber.Outsole` (shader, not baked) | §5.4 | lug tops lit pale on the left toe row |
| **Metal rim wear** | `ShaderNodeBevel` mask (shader) | §5.1 Gunmetal | eyelet rims #322d28 vs body #1f1b16 |

### 5.6 Colour targets after grading (read 5 × 5 means on V1/V2; tolerance ΔE 12 unless stated)
(640,870) #423c36 · (660,860) #3e372e · (690,855) #2f2c27 · (740,840) #101115 · (750,820) #393e47 · (700,880) #333a48 · (720,890) #202227 · (760,885) #303436 · (706,816) #322d28 · (915,870) #6c5943 (ΔE 15) · (955,872) #4a5363 · (955,840) #3e444e · (905,830) #272017 · (935,850) #3d3933 · (960,905) #020202 (luminance ≤ 6) · (720,915) floor smudge #343435 (luminance 45–85).

---

## 6. Fibres, simulation or dynamics

* **No hair, no fur.** The leather is grain, not nap; the Cordura collar's fuzz is below pixel size at every view (a 0.05 mm fibre at 12 px/mm is 0.6 px) and is represented by the sheen term only.
* **No cloth simulation in this part.** Boots are stiff; the only soft components (collar roll, tongue, gussets, strap) are shaped parametrically. The trouser hems that fall on our collars are simulated in spec 09 against our `Boot.L/R.ShaftProxy` (§10.2).
* **Laces are static curves**, not simulated: their shape is fully determined by the routing (§4.11); the only "physics" is the gravity sag of the hidden tails (3 extra points with a 4 mm droop) and the flattening of the cord at eyelets (radius 0.8).
* **Leather flex creases and the strap dent are procedural displacement** (`Boot.GN.Creases`), seeded; `--seed` changes the noise terms only, never the crease positions.
* **Dust is static**; the left boot is dustier by design (§5.5). A `--dust 0.0…1.5` command-line multiplier lets the critic loop tune it without editing the script.
* **Floor interaction:** the floor reflection smudges and contact shadows are produced by the eval floor material; we only guarantee the boots' albedo and the lug tips at z 0 ± 0.2 (the sole must sit on the floor, not hover or sink — asserted on the mesh).

---

## 7. Rigging and attachment

### 7.1 Bones (MPFB `default` rig names via the shared `BONE_MAP`; spec 01 adds `heel.L/R`, `ball.L/R`, `toes_master.L/R`)
| Region (left boot) | Bone(s) | Weights | Why |
|---|---|---|---|
| Sole, upper, rand, counter, hardware behind the ball line (y > −210) and below h 110 | `foot.L` | 1.0 | the hindfoot and the sole are one rigid shell |
| Sole and upper forward of the ball line (y < −210): toe box, bumper, forefoot lugs | `ball.L` | 1.0, blended to `foot.L` over y −195 … −225 (30 mm smoothstep) | the only flex a boot has is at the ball; each **lug** takes the uniform weight of its base centre so lugs never shear |
| Shaft h 110 → 222 (quarters, stays, collar, tongue, strap, hooks) | `foot.L` → `lowerleg02.L` | `lowerleg02` weight 0 at h 110 rising to **0.7** at h 212 (smoothstep) | a laced shaft follows the shin partly; the ankle is plantigrade in the pose so the shaft stays near vertical |
| Laces, knot, aglets | follow the upper | `SurfaceDeform` to `Boot.L.Upper` | curves cannot carry armature weights cleanly |
| Eyelets, hooks, buckle, keepers, stitches | `SurfaceDeform` to their host (`Upper`, `Stay`, `Collar`) | bound after the host stack is final | |

Weights are written by script from position (no auto-weights): `vg.add([i], w, 'REPLACE')` from the formulas above, then an `Armature` modifier (`Morgan.Rig`, `use_deform_preserve_volume False`) is placed FIRST in every stack. Weight transfer from the body is not used (the body's foot weights would bend the sole like skin).

*2026-10-27 (§0 item 3), the bind and the weights, replacing the table's first two rows.* The boot is built in frame B, standing on the floor with the seated last inside; the rig's rest foot is flat on the floor, so the two do not coincide. The `weights` stage therefore computes, per side, the rigid transform **T** that carries the seated last's markers (`Boot.L.Marker.Pternion`, `.Ball1`, `.Ball5`) onto `Foot.L.Last`'s own markers at rest (a least-squares rigid fit, residual < 0.5 mm), applies T to every `Boot.L.*` object (the boot then sinks 24–36 mm below the floor and tilts heel-down by the pitch, wrapped round the flat rest foot) and binds there. In the hero pose spec 08 sets `foot.*` so that `Boot.*.Marker.Ground.*` lie on z 0 at the headings, which restores the boot to the floor and makes the plantar flexion (≈ 4–4.5°) and the ankle height (≈ 113) readbacks (dated note in spec 08). Weights: **everything below h 110 and the whole sole, toe box, bumper and lugs `foot.L` 1.0** (rigid; no flex at the ball in this build): spec 08 makes `ball.*` a non-deforming marker, and weighting the forefoot to the `toeN-1` bones would turn the toe box up by the hero's 12° toe extension on top of the toe spring it was built with (Q18 asks about a flex bone for animation). The shaft's ramp to `lowerleg02.L` (0 at h 110 → 0.7 at h 212), the laces' and hardware's `SurfaceDeform`, the script-written groups and the `Armature` modifier first in every stack stand; heights h in the ramp are frame-B heights, evaluated before T.

### 7.2 Heel pitch and the foot inside
The last is rotated 5.4° about the ball line (§4.1); the foot and sock of spec 01 inside the boot must carry the same rotation: the pose part sets `foot.L/R` plantar flexion **+5.4°** with `ball.L/R` (toes) dorsiflexed −5.4° + the last's toe spring, so the sole plane of the foot matches the footbed. With the boots on, the body's feet are hidden, so this only matters for clearance (§8.6) — but it is the honest geometry (§10.3 question 10). *2026-10-27 (§0 items 2, 3):* the seats are 36 / 24 and the pitch ≈ 4–4.5°, set by the last's markers (§4.1 step 2); with the boot bound to the foot (§7.1) the foot and the boot cannot disagree in any pose, and spec 08 reads the plantar flexion back instead of typing 5.4°; `toes_master.*` keeps the last's 12°.

### 7.3 Modes
* `--mode posed` (hero): built in frame B at the rest pternion, then the armature places it; the pose part's values: right foot heading 90° to his right plus 15–20° toe-away, left foot 15° to his left, ankles at (±208, ∓75, 80) (spec 01 §7.3), weight 55/45 right-heavy (no visible effect on rigid boots).
* `--mode rest`: the same build, armature in rest; deliverable for animation.
* Right boot = mirror (§4.14) before binding; both boots bound to the same rig.
* *2026-10-27 (§0 items 3, 5):* the hero values are spec 08's: heading **85°** to his right (toe 5° toward the camera) and **17°** to his left, ankles at (−208, +75) and (+208, −75) in plan, the boots' ground markers on z 0, the ankle axes then at h ≈ 113 (not 80, not 122); the buckle at φ 150° does not show behind the right heel (§2.4 item 3). `--mode posed` renders the frame-B copies placed by those rigid transforms (§1.3 note), so the part needs no posed rig for V1–V2. Export consequence: in the bind (rest) pose the boots stand below the floor and tilted, and the game's rest pose inherits that; a rest with the soles on the floor needs a booted rest pose, spec 08's call (§9.4).

### 7.4 Collisions and proxies
`Boot.L/R.ShaftProxy` (for spec 09's cloth sim): a decimated copy of the evaluated upper + collar from h 60 to the rim, ≈ 600 faces, with the collar's rounded rim (r ≥ 10, essential: a sharp rim slices cloth) and the instep wedge (the upper's own instep slope, 35°), `Collision` modifier `thickness_outer 0.003`, `cloth_friction 30`; nothing above h 222 and nothing wider than the rim ellipse 138 × 106 above h 200 (spec 09 asks for no geometry above h 212 at radius > 75: our pull loop stands 25 above the rim at the back — it is excluded from the proxy and from the collision set, and sits under the hem anyway). *2026-10-27 (§0 item 11):* the hems stack on the collars (spec 09 §2.4: neither tucked nor bloused), so this proxy is the surface they land on; it is made from the bound boot and deforms with it, and the posed proxy (the hero) is what spec 09 simulates against. The rim ellipse 138 × 106 (385) is the drawing's, measured; the real boot's collar (S1) is the same height.

---

## 8. Evaluation protocol

### 8.1 Renders
`--eval` renders V1–V7 of §1.3 for both boots (V3–V7 for the left boot and mirrored for the right: 12 closeups + 2 reference frames), writing `renders/02_boots/V<k>_<name>_<L|R>.png`, plus `swatch.png`. V1/V2 use `render.use_border` + `use_crop_to_border` on the hero frame (1672 × 941 at 48 spp, adaptive, OIDN, `use_persistent_data`) so only the boot boxes are traced (≈ 45 s each); closeups 1024² at 48 spp (≈ 30 s each); `--fast` uses Workbench (matcap + cavity, ≈ 5 s per view) for geometry iterations; `--final` 2048² at 256 spp on the GPU machine. *2026-10-27 (§0 items 8, 10):* through spec 18's CLI and spec 17's harness instead: `--render --views … --quality form|look|eval|final` renders the `p02.json` presets (V1–V9, `.L`/`.R` by `sides`) into `renders/02_boots/<preset>_<tier>.png` with JSON sidecars; `form` (Workbench clay) for every geometry iteration, `eval` for critic packets, `final` for acceptance. On the RTX 3050 a boots crop at `eval` takes ≈ 4 s and a warm `form` view 0.03–0.1 s (spec 17 §4.14), so a whole set is minutes. The part makes its render copies itself after saving the cache, as part 01 does (spec 18 §4.13, "left of W1": `cli.py`'s `--render` has no hook for them yet). The swatch procedure is spec 16's `lookdev.py --swatch` on the boot's IDs.

### 8.2 Overlays and silhouette metric
* Difference-blend and 50 % blend of V1/V2 over the reference crops (PIL), saved as `V1_overlay.png`, `V2_overlay.png`; the critic reads the edges of the collar top, sole line, toe tip and heel back directly.
* Boot masks: render a second pass with `Boot.*` as an emission-white override (or Cryptomatte object pass) → M_r. Reference mask M_ref: `rembg` u2net failed exactly on dark boots against the dark floor (research_ai_helpers §5), so the reference mask is a **luminance threshold < 110 inside the boot boxes, excluding the reflection below the sole line (y > 896 right, > 908 left) and the trouser cuff above y 806**, saved once to `ref/masks/boot_R.png`, `boot_L.png`. IoU(M_r, M_ref) ≥ 0.90 (right), ≥ 0.88 (left, its lacing region is noisier). Report the widths at y 810 / 830 / 855 / 880 / 895 against spec 01 §2.2's silhouette runs (±5 px).

### 8.3 Metrics (`measure_boot.py`, printed and written to `renders/02_boots/measure.json`)
On the evaluated meshes: outsole length and widths at y −40 / −110 / −185 / −210 / −265 (bisect planes); heel and forefoot stacks (z of the midsole top at y −40 and −210); toe spring (lug tip z at y −295); heel block length (heel breast y); lug heights by zone (ray casts from z −20 upward at 500 sample points: tip z vs base z); lug coverage (rasterised); sipe count per lug (sample 10 lugs); rand height; bumper top height at s 0 / 40 / 80 / 120; collar rim heights at φ 0 / 90 / 180 / 270 and roll section; eyelet and hook positions vs the table of §4.8 (±1.5 mm); stay width; strap width, height band, buckle φ and proudness; lace diameter at a crossing and at an eyelet; lace total length; stitch pitch (distance between consecutive stitch instances on three seams); shaft ellipse semi-axes at h 110 / 158 / 212; last-to-lining minimum distance (BVH, must be ≥ 0.5); lowest vertex z; inter-object overlaps (BVH between every object pair, excluding designed contacts of §4.12); face counts.

*2026-10-27 (§0 items 2, 3, 6, 9, 10).* `measure()` lives in the part script and returns spec 18's envelope (`{part, metric, value, target, tol, unit, pass, source}`) on its `measure.py` primitives (`section`, `girth`, `clearance`, `landmarks`); it runs on the frame-B state. Added: **seats** at the heel seat point and under `.Ball1`/`.Ball5` (36 ± 1.5, 24 ± 1.5) and the **pitch** read back (report); the lug heights by zone against 5 / 4.5 / 3 (± 0.5); the **ground markers** at z 0 ± 0.2; after the bind, T's fit residual (< 0.5) and, posed by spec 08's transforms, the ankle axis height (report, ≈ 113); E1–H2 heights against §4.8's drawn table (report) and the stays' pitch; the outsole length 297 ± 2 and its widths against §3.1's derived values; the internal toe box at the hallux against 73.2 × 27.2 (report, S4); the **fold statistics** per boot (count, spacing and depth mean and coefficient of variation; CV ≥ 0.2; the left and right boots' fold sets differing by ≥ 3 mm in mean position); and, with the reference scans in (§3.6), `scan_ref_shaft_rms`, `scan_ref_collar_rms`, `scan_ref_toebox_rms`, `scan_ref_counter_rms`: the RMS distance of our outer sections from R1's at the stations of §3.6 (bands set on the first run, as part 01's were; R2's fold statistics side by side with ours).

### 8.4 Colour patches
The 16 targets of §5.6 as 5 × 5 means on the graded V1/V2 with ΔE (CIE76) printed; plus the stripe test: B − R at (700,880) minus B − R at (720,890) ≥ +10.

### 8.5 Questions the critic must answer (yes/no, naming the proving view)
1. Do the boots sit on the floor at the right scale: collar top y 795 ± 3, toe x 631 ± 4, heel x 767 ± 4 in V1? 
2. Does the right boot show its MEDIAL side with the lace ladder climbing from (690,858) to (720,800), the strap band across the quarter and a buckle behind the heel?
3. Does the left boot show seven lace crossings with alternating over/under, two hooks each side at the collar, and a knot at the top centre?
4. Is the sole three layers — black matte outsole edge, blue-grey semi-gloss midsole stripe, black rand — with lug teeth along the edge wrapping up the wall (V1, V7)?
5. Do the lugs form chevrons at 15 mm pitch in the forefoot, blocks at the heel with a heel breast, shallow bars in the arch, each with two sipes and worn grey tops (V3)?
6. Is the toe bumper a moulded cap with a raised lip and an oval emboss, scuffed at the front and dusty on top (V6)?
7. Is the leather grained, creased across the vamp and at the ankle break, polished dark on the quarters, dusty only on top (V4, V6, V7)?
8. Is every seam a real double stitch row at 3.4 mm pitch on a ridge, including the stays, counter, toe-cap seam and collar binding (V4, V5, V7)?
9. Are the eyelets 0.7 mm proud gunmetal rings with bright worn rims, the hooks real open hooks with the lace wrapped round them (V4)?
10. Is the strap 15 mm, under two keepers, through a ladder-lock at the back-lateral corner, with its tail folded and bar-tacked (V5)?
11. Is the collar a padded roll 22 × 10 with binding and an Achilles notch that a trouser cuff can rest on (V5, V7)?
12. Is the floor reflection smudge under each boot dark (lum 45–85) and the contact core black (V1, V2)?
13. Does anything look painted, floating, buried, hovering, mirrored wrongly or symmetric where the picture is not?

*2026-10-27 (§0 items 5, 8, 9).* These are scored 1–10 under spec 18's protocol (three critics, three lenses; pass at a median of 8 with nothing blocking; metrics first; packets by `scripts/eval/critic/packet.py`). Q2's "a buckle behind the heel" is a declared difference (§2.4 item 3). Added:
14. V8, V9 (clay, beside R1 if fetched): do the large forms read as a real worn boot (the shaft's taper and lean, the collar, the instep line, the domed toe box, the counter's bell over the heel from behind), not as an ellipse loft or a sock-like shell?
15. V4, V6, V7, V8: are the folds where a boot bends (along the metatarsal-head line and at the ankle break), uneven in spacing and depth, with a fold's profile (narrow valley, round shoulders), and are the toe box ahead of them and the rest of the upper free of noise-wobble?
16. All views: does anything read stamped from one template or perfectly even (fold rows, lace crossings, stitch rows, lug wear, dust), and do the two boots differ the way two worn boots do?
17. V3, V6, V9: is the wear where use puts it (lug edges by load, the heel's lateral back edge, the bumper's lip and toe front, the medial sides, the collar top, hook lips and eyelet rims), with edges rounded rather than crisp?

### 8.6 Known failure modes to check
| Failure | Symptom | Guard |
|---|---|---|
| Smooth sock-like upper | no panel edges, no creases | overlays with thickness (§4.5), crease GN, stitch rows; critic Q7–8 |
| Eyelets buried | rings invisible in V4 | Solidify sign assert on stays (bbox grows outward); flange proud 0.7 measured |
| Laces floating or cutting | gaps or penetration at crossings | ray tests §4.11 step 8 |
| Grey rubber | lugs read mid-grey | albedo 0.012, wear only on `N·−Z > 0.7`; swatch render first |
| Sparse lugs | gaps 6–8 mm, coverage < 50 % | coverage assert 55–65 % |
| Matte midsole | stripe not cooler than the outsole | B − R test §8.4; roughness 0.30 |
| Dust everywhere | shaft sides lighter than #30302e | `N·Z` gate, zone weights, `--dust` |
| Plastic leather | large specular blob on the toe box | roughness ≥ 0.36 even when polished, Coat only on `zone_polish`; highlight area ≤ 25 % |
| Wrong height | collar top off by > 3 px in V1 | measure h 212 on the mesh; camera verification overlay of the lighting note |
| Buckle on the wrong side or hidden | no protrusion behind the right heel | φ 150° check in V5 and V1 |
| Hooks hidden by the cuff | lower hook not visible in V1/V2 | interface §10.1 with spec 09: cuff edge ≥ h 192 |
| Mirror errors | right boot inside-out normals, laces inverted | `recalc_face_normals`, lace routing re-asserted on `Boot.R` |
| Hovering or sinking | lug tips not at z 0 | lowest-z assert ± 0.2 |
| Poly explosion | > 700 k faces the pair | budget table §4.13; `--lod bump` |
| Mechanical regularity (2026-10-27) | even fold rows, a laced zigzag of equal amplitude, identical boots, crisp bevels, noise-wobble everywhere | §4.15; fold statistics and L/R difference in `measure()`; critic Q15–Q17 |
| Large forms from scalars (2026-10-27) | the shaft an ellipse loft, the counter a box from behind, the toe box a smooth bulb | R1 sections (§3.6) and `scan_ref_*_rms`; V8, V9 beside the scan; critic Q14 |
| Boot off the foot (2026-10-27) | the boot floating and pitched toe-down in the hero, or the foot through the sole in rest | the bind of §7.1 (T residual < 0.5); ground markers on z 0 in the hero |

---

## 9. Build order, effort and risks

### 9.1 Dependencies
Needs: `Foot.L.Last` + markers (spec 01; stand-in otherwise), `Morgan.Rig` with `foot.*`, `ball.*`, `lowerleg02.*`, the eval harness camera/lights, `gn_stitches.py` (spec 09), `gear_webbing.py` / `gear_hardware.py` / `mat_fabric.py` / `mat_hard.py` (prototype recipes → `scripts/lib/`), assets `Leather032`, `Rubber004`, `Fabric063`, `Metal027`, `SurfaceImperfections015/017` (all in `assets/manifest.json`). Provides: `Boot.L/R.*`, `Boot.L/R.ShaftProxy`, the sole/lug/lace/eyelet helpers (reusable for nothing else on this character, but kept in `scripts/lib/`).

*2026-10-27 (§0 items 6, 7, 10), the state of what it needs.* **Ready:** spec 18's core library (`env`, `cli`, `naming`, `log`, `ctx`, `replace`, `cache`, `params`, `interfaces`, `measure`, `linmodel`, `optim`; spec 18 §4.13), spec 01's `sculpt.py`, spec 17's `render.py`, `camera.py`, `scene.py`, `lookdev.py`, `masks.py` (boot masks into `cache/masks/`) and `p02.json`, the rig with `foot.*`, `lowerleg02.*` (`cache/body/rigged.blend`), and every texture asset of §5 in the manifest. **Being built now:** `Foot.L/R.Last` and its markers (part 01, `scripts/parts/p01/last.py`). **Not built, needed here:** `modifiers.py`, `sweep.py`, `uv.py` (spec 18 §4.3), `gn_stitches.py` (spec 09), `gear_webbing.py`, `gear_hardware.py` (spec 13): part 02 builds them to spec 18 §4.3's signatures, each with its `selftest()`; spec 16's twelve boot recipes and seven groups (§5 note; `MG.GN.Crest` too if the crease attribute is not written by the part), built in its family modules. **Optional, Jeff's:** the reference scans R1–R2 (§3.6, Q17). The boot's private code is `scripts/parts/p02/` (spec 18 §10.2), not `scripts/lib/`, except the shared modules just named.

### 9.2 Order inside the script (idempotent: deletes `Part02.Boots` and `Boot.*` data blocks first; ≈ 9 min full run on 4 cores, ≈ 1 min with `--fast`)
1. Last load / stand-in, pitch, remesh, shaft loft — 3 s.
2. Sole outline, three lofts, heel breast, toe spring, bevels — 0.5 s.
3. Lugs, coverage assert — 0.5 s.
4. Upper shell, throat, Solidify, creases GN, zone groups — 2 s.
5. Overlays (stays, counter, backstrap), rand + bumper + lip + emboss — 2 s.
6. Collar roll, binding, tongue, gussets, pull loop, footbed — 1 s.
7. Hardware — 0.5 s. 8. Strap, keepers, buckle, tail — 0.5 s. 9. Laces, knot, bow, collision pass — 0.5 s.
10. Seams and stitches GN — 3 s. 11. Materials and UVs — 2 s.
12. Mask bakes (AO 64 spp + 4 EMIT bakes at 2048²) — ≈ 90 s per boot.
13. Mirror to `Boot.R`, rebind — 2 s. 14. Weights and armature — 1 s. 15. `ShaftProxy` — 1 s.
16. `measure_boot()` + BVH tests — 10 s. 17. Save `builds/02_boots.blend`; renders (§8.1) — ≈ 5 min.

### 9.3 Script size
`02_boots.py` ≈ 500 lines of orchestration; libs ≈ 1,400 lines (`boot_last` 150, `boot_sole` 350, `boot_upper` 400, `boot_hardware` 200, `boot_laces` 200, `boot_mats` 250, `measure_boot` 250).

*2026-10-27, re-estimated.* Part 01 was planned at 1,400–1,800 lines and three to four sessions; it stands at about 7,000 lines of part code and 7,800 of research code after 34 commits over 17 days, most of it spent on the realism loop. For the boot, with the foot's lessons applied from the start: **≈ 3,000 lines** in `02_boots.py` and `scripts/parts/p02/` (seat and shaft 250, sole and lugs 400, upper, throat and folds 550, overlays, rand and bumper 300, collar, tongue and gussets 200, hardware, strap and laces 500, wear fields 200, mirror, seeds, bind, weights and proxy 250, scan reference 200, `measure()` 300), **≈ 1,300** in the shared modules it must build first (`sweep` 350, `gn_stitches` 250, `gear_hardware` 250, `uv` 200, `modifiers` 150, `gear_webbing` 150), and **≈ 1,000** in spec 16's recipes and groups for the boot: about 5,300 lines in all. **Sessions on Jeff's workstation: about 8–12** (spec 18's table says 20 h; read that as the first pass only): 1 the shared modules and the seat, sole and lugs; 2–3 the upper, overlays, collar and tongue to a first clay round beside R1; 4 hardware, strap, laces, stitches; 5 materials (spec 16's recipes and groups) and wear; 6 mirror, seeds, bind, weights, proxy, measure, and the hero crops; 7–12 critic rounds (form, then look) and their fixes, which the foot shows to be the larger share. Build time per run ≈ 1–2 min without mask bakes on the GPU machine; a full `eval` set of the eighteen views (V1–V9 × 2) a few minutes.

### 9.4 Risks and fallbacks
| Risk | Likelihood | Mitigation |
|---|---|---|
| Spec 01's last is late or its shape differs from the stations here | medium | stand-in last from §4.1; the boot's sole and shaft are parametric, only the upper's remesh changes |
| Remesh + Displace shell shows faceting at the throat edge | medium | `Subdivision` 2 and boundary smoothing; fallback `Shrinkwrap` of a clean lofted shaft onto the shell |
| Solidify/Shrinkwrap sign traps (prototype §0) bury overlays or hardware | high if unchecked | bounding-box asserts after every Solidify |
| Lace curves self-intersect at the hooks | medium | explicit wrap points (3 per hook) and the ray test |
| Dust or rubber reads grey (albedo trap) | high | swatch render first; `--dust` multiplier; targets §5.6 checked numerically |
| The reference's two boot heights differ by 6 % | certain | one height (212); the critic scores the right boot's y positions, the left only by IoU |
| The buckle is hidden if the pose turns the right toe toward the camera | medium | §10.3 question 4; the keeper/tail still shows on the left boot |
| Trouser cuff hides the hooks | medium | interface rule cuff edge ≥ h 192 (§10.1) |
| Render budget blown by 560 k faces + stitches | low | `--lod bump`; stitches only in closeups |
| Bake of masks fails headless (needs real selection + active image node) | low | the bake helper from research_blender_capabilities §10 sets selection explicitly |
| *2026-10-27:* the real instep stands above the drawn vamp line (the scan's dorsum is ≈ 20 mm over the estimates) | medium | run spec 01's V6 (the last inside the drawn boot) first; if it pokes out, the vamp follows the foot (reality), the V1 IoU is read with the vamp band declared and E1–E3 stand higher (§1.4 items 1, 3) |
| *2026-10-27:* the large forms read modelled next to real boots | high (the foot's history) | §4.15; R1 as the section reference from the first clay round (Q17); V8, V9 |
| *2026-10-27:* the reference scans cannot be fetched by script (Sketchfab needs a login) | certain | Jeff downloads them into `assets/scans/boots/`; the build runs without them, its scan metrics reported as missing |
| *2026-10-27:* the shared modules (`sweep`, `gn_stitches`, `gear_*`, `uv`, `modifiers`) and the boot's material recipes do not exist | certain | build them first, to spec 18 §4.3 and spec 16, with self-tests; `form` iterations need none of the materials |
| *2026-10-27:* the bind leaves the game's rest pose with the boots below the floor | certain | expected (the rest foot is barefoot); spec 08 decides on a booted rest for the export (its dated note) |
| *2026-10-27:* part 01's last changes while the boot is built | medium | the seat, throat, eyelets and shaft are placed from the last's markers and surfaces, so a new last is a re-run; the part's cache key includes part 01's |

---

## 10. Interfaces and open questions

### 10.1 What neighbouring parts must provide or respect
| Part | Must provide | Must respect |
|---|---|---|
| Foot / sock (spec 01) | `Foot.L/R.Last` with the groups and markers of its §4.13; sock thickness under load 1.8 (already in the last) | our heel pitch rotation of 5.4° about the ball line: the last is fixed, we rotate our copy; the foot inside must be posed to match (§7.2) |
| Trousers (spec 09) | the cuff drapes on our collar; sim collider = our `Boot.L/R.ShaftProxy` (friction 30, rounded rim) | **collar rim at h 212 (sides) / 206 (notch) / 218 (stay tops), tongue top 222; rim outer ellipse 138 × 106 → circumference 385 (not Ø 140 = 440 as assumed); shaft ellipses 128 × 100 at h 110, 136 × 104 at h 158; the lower hook (h 189) must stay fully exposed → cuff edge ≥ h 192 on both legs (the picture shows y 803–810 = h 180–195 on the right: the lower part of that range hides H1; we ask spec 09 to keep the right cuff at h ≥ 192, within its 180–205 tolerance); the top hook (206) may be half hidden; no trouser geometry inside our rim** |
| Rig | `foot.*`, `ball.*`, `lowerleg02.*` with the names in `BONE_MAP`; `ball.*` placed on the MT-head line (spec 01) | our weight formulas (§7.1); no auto-weights on `Boot.*` |
| Pose | right heading 90° + 15–20° toe-away, left 15° toe-left, ankles (±208, ∓75, 80), plantar flexion 5.4° inside the boots | the right boot's medial side faces the camera; the buckle at φ 150° shows behind the right heel only with toe-away |
| Lighting / eval | hero camera and lights unchanged; the floor material (roughness 0.30) that makes the reflection smudges; the PIL overlay tool | our albedos are part of the floor-reflection calibration: finish the boots before the final light calibration (as spec 09 says of the trousers) |
| Body | the shin at h 212 must fit inside the rim's inner ellipse 118 × 86 (circumference ≈ 322) with the sock: spec 01 gives the min ankle circumference 236 at z 115 — fine | — |

*2026-10-27 (§0), the rows above as revised.*
| Part | Must provide | Must respect |
|---|---|---|
| Foot / sock (spec 01) | `Foot.L/R.Last` (289.3 long, toe spring 12°, collar z 210) with `.Pternion`, `.Ball1`, `.Ball5` on its insole plane, `.ToeTip`, `.AnkleAxis.*`; built from the rest foot under load with the sock at 1.8 under the sole | the boot seats its own copy on the real footbed (36 / 24, ≈ 4–4.5°, §4.1 step 2) and never cuts inside the last; spec 01's V6 and its §0 item 4 / §7.3 take the seats from spec 08's note, not the old 49 / 29 / 5.4° |
| Trousers (spec 09) | the hems stack on our collars, neither tucked nor bloused (its §2.4); sim collider = our posed `Boot.L/R.ShaftProxy` (friction 30, rounded rim) | rim h 212 sides / 206 notch / 218 stay tops (S1: 210 outside), tongue top 222; the rim an ellipse 138 × 106 (385), not Ø 140; H1 spans h 185–196, so the cuff edge stays ≥ 192 where it crosses H1 on both legs (its 180–205 band allows it); H2 may be half hidden; no trouser geometry inside our rim (dated note in spec 09 §10.1) |
| Rig (spec 08) | `foot.*`, `lowerleg02.*`; `ball.*`, `heel.*`, `toes_master.*` as its non-deforming helpers | the boot's weights (§7.1: rigid `foot.*` below h 110, the shaft ramp to `lowerleg02.*`); no auto-weights on `Boot.*`; the boot is bound under the rest foot by T |
| Pose (spec 08) | headings 85° right, 17° left; ankles (−208, +75) and (+208, −75) in plan; `foot.*` set so `Boot.*.Marker.Ground.*` lie on z 0 (the plantar flexion and the ankle height ≈ 113 are readbacks); `toes_master.*` 12° | the right boot's medial side faces the camera; the buckle at φ 150° does not show behind the right heel (declared) |
| Materials (spec 16) | the twelve recipes and seven groups of §5's note | the zones, side factors and targets this spec gives |
| Evaluation (spec 17) | `render.py`, `camera.py`, `LookDev`, `Hero`, `masks.py`'s boot recipe | `p02.json` is ours (V1–V9) |
| Leg rigs (spec 14) | — | nothing shared: the rigs end at the thighs |

### 10.2 What this part provides
`Boot.L/R.*` objects and materials; `Boot.L/R.ShaftProxy`; `renders/02_boots/measure.json`; the helpers `boot_sole.place_lugs` (any lug sole), `boot_laces.route_crisscross` (any laced item: the gloves' cuffs have none, so boots only), `boot_hardware.eyelet/speed_hook/ladder_lock` (the ladder-lock is reusable by the kneepad and belt specs), and the swatch procedure.

### 10.3 Open questions for the client
1. **Identity:** a generic boot with our panel layout (recommended; nothing in the picture is a readable brand), or a recognisable real model (Belleville Khyber / Lowa Zephyr) — which would import trade dress?
2. **Height:** follow the picture (rim 212 mm from the floor ≈ 6.5-inch shaft) or a true 8-inch (rim ≈ 235) as the analysts' label implies? The trousers' hem stack height depends on it.
3. **Lug pattern:** our Vibram-like chevron/block pattern, or a specific real sole?
4. **Strap buckle side:** posterior-lateral (our reading, §2.4) — or should the buckle sit where it shows best from the hero camera on each boot even though a real pair would not do that?
5. **Lace colour:** faded charcoal #4a473f as the picture, true black, or coyote brown (the sock of spec 01 is coyote)?
6. **Toe-bumper emboss:** plain oval, or a hexcom mark?
7. **Dust level:** medium as pictured (left dustier than right), or evened out / cleaner for a "fresh issue" look?
8. **Quarters:** leather (chosen) or nylon panels (Lowa-style)?
9. **Hidden parts:** lining, footbed, pull loop, lace tails and knot interior are built low-poly — keep, or drop for a lighter game export?
10. **Heel pitch:** accept 5.4° plantar flexion of the hidden foot inside the boot (true to real boots), or keep the foot flat and let the boot's footbed be flat (a 20 mm-thinner heel, less like the picture)?
11. **Eyelet metal:** gunmetal black-oxide brass (chosen) or bright steel/antique brass?
12. **Export:** laces as mesh (≈ 12 k tris per boot) in the game export, or baked to a normal map on the tongue?

*2026-10-27, status of Q1–Q12.* Q1 answered by `CLAUDE.md` (a Zephyr class boot, generic: our panel layout, no marks or trade dress). Q2 settled by the real boot (210 outside = the drawing). Q3 open, default our chevron-and-block pattern (not the X-TRAC MILITARY's own, nor its rope arch). Q4 replaced by Q16. Q5 settled by spec 16 D14 (black, greyed by dust and fuzz). Q6 open, default a plain oval. Q7 open, default as pictured (the left boot dustier). Q8 replaced by Q15. Q9 open, default keep them low-poly. Q10 settled: the foot stands on the real footbed (Jeff's Q7 of spec 01; seats from the real boot). Q11 settled by spec 16 (`Metal.Gunmetal`). Q12 open, default mesh laces.

*Added 2026-10-27* (each with the default the build follows until Jeff answers):

13. **Stature and the real footbed.** `CLAUDE.md` sets the rest stature at 1835 so that the posed skull top meets the drawing, "the footbeds add 42". The real boot's footbed (36 / 24) lifts the figure ≈ 33 mm, so at 1835 the skull top lands ≈ 9 mm (≈ 4 px) under the drawn line, at the edge of spec 08's ± 4 px. Keep 1835, or raise it to ≈ 1844 to keep your "match the drawing"? **Default: 1835, unchanged until you say** (the boot does not depend on it); the recommendation is 1844.
14. **Leather finish.** Smooth full-grain, as the drawing's highlights show, or the real Zephyr's black suede (1.4–1.6 mm, a nap that holds dust; it needs a new spec 16 recipe)? **Default: smooth full-grain.**
15. **Upper shaft.** Cordura 500D panels above the counter and behind the stays, as the Zephyr Hi has, or all leather (this spec's first reading)? **Default: Cordura panels.**
16. **The buckle.** At φ 150° (posterior-lateral, where real cuff straps put it; at spec 08's 85° heading it hides behind the right shaft, so the drawn box behind the right heel is not reproduced), or at φ ≈ 170°, beside the Achilles, where it pokes out ≈ 4 mm as drawn? **Default: φ 150°.**
17. **Reference scans.** Will you download R1 (the Garmont T8 scan, 69 MB source / 8 MB glTF) and R2 (the worn Danner TFX, 28 MB), and R4 (the LOWA Tibet, 36 MB) if you like, from Sketchfab (a login is needed; CC BY, credits in `deliver/`) into `assets/scans/boots/`, to drive the large forms and the folds as the foot's scans did? **Default: yes, as section and fold references; the build starts without them and adds the comparison when they arrive.**
18. **Forefoot flex.** The boot is rigid on `foot.*` (spec 08's `ball.*` does not deform, and the toe bones would double the toe spring in the hero). Should a later animation pass add a deforming flex bone at the metatarsal line (spec 08's), or stay rigid? **Default: rigid.**
19. **Anchor photographs.** Can you supply photographs of a real worn black 8-inch tactical boot (ideally a Zephyr Hi) for the critics' anchor (spec 18 §2.2)? **Default: none; the scans' clay renders are the reference half of the pairs.**

### 10.4 Items tagged [VERIFY]
* Leather thickness 2.2, eyelet flange/hole sizes, hook dimensions, thread pitch 7.5 spi, heel pitch 20 — standard values from general knowledge; `notes/research_dimensions.md` §2 has no row for them.
* `Leather032` grain cell size at the 250 mm tile — measure the normal map's feature size before fixing the tile.
* Lace length for 7 pairs (1500) — research gives 1600–1830 for 8–10 pairs.

*2026-10-27, status.* Leather thickness: **2.0** (S5; the Zephyr's suede 1.4–1.6, S3). Heel pitch: **settled**, drop 12.6 (S4), the pitch derived (§4.1). Lace length: **settled**, 1400–1600 for 7–8 pairs (S7). Hooks: a riveted speed hook's 10 mm cap, 6 mm post, 3 mm opening (S8) agree in scale; our plate hooks stand. Eyelet flange and hole: no source found; kept (E). Thread pitch 7.5 spi: kept (E). `Leather032`'s cell size: **settled** by spec 16 (78 cells a tile: 80 mm for 1.0 mm cells, C33). Still open: the X-TRAC MILITARY's tread geometry (no published figures beyond its 4.7 lug depth), the Zephyr Hi's eyelet and hook count (the drawing's 5 + 2 is kept), and the sidewall band heights at the heel (re-measure, §3.1).

Sources (read 2026-10-27):
* S1 tacwrk.com, LOWA ZEPHYR MK2 GTX HI Black: https://tacwrk.com/en/p/lowa-zephyr-mk2-gtx-hi-black-68153 (shaft 210 outside, 175 inside; 80 % leather, 20 % textile; injected PU on the MONOWRAP frame; X-TRAC MILITARY; closed hooks, lace garages, grip loops; insole ≈ 90 % PU, 9 % PA; its "1,55 kg" is not said to be a boot or a pair); the 625 g a boot quoted for the MK2 GTX Hi came from a search summary of us-elitegear.com / goodsports.com listings that could not be opened (HTTP 429) [VERIFY]
* S2 alpinstore.com, Zephyr MK2 GTX MID: https://www.alpinstore.com/en/626395-zephyr-mk2-gtx-mid-dark-brown-ref.html (110 inside, 145 outside; ≈ 570 g; double-injection DuraPU, MONOWRAP)
* S3 airsoftfenix.cz, LOWA Zephyr GTX Mid TF black: https://www.airsoftfenix.cz/en/lowa-zephyr-gtx-mid-tf-boots--black/ (hydrophobic suede 1.4–1.6 mm with Cordura; LOWA Cross sole, MONOWRAP; 1120 g a pair; 110 / 145)
* S4 RunRepeat, Lowa Zephyr GTX Mid lab test: https://www.runrepeat.com/lowa-zephyr-gtx-mid (heel stack 36.3 with the insole, forefoot 23.7, drop 12.6, lug depth 4.7, outsole 2.3 without lugs, insole 3.7, tongue 14.0, toe box 73.2 × 27.2 at the big toe, 601 g; the measuring stations are not stated)
* S5 Bureau of Indian Standards, draft QR and TDs of non-skid tactical/combat boots (2024): https://services.bis.gov.in/tmp/17321_18102024113035_14.docx (full-grain upper leather 2.0 ± 0.2 mm with nylon at the ankle and quarter; read from the search summary, the document itself not opened) [VERIFY]
* S6 Sport Conrad, LOWA size chart: https://www.sport-conrad.com/en/brands/lowa/size-chart/ (Mondopoint 25.2 at EU 40, 26.5 at EU 42, 27.7 at EU 44, 28.5 at EU 45)
* S7 Pear Shoelace, boot lace length guide: https://www.pearshoelace.com.au/shoelace-length-guide/boot-lace-length-guide.html
* S8 Weaver Leather Supply, 3/8" steel boot lace hook: https://www.weaverleathersupply.com/products/a-295-blk
* Scans R1–R5: §3.6.
