"""Skin and nail recipes (spec 16 §3.3.1, §4.1; the regional data of spec 01 §3.4 and §5.1-5.3).

`Skin.Foot` lays part 01's regions over MG.Skin.Core in the order of spec 01 §5.1 (dorsum base, sole,
pressure, toes, callus, corn, rub patch, then the vein tint, tendon and crease shading and the nail bed),
adds §5.2's colour variation and builds §5.3's relief as two physical heights (macro and micro, each one
Bump at Distance 1, Strength 1). Masks are read by name with Attribute nodes (vertex groups and point
attributes alike); a mask the mesh lacks reads 0 in Cycles and switches its layer off. Above the ankle seam
the foot's own layers fade out (z 170 -> 120 mm, §5.5). Random-walk scattering all but erases a 0.04 mm
bump, so the furrows, pits and ridge valleys also darken the albedo a little (micro-occlusion) and the
coat follows the whole relief: that is how fine skin texture reads in macro photographs.

Two places where spec 01's recipe table (§5.2-5.3) disagrees with its own data (§3.4) and the data wins
(reality wins). Follicles: a 3D Voronoi cut by the skin shows a dot wherever a feature point lies within the
threshold r of the surface, so dots number 2r/L³ per area; the table's 2200 /m cells with a 0.09 threshold
give about 90 per cm² of dots under 0.08 mm, while 0.91 mm cells with r 0.075 mm give §3.4's 20 per cm² of
pits up to 0.15 mm across. Friction ridges: the Wave scale comes from the 0.45 mm pitch (Blender's BANDS
phase is 20 x the coordinate, so scale = 0.314 / pitch), not the table's 2200, which is a 0.14 mm pitch.

The nail plate is a refracting keratin shell (§3.3.1's IOR 1.5 and coat 0.6; its transmissions 0.55 / 0.70
rendered an opaque white tile and are 0.88 / 0.40 as built, see mat_catalogue). Caustics are off in every
render tier, so shadow rays pass the plate (as §3.3.3 does for the cornea), or the bed under it is unlit. It reads the point attribute `nail_coords` (u across, v from
the proximal fold, w past the bed, all mm) and the object properties `nail_lunula_mm` and `nail_ridge_mm`
that nail_coords() writes from the plate's own mesh, for the lunula, the longitudinal ridges, the hallux
trauma ridge and the grime line under the free edge.
"""
import math

import numpy as np

from . import mat_catalogue as C
from . import mat_core as K

GROUPS_USED = {"skin_foot": ("MG.Skin.Core", "MG.Skin.Micro"), "nail": ()}


def _lin(h):
    return C.hex_to_linear(h)


def build_material(mat, rec, part, overrides):
    {"skin_foot": build_skin_foot, "nail": build_nail}[rec["builder"]](mat, rec)


# --------------------------------------------------------------------------- Skin.Foot

