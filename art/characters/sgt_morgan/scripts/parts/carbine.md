# Carbine

Build: `"$SGT_BLENDER" -b --python scripts/parts/carbine.py [-- --no-render] [--keep-scene]` (about 15 s on
the RTX 3050). Output: `cache/parts/carbine.blend`, `renders/carbine/*.png`, `renders/carbine/measure.json`.

## 1. What it is

The loadout card calls it the "AR-12 Carbine". It is built as one real M4-pattern carbine, the
configuration take 1 chose (`archive/v1/spec/15_carbine.md` §1.2):

- **Upper:** BCM M4 forged flat-top upper with a mil-spec charging handle (latch on the left).
- **Lower and grip:** BCM M4 forged lower with a USGI A2 pistol grip.
- **Barrel and muzzle:** 16 in government-profile barrel with mid-length gas, a low-profile gas block and an A2 birdcage.
- **Handguard:** BCM MCMR-13 M-LOK free-float handguard.
- **Stock:** mil-spec carbine receiver extension and castle nut, QD end plate, and an MFT BATTLELINK Minimalist stock at position 3 of 6.
- **Magazine:** Magpul PMAG 30 GEN M3.
- **Light:** SureFire M300C Mini Scout on an Arisaka offset M-LOK mount.
- **Optic:** Aimpoint Micro T-2 on an LRP mount with a 39 mm spacer.
- **Finish:** Cerakote burnt bronze on the barrel and the A2, plus hand-painted FDE patches.

### Frame (shared with the pose agent)
- **Root:** `Carbine.Root` sits on the bore axis, directly above the trigger face.
- **Axes:** local +X runs along the bore to the muzzle, +Z points up through the top rail, and +Y points to the gun's LEFT. The ejection-port side is therefore −Y.
- **Mapping from take 1:** in take 1's rifle frame R, x = R.y + 122, y = −R.x, z = R.z.
- **Collection and names:** everything is in `Part.Carbine` and is parented to the root. The objects are `Carbine.<Component>` and the materials are `Carbine.Mat.<Name>`.
- **Hand empties:** the empties sit at the centre of each palm's contact with the gun. Local +Z is the palm normal pointing into the gun, local +X runs across the palm from the little finger to the index finger, and Y = Z × X.
  - `Carbine.Grip.R` is at (−74.6, −15.0, −85.2) mm. That is the right side of the A2 grip, 54 mm down its 25° axis from the receiver. Its Z axis is +Y, and it is 0.6 mm from the grip surface.
  - `Carbine.Grip.L` is at (292.0, 10.2, 17.6) mm, at take 1's left-hand station R.y 170. It is an overhand hold: the palm sits over the 11 o'clock side of the handguard, which is how the reference reads (the back of the hand over the rail, the fingers down the right face, the tips under the 4:30 bevel). Its Z axis is (0, −0.5, −0.87), and it is 0.6 mm from the handguard surface.

## 2. Dimensions built (mm; sources in take 1 spec 15 §3.15 and weapon analysis §2)

The script measured the following on the built meshes (`measure.json`):

| Quantity | Built | Real / source |
|---|---|---|
| Overall length, butt heel to A2 front | **855.3** | 16 in carbine: 794 collapsed to 876 extended, so position 3 is about 856 (research_dimensions §12) |
| Barrel, bolt face to crown | **406.4** | 16.0 in |
| Barrel and A2 ahead of the handguard | 86.3 | the MCMR-13 is 340.4 long; the A2 is 44.5 × 21.8 |
| Height, optic top to floorplate | 302.4 | T-2 axis 39 mm above the rail (LRP + 39 mm spacer) |
| Height without the optic | 242.4 | rail top +30.2 above the bore (A2 sight height 2.6 in minus 1.41 in co-witness) |
| Height without the optic or magazine (rail top to grip bottom) | 174.2 | A2 grip is about 102 tall, raked 25° |
| Width overall | 68.5 | includes the light on its offset mount |
| Length of pull, trigger face to pad centre | 292.8 | short pull, right over plate armour |
| Stock pad rake | 12.2° | the Minimalist's angled pad |
| Magazine floorplate tilt | 15.5° | PMAG 190.5 × 66 × 22.1, constant curve |
| Rail teeth | 20 on the receiver, 34 on the handguard | MIL-STD-1913: 10.01 pitch, 5.23 slots, 3.0 deep, 21.2 top |

