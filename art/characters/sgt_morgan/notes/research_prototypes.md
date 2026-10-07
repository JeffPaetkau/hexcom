# Research F: procedural technique prototypes (Blender 4.5.14 LTS, Cycles CPU)

Six throw-away prototypes of the gear techniques the build will lean on, each a headless script
in `scripts/research/` sharing `proto_common.py` (scene reset, HDRI + key light, auto-framed
camera, bmesh/modifier helpers, procedural Cordura / polymer / thread materials, Pointiness+AO
edge-wear mask, bar-tack generator, rounded-rectangle profile, loft). Renders and logs are in
`renders/research/proto_*.{png,log,blend}` (gitignored). Every render was opened and looked at;
the verdicts below are from looking, not from "it ran".

How to run one (all take `[samples] [resx]`; the `--python-expr` line makes Python's prints reach
the log immediately, otherwise they are lost if the process is killed):

```
cd /home/user/sgt_morgan
/usr/local/bin/blender -b \
  --python-expr "import sys; sys.stdout.reconfigure(line_buffering=True)" \
  --python scripts/research/proto_pouch.py -- 64 800 > renders/research/proto_pouch.log 2>&1
```

Second pass (this session): all six scripts re-run strictly sequentially at 64 spp / 800x600
(magwell v1, pouch, lace (failed), sole side only, molle, kneepad, magwell v2, lace v2);
total wall time 12 min 48 s (768 s) for 13 renders. Scripts, renders, logs and .blends:
`scripts/research/proto_{common,molle,pouch,kneepad,sole,lace,magwell,dbg_sheen}.py`,
`renders/research/proto_*.png|log|blend`.

## 0. Two things that went wrong first time, and what they teach

1. **Lost logs.** The first attempt launched four prototypes concurrently at 96 spp / 1024x768;
   each took 3-5 min (`Time: 05:03.92` molle, `03:56` kneepad, `02:59` sole; the pouch was killed
   at 4:32 with 45 s to go) and all four processes were killed after their first render, so the
   `.blend` files, second views and every buffered `print()` (build time, polygon count) were
   lost. Rule for the build: one Blender process at a time on 4 cores (concurrency buys nothing),
   line-buffer stdout, write the report line *before* rendering, save the .blend before rendering.
2. **Sheen bleaches dark fabric.** Every fabric in the first renders came out cream/white
   (`proto_molle.png`, kneepad straps and leg, `proto_dbg_cordura.png`). `proto_dbg_sheen.py`
   (17.5 s render, `proto_dbg_sheen.png`) isolates it: four spheres of albedo (0.115, 0.105,
   0.062); plain Principled = dark olive; plain + `Sheen Weight 0.35` = pale beige; the full
   `cordura_material()` = pale beige; the same with sheen 0 = dark olive. The 4.x Principled
   sheen is a strong micro-flake layer; 0.35 adds roughly +0.2 albedo everywhere, not just at
   grazing angles. **Keep Sheen Weight at 0.05-0.08 on Cordura/webbing, 0.10-0.12 on thread,
   never above 0.15 on anything dark.** Fixed in `proto_common.py`, `proto_molle.py`,
   `proto_lace.py`. The reference's vest Cordura is #463E34 (albedo about 0.07); with the fix
   the olive base lands there.

Also fixed on the way: `camera_fit()` used the horizontal FOV for landscape frames and cropped
the subject (`proto_dbg_sheen.png` is cropped); it now uses the limiting (vertical) FOV.

Three more general lessons from the second pass, detailed in the sections below:
- **Albedo must be calibrated by rendering, not read off the reference.** Under the hangar
  HDRI at 0.6 + a 3 W/m^2 key with AgX Base Contrast, albedo 0.045 leather displays as light
  beige and 0.06 laces as mid-grey. Before shading any part, render the four-sphere swatch
  (`proto_dbg_sheen.py` pattern) under the *evaluation* lighting next to a grey card and pick
  albedos that land on the reference hexes; expect 0.02-0.03 for "black" gear and 0.06-0.08 for
  the olive-brown Cordura.
- **Solidify's offset sign follows the face normal.** After flipping faces to face the camera,
  `offset=+1` grows the thickness towards the camera (buried the lace grommets).
- **Pointiness is per-vertex** and smears across large triangulated faces (boolean hard
  surfaces) and is weak on sparse lofts; use the Bevel-node edge mask on metal and bake masks
  for everything else.

