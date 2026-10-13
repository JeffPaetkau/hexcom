"""Builders of the shared node groups of spec 16 §4 (`MG.*`).

Built so far, as far as the skin, nail and sock recipes need them: MG.Skin.Core and MG.Skin.Micro (§4.1),
MG.Tile.AntiRepeat (§4.8), MG.Knit.Stitch (§4.7) and MG.Weather.Grime (§4.3). Every other group of §4 is in
PLANNED and asking for it raises NotBuilt with its section, so a part learns at once what is missing.

Rules from §4.0: lengths at a group's interface are millimetres (one Math node converts inside), colours
linear, factors 0-1; every group that adds relief outputs a height in metres, never a normal; every group
has an LOD input (0 for renders; bakes are not built yet, so it is carried, not used). A group records the
hash of the library's source it was built from (`lib_source`), and ensure_groups() rebuilds it when that
changes, so a fix reaches every material on its next build.
"""
import hashlib
import math
import os

from . import mat_catalogue as C
from . import mat_core as K

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = ("mat_catalogue.py", "mat_core.py", "mat_groups.py")


class NotBuilt(NotImplementedError):
    """A recipe, group or function of spec 16 that the library does not have yet."""


PLANNED = {
    "MG.Weather.Dust": "§4.2", "MG.Mask.EdgeBevel": "§4.4", "MG.Weather.Edge": "§4.4", "MG.Weather.Chips": "§4.4",
    "MG.GN.Touch": "§4.4", "MG.GN.Crest": "§4.5", "MG.Fabric.Crest": "§4.5", "MG.Fabric.StressWhite": "§4.5",
    "MG.Polish": "§4.5", "MG.Camo.Blotch4": "§4.6", "MG.Weave.Plain": "§4.7", "MG.Weave.Ripstop": "§4.7",
    "MG.Weave.Basket": "§4.7", "MG.Weave.Herringbone": "§4.7", "MG.Weave.Grosgrain": "§4.7", "MG.Braid": "§4.7",
    "MG.Anodise": "§4.8", "MG.Paint.OrangePeel": "§4.8", "MG.Decal": "§4.9", "MG.GN.Fuzz": "§6",
}


def source_hash(*files):
    """sha256 (16 hex) of library sources with LF line endings, so Git's checkout setting cannot change it."""
    h = hashlib.sha256()
    for f in files or SOURCES:
        with open(os.path.join(HERE, f), "rb") as fh:
            h.update(fh.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]


# --------------------------------------------------------------------------- §4.1 skin

