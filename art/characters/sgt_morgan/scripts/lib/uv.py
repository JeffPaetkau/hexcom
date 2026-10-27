"""UV maps (spec 18 §4.3, §5.4; spec 16 §5.1, §5.2, §5.4): unwrap with seams, texel density per island,
normalising islands to a density, packing objects into one atlas, and an overlap check.

Densities are pixels per millimetre of world surface: px/mm = sqrt(UV area x W x H / world area in mm²) per
UV island (faces joined through corners whose UVs coincide). `UV.Real` (1 UV unit = 1 m) gives 1 px/mm at
W = H = 1000, so a tile's density there is its pixels per metre / 1000. The targets of spec 16 §5.2 and the
export atlases of §5.4 are the tables DENSITY and ATLASES below; the export stage fails an island below
EXPORT_FLOOR (70 %) of its atlas's figure (spec 18 §5.4), which check_density() answers.

The overlap check rasterises every island's triangles at pixel centres on the atlas grid (span filling with
a half-open rule, so two triangles sharing an edge never both claim a pixel): pixels claimed by two islands
are overlaps, pixels claimed twice inside one island are folds, faces whose UV winding disagrees with their
island's are flipped, and with margin_px each island is grown by half the margin first, so islands packed
closer than the margin show as margin conflicts. Unwrapping and packing use Blender's operators in edit
mode through the real selection (research C, ctx.py); measuring is numpy on the mesh data.
"""
import math

import numpy as np

from . import ctx

MM = 0.001
REAL, ATLAS = "UV.Real", "UV.Atlas"

# spec 16 §5.2: targets in px/mm (a pair is a range)
DENSITY = {
    "micro_tile_min": 13.0,      # tiled weave, knit, grain, ripstop (Fabric063 at 156 mm, Leather032 at 80 mm)
    "cotton_jersey": 7.8,        # the one exception: a 0.69 mm course is still 5 texels
    "wear_hero": (4.0, 8.0),     # wear masks on hero parts: armour, carrier front, gloves, rifle, boots
    "wear_other": (2.0, 4.0),
    "skin_head": 13.6,           # spec 06
    "skin_body": 2.4,            # specs 03, 04
    "skin_hand": 1.6,            # spec 05
    "export": (1.2, 9.0),        # the export bakes, by atlas (ATLASES)
}
# spec 16 §5.4: export atlas -> (size px, px/mm); Export.Eyes and Export.Hair have no density figure
ATLASES = {
    "Export.Head": (4096, 8.8), "Export.Body": (2048, 1.2), "Export.Garments": (4096, 2.1),
    "Export.Carrier": (4096, 3.1), "Export.Armour": (4096, 5.1), "Export.Rifle": (4096, 9.0),
    "Export.RifleKit": (2048, 7.7), "Export.Hands": (2048, 4.9), "Export.Boots": (2048, 3.1),
    "Export.Belt": (2048, 2.4),
}
EXPORT_FLOOR = 0.7
MARGIN_PX = {1024: 4, 2048: 8, 4096: 16}  # spec 16 §5.1: 8 px at 2K, 16 at 4K


def target(kind):
    """A density target in px/mm: a DENSITY key (a range gives its lower end), or an atlas name."""
    if kind in ATLASES:
        return ATLASES[kind][1]
    v = DENSITY[kind]
    return v[0] if isinstance(v, tuple) else v


def _wh(px):
    return (int(px), int(px)) if np.isscalar(px) else (int(px[0]), int(px[1]))


# --------------------------------------------------------------------------- layers and mesh data

def layer(ob, uv=ATLAS, make=True):
    """The object's UV layer `uv` (made if missing and make), set active so operators work on it."""
    me = ob.data
    lay = me.uv_layers.get(uv)
    if lay is None:
        if not make:
            raise KeyError(f"{ob.name} has no UV layer {uv!r} (has {[l.name for l in me.uv_layers]})")
        lay = me.uv_layers.new(name=uv)
        if lay is None:
            raise RuntimeError(f"{ob.name}: cannot add UV layer {uv!r} (8 layers at most)")
    me.uv_layers.active = lay
    return lay