## 1. MOLLE / PALS panel — `proto_molle.py` → `proto_molle.png`, `proto_molle_detail.png`

Build: 200 x 150 mm Cordura panel (bmesh grid 40x30, Solidify 1.5 mm, Bevel 0.6 mm/2),
four 25 mm webbing rows as one dense mesh (190 x 6 quads per row, Solidify 1.3 mm, Bevel
0.5 mm/2) with analytic sag `SAG * sin(pi*t)^0.8` (3.5 mm) between bar-tacks every 38 mm,
bar-tacks (17 zigzag passes, 3 mm wide, 22 mm tall) and a 2.2 mm running stitch 1.8 mm
inside both edges, all as 6-sided thread cylinders r = 0.35 mm in one mesh. Panel weave =
3dtextures nylon normal map, 40 mm tile; webbing weave = procedural wave x wave bump.
Build 3.27 s (the slowest of the six: 896 thread cylinders made one by one in bmesh),
evaluated 27,388 faces / 58,360 tris, of which roughly 21,000 tris are thread. Renders: 5 min
04 s at 96 spp / 1024x768 sharing the CPU with three other renders (first attempt); second pass
64 spp / 800x600 alone: see §7.

Convincing: the sag silhouette and the shadow it casts under each strip, the bar-tack zigzag
reading as thread, the running stitch catching light, the strips' thickness at their ends.
Not convincing: (a) colour (sheen, fixed); (b) the 40 mm normal-map tile shows a 5-8 mm diagonal
twill that reads as corduroy, real 1000D Cordura yarns are 0.5 mm — tile at 12-15 mm, or use the
procedural weave at scale 1000-1400 per metre; (c) the procedural weave on the webbing is a uniform
moiré of fine lines — needs `Distortion` 2-3 and a 2nd lower-frequency wave (herringbone rib,
period 2.5 mm across the strap) layered on it; (d) all strips identical — add per-strip random
sag amplitude (+-20 %), 0.5 mm Z jitter, 0.3-0.5 deg roll; (e) thread sits as bright beads on
top of the cloth — sink the cylinders 0.15 mm into the surface and use the thread colour at
albedo 0.12-0.15 with sheen 0.1; (f) strip edges are knife-sharp — Bevel 0.5 mm with 2 segments
on a 1.3 mm strip is right, but the selvedge should be rounded fully: Bevel width 0.6, segments 3,
`profile 0.5`.
Second pass with sheen 0.06 (`proto_molle.png`, 70.9 s at 64 spp / 800x600): the panel now
reads khaki-olive instead of white, the sag shadows and stitch lines hold up, and the two
remaining faults are plain to see — the coarse 6 mm twill tile on the panel and the wood-grain
streaks on the strips. Still about a stop too light for the reference's #463E34: use albedo
0.07 for the vest Cordura.
Verdict: stitch *geometry* is worth it at this scale (the bar-tacks are what sell PALS); bump
stitches would only be acceptable on rows further than ~0.6 m from the camera.

## 2. Magazine pouch — `proto_pouch.py` → `proto_pouch.png`, `proto_pouch_buckle.png`

Build: body = cube 78 x 42 x 150 mm → Bevel 10 mm / 3 seg → Subsurf 2 (render 3) → Displace
(Clouds, 4 mm) for cloth bulge; lid = L-profile loft (17 sections x 17) with a 4 mm centre dome,
Solidify 3.5 mm, Bevel 1.2 mm, Subsurf 1; elastic band = rounded-rect loft pinched 1.5 %;
two webbing stubs; 25 mm side-release buckle (female: box minus through-slot, two windows and a
bar slot via EXACT booleans, Bevel 1.2 mm / 3, Weighted Normal; male: joined cross-bar, tongue,
two prongs rotated 3 deg and hooks, Bevel 0.8 mm / 2); four bar-tacks (50 thread segments).
Build 0.09 s, evaluated 7,119 faces / 14,544 tris (body with Subsurf 3 is about half of it).
Renders 83.9 s (3/4 view) and 125.6 s (buckle close-up, more adaptive samples on the dark
acetal) at 64 spp / 800x600, wall 210 s including start-up.

