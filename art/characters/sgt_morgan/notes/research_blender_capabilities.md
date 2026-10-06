# Research C: headless Blender capability tests (Blender 4.5.14 LTS, CPU only)

Date: 2026-10-06. Machine: Intel Xeon @ 2.10 GHz, 4 cores, 15 GB RAM, no GPU, ~19 GB free disk.
Blender 4.5.14 LTS (hash 62c1db4208e8) at `/usr/local/bin/blender`; the MPFB extension is installed
and initialises on every headless start (adds ~2 s). All tests run as
`cd /home/user/sgt_morgan && blender -b --python scripts/research/test_XX_*.py [-- args] > renders/research/tXX_log.txt 2>&1`;
renders, logs and .blend files are in `renders/research/`. Every render was opened and looked at.

Timing caveat. The first pass (15:26–15:38) ran while other Blender jobs shared the 4 cores (load
average 5–10), so those numbers (t01, t04, t05, t07) are pessimistic by roughly 1.5–2×. The second
pass (22:11–22:40, t02, t03, t06, t08, t10 and a t01 rerun) ran one test at a time, but other
researchers' Blender jobs kept appearing: t02 and t06 ran at load 0.2–2.5 (clean), t03 and t08 shared
the box with one 2-thread job (load 4.5–8). `/usr/bin/time` does not exist on this box; wall-clock
comes from `time.time()` inside the scripts and `date +%s.%N` around the whole process.

## Summary table

| # | Test | Works headless | Wall-clock | Notes |
|---|------|----------------|-----------|-------|
| 1 | Cycles CPU benchmark, 1920×1080, OIDN | yes | 32 spp: 67.9 / 71.6 / 91.1 s (all with other jobs running) | 128 spp interrupted at sample 113 after 8 min 56 s; no idle run obtained |
| 2 | Cloth: tube round cylinder, 60 frames | yes | bake 10.4 s (3136 verts) + render 5.3 s | `ptcache.bake_all` works headless; `modifier_apply` works with `temp_override` |
| 2 | Cloth: sewing-spring panels, 60 frames | yes | 21 s stepping (3534 verts) + render 5.1 s | panels closed round the thigh; pinned rows cannot sew |
| 3 | Hair: particle 2000 × 20 children; Curves object from Python; convert; GN on Curves | yes (all four) | 40 k strands render 239.6 s; 3 k curves 84.9 s (800², 64 spp, shared) | strand radius was 50× too thick in the test; shader and clumping fine |
| 4 | Cycles adaptive subdivision + true displacement | yes | 229 s, 1280×720, 64 spp (loaded) | needs EXPERIMENTAL; silhouette visibly displaced |
| 5 | Geometry Nodes: webbing strip, MOLLE grid; glTF export | yes | render 87.5 s, 1280×720, 48 spp (loaded); glTF 0.1 s | 512 / 1961 faces evaluated |
| 6 | Modifier-stack clothing: shrinkwrap → solidify → bevel → subsurf → displace ×2, then apply | yes | render 20.3 s (800², 48 spp, idle); apply 6 modifiers 0.37 s | 53 k faces; dangling-modifier gotcha |
| 7 | Rig + auto weights + shape key + glTF/FBX export + reimport | yes | GLB 0.32 s, FBX 0.08 s, reimport 0.2 s, render 50 s (640×800, 32 spp, loaded) | `mode_set` gotcha, see §7 |
| 8 | Skin: Random Walk (Skin) SSS sphere closeup | yes | SSS 136.2 s vs no-SSS 37.6 s (640², 48 spp, shared); first attempt 427.6 / 163.3 s at 800², 96 spp | first attempt blown out (lights 10× too strong, f/4 DOF); look enum gotcha |
| 10 | Probes: hair node assets append, GN named attribute after apply, `object.bake` | yes (all three) | 2.1 s total; bake 512² 0.4 s | 27 hair node groups available |

Sections below give what was run, the snippet that worked, timings, and what failed.

## 1. Cycles CPU benchmark (`test_01_cycles_bench.py`, log `t01_log.txt`, render `t01_cycles_32spp.png`)