def _data(ob, uv=None, world=True):
    """Mesh arrays: co (V, 3) mm (world), loop_start, loop_total, loop_vert, uv (L, 2) of the layer."""
    me = ob.data
    lay = me.uv_layers.get(uv) if uv else me.uv_layers.active
    if lay is None:
        raise KeyError(f"{ob.name} has no UV layer {uv or '(active)'}")
    V, P, L = len(me.vertices), len(me.polygons), len(me.loops)
    co = np.empty(V * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    if world:
        M = np.array(ob.matrix_world, float)
        co = co @ M[:3, :3].T + M[:3, 3]
    ls, lt, lv = np.empty(P, np.int64), np.empty(P, np.int64), np.empty(L, np.int64)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    me.loops.foreach_get("vertex_index", lv)
    t = np.empty(L * 2)
    lay.data.foreach_get("uv", t)
    return {"co": co / MM, "ls": ls, "lt": lt, "lv": lv, "uv": t.reshape(-1, 2), "layer": lay.name}


def _fan_corners(ls, lt):
    """Fan triangles as loop indices (T, 3) and the face of each."""
    tris, face = [], []
    for k in range(1, int(lt.max()) - 1 if len(lt) else 0):
        ok = np.flatnonzero(lt > k + 1)
        tris.append(np.stack([ls[ok], ls[ok] + k, ls[ok] + k + 1], 1))
        face.append(ok)
    if not tris:
        return np.zeros((0, 3), np.int64), np.zeros(0, np.int64)
    return np.vstack(tris), np.concatenate(face)


def _areas(d):
    """Per face: world area (mm²) and signed UV area."""
    tris, face = _fan_corners(d["ls"], d["lt"])
    P = len(d["ls"])
    p = d["co"][d["lv"][tris]]
    a3 = 0.5 * np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1)
    q = d["uv"][tris]
    e1, e2 = q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]
    auv = 0.5 * (e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
    return np.bincount(face, a3, P), np.bincount(face, auv, P), tris, face


def _components(n, a, b):
    """Connected components of n nodes joined by the edges a-b: labels 0..k-1 (hooking and pointer jumping)."""
    parent = np.arange(n)
    if len(a) == 0:
        return parent
    while True:
        pa, pb = parent[a], parent[b]
        m = np.minimum(pa, pb)
        np.minimum.at(parent, pa, m)
        np.minimum.at(parent, pb, m)
        while True:
            pp = parent[parent]
            if np.array_equal(pp, parent):
                break
            parent = pp
        if np.array_equal(parent[a], parent[b]):
            break
    return np.unique(parent, return_inverse=True)[1]


def islands(ob, uv=None, d=None):
    """Island label of every face (faces joined through corners on the same vertex with the same UV)."""
    d = d or _data(ob, uv)
    P = len(d["ls"])
    if P == 0:
        return np.zeros(0, np.int64)
    q = np.round(d["uv"] * (1 << 22)).astype(np.int64)
    keys = np.stack([d["lv"], q[:, 0], q[:, 1]], 1)
    _, uvv = np.unique(keys, axis=0, return_inverse=True)
    corner_face = np.repeat(np.arange(P), d["lt"])
    lab = _components(P + int(uvv.max()) + 1, corner_face, P + uvv.ravel())
    return np.unique(lab[:P], return_inverse=True)[1]


# --------------------------------------------------------------------------- seams and unwrapping

def _segment_dist(pts, a, b):
    ab = b - a
    t = np.clip(((pts - a) @ ab) / max(float(ab @ ab), 1e-30), 0.0, 1.0)
    return np.linalg.norm(pts - (a + t[:, None] * ab), axis=1)


def seam_edges(ob, seams, tol=1.0):
    """Edge indices from a seam spec: edge indices, the name of a boolean edge attribute, or polylines
    (each (k, 3) mm world): edges whose two vertices both lie within tol mm of one polyline."""
    me = ob.data
    if isinstance(seams, str):
        att = me.attributes.get(seams)
        if att is None or att.domain != "EDGE":
            raise KeyError(f"{ob.name} has no edge attribute {seams!r}")
        a = np.zeros(len(me.edges), bool)
        att.data.foreach_get("value", a)
        return np.flatnonzero(a)
    seams = list(seams)
    if not seams:
        return np.zeros(0, np.int64)
    if np.ndim(seams[0]) == 2:
        co = _co_mm(ob)
        ev =np.empty(len(me.edges) * 2, np.int64)
        me.edges.foreach_get("vertices", ev)
        ev = ev.reshape(-1, 2)
        near = np.zeros(len(co), bool)
        for line in seams:
            line = np.asarray(line, float)
            d = np.full(len(co), np.inf)
            for a, b in zip(line[:-1], line[1:]):
                d = np.minimum(d, _segment_dist(co, a, b))
            near |= d <= tol
        return np.flatnonzero(near[ev[:, 0]] & near[ev[:, 1]])
    return np.asarray(seams, np.int64)


def _co_mm(ob):
    me = ob.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    M = np.array(ob.matrix_world, float)
    return (co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]) / MM


