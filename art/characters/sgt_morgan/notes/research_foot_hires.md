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
