"""Head shape round 5 (scripts/parts/head.md §13.5): a sculpt on top of round 4, for the hero view (not wired).

Round 4's §11.7 item 1: in the hero view the face is fuller than the drawing's (the cheeks hollow less under the
cheekbones, the chin is broader, the near jaw line sits lower), and round 10 found the orbit under the brow so
deep that the key never reaches the upper lid or the eye (the "dark, empty sockets"). Rounds 2-4 were fits; this
one is five explicit local displacement fields on round 4's face, each measured before rendering:

  hood     the skin between the brow and the upper lid's margin comes forward (a hooded lid: analysis §5)
  hollow   the cheek under the zygoma sits in, along the surface normal
  chin     the chin narrows towards the midline
  jaw      the mandible's lower border, chin to angle, rises (and the jowl with it)
  crease   round 4's hard groove from beside the nose to the mouth corner is relaxed

Only skin vertices of the face move: no helper geometry, no joint cube, so base.py's rig, eye bones and MHCLO
fits come out unchanged and the pose stays valid. Developed on copies in memory (a shape key on an opened
base.blend, never saved); `head-shape.target` and base.py are untouched.

  "$SGT_BLENDER" -b --python scripts/parts/head_shape_r5.py -- --measure     # r4 against r5, cache/head_r5/measure.json
  "$SGT_BLENDER" -b --python scripts/parts/head_shape_r5.py -- --write       # scripts/parts/head-shape-r5.target
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
SCRIPTS = os.path.join(PROJECT, "scripts")
for p in (SCRIPTS, HERE, os.path.join(SCRIPTS, "stages")):
    if p not in sys.path:
        sys.path.insert(0, p)

WORK = os.path.join(PROJECT, "cache", "head_r5")
R4_TARGET = os.path.join(HERE, "head-shape-r4.target")
R5_TARGET = os.path.join(HERE, "head-shape-r5.target")
R5_JSON = os.path.join(HERE, "head_shape_r5.json")
REF_CROP = os.path.join(PROJECT, "ref", "crop_head_face.png")
JAW_MARKS = os.path.join(HERE, "head_jaw_marks.json")
FACE_TARGETS = os.path.join(SCRIPTS, "stages", "face_targets.json")
CROP_BOX, CROP_SCALE = (715, 30, 885, 200), 5.0

P5 = {
    "hood_mm": 4.5, "hood_sx": 15.0, "hood_sz": 4.8,
    "lid_mm": 0.3,
    "hollow_mm": 3.2, "hollow_sigma": 13.0,
    "chin_k": 0.16, "chin_sz": 16.0,
    "jaw_up_mm": 4.0, "jaw_in_mm": 3.0, "jaw_sigma": 11.0,
    "taper_mm": 2.4, "taper_sz": 20.0,
    "crease_iters": 8, "crease_sigma": 7.0,
    "smooth_iters": 2,
}


def _ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _seg_dist(V, A, B):
    ab = B - A
    t = np.clip(((V - A) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(V - (A + t[:, None] * ab), axis=1)


def delta(C, bd, marks, P=P5):
    """The round-5 displacement of round 4's face, world mm, per Body.Mesh vertex (0 off the face's skin)."""
    import head as H
    import head_look as HL
    V, N, g = bd["V"], bd["N"], bd["groups"]
    region = H.head_region(bd) & bd["in_body"] & (g["ears"] < 0.3)
    L = HL.landmarks(bd, marks)
    E = C.edges_of(bd["F"])
    D = np.zeros_like(V)
    parts = {}
    sx = np.where(V[:, 0] >= 0, 1.0, -1.0)
    Vr = np.stack([-np.abs(V[:, 0]), V[:, 1], V[:, 2]], 1)          # every vertex folded onto his right (x < 0)
    # --- hood: between the brow's lower row and the upper lid margin, strongest on the lateral half
    bm, bo, bi = L["brow_mid"], L["brow_out"], L["brow_in"]
    lid_top = L["pupil"][2] + 4.5                                       # about the upper lid's margin
    zc = 0.5 * (bm[2] + lid_top) + 0.5
    xc = 0.5 * (bm[0] + bo[0]) + 6.0
    w = np.exp(-0.5 * ((Vr[:, 0] - xc) / P["hood_sx"]) ** 2 - 0.5 * ((V[:, 2] - zc) / P["hood_sz"]) ** 2)
    w *= _ss(L["pupil"][1] + 16.0, L["pupil"][1] + 4.0, V[:, 1]) * _ss(bi[0] + 3.0, bi[0] - 6.0, Vr[:, 0])
    w *= _ss(lid_top - 1.5, lid_top + 3.0, V[:, 2])                     # the lid margin itself stays on the eye
    parts["hood"] = w[:, None] * np.array([0.0, -1.0, -0.25]) * P["hood_mm"]
    # --- lid: the upper lid's margin comes down over the eyeball (the drawn eyes are narrowed: aspect 0.28)
    import bpy
    eo = bpy.data.objects.get("Body.Eyes")
    parts["lid"] = np.zeros_like(V)
    if eo is not None and P["lid_mm"] > 0:
        EV = np.array([v.co[:] for v in eo.data.vertices]) * 1000.0
        Q = EV[EV[:, 0] < 0]
        A = np.c_[2 * Q, np.ones(len(Q))]
        sol = np.linalg.lstsq(A, (Q ** 2).sum(1), rcond=None)[0]
        ce = sol[:3]
        re = float(np.sqrt(sol[3] + ce @ ce))
        rr = np.linalg.norm(Vr - ce, axis=1)
        w = np.exp(-0.5 * ((Vr[:, 2] - (ce[2] + 3.2)) / 2.4) ** 2 - 0.5 * ((Vr[:, 0] - ce[0]) / 12.0) ** 2)
        w *= _ss(re + 3.0, re + 0.8, rr) * (Vr[:, 1] < ce[1] - 8.0)
        q = Vr + np.array([0.0, 0.0, -P["lid_mm"]]) * w[:, None]
        q = ce + (q - ce) * (rr / np.maximum(np.linalg.norm(q - ce, axis=1), 1e-9))[:, None]
        dl = q - Vr
        dl[:, 0] *= np.where(V[:, 0] > 0, -1.0, 1.0)
        parts["lid"] = dl
    # --- hollow: under the zygoma, outside the mouth corner
    mo, sn = L["mouth"], L["subnasale"]
    c = np.array([mo[0] - 24.0, 0.0, 0.5 * (mo[2] + sn[2]) + 5.0])
    k = np.argmin(np.where(region & (V[:, 0] < 0), np.hypot(V[:, 0] - c[0], V[:, 2] - c[2]) + 0.5 * np.maximum(V[:, 1] + 60.0, 0), 1e9))
    c = V[k]
    w = np.exp(-0.5 * (np.linalg.norm(Vr - c, axis=1) / P["hollow_sigma"]) ** 2)
    parts["hollow"] = -N * (w * P["hollow_mm"])[:, None]
    parts["_hollow_centre"] = c
    # --- chin: narrower
    ch, lb = L["chin"], L["lip_bot"]
    w = np.exp(-0.5 * ((V[:, 2] - (ch[2] + 9.0)) / P["chin_sz"]) ** 2) * _ss(ch[1] + 55.0, ch[1] + 20.0, V[:, 1]) * _ss(lb[2] + 2.0, lb[2] - 6.0, V[:, 2])
    w *= _ss(52.0, 30.0, np.abs(V[:, 0]))
    parts["chin"] = np.stack([-P["chin_k"] * V[:, 0] * w, np.zeros(len(V)), np.zeros(len(V))], 1)
    # --- jaw: the lower border from beside the chin to the angle rises and tucks in
    ear = np.array(marks["ear_R"]["rest_mm"])
    gon = np.array([-abs(ear[0]) + 14.0, ear[1] + 3.0, ch[2] + 44.0])   # round 4's triangulated gonion: (+-73, -36, 1636)
    a0 = np.array([-24.0, ch[1] + 14.0, ch[2] + 4.0])
    a1 = np.array([0.5 * (a0[0] + gon[0]) - 6.0, 0.5 * (a0[1] + gon[1]) - 6.0, ch[2] + 17.0])
    dj = np.minimum(_seg_dist(Vr, a0, a1), _seg_dist(Vr, a1, gon))
    w = np.exp(-0.5 * (dj / P["jaw_sigma"]) ** 2) * _ss(lb[2] + 6.0, lb[2] - 8.0, V[:, 2])
    parts["jaw"] = np.stack([-sx * P["jaw_in_mm"] * w, np.zeros(len(V)), P["jaw_up_mm"] * w], 1)
    # --- taper: the lower cheek and jaw come in towards the midline (the far cheek's outline, rows 110-124)
    w = np.exp(-0.5 * ((V[:, 2] - (ch[2] + 40.0)) / P["taper_sz"]) ** 2) * _ss(38.0, 58.0, np.abs(V[:, 0])) * _ss(ear[1] - 2.0, ear[1] - 20.0, V[:, 1])
    parts["taper"] = np.stack([-sx * P["taper_mm"] * w, np.zeros(len(V)), np.zeros(len(V))], 1)
    for kk in ("hood", "lid", "hollow", "chin", "jaw", "taper"):
        D += parts[kk] * region[:, None]
    # --- crease: relax the groove from beside the nose down to the mouth corner (positions, masked)
    ala = L["ala"]
    b0 = np.array([ala[0] - 2.0, ala[1] + 6.0, L["pupil"][2] - 16.0])
    b1 = np.array([ala[0] - 7.0, ala[1] + 3.0, ala[2] - 4.0])
    b2 = np.array([mo[0] - 6.0, mo[1] + 1.0, mo[2] + 3.0])
    dc = np.minimum(_seg_dist(Vr, b0, b1), _seg_dist(Vr, b1, b2))
    m = np.exp(-0.5 * (dc / P["crease_sigma"]) ** 2) * region * (g["lips"] < 0.3)
    X = V + D
    for _ in range(P["crease_iters"]):
        X = X + m[:, None] * 0.5 * (C.smooth_field(X, E, iters=1, lam=1.0) - X)
    parts["crease"] = (X - (V + D))
    D = X - V
    # symmetric, smooth, nothing off the skin
    for _ in range(P["smooth_iters"]):
        D = D + 0.5 * (C.smooth_field(D, E, iters=1, lam=1.0) - D) * region[:, None]
    D[~region] = 0.0
    stats = {k: {"max_mm": round(float(np.linalg.norm(v, axis=1).max()), 2), "verts": int((np.linalg.norm(v, axis=1) > 0.1).sum())}
             for k, v in parts.items() if not k.startswith("_")}
    stats["total"] = {"max_mm": round(float(np.linalg.norm(D, axis=1).max()), 2), "verts": int((np.linalg.norm(D, axis=1) > 0.05).sum()),
                      "asymmetry_mm": None}
    return D, stats, L


def apply_dev(body, D_mm, name="head-shape-r5-dev"):
    """The displacement as a shape key at 1.0 on the opened Body.Mesh (in memory; the file is never saved)."""
    me = body.data
    kb = me.shape_keys.key_blocks.get(name)
    if kb is not None:
        body.shape_key_remove(kb)
    kb = body.shape_key_add(name=name, from_mix=False)
    base = me.shape_keys.reference_key
    n = len(me.vertices)
    co = np.empty(n * 3)
    base.data.foreach_get("co", co)
    Minv = np.linalg.inv(np.array(body.matrix_world)[:3, :3])
    co = co.reshape(-1, 3) + (D_mm / 1000.0) @ Minv.T
    kb.data.foreach_set("co", co.ravel())
    kb.value = 1.0
    me.update()
    return kb


# =========================================================================== measures (the hero view, posed)

def ref_far_cheek():
    """head_shape.ref_edges' hero edge without PIL: the last pixel from the right brighter than 70 in luminance,
    crop columns 425-700, rows 190-470 -> (full-frame y, x)."""
    import bpy
    img = bpy.data.images.load(REF_CROP)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    a = px.reshape(h, w, 4)[::-1, :, :3]
    lum = (a * 255.0) @ np.array([0.2126, 0.7152, 0.0722])      # a byte image's pixels are its own sRGB values
    fg = lum > 70.0
    ys, xs = [], []
    for y in range(190, 471):
        cc = np.where(fg[y, 425:700])[0]
        if len(cc):
            ys.append(30.0 + y / 5.0)
            xs.append(715.0 + (425 + cc[-1] + 0.5) / 5.0)
    xs = np.array(xs)
    med = np.array([np.median(xs[max(0, i - 2):i + 3]) for i in range(len(xs))])
    return np.array(ys), med


def posed(C, body, bd):
    """Posed world positions (m) of every Body.Mesh vertex (its own indices), and posed normals."""
    import bpy
    mask = [m for m in body.modifiers if m.type == "MASK"]
    saved = [(m, m.show_viewport) for m in mask]
    for m in mask:
        m.show_viewport = False
    try:
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = body.evaluated_get(dg)
        me = ev.to_mesh()
        n = len(me.vertices)
        co = np.empty(n * 3)
        me.vertices.foreach_get("co", co)
        no = np.empty(n * 3)
        me.vertices.foreach_get("normal", no)
        ev.to_mesh_clear()
    finally:
        for m, v in saved:
            m.show_viewport = v
    mw = np.array(body.matrix_world)
    return co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3], no.reshape(-1, 3) @ np.linalg.inv(mw[:3, :3])


def _rot(v):
    th = np.linalg.norm(v)
    if th < 1e-12:
        return np.eye(3)
    k = v / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def measure(C, body, rig, bd, marks, tag):
    """Hero-view numbers for the face now on Body.Mesh (the rig in the hero pose)."""
    import head as H
    from eval import camproj
    V, g = bd["V"], bd["groups"]
    region = H.head_region(bd) & bd["in_body"]
    W, Nw = posed(C, body, bd)
    xy = camproj.project(W)
    out = {"tag": tag}
    # 1. the far cheek against the dark background (head_shape.sil_hero's measure, rows 68-124)
    ys, xs = ref_far_cheek()
    face = region & (g["ears"] < 0.3)
    Ed = np.array([e for e in C.edges_of(bd["F"]) if face[e[0]] and face[e[1]]])
    ya, yb = xy[Ed[:, 0], 1], xy[Ed[:, 1], 1]
    lo, hi = np.minimum(ya, yb), np.maximum(ya, yb)
    res = []
    for y0 in np.arange(68.0, 124.0, 0.6):
        k = np.where((lo <= y0) & (hi > y0))[0]
        if not len(k):
            continue
        t = (y0 - ya[k]) / np.where(yb[k] != ya[k], yb[k] - ya[k], 1.0)
        x = (xy[Ed[k, 0], 0] * (1 - t) + xy[Ed[k, 1], 0] * t).max()
        res.append((y0, x - np.interp(y0, ys, xs)))
    res = np.array(res)
    out["far_cheek_px"] = {"rms": round(float(np.sqrt((res[:, 1] ** 2).mean())), 2), "mean": round(float(res[:, 1].mean()), 2),
                           "rows": int(len(res)),
                           "by_band_mean": {f"{int(a)}-{int(b)}": round(float(res[(res[:, 0] >= a) & (res[:, 0] < b), 1].mean()), 2)
                                            for a, b in ((68, 82), (82, 96), (96, 110), (110, 124))}}
    # 2. the face landmarks at fixed mesh points (face_targets.json) and the rigid head turn they ask for
    ft = json.load(open(FACE_TARGETS, encoding="utf-8"))["landmarks"]
    Pl = np.array([(W[l["verts"]] * np.array(l["bary"])[:, None]).sum(0) for l in ft])
    ref = np.array([l["ref_px"] for l in ft])
    wt = np.array([l.get("weight", 1.0) for l in ft])
    r0 = camproj.project(Pl) - ref
    out["landmarks_px"] = {"rms": round(float(np.sqrt((wt[:, None] * r0 ** 2).sum() / wt.sum())), 2), "n": int(len(ft))}
    hb = rig.pose.bones["head"]
    piv = np.array(rig.matrix_world @ hb.head)
    x = np.zeros(3)

    def resid(x):
        return ((camproj.project(piv + (Pl - piv) @ _rot(x).T) - ref) * np.sqrt(wt)[:, None]).ravel()
    for _ in range(12):
        r = resid(x)
        J = np.stack([(resid(x + np.eye(3)[i] * 1e-4) - r) / 1e-4 for i in range(3)], 1)
        x = x - np.linalg.solve(J.T @ J + 1e-9 * np.eye(3), J.T @ r)
    r = resid(x)
    Rm = _rot(x)
    # the turn's part about the vertical: positive = towards his left (+X side, anticlockwise from above)
    fwd = np.array([0.0, -1.0, 0.0])
    f1 = Rm @ fwd
    yaw_more = float(np.degrees(np.arctan2(f1[0], -f1[1])))
    pitch_more = float(np.degrees(np.arcsin(np.clip(f1[2], -1, 1))))
    out["rigid_head_fit"] = {"rms_px": round(float(np.sqrt((r ** 2).sum() / wt.sum())), 2), "yaw_more_deg": round(yaw_more, 2),
                             "pitch_up_more_deg": round(pitch_more, 2), "rotvec_deg": [round(float(np.degrees(v)), 2) for v in x]}
    # the head's yaw now: the head bone's forward (its rest forward is -Y) against the world's -Y
    Mh = np.array((rig.matrix_world @ hb.matrix).to_3x3()) @ np.linalg.inv(np.array(rig.data.bones["head"].matrix_local.to_3x3()))
    fnow = Mh @ fwd
    yaw_now = float(np.degrees(np.arctan2(fnow[0], -fnow[1])))
    out["head_yaw_deg"] = {"now": round(yaw_now, 2), "face_wants": round(yaw_now + yaw_more, 2)}
    # 3. the jaw's lower border in the hero crop (head_jaw_marks.json hero_crop: the top and bottom of the dark
    # band under the jaw): per mark column, the first and last visible under-jaw face (normal turned down)
    jm = json.load(open(JAW_MARKS, encoding="utf-8"))["hero_crop"]
    F3 = [f for f in bd["F"] if region[list(f)].all()]
    cen = np.array([W[list(f)].mean(0) for f in F3])
    fn = np.array([Nw[list(f)].mean(0) for f in F3])
    fn /= np.linalg.norm(fn, axis=1, keepdims=True)
    cxy = camproj.project(cen)
    cam = np.array(camproj.HERO_LOC)
    facing = ((cam - cen) * fn).sum(1) > 0
    lip_px = camproj.project(np.array([(W[l["verts"]] * np.array(l["bary"])[:, None]).sum(0) for l in ft if l["mp"] == 17]))
    y_lip = float(lip_px[0, 1]) if len(lip_px) else 0.0
    under = facing & (fn[:, 2] < -0.35) & (cxy[:, 1] > y_lip + 1.5)
    rows = {"top": [], "bottom": []}
    for (mx, my_top), (_, my_bot) in zip(jm["jaw_border_top"], jm["underjaw_crease"]):
        fx = CROP_BOX[0] + mx / CROP_SCALE
        k = under & (np.abs(cxy[:, 0] - fx) < 1.6) & (cxy[:, 1] > CROP_BOX[1] + (my_top - 90) / CROP_SCALE) & (cxy[:, 1] < CROP_BOX[1] + (my_bot + 90) / CROP_SCALE)
        if k.sum() < 1:
            continue
        rows["top"].append(np.percentile(cxy[k, 1], 10) - (CROP_BOX[1] + my_top / CROP_SCALE))
        rows["bottom"].append(cxy[k, 1].max() - (CROP_BOX[1] + my_bot / CROP_SCALE))
    out["jaw_band_px"] = {k: {"mean": round(float(np.mean(v)), 2), "per_mark": [round(float(q), 2) for q in v]} for k, v in rows.items() if v}
    out["jaw_band_px"]["note"] = "model - drawn, full-frame px, + = lower in the image; near side (his right) first"
    # 4. rest breadths above the menton, in front of the ears
    ch = np.array(marks["chin"]["rest_mm"])
    ear_y = marks["ear_R"]["rest_mm"][1]
    br = {}
    for dz in (10.0, 20.0, 38.0):
        s = region & (np.abs(V[:, 2] - (ch[2] + dz)) < 3.0) & (V[:, 1] < ear_y - 5.0)
        br[f"{int(dz)}mm_above_menton"] = round(float(2 * np.abs(V[s, 0]).max()), 1) if s.any() else None
    out["breadth_mm"] = br
    return out


def flips(Va, Vb, F, keep):
    n = 0
    for f in F:
        if not keep[list(f)].all():
            continue
        a = np.cross(Va[f[1]] - Va[f[0]], Va[f[2]] - Va[f[0]])
        b = np.cross(Vb[f[1]] - Vb[f[0]], Vb[f[2]] - Vb[f[0]])
        if a @ b < 0:
            n += 1
    return n


def main(argv):
    import bpy
    import common as C
    import head as H
    import head_shape as HS
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(WORK, exist_ok=True)
    body, rig = C.open_base()
    bd = C.body_data(body)
    marks = C.base_json()["landmarks"]
    D, stats, L = delta(C, bd, marks)
    stats["total"]["asymmetry_mm"] = "symmetric by construction (fields of |x|)"
    print("[r5] delta", json.dumps(stats), flush=True)
    rec = {"params": P5, "delta": stats, "base": "cache/stages/base.blend (round 4's face, stature 1844), scripts/stages/hero_pose.json"}
    if a.measure:
        C.apply_hero_pose(rig)
        bpy.context.view_layer.update()
        rec["r4"] = measure(C, body, rig, bd, marks, "r4")
        C.rest_pose(rig)
        apply_dev(body, D)
        bd5 = C.body_data(body)
        region = H.head_region(bd) & bd["in_body"]
        rec["flipped_vs_r4"] = flips(bd["V"], bd5["V"], bd["F"], region)
        rec["applied_max_mm"] = round(float(np.linalg.norm(bd5["V"] - bd["V"], axis=1).max()), 2)
        C.apply_hero_pose(rig)
        bpy.context.view_layer.update()
        rec["r5"] = measure(C, body, rig, bd5, marks, "r5")
        with open(os.path.join(WORK, "measure.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1)
        for k in ("r4", "r5"):
            print(f"[r5] {k}", json.dumps(rec[k]), flush=True)
        print("[r5] flipped", rec["flipped_vs_r4"], "applied max", rec["applied_max_mm"], flush=True)
    if a.write:
        n = len(bd["V"])
        D4 = HS.read_target(n, R4_TARGET)
        HS.write_target(D4 + D, R5_TARGET, "head round 5 (head_shape_r5.py): round 4 plus the hero-view sculpt")
        with open(R5_JSON, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1)
        print("[r5] wrote", R5_TARGET, flush=True)
    return 0


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
        rc = main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    except Exception:
        import traceback
        traceback.print_exc()
        rc = 1
    sys.stdout.flush()
    os._exit(rc)
