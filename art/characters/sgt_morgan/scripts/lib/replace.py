"""Idempotent re-runs: a part deletes and recreates only its own data-blocks (spec 18 §4.7 rules 1–2).

part_scope(PART) removes the part's objects (everything in its collection and everything named under
its prefixes), then its other data-blocks by prefix, then purges orphans recursively, so a second run
starts from the state the first run started from. new_object() refuses names outside the part's
prefixes, and the scope refuses on exit any object in the part's collection that slipped past it (an
operator's "Cube"). body_layer() strips the part's own shape keys, vertex groups and attributes from
the shared Body.Mesh before it re-adds them; MPFB's own are lower case and so never match a prefix.
"""
import contextlib

from . import naming

BODY = "Body.Mesh"
# The ID collections a part may fill; everything here is found by prefix and removed on a re-run.
ID_TYPES = ("objects", "meshes", "curves", "hair_curves", "pointclouds", "volumes", "lattices",
            "armatures", "cameras", "lights", "materials", "images", "textures", "node_groups",
            "actions", "particles", "collections")
# Data-blocks Blender makes by itself while a part builds; not strays.
IGNORED = {("images", "Render Result"), ("images", "Viewer Node")}

_scope = None  # the active Scope, for the module-level new_object()


def _data():
    import bpy
    return bpy.data


def local_ids():
    """{id type: set of names} of every local (not linked) data-block of ID_TYPES."""
    d = _data()
    return {t: {i.name for i in getattr(d, t) if i.library is None} for t in ID_TYPES if hasattr(d, t)}


def local(kind, name):
    """The local data-block of that name; a linked one from a part cache may share the name."""
    ids = getattr(_data(), kind)
    hit = ids.get(name)
    if hit is None or hit.library is None:
        return hit
    return next((i for i in ids if i.name == name and i.library is None), None)


def parts_collection(scene=None):
    """The scene's `Parts` collection, made on first use."""
    import bpy
    scene = scene or bpy.context.scene
    coll = local("collections", naming.PARTS) or bpy.data.collections.new(naming.PARTS)
    if not any(c == coll for c in scene.collection.children):
        scene.collection.children.link(coll)
    return coll


def ensure_collection(part):
    """The part's own collection, made under `Parts` if it does not exist."""
    import bpy
    coll = local("collections", part.collection)
    if coll is None:
        coll = bpy.data.collections.new(part.collection)
    if coll.users == 0:  # linked nowhere yet
        parts_collection().children.link(coll)
    return coll


def owned_ids(part):
    """Local data-blocks named under the part's prefixes (its collection itself excluded)."""
    d = _data()
    out = []
    for t in ID_TYPES:
        for i in getattr(d, t, ()):
            if i.library is None and naming.owned(i.name, part.prefixes) and i.name != part.collection:
                out.append(i)
    return out


def remove(part):
    """Delete the part's objects, child collections and prefixed data; keep its (emptied) collection.

    Returns the number of data-blocks removed. Linked (library) data is never touched."""
    import bpy
    coll = local("collections", part.collection)
    doomed = set(owned_ids(part))
    if coll is not None:
        doomed |= {o for o in coll.all_objects if o.library is None}
        doomed |= {c for c in coll.children_recursive if c.library is None}
    if doomed:
        bpy.data.batch_remove(list(doomed))
    return len(doomed)


def purge():
    import bpy
    return bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def _layer_collection(lc, coll):
    if lc.collection == coll:
        return lc
    for ch in lc.children:
        hit = _layer_collection(ch, coll)
        if hit is not None:
            return hit
    return None


def relink_foreign(part, before):
    """Map data a part cache carried from other parts back onto the session's own copies.

    A cache holds the data-blocks its objects point at (a rig behind an Armature modifier); appended
    into a session that already has them, they arrive as `Morgan.Rig.001`. Only project-named data
    owned by another part is remapped (such names are unique by convention); anything else is left
    and reported. Returns (remapped, kept) name lists."""
    import bpy
    d = bpy.data
    remapped, kept, dupes = [], [], []
    for t in ID_TYPES:
        old = before.get(t, set())
        for i in list(getattr(d, t, ())):
            if i.library is not None or i.name in old or naming.owned(i.name, part.prefixes):
                continue
            base = i.name[:-4] if naming.DUPLICATE.search(i.name) else None
            target = local(t, base) if base and base in old else None
            if target is not None and naming.valid(base) and target != i:
                i.user_remap(target)
                dupes.append(i)
                remapped.append(f"{t}:{i.name}")
            elif i.name != part.collection:
                kept.append(f"{t}:{i.name}")
    if dupes:
        d.batch_remove(dupes)
    return remapped, kept


