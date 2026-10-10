"""The materials library (spec 16): the only material API part scripts import (§7.2, §7.3).

    from lib import materials as M
    M.ensure_groups()
    M.assign(body, "Skin.Foot", part="Body", faces="Foot.Region")
    for nail in nails:                      # spec 01 §3.3: visible length, free edge, lunula
        free = M.nail_coords(nail, visible_mm, free_edge_mm, lunula_mm)
        M.assign(nail, "Nail.Plate")
        M.assign(nail, "Nail.FreeEdge", faces=free)
    issues = M.lint("part:Foot")

get() creates or updates `<Part>.Mat.<ID>` idempotently: the material records the hash of its recipe, its
overrides, LIB_VERSION and the library's own source, and is rebuilt in place only when that hash changes
(§7.4), so its users keep it. assign() also checks the inputs the recipe reads (masks, attributes, UV maps,
object properties) against the object and says which are missing: a missing mask reads 0 and switches its
layer off, which is the library's clean fallback, never a silent one.

Built (spec 16 §9): the catalogue as data (step 1), the node builder and hashing (step 2), the groups and
recipes the skin, nail and sock need (steps 4, 5, 7 in part), and lint (step 10). Everything else of §7.2
raises NotBuilt with its section: the weathering groups (dust, edge, chips, crest), camouflage, bakes and
the wear-source switch.
"""
import copy
import difflib
import hashlib
import importlib
import json
import os
from collections import namedtuple

import numpy as np

from . import env, log, naming
from . import mat_catalogue as C
from . import mat_core as K
from . import mat_groups as G
from .mat_catalogue import LIB_VERSION, hex_to_linear, linear_to_hex  # noqa: F401 (the API re-exports them)
from .mat_groups import NotBuilt
from .mat_skin import nail_coords  # noqa: F401

FAMILY_MODULES = {"skin": "mat_skin", "fabric": "mat_fabric"}
FAMILY_PLANNED = {"hard": "mat_hard.py, §3.3.5-3.3.8", "hair": "the Principled Hair settings of §3.3.2",
                  "eye": "spec 06's eye and mouth recipes, §3.3.3"}
SPEC17 = ("Scene.", "Cal.", "LookDev.", "Set.")   # spec 17's own materials (§5.1-5.5): not the library's to lint
LintIssue = namedtuple("LintIssue", "level code target message")
_REPORT = []


# --------------------------------------------------------------------------- catalogue

def recipe(id):
    """A copy of a catalogue entry (with its id); NotBuilt for a planned ID, KeyError with close matches
    for an unknown one."""
    if id in C.CATALOGUE:
        r = copy.deepcopy(C.CATALOGUE[id])
        r["id"] = id
        return r
    if id in C.PLANNED:
        p = C.PLANNED[id]
        raise NotBuilt(f"{id} is in spec 16 {p['section']} (family {p['family']}) but its recipe is not built yet")
    close = difflib.get_close_matches(id, list(C.CATALOGUE) + list(C.PLANNED), n=4, cutoff=0.5)
    raise KeyError(f"no catalogue ID {id!r} in spec 16 §3.3" + (f"; did you mean {close}?" if close else ""))


def material_name(id, part):
    """§7.1: `<Part>.Mat.<ID>`, dropping a leading word of the ID equal to the part (`Eye.Mat.Cornea`)."""
    first, _, rest = id.partition(".")
    return naming.check(f"{part}.Mat.{rest if first == part and rest else id}")


def _overridden(rec, overrides):
    """Overrides by top-level key or dotted path (`regions.sole.hex`); unknown keys are refused."""
    rec = copy.deepcopy(rec)
    for k, v in sorted(overrides.items()):
        path = k.replace("__", ".").split(".")
        node = rec
        for p in path[:-1]:
            if p not in node:
                raise KeyError(f"override {k!r}: {rec['id']} has no {p!r}")
            node = node[p]
        if path[-1] not in node:
            raise KeyError(f"override {k!r}: {rec['id']} has no {path[-1]!r}")
        node[path[-1]] = v
    return rec


