"""The hero camera, the equivalent crop camera and the preset registry (spec 17 §4.3, spec 18 §4.8.2).

`Scene.Cam.Hero` is built here and nowhere else. Every other view (a crop, a look-at closeup, an ortho
measurement) goes on one reusable camera, `Scene.Cam.Preset`, so a preset render never disturbs the
hero camera. A crop of the hero frame is rendered through the equivalent crop camera (same centre of
projection and rotation, lens x W / w, lens shift), which renders only the crop's pixels; the render
border of spec 17 remains as `mode="border"` for comparison.

The registry is JSON (`presets/*.json`, one file per part) and loads without bpy, so the sheet and
overlay tools read the same boxes the renders use. Preset keys are spec 17's schema: id, label, scene
(hero | lookdev | form), camera {type (hero | look_at | ortho | ray | turntable), frame (W or an
object), mirror_x, pos_mm, target_mm, up, lens_mm, sensor_mm, ortho_scale_mm, anchor, distance_mm,
n, elev_deg}, dof {fstop, focus}, render {res, border_px, scale, tier, film_transparent}, compare,
owner. Added here: alias (this view is that preset; its own label, compare, mask, hide and note
win), sides (["L", "R"]: expand to id.L and id.R, "{side}" and "{other}" in the frame, anchor and
hide names, the sides after the first mirrored in X), hide (object or collection name patterns
hidden for the view, e.g. the other boot in a medial view), mask (names of reference masks the
sheets outline, ref/masks/<name>.png), form (Workbench overrides: light, color, background, cavity)
and note. Names: the id, pNN.<label> and id.<label>, each with .L/.R for sided views; the bare id of
a sided view means its first side.

  blender -b [cache/scene_eval.blend] --python scripts/eval/camera.py -- --selftest | --lint [--strict]
  python scripts/eval/camera.py --lint | --list | --show ID     (no Blender needed)
"""
import argparse
import copy
import fnmatch
import glob
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(HERE))  # scripts/, for `from lib import ...`
from lib import env  # noqa: E402
from eval import camproj  # noqa: E402

PRESET_DIR = os.path.join(HERE, "presets")
HERO_NAME, FOCUS_NAME, PRESET_NAME, CAM_COLL = "Scene.Cam.Hero", "Scene.Cam.Focus", "Scene.Cam.Preset", "Scene.Cam"
TYPES = ("hero", "look_at", "ortho", "ray", "turntable")
SCENES = ("hero", "lookdev", "form")
TIERS = ("form", "look", "eval", "cal", "final")
KEYS = {"id", "label", "scene", "camera", "dof", "render", "compare", "owner", "alias", "sides", "hide",
        "mask", "form", "note"}
CAMERA_KEYS = {"type", "frame", "mirror_x", "pos_mm", "target_mm", "up", "lens_mm", "sensor_mm",
               "ortho_scale_mm", "anchor", "distance_mm", "n", "elev_deg"}
RENDER_KEYS = {"res", "border_px", "scale", "tier", "film_transparent"}
FORM_KEYS = {"light", "color", "background", "cavity"}
# render folders as the specs name them (renders/<part>/)
PART_DIRS = {"01": "01_foot", "02": "02_boots", "03": "03_leg_pelvis", "04": "04_torso", "05": "05_arm_hand",
             "06": "06_head", "07": "07_hair", "08": "08_rig", "09": "09_combat_trousers",
             "10": "10_combat_shirt_gaiter", "11": "11_gloves", "12": "12_hard_armour", "13": "13_plate_carrier",
             "14": "14_belt_leg_rigs", "15": "15_carbine", "16": "16_materials", "17": "17_scene",
             "18": "18_pipeline"}


class MissingObject(LookupError):
    """A preset needs an object (a part's frame or anchor) that the open scene does not have."""


def part_dir(owner):
    owner = str(owner or "17")
    return os.path.join(env.RENDERS_DIR, PART_DIRS.get(owner, f"p{owner}"))


# --------------------------------------------------------------------------- registry (no bpy)

