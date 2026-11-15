"""Hard-family recipes (spec 16 §3.3.5-3.3.7): leather, rubber, moulded polymers, metals.

Built so far, the boot's (2026-10-27, spec 02 §0 item 7):

* Leather.Boot.FullGrain: Leather032 at 80 mm on UV.Real (1.0 mm grain cells), its normal at 0.35, its
  roughness map spread over 0.35 about the recipe's 0.50, its colour as a +-10 % multiply (the photograph's
  luminance high-pass; its grey is never used); the part's `crease` field lifts crests (+0.012 albedo, +0.1
  roughness), horizontal scuff streaks (1 : 1 : 14, 6 % cover) roughen and lighten, MG.Polish takes the
  part's `polish` zones and the worn edges (MG.Mask.EdgeBevel, §4.4's "leather -> polish") to roughness 0.36
  with coat 0.12 / 0.30, then grime in the height band and dust last (preset boot.toe: the part's zones,
  the side factor), dust also scaling the coat and damping the grain (§4.2 step 9-10).
* Rubber.Outsole.Black and Rubber.Rand.Black: carbon-black rubber at the class floor, roughness on a 17 mm
  noise, Rubber004 at 50 mm by box projection (its displacement as a 0.03 mm physical bump: a box projection
  has no tangent frame for a normal map), a 0.15 mm micro grain; the outsole's lug tops (faces looking at the
  floor) worn to albedo 0.14, roughness 0.75; the rand's bumper (`bumper` attribute) at 0.48 and scuffed pale
  on its lip and in short streaks along the boot's axis.
* EVA.Midsole.BlueGrey: the painted PU stripe, roughness 0.26-0.36, specular 0.6, a 0.08 mm cell bump.
* Metal.Gunmetal: black-oxide steel F0 (0.100, 0.100, 0.105), roughness 0.38-0.52 from Metal027 (box),
  anisotropy 0.3 round the object's Z, worn to bare steel F0 (0.56, 0.57, 0.58) at 0.25 on its edges
  (MG.Mask.EdgeBevel -> MG.Weather.Edge), dust as a dielectric layer over the metal (dust_over_metal()).
* Polymer.Black.Smooth: acetal at 0.40, Plastic012B (box) as roughness and a 4 um scratch relief, edges
  abraded +0.012 albedo, +0.08 roughness.

Take 2's materials round (2026-11-15):

* `painted` (Polymer.Painted.Armour, Paint.FDE.Brushed): an aerosol or brushed paint over a moulding of
  another colour. The paint's uneven cover is a mottle toward a second hex over a few cm; orange peel as a
  bump; the paint wears through to the substrate on the edges (MG.Mask.EdgeBevel at a wide radius, broken by
  a noise) and in chips (a noise above a cover threshold, gathered in patches, the threshold lowered near the
  edges), a small step down where it is gone; grime and dust last, by box projection.
* `lens`: a clear or frosted polymer or glass (transmission, roughness, an optional coat), no wear.
* `decal`: a brushed anodised plate (metal F0, edge wear to bare metal like `metal`) with a mark from a
  painted mask (GEN_TEXTURES, thresholded) on the object's 0-1 `UV.Decal`, the mark a dielectric paint mixed
  over the metal, grime on both, dust as the dielectric layer of dust_over_metal().

Hard parts without UV.Real sample tiled maps by box projection on Object coordinates (blend 0.2, §5.1); the
leather reads UV.Real like cloth (§3.3.5: "grain through UV.Real").
"""
from . import mat_catalogue as C
from . import mat_core as K
from . import mat_groups as G

_WEAR = ("MG.Tile.AntiRepeat", "MG.Weather.Grime", "MG.Weather.Dust")
GROUPS_USED = {"leather": _WEAR + ("MG.Polish", "MG.Mask.EdgeBevel"),
               "rubber": _WEAR + ("MG.Mask.EdgeBevel",),
               "midsole": _WEAR,
               "metal": _WEAR + ("MG.Mask.EdgeBevel", "MG.Weather.Edge"),
               "polymer": _WEAR + ("MG.Mask.EdgeBevel", "MG.Weather.Edge"),
               "painted": _WEAR,
               "lens": (),
               "decal": _WEAR + ("MG.Mask.EdgeBevel", "MG.Weather.Edge")}


