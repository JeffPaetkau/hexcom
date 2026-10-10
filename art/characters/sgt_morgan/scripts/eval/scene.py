"""The evaluation scene under spec 17's scope note: the hero camera, the key and cool side lights with
light groups, the dim cool world, a plain concrete floor plane and colour management (§4.1-4.4, §4.10,
§5.1, §5.4, §5.6). Deferred until the model is accepted, so not built here: the hangar set, the floor
joints and trench, the floor-pool spot, the kicker and under fill (both off in the spec anyway), depth
of field, haze and glare. Hero renders use a transparent film; grade.py composites them over a flat
backdrop.

  python scripts/eval/scene.py --build --proxy                      (launches Blender)
  blender -b --python scripts/eval/scene.py -- --build [--proxy | --character cache/character_hero.blend]
                                             [--world hdri|gradient] [--out cache/scene_eval.blend]
  python scripts/eval/scene.py --build --character cache/body/rigged.blend --collection Body
                                             (the rigged rest body of build_all.py S2, before S11 exists)

Idempotent: build() deletes and rebuilds everything named Scene.* and the proxy, and never touches a
linked character's own objects. The proxy is spec 17 §4.7's Cal.Proxy: the MPFB default male (the
default macros with gender 1.0) standing at the origin, facing -Y, the midpoint of his ankle joints
over the origin; it stands in for the character when checking the camera and timing renders.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(HERE))  # scripts/
from lib import env  # noqa: E402
from eval import camera  # noqa: E402

OUT_BLEND = env.path("cache", "scene_eval.blend")
HDRI = env.path("assets", "hdri", "empty_warehouse_01_2k.hdr")
SCENE_NAME, CHAR_COLL = "Hero", "Character"
OWNED = ("Scene.", "Cal.Proxy", "Cal.Mat.Proxy")
# §4.4, the lights in scope: positions from chest (0, 0, 1.30) + d (sin az cos el, -cos az cos el, sin el)
LIGHTS = {
    "Scene.Light.R.Key": {"size": 1.50, "loc": (-1.70, -2.00, 3.60), "target": (0.0, 0.0, 1.25), "energy": 800.0,
                          "temperature": 4500.0, "color": (1.0, 1.0, 1.0), "spread": 180.0, "group": "key"},
    "Scene.Light.L.Cool": {"size": 3.00, "loc": (3.20, 0.60, 3.60), "target": (0.0, 0.0, 1.00), "energy": 600.0,
                           "temperature": None, "color": (0.55, 0.76, 1.00), "spread": 180.0, "group": "cool"},
}
# §3.4 and §5.1 without joints, slabs or wear: the reflectance that gives contact shadows, boot reflections
# and bounce. Albedo 0.12 is calibration's start value (D8), slightly cool.
FLOOR = {"albedo": 0.12, "tint": (0.96, 1.00, 1.05), "roughness": 0.30, "ior": 1.50, "specular_ior_level": 0.5,
         "coat": 0.10, "coat_roughness": 0.20, "coat_ior": 1.50, "size": 30.0, "centre": (3.0, 1.0)}
WORLD = {"strength": 0.05, "tint": (0.60, 0.75, 1.00), "rotation_z_deg": -80.0}
GRADIENT = {"zenith": (0.010, 0.020, 0.035), "horizon": (0.004, 0.006, 0.008), "ground": (0.012, 0.010, 0.008)}
MIST = {"start": 5.0, "depth": 15.0, "falloff": "LINEAR"}
PROXY_SKIN = "#b98670"   # spec 06's base skin albedo (sRGB)
PROXY_BODY = 0.05        # Lambertian grey for everything below the neck (spec 17 §4.7)


def srgb_to_linear(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def hex_linear(h):
    h = h.lstrip("#")
    return tuple(float(v) for v in srgb_to_linear([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]))


def _input(node, *names):
    for n in names:
        for s in node.inputs:
            if s.name == n or s.identifier == n:
                return s
    raise KeyError(f"{node.bl_idname} has no input {names}")


def _output(node, *names):
    for n in names:
        for s in node.outputs:
            if s.name == n or s.identifier == n:
                return s
    raise KeyError(f"{node.bl_idname} has no output {names}")


def clear(scene):
    """Remove what this script owns, so a rebuild starts clean."""
    import bpy
    if scene.world is not None and scene.world.name.startswith(OWNED):
        scene.world = None  # else the old world keeps a user and the new one becomes .001
    for ob in list(bpy.data.objects):
        if ob.name.startswith(OWNED) and ob.library is None:
            bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.worlds, bpy.data.lights, bpy.data.cameras, bpy.data.meshes, bpy.data.materials,
                 bpy.data.images):
        for d in list(coll):
            if d.name.startswith(OWNED) and d.library is None and d.users == 0:
                coll.remove(d)
    for c in list(bpy.data.collections):
        if c.name.startswith("Scene.") and c.library is None and not c.all_objects:
            bpy.data.collections.remove(c)


def collection(scene, name, parent=None):
    import bpy
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    parent = parent or scene.collection
    if c not in scene.collection.children_recursive:
        parent.children.link(c)
    return c


def build_floor(scene):
    import bpy
    coll = collection(scene, "Scene.Floor")
    half = FLOOR["size"] / 2.0
    me = bpy.data.meshes.new("Scene.Floor.C.Slab")
    me.from_pydata([(-half, -half, 0.0), (half, -half, 0.0), (half, half, 0.0), (-half, half, 0.0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new("Scene.Floor.C.Slab", me)
    ob.location = (FLOOR["centre"][0], FLOOR["centre"][1], 0.0)
    coll.objects.link(ob)
    m = bpy.data.materials.new("Scene.Mat.Floor.Concrete")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    _input(p, "Base Color").default_value = (*[FLOOR["albedo"] * t for t in FLOOR["tint"]], 1.0)
    _input(p, "Roughness").default_value = FLOOR["roughness"]
    _input(p, "IOR").default_value = FLOOR["ior"]
    _input(p, "Specular IOR Level").default_value = FLOOR["specular_ior_level"]
    _input(p, "Coat Weight").default_value = FLOOR["coat"]
    _input(p, "Coat Roughness").default_value = FLOOR["coat_roughness"]
    _input(p, "Coat IOR").default_value = FLOOR["coat_ior"]
    me.materials.append(m)
    return ob


def build_lights(scene):
    import bpy
    coll = collection(scene, "Scene.Light")
    vl = scene.view_layers[0]
    made = []
    for name, L in LIGHTS.items():
        data = bpy.data.lights.new(name, "AREA")
        data.shape, data.size, data.energy = "SQUARE", L["size"], L["energy"]
        data.spread = math.radians(L["spread"])
        data.use_shadow = True
        data.normalize = True
        data.cycles.use_multiple_importance_sampling = True
        data.color = L["color"]
        data.use_temperature = L["temperature"] is not None
        if L["temperature"]:
            data.temperature = L["temperature"]
        ob = bpy.data.objects.new(name, data)
        ob.location = L["loc"]
        coll.objects.link(ob)
        tgt = bpy.data.objects.new(name + ".Target", None)
        tgt.location, tgt.empty_display_size = L["target"], 0.1
        coll.objects.link(tgt)
        con = ob.constraints.new("TRACK_TO")
        con.target, con.track_axis, con.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
        if L["group"] not in vl.lightgroups:
            vl.lightgroups.add(name=L["group"])
        ob.lightgroup = L["group"]
        made.append(ob)
    return made


def build_world(scene, kind="hdri"):
    import bpy
    w = bpy.data.worlds.new("Scene.World.Hangar")
    scene.world = w  # first: Cycles' world property callbacks expect the scene to have one
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(_output(bg, "Background"), _input(out, "Surface"))
    if kind == "hdri" and not os.path.exists(HDRI):
        print(f"[scene] {os.path.relpath(HDRI, env.PROJECT_DIR)} is missing (setup_session.sh fetches it); "
              "using the gradient world", flush=True)
        kind = "gradient"
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if kind == "hdri":
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.vector_type = "POINT"
        _input(mp, "Rotation").default_value = (0.0, 0.0, math.radians(WORLD["rotation_z_deg"]))
        tex = nt.nodes.new("ShaderNodeTexEnvironment")
        img = bpy.data.images.load(HDRI, check_existing=True)
        img.name = "Scene.Img.Hangar"
        tex.image, tex.interpolation, tex.projection = img, "Linear", "EQUIRECTANGULAR"
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
        _input(mix, "Factor_Float").default_value = 1.0
        _input(mix, "B_Color").default_value = (*WORLD["tint"], 1.0)
        nt.links.new(_output(tc, "Generated"), _input(mp, "Vector"))
        nt.links.new(_output(mp, "Vector"), _input(tex, "Vector"))
        nt.links.new(_output(tex, "Color"), _input(mix, "A_Color"))
        nt.links.new(_output(mix, "Result_Color"), _input(bg, "Color"))
        _input(bg, "Strength").default_value = WORLD["strength"]
    else:  # the lighting note's procedural sky: ground below the horizon, zenith above
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mr = nt.nodes.new("ShaderNodeMapRange")
        _input(mr, "From Min").default_value, _input(mr, "From Max").default_value = -1.0, 1.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        el = ramp.color_ramp.elements
        el[0].position, el[0].color = 0.0, (*GRADIENT["ground"], 1.0)
        el[1].position, el[1].color = 1.0, (*GRADIENT["zenith"], 1.0)
        mid = el.new(0.5)
        mid.color = (*GRADIENT["horizon"], 1.0)
        nt.links.new(_output(tc, "Generated"), _input(sep, "Vector"))
        nt.links.new(_output(sep, "Z"), _input(mr, "Value"))
        nt.links.new(_output(mr, "Result"), _input(ramp, "Fac"))
        nt.links.new(_output(ramp, "Color"), _input(bg, "Color"))
        _input(bg, "Strength").default_value = 1.0
    vis = getattr(w, "visibility", None) or getattr(w, "cycles_visibility", None)
    if vis is not None and hasattr(vis, "camera"):
        vis.camera = False  # the frame is film-transparent; the world only lights
    w.cycles.sampling_method, w.cycles.sample_map_resolution = "AUTOMATIC", 1024
    w.mist_settings.start, w.mist_settings.depth, w.mist_settings.falloff = MIST["start"], MIST["depth"], MIST["falloff"]
    vl = scene.view_layers[0]
    if "world" not in vl.lightgroups:
        vl.lightgroups.add(name="world")
    w.lightgroup = "world"
    scene.world = w
    return kind


def colour_management(scene):
    """§5.6: AgX Medium High Contrast to sRGB, nothing else; the grade happens after, in grade.py."""
    scene.display_settings.display_device = "sRGB"
    vs = scene.view_settings
    vs.view_transform, vs.look = "AgX", "AgX - Medium High Contrast"
    vs.exposure, vs.gamma, vs.use_curve_mapping = 0.0, 1.0, False
    if hasattr(vs, "use_white_balance"):
        vs.use_white_balance = False
    scene.render.dither_intensity = 0.0


def _vertex_group_centroids(ob, names):
    """Evaluated centroids of vertex groups, with the helper mask off so the joint cubes are there."""
    import bpy
    masks = [m for m in ob.modifiers if m.type == "MASK"]
    saved = [(m, m.show_viewport) for m in masks]
    for m in masks:
        m.show_viewport = False
    try:
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        ev.to_mesh_clear()
    finally:
        for m, v in saved:
            m.show_viewport = v
    co = co.reshape(-1, 3) @ np.array(ob.matrix_world)[:3, :3].T + np.array(ob.matrix_world)[:3, 3]
    out = {}
    for n in names:
        g = ob.vertex_groups.get(n)
        if g is None:
            continue
        idx = [v.index for v in ob.data.vertices if any(e.group == g.index and e.weight > 0.5 for e in v.groups)]
        if idx:
            out[n] = co[idx].mean(axis=0)
    return out, co


def build_proxy(scene):
    """Cal.Proxy in the Character collection: the MPFB default male at the origin (spec 17 §4.7)."""
    import bpy
    mod = "bl_ext.user_default.mpfb"
    if mod not in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_enable(module=mod)
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    from bl_ext.user_default.mpfb.services.targetservice import TargetService
    macro = TargetService.get_default_macro_info_dict()
    macro["gender"] = 1.0
    ob = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                   feet_on_ground=True, scale=0.1, macro_detail_dict=macro)
    ob.name = ob.data.name = "Cal.Proxy"
    char = collection(scene, CHAR_COLL)
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    char.objects.link(ob)
    joints, co = _vertex_group_centroids(ob, ("joint-l-ankle", "joint-r-ankle", "joint-neck", "joint-head-2"))
    mid = (joints["joint-l-ankle"] + joints["joint-r-ankle"]) / 2.0
    ob.location.x -= mid[0]
    ob.location.y -= mid[1]
    # materials: spec 06's skin albedo above the neck joint, Lambertian 0.05 grey below
    skin = bpy.data.materials.new("Cal.Mat.Proxy.Skin")
    skin.use_nodes = True
    p = skin.node_tree.nodes["Principled BSDF"]
    _input(p, "Base Color").default_value = (*hex_linear(PROXY_SKIN), 1.0)
    _input(p, "Roughness").default_value = 0.45
    body = bpy.data.materials.new("Cal.Mat.Proxy.Body")
    body.use_nodes = True
    nt = body.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    _input(dif, "Color").default_value = (PROXY_BODY, PROXY_BODY, PROXY_BODY, 1.0)
    nt.links.new(_output(dif, "BSDF"), _input(nt.nodes["Material Output"], "Surface"))
    me = ob.data
    me.materials.clear()
    me.materials.append(body)
    me.materials.append(skin)
    neck_z = joints["joint-neck"][2]
    loop_v = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", loop_v)
    starts = np.empty(len(me.polygons), np.int64)
    counts = np.empty(len(me.polygons), np.int64)
    me.polygons.foreach_get("loop_start", starts)
    me.polygons.foreach_get("loop_total", counts)
    zc = np.add.reduceat(co[loop_v, 2], starts) / counts   # face centre heights (polygon loops are contiguous)
    me.polygons.foreach_set("material_index", (zc > neck_z).astype(np.int32))
    me.shade_smooth()
    me.update()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    em = ev.to_mesh()
    ec = np.empty(len(em.vertices) * 3)
    em.vertices.foreach_get("co", ec)
    ev.to_mesh_clear()
    ec = ec.reshape(-1, 3) @ np.array(ob.matrix_world)[:3, :3].T + np.array(ob.matrix_world)[:3, 3]
    ank = {k: [round(float(v), 4) for v in joints[k] - np.array([mid[0], mid[1], 0.0])] for k in ("joint-l-ankle", "joint-r-ankle")}
    return {"object": ob.name, "stature_m": round(float(ec[:, 2].max() - ec[:, 2].min()), 4),
            "lowest_z_m": round(float(ec[:, 2].min()), 5), "ankles_m": ank,
            "moved_xy_m": [round(-float(mid[0]), 5), round(-float(mid[1]), 5)],
            "faces_forward": bool(joints["joint-head-2"][1] - mid[1] < 0.02 and ec[:, 1].min() < -0.1)}


def link_character(scene, path, name=CHAR_COLL):
    """Link the Character collection that spec 18's build_all.py writes, or another collection by name:
    `Body` (Body.Mesh and Morgan.Rig) from cache/body/rigged.blend until the assembly stage exists."""
    import bpy
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} is missing; spec 18's build_all.py writes it (or build with --proxy)")
    with bpy.data.libraries.load(path, link=True) as (src, dst):
        if name not in src.collections:
            raise KeyError(f"{path} has no {name!r} collection")
        dst.collections = [name]
    coll = dst.collections[0]
    if coll not in scene.collection.children_recursive:
        scene.collection.children.link(coll)
    return {"linked": os.path.relpath(path, env.PROJECT_DIR), "objects": len(coll.all_objects)}


def build(proxy=False, character=None, world="hdri", collection=CHAR_COLL):
    """Build or rebuild the hero scene in the open file. Returns a summary."""
    import bpy
    from eval import render  # the Cycles defaults live with the tiers
    t0 = time.time()
    scene = bpy.data.scenes.get(SCENE_NAME) or bpy.context.scene
    scene.name = SCENE_NAME
    clear(scene)
    scene.unit_settings.system, scene.unit_settings.scale_length = "METRIC", 1.0
    scene.frame_set(1)
    camera.hero_camera(scene)
    floor = build_floor(scene)
    lights = build_lights(scene)
    used_world = build_world(scene, world)
    colour_management(scene)
    scene.render.engine = "CYCLES"
    render.cycles_common(scene)
    scene.render.film_transparent = True
    summary = {"scene": scene.name, "camera": camera.HERO_NAME, "floor": floor.name, "lights": [o.name for o in lights],
               "world": used_world, "view": [scene.view_settings.view_transform, scene.view_settings.look],
               "lightgroups": [g.name for g in scene.view_layers[0].lightgroups]}
    if character:
        summary["character"] = link_character(scene, character, collection)
    elif proxy:
        summary["proxy"] = build_proxy(scene)
    summary["seconds"] = round(time.time() - t0, 2)
    return summary


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--build", action="store_true", help="build the hero scene from an empty file and save it")
    ap.add_argument("--proxy", action="store_true", help="add Cal.Proxy, the MPFB default male, as the character")
    ap.add_argument("--character", help="link the Character collection from this .blend instead")
    ap.add_argument("--collection", default=CHAR_COLL,
                    help="the collection --character links (default Character; Body for cache/body/rigged.blend)")
    ap.add_argument("--world", choices=("hdri", "gradient"), default="hdri")
    ap.add_argument("--out", default=os.path.relpath(OUT_BLEND, env.PROJECT_DIR), help="where to save (project-relative)")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args(argv)
    if not a.build:
        ap.print_help()
        return 2
    if not camera.in_blender():
        return camera.run_in_blender(__file__, argv)
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)  # resets preferences in memory only; MPFB is re-enabled by the proxy
    try:
        summary = build(a.proxy, a.character, a.world, a.collection)
    except (FileNotFoundError, KeyError) as e:
        print(f"[scene] {e}", flush=True)
        return 3
    if not a.no_save:
        out = env.path(a.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
        summary["saved"] = os.path.relpath(out, env.PROJECT_DIR).replace(os.sep, "/")
    print("RESULT " + json.dumps(summary), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(camera.script_args()))
