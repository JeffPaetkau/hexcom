"""Spec 16's catalogue as data (§3, §4.6, §4.10, §5.4), with the colour conversions it is written in.

Pure Python, no bpy: the swatch sheets, texmeasure and the tests read it under system Python too. A
recipe's colours are sRGB-encoded hexes exactly as the spec prints them; hex_to_linear() is the only way
they become scene-linear (§5.6), so nobody types a linear value by eye. Every entry of CATALOGUE is built
by a family module (mat_skin, mat_fabric); every other catalogue ID of §3.3 is listed in PLANNED with its
section, so asking for it fails with "not built yet" rather than "unknown".

Units: millimetres for lengths (the node groups convert), metres for subsurface scales (Blender's own
unit for that socket, and how §3.3.1 states them), colours as hexes or linear triples where §3.4 gives F0.
"""
import math

LIB_VERSION = "16.1"   # bump on any recipe change (§7.4); materials also hash the library's source


# --------------------------------------------------------------------------- colour (§5.6)

def _decode(c):
    """IEC 61966-2-1 decode of one channel in [0, 1]."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _encode(c):
    c = min(max(c, 0.0), 1.0)
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1.0 / 2.4) - 0.055


def hex_to_linear(h):
    """'#b6886f' -> scene-linear (r, g, b)."""
    h = h.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"colour {h!r}: expected six hex digits")
    return tuple(_decode(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def linear_to_hex(rgb):
    """Scene-linear (r, g, b) -> '#rrggbb' (rounded to the nearest 8-bit code)."""
    return "#" + "".join(f"{int(math.floor(_encode(c) * 255.0 + 0.5)):02x}" for c in rgb)


def luminance(rgb):
    """Rec.709 Y of a linear triple."""
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def lift(rgb, share):
    """A colour lifted `share` of the way toward white: §3.1's sheen tint rule (base + 25 %)."""
    return tuple(c + (1.0 - c) * share for c in rgb)


# --------------------------------------------------------------------------- §3.1 class rules

# albedo_y: Rec.709 Y floor and ceiling of the base albedo; rough: roughness band; spec: Specular IOR Level
# band; sheen: (low, high) for the class, sheen_fibre the allowance for thread, loop pile and fleece, and
# sheen_max the hard cap. None means the spec sets no bound.
CLASS_RULES = {
    "textile_black": {"albedo_y": (0.018, 0.040), "rough": (0.60, 0.90), "ior": 1.53, "spec": (0.30, 0.45),
                      "sheen": (0.04, 0.08), "sheen_fibre": 0.10, "sheen_max": 0.12, "sheen_rough": (0.5, 0.6),
                      "sheen_tint_lift": 0.25},
    "textile_coloured": {"albedo_y": (0.020, 0.25), "rough": (0.62, 0.85), "ior": 1.53, "spec": (0.35, 0.45),
                         "sheen": (0.04, 0.08), "sheen_fibre": 0.10, "sheen_max": 0.12, "sheen_rough": (0.5, 0.6),
                         "sheen_tint_lift": 0.25},
    "leather": {"albedo_y": (0.020, 0.06), "rough": (0.35, 0.80), "ior": 1.50, "spec": (0.5, 0.5),
                "sheen": (0.0, 0.04), "sheen_max": 0.04, "coat_max": 0.15},
    "rubber": {"albedo_y": (0.018, 0.030), "rough": (0.45, 0.90), "ior": 1.52, "spec": (0.5, 0.5),
               "sheen": (0.0, 0.06), "sheen_max": 0.06},
    "plastic": {"albedo_y": (0.015, 0.25), "rough": (0.35, 0.60), "ior": (1.48, 1.58), "spec": (0.5, 0.5),
                "sheen": (0.0, 0.0), "sheen_max": 0.0},
    "paint": {"albedo_y": (0.020, 0.85), "rough": (0.50, 0.70), "ior": 1.50, "spec": (0.5, 0.5),
              "sheen": (0.0, 0.0), "sheen_max": 0.0},
    # §3.1 skin: "regional, 0.28 - 0.42". The bound is for dorsal and facial skin: spec 16's own §3.3.1 sole
    # (#d8b798, Y 0.51) and callus (#e0cba8, Y 0.61) lie above it, so lint checks a skin recipe's base albedo
    # only (2026-10-10, as built).
    "skin": {"albedo_y": (0.28, 0.42), "rough": (0.38, 0.72), "ior": 1.40, "spec": (0.5, 0.5),
             "sheen": (0.04, 0.04), "sheen_max": 0.04, "sss_scale": (0.0015, 0.006)},
    "metal": {"albedo_y": None, "rough": (0.15, 0.60), "ior": None, "spec": None, "sheen": (0.0, 0.0),
              "sheen_max": 0.0, "f0_min": 0.05},
    "anodic": {"albedo_y": None, "rough": (0.30, 0.62), "ior": None, "coat_ior": 1.65, "sheen": (0.0, 0.0),
               "sheen_max": 0.0},
    "glass": {"albedo_y": None, "rough": (0.0, 0.30), "ior": (1.336, 1.58), "sheen": (0.0, 0.0), "sheen_max": 0.0},
    # Not in §3.1: nail keratin has no class there; its values come straight from §3.3.1 (library addition).
    "keratin": {"albedo_y": None, "rough": (0.10, 0.30), "ior": 1.50, "spec": (0.5, 0.5), "sheen": (0.0, 0.0),
                "sheen_max": 0.0},
}


