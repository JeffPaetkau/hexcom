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
        ctx.plates[k] = (nob, uvw)
        made[k] = nail
        ctx.report.setdefault("nails", {})[k] = {
            "t_fold": round(nail.t0, 2), "t_free_edge": round(nail.t_fe, 2),
            "free_edge_F": nail.to_world(nail.L, 0.0, nail.plate_top(nail.L, 0.0)).round(2).tolist(),
            "fold_F": nail.to_world(0.0, 0.0, nail.plate_top(0.0, 0.0)).round(2).tolist(),
            "plate_vertices": len(verts)}
    dq, cw = M.creases(q, nrm, segs, P)
    return q + dq, beds, cw, made


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
    # the shader also darkens and wrinkles along Foot.Crease: at half weight, or the two together read as cuts
    C.set_group(skin, "Foot.Crease", 0.5 * cw)
    for k in (3, 4, 5):
        ctx.plates[k] = (bpy.data.objects[f"Foot.L.Nail.{k}"], None)


def web_by_closing(q, topo, segs, P, adj):
    """The hybrid's web: a signed distance field of the skin around the 1-2 cleft, closed by P['web_r'] over
    the cleft's floor (sdf.Field.close), and the dense skin there moved onto it. The cleft's two walls and
    its floor are already one surface on MakeHuman's mesh, so projecting them onto the closed field rounds
    and fills the floor without new topology."""
    import sdf as S
    a, b = segs["h1"].o, segs["t2p"].o
    xm, xw = 0.5 * (a[0] + b[0]), 0.5 * abs(b[0] - a[0])
    lo = (xm - xw - 6.0, P["web_y"] - 12.0, -3.0)
    hi = (xm + xw + 6.0, a[1] + 22.0, 34.0)
    field = S.Field(q, topo[2].reshape(-1, 4), y_cut=-140.0, voxel=P.get("web_voxel", 0.15), half_mm=4.0)
    field.box(lo, hi)

    def web_mask(Pts):
        x, y, z = Pts[..., 0], Pts[..., 1], Pts[..., 2]
        return (1.0 - T.smoothstep(np.abs(x - xm), 0.45 * xw, 0.85 * xw))             * T.window(y, P["web_y"] - 3.5, P["web_y"] + 0.5, a[1] + 6.0, a[1] + 14.0)             * (1.0 - T.smoothstep(z, 20.0, 27.0))

    field.close(P["web_r"], web_mask)
    w = np.ones(len(q))
    for d in range(3):
        w *= T.window(q[:, d], lo[d] + 0.5, lo[d] + 2.0, hi[d] - 2.0, hi[d] - 0.5)
    w *= np.clip(web_mask(q) * 3.0, 0.0, 1.0)
    q = field.project(q, w)
    # where the cleft's two walls came onto one surface they crumple: relax the vertices along it (a plain
    # Laplacian) and put them back on the field, a few rounds, so they spread evenly over the new web
    zone = np.clip(w * 2.0, 0.0, 1.0)
    for _ in range(int(P.get("web_relax", 6))):
        q = M.taubin(q, adj, 0.8 * zone, iterations=8, lam=0.5, mu=0.0)
        q = field.project(q, w, iterations=3)
    return q


def build(ctx):
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
    t1 = time.time()
    edges, _ = C.edge_lengths(skin)
    adj = M.adjacency(edges, len(q))
    q = M.apply(q, C.vertex_normals(q, topo), segs, groups, adj, P, ctx.report)
    ctx.report["t_macro"] = round(time.time() - t1, 2)
    if P.get("web_sdf"):
        t1 = time.time()
        q = web_by_closing(q, topo, segs, P, adj)
        ctx.report["t_web_sdf"] = round(time.time() - t1, 2)
    t1 = time.time()
    q, beds, cw, _ = nails_and_creases(ctx, q, topo, groups, segs, P)
    ctx.report["t_detail"] = round(time.time() - t1, 2)
    finish(ctx, q, beds, cw, groups)
    ctx.report["params"] = P
