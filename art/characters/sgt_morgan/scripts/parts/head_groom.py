"""The head's hair, round 10 (scripts/parts/head.md §13): scalp hair, brows and lashes as Blender hair curves
(Curves objects, generated here strand by strand in numpy: no interactive groom, no particle system), the stubble
as short mesh strands, and a low-poly mesh proxy of the scalp hair for the glTF export.

- Head.Hair (Curves): roots sampled on the scalp by a density field (a soft, arched front hairline, thinner at
  the temple corners, MPFB's scalp group at the sides and back); length by zone (take 1's spec 07 §3.2, shortened
  to the drawn mass: the top 24-32 mm, the upper sides ~10, a fade to under 1 mm at the ear top and the nape); a
  lie direction swept up, forward and to his right on top and down-and-back on the sides; clumps on the top whose
  strands converge on a guide's tip (the piecey, lifted texture; a few long ones are the silhouette spikes).
- Head.Brows, Head.Lashes (Curves): short strands along the brow band (MediaPipe's brow rows on the model) and
  the lid margins (head_look.lid_lines).
- Head.Stubble (mesh, three-sided strands, weights from the body): 2.5-4 mm stubs at the analysis's densities;
  a mesh, not curves, because the jaw and the under-jaw blend into the neck bones and curves cannot be skinned.
- Head.Hair.Proxy (mesh, hidden from Cycles, ob["sgt_role"] = "export"): one tapered blade per clump over a thin
  cap, for engines; export_godot.py takes it in place of the curves.
The curves ride the head bone (ob["sgt_bone"]; head_look.attach_to_bones). Render-only objects carry
ob["sgt_role"] = "render".
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

MM = 0.001
HEAD_CENTRE = np.array([0.0, -25.0, 1735.0])      # between the ears at about the ear top (rest, mm): head.py's
HAIR = {
    "trichion_above_glabella": 44.0,   # mm: the reference's central hairline (24 px above the glabella)
    "arch": 7.0,                       # the hairline drops this much from the centre to the temple corner (|x| 58)
    "temple_x": 60.0, "temple_thin": 0.88, "temple_sigma": 19.0, "temple_dz": -12.0,
    "top_front": 36.0, "top_back": 27.0,
    "side_max": 10.0, "side_min": 0.6,
    "density_top": 70.0, "density_side": 110.0,      # roots / cm2 (real ~200; thicker strands stand in)
    "radius_root": 0.060, "radius_tip": 0.018,       # mm
    "clump_gap": 10.5, "clump_max": 0.92, "spike_share": 0.14, "flyaway": 0.05,
    "points": 7,
    "melanin": 0.76, "redness": 0.05, "roughness": 0.36, "tip_lighten": 0.30,
}
BROW = {"below": 0.70, "above": 0.15, "n": 950, "length": (5.0, 8.5), "radius": 0.065, "melanin": 0.92, "redness": 0.25}
LASH = {"upper": 95, "lower": 34, "len_upper": 5.0, "len_lower": 2.0, "radius": 0.045, "melanin": 0.95}
STUBBLE = {"centre_boost": 1.3, "density": 30.0, "length": (2.4, 3.9), "radius": 0.070, "hex": "#33241c", "grey_hex": "#9a938c", "grey_share": 0.45}


def _ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


# =========================================================================== fields and sampling

def scalp_fields(C, bd, L):
    """Per-vertex hair density (0..1), length (mm), top-ness s (0 sides .. 1 top), on Body.Mesh."""
    import head as H
    V, N, g = bd["V"], bd["N"], bd["groups"]
    region = H.head_region(bd) & (g["ears"] < 0.3)
    E = C.edges_of(bd["F"])
    d = V - HEAD_CENTRE
    az = np.degrees(np.arctan2(d[:, 0], -d[:, 1]))
    el = np.degrees(np.arctan2(d[:, 2], np.hypot(d[:, 0], d[:, 1])))
    aaz = np.abs(az)
    front = np.clip(np.cos(np.radians(az)), 0, 1)
    z0 = L["glabella"][2] + HAIR["trichion_above_glabella"]
    zh = z0 - HAIR["arch"] * (np.abs(V[:, 0]) / 58.0) ** 2
    frontish = _ss(85.0, 60.0, aaz)
    inside = frontish * _ss(-3.0, 3.0, V[:, 2] - zh) + (1 - frontish) * (g["scalp"] > 0.5)
    inside = inside * region
    sm = np.clip(C.smooth_field(inside.astype(float), E, iters=2, lam=0.5), 0, 1) * region
    dens = _ss(0.25, 0.8, sm)
    # the temple corners: thinner (the reference recedes a little there and the fade starts)
    for sx in (-1.0, 1.0):
        c = np.array([sx * HAIR["temple_x"], 0.0, z0 + HAIR["temple_dz"]])
        r = np.hypot(V[:, 0] - c[0], V[:, 2] - c[2])
        dens *= 1.0 - HAIR["temple_thin"] * np.exp(-0.5 * (r / HAIR["temple_sigma"]) ** 2) * (V[:, 1] < HEAD_CENTRE[1] - 20.0)
    el_lo = 12.0 + 22.0 * np.abs(np.sin(np.radians(az)))            # the parietal ridge, higher at the sides
    s = _ss(el_lo, el_lo + 28.0, el)
    l_top = HAIR["top_back"] + (HAIR["top_front"] - HAIR["top_back"]) * front
    e = _ss(-22.0, el_lo + 6.0, el)
    l_side = HAIR["side_min"] + (HAIR["side_max"] - HAIR["side_min"]) * e ** 1.7
    length = (l_side + (l_top - l_side) * s) * (0.3 + 0.7 * _ss(0.3, 0.95, sm))
    cover = dens * _ss(0.2, 3.5, length)
    return {"dens": dens, "length": length, "s": s, "az": az, "el": el, "front": front, "cover": cover, "z0": z0}


def tris_of(bd, keep):
    T = []
    for f in bd["F"]:
        if keep[list(f)].all():
            for j in range(1, len(f) - 1):
                T.append((f[0], f[j], f[j + 1]))
    return np.array(T)


def sample_roots(V, N, T, dens, per_cm2, rng):
    """Random roots on triangles T, count by area x density. Returns positions, normals, (tri index, barycentrics)."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1) / 100.0          # cm2
    w = area * dens[T].mean(1) * per_cm2
    n = int(w.sum() * 1.3)
    if n == 0:
        return np.zeros((0, 3)), np.zeros((0, 3)), (np.zeros(0, int), np.zeros((0, 3)))
    ti = rng.choice(len(T), size=n, p=w / w.sum())
    u, v = rng.random(n), rng.random(n)
    flip = u + v > 1
    u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
    B = np.stack([1 - u - v, u, v], 1)
    keep = rng.random(n) < np.clip((B * dens[T[ti]]).sum(1) / np.maximum(1.3 * dens[T[ti]].mean(1), 1e-6), 0, 1)
    ti, B = ti[keep], B[keep]
    P = (B[:, :, None] * V[T[ti]]).sum(1)
    Nn = _unit((B[:, :, None] * N[T[ti]]).sum(1))
    return P, Nn, (ti, B)


