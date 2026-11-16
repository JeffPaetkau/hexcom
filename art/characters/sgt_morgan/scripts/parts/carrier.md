# Carrier

Build: `"$SGT_BLENDER" -b --python scripts/parts/carrier.py [-- --no-render]` (about 25 s on the RTX 3050). Output:
`cache/parts/carrier.blend` (collection `Part.Carrier`), `cache/parts/carrier.json` (placements, gaps and the
interpenetration check), `renders/carrier/*.png`, `renders/carrier/carrier_check.json`. Shared helpers:
`scripts/parts/gear_common.py` (on top of the clothing agent's `common.py`); round 10: `scripts/parts/softgear.py` (soft Cordura pouches, fabric noise).

## 1. What it is (real identity and dimensions)

A **Crye JPC 2.0 class plate carrier, size Medium**: the round-1 body (base.json chest girth 990-993 mm, 39 in)
falls in Crye's Medium (about 38-43 in); take 1's spec 13 chose Large for a 1100 mm chest that this body does not
have.

| Item | Built (mm) | Source / class |
|---|---|---|
| Plates | SAPI Medium 241 x 318, multi-curve R 254 across, R 457 along | SAPI sizing chart (9.5 x 12.5 in); curvatures spec 13 §3.2 |
| Front and rear bags | 285 x 340, shooter's-cut corners 50 at 45 deg, 37 thick over the plate (round 9; 31 before) rolling over the plate's edge in 18 mm (a cosine, round 10) to 16 at the margin; a 1 mm padded-face unevenness on the outer faces (round 10); rear bag 5 x 6 PALS and a drag handle (round 10); every edge bound (a 7 mm radius roll, black) | plate + about 22 per side; build-up spec 13 §3.2 (5 back panel and foam + 25 plate + 1 front); 25 mm binding tape folded (spec 13 §3.2) |
| Front bag position (round 2) | top at z 1453, 52 below the suprasternal notch (1505, the clavicles' sternal ends); plate top 60 below it; rear bag top 1503 | drawn (see §3) |
| Front flap | 255 x 34 x 6 (round 4; 42 before), below the front bag (one object with the bag); lies on the belly where it stands proud of the plate; bound hem; one PALS row of 6 cells | JPC class, spec 13 §3.2 |
| PALS (round 2) | Type III 25.4 x 1.3 webbing, bar-tack columns at 38.1, rows at 50.8: front bag 5 rows x 7 cells from 25 above its bottom up to the panel, flap 1 x 6, cummerbund 3 x 6 a side; 3 mm sag between columns | MIL-spec PALS, spec 13 §3.3; `lib/gear_webbing.pals_rows` |
| Cummerbund | 150 tall x 20 thick, from 25 mm behind the front bag's edge to 25 mm behind the rear bag's; rises 45 toward the back (over the belt and the trousers' waist there) | JPC/6094 class, 3 PALS rows (spec 13 §3.8) |
| Shoulder pads | 64 x 15 (round 9; 8 before), thinning to 6 over the last 36 mm at each end (round 10), 5.5 mm rounded edges, centre lines at x +-140 (`shirt.STRAP`), tilted to the trapezius, 2.2 over the shirt (round 10; 3 before), running 32 mm down onto the rear bag's face (round 10); 38 x 1.5 webbing down their centre | spec 13 §3.7 (70 wide, 6-10 pad); the drawn pads sit at the gaiter's outer edge |
| Front strap roots | 38 x 2 webbing from the pad's end down the chest to the bag's top edge at x +-105 and down the bag face to 95 below its top; a broad gunmetal buckle 56 x 58 x 7 (round 10; a black 52 x 44 x 6 ladder-lock before) 30 mm down the run; a 110 mm loose tail through five 10 mm webbing loops at 20 mm (round 10; two 16 mm keepers before) | spec 13 §3.6-3.7 |
| Admin panel | 175 x 90 x 12 (round 9) moulded to the bag face, canted 2.6 deg (right end up); round 10: a dark 92 x 24 name-tape field, a 64 x 6 slot, three domed studs, a bound rim | drawn (spec 13 D5) |
| Rifle-mag pouches | three, body 64 x 38 x 184 (round 10, soft: `softgear.soft_pouch`; 178 box round 9, 62 x 32 x 158 before), the magazine's 4.5 mm bulge, a rounded bottom; a 3.5 mm flap crowned 7 over the magazine top and draped 54 down the front over the body's rounded corners, a bound edge, piped front seams; a 20 mm pull tab with a 24 x 20 slide-lock plate at the hem; at x -20, +46, +112, bottoms 32 above the bag's bottom, lying on the PALS (round 10; 5 mm over its sag before) | single 5.56 pouch holding a 30-round STANAG (Esstac KYWI single class) |
| Pistol-mag carrier, right flank | 100 x 38 x 105 black body, two tan plates 40 x 92, two magazine bases | Blade-Tech/HSGI double pistol TACO class (spec 14 §3.8) |
| Utility pouch, left flank | 50 x 30 x 70 | spec 13 D9 |
| Radio pouch | 70 x 52 x 220 soft (round 10; 76 x 57 x 229 box before) on the rear bag's PALS at x +74 (his left), its top 40 below the bag's top (round 10; it hung off the bag's edge at 128 deg round the torso before), radio top 66 x 40 x 18 | Fight Light class pouch, PRC-152 class radio (spec 13 §3.9) |
| Antenna | round 10 (m42, `zoom_carrier13_antenna_x14`): a steel connector 18 x 22, a tan tube 26 x 100, a yellow end 26 x 34, a flat black cap 24 x 12 (no dome); leans 14 deg out toward his left and 5 back; radio top with two knobs (16 x 12) and a 4 mm bungee over it (round 1-9: steel, brass with a ring groove, a domed black cap, top at z 1613) | spec 13 D11, §3.9 |

## 2. What the reference shows (ref/crop_torso_vest.png, zoom_carrier13_*, zoom_vest_*)

Olive-brown 500D bags; a khaki hard panel at the top, off-centre to his right, with the right strap passing over
its right end; a row of pouches under one PALS row, three visible (the fourth position is behind the carbine);
two lower PALS rows and the hem below them; straps with olive webbing and gunmetal frames; a near-black
cummerbund at the flanks; a two-cell tan/black pouch at the right flank; a brass antenna with a black cap rising
behind the left shoulder.

## 3. Departures and why

- **Medium, not Large** (body girth, above).
- **The bag is worn lower than a textbook fit** (round 2). Round 1 put the bag's top at "the notch", found as the
  deepest point of the front midline; that is the throat (z 1528), not the suprasternal notch, which lies between
  the clavicles' sternal ends (z 1505; ANSUR II suprasternale 0.818 of stature = 1500). The drawing's bag top,
  measured on the round-2 hero crop against the panel and pouch row, sits about 50 below that notch, so the plate's
  top is 60 below it. Real fit guidance puts the plate's top at the notch or a finger or two below; the drawing
  wears it lower, which is common and plausible, so the arrangement follows the drawing (`TOP_DROP`).
- **Panel flush with the bag's top** (6 below it, the binding showing above), as drawn.
- **Three magazine pouches, not four.** The image shows three; the posed carbine (stock, castle nut, charging
  handle, optic) lies where a fourth would be, and the row sits 37 mm above the bag's bottom edge so the posed
  carbine clears the pouches (it touched them by 7-9 mm lower down). The row is shifted to his left.
- **Straps symmetric at +-140** (round 2; take 1 D6 put them at +-110, round 1 at +-125). The drawn gaiter reaches
  about 110 out from the neck and is tucked under the pads, so the pads' inner edges sit at 108. The drawing's strap
  pair is 51 mm off to his right.
- **Pistol-mag carrier on the cummerbund's rows** (round 2; round 1 hung it 12 mm below them, into the belt).
- **The bag stands off the chest's midline.** A rigid multi-curve plate bridges the sternum between the pectorals
  and, on this body, rests on the lower abdomen (z 1133) as much as on the chest: the plate's inner face is 2 mm off
  the shirt at its nearest points, 34 at the top of the midline, 49 at mid-chest, 7 at the bottom (round 2,
  `carrier.json` gap_to_shirt.centre_by_z). Plates do bridge the sternum; the bottom contact comes from the body's
  belly in the rest pose. The soft flap below the bag follows the belly instead of the plate.

## 4. Round 1 (2026-11-14)

- Plate bags as analytic multi-curve surfaces (a plane fitted per bag by searching the pitch that lies closest to
  the chest while clearing the shirt everywhere, then bent by the SAPI curvatures), slabs with a thickness taper.
- Cummerbund from convex hulls of the clothed torso sections (sleeves excluded), clamped behind the bags' inner
  faces where it runs under them. Straps from convex hulls in the plane x = +-125, sampled across the pad's width.
- Side items seated on the outermost carrier/shirt surface (`gear_common.seat`), front items on the bag's outer
  face. The front strap roots are draped over the bag and the panel.
- Fitted to the shirt cache (`Part.Shirt`, sleeves and head region excluded by the nearest skin vertex) with the
  skin + 2 mm as a floor; without the cache it falls back to the skin + 4 mm.
- Rigging: every object soft-bound (weights transferred from Body.Mesh, common.bind) with all arm bones from
  `shoulder01` down collapsed into the clavicles, so the carrier follows the spine and shoulder girdle, not the arms.
- Colours (flat, from spec 13 §2.2): bag #463e34, pouches #3b342b, panel #7d705c, cummerbund #2f2a24, webbing
  #6d5f50, hardware #4c4943, brass #8a7550, cap #151718.

Renders opened: `carrier_rest_{front,side,back,threequarter}.png`, `carrier_hero_torso_vest_pair.png`,
`carrier_hero_soldier_full_pair.png`, `renders/round_01/gear_hero*.png`.

Check (`carrier_check.json`), triangle overlaps:
- rest: none with the body; the rear strap roots touch the shirt (16-20); the remaining gear/gear overlaps are
  the sewn joints (pad/root/ladder-lock, roots on the bag faces 13-28) and the pistol carrier on the cummerbund (10);
- posed with the carbine: the carbine has **no vertex inside the bag** (stock 3.8 mm and buffer tube 0.1 mm clear:
  it rests against it), surface crossings remain at the bag's right edge (stock 104, buffer tube 54); the right
  glove reaches up to 3 mm into the bag's lower right corner (260); the posed right upper arm passes 4 vertices
  through the bag's top-right corner.

## 5. Round 2 (2026-11-14): the neck and chest region, then the next level of form

### Position and fit
1. **Bag lowered.** The notch is now the clavicles' sternal ends (z 1505), not the throat (1528); the front bag's top
   is 52 below it (z 1453), measured against the drawn panel and pouch row on the hero crop (§3). The rear bag top
   is 1503 (50 higher than the front, as real carriers sit; round 1 had it at 1543, which would have left the
   cummerbund hanging below it).
2. **Tilt and gap:** the plate is fitted over the rigid bag only (round 1 included the flap, so the belly at the hem
   set the pitch); dw/dz 0.08, the top 34 mm off the midline (round 1: 84 at the top).
3. **Flap** 42 tall (was 60: its hem now clears the belt's top), lying on the shirt and trousers where the belly
   stands proud of the plate's surface; bound hem; one PALS row.
4. **Cummerbund** fitted over the shirt and the trousers' waistband, rising 45 mm toward the back so it clears the
   belt and the waistband there; its ends go under the flap (no longer clamped behind the plate there).
5. **Panel flush** (6 below the bag's top); **pouches** 48 above the bag's bottom, standing on the PALS.
6. **Pistol-mag carrier** on the cummerbund's rows (centre 58 above its bottom), clear of the belt.

### Shoulder straps (rebuilt)
- Centre lines at x +-140 (`shirt.STRAP`, shared with the gaiter, which is pressed flat under them), pads 64 x 8.
- At each of 116 stations over the shoulder the surface (shirt and gaiter) is sampled at 7 points across the pad;
  the pad's cross-section takes the surface's slope (least squares, smoothed along the strap: -0.33 over the top,
  about 18 degrees down toward the shoulder) and rides 3 mm over the highest sample; along its length it bridges
  hollows (a 1D hull). Round 1 held the section horizontal and rode the highest point under the whole width (the
  trapezius next to the neck), which made the yoke. The pads end 45 above the front bag; they take their weights
  from the shirt shell (shoulder01 kept), so they move with the surface they lie on.
- Front: the webbing leaves the pad's end, runs down the chest to the bag's top edge at x +-105 and down the bag face
  (the root); a 38 mm ladder-lock (`gear_hardware.ladder_lock(52, 44, 4, 6)`, two slots) 30 mm down the run, a
  110 mm tail over the root, two keepers. Rear: the root down the rear bag's face. A 38 mm webbing down each pad.

### Form
- **PALS** (`gear_webbing.pals_rows`, 25.4 x 1.3 webbing, columns at 38.1, rows at 50.8, 3 mm sag): front bag 5 rows
  x 7 cells (z 1138 to 1341: the top one shows between the panel and the pouch flaps, the bottom one below the
  pouches), flap 1 x 6, cummerbund 3 x 6 a side. No bar tacks yet.
- **Binding:** a 7 mm radius roll round both bags' outlines and along the flap's hem.
- **Pouches:** body, a flap over the top and 44 mm down the front, a 20 mm pull tab to 22 below the flap's edge.
- **Radio:** two knobs and a bungee on the radio top; the antenna's brass split by a 2 mm ring groove.

### Checks
- Rest: no overlap with the body; carrier/clothing overlaps only where the bag's bottom edge and its binding rest on
  the shirt over the belly (2 to 4 mm, triangle test).
- Renders opened: `renders/carrier/carrier_rest_{front,side,back,threequarter}.png`,
  `carrier_hero_torso_vest_pair.png` (and a crop of it against the reference: panel and pouch row on the drawn ones
  within about 15 to 20 mm, the gaiter now showing above the bag), `renders/round_02/torso_vest_compare.png`,
  `head_face_compare.png`, `soldier_full_compare.png`, `turnaround.png`.

### Clashes in the round-2 assembly (`renders/round_02/clashes.md`)

| Clash | Max (mm) | Kind |
|---|---:|---|
| Right glove and hand in the bag's lower right corner (-195, -48, 1176), 382 + 101 verts | 15.4 | pose: the grip hand must sit on the bag's face; the bag is lower than round 1's, where the hand is |
| Bag (and its PALS) in the shirt's right sleeve and the body at the bag's top right (12, -111, 1360) | 19.5 | pose: the posed right upper arm crosses the bag's edge |
| Carbine (charging handle, castle nut, end plate, optic) in pouch 1; the stock in the bag's PALS | 14.1 / 6.5 | pose: the hold (round 1's item, worse with the pouches lower) |
| Flap's hem binding in the trousers' waistband, posed only (rest: clear) | 12.7 | skinning: the flap follows the spine, the waistband the pelvis |
| Strap pads into the shirt and gaiter over the shoulders, posed only (rest: clear) | 5.4 | skinning |
| Pauldron caps in the strap pads | 1.1 | armour/carrier contact, small |

Gone since round 1: the pistol-mag carrier in the belt (clash 9), the strap pads 14 mm in the gaiter at the front of
the neck (clash 6), the cummerbund under the shirt (clash 10).

## 6. Still wrong, ranked for round 3

1. **The hold and the bag disagree** (the three pose clashes above): re-solve the hero pose with the bag's outer
   face (31 over the plate, PALS 5 more) and the pouches (32 deep) as the right hand's and the butt's contact
   surface; the right upper arm must clear the bag's top-right edge.
2. **Pouches and the panel are still blocks**: no magazine bulge, piping, bound flap edges, slide-lock plate; the
   panel has no chamfer, studs, label or slot (spec 13 §3.4-3.5).
3. **Straps:** the drawn strap has stacked frames on the bag face beside the panel; ours puts the lock at the pad's
   end. No keeper loops on the pad, no pauldron tab loop. The pads sink a few mm into the shirt in the pose.
4. **No bar tacks or stitches** on the PALS (`gear_webbing.pals_tacks` is ready), no edge topstitch.
5. **Cummerbund** is a constant 20 mm band (no padded rows, ribbed edges); its front ends lie under the flap
   without a closure.
6. **Flap in the trousers in the pose**: fixed in round 4 (§8).
7. Radio pouch is a box; the radio's body is hidden; the antenna 28 mm more lateral than take 1's position.
8. Colours flat; no Cordura, webbing or hardware materials yet.

## 7. For integration

- `shirt.STRAP` (x 140, pad 64) is the contract between the gaiter and the straps: change it in shirt.py only.
- The carrier fits to the shirt cache (shirt and gaiter) and to the trousers cache (cummerbund, flap); the armour
  fits to the shirt. `assemble.py`'s DEPS list only base and shirt for the carrier, so a trousers change does not
  mark it stale: add "trousers" there when the integrator next touches assemble.py.

## 8. Round 4 (2026-11-15): the flap and the trousers' waistband

The clash (rounds 2-3): `Carrier.Front.Flap.Binding` 390 vertices to 12.8 mm and the flap part of `Carrier.Front.Bag` 69
to 10.0 mm in `Trousers.Shell`, at the front waist. Two causes, measured with the assembly's open-shell rule (nearest
trousers face within 25 mm, offset within 45 deg of its inward normal):
- **Skinning** (the bag's flap): the flap took the belly's weights (the spine) and the waistband the pelvis's, so the
  posed waistband rose into the flap. `flap_to_waist()` now blends the weights of every vertex below the bag's bottom
  edge (the flap in `Carrier.Front.Bag`, the hem binding, the flap's PALS) toward those of the nearest trousers vertex:
  none at the bag's edge, all of them from 12 mm above the hem down (smoothstep). The flap's top moves with the plate,
  its hem with the waistband. Bag: 69 -> 0 vertices.
- **Fit** (the hem binding): the binding (a 4.5 mm radius roll) lay 4-10 mm above the waistband's top edge (z 1052 at the
  front) but 5 mm behind its front plane, so in rest already it counted as inside the waistband's lip (247 vertices,
  13.4 mm; the round-2 notes' "rest: clear" came from the carrier's own triangle check, which does not test the
  trousers). The flap is 34 mm tall (was 42): it still carries its PALS row (25.4 webbing, 4 mm margins) and its hem,
  after following the belly, ends about 12 mm above the waistband, as the drawing's flap hem sits above the belt.
  Binding: 390 -> 0 vertices, in rest and posed.

The cummerbund's rows start 2 mm above the hem (`zc0`), so they rose 8 mm with it.

## 9. Round 5 (2026-11-15): materials

`MATERIALS` in carrier.py (swapped by `common.library_pass`; `COL` stays the solid-view colour):
- **`Cordura.500D.OliveBrown`** (new, `printed` builder) on the bag, flap, pads, admin panel and cummerbund:
  ChatGPT's R000 swatch made seamless by the half-offset blend (`scripts/tools/seamless.py`,
  `gen/R000/cordura_olive_worn_seamless.png`) on `UV.Real` at 250 mm (its colour over its own mean, so the
  recipe's albedo sets the level), Fabric063's normal at 156 mm and the 0.61 mm basket weave, a ±28 % fade and
  soiling mottle over 70 mm, dust 1.2 from preset `cordura.top` (up-facing flap tops and pouch lids), grime at
  pouch bottoms. Albedos per use: bag #4d473d, flap #524a3f, pads #4a443a, admin panel #5a5244 (paler and
  dustier, as drawn), cummerbund #403b33.
- **`Cordura.1000D.OliveBrown`** (new) on the pouches (#474138) and the radio pouch (#413b33).
- **`Webbing.Nylon.OliveBrown`** (new) on the straps, PALS and cummerbund webbing (#4b453b, #464036, #3a362f);
  **`Webbing.Nylon.Black`** on the binding.
- **`Polymer.Black.Smooth`** on the buckles and ladder-locks, **`Polymer.Black.Textured`** (new) on the radio,
  the magazines and the black polymer, **`Polymer.Tan.Moulded`** (new) on the tan polymer,
  **`Metal.Brass.Aged`** (new; tarnished F0, bright worn edges) on the antenna, **`Rubber.Moulded.Black`** (new)
  on its cap, **`Metal.Gunmetal`** on the steel.
- Albedos were set against the hero render: the first pass (#3f382e) rendered 1.65 x too dark and too saturated
  against the reference's median over the carrier's mask; the second sits at ratio 1.10.

Renders opened: `renders/round_05/torso_vest_compare.png`, `soldier_full_compare.png`, `turnaround.png`.

Still wrong (materials):
1. Flatter than the drawn vest: the reference's carrier has strong light and dark scuffing, dark stains on the
   panel, frayed edges and dust in the PALS slots; ours has a mottle and up-facing dust. Per-panel wear masks
   (pouch and flap edges, the panel's stains) are the next step; a painted panel swatch could carry them.
2. The admin panel's hook-and-loop field, patches and name tape are not built.
3. Under the evaluation's warm key the olive reads brown (session log, round 5).

## 10. Round 8 (2026-11-15): the look (critics m9, m50, m48, m12, m52)

- **Worn olive-coyote, not chocolate** (m9, m50): with the evaluation light corrected (scene.py, key 5800 K) the
  carrier's median rendered 2.1 x too dark and too red. `Cordura.500D.OliveBrown` #4d473d -> #605d50,
  `Cordura.1000D.OliveBrown` #474138 -> #5b594c, `Webbing.Nylon.OliveBrown` #4b453b -> #5d5a4e; the per-use
  overrides in `MATERIALS` scaled by the same per-channel factor (flap #686156, pads #5e594f, admin panel #726b5c,
  cummerbund #524e46, radio pouch #555148, PALS #59544a, cummerbund webbing `_CB` #4a4741). Graded median now
  ratio 1.16, chromaticity (1.17, 0.73) against the reference's (1.21, 0.78).
- **Response** (m48): Cordura roughness 0.78 -> 0.84, a faint sheen 0.08; webbing 0.70 with sheen 0.08; the
  polymers satin (`Polymer.Black.Smooth` 0.38, `.Textured` 0.48 and #262625, scuffed edges +0.035).
- **Wear** (m12, m52; `mat_groups.abrasion`): pouch and flap edges and corners abraded toward #8d887a (45 %, broken
  by a 7 mm noise; the 4 mm `edge_near` band on finely meshed panels, the 2 mm Bevel mask on the low-poly box
  pouches, which `materials.edge_distance()` skips); rubbing where straps, arms and the carbine lie on it (contact
  within 14 mm); dust off the open faces into the seams (open 0.35, shelter 1.2), grime in the cavities.

Look-loop renders opened (`renders/look/M1`..`M6`): `sheet_torso_vest_graded`, `sheet_hands_rifle_graded`. The
carrier now reads lighter than the shirt and olive-grey, the layering the reference shows.

Still wrong: the drawn carrier has strong light and dark scuffing, dark stains on the panel and dust in the PALS
slots; ours is still too even and a little grey (the drawn olive has more yellow-green); the edge abrasion is faint
at hero distance on the box pouches.

## 11. Round 9 (2026-11-15): thickness, bulk and colour (critics m8, m41, m30, m15, m29, m33, m34)

- **Plate bags** 31 -> 37 mm over the plate (back panel and foam 7 + plate 25 + front laminate 5), margins 14 -> 18
  (`BAG_T`, `BAG_MARGIN_T`).
- **Mag pouches** 62 x 32 x 158 -> 64 x 38 x 178 (a pouch that holds a 30-round STANAG to its shoulder), bottoms 48 -> 32
  above the bag's bottom so they reach toward the belt as drawn, the flap over the magazine top 12 -> 18 thick and down
  the front 44 -> 54, bevels 4 -> 6 (`POUCH`, `POUCH_FLAP_TOP`, `POUCH_FLAP_DOWN`, `POUCH_LIFT`).
- **Admin panel** 8 -> 12 thick.
- **Shoulder pads** 8 -> 15 thick (12 foam + 3 fabric) with 5.5 mm rounded edges (`PAD_T`, `PAD_BEVEL`); along their
  length they now bridge only short dips (a 9-station moving average, `PAD_BRIDGE`) instead of the convex hull of the
  centre line, which stood the pad off the trapezius (m15, m29: "kinks up, daylight under it").
  The cross-section's tilt to the trapezius is capped at 0.55 (`PAD_TILT`; 0.9 before), which stood the pad's inner
  corner up beside the neck (m29, also flagged by the hard-kit lane).
- **Colour** (`TONE`, `ABRADE_TONE`, `_olive()`): measured on round 8's graded torso_vest crop under the carrier's mask
  taken from the Workbench parts panel, the render's median luminance was 1.44 x the reference's at the same r/g (1.24),
  b/g 0.82 against 0.79; round 8's look_stats (eroded flat masks) had the median at 1.00. The step is taken half way:
  every olive Cordura and webbing albedo of the carrier x 0.80 in linear light with b/g x 0.96, the abraded edges' and
  rubbed colours x 0.85 (overrides in `MATERIALS`, not the catalogue: the belt and the armour share those recipes).

Not done this round: PALS rows on the cummerbund existed already (3 x 6 a side, round 2); no magazine baseplates or
bungees on the pouches, no placard hook-and-loop field, no frayed edges.

Checks (`carrier_check.json`): no overlap with the body, rest or posed. Carbine against the thicker bag: 34-38 stock and
butt-pad triangles and 166 PALS triangles cross in the pose (the bag's face moved 6 mm out, the pouches 6 deeper); see
round 9's clash report.

Renders opened: `renders/carrier/carrier_hero_torso_vest_pair.png`, `carrier_rest_side.png`. Round 9's evaluation: below.

**Round 9's evaluation** (`renders/round_09/`: `torso_vest_compare`, `soldier_full_compare`, `turnaround`): the carrier is
visibly thicker from the side and the pouches are taller and reach toward the belt; the pads lie on the shoulders with
thickness. Colour (my measure, graded torso_vest crop under the carrier's parts mask; round 8 in brackets): median
luminance 1.16 x the reference's (1.46), r/g 1.26 against 1.19 (1.24 / 1.24), b/g 0.75 against 0.76 (0.82 / 0.79). It still
reads cleaner and flatter than the drawn one: the plate-bag face is one plain field above the pouches (the PALS show as
one row), the admin panel is a pale plain board, and the drawn vest's dark seams, stains and busy webbing are missing.
Clashes: carrier-carbine 111 vertices to 6.5 mm (round 8: 56 to 2.3; the butt pad against the thicker bag), strap pads in
the gaiter 7.5 mm (round 8: 6.4). Next: PALS slots and rows visible on the bag face above and between the pouches,
magazine baseplates and bungee on the pouches, the placard's hook-and-loop field and darker stained panel, and the hold
re-solved against the thicker bag.

## 12. Round 10 (2026-11-15): soft kit, the front, the loaded straps, the radio (G1 D2, D3, D11, D13; m10, m11, m18, m28, m33, m42, m44)

Round 10 does not use a cloth simulation. Take 1's spec 13 §4 had already judged one unnecessary for a stuffed,
plate-backed carrier ("a 20-layer stuffed bag behaves as a solid"). The soft look is shaped by code in the new
`scripts/parts/softgear.py`, which the belt shares:
- **Magazine pouches, rebuilt as fabric** (G1 D3, m28, m33: "deep straight boxes with flat lids"; `softgear.soft_pouch`).
  - The body has a superellipse section: square-backed where it is sewn to the backing, round-cornered at the front.
  - The magazine bulges the front 4.5 mm at mid-height, the sides pinch out 1.2 mm, the bottom is rounded, and a 0.7 mm
    low-frequency noise breaks up the surfaces.
  - The flap is a 3.5 mm slab, crowned 7 mm over the magazine's top. It rounds over the front edge and drapes 54 mm down
    the body's own front, wrapping its rounded corners at the sides, and its hem flares 1.6 mm.
  - Bound edges and seams: a bound flap edge, and piping down the two front corners.
  - The pull tab carries a 24 x 20 slide-lock plate at the hem (drawn).
  - Bodies are 184 tall (178 before): the soft flap crowns 10 mm over the top where the box lid stood 16.
  - The pouches now lie on the PALS (lift `BAG_T + PALS_T + 1.5`); before they stood 5 mm off over the webbing's sag.
- **Plate bags** (G1 D13: "a smooth hard suitcase"):
  - The fabric rolls over the plate's edge in 18 mm, on a cosine flat at both ends, down to a 16 mm margin (`BAG_ROLL`,
    `BAG_MARGIN_T`; before, a straight 16 mm ramp to 18). A quarter round was tried first: it put the outer face 6 mm
    further out at the edge and drove the carbine's butt 9.5 mm into the bag.
  - The outer faces only get a padded unevenness: 1.0 mm over 60 mm (`softgear.fabric_noise`). It is masked off at the
    bag's upper right, where the butt rests.
  - The rear bag gains a 5 x 6 PALS field (`REAR_PALS`) and a 38 mm drag handle, off centre to his right.
- **Front** (m10, m18, D11):
  - The strap adjuster is now the drawn broad gunmetal buckle (`CAM` 56 x 58 x 7, `Carrier.Mat.MetalHw` =
    Metal.Gunmetal). It was a black 52 x 44 ladder-lock.
  - Five 10 mm webbing loops at 20 mm (`KEEPERS`) cross the run below it, where two broad keepers were.
  - The admin panel carries a dark 92 x 24 name-tape field, a 64 x 6 slot, three domed studs and a bound rim.
- **Shoulder pads** (G1 D2, r8 m29: "bridge over open gaps above the shoulders and end abruptly"):
  - The pad's profile now lies on the shirt AND the rear bag. It runs over the bag's top, 32 mm down its face
    (`PAD_REAR_ON`), and the rear root continues 50 mm from there. Before, it ended in the air 15 mm above the bag, and the
    root ramped out over a gap.
  - It rides 2.2 mm over the shirt (`PAD_CLEAR`; 3 before).
  - The padding thins to 40 % over its last 36 mm at each end (`PAD_END`, `taper_strip`).
  - Where the pad lies on the rear bag there is no cross-slope (`flat_back_z`). The bag's clipped corner under half the
    pad's width had twisted its end. The cross-slope's smoothing went from 9 to 15 stations (`PAD_SLOPE_K`).
  - `PAD_BRIDGE` 5 was tried and went back to 9.
- **Radio pouch** (m44: it hung off the back plate's edge at 128 deg, attached to nothing): the pouch is soft, 70 x 52 x 220
  (`RADIO_POUCH`). It stands on the rear bag's PALS at x +74, its top 40 mm below the bag's top (`RADIO_X`,
  `RADIO_TOP_DROP`).
- **Antenna** (m42: "black with a ball tip"): the drawn tan tube with a yellow end and a short flat black cap.
  - Parts: a steel connector 18 x 22, a tan tube 26 x 100 (`Carrier.Mat.Antenna`), a yellow end 26 x 34
    (`Carrier.Mat.AntennaTip`), a black cap 24 x 12. Both new materials are Polymer.Tan.Moulded with albedo overrides.
  - It leans 14 deg out toward his left (`ANTENNA_LEAN`) and 5 deg back, so it rises behind the left shoulder outside the
    strap, as drawn. Base (rest) at [113, 193, 1485], top at [159, 205, 1647].
- **Colour** (m11, D11), measured with `look_loop.py` and `look_stats.py --grade` on the torso_vest crop (eroded part mask).
  Round 9's "1.16 x" came from a different measure (the parts panel, not eroded); on this one round 9 already sat at ratio
  1.08 (reference / render).

  | | Median Y | p90 | r/g | b/g |
  |---|---:|---:|---:|---:|
  | Reference | 0.0330 | 0.193 | 1.20 | 0.79 |
  | Round 9 | 0.0304 | 0.211 | 1.21 | 0.75 |
  | Round 10 | 0.0318 | 0.169 | 1.20 | 0.75 |

  - `TONE` (0.80, 0.80, 0.77) -> (0.745, 0.76, 0.77). Two trials are recorded in the code comment.
  - `WEAR` overrides on every olive Cordura use: print contrast 1.4, mottle 0.42 over 55 mm, grime 1.0 (cavity 1.2),
    abraded-edge share 0.6.
  - A stronger trial changed little at hero distance (look run `r10cb_v3`: print 2.2, mottle 0.65, abrasion 0.9,
    dust 1.3, grime 1.5). The recipe's procedural wear does not make the drawn scuffs and stains.

**Checks.** "Round 10" is an in-memory assembly of the current caches: carrier 21:11, belt 21:07, and the other lane's
armour 21:06 and boots 21:13. It is not a round, and its script is `cache/scratch_r10cb/scratch_asm.py`.

| Check | Round 9 | Round 10 | What |
|---|---|---|---|
| carrier-carbine | 111 verts, 6.5 mm | 129 verts, 5.0 mm | butt pad in the bag, 24 verts at [-235, -54, 1354]; stock 2.5; PALS in the stock 2.4 |
| shirt-carrier | 783 verts, 7.5 mm | 890 verts, 7.8 mm | the right pad in the gaiter at the back of the shoulder [-221, 105, 1609], as round 9 (skinning); 0.3 mm worse from the lower pads |
| body-carrier | none | none | |

Stand-off, round 9 -> round 10:
- Gone: `Carrier.Radio.Pouch` (floated, 52.1), `Carrier.Front.Binding` (5.7).
- Lower: `Carrier.Pouch.2` 13.4 floats -> 8.2 stands off; `Pouch.3` 17.9 floats -> 16.7 stands off; `Front.Bag` 28.0 ->
  25.8 (by design: a rigid plate bridges the sternum); `Rear.Binding` 7.1 -> 5.8.
- New: `Pouch.1` 21.5 and `Front.Panel` 12.4. The soft pouch's rounded bottom and the panel's rim face the skin across a
  gap, an artefact of the heuristic.
- Unchanged: `PistolMags` 31-33, the roots 19-20, `UtilPouch.L` 7.6.

Renders opened:
- `renders/carrier/carrier_rest_{side,back,threequarter}.png` and `carrier_hero_torso_vest.png`;
- the in-memory hero crops in `renders/scratch_r10cb/{c1,c2,final}/`: `torso_vest_cycles`, `soldier_full_cycles`, the
  turnarounds, and the closeups `close_shoulders_R`, `close_shoulders_back`, `close_radio`;
- the look runs' sheets `renders/look/r10cb_{v2,v3,final}/sheet_torso_vest_graded.png`.

**Still wrong, for round 11:**
1. The front still reads plainer than the drawn vest. The strap runs, buckles and loops are small at hero distance. The
   drawn vest is bulkier, with taller pouches nearer the panel and busy webbing.
2. The olive is right by the numbers but flat to the eye. The drawn grime, scuffs and paler worn khaki highlights need a
   painted or baked wear mask; the recipe's procedural wear does not make them. The lights (p90) are 12 % under the
   reference.
3. The pads' rear ends fold over the rear bag's clipped corners in visible angled blocks (rest back view). The right pad
   still meets the gaiter 7.8 mm deep in the pose; that is skinning, the pad taking its weights from Shirt.Shell.
4. The carbine's butt stays 5.0 mm into the bag's upper right (the hold, a pose item).
5. The pistol-magazine carrier's magazines and the utility pouch are still boxes; there are no bar tacks.
