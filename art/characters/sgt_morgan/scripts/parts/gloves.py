"""Gloves, round 1 blockout: a pair of hard-knuckle tactical gloves (Mechanix M-Pact class: stretch knit back,
synthetic leather palm, one-piece moulded TPR knuckle guard, TPR PIP pads, a neoprene cuff closing with a
hook-and-loop tab), fitted to the MPFB hands. Notes: scripts/parts/gloves.md.

  "$SGT_BLENDER" -b --python scripts/parts/gloves.py [-- --no-render]
  -> cache/parts/gloves.blend (Part.Gloves: Glove.{L,R}.Shell, .Knuckle, .Pad.{2..5}), cache/parts/gloves.json,
     renders/gloves/*.png

Shell: the hand skin and the forearm up to 50 mm proximal of the wrist joint, refined, pushed out 1.8 mm
(knit 1.2 + air; capped between the fingers by the gap test) and 11 mm over the cuff (3.5 air over the
shirt cuff + 3 neoprene + the sleeve itself), smoothed lightly, cut at the cuff edge. Knuckle guard and PIP
pads: sheets laid on the glove shell from above the back of the hand (rays down onto it), with a flat top
and four bosses over the knuckles. All take weights from the body.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PART, TAG = "Glove", "gloves"
HAND_EASE, CUFF_EASE = 1.8, 11.0
CUFF_LEN = 50.0                         # cuff edge, mm proximal of the wrist joint (M-Pact ~ 50)
GUARD = {"half_w": 46.0, "half_h": 17.0, "thick": 4.5, "boss": 2.0, "back": 16.0}   # 92 x 34 x 6.5 (M-Pact 3 class: ~95 x 35 x 6)
PAD = {"half_w": 9.0, "half_h": 8.0, "thick": 2.5}
COLOURS = {"knit": "#1e1c1b", "cuff": "#1b1c1e", "guard": "#2f2c2a", "pad": "#2a2826", "palm": "#232120"}
# Materials round (round 5, 2026-11-15; the solid-view colours above stay): an M-Pact-class glove is a black
# stretch-knit back, a synthetic-leather palm (the shell's faces that look out of the palm side, palm_faces()),
# a neoprene cuff, TPR knuckle guard and PIP pads. The right hand (on the grip, the knuckles up) the dustier.
MATERIALS = {
    "Glove.Mat.Knit": ("Knit.Glove.Honeycomb", "Knit", {}),
    "Glove.Mat.Palm": ("Leather.Glove.Goat", "Palm", {}),
    "Glove.Mat.Cuff": ("Neoprene.Black", "Cuff", {}),
    "Glove.Mat.Guard": ("TPR.Glove.Black", "Guard", {}),
    "Glove.Mat.Pad": ("TPR.Glove.Black", "Pad", {"dust__amount": 0.5}),
}


def palm_faces(V, F, fc, side):
    """Face materials with the palm (2) on knit faces (0) whose normal looks out of the palm side of the hand
    (against the hand frame's z, the back of the hand) by more than 0.25."""
    _, _, _, z, _ = hand_frame(side)
    V = np.asarray(V, float)
    fc = np.array(fc, np.int32)
    N, Cn = [], []
    for f in F:
        p = V[list(f)]
        n = np.cross(p[1] - p[0], p[-1] - p[0])
        N.append(n / max(np.linalg.norm(n), 1e-12))
        Cn.append(p.mean(0))
    N, Cn = np.array(N), np.array(Cn)
    # the shell's winding: outward when the normals point away from the shell's own centroid on the whole
    if np.einsum("ij,ij->i", N, Cn - Cn.mean(0)).sum() < 0:
        N = -N
    fc[(fc == 0) & (N @ z < -0.25)] = 2
    return fc


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def hand_frame(side):
    """Origin at the knuckle line's centre, x across the knuckles (index -> little), y along the fingers,
    z out of the back of the hand."""
    heads = np.array([C.bone_mm(f"finger{k}-1.{side}") for k in (2, 3, 4, 5)])
    O = heads.mean(0)
    x = heads[3] - heads[0]
    x /= np.linalg.norm(x)
    y = C.bone_mm(f"finger3-1.{side}", "tail") - C.bone_mm(f"metacarpal3.{side}")
    y -= x * (y @ x)
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    thumb = C.bone_mm(f"finger1-3.{side}", "tail")
    if (thumb - O) @ z > 0:                       # the thumb lies on the palm side
        z = -z
    return O, x, y, z, heads


def build_shell(bd, side, bvh0):
    V0 = bd["V"]
    sg = 1.0 if side == "L" else -1.0
    el, wr = C.bone_mm(f"lowerarm01.{side}"), C.bone_mm(f"wrist.{side}")
    d = (wr - el) / np.linalg.norm(wr - el)
    hand = C.weight_sum(bd, C.is_hand)
    fore = C.weight_sum(bd, lambda n: n.startswith("lowerarm"))
    s0 = (V0 - wr) @ d
    keep = bd["in_body"] & (np.sign(V0[:, 0]) == sg) & ((hand > 0.3) | ((fore > 0.3) & (s0 > -CUFF_LEN - 40)))
    V, F, _ = C.submesh(V0, bd["F"], keep)
    V, F = C.bisect(V, F, wr - d * (CUFF_LEN + 20), d, keep="above")
    V, F, N = C.refine_on_skin(V, F, bvh0, cuts=1)
    s = (V - wr) @ d
    off = HAND_EASE + (CUFF_EASE - HAND_EASE) * (1 - smoothstep(4.0, 26.0, s))
    off = C.limit_by_gap(V, N, off, bvh0, share=0.5, floor=0.6)
    E = C.edges_of(F)
    off = C.smooth_field(off, E, iters=3)
    V1 = V + N * off[:, None]
    V1, F, ex = C.bisect(V1, F, wr - d * CUFF_LEN, d, keep="above", extra=s[:, None])
    E = C.edges_of(F)
    V1 = C.despike(V1, E, factor=2.0)
    V1 = C.taubin(V1, E, iters=4, lam=0.5, mu=-0.53, pin=C.boundary_verts(F, len(V1)))
    V1 = C.push_out(V1, bvh0, np.maximum(0.6 * HAND_EASE, 0.8))
    s1 = (V1 - wr) @ d
    face_cuff = [1 if s1[list(f)].mean() < 6.0 else 0 for f in F]
    return V1, F, face_cuff


def plate_on(bvh, O, x, y, z, half_w, half_h, thick, bumps=(), nu=28, nv=12, edge=5.0):
    """A sheet over the glove: a grid in the (x, y) plane of the hand frame, rays down -z onto the shell,
    raised by 0.6 + thick x a flat-topped profile (+ bosses: (u, v, radius, height))."""
    from mathutils import Vector
    us, vs = np.linspace(-half_w, half_w, nu + 1), np.linspace(-half_h, half_h, nv + 1)
    V = []
    for v in vs:
        for u in us:
            P0 = O + x * u + y * v + z * 60.0
            hit = bvh.ray_cast(Vector(P0), Vector(-z), 120.0)
            p = np.array(hit[0]) if hit[0] is not None else O + x * u + y * v
            du = max(0.0, abs(u) - (half_w - edge)) / edge
            dv = max(0.0, abs(v) - (half_h - edge)) / edge
            q = min(1.0, math.hypot(du, dv))
            h = thick * math.cos(q * math.pi / 2) ** 0.6
            for (bu, bv, br, bh) in bumps:
                rr = math.hypot(u - bu, v - bv) / br
                if rr < 1:
                    h += bh * math.cos(rr * math.pi / 2) ** 2 * (1 - q)
            V.append(p + z * (0.6 + h))
    V = np.array(V)
    F = []
    for j in range(nv):
        for i in range(nu):
            k = j * (nu + 1) + i
            F.append((k, k + 1, k + nu + 2, k + nu + 1))
    f = F[len(F) // 2]
    if np.cross(V[f[1]] - V[f[0]], V[f[3]] - V[f[0]]) @ z < 0:
        F = [tuple(reversed(t)) for t in F]
    return V, F


def main():
    import bpy
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    body, rig = C.open_base()
    coll = C.part_collection(PART, "Part.Gloves")
    bd = C.body_data(body)
    bvh0 = C.skin_bvh(bd)
    mats = {k: C.flat_material(f"Glove.Mat.{k.title()}", h, 0.7) for k, h in COLOURS.items()}
    objs, meas = [], {}
    for side in ("L", "R"):
        V, F, fc = build_shell(bd, side, bvh0)
        fc = palm_faces(V, F, fc, side)
        sh = C.mesh_object(f"Glove.{side}.Shell", V, F, coll, mats=[mats["knit"], mats["cuff"], mats["palm"]],
                           face_mat=fc)
        sh["sgt_clay"] = (0.40, 0.40, 0.42)
        shell_bvh = C.bvh_from(V, F)
        O, x, y, z, heads = hand_frame(side)
        # knuckle guard: centred GUARD["back"] mm proximal of the joint centres (the dorsal knuckle apex sits
        # behind the joint axis), bosses over the four knuckles
        bumps = [(float((h - O) @ x), GUARD["back"] - 8.0, 10.0, GUARD["boss"]) for h in heads]
        Vg, Fg = plate_on(shell_bvh, O - y * GUARD["back"], x, y, z, GUARD["half_w"], GUARD["half_h"], GUARD["thick"], bumps)
        gd = C.mesh_object(f"Glove.{side}.Knuckle", Vg, Fg, coll, mat=mats["guard"])
        gd["sgt_clay"] = (0.30, 0.30, 0.32)
        parts = [sh, gd]
        for k in (2, 3, 4, 5):
            pip = C.bone_mm(f"finger{k}-2.{side}")
            fy = C.bone_mm(f"finger{k}-2.{side}", "tail") - pip
            fy /= np.linalg.norm(fy)
            fx = x - fy * (x @ fy)
            fx /= np.linalg.norm(fx)
            fz = np.cross(fx, fy)
            if fz @ z < 0:
                fz = -fz
            Vp, Fp = plate_on(shell_bvh, pip, fx, fy, fz, PAD["half_w"], PAD["half_h"], PAD["thick"], nu=10, nv=8, edge=4.0)
            pd = C.mesh_object(f"Glove.{side}.Pad.{k}", Vp, Fp, coll, mat=mats["pad"])
            pd["sgt_clay"] = (0.30, 0.30, 0.32)
            parts.append(pd)
        for o in parts:
            C.bind(o, body, rig)
            if o is sh:
                C.solidify(o, 1.0, inward=True)
            C.subsurf(o, 1)
        objs += parts
        Vw, _ = C.evaluated_world_mm(sh)
        meas[side] = {"guard_mm": [2 * GUARD["half_w"], 2 * GUARD["half_h"], GUARD["thick"] + GUARD["boss"]],
                      "knuckle_breadth_mm": round(float(np.linalg.norm(heads[3] - heads[0])), 1),
                      "cuff_len_mm": CUFF_LEN, "verts": len(Vw)}
    lib = C.library_pass(coll, "Glove", MATERIALS, side_dust={"R": 1.0, "L": 0.7}, say_tag=TAG)
    rest = C.clearance(objs, body, "rest")
    used = C.apply_hero_pose(rig)
    posed = C.clearance(objs, body, "hero pose")
    C.rest_pose(rig)
    C.save_part(TAG, coll, {"measure_mm": meas, "clearance_rest": rest, "clearance_posed": posed, "pose": used,
                            "materials": lib})
    if "--no-render" not in args:
        wr = C.bone_mm("wrist.L")
        C.render_part(TAG, coll, (wr[0] + 30, wr[1] - 70, wr[2] - 50), (330, 330), crops=("ref.hands_rifle", "ref.soldier_full"))
        C.rest_pose(rig)
        O, x, y, z, _ = hand_frame("L")
        C.render_view(TAG, [coll], "rest_dorsal_L", O + z * 500 - y * 30, O - y * 30, 300)


if __name__ == "__main__":
    main()