Scene: UV sphere (64×32) + Subdivision level 3, Principled BSDF, floor, three area lights, 1920×1080,
OIDN denoise with albedo+normal passes, adaptive sampling OFF (fixed spp for fair timing),
`threads_mode = 'AUTO'` (4 threads). Command:
`blender -b --python scripts/research/test_01_cycles_bench.py -- 32,128,512 2`.

* 32 spp: 67.88 s and 71.61 s (two runs at 15:28, load average 5–10). Peak memory 138 MB. A third
  single run at 22:35 (`-- 32 1`, log `t01_clean_log.txt`) meant to be the idle measurement took
  91.14 s because another researcher's 2-thread Blender job was running (load 8); an idle figure for
  this exact scene was never obtained, so the idle throughput below comes from t06.
* 128 spp: the run was killed by the API-limit interruption at sample 113/128 after 8 min 56 s. Early
  in that render 16 samples took 26 s (≈1.6 s/sample, consistent with the 32 spp runs: ≈2.1 s/sample
  including denoise and startup), later 16 samples took 3 min 16 s because the other jobs started.
  512 spp never ran.
* The render looks right: smooth sphere, three soft highlights, clean floor shadow, no fireflies at
  32 spp with OIDN.

Snippet that mattered:

```python
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
scene.cycles.use_adaptive_sampling = False       # fixed spp for benchmarking only; turn ON for production
bpy.ops.render.render(write_still=True)          # works in background mode without any context override
```

Scaling rule of thumb for this machine (see §Recommendations): 1920×1080 × 32 spp = 66 MP·spp
took 68–91 s shared (≈ 0.7–1.0 MP·spp/s); the one idle data point (t06, 0.64 MP × 48 spp in 20.3 s)
gives ≈ 1.5 MP·spp/s. Cost is close to linear in pixel count × spp for simple surfaces, plus 1–3 s
fixed per render for startup, BVH and OIDN, and multiplied by the SSS / hair / displacement factors in
§Recommendations.

## 2. Cloth simulation (`test_02_cloth.py`, log `t02_log.txt`, renders `t02_cloth_tube.png`, `t02_cloth_sewing.png`, blends `t02_cloth_*.blend`)

Command: `blender -b --python scripts/research/test_02_cloth.py -- AB`. Whole process (both variants,
two bakes, two renders at 640×720 / 48 spp): 42.7 s wall-clock.

Variant A, "trouser leg": open tube r = 115 mm, 64 × 48 quads (3136 verts, ~7 mm quads), top ring
pinned (`vertex_group_mass`), round a 48-vertex cylinder "thigh" r = 80 mm with a Collision
modifier (`thickness_outer = 3 mm`). Cloth: quality 8, mass 0.3, tension/compression 15, shear 5,
bending 0.5, air damping 1, self-collision ON (distance 4 mm, quality 4).

* `bpy.ops.ptcache.bake_all(bake=True)` WORKS headless inside
  `bpy.context.temp_override(scene=sc, point_cache=None)`: 60 frames in 10.4 s. After it, stepping
  frames is free (0.0 s) because the cache is filled.
* `bpy.ops.object.modifier_apply(modifier="Cloth")` WORKS at frame 60 inside
  `temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob])`;
  applied mesh 3136 verts, z range −22 mm … 520 mm (no stretching, pinned ring stayed put).
  Fallback that also works without any operator:
  `bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)`.
* Render looked at: a smooth stiff cylinder of fabric hanging from the pinned ring, hiding the thigh.
  It is a correct simulation but a useless drape: a uniform tube pinned at the top with nothing to
  push it develops no folds. The key light was also far too hot (fabric rendered near white). For the
  trousers the hem must land on something (collar/boot) and the tube must be longer than the leg,
  which is what `spec/09_combat_trousers.md` plans.

Variant B, sewing springs: two 30 × 56 panels (300 × 560 mm, ~10 mm quads, 3534 verts) at
y = ±160 mm, loose edges joining the side borders row by row (114 sewing edges),
`use_sewing_springs = True, sewing_force_max = 5`, same cloth and collision settings, top rows pinned.

