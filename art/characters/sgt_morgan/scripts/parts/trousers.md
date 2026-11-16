# Trousers

Build: `"$SGT_BLENDER" -b --python scripts/parts/trousers.py [-- --no-render]` (about 25 s with renders on the
workstation). Output: `cache/parts/trousers.blend` (collection `Part.Trousers`), `cache/parts/trousers.json`
(measurements, clearance, seat standoff), `renders/trousers/*.png` (rest front, side, three-quarter, back,
hem side; the hero pairs). Shared helpers: `scripts/parts/common.py`. The belt and the armour's knee pads
fit to this cache and rebuild after it.

## 1. What it is

**Identity:** Crye Precision G3 class combat trousers (CLAUDE.md rule 1). The construction is:
- NYCO 50/50 ripstop shell;
- black 500D Cordura knee-pad pockets holding an AirFlex class pad;
- bellows thigh cargo pockets;
- slim calf pockets;
- a two-ply waistband;
- an articulated knee;
- a plain hem stacked over the boots.

Sources: take 1 `archive/v1/spec/09_combat_trousers.md` §2 to §3 (Crye G3/G4 product descriptions; size 34R
pattern estimates marked E there).

| Quantity | Real / source (mm) | Built, round 2, rest (mm) |
|---|---|---|
| Waist top | front about 63 above the hip joints (spec 09 §2.1, re-based on this body) | plane: 1052 front, 1087 back |
| Waistband | 45 tall, two-ply | 45 band standing 3 proud |
| Seat | room to sit and kneel: the cloth spans the cleft and falls past the gluteal fold | 29 to 30 mm off the skin straight behind at z 930, 41 at z 880 (round 1: ease 14 to 16, following the fold) |
| Thigh girth (garment) | about 600 to 650 for size 34 (spec 09 §3.3: 600 + ease) | 677 at z 820 (body thigh 546) |
| Knee girth incl. pocket | about 500 | 679 at the knee less 8, but this counts the back-of-knee folds and the perimeter round the pocket's edge; about 520 for the shell alone |
| Calf girth | about 480, hanging from the knee | 567 at z 420 (the drape from the knee) |
| Leg opening at the stack | 460 (spec 09 §3.3) | 609 round the middle roll (z 218), the edge at base + 14 |
| Knee pocket | 175 x 225, pad inside about 16 thick | 176 x 224 sheet, 17 proud |
| Thigh cargo | 200 x 190 x 25 bellows, 70 flap overhanging | 200 x 190, 22 proud, edge radius 7; flap 212 x 72, 27 proud, edge radius 4 |
| Calf pocket | 85 x 145 x 15, 45 flap | 84 x 144, 11 proud; flap 92 x 46, 14 proud |
| Hem edge | 10 to 25 below the boot collar top (spec 09 §2.1) | rest z 152 = 188 above the floor in the pose (rim 212) |
| Hem stack | three rolls, crests at h 293 / 254 / 212 | three rolls at rest z 257 / 218 / 184 (crests wander 9 + 4 mm round the leg), 13 / 17 / 19 proud (± 30 %) over the shaft ellipse + 8 |

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
- **No camouflage:** flat colours. Shell #2a2723, knee pocket #232325 (lit samples used as albedo).
- **No gusset, seams, belt loops, fly or drawcord:** these are detail rounds. A back seam to the crotch
  exists as the seat hull's ridge.
- **No cloth simulation:** the hang is procedural (§4), deterministic, from the rest body. A baked
  simulation is a later option (§5 item 2).

## 4. Round 2 (2026-11-14)

Round 1 (see git history for its notes): an offset shell from the skin with an ease field, the gap cap at
the crotch, each leg's sections moved 85 % of the way to their convex hull, the lower legs widened to the
boot shaft with three small rolls, pockets as sheets. From behind it read as leggings, and the lower legs
were slim, smooth tubes.

**What round 2 changed** (`trousers.py`; module doc for the order):
1. **Seat room.** 10 mm more ease at the back, from below the seat to the waistband. Above the crotch the
   back half of each section moves fully out to its convex hull, measured from the pelvis centre, so the
   cloth spans the gluteal cleft. A second hull pass, from the crotch up 40 mm, gives the back seam.
   - It is the back only: a whole-section hull also pushed the lower belly out.
   - The pelvis centre matters: the half-ring's own centre threw one vertex 29 mm inside the buttock.
2. **The drape envelope** (`drape()`), per leg, in cylindrical coordinates round the leg's bone chain, in
   10-degree by 6 mm bins:
   - Going down the leg, the radius may fall by no more than 0.24 per mm from the seat to the knee and 0.08
     below the knee. So the cloth falls from the buttock's crest past the gluteal fold, and from the knee
     past the calf.
   - Not on the inner thigh (58 degrees either side of medial, faded over 25), where the legs would meet.
   - The bins are smoothed round the leg before lookup.
   - The legs' sectional hulls now move fully (k 0.9) before the drape.