def _module(rec):
    fam = rec["family"]
    if fam in FAMILY_PLANNED:
        raise NotBuilt(f"family {fam!r} ({FAMILY_PLANNED[fam]}) is not built yet")
    return importlib.import_module(f".{FAMILY_MODULES[fam]}", __package__)


def recipe_hash(rec, overrides, module):
    src = G.source_hash(*G.SOURCES, os.path.basename(module.__file__), "materials.py")
    blob = json.dumps({"rec": rec, "over": overrides, "lib": LIB_VERSION, "src": src}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- groups and materials

def ensure_groups(names=None):
    """Build the library's node groups (all built ones, or the names given), rebuilding any whose library
    source changed; a planned group raises NotBuilt. Returns {name: node tree}."""
    names = list(G.GROUPS) if names is None else list(names)
    return {n: G.build(n) for n in names}


def get(id, part, **overrides):
    """The material `<Part>.Mat.<ID>`, created or brought up to date (idempotent, §7.4)."""
    import bpy
    rec = _overridden(recipe(id), overrides)
    mod = _module(rec)
    ensure_groups(mod.GROUPS_USED.get(rec["builder"], ()))
    h = recipe_hash(rec, overrides, mod)
    name = material_name(id, part)
    mat = next((m for m in bpy.data.materials if m.name == name and m.library is None), None)
    if mat is not None and mat.get("recipe_hash") == h:
        return mat
    if mat is None:
        mat = bpy.data.materials.new(name)
    elif mat.get("lib_version") is None:
        raise RuntimeError(f"{name} exists and was not made by the library (lint L1); the library never "
                           "replaces a material it did not create (§7.4): remove or rename it")
    mod.build_material(mat, rec, part, overrides)
    mat["recipe"], mat["recipe_hash"], mat["lib_version"] = id, h, LIB_VERSION
    mat["overrides"] = json.dumps(overrides, sort_keys=True, default=str)
    mat["reads"] = json.dumps(rec.get("reads", {}), sort_keys=True)
    mat["tree_hash"] = K.tree_hash(mat.node_tree)
    mat.diffuse_color = tuple(hex_to_linear(rec["albedo_hex"])) + (1.0,)   # the solid-view colour
    return mat


def _vertex_weights(ob, name):
    g = ob.vertex_groups.get(name)
    if g is None:
        raise KeyError(f"{ob.name} has no vertex group or face attribute {name!r}")
    w = np.zeros(len(ob.data.vertices))
    for v in ob.data.vertices:
        for e in v.groups:
            if e.group == g.index:
                w[v.index] = e.weight
    return w


def face_selection(ob, faces):
    """A boolean per face: None = all; indices; a boolean face attribute; or a vertex group (faces whose
    corners all weigh 0.5 or more)."""
    me = ob.data
    n = len(me.polygons)
    if faces is None:
        return np.ones(n, bool)
    if isinstance(faces, str):
        att = me.attributes.get(faces)
        if att is not None and att.domain == "FACE":
            vals = np.zeros(n, bool)
            att.data.foreach_get("value", vals)
            return vals
        w = _vertex_weights(ob, faces) >= 0.5
        loops = np.empty(len(me.loops), np.int64)
        me.loops.foreach_get("vertex_index", loops)
        start = np.empty(n, np.int64)
        me.polygons.foreach_get("loop_start", start)
        return np.logical_and.reduceat(w[loops], start) if n else np.zeros(0, bool)
    sel = np.zeros(n, bool)
    sel[np.asarray(list(faces), np.int64)] = True
    return sel


def assign(obj, id, part=None, faces=None, **overrides):
    """Put the recipe's material on an object (on `faces` only, if given) and report the recipe's inputs
    the object lacks. `part` defaults to the object's own prefix (`Foot.L.Nail.1` -> `Foot`)."""
    part = part or obj.name.split(".")[0]
    mat = get(id, part, **overrides)
    me = obj.data
    if all(m is None or m.name != mat.name for m in me.materials):
        me.materials.append(mat)
    idx = next(i for i, m in enumerate(me.materials) if m is not None and m.name == mat.name)
    sel = face_selection(obj, faces)
    cur = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get("material_index", cur)
    cur[sel] = idx
    me.polygons.foreach_set("material_index", cur)
    me.update()
    rep = inputs_report(obj, [mat])
    _REPORT.append({"object": obj.name, "material": mat.name, "faces": int(sel.sum()), **rep.get(mat.name, {})})
    missing = rep.get(mat.name, {}).get("missing")
    if missing:
        log.info("materials", f"{mat.name} on {obj.name}: missing {', '.join(missing)} (read as 0: those layers are off)")
    return mat


def _object_inputs(ob):
    names = set(ob.data.attributes.keys()) | {g.name for g in ob.vertex_groups}
    return names, {u.name for u in ob.data.uv_layers}, set(ob.keys())


def inputs_report(obj, mats=None):
    """{material: {"missing": [...], "present": [...]}} for the library materials on obj (or `mats`)."""
    attrs, uvs, props = _object_inputs(obj)
    out = {}
    for mat in mats or [m for m in obj.data.materials if m is not None]:
        if mat.get("reads") is None:
            continue
        reads = json.loads(mat["reads"])
        opt = set(reads.get("optional", []))
        need = [("attribute", a, a in attrs) for a in reads.get("attributes", [])]
        need += [("uv", u, u in uvs) for u in reads.get("uv", [])]
        need += [("object property", p, p in props) for p in reads.get("object_props", [])]
        out[mat.name] = {"missing": [f"{k} {n}" for k, n, ok in need if not ok and n not in opt],
                         "present": [n for k, n, ok in need if ok]}
    return out


def report():
    """What assign() did in this session: object, material, faces, inputs present and missing."""
    return list(_REPORT)


def set_wear_source(mat, channel, source, image=None, attribute=None):
    raise NotBuilt("set_wear_source needs the weathering groups of spec 16 §4.2-4.5 (dust, edge, chips, crest), "
                   "which are not built yet")


def apply_wear_preset(mat, preset):
    """Only the `none` preset exists so far (skin, eyes, hidden parts); the others need §4.2-4.5's groups."""
    name = preset if isinstance(preset, str) else preset.get("name")
    if name not in C.WEAR_PRESETS:
        raise KeyError(f"no wear preset {name!r} in spec 16 §4.10")
    if name != "none":
        raise NotBuilt(f"wear preset {name!r} needs MG.Weather.Dust, MG.Mask.EdgeBevel, MG.Weather.Chips and "
                       "MG.Fabric.Crest (spec 16 §4.2-4.5), not built yet")
    mat["wear_preset"] = "none"


def set_lod(mats, lod):
    """Every library group in these materials to LOD 0 (renders) or 1 (export bakes, §5.4 step 2)."""
    for mat in mats:
        for nd in mat.node_tree.nodes:
            if nd.bl_idname == "ShaderNodeGroup" and nd.node_tree and nd.node_tree.name.startswith("MG."):
                s = nd.inputs.get("LOD")
                if s is not None and not s.is_linked:
                    s.default_value = float(lod)


def camo_calibrate(seed=7.0, size_m=2.0, px=2048):
    raise NotBuilt("MG.Camo.Blotch4 and its calibration (spec 16 §4.6, §9 step 6) are not built yet; "
                   "the calibrated values are data in mat_catalogue.CAMO")


def bake_masks(objects, part, size=2048, channels="RGBA", wear2=False):
    raise NotBuilt("bake_masks (spec 16 §5.3, mat_bake.py) is not built yet")


def bake_atlas(atlas, objects, size, samples=16, use_cage=True):
    raise NotBuilt("bake_atlas (spec 16 §5.4, mat_bake.py, §9 step 11) is not built yet")


# --------------------------------------------------------------------------- test objects and swatches (§8.2)

TEST_COLL = "Lib.Test"   # beside spec 17's swatch stage; lookdev.aim() shows it only for spec 16 and 17's views
BALL_AT, TOE_AT, FOLD_AT = (-0.125, 0.03, 1.0), (-0.045, 0.0, 0.995), (-0.045, 0.0, 1.0)


def _mesh_object(name, verts, faces, coll, uv=None, smooth=True, subsurf=2):
    import bpy
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old)
    me = bpy.data.meshes.get(name)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    if uv is not None:
        layer = me.uv_layers.new(name="UV.Real")
        loops = np.empty(len(me.loops), np.int64)
        me.loops.foreach_get("vertex_index", loops)
        layer.data.foreach_set("uv", np.asarray(uv, np.float32)[loops].ravel())
    if smooth:
        me.shade_smooth()
    me.validate()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    if subsurf:
        sub = ob.modifiers.new("Subdivision", "SUBSURF")
        sub.levels, sub.render_levels = 1, subsurf
    return ob


