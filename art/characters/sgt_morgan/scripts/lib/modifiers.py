"""Modifier helpers (spec 18 §4.3): bevel, subdivision, solidify with the growth assertion, weighted
normals, displace, shrinkwrap, smooth by angle, and applying a stack under shape keys.

Millimetres in the API (widths, thicknesses, offsets, strengths), metres in Blender. Every helper adds or
updates the modifier of its name (default: the type's usual name), so a re-run of a part's stage changes
the stack in place instead of stacking duplicates, sets every property it is given, refuses a property the
modifier does not have, and returns the modifier.

The prototype trap (notes/research_prototypes.md §0 and §5 (c)): Solidify's offset sign follows the face
normals, not the viewer, so leather grown with offset +1 on faces flipped to face the camera grew toward it
and buried the eyelets. solidify() therefore states where the thickness should go (`grow`) and checks it on
the evaluated mesh: the mean displacement the modifier adds, measured from a centre (out or in) or along a
direction, must have the stated sign and at least a quarter of its nominal size. The bounding boxes before
and after are reported with it. By default `grow` follows the project's convention, normals pointing out of
the solid (away from the centre), so offset -1 grows inward and +1 outward, and a flipped shell fails.

apply_keep_shapes() is spec 08 §7.6's apply_modifiers_keep_shapes: each shape key is evaluated through the
stack on its own (the key's absolute shape, its vertex group lifted), the stack is applied to the basis, and
the keys come back as the evaluated shapes with their names, relative keys, values, ranges, groups and mute
flags. Kept modifiers (the Armature) stay on the stack and are left out of the captured shapes. The result
equals the live stack at every mix of key values when the applied modifiers are linear in the positions
(subdivision, a displace in a fixed direction); a normal-direction displace or a vertex-grouped key whose
weights vary under a subdivision come back as the nearest per-key approximation, as any per-key apply does.
"""
import math

import numpy as np

from . import ctx

MM = 0.001
SMOOTH_GROUP = "Lib.GN.SmoothByAngle"
SMOOTH_GROUP_VERSION = 1


# --------------------------------------------------------------------------- the modifier of a name

def _mod(ob, name, kind):
    """The modifier `name` of type `kind`, made if missing; one of another type under that name is replaced."""
    m = ob.modifiers.get(name)
    if m is not None and m.type != kind:
        ob.modifiers.remove(m)
        m = None
    if m is None:
        m = ob.modifiers.new(name, kind)
        if m is None:
            raise TypeError(f"{ob.name} ({ob.type}) cannot take a {kind} modifier")
    return m


def _set(m, props):
    for k, v in props.items():
        if not hasattr(m, k):
            raise AttributeError(f"{m.type} modifier has no property {k!r}")
        setattr(m, k, v)
    return m


def _group(m, vertex_group, invert=False):
    if vertex_group:
        ob = m.id_data
        if ob.vertex_groups.get(vertex_group) is None:
            raise KeyError(f"{ob.name} has no vertex group {vertex_group!r}")
        m.vertex_group = vertex_group
        if hasattr(m, "invert_vertex_group"):
            m.invert_vertex_group = invert
    return m


# --------------------------------------------------------------------------- the helpers

def bevel(ob, width, segments=2, angle_deg=30.0, profile=0.5, harden=False, *, limit="ANGLE", clamp=True,
          vertex_group=None, name="Bevel", **props):
    """Bevel edges by `width` mm in `segments`, limited to edges sharper than angle_deg (limit 'ANGLE'),
    or by 'WEIGHT', 'VGROUP' (with vertex_group) or 'NONE'; profile 0.5 is round; harden sets harden
    normals (custom normals that keep the flats flat)."""
    m = _mod(ob, name, "BEVEL")
    m.width = width * MM
    m.segments = int(segments)
    m.limit_method = "VGROUP" if vertex_group else limit
    m.angle_limit = math.radians(angle_deg)
    m.profile = profile
    m.harden_normals = bool(harden)
    m.use_clamp_overlap = bool(clamp)
    _group(m, vertex_group)
    return _set(m, props)