* 60 frames by `scene.frame_set(f)` stepping: 20.7 s (no bake operator needed; stepping fills the
  point cache as it goes). Same `modifier_apply` route worked.
* Render looked at: the two panels wrapped round the thigh and closed into a tube; the cylinder shows
  at the bottom in skin colour; the two pinned top rows stay flat at ±160 mm as "wings", which is
  exactly the 0.32 m `gap max` in the log (mean gap 31 mm is dominated by those 2 pinned pairs out of
  114). Lesson: never pin the vertices that carry sewing edges; pin a waistband ring instead, or pin
  after the seam has closed.

Cost model from these two runs: about 0.15–0.35 s per frame for 3–3.5 k verts with self-collision at
quality 8 (sewing is slower because the panels fly together fast and collide). Scaling is roughly
linear in vertex count (collision quality dominates), so the trousers plan in `spec/09` (13.7 k verts
× 100 frames) is ≈ 1–2 min on this box, not the 2–4 min feared, as long as self-collision distance
stays ≥ 3 mm.

Gotcha worth recording: `scene.frame_set()` from Python is the most reliable way to run a sim headless
and it is deterministic across runs on the same build; `ptcache.bake_all` also works but needs the
`scene` override and bakes every cache in the scene.

## 3. Hair (`test_03_hair.py`, log `t03_log.txt`, renders `t03_hair_particles.png`, `t03_hair_curves.png`, `t03_hair.blend`)

