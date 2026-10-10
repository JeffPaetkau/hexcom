"""Fabric recipes (spec 16 §3.3.4). Built so far: Knit.Sock.WoolNylon and its .Reinforced (spec 01 §3.6,
§5.4 as spec 16 resolved them: sheen 0.08 / 0.06 with §3.1's tint rule, roughness 0.80 / 0.65,
knitted_fleece at a 230 mm tile, grime from the part's `sock_grime` mask, pilling on `sock_sole`; the
MG.Knit.Stitch brick is off while the photographed knit carries the stitch, see mat_catalogue). Every tiled
map is sampled on `UV.Real` (metres; u around the sock, v along it, so the wales run along the leg) through
MG.Tile.AntiRepeat (§4.8); an object without that UV map samples one texel everywhere, i.e. a plain knit,
and assign() reports the missing map.
"""
from . import mat_catalogue as C
from . import mat_core as K

GROUPS_USED = {"knit_sock": ("MG.Tile.AntiRepeat", "MG.Knit.Stitch", "MG.Weather.Grime")}


def build_material(mat, rec, part, overrides):
    {"knit_sock": build_knit_sock}[rec["builder"]](mat, rec)


def antirepeat(nb, asset, kind, vector, tile_mm):
    """One map of a texture set sampled twice through MG.Tile.AntiRepeat and blended. Colour and data maps
    return the blended colour; a normal map (normal_gl) returns a tangent-space colour for a Normal Map
    node, with sample B's XY turned back by -90 degrees and the blend renormalised (§4.8). A directional
    set (TILE_PERIODS "directional") is offset, never turned."""
    turn = 0.0 if C.TILE_PERIODS.get(asset, {}).get("directional") else 1.0
    g = nb.group("MG.Tile.AntiRepeat", {"Vector": vector, "Tile mm": tile_mm, "Turn": turn})
    img = K.texture(asset, kind)
    a = K.image_node(nb, img, K.sock(g, "Vector A", out=True)).outputs["Color"]
    b = K.image_node(nb, img, K.sock(g, "Vector B", out=True)).outputs["Color"]
    blend = K.sock(g, "Blend", out=True)
    if kind != "normal_gl":
        return nb.mix(blend, a, b)

    def decode(c):
        return nb.vmath("SUBTRACT", nb.vmath("SCALE", c, scale=2.0), (1.0, 1.0, 1.0))

    nb_b = decode(b)
    if turn:
        x, y, z = nb.separate(nb_b)
        nb_b = nb.combine(y, nb.math("MULTIPLY", x, -1.0), z)   # B was sampled at coordinates turned +90 degrees
    n = nb.vmath("NORMALIZE", nb.mix(blend, decode(a), nb_b, kind="VECTOR"))
    return nb.vmath("ADD", nb.vmath("SCALE", n, scale=0.5), (0.5, 0.5, 0.5))


