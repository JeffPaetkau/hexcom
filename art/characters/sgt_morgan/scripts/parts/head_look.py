"""The head's look, round 10 (scripts/parts/head.md §13): a skin material of the head part's own, the eyes, the
tear lines. Built by head.py on the rest body and written to cache/parts/head_look.blend (the materials) and into
the part (the eye and tear-line objects); scripts/assemble.py calls on_assemble() after loading the parts, which
puts the skin on Body.Mesh and hides base.py's Body.Eyes. Nothing here touches base.blend or base.py.

- skin (Head.Mat.Skin): a Principled BSDF with random-walk (skin) subsurface at measured radii (mean free paths
  3.67 / 1.37 / 0.68 mm), MPFB's diffuse texture toned, and three painted mask textures on MPFB's UVs, rasterised
  here from per-vertex zone fields: A = stubble density, grey share, hair cover of the scalp; B = redness (nose,
  cheeks, ears), oil (the T-zone), pale (the forehead); C = under-eye, lips, a wrinkle height map (forehead
  creases, the glabellar pair, crow's feet, nasolabial folds, the lower-lid crease) drawn as lines in UV space.
  Pores and a coarser mottling are procedural bumps; the roughness falls on the T-zone and rises under stubble.
- eyes (Head.Eyes, a copy of Body.Eyes with its weights): the inner ball gets an iris, limbal ring, pupil and a
  sclera that reddens to the canthi from one radial UV map (IrisUV); the outer shell a clear wet coat (Fresnel
  mix of a sharp glossy and transparent, transparent to shadow rays) so the cornea carries a highlight and light
  reaches the iris.
- tear lines (Head.Tearline): a thin wet tube where the lower lid's skin meets the eyeball.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
SCRIPTS = os.path.join(PROJECT, "scripts")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

TEX_DIR = os.path.join(PROJECT, "cache", "head", "tex")
LOOK_BLEND = os.path.join(PROJECT, "cache", "parts", "head_look.blend")
FACE_TARGETS = os.path.join(SCRIPTS, "stages", "face_targets.json")
SIZE = 2048

# ---- the skin's numbers (calibrated against ref/crop_head_face.png through the hero camera: head.md §13)
SKIN = {
    "tone": (0.485, 0.372, 0.335),       # x MPFB's diffuse (linear); round 11b: a further 30 % less saturated
    "sat": 0.92, "hue": 0.503,           # round 11b: the whole chain's saturation, and a little towards yellow
    "sss_weight": 0.35,
    "sss_scale": 0.0016,                 # m: the red radius
    "sss_radius": (1.0, 0.55, 0.40),     # x scale
    "sss_ior": 1.4, "sss_anisotropy": 0.8,
    "ior": 1.4,
    "rough": 0.50, "rough_noise": 0.26, "rough_patch": 0.16, "weather_rgb": (0.84, 0.78, 0.74), "weather_k": 0.55, "rough_oil": -0.22, "rough_stubble": 0.16, "rough_lips": -0.10,
    "red_rgb": (1.07, 0.86, 0.84), "red_k": 0.75,
    "pale_rgb": (1.0, 0.99, 1.02), "pale_k": 0.8,
    "undereye_rgb": (0.86, 0.76, 0.78), "undereye_k": 0.8,
    "beard_rgb": (0.76, 0.86, 0.98), "beard_k": 0.5,      # the shadow of the follicles under the skin: darker, bluer
    "stubble_hex": "#2b2523", "stubble_grey_hex": "#8c8580", "stubble_cover": 0.6, "stubble_dots_scale": 1300.0,
    "scalp_rgb": (0.30, 0.27, 0.27), "scalp_k": 0.9,      # the scalp under hair: shaded and tinted by the roots
    "lips_rgb": (0.84, 0.78, 0.80), "lips_k": 0.8,
    "pore_mm": 0.12, "mottle_mm": 0.35, "wrinkle_mm": 4.0,  # bump distances; the height map spans +-2 mm
}
EYE = {
    "iris_r": 6.1,            # mm on the ball (a 12.2 mm iris)
    "pupil_r": 1.7,
    "rmap": 20.0,             # mm: IrisUV's half-width
    "iris_inner": "#7a6a55", "iris_body": "#5b4a3e", "limbal": "#2a201b",       # analysis §5: grey-hazel, no blue pixel
    "sclera": "#b9aea8", "sclera_edge": "#96766e",
    "gaze_deg": (-8.0, -14.0),   # yaw to his left, pitch up: turns the iris on the ball (the eye bones stay unposed)
}


def srgb_lin(h):
    c = [int(h.lstrip("#")[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def _ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# =========================================================================== landmarks and zone fields

def face_points(V):
    """MediaPipe landmark -> rest position (mm) on Body.Mesh, from pose_solve's face_targets.json (vertex ids and
    barycentrics on the current face). Mirrored pairs are averaged by the caller."""
    P = {}
    if os.path.exists(FACE_TARGETS):
        for L in json.load(open(FACE_TARGETS, encoding="utf-8"))["landmarks"]:
            P[int(L["mp"])] = (V[L["verts"]] * np.array(L["bary"])[:, None]).sum(0)
    return P


def sym(P, r, l=None, default=None):
    """A right-side (x < 0) point from landmark r and its mirror l."""
    pts = []
    if r in P:
        pts.append(P[r])
    if l is not None and l in P:
        pts.append(P[l] * np.array([-1.0, 1.0, 1.0]))
    if not pts:
        if default is None:
            raise KeyError(f"face landmark {r}/{l} missing from face_targets.json")
        return np.array(default, float)
    p = np.mean(pts, 0)
    if l is None:
        p[0] = 0.0
    else:
        p[0] = -abs(p[0])
    return p


def both(p):
    return [p, p * np.array([-1.0, 1.0, 1.0])]


def landmarks(bd, marks):
    V = bd["V"]
    P = face_points(V)
    nose = np.array(marks["nose_tip"]["rest_mm"])
    chin = np.array(marks["chin"]["rest_mm"])
    pup = np.array(marks["pupil_R"]["rest_mm"])
    L = {
        "nose_tip": nose, "chin": chin, "pupil": pup,
        "subnasale": sym(P, 2, default=nose + [0, 14, -12]),
        "dorsum": sym(P, 197, default=nose + [0, 12, 22]),
        "nasion": sym(P, 168, default=nose + [0, 30, 42]),
        "glabella": sym(P, 9, default=nose + [0, 28, 58]),
        "ala": sym(P, 129, 358, default=nose + [-17, 22, -6]),
        "mouth": sym(P, 61, 291, default=[-27, chin[1] - 5, chin[2] + 48]),
        "lip_top": sym(P, 0, default=nose + [0, 18, -24]),
        "lip_bot": sym(P, 17, default=chin + [0, -10, 36]),
        "eye_out": sym(P, 33, 263, default=pup + [-16, 10, 0]),
        "eye_in": sym(P, 133, 362, default=pup + [16, 4, -1]),
        "lid_low": sym(P, 145, 374, default=pup + [0, 0, -5]),
        "under_eye": sym(P, 230, 450, default=pup + [0, 3, -12]),
        "cheek": sym(P, 205, 425, default=nose + [-45, 45, -2]),
        "cheekbone": sym(P, 50, 280, default=nose + [-50, 50, 12]),
        "zygoma": sym(P, 116, 345, default=nose + [-62, 70, 22]),
        "brow_in": sym(P, 55, 285, default=pup + [16, -2, 12]),
        "brow_mid": sym(P, 52, 282, default=pup + [0, -2, 15]),
        "brow_out": sym(P, 46, 276, default=pup + [-20, 8, 12]),
        "brow_in_top": sym(P, 107, 336, default=pup + [17, -3, 20]),
        "brow_mid_top": sym(P, 105, 334, default=pup + [-2, -2, 23]),
        "brow_out_top": sym(P, 70, 300, default=pup + [-22, 8, 17]),
    }
    return L


def zone_fields(C, bd, marks, stubble=None):
    """Per-vertex zone fields (all Body.Mesh vertices; 0 off the head) for the mask textures."""
    import head as H
    V, N, g = bd["V"], bd["N"], bd["groups"]
    region = H.head_region(bd) & bd["in_body"]
    L = landmarks(bd, marks)
    E = C.edges_of(bd["F"])

    def blob(p, sig):
        out = np.zeros(len(V))
        for q in both(p) if abs(p[0]) > 1e-6 else [p]:
            out = np.maximum(out, np.exp(-0.5 * (np.linalg.norm(V - q, axis=1) / sig) ** 2))
        return out

    ears = np.clip(C.smooth_field((g["ears"] > 0.3).astype(float), E, iters=3, lam=0.5), 0, 1)
    red = np.maximum.reduce([1.0 * blob(L["nose_tip"], 11.0), 0.85 * blob(L["ala"], 8.0), 0.75 * blob(L["cheek"], 17.0),
                             0.55 * blob(L["cheekbone"], 16.0), 0.9 * ears])
    gl = L["glabella"]
    fh = _ss(gl[2] + 8.0, gl[2] + 26.0, V[:, 2]) * _ss(-0.25, -0.7, N[:, 1]) * _ss(62.0, 40.0, np.abs(V[:, 0]))
    pale = fh
    centre = gl + np.array([0.0, 4.0, 30.0])
    oil = np.maximum.reduce([0.9 * fh * np.exp(-0.5 * (np.linalg.norm(V - centre, axis=1) / 30.0) ** 2),
                             1.0 * blob(L["dorsum"], 9.0), 1.0 * blob(L["nose_tip"], 8.0), 0.6 * blob(L["zygoma"], 13.0),
                             0.35 * blob(L["chin"] + np.array([0, -4.0, 16.0]), 11.0)])
    under = blob(L["under_eye"], 6.5)
    lips = np.clip(C.smooth_field((g["lips"] > 0.3).astype(float), E, iters=1, lam=0.5), 0, 1)
    out = {"red": red, "pale": pale, "oil": oil, "undereye": under, "lips": lips}
    for k in out:
        out[k] = np.clip(out[k], 0, 1) * region
    if stubble is None:
        import head_skin
        dens, grey = head_skin.stubble_fields(_BODY[0], marks)
    else:
        dens, grey = stubble
    out["stubble"], out["grey"] = dens, grey
    return out, L


_BODY = [None]


# =========================================================================== UV rasterising

def uv_tris(body, keep=None):
    """Body.Mesh as triangles with UVs: (tri vertex ids [n,3], tri UVs [n,3,2]); keep = a vertex mask."""
    me = body.data
    uv = np.empty(len(me.loops) * 2, np.float32)
    me.uv_layers["UVMap"].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    T, U = [], []
    for p in me.polygons:
        vs = list(p.vertices)
        if keep is not None and not keep[vs].all():
            continue
        ls = list(p.loop_indices)
        for j in range(1, len(vs) - 1):
            T.append((vs[0], vs[j], vs[j + 1]))
            U.append((uv[ls[0]], uv[ls[j]], uv[ls[j + 1]]))
    return np.array(T), np.array(U, np.float64)


def rasterise(T, U, F, size=SIZE):
    """Per-vertex fields F [nv, k] -> image [size, size, k] and its cover mask; triangles where every field is 0
    are skipped."""
    img = np.zeros((size, size, F.shape[1]), np.float32)
    cover = np.zeros((size, size), bool)
    act = np.where(F[T].reshape(len(T), -1).max(1) > 1e-3)[0]
    for i in act:
        P = U[i] * (size - 1)
        x0, y0 = np.floor(P.min(0)).astype(int)
        x1, y1 = np.ceil(P.max(0)).astype(int)
        if x1 - x0 > size // 2 or y1 - y0 > size // 2:
            continue
        M = np.array([P[1] - P[0], P[2] - P[0]]).T
        det = M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0]
        if abs(det) < 1e-9:
            continue
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, size - 1) + 1), np.arange(max(y0, 0), min(y1, size - 1) + 1))
        qx, qy = xs.ravel() - P[0, 0], ys.ravel() - P[0, 1]
        a = (qx * M[1, 1] - qy * M[0, 1]) / det
        b = (qy * M[0, 0] - qx * M[1, 0]) / det
        w = np.stack([1 - a - b, a, b], 1)
        ok = (w >= -0.03).all(1)
        img[ys.ravel()[ok], xs.ravel()[ok]] = w[ok] @ F[T[i]]
        cover[ys.ravel()[ok], xs.ravel()[ok]] = True
    return img, cover


def _blur(a, r=1, n=2):
    for _ in range(n):
        for ax in (0, 1):
            a = sum(np.roll(a, k, ax) for k in range(-r, r + 1)) / (2 * r + 1)
    return a


def _dilate(a, cover, n=6):
    """Grow the covered texels outward n px (island padding)."""
    a = a.copy()
    cov = cover.copy()
    for _ in range(n):
        acc = np.zeros_like(a)
        cnt = np.zeros(a.shape[:2], np.float32)
        for ax, k in ((0, 1), (0, -1), (1, 1), (1, -1)):
            acc += np.roll(a * cov[..., None], k, ax)
            cnt += np.roll(cov, k, ax)
        new = (~cov) & (cnt > 0)
        a[new] = acc[new] / cnt[new][:, None]
        cov = cov | new
    return a


def save_image(name, arr, colorspace="Non-Color"):
    """arr [h, w, 3] in 0..1 -> a PNG in cache/head/tex, loaded as a file image and packed (a generated image
    loses its pixels on a render-engine switch: head.md §6.4)."""
    import bpy
    os.makedirs(TEX_DIR, exist_ok=True)
    h, w = arr.shape[:2]
    tmp = bpy.data.images.new(name + ".tmp", w, h, alpha=False, float_buffer=False)
    tmp.colorspace_settings.name = colorspace
    rgba = np.concatenate([np.clip(arr, 0, 1).astype(np.float32), np.ones((h, w, 1), np.float32)], 2)
    tmp.pixels.foreach_set(rgba.ravel())
    path = os.path.join(TEX_DIR, name + ".png")
    tmp.filepath_raw, tmp.file_format = path, "PNG"
    tmp.save()
    bpy.data.images.remove(tmp)
    old = bpy.data.images.get(name)
    if old is not None:
        bpy.data.images.remove(old)
    img = bpy.data.images.load(path)
    img.name = name
    img.colorspace_settings.name = colorspace
    img.pack()
    return img


# =========================================================================== wrinkles (lines in UV space)

class Surface:
    """The head's skin as a BVH with UVs: 3D point -> nearest surface point's UV (px) and texel scale."""

    def __init__(self, bd, T, U):
        from mathutils.bvhtree import BVHTree
        self.V, self.T, self.U = bd["V"], T, U
        self.bvh = BVHTree.FromPolygons([tuple(v) for v in self.V], [tuple(int(i) for i in t) for t in T])

    def _bary(self, i, p):
        a, b, c = self.V[self.T[i]]
        v0, v1, v2 = b - a, c - a, p - a
        d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        v = (d11 * d20 - d01 * d21) / den
        w = (d00 * d21 - d01 * d20) / den
        return np.array([1 - v - w, v, w])

    def nearest(self, p):
        loc, nor, i, _ = self.bvh.find_nearest(tuple(p))
        return np.array(loc), np.array(nor), i

    def ray(self, o, d):
        loc, nor, i, _ = self.bvh.ray_cast(tuple(o), tuple(d))
        return (None, None, None) if loc is None else (np.array(loc), np.array(nor), i)

    def uv_px(self, loc, i, size=SIZE):
        return (self._bary(i, loc) @ self.U[i]) * (size - 1)

    def px_per_mm(self, i, size=SIZE):
        a, b, c = self.V[self.T[i]]
        ua, ub, uc = self.U[i] * (size - 1)
        A3 = 0.5 * np.linalg.norm(np.cross(b - a, c - a))
        A2 = 0.5 * abs((ub[0] - ua[0]) * (uc[1] - ua[1]) - (ub[1] - ua[1]) * (uc[0] - ua[0]))
        return float(np.sqrt(A2 / max(A3, 1e-9)))


def wrinkle_lines(L, surf, seed=3):
    """The lines of the face as surface polylines: (points [n,3], depth mm, half-width mm). Analysis §7: two
    glabellar lines (prominent), a faint horizontal forehead crease or three, shallow crow's feet, moderate
    nasolabial folds, a faint lower-lid crease."""
    rng = np.random.default_rng(seed)
    lines = []
    gl = L["glabella"]

    def cast_front(x, z):
        loc, _, i = surf.ray((x, -400.0, z), (0.0, 1.0, 0.0))
        return loc

    def proj(P):
        return [surf.nearest(p)[0] for p in P]

    # forehead creases: three wavy horizontals, the middle one the deepest
    for dz, depth, hw in ((19.0, 0.16, 1.0), (30.0, 0.24, 1.1), (41.0, 0.14, 1.0)):
        ph = rng.uniform(0, 6.28)
        pts = []
        for x in np.linspace(-40.0, 40.0, 41):
            z = gl[2] + dz + 1.6 * np.sin(x / 11.0 + ph) - 0.0022 * x * x
            p = cast_front(x, z)
            if p is not None:
                pts.append(p)
        lines.append((pts, depth, hw))
    # the glabellar pair
    bi = L["brow_in"]
    for s in (-1.0, 1.0):
        x0 = s * 5.5
        pts = [cast_front(x0 + s * 0.8 * np.sin(t * 3.0), bi[2] - 1.0 + 15.0 * t) for t in np.linspace(0, 1, 9)]
        lines.append(([p for p in pts if p is not None], 0.42, 1.1))
    for s in (-1.0, 1.0):
        m = np.array([s, 1.0, 1.0])
        eo, ei, ll = L["eye_out"] * [-s, 1, 1], L["eye_in"] * [-s, 1, 1], L["lid_low"] * [-s, 1, 1]
        # crow's feet: three short radial lines from the outer canthus over the temple
        lat = np.array([np.sign(eo[0]) * 0.78, 0.62, 0.0])
        for ang, ln, dp in ((28.0, 8.0, 0.16), (2.0, 9.5, 0.2), (-24.0, 8.5, 0.16)):
            d = lat * np.cos(np.radians(ang)) + np.array([0, 0, 1.0]) * np.sin(np.radians(ang))
            pts = proj([eo + lat * 2.5 + d * t for t in np.linspace(0.0, ln, 7)])
            lines.append((pts, dp, 0.8))
        # the lower-lid crease
        a, b, c = ei + [0, 0, -5.5], ll + [0, 0, -6.5], eo + [0, 0, -4.0]
        pts = proj([(1 - t) ** 2 * a + 2 * t * (1 - t) * (2 * b - 0.5 * (a + c)) + t * t * c for t in np.linspace(0, 1, 13)])
        lines.append((pts, 0.2, 1.2))
        # the nasolabial fold: from beside the ala down past the mouth corner
        ala, mo = L["ala"] * [-s, 1, 1], L["mouth"] * [-s, 1, 1]
        sx = np.sign(ala[0])
        a = ala + [sx * 3.0, 2.0, 3.0]
        c = mo + [sx * 9.0, 3.0, -6.0]
        b = 0.5 * (a + c) + [sx * 5.0, 0.0, 2.0]
        pts = proj([(1 - t) ** 2 * a + 2 * t * (1 - t) * b + t * t * c for t in np.linspace(0, 1, 15)])
        lines.append((pts, 0.5, 2.6))
    return lines


def draw_lines(lines, surf, size=SIZE, span_mm=4.0):
    """The lines as a height image (0.5 = the surface, span_mm from 0 to 1): Gaussian grooves, tapered at the ends."""
    H = np.zeros((size, size), np.float32)
    for pts, depth, hw in lines:
        if len(pts) < 2:
            continue
        uvs, scl = [], []
        for p in pts:
            loc, _, i = surf.nearest(p)
            uvs.append(surf.uv_px(loc, i, size))
            scl.append(surf.px_per_mm(i, size))
        uvs, scl = np.array(uvs), np.array(scl)
        n = len(uvs)
        for k in range(n - 1):
            a, b = uvs[k], uvs[k + 1]
            if np.linalg.norm(b - a) > 60:                  # a UV seam between the samples
                continue
            s = 0.5 * (scl[k] + scl[k + 1])
            sig = max(0.8, hw * s * 0.6)
            r = int(np.ceil(3 * sig)) + 1
            x0, x1 = int(min(a[0], b[0])) - r, int(max(a[0], b[0])) + r + 1
            y0, y1 = int(min(a[1], b[1])) - r, int(max(a[1], b[1])) + r + 1
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size - 1), min(y1, size - 1)
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            ab = b - a
            t = np.clip(((xs - a[0]) * ab[0] + (ys - a[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
            d = np.hypot(xs - (a[0] + t * ab[0]), ys - (a[1] + t * ab[1]))
            taper = np.sin(np.pi * np.clip((k + t) / (n - 1), 0, 1)) ** 0.6
            g = depth * taper * np.exp(-0.5 * (d / sig) ** 2)
            H[y0:y1 + 1, x0:x1 + 1] = np.maximum(H[y0:y1 + 1, x0:x1 + 1], g)
    return np.clip(0.5 - H / span_mm, 0, 1)


# =========================================================================== node helpers

def _sock(sockets, ident):
    return next(x for x in sockets if x.identifier == ident)


class NT:
    def __init__(self, nt):
        self.nt = nt

    def new(self, kind, name=None, **props):
        n = self.nt.nodes.new(kind)
        if name:
            n.name = n.label = name
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def put(self, sock, v):
        if hasattr(v, "default_value") and hasattr(v, "node"):
            self.nt.links.new(v, sock)
        else:
            sock.default_value = v

    def mix(self, blend, fac, a, b, name=None):
        n = self.new("ShaderNodeMix", name, data_type="RGBA", blend_type=blend, clamp_factor=True)
        for ident, v in (("Factor_Float", fac), ("A_Color", a), ("B_Color", b)):
            if not hasattr(v, "node") and ident != "Factor_Float":
                v = (*v, 1.0) if len(v) == 3 else v
            self.put(_sock(n.inputs, ident), v)
        return _sock(n.outputs, "Result_Color")

    def math(self, op, a, b=None, c=None, clamp=False, name=None):
        n = self.new("ShaderNodeMath", name, operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self.put(n.inputs[i], v)
        return n.outputs[0]

    def value(self, v, name):
        n = self.new("ShaderNodeValue", name)
        n.outputs[0].default_value = v
        return n.outputs[0]

    def rgb(self, c, name):
        n = self.new("ShaderNodeRGB", name)
        n.outputs[0].default_value = (*c, 1.0)
        return n.outputs[0]


def skin_material(images, P=SKIN, name="Head.Mat.Skin"):
    """images: albedo, A, B, C. Every tunable is a named Value / RGB node (Skin.<key>), so a look loop can set it."""
    import bpy
    old = bpy.data.materials.get(name)
    if old is not None:
        bpy.data.materials.remove(old)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    n = NT(nt)
    out = n.new("ShaderNodeOutputMaterial")
    bsdf = n.new("ShaderNodeBsdfPrincipled", "Skin.BSDF")
    bsdf.subsurface_method = "RANDOM_WALK_SKIN"
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    uv = n.new("ShaderNodeUVMap", uv_map="UVMap")
    tc = n.new("ShaderNodeTexCoord")

    def tex(key, cs):
        t = n.new("ShaderNodeTexImage", "Skin.Tex." + key, image=images[key], interpolation="Cubic")
        t.image.colorspace_settings.name = cs
        nt.links.new(uv.outputs["UV"], t.inputs["Vector"])
        return t
    alb = tex("albedo", "sRGB")
    seps = {}
    for k in "ABC":
        s = n.new("ShaderNodeSeparateColor")
        nt.links.new(tex(k, "Non-Color").outputs["Color"], s.inputs["Color"])
        seps[k] = s
    stub, grey, scalp = (seps["A"].outputs[c] for c in ("Red", "Green", "Blue"))
    red, oil, pale = (seps["B"].outputs[c] for c in ("Red", "Green", "Blue"))
    under, lips, height = (seps["C"].outputs[c] for c in ("Red", "Green", "Blue"))

    def noise(scale, detail=2.0, rough=0.5, name=None):
        t = n.new("ShaderNodeTexNoise", name)
        t.inputs["Scale"].default_value, t.inputs["Detail"].default_value = scale, detail
        t.inputs["Roughness"].default_value = rough
        nt.links.new(tc.outputs["Object"], t.inputs["Vector"])
        return t.outputs["Fac"]

    col = n.mix("MULTIPLY", 1.0, alb.outputs["Color"], n.rgb(P["tone"], "Skin.tone"))
    mott = noise(95.0, 3.0, 0.55, "Skin.Mottle")                   # ~10 mm blotches: redder / yellower
    col = n.mix("MULTIPLY", 1.0, col, n.mix("MIX", mott, (1.10, 0.93, 0.91), (0.93, 1.04, 1.06)))
    # weathering: 3 mm sun blotches, browner and darker, sparse
    wth = n.math("POWER", noise(330.0, 4.0, 0.65, "Skin.Weather"), 2.0)
    col = n.mix("MULTIPLY", n.math("MULTIPLY", wth, n.value(P["weather_k"], "Skin.weather_k"), clamp=True), col, n.rgb(P["weather_rgb"], "Skin.weather_rgb"))
    for key, fac in (("red", red), ("pale", pale), ("undereye", under), ("lips", lips), ("beard", stub), ("scalp", scalp)):
        col = n.mix("MULTIPLY", n.math("MULTIPLY", fac, n.value(P[key + "_k"], f"Skin.{key}_k"), clamp=True),
                    col, n.rgb(P[key + "_rgb"], f"Skin.{key}_rgb"))
    hs = n.new("ShaderNodeHueSaturation", "Skin.HSV")
    hs.inputs["Hue"].default_value, hs.inputs["Saturation"].default_value = P["hue"], P["sat"]
    nt.links.new(col, hs.inputs["Color"])
    col = hs.outputs["Color"]
    # the stubs: dots of hair colour, greyed on the chin; on the scalp the same dots stand for the clipped fade
    dots = noise(P["stubble_dots_scale"], 1.0, 0.5, "Skin.StubbleDots")
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.42, (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.62, (1, 1, 1, 1)
    nt.links.new(dots, ramp.inputs["Fac"])
    hairy = n.math("MAXIMUM", stub, n.math("MULTIPLY", scalp, 0.8))
    dfac = n.math("MULTIPLY", n.math("MULTIPLY", hairy, ramp.outputs["Color"]), n.value(P["stubble_cover"], "Skin.stubble_cover"), clamp=True)
    hairc = n.mix("MIX", n.math("MULTIPLY", grey, 0.45, clamp=True), n.rgb(srgb_lin(P["stubble_hex"]), "Skin.stubble_rgb"),
                  n.rgb(srgb_lin(P["stubble_grey_hex"]), "Skin.stubble_grey_rgb"))
    col = n.mix("MIX", dfac, col, hairc, "Skin.Colour")
    nt.links.new(col, bsdf.inputs["Base Color"])
    # roughness
    r = n.math("MULTIPLY_ADD", oil, n.value(P["rough_oil"], "Skin.rough_oil"), n.value(P["rough"], "Skin.rough"))
    r = n.math("MULTIPLY_ADD", stub, n.value(P["rough_stubble"], "Skin.rough_stubble"), r)
    r = n.math("MULTIPLY_ADD", lips, n.value(P["rough_lips"], "Skin.rough_lips"), r)
    r = n.math("ADD", r, n.math("MULTIPLY_ADD", noise(260.0, 2.0, 0.6, "Skin.RoughNoise"), P["rough_noise"], -0.5 * P["rough_noise"]), clamp=True)
    r = n.math("ADD", r, n.math("MULTIPLY_ADD", noise(45.0, 2.0, 0.5, "Skin.RoughPatch"), P["rough_patch"], -0.5 * P["rough_patch"]), clamp=True)   # 2 cm patches: the sheen is not uniform
    nt.links.new(r, bsdf.inputs["Roughness"])
    # normal: the wrinkle height map, a coarse mottle, the pores
    b1 = n.new("ShaderNodeBump", "Skin.Bump.Wrinkles")
    b1.inputs["Strength"].default_value, b1.inputs["Distance"].default_value = 1.0, P["wrinkle_mm"] * 0.001
    nt.links.new(height, b1.inputs["Height"])
    b2 = n.new("ShaderNodeBump", "Skin.Bump.Mottle")
    b2.inputs["Strength"].default_value, b2.inputs["Distance"].default_value = 1.0, P["mottle_mm"] * 0.001
    nt.links.new(noise(420.0, 3.0, 0.6, "Skin.MottleBump"), b2.inputs["Height"])
    nt.links.new(b1.outputs["Normal"], b2.inputs["Normal"])
    vor = n.new("ShaderNodeTexVoronoi", "Skin.Pores", feature="F1")
    vor.inputs["Scale"].default_value = 2600.0                      # ~0.4 mm cells
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    b3 = n.new("ShaderNodeBump", "Skin.Bump.Pores")
    b3.inputs["Strength"].default_value, b3.inputs["Distance"].default_value = 1.0, P["pore_mm"] * 0.001
    nt.links.new(vor.outputs["Distance"], b3.inputs["Height"])
    nt.links.new(b2.outputs["Normal"], b3.inputs["Normal"])
    nt.links.new(b3.outputs["Normal"], bsdf.inputs["Normal"])
    bi = bsdf.inputs
    bi["Subsurface Weight"].default_value = P["sss_weight"]
    bi["Subsurface Radius"].default_value = P["sss_radius"]
    bi["Subsurface Scale"].default_value = P["sss_scale"]
    bi["Subsurface IOR"].default_value = P["sss_ior"]
    bi["Subsurface Anisotropy"].default_value = P["sss_anisotropy"]
    bi["IOR"].default_value = P["ior"]
    mat.diffuse_color = (*srgb_lin("#b08a74"), 1.0)
    mat["sgt_look"] = json.dumps({k: (list(v) if isinstance(v, tuple) else v) for k, v in P.items()})
    return mat


# =========================================================================== eyes

def eye_materials(P=EYE):
    import bpy
    for nm in ("Head.Mat.Eye", "Head.Mat.Cornea", "Head.Mat.Tear"):
        old = bpy.data.materials.get(nm)
        if old is not None:
            bpy.data.materials.remove(old)
    # --- the ball: iris, limbal ring, pupil, sclera from the radius in IrisUV
    mat = bpy.data.materials.new("Head.Mat.Eye")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    n = NT(nt)
    out = n.new("ShaderNodeOutputMaterial")
    bsdf = n.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    uv = n.new("ShaderNodeUVMap", uv_map="IrisUV")
    sub = n.new("ShaderNodeVectorMath", operation="SUBTRACT")
    nt.links.new(uv.outputs["UV"], sub.inputs[0])
    sub.inputs[1].default_value = (0.5, 0.5, 0.0)
    ln = n.new("ShaderNodeVectorMath", operation="LENGTH")
    nt.links.new(sub.outputs[0], ln.inputs[0])
    rmax = 16.0
    rn = n.math("MULTIPLY", ln.outputs["Value"], 2.0 * P["rmap"] / rmax, clamp=True)      # 0..1 over 0..16 mm
    ramp = n.new("ShaderNodeValToRGB", "Eye.Ramp")
    cr = ramp.color_ramp
    R, pr = P["iris_r"], P["pupil_r"]
    stops = [(0.0, (0.004, 0.003, 0.003)), ((pr - 0.15) / rmax, (0.004, 0.003, 0.003)), ((pr + 0.35) / rmax, srgb_lin(P["iris_inner"])),
             (0.62 * R / rmax, srgb_lin(P["iris_body"])), (0.93 * R / rmax, srgb_lin(P["limbal"])),
             ((R + 0.55) / rmax, srgb_lin(P["sclera"])), (1.0, srgb_lin(P["sclera_edge"]))]
    while len(cr.elements) < len(stops):
        cr.elements.new(0.5)
    for e, (pos, c) in zip(cr.elements, stops):
        e.position, e.color = pos, (*c, 1.0)
    nt.links.new(rn, ramp.inputs["Fac"])
    # radial fibres: noise on the direction, only inside the iris
    nrm = n.new("ShaderNodeVectorMath", operation="NORMALIZE")
    nt.links.new(sub.outputs[0], nrm.inputs[0])
    sc = n.new("ShaderNodeVectorMath", operation="SCALE")
    nt.links.new(nrm.outputs[0], sc.inputs[0])
    sc.inputs["Scale"].default_value = 9.0
    fib = n.new("ShaderNodeTexNoise")
    fib.inputs["Scale"].default_value, fib.inputs["Detail"].default_value = 1.0, 3.0
    nt.links.new(sc.outputs[0], fib.inputs["Vector"])
    in_iris = n.math("MULTIPLY", n.math("LESS_THAN", rn, R / rmax), n.math("GREATER_THAN", rn, (pr + 0.2) / rmax))
    k = n.math("MULTIPLY_ADD", fib.outputs["Fac"], 0.9, 0.55)                     # 0.55..1.45
    k = n.math("ADD", n.math("MULTIPLY", n.math("SUBTRACT", k, 1.0), in_iris), 1.0)
    kcol = n.new("ShaderNodeCombineColor")
    for i in range(3):
        nt.links.new(k, kcol.inputs[i])
    col = n.mix("MULTIPLY", 1.0, ramp.outputs["Color"], kcol.outputs[0])
    # faint veins on the sclera
    tc = n.new("ShaderNodeTexCoord")
    vein = n.new("ShaderNodeTexNoise")
    vein.inputs["Scale"].default_value, vein.inputs["Detail"].default_value = 300.0, 4.0
    nt.links.new(tc.outputs["Object"], vein.inputs["Vector"])
    vfac = n.math("MULTIPLY", n.math("GREATER_THAN", rn, (R + 0.6) / rmax), n.math("MULTIPLY", vein.outputs["Fac"], 0.35))
    col = n.mix("MULTIPLY", vfac, col, (0.95, 0.72, 0.68))
    nt.links.new(col, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.45
    bsdf.inputs["Subsurface Weight"].default_value = 0.0
    mat.diffuse_color = (*srgb_lin(P["sclera"]), 1.0)
    # --- the wet shell over it: a sharp reflection by Fresnel, clear otherwise, no shadow
    cor = bpy.data.materials.new("Head.Mat.Cornea")
    cor.use_nodes = True
    nt = cor.node_tree
    nt.nodes.clear()
    n = NT(nt)
    out = n.new("ShaderNodeOutputMaterial")
    gl = n.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.03
    tr = n.new("ShaderNodeBsdfTransparent")
    fr = n.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.376
    lp = n.new("ShaderNodeLightPath")
    fac = n.math("MULTIPLY", fr.outputs[0], n.math("SUBTRACT", 1.0, lp.outputs["Is Shadow Ray"]), clamp=True)
    mx = n.new("ShaderNodeMixShader")
    nt.links.new(fac, mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    cor.diffuse_color = (0.9, 0.9, 0.9, 0.1)
    cor.blend_method = "BLEND"
    # --- the tear film on the lower lid: wetter (a higher share of reflection), a little pink
    tear = bpy.data.materials.new("Head.Mat.Tear")
    tear.use_nodes = True
    nt = tear.node_tree
    nt.nodes.clear()
    n = NT(nt)
    out = n.new("ShaderNodeOutputMaterial")
    gl = n.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.05
    tr = n.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (1.0, 0.86, 0.84, 1.0)
    fr = n.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.34
    lp = n.new("ShaderNodeLightPath")
    fac = n.math("MULTIPLY", n.math("MULTIPLY_ADD", fr.outputs[0], 1.0, 0.12), n.math("SUBTRACT", 1.0, lp.outputs["Is Shadow Ray"]), clamp=True)
    mx = n.new("ShaderNodeMixShader")
    nt.links.new(fac, mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    tear.diffuse_color = (0.9, 0.8, 0.8, 0.2)
    return mat, cor, tear


def _components(me):
    import collections
    adj = collections.defaultdict(list)
    for e in me.edges:
        a, b = e.vertices
        adj[a].append(b)
        adj[b].append(a)
    lab = -np.ones(len(me.vertices), int)
    k = 0
    for i in range(len(lab)):
        if lab[i] >= 0:
            continue
        st = [i]
        lab[i] = k
        while st:
            a = st.pop()
            for b in adj[a]:
                if lab[b] < 0:
                    lab[b] = k
                    st.append(b)
        k += 1
    return lab, k


def _sphere(P):
    A = np.c_[2 * P, np.ones(len(P))]
    x = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
    c = x[:3]
    return c, float(np.sqrt(x[3] + c @ c))


def build_eyes(C, coll, rig, marks=None, P=EYE):
    """Head.Eyes: Body.Eyes' mesh and weights with the round-10 materials and the IrisUV map. Returns the object
    and per-eye numbers (centre, radius of the shell, the iris axis)."""
    import bpy
    src = bpy.data.objects["Body.Eyes"]
    old = bpy.data.objects.get("Head.Eyes")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name, ob.data.name = "Head.Eyes", "Head.Eyes"
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    ob.hide_render = ob.hide_viewport = False
    me = ob.data
    mats = eye_materials(P)
    me.materials.clear()
    me.materials.append(mats[0])
    me.materials.append(mats[1])
    V = np.array([v.co[:] for v in me.vertices]) * 1000.0
    lab, k = _components(me)
    info, outer, eyes = {}, np.zeros(len(V), bool), {}
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        comps = [np.where(lab == i)[0] for i in range(k) if sgn * V[lab == i, 0].mean() > 0]
        fits = [(_sphere(V[c]), c) for c in comps]
        fits.sort(key=lambda f: f[0][1])
        (c_in, r_in), inner = fits[0]
        (c_out, r_out), shell = fits[-1]
        outer[shell] = True
        # the iris axis: where the ball's front dips in from the sphere (MPFB's iris is concave), else -Y
        d = np.linalg.norm(V[inner] - c_in, axis=1)
        dip = inner[(d < r_in - 0.6) & (V[inner, 1] < c_in[1])]
        f = (V[dip].mean(0) - c_in) if len(dip) >= 3 else np.array([0.0, -1.0, 0.0])
        if marks is not None and f"pupil_{side}" in marks:      # base.py's pupil mark: the centre of MPFB's iris
            f = np.array(marks[f"pupil_{side}"]["rest_mm"]) - c_in
        f /= np.linalg.norm(f)
        yaw, pitch = (np.radians(a) for a in P["gaze_deg"])
        up0 = np.array([0.0, 0.0, 1.0])
        right0 = np.cross(up0, f)
        right0 /= np.linalg.norm(right0)
        f = f * np.cos(yaw) * np.cos(pitch) + right0 * np.sin(yaw) * np.cos(pitch) + up0 * np.sin(pitch)
        f /= np.linalg.norm(f)
        right = np.cross(up0, f)
        right /= np.linalg.norm(right)
        up = np.cross(f, right)
        eyes[side] = {"centre": c_in, "r_in": r_in, "c_out": c_out, "r_out": r_out, "axis": f, "right": right, "up": up,
                      "inner": inner, "shell": shell}
        info[side] = {"centre_mm": [round(float(x), 1) for x in c_in], "ball_r_mm": round(r_in, 2), "shell_r_mm": round(r_out, 2),
                      "iris_axis": [round(float(x), 3) for x in f], "iris_dip_verts": int(len(dip))}
    uvl = me.uv_layers.get("IrisUV") or me.uv_layers.new(name="IrisUV")
    side_of = np.where(V[:, 0] > 0, "L", "R")
    UV = np.full((len(V), 2), 3.0)
    for i in range(len(V)):
        e = eyes[side_of[i]]
        q = V[i] - e["centre"]
        if q @ e["axis"] > 0:
            UV[i] = 0.5 + np.array([q @ e["right"], q @ e["up"]]) / (2.0 * P["rmap"])
    loops = np.empty(len(me.loops), int)
    me.loops.foreach_get("vertex_index", loops)
    uvl.data.foreach_set("uv", UV[loops].ravel())
    pm = np.array([1 if outer[list(p.vertices)].all() else 0 for p in me.polygons])
    me.polygons.foreach_set("material_index", pm)
    me.update()
    for m in ob.modifiers:
        if m.type == "ARMATURE":
            m.object = rig
    ob["sgt_clay"] = (0.85, 0.83, 0.8)
    info["shell_faces"] = int(pm.sum())
    return ob, info, eyes


def split_wet(coll, eyes_ob):
    """Move the wet shell's faces (material slot 1) out of Head.Eyes into Head.Eyes.Wet, a render-only object
    (ob["sgt_role"] = "render"): an engine export keeps the ball and drops the shell. Call after lid_lines(),
    which reads the shell from Head.Eyes."""
    import bmesh
    import bpy
    old = bpy.data.objects.get("Head.Eyes.Wet")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    wet = eyes_ob.copy()
    wet.data = eyes_ob.data.copy()
    wet.name, wet.data.name = "Head.Eyes.Wet", "Head.Eyes.Wet"
    coll.objects.link(wet)
    for ob, drop in ((eyes_ob, 1), (wet, 0)):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == drop], context="FACES")
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
    wet["sgt_role"] = "render"
    wet["sgt_clay"] = (0.85, 0.83, 0.8)
    return wet


def lid_lines(bd, eyes_ob, eyes, L, n=26):
    """Where the lids' skin meets the eyeball's shell (the zero crossing of the skin's signed distance to the
    shell), per eye: {"lower": points [n,3], "upper": ...} ordered from the inner canthus out, with the shell's
    outward normals. The split is the line through the canthi."""
    from mathutils.bvhtree import BVHTree
    V, F = bd["V"], bd["F"]
    me = eyes_ob.data
    EV = np.array([v.co[:] for v in me.vertices]) * 1000.0
    out = {}
    for side, e in eyes.items():
        sgn = 1.0 if side == "L" else -1.0
        idx = {int(v): i for i, v in enumerate(e["shell"])}
        polys = [tuple(idx[v] for v in p.vertices) for p in me.polygons if all(v in idx for v in p.vertices)]
        bvh = BVHTree.FromPolygons([tuple(EV[v]) for v in e["shell"]], polys)
        near = np.where(bd["in_body"] & (np.linalg.norm(V - e["c_out"], axis=1) < e["r_out"] + 9.0) & (V[:, 1] < e["c_out"][1] + 2.0))[0]
        sd = {}
        for i in near:
            loc, nor, _, dist = bvh.find_nearest(tuple(V[i]))
            sd[int(i)] = dist if np.dot(V[i] - np.array(loc), V[i] - e["c_out"]) >= 0 else -dist
        eo, ei = L["eye_out"] * [-sgn, 1, 1], L["eye_in"] * [-sgn, 1, 1]
        pts = {"lower": [], "upper": []}
        seen = set()
        for f in F:
            if not all(v in sd for v in f):
                continue
            for a, b in zip(f, f[1:] + f[:1]):
                key = (min(a, b), max(a, b))
                if key in seen or sd[a] * sd[b] >= 0:
                    continue
                seen.add(key)
                t = sd[a] / (sd[a] - sd[b])
                p = V[a] + t * (V[b] - V[a])
                tx = (p[0] - ei[0]) / (eo[0] - ei[0])
                if -0.08 <= tx <= 1.08:
                    dz = p[2] - (ei[2] + tx * (eo[2] - ei[2]))
                    if abs(dz) > 0.8:
                        pts["lower" if dz < 0 else "upper"].append((tx, p))
        out[side] = {"centre": e["c_out"], "crossings": {k: len(v) for k, v in pts.items()}}
        for k, pl in pts.items():
            if len(pl) < 5:
                continue
            pl.sort(key=lambda q: q[0])
            tt = np.array([t for t, _ in pl])
            Pl = np.array([p for _, p in pl])
            ts = np.linspace(tt.min(), tt.max(), n)
            Ps = np.stack([np.interp(ts, tt, _blur1(Pl[:, c])) for c in range(3)], 1)
            nrm = Ps - e["c_out"]
            nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
            out[side][k] = Ps
            out[side][k + "_n"] = nrm
    return out


def build_tearline(C, coll, body, rig, lids, radius=0.42):
    """Head.Tearline: a thin wet tube along the lower lid's margin, where the skin meets the eyeball."""
    import bpy
    tubesV, tubesF, info = [], [], {}
    nv = 0
    for side, e in lids.items():
        info[side] = dict(e["crossings"])
        if "lower" not in e:
            continue
        nrm = e["lower_n"]
        Ps = e["lower"] + nrm * (radius * 0.55)
        tan = np.gradient(Ps, axis=0)
        tan /= np.linalg.norm(tan, axis=1, keepdims=True)
        bin_ = np.cross(tan, nrm)
        bin_ /= np.linalg.norm(bin_, axis=1, keepdims=True)
        segs = 6
        rr = radius * np.sin(np.pi * np.linspace(0.04, 0.96, len(Ps))) ** 0.5
        for j in range(len(Ps)):
            for k in range(segs):
                a = 2 * np.pi * k / segs
                tubesV.append(Ps[j] + rr[j] * (np.cos(a) * nrm[j] + np.sin(a) * bin_[j]))
        for j in range(len(Ps) - 1):
            for k in range(segs):
                a0, a1 = nv + j * segs + k, nv + j * segs + (k + 1) % segs
                tubesF.append((a0, a1, a1 + segs, a0 + segs))
        nv += len(Ps) * segs
        info[side]["length_mm"] = round(float(np.linalg.norm(np.diff(Ps, axis=0), axis=1).sum()), 1)
    old = bpy.data.objects.get("Head.Tearline")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    if not tubesV:
        return None, info
    ob = C.mesh_object("Head.Tearline", np.array(tubesV), tubesF, coll, mat=bpy.data.materials["Head.Mat.Tear"])
    ob["sgt_clay"] = (0.8, 0.7, 0.7)
    ob["sgt_role"] = "render"
    C.bind(ob, body, rig)
    return ob, info