def _expand_sides(raw):
    sides = raw.get("sides")
    if not sides:
        return [raw]
    out = []
    for i, s in enumerate(sides):
        p = copy.deepcopy(raw)
        del p["sides"]
        p.update(id=f"{raw['id']}.{s}", side=s, side_index=i, base_id=raw["id"])
        other = {"L": "R", "R": "L"}.get(s, s)

        def sub(t):
            return t.replace("{side}", s).replace("{other}", other)

        cam = p.setdefault("camera", {})
        for k in ("frame", "anchor"):
            if isinstance(cam.get(k), str):
                cam[k] = sub(cam[k])
        p["hide"] = [sub(h) for h in p.get("hide") or []]
        if i > 0:  # the spec's coordinates are written for the first side
            cam["mirror_x"] = not cam.get("mirror_x", False)
        out.append(p)
    return out


def _names(p):
    pid, label, side = p["id"], p.get("label"), p.get("side")
    base = p.get("base_id", pid)
    prefix = base.split(".")[0]
    names = [pid]
    if label:
        names += [f"{prefix}.{label}" + (f".{side}" if side else ""), f"{base}.{label}" + (f".{side}" if side else "")]
    if side and p.get("side_index") == 0:
        names += [base] + ([f"{prefix}.{label}"] if label else [])
    return names


def _defaults(p):
    p.setdefault("scene", "hero")
    cam = p.setdefault("camera", {})
    cam.setdefault("type", "hero")
    cam.setdefault("frame", "W")
    cam.setdefault("mirror_x", False)
    cam.setdefault("up", [0, 0, 1])
    cam.setdefault("sensor_mm", camproj.SENSOR_MM)
    r = p.setdefault("render", {})
    r.setdefault("scale", 1)
    r.setdefault("tier", "eval")
    r.setdefault("film_transparent", p["scene"] == "hero")
    for k in ("compare", "hide", "mask"):
        p[k] = list(p.get(k) or [])
    return p