def _grid(nu, nv, closed_u=False):
    faces = []
    cols = nu if closed_u else nu - 1
    for j in range(nv - 1):
        for i in range(cols):
            a, b = j * nu + i, j * nu + (i + 1) % nu
            faces.append((a, b, b + nu, a + nu))
    return faces


def _paint(ob, name, weights):
    g = ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)
    w = np.round(np.asarray(weights, float), 4)
    g.remove(list(range(len(w))))
    for value in np.unique(w[w > 1e-4]):
        g.add(np.nonzero(w == value)[0].tolist(), float(value), "REPLACE")


def test_objects(scene=None):
    """Lib.Test.Ball (Ø 60 mm), Lib.Test.Toe (a Ø 22 mm toe with a nail bed on top), Lib.Test.Nail (a 15 x
    14.5 mm plate on it with a 1.5 mm free edge) and Lib.Test.Fold (a 120 x 80 mm sheet with one soft
    fold), all with a metric UV.Real, in the collection Lib.Test. Rebuilt on every call (cheap)."""
    import bpy
    scene = scene or bpy.context.scene
    coll = bpy.data.collections.get(TEST_COLL) or bpy.data.collections.new(TEST_COLL)
    if coll not in scene.collection.children_recursive:
        scene.collection.children.link(coll)
    out = {}
    # ball: an equirectangular sphere whose UV is metres along the surface at the equator
    r, nu, nv = 0.030, 96, 48
    V, UV = [], []
    for j in range(nv + 1):
        th = np.pi * j / nv
        for i in range(nu + 1):
            ph = 2.0 * np.pi * i / nu
            V.append((BALL_AT[0] + r * np.sin(th) * np.cos(ph), BALL_AT[1] + r * np.sin(th) * np.sin(ph),
                      BALL_AT[2] - r * np.cos(th)))
            UV.append((r * ph, r * th))
    out["ball"] = _mesh_object("Lib.Test.Ball", V, _grid(nu + 1, nv + 1), coll, UV, subsurf=1)
    # toe: a capsule along Y, its rounded tip toward the camera (-Y); rings every 0.5 mm
    rt, n_ring = 0.011, 64
    ys = np.concatenate([-rt * np.cos(np.linspace(0.04, np.pi / 2, 24)), np.arange(0.0005, 0.045, 0.0005)])
    V, UV = [], []
    for y in ys:
        rad = np.sqrt(max(rt * rt - y * y, 0.0)) if y < 0 else rt
        for i in range(n_ring):
            a = 2.0 * np.pi * i / n_ring
            V.append((TOE_AT[0] + rad * np.sin(a), TOE_AT[1] + y, TOE_AT[2] + rad * np.cos(a)))
            UV.append((rt * a, y))
    F = _grid(n_ring, len(ys), closed_u=True)
    tip = len(V)
    V.append((TOE_AT[0], TOE_AT[1] - rt, TOE_AT[2]))
    UV.append((0.0, -rt))
    F += [(tip, (i + 1) % n_ring, i) for i in range(n_ring)]
    toe = _mesh_object("Lib.Test.Toe", V, F, coll, UV, subsurf=1)
    P = np.array(V) - np.array(TOE_AT)
    on_top = (P[:, 2] > 0.75 * rt) & (np.abs(P[:, 0]) < 0.0072)
    _paint(toe, "toenails", (on_top & (P[:, 1] > 0.0005) & (P[:, 1] < 0.0145)).astype(float))
    _paint(toe, "Foot.ToeRed", np.clip(1.0 - (P[:, 1] + 0.004) / 0.03, 0.0, 1.0))
    _paint(toe, "Foot.DorsumThin", (P[:, 2] > 0.0).astype(float))
    _paint(toe, "Foot.Sole", np.clip(-P[:, 2] / rt * 1.5 - 0.3, 0.0, 1.0))
    out["toe"] = toe
    # nail: a curved plate over the bed, lifted 0.35 mm, its free edge past the tip
    xs, yn = np.linspace(-0.0075, 0.0075, 16), np.linspace(-0.0005, 0.0145, 31)
    V = [(TOE_AT[0] + x, TOE_AT[1] + y, TOE_AT[2] + np.sqrt(rt * rt - x * x) + 0.00035) for y in yn for x in xs]
    nail = _mesh_object("Lib.Test.Nail", V, _grid(len(xs), len(yn)), coll, subsurf=2)   # faces +Z, off the toe
    sol = nail.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness, sol.offset, sol.use_rim, sol.use_even_offset = 0.0011, 1.0, True, True
    nail.modifiers.move(1, 0)
    nail["p01_axis"] = [0.0, -1.0, 0.0]
    out["nail"] = nail
    # fold: a vertical sheet facing the camera with one soft fold toward it (the cloth test of §8.2)
    xs, zs = np.linspace(-0.06, 0.06, 121), np.linspace(-0.04, 0.04, 81)
    V, UV = [], []
    arc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(xs), np.diff(-0.012 * np.exp(-(xs / 0.02) ** 2))))])
    for z in zs:
        for i, x in enumerate(xs):
            V.append((FOLD_AT[0] + x, FOLD_AT[1] - 0.012 * np.exp(-(x / 0.02) ** 2), FOLD_AT[2] + z))
            UV.append((arc[i], z + 0.04))
    out["fold"] = _mesh_object("Lib.Test.Fold", V, _grid(len(xs), len(zs)), coll, UV, subsurf=1)
    return out


