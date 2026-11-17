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

## 8. Round 9 (2026-11-15): a real cut, draped by the cloth solver (critics m1, m13, m6, m21, m42, m16, m35, m19)

**Method** (trousers.py module doc; shared helpers `scripts/parts/cloth.py`):
1. **The cut as a field** (`cut_field`, `CUT`): per 8 mm slice of the rest body, the convex hull of the skin's exact plane
   section (the skin's edges cut by the plane) grown by the ease. Above the crotch one hull round the whole section, 8 mm
   more behind (the seat); below it one per leg (`leg_out` 22-27 outward, front and back; `leg_in` 8-18 on the medial
   side). The legs are joined by a smooth union (`gusset_k` 60 at the crotch to 0 at z 790): the **gusset**, so the
   crotch seam bridges the hollows instead of following the perineum. Hull points are carried down the back from the
   seat's crest (0.18 mm in per mm down) and all round below the knee (0.12): the cloth falls from crests. Below z 400 the
   leg blends into the boot shaft's ellipse + 8 (flaring 24 going up). Meshed by surface nets (`cloth.surface_nets`),
   cut at the waist plane and at z 75, Taubin-smoothed.
2. **The drape** (`cloth.simulate`, `SIM`; Blender 4.5 cloth, 60 frames, about 2 min for 24k vertices on 8 threads;
   cached in `cache/cloth/trousers_<hash>.npz`): NYCO ripstop at a G3's weight (vertex mass 0.03: the first solve at
   0.12 hung 2.6 kg from the waistband, stretched the seat onto the buttocks and gathered the thighs like a skirt),
   tension 80, bending 4, self-collision below z 560; colliders the rest skin and two boot-shaft proxies; the waistband
   held, the hips and seat on a soft goal (0.3), the legs free.
3. **The blousing** (`BLOUSE`): each leg is cut long (down to z 75) and in the solve its bottom ring is held and pushed
   up over 25 frames, 75 mm on the left, 85 on the right, to the cuff (z 150 / 160, 16-26 mm under the boot collar's
   rim, outside the shaft). The surplus length buckles under gravity and self-collision and folds down over the cuff;
   the start carries smooth radial bumps (seed 9, 4 mm), so the legs stack differently.
   - Cloth's `rest_shape_key` (springs' rest lengths from a longer shape key) was tried first and does nothing in 4.5
     headless (a test tube gave identical vertices with and without it); moving held vertices does work (`cloth.py`).
4. **Rest-solved and weight-bound, not hero-solved and baked**: the one mesh serves the hero pose and the walk; a
   standing man's folds are gravity's and the blousing's, which a rest solve gives. The cost: no knee-bend folds from
   the pose (skinning only) and none at the hip crease when the thigh lifts. The gusset and seat weights are smoothed
   (`smooth_weights`, z > 860 and the inner thighs above z 740, |x| < 70), so the gusset takes both thighs' motion.
5. Pockets lie on a heavily smoothed copy of the drape (laid on the folds they crumpled with them). The procedural knee
   folds, seam band and hem rolls of round 2 are gone.

**Ease and girths** (rest; girth = convex hull of the section, a tape measure; ease = shell to skin, p10 / median /
p90 mm; round 8 in brackets):

| | Round 9 | Round 8 |
|---|---|---|
| Thigh girth z 820 (body 524) | L 723, R 723 | 689 |
| Knee girth (body 310) | 513 | 529 |
| Calf girth z 420 (body 374) | 519 | 556 |
| At z 218 (the stack / blousing) | L 475, R 466 | 499 |
| Ease, seat and crotch, back | 21 / 30 / 47 | 26 / 34 / 50 |
| Ease, blousing above the cuff (z 165-300) | 12 / 28 / 44 | 17-20 / 33-36 / 46-48 |
| Ease, seat and crotch, front | 17 / 20 / 31 | 11 / 17 / 20 |
| Ease, thigh front / back | 16 / 21 / 27 ; 16 / 25 / 39 | 20 / 21 / 22 ; 20 / 21 / 22 |
| Ease, knee front / back | 12 / 21 / 35 ; 15 / 21 / 27 | 22 / 24 / 27 ; 22 / 25 / 29 |
| Ease, calf front / back | 10 / 24 / 40 ; 14 / 19 / 25 | 24 / 24 / 35 ; 23 / 24 / 27 |
| Seat standoff straight behind, z 930 / 880 / 840 | 31 / 49 / 61 | 30 / 44 / 31 |