def build_material(mat, rec, part, overrides):
    BUILDERS[rec["builder"]](mat, rec)


def _band01(nb, x, lo, hi):
    """A map's p2-p98 band to 0-1."""
    return nb.map_range(x, lo, hi, 0.0, 1.0)


def _bw(nb, colour):
    return nb.node("ShaderNodeRGBToBW", inputs={"Color": colour}).outputs[0]


def _noise01(nb, mm, detail=2.0, vector=None):
    """A noise at `mm` features remapped from its measured band to 0-1 (§9's noise lesson)."""
    lo, hi = K.NOISE_BANDS[int(detail)]
    return nb.map_range(nb.noise(vector if vector is not None else nb.coords("Object"), 1000.0 / mm, detail=detail),
                        lo, hi, 0.0, 1.0)


def _add(nb, colour, value):
    """colour + value on every channel (the spec's "+0.012 albedo")."""
    return nb.vmath("ADD", colour, nb.combine(value, value, value))


def _box_relief(nb, rec):
    """A box-projected set's displacement as a physical height (metres): its p2-p98 band is `relief_mm`."""
    st = C.TILE_PERIODS[rec["texture"]]["stats"]
    disp = _bw(nb, G.antirepeat(nb, rec["texture"], "displacement", nb.coords("Object"), rec["tile_mm"], box=True))
    return nb.math("MULTIPLY", nb.math("SUBTRACT", _band01(nb, disp, st["disp_p2"], st["disp_p98"]), 0.5),
                   rec["relief_mm"] * 0.001)


def _out(nb, shader):
    K.output(nb, shader)


# --------------------------------------------------------------------------- leather

def build_leather(mat, rec):
    nb = K.new_tree(mat)
    tp = C.TILE_PERIODS[rec["texture"]]
    st = tp["stats"]
    base = C.hex_to_linear(rec["albedo_hex"])
    uv = nb.uv(rec["uv"])
    tile = rec["tile_mm"]
    # grain colour: the photograph's luminance high-pass as a +-10 % multiply on the recipe's albedo (§3.2)
    lum = _bw(nb, G.antirepeat(nb, rec["texture"], "color", uv, tile))
    hp = nb.map_range(nb.math("DIVIDE", nb.math("SUBTRACT", lum, st["diff_lum_mean"]), 2.0 * st["diff_lum_sd"]),
                      -1.0, 1.0, -1.0, 1.0)
    col = nb.vmath("SCALE", base, scale=nb.math("MULTIPLY_ADD", hp, tp["maps"]["diff_multiply"], 1.0))
    # grain roughness: the map's p2-p98 band spread over rough_span about the recipe's value
    rmap = _bw(nb, G.antirepeat(nb, rec["texture"], "roughness", uv, tile))
    r = nb.math("ADD", rec["rough"] - 0.5 * rec["rough_span"],
                nb.math("MULTIPLY", _band01(nb, rmap, st["rough_p2"], st["rough_p98"]), rec["rough_span"]))
    sm = rec.get("sheen_mottle")
    if sm:   # the finish's uneven wear over a few cm
        r = nb.math("MULTIPLY_ADD", nb.noise_signed(nb.coords("Object"), 1000.0 / sm["noise_mm"]), sm["rough"], r)
    nmap = nb.node("ShaderNodeNormalMap", space="TANGENT", uv_map=rec["uv"],
                   inputs={"Strength": rec["normal_strength"],
                           "Color": G.antirepeat(nb, rec["texture"], "normal_gl", uv, tile)})
    # flex-crease crests (the part's `crease` field): paler and rougher, spec 02 §5.3 step 2
    cr = rec["crease"]
    crest = nb.smoothstep(nb.attr("crease"), cr["at"][0], cr["at"][1])
    col = _add(nb, col, nb.math("MULTIPLY", crest, cr["albedo_add"]))
    r = nb.math("MULTIPLY_ADD", crest, cr["rough_add"], r)
    # scuff streaks: a noise squashed 14 x along Z, so the streaks lie horizontal (spec 02 §5.3 step 4)
    sc = rec["scuff"]
    mp = nb.node("ShaderNodeMapping", vector_type="POINT", inputs={"Vector": nb.coords("Object")})
    L = 1000.0 / sc["length_mm"]
    nb.set(mp, "Scale", (L, L, L * sc["stretch"]))
    thr = K.cover_threshold(sc["cover"])
    scuff = nb.smoothstep(nb.noise(mp.outputs[0], 1.0, detail=2.0), thr - 0.01, thr + 0.01)
    # gathered where the boot is knocked: patches of `patch_mm` hold the 6 % and the rest is clean (an even
    # cover read as rain streaks over the whole upper)
    patch = nb.smoothstep(_noise01(nb, sc["patch_mm"]), 0.45, 0.65)
    scuff = nb.math("MULTIPLY", scuff, patch)
    col = _add(nb, col, nb.math("MULTIPLY", scuff, sc["albedo_add"]))
    r = nb.mix(scuff, r, sc["rough"], kind="FLOAT")
    # polish: the part's zones and the worn edges (§4.4: leather edges polish)
    ed = rec["edge"]
    edge = G.edge_mask(nb, ed)
    po = rec["polish"]
    pg = nb.group("MG.Polish", {"Polish": nb.math("MAXIMUM", nb.attr("polish"), nb.math("MULTIPLY", edge, ed["amount"])),
                                "Base Color": col, "Base Roughness": r, "Polished Roughness": po["rough"],
                                "Coat": po["coat"], "Noise mm": po["noise_mm"]})
    r = K.sock(pg, "Roughness", out=True)
    coat = K.sock(pg, "Coat", out=True)
    # dust last; the crease crests count as rubbed (§4.2 step 4's edge term): spec 02 §3.5, dust "wears off the crests"
    w = G.weather(nb, rec, col, r, rec["spec"], edge=nb.math("MAXIMUM", edge, crest), vector=uv)
    coat = nb.math("MULTIPLY", coat, nb.math("SUBTRACT", 1.0, w["coverage"]))
    # the grain's normal damped by dust (it fills the grain), then the dust's grit as a physical bump
    nb.set(nmap, "Strength", nb.math("MULTIPLY", rec["normal_strength"], w["damp"]))
    n = nb.bump(w["height"], normal=nmap.outputs["Normal"])
    p = K.principled(nb, base=w["color"], rough=w["rough"], ior=rec["ior"], spec=w["spec"], coat=coat,
                     coat_rough=po["coat_rough"], coat_ior=1.5, normal=n, coat_normal=n)
    _out(nb, p.outputs[0])