Command: `blender -b --python scripts/research/test_03_hair.py`. Whole process 325.9 s (another
researcher's Blender job, `ai_render_obj.py`, overlapped the first render; load average 4.5–6).
Scene: 100 mm UV sphere "scalp", Principled Hair BSDF (Chiang model, melanin 0.9), Cycles curves
`sc.cycles_curves.shape = "THICK"`, `subdivisions = 2`, 800 × 800, 64 spp, OIDN, 85 mm lens closeup.

* (3a) Legacy particle hair, built entirely from Python (no operator): 2000 parents, 20 interpolated
  children each → 40 000 strands evaluated (`len(ev.particle_systems[0].child_particles)`), length
  30 mm, 5 segments, clump 0.6, roughness; density restricted to the upper hemisphere by
  `psys.vertex_group_density = "HairDensity"`; material slot by `ps.material = 2` (1-based). Setup
  0.3 s. Render 239.6 s. Looked at: a dense, clumped dark-brown pelt covering the sphere, strands far
  too THICK (`radius_scale = 0.005` means 5 mm root diameter; real hair wants 0.05–0.1 mm, i.e.
  `radius_scale ≈ 0.0001` with `root_radius 1.0, tip_radius 0.2`) and too dark for the lights, but
  clumping, tip tapering and the melanin shader all clearly work headless.
* (3b) New Curves hair object built from Python: `hc = bpy.data.hair_curves.new(); hc.add_curves([6]*3000)`;
  `hc.points.foreach_set("position", flat_list)`; `hc.surface = scalp`; per-point radius through
  `hc.attributes.new("radius", "FLOAT", "POINT")` + `foreach_set("value", ...)`; 3000 curves / 18 000
  points built in 0.03 s. Render 84.9 s. Looked at: sparse copper bristles with the droop and the
  root-to-tip taper exactly as programmed (radius attribute is honoured by Cycles), so Curves objects
  render with no extra setup.
* (3c) `bpy.ops.curves.convert_from_particle_system()` works headless inside
  `temp_override(object=scalp, active_object=scalp, selected_objects=[scalp])` and produced a Curves
  object `HairPS` with 40 000 curves (children included).
* (3d) A Geometry Nodes modifier on a Curves object built from Python (Set Position with a noise
  offset scaled by Spline Parameter) evaluates headless: 18 000 points.

Cost: the 40 000-strand particle render took ≈ 2.8× the 3000-curve render in the same scene, so hair
cost is roughly proportional to strand count × pixel coverage; a 15 mm buzz cut of ~60–100 k short
strands in a head closeup should land in the 2–5 min range at 64 spp 800 px if nothing else is in
frame, and is negligible in full-body evaluation renders where the head is ~120 px tall.

## 4. Adaptive subdivision and true displacement (`test_04_displacement.py`, log `t04_log.txt`, render `t04_disp_adaptive.png`)

2 × 2 m plane, Subdivision (SIMPLE, 2 levels) as the last modifier, Noise × Voronoi height →
Displacement node (scale 0.12 m) → Material Output displacement, 1280 × 720, 64 spp, OIDN.

* Works headless. Render 229 s under load (render only; the scene has one plane and two lights, so
  this is almost all dicing + displacement shading). Memory stayed under 80 MB.
* Render looked at: the plane has become a crumpled sheet; the silhouette at the far edges is
  visibly broken by real geometry, not bump shading, so true displacement is confirmed. (Material
  colour washed out by a 1500 W key, irrelevant.)
* The comparison renders (fixed subsurf level 6; bump-only) were lost to the interruption; not rerun
  because the yes/no question is answered.

Snippet that worked (4.x API):

```python
sc.cycles.feature_set = "EXPERIMENTAL"          # adaptive subdivision is still experimental in 4.5
sc.cycles.dicing_rate = 1.0                      # render dicing rate, px per micro-polygon edge
sc.cycles.max_subdivisions = 10
sub = ob.modifiers.new("Subd", "SUBSURF"); sub.subdivision_type = "SIMPLE"; sub.levels = 2  # must be LAST
ob.cycles.use_adaptive_subdivision = True        # per object
ob.cycles.dicing_rate = 1.0
mat.displacement_method = "DISPLACEMENT"         # on Material since 4.1 ('BUMP'|'DISPLACEMENT'|'BOTH'); mat.cycles.* no longer exists
```

Verdict: usable but expensive. Even this trivial scene cost ~4 min at 720p. Use adaptive
displacement only on the few hero surfaces that need a broken silhouette (boot sole lugs seen edge-on,
knitted gaiter cuff) with `dicing_rate` 2–4 px, and use the Displace modifier or bump everywhere else.

## 5. Geometry Nodes (`test_05_geonodes.py`, log `t05_log.txt`, render `t05_geonodes.png`, `t05_geonodes.blend`, `t05_geonodes.glb`)

* (5a) webbing strip from a Bezier circle: Resample Curve (128) → Curve Primitive Quadrilateral
  (RECTANGLE 50 × 3.5 mm) → Curve to Mesh (fill caps): 512 verts / 512 faces evaluated.
* (5b) MOLLE panel: Mesh Grid → Instance on Points of an Object Info (ORIGINAL space) loop object
  → Translate Instances → Realize → Join: 1924 verts / 1961 faces, 20 loops.
* Group inputs are set on the modifier by socket identifier, not by name:
  `for item in ng.interface.items_tree: if item.item_type == "SOCKET" and item.in_out == "INPUT": mod[item.identifier] = value`
  (identifiers look like `Socket_2`). `ng.interface.new_socket(name, in_out=, socket_type=)` builds
  the interface; node tree creation is `bpy.data.node_groups.new(name, "GeometryNodeTree")`.
* Render 1280 × 720 at 48 spp: 87.5 s under load; looked at: clean bevelled webbing loop and a 5 × 4
  grid of stitched-down MOLLE loops, correct.
* `bpy.ops.export_scene.gltf(filepath, export_format="GLB", export_apply=True, use_visible=True)`
  evaluates the GN modifiers and wrote 314 KB in 0.1 s.

## 6. Modifier-stack clothing (`test_06_modstack.py`, log `t06_log.txt`, render `t06_modstack.png`, `t06_modstack.blend`)

Command: `blender -b --python scripts/research/test_06_modstack.py`. Whole process 22.2 s on an
otherwise idle box (load 0.2 at start). First attempt (15:32) never ran because the runner used
`/usr/bin/time`, which does not exist here; second attempt (22:16) rendered but crashed in the apply
loop, see gotcha below; third attempt (22:25) complete.

Body = UV sphere 64 × 48 scaled to 100 × 80 × 240 mm. A z-band of 1344 faces is copied out with
bmesh into a new "Sleeve" mesh, then the stack Shrinkwrap (NEAREST_SURFACEPOINT, offset 12 mm) →
Solidify (4 mm, even offset, rim) → Bevel (1.5 mm, 2 segments, angle 40°) → Subdivision (render 3)
→ Displace "Wrinkle" (CLOUDS texture, Voronoi F2−F1 basis, noise 30 mm, strength 4 mm, along normals)
→ Displace "Folds" (WOOD band-noise, strength 3 mm). Stack set-up 0.11 s; evaluated 53 248 verts /
53 248 faces (`ob.evaluated_get(dg).to_mesh()`).

* Render 800 × 800, 48 spp, OIDN: 20.3 s. Looked at: the sleeve fills the frame; a crumpled,
  parchment-like relief of random wrinkles with a slightly lumpy silhouette, so both Displace passes
  and the subdivision work. The 250 W key light at 0.35 m blew the fabric out to white (a recurring
  mistake in these tests: light energies tuned for metre-scale scenes used on 100 mm objects; scale
  area-light power with the square of the distance, ~10–25 W at 0.3–0.5 m).
* Applying the whole stack with `bpy.ops.object.modifier_apply(modifier=name)` inside
  `temp_override(object=ob, active_object=ob, selected_objects=[ob])` works headless for all six
  modifiers in 0.37 s; final mesh 53 248 verts, identical to the evaluated count.
* GOTCHA: after `modifier_apply` the Python `Modifier` reference you iterated over is a dangling RNA
  pointer; `mod.name` then returns garbage bytes and raises `UnicodeDecodeError: 'utf-8' codec can't
  decode byte 0xd3`. Capture `[m.name for m in ob.modifiers]` first and apply by name.

Verdict: the modifier-stack route is instant and fully controllable. Legacy `bpy.data.textures`
(CLOUDS, WOOD, VORONOI, MUSGRAVE…) still exist in 4.5 and drive the Displace modifier, which is the
simplest way to get procedural wrinkles without Geometry Nodes; the Displace modifier does not read
shader-node textures, so for image-driven wrinkles bake to an image and use `texture_coords = "UV"`.

## 7. Rigging, shape keys, export and reimport (`test_07_export.py`, log `t07_log.txt`, render `t07_export_reimport.png`, files `assets/blender_caps/t07_limb.*`)

Bent-tube limb mesh, Smart UV Project, two numpy-generated textures packed into the .blend, two shape
keys (Basis, Bulge), 2-bone armature, automatic weights, a 24-frame action, GLB / glTF-separate / FBX
export, GLB reimport into a fresh scene, render.

* THE context gotcha of this whole research: `bpy.ops.object.mode_set()` IGNORES
  `temp_override(object=rig, active_object=rig, selected_objects=[rig])` in background mode. It
  returns `{'FINISHED'}` and silently puts the view-layer's real active object (the limb) into Edit
  mode, leaving the armature in Object mode (log: `rig.mode=OBJECT limb.mode=EDIT`). The working way
  is the real selection state:

```python
def set_active(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
set_active(rig); bpy.ops.object.mode_set(mode="EDIT")       # now edit_bones are available
...
bpy.ops.object.mode_set(mode="OBJECT")
limb.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")             # works headless; vgroups 'upper','lower' created
```

  By contrast `modifier_apply`, `ptcache.bake_all`, `curves.convert_from_particle_system` and the
  exporters do honour `temp_override`. Rule for the build: use `temp_override` for object-level
  operators, use real `select_set` + `view_layer.objects.active` for anything that changes mode or
  parents.
* Exports (all headless, no override needed): GLB with embedded textures 112 KB in 0.32 s
  (`export_scene.gltf(export_format="GLB", export_apply=False)`); glTF separate with
  `export_texture_dir="tex"` 0.08 s; FBX (`use_selection=False, path_mode="COPY", embed_textures=True`)
  104 KB in 0.08 s. Reimport of the GLB (`import_scene.gltf`) 0.2 s recovered the mesh, the armature,
  the action `RigAction`, both images and both shape keys.
* Render 640 × 800, 32 spp: 50 s under load; looked at: bent checker-textured limb, smooth skinning
  at the knee, textures survived the round trip.

## 8. Skin shading (`test_08_skin.py`, log `t08_log.txt`, renders `t08_skin_sss.png`, `t08_skin_nosss.png`, `t08_skin.blend`; first attempt `t08_log_v1_blownout.txt`, `t08_skin_*_v1_blownout.png`)

Command: `blender -b --python scripts/research/test_08_skin.py`. 100 mm UV sphere (96 × 48 + Subdivision
render level 2), Principled BSDF with `subsurface_method = "RANDOM_WALK_SKIN"`, Subsurface Weight 1,
Radius (1.0, 0.2, 0.1) × Scale 0.012 m, IOR 1.4, anisotropy 0.8, Coat 0.15, mottling (Noise 60 →
ColorRamp → Base Color), micro-normal (Noise 900 + Voronoi 700 → Bump, distance 0.4 mm, strength
0.25), roughness 0.35–0.6 from the same mask, AgX view transform, three area lights, OIDN.

Three attempts:
1. 22:16 — failed at once: `sc.view_settings.look = "AgX - Medium Contrast"` is not a 4.5 enum value
   (list in the script header; use "AgX - Base Contrast" or "AgX - Medium High Contrast").
2. 22:25 — ran as written (800 × 800, 96 spp, 100 mm lens at 0.31 m, f/4 DOF, 80/20/90 W lights):
   SSS render 427.6 s, no-SSS 163.3 s, process 591.8 s (load 4→8, another job started). Looked at:
   both frames are a blown-out pale pink blur, unusable; the lights were ~10× too strong for a
   100 mm subject and the f/4 depth of field at 0.3 m blurred the whole sphere.
3. 22:36 — corrected (640 × 640, 48 spp, 85 mm at 0.54 m so the sphere fills ~90 % of the frame,
   DOF off, 12/3/12 W lights): SSS render 136.2 s, no-SSS 37.6 s, process 174.8 s, still sharing the
   box with a 2-thread job (load 7.8). Looked at: the SSS sphere reads as soft skin, the 1 cm mottling
   is there, the 0.4 mm pore bump is almost completely smoothed away by the 12 mm scattering radius
   and the limb glows slightly; the no-SSS sphere shows the pore grain sharply with harder mottling.
   So Random Walk (Skin) works headless and shows, but the lighting is still flat (no clear
   terminator because key, fill and rim surround the sphere), so this is a capability check, not a
   look-dev result.

Cost: SSS cost 2.6× (run 2) and 3.6× (run 3) the plain-surface render of the same frame; call it 3×.
For the real head use `Subsurface Scale` ≈ 0.003–0.005 m (3–5 mm red radius) so pores survive, and
expect a 1024² head closeup at 64 spp to take 4–8 min on this box.

Snippet that worked:

```python
p = mat.node_tree.nodes["Principled BSDF"]
p.subsurface_method = "RANDOM_WALK_SKIN"              # 4.x: 'BURLEY' | 'RANDOM_WALK' | 'RANDOM_WALK_SKIN'
p.inputs["Subsurface Weight"].default_value = 1.0
p.inputs["Subsurface Radius"].default_value = (1.0, 0.2, 0.1)
p.inputs["Subsurface Scale"].default_value = 0.004   # metres; 0.012 in the test erased the pore bump
p.inputs["Subsurface IOR"].default_value = 1.4
p.inputs["Subsurface Anisotropy"].default_value = 0.8
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Base Contrast"
```

## 10. Probes asked for by the part specs (`test_10_probes.py`, log `t10_log.txt`, `t10_bake_wear.png`)

Command: `blender -b --python scripts/research/test_10_probes.py`; whole process 2.1 s. Written to
answer the `[VERIFY: research_blender_capabilities]` tags in `spec/01_foot_ankle_sock.md` and
`spec/09_combat_trousers.md`.

(10a) Bundled hair node assets. The file exists and appends headless in 0.33 s:

```python
HAIR_BLEND = "/opt/blender/blender-4.5.14-linux-x64/4.5/datafiles/assets/geometry_nodes/procedural_hair_node_assets.blend"
with bpy.data.libraries.load(HAIR_BLEND, link=False) as (src, dst):
    dst.node_groups = [n for n in src.node_groups if n in ("Generate Hair Curves", "Hair Curves Noise", ...)]
m = curves_ob.modifiers.new("Noise", "NODES"); m.node_group = bpy.data.node_groups["Hair Curves Noise"]
m["Input_3"] = 0.5        # inputs by socket identifier (see list below), NOT by name
```

Node groups available (27): Attach Hair Curves to Surface, Blend Hair Curves, Braid Hair Curves,
Clump Hair Curves, Create Guide Index Map, Curl Hair Curves, Curve Info, Curve Root, Curve Segment,
Curve Tip, Displace Hair Curves, Duplicate Hair Curves, Frizz Hair Curves, Generate Hair Curves,
Hair Attachment Info, Hair Curves Noise, Interpolate Hair Curves, Redistribute Curve Points,
Restore Curve Segment Length, Roll Hair Curves, Rotate Hair Curves, Set Hair Curve Profile,
Shrinkwrap Hair Curves, Smooth Hair Curves, Straighten Hair Curves, Trim Hair Curves, shape_range.
"Hair Curves Noise" inputs → identifiers: Geometry `Input_0`, Cumulative Offset `Input_10` (bool),
Factor `Input_3`, Distance `Input_14`, Shape `Input_2`, Scale `Input_11`, Scale along Curve
`Input_12`, Offset per Curve `Input_13`, Seed `Input_8` (int), Preserve Length `Input_6` (bool).
Enumerate them with `[(it.name, it.identifier) for it in ng.interface.items_tree if it.item_type == "SOCKET" and it.in_out == "INPUT"]`.
A Curves object with that modifier evaluated headless (40 points in, 40 out).

(10b) Geometry Nodes `Store Named Attribute` (FLOAT, POINT, "wear" = Map Range of position z) →
`bpy.ops.object.modifier_apply` under `temp_override` → `ob.data.attributes["wear"]` is present on
the real mesh as (POINT, FLOAT) with values 0.0–1.0, and the shader `ShaderNodeAttribute`
(`attribute_name = "wear"`, `attribute_type = "GEOMETRY"`) reads it: yes, the attribute pipeline
survives apply, so wear/dirt masks can be computed in GN and consumed by materials.

(10c) `bpy.ops.object.bake(type="DIFFUSE")` with `use_pass_color` only, 512 × 512, 4 spp, works
headless with NO context override provided the object is selected and active in the view layer, has
UVs, and the target Image Texture node is the material's active node (`nodes.active = tex`,
`tex.select = True`): 0.4 s, baked pixel range 0.00–0.99; looked at: the UV islands carry the
black-to-white z gradient with a 4 px margin, correct. Combined/normal bakes at 2–4 k will take tens of
seconds to a few minutes (bake cost ≈ render cost at the texel count), fine for one-off texture bakes.

