"""Materials and the look-dev scene for the trial's region: spec 16's recipes put on the dense skin and the
plates as part 01's materials stage is to call them (the same calls as scripts/eval/lookdev_p01.py), with
lookdev_p01's stand-in masks for the regional layers part 01 has not published yet.

The skin recipe reads Object coordinates in metres and the masks as attributes, so the dense copy keeps the
world transform and its interpolated groups; `toenails` is rewritten by a method that moves the nail beds,
or the bed's pink lands where the old bed was.
"""
import math

import numpy as np

# Round 4 (critic round 3 m2: no lunula seen; round 3's 2.3 mm crescent was a translucent tint, transmission
# 0.8, that let the pink bed through). Spec 01 §3.3 gives the hallux a 3.5 mm lunula and toe 2 a faint one; on
# the trial's plates 3.5 mm read as a white band (a manicure, round 1). An opaque pale crescent (PLATE_OVERRIDES'
# lunula_transmission) about 2 mm deep at the centre past the fold, fading over the recipe's last 0.4 mm.
LUNULA_MM = {1: 2.4, 2: 0.6}
# The lunula's own half-width (the recipe draws its distal edge as lunula_mm x sqrt(1 - (u / half)^2)): a
# crescent over the middle of the root, as on a real big toe, not an arc edge to edge (round 1, m6)
LUNULA_HALF_MM = {1: 6.0, 2: 3.2}
# Recipe overrides for the trial's plates (the catalogue's values are spec 16's; the zones are the library's
# NAIL_ZONES). Round 4 (critic round 3 m2, m16, m20: a milky, glassy plate, acrylic free edges):
#  * the plate satin, not wet: rougher (0.22, so the bed is seen softened through it and the highlight is one
#    broad band) with a thin coat (0.25, rough 0.3); clear enough to show the pink bed (0.9), its haze a little
#    pink; its underside over the bed is open (bonded to the bed: detail.Nail.plate_mesh, `open_bed`);
#  * the lunula an opaque pale crescent (transmission 0.22), a little pink, not a white band;
#  * the ridges 0.0012 mm, their strength varying along each ridge (the recipe's ridge_vary_mm); at 0.002 they
#    still combed the satin highlight into streaks.
PLATE_OVERRIDES = {"ridge_depth_mm": 0.0012, "transmission": 0.9, "rough": 0.22, "coat": 0.25, "coat_rough": 0.3,
                   "albedo_hex": "#ecdcd3", "lunula_hex": "#efe5e1", "lunula_transmission": 0.22}
# the free edge over air: ivory and nearly opaque (keratin with air under it scatters), matte at the cut
FREE_EDGE_OVERRIDES = {"albedo_hex": "#ebdfca", "transmission": 0.15, "rough": 0.42, "coat": 0.12,
                       "coat_rough": 0.35, "ridge_depth_mm": 0.0012}
# The bed seen through the plate: the skin recipe fades its line network and cavity shading there itself now
# (spec 16 Skin.Foot, LINES); the trial only lowers the bed's macro undulation, which a plate shows.
BED_OVERRIDES = {"micro__A_undulation__height_mm": 0.1}