def build_skin_foot(mat, rec):
    R, V, Mi = rec["regions"], rec["variation"], rec["micro"]
    nb = K.new_tree(mat)
    obj = nb.coords("Object")   # metres: the closeup copies and Body.Mesh both sit at the world origin
    _, _, oz = nb.separate(obj)
    fade = nb.map_range(nb.math("MULTIPLY", oz, 1000.0), rec["seam_fade_mm"][0], rec["seam_fade_mm"][1],
                        0.0, 1.0, "SMOOTHSTEP")

    def mask(name, faded=True):
        a = nb.attr(name)
        return nb.math("MULTIPLY", a, fade) if faded else a

    sole, pres, toe = mask("Foot.Sole"), mask("Foot.Pressure"), mask("Foot.ToeRed")
    thin, corn, rub = mask("Foot.DorsumThin"), mask("Foot.Corn.L4"), mask("Foot.Rub.Achilles")
    cal = R["callus"]
    parts = {g: nb.math("MULTIPLY", mask(g), s) for g, s in cal["strength"].items()}
    callus = nb.math("MAXIMUM", nb.math("MAXIMUM", parts["Foot.Callus.Heel"], parts["Foot.Callus.Ball"]),
                     nb.math("MAXIMUM", parts["Foot.Callus.MTP5"], parts["Foot.Callus.Hallux"]))
    callus_s = nb.smoothstep(callus, 0.05, 0.5)
    heel = mask("Foot.Callus.Heel")
    nail_g = nb.attr("toenails")
    bed = nb.smoothstep(nail_g, *R["nail_bed"]["group_edge"])   # the bed faces only, not a pink halo
    vein, tendon, crease = nb.attr("Foot.Vein"), nb.attr("Foot.Tendon"), nb.attr("Foot.Crease")

    # ---- §5.3 E heel crazing (shared by colour and relief). Not every plate edge is a fissure: a noise at
    # three plates opens about half the network, so it reads as dry cracking, not crazy paving
    E = Mi["E_crazing"]
    craze_d = nb.voronoi(obj, 1000.0 / E["cell_mm"], feature="DISTANCE_TO_EDGE", randomness=0.9)
    crack = nb.math("SUBTRACT", 1.0, nb.smoothstep(craze_d, 0.0, E["crack"]))
    opened = nb.smoothstep(nb.noise(obj, 1000.0 / (3.0 * E["cell_mm"]), detail=2.0), 0.47, 0.56)
    crack = nb.math("MULTIPLY", nb.math("MULTIPLY", crack, opened), heel)

    # ---- micro relief first: its grooves and pits also shade the colour (the cavity term below)
    B, Cf, D = Mi["B_lines"], Mi["C_follicles"], Mi["D_ridges"]
    not_sole = nb.math("SUBTRACT", 1.0, sole)
    micro = nb.group("MG.Skin.Micro", {
        "Vector": obj, "Line Cell mm": B["cell_mm"], "Line Width mm": B["width"] * B["cell_mm"],
        "Line Depth mm": B["depth_mm"], "Line Mask": not_sole,
        "Pit Cell mm": Cf["cell_mm"], "Pit Threshold": Cf["threshold"], "Pit Depth mm": Cf["depth_mm"], "Pit Mask": thin,
        "Ridge Pitch mm": D["pitch_mm"], "Ridge Depth mm": D["depth_mm"], "Ridge Distortion": D["distortion"],
        "Ridge Distortion mm": D["distortion_mm"], "Ridge Mask": sole})
    toe_lines = nb.group("MG.Skin.Micro", {
        "Vector": obj, "Line Cell mm": B["cell_toes_mm"], "Line Width mm": B["width"] * B["cell_toes_mm"],
        "Line Depth mm": B["depth_mm"], "Line Mask": not_sole})
    lines = nb.mix(toe, K.sock(micro, "Lines", out=True), K.sock(toe_lines, "Lines", out=True), kind="FLOAT")
    pits, ridges = K.sock(micro, "Pits", out=True), K.sock(micro, "Ridges", out=True)
    # Under random-walk scattering a 0.04 mm bump all but vanishes (the light leaves millimetres from where
    # it entered), yet furrows and pits read in real skin: they are darker inside (micro-occlusion) and break
    # the oil film's sheen. So depth also darkens the albedo, by up to `cavity` (E), and the coat follows it.
    cav = rec["cavity"]
    cavity = nb.math("ADD", nb.math("DIVIDE", lines, -B["depth_mm"] / 1000.0),
                     nb.math("DIVIDE", pits, -Cf["depth_mm"] / 1000.0), clamp=True)
    valley = nb.math("DIVIDE", ridges, -D["depth_mm"] / 2000.0, clamp=True)
    shade = nb.math("SUBTRACT", 1.0, nb.math("ADD", nb.math("MULTIPLY", cavity, cav["lines"]),
                                             nb.math("MULTIPLY", valley, cav["ridges"])))

    # ---- colour (§5.1 cascade, §5.2 variation)
    d = R["dorsum"]
    c = _lin(d["hex"])
    c = nb.mix(sole, c, _lin(R["sole"]["hex"]))
    c = nb.mix(nb.math("MULTIPLY", pres, R["pressure"]["share"]), c, _lin(R["pressure"]["hex"]))
    c = nb.mix(nb.math("MULTIPLY", toe, R["toes"]["share"]), c, _lin(R["toes"]["hex"]))
    core = nb.mix(nb.math("MINIMUM", nb.math("MULTIPLY", parts["Foot.Callus.Hallux"], 2.0), 1.0),
                  _lin(cal["hex"]), _lin(cal["hallux_hex"]))
    core = nb.mix(nb.smoothstep(callus, 0.35, 0.85), _lin(cal["edge_hex"]), core)   # paler core, darker rim
    dry = R["dry"]
    dry_n = nb.math("MULTIPLY", nb.smoothstep(nb.noise_signed(obj, dry["noise_per_m"], detail=3.0), -0.3, 0.8),
                    dry["share"])
    core = nb.mix(dry_n, core, _lin(dry["hex"]))
    core = nb.mix(crack, core, _lin(cal["fissure_hex"]))
    c = nb.mix(callus_s, c, core)
    co = R["corn"]
    corn_col = nb.mix(nb.smoothstep(corn, 0.5, 0.9), _lin(co["ring_hex"]), _lin(co["hex"]))
    corn_s = nb.smoothstep(corn, 0.1, 0.4)
    c = nb.mix(corn_s, c, corn_col)
    c = nb.mix(nb.math("MULTIPLY", rub, R["rub"]["share"]), c, _lin(R["rub"]["hex"]))
    c = nb.mix(nb.math("MULTIPLY", vein, R["vein"]["share"]), c, _lin(R["vein"]["hex"]))
    c = nb.mix(nb.math("MULTIPLY", tendon, R["tendon"]["lighten"]), c, c, blend="ADD")   # +3 % on the crest
    c = nb.mix(crease, c, nb.mix(1.0, c, (R["crease"]["darken"],) * 3, blend="MULTIPLY"))
    c = nb.mix(bed, c, _lin(R["nail_bed"]["hex"]))
    blotch = nb.noise_signed(obj, V["blotch_per_m"], detail=3.0)   # about -1..+1 (mat_core.NOISE_BAND)
    mottle = nb.noise_signed(obj, V["mottle_per_m"], detail=2.0)
    value = nb.math("ADD", 1.0, nb.math("ADD", nb.math("MULTIPLY", blotch, V["blotch_value"]),
                                        nb.math("MULTIPLY", mottle, V["mottle_value"])))
    sat = nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", blotch, V["blotch_sat"]))   # redder in the valleys
    hsv = nb.node("ShaderNodeHueSaturation", inputs={"Hue": 0.5, "Saturation": sat, "Value": value, "Fac": 1.0,
                                                    "Color": c})
    c = hsv.outputs["Color"]
    fol = nb.voronoi(obj, 1000.0 / V["follicle_cell_mm"], feature="F1", randomness=1.0)
    dot = nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, nb.smoothstep(fol, 0.0, V["follicle_threshold"])), thin)
    tint = (1.0 - V["follicle_darken"]) * (1.0 + V["follicle_redden"]), 1.0 - V["follicle_darken"], 1.0 - V["follicle_darken"]
    c = nb.mix(dot, c, nb.mix(1.0, c, tint, blend="MULTIPLY"))
    c = nb.vmath("SCALE", c, scale=shade)

    # ---- roughness (furrows a little rougher: the oil film breaks there)
    r = nb.math("ADD", d["rough"], nb.math("MULTIPLY", nb.noise_signed(obj, 1000.0 / d["rough_noise_mm"]), d["rough_var"]))
    r = nb.math("ADD", r, nb.math("MULTIPLY", cavity, cav["rough"]))
    r = nb.mix(sole, r, R["sole"]["rough"], kind="FLOAT")
    r = nb.mix(toe, r, R["toes"]["rough"], kind="FLOAT")
    r = nb.mix(callus_s, r, cal["rough"], kind="FLOAT")
    r = nb.mix(corn_s, r, co["rough"], kind="FLOAT")
    r = nb.mix(rub, r, R["rub"]["rough"], kind="FLOAT")
    r = nb.math("ADD", r, nb.math("MULTIPLY", crease, R["crease"]["rough_add"]), clamp=True)

    # ---- subsurface: radius by region, scale by the part's Foot.SSSScale (0 means "not given": then the
    # toe mask's 0.65, so toes never glow more than spec 01 §4.6 allows)
    thick = nb.math("MAXIMUM", sole, callus_s)
    rad = nb.mix(thick, d["sss_radius"], R["sole"]["sss_radius"], kind="VECTOR")
    rad = nb.vmath("SCALE", rad, scale=nb.math("ADD", 1.0, nb.math("MULTIPLY", vein, R["vein"]["sss_radius_factor"] - 1.0)))
    sss_attr = nb.attr("Foot.SSSScale")
    given = nb.math("GREATER_THAN", sss_attr, 1e-4)
    factor = nb.mix(given, nb.mix(toe, 1.0, R["toes"]["sss_factor"], kind="FLOAT"), sss_attr, kind="FLOAT")
    s = nb.math("MULTIPLY", d["sss_scale"], factor)
    s = nb.mix(sole, s, R["sole"]["sss_scale"], kind="FLOAT")
    s = nb.mix(callus_s, s, cal["sss_scale"], kind="FLOAT")
    s = nb.mix(bed, s, R["nail_bed"]["sss_scale"], kind="FLOAT")

    # ---- coat (skin oil on the dorsum and toes; none on the sole or callus)
    coat = nb.mix(toe, d["coat"], R["toes"]["coat"], kind="FLOAT")
    coat = nb.math("MULTIPLY", coat, nb.math("SUBTRACT", 1.0, nb.math("MAXIMUM", sole, callus_s)))
    coat_r = nb.mix(toe, d["coat_rough"], R["toes"]["coat_rough"], kind="FLOAT")

    # ---- relief (§5.3) in metres: macro (A, E-H) and micro (B-D, I)
    A = Mi["A_undulation"]
    h1 = nb.math("MULTIPLY", nb.noise_signed(obj, A["per_m"], detail=2.0), A["height_mm"] / 2000.0)
    h1 = nb.math("ADD", h1, nb.math("MULTIPLY", crack, -E["depth_mm"] / 1000.0))
    ten = nb.map_range(tendon, 0.0, 1.0, 0.0, 1.0, "SMOOTHERSTEP")
    h1 = nb.math("ADD", h1, nb.math("MULTIPLY", ten, Mi["F_tendon_mm"] / 1000.0))
    h1 = nb.math("ADD", h1, nb.math("MULTIPLY", vein, Mi["G_vein_mm"] / 1000.0))
    h1 = nb.math("ADD", h1, nb.math("MULTIPLY", crease, -Mi["H_crease_mm"] / 1000.0))
    h2 = nb.math("ADD", nb.math("SUBTRACT", K.sock(micro, "Height", out=True), K.sock(micro, "Lines", out=True)), lines)
    I = Mi["I_toe_wrinkles"]
    wr = nb.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y", wave_profile="SIN",
                 inputs={"Vector": obj, "Scale": (2.0 * math.pi / 20.0) / (I["period_mm"] / 1000.0),
                         "Distortion": 1.0, "Detail": 1.0, "Detail Scale": 0.2})
    wrinkle = nb.math("MULTIPLY", nb.math("SUBTRACT", wr.outputs["Fac"], 0.5),
                      nb.math("MULTIPLY", nb.math("MULTIPLY", crease, toe), I["depth_mm"] / 1000.0))
    h2 = nb.math("ADD", h2, wrinkle)
    n1 = nb.bump(h1)
    n2 = nb.bump(h2, normal=n1)

    core_g = nb.group("MG.Skin.Core", {"Base Color": c, "Roughness": r, "SSS Scale": s, "SSS Radius": rad,
                                       "Coat Weight": coat, "Coat Roughness": coat_r, "Normal": n2, "Coat Normal": n2})
    K.output(nb, K.sock(core_g, "BSDF", out=True))


