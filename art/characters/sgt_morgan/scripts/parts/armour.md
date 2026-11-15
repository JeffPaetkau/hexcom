# Armour

Build: `"$SGT_BLENDER" -b --python scripts/parts/armour.py [-- --no-render]` (about 30 s). Output:
`cache/parts/armour.blend` (collection `Part.Armour`), `cache/parts/armour.json`, `renders/armour/*.png`,
`renders/armour/armour_check.json`.

## 1. What it is (real identity and dimensions)

No issued military pauldron exists; the classes follow take 1's spec 12 §3.1.

| Piece | Built (mm) | Class / source |
|---|---|---|
| Pauldron tier 1, cap | 125 wide at the top, 100 at the lip, lower corners chamfered 25; spans 98 deg about its centre direction at a mean radius of 83 from the shoulder joint; wall 3; inner face 12 over the shirt | sport shoulder cup (motocross / lacrosse class), spec 12 §3.2 |
| Tier 2, mid plate | 115 arc x 89 tall (s 88-177 below the joint), wall 3, 6 over the shirt | spec 12 §3.2 (80 tall, arc 100; lengthened to close the gap under the cap) |
| Tier 3, bicep band | 200 deg x 48 tall (s 190-238), wall 2.5; black elastic closing the medial 160 deg | spec 12 §3.2 (s 214-262 raised 24 so it clears the forearm guard at 102 deg elbow flexion) |
| Emblem (left) | shield 50 x 95, 1 mm plate 1.5 proud of the cap | drawn; US practice: unit insignia on the left |
| IR strobe (left) | 30 x 45 x 18 on tier 2's rear edge | Adventure Lights VIP class |
| Forearm guard | neoprene sleeve 3 mm, d 27-255 from the elbow; elbow band d 32-66 (180 deg), main plate d 62-224 (200 deg), wrist band d 220-252 (230 deg); walls 2.5-3; 4 mm foam | Hatch Centurion class riot guard, 220-260 long (spec 12 §3.3) |
| Elbow cap | fin 14 x 40 x 5 on the lateral epicondyle, pad 30 x 28 x 6 just below | drawn (spec 12 D6: no real product this small) |
| Knee pad | octagonal cap 160 x 190, 3.5 wall, 8 mm dome, on a 4 mm neoprene base 12 larger all round, 38 mm strap round the back of the knee | Alta AltaFlex / Crye AirFlex class (Alta 229 x 165 x 38) |

## 2. What the reference shows (crop_arm_*, zoom_armour_*, crop_legs_knees)

Worn tan-grey moulded shells (the left side reads blue-grey under the cool light: one colour, spec 12 D1). The
cap is a bent plate over the front of the shoulder with the shield emblem; below it a plate with the strobe at
its rear edge; a tan band above the elbow; a small fin on the left elbow; segmented forearm guards from elbow to
glove cuff; external hexagonal knee caps on black bases, strap and buckle on the medial side.

## 3. Departures and why

- Tier 2 is 9 mm longer and 15 mm wider and tier 3 sits 24 mm higher than spec 12, see the table.
- The forearm guard's elbow band is 180 deg, not 230: at the hero pose's 102 deg elbow it met tier 3.
- The knee base is soft (neoprene, bound by weights to follow the knee pocket); only the cap is rigid.
- The pauldron cap is turned toward the front of the shoulder (`CAP_FWD`), as drawn, rather than centred on
  the lateral deltoid.

## 4. Round 1 (2026-11-14)

- Every shell is a slab over a smooth radius field round a limb axis (`gear_common.LimbSurf`/`Field`): rays from
  the axis outward through the shirt and glove caches (walking through a garment's solidified thickness), the
  field smoothed and kept outside the raw surface. The cap is a gnomonic patch of rays from the shoulder joint.
  The knee pads use rays inward onto the trousers' knee pocket.
- Fitted to the shirt (sleeves) and glove caches and to the trousers cache with its knee pocket.
- Rigging, rigid pieces skinned 100 % to one bone (`gear_common.rigid_bind`): cap, emblem, tier 2 and strobe to
  `upperarm01`; tier 3 and its elastic to `upperarm02`; elbow band, main plate and foam to `lowerarm01`; wrist
  band to `lowerarm02` (so the pronation twist carries it); elbow fin to `upperarm02`, pad to `lowerarm01`; knee
  cap to `lowerleg01`. Soft (weights from the body): the guard sleeves, the knee bases and straps. The brief asked
  for bone parenting; single-bone skinning is the same motion, survives `common.save_part`/`load_part` (which
  only restores Armature modifiers and plain parents) and exports to glTF as skinning.
- Colours: shells #7b7064, knee cap #6a6158, black #1d1c1b, emblem #a9b3bd, strobe #9fb0bf.

Renders opened: `armour_rest_{front,side,threequarter}.png`, `armour_hero_arm_R_pair.png`,
`armour_hero_arm_L_pair.png`, `armour_hero_legs_knees_pair.png`, `renders/round_01/gear_hero*.png`.

Check (`armour_check.json`):
- rest: no overlap with body or clothing; gear/gear only at designed joints (cap lip over tier 2 66-68, tier 3
  band edge on its elastic 22, knee base under its strap 60, elbow pad on the sleeve 14-16, strobe on tier 2 20);
- posed: the right guard's sleeve and plates cross the shirt at the inner elbow (sleeve 558 shirt triangles, body
  96) because the elbow folds 102 deg; the carbine's stock crosses the right guard (sleeve 113, main plate 85) but
  reaches only 0.5-0.7 mm into it; the stock is 15 mm inside the right arm's skin itself (pose, not armour);
  main and wrist plates overlap 30-38 under pronation.

## 5. Still wrong, ranked for round 2

1. **The forearm guards are fat cones**: their radius follows the clothed forearm near the elbow, so the elbow
   end flares; the drawn guard is a straighter, segmented sleeve with a longitudinal rib and grooves.
2. **The pauldron cap is too small and too close in the hero frame**: the drawn cap stands out further and
   covers more of the shoulder top; tier 2 is a curved strip, not the drawn plate with a recess and vents.
3. **No details**: rim beads, rivets, slots, the knee caps' frame steps and slots, buckles, ladder-locks, the
   red tab, the X-star on the emblem.
4. **Knee pads sit higher than drawn**: the drawn thighs are short (CLAUDE.md, accepted), so the overlay misses.
5. **Right elbow fold**: soft sleeve and shirt cross at 102 deg; needs corrective weights or a split sleeve.

## 6. For integration

- The posed carbine stock lies 15 mm inside the right forearm's skin; the pose should move the stock out of the
  forearm (the guard needs another 12 mm over the skin).
- Rebuilt on the base of 18:25; the shirt, glove and trousers caches it fits are from 18:09. Rerun after them.
