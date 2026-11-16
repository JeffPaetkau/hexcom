# Boots

Build: `"$SGT_BLENDER" -b --python scripts/parts/boots.py [-- --no-render]` (about 40 s with renders on the
workstation). Output: `cache/parts/boots.blend` (collection `Part.Boots`), `cache/parts/boots.json`,
`renders/boots/*.png` (rest views, the hero pairs, and four closeups of the left boot: `boots_closeup_L_*`).

## 1. What it is

**Identity:** a LOWA Zephyr MK2 GTX Hi TF class tactical boot. Its construction is:
- 210 mm outside height;
- a leather and Cordura upper;
- a DuraPU double-density midsole on a rubber outsole;
- a padded collar and a gusseted tongue.

Sources: take 1 `archive/v1/spec/02_boots.md` §2 to §3, which cites LOWA's product pages (its S1 to S4) and a
measured review (S4: stack heights, lug depth, drop).

| Quantity | Real / source (mm) | Built, round 2 (mm) |
|---|---|---|
| Outsole length | 300 to 305 for this 274 mm foot (spec 02 §0, last 297 + 5 + 3) | 306 (upper 300, toe room 10 past the 5 mm offset) |
| Outsole width at the ball | about 116 | 124 (upper 116 + 2 x 3 sidewall; see §5 item 6) |
| Heel seat (floor to footbed) | 36 (S4: 36.3) | 36 |
| Ball seat | 24 (S4: 23.7), so the drop is 12 | 24 |
| Midsole stripe top (floor) | stripe and rand: 49 to the rand top at the heel, 23 at the ball | stripe 40 / 21 / 19 (heel, ball, toe), rand 10 above it, 12 at the heel, rising to a 26 mm toe bumper |
| Lugs | 4.5 to 5 deep (S4: 4.7); perimeter teeth 15 / 30 pitch, forefoot chevrons, waist bars, heel blocks | 5 deep (waist bars 3), teeth 15 forefoot / 26 behind, teeth wrap 3 up the sidewall; 2 x 3 heel blocks, about 400 lug faces a boot |
| Toe spring | 15 | 15 (quadratic from the ball line) |
| Rim height above the floor | 212 at the sides (S1: 210 outside), Achilles notch 206 | 212, notch 6 deep |
| Shaft outer section | 128 x 100 at h 110, 136 x 104 at h 158, 138 x 106 at the rim (drawing) | the same ellipses (at least), centred on the shin, narrowing 22 % into the heel counter |
| Throat | E1 at h 85 to 95 on the real last (spec 02 §0 item 6); gap 30 at E1, 44 at the top | E1 at h 97 (60 % of the length from the heel), gap 30 to 44, stays 22 wide standing 2.4 proud |
| Eyelets and hooks | 5 eyelets (flange 10, hole 5.5) + 2 speed hooks | the same, as rings and a plate with a bent wire |
| Lace | round 4 mm, criss-cross | 4 mm tubes, criss-cross with one strand over the other, a bar at E1 |
| Tongue | top at h 222, 12 thick | top 10 above the rim, 6 thick (Solidify) |
| Padded collar | about 22 tall x 10 thick | 22 x 10 roll behind the stays, tapering into them |

## 2. What the reference shows