3. **Finer faces below the knee.** MPFB's shin faces are about 25 mm tall, too coarse for 10 mm rolls. The
   knee band and everything below z 360 are split twice (`subdivide_below`, carrying the ease column), then
   the whole shell is Taubin-smoothed (26 passes).
4. **Knee articulation** as radial reliefs added after the smoothing:
   - three soft folds behind the knee (1.8 mm, 24 mm pitch, only within 30 degrees of the back);
   - the seam band 118 mm above the knee joint across the front (1.8 mm ridge).
5. **The hem stack** after the smoothing. From 300 mm down, the radius is the boot shaft's ellipse + 8 mm
   plus three rolls. Each roll's crest wanders round the leg and its size varies about 30 %. Between rolls
   the cloth draws in to the ellipse + 6. Below the last roll the edge stays open on the boot (base + 14), so
   it does not gather like a jogger's cuff.
6. **Lower back.** The minimum clearance behind, above z 930, is 5 mm more (room for the tucked shirt tail).
   The shell's weights are Laplacian-smoothed over the shell above rest z 860 (`smooth_weights`, 14
   passes), so the outer layer follows the hips' mean motion instead of pinching where the spine extends.
7. **Pockets:** the bellows cargo is boxier (edge radius 7, 22 proud); its flap overhangs it (212 wide,
   27 proud, edge radius 4). The calf pocket and flap are sharper and deeper. The knee panel's pillow edge
   went from 34 to 26.

**Measured** (`trousers.json`):
- clearance from the skin: minimum 8.1 mm in rest, 9.0 posed, 0 vertices inside;
- seat standoff: as in §1.

**Integration** (`renders/round_02/`, built with the boots, the belt and the armour rebuilt after it):
- **No shirt–trousers clash.** Round 1's 12 vertices of trousers through the shirt at the lower back are
  gone, and the shirt tail stays inside.
- **No trousers–boots clash.** The hems cover the boot collars; the boots show from the hem down, as drawn.
- **Carrier front flap binding in the trouser waist: 278 vertices, 14 mm deep, at z 1074 to 1083 posed,
  front and right side.** This is new this round, and it is not caused by the trouser waist: it stayed after
  the belly was put back to round 1's fit. The carrier was rebuilt at the same time with its front bag
  lowered (round 1 integration, carrier item 2), and it fits to the shirt only (`assemble.py` DEPS: base,
  shirt). For the carrier owner: fit the flap's lower edge over the trousers' waistband, or add trousers to
  the carrier's fit.
- **The belt's rigs and holster against the cargo pockets: up to 3.4 mm both ways.** The cargo pockets grew
  4 mm and the flaps 5 mm; the belt rebuilt on them but its platform slab still dips into the pocket. Small.
- **Knee pocket into the knee pad base: 1.0 mm.** Small.

**Renders looked at.**
- `trousers_rest_back`, `_threequarter`:
  - The seat spans the cleft, with a back seam.
  - The backs of the thighs fall straight from the seat.
  - The lower legs hang wide from the knee into three soft rolls on the boot.
- `renders/round_02/legs_knees_overlay.png`: the lower legs' silhouettes lie on the drawn ones; round 1's
  were narrower.
- `boots_feet_compare.png`: the rolls stack above the boot collars, and the boots show below the hem as drawn.
- `turnaround.png`, back view: no longer leggings. The seat still shows the two buttocks' shape under the
  cloth, softened.

## 5. Still wrong, ranked for round 3

