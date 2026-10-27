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
recipes the skin, nail and sock need (steps 4, 5, 7 in part), and lint (step 10); since 2026-10-27 the boot's
twelve recipes (spec 02 §0 item 7) with the dust, edge-mask, edge-wear, polish, basket, herringbone and braid
groups, the wear presets for recipes that carry one (apply_wear_preset), the dust zones (wear_zones) and the
boot test object (test_boot, swatch views V8-V10). A part script for the boot:

    for ob in (upper_l, upper_r):
        M.assign(ob, "Leather.Boot.FullGrain", part="Boot", faces="leather")
        M.assign(ob, "Cordura.500D.Black", part="Boot", faces="cordura")
        M.wear_zones(ob, "boot.toe", {"toe": "zone_toe", "vamp": "zone_vamp", ...})   # vertex groups
        ob["wear_dust_scale"] = 1.0 if ".L." in ob.name else 0.7
    # and the attributes the leather reads: `crease` (the crease field), `polish` (counter, lateral quarter)

Everything else of §7.2 raises NotBuilt with its section: chips, crest, camouflage, bakes and the
wear-source switch.
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

FAMILY_MODULES = {"skin": "mat_skin", "fabric": "mat_fabric", "hard": "mat_hard"}
FAMILY_PLANNED = {"hair": "the Principled Hair settings of §3.3.2", "eye": "spec 06's eye and mouth recipes, §3.3.3"}
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
        return C.resolve(r)
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
    if "wear" in overrides and rec.get("wear") not in C.WEAR_PRESETS:
        raise KeyError(f"override 'wear': {rec['wear']!r} is not a wear preset of spec 16 §4.10")
    return C.resolve(rec)


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
        zone = [m for m in missing if m == "attribute wear_dust"]
        rest = [m for m in missing if m != "attribute wear_dust"]
        if rest:
            log.info("materials", f"{mat.name} on {obj.name}: missing {', '.join(rest)} (read as 0: those layers are off)")
        if zone:
            log.info("materials", f"{mat.name} on {obj.name}: no dust zones (wear_zones()): geometry alone places the dust")
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
    raise NotBuilt("set_wear_source (spec 16 §5.3) is not built: the built recipes take their masks live from "
                   "the shader (dust, grime, edge) and from fixed attribute names (wear_dust with the wear_zones "
                   "flag, polish, crease, bumper; mat_catalogue's `reads`); image sources need bake_masks")


def apply_wear_preset(mat, preset):
    """Rebuild a library material with a wear preset of §4.10 (its recipe's `wear` overridden; the material
    keeps its name and users). Recipes that carry their own wear (skin, nails, the sock) take only `none`,
    which marks them. Returns the material."""
    name = preset if isinstance(preset, str) else preset.get("name")
    if name not in C.WEAR_PRESETS:
        raise KeyError(f"no wear preset {name!r} in spec 16 §4.10")
    rid = mat.get("recipe")
    if rid is None:
        raise RuntimeError(f"{mat.name} was not made by the library")
    if recipe(rid).get("wear") not in C.WEAR_PRESETS:
        if name != "none":
            raise ValueError(f"{rid} carries its own wear ({recipe(rid).get('wear')}); only 'none' applies")
        mat["wear_preset"] = "none"
        return mat
    over = json.loads(mat.get("overrides", "{}"))
    over["wear"] = name
    m = get(rid, mat.name.split(".Mat.")[0], **over)
    m["wear_preset"] = name
    return m


def wear_zones(obj, preset, zones, attribute="wear_dust"):
    """Write a part's dust zones (§4.10's table for `preset`, e.g. boot.toe: toe 1.0, vamp 0.8, ...) as the
    point attribute `wear_dust` = max over zones of weight x mask, and set the object flag `wear_zones` that
    tells the library's dusty recipes to read it (without the flag they read 1: geometry alone places the
    dust). `zones` maps zone names to a vertex group name, a per-vertex weight array or a constant (the whole
    object, e.g. {"laces": 1.0}). Returns the weights."""
    table = C.WEAR_PRESETS[preset].get("dust_zones")
    if not table:
        raise KeyError(f"wear preset {preset!r} has no dust zones (spec 16 §4.10)")
    n = len(obj.data.vertices)
    w = np.zeros(n)
    for zone, src in zones.items():
        if zone not in table:
            raise KeyError(f"{preset} has no zone {zone!r}: {sorted(table)}")
        if isinstance(src, str):
            m = _vertex_weights(obj, src)
        elif np.ndim(src) == 0:
            m = np.full(n, float(src))
        else:
            m = np.asarray(src, float)
        w = np.maximum(w, table[zone] * np.clip(m, 0.0, 1.0))
    att = obj.data.attributes.get(attribute)
    if att is not None and (att.domain != "POINT" or att.data_type != "FLOAT"):
        obj.data.attributes.remove(att)
        att = None
    att = att or obj.data.attributes.new(attribute, "FLOAT", "POINT")
    att.data.foreach_set("value", w.astype(np.float32))
    obj["wear_zones"] = 1
    obj["wear_preset"] = preset
    return w


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


# --------------------------------------------------------------------------- the boot test object (2026-10-27)

