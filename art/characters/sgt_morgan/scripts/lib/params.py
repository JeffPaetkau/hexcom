"""The parameter registry (spec 18 §4.3, §4.8.1): the named values that the server's set and get,
snapshot and restore, the variant sweeps and the optimisers all address the same way.

An address is a string, so it travels in JSON, on the command line and in params.json:

  key:<Object>:<KeyBlock>                      a shape key's value (MPFB detail targets are shape keys)
  mod:<Object>:<Modifier>:<property>           a modifier property (`width`, `levels`; dotted for nested)
  gn:<Object>:<Modifier>:<input>               a Geometry Nodes input by socket identifier (`Socket_2`),
                                               or by its interface name when that name is unique
  xf:<Object>:<location|rotation_euler|scale>[:<0|1|2>]   a transform, whole or one axis
  const:<part>:<name>                          a part constant, merged into the part's params on build
  macro:<Object>:<name>                        an MPFB macro slider (gender, age, muscle, weight, height,
                                               proportions, cupsize, firmness, african, asian, caucasian), in
                                               [0, 1]; a write reapplies the macro targets once per object
                                               (MPFB's reapply_macro_details: under 1 ms, ≈ 0.2 s when a
                                               corner target must be loaded), after which a linear target
                                               model must refresh(); the race values are not renormalised

A registered name stands for an address with bounds, a unit and a factor from that unit to Blender's:
register("collar_h", "mod:Boot.L.Collar:Solidify:thickness", lo=4, hi=12, unit="mm", factor=0.001).
Every lookup goes by name when it is used, never through a stored RNA reference, so registered values
survive the server's restore (which re-opens the file) and module reloads.
"""
import contextlib

KINDS = ("key", "mod", "gn", "xf", "const", "macro")
TRANSFORMS = ("location", "rotation_euler", "scale")
MACROS = ("gender", "age", "muscle", "weight", "height", "proportions", "cupsize", "firmness", "african", "asian",
          "caucasian")

# importlib.reload re-runs this module in its old namespace, and the server reloads changed modules
# before a build, so the registry is carried over rather than emptied.
REGISTRY = globals().get("REGISTRY", {})
CONSTANTS = globals().get("CONSTANTS", {})


class Param:
    __slots__ = ("name", "address", "lo", "hi", "unit", "factor")

    def __init__(self, name, address, lo=None, hi=None, unit=None, factor=1.0):
        parse(address)
        self.name, self.address, self.lo, self.hi, self.unit, self.factor = name, address, lo, hi, unit, factor

    def as_dict(self):
        return {s: getattr(self, s) for s in self.__slots__}


def parse(address):
    """('key', ['Body.Mesh', 'Face.Jaw']) and the like; ValueError for a malformed address."""
    kind, sep, rest = address.partition(":")
    n = {"key": 2, "mod": 3, "gn": 3, "const": 2, "macro": 2}.get(kind)
    if not sep or kind not in KINDS:
        raise ValueError(f"bad address {address!r}: expected one of {KINDS} then ':'")
    if kind == "xf":
        args = rest.split(":")
        if len(args) not in (2, 3) or args[1] not in TRANSFORMS or (len(args) == 3 and args[2] not in "012"):
            raise ValueError(f"bad transform address {address!r}: xf:<Object>:<{'|'.join(TRANSFORMS)}>[:0|1|2]")
        return kind, args
    args = rest.split(":", n - 1)
    if len(args) != n or not all(args):
        raise ValueError(f"bad address {address!r}: {kind} takes {n} fields")
    if kind == "macro" and args[1] not in MACROS:
        raise ValueError(f"bad address {address!r}: MPFB's macros are {', '.join(MACROS)}")
    return kind, args


def register(name, address, lo=None, hi=None, unit=None, factor=1.0):
    p = Param(name, address, lo, hi, unit, factor)
    REGISTRY[name] = p
    return p


def unregister(*names):
    for n in names:
        REGISTRY.pop(n, None)


def lookup(name):
    """The registered Param, or an unregistered one for a raw address."""
    if name in REGISTRY:
        return REGISTRY[name]
    try:
        return Param(name, name)
    except ValueError:
        raise KeyError(f"{name!r} is neither a registered parameter nor an address") from None


