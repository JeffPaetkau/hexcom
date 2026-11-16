# Carbine

Build: `"$SGT_BLENDER" -b --python scripts/parts/carbine.py [-- --no-render] [--keep-scene]` (about 9 s
without renders, 50 s with them, on the RTX 3050), or `"$SGT_PYIMG" -I scripts/assemble.py --rebuild carbine`.
Output: `cache/parts/carbine.blend`, `renders/carbine/*.png`, `renders/carbine/measure.json`.

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
  - Round 2 did not move either empty: the grip's right face at that station and the handguard's bevel stayed where they were. The script measures the gaps on every build (`measure.json` `grip_empty_gap_mm`: 0.54 and 0.56 mm). Object names the pose solve reads, `Carbine.Grip` and `Carbine.Stock.ButtPad`, are unchanged. The A2 grip's outline did change slightly (finger groove, nub, beavertail), and so did the pad (grooves); the pose agent's voxelised carbine should be re-exported.

## 2. Dimensions built (mm; sources in take 1 spec 15 §3.15 and weapon analysis §2)

The script measured the following on the built meshes (`measure.json`, round 2):

| Quantity | Built | Real / source |
|---|---|---|
| Overall length, butt heel to A2 front | **855.7** | 16 in carbine: 794 collapsed to 876 extended, so position 3 is about 856 (research_dimensions §12) |
| Barrel, bolt face to crown | **406.4** | 16.0 in |
| Barrel and A2 ahead of the handguard | 86.3 | the MCMR-13 is 340.4 long; the A2 is 44.5 × 21.8 |
| Height, optic top to floorplate | 300.9 | T-2 axis 39 mm above the rail (LRP + 39 mm spacer) |
| Height without the optic | 240.0 | rail top +30.2 above the bore (A2 sight height 2.6 in minus 1.41 in co-witness) |
| Height without the optic or magazine (rail top to grip bottom) | 174.5 | A2 grip is about 102 tall, raked 25° |
| Width overall | 68.5 | includes the light on its offset mount |
| Width of the upper across the forward assist | 46.3 | walls 31.0; the forward-assist housing 15.5 proud of the right wall (take 1 §3.2: X +31.5) |
| Length of pull, trigger face to pad centre | 292.8 | short pull, right over plate armour |
| Stock pad rake | 12.2° | the Minimalist's angled pad |
| Magazine floorplate tilt | 15.2° | PMAG 190.5 × 66 × 22.1, constant curve |
| Rail recoil slots | 20 on the receiver, 34 on the handguard, one phase (the joint falls inside one slot) | MIL-STD-1913: 10.01 pitch, 5.23 slots, 3.0 deep, 21.2 top, 45° flanks to the 15.67 neck |
| Rendered triangles, whole carbine | 70.1 k | take 1 §4.18 budget 143 k; no Subdivision |

Other built dimensions:
- **Receiver:** upper 197 long, walls 31.0 wide, a 22.6 deck under the rail with 45°-ish shoulders, carrier bore Ø25.6 hollow behind the port, front lower corner rounded r 7. Lower: pocket walls 30.0, magwell 27.6 with front corners r 7, flaring at the lip to 31.6 wide (3.0 forward, 1.0 back), 67 × 23 opening with a 2.2 inner flare. Buffer-tower boss Ø35.6, cut flat at z +11.6 under the charging handle.
- **Port:** ejection port 76.2 × 20.3 with r 3 corners; the dust cover (78.7 × 23.4 × 1.6) hangs open on a Ø2.4 rod in two hinge bosses, its latch bump outward.
- **Forward assist:** Ø19 housing on an axis 13° out from the bore in plan, rising out of the wall as a teardrop boss; Ø14 round button, 11 mm behind it, with a grooved face. **Deflector:** wedge behind the port, ridge 9.5 out from the wall.
- **Lower controls:** pin heads Ø9.5 (right) and flush ends (left) at the pivot and takedown pins, hammer and trigger pin ends Ø3.9, mag release Ø9.5 in a 160°-to-340° fence 2.2 proud, bolt catch with a 4-rib paddle (left), selector lever on SAFE (left) with its axle end on the right, trigger guard a 6.5 × 5.5 bar.
- **Handguard and rail:** octagon 38.1 across the flats, 33 ID, rear collar 39.7, front chamfer 2. M-LOK 32 × 7 slots (r 2.4) at 3, 6 and 9 o'clock, 8 per face on a 40 pitch. Seven Ø10 holes on each lower bevel at 26 mm pitch. Two clamp screws in the rear collar's lower bevels.
- **Receiver extension:** buffer tube Ø29.16 with its bottom rib, castle nut Ø36 with three notches, QD end plate.
- **Stock (round 4):** 180 × 128 (real 180 × 133 × 44.5), a rounded 34 × 37 tube housing, a 16 mm skeleton plate: the rear post widening from 17 to 42 mm to the 44.5 wide pad, one diagonal strut (14 mm) from the toe up to a front junction under the housing (22 wide, down to z −44) with the QD socket through it (both sides, at x −146.7, z −31) and the tan frame round it; a sling slot through the toe block. Round 2's bottom rail and the front lug to z −96 are gone (§8).
- **Light:** M300C, 104 long with a Ø28.6 bezel and a knurled Ø24 tail cap with its shroud, axis at y −32, z +16.