# --------------------------------------------------------------------------- Nail.Plate / Nail.FreeEdge

def build_nail(mat, rec):
    nb = K.new_tree(mat)
    u, v, w = nb.separate(nb.attr("nail_coords", out="Vector"))
    lun_mm = nb.attr("nail_lunula_mm", kind="OBJECT")
    half = nb.math("MAXIMUM", nb.attr("nail_half_mm", kind="OBJECT"), 0.1)
    ridge_at = nb.attr("nail_ridge_mm", kind="OBJECT")
    base, trans = _lin(rec["albedo_hex"]), rec["transmission"]
    col, tr = base, trans
    if rec["part"] == "plate":
        # the lunula: a pale crescent from the proximal fold, its distal edge an arc across the nail
        across = nb.math("DIVIDE", u, half)
        arc = nb.math("SQRT", nb.math("MAXIMUM", nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", across, across)), 0.0))
        edge = nb.math("MULTIPLY", lun_mm, arc)
        lun = nb.math("MULTIPLY", nb.map_range(v, edge, nb.math("SUBTRACT", edge, 0.5), 0.0, 1.0, "SMOOTHSTEP"),
                      nb.math("GREATER_THAN", lun_mm, 0.0))
        col = nb.mix(lun, base, _lin(rec["lunula_hex"]))
        tr = nb.mix(lun, trans, rec["lunula_transmission"], kind="FLOAT")
    else:
        # the grime line under the start of the free edge (spec 01 §3.4: #6d5a4a at 25 %)
        band = nb.math("MULTIPLY", nb.smoothstep(w, -0.1, 0.1),
                       nb.math("SUBTRACT", 1.0, nb.smoothstep(w, rec["grime_band_mm"] * 0.6, rec["grime_band_mm"])))
        col = nb.mix(nb.math("MULTIPLY", band, rec["grime_share"]), base, _lin(rec["grime_hex"]))
    # longitudinal ridges across u (0.25 mm pitch, up to 0.01 mm), each its own strength along its length (a
    # pure sine read as corduroy in a glossy highlight); the trauma ridge across v
    phase = nb.math("ADD", nb.math("MULTIPLY", u, 2.0 * math.pi / rec["ridge_pitch_mm"]),
                    nb.math("MULTIPLY", nb.noise(nb.coords("Object"), 400.0, detail=1.0), 3.0))
    per_ridge = nb.combine(nb.math("MULTIPLY", u, 2.8 / rec["ridge_pitch_mm"]), nb.math("MULTIPLY", v, 0.08), 0.0)
    strength = nb.map_range(nb.noise(per_ridge, 1.0, detail=1.0), K.NOISE_BAND[0], K.NOISE_BAND[1], 0.15, 1.0)
    h = nb.math("MULTIPLY", nb.math("MULTIPLY", nb.math("SINE", phase), strength), rec["ridge_depth_mm"] / 2000.0)
    dv = nb.math("DIVIDE", nb.math("SUBTRACT", v, ridge_at), 0.35)
    bump_ridge = nb.math("MULTIPLY", nb.math("EXPONENT", nb.math("MULTIPLY", nb.math("MULTIPLY", dv, dv), -1.0)),
                         nb.math("GREATER_THAN", ridge_at, 0.0))
    h = nb.math("ADD", h, nb.math("MULTIPLY", bump_ridge, rec["trauma_ridge_mm"] / 1000.0))
    n = nb.bump(h)
    p = K.principled(nb, base=col, rough=rec["rough"], ior=rec["ior"], spec=rec["spec"], transmission=tr,
                     coat=rec["coat"], coat_rough=rec["coat_rough"], normal=n, coat_normal=n)
    clear = nb.node("ShaderNodeBsdfTransparent", inputs={"Color": (1.0, 1.0, 1.0)})
    shadow = nb.math("MULTIPLY", nb.node("ShaderNodeLightPath").outputs["Is Shadow Ray"], rec["shadow_transmit"])
    mix = nb.node("ShaderNodeMixShader", inputs={"Fac": shadow})
    nb.link(p.outputs[0], mix.inputs[1])
    nb.link(clear.outputs[0], mix.inputs[2])
    K.output(nb, mix.outputs[0])


def nail_coords(ob, visible_mm, free_edge_mm, lunula_mm=0.0, ridge_mm=0.0, axis=None):
    """Write the attribute the nail recipes read on one plate mesh (object space, mm):
    nail_coords = (u across from the centre line, v from the visible proximal fold, w past the bed's
    distal end), and the object properties nail_lunula_mm, nail_ridge_mm (0 = none) and nail_half_mm.
    `axis` defaults to the plate's `p01_axis` (part 01's toe axis, world). Returns the indices of the
    free-edge faces (w > 0), for assign(..., "Nail.FreeEdge", faces=...)."""
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    P = co.reshape(-1, 3) * 1000.0
    if axis is None:
        axis = ob.get("p01_axis")
        if axis is None:
            raise KeyError(f"{ob.name} has no p01_axis; pass axis=")
    M = np.array(ob.matrix_world)[:3, :3]
    a = np.linalg.solve(M, np.asarray(axis, float))   # the axis in object space
    nrm = np.zeros(3)
    for poly in me.polygons:
        nrm += np.array(poly.normal) * poly.area
    nrm /= max(np.linalg.norm(nrm), 1e-12)
    a = a - (a @ nrm) * nrm
    a /= np.linalg.norm(a)
    b = np.cross(nrm, a)
    t, s = P @ a, P @ b
    tmax = t.max()
    v = t - (tmax - visible_mm)
    w = t - (tmax - free_edge_mm)
    u = s - 0.5 * (s.max() + s.min())
    att = me.attributes.get("nail_coords")
    if att is not None and (att.domain != "POINT" or att.data_type != "FLOAT_VECTOR"):
        me.attributes.remove(att)
        att = None
    if att is None:
        att = me.attributes.new("nail_coords", "FLOAT_VECTOR", "POINT")
    att.data.foreach_set("vector", np.stack([u, v, w], axis=1).astype(np.float32).ravel())
    ob["nail_lunula_mm"], ob["nail_ridge_mm"] = float(lunula_mm), float(ridge_mm)
    ob["nail_half_mm"] = float(0.5 * (s.max() - s.min()))
    me.update()
    free = []
    for poly in me.polygons:
        if np.mean(w[list(poly.vertices)]) > 0.05:
            free.append(poly.index)
    return free


def selftest():
    """nail_coords on a flat 10 x 12 mm plate pointing -Y, and the skin and nail trees' key parts."""
    import bpy
    from . import materials as M
    xs, ys = np.linspace(-0.005, 0.005, 6), np.linspace(-0.012, 0.0, 13)
    V = [(x, y, 0.0) for y in ys for x in xs]
    F = [(j * 6 + i, j * 6 + i + 1, (j + 1) * 6 + i + 1, (j + 1) * 6 + i) for j in range(12) for i in range(5)]
    me = bpy.data.meshes.new("Lib.Test.SelfNail")
    me.from_pydata(V, [], F)
    ob = bpy.data.objects.new("Lib.Test.SelfNail", me)
    try:
        free = nail_coords(ob, visible_mm=12.0, free_edge_mm=1.5, lunula_mm=3.0, axis=(0.0, -1.0, 0.0))
        uvw = np.empty(len(V) * 3, np.float32)
        me.attributes["nail_coords"].data.foreach_get("vector", uvw)
        uvw = uvw.reshape(-1, 3)
        assert abs(uvw[:, 1].min()) < 1e-3 and abs(uvw[:, 1].max() - 12.0) < 1e-3, uvw[:, 1]   # v: fold 0, tip 12
        assert abs(uvw[:, 2].max() - 1.5) < 1e-3 and abs(uvw[:, 0]).max() < 5.0 + 1e-3        # w: tip 1.5; u: +-5
        assert len(free) == 5 and abs(ob["nail_half_mm"] - 5.0) < 1e-3, (len(free), ob["nail_half_mm"])
        skin = M.get("Skin.Foot", "Lib")
        groups = {n.node_tree.name for n in skin.node_tree.nodes if n.bl_idname == "ShaderNodeGroup"}
        assert {"MG.Skin.Core", "MG.Skin.Micro"} <= groups, groups
        plate = M.get("Nail.Plate", "Lib")
        kinds = {n.bl_idname for n in plate.node_tree.nodes}
        assert {"ShaderNodeLightPath", "ShaderNodeBsdfTransparent", "ShaderNodeMixShader"} <= kinds, kinds
        return {"free_faces": len(free), "v_mm": [0.0, 12.0], "skin_groups": sorted(groups)}
    finally:
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
        for rid in ("Skin.Foot", "Nail.Plate"):
            m = bpy.data.materials.get(M.material_name(rid, "Lib"))
            if m is not None and m.users == 0:
                bpy.data.materials.remove(m)