1. **No real drape folds.** The legs are smooth, wide cylinders with soft vertical ridges. In the turnaround
   the lower legs show faint vertical stripes (the drape's angular bins and the coarse MPFB columns). The
   drawing has diagonal pulls from the knee, a break over the boot, and creases at the crotch and behind the
   knee. Next: a baked cloth simulation on the GPU machine (the shell as the cloth, pinned at the waistband,
   the posed body as the collider, a few hundred frames, the result written back as the rest shape through
   the inverse pose, or a corrective shape key), or displacement of fold shapes along the pose's strain.
2. **The hem stack reads a little like a regular cuff.** The rolls are rings that vary round the leg, but
   they are not the drawn bunched pile that folds over the laces at the front. Simulation would give this
   too.
3. **Seat:** in the hero pose the buttocks still show under the cloth from behind, and there is a small
   knob where the back seam meets the crotch.
4. **Carrier flap in the waist (14 mm):** the carrier owner's to fix (§4). Check after their rebuild.
5. **Waistband:** a plain offset ring 9 to 12 mm off the skin, with no belt loops or fly.
6. **Pockets are still pillows on a sheet:** no bellows side gussets, hook-and-loop strips or the knee
   pocket's top opening. The flap overhangs only by being larger.
7. **No camouflage, ripstop or Cordura materials** (the materials round; spec 16 has `Cordura.500D.*`).

## 6. Round 5 (2026-11-15): materials

The flat colours became the library's recipes (`MATERIALS` in trousers.py, swapped by `common.library_pass`;
the hexes in `COLOURS` stay as the solid-view colours):
- **Shell: `NYCO.Ripstop.Camo`** (new; `Trousers.Mat.Camo`). The pattern is ChatGPT's R002 print on `UV.Real`
  (Smart UV Project scaled to metres per island, `lib/uv.py real_project`), tiled at 750 mm so the blotches are
  about 90-180 mm as on the drawn thighs (the painter's were smaller). The print's colour is divided by its own
  mean and its luminance spread raised by `contrast` 2.0 (R002 spans only 1 : 3.3 p5-p95); the recipe's albedo
  #363533 sets the mean. Fabric061's normal at 64 mm, the 6 mm ripstop grid (raised, glossier lines), a ±15 %
  fade mottle over 150 mm.
- **Wear where it happens**: dust held on the cloth's sides too (the up-facing band widened to -0.55..0.9, power
  1), in 90 mm patches, by height zones from the rest heights (`dust_zones()`: shin 1.0, knee 0.8, thigh 0.45,
  seat 0.25), the left leg x1.0 and the right x0.8 (the left boot is the dustier); grime in the hem band (below
  200-320 mm above the floor, preset `cloth.thigh`).
- **Knee-pad pockets: `Cordura.500D.Black`** (`Trousers.Mat.KneePocket`) with the trousers' wear preset.
- The albedo was set against the hero render (the flat #2a2723 rendered 1.75 x too dark against the reference's
  median over the trousers' mask); see the integration notes in `notes/session_log.md` (round 5) for the
  per-part table and the warm cast of the evaluation light.

Renders opened: `renders/round_05/legs_knees_compare.png`, `soldier_full_compare.png`, `boots_feet_compare.png`.
The camouflage reads on the lower legs and the shins are dustier than the thighs, as drawn.

Still wrong (materials):
1. The print is cut at the Smart UV islands (no garment panel layout yet): blotches jump at island seams.
2. The drawn trousers carry larger pale scuffed patches on the thighs and shins (wear plus dust); ours are
   evener. A wear mask (scuffs at the knees and the shin fronts) is the next step.
3. Under the evaluation's warm key everything dark reads brown; see the session log.

## 7. Round 8 (2026-11-15): the look (critics m26, m40, m9, m48, m12, m52)

- **The camouflage's square steps on the shins (m26, m40) were not texture resolution**: R002 at 750 mm is 0.6 mm a
  texel, finer than the shin crop's pixel. The print sat on `UV.Real` (Smart UV Project), whose islands are a
  few mm across in the hem rolls and folds, so every island sampled a different part of the print: a patchwork of
  small squares. Now the print is **box-projected on the rest mesh** (`print.projection: rest_box`, blend 0.35;
  the point attribute `rest_pos` = the unposed vertex positions, written by `common.library_pass` through
  `materials.rest_position()`, carried through Armature, Solidify and Subdivision), so it is continuous over the
  whole shell and does not swim with the pose. The fine weave and the 6 mm ripstop grid stay on `UV.Real` (an
  island seam in a 6 mm grid does not show at hero scale).
- **Matte ripstop** (m48): roughness 0.74 -> 0.82, specular 0.42 -> 0.36, sheen 0.06 -> 0.04.
- **Albedo** #363533 -> #474644: with the evaluation light corrected (scene.py, round 8) the trousers' median
  rendered 1.36 x too dark against the reference's; now 1.05 (graded).
- **Wear by edges and contact** (`mat_groups.abrasion`): `abrade` along the shell's own edges (the hems, pocket
  and flap edges: `edge_near`, `materials.edge_distance()`, an 8 mm band) toward a paler abraded #5e5b55; `rub`
  where the leg rigs' straps and the knee pads lie on the cloth (occlusion by other objects within 12 mm). The
  height dust zones and the hem grime are as round 5.

Look-loop renders opened (`renders/look/M1`..`M5`, the round-6 caches re-materialled in memory,
`scripts/tools/look_loop.py`): `sheet_legs_knees_graded`, `sheet_boots_feet_graded`, the shin zoom. The print is
continuous over the shins and the hem roll; no steps.

Still wrong: the drawn trousers are near-black with pale grey scuffed patches; ours read as a grey-brown mottle,
the dust drift still the brightest element on the shins. The knee and shin scuffs of the drawing (large pale worn
patches) are not modelled as such; `abrade` follows edges only.