# --------------------------------------------------------------------------- §3.2 texture registry

# Measured periods (Hann-windowed FFT of the displacement map at 2048 px) and the tile each map is scaled
# to: tile_mm = periods_per_tile x real feature (§3.2). Statistics of knitted_fleece were measured on this
# workstation (2026-10-10, PIL on the restored 2K maps): the colour map's linear luminance mean and spread
# feed the ±6 % high-pass of the sock, the roughness map's mean the ×0.5 modulation about the recipe value.
TILE_PERIODS = {
    "Fabric063": {"native_mm": 400.0, "period_px": 8.0, "feature": "500D yarn 0.61 mm; 1000D 0.74 mm",
                  "tiles_mm": {"500D": 156.0, "1000D": 190.0}, "maps": {"nor_gl": 0.6, "rough": 0.9, "ao": 0.3}},
    "Fabric061": {"native_mm": 400.0, "period_px": 16.0, "feature": "NYCO warp pair 0.50 mm",
                  "tiles_mm": {"default": 64.0}, "maps": {"nor_gl": 0.25}},
    "Fabric082A": {"native_mm": None, "period_px": 2.5, "feature": "stretch yarn 0.24 mm",
                   "tiles_mm": {"default": 200.0}, "maps": {"nor_gl": 0.4}},
    "cotton_jersey": {"native_mm": 264.0, "period_px": 5.4, "feature": "jersey course 0.69 mm", "directional": True,
                      "tiles_mm": {"default": 264.0, "glove_floor": 115.0}, "maps": {"nor_gl": 0.6, "ao": 0.3}},
    "knitted_fleece": {"native_mm": 266.0, "period_px": 14.2, "period_axis": "u", "directional": True,
                       "feature": "fleece clump and sock stitch 1.6 mm", "tiles_mm": {"default": 230.0},
                       "maps": {"nor_gl": 0.5, "rough": 0.5, "diff_highpass": 0.06},
                       "stats": {"diff_lum_mean": 0.0785, "diff_lum_sd": 0.0331, "rough_mean": 0.6233}},
    "poly_wool_herringbone": {"native_mm": 270.0, "period_px": 18.3, "feature": "herringbone 2.5 mm across",
                              "directional": True,
                              "tiles_mm": {"default": 280.0}, "maps": {"nor_gl": 0.5}},
    "Leather032": {"native_mm": 450.0, "period_px": 32.0, "feature": "boot grain 1.0 mm",
                   "tiles_mm": {"default": 80.0}, "maps": {"nor_gl": 0.35}},
    "Leather037": {"native_mm": None, "period_px": 30.0, "feature": "goat pebble 0.6 mm",
                   "tiles_mm": {"default": 41.0}, "maps": {"nor_gl": 1.0}},
    "Rubber004": {"native_mm": 750.0, "period_px": 21.0, "feature": "mould irregularity 0.5 mm",
                  "tiles_mm": {"default": 50.0}, "maps": {"nor_gl": 0.3}},
    "Plastic012B": {"native_mm": None, "period_px": 3.75, "feature": "moulding scratches 0.2 mm",
                    "tiles_mm": {"default": 100.0}, "maps": {"nor_gl": 0.3}},
    "Plastic018B": {"native_mm": None, "period_px": 4.05, "feature": "paint scratches 0.12 mm",
                    "tiles_mm": {"default": 60.0}, "maps": {"nor_gl": 0.35}},
    "Metal027": {"native_mm": None, "period_px": None, "feature": "oxide mottle", "tiles_mm": {"default": 60.0}},
    "Metal063": {"native_mm": None, "period_px": None, "feature": "handling smudge", "tiles_mm": {"default": 20.0}},
    "SurfaceImperfections015": {"native_mm": 650.0, "period_px": None, "feature": "dust drifts",
                                "tiles_mm": {"default": 650.0}},
    "SurfaceImperfections017": {"native_mm": 400.0, "period_px": None, "feature": "dirt speckle",
                                "tiles_mm": {"default": 400.0}},
}
TILE_TOLERANCE = 0.08   # L6: a tile scale more than 8 % off its registry value is an error


