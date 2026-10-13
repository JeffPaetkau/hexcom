"""Shared ground for the high-resolution foot trial (notes/research_foot_hires.md): the default build's left
foot as a dense render copy, frame F, the joints of the region's toes, the trial's camera presets, the
materials and the contact sheets.

Nothing here writes outside the session, cache/research/foot_hires/ and renders/research/foot_hires/: the
trial reads part 01's layers and cache the way scripts/eval/lookdev_p01.py does and never saves a .blend.

Run inside Blender on cache/body/rigged.blend (run.py is the entry point).
"""
import importlib.util
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(os.path.dirname(HERE))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
from lib import env  # noqa: E402

OUT = env.path("renders", "research", "foot_hires")
CACHE = env.path("cache", "research", "foot_hires")
PART_SCRIPT = env.path("scripts", "parts", "01_foot_ankle_sock.py")
PRESETS = os.path.join(HERE, "presets.json")
SIDE = "L"          # the trial works on the soldier's left foot (+X), frame F unmirrored
PREFIX = "Hires."   # the trial's own objects; nothing of a part's prefixes
MM = 1000.0


# --------------------------------------------------------------------------- the build

def part_module():
    """Part 01's script as a module (its name starts with a digit, so it cannot be imported by name)."""
    spec = importlib.util.spec_from_file_location("part01_hires", PART_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def open_build():
    """Body.Mesh with part 01's layers put back and the part cache appended (nails, frames): the foot a
    `--rebuild` of part 01 made. Returns (part module, body)."""
    import bpy
    from lib import cache
    from parts.p01 import layers
    part = part_module()
    body = bpy.data.objects["Body.Mesh"]
    if not layers.apply(part.PART, body):
        raise RuntimeError("part 01's layer cache is missing or was made on another body: run "
                           "scripts/parts/01_foot_ankle_sock.py -- --rebuild first")
    cache.load_part(part.PART)
    bpy.context.view_layer.update()  # the appended frames' matrix_world is the identity until evaluated
    return part, body


class Frame:
    """Frame F of the left foot from its Empty (metres in Blender, millimetres here)."""

    def __init__(self, name="Frame.Foot.L"):
        import bpy
        M = np.array(bpy.data.objects[name].matrix_world)
        self.R, self.o = M[:3, :3].copy(), M[:3, 3] * MM

    def to_f(self, p_mm):
        return (np.asarray(p_mm, float) - self.o) @ self.R

    def to_w(self, q_mm):
        return np.asarray(q_mm, float) @ self.R.T + self.o

    def vec_to_f(self, v):
        return np.asarray(v, float) @ self.R

    def vec_to_w(self, v):
        return np.asarray(v, float) @ self.R.T


def joints(body, frame):
    """Joint centres of the left foot in F (mm), from MakeHuman's joint cubes on the shape-key mix with
    the contact key off: {"toe-1-1": MTP of the hallux, "toe-1-2": its IP, "toe-1-3": its tip end,
    "toe-2-1" ... "toe-2-4", ...}. The cubes are helper geometry, so the render copy has none of them."""
    from lib import sculpt as S
    co = S.mix(body, exclude=("Foot.Contact",)) * MM
    names = [g.name for g in body.vertex_groups if g.name.startswith("joint-l-toe-")]
    W = S.group_weights_many(body, names)
    out = {}
    for name, w in W.items():
        sel = w > 0.5
        if sel.any():
            out[name[len("joint-l-"):]] = frame.to_f(co[sel].mean(axis=0))
    return out


def strip_nail_beds(body, toes=(1, 2)):
    """Take part 01's nail-bed step (fields.nail_beds: the 4 x 5 patch sunk, its rings raised) back out of
    Foot.Sculpt on the named toes of the left foot, for this session only: the trial builds its own beds
    and folds at sub-millimetre resolution, and the old ones would leave their grooves under them. The
    sculpt is recomputed with and without the step through part 01's own fields (read-only use) and the
    difference, weighted by the toes' groups, is taken off the key. Returns the largest change (mm)."""
    import json as _json
    from lib import sculpt as S
    from parts.p01 import fields
    with open(env.path("scripts", "parts", "p01", "params.json"), encoding="utf-8") as f:
        params = _json.load(f)
    keys = ("Foot.Sculpt", "Foot.Contact")
    fb = fields.Body(body, exclude=keys)
    a = fields.amounts(params)
    o = dict(fields.FIXED, **fields.options(params))
    foot = fb.feet[SIDE]
    a["toe2_ext"] = a.get("toe2_ext", 0.0) + o["toe2_ext_extra_mm"][SIDE]
    qa = fields.pass_a(foot, fb.fields(SIDE), a)
    with_beds = fields.pass_b(foot, qa, foot.adj, o, nails=True)
    without = fields.pass_b(foot, qa, foot.adj, o, nails=False)
    w = np.clip(sum(foot.w[k] for k in toes), 0.0, 1.0)[:, None]
    delta_w = foot.frame.vec_to_w((without - with_beds) * w) / MM
    kb = body.data.shape_keys.key_blocks["Foot.Sculpt"]
    co = S.key_coords(kb)
    co[foot.R] += delta_w
    kb.data.foreach_set("co", co.astype(np.float32).ravel())
    body.data.update()
    return float(np.abs(delta_w).max() * MM)


def dense_copy(part, body, level, name=PREFIX + "Skin"):
    """The left foot below z 300 (part 01's own closeup copy) with its Catmull-Clark subdivision applied at
    `level`: vertex groups come through interpolated, as the masks the skin recipe reads need. Returns the
    object (world coordinates, identity transform: the skin recipe reads Object coordinates in metres)."""
    import bpy
    copies = part.isolate_copies(body)
    keep = None
    for cp in copies:
        if cp.name.endswith(".L.Isolate"):
            keep = cp
        else:
            bpy.data.objects.remove(cp)
    sub = keep.modifiers["Subdivision"]
    sub.levels = sub.render_levels = level
    sub.quality = 4
    sub.use_limit_surface = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(keep.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old)
    me.name = name
    ob = bpy.data.objects.new(name, me)
    for coll in keep.users_collection:
        coll.objects.link(ob)
    # the copy's own vertex groups by name (new_from_object keeps their weights, not the object's list)
    for g in keep.vertex_groups:
        if ob.vertex_groups.get(g.name) is None:
            ob.vertex_groups.new(name=g.name)
    bpy.data.objects.remove(keep)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def positions(ob):
    co = np.empty(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3) * MM


def set_positions(ob, co_mm):
    ob.data.vertices.foreach_set("co", (np.asarray(co_mm, float) / MM).ravel())
    ob.data.update()


def faces(ob):
    """(loop_start, loop_total, loop_vert) of a mesh, as lib/sculpt's topology()."""
    from lib import sculpt as S
    return S.topology(ob.data)


def vertex_normals(co, topo):
    from lib import sculpt as S
    return S.vertex_normals(co, *topo)


def group(ob, name):
    from lib import sculpt as S
    return S.group_weights(ob, name)


def set_group(ob, name, w, eps=1e-4):
    """A vertex group from per-vertex weights, replacing one of the same name."""
    g = ob.vertex_groups.get(name)
    if g is not None:
        ob.vertex_groups.remove(g)
    g = ob.vertex_groups.new(name=name)
    w = np.round(np.clip(np.asarray(w, float), 0.0, 1.0), 3)
    for value in np.unique(w[w > eps]):
        g.add(np.nonzero(w == value)[0].tolist(), float(value), "REPLACE")
    return g


def edge_lengths(ob):
    e = np.empty(len(ob.data.edges) * 2, np.int64)
    ob.data.edges.foreach_get("vertices", e)
    e = e.reshape(-1, 2)
    co = positions(ob)
    return e, np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)