def constants(part_id):
    return dict(CONSTANTS.get(part_id, {}))


# --------------------------------------------------------------------------- adapters

def _object(name):
    import bpy
    ob = bpy.data.objects.get(name)
    if ob is None:
        raise KeyError(f"no object {name!r}")
    return ob


def _key_block(ob, key):
    keys = ob.data.shape_keys if ob.type in ("MESH", "CURVE", "SURFACE", "LATTICE") else None
    kb = keys.key_blocks.get(key) if keys else None
    if kb is None:
        raise KeyError(f"{ob.name} has no shape key {key!r}")
    return kb


def _modifier(ob, name):
    m = ob.modifiers.get(name)
    if m is None:
        raise KeyError(f"{ob.name} has no modifier {name!r}")
    return m


def _socket(mod, inp):
    if mod.type != "NODES" or mod.node_group is None:
        raise KeyError(f"modifier {mod.name!r} is not a Geometry Nodes modifier with a node group")
    if inp in mod.keys():  # an identifier already
        return inp
    hits = [i.identifier for i in mod.node_group.interface.items_tree
            if i.item_type == "SOCKET" and i.in_out == "INPUT" and i.name == inp]
    if len(hits) != 1:
        raise KeyError(f"{mod.name}: input {inp!r} matches {len(hits)} sockets; use its identifier")
    return hits[0]


def _owner_attr(obj, path):
    *head, attr = path.split(".")
    for h in head:
        obj = getattr(obj, h)
    if not hasattr(obj, attr):
        raise KeyError(f"{obj!r} has no property {attr!r}")
    return obj, attr


def _plain(v):
    if isinstance(v, (bool, int, float, str)):
        return v
    try:
        return [float(x) for x in v]
    except TypeError:
        return v


def _like(cur, v):
    """v coerced to the type of the value it replaces (an int input stays an int)."""
    if isinstance(cur, bool):
        return bool(v)
    if isinstance(cur, int):
        return int(round(v))
    if isinstance(cur, float):
        return float(v)
    return [float(x) for x in v] if isinstance(v, (list, tuple)) else v


def _mpfb():
    """MPFB's human properties and target service, or KeyError when MPFB is not enabled in this session."""
    try:
        from bl_ext.user_default.mpfb.entities.objectproperties import HumanObjectProperties
        from bl_ext.user_default.mpfb.services.targetservice import TargetService
    except ImportError:
        raise KeyError("macro: parameters need MPFB enabled in this session (not --factory-startup)") from None
    return HumanObjectProperties, TargetService


_MACRO_PENDING = []  # objects whose macros changed in this write, reapplied once each at its end
# MPFB deletes a corner target whose weight falls to 0 and reads it from disk again when a slider brings it
# back: 25-35 ms each time a slider crosses a corner (0.5), against 0.3 ms with the target kept. Searches and
# sweeps keep them (keep_macro_targets()) and prune once at the end, so a build's key set never depends on
# the values a search happened to visit.
_MACRO_KEEP = {"on": False, "touched": []}


@contextlib.contextmanager
def keep_macro_targets():
    """Keep MPFB's zero-weight corner targets loaded while macros change; prune them once on the way out."""
    if _MACRO_KEEP["on"]:
        yield
        return
    _MACRO_KEEP.update(on=True, touched=[])
    try:
        yield
    finally:
        _MACRO_KEEP["on"] = False
        for name in _MACRO_KEEP["touched"]:
            try:
                _mpfb()[1].reapply_macro_details(_object(name))
            except KeyError:  # the object went away (a restore)
                pass
        _MACRO_KEEP["touched"] = []


def _get(address):
    kind, a = parse(address)
    if kind == "const":
        if a[1] not in CONSTANTS.get(a[0], {}):
            raise KeyError(f"part {a[0]} has no constant {a[1]!r} set in this session")
        return CONSTANTS[a[0]][a[1]]
    ob = _object(a[0])
    if kind == "macro":
        return float(_mpfb()[0].get_value(a[1], entity_reference=ob))
    if kind == "key":
        return _key_block(ob, a[1]).value
    if kind == "mod":
        return _plain(getattr(*_owner_attr(_modifier(ob, a[1]), a[2])))
    if kind == "gn":
        m = _modifier(ob, a[1])
        return _plain(m[_socket(m, a[2])])
    v = getattr(ob, a[1])
    return float(v[int(a[2])]) if len(a) == 3 else _plain(v)


