"""Node-building helpers for the materials library (spec 16 §7.2): no recipes live here.

NodeBuilder wraps one node tree and names and places every node it makes from a counter, so building the
same recipe twice gives the same tree (tree_hash, §7.4 and test T3). Values passed to its helpers may be
constants or output sockets; a socket is linked, a constant is written into the input. Texture sets are
addressed by their manifest id and map kind (`texture("knitted_fleece", "normal_gl")`, spec 18 §5.1), never
by a path, and every image gets its colour space from that kind (§5.5): colour maps sRGB, the rest
Non-Color.
"""
import hashlib
import json
import os

from . import env

MANIFEST = os.path.join(env.ASSETS_DIR, "manifest.json")
RESTORE = "bash scripts/setup_session.sh"   # what restores assets/ from the manifest (CLAUDE.md, spec 18 §4.2)
COLOUR_KINDS = ("color", "diffuse", "basecolor", "albedo")
# The 2nd and 98th percentiles of a normalised 3D Noise Fac at detail 2, roughness 0.5 (Blender 4.5, 65 k
# samples, 2026-10-10; detail 1 gives 0.314-0.688, detail 3 0.345-0.654): the band noise_signed() maps to ±1.
NOISE_BAND = (0.336, 0.665)
NOISE_BANDS = {1: (0.314, 0.688), 2: NOISE_BAND, 3: (0.345, 0.654)}


def cover_threshold(cover, detail=2):
    """The Fac above which a normalised Noise (detail 1-3) covers `cover` of a surface: the Fac is close to
    normal about 0.5 with the 2nd-98th percentile band of NOISE_BANDS, so a spec's "6 % cover" lands on the
    tail it means instead of on a threshold read off the 0-1 range (§9's lesson on noise remapping)."""
    from statistics import NormalDist
    lo, hi = NOISE_BANDS[int(round(detail))]
    sd = (hi - lo) / (2.0 * NormalDist().inv_cdf(0.98))
    return 0.5 + sd * NormalDist().inv_cdf(1.0 - min(max(cover, 1e-4), 1.0 - 1e-4))
# node properties that are layout, not meaning: left out of tree_hash
_SKIP = {"name", "label", "location", "location_absolute", "width", "width_hidden", "height", "select",
         "show_options", "show_preview", "hide", "mute", "show_texture", "color", "use_custom_color", "parent",
         "warning_propagation", "bl_idname", "bl_label", "bl_description", "bl_icon", "bl_static_type",
         "bl_width_default", "bl_width_min", "bl_width_max", "bl_height_default", "bl_height_min",
         "bl_height_max", "type", "dimensions", "is_active_output", "internal_links", "inputs", "outputs",
         "rna_type", "image_user", "color_mapping", "texture_mapping"}


class MissingAsset(FileNotFoundError):
    """A CC0 file the manifest lists is not on disk (lint L5): the message says how to restore it."""


# --------------------------------------------------------------------------- sockets

def sock(node, key, out=False):
    """A node's input (or output) by identifier, name or index; a clear KeyError otherwise."""
    socks = node.outputs if out else node.inputs
    if isinstance(key, int):
        return socks[key]
    for s in socks:
        if s.identifier == key:
            return s
    for s in socks:
        if s.name == key and s.enabled:
            return s
    for s in socks:
        if s.name == key:
            return s
    raise KeyError(f"{node.bl_idname} has no {'output' if out else 'input'} {key!r}: "
                   f"{[s.identifier for s in socks]}")


def is_socket(v):
    return hasattr(v, "is_linked") and hasattr(v, "node")