def build_skin_core(ng):
    """One Principled BSDF with §3.3.1's constants; only what varies by region is an input. Coat Normal is
    an addition to §4.1's list: unlinked, Blender's coat ignores the bump, and under random-walk scattering
    the oil film's sheen is where fine relief shows at all."""
    sk = C.SKIN_FOOT   # the core constants are shared by Skin.Head, Skin.Body and Skin.Foot (§4.1)
    K.group_interface(ng, inputs=[
        ("Base Color", "Color", C.hex_to_linear(sk["albedo_hex"])), ("Roughness", "Float", 0.45, 0.0, 1.0),
        ("SSS Scale", "Float", 0.003, 0.0, 0.1), ("SSS Radius", "Vector", (1.0, 0.2, 0.1)),
        ("Coat Weight", "Float", 0.0, 0.0, 1.0), ("Coat Roughness", "Float", 0.25, 0.0, 1.0),
        ("Normal", "Vector", (0.0, 0.0, 0.0)), ("Coat Normal", "Vector", (0.0, 0.0, 0.0)), ("LOD", "Float", 0.0)],
        outputs=[("BSDF", "Shader")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    i = lambda k: K.sock(gi, k, out=True)   # noqa: E731
    p = K.principled(nb, method="RANDOM_WALK_SKIN", name="Principled", base=i("Base Color"), rough=i("Roughness"),
                     sss=1.0, sss_radius=i("SSS Radius"), sss_scale=i("SSS Scale"), sss_ior=sk["sss_ior"],
                     sss_aniso=sk["sss_aniso"], ior=sk["ior"], spec=sk["spec"], coat=i("Coat Weight"),
                     coat_rough=i("Coat Roughness"), coat_ior=1.5, normal=i("Normal"), coat_normal=i("Coat Normal"),
                     sheen=sk["sheen"], sheen_rough=sk["sheen_rough"], sheen_tint=(1.0, 1.0, 1.0))
    nb.link(p.outputs[0], K.sock(go, "BSDF"))


def build_skin_micro(ng):
    """§4.1's five switchable layers as one height (metres): skin lines (Voronoi distance to edge, two cell
    sizes), follicle pits (Voronoi F1 under a threshold), friction ridges (Wave bands with a noise
    distortion), pores (smooth F1) and an orange-peel noise. A layer with depth 0 costs nothing: Cycles
    folds the product with zero away. Per-layer heights are outputs too, so a material can blend two cell
    sizes by a mask without warping the cells (a varying Voronoi scale would).

    The skin lines (2026-10-12, critic round 3 m5: one crisp, dark-outlined Voronoi crackle on every skin
    surface, read as crazed porcelain): a raw Voronoi edge network is a tiling of convex cells with V-grooves
    of one depth, and real skin's furrows are none of that. So the lines' domain is stretched along the
    tension (Langer) direction (§4.1's 1.6, `Line Stretch`, `Langer Direction` in the Vector's space: cells
    elongated along it, so the furrows run mostly that way) and warped by a noise of about two cells
    (`Line Warp`, a share of the cell: the edges bend); each groove is soft (a Gaussian section whose full
    width at half depth is `Line Width mm`, shallow-sloped, in place of round 3's hard smoothstep V), and its
    depth varies along the line (`Line Breakup`: from 1 - breakup to 1, so some edges fade out and the
    network reads as furrows, not cells). The fine network gets the same treatment at its own cell, its
    groove the same share of its cell."""
    K.group_interface(ng, inputs=[
        ("Vector", "Vector", (0.0, 0.0, 0.0)),
        ("Line Cell mm", "Float", 0.5), ("Line Width mm", "Float", 0.04), ("Line Depth mm", "Float", 0.0),
        ("Line Mask", "Float", 1.0, 0.0, 1.0),
        ("Langer Direction", "Vector", (1.0, 0.0, 0.0)), ("Line Stretch", "Float", 1.6, 1.0, 4.0),
        ("Line Warp", "Float", 0.35, 0.0, 1.0), ("Line Breakup", "Float", 0.5, 0.0, 1.0),
        ("Fine Cell mm", "Float", 0.15), ("Fine Depth mm", "Float", 0.0),
        ("Pit Cell mm", "Float", 0.45), ("Pit Threshold", "Float", 0.09), ("Pit Depth mm", "Float", 0.0),
        ("Pit Mask", "Float", 1.0, 0.0, 1.0),
        ("Ridge Pitch mm", "Float", 0.45), ("Ridge Depth mm", "Float", 0.0), ("Ridge Distortion", "Float", 3.0),
        ("Ridge Distortion mm", "Float", 5.0), ("Ridge Mask", "Float", 1.0, 0.0, 1.0),
        ("Pore Cell mm", "Float", 1.1), ("Pore Radius", "Float", 0.3), ("Pore Depth mm", "Float", 0.0),
        ("Pore Mask", "Float", 1.0, 0.0, 1.0),
        ("Peel mm", "Float", 1.1), ("Peel Depth mm", "Float", 0.0), ("LOD", "Float", 0.0)],
        outputs=[("Height", "Float"), ("Lines", "Float"), ("Pits", "Float"), ("Ridges", "Float")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    i = lambda k: K.sock(gi, k, out=True)   # noqa: E731
    v = i("Vector")
    m = 0.001

    def per_m(mm):   # cells per metre for a feature size in mm
        return nb.math("DIVIDE", 1000.0, mm)

    # the lines' domain: squashed along the Langer direction by 1 / stretch (cells that much longer that way)
    ldir = nb.vmath("NORMALIZE", i("Langer Direction"))
    squash = nb.math("SUBTRACT", 1.0, nb.math("DIVIDE", 1.0, nb.math("MAXIMUM", i("Line Stretch"), 1.0)))
    vl = nb.vmath("SUBTRACT", v, nb.vmath("SCALE", ldir, scale=nb.math("MULTIPLY", nb.vmath("DOT_PRODUCT", v, ldir),
                                                                         squash)))
    # the share of the cell a groove's half width takes (Line Width mm is the primary network's full width at
    # half depth; the fine network's groove is the same share of its own cell)
    share = nb.math("DIVIDE", nb.math("MULTIPLY", i("Line Width mm"), 0.5), i("Line Cell mm"))

    def lines(cell, depth):
        cell_m = nb.math("MULTIPLY", cell, m)
        # the warp: a detail-1 noise's colour about 0.5 (each channel within about +-0.19, 2nd-98th
        # percentile), scaled so the offsets reach +-`Line Warp` cells, varying over about two cells
        wc = nb.noise(vl, nb.math("DIVIDE", 1.0, nb.math("MULTIPLY", cell_m, 2.2)), detail=1.0, out="Color")
        off = nb.vmath("SCALE", nb.vmath("SUBTRACT", wc, (0.5, 0.5, 0.5)),
                       scale=nb.math("DIVIDE", nb.math("MULTIPLY", i("Line Warp"), cell_m), 0.19))
        vw = nb.vmath("ADD", vl, off)
        d = nb.voronoi(vw, per_m(cell), feature="DISTANCE_TO_EDGE", randomness=1.0)
        # a soft groove: exp(-ln2 (d / half width)^2), half depth at the half width; distance to the edge
        # runs from both sides, so the full width at half depth is Line Width mm
        x = nb.math("DIVIDE", d, nb.math("MAXIMUM", share, 1e-4))
        groove = nb.math("EXPONENT", nb.math("MULTIPLY", nb.math("MULTIPLY", x, x), -math.log(2.0)))
        # the break-up: each line's depth varies along it over about 1.5 cells (a detail-1 noise's Fac keeps
        # to 0.314-0.688; mat_core.NOISE_BAND's note), from 1 - Line Breakup to 1
        br = nb.noise(vw, nb.math("DIVIDE", 1.0, nb.math("MULTIPLY", cell_m, 1.5)), detail=1.0)
        keep = nb.map_range(br, 0.36, 0.64, nb.math("SUBTRACT", 1.0, i("Line Breakup")), 1.0, "SMOOTHSTEP")
        return nb.math("MULTIPLY", nb.math("MULTIPLY", groove, keep), nb.math("MULTIPLY", depth, -m))

    ln = nb.math("MULTIPLY", nb.math("ADD", lines(i("Line Cell mm"), i("Line Depth mm")),
                                     lines(i("Fine Cell mm"), i("Fine Depth mm"))), i("Line Mask"))
    pit_d = nb.voronoi(v, per_m(i("Pit Cell mm")), feature="F1", randomness=1.0)
    pit = nb.math("SUBTRACT", 1.0, nb.smoothstep(pit_d, 0.0, i("Pit Threshold")))
    pits = nb.math("MULTIPLY", nb.math("MULTIPLY", pit, i("Pit Mask")), nb.math("MULTIPLY", i("Pit Depth mm"), -m))
    # Wave BANDS on the diagonal: phase = 10 (x + y + z) with p = vector x scale. Any one axis leaves the
    # faces perpendicular to it without ridges; the diagonal changes at sqrt(2) per unit across every face
    # whose normal lies along an axis, so one period there is 2 pi / (10 sqrt(2) scale) metres.
    pitch_m = nb.math("MULTIPLY", i("Ridge Pitch mm"), m)
    scale = nb.math("DIVIDE", 2.0 * math.pi / (10.0 * math.sqrt(2.0)), pitch_m)
    dscale = nb.math("DIVIDE", 1.0, nb.math("MULTIPLY", scale, nb.math("MULTIPLY", i("Ridge Distortion mm"), m)))
    wave = nb.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL", wave_profile="SIN",
                   inputs={"Vector": v, "Scale": scale, "Distortion": i("Ridge Distortion"), "Detail": 2.0,
                           "Detail Scale": dscale, "Detail Roughness": 0.5})
    ridges = nb.math("MULTIPLY", nb.math("SUBTRACT", wave.outputs["Fac"], 0.5),
                     nb.math("MULTIPLY", nb.math("MULTIPLY", i("Ridge Depth mm"), m), i("Ridge Mask")))
    pore_d = nb.voronoi(v, per_m(i("Pore Cell mm")), feature="SMOOTH_F1", randomness=1.0)
    pore = nb.math("SUBTRACT", 1.0, nb.smoothstep(pore_d, 0.0, i("Pore Radius")))
    pores = nb.math("MULTIPLY", nb.math("MULTIPLY", pore, i("Pore Mask")), nb.math("MULTIPLY", i("Pore Depth mm"), -m))
    peel = nb.math("MULTIPLY", nb.noise_signed(v, per_m(i("Peel mm")), detail=1.0),
                   nb.math("MULTIPLY", i("Peel Depth mm"), 0.5 * m))
    total = nb.math("ADD", nb.math("ADD", ln, pits), nb.math("ADD", nb.math("ADD", ridges, pores), peel))
    for k, s in (("Height", total), ("Lines", ln), ("Pits", pits), ("Ridges", ridges)):
        nb.link(s, K.sock(go, k))


# --------------------------------------------------------------------------- §4.8 tiling

def build_antirepeat(ng):
    """§4.8's coordinates: sample A at Vector / Tile, sample B rotated 90 degrees and offset (0.37, 0.61)
    tile, and the blend between them (a noise at three tiles, smoothstepped 0.3-0.7). An image cannot be a
    shader group's input in 4.5, so the two image nodes sit in the material (`antirepeat` in mat_fabric)
    and read these outputs; a normal map's sample B is turned back by -90 degrees there. `Turn` (an
    addition) is 1 for §4.8's turn and 0 for directional maps (knits, weaves, herringbone): turning a knit
    by 90 degrees lays a second knit across the first, and where the two blend neither shows."""
    K.group_interface(ng, inputs=[("Vector", "Vector", (0.0, 0.0, 0.0)), ("Tile mm", "Float", 100.0),
                                  ("Turn", "Float", 1.0, 0.0, 1.0), ("LOD", "Float", 0.0)],
                      outputs=[("Vector A", "Vector"), ("Vector B", "Vector"), ("Blend", "Float")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    v, tile = K.sock(gi, "Vector", out=True), K.sock(gi, "Tile mm", out=True)
    tile_m = nb.math("MULTIPLY", tile, 0.001)
    a = nb.vmath("SCALE", v, scale=nb.math("DIVIDE", 1.0, tile_m))
    x, y, _ = nb.separate(a)
    turned = nb.mix(K.sock(gi, "Turn", out=True), a, nb.combine(nb.math("MULTIPLY", y, -1.0), x, 0.0), kind="VECTOR")
    b = nb.vmath("ADD", turned, (0.37, 0.61, 0.0))
    n = nb.noise(v, nb.math("DIVIDE", 1.0, nb.math("MULTIPLY", tile_m, 3.0)), detail=2.0)
    blend = nb.smoothstep(n, 0.3, 0.7)
    nb.link(a, K.sock(go, "Vector A"))
    nb.link(b, K.sock(go, "Vector B"))
    nb.link(blend, K.sock(go, "Blend"))


# --------------------------------------------------------------------------- §4.7 knits

def build_knit_stitch(ng):
    """§4.7: a Brick texture with brick width = wale, row height = course, offset 0.5, mortar 0.15 x wale;
    the stitch stands proud of the mortar by Height. Vector in metres (UV.Real)."""
    K.group_interface(ng, inputs=[("Vector", "Vector", (0.0, 0.0, 0.0)), ("Wale mm", "Float", 1.6),
                                  ("Course mm", "Float", 1.2), ("Mortar", "Float", 0.15, 0.0, 0.5),
                                  ("Height mm", "Float", 0.04), ("LOD", "Float", 0.0)],
                      outputs=[("Height", "Float")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    i = lambda k: K.sock(gi, k, out=True)   # noqa: E731
    wale_m = nb.math("MULTIPLY", i("Wale mm"), 0.001)
    brick = nb.node("ShaderNodeTexBrick", offset=0.5, offset_frequency=2, squash=1.0, squash_frequency=2,
                    inputs={"Vector": i("Vector"), "Scale": 1.0, "Brick Width": wale_m,
                            "Row Height": nb.math("MULTIPLY", i("Course mm"), 0.001),
                            "Mortar Size": nb.math("MULTIPLY", i("Mortar"), wale_m), "Mortar Smooth": 0.5,
                            "Bias": 0.0})
    proud = nb.math("SUBTRACT", 1.0, brick.outputs["Fac"])   # Fac is 1 in the mortar
    nb.link(nb.math("MULTIPLY", proud, nb.math("MULTIPLY", i("Height mm"), 0.001)), K.sock(go, "Height"))


# --------------------------------------------------------------------------- §4.3 grime

def build_grime(ng):
    """§4.3 steps 1-7. `Mask Only` (an addition) is set to 1 by a material that always drives the group
    from a mask: the geometric branch (an AO node of 8 rays among it) then folds away at compile time
    instead of being evaluated and discarded at every shading point."""
    K.group_interface(ng, inputs=[
        ("Base Color", "Color", (0.5, 0.5, 0.5)), ("Base Roughness", "Float", 0.5, 0.0, 1.0),
        ("Amount", "Float", 0.0, 0.0, 1.0), ("Oil", "Float", 0.0, 0.0, 1.0),
        ("Band Low mm", "Float", -10.0), ("Band High mm", "Float", 0.0), ("Bottom", "Float", 0.0, 0.0, 1.0),
        ("Cavity Weight", "Float", 0.6), ("Streak Amount", "Float", 0.0), ("Streak Length mm", "Float", 55.0),
        ("Streak Width mm", "Float", 4.0), ("Dry", "Color", C.hex_to_linear("#3a342c")),
        ("Oily", "Color", C.hex_to_linear("#1a1612")), ("Mask", "Float", -1.0), ("Mask Only", "Float", 0.0, 0.0, 1.0),
        ("LOD", "Float", 0.0)],
        outputs=[("Color", "Color"), ("Roughness", "Float"), ("Grime", "Float")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    i = lambda k: K.sock(gi, k, out=True)   # noqa: E731
    _, _, z = nb.separate(nb.geometry("True Normal"))
    down = nb.map_range(z, 0.2, -0.9, 0.0, 1.0, "SMOOTHSTEP")
    ao = nb.node("ShaderNodeAmbientOcclusion", samples=8, inside=False, only_local=False,
                 inputs={"Distance": 0.004})
    cav = nb.map_range(nb.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.4, 0.9)
    _, _, pz = nb.separate(nb.geometry("Position"))
    band = nb.map_range(nb.math("MULTIPLY", pz, 1000.0), i("Band High mm"), i("Band Low mm"), 0.0, 1.0, "SMOOTHSTEP")
    obj = nb.coords("Object")
    mp = nb.node("ShaderNodeMapping", vector_type="POINT", inputs={"Vector": obj})
    w, ln = nb.math("DIVIDE", 1000.0, i("Streak Width mm")), nb.math("DIVIDE", 1000.0, i("Streak Length mm"))
    nb.set(mp, "Scale", nb.combine(w, w, ln))
    streak = nb.map_range(nb.noise(mp.outputs[0], 1.0, detail=2.0), 0.55, 0.75)
    streak = nb.math("MULTIPLY", nb.math("MULTIPLY", streak, nb.math("SUBTRACT", 1.0, nb.math("ABSOLUTE", z))),
                     i("Streak Amount"))
    worst = nb.math("MAXIMUM", nb.math("MAXIMUM", nb.math("MULTIPLY", cav, i("Cavity Weight")),
                                       nb.math("MULTIPLY", down, 0.5)),
                    nb.math("MAXIMUM", band, i("Bottom")))
    patch = nb.map_range(nb.noise(obj, 1000.0 / 80.0, detail=2.0), 0.0, 1.0, 0.6, 1.0)
    g_geo = nb.math("ADD", nb.math("MULTIPLY", nb.math("MULTIPLY", i("Amount"), worst), patch), streak, clamp=True)
    g_mask = nb.math("MULTIPLY", i("Mask"), i("Amount"), clamp=True)
    use_mask = nb.math("MAXIMUM", i("Mask Only"), nb.math("GREATER_THAN", i("Mask"), -0.5))
    g = nb.mix(use_mask, g_geo, g_mask, kind="FLOAT")
    grime = nb.mix(i("Oil"), i("Dry"), i("Oily"))
    darker = nb.mix(g, i("Base Color"), nb.mix(0.55, i("Base Color"), (0.0, 0.0, 0.0)))   # Base x mix(1, 0.45, g)
    col = nb.mix(nb.math("MULTIPLY", g, 0.3), darker, grime)
    rough = nb.math("ADD", i("Base Roughness"), nb.math("MULTIPLY", g, nb.mix(i("Oil"), 0.10, -0.08, kind="FLOAT")))
    nb.link(col, K.sock(go, "Color"))
    nb.link(rough, K.sock(go, "Roughness"))
    nb.link(g, K.sock(go, "Grime"))


GROUPS = {
    "MG.Skin.Core": build_skin_core,
    "MG.Skin.Micro": build_skin_micro,
    "MG.Tile.AntiRepeat": build_antirepeat,
    "MG.Knit.Stitch": build_knit_stitch,
    "MG.Weather.Grime": build_grime,
}


def build(name, force=False):
    """Build (or rebuild in place) one group; returns the node tree."""
    import bpy
    if name in PLANNED:
        raise NotBuilt(f"{name} (spec 16 {PLANNED[name]}) is not built yet")
    if name not in GROUPS:
        raise KeyError(f"no node group {name!r} in spec 16 §4")
    src = source_hash()
    ng = bpy.data.node_groups.get(name)
    if ng is not None and ng.library is None and not force and ng.get("lib_source") == src:
        return ng
    if ng is None or ng.library is not None:
        ng = bpy.data.node_groups.new(name, "ShaderNodeTree")
    ng.nodes.clear()
    GROUPS[name](ng)
    ng["lib_version"], ng["lib_source"] = C.LIB_VERSION, src
    ng["recipe_hash"] = K.tree_hash(ng)
    ng.use_fake_user = False
    return ng


def build_all(force=False):
    return {n: build(n, force) for n in GROUPS}


# the sockets each group must expose (§8.1 T4): (inputs, outputs)
SOCKETS = {
    "MG.Skin.Core": ({"Base Color", "Roughness", "SSS Scale", "SSS Radius", "Coat Weight", "Coat Roughness", "Normal",
                      "Coat Normal", "LOD"}, {"BSDF"}),
    "MG.Skin.Micro": ({"Vector", "Line Cell mm", "Line Width mm", "Line Depth mm", "Line Mask", "Langer Direction",
                       "Line Stretch", "Line Warp", "Line Breakup", "Fine Cell mm",
                       "Fine Depth mm", "Pit Cell mm", "Pit Threshold", "Pit Depth mm", "Pit Mask", "Ridge Pitch mm",
                       "Ridge Depth mm", "Ridge Distortion", "Ridge Distortion mm", "Ridge Mask", "Pore Cell mm",
                       "Pore Radius", "Pore Depth mm", "Pore Mask", "Peel mm", "Peel Depth mm", "LOD"},
                      {"Height", "Lines", "Pits", "Ridges"}),
    "MG.Tile.AntiRepeat": ({"Vector", "Tile mm", "Turn", "LOD"}, {"Vector A", "Vector B", "Blend"}),
    "MG.Knit.Stitch": ({"Vector", "Wale mm", "Course mm", "Mortar", "Height mm", "LOD"}, {"Height"}),
    "MG.Weather.Grime": ({"Base Color", "Base Roughness", "Amount", "Oil", "Band Low mm", "Band High mm", "Bottom",
                          "Cavity Weight", "Streak Amount", "Streak Length mm", "Streak Width mm", "Dry", "Oily",
                          "Mask", "Mask Only", "LOD"}, {"Color", "Roughness", "Grime"}),
}


def selftest():
    """T4: every built group builds twice to the same tree and exposes its sockets; a planned one refuses.
    Built into scratch trees, never the live ones: rebuilding a live group's interface would drop the links
    of every material in the session that uses it."""
    import bpy
    out = {}
    for name in GROUPS:
        hashes = []
        for _ in range(2):
            ng = bpy.data.node_groups.new(f"Lib.Test.{name}", "ShaderNodeTree")
            try:
                GROUPS[name](ng)
                hashes.append(K.tree_hash(ng))
                ins = {i.name for i in ng.interface.items_tree if getattr(i, "in_out", "") == "INPUT"}
                outs = {i.name for i in ng.interface.items_tree if getattr(i, "in_out", "") == "OUTPUT"}
            finally:
                bpy.data.node_groups.remove(ng)
        assert hashes[0] == hashes[1], name
        assert (ins, outs) == SOCKETS[name], (name, ins ^ SOCKETS[name][0], outs ^ SOCKETS[name][1])
        out[name] = hashes[0]
    # the skin lines (2026-10-12): §4.1's stretch along the Langer direction by default, two networks each
    # warped and broken up by noises, soft grooves (an exponent) rather than a smoothstep V
    ng = bpy.data.node_groups.new("Lib.Test.MicroLines", "ShaderNodeTree")
    try:
        build_skin_micro(ng)
        items = {i.name: i for i in ng.interface.items_tree if getattr(i, "in_out", "") == "INPUT"}
        assert abs(items["Line Stretch"].default_value - 1.6) < 1e-6, items["Line Stretch"].default_value
        assert tuple(items["Langer Direction"].default_value) == (1.0, 0.0, 0.0)
        vor = [n for n in ng.nodes if n.bl_idname == "ShaderNodeTexVoronoi" and n.feature == "DISTANCE_TO_EDGE"]
        assert len(vor) == 2 and all(abs(n.inputs["Randomness"].default_value - 1.0) < 1e-6 for n in vor), len(vor)
        noises = [n for n in ng.nodes if n.bl_idname == "ShaderNodeTexNoise"]
        ops = {n.operation for n in ng.nodes if n.bl_idname in ("ShaderNodeMath", "ShaderNodeVectorMath")}
        assert len(noises) >= 5 and {"EXPONENT", "DOT_PRODUCT", "NORMALIZE"} <= ops, (len(noises), ops)
        out["micro_lines"] = {"voronoi_edges": len(vor), "noises": len(noises)}
    finally:
        bpy.data.node_groups.remove(ng)
    try:
        build("MG.Weather.Dust")
        raise AssertionError("a planned group was built")
    except NotBuilt:
        pass
    return out
