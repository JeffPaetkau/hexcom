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
| Front and rear bags | 285 x 340, shooter's-cut corners 50 at 45 deg, 31 thick over the plate tapering to 14 at the margin | plate + about 22 per side; build-up spec 13 §3.2 (5 back panel and foam + 25 plate + 1 front) |
| Front flap | 255 x 60 x 6, below the front bag (one object with the bag) | JPC class, spec 13 §3.2 |
| Cummerbund | 150 tall x 20 thick, from 25 mm behind the front bag's edge to 25 mm behind the rear bag's | JPC/6094 class, 3 PALS rows (spec 13 §3.8) |
| Shoulder pads | 70 x 8, centre lines at x +-125 | spec 13 §3.7 (70 wide, 6-10 pad) |
| Front strap roots | 38 x 2 webbing from the pad over the bag top down to 95 below it; 38 mm ladder-lock 52 x 44 x 6 | spec 13 §3.6-3.7 |
| Admin panel | 175 x 90 x 8 moulded to the bag face, canted 2.6 deg (right end up) | drawn (spec 13 D5) |
| Rifle-mag pouches | three, body 62 x 32 x 158 + flap 64 x 36 x 24 (174 overall), at x -20, +46, +112 | slim single 5.56 pouch (Esstac KYWI single class); STANAG 25 thick + walls |
| Pistol-mag carrier, right flank | 100 x 38 x 105 black body, two tan plates 40 x 92, two magazine bases | Blade-Tech/HSGI double pistol TACO class (spec 14 §3.8) |
| Utility pouch, left flank | 50 x 30 x 70 | spec 13 D9 |
| Radio pouch | 76 x 57 x 229 on the back-left at 128 deg round the torso, radio top 66 x 40 x 18 | Fight Light class pouch, PRC-152 class radio (spec 13 §3.9) |
| Antenna | steel 26 x 60, brass 30 x 55, rubber cap 32 with a 16 mm dome; leans 5 deg back; top at z 1601 | spec 13 D11 |

## 2. What the reference shows (ref/crop_torso_vest.png, zoom_carrier13_*, zoom_vest_*)

Olive-brown 500D bags; a khaki hard panel at the top, off-centre to his right, with the right strap passing over
its right end; a row of pouches under one PALS row, three visible (the fourth position is behind the carbine);
two lower PALS rows and the hem below them; straps with olive webbing and gunmetal frames; a near-black
cummerbund at the flanks; a two-cell tan/black pouch at the right flank; a brass antenna with a black cap rising
behind the left shoulder.

## 3. Departures and why

- **Medium, not Large** (body girth, above). The bag's top is at the suprasternal notch measured on the body
  (z 1516 on the current base: the deepest point of the front midline), the plate's top 8 mm below it.
- **Three magazine pouches, not four.** The image shows three; the posed carbine (stock, castle nut, charging
  handle, optic) lies where a fourth would be, and the row sits 37 mm above the bag's bottom edge so the posed
  carbine clears the pouches (it touched them by 7-9 mm lower down). The row is shifted to his left.
- **Straps symmetric at +-125** (take 1 D6 put them at +-110; the shirt agent's gaiter is about 100 mm in
  half-width, so the pads ride over its flare). The drawing's strap pair is 51 mm off to his right.
- **Panel 24 mm below the bag's top** (drawn flush): the bag thins at its clipped top corners and the panel's
  corners would float there.
- **Pistol-mag carrier on the cummerbund's lowest row**, hanging 12 mm below it in front of the belt: the drawn
  position floats between hem and belt; take 1 D6.
- **The bag stands off the upper chest.** A rigid plate rests on the pectorals; on this body (pectoral muscle 0.7
  since the body part's round 1) the plate's inner face is 2 mm off the shirt at its nearest point, 36 mm at the
  median and up to 92 mm at the top corners (`carrier.json` gap_to_shirt). The drawing's carrier hugs the neck.

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

## 5. Still wrong, ranked for round 2

1. **No PALS, binding, buckle, keepers or frames.** The front reads as smooth slabs; row 1 under the panel and
   the two rows under the pouches carry much of the image's identity. `gear_webbing.pals_rows` is ready.
2. **Strap arrangement**: no keeper loops, no tail, a single box for the ladder-lock; the pads ride on top of
   the gaiter's flare instead of the gaiter being tucked under them (clothing and carrier must agree which is on
   top: the image has the straps over the gaiter).
3. **The top of the front bag stands 40-90 mm off the upper chest** (rigid plate on a prominent chest); the
   drawing's carrier sits closer to the neck. Check against photos of a JPC on a lean man; maybe the plate should
   pitch further back and rest on the pecs' upper edge.
4. **Pouches are boxes** without the flap's front tab, the magazine bulge and the bottom shadow band.
5. **Cummerbund** is a constant 20 mm band, not padded rows; it ends abruptly behind the bags.
6. **Radio** sits 28 mm more lateral than take 1's antenna position (x 185 vs 157); the radio body is hidden and
   only its top exists.
7. The pistol-mag carrier is hidden behind the right forearm guard in the hero frame; the drawn pouch shows
   below the elbow.

## 6. For integration

- The carbine pose was solved on round 0's chest. On the current base the butt rests on the bag's right edge and
  the right glove reaches 3 mm into the bag's lower corner: re-solve the pose with the carrier's front (bag outer
  face 31 mm over the plate surface, pouches 32 deep) as the butt's and hand's contact surface.
- The carrier was rebuilt on the base of 18:25 (the body part's round-1 chest, neck and arms); the shirt cache it
  fits to is older (18:09). Rebuild the shirt, then rerun `carrier.py`, `armour.py`, `belt.py`: they refit.