# --------------------------------------------------------------------------- §3.3 recipes built so far

# Spec 01 §3.4 and §5.1-5.3 are the regional data Skin.Foot takes from part 01 (§3.3.1: "regional data
# owned by specs 01, 03-06"); spec 16 fixes the core (§4.1) and resolved the conflicts (C27-C29). Masks are
# vertex groups or point attributes on the rendered mesh, read by name; a missing one reads 0 in Cycles,
# which every layer below treats as "this layer is off" (and assign() reports it).
SKIN_FOOT = {
    "family": "skin", "class": "skin", "builder": "skin_foot",
    "identity": "foot below the ankle seam ring of a 40-year-old Fitzpatrick II-III man, boot-wearing",
    "users": {"01": "Body.Mat.Skin.Foot (faces Foot.Region of Body.Mesh; the closeup copies inherit it)"},
    "owner": "core 16 (§4.1), regional data 01 (§3.4, §5.1-5.3)",
    "albedo_hex": "#b6886f",   # dorsum, the base the regions are laid over
    "ior": 1.40, "spec": 0.5, "sss_ior": 1.4, "sss_aniso": 0.8, "sheen": 0.04, "sheen_rough": 0.5,
    # The coat ("skin oil") is 0.08 / 0.35 on the dorsum and 0.06 / 0.35 on the toes as built, against spec 01
    # §5.1's 0.15 / 0.25 and 0.12 / 0.30: a foot has few sebaceous glands, and at 0.15 the forefoot's
    # highlight read wet in the V5 closeups; §3.3.1's skin coat range (0 - 0.12, rough 0.20 - 0.35) holds.
    "regions": {
        "dorsum": {"hex": "#b6886f", "rough": 0.42, "rough_var": 0.08, "rough_noise_mm": 3.0,
                   "sss_radius": (1.0, 0.2, 0.1), "sss_scale": 0.0032, "coat": 0.08, "coat_rough": 0.35},
        "sole": {"hex": "#d8b798", "rough": 0.52, "sss_radius": (1.0, 0.45, 0.28), "sss_scale": 0.0022, "coat": 0.0},
        "pressure": {"hex": "#d9a48e", "share": 0.6},
        "toes": {"hex": "#c48474", "share": 0.6, "rough": 0.45, "sss_factor": 0.65, "coat": 0.06, "coat_rough": 0.35},
        "callus": {"hex": "#e0cba8", "edge_hex": "#c9ad8a", "fissure_hex": "#b89a7e", "hallux_hex": "#e6d0a4",
                   "rough": 0.72, "sss_radius": (1.0, 0.45, 0.28), "sss_scale": 0.0015, "coat": 0.0,
                   "strength": {"Foot.Callus.Heel": 1.0, "Foot.Callus.Ball": 0.7, "Foot.Callus.MTP5": 0.8,
                                "Foot.Callus.Hallux": 0.6}},
        "corn": {"hex": "#e6d0a4", "ring_hex": "#c9ad8a", "rough": 0.75},
        "rub": {"hex": "#a67a66", "share": 0.4, "rough": 0.40},
        "nail_bed": {"hex": "#d49a88", "hyponychium_hex": "#c99585", "sss_scale": 0.002, "group_edge": (0.75, 1.0)},
        "vein": {"hex": "#7d8b86", "share": 0.18, "sss_radius_factor": 1.2},
        "tendon": {"lighten": 0.03},
        "crease": {"darken": 0.92, "rough_add": 0.10},
        "dry": {"hex": "#ece0cf", "share": 0.10, "noise_per_m": 400.0},
    },
    # §5.2 colour variation: noise scales in 1/m on Object coordinates (metres). The follicle dots share the
    # pits' Voronoi (same cells, a wider radius for the shadow round each pit): §3.4's 15-25 per cm² (see
    # mat_skin's note on the §5.2-5.3 table's 2200 /m cells)
    "variation": {"blotch_per_m": 180.0, "blotch_value": 0.06, "blotch_sat": 0.04,
                  "mottle_per_m": 900.0, "mottle_value": 0.03,
                  "follicle_cell_mm": 0.91, "follicle_threshold": 0.12, "follicle_darken": 0.08,
                  "follicle_redden": 0.05},
    # §5.3 relief as physical heights (Bump Distance 1, Strength 1): mm here, metres in the tree
    "micro": {
        "A_undulation": {"per_m": 60.0, "height_mm": 0.30},
        "B_lines": {"cell_mm": 1000.0 / 2400.0, "cell_toes_mm": 1000.0 / 3000.0, "width": 0.10, "depth_mm": 0.04},
        "C_follicles": {"cell_mm": 0.91, "threshold": 0.082, "depth_mm": 0.05},   # §3.4: Ø 0.15, 0.05 deep, 20 /cm²
        "D_ridges": {"pitch_mm": 0.45, "depth_mm": 0.05, "distortion": 3.0, "distortion_mm": 5.0},
        "E_crazing": {"cell_mm": 1000.0 / 350.0, "crack": 0.06, "depth_mm": 0.30},
        "F_tendon_mm": 1.5, "G_vein_mm": 1.0, "H_crease_mm": 0.8,
        "I_toe_wrinkles": {"period_mm": 1.0, "depth_mm": 0.15},
    },
    # micro-occlusion in furrows, pits and ridge valleys (E: a groove as deep as it is wide hides about a
    # tenth of the light; library addition, because random-walk scattering erases a 0.04 mm bump)
    "cavity": {"lines": 0.12, "ridges": 0.06, "rough": 0.06},
    "seam_fade_mm": (170.0, 120.0),   # §5.5: the foot's own layers fade out up the shin
    "reads": {"attributes": ["Foot.Sole", "Foot.Pressure", "Foot.ToeRed", "Foot.Callus.Heel", "Foot.Callus.Ball",
                             "Foot.Callus.MTP5", "Foot.Callus.Hallux", "Foot.Corn.L4", "Foot.Rub.Achilles",
                             "Foot.DorsumThin", "Foot.SSSScale", "Foot.Tendon", "Foot.Vein", "Foot.Crease",
                             "toenails"],
              "optional": ["Foot.Corn.L4"]},   # left foot only: its absence on the right is not news
    "wear": "none", "export": "dielectric; BaseColor = albedo, SSS dropped (§5.4)",
    "marks": "S: spec 01 §3.4 (sourced and estimated there); E: the core constants of §4.1",
}