**Mass.** The script sums each component's mesh volume × density.
- The closed volumes (now hollow where the real parts are hollow: the upper's bore, the stock's window and channel) weigh 4.34 kg solid.
- With per-component fill factors it is **3.01 kg empty and 3.37 kg loaded** (30 × 12 g rounds). Fill factors are the fraction of each closed volume that is material in the real part, e.g. upper 0.75 and the magazine 0.2.
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

**Round 2 materials.** The hexes above remain the solid-view colours (the Workbench ortho views). Cycles now uses:
- `Carbine.Mat.Anodised`, `.Handguard` and `.Hardcoat`: the library's `Metal.Gunmetal` recipe (`scripts/lib/mat_hard.py`), re-tuned toward black Type III hardcoat. F0 is about 0.04 (0.05 for the semi-gloss hardcoat on the tube, light and optic), roughness 0.46 to 0.64 (0.28 to 0.40 semi-gloss), no anisotropy. Edges wear to bare aluminium (F0 0.62) through the library's bevel edge mask (radius 0.35 mm, amount 0.35 to 0.45), and the recipe adds its dust and grime.
- `Carbine.Mat.Polymer`, `.PolymerDark` and `.Magazine`: `Polymer.Black.Smooth` re-coloured to albedo #232120 (stock), #1e1d1c (grip, trigger guard) and #3a3835 (the PMAG).
- Flat colours for the rest: FDE (now #9a7a58, rougher), bronze, steel, rubber, lens and the floorplate (#4a4644).

The library names a material `<Part>.Mat.<ID>`, so one recipe could make only one material per part. `lib_material()` therefore renames each result.

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

## 6. Round 2 (2026-11-14): the forms of the real parts

**Method.** Each hull is now one manifold solid. Parts are built from closed primitives:
- prisms of filleted outlines (`fillet()`), with n-gon caps;
- lofts of rounded sections (`loft()`, `rect_f()`);
- lathes, and convex hulls (`hull()`).

These are joined by EXACT unions and cut by EXACT differences, then smoothed by angle and finished with a Bevel plus a Weighted Normal modifier. The weighted normals replaced the bevel's harden normals: the large flat n-gons had been shading with diagonal seams. There is no Subdivision anywhere. Every mesh is manifold (`measure.json` `non_manifold_edges` is empty), and the whole gun renders 70 k triangles. Take 1 never built the carbine (spec 15 only), so what was reused is its §3 dimensions and §4 construction plan.

**Built:**
- **Upper.** The section has walls, shoulders and the rail deck, and the 1913 rail is integral, with the real dovetail profile and its slots on one phase with the handguard rail. The carrier bore is hollow, so the port opens onto the carrier, which shows its forward-assist serrations and its bolt. Also built: the forward-assist teardrop boss and round button, the deflector ridge, hinge bosses with the rod, and the open dust cover with its curl and latch bump. The charging handle has a left latch with grooves.
- **Lower.** The pocket body carries a lofted magwell with rounded front corners and a flared, rounded lip, plus the opening and its inner flare. The pivot-pin lobe, trigger-guard ears and mag-release fence are on the right; the bolt-catch boss and selector boss are on the left. The tower boss is flat under the charging handle. Separate small parts: pin heads, pin ends, selector axle end, mag release, ribbed bolt catch, selector lever on SAFE, trigger, the swept trigger guard and its pin.
- **A2 grip.** A 15-section loft with a beavertail, finger groove and nub, flat sides and round straps, and a hollow open bottom.
- **Stock and tube.** A Minimalist skeleton: housing, plate with the window, a rear post widening to the pad, and a front lug with the sling loop. The pad is grooved. The buffer tube has its rib, the castle nut three notches, and the QD end plate a bored socket.
- **Handguard.** Octagon with the integral rail and slots, rounded M-LOK slots, holes, and two clamp screws. The handguard QD socket is lathed.
- **Light, optic, muzzle.**
  - Light: knurled tail cap with its shroud, body, head cone, a bezel ring groove and a recessed lens. Its mount has screw recesses.
  - Optic: T-2 body with its hood, the turret block and base block, fluted-cap turrets, and the LRP riser with its lightening window and a throw lever.
  - A2: rounded-end slots and wrench flats.
- **PMAG.** The section is resampled to 240 points, so the three ribs a side are lofted into the body and taper in and out. Below the magwell lip a 63 → 66 step stands in for the over-travel stop. The floorplate is flared, with its front lip.
- **Paint.** The patches moved onto the new surfaces:
  - the stock-lug patch is now a frame round the sling loop, which is what the drawing's tan frame with a dark interior is;
  - the handguard patches have the M-LOK slots cut through them;
  - the upper stripe stays on the flat wall.

**Renders looked at** (all in `renders/carbine/`):
- `carbine_right_ortho.png`, `carbine_left_ortho.png`, `carbine_top_ortho.png` (100 mm bar);
- `carbine_34_clay.png`, `carbine_34_cycles.png`;
- `carbine_receiver_R_clay.png`, `carbine_receiver_R_cycles.png`, `carbine_receiver_L_clay.png`, `carbine_receiver_L_cycles.png`: new closeups, 70 mm lens;
- `carbine_hero_vs_ref.png`.

**What they show:**
- From the right it now reads as an M4: port with carrier and serrations, hanging dust cover, forward assist and deflector, mag release in its fence, pivot and takedown pins, A2 grip with nub and beavertail.
- From the left: bolt catch, selector and pin ends.
- From above: the light offset at 2 o'clock and the deflector and forward assist standing out on the right.
- In Cycles the receivers are dark with a soft sheen and lighter edges.
- First pass: diagonal shading seams crossed the flat sides of the upper and lower, and the deflector was a flat-faced block. Both were fixed (weighted normals; a ridge-shaped hull).
- In the hero direction the silhouette lies on the reference as in round 1. Under that view's studio key the receivers and stock still read mid-grey, lighter than the reference's dark gun. It is a different light from the evaluation scene; judge it in the round's hero frame.

## 7. Still wrong or missing, ranked for round 3

1. **The lower is still a flat slab on its sides.** A forged lower has relief that catches light and reads in the hero frame:
   - the rear takedown lobe and tang curve;
   - a raised rim round the trigger-pocket walls;
   - the magwell's side pockets (left);
   - the curved transition from the magwell's rear into the trigger-guard area;
   - the grip's top meeting the lower's angled tang.

   The upper's right wall above and ahead of the port is also one flat plane. Next round: a side-profile relief pass on both receivers, judged against a photo.
2. **Finish under the evaluation lights.** Check the receivers, stock and paint in the round's hero frame (the carbine's own studio key reads them lighter than the reference):
   - the rail-tooth tops read nearly silver (edge wear plus the key on the flat tops);
   - the FDE patches are flat stickers with hard edges, needing chipping and wear, which is the library's planned `chips` (NotBuilt);
   - the grip checkering and the PMAG texture and dot-matrix panel are not in any material.