class Registry:
    """Every preset of presets/*.json by id, with the alias names of the module doc."""

    def __init__(self, files=None):
        self.presets, self.names, self.files, self.problems = {}, {}, [], []
        for path in files or sorted(glob.glob(os.path.join(PRESET_DIR, "*.json"))):
            self._load(path)

    def _load(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            self.problems.append(("error", os.path.basename(path), f"cannot read: {e}"))
            return
        self.files.append(path)
        for raw in data.get("presets", []):
            raw = dict(raw)
            raw.setdefault("owner", data.get("owner"))
            raw["file"] = os.path.relpath(path, env.PROJECT_DIR).replace(os.sep, "/")
            if "id" not in raw:
                self.problems.append(("error", raw["file"], f"preset without an id: {raw}"))
                continue
            for p in _expand_sides(raw):
                if p["id"] in self.presets:
                    self.problems.append(("error", p["id"], f"defined twice ({self.presets[p['id']]['file']}, {p['file']})"))
                    continue
                self.presets[p["id"]] = p
                for n in _names(p):
                    if self.names.setdefault(n, p["id"]) != p["id"]:
                        self.problems.append(("warning", p["id"], f"name {n!r} already means {self.names[n]}"))

    def ids(self):
        return list(self.presets)

    def owner_ids(self, owner):
        return [i for i, p in self.presets.items() if str(p.get("owner")) == str(owner)]

    def get(self, name):
        """The preset a name means, aliases followed and defaults filled, as a fresh copy."""
        pid = self.names.get(name, name if name in self.presets else None)
        if pid is None:
            raise KeyError(f"unknown preset {name!r} (camera.py --list shows the registry)")
        p, seen = copy.deepcopy(self.presets[pid]), [pid]
        while "alias" in p:
            tid = self.names.get(p["alias"])
            if tid is None:
                raise KeyError(f"{pid}: alias {p['alias']!r} is not in the registry")
            if tid in seen:
                raise ValueError("alias loop: " + " -> ".join(seen + [tid]))
            seen.append(tid)
            own = {k: v for k, v in p.items() if k in ("id", "label", "owner", "file", "note", "compare", "mask", "hide")}
            p = copy.deepcopy(self.presets[tid])
            p.update(own)
            p["alias_of"] = tid
        return _defaults(p)


def load_registry(files=None):
    return Registry(files)


def _vec(v, n=3):
    return isinstance(v, (list, tuple)) and len(v) == n and all(isinstance(x, (int, float)) for x in v)


def check(p):
    """Errors and warnings of one resolved preset, without Blender."""
    E, Wn = [], []
    for k in set(p) - KEYS - {"file", "side", "side_index", "base_id", "alias_of"}:
        Wn.append(f"unknown key {k!r}")
    cam, r = p["camera"], p["render"]
    for k in set(cam) - CAMERA_KEYS:
        Wn.append(f"unknown camera key {k!r}")
    for k in set(r) - RENDER_KEYS:
        Wn.append(f"unknown render key {k!r}")
    for k in set(p.get("form") or {}) - FORM_KEYS:
        Wn.append(f"unknown form key {k!r}")
    if p["scene"] not in SCENES:
        E.append(f"scene {p['scene']!r} not in {SCENES}")
    kind = cam["type"]
    if kind not in TYPES:
        E.append(f"camera type {kind!r} not in {TYPES}")
    if r["tier"] not in TIERS:
        E.append(f"tier {r['tier']!r} not in {TIERS}")
    if not (isinstance(r["scale"], (int, float)) and r["scale"] > 0):
        E.append(f"scale {r['scale']!r} must be positive")
    if kind == "hero":
        box = r.get("border_px")
        if box is not None:
            try:
                camproj.check_box(box)
                camproj.box_size(box, r["scale"])
            except (ValueError, TypeError) as e:
                E.append(str(e))
    else:
        if not (isinstance(r.get("res"), (list, tuple)) and len(r["res"]) == 2 and all(isinstance(v, int) and v > 0 for v in r["res"])):
            E.append(f"{kind} needs render.res [w, h] in whole pixels")
        if kind in ("look_at", "ortho"):
            if not (_vec(cam.get("pos_mm")) and _vec(cam.get("target_mm")) and _vec(cam.get("up"))):
                E.append(f"{kind} needs pos_mm, target_mm and up as 3-vectors")
            else:
                try:
                    camproj.look_at_matrix(cam["pos_mm"], cam["target_mm"], cam["up"])
                except ValueError as e:
                    E.append(str(e))
        if kind in ("look_at", "ray", "turntable") and not (cam.get("lens_mm") or 0) > 0:
            E.append(f"{kind} needs lens_mm")
        if kind == "ortho" and not (cam.get("ortho_scale_mm") or 0) > 0:
            E.append("ortho needs ortho_scale_mm")
        if kind == "ray" and not (isinstance(cam.get("anchor"), str) and (cam.get("distance_mm") or 0) > 0):
            E.append("ray needs anchor and distance_mm")
        if kind == "turntable" and not ((cam.get("n") or 0) >= 1 and (cam.get("distance_mm") or 0) > 0):
            E.append("turntable needs n and distance_mm")
    dof = p.get("dof")
    if dof:
        if not (dof.get("fstop") or 0) > 0:
            E.append("dof needs fstop")
        f = dof.get("focus", "target")
        if not (isinstance(f, str) or _vec(f)):
            E.append("dof.focus is 'target', an object name or a 3-vector in mm")
    for c in p["compare"]:
        if not os.path.exists(env.path(c)):
            E.append(f"compare file {c} is missing")
    return E, Wn


def lint(reg=None, strict=False):
    """Resolve every preset; inside Blender also check the frames and anchors the open scene has."""
    reg = reg or load_registry()
    out = {"files": [os.path.basename(f) for f in reg.files], "presets": len(reg.presets), "errors": [], "warnings": []}
    for level, pid, msg in reg.problems:
        out[level + "s"].append(f"{pid}: {msg}")
    bpy = _bpy()
    for pid in reg.ids():
        try:
            p = reg.get(pid)
        except (KeyError, ValueError) as e:
            out["errors"].append(f"{pid}: {e}")
            continue
        E, Wn = check(p)
        out["errors"] += [f"{pid}: {e}" for e in E]
        out["warnings"] += [f"{pid}: {w}" for w in Wn]
        if bpy is not None:
            cam = p["camera"]
            for need in (cam.get("frame"), cam.get("anchor")):
                if need and need != "W" and need not in bpy.data.objects:
                    msg = f"{pid}: object {need!r} is not in this scene (built by part {p.get('owner')})"
                    out["errors" if strict else "warnings"].append(msg)
    return out


# --------------------------------------------------------------------------- Blender side

def _bpy():
    try:
        import bpy
        return bpy
    except ImportError:
        return None


def _collection(scene, name):
    import bpy
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c not in scene.collection.children_recursive:
        scene.collection.children.link(c)
    return c


def _ensure_camera_object(name, coll):
    import bpy
    data = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, data)
    elif ob.data != data:
        ob.data = data
    if ob.name not in coll.objects:
        coll.objects.link(ob)
    ob.parent = None
    ob.rotation_mode = "XYZ"
    ob.scale = (1.0, 1.0, 1.0)
    return ob