def interp(field, T, ti, B):
    return (B * field[T[ti]]).sum(1)


def strands(P, Nn, tang, lift_deg, length, bend, K, rng, frizz=0.05):
    """Polyline strands [n, K, 3]: leave the root at the lift angle along the tangent `tang`, lean over towards it
    with arc length (bend), a little per-strand frizz."""
    a = np.radians(lift_deg)[:, None]
    d0 = _unit(np.cos(a) * tang + np.sin(a) * Nn)
    out = np.zeros((len(P), K, 3))
    out[:, 0] = P
    step = (length / (K - 1))[:, None]
    fr = rng.normal(0, 1, (len(P), 3)) * frizz
    for k in range(1, K):
        t = (k - 0.5) / (K - 1)
        d = _unit(d0 + bend[:, None] * t * (tang - 0.2 * Nn) + fr * t)
        out[:, k] = out[:, k - 1] + d * step
    return out


def curves_object(name, pts, radius, coll, mat, bone="head", clay=(0.2, 0.15, 0.12)):
    """A Curves (hair) object from strands [n, K, 3] in mm and radii [n, K] in mm."""
    import bpy
    old = bpy.data.objects.get(name)
    if old is not None:
        data = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if data.users == 0:
            bpy.data.hair_curves.remove(data)
    n, K = pts.shape[:2]
    cu = bpy.data.hair_curves.new(name)
    cu.add_curves([K] * n)
    cu.attributes["position"].data.foreach_set("vector", (pts * MM).astype(np.float32).ravel())
    ra = cu.attributes.get("radius") or cu.attributes.new("radius", "FLOAT", "POINT")
    ra.data.foreach_set("value", (radius * MM).astype(np.float32).ravel())
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    ob["sgt_bone"] = bone
    ob["sgt_role"] = "render"
    ob["sgt_clay"] = clay
    ob.color = (*clay, 1.0)
    return ob


