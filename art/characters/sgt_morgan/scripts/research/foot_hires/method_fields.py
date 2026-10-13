"""Method (a): the default build's foot subdivided to sub-millimetre spacing and shaped by fields at that
resolution (macro.py for the large forms, detail.py for the nails and creases), MakeHuman's topology kept.

The dense copy keeps every vertex group the body had (interpolated by the subdivision), so the masks, the
rig's weights and the UVs come through; what the method changes is positions, plus `toenails` (the beds
moved) and `Foot.Crease` (where the creases are). The hallux and toe 2 get new plates; toes 3-5 keep part
01's.
"""
import time

import numpy as np

import common as C
import detail as D
import macro as M
import toes as T

GROUPS = ("toe1-1.L", "toe1-2.L", "toe2-1.L", "toe2-2.L", "toe2-3.L", "toenails")


def read_groups(skin, names=GROUPS):
    from lib import sculpt as S
    return S.group_weights_many(skin, list(names))


def dense_skin(ctx, P):
    """The dense skin with part 01's nail beds taken out on the hallux and toe 2."""
    ctx.report["strip_nail_beds_mm"] = round(C.strip_nail_beds(ctx.body, (1, 2)), 3)
    return C.dense_copy(ctx.part, ctx.body, ctx.args.level or P["level"], name="Hires.L.Skin")


def nails_and_creases(ctx, q, topo, groups, segs, P, region_extra=None):
    """The nails of the hallux and toe 2 and the creases, on any dense skin (q: F, mm). Returns the new
    positions, the bed mask, the crease weight and the nails."""
    import bpy
    fr = ctx.frame
    nrm = C.vertex_normals(q, topo)
    beds = np.zeros(len(q))
    made = {}
    for k, segname, distal, near in ((1, "h2", "toe1-2.L", "toe1-1.L"), (2, "t2d", "toe2-3.L", "toe2-2.L")):
        mine = groups[distal] > 0.5
        nail = D.Nail(k, segs[segname], q, nrm, mine, P[f"nail{k}"])
        region = (groups[distal] + groups[near]) > 0.05
        if region_extra is not None:
            region |= region_extra
        before = q
        q, bed = nail.apply(q, nrm, region)
        if ctx.params.get("debug_sections"):
            dump_sections(ctx, k, nail, before, q, region)
        nrm = C.vertex_normals(q, topo)
        beds = np.maximum(beds, bed)
        verts, quads, uvw = nail.plate_mesh()
        old = bpy.data.objects.get(f"Hires.L.Nail.{k}")
        if old is not None:
            bpy.data.objects.remove(old)
        nob = D.mesh_object(f"Hires.L.Nail.{k}", fr.to_w(verts), quads,
                            coll=ctx.skin.users_collection[0] if ctx.skin.users_collection else None)
        orient_plate(nob, fr.vec_to_w(nail.n))
        # what the nail recipe's zones read beyond nail_coords (look.dress_plate): the proximal fold's line
        # rises `cuticle` mm toward the visible edges, which lie half_plan(0) from the centre line
        nob["hires_cuticle_mm"] = float(nail.P.get("cuticle", 0.0))
        nob["hires_half_vis0"] = float(nail.half_plan(0.0))
        ctx.plates[k] = (nob, uvw)
        made[k] = nail
        ctx.report.setdefault("nails", {})[k] = {
            "t_fold": round(nail.t0, 2), "t_free_edge": round(nail.t_fe, 2),
            "free_edge_F": nail.to_world(nail.L, 0.0, nail.plate_top(nail.L, 0.0)).round(2).tolist(),
            "fold_F": nail.to_world(0.0, 0.0, nail.plate_top(0.0, 0.0)).round(2).tolist(),
            "plate_vertices": len(verts), "burial": nail.burial()}
    dq, cw = M.creases(q, nrm, segs, P, groups)
    return q + dq, beds, cw, made


def orient_plate(nob, up_w):
    """Face normals outward: with its underside open over the bed (detail.Nail.plate_mesh, `open_bed`) the
    plate is no longer closed, and bmesh's recalculation may turn the whole shell inside out; its top must face
    the nail's up (a refracting surface's side decides entering from leaving)."""
    me = nob.data
    n = np.empty(len(me.polygons) * 3)
    me.polygons.foreach_get("normal", n)
    a = np.empty(len(me.polygons))
    me.polygons.foreach_get("area", a)
    if (n.reshape(-1, 3) @ np.asarray(up_w, float) * a).sum() < 0.0:
        me.flip_normals()
        me.update()


