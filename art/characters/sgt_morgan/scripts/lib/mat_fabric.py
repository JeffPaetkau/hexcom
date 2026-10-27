"""Fabric recipes (spec 16 §3.3.4).

Knit.Sock.WoolNylon and its .Reinforced (spec 01 §3.6, §5.4 as spec 16 resolved them: sheen 0.08 / 0.06 with
§3.1's tint rule, roughness 0.80 / 0.65, knitted_fleece at a 230 mm tile, grime from the part's `sock_grime`
mask, pilling on `sock_sole`; the MG.Knit.Stitch brick is off while the photographed knit carries the
stitch, see mat_catalogue).

The boot's textiles (2026-10-27, spec 02 §0 item 7): Cordura.500D.Black (Fabric063 at 156 mm, normal x0.6,
roughness about the recipe's value, its AO x0.3 into the albedo, MG.Weave.Basket at the 0.61 mm yarn, polish
and scuffs from the part's `polish` attribute), Webbing.Nylon.Black (poly_wool_herringbone at 280 mm, its
image axes crossed with the strap's UV, MG.Weave.Herringbone, selvedge fuzz on the strap's edges by
MG.Mask.EdgeBevel), Lace.Nylon.Black (MG.Braid on the sweep's UV.Real), Thread.Bonded.Black (sun-greyed on
up-facing runs), Foam.ClosedCell.Black (cut cells) and Fabric.BackFace (the parent recipe's builder with its
albedo x 0.8, raised to the class floor, roughness + 0.05, no wear). Grime then dust come last through
mat_groups.weather() from the recipe's wear preset; dust scales the coat and the sheen by (1 - c) and damps
the weave's relief (§4.2 steps 9-10).

Every tiled map is sampled on `UV.Real` (metres; u along a strap or a lace, v across or around) through
MG.Tile.AntiRepeat (§4.8); an object without that UV map samples one texel everywhere, i.e. a plain cloth,
and assign() reports the missing map.
"""
from . import mat_catalogue as C
from . import mat_core as K
from . import mat_groups as G

_WEAR = ("MG.Tile.AntiRepeat", "MG.Weather.Grime", "MG.Weather.Dust")
GROUPS_USED = {"knit_sock": ("MG.Tile.AntiRepeat", "MG.Knit.Stitch", "MG.Weather.Grime"),
               "cordura": _WEAR + ("MG.Weave.Basket", "MG.Polish"),
               "webbing": _WEAR + ("MG.Weave.Herringbone", "MG.Mask.EdgeBevel"),
               "lace": _WEAR + ("MG.Braid",),
               "thread": (), "foam": (),
               "backface": _WEAR + ("MG.Knit.Stitch", "MG.Weave.Basket", "MG.Polish", "MG.Weave.Herringbone",
                                    "MG.Mask.EdgeBevel", "MG.Braid")}

antirepeat = G.antirepeat   # the shared sampler (it lived here until the hard family needed it too)


def build_material(mat, rec, part, overrides):
    BUILDERS[rec["builder"]](mat, rec)


def _sheen_tint(rec, base):
    return C.lift(base, C.CLASS_RULES[rec["class"]].get("sheen_tint_lift", 0.25))


def _finish(nb, rec, base, w, normal, height, sheen=None, **extra):
    """The Principled at the end of a textile: dust damps the relief and scales the sheen (§4.2 steps 9-10)."""
    h = nb.math("ADD", nb.math("MULTIPLY", height, w["damp"]), w["height"]) if height is not None else w["height"]
    n = nb.bump(h, normal=normal)
    sh = rec.get("sheen", 0.0) if sheen is None else sheen
    if not isinstance(w["coverage"], float):
        sh = nb.math("MULTIPLY", sh, nb.math("SUBTRACT", 1.0, w["coverage"]))
    p = K.principled(nb, base=w["color"], rough=w["rough"], ior=rec["ior"], spec=w["spec"], sheen=sh,
                     sheen_rough=rec.get("sheen_rough", 0.5), sheen_tint=_sheen_tint(rec, base), normal=n, **extra)
    K.output(nb, p.outputs[0])
    return p