def unwrap(ob, seams=None, *, uv=ATLAS, method="ANGLE_BASED", margin=0.002, tol=1.0, clear=True,
           fill_holes=True):
    """Mark seams (see seam_edges; None keeps the mesh's own; clear replaces them) and unwrap every face
    into the layer `uv` with bpy.ops.uv.unwrap (method 'ANGLE_BASED', 'CONFORMAL' or 'MINIMUM_STRETCH').
    Returns the seam and island counts."""
    import bpy
    me = ob.data
    if seams is not None:
        edges = seam_edges(ob, seams, tol)
        flags = np.zeros(len(me.edges), bool)
        if not clear:
            me.edges.foreach_get("use_seam", flags)
        flags[edges] = True
        me.edges.foreach_set("use_seam", flags)
        me.update()
    layer(ob, uv)
    with ctx.mode(ob, "EDIT"):
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.unwrap(method=method, fill_holes=fill_holes, correct_aspect=True, margin_method="FRACTION",
                          margin=margin)
    flags = np.zeros(len(me.edges), bool)
    me.edges.foreach_get("use_seam", flags)
    return {"seams": int(flags.sum()), "islands": int(islands(ob, uv).max() + 1) if len(me.polygons) else 0}


# --------------------------------------------------------------------------- density

def texel_density(ob, px, uv=None):
    """px/mm per UV island for a texture of px (or (w, h)) pixels: a record with every island and the
    minimum, maximum, median and area-weighted mean."""
    w, h = _wh(px)
    d = _data(ob, uv)
    a3, auv, _, _ = _areas(d)
    lab = islands(ob, d=d)
    n = int(lab.max()) + 1 if len(lab) else 0
    A3 = np.bincount(lab, a3, n)
    Auv = np.bincount(lab, np.abs(auv), n)
    dens = np.sqrt(Auv * w * h / np.maximum(A3, 1e-12))
    faces = np.bincount(lab, minlength=n)
    rows = [{"island": k, "faces": int(faces[k]), "area_mm2": float(A3[k]), "uv_area": float(Auv[k]),
             "px_per_mm": float(dens[k])} for k in range(n)]
    ok = A3 > 0
    return {"object": ob.name, "uv": d["layer"], "px": [w, h], "islands": rows,
            "min": float(dens[ok].min()) if ok.any() else 0.0, "max": float(dens[ok].max()) if ok.any() else 0.0,
            "median": float(np.median(dens[ok])) if ok.any() else 0.0,
            "mean": float(np.sqrt((Auv * w * h).sum() / max(A3.sum(), 1e-12)))}


def check_density(objs, px, want, floor=EXPORT_FLOOR, uv=None):
    """Islands below floor x want px/mm (want a number, a DENSITY key or an atlas name): the export stage's
    test (spec 18 §5.4). Returns {"pass", "want", "low": [(object, island, px/mm)]}."""
    want = target(want) if isinstance(want, str) else float(want)
    low = []
    for ob in objs:
        rep = texel_density(ob, px, uv)
        low += [(ob.name, r["island"], round(r["px_per_mm"], 3)) for r in rep["islands"]
                if r["area_mm2"] > 0 and r["px_per_mm"] < floor * want]
    return {"pass": not low, "want": want, "floor": floor, "low": low}


