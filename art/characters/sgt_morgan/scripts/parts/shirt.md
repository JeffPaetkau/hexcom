# Shirt (combat shirt and neck gaiter)

Build: `"$SGT_BLENDER" -b --python scripts/parts/shirt.py [-- --no-render]` (about 12 s with renders). Output:
`cache/parts/shirt.blend` (collection `Part.Shirt`: `Shirt.Shell`, `Shirt.Gaiter`), `cache/parts/shirt.json`,
`renders/shirt/*.png`.

## 1. What it is

**Shirt:** a Crye Precision G3 class combat shirt. Its construction is:
- an FR knit torso, worn tucked under the trousers and carrier;
- NYCO ripstop sleeves;
- a zipped mandarin collar;
- elbow-pad pockets;
- hook-and-loop cuffs.

**Gaiter:** a polyester fleece neck gaiter, about 280 mm long, 460 mm round and 3 mm thick. Pushed down, it buckles into three rolls. A thin 530 mm microfibre tube was rejected (take 1 D3).

Sources: take 1 `archive/v1/spec/10_combat_shirt_gaiter.md` §2 to §3 (G3 product description, ANSUR sleeve length; gaiter class and the buckling wavelength argument).

| Quantity | Real / source (mm) | Built, rest (mm) |
|---|---|---|
| Torso ease | snug knit, chest +40 | 5 mm offset (3.5 mm where it is tucked, below z 1060) |
| Chest girth (garment) | body + about 40 | 1059 (convex hull at z 1360; body chest 993) |
| Sleeve ease | rib or ripstop upper arm 390 vs body 345 (about +7 offset); elbow 360; forearm 350 | 10 at the shoulder, 14 upper arm, 18 at the elbow, 16 forearm, 11 then 5.5 over the last 40 mm |
| Cuff | 215, closing to 200, ending inside the glove gauntlet | cut 8 mm past the wrist joint, 5 to 5.5 mm offset, inside the glove cuff (0 and 1 vertex uncovered in the pose) |
| Hem | tucked, at about h 850 | cut at z 930, inside the trousers |
| Collar | mandarin, 55 tall | the shell runs up the neck to a plane at 1542 front and about 1600 back (under the gaiter) |
| Gaiter | 280 x 460 tube, 3 thick; stack about 82 to 92 tall; roll 1 about 42 tall and 22 proud, roll 2 28 / 16, roll 3 20 / 12 | seat 10 mm (front) to 40 mm (back) up the neck axis, top 110 to 150 (saddle); rolls 27 / 19 / 13 proud; wall 3; spans z 1493 to 1647, 210 wide |

## 2. What the reference shows

Evidence: `ref/crop_torso_vest.png`, `ref/crop_arm_*`, `ref/zoom_shirt_*`, `ref/zoom_gaiter_rolls_x8.png`, spec 10 §2.
- A dark shirt, about #332f2d (the left sleeve median, cool-lit).
- The torso is almost entirely under the carrier.
- The sleeves show between the pauldrons and forearm guards, and fold at the elbows.
- A bulky dark brown gaiter, #373029, rolled in three lobes under the jaw, with its top edge higher at the back.

## 3. Departures and why

- **Rib-knit shoulder panels:** none yet. Take 1 kept them as "image wins, plausible"; they are a detail round.
- **Bicep pockets:** omitted (take 1 D6). Elbow-pad pockets are not modelled; the armour part's elbow caps sit outside.
- **Collar zip and placket:** not built; hidden by the gaiter and carrier.
- **Colours:** flat. Shirt #2c2927, gaiter #383029.

## 4. Round 1 (2026-11-14)

### Shell
1. Torso, neck and arm skin is copied (legs below the hem, head and hands excluded by bone weight), and refined.
2. Each vertex is pushed out by an ease field. The torso and sleeve eases are blended by each vertex's arm-bone weight, so the shoulder joins smoothly. Sleeve ease follows an arm parameter: 0 at the shoulder joint, 1 at the elbow, 2 at the wrist.
3. The push is capped across the armpits.
4. The upper arm and forearm sections move 85 % of the way to their convex hull.
5. The shell is cut at the collar line, the hem and both wrists, reduced to its largest connected piece, smoothed, and pushed out to at least 3 mm.

### Gaiter
1. Rings round a neck axis run from (0, 12, 1488) to the neck03 joint, from a seat ring to a saddle-shaped top.
2. Each point is a ray to the skin, plus 11 mm (shirt collar and air), plus the three rolls' cos² lobes, plus a 2 mm band at the bottom.
3. The rings are Taubin-smoothed and pushed out to 10 mm from the skin.

### Thickness and rigging
- Solidify 1.2 mm (shirt) and 3 mm (gaiter, non-even offset); Subdivision 1.
- Weights by Data Transfer from Body.Mesh; Armature modifier on Morgan.Rig.

### Clearance from the skin
- Rest: shell minimum 1.5 mm, gaiter 10 mm, 0 inside.
- Hero pose: gaiter 8.9 mm and 0 inside. The shell has 71 vertices inside, to -15.7 mm, all at the back of the right elbow (see §5).

### Layering in the pose
- Sleeve ends inside the glove cuffs: 0 of 330 (left) and 1 of 322 (right) uncovered.
- Collar under the gaiter: 13 of 287 uncovered, at the back of the neck.
- Shirt tail under the trousers: 19 of 822 uncovered, at the lower back.

### Renders looked at
- `shirt_rest_front`, `_side`, `_threequarter`: a snug long-sleeved shirt with roomier sleeves narrowing to the cuffs, and the gaiter in three rolls.
- `shirt_hero_torso_vest_pair`: the gaiter sits where the drawn one does but is smaller and lower. The torso is right for something the carrier will cover; the knit shows the pectorals through, which the carrier hides.
- `shirt_hero_arm_R_pair` and `shirt_hero_arm_L_pair`: the sleeves follow the drawn arms. They are a little slimmer than the drawn sleeves, which also carry the pauldron and guard bulk.
- `shirt_hero_soldier_full_pair`.

Earlier failures, now fixed:
- The gaiter's Solidify exploded until its rings were smoothed and the offset made non-even.
- The first sleeves were too slim.
- The first gaiter was too small.

## 5. Still wrong, ranked for round 2

1. **The gaiter is still smaller than drawn** (210 wide against the drawing's about 233), and its rolls are too regular. Its lower front edge is ragged where the seat ring meets the chest. It needs the saddle tilt of the crevices (15°), the left pleat, and a sculpted or simulated buckle pattern.
2. **Right elbow in the pose:** 71 shell vertices are inside the arm at the back of the 107° right elbow (posed x -385, y +97, z 1279). The skin there stretches beyond the 18 mm ease under linear skinning. It is not visible from the hero camera; the elbow points back and the forearm guard covers the area. Fix with a corrective shape or more ease at the olecranon, or let the armour part's elbow cap cover it.
3. **No folds:** the elbow bunching, the drape under the pauldrons and the blousing above the waistband all need cloth simulation or displacement.
4. **No rib shoulder panels, back seam, cuff tab or collar.**
5. **Shirt tail at the lower back** and **collar back under the gaiter:** small layering misses behind the figure (§4).
6. **No knit, ripstop or fleece materials.**