class NodeBuilder:
    """Deterministic node making on one tree (a material's or a group's)."""

    COLS = 8   # nodes are laid out in rows of eight, in creation order: tidy enough to read in the UI

    def __init__(self, tree):
        self.tree, self.nodes, self.links = tree, tree.nodes, tree.links
        self.n = 0

    # ---- making and wiring
    def node(self, type, name=None, inputs=None, **props):
        nd = self.nodes.new(type)
        tag = type.replace("ShaderNode", "").replace("NodeGroup", "Group")
        nd.name = name or f"{tag}.{self.n:03d}"
        nd.location = ((self.n % self.COLS) * 220.0, -(self.n // self.COLS) * 260.0)
        self.n += 1
        for k, v in props.items():
            setattr(nd, k, v)
        for k, v in (inputs or {}).items():
            self.set(nd, k, v)
        return nd

    def set(self, node, key, value):
        s = sock(node, key)
        if is_socket(value):
            self.links.new(value, s)
        elif value is not None:
            dv = s.default_value
            if hasattr(dv, "__len__") and not isinstance(value, (list, tuple)):
                value = [value] * len(dv)
            elif hasattr(dv, "__len__") and len(value) == 3 and len(dv) == 4:
                value = tuple(value) + (1.0,)
            s.default_value = value
        return s

    def link(self, out, inp):
        self.links.new(out, inp)

    @staticmethod
    def out(node, key=0):
        return sock(node, key, out=True)

    # ---- small helpers that return an output socket
    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self.set(nd, i, v)
        return nd.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        nd = self.node("ShaderNodeVectorMath", operation=op)
        self.set(nd, 0, a)
        if b is not None:
            self.set(nd, 1, b)
        if scale is not None:
            self.set(nd, "Scale", scale)
        return nd.outputs["Value"] if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else nd.outputs["Vector"]

    def mix(self, fac, a, b, kind="RGBA", blend="MIX", clamp=True):
        """Mix node in 4.5: kind RGBA, FLOAT or VECTOR."""
        nd = self.node("ShaderNodeMix", data_type=kind, blend_type=blend, clamp_factor=clamp)
        suffix = {"RGBA": "Color", "FLOAT": "Float", "VECTOR": "Vector"}[kind]
        self.set(nd, "Factor_Float", fac)
        self.set(nd, f"A_{suffix}", a)
        self.set(nd, f"B_{suffix}", b)
        return {"RGBA": nd.outputs[2], "FLOAT": nd.outputs[0], "VECTOR": nd.outputs[1]}[kind]

    def map_range(self, x, a0, a1, b0=0.0, b1=1.0, interp="LINEAR", clamp=True):
        nd = self.node("ShaderNodeMapRange", interpolation_type=interp, clamp=clamp, data_type="FLOAT")
        for k, v in (("Value", x), ("From Min", a0), ("From Max", a1), ("To Min", b0), ("To Max", b1)):
            self.set(nd, k, v)
        return nd.outputs["Result"]

    def smoothstep(self, x, a0, a1):
        return self.map_range(x, a0, a1, 0.0, 1.0, "SMOOTHSTEP")

    def attr(self, name, kind="GEOMETRY", out="Fac"):
        nd = self.node("ShaderNodeAttribute", attribute_type=kind, attribute_name=name)
        return nd.outputs[out]

    def coords(self, out="Object"):
        return self.node("ShaderNodeTexCoord").outputs[out]

    def uv(self, name):
        return self.node("ShaderNodeUVMap", uv_map=name).outputs["UV"]

    def geometry(self, out):
        return self.node("ShaderNodeNewGeometry").outputs[out]

    def separate(self, v):
        nd = self.node("ShaderNodeSeparateXYZ")
        self.set(nd, 0, v)
        return nd.outputs["X"], nd.outputs["Y"], nd.outputs["Z"]

    def combine(self, x, y, z):
        nd = self.node("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            self.set(nd, i, v)
        return nd.outputs[0]

    def noise(self, vector, scale, detail=2.0, roughness=0.5, dims="3D", w=None, out="Fac"):
        nd = self.node("ShaderNodeTexNoise", noise_dimensions=dims, normalize=True,
                       inputs={"Vector": vector, "Scale": scale, "Detail": detail, "Roughness": roughness})
        if w is not None:
            self.set(nd, "W", w)
        return nd.outputs[out]

    def noise_signed(self, vector, scale, detail=2.0, roughness=0.5):
        """A Noise texture remapped to about -1..+1: the normalised Fac of 4.5 keeps to a narrow band about
        0.5 (NOISE_BAND, measured), so an amplitude written in a spec ("±6 % value") means what it says."""
        lo, hi = NOISE_BAND
        return self.map_range(self.noise(vector, scale, detail, roughness), lo, hi, -1.0, 1.0)

    def voronoi(self, vector, scale, feature="F1", randomness=1.0, out="Distance", dims="3D"):
        nd = self.node("ShaderNodeTexVoronoi", feature=feature, voronoi_dimensions=dims,
                       inputs={"Vector": vector, "Scale": scale, "Randomness": randomness})
        return nd.outputs[out]

    def group(self, name, inputs=None):
        import bpy
        ng = bpy.data.node_groups.get(name)
        if ng is None:
            raise KeyError(f"node group {name} is not built (materials.ensure_groups())")
        nd = self.node("ShaderNodeGroup", name=None)
        nd.node_tree = ng
        for k, v in (inputs or {}).items():
            self.set(nd, k, v)
        return nd

    def bump(self, height, normal=None, distance=1.0):
        """A physical bump (§4.0): Height in metres, Distance 1, Strength 1."""
        nd = self.node("ShaderNodeBump", inputs={"Strength": 1.0, "Distance": distance, "Height": height})
        if normal is not None:
            self.set(nd, "Normal", normal)
        return nd.outputs["Normal"]


# --------------------------------------------------------------------------- trees

def new_tree(mat):
    """Empty a material's node tree in place (its users keep the material) and return a builder."""
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return NodeBuilder(mat.node_tree)


def output(nb, shader, displacement=None):
    out = nb.node("ShaderNodeOutputMaterial", name="Material Output", target="ALL")
    nb.link(shader, out.inputs["Surface"])
    if displacement is not None:
        nb.link(displacement, out.inputs["Displacement"])
    return out


PRINCIPLED_ALIASES = {"base": "Base Color", "rough": "Roughness", "metal": "Metallic", "ior": "IOR",
                      "spec": "Specular IOR Level", "normal": "Normal", "sss": "Subsurface Weight",
                      "sss_radius": "Subsurface Radius", "sss_scale": "Subsurface Scale", "sss_ior": "Subsurface IOR",
                      "sss_aniso": "Subsurface Anisotropy", "transmission": "Transmission Weight",
                      "coat": "Coat Weight", "coat_rough": "Coat Roughness", "coat_ior": "Coat IOR",
                      "coat_normal": "Coat Normal", "sheen": "Sheen Weight", "sheen_rough": "Sheen Roughness",
                      "sheen_tint": "Sheen Tint", "aniso": "Anisotropic", "aniso_rot": "Anisotropic Rotation",
                      "tangent": "Tangent", "spec_tint": "Specular Tint", "alpha": "Alpha"}


def principled(nb, method="RANDOM_WALK", distribution="MULTI_GGX", name=None, **values):
    """A Principled BSDF with friendly or real socket names (checked against 4.5: a KeyError names the
    sockets there are). Unset sockets keep Blender's defaults except Sheen, Coat and Subsurface, which start
    at 0 as they do in 4.5."""
    nd = nb.node("ShaderNodeBsdfPrincipled", name=name, subsurface_method=method, distribution=distribution)
    for k, v in values.items():
        nb.set(nd, PRINCIPLED_ALIASES.get(k, k), v)
    return nd


def group_interface(ng, inputs, outputs):
    """Declare a group's sockets: (name, type, default[, min, max]) with type Float, Vector, Color or Shader."""
    ng.interface.clear()
    for in_out, items in (("OUTPUT", outputs), ("INPUT", inputs)):
        for it in items:
            name, kind = it[0], it[1]
            s = ng.interface.new_socket(name, in_out=in_out, socket_type=f"NodeSocket{kind}")
            if len(it) > 2 and it[2] is not None and hasattr(s, "default_value"):
                dv = it[2]
                if kind == "Color" and len(dv) == 3:
                    dv = tuple(dv) + (1.0,)
                s.default_value = dv
            if len(it) > 3 and hasattr(s, "min_value"):
                s.min_value, s.max_value = it[3], it[4]


def group_nodes(nb):
    """The Group Input and Group Output nodes of a group tree (made once, named for tree_hash)."""
    gi = nb.node("NodeGroupInput", name="Group Input")
    go = nb.node("NodeGroupOutput", name="Group Output")
    return gi, go


def _round(v):
    if isinstance(v, float):
        return round(v, 6)
    if isinstance(v, (list, tuple)):
        return [_round(x) for x in v]
    return v


def _value(v):
    if hasattr(v, "__len__") and not isinstance(v, str):
        try:
            return _round([float(x) for x in v])
        except (TypeError, ValueError):
            return str(list(v))
    if isinstance(v, (int, float, bool, str)) or v is None:
        return _round(v)
    return getattr(v, "name", str(v))


def tree_hash(tree):
    """sha256 (16 hex) of a node tree's meaning: nodes by name with their type, properties and unlinked
    input values, the links, a group's interface and a colour ramp's stops; layout is left out."""
    rec = {"nodes": [], "links": [], "interface": []}
    for nd in sorted(tree.nodes, key=lambda x: x.name):
        props = {}
        for p in nd.bl_rna.properties:
            if p.identifier in _SKIP or p.is_readonly or p.type == "COLLECTION":
                continue
            try:
                v = getattr(nd, p.identifier)
            except AttributeError:
                continue
            # a pointer is its target's name (an image, a group, an object); never its address
            props[p.identifier] = getattr(v, "name", None) if p.type == "POINTER" else _value(v)
        if getattr(nd, "image", None) is not None:
            props["image"] = [nd.image.name, nd.image.colorspace_settings.name]
        if getattr(nd, "node_tree", None) is not None:
            props["node_tree"] = nd.node_tree.name
        if nd.bl_idname == "ShaderNodeValToRGB":
            props["ramp"] = [nd.color_ramp.interpolation] + [[_round(e.position), _value(e.color)]
                                                             for e in nd.color_ramp.elements]
        ins = [[s.identifier, _value(s.default_value)] for s in nd.inputs
               if not s.is_linked and hasattr(s, "default_value")]
        rec["nodes"].append([nd.name, nd.bl_idname, props, ins])
    for lk in tree.links:
        rec["links"].append([lk.from_node.name, lk.from_socket.identifier, lk.to_node.name, lk.to_socket.identifier])
    rec["links"].sort()
    if hasattr(tree, "interface"):
        for it in tree.interface.items_tree:
            rec["interface"].append([it.name, getattr(it, "in_out", ""), getattr(it, "socket_type", ""),
                                     _value(getattr(it, "default_value", None))])
    return hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- textures by manifest id

_manifest = None


def manifest():
    global _manifest
    if _manifest is None:
        with open(MANIFEST, encoding="utf-8") as f:
            _manifest = {a["id"]: a for a in json.load(f)["assets"]}
    return _manifest


def asset_path(asset, kind):
    """The file of a texture set's map kind (color, normal_gl, roughness, ao, displacement, ...)."""
    entry = manifest().get(asset)
    if entry is None:
        raise KeyError(f"{asset} is not in assets/manifest.json")
    for fname, info in entry.get("maps", {}).items():
        if info.get("kind") == kind:
            return os.path.join(env.ASSETS_DIR, entry["folder"], fname)
    raise KeyError(f"{asset} has no {kind!r} map: {sorted(i.get('kind') for i in entry.get('maps', {}).values())}")


def texture(asset, kind):
    """The image of one map, loaded once and named Lib.Img.<asset>.<kind>, in its kind's colour space."""
    import bpy
    path = asset_path(asset, kind)
    name = f"Lib.Img.{asset}.{kind}"
    img = bpy.data.images.get(name)
    if img is not None and os.path.normcase(bpy.path.abspath(img.filepath)) == os.path.normcase(path):
        return img
    if not os.path.isfile(path):
        raise MissingAsset(f"{os.path.relpath(path, env.PROJECT_DIR)} is missing (lint L5); restore it with {RESTORE}")
    if img is not None:
        bpy.data.images.remove(img)
    img = bpy.data.images.load(path, check_existing=False)
    img.name = name
    img.colorspace_settings.name = "sRGB" if kind in COLOUR_KINDS else "Non-Color"
    img["lib_asset"], img["lib_kind"] = asset, kind
    return img


def image_node(nb, img, vector, interpolation=None, box=False):
    """An Image Texture node: Linear for colour, Cubic for normals and data (§5.5), Closest never; `box`
    projects it on the three object planes with spec 16's blend 0.2 (§5.1, hard parts without UV.Real)."""
    interp = interpolation or ("Linear" if img.colorspace_settings.name == "sRGB" else "Cubic")
    nd = nb.node("ShaderNodeTexImage", interpolation=interp, extension="REPEAT")
    if box:
        nd.projection, nd.projection_blend = "BOX", 0.2
    nd.image = img
    nb.set(nd, "Vector", vector)
    return nd


def selftest():
    import bpy
    m = bpy.data.materials.new("Lib.Mat.SelfTest")
    try:
        hashes = []
        for _ in range(2):
            nb = new_tree(m)
            p = principled(nb, base=(0.2, 0.3, 0.4), rough=0.5, sheen=0.04)
            nb.set(p, "Normal", nb.bump(nb.math("MULTIPLY", nb.noise(nb.coords(), 100.0), 1e-4)))
            output(nb, p.outputs[0])
            hashes.append(tree_hash(m.node_tree))
        assert hashes[0] == hashes[1], hashes
        try:
            principled(nb, nonsense=1.0)
            raise AssertionError("an unknown socket was accepted")
        except KeyError:
            pass
        img = texture("knitted_fleece", "normal_gl")
        assert img.colorspace_settings.name == "Non-Color"
        assert texture("knitted_fleece", "color").colorspace_settings.name == "sRGB"
        return {"tree_hash": hashes[0], "image": img.name}
    finally:
        bpy.data.materials.remove(m)