def hair_material(name, melanin, redness, roughness=0.34, tip_lighten=0.0, random_color=0.08):
    import bpy
    old = bpy.data.materials.get(name)
    if old is not None:
        bpy.data.materials.remove(old)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    h = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    h.parametrization = "MELANIN"
    info = nt.nodes.new("ShaderNodeHairInfo")
    h.inputs["Melanin Redness"].default_value = redness
    h.inputs["Roughness"].default_value = roughness
    h.inputs["Radial Roughness"].default_value = 0.35
    h.inputs["Coat"].default_value = 0.05
    h.inputs["Random Color"].default_value = random_color
    h.inputs["Random Roughness"].default_value = 0.2
    nt.links.new(info.outputs["Random"], h.inputs["Random"])
    if tip_lighten > 0:
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.35, 1.0
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = melanin, melanin * (1 - tip_lighten)
        nt.links.new(info.outputs["Intercept"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], h.inputs["Melanin"])
    else:
        h.inputs["Melanin"].default_value = melanin
    nt.links.new(h.outputs[0], out.inputs["Surface"])
    mat.diffuse_color = (0.12, 0.085, 0.06, 1.0)
    return mat


# =========================================================================== scalp hair

def build_hair(C, bd, coll, L, seed=11):
    V, N = bd["V"], bd["N"]
    Fd = scalp_fields(C, bd, L)
    rng = np.random.default_rng(seed)
    T = tris_of(bd, bd["in_body"] & (Fd["dens"] > 0.01))
    # density per cm2 varies from the sides to the top: fold it into the field
    per = HAIR["density_side"] + (HAIR["density_top"] - HAIR["density_side"]) * Fd["s"]
    P, Nn, (ti, B) = sample_roots(V, N, T, Fd["dens"] * per / per.max(), per.max(), rng)
    s, front, length = (interp(Fd[k], T, ti, B) for k in ("s", "front", "length"))
    n = len(P)
    length = length * rng.normal(1.0, 0.09, n).clip(0.7, 1.3)
    # the lie: swept up, forward and to his right on top (take 1's spec 07 §4.4), back-left strands up and back,
    # the sides down and back towards the ear
    zf, zm = np.array([-0.60, -0.50, 0.60]), np.array([-0.35, 0.25, 0.90])
    sweep = _unit(zm[None] + (zf - zm)[None] * front[:, None])
    back_left = _ss(0.0, 40.0, P[:, 0]) * _ss(HEAD_CENTRE[1], HEAD_CENTRE[1] + 50.0, P[:, 1])
    sweep = _unit(sweep * (1 - back_left[:, None]) + np.array([0.30, 0.60, 0.70])[None] * back_left[:, None])
    side = np.array([0.0, 0.55, -0.83])
    raw = _unit(side[None] * (1 - s[:, None]) + sweep * s[:, None] + rng.normal(0, 0.12, (n, 3)))
    tang = _unit(raw - (raw * Nn).sum(1, keepdims=True) * Nn)
    lift = 28.0 + 30.0 * s + rng.normal(0, 8.0, n)
    bend = 0.35 + 0.75 * s
    K = HAIR["points"]
    S = strands(P, Nn, tang, lift, length, bend, K, rng)
    # clumps on the top: centres at least clump_gap apart; a strand leans to its centre's guide towards the tip
    cand = np.where((s > 0.45) & (length > 12.0))[0]
    centres = []
    CP = np.zeros((0, 3))
    for i in rng.permutation(cand)[:4000]:
        if not len(CP) or np.linalg.norm(CP - P[i], axis=1).min() > HAIR["clump_gap"]:
            centres.append(i)
            CP = np.concatenate([CP, P[i][None]])
    centres = np.array(centres, int)
    spikes = 0
    if len(centres):
        m = len(centres)
        gl = length[centres] * rng.uniform(0.9, 1.2, m)
        tall = rng.random(m) < HAIR["spike_share"]
        gl[tall] *= 1.35
        spikes = int(tall.sum())
        graw = _unit(tang[centres] + rng.normal(0, 0.45, (m, 3)))
        gt = _unit(graw - (graw * Nn[centres]).sum(1, keepdims=True) * Nn[centres])
        glift = np.clip(lift[centres] + rng.normal(0, 16.0, m) + 16.0 * tall, 22.0, 88.0)
        G = strands(P[centres], Nn[centres], gt, glift, gl, bend[centres] * rng.uniform(0.4, 1.1, m), K, rng, frizz=0.0)
        top = np.where(s > 0.3)[0]
        D = np.linalg.norm(P[top][:, None, :] - P[centres][None, :, :], axis=2)
        near = D.argmin(1)
        dist = D.min(1)
        w = HAIR["clump_max"] * _ss(0.3, 0.6, s[top]) * _ss(16.0, 7.0, dist) * (rng.random(len(top)) > HAIR["flyaway"])
        tk = (np.arange(K) / (K - 1)) ** 1.3
        S[top] = S[top] + w[:, None, None] * tk[None, :, None] * (G[near] - S[top])
    rad = HAIR["radius_root"] + (HAIR["radius_tip"] - HAIR["radius_root"]) * (np.arange(K) / (K - 1))[None, :] ** 1.5
    rad = np.repeat(rad, n, 0)
    short = length < 6.0
    rad[short] = np.linspace(0.045, 0.034, K)[None, :]
    mat = hair_material("Head.Mat.Hair", HAIR["melanin"], HAIR["redness"], HAIR["roughness"], HAIR["tip_lighten"])
    ob = curves_object("Head.Hair", S, rad, coll, mat)
    top_z = float(S[:, :, 2].max())
    info = {"strands": int(n), "points": int(n * K), "clumps": int(len(centres)), "spikes": spikes,
            "length_mm": {"top_median": round(float(np.median(length[s > 0.8])), 1), "side_median": round(float(np.median(length[s < 0.1])), 1) if (s < 0.1).any() else None,
                          "max": round(float(length.max()), 1)},
            "top_z_mm": round(top_z, 1), "trichion_z_mm": round(float(Fd["z0"]), 1),
            "short_strands": int(short.sum())}
    guides = None
    if len(centres):
        cnt = np.bincount(near[w > 0.2], minlength=len(centres))
        guides = {"G": G, "count": cnt, "root_n": Nn[centres]}
    return ob, info, Fd, guides