def _blur1(x, n=2):
    x = np.asarray(x, float).copy()
    for _ in range(n):
        x[1:-1] = 0.25 * x[:-2] + 0.5 * x[1:-1] + 0.25 * x[2:]
    return x


# =========================================================================== build, save, assemble

def build_skin(C, body, bd, marks, scalp_cover=None, stubble=None, params=None):
    """The mask textures and Head.Mat.Skin. scalp_cover: per-vertex hair cover of the scalp (head_groom)."""
    import bpy
    import head as H
    _BODY[0] = body
    P = dict(SKIN, **(params or {}))
    Z, L = zone_fields(C, bd, marks, stubble)
    region = H.head_region(bd) & bd["in_body"]
    keep = bd["in_body"].copy()
    T, U = uv_tris(body, keep)
    nv = len(bd["V"])
    sc = np.zeros(nv) if scalp_cover is None else scalp_cover
    A = np.stack([Z["stubble"], Z["grey"], sc], 1)
    B = np.stack([Z["red"], Z["oil"], Z["pale"]], 1)
    Cc = np.stack([Z["undereye"], Z["lips"], np.zeros(nv)], 1)
    imgs = {}
    for key, Fv in (("A", A), ("B", B), ("C", Cc)):
        im, cov = rasterise(T, U, Fv.astype(np.float32))
        im = _blur(_dilate(im, cov, 6), 1, 1)
        imgs[key] = im
    head_T = np.array([i for i, t in enumerate(T) if region[t].all()])
    surf = Surface(bd, T[head_T], U[head_T])
    lines = wrinkle_lines(L, surf)
    imgs["C"][..., 2] = _blur(draw_lines(lines, surf, span_mm=P["wrinkle_mm"]), 1, 1)
    scale = float(np.median([surf.px_per_mm(i) for i in range(0, len(head_T), 23)]))
    src = bpy.data.node_groups["Body.Skin.Group"].nodes["DiffuseTexture"].image
    w, h = src.size
    px = np.empty(w * h * 4, np.float32)
    src.pixels.foreach_get(px)
    alb = px.reshape(h, w, 4)[..., :3]
    images = {"albedo": save_image("Head.Skin.Albedo", alb, "sRGB")}
    for key in "ABC":
        images[key] = save_image("Head.Skin.Mask" + key, imgs[key])
    mat = skin_material(images, P)
    info = {"texel_px_per_mm": round(scale, 2), "wrinkle_lines": len(lines), "size": SIZE,
            "zones": {k: int((v > 0.05).sum()) for k, v in Z.items()}, "params": P}
    return mat, info, L