3. **Trigger guard** is still a round-cornered loop. The mil-spec guard is a flat band with a squarer front drop and a hinged front with a plunger. The trigger blade is a plain extrusion.
4. **Stock:** round 4 rebuilt it as the real Minimalist's three members (§8); still unchecked against a catalogue photo: the housing section (round or squared), the cheek riser, the exact strut angle. The latch lever is not built.
5. **Forward assist and deflector:** better proportioned, but still a cylinder plus a hull. The real forging blends the two into one sculpted boss, and the deflector's top runs into the rail deck.
6. **Optic and light:** the T-2's square body sides, battery cap, brightness dial and tethered caps are simplified. The LRP's clamp shape and the light's window and TIR are absent.
7. **PMAG:** ribs only on the lower body. There is no bolt-catch notch, and no front and rear texture.
8. **Not built:** markings and T-marks, gas-block set screws, the barrel nut, BCG details beyond serrations, the dust-cover spring, the buffer-tube position holes, the sling itself (none in the reference).
9. **Hero placement** still uses take 1's spec 08 solve in this part's own hero check. The pose agent's solve is the one that counts.
10. **Mass** fill factors are judgement; replace them with real component masses (take 1 §3.14) when they matter.

## Round 1's ranked list (kept for the record; round 2 addressed items 1 to 4 and 7, partly 8 and 9)

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

## 8. Round 4 (2026-11-15): the stock checked against the real part

**What was wrong.** The pose round (scripts/stages/README.md, round 2, "Still wrong" 1) found the stock's front strut
hanging to z −96 only 30–35 mm behind the A2 grip's back strap, where the firing hand's web and wrist go: the right hand
had to turn about 30° on the grip to pass it. Round 2's outline was a closed frame (housing, rear post, a bottom rail from
the toe and a front lug hanging below the housing's front), which is a fixed-stock shape, not the Minimalist's.