def dump_sections(ctx, k, nail, before, after, region):
    """The skin's vertices near the nail in its frame, before and after, and the plate's own mesh in the same
    frame, for plotting sections (cache/research/foot_hires/sections_nail<k>.npz)."""
    import os
    v0, x0, h0 = nail.vx(before)
    v1, x1, h1 = nail.vx(after)
    near = region & (v0 > -16.0) & (v0 < nail.L + 6.0) & (np.abs(x0) < 18.0)
    verts, quads, uvw = nail.plate_mesh()
    pv, px, ph = nail.vx(verts)
    os.makedirs(C.CACHE, exist_ok=True)
    np.savez_compressed(os.path.join(C.CACHE, f"sections_nail{k}.npz"),
                        before=np.stack([v0, x0, h0], 1)[near], after=np.stack([v1, x1, h1], 1)[near],
                        plate=np.stack([pv, px, ph], 1), L=nail.L, L_bed=nail.L_bed, W=nail.P["width"])


def finish(ctx, q, beds, cw, groups):
    """Write the shaped skin back: positions, the beds of toes 1-2 into `toenails` (toes 3-5 keep theirs),
    the creases into Foot.Crease; toes 3-5 keep part 01's plates."""
    import bpy
    skin, fr = ctx.skin, ctx.frame
    C.set_positions(skin, fr.to_w(q))
    mine = np.clip(groups["toe1-1.L"] + groups["toe1-2.L"] + groups["toe2-1.L"] + groups["toe2-2.L"]
                   + groups["toe2-3.L"], 0.0, 1.0) > 0.02
    C.set_group(skin, "toenails", np.where(mine, beds, groups["toenails"]))
    # the new beds' faces (every corner on the bed) as a face attribute: look.py gives them a smoother skin, as
    # the clear plates show the bed (round 3)
    me = skin.data
    loops = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", loops)
    start = np.empty(len(me.polygons), np.int64)
    me.polygons.foreach_get("loop_start", start)
    sel = np.logical_and.reduceat(np.where(mine, beds, 0.0)[loops] >= 0.5, start)
    att = me.attributes.get("Hires.Bed")
    if att is not None:
        me.attributes.remove(att)
    me.attributes.new("Hires.Bed", "BOOLEAN", "FACE").data.foreach_set("value", sel)
    # the shader also darkens and wrinkles along Foot.Crease: at half weight, or the two together read as cuts
    C.set_group(skin, "Foot.Crease", 0.5 * cw)
    for k in (3, 4, 5):
        ctx.plates[k] = (bpy.data.objects[f"Foot.L.Nail.{k}"], None)


def cleft(q, groups, P):
    """The 1-2 cleft's centre line and half-gap (F, x), measured just ahead of the commissure where the toes
    part: the hallux's lateral-most skin and toe 2's medial-most. (Round 1 took the midpoint of the two MTP
    joints, x -17.8; the hallux is 30 mm wide and toe 2 16, so the cleft is at x -8, in the mask's fade.)"""
    y0 = P["web_y"] - 3.0
    band = np.abs(q[:, 1] - y0) < 1.0
    x_lat = q[band & (groups["toe1-1.L"] > 0.5), 0].max()
    x_med = q[band & (groups["toe2-1.L"] > 0.5), 0].min()
    return 0.5 * (x_lat + x_med), max(0.5 * (x_med - x_lat), 0.5)