def save_look(mats):
    """cache/parts/head_look.blend: the materials on_assemble() puts on base.blend's objects."""
    import bpy
    os.makedirs(os.path.dirname(LOOK_BLEND), exist_ok=True)
    tmp = LOOK_BLEND + ".tmp.blend"
    bpy.data.libraries.write(tmp, set(mats), path_remap="NONE", fake_user=True, compress=False)
    os.replace(tmp, LOOK_BLEND)
    return LOOK_BLEND


HIDE = ("Body.Eyes", "Body.Eyebrows", "Body.Eyelashes")


def apply_to_scene(body, skin, coll=None):
    """Put the head part's skin on Body.Mesh and hide what the part replaces (the eyes always; the brow and lash
    cards when the part carries its own)."""
    import bpy
    body.data.materials[0] = skin
    have = {o.name for o in coll.all_objects} if coll is not None else set()
    hidden = []
    for nm, mine in (("Body.Eyes", "Head.Eyes"), ("Body.Eyebrows", "Head.Brows"), ("Body.Eyelashes", "Head.Lashes")):
        o = bpy.data.objects.get(nm)
        if o is not None and (coll is None or mine in have):
            o.hide_render = o.hide_viewport = True
            hidden.append(nm)
    return hidden


def attach_to_bones(coll, rig):
    """The part's curves (hair, brows, lashes) ride one bone each (ob["sgt_bone"]); they are saved unparented, in
    rest world coordinates, and parented here with the inverse of the bone's REST matrix, whatever the pose."""
    from mathutils import Matrix
    done = []
    for ob in coll.all_objects:
        bone = ob.get("sgt_bone")
        if not bone or bone not in rig.data.bones:
            continue
        b = rig.data.bones[bone]
        ob.parent, ob.parent_type, ob.parent_bone = rig, "BONE", bone
        ob.matrix_parent_inverse = (rig.matrix_world @ b.matrix_local @ Matrix.Translation((0.0, b.length, 0.0))).inverted()
        ob.matrix_basis = Matrix.Identity(4)
        done.append(ob.name)
    return done


def on_assemble(body, rig, coll):
    """Called by scripts/assemble.py after the parts are loaded: Head.Mat.Skin from cache/parts/head_look.blend
    onto Body.Mesh, base.py's eyes (and the cards the part replaces) hidden."""
    import bpy
    if not os.path.exists(LOOK_BLEND):
        return {"applied": False, "why": "no cache/parts/head_look.blend (rebuild the head part)"}
    with bpy.data.libraries.load(LOOK_BLEND, link=False) as (src, dst):
        dst.materials = [m for m in src.materials if m == "Head.Mat.Skin"]
    if not dst.materials:
        return {"applied": False, "why": "head_look.blend has no Head.Mat.Skin"}
    skin = dst.materials[0]
    hidden = apply_to_scene(body, skin, coll)
    return {"applied": True, "skin": skin.name, "hidden": hidden, "on_bones": attach_to_bones(coll, rig)}