NAIL_COMMON = {
    "family": "skin", "class": "keratin", "builder": "nail",
    "users": {"01": "Foot.Mat.Nail.Plate / .FreeEdge on Foot.<S>.Nail.<k>", "05": "finger nails"},
    "owner": "16 (§3.3.1), values from 01 §3.3-3.4",
    "ior": 1.5, "spec": 0.5, "coat": 0.6, "coat_rough": 0.10,
    # Caustics are off in every tier (spec 17 §4.9), so a refracting plate would leave the bed it covers in
    # the dark (measured: black under clear glass); shadow rays pass the plate instead, as §3.3.3 does for
    # the cornea. Keratin absorbs little, so all of the light gets through.
    "shadow_transmit": 1.0,
    "ridge_pitch_mm": 0.25, "ridge_depth_mm": 0.01, "trauma_ridge_mm": 0.20,
    "lunula_hex": "#efe4dc", "lunula_transmission": 0.35,
    "grime_hex": "#6d5a4a", "grime_share": 0.25, "grime_band_mm": 0.5,
    "reads": {"attributes": ["nail_coords"], "object_props": ["nail_lunula_mm", "nail_ridge_mm"],
              "optional": ["nail_ridge_mm"]},
    "wear": "none", "export": "opaque dielectric (§5.4: nails opaque)",
    "marks": "S: spec 01 §3.3-3.4; E: coat roughness 0.10 and the shadow transmittance (library choices)",
}
# Transmission, as built (2026-10-10): §3.3.1 gives 0.55 (plate) and 0.70 (free edge). In 4.5's Principled
# a transmission weight is the share that refracts at each hit, the rest going to a diffuse lobe of the base
# colour, and with a base this pale (#e9dfd6, Y 0.75) 0.55 renders an opaque white tile; 0.88 shows the pink
# bed through a milky plate. The free edge, over air, is white because it scatters with nothing behind it,
# which here is (1 - t) x base: 0.50 (0.40 on the test toe, renders/16_materials/probe/nail_sheet2.png,
# read as a French manicure on the foot).
NAIL_PLATE = dict(NAIL_COMMON, identity="toe and finger nail plate over its pink bed",
                  albedo_hex="#e9dfd6", rough=0.15, transmission=0.88, part="plate")
