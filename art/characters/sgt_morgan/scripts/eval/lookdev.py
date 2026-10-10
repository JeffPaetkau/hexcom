"""Spec 17 §4.8's look-dev scene `LookDev`: where materials and part closeups are judged, under neutral
light and AgX Base Contrast, with no grade (spec 16 §5.6), and not under the hero lights, which are 3-5 x too
bright until calibration (§4.14).

  LookDev.Stage.Cyc        an 18 % grey cyclorama: floor Y -3 .. +1 at z 0, a 1 m cove, wall at Y +2 to 4 m
  LookDev.Rig              an Empty carrying the three white area lights; aim() puts it on the subject
                           and scales it by s = subject radius / 0.5 m, the powers by s², so the irradiance
                           at the subject is the same for a swatch and the whole figure
  LookDev.World.Studio     autoshop_01 desaturated, strength 0.30, turned +106° about Z
  Cal.Card18 / BallGrey / BallChrome / Chart   the calibration rig of §4.7 on a stand at (0, 0, 1.0)
  LookDev.Swatch           the 100 x 100 mm swatch plane at (-0.06, 0, 1.0) beside the card (spec 16 V1)
  LookDev.Turntable        the turntable Empty (camera.py's turntables orbit the camera, §4.14 item 8)

The key, fill and rim powers come from lookdev.json, written by --calibrate: one light at a time, the
Lambertian 0.18 card facing it reads 0.180 (key), 0.045 (fill, a quarter) and 0.090 (rim, a half).

As built (2026-10-10), beyond §4.8: aim() turns the rig with the camera, so every closeup is lit key-left-
front in its own view (§4.8's orbit_camera mode, generalised; for a camera on -Y it is §4.8's placement):
about Z for a camera level with or above the subject, in full for one below it (spec 01's plantar view,
which the hero lights cannot reach). The cyclorama turns about the subject with the camera's heading, so
side views keep the wall behind them. The stage props (the calibration rig, the swatch and the library's
test objects) render only for spec 16 and 17's own presets.

  python scripts/eval/lookdev.py --build                  (adds LookDev to cache/scene_eval.blend)
  python scripts/eval/lookdev.py --calibrate              (measures the light powers into lookdev.json)
  python scripts/eval/lookdev.py --swatch Skin.Foot,Nail.Plate [--tier look|eval]   (spec 16 swatches)
  python scripts/eval/lookdev.py --render p17.V6 [--tier eval]
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

SCENE = "LookDev"
SWATCH = "LookDev.Swatch"
CAL_JSON = os.path.join(HERE, "lookdev.json")
HDRI = env.path("assets", "hdri", "autoshop_01_2k.hdr")
OWNED_PREFIXES = ("LookDev.", "Cal.Card18", "Cal.BallGrey", "Cal.BallChrome", "Cal.Chart", "Cal.Mat.Grey18",
                  "Cal.Mat.GreyBall", "Cal.Mat.Chrome", "Cal.Mat.Chart", "Cal.Img.Chart", "Lib.Test.")
COLLS = ("LookDev.Stage", "LookDev.Light", "LookDev.Cal", "LookDev.Swatch", "LookDev.Turntable")
STAGE_OWNERS = ("16", "17")   # presets whose views include the calibration rig and the swatch stage
# §4.8: azimuth from -Y, positive toward +X (the soldier's left); elevation; distance and size at s = 1
LIGHTS = {
    "LookDev.Light.R.Key": {"shape": "SQUARE", "size": (1.0, 1.0), "az": -35.0, "el": 45.0, "d": 3.0, "target": 0.180},
    "LookDev.Light.L.Fill": {"shape": "SQUARE", "size": (1.5, 1.5), "az": 60.0, "el": 20.0, "d": 3.5, "target": 0.045},
    "LookDev.Light.C.Rim": {"shape": "RECTANGLE", "size": (0.5, 2.0), "az": 160.0, "el": 30.0, "d": 3.0, "target": 0.090},
}
DEFAULT_POWER = {"LookDev.Light.R.Key": 100.0, "LookDev.Light.L.Fill": 30.0, "LookDev.Light.C.Rim": 60.0}
WORLD = {"strength": 0.30, "rotation_z_deg": 106.0}
CYC = {"y0": -3.0, "y1": 1.0, "cove": 1.0, "wall_y": 2.0, "top": 4.0, "half_x": 3.0, "segments": 16}
STAND = (0.0, 0.0, 1.0)
CARD_AT, SWATCH_AT = (0.06, 0.0, 1.0), (-0.06, 0.0, 1.0)
# §3.5 ColorChecker Classic, sRGB D65 (BabelColor averages as commonly published), rows of six
CHART = ["#735244", "#c29682", "#627a9d", "#576c43", "#8580b1", "#67bdaa",
         "#d67e2c", "#505ba6", "#c15a63", "#5e3c6c", "#9dbc40", "#e0a32e",
         "#383d96", "#469449", "#af363c", "#e7c71f", "#bb5695", "#0885a1",
         "#f3f3f2", "#c8c8c8", "#a0a0a0", "#7a7a79", "#555555", "#343434"]


def _lin(h):
    h = h.lstrip("#")
    c = np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4))


def load_powers():
    try:
        with open(CAL_JSON, encoding="utf-8") as f:
            return dict(DEFAULT_POWER, **json.load(f)["power_w_at_s1"])
    except (OSError, ValueError, KeyError):
        print("[lookdev] lookdev.json is missing: uncalibrated light powers (run --calibrate)", flush=True)
        return dict(DEFAULT_POWER)


# --------------------------------------------------------------------------- building

def _coll(scene, name, parent=None):
    import bpy
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    parent = parent or scene.collection
    if c not in scene.collection.children_recursive:
        parent.children.link(c)
    return c


def clear():
    """Remove what this module owns (never a linked character, never the hero scene's own objects)."""
    import bpy
    for ob in list(bpy.data.objects):
        if ob.name.startswith(OWNED_PREFIXES) and ob.library is None:
            bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.lights, bpy.data.materials, bpy.data.images, bpy.data.worlds):
        for d in list(coll):
            if d.name.startswith(OWNED_PREFIXES) and d.library is None and d.users == 0:
                coll.remove(d)