# --------------------------------------------------------------------------- rubber and the midsole

def build_rubber(mat, rec):
    nb = K.new_tree(mat)
    base = C.hex_to_linear(rec["albedo_hex"])
    obj = nb.coords("Object")
    lo, hi = rec["rough_range"]
    r = nb.map_range(_noise01(nb, rec["rough_noise_mm"]), 0.0, 1.0, lo, hi)
    mi = rec["micro"]
    h = nb.math("ADD", _box_relief(nb, rec),
                nb.math("MULTIPLY", nb.noise_signed(obj, 1000.0 / mi["noise_mm"], detail=1.0), 0.5 * mi["height_mm"] * 0.001))
    col = base
    edge = None
    if rec.get("lug_wear"):   # the outsole's lug tops: the faces that look at the floor, worn grey and matte
        lw = rec["lug_wear"]
        _, _, z = nb.separate(nb.geometry("True Normal"))
        top = nb.map_range(nb.math("MULTIPLY", z, -1.0), lw["facing"][0], lw["facing"][1], 0.0, 1.0, "SMOOTHSTEP")
        col = nb.mix(top, col, (lw["albedo"],) * 3)
        r = nb.mix(top, r, lw["rough"], kind="FLOAT")
    if rec.get("bumper_rough") is not None:   # the toe bumper (`bumper` attribute) is a little glossier
        r = nb.mix(nb.attr("bumper"), r, rec["bumper_rough"], kind="FLOAT")
    if rec.get("scuff"):   # the bumper lip's wear and short pale streaks along the boot's axis on forward faces
        sc = rec["scuff"]
        edge = G.edge_mask(nb, rec["edge"])
        # streaks long in plan and thin in height: horizontal on the bumper's front and along the sides (a
        # streak "along the boot's axis" alone would be a dot on the front face, which looks along that axis)
        mp = nb.node("ShaderNodeMapping", vector_type="POINT", inputs={"Vector": obj})
        nb.set(mp, "Scale", (1000.0 / sc["length_mm"], 1000.0 / sc["length_mm"], 1000.0 / sc["width_mm"]))
        thr = K.cover_threshold(sc["streak_cover"])
        streak = nb.smoothstep(nb.noise(mp.outputs[0], 1.0, detail=2.0), thr - 0.015, thr + 0.015)
        n_obj = nb.node("ShaderNodeVectorTransform", vector_type="NORMAL", convert_from="WORLD", convert_to="OBJECT",
                        inputs={"Vector": nb.geometry("Normal")}).outputs[0]
        _, ny, _ = nb.separate(nb.vmath("NORMALIZE", n_obj))
        front = nb.map_range(nb.math("MULTIPLY", ny, -1.0), 0.2, 0.6, 0.0, 1.0, "SMOOTHSTEP")
        s = nb.math("MAXIMUM", nb.math("MULTIPLY", edge, sc["edge"]), nb.math("MULTIPLY", streak, front))
        col = nb.mix(nb.math("MULTIPLY", s, sc["share"]), col, C.hex_to_linear(sc["hex"]))
        r = nb.mix(s, r, sc["rough"], kind="FLOAT")
    w = G.weather(nb, rec, col, r, rec["spec"], edge=edge)
    n = nb.bump(nb.math("ADD", nb.math("MULTIPLY", h, w["damp"]), w["height"]))
    p = K.principled(nb, base=w["color"], rough=w["rough"], ior=rec["ior"], spec=w["spec"], normal=n)
    _out(nb, p.outputs[0])