def _set(address, v):
    kind, a = parse(address)
    if kind == "const":
        CONSTANTS.setdefault(a[0], {})[a[1]] = v
        return
    ob = _object(a[0])
    if kind == "macro":
        _mpfb()[0].set_value(a[1], float(v), entity_reference=ob)
        if ob.name not in _MACRO_PENDING:
            _MACRO_PENDING.append(ob.name)
    elif kind == "key":
        kb = _key_block(ob, a[1])
        kb.slider_min, kb.slider_max = min(kb.slider_min, v), max(kb.slider_max, v)  # else Blender clamps
        kb.value = v
    elif kind == "mod":
        owner, attr = _owner_attr(_modifier(ob, a[1]), a[2])
        setattr(owner, attr, _like(getattr(owner, attr), v))
    elif kind == "gn":
        m = _modifier(ob, a[1])
        ident = _socket(m, a[2])
        m[ident] = _like(m[ident], v)
        ob.update_tag()  # an ID property write does not re-evaluate the modifier by itself
    elif len(a) == 3:
        getattr(ob, a[1])[int(a[2])] = float(v)
    else:
        setattr(ob, a[1], [float(x) for x in v])


def _scale(v, f):
    if f == 1.0 or isinstance(v, (bool, str)):
        return v
    return [x * f for x in v] if isinstance(v, list) else v * f


# --------------------------------------------------------------------------- the API

def read(names=None):
    """{name: value} in registry units; all registered names by default."""
    out = {}
    for n in REGISTRY if names is None else names:
        p = lookup(n)
        out[n] = _scale(_get(p.address), 1.0 / p.factor)
    return out


def write(values, bounds=True):
    """Set {name: value} (registry units) and return the values read back.

    Every name is resolved and checked against its bounds before anything changes, so a bad entry
    leaves the session as it was."""
    plan = []
    for n, v in values.items():
        p = lookup(n)
        if p.address.startswith("const:"):
            plan.append((p, v))
            continue
        _get(p.address)  # resolves the object, modifier or key now
        comps = v if isinstance(v, (list, tuple)) else [v]
        if bounds and any((p.lo is not None and c < p.lo) or (p.hi is not None and c > p.hi) for c in comps):
            raise ValueError(f"{n} = {v} is outside [{p.lo}, {p.hi}]{' ' + p.unit if p.unit else ''}")
        if p.address.startswith("macro:") and not 0.0 <= v * p.factor <= 1.0:
            raise ValueError(f"{n} = {v}: MPFB's macro sliders run from 0 to 1 (outside, it blends no targets)")
        plan.append((p, list(v) if isinstance(v, tuple) else v))
    del _MACRO_PENDING[:]
    try:
        for p, v in plan:
            _set(p.address, _scale(v, p.factor))
    finally:
        for name in _MACRO_PENDING:  # once per object, however many of its macros changed
            _mpfb()[1].reapply_macro_details(_object(name), remove_zero_weight_targets=not _MACRO_KEEP["on"])
            if _MACRO_KEEP["on"] and name not in _MACRO_KEEP["touched"]:
                _MACRO_KEEP["touched"].append(name)
        del _MACRO_PENDING[:]
    return read([p.name for p, _ in plan])


def snapshot(names=None):
    return read(names)


def restore(snap):
    """Put back what snapshot() returned (no bounds check: those values were in the session)."""
    return write(snap, bounds=False)


