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
TUCK_EASE = 2.0      # under the trousers' waistband the knit is pressed to the skin (round 1: 3.5, it showed through)
SLEEVE = [(0.0, 12.0), (0.5, 18.0), (0.95, 19.0), (1.05, 18.0), (1.5, 16.0), (1.72, 11.0), (1.84, 5.5), (2.0, 5.0)]  # arm param: 0 shoulder, 1 elbow, 2 wrist
COLLAR = {"co": (0.0, -60.0, 1542.0), "no": (0.0, -0.35, 1.0)}    # collar top: 1542 front, ~1584 back (under the gaiter)
HEM_Z = 930.0                                                     # tucked hem, inside the trousers
CUFF_BEYOND_WRIST = 8.0                                           # the cuff edge past the wrist joint (mm)
# The gaiter (round 2): a fleece cowl bunched round the neck. s = arc length along the skin's meridian, 0 at
# the ring h_ref up the neck axis (on the neck all round), + up. Triples are (front, side, back).
GAITER = {"h_c": 60.0, "h_ref": 100.0, "fan_deg": 70.0,      # fan centre for the skirt's rays; s origin
          "s_top": (18.0, 40.0, 62.0),                       # top edge: under the chin, behind the jaw, occiput
          "tilt_side": 12.0,                                 # top edge and folds higher on his left (drawn)
          "s_bot": (-120.0, -88.0, -48.0),                   # skirt edge: under the bag top, under the straps
          "base_neck": 11.0, "base_skirt": 10.0,             # shirt collar / shirt plus air under the fleece
          # folds: (depth below s_top, half-width, proud above the base)
          "rolls": [((9.0, 10.0, 10.0), 16.0, (26.0, 20.0, 16.0)),        # lip at the top edge
                    ((44.0, 47.0, 50.0), 30.0, (52.0, 36.0, 24.0)),       # main roll under the jaw
                    ((90.0, 88.0, 90.0), 24.0, (18.0, 14.0, 8.0))],       # lower roll falling over the collar
          "wobble": [(2, 0.24), (3, 0.14), (5, 0.07)],       # fold height variation round the neck (harmonic, amp)
          "pleat": (65.0, 14.0, 0.55),                       # crease on his left front: phi deg, width deg, depth
          "drape": 7.0,                                      # vertical drapes of the skirt over the chest
          "strap_clear": 4.0,                                # flat this far inside the strap's inner edge
          "smooth": 6, "nphi": 96, "ns": 64, "seed": 7, "wall": 3.0}
# The carrier's shoulder straps (carrier.py imports this): centre line |x| and pad width (mm). The gaiter is
# pressed flat under them.
STRAP = {"x": 140.0, "w": 64.0}
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
    off = TORSO_EASE - (TORSO_EASE - TUCK_EASE) * (1 - smoothstep(1060.0, 1100.0, V[:, 2]))  # pressed where tucked
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
    V1 = C.push_out(V1, bvh0, np.where(V1[:, 2] < 1060.0, TUCK_EASE - 0.3, 3.0))
    # the tail under the trousers lies on the skin at TUCK_EASE (smoothing bridged the lumbar hollow, so the
    # trousers, which hug it, came through the shirt at the lower back: round 1's clash 13)
    w = 1.0 - smoothstep(1040.0, 1080.0, V1[:, 2])
    sel = w > 0
    d, n = C.signed_dist(V1[sel], bvh0)
    V1[sel] += n * ((TUCK_EASE - d) * w[sel])[:, None]
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


def _ray_profile(bvh, A, d, e, h_c, h_ref, fan_deg, h_max, step=1.5):
    """The skin under one meridian of the gaiter, bottom to top: hits of a fan of rays from the neck axis
    point A + d h_c swept from fan_deg below the horizontal up to it (they land on the chest, trapezius or
    upper back), then of horizontal rays from points climbing the axis to h_max (they land on the neck).
    Returns (points, normals, index of the first ray at or above h_ref)."""
    from mathutils import Vector
    P, N = [], []
    C0 = A + d * h_c
    for el in np.arange(-fan_deg, 0.0, 1.0):
        a = math.radians(el)
        dr = math.cos(a) * e + math.sin(a) * d
        hit = bvh.ray_cast(Vector(C0), Vector(dr), 400.0)
        if hit[0] is not None:
            P.append(np.array(hit[0]))
            N.append(np.array(hit[1]))
    k0 = None
    for h in np.arange(h_c, h_max, step):
        if k0 is None and h >= h_ref:
            k0 = len(P)
        hit = bvh.ray_cast(Vector(A + d * h), Vector(e), 200.0)
        if hit[0] is not None:
            P.append(np.array(hit[0]))
            N.append(np.array(hit[1]))
    P, N = np.array(P), np.array(N)
    N = N * np.sign(np.sum(N * (P - (A + d * h_c)), axis=1))[:, None]       # outward
    return P, N, k0