def _mesh(name, verts, faces, coll, smooth=False):
    import bpy
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    if smooth:
        me.shade_smooth()
    me.validate()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _principled(name, **v):
    import bpy
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    for k, val in v.items():
        p.inputs[k].default_value = val
    return m, p


def build_cyc(coll):
    c = CYC
    prof = [(c["y0"], 0.0), (c["y1"], 0.0)]
    for k in range(1, c["segments"] + 1):   # the cove: a quarter circle from the floor up to the wall
        a = -math.pi / 2 + (math.pi / 2) * k / c["segments"]
        prof.append((c["y1"] + c["cove"] * math.cos(a), c["cove"] + c["cove"] * math.sin(a)))
    prof.append((c["wall_y"], c["top"]))
    V = [(x, y, z) for (y, z) in prof for x in (-c["half_x"], c["half_x"])]
    F = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(prof) - 1)]
    ob = _mesh("LookDev.Stage.Cyc", V, F, coll, smooth=True)
    sub = ob.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = sub.render_levels = 1
    m, _ = _principled("LookDev.Mat.Cyc", **{"Base Color": (0.18, 0.18, 0.18, 1.0), "Roughness": 0.9,
                                             "Specular IOR Level": 0.25})
    ob.data.materials.append(m)
    return ob


def build_rig(scene, coll):
    """The rig Empty and its three lights, each aimed at the rig's origin with its long side up."""
    import bpy
    from mathutils import Matrix, Vector
    rig = bpy.data.objects.new("LookDev.Rig", None)
    rig.empty_display_type, rig.empty_display_size = "SPHERE", 0.1
    coll.objects.link(rig)
    vl = scene.view_layers[0]
    powers = load_powers()
    for name, L in LIGHTS.items():
        d = bpy.data.lights.new(name, "AREA")
        d.shape = L["shape"]
        d.size = L["size"][0]
        if L["shape"] == "RECTANGLE":
            d.size_y = L["size"][1]
        d.color, d.use_temperature = (1.0, 1.0, 1.0), False
        d.normalize, d.use_shadow = True, True
        d.cycles.use_multiple_importance_sampling = True
        d.energy = powers[name]
        d["power_w_at_s1"] = powers[name]
        ob = bpy.data.objects.new(name, d)
        coll.objects.link(ob)
        az, el = math.radians(L["az"]), math.radians(L["el"])
        pos = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * L["d"]
        z = (-pos).normalized()              # area lights shine down their local -Z
        fwd = -z
        x = Vector((0.0, 0.0, 1.0)).cross(fwd).normalized() if abs(fwd.z) < 0.999 else Vector((1.0, 0.0, 0.0))
        y = fwd.cross(x).normalized()
        R = Matrix((x, y, fwd)).transposed()  # columns x, y, z(= -direction): -Z points at the origin
        ob.parent = rig
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_basis = Matrix.Translation(pos) @ R.to_4x4()
        group = name.split(".")[-1].lower()
        if group not in vl.lightgroups:
            vl.lightgroups.add(name=group)
        ob.lightgroup = group
    return rig