def build_midsole(mat, rec):
    nb = K.new_tree(mat)
    lo, hi = rec["rough_range"]
    r = nb.map_range(_noise01(nb, rec["rough_noise_mm"]), 0.0, 1.0, lo, hi)
    ce = rec["cell"]
    h = nb.math("MULTIPLY", nb.noise_signed(nb.coords("Object"), 1000.0 / ce["noise_mm"], detail=1.0),
                0.5 * ce["height_mm"] * 0.001)
    w = G.weather(nb, rec, C.hex_to_linear(rec["albedo_hex"]), r, rec["spec"])
    n = nb.bump(nb.math("ADD", nb.math("MULTIPLY", h, w["damp"]), w["height"]))
    p = K.principled(nb, base=w["color"], rough=w["rough"], ior=rec["ior"], spec=w["spec"], normal=n)
    _out(nb, p.outputs[0])


# --------------------------------------------------------------------------- metal and polymer

def dust_over_metal(nb, metal_shader, coverage):
    """§4.2 step 10: dust never changes Metallic; on metal it is a dielectric layer (the ramp's colour by
    thickness c², roughness 0.88) mixed over the metal's shader by the coverage c."""
    t = nb.math("MULTIPLY", coverage, coverage)
    dust = nb.mix(t, C.hex_to_linear(G.DUST_THIN), C.hex_to_linear(G.DUST_THICK))
    d = K.principled(nb, base=dust, rough=0.88, ior=1.5, spec=0.5)
    mx = nb.node("ShaderNodeMixShader")
    nb.set(mx, 0, coverage)
    nb.link(metal_shader, mx.inputs[1])
    nb.link(d.outputs[0], mx.inputs[2])
    return mx.outputs[0]


def build_metal(mat, rec):
    nb = K.new_tree(mat)
    st = C.TILE_PERIODS[rec["texture"]]["stats"]
    rmap = _bw(nb, G.antirepeat(nb, rec["texture"], "roughness", nb.coords("Object"), rec["tile_mm"], box=True))
    lo, hi = rec["rough_range"]
    r = nb.map_range(rmap, st["rough_p2"], st["rough_p98"], lo, hi)
    ed = rec["edge"]
    edge = G.edge_mask(nb, ed)
    we = nb.group("MG.Weather.Edge", {"Base Color": rec["f0"], "Base Roughness": r, "Base Metallic": 1.0,
                                      "Worn Color": ed["f0"], "Worn Roughness": ed["rough"], "Worn Metallic": 1.0,
                                      "Edge": edge, "Amount": ed["amount"]})
    rec_metal = dict(rec, dust={"amount": 0.0})   # grime on the plate; the dust goes on as a layer below
    w = G.weather(nb, rec_metal, K.sock(we, "Color", out=True), K.sock(we, "Roughness", out=True), 0.5)
    tan = nb.node("ShaderNodeTangent", direction_type="RADIAL", axis="Z").outputs["Tangent"]
    p = K.principled(nb, base=w["color"], metal=1.0, rough=w["rough"], aniso=rec["aniso"], tangent=tan)
    shader = p.outputs[0]
    du = rec.get("dust") or {}
    if du.get("amount", 0.0) > 0.0:
        d = nb.group("MG.Weather.Dust", {"Amount": du["amount"], "Side": G.object_prop(nb, "wear_dust_scale", 1.0),
                                         "Edge": edge})
        shader = dust_over_metal(nb, shader, K.sock(d, "Coverage", out=True))
    _out(nb, shader)


