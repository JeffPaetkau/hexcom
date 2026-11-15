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