def normalise_density(objs, px_per_mm, size=2048, uv=None):
    """Scale every island of every object about its UV centroid to px_per_mm at a size (or (w, h)) texture;
    islands are not moved apart (pack() does that). Returns {object: [scale per island]}."""
    w, h = _wh(size)
    out = {}
    for ob in objs:
        d = _data(ob, uv)
        a3, auv, _, _ = _areas(d)
        lab = islands(ob, d=d)
        n = int(lab.max()) + 1 if len(lab) else 0
        A3 = np.bincount(lab, a3, n)
        Auv = np.bincount(lab, np.abs(auv), n)
        cur = np.sqrt(Auv * w * h / np.maximum(A3, 1e-12))
        f = np.where(cur > 0, px_per_mm / np.maximum(cur, 1e-12), 1.0)
        loop_lab = np.repeat(lab, d["lt"])
        t = d["uv"]
        cen = np.stack([np.bincount(loop_lab, t[:, k], n) / np.maximum(np.bincount(loop_lab, minlength=n), 1)
                        for k in (0, 1)], 1)
        t = cen[loop_lab] + (t - cen[loop_lab]) * f[loop_lab, None]
        ob.data.uv_layers[d["layer"]].data.foreach_set("uv", t.astype(np.float32).ravel())
        ob.data.update()
        out[ob.name] = f.tolist()
    return out


# --------------------------------------------------------------------------- packing

def _all_uv(objs, uv):
    return np.vstack([_data(o, uv)["uv"] for o in objs if len(o.data.loops)])


