"""Materials and the look-dev scene for the trial's region: spec 16's recipes put on the dense skin and the
plates as part 01's materials stage is to call them (the same calls as scripts/eval/lookdev_p01.py), with
lookdev_p01's stand-in masks for the regional layers part 01 has not published yet.

The skin recipe reads Object coordinates in metres and the masks as attributes, so the dense copy keeps the
world transform and its interpolated groups; `toenails` is rewritten by a method that moves the nail beds,
or the bed's pink lands where the old bed was.
"""
import numpy as np

# spec 01 §3.3 gives the hallux a 3.5 mm lunula and toe 2 a faint one; on the trial's plates 3.5 mm read as a
# white band (a manicure), so the trial shows the crescent's last 1.6 mm beyond the fold, and none on toe 2
LUNULA_MM = {1: 1.6, 2: 0.0}
# The recipe draws the lunula's distal edge as lunula_mm x sqrt(1 - (u / nail_half_mm)^2); nail_coords sets
# nail_half_mm to the whole plate's half-width (hidden margins included), so the arc ran edge to edge and the
# curved cuticle line cut it into a band. A half-width of 6 mm on the hallux (its visible half is 9.25) makes it
# a crescent over the middle of the root, as on a real big toe (critic round 1, m6).
LUNULA_HALF_MM = {1: 6.0}
# Recipe overrides for the trial's plates (critic round 1: m8 the plates "combed" with white streaks, m16/m17/
# m41 an even, opaque French-white free edge). The library's values are spec 16's; these are what the trial
# shows, and the notes list them as proposed library changes rather than editing scripts/lib.
PLATE_OVERRIDES = {"ridge_depth_mm": 0.004}
FREE_EDGE_OVERRIDES = {"albedo_hex": "#dfd2bb", "transmission": 0.56, "rough": 0.34}


def dress_skin(skin, standin=True):
    """Skin.Foot on every face of the dense copy; the stand-in masks where part 01 has none."""
    from lib import materials as M
    M.ensure_groups()
    if standin:
        from eval import lookdev_p01 as LP
        LP.standin_masks([skin])
    skin.data.materials.clear()
    M.assign(skin, "Skin.Foot", part="Body")


def write_nail_coords(nob, uvw_mm, lunula_mm=0.0, ridge_mm=0.0):
    """The attribute and properties the nail recipes read (lib/mat_skin.nail_coords's contract), from a
    plate's own parametrisation: u across from the centre line, v from the visible proximal fold, w past the
    bed's distal end (all mm). Returns the free-edge faces (w > 0)."""
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
    free = [i for i in range(len(start)) if w[loops[start[i]:start[i] + total[i]]].mean() > 0.05]
    return free


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
        free = write_nail_coords(nob, uvw_mm, LUNULA_MM.get(k, 0.0), ridge_mm)
        if k in LUNULA_HALF_MM:
            nob["nail_half_mm"] = float(LUNULA_HALF_MM[k])
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
