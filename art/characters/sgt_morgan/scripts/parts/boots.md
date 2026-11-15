# Boots

Build: `"$SGT_BLENDER" -b --python scripts/parts/boots.py [-- --no-render]` (about 12 s with renders). Output:
`cache/parts/boots.blend` (collection `Part.Boots`), `cache/parts/boots.json`, `renders/boots/*.png`.

## 1. What it is

**Identity:** a LOWA Zephyr MK2 GTX Hi TF class tactical boot. Its construction is:
- 210 mm outside height;
- a leather and Cordura upper;
- a DuraPU double-density midsole on a rubber outsole;
- a padded collar and a gusseted tongue.

Sources: take 1 `archive/v1/spec/02_boots.md` §3, which cites LOWA's product pages (its S1 to S4) and a measured review (S4: stack heights, lug depth, drop).

| Quantity | Real / source (mm) | Built (mm) |
|---|---|---|
| Outsole length | 297 for this 274 mm foot (last 289 + toe 5 + heel 3) | 301 |
| Outsole width at the ball | about 116 | 116.6 |
| Heel seat (floor to footbed) | 36 (S4: 36.3) | 36 |
| Ball seat | 24 (S4: 23.7), so the drop is 12 | 24 |
| Visible stack (floor to rand top) | 49 at the heel, 23 at the ball | 49 / 23 / 21 at the toe |
| Toe spring | 15 | 15 (quadratic from the ball line) |
| Rim height above the floor | 212 at the sides (S1: 210 outside) | 212 (rim at rest z 176, sole at rest z -36) |
| Shaft outer section | 128 x 100 at h 110, 136 x 104 at h 158, 138 x 106 at the rim (measured on the drawing) | the same ellipses, centred on the leg's section at the rim |
| Padded collar | about 22 tall x 10 thick | 22 x 10 roll |
| Upper over the foot | leather 2.0 + lining 1.5 | 5 mm offset from the skin (with air); toe allowance +10 |

## 2. What the reference shows

Evidence: `ref/crop_boots_feet.png`, `ref/zoom_boots_*`, spec 02 §2.
- Black smooth leather with dust.
- A chunky lugged sole with a toe bumper.
- Five eyelets and two hooks with laces.
- A cuff strap with a buckle.
- A padded collar under the stacked trouser hems.
- The right boot points 85° to his right (seen in profile); the left points 17° to his left.

## 3. Departures and why

- **Not built:** laces, eyelets, hooks, the strap and buckle, lugs, the toe bumper and the panel seams. These are round 2 and later.
- **Lacing:** a 48 mm raised strip, 3.5 proud, stands in for the tongue and lace stays from the throat up the shaft front.
- **Sole:** a plain two-material slab, midsole #262626 over outsole #121212, with an outsole line at +8.
- **Colours:** flat. Leather #201e1c, collar #1b1b1c.

## 4. Round 1 (2026-11-14)

### Frame
The boot is built in the rest body's frame with the footbed under the rest foot. The sole plane runs through:
- z = -36 under the heel seat (30 mm ahead of the heel point);
- z = -24 under the ball (the mt1 and mt5 midpoint).

So in rest the soles hang 24 to 36 mm below the floor. Round 0's hero pose lifts each foot onto exactly these seats (`pose_solve.py`, `HEEL_SEAT, BALL_SEAT = 0.036, 0.024`).

### How the posed feet sit in the boots
Measured with `scripts/stages/pose.py apply_hero_pose(rig)` and `hero_pose.json` of 2026-11-14 17:47:
- Lowest sole point in the pose: L **-3.2 mm**, R **-2.9 mm**. The 2nd-percentile point (heel area) is -2.9 and -2.6 mm.
- The boots therefore stand on the floor, sunk 3 mm into it.
- The foot sits on its footbed, because the boot is rigged to the same foot it was built around.