The round-8 shell held a near-constant 20-24 mm everywhere (an offset from the skin, so every form showed through); the
draped one varies from 13 to 48, which is what reads as cloth. Clearance: rest minimum 3.0 mm, hero pose 3.0, nothing
inside.

**Materials** (critics m16, m35, m19; measured on round 8's graded legs_knees crop under the trousers' mask: median
luminance 1.25 x the reference's, b/g 0.96 against 0.86, saturation 0.24 against 0.32, the brightest tenth 1.8 x): albedo
#474644 -> #43403b (darker, warmer), dust amount 1.2 -> 0.6 and **brown dust** (the camo recipe's new `dust.thin` /
`dust.thick` #6e5f4f / #8f7a62, read by `mat_groups.weather`; the library's grey hangar film is the default elsewhere),
abraded edges #57503f at 32 %, the weave photo's normal (Fabric061, lint holds its physical 64 mm tile) at 0.06 instead
of 0.25 so it no longer reads as burlap; the 6 mm ripstop grid carries the fine texture.

Renders opened: `renders/trousers/trousers_rest_{front,back,side,threequarter}.png` and `trousers_hero_soldier_full_pair`
after each solve (four solves: the soft-and-heavy one, the rest-key one that did nothing, the moving-cuff one, the
fuller-leg one kept). Round 9's evaluation: section 9 below.

## 9. Round 9's evaluation (renders/round_09/) and what is still wrong

Opened: `soldier_full_compare`, `legs_knees_compare`, `boots_feet_compare`, `torso_vest_compare`, `turnaround`.
- **No longer tights**: front and three-quarter views show even ease from hip to cuff, the crotch bridged by the gusset
  (hidden by the carbine in the hero frame), soft drape folds on the thighs and shins.
- **The blousing** reads as cloth bunched over the boot tops, different on the two legs, but more like a gathered
  elastic cuff than the reference's loose break: the held cuff ring is a tidy band round the collar with the puff above
  it. Next: let the cuff ring go free after the push (hold it only by a soft goal) so the hem drops and opens over the
  collar, or push it down onto the boot instead of holding it at a fixed ring.
- **Seat from behind**: the cleft is spanned and the buttocks' lower curve is softer, but the two forms still read in the
  back view and a small dip remains where the back seam meets the gusset.
- **Colour** (my measure, graded legs_knees crop under the trousers' mask; round 8 in brackets): median luminance
  0.45 x the reference's (1.25 x), brightest tenth 0.97 x (1.8 x), b/g 0.88 against 0.87 (0.96), saturation 0.27
  against 0.32 (0.24). The pale wash and the grey cast are gone, the hue matches, but the median is now too dark: the
  roomier cloth self-shadows more than the offset shell did. Next round: albedo up about 1.4 x (#43403b -> about
  #504c46) with the brown dust kept.
- **Clashes** (`clashes.md`): the first round-9 build had boots-trousers 194 vertices to 14.2 mm (the cuff ring in the
  right boot's tongue and collar in the pose). Fixed in the same round: the cuff 13 mm over the shaft's ellipse (was 8)
  and the solve's boot proxies grown 5 mm for the tongue and collar padding (`CUFF["over"]`, `CUFF["proxy_grow"]`);
  the final round-9 numbers are in `renders/round_09/clashes.md`. Trousers-belt (1.7 mm) and trousers-armour (0.6) as
  before.
- Not touched this round: pockets are still pillows on sheets (no bellows gussets, flap hardware); waistband plain;
  knee-bend and hip-crease folds come from skinning only (the solve is at rest).

## 10. Round 10 (2026-11-16): hems over the boots, the seat, the print (critics m5, m18, m19, m32, m20, m35, m44, m28)

**The hem falls over the real boots** (m18, m5; `HEM`, `BootHulls`, `drape10`). Round 9's blousing (a held cuff ring pushed
up 75-85 mm) read as a gathered elastic cuff over bare boot shafts, crinkled the shins into even foil-like lumps, and gave
the Godot export its spiky crown; it is kept behind `--blouse` only.
- `BootHulls` reads `cache/parts/boots.blend` in the rest frame (upper, collar, tongue, hooks, laces, strap, buckle, keepers,
  tacks, stays, eyelets) and keeps their convex section every 6 mm. The loaded data are removed again, so nothing of the
  boots is saved with the trousers.
- Below z 400 each leg blends into a tube round the boot's section at that height and at the collar, plus 12 mm (the G3's
  460 opening over a 385 collar), flaring 22 going up. It is cut by a plane tilted forward, z 76 at y +80 rising to z 118 at
  y -70 (rest). The first cut, 88 / 138, still showed the shaft from the hooks down.
- The solve: no held ring. The hem carries a soft goal (0.18) pushed up 30 / 38 mm, the waist is held, and the colliders are
  the rest skin and the boots' sections (grown 2.5 mm) instead of round 9's elliptic stand-ins. Bending stiffness is
  4 -> 12 (`SIM10`), for crisper, larger folds.
- After the solve the shell is pushed out of the boots, then out of the skin. Below the boot top it takes the weights of the
  nearest vertex of the boot's upper, blended back over 40 mm above it (`boot_weights`), so the hem rides on the boot in the
  pose.
- The hem at rest, front / back: left 136 / 95, right 135 / 97 (172 / 131 above the floor; round 9's cuff was a level ring
  at 150 / 160). Hem girth: left 497, right 510 (target 460).
- Rest shell vertices inside the boots' sections: 0. In the hero pose: 0 inside the posed boot sections on either leg; the
  least clearance is 3.4 mm left, 3.7 right (scratch check against the posed upper, collar, tongue, stays, hooks, laces,
  strap and buckle).

**The seat** (m19, m32). The per-slice hull of the cut already bridged the cleft at rest. The round 9 solve let the bridged
cloth sag back under a soft 0.3 goal, and the posed hips folded it in through the seat's weights.
- In the solve the centre back (|x| < 85, from the crotch to the waistband) now carries a firm 0.85 goal on the cut.
- The seat behind (z 860-1070, y > 20) gets 26 more passes of weight smoothing. The first try smoothed the whole hips
  40 times; that also moved the front waistband's weights, which the carrier's front flap and bag copy.
- New metric, `seat_concavity` (how deep the back profile dips below its convex hull within 60 mm of the middle, in the
  slab's own frame):
  - rest: 0.1 mm at z 1040 / 1000 / 960, 0.6 at 920;
  - hero pose: 1.4 / 2.2 / 2.7 / 11.4 mm;
  - 37 mm at z 890 is the gap between the legs, not the seat.
- Round 9 was not measured this way. Its turnaround showed a deep cleft; the new back view shows the two buttocks' lower
  curves softened and a shallow line at the back seam.

**Knee pocket** (m28): the pocket's top stood 28 mm above round 10's smaller knee cap as a plain black band. It is now
centre -19 below the knee joint, half height 101 (was -8, 112), so its top lies 6 mm above the cap and its bottom where it
was.

**Print and dust** (m20, m35, m44). Measured with `look_loop.py` on in-memory assembly copies and `look_stats.py`
(graded, under the trousers' mask, reference / render).

| | Round 10 (round 9's table) | Final |
|---|---|---|
| legs_knees median | 1.85 | 0.96 |
| legs_knees p90 | 1.34 | 1.31 |
| legs_knees b/g, ref vs render | 0.90 vs 0.94 | 0.86 vs 0.86 |
| boots_feet median (the hems) | - | 0.66 |

What changed in the table:
- albedo #43403b -> #4c4843;
- the print's spread `contrast` 2.0 -> 0.8 (the soft high-contrast pale blotches);
- mottle 0.15 -> 0.10;
- dust 0.6 -> 1.25, in 170 mm drifts (was 90) of a lighter tan (#85725a / #a08a6c);
- the ripstop grid 6 -> 5 mm at a quarter of its relief (0.05 -> 0.012 mm, rough_add -0.05 -> -0.015): the coarse grid;
- dust zones evened (`dust_zones`): thigh 0.45 -> 0.8 and seat 0.25 -> 0.45 of the shin, the right leg 0.8 -> 0.9 of the
  left. The preset's table caps each zone's mask, so the profile is written as one mask on the shin's weight.

The loop's variants and why the table ended where it did:
- an olive-grey version matched the median chroma but read green;
- a cool charcoal one read right but measured too blue;
- the first table on the new cut (#53514d, dust 1.5) went too bright (legs_knees 0.85, the hems 0.54), because the straight
  legs self-shadow less.

**Girths and ease** (rest; hull girths; ease p10 / median / p90 mm). Round 9 is in brackets.
- Girths: thigh 733 (723), knee 513 (512), calf 518 (518).
- At z 218: 516 (475). The tube now goes round the boot, so the "blouse" band's ease, 31 / 43 / 50 front (12 / 28 / 44),
  counts the boot under it.
- Ease, seat and crotch, back: 23 / 30 / 47 (21 / 30 / 47).
- Ease, thigh front: 16 / 25 / 26 (16 / 21 / 27).
- Ease, calf front: 15 / 24 / 37 (10 / 24 / 40).
- Seat standoff straight behind at z 930 / 880 / 840: 31.5 / 49.9 / 61.8 (31 / 49 / 61).

**Clearance.**
- Rest: 2 shell vertices at the back of the right hem (-223, 80, 87) read 28 mm inside the skin, 7 in the pose (to 31 mm at
  (-202, 312, 136)). This is where the body's heel already comes through the boot's counter (the boots' body-boots clash);
  pushing out of the skin after the boots did not move them.
- Elsewhere the minimum is 10 mm (p01).

**Integration** (scratch assembly of the caches, `clash_report` and `standoff_report` as `assemble.py` runs them; round 10 in
brackets):
- boots-trousers: 70 vertices to 25.0 mm in `Boot.L.Stays` (112 to 14.1 in five boot objects). Checked: these are hem
  vertices at the left boot's front-medial corner, 10-24 mm OUTSIDE the posed boot's sections. No trouser vertex lies inside
  either posed boot. The open-shell test reads the cloth over the shaft's opening as inside. The real round 9 problem (the
  hem in the tongues) is gone.
- trousers-belt: 66 to 2.1 mm (53 to 2.6).
- The carrier, armour and belt rebuilt on the new caches.
- Stand-offs: 27 flagged (28).
  - Cleared: `Carrier.Front.Bag`, `Carrier.Strap.R.Pad`.
  - New: `Belt.Rig.L.MagPouch.1`, median 16.7 mm, for the belt's owner. The thigh hull girth went 723 -> 733.

**Renders opened**:
- `renders/trousers/trousers_rest_{back,hem_side}.png` and `trousers_hero_legs_knees_pair.png` after the first solve;
- the scratch turnarounds (back, three-quarter, side);
- `renders/look/tr10_base`, `tr10_a` to `tr10_d`, `tr10_new` and `tr10_final`: `sheet_legs_knees_graded`,
  `sheet_boots_feet_graded`.

## 11. Still wrong, ranked for round 11

1. **The lower legs are now plain, almost smooth tubes.** The lumps are gone, but so are most folds. The reference has a few
   big diagonal pulls from the knee and a loose break over the boot. The hem's soft goal lifted it about 20 mm at the back
   and 7 at the front, so the break is a straight edge, not the drawn roll.
   - Next: a longer cut below the hem (more surplus) with the hem free to land on the laces, or a short hero-pose settle of
     the lower legs only.
2. **The hems still sit a little high at the front** (172 above the floor): the boots_feet crop shows the top of the lacing
   between hem and vamp. The drawn hem covers the collar and rolls onto the laces.
3. **The seat** shows a shallow back-seam line and the buttocks' lower curves in the posed back view (11 mm dip at z 920).
4. **The print** reads as a brown-grey with soft khaki drifts. The drawn trousers are blue-black with tan patches that are
   crisper and larger on the shins and thighs. Dust is still placed by height and up-facing only (no knee or shin scuffs).
   The boots_feet crop's hems render 1.5 x the reference's median; the reference's hems sit in deep shadow.
5. **The hem against the heel**: 2 rest / 7 posed vertices in the right heel's skin. The boots part's heel and the body
   clash there (boots-body).
6. Not touched: pockets are still pillows on sheets; the waistband is plain; there are no knee-bend folds from the pose
   (rest solve).