def hero_camera(scene=None, dof=False):
    """`Scene.Cam.Hero` and `Scene.Cam.Focus` with spec 17 §4.3's values (idempotent: an existing hero
    camera is reset to them). Depth of field is off under the scope note: at f/1.5 focused at 4.5 m the
    blur on the figure is about one pixel or less, so it only ever affected the deferred background."""
    import bpy
    scene = scene or bpy.context.scene
    coll = _collection(scene, CAM_COLL)
    focus = bpy.data.objects.get(FOCUS_NAME) or bpy.data.objects.new(FOCUS_NAME, None)
    if focus.name not in coll.objects:
        coll.objects.link(focus)
    focus.empty_display_size = 0.05
    focus.location = camproj.FOCUS
    ob = _ensure_camera_object(HERO_NAME, coll)
    ob.location = camproj.HERO_LOC
    ob.rotation_euler = [math.radians(a) for a in camproj.HERO_ROT_DEG]
    # matrix_world too: it is otherwise stale until the next depsgraph update, and the crop camera copies it
    from mathutils import Euler, Matrix, Vector
    ob.matrix_world = Matrix.LocRotScale(Vector(camproj.HERO_LOC), Euler(ob.rotation_euler, "XYZ"), Vector((1.0, 1.0, 1.0)))
    cam = ob.data
    cam.type = "PERSP"
    cam.lens, cam.sensor_width, cam.sensor_fit = camproj.LENS_MM, camproj.SENSOR_MM, "HORIZONTAL"
    cam.shift_x = cam.shift_y = 0.0
    cam.clip_start, cam.clip_end = camproj.CLIP
    cam.dof.use_dof = dof
    cam.dof.focus_object = focus
    cam.dof.aperture_fstop, cam.dof.aperture_blades, cam.dof.aperture_ratio = 1.5, 0, 1.0
    scene.camera = ob
    r = scene.render
    r.resolution_x, r.resolution_y, r.pixel_aspect_x, r.pixel_aspect_y = camproj.W, camproj.H, 1.0, 1.0
    return ob


def preset_camera(scene=None):
    """The one reusable camera every non-hero view is placed on."""
    import bpy
    scene = scene or bpy.context.scene
    return _ensure_camera_object(PRESET_NAME, _collection(scene, CAM_COLL))


def _frame_matrix(p):
    import bpy
    name = p["camera"].get("frame", "W")
    if name in (None, "W"):
        return np.eye(4)
    ob = bpy.data.objects.get(name)
    if ob is None:
        raise MissingObject(f"{p['id']}: frame object {name!r} is not in this scene (built by part {p.get('owner')})")
    return np.array(ob.matrix_world)


def frame_point(p, v_mm):
    """A point given in mm in the preset's frame (mirrored in X first if mirror_x), in world metres."""
    M = _frame_matrix(p)
    sign = np.array([-1.0 if p["camera"].get("mirror_x") else 1.0, 1.0, 1.0])
    return M[:3, :3] @ (np.asarray(v_mm, float) / 1000.0 * sign) + M[:3, 3]