def subdiv(ob, levels=1, render_levels=None, *, quality=3, limit_surface=True, simple=False,
           name="Subdivision", **props):
    """Catmull-Clark (or simple) subdivision; render_levels defaults to levels."""
    m = _mod(ob, name, "SUBSURF")
    m.subdivision_type = "SIMPLE" if simple else "CATMULL_CLARK"
    m.levels = int(levels)
    m.render_levels = int(levels if render_levels is None else render_levels)
    m.quality = int(quality)
    m.use_limit_surface = bool(limit_surface)
    return _set(m, props)


def weighted_normal(ob, weight=50, keep_sharp=True, *, mode="FACE_AREA", thresh=0.01, face_influence=False,
                    vertex_group=None, name="WeightedNormal", **props):
    """Weighted Normal (custom normals weighted by face area, corner angle or both); after a bevel it keeps
    the flat faces flat."""
    m = _mod(ob, name, "WEIGHTED_NORMAL")
    m.weight = int(weight)
    m.keep_sharp = bool(keep_sharp)
    m.mode = mode
    m.thresh = thresh
    m.use_face_influence = bool(face_influence)
    _group(m, vertex_group)
    return _set(m, props)


def displace(ob, strength, texture=None, *, direction="NORMAL", mid_level=0.0, space="LOCAL", coords="LOCAL",
             uv_layer=None, vertex_group=None, name="Displace", **props):
    """Displace by `strength` mm times (texture value - mid_level) times the group weight. Without a texture
    the value is 1, so with the default mid_level 0 every vertex moves exactly strength x its weight along
    `direction` (spec 02 §4.4's shell build-up by vertex-group weights). Note mid_level 0, not Blender's 0.5."""
    m = _mod(ob, name, "DISPLACE")
    m.strength = strength * MM
    m.texture = texture
    m.direction = direction
    m.mid_level = mid_level
    m.space = space
    m.texture_coords = "UV" if uv_layer else coords
    if uv_layer:
        m.uv_layer = uv_layer
    _group(m, vertex_group)
    return _set(m, props)


def shrinkwrap(ob, target, offset=0.0, *, method="NEAREST_SURFACEPOINT", wrap_mode="ON_SURFACE", project=None,
               negative=True, positive=True, limit=0.0, vertex_group=None, name="Shrinkwrap", **props):
    """Shrinkwrap onto `target` with `offset` mm. method 'NEAREST_SURFACEPOINT', 'NEAREST_VERTEX', 'PROJECT'
    (along the vertex normals, or along the local axes named in `project`, e.g. "Z"; both directions unless
    told otherwise, limited to `limit` mm when > 0) or 'TARGET_PROJECT'."""
    m = _mod(ob, name, "SHRINKWRAP")
    m.target = target
    m.wrap_method = method
    m.wrap_mode = wrap_mode
    m.offset = offset * MM
    if method == "PROJECT":
        axes = (project or "").upper()
        m.use_project_x, m.use_project_y, m.use_project_z = ("X" in axes), ("Y" in axes), ("Z" in axes)
        m.use_negative_direction, m.use_positive_direction = bool(negative), bool(positive)
        m.project_limit = limit * MM
    _group(m, vertex_group)
    return _set(m, props)