### What round 0 or integration must change
1. **Nothing has to move for the boots to stand.** The pose already raises the feet by the footbed heights, so do not raise the body again: that would float the boots 33 to 36 mm.
2. **The 3 mm sink.** Either lower the solver's seats by 3 mm in its foot term, or raise the root by 3 mm.
3. **Rest pose.** If the rest pose ever has to show the boots on the floor (for example a glTF export in rest), raise Body and Rig by the heel seat (36 mm), or export the rest pose with that offset. Then re-solve the pose with the seats at zero.
4. **Stature.** CLAUDE.md's 1855 mm in boots assumes the footbed lift. The solver's pelvis height already includes it.

### Method, per side
1. The foot and ankle skin is copied, cut 50 mm above the rim (MPFB's shin faces are long, so it is cut rather than filtered), refined, and pushed out 5 mm.
2. The front is pushed 10 mm forward into a toe box. Each cross-section across the foot moves to its convex hull, which bridges the toes, and the forefoot is domed (+7 mm at the centre line).
3. The ankle and shaft are set to the measured shaft ellipses.
4. The shell is voxel-remeshed (4.5 mm, `common.voxel_remesh`) into a clean surface, opened above the rim again, Taubin-smoothed (60 iterations, boundary pinned), cut at the rim, and pushed out to 3.5 mm.
5. Everything below the sole top less 4 mm is clamped up, and the flattened floor faces are dropped; they sit inside the sole.

**Sole.** The upper's footprint near the sole top: the lateral and medial extremes per 5 mm station, smoothed, with half-ellipse toe and heel ends, grown 3 mm for the sidewall. It is extruded from the sole plane (with toe spring) up to the visible stack, and is rigid on `foot.{L,R}`.

**Collar.** The rim vertices are ordered by angle, resampled to 72 points, and a 10 x 22 elliptical roll is swept round them.

**Rigging.**
- The upper and collar take weights from the body, with the toes merged into the foot.
- The sole is weighted 1.0 to the foot bone.
- No Solidify on the upper: it is closed except at the rim, the collar covers that, and even-offset Solidify exploded on the toe box.

**Clearance from the skin.** Rest: upper 2.8 mm minimum, sole 6.7, collar 16.5, 0 inside. Hero pose: the same, 0 inside.

**Renders looked at.**
- `boots_rest_front`, `_side`, `_threequarter`: these read as a pair of high-top tactical boots. Chunky sole with heel drop and toe spring, domed toe box, upright shaft, padded collar.
- `boots_hero_boots_feet_pair`: both boots in the drawn places and headings, soles on the floor. Our right boot is a little longer in profile than the drawn one (real length).
- `renders/round_01/clothing_hero_boots_feet.png`: the trouser hems are over the shafts.

Earlier failures, now fixed:
- Solidify spikes from the flattened floor.
- A half collar, because the rim boundary was fragmented.
- The voxel step's filled top sagging into the shaft.
- A crumpled toe from the hull step.

## 5. Still wrong, ranked for round 2

1. **No laces, eyelets, hooks, tongue edges, strap or buckle.** These carry the boot's identity in the drawing. The take 1 materials library already has the boot recipes and a test boot with laces (`scripts/lib/materials.py` `test_boot`, `_laces_and_hardware`, `_strap_and_buckle`).
2. **The forefoot is still lumpy** where the toes were bridged, with a faint crease at the toe tip. The toe box should come from a last (a smooth parametric or scanned last; take 1 spec 02 §3.6 lists CC BY boot scans: Garmont T8, Danner TFX, a LOWA Tibet).
3. **The shaft is a plain upright cylinder.** It needs the real shaft's taper toward the ankle at the front, the heel counter's bell, ankle padding, and the forward lean that follows the shin.
4. **The sole is a smooth slab.** It needs lugs, the heel breast step, the toe bumper with its lip, and the rand.
5. **The 3 mm sink into the floor** in the pose (see §4).
6. **No leather, Cordura or rubber materials.** The take 1 recipes exist (`Leather.Boot.FullGrain` and others).