def placement(p, view=0):
    """World position, target and up (metres) of a non-hero preset's camera; view picks a turntable view."""
    import bpy
    cam, kind = p["camera"], p["camera"]["type"]
    M = _frame_matrix(p)
    sign = np.array([-1.0 if cam.get("mirror_x") else 1.0, 1.0, 1.0])

    def point(v):
        return frame_point(p, v)

    up = M[:3, :3] @ (np.asarray(cam.get("up", [0, 0, 1]), float) * sign)
    if kind in ("look_at", "ortho"):
        return point(cam["pos_mm"]), point(cam["target_mm"]), up
    if kind == "ray":  # along the anchor's ray to the hero camera, so the view matches the hero's angle
        ob = bpy.data.objects.get(cam["anchor"])
        if ob is None:
            raise MissingObject(f"{p['id']}: anchor {cam['anchor']!r} is not in this scene (built by part {p.get('owner')})")
        A = np.array(ob.matrix_world.translation)
        d = np.asarray(camproj.HERO_LOC) - A
        return A + d / np.linalg.norm(d) * cam["distance_mm"] / 1000.0, A, np.array([0.0, 0.0, 1.0])
    if kind == "turntable":  # orbiting camera: view 0 in front (-Y), then toward his left (+X)
        n, el = int(cam["n"]), math.radians(cam.get("elev_deg") or 0.0)
        az = 2.0 * math.pi * (view % n) / n
        target = point(cam.get("target_mm", [0, 0, 0]))
        d = np.array([math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)])
        return target + d * cam["distance_mm"] / 1000.0, target, np.array([0.0, 0.0, 1.0])
    raise ValueError(f"{p['id']}: no placement for camera type {kind!r}")


def views(p):
    """How many renders a preset makes (a turntable makes n)."""
    return int(p["camera"].get("n") or 1) if p["camera"]["type"] == "turntable" else 1


def apply(preset, scene=None, mode="equiv", percent=100, view=0, registry=None):
    """Place the camera and set the resolution for a preset; returns what was set, for the sidecar.

    mode "equiv" renders a box of the hero frame through the equivalent crop camera (spec 18 §4.8.2),
    "border" through the hero camera with a render border (spec 17 §4.3). percent is the tier's
    resolution percentage, applied on top of the preset's scale.
    """
    import bpy
    from mathutils import Matrix
    p = preset if isinstance(preset, dict) else (registry or load_registry()).get(preset)
    scene = scene or bpy.context.scene
    r = scene.render
    cam, R = p["camera"], p["render"]
    hero = hero_camera(scene, dof=hero_dof(scene))
    r.use_border = r.use_crop_to_border = False
    r.pixel_aspect_x = r.pixel_aspect_y = 1.0
    s = R.get("scale", 1)
    info = {"type": cam["type"]}
    if cam["type"] == "hero":
        box = R.get("border_px")
        if not box:
            scene.camera = hero
            r.resolution_x, r.resolution_y, r.resolution_percentage = camproj.W, camproj.H, round(percent * s)
            info.update(mode="hero", camera=HERO_NAME)
        elif mode == "border":
            b = camproj.border_params(box)
            scene.camera = hero
            r.resolution_x, r.resolution_y, r.resolution_percentage = camproj.W, camproj.H, round(percent * s)
            r.use_border = r.use_crop_to_border = True
            r.border_min_x, r.border_max_x, r.border_min_y, r.border_max_y = b["min_x"], b["max_x"], b["min_y"], b["max_y"]
            info.update(mode="border", camera=HERO_NAME, box=list(box), scale=s)
        else:
            cp = camproj.crop_params(box, s)
            ob = preset_camera(scene)
            ob.matrix_world = hero.matrix_world.copy()
            c, h = ob.data, hero.data
            c.type, c.lens, c.sensor_width, c.sensor_fit = "PERSP", cp["lens"], cp["sensor"], cp["fit"]
            c.shift_x, c.shift_y = cp["shift_x"], cp["shift_y"]
            c.clip_start, c.clip_end = h.clip_start, h.clip_end
            c.dof.use_dof = h.dof.use_dof
            if h.dof.use_dof:  # keep the entrance pupil: the f-number scales with the focal length
                c.dof.focus_object = h.dof.focus_object
                c.dof.aperture_fstop = h.dof.aperture_fstop * cp["lens"] / h.lens
                c.dof.aperture_blades, c.dof.aperture_ratio = h.dof.aperture_blades, h.dof.aperture_ratio
            scene.camera = ob
            r.resolution_x, r.resolution_y = cp["res"]
            r.resolution_percentage = percent
            info.update(mode="equiv", camera=PRESET_NAME, box=list(box), scale=s, lens=round(cp["lens"], 4),
                        shift=[round(cp["shift_x"], 5), round(cp["shift_y"], 5)])
    else:
        pos, target, up = placement(p, view)
        Rm = camproj.look_at_matrix(pos, target, up)
        ob = preset_camera(scene)
        M = np.eye(4)
        M[:3, :3], M[:3, 3] = Rm, pos
        ob.matrix_world = Matrix(M.tolist())
        c = ob.data
        if cam["type"] == "ortho":
            c.type, c.ortho_scale = "ORTHO", cam["ortho_scale_mm"] / 1000.0
        else:
            c.type, c.lens = "PERSP", float(cam["lens_mm"])
        c.sensor_width, c.sensor_fit = float(cam.get("sensor_mm", camproj.SENSOR_MM)), "HORIZONTAL"
        c.shift_x = c.shift_y = 0.0
        c.clip_start, c.clip_end = 0.01, camproj.CLIP[1]
        dof = p.get("dof")
        c.dof.use_dof = bool(dof)
        if dof:
            f = dof.get("focus", "target")
            c.dof.focus_object = None
            if f == "target":
                c.dof.focus_distance = float(np.linalg.norm(target - pos))
            elif isinstance(f, str):
                fo = bpy.data.objects.get(f)
                if fo is None:
                    raise MissingObject(f"{p['id']}: focus object {f!r} is not in this scene")
                c.dof.focus_object = fo
            else:
                c.dof.focus_distance = float(np.linalg.norm(frame_point(p, f) - pos))
            c.dof.aperture_fstop = float(dof["fstop"])
        scene.camera = ob
        r.resolution_x, r.resolution_y = R["res"]
        r.resolution_percentage = round(percent * s)
        info.update(mode=cam["type"], camera=PRESET_NAME, pos=[round(v, 4) for v in pos],
                    target=[round(v, 4) for v in target], frame=cam.get("frame"), mirror_x=bool(cam.get("mirror_x")))
        if cam["type"] == "turntable":
            info["view"] = view
    info["res"] = [round(r.resolution_x * r.resolution_percentage / 100), round(r.resolution_y * r.resolution_percentage / 100)]
    if r.use_border:
        b = R["border_px"]
        info["res"] = [round((b[2] - b[0]) * r.resolution_percentage / 100), round((b[3] - b[1]) * r.resolution_percentage / 100)]
    return info