def build_polymer(mat, rec):
    nb = K.new_tree(mat)
    st = C.TILE_PERIODS[rec["texture"]]["stats"]
    rmap = _bw(nb, G.antirepeat(nb, rec["texture"], "roughness", nb.coords("Object"), rec["tile_mm"], box=True))
    r = nb.math("ADD", rec["rough"] - 0.5 * rec["rough_span"],
                nb.math("MULTIPLY", _band01(nb, rmap, st["rough_p2"], st["rough_p98"]), rec["rough_span"]))
    base = C.hex_to_linear(rec["albedo_hex"])
    ed = rec["edge"]
    edge = G.edge_mask(nb, ed)
    we = nb.group("MG.Weather.Edge", {"Base Color": base, "Base Roughness": r, "Base Metallic": 0.0,
                                      "Worn Color": tuple(c + ed["albedo_add"] for c in base),
                                      "Worn Roughness": nb.math("ADD", r, ed["rough_add"]), "Worn Metallic": 0.0,
                                      "Edge": edge, "Amount": ed["amount"]})
    w = G.weather(nb, rec, K.sock(we, "Color", out=True), K.sock(we, "Roughness", out=True), rec["spec"], edge=edge)
    n = nb.bump(nb.math("ADD", nb.math("MULTIPLY", _box_relief(nb, rec), w["damp"]), w["height"]))
    p = K.principled(nb, base=w["color"], rough=w["rough"], ior=rec["ior"], spec=w["spec"], normal=n)
    _out(nb, p.outputs[0])


# --------------------------------------------------------------------------- take 2: paint, lenses, decals