Convincing (`proto_pouch.png`, `proto_pouch_buckle.png`): the rounded box with its soft bulge
reads as a stuffed Cordura pouch, the flap dome and its overhang, the elastic band pinched
round the body with bar-tacks at the sides, the bar-tacks themselves (zigzag thread at 0.35 mm
is exactly the right weight at this distance), and above all the female buckle: EXACT booleans
+ Bevel 1.2 mm / 3 + Weighted Normal give crisp, slightly rounded acetal edges with a correct
dark-grey roll-off and a readable through-slot and windows. Not convincing: (a) the procedural
weave (wave x wave, `Distortion 1.5`, Object coordinates) reads as *wood grain* — 5 mm streaks
across body and flap. Drop Distortion to 0.3-0.5, raise the scale to 1400-1800 per metre, and on
any curved body use UV or Box projection; or use the 3dtextures nylon normal map at a 12-15 mm
tile; (b) the colour is khaki-light: albedo 0.115 under this HDRI lands near #6A6248, the
reference pouch bodies are #363028 — use (0.06, 0.052, 0.04); (c) the straps do not pass
through the buckle, they end in a stub glued behind it, and the male half's three prong hooks
poke out of the bottom as blocks — the strap must be a swept strip that threads the bar slot
and folds back with a bar-tack, and the male half needs its prongs visible in the side windows
(model male + female as one assembly with the engagement offset as a parameter); (d) no
edge piping, binding tape on the flap rim, drain grommet or stitched seam lines on the body —
a 2 mm piping tube along the body edges is the single biggest realism gain; (e) the flap floats
2 mm above the body at the hinge; it should be a continuation of the back panel.
Verdict: rounded-box body + lofted L-flap + boolean buckle is the right pipeline; fix the weave
projection and add piping.

## 3. Hard knee-pad cap — `proto_kneepad.py` → `proto_kneepad.png`, `proto_kneepad_side.png`

Build: lofted shell 28 x 36 sections around the knee axis (hex-like outline via a half-angle
function of height, forward bulge +12 mm at mid height, raised 3.5 mm centre ridge with
smoothstep shoulders), boundary vertices flared 1.8 mm for the lip, Solidify 3.5 mm inward,
Bevel 1.2 mm / 3 at 35 deg, Subsurf 1 (render 2); two webbing straps (40 segments round the
back) with ladder-lock buckles (box 10 x 36 x 34 mm minus two 4.5 mm slots, Bevel 1.2 mm / 3,
Weighted Normal); dark fabric cylinder for the leg. Worn-paint shader = Pointiness/AO edge mask
+ stretched-noise scratches (Mapping scale 1,1,14; noise 180; threshold 0.66-0.72) + blotch
chips (noise 40, detail 8, threshold 0.62-0.68), all added and clamped, mixing paint → dark
polymer and roughness 0.62 → 0.38, plus orange-peel bump (noise 900, 0.2 mm).
Build 0.02 s, evaluated 14,240 faces / 28,592 tris (cap with Subsurf 2 is about 11k faces).
Renders: 3 min 56 s at 96 spp / 1024x768 shared (first attempt); second pass alone at
64 spp / 800x600: 43.5 s (3/4) and 23.9 s (side), wall 68 s for the whole script.

Second pass (`proto_kneepad.png`, `proto_kneepad_side.png`, straps and leg now dark with the
sheen fix): the side view is the useful one — the cap's forward bulge, 3.5 mm wall, flared lip
and the gap to the leg read exactly like a moulded cap, and the straps keep a believable 2 mm
edge. The cap colour is still far too pale (see (a) below) and the chips are a handful of dark
blotches rather than the reference's heavily flaked centre.

Convincing (first render, `proto_kneepad.png`): the shell shape and lip, the dome highlight,
hairline scratches, grime blotches, the buckles' slots. Not convincing: (a) paint colour
(0.27, 0.235, 0.165) renders as pale pink-cream — the reference frame is #5F554F-#796C62,
albedo about 0.12-0.18, so halve it; (b) chips have no edge — a flake needs the paint step:
feed the chip mask into a Bump (distance 0.12 mm, strength 1) so every chip border catches
light, and use a Voronoi (F1, smooth 0) or hard-thresholded noise for flake shapes instead of
soft blobs; the reference wants 30-40 % of the centre panel flaked, i.e. threshold 0.52-0.56
in a Voronoi distance field; (c) the lip edge wear is faint because Pointiness is weak on a
lofted shell even after Subsurf 2 — add Bevel segments (3 → 5) or bake an edge mask (see §8);
(d) the ladder-locks read as grey bricks: real ones are 3-4 mm stamped bars — model them as a
rounded-rect frame (loft of two rounded rectangles) 3.5 mm thick with the strap passing
through, not a 10 mm block with slots; (e) the leg cylinder shows vertical stripes because the
procedural weave uses *Object* coordinates — on anything curved use UV or Box projection
(`ShaderNodeTexImage.projection = 'BOX'`, blend 0.2), never Object/Generated;
(f) the straps are flat, untwisted, unstitched and unfolded at the buckle — every strap
needs an end fold (Solidify thickness x2 for 15 mm), a bar-tack and 0.3 deg of twist.

