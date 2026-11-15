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

GROUPS = tuple(g for k in (1, 2, 3, 4, 5) for g in T.TOES[k][3]) + ("toenails",)


def read_groups(skin, names=GROUPS):
    from lib import sculpt as S
    return S.group_weights_many(skin, list(names))


def dense_skin(ctx, P):
    """The dense skin with part 01's nail beds taken out on every toe (whole foot, pass 1; the trial took them
    out on the hallux and toe 2)."""
    ctx.report["strip_nail_beds_mm"] = round(C.strip_nail_beds(ctx.body, (1, 2, 3, 4, 5)), 3)
    return C.dense_copy(ctx.part, ctx.body, ctx.args.level or P["level"], name="Hires.L.Skin")


def nails_and_creases(ctx, q, topo, groups, segs, P, region_extra=None):
    """The nails of the hallux and toe 2 and the creases, on any dense skin (q: F, mm). Returns the new
    positions, the bed mask, the crease weight and the nails."""
    import bpy
    fr = ctx.frame
    nrm = C.vertex_normals(q, topo)
    beds = np.zeros(len(q))
    made = {}
    adj = None
    toes = [k for k in (1, 2, 3, 4, 5) if P.get(f"nail{k}")]
    if any(P[f"nail{k}"].get("relax_iters") for k in toes):
        edges, _ = C.edge_lengths(ctx.skin)
        adj = M.adjacency(edges, len(q))
    for k, segname, distal, near in [(k,) + T.TOES[k][:3] for k in toes]:
        mine = groups[distal] > 0.5
        nail = D.Nail(k, segs[segname], q, nrm, mine, P[f"nail{k}"])
        region = (groups[distal] + groups[near]) > 0.05
        if region_extra is not None:
            region |= region_extra
        before = q
        q, bed = nail.apply(q, nrm, region, adj=adj)
        if ctx.params.get("debug_sections"):
            dump_sections(ctx, k, nail, before, q, region)
        nrm = C.vertex_normals(q, topo)
        beds = np.maximum(beds, bed)
        cont = bool(nail.P.get("continuous"))
        # round 5 (`continuous`): the plate's visible top is the skin's own surface, shaded as nail from the
        # fields the nail wrote (finish -> Hires.NailA / NailB / NailC); the only separate mesh is the free edge
        verts, quads, uvw = nail.free_edge_mesh() if cont else nail.plate_mesh()
        if cont:
            ctx.nail_shade = getattr(ctx, "nail_shade", {})
            ctx.nail_shade[k] = dict(nail.shade, lunula_k=float(nail.P.get("lunula_k", 0.0)))
            A_ = nail.shade["A"]
            ins = A_[:, 0] < 0.0
            ctx.report.setdefault("nail_fields", {})[k] = {
                "inside": int(ins.sum()), "lunula": int((ins & (A_[:, 2] < 0.0)).sum()),
                "lun_range": [round(float(A_[ins, 2].min()), 2), round(float(A_[ins, 2].max()), 2)] if ins.any() else None,
                "v_range": [round(float(nail.shade["B"][ins, 1].min()), 2), round(float(nail.shade["B"][ins, 1].max()), 2)]
                if ins.any() else None}
        old = bpy.data.objects.get(f"Hires.L.Nail.{k}")
        if old is not None:
            bpy.data.objects.remove(old)
        nob = D.mesh_object(f"Hires.L.Nail.{k}", fr.to_w(verts), quads,
                            coll=ctx.skin.users_collection[0] if ctx.skin.users_collection else None)
        if cont:
            orient_closed(nob)
        else:
            orient_plate(nob, fr.vec_to_w(nail.n))
        nob["hires_free_edge"] = int(cont)
        # what the nail recipe's zones read beyond nail_coords (look.dress_plate): the proximal fold's line
        # rises `cuticle` mm toward the visible edges, which lie half_plan(0) from the centre line
        nob["hires_cuticle_mm"] = float(nail.P.get("cuticle", 0.0))
        nob["hires_half_vis0"] = float(nail.half_plan(0.0))
        ctx.plates[k] = (nob, uvw)
        made[k] = nail
        census = getattr(ctx, "census", None)
        if census is not None:
            census(f"nail{k}", q)
        ctx.report.setdefault("nails", {})[k] = {
            "t_fold": round(nail.t0, 2), "t_free_edge": round(nail.t_fe, 2),
            "free_edge_F": nail.to_world(nail.L, 0.0, nail.plate_top(nail.L, 0.0)).round(2).tolist(),
            "fold_F": nail.to_world(0.0, 0.0, nail.plate_top(0.0, 0.0)).round(2).tolist(),
            "plate_vertices": len(verts), "burial": nail.burial()}
    import whole
    dq, cw = whole.creases(q, nrm, segs, P, groups, ctx.report)
    q = q + dq
    census = getattr(ctx, "census", None)
    if census is not None:
        census("creases", q)
    if P.get("untangle", 0):
        q, ctx.report["untangle"] = untangle(q, topo, groups, adj if adj is not None else None, ctx, P)
    return q, beds, cw, made