NAIL_FREE_EDGE = dict(NAIL_COMMON, identity="the free edge, past the hyponychium, over air",
                      albedo_hex="#ece6dd", rough=0.25, transmission=0.50, part="free_edge")

SOCK_COMMON = {
    "family": "fabric", "builder": "knit_sock",
    "users": {"01": "Sock.<S>.Body (leg, cuff, sole; heel pocket and toe cap Reinforced)"},
    "owner": "16 (§3.3.4), construction 01 (§3.6, §5.4)",
    "ior": 1.53, "spec": 0.35, "sheen_rough": 0.5,
    "sss_radius": (1.0, 0.8, 0.6), "sss_scale": 0.001,
    "texture": "knitted_fleece", "tile_mm": 230.0,
    # the knit's normal map at 1.0, not §3.2's x0.5: the map's tangent slopes are mild (XY spread 0.12-0.15,
    # measured), a cushion sock's 1.6 mm loops stand about 0.5 mm, and at 0.5 the V2 macro and V7 fold read
    # as felt (2026-10-10, as built)
    "normal_strength": 1.0,
    "stitch": {"wale_mm": 1.6, "course_mm": 1.2, "mortar": 0.15, "height_mm": 0.04},
    "grime": {"amount": 0.5, "oil": 0.2},   # the part's sock_grime mask carries sole 1.0, heel 0.6
    # spec 01 §3.6: bobbles 1-2 mm over 10 % of the sole. Its §5.4 recipe (600 /m cells, threshold 0.08)
    # makes 0.27 mm dots over 2 %; a 2D Voronoi of 4.2 mm cells with r 0.75 mm gives the §3.6 data. A pill
    # is a matted tuft, not a bead: irregular outline, a low soft dome (0.2 mm, not §5.4's 0.4), rougher
    "pilling": {"cell_mm": 4.2, "threshold": 0.18, "height_mm": 0.2, "lighten": 0.05, "rough_add": 0.12,
                "irregular": 0.35},
    "uv": "UV.Real",
    "reads": {"attributes": ["sock_grime", "sock_sole"], "uv": ["UV.Real"]},
    "wear": "none (its own grime and pilling)", "export": "dielectric; sheen dropped",
    "marks": "S: spec 01 §3.6; M: knitted_fleece period and statistics (§3.2)",
}
# stitch_relief scales MG.Knit.Stitch's brick (§4.7's procedural fallback). It is 0 as built (2026-10-10):
# knitted_fleece is a real stockinette at the measured 1.6 mm wale, and the brick's rows of rectangles,
# out of phase with its V columns, read as a woven rib in the V2 macro.
SOCK = dict(SOCK_COMMON, class_="textile_coloured", identity="merino/nylon cushion boot sock, coyote brown",
            albedo_hex="#5a4b3a", rough=0.80, sheen=0.08, sss_weight=0.30, stitch_relief=0.0)