def _swatch_masks(plane, rec):
    """Regional masks painted on LookDev.Swatch so one swatch shows a recipe's regions side by side: skin in
    four 25 mm strips (dorsum, sole with its pressure pink, heel callus, toe red); the sock with grime on the
    lower half and pilling on the right half."""
    co = np.array([v.co for v in plane.data.vertices])
    x = (co[:, 0] - co[:, 0].min()) / max(np.ptp(co[:, 0]), 1e-9)
    z = (co[:, 2] - co[:, 2].min()) / max(np.ptp(co[:, 2]), 1e-9)
    for g in list(plane.vertex_groups):
        plane.vertex_groups.remove(g)
    if rec["builder"] == "skin_foot":
        strip = np.minimum((x * 4).astype(int), 3)
        _paint(plane, "Foot.DorsumThin", (strip == 0).astype(float))
        _paint(plane, "Foot.Sole", ((strip == 1) | (strip == 2)).astype(float))
        _paint(plane, "Foot.Pressure", ((strip == 1) & (z < 0.5)).astype(float))
        _paint(plane, "Foot.Callus.Heel", (strip == 2).astype(float))
        _paint(plane, "Foot.ToeRed", (strip == 3).astype(float))
    elif rec["builder"] == "knit_sock":
        _paint(plane, "sock_grime", (z < 0.5).astype(float))
        _paint(plane, "sock_sole", (x > 0.5).astype(float))