class FoldCensus:
    """Whole foot, pass 2: adjacent faces turned over (normals more than 120 degrees apart, untangle's test) over
    the whole dense skin, counted after each step of the build (`debug_folds`), so the step that makes them is
    found instead of their being laid flat afterwards. Each pair is put on the toe whose groups hold its first
    face (0: the rest of the foot)."""

    def __init__(self, topo, groups, n_verts):
        ls, lt, lv = topo
        if not np.all(lt == 4):
            raise ValueError("FoldCensus: quads only")
        self.F = lv.reshape(-1, 4)
        F = self.F
        e = np.concatenate([np.stack([F[:, a], F[:, b]], 1) for a, b in ((0, 1), (1, 2), (2, 3), (3, 0))])
        fid = np.tile(np.arange(len(F)), 4)
        key = np.minimum(e[:, 0], e[:, 1]) * (n_verts + 1) + np.maximum(e[:, 0], e[:, 1])
        order = np.argsort(key, kind="stable")
        ks, fs = key[order], fid[order]
        same = ks[1:] == ks[:-1]
        self.a, self.b = fs[:-1][same], fs[1:][same]
        W = np.stack([T.toe_weight(groups, k) for k in (1, 2, 3, 4, 5)], 1)
        wv = W[F[:, 0]]
        self.owner = np.where(wv.max(axis=1) > 0.5, wv.argmax(axis=1) + 1, 0)
        self.steps = {}

    def __call__(self, name, q):
        if name in getattr(self, "keep_steps", ()):
            self.kept[name] = np.asarray(q, np.float32).copy()
        F = self.F
        P_ = q[F]
        n = np.cross(P_[:, 2] - P_[:, 0], P_[:, 3] - P_[:, 1])
        n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
        bad = np.einsum("ij,ij->i", n[self.a], n[self.b]) < -0.5
        fa = self.a[bad]
        own = self.owner[fa]
        c = q[F[fa]].mean(axis=1)
        out = {"pairs": int(bad.sum()), "by_toe": {str(k): int((own == k).sum()) for k in range(6) if (own == k).any()}}
        if len(fa):
            out["y_range"] = [round(float(c[:, 1].min()), 1), round(float(c[:, 1].max()), 1)]
            out["z_range"] = [round(float(c[:, 2].min()), 1), round(float(c[:, 2].max()), 1)]
            # a few places, spread over the pairs (F mm)
            pick = np.linspace(0, len(fa) - 1, min(len(fa), 6)).astype(int)
            out["at"] = np.round(c[np.argsort(c[:, 1])][pick], 1).tolist()
        self.steps[name] = (out, np.unique(np.concatenate([self.a[bad], self.b[bad]])))
        print(f"[folds] {name}: {out}", flush=True)
        return out

    def save(self, path):
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        np.savez_compressed(path, **{f"faces_{k}": v[1] for k, v in self.steps.items()})
        return {k: v[0] for k, v in self.steps.items()}