## 4. Lug sole — `proto_sole.py` → `proto_sole_below.png`, `proto_sole_side.png`

Build: right-foot outline from 12 stations (lateral/medial half widths) + 4-point toe and heel
arcs, lofted in four rings (inset 4 mm at the ground, 2 mm at the top) → 21 bisect planes along
the length → per-vertex toe spring (28 mm over the last 32 %) and heel lift (6 mm), Bevel
2.5 mm / 3 at 40 deg; lugs = chamfered boxes 19 x 12 x 7.5 mm (heel 22 x 14 x 8.5) on a
herringbone grid (rows alternate +-28 deg, half-pitch offset), clipped to a 6.5 mm inset outline
by point-in-polygon, tilted to the local sole slope, sunk 1.5 mm into the shell, merged into
one mesh (no boolean needed). Rubber shader: albedo 0.012 + Pointiness/AO wear to 0.16 dust,
large-scale dirt noise, roughness 0.45-0.7, micro grain bump (noise 2500, 0.15 mm).
Build 0.02 s, 26 lugs, evaluated 1,284 faces / 2,620 tris (the cheapest prototype by far; the
whole sole could carry 150 lugs and still be under 10k tris). Renders: below view 2 min 59 s at
96 spp / 1024x768 (shared CPU, first attempt); side view 17.8 s at 64 spp / 800x600 alone.