class Scope:
    """What part_scope yields: the part, its collection, and the guarded constructors."""

    def __init__(self, part, coll):
        self.part, self.coll = part, coll
        self.strays = []

    def new_object(self, name, data=None, coll=None):
        """Make an object (and name its fresh data the same) in the part's collection or a child of it."""
        import bpy
        naming.check(name)
        if not naming.owned(name, self.part.prefixes):
            raise ValueError(f"{name!r} is outside part {self.part.id}'s prefixes {self.part.prefixes}")
        if local("objects", name) is not None:
            raise ValueError(f"object {name!r} exists already: part_scope should have removed it")
        ob = bpy.data.objects.new(name, data)
        if ob.name != name:
            raise ValueError(f"Blender named the object {ob.name!r}, not {name!r}")
        if data is not None and data.users == 1 and data.name != name:  # fresh data only, not shared
            data.name = name
            if data.name != name:
                raise ValueError(f"data name {name!r} is taken (got {data.name!r})")
        (coll or self.coll).objects.link(ob)
        return ob

    def clear(self, prefix):
        """Remove the part's objects named `prefix` or `prefix.*`, and their data once unused: how a stage
        replaces its own objects when --stage re-runs it on the cached part. Returns the count."""
        import bpy
        if not naming.owned(prefix, self.part.prefixes):
            raise ValueError(f"{prefix!r} is outside part {self.part.id}'s prefixes {self.part.prefixes}")
        obs = [o for o in bpy.data.objects
               if o.library is None and (o.name == prefix or o.name.startswith(prefix + "."))]
        datas = {o.data for o in obs if o.data is not None}
        bpy.data.batch_remove(obs)
        bpy.data.batch_remove([d for d in datas if d.users == 0])
        return len(obs)

    def collection(self, name):
        """A child collection of the part's collection (named under its prefixes)."""
        import bpy
        naming.check(name)
        if not naming.owned(name, self.part.prefixes):
            raise ValueError(f"collection {name!r} is outside part {self.part.id}'s prefixes")
        c = bpy.data.collections.new(name)
        if c.name != name:
            raise ValueError(f"collection {name!r} exists already")
        self.coll.children.link(c)
        return c


def new_object(name, data=None, coll=None):
    """Scope.new_object on the active part_scope (the form of spec 18 §4.3)."""
    if _scope is None:
        raise RuntimeError("new_object() outside replace.part_scope()")
    return _scope.new_object(name, data, coll)


@contextlib.contextmanager
def part_scope(part):
    """Remove the part's data, purge orphans, and yield a Scope over its emptied collection.

    New objects from operators land in the part's collection (it is made the active layer
    collection for the duration). On a clean exit every object and collection in it must be named
    under the part's prefixes, and other new data-blocks outside them are reported as strays."""
    import bpy
    global _scope
    remove(part)
    purge()
    coll = ensure_collection(part)
    vl = bpy.context.view_layer
    prev_lc = vl.active_layer_collection
    lc = _layer_collection(vl.layer_collection, coll)
    if lc is not None:
        vl.active_layer_collection = lc
    before = local_ids()
    scope, outer = Scope(part, coll), _scope
    _scope = scope
    try:
        yield scope
        bad = sorted(o.name for o in coll.all_objects
                     if o.library is None and not (naming.valid(o.name) and naming.owned(o.name, part.prefixes)))
        bad += sorted(c.name for c in coll.children_recursive
                      if c.library is None and not (naming.valid(c.name) and naming.owned(c.name, part.prefixes)))
        if bad:
            raise ValueError(f"part {part.id} left objects or collections outside its prefixes "
                             f"{part.prefixes} or badly named: {bad}")
        after = local_ids()
        for t, names in after.items():
            for n in sorted(names - before.get(t, set())):
                if (t, n) not in IGNORED and not naming.owned(n, part.prefixes):
                    scope.strays.append(f"{t}:{n}")
        if scope.strays:
            from . import cli
            msg = f"data-blocks outside the prefixes {part.prefixes}: {scope.strays}"
            if cli.active() is not None:
                cli.active().warn(msg)
            else:
                print(f"[replace] part {part.id}: {msg}", flush=True)
    finally:
        _scope = outer
        try:
            vl.active_layer_collection = prev_lc
        except (ReferenceError, TypeError, RuntimeError):
            pass


def body_layer(part, body=BODY):
    """Remove the part's own shape keys, vertex groups and attributes from the body before re-adding.

    Returns the body object. A missing body is a missing hard dependency (exit 3)."""
    import bpy
    ob = bpy.data.objects.get(body)
    if ob is None or ob.type != "MESH":
        from . import cli
        raise cli.MissingDependency(f"{body} (the shared body mesh) is not in this session")
    keys = ob.data.shape_keys
    if keys is not None:
        for kb in [k for k in keys.key_blocks if naming.owned(k.name, part.prefixes)]:
            ob.shape_key_remove(kb)
    for vg in [g for g in ob.vertex_groups if naming.owned(g.name, part.prefixes)]:
        ob.vertex_groups.remove(vg)
    for n in [a.name for a in ob.data.attributes if naming.owned(a.name, part.prefixes)]:
        ob.data.attributes.remove(ob.data.attributes[n])
    return ob