SOCK_REINFORCED = dict(SOCK_COMMON, class_="textile_black",
                       identity="the same sock's nylon-plated heel pocket and toe cap, charcoal",
                       albedo_hex="#33302c", rough=0.65, sheen=0.06, sss_weight=0.15, stitch_relief=0.0)
for _d in (SOCK, SOCK_REINFORCED):
    _d["class"] = _d.pop("class_")

CATALOGUE = {
    "Skin.Foot": SKIN_FOOT,
    "Nail.Plate": NAIL_PLATE,
    "Nail.FreeEdge": NAIL_FREE_EDGE,
    "Knit.Sock.WoolNylon": SOCK,
    "Knit.Sock.WoolNylon.Reinforced": SOCK_REINFORCED,
}

# Every other ID of §3.3, by family and section: in the catalogue, not built yet.
PLANNED = {}
for _sec, _fam, _ids in (
        ("§3.3.1", "skin", "Skin.Head Skin.Body"),
        ("§3.3.2", "hair", "Hair.Scalp Hair.Stubble Hair.Brow Hair.Lash Hair.Body Fibre.Fleece"),
        ("§3.3.3", "eye", "Eye.Cornea Eye.Iris Eye.Sclera Eye.Wet Eye.Caruncle Eye.Occluder Teeth.Enamel "
                          "Teeth.Gums Mouth.Tongue Mouth.Bag"),
        ("§3.3.4", "fabric", "NYCO.Ripstop.Camo NYCO.Stretch.Camo NYCO.Ripstop.Black Knit.Jersey.FR Knit.Rib.2x2 "
                             "Fleece.Polyester Cordura.500D.OliveBrown Cordura.1000D.OliveBrown Cordura.500D.Black "
                             "Webbing.Nylon.Black Webbing.Nylon.OliveBrown Webbing.Nylon.Coyote "
                             "Binding.Grosgrain.Black Elastic.Woven.Black Cord.Braided.Black HookLoop.Hook.Black "
                             "HookLoop.Loop.Black Thread.Bonded.Black Thread.Bonded.OliveBrown Lace.Nylon.Black "
                             "Neoprene.Black Foam.ClosedCell.Black SpacerMesh.Black Knit.Glove.Honeycomb "
                             "Fabric.BackFace"),
        ("§3.3.5", "hard", "Leather.Boot.FullGrain Leather.Glove.Goat Rubber.Outsole.Black Rubber.Rand.Black "
                           "EVA.Midsole.BlueGrey Rubber.Moulded.Black Rubber.Red TPR.Glove.Black"),
        ("§3.3.6", "hard", "Polymer.Black.Smooth Polymer.Black.Textured Polymer.Grey.Light Polymer.Grey.Case "
                           "Polymer.Grey.PMAG Polymer.Tan.Painted Polymer.Tan.Moulded Paint.FDE.Brushed "
                           "Paint.Stencil.Black Paint.Stencil.Light Paint.Emblem.White"),
        ("§3.3.7", "hard", "Metal.Gunmetal Metal.Nickel Metal.Stainless Metal.Steel.Turned Metal.Steel.Polished "
                           "Metal.Steel.Phosphate Metal.Steel.Blued Metal.Aluminium.Hardcoat.Black "
                           "Metal.Aluminium.Hardcoat.Black.Gloss Metal.Aluminium.Anodised.Grey "
                           "Metal.Aluminium.Anodised.ClearBrushed Metal.Aluminium.Anodised.Gold Metal.Brass.Aged "
                           "Coating.Cerakote.BurntBronze"),
        ("§3.3.8", "hard", "Lens.Strobe.Polycarbonate Glass.Optic.Coated Glass.Light.TIR Scene.Concrete.Polished")):
    for _id in _ids.split():
        PLANNED[_id] = {"family": _fam, "section": _sec}