# Lib.Test.Boot.*: a lasted boot for judging the boot's recipes together (spec 02 §0 item 7, swatch views
# V8-V10): an upper (the smooth union of four ellipsoids for toe box, vamp, instep and heel and an elliptic
# shaft 106 x 138 mm to 212 mm, cut flat at 26 mm), leather overlays standing 0.8 mm proud of the Cordura
# shaft panels (toe cap, counter and quarters, lace stays, backstrap), three flex creases across the vamp,
# a 2.5 mm lining (Fabric.BackFace) with a foam rim, a rubber rand rising to a toe bumper, the PU midsole
# stripe, the outsole with chevron and perimeter lugs, eyelets, a criss-crossed lace with tails and aglets,
# a webbing collar strap with a buckle, and stitch rows on the overlay edges. Millimetres in the boot frame
# (floor z 0, toes toward -Y, a left boot: lateral +X), metres in Blender at BOOT_AT on LookDev's floor.
BOOT_AT = (0.0, 0.0, 0.0005)   # half a millimetre up: the lugs would otherwise share the floor's plane
BOOT_PREFIX = "Lib.Test.Boot."
_BLOBS = (((-6.0, -103.0, 32.0), (49.0, 50.0, 38.0)),    # toe box
          ((-3.0, -45.0, 36.0), (54.0, 62.0, 54.0)),     # vamp and ball
          ((0.0, 22.0, 50.0), (46.0, 62.0, 72.0)),       # instep
          ((0.0, 95.0, 46.0), (41.0, 50.0, 46.0)))       # heel
_SHAFT = {"c": (0.0, 70.0), "r": (53.0, 69.0), "z": (40.0, 212.0)}
_UPPER_CUT, _TOP, _K_UNION = 26.0, 212.0, 20.0
_C0 = np.array([0.0, 45.0, 70.0])   # the upper is star-shaped about this point (rays cross its surface once)


def _smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def _upper_sdf(P, cut=True):
    """A distance-like field of the upper (mm): negative inside."""
    d = None
    for c, r in _BLOBS:
        q = (P - np.asarray(c)) / np.asarray(r)
        e = (np.linalg.norm(q, axis=-1) - 1.0) * min(r)
        d = e if d is None else _smin(d, e, _K_UNION)
    q = (P[..., :2] - np.asarray(_SHAFT["c"])) / np.asarray(_SHAFT["r"])
    s = np.maximum((np.linalg.norm(q, axis=-1) - 1.0) * min(_SHAFT["r"]), _SHAFT["z"][0] - P[..., 2])
    d = _smin(d, s, _K_UNION)
    d = np.maximum(d, P[..., 2] - _TOP)
    if cut:
        d = -_smin(-d, -(_UPPER_CUT - P[..., 2]), 3.0)
    return d


def _cast(O, D, far=420.0, cut=True, iters=24):
    """Points where rays from inside points O along unit directions D leave the upper (bisection)."""
    O, D = np.broadcast_arrays(np.asarray(O, float), np.asarray(D, float))
    lo, hi = np.zeros(len(D)), np.full(len(D), far)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        inside = _upper_sdf(O + D * mid[:, None], cut) < 0.0
        lo, hi = np.where(inside, mid, lo), np.where(inside, hi, mid)
    return O + D * (0.5 * (lo + hi))[:, None]


def _sdf_normal(P, cut=True, h=0.3):
    g = np.stack([_upper_sdf(P + e, cut) - _upper_sdf(P - e, cut) for e in np.eye(3) * h], axis=-1)
    return g / np.maximum(np.linalg.norm(g, axis=-1, keepdims=True), 1e-9)


def _ss(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _mesh_loops(name, verts_mm, faces, coll, loop_uv=None, smooth=True, subsurf=1, at=BOOT_AT):
    """A mesh object from mm vertices and faces, with per-corner UV.Real (metres) when given."""
    import bpy
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old)
    me = bpy.data.meshes.get(name)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in np.asarray(verts_mm) * 0.001], [], [tuple(f) for f in faces])
    if loop_uv is not None:
        layer = me.uv_layers.new(name="UV.Real")
        layer.data.foreach_set("uv", np.asarray(loop_uv, np.float32).ravel())
    if smooth:
        me.shade_smooth()
    me.validate()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.location = at
    if subsurf:
        sub = ob.modifiers.new("Subdivision", "SUBSURF")
        sub.levels, sub.render_levels = 0, subsurf
    return ob


def _point_attr(ob, name, values):
    me = ob.data
    att = me.attributes.get(name) or me.attributes.new(name, "FLOAT", "POINT")
    att.data.foreach_set("value", np.asarray(values, np.float32))