# =========================================================================== brows and lashes

def build_brows(C, bd, coll, L, surf_bvh, seed=5):
    """Head.Brows: a band between the brow's lower and upper rows, inner end square, the tail tapering; the inner
    third brushed up and out, the body lateral, the tail down and out (analysis §5)."""
    rng = np.random.default_rng(seed)
    P, D, Ln = [], [], []
    for sx in (-1.0, 1.0):
        m = np.array([-sx, 1.0, 1.0])
        lo0 = [L["brow_in"] * m, L["brow_mid"] * m, L["brow_out"] * m]
        hi0 = [L["brow_in_top"] * m, L["brow_mid_top"] * m, L["brow_out_top"] * m]
        # the drawn brows are low-set: the band is centred on MediaPipe's lower row (its upper row lies on the
        # forehead above the brow), BROW["below"] of the rows' gap under it and BROW["above"] over it
        lo = [a - BROW["below"] * (b - a) for a, b in zip(lo0, hi0)]
        hi = [a + BROW["above"] * (b - a) for a, b in zip(lo0, hi0)]
        n = BROW["n"]
        u = rng.random(n) ** 0.9
        v = rng.random(n)

        def poly(pts, t):
            a, b, c = pts
            return (1 - t)[:, None] ** 2 * a + 2 * (t * (1 - t))[:, None] * (2 * b - 0.5 * (a + c)) + t[:, None] ** 2 * c
        ue = -0.06 + 1.2 * u                                   # a little past the detected ends
        width = np.where(ue < 0.7, 1.0, np.clip((1.26 - ue) / 0.56, 0.05, 1.0))
        vv = 0.5 + (v - 0.5) * width * 1.15
        p = poly(lo, ue) * (1 - vv)[:, None] + poly(hi, ue) * vv[:, None]
        out_dir = _unit(np.array([[np.sign(m[0]) * -1.0 * -1.0, 0.0, 0.0]]) * 0 + (poly(lo, np.clip(ue + 0.1, 0, 1.3)) - poly(lo, ue)))
        up = np.array([0.0, 0.0, 1.0])
        k_in = _ss(0.35, 0.0, ue)[:, None]
        k_tail = _ss(0.6, 1.1, ue)[:, None]
        d = _unit(out_dir * (1 - 0.75 * k_in) + up * (0.9 * k_in - 0.2 * k_tail) + rng.normal(0, 0.12, (n, 3)))
        for i in range(n):
            loc, nor, _, _ = surf_bvh.find_nearest(tuple(p[i]))
            P.append(np.array(loc))
            nn = np.array(nor)
            t = d[i] - (d[i] @ nn) * nn
            D.append((_unit(t), nn))
            Ln.append(rng.uniform(*BROW["length"]) * (1.0 - 0.35 * float(k_tail[i, 0])))
    P = np.array(P)
    tang = np.array([t for t, _ in D])
    Nn = np.array([nn for _, nn in D])
    S = strands(P, Nn, tang, 20.0 + rng.normal(0, 4.0, len(P)), np.array(Ln), np.full(len(P), 0.15), 4, rng, frizz=0.03)
    # the brow ridge is convex: a strand lying along it dives under the skin, so every point is kept a little over it
    for i in range(S.shape[0]):
        for k in range(1, S.shape[1]):
            loc, nor, _, _ = surf_bvh.find_nearest(tuple(S[i, k]))
            nn = np.array(nor)
            hgt = float((S[i, k] - np.array(loc)) @ nn)
            need = 0.3 + 0.45 * k
            if hgt < need:
                S[i, k] = S[i, k] + nn * (need - hgt)
    rad = np.repeat(np.linspace(BROW["radius"], 0.012, 4)[None], len(P), 0)
    mat = hair_material("Head.Mat.Brow", BROW["melanin"], BROW["redness"], 0.32)
    ob = curves_object("Head.Brows", S, rad, coll, mat)
    return ob, {"strands": int(len(P))}


