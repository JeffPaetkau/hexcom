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

# The skin's line network as built (2026-10-12, critic round 3 m5: every skin surface wore one crisp,
# dark-outlined Voronoi crackle, equally sharp on knuckle, shaft and pulp and into the folds: crazed porcelain).
# Real skin's relief is anisotropic and regional: faint on the dorsum and along its tension lines, deeper over
# the joints, nearly gone on the nail folds, absent on the nail bed, and friction ridges instead on the sole
# and pads. The catalogue's B_lines keeps spec 01's cell sizes and its nominal depth (0.04 mm); this is the
# network's shape and its share of that depth by region, read from the masks the recipe already has. It lives
# here until the catalogue carries it (the next LIB_VERSION; this change could not edit mat_catalogue).
LINES = {
    # the foot's tension lines run across it on the dorsum and the toes (spec 16 §4.1: cells stretched 1.6 along
    # the Langer direction); Object space, +X is mediolateral for both feet
    "langer_dir": (1.0, 0.0, 0.0), "stretch": 1.6,
    "warp": 0.35,        # cell edges bent by up to this share of a cell
    "breakup": 0.6,      # each line's depth varies along it between 1 - breakup and 1
    "fwhm_share": 0.22,  # a groove's full width at half depth, as a share of its cell (0.09 mm on the dorsum)
    "fine": (0.45, 0.35),  # a secondary network: cell (share of the primary's), depth (share of the primary's)
    # the share of the nominal depth by region: the dorsum and the toes faint, the joints (Foot.Crease) full,
    # the nail folds nearly none (toenails' soft margin, `fold_mask`), the bed none
    "region": {"dorsum": 0.6, "toes": 0.5, "joints": 1.0, "folds": 0.1},
    "fold_mask": (0.02, 0.4),  # toenails weights read as "a nail fold": its margin, below the bed's group_edge
    "cavity": 0.4,       # the share of cavity.lines the network keeps: it reads by relief and sheen, not outlines
}

