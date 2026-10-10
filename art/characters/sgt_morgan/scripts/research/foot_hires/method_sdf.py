"""Method (b), and the hybrid: the region's large forms as a signed distance field (sdf.py), realised two
ways, with the same nails and creases as method (a) on top (detail.py through method_fields).

  sdf_mode "polygonise" (method b proper): OpenVDB meshes the edited field in front of y_F -146 into a new
      quad mesh; the dense skin behind that line is kept and the two meet there. The new mesh has no UVs or
      weights of its own: its vertex groups are taken from the nearest vertex of the dense skin.
  sdf_mode "project" (the hybrid): the dense MakeHuman-derived skin is moved onto the edited field's zero
      set by Newton steps, so the field's shape arrives on the base topology with its UVs and weights.
"""
import time

import numpy as np

import common as C
import method_fields as MF
import sdf as S
import toes as T

MASKS = ("Foot.Region", "Foot.Sole", "Foot.PlantarContact", "Foot.ContactZone", "body")
BOX = ((-62.0, -292.0, -4.0), (12.0, -156.0, 46.0))   # the edit box (F mm): every edit fades out inside it
SEAM_Y = -146.0                                        # where the polygonised forefoot meets the dense skin


def quads_of(ob):
    ls, lt, lv = C.faces(ob)
    if not np.all(lt == 4):
        raise ValueError(f"{ob.name}: the field is made from quads (a subdivided copy is all quads)")
    return lv.reshape(-1, 4)


def transfer_groups(src_q, src_groups, dst_q, names, y_max=-120.0):
    """Each destination vertex takes the source's weights at its nearest source vertex (mathutils KD-tree
    over the source's forefoot)."""
    from mathutils.kdtree import KDTree
    sel = np.nonzero(src_q[:, 1] < y_max)[0]
    kd = KDTree(len(sel))
    for i, j in enumerate(sel):
        kd.insert(src_q[j], i)
    kd.balance()
    near = np.empty(len(dst_q), np.int64)
    for i, p in enumerate(dst_q):
        near[i] = sel[kd.find(p)[1]]
    return {n: src_groups[n][near] for n in names if n in src_groups}, near


def build(ctx):
    import bpy
    P = T.merged(ctx.params)
    mode = P.get("sdf_mode", "polygonise")
    rep = ctx.report
    t0 = time.time()
    skin = MF.dense_skin(ctx, P)
    ctx.skin = skin
    fr = ctx.frame
    q = fr.to_f(C.positions(skin))
    topo = C.faces(skin)
    nrm = C.vertex_normals(q, topo)
    groups = MF.read_groups(skin, MF.GROUPS + MASKS)
    segs = T.segments(ctx.joints)
    rep["t_dense"] = round(time.time() - t0, 2)
    t1 = time.time()
    field = S.Field(q, quads_of(skin), y_cut=-140.0, voxel=P.get("voxel", 0.2), half_mm=4.5)
    field.box(*BOX)
    rep["field"] = {"voxel": field.voxel, "box_voxels": list(field.A.shape), "active": int(field.grid.activeVoxelCount())}
    S.region_forms(field, q, nrm, segs, groups, P, rep)
    rep["t_field"] = round(time.time() - t1, 2)
    t1 = time.time()
    if mode == "project":
        lo, hi = np.array(BOX[0]), np.array(BOX[1])
        inside = np.ones(len(q))
        for d in range(3):
            inside *= T.window(q[:, d], lo[d] + 0.5, lo[d] + 2.5, hi[d] - 2.5, hi[d] - 0.5)
        q = field.project(q, inside)
        rep["t_project"] = round(time.time() - t1, 2)
        t1 = time.time()
        q, beds, cw, _ = MF.nails_and_creases(ctx, q, topo, groups, segs, P)
        rep["t_detail"] = round(time.time() - t1, 2)
        MF.finish(ctx, q, beds, cw, groups)
    else:
        pts, qd = field.polygonise()
        keep = np.all(pts[qd][:, :, 1] < SEAM_Y, axis=1)
        qd = qd[keep]
        used = np.unique(qd)
        remap = np.full(len(pts), -1, np.int64)
        remap[used] = np.arange(len(used))
        pts, qd = pts[used], remap[qd]
        rep["t_polygonise"] = round(time.time() - t1, 2)
        rep["polygonised"] = {"vertices": len(pts), "quads": len(qd)}
        t1 = time.time()
        names = list(MF.GROUPS) + list(MASKS)
        bgroups, _ = transfer_groups(q, groups, pts, names)
        rep["t_transfer"] = round(time.time() - t1, 2)
        # the dense skin behind the seam stays as the rest of the foot (its forefoot faces go)
        import bmesh
        lv = topo[2].reshape(-1, 4)
        kill_idx = np.nonzero(np.all(q[lv][:, :, 1] < SEAM_Y + 2.0, axis=1))[0]
        bm = bmesh.new()
        bm.from_mesh(skin.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[int(i)] for i in kill_idx], context="FACES")
        bm.to_mesh(skin.data)
        bm.free()
        skin.name = "Hires.L.Rest"
        skin.data.name = "Hires.L.Rest"
        import detail as D
        new = D.mesh_object("Hires.L.Skin", fr.to_w(pts), qd, coll=skin.users_collection[0], recalc=True)
        for n in names:
            C.set_group(new, n, bgroups[n])
        ctx.extra_skins = [skin]
        ctx.skin = new
        topo_b = C.faces(new)
        qb = fr.to_f(C.positions(new))
        t1 = time.time()
        qb, beds, cw, _ = MF.nails_and_creases(ctx, qb, topo_b, bgroups, segs, P)
        rep["t_detail"] = round(time.time() - t1, 2)
        MF.finish(ctx, qb, beds, cw, bgroups)
    rep["params"] = P