# Round 5 (critic round 4 m2, m3, m15, m17, m20, m24; detail.py `continuous`): the hallux's and toe 2's plates
# are the skin's own surface, shaded as nail where the fields Hires.NailA / NailB / NailC say (s < 0 inside the
# visible outline, w < 0 over the bed). One unpolished toenail over its bed, as close photographs show it: a
# pink-beige a little lighter than the toe, a satin sheen broken by faint longitudinal ridges, the lunula a
# dull milky crescent with a soft border, half under the fold (faint on toe 2), the cuticle the fold's skin
# running a fraction of a millimetre onto the plate with a ragged edge, a narrow pink-brown onychodermal band
# before the free edge (round 4's was paler than the plate: the white stripe), a faint yellow-grey cast
NAIL_LOOK = {
    "body_hex": "#d3a596", "root_hex": "#d6ab9e", "root_mm": 3.0, "lunula_hex": "#ebe0da", "lunula_soft_mm": 0.9,
    "band_hex": "#b98073", "band_mm": 0.55, "band_soft_mm": 0.25, "band_wobble_mm": 0.16, "band_share": 0.75,
    "yellow_hex": "#d6bc9c", "yellow_share": 0.12,
    "streak_mm": (0.7, 6.0), "streak_value": 0.035,
    "rough": 0.34, "rough_var": 0.06, "spec": 0.5, "ior": 1.5, "coat": 0.3, "coat_rough": 0.22,
    "sss_radius": (1.0, 0.4, 0.25), "sss_scale": 0.0012,
    "ridge_pitch_mm": 0.32, "ridge_mm": 0.0012, "ridge_vary_mm": 2.5,
    "edge_soft_mm": 0.035,
    "cuticle_mm": 0.35, "cuticle_share": 0.65, "cuticle_rag_mm": 0.09,
    # the contact line where a fold tucks against the plate (_contact_line): centred just inside the outline
    "line_centre_mm": -0.02, "line_half_mm": 0.07, "line_dark": 0.35,
}
# the free edge over air (detail.free_edge_mesh): keratin a little opaque, faintly yellow-grey, uneven, its
# start (over the bed's end) the band's colour, so the plate runs on into it; a trace of grime seen through
# it over the distal groove
FREE_EDGE_LOOK = {
    "hex": "#c6b8a2", "hex2": "#b8a991", "var_mm": 0.9, "band_hex": "#b98073", "grime_hex": "#857262",
    "grime_mm": (0.05, 0.35), "grime_share": 0.3, "rough": 0.38, "coat": 0.15, "coat_rough": 0.3,
    "sss": 0.2, "sss_radius": (1.0, 0.85, 0.6), "sss_scale": 0.0004,
}
# Round 5 (critic round 4 m26): spec 01 §3.4's colour zones the first-pass skin lacked, from Hires.Tint
# (method_fields.tint_masks): capillary redness on the knuckles and toe tips, slightly darker creases, a faint
# blue-grey cast (#a89a95 at about 10 %) over the hallux's dorsum
TINT = {"cap_hex": "#b4645a", "cap_share": 0.30, "cool_hex": "#a89a95", "cool_share": 0.12, "crease_dark": 0.10}
# spec 01 §3.4 / spec 16 Hair.Body (#3a2a1e root -> #5a4030 tip): dark brown terminal hair, by melanin
HAIR_LOOK = {"melanin": 0.82, "redness": 0.45, "roughness": 0.32, "radial": 0.35, "random_rough": 0.15,
             "random_color": 0.12, "coat": 0.0, "ior": 1.55}


def dress_skin(skin, standin=True):
    """Skin.Foot on every face of the dense copy; the stand-in masks where part 01 has none; on the new nail
    beds (the face attribute Hires.Bed, method_fields.finish) the recipe with BED_OVERRIDES. Round 5: with the
    plates on the skin (Hires.NailA present) the material is the trial's copy of the recipe with the nail
    mixed in (nail_on_skin) and spec 01 §3.4's tints (tint_skin)."""
    from lib import materials as M
    M.ensure_groups()
    if standin:
        from eval import lookdev_p01 as LP
        LP.standin_masks([skin])
    skin.data.materials.clear()
    mat = M.assign(skin, "Skin.Foot", part="Body")
    att = skin.data.attributes.get("Hires.Bed")
    if att is not None and att.domain == "FACE" and skin.data.attributes.get("Hires.NailA") is None:
        M.assign(skin, "Skin.Foot", part="HiresNailBed", faces="Hires.Bed", **BED_OVERRIDES)
    if skin.data.attributes.get("Hires.NailA") is None and skin.data.attributes.get("Hires.Tint") is None:
        return
    # the trial's own copy (the library's material is shared and cached by its hash)
    own = mat.copy()
    own.name = "Hires.Mat.Skin.Foot"
    skin.data.materials[0] = own
    tint_skin(own, tint=skin.data.attributes.get("Hires.Tint") is not None,
              nail=skin.data.attributes.get("Hires.NailA") is not None)
    if skin.data.attributes.get("Hires.NailA") is not None:
        nail_on_skin(own)


def _core(mat):
    return next(n for n in mat.node_tree.nodes if n.bl_idname == "ShaderNodeGroup"
                and n.node_tree is not None and n.node_tree.name == "MG.Skin.Core")


def _contact_line(nb, s, w):
    """The thin shadowed line where a fold's skin tucks against the plate (round 5): drawn from the
    interpolated distance s, so it stays smooth between the vertices, which a geometric crease that narrow
    cannot (it zigzagged across the mesh grid); only beside the bed (w < 0: the outline runs on, open, down
    the toe past the free edge). 1 on the line, 0 away from it."""
    N = NAIL_LOOK
    d = nb.math("ABSOLUTE", nb.math("SUBTRACT", s, N["line_centre_mm"]))
    line = nb.math("SUBTRACT", 1.0, nb.smoothstep(d, 0.25 * N["line_half_mm"], N["line_half_mm"]))
    return nb.math("MULTIPLY", line, nb.math("SUBTRACT", 1.0, nb.smoothstep(w, -0.6, -0.1)))