def _tube(path_mm, radius, sides=12, closed=False, caps=False):
    """A round tube along a polyline (parallel-transported frames): vertices, faces and per-corner UV.Real
    (u along in metres, v round the perimeter in metres, sweep.py's convention)."""
    P = np.asarray(path_mm, float)
    n = len(P)
    T = np.gradient(P, axis=0) if not closed else np.roll(P, -1, 0) - np.roll(P, 1, 0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    ref = np.array([0.0, 0.0, 1.0]) if abs(T[0, 2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    N = [np.cross(np.cross(T[0], ref), T[0])]
    N[0] /= np.linalg.norm(N[0])
    for k in range(1, n):
        v = N[-1] - T[k] * (N[-1] @ T[k])
        N.append(v / max(np.linalg.norm(v), 1e-9))
    N = np.array(N)
    B = np.cross(T, N)
    a = 2.0 * np.pi * np.arange(sides) / sides
    V = (P[:, None, :] + radius * (np.cos(a)[None, :, None] * N[:, None, :] + np.sin(a)[None, :, None] * B[:, None, :]))
    V = V.reshape(-1, 3)
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]) * 0.001
    circ = 2.0 * np.pi * radius * 0.001
    F, UV = [], []
    rows = n if closed else n - 1
    for k in range(rows):
        k1 = (k + 1) % n
        s1 = s[k1] if k1 else s[-1] + np.linalg.norm(P[0] - P[-1]) * 0.001
        for j in range(sides):
            j1 = (j + 1) % sides
            F.append((k * sides + j, k * sides + j1, k1 * sides + j1, k1 * sides + j))
            UV += [(s[k], circ * j / sides), (s[k], circ * (j + 1) / sides), (s1, circ * (j + 1) / sides),
                   (s1, circ * j / sides)]
    if caps and not closed:
        for k, sign in ((0, -1), (n - 1, 1)):
            c = len(V)
            V = np.vstack([V, P[k]])
            for j in range(sides):
                j1 = (j + 1) % sides
                F.append((k * sides + j1, k * sides + j, c) if sign > 0 else (k * sides + j, k * sides + j1, c))
                UV += [(s[k], 0.0)] * 3
    return V, F, UV


def _join(name, coll, pieces, subsurf=1):
    """One mesh object from pieces given as (V, F, per-corner UV)."""
    V, F, UV = [], [], []
    for v, f, uv in pieces:
        base = len(V)
        V.extend(np.asarray(v, float).tolist())
        F.extend(tuple(i + base for i in face) for face in f)
        UV.extend(uv)
    return _mesh_loops(name, V, F, coll, UV, subsurf=subsurf)


def _outward(P, F, UV, centre):
    """Faces (and their corner UVs) wound so the first face's normal points away from `centre`."""
    a, b, c = (np.asarray(P[i]) for i in F[0][:3])
    if np.cross(b - a, c - a) @ (a - centre) >= 0.0:
        return F, UV
    out, pos = [], 0
    for f in F:
        out += list(reversed(UV[pos:pos + len(f)]))
        pos += len(f)
    return [tuple(reversed(f)) for f in F], out


def _attr_values(ob, name):
    att = ob.data.attributes[name]
    v = np.empty(len(att.data), np.float32)
    att.data.foreach_get("value", v)
    return v


def _upper(coll):
    """The upper: rays from _C0 over a grid whose first row is the collar rim, so the opening has a clean
    edge; UV.Real by arc length along both grid directions (the seam at the heel's back)."""
    n_phi, n_th = 400, 300
    phi = 2.0 * np.pi * np.arange(n_phi) / n_phi           # 0 = +Y (the heel's back), toward +X (lateral)
    # the rim angle per column: the steepest ray that still meets the shaft's side below the top cut
    lo, hi = np.full(n_phi, 0.02), np.full(n_phi, 1.2)
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        d = np.stack([np.sin(mid) * np.sin(phi), np.sin(mid) * np.cos(phi), np.cos(mid)], -1)
        top = _cast(np.tile(_C0, (n_phi, 1)), d)[:, 2] > _TOP - 0.2
        lo, hi = np.where(top, mid, lo), np.where(top, hi, mid)
    th0 = hi + 0.002
    s = np.linspace(0.0, 1.0, n_th)
    TH = th0[None, :] + (np.pi - 1e-3 - th0[None, :]) * s[:, None]
    PH = np.broadcast_to(phi[None, :], TH.shape)
    D = np.stack([np.sin(TH) * np.sin(PH), np.sin(TH) * np.cos(PH), np.cos(TH)], -1).reshape(-1, 3)
    P = _cast(np.tile(_C0, (len(D), 1)), D)
    Nrm = _sdf_normal(P)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    # regions: Cordura shaft panels above 92 mm, except the lace stays (|x| < 30 at the front) and the
    # backstrap (|x| < 10 at the back); the toe cap behind y -86
    stay = _ss(np.abs(x), 31.0, 29.0) * _ss(y, 40.0, 30.0)
    back = _ss(np.abs(x), 11.0, 9.0) * _ss(y, 100.0, 110.0)
    cordura = _ss(z, 91.0, 93.0) * (1.0 - stay) * (1.0 - back)
    toecap = _ss(y, -85.0, -87.0)
    # overlays stand proud: leather over Cordura, the toe cap over the vamp
    lift = 0.8 * (1.0 - cordura) + 0.8 * toecap
    # flex creases (spec 02 §3.5): three folds across the vamp at the ball, each a narrow valley with a
    # rounded crest behind it, of uneven depth along its length, deeper laterally and fading down the sides,
    # and a field of fine wrinkles between them; bowed back toward the sides
    sc = y + 0.004 * x * x + 1.5 * np.sin(x / 13.0)
    side = _ss(z, 52.0, 72.0) * _ss(np.abs(x), 50.0, 30.0)
    h = np.zeros_like(x)
    for s0, a, ph in ((-63.0, 1.0, 0.0), (-50.5, 0.8, 1.7), (-39.0, 0.55, 3.1)):
        along = a * (0.65 + 0.35 * np.sin(x / 7.0 + ph)) * (0.8 + 0.2 * _ss(x, -30.0, 30.0))
        h += along * (0.45 * np.exp(-((sc - s0 - 5.5) / 3.5) ** 2) - np.exp(-((sc - s0) / 1.4) ** 2))
    fine = 0.18 * np.sin(2.0 * np.pi * sc / 3.7 + 0.8 * np.sin(x / 4.0)) * _ss(sc, -72.0, -64.0) * _ss(sc, -30.0, -38.0)
    h = 1.8 * h * side + fine * side
    disp = lift + h
    P = P + Nrm * disp[:, None]
    crease = _ss(h, 0.15, 0.6)
    # faces (rows top -> bottom, columns round), the bottom pole closed by a fan, outward winding
    idx = np.arange(n_th * n_phi).reshape(n_th, n_phi)
    F, UV = [], []
    seg_u = np.linalg.norm(np.roll(P.reshape(n_th, n_phi, 3), -1, 1) - P.reshape(n_th, n_phi, 3), axis=2) * 0.001
    U = np.concatenate([np.zeros((n_th, 1)), np.cumsum(seg_u, axis=1)], axis=1)   # n_phi + 1 columns (seam)
    seg_v = np.linalg.norm(np.diff(P.reshape(n_th, n_phi, 3), axis=0), axis=2) * 0.001
    Vv = np.vstack([np.zeros((1, n_phi)), np.cumsum(seg_v, axis=0)])
    Vv = np.concatenate([Vv, Vv[:, :1]], axis=1)
    for i in range(n_th - 1):
        for j in range(n_phi):
            j1 = (j + 1) % n_phi
            F.append((idx[i, j], idx[i + 1, j], idx[i + 1, j1], idx[i, j1]))
            UV += [(U[i, j], -Vv[i, j]), (U[i + 1, j], -Vv[i + 1, j]), (U[i + 1, j + 1], -Vv[i + 1, j + 1]),
                   (U[i, j + 1], -Vv[i, j + 1])]
    # the bottom stays open (it sits inside the sole stack): a 400-valent fan there would cost OpenSubdiv
    # minutes per render (measured: 2 min 15 s of object sync for the upper, 1 min 36 s for a 360-fan)
    F, UV = _outward(P, F, UV, _C0)
    ob = _mesh_loops(BOOT_PREFIX + "Upper", P, F, coll, UV, subsurf=1)
    weights = {"crease": crease}
    zx, zy, zz = x, y, z
    # polish (part data, spec 02 §5.5): the counter and the lateral quarter at 0.85, and the toe cap at 0.6,
    # which spec 02 does not list but its §0 item 4 asks for (broad highlights on both toe boxes)
    weights["polish"] = np.maximum.reduce([0.85 * _ss(zy, 85.0, 105.0) * _ss(zz, 100.0, 85.0),
                                           0.85 * _ss(zx, 20.0, 35.0) * _ss(zy, -35.0, -20.0) * _ss(zy, 75.0, 60.0)
                                           * _ss(zz, 95.0, 80.0),
                                           0.6 * _ss(zy, -86.0, -92.0)])
    for k, v in weights.items():
        _point_attr(ob, k, v)
    zones = {"toe": _ss(zy, -85.0, -115.0) * _ss(zz, 85.0, 70.0),
             "vamp": _ss(zy, -100.0, -85.0) * _ss(zy, 0.0, -15.0) * _ss(zz, 48.0, 62.0),
             "quarters": _ss(zz, 100.0, 90.0), "shaft_sides": _ss(zz, 90.0, 100.0),
             "collar_top": _ss(zz, 196.0, 206.0)}
    face_c = np.array([P[list(f)].mean(axis=0) for f in F])
    fx, fy, fz = face_c[:, 0], face_c[:, 1], face_c[:, 2]
    f_cordura = (_ss(fz, 91.0, 93.0) * (1.0 - _ss(np.abs(fx), 31.0, 29.0) * _ss(fy, 40.0, 30.0))
                 * (1.0 - _ss(np.abs(fx), 11.0, 9.0) * _ss(fy, 100.0, 110.0))) > 0.5
    return ob, zones, f_cordura


def _upper_point(O, D):
    P = _cast(O, D)
    return P, _sdf_normal(P)


def _sole_parts(coll):
    """Rand (rising to a toe bumper), PU midsole stripe, outsole and lugs, from the upper's outline."""
    n = 360
    psi = 2.0 * np.pi * np.arange(n) / n
    D = np.stack([np.sin(psi), np.cos(psi), np.zeros(n)], -1)   # 0 = +Y (heel), toward +X
    centre = np.array([0.0, -5.0, 0.0])

    base = _cast(np.tile(centre + [0.0, 0.0, 30.0], (n, 1)), D)   # the outline the stack follows
    toe = _ss(-np.cos(psi), 0.80, 0.97)                      # toward -Y
    heel = _ss(np.cos(psi), 0.85, 0.98)
    z_top = 38.0 + 22.0 * toe + 6.0 * heel                   # the rand rises to a toe bumper

    def row(z, off):
        """The upper's surface at height z (the outline's at or below 30 mm) pushed out horizontally by off."""
        z = np.broadcast_to(np.asarray(z, float), (n,))
        P = _cast(centre + np.stack([np.zeros(n), np.zeros(n), np.maximum(z, 30.0)], -1), D)
        N = _sdf_normal(P)
        N[:, 2] = 0.0
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
        P[:, 2] = z
        return P + N * np.broadcast_to(np.asarray(off, float), (n,))[:, None]

    def band(zs, offs, name, closed_bottom=False, extra=None, subsurf=1):
        rows = [row(z, o) for z, o in zip(zs, offs)]
        V = np.vstack(rows)
        mid = rows[len(rows) // 2]
        L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(np.vstack([mid, mid[:1]]), axis=0), axis=1))]) * 0.001
        F, UV = [], []
        for r in range(len(rows) - 1):
            v0, v1 = float(np.mean(rows[r][:, 2])) * 0.001, float(np.mean(rows[r + 1][:, 2])) * 0.001
            for j in range(n):
                j1 = (j + 1) % n
                F.append((r * n + j, (r + 1) * n + j, (r + 1) * n + j1, r * n + j1))
                UV += [(L[j], v0), (L[j], v1), (L[j + 1], v1), (L[j + 1], v0)]
        if closed_bottom:
            c = len(V)
            V = np.vstack([V, rows[0].mean(axis=0)])
            for j in range(n):
                F.append((j, (j + 1) % n, c))
                UV += [(0.0, 0.0)] * 3
        F, UV = _outward(V, F, UV, np.array([0.0, -5.0, float(np.mean(V[:, 2]))]))
        ob = _mesh_loops(BOOT_PREFIX + name, V, F, coll, UV, subsurf=subsurf)
        for k, v in (extra or {}).items():
            _point_attr(ob, k, np.concatenate([np.tile(v, len(rows)), np.zeros(len(V) - n * len(rows))]))
        return ob

    zr = [21.0, 24.0, 27.0, 30.0] + [30.0 + (z_top - 30.0) * t for t in (0.25, 0.5, 0.75, 0.92, 1.0)]
    offr = [4.0, 3.8, 3.4, 3.0, 2.4, 1.8, 1.2, 0.6, 0.0]
    rand = band(zr, offr, "Rand", extra={"bumper": toe})
    mid = band([12.5, 15.0, 18.5, 21.0], [4.5, 5.0, 4.8, 4.0], "Midsole")
    out = band([4.5, 7.0, 10.0, 12.5], [4.2, 4.4, 4.5, 4.5], "Outsole", closed_bottom=True, subsurf=0)   # a 360-fan: never subdivided
    # lugs: chevron blocks inside the footprint and teeth round its edge, 4.5 mm deep
    nrm2 = _sdf_normal(base)[:, :2]
    nrm2 /= np.linalg.norm(nrm2, axis=1, keepdims=True)
    edge = base[:, :2] + nrm2 * 4.2                          # the outsole's sidewall

    def inside(pts, poly):
        x, y = pts[:, 0], pts[:, 1]
        res = np.zeros(len(pts), bool)
        px, py = poly[:, 0], poly[:, 1]
        qx, qy = np.roll(px, -1), np.roll(py, -1)
        for k in range(len(px)):
            c = ((py[k] > y) != (qy[k] > y)) & (x < (qx[k] - px[k]) * (y - py[k]) / (qy[k] - py[k] + 1e-12) + px[k])
            res ^= c
        return res

    boxes = []   # (x, y, length, depth, angle, the polygon the corners must lie in)
    rng = np.random.default_rng(17)
    inner = base[:, :2] - nrm2 * 4.0
    for r, yc in enumerate(np.arange(-148.0, 140.0, 15.0)):
        for xc in np.arange(-60.0, 61.0, 16.0) + (8.0 if r % 2 else 0.0):
            boxes.append((xc, yc, 11.0, 8.0, np.radians(20.0 if xc < 0 else -20.0), inner))
    L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(np.vstack([edge, edge[:1]]), axis=0), axis=1))])
    outer = base[:, :2] + nrm2 * 5.0
    for s in np.arange(4.0, L[-1] - 4.0, 13.0):
        k = np.searchsorted(L, s) - 1
        t = edge[(k + 1) % len(edge)] - edge[k]
        p = edge[k] + t * (s - L[k]) / max(np.linalg.norm(t), 1e-9) - nrm2[k] * 3.3
        boxes.append((p[0], p[1], 9.0, 6.6, np.arctan2(t[1], t[0]), outer))
    V, F = [], []
    for xc, yc, w, d, ang, poly in boxes:
        c, s_ = np.cos(ang), np.sin(ang)
        corners = np.array([[-w / 2, -d / 2], [w / 2, -d / 2], [w / 2, d / 2], [-w / 2, d / 2]])
        xy = corners @ np.array([[c, s_], [-s_, c]]) + [xc, yc]
        if not inside(xy, poly).all():
            continue
        h = 4.5 - 0.4 * rng.random()   # worn a little unevenly
        b0 = len(V)
        for zz in (0.0, h):
            for p in xy:
                V.append((p[0], p[1], zz + (4.5 - h)))
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            F.append(tuple(b0 + i for i in f))
    lugs = _mesh_loops(BOOT_PREFIX + "Lugs", V, F, coll, None, smooth=False, subsurf=0)
    bev = lugs.modifiers.new("Bevel", "BEVEL")
    bev.width, bev.segments, bev.limit_method = 0.0012, 2, "ANGLE"
    return {"rand": rand, "midsole": mid, "outsole": out, "lugs": lugs, "toe_weight": toe}