def untangle(q, topo, groups, adj, ctx, P):
    """Round 5: folds of a few faces left on toes 1-2 unfolded. Under the hallux's free edge, at the front of the
    pulp's ellipsoid (macro.pulps grows the skin along its normals, and where the growth changes faster than 1:1
    across the front of the toe it folds), a row of faces 1.3 mm long lay turned over: a white fleck in clay and a
    dark slit in Cycles (round 4's m19, which the critics took for the plate piercing the hyponychium). Faces
    whose normal turns more than 120 degrees from a neighbour's are found, their vertices and `untangle_rings`
    rings round them smoothed by plain Laplacian passes (positions toward the neighbours' mean), which lays a fold
    of a few faces flat without moving anything else. Returns (positions, report)."""
    import macro as M
    w = T.toes_weight(groups) > 0.05
    ls, lt, lv = topo
    quads = lv.reshape(-1, 4) if np.all(lt == 4) else None
    if quads is None:
        return q, {"skipped": "not all quads"}
    mine = w[quads].any(axis=1)
    F = quads[mine]
    P_ = q[F]
    n = np.cross(P_[:, 2] - P_[:, 0], P_[:, 3] - P_[:, 1])
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    e = np.concatenate([np.stack([F[:, a], F[:, b]], 1) for a, b in ((0, 1), (1, 2), (2, 3), (3, 0))])
    fid = np.tile(np.arange(len(F)), 4)
    key = np.minimum(e[:, 0], e[:, 1]) * (len(q) + 1) + np.maximum(e[:, 0], e[:, 1])
    order = np.argsort(key, kind="stable")
    ks, fs = key[order], fid[order]
    same = ks[1:] == ks[:-1]
    a, b = fs[:-1][same], fs[1:][same]
    bad = (np.einsum("ij,ij->i", n[a], n[b]) < -0.5)
    bad_f = np.unique(np.concatenate([a[bad], b[bad]]))
    rep = {"folded_pairs": int(bad.sum()), "faces": int(len(bad_f))}
    if not len(bad_f):
        return q, rep
    if adj is None:
        edges, _ = C.edge_lengths(ctx.skin)
        adj = M.adjacency(edges, len(q))
    ptr, nb = adj
    deg = np.diff(ptr)
    row = np.repeat(np.arange(len(deg)), deg)
    zone = np.zeros(len(q))
    zone[np.unique(F[bad_f])] = 1.0
    for _ in range(int(P.get("untangle_rings", 4))):
        zone = np.maximum(zone, (np.bincount(row, zone[nb], minlength=len(deg)) > 0).astype(float))
    q = M.taubin(q, adj, zone, iterations=int(P.get("untangle", 0)), lam=0.5, mu=0.0)
    rep["vertices"] = int((zone > 0).sum())
    return q, rep


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