## Recommendations for the build

**Render time budget per evaluation render on this machine.** Measured Cycles CPU throughput with
OIDN is about 1 MP·spp per second when the box is shared (t01: 1920×1080 × 32 spp = 66 MP·spp in
68–72 s) and roughly 2 MP·spp/s when it is not (t06: 0.64 MP × 48 spp = 31 MP·spp in 20 s, idle box).
Rules: (1) the reference-matched full-body evaluation render at 1024 × 1536 with 64 spp and
adaptive sampling (threshold 0.02) is ≈ 100 MP·spp → budget 2 min idle, 4 min shared; (2) part
closeups at 800 × 800 and 48 spp ≈ 30 MP·spp → 20–40 s, so a part script can afford 3–5 views;
(3) skin with Random Walk SSS costs ≈ 3× a plain surface (t08: 428 vs 163 s, then 136 vs 38 s for the same frame),
hair ≈ 3× per 40 k thick strands in frame, adaptive displacement 3–5× on the surfaces that use it:
budget head closeups at 6–10 min and keep SSS to the head and hands; (4) 1080p × 128 spp "final"
renders are 4–9 min and must be run one at a time (two renders in parallel are slower than two in
series on 4 cores, as the first pass showed). Always set `use_denoising = True` with
`RGB_ALBEDO_NORMAL`, `use_adaptive_sampling = True`, and `scene.render.use_persistent_data = True`
when a script renders several views of the same scene (saves the 1–3 s BVH/shader rebuild per view).
Keep a 10-second "look" preset too: 480 × 720, 16 spp, OIDN, for geometry checks.