def hero_dof(scene):
    """Keep whatever depth of field the scene's hero camera has (off unless someone switched it on)."""
    import bpy
    ob = bpy.data.objects.get(HERO_NAME)
    return bool(ob and ob.type == "CAMERA" and ob.data.dof.use_dof)


def hidden(patterns, scene=None):
    """Objects and collections matching name patterns, for a preset's `hide` list."""
    import bpy
    scene = scene or bpy.context.scene
    obs = [o for o in scene.objects if any(fnmatch.fnmatchcase(o.name, pat) for pat in patterns)]
    colls = [c for c in scene.collection.children_recursive if any(fnmatch.fnmatchcase(c.name, pat) for pat in patterns)]
    return obs, colls


def selftest(scene=None):
    """camproj against Blender's own projection (spec 17 §1.4 item 1; spec 18 §8.4 items 1-2)."""
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    R = {"camproj": camproj.selftest()}
    scene = scene or bpy.context.scene
    r = scene.render
    saved = (scene.camera, r.resolution_x, r.resolution_y, r.resolution_percentage, r.use_border, r.use_crop_to_border)
    reg = load_registry()
    hero = hero_camera(scene, dof=hero_dof(scene))
    rng = np.random.default_rng(17)
    xy = rng.uniform([0.0, 0.0], [camproj.W, camproj.H], (20, 2))
    o, d = camproj.HERO.ray(xy)
    P = o + d * rng.uniform(2.0, 12.0, 20)[:, None]  # 20 points spread over the frame at 2-12 m

    def blender_px(cam_ob):
        res = (r.resolution_x * r.resolution_percentage / 100.0, r.resolution_y * r.resolution_percentage / 100.0)
        out = []
        for p in P:
            v = world_to_camera_view(scene, cam_ob, Vector(p))
            out.append((v.x * res[0], (1.0 - v.y) * res[1]))
        return np.array(out)

    try:
        apply(reg.get("ref.full"), scene)
        err = np.abs(blender_px(hero) - camproj.HERO.project(P)).max()
        R["hero_max_err_px"] = round(float(err), 5)
        assert err <= 0.1, f"hero camera: camproj and world_to_camera_view differ by {err:.3f} px"
        R["crop_max_err_px"] = {}
        for name in ("ref.head_face", "ref.boots_feet", "ref.soldier_full", "p02.V2"):
            p = reg.get(name)
            apply(p, scene)
            box, s = p["render"]["border_px"], p["render"]["scale"]
            err = np.abs(blender_px(scene.camera) - camproj.to_crop(camproj.HERO.project(P), box, s)).max()
            R["crop_max_err_px"][name] = round(float(err), 5)
            assert err <= 0.1 * s, f"{name}: crop camera off by {err:.3f} px at scale {s}"
        p = reg.get("hero.alt50")
        apply(p, scene)
        ob = scene.camera
        pitch = math.degrees(ob.matrix_world.to_euler("XYZ").x)
        R["alt50_pitch_deg"] = round(pitch, 4)
        assert abs(pitch - camproj.HERO_ROT_DEG[0]) < 1e-3, pitch
        cam = camproj.Camera.blender(np.array(ob.matrix_world.translation), np.array(ob.matrix_world.to_3x3()),
                                     r.resolution_x, r.resolution_y, ob.data.lens, ob.data.sensor_width)
        err = np.abs(blender_px(ob) - cam.project(P)).max()
        R["look_at_max_err_px"] = round(float(err), 5)
        assert err <= 0.1, f"look_at camera off by {err:.3f} px"
    finally:
        scene.camera = saved[0]
        r.resolution_x, r.resolution_y, r.resolution_percentage, r.use_border, r.use_crop_to_border = saved[1:]
    return R