**The real part** (MFT BATTLELINK Minimalist, mil-spec; retailer specifications): 7.08 × 5.22 × 1.75 in (180 × 133 ×
44.5 mm), 5.8 oz; a skeleton of the tube housing, the rear post to the angled rubber pad, and one diagonal strut from the
toe forward and up to the front of the housing, where the latch and a single ambidextrous QD socket sit ("forward/bottom
portion"); several sling slots. Under the housing's front it is open. On an AR-15 the space directly behind the A2 grip
and under the receiver extension is empty down to the hand: the only parts there are the castle nut and the QD end plate
(to z −32 here, which is real).

**Built** (`build_stock_and_tube`): the outline is the housing, the post and the strut from the toe block (solid below
z −82, with a 24 × 7 sling slot) up at about 37° to a junction under the housing's front, x −166.7 to −126.7, its lowest
point z −44 (was −96); a quadrilateral window between them. The QD socket is a through-bore with a steel cup on each side
(`Sling.Stock.QD`, `Sling.Stock.QD.L`); the drawn tan frame (`Paint.StockLug`) is now on the junction's right face round
the cup. Length of pull 292.8 mm and the pad (12.2° rake) are unchanged: about position 2–3 of 6 on a mil-spec tube
(collapsed about 268 mm here; real carbine stocks collapse to about 10.5–10.75 in and step about 0.65–0.75 in), within a
position of the "position 3" label, so it was left (moving it moves the butt contact the pose solves).
`Carbine.Root`, the grip empties (gaps 0.54 / 0.56 mm) and every name the pose reads are unchanged; `measure.json` adds
`stock_qd_xz_mm` and `stock_front_junction_bottom_z_mm`.

**Renders looked at:** `renders/carbine/carbine_right_ortho.png`: the stock reads as the Minimalist (the diagonal strut
from the toe to the front junction, the tan frame round the QD cup), and the space behind the grip is open below the
end plate.

## 9. Round 5 (2026-11-15): materials

- `lib_material()` now asks the library for a **variant** (`materials.get(recipe, "Carbine", key, ...)`), so the
  library itself names the material `Carbine.Mat.<Key>` and lint checks it (round 2 renamed the result, which
  broke lint's name rule).
- Round 2's hardcoat and polymer kept, retuned against the hero render. A first darkening (F0 0.032) put the
  carbine's median at about half the reference's (ratio 1.95: the drawn rifle reads a lighter grey with a broad
  sheen), so the anodise sits at F0 0.060, roughness 0.50-0.66, dust 0.15-0.2 (honest wear: the edges to bare
  aluminium as before, dust in the low spots); stock #2e2d2b, grip #222120 (the plastic floor), PMAG #403f3d.
- The remaining flat colours moved onto recipes: bolt carrier and pins `Metal.Steel.Phosphate` (new), polished
  parts a bright gunmetal, barrel and A2 `Coating.Cerakote.BurntBronze` (new), the tan stripes
  `Paint.FDE.Brushed` (new; the painted builder, chipped to the black beneath), the butt pad
  `Rubber.Moulded.Black`, the floorplate a grey polymer, the glass `Glass.Optic.Coated` (new).

Renders opened: `renders/round_05/hands_rifle_compare.png`, `torso_vest_compare.png`. Median ratio 1.15 (still a
little dark), warm under the key like everything else.

Still wrong (materials): no markings, no bead-blast micro-structure (spec 16's MG.Anodise is not built), no
carbon soot at the muzzle.

## 10. Round 8 (2026-11-15): the look (critic m5)

- **The muzzle device and barrel are dark** (m5): round 5's Burnt Bronze Cerakote (take 1 D3) read as bare copper
  against the black gun. The slots are now `Carbine.Mat.Barrel` (manganese-phosphate steel, F0 0.055, edges worn
  45 %) and `Carbine.Mat.Muzzle` (black phosphate, F0 0.045, rougher, sooty grime, its tines' edges worn to grey
  steel); the round-5 `Bronze` slot is gone.
- **The tan stripes are muted** (`Paint.FDE.Brushed` #8a6a48 -> #857560, roughness 0.70, chips denser within 4 mm
  of the stripes' edges): the reference's accents read #9f8060 lit under its warm key, not orange.
- **The gun is a dark grey with a sheen, not flat black**: the hardcoat's F0 0.060 -> 0.080 (roughness 0.46-0.62),
  polymer #2e2d2b -> #333231, the PMAG #403f3d -> #434240. In the look loop (round-6 pose) F0 0.095 gave a graded
  median ratio of 1.14 (1.95 before, with the light corrected); in round 8's pose the same values read 0.66 (the
  gun turned more to the key), so they were brought back to 0.080.

Look-loop renders opened: `renders/look/M*/sheet_hands_rifle_graded`, `sheet_torso_vest_graded`.

Still wrong: no markings, no carbon soot at the muzzle beyond the grime, the drawn receiver's worn highlights.