def build_lashes(C, coll, lids, seed=9):
    rng = np.random.default_rng(seed)
    S, R = [], []
    for side, e in lids.items():
        for which, cnt, ln in (("upper", LASH["upper"], LASH["len_upper"]), ("lower", LASH["lower"], LASH["len_lower"])):
            if which not in e:
                continue
            Pl, Nl = e[which], e[which + "_n"]
            t = np.sort(rng.uniform(0.12 if which == "upper" else 0.3, 0.98, cnt))
            x = t * (len(Pl) - 1)
            i0 = np.clip(x.astype(int), 0, len(Pl) - 2)
            f = (x - i0)[:, None]
            p = Pl[i0] * (1 - f) + Pl[i0 + 1] * f
            nn = _unit(Nl[i0] * (1 - f) + Nl[i0 + 1] * f)
            lat = _unit(Pl[-1] - Pl[0])[None]
            down = np.array([[0.0, 0.0, -1.0]])
            sgn = 1.0 if which == "upper" else -1.0
            d0 = _unit(nn * 0.85 + down * (0.45 if which == "upper" else 0.75) + lat * 0.35 * (t[:, None] - 0.3) + rng.normal(0, 0.08, (cnt, 3)))
            L_ = ln * (0.6 + 0.6 * np.sin(np.pi * t) ** 0.7) * rng.uniform(0.8, 1.15, cnt)
            K = 4
            pts = np.zeros((cnt, K, 3))
            pts[:, 0] = p + nn * 0.15
            for k in range(1, K):
                tt = (k - 0.5) / (K - 1)
                d = _unit(d0 + sgn * np.array([[0.0, 0.0, 1.0]]) * 0.9 * tt)
                pts[:, k] = pts[:, k - 1] + d * (L_ / (K - 1))[:, None]
            S.append(pts)
            R.append(np.repeat(np.linspace(LASH["radius"], 0.012, K)[None], cnt, 0))
    if not S:
        return None, {"strands": 0}
    S, R = np.concatenate(S), np.concatenate(R)
    mat = hair_material("Head.Mat.Lash", LASH["melanin"], 0.2, 0.28, 0.0, 0.0)
    ob = curves_object("Head.Lashes", S, R, coll, mat)
    return ob, {"strands": int(len(S))}


