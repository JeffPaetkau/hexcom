# Research: a scripted high-resolution method for the bare foot (2026-10-10)

Trial region: the LEFT foot's hallux, toe 2 and the 1-2 web, with the first MTP prominence, on part 01's
default build (X3 locked). Code: `scripts/research/foot_hires/` (`run.py` is the entry point; `common`, `toes`,
`macro`, `detail`, `sdf`, `method_fields`, `method_sdf`, `look`, `sheet`, `presets.json`). Renders:
`renders/research/foot_hires/<run>/` (ignored). Critic sheets: `critic_sheet.png` (LookDev, spec 16's
recipes) and `critic_sheet_form.png` (clay).

    blender -b cache/body/rigged.blend --python-exit-code 1 --python scripts/research/foot_hires/run.py --
        --method fields --tier form,eval --tag final --views hr.front,hr.top34,hr.medial,hr.plantar,hr.hallux,hr.toe2

## Why the foot looked the way the reviews say

MPFB's foot is a 5 mm cage with toes as cylinders and a flush nail patch; part 01 shaped it with fields
whose radii must exceed 1.7 x the cage spacing. A nail fold is about 1 mm, a lip's roll 0.5 mm: on that cage
the only way to show a nail was a plate in a groove. Section plots (`detail.py` debug, `method_fields.dump_sections`)
showed the rest: MakeHuman's toes end as flat-topped cylinders with a vertical front, the plantar line of the
hallux is straight (no pulp), and MakeHuman's own nail patch leaves raised sides and a dip behind the fold.

## Methods tried

* **base** (`base/`): part 01 as built, the reviews' foot.
* **(a) fields on the subdivided cage** (`fields_v1` ... `fields_v13`, `fields_final`). The closeup copy at
  Catmull-Clark level 5 (0.16-0.19 mm on the toes; 1.2 M vertices below z 300), part 01's nail-bed step taken
  back out on toes 1-2 (its own `fields.pass_b(nails=False)`, read-only). Large forms as explicit fields in toe
  frames (`macro.py`): pulps and their noses, the tip's dorsum drooped toward the nose, distal sections squared,
  a spade-shaped hallux end, the MTP prominence, the metatarsal head, the extensor tendons. Detail as height
  fields (`detail.py`): a **fitted nail** (a blurred height map of the dorsum; the plate fitted to it station by
  station so the folds have exactly their set heights; the skin made to fit the plate: bed, a ramp so the
  contact line is interpolated, lips onto the edge, hidden margins clamped to what the skin covers, the root
  diving toward the matrix, the free edge 3 mm short of the nose with an undercut) and wrinkle creases (a Ricker
  section, seeded wobble).
* **(b) SDF / volume** (`sdf_p1`, `sdf_p2`). An OpenVDB level set of the cropped, capped forefoot (0.2 mm
  voxels, +-4.5 mm band; `import openvdb` works in Blender 4.5.14: level sets from quads, numpy box copies,
  `convertToQuads`), edited by smooth unions with ellipsoids, spheres and tapered capsules, smooth
  subtraction for the droop, and a masked morphological closing (dilate, re-distance, erode) for the web;
  polygonised by OpenVDB (1.08 M quads in front of y_F -146), groups taken from the nearest dense vertex, the same
  nails and creases on top.
* **Webs compared** (`sheets/webs.png`): Taubin fairing of the cleft (`fields_webfair`) changes nothing (it is
  volume-preserving, so a slot stays a slot); the SDF closing projected onto the dense cage (`fields_websdf`)
  fills the floor but crumples where the two walls land on one surface; a relax-and-reproject loop cures it.
* **(c) parametric loft**: not built. Its value (control of sections) is in the squaring and spade fields; its
  hard part (fusing toes into the forefoot) is exactly what the closing does.

## Choice: (a) as the carrier, (b)'s closing where topology must be bridged

The cage subdivided to 0.17 mm, shaped by fields, with SDF operations only where surfaces must merge (the web,
by `method_fields.web_by_closing`: field, closing, projection, relaxation). Why:

1. It keeps MakeHuman's topology, UVs, vertex groups and shape-key correspondence; the result is a level-5
   sculpt of `Body.Mesh` (Multires-shaped data), so rig, export and expressions keep working.
2. Height-field detail needs a regular, top-most surface. On (b)'s voxel mesh the same nail code went noisy (a
   pitted patch, a raised frame), and separate primitives read as lumps (a peanut pulp, a ball on toe 2).
3. Cost: (a) builds in 31 s (144 s with the web's closing), (b) in 117-133 s, plus a seam and weights by transfer.

## Honest state against the reviews

Better: nails thin, set in, overlapped by lateral folds, a soft eponychium, no groove; the hallux nail broader
(18.5 x 17.5) and back from the tip with the pulp leading and a dark line under the free edge; tips are pads,
not sawn cylinders; the hallux end broad and flat-topped; the first MTP prominence and the EHL cord present;
the 1-2 web filled at its floor. X3 kept (hallux 30 mm, 1-2 gap 4.5, curl 25), the hallux's IP features 3 mm
distal of MakeHuman's joint cube.

Still wrong: a small sawtooth at the hallux free edge's medial corner and a faint lens behind its fold; the
dorsal IP creases read as three parallel grooves; plantar creases are sharp lines and the hallux pulp's
underside has a flat facet; toe 2 is still somewhat tubular; toes 3-5 keep part 01's capped nails (visible in
the front views); the skin's micro network (spec 16) is too regular and strong at 50 px/mm; lookdev_p01's
stand-in masks show (a corn on toe 4, the ball callus).

## Costs (RTX 3050, OptiX)

Build 144 s (dense copy 10, fields 3, web closing about 110, nails and creases 5); render 0.7 s a view in
clay, 60 s a view at 2048 px eval (1.2 M quads plus two plates of 41 k and 15 k vertices).

## Path to the whole foot, the export and the head

