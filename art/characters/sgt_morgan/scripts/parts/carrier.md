# Carrier

Build: `"$SGT_BLENDER" -b --python scripts/parts/carrier.py [-- --no-render]` (about 25 s on the RTX 3050). Output:
`cache/parts/carrier.blend` (collection `Part.Carrier`), `cache/parts/carrier.json` (placements, gaps and the
interpenetration check), `renders/carrier/*.png`, `renders/carrier/carrier_check.json`. Shared helpers:
`scripts/parts/gear_common.py` (on top of the clothing agent's `common.py`).

## 1. What it is (real identity and dimensions)

A **Crye JPC 2.0 class plate carrier, size Medium**: the round-1 body (base.json chest girth 990-993 mm, 39 in)
falls in Crye's Medium (about 38-43 in); take 1's spec 13 chose Large for a 1100 mm chest that this body does not
have.

| Item | Built (mm) | Source / class |
|---|---|---|
| Plates | SAPI Medium 241 x 318, multi-curve R 254 across, R 457 along | SAPI sizing chart (9.5 x 12.5 in); curvatures spec 13 §3.2 |
| Front and rear bags | 285 x 340, shooter's-cut corners 50 at 45 deg, 31 thick over the plate tapering to 14 at the margin; every edge bound (a 7 mm radius roll, black) | plate + about 22 per side; build-up spec 13 §3.2 (5 back panel and foam + 25 plate + 1 front); 25 mm binding tape folded (spec 13 §3.2) |
| Front bag position (round 2) | top at z 1453, 52 below the suprasternal notch (1505, the clavicles' sternal ends); plate top 60 below it; rear bag top 1503 | drawn (see §3) |
| Front flap | 255 x 34 x 6 (round 4; 42 before), below the front bag (one object with the bag); lies on the belly where it stands proud of the plate; bound hem; one PALS row of 6 cells | JPC class, spec 13 §3.2 |
| PALS (round 2) | Type III 25.4 x 1.3 webbing, bar-tack columns at 38.1, rows at 50.8: front bag 5 rows x 7 cells from 25 above its bottom up to the panel, flap 1 x 6, cummerbund 3 x 6 a side; 3 mm sag between columns | MIL-spec PALS, spec 13 §3.3; `lib/gear_webbing.pals_rows` |
| Cummerbund | 150 tall x 20 thick, from 25 mm behind the front bag's edge to 25 mm behind the rear bag's; rises 45 toward the back (over the belt and the trousers' waist there) | JPC/6094 class, 3 PALS rows (spec 13 §3.8) |
| Shoulder pads | 64 x 8, centre lines at x +-140 (`shirt.STRAP`), tilted to the trapezius; 38 x 1.5 webbing down their centre | spec 13 §3.7 (70 wide, 6-10 pad); the drawn pads sit at the gaiter's outer edge |
| Front strap roots | 38 x 2 webbing from the pad's end down the chest to the bag's top edge at x +-105 and down the bag face to 95 below its top; 38 mm ladder-lock 52 x 44 x 6 (two slots, `gear_hardware.ladder_lock`) 30 mm down the run; a 110 mm loose tail through two keepers 16 x 44 | spec 13 §3.6-3.7 |
| Admin panel | 175 x 90 x 8 moulded to the bag face, canted 2.6 deg (right end up) | drawn (spec 13 D5) |
| Rifle-mag pouches | three, body 62 x 32 x 158; flap over the top (12 thick) and 44 down the front; 20 mm pull tab to 22 below the flap's edge; at x -20, +46, +112, bottoms 48 above the bag's bottom, standing on the PALS | slim single 5.56 pouch (Esstac KYWI single class); STANAG 25 thick + walls |
| Pistol-mag carrier, right flank | 100 x 38 x 105 black body, two tan plates 40 x 92, two magazine bases | Blade-Tech/HSGI double pistol TACO class (spec 14 §3.8) |
| Utility pouch, left flank | 50 x 30 x 70 | spec 13 D9 |
| Radio pouch | 76 x 57 x 229 on the back-left at 128 deg round the torso, radio top 66 x 40 x 18 | Fight Light class pouch, PRC-152 class radio (spec 13 §3.9) |
| Antenna | steel 26 x 60, brass 30 x 55 with a 2 mm ring groove 38 up, rubber cap 32 with a 16 mm dome; leans 5 deg back; top at z 1613; radio top with two knobs (16 x 12) and a 4 mm bungee over it | spec 13 D11, §3.9 |

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
