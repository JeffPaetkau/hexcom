"""Soft gear shapes (round 10, carrier and belt lane): Cordura pouches built as fabric around their contents instead of
bevelled boxes (critics r9 m28, m33, G1 D3, D13: "soft kit reads as hard boxes"), and a fabric noise for slabs.

    import softgear as SG
    objs = SG.soft_pouch("Carrier.Pouch.1", coll, (64, 38, 178), M, mats, drop=54, bulge=4.0, seed=1)
    SG.fabric_noise(ob, amp=0.8, scale=45.0, outward=(0, -1, 0))

soft_pouch builds in the pouch's own frame M (4 x 4, mm: columns x across, y out of the backing, z up; origin the body's
centre, its back face at y = -d/2):
  - the body: a superellipse section (square-ish at the back, where it is sewn to the backing; round-cornered at the front,
    exponent `pf`), its bottom rounded over `rb`, the front bulging `bulge` mm at mid-height over the magazine (falling to
    nothing at the corners and the ends), the sides pinched out `side_bulge`, and a low-frequency fabric noise;
  - the flap (optional): a 3.5 mm slab that lies `gap` off the body's top, crowned `dome` mm over the magazine's top,
    rounds over the front edge (radius `rc`) and drapes `drop` mm down the front, following the body's own front and its
    rounded corners (so at the edges it wraps round them), its hem flaring a little; a bound edge (tube) round its free
    sides and hem; bound vertical seams (piping) down the body's front corners;
  - a pull tab down the flap's centre to `tab_below` under the hem, with a square slide-lock plate at the hem (drawn).
Weights are the caller's (the objects are world-space identity meshes). Takes 0.1-0.3 s a pouch.
"""
import math

import numpy as np

import common as C
import gear_common as G


# --------------------------------------------------------------------------- noise

def _hash(ix, iy, iz, table):
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791)
    return table[np.bitwise_and(h, 4095)]


def vnoise(P, scale, seed=0):
    """Smooth value noise in [-1, 1] at points P (n, 3) mm, feature size `scale` mm."""
    table = np.random.default_rng(seed).uniform(-1.0, 1.0, 4096)
    X = np.asarray(P, float) / scale
    i0 = np.floor(X).astype(np.int64)
    f = X - i0
    s = f * f * (3.0 - 2.0 * f)
    out = 0.0
    for dx in (0, 1):
        wx = s[:, 0] if dx else 1.0 - s[:, 0]
        for dy in (0, 1):
            wy = s[:, 1] if dy else 1.0 - s[:, 1]
            for dz in (0, 1):
                wz = s[:, 2] if dz else 1.0 - s[:, 2]
                out = out + wx * wy * wz * _hash(i0[:, 0] + dx, i0[:, 1] + dy, i0[:, 2] + dz, table)
    return out


def fbm(P, scale, seed=0):
    return 0.7 * vnoise(P, scale, seed) + 0.3 * vnoise(P, scale * 0.45, seed + 7)


def fabric_noise(ob, amp=0.8, scale=45.0, seed=0, outward=None, only_out=0.3, positive=True, mask=None):
    """Displace a mesh's vertices along their normals by a low-frequency noise (amp mm): the soft unevenness of padded
    Cordura. With `outward` (a direction), only vertices whose normal faces it by more than `only_out` move (a bag's
    outer face, never its inner one toward the shirt); `positive` keeps every move outward; mask(V mm) -> weights 0..1."""
    me = ob.data
    n = len(me.vertices)
    V = np.zeros(n * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3) * 1000.0
    Nn = np.zeros(n * 3)
    me.vertices.foreach_get("normal", Nn)
    Nn = Nn.reshape(-1, 3)
    d = fbm(V, scale, seed)
    if positive:
        d = 0.5 * (d + 1.0)
    w = np.ones(n)
    if outward is not None:
        o = G.unit(np.asarray(outward, float))
        w = np.clip((Nn @ o - only_out) / max(1.0 - only_out, 1e-3), 0.0, 1.0)
    if mask is not None:
        w = w * np.asarray(mask(V), float)
    V = V + Nn * (amp * d * w)[:, None]
    me.vertices.foreach_set("co", (V / 1000.0).ravel())
    me.update()
    return ob