def smooth_group():
    """The shared node group behind smooth_by_angle (built once, rebuilt when its version changes): every
    face smooth, an edge smooth when its angle is at most `Angle` and, unless `Ignore Sharpness`, it was
    not marked sharp. Blender's own Smooth by Angle asset does the same; this one needs no asset file."""
    import bpy
    ng = bpy.data.node_groups.get(SMOOTH_GROUP)
    if ng is not None and ng.get("version") == SMOOTH_GROUP_VERSION:
        return ng
    if ng is not None:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(SMOOTH_GROUP, "GeometryNodeTree")
    ng["version"] = SMOOTH_GROUP_VERSION
    ng.is_modifier = True
    it = ng.interface
    it.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    a = it.new_socket("Angle", in_out="INPUT", socket_type="NodeSocketFloat")
    a.subtype, a.default_value, a.min_value, a.max_value = "ANGLE", math.radians(30.0), 0.0, math.pi
    it.new_socket("Ignore Sharpness", in_out="INPUT", socket_type="NodeSocketBool")
    it.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    angle = N.new("GeometryNodeInputMeshEdgeAngle")
    cmp = N.new("FunctionNodeCompare")
    cmp.data_type, cmp.operation = "FLOAT", "LESS_EQUAL"
    smooth_in = N.new("GeometryNodeInputEdgeSmooth")
    keep = N.new("FunctionNodeBooleanMath")
    keep.operation = "OR"
    both = N.new("FunctionNodeBooleanMath")
    both.operation = "AND"
    faces = N.new("GeometryNodeSetShadeSmooth")
    faces.domain = "FACE"
    edges = N.new("GeometryNodeSetShadeSmooth")
    edges.domain = "EDGE"
    faces.inputs["Shade Smooth"].default_value = True
    L.new(angle.outputs["Unsigned Angle"], cmp.inputs[0])
    L.new(gi.outputs["Angle"], cmp.inputs[1])
    L.new(gi.outputs["Ignore Sharpness"], keep.inputs[0])
    L.new(smooth_in.outputs[0], keep.inputs[1])
    L.new(cmp.outputs[0], both.inputs[0])
    L.new(keep.outputs[0], both.inputs[1])
    L.new(gi.outputs["Geometry"], faces.inputs["Geometry"])
    L.new(faces.outputs["Geometry"], edges.inputs["Geometry"])
    L.new(both.outputs[0], edges.inputs["Shade Smooth"])
    L.new(edges.outputs["Geometry"], go.inputs["Geometry"])
    for k, nd in enumerate((gi, angle, smooth_in, cmp, keep, both, faces, edges, go)):
        nd.location = (200 * k, 0)
    return ng


def smooth_by_angle(ob, angle_deg=30.0, ignore_sharp=False, *, pin_last=True, name="SmoothByAngle"):
    """Shade smooth with edges sharper than angle_deg kept sharp, as a modifier (pinned last by default, as
    Blender's own, so it sees the final geometry)."""
    ng = smooth_group()
    m = _mod(ob, name, "NODES")
    m.node_group = ng
    ids = {s.name: s.identifier for s in ng.interface.items_tree if getattr(s, "in_out", None) == "INPUT"}
    m[ids["Angle"]] = math.radians(angle_deg)
    m[ids["Ignore Sharpness"]] = bool(ignore_sharp)
    m.use_pin_to_last = bool(pin_last)
    ob.update_tag()
    return m


# --------------------------------------------------------------------------- solidify and its assertion

def _world_mm(ob, depsgraph=None):
    """World-space vertex positions (mm) of the object's evaluated mesh."""
    import bpy
    dg = depsgraph or bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        co = np.empty(len(me.vertices) * 3, np.float64)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
    finally:
        ev.to_mesh_clear()
    M = np.array(ob.matrix_world, float)
    return (co @ M[:3, :3].T + M[:3, 3]) / MM


def _stack_state(ob, upto, include):
    """Evaluate ob with the modifiers from `upto` on disabled (and `upto` itself enabled when include)."""
    import bpy
    names = [m.name for m in ob.modifiers]
    k = names.index(upto)
    saved = [(m, m.show_viewport) for m in ob.modifiers]
    try:
        for i, m in enumerate(ob.modifiers):
            if i > k or (i == k and not include):
                m.show_viewport = False
        ob.update_tag()
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        return _world_mm(ob, dg)
    finally:
        for m, v in saved:
            m.show_viewport = v
        ob.update_tag()