def _throat():
    """Eyelet anchors on both stays (surface points and normals), bottom to top."""
    yz = [(-66.0, 80.0), (-46.0, 94.0), (-26.0, 108.0), (-10.0, 126.0), (-2.0, 150.0), (0.0, 175.0), (0.0, 199.0)]
    out = []
    for k, (y, z) in enumerate(yz):
        xo = 19.0 + 4.0 * k / (len(yz) - 1)
        pair = []
        for sx in (-1.0, 1.0):
            O = np.array([[sx * xo, 70.0, z]]) if z > 120.0 else _C0[None]
            T = np.array([sx * xo, y, z])
            D = np.array([[0.0, -1.0, 0.0]]) if z > 120.0 else ((T - _C0) / np.linalg.norm(T - _C0))[None]
            P, N = _upper_point(O, D)
            pair.append((P[0], N[0]))
        out.append(pair)
    return out


def _on_surface(pts, lift):
    """Points near the upper moved onto it (rays from _C0) and lifted along its normal."""
    pts = np.asarray(pts, float)
    D = pts - _C0
    D /= np.linalg.norm(D, axis=1, keepdims=True)
    P, N = _upper_point(np.tile(_C0, (len(D), 1)), D)
    return P + N * np.asarray(lift, float).reshape(-1, 1)


