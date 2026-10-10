# Part 11 — Gloves (hard-knuckle tactical gloves, both hands)

Status: draft 1 (spec writer), 2026-10-07, written under the **reality wins** rule (`CLAUDE.md`, Source of truth). Owner script: `scripts/parts/11_gloves.py` (plus `scripts/lib/glove_pattern.py`, the shared `scripts/lib/stitch.py`, `scripts/lib/gear_hardware.py`, `scripts/lib/mat_fabric.py`, `scripts/lib/mat_hard.py`). Object prefix `Glove.<L|R>.*`; materials `Glove.Mat.*`.

Conventions (from `CLAUDE.md`): millimetres in this spec, metres in Blender; world origin on the floor midway between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT = viewer's right**. Every "left/right" is the soldier's own. This spec reuses spec 05's **hand frame H** (one per hand): origin at the centre of the carpus on the distal wrist crease; **d** = distal along the third metacarpal, **n** = dorsal (palm → back), **r** = radial (toward the thumb); coordinates (r, d, n); all hand tables are for the LEFT hand, the right is `mirror(r)` unless a row says otherwise. Pixel coordinates are in `ref/reference_full.png` (1672 × 941), 1 px ≈ 2.1 mm at the figure (`analysis_consolidated.md`, Agreed scale). Hex colours are display values under the hero lighting; **albedos** (the shader inputs) are stated separately and must be calibrated by rendering (research_prototypes §0).

Sources: `notes/analysis_consolidated.md` §1 Hands, §4 (Gloves row), §5 (forearm guards), §6 (weathering), §9 items 9 and 17; `notes/analysis_gear_inventory.md` §8 (gloves), §7 (forearm guards), §12 (weathering); `notes/analysis_pose_proportions.md` §7 (hands and rifle, finger angles); `notes/research_dimensions.md` §1d (ANSUR hand), §8 (Mechanix M-Pact), §12 (carbine); `notes/research_assets.md` (texture sets `Leather032`, `Leather037`, `Rubber004`, `cotton_jersey`, model `garden_gloves_01`); `notes/research_blender_capabilities.md` §5 (geometry nodes), §6 (shrinkwrap → solidify → bevel → subsurf stack, apply gotcha), §7 (rig, export), §10 (bakes); `notes/research_prototypes.md` §0 (sheen bleaches dark fabric; albedo by rendering), §3 (moulded cap recipe), §8 (stitch, buckle and polymer recipes); `spec/05_arm_hand.md` §2.1–§2.3, §3.4–§3.8, §4.8–§4.9, §7.1–§7.3, §7.6, §10.1 (the hand this glove is built on, the grips, the frames it provides); `spec/10_combat_shirt_gaiter.md` §3 cuff rows, §4.7 (the gauntlet stand-in it collides with). Own zooms made for this spec with PIL (gridded, Lanczos, full-image coordinates on the grid lines): `ref/zoom_glove_rknuckle_x12.png` (690–745 × 330–375), `ref/zoom_glove_rfingers_x10.png` (690–755 × 355–402), `ref/zoom_glove_rcuff_x12.png` (685–715 × 322–355), `ref/zoom_glove_lthumb_cuff_x10.png` (840–890 × 405–450), `ref/zoom_glove_ltips_x10.png` (798–840 × 448–500); sampling script in the session scratchpad, to be committed as `scripts/eval/sample_glove_ref.py` (§8.2).

---

## 1. Purpose and acceptance

### 1.1 What this part is
Both gloves, complete: the one-piece glove shell (goatskin palm trank and palmar finger faces, honeycomb-embossed stretch-knit back and fourchettes, set-in thumb, reinforced fingertip caps, double-layer heel-of-hand patch), the moulded ribbed TPR knuckle plate over the four MCP joints, the five TPR joint pads (PIP of the four fingers, IP of the thumb), the 45 mm neoprene gauntlet cuff with its bound edge, hook-and-loop closure tab with a moulded TPR pull, loop field and webbing pull loop, every seam with its stitch type, pitch and thread colour, the materials of leather, knit, TPR, neoprene, hook-and-loop, binding and thread, the dust, abrasion, polish and grime of a worn pair, the glove's skinning to the hand bones of `Morgan.Rig` so it follows the two hero grips without a poke-through of skin or rifle, and the evaluation renders that prove it. In the hero render the gloves are the **only visible part of the hands**: everything the viewer reads as "his hands" is this part. Not in this part: the bare hand and its hero finger poses (spec 05, which this glove wraps), the shirt cuff inside the gauntlet (spec 10), the forearm guards whose wrist bands overlap the gauntlet (spec 12), the rifle the gloves grip (spec 15).

### 1.2 What "perfect" looks like
At the hero distance (46 mm lens at 4.5 m, 2.1 mm/px) the right glove reads as a black, slightly warm, dusty hard-knuckle glove whose segmented knuckle plate catches the key on its ulnar bosses, whose index finger lies dead straight along the lower receiver and darkens into its shadow, whose three curled fingers show a lit pad over each PIP, and whose wrist vanishes under the tan forearm-guard band with no skin and no gap; the left glove reads as a cooler, shadowed back of a hand with a thumb lying across the top rail (one bright highlight at its tip), four rounded fingertips stacked under the handguard at 27 mm pitch and brightest at the index, and 25–30 mm of black neoprene gauntlet between the glove and the guard band. In a 160 mm-wide closeup a critic who owns a pair of M-Pact or SI Assault gloves recognises the pattern at once: the goat grain of the palm (0.5 mm pebble, pore rows), the 2.4 mm honeycomb of the back knit flattening where it stretches over the knuckles, the knit fourchettes between fingers, the fingertip caps with their U-shaped outside stitch row 1.5 mm from the edge, the knuckle plate as one moulded piece with four bosses and three ribs per boss, each rib with a lit crest and a dusty valley, its sewn flange visible as a 2.2 mm lockstitch row, the five joint pads as low domes on sewn flanges, the gauntlet's 10 mm bound edge, the hook tab crossing the dorsum with its chevron-moulded pull, the loop field's pile, the webbing pull loop at the palm side, polished leather on the finger pads where the rifle is held, dust only where dust settles, no logo. Nothing mitten-like, nothing balloon-like, no finger thicker than 23 mm, no seam without a stitch, no stitch floating in the air, no blue paint where the picture shows blue light.

### 1.3 Closeup render views (definitions for the render harness in §8.1)
Hand-frame views are defined in frame H of the LEFT hand (the right mirrored); the grip views are in world W with the character in `Hero.Pose` and the rifle placed.

| View | Camera position (mm) | Target (mm) | Lens / sensor | Compared with |
|---|---|---|---|---|
| V1 Right grip | W (−620, −1500, 1320) (spec 05 V1) | W (−200, −250, 1130) | 85 mm, 36 mm sensor, 2048² | `ref/crop_hands_rifle.png`, `ref/zoom_arm_rhand_grip_x8.png`, `ref/zoom_glove_rknuckle_x12.png`, `ref/zoom_glove_rfingers_x10.png`: knuckle plate facing camera, index straight along the receiver, three curled fingers with PIP pads, cuff under the guard band |
| V2 Left clamp | W (+320, −1400, 1080) (spec 05 V2) | W (+60, −330, 920) | 85 mm, 2048² | `ref/zoom_arm_lhand_clamp_x8.png`, `ref/zoom_glove_lthumb_cuff_x10.png`, `ref/zoom_glove_ltips_x10.png`: thumb across the rail with the tip-cap highlight at (850,445), four fingertips at (806,458) (812,470) (820,483) (828,495), gauntlet between glove and guard |
| V3 Knuckle plate macro | H (+40, +60, +380) | H (−5, 92, +15) | 100 mm, 2048², DOF f/8 on the middle boss | §3.3 plate table (bosses, rib count and pitch, flange, stitch row), §5.5 dust-on-crest targets; hand in rest with fingers at MCP 30° |
| V4 Cuff and closure | H (−120, −200, +300) | H (0, −25, +20) | 85 mm, 2048² | §3.5 cuff table: 45 mm gauntlet, binding, hook tab crossing the dorsum, TPR pull, loop field, pull loop, wrist seam, sleeve cuff disappearing inside |
| V5 Palm (hand open, off the rifle) | H (−40, −420, −380) (spec 05 V4) | H (0, 95, −8) | 70 mm, 2048² | §3.2 palm pattern: trank outline, heel patch, thumb trank seam, fourchettes, tip caps, polish zones on the finger pads, grip grime |
| V6 Hero arm crops | hero camera W (0, −4500, 600), 46 mm, cropped to (600,170)–(770,490) and (850,170)–(1000,490) at ×3 | — | as hero | `ref/crop_arm_right_viewerleft.png`, `ref/crop_arm_left_viewerright.png`: glove silhouette inside the hand boxes 690–752 × 325–400 and 803–882 × 420–497, cuff/guard junctions |
| V7 Fingertips under the handguard | W (+120, −900, 760) | W (+60, −330, 920) | 100 mm, 2048² | `ref/zoom_glove_ltips_x10.png`: tip caps, 27 mm pitch, lit-side gradient index → little, 0.3 mm clearance to the lower facet |

Each view is rendered once in the neutral look-dev scene (§8.1) for form and once under the hero lights for colour; V3–V5 additionally as Workbench matcap + cavity for the fast loop.