def build_world(scene):
    import bpy
    w = bpy.data.worlds.new("LookDev.World.Studio")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = WORLD["strength"]
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    if os.path.exists(HDRI):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(WORLD["rotation_z_deg"]))
        tex = nt.nodes.new("ShaderNodeTexEnvironment")
        img = bpy.data.images.load(HDRI, check_existing=True)
        img.name = "LookDev.Img.Studio"
        tex.image, tex.interpolation = img, "Linear"
        hsv = nt.nodes.new("ShaderNodeHueSaturation")
        hsv.inputs["Saturation"].default_value = 0.0   # the grey studio: a neutral albedo renders neutral
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], hsv.inputs["Color"])
        nt.links.new(hsv.outputs["Color"], bg.inputs["Color"])
    else:
        print(f"[lookdev] {os.path.relpath(HDRI, env.PROJECT_DIR)} is missing (setup_session.sh fetches it): "
              "a flat grey world", flush=True)
        bg.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1.0)
    w.cycles.sampling_method, w.cycles.sample_map_resolution = "AUTOMATIC", 1024
    vl = scene.view_layers[0]
    if "world" not in vl.lightgroups:
        vl.lightgroups.add(name="world")
    w.lightgroup = "world"
    return w


def _chart_image():
    import bpy
    W, H = 1100, 850
    mm = W / 279.4
    a = np.full((H, W, 4), 1.0)
    a[..., :3] = 0.07   # the card between the patches (sRGB-encoded value)
    for k, hx in enumerate(CHART):
        r, c = divmod(k, 6)
        x0 = (279.4 - 260.0) / 2 + c * 44.0
        y0 = (215.9 - 172.0) / 2 + r * 44.0
        px = [int(round(v * mm)) for v in (x0, y0, x0 + 40.0, y0 + 40.0)]
        a[px[1]:px[3], px[0]:px[2], :3] = [int(hx[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    img = bpy.data.images.new("Cal.Img.Chart", W, H, alpha=False)
    img.colorspace_settings.name = "sRGB"
    img.pixels.foreach_set(a[::-1].astype(np.float32).ravel())   # Blender's rows run bottom up
    img.pack()
    return img


def build_cal(coll):
    import bpy
    out = {}
    w, h = 0.100, 0.150
    card = _mesh("Cal.Card18", [(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)],
                 [(0, 1, 2, 3)], coll)
    card.location = CARD_AT
    m, _ = _principled("Cal.Mat.Grey18", **{"Base Color": (0.18, 0.18, 0.18, 1.0), "Roughness": 1.0,
                                            "Specular IOR Level": 0.0})
    card.data.materials.append(m)
    out["card"] = card
    for name, x, mat in (("Cal.BallGrey", -0.21, ("Cal.Mat.GreyBall", {"Base Color": (0.18, 0.18, 0.18, 1.0),
                                                                        "Roughness": 0.6, "IOR": 1.5})),
                         ("Cal.BallChrome", 0.21, ("Cal.Mat.Chrome", {"Base Color": (0.62, 0.62, 0.62, 1.0),
                                                                      "Metallic": 1.0, "Roughness": 0.02}))):
        me = bpy.data.meshes.new(name)
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=0.05)
        bm.to_mesh(me)
        bm.free()
        me.shade_smooth()
        ob = bpy.data.objects.new(name, me)
        ob.location = (x, 0.0, STAND[2])
        coll.objects.link(ob)
        mm, _ = _principled(mat[0], **mat[1])
        me.materials.append(mm)
        out[name] = ob
    cw, ch = 0.2794, 0.2159
    chart = _mesh("Cal.Chart", [(-cw / 2, 0, -ch / 2), (cw / 2, 0, -ch / 2), (cw / 2, 0, ch / 2), (-cw / 2, 0, ch / 2)],
                  [(0, 1, 2, 3)], coll)
    chart.location = (0.0, 0.02, STAND[2])
    uv = chart.data.uv_layers.new(name="UVMap")
    uv.data.foreach_set("uv", [0, 0, 1, 0, 1, 1, 0, 1])
    m, p = _principled("Cal.Mat.Chart", **{"Roughness": 0.85, "Specular IOR Level": 0.3})
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = _chart_image()
    m.node_tree.links.new(tex.outputs["Color"], p.inputs["Base Color"])
    chart.data.materials.append(m)
    out["chart"] = chart
    return out


def build_swatch(coll):
    """The swatch plane: 100 x 100 mm facing the camera on -Y, 40 x 40 quads (regional masks can be painted
    on it), with a metric UV.Real (spec 16 §5.1) so tiled fabric maps land at their real scale."""
    n, size = 41, 0.100
    V, UV = [], []
    for j in range(n):
        for i in range(n):
            u, v = size * i / (n - 1), size * j / (n - 1)
            V.append((u - size / 2, 0.0, v - size / 2))
            UV.append((u, v))
    F = [(j * n + i, j * n + i + 1, (j + 1) * n + i + 1, (j + 1) * n + i) for j in range(n - 1) for i in range(n - 1)]
    ob = _mesh(SWATCH, V, F, coll, smooth=True)
    ob.location = SWATCH_AT
    me = ob.data
    layer = me.uv_layers.new(name="UV.Real")
    loops = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", loops)
    layer.data.foreach_set("uv", np.asarray(UV, np.float32)[loops].ravel())
    return ob


def colour_management(scene):
    """§5.6: LookDev views through AgX Base Contrast; no grade."""
    scene.display_settings.display_device = "sRGB"
    vs = scene.view_settings
    vs.view_transform, vs.look = "AgX", "AgX - Base Contrast"
    vs.exposure, vs.gamma, vs.use_curve_mapping = 0.0, 1.0, False
    if hasattr(vs, "use_white_balance"):
        vs.use_white_balance = False
    scene.render.dither_intensity = 0.0


def build(scene=None, character=None):
    """Build or rebuild LookDev: a new scene named LookDev, or the scene given (renamed LookDev, so a
    session that already holds the subject can look at it). `character`, a collection, is linked in."""
    import bpy
    from eval import render
    t0 = time.time()
    if scene is None:
        scene = bpy.data.scenes.get(SCENE) or bpy.data.scenes.new(SCENE)
    scene.name = SCENE
    if scene.world is not None and scene.world.name.startswith("LookDev."):
        scene.world = None
    clear()
    scene.unit_settings.system, scene.unit_settings.scale_length = "METRIC", 1.0
    c = {n: _coll(scene, n) for n in COLLS}
    build_cyc(c["LookDev.Stage"])
    build_rig(scene, c["LookDev.Light"])
    build_cal(c["LookDev.Cal"])
    build_swatch(c["LookDev.Swatch"])
    tt = bpy.data.objects.new("LookDev.Turntable", None)
    c["LookDev.Turntable"].objects.link(tt)
    build_world(scene)
    colour_management(scene)
    scene.render.engine = "CYCLES"
    render.cycles_common(scene)
    scene.render.film_transparent = False
    if character is not None and character not in scene.collection.children_recursive:
        scene.collection.children.link(character)
    camera.hero_camera(scene)   # the registry's cameras live in every scene that renders presets
    return {"scene": scene.name, "powers_w_at_s1": load_powers(), "seconds": round(time.time() - t0, 2)}


def ensure():
    """The LookDev scene of this file, built if it is missing."""
    import bpy
    scene = bpy.data.scenes.get(SCENE)
    if scene is None or bpy.data.objects.get("LookDev.Rig") is None:
        build(scene)
        scene = bpy.data.scenes[SCENE]
    return scene


# --------------------------------------------------------------------------- aiming (called per render)

def _frame(cam_pos, target, up):
    """The rig's rotation: its -Y toward the camera, turned about Z for a camera level with or above the
    subject, in full (its Z the camera's up) for one below it."""
    d = np.asarray(cam_pos, float) - np.asarray(target, float)
    d /= max(np.linalg.norm(d), 1e-9)
    if d[2] < -math.sin(math.radians(10.0)):
        y = -d
        z = np.asarray(up, float) - (np.asarray(up, float) @ y) * y
    else:
        h = d[:2] if np.linalg.norm(d[:2]) > 1e-3 else -np.asarray(up, float)[:2]
        y = -np.array([h[0], h[1], 0.0])
        z = np.array([0.0, 0.0, 1.0])
    y /= np.linalg.norm(y)
    z /= np.linalg.norm(z)
    x = np.cross(y, z)
    return np.stack([x, y, z], axis=1)


def aim(scene, preset, cam_info):
    """Put the rig on the preset's subject (its look-at target, else the standing figure) scaled to the
    view, turn it with the camera, set the light powers, and show the stage props only for spec 16 and
    17's presets. Returns what it set, for the render's sidecar."""
    import bpy
    from mathutils import Matrix
    rig = bpy.data.objects.get("LookDev.Rig")
    if rig is None:
        return None
    cam = scene.camera
    pos = np.array(cam.matrix_world.translation)
    up = np.array(cam.matrix_world.to_3x3().col[1])
    if cam_info.get("target") is not None:
        target = np.asarray(cam_info["target"], float)
        dist = np.linalg.norm(target - pos)
        if cam.data.type == "ORTHO":
            radius = cam.data.ortho_scale / 2.0
        else:
            radius = dist * (cam.data.sensor_width / 2.0) / cam.data.lens
    else:   # hero-style views: the whole figure
        target, radius = np.array([0.0, 0.0, 0.93]), 1.0
    s = max(radius / 0.5, 0.02)
    R = _frame(pos, target, up)
    M = np.eye(4)
    M[:3, :3], M[:3, 3] = R * s, target
    rig.matrix_world = Matrix(M.tolist())
    for ob in rig.children:
        if ob.type == "LIGHT":
            ob.data.energy = float(ob.data["power_w_at_s1"]) * s * s
    # the cyclorama turns about the subject with the camera too, so a side or back view still has the
    # seamless wall behind it instead of looking past the cove into the studio HDRI
    cyc = bpy.data.objects.get("LookDev.Stage.Cyc")
    if cyc is not None:
        h = R[:2, 1] if np.linalg.norm(R[:2, 1]) > 0.2 else R[:2, 2]
        yaw = math.atan2(-h[0], h[1])
        cyc.matrix_world = Matrix.Translation((float(target[0]), float(target[1]), 0.0)) @ Matrix.Rotation(yaw, 4, "Z")
    stage = str(preset.get("owner")) in STAGE_OWNERS
    for name in ("LookDev.Cal", "LookDev.Swatch", "Lib.Test"):
        coll = bpy.data.collections.get(name)
        if coll is not None:
            coll.hide_render = not stage
    return {"rig_target_m": [round(float(v), 4) for v in target], "rig_scale": round(float(s), 4),
            "mode": "full" if R[2, 2] < 0.999 else "yaw", "stage": stage}


# --------------------------------------------------------------------------- calibration and checks

def _render_mean(scene, path):
    """Render the scene to a small float EXR and return the mean RGB of its centre (scene-linear)."""
    import bpy
    r = scene.render
    r.image_settings.file_format, r.image_settings.color_depth = "OPEN_EXR", "32"
    r.filepath = path
    bpy.ops.render.render(write_still=True, scene=scene.name)
    img = bpy.data.images.load(path, check_existing=False)
    try:
        img.colorspace_settings.name = "Non-Color"
        w, h = img.size
        a = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(a)
        a = a.reshape(h, w, 4)[h // 4: 3 * h // 4, w // 4: 3 * w // 4, :3]
        return a.reshape(-1, 3).mean(axis=0)
    finally:
        bpy.data.images.remove(img)


def calibrate(scene=None, write=True):
    """One light at a time, the 18 % card turned to face it at the rig centre (s = 1), everything else
    hidden and the world off: each light's power is scaled until the card reads its target."""
    import bpy
    from mathutils import Matrix, Vector
    from eval import render
    scene = ensure() if scene is None else scene
    rig = bpy.data.objects["LookDev.Rig"]
    card = bpy.data.objects["Cal.Card18"]
    lights = [o for o in rig.children if o.type == "LIGHT"]
    saved = {"card": card.matrix_world.copy(), "cam": scene.camera, "res": (scene.render.resolution_x,
             scene.render.resolution_y, scene.render.resolution_percentage),
             "hide": {o.name: o.hide_render for o in scene.objects}, "strength": None}
    bg = scene.world.node_tree.nodes.get("Background")
    saved["strength"] = bg.inputs["Strength"].default_value
    tmp_cam = bpy.data.objects.new("LookDev.CalCam", bpy.data.cameras.new("LookDev.CalCam"))
    scene.collection.objects.link(tmp_cam)
    out = {}
    try:
        render._set_tier(scene, "look")
        c = scene.cycles
        c.samples, c.use_adaptive_sampling, c.use_denoising = 256, False, False
        scene.render.resolution_x = scene.render.resolution_y = 32
        scene.render.resolution_percentage = 100
        bg.inputs["Strength"].default_value = 0.0
        rig.matrix_world = Matrix.Translation(STAND)
        for o in scene.objects:
            o.hide_render = o not in lights and o not in (card, tmp_cam)
        bpy.context.view_layer.update()
        for L in lights:
            for o in lights:
                o.hide_render = o != L
            to_light = (L.matrix_world.translation - Vector(STAND)).normalized()
            q = Vector((0.0, -1.0, 0.0)).rotation_difference(to_light)   # the card's normal is -Y
            card.matrix_world = Matrix.Translation(STAND) @ q.to_matrix().to_4x4()
            tmp_cam.data.type, tmp_cam.data.ortho_scale = "ORTHO", 0.06
            look = (-to_light).to_track_quat("-Z", "Z")
            tmp_cam.matrix_world = Matrix.Translation(Vector(STAND) + to_light * 0.5) @ look.to_matrix().to_4x4()
            scene.camera = tmp_cam
            bpy.context.view_layer.update()
            p_trial = float(L.data["power_w_at_s1"])
            L.data.energy = p_trial
            mean = _render_mean(scene, os.path.join(env.CACHE_DIR, "lookdev_cal.exr"))
            read = float(mean.mean())
            want = LIGHTS[L.name]["target"]
            out[L.name] = {"power": round(p_trial * want / read, 3), "read_at_trial": round(read, 5),
                           "trial_w": p_trial, "rgb": [round(float(v), 5) for v in mean]}
    finally:
        card.matrix_world = saved["card"]
        scene.camera = saved["cam"]
        r = scene.render
        r.resolution_x, r.resolution_y, r.resolution_percentage = saved["res"]
        for name, h in saved["hide"].items():
            if name in scene.objects:
                scene.objects[name].hide_render = h
        bg.inputs["Strength"].default_value = saved["strength"]
        bpy.data.objects.remove(tmp_cam)
    powers = {k: v["power"] for k, v in out.items()}
    for L in lights:
        L.data["power_w_at_s1"] = powers[L.name]
        L.data.energy = powers[L.name]
    if write:
        with open(CAL_JSON, "w", encoding="utf-8") as f:
            json.dump({"doc": "LookDev light powers at rig scale 1 (spec 17 §4.8), written by lookdev.py --calibrate: "
                              "with one light on and the world off, the 18 % Lambertian card facing it reads the target",
                       "power_w_at_s1": powers, "measured": out,
                       "targets": {k: v["target"] for k, v in LIGHTS.items()},
                       "written": time.strftime("%Y-%m-%d %H:%M"), "device": env.device()}, f, indent=1)
            f.write("\n")
    return out


# --------------------------------------------------------------------------- command line

def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--build", action="store_true", help="add LookDev to the scene file and save it")
    ap.add_argument("--calibrate", action="store_true", help="measure the light powers into lookdev.json")
    ap.add_argument("--swatch", help="spec 16 recipe ids, comma-separated: render their swatch views")
    ap.add_argument("--views", default="", help="swatch views (default per family), e.g. V1,V2,V7")
    ap.add_argument("--render", help="preset ids to render in LookDev, comma-separated")
    ap.add_argument("--tier", default="look")
    ap.add_argument("--samples", type=int)
    ap.add_argument("--blend", default=os.path.relpath(env.path("cache", "scene_eval.blend"), env.PROJECT_DIR),
                    help="the scene file to add LookDev to (--build) or open (default cache/scene_eval.blend)")
    ap.add_argument("--empty", action="store_true", help="start from an empty file instead of --blend")
    a = ap.parse_args(argv)
    if not camera.in_blender():
        blend = env.path(a.blend)
        return camera.run_in_blender(__file__, argv, None if a.empty or not os.path.exists(blend) else blend)
    import bpy
    t0 = time.time()
    res = {}
    if bpy.data.scenes.get(SCENE) is None or a.build:
        char = next((c for c in (bpy.data.collections.get(n) for n in ("Character", "Body")) if c is not None), None)
        res["build"] = build(bpy.data.scenes.get(SCENE), character=char)
    scene = bpy.data.scenes[SCENE]
    if bpy.context.window is not None:
        bpy.context.window.scene = scene
    if a.calibrate:
        res["calibrate"] = calibrate(scene)
    if a.swatch:
        from lib import materials as M
        views = tuple(v for v in a.views.split(",") if v) or None
        res["swatch"] = {rid: M.swatch(rid, views=views, tier=a.tier, samples=a.samples) for rid in a.swatch.split(",")}
    if a.render:
        from eval import render
        res["render"] = []
        for pid in a.render.split(","):
            side = render.render_preset(pid, tier=a.tier, samples=a.samples, scene_name="lookdev")
            res["render"].append({"preset": side["preset"], "seconds": side["seconds"], "png": side["outputs"]["png"]})
    if a.build:
        out = env.path(a.blend)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
        res["saved"] = os.path.relpath(out, env.PROJECT_DIR).replace(os.sep, "/")
    res["seconds"] = round(time.time() - t0, 2)
    print("RESULT " + json.dumps(res, default=str), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(camera.script_args()))