# =========================================================================== stubble (mesh strands)

def build_stubble(C, bd, coll, body, rig, L, dens, grey, seed=21):
    import bpy
    V, N = bd["V"], bd["N"]
    rng = np.random.default_rng(seed)
    T = tris_of(bd, bd["in_body"] & (dens > 0.02))
    # the moustache and the chin pad are the densest (spec 07 section 3.4: 55 / cm2 against 28 on the cheek)
    zone = (np.abs(V[:, 0]) < abs(L["mouth"][0]) + 5.0) & (V[:, 2] < L["subnasale"][2]) & (V[:, 2] > L["chin"][2] - 6.0) & (V[:, 1] < L["mouth"][1] + 22.0)
    boost = 1.0 + STUBBLE["centre_boost"] * zone
    P, Nn, (ti, B) = sample_roots(V, N, T, dens * boost / boost.max(), STUBBLE["density"] * boost.max(), rng)
    n = len(P)
    dn = interp(dens, T, ti, B)
    gr = interp(grey, T, ti, B)
    sx = np.sign(P[:, 0])
    raw = np.stack([sx * 0.25, np.full(n, 0.25), np.full(n, -0.92)], 1)
    moust = (P[:, 2] > L["lip_top"][2]) & (np.abs(P[:, 0]) < abs(L["mouth"][0]) + 6.0)
    raw[moust] = np.stack([sx[moust] * 0.7, np.zeros(moust.sum()), np.full(moust.sum(), -0.7)], 1)
    raw = _unit(raw + rng.normal(0, 0.22, (n, 3)))
    tang = _unit(raw - (raw * Nn).sum(1, keepdims=True) * Nn)
    lift = np.radians(34.0 + rng.normal(0, 10.0, n))[:, None]
    d = _unit(np.cos(lift) * tang + np.sin(lift) * Nn)
    ln = (STUBBLE["length"][0] + (STUBBLE["length"][1] - STUBBLE["length"][0]) * dn) * rng.uniform(0.85, 1.12, n)
    a = _unit(np.cross(d, Nn + 1e-3))
    b = np.cross(d, a)
    r0 = STUBBLE["radius"]
    ang = rng.uniform(0, 2 * np.pi, n)
    VV = np.zeros((n, 6, 3))
    for k in range(3):
        th = ang + 2 * np.pi * k / 3
        o = np.cos(th)[:, None] * a + np.sin(th)[:, None] * b
        VV[:, k] = P - d * 0.15 + o * r0
        VV[:, 3 + k] = P + d * ln[:, None] + o * r0 * 0.75
    base = (np.arange(n) * 6)[:, None]
    quads = np.concatenate([base + np.array([[k, (k + 1) % 3, 3 + (k + 1) % 3, 3 + k]]) for k in range(3)], 0)
    caps = base + np.array([[3, 4, 5]])
    is_grey = rng.random(n) < gr * STUBBLE["grey_share"]
    old = bpy.data.objects.get("Head.Stubble")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    mats = []
    for nm, hx in (("Head.Mat.Stubble", STUBBLE["hex"]), ("Head.Mat.StubbleGrey", STUBBLE["grey_hex"])):
        m = bpy.data.materials.get(nm)
        if m is not None:
            bpy.data.materials.remove(m)
        m = C.flat_material(nm, hx, rough=0.42, sheen=0.0)
        mats.append(m)
    me = bpy.data.meshes.new("Head.Stubble")
    verts = (VV.reshape(-1, 3) * MM)
    faces = [tuple(int(i) for i in q) for q in quads] + [tuple(int(i) for i in c) for c in caps]
    me.from_pydata([tuple(v) for v in verts], [], faces)
    for m in mats:
        me.materials.append(m)
    fm = np.concatenate([np.tile(is_grey, 3), is_grey]).astype(np.int32)
    me.polygons.foreach_set("material_index", fm)
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    me.update()
    ob = bpy.data.objects.new("Head.Stubble", me)
    coll.objects.link(ob)
    ob["sgt_clay"] = (0.25, 0.2, 0.17)
    ob["sgt_role"] = "render"
    C.bind(ob, body, rig)
    return ob, {"strands": int(n), "grey": int(is_grey.sum()), "tris": int(n * 7)}