### 1.4 Pass criteria a critic can score (full list in §8.3)
1. `measure_glove()` (§8.2) within tolerance of §3: shell offsets per zone ±0.3 mm, gloved finger widths ±1 mm, plate 95 × 35 ± 1.5, rib pitch 7.0 ± 0.3, pad sizes ±1, cuff height 45 ± 2, cuff thickness 3.0 ± 0.3, binding 10 ± 1.
2. Silhouette: the gloved-hand masks in V6 reach IoU ≥ 0.85 against the reference hand boxes; the right index reads 9–10 px wide at rows 370–385; the left fingertip centroids within ±4 px of their reference pixels; the thumb-tip highlight within ±4 px of (850,445).
3. Clearance: no hand vertex outside the glove's inner surface (V7 statistics, `clearance_report()`), minimum skin-to-inner-face 0.2 mm, maximum air gap ≤ 3.0 mm dorsal / ≤ 1.5 palmar; no glove vertex inside `Rifle.Collider` (penetration 0), pulp-to-rifle 0.3 ± 0.3 mm at every contact finger.
4. Plate: one piece, four bosses on the four MCP apexes (+2 mm foam), three ribs per boss at 7 mm pitch, 1.4 mm proud, flange stitched; the index boss 5–7 mm lower (toward the camera/n) than the middle boss on the right hand because the index is extended.
5. Pads: five, over the PIPs and the thumb IP only (none on the DIPs), each a 3 mm dome on a sewn flange.
6. Seams: no panel border without its stitch type; outside stitches as geometry in V3–V5, V7 (thread Ø 0.33 mm, sunk 0.15 mm), pitch 2.2 (plates), 2.5 (caps, binding), 2.8 (overlock) ± 0.2; bar tacks at the tab root and the pull loop.
7. Materials: goat grain visible in V5 (0.5 mm pebble), honeycomb 2.4 mm across flats in V3 and flattened ≥ 35 % over the flexed PIPs, TPR matte with a shot-blast micro grain, neoprene dead matte, loop pile fuzzy at the rim; leather polish on the finger pads (roughness 0.28–0.32) and nowhere else.
8. Colour under the hero lights (5 × 5 means): right dorsum knit #57504b–#605a55; dusty plate crests #8f837c–#9c908a; index PP #4a4542 → tip #0a0a08; left thumb #564d4e, tip highlight #645b55 ± 8 per channel; cuff neoprene #2c2a2b in shadow, #444d5c where the cool fill reaches it (from the light, not the albedo).
9. Weathering: dust only where n·Ẑ > 0.3 in the hero pose and heaviest on rib crests and the right hand's ulnar bosses; polish only on the palmar pads; no uniform dirt wash; the left glove 30 % less dusty (it is shaded).
10. Deformation: the glove follows every finger through the hero grips without a crease artefact, a candy-wrapper wrist or a floating plate; the plate bends between the index and middle bosses (index extended, middle flexed) by 15–25° without a kink.
11. Critic's free judgement (0–2): "would a Mechanix or Oakley wearer recognise this glove, and would a rifleman believe this grip?"

---

## 2. Reference observations

