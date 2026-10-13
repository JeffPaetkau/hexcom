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