def _mpfb_human():
    """An MPFB human named Body.Mesh if MPFB is installed here, else None."""
    import bpy
    mod = "bl_ext.user_default.mpfb"
    try:
        if mod not in bpy.context.preferences.addons:
            bpy.ops.preferences.addon_enable(module=mod)
        from bl_ext.user_default.mpfb.services.humanservice import HumanService
    except Exception:  # not installed here (a factory-startup session or a bare box)
        return None
    ob = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                   feet_on_ground=True, scale=0.1)
    ob.name = BODY
    return ob


def selftest():
    import bpy
    from .cli import Part
    part = Part(id="98", name="replace_selftest", prefixes=("SelftestR.",), script="scripts/lib/replace.py")
    other = bpy.data.objects.new("Other.Thing", None)
    bpy.context.scene.collection.objects.link(other)
    body = None
    try:
        def build():
            with part_scope(part) as scope:
                me = bpy.data.meshes.new("tmp")
                me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
                ob = scope.new_object("SelftestR.L.Tri", me)
                me.materials.append(bpy.data.materials.new("SelftestR.Mat"))
                scope.new_object("SelftestR.R.Empty", None, scope.collection("SelftestR.Sub"))
                for bad in ("Elsewhere.Tri", "selftestR.x"):
                    try:
                        scope.new_object(bad)
                        raise AssertionError(f"new_object accepted {bad}")
                    except ValueError:
                        pass
                bpy.ops.mesh.primitive_cube_add()  # an operator's object, renamed as the rules ask
                bpy.context.active_object.name = "SelftestR.Cube"
                bpy.context.active_object.data.name = "SelftestR.Cube"
                return ob
        build()
        first = sorted(o.name for o in bpy.data.collections[part.collection].all_objects)
        n_mesh = len(bpy.data.meshes)
        build()
        second = sorted(o.name for o in bpy.data.collections[part.collection].all_objects)
        assert first == second == ["SelftestR.Cube", "SelftestR.L.Tri", "SelftestR.R.Empty"], (first, second)
        assert len(bpy.data.meshes) == n_mesh and "SelftestR.Mat" in bpy.data.materials
        assert not any(naming.DUPLICATE.search(i.name) for t in ("objects", "meshes", "materials")
                       for i in getattr(bpy.data, t) if i.name.startswith("SelftestR."))
        assert bpy.data.objects.get("Other.Thing") is not None, "another part's object was removed"
        try:
            with part_scope(part):
                bpy.ops.mesh.primitive_cube_add()  # left as "Cube": the scope must refuse it
            raise AssertionError("part_scope accepted an object named Cube")
        except ValueError:
            pass
        try:
            new_object("SelftestR.Outside")
            raise AssertionError("new_object worked outside a scope")
        except RuntimeError:
            pass

        body = _mpfb_human()
        used_mpfb = body is not None
        if body is None:  # a stand-in with MPFB-like names, so the test still means something
            me = bpy.data.meshes.new(BODY)
            me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
            body = bpy.data.objects.new(BODY, me)
            bpy.context.scene.collection.objects.link(body)
            body.shape_key_add(name="Basis")
            body.shape_key_add(name="$md-universal-male-young")
            body.vertex_groups.new(name="body")
        mine = Part(id="97", name="layer_selftest", prefixes=("SelftestL.",), script="scripts/lib/replace.py")
        keys0 = [k.name for k in body.data.shape_keys.key_blocks] if body.data.shape_keys else []
        groups0 = [g.name for g in body.vertex_groups]
        attrs0 = sorted(a.name for a in body.data.attributes)
        for _ in range(2):  # twice: the second pass must find and replace the first pass's layer
            body_layer(mine)
            if body.data.shape_keys is None:
                body.shape_key_add(name="Basis")
            body.shape_key_add(name="SelftestL.Bulge")
            body.vertex_groups.new(name="SelftestL.Zone")
            body.data.attributes.new("SelftestL.Wear", "FLOAT", "POINT")
        assert [k.name for k in body.data.shape_keys.key_blocks].count("SelftestL.Bulge") == 1
        body_layer(mine)
        assert [k.name for k in body.data.shape_keys.key_blocks] == (keys0 or ["Basis"])
        assert [g.name for g in body.vertex_groups] == groups0
        assert sorted(a.name for a in body.data.attributes) == attrs0
        return {"objects": second, "body": "mpfb" if used_mpfb else "stand-in", "body_keys": len(keys0),
                "body_groups": len(groups0)}
    finally:
        remove(part)
        coll = bpy.data.collections.get(part.collection)
        if coll is not None:
            bpy.data.collections.remove(coll)
        doomed = [bpy.data.objects.get("Other.Thing")] + [o for o in bpy.data.objects
                                                          if o.name == "Cube" or o.name.startswith("Cube.")]
        if body is not None:
            doomed += [body] + list(body.children_recursive)
        bpy.data.batch_remove([d for d in doomed if d is not None])
        purge()
