"""Test 2: headless cloth simulation.
Variant A: tube 'trouser leg' cloth around a cylinder 'thigh' collider, self-collision on,
           60 frames, apply at last frame, render.
Variant B: two flat panels with sewing springs around the cylinder.
Run: blender -b --python test_02_cloth.py -- [A|B|AB]
"""
import bpy, bmesh, sys, time, math, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
variants = argv[0] if argv else "AB"
OUT = "/home/user/sgt_morgan/renders/research"
os.makedirs(OUT, exist_ok=True)
T = {}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 960
    sc.render.resolution_y = 1080
    sc.frame_start = 1
    sc.frame_end = 60
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.2, 0.2, 0.22, 1)
    # lights
    for name, loc, e in (("Key", (2, -2.5, 2.5), 600), ("Fill", (-2.5, -1.5, 1.5), 200), ("Rim", (0.5, 2.5, 2.0), 400)):
        ld = bpy.data.lights.new(name, "AREA"); ld.energy = e; ld.size = 1.5
        lo = bpy.data.objects.new(name, ld); lo.location = loc
        sc.collection.objects.link(lo)
        import mathutils
        direction = mathutils.Vector((0, 0, 0.3)) - lo.location
        lo.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cd = bpy.data.cameras.new("Cam"); cd.lens = 60
    cam = bpy.data.objects.new("Cam", cd); cam.location = (0.9, -1.6, 0.45)
    import mathutils
    direction = mathutils.Vector((0, 0, 0.2)) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(cam); sc.camera = cam
    return sc


def fabric_material(name, color):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = color
    p.inputs["Roughness"].default_value = 0.85
    p.inputs["Sheen Weight"].default_value = 0.4
    return m


def make_thigh(sc):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.08, depth=0.5, location=(0, 0, 0.25))
    thigh = bpy.context.active_object
    thigh.name = "Thigh"
    bpy.ops.object.shade_smooth()
    thigh.modifiers.new("Collision", "COLLISION")
    thigh.collision.thickness_outer = 0.003
    m = bpy.data.materials.new("Skin"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.6, 0.5, 1)
    thigh.data.materials.append(m)
    return thigh


def build_tube(name, radius, z0, z1, segs=64, rings=40):
    """Open tube mesh with vertical rings (quad grid) built with bmesh."""
    bm = bmesh.new()
    ring_verts = []
    for r in range(rings + 1):
        z = z0 + (z1 - z0) * r / rings
        row = []
        for s in range(segs):
            a = 2 * math.pi * s / segs
            row.append(bm.verts.new((radius * math.cos(a), radius * math.sin(a), z)))
        ring_verts.append(row)
    for r in range(rings):
        for s in range(segs):
            v1 = ring_verts[r][s]; v2 = ring_verts[r][(s + 1) % segs]
            v3 = ring_verts[r + 1][(s + 1) % segs]; v4 = ring_verts[r + 1][s]
            bm.faces.new((v1, v2, v3, v4))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    # pin group = top ring
    vg = ob.vertex_groups.new(name="Pin")
    top = [v.index for v in me.vertices if v.co.z > z1 - 1e-4]
    vg.add(top, 1.0, "REPLACE")
    return ob


def add_cloth(ob, pin_group="Pin", sewing=False):
    cm = ob.modifiers.new("Cloth", "CLOTH")
    cs = cm.settings
    cs.quality = 8
    cs.mass = 0.3
    cs.tension_stiffness = 15
    cs.compression_stiffness = 15
    cs.shear_stiffness = 5
    cs.bending_stiffness = 0.5
    cs.tension_damping = 5
    cs.air_damping = 1.0
    cs.vertex_group_mass = pin_group
    if sewing:
        cs.use_sewing_springs = True
        cs.sewing_force_max = 5.0
        cs.shrink_min = 0.0
    col = cm.collision_settings
    col.use_collision = True
    col.distance_min = 0.004
    col.collision_quality = 4
    col.use_self_collision = True
    col.self_distance_min = 0.004
    col.self_friction = 5
    cm.point_cache.frame_start = 1
    cm.point_cache.frame_end = 60
    return cm


def bake_by_stepping(sc, frames=60):
    t0 = time.time()
    for f in range(1, frames + 1):
        sc.frame_set(f)
    return time.time() - t0


def try_bake_all(sc):
    """Try the operator route and report whether it works headless."""
    t0 = time.time()
    try:
        with bpy.context.temp_override(scene=sc, point_cache=None):
            r = bpy.ops.ptcache.bake_all(bake=True)
        return True, r, time.time() - t0
    except Exception as e:
        return False, repr(e), time.time() - t0


def apply_cloth_at_current_frame(ob, modname="Cloth"):
    """Headless-safe 'apply': take the evaluated mesh and replace the object data."""
    dg = bpy.context.evaluated_depsgraph_get()
    ob_eval = ob.evaluated_get(dg)
    me_new = bpy.data.meshes.new_from_object(ob_eval, preserve_all_data_layers=True, depsgraph=dg)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me_new
    for p in me_new.polygons:
        p.use_smooth = True
    bpy.data.meshes.remove(old)
    return me_new