* **Whole foot**: the same code per toe (five nails, a crease table per joint, a closing per web, including the
  touching lesser toes, which replaces part 01's `close_webs`), level 5 on the forefoot only (about 0.6 M).
* **Export**: bake normals (and displacement) from the dense copy to the export mesh by selected-to-active on
  spec 01 §4.9's `Foot.UV` tiles (4096 per foot, 1.2 px/mm: enough for folds, not for the finest creases,
  which stay procedural); the plates export as separate skinned meshes on the distal bones.
* **Rig**: the fields move positions only; subdivision interpolates the deform groups, so the weights hold.
* **Head**: the same structures. Eyeball and teeth are the nail plate (skin fitted onto an inset object with
  lips and hidden margins: lid margins, the lid crease as a fold's back); mouth corners and alar creases are
  webs (closings, projected); the nasolabial fold a crease with shoulders. Ears and eyelids overhang, so the
  top-most-skin gate becomes vector displacement or SDF projection there.

## Risks

Height fields fail on steep sides (gated here; real overhangs on the head); 1.2 M vertices a foot (region
subdivision or Multires needed); projections crumple where surfaces meet (relax-and-reproject); every regime
switch must be continuous or it shows as a sawtooth at 0.2 mm; a 1.2 px/mm bake loses the finest folds;
OpenVDB's Python API is versioned with Blender.

## What I would add to the library

`lib/sdf.py` (sdf.Field: crop-and-cap level sets, local edits, closing, projection; smin/smax and primitives);
in `lib/sculpt.py` a subgraph Taubin/Laplacian (bincount, not `np.add.at`), a 2-D height-map blur, a
top-most-skin gate and the wrinkle crease; part 01's `nails.py` plate and `fields.nail_beds` replaced by
`detail.Nail` on a dense copy; in spec 16's `Nail.Plate` a cuticle and onychodermal band and a lunula of about
1.6 mm (3.5 reads as a manicure); a multi-tier render in one process (`run.py --tier form,eval`).

## Round 1 fixes (2026-10-10)

Critic round 1 (`notes/critic/foot_hires_r1/tally.md`): 4/10 from all three, ten blocking. Fixed on the same
region, run `fields_r2` (parameters in `toes.PARAMS`, marked "round 2"); round 2's packet is
`renders/research/foot_hires/critic/r2/`, round 1 beside round 2 in `renders/research/foot_hires/fields_r2/zooms/`.
`--params '{"nail1": {"debug_dump": 1}}'` dumps a nail's fit and every term of its skin target to
`cache/research/foot_hires/nail1_dbg.npz`, which is how the causes below were found.

* **Torn nail corners (m2, m4, m5).** Cause: the plate was allowed a 26 mm transverse radius and was fitted on
  a dorsum that was flat and, laterally, higher than its midline (the squaring field pushed the section's upper
  corners out), so near the free edge its corners sat 1-2.5 mm inside the side skin. The skin was cut back
  under them by a gate (`on_top`) and a blend (the blurred dorsum) that fell to zero cell by cell where the
  dorsal height map had no vertex (NaN): neighbouring vertices alternated between pulled a millimetre under the
  plate and left where they were, and the plate's white rim showed between them (628 folded edges, all at the
  corners). `past` also switched the target at the outline in the free-edge zone. Fix at the source: the dorsum
  domed to the nail (`square` < 0 rounds the shoulders in, `crown` raises the midline), the plate held to at
  least its own radius (11 / 6 mm), the maps filled outward with a coverage mask for the blend, the skin target
  rewritten so every regime meets the next at the same height (inside and outside blended across +-0.08 mm,
  `past` read at the outline point), the lateral fold running from the plate's edge to the toe's own skin (held
  at the plate's level it stood as a shelf where the side falls away near the tip), the blurred dorsum used only
  over the bed and bias-corrected ("twicing": a plain blur lowered the dome by sigma^2 / 2R, a step at the
  sides). Folds over the plate's edges now 0.5-0.9 mm, equal both sides (round 1: up to 2.5 laterally).
* **Torn web (m3).** The closing was right; the projection was not. Vertices were moved by a mask weight, so
  part-moved ones stopped inside the closed surface; the Newton steps used a 0.1 mm gradient step inside
  0.15 mm voxels with steps up to 3 mm; the relax was a plain Laplacian. Now a vertex moves by how deep the
  closing swallowed it (the field's own value; on the old surface nothing moves), the gradient step is one
  voxel, steps are at most 1 mm, the crowded vertices are spread within the surface (tangential relax) between
  re-projections, and the mask is centred on the measured cleft (x -16.1). In the web's box: one edge with a
  dihedral cosine under 0.9, none folded.
* **Wedge profile (m1).** MakeHuman's toe joint cubes sit under the dorsum, so the hallux's distal axis, and
  the dorsum with it, falls 21 degrees from the IP to the tip; round 1's droop (2.2 mm over the last 9 mm)
  tipped it further, and its pulp inflations peaked mid-pad with the underside rising 3 mm toward the tip.
  Now `lift1` raises the distal dorsum toward the tip (2.4 mm), the droop only rounds the stretch ahead of the
  free edge (over the whole front face, not a 3 mm band that folded it), and the pulp is grown as a smooth union
  with an ellipsoid resting on the floor (`macro.grow`, `macro.pulps`; 28 x 29.6 x 13.6 mm, its front just ahead
  of the nose), so the tip is blunt and fleshy, the pulp bulging below and just beyond the free edge.
  Hallux depth (vertical extent, `report["measure"]`): 19.0 mm at the nail root (round 1 17.6 measured the same
  way, the critics read 15.6 off the profile; spec 19), 22.3 at the IP crease (unchanged; spec 22, X3 about 25).
* **Nails (m6, m14-m17, m21).** Domed (fitted radius 9.5-11 mm on the hallux, 4.5-4.7 on toe 2), the edges
  under soft folds, a curved cuticle line (rising 2.2 / 1.2 mm to the sides), an eponychium lying 1.4 / 0.9 mm
  on the plate 0.3 / 0.22 mm thick so the plate's root never shows, the free edge's line and the bed's end
  uneven (+-0.1, +-0.22 mm), a flatter rim. Material through the trial's own overrides (`look.py`): the lunula a
  1.6 mm crescent over the middle 12 mm (the recipe's arc takes the plate's whole half-width, so the object's
  `nail_half_mm` is set to 6), the free edge ivory and matte (#dfd2bb, transmission 0.56, roughness 0.34), the
  longitudinal ridges 0.004 mm.
* **Pulps (m7).** Grown as ellipsoid unions, so from below they are oval domes: the hallux widest mid-pad (29.4
  mm at y -269, 25.7 at the IP), rounding into the tip, with a `neck` at the flexion crease; toe 2 widest
  mid-pad (15.5 mm) with its neck at the DIP, its pad 2 mm lower and fuller.

Still open: the other majors of round 1 (creases, friction ridges, the skin's crackle, hair, veins, toe 2's
plantar step); a soft vertical crease on the hallux's lateral wall of the web, where its wall meets the web; a
faint mark at toe 2's medial distal corner. Cost: build 167 s (the closing 127).

Library changes proposed (not made): `Nail.FreeEdge` ivory and matte as above; `Nail.Plate`'s ridge depth
0.004 mm; `nail_coords` to take the lunula's half-width separately from the plate's, and the hallux's lunula 1.6
mm; in `lib/sculpt.py` `grow` (a smooth union along the normals), the tangential relax, the map fill with a
coverage mask and the twicing blur; in `lib/sdf.py` the projection weighted by the field's own depth.

## Round 2 fixes (2026-10-12)

Critic round 2 (`notes/critic/foot_hires_r2/tally.md`): 4 / 4 / 5, nothing blocking, all three leading with the
nails. Fixed on the same region, run `fields_r3` (parameters in `toes.PARAMS`, marked "round 3"); round 3's
packet is `renders/research/foot_hires/critic/r3/`, round 2 beside round 3 in
`renders/research/foot_hires/fields_r3/zooms/`.

* **Press-on nails (m1, m20, m33).** Three causes. The lateral fold's target added a roll on top of the toe's
  own skin (`fold_h x 4x(1 - x)`), so a rim stood above the skin all round with a crevice at the plate: the
  piped rim in an even gutter. The proximal fold rose 0.3 mm over a plate that stood 0.12 proud of the dorsum,
  lay flat on it for 1.4 mm, then stepped back up to the dorsum: the second ridge, and the plate's root showing
  as a lip. And the width clip's lower bound (`min_width` x width, 10.2 mm) was over its upper (9.25), so every
  station was width / 2, and toe 2's parameters were the hallux's ratios: one rounded rectangle, scaled. Now a
  fold is the toe's own skin running on to the outline and rounding down onto the plate over its last
  `epo_w` / `lat_width` mm (`roll_k`), and the plate is fitted under it: the lateral folds' heights as before,
  at the root `lift_root` (-0.32 / -0.22 mm) below the dorsum, so the plate comes out from under the proximal
  fold and nothing stands above the skin. Each nail has its own plan (`plan`, `asym`, `cuticle`, `corner_prox`)
  and each lateral fold its own height (`fold_asym`, `fold_wobble`): the hallux a broad shovel, narrower at the
  root, its lateral side tucked under a higher fold; toe 2 a short rounded D whose sides converge toward the cut.
  The plate keeps its 9.7-11 mm transverse radius (4.7-4.9 on toe 2); the folds now stand 1.1 / 1.4 mm (medial /
  lateral) over the hallux plate's visible edge at the root, 0.4 / 0.7 mid-nail and none at the free edge (toe 2
  0.6 / 0.5, 0.4 / 0.35, none).
* **French-tip free edge (m2).** Round 2's rim was a half-round (`bulge` 0.3): the bead. The cut face is now
  flat and thinner (0.6 / 0.42 mm at the edge, spec 1.1 / 0.8, which read as a slab at 45 px/mm), the cut
  straight across with its corners taken back at a slant (`clip`: past 0.6 / 0.5 of the half-width, 6-9 degrees)
  and small, unequal corner radii, `edge_wave` 0.03 (round 2's 0.1 mm wave and 2.8 mm corners curling back read
  as an S). The bed ends in an arc (`bed_arc` 0.8 / 0.45 mm back at the sides), so the white edge is narrowest at
  the centre.
* **Nail shading (m3, m4), through `look.py`'s overrides only.** The plate clear (transmission 0.96: at 0.88
  each of its two surfaces sent 12 % of the light to a diffuse lobe of the pale base, which milked the bed over),
  rough 0.10; the ridges 0.0015 mm and the coat's roughness 0.18 (at 0.10 the coat's lobe was narrower than
  the ridges' slopes, so every ridge lit as a line; now they ripple only at a highlight's edge); the hallux's
  lunula 2.3 mm over its middle 13 mm, a translucent pinkish white (transmission 0.8); the onychodermal band as
  two steps of a paler, less clear plate over the last 0.75 mm of the bed (`BAND_STEPS`: the library names a
  material by recipe and part, so they are parts of their own); the free edge off-white and translucent
  (transmission 0.74). The clear plate showed the skin's crackle on the bed, so the bed's faces (the face
  attribute `Hires.Bed`, written by `method_fields.finish`) carry the skin recipe with its line network
  nearly flat and its cavity shading off (`BED_OVERRIDES`).