def check_growth(ob, modifier, grow=None, centre=None):
    """The prototype trap's assertion for a Solidify modifier on ob. grow: 'out' or 'in' (away from or
    toward `centre`, mm world, default the base mesh's bounding-box centre), a world direction (3,), or
    per-vertex directions (V, 3) aligned with the base mesh's vertices; None means the convention, normals
    out: 'out' for a positive offset, 'in' for a negative one. Returns the measurement; raises
    AssertionError when the thickness went the other way or neither way."""
    import bpy
    m = ob.modifiers[modifier] if isinstance(modifier, str) else modifier
    if bpy.context.scene not in ob.users_scene:
        raise RuntimeError(f"{ob.name} is not in the scene: its evaluated mesh cannot be checked")
    t, off = m.thickness / MM, m.offset
    base = _stack_state(ob, m.name, include=False)
    ev = _stack_state(ob, m.name, include=True)
    want = abs(off) * abs(t) / 2.0  # the mean shift of a pair of surfaces at (off -/+ 1) t / 2
    rec = {"thickness_mm": t, "offset": off, "bbox_base_mm": [base.min(0).tolist(), base.max(0).tolist()],
           "bbox_eval_mm": [ev.min(0).tolist(), ev.max(0).tolist()], "nominal_mm": want}
    if want < 0.05 * abs(t) or len(base) == 0:
        rec.update(checked=False, why="centred offset: no side to check")
        return rec
    if grow is None:
        grow = "out" if off * t > 0 else "in"
    if isinstance(grow, str):
        if grow not in ("out", "in"):
            raise ValueError(f"grow {grow!r}: 'out', 'in', a direction or per-vertex directions")
        c = np.asarray(centre, float) if centre is not None else (base.min(0) + base.max(0)) / 2.0
        delta = np.linalg.norm(ev - c, axis=1).mean() - np.linalg.norm(base - c, axis=1).mean()
        sign = 1.0 if grow == "out" else -1.0
        rec["centre_mm"] = c.tolist()
    else:
        d = np.asarray(grow, float)
        if d.ndim == 1:
            d = d / np.linalg.norm(d)
            delta = float((ev @ d).mean() - (base @ d).mean())
        else:
            if len(d) != len(base):
                raise ValueError(f"{len(d)} directions for {len(base)} base vertices")
            from mathutils.kdtree import KDTree
            tree = KDTree(len(base))
            for i, p in enumerate(base):
                tree.insert(p, i)
            tree.balance()
            d = d / np.linalg.norm(d, axis=1, keepdims=True)
            idx = np.array([tree.find(p)[1] for p in ev])
            delta = float(((ev - base[idx]) * d[idx]).sum(1).mean())
        sign = 1.0
        grow = "direction"
    rec.update(checked=True, grow=grow, delta_mm=float(delta))
    if sign * delta < 0.25 * want:
        where = "the other way" if sign * delta < -0.25 * want else "neither way"
        raise AssertionError(
            f"{ob.name}: {m.name} (thickness {t:g} mm, offset {off:+g}) grew {where} (mean shift {delta:+.3f} mm "
            f"against {sign * want:+.3f} mm {grow}): the face normals do not point the way the offset assumes "
            "(research_prototypes §0); flip the normals or the offset sign, or state grow= correctly")
    return rec


def solidify(ob, thickness, offset=-1.0, even=True, rim=True, *, grow=None, centre=None, check=True,
             vertex_group=None, factor=None, material_offset=0, rim_material_offset=0, name="Solidify",
             **props):
    """Solidify by `thickness` mm. offset -1 puts the thickness behind the faces (against their normals),
    +1 in front, 0 centred. vertex_group with factor (the thickness factor where the group's weight is 0)
    varies the thickness. With check (the default), the growth assertion above runs on the evaluated mesh;
    its record is left on the modifier's object as `ob["Lib.SolidifyCheck"]`."""
    m = _mod(ob, name, "SOLIDIFY")
    m.thickness = thickness * MM
    m.offset = offset
    m.use_even_offset = bool(even)
    m.use_rim = bool(rim)
    m.use_quality_normals = True
    m.material_offset = int(material_offset)
    m.material_offset_rim = int(rim_material_offset)
    _group(m, vertex_group)
    if factor is not None:
        m.thickness_vertex_group = factor
    _set(m, props)
    if check:
        rec = check_growth(ob, m, grow, centre)
        ob["Lib.SolidifyCheck"] = {k: v for k, v in rec.items() if isinstance(v, (int, float, str, bool))}
    return m


# --------------------------------------------------------------------------- applying under shape keys

def _key_record(kb):
    return {"name": kb.name, "relative": kb.relative_key.name, "value": kb.value, "min": kb.slider_min,
            "max": kb.slider_max, "group": kb.vertex_group, "mute": kb.mute, "interp": kb.interpolation}