Other built dimensions:
- **Receiver:** upper 197 long and 29 wide; lower 26 wide with a 30 mm magwell (33 at the flared lip); 67 × 23 magwell opening.
- **Port:** ejection port 76.2 × 20.3, with the dust cover open.
- **Handguard and rail:** octagon 38.1 across the flats, 33 ID. M-LOK 32 × 7 slots at 3, 6 and 9 o'clock, 8 per face. Seven Ø10 holes on each lower bevel at 26 mm pitch.
- **Receiver extension:** buffer tube Ø29.16, castle nut Ø36.
- **Stock:** 180 × 128 with a 44.5 wide pad.
- **Light:** M300C, 104 long with a Ø28.6 bezel, axis at y −32, z +16.

**Mass.** The script sums each component's mesh volume × density.
- A fully solid blockout weighs 5.09 kg.
- With per-component fill factors it is **3.11 kg empty and 3.47 kg loaded** (30 × 12 g rounds). Fill factors are the fraction of each envelope that is material in the real part, e.g. upper 0.45 and magazine shell 0.25.
- Real: an M4 is 2.9 kg empty, plus the T-2 (0.105 kg) and the M300C (0.116 kg), which gives about 3.1 kg; take 1 §3.14 estimates 3.2 to 3.4 kg loaded.
- The fill factors are judgement, so this number is a sanity check, not a measurement.

## 3. What the reference shows, and where the build departs from it (reality wins)

Evidence: `ref/zoom_carbine15_*`, `ref/crop_hands_rifle.png`, `ref/crop_icon_carbine.png`, the take 1
weapon analysis and spec 15 §2. In the hero view the camera sees the gun's right side. The butt sits on his
right pectoral and the muzzle points toward his left thigh.

- **Three or four muzzle tubes.** They are an image artefact. Built as one barrel with an A2 birdcage, in the drawing's burnt-bronze colour (take 1 D3).
- **Rail drawn about 10 cm above the bore.** Built at the real +30.2. The receiver and handguard rails are coplanar.
- **Light straddling the receiver/handguard joint.** No mount can hold it there. Built as an M300C on an offset mount in the first 3 o'clock M-LOK slot, with its tail 10 mm ahead of the receiver face and its top level with the rail, as drawn.
- **Optic.** The held view shows none. The icon shows a CompM4-class tube. A fighting carbine carries a sight, so a T-2 + LRP is mounted on the rear of the receiver rail; that keeps the drawn light's area clear (take 1 D9).
- **Foregrip and hand stop.** Not built. The held view shows nothing under the handguard: the left hand is overhand, with its fingertips wrapped under the lower bevel, and an underbarrel part would collide with them. The icon's long underbarrel module belongs to the 9 in-handguard icon gun.
- **Sling.** None is visible in either view. Only the attachment points are built: QD sockets in the end plate (both sides), in the stock's front lug (right) and in an M-LOK slot on the handguard's left side.
- **Magazine.** It is drawn straight and rotated about 30° relative to its own receiver. Built as a seated PMAG with its real curve.
- **Handguard length.** The drawn handguard ends about 4 cm short and the muzzle stub is drawn about 5 cm long. The real MCMR-13 is kept, so only 86 mm of barrel and A2 shows, where the image shows about 138 mm.
- **Receiver size.** The drawn receiver is 12 to 34 % oversize relative to the pinned real rifle. Built to the real size.
- **Tan accents.** Kept as thin painted plates in the drawing's places: the stock stripe, the stock front lug (painted QD frame), a stripe on the upper's rear right, a small mark on the lower, a patch at the magwell front, and two patches on the handguard's rear right. The upper stripe is cut short so that it ends behind the forward assist.

## 4. Colours (flat, sampled from the reference, weapon analysis §3.15)

| Parts | Colour |
|---|---|
| Receivers | #3e3a38 |
| Handguard | #393532 |
| Hardcoat (tube, light, optic) | #2c2a29 |
| Stock | #3d3733 |
| Grip and trigger guard | #1f1d1c |
| Butt pad | #141211 |
| Magazine | #423e3a |
| Floorplate | #595452 |
| Barrel and A2 (bronze) | #5f4c3e |
| FDE paint | #b08a62 |
| Steel | #2f2e2e |
| Lens | #0e1418 |