* **Toe 2, a sausage (m5).** `macro.toe2_outline`: Gaussians along the segments on the toe's sides (|n . b|^1.5),
  along the normals: the PIP knuckle +1.6 mm (and a little on top), the middle phalanx's waist -1.2, the pulp's
  flare +0.45; growth stops 0.35 mm from any other toe's skin (a k-d tree's nearest distance, by a soft minimum),
  because toes 2 and 3 touch: the knuckle grows medially and on top, the waist opens a gap to toe 3. Plan widths
  (`report["measure"]`, y slices): 15.9 mm at the PIP, 12.7 at the waist (round 2 14.2-14.5), 14.3 at the DIP,
  15.5 at the pulp.
* **A stage cache.** The large forms and the web take about 150 s, the nails 6: `method_fields.build` keeps the
  skin after the web in `cache/research/foot_hires/stage_<key>.npz`, the key hashing the dense skin as copied,
  every parameter but the nails' and creases', and macro.py and sdf.py (`--params '{"stage_cache": 0}'` turns it
  off; clear it if `web_by_closing` changes). A nail-only change rebuilds in about 16 s.

Library changes proposed (not made): in `Nail.Plate` transmission 0.96, roughness 0.10, coat roughness 0.18,
albedo #eee4dc, lunula #f3e7e3 at transmission 0.8, and `ridge_depth_mm` 0.0015 in the nails' common values;
in `Nail.FreeEdge` albedo #efe8dd, transmission 0.74, coat roughness 0.18; in `mat_skin.build_nail` each ridge's
strength varied along the nail every couple of millimetres (its noise reads `v x 0.08`, so a ridge keeps one
strength for the nail's whole length, which no override reaches) with its floor at 0 rather than 0.15, an
onychodermal band term (a smooth paler, less clear band before the free edge) in place of the trial's stepped
materials, and the lunula's half-width as its own property; in `Skin.Foot` the micro network and its cavity
shading faded out on the nail bed (the `toenails` mask), and the catalogue's unused `nail_bed.hyponychium_hex`
put on the skin under the free edge; in part 01, `detail.Nail`'s fold and plan (a fold as the skin rounding
onto a plate fitted under it, per-nail plans, a clipped straight cut with a flat cut face) replacing
`nails.py`'s plates.

