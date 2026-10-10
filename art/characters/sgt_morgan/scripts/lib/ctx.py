"""Blender context rules for headless scripts (research C, notes/research_blender_capabilities.md §7).

temp_override is enough for object-level operators (modifier_apply, ptcache.bake_all, curve
conversion, the exporters), but mode_set and parent_set ignore it in background mode and silently act
on the view layer's real active object, so anything that changes mode goes through the real selection.
A Modifier reference dangles after an apply, so names are captured before applying.
"""
import contextlib


def _view_layer(view_layer=None):
    import bpy
    return view_layer or bpy.context.view_layer


def set_active(ob, select=(), view_layer=None):
    """Make ob the active object and the only selected one (plus `select`), for real."""
    vl = _view_layer(view_layer)
    for o in vl.objects:
        if o.select_get():
            o.select_set(False)
    for o in (ob, *select):
        o.select_set(True)
    vl.objects.active = ob
    return ob


def _object_mode(vl):
    import bpy
    act = vl.objects.active
    if act is not None and act.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


@contextlib.contextmanager
def mode(ob, m="EDIT", view_layer=None):
    """Enter mode `m` on ob through the real selection; back to OBJECT and the old selection after."""
    import bpy
    vl = _view_layer(view_layer)
    prev_active = vl.objects.active
    prev_selected = [o for o in vl.objects if o.select_get()]
    _object_mode(vl)
    set_active(ob, view_layer=vl)
    bpy.ops.object.mode_set(mode=m)
    if ob.mode != m:
        raise RuntimeError(f"mode_set({m}) left {ob.name} in {ob.mode}")
    try:
        yield ob
    finally:
        try:
            if vl.objects.active is not None and vl.objects.active.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
        finally:
            for o in vl.objects:
                o.select_set(False)
            for o in prev_selected:
                try:
                    o.select_set(True)
                except ReferenceError:  # deleted inside the block
                    pass
            try:
                vl.objects.active = prev_active
            except ReferenceError:
                vl.objects.active = None


def override(**kw):
    """bpy.context.temp_override with the object keys filled in from `object` (or `active_object`)."""
    import bpy
    ob = kw.get("object") or kw.get("active_object")
    if ob is not None:
        kw.setdefault("object", ob)
        kw.setdefault("active_object", ob)
        kw.setdefault("selected_objects", [ob])
        kw.setdefault("selected_editable_objects", [ob])
    return bpy.context.temp_override(**kw)


def apply_modifier(ob, name):
    """Apply one modifier by name; returns the names left on the stack."""
    import bpy
    names = [m.name for m in ob.modifiers]
    if name not in names:
        raise KeyError(f"{ob.name} has no modifier {name!r} (has {names})")
    if ob.type == "MESH" and ob.data.shape_keys is not None:
        raise ValueError(f"{ob.name} has shape keys; modifier_apply refuses them "
                         "(use modifiers.apply_keep_shapes)")
    with override(object=ob):
        bpy.ops.object.modifier_apply(modifier=name)
    return [m.name for m in ob.modifiers]


def apply_all(ob, names=None):
    """Apply the named modifiers (default: the whole stack) top to bottom, by captured names."""
    for n in list(names) if names is not None else [m.name for m in ob.modifiers]:
        apply_modifier(ob, n)
    return ob


def selftest():
    import bpy
    sc = bpy.context.scene
    made = []
    try:
        me = bpy.data.meshes.new("Selftest.Ctx.Mesh")
        me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
        ob = bpy.data.objects.new("Selftest.Ctx.Plane", me)
        arm = bpy.data.armatures.new("Selftest.Ctx.Arm")
        rig = bpy.data.objects.new("Selftest.Ctx.Rig", arm)
        for o in (ob, rig):
            sc.collection.objects.link(o)
            made.append(o)
        set_active(ob, select=(rig,))
        assert bpy.context.view_layer.objects.active == ob and ob.select_get() and rig.select_get()

        # the research gotcha: mode_set acts on the real active object, so mode() must make rig active
        with mode(rig, "EDIT"):
            assert rig.mode == "EDIT" and ob.mode == "OBJECT"
            b = arm.edit_bones.new("Selftest.Bone")
            b.head, b.tail = (0, 0, 0), (0, 0, 0.1)
        assert rig.mode == "OBJECT" and "Selftest.Bone" in arm.bones
        assert bpy.context.view_layer.objects.active == ob, "the old active object was not restored"
        try:
            with mode(ob, "EDIT"):
                raise KeyError("inside")
        except KeyError:
            pass
        assert ob.mode == "OBJECT", "an error inside mode() left edit mode on"

        ob.modifiers.new("Subdiv", "SUBSURF").levels = 1
        ob.modifiers.new("Weld", "WELD")
        assert apply_modifier(ob, "Subdiv") == ["Weld"] and len(me.vertices) == 9, len(me.vertices)
        apply_all(ob)
        assert len(ob.modifiers) == 0
        ob.shape_key_add(name="Basis")
        ob.modifiers.new("Subdiv", "SUBSURF")
        try:
            apply_modifier(ob, "Subdiv")
            raise AssertionError("applied a modifier over shape keys")
        except ValueError:
            pass
        return {"vertices_after_subdiv": 9}
    finally:
        for o in made:
            data = o.data
            bpy.data.objects.remove(o)
            if data.users == 0:
                (bpy.data.meshes if isinstance(data, bpy.types.Mesh) else bpy.data.armatures).remove(data)
