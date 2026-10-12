"""Materials and the look-dev scene for the trial's region: spec 16's recipes put on the dense skin and the
plates as part 01's materials stage is to call them (the same calls as scripts/eval/lookdev_p01.py), with
lookdev_p01's stand-in masks for the regional layers part 01 has not published yet.

The skin recipe reads Object coordinates in metres and the masks as attributes, so the dense copy keeps the
world transform and its interpolated groups; `toenails` is rewritten by a method that moves the nail beds,
or the bed's pink lands where the old bed was.
"""
import numpy as np

# spec 01 §3.3 gives the hallux a 3.5 mm lunula and toe 2 a faint one; on the trial's plates 3.5 mm read as a
# white band (a manicure). Round 3: 2.3 mm on the hallux (about 1.8 mm shows past the fold at the centre, fading
# over the last 0.5), paler than the bed but translucent (PLATE_OVERRIDES), none on toe 2
LUNULA_MM = {1: 2.3, 2: 0.0}
# The recipe draws the lunula's distal edge as lunula_mm x sqrt(1 - (u / nail_half_mm)^2); nail_coords sets
# nail_half_mm to the whole plate's half-width (hidden margins included), so the arc ran edge to edge and the
# curved cuticle line cut it into a band. A half-width of 6.5 mm on the hallux (its visible half at the root is
# about 8) makes it a crescent over the middle of the root, as on a real big toe (critic round 1, m6).
LUNULA_HALF_MM = {1: 6.5}
# Recipe overrides for the trial's plates. The library's values are spec 16's; these are what the trial shows,
# and the notes list them as proposed library changes rather than editing scripts/lib.
#  * critic round 2, m4 (frosted acrylic): the plate clear (transmission 0.96: each hit sends 1 - t to a diffuse
#    lobe of the pale base, which at 0.88 milked the pink bed over), a little smoother;
#  * m3 (highlights combed into white streaks): the ridges 0.0015 mm (a slope of about 0.02 at 0.25 mm pitch,
#    against the coat's 0.18 roughness, so they ripple only where a highlight's edge grazes them) and the coat
#    rougher (at 0.10 its lobe was narrower than the ridges' slopes, so every ridge lit up as a line);
#  * the lunula a translucent pinkish white, not round 2's opaque cream.
PLATE_OVERRIDES = {"ridge_depth_mm": 0.0015, "transmission": 0.96, "rough": 0.10, "coat_rough": 0.18,
                   "albedo_hex": "#eee4dc", "lunula_hex": "#f3e7e3", "lunula_transmission": 0.8}
# m2 (an opaque cream French tip): the free edge over air a thin, translucent off-white (transmission 0.74),
# its ridges and coat as the plate's
FREE_EDGE_OVERRIDES = {"albedo_hex": "#efe8dd", "transmission": 0.74, "rough": 0.26, "ridge_depth_mm": 0.0015,
                       "coat_rough": 0.18}
# m4: the onychodermal band, a paler line where the plate leaves the bed: the plate's faces in the last
# BAND_W mm before the free edge (w, mm past the bed's end) a less clear, paler keratin, in two steps so the
# band fades in proximally. Separate materials (a part of their own: the library names a material by recipe
# and part, so a second set of overrides on Hires.* would rebuild the plate's own)
BAND_STEPS = (((-0.75, -0.38), "HiresNailBandA", {"transmission": 0.9, "albedo_hex": "#f1e8de"}),
              ((-0.38, 0.05), "HiresNailBandB", {"transmission": 0.8, "albedo_hex": "#f3ebe1"}))
# The bed seen through a clear plate: the skin recipe's micro network (its 0.33 mm crackle cells, their
# darkened furrows) is skin texture, and under the plate it read as crazed glaze; a nail bed is smooth. The
# recipe on the bed's faces with the network nearly flat and its cavity shading off, the undulation lowered.
BED_OVERRIDES = {"micro__B_lines__depth_mm": 0.004, "cavity__lines": 0.0, "micro__A_undulation__height_mm": 0.1}


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
    bands = []
    if uvw_mm is None:
        w, vis, fe, thick = nails.PLATES[k]
        free = M.nail_coords(nob, vis, fe, lunula_mm=LUNULA_MM.get(k, 0.0), ridge_mm=ridge_mm)
        over_p, over_f = {}, {}
    else:
        wf = write_nail_coords(nob, uvw_mm, LUNULA_MM.get(k, 0.0), ridge_mm)
        free = np.nonzero(wf > 0.05)[0].tolist()
        if k in LUNULA_HALF_MM:
            nob["nail_half_mm"] = float(LUNULA_HALF_MM[k])
        over_p, over_f = PLATE_OVERRIDES, FREE_EDGE_OVERRIDES
        bands = [(np.nonzero((wf > lo) & (wf <= hi))[0].tolist(), part, dict(PLATE_OVERRIDES, **over))
                 for (lo, hi), part, over in BAND_STEPS]
    nob.data.materials.clear()
    M.assign(nob, "Nail.Plate", **over_p)
    for faces, part, over in bands:
        M.assign(nob, "Nail.Plate", part=part, faces=faces, **over)
    M.assign(nob, "Nail.FreeEdge", faces=free, **over_f)
    sol = nob.modifiers.get("Solidify")
    if sol is not None:
        sol.material_offset_rim = 0  # each rim takes its own face's material (as lookdev_p01 does)


def lookdev_scene():
    """Turn the open scene into spec 17's LookDev (cyclorama, the three lights, AgX Base Contrast)."""
    import bpy
    from eval import lookdev
    return lookdev.build(bpy.context.scene)