def _rough_about(nb, rmap, rough, mean, gain):
    """A roughness map's variation about its own mean, x gain, about the recipe's value (§3.2)."""
    return nb.math("ADD", rough, nb.math("MULTIPLY", nb.math("SUBTRACT", rmap, mean), gain), clamp=True)


def build_cordura(mat, rec):
    """§3.3.4 Cordura.500D.Black: Fabric063 (never its colour) and the basket weave on UV.Real."""
    nb = K.new_tree(mat)
    tp = C.TILE_PERIODS[rec["texture"]]
    st, mp = tp["stats"], tp["maps"]
    base = C.hex_to_linear(rec["albedo_hex"])
    uv = nb.uv(rec["uv"])
    tile = rec["tile_mm"]
    # §3.2: the photograph's AO x0.3 into the albedo, about its own mean so the recipe's albedo holds
    ao = nb.node("ShaderNodeRGBToBW", inputs={"Color": antirepeat(nb, rec["texture"], "ao", uv, tile)}).outputs[0]
    col = nb.vmath("SCALE", base, scale=nb.math("ADD", 1.0, nb.math(
        "MULTIPLY", nb.math("SUBTRACT", nb.math("DIVIDE", ao, st["ao_mean"]), 1.0), mp["ao"])))
    rmap = nb.node("ShaderNodeRGBToBW", inputs={"Color": antirepeat(nb, rec["texture"], "roughness", uv, tile)}).outputs[0]
    r = _rough_about(nb, rmap, rec["rough"], st["rough_mean"], mp["rough"])
    nmap = nb.node("ShaderNodeNormalMap", space="TANGENT", uv_map=rec["uv"],
                   inputs={"Strength": mp["nor_gl"], "Color": antirepeat(nb, rec["texture"], "normal_gl", uv, tile)})
    wv = rec["weave"]
    weave = K.sock(nb.group("MG.Weave.Basket", {"Vector": uv, "Pitch U mm": wv["pitch_mm"], "Pitch V mm": wv["pitch_mm"],
                                                "Crown mm": wv["crown_mm"], "Distortion": wv["distortion"]}),
                   "Height", out=True)
    # polish (knee pockets, a boot's counter rub) and, inside it, scuffs toward a pale grey (§3.3.4)
    pol = rec.get("polish")
    if pol and "polish" in rec.get("reads", {}).get("attributes", ()):
        pg = nb.group("MG.Polish", {"Polish": nb.attr("polish"), "Base Color": col, "Base Roughness": r,
                                    "Polished Roughness": pol["rough"], "Noise mm": pol["noise_mm"]})
        r = K.sock(pg, "Roughness", out=True)
        sc = rec["scuff"]
        lo, hi = K.NOISE_BAND
        n = nb.map_range(nb.noise(uv, 1000.0 / sc["noise_mm"], detail=2.0), lo, hi, 0.0, 1.0)
        col = nb.mix(nb.math("MULTIPLY", nb.math("MULTIPLY", n, sc["share"]), K.sock(pg, "Mask", out=True)),
                     col, C.hex_to_linear(sc["hex"]))
    w = G.weather(nb, rec, col, r, rec["spec"], vector=uv)
    _finish(nb, rec, base, w, nmap.outputs["Normal"], weave)


