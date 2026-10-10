# Part 15 — The "AR-12 Carbine" (built as one real BCM 16 in mid-length M4-pattern carbine) and the P9 sidearm appendix

Status: draft 1 (spec writer), 2026-10-10, written under the **reality-wins** rule (`CLAUDE.md`, Source of truth; Jeff singled out the weapon). Owner script: `scripts/parts/15_carbine.py`, with shared helpers `scripts/lib/hardsurf.py` (EXACT-boolean union/difference, manifold and volume checks, bevel + weighted-normal finish), `scripts/lib/lathe.py` (revolve a station table), `scripts/lib/rail1913.py` (MIL-STD-1913 rail generator), `scripts/lib/mlok.py` (M-LOK slot cutters), `scripts/lib/mat_hard.py` (hard-surface materials and the `Wear.EdgeBevel` node group), `scripts/lib/decal.py`, `scripts/lib/measure.py::measure_rifle()`, and the evaluation scripts `scripts/eval/rifle_overlay.py` and `scripts/eval/rifle_views.py`. Object prefix `Rifle.*` (and `Pistol.*` for the appendix). Collection `Rifle`.

**Frames.** Millimetres in this spec, metres in Blender. The character frame **W** is the project's (origin on the floor between the feet, +Z up, the character faces −Y, **+X = the soldier's LEFT**). The rifle is built in its own **rifle frame R**: origin on the bore axis in the plane of the upper receiver's front face (the face the barrel nut and the handguard seat against); **+Y toward the muzzle, +Z toward the top rail, +X toward the rifle's RIGHT** (the ejection-port side, the shooter's right when shouldered, the side the camera sees). This is the weapon note's and spec 08's frame with one wording correction: their "origin at the bolt face … at the receiver face" conflates two planes; the real closed bolt face sits **12.2 mm behind** the origin (§3.4), and every number in the neighbouring specs already measures from the receiver face. "Left/right" of a rifle part are the rifle's own; "his left/right" are the soldier's.

**Provenance tags** on every number: **S** = sourced (a published specification; the URL list is §3.15), **M** = measured (on `reference_full.png`, on my zooms, or on the CC0 M4A1 model `assets/models/oga_m4a1_nisu`, which is a dimensional cross-check only), **E** = estimated (reasoned from the mechanism, marked [VERIFY] where a physical sample or a drawing would settle it).

Sources read: `notes/analysis_weapon.md` (whole), `notes/analysis_consolidated.md` "Agreed scale", §1 (pose, hands), §7 (weapon), §8 (camera, lights, grading), §9 (disputes 1, 7, 13, 17); `notes/research_dimensions.md` §12–13; `notes/research_assets.md` (model and texture rows); `notes/research_prototypes.md` §0, §6 (magwell), §8 (recipes); `notes/research_blender_capabilities.md` (bake, export); `spec/01_foot_ankle_sock.md` (format); `spec/05_arm_hand.md` §3.8, §4.8 (grips, frames); `spec/08_rig_pose.md` §2.2, §3.5, §4.8, §10 (placement, pins, frames); `spec/11_gloves.md` §4.11, §10 (collider, 0.3 mm contact rule); `spec/13_plate_carrier.md` (`Vest.Collider`, light clearance); `spec/14_belt_leg_rigs.md` (PMAG pouches, optional P226 holster). Own work for this spec (the projection is saved as `scripts/eval/rifle_project.py`, run with `python3 -I`): an orthographic mm-gridded render and Y-slices of the CC0 M4A1; a forward and inverse projection of the real geometry through the reference camera and spec 08's rifle transform (every "real px" in §2 comes from it); gridded zooms `ref/zoom_carbine15_grid_{hgfront_x10, receiver_x8, stock_x6, magwell_x8, muzzle_x10}.png` (full-image coordinates on the grid lines, gamma 1.4–1.6), and the ungridded `ref/zoom_carbine15_*` set made earlier.

---

## 1. Purpose and acceptance

### 1.1 What this part is
The soldier's primary weapon, complete and at real scale: upper receiver with its rail, ejection port, open dust cover, visible bolt carrier, forward assist, brass deflector and charging handle; lower receiver with magazine well, controls, pins, trigger, trigger guard and pistol grip; receiver extension, castle nut, end plate and the skeleton stock with its butt pad; barrel, gas block and gas tube; free-float M-LOK handguard; muzzle device; weapon light on its offset mount; optic on its mount (option A by default, option B on request); one seated 30-round magazine; every pin, roll pin, set screw, spring end and detent that a closeup can see; the paint, wear, carbon and dust of a carried rifle; the frames, pins and collider that specs 05, 08 and 11 consume; a game LOD; and an appendix for the "P9 Sidearm", which the soldier does not visibly carry. In the hero image the rifle is the largest hard-surface object in frame (about 380 × 330 px), crossing the chest from the right pectoral to the left thigh, and both hands are on it.

### 1.2 The one real configuration (the source of truth for every dimension)
The loadout card calls it the "AR-12 Carbine"; the drawing is an AR-15/M4-pattern carbine. Built as **one purchasable rifle**:

| Assembly | Named real part (build to its published dimensions) | Why this part |
|---|---|---|
| Upper receiver | **BCM M4 forged flat-top upper** (mil-spec, Colt-TDP pattern: forward assist, brass deflector, ejection-port cover, M4 feed ramps, T-marked 1913 rail) | standard M4 upper; matches every drawn upper feature |
| Barrel and gas | **BCM 16 in mid-length, government profile** 5.56 NATO, 1:7, chrome-lined, M4 extension; **low-profile 0.750 in gas block**, mid-length gas tube | the 16 in barrel of the analysis; mid-length is the usual gas system on a 16 in barrel, and its low-profile block fits under the handguard [VERIFY the exact BCM barrel SKU] |
| Handguard | **BCM MCMR-13** M-LOK free-float rail: 13.0 in top rail, 13.4 in to the flare, 1.50 in wide, 1.30 in ID, steel barrel nut indexed to the 12 o'clock rail, 6061-T6, Type III Class 2 hardcoat | the 13 in octagonal M-LOK handguard of the analysis and of every neighbouring spec |
| Bolt carrier group | **BCM M16-profile BCG**, manganese phosphate, chrome-lined carrier bore, staked gas key | the bright glint in the open port = its polished bearing bands |
| Charging handle | **mil-spec (Colt-pattern) charging handle**, latch on the LEFT | consolidated dispute 13 |
| Lower receiver | **BCM M4 forged lower** (mil-spec): magwell with flared lip, mag-release button and fence on the right, bolt catch and selector on the left, pivot and takedown pins, mil-spec trigger guard, mil-spec trigger | standard lower; matches the drawn right face |
| Pistol grip | **USGI A2 pistol grip** (A2 finger nub, checkered straps) | the icon's grip; spec 05's grip |
| Receiver extension | **mil-spec 6-position carbine receiver extension** (OD 1.148 in), mil-spec castle nut, **QD end plate** | the drawn glossy tube |
| Stock | **Mission First Tactical BATTLELINK Minimalist, MIL-SPEC, black polymer** (7.084 × 5.22 × 1.752 in, angled rubberised butt pad, sling slots, QD point), at position 3 of 6 | the drawn skeleton stock with one big window |
| Muzzle device | **A2 birdcage flash hider**, 1/2-28, 1.75 in long, 0.86 in diameter, 5 ports, closed bottom | the standard M4 device; its front lands 1.6 px from the drawn muzzle tip (§2.2) |
| Weapon light | **SureFire M300C Mini Scout Light** (4.1 in long, 1.125 in bezel, 1 × 123A, Z68 click tail cap) | the drawn light is 2.9 cm across and ~8.6 cm long; the M300C is 2.9 cm and 10.4 cm; an M600 is 13.7–14.1 cm |
| Light mount | **Arisaka Offset Scout Mount, M-LOK** (< 0.20 in plate; sets the light at 1:30–2:00 beside the rail) | the drawn light sits beside the top rail on the right |
| Optic (option A, default) | **Aimpoint Micro T-2 on the Aimpoint LRP mount with the 39 mm spacer** ("AR-ready" package) | real rifles carry a sight; the micro dot is the smallest real one |
| Optic (option B) | **Aimpoint CompM4** on its mount | the loadout icon's optic |
| Magazine | **Magpul PMAG 30 AR/M4 GEN M3 (MAG557), Stealth Gray** | real dimensions published; grey, ribbed, flared floorplate, no window |
| Finish (owner-applied) | Cerakote **H-148 Burnt Bronze** on the barrel and the A2; hand-applied **flat dark earth** stripes and patches in the drawing's six places | the drawing's two colour accents, on a real rifle |

No iron sights, no sling, no underbarrel accessory, no rail covers (all as drawn; §2.6 D20–D21).

### 1.3 What "perfect" looks like
A gun-literate critic looking at the orthographic and closeup renders names the build part by part without being told: a forged BCM-pattern M4 upper and lower, MCMR-13, Minimalist stock, A2 grip, A2 birdcage, Mini Scout on an offset mount, T-2 on an LRP, PMAG GEN M3. He finds no proportion that a calliper would refute. Specifically:
- the rail's 10.01 mm slot pitch;
- the dust cover hanging open on its hinge rod;
- the bolt carrier's forward-assist notches inside the port;
- the deflector's wedge and the forward assist's round button;
- the flared magwell lip and the mag release standing in its fence;
- the A2 grip's finger nub;
- the castle nut's notches and the staked end plate;
- the M-LOK slots at 32 × 7 on a 40 mm pitch;
- the lightening holes punched cleanly through the lower bevels;
- the gas block glimpsed through the last two holes;
- the A2's five slots and closed bottom;
- the Mini Scout's knurled tail cap, shroud and TIR lens;
- the T-2's turrets and the LRP lever;
- the PMAG's low ribs, dot-matrix panel and flared floorplate.

The surfaces read as a carried rifle, not a catalogue render:
- matte black hardcoat whose sharp edges are worn to grey-silver aluminium;
- semi-gloss tube and light;
- hand-painted tan stripes chipped at their edges and wherever hands and gear rub;
- burnt-bronze Cerakote sooted black at the A2's slots;
- dust in the rail slots and the handguard holes;
- a polished trigger face and mag-release button.

In the hero frame the rifle sits on spec 08's two pins (butt pad on the right pectoral, muzzle tip at pixel (903, 570)). Every real feature then lands where the projection table of §2.2 predicts, and the known AI errors of the drawing are not copied: no three muzzle tubes, no rail floating 10 cm above the bore, no light straddling the receiver joint.

### 1.4 Closeup render views (rendered by `scripts/eval/rifle_views.py`, written to `renders/15_carbine/`)
Cameras V2–V11 are given in the **rifle frame R** with `Rifle.Root` at the world origin and identity rotation; V1 uses the hero placement. Sensor 36 mm wide everywhere. Look-dev lighting = the neutral HDRI at 0.6 plus a 3 W/m² key (research_prototypes §0), then once more under the hero lights of `analysis_consolidated.md` §8 for colour.

| View | Camera position (mm) | Target (mm) | Lens / output | Compared with |
|---|---|---|---|---|
| V1 Hero match | the reference camera: W (0, −4500, 600), rotation (93.9°, 0, 0) | — | 46 mm, 1672 × 941, then the crop (630, 230)–(950, 570) upscaled ×3 | `ref/crop_hands_rifle.png`, `ref/zoom_carbine15_whole_bright_x3.png`; the projection table §2.2; colour patches §5.6 |
| V2 Right side, orthographic | R (+1000, +5, −30) looking −X | — | ortho scale 900, 4096 × 1600 | §3 tables (every length); `ref/crop_icon_carbine.png` for the silhouette of stock, receiver, grip, guard and magazine (the icon's handguard, optic and underbarrel unit differ by design, §2.5) |
| V3 Top, orthographic | R (0, +5, +1000) looking −Z | — | ortho 900, 4096 × 1200 | rail pitch and continuity, light offset, optic footprint, charging-handle latch |
| V4 Left side, orthographic | R (−1000, +5, −30) looking +X | — | ortho 900, 4096 × 1600 | bolt catch, selector, charging-handle latch, QD socket on the handguard's left, markings |
| V5 Three-quarter | R (+520, +520, +260) | R (0, −20, −20) | 50 mm, 3000 × 2000 | overall impression; §1.3 list |
| V6 Port closeup | R (+300, −58, +60) | R (+15, −58, 0) | 100 mm, 2048², f/5.6 focused on the port | §3.4 and §3.5: port, cover, hinge rod, BCG with its notches and wear, deflector, forward assist; `ref/zoom_carbine15_grid_receiver_x8.png` for the tan stripe and the glints |
| V7 Handguard closeup | R (+320, +200, −120) | R (+12, +200, −6) | 85 mm, 2048² | §3.8: M-LOK slots, lightening holes, gas block through holes 5–6, rail teeth, T-marks, front chamfer; `ref/zoom_carbine15_grid_hgfront_x10.png` |
| V8 Muzzle closeup | R (+230, +480, +60) | R (0, +405, 0) | 100 mm, 2048² | §3.9: barrel step, crush washer, A2 slots and closed bottom, wrench flats, bronze finish, soot; `ref/zoom_carbine15_grid_muzzle_x10.png` (colour only) |
| V9 Magwell, grip and stock junction | R (+380, −160, −160) | R (+10, −120, −60) | 85 mm, 2048² | §3.6, §3.7, §3.11: magwell flare, mag release, pins, trigger, guard, A2 grip, PMAG ribs, castle nut, end plate, stock front; `ref/zoom_carbine15_grid_magwell_x8.png`, `ref/zoom_carbine15_grid_stock_x6.png` |
| V10 Light and mount | R (+260, +60, +160) | R (+28, +62, +14) | 100 mm, 2048² | §3.10: M300C head, body, tail cap knurl and shroud, mount plate, clearances |
| V11 Optic | R (+300, −140, +180) | R (0, −140, +60) | 85 mm, 2048², once per optic option (`--optic a`, `--optic b`) | §3.12: T-2 turrets and lenses, LRP lever and spacer; CompM4 |
| V12 Icon silhouette | V2 with `--optic b`, scaled to the icon (250 px ≈ 860 mm) | — | 1050 × 360 | `ref/crop_icon_carbine.png`: outline of stock, receiver, grip, trigger guard and magazine only |

### 1.5 Pass criteria (scored by the critic, 0–2 each; the part passes at ≥ 26/32 with no zero; full method §8)
1. **Dimensions:** every length in the `measure_rifle()` report (§8.2) is within tolerance of §3 (rail pitch ±0.02 mm per slot over 10 slots, slot width ±0.05, M-LOK slots ±0.2, part lengths ±1, assemblies ±2, OAL ±3).
2. **Identity:** a gun-literate critic identifies the named parts of §1.2 from V2–V5 without help.
3. **Rail:** MIL-STD-1913 profile (21.2 top, 45° flanks, 5.23 slots, 3.0 deep), one straight line from the receiver's rear to the handguard's front, top 30.2 above the bore, T-marks present.
4. **Upper:** port open with the cover hanging on its rod; BCG visible with forward-assist notches and polished bands; forward assist and deflector in the right places and shapes; charging handle latch on the left.
5. **Lower:** flared magwell, mag release inside its fence, pin heads, trigger and guard, A2 grip with nub and checkering, bolt catch and selector on the left.
6. **Handguard:** octagon 38.1 across flats; M-LOK at 3, 6 and 9 o'clock; lightening holes clean through the 4:30 and 7:30 bevels; chamfered front; QD socket on the left; gas block visible through holes 5 and 6.
7. **Muzzle:** one barrel, government profile step visible, A2 with five slots and a closed bottom, burnt bronze with soot. No second tube anywhere.
8. **Light:** M300C proportions, bezel 28.6, knurled tail cap with shroud, TIR lens; offset mount real and touching; clearances of §3.10 met.
9. **Magazine:** PMAG GEN M3 features (ribs, texture, dot matrix, flared floorplate, bolt-catch notch, over-travel stop); constant curve; seated with ≤ 0.5 mm gap at the magwell.
10. **Stock:** Minimalist outline with its large window; butt pad raked 12°; castle nut, staked end plate, QD socket; 30 mm of bare tube between nut and stock.
11. **Finish:** the hex targets of §5.6 within ΔE2000 ≤ 6 (≤ 8 for the tan and bronze); edge wear only on edges; chips only on paint; dust, carbon and polish where use puts them.
12. **Hero overlay:** pins within ±4 px; each "real" landmark of §2.2 within ±6 px of its predicted pixel (not of the drawn one, where the two differ by an accepted decision).
13. **Contacts:** spec 05/11 contact reports pass against `Rifle.Collider` (pulp 0.3 ± 0.3 mm, no penetration); the butt pad touches `Vest.Collider` within 0–3 mm.
14. **Clean geometry:** every boolean result manifold, no shading smear, no decal z-fighting, no floating or interpenetrating parts (§8.5).
15. **Silhouette:** hero-crop IoU with the reference rifle mask ≥ 0.75 outside the accepted-deviation zones of §2.6.
16. **Free judgement:** "Would an armourer believe this rifle, and would a player recognise it as the one in the picture?"

---

## 2. Reference observations

All pixel coordinates are full-image coordinates of `ref/reference_full.png` (1672 × 941). The agreed figure scale is 4.72 px/cm; the rifle lies 15–40 cm nearer the camera than the body and runs 43° toward the camera, so along its bore the projected scale is **0.415 px/mm at the stock and 0.452 px/mm at the handguard** (from the projection, below). Colour samples are the analysts' 3 × 3 means unless marked; "single" is one pixel.

### 2.1 Pose and placement (spec 08 owns the transform; this spec owns the pins)
| Quantity | Value | Source |
|---|---|---|
| Butt-pad centre | pixel (695, 268); in contact with the carrier over the right pectoral (0–3 mm) | consolidated §7, spec 08 §2.1 |
| Muzzle tip | pixel (903, 570), 682 mm above the floor (analysts: 690) | consolidated §7, spec 08 |
| Bore direction (spec 08 solve) | W (0.441, −0.468, −0.766): 50.0° below horizontal, 43.3° toward his left of the camera axis (analysts: 56° in the image plane, 25° toward the camera) | spec 08 §2.2, §4.8 |
| `Rifle.Root` | W (−67, −346, 1014); axes +X (−0.271, −0.883, 0.384), +Y (0.441, −0.468, −0.766), +Z (0.856, −0.038, 0.516) | spec 08 §4.8 |
| Side seen | the rifle's RIGHT (port, forward assist, mag release); roll about the bore ≈ 0 | weapon note §1 |
| Hands | right hand on the pistol grip with the index straight along the lower's right face; left hand over the handguard, thumb across the rail, four fingertips under it at (806, 458) (812, 470) (820, 483) (828, 495) | consolidated §1 |

### 2.2 Where the real rifle lands in the picture (my projection through the reference camera and spec 08's transform)
The reference camera of consolidated §8 (W (0, −4500, 600), 93.9° pitch, 46 mm, f = 2136 px) reproduces spec 08's pins (butt pad (695.8, 270.1) against (695, 268)), so the table can be trusted to ±2 px. "Drawn" is the analysts' landmark; "real" is the §3 geometry projected; the error is what the critic will see, and the decision column says whether it is accepted (§2.6).

| Landmark | Real geometry, R (mm) | Real px | Drawn px | Error px | Reading |
|---|---|---|---|---|---|
| Butt-pad centre | (0, −415, −46) | (695, 271) | (695, 268) | 2.6 | pin |
| Butt heel / toe | (0, −428.6, +18) / (0, −401, −112) | (719, 250) / (670, 292) | (706, 243) / (683, 296) | 15 / 13 | the drawn pad is raked ≈ 30°, the real pad 12° (D15) |
| Ejection-port centre | (+15.5, −58, +1.5) | (787, 378) | (790, 375) | **4.3** | the real port is where the drawing has it; the analysis's −160 … −81 was wrong (D10) |
| Port rear / front edge | Y −96 / −20 | (779, 365) / (796, 392) | (778, 358) / (802, 392) | 6.8 / 6.3 | |
| Mag-release button | (+16, −74, −38) | (767, 383) | (764, 384) | **2.8** | |
| Bolt-carrier glint | (+12.7, −42, +5) | — | (793, 384) | — | inverse projection puts it at Y −42, the front of the port: the carrier's polished front band |
| Receiver face on the bore | (0, 0, 0) | (802, 404) | (793, 402) | 8.9 | handguard rear end |
| Handguard lightening hole #1 / #7 | 4:30 bevel, Y 105 / 261 | (817, 443) / (853, 503) | (822, 447) / (853, 510) | 6.1 / 6.8 | the drawn row is real-positioned |
| Handguard front, MCMR-13 | (0, 340.9, 0) | (881, 534) | (873, 512) | **23.5** | the drawn handguard ends at Y ≈ 290 (11.4 in); accepted, open question Q1 (D5) |
| Barrel shoulder / A2 rear face | (0, 382.7, 0) | (891, 551) | drawn "ring groove 2" (885, 548) | 6.5 | the second drawn groove is this joint (D4) |
| A2 front (muzzle end) | (0, 427.2, 0) | (902, 569) | (903, 570) | **1.6** | pin; a real 16 in barrel and A2 reproduce the drawn length |
| Weapon light tail / bezel | (+32, 10, +16) / (+32, 114, +16) | (806, 395) / (830, 434) | (813, 362) / (832, 394) | 34 / 40 | the drawn light straddles the receiver joint beside a rail drawn 10 cm too high; moved onto the handguard (D8) |
| Top rail at Y 255 | (0, 255, 30.2) | (874, 492) | (872, 438) | **54** | the drawn rail floats ≈ 10 cm off the bore; not copied (D18) |
| Castle nut top | (0, −215, +20) | (764, 322) | (748, 300) | 27 | the drawn receiver is longer than a real one (D12) |
| Charging-handle rear top | (0, −205, +25) | (768, 324) | (752, 312) | 20 | as above |
| Magwell front / rear lip | (0, −12, −76) / (0, −86, −82) | (766, 419) / (747, 394) | (790, 412) / (760, 402) | 25 / 15 | as above |
| Magazine floorplate centre | (0, −32, −197) curved | (709, 444) | (748, 455) | **41** | the drawn magazine is rotated ≈ 30° in the image plane relative to its own receiver — impossible for a seated magazine (D14) |
| Grip frame (spec 05) | real (0, −169.0, −94.8) | (724, 368) | right index MCP (727, 352) | 16 | spec 08's frame (0, −194, −76) sat on the drawing; a real A2 grip is 19 mm lower and 25 mm further forward (D13) |
| Left-hand station | (0, 170, 0) | (840, 467) | (840, 467) | 0.4 | spec 08 D5 holds |
| Optic A (T-2), rear-mounted, top | (0, −174 … −106, +87) | (801, 319) … (816, 343) | none drawn | — | a front-mounted T-2 would land on the drawn light at (822, 369); rear mounting keeps that area clean (D9) |

Inverse projections of the drawn accents onto the real part surfaces (the ray from each pixel meets the named plane):

| Drawn feature | Pixel | Plane | Lands at (R, mm) | Used for |
|---|---|---|---|---|
| Tan stripe on the upper, rear end / front end | (752, 305) / (775, 345) | X +15.5 (upper's right wall) | Y −254, Z +17 / Y −142, Z +15 | the stripe runs 57 mm past the real upper's rear: shortened to the receiver, Y −198 … −113 (D11) |
| Lower small tan mark | (774, 390) | X +16.0 | Y −51, Z −33 | lower paint patch §5.4 (P4) |
| Magwell front "rivet" patch | (792, 417) | X +14.5 | Y +24, Z −30 | in front of the real magwell; moved to its front-right corner (P5) |
| Stock tan frame centre | (741, 330) | X +22 | Y −211, Z −28 | the end plate / stock-front junction (P2, D16) |
| Stock stripe, warmest | (718, 281) | X +22 | Y −345, Z −17 | stock stripe (P1) |
| Handguard tan patches | (809, 426) / (799, 408) | X +19.05 | Y +65 / +18, Z ≈ −10 | patches P6 on the 3 o'clock face |
| "Screws" a, b, c | (851, 478) (855, 486) (860, 497) | X +19.05 | Y 214 / 234 / 260, Z +7 … +3 | mid-height of the 3 o'clock face where nothing real sits; dropped (D7) |
| Right index tip / MCP | (750, 398) / (727, 355) | X +18 / +25 | Y −62, Z −81 / Y −174, Z −77 | spec 05/08 hand placement (moves with D13) |
| Left thumb tip | (846, 447) | X 0 | Y 138, Z +30 | rail top |

### 2.3 Colour samples (held rifle; analysts' values, re-checked in my zooms)
| Part | Hex (lit / mid / shadow) | Sampled at | Finish read |
|---|---|---|---|
| Upper receiver | **#413c3b** median; lit edge #686463; shadow #44413e | box (745, 300)–(800, 380); (772, 352); (755, 345) | matte hardcoat, edges worn 1–1.5 stops lighter |
| Lower receiver | #403c39 median; darkest #262321 | box (745, 375)–(790, 410); (760, 392) | same |
| Stock body | **#3d3733** median; lit cheek #5e4f44 (725, 290); butt #141211; scuffs #5e4f44 → #8d8787 | | matte polymer, scuffed |
| Buffer tube | shadow #534232; mid #807a75; highlight #aba6a6–#b5b0b1; peak #ece7e9 (741, 297) | (712, 262) (722, 268) (741, 297) | semi-gloss hardcoat, warm dust in the shadow |
| Tan accents | stock stripe #a68869 (single #c1a27f) (718, 281); stock frame #bf9c70 (single #cea676), interior #86694f (741, 330); **upper stripe #d4a271** (single #d29b65) (767, 342); lower mark #736456 (single #b09f8c) (774, 390); magwell patch #8d764b (single #a18958) (792, 417); handguard #685840 (single #7f6c50) (809, 426), #312e28 (799, 408) | | hand-applied FDE, 20–30 % chipped, worn centres |
| Magazine | #423e3a median; lit #3f3c36; ribs #625a56 (752, 431); baseplate #595452 (748, 453) | | worn grey |
| Handguard right face | **#393532** median; lit #5e5040 (812, 430); mid #36332f; between holes #0d0a08; hole interiors #2b2927 | (835, 470), (845, 488), (838, 478) | matte, warmer than the receiver (dust) |
| Top rail | #283547 (shadow, receiver); #697b97 / #6d7e9d (rim-lit, (872, 438)); lit tops #78706d (828, 382) | | the cool side light from his left |
| Weapon light | #302f30 median; highlight #8f8b84, peak #c9c6be (827, 385); tail #46433a; bezel face #020000 | | black hardcoat |
| Exposed "barrel" (bronze tube) | **#5f4c3e** (single #6a5344) (874, 554); mouth #15191d (895, 568) | | burnt bronze; ring lines at (876, 530) and (885, 548) |
| Thin blued rods | #4d5f73 / #575f6e, specular #d2dff1 (897, 555) | | artefacts (D3); the colour is the cool rim light on glossy metal |
| Port interior | #3e3a39 median, glint at (793, 384) | | dark carrier, one polished band |
| Mag-release button | #676261 (single #c0bbbb) (764, 384) | | polished steel |
| Handguard front cap | #596672 (single #92a1b0 at (877, 521)) | | rim-lit chamfer |

The loadout icon (muted by the dark UI card #0f1317) shows the same family, darker and cleaner: stock #1d1d1d / #303131 with a tan stripe #88745b; upper #4c4b4b with a light-blue window #80a8c2–#98c1de; gold plates #917652; grip #121415; magazine #312f31 with ribs #474647; optic #262828; handguard #403f3e with bare-metal hole rims #9e9897; flash hider #0f1315.

### 2.4 What the picture shows that is physically wrong or self-contradictory
1. **Three (in the x10 zoom, four) parallel tubes at the muzzle:** two bronze tubes with ring lines and two thin blued rods leave the handguard's lower front. No AR has this. The only element of barrel diameter (the drawn bronze tube, Ø 21–23 mm projected against a real 19.05 mm barrel and a 21.8 mm A2) is the barrel plus its device; the rods (Ø 10–11 mm) match nothing.
2. **The top rail floats ≈ 10 cm above the bore** along its whole length (real: 30.2 mm). Everything drawn relative to that rail (the light, the thumb, the "screws" near "the top" of the right face) is displaced with it.
3. **The light straddles the receiver/handguard joint**; no mount can hold it there.
4. **The receiver is drawn 12–34 % oversize** relative to the pinned real rifle (castle nut 27 px, charging handle 20 px, magwell 15–25 px off the real projection), while the handguard is drawn ≈ 40 mm short and the muzzle stub ≈ 55 mm long.
5. **The magazine is rotated ≈ 30° in the image plane relative to its receiver**: it hangs toward the floor as if loose. A seated magazine is rigid with the lower.
6. **The butt pad is drawn raked ≈ 30°** (heel 36 mm behind the pad centre); a 12° pad is real.
7. **No sight of any kind** on a fighting carbine (the icon has one).
8. **The ejection-port interior is a dark box with one glint**: right for a dark phosphate carrier; wrong if read as "bright steel".

### 2.5 Ambiguities read at image level
* **Icon vs held rifle.** The icon has a 9 in handguard, an underbarrel laser module, a CompM4, a blue-glowing window and a closed port. The held rifle (the hero view) wins everywhere except the optic, which becomes an option (D9). The icon's grip, trigger guard and single barrel with a birdcage support the held reading.
* **The ring lines on the bronze tube** at (876, 530) and (885, 548) project to Y ≈ 325 and 369 on the bore. The second lies 6.5 px from the real barrel-to-A2 joint (Y 382.7). The first falls where a 13 in handguard ends. Neither is a separate part.
* **The rail band's "braided" look** in the x3 crop is Lanczos ringing on the 10 mm slot pitch (weapon note §3.5), not paracord.
* **The tan "QD frame" on the stock** (≈ 3 × 7 cm with a dark interior) could be a painted QD end plate or the stock's own sling-slot loop. Both are real; the stock's front loop is taken because the frame sits below the tube (D16).
* **Rib count on the magazine**: three on the held rifle, four on the icon. The PMAG GEN M3 has "low profile ribs" (Magpul data sheet) but the count is not published (D14, [VERIFY]).

### 2.6 Reality-wins decisions (the record the client's rule requires: image or analysis → reality → decision)
| # | Item | Image / analysis said | Reality | Decision (and consequence) |
|---|---|---|---|---|
| D1 | Identity | "AR-15/M4-pattern carbine, 16 in barrel, 13 in handguard" (a class) | a class is not a rifle | **one named BCM-built 16 in mid-length carbine, §1.2**; every dimension in §3 comes from it |
| D2 | Frame origin | "bolt face on the bore at the receiver face" | the closed bolt face is 12.2 mm behind the receiver face (barrel tenon 0.620 in inside a flanged extension) | origin = bore ∩ receiver front face (all neighbour numbers unchanged); bolt face at Y −12.2 |
| D3 | Muzzle | analysis: blued barrel (the top rod) + a 64 mm bronze device | the rods are artefacts; the bronze tube is the barrel + device; real 16 in barrel ends at Y 394.2 | **exposed barrel and A2 in Cerakote H-148 Burnt Bronze**; the barrel inside the handguard bronze too (one coat); no rods |
| D4 | "Two ring grooves" on the device | decorative grooves | no real A2 has them | the joint (crush washer) at Y 382.7 and the A2's slot band read as the lines; nothing added |
| D5 | Handguard section and length | 45 × 55 mm (drawn chunky); 330 mm | MCMR-13: 38.1 mm wide, 33.0 ID, 340.4 overall (13.4 in to the flare), rail 13.0 in | **38.1 × 49.3 mm octagon, body Y 0.5 → 340.9**; the front ends 23.5 px beyond the drawn cap (accepted; Q1 offers MCMR-10, 13.6 px short, or a 12 in rail from another maker, 8 px) |
| D6 | Lower-bevel holes | Ø 14 mm at 26 mm pitch, "8 per side from 205 → 330" | a 38.1 mm octagon's bevels are 15.8 mm wide: Ø 14 leaves 0.9 mm lands; the analysis's own landmarks put the row at Y 105–261, not 205–330 | **Ø 10.0 holes at 26.0 pitch, 7 per bevel at Y 105 … 261**: the drawn identity in a physically possible size; the catalogue MCMR's bevel pattern is [VERIFY], switch `--hg-holes image` or `--hg-holes none` (Q2) |
| D7 | Three Ø 5 mm socket screws on the right face | "near the top, at 190/215/240" | inverse projection puts them mid-height on the 3 o'clock face, where an MCMR has only its M-LOK slots | **dropped**; the M-LOK slot rims carry a 0.5 mm chamfer that catches the key there (Q5) |
| D8 | Weapon light | SureFire M600-Scout class, 110 mm "compromise", straddling the joint | an M600 is 137–141 mm; the drawn light is 2.9 cm across, like the M300C's 1.125 in bezel; nothing mounts across the joint | **SureFire M300C (104 × 28.6 mm) on an Arisaka Offset Scout Mount (M-LOK) in the rearmost 3 o'clock slot, axis at X +32, Z +16, Y +10 … +114**; 34–40 px from the drawn light (accepted) |
| D9 | Optic | held: none; icon: CompM4; analysis: T-2 low mount at the receiver front | a fighting carbine carries a sight; a front-mounted T-2 projects onto the drawn light | **option A default: T-2 on LRP + 39 mm spacer at the rear of the receiver rail (Y −174 … −106)**; option B CompM4; `--optic none` only for overlays |
| D10 | Ejection port | analysis: Y −160 … −81 | port spans the case's travel behind the 12.2 mm-deep bolt face; real projection lands 4 px from the drawn port | **opening Y −20.0 … −96.2, Z −8.6 … +11.7; cover open 165° on its hinge rod** |
| D11 | Panel behind the port | tan 10 × 85 mm (held) or blue emissive (icon) | the drawn stripe runs 57 mm past the real upper's rear; an emissive panel is not a real part | **FDE stripe 85 × 10 mm, Y −198 … −113, Z +8 … +18**, painted over whatever lies there; emissive off (switch kept, documented as unreal) |
| D12 | Upper receiver length | 205 mm | 7.75 in stripped (listing), 199 mm on the CC0 model | **197 mm** (Y −197 … 0) |
| D13 | Grip position | spec 05/08 frame (0, −194, −76) fitted to the drawn hand | A2 grip top 54 mm below the bore, front strap at Y −150 (CC0 −151) | **`Rifle.GripFrame` at (0, −169.0, −94.8)**; the right hand lands ≈ 16 px lower than drawn (accepted; spec 05/08 change, §10) |
| D14 | Magazine | straight, 70 × 24 section, 3 ribs | no 30-round 5.56 magazine is straight; PMAG GEN M3: 190 × 66 × 22, constant curve | **PMAG GEN M3 Stealth Gray, curved (floorplate tilted 14.9°), 3 ribs per side as drawn [VERIFY count]**; floorplate 41 px from the drawn one (accepted) |
| D15 | Stock and butt pad | MFT Minimalist class; pad raked 12° (analysis) or ≈ 30° (drawn) | MFT Minimalist MIL-SPEC 179.9 × 132.6 × 44.5 mm, angled pad | **real stock at position 3 of 6, pad centre (0, −415, −46), rake 12°** |
| D16 | Tan "QD frame" on the stock | 30 × 70 mm tan frame at the stock/receiver junction | the Minimalist has sling slots and a QD point at its front | **the stock's front sling loop and QD socket painted FDE** [VERIFY the Minimalist's QD position] |
| D17 | Buffer tube | "exposed along the whole stock top", 165 mm outside the receiver | a stock at position 3 encloses the tube; 30 mm shows between nut and stock | real; the glossy cylinder along the stock top is the stock's own tube housing |
| D18 | Rail height | drawn ≈ 10 cm off the bore | rail top 1.19 in (30.2 mm) above the bore (2.6 in A2 sight height − 1.41 in co-witness) | **Z +30.2**, receiver and handguard rails coplanar |
| D19 | Gas system | carbine-like block at 190 mm | BCM 16 in uses mid-length: port ≈ 9.0 in from the bolt face | **port at Y 216.4, low-profile block Y 204 … 229**; seen through holes 5–6 |
| D20 | Iron sights | none | real carbines often carry folding BUIS | none (as drawn); `--buis` adds folded Magpul MBUS-class sights (Q8) |
| D21 | Sling | none; QD plate on the stock | — | none; QD sockets in the end plate, the stock and the handguard's left side at Y 250 |
| D22 | Barrel colour under the handguard | dark parkerised | one Cerakote coat covers the whole barrel | bronze, seen only through slots and holes |
| D23 | Markings | — | real parts carry maker roll marks | geometry real; **maker logos replaced by fictional "AR-12" markings** (trademark caution, Q7) |
| D24 | Pistol | icon "P9 Sidearm"; none visible on the body | SIG P226 196 × 140 × 38.1 | appendix only, hidden by default (spec 14's optional holster) |

---

## 3. Real-world reference

Every number below is in the rifle frame R unless a row says otherwise. Positions along the bore are Y; heights are Z (bore = 0); the right face is +X.

### 3.1 The master chain along the bore
| Station | Y (mm) | Tag | Note |
|---|---|---|---|
| Butt-pad heel (top-rear corner of the pad) | −428.6 (at Z +18) | E | pad centre −415 (Z −46), rake 12° toe forward; toe −401.4 (Z −110) |
| Buffer-tube rear end (inside the stock) | −368.0 | S/E | 184 mm mil-spec carbine extension |
| Stock front (tube-housing front face) | −248.7 | S/E | stock 179.9 long, position 3 of 6 |
| Castle-nut rear face / end plate / lower rear face | −220.6 / −210.2 … −207.0 / −207.0 | E | 28 mm of bare tube shows between nut and stock |
| Charging-handle T, rear face | −208.0 | M | CC0 −208.7 |
| Upper receiver rear face | −197.0 | S/M | 7.75 in stripped (listing); CC0 −199 |
| Rear takedown pin | −183 | E | |
| Pistol-grip front strap top | −150 (Z −54) | M | CC0 −151 / −54 |
| Forward-assist button rear face | −150 (Z +7) | E | |
| Trigger face | −122 (Z −68) | M | CC0 −121 … −130 |
| Ejection port (opening) | −96.2 … −20.0 | E/M | projection lands 4 px from the drawn port |
| Magwell outer rear / front | −88 / −10 | M | CC0 −83 … −90 / −10 |
| Pivot pin | −13 | E | |
| Bolt face (closed) | −12.2 | E | barrel tenon 0.620 in (S) inside a flanged extension |
| **Receiver front face (origin)** | **0** | — | barrel-nut and handguard seat |
| Handguard body | +0.5 … +340.9 | S | 13.4 in to the flare |
| Weapon light (tail → bezel) | +10 … +114 | S/E | 104 mm long |
| Left-hand station | +170 | M | spec 08 D5 |
| Gas block | +204 … +229 (port +216.4) | E | mid-length port 9.0 in from the bolt face |
| Barrel shoulder / A2 rear face on its washer | +381.5 / +382.7 | E | |
| Barrel crown | +394.2 | S | 16.0 in from the bolt face |
| **A2 front face (muzzle end, spec 08 pin)** | **+427.2** | S | 1.75 in device; spec 08 used 434 |

Overall length heel → muzzle **855.8 mm (33.7 in)**: between a 16 in carbine's collapsed 794 and extended 876 (research_dimensions §12), as position 3 of 6 should be. Butt-pad centre → muzzle end **843.5 mm** (spec 08 used 849; its two-pin solve re-runs with the new length). Length of pull (trigger face → pad centre) **293 mm (11.5 in)**: a short pull, normal over plate armour.

### 3.2 Upper receiver — BCM M4 forged flat-top (Colt-TDP pattern)
| Feature | Dimension (mm) | Tag |
|---|---|---|
| Length, front face → rear face | 197.0 | S (7.75 in listing) / M (CC0 199) |
| Body width over the side walls | 31.0 (X ±15.5) | E |
| Parting line with the lower | Z −17.0 | E (carrier Ø 25.3 on the bore + 4.4 wall) |
| Rail top | Z +30.2 | S-derived (A2 sight height 2.6 in − absolute co-witness 1.41 in = 1.19 in) / M (CC0 30.6) |
| Receiver rail extent | Y −196.5 … −1.5: 19 full slots plus the joint slot shared with the handguard | E [VERIFY slot count on a Colt-pattern upper] |
| Front threaded ring (barrel-nut thread), hidden under the nut | Ø 31.75 × 15.0 (Y −15.0 … 0) | E |
| Carrier bore | Ø 25.6, Y −197 … −15 | E |
| Gas-tube hole | Ø 4.8 at (0, 0, +10.7) | E |
| **Ejection port opening** | 76.2 × 20.3 (3.00 × 0.80 in), Y −96.2 … −20.0, Z −8.6 … +11.7, corner radius 3.0, front edge relieved 1.0 × 45° | E (D10) |
| **Ejection-port cover** | sheet 78.7 × 23.4 × 1.6 (3.10 × 0.92 in), hinge rod Ø 2.4 (0.093 in) along Y at (X +15.8, Z −11.0), spring hidden; inner latch bump 6 × 4 × 1.5 near the front; outer face flat with a 0.6 mm raised border; **open: rotated 165° about the rod**, lying 0.8 mm off the lower's right face | S (cover size) / E |
| **Brass deflector** | wedge behind the port's rear-top corner, Y −96 … −117, root Z +8 … +22, peak at X +23.0, striking face 40° to the bore | E |
| **Forward-assist housing** | OD 19.0, axis from (X +13.0, Y −96, Z +5) to (X +22.0, Y −140, Z +7): 11° out from the bore in plan, 3° up; outer surface reaches X +31.5 at the rear | E |
| **Forward-assist button** | "round" M4 button Ø 14.0, 12.0 proud of the housing, rear face at Y −150; face with 5 concentric grooves 0.8 wide × 0.4 deep; retaining roll pin Ø 2.4 across the housing at Y −112 | E |
| Takedown lug (rear) / pivot lug (front) | below the parting line to Z −30, Y −176 … −192 / −6 … −22 | E |
| Charging handle (mil-spec) | shaft in the top channel Y −21 … −197; T-handle 29.0 wide × 10.0 deep (Y −198 … −208) × 12.0 tall (Z +12 … +24); latch on the LEFT, 14 × 9 × 4, serrated pad (6 grooves 1.0 pitch), pivot roll pin Ø 1.6 | E (research ≈ 190 × 29 at the latch) |
| T-marks (receiver rail) | white laser etch on the top lands of every second slot, numerals 3.5 tall, "1" at the rear | E [VERIFY position on the part] |
| Material / finish | 7075-T6 forging, bead-blasted, Type III Class 2 hardcoat, black, matte | S (mil-spec) |

### 3.3 MIL-STD-1913 rail profile (receiver and handguard; `scripts/lib/rail1913.py`)
| Feature | Dimension (mm) | Tag |
|---|---|---|
| Top width | 21.2 (0.835 in), top-edge chamfer 0.5 × 45° | S / E |
| Neck width | 15.67 (0.617 in) | S |
| Upper flanks | 45° ± 20′, from the top edge down and in to the neck, 2.77 tall | S |
| Datum separation / datum vertical | 19.0 (0.748 in) / 2.74 (0.108 in) | S |
| Neck straight / lower flare to the spine | 2.2 / 45° out, 2.6 tall (profile height 7.6) | E |
| Recoil slots | 5.23 (0.206 in) wide, **10.01 (0.394 in) pitch**, 3.00 (0.118 in) deep across the full rail width; slot edges broken 0.3 | S / E |
| Spine under the rail (handguard only) | 3.55 tall, 15.67 wide, so that the rail top lies at Z +30.2 over an octagon whose top flat is at Z +19.05 | derived |

### 3.4 Barrel, extension and gas system — BCM 16 in mid-length, government profile
| Feature | Dimension (mm) | Tag |
|---|---|---|
| Barrel length, bolt face → crown | 406.4 (16.0 in) | S |
| Bolt face (closed) | Y −12.2: barrel tenon 0.620 in inside the extension, flange 0.14 in | S (tenon) / E |
| Extension flange (hidden, clamped by the nut) | Ø 25.0 × 4.0, Y 0 … +4.0 | E |
| Profile in front of the nut | Ø 17.1 (0.675 in) at Y +10, tapering to Ø 15.9 (0.625 in) at Y +60 | S (government-profile description) |
| Under the handguard | Ø 15.9, Y +60 … +191 | S |
| Step to the journal | shoulder with a 30° chamfer, Y +191 … +194 | E |
| Gas-block journal and forward section | Ø 19.05 (0.750 in), Y +194 … +381.5 | S |
| Muzzle thread | 1/2-28 UNEF (Ø 12.7 major), Y +381.5 … +394.2 | S thread / E length |
| Crown, bore | 11° target crown; bore Ø 5.56 (grooves 5.69), 1:7 twist, chrome-lined | S |
| Gas port | Ø 1.9 at Y +216.4, 12 o'clock | E (mid-length ≈ 9.0 in from the bolt face, forum) |
| Low-profile gas block | 0.750 in bore, round body Ø 27.0 × 25.0 (Y +204 … +229), gas boss on top to Z +17.0, two 8-32 cup-point set screws at 5 and 7 o'clock (Y +216), black nitride | E |
| Gas tube | Ø 4.57 (0.180 in) stainless, mid-length 301.6 (11.875 in), axis Z +10.7, from Y +222 (in the block) to Y −79.6 (in the carrier key); roll pin Ø 1.6 through block and tube | E [VERIFY length] |
| Barrel nut (BCM proprietary steel) | Ø 32.0 × 28.0, Y −14 … +14, hidden inside the handguard | E |
| Finish | Cerakote H-148 Burnt Bronze over the factory phosphate, barrel and A2 together; block nitride black | D3, D22 |

### 3.5 Bolt carrier group — BCM M16 profile (only what the open port shows)
| Feature | Dimension (mm) | Tag |
|---|---|---|
| Carrier | Ø 25.3 bearing sections, front face at Y −26 in battery; seen through the port from Y −20 to −96 | E |
| Bolt head | Ø 18.0, extractor claw visible at the port's front lower corner (Y −24, Z −6), 7 lugs hidden | E |
| Forward-assist notches | 14 serrations on the carrier's right side, 1.6 pitch × 0.6 deep, Y −70 … −92, Z −3 … +3 | E |
| Bearing bands | the carrier's raised rails, 3.0 wide at Z +9 and Z −9 on the right side | E |
| Finish | manganese phosphate, dark grey; the bearing bands polished to bright steel by the receiver (the drawn glint at Y −42) | E (D10) |

### 3.6 Lower receiver — BCM M4 forged lower (mil-spec)
| Feature | Dimension (mm) | Tag |
|---|---|---|
| Length, magwell front → buffer-boss rear | 197 (Y −10 … −207) | E (listings 197–216; CC0 ≈ 207) |
| Body width (fire-control pocket walls) | 32.0 (X ±16.0) | S (research: ≈ 32 wide) |
| Bottom surface behind the magwell | Z −54, Y −88 … −150 (trigger slot 8.5 wide through it) | M (CC0 −54) |
| Magwell outer | 27.6 wide; front edge Y −10, rear edge Y −88; bottom lip raked 6°: Z −76.5 at the front, −84.0 at the rear | M (CC0) / E |
| Magwell opening | 67.0 × 23.0, through to the receiver | E (PMAG 66 × 22 + clearance) |
| **Flared lip** | the bottom 9 mm flares outward 2.0 all round (outer 31.6 × 82), lip edge radius 1.5 | E (prototype: "wants 2 mm more depth") |
| Magwell side pockets (forging reliefs) | 44 × 22 × 1.0 deep, corner radius 6, both sides, centred Y −49, Z −50 | E (prototype) |
| **Mag-release button** | Ø 9.5, face with 12 radial serrations, 1.5 proud of the fence; centre (+16.0, −74, −38) | M (2.8 px) / E (size) |
| Mag-release fence | raised arc 3.0 tall, 2.5 wide, around the button's lower and rear sides (outer radius 11) | E |
| Pivot pin / takedown pin heads (right side) | Ø 9.5 × 1.5 domed heads, shafts Ø 6.35 (0.250 in); at (Y −13, Z −24) / (Y −183, Z −24) | E |
| Trigger and hammer pin ends | Ø 3.9 (0.154 in), flush, at (Y −110, Z −42) / (Y −128, Z −33) | E [VERIFY order] |
| Bolt catch (left) | paddle 24 × 11 × 3, ribbed, pivot roll pin Ø 3.2 at (X −15, Y −84, Z −22) | E |
| Selector (left) | lever 26 × 7 on a Ø 9.5 boss at (X −16, Y −150, Z −30); right side: axle end Ø 7 flush with a scribed indicator line | E |
| **Trigger guard** (mil-spec aluminium) | bar 6.5 × 4.5 section, inside opening 60 × 26, bottom at Z −88; front ear pinned by a Ø 3.2 roll pin at (Y −90, Z −58); rear resting in the grip's front lug at (Y −150, Z −58) | S (≈ 60 × 32 opening, 6 thick) / E |
| **Trigger** (mil-spec) | curved blade 6.4 wide, face radius 30, polished face, lowest point Z −80; face at Y −122 (Z −68) | M (CC0) / E |
| Grip boss | the lower's rear underside is cut on the grip's mating plane, perpendicular to the 25° grip axis, from (Y −150, Z −54) up to (Y −207, Z −27.4); grip screw 1/4-28 × 1.75 in socket head from inside the grip | E |
| Buffer boss | Ø 35.6 ring, Y −184 … −207, threaded 1.185 in (1 3/16-16 UN) for the extension | S (thread) / E |
| Material / finish | 7075-T6 forging, bead-blasted, Type III Class 2 hardcoat, black | S (mil-spec) |
| Markings | left magwell: fictional "AR-12" maker block, serial, "CAL 5.56 mm"; left selector: SAFE / SEMI; right side: none | D23 |

### 3.7 USGI A2 pistol grip
| Feature | Dimension (mm) | Tag |
|---|---|---|
| Height along its axis | 102 | S (Brownells "about 4 in"; Magpul MOE 102) |
| Rake | 25° from the receiver normal, bottom toward the butt | E (spec 05/08) |
| Top section | 55 front-to-back × 30.5 wide, corner radius 8 | E (spec 05) |
| Bottom section | 45 × 28; bottom open (hollow core, wall 2.5), the grip screw seated inside | E |
| **Finger nub** | on the front strap, 22 below the top, 3.5 proud, 18 wide, blended over 12 | E (spec 05) |
| Front and back straps | diamond checkering, 1.2 pitch, 0.3 deep | E |
| Sides | fine pebble 0.4 | E |
| Material | glass-filled nylon, black | E |

### 3.8 Handguard — BCM MCMR-13
| Feature | Dimension (mm) | Tag |
|---|---|---|
| Overall length (to the flare) | 340.4 (13.4 in): body Y +0.5 … +340.9 | S |
| Top rail | 13.0 in nominal; built continuous over the body | S / E [VERIFY rail start] |
| Width across the 3–9 o'clock flats | 38.1 (1.50 in) | S |
| Inside diameter | 33.0 (1.30 in) | S |
| Section | regular octagon 38.1 across flats centred on the bore (bevels 15.78 wide; wall 2.55 at the flats) + 1913 rail on a 3.55 spine → height 49.3 | E |
| Rear flare collar | rear 10.0 of the body, outer +0.8, edge 1 × 45° | E |
| Front end | square face, all eight edges chamfered 3.0 × 45°; the rail's last tooth chamfered 1 × 45° | E |
| **M-LOK slots** | 3, 6 and 9 o'clock faces; 32.0 × 7.0, corner radius 2.38, 40.0 pitch (8.0 web); 8 per face at Y 14–46, 54–86, 94–126, 134–166, 174–206, 214–246, 254–286, 294–326; rims chamfered 0.5 × 45° | S (M-LOK) / E (positions) |
| **Lightening holes** | Ø 10.0, 26.0 pitch, 4:30 and 7:30 bevels, 7 per bevel, centres Y 105, 131, 157, 183, 209, 235, 261; rims 0.4 × 45° | M (positions) / E (D6) |
| QD socket | 9 o'clock face at Y 250 (between slots 6 and 7): steel insert, flange Ø 14.0 × 1.0, bore Ø 9.5 with a 1.6 detent groove | E (D21) |
| Clamp to the barrel nut | two socket-head screws at 5 and 7 o'clock, Y +6, heads Ø 7.0 in counterbores | E [VERIFY] |
| Index | rail rear end abuts the receiver rail (0.5 gap) | S |
| T-marks | continuing the receiver's numbering on even slots | E |
| Material, finish, mass | 6061-T6, Type III Class 2 hardcoat black; 232 g + 65 g hardware | S |

### 3.9 Muzzle device — A2 birdcage
| Feature | Dimension (mm) | Tag |
|---|---|---|
| Overall length / diameter | 44.5 (1.75 in) / 21.8 (0.86 in) | S |
| Internal thread | 1/2-28, 12.7 deep | S / E |
| Crush washer | 1.2 compressed, OD 21.8, ID 12.8 | E |
| Rear body | 19.0 long, two wrench flats 19.05 (3/4 in) across at 3 and 9 o'clock | E |
| **Ports** | 5 slots 2.6 wide × 18.0 long at 0°, ±60°, ±120° from the top; the 120° bottom sector closed | S (5 ports, closed bottom; research note, uncited) / E |
| Front ring | 5.5 long, mouth Ø 15.0, the bullet hole Ø 6.6 visible at the cage floor | E |
| Mass | 85 g | S |
| Finish | Cerakote H-148 Burnt Bronze; soot from each slot forward and on the front ring | D3 |

### 3.10 Weapon light — SureFire M300C Mini Scout, on an Arisaka Offset Scout Mount (M-LOK)
| Feature | Dimension (mm) | Tag |
|---|---|---|
| Length | 104 (4.1 in) | S |
| Bezel | Ø 28.6 (1.125 in), 24.0 long (Y +90 … +114), front edge radius 0.8 | S / E |
| Head taper | cone from Ø 28.6 down to the body over 14 (Y +76 … +90) | E |
| Body | Ø 22.0, 42 long (Y +34 … +76), with a flat mounting pad 12 wide underneath carrying two tapped holes 20 apart | E [VERIFY body diameter] |
| Tail cap (Z68) | Ø 24.0 × 24 (Y +10 … +34); fine diamond knurl over Y +13 … +28 (0.8 pitch, 0.3 deep); rubber click button Ø 13 inside a protective shroud (two ears 3.0 high) | S (Z68, shroud) / E |
| Window and optic | tempered flat window Ø 24.0; behind it a TIR optic (cone 24 → 8 over 12) and the LED die | S (TIR) / E |
| Mass / output | 116 g / 500 lm, 7600 cd (emissive off) | S |
| Mount | 6061 plate < 5.1 (0.20 in) thick, three lateral positions over 6.1 (0.240 in); M-LOK foot with two T-nuts in slot 1 of the 3 o'clock face (Y 14 … 46); 45° arm; pad bolted to the light's two holes | S (thickness, positions) / E |
| **Placement** | light axis (X +32, Z +16) ≈ 2 o'clock; Y +10 (tail) … +114 (bezel face) | E (D8) |
| Clearances | bezel to the 1:30 bevel ≥ 0.5; light top Z +30.3 (level with the rail top, as drawn); bezel face to the left thumb ≥ 20 (thumb at Y ≥ 137) | derived |

### 3.11 Receiver extension, castle nut, end plate, stock and butt pad
| Feature | Dimension (mm) | Tag |
|---|---|---|
| Receiver extension | OD 29.16 (1.148 in) mil-spec; 184 long (7.25 in), Y −184 … −368; bottom rib 6.5 wide × 3.0 deep with 6 position holes Ø 4.8 at 16.5 pitch | S (OD, length) / E |
| QD end plate | steel, 3.2 thick, ring Ø 38 with a tab down to Z −30 carrying a QD socket boss Ø 16 on each side; two staking dents into the castle nut | E |
| Castle nut | Ø 36.0 × 10.4; 3 spanner notches 4.8 × 3.2 at 120°; black | E [VERIFY notch count] |
| Bare tube between nut and stock | Y −220.6 … −248.7 | derived |
| **MFT BATTLELINK Minimalist (MIL-SPEC)** | 179.9 L × 132.6 H × 44.5 W (7.084 × 5.22 × 1.752 in), 164 g (5.8 oz); fits 1.148 in tubes | S |
| Its outline (position 3) | tube housing top Z +20.6 from Y −248.7 to −428.6; large window: top edge Y −272 … −396 at Z −8, bottom edge Y −290 … −388 at Z −78, corner radii 8; lower strut 12 thick from the toe (Y −401, Z −110) forward and up to the front lug; front lug (latch housing + sling loop) Y −249 … −282, Z −12 … −94 | E (photographs as remembered + the drawing's proportions) [VERIFY against a catalogue photograph] |
| Housing | tube channel ID 29.6, wall 3.2, flattened cheek top 30 wide | E |
| Latch lever | under the housing front, 32 × 8, pivot at Y −258 | E |
| QD socket | steel insert Ø 14 with a Ø 9.5 bore in the front lug's right face at (Y −266, Z −60) | E (D16) |
| **Butt pad** | rubberised, face 128 × 40, raked 12° toe-forward, 6 horizontal grooves 1.5 wide × 0.8 deep, 8 thick over the frame | S (angled, rubberised) / E |
| Position | 3 of 6 (two clicks out from collapsed); pad centre (0, −415, −46) | E (D15) |

### 3.12 Optics
| Feature | Option A: Aimpoint Micro T-2 + LRP mount + 39 mm spacer | Option B: Aimpoint CompM4 on its mount |
|---|---|---|
| Size | 68 L × 41 W × 36 H; 84 g sight, 105 g with mount (S) | 120 L; 53 × 60 sight; 72 × 72 with mount; 265 / 335 g; 38 mm objective (S) |
| Optical axis | 39.0 above the rail top → Z +69.2 (S) | 72 mm tall with mount: axis ≈ Z +68 (E) |
| Placement | mount clamp centred Y −140; sight Y −174 … −106 (D9) | Y −105 … +15 (the icon's position over the receiver front) |
| Features | cylindrical body Ø 30 with an 18 mm objective (E); elevation cap on top and windage cap on the right (Ø 13 × 7, E); rotary brightness knob on the right (E); battery cap on the left (E); flat front and rear lenses with an amber-red reflection at the rear and a blue-green one at the front (E); LRP lever-release clamp, recoil lug in one rail slot (S lever release; E rest) | long tube with a front objective bell, rear eyepiece, side battery and switch, high mount with a throw lever (E) |

### 3.13 Magazine — Magpul PMAG 30 AR/M4 GEN M3 (MAG557), Stealth Gray
| Feature | Dimension (mm) | Tag |
|---|---|---|
| Maximum length / depth / thickness | 190.5 (7.5 in) / 66.0 (2.6 in) / 22.1 (0.87 in) | S |
| Mass | 146 g empty, 503 g with 30 rounds | S |
| Body in the magwell | 63.0 × 21.4, straight for the top 72 | E |
| Constant curve | below the magwell the spine follows R 400 for 104 mm of arc, so the floorplate is tilted 14.9° forward | S (constant-curve geometry) / E (radius; CC0 14°) |
| Seating | feed lips at Z −14.5; body perpendicular to the bore down to the magwell lip | M (CC0) |
| Floorplate | "flared": 1.3 beyond the body all round, 6.0 thick, front corner radius 8, rear disassembly dimple Ø 5 | S (flared) / E |
| Ribs | 3 low longitudinal ribs per side, 2.4 wide × 0.8 proud, over the lower 95 | S ("low profile ribs") / E (count, D14) |
| Front and rear texture | diamond 1.5 pitch on the spine and the rear face | S / E |
| Dot-matrix panel | 15 × 40 grid of 0.8 dots, both sides, lower body | S / E |
| Bolt-catch notch / over-travel stop | rear top / 2.0 bump on the spine at the magwell lip | S |

### 3.14 Mass and balance (sanity check for `measure_rifle()`)
Estimated loaded mass **3.2–3.4 kg**:
- upper group with barrel, MCMR and A2: ≈ 1.45 kg (E);
- lower with grip: ≈ 0.48 kg (E);
- tube, buffer, spring, nut and plate: ≈ 0.26 kg (E);
- stock: 0.164 kg (S);
- M300C: 0.116 kg (S);
- T-2 with mount: 0.105 kg (S);
- loaded PMAG: 0.503 kg (S).

Spec 08's centre-of-mass sum used 3.6 kg; 3.3 kg is the better figure. The balance point is ≈ 30 mm in front of the magwell, at Y ≈ +20 (E).

### 3.15 Sources (opened for this spec or by the research notes)
- SureFire M300C (length, bezel, mass, Z68, TIR, M75): https://www.surefire.com/m300c/
- MFT BATTLELINK Minimalist MIL-SPEC (7.084 × 5.22 × 1.752 in, 5.8 oz, angled rubberised pad, sling slots, QD): https://www.primaryarms.com/mission-first-tactical-battlelink-minimalist-stock-commercial-scorched-dark-earth-bmssde (and the MIL-SPEC listings beside it)
- BCM MCMR-13 (13.4 in to the flare, 1.5 in wide, 1.3 in ID, 8.2 oz + 2.3 oz, Type III Class 2, steel nut indexed to 12 o'clock, low-profile gas block): https://bravocompanyusa.com/bcm-mcmr-13-m-lok-compatible-modular-rail/ and https://www.primaryarms.com/bcm-13-mlok-compatible-modular-rail-bcm-mcmr-13-556-blk
- MCMR lengths available (7, 8, 9, 10, 13, 15 in): retailer listings via search
- Magpul PMAG 30 GEN M3 data sheet (low profile ribs, front and rear texture, dot matrix, flared floorplate, constant curve, bolt-catch notch, over-travel stop): https://magpul.com/media/wysiwyg/GIS/MAG557_PMAG_30_AR_M4_GEN_M3_GIS_01.pdf
- PMAG dimensions: research_dimensions §12 (trex-arms, copsplus listings)
- A2 flash hider 1.75 in (KAK, Rosco listings): https://brownells.co.uk/556-NATO-A2-BIRDCAGE-FLASH-HIDER-FOR-AR-15-KAK-INDUSTRY-LLC-556-NATO-A2-BIRDCAGE-FLASH-HIDER-1-2X28-FOR-AR-15-Black-Steel-22-Caliber-223-224-1-2-28-430113026
- A2 flash hider, 0.86 in diameter, 85 g: research_dimensions §12
- Government profile (0.675 → 0.625 under the handguard, 0.750 from the gas block on): https://www.everydaymarksman.co/?p=320 and https://snipershide.com/shooting/threads/a-visual-library-of-ar-15-barrel-profiles.7106548
- Barrel tenon 0.620 in: https://benchrest.com/forum/threads/ar-15-barrel-tenon.75006
- Gas-port distances (mid-length ≈ 9 in): https://forum.308ar.com/topic/7934-school-me-on-gas-port-locations
- Aimpoint 39 mm spacer: https://www.primaryarms.com/aimpoint-micro-spacer-high-39mm-ar-15
- Aimpoint T-2 size and mass: research_dimensions §12 (tnvc.com)
- Arisaka Offset Scout Mount (< 0.20 in, three positions over 0.240 in, 1:30 placement, M300 compatibility): https://www.bigtexordnance.com/product/arisaka-offset-scout-mount-mlok-picatinny-fits-modlite-surefire-lights/
- Mil-spec buffer tube (1.148 in OD, 1.185 in thread): https://forged-armory.odoo.com/shop/2a-bta6-1-2a-buffer-tube-assembly-ar15-blk-27056
- Luth-AR stripped upper, 7.75 in: https://www.ar15.build/products/upper-receiver/52052/luth-ar-slick-side-a1-st-3fn-upr-odye88-ur-01-e3-s
- From analysis_weapon §2 (Wikipedia and retailer pages): Picatinny and M-LOK dimensions, M4 OAL, CompM4, dust cover 3.10 × 0.92 in, A2 grip ≈ 4 in, P226

### 3.16 Wear — what reality and the picture agree on
A carried, cleaned and repainted service rifle about a year into hard use.
- **Hardcoat:** worn through to grey-silver aluminium only on sharp convex edges that hands, gear and holsters rub. These are:
  - the rail's top edges and tooth corners;
  - the magwell's flared lip;
  - the receiver's parting-line edges;
  - the handguard's 1:30, 4:30 and 10:30 edges where the left hand sits;
  - the front-end chamfer;
  - the deflector's peak;
  - the forward-assist button rim;
  - the charging-handle latch.
- **Paint (tan):** hand-applied over the hardcoat with masking tape. It chips at its edges and wherever it is touched, about 20–30 % lost. The worst chipping is on the upper stripe nearest the charging handle and on the stock frame nearest the receiver.
- **Polish:** steel polished bright by use on the trigger face, the mag-release button, the carrier's bearing bands, the takedown-pin heads and the T-handle's rear edge.
- **Polymer:** scuffs lighter on the stock's cheek area (#5e4f44 → #8d8787 streaks) and on the PMAG's rib crests and floorplate flare.
- **Carbon:** soot blackens the A2's slots, its front ring and the barrel's last 10 mm. It also blackens the inside of the port, the deflector's face (with brass-coloured smears where cases strike it) and the carrier's front.
- **Dust:** warm brown-grey dust settles in the rail slots, the handguard holes and slots, the castle-nut notches, the magwell pockets, and on the up-facing surfaces of the carry. The handguard reads warmer than the receiver because of it.
- **Butt pad:** dusty grey rubber with a clean crescent where it beds against the carrier.
- **Not present:** no rust, no cracks, no missing parts, no tape.

---

## 4. Geometry construction plan

Everything is executed by `scripts/parts/15_carbine.py`, headless:

```
blender -b --python-expr "import sys; sys.stdout.reconfigure(line_buffering=True)" --python scripts/parts/15_carbine.py -- [--optic a|b|none] [--hg-holes image|none] [--buis] [--emissive-panel] [--markings fictional|real|none] [--lod hero|game|both] [--pistol] [--eval]
```

Defaults: `--optic a --hg-holes image --markings fictional --lod both`.

General rules:
- **Idempotent.** The script deletes every object, mesh, material, node group, image and collection whose name starts with `Rifle.` or `Pistol.` before rebuilding.
- **Built in frame R.** `Rifle.Root` sits at the world origin with identity rotation; spec 08's `rifle_place.py` moves it.
- **Logged.** A report line for each object (faces, tris, volume, manifold flag) is written before any render; the .blend (`renders/15_carbine/15_carbine.blend`) is saved before rendering (research_prototypes §0).
- **Booleans.** Hard-surface recipe from research_prototypes §6 and §8: build each part's hull as **one manifold solid** (a single profile extrusion, loft or lathe, or EXACT unions of manifold primitives, never `join` of overlapping shells), then EXACT differences, then Bevel (limit by angle 30°, clamp overlap, harden normals), then Weighted Normal (keep sharp, face-area mode), then shade smooth with `Mesh.set_sharp_from_angle(30°)`.
- **Boolean checks.** Every boolean result is checked: all edges manifold (`bmesh` `is_manifold`), volume within 2 % of the analytic estimate, no face with area < 1e-4 mm². A failure raises and names the operand.
- **Cutter shells.** Disjoint closed cutter shells may share one cutter object. Overlapping ones are unioned first.

### 4.1 Shared helpers (new, reused by specs 12–14 and the pistol)
| Helper | Signature (metres inside, millimetres in the call) | Does |
|---|---|---|
| `hardsurf.extrude(name, profile, axis, a0, a1)` | profile = list of 2D points (closed, CCW), extruded along the named axis | bmesh face → `extrude_face_region` → recalc normals; returns a manifold prism |
| `hardsurf.union(obj, others)` / `difference(obj, cutters)` | EXACT solver, `use_self False`, `use_hole_tolerant False`, applied with `modifier_apply` under `temp_override` | then the checks above |
| `hardsurf.finish(obj, width, segments, angle=30, harden=True)` | Bevel + Weighted Normal + sharp-by-angle | the standard finish |
| `lathe.revolve(name, stations, segments=64, axis='Y', centre=(x, z))` | stations = [(y, r_outer[, r_inner])…], chamfers as extra stations | closed solid of revolution with caps |
| `rail1913.make(name, y0, y1, z_top, spine=0, phase_y, chamfer_front=True)` | phase_y = Y of one slot centre so that all rails share one pitch | sweeps the **full** profile on every land and the **slot-floor** profile in every slot (no booleans, all quads); slot edges broken 0.3 by two extra loops; returns the rail and a list of land Ys (for T-marks) |
| `mlok.cutters(face_frame, y_centres, depth)` | slot 32 × 7, r 2.38, 16 segments per corner | one multi-shell cutter object |
| `hardsurf.knurl(r, y0, y1, pitch=0.8, depth=0.3, segs=192)` | diamond knurl band | cylinder grid whose radius is lowered by the max of two crossed triangle waves |

### 4.2 Step 1 — frames, pins and anchors (`Rifle.Root` and its empties)
Empties, all children of `Rifle.Root`, display size 20 mm:

| Empty | Location (R, mm) | Axes | For |
|---|---|---|---|
| `Rifle.Root` | (0, 0, 0) | R | spec 08 places it |
| `Rifle.Pin.Butt` | (0, −415, −46) | — | spec 08 two-pin solve |
| `Rifle.Pin.Muzzle` | (0, 427.2, 0) | — | spec 08 two-pin solve |
| `Rifle.GripFrame` | (0, −169.0, −94.8) | +Z up the grip (0, 0.4226, 0.9063); −Y out of the front strap (0, 0.9063, −0.4226); +X = (−1, 0, 0) | spec 05 right hand (D13) |
| `Rifle.HandguardFrame` | (0, 170, 0) | +Y to the muzzle, +Z to the rail, +X right | spec 05 left hand |
| `Rifle.Anchor.IndexFace` | (+16.0, −100, −46) | normal +X | spec 05: index pad plane (lower's right face above the guard) |
| `Rifle.Anchor.ThumbRail` | (0, 165, 30.2) | normal +Z | thumb across the rail |
| `Rifle.Anchor.FingerFacet` | (+13.47, 165, −13.47) | normal (0.7071, 0, −0.7071) | fingertips under the 4:30 bevel (spec 11: 0.3 mm) |
| `Rifle.Anchor.Light`, `.Optic`, `.Mag` | (32, 10, 16), (0, −140, 30.2), (0, −49, −14.5) | — | the moving or optional parts' origins |

### 4.3 Step 2 — upper receiver body (`Rifle.Upper.Body`)
1. **Cross-section hull.** XZ profile extruded along Y −15 … −197, one manifold prism. Points, right half, mirrored for the left:
   - (15.5, −17.0)
   - (15.5, +12.0)
   - chamfer 45° to (11.0, +16.5)
   - (11.0, +22.6), the rail base.
2. **Front threaded ring.** `lathe.revolve`: Ø 31.75, Y −15 … 0, 64 segments, front edge chamfer 0.8. UNION.
3. **Lugs.** Pivot lug: box X ±6.3, Y −8 … −20, Z −17 … −30, lower corners rounded r 3. Takedown lug: box X ±6.3, Y −176 … −190, Z −17 … −30. UNION.
4. **Forward-assist housing.** Capped cylinder OD 19.0, 48 segments, from (13.0, −94, 5) to (22.0, −140, 7). UNION. Its front end buries itself in the right wall; the later 30° bevel turns the intersection into a 0.8 mm fillet.
5. **Brass deflector.** Convex hull (`bmesh.ops.convex_hull`) of (15.5, −96, 8), (15.5, −117, 8), (15.5, −96, 22), (15.5, −117, 22), (23.0, −104, 16), (21.5, −114, 14). UNION.
6. **Port-cover hinge bosses.** Two 6 × 4 × 4 lugs on the right wall below the port, Y −15 … −21 and −95 … −101, centred at Z −11. UNION.
7. **Differences** (one cutter object per line):
   - carrier bore: Ø 25.6 cylinder along Y −200 … −13;
   - port: rounded rectangle 76.2 × 20.3, r 3.0, at Y −96.2 … −20.0, Z −8.6 … +11.7, extruded from X 0 to +20;
   - front-edge relief: 1 × 45° wedge along the port's front edge;
   - charging-handle channel: 9.6 wide × 8.0 tall, Y −21 … −200, Z +12.6 … +20.6;
   - forward-assist bore: Ø 14.2 along the forward-assist axis, from its rear face to the carrier bore;
   - gas-tube hole: Ø 4.8 along Y at Z +10.7 through the ring;
   - pin holes: Ø 6.35 along X through the lugs at (Y −13, Z −24) and (Y −183, Z −24);
   - hinge-rod hole: Ø 2.45 along Y at (15.8, ·, −11) through both bosses;
   - forward-assist roll-pin hole: Ø 2.4 along X through the housing at Y −112.
8. **Finish.** `hardsurf.finish(width 0.6, segments 3)`. Expected ≈ 9 k tris.

### 4.4 Step 3 — rails (`Rifle.Upper.Rail`, `Rifle.Handguard.Rail`)
`rail1913.make`:
- receiver rail Y −196.5 … −1.5, z_top 30.2, spine 0, sitting on the body's top flat at Z +22.6;
- handguard rail Y +0.5 … +340.9, z_top 30.2, spine 3.55.

Both take one phase: slot centres at **Y = −0.5 + 10.01 k**. The 2.0 mm joint between the rails (Y −1.5 … +0.5) therefore falls inside one slot (Y −3.115 … +2.115): the pitch runs unbroken from the receiver's rear to the handguard's front and no sliver land is left at the joint. No other slot is cut within 3 mm of a rail end. This gives the receiver rail 19 full slots plus the joint slot, and the handguard rail 33 full slots plus the joint slot and an 8.5 mm front land; the generator reports the counts.

The front land gets a 1 × 45° chamfer. Each rail is unioned to its body; if the union fails the checks, it stays a separate object with a 0.1 mm overlap. Expected ≈ 5 k tris (receiver rail) and ≈ 9 k (handguard rail).

### 4.5 Step 4 — moving parts of the upper
- **`Rifle.Upper.DustCover`.**
  - Sheet: rounded rectangle 78.7 × 23.4, r 2.0, `Solidify` 1.6.
  - Hinge curl: a C-section tube (OD 3.6, ID 2.45, 270°) along its lower edge.
  - Latch bump: 6 × 4 × 1.5 box on the inner face, 8 from the front.
  - Raised border: 0.6 tall × 1.2 wide strip around the outer face.
  - Origin on the hinge axis (15.8, −58.1, −11.0); open = rotate 165° about +Y so that it hangs against the lower.
  - Spring: a 4-turn coil (curve, bevel 0.4, pitch 1.2) round the rod, Y −22 … −27.
  - Hinge rod: Ø 2.4 × 84 cylinder (`Rifle.Upper.HingeRod`).
  - ≈ 1.5 k tris.
- **`Rifle.Upper.FAButton`.** `lathe.revolve` Ø 14.0 × 12; five concentric face grooves 0.8 wide × 0.4 deep as lathe stations; rear rim 0.4 chamfer. Roll pin ends: Ø 2.4 discs flush in the housing at Y −112, both sides (`Rifle.Upper.FAPin`). ≈ 1.2 k tris.
- **`Rifle.ChargingHandle`.**
  - T-handle: top-view outline (29 × 10 with 2 mm radii) extruded Z +12 … +24; a 0.8 × 45° chamfer on the rear top edge.
  - Shaft: box 9.0 × 175 × 7.6 in the channel, mostly hidden.
  - Latch (left, `Rifle.ChargingHandle.Latch`): outline 14 × 9 extruded 4; six 0.5 × 0.4 grooves on its pad.
  - Roll pin Ø 1.6 through the latch.
  - Origin at (0, −208, +18). ≈ 2 k tris.
- **`Rifle.BCG`.**
  - Carrier: lathe Ø 25.3 from Y −26 to −198.
  - Bearing rails: two 3.0-wide bands 0.4 proud at Z ±9 on the right.
  - Forward-assist notches: 14 wedge cutters, 1.6 pitch × 0.6 deep, at Y −70 … −92, DIFFERENCE.
  - Bolt head: lathe Ø 18 from Y −12.2 to −26.
  - Extractor: box 4 × 22 × 3 on the bolt's right at Z −2, its claw 1 mm proud of the face.
  - Origin at (0, −12.2, 0). ≈ 4 k tris.

### 4.6 Step 5 — lower receiver (`Rifle.Lower.Body`) and its small parts
1. **Hull** (UNION chain of manifold pieces):
   - (a) **Pocket body.** YZ side profile extruded X ±16.0: (−88, −17), (−207, −17), (−207, −27.4), (−150, −54), (−88, −54). The edge (−150, −54) → (−207, −27.4) is the grip's mating plane, perpendicular to the 25° grip axis.
   - (b) **Magwell loft** through rounded rectangles (r 3), each perpendicular to Z. The lip sections are raked 6° by shifting their Z with Y:
     - Z −17: Y −10 … −88, width 27.6;
     - Z −72: same;
     - lip top (Z −75.5 front … −83.0 rear): width 27.6;
     - lip bottom (Z −76.5 front … −84.0 rear): Y −8 … −90, width 31.6 (the outer flare).
   - (c) **Buffer boss.** `lathe.revolve` Ø 35.6 from Y −197 to −207, centred on the bore (it rises above the parting line behind the upper).
   - (d) **Ears.** Front ears X ±6.4 … ±12.7, Y −8 … −20, Z −17 … −32; rear ears X ±6.4 … ±12.7, Y −176 … −190, Z −17 … −32 (both straddle the upper's lugs).
   - (e) **Trigger-guard front ears.** Two plates 3.0 thick at X ±4.8, Y −86 … −94, Z −54 … −62.
   - (f) **Mag-release fence.** A 3.0-tall, 2.5-wide arc of outer radius 11 standing on the magwell's right face (X +13.8) round the button's axis (Y −74, Z −38), covering its rear and lower sides (from 12 to 6 o'clock through 9 as seen from the right, the rear being toward −Y).
   - (g) **Left bosses.** Bolt-catch boss (left magwell top, 14 × 10 × 2) and selector boss (Ø 14 × 1.5 on the left at (−16, −150, −30)).
   - (h) **Grip boss.** A 10 mm-deep pad on the raked mating plane round the grip-screw hole, so that the grip's top section (55 deep) lands flush from (−150, −54) to (−199.8, −30.8).
2. **Differences:**
   - magazine opening 67.0 × 23.0, r 2, from Z −10 to −75 (perpendicular to the bore);
   - mouth frustum from 67 × 23 at Z −75 to 71 × 27 at the lip bottom (the inner flare);
   - side pockets 44 × 22 × 1.0, r 6, both sides, centred (Y −49, Z −50), with a 0.8 floor fillet;
   - trigger slot 8.5 × 46 through the bottom at Y −98 … −144;
   - pin holes Ø 6.35 (ears) and Ø 3.9 (trigger and hammer);
   - mag-catch window 4 × 9 on the right magwell wall at (Y −66, Z −40);
   - buffer bore Ø 30.1 from Y −207 forward 23;
   - grip-screw hole Ø 6.6 up through the pad.
3. **Finish.** `hardsurf.finish(0.8, 3)`. Expected ≈ 11 k tris. Prototype check: the side faces must stay dark; edge wear comes from the shader's Bevel-node mask, never from Pointiness.
4. **Small parts** (separate objects, `hardsurf.finish(0.3, 2)` each):

| Object | Construction | Tris |
|---|---|---|
| `Rifle.Lower.PinPivot`, `.PinTakedown` | lathe: domed head Ø 9.5 × 1.5 (a 0.4 pull groove on the takedown head) + shaft Ø 6.35 through + flush left end with a detent groove | 0.6 k each |
| `Rifle.Lower.PinTrigger`, `.PinHammer` | Ø 3.9 × 32 cylinders, 0.3 chamfered ends flush both sides | 0.2 k each |
| `Rifle.Lower.MagRelease` | lathe Ø 9.5 × 5.5 (1.5 proud of the fence), domed 0.5; 12 radial V-cutters 0.6 wide × 0.4 deep on the face; origin on its axis (16.0, −74, −38); the catch bar inside is omitted | 0.8 k |
| `Rifle.Lower.BoltCatch` (left) | paddle outline extruded 3, four 0.6 ribs; roll pin Ø 3.2 ends flush in the boss | 0.6 k |
| `Rifle.Lower.Selector` (left) + `.SelectorEnd` (right) | lever outline 26 × 7 extruded 3.5 on a Ø 9.5 hub; right end disc Ø 7 with a 0.3 indicator groove | 0.8 k |
| `Rifle.Lower.Trigger` | side outline (curved blade, face radius 30) extruded 6.4, all edges bevelled 0.6; origin on the trigger pin | 0.6 k |
| `Rifle.Lower.TriggerGuard` | rounded rectangle 6.5 × 4.5 swept along the 8-point polyline (−90, −58) → (−92, −72) → (−98, −86) → (−110, −88) → (−136, −88) → (−146, −82) → (−150, −68) → (−150, −58) (prototype recipe, Subsurf 1); front roll pin Ø 3.2 (`.GuardPin`) | 1.5 k |
| `Rifle.Lower.GripScrew` | socket-head cap 1/4-28, head Ø 9.5 × 6.4 with a 4.8 hex, seen inside the grip's open bottom | 0.4 k |

### 4.7 Step 6 — A2 pistol grip (`Rifle.Grip`)
1. **Spine.** The grip axis starts at the top section's centre (0, −174.9, −42.4), 27.5 mm behind the front-strap top along the section, and runs 102 mm down and back at 25° (direction (0, −0.4226, −0.9063)). The front strap's top is (0, −150, −54) and `Rifle.GripFrame` lies 45 mm down the strap at (0, −169.0, −94.8).
2. **Loft.** Nine sections along the axis (0, 12, 22, 32, 45, 60, 75, 90, 102 mm from the top). Each is a superellipse with exponent 2.6:
   - top section 55 × 30.5, bottom section 45 × 28, linear in between;
   - the front strap is pushed out by a Gaussian bump of 3.5 at 22 mm (σ 6): the finger nub;
   - the back strap curves to a 6 mm "beaver tail" lip at the top rear.
3. **Top.** Cut by the lower's grip plane (DIFFERENCE with a half-space box).
4. **Bottom.** Open: an inner offset loft (wall 2.5) differenced from the bottom up to 70 mm, so the screw head sits visible in the hollow.
5. **Finish.** `hardsurf.finish(1.2, 3)` then `Subdivision` level 1 (render 2) with creases 1.0 on the top plane edges. The checkering is in the material (§5). ≈ 6 k tris at render.

### 4.8 Step 7 — receiver extension, castle nut, QD end plate
- **`Rifle.Stock.Tube`.**
  - `lathe.revolve` Ø 29.16 from Y −197 to −368, rear edge radius 1.5.
  - Bottom rib: box 6.5 × 3.0, Y −220 … −368, UNION.
  - Six position holes Ø 4.8 at Y −262.1, −278.6, −295.1, −311.6, −328.1, −344.6, DIFFERENCE (the stock's latch sits in the third from the front).
  - ≈ 1.5 k tris.
- **`Rifle.Stock.CastleNut`.** `lathe.revolve` Ø 36.0 × 10.4 (Y −210.2 … −220.6), 0.6 chamfers; three spanner notches 4.8 wide × 3.2 deep at 120° (0° = top), DIFFERENCE. ≈ 1.2 k tris.
- **`Rifle.Stock.EndPlate`.**
  - Outline: ring Ø 38 / ID 30.2 + a tab 12 wide hanging to Z −30, extruded 3.2 (Y −207.0 … −210.2).
  - QD socket bosses: cylinders Ø 16 × 10 on each side of the tab at Z −24, with a Ø 9.5 bore and a 1.6 detent groove.
  - Staking dents: two 2 × 2 × 1 dents into the castle nut's rear face at the 5 and 7 o'clock positions, made as matching bumps on the plate's lip.
  - ≈ 1.5 k tris.

### 4.9 Step 8 — MFT Minimalist stock (`Rifle.Stock.Body`, `Rifle.Stock.Pad`, `Rifle.Stock.Latch`)
1. **Tube housing.** A loft along Y −248.7 … −425 of a section that is a circle Ø 36.0 with its top flattened to a 30 mm-wide cheek flat at Z +20.6. Inner channel Ø 29.6 (DIFFERENCE), open at the front.
2. **Skeleton plate.** The side outline of §3.11 extruded X ±9.0 (18 thick), from the housing's underside down to the strut and the front lug. Outline points, in order:
   - (−252, −12), front-top
   - (−252, −94), front lug bottom
   - (−282, −94)
   - lower strut: (−282, −94) to (−401, −110), 12 thick
   - (−401, −110), toe
   - (−428.6, +18), heel, along the 12° pad plane
   - (−425, +14)
   - closing along the housing.

   UNION with the housing. DIFFERENCE the window: trapezoid top edge (−272 … −396, Z −8), bottom edge (−290 … −388, Z −78), corner radii 8, through all.
3. **Front lug details.**
   - Sling loop: a 25 × 6 vertical through-slot at Y −266 … −291, X ±9.
   - QD socket: steel insert `Rifle.Stock.QD`, lathe Ø 14 flange × 1.0 + Ø 9.5 bore with its detent groove, at (+9.0, −266, −60).
   - Latch lever `Rifle.Stock.Latch`: outline 32 × 8 extruded 10 under the housing front, pivot at Y −258, a 6-groove finger pad.
4. **Butt pad (`Rifle.Stock.Pad`).** Rubber slab, outline 128 × 44.5 with r 6 corners, 8.0 thick, lying on the 12° plane through (−415, −46).
   - Six horizontal grooves 1.5 wide × 0.8 deep across the face.
   - Face slightly convex: 1.5 crown across its width.
   - Edges rounded with `hardsurf.finish(1.5, 3)` + Subdivision 1.
5. **Polymer finish.** `hardsurf.finish(1.5, 3)` + Subdivision 1 (render 2), creases on the window rim's outer edge. ≈ 12 k tris at render.

### 4.10 Step 9 — barrel, gas block, gas tube, barrel nut
- **`Rifle.Barrel`.**
  - `lathe.revolve`, 64 segments, through the stations of §3.4 from Y +4 to +394.2: flange edge, Ø 17.1 → Ø 15.9 taper, step with its 30° chamfer, Ø 19.05 run, thread section Ø 12.7 under the A2, crown.
  - Crown: an 11° cone into the Ø 5.56 bore, the bore 30 deep.
  - Gas port: Ø 1.9 radial hole at Y +216.4 (hidden).
  - ≈ 3 k tris.
- **`Rifle.GasBlock`.**
  - Lathe body Ø 27.0 × 25.0 (Y +204 … +229).
  - Gas boss on top: 12 wide box to Z +17.0, with the tube bore Ø 4.6 at Z +10.7.
  - Two set screws `Rifle.GasBlock.SetScrew.*`: Ø 4.2 cylinders with 2.4 hex sockets, sunk 0.5 in counterbores at 5 and 7 o'clock, Y +216.
  - Roll pin Ø 1.6 across the boss.
  - ≈ 2 k tris.
- **`Rifle.GasTube`.** Curve object, straight from (0, +222, 10.7) to (0, −79.6, 10.7) with a 6 mm S-bend 30 mm behind the block (rise 1.0). `bevel_depth` 2.285, `bevel_resolution` 4, `resolution_u` 12; converted to a mesh at build time. ≈ 1 k tris.
- **`Rifle.BarrelNut`.** Lathe Ø 32 × 28 (Y −14 … +14), hidden but present so the slots show metal behind them.

### 4.11 Step 10 — handguard (`Rifle.Handguard.Body`, `.QD`, `.ClampScrew.*`)
1. **Section.** One bmesh face with a hole:
   - outer regular octagon, 38.1 across flats, rotated so that its flats face 12, 3, 6 and 9 o'clock;
   - plus the top spine (15.67 wide, from Z +19.05 to +22.6);
   - inner circle Ø 33.0 at 64 segments;
   - outer and inner loops bridged into one ring face.

   Extrude along Y +0.5 … +340.9 with loop cuts at every 10 mm. One manifold tube.
2. **Rear collar.** Scale the last 10 mm loop outward by 0.8, 1 × 45° edge.
3. **Front chamfer.** `bmesh.ops.bevel` on the eight outer front edges (offset 3.0, segments 1), done **before** the booleans.
4. **M-LOK slots.** `mlok.cutters` on the 3, 6 and 9 o'clock faces at Y centres 30, 70, 110, 150, 190, 230, 270, 310, depth 8. That is 24 shells in one object; one DIFFERENCE.
5. **Lightening holes** (`--hg-holes image`). 14 cylinders Ø 10.0 (32 segments) along the 4:30 normal (0.7071, 0, −0.7071) and the 7:30 normal (−0.7071, 0, −0.7071), centred on each bevel at Y 105 … 261 step 26. One DIFFERENCE.
6. **QD socket.**
   - Counterbore Ø 14 × 1.0 + Ø 9.5 through on the 9 o'clock face at Y 250, DIFFERENCE.
   - Insert `Rifle.Handguard.QD`: lathe, steel, with its 1.6 detent groove.
7. **Clamp screws.**
   - Counterbores Ø 7.0 × 2.0 + Ø 4.2 through at 5 and 7 o'clock, Y +6, DIFFERENCE.
   - Socket-head cap screws M4 × 12 (head Ø 7.0 × 4.0, hex 3.0), sunk 0.3.
8. **Rail.** Union the handguard rail from Step 3.
9. **Finish.** `hardsurf.finish(0.5, 2)`: this makes the 0.5 × 45° rims of the M-LOK slots that catch the key at the drawn "screw" pixels (D7). ≈ 32 k tris with the rail.

### 4.12 Step 11 — A2 birdcage and crush washer (`Rifle.Muzzle.A2`, `Rifle.Muzzle.Washer`)
- **A2.**
  - Lathe stations, Y from +382.7: rear face Ø 21.8 with a 0.5 chamfer; body to +401.7; slot band +401.7 … +421.7 at Ø 21.8; front ring +421.7 … +427.2 with a 0.6 front chamfer.
  - Interior: Ø 12.7 threaded bore from the rear, 12.7 deep (thread as a bump texture); a rear wall with a Ø 6.6 hole at +396.0; cage interior Ø 15.0 from +398.0 to the front.
  - Wrench flats: two DIFFERENCE boxes leaving 19.05 across at 3 and 9 o'clock, Y +382.7 … +397.
  - Ports: five boxes 2.6 wide × 18.0 long × 12 deep, radial at 0°, ±60°, ±120° from the top, Y +402.7 … +420.7, ends rounded r 1.3. DIFFERENCE.
  - `hardsurf.finish(0.3, 2)`. ≈ 3 k tris.
- **Washer.** Lathe ring OD 21.8 / ID 12.8 × 1.2, Y +381.5 … +382.7, outer edge rounded 0.3.

### 4.13 Step 12 — weapon light and mount (`Rifle.Light.*`, `Rifle.LightMount.*`)
All light parts are built on a local axis Y, then the assembly is moved so that the axis runs through (32, ·, 16), parallel to the bore, Y +10 … +114.

| Object | Construction | Tris |
|---|---|---|
| `Rifle.Light.Body` | lathe: tail cap Ø 24.0 at +10 … +34 (rear edge radius 1.0) → body Ø 22.0 to +76 → cone up to Ø 28.6 at +90 → bezel Ø 28.6 to +114, front edge radius 0.8; the bezel's inner bore Ø 24.0, 2.0 deep. Mounting pad: box 12 × 40 × 3 under the body at its local 7 o'clock (facing the mount), two Ø 3.5 tapped holes 20 apart | 3 k |
| `Rifle.Light.Knurl` | `hardsurf.knurl(r 12.0, +13 … +28, pitch 0.8, depth 0.3)` on the tail cap, 192 × 20 grid | 6 k |
| `Rifle.Light.Tailcap.Button` + `.Shroud` | rubber button: lathe Ø 13 × 3 with a 0.5 dimple; shroud: two arc ears, each 70° of a Ø 24 ring, 3.0 tall, at 12 and 6 o'clock of the tail | 1 k |
| `Rifle.Light.Window` + `.TIR` + `.LED` | flat glass disc Ø 24 × 2 recessed 1.5; TIR cone (glass) Ø 24 → 8 over 12 behind it; LED a 3 × 3 × 0.5 tile (emissive off) | 0.5 k |
| `Rifle.LightMount.Plate` | Arisaka-style plate 5.0 thick: foot 40 × 20 on the 3 o'clock face → 45° arm → pad under the light; outline extruded then the arm bent by `bmesh.ops.bend`-equivalent (two extrusions joined at 45°), `hardsurf.finish(0.6, 2)` | 1 k |
| `Rifle.LightMount.Screw.*` | 4 button-head screws (two M-LOK, two to the light), heads Ø 8.5 × 2.5 with 3 mm hex; the two T-nuts inside the slot (hidden) | 0.6 k |

Clearance checks are asserted, not assumed:
- BVH distance from the bezel to the handguard ≥ 0.5;
- light top ≤ Z +30.5;
- no overlap with the rail's land volume;
- the light's front ≥ 20 mm from `Rifle.Anchor.ThumbRail` along Y.

### 4.14 Step 13 — optic (`Rifle.Optic.*`, by `--optic`)
**Option A (T-2 on the LRP mount with the 39 mm spacer).**

| Object | Construction | Tris |
|---|---|---|
| `Rifle.Optic.Mount` | clamp base 45 × 30 × 9 on the rail at Y −162 … −117, its recoil lug (5.0 × 15 × 3) dropped into one slot; throw lever (outline 38 × 9 extruded 4) on the left; 39 mm spacer block 30 × 41 rising to the sight's base; two cross screws Ø 5 visible on the right | 2.5 k |
| `Rifle.Optic.Body` | lathe tube Ø 30 × 54 on the axis Z +69.2, Y −174 … −106 with lens recesses 2.5 deep; integral base block 41 × 30 × 10 under it | 3 k |
| `Rifle.Optic.Turret.Elev` / `.Wind` | lathe caps Ø 13 × 7 with 24 flutes 0.6 deep, top (12 o'clock) and right (3 o'clock); tethers omitted | 2 k |
| `Rifle.Optic.Knob` | brightness knob Ø 16 × 6 on the right rear, 20 flutes, raised index dot | 1.2 k |
| `Rifle.Optic.BatteryCap` | Ø 20 × 5 on the left, coin slot 1 × 12 × 0.8 | 0.6 k |
| `Rifle.Optic.Lens.Front` / `.Rear` | flat glass discs Ø 20 × 2 | 0.2 k |

**Option B (CompM4).** Lathe tube 120 long (objective bell Ø 45 front, body Ø 30, eyepiece Ø 38 rear), side battery and switch box, high QRP2-style mount (72 mm total height, throw lever on the right), axis at Z +68. About 10 k tris.

**Folded BUIS** (`--buis`). Two Magpul MBUS-class bodies, each 12 mm tall folded: the rear at Y −190 on the receiver rail, the front at Y +330 on the handguard rail. Each is an outline extrusion plus its rail clamp. About 2 k tris.

### 4.15 Step 14 — magazine (`Rifle.Mag.Body`, `Rifle.Mag.Floorplate`)
1. **Spine.** Straight from (Y −49, Z −14.5) down to (−49, −86.5); then an arc of R 400 curving forward (centre at Y +351, Z −86.5) for 104 mm of arc. The end tangent is tilted 14.9°.
2. **Body loft.** 24 rounded-rectangle sections (r 3 front, r 2 rear) along the spine: 63.0 × 21.4 at the top → 66.0 × 22.1 at the bottom. The front spine is a semicircular nose of r 4.
3. **Feed-lip region (hidden).** The top 8 mm narrows to the lips (body 17 wide) with the follower inside (a tan block, never seen).
4. **Ribs.** Three per side, each a 2.4 × 0.8 rounded strip lofted along the body's lower 95 mm at 25 %, 50 % and 75 % of the depth; ends tapered over 6. UNION.
5. **Bolt-catch notch.** 4 × 12 × 6 at the rear top, DIFFERENCE.
6. **Over-travel stop.** 2.0 × 8 × 10 bump on the spine at Z −86, UNION.
7. **Finish.** `hardsurf.finish(0.8, 3)` + Subdivision 1 (render 2). Origin at the top centre (0, −49, −14.5), so `Rifle.Anchor.Mag` drives a reload.
8. **Floorplate.** Rounded slab 68.6 × 24.7 × 6.0, front corner r 8, rear r 4, bottom crowned 1.0, flared 1.3 beyond the body with a 0.6 lip under the body's last section; rear dimple Ø 5 × 1.0; fictional text recessed 0.3 (no Magpul logo, D23). Placed on the spine's end tangent, its top 0.2 below the body's last section so that no gap shows.

About 10 k tris for the body and floorplate together. Texture panels and the dot matrix are in the material (§5.2).

### 4.16 Step 15 — markings and T-marks (`scripts/lib/decal.py`, no painting)
- **Mask generation.** Markings are masks, not geometry. The script places Blender Text objects (DejaVu Sans Bold, sizes below) in a temporary scene, renders them with an orthographic Workbench camera to 16-bit PNG masks (`assets/generated/rifle_mark_*.png`, 40 px/mm), then deletes them.
- **Sampling.** The material samples each mask through object-space box mapping of the part (the decal's projection axis is ±X).

| Marking | Where | Text / size |
|---|---|---|
| Rail T-marks | top lands of every 2nd slot, receiver and handguard, numbered from the rear | "1", "3", "5" … 3.5 tall, white etch |
| Lower left magwell | X −14.2 face | fictional maker block "HELIX ARMS AR-12" 4.0, "CAL 5.56 mm" 3.0, serial "HX 0417 3" 3.0 |
| Selector markings | left, round the selector | "SAFE" / "SEMI" 2.5, white-filled |
| Barrel | top, Y +230 (under the handguard, seen through the top-right slot only) | "5.56 NATO 1/7" 2.0 stamp, depth 0.1 (bump) |
| Magazine floorplate | bottom | "AR-12 30RD" 3.0 recessed (geometry, step 14) |

`--markings real` substitutes the real makers' marks for reference renders only; `--markings none` drops them.

### 4.17 Step 16 — collider, proxy and game LODs
- **`Rifle.Collider`.** EXACT union of closed, simplified hulls, then `Decimate` (collapse) to ≤ 8 k faces; no bevel; `hide_render`; display wire. Members:
  - the handguard octagon (no slots or holes) with the rail as a solid 21.2-wide trapezoid prism to Z +30.2;
  - the upper and lower hulls without the port, pockets or slots;
  - the grip loft at 12 sections × 24;
  - the trigger guard sweep;
  - the magazine loft at 10 × 16;
  - the stock housing and plate (window kept);
  - the light and optic as cylinders.

  Vertex groups: `Rifle.Contact.Grip`, `.LowerRight` (index finger), `.Handguard`, `.Rail` (thumb), `.Pad` (butt), used by specs 05, 08 and 11. Its surface must lie within 0.3 mm of the hero surfaces in those groups (checked, §8.2).
- **`Rifle.Proxy`.** ≤ 2 k tris: boxes and cylinders of the main volumes; spec 13 uses it as `Rifle.StandIn`.
- **`Rifle.LOD0`** (game, ≤ 20 k tris). Rebuilt by the same steps with:
  - bevels at 1 segment;
  - no pins, screws, knurl, ribs or grooves (these go to the normal map);
  - slots, holes, port and window kept as geometry because they shape the silhouette;
  - Smart UV Project (angle 66°, island margin 0.004) packed into one 4096² sheet at ≈ 9 px/mm.

  Normal, ORM and albedo are baked from the hero meshes (cage extrusion 1.5 mm).
- **`Rifle.LOD1`** (≤ 6 k tris). Decimate (planar 5°) of LOD0, sharing its maps. The magazine, light and optic stay separate meshes in both LODs, so they can be swapped.

### 4.18 Topology and poly budget (hero, evaluated, after bevel and subdivision)
| Assembly | Objects | Budget (tris) |
|---|---|---|
| Upper (body + rail + cover + hinge + forward assist + charging handle + BCG) | 9 | 24 k |
| Lower (body + 12 small parts) | 13 | 18 k |
| Grip | 1 | 6 k |
| Tube, nut, plate | 3 | 4 k |
| Stock, pad, latch, QD | 4 | 14 k |
| Barrel, gas block, tube, nut | 6 | 7 k |
| Handguard (with rail, QD, screws) | 5 | 34 k |
| A2 + washer | 2 | 3.5 k |
| Light + mount | 8 | 12 k |
| Optic A (B ≈ 10 k) | 7 | 10 k |
| Magazine | 2 | 10 k |
| **Total** | **≈ 60** | **≈ 143 k (ceiling 180 k)** |

Flat faces may stay as n-gons in the hero (Weighted Normal shades them correctly). Curved faces are quads. No triangle is longer than 40 mm on a curved surface (it would facet under the rim light), and lathe parts use 64 segments (48 under Ø 10).

### 4.19 Origins, parenting and joins
- **Parenting.** Every rifle object is parented to `Rifle.Root` with `matrix_parent_inverse` identity, so its local and R coordinates coincide.
- **Origins.** Static parts keep their origin at R's origin. Moving parts carry their pivot as origin: dust cover (hinge axis), trigger (trigger pin), selector (its axis), mag release (its axis), bolt catch (its roll pin), charging handle (0, −208, +18), BCG (0, −12.2, 0), magazine (0, −49, −14.5), light (32, 10, 16), optic (0, −140, 30.2).
- **Joins.** Nothing is joined in the hero file (each object keeps one material where possible, so masks stay simple). The game export joins per material and per moving part (§7.3).

---

## 5. Materials and textures

All materials come from `scripts/lib/mat_hard.py` (shared with specs 12–14). Base colours are **starting values in linear RGB**, to be calibrated by rendering (§5.5); the reference hexes are what the hero render must show, not albedos.

### 5.1 Material slots
| Slot | Used on | Base colour (linear) | Metallic | Roughness | Layers and notes |
|---|---|---|---|---|---|
| `Rifle.Mat.Anodised` | upper, lower, rails, handguard, trigger guard, light mount, optic mount | (0.024, 0.022, 0.021) | 0.75 | 0.48 (noise 0.42–0.58, 30 mm) | bead-blast bump (noise 4000 /m, 0.05 mm, strength 0.2); low-frequency "thinning" toward (0.06, 0.055, 0.05) on large flats (prototype §6); edge wear → bare 7075/6061 (0.60, 0.59, 0.57), metallic 1.0, roughness 0.30, through `Wear.EdgeBevel`; etch masks (§4.16) → (0.20, 0.20, 0.19), roughness 0.60 |
| `Rifle.Mat.Hardcoat.Gloss` | receiver extension, light body and head, optic body | (0.018, 0.017, 0.017) | 0.60 | 0.32 tube / 0.40 light / 0.36 optic | the same edge wear at half strength; the light's bezel lip and tail-cap ears worn bright |
| `Rifle.Mat.Steel.Phosphate` | BCG, barrel nut, castle nut, end plate, pins, roll pins, set screws, gas block (nitride), grip screw | (0.040, 0.040, 0.042) | 0.85 | 0.55 | polish zones → (0.55, 0.55, 0.56), metallic 1, roughness 0.18: BCG bearing bands, pin heads, trigger face, mag-release face, T-handle rear edge |
| `Rifle.Mat.Steel.Blued` | socket screws (clamp, light mount), QD inserts | (0.045, 0.050, 0.060) | 1.0 | 0.30 | specular tint (0.6, 0.7, 1.0): the "blue-tinted specular" of the analysis, real on blued steel |
| `Rifle.Mat.Cerakote.Bronze` | barrel, A2, washer | (0.135, 0.082, 0.050) | 0.45 | 0.38 | Cerakote H-148 Burnt Bronze: fine metallic flake (Voronoi 0.08 mm, roughness ±0.06); soot layer (0.012, 0.011, 0.010), roughness 0.85; edge wear to the dark phosphate under it on the A2's flats and front ring |
| `Rifle.Mat.Polymer.Black` | stock body, latch, grip | (0.030, 0.028, 0.026) | 0 | 0.55 | micro grain (noise 3000 /m, 0.1 mm); grip checkering on the straps (two crossed Wave textures in object space, 1.2 mm pitch, bump 0.3 mm) and pebble on the sides (0.4 mm); stock scuff streaks → (0.10, 0.09, 0.085), roughness 0.42, anisotropic noise (Mapping scale 1 : 1 : 14 along Y) on the cheek flat and housing |
| `Rifle.Mat.Polymer.Grey` | PMAG body, floorplate | (0.075, 0.072, 0.068) | 0 | 0.60 | diamond texture panels front and rear (1.5 mm, bump 0.25); dot matrix (0.8 mm dots, bump 0.15); rib crests and floorplate flare scuffed → (0.15, 0.14, 0.13), roughness 0.45 |
| `Rifle.Mat.Rubber` | butt pad, light button | (0.020, 0.019, 0.018) | 0 | 0.78 | grain noise 2500 /m, 0.1 mm; sheen 0.03 (never above 0.15 on dark, prototype §0) |
| `Rifle.Mat.Paint.FDE` | paint patches P1–P6 (§5.4), layered on top of whatever material is under them | (0.479, 0.279, 0.115) = #b8905f | 0 | 0.62 | hand-brushed streaks along each patch's long axis (anisotropic noise 1 : 1 : 10, ±0.04 value); orange peel (noise 900 /m, 0.15 mm); chips reveal the material under them, each chip edge bumped 0.08 mm so it catches light |
| `Rifle.Mat.Glass` | light window and TIR, optic lenses | white, transmission 1.0 | 0 | 0.02 | IOR 1.52; optic front lens: thin film 300 nm (IOR 1.38) → blue-green reflection; rear lens: thin film 520 nm → amber; TIR cone roughness 0.05 |
| `Rifle.Mat.Emissive.Blue` | `--emissive-panel` only (D11) | #80a8c2 | — | — | 2 W/m², recessed 60 × 20 panel; off by default |

### 5.2 Maps and texture sets
- **Hero (Cycles).** Fully procedural in **object space** (Texture Coordinate → Object, so the 1 mm scales stay true on every part). No image textures, except the decal masks of §4.16 and the downloaded micro-detail sets:
  - `Metal038` normal at 0.15 strength for the anodised micro-structure (75 cm tile → 1 : 1 scale);
  - `Metal050C` as the bare-edge reference colour;
  - `Rubber004` for the pad;
  - `Plastic012B` grain for the black polymer.

  All are in `assets/textures`, per research_assets.
- **UVs.** Smart UV Project (angle 66°, margin 0.004) on every hero object, used only for bakes. On LOD0 one packed 4096² sheet for the whole rifle at ≈ 9 px/mm (the receivers, handguard and stock need ≈ 15 Mpx at that density). Magazine, light and optic share a second 2048² sheet.
- **Game bakes** (`--lod game`), at 16 spp from the hero meshes: albedo (diffuse colour), ORM (AO, roughness, metallic) and tangent-space normal (cage 1.5 mm). Masks are baked with the hero lighting off. Bake cost ≈ render cost per texel (research_blender_capabilities §10): budget ≈ 6 min on this machine.

### 5.3 Wear masks (shared node groups in `mat_hard.py`)
| Node group | Recipe | Applied where |
|---|---|---|
| `Wear.EdgeBevel` | Cycles Bevel node (radius 0.8 mm, 4 samples) → `1 − dot(bevel normal, true normal)` → Map Range 0.0–0.08 → × noise break-up (2 mm, contrast 3) → × `Wear.Touch` boost. **Never Pointiness** on boolean meshes (prototype §6) | all hard materials |
| `Wear.Touch` | sum of spherical falloffs (radius 25–40 mm) around the contact anchors: grip and index face (right hand), handguard station Y 125–215 on the 10:30, 12 and 1:30 facets (left hand), rail top under the thumb, magwell lip (reloads), charging-handle latch, mag-release button, pad heel | raises edge wear ×1.8 and paint chipping ×2; drives polish on steel |
| `Wear.Chips` | Voronoi F1 (cell 2.5 mm) thresholded hard at 0.62 (≈ 25 % coverage) ∪ `Wear.EdgeBevel` > 0.3 ∪ hairline scratches (noise with anisotropic mapping 1 : 1 : 14, threshold 0.68) → chip mask; per patch the coverage target of §5.4 sets the threshold | FDE paint only |
| `Wear.Dust` | (AO 16 mm < 0.6) × 0.6 + (normal · rifle +Z)⁺ × 0.3 + (normal · world +Z in the hero pose)⁺ × 0.2, broken by noise 6 mm; colour (0.30, 0.26, 0.21), roughness 0.9, max coverage 35 % | rail slots, handguard holes and slots, castle-nut notches, magwell pockets, tops; the handguard gets ×1.3 (it reads warmer, §2.3) |
| `Wear.Grime` | AO 4 mm < 0.4 → darkening ×0.6, roughness −0.05 (oil) | inside the port, slot floors, hole bores, trigger slot |
| `Wear.Carbon` | distance-from-source gradients: forward of each A2 slot (cone 15°, 25 mm), the A2 front ring and the barrel's last 10 mm; the port's rear edge and the deflector's face; the bolt's face and extractor; colour (0.012, 0.011, 0.010), roughness 0.85 | bronze, anodised, phosphate |
| `Wear.Brass` | two smears 6 × 3 mm, (0.35, 0.24, 0.08), metallic 1, roughness 0.35, on the deflector's striking face | deflector only |
| `Wear.Scuff` | anisotropic streaks along Y, coverage 15 %, lighter and glossier | stock cheek flat, PMAG ribs, floorplate flare |

### 5.4 Paint patches (FDE, `Rifle.Mat.Paint.FDE` layered by mask)
Each patch is a rounded-rectangle mask (corner radius 1.5, edge softness 0.2 mm, a masking-tape edge) projected along ±X onto the parts it covers, so that it wraps the forward-assist housing or slot rims exactly as a spray stripe would.

| Patch | Where (R) | Size (mm) | Chip coverage | Drawn reference |
|---|---|---|---|---|
| P1 stock stripe | stock housing, lower right flank, Y −310 … −380, Z −12 … −22 | 70 × 10 | 25 % | (718, 281) #a68869 |
| P2 stock front frame | front lug's right face round the QD socket and sling loop, Y −252 … −282, Z −22 … −92; 4.0-wide band, interior unpainted | 30 × 70 outer | 30 %, worst nearest the receiver | (741, 330) #bf9c70, interior #86694f |
| P3 upper stripe | upper's right side, Y −198 … −113, Z +8 … +18, over the forward-assist housing | 85 × 10 | 25 %, worst over the rear 20 mm (charging-handle hand) | (767, 342) #d4a271 |
| P4 lower patch | magwell's upper right face in front of the fence, Y −24 … −64, Z −30 … −45 | 40 × 15 | 20 % | (774, 390) #736456 |
| P5 magwell dab | magwell's front-right lower corner, centre (Y −17, Z −70) | Ø 10 with a Ø 4 chipped centre | 35 % | (792, 417) #8d764b |
| P6a / P6b handguard patches | 3 o'clock face, Y +14 … +34 (under the light mount's foot) and Y +55 … +75, full face height | 20 × 15.8 each | 25 % | (799, 408) #312e28 (in shade) / (809, 426) #685840 |

### 5.5 Calibration (before any shader is judged)
Render the swatch board under the **evaluation** lighting (hero lights, AgX Medium High Contrast, `analysis_consolidated.md` §8) next to a grey card, as research_prototypes §0 requires. The board is `scripts/eval/rifle_swatches.py`: a flat, a 45° bevel and a cylinder per material. Adjust base colour (never more than ×2) until the lit flat reads the §5.6 target within ΔE2000 3, then freeze the values in `mat_hard.py`. Expected outcome from the prototypes: "black" hardcoat lands near 0.02–0.03 albedo, the tan at about 0.3–0.45.

### 5.6 Hex targets in the hero render (V1, 5 × 5 means at the projected pixel of the named feature)
| Feature | Target | Tolerance (ΔE2000) |
|---|---|---|
| Upper receiver flat, median | #413c3b | 6 |
| Upper worn edge | #686463 | 8 |
| Lower receiver, median / darkest | #403c39 / #262321 | 6 |
| Handguard right face, median / lit | #393532 / #5e5040 | 6 |
| Hole interiors / between holes | #2b2927 / #0d0a08 | 6 |
| Rail rim-lit (cool side light) | #697b97 | 8 |
| Stock body / lit cheek / butt | #3d3733 / #5e4f44 / #141211 | 6 |
| Tube highlight / peak | #b5b0b1 / #ece7e9 | 8 |
| FDE upper stripe lit / stock stripe / stock frame | #d4a271 / #a68869 / #bf9c70 | 8 |
| Magazine median / rib crest / floorplate | #423e3a / #625a56 / #595452 | 6 |
| Barrel and A2 (bronze), lit | #5f4c3e (to #6a5344) | 8 |
| Light body / highlight | #302f30 / #8f8b84 | 6 |
| Mag-release button glint | #676261 (peak ≥ #c0bbbb) | 8 |

---

## 6. Fibres, simulation or dynamics

None. The rifle is rigid metal and polymer: no cloth, no hair, no particles, no soft body. There is no sling, cable or lanyard (the M300C has a click tail cap, so there is no pressure-switch cable). Dust, carbon and scuffs are shader masks (§5.3), not particles. The only "dynamics" are the articulated parts of §7.3, posed by rotation or translation about the origins of §4.19. Their **hero states** are:
- dust cover open 165°;
- trigger forward (finger off it);
- selector on SAFE (lever horizontal, pointing to the rear);
- bolt closed;
- charging handle home;
- mag-release out;
- bolt catch down.

---

## 7. Rigging and attachment

### 7.1 Placement in the character frame (spec 08 owns the solve)
`rifle_place.py` (spec 08 §4.8) reads the pins from the empties **`Rifle.Pin.Butt` (0, −415, −46)** and **`Rifle.Pin.Muzzle` (0, 427.2, 0)**, not from typed numbers. The solve:
- puts the butt pad in contact with `Vest.Collider.RightPectoral` at 0–3 mm;
- puts the muzzle on pixel (903, 570) at the depth that makes the pin distance 843.5 mm (was 849);
- rolls the rifle until +X_R faces the camera.

Expected result within 1° of spec 08's present transform: bore ≈ W (0.44, −0.47, −0.77), 50° below horizontal, 43° to his left of the camera axis, muzzle ≈ 0.68 m above the floor. The analysts' looser reading (56° in the image plane, 25° toward the camera, 690 mm) is the same pose seen without depth. After the solve, `rifle_overlay.py` (§8.3) checks the frames:
- `Rifle.GripFrame` lands at (724, 368) ± 6 px (spec 08's present tolerance (727, 352) must change, D13);
- `Rifle.HandguardFrame` lands at (840, 467) ± 8 px.

### 7.2 Hand contacts (consumed by specs 05, 08, 11)
| Contact | Rifle object / anchor | Rule |
|---|---|---|
| Right palm, middle/ring/little fingers | `Rifle.GripFrame`; `Rifle.Collider` group `Rifle.Contact.Grip` | spec 05 IK and `close_finger()` with `contact_offset` 1.5 (spec 11): gloved pulp 0.3 ± 0.3 mm from the grip, no penetration |
| Right index (straight, off the trigger) | `Rifle.Anchor.IndexFace` (+16.0, −100, −46), plane X = +16.0 between Y −95 and −150, Z −30 … −52 | pad within 1.5 mm of the lower's right face, above the trigger guard (bottom Z −88) and below the fence; tip 25 mm short of and 15 mm below the mag release, i.e. near (16, −99, −53) |
| Left palm | `Rifle.HandguardFrame` (0, 170, 0); the 10:30 bevel's centre line (−13.47, Y, +13.47) | palm on the 10:30 bevel and the 12 o'clock flat beside the rail |
| Left thumb | `Rifle.Anchor.ThumbRail` (0, 165, 30.2) | pulp on the rail top lands (21.2 wide); the glove cap folds 15° over the rail's right edge (X +10.6); thumb tip ≥ 20 mm forward of the light's bezel face (Y 114) |
| Left fingertips | `Rifle.Anchor.FingerFacet` (+13.47, 165, −13.47) | four tips under the 4:30 bevel at 27 mm pitch from Y ≈ 125, gloved caps 0.3 mm off the facet; they may sit over lightening holes 2–5, which is fine |
| Butt pad | `Rifle.Contact.Pad` | 0–3 mm from `Vest.Collider.RightPectoral` |

Section changes the hands must absorb (spec 05 §3.8, spec 08 §3.5, spec 11 §10.1):
- the handguard is **38.1 × 49.3**, not 45 × 55: the C-clamp closes ≈ 7 mm further round;
- the grip is 19 mm lower and 25 mm further forward (D13);
- there is nothing under the handguard between Y 125 and 260 except the lightening holes (spec 11's 150–250 zone is clear).

### 7.3 Parenting, game rig and export
- **Hero file.** All `Rifle.*` objects are children of `Rifle.Root`. After spec 08's bake, `Rifle.Root` is bone-parented to `wrist.R` (spec 08 §4.8) with `matrix_parent_inverse` set so nothing moves.
- **Game rig `Rifle.Rig`.** An armature that is a child of `Rifle.Root`. Bones, each moving one rigidly weighted object (100 %):

| Bone | Head (R, mm) | Axis / motion | Range |
|---|---|---|---|
| `rifle_root` | (0, 0, 0) | — | — |
| `mag` | (0, −49, −14.5) | translate −Z_R (drop) | 0 … 200 |
| `bcg` | (0, −12.2, 0) | translate −Y_R | 0 … 82 (carrier stroke, E) |
| `charging_handle` | (0, −208, 18) | translate −Y_R | 0 … 70 (E) |
| `dust_cover` | (15.8, −58.1, −11.0) | rotate about +Y | 0 … 165° |
| `trigger` | trigger pin | rotate about X | 0 … 12° |
| `selector` | selector axis | rotate about X | 0 / 90° |
| `mag_release` | its axis | translate −X | 0 … 3 |
| `bolt_catch` | its roll pin | rotate about Y | 0 … 8° |

- **Export.** `--lod game` writes `export/rifle_ar12.glb` (LOD0 + LOD1 as separate meshes, the rig, the two texture sets) with the hero state as the rest pose. Spec 08/18 attach it in Godot as a `BoneAttachment3D` child of `wrist.R`, carrying the game scale factor 1.80 / 1.855 = 0.970 like the body (the rifle scales with the man so that the hands still close on it).

### 7.4 Clearances against other parts (checked in the hero pose, §8.4)
| Pair | Requirement | Source |
|---|---|---|
| Butt pad ↔ carrier | 0–3 mm contact | spec 08 |
| Light, mount and handguard ↔ carrier PALS rows 6–7 | 20–40 mm, no contact | spec 13 §10 |
| Magazine floorplate ↔ belt buckle and abdomen | ≥ 10 mm (drawn ≈ 15 cm in front of the lower abdomen; real position is further from the body, D14) | consolidated §7 |
| Muzzle ↔ left thigh / kneepad | ≥ 150 mm | consolidated §7 |
| Optic A ↔ chin and gaiter | ≥ 60 mm | spec 06 / 10 |
| Rifle ↔ left forearm guard | ≥ 3 mm | spec 12 |

---

## 8. Evaluation protocol

### 8.1 Renders (one Blender process at a time; report lines written and the .blend saved before rendering)
| When | Views | Engine and settings | Time on this machine |
|---|---|---|---|
| After every geometry step | V2, V3, V4 (+ the step's closeup) | Workbench, matcap + cavity + outline, 2048 wide, a 10 mm grid overlaid by `rifle_views.py --grid` | ≈ 5 s each |
| After materials | V5–V11 | Cycles 128 spp, adaptive 0.02, OIDN, 2048² (V5 3000 × 2000), look-dev lighting | 2–4 min each |
| Acceptance | V1 hero, rendered with a border to the crop (630, 230)–(950, 570) | Cycles 256 spp, hero lights and grading of `analysis_consolidated.md` §8, the body and gear if built, else their proxies; an object-index pass for `Rifle.*` | ≈ 4 min |
| Icon check | V12 | Workbench silhouette, black on white | 5 s |

Every render is opened and looked at before a step is called done (`CLAUDE.md` rule 3).

### 8.2 Dimension readback (`scripts/lib/measure.py::measure_rifle()` → `renders/15_carbine/readback.json`)
All values are measured on the evaluated meshes by ray casts and bounding boxes in frame R, never read back from the script's own parameters.

| Quantity | Target (mm) | Tolerance | Method |
|---|---|---|---|
| OAL heel → muzzle; pad centre → muzzle | 855.8; 843.5 | ±3; ±2 | extremes along Y; pin empties |
| Upper / lower length | 197.0 / 197.0 | ±1 | bounding boxes |
| Rail top height (10 stations along Y) | 30.2 | ±0.2; straightness ≤ 0.1 | rays −Z from Z +60 |
| Rail pitch over 10 slots; slot width; slot depth | 100.10; 5.23; 3.00 | ±0.2; ±0.05; ±0.05 | ray hits along Y at Z +29.9 |
| Rail top width; neck width | 21.2; 15.67 | ±0.1 | rays along X at Z +29.9 and +27.0 |
| Handguard width, height, length | 38.1, 49.3, 340.4 | ±0.2, ±0.3, ±1 | rays and bounding box |
| M-LOK slot size and pitch | 32.0 × 7.0; 40.0 | ±0.2; ±0.2 | rays in the face planes |
| Lightening holes (`--hg-holes image`) | Ø 10.0 at 26.0 | ±0.2 / ±0.3 | rays along the bevel normals |
| Port opening, position | 76.2 × 20.3 at Y −96.2 … −20.0 | ±0.5; ±1 | rays −X at X +20 |
| Dust cover sheet, open angle | 78.7 × 23.4; 165° | ±0.3; ±2° | bounding box in its local frame |
| Barrel diameters at Y 30, 120, 200, 300, 380 | 16.9, 15.9, 19.05, 19.05, 19.05 | ±0.1 | ring rays |
| A2 length and diameter; slots | 44.5, 21.8; 5, none in the bottom 120° | ±0.3, ±0.1 | rays; angular scan at Y +412 |
| Light length, bezel; axis position | 104.0, 28.6; (32, 16) | ±1, ±0.2; ±0.5 | bounding box in the light frame |
| Magazine max length, depth, thickness | 190.5, 66.0, 22.1 | ±2, ±1, ±0.3 | oriented bounding box |
| Grip height along its axis; rake | 102; 25° | ±1; ±1° | principal axis |
| Stock L × H × W | 179.9 × 132.6 × 44.5 | ±1 / ±1 / ±0.5 | bounding box |
| Tube OD | 29.16 | ±0.05 | ring rays |
| Mass (volumes × densities: 7075 2.81, 6061 2.70, steel 7.85, glass-filled nylon 1.35, rubber 1.2 g/cm³; magazine as 503 g) | 3.3 kg | ±15 % | mesh volumes (hollow parts as modelled) |
| `Rifle.Collider` vs hero surface in the contact groups | ≤ 0.3 | max | BVH nearest |

### 8.3 Projection check (`scripts/eval/rifle_overlay.py`)
After spec 08's solve, the script projects every landmark of §2.2 through the hero camera and reports two numbers per landmark:
- the error to its **predicted real pixel**: must be ≤ 6 px; the pins ≤ 4;
- its distance to the **drawn pixel**: informational; must match §2.2's error column within ±5 px. If it does not, the geometry has drifted toward or away from the drawing in a way nobody decided.

It also writes three images:
- `overlay_hero.png`: the V1 crop at ×3, 50 % over `crop_hands_rifle.png`, Sobel edges of the render in cyan and of the reference in magenta, green crosses at predicted pixels and red at drawn ones;
- `iou.png`: the render's `Rifle.*` object-index mask against the reference rifle polygon. The polygon is 40 vertices digitised from the analysts' landmarks and stored in `scripts/eval/rifle_ref_polygon.json`. IoU must be ≥ 0.75, computed outside the accepted-deviation zones: light, magazine below the magwell, handguard front 40 mm, rail band, receiver rear;
- `colour_patches.png`: §5.6 with ΔE2000 per patch.

### 8.4 Contacts and clearances
- Every pair in §7.4 is checked by BVH distance in the hero pose; failures name the pair and the gap.
- The hands' contact reports of specs 05 and 11 must pass against `Rifle.Collider`: pulp 0.3 ± 0.3 mm, penetration 0, index pad ≤ 1.5 mm from `Rifle.Anchor.IndexFace`, thumb pulp ≤ 1 mm from the rail top.
- The magazine must sit with ≤ 0.5 mm gap and no penetration against the magwell walls (rays from the magazine's four faces at Z −20 and −80).

### 8.5 Clean geometry
- Zero non-manifold edges on every boolean result.
- Zero faces under 1e-4 mm².
- Consistent outward normals (a ray-parity test from 200 random interior points).
- Pairwise BVH overlap between rifle objects zero except on the allowed list: rails ↔ bodies 0.1, pins ↔ holes, rods ↔ bores, washer ↔ barrel and A2, mount ↔ handguard face 0.05.
- No shading smear on large flats: the V2 matcap render is checked for diagonal streaks from the boolean corners, the prototype's failure.
- No decal z-fighting: markings are masks, not geometry.

### 8.6 Critic questions (each 0–2; answered on V1–V12 and the overlays)
1. Does it read at once as a real AR-15/M4 carbine built from real parts, with nothing invented?
2. Can you name the handguard, stock, grip, light, mount, optic, magazine and flash hider classes from V2–V5?
3. Is the rail one straight line at 10 mm pitch, with T-marks, sitting 30 mm above the bore, the receiver and handguard rails continuous?
4. Is the port open with the cover hanging on its rod, the dark carrier visible with its notches and a polished band, the forward assist and deflector right in shape and place?
5. Is the charging-handle latch on the left; are the bolt catch and selector on the left, and the mag release in its fence on the right?
6. Does the magwell flare; are the pins, trigger, guard and A2 grip (nub, checkering, open bottom) all there?
7. Are the M-LOK slots, lightening holes, front chamfer and QD socket correct, with the gas block glimpsed through the holes?
8. Is there exactly one barrel, with the government step, crush washer and an A2 with five slots and a closed bottom, in burnt bronze with soot?
9. Does the light look like a Mini Scout (bezel, taper, thin body, knurled tail cap with shroud, TIR lens) on a real offset plate, clear of the handguard and the thumb?
10. Is the magazine a PMAG GEN M3 (ribs, texture, dot matrix, flared floorplate, curve) fully seated?
11. Is the stock the Minimalist outline (big window, angled grooved pad), with castle nut, staked QD plate and a hand's width of bare tube?
12. Are the six tan patches where the picture has them, hand-painted and chipped like real field paint, not printed decals?
13. Is the wear honest: edges silvered only where rubbed, polish where touched, dust in slots and holes, carbon at the muzzle and port, brass smears on the deflector?
14. In V1, do the pins, the port, the mag release, the vent-hole row and the muzzle sit on the picture, and are the deviations exactly the accepted ones?
15. Do both hands meet the rifle with no gap and no penetration, the index straight along the lower, the thumb across the rail?
16. Would an armourer believe this rifle, and would a player recognise it as the one in the picture?

### 8.7 Failure modes to look for (and the fix)
| Symptom | Likely cause | Fix |
|---|---|---|
| Solid blocks where holes should be; bands of bare metal on flats | boolean operand not one manifold solid (prototype §6 v1) | union primitives first or build the hull as one extrusion; re-run the checks |
| Diagonal light streaks across a receiver flat | Pointiness-based wear on triangulated boolean faces | wear from `Wear.EdgeBevel` only |
| Rail pitch drifts (slot 20 is 0.5 mm off) | slots placed by accumulated float offsets, or two phases | one phase formula Y = −0.5 + 10.01 k from a single datum |
| Sliver land or slot at the receiver/handguard joint | phase not shared | the joint must fall inside slot k = 0 |
| Handguard reads chunky or the hand floats | section built at the drawn 45 × 55 | 38.1 × 49.3 (D5); rerun the hands' contact solve |
| A second tube or rod at the muzzle | someone "matched the picture" | D3: one barrel; delete it |
| Bronze looks copper-orange or plastic | base too saturated, metallic too low | calibrate on the swatch board (§5.5); metallic 0.45, flake on |
| Tan reads yellow or pasted on | saturation too high; no chips or streaks; mask not wrapping the forward-assist housing | §5.4 projection along X; chips by `Wear.Chips`; edge softness 0.2 |
| Magazine floats or sinks in the magwell | spine not starting at the feed-lip datum, or the floorplate gap | origin at (0, −49, −14.5); ≤ 0.5 mm gap check |
| Light intersects the handguard or the thumb | axis too close, or the hand station moved | axis (32, 16); thumb ≥ 20 mm forward; re-check after spec 05 changes |
| Grip frame off by 15–20 px in V1 | spec 05/08 still using (0, −194, −76) | adopt (0, −169.0, −94.8) (D13) |
| Port interior bright | BCG material set to bright steel | phosphate with polished bands only (D10) |
| Logos of real makers visible | `--markings real` left on | default `fictional` (D23) |

---

## 9. Build order, effort and risks

| # | Step | Script stage | Wall time per run | Effort to write and check | Risk |
|---|---|---|---|---|---|
| 1 | Helpers `hardsurf`, `lathe`, `rail1913`, `mlok`, knurl + unit tests (a 10-slot rail, a slotted plate, a lathe) | lib | 2 s | 4 h | low |
| 2 | Frames, pins, anchors | `--stage frames` | < 1 s | 0.5 h | low |
| 3 | Upper body + receiver rail | `--stage upper` | 2 s | 4 h | medium (boolean count) |
| 4 | Dust cover, hinge, forward assist, charging handle, BCG | `--stage upper_parts` | 1 s | 3 h | low |
| 5 | Lower body + 12 small parts | `--stage lower` | 2 s | 5 h | medium (magwell flare: prototype exists) |
| 6 | A2 grip | `--stage grip` | 1 s | 1.5 h | low |
| 7 | Tube, nut, end plate | `--stage buffer` | < 1 s | 1 h | low |
| 8 | Stock and pad | `--stage stock` | 1 s | 3 h | **high: outline unverified** |
| 9 | Barrel, gas block, gas tube, nut | `--stage barrel` | < 1 s | 1.5 h | low |
| 10 | Handguard + rail + QD + screws | `--stage handguard` | 4 s | 3 h | medium (38 cutter shells) |
| 11 | A2 + washer | `--stage muzzle` | < 1 s | 1 h | low |
| 12 | Light + mount | `--stage light` | 2 s | 2.5 h | medium (knurl density) |
| 13 | Optic A / B, BUIS | `--stage optic` | 1 s | 2.5 h | low |
| 14 | Magazine | `--stage mag` | 1 s | 2.5 h | low |
| 15 | Markings masks | `--stage marks` | 10 s | 1.5 h | low |
| 16 | Materials, masks, swatch calibration | `--stage materials` | swatches 3 min | 5 h | **high: dark-metal and bronze calibration** |
| 17 | Collider, proxy, LOD0/LOD1, bakes, glTF | `--stage export` | ≈ 8 min | 4 h | medium |
| 18 | Views, readback, overlay, critic round | `--eval` | ≈ 30 min Cycles | 4 h | — |
| | **Total** | | | **≈ 50 h** | |

Order constraints:
- step 2 first: specs 05, 08 and 11 can start against the frames and `Rifle.Proxy` at once;
- step 10 before the hands' contact solve;
- step 16 after the swatch board of spec 17 exists;
- the acceptance render after spec 08's re-solve with the new pins.

Main risks and mitigations:
1. **Dimensions that are estimates.** The highest-visibility ones are the Minimalist's outline and its LOP per position, the upper's internal stations (port, forward assist, pins) and the M300C body diameter. Each is marked E [VERIFY]; the §10.3 list is the work order for a session with catalogue drawings or a part in hand.
2. **Ripple into the hands** (D5 section, D13 grip): specs 05, 08 and 11 re-run their solves. Every frame is an empty, so nothing in those specs is retyped.
3. **Boolean robustness on the handguard.** Split the difference per face (3 + 2 operations) if one 38-shell cutter fails; volume checks catch silent failures.
4. **Render cost.** Twelve Cycles views at 2–4 min each fit one session if run sequentially. Hero acceptance on Jeff's GPU machine.
5. **Trademarks.** Real shapes, fictional markings by default (Q7).

---

## 10. Interfaces and open questions for the client

### 10.1 Interfaces (what this spec gives and needs)
| Spec | This spec provides | This spec needs |
|---|---|---|
| 05 Arms and hands | `Rifle.GripFrame` **moved to (0, −169.0, −94.8)** (was (0, −194, −76)); `Rifle.HandguardFrame` (0, 170, 0) unchanged; anchors `IndexFace`, `ThumbRail`, `FingerFacet`; `Rifle.Collider` with contact groups; grip 102 tall, 25° rake, top 55 × 30.5, nub at 22; handguard **38.1 × 49.3** (was 45 × 55); rail 21.2 | `grip.py::close_finger()` with `contact_offset` 1.5; the hands fitted after `rifle_place.py` |
| 08 Rig and pose | `Rifle.Root`; pin empties **butt (0, −415, −46), muzzle (0, 427.2, 0)**: pin distance **843.5** (was 849); predicted frame pixels GripFrame (724, 368), HandguardFrame (840, 467); `Rifle.Rig` for the game; mass 3.3 kg (was 3.6) | the two-pin solve against `Vest.Collider`; parent to `wrist.R` after the bake; its frame check in §4.8 changes to GripFrame (724, 368) ± 6 |
| 11 Gloves | `Rifle.Collider` (≤ 0.3 mm from the hero surfaces in the contact groups); nothing under the handguard between Y 125 and 260 but lightening holes | the 0.3 mm push-out rule |
| 12 Hard armour | rifle volume for the forearm-guard clearance (≥ 3 mm) | guard meshes in the hero pose |
| 13 Plate carrier | `Rifle.Proxy` (= `Rifle.StandIn`); light clearance 20–40 mm in front of PALS rows 6–7; the chest pouches hold PMAG GEN M3 (190 × 66 × 22) | `Vest.Collider.RightPectoral` |
| 14 Belt and leg rigs | the leg carriers hold two PMAG GEN M3 (190.5 × 66 × 22.1, Stealth Gray, same material); the optional P226 (Appendix A) for the Safariland 6378-class holster; note: the real magazine floorplate projects at (709–717, 444–455), above the belt (y 490–512), so it does not hide the buckle | — |
| 16 Materials library | `mat_hard.py` slots of §5.1 and node groups `Wear.EdgeBevel`, `Wear.Touch`, `Wear.Chips`, `Wear.Dust`, `Wear.Grime`, `Wear.Carbon`, `Wear.Brass`, `Wear.Scuff` | the swatch board and the calibration rule |
| 17 Evaluation scene | V1–V12 definitions; `rifle_overlay.py`; `rifle_ref_polygon.json` | the reference camera and hero lights as callable setup |
| 18 Pipeline | stage list of §9; `export/rifle_ar12.glb` (LOD0 ≤ 20 k, LOD1 ≤ 6 k, rig, two texture sets); generated masks in `assets/generated/` (gitignored, rebuilt) | build order and the export scale (×0.970) |
| `assets/interfaces.json` | `rifle.pins`, `rifle.frames`, `rifle.anchors`, `rifle.oal` 855.8, `rifle.mass` 3.3, `rifle.section_handguard` [38.1, 49.3], `rifle.rail_top` 30.2, `rifle.light_axis` [32, 16], `rifle.optic` "a" | — |

### 10.2 Open questions for the client (the default is built until answered)
1. **Q1 Handguard length.** Default **MCMR-13** (13.4 in): it agrees with the analysis and all neighbouring specs, but its front lands 23.5 px past the drawn cap and the muzzle stub shrinks from ≈ 146 to 86 mm of exposure. Alternatives: MCMR-10 (13.6 px short of the cap) or a 12 in rail from another maker (8 px).
2. **Q2 Lightening holes.** Default **on**, Ø 10 at 26 mm on the lower bevels (the image's identity in a physically possible size). The catalogue MCMR's bevels may be plain: `--hg-holes none` builds the catalogue look.
3. **Q3 Optic.** Default **A: Aimpoint T-2 on the LRP with the 39 mm spacer, rear of the receiver**: real, smallest, keeps the drawn light area clean. B: CompM4 as on the loadout icon. `none`: the picture as drawn, but no real carbine is fielded without a sight.
4. **Q4 Barrel finish.** Default **whole barrel and A2 in Burnt Bronze** (the bronze tube in the picture is the barrel). Alternative: factory phosphate barrel and a bronze A2 only (the analysis's reading).
5. **Q5 The three "screws".** Default **dropped** (nothing real sits there; the M-LOK rims give the glints). Alternative: a short M-LOK rail section on the 3 o'clock face at Y 200–250 with its two screws.
6. **Q6 Light.** Default **SureFire M300C** (matches the drawn 2.9 cm head and the short body). Alternative: the M600 Scout class of the brief (≈ 140 mm long), which would reach Y 150 and crowd the left thumb.
7. **Q7 Markings.** Default **fictional "AR-12" markings**, no real maker logos on a game asset. Real marks only for reference renders.
8. **Q8 Back-up iron sights.** Default **none** (as drawn); `--buis` adds folded ones.
9. **Q9 Magazine.** Default **PMAG GEN M3 Stealth Gray**. Alternative: USGI aluminium 30-round (matches "worn aluminium" but has no published dimensions in our notes).
10. **Q10 Sidearm.** Default **not built on the body** (none visible). Option: the Appendix A P226 in spec 14's optional holster at his right rear.
11. **Q11 Blue window.** Default **off** (it is not a real part); `--emissive-panel` keeps the icon's sci-fi cue as a recessed panel.

### 10.3 Facts to verify with a drawing or a part in hand (the [VERIFY] work order)
1. Upper receiver stations: port opening, forward-assist axis, pin heights, receiver rail slot count and T-mark position.
2. BCM MCMR-13: facet pattern on the 45° bevels, clamp screws, where the rail starts at the flare.
3. MFT Minimalist: side outline, window, front lug, QD position, length of pull at each of the 6 positions, pad rake.
4. M300C: body diameter; tail-cap knurl length.
5. Mil-spec castle nut notch count.
6. Gas-tube length and its bend.
7. Order of the trigger and hammer pins.
8. A2 port width.
9. PMAG GEN M3 rib count and texture extents.
10. T-2 control layout (which side carries the knob and the battery cap).

### 10.4 Export notes
The game asset scales with the character (×0.970 to the rules' 1.80 m man), so the exported rifle is 830 mm long. If a real-size rifle is ever needed in the game, the hands must be re-solved at that scale.

---

## Appendix A — "P9 Sidearm": SIG Sauer P226 class (hidden; built only with `--pistol`)

**A.1 Identity and decisions.** The loadout icon shows a hammer-fired DA/SA 9 mm with a grey slide, a darker frame, a stippled grip and a rail light: a SIG Sauer **P226R** (two-tone: stainless slide, black alloy frame). Its proportions are stretched (OAL/height 1.78 against the real 1.40), so reality wins: build the real P226. The icon's "5 coarse rear serrations" become the real part's fine rear serrations. **No pistol or holster is visible on the soldier** (weapon note §5, spec 14 D12). Default: not built. With `--pistol` it sits in spec 14's optional Safariland 6378-class holster at his right rear (azimuth 135°), invisible from the hero camera. For the loadout card a turntable view is rendered.

**A.2 Real dimensions**

| Feature | Dimension (mm) | Tag |
|---|---|---|
| Overall length / height / width | 196 / 140 / 38.1 | S |
| Barrel | 112 | S |
| Mass with magazine | 964 g | S |
| Sight radius | ≈ 160 | E |
| Slide | 196 × 31 tall × 25 wide; top radius 9; rear serrations 14 at 2.6 pitch, 1.0 deep, 22° rake | E |
| Ejection port | 34 × 13, barrel hood visible | E |
| Frame dust-cover rail | one 1913 slot pair, 21.2 wide | S (profile) / E |
| Controls (left) | decocker, slide-stop, takedown lever | S (P226 layout) / E (sizes) |
| Hammer | spur 8 above the slide line at full cock; down (decocked) in the holster | E |
| Grip | stippled polymer panels, 15-round magazine with a flush base 125 long | S (15-round) / E (spec 14 used 125) |
| Light | Streamlight TLR-1-class rail light, ≈ 86 × 36 × 33 [VERIFY] | E |

**A.3 Construction** (same helpers). The slide is the side profile (YZ) extruded 25 wide:
- top rounded by a loft of the cross-section;
- ejection port DIFFERENCE;
- serrations as one arrayed cutter;
- sights as extrusions with three tritium dots (glass, off).

The frame is the side outline extruded, with the rail, trigger guard, grip and magazine well. The parts are: hammer, trigger (DA curve), decocker, slide stop and takedown lever; stippled grip panels (bump 0.4); magazine and base plate; rail light. The total is ≈ 25 k tris; `hardsurf.finish(0.5, 3)`. All are named `Pistol.*` under `Pistol.Root` (origin at the bore line over the trigger, +Y to the muzzle).

**A.4 Materials.**
- Slide: bead-blasted stainless, metallic 1.0, roughness 0.45, base (0.50, 0.50, 0.49); the hero target is the icon's #4f5050 (top #868788), with worn bright edges.
- Frame: `Rifle.Mat.Anodised` black.
- Grips: `Rifle.Mat.Polymer.Black` with stipple.
- Light: `Rifle.Mat.Hardcoat.Gloss`.
- Muzzle crown: polished.
- Markings: fictional.