def _laces_and_hardware(coll):
    """Eyelets (gunmetal rings), a criss-crossed lace with a top bar and two tails, aglets."""
    anchors = _throat()
    rings, laces, aglets = [], [], []
    a = 2.0 * np.pi * np.arange(24) / 24
    b = 2.0 * np.pi * np.arange(10) / 10
    for pair in anchors:
        for P, N in pair:
            t1 = np.cross(N, [0.0, 0.0, 1.0] if abs(N[2]) < 0.9 else [1.0, 0.0, 0.0])
            t1 /= np.linalg.norm(t1)
            t2 = np.cross(N, t1)
            V = []
            for ai in a:
                ring_c = P + N * 0.4 + 3.6 * (np.cos(ai) * t1 + np.sin(ai) * t2)
                rad = np.cos(ai) * t1 + np.sin(ai) * t2
                for bi in b:
                    V.append(ring_c + 1.1 * (np.cos(bi) * rad + np.sin(bi) * N))
            F = [(i * 10 + j, i * 10 + (j + 1) % 10, ((i + 1) % 24) * 10 + (j + 1) % 10, ((i + 1) % 24) * 10 + j)
                 for i in range(24) for j in range(10)]
            rings.append((V, F, [(0.0, 0.0)] * 4 * len(F)))
    lift = 2.4

    def segment(p, q, over, n=28):
        s = np.linspace(0.0, 1.0, n)
        pts = p[None] * (1 - s)[:, None] + q[None] * s[:, None]
        h = lift + (1.6 if over else 0.0) * np.sin(np.pi * s) - 1.2 * (1.0 - np.sin(np.pi * s)) ** 6
        return _on_surface(pts, h)

    path_l, path_r = [], []
    (l0, _), (r0, _) = anchors[0]
    bottom = segment(l0, r0, False)
    for k in range(len(anchors) - 1):
        (lk, _), (rk, _) = anchors[k]
        (lk1, _), (rk1, _) = anchors[k + 1]
        path_l.append(segment(lk, rk1, k % 2 == 0))
        path_r.append(segment(rk, lk1, k % 2 == 1))
    (lt, nl), (rt, nr) = anchors[-1]
    top = segment(lt, rt, False)
    tails = []
    for p, side in ((rt, 1.0), (lt, -1.0)):   # tails drop down the side from the top bar
        s = np.linspace(0.0, 1.0, 30)
        pts = np.stack([p[0] + side * (6.0 + 30.0 * s), p[1] + 6.0 * s, p[2] - 4.0 - 70.0 * s ** 1.3], -1)
        P = _on_surface(pts, lift + 0.5)
        tails.append(P)
    for P in [bottom, top] + path_l + path_r + tails:
        laces.append(_tube(P, 2.0, sides=12))
    for P in tails:
        d = P[-1] - P[-2]
        d /= np.linalg.norm(d)
        aglets.append(_tube(np.array([P[-1] + d * k for k in np.linspace(0.0, 14.0, 6)]), 2.3, sides=12, caps=True))
    eyelets = _join(BOOT_PREFIX + "Eyelets", coll, rings, subsurf=1)
    lace = _join(BOOT_PREFIX + "Laces", coll, laces, subsurf=1)
    agl = _join(BOOT_PREFIX + "Aglets", coll, aglets, subsurf=1)
    return eyelets, lace, agl