def build_webbing(mat, rec):
    """§3.3.4 Webbing.Nylon.Black: the photographed herringbone (its image x is across the strap, so it is
    sampled at (v, u)) at 280 mm, the procedural herringbone on top, selvedge fuzz on the strap's edges."""
    nb = K.new_tree(mat)
    tp = C.TILE_PERIODS[rec["texture"]]
    base = C.hex_to_linear(rec["albedo_hex"])
    uv = nb.uv(rec["uv"])
    tile = rec["tile_mm"]
    swap = tp.get("across_axis") == "x"
    rmap = nb.node("ShaderNodeRGBToBW", inputs={"Color": antirepeat(nb, rec["texture"], "roughness", uv, tile,
                                                                    swap=swap)}).outputs[0]
    r = _rough_about(nb, rmap, rec["rough"], tp["stats"]["rough_mean"], 1.0)
    nmap = nb.node("ShaderNodeNormalMap", space="TANGENT", uv_map=rec["uv"],
                   inputs={"Strength": rec.get("normal_strength", tp["maps"]["nor_gl"]),
                           "Color": antirepeat(nb, rec["texture"], "normal_gl", uv, tile, swap=swap)})
    wv = rec["weave"]
    weave = K.sock(nb.group("MG.Weave.Herringbone", {"Vector": uv, "Period mm": wv["period_mm"], "Twill mm": wv["twill_mm"],
                                                     "Twill Share": wv["twill_share"], "Distortion": wv["distortion"],
                                                     "Height mm": wv["height_mm"]}), "Height", out=True)
    sv = rec["selvedge"]
    e = G.edge_mask(nb, {"radius_mm": sv["radius_mm"], "width": sv["width"], "noise_mm": 2.0, "noise_amount": 0.6})
    col = nb.vmath("SCALE", base, scale=nb.math("MULTIPLY_ADD", e, sv["lift"], 1.0))
    r = nb.mix(e, r, sv["rough"], kind="FLOAT")
    w = G.weather(nb, rec, col, r, rec["spec"], edge=e, vector=uv)
    _finish(nb, rec, base, w, nmap.outputs["Normal"], weave)


def build_lace(mat, rec):
    """§3.3.4 Lace.Nylon.Black: MG.Braid on the lace's UV.Real, the grooves darkened x 0.8."""
    nb = K.new_tree(mat)
    base = C.hex_to_linear(rec["albedo_hex"])
    uv = nb.uv(rec["uv"])
    b = rec["braid"]
    br = nb.group("MG.Braid", {"Vector": uv, "Repeat mm": b["repeat_mm"], "Around": b["around"],
                               "Circumference mm": 3.141592653589793 * rec["diameter_mm"], "Height mm": b["height_mm"]})
    col = nb.vmath("SCALE", base, scale=nb.map_range(K.sock(br, "Groove", out=True), 0.0, 1.0, b["groove"], 1.0))
    w = G.weather(nb, rec, col, rec["rough"], rec["spec"], vector=uv)
    _finish(nb, rec, base, w, None, K.sock(br, "Height", out=True))


def build_thread(mat, rec):
    """§3.3.4 Thread.Bonded.Black: the dyed thread, sun-greyed toward #3a3430 where its runs face up."""
    nb = K.new_tree(mat)
    base = C.hex_to_linear(rec["albedo_hex"])
    _, _, z = nb.separate(nb.geometry("True Normal"))
    up = nb.map_range(z, 0.25, 0.85, 0.0, 1.0, "SMOOTHSTEP")
    col = nb.mix(nb.math("MULTIPLY", up, rec["sun"]["share"]), base, C.hex_to_linear(rec["sun"]["hex"]))
    p = K.principled(nb, base=col, rough=rec["rough"], ior=rec["ior"], spec=rec["spec"], sheen=rec["sheen"],
                     sheen_rough=rec["sheen_rough"], sheen_tint=_sheen_tint(rec, base))
    K.output(nb, p.outputs[0])


def build_foam(mat, rec):
    """§3.3.4 Foam.ClosedCell.Black: cut closed cells as shallow dimples (Voronoi F1, 0.3 mm, 0.1 mm)."""
    nb = K.new_tree(mat)
    c = rec["cell"]
    d = nb.voronoi(nb.coords("Object"), 1000.0 / c["cell_mm"], feature="F1", randomness=1.0)
    h = nb.math("MULTIPLY", nb.smoothstep(d, 0.0, 0.6), c["depth_mm"] * 0.001)
    p = K.principled(nb, base=C.hex_to_linear(rec["albedo_hex"]), rough=rec["rough"], ior=rec["ior"], spec=rec["spec"],
                     normal=nb.bump(h))
    K.output(nb, p.outputs[0])