Still open: round 2's other majors (the hallux's plantar IP notch, toe 2's knife-cut DIP crease and PIP cuff, the
MTP line, the base sulcus, tendons, veins and hair, the stamped knuckle wrinkles, the boxy pulps, the web's
shelf, the friction ridges, the skin's crackle, the hallux's depth); the ridges still run the nail's whole length
(the library's noise, above); a pinch on toe 2's medial side just past the DIP (the trial's `neck2`); toes 3-5 keep
part 01's nails, whose combed streaks and white tips now stand out beside the new ones. Cost: build 161 s from
scratch (16 s with the stage cached), render 63 s a view at 2048 px eval.

## Round 3 fixes (2026-10-12)

Critic round 3 (`notes/critic/foot_hires_r3/tally.md`): 4 / 4 / 4, two blocking; its fix agent had claimed changes
the packet did not show. Fixed in run `fields_r4` (parameters in `toes.PARAMS`, marked "round 4"); round 4's packet
is `renders/research/foot_hires/critic/r4/` (sha 9b080f3ae430). Every change was judged in the packet's own views at
its scale, round 3 beside round 4: `renders/research/foot_hires/fields_r4/sbs/` (`item1_*`, `item2_*`, `item3_*`).

* **Toe 2's sleeve cuff (m1) and the hallux's V-notch (m4).** The base has no fold; round 3's waist alone folded 35
  faces. Its station was t along the middle phalanx's axis, which dips 31 degrees, so on the plantar skin, 13 mm below
  the joint, t 8 fell under the PIP, on the flexion fold part 01's curl leaves there (faces squeezed to 0.003-0.015 mm,
  a 45 degree kink), and pulled in along normals that turn sharply in it the skin folded over itself. The same tilt
  put every plantar crease 3-8 mm proximal of its joint: toe 2's PIP crease under its proximal phalanx (the "slot at
  the toe's base", m21), the hallux's 6 mm behind its IP, stacked on the neck's 0.85 mm pinch (the notch). Now
  `macro.Plan` gives each toe a plan frame (stations are vertical planes from a joint); toe 2's knuckle, waist and
  flare move the skin sideways by its share of the side, not along normals (`toe2_outline`); the plantar creases are
  soft Gaussian dips cut straight up under their joints, on the underside only, fading before the sides
  (`plan_crease`: a move along one direction cannot fold the skin while it changes slower than 1:1 along it); the
  necks pinch the lower sides only (0.35 / 0.3 mm); and toe 2's PIP fold is rounded (`close_folds`: the underside's
  height map in the plan frame closed from below along the toe, sigma 1.6 mm, the squeezed band spread by 400
  Laplacian passes in plan coordinates and set on the closed surface). Toe 2's underside, edges with a dihedral
  cosine under 0.7: 140 (53 folded) in round 3, none now. At the packet's scale the flaps and the step are gone and
  the hallux's profile arches with a shallow dip; the PIP fold still shows as a thin infold line across toe 2.
  Dead ends: Taubin fairing of the band (more folds), a smoothed correction added to the kink (lowered it 0.4 mm,
  kept its corner), 0.2 mm map cells (spikes), sigma 2.0 with 900 passes (a faint rectangle at the window's edges).
* **The skin's crackle (m5), in the library** (spec 16 §9, 2026-10-12): `MG.Skin.Micro`'s lines stretched 1.6 along
  a Langer direction, warped, broken up along their length, soft Gaussian grooves; `Skin.Foot` scales them by region
  (dorsum 0.6, toes 0.5, joints 1.0, nail folds 0.1, bed 0) and keeps 0.4 of their darkening. The folds are the
  `toenails` group's soft margin: `detail.Nail.apply` now writes a halo of 0.42 up to 1.8 / 1.2 mm past the outline
  (`fold_halo`). `look.BED_OVERRIDES` keeps only the bed's lower undulation.
* **The nail rebuilt from its parts (m2, m3, m16, m20).** The plate is bonded to its bed: its underside over the bed
  is open (`open_bed`; round 3's closed shell had an air gap under it, two glass interfaces a pass and light piped
  round to a bright rim). The lateral folds swallow the margin unevenly (`cover_wobble` 0.35 / 0.22 mm, slow waves,
  one-sided, fading toward the tip) over a plate whose own edge stays smooth (`half_plan` beside `half_vis`), with
  more uneven heights and steeper lips; the proximal fold is a broad soft roll (`roll_k_prox` 1.5, `epo_w` 0.9 /
  0.6); the free edge is thinner (0.5 / 0.36 mm). The zones are the library's (`mat_skin.build_nail`): a lunula over
  its own half-width (2.4 mm deep, half-width 6 on the hallux; 0.6 / 3.2 on toe 2), opaque (transmission 0.22); the
  body satin (transmission 0.9, roughness 0.22, coat 0.25 / 0.3) with faint longitudinal streaks; an onychodermal
  band over the bed's last 0.9 mm; an ivory free edge (#ebdfca, transmission 0.15, roughness 0.42) with its grime
  line; ridges 0.0012 mm, varying along each ridge to 0; a cuticle band along the fold's line. At the packet's scale
  the lunula, the pink bed, the band, the ivory edge and the uneven medial fold read; the cuticle merges with the
  lunula's edge; in clay the plate still sits in a continuous outline groove, narrower and uneven but not gone.
* Cost: build 166 s from scratch, render 63 s a view at 2048 px eval.

Still open: the PIP fold's line on toe 2; the clay outline groove round the plates; the free edge's squared lateral
corner (m23); the dorsal knuckle wrinkles and toe 2's DIP crease (m8, m14: the shader's crease groove on narrow
masks); the base sulcus, tendons, veins, hair, pulps, web shelf and friction ridges (m6, m7, m9-m13); toes 3-5.