# The nail plate's zones as built (2026-10-12, build_nail), from close photographs of real toenails: the cuticle
# along the proximal fold, the lunula (its colour and clarity are the catalogue's lunula_hex and
# lunula_transmission), the body's faint longitudinal streaks, the onychodermal band over the bed's distal end;
# the ridges' variation along the nail. Here until the catalogue carries them (the next LIB_VERSION).
NAIL_ZONES = {
    "cuticle_mm": 0.35, "cuticle_rag_mm": 0.06, "cuticle_hex": "#eadbd2", "cuticle_transmission": 0.3,
    "cuticle_rough": 0.55,
    "lunula_soft_mm": 0.5,
    "band_mm": 0.9, "band_soft_mm": 0.45, "band_wobble_mm": 0.15, "band_hex": "#f2e5da", "band_transmission": 0.5,
    "streak_mm": (0.6, 5.0), "streak_value": 0.05, "streak_transmission": 0.05,
    "ridge_vary_mm": 2.0, "ridge_floor": 0.0,
}


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
    L = dict(LINES, **B.get("network", {}))
    not_sole = nb.math("SUBTRACT", 1.0, sole)
    # the line network's share of its nominal depth by region (LINES): faint on the dorsum and the toes, full
    # over the joints, nearly gone on the nail folds (toenails' soft margin), none on the bed or the sole
    Lr = L["region"]
    share = nb.mix(toe, Lr["dorsum"], Lr["toes"], kind="FLOAT")
    share = nb.mix(nb.smoothstep(crease, 0.0, 0.5), share, Lr["joints"], kind="FLOAT")
    near_nail = nb.smoothstep(nail_g, *L["fold_mask"])
    share = nb.math("MULTIPLY", share, nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", near_nail, 1.0 - Lr["folds"])))
    share = nb.math("MULTIPLY", share, nb.math("SUBTRACT", 1.0, bed))
    line_mask = nb.math("MULTIPLY", not_sole, share, clamp=True)
    fine_cell, fine_depth = L["fine"]

    def network(cell):
        return {"Line Cell mm": cell, "Line Width mm": L["fwhm_share"] * cell, "Line Depth mm": B["depth_mm"],
                "Line Mask": line_mask, "Langer Direction": L["langer_dir"], "Line Stretch": L["stretch"],
                "Line Warp": L["warp"], "Line Breakup": L["breakup"], "Fine Cell mm": fine_cell * cell,
                "Fine Depth mm": fine_depth * B["depth_mm"]}

    # the friction ridges' pattern (2026-10-13): where the mesh carries `Foot.Ridges` (a point attribute: the phase in
    # mm whose level lines the ridges follow, its coverage, its amplitude; whorls or loops on the pulps, arcs on the
    # ball, breaking at the creases), MG.Skin.Micro follows it; a mesh without it reads (0, 0, 0): the diagonal
    # bands at full depth, as before
    rf_phase, rf_cov, rf_amp = nb.separate(nb.attr("Foot.Ridges", out="Vector"))
    ridge_mask = nb.math("MULTIPLY", sole, nb.math("ADD", nb.math("SUBTRACT", 1.0, rf_cov), nb.math("MULTIPLY", rf_cov, rf_amp)),
                         clamp=True)
    micro = nb.group("MG.Skin.Micro", dict(
        network(B["cell_mm"]), **{
            "Vector": obj, "Pit Cell mm": Cf["cell_mm"], "Pit Threshold": Cf["threshold"], "Pit Depth mm": Cf["depth_mm"],
            "Pit Mask": thin, "Ridge Pitch mm": D["pitch_mm"], "Ridge Depth mm": D["depth_mm"],
            "Ridge Distortion": D["distortion"], "Ridge Distortion mm": D["distortion_mm"], "Ridge Mask": ridge_mask,
            "Ridge Field mm": rf_phase, "Ridge Field Weight": rf_cov}))
    toe_lines = nb.group("MG.Skin.Micro", dict(network(B["cell_toes_mm"]), Vector=obj))
    lines = nb.mix(toe, K.sock(micro, "Lines", out=True), K.sock(toe_lines, "Lines", out=True), kind="FLOAT")
    pits, ridges = K.sock(micro, "Pits", out=True), K.sock(micro, "Ridges", out=True)
    # Under random-walk scattering a 0.04 mm bump all but vanishes (the light leaves millimetres from where
    # it entered), yet furrows and pits read in real skin: they are darker inside (micro-occlusion) and break
    # the oil film's sheen. So depth also darkens the albedo, by up to `cavity` (E), and the coat follows it.
    # The line network keeps LINES["cavity"] of it: round 3's full share drew every cell edge as a dark outline.
    cav = rec["cavity"]
    cavity = nb.math("ADD", nb.math("DIVIDE", lines, -B["depth_mm"] / 1000.0 / L["cavity"]),
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
    """The plate and the free edge in zones by the nail's own coordinates (u across, v from the visible
    proximal fold at the centre line, w past the bed's end; mm, nail_coords), as a close photograph of a real
    toenail shows them (2026-10-12, critic round 3 m2, m16, m20: round 3's plate was one milky pink from root to
    edge, its lunula a translucent tint that let the pink through, its free edge clear acrylic):

      plate: the cuticle, a thin pale matte line along the proximal fold (the fold's line rises
      `nail_cuticle_mm` toward the plate's sides); the lunula, an opaque pale crescent whose distal edge is an
      arc over its own half-width (`nail_lunula_half_mm`; the plate's half-width when absent); the body, the
      bed seen through translucent keratin with faint longitudinal streaks; the onychodermal band, a paler,
      less clear band over the bed's last `band_mm`;
      free edge: ivory over air, with the grime line under its start, a little uneven.

    The longitudinal ridges vary in strength along each ridge every `ridge_vary_mm`, down to `ridge_floor`
    (round 3's noise read v x 0.08, so a ridge kept one strength for the nail's whole length; its floor was
    0.15). The zones' values (NAIL_ZONES) live here until the catalogue carries them."""
    Z = dict(NAIL_ZONES, **rec.get("zones", {}))
    nb = K.new_tree(mat)
    u, v, w = nb.separate(nb.attr("nail_coords", out="Vector"))
    lun_mm = nb.attr("nail_lunula_mm", kind="OBJECT")
    half = nb.math("MAXIMUM", nb.attr("nail_half_mm", kind="OBJECT"), 0.1)
    lun_half_p = nb.attr("nail_lunula_half_mm", kind="OBJECT")
    lun_half = nb.mix(nb.math("GREATER_THAN", lun_half_p, 0.0), half, lun_half_p, kind="FLOAT")
    cut_rise = nb.attr("nail_cuticle_mm", kind="OBJECT")
    ridge_at = nb.attr("nail_ridge_mm", kind="OBJECT")
    obj = nb.coords("Object")
    base, trans = _lin(rec["albedo_hex"]), rec["transmission"]
    col, tr, rough = base, trans, rec["rough"]
    if rec["part"] == "plate":
        # faint longitudinal streaks in the keratin: a noise stretched along the nail (narrow across, long
        # along), a few per cent in value and clarity
        sw, sl = Z["streak_mm"]
        streak = nb.noise_signed(nb.combine(nb.math("DIVIDE", u, sw), nb.math("DIVIDE", v, sl), 0.0), 1.0, detail=2.0)
        col = nb.vmath("SCALE", col, scale=nb.math("ADD", 1.0, nb.math("MULTIPLY", streak, Z["streak_value"])))
        tr = nb.math("ADD", tr, nb.math("MULTIPLY", streak, Z["streak_transmission"]))
        # the onychodermal band: the bed's last band_mm, paler and less clear, its proximal edge soft and uneven
        wob = nb.math("MULTIPLY", nb.noise_signed(nb.combine(nb.math("DIVIDE", u, 1.8), 0.0, 0.0), 1.0, detail=1.0),
                      Z["band_wobble_mm"])
        w_b = nb.math("ADD", w, wob)
        band = nb.math("MULTIPLY", nb.smoothstep(w_b, -Z["band_mm"], -Z["band_mm"] + Z["band_soft_mm"]),
                       nb.math("SUBTRACT", 1.0, nb.smoothstep(w, 0.02, 0.12)))
        col = nb.mix(band, col, _lin(Z["band_hex"]))
        tr = nb.mix(band, tr, Z["band_transmission"], kind="FLOAT")
        # the lunula: an opaque pale crescent from under the proximal fold, its distal edge an arc over its own
        # half-width, softened over lunula_soft_mm
        across = nb.math("DIVIDE", u, lun_half)
        arc = nb.math("SQRT", nb.math("MAXIMUM", nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", across, across)), 0.0))
        edge = nb.math("MULTIPLY", lun_mm, arc)
        lun = nb.math("MULTIPLY", nb.map_range(v, edge, nb.math("SUBTRACT", edge, Z["lunula_soft_mm"]), 0.0, 1.0,
                                               "SMOOTHSTEP"),
                      nb.math("GREATER_THAN", lun_mm, 0.0))
        col = nb.mix(lun, col, _lin(rec["lunula_hex"]))
        tr = nb.mix(lun, tr, rec["lunula_transmission"], kind="FLOAT")
        # the cuticle: dead skin lying on the plate along the fold's line (v_fold = rise x (u / half)^2), a thin
        # pale matte band with a ragged distal edge
        v_fold = nb.math("MULTIPLY", cut_rise, nb.math("MULTIPLY", nb.math("DIVIDE", u, half), nb.math("DIVIDE", u, half)))
        rag = nb.math("MULTIPLY", nb.noise_signed(obj, 1000.0 / 0.6, detail=2.0), Z["cuticle_rag_mm"])
        v_rel = nb.math("SUBTRACT", nb.math("ADD", v, rag), v_fold)
        cut = nb.math("SUBTRACT", 1.0, nb.smoothstep(v_rel, Z["cuticle_mm"] * 0.45, Z["cuticle_mm"]))
        col = nb.mix(cut, col, _lin(Z["cuticle_hex"]))
        tr = nb.mix(cut, tr, Z["cuticle_transmission"], kind="FLOAT")
        rough = nb.mix(cut, rough, Z["cuticle_rough"], kind="FLOAT")
    else:
        # the grime line under the start of the free edge (spec 01 §3.4: #6d5a4a at 25 %), a little uneven
        g_mm = nb.math("MULTIPLY", rec["grime_band_mm"],
                       nb.math("ADD", 1.0, nb.math("MULTIPLY", nb.noise_signed(nb.combine(nb.math("DIVIDE", u, 1.2), 0.0, 0.0),
                                                                                   1.0, detail=1.0), 0.35)))
        band = nb.math("MULTIPLY", nb.smoothstep(w, -0.1, 0.1),
                       nb.math("SUBTRACT", 1.0, nb.smoothstep(w, nb.math("MULTIPLY", g_mm, 0.6), g_mm)))
        col = nb.mix(nb.math("MULTIPLY", band, rec["grime_share"]), base, _lin(rec["grime_hex"]))
    # longitudinal ridges across u (0.25 mm pitch, up to ridge_depth), each its own strength along its length,
    # varying every ridge_vary_mm and fading out entirely in places (a pure sine read as corduroy in a glossy
    # highlight); the trauma ridge across v
    phase = nb.math("ADD", nb.math("MULTIPLY", u, 2.0 * math.pi / rec["ridge_pitch_mm"]),
                    nb.math("MULTIPLY", nb.noise(obj, 400.0, detail=1.0), 3.0))
    per_ridge = nb.combine(nb.math("MULTIPLY", u, 2.8 / rec["ridge_pitch_mm"]),
                           nb.math("DIVIDE", v, Z["ridge_vary_mm"]), 0.0)
    strength = nb.map_range(nb.noise(per_ridge, 1.0, detail=1.0), K.NOISE_BAND[0], K.NOISE_BAND[1],
                            Z["ridge_floor"], 1.0, "SMOOTHSTEP")
    h = nb.math("MULTIPLY", nb.math("MULTIPLY", nb.math("SINE", phase), strength), rec["ridge_depth_mm"] / 2000.0)
    dv = nb.math("DIVIDE", nb.math("SUBTRACT", v, ridge_at), 0.35)
    bump_ridge = nb.math("MULTIPLY", nb.math("EXPONENT", nb.math("MULTIPLY", nb.math("MULTIPLY", dv, dv), -1.0)),
                         nb.math("GREATER_THAN", ridge_at, 0.0))
    h = nb.math("ADD", h, nb.math("MULTIPLY", bump_ridge, rec["trauma_ridge_mm"] / 1000.0))
    n = nb.bump(h)
    p = K.principled(nb, base=col, rough=rough, ior=rec["ior"], spec=rec["spec"],
                     transmission=nb.math("MINIMUM", nb.math("MAXIMUM", tr, 0.0), 1.0) if K.is_socket(tr) else tr,
                     coat=rec["coat"], coat_rough=rec["coat_rough"], normal=n, coat_normal=n)
    clear = nb.node("ShaderNodeBsdfTransparent", inputs={"Color": (1.0, 1.0, 1.0)})
    shadow = nb.math("MULTIPLY", nb.node("ShaderNodeLightPath").outputs["Is Shadow Ray"], rec["shadow_transmit"])
    mix = nb.node("ShaderNodeMixShader", inputs={"Fac": shadow})
    nb.link(p.outputs[0], mix.inputs[1])
    nb.link(clear.outputs[0], mix.inputs[2])
    K.output(nb, mix.outputs[0])


def nail_coords(ob, visible_mm, free_edge_mm, lunula_mm=0.0, ridge_mm=0.0, axis=None, lunula_half_mm=0.0,
                cuticle_mm=0.0):
    """Write the attribute the nail recipes read on one plate mesh (object space, mm):
    nail_coords = (u across from the centre line, v from the visible proximal fold, w past the bed's
    distal end), and the object properties nail_lunula_mm, nail_ridge_mm (0 = none) and nail_half_mm.
    `axis` defaults to the plate's `p01_axis` (part 01's toe axis, world). Returns the indices of the
    free-edge faces (w > 0), for assign(..., "Nail.FreeEdge", faces=...).

    Optional (2026-10-12): nail_lunula_half_mm, the lunula's own half-width (0: the plate's), and
    nail_cuticle_mm, how far the proximal fold's line rises distally at the plate's sides (0: straight across),
    which the plate's lunula and cuticle zones read (build_nail)."""
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
    ob["nail_lunula_half_mm"], ob["nail_cuticle_mm"] = float(lunula_half_mm), float(cuticle_mm)
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
        assert ob["nail_lunula_half_mm"] == 0.0 and ob["nail_cuticle_mm"] == 0.0   # optional, absent = 0
        nail_coords(ob, visible_mm=12.0, free_edge_mm=1.5, lunula_mm=3.0, axis=(0.0, -1.0, 0.0), lunula_half_mm=3.5,
                    cuticle_mm=1.2)
        assert abs(ob["nail_lunula_half_mm"] - 3.5) < 1e-6 and abs(ob["nail_cuticle_mm"] - 1.2) < 1e-6
        skin = M.get("Skin.Foot", "Lib")
        groups = {n.node_tree.name for n in skin.node_tree.nodes if n.bl_idname == "ShaderNodeGroup"}
        assert {"MG.Skin.Core", "MG.Skin.Micro"} <= groups, groups
        # the line network by region (LINES): every MG.Skin.Micro carries the Langer stretch and a fine network,
        # and its Line Mask is driven (the regional share), never a constant
        micros = [n for n in skin.node_tree.nodes if n.bl_idname == "ShaderNodeGroup" and n.node_tree.name == "MG.Skin.Micro"]
        for n in micros:
            assert abs(n.inputs["Line Stretch"].default_value - LINES["stretch"]) < 1e-6
            assert n.inputs["Line Mask"].is_linked and n.inputs["Fine Depth mm"].default_value > 0.0
        reads = {n.attribute_name for n in skin.node_tree.nodes if n.bl_idname == "ShaderNodeAttribute"}
        assert {"toenails", "Foot.Crease", "Foot.ToeRed", "Foot.Sole", "Foot.Ridges"} <= reads, reads
        # the friction ridges follow the mesh's ridge field where it has one (2026-10-13)
        ridged = [n for n in micros if n.inputs["Ridge Field Weight"].is_linked]
        assert len(ridged) == 1 and ridged[0].inputs["Ridge Mask"].is_linked, len(ridged)
        plate = M.get("Nail.Plate", "Lib")
        kinds = {n.bl_idname for n in plate.node_tree.nodes}
        assert {"ShaderNodeLightPath", "ShaderNodeBsdfTransparent", "ShaderNodeMixShader"} <= kinds, kinds
        # the plate's zones read the lunula's own half-width and the fold's line (2026-10-12)
        props = {n.attribute_name for n in plate.node_tree.nodes if n.bl_idname == "ShaderNodeAttribute"
                 and n.attribute_type == "OBJECT"}
        assert {"nail_lunula_mm", "nail_lunula_half_mm", "nail_cuticle_mm", "nail_half_mm"} <= props, props
        return {"free_faces": len(free), "v_mm": [0.0, 12.0], "skin_groups": sorted(groups),
                "micro_nodes": len(micros), "plate_props": sorted(props)}
    finally:
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
        for rid in ("Skin.Foot", "Nail.Plate"):
            m = bpy.data.materials.get(M.material_name(rid, "Lib"))
            if m is not None and m.users == 0:
                bpy.data.materials.remove(m)