# --------------------------------------------------------------------------- §4.10 wear presets (data)

WEAR_PRESETS = {
    "armour.top": {"dust": 0.55, "dust_elsewhere": 0.25, "grime_cavity": 0.6, "grime_oil": 0.3,
                   "edge_mm": 1.2, "chips": {"paint.centre": (120, 0.48), "paint.frame": (220, 0.71),
                                             "paint.rib": (220, 0.65)}, "users": ["12"]},
    "panel": {"dust": 0.30, "grime_band": 0.5, "chips": {"panel": (220, 0.60)}, "users": ["13"]},
    "cordura.top": {"dust": 0.35, "grime_bottom": 0.8, "crest": 0.6, "users": ["13", "14"]},
    "cloth.thigh": {"dust": 0.40, "grime_band_mm": (320, 200), "grime": 0.6, "grime_oil": 0.2, "crest": 0.7,
                    "stress": 0.45, "users": ["09"]},
    "cloth.shoulder": {"dust": 0.35, "dust_cuff": 0.4, "crest": 0.6, "users": ["10"]},
    "fleece.toproll": {"dust": 0.45, "crest": 0.5, "users": ["10"]},
    "boot.toe": {"dust_zones": {"toe": 1.0, "vamp": 0.8, "collar_top": 0.6, "bumper_top": 0.9, "quarters": 0.15,
                                "shaft_sides": 0.05, "laces": 0.3}, "side": {"L": 1.0, "R": 0.7},
                 "grime_band_mm": (60, 20), "users": ["02"]},
    "glove.crest": {"dust_zones": {"plate": 0.55, "knit": 0.25, "leather": 0.10}, "side": {"R": 1.0, "L": 0.7},
                    "grime_oil": 0.6, "users": ["11"]},
    "belt.kit": {"dust_zones": {"tan": 0.55, "belt_top": 0.35, "black_polymer": 0.20, "hardware_under": 0.0},
                 "grime_bottom": 0.45, "users": ["14"]},
    "metal.hardware": {"dust": 0.15, "grime_cavity": 0.5, "edge_mm": 0.8, "users": ["02", "09", "12", "13", "14"]},
    "rifle": {"dust_cavity": 0.3, "dust": 0.2, "dust_local_up": 0.6, "edge_mm": 0.8,
              "chips": {"paint.overcoat": (400, 0.55)}, "users": ["15"]},
    "none": {"users": ["skin", "eyes", "hidden parts"]},
}