# --------------------------------------------------------------------------- command line

def in_blender():
    return _bpy() is not None


def script_args():
    """This script's arguments: after '--' inside Blender, else the whole command line."""
    if in_blender():
        return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return sys.argv[1:]


def run_in_blender(script, args, blend=None):
    """Re-run a script inside background Blender with the project's user resources; the exit code."""
    argv = ["-b"] + ([blend] if blend else []) + ["--python-exit-code", "1", "--python", os.path.abspath(script), "--"] + list(args)
    return env.run_blender(argv).returncode


def _describe(p):
    cam, r = p["camera"], p["render"]
    if cam["type"] == "hero":
        box = r.get("border_px")
        what = f"box {tuple(box)} x{r['scale']} -> {camproj.box_size(box, r['scale'])}" if box else "full frame"
    else:
        what = f"{cam['type']} {cam.get('frame', 'W')}{' mirrored' if cam.get('mirror_x') else ''} {tuple(r.get('res', ()))}"
    alias = f" = {p['alias_of']}" if "alias_of" in p else ""
    return f"{p['id']:<14} {p.get('label', ''):<22} {p['scene']:<8} {what}{alias}"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--list", action="store_true", help="list every preset")
    ap.add_argument("--show", metavar="NAME", help="print one resolved preset")
    ap.add_argument("--lint", action="store_true", help="resolve every preset (and its frames inside Blender)")
    ap.add_argument("--strict", action="store_true", help="with --lint: a missing frame object is an error")
    ap.add_argument("--selftest", action="store_true", help="camproj against Blender's projection")
    a = ap.parse_args(argv)
    reg = load_registry()
    code = 0
    if a.list:
        for pid in reg.ids():
            try:
                print(_describe(reg.get(pid)))
            except (KeyError, ValueError) as e:
                print(f"{pid:<14} ERROR {e}")
    if a.show:
        print(json.dumps(reg.get(a.show), indent=1))
    if a.lint:
        res = lint(reg, a.strict)
        for e in res["errors"]:
            print("ERROR  ", e)
        for w in res["warnings"]:
            print("warning", w)
        print(f"lint: {res['presets']} presets in {len(res['files'])} files, {len(res['errors'])} errors, {len(res['warnings'])} warnings")
        code = 1 if res["errors"] else code
    if a.selftest:
        if in_blender():
            print(json.dumps(selftest(), indent=1))
            print("camera selftest: ok")
        else:
            code = run_in_blender(__file__, ["--selftest"]) or code
    return code


if __name__ == "__main__":
    sys.exit(main(script_args()))