def build_painted(mat, rec):
    nb = K.new_tree(mat)
    st = C.TILE_PERIODS[rec["texture"]]["stats"]
    obj = nb.coords("Object")
    rmap = _bw(nb, G.antirepeat(nb, rec["texture"], "roughness", obj, rec["tile_mm"], box=True))
    r = nb.math("ADD", rec["rough"] - 0.5 * rec["rough_span"],
                nb.math("MULTIPLY", _band01(nb, rmap, st["rough_p2"], st["rough_p98"]), rec["rough_span"]))
    base = C.hex_to_linear(rec["albedo_hex"])
    mo = rec["mottle"]
    col = nb.mix(nb.math("MULTIPLY", _noise01(nb, mo["noise_mm"], 3.0), mo["amount"]), base, C.hex_to_linear(mo["hex"]))
    pi = rec.get("paint_image")
    if pi:   # a painted swatch (GEN_TEXTURES) by box projection: its colour over its own mean, times the paint's
        st_i = C.GEN_TEXTURES[pi["image"]]["stats"]
        img = G.antirepeat(nb, pi["image"], "color", obj, pi["tile_mm"], box=True)
        ratio = nb.vmath("DIVIDE", img, tuple(st_i["mean_lin"]))
        ratio = nb.vmath("ADD", nb.vmath("SCALE", ratio, scale=pi["amount"]), (1.0 - pi["amount"],) * 3)
        col = nb.vmath("MULTIPLY", col, ratio)
    # where the paint is gone: the worn edges and the chips. The rims are found against the TRUE normal: the
    # plates' bevelled, weighted-normal edges already round the shading normal, so MG.Mask.EdgeBevel (which
    # compares with it) sees nothing there; facets of a curved face differ from the bevel's normal by less
    # than `floor`, which the mask ignores
    ed = rec["edge"]
    bev = nb.node("ShaderNodeBevel", samples=8, inputs={"Radius": ed["radius_mm"] * 0.001})
    d = nb.math("SUBTRACT", 1.0, nb.vmath("DOT_PRODUCT", bev.outputs["Normal"], nb.geometry("True Normal")))
    fl = ed.get("floor", 0.015)
    edge = nb.map_range(d, fl, fl + ed["width"], 0.0, 1.0, "SMOOTHSTEP")
    lo_b, hi_b = K.NOISE_BAND
    en = nb.map_range(nb.noise(obj, 1000.0 / ed["noise_mm"], detail=2.0), lo_b, hi_b, 0.3, 1.0)
    edge = nb.math("MULTIPLY", edge, nb.math("MULTIPLY_ADD", en, ed["noise_amount"], 1.0 - ed["noise_amount"]))
    ch = rec["chips"]
    thr = K.cover_threshold(ch["cover"])
    thr_local = nb.math("MULTIPLY_ADD", edge, -0.08 * ch["edge_bias"], thr)
    cn = _noise01(nb, ch["noise_mm"], 2.0)
    chip = nb.map_range(nb.math("SUBTRACT", cn, thr_local), -0.006, 0.006, 0.0, 1.0)
    patch = nb.smoothstep(_noise01(nb, ch["patch_mm"]), 0.42, 0.62)
    chip = nb.math("MULTIPLY", chip, nb.math("MAXIMUM", patch, edge))
    worn = nb.math("MAXIMUM", nb.math("MULTIPLY", edge, ed["amount"]), chip, clamp=True)
    fr = rec.get("frame")
    if fr:   # a part's own wear zone (the knee caps' raised frames, worn bare in the reference): a point attribute
        fw = nb.math("MULTIPLY", nb.attr(fr["attribute"]), nb.map_range(_noise01(nb, fr["noise_mm"]), 0.25, 0.6,
                                                                        1.0 - fr["break"], 1.0))
        worn = nb.math("MAXIMUM", worn, nb.math("MULTIPLY", fw, fr["amount"]), clamp=True)
    sub = rec["substrate"]
    col = nb.mix(worn, col, C.hex_to_linear(sub["hex"]))
    r = nb.mix(worn, r, sub["rough"], kind="FLOAT")
    pe = rec["peel"]
    h = nb.math("ADD", nb.math("MULTIPLY", nb.noise_signed(obj, 1000.0 / pe["noise_mm"], detail=1.0), 0.5 * pe["height_mm"] * 0.001),
                nb.math("MULTIPLY", worn, -sub["step_mm"] * 0.001))
    w = G.weather(nb, rec, col, r, rec["spec"], edge=edge)
    n = nb.bump(nb.math("ADD", nb.math("MULTIPLY", h, w["damp"]), w["height"]))
    p = K.principled(nb, base=w["color"], rough=w["rough"], ior=rec["ior"], spec=w["spec"], normal=n)
    _out(nb, p.outputs[0])


def build_lens(mat, rec):
    nb = K.new_tree(mat)
    p = K.principled(nb, base=C.hex_to_linear(rec["albedo_hex"]), rough=rec["rough"], ior=rec["ior"],
                     transmission=rec.get("transmission", 0.0), coat=rec.get("coat", 0.0), coat_rough=0.03,
                     coat_ior=1.5)
    _out(nb, p.outputs[0])