def web_by_closing(q, topo, segs, P, adj, groups=None, report=None):
    """The hybrid's web: a signed distance field of the skin around the 1-2 cleft, closed by P['web_r'] over
    the cleft's floor (sdf.Field.close), and the dense skin there moved onto it. The cleft's two walls and
    its floor are already one surface on MakeHuman's mesh, so projecting them onto the closed field rounds
    and fills the floor without new topology.

    Round 1's tear (a black slit on the hallux's lateral wall deep in the cleft) came from three things: the
    mask centred between the MTP joints left the cleft in its fade, so the field there was only partly closed;
    the projection was weighted by that mask, so vertices stopped part-way, inside the closed surface; and a
    plain Laplacian relax shrank what it spread. Now the mask is centred on the cleft itself and full across
    it, a vertex moves by how deep the closing swallowed it (the field's own value: on the old surface it is
    0 and nothing moves), with a gradient step of one voxel, and the crowded vertices are spread within the
    surface (tangential relax) before each re-projection."""
    import sdf as S
    a = segs["h1"].o
    if groups is not None:
        xm, half = cleft(q, groups, P)
    else:
        b = segs["t2p"].o
        xm, half = 0.5 * (a[0] + b[0]), 2.0
    full, fade = half + P.get("web_band", 2.5), half + P.get("web_band", 2.5) + 3.0
    lo = (xm - fade - 4.0, P["web_y"] - 12.0, -3.0)
    hi = (xm + fade + 4.0, a[1] + 22.0, 34.0)
    vox = P.get("web_voxel", 0.15)
    field = S.Field(q, topo[2].reshape(-1, 4), y_cut=-140.0, voxel=vox, half_mm=4.0)
    field.box(lo, hi)

    def web_mask(Pts):
        x, y, z = Pts[..., 0], Pts[..., 1], Pts[..., 2]
        return (1.0 - T.smoothstep(np.abs(x - xm), full, fade)) \
            * T.window(y, P["web_y"] - 3.5, P["web_y"] + 0.5, a[1] + 6.0, a[1] + 14.0) \
            * (1.0 - T.smoothstep(z, 20.0, 27.0))

    field.close(P["web_r"], web_mask)
    box = np.ones(len(q))
    for d in range(3):
        box *= T.window(q[:, d], lo[d] + 0.5, lo[d] + 2.0, hi[d] - 2.0, hi[d] - 0.5)
    inb = np.nonzero(box > 1e-4)[0]
    f0 = np.full(len(q), 0.0)
    f0[inb] = np.nan_to_num(field.sample(q[inb]), nan=0.0)
    swallowed = T.smoothstep(-f0, 0.02, 0.12) * box
    q0 = q
    q = field.project(q, swallowed, iterations=8, h=vox, max_step=1.0)
    moved = np.linalg.norm(q - q0, axis=1)
    # the zone to relax: what moved, widened by a few rings so the crowding spreads into its surroundings
    zone = T.smoothstep(moved, 0.01, 0.1)
    ptr, nb = adj
    deg = np.diff(ptr)
    row = np.repeat(np.arange(len(deg)), deg)
    for _ in range(int(P.get("web_zone_rings", 12))):
        zone = np.maximum(zone, 0.85 * np.bincount(row, zone[nb], minlength=len(deg)) / np.maximum(deg, 1))
    zone = np.clip(zone, 0.0, 1.0) * box
    for _ in range(int(P.get("web_relax", 6))):
        nrm = C.vertex_normals(q, topo)
        q = M.relax_tangent(q, adj, nrm, 0.9 * zone, iterations=8, lam=0.5)
        q = field.project(q, zone, iterations=3, h=vox, max_step=0.5)
    if report is not None:
        report["web"] = {"cleft_x": round(float(xm), 2), "half_gap": round(float(half), 2),
                         "moved_max": round(float(moved.max()), 2), "moved_n": int((moved > 0.05).sum())}
    return q


# the keys that act only after the large forms and the web (the nails and creases): a change to them reuses
# the cached stage (stage_key)
DETAIL_KEYS = ("nail1", "nail2", "crease_scale", "debug_sections", "stage_cache")