# --------------------------------------------------------------------------- presets and rendering

def registry():
    """The trial's presets (presets.json) with part 01's, so p01.V5f and the rest work as well."""
    from eval import camera
    return camera.load_registry([PRESETS, os.path.join(camera.PRESET_DIR, "p01.json")])


def render(ids, tier, out_dir, tag="", hide=(), samples=None):
    """Render the named presets at a tier into out_dir as <id><tag>_<tier>.png; returns {id: sidecar}."""
    from eval import render as R
    reg = registry()
    os.makedirs(out_dir, exist_ok=True)
    out = {}
    import bpy
    for pid in ids:
        p = reg.get(pid)
        p["hide"] = list(p.get("hide") or []) + list(hide)
        # whole foot, pass 1: the camera's millimetres per pixel at 1 m (sensor / (lens x width)) for the skin's
        # texture LOD (look.ridge_lod reads it through a View Layer attribute; 0 = no fade)
        cam = p.get("camera") or {}
        res = (p.get("render") or {}).get("res") or [2048, 2048]
        k = cam.get("sensor_mm", 36.0) / (cam["lens_mm"] * res[0]) if cam.get("lens_mm") else 0.0
        for sc in bpy.data.scenes:   # the harness renders in LookDev or Hero (render.pick_scene)
            sc["hires_px_k"] = float(k)
        out[pid] = R.render_preset(p, tier=tier, out_dir=out_dir, stem=f"{pid}{tag}_{tier}", samples=samples,
                                   registry=reg)
    return out


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
        f.write("\n")
    os.replace(tmp, path)