These are the image's lit values used as albedo, so they are not calibrated.

## 5. Round 1 (2026-11-14)

**Built:** every major component as its own object (46 objects).
- Upper (with the port cut through its wall), forward assist, deflector, open dust cover, bolt carrier visible in the port, charging handle, upper rail.
- Lower (with the magwell, flared lip and opening), trigger guard, trigger, mag release, bolt catch, selector.
- A2 grip, lofted with its finger nub.
- Buffer tube, castle nut, QD end plate.
- Stock (outline with its window, tube housing), butt pad.
- Barrel (stepped government profile), gas block, gas tube, A2 (five slots, closed bottom).
- Handguard: octagon tube with rail, M-LOK slots and lightening holes.
- Light, lens and offset mount.
- Optic, turrets, lenses and mount.
- Magazine (constant curve, three ribs a side) and floorplate.
- Seven paint patches and the two hand empties.

**Method:** all the geometry is closed primitives; slots, holes and the port are cut with EXACT booleans (self-intersection on). The flat parts get Bevel and harden-normal modifiers. The .blend starts from an empty factory scene, so the build is idempotent.

**Renders looked at:**
- `carbine_left_ortho.png` and `carbine_right_ortho.png`: Workbench material colours with a 100 mm bar.
- `carbine_top_ortho.png`: muzzle to the right, the gun's left at the top.
- `carbine_34_clay.png`: Workbench clay.
- `carbine_34_cycles.png`: OptiX, three area lights.
- `carbine_hero_vs_ref.png`: the reference crop, the Cycles render at take 1's spec 08 placement through the reference camera, and the render over the reference.
- The first Cycles pass was blown out (260 W key on a 1 m object) and was fixed to 45/12/40 W.

**What the renders show:**
- It reads at once as an M4-pattern carbine with a free-float M-LOK handguard, red dot, side light and PMAG, at the right proportions against the scale bar.
- In the hero direction the orientation matches the reference.
- The real gun's receiver lands up and left of the drawn one, the magazine hangs about 30° more forward than drawn, and less muzzle shows. These are the accepted reality-wins deviations above.

## 6. Still wrong or missing, ranked for round 2

1. **Receivers are slab boxes.** The forged upper's shape is missing: the front ring and the step down to the lower, the rear "ears", and the takedown and pivot lug bosses. So is the lower's: the rounded magwell front, the trigger-guard ears, the pin bosses and the rear tower blend. Together these are what makes a gun-literate eye say "M4", and they are the biggest gap.
2. **Forward assist reads as a long tube lying beside the port.** It is too long and too low, and in the side view it looks like a second barrel. The deflector is too small to read. The dust cover is a flat rectangle hanging straight down, where the real cover is open at about 165° on its hinge rod.
3. **Stock.** The outline is a trapezoid window in a thick slab, and the tube housing is a plain cylinder. The Minimalist's skeletal frame, the latch and the sling slots need the catalogue outline. The reference also shows a glossy tube along the stock top; decide whether the housing should read glossy.
4. **Grip** is a smooth loft. It needs the A2's straight back strap, flat sides and finger-nub profile, checked against a photo.
5. **Hero placement** uses take 1's spec 08 solve. The pose agent's own solve should replace it, then the overlay should be re-run, comparing the grip pin and the butt-pad contact.
6. **Colours** are lit samples used as albedo. In Cycles the receivers read mid-grey-brown and lighter than the reference, and the FDE is too bright and saturated. Calibrate under the evaluation lights.
7. **Handguard:** no rear clamp screws, no QD insert detail, no front-cap chamfer detail; the rail ends are square.
8. **Optic and light** are plain lathes. They lack the T-2's square body flats and lens hood, the LRP lever shape, and the M300C's tail-cap shroud and knurl.
9. **Magazine:** no dot-matrix panel, texture, bolt-catch notch or over-travel stop. Rib proportions are unchecked against a PMAG photo.
10. **Not built:** pins, the selector's right-side axle, T-marks, markings, the sling itself (none in the reference), the barrel nut, and the bolt-face detail inside the port.
11. **Mass** depends on guessed fill factors; replace them with real component masses (take 1 §3.14) when they matter.