def build_decal(mat, rec):
    nb = K.new_tree(mat)
    mk = rec["mask"]
    u0, v0, u1, v1 = mk["box"]
    uv = nb.vmath("ADD", nb.vmath("MULTIPLY", nb.uv(mk["uv"]), (u1 - u0, v1 - v0, 0.0)), (u0, v0, 0.0))
    nd = K.image_node(nb, K.texture(mk["image"], "mask"), uv)
    nd.extension = "CLIP"
    m = nb.smoothstep(_bw(nb, nd.outputs["Color"]), mk["threshold"][0], mk["threshold"][1])
    ed = rec["edge"]
    edge = G.edge_mask(nb, ed)
    r = nb.math("MULTIPLY_ADD", _noise01(nb, 8.0), 0.08, rec["rough"] - 0.04)
    we = nb.group("MG.Weather.Edge", {"Base Color": rec["f0"], "Base Roughness": r, "Base Metallic": 1.0,
                                      "Worn Color": ed["f0"], "Worn Roughness": ed["rough"], "Worn Metallic": 1.0,
                                      "Edge": edge, "Amount": ed["amount"]})
    rec_g = dict(rec, dust={"amount": 0.0})
    wm = G.weather(nb, rec_g, K.sock(we, "Color", out=True), K.sock(we, "Roughness", out=True), 0.5)
    metal = K.principled(nb, base=wm["color"], metal=1.0, rough=wm["rough"]).outputs[0]
    wk = G.weather(nb, rec_g, C.hex_to_linear(rec["mark"]["hex"]), rec["mark"]["rough"], 0.5)
    mark = K.principled(nb, base=wk["color"], rough=wk["rough"], ior=1.5, spec=0.5).outputs[0]
    mx = nb.node("ShaderNodeMixShader")
    nb.set(mx, 0, m)
    nb.link(metal, mx.inputs[1])
    nb.link(mark, mx.inputs[2])
    shader = mx.outputs[0]
    du = rec.get("dust") or {}
    if du.get("amount", 0.0) > 0.0:
        d = nb.group("MG.Weather.Dust", {"Amount": du["amount"], "Side": G.object_prop(nb, "wear_dust_scale", 1.0),
                                         "Edge": edge})
        shader = dust_over_metal(nb, shader, K.sock(d, "Coverage", out=True))
    _out(nb, shader)


BUILDERS = {"leather": build_leather, "rubber": build_rubber, "midsole": build_midsole, "metal": build_metal,
            "polymer": build_polymer, "painted": build_painted, "lens": build_lens, "decal": build_decal}


# --------------------------------------------------------------------------- self-test

def selftest():
    """The hard recipes build with their groups and maps: tiled maps on hard parts by box projection, the
    leather on UV.Real; no normal map under a box projection; the gunmetal metallic with its dust as a
    dielectric layer; the leather's coat only through MG.Polish and inside §3.1's leather cap."""
    import bpy
    from . import materials as M
    out, made = {}, []
    try:
        for rid in ("Leather.Boot.FullGrain", "Rubber.Outsole.Black", "Rubber.Rand.Black", "EVA.Midsole.BlueGrey",
                    "Metal.Gunmetal", "Polymer.Black.Smooth"):
            m = M.get(rid, "Lib")
            made.append(m)
            nodes = m.node_tree.nodes
            rec = M.recipe(rid)
            imgs = [n for n in nodes if n.bl_idname == "ShaderNodeTexImage"]
            for n in imgs:
                want = "sRGB" if n.image.get("lib_kind") in K.COLOUR_KINDS else "Non-Color"
                assert n.image.colorspace_settings.name == want, (rid, n.image.name)
                assert n.projection != "BOX" or n.image.get("lib_kind") != "normal_gl", (rid, "a box-projected normal map")
            if rec.get("projection") == "box":
                assert imgs and all(n.projection == "BOX" for n in imgs), rid
            groups = {n.node_tree.name for n in nodes if n.bl_idname == "ShaderNodeGroup"}
            assert groups <= set(GROUPS_USED[rec["builder"]]), (rid, groups - set(GROUPS_USED[rec["builder"]]))
            assert "MG.Weather.Dust" in groups, rid
            out[rid] = K.tree_hash(m.node_tree)
        lea = bpy.data.materials[M.material_name("Leather.Boot.FullGrain", "Lib")]
        p = next(n for n in lea.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
        assert p.inputs["Coat Weight"].is_linked and p.inputs["Sheen Weight"].default_value == 0.0
        assert C.LEATHER_BOOT["polish"]["coat"] <= C.CLASS_RULES["leather"]["coat_max"]
        uvs = {n.uv_map for n in lea.node_tree.nodes if n.bl_idname in ("ShaderNodeUVMap", "ShaderNodeNormalMap")}
        assert uvs == {"UV.Real"}, uvs
        gm = bpy.data.materials[M.material_name("Metal.Gunmetal", "Lib")]
        ps = [n for n in gm.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"]
        assert sorted(n.inputs["Metallic"].default_value for n in ps) == [0.0, 1.0], "metal + dielectric dust layer"
        assert any(n.bl_idname == "ShaderNodeMixShader" for n in gm.node_tree.nodes)
        return out
    finally:
        for m in made:
            if m.name in bpy.data.materials and m.users == 0:
                bpy.data.materials.remove(m)
