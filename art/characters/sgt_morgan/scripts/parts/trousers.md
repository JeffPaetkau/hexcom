# Trousers

Build: `"$SGT_BLENDER" -b --python scripts/parts/trousers.py [-- --no-render]` (about 8 s with renders). Output:
`cache/parts/trousers.blend` (collection `Part.Trousers`), `cache/parts/trousers.json` (measurements, clearance),
`renders/trousers/*.png`. Shared helpers: `scripts/parts/common.py`.

## 1. What it is

**Identity:** Crye Precision G3 class combat trousers (CLAUDE.md rule 1). The construction is:
- NYCO 50/50 ripstop shell;
- black 500D Cordura knee-pad pockets holding an AirFlex class pad;
- bellows thigh cargo pockets;
- slim calf pockets;
- a two-ply waistband;
- a plain hem stacked over the boots.

Sources: take 1 `archive/v1/spec/09_combat_trousers.md` §2 to §3 (Crye G3/G4 product descriptions; size 34R pattern estimates marked E there).

| Quantity | Real / source (mm) | Built, rest (mm) |
|---|---|---|
| Waist top | front about 63 above the hip joints (spec 09 §2.1, re-based on this body) | plane: 1052 front, 1087 back (`waist_top_z` 1085) |
| Waistband | 45 tall, two-ply | 45 band standing 3 proud |
| Thigh girth (garment) | about 600 to 650 for size 34 (spec 09 §3.3: 600 + ease) | 634 at z 820 (body thigh 546) |
| Knee girth incl. pocket | about 500 | 494 at the knee joint less 8 |
| Calf girth | about 480 | 515 at z 420 |
| Leg opening at the stack | 460 (spec 09 §3.3) | 442 to 449 at z 200 (rest), round the boot shaft |
| Knee pocket | 175 x 225, pad inside about 16 thick | 176 x 224 sheet, 17 proud |
| Thigh cargo | 200 x 190 x 25 bellows, 70 flap | 200 x 190, 18 proud, flap 208 x 66 (22 proud) |
| Calf pocket | 85 x 145 x 15, 45 flap | 84 x 144, 10 proud, flap 90 x 44 |
| Hem edge | 10 to 25 below the boot collar top (spec 09 §2.1) | rest z 152 = 188 above the floor in the pose (rim 212) |
| Hem stack | three rolls, crests at h 293 / 254 / 212, 8 to 17 proud | three rolls of 8 / 12 / 13 at rest z 257 / 218 / 184, over the shaft ellipse + 8 |

## 2. What the reference shows

Evidence: `ref/crop_legs_knees.png`, `ref/zoom_trousers_*`, spec 09 §2.
- Near-black camouflage: median lit colour #272422 to #3e3c38.
- Black knee pockets: #252527.
- Pads in the pockets, with external caps (the caps belong to the armour part).
- Baggy legs with drape folds.
- A seam band above each knee pocket.
- The left calf pocket is visible.
- Three hem rolls stacked on each boot collar.
- The thigh straps of the leg rigs (the belt part) cover the lateral thighs.

## 3. Departures and why

- **Thighs:** they follow the body's ANSUR-length thighs, not the drawn short ones (CLAUDE.md, reality wins). The knee pockets therefore sit about 3 to 5 cm higher than drawn in the hero overlay. This is accepted.
- **Cargo pockets:** built under where the rigs will go. The drawing shows none, but a G3 has them.
- **No camouflage:** flat colours only in round 1. Shell #2a2723, knee pocket #232325 (lit samples used as albedo).
- **No gusset, seams, belt loops, fly or drawcord:** these are detail rounds.

## 4. Round 1 (2026-11-14)

**Method.**
1. The rest skin from just above the ankles to above the hips is copied. Arms and head are excluded by bone weight, and the region is refined once and snapped back to the skin.
2. Each vertex is pushed out along its normal by an ease field: 9 mm at the waist, 14 at the seat, 16 at the crotch, 19 to 21 at the thigh and knee, 24 at the shin, plus 3 mm for the waistband.
3. The push is capped where the skin faces itself (`common.limit_by_gap`, the crotch).
4. Below the crotch, each leg's sections move 85 % of the way to their convex hull (`common.convexify_along`). The cloth spans the hollows, so the legs hang instead of showing the muscles.
5. The lower legs are widened radially to the boot's shaft ellipse (`common.BOOT`, 138 x 106 at the rim), plus 8 mm, plus the three hem rolls.
6. The shell is cut at the waist plane and the hem plane, Taubin-smoothed, and pushed out to at least 4 mm (7 mm above z 940, which leaves room for the tucked shirt).
7. The pockets are separate sheets laid on the shell (`common.surface_patch`: rays from the leg axis, flat-topped pillow profile). This gives them clean outlines.

**Thickness and rigging.**
- Solidify 1.5 mm inward on the shell and 1.2 mm on the pockets; Subdivision 1.
- All parts take weights by Data Transfer from Body.Mesh (nearest face interpolated) and have an Armature modifier on Morgan.Rig.
- Objects: `Trousers.Shell` and `Trousers.{L,R}.Pocket.{Knee,Cargo,CargoFlap,Calf,CalfFlap}`.

**Clearance from the skin (`trousers.json`).**
- Rest: minimum 2.4 mm, 0 vertices inside.
- Hero pose: minimum 1.9 mm, 0 inside.

**Layering in the pose (`renders/round_01/clothing_hero.json`).**
- Boot shaft tops are inside the hems on both sides (0 of 447 and 0 of 450 uncovered).
- The shirt tail is inside the waist except 19 of 822 vertices at the back (see §5).

**Renders looked at.**
- `trousers_rest_front`, `_side`, `_threequarter`: these read as combat trousers. Baggy straight legs, boxy cargo pockets with flaps, domed knee pockets, calf pockets, a waistband, and hems wide enough for a boot.
- `trousers_hero_legs_knees_pair`: knee pockets in the drawn places, a little high (thigh length, above). The lower legs are slimmer than drawn.
- `trousers_hero_soldier_full_pair` and `renders/round_01/clothing_hero_boots_feet.png`: the hems sit over the boot shafts.

## 5. Still wrong, ranked for round 2

1. **Lower legs are too slim and too clean.** The drawing's shins are baggier, and the hem stack is a real bunched pile down onto the laces. Ours shows almost no rolls, because the stack bulges are 8 to 13 mm on an already wide hem. This needs real stacking: cloth simulation, or sculpted roll rings that follow the boot.
2. **No drape folds.** The shell is smooth. Thigh and knee folds, the seam band above each knee pocket, and the crotch pleats need cloth simulation on the GPU machine or displacement.
3. **Lower back in the pose.** The shirt tail pokes through the trouser waist at 19 vertices behind the right hip (posed y +170 to +186, z 960 to 1005). Linear skinning pinches the outer layer as the spine extends. It is hidden from the hero camera, and the belt and carrier will cover it. Fix with more ease at the back of the waist, or smoothed weights for the outer layer.
4. **Back of the boot collars.** 144 of 504 outward-facing vertices on each collar roll are not under the hem. They are at the back and medial side of the roll's top. The hem's lower edge rides about level with the roll there; it is not visible from the front.
5. **Waistband:** a plain offset ring that stands off the hip bones (the belt hides it). It has no belt loops or fly.
6. **No camouflage, ripstop or Cordura materials:** the materials round.
7. **Pockets are pillows.** They lack the bellows' side gussets, flap overhang, hook-and-loop strips and the knee pocket's top opening.