def try_modifier_apply_operator(ob, modname):
    try:
        with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
            r = bpy.ops.object.modifier_apply(modifier=modname)
        return True, r
    except Exception as e:
        return False, repr(e)


# ------------------------------------------------------------------ Variant A
if "A" in variants:
    sc = reset_scene()
    thigh = make_thigh(sc)
    leg = build_tube("TrouserLeg", radius=0.115, z0=-0.02, z1=0.52, segs=64, rings=48)
    leg.data.materials.append(fabric_material("Fabric", (0.35, 0.33, 0.22, 1)))
    cm = add_cloth(leg)
    # ask bake_all first (on a copy of the situation) to record the gotcha
    ok, info, dt = try_bake_all(sc)
    print(f"[A] ptcache.bake_all headless ok={ok} info={info} dt={dt:.1f}s", flush=True)
    T["A_bake_all_ok"] = ok; T["A_bake_all_info"] = str(info); T["A_bake_all_s"] = round(dt, 1)
    if not ok or sc.frame_current != 60:
        # fall back to stepping (also warms cache)
        dt2 = bake_by_stepping(sc, 60)
        print(f"[A] frame stepping 60 frames: {dt2:.1f}s", flush=True)
        T["A_step_s"] = round(dt2, 1)
    sc.frame_set(60)
    # test operator apply (expected to work with temp_override in 4.x), fallback to evaluated mesh
    ok2, info2 = try_modifier_apply_operator(leg, "Cloth")
    print(f"[A] modifier_apply via temp_override ok={ok2} info={info2}", flush=True)
    T["A_modifier_apply_ok"] = ok2; T["A_modifier_apply_info"] = str(info2)
    if not ok2:
        apply_cloth_at_current_frame(leg)
    nverts = len(leg.data.vertices)
    zs = [v.co.z for v in leg.data.vertices]
    print(f"[A] applied mesh verts={nverts} zmin={min(zs):.3f} zmax={max(zs):.3f}", flush=True)
    T["A_zmin"] = round(min(zs), 3)
    t0 = time.time()
    sc.render.filepath = f"{OUT}/t02_cloth_tube.png"
    bpy.ops.render.render(write_still=True)
    T["A_render_s"] = round(time.time() - t0, 1)
    bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/t02_cloth_tube.blend")

# ------------------------------------------------------------------ Variant B
if "B" in variants:
    sc = reset_scene()
    thigh = make_thigh(sc)
    # Two flat panels (front at -Y, back at +Y), each a grid; sewing edges join side borders.
    W, H = 0.30, 0.56   # panel width (half circumference-ish 2*pi*0.115/2=0.36), height
    nx, nz = 30, 56
    bm = bmesh.new()
    panels = []
    for sign in (-1, 1):   # -1 front, +1 back
        grid = []
        for j in range(nz + 1):
            row = []
            for i in range(nx + 1):
                x = -W / 2 + W * i / nx
                z = -0.03 + H * j / nz
                y = sign * 0.16
                row.append(bm.verts.new((x, y, z)))
            grid.append(row)
        for j in range(nz):
            for i in range(nx):
                bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
        panels.append(grid)
    # sewing springs: loose edges between corresponding border verts of both panels
    front, back = panels
    for j in range(nz + 1):
        bm.edges.new((front[j][0], back[j][0]))
        bm.edges.new((front[j][nx], back[j][nx]))
    me = bpy.data.meshes.new("Panels"); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    pan = bpy.data.objects.new("TrouserPanels", me)
    sc.collection.objects.link(pan)
    vg = pan.vertex_groups.new(name="Pin")
    top = [v.index for v in me.vertices if v.co.z > -0.03 + H - 1e-4]
    vg.add(top, 1.0, "REPLACE")
    pan.data.materials.append(fabric_material("Fabric", (0.35, 0.33, 0.22, 1)))
    cm = add_cloth(pan, sewing=True)
    dt = bake_by_stepping(sc, 60)
    print(f"[B] frame stepping 60 frames (sewing): {dt:.1f}s", flush=True)
    T["B_step_s"] = round(dt, 1)
    sc.frame_set(60)
    ok2, info2 = try_modifier_apply_operator(pan, "Cloth")
    if not ok2:
        apply_cloth_at_current_frame(pan)
    # measure closure: max distance between sewn vertex pairs
    import mathutils
    me = pan.data
    # after apply, loose sewing edges still exist in the mesh; measure their lengths
    loose = [e for e in me.edges if e.is_loose]
    gaps = [(me.vertices[e.vertices[0]].co - me.vertices[e.vertices[1]].co).length for e in loose]
    print(f"[B] sewing edges={len(loose)} gap max={max(gaps) if gaps else -1:.4f} mean={sum(gaps)/len(gaps) if gaps else -1:.4f}", flush=True)
    T["B_sew_gap_max"] = round(max(gaps), 4) if gaps else None
    T["B_sew_gap_mean"] = round(sum(gaps) / len(gaps), 4) if gaps else None
    t0 = time.time()
    sc.render.filepath = f"{OUT}/t02_cloth_sewing.png"
    bpy.ops.render.render(write_still=True)
    T["B_render_s"] = round(time.time() - t0, 1)
    bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/t02_cloth_sewing.blend")

import json
print("[T02_JSON] " + json.dumps(T))