def build_knit_sock(mat, rec):
    nb = K.new_tree(mat)
    tp = C.TILE_PERIODS[rec["texture"]]
    st, mp = tp["stats"], tp["maps"]
    base = C.hex_to_linear(rec["albedo_hex"])
    uv = nb.uv(rec["uv"])
    tile = rec["tile_mm"]
    # colour: the photograph's yarn-to-yarn luminance as a ±6 % high-pass on the recipe's albedo (its own
    # brown is never used: §3.2 keeps the photographed colours out of every recipe)
    diff = antirepeat(nb, rec["texture"], "color", uv, tile)
    lum = nb.node("ShaderNodeRGBToBW", inputs={"Color": diff}).outputs[0]
    hp = nb.map_range(nb.math("DIVIDE", nb.math("SUBTRACT", lum, st["diff_lum_mean"]), 2.0 * st["diff_lum_sd"]),
                      -1.0, 1.0, -1.0, 1.0)
    col = nb.vmath("SCALE", base, scale=nb.math("ADD", 1.0, nb.math("MULTIPLY", hp, mp["diff_highpass"])))
    # roughness: the map's variation about its own mean, at half strength, about the recipe's value
    rmap = antirepeat(nb, rec["texture"], "roughness", uv, tile)
    r = nb.math("ADD", rec["rough"], nb.math("MULTIPLY", nb.math("SUBTRACT", rmap, st["rough_mean"]), mp["rough"]))
    nmap = nb.node("ShaderNodeNormalMap", space="TANGENT", uv_map=rec["uv"],
                   inputs={"Strength": rec.get("normal_strength", mp["nor_gl"]),
                           "Color": antirepeat(nb, rec["texture"], "normal_gl", uv, tile)})
    # pills: matted tufts with irregular outlines, a low soft dome, rougher and a little paler
    pl = rec["pilling"]
    pd = nb.voronoi(uv, 1000.0 / pl["cell_mm"], feature="F1", randomness=1.0, dims="2D")
    thr = nb.math("MULTIPLY", pl["threshold"], nb.math("ADD", 1.0, nb.math(
        "MULTIPLY", nb.noise_signed(uv, 1000.0 / (0.4 * pl["cell_mm"])), pl["irregular"])))
    pill = nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, nb.smoothstep(pd, nb.math("MULTIPLY", thr, 0.3), thr)),
                   nb.attr("sock_sole"))
    h = nb.math("MULTIPLY", pill, pl["height_mm"] / 1000.0)
    sti = rec["stitch"]
    if rec["stitch_relief"] > 0.0:   # the procedural stitch, where no photographed knit carries it (§4.7)
        stitch = nb.group("MG.Knit.Stitch", {"Vector": uv, "Wale mm": sti["wale_mm"], "Course mm": sti["course_mm"],
                                             "Mortar": sti["mortar"],
                                             "Height mm": sti["height_mm"] * rec["stitch_relief"]})
        h = nb.math("ADD", h, K.sock(stitch, "Height", out=True))
    n = nb.bump(h, normal=nmap.outputs["Normal"])
    col = nb.vmath("SCALE", col, scale=nb.math("ADD", 1.0, nb.math("MULTIPLY", pill, pl["lighten"])))
    r = nb.math("ADD", r, nb.math("MULTIPLY", pill, pl["rough_add"]), clamp=True)
    gr = rec["grime"]
    grime = nb.group("MG.Weather.Grime", {"Base Color": col, "Base Roughness": r, "Amount": gr["amount"],
                                          "Oil": gr["oil"], "Mask": nb.attr("sock_grime"), "Mask Only": 1.0})
    p = K.principled(nb, base=K.sock(grime, "Color", out=True), rough=K.sock(grime, "Roughness", out=True),
                     ior=rec["ior"], spec=rec["spec"], sheen=rec["sheen"], sheen_rough=rec["sheen_rough"],
                     sheen_tint=C.lift(base, C.CLASS_RULES[rec["class"]]["sheen_tint_lift"]),
                     sss=rec["sss_weight"], sss_radius=rec["sss_radius"], sss_scale=rec["sss_scale"], normal=n)
    K.output(nb, p.outputs[0])


def selftest():
    """The sock tree: the knit sampled on UV.Real, never turned (a directional set), its maps in their colour
    spaces, the grime group driven by the mask alone, the sheen inside the class cap."""
    import bpy
    from . import materials as M
    m = M.get("Knit.Sock.WoolNylon", "Lib")
    try:
        nodes = m.node_tree.nodes
        ar = [n for n in nodes if n.bl_idname == "ShaderNodeGroup" and n.node_tree.name == "MG.Tile.AntiRepeat"]
        assert ar and all(n.inputs["Turn"].default_value == 0.0 for n in ar), "knitted_fleece must not be turned"
        assert all(n.uv_map == "UV.Real" for n in nodes if n.bl_idname in ("ShaderNodeUVMap", "ShaderNodeNormalMap"))
        cs = {n.image.get("lib_kind"): n.image.colorspace_settings.name for n in nodes if n.bl_idname == "ShaderNodeTexImage"}
        assert cs == {"color": "sRGB", "roughness": "Non-Color", "normal_gl": "Non-Color"}, cs
        gr = next(n for n in nodes if n.bl_idname == "ShaderNodeGroup" and n.node_tree.name == "MG.Weather.Grime")
        assert gr.inputs["Mask Only"].default_value == 1.0 and gr.inputs["Mask"].is_linked
        p = next(n for n in nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
        assert p.inputs["Sheen Weight"].default_value <= C.CLASS_RULES["textile_coloured"]["sheen"][1] + 1e-9
        return {"antirepeat": len(ar), "images": cs, "tree_hash": K.tree_hash(m.node_tree)}
    finally:
        if m.users == 0:
            bpy.data.materials.remove(m)