# --------------------------------------------------------------------------- §4.6 and §5.4 (data only)

CAMO = {"seed": 7.0, "warp_mm": 25.0, "warp_amp_mm": 6.0, "blotch_mm": 80.0, "macro_mm": 220.0, "speckle_mm": 14.0,
        "weights": (0.60, 0.25, 0.15), "grain_mm": 0.45, "cuts": (0.4697, 0.5218, 0.5719), "edge": 0.004,
        "dither": 0.010, "tones": ("#292924", "#423f39", "#5b554c", "#847464"), "level": 1.0,
        "status": "data only: MG.Camo.Blotch4 and camo_calibrate() are not built (spec 16 §9 step 6)"}

ATLASES = {
    "Export.Head": {"size": 4096, "area_m2": 0.15, "px_mm": 8.8},
    "Export.Eyes": {"size": 1024, "alpha": "cornea BLEND 0.1"},
    "Export.Hair": {"size": 2048, "alpha": "MASK 0.5"},
    "Export.Body": {"size": 2048, "area_m2": 1.9, "px_mm": 1.2},
    "Export.Garments": {"size": 4096, "area_m2": 2.7, "px_mm": 2.1},
    "Export.Carrier": {"size": 4096, "area_m2": 1.2, "px_mm": 3.1},
    "Export.Armour": {"size": 4096, "area_m2": 0.45, "px_mm": 5.1},
    "Export.Rifle": {"size": 4096, "area_m2": 0.13, "px_mm": 9.0},
    "Export.RifleKit": {"size": 2048, "area_m2": 0.05, "px_mm": 7.7, "alpha": "lens BLEND"},
    "Export.Hands": {"size": 2048, "area_m2": 0.12, "px_mm": 4.9},
    "Export.Boots": {"size": 2048, "area_m2": 0.30, "px_mm": 3.1},
    "Export.Belt": {"size": 2048, "area_m2": 0.50, "px_mm": 2.4},
}


def selftest():
    """T1 (hex round trips) and T2 (catalogue against its class rules)."""
    import random
    for rec in CATALOGUE.values():
        for k, v in _hexes(rec):
            assert linear_to_hex(hex_to_linear(v)) == v.lower(), (k, v)
    rnd = random.Random(17)
    for _ in range(1000):
        h = "#" + "".join(f"{rnd.randrange(256):02x}" for _ in range(3))
        assert linear_to_hex(hex_to_linear(h)) == h, h
    problems = []
    for rid, rec in CATALOGUE.items():
        rule = CLASS_RULES[rec["class"]]
        y = luminance(hex_to_linear(rec["albedo_hex"]))
        lo_hi = rule.get("albedo_y")
        if lo_hi and not (lo_hi[0] <= y <= lo_hi[1]):
            problems.append(f"{rid}: albedo Y {y:.3f} outside {lo_hi}")
        if rec.get("sheen", 0.0) > rule.get("sheen_max", 1.0) + 1e-9:
            problems.append(f"{rid}: sheen {rec['sheen']} above the class cap {rule['sheen_max']}")
        assert rid not in PLANNED, rid
    assert not problems, problems
    return {"recipes": len(CATALOGUE), "planned": len(PLANNED), "classes": len(CLASS_RULES)}


def _hexes(obj, path=""):
    """Every '#rrggbb' string in a nested recipe, with its key path."""
    if isinstance(obj, str):
        if obj.startswith("#") and len(obj) == 7:
            yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _hexes(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _hexes(v, f"{path}[{i}]")


if __name__ == "__main__":
    import json
    print(json.dumps(selftest()))