**Is cloth simulation viable for the trousers and the gaiter?** Yes. The headless pipeline is
proven end to end (Collision modifier on the body proxy, Cloth on the garment, `scene.frame_set`
stepping or `ptcache.bake_all` under `temp_override(scene=…)`, then `modifier_apply` under
`temp_override(object=…)`), it is deterministic, and it is cheap: 60 frames of a 3.1 k-vert tube
with self-collision took 10 s, 60 frames of a 3.5 k-vert sewn pair 21 s. The 13.7 k-vert, 100-frame
trousers plan in `spec/09` should take 1–2 min, well inside budget, and the gaiter (a few thousand
verts) seconds. Conditions learnt here: give the hem something to land on and make the leg longer
than the body so folds form (a pinned uniform tube drapes as a stiff cylinder); keep
`distance_min`/`self_distance_min` ≥ 3–4 mm at 7–10 mm quads; never pin vertices that carry sewing
edges; pin to a waistband ring instead; sewing springs close reliably at `sewing_force_max = 5` within
60 frames. Sim first, then Shrinkwrap + Solidify + Displace (t06, instant) for thickness, seams and
micro-wrinkles, and bake the result into `Trousers.Base` so the rig deforms a static mesh.

**Which hair system to use?** The new Curves system (`bpy.data.hair_curves`) with the bundled
procedural node groups (t10a: Generate / Interpolate / Clump / Hair Curves Noise / Trim / Set Hair
Curve Profile, appended with `bpy.data.libraries.load`). Reasons: curves are built from Python in
milliseconds with exact root placement, radius is a per-point attribute Cycles honours (t03b), GN
modifiers evaluate headless on Curves objects (t03d), and the particle system can still be used as a
generator and converted (`curves.convert_from_particle_system`, t03c) when its interpolated-children
look is wanted. Legacy particle hair also renders headless (t03a) and is the fallback for the cheap
"20 children per parent" density. Both render through `sc.cycles_curves.shape = "THICK"`; set strand
radius to 0.03–0.06 mm (`radius_scale ≈ 1e-4` on particles, radius attribute on curves), not the
5 mm used in the test. Use the Principled Hair BSDF (Chiang) with melanin; for stubble and brows at
evaluation-render scale (head ≈ 120 px tall) a few thousand curves are enough.