def _evaluated_local(ob, dg):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
    finally:
        ev.to_mesh_clear()
    return co.reshape(-1, 3)


def apply_keep_shapes(ob, keep=("ARMATURE",), names=None):
    """Apply modifiers while keeping the shape keys (spec 08 §7.6). names: the modifiers to apply (default
    every modifier whose type is not in `keep`), applied in stack order; kept modifiers stay, disabled while
    the shapes are captured. A kept modifier that sits after an applied one is refused (applying would move
    it ahead of it). Every key's shape must evaluate to the same vertex count. Returns a record."""
    import bpy
    mods = list(ob.modifiers)
    if names is None:
        names = [m.name for m in mods if m.type not in keep]
    names = list(names)
    missing = [n for n in names if n not in ob.modifiers]
    if missing:
        raise KeyError(f"{ob.name} has no modifiers {missing}")
    order = [m.name for m in mods]
    last = max((order.index(n) for n in names), default=-1)
    stay = [m for m in mods if m.name not in names]
    late = [m.name for m in stay if order.index(m.name) < last and m.show_viewport
            and order.index(m.name) > min(order.index(n) for n in names)]
    if late:
        raise ValueError(f"{ob.name}: kept modifiers {late} sit between applied ones; reorder the stack first")
    if not names:
        return {"applied": [], "kept": [m.name for m in stay], "keys": 0}
    keys = ob.data.shape_keys if ob.type == "MESH" else None
    if keys is None or len(keys.key_blocks) == 0:
        ctx.apply_all(ob, names)
        return {"applied": names, "kept": [m.name for m in ob.modifiers], "keys": 0}

    blocks = list(keys.key_blocks)
    recs = [_key_record(kb) for kb in blocks]
    saved_show = [(m, m.show_viewport) for m in stay]
    saved_lock, saved_index = ob.show_only_shape_key, ob.active_shape_key_index
    shapes = []
    try:
        for m, _ in saved_show:
            m.show_viewport = False
        ob.show_only_shape_key = True
        for i, kb in enumerate(blocks):
            group, mute = kb.vertex_group, kb.mute
            kb.vertex_group, kb.mute = "", False
            try:
                ob.active_shape_key_index = i
                ob.update_tag()
                dg = bpy.context.evaluated_depsgraph_get()
                dg.update()
                shapes.append(_evaluated_local(ob, dg))
            finally:
                kb.vertex_group, kb.mute = group, mute
    finally:
        ob.show_only_shape_key, ob.active_shape_key_index = saved_lock, saved_index
        for m, v in saved_show:
            m.show_viewport = v
    counts = {len(s) for s in shapes}
    if len(counts) != 1:
        raise ValueError(f"{ob.name}: the stack gives different vertex counts per shape key {sorted(counts)} "
                         "(an angle-limited bevel or a weld?); these modifiers cannot be applied under keys")

    basis = np.empty(len(ob.data.vertices) * 3, np.float32)
    keys.reference_key.data.foreach_get("co", basis)
    ob.shape_key_clear()
    ob.data.vertices.foreach_set("co", basis)
    ob.data.update()
    ctx.apply_all(ob, names)
    got = np.empty(len(ob.data.vertices) * 3, np.float32)
    ob.data.vertices.foreach_get("co", got)
    got = got.reshape(-1, 3)
    if got.shape != shapes[0].shape or np.abs(got - shapes[0]).max() > 1e-5:
        raise AssertionError(f"{ob.name}: the applied mesh differs from the captured basis "
                             f"({got.shape} vs {shapes[0].shape}); the stack does not apply as it evaluates")
    made = {}
    for rec, co in zip(recs, shapes):
        kb = ob.shape_key_add(name=rec["name"], from_mix=False)
        kb.data.foreach_set("co", co.ravel())
        made[rec["name"]] = kb
    for rec in recs:
        kb = made[rec["name"]]
        kb.relative_key = made.get(rec["relative"], ob.data.shape_keys.reference_key)
        kb.slider_min, kb.slider_max = rec["min"], rec["max"]
        kb.value = rec["value"]
        kb.mute, kb.interpolation = rec["mute"], rec["interp"]
        if rec["group"] and ob.vertex_groups.get(rec["group"]) is not None:
            kb.vertex_group = rec["group"]
    ob.active_shape_key_index = min(saved_index, len(recs) - 1)
    ob.data.update()
    return {"applied": names, "kept": [m.name for m in ob.modifiers], "keys": len(recs),
            "vertices": int(len(got))}