# =========================================================================== the export proxy

def build_proxy(C, bd, coll, body, rig, Fd, guides, hex_colour="#3a2a1e"):
    """Head.Hair.Proxy: a thin cap over the haired scalp (thickness by hair length, capped) and one flat tapered
    blade per clump along its guide; a mesh an engine can draw without hair curves. Hidden from Cycles."""
    import bpy
    V, F = bd["V"], bd["F"]
    keep = bd["in_body"] & (Fd["cover"] > 0.45)
    Vs, Fs, idx = C.submesh(V, F, keep)
    Ns = C.vertex_normals(Vs, Fs)
    th = np.clip(0.45 * Fd["length"][idx], 1.8, 9.0)
    Pc = Vs + Ns * th[:, None]
    verts, faces = [Pc], [list(f) for f in Fs]
    nv = len(Pc)
    blades = 0
    if guides is not None:
        G, cnt, rn = guides["G"], guides["count"], guides["root_n"]
        for gi in np.argsort(-cnt)[:170]:
            if cnt[gi] < 4:
                continue
            g = G[gi][::2].copy()                                    # 4 points along the guide
            g[0] = g[0] + rn[gi] * 2.5                               # the root ring clear of the skin
            tan = _unit(np.gradient(g, axis=0))
            side = _unit(np.cross(tan, rn[gi][None]))
            wd = np.array([4.2, 3.4, 2.0, 0.3])[: len(g)]
            ring = np.concatenate([g - side * wd[:, None], g + side * wd[:, None]])
            k = len(g)
            verts.append(ring)
            for j in range(k - 1):
                faces.append((nv + j, nv + j + 1, nv + k + j + 1, nv + k + j))
            nv += 2 * k
            blades += 1
    P = np.concatenate(verts)
    old = bpy.data.objects.get("Head.Hair.Proxy")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    m = bpy.data.materials.get("Head.Mat.HairProxy")
    if m is not None:
        bpy.data.materials.remove(m)
    mat = C.flat_material("Head.Mat.HairProxy", hex_colour, rough=0.6, sheen=0.0)
    ob = C.mesh_object("Head.Hair.Proxy", P, faces, coll, mat=mat)
    ob["sgt_clay"] = (0.3, 0.25, 0.21)
    ob["sgt_role"] = "export"
    C.bind(ob, body, rig)
    ob.hide_render = True
    ob.hide_viewport = True
    tris = sum(len(f) - 2 for f in faces)
    return ob, {"verts": int(len(P)), "tris": int(tris), "blades": blades}


# =========================================================================== all of it

def build(C, bd, coll, body, rig, marks, L, lids, stubble_fields=None, proxy=True):
    """Hair, brows, lashes, stubble (and the export proxy). Returns the scalp cover field for the skin's mask, the
    stubble fields used, and the numbers."""
    from mathutils.bvhtree import BVHTree
    import head as H
    info = {}
    hair, info["hair"], Fd, guides = build_hair(C, bd, coll, L)
    region = H.head_region(bd)
    T = tris_of(bd, region)
    bvh = BVHTree.FromPolygons([tuple(v) for v in bd["V"]], [tuple(int(i) for i in t) for t in T])
    _, info["brows"] = build_brows(C, bd, coll, L, bvh)
    _, info["lashes"] = build_lashes(C, coll, lids)
    if stubble_fields is None:
        import head_skin
        stubble_fields = head_skin.stubble_fields(body, marks)
    _, info["stubble"] = build_stubble(C, bd, coll, body, rig, L, *stubble_fields)
    if proxy:
        _, info["proxy"] = build_proxy(C, bd, coll, body, rig, Fd, guides)
    return Fd["cover"], stubble_fields, info