def swatch(id, out_dir=None, views=None, tier="look", samples=None):
    """Render a recipe's swatch views in spec 17's LookDev (§8.2): V1 the flat swatch beside the 18 % card,
    V2 the macro, V7 (an addition) the ball with the toe and nail (skin, nails) or the fold (fabrics).
    V3 needs Lib.Test.WearBlock and the weathering groups (NotBuilt). Returns {view: png path}."""
    import bpy
    env.bootstrap()
    from eval import lookdev, render
    rec = recipe(id)
    scene = lookdev.ensure()
    if bpy.context.window is not None:
        bpy.context.window.scene = scene
    objs = test_objects(scene)
    plane = bpy.data.objects[lookdev.SWATCH]
    nail_like = rec["builder"] == "nail"
    if views is None:
        views = ("V7",) if nail_like else ("V1", "V2", "V7")
    if "V3" in views:
        raise NotBuilt("p16.V3 needs Lib.Test.WearBlock and MG.Weather.Dust, MG.Mask.EdgeBevel, MG.Weather.Chips")
    for ob in [plane] + list(objs.values()):
        ob.data.materials.clear()
    _swatch_masks(plane, rec)
    hide = []
    if rec["family"] == "skin":
        assign(objs["toe"], "Skin.Foot", part="Lib")
        free = nail_coords(objs["nail"], 14.5, 1.5, lunula_mm=3.5)
        assign(objs["nail"], "Nail.Plate", part="Lib")
        assign(objs["nail"], "Nail.FreeEdge", part="Lib", faces=free)
        objs["nail"].modifiers["Solidify"].material_offset_rim = 0   # each rim takes its own face's material
        assign(objs["ball"], id if not nail_like else "Skin.Foot", part="Lib")
        if not nail_like:
            assign(plane, id, part="Lib")
        hide.append(objs["fold"])
    else:
        for k in ("ball", "fold"):
            assign(objs[k], id, part="Lib")
        assign(plane, id, part="Lib")
        hide += [objs["toe"], objs["nail"]]
    for ob in hide:
        ob.hide_render = True
    out_dir = out_dir or os.path.join(env.RENDERS_DIR, "16_materials", "swatch")
    safe = id.replace(".", "_")
    files = {}
    try:
        for v in views:
            side = render.render_preset(f"p16.{v}", tier=tier, out_dir=out_dir, stem=f"p16.{v}_{safe}_{tier}",
                                        samples=samples)
            files[v] = env.path(side["outputs"]["png"])
            log.info("materials", f"swatch {id} {v} {tier}: {side['seconds']:.2f} s -> {side['outputs']['png']}")
    finally:
        for ob in hide:
            ob.hide_render = False
    return files