# --------------------------------------------------------------------------- the pouch

def _sec(t, a, bf, bb, pf, pb):
    c, s = np.cos(t), np.sin(t)
    p = np.where(s > 0, pf, pb)
    x = a * np.sign(c) * np.abs(c) ** (2.0 / p)
    y = np.where(s > 0, bf, bb) * np.sign(s) * np.abs(s) ** (2.0 / p)
    return x, y


def _front_y(x, a, bf, pf):
    """The section's front y at x (|x| < a)."""
    r = np.clip(1.0 - np.abs(x / a) ** pf, 0.0, 1.0)
    return bf * r ** (1.0 / pf)


def _resample(Q, n):
    Q = np.asarray(Q, float)
    L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))])
    t = np.linspace(0.0, L[-1], n)
    return np.column_stack([np.interp(t, L, Q[:, k]) for k in range(Q.shape[1])])


def soft_pouch(name, coll, size, M, mat, bind_mat=None, flap=True, drop=50.0, bulge=4.0, side_bulge=1.2, pf=3.2,
               pb=9.0, rb=None, gap=1.0, dome=5.0, rc=9.0, flap_t=3.5, noise=0.7, seed=0, tab=True, tab_mat=None,
               plate_mat=None, tab_below=16.0, piping=True, K=56, nz=34, nu=27, ns=30, top_cap=True, rim=False):
    """Build the pouch (see the module docstring). Returns {"body", "flap", "binding", "piping", "tab", "plate"} (the
    objects that were made) and "hem_z" (the flap hem's height in the local frame)."""
    w, d, h = [float(v) for v in size]
    a, bf, bb = w / 2.0, d / 2.0, d / 2.0
    z0, z1 = -h / 2.0, h / 2.0
    rb = min(9.0, 0.45 * min(a, d)) if rb is None else rb
    R3, O = np.asarray(M, float)[:3, :3], np.asarray(M, float)[:3, 3]

    def world(P):
        return np.asarray(P, float) @ R3.T + O

    bind_mat = bind_mat or mat
    tab_mat = tab_mat or bind_mat
    plate_mat = plate_mat or tab_mat
    out = {}

    def g(z):
        zz = np.clip((z - z0) / h, 0.0, 1.0)
        return np.sin(math.pi * zz) ** 0.7

    # ---- body rings
    ts = np.linspace(0.0, 2.0 * math.pi, K, endpoint=False)
    rings = []
    nb = 6
    for k in range(nb):                                   # rounded bottom
        ph = (math.pi / 2.0) * k / nb
        rings.append((z0 + rb - rb * math.cos(ph), rb - rb * math.sin(ph)))
    for z in np.linspace(z0 + rb, z1, nz):
        rings.append((float(z), 0.0))
    V = []
    for z, e in rings:
        x, y = _sec(ts, a - e, bf - e, bb - 0.5 * e, pf, pb)
        front = y > 0
        y = y + np.where(front, bulge * g(z) * np.clip(1.0 - (x / a) ** 2, 0.0, 1.0), 0.0)
        x = x + np.sign(x) * side_bulge * g(z) * np.abs(np.cos(ts)) ** 3
        V.append(np.column_stack([x, y, np.full(K, z)]))
    V = np.array(V)                                       # (rings, K, 3)
    if noise > 0:
        flat = V.reshape(-1, 3)
        dirs = flat[:, :2] / np.maximum(np.linalg.norm(flat[:, :2], axis=1, keepdims=True), 1e-6)
        wgt = np.clip((flat[:, 1] + 0.5 * bb) / (bf + 0.5 * bb), 0.25, 1.0)
        dn = noise * fbm(flat, 38.0, seed) * wgt
        flat[:, :2] += dirs * dn[:, None]
        V = flat.reshape(V.shape)
    nr = len(rings)
    verts = list(V.reshape(-1, 3))
    F = []
    for r in range(nr - 1):
        for i in range(K):
            j = (i + 1) % K
            F.append((r * K + i, r * K + j, (r + 1) * K + j, (r + 1) * K + i))
    cb = len(verts)
    verts.append(V[0].mean(0))
    for i in range(K):
        F.append((cb, (i + 1) % K, i))
    if top_cap:
        ct = len(verts)
        verts.append(V[-1].mean(0))
        base = (nr - 1) * K
        for i in range(K):
            F.append((ct, base + i, base + (i + 1) % K))
    out["body"] = G.new_mesh(name, world(np.array(verts)), F, coll, mat, bevel_mm=0.0, angle=75.0)

    hem_z = None
    if flap:
        # ---- flap: per across-station x, the envelope profile (y, z): over the top (crowned over the magazine), round
        # the front edge, down the front following the body's front at that x; offset `gap` outward
        xs = (a + 1.8) * np.sin(np.linspace(-math.pi / 2, math.pi / 2, nu))
        y_h = -bb * 0.55
        P = []
        for x in xs:
            xb = float(np.clip(x, -a * 0.985, a * 0.985))
            yft = float(_front_y(xb, a, bf, pf))
            rce = min(rc, max(1.5, 0.45 * (yft - y_h)))
            ym, hw = 0.5 * (y_h + yft), 0.5 * (yft - y_h) + 0.3 * rce
            edge = max(0.0, (abs(x) - a * 0.85) / (a * 0.15 + 1.8))       # the crown falls off toward the side edges

            def ztop(y):
                return z1 + dome * max(0.0, 1.0 - ((y - ym) / hw) ** 2) * (1.0 - 0.6 * edge)
            prof = [(y, ztop(y)) for y in np.linspace(y_h, yft - rce, 10)]
            zc = ztop(yft - rce) - rce
            for k in range(1, 9):
                an = (math.pi / 2.0) * (1.0 - k / 8.0)
                prof.append((yft - rce + rce * math.cos(an), zc + rce * math.sin(an)))
            for z in np.linspace(zc - 2.0, z1 - drop, 14):
                yy = float(_front_y(xb, a, bf, pf)) + bulge * g(z) * max(0.0, 1.0 - (xb / a) ** 2)
                prof.append((yy, float(z)))
            prof = np.array(prof)
            # offset by gap along the profile's outward normal (2-D)
            T = np.gradient(prof, axis=0)
            Nn = np.column_stack([T[:, 1], -T[:, 0]])
            Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-9)
            prof = prof + Nn * gap
            prof = _resample(prof, ns)
            # hem flare and a slight droop past the body's side
            tt = np.linspace(0.0, 1.0, ns)
            prof[:, 0] += 1.6 * np.clip((tt - 0.75) / 0.25, 0.0, 1.0) ** 2
            over = max(0.0, abs(x) - a)
            prof[:, 1] -= 1.5 * over
            P.append(np.column_stack([np.full(ns, x), prof]))
        P = np.array(P)                                    # (nu, ns, 3)
        if noise > 0:
            fl = P.reshape(-1, 3)
            fl[:, 1:] += 0.4 * noise * fbm(fl, 30.0, seed + 3)[:, None] * np.array([0.6, 0.4])
            P = fl.reshape(P.shape)
        du = np.gradient(P, axis=0)
        dv = np.gradient(P, axis=1)
        N = np.cross(du, dv)
        N /= np.maximum(np.linalg.norm(N, axis=2, keepdims=True), 1e-9)
        ref = P - np.array([0.0, 0.0, z1 - 0.3 * h])
        if float(np.sum(N * ref)) < 0:
            N = -N
        Vf, Ff = G.slab_from_grid(P, N, flap_t)
        out["flap"] = G.new_mesh(f"{name}.Flap", world(Vf), Ff, coll, mat, bevel_mm=0.0, angle=75.0)
        hem_z = float(P[nu // 2, -1, 2])
        # bound edge: up one side, across the hem, up the other
        mid = P + N * (flap_t * 0.5)
        edge = np.concatenate([mid[0, ::-1], mid[1:-1, -1], mid[-1, :]])
        out["binding"] = G.tube(f"{name}.Flap.Binding", coll, world(edge), flap_t * 0.5 + 0.7, bind_mat, sides=8,
                                step=2.0)
        if tab:
            c = nu // 2
            k0 = int(ns * 0.45)
            tp = list(P[c, k0:] + N[c, k0:] * (flap_t + 0.3))
            tn = list(N[c, k0:])
            last, ln = tp[-1], tn[-1]
            for dz in np.linspace(3.0, tab_below, 4):
                z = last[2] - dz
                yy = float(_front_y(0.0, a, bf, pf)) + bulge * g(z) + 0.6 + 2.0 * (1.0 - dz / tab_below)
                tp.append(np.array([0.0, yy, z]))
                tn.append(np.array([0.0, 1.0, 0.0]))
            tp = np.array(tp)
            W = world(tp)
            Wn = [R3 @ v for v in tn]
            out["tab"] = G.strip(f"{name}.Tab", coll, W, Wn, 20.0, 2.0, tab_mat, bevel_mm=0.6)
            # the square slide-lock plate at the hem (drawn on the pouches' tabs)
            ph = P[c, -1] + N[c, -1] * (flap_t + 2.5 + 1.8)
            Mp = np.eye(4)
            Mp[:3, :3] = R3 @ np.column_stack([[1.0, 0.0, 0.0], G.unit(N[c, -1]), np.cross([1.0, 0.0, 0.0], G.unit(N[c, -1]))])
            Mp[:3, 3] = world(ph[None])[0]
            out["plate"] = G.rbox(f"{name}.Plate", coll, (24.0, 3.6, 20.0), Mp, plate_mat, bevel_mm=1.0)
    if piping:
        # bound vertical seams down the body's front corners (under the flap at the top)
        ztop = (hem_z + 6.0) if hem_z is not None else z1
        idx = [int(round(K * 0.11)), int(round(K * 0.39))]
        pipes = []
        for i in idx:
            pts = [V[r, i] for r in range(nb, nr) if V[r, i, 2] < ztop]
            pts = np.array(pts)
            if len(pts) < 3:
                continue
            dirs = pts[:, :2] / np.maximum(np.linalg.norm(pts[:, :2], axis=1, keepdims=True), 1e-6)
            pts[:, :2] += dirs * 0.3
            pipes.append(G.tube(f"{name}.Piping.{len(pipes) + 1}", coll, world(pts), 1.4, bind_mat, sides=6, step=3.0))
        if pipes:
            out["piping"] = G.join(pipes[0], pipes[1:])
    if rim and not flap:
        # an open-top pouch: its mouth bound (a tube round the top ring, a little inside the section)
        ring = V[-1].copy()
        dirs = ring[:, :2] / np.maximum(np.linalg.norm(ring[:, :2], axis=1, keepdims=True), 1e-6)
        ring[:, :2] -= dirs * 0.6
        out["rim"] = G.tube(f"{name}.Rim", coll, world(np.vstack([ring, ring[:1]])), 2.6, bind_mat, closed=False,
                            sides=8, step=2.0)
    out["hem_z"] = hem_z
    return out


def face_band(name, coll, size, M, z, width, thick, mat, bulge=4.0, pf=3.2, frac=0.94, n=17):
    """A webbing band (a PALS row, an elastic) lying across a soft_pouch's front at local height z, following its
    section and the magazine's bulge (frame M and size as soft_pouch's)."""
    w, d, h = [float(v) for v in size]
    a, bf = w / 2.0, d / 2.0
    zz = np.clip((z + h / 2.0) / h, 0.0, 1.0)
    g = math.sin(math.pi * zz) ** 0.7
    R3, O = np.asarray(M, float)[:3, :3], np.asarray(M, float)[:3, 3]
    xs = np.linspace(-a * frac, a * frac, n)
    P = np.array([[x, float(_front_y(x, a, bf, pf)) + bulge * g * max(0.0, 1.0 - (x / a) ** 2) + 0.4, z] for x in xs])
    T = np.gradient(P, axis=0)
    Nl = np.column_stack([-T[:, 1], T[:, 0], np.zeros(n)])
    Nl /= np.maximum(np.linalg.norm(Nl, axis=1, keepdims=True), 1e-9)
    Nl[Nl[:, 1] < 0] *= -1.0
    return G.strip(name, coll, P @ R3.T + O, [R3 @ v for v in Nl], width, thick, mat, bevel_mm=0.5)


def objects(res):
    return [v for k, v in res.items() if k != "hem_z" and v is not None]
