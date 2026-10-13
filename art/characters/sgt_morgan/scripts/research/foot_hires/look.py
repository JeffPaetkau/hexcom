"""Materials and the look-dev scene for the trial's region: spec 16's recipes put on the dense skin and the
plates as part 01's materials stage is to call them (the same calls as scripts/eval/lookdev_p01.py), with
lookdev_p01's stand-in masks for the regional layers part 01 has not published yet.

The skin recipe reads Object coordinates in metres and the masks as attributes, so the dense copy keeps the
world transform and its interpolated groups; `toenails` is rewritten by a method that moves the nail beds,
or the bed's pink lands where the old bed was.
"""
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


def dress_skin(skin, standin=True):
    """Skin.Foot on every face of the dense copy; the stand-in masks where part 01 has none; on the new nail
    beds (the face attribute Hires.Bed, method_fields.finish) the recipe with BED_OVERRIDES."""
    from lib import materials as M
    M.ensure_groups()
    if standin:
        from eval import lookdev_p01 as LP
        LP.standin_masks([skin])
    skin.data.materials.clear()
    M.assign(skin, "Skin.Foot", part="Body")
    att = skin.data.attributes.get("Hires.Bed")
    if att is not None and att.domain == "FACE":
        M.assign(skin, "Skin.Foot", part="HiresNailBed", faces="Hires.Bed", **BED_OVERRIDES)


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
    """Turn the open scene into spec 17's LookDev (cyclorama, the three lights, AgX Base Contrast)."""
    import bpy
    from eval import lookdev
    return lookdev.build(bpy.context.scene)