Convincing (`proto_sole_below.png`): the outline and toe spring read as a boot sole; lugs sit in
the shell without seams; chamfered lug tops catch light the way moulded rubber does.
Not convincing: (a) far too sparse — about 40 lugs with 6-8 mm gaps where a Vibram-type sole is
55-65 % lug by area; use pitch = lug + 4 mm, two lug sizes and a chevron (V) lug in the forefoot
built from two rotated boxes merged; (b) the rubber reads mid-grey: the wear/dust mask covers
every lug face because every lug edge is "pointy" — mask dust with (normal . -Z) so only the
ground-contact faces go grey, keep sides at albedo 0.015-0.02; (c) the outline's 4-point arcs are
visibly faceted at toe and heel — 10-12 points per arc, or Subsurf 1 on the shell after the bevel;
(d) no heel breast, arch cut-out, midsole stripe or side-wall texture (the reference shows a
bluish midsole band #363D4B above a black rand) — two lofts: midsole (lighter, 8 mm) and outsole;
(e) lug tops perfectly flat — add 0.3 mm sipes or a 1 deg random tilt per lug.
Side view (`proto_sole_side.png`): the profile is right — 22 mm slab, 28 mm toe spring over the
last third, slight heel lift, lugs showing as a 7 mm fringe underneath — but the side wall is a
featureless dark band. The reference boot shows, bottom to top, black outsole edge, a bluish
midsole band (#363D4B) and a black rubber rand climbing onto the leather; so the sole must be
two or three stacked lofts with their own bevels and a 0.5 mm groove between them, and the
side wall wants the moulded "tread wraps round the edge" look: extend every outer lug 3 mm
up the side wall. Camera note: a side view of a sole needs an elevation of -5 to +5 deg, the
0.12 used here still shows mostly the top face.

## 5. Boot laces — `proto_lace.py` → `proto_lace.png`, `proto_lace_detail.png`

Build: 5 eyelet pairs at 22 mm pitch on a plane leaning back 0.35 (dy/dz); two Bezier curves
(`bevel_depth 1.9 mm`, `bevel_resolution 6`, `resolution_u 16`, `use_fill_caps`,
`use_uv_as_generated`) threaded through alternating eyelets, dipping 3.5 mm behind the grommet
plane at each eyelet and lifting 6.2 / 2.4 mm at the crossings so one strand rides over the
other; free ends hang to the sides; 20 x 10 torus grommets (metallic 1, roughness 0.35); leather
stays and tongue for context. Braid shader from curve UV: `u = U*170`, `v = V*3`,
`max(pingpong(u+v), pingpong(u-v))^1.6` → Bump (0.4 mm, strength 0.8) and groove darkening.
Build 0.02 s, evaluated 7,688 faces / 15,320 tris (two curves at resolution 16 x bevel 6 =
about 6k; grommets 20 x 10 x 10 = 2k). Renders 19.6 s and 35.4 s at 64 spp / 800x600, wall 56 s.
First run died at build time: `AttributeError: 'Curve' object has no attribute
'use_uv_as_generated'` — the property is gone in 4.5; the curve's bevel mesh always carries a
`UVMap` attribute and `TexCoord.UV` picks it up. Removed the line, re-ran.

Convincing (`proto_lace.png`, `proto_lace_detail.png`): the routing itself — criss-cross, one
strand riding over the other at each crossing, the dip behind each eyelet, the free ends
curling down under their own weight — reads as a laced boot at a glance, and Bezier + round
bevel + fill caps is a one-line way to get it. Not convincing: (a) the braid is rope: 170 repeats
over a 0.45 m lace is a 2.6 mm diamond, a real boot lace braid is 0.6-0.8 mm — use 550-600
repeats, bump distance 0.15 mm, strength 0.5; (b) the laces are mid-grey — albedo 0.06 under
this HDRI/AgX lands at display 0.45; the reference laces are #41362D-#4A473F in the lit
areas, i.e. nearly black: use 0.02-0.03 with roughness 0.75; (c) **the grommets are invisible**:
the stays were Solidified with `offset=+1` after their normals had been flipped to face the
camera, so the 2.8 mm of leather grew *towards* the camera and buried the 0.7 mm-proud rings
(same sign trap in the tongue, and in the MOLLE panel/webbing where it merely makes strips and
panel interpenetrate at the bar-tacks). Rule: with normals facing the viewer, `offset=-1`
puts thickness behind the visible face; assert it from the evaluated bounding box;
(d) the laces have the same radius everywhere — real cord flattens 20-30 % where it bends
over an eyelet: scale `bezier_points[i].radius` 0.8 at eyelet points and 1.0 at crossings.
Verdict: curve laces are the recipe; the braid, colour and the Solidify sign are the fixes.

## 6. AR-15 magwell + trigger guard, anodised — `proto_magwell.py`

Build (v2): hull = receiver box 124 x 28 x 26 mm UNION raked magwell loft (74 mm long at the
mouth, 4 deg rake) UNION rear boss, then DIFFERENCE cutters: magazine slot 62 x 24 mm through
the whole lower (rotated with the rake), a lofted rounded-rect frustum for the flared mouth
(70 x 30 → 62 x 24 over 9 mm), two 1 mm side pockets (rounded rect 44 x 22, r 6), the trigger-
guard ear slot; then Bevel 0.8 mm / 3 at 30 deg clamped + Weighted Normal. Trigger guard =
rounded-rect bar 6.5 x 4.5 mm swept along an 8-point polyline (loft, Subsurf 1), roll pins,
pivot/takedown pin heads (dia 8 mm), mag-release fence (box minus box, Bevel 0.7 mm / 3) and
button, polymer grip stub. Shader: anodised = Principled metallic 0.75, roughness 0.5, base
(0.022, 0.023, 0.025), bead-blast bump (noise 4000, 0.05 mm, strength 0.2), low-frequency
"thinning" towards grey 0.09, Pointiness/AO edge mask → bare aluminium (0.72, metallic 1,
roughness 0.32).
Build 0.01 s (v2), evaluated 2,399 faces / 5,246 tris, hull alone 993 faces / 2,194 tris.
Renders 29.1 s (right 3/4) and 45.4 s (mouth from below) at 64 spp / 800x600, wall 75 s.

**v1 failure (kept as `proto_magwell_v1_joined.png`, `_v1_joined.log`):** the hull was made by
`bpy.ops.object.join()` of three overlapping closed boxes and *then* cut. The EXACT boolean on
that multi-shell operand inverted: the magazine cutter and the flare frustum came out as *solid*
anodised blocks sticking out of the receiver, the pockets became a bright full-length band, and
Pointiness went to 1 on the doubled faces so the whole side rendered as bare metal. Build time
0.05 s, 574 evaluated faces (the cut edges simply were not there), render 54.7 s at 64 spp/800px.
Lesson: **a boolean operand must be one manifold solid.** Union the primitives with Boolean
UNION modifiers (EXACT) first, or build the hull as a single loft; never join overlapping shells
and cut. The pouch buckle and kneepad ladder-locks, which cut single boxes, were fine.

v2 (`proto_magwell.png`, `proto_magwell_mouth.png`): the geometry pipeline now works — one
manifold hull, the magazine slot and flared mouth cut cleanly, the 1 mm side pocket reads as a
machined recess with a rounded floor, the 0.8 mm / 3 bevel puts a crisp bright line on every
edge, pin heads, fence and button read as separate dark anodised parts, and the swept rounded
bar is a believable trigger guard. Convincing: all of that, plus the bead-blast grain and the
polymer grip's roll-off. Not convincing: **the whole side face renders as bare aluminium with
diagonal creases running from the pocket corners to the hull corners.** That is Pointiness
smearing: it is a per-*vertex* attribute, the EXACT boolean leaves the side as one big face
with a hole that gets triangulated into long slivers, and the high pointiness of the pocket
rim vertices is interpolated across the slivers to the whole face. (The pocket floor is light
for the same reason.) Pointiness is therefore unusable on boolean hard-surface meshes unless
the flat faces are densely subdivided. The fix for metal: a shading-point edge mask from the
Cycles **Bevel node** — `ShaderNodeBevel(radius 0.8 mm, samples 4)` → `Vector Math DOT` with
`Geometry.Normal` → `1 - dot` → Map Range 0.0-0.08 → noise break-up; it has no mesh
dependency, costs about 10 % render time and gives the thin bright edges the reference lower
shows (#686463 on #403C39). Also still missing: roll marks, the mag-catch slot, bolt catch and
selector on the left, the tan accent plate; the mouth flare wants 2 mm more depth. The
anodised base (metallic 0.75, roughness 0.5, 0.022 grey) itself is right where it is not
overwritten by the mask — compare the dark top face and pins.
Verdict: UNION → DIFFERENCE → Bevel → Weighted Normal is the hard-surface recipe; wear masks
on metal come from the Bevel node or a bake, never from Pointiness.

## 7. Numbers at a glance

| Prototype | Build (s) | Evaluated faces / tris | Render, 64 spp 800x600, alone | Render, 96 spp 1024x768, 4 concurrent |
|---|---|---|---|---|
| MOLLE panel (4 rows, 896 thread segments) | 3.27 | 27,388 / 58,360 | 70.9 s + 121.0 s (detail) | 5 min 04 s |
| Mag pouch + buckle | 0.09 | 7,119 / 14,544 | 83.9 s + 125.6 s (buckle) | killed at 4 min 32 s |
| Knee-pad cap + straps + buckles | 0.02 | 14,240 / 28,592 | 43.5 s + 23.9 s (side) | 3 min 56 s |
| Lug sole (26 lugs) | 0.02 | 1,284 / 2,620 | 17.8 s (side) | 2 min 59 s (below) |
| Laces + grommets | 0.02 | 7,688 / 15,320 | 19.6 s + 35.4 s (detail) | — |
| Magwell v1 (joined shells, broken) | 0.05 | 1,980 / 4,296 (hull 574) | 54.7 s | — |
| Magwell v2 (union hull) | 0.01 | 2,399 / 5,246 (hull 993) | 29.1 s + 45.4 s (mouth) | — |

Blender start-up (MPFB enabled) plus scene build is about 1 s per script — wall time is
render time. Build time is negligible
everywhere except thread generation (896 cylinders in 3.3 s; a full plate carrier with ~40 PALS
columns x 6 rows would be ~15,000 segments, about 60 s and 400k tris — do it once per part and
cache the .blend, and give stitches their own object so they can be hidden for form checks).

Cycles CPU, 4 cores, 64 spp adaptive (threshold 0.02), OIDN denoise, 800x600: 45-60 s per
view when nothing else runs; 96 spp / 1024x768 with four renders sharing the cores: 3-5 min
each. Workbench form checks stay the fast loop (about 5 s); use Cycles only to judge shaders.

## 8. Recommended standard recipes for the build

All in metres; thickness and widths from the specs in mm. Put these in `scripts/lib/` as
`gear_webbing.py`, `gear_hardware.py`, `mat_fabric.py`, `mat_hard.py` and reuse them unchanged
across parts.

**Webbing strips (25 / 38 mm).** Dense strip mesh along the path (segment every 1 mm, 6 quads
across) so sag/curvature are real geometry; Solidify 1.3 mm (`offset +1`, even thickness, rim on);
Bevel 0.6 mm, 3 segments, profile 0.5, angle 60 deg; shade smooth. Random per-strip sag
amplitude (+-20 %), 0.5 mm Z jitter, 0.3-0.5 deg roll. Ends folded under (15 mm) and bar-tacked.
Material `cordura_material(color, weave_scale 1000, rough 0.7, sheen 0.06)` with the weave
driven by UV (`u` along the strap, scale so one herringbone rib = 2.5 mm) plus wave distortion 2.
Fabric weave by bump, never geometry.

**PALS rows.** Generator takes a surface (panel mesh or pouch front), row pitch 38 mm, column
pitch 38 mm, sag 3-4 mm, and emits strips + bar-tacks + running stitches as *three* objects
(`<Part>.Webbing`, `<Part>.Stitches`, `<Part>.Bartacks`) so the stitches can be dropped for
LOD. Stitches as 6-sided thread cylinders r 0.3-0.35 mm sunk 0.15 mm into the cloth, 2.2 mm
stitch / 0.8 mm gap, thread albedo 0.12-0.15, roughness 0.6, sheen 0.1. Bar-tack: 3 mm wide,
0.9 x strip height, 1.3 mm pitch zigzag. Use geometry for stitches within ~0.6 m of the camera
(the whole torso in the reference framing); bump-only stitches elsewhere.

**Pouch bodies and flaps.** Body: box → Bevel 8-10 mm / 3 seg → Subsurf 2 (render 3) →
Displace (Clouds 60 mm, 3-4 mm) → Lattice or second Displace for the band squeeze; keep the
corner bevel below the Subsurf so the box keeps its crease (a real Cordura box has a sewn edge
with piping — add a 2 mm piping tube along the body edges as a curve with bevel 1 mm, it is the
single biggest realism gain on pouches). Flap: L-profile loft (not a bent box) with 3-5 mm
centre dome, Solidify 3.5 mm, Bevel 1.2 mm / 2, Subsurf 1; edge binding tape as a 12 mm strip
along the flap rim. Elastic band: rounded-rect loft pinched 1.5 %, Solidify 2.2 mm, ribbed bump
across (wave bands, 1 mm period), albedo 0.05, roughness 0.85, no wear. Drain grommet at the
bottom. Materials: body Cordura olive-brown (0.07, 0.06, 0.045) matched to #463E34; dust on
flap tops via (normal . +Z) mask; grime at the bottom via a Z-gradient.

**Buckles and ladder-locks.** Acetal side-release 25 mm: female = box 33.5 x 8.5 x 30 mm
minus through-slot, two side windows and a bar slot (EXACT booleans on a *single* manifold box),
Bevel 1.0-1.2 mm / 3 at 30 deg, Weighted Normal, keep sharp. Male = cross-bar + tongue + two
prongs (3 deg splay) + hooks joined, Bevel 0.8 mm / 2. Ladder-lock / tri-glide: a 3.5 mm thick
rounded-rect frame (loft two rounded rectangles, Solidify 3.5 mm, Bevel 0.8 mm / 3) with the
strap actually passing through, plus a centre bar; gunmetal version metallic 1, roughness 0.45,
colour 0.1 with edge wear to 0.6. `polymer_material()` (albedo 0.02, roughness 0.4, micro grain
noise 3000 at 0.1 mm, pointiness mid 0.66) is right as it stands.

**Moulded polymer caps with worn paint.** Shell: parametric loft (sections x angles, 28 x 36 is
enough) → boundary flare for the lip → Solidify 3.5 mm → Bevel 1.2 mm / 5 seg at 35 deg →
Subsurf 1 (render 2). Cut-outs (slots, D-holes) with EXACT boolean *before* the bevel. Paint:
tan albedo 0.12-0.18 (#5F554F-#796C62), roughness 0.6; chips = Voronoi F1 distance thresholded
hard (coverage 30-40 % on the centre panel, 5 % on the frame) + hairline scratches (noise with
anisotropic Mapping 1,1,14, threshold 0.66-0.72) + Pointiness/AO edge mask; chip mask → Bump
0.12 mm so every flake has a lit edge; under the chips dark polymer 0.028, roughness 0.38;
dust (normal . +Z) 0.5 mm noise; orange-peel bump noise 900 at 0.2 mm. Bake the combined mask
to a 2k image per cap once the shape is final (Pointiness is Cycles-only and mesh-density
dependent) so EEVEE/Workbench and glTF see the same wear.

**Lug soles.** Outline from stations (12+) with 10-12 points per arc; loft 4 rings with inset,
bisect every 14 mm, apply toe spring / heel lift per vertex; Bevel 2.5 mm / 3, Subsurf 1. Two
lofts: midsole (8 mm, dark blue-grey 0.03) and outsole. Lugs as merged chamfered boxes (no
boolean): forefoot chevrons from two 19 x 9 mm boxes at +-30 deg, heel blocks 22 x 14 mm,
height 7-8 mm, bottom bevel 2.2 mm / 2, pitch = lug + 4 mm, 55-65 % coverage, clipped to a
6 mm inset outline, tilted to the local slope, sunk 1.5 mm, 1 deg random tilt. Rubber: albedo
0.012-0.02, roughness 0.5-0.7 noise, micro grain noise 2500 at 0.15 mm; dust/scuff only where
(normal . -Z) > 0.7 and on the toe/heel edge via Pointiness; side walls stay black.

**Laces.** Bezier curve per lace end, `bevel_depth` = lace radius (1.9 mm for round 4 mm cord),
`bevel_resolution 6`, `resolution_u 16`, fill caps, `use_uv_as_generated`; control points at
each eyelet 3.5 mm behind the grommet plane, crossing midpoints lifted alternately (over 6 mm,
under 2.4 mm), free ends with 3 extra points and gravity sag; aglets as 2 mm cylinders.
Braid = diamond pattern from curve UV (`max(pingpong(u+v), pingpong(u-v))^1.6`, one repeat
per 0.7 mm of lace length, 3 around) → Bump 0.15 mm, strength 0.5, and groove darkening;
albedo 0.02-0.03, roughness 0.75, sheen 0.1; point radius 0.8 at eyelets, 1.0 at crossings.
Convert to mesh only for export. Grommets: 20 x 10 torus, r 3.3 / 1.2 mm, 0.7 mm proud of the
*outer* leather surface (check the Solidify direction), metallic, roughness 0.35, dark gunmetal
0.1 with worn rim.

**Anodised hard-surface parts (receivers, rails, buckles' metal, pin heads).** Build each solid
as one manifold hull (loft or box, UNION further primitives with EXACT boolean modifiers),
then DIFFERENCE cutters, then Bevel 0.6-0.8 mm / 3 seg at 30 deg clamped + harden normals,
then Weighted Normal; keep the cutters as hidden objects in a `<Part>.Cutters` collection so
the stack stays editable. Shader: Principled metallic 0.75, roughness 0.5, base
(0.022, 0.023, 0.025) (reference #403C39 after discounting light), bead-blast bump noise 4000 at
0.05 mm strength 0.2, low-frequency thinning to grey 0.09 (noise 35, 0-35 %), Pointiness/AO edge
mask (mid 0.60, width 0.10, AO 3 mm, noise 600) → bare aluminium (0.72, metallic 1, roughness
0.32); roll marks and the tan accent plates as decals (Shrinkwrap'd planes, 0.3 mm offset).

**Wear masks in general.** Pointiness + AO + noise works in Cycles and only on dense bevelled
geometry; it goes to 1 on doubled faces, smears across the long triangles a boolean leaves on
flat faces (magwell v2) and is invisible on sparse lofts (knee-pad lip). Metal and polymer
hard-surface parts: use the Bevel-node mask (`ShaderNodeBevel` radius 0.8 mm, 4 samples, dotted
with the true normal) instead. For the build:
finish the geometry, then bake `Pointiness x AO x noise` to a per-part 2k mask image
(`bpy.ops.object.bake(type='EMIT')` with the mask wired to emission) and drive the wear from the
image — identical in Cycles, EEVEE and the glTF export, and paintable later on Jeff's machine.