def build_backface(mat, rec):
    """§3.3.4 / C41 Fabric.BackFace: the parent's own recipe, its albedo x 0.8 (raised to the class floor by
    mat_catalogue.resolve()), roughness + 0.05, no wear: AO does the darkening of a pocket or a lining."""
    import copy
    parent = copy.deepcopy(C.CATALOGUE[rec["parent"]])
    if parent.get("family") != "fabric" or parent["builder"] == "backface":
        raise ValueError(f"Fabric.BackFace: parent {rec['parent']} is not a cloth recipe")
    parent.update(id=rec["parent"], albedo_hex=rec["albedo_hex"], rough=parent["rough"] + rec["rough_add"],
                  wear="none")
    if "reads" in parent:
        parent["reads"] = {k: [a for a in v if a not in ("polish",)] for k, v in parent["reads"].items()}
    BUILDERS[parent["builder"]](mat, parent)


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


BUILDERS = {"knit_sock": build_knit_sock, "cordura": build_cordura, "webbing": build_webbing, "lace": build_lace,
            "thread": build_thread, "foam": build_foam, "backface": build_backface}


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
        out = {"antirepeat": len(ar), "images": cs, "tree_hash": K.tree_hash(m.node_tree)}
    finally:
        if m.users == 0:
            bpy.data.materials.remove(m)
    out["boot"] = _selftest_boot()
    return out


def _groups_in(m):
    return {n.node_tree.name for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeGroup"}


def _selftest_boot():
    """The boot's textiles (2026-10-27): each builds with its groups; the Cordura never uses its photograph's
    colour; the webbing's herringbone is directional (never turned) and read at (v, u); dust is last and
    reads the dust zone; the back face is darker than its parent but not under the class floor."""
    import bpy
    from . import materials as M
    made, res = [], {}
    try:
        for rid, groups in (("Cordura.500D.Black", {"MG.Weave.Basket", "MG.Polish", "MG.Weather.Dust"}),
                            ("Webbing.Nylon.Black", {"MG.Weave.Herringbone", "MG.Mask.EdgeBevel", "MG.Weather.Dust"}),
                            ("Lace.Nylon.Black", {"MG.Braid", "MG.Weather.Dust"}),
                            ("Thread.Bonded.Black", set()), ("Foam.ClosedCell.Black", set()),
                            ("Fabric.BackFace", {"MG.Weave.Basket"})):
            m = M.get(rid, "Lib")
            made.append(m)
            assert groups <= _groups_in(m), (rid, groups - _groups_in(m))
            res[rid] = K.tree_hash(m.node_tree)
        cord = bpy.data.materials[M.material_name("Cordura.500D.Black", "Lib")]
        kinds = {n.image.get("lib_kind") for n in cord.node_tree.nodes if n.bl_idname == "ShaderNodeTexImage"
                 and n.image.get("lib_asset") == "Fabric063"}
        assert "color" not in kinds and {"ao", "roughness", "normal_gl"} <= kinds, kinds
        web = bpy.data.materials[M.material_name("Webbing.Nylon.Black", "Lib")]
        ar = [n for n in web.node_tree.nodes if n.bl_idname == "ShaderNodeGroup" and n.node_tree.name == "MG.Tile.AntiRepeat"
              and n.inputs["Tile mm"].default_value == 280.0]
        assert ar and all(n.inputs["Turn"].default_value == 0.0 for n in ar), "the herringbone must not be turned"
        back = M.recipe("Fabric.BackFace")
        y_b, y_p = (C.luminance(C.hex_to_linear(M.recipe(r)["albedo_hex"])) for r in ("Fabric.BackFace", back["parent"]))
        assert C.CLASS_RULES[back["class"]]["albedo_y"][0] <= y_b < y_p, (y_b, y_p)
        backm = bpy.data.materials[M.material_name("Fabric.BackFace", "Lib")]
        assert "MG.Weather.Dust" not in _groups_in(backm) and "MG.Polish" not in _groups_in(backm)
        return res
    finally:
        for m in made:
            if m.name in bpy.data.materials and m.users == 0:
                bpy.data.materials.remove(m)