### 2.1 What the image shows about this part
| Feature | Pixels (full image) | Reading | Source |
|---|---|---|---|
| Right glove box | 690–752 × 325–400 (62 × 75 px ≈ 130 × 158 mm projected) | back of the hand faces the camera and up-left; forearm pronated 70°, wrist extension 12°, ulnar deviation 10° | consolidated §1 Hands, pose §7 |
| Right knuckle plate | 698–735 × 343–365 (37 × 22 px ≈ 78 × 46 mm projected) | a raised quadrilateral panel with three horizontal rib lines (pitch 3–4 px ≈ 7 mm) and four rounded bosses; the ulnar bosses at (709,353) and (701,356) are dusty-bright, the index boss at (727,352) darker and lower (the index is extended) | my `zoom_glove_rknuckle_x12.png`, `zoom_arm_rhand_grip_x8.png` |
| Plate radial/thumb-web edge | dark channel from (700,340) to (712,366) | the plate's radial end and the knit valley toward the thumb web; the thumb itself is hidden behind the grip | my zoom |
| Right index finger | MCP (727,355) → tip (750,398); width 9–10 px at rows 370–385 | gloved width 19–21 mm (bare 18 + 2 × 1.2–1.5 glove) ✓; PIP pad highlight at (740,377); the finger darkens from #4b4642 (PP) to #090907 (tip) as it enters the receiver's shadow → it is in contact with the receiver | spec 05 §2.1, my samples |
| Right curled fingers | PPs from (712,370) (704,380) (697,388), running down-right | middle, ring, little MCPs 8–9 px apart = 17–18 mm pitch (adducted, tight); a lit PIP pad on each at (714,388) region | pose §7 |
| Right cuff | (690–712, 325–350) | the glove's wrist disappears under the forearm guard's wrist band (685–700 × ...) — the light strip at (700–712, 333–345) #41362f is the **shirt cuff hem** between glove and band, not glove | gear §7, spec 10 §2 D9 |
| Left glove box | 803–882 × 420–497 (79 × 77 px ≈ 158 × 154 mm) | palm on the top/his-left handguard facets, forearm semi-pronated 40° arriving at 45° | consolidated §1 |
| Left thumb | thenar bulge (880,428) → tip (846,447); MCP ≈ (866,436) | a dark blue-grey cylinder across the rail, a bright highlight along its upper edge, brightest at (850,445) #645b55 | my `zoom_glove_lthumb_cuff_x10.png` |
| Left fingertips | (806,458) (812,470) (820,483) (828,495); bright runs 8–10 px wide | four rounded caps stacked along the handguard at 12.3 px = 24.5 mm image pitch → 27 mm true (handguard foreshortening 0.904); lit from the upper left, brightest at the index (#534c47) and darkening ulnar-wards (#342d29, #22211f, #23201f) | my `zoom_glove_ltips_x10.png`, spec 05 §2.1 |
| Left gauntlet | (865–885, 410–440), 30 px ≈ 63 mm projected along a 45° forearm | neoprene band between the glove's dorsal edge and the guard's wrist band (tan from x ≈ 885); colour #2c2a2b in shadow to #444d5c where the cool fill reaches it; a lighter strip at (872–880, 428–436) = the closure tab's free end | my zoom, gear §8 |
| Left dorsum | (835–860, 436–456) | almost black (#211d1b–#2a2726): shaded by the handguard; the back texture is not resolvable at 2.1 mm/px | my samples |
| Weathering | knuckle crests #8f837c–#9c908a, finger pads with a soft sheen highlight | pale dust on up-facing crests; polished leather on the pads; no visible tears, no logos, no colour patches | gear §12 |

### 2.2 My own colour samples (5 × 5 means on `reference_full.png`) [measured]
| Right glove | px | hex | Left glove | px | hex |
|---|---|---|---|---|---|
| Plate, index boss | (727,352) | #4f4a47 | Thumb across the rail | (860,436) | #564d4e |
| Plate, middle boss | (718,352) | #504d4a | Thumb tip highlight ("stud") | (850,445) | #645b55 |
| Plate, ring boss (dusty crest) | (709,353) | #9c908a | Thumb MCP / cuff junction | (868,434) | #444d5c |
| Plate, little boss | (701,356) | #7e746d | Dorsum, lit edge | (840,440) | #2a2726 |
| Plate upper (proximal) edge | (715,343) | #44403d | Dorsum, shaded | (850,452) | #211d1b |
| Dorsum knit proximal of the plate | (705,340) / (698,345) | #57544e / #57504b | Cuff neoprene, shadow | (872,425) | #2c2a2b |
| Index PP dorsal | (735,368) | #4b4642 | Cuff, upper (guard band beyond) | (878,415) / (890,418) | #64584b / #685b4e |
| Index PIP pad | (740,377) | #2b2624 | Tip index | (806,458) | #534c47 |
| Index MP / tip | (744,386) / (749,396) | #211f1e / #090907 | Tip middle | (812,470) | #342d29 |
| Middle PP / PIP pad | (720,378) / (714,388) | #161615 / #0f100d | Tip ring | (820,483) | #22211f |
| Ring PP / little PP | (708,385) / (700,392) | #0b0b0b / #251e1a | Tip little | (828,495) | #23201f |
| Ulnar edge of the hand | (694,365) | #5b5049 | Finger underside, shaded | (815,476) | #3d3732 |
| Shadow under the fingers | (725,398) | #110e0a | Tip index, lit rim | (804,455) | #443b37 |

Luminance profile down the plate at x = 712 (rows 338–372): 66 → 115 (proximal rim) → 157 (first crest, y 355) → 24 (groove, y 359) → 147 (second crest, y 361) → 102 → 38; the crest/groove alternation at 3–4 px is the rib structure. Across the plate at y = 352: peaks at x 700, 703, 707, 710, 718, 725 — the boss crowns and rib ends. Reading: the plate is lit by the key from the upper viewer's-left, so its crests are highlights plus dust, its grooves hold shadow; the index boss is ~0.5 stop darker than the ring boss although it faces the camera more squarely, i.e. the dust is on the up-facing (ulnar, with 70° pronation and ulnar deviation) bosses, which is where dust settles on a hand that hangs at a grip all day.

### 2.3 Ambiguities, contradictions and decisions (reality wins)
| # | Question | Image says | Reality says | Decision |
|---|---|---|---|---|
| D1 | Glove identity | hard-knuckle glove with a ribbed segmented plate, joint pads, knit back, short cuff | Mechanix M-Pact 3 (one-piece ribbed TPR knuckle guard, TPR PIP pads, TrekDry stretch back, synthetic-leather palm, hook-and-loop wrist) and Oakley SI Assault (carbon-fibre knuckle shell, **goatskin** palm, spandex back, **neoprene cuff**) are the two real patterns | **Hybrid built from real parts:** SI Assault-type pattern and materials (goatskin palm, neoprene cuff) with an M-Pact 3-type ribbed TPR plate and pads (the image's ribs are unmistakable and a carbon shell has none). Image wins on the plate, reality on everything it cannot show |
| D2 | Knuckle plate size | 78 × 46 mm projected (plate seen obliquely, bosses foreshortened) | M-Pact 3 guard ≈ 95 wide × 35 tall × 6 thick [sourced, research §8; height uncited → estimated] | **95 × 35 × 6**, following the metacarpal-head arc; the projection check in V6 must reproduce 37 × 22 px |
| D3 | Rib count and pitch | three crest/groove cycles over ≈ 26 mm of plate | M-Pact 3 segments carry three moulded ridges each | **3 ribs per boss, 7.0 mm pitch**, rib 3.0 wide × 1.4 proud |
| D4 | Thumb length | 95 mm projected from (880,428) to (846,447) | gloved thumb 61 mm from the MCP axis (bare 58 + 2.5 ease) | the proximal point is the thenar, not the MCP (spec 05 §2.3 c); **real length**, the tip registered at (846,447) |
| D5 | "Bright stud" at (850,445) | a point highlight on the thumb tip | no tactical glove carries a metal stud on a thumb tip; it is the specular of the smooth tip cap curving over the rail edge | **tip-reinforcement cap** (0.6 mm synthetic leather, satin) — the highlight must appear from the shading, not from a modelled stud |
| D6 | Cuff colour | #444d5c, distinctly blue | neoprene is black; the blue is the cool fill from the hangar (consolidated §8) | albedo neutral black (#1c1d20 equivalent, albedo 0.02); **never tint the cuff blue** |
| D7 | Gauntlet height | 63 mm projected along a 45° forearm (spec 10 read this as "60 mm shows") | SI Assault neoprene cuff ≈ 45 mm, M-Pact 3 cuff ≈ 50 mm from the wrist seam [estimated] | **45 mm** (d −5 → −50); on the left ≈ 28 mm is visible between glove and guard band once the band (d −11 … −38) overlaps it; the full-figure overlay accepts the residual |
| D8 | Back texture | not resolvable | TrekDry is plain; honeycomb-embossed stretch knits exist on several hard-knuckle gloves (HWI, Oakley Factory Pilot class) [VERIFY name in the critique pass] | **honeycomb emboss 2.4 mm across flats** on a stretch knit (the analysts' "carbon/honeycomb" kept; plausible; it is what makes the back read as a tactical glove in closeup) |
| D9 | Plate: one piece or four | continuous lit panel with groove lines | M-Pact 3: one moulded piece | **one piece**, four bosses joined by 2.5 mm webs |
| D10 | Joint pads | highlight at each PIP of the right hand, none at the DIPs | M-Pact 3: PIP pads only; thumb pad over the IP | **five pads** (PIP × 4, thumb IP) |
| D11 | Palm | not visible; gear note "assume suede-grey" | SI Assault palm is black top-grain goatskin with a double-layer heel patch and a foam pad | **black goatskin**, grain side out; the gear note is overruled |
| D12 | Finger widths | index 19–21 mm | bare 20 × 17 + 2 × (1.0 air + 1.2 knit) dorsal / 2 × (0.5 + 0.9) palmar → 22.5 wide | **22.5**, within the image's tolerance at 2.1 mm/px |
| D13 | Dust distribution | ulnar bosses brightest on the right hand; left glove dark | dust settles on up-facing surfaces; the right hand's ulnar side faces up in the 70° pronated grip; the left glove sits in the handguard's shadow | image wins (physically consistent): dust mask by n·Ẑ in the hero pose, left glove 30 % weaker |
| D14 | The lighter strip at (872–880, 428–436) on the left cuff | a paler band on the gauntlet | a hook tab's free end stands 1 mm proud and catches the fill | **closure tab free end on the dorsal-radial side**, visible there |
| D15 | Glove size | hand box 130 × 158 mm projected | ANSUR hand 201 long, breadth 91, palm girth 218 → Mechanix **L** (palm 8.5–9.8 in = 216–249 mm); 218 is at the small end of L, so the glove fits snug (small ease) [sourced size chart; the chart's finger-length unit is unclear — VERIFY] | size L, ease 1.0 dorsal / 0.5 palmar / 0 at the pulps (spec 05 §3.7) |
| D16 | Logos and patches | none resolvable | real gloves carry a brand on the pull and an ID label inside | **no brand**; the TPR pull carries a chevron emboss, the inside label is not modelled |

---

## 3. Real-world reference

### 3.1 The hand inside (from spec 05 §3.4–§3.5; the glove is a skin over it)
| Quantity | Bare (mm) | Gloved (mm) | Mark | Note |
|---|---|---|---|---|
| Hand length, distal wrist crease → middle tip | 193 | 195.5 | sourced / estimated | glove finger ease +2.5 at every tip |
| Hand breadth at the MC heads | 91 | 95.8 | sourced | + 2 × 2.4 (palm/back offsets, §4.3) |
| Hand circumference at the MC heads | 218 | 232 | sourced | + 2π × 2.3 (mean offset) |
| Wrist w × t / circumference at the axis | 62 × 42 / 179 | gauntlet inner 201, outer 220 | sourced | 3.5 mm air (over the shirt cuff, spec 10 §3) + 3.0 neoprene |
| Thumb, MCP axis → tip (chain 31 + 27) | 58 | 60.5 | estimated | |
| Index, MCP axis → tip (40 + 24 + 24) | 88 | 90.5 | estimated | |
| Middle (44 + 27 + 26) | 97 | 99.5 | estimated | |
| Ring (41 + 26 + 25) | 92 | 94.5 | estimated | |
| Little (34 + 20 + 23) | 77 | 79.5 | estimated | |
| Interdigital webs | d 110–113 (2/3, 3/4), d 100 (4/5) | the fourchettes start 2 mm distal of the web | estimated | |
| First web (thumb–index) | 50 mm fold MCP1 → MCP2 | thumb trank seam runs along it | estimated | |
| Dorsal knuckle apex (each MCP) | axis + (0, +3, +7) | plate underside = apex + 2.2 (glove) + 2.0 (foam) | estimated | |

Gloved finger circumferences (ellipse perimeters from spec 05 §3.5 plus the glove: +2π × 1.7 at the PP/MP, +2π × 1.85 at the DP where the tip cap adds 0.6) [estimated]:

| Digit | PP bare → gloved | MP bare → gloved | DP bare → gloved | Gloved width × thickness at the PP |
|---|---|---|---|---|
| Thumb | 69 → 80 | — | 57 → 69 | 26.5 × 23.4 |
| Index | 58 → 69 | 52 → 63 | 44 → 56 | 22.5 × 20.4 |
| Middle | 61 → 72 | 55 → 66 | 47 → 59 | 23.5 × 21.4 |
| Ring | 58 → 69 | 52 → 63 | 44 → 56 | 22.5 × 20.4 |
| Little | 50 → 61 | 44 → 55 | 39 → 51 | 19.5 × 18.4 |

(Width adds 2 × 1.2 knit + 2 × 0 side ease; thickness adds 2.2 dorsal + 1.2 palmar.) Fingertip caps add 0.6 on the palmar and side faces of the distal 22 mm.

### 3.2 Pattern pieces (left glove; sizes are cut dimensions including the 3 mm seam allowance where sewn) [estimated from the hand, construction sourced from the SI Assault / M-Pact patterns]
| Piece | Material | Count | Size (mm) | Position in H | Edges |
|---|---|---|---|---|---|
| Palm trank | goatskin 0.9 | 1 | 96 wide at the MC-head line × 118 long (d −5 → d 113 at the webs), extended as four palmar finger faces to each tip | palmar face, n ≤ 0 side from r −48 to +43, thumb hole at (+42, 50) | inseam to the back trank around the hand's side; inseam to the fourchettes; thumb-trank seam around the thumb hole |
| Palm foam | EVA 1.0 | 1 | 80 × 60, the MC-head pad zone d 85–115, r −40 … +35, plus 40 × 35 at the heel of hand (d 10–45, r −40 … −5) | between leather and lining | bonded, no stitch |
| Heel patch | goatskin 0.9 (second layer) | 1 | 48 × 42 rounded, over the hypothenar d 5–47, r −45 … +3 | palmar | outside lockstitch 2.5 mm pitch, 2 mm from the edge |
| Back trank | honeycomb knit 1.2 | 1 | 96 × 118 as the palm, extended as four dorsal finger faces | dorsal | inseam to the palm; the plate and pads sewn on through it |
| Fourchettes | honeycomb knit 1.2 | 8 (two per finger) | width 0.75 × finger thickness at the PP tapering to 0.6 × at the DP: index 13 → 9, middle 13.5 → 10, ring 13 → 9, little 11 → 8; length from the web + 2 to the tip cap edge | the sides of each finger, r ± | inseam both edges, 3-thread overlock 2.8 mm pitch |
| Thumb trank (palmar) | goatskin 0.9 | 1 | wraps the thumb's palmar and radial faces, 60.5 long from the MCP line + the thenar gusset to the thumb hole | thumb | inseam to the dorsal thumb piece and to the palm hole |
| Thumb back | honeycomb knit 1.2 | 1 | the thumb's dorsal face, 26 wide at the MCP → 20 at the IP | thumb | inseam |
| Tip caps | synthetic leather 0.6 (satin finish) | 5 | distal 22 mm of each digit, palmar + side faces, U-shaped free edge | d tip − 22 → tip | outside lockstitch 2.5 mm pitch, 1.5 mm from the U edge |
| Wrist elastic band | 20 mm elastic 1.5 | 1 | 190 long sewn in a ring at d −5 under the cuff seam | d −8 … −2 | overlock to the trank and cuff |
| Gauntlet cuff | neoprene 3.0 (nylon-faced both sides) | 1 | 45 tall (d −5 → −50), inner girth 201 at d −5 flaring to 207 at d −50, one 15 mm overlap slit on the ulnar-dorsal side closed by the tab | wrist/forearm | bound edge; wrist seam overlock |
| Cuff binding | nylon grosgrain tape 1.0, folded | 1 | 10 mm visible each side, 232 long around the proximal edge + 60 up the slit | cuff edge | lockstitch 2.5 mm pitch, 2 mm from the inner edge |
| Hook tab | hook tape 25 wide, 1.6 thick, on a 1.0 nylon backing | 1 | 25 × 70, root sewn at the ulnar-dorsal slit edge, free end toward the radial side | across the dorsum of the cuff | box-X stitch at the root 25 × 20, bar tacks 8 mm at both root corners |
| TPR pull on the tab | TPR 2.5 | 1 | 25 × 30 rounded, three moulded chevrons 1.0 proud at 6 mm pitch, no logo | the tab's free end | sewn through 2 holes rows, 2.2 mm pitch |
| Loop field | loop tape 1.8 | 1 | 30 × 55 on the radial-dorsal cuff face | d −12 … −42 | lockstitch perimeter 2.5 mm pitch |
| Pull loop | nylon webbing 10 wide × 1.0 | 1 | 65 long folded to a 30 mm loop | palmar cuff edge at r 0 | bar tack 8 mm through the binding |
| Lining | none (SI Assault is unlined); the palm foam is faced with 0.3 mm tricot | — | — | — | not modelled |

### 3.3 Knuckle plate and joint pads [estimated against the M-Pact 3; the 95 × 35 × 6 envelope sourced per research §8]
| Element | Dimension (mm) | Detail |
|---|---|---|
| Plate footprint | 95 along the MC-head arc × 35 (d 80–115 at the middle boss), corners R 6 | the long axis follows the arc through the four MCP apexes (d 93, 95, 88, 79 at r +25, +3, −17, −36 for MCP2–5), so it is not straight: it curves 8 mm ulnar-proximal |
| Bosses | 4; each 20 (r) × 26 (d) rounded, crown 4.0 above the flange plane; centres on the apexes | boss spacing = MCP pitch 20–22 mm (index–middle 22, middle–ring 20, ring–little 20) |
| Webs between bosses | 2.5 thick, 8 wide, saddle 1.5 lower than the crowns | they let the plate bend between fingers |
| Ribs | 3 per boss, transverse (across r), pitch 7.0, rib 3.0 wide × 1.4 proud, groove 4.0 wide with R 0.6 fillets; the middle rib on the boss crown | the lit crests of §2.2 |
| Foam under the plate | 2.0 EVA, footprint = plate − 3 mm | sets the plate 2 mm off the knit |
| Sewing flange | 4.0 wide × 1.2 thick around the perimeter, stitched 1.5 mm inside its edge | lockstitch 2.2 mm pitch, thread black |
| Total height above the knit at the crowns | 2 (foam) + 1.2 (flange) + 4.0 (boss) + 1.4 (rib) = 8.6 | the "knuckle plate 95 × 35 × 6" of spec 05 is the moulding alone |
| PIP pads (index, middle) | 16 (d) × 11 (r) × 3.0 dome, edge fillet R 1.5, one central transverse groove 1.0 wide × 0.6 deep | flange 1.5 wide, lockstitch 2.2 |
| PIP pad (ring) | 15 × 10 × 3.0 | same |
| PIP pad (little) | 13 × 9 × 2.5 | same |
| Thumb IP pad | 15 × 12 × 3.0 | same |
| Pad centres | on each PIP dorsum + 1 mm distal (the dome sits over the joint when flexed 85°) | PIP2 (+29, 133), PIP3 (+3, 139), PIP4 (−20, 129), PIP5 (−41, 113), IP1 (+81, 78) |

### 3.4 Materials, construction and wear (real)
| Material | Where | Thickness | Surface | Wear behaviour |
|---|---|---|---|---|
| Goatskin, drum-dyed black, light finish | palm trank, thumb trank, heel patch | 0.9 | pebbled grain 0.4–0.7 mm, pore pairs in rows ≈ 0.25 mm apart, satin sheen (roughness 0.45–0.52) | polishes where it rubs (roughness → 0.28, dye wears to warm grey-brown #3d3836), creases at the palmar PIP/MCP into 3–4 folds 1.5 mm pitch, grip grime (carbon, oil) darkens the thumb web and the MC-head line |
| Stretch knit, polyester/elastane, honeycomb emboss | back trank, fourchettes, thumb back | 1.2 | hexagonal cells 2.4 across flats, walls 0.4, relief 0.25; yarn 0.3 mm visible in the cell floors; matte (0.7) with a faint yarn sheen | pills on the knuckle webs, flattens where stretched over a flexed joint (relief −40 %), fades 6 % on crests, holds dust in the cell floors |
| TPR (thermoplastic rubber, Shore A 60–70) | knuckle plate, five pads, tab pull | 2.5–8.6 | shot-blast micro grain 0.05 mm (noise 600/m), dead matte (0.55–0.6) | scuffs on rib crests (grey streaks), dust in grooves and on up-facing crests, no chips (rubber does not chip) |
| EVA foam | under the plate, palm | 1.0–2.0 | hidden | — |
| Neoprene 3 mm, nylon-faced | gauntlet | 3.0 | fine tricot face 0.15 mm, matte 0.8 | fuzzed at the bound edge, dust on the dorsal top, slight salt bloom none (hangar) |
| Nylon grosgrain binding | cuff edge, slit | 1.0 | fine ribs 0.5 mm across the tape, satin 0.45 | abrasion lightening at the fold |
| Hook tape / loop tape | tab / field | 1.6 / 1.8 | hooks 0.35 mm as a bump field; loop pile 1 mm fuzz | lint in the hooks |
| Bonded nylon thread Tex 70 | all visible stitching | Ø 0.33 | black #1a1917, sheen 0.10 | sun-greyed to #2e2b28 on the dorsum |
| Nylon webbing 10 mm | pull loop | 1.0 | herringbone 1.5 mm rib | — |

Construction order of the real glove (why the seams lie where they do): the palm and back tranks are cut mirror-alike and joined inseam around the hand's side and the fingers with the fourchettes between them; the thumb is set in through the palm's thumb hole; the tip caps are top-stitched on after the finger seams; the plate, pads and heel patch are sewn through the single fabric layer onto the turned glove; the elastic ring and the neoprene cuff are overlocked to the wrist edge last, then the binding, tab, loop field and pull loop are stitched to the cuff. The glove's visible stitching is therefore only: cap U-rows, plate and pad flanges, heel-patch perimeter, binding, tab box-X, loop-field perimeter, pull-loop bar tack — exactly the stitches §4.8 generates.

---

## 4. Geometry construction plan

Inputs: `Body.Mesh` (rest, spec 03/05), `Body.Mesh.Posed` and `Hand.L/R.GloveLast` (spec 05 §4.9; hero keys), `Morgan.Rig` with `Hero.Pose`, `Hand.L/R.PalmFrame`, `Arm.L/R.CuffRing` (185 at d −30), `measure_hand()` JSON (landmarks of §3.4 in H), `Rifle.Collider`, `Rifle.GripFrame`, `Rifle.HandguardFrame` (spec 15 [VERIFY names]); texture sets from `assets/` per `research_assets.md`. All steps are idempotent: the script deletes every object, material and image whose name starts with `Glove.` before rebuilding. Build in **rest pose** in frame H, skin by transferred weights, then verify in `Hero.Pose` (steps 10–12). Left glove built, right glove = mirror in X of the rest-pose shell before skinning, with the right-hand asymmetries of spec 05 §4.4 respected automatically because the shrinkwrap targets the right hand itself.

### 4.1 Step 1 — Hand region copy (`glove_pattern.py::copy_hand_region(side)`)
bmesh: select the faces of `Body.Mesh` whose vertices lie distal of d −60 in frame H (the wrist region down to the fingertips; the `hand_*` and `wrist_*` vertex groups of spec 05 §4.3), duplicate into a new mesh `Glove.L.Shell` (MPFB hand topology ≈ 1 300 quads, with the extra joint loops of spec 05 §4.7), delete the nail faces' inner geometry (`Hand.L.Nail.*` are separate objects, so nothing to delete; the nail bed depression is flattened by the shrinkwrap offset). Cap the open proximal ring at d −60 and dissolve the cap (the ring stays open: the cuff object closes it). Origin at H origin; parent none (the Armature does the work). Shade smooth, auto-smooth 40°. Rejected alternative: `garden_gloves_01` (tris, one object for both gloves, unposed, research_assets) — retopo would cost more than the copy and lose the hand's loops.

### 4.2 Step 2 — Zone vertex groups (`glove_pattern.py::make_zones()`), analytic in H, weights 1 with a 2 mm falloff at borders
| Group | Definition |
|---|---|
| `Glove.Zone.Palm` | n < 0 side of the hand's silhouette plane (the rest-space sign of n relative to the local mid-plane, as spec 05's `hand_palm`), d ≥ −5, excluding the thumb |
| `Glove.Zone.Back` | n ≥ 0 side, d ≥ −5, excluding fourchettes |
| `Glove.Zone.Fourchette.2r/2u … 5r/5u` | finger side faces: on each finger, vertices within ±0.375 × finger thickness of the finger's mid-plane (n = 0 in the finger's own frame) and distal of the web + 2 |
| `Glove.Zone.Thumb.Palm` / `.Back` | the thumb's palmar-radial / dorsal-ulnar halves from the thenar fold to the tip |
| `Glove.Zone.TipCap.1–5` | distal 22 mm of each digit, palmar and side faces (n_f < +0.3 × t) |
| `Glove.Zone.HeelPatch` | ellipse 48 × 42 at (−21, 26) on the palm |
| `Glove.Zone.PalmFoam` | the foam footprints of §3.2 |
| `Glove.Zone.Pulp.2–5`, `.Pulp.1` | the palmar pads of the distal phalanges (spec 05 `hand_pulp_N`) |
| `Glove.Zone.Wrist` | d −8 … −2 (elastic band) |
| `Glove.Zone.Contact.R` / `.L` | all palmar and side faces of the digits plus the palm (the rifle push-out mask, step 11) |
| `Glove.Seam.*` | edge loops along each zone border, as vertex groups on the border vertices (used by the stitch generator and the seam groove) |
Material indices are set from the zones: 0 leather (Palm, Thumb.Palm, HeelPatch), 1 knit (Back, Fourchettes, Thumb.Back), 2 tip cap, 3 elastic.

### 4.3 Step 3 — Per-zone shrinkwrap offsets (the fit)
Modifier chain on `Glove.L.Shell`, each `Shrinkwrap` with `wrap_method = 'NEAREST_SURFACEPOINT'`, `target = Body.Mesh`, `vertex_group` = the zone, so each zone's vertices are pushed to the hand surface plus its own offset (the groups partition the mesh; falloffs blend the borders):

| Zone | Air gap | Material | Outer-surface offset (mm) |
|---|---|---|---|
| Back, Thumb.Back | 1.0 | 1.2 knit | **2.2** |
| Fourchettes | 0.3 | 1.2 | **1.5** |
| Palm (no foam) | 0.5 | 0.9 leather | **1.4** → rounded to 1.5 |
| Palm over foam, HeelPatch | 0.5 | 0.9 + 1.0 foam (+ 0.9 patch) | **2.4** (heel 3.3) |
| Pulps and TipCaps (palmar/side) | 0 | 0.9 + 0.6 cap | **1.5** |
| TipCap dorsal part (cap wraps 3 mm over the nail) | 1.0 | 1.2 + 0.6 | 2.8 |
| Wrist band | 0.5 | 1.5 elastic | 2.0 |
Then `Solidify` (`offset = −1`, i.e. inward from the outer surface, `use_even_offset`, `thickness_vertex_group = Glove.Thick` where the group's weight scales a 2.4 mm base thickness to 1.2 (knit), 0.9 (leather), 1.5 (cap), 1.9 (palm + foam) — the inner face is then the air-gap surface), rim on. Research_blender_capabilities §6 proved this stack (shrinkwrap → solidify → bevel → subsurf) and its headless apply; capture modifier names before applying (gotcha). The normals must point outward before Solidify (prototypes §0: the offset sign follows the normal).

### 4.4 Step 4 — Panel steps, seams and the cuff ring (`glove_pattern.py::seams()`)
* **Panel steps**: `Displace` modifiers along normals with the zone groups: `TipCap` +0.6 with a 1 mm falloff (the cap's edge is a visible 0.6 mm step), `HeelPatch` +0.9, foam zones already in the offsets.
* **Inseams** (palm/back perimeter, fourchettes, thumb): a 0.4 mm-deep, 1.2 mm-wide groove along each `Glove.Seam.*` loop (Displace −0.4 on the border group with a 0.6 mm falloff). No visible thread.
* **Outside stitches** are generated in step 8 along `Glove.Seam.TipCap.*`, `Glove.Seam.HeelPatch`, and the plate/pad flanges.
* **Proximal ring**: the shell ends at d −5 in a 20 mm elastic band (Zone.Wrist, material 3, a 1.0 mm-pitch rib bump); its last edge loop is `Glove.Ring.Wrist.L` (64 vertices after a `bmesh.ops.subdivide_edges` to that count), the cuff's sewing line.
* Apply the chain (shrinkwraps, solidify, displaces) into the mesh so that the Armature deforms a static shell; keep `Bevel` (0.3 mm, 2 segments, angle 50°, on the rim and seam-groove edges only via a bevel weight) and `Subdivision` (viewport 1, render 2) live.

### 4.5 Step 5 — Knuckle plate (`Glove.L.KnucklePlate`; recipe = research_prototypes §8 "moulded polymer caps", without paint)
1. **Base curve**: a 2D spline through the four MCP apexes (H, from `measure_hand()`), extended 12 mm beyond MCP2 and MCP5, offset to a rounded-rect outline 95 × 35, corner R 6 (`glove_pattern.py::plate_outline()`).
2. **Loft**: 48 (along) × 20 (across) grid; height field z(u, v) = flange 1.2 within 4 mm of the outline, else the boss profile: four super-ellipse domes (exponent 2.6) 20 × 26 × 4.0 at the apexes, blended with the 2.5 mm web by `smooth_max(k = 1.5)`; ribs added as `1.4 × smoothstep` bands 3.0 wide at d-offsets −7, 0, +7 from each boss centre, running across r, with R 0.6 fillets by a second smoothstep; the central groove floors are 0.2 mm lower than the web for shadow.
3. **Underside**: the grid's base is shrinkwrapped (`NEAREST_SURFACEPOINT`, offset 2.0 for the foam) onto the applied `Glove.L.Shell` so the plate conforms to the knuckle arc; `Solidify` 1.2 at the flange only (`thickness_vertex_group`), the bosses are solid lofts closed to the base; `Bevel` 0.8 mm / 3 segments / 35°; `Subdivision` render 2; `Weighted Normal`. Evaluated ≈ 6 k faces.
4. **Foam** `Glove.L.PlateFoam`: the outline inset 3 mm, lofted 2.0 thick between knit and plate (it shows as a dark edge under the flange in V3).
5. **Flange stitch row**: `Glove.Seam.PlateFlange.L` = the outline inset 1.5 mm, consumed by step 8 at 2.2 mm pitch.
6. Right plate: built on the right shell with the same code (the index boss sits 5–7 mm lower in n when posed, from the hand itself).

### 4.6 Step 6 — Joint pads (`Glove.L.Pad.Index/Middle/Ring/Little/Thumb`)
Each a rounded-rect super-ellipse dome (sizes §3.3) lofted 16 × 12, edge fillet R 1.5 by the loft profile, a 1.0 × 0.6 transverse groove across the crown; `Solidify` 1.2 at the 1.5 mm flange; shrinkwrapped (offset 0) onto the shell at the PIP dorsum + 1 mm distal, oriented with the finger's local frame (long axis along d_f); `Bevel` 0.5 / 2; `Subdivision` render 2; ≈ 1.2 k faces each. Flange stitch loop `Glove.Seam.Pad.N.L` at 0.8 mm inside the edge, 2.2 mm pitch.

### 4.7 Step 7 — Cuff, binding, closure, pull loop (`Glove.L.Cuff`, `.CuffBinding`, `.HookTab`, `.TabPull`, `.LoopField`, `.PullLoop`)
1. **Cuff**: a loft of 64 × 10 rings from `Glove.Ring.Wrist.L` (d −5) to d −50; section = the forearm's section at each d (spec 05 §3.3 girths 179 → 185) offset +3.5 inner (`Arm.L.CuffRing` 185 at d −30 lies inside with 1.5 mm to spare over the shirt cuff's 215 → 200 closed girth, spec 10 §3: the gauntlet inner face is body + 3.5 as spec 10 asks); `Solidify` 3.0 outward, even, rim; a 15 mm slit on the ulnar-dorsal side (clock 7 in the anatomical frame) from d −50 to d −20 as an overlap (the ulnar flap under, the dorsal flap over by 15 mm); `Bevel` 0.6 / 2 on the rim; `Subdivision` 1. The proximal edge is slightly flared (+3 % girth) so the sleeve enters without a pinch.
2. **Binding**: a 10 mm strip along the proximal rim and the slit edges, folded over the edge (two faces 10 wide joined by a 3 mm radius fold), `Solidify` 1.0, grosgrain material; stitch loop 2 mm inside the strip's inner edge both faces, 2.5 mm pitch.
3. **Hook tab**: strip 25 × 70 × 1.6 + 1.0 backing, following the cuff surface from the slit's ulnar flap root across the dorsum toward the radial side (shrinkwrapped at +0.5 mm over the cuff, +1.6 over the loop field), its free end at clock 2 (radial-dorsal) so it reads at (872–880, 428–436) on the left hand (D14); root box-X stitch 25 × 20 at 2.5 pitch, bar tacks 8 × 3 mm at both root corners.
4. **Tab pull**: TPR 25 × 30 × 2.5 rounded (R 5) with three chevrons 1.0 proud at 6 mm pitch (bmesh ridges + `Bevel` 0.4), bonded to the tab's last 30 mm; a 2.2 mm-pitch stitch row through its root.
5. **Loop field**: 30 × 55 × 1.8 patch on the radial-dorsal cuff face (clock 1–3, d −12 … −42), perimeter stitch 2.5 pitch; loop pile by material (bump + optional fuzz, §6).
6. **Pull loop**: webbing 10 × 1.0 through the binding at the palmar rim (clock 12), a 30 mm loop lying flat along the forearm (−d), ends folded 10 mm, bar tack 8 mm; built with `gear_webbing.py` (prototypes §8, segment every 1 mm, Solidify 1.0, Bevel 0.4).
7. **Wrist seam**: the cuff's distal ring is coincident with `Glove.Ring.Wrist.L`; a 3-thread overlock is suggested by a 1.6 mm proud, 3 mm wide ridge (the seam allowance under the cuff turns outward — Displace +1.6 on a 3 mm band of the cuff at d −5 … −8) with a zigzag stitch 2.8 mm pitch generated by step 8 (`Glove.Seam.Wrist.L`).

### 4.8 Step 8 — Stitches, bar tacks, box-X (`scripts/lib/stitch.py::stitch_along(curve_or_vgroup, pitch, gap, radius, sink)`, shared with specs 09/10/13)
For every `Glove.Seam.*` loop with an outside stitch: resample the loop at the pitch, place a 6-sided thread cylinder of radius 0.165 mm (Tex 70) and length pitch − 0.6 (the 0.6 mm is the needle hole where the thread dives), sunk 0.15 mm into the surface along the local normal, slightly bowed (+0.1 mm at mid-length), with a 0.3 mm-wide, 0.1 mm-deep needle dimple at each end (Displace by a baked dimple mask, or ignore at hero LOD). Pitches: plate and pad flanges and the pull root 2.2; caps, heel patch, binding, loop field, box-X 2.5; overlock zigzag at the wrist 2.8 (zigzag amplitude 3 mm). Bar tack: 8 × 3 mm, 1.3 mm-pitch zigzag. All stitches of a glove in one object `Glove.L.Stitches` (≈ 1 100 stitches × 24 tris ≈ 26 k tris), bar tacks and box-X in `Glove.L.Bartacks`; material `Glove.Mat.Thread`. `--stitches bump` replaces them with a baked stitch bump (hero LOD).

### 4.9 Step 9 — UVs and bakes (`glove_pattern.py::unwrap()`)
Mark seams on the shell along every `Glove.Seam.*` loop plus the finger undersides (hidden), `bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.004)` under `temp_override`, pack both gloves' shells into one 2048² `Glove.Masks.png` layout (palm, back, fingers, thumb, cuff: texel density ≈ 8 px/mm, enough for colour and masks; micro-structure comes from tiled detail textures at 40–60 px/mm, §5.2). Bake per glove: `Glove.L.AO.png` (ambient occlusion with the hand present, for grime and the plate's underside shadow), `Glove.L.Curv.png` (Pointiness/Bevel-node edge mask, prototypes §3 c: Pointiness is weak on lofts, so use the Bevel node radius 0.6 mm and bake), `Glove.L.UpMask.png` (n·Ẑ in the hero pose, for dust), `Glove.L.Stretch.png` (step 10). Plates, pads and the cuff carry their own unwrap in the same atlas.

### 4.10 Step 10 — Skinning and the stretch attribute (`glove_pattern.py::skin()`)
* `Data Transfer` modifier from `Body.Mesh` → `Glove.L.Shell`, `Glove.L.Cuff` (vertex groups, `POLYINTERP_NEAREST`, all layers), applied; weights normalised, ≤ 4 influences (game export); the cuff's proximal ring re-weighted 0.7 `lowerarm02.L` / 0.3 `wrist.L` (spec 05 §7.2 wrist blend) so it twists with the pronation ramp. `Armature` (`Morgan.Rig`) → `Corrective Smooth` (factor 0.5, 5 iterations, pin boundary) → the pose-space clearance pass (step 11) → `Subdivision`.
* `Glove.L.KnucklePlate` and `Glove.L.PlateFoam`: `Surface Deform` bound to the applied shell in rest (they ride the knuckles and bend between bosses); `Glove.L.Pad.*`: parented to the finger bone of their PIP's proximal phalanx (`finger2-2.L` … `finger5-2.L`, thumb `finger1-2.L`, spec 05 §7.1 names) with a `Surface Deform` fallback if the parent-only solution lifts off the knit by > 0.5 mm in the hero pose.
* Cuff parts (binding, tab, pull, loop field, pull loop): `Surface Deform` bound to the cuff.
* **Stretch attribute** (Geometry Nodes on the shell, evaluated after the Armature): for each face, the ratio of posed to rest area (`Face Area` on the evaluated mesh versus a stored rest area attribute written by Python) → `Store Named Attribute` "stretch" (FLOAT, FACE); the knit shader reads it to flatten the honeycomb bump (§5.2) and the leather shader to add palmar compression folds where stretch < 0.85 (research §5 and §10b proved the node path headless). Baked to `Glove.L.Stretch.png` for Workbench/EEVEE and export.

### 4.11 Step 11 — Pose-space clearance and the rifle push-out
After the Armature on both shells: `Shrinkwrap` (`wrap_mode = 'OUTSIDE'`, target `Body.Mesh.Posed`, offset = the zone air gap − 0.2, vertex group per zone as in step 3) repairs any skin poke-through from weight-interpolation differences at the knuckles; then `Shrinkwrap` (`wrap_mode = 'OUTSIDE'`, target `Rifle.Collider`, offset **0.3 mm**, vertex group `Glove.Zone.Contact.*`) pushes any glove vertex that the contact solve left inside the rifle back to 0.3 mm outside it. Both are cheap and live (they re-evaluate when the pose changes). Requirement on spec 05 (§10.1): `grip.py::close_finger()` must take `contact_offset` per finger = the glove's pulp thickness **1.5 mm** (palm 2.4, dorsal 2.2 where a knuckle touches), so the bare pulp stops 1.8 mm from the rifle and the gloved pulp 0.3 mm — otherwise the push-out stretches the finger caps by the full 1.5 mm and the pads flatten.

### 4.12 Step 12 — Right glove, hero check, exports
Mirror the rest-pose zone definitions in r for the right hand and run steps 1–11 on `Body.Mesh`'s right hand (the right hand's own asymmetries are inherited); render V1–V7 and run §8.2; write `renders/11_gloves/report.json`; export `Glove.L/R.Game` (shell + cuff + plate + pads joined, Subdivision 1 applied, stitches as bump, ≈ 12 k tris per glove, one 2048 atlas) for the game pipeline (spec 18 [VERIFY]), scaled by 1800/1855 with the body.

### 4.13 Poly budget and object list (per glove; closeup LOD / hero LOD / game LOD)
| Object | Base faces | Evaluated (render) | Notes |
|---|---|---|---|
| `Glove.L.Shell` | ≈ 2 700 quads (hand copy 1 300 × solidify 2 + rim) | 43 k (Subdivision 2) / 11 k / 5 k | one mesh, 4 material slots |
| `Glove.L.KnucklePlate` + `.PlateFoam` | 960 + 320 | 15 k / 4 k / 1.5 k | |
| `Glove.L.Pad.1–5` | 5 × 192 | 5 × 3 k / 5 × 0.8 k / 5 × 0.2 k | |
| `Glove.L.Cuff` | 640 + slit | 5 k / 2.6 k / 1.3 k | |
| `Glove.L.CuffBinding`, `.HookTab`, `.TabPull`, `.LoopField`, `.PullLoop` | ≈ 1 400 | 6 k / 3 k / 1 k | |
| `Glove.L.Stitches`, `.Bartacks` | ≈ 26 k tris | 26 k / 0 (bump) / 0 | dropped at hero/game LOD |
| **Total per glove** | | **≈ 110 k / 26 k / 12 k tris** | both gloves ≤ 220 k tris in the closeup scene |

---

## 5. Materials and textures

All materials are Principled BSDF node groups in `scripts/lib/mat_fabric.py` / `mat_hard.py` (spec 16 materials library [VERIFY number]), `displacement_method = 'BUMP'` except the leather grain on V5 (`'DISPLACEMENT'` with adaptive subdivision when `--adaptive`), sheen weights per the prototype lesson (never above 0.12 on anything dark), albedos **calibrated by rendering the four-sphere swatch under the evaluation lighting** before acceptance (prototypes §0). Projection: UV for everything on the shell (Object/Generated coordinates stripe on curved fingers, prototypes §3 e); `BOX` blend 0.2 for the plates and cuff detail tiles.

### 5.1 Principled values (base; weathering in §5.4 modulates them)
| Material | Base colour (albedo, linear) | Target hex under the hero lights | Roughness | Specular IOR level | Sheen | Other |
|---|---|---|---|---|---|---|
| `Glove.Mat.Leather` (goatskin) | (0.028, 0.025, 0.023) | #2a2624 lit, #0b0a09 shadow; polished pads #3d3836 | 0.50 base; grain-floor 0.58 / grain-crest 0.44 by the grain map; worn 0.28–0.32 | 0.5 | 0.04 | coat weight 0.08, coat roughness 0.25 on the polished zones only (the "shiny worn pads") |
| `Glove.Mat.Knit` (honeycomb stretch) | (0.036, 0.033, 0.030) | #57504b–#605a55 lit dorsum (R), #211d1b shaded (L) | 0.72 cell floor, 0.62 cell walls | 0.4 | 0.08 (yarn fuzz) | subsurface 0 |
| `Glove.Mat.TPR` (plate, pads, pull) | (0.022, 0.021, 0.020) | #4f4a47 undusted boss, #9c908a dusty crest | 0.56 + micro grain noise 600/m × 0.06 | 0.45 | 0 | no metallic; scuffs lower roughness to 0.40 |
| `Glove.Mat.Neoprene` | (0.020, 0.020, 0.021) | #2c2a2b shadow; #444d5c only under the cool fill | 0.80 | 0.35 | 0.06 | tricot face bump 0.15 mm, pitch 0.3 |
| `Glove.Mat.Binding` (grosgrain) | (0.030, 0.028, 0.026) | #3a3634 | 0.45 | 0.5 | 0.06 | rib bump 0.5 mm pitch across the tape |
| `Glove.Mat.Hook` | (0.025, 0.024, 0.023) | #312e2c | 0.55 | 0.45 | 0 | hook bump field: Voronoi F1 2.8 mm/0.35 mm cells, 0.3 mm |
| `Glove.Mat.Loop` | (0.028, 0.026, 0.024) | #353130 | 0.85 | 0.3 | 0.12 | pile fuzz optional (§6) |
| `Glove.Mat.Thread` | (0.13, 0.12, 0.11) | #1a1917 new, #2e2b28 sun-greyed | 0.60 | 0.5 | 0.10 | prototypes §8 thread values |
| `Glove.Mat.Webbing` (pull loop) | (0.030, 0.028, 0.026) | #302d2b | 0.70 | 0.4 | 0.06 | herringbone bump 1.5 mm |
| `Glove.Mat.Elastic` (wrist band) | (0.026, 0.025, 0.024) | #2b2826 | 0.78 | 0.35 | 0.05 | rib bump 1.0 mm pitch along d |
| `Glove.Mat.Foam` (visible foam edge) | (0.020, 0.019, 0.018) | #1d1b1a | 0.90 | 0.3 | 0 | cell noise 0.3 mm |

### 5.2 Micro-structure: maps, tiles and bump chains
| Layer | Source | Scale | Strength | Where |
|---|---|---|---|---|
| Goat grain | `Leather037` normal + roughness (photo set, research_assets) tinted to the base colour; grain period re-scaled to **0.6 mm** (tile 45 cm → UV scale so 1 tile = 60 mm on the glove) | 0.6 mm pebble, pore rows 0.25 | bump 0.12 mm (displacement 0.12 on V5) | Palm, Thumb.Palm, HeelPatch |
| Leather creases (compression folds) | procedural: 3–4 bands 1.5 mm pitch, wave texture along r_f, masked to the palmar PIP/MCP 10 mm zones × (1 − stretch) | 1.5 mm pitch | 0.4 mm bump | palmar finger faces, flexed digits only |
| Honeycomb emboss | **generated tile** `assets/generated/glove_honeycomb_h.png` 512² (python3 -I + PIL: hex lattice 2.4 mm across flats, wall 0.4, floor at 0, wall at 1 with a 0.15 mm radius shoulder; 12 mm tile = 5 cells across → 43 px/mm) + a yarn tile (`cotton_jersey` normal re-scaled to 0.3 mm loops) in the cell floors | 2.4 mm cells | bump 0.25 mm × (0.6 + 0.4 × clamp(stretch, 0, 1)) — flattens 40 % at stretch 0 | Back, Fourchettes, Thumb.Back |
| Knit pilling | Voronoi F1 cells 1.2 mm, threshold 0.9, 0.2 mm | sparse | bump + roughness +0.1 | knuckle webs, cuff edge |
| TPR shot-blast grain | noise 600/m (≈ 0.05 mm) | 0.05 mm | bump 0.03 mm | plates, pads, pull |
| Neoprene face | `cotton_jersey` normal at 0.3 mm | 0.3 mm | bump 0.08 mm | cuff |
| Stitch dimples (hero LOD) | baked from `Glove.L.Stitches` to `Glove.L.StitchBump.png` (2048, Cycles emission-normal bake of the stitches' footprint) | per stitch | bump 0.15 mm | all outside seams when `--stitches bump` |
| Seam grooves (inseams) | geometry (step 4) | 1.2 wide | — | panel borders |

Texel density: `Glove.Masks.png` / AO / Curv / UpMask / Stretch at 2048² over both gloves ≈ 8 px/mm (colour and masks only); detail tiles 40–60 px/mm; a 160 mm hand filling 2048 px is 12.8 px/mm on screen, so masks are sampled at ≤ 1.6 screen px per texel and the tiles above screen resolution — no texture pixelation at V3–V5, V7.

### 5.3 UV layout
One atlas per pair: shell islands cut on the seam loops (palm trank, back trank, 8 fourchettes, thumb palm, thumb back, 5 caps as islands continuous with their finger faces but split on the cap seam, wrist band), cuff (one island with the slit), plate (top and flange), pads, binding, tab, pull, loop field, webbing. Island scale equalised (`bpy.ops.uv.average_islands_scale`), margin 4 px. The honeycomb tile is oriented so one hexagon axis runs along d on the back trank (as on a real knit's wale direction) — a `Mapping` rotation per island is avoided by orienting the islands in the pack (`rotate = False`, islands pre-rotated in Python).

### 5.4 Weathering masks (`Glove.L.Masks.png`: R dust, G polish, B grime, A abrasion) — baked once from the procedural definitions
| Mask | Definition | Effect | Target |
|---|---|---|---|
| Dust (R) | `UpMask` (n·Ẑ in the hero pose, clamp 0.3–1 → 0–1) × `Curv` crest term (×1.6 on rib crests and boss crowns, ×0.4 in grooves) × noise 25 mm (0.6–1.0) × hand factor (R 1.0, L 0.7) | mix toward dust colour (0.42, 0.37, 0.33) up to 55 % on the plate crests, 25 % on the knit, 10 % on the leather; roughness +0.15 | plate crests #8f837c–#9c908a (R), knit #57504b; L plate ≤ #5a5350 |
| Polish (G) | pulps 2–5 and thumb (×1.0), palmar MP faces (×0.7), palm MC-head line d 95–115 (×0.6), right thumb web (×0.8); soft 4 mm edges | roughness → 0.28–0.32, coat 0.08, colour toward (0.045, 0.040, 0.037) (dye worn to grey-brown) | pads #3d3836 in the lit closeup; the "shiny worn finger pads" of the analysts |
| Grime (B) | AO × 0.5 + palm contact zones of the grip (right: thenar, MC-head line, index radial side; left: palm centre, finger pulps) × noise 8 mm | colour ×0.6, roughness −0.05 (oil) | hidden in the hero; visible in V5 |
| Abrasion (A) | `Curv` edge term on the knit's knuckle webs, the cuff binding fold, the tab edge; the index finger's radial side (rides the receiver) | knit: colour +8 % lighter, roughness +0.1, pilling on; leather: polish; binding: colour +10 % | subtle |
| Scuffs on TPR | anisotropic noise streaks (Mapping scale 1, 1, 14, noise 180, threshold 0.68–0.72, prototypes §3) on rib crests | roughness 0.40, colour +15 % grey | a few per boss |
| Thread sun-greying | UpMask × 0.6 | thread colour → #2e2b28 | dorsal stitches |

No tears, no holes, no salt stains, no paint (the gloves are black rubber and cloth; nothing chips). The left glove gets the same masks at 0.7 dust and the mirror of the grip zones.

### 5.5 Hex targets (5 × 5 means in the hero-lit render, AgX, matched at the same pixels as §2.2)
| Pixel | Target | Tolerance |
|---|---|---|
| (709,353) ring boss crest | #9c908a | ±10 per channel |
| (701,356) little boss | #7e746d | ±10 |
| (727,352) index boss | #4f4a47 | ±8 |
| (698,345) dorsum knit | #57504b | ±8 |
| (735,368) index PP | #4b4642 | ±8 |
| (749,396) index tip (in the receiver's shadow) | #090907 | ±5 |
| (740,377) index PIP pad | #2b2624 | ±8 |
| (860,436) left thumb | #564d4e | ±8 |
| (850,445) thumb tip highlight | #645b55 | ±10, and it must be the local maximum within 4 px |
| (806,458) / (812,470) / (820,483) / (828,495) | #534c47 / #342d29 / #22211f / #23201f | ±8, monotone darkening index → ring |
| (872,425) cuff shadow / (868,434) cuff under fill | #2c2a2b / #444d5c | ±8; the blue must vanish when the fill is switched off (scene check) |

---

## 6. Fibres, simulation or dynamics
* **No cloth simulation.** The glove is a tight skin; every fold it has is a compression fold at a flexed joint, and those come from the stretch attribute (§4.10, §5.2) and the Corrective Smooth, not from a sim. The sleeve cuff (spec 10) collides with the gauntlet stand-in (a 45 mm tube at body + 3.5 inner, + 6.5 outer); this part provides the real cuff as `Glove.L/R.Cuff` for spec 10's final sim pass.
* **Knit fuzz** (`--fuzz`, look-dev and V3/V4 only): hair curves (`bpy.data.hair_curves`, the proven Curves route) on the knit zones, 250 fibres/cm², length 0.4–0.9 mm, radius 0.010 root → 0.004 tip, 25° random lean, colour = the knit base ×1.3; on the loop field 120/cm², length 1.0–1.4 mm, radius 0.012 (the pile); on the cuff binding fold 60/cm², 0.6 mm. Principled Hair BSDF, melanin 0.9 (near-black). About 60 k fibres per glove at the closeup; dropped at the hero LOD, where a sheen 0.08 stands in for the rim-light glow.
* **Leather**: no fibres; the grain and polish are shader.
* **Dynamics**: none. The gloves are static in the hero pose; the Armature and the two OUTSIDE shrinkwraps are the only pose-time evaluation.

---

## 7. Rigging and attachment
* **No bones of its own.** `Morgan.Rig` (MPFB default names, spec 05 §7.1: `wrist.L`, `metacarpal1..4.L`, `finger1-1..5-3.L`, `lowerarm02.L`) drives the shell and cuff through weights transferred from `Body.Mesh` (step 10); ≤ 4 influences per vertex; the `Hand.Corr.Grip.R` / `Hand.Corr.Clamp.L` corrective keys of spec 05 are inherited by the glove through a `Surface Deform` option (`--follow-correctives`: bind the shell to `Body.Mesh` instead of transferring weights; slower, exact). Default: transferred weights + Corrective Smooth, verified by the clearance pass.
* **Modifier order** (shell): [applied: Shrinkwraps, Solidify, Displaces] → `Armature` → `Corrective Smooth` → `Shrinkwrap OUTSIDE (Body.Mesh.Posed)` → `Shrinkwrap OUTSIDE (Rifle.Collider, Contact group)` → `GeometryNodes Stretch` → `Bevel` → `Subdivision`. Cuff: `Armature` → `Corrective Smooth` → `Bevel` → `Subdivision`. Plate/foam: `Surface Deform (Shell)` → `Bevel` → `Subdivision` → `Weighted Normal`. Pads: bone parent (`finger*-2.L`) → `Bevel` → `Subdivision`. Cuff parts: `Surface Deform (Cuff)`.
* **Hero pose**: `build_all.py` runs spec 05's `grip.py` with `contact_offset` per finger (§4.11), sets `Hero.Pose` frame 1, then builds or re-evaluates the gloves; the gloves never move the hands — if a glove vertex needs more than 1.5 mm of push-out against the rifle, the script warns and the hand pose is wrong (spec 05 §4.8 tolerance logic).
* **Game rig**: the same bones; `Glove.L/R.Game` carries the transferred weights; the plate and pads are joined into the game mesh with their weights copied from the nearest shell faces (`Data Transfer` before the join).
* **Attachments provided**: `Glove.L/R.Cuff` (collider for spec 10), `Glove.L/R.GauntletRing.Outer` (the outer girth curve at d −30, for spec 12's wrist band: inner radius = this + 1.0 mm), `Glove.L/R.ContactReport.json` (per-finger gloved pulp distances to the rifle), `Glove.L/R.Game`.

---

## 8. Evaluation protocol

### 8.1 Renders (`scripts/eval/render_part11.py`, the shared harness)
Look-dev scene A: neutral grey HDRI 0.5 + a 10 W area key at 0.4 m for the hand-frame views (research §6: scale light power with distance²), AgX Base Contrast, 800² × 48 spp (20–40 s) for the loop, 2048² × 128 spp for acceptance; Workbench matcap + cavity variants of V3–V5 for the 5 s form loop. Hero scene: the consolidated §8 camera (0, −4500, 600), 46 mm, lights as spec 17 [VERIFY], for V1, V2, V6, V7 and the colour targets. Outputs `renders/11_gloves/V1..V7_{form,hero}.png`, plus `V3_cavity.png`, `V5_cavity.png`; the latest acceptance set is copied to `renders/eval/11_gloves_*.png`.

### 8.2 Metrics (`scripts/lib/measure.py::measure_glove(side)`, `clearance_report()`, `eval/overlay.py`, `scripts/eval/sample_glove_ref.py`)
* `measure_glove()`: shell offset per zone (nearest distance from the glove's outer surface to `Body.Mesh` at 200 sample points per zone: mean and range, targets §4.3 ±0.3); gloved finger widths and thicknesses at the PP/MP/DP mids (§3.1 ±1); plate footprint (longest chord, width), rib pitch (crest spacing on the three-rib profile across each boss), boss heights; pad sizes; cuff height, thickness, inner girth at d −5 and −50; binding width; tab length; stitch pitch by nearest-neighbour distance in `Glove.L.Stitches` (±0.2).
* `clearance_report()` (hero pose): per zone the min/mean/max of skin-to-inner-face distance (min ≥ 0.2, dorsal max ≤ 3.0, palmar ≤ 1.5); count of hand vertices outside the glove (must be 0); per finger the gloved pulp-to-rifle distance (0.3 ± 0.3) and the maximum glove penetration into `Rifle.Collider` (0); plate-to-knit gap at the flange (≤ 0.3); pad lift-off (≤ 0.5); thumb-tip highlight position in V2 (local luminance maximum within 4 px of (850,445) after the hero render is mapped to reference pixels).
* `overlay.py` (shared with spec 05): the hero render over `reference_full.png` ×4 in the hand boxes; IoU of the gloved-hand masks ≥ 0.85; fingertip centroid errors ±4 px; index width in px at rows 370–385 (target 9–10); the knuckle-plate footprint pixels (698–735 × 343–365 ± 3).
* `sample_glove_ref.py`: the §2.2 / §5.5 sample table re-run on the render and the reference side by side; reports ΔE and per-channel differences, the luminance ordering of the four left tips, the crest/groove alternation down x = 712 (at least two crest–groove cycles with contrast ≥ 0.6 stop).

### 8.3 Critic questions (score 0–2 each; 32 max; ≥ 26 passes)
1. Is it recognisably a hard-knuckle tactical glove of the M-Pact / SI Assault class, not a work glove, a mitten or a superhero gauntlet? 2. Does the knuckle plate read as one moulded piece with four bosses and three ribs each, sewn on, sitting 2 mm proud on foam? 3. Do the five pads sit over the PIPs (and the thumb IP) and nowhere else? 4. Do the fingers have the right widths (22–23 mm) and lengths, with knit fourchettes visible between them? 5. Are the tip caps there, with their U stitch row, and is the thumb-tip highlight a specular on the cap? 6. Does the palm show goat grain and polished pads in V5? 7. Does the honeycomb read at 2.4 mm and flatten over flexed knuckles? 8. Is every visible seam stitched, at a believable pitch, with no floating thread? 9. Is the gauntlet 45 mm of matte black neoprene with a bound edge, a tab crossing the dorsum, a TPR pull, a loop field and a pull loop? 10. Does the sleeve cuff vanish inside the gauntlet and the guard band overlap it, with no skin and no gap on either wrist? 11. Right grip: index dead straight along the receiver and in contact, three fingers closed on the grip with lit PIP pads, plate facing the camera with the index boss lower? 12. Left clamp: thumb across the rail, four tips at the reference pixels and pitch, brightest at the index? 13. Is dust where dust settles (rib crests, ulnar bosses, up-facing knit) and absent from the shaded left dorsum and the palm? 14. Is the cuff black under neutral light (the blue only from the fill)? 15. Any poke-through of skin or rifle, any floating plate or pad, any candy-wrapper wrist? (2 = none.) 16. Would a Mechanix or Oakley wearer and a rifleman both believe it?

### 8.4 Failure modes and their fixes
| Symptom | Cause | Fix |
|---|---|---|
| Mitten: fingers fused, no fourchette valleys | shrinkwrap offset applied before the finger side groups were set; Corrective Smooth too strong | set zones before the modifiers; Corrective Smooth factor ≤ 0.5, `use_pin_boundary` |
| Balloon hand | offsets stacked (air + thickness added twice through Solidify outward) | Solidify inward from the outer surface (`offset = −1`), check `measure_glove()` offsets |
| Skin shows through the knit at the knuckles in the hero pose | weight interpolation at the MCP loops | the OUTSIDE shrinkwrap against `Body.Mesh.Posed` (step 11); if > 1 mm, use `--follow-correctives` |
| Fingers inside the grip or rail | `grip.py` solved for the bare pulp | pass `contact_offset` 1.5 to spec 05's solve; the OUTSIDE push-out is a 0.3 mm safety only |
| Plate floats or sinks between bosses | Surface Deform bound after the shell's modifiers were applied in a different pose | bind in rest before posing; re-bind on rebuild |
| Plate reads as a flat sticker | ribs too low or bevel too soft; no foam edge shadow | rib 1.4 proud with R 0.6 fillets, foam object present, AO bake |
| Pads at the DIPs or mid-phalanx | wrong landmark (used `finger*-3` heads) | pad centres on the PIP landmarks + 1 mm distal |
| Stitches float or sink | normal sampling off the subdivided surface | sample the evaluated mesh (`evaluated_get`), sink 0.15 |
| Glove bleached grey (prototype §0) | sheen > 0.12 or albedo read off the reference hex | sheen ≤ 0.08; calibrate albedo by the swatch render |
| Cuff painted blue | tinted albedo | neutral albedo; confirm by the fill-off render |
| Honeycomb reads as chainmail or scales | cell too large or relief too high | 2.4 mm cells, 0.25 mm relief, flatten by stretch |
| Right index too thick (> 10 px) | dorsal offset on the finger sides | side ease 0 on the fourchettes (offset 1.5) |
| Thumb-tip highlight missing at (850,445) | cap not curving over the rail edge; roughness too high | cap roughness 0.35 satin; the thumb IP 15°, pad folded 15° over the rail (spec 05 table B) |
| Left tips not darkening ulnar-wards | tips not stacked in depth | abductions +6/+2/−2/−6 and the 27 mm pitch from spec 05; the handguard's shadow must fall on them (spec 15 placement) |
| Dust uniform | UpMask not baked in the hero pose | bake the mask after `Hero.Pose` is set |

---

## 9. Build order, effort and risks
| # | Step | Effort | Risk | Mitigation |
|---|---|---|---|---|
| 1 | Hand copy, zones, offsets, solidify, seams (left) | 4 h | zone borders ragged on MPFB loops | define zones by the finger frames (spec 05 landmarks), 2 mm falloff; check V5 cavity |
| 2 | Plate and pads (lofts, ribs, flanges, foam) | 4 h | ribs too soft after Subdivision | bevel before subsurf, 0.8 mm / 3 seg; crease the groove floors |
| 3 | Cuff, binding, tab, pull, loop field, pull loop | 4 h | the slit/overlap and the tab path on a curved cuff | shrinkwrap the tab onto the cuff; build the slit as two overlapping lofts |
| 4 | Stitch library and seam loops | 3 h (shared `stitch.py`) | stitch count at closeup | one object, instancing by Geometry Nodes if > 40 k tris |
| 5 | UVs, bakes (AO, Curv, UpMask, Stretch) | 3 h | Pointiness weak on lofts | Bevel-node mask; bake after the shape is final |
| 6 | Materials, honeycomb tile generator, weathering masks, swatch calibration | 5 h | bleaching, blue cuff, albedo | prototype §0 rules; fill-off render |
| 7 | Skinning, stretch attribute, pose-space clearance, rifle push-out | 4 h | depends on spec 05's `grip.py` `contact_offset` and spec 15's `Rifle.Collider` | stand-in rifle (A2 grip box + octagonal handguard from spec 05 §3.8) until spec 15 lands |
| 8 | Right glove, V1–V7 renders, metrics, critic round | 4 h | render budget (two hero-lit 2048² views ≈ 3 min each on 4 cores) | 800² for the loop, acceptance renders on Jeff's GPU |
| | **Total** | **≈ 31 h** (two cloud sessions plus a GPU critic round) | | |

Biggest risks: (1) the hand underneath — every glove error that is really a hand error (finger lengths, knuckle positions, the grips) must be fixed in spec 05, not hidden by the glove; (2) the contact offsets — until `grip.py` knows the glove thickness, the gloved fingers will sit inside the rifle; (3) the knit back is the one surface the reference cannot confirm (D8), so its scale must be judged by a critic against real gloves rather than against the picture.

---

## 10. Interfaces and open questions for the client

### 10.1 What neighbouring parts must provide or respect
| Part | This part provides | This part needs / the neighbour must respect |
|---|---|---|
| Spec 05 hands | the gloved envelope `Glove.L/R.Shell` (for exclusion checks), `Glove.L/R.ContactReport.json`; the gloved finger widths (§3.1) that the hero index must read as 9–10 px | `Hand.L/R.GloveLast` (hero keys), `Body.Mesh` / `Body.Mesh.Posed`, `measure_hand()` landmarks (MCP/PIP apexes in H), `Hand.L/R.PalmFrame`, the vertex groups `hand_*`, `hand_pulp_N`; **`grip.py::close_finger(contact_offset=1.5)`** (palm 2.4 where the palm touches); corrective keys at the hero values; MPFB bone names unchanged |
| Spec 10 shirt and gaiter | `Glove.L/R.Cuff` as the sleeve collider (inner face body + 3.5, matching spec 10 §4.7's stand-in), gauntlet d −5 … −50 | the sleeve cuff ends at d −25 and closes to girth 200 (spec 10 §3): it stays inside the gauntlet; no shirt pixel may show between glove and gauntlet |
| Spec 12 hard armour (forearm guards, wrist bands) | `Glove.L/R.GauntletRing.Outer` (girth 220 at d −30) | the guard's wrist band (25 wide, forearm s 86–96 % = d −11 … −38) sits **over** the gauntlet with inner radius = gauntlet outer + 1.0; on the right hand the band hides all but 5–8 mm of the gauntlet (image); on the left ≈ 28 mm of neoprene shows; the band must not intersect the tab pull (clock 2) — place the band's buckle at clock 8–9 |
| Spec 15 carbine (grip and handguard) | the glove's 0.3 mm clearance rule, `Glove.Zone.Contact.*` | `Rifle.Collider`, `Rifle.GripFrame`, `Rifle.HandguardFrame` as spec 05 §4.8 assumes [VERIFY names]; the A2 grip (102 tall, serrated sides), the handguard (octagonal 45 × 55, lower-facet holes Ø 13–15 at 26 mm pitch) and the top rail (21.2 mm flat, 5.23 slots at 10.01 pitch) exactly as spec 05 §3.8 and the weapon note §3 — the thumb cap folds 15° over the rail's right edge and the fingertip caps sit 0.3 mm under the lower-right facet; no accessory under the handguard at 150–250 mm from the receiver face |
| Spec 08 rig and pose | nothing | `Hero.Pose` frame 1, `Corrective Smooth` after `Armature`, ≤ 4 influences, `pose_report.json` |
| Spec 13 plate carrier | nothing | the right cuff passes in front of the carrier's lower pouches; no contact |
| Spec 16 materials library | `Glove.Mat.*` node groups (leather, honeycomb knit, TPR, neoprene, hook, loop, grosgrain, thread, webbing), the honeycomb tile generator, the dust/polish/grime mask convention (RGBA) | the shared `fabric_material()` sheen limits, `polymer_material()` micro grain, the four-sphere swatch scene |
| Spec 17 evaluation scene | V1–V7 definitions, `sample_glove_ref.py` | hero camera and lights; the fill-off variant for the cuff colour check |
| Spec 18 pipeline | `Glove.L/R.Game` (12 k tris, one 2048 atlas, baked stitch bump), LOD switches `--stitches geo|bump`, `--fuzz`, `--adaptive` | export scale 1800/1855; glTF with the body's skin |

### 10.2 Questions for the client
1. **Glove identity**: the hybrid of D1 (SI Assault pattern and materials with an M-Pact 3-type ribbed TPR plate) is my reading of the image under the reality rule. If you would rather have a pure M-Pact 3 (synthetic-leather palm, elastic cuff with a TPR tab, no neoprene gauntlet) or a pure SI Assault (carbon plate without ribs, goatskin, neoprene), say so; the plate ribs and the gauntlet would change.
2. **Brand marks**: none modelled (D16). A fictional "HEXCOM" emboss on the TPR pull is cheap if wanted.
3. **Colour**: black gloves whose warm dust and the hangar's cool fill make the brown-black and blue-grey of the picture. Confirm you do not want brown or coyote gloves.
4. **Gauntlet height 45 mm** (D7) versus the analysts' "60 mm shows": accept the smaller visible band on the left wrist?
5. **Knit back honeycomb** (D8): keep, or plain TrekDry-type knit as the M-Pact really has?

### 10.3 Items tagged [VERIFY]
Spec numbers of the weapon (15), materials (16), evaluation (17) and pipeline (18) specs and their object names (`Rifle.Collider`, `Rifle.GripFrame`, `Rifle.HandguardFrame`); the Mechanix size chart's finger-length unit (research §8 lists 138–145 for L, which matches neither our 80 mm finger nor our 201 mm hand); the M-Pact 3 plate height and thickness (35 × 6 uncited); the SI Assault cuff height (45 estimated); a named real glove with a honeycomb-embossed back; the `Hand.L/R.GloveLast` pose state in spec 05 §4.9 (rest with hero correctives, or posed) — this spec builds on `Body.Mesh` in rest and checks against `Body.Mesh.Posed`, so either reading works, but `clearance_report()` must use the posed hand.
