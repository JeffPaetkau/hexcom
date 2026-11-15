"""Shirt, round 1 blockout: a Crye G3 class combat shirt (snug knit torso tucked into the trousers, roomier
ripstop sleeves to hook-and-loop cuffs at the wrist) as an offset shell from the rest body, and a fleece
neck gaiter (280 mm tube, 3 mm wall) worn pushed down into three rolls. Notes: scripts/parts/shirt.md.

  "$SGT_BLENDER" -b --python scripts/parts/shirt.py [-- --no-render]
  -> cache/parts/shirt.blend (Part.Shirt: Shirt.Shell, Shirt.Gaiter), cache/parts/shirt.json, renders/shirt/

Shell: the torso, neck and arm skin (legs, head and hands excluded by bone weight) copied and refined,
pushed out by an ease field (torso 5 mm, sleeves 10 to 14 mm tapering to 5 at the cuff, blended by the arm
bones' weights), capped across the armpit, each sleeve segment moved toward its sectional convex hull,
smoothed, cut at the collar line, the tucked hem and both wrists, pushed out to a minimum clearance.
Gaiter: rings round the neck axis from a seat ring on the clavicles to a saddle-shaped top (higher at the
back), each point a ray to the skin plus the shirt collar plus the rolls' profile.
Both bound to Morgan.Rig by weight transfer from Body.Mesh.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PART, TAG = "Shirt", "shirt"
TORSO_EASE = 5.0
SLEEVE = [(0.0, 10.0), (0.5, 14.0), (0.95, 18.0), (1.05, 18.0), (1.5, 16.0), (1.72, 11.0), (1.84, 5.5), (2.0, 5.0)]  # arm param: 0 shoulder, 1 elbow, 2 wrist
COLLAR = {"co": (0.0, -60.0, 1542.0), "no": (0.0, -0.5, 1.0)}     # collar top: 1542 front, ~1600 back
HEM_Z = 930.0                                                     # tucked hem, inside the trousers
CUFF_BEYOND_WRIST = 8.0                                           # the cuff edge past the wrist joint (mm)
GAITER = {"seat_front": 10.0, "seat_back": 40.0, "top_front": 110.0, "top_back": 150.0,  # mm along the neck axis
          "base": 11.0, "wall": 3.0,
          "rolls": [(0.85, 0.15, 27.0), (0.64, 0.10, 19.0), (0.48, 0.08, 13.0)]}         # (s centre, half-width, proud)
COLOURS = {"shirt": "#2c2927", "gaiter": "#383029"}


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def arm_param(V, side):
    """0 at the shoulder joint, 1 at the elbow, 2 at the wrist, by projection on the nearer arm segment."""
    sh, el, wr = C.bone_mm(f"upperarm01.{side}"), C.bone_mm(f"lowerarm01.{side}"), C.bone_mm(f"wrist.{side}")
    out = np.zeros(len(V))
    best = np.full(len(V), 1e9)
    for k, (a, b) in enumerate(((sh, el), (el, wr))):
        d = b - a
        t = np.clip(((V - a) @ d) / (d @ d), -0.5, 1.2)
        dist = np.linalg.norm(V - (a + np.outer(np.clip(t, 0, 1), d)), axis=1)
        m = dist < best
        out[m] = k + t[m]
        best[m] = dist[m]
    return out


def build_shell(bd, bvh0):
    V0 = bd["V"]
    leg = C.weight_sum(bd, lambda n: n.startswith(("upperleg", "lowerleg", "foot", "toe")))
    head = C.weight_sum(bd, lambda n: C.is_head(n) and not n.startswith("neck"))
    hand = C.weight_sum(bd, lambda n: n.startswith(("finger", "metacarpal")))
    keep = bd["in_body"] & ((leg < 0.5) | (V0[:, 2] > HEM_Z - 60)) & (head < 0.3) & (hand < 0.3) & (V0[:, 2] > HEM_Z - 120)
    V, F, _ = C.submesh(V0, bd["F"], keep)
    V, F, N = C.refine_on_skin(V, F, bvh0, cuts=1)
    C.say(TAG, f"shell region {len(V)} verts")
    # ease: torso, sleeves by arm parameter, blended by the arm bones' weights (nearest skin vertex)
    from mathutils.kdtree import KDTree
    kd = KDTree(len(V0))
    for i, v in enumerate(V0):
        kd.insert(v, i)
    kd.balance()
    near = np.array([kd.find(v)[1] for v in V])
    w_arm = C.weight_sum(bd, lambda n: n.startswith(("upperarm", "lowerarm", "wrist")))[near]
    w_arm = np.clip(w_arm * 1.3, 0, 1)
    off = TORSO_EASE - 1.5 * (1 - smoothstep(1060.0, 1100.0, V[:, 2]))      # 3.5 mm where it is tucked
    ps, pv = zip(*SLEEVE)
    for side, sg in (("L", 1.0), ("R", -1.0)):
        m = np.sign(V[:, 0]) == sg
        t = arm_param(V[m], side)
        sl = np.interp(t, ps, pv)
        off[m] = TORSO_EASE * (1 - w_arm[m]) + sl * w_arm[m]
    off = C.limit_by_gap(V, N, off, bvh0, share=0.5, floor=1.5)
    E = C.edges_of(F)
    off = C.smooth_field(off, E, iters=4)
    V1 = V + N * off[:, None]
    # sleeves hang: each segment toward its sectional convex hull
    for side, sg in (("L", 1.0), ("R", -1.0)):
        sh, el, wr = C.bone_mm(f"upperarm01.{side}"), C.bone_mm(f"lowerarm01.{side}"), C.bone_mm(f"wrist.{side}")
        m = np.sign(V[:, 0]) == sg
        t = np.zeros(len(V))
        t[m] = arm_param(V[m], side)
        for (a, b, lo, hi) in ((sh, el, 0.15, 1.0), (el, wr, 1.0, 1.72)):
            sel = m & (t >= lo) & (t < hi) & (w_arm > 0.7)
            V1 = C.convexify_along(V1, sel, a, b - a, slab=8.0, k=0.85)
    # cuts: collar line, tucked hem, wrists
    V1, F = C.bisect(V1, F, COLLAR["co"], COLLAR["no"], keep="below")
    V1, F = C.bisect(V1, F, (0, 0, HEM_Z), (0, 0, 1), keep="above")
    for side in ("L", "R"):
        el, wr = C.bone_mm(f"lowerarm01.{side}"), C.bone_mm(f"wrist.{side}")
        d = (wr - el) / np.linalg.norm(wr - el)
        V1, F = C.bisect(V1, F, wr + d * CUFF_BEYOND_WRIST, d, keep="below")
    # drop small islands left by the cuts (e.g. bits of hand) : keep the largest connected piece
    V1, F = largest_piece(V1, F)
    E = C.edges_of(F)
    pin = C.boundary_verts(F, len(V1))
    V1 = C.taubin(V1, E, iters=10, lam=0.5, mu=-0.53, pin=pin)
    V1 = C.push_out(V1, bvh0, 3.0)
    return V1, F


def largest_piece(V, F):
    n = len(V)
    parent = np.arange(n)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for f in F:
        r0 = find(f[0])
        for v in f[1:]:
            r = find(v)
            if r != r0:
                parent[r] = r0
    roots = np.array([find(i) for i in range(n)])
    vals, cnt = np.unique(roots, return_counts=True)
    big = vals[np.argmax(cnt)]
    keep = roots == big
    Vn, Fn, _ = C.submesh(V, F, keep)
    return Vn, Fn


def build_gaiter(bvh0):
    from mathutils import Vector
    A = np.array([0.0, 12.0, 1488.0])                    # neck base centre (between the clavicles' ends)
    B = C.bone_mm("neck03")                              # up the neck
    d = (B - A) / np.linalg.norm(B - A)
    ef = np.array([0.0, -1.0, 0.0]) - d * (-d[1])
    ef /= np.linalg.norm(ef)
    es = np.cross(d, ef)                                 # +X side (his left) or -X: sign does not matter
    g = GAITER
    nphi, ns = 64, 36
    V = []
    for j in range(ns + 1):
        s = j / ns
        for i in range(nphi):
            phi = 2 * math.pi * i / nphi
            back = 0.5 - 0.5 * math.cos(phi)            # 0 front, 1 back
            hb = g["seat_front"] + (g["seat_back"] - g["seat_front"]) * back
            ht = g["top_front"] + (g["top_back"] - g["top_front"]) * back
            h = hb + s * (ht - hb)
            P = A + d * h
            dr = math.cos(phi) * ef + math.sin(phi) * es
            hit = bvh0.ray_cast(Vector(P), Vector(dr), 200.0)
            r = min(hit[3], 75.0) if hit[0] is not None else 60.0
            proud = sum(p * math.cos(min(abs(s - c) / w, 1.0) * math.pi / 2) ** 2 for c, w, p in g["rolls"])
            band = 2.0 * (1 - smoothstep(0.30, 0.42, s))     # flat band squeezed by the carrier at the bottom
            R = r + g["base"] + proud + band
            V.append(P + dr * R)
    V = np.array(V)
    F = []
    for j in range(ns):
        for i in range(nphi):
            a, b = j * nphi + i, j * nphi + (i + 1) % nphi
            F.append((a, b, b + nphi, a + nphi))
    # outward faces
    f = F[0]
    nrm = np.cross(V[f[1]] - V[f[0]], V[f[3]] - V[f[0]])
    if nrm @ (V[f[0]] - A) < 0:
        F = [tuple(reversed(q)) for q in F]
    E = C.edges_of(F)
    pin = np.zeros(len(V), bool)
    V = C.taubin(V, E, iters=8, lam=0.5, mu=-0.53, pin=pin)
    V = C.push_out(V, bvh0, g["base"] - 1.0)
    return V, F


def measure(shell, gaiter):
    V, _ = C.evaluated_world_mm(shell)
    out = {}
    for label, z in (("chest", 1360.0), ("waist", 1180.0)):
        sel = (np.abs(V[:, 2] - z) < 4.0) & (np.abs(V[:, 0]) < 190)
        P = V[sel][:, :2]
        if len(P) > 8:
            H = C.hull2d(P)
            out[f"{label}_girth_hull_mm"] = round(float(np.linalg.norm(np.diff(np.vstack([H, H[:1]]), axis=0), axis=1).sum()), 1)
    Vg, _ = C.evaluated_world_mm(gaiter)
    out["gaiter_height_front_back_mm"] = [round(float(Vg[:, 2].min()), 1), round(float(Vg[:, 2].max()), 1)]
    out["gaiter_width_x_mm"] = round(float(Vg[:, 0].ptp()), 1)
    return out


def main():
    import bpy
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    body, rig = C.open_base()
    coll = C.part_collection(PART)
    bd = C.body_data(body)
    bvh0 = C.skin_bvh(bd)
    Vs, Fs = build_shell(bd, bvh0)
    shell = C.mesh_object("Shirt.Shell", Vs, Fs, coll, mat=C.flat_material("Shirt.Mat.Shirt", COLOURS["shirt"], 0.85))
    shell["sgt_clay"] = (0.44, 0.47, 0.52)
    Vg, Fg = build_gaiter(bvh0)
    gaiter = C.mesh_object("Shirt.Gaiter", Vg, Fg, coll, mat=C.flat_material("Shirt.Mat.Gaiter", COLOURS["gaiter"], 0.95, 0.4))
    gaiter["sgt_clay"] = (0.52, 0.47, 0.42)
    for o, th in ((shell, 1.2), (gaiter, GAITER["wall"])):
        C.bind(o, body, rig)
        m = C.solidify(o, th, inward=True)
        if o is gaiter:
            m.use_even_offset = False
        C.subsurf(o, 1)
    rest = C.clearance([shell, gaiter], body, "rest")
    lay_rest = C.clearance_between(gaiter, shell, "rest")
    meas = measure(shell, gaiter)
    C.say(TAG, json.dumps(meas))
    used = C.apply_hero_pose(rig)
    posed = C.clearance([shell, gaiter], body, "hero pose")
    lay_pose = C.clearance_between(gaiter, shell, "hero pose")
    C.rest_pose(rig)
    C.save_part(TAG, coll, {"measure_mm": meas, "clearance_rest": rest, "clearance_posed": posed,
                            "gaiter_over_shirt": {"rest": lay_rest, "posed": lay_pose}, "pose": used})
    if "--no-render" not in args:
        C.render_part(TAG, coll, (0, -40, 1260), (1400, 900), crops=("ref.torso_vest", "ref.arm_R", "ref.arm_L", "ref.soldier_full"))


if __name__ == "__main__":
    main()