## Round 4 fixes (2026-10-12)

Critic round 4 (`notes/critic/foot_hires_r4/tally.md`): 4 / 4 / 4, the fourth round at 4, one blocking (no hair).
Fixed in run `fields_r5` (parameters in `toes.PARAMS`, marked "round 5"); round 5's packet is
`renders/research/foot_hires/critic/r5/`. Every image of round 4's packet beside the same view of round 5 at the
packet's scale: `renders/research/foot_hires/fields_r5/sbs/sbs_<packet file>.png`.

* **The nail and its folds as one surface (m2, m3, m15, m17, m18, m20, m25).** Why four rounds stalled: the plate
  was a separate shell and the skin was fitted round it, so wherever they met the shell's thickness showed as a
  bevel, the skin met it in an intersection crease of one width all round (the gutter), and every zone was a
  colour on a refracting slab (the French tip, the white stripe, the white crescent). Now (`continuous`,
  `detail.Nail._target_continuous`) the plate's visible top is the skin's own surface: the fitted dome, turning
  down 0.22 mm (toe 2 0.14) into each lateral groove over its last 1.4 mm (0.9; `edge_curl`, `edge_drop`). The
  folds are the same skin rolling down onto it: the lateral folds 1.6 mm wide (toe 2 1.1), each varying by a
  third along the nail on its own slow wave (`lat_width_wobble`) and kept to the bed's end (`lat_fade`), the
  proximal fold a 1.4 mm roll (1.0) 0.38 mm over the plate's root. The skin meets the plate in a tuck faired by
  Taubin passes (`tuck_fair`): a tuck narrower than the 0.17 mm vertices zigzagged across the mesh grid, a
  hatching along the proximal fold in clay. Before that a length-weighted spring relaxation in the nail's plane,
  reprojected each pass (`relax_iters`, `_relax_springs`; a plain Laplacian is separable by axis and never moves a
  vertex sideways toward a step), gives the lips vertices of their own. The thin contact line is drawn by the
  shader from the interpolated distance to the outline, which stays smooth between vertices.
  The skin material shades the plate (`look.nail_on_skin`: a Principled nail mixed over Skin.Foot where
  `Hires.NailA`'s distance s < 0 and `Hires.NailB`'s w < 0, fields written by `method_fields.write_nail_fields`):
  a pink-beige a little lighter than the toe, satin, faint longitudinal streaks and ridges; the lunula a soft milky
  crescent, 2 mm at the centre over the middle 11 mm at strength 0.6, its border softened over 0.9 mm and half
  under the fold (toe 2 0.5 mm at 0.25); the cuticle the fold's skin running 0.35 mm onto the plate with a ragged
  edge; a narrow pink-brown onychodermal band (round 4's was paler than the plate: the white stripe); a faint
  yellow cast. The free edge is the only separate mesh (`free_edge_mesh`): a sliver 0.4 mm thick (toe 2 0.3), from
  0.5 mm behind the bed's uneven end, where it emerges from the skin's plate surface with its thickness feathered
  from nothing, to the cut, its sides thinner and its corners rounded; faint yellow-grey keratin with a trace of
  grime seen through it (`look.dress_free_edge`), 0.7 mm wide on the hallux (was 1.0) and 0.6 on toe 2, its line
  and the bed's end uneven. The hollow under it is shallower (`undercut` 0.3 / 0.25, was 0.45) and faired
  (`front_fair`).
  Three causes found on the way. The plate's root dive behind the proximal fold, smeared forward by the fit's 1.5
  mm smoothing, sloped the first millimetre of the visible plate down into the fold, so the fold seemed to start
  1 mm in and the lunula's colour lay on that slope as a pale strip (round 4's white sliver against the fold);
  with the plate on the skin nothing is hidden at the root, so `root_dive` is 0 (found by striping v, x and the
  lunula's field in the shader). A closed shell's area-weighted normal sums to zero, so `orient_plate` turned the
  first sliver inside out; closed shells are oriented by signed volume (`method_fields.orient_closed`). And the
  fleck under the hallux's free edge (m19, which the critics took for the plate piercing the hyponychium) is a
  fold: 32 pairs of faces turned over at the front of the pulp's ellipsoid, where `macro.pulps` grows the skin
  along normals that turn faster than the growth. `method_fields.untangle` finds faces turned more than 120
  degrees from a neighbour on toes 1-2 after the nails and creases and lays them flat with Laplacian passes over
  them and four rings round them; the fleck is gone in clay and the slit in Cycles.
  At the packet's scale the plates now read as nails set in the toes, with no white crescent, stripe or French
  tip; in clay the plate runs into soft rolled folds with no rim or bevel, the free edge's cut the only edge; a
  thin, fairly even tuck line still outlines the plate in clay.
* **The hallux's depth (m5).** `macro.deepen`, in the hallux's plan frame: the upper part of each section rises 2.2
  mm from 6 mm past the MTP, fully from the IP over the distal phalanx, easing to 45 % at the tip; the lower part
  under the IP and the proximal pad sinks 0.6 mm (never nearer the floor than 0.6); the pulp's ellipsoid 14.2 mm
  across (14.8) and 7.4 tall (6.8). Measured (`report["measure"]`, vertical extent at round 4's stations): 25.1 mm
  deep at the IP (round 4 22.3), 20.7 at the nail root (18.7), 9.8 at the free edge (8.2); widest 28.4 mm, at the
  pulp (29.4); at the nail root 28.3 wide by 20.8 deep, 0.73 (0.64). Jeff's photographs show a round, full big toe,
  so the depth went up rather than the width down; the width fell a little with the narrower pad. In the medial
  clay the dorsum stands higher from the IP to the nose and the pad hangs a little lower under the IP.
* **Toe 2's plantar seam (m4).** Two halves. Colour and texture: part 01's `Foot.Sole` is made on the 5 mm cage, so
  under the curled PIP, where the cage's faces are squeezed into the fold, it stepped from smooth skin to ridged
  sole skin within a fraction of a millimetre; on toes 1-2 it is now also taken from the dense normals and
  diffused over about 2 mm (`method_fields.soften_sole`). Form: sliced, the curled toe's steep distal face met the
  proximal pad at an apex rounded over only 0.3-0.4 mm, the cuff's edge; the closing now blurs 2.6 mm along the
  toe (1.6) over a wider window (`fold_close_win`), its soft-minimum knee 0.3 mm (0.06 creased the crossing), the
  knuckle's sideways growth kept to the upper sides (30 % below, `t2_knuckle_low`) and the waist eased (-1.0, was
  -1.2), and the plantar PIP crease is wider and shallower, just before the bend (1.8 mm past the joint, sigma
  1.1, 0.1 deep: at 0.18 on the bend it notched the apex). At the packet's scale the ridges run on across the
  crease, the flecked patch above it is gone and the outline barely steps (`sbs_pair_hr.plantar_eval.png`); in
  clay a thin, softer line remains at the PIP, and at 1.6x a faint banding shows at the closing window's sides.
* **Colour (m26).** Through the trial's own copy of Skin.Foot (`look.tint_skin`, base colour only) from
  `Hires.Tint` (`method_fields.tint_masks`): capillary redness (#b4645a at up to 30 %) over the dorsal knuckles
  (hallux IP, toe 2 PIP and DIP, the first MTP faintly) and all round the toes' last 6-9 mm; spec 01 §3.4's
  blue-grey #a89a95 at up to 12 % over the hallux's dorsum; the creases 10 % darker. At the packet's scale the
  knuckles and tips are a little pinker and the creases a little darker; the cool cast is faint, as spec 01 asks.
* **Hair (m1, blocking).** `hair.py`: Blender hair curves, `Hires.L.Hair`, 10 hairs of 4-7 mm on a 12 x 10 mm patch
  of the hallux's proximal phalanx and 3 of 3-5 mm on toe 2's, 0.035 mm radius at the root and 0.014 at the tip,
  grown along the skin (leaving the follicle at 30 degrees and lying down within a millimetre), heading distally
  with 12 degrees of random yaw and a random bend of about 25 degrees over each hair (straight strands read as
  scratches in the first render); Principled Hair by melanin (0.82, redness 0.45; spec 16's Hair.Body is planned,
  not built), Cycles curves as 3D tubes; hidden in the clay tier. At the packet's scale the tuft reads as fine
  dark hairs lying along the hallux's proximal phalanx (front and medial views).

No library changes: everything is in `scripts/research/foot_hires/` (the nail's and the tints' shading are the
trial's own nodes added to its copy of Skin.Foot; `bl.py selftest --lib` passes). For the library later: Skin.Foot
to take the nail as a layer read from per-vertex nail fields (s, p, lunula, v, w) with the contact line, the free
edge a mesh of its own, replacing Nail.Plate's refracting shell; the tints as masks part 01 publishes; Hair.Body.

Cost: build 195 s from scratch (34 s with the stage cached, the nails about 9 of it), render 95 s a view at 2048 px
eval.

Still open: from below the free edges' corners show as dark specks past the pulps (m14); at the 89 px/mm zoom the
free edge is still a fairly even band; round 4's other majors (the web's shelf m6, the hallux's plantar sulcus and
pads m7, the stamped knuckle wrinkles m8, the tendons m9, the friction ridges m10, the MTP scar line m11, toe 2's
DIP crease m12, the micro-relief m13, toe 2's distal segment m16); toes 3-5 keep part 01's old nails (declared).

## Whole foot, pass 1 (2026-10-13)

Jeff accepted the method at round 5's level ("Accept for now"); the whole left foot starts its own round count. Run
`fields_w1` (`run.py --method fields --tier eval --tag w1 --views p01.V1f.L,p01.V5f.L,p01.V2.L,p01.V3.L,p01.V4.L,
p01.V8.L,hr.hallux,hr.plantar,hr.lesser`); clay and the first look in `fields_w1b`; round 5 beside it by eye at the
same crops. Packet `renders/research/foot_hires/critic/whole_r1/` (sha 8f060149975d), round 1 of the new series.
New code: `whole.py` (after the stage, so none of it rebuilds the stage cache), `toes.TOES` and the toes 3-5 keys in
`toes.PARAMS`, a `hr.lesser` preset.

* **Toes 3-5 in the method.** Part 01's beds stripped on every toe; `detail.Nail` on all five (spec 01 §3.3's
  sizes, each its own plan and fold heights: toe 3 a short rounded square, toe 4 rolled 9 degrees with a higher
  medial fold, toe 5 6.6 x 6.2, thick, rolled 38 degrees out with a puffy medial fold; no lunula on 3-5); the
  nails start 4-5 mm past the DIP. Pulps, droop, crown, squaring and dorsal fairing as toe 2's; toe 2's plantar
  fold closing on every lesser toe; `macro.toe5_form` (1.4 mm shorter, 0.6 mm stouter on its free sides). The
  2-3, 3-4 and 4-5 webs by one closing (`method_fields.webs_lesser`: one level set, r 1.6, a mask 0.7 mm full and
  1.8 of fade either side of each cleft, low on the toes; the first try, 1.6 + 3 mm, filled the plantar sulcus and
  ended in seams across the toes). Stand-in corn off (a zero `Foot.Corn.L4`); the callus stand-ins softened.
* **Tendons** (`whole.tendons`): the EHL a cord 1.1 mm proud, radius 3.6, along a Catmull-Rom path over the first
  metatarsal, the MTP and the proximal phalanx, fading at the IP; four EDL slips 0.62-0.4 mm, fading into the
  dorsum and over the proximal phalanges; `Foot.Tendon` on the crests. A polyline with a gutter read as piping.
* **Lunula**: a half-moon 3.4 mm at the centre over the middle 60 % of the root, 1.6 mm more of it under the fold
  (`lunula_hide`, so its border meets the fold steeply), duller and paler (`look.NAIL_LOOK`); the plate's root no
  longer paler than its body. Faint on toe 2.
* **Knuckle creases** (`whole.KNUCKLES`): a seeded cluster of 2-6 short Gaussian grooves per joint (IP, MTP, every
  PIP and DIP), varied in place, length, angle, bow and depth, some broken or forked, 0.01-0.03 mm deep so nothing
  dents the profile; the shader draws them from `Foot.Crease`; the recipe's world-Y toe wrinkles are off
  (`look.SKIN_OVERRIDES`). Plantar flexion creases on every toe.
* **Friction ridges** (library, spec 16 §9 2026-10-13): `MG.Skin.Micro` follows an optional phase field,
  `Skin.Foot` reads it from `Foot.Ridges`; `whole.ridge_field` writes a whorl (hallux, toe 3) or a loop (2, 4, 5)
  on each pulp, gentle arcs on the proximal pads and the ball, the amplitude nil at the creases, the region borders
  and a whorl's core. At V4's 0.21 mm a pixel the 0.45 mm ridges aliased into phantom rings over the ball, so the
  trial fades them by the pixel's footprint (`look.ridge_lod`, the camera's mm per pixel from `common.render`).
* **Sheen**: `Hires.Sheen` (the forefoot's dorsum, 0.75 on the toes) adds 0.18 roughness and keeps 25 % of the coat.

What reads at the evaluation scale: toes 3-5 carry nails set in rolled folds, no press-on tips or corn
(`p01.V5f.L_eval.png`, `hr.lesser_eval.png`); the tendons as soft ridges along the toes' lines (`p01.V1f.L_eval.png`,
V5f); the lunula as a soft pale half-moon in `hr.hallux_eval.png` (still a little heavier medially); no stamped
grooves (the new creases are faint at V5f's 15 px/mm); whorls and arcs in `hr.plantar_eval.png`, smooth pads at V4;
a matte dorsum. Still wrong: from below thin dark seams cross the lesser toes' bases and run along their touching
sides (`p01.V4.L_eval.png`; also in clay, not from the web mask: unexplained); `method_fields.untangle` lays flat
10,855 folded face pairs on the toes (round 5: 32), source not found; the hair still reads as scratches (round 5
m8); no veins; the 1-2 web's shelf and the hallux's base sulcus (round 5 m7, m9) untouched.

Cost: stage from scratch 397-408 s (the 1-2 closing 137, the lesser webs 137-143, macro 74), with it cached 46 s;
dress 11 s; eval at 2048 px: V1f 40 s, V5f 63, V2 48, V3 47, V4 19, V8 59, hr.hallux 111, hr.plantar 94, hr.lesser 109.

## Whole foot, pass 2 (2026-10-13)

Critic series `foot_whole` round 1 (`notes/critic/foot_whole_r1/tally.md`): 5 / 5 / 4, four blocking. Run `fields_w2`
(`run.py --method fields --tier eval --tag w2 --save --views` as pass 1's, `--params '{"debug_folds": 1}'`); packet
`renders/research/foot_hires/critic/whole_r2/` (`--previous` whole_r1: 32 claims); every packet image beside round 1's
at the packet's scale in `renders/research/foot_hires/fields_w2/sbs/`. New code in `whole.py` (`toe_contact`, `arch`,
`achilles`, `veins`, `wear_masks`), `macro.harmonic` and `_close_fold`'s new options, `method_fields.FoldCensus`.

* **Folded faces, found at their cause.** `debug_folds` counts flipped neighbour pairs (untangle's test) after every
  step. 71 through the stage, then `webs_lesser` added 10,731: a closing between toes that touch (0.2-0.35 mm apart)
  fills the slit itself, its mask's fade along the toe capped the slit across, and the projection landed both facing
  walls on the one filled surface, where they crumpled (round 1's dark seams along the touching sides; untangle left
  481). It is off; `toe_contact` moves each facing wall toward its neighbour by half the gap less 0.05 mm (fully under
  0.35 mm, fading by 1.4; the new gap a monotone function of the old, so nothing folds), the commissures part 01's.
* **The hairline cut across toes 3 and 4** (m7) was not the webs: in clay it stayed. Sliced (scratch plots of the
  stage's dense skin, `debug_keep`), the curled toes' plantar skin overlaps itself under the PIP in a Z about 1 mm deep
  (part 01's curl on the 5 mm cage; too gradual for the flip census, 66 edges over 60 degrees on toe 3).
  `close_folds` gated its relaxation and closing by height over the lowest skin in its map cell, so the Z's upper
  layers stood as a slit 2 mm deep and 0.3 wide while the skin round them was lowered. Now: the gate is the lower part
  of the toe's own section (`fold_close_under`); the plan relaxation solved to convergence (`macro.harmonic`, conjugate
  gradients over the PIP window and the toe's inner 0.8; 400 Jacobi passes left the Z packed into 0.7 mm, 249 flipped
  pairs; 4000 passes, none, at 43 s a toe), the window from 8 mm behind the joint; the band where the closing gives
  way to the held sides faired (`fold_close_edge_fair`: toe 4's contact corner against toe 3 had stood up as a 2 mm
  knob). Tested offline on the dense skin (1-2 s a toe): toes 2-5 have no flipped pair and no edge over 60 degrees. The
  crease is now a soft fold (`whole.PLANTAR_LESSER`: 0.28 mm, sigma 0.7, doubled 1.3 mm proximal at 0.12).
* **Folded pairs now**: before the repair step 71 (the hallux pulp's 32, known since round 5; nail 5's 39), after it 0
  (round 1: 10,855 and 481).
* **The arcs at the toes' plantar bases** (m12, m28) were the ridges' phase jumping where a toe's own weight crosses
  0.5 while their break sat on the toes' summed weight, which a neighbour lifts there; now on each toe's weight.
* **Veins** (blocking m1, m3; `whole.veins`): curves laid on the skin from anchors ("top" x, y; "med" / "lat" y, z),
  Catmull-Rom, a slow meander, set on the skin's tangent planes; the skin rises along its normals by (1 - (d/r)^2)^3,
  height and radius varying along each vein (slow wobble, faint beading), joined by a p-norm. One vein from the lateral
  marginal (0.2-0.4 mm) across the dorsum as the arch (0.75 mm, about 3 mm across, y -166 to -182) and round up in front
  of the medial malleolus as the great saphenous (0.95 mm, 3.4 mm), fading up the leg by z 205; three tributaries from
  the webs (0.35-0.45 mm) and an oblique branch to the saphenous (0.45). Foot.Vein tints (look.py: the recipe's bump
  off, 38 % of #687a85: spec 01's 18 % of #7d8b86 read as pale welts, a grey of the skin's lightness only desaturating).
* **Achilles** (blocking m2; `whole.achilles`): along the horizontal normal of the ankle's back, the cord raised 1.4 mm
  over 11.5 mm and a hollow either side sunk 3.2 mm (Gaussian, sigma 5, at 15.5 mm from its line), z windows C2-smooth
  (the first hollows, sigma 3.4, read as tram lines on a ledge).
* **Arch** (m5; `whole.arch`): the underside of the midfoot's medial two thirds raised up to 7 mm (eased to nothing
  under the medial border), the lateral column lowered 2.2 mm (never nearer the floor than 0.8), the instep a 2.5 mm
  bell over y, the navicular a 1.2 mm dome; smootherstep profiles (a sin^0.8 envelope creased the sole straight across;
  smoothsteps drew curvature lines in clay). Spec 01's figures, before and after: medial clearance at 45 % L 14.4 /
  14.8 (13), lateral border at 50 % L 3.6 / 2.1 (4), dorsum at 50 / 60 / 70 % L 65.5 / 54.2 / 39.7 and 67.2 / 56.4 /
  39.7 (66 / 56 / 40). The medial view's lift comes from the vault's shaded underside behind the border.
* **Wear and age** (m4, m6, m11, m19, m26, m33, m34; `whole.wear_masks`, `look.WEAR_LOOK`): Foot.Callus.Heel a band by
  the heel's own slope (normal turned 21-72 degrees from the floor, a 15 mm band on this heel pad) over the
  posterior-lateral sector, its edges broken and patchy, kept under 0.72 so the recipe's colour and cracks fade over the
  inner margin; Hires.Wear's pressure redness (ball, heel pad, toe 5's outer side, lateral 5th MTP, medial first MTP and
  hallux IP), dry scaling (a 0.45 mm flake noise, rougher, no coat) and tone (blobs 25-45 mm across, the malleoli
  browner, the plantar margins paler: a few plane waves drew bands across the shin); the recipe's 5.5 mm blotch lower.
* **Toe hair** (m14, m32): 0.052 to 0.016 mm, 7 hairs on the hallux, 2 / 2 / 1 on toes 2-4, none on toe 5, each a
  tightening arc of 18-38 degrees turning the same way, headings within 8 degrees (random sides crossed in X's).

No library changes: the shading is the trial's (`look.py` overrides and its copy of Skin.Foot). For the library later:
Foot.Vein's colour and share as above, Hires.Wear's layers, the heel callus mask by slope.

Cost: stage from scratch 274-287 s (no lesser-web closing; the fold closing 1-2 s a toe), cached 78-82 s with the
forms (8 s) and veins (2 s); dress 10-12 s; eval at 2048 px 632 s: V1f 41, V5f 63, V2 52, V3 55, V4 23, V8 60,
hr.hallux 112, hr.plantar 92, hr.lesser 108. Packet sha d3a749626a19.

Still open: the extensor tendons are still thin, even lines (round 1's m9, m29); the lateral malleolus soft (m25) and
no 5th metatarsal styloid (m10); the nails' French-tip edge and copied lesser nails (m15-m17, m20, m21); the whorls'
seam (m30); toe 5 not tucked under toe 4 (m31, m40); the tone's regional logic is broad, not yet per region (m26).