def tint_skin(mat, tint=True, nail=False):
    """Spec 01 §3.4's colour zones on the skin's base colour, from Hires.Tint (capillary, cool, crease), and
    the nail folds' contact line (from Hires.NailA)."""
    from lib import mat_catalogue as CAT
    from lib import mat_core as K
    nb = K.NodeBuilder(mat.node_tree)
    core = _core(mat)
    sock_in = core.inputs["Base Color"]
    c = sock_in.links[0].from_socket
    if tint:
        cap, cool, crease = nb.separate(nb.attr("Hires.Tint", out="Vector"))
        c = nb.mix(nb.math("MULTIPLY", cap, TINT["cap_share"], clamp=True), c, CAT.hex_to_linear(TINT["cap_hex"]))
        c = nb.mix(nb.math("MULTIPLY", cool, TINT["cool_share"], clamp=True), c, CAT.hex_to_linear(TINT["cool_hex"]))
        c = nb.vmath("SCALE", c, scale=nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", crease, TINT["crease_dark"]), clamp=True))
    if nail:
        s, _, _ = nb.separate(nb.attr("Hires.NailA", out="Vector"))
        _, _, w = nb.separate(nb.attr("Hires.NailB", out="Vector"))
        line = _contact_line(nb, s, w)
        c = nb.vmath("SCALE", c, scale=nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", line, NAIL_LOOK["line_dark"])))
    nb.link(c, sock_in)


def nail_on_skin(mat):
    """The plate shaded on the skin (round 5): a Principled nail mixed over the skin's own BSDF where the
    fields say the skin is the plate's top. The mask is computed here from the interpolated distance s (a
    linear interpolation of a smooth field keeps the outline smooth between the 0.17 mm vertices)."""
    from lib import mat_catalogue as CAT
    from lib import mat_core as K
    N = NAIL_LOOK
    lin = CAT.hex_to_linear
    nb = K.NodeBuilder(mat.node_tree)
    out = next(n for n in mat.node_tree.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
    skin_bsdf = out.inputs["Surface"].links[0].from_socket
    s, p, lun = nb.separate(nb.attr("Hires.NailA", out="Vector"))
    x, v, w = nb.separate(nb.attr("Hires.NailB", out="Vector"))
    lun_k, _, _ = nb.separate(nb.attr("Hires.NailC", out="Vector"))
    obj = nb.coords("Object")
    soft = N["edge_soft_mm"]
    inside = nb.math("SUBTRACT", 1.0, nb.smoothstep(s, -soft, soft))
    on_bed = nb.math("SUBTRACT", 1.0, nb.smoothstep(w, 0.0, 0.1))
    # the cuticle: the proximal fold's skin running onto the plate, its distal edge ragged
    rag = nb.math("MULTIPLY", nb.noise_signed(obj, 1000.0 / 0.45, detail=2.0), N["cuticle_rag_mm"])
    depth_in = nb.math("ADD", nb.math("MULTIPLY", s, -1.0), rag)
    cut = nb.math("MULTIPLY", p, nb.math("SUBTRACT", 1.0, nb.smoothstep(depth_in, 0.35 * N["cuticle_mm"], N["cuticle_mm"])))
    mask = nb.math("MULTIPLY", nb.math("MULTIPLY", inside, on_bed),
                   nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", cut, N["cuticle_share"])), clamp=True)
    # colour: the body, paler toward the root, faint longitudinal streaks, the lunula, the band, a yellow cast
    col = nb.mix(nb.math("SUBTRACT", 1.0, nb.smoothstep(v, 0.0, N["root_mm"])), lin(N["body_hex"]), lin(N["root_hex"]))
    sw, sl = N["streak_mm"]
    streak = nb.noise_signed(nb.combine(nb.math("DIVIDE", x, sw), nb.math("DIVIDE", v, sl), 0.0), 1.0, detail=2.0)
    col = nb.vmath("SCALE", col, scale=nb.math("ADD", 1.0, nb.math("MULTIPLY", streak, N["streak_value"])))
    lw = nb.math("MULTIPLY", lun_k, nb.math("SUBTRACT", 1.0, nb.smoothstep(lun, -N["lunula_soft_mm"], 0.15)))
    col = nb.mix(lw, col, lin(N["lunula_hex"]))
    wob = nb.math("MULTIPLY", nb.noise_signed(nb.combine(nb.math("DIVIDE", x, 1.6), 0.0, 0.0), 1.0, detail=1.0),
                  N["band_wobble_mm"])
    wb = nb.math("ADD", w, wob)
    band = nb.math("MULTIPLY", nb.smoothstep(wb, -N["band_mm"], -N["band_mm"] + N["band_soft_mm"]),
                   nb.math("SUBTRACT", 1.0, nb.smoothstep(w, 0.02, 0.12)))
    col = nb.mix(nb.math("MULTIPLY", band, N["band_share"]), col, lin(N["band_hex"]))
    col = nb.mix(N["yellow_share"], col, lin(N["yellow_hex"]))
    col = nb.vmath("SCALE", col, scale=nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", _contact_line(nb, s, w), N["line_dark"])))
    rough = nb.math("ADD", N["rough"], nb.math("MULTIPLY", streak, N["rough_var"]))
    # longitudinal ridges, each its own strength along its length
    pitch = N["ridge_pitch_mm"]
    phase = nb.math("ADD", nb.math("MULTIPLY", x, 2.0 * math.pi / pitch), nb.math("MULTIPLY", nb.noise(obj, 400.0, detail=1.0), 3.0))
    per = nb.combine(nb.math("MULTIPLY", x, 2.8 / pitch), nb.math("DIVIDE", v, N["ridge_vary_mm"]), 0.0)
    strength = nb.map_range(nb.noise(per, 1.0, detail=1.0), K.NOISE_BAND[0], K.NOISE_BAND[1], 0.0, 1.0, "SMOOTHSTEP")
    h = nb.math("MULTIPLY", nb.math("MULTIPLY", nb.math("SINE", phase), strength), N["ridge_mm"] / 2000.0)
    n = nb.bump(h)
    nail = K.principled(nb, base=col, rough=rough, ior=N["ior"], spec=N["spec"], sss=1.0,
                        sss_radius=N["sss_radius"], sss_scale=N["sss_scale"], sss_ior=1.4,
                        coat=N["coat"], coat_rough=N["coat_rough"], coat_ior=1.5, normal=n, coat_normal=n)
    mix = nb.node("ShaderNodeMixShader", inputs={"Fac": mask})
    nb.link(skin_bsdf, mix.inputs[1])
    nb.link(nail.outputs[0], mix.inputs[2])
    nb.link(mix.outputs[0], out.inputs["Surface"])


def dress_free_edge(nob, uvw_mm):
    """The free-edge sliver (detail.free_edge_mesh): its own Principled, by w (past the bed's end)."""
    import bpy
    from lib import mat_catalogue as CAT
    from lib import mat_core as K
    F = FREE_EDGE_LOOK
    lin = CAT.hex_to_linear
    write_nail_coords(nob, uvw_mm)
    mat = bpy.data.materials.get("Hires.Mat.Nail.FreeEdge") or bpy.data.materials.new("Hires.Mat.Nail.FreeEdge")
    nb = K.new_tree(mat)
    u, v, w = nb.separate(nb.attr("nail_coords", out="Vector"))
    obj = nb.coords("Object")
    var = nb.smoothstep(nb.noise(nb.combine(nb.math("DIVIDE", u, F["var_mm"]), 0.0, 0.0), 1.0, detail=2.0), 0.4, 0.6)
    col = nb.mix(var, lin(F["hex"]), lin(F["hex2"]))
    g0, g1 = F["grime_mm"]
    gw = nb.math("MULTIPLY", nb.smoothstep(w, -0.05, g0), nb.math("SUBTRACT", 1.0, nb.smoothstep(w, g1 * 0.5, g1)))
    gw = nb.math("MULTIPLY", gw, nb.math("ADD", 0.6, nb.math("MULTIPLY", nb.noise(nb.combine(nb.math("DIVIDE", u, 1.2), 0.0, 0.0), 1.0), 0.8)))
    col = nb.mix(nb.math("MULTIPLY", gw, F["grime_share"], clamp=True), col, lin(F["grime_hex"]))
    col = nb.mix(nb.math("SUBTRACT", 1.0, nb.smoothstep(w, -0.12, 0.04)), col, lin(F["band_hex"]))
    p = K.principled(nb, base=col, rough=F["rough"], ior=1.5, spec=0.5, sss=F["sss"], sss_radius=F["sss_radius"],
                     sss_scale=F["sss_scale"], sss_ior=1.45, coat=F["coat"], coat_rough=F["coat_rough"])
    K.output(nb, p.outputs[0])
    nob.data.materials.clear()
    nob.data.materials.append(mat)


def hair_material():
    """Dark brown terminal hair (spec 01 §3.4; spec 16's Hair.Body is planned, not built): Principled Hair by
    melanin."""
    import bpy
    H = HAIR_LOOK
    mat = bpy.data.materials.get("Hires.Mat.Hair.Body") or bpy.data.materials.new("Hires.Mat.Hair.Body")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    hb = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    hb.parametrization = "MELANIN"
    for k, val in (("Melanin", H["melanin"]), ("Melanin Redness", H["redness"]), ("Roughness", H["roughness"]),
                   ("Radial Roughness", H["radial"]), ("Random Roughness", H["random_rough"]),
                   ("Random Color", H["random_color"]), ("Coat", H["coat"]), ("IOR", H["ior"])):
        hb.inputs[k].default_value = val
    info = nt.nodes.new("ShaderNodeHairInfo")
    nt.links.new(info.outputs["Random"], hb.inputs["Random"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(hb.outputs[0], out.inputs["Surface"])
    return mat


def write_nail_coords(nob, uvw_mm, lunula_mm=0.0, ridge_mm=0.0):
    """The attribute and properties the nail recipes read (lib/mat_skin.nail_coords's contract), from a
    plate's own parametrisation: u across from the centre line, v from the visible proximal fold, w past the
    bed's distal end (all mm). Returns each face's mean w."""
    me = nob.data
    uvw = np.asarray(uvw_mm, np.float32)
    att = me.attributes.get("nail_coords")
    if att is not None:
        me.attributes.remove(att)
    att = me.attributes.new("nail_coords", "FLOAT_VECTOR", "POINT")
    att.data.foreach_set("vector", uvw.ravel())
    nob["nail_lunula_mm"], nob["nail_ridge_mm"] = float(lunula_mm), float(ridge_mm)
    u = uvw[:, 0]
    nob["nail_half_mm"] = float(0.5 * (u.max() - u.min()))
    me.update()
    loops = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", loops)
    start = np.empty(len(me.polygons), np.int64)
    total = np.empty(len(me.polygons), np.int64)
    me.polygons.foreach_get("loop_start", start)
    me.polygons.foreach_get("loop_total", total)
    w = uvw[:, 2]
    return np.array([w[loops[start[i]:start[i] + total[i]]].mean() for i in range(len(start))])


def dress_plate(nob, k, uvw_mm=None, ridge_mm=0.0):
    """Nail.Plate with Nail.FreeEdge on its free edge. With uvw_mm the plate's own coordinates are written;
    without, part 01's plate is read the library's way (its p01_axis)."""
    from lib import materials as M
    from parts.p01 import nails
    if nob.get("hires_free_edge"):
        return dress_free_edge(nob, uvw_mm)
    if uvw_mm is None:
        w, vis, fe, thick = nails.PLATES[k]
        free = M.nail_coords(nob, vis, fe, lunula_mm=LUNULA_MM.get(k, 0.0), ridge_mm=ridge_mm)
        over_p, over_f = {}, {}
    else:
        wf = write_nail_coords(nob, uvw_mm, LUNULA_MM.get(k, 0.0), ridge_mm)
        free = np.nonzero(wf > 0.05)[0].tolist()
        nob["nail_lunula_half_mm"] = float(LUNULA_HALF_MM.get(k, 0.0))
        # the proximal fold's line, as the recipe's cuticle zone draws it: rise x (u / nail_half_mm)^2, matched
        # to the geometry's (detail.Nail.cuticle: `cuticle` at the visible edges, half_plan(0) from the centre)
        half, vis0 = float(nob["nail_half_mm"]), float(nob.get("hires_half_vis0", 0.0) or 0.0)
        rise = float(nob.get("hires_cuticle_mm", 0.0))
        nob["nail_cuticle_mm"] = rise * (half / vis0) ** 2 if vis0 > 0 else 0.0
        over_p, over_f = PLATE_OVERRIDES, FREE_EDGE_OVERRIDES
    nob.data.materials.clear()
    M.assign(nob, "Nail.Plate", **over_p)
    M.assign(nob, "Nail.FreeEdge", faces=free, **over_f)
    sol = nob.modifiers.get("Solidify")
    if sol is not None:
        sol.material_offset_rim = 0  # each rim takes its own face's material (as lookdev_p01 does)


def lookdev_scene():
    """Turn the open scene into spec 17's LookDev (cyclorama, the three lights, AgX Base Contrast). Hair
    curves render as 3D tubes (spec 01 §6.1: closeups), not ribbons."""
    import bpy
    from eval import lookdev
    out = lookdev.build(bpy.context.scene)
    bpy.context.scene.cycles_curves.shape = "THICK"
    bpy.context.scene.cycles_curves.subdivisions = 3
    return out