def stage_key(q, P):
    """The large forms' and the web's inputs: the dense skin as copied, every other parameter and the sources
    of macro.py and sdf.py (web_by_closing's own code is not hashed: clear the cache if it changes)."""
    import hashlib
    import json
    import os
    h = hashlib.sha256(np.ascontiguousarray(q).tobytes())
    h.update(json.dumps({k: v for k, v in P.items() if k not in DETAIL_KEYS}, sort_keys=True, default=str).encode())
    for f in ("macro.py", "sdf.py"):
        with open(os.path.join(C.HERE, f), "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:16]


def build(ctx):
    import json
    import os
    P = T.merged(ctx.params)
    t0 = time.time()
    skin = dense_skin(ctx, P)
    ctx.skin = skin
    fr = ctx.frame
    q = fr.to_f(C.positions(skin))
    topo = C.faces(skin)
    groups = read_groups(skin)
    segs = T.segments(ctx.joints)
    ctx.report["t_dense"] = round(time.time() - t0, 2)
    # the large forms and the web take about 150 s, the nails 6: with `stage_cache` (default on) the skin
    # after them is kept in cache/research/foot_hires/stage_<key>.npz, so a nail-only change rebuilds in seconds
    path = os.path.join(C.CACHE, f"stage_{stage_key(q, P)}.npz") if P.get("stage_cache", 1) else None
    if path and os.path.exists(path):
        with np.load(path) as z:
            q = z["q"]
            ctx.report.update(json.loads(str(z["report"])))
        ctx.report["stage_cache"] = os.path.basename(path)
    else:
        t1 = time.time()
        edges, _ = C.edge_lengths(skin)
        adj = M.adjacency(edges, len(q))
        q = M.close_folds(q, segs, groups, P, adj, ctx.report)
        q = M.apply(q, C.vertex_normals(q, topo), segs, groups, adj, P, ctx.report)
        q = M.pulps(q, C.vertex_normals(q, topo), segs, groups, P, ctx.report)
        ctx.report["t_macro"] = round(time.time() - t1, 2)
        if P.get("web_sdf"):
            t1 = time.time()
            q = web_by_closing(q, topo, segs, P, adj, groups, ctx.report)
            ctx.report["t_web_sdf"] = round(time.time() - t1, 2)
        if path:
            os.makedirs(C.CACHE, exist_ok=True)
            keep = {k: ctx.report[k] for k in ("anchors", "pulps", "web", "toe2_outline", "fold_close", "t_macro",
                                               "t_web_sdf")
                    if k in ctx.report}
            np.savez(path, q=q, report=json.dumps(keep))
    t1 = time.time()
    q, beds, cw, _ = nails_and_creases(ctx, q, topo, groups, segs, P)
    ctx.report["t_detail"] = round(time.time() - t1, 2)
    finish(ctx, q, beds, cw, groups)
    ctx.report["params"] = P
    ctx.report["joints"] = {k: np.round(v, 2).tolist() for k, v in ctx.joints.items() if k.startswith(("toe-1", "toe-2"))}
    ctx.report["axes"] = {k: {"a": np.round(s.a, 3).tolist(), "n": np.round(s.n, 3).tolist(), "length": round(s.length, 2)}
                          for k, s in segs.items()}
    ip_y = float(segs["h2"].point(1.2 + P.get("ip_shift", 0.0), 0.0, 0.0)[1])
    ctx.report["measure"] = measure(q, groups, ctx.report.get("nails", {}), ip_y)


def measure(q, groups, nails, ip_y):
    """The region's dimensions on the finished skin (F, mm): the hallux's depth (its vertical extent) at the
    nail's proximal fold and at the IP crease, and both toes' plan widths along their length (the plantar
    outline the critics read as blocks)."""
    out = {}
    floor = float(q[:, 2].min())
    for name, gs in (("hallux", ("toe1-1.L", "toe1-2.L")), ("toe2", ("toe2-1.L", "toe2-2.L", "toe2-3.L"))):
        w = sum(groups[g] for g in gs) > 0.5
        c = q[w]
        rows = []
        for y0 in np.arange(np.floor(c[:, 1].max()) - 1.0, c[:, 1].min(), -2.0):
            s = np.abs(c[:, 1] - y0) < 0.3
            if s.sum() > 20:
                cc = c[s]
                rows.append([round(float(y0), 1), round(float(cc[:, 2].min()), 2), round(float(cc[:, 2].max()), 2),
                             round(float(np.ptp(cc[:, 2])), 2), round(float(np.ptp(cc[:, 0])), 2)])
        out[name] = {"columns": ["y", "z_min", "z_max", "depth", "width"], "rows": rows}
    out["floor_z"] = round(floor, 2)
    nail = nails.get(1) or nails.get("1")
    if nail:
        w = (groups["toe1-1.L"] + groups["toe1-2.L"]) > 0.5
        c = q[w]
        for key, y0 in (("hallux_depth_nail_root", nail["fold_F"][1]), ("hallux_depth_ip", ip_y),
                        ("hallux_depth_free_edge", nail["free_edge_F"][1])):
            s = np.abs(c[:, 1] - y0) < 0.3
            out[key] = round(float(np.ptp(c[s][:, 2])), 2)
            out[key + "_y"] = round(float(y0), 2)
    return out