def _strap_and_buckle(coll):
    """A webbing collar strap (25 x 1.3 mm, a solid strip with hard edges) round the shaft and a buckle."""
    n = 360
    psi = 2.0 * np.pi * np.arange(n) / n
    D = np.stack([np.sin(psi), np.cos(psi), np.zeros(n)], -1)
    zs = np.linspace(178.0, 203.0, 7)
    surf = []
    for z in zs:
        P = _cast(np.tile([0.0, 70.0, z], (n, 1)), D)
        N = _sdf_normal(P)
        N[:, 2] = 0.0
        N /= np.linalg.norm(N, axis=1, keepdims=True)
        surf.append((P, N))
    L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(np.vstack([surf[3][0], surf[3][0][:1]]), axis=0), axis=1))]) * 0.001
    strips = []

    def strip(rows, vs):
        V = np.vstack(rows)
        F, UV = [], []
        for r in range(len(rows) - 1):
            for j in range(n):
                j1 = (j + 1) % n
                F.append((r * n + j, r * n + j1, (r + 1) * n + j1, (r + 1) * n + j))
                UV += [(L[j], vs[r]), (L[j + 1], vs[r]), (L[j + 1], vs[r + 1]), (L[j], vs[r + 1])]
        return V, F, UV

    w = (zs - zs[0]) * 0.001
    strips.append(strip([P + N * 2.3 for P, N in surf], w))                      # outer face
    strips.append(strip([surf[-1][0] + surf[-1][1] * o for o in (2.3, 1.0)], [w[-1], w[-1] + 0.0013]))   # top edge
    strips.append(strip([P + N * 1.0 for P, N in surf[::-1]], w[::-1]))         # inner face
    strips.append(strip([surf[0][0] + surf[0][1] * o for o in (1.0, 2.3)], [0.0, 0.0013]))   # bottom edge
    strap = _join(BOOT_PREFIX + "Strap", coll, strips, subsurf=0)
    # the buckle: a rounded-rectangle frame on the lateral side (+X), in the strap's tangent plane
    k = int(round(n * 0.25))
    P0, N0 = surf[3][0][k] + surf[3][1][k] * 4.2, surf[3][1][k]
    t = surf[3][0][(k + 1) % n] - surf[3][0][k - 1]
    t /= np.linalg.norm(t)
    up = np.array([0.0, 0.0, 1.0])
    pts = []
    hw, hh, rc = 11.0, 16.0, 4.0
    for cx, cy, a0 in ((hw - rc, hh - rc, 0.0), (-hw + rc, hh - rc, 90.0), (-hw + rc, -hh + rc, 180.0),
                       (hw - rc, -hh + rc, 270.0)):
        for a in np.radians(a0 + np.linspace(0.0, 90.0, 7)):
            pts.append(P0 + t * (cx + rc * np.cos(a)) + up * (cy + rc * np.sin(a)))
    bar = [P0 + t * 0.0 + up * hh * s for s in np.linspace(-1.0, 1.0, 9)]
    buckle = _join(BOOT_PREFIX + "Buckle", coll,
                            [_tube(np.array(pts), 1.6, sides=10, closed=True), _tube(np.array(bar), 1.4, sides=10)],
                            subsurf=1)
    return strap, buckle


