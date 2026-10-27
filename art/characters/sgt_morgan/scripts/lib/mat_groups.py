"""Builders of the shared node groups of spec 16 §4 (`MG.*`).

Built so far, as far as the skin, nail, sock and boot recipes need them: MG.Skin.Core and MG.Skin.Micro
(§4.1), MG.Tile.AntiRepeat (§4.8), MG.Knit.Stitch, MG.Weave.Basket, MG.Weave.Herringbone and MG.Braid (§4.7),
MG.Weather.Grime (§4.3), MG.Weather.Dust (§4.2), MG.Mask.EdgeBevel and MG.Weather.Edge (§4.4) and MG.Polish
(§4.5). Every other group of §4 is in PLANNED and asking for it raises NotBuilt with its section, so a part
learns at once what is missing. The material-side wiring that every family shares lives here too:
antirepeat() (the two image samples of MG.Tile.AntiRepeat), weather() (grime then dust, §4.0's order, from
a recipe's wear preset), dust_zone(), object_prop() and edge_mask().

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
    "MG.Weather.Chips": "§4.4", "MG.GN.Touch": "§4.4", "MG.GN.Crest": "§4.5", "MG.Fabric.Crest": "§4.5",
    "MG.Fabric.StressWhite": "§4.5", "MG.Camo.Blotch4": "§4.6", "MG.Weave.Plain": "§4.7", "MG.Weave.Ripstop": "§4.7",
    "MG.Weave.Grosgrain": "§4.7", "MG.Anodise": "§4.8", "MG.Paint.OrangePeel": "§4.8", "MG.Decal": "§4.9",
    "MG.GN.Fuzz": "§6",
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
    distortion, or, where the mesh gives a ridge field, its level lines: 2026-10-13), pores (smooth F1) and an
    orange-peel noise. A layer with depth 0 costs nothing: Cycles
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
        ("Ridge Field mm", "Float", 0.0), ("Ridge Field Weight", "Float", 0.0, 0.0, 1.0),
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
    # 2026-10-13 (the foot trial's whole-foot pass; its critics read the diagonal bands as corduroy over the pads
    # and the ball): where the mesh gives a ridge field (`Ridge Field mm`, a phase whose level lines the ridges
    # follow: whorls and loops on the pulps, arcs on the ball; `Ridge Field Weight` 1), the ridges are
    # sin(2 pi (field + wobble) / pitch), the wobble the bands' own distortion (`Ridge Distortion` radians of phase
    # over features of `Ridge Distortion mm`); with the weight at its default 0 the bands are unchanged
    wob = nb.math("MULTIPLY", nb.noise_signed(v, nb.math("DIVIDE", 1.0, nb.math("MULTIPLY", i("Ridge Distortion mm"), m)),
                                              detail=2.0),
                  nb.math("DIVIDE", nb.math("MULTIPLY", i("Ridge Distortion"), i("Ridge Pitch mm")), 2.0 * math.pi))
    phase = nb.math("DIVIDE", nb.math("MULTIPLY", nb.math("ADD", i("Ridge Field mm"), wob), 2.0 * math.pi),
                    i("Ridge Pitch mm"))
    pattern = nb.mix(i("Ridge Field Weight"), nb.math("SUBTRACT", wave.outputs["Fac"], 0.5),
                     nb.math("MULTIPLY", nb.math("SINE", phase), 0.5), kind="FLOAT")
    ridges = nb.math("MULTIPLY", pattern,
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


# --------------------------------------------------------------------------- §4.2 dust (2026-10-27)

DUST_THIN, DUST_THICK = "#9a8d85", "#d2c5b5"   # D12, C25: one hangar, one dust


def build_dust(ng):
    """§4.2 steps 1-9: up-facing (the true normal, so weave and grain never speckle it) x shelter (AO) x
    (1 - 0.6 edge) x a large noise x amount x side, thin film #9a8d85 to crust #d2c5b5 by thickness c².
    Additions, as built: `Zone` (a part's dust-zone weight, §4.10's tables, multiplied in like `Side`);
    `Drift` replaces §4.2's `Tile mm`: SurfaceImperfections015's opacity is sampled by the material through
    MG.Tile.AntiRepeat (on UV.Real, or by box projection on hard parts: an image cannot be a group input)
    and passed in, -1 = none (N = N1); `Dust Roughness` (0.88; the boot leather's 0.78, §3.3.5); `Open` and
    `Shelter`, step 4's 0.7 and 0.6 (Geo = Up x (Open + Shelter x Occ) x (1 - 0.6 Edge)), so a preset can
    send the dust into creases and seams and off the open faces (boot.toe, 2026-10-27)."""
    K.group_interface(ng, inputs=[
        ("Base Color", "Color", (0.5, 0.5, 0.5)), ("Base Roughness", "Float", 0.5, 0.0, 1.0),
        ("Base Specular", "Float", 0.5, 0.0, 1.0), ("Amount", "Float", 0.0, 0.0, 2.0),
        ("Up Low", "Float", 0.25), ("Up High", "Float", 0.85), ("Up Power", "Float", 2.0),
        ("AO Distance mm", "Float", 15.0), ("Open", "Float", 0.7, 0.0, 2.0), ("Shelter", "Float", 0.6, 0.0, 4.0),
        ("Noise mm", "Float", 300.0), ("Side", "Float", 1.0, 0.0, 2.0),
        ("Edge", "Float", 0.0, 0.0, 1.0), ("Zone", "Float", 1.0, 0.0, 1.0), ("Local Up", "Float", 0.0, 0.0, 1.0),
        ("Thin", "Color", C.hex_to_linear(DUST_THIN)), ("Thick", "Color", C.hex_to_linear(DUST_THICK)),
        ("Dust Roughness", "Float", 0.88, 0.0, 1.0), ("Drift", "Float", -1.0), ("Mask", "Float", -1.0),
        ("LOD", "Float", 0.0)],
        outputs=[("Color", "Color"), ("Roughness", "Float"), ("Specular", "Float"), ("Coverage", "Float"),
                 ("Height", "Float"), ("Bump Damp", "Float")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    i = lambda k: K.sock(gi, k, out=True)   # noqa: E731
    tn = nb.geometry("True Normal")
    _, _, z = nb.separate(tn)
    # step 1's object-up term (spec 15's rifle): the object's +Z in world space
    oz = nb.node("ShaderNodeVectorTransform", vector_type="VECTOR", convert_from="OBJECT", convert_to="WORLD",
                 inputs={"Vector": (0.0, 0.0, 1.0)}).outputs[0]
    zo = nb.vmath("DOT_PRODUCT", tn, nb.vmath("NORMALIZE", oz))
    z = nb.mix(i("Local Up"), z, zo, kind="FLOAT")
    up = nb.math("POWER", nb.map_range(z, i("Up Low"), i("Up High"), 0.0, 1.0, "SMOOTHSTEP"), i("Up Power"))
    ao = nb.node("ShaderNodeAmbientOcclusion", samples=8, inside=False, only_local=False,
                 inputs={"Distance": nb.math("MULTIPLY", i("AO Distance mm"), 0.001)})
    occ = nb.math("SUBTRACT", 1.0, ao.outputs["AO"])
    geo = nb.math("MULTIPLY", nb.math("MULTIPLY", up, nb.math("MULTIPLY_ADD", occ, i("Shelter"), i("Open"))),
                  nb.math("MULTIPLY_ADD", i("Edge"), -0.6, 1.0))
    obj = nb.coords("Object")
    # N1: a detail-3 noise's Fac keeps to 0.345-0.654 (mat_core.NOISE_BANDS), so §4.2's 0.35-0.65 is its range
    n1 = nb.map_range(nb.noise(obj, nb.math("DIVIDE", 1000.0, i("Noise mm")), detail=3.0, roughness=0.55), 0.35, 0.65)
    use_drift = nb.math("GREATER_THAN", i("Drift"), -0.5)
    n = nb.mix(use_drift, n1, nb.math("ADD", nb.math("MULTIPLY", n1, 0.6), nb.math("MULTIPLY", i("Drift"), 0.4)),
               kind="FLOAT")
    use_mask = nb.math("GREATER_THAN", i("Mask"), -0.5)
    where = nb.mix(use_mask, geo, i("Mask"), kind="FLOAT")
    c = nb.math("MULTIPLY", nb.math("MULTIPLY", where, n), nb.math("MULTIPLY", i("Amount"), i("Side")))
    c = nb.math("MULTIPLY", c, i("Zone"), clamp=True)
    t = nb.math("MULTIPLY", c, c)
    dust = nb.mix(t, i("Thin"), i("Thick"))
    nb.link(nb.mix(c, i("Base Color"), dust), K.sock(go, "Color"))
    nb.link(nb.mix(c, i("Base Roughness"), i("Dust Roughness"), kind="FLOAT"), K.sock(go, "Roughness"))
    nb.link(nb.math("MULTIPLY", i("Base Specular"), nb.math("MULTIPLY_ADD", c, -0.5, 1.0)), K.sock(go, "Specular"))
    nb.link(c, K.sock(go, "Coverage"))
    grit = nb.voronoi(obj, 1000.0 / 0.05, feature="F1", randomness=1.0)
    nb.link(nb.math("MULTIPLY", nb.math("MULTIPLY", c, grit), 0.01 * 0.001), K.sock(go, "Height"))
    nb.link(nb.math("MULTIPLY_ADD", c, -0.7, 1.0), K.sock(go, "Bump Damp"))


# --------------------------------------------------------------------------- §4.4 edge wear

def _noise_factor(nb, noise_mm, amount, lo=0.3):
    """§4.4 step 4: Map Range(Noise at noise_mm, 0.3-1.0) x amount + (1 - amount), with the noise's measured
    band mapped onto 0.3-1.0 (mat_core.NOISE_BAND)."""
    lo_b, hi_b = K.NOISE_BAND
    n = nb.map_range(nb.noise(nb.coords("Object"), nb.math("DIVIDE", 1000.0, noise_mm), detail=2.0), lo_b, hi_b,
                     lo, 1.0)
    return nb.math("ADD", nb.math("MULTIPLY", n, amount), nb.math("SUBTRACT", 1.0, amount))


def build_edge_bevel(ng):
    """§4.4 MG.Mask.EdgeBevel (spec 15's Wear.EdgeBevel): the Bevel node's virtually rounded normal against
    the surface's own, d = 1 - dot, smoothstepped over [0, Width], broken by a noise, times Zone. As built
    the comparison is with the interpolated (unbumped) normal, not §4.4's true normal: on a smooth-shaded
    mesh the true normal is each facet's, and it differs from the bevel's on every facet of a curved face,
    which drew faint wear across the faces of the test objects; at a real edge the two agree."""
    K.group_interface(ng, inputs=[("Radius mm", "Float", 0.8), ("Width", "Float", 0.08, 0.0, 1.0),
                                  ("Noise mm", "Float", 0.6), ("Noise Amount", "Float", 0.5, 0.0, 1.0),
                                  ("Zone", "Float", 1.0, 0.0, 1.0), ("LOD", "Float", 0.0)],
                      outputs=[("Edge", "Float")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    i = lambda k: K.sock(gi, k, out=True)   # noqa: E731
    bev = nb.node("ShaderNodeBevel", samples=4, inputs={"Radius": nb.math("MULTIPLY", i("Radius mm"), 0.001)})
    d = nb.math("SUBTRACT", 1.0, nb.vmath("DOT_PRODUCT", bev.outputs["Normal"], nb.geometry("Normal")))
    e = nb.map_range(d, 0.0, i("Width"), 0.0, 1.0, "SMOOTHSTEP")
    e = nb.math("MULTIPLY", e, _noise_factor(nb, i("Noise mm"), i("Noise Amount")))
    nb.link(nb.math("MULTIPLY", e, i("Zone"), clamp=True), K.sock(go, "Edge"))


def build_weather_edge(ng):
    """§4.4 MG.Weather.Edge: the worn surface over the base by Edge x Amount (gunmetal to bare steel,
    hardcoat to bare aluminium, black polymer lightened and roughened, leather polished)."""
    K.group_interface(ng, inputs=[
        ("Base Color", "Color", (0.5, 0.5, 0.5)), ("Base Roughness", "Float", 0.5, 0.0, 1.0),
        ("Base Metallic", "Float", 0.0, 0.0, 1.0), ("Base Coat", "Float", 0.0, 0.0, 1.0),
        ("Worn Color", "Color", (0.56, 0.57, 0.58)), ("Worn Roughness", "Float", 0.25, 0.0, 1.0),
        ("Worn Metallic", "Float", 1.0, 0.0, 1.0), ("Worn Coat", "Float", 0.0, 0.0, 1.0),
        ("Edge", "Float", 0.0, 0.0, 1.0), ("Amount", "Float", 1.0, 0.0, 2.0), ("LOD", "Float", 0.0)],
        outputs=[("Color", "Color"), ("Roughness", "Float"), ("Metallic", "Float"), ("Coat", "Float"),
                 ("Wear", "Float")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    i = lambda k: K.sock(gi, k, out=True)   # noqa: E731
    w = nb.math("MULTIPLY", i("Edge"), i("Amount"), clamp=True)
    nb.link(nb.mix(w, i("Base Color"), i("Worn Color")), K.sock(go, "Color"))
    for k in ("Roughness", "Metallic", "Coat"):
        nb.link(nb.mix(w, i(f"Base {k}"), i(f"Worn {k}"), kind="FLOAT"), K.sock(go, k))
    nb.link(w, K.sock(go, "Wear"))


# --------------------------------------------------------------------------- §4.5 polish

def build_polish(ng):
    """§4.5 MG.Polish: a plain mix by Polish x Map Range(Noise 4 mm, 0.3-1.0). Inputs beyond §4.5's list:
    `Base Color` (the colour the shift starts from), `Shift` (how far the colour goes toward `Color Shift`:
    the glove's dye wearing to (0.045, 0.040, 0.037); 0 leaves the colour) and `Noise mm`; output `Mask`, the
    polish actually applied (the material scales its coat roughness or scuffs by it)."""
    K.group_interface(ng, inputs=[
        ("Polish", "Float", 0.0, 0.0, 1.0), ("Base Color", "Color", (0.5, 0.5, 0.5)),
        ("Base Roughness", "Float", 0.5, 0.0, 1.0), ("Polished Roughness", "Float", 0.36, 0.0, 1.0),
        ("Coat", "Float", 0.0, 0.0, 1.0), ("Color Shift", "Color", (0.045, 0.040, 0.037)),
        ("Shift", "Float", 0.0, 0.0, 1.0), ("Noise mm", "Float", 4.0), ("LOD", "Float", 0.0)],
        outputs=[("Roughness", "Float"), ("Coat", "Float"), ("Color", "Color"), ("Mask", "Float")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    i = lambda k: K.sock(gi, k, out=True)   # noqa: E731
    p = nb.math("MULTIPLY", i("Polish"), _noise_factor(nb, i("Noise mm"), 1.0), clamp=True)
    nb.link(nb.mix(p, i("Base Roughness"), i("Polished Roughness"), kind="FLOAT"), K.sock(go, "Roughness"))
    nb.link(nb.math("MULTIPLY", i("Coat"), p), K.sock(go, "Coat"))
    nb.link(nb.mix(nb.math("MULTIPLY", p, i("Shift")), i("Base Color"), i("Color Shift")), K.sock(go, "Color"))
    nb.link(p, K.sock(go, "Mask"))


# --------------------------------------------------------------------------- §4.7 weaves and braid

def _wave_scale(nb, pitch_mm):
    """Blender's BANDS phase is 20 x the coordinate (x scale), so one period of `pitch_mm` takes scale
    2 pi / (20 pitch) with the vector in metres."""
    return nb.math("DIVIDE", 2.0 * math.pi / 20.0, nb.math("MULTIPLY", pitch_mm, 0.001))


def _wave(nb, vector, scale, axis, distortion):
    nd = nb.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction=axis, wave_profile="SIN",
                 inputs={"Vector": vector, "Scale": scale, "Distortion": distortion, "Detail": 2.0,
                         "Detail Scale": 1.0, "Detail Roughness": 0.5})
    return nd.outputs["Fac"]


def build_basket(ng):
    """§4.7 MG.Weave.Basket (Cordura): two orthogonal Wave bands at the yarn pitch, Distortion 0.4,
    multiplied and mapped to the crown height. As built the product is of the signed waves (2 Fac - 1), so
    crossings alternate high and low as a plain weave's warp and weft floats do; the product of the 0-1
    waves would be an egg crate of equal bumps. Vector on UV.Real (metres): x warp, y weft."""
    K.group_interface(ng, inputs=[("Vector", "Vector", (0.0, 0.0, 0.0)), ("Pitch U mm", "Float", 0.61),
                                  ("Pitch V mm", "Float", 0.61), ("Crown mm", "Float", 0.04),
                                  ("Distortion", "Float", 0.4), ("LOD", "Float", 0.0)],
                      outputs=[("Height", "Float")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    i = lambda k: K.sock(gi, k, out=True)   # noqa: E731
    su = nb.math("MULTIPLY_ADD", _wave(nb, i("Vector"), _wave_scale(nb, i("Pitch U mm")), "X", i("Distortion")), 2.0, -1.0)
    sv = nb.math("MULTIPLY_ADD", _wave(nb, i("Vector"), _wave_scale(nb, i("Pitch V mm")), "Y", i("Distortion")), 2.0, -1.0)
    h = nb.math("MULTIPLY", nb.math("MULTIPLY_ADD", nb.math("MULTIPLY", su, sv), 0.5, 0.5),
                nb.math("MULTIPLY", i("Crown mm"), 0.001))
    nb.link(h, K.sock(go, "Height"))


def build_herringbone(ng):
    """§4.7 MG.Weave.Herringbone (webbing), on a strap's UV.Real (x along the strap, y across, metres):
    s = sign(frac(y / P) - 0.5) with P the herringbone period across; twill bands along x + s y at the twill
    pitch (Distortion 2, Detail 2), so the lines reverse every half period; the rib (the reversal lines as
    shallow grooves, P / 2 apart) and the twill share the relief by `Twill Share` (§3.3.4's "twill 1.2 mm at
    30 %")."""
    K.group_interface(ng, inputs=[("Vector", "Vector", (0.0, 0.0, 0.0)), ("Period mm", "Float", 2.5),
                                  ("Twill mm", "Float", 1.2), ("Twill Share", "Float", 0.3, 0.0, 1.0),
                                  ("Distortion", "Float", 2.0), ("Height mm", "Float", 0.05), ("LOD", "Float", 0.0)],
                      outputs=[("Height", "Float")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    i = lambda k: K.sock(gi, k, out=True)   # noqa: E731
    x, y, _ = nb.separate(i("Vector"))
    p_m = nb.math("MULTIPLY", i("Period mm"), 0.001)
    q = nb.math("DIVIDE", y, p_m)
    s = nb.math("SIGN", nb.math("SUBTRACT", nb.math("FRACT", q), 0.5))
    t = nb.math("ADD", x, nb.math("MULTIPLY", s, y))
    twill = _wave(nb, nb.combine(t, y, 0.0), _wave_scale(nb, i("Twill mm")), "X", i("Distortion"))
    rib = nb.math("MULTIPLY_ADD", nb.math("COSINE", nb.math("MULTIPLY", q, 4.0 * math.pi)), -0.5, 0.5)
    share = i("Twill Share")
    h = nb.math("ADD", nb.math("MULTIPLY", rib, nb.math("SUBTRACT", 1.0, share)), nb.math("MULTIPLY", twill, share))
    nb.link(nb.math("MULTIPLY", h, nb.math("MULTIPLY", i("Height mm"), 0.001)), K.sock(go, "Height"))


def build_braid(ng):
    """§4.7 MG.Braid (laces, shock cord): u = arc length / repeat, v = turns around x strands around;
    height = max(tri(u + v), tri(u - v))^1.6 x height, tri a 0-1-0 triangle wave of period 1. The vector is
    a sweep's UV.Real (lib/sweep.py: x along, y round the perimeter, both metres), so the turns are y over
    `Circumference mm` (pi x the lace's diameter). `Groove` (0 in the grooves, 1 on the crowns) is the
    material's darkening term (x 0.8 in the groove, §4.7)."""
    K.group_interface(ng, inputs=[("Vector", "Vector", (0.0, 0.0, 0.0)), ("Repeat mm", "Float", 0.7),
                                  ("Around", "Float", 3.0), ("Circumference mm", "Float", 12.566),
                                  ("Height mm", "Float", 0.15), ("LOD", "Float", 0.0)],
                      outputs=[("Height", "Float"), ("Groove", "Float")])
    nb = K.NodeBuilder(ng)
    gi, go = K.group_nodes(nb)
    i = lambda k: K.sock(gi, k, out=True)   # noqa: E731
    x, y, _ = nb.separate(i("Vector"))
    u = nb.math("DIVIDE", x, nb.math("MULTIPLY", i("Repeat mm"), 0.001))
    v = nb.math("MULTIPLY", nb.math("DIVIDE", y, nb.math("MULTIPLY", i("Circumference mm"), 0.001)), i("Around"))

    def tri(w):
        return nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", w), 0.5)), 2.0))

    crown = nb.math("POWER", nb.math("MAXIMUM", tri(nb.math("ADD", u, v)), tri(nb.math("SUBTRACT", u, v))), 1.6)
    nb.link(nb.math("MULTIPLY", crown, nb.math("MULTIPLY", i("Height mm"), 0.001)), K.sock(go, "Height"))
    nb.link(crown, K.sock(go, "Groove"))


GROUPS = {
    "MG.Skin.Core": build_skin_core,
    "MG.Skin.Micro": build_skin_micro,
    "MG.Tile.AntiRepeat": build_antirepeat,
    "MG.Knit.Stitch": build_knit_stitch,
    "MG.Weather.Grime": build_grime,
    "MG.Weather.Dust": build_dust,
    "MG.Mask.EdgeBevel": build_edge_bevel,
    "MG.Weather.Edge": build_weather_edge,
    "MG.Polish": build_polish,
    "MG.Weave.Basket": build_basket,
    "MG.Weave.Herringbone": build_herringbone,
    "MG.Braid": build_braid,
}


# --------------------------------------------------------------------------- material-side wiring

def antirepeat(nb, asset, kind, vector, tile_mm, box=False, swap=False):
    """One map of a texture set sampled twice through MG.Tile.AntiRepeat and blended (§4.8). Colour and data
    maps return the blended colour; a normal map (normal_gl) returns a tangent-space colour for a Normal Map
    node, with sample B's XY turned back by -90 degrees and the blend renormalised. A directional set
    (TILE_PERIODS "directional") is offset, never turned. `box` projects both samples on the object's three
    planes (hard parts; never a normal map, which has no tangent frame there); `swap` samples the image at
    (y, x), and swaps a normal map's XY to match, for a set whose image axes are crossed with the UV's
    (a strap's u runs along it, the herringbone's image x across it)."""
    if box and kind == "normal_gl":
        raise ValueError(f"{asset}: a box-projected normal map has no tangent frame; use its displacement (§4.0)")
    turn = 0.0 if C.TILE_PERIODS.get(asset, {}).get("directional") else 1.0
    if swap:
        x, y, z = nb.separate(vector)
        vector = nb.combine(y, x, z)
    g = nb.group("MG.Tile.AntiRepeat", {"Vector": vector, "Tile mm": tile_mm, "Turn": turn})
    img = K.texture(asset, kind)
    a = K.image_node(nb, img, K.sock(g, "Vector A", out=True), box=box).outputs["Color"]
    b = K.image_node(nb, img, K.sock(g, "Vector B", out=True), box=box).outputs["Color"]
    blend = K.sock(g, "Blend", out=True)
    if kind != "normal_gl":
        return nb.mix(blend, a, b)

    def decode(c):
        return nb.vmath("SUBTRACT", nb.vmath("SCALE", c, scale=2.0), (1.0, 1.0, 1.0))

    nb_b = decode(b)
    if turn:
        x, y, z = nb.separate(nb_b)
        nb_b = nb.combine(y, nb.math("MULTIPLY", x, -1.0), z)   # B was sampled at coordinates turned +90 degrees
    n = nb.mix(blend, decode(a), nb_b, kind="VECTOR")
    if swap:
        x, y, z = nb.separate(n)
        n = nb.combine(y, x, z)
    n = nb.vmath("NORMALIZE", n)
    return nb.vmath("ADD", nb.vmath("SCALE", n, scale=0.5), (0.5, 0.5, 0.5))


def object_prop(nb, name, default=1.0):
    """An object custom property read in the shader, `default` where the object lacks it (an object
    attribute's Alpha is 1 when the property exists, 0 when it does not: measured in 4.5, 2026-10-27)."""
    a = nb.node("ShaderNodeAttribute", attribute_type="OBJECT", attribute_name=name)
    return nb.mix(a.outputs["Alpha"], default, a.outputs["Fac"], kind="FLOAT")


def dust_zone(nb):
    """A part's dust-zone weight (§4.10): the point attribute `wear_dust` where the object carries the flag
    `wear_zones` (both written by materials.wear_zones()), else 1, so an object without zones gets the
    geometric dust alone. A geometry attribute cannot tell missing from 0, hence the object flag."""
    flag = nb.node("ShaderNodeAttribute", attribute_type="OBJECT", attribute_name="wear_zones").outputs["Alpha"]
    return nb.mix(flag, 1.0, nb.attr("wear_dust"), kind="FLOAT")


def edge_mask(nb, spec, zone=1.0):
    """MG.Mask.EdgeBevel with a recipe's edge settings ({radius_mm, width, noise_mm})."""
    g = nb.group("MG.Mask.EdgeBevel", {"Radius mm": spec.get("radius_mm", 0.8), "Width": spec.get("width", 0.08),
                                       "Noise mm": spec.get("noise_mm", 0.6),
                                       "Noise Amount": spec.get("noise_amount", 0.5), "Zone": zone})
    return K.sock(g, "Edge", out=True)


def weather(nb, rec, color, rough, spec, edge=None, vector=None, box=False):
    """§4.0's last two layers for a recipe with a wear preset (§4.10): grime (the preset's height band, the
    recipe's amount, oil and cavity weight) then dust last (the recipe's amount or the preset's, the part's
    zones and side factor, SurfaceImperfections015's drift sampled on `vector`: UV.Real for cloth and
    leather, the object's coordinates by box projection for hard parts). A recipe whose wear is "none"
    passes through. Returns {color, rough, spec, coverage, damp, height} as sockets or constants."""
    out = {"color": color, "rough": rough, "spec": spec, "coverage": 0.0, "damp": 1.0, "height": 0.0}
    name = rec.get("wear")
    if name not in C.WEAR_PRESETS or name == "none":
        return out
    preset = C.WEAR_PRESETS[name]
    gr = rec.get("grime")
    if gr:
        hi, lo = preset.get("grime_band_mm", (0.0, -10.0))
        g = nb.group("MG.Weather.Grime", {"Base Color": out["color"], "Base Roughness": out["rough"],
                                          "Amount": gr.get("amount", preset.get("grime", 0.0)),
                                          "Oil": gr.get("oil", preset.get("grime_oil", 0.2)),
                                          "Band Low mm": lo, "Band High mm": hi,
                                          "Cavity Weight": gr.get("cavity", preset.get("grime_cavity", 0.6))})
        out["color"], out["rough"] = K.sock(g, "Color", out=True), K.sock(g, "Roughness", out=True)
    du = rec.get("dust") or {}
    amount = du.get("amount", preset.get("dust", 0.0))
    if amount <= 0.0:
        return out
    if vector is None:
        vector, box = nb.coords("Object"), True
    st = C.TILE_PERIODS["SurfaceImperfections015"]
    drift = antirepeat(nb, "SurfaceImperfections015", "opacity", vector, st["tiles_mm"]["default"], box=box)
    drift = nb.node("ShaderNodeRGBToBW", inputs={"Color": drift}).outputs[0]
    shape = {k: du.get(k, preset.get(f"dust_{k}")) for k in ("noise_mm", "ao_mm", "open", "shelter")}
    d = nb.group("MG.Weather.Dust", {"Base Color": out["color"], "Base Roughness": out["rough"],
                                     "Base Specular": out["spec"], "Amount": amount,
                                     "Noise mm": shape["noise_mm"], "AO Distance mm": shape["ao_mm"],
                                     "Open": shape["open"], "Shelter": shape["shelter"],
                                     "Side": object_prop(nb, "wear_dust_scale", 1.0),
                                     "Zone": dust_zone(nb) if "wear_dust" in rec.get("reads", {}).get("attributes", ())
                                     else 1.0,
                                     "Edge": edge if edge is not None else 0.0,
                                     "Dust Roughness": du.get("rough", 0.88), "Drift": drift})
    out.update(color=K.sock(d, "Color", out=True), rough=K.sock(d, "Roughness", out=True),
               spec=K.sock(d, "Specular", out=True), coverage=K.sock(d, "Coverage", out=True),
               damp=K.sock(d, "Bump Damp", out=True), height=K.sock(d, "Height", out=True))
    return out


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
                       "Ridge Depth mm", "Ridge Distortion", "Ridge Distortion mm", "Ridge Mask", "Ridge Field mm",
                       "Ridge Field Weight", "Pore Cell mm",
                       "Pore Radius", "Pore Depth mm", "Pore Mask", "Peel mm", "Peel Depth mm", "LOD"},
                      {"Height", "Lines", "Pits", "Ridges"}),
    "MG.Tile.AntiRepeat": ({"Vector", "Tile mm", "Turn", "LOD"}, {"Vector A", "Vector B", "Blend"}),
    "MG.Knit.Stitch": ({"Vector", "Wale mm", "Course mm", "Mortar", "Height mm", "LOD"}, {"Height"}),
    "MG.Weather.Grime": ({"Base Color", "Base Roughness", "Amount", "Oil", "Band Low mm", "Band High mm", "Bottom",
                          "Cavity Weight", "Streak Amount", "Streak Length mm", "Streak Width mm", "Dry", "Oily",
                          "Mask", "Mask Only", "LOD"}, {"Color", "Roughness", "Grime"}),
    "MG.Weather.Dust": ({"Base Color", "Base Roughness", "Base Specular", "Amount", "Up Low", "Up High", "Up Power",
                         "AO Distance mm", "Open", "Shelter", "Noise mm", "Side", "Edge", "Zone", "Local Up", "Thin", "Thick",
                         "Dust Roughness", "Drift", "Mask", "LOD"},
                        {"Color", "Roughness", "Specular", "Coverage", "Height", "Bump Damp"}),
    "MG.Mask.EdgeBevel": ({"Radius mm", "Width", "Noise mm", "Noise Amount", "Zone", "LOD"}, {"Edge"}),
    "MG.Weather.Edge": ({"Base Color", "Base Roughness", "Base Metallic", "Base Coat", "Worn Color", "Worn Roughness",
                         "Worn Metallic", "Worn Coat", "Edge", "Amount", "LOD"},
                        {"Color", "Roughness", "Metallic", "Coat", "Wear"}),
    "MG.Polish": ({"Polish", "Base Color", "Base Roughness", "Polished Roughness", "Coat", "Color Shift", "Shift",
                   "Noise mm", "LOD"}, {"Roughness", "Coat", "Color", "Mask"}),
    "MG.Weave.Basket": ({"Vector", "Pitch U mm", "Pitch V mm", "Crown mm", "Distortion", "LOD"}, {"Height"}),
    "MG.Weave.Herringbone": ({"Vector", "Period mm", "Twill mm", "Twill Share", "Distortion", "Height mm", "LOD"},
                             {"Height"}),
    "MG.Braid": ({"Vector", "Repeat mm", "Around", "Circumference mm", "Height mm", "LOD"}, {"Height", "Groove"}),
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
        # the ridge field (2026-10-13): off by default (weight 0, the diagonal bands), a sine of the field's phase
        assert items["Ridge Field Weight"].default_value == 0.0 and "SINE" in ops, ops
        waves = [n for n in ng.nodes if n.bl_idname == "ShaderNodeTexWave"]
        assert len(waves) == 1 and waves[0].bands_direction == "DIAGONAL", len(waves)
    finally:
        bpy.data.node_groups.remove(ng)
    # the weathering groups (2026-10-27): dust reads the TRUE normal (weave and grain never speckle it) and
    # shelters by AO; the edge mask is a Bevel node against the interpolated normal; the weaves are Wave bands
    for name, check in (("MG.Weather.Dust", lambda ng: (
                            any(n.bl_idname == "ShaderNodeNewGeometry" and n.outputs["True Normal"].is_linked
                                for n in ng.nodes)
                            and any(n.bl_idname == "ShaderNodeAmbientOcclusion" for n in ng.nodes))),
                        ("MG.Mask.EdgeBevel", lambda ng: any(n.bl_idname == "ShaderNodeBevel" for n in ng.nodes)),
                        ("MG.Weave.Basket", lambda ng: sorted(n.bands_direction for n in ng.nodes
                                                              if n.bl_idname == "ShaderNodeTexWave") == ["X", "Y"]),
                        ("MG.Weave.Herringbone", lambda ng: any(n.bl_idname == "ShaderNodeMath" and n.operation == "SIGN"
                                                                for n in ng.nodes))):
        ng = bpy.data.node_groups.new(f"Lib.Test.{name}", "ShaderNodeTree")
        try:
            GROUPS[name](ng)
            assert check(ng), name
        finally:
            bpy.data.node_groups.remove(ng)
    assert abs(K.cover_threshold(0.5) - 0.5) < 1e-9 and 0.6 < K.cover_threshold(0.06) < 0.65
    try:
        build("MG.Weather.Chips")
        raise AssertionError("a planned group was built")
    except NotBuilt:
        pass
    return out