def selftest():
    import importlib
    import sys
    import bpy
    made = []
    try:
        me = bpy.data.meshes.new("SelftestP.Plane")
        me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
        ob = bpy.data.objects.new("SelftestP.Plane", me)
        bpy.context.scene.collection.objects.link(ob)
        made.append(ob)
        ob.shape_key_add(name="Basis")
        ob.shape_key_add(name="SelftestP.Bulge").data[0].co.z = 1.0
        ob.modifiers.new("Bevel", "BEVEL")
        ng = bpy.data.node_groups.new("SelftestP.GN", "GeometryNodeTree")
        made.append(ng)
        ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        lift = ng.interface.new_socket("Lift", in_out="INPUT", socket_type="NodeSocketFloat")
        count = ng.interface.new_socket("Count", in_out="INPUT", socket_type="NodeSocketInt")
        gi, go = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
        sp, cx = ng.nodes.new("GeometryNodeSetPosition"), ng.nodes.new("ShaderNodeCombineXYZ")
        ng.links.new(gi.outputs[0], sp.inputs["Geometry"])
        ng.links.new(sp.outputs[0], go.inputs[0])
        ng.links.new(gi.outputs["Lift"], cx.inputs["Z"])
        ng.links.new(cx.outputs[0], sp.inputs["Offset"])
        ob.modifiers.new("GN", "NODES").node_group = ng

        register("bulge", "key:SelftestP.Plane:SelftestP.Bulge", lo=-1, hi=1)
        register("bevel_mm", "mod:SelftestP.Plane:Bevel:width", lo=0, hi=50, unit="mm", factor=0.001)
        register("lift", "gn:SelftestP.Plane:GN:Lift", lo=-1, hi=1)
        register("count", f"gn:SelftestP.Plane:GN:{count.identifier}")
        register("z_mm", "xf:SelftestP.Plane:location:2", unit="mm", factor=0.001)
        register("depth", "const:96:lug_depth_mm")
        got = write({"bulge": -0.5, "bevel_mm": 12, "lift": 0.25, "count": 3.0, "z_mm": 40, "depth": 4.5})
        assert got["bulge"] == -0.5, got  # past the default slider range, which would clamp to 0
        assert abs(got["bevel_mm"] - 12) < 1e-6 and abs(ob.modifiers["Bevel"].width - 0.012) < 1e-9
        assert got["count"] == 3 and isinstance(ob.modifiers["GN"][count.identifier], int)
        assert abs(ob.location.z - 0.04) < 1e-9 and constants("96") == {"lug_depth_mm": 4.5}
        dg = bpy.context.evaluated_depsgraph_get()
        z = max(v.co.z for v in ob.evaluated_get(dg).data.vertices)  # the bulge only lowers vertex 0
        assert abs(z - 0.25) < 1e-6, f"the GN input did not re-evaluate: top z {z}"
        assert read(["xf:SelftestP.Plane:scale"]) == {"xf:SelftestP.Plane:scale": [1.0, 1.0, 1.0]}

        snap = snapshot()
        try:
            write({"bulge": 0.1, "lift": 2.0})  # lift is out of bounds: nothing may change
            raise AssertionError("an out-of-bounds value was accepted")
        except ValueError:
            pass
        assert read(["bulge"])["bulge"] == -0.5, "a refused write changed an earlier entry"
        write({"bulge": 0.9, "bevel_mm": 1, "z_mm": 0})
        restore(snap)
        assert read() == snap
        assert parse("macro:Body.Mesh:muscle") == ("macro", ["Body.Mesh", "muscle"])  # live: linmodel's selftest
        for bad in ("xf:X:location:7", "nope:X", "mod:X:Y", "key:", "macro:Body.Mesh:strength"):
            try:
                parse(bad)
                raise AssertionError(f"parsed {bad}")
            except ValueError:
                pass
        try:
            read(["key:SelftestP.Nothing:Basis"])
            raise AssertionError("read a missing object")
        except KeyError:
            pass
        n = len(REGISTRY)
        importlib.reload(sys.modules[__name__])  # the server's reload must keep the registry
        assert len(sys.modules[__name__].REGISTRY) == n
        return {"registered": n, "gn_identifier": count.identifier}
    finally:
        unregister("bulge", "bevel_mm", "lift", "count", "z_mm", "depth")
        CONSTANTS.pop("96", None)
        for d in made:
            (bpy.data.objects if isinstance(d, bpy.types.Object) else bpy.data.node_groups).remove(d)
        if bpy.data.meshes.get("SelftestP.Plane"):
            bpy.data.meshes.remove(bpy.data.meshes["SelftestP.Plane"])