def _stitches(coll):
    """Stitch rows (Ø 0.4 mm dashes, 3.0 mm with 1.2 mm gaps, two rows 2 mm apart) on the overlay edges: the
    lace stays, the counter and quarters' top edge and the toe cap."""
    paths = []   # (points on the field's surface, the overlay's lift there in mm)
    for sx in (-1.0, 1.0):
        for xo in (27.0, 25.0):
            zs = np.linspace(95.0, 207.0, 60)
            O = np.stack([np.full_like(zs, sx * xo), np.full_like(zs, 70.0), zs], -1)
            paths.append((_cast(O, np.tile([0.0, -1.0, 0.0], (len(zs), 1))), 0.8))
    for zc in (88.5, 86.0):
        ang = np.radians(np.linspace(-150.0, 150.0, 160))   # round the back from stay to stay
        ang = ang[np.abs(ang) > np.radians(13.0)]           # the backstrap crosses at the back
        for part in (ang[ang < 0], ang[ang > 0]):
            D = np.stack([np.sin(part), np.cos(part), np.zeros_like(part)], -1)
            paths.append((_cast(np.tile([0.0, 70.0, zc], (len(D), 1)), D), 0.8))
    for yc in (-89.0, -91.5):
        al = np.radians(np.linspace(-100.0, 100.0, 120))
        D = np.stack([np.sin(al), np.zeros_like(al), np.cos(al)], -1)
        paths.append((_cast(np.tile([0.0, yc, 36.0], (len(D), 1)), D), 1.6))
    dashes = []
    for P, lift in paths:
        N = _sdf_normal(P)
        P = P + N * (lift + 0.06)   # on the lifted overlay, a 0.4 mm thread sunk to 0.06 mm proud of its centre
        s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        for s0 in np.arange(1.0, s[-1] - 3.0, 4.2):
            q = np.array([np.interp(s0 + d, s, P[:, i]) for d in np.linspace(0.0, 3.0, 4) for i in range(3)]).reshape(4, 3)
            dashes.append(_tube(q, 0.2, sides=6, caps=True))
    return _join(BOOT_PREFIX + "Stitches", coll, dashes, subsurf=0)