# --------------------------------------------------------------------------- lint (§7.5)

def _scope_materials(scope):
    import bpy
    if isinstance(scope, (list, tuple)):
        mats = set()
        for x in scope:
            if isinstance(x, bpy.types.Material):
                mats.add(x)
            elif hasattr(x, "data") and hasattr(x.data, "materials"):
                mats.update(m for m in x.data.materials if m)
        return sorted(mats, key=lambda m: m.name)
    if scope.startswith("part:"):
        pre = scope[5:].rstrip(".") + "."
        mats = {m for m in bpy.data.materials if m.name.startswith(pre)}
        for ob in bpy.data.objects:
            if ob.name.startswith(pre) and ob.type == "MESH":
                mats.update(m for m in ob.data.materials if m)
        return sorted(mats, key=lambda m: m.name)
    return sorted((m for m in bpy.data.materials if m.library is None and not m.name.startswith(SPEC17)
                   and m.users > 0), key=lambda m: m.name)


def _users(mat):
    import bpy
    return [ob for ob in bpy.data.objects if ob.type == "MESH" and any(m == mat for m in ob.data.materials)]


def _upstream(sock_in, seen=None):
    """Every (node, output name) feeding an input socket, through groups (all a group node's inputs)."""
    seen = set() if seen is None else seen
    for lk in sock_in.links:
        key = (lk.from_node.name, lk.from_socket.identifier)
        if key in seen:
            continue
        seen.add(key)
        yield lk.from_node, lk.from_socket.name
        for s in lk.from_node.inputs:
            if s.is_linked:
                yield from _upstream(s, seen)