def pack(objs, size=2048, margin_px=None, uv=ATLAS, *, rotate=True, keep_density=True, shape="AABB"):
    """Pack the islands of every object into one 0-1 square with bpy.ops.uv.pack_islands in multi-object edit
    mode, margin_px (default spec 16's 8 at 2K, 16 at 4K) as a fraction of size. keep_density packs without
    scaling the islands, so normalise_density()'s figure survives; when they do not fit at that density they
    are packed again with scaling and the record says by how much the density fell. shape 'AABB' (bounding
    boxes) is the default because the shaped packers are slow here: eight islands took 12 s ('CONVEX') and
    35 s ('CONCAVE') without scaling, 130-220 s with it (Blender 4.5.14, 2026-10-27); pass them for a final
    atlas where the extra density is worth it."""
    import bpy
    objs = list(objs)
    if not objs:
        raise ValueError("pack() needs objects")
    w, _ = _wh(size)
    margin_px = MARGIN_PX.get(w, max(2, w // 256)) if margin_px is None else margin_px
    for o in objs:
        layer(o, uv)
    before = sum(abs(_areas(_data(o, uv))[1]).sum() for o in objs)
    vl = bpy.context.view_layer
    prev_active, prev_sel = vl.objects.active, [o for o in vl.objects if o.select_get()]
    ts = bpy.context.scene.tool_settings
    sync = ts.use_uv_select_sync
    fitted = True
    try:
        if vl.objects.active is not None and vl.objects.active.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        ctx.set_active(objs[0], select=objs[1:])
        bpy.ops.object.mode_set(mode="EDIT")
        ts.use_uv_select_sync = True
        bpy.ops.mesh.select_all(action="SELECT")

        def run(scale):
            bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", rotate=rotate, rotate_method="ANY", scale=scale,
                                    merge_overlap=False, margin_method="FRACTION", margin=margin_px / w,
                                    shape_method=shape)
        run(not keep_density)
        bpy.ops.object.mode_set(mode="OBJECT")
        t = _all_uv(objs, uv)
        if keep_density and (t.min() < -1e-6 or t.max() > 1 + 1e-6):
            fitted = False
            bpy.ops.object.mode_set(mode="EDIT")
            run(True)
    finally:
        if vl.objects.active is not None and vl.objects.active.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        ts.use_uv_select_sync = sync
        for o in vl.objects:
            o.select_set(False)
        for o in prev_sel:
            try:
                o.select_set(True)
            except ReferenceError:
                pass
        vl.objects.active = prev_active
    t = _all_uv(objs, uv)
    after = sum(abs(_areas(_data(o, uv))[1]).sum() for o in objs)
    return {"objects": [o.name for o in objs], "size": w, "margin_px": margin_px, "fitted": fitted,
            "density_factor": float(math.sqrt(after / before)) if before > 0 else 1.0,
            "bounds": [t.min(0).tolist(), t.max(0).tolist()], "coverage": float(after)}


# --------------------------------------------------------------------------- overlaps

def _raster(tri, w, h):
    """Coverage counts (h, w) of triangles (T, 3, 2) in pixel units, sampled at pixel centres (half-open)."""
    out = np.zeros((h, w + 1), np.int32)
    if len(tri) == 0:
        return out[:, :w]
    ys = tri[..., 1]
    y0 = np.clip(np.ceil(ys.min(1) - 0.5).astype(np.int64), 0, h)
    y1 = np.clip(np.ceil(ys.max(1) - 0.5).astype(np.int64), 0, h)
    nrow = np.maximum(y1 - y0, 0)
    total = int(nrow.sum())
    if total == 0:
        return out[:, :w]
    tid = np.repeat(np.arange(len(tri)), nrow)
    start = np.cumsum(nrow) - nrow
    rows = np.repeat(y0, nrow) + (np.arange(total) - np.repeat(start, nrow))
    yc = rows + 0.5
    xl = np.full(total, np.inf)
    xr = np.full(total, -np.inf)
    hits = np.zeros(total, np.int8)
    for i, j in ((0, 1), (1, 2), (2, 0)):
        p, q = tri[tid, i], tri[tid, j]
        lo, hi = np.minimum(p[:, 1], q[:, 1]), np.maximum(p[:, 1], q[:, 1])
        hit = (yc >= lo) & (yc < hi)
        dy = np.where(q[:, 1] != p[:, 1], q[:, 1] - p[:, 1], 1.0)
        x = p[:, 0] + (yc - p[:, 1]) * (q[:, 0] - p[:, 0]) / dy
        xl = np.where(hit, np.minimum(xl, x), xl)
        xr = np.where(hit, np.maximum(xr, x), xr)
        hits += hit
    ok = hits >= 2
    i0 = np.clip(np.ceil(xl[ok] - 0.5), 0, w).astype(np.int64)
    i1 = np.clip(np.ceil(xr[ok] - 0.5), 0, w).astype(np.int64)
    r = rows[ok]
    keep = i1 > i0
    np.add.at(out, (r[keep], i0[keep]), 1)
    np.add.at(out, (r[keep], i1[keep]), -1)
    return np.cumsum(out, axis=1)[:, :w]


def _grow(mask, r):
    """A boolean mask grown by r pixels (a square)."""
    if r <= 0:
        return mask
    m = mask.copy()
    for k in range(1, r + 1):
        m[k:, :] |= mask[:-k, :]
        m[:-k, :] |= mask[k:, :]
    m2 = m.copy()
    for k in range(1, r + 1):
        m2[:, k:] |= m[:, :-k]
        m2[:, :-k] |= m[:, k:]
    return m2


def overlaps(objs, uv=None, size=1024, margin_px=0):
    """The overlap check (see the module docstring) on a size-pixel grid of the 0-1 square. Returns
    overlap_px (pixels in two islands or more), their share of the covered pixels, the worst island pairs,
    fold_px (pixels covered twice inside an island), flipped_faces, outside_faces (a corner outside 0-1),
    and with margin_px the margin_conflict_px between islands grown by half the margin."""
    w = h = int(size)
    count = np.zeros((h, w), np.int32)
    owner = np.full((h, w), -1, np.int64)
    grown_owner = np.full((h, w), -1, np.int64) if margin_px else None
    names, pairs, conflicts = [], {}, {}
    fold_px = flipped = outside = 0
    margin_conflict = 0
    rad = int(math.floor(margin_px / 2.0)) - 1 if margin_px else 0
    for ob in objs:
        d = _data(ob, uv)
        if len(d["ls"]) == 0:
            continue
        _, auv, tris, face = _areas(d)
        lab = islands(ob, d=d)
        corners = d["uv"]
        bad = (corners < -1e-6) | (corners > 1 + 1e-6)
        outside += int(np.bincount(np.repeat(np.arange(len(d["ls"])), d["lt"]), bad.any(1), len(d["ls"])).astype(bool).sum())
        for k in range(int(lab.max()) + 1):
            fk = np.flatnonzero(lab == k)
            sign = np.sign(auv[fk].sum()) or 1.0
            flipped += int((np.sign(auv[fk]) == -sign).sum())
            tk = tris[np.isin(face, fk)]
            xy = corners[tk] * [w, h]
            lo = np.clip(np.floor(xy.reshape(-1, 2).min(0)).astype(int) - rad - 1, 0, [w, h])
            hi = np.clip(np.ceil(xy.reshape(-1, 2).max(0)).astype(int) + rad + 2, 0, [w, h])
            if np.any(hi <= lo):
                continue
            ww, hh = hi - lo
            c = _raster(xy - lo, int(ww), int(hh))
            fold_px += int((c >= 2).sum())
            mask = c > 0
            gid = len(names)
            names.append((ob.name, k))
            win = (slice(lo[1], hi[1]), slice(lo[0], hi[0]))
            prev = owner[win][mask]
            hit = prev[prev >= 0]
            if len(hit):
                ids, n = np.unique(hit, return_counts=True)
                for i, m in zip(ids, n):
                    pairs[(int(i), gid)] = pairs.get((int(i), gid), 0) + int(m)
            count[win] += mask
            o = owner[win]
            o[mask & (o < 0)] = gid
            if grown_owner is not None:
                g = _grow(mask, max(rad, 0))
                go = grown_owner[win]
                prev = go[g]
                margin_conflict += int(((prev >= 0) & (prev != gid)).sum())
                go[g & (go < 0)] = gid
    covered = int((count > 0).sum())
    over = int((count >= 2).sum())
    worst = sorted(pairs.items(), key=lambda kv: -kv[1])[:20]
    rec = {"size": w, "covered_px": covered, "overlap_px": over, "overlap_frac": over / covered if covered else 0.0,
           "pairs": [[list(names[a]), list(names[b]), n] for (a, b), n in worst], "fold_px": fold_px,
           "flipped_faces": flipped, "outside_faces": outside, "islands": len(names)}
    if margin_px:
        rec.update(margin_px=margin_px, margin_conflict_px=margin_conflict)
    return rec


# --------------------------------------------------------------------------- self-test

def _mesh(name, verts, faces):
    import bpy
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _box(name, size_mm, centre=(0, 0, 0)):
    s = np.asarray(size_mm, float) * MM / 2
    c = np.asarray(centre, float) * MM
    v = [c + s * p for p in np.array([(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                                       (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], float)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return _mesh(name, v, f)


def _grid(name, n, size_mm, z_mm=0.0):
    g = np.linspace(-size_mm / 2, size_mm / 2, n + 1) * MM
    X, Y = np.meshgrid(g, g)
    v = np.stack([X.ravel(), Y.ravel(), np.full(X.size, z_mm * MM)], 1)
    idx = np.arange(X.size).reshape(n + 1, n + 1)
    f = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    return _mesh(name, v, f)


def selftest():
    """Unwrap a box cut on every edge (six islands) and a grid cut by a polyline (two), measure density
    against the areas, normalise to 5 px/mm, pack two objects into 2048² keeping it with no overlap and no
    margin conflict, and catch a deliberate overlap and a flipped face."""
    import bpy
    R, made = {}, []
    try:
        box = _box("SelftestUV.Box", (100, 60, 40))
        made.append(box)
        r = unwrap(box, seams=list(range(12)))
        assert r["islands"] == 6 and r["seams"] == 12, r
        rep = texel_density(box, 1024)
        areas = sorted(round(i["area_mm2"]) for i in rep["islands"])
        assert areas == [2400, 2400, 4000, 4000, 6000, 6000], areas
        for i in rep["islands"]:
            assert abs(i["px_per_mm"] - 1024 * math.sqrt(i["uv_area"] / i["area_mm2"])) < 1e-9
        R["box_unwrap_density_px_mm"] = [round(rep["min"], 3), round(rep["max"], 3)]

        grid = _grid("SelftestUV.Grid", 10, 100.0)
        made.append(grid)
        r = unwrap(grid, seams=[np.array([(-60.0, 0.0, 0.0), (60.0, 0.0, 0.0)])])
        assert r["islands"] == 2 and r["seams"] == 10, r
        hold = check_density([grid], 2048, 100.0)
        assert not hold["pass"] and len(hold["low"]) == 2

        normalise_density([box, grid], 5.0, 2048)
        for ob in (box, grid):
            rep = texel_density(ob, 2048)
            assert abs(rep["min"] - 5.0) < 1e-4 and abs(rep["max"] - 5.0) < 1e-4, (ob.name, rep["min"], rep["max"])
        assert check_density([box, grid], 2048, "Export.Boots")["pass"]  # 5 px/mm >= 0.7 x 3.1
        pk = pack([box, grid], 2048)
        assert pk["fitted"] and abs(pk["density_factor"] - 1.0) < 1e-4, pk
        for ob in (box, grid):
            rep = texel_density(ob, 2048, ATLAS)
            assert abs(rep["min"] - 5.0) < 1e-3 and abs(rep["max"] - 5.0) < 1e-3, rep
        ov = overlaps([box, grid], ATLAS, 2048, margin_px=pk["margin_px"])
        assert ov["overlap_px"] == 0 and ov["fold_px"] == 0 and ov["flipped_faces"] == 0, ov
        assert ov["outside_faces"] == 0 and ov["margin_conflict_px"] == 0 and ov["islands"] == 8, ov
        lo, hi = pk["bounds"]
        assert min(lo) >= 0.0 and max(hi) <= 1.0
        R["pack"] = {"bounds": [[round(x, 4) for x in lo], [round(x, 4) for x in hi]],
                     "covered_px": ov["covered_px"]}

        # a pack that cannot keep its density: 20 px/mm of a 1 m² box does not fit 2048²
        big = _box("SelftestUV.Big", (1000, 1000, 10))
        made.append(big)
        unwrap(big, seams=list(range(12)))
        normalise_density([big], 20.0, 2048)
        pk2 = pack([big], 2048)
        assert not pk2["fitted"] and pk2["density_factor"] < 0.2 and max(pk2["bounds"][1]) <= 1.0, pk2

        # the check catches what it should: two quads on the same UVs, a fold, a flipped face
        qa = _mesh("SelftestUV.QuadA", [(0, 0, 0), (0.01, 0, 0), (0.01, 0.01, 0), (0, 0.01, 0)], [(0, 1, 2, 3)])
        qb = _mesh("SelftestUV.QuadB", [(0, 0, 0.02), (0.01, 0, 0.02), (0.01, 0.01, 0.02), (0, 0.01, 0.02)],
                   [(0, 1, 2, 3)])
        made += [qa, qb]
        for ob in (qa, qb):
            lay = layer(ob, ATLAS)
            lay.data.foreach_set("uv", np.array([(0.1, 0.1), (0.5, 0.1), (0.5, 0.5), (0.1, 0.5)], np.float32).ravel())
        ov = overlaps([qa, qb], ATLAS, 1000)
        assert abs(ov["overlap_px"] - 400 * 400) <= 800 and ov["pairs"][0][2] == ov["overlap_px"], ov
        fold = _mesh("SelftestUV.Fold", [(0, 0, 0), (0.01, 0, 0), (0.02, 0, 0), (0, 0.01, 0), (0.01, 0.01, 0),
                                         (0.02, 0.01, 0)], [(0, 1, 4, 3), (1, 2, 5, 4)])
        made.append(fold)
        lay = layer(fold, ATLAS)
        # the second face folded back over the first: a fold and a flipped face, one island
        lay.data.foreach_set("uv", np.array([(0.1, 0.1), (0.3, 0.1), (0.3, 0.3), (0.1, 0.3),
                                             (0.3, 0.1), (0.15, 0.1), (0.15, 0.3), (0.3, 0.3)], np.float32).ravel())
        ov = overlaps([fold], ATLAS, 1000)
        assert ov["islands"] == 1 and ov["flipped_faces"] == 1 and ov["fold_px"] > 0.9 * 150 * 200, ov
        R["checks"] = {"overlap_px": 160000, "fold_px": ov["fold_px"]}
        return R
    finally:
        for o in made:
            data = o.data
            bpy.data.objects.remove(o)
            if data is not None and data.users == 0:
                bpy.data.meshes.remove(data)