def test_boot(scene=None, side_factor=1.0):
    """Lib.Test.Boot.*: the boot test object wearing the boot's recipes (Lib.Mat.<ID>), its dust zones from
    the preset boot.toe, `crease` and `polish` on the upper, `bumper` on the rand, the side factor as the
    object property `wear_dust_scale` (1.0: the dustier left boot). Rebuilt on every call (a few seconds).
    Returns {name: object}."""
    import bpy
    scene = scene or bpy.context.scene
    coll = bpy.data.collections.get(TEST_COLL) or bpy.data.collections.new(TEST_COLL)
    if coll not in scene.collection.children_recursive:
        scene.collection.children.link(coll)
    for ob in [o for o in bpy.data.objects if o.name.startswith(BOOT_PREFIX)]:
        bpy.data.objects.remove(ob)
    upper, zones, f_cordura = _upper(coll)
    leather = np.nonzero(~f_cordura)[0]
    assign(upper, "Leather.Boot.FullGrain", part="Lib", faces=leather)
    assign(upper, "Cordura.500D.Black", part="Lib", faces=np.nonzero(f_cordura)[0])
    me = upper.data
    for rid in ("Fabric.BackFace", "Fabric.BackFace", "Foam.ClosedCell.Black", "Foam.ClosedCell.Black"):
        me.materials.append(get(rid, "Lib"))   # slots 2, 3 lining; 4, 5 the rim (Solidify's offsets)
    sol = upper.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness, sol.offset, sol.use_rim, sol.use_even_offset = 0.0025, -1.0, True, True
    sol.material_offset, sol.material_offset_rim = 2, 4
    upper.modifiers.move(1, 0)
    wear_zones(upper, "boot.toe", zones)
    parts = _sole_parts(coll)
    assign(parts["rand"], "Rubber.Rand.Black", part="Lib")
    wear_zones(parts["rand"], "boot.toe", {"bumper_top": _attr_values(parts["rand"], "bumper"), "quarters": 1.0})
    assign(parts["midsole"], "EVA.Midsole.BlueGrey", part="Lib")
    for k in ("outsole", "lugs"):
        assign(parts[k], "Rubber.Outsole.Black", part="Lib")
    eyelets, laces, aglets = _laces_and_hardware(coll)
    assign(eyelets, "Metal.Gunmetal", part="Lib")
    assign(laces, "Lace.Nylon.Black", part="Lib")
    wear_zones(laces, "boot.toe", {"laces": 1.0})
    assign(aglets, "Polymer.Black.Smooth", part="Lib")
    strap, buckle = _strap_and_buckle(coll)
    assign(strap, "Webbing.Nylon.Black", part="Lib")
    assign(buckle, "Metal.Gunmetal", part="Lib")
    stitches = _stitches(coll)
    assign(stitches, "Thread.Bonded.Black", part="Lib")
    objs = {"upper": upper, **{k: v for k, v in parts.items() if k != "toe_weight"}, "eyelets": eyelets,
            "laces": laces, "aglets": aglets, "strap": strap, "buckle": buckle, "stitches": stitches}
    for ob in objs.values():
        ob["wear_dust_scale"] = float(side_factor)
    return objs


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
    elif rec["builder"] in ("leather", "cordura"):   # the polished zone on the right half
        _paint(plane, "polish", (x > 0.5).astype(float))
    elif rec["builder"] == "rubber":                 # the toe bumper's gloss on the right half
        _paint(plane, "bumper", (x > 0.5).astype(float))


BOOT_VIEWS = ("V8", "V9", "V10")   # p16.json: the test boot three-quarter, lateral and the toe closeup


def swatch(id, out_dir=None, views=None, tier="look", samples=None):
    """Render a recipe's swatch views in spec 17's LookDev (§8.2): V1 the flat swatch beside the 18 % card,
    V2 the macro, V7 (an addition) the ball with the toe and nail (skin, nails) or the fold (fabrics), and
    for the boot's recipes V8-V10 (additions, 2026-10-27): Lib.Test.Boot wearing all of them on LookDev's
    floor. V3 needs Lib.Test.WearBlock and MG.Weather.Chips (NotBuilt). Returns {view: png path}."""
    import bpy
    env.bootstrap()
    from eval import lookdev, render
    rec = recipe(id)
    scene = lookdev.ensure()
    if bpy.context.window is not None:
        bpy.context.window.scene = scene
    nail_like = rec["builder"] == "nail"
    if views is None:
        views = ("V7",) if nail_like else ("V1", "V2", "V7")
    if "V3" in views:
        raise NotBuilt("p16.V3 needs Lib.Test.WearBlock and MG.Weather.Chips (§4.4)")
    if any(v in BOOT_VIEWS for v in views):
        if id not in C.BOOT_RECIPES:
            raise ValueError(f"views {BOOT_VIEWS} show the boot test object; {id} is not one of its recipes")
        test_boot(scene)
    objs = test_objects(scene)
    plane = bpy.data.objects[lookdev.SWATCH]
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
                    # §5.1: box projection (blend 0.2) is the sanctioned way to tile a map on a hard part
                    if (src.bl_idname == "ShaderNodeTexCoord" and outname in ("Object", "Generated")
                            and nd.projection != "BOX"):
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
    # dust zones and wear presets (2026-10-27): zones by max of weight x mask with the flag set; a preset
    # rebuilds the material in place under its own name; a recipe with its own wear takes only `none`
    me = bpy.data.meshes.new("Lib.Test.Zones")
    me.from_pydata([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [], [(0, 1, 2)])
    ob = bpy.data.objects.new("Lib.Test.Zones", me)
    try:
        w = wear_zones(ob, "boot.toe", {"toe": [1.0, 0.0, 0.0], "quarters": 1.0})
        assert np.allclose(w, [1.0, 0.15, 0.15]) and ob["wear_zones"] == 1, w
        m = get("Leather.Boot.FullGrain", "Lib")
        name = m.name
        assert apply_wear_preset(m, "metal.hardware").name == name
        assert json.loads(m["overrides"])["wear"] == "metal.hardware" and m["wear_preset"] == "metal.hardware"
        apply_wear_preset(m, "boot.toe")
        sock = get("Knit.Sock.WoolNylon", "Lib")
        apply_wear_preset(sock, "none")
        try:
            apply_wear_preset(sock, "boot.toe")
            raise AssertionError("a preset was applied to a recipe that carries its own wear")
        except ValueError:
            pass
        res["wear_presets"] = "ok"
    finally:
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
    for rid in C.CATALOGUE:
        m = bpy.data.materials.get(material_name(rid, "Lib"))
        if m is not None and m.users == 0:
            bpy.data.materials.remove(m)
    return res