**Is adaptive displacement usable?** Technically yes (t04: EXPERIMENTAL feature set, Subdivision as
the last modifier, `ob.cycles.use_adaptive_subdivision`, `mat.displacement_method = "DISPLACEMENT"`),
and it gives real silhouettes, but at ≈ 4 min for a single plane at 720p/64 spp it is the most
expensive feature tested. Use it only on hero surfaces whose silhouette must break (boot-sole lugs
seen edge-on, knit gaiter cuff, helmet cover texture if it is ever in closeup) with `dicing_rate`
2–4 px, and everywhere else use `displacement_method = "BUMP"` or the Displace modifier on a
real subdivided mesh (t06), which costs nothing at render time and exports to glTF.

**Context-override rules for headless scripts (from t02, t03, t06, t07, t10).**
`temp_override(object=ob, active_object=ob, selected_objects=[ob])` is enough for
`object.modifier_apply`, `ptcache.bake_all` (with `scene=`), `curves.convert_from_particle_system`
and the glTF/FBX exporters. It is NOT enough for `object.mode_set` and `object.parent_set`: those
silently act on the view layer's real active/selected objects, so set `view_layer.objects.active`
and `select_set()` first. `object.bake` needs the real selection plus an active Image Texture node.
`render.render(write_still=True)` needs nothing. Capture modifier names before applying (dangling
RNA pointers), set GN inputs by socket identifier, and remember `view_settings.look` names changed
("AgX - Base Contrast", "AgX - Medium High Contrast"; there is no "AgX - Medium Contrast").