def _planar(ob, tol_m=1e-4):
    co = np.array([v.co for v in ob.data.vertices])
    if len(co) < 4:
        return True
    s = np.linalg.svd(co - co.mean(axis=0), compute_uv=False)
    return s[-1] / np.sqrt(len(co)) < tol_m


def _bump_chain(nd):
    n = 1
    while True:
        s = nd.inputs.get("Normal")
        prev = s.links[0].from_node if s is not None and s.is_linked else None
        if prev is None or prev.bl_idname != "ShaderNodeBump":
            return n
        nd, n = prev, n + 1


def lint(scope="all"):
    """§7.5's rules over the materials in scope ("all" = every local material but spec 17's own, "part:Foot",
    or a list of materials and objects). Returns LintIssue(level, code, target, message) records; errors
    are L1-L10, warnings W1-W4, plus W5 (a library material older than the library) and W6 (an input the
    recipe reads is missing on an object that uses it)."""
    import bpy
    out = []

    def add(level, code, target, msg):
        out.append(LintIssue(level, code, target, msg))

    for mat in _scope_materials(scope):
        nt = mat.node_tree
        if nt is None:
            continue
        lib = mat.get("lib_version") is not None
        users = _users(mat)
        if not lib and any(n.bl_idname == "ShaderNodeBsdfPrincipled" for n in nt.nodes):
            add("error", "L1", mat.name, "a Principled BSDF not built by the library")
        if not lib and users and not mat.name.startswith(SPEC17) and ".Mat." not in mat.name:
            add("error", "L10", mat.name, "material name breaks <Part>.Mat.<ID> (§7.1)")
        if lib:
            rid = mat.get("recipe")
            try:
                rec = _overridden(recipe(rid), json.loads(mat.get("overrides", "{}")))
            except (KeyError, NotBuilt) as e:
                add("error", "L10", mat.name, f"recipe {rid!r}: {e}")
                continue
            part = mat.name.split(".Mat.")[0]
            if material_name(rid, part) != mat.name:
                add("error", "L10", mat.name, f"expected {material_name(rid, part)} for recipe {rid}")
            rule = C.CLASS_RULES[rec["class"]]
            y = C.luminance(hex_to_linear(rec["albedo_hex"]))
            if rule.get("albedo_y") and not (rule["albedo_y"][0] <= y <= rule["albedo_y"][1]):
                add("error", "L2", mat.name, f"albedo Y {y:.3f} outside {rec['class']} {rule['albedo_y']}")
            cap = rule.get("sheen_max", 0.12)
            for nd in nt.nodes:
                if nd.bl_idname == "ShaderNodeBsdfPrincipled":
                    s = nd.inputs["Sheen Weight"]
                    if not s.is_linked and s.default_value > cap + 1e-6:
                        add("error", "L3", mat.name, f"sheen {s.default_value:.3f} above {rec['class']}'s {cap}")
            try:
                current = recipe_hash(rec, json.loads(mat.get("overrides", "{}")), _module(rec))
            except NotBuilt:
                current = None
            if current is not None and mat.get("recipe_hash") != current:
                add("warning", "W5", mat.name, "built by an older library: get() rebuilds it")
            for ob in users:
                rep = inputs_report(ob, [mat]).get(mat.name, {})
                if rep.get("missing"):
                    add("warning", "W6", f"{mat.name} on {ob.name}", "missing " + ", ".join(rep["missing"]))
        for nd in nt.nodes:
            if nd.bl_idname == "ShaderNodeTexImage" and nd.image is not None:
                img = nd.image
                kind = img.get("lib_kind")
                low = img.name.lower()
                colour = kind in K.COLOUR_KINDS if kind else any(t in low for t in ("diff", "color", "albedo", "base"))
                data = (kind is not None and not colour) or any(t in low for t in ("nor", "rough", "disp", "_ao", "metal", "mask", "height"))
                cs = img.colorspace_settings.name
                if colour and cs != "sRGB":
                    add("error", "L4", f"{mat.name}/{nd.name}", f"{img.name} is a colour map in {cs}")
                elif data and not colour and cs not in ("Non-Color", "Linear Rec.709"):
                    add("error", "L4", f"{mat.name}/{nd.name}", f"{img.name} is a data map in {cs}")
                path = bpy.path.abspath(img.filepath) if img.filepath else ""
                if path and img.packed_file is None and not os.path.isfile(path):
                    add("error", "L5", f"{mat.name}/{nd.name}", f"{path} is missing; restore it with {K.RESTORE}")
                srcs = list(_upstream(nd.inputs["Vector"]))
                for src, outname in srcs:
                    if src.bl_idname == "ShaderNodeTexCoord" and outname in ("Object", "Generated"):
                        bad = [ob.name for ob in users if not _planar(ob)]
                        if bad:
                            add("error", "L7", f"{mat.name}/{nd.name}", f"{outname} coordinates feed a tiled map on "
                                f"non-planar {', '.join(bad[:3])}")
                    if (src.bl_idname == "ShaderNodeGroup" and src.node_tree and src.node_tree.name == "MG.Tile.AntiRepeat"
                            and kind and img.get("lib_asset") in C.TILE_PERIODS):
                        t = src.inputs["Tile mm"]
                        if not t.is_linked:
                            tiles = C.TILE_PERIODS[img["lib_asset"]]["tiles_mm"].values()
                            if all(abs(t.default_value / x - 1.0) > C.TILE_TOLERANCE for x in tiles):
                                add("error", "L6", f"{mat.name}/{nd.name}", f"{img['lib_asset']} tiled at "
                                    f"{t.default_value} mm; §3.2 says {sorted(tiles)}")
            if nd.bl_idname == "ShaderNodeNewGeometry" and nd.outputs["Pointiness"].is_linked:
                for ob in users:
                    boolean = any(m.type == "BOOLEAN" for m in ob.modifiers)
                    me = ob.data
                    e = np.array([(me.vertices[a].co - me.vertices[b].co).length for a, b in
                                  (ed.vertices for ed in me.edges)]) if len(me.edges) else np.zeros(1)
                    if boolean or e.mean() > 0.005:
                        add("error", "L8", f"{mat.name} on {ob.name}", "Pointiness on a boolean or sparse mesh")
            if nd.bl_idname == "ShaderNodeBump":
                s = nd.inputs["Strength"]
                if not s.is_linked and abs(s.default_value - 1.0) > 1e-6:
                    add("warning", "W2", f"{mat.name}/{nd.name}", f"Bump strength {s.default_value} on a procedural height")
                if _bump_chain(nd) > 3:
                    add("warning", "W3", f"{mat.name}/{nd.name}", "more than three chained Bump nodes")
    return out