def orient_closed(nob):
    """Face normals outward on a closed shell (the free-edge sliver, round 5): by its signed volume. The
    area-weighted normal of a closed surface sums to zero, so orient_plate's test is a coin toss there (round
    5's first sliver rendered inside out)."""
    me = nob.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    loops = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", loops)
    start = np.empty(len(me.polygons), np.int64)
    total = np.empty(len(me.polygons), np.int64)
    me.polygons.foreach_get("loop_start", start)
    me.polygons.foreach_get("loop_total", total)
    vol = 0.0
    for k in range(2, int(total.max()) + 1):   # fan triangles (a, b_k-1, b_k) of each polygon
        sel = total >= k + 1
        a, b, c = co[loops[start[sel]]], co[loops[start[sel] + k - 1]], co[loops[start[sel] + k]]
        vol += float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6.0
    if vol < 0.0:
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
    mine = T.toes_weight(groups) > 0.02
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
    for k in (3, 4, 5):   # whole foot, pass 1: every toe has its nail in the method; part 01's plates only without
        if k not in ctx.plates:
            ctx.plates[k] = (bpy.data.objects[f"Foot.L.Nail.{k}"], None)
    write_nail_fields(skin, getattr(ctx, "nail_shade", {}))
    P = T.merged(ctx.params)
    import whole
    ctx.report["whole_masks"] = whole.write_masks(ctx, skin, q, groups, cw, P)
    if P.get("toe_sole", 0):
        ctx.report["toe_sole"] = soften_sole(skin, q, groups, P)
    if P.get("tint", 0):
        segs = T.segments(ctx.joints)
        nrm = C.vertex_normals(q, C.faces(skin))
        tint = tint_masks(q, nrm, segs, groups, cw, P)
        att = me.attributes.get("Hires.Tint")
        if att is not None:
            me.attributes.remove(att)
        me.attributes.new("Hires.Tint", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", tint.astype(np.float32).ravel())
        me.update()


def soften_sole(skin, q, groups, P):
    """Round 5 (critic round 4 m4: a crisp seam rings toe 2's underside, smooth and pinker above it, ridged
    below). Part 01's Foot.Sole is made on the 5 mm cage (plantar by the cage's normals, fading out between z 8
    and 14 mm), so under toe 2's curled PIP, where the cage's faces are squeezed into the fold, it steps from
    smooth skin to ridged sole skin within a fraction of a millimetre: the colour and texture half of the seam.
    On toes 1-2 it is taken from the dense normals as well (a pad's underside is plantar skin at any height)
    and diffused over a couple of millimetres (`toe_sole_smooth` Laplacian passes). Returns a report."""
    import macro as M
    topo = C.faces(skin)
    nrm = C.vertex_normals(q, topo)
    w = T.toes_weight(groups)
    old = C.group(skin, "Foot.Sole")
    plantar = T.smoothstep(-nrm[:, 2], 0.25, 0.6)
    new = old + (np.maximum(old, plantar) - old) * T.smoothstep(w, 0.3, 0.8)
    edges, _ = C.edge_lengths(skin)
    adj = M.adjacency(edges, len(q))
    arr = np.zeros((len(q), 3))
    arr[:, 0] = new
    arr = M.taubin(arr, adj, 0.9 * T.smoothstep(w, 0.2, 0.6), iterations=int(P.get("toe_sole_smooth", 40)), mu=0.0)
    C.set_group(skin, "Foot.Sole", np.clip(arr[:, 0], 0.0, 1.0))
    sel = w > 0.5
    return {"changed_max": round(float(np.abs(arr[sel, 0] - old[sel]).max()), 3),
            "changed_n": int((np.abs(arr[:, 0] - old) > 0.05).sum())}


def tint_masks(q, nrm, segs, groups, cw, P):
    """Round 5 (critic round 4 m26: one clean, even salmon from dorsum to tip): spec 01 §3.4's colour zones as
    (capillary, cool, crease) per vertex, Hires.Tint, which look.tint_skin reads. Capillary redness over the
    dorsal knuckles (the hallux's IP, toe 2's PIP and DIP, the first MTP faintly) and all round the toes' last
    millimetres; the faint blue-grey cast over the hallux's dorsum (#a89a95 at about 10 %); the creases
    (detail.crease and the plantar flexion creases) a little darker."""
    h1, h2, t2m, t2d = segs["h1"], segs["h2"], segs["t2m"], segs["t2d"]
    w1 = np.clip(groups["toe1-1.L"] + groups["toe1-2.L"], 0.0, 1.0)
    w2 = np.clip(groups["toe2-1.L"] + groups["toe2-2.L"] + groups["toe2-3.L"], 0.0, 1.0)
    up = T.smoothstep(nrm[:, 2], 0.05, 0.55)
    cap = np.zeros(len(q))
    ip = h2.point(P.get("ip_shift", 0.0), 0.0, 0.0)
    for c, r, amt in ((M.skin_top(q, ip[0], ip[1]), 7.5, 1.0), (M.skin_top(q, t2m.o[0], t2m.o[1]), 5.5, 1.0),
                      (M.skin_top(q, t2d.o[0], t2d.o[1]), 4.5, 0.7), (M.skin_top(q, h1.o[0], h1.o[1] - 3.0), 10.0, 0.35)):
        cap = np.maximum(cap, amt * M.sphere(q, c, r) * up)
    for seg, w, reach in ((h2, w1, 9.0), (t2d, w2, 6.5)):
        t = seg.local(q)[0]
        t_tip = float(t[w > 0.5].max())
        cap = np.maximum(cap, 0.85 * T.smoothstep(t, t_tip - reach, t_tip - 2.0) * w)
    # whole foot, pass 1: the lesser toes' knuckles and tips as toe 2's, a little less each toe outward
    for k, amt in ((3, 0.9), (4, 0.85), (5, 0.8)):
        tm, td = segs[f"t{k}m"], segs[f"t{k}d"]
        wk = T.toe_weight(groups, k)
        for c, r, a in ((M.skin_top(q, tm.o[0], tm.o[1]), 4.8, 1.0), (M.skin_top(q, td.o[0], td.o[1]), 3.8, 0.65)):
            cap = np.maximum(cap, amt * a * M.sphere(q, c, r) * up)
        t = td.local(q)[0]
        t_tip = float(t[wk > 0.5].max())
        cap = np.maximum(cap, 0.85 * amt * T.smoothstep(t, t_tip - 5.5, t_tip - 1.5) * wk)
    cool = w1 * T.smoothstep(nrm[:, 2], 0.25, 0.75)
    crease = np.clip(cw, 0.0, 1.0)
    return np.stack([cap, cool, crease], 1)


def write_nail_fields(skin, shade):
    """Round 5 (`continuous`): the fields the skin material shades the plates from (look.py), as point
    attributes: Hires.NailA (s, p, lunula: mm to the visible outline, negative inside; the proximal fold's
    share; the lunula's field), Hires.NailB (x, v, w: mm across, from the fold, past the bed's end) and
    Hires.NailC (the lunula's strength). Everywhere else s reads 9 mm, outside any nail."""
    n = len(skin.data.vertices)
    A = np.zeros((n, 3), np.float32)
    A[:, 0], A[:, 2] = 9.0, 9.0
    B = np.zeros((n, 3), np.float32)
    Cc = np.zeros((n, 3), np.float32)
    for k, f in sorted(shade.items()):
        idx = f["idx"]
        nearer = f["A"][:, 0] < A[idx, 0]
        i = idx[nearer]
        A[i], B[i] = f["A"][nearer], f["B"][nearer]
        Cc[i, 0], Cc[i, 1] = f["lunula_k"], float(k)
    me = skin.data
    for name, arr in (("Hires.NailA", A), ("Hires.NailB", B), ("Hires.NailC", Cc)):
        att = me.attributes.get(name)
        if att is not None:
            me.attributes.remove(att)
        if shade:
            me.attributes.new(name, "FLOAT_VECTOR", "POINT").data.foreach_set("vector", arr.ravel())
    me.update()


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


def webs_lesser(q, topo, segs, P, adj, groups, report=None):
    """Whole foot, pass 1: the 2-3, 3-4 and 4-5 webs by one closing, as web_by_closing does the 1-2 web (one
    level set of the forefoot, one dilation and erosion, so the three cost about what one does). Each cleft is
    measured just ahead of its commissure (`webs_lesser.y`, part 01's closed clefts): the toes' facing sides,
    which touch there (0.2-0.35 mm apart), so the half-gap is the floor's 0.5. The mask is full across the cleft
    (`band` mm either side), from just ahead of the commissure back over the toes' bases, and low (`z`): a closing
    by r fills every concavity narrower than 2 r, and between two touching toes that is a groove r^2 / R-ish
    high, so up on the dorsum it would fuse the proximal phalanges. Returns positions."""
    import sdf as S
    W = P.get("webs_lesser")
    if not W:
        return q
    clefts = []
    for (ka, kb), yw in zip(((2, 3), (3, 4), (4, 5)), W["y"]):
        y0 = yw - 3.0
        band = np.abs(q[:, 1] - y0) < 1.0
        # the whole toes' skin (3 mm ahead of the 4-5 commissure toe 5 is already past its proximal phalanx)
        x_lat = q[band & (T.toe_weight(groups, ka) > 0.5), 0].max()
        x_med = q[band & (T.toe_weight(groups, kb) > 0.5), 0].min()
        xm, half = 0.5 * (x_lat + x_med), max(0.5 * (x_med - x_lat), 0.5)
        clefts.append((float(xm), float(half), float(yw), float(segs[f"t{ka}p"].o[1])))
    full_w, fade_w = W.get("band", 1.6), W.get("fade", 3.0)
    z0, z1 = W.get("z", (15.0, 21.0))
    lo = (min(c[0] for c in clefts) - c_pad(clefts, full_w, fade_w), min(c[2] for c in clefts) - 10.0, -3.0)
    hi = (max(c[0] for c in clefts) + c_pad(clefts, full_w, fade_w), max(c[3] for c in clefts) + 16.0, z1 + 6.0)
    vox = W.get("voxel", 0.15)
    field = S.Field(q, topo[2].reshape(-1, 4), y_cut=-140.0, voxel=vox, half_mm=4.0)
    field.box(lo, hi)

    def mask(Pts):
        x, y, z = Pts[..., 0], Pts[..., 1], Pts[..., 2]
        m = np.zeros(x.shape)
        for xm, half, yw, my in clefts:
            full, fade = half + full_w, half + full_w + fade_w
            m = np.maximum(m, (1.0 - T.smoothstep(np.abs(x - xm), full, fade))
                           * T.window(y, yw - 3.5, yw + 0.5, my + 4.0, my + 10.0))
        return m * (1.0 - T.smoothstep(z, z0, z1))

    field.close(W.get("r", 1.6), mask)
    box = np.ones(len(q))
    for d in range(3):
        box *= T.window(q[:, d], lo[d] + 0.5, lo[d] + 2.0, hi[d] - 2.0, hi[d] - 0.5)
    inb = np.nonzero(box > 1e-4)[0]
    f0 = np.zeros(len(q))
    f0[inb] = np.nan_to_num(field.sample(q[inb]), nan=0.0)
    swallowed = T.smoothstep(-f0, 0.02, 0.12) * box
    q0 = q
    q = field.project(q, swallowed, iterations=8, h=vox, max_step=1.0)
    moved = np.linalg.norm(q - q0, axis=1)
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
        report["webs_lesser"] = {"clefts": [[round(c, 2) for c in cl] for cl in clefts],
                                 "moved_max": round(float(moved.max()), 2), "moved_n": int((moved > 0.05).sum())}
    return q


def c_pad(clefts, full_w, fade_w):
    """The box's margin across the clefts: the widest mask's reach and 4 mm."""
    return max(c[1] for c in clefts) + full_w + fade_w + 4.0


# the keys that act only after the large forms and the web (the nails and creases): a change to them reuses
# the cached stage (stage_key)
DETAIL_KEYS = ("nail1", "nail2", "crease_scale", "debug_sections", "stage_cache", "tint", "hair", "toe_sole",
               "toe_sole_smooth", "untangle", "untangle_rings", "crease2p_s", "crease2p_d", "crease2p_w",
               # whole foot, pass 1: everything whole.py and the lesser nails read acts after the stage
               "nail3", "nail4", "nail5", "tendons", "knuckles", "plantar_lesser", "ridges", "sheen", "corn",
               # whole foot, pass 2: the census, and whole.py's new forms and masks (all after the stage)
               "debug_folds", "contact", "arch", "achilles", "veins", "wear", "forms",
               # shape pass 2: whole.py's toe fill, sole and ankle crease (after the stage)
               "toe_fill", "sole", "ankle_crease",
               # the scan-driven pass: the dense sole's remaining difference from the scans (whole.scan_sole)
               "scan_sole")


def stage_key(q, P):
    """The large forms' and the web's inputs: the dense skin as copied, every other parameter and the sources
    of macro.py and sdf.py (web_by_closing's own code is not hashed: clear the cache if it changes)."""
    import hashlib
    import json
    import os
    h = hashlib.sha256(np.ascontiguousarray(q).tobytes())
    h.update(json.dumps({k: v for k, v in P.items() if k not in DETAIL_KEYS}, sort_keys=True, default=str).encode())
    for f in ("macro.py", "sdf.py", "scanxfer.py", os.path.join("..", "..", "parts", "p01", "transfer.py")):
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
    # whole foot, pass 2: `debug_folds` counts the folded face pairs after every step (FoldCensus)
    census = FoldCensus(topo, groups, len(q)) if P.get("debug_folds") else (lambda name, q_: None)
    if P.get("debug_folds") and P.get("debug_keep"):
        # the skin at the named steps, the toes' weights and the faces, for sections offline (dbg_steps.npz)
        census.keep_steps, census.kept = tuple(P["debug_keep"]), {}
    ctx.census = census
    census("dense", q)
    # the large forms and the web take about 150 s, the nails 6: with `stage_cache` (default on) the skin
    # after them is kept in cache/research/foot_hires/stage_<key>.npz, so a nail-only change rebuilds in seconds
    path = os.path.join(C.CACHE, f"stage_{stage_key(q, P)}.npz") if P.get("stage_cache", 1) else None
    if path and os.path.exists(path):
        with np.load(path) as z:
            q = z["q"]
            ctx.report.update(json.loads(str(z["report"])))
        ctx.report["stage_cache"] = os.path.basename(path)
        census("stage_cached", q)
    else:
        t1 = time.time()
        edges, _ = C.edge_lengths(skin)
        adj = M.adjacency(edges, len(q))
        q = M.close_folds(q, segs, groups, P, adj, ctx.report)
        census("close_folds", q)
        # the scan transfer (2026-10-17): the dense skin laid on the scan part 01's cage was fitted to (scanxfer.py),
        # before the nails and the other detail; the large-form edits it supersedes are off in toes.PARAMS
        import scanxfer
        q = scanxfer.apply(ctx, q, topo, P, ctx.report)
        census("scan_transfer", q)
        q = M.apply(q, C.vertex_normals(q, topo), segs, groups, adj, P, ctx.report)
        census("macro_apply", q)
        q = M.pulps(q, C.vertex_normals(q, topo), segs, groups, P, ctx.report)
        census("pulps", q)
        q = M.deepen(q, segs, groups, P, ctx.report)
        census("deepen", q)
        q = M.toe5_form(q, segs, groups, P, ctx.report)
        census("toe5_form", q)
        ctx.report["t_macro"] = round(time.time() - t1, 2)
        if P.get("web_sdf"):
            t1 = time.time()
            q = web_by_closing(q, topo, segs, P, adj, groups, ctx.report)
            ctx.report["t_web_sdf"] = round(time.time() - t1, 2)
            census("web_1_2", q)
        if P.get("webs_lesser"):
            t1 = time.time()
            q = webs_lesser(q, topo, segs, P, adj, groups, ctx.report)
            ctx.report["t_webs_lesser"] = round(time.time() - t1, 2)
            census("webs_lesser", q)
        if path:
            os.makedirs(C.CACHE, exist_ok=True)
            keep = {k: ctx.report[k] for k in ("anchors", "pulps", "web", "toe2_outline", "fold_close", "deepen", "t_macro",
                                               "t_web_sdf", "toe5_form", "webs_lesser", "t_webs_lesser", "scan_transfer")
                    if k in ctx.report}
            np.savez(path, q=q, report=json.dumps(keep))
    # whole foot, pass 1: the long extensors after the webs (whole.tendons), so a tendon change keeps the stage
    import whole
    # pass 2: the touching toes' contact, the arch, the Achilles (whole.forms), and the veins after the tendons
    t1 = time.time()
    ctx.q_stage = q
    if P.get("forms", 1):
        q = whole.forms(ctx, q, topo, groups, segs, P)
    ctx.q_forms = q
    ctx.report["t_forms"] = round(time.time() - t1, 2)
    census("forms", q)
    t1 = time.time()
    q, ctx.tendon_mask = whole.tendons(q, C.vertex_normals(q, topo), segs, groups, ctx.joints, P, ctx.report)
    ctx.report["t_tendons"] = round(time.time() - t1, 2)
    census("tendons", q)
    t1 = time.time()
    q, ctx.vein_mask = whole.veins(q, C.vertex_normals(q, topo), P, ctx.report)
    ctx.report["t_veins"] = round(time.time() - t1, 2)
    census("veins", q)
    t1 = time.time()
    q, beds, cw, _ = nails_and_creases(ctx, q, topo, groups, segs, P)
    ctx.report["t_detail"] = round(time.time() - t1, 2)
    census("final", q)
    if P.get("debug_folds"):
        ctx.report["folds"] = census.save(os.path.join(C.CACHE, "folds_census.npz"))
        if getattr(census, "kept", None):
            W = np.stack([T.toe_weight(groups, k) for k in (1, 2, 3, 4, 5)], 1).astype(np.float32)
            np.savez(os.path.join(C.CACHE, "dbg_steps.npz"), faces=census.F.astype(np.int32), toe_w=W,
                     joints=json.dumps({k: np.asarray(v).tolist() for k, v in ctx.joints.items()}),
                     **{f"q_{k}": v for k, v in census.kept.items()})
    finish(ctx, q, beds, cw, groups)
    if P.get("hair", 0):
        import hair
        ctx.report["hair"] = hair.build(ctx, q, C.vertex_normals(q, topo), segs, groups)
    ctx.report["params"] = P
    ctx.report["joints"] = {k: np.round(v, 2).tolist() for k, v in ctx.joints.items() if k.startswith("toe-")}
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
