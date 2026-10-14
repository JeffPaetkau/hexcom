"""Round 5 (critic round 4 m1, its one blocking defect: bald toes): the toes' terminal hair of spec 01 §3.4
and §6.1 as Blender hair curves, rendered in Cycles as 3D tubes (look.lookdev_scene) with a Principled Hair
material (look.hair_material). Kept modest: a sparse tuft on the hallux's proximal phalanx (8-12 hairs, 5-8
mm) and two or three on toe 2's (3-6 mm), dark brown, 0.035 mm root and 0.016 mm tip radius, lying flat
toward the toes with 10-20 degrees of random yaw.

Each hair is grown along the skin from its root: it leaves the follicle at `rise_deg` and lies down within a
millimetre (its height over the skin h(s) = s tan(rise) exp(-s / s0), plus a slow wave so it is not glued
on), each step's heading kept in the skin's tangent plane at the nearest dense vertex. Roots are dense-skin
vertices in an ellipse on the phalanx's dorsum, at least `spacing` mm apart, seeded.
"""
import math

import numpy as np

import toes as T

HAIR = {
    "seed": 11, "points": 18, "radius_mm": (0.026, 0.008), "rise_deg": 22.0, "s0_mm": 0.8, "yaw_deg": 8.0,
    "wave_mm": 0.03, "embed_mm": 0.04,
    # each hair bends in the skin's plane by a total angle (degrees over its length), as terminal body hair does:
    # straight strands read as scratches (round 5's first render). Whole foot, pass 2 (round 1's m14, m32: still short,
    # straight, parallel dark dashes in a tight clump, like pen hatching): the bend is `curl_deg` = (least, most),
    # growing toward the tip (an arc that tightens, not a kink); the hairs finer (0.052 mm at the root, tapering to
    # 0.016), fewer, longer, spread at least `spacing` apart over a wider patch. (With the bend's side random and 22
    # degrees of yaw they crossed in X's, scratches again: a tuft is a stream, every hair in it turning the same way,
    # `curl_side`, its heading within 8 degrees of the others')
    "curl_deg": (18.0, 38.0), "curl_side": 1.0,
    # per toe: the segment, the patch's centre (share of the segment from its proximal joint), its half-axes
    # (along, across, mm), the count and the lengths (mm)
    "tufts": [
        {"seg": "h1", "centre": 0.5, "half": (7.5, 5.5), "u0": -0.8, "n": 7, "len": (4.5, 7.5), "spacing": 2.0},
        {"seg": "t2p", "centre": 0.45, "half": (3.4, 2.4), "u0": 0.0, "n": 2, "len": (3.5, 5.5), "spacing": 2.0},
        # whole foot, pass 1: spec 01 §3.4's 2-4 hairs on toes 3 and 4, 0-3 short ones on toe 5 (pass 2: 2, 1, 0)
        {"seg": "t3p", "centre": 0.45, "half": (3.0, 2.2), "u0": 0.0, "n": 2, "len": (3.0, 5.0), "spacing": 2.0},
        {"seg": "t4p", "centre": 0.45, "half": (2.8, 2.0), "u0": 0.2, "n": 1, "len": (3.0, 4.5), "spacing": 2.0},
    ],
}


def build(ctx, q, nrm, segs, groups, params=None):
    """The hair object `Hires.L.Hair` on the finished dense skin (q, nrm: F, mm). Returns a report."""
    import bpy
    from mathutils.kdtree import KDTree
    H = dict(HAIR, **(params or {}))
    rng = np.random.default_rng(H["seed"])
    near = T.toes_weight(groups) > 0.02
    ids = np.nonzero(near)[0]
    kd = KDTree(len(ids))
    for i, j in enumerate(ids):
        kd.insert(q[j], i)
    kd.balance()

    def surface(p):
        _, i, _ = kd.find(p)
        j = ids[i]
        return q[j], nrm[j]

    curves, rep = [], []
    npts = int(H["points"])
    for tuft in H["tufts"]:
        seg = segs[tuft["seg"]]
        t, u, h = seg.local(q)
        tc, uc = tuft["centre"] * seg.length, tuft["u0"]
        ea, eb = tuft["half"]
        r2 = ((t - tc) / ea) ** 2 + ((u - uc) / eb) ** 2
        cand = np.nonzero((r2 < 1.0) & (nrm @ seg.n > 0.55) & near)[0]
        roots = []
        for j in rng.permutation(cand):
            if len(roots) >= tuft["n"]:
                break
            if all(np.linalg.norm(q[j] - q[r]) >= tuft["spacing"] for r in roots):
                roots.append(j)
        for j in roots:
            L = rng.uniform(*tuft["len"])
            yaw = math.radians(rng.normal(0.0, H["yaw_deg"]))
            n0 = nrm[j]
            d = T.rotate(seg.a, n0, math.degrees(yaw))
            d = d - (d @ n0) * n0
            d /= np.linalg.norm(d)
            step = L / (npts - 1)
            base = q[j].copy()
            pts = [base - H["embed_mm"] * n0]
            ph = rng.uniform(0.0, 2.0 * math.pi)
            cd = H["curl_deg"]
            total = rng.uniform(*cd) if isinstance(cd, (list, tuple)) else rng.normal(0.0, cd)
            side_k = H.get("curl_side") or (1.0 if rng.random() < 0.5 else -1.0)
            total = math.radians(total) * side_k
            norm_k = 0.5 * npts * (npts - 1)
            for k in range(1, npts):
                s = k * step
                base_guess = base + d * step
                sp, sn = surface(base_guess)
                d = sp - base          # the heading follows the skin
                d = d - (d @ sn) * sn
                d = T.rotate(d, sn, math.degrees(total * k / norm_k))   # tightening toward the tip
                if np.linalg.norm(d) < 1e-6:
                    d = seg.a - (seg.a @ sn) * sn
                d /= np.linalg.norm(d)
                base = sp
                lift = s * math.tan(math.radians(H["rise_deg"])) * math.exp(-s / H["s0_mm"]) \
                    + H["radius_mm"][0] + H["wave_mm"] * (1.0 + math.sin(ph + 2.2 * s))
                pts.append(sp + sn * lift)
            curves.append(np.asarray(pts))
        rep.append({"seg": tuft["seg"], "hairs": len(roots), "candidates": int(len(cand))})
    fr = ctx.frame
    P_w = np.concatenate([fr.to_w(c) for c in curves]) / 1000.0
    rad = np.concatenate([np.linspace(H["radius_mm"][0], H["radius_mm"][1], npts) for _ in curves]) / 1000.0
    old = bpy.data.objects.get("Hires.L.Hair")
    if old is not None:
        bpy.data.objects.remove(old)
    hc = bpy.data.hair_curves.new("Hires.L.Hair")
    hc.add_curves([npts] * len(curves))
    hc.position_data.foreach_set("vector", P_w.astype(np.float32).ravel())
    att = hc.attributes.get("radius") or hc.attributes.new("radius", "FLOAT", "POINT")
    att.data.foreach_set("value", rad.astype(np.float32))
    ob = bpy.data.objects.new("Hires.L.Hair", hc)
    coll = ctx.skin.users_collection[0] if ctx.skin.users_collection else bpy.context.scene.collection
    coll.objects.link(ob)
    import look
    hc.materials.append(look.hair_material())
    return {"tufts": rep, "curves": len(curves), "points": npts}