# --------------------------------------------------------------------------- self-test (§8.1 T1-T5, T9)

def selftest():
    import bpy
    res = {"catalogue": C.selftest()}
    built = ensure_groups()
    res["groups"] = {n: g["recipe_hash"] for n, g in built.items()}
    hashes = {}
    for rid in C.CATALOGUE:
        h = []
        for _ in range(2):
            m = get(rid, "Lib")
            h.append(K.tree_hash(m.node_tree))
            m["recipe_hash"] = "stale"   # force the second get() to rebuild: T3 wants two builds, not one
        assert h[0] == h[1], (rid, h)
        hashes[rid] = h[0]
        get(rid, "Lib")
    res["tree_hash"] = hashes
    try:
        recipe("Cordura.500D.OliveBrown")
        raise AssertionError("a planned recipe was handed out")
    except NotBuilt:
        pass
    assert material_name("Skin.Foot", "Body") == "Body.Mat.Skin.Foot"
    assert material_name("Eye.Cornea", "Eye") == "Eye.Mat.Cornea"
    issues = [i for i in lint([bpy.data.materials[material_name(r, "Lib")] for r in C.CATALOGUE]) if i.level == "error"]
    assert not issues, issues
    res["lint_errors"] = 0
    for rid in C.CATALOGUE:
        m = bpy.data.materials.get(material_name(rid, "Lib"))
        if m is not None and m.users == 0:
            bpy.data.materials.remove(m)
    return res