# --------------------------------------------------------------------------- self-test

def _mesh_object(name, verts, faces):
    import bpy
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _cube(name, size_mm=20.0, centre=(0.0, 0.0, 0.0)):
    h = size_mm * MM / 2
    c = np.asarray(centre, float) * MM
    v = [c + h * np.array(p) for p in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                                       (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return _mesh_object(name, v, f)


def _grid(name, n=8, size_mm=40.0, z_mm=0.0):
    g = np.linspace(-size_mm / 2, size_mm / 2, n + 1) * MM
    X, Y = np.meshgrid(g, g)
    v = np.stack([X.ravel(), Y.ravel(), np.full(X.size, z_mm * MM)], 1)
    idx = np.arange(X.size).reshape(n + 1, n + 1)
    f = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    return _mesh_object(name, v, f)


def _eval_info(ob):
    import bpy
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        sharp = me.attributes.get("sharp_edge")
        flat = me.attributes.get("sharp_face")
        n_sharp = 0
        if sharp is not None:
            a = np.zeros(len(me.edges), bool)
            sharp.data.foreach_get("value", a)
            n_sharp = int(a.sum())
        n_flat = 0
        if flat is not None:
            a = np.zeros(len(me.polygons), bool)
            flat.data.foreach_get("value", a)
            n_flat = int(a.sum())
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        return {"verts": len(me.vertices), "faces": len(me.polygons), "edges": len(me.edges), "sharp": n_sharp,
                "flat": n_flat, "custom_normals": bool(me.has_custom_normals), "co": co.reshape(-1, 3) / MM}
    finally:
        ev.to_mesh_clear()


def selftest():
    """Each helper on scratch meshes: the trap caught on a flipped shell and a flipped sheet, bevel and
    harden, subdivision counts, a vertex-group displace, shrinkwrap onto a sphere at an offset, smooth by
    angle on a cube, and apply_keep_shapes against the live stack at mixed key values."""
    import bpy
    R, made = {}, []
    had_group = bpy.data.node_groups.get(SMOOTH_GROUP) is not None
    try:
        # solidify: a closed cube with outward normals; -1 grows in, +1 grows out (convention default)
        cube = _cube("SelftestMod.Cube")
        made.append(cube)
        solidify(cube, 2.0, offset=-1)
        rin = dict(cube["Lib.SolidifyCheck"])
        assert rin["grow"] == "in" and rin["delta_mm"] < -0.5, rin
        bb = _eval_info(cube)["co"]
        assert abs(bb.max() - 10.0) < 1e-4, "inward growth moved the outer surface"
        solidify(cube, 2.0, offset=+1)
        rout = dict(cube["Lib.SolidifyCheck"])
        assert rout["grow"] == "out" and rout["delta_mm"] > 0.5 and abs(_eval_info(cube)["co"].max() - 12.0) < 1e-3
        assert [m.name for m in cube.modifiers] == ["Solidify"], "solidify() stacked a second modifier"
        # the trap: normals flipped inward, offset +1 meant as outward growth
        cube.modifiers.clear()
        cube.data.flip_normals()
        try:
            solidify(cube, 2.0, offset=+1, grow="out")
            raise AssertionError("a flipped shell grown with offset +1 passed as outward")
        except AssertionError as e:
            assert "other way" in str(e), e
        R["trap_cube"] = "caught"
        cube.modifiers.clear()
        solidify(cube, 2.0, offset=-1, grow="out")  # the fix: offset -1 on the flipped shell grows out
        # an open sheet: normal +Z; growth stated as a direction
        sheet = _grid("SelftestMod.Sheet", n=4)
        made.append(sheet)
        solidify(sheet, 1.5, offset=+1, grow=(0, 0, 1))
        co = _eval_info(sheet)["co"]
        assert abs(co[:, 2].max() - 1.5) < 1e-4 and abs(co[:, 2].min()) < 1e-6
        sheet.modifiers.clear()
        sheet.data.flip_normals()
        try:
            solidify(sheet, 1.5, offset=+1, grow=(0, 0, 1))
            raise AssertionError("a flipped sheet passed")
        except AssertionError as e:
            assert "other way" in str(e), e
        # per-vertex directions (the strip case): every vertex should grow along +Z
        sheet.modifiers.clear()
        sheet.data.flip_normals()
        dirs = np.tile([0.0, 0.0, 1.0], (len(sheet.data.vertices), 1))
        solidify(sheet, 1.5, offset=+1, grow=dirs)
        R["solidify"] = {"in": round(rin["delta_mm"], 3), "out": round(rout["delta_mm"], 3)}

        # bevel with harden, then weighted normal and smooth by angle
        bev = _cube("SelftestMod.Bevel")
        made.append(bev)
        bevel(bev, 1.0, segments=3, angle_deg=30, harden=True)
        info = _eval_info(bev)
        assert info["faces"] > 6 + 12 * 3, info["faces"]  # the faces, three strips per edge, the corners
        assert abs(info["co"].max() - 10.0) < 1e-4, "a bevel moved the outer faces"
        assert info["custom_normals"], "harden normals left no custom normals"
        R["bevel_faces"] = info["faces"]
        weighted_normal(bev)
        assert bev.modifiers[-1].type == "WEIGHTED_NORMAL"

        sm = _cube("SelftestMod.Smooth")
        made.append(sm)
        smooth_by_angle(sm, 30.0)
        i30 = _eval_info(sm)
        smooth_by_angle(sm, 100.0)
        i100 = _eval_info(sm)
        assert i30["sharp"] == 12 and i30["flat"] == 0, i30
        assert i100["sharp"] == 0 and i100["flat"] == 0, i100
        assert len(sm.modifiers) == 1 and sm.modifiers[0].use_pin_to_last
        e0 = sm.data.edges[0]
        e0.use_edge_sharp = True
        sm.data.update()
        assert _eval_info(sm)["sharp"] == 1, "a marked sharp edge was smoothed"
        smooth_by_angle(sm, 100.0, ignore_sharp=True)
        assert _eval_info(sm)["sharp"] == 0
        R["smooth_by_angle"] = {"30deg_sharp": i30["sharp"], "100deg_sharp": i100["sharp"]}

        # subdivision
        sd = _cube("SelftestMod.Subdiv")
        made.append(sd)
        m = subdiv(sd, 2, render_levels=3)
        assert m.levels == 2 and m.render_levels == 3 and _eval_info(sd)["faces"] == 6 * 16

        # displace by a vertex group: weight 1 on half the grid moves it 2 mm along the normal
        dp = _grid("SelftestMod.Displace", n=4)
        made.append(dp)
        vg = dp.vertex_groups.new(name="SelftestMod.Half")
        half = [v.index for v in dp.data.vertices if v.co.x > 1e-6]
        vg.add(half, 1.0, "REPLACE")
        displace(dp, 2.0, vertex_group="SelftestMod.Half")
        z = _eval_info(dp)["co"][:, 2]
        assert np.allclose(z[half], 2.0, atol=1e-5) and np.allclose(np.delete(z, half), 0.0, atol=1e-6), z
        try:
            displace(dp, 1.0, vertex_group="SelftestMod.Nope")
            raise AssertionError("a missing vertex group was accepted")
        except KeyError:
            pass
        try:
            bevel(dp, 1.0, not_a_property=1)
            raise AssertionError("an unknown property was accepted")
        except AttributeError:
            pass

        # shrinkwrap a grid onto a sphere of 30 mm with a 1 mm offset
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, segments=64, ring_count=32, location=(0, 0, 0))
        sph = bpy.context.active_object
        sph.name = "SelftestMod.Sphere"
        made.append(sph)
        sw = _grid("SelftestMod.Wrap", n=6, size_mm=20.0, z_mm=40.0)
        made.append(sw)
        shrinkwrap(sw, sph, 1.0)
        r = np.linalg.norm(_eval_info(sw)["co"], axis=1)
        assert np.all(np.abs(r - 31.0) < 0.15), (r.min(), r.max())  # the sphere is faceted: 0.15 mm slack
        R["shrinkwrap_r_mm"] = [round(float(r.min()), 3), round(float(r.max()), 3)]

        # apply_keep_shapes: a grid with Subdivision and Displace, three keys (one by group, one relative
        # to another), an Armature first and kept; the live mix and the applied mix must agree
        ks = _grid("SelftestMod.Keys", n=4)
        made.append(ks)
        arm = bpy.data.armatures.new("SelftestMod.Arm")
        rig = bpy.data.objects.new("SelftestMod.Rig", arm)
        bpy.context.scene.collection.objects.link(rig)
        made.append(rig)
        a = ks.modifiers.new("Armature", "ARMATURE")
        a.object = rig
        grp = ks.vertex_groups.new(name="SelftestMod.Side")  # uniform: a weight field through a subdivision
        grp.add([v.index for v in ks.data.vertices], 0.6, "REPLACE")  # is only exact when it is constant
        ks.shape_key_add(name="Basis", from_mix=False)
        rng = np.random.default_rng(3)
        n = len(ks.data.vertices)
        for kname in ("Bulge", "Tilt", "OnTilt"):
            kb = ks.shape_key_add(name=kname, from_mix=False)
            co = np.empty(n * 3, np.float32)
            kb.data.foreach_get("co", co)
            co = co.reshape(-1, 3)
            co[:, 2] += rng.normal(0, 0.002, n)
            kb.data.foreach_set("co", co.ravel())
        kbs = ks.data.shape_keys.key_blocks
        kbs["Tilt"].vertex_group = "SelftestMod.Side"
        kbs["OnTilt"].relative_key = kbs["Tilt"]
        subdiv(ks, 1)
        displace(ks, 0.5, direction="Z")  # linear in the positions, so the comparison is exact
        values =[(0.3, 0.7, 0.4), (1.0, 0.0, 1.0), (0.0, 1.0, 0.5)]

        def live(vals):
            for kname, v in zip(("Bulge", "Tilt", "OnTilt"), vals):
                ks.data.shape_keys.key_blocks[kname].value = v
            return _eval_info(ks)["co"]
        before = [live(v) for v in values]
        rec = apply_keep_shapes(ks)
        assert rec["applied"] == ["Subdivision", "Displace"] and rec["kept"] == ["Armature"], rec
        assert [k.name for k in ks.data.shape_keys.key_blocks] == ["Basis", "Bulge", "Tilt", "OnTilt"]
        kbs = ks.data.shape_keys.key_blocks
        assert kbs["Tilt"].vertex_group == "SelftestMod.Side" and kbs["OnTilt"].relative_key.name == "Tilt"
        after = [live(v) for v in values]
        err = max(float(np.abs(b - c).max()) for b, c in zip(before, after))
        assert err < 1e-3, f"applied keys differ from the live stack by {err} mm"
        R["apply_keep_shapes"] = {"vertices": rec["vertices"], "max_err_mm": err}
        # a kept modifier between applied ones is refused
        bad = _grid("SelftestMod.Order", n=2)
        made.append(bad)
        bad.shape_key_add(name="Basis")
        subdiv(bad, 1)
        bad.modifiers.new("Armature", "ARMATURE")
        displace(bad, 0.5)
        try:
            apply_keep_shapes(bad)
            raise AssertionError("a kept modifier between applied ones was accepted")
        except ValueError:
            pass
        return R
    finally:
        for o in made:
            data = o.data
            bpy.data.objects.remove(o)
            if data is not None and data.users == 0:
                (bpy.data.meshes if isinstance(data, bpy.types.Mesh) else bpy.data.armatures).remove(data)
        ng = bpy.data.node_groups.get(SMOOTH_GROUP)
        if ng is not None and not had_group and ng.users == 0:
            bpy.data.node_groups.remove(ng)