def _arclen_resample(P, N, k0, s_new):
    """Resample a polyline (and its normals) at arc lengths s_new measured from point k0 (+ toward the end)."""
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    s -= s[k0]
    s_new = np.clip(s_new, s[0], s[-1])
    Q = np.column_stack([np.interp(s_new, s, P[:, i]) for i in range(3)])
    M = np.column_stack([np.interp(s_new, s, N[:, i]) for i in range(3)])
    return Q, M / np.linalg.norm(M, axis=1)[:, None]


def _bump(s, c, w):
    """cos^2 lobe of half-width w at c (1 at c, 0 beyond)."""
    t = np.clip(np.abs(s - c) / w, 0.0, 1.0)
    return np.cos(t * math.pi / 2.0) ** 2


def _by_phi(phi, front, side, back):
    """A value that runs front (phi 0) -> side (+-90) -> back (180), smoothly."""
    c = math.cos(phi)
    return side + (front - side) * c if c >= 0 else side + (back - side) * (-c)


def build_gaiter(bvh0):
    """The cowl: for each meridian round the neck axis, the skin's profile from the shoulders up the neck
    (_ray_profile), resampled by arc length s (0 at the neck base ring, + up), pushed out along the skin
    normal by the collar allowance plus the folds: a lip at the top edge, the big main roll under the jaw
    that sags at the front, a lower roll, and a skirt that lies flat over the collar onto the chest,
    trapezius and upper back. The fold heights and depths vary round the neck (low harmonics, a pleat on
    his left), so the rolls read as one bunched tube, not as rings. Where the carrier's shoulder straps
    will lie (|x| inside STRAP's corridor) the gaiter is pressed flat to the collar allowance."""
    g = GAITER
    A = np.array([0.0, 12.0, 1488.0])                    # neck base centre (between the clavicles' ends)
    B = C.bone_mm("neck03")
    d = (B - A) / np.linalg.norm(B - A)
    ef = np.array([0.0, -1.0, 0.0]) - d * (-d[1])
    ef /= np.linalg.norm(ef)
    es = np.cross(d, ef)
    if es[0] < 0:
        es = -es                                          # phi +90 = his left (+X)
    nphi, ns = g["nphi"], g["ns"]
    rng = np.random.default_rng(g["seed"])
    ph_off = rng.uniform(0, 2 * math.pi, 6)
    x_in = STRAP["x"] - STRAP["w"] / 2.0 - g["strap_clear"]
    PH = 2 * math.pi * np.arange(nphi) / nphi
    # 1. the skin under the gaiter on a grid that is coherent round the neck: the same rays (fan angle, then
    #    height up the axis) for every meridian, smoothed, so neighbouring meridians do not disagree
    from mathutils import Vector
    C0 = A + d * g["h_c"]
    us = [("fan", el) for el in np.arange(-g["fan_deg"], 0.0, 1.0)] + [("h", h) for h in np.arange(g["h_c"], 200.0, 1.5)]
    k_ref = next(k for k, (t, v) in enumerate(us) if t == "h" and v >= g["h_ref"])
    R = np.full((len(us), nphi), np.nan)
    for i, phi in enumerate(PH):
        e = math.cos(phi) * ef + math.sin(phi) * es
        for k, (t, v) in enumerate(us):
            if t == "fan":
                a_ = math.radians(v)
                o, dr = C0, math.cos(a_) * e + math.sin(a_) * d
            else:
                o, dr = A + d * v, e
            hit = bvh0.ray_cast(Vector(o), Vector(dr), 400.0)
            if hit[0] is not None:
                R[k, i] = hit[3]
    for k in range(len(us)):                       # fill misses from the meridian neighbours
        row = R[k]
        if np.isnan(row).any() and not np.isnan(row).all():
            ok = ~np.isnan(row)
            row[~ok] = np.interp(np.nonzero(~ok)[0], np.nonzero(ok)[0], row[ok], period=nphi)
    G = np.zeros((len(us), nphi, 3))
    for i, phi in enumerate(PH):
        e = math.cos(phi) * ef + math.sin(phi) * es
        for k, (t, v) in enumerate(us):
            if t == "fan":
                a_ = math.radians(v)
                G[k, i] = C0 + (math.cos(a_) * e + math.sin(a_) * d) * R[k, i]
            else:
                G[k, i] = A + d * v + e * R[k, i]
    Fg = [(k * nphi + i, k * nphi + (i + 1) % nphi, (k + 1) * nphi + (i + 1) % nphi, (k + 1) * nphi + i)
          for k in range(len(us) - 1) for i in range(nphi)]
    G = C.taubin(G.reshape(-1, 3), C.edges_of(Fg), iters=15, lam=0.5, mu=-0.53).reshape(len(us), nphi, 3)
    # 2. arc length along each smoothed meridian (0 at h_ref), resampled at the gaiter's own rows
    S = np.zeros((ns, nphi))
    Q = np.zeros((ns, nphi, 3))
    for i, phi in enumerate(PH):
        P = G[:, i]
        sl = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        sl -= sl[k_ref]
        s_top = _by_phi(phi, *g["s_top"]) + g["tilt_side"] * math.sin(phi)
        s_bot = max(_by_phi(phi, *g["s_bot"]), sl[0])
        S[:, i] = np.linspace(s_bot, s_top, ns)
        Q[:, i] = np.column_stack([np.interp(S[:, i], sl, P[:, j]) for j in range(3)])
    F = []
    for j in range(ns - 1):
        for i in range(nphi):
            a, b = j * nphi + i, j * nphi + (i + 1) % nphi
            F.append((a, b, b + nphi, a + nphi))
    E = C.edges_of(F)
    Qf = C.taubin(Q.reshape(-1, 3), E, iters=6, lam=0.5, mu=-0.53).reshape(ns, nphi, 3)
    du = np.roll(Qf, -1, 1) - np.roll(Qf, 1, 1)
    dv = np.gradient(Qf, axis=0)
    M = np.cross(dv, du)
    rad = Qf - (A + np.outer(((Qf.reshape(-1, 3) - A) @ d), d).reshape(ns, nphi, 3))
    M *= np.sign(np.sum(M * rad, axis=2))[..., None]
    M /= np.linalg.norm(M, axis=2)[..., None]
    OFF = np.zeros((ns, nphi))
    BASE = np.zeros((ns, nphi))
    for i, phi in enumerate(PH):
        s = S[:, i]
        s_top, s_bot = s[-1], s[0]
        # collar allowance: the shirt over the chest, its collar plus air on the neck
        base = g["base_skirt"] + (g["base_neck"] - g["base_skirt"]) * smoothstep(-20.0, 10.0, s)
        wob = 1.0 + sum(a * math.sin(k * phi + ph_off[j]) for j, (k, a) in enumerate(g["wobble"]))
        pleat = 1.0 - g["pleat"][2] * math.exp(-0.5 * ((math.degrees(phi) - g["pleat"][0] + 180) % 360 - 180) ** 2
                                               / g["pleat"][1] ** 2)
        lift = 7.0 * math.sin(2 * phi + ph_off[4]) + 4.0 * math.sin(3 * phi + ph_off[5])   # folds wander up and down
        off = base.copy()
        for (dc, w, amp) in g["rolls"]:
            dcv = _by_phi(phi, *dc)
            off += _by_phi(phi, *amp) * wob * pleat * _bump(s, s_top - dcv + lift, w)
        # the skirt's soft drapes over the chest (front half only)
        fr = max(math.cos(phi), 0.0) ** 1.5
        sk = 1.0 - smoothstep(s_top - 95.0, s_top - 70.0, s)
        off += g["drape"] * fr * sk * (0.5 + 0.5 * math.cos(5 * phi + ph_off[5])) * smoothstep(s_bot, s_bot + 25.0, s)
        # the bottom edge thins out where it tucks under the carrier
        off -= (off - g["base_skirt"]) * (1 - smoothstep(s_bot, s_bot + 18.0, s))
        OFF[:, i], BASE[:, i] = off, base
    # the folds bulge away from the neck axis (a bunched tube), not along the skin normal: normals converge in
    # the hollow where the neck meets the shoulders and 50 mm along them would fold the surface through itself
    Dr = rad / np.linalg.norm(rad, axis=2)[..., None]
    Dr = 0.35 * M + Dr
    Dr /= np.linalg.norm(Dr, axis=2)[..., None]

    def place(off):
        return Qf + M * BASE[..., None] + Dr * (off - BASE)[..., None]
    V = place(OFF)
    # pressed flat under the shoulder straps: nothing outboard of the strap's inner edge stands proud
    k = np.clip((np.abs(V[..., 0]) - (x_in - 12.0)) / 12.0, 0.0, 1.0)
    k = k * k * (3 - 2 * k)
    OFF = BASE + (OFF - BASE) * (1 - k)
    V = place(OFF)
    Vf = V.reshape(-1, 3)
    f = F[len(F) // 2]
    nrm = np.cross(Vf[f[1]] - Vf[f[0]], Vf[f[3]] - Vf[f[0]])
    c = Vf[f[0]] - (A + d * ((Vf[f[0]] - A) @ d))
    if nrm @ c < 0:
        F = [tuple(reversed(q)) for q in F]
    Vf = C.taubin(Vf, E, iters=g["smooth"], lam=0.5, mu=-0.53)
    Vf = C.push_out(Vf, bvh0, g["base_skirt"] - 1.0)
    return Vf, F


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