Evidence: `ref/crop_boots_feet.png`, `ref/zoom_boots_*`, spec 02 §2.
- Black smooth leather with dust.
- A chunky lugged sole with a toe bumper.
- Five eyelets and two hooks with laces.
- A cuff strap with a buckle.
- A padded collar under the stacked trouser hems.
- The right boot is seen in profile (pointing to his right); the left faces the camera with its laces centred
  (round 2 measurement: about 5 degrees to his left, not the pose's 15.5, see §4).

## 3. Departures and why

- **Not built yet:** the cuff strap and buckle (the drawing's identity, not the Zephyr's), the pull loop, the
  stitching (`gn_stitches.py`), the toe bumper's emboss, sipes, the heel rocker.
- **Length:** reality wins (CLAUDE.md): 306 mm outsole for the 274 mm foot, though the drawn boots look shorter.
- **The feet stand inside the soles** below the footbed (clash list: body in boot soles, designed). The toes
  also pass through the sprung toe's floor; a footbed cavity can wait.

## 4. Round 2 (2026-11-14)

**The upper is a last's form, not the skin's.** Round 1 offset the skin and bridged the toes with convex
hulls, which read as a clog. Round 2 (`Last` in `boots.py`):
1. The foot and lower leg skin is refined twice and offset 5 mm (6 over the top): the cloud the upper must
   hold.
2. **The foot:** every 4 mm along the foot, the convex hull of the cloud's slice across the foot; its half
   widths, medial and lateral of the crown, per 3 mm height band. Behind the instep only the part below
   60 mm belongs to the foot; the ankle above that belongs to the shaft.
3. The ends: the toe is the nose station's section shrunk elliptically over 50 mm in plan and squashed in
   profile, 10 mm past the offset toes; the heel is a half-ellipse in plan.
4. **Smoothing in each section's own height fraction** (0 at the base, 1 at the top): an upper envelope
   along the foot on the top line and on the widths at each fraction. Smoothing in absolute height bands
   instead let the instep's height spill forward and raised the toe box by 20 mm. Widths never grow upward,
   so everything stays inside.
5. **The shaft:** horizontal ellipses centred on a straight line fitted through the shin's slices, at least
   the drawn axes, grown to contain the ankle, narrowing 22 % below h 130 into the heel counter and running
   down into the sole. If the shaft stops at a height, a shelf forms where it meets the foot.
6. A smooth union (radius 16) of foot and shaft, cut at the rim (6 mm Achilles notch) and at the sole top
   less 4.
7. Meshed by first-exit ray casting from a point inside, 240 x 210, first row on the rim. Despiked,
   Taubin-smoothed and pushed out to 2.5 mm from the skin (0 to 8 vertices need it).

**Overlays and throat.** Leather (toe cap, heel counter, quarters below h 98) stands 0.8 mm proud of the
Cordura shaft panels; the toe cap and the counter take another 0.8. Three flex creases cross the vamp behind
the toe cap, deeper laterally (the take 1 test boot's pattern). The throat's centre line runs from the rim
down the shaft front and over the instep (`Throat`). E1 sits at 60 % of the boot's length and the 7
positions are evenly spaced above it. The tongue and gussets sit 1.2 mm below the quarters between the
stays. The stays, tongue top, collar, eyelets, hooks and laces are separate objects; the laces lie at a
constant height over the surface cast under each point.

**Rand and sole.** Both use horizontal sections of the upper at the stripe top (casts from inside the
forefoot). The rand's upper rows follow the upper's 3-D normal, so the bumper lies on the toe box's slope
instead of standing off it as a lip. The sole and lug layer are as in §1.

**Materials.** The take 1 boot recipes drop in (`apply_library`):
- leather and Cordura on the upper, with UV.Real from the grid's arc lengths;
- leather on the stays and tongue, Cordura on the collar (UV.Real by principal axes);
- the rand and outsole rubbers, the PU midsole, gunmetal hardware, the nylon lace;
- dust zones from `boot.toe`, with the left boot the dustier.

If the library raises, the flat colours stay.

**Measured** (`boots.json`): outsole 306 x 124, posed lug bottoms at -3.3 (L) and -2.9 (R) mm, so the
3 mm sink of round 1 is unchanged (a round 0 item). Posed headings: L 15.5 degrees to his left, R 83 degrees
to his right. Clearance: 0 vertices inside except one stray vertex of `Boot.R.Upper` at rest
(-213, 66, 91), behind the right heel, reported 18 mm inside the skin. It survived the neighbour-mean
repair and the push-out, so it may be a sign error of the nearest-face test there; it is not visible and the
clash test does not list it.

**The left boot's heading and length** (round 1 integration item 1). Its silhouette still reaches past
the drawn toe to the viewer's right in `renders/round_02/boots_feet_overlay.png`. Projecting the posed toe
through `eval/camproj.py`, the drawn toe's x (935 px) matches a heading of about 5 degrees, not the pose's
15.5. Length cannot be judged from the image: its floor perspective is about 150 mm inconsistent in depth
(`floor_point` puts the drawn right toe 150 mm behind ours at the same x). **For round 0: turn the left foot
to about 5 degrees.** The boot follows the foot bone. Length stays real.

**Renders looked at.**
- `boots_closeup_L_lateral`, `_front34`, `_medial_back`, `_below`: these read as a laced high boot. Low toe
  box with toe spring and a bumper, vamp and creases, lace throat with stays, eyelets and laces, quarters
  with the counter and the Cordura line, padded collar, lugged sole.
- `renders/round_02/boots_feet_compare.png`: the right boot's profile lies on the drawn one from heel to toe.
  The left boot faces the camera with the laces visible below the hem.
- In Cycles the leather shows grain and sheen.

## 5. Still wrong, ranked for round 3

1. **Left boot heading** (round 0): about 5 degrees instead of 15.5 (§4). Until then its toe stands about
   6 cm too far to his left in the hero frame.
2. **The shaft is a stovepipe.** It is a plain cylinder from the counter to the rim, wider than the heel
   (real, but stark). The drawn shaft follows the shin with ankle padding, and its throat side is open in the
   lace area. The shaft-instep junction shows faceted crumples in the clay renders (the smooth union, plus
   the Cordura step and creases there).
3. **Lacing too short and high.** E1 at h 97 (this foot's high instep; the drawn E1 is at h 72 to 80). The
   stays are thin flat strips and the hooks read as boxy flags. They sit mostly above the hem, so they matter
   little in the hero frame.
4. **No cuff strap and buckle** (the drawing's identity), no stitching, no pull loop.
5. **The toe tip** has a small crease where the rounded nose meets the bumper's top rows. The bumper's top
   edge is plain, with no lip detail or emboss.
6. **Width:** the outsole is 124 at the ball against the real boot's ~116. The forefoot follows this foot's
   99 mm skin width + 10 mm of offset + 6 mm of sidewall. Thin the sidewall at the ball, or the offset at the
   sides.
7. **Wear:** no creases at the ankle break, no collar slump, the pair is still a mirror image, and the dust is
   from zones only (no baked masks).
8. The 3 mm sink into the floor in the pose (round 0, unchanged). One stray upper vertex on the right boot
   (§4).

## 6. Take 1's foot and boot work: reuse it (Jeff, 2026-11-14)

Jeff: "For the foot and boot work it's probably worth referencing all the work we did in the
previous iteration." Take 1 spent three weeks here; round 3 starts from it, not from scratch.

- **The boot spec, revised for building on 2026-10-27**: `archive/v1/spec/02_boots.md`. §0 holds
  the settled decisions (reality wins: Lowa Zephyr / Garmont T8 class, the pair not a mirror, the
  trousers stacking on the collars, the strap as a three-quarter ring, the footbed 36/24); §2 the
  measured reference (extents, colours, construction cues read from the zooms); §3 the real
  boot's dimensions (sole stack, upper components, lugs, hardware, laces, strap, how it wears);
  §4 a twelve-step construction plan (last, sole outline and lofts, lugs, upper shell and throat,
  overlays, rand and bumper, collar, tongue and gussets, hardware, stitch rows, strap, laces with
  the exact criss-cross routing and over/under order, joins, topology budget, "against the
  mechanical look" §4.15); §5 materials and wear masks. Its questions Q13-Q19 are in §10.3 (Q13:
  the real footbed lifts 33 mm, not 42).
- **The last** (take 1 part 01, `archive/v1/scripts/parts/p01/last.py`): built on the loaded,
  scan-shaped foot with real allowances, the toe room measured from the standing socked toe
  (Jeff: "Reality"), 297.1 mm long (right 297.0), 12° toe spring, markers on the insole plane.
  The boot is built round the last, which is built round the foot.
- **The library made for this boot**: the twelve boot recipes and seven groups in
  `scripts/lib/materials.py` and `mat_*.py` (tested on a stand-in boot: `archive/v1/scripts/
  lib_gear.py`, take 1's renders under `renders/16_materials/` and `renders/lib_gear/`), and
  `gn_stitches.py` (3.4 mm pitch, felled ridges, bar tacks), `gear_hardware.py` (eyelets, speed
  hooks, ladder-lock, aglets: quad-only, no triangle fans), `gear_webbing.py` (the ankle strap,
  keepers, pull loop), `sweep.py` (laces), `modifiers.py`, `uv.py`. Spec 02 §4.9 has the as-built
  notes (bar-tack pitch 0.6, hook plate 12 × 13 × 1, the welt as swept geometry).
- **Lessons**: triangle fans under Subdivision cost minutes per Cycles render; the scuffs read as
  horizontal dashes; the reference has stronger contrast and a warm/cool split than the stand-in;
  real boots leave 15-22 mm ahead of the standing toe.
- **Optional references**: spec 02 §3.6 lists two licensed boot scans on Sketchfab (Garmont T8,
  Danner TFX) that Jeff would have to download himself.

## 7. Round 3 (2026-11-15; developed on `cache/stages/foot_dev.blend`, cache `boots_dev`)

Build (development): `"$SGT_BLENDER" -b --python scripts/parts/boots.py -- --base cache/stages/foot_dev.blend
--tag boots_dev` (about 2 min with renders), then `"$SGT_PYIMG" -I scripts/parts/boots_sections.py --tag boots_dev`.
Once the foot is in base.blend the defaults (`--base` base.blend, `--tag boots`) are the pipeline's. It needs the
body's `Foot.Contact`, `Foot.NailBed.*` and nail plates (scripts/stages/foot.py) and raises without them.

**What changed, from take 1's work** (Jeff: reuse it; PLAN.md Decisions 3: Q14 smooth full-grain, Q15 Cordura,
Q16 buckle at phi 150, Q17 no reference scans, Q18 rigid):
1. **The sock** (take 1 part 01 §4.10-4.11, `stages/foot/sock.py`): `Sock.{L,R}.Body` in Part.Boots, 155 rings
   x 96, a membrane 0.3 mm off the rendered skin with its nails, Solidify by region (leg 1.6, cuff 2.4, heel and
   toe 2.2, sole 3.0), the GN knit ribs, `Knit.Sock.WoolNylon(.Reinforced)`; bound to the rig like a garment.
2. **The last** (part 01 §4.13, `stages/foot/last.py`): the loaded foot, socked at its loaded thickness, ball
   sides +2, instep +2, heel sides +1, the insole plane, the toe box stretched (x 1.44 over its front 45 mm) so its
   tip is 15 mm ahead of the standing socked toe, 12 degrees of toe spring about the 1st-5th metatarsal heads'
   line. Saved apart in `cache/parts/<tag>_lasts.blend` (`Boot.{L,R}.Last`, markers `.Pternion`, `.Ball1`,
   `.Ball5`, `.ToeTip`), out of the part, so the assembly's clash test never sees the foot inside it.
3. **The upper on the last**: round 2's implicit form, its cloud now the last grown 3.5 mm (leather 2.0 + lining
   1.5) and 9.5 over the ankle padding behind the throat, not the skin + 5. The sections' crowns are rounded (a
   soft |t|), the heel's rear 38 mm capped back to a half-ellipse (it was a flat-backed box), the nose a domed
   puff (e^0.55, not a wedge). The skin clearance signs by ray parity (the nearest face misread points behind the
   Achilles as inside and the push made spikes). Grid 300 x 240.
4. **The sole plane is the pose's**: 36 mm under the heel landmark and 24 under the metatarsal heads, exactly the
   points `pose_solve.py` seats (round 2 put 36 at 30 mm ahead of the heel landmark: its 3 mm sink).
5. **The throat** runs from the rim down the shaft front (horizontal casts from the shaft's axis; casts from one
   inner point left the shaft half way up, so round 2's top hook stood at h 168) and over the instep; the stays,
   eyelets and laces are laid in its own (arc length, across) coordinates by casts along the local normal.
6. **Library hardware**: `gear_hardware.eyelet()` x 5 and `speed_hook()` x 2 a side, seated with seeded error and
   oriented outward; laces criss-cross in the throat's coordinates, the strands taking turns over, slacker low.
7. **The cuff strap** (take 1's `lib_gear.build_strap`, on the real boot): 15 x 1.5 webbing at h 158 (159.5 on
   the right), anchored under both stays (phi -31 / +31), round the heel into a ladder-lock at phi 150, the lateral
   end threaded back through it and forward through the lateral keeper; leather keepers at phi +-72 with box-X
   stitches; fold and anchor bar tacks. 0 mm into the boot.
8. **Stitches** (`gn_stitches`, `Thread.Bonded.Black`): double rows on the toe cap's seam (136-141 mm), the
   counter's top edge (239), the leather quarters' edge under the Cordura (75 / 90), three rows a stay; about 560
   stitches, 1.4 m of thread a boot.
9. **Detail where the boot flexes** (spec 02 §4.15), seeded per boot (a pair, not a mirror): 2-3 dominant vamp
   folds along the oblique metatarsal heads' line, spacings 9-16, depths 1.5-2.4, wandering and fading to one side,
   5-8 fine wrinkles; 2-3 ankle-break folds on the quarters, deeper laterally; padding swells over the malleoli
   (the lateral lower); 16 short compression wrinkles on the Cordura.

**Measured** (`cache/parts/boots_dev.json`):

| Quantity | Round 3 (L / R) | Target / source |
|---|---|---|
| Foot (scan transfer) | 275.3 / 275.1 | 274.3 declared (CLAUDE.md: 274) |
| Last length | 297.07 / 297.05 | 297.1 (take 1) |
| Last tip ahead of the standing socked toe / bare toe | 14.98 / 17.5 (15.6 on the x 0 section) | 15 (Jeff: "Reality"; real boots 15-22) |
| Last toe spring, read on its bottom | 12.15 / 12.29 deg | 12 |
| Last width across the ball line | 114.7 | 038's broad forefoot + sock + 2 x 2 |
| Outsole length | 310.0 / 309.9 | 305 (spec 02 §0 note): +5 from the end allowances that let the ends round |
| Outsole width max / at the ball | 141.3 / 133.1 (R 141.0 / 132.3) | ~116 was for the stand-in last; this last is 115 wide |
| Rim above the floor at the heel; shaft at the rim | 212; 138 x 106 | 212; 138 x 106 (drawing; Zephyr Hi 210) |
| E1 (lowest eyelet) height | 90.9 / 91.5 | 85-95 on the real instep (spec 02 §0 item 6); drawn 80 |
| Lace rows, h | 198, 176, 153, 130, 111, 101, 90 | hooks 206 / 189 |
| Footbed seats | 36 / 24 at the pose's landmarks | 36 / 24 (spec 02 §0 item 2) |
| Posed lug bottoms | -1.6 / -1.8 mm | 0 (round 2: -3.3 / -2.9) |
| Upper outer face to the last | min -6.6, 1st percentile +5.3 | >= 3.5; the min is the nose rounding the last's square toe-box corner, above the toes |

**The footbed and the pose (the numbers).** The pose seats the rest skin floor (z 0) at 36 / 24; the last's
insole plane is the loaded sock's sole, 2.1 mm below that floor (`last.insole_z`), and the bare heel pad reaches
z -1.5. So inside the boot the sock sits 2.1 mm into the footbed's top. Exact would be the pose seating at
38.1 / 26.1, or the boot's seats at 33.9 / 21.9 (the pose's call; Q13's 1844 rebuild re-solves it anyway). The
-1.6 / -1.8 mm posed sink is measured against a pose solved on base.json's OLD foot landmarks; re-measure once
base.py runs foot.py and the pose is re-solved on the new ones.

**Renders looked at** (renders/boots/; round 2's are kept in `renders/boots/round2/`):
- `sheet_r3f.png` (lateral, front 3/4, rear, below, medial-back, right medial) and `boots_closeup_L_*`: a laced
  high boot, the lacing now from the instep to the collar, a cuff strap with ladder-lock and keepers, stitch rows
  on the toe cap, counter and quarters, a rounded heel from behind and in the sole's plan.
- `dbg_eyelets.png` (the lower throat): rolled eyelets seated on stitched stays, the laces entering them.
- `dbg_toe.png`: the toe box low and flat behind a near-vertical rubber bumper wall: still the weakest form.
- `boots_last_L_lateral/top/in_boot_lateral.png` (X-ray) and `sections_L.png` / `sections_R.png`: the last
  encloses the loaded foot with the toe room ahead and the sprung toe box; the upper stands outside the last at the
  ball and the heel; on the long section the upper's nose cuts the last's square toe-box corner by up to 6.6 mm.
- `sheet_sock.png`: the sock reads as a sock over the foot (the knit is shader-side, not seen in Workbench); a flat
  facet at the toe tip where the toe closure links.
- `boots_hero_boots_feet_pair.png` (hero camera, the pose agent's in-progress pose): the left boot stands where
  the drawn one does, laces centred; the right boot's toe still reaches past the drawn toe (real length) and reads
  as a flat wedge where the drawn toe is a high rounded cap.

## 8. Still wrong, ranked for round 4

1. **The toe box**: low and flat behind a vertical bumper wall; the drawn boots have a high, rounded, scuffed toe
   cap with the bumper wrapping it. The last's toe box is take 1's stretched sock (flat-topped, square-cornered):
   give the last a real toe-box section (the Zephyr's internal 73 x 27 at the hallux, spec 02 §3.1) and lay the
   bumper on the toe's curve. The nose rounding also cuts the last's corner (6.6 mm).
2. **Still smooth beside the reference**: the folds exist but are faint at the hero distance; the drawing's
   creased, scuffed, panelled leather needs the wear masks (dust in creases, scuffs) and fewer, stronger folds;
   no welts (`gn_stitches.welt`), no collar binding row, no pull loop yet.
3. **The collar** is a uniform roll on the rim; the drawn one is a soft padded slump under the hems.
4. **Outsole 310 x 141**: 5 mm over spec 02's 305 (the end allowances that let heel and nose round); the width
   follows this broad last. Round the ends without adding length.
5. **E1 at h 91** against the drawn 80 (the real instep); the drawn lacing starts lower on the vamp.
6. **Hooks** at h 198 / 176 (spec 206 / 189, H1-H2 17.5 apart); the pitch is even; the knot is a plain torus.
7. **Toes in the sole**: the rest foot's flat toes pass through the sprung sole top (hidden); the pose should
   extend the toes 12 degrees (a pose item), then that clash goes.
8. **Footbed consistency**: the 2.1 mm of sock in the footbed and the -1.7 mm posed sink (above).

### Round 3 in the assembly (2026-11-15, `renders/round_03/`)

Built in the pipeline (base.blend now carries the foot: body.md §6; the pose re-applied, not re-solved; the toes
turned up 12 degrees by pose.py). Two faults only the assembly showed, fixed in boots.py:
- **The buckles lay on the floor between the feet**: the ladder-lock had an object transform, and
  `common.load_part` reads `matrix_world` from the freshly loaded cache before any depsgraph update (it reads
  identity). boots.py now bakes every object's transform into its mesh before binding (`bake_transform`). Any part
  with transformed objects would hit the same `load_part` limitation.
- **Stitches stayed at rest** (threads drawn from the posed boot back to its rest place): `common.bind`'s weight
  transfer gives edge-only meshes (the stitch carriers) no weights. boots.py now copies the upper's nearest
  vertex's weights onto unweighted vertices (`fill_unweighted`; 1338 / 1362 stitch and 156 / 160 tack vertices).
  Other parts' stitch carriers (if any) would need the same.

Clashes (`clashes.md`): body in the boot soles 113 vertices, max 6.7 mm (designed: the footbed stands 4 mm below
the stripe top that closes the sole solid, plus the 2.1 mm sock, the heel pad); the socks in the skin 2231
vertices, max 3.0 at the ankle (linear skinning of a 0.3 mm garment over the flexed ankle; hidden). No boot part
clashes with the trousers or another part. Posed lugs sink 1.6 / 1.8 mm (the new feet's landmarks sit 0.3-1.9 mm
under the seats until the next pose solve).

Renders looked at: `boots_feet_compare.png` (the left boot stands on the drawn one, laces centred, stitch rows
visible; the right boot's toe a flat wedge past the drawn toe; the cuff straps under the trouser hems, as drawn),
`soldier_full_compare.png`, `legs_knees_compare.png`, `turnaround.png` (the boots sit under the stacked hems from
every side; no stray geometry).

## 9. Round 5 (2026-11-15): materials checked in the hero frame

The boots keep take 1's twelve recipes (`apply_library`); the round checked them in the hero frame's Cycles
render against the reference's median over the boots' mask. `Leather.Boot.FullGrain` (in the catalogue, so
`boots.py` is unchanged): albedo #2d2b29 -> #353433 (the boots rendered 1.35 x too dark), roughness 0.50 -> 0.55
(the satin highlight read brighter than the drawn one: p90 ratio 0.73); dust stays 1.0 on preset `boot.toe` with
the left boot the dustier. `Cordura.500D.Black`'s dust gained the up-band keys (None here: unchanged).
Now at a median ratio of 1.09 and p90 0.63.

Renders opened: `renders/round_05/boots_feet_compare.png`, `soldier_full_compare.png`.

Still wrong (materials): the drawn boots are scuffed and creased all over, grey with dust in the creases and on the
toe caps and dull; ours read as a smooth, even satin with dust on the toe only. The crease field and polish zones
the leather recipe reads (`crease`, `polish`) are missing on this build (spec 02 §5), so the scuff, crease and
polish layers are off; the specular highlight stays brighter than the drawing's.

## 10. Round 6 (2026-11-15): the "galosh" (critic m3)

All three critics: the right boot is a seamless galosh with a hard collar seam and no laces down the vamp, next
to a properly laced left boot.

**Not a bug of mirroring, cache, binding or material.** Both boots come from the same code with their own seeds;
the left boot seen from the lateral side (`renders/boots/boots_closeup_L_lateral.png`, round 3, and the round-5
turnaround's threeq_L) is the same galosh. The right boot is simply the one the hero camera sees in profile, the left
one from the front, where the lacing dominates. In profile three things read as an overshoe:
1. **The lacing stopped 150 mm behind the toe.** E1 was meant to sit at h 86, but the throat's centre line ended
   at h ~93 (its casts from the ankle point toward targets on the forefoot dipped out of the vamp short of them),
   so `Throat` capped E1 at the line's end minus 20 mm: h 93, about 90 mm of bare vamp ahead of it.
2. **The leather/Cordura edge was a level line at h 98** all round: the critics' "hard collar seam".
3. **The toe cap stood 0.8 mm proud**, invisible in profile, and there was no panel line between it and the counter.

**Changed** (geometry only; the leather/Cordura face split follows the new quarter edge, the recipes are untouched):
- The throat line runs on to the ball + 45 mm, cast also straight up from inside the last's bottom under each
  target (the nearer hit wins), and E1_H is 79: E1 now at h 79, s 202 (about 125 mm behind the toe tip; drawn
  ~137), seven rows at h 199, 172, 146, 121, 104, 92, 79 (pitch 26.7 mm, was 22).
- `quarter_h()`: the quarter's top edge h 98 behind, rising 14 mm over 60 mm toward the throat.
- `mud_h()`: a leather mudguard 1.0 mm proud, its top edge h 92 at the heel falling to h 45 at the ball, with a
  double stitch row along it (`mudguard_lat/med_mm` about 95 / 120 mm a side).
- The toe cap 1.6 mm proud (TOECAP_LIFT).

**Renders opened** (renders/round_06/): `boots_feet_compare` (three builds), `soldier_full_compare`, `turnaround`.
The right boot in profile now shows lacing down the vamp to about mid-foot, the diagonal mudguard seam from the heel
toward the ball and a visible toe-cap step; the left boot from the front laces lower on the vamp. **It still reads
more like a sneaker than the drawn boot**: the toe box is long, low and smooth behind a thick slab rand, where the
drawing has a high, rounded, scuffed toe cap with a wrapped bumper and a chunky stepped sole. That is section 8 item 1
(the last's toe box), not touched this round.

Stand-off check: the boots' tongues and lugs are listed as designed gaps; nothing flagged. Clashes: body in the boot
soles 148 vertices, 10.4 mm (the designed footbed and sock, as rounds 3-5).

**Still wrong, for round 7**: section 8 items 1-8 stand, with item 5 (E1) done. First the toe box (a real toe-box
section on the last, the bumper on the toe's curve), then the outsole's slab rand (a stepped, chunkier midsole and lug
wall).

## 11. Round 9 (2026-11-15): away from the sneaker (critics r8 m4, all three)

All three critics: smooth wrapped uppers, thin wedge soles, no toe cap, laces only at the ankle; a Zephyr-class boot
laces from the toe box, has a defined toe cap, a deep lugged sole with a heel breast and a high rounded toe. Round 8's
own list (§8 items 1, 2, 5) said the same. Constants only, in `boots.py` (the last, the sock and the upper's method are
unchanged):
- **Toe box** (`NOSE_H, NOSE_EXP, NOSE_PLAN`, `TOE_PUFF`): the nose section keeps 24 mm of height at the very tip (was 12)
  and rounds as e^0.42 in profile (0.5) and e^0.50 in plan (0.6) over a 40 mm nose (44); the toe box is raised 6 mm
  ahead of the ball (ramped from the ball + 5 to + 45). Top of the upper (rest z) at s 240 / 260 / 280: 47 / 51 / 56
  (round 8: 45 / 46 / 49).
- **Rand and bumper** (`RAND`): side 13, heel 16, toe 26 (10 / 12 / 20), 3.2 proud (2.5) with a 1.4 lip (0.7). A first
  try at toe 32 folded the bumper's top rows into a black visor over the nose (`boots_closeup_L_lateral`, first build).
- **Outsole** (`CUP`, `TOOTH_WRAP`, `TOOTH_PROUD`, `ARCH_H`): the cup wall 9 mm (6); the perimeter teeth wrap 8 mm up the
  sidewall (3), stand 2.6 proud (1.4), 12 / 19 long (11 / 18), drafted 1.2; the waist recessed 6 mm between the heel block
  (s < 68) and the forefoot (from the ball - 52), so the heel breast shows (`FootFrame.arch()`; no teeth in the recess).
  Lug depth is still the real 5 mm under the forefoot.
- **Lacing lower** (`E1_H` 79 -> 72, the throat line to the ball + 50, was + 45): E1 at h 72.0 / 71.9. A first try at
  h 64 with the line to the ball + 62 ran the stays and laces off the nose (the line passes the toe box's crown there).
- Measured (`boots.json`): outsole 310.0 x 146.7 max, 135.0 at the ball (L; R 140.9 / 130.8): wider than round 8's
  141 / 133 by the prouder rand and teeth (real ~116-125; see below).

**Renders opened**: `renders/boots/boots_closeup_L_lateral.png` and `_R_front34.png` (two builds), the hero
`boots_feet` crop in Cycles from an in-memory assembly (not a round; scratch). What they show, honestly: from the side
the boot now has a chunky sole with a lug wall, a heel block and a visible arch recess, and a taller rubber toe; the toe
box is higher and blunter. From the front the toe reads as a wide square rubber cap, boxier than the drawn rounded one,
and the vamp is still one smooth leather surface with the round-6 mudguard line: in the hero frame the right boot
(profile) reads more like a boot than in round 8, but still smooth and plain beside the drawn creased, panelled one.

Clashes (in-memory assembly with the other agent's round-9 clothing): body in the boot soles 125 vertices, 7.5 mm
(round 8: 152, 10.4; designed); socks in the skin as before. New: the trousers' hems 12-14 mm into the boot tongues and
uppers (trousers in boots: the round-9 hems, not a boot change; the tongue tops stand 10 mm above the rim as since round 2).

### Still wrong, for round 10
1. The toe reads boxy and square from the front (the bumper is a slab on a flat-topped toe box): round the toe box's
   crown across (the last's square toe-box corners, §8 item 1) and give the bumper a curved top edge.
2. Width: 141-147 mm max with the prouder rand and teeth; real ~116-125. Thin `SIDEWALL` / `TOOTH_PROUD` at the ball.
3. The upper is still smooth: no quarter/vamp overlay seams that read at hero scale, no scuffs or crease field.
4. Lacing still starts at h 72, about 110 mm behind the toe; the throat line cannot go further without leaving the vamp.

## 12. Round 10 (2026-11-15): a Zephyr-class upper (critics r9 m1, all three; G1 D9, D10)

All three critics: the right boot (seen in profile) reads as a galosh: a smooth moulded lower, a long flat wedge toe, a
squared bumper, laces that stop at the instep. G1: a stretched wedge toe with a straight front bumper (right), a squared flat
bumper and a slab sole front (left). The brief: eyelets down toward the toe, a rounded protective toe cap with a rubber rand,
stitched suede and textile panels over the vamp and quarters with visible seams, a flex crease across the vamp, a sole
116-125 wide, both boots made the same way (they are: one code path, two seeds).

**The width, and round 9's figure.** `outsole_width_max_mm` (141-147 in round 9) was the outline's whole extent across the
foot frame's axis, which the sole's own slant (a few degrees off the heel-toe landmark line) inflates by 15-20 mm; the new
`outsole_section_width_max_mm` is the widest 10 mm station across the foot (the old key is kept for comparison). The real
excess came from the last: take 1's last grown 3.5 mm reached 128.6 across the forefoot. Now no station of the upper is
wider than `UPPER_W_MAX` 119 mm (113 was tried: it cut into the 5th metatarsal head), `SIDEWALL` 3 -> 1.5, `TOOTH_PROUD`
2.6 -> 1.4, the rand 3.2 -> 2.0 proud. Widest sole section now 123.5 (L) / 123.2 (R), 123.5 / 122.6 at the ball, length 307
(round 9 not measured this way; from its 128.6 last and 3 mm sidewalls about 137). The old key reads 137.0 / 130.1.

**The toe (D9, D10).** Take 1's last has a stretched-sock toe box, square in plan and flat-topped; the nose kept its corners.
Now the nose's sections may lie up to `NOSE_RELAX` 16 mm (times their share of the nose) inside that last, over a longer,
rounder nose (`NOSE` 40 -> 52, `NOSE_PLAN` 0.5 -> 0.8), and the forefoot's sections round over to the crown above 40 % of
their height (`TOE_ROUND`, an elliptical shoulder, up to `TOE_RELAX` 12 mm inside the last's corners): the toe is round in
plan and domed across. **The rubber toe cap** is now an overlay moulded on the toe box (`RUBBER_TOE`: 60 mm back from the tip,
its top edge 30 mm over the stripe at the tip curving down into the rand along the sides, 1.8 mm proud, `Rubber.Rand.Black`
on face index 3), and the rand is a low strip (toe 26 -> 14 mm, `toe_exp` 4: it wraps the toe's front and sides). Round 9's
26 mm rand wall with a lip was the "squared bumper".

**The panels (m1).** `vamp_s()`: a suede vamp ahead of a seam slanting back from the mudguard behind the ball (s_ball - 12 at
h 50) up to the stays; Cordura quarter panels behind it down to the mudguard (round 9: smooth leather all round below h 98);
the mudguard suede; the toe cap and counter smooth leather (the drawing's highlights, Q14). Suede is `Boot.Mat.Leather.Suede`
(Leather.Boot.FullGrain made matte: #4a4642, roughness 0.90, the grain flattened, no polish, dust 1.4). The overlays step
0.8-1.0 mm over the textile; a double stitch row runs along the vamp seam (26-30 mm a side; the rest of the seam lies under
the stays). The vamp's dominant flex folds are deeper (2.6-3.6 mm, was 1.5-2.4), with fewer fine wrinkles.

**Lacing.** E1 sits where the throat comes down to `E1_H` 62 or forward to s_ball + `E1_DS` 12, whichever is first (the raised,
rounded toe box keeps the crown above h 70 ahead of the ball, so a height alone ran E1 onto the nose, first try); the line runs
to s_ball + 62. E1 at s 235, h 71-72 (round 9: s 218, h 72), about 64 mm behind the toe tip; rows at s 124-235.

**The sock.** The narrower upper came close enough to the forefoot that the sock (its Solidify grows outward 2.2-3.0 mm) poked
through as a lump at the 5th metatarsal head; the upper now clears the skin by `SOCK_CLEAR` 4.2 mm (281 / 267 vertices moved),
the moved patch Taubin-smoothed over 4 rings and pushed again. A small dot remains on the left boot's lateral forefoot.

**Numbers, final build** (`cache/parts/boots.json`; clashes from a scratch in-memory assembly of the final caches, not a
round; round 9 in brackets): outsole section 123.5 / 123.2 mm (about 137); E1 h 71.3 / 72.2 at s 235 (h 72 at s 218); posed
lug bottoms -1.3 / -1.4 mm. Body in the boot soles 81 vertices, 6.6 mm (125, 7.5; designed: the footbed and the sock); socks
in the skin 2175, 3.0 (as before, designed); trousers in the boots 112, 14.1 (113, 14.1: the round-9 hems in the tongues, a
trousers item); nothing else. Whole boots mask (`look_stats.py`, graded, `renders/look/r10_base` -> `r10_final`): median ratio
1.76 -> 1.52 (render #181819 -> #1a1a1a against #222220), b/g 1.06 -> 1.00 against 0.90.

**Renders opened**: clay zooms in the hero pose from scratch in-memory assemblies (`zoom_bootR_side`, `zoom_bootL_front`,
`zoom_bootL_lat`, `zoom_bootL_top` for each build), and the graded Cycles `sheet_boots_feet` of `renders/look/r10_base`,
`r10_d1`, `r10_final`. What they show: in clay the toe is round in plan and domed, lower, with a moulded rubber cap whose top
edge arcs down into a low rand; the vamp carries the suede panel step, the mudguard line and deeper flex folds; the lacing
runs onto the forefoot; the sole is narrower. In Cycles at hero scale the right boot's toe reads shorter and rounder, but the
panels and seams barely separate in value: the boot still reads smoother than the drawn one.

### Still wrong, for round 11
1. At hero scale the panels hardly read: suede, textile and leather are all near-black under this light; the drawn boot's
   structure comes from dust in the creases, scuffs and highlights on creased leather. Next: the dust and crease wear masks
   (spec 02 §5, `crease` / `polish` are written but faint), stronger seam shading.
2. The boots are still darker than drawn (ratio 1.52) and slightly cool (b/g 1.00 against 0.90).
3. The vamp seam's stitch rows are short (22-30 mm a side): the seam's upper half lies under the stays.
4. A small dot remains on the left boot's lateral forefoot (where the sock clearance was smoothed).
5. The tongue tops stand 10 mm above the rim and the trousers' hems pass 14 mm into them (round 9's item; the hems').
