"""Sculpting by script (spec 01 §4.2; owned by part 01, reused by the hands, face and neck parts).

Brushes work on numpy arrays of positions, in whatever unit the caller uses (part 01 works in millimetres
in a foot's frame), and come in two forms: a field, the displacement of every vertex for a unit amount, and
the spec's in-place calls (soft_move, soft_inflate, flatten_to_plane, soft_rotate, laplacian_smooth). A
field is linear in its amount, so a sculpt made of fields is a linear model of its amounts exactly as MPFB's
targets are of their weights, and the amounts can be solved by least squares against measured dimensions
(spec 18 §4.8.5) instead of being set by hand.

Falloffs map t = distance / radius in [0, 1] to a weight that is 1 at the centre and 0 at the radius:
'smooth' is the sculpt-brush smoothstep 3s² - 2s³ of s = 1 - t, 'sharp' (1 - t)³, 'linear' 1 - t, and
'gauss' exp(-4.5 t²) (cut at the radius, where it is 0.011), the Gaussian specs 03 and 04 use.

Shape keys: mix() reads the relative-key mix of a mesh without the depsgraph (so helper geometry hidden
by a Mask modifier is there too), and key_from_positions() stores sculpted positions as a new key holding
basis + (sculpted - mix), which adds exactly the sculpt on top of whatever the other keys do (spec 01 §4.1).
Measuring is not here: spec 18's measure.py does it.
"""
import math

import numpy as np

FALLOFFS = ("smooth", "sharp", "linear", "gauss")


# --------------------------------------------------------------------------- falloffs and weights

def falloff(t, kind="smooth"):
    """Weight for t = d / r (clipped to [0, 1]): 1 at the centre, 0 at the radius."""
    t = np.clip(np.asarray(t, float), 0.0, 1.0)
    s = 1.0 - t
    if kind == "smooth":
        return s * s * (3.0 - 2.0 * s)
    if kind == "sharp":
        return s ** 3
    if kind == "linear":
        return s
    if kind == "gauss":
        return np.where(t < 1.0, np.exp(-4.5 * t * t), 0.0)
    raise ValueError(f"falloff {kind!r}: one of {FALLOFFS}")


def smoothstep(x, a, b):
    """0 below a, 1 above b (or the reverse when b < a), smooth in between."""
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def sphere_weights(co, centre, radius, kind="smooth", scale=(1.0, 1.0, 1.0)):
    """Brush weights of a sphere (an ellipsoid with `scale` per axis) around centre."""
    d = (np.asarray(co, float) - np.asarray(centre, float)) / np.asarray(scale, float)
    return falloff(np.sqrt((d * d).sum(axis=1)) / radius, kind)


def segment_distance(co, a, b):
    """Distance of each point to the segment a-b, and the parameter (0 at a, 1 at b) of its foot."""
    co, a, b = np.asarray(co, float), np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    t = np.clip(((co - a) @ ab) / max(float(ab @ ab), 1e-30), 0.0, 1.0)
    return np.linalg.norm(co - (a + t[:, None] * ab), axis=1), t


def line_weights(co, points, radius, kind="smooth"):
    """Brush weights of a capsule along a polyline (spec 04's soft_line): the falloff of the distance to
    the nearest segment."""
    pts = np.asarray(points, float)
    d = np.full(len(co), np.inf)
    for a, b in zip(pts[:-1], pts[1:]):
        d = np.minimum(d, segment_distance(co, a, b)[0])
    return falloff(d / radius, kind)


# --------------------------------------------------------------------------- fields (unit amounts)

def move_field(co, centre, radius, vector, kind="smooth", weights=None):
    """soft_move's displacement: vector times the brush weight (times extra weights, if given)."""
    w = sphere_weights(co, centre, radius, kind)
    if weights is not None:
        w = w * weights
    return w[:, None] * np.asarray(vector, float)[None, :]


def inflate_field(co, normals, centre, radius, kind="smooth", weights=None):
    """soft_inflate's displacement for amount 1: along each vertex normal."""
    w = sphere_weights(co, centre, radius, kind)
    if weights is not None:
        w = w * weights
    return w[:, None] * np.asarray(normals, float)


def scale_field(co, centre, axis, weights):
    """Displacement of a scale by +1 along an axis about a centre (per vertex, so a centre line works):
    ((p - c) . a) a w. A scale by s is this field times s - 1."""
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    d = (np.asarray(co, float) - np.asarray(centre, float)) @ a
    return (d * weights)[:, None] * a[None, :]


def rotation_field(co, pivot, axis, angle_deg, weights):
    """Displacement of a rotation about an axis through pivot, blended by weights (not linear in the
    angle: a fixed operation, not an amount to fit)."""
    co = np.asarray(co, float)
    R = rotation_matrix(axis, math.radians(angle_deg))
    p = co - np.asarray(pivot, float)
    return ((p @ R.T) - p) * np.asarray(weights, float)[:, None]


def rotation_matrix(axis, angle):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    x, y, z = a
    c, s = math.cos(angle), math.sin(angle)
    C = 1.0 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


# --------------------------------------------------------------------------- the spec's in-place calls

def soft_move(co, centre, radius, vector, falloff="smooth", mask=None):
    """Displace positions within radius of centre by vector times the falloff (spec 01 §4.2); in place."""
    co += move_field(co, centre, radius, vector, falloff, mask)
    return co


def soft_inflate(co, normals, centre, radius, amount, falloff="smooth", mask=None):
    """Push positions along their normals by amount times the falloff; in place."""
    co += amount * inflate_field(co, normals, centre, radius, falloff, mask)
    return co


def flatten_to_plane(co, weights, plane_z, blend=1.0):
    """Pull z toward plane_z by weight x blend (a weight of 1 at blend 1 lands on the plane); in place."""
    w = np.clip(np.asarray(weights, float) * blend, 0.0, 1.0)
    co[:, 2] += (plane_z - co[:, 2]) * w
    return co


def soft_rotate(co, pivot, axis, angle_deg, weights):
    """Rotate about an axis through pivot, each vertex by its weight's share of the motion; in place."""
    co += rotation_field(co, pivot, axis, angle_deg, weights)
    return co


# --------------------------------------------------------------------------- mesh helpers

def edges_from_polys(loop_start, loop_total, loop_vert):
    """The unique undirected edges (E, 2) of polygons given as loops."""
    loop_start, loop_total, loop_vert = (np.asarray(x, np.int64) for x in (loop_start, loop_total, loop_vert))
    nxt = np.arange(1, len(loop_vert) + 1)
    nxt[loop_start + loop_total - 1] = loop_start
    e = np.sort(np.stack([loop_vert, loop_vert[nxt]], axis=1), axis=1)
    return np.unique(e, axis=0)


def adjacency(n, edges):
    """Vertex neighbours as CSR (indptr, indices) from undirected edges."""
    e = np.asarray(edges, np.int64)
    a = np.concatenate([e[:, 0], e[:, 1]])
    b = np.concatenate([e[:, 1], e[:, 0]])
    order = np.argsort(a, kind="stable")
    a, b = a[order], b[order]
    indptr = np.zeros(n + 1, np.int64)
    np.add.at(indptr, a + 1, 1)
    return np.cumsum(indptr), b


def laplacian_smooth(co, adj, weights, iterations=1, factor=0.5):
    """Move each vertex toward the mean of its neighbours by factor x weight, `iterations` times (the numpy
    form of bmesh's smooth_vert restricted to a subset: weight 0 keeps a vertex); in place."""
    indptr, nb = adj
    counts = np.diff(indptr)
    w = np.asarray(weights, float) * factor
    rows = np.repeat(np.arange(len(counts)), counts)
    for _ in range(iterations):
        mean = np.zeros_like(co)
        for k in range(3):
            mean[:, k] = np.bincount(rows, co[nb, k], minlength=len(counts))
        has = counts > 0
        mean[has] /= counts[has, None]
        co[has] += (mean[has] - co[has]) * w[has, None]
    return co


def vertex_normals(co, loop_start, loop_total, loop_vert):
    """Area-weighted vertex normals of polygons (fan triangulation from each polygon's first corner)."""
    co = np.asarray(co, float)
    ls, lt, lv = (np.asarray(x, np.int64) for x in (loop_start, loop_total, loop_vert))
    n = np.zeros_like(co)
    first = lv[ls]
    face_n = np.zeros((len(ls), 3))
    for k in range(1, int(lt.max()) - 1):
        ok = lt > k + 1
        i0, i1, i2 = first[ok], lv[ls[ok] + k], lv[ls[ok] + k + 1]
        face_n[ok] += np.cross(co[i1] - co[i0], co[i2] - co[i0])
    corner_face = np.repeat(np.arange(len(ls)), lt)
    for k in range(3):
        n[:, k] = np.bincount(lv, face_n[corner_face, k], minlength=len(co))
    length = np.linalg.norm(n, axis=1)
    ok = length > 0
    n[ok] /= length[ok, None]
    return n


def topology(me):
    """(loop_start, loop_total, loop_vert) of a bpy Mesh, as int64 arrays."""
    P, L = len(me.polygons), len(me.loops)
    ls, lt, lv = np.empty(P, np.int32), np.empty(P, np.int32), np.empty(L, np.int32)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    me.loops.foreach_get("vertex_index", lv)
    return ls.astype(np.int64), lt.astype(np.int64), lv.astype(np.int64)


# --------------------------------------------------------------------------- shape keys

def key_coords(kb):
    a = np.empty(len(kb.data) * 3, np.float32)
    (kb.points if hasattr(kb, "points") else kb.data).foreach_get("co", a)
    return a.reshape(-1, 3).astype(np.float64)


def mix(ob, exclude=()):
    """Object-space positions of the relative shape-key mix, every vertex (helpers too), without the
    depsgraph: basis + sum of value x (key - its relative key) x its group weight, mute keys skipped.
    Keys named in `exclude` are left out (a part re-sculpting over its own old key)."""
    me = ob.data
    if me.shape_keys is None:
        a = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", a)
        return a.reshape(-1, 3).astype(np.float64)
    sk = me.shape_keys
    if not sk.use_relative:
        raise ValueError(f"{ob.name}: absolute shape keys are not supported")
    cache = {}

    def get(kb):
        if kb.name not in cache:
            cache[kb.name] = key_coords(kb)
        return cache[kb.name]

    out = get(sk.reference_key).copy()
    for kb in sk.key_blocks:
        if kb == sk.reference_key or kb.mute or kb.value == 0.0 or kb.name in exclude:
            continue
        d = get(kb) - get(kb.relative_key)
        if kb.vertex_group:
            d *= group_weights(ob, kb.vertex_group)[:, None]
        out += kb.value * d
    return out


def group_weights(ob, name):
    """Each vertex's weight in a vertex group (0 outside it)."""
    return group_weights_many(ob, [name])[name]


def group_weights_many(ob, names):
    """{name: weights} for several vertex groups in one pass over the vertices (Blender has no bulk read
    for weights; one pass for ninety groups costs what one group costs)."""
    n = len(ob.data.vertices)
    want = {ob.vertex_groups[nm].index: nm for nm in names if ob.vertex_groups.get(nm) is not None}
    out = {nm: np.zeros(n) for nm in names}
    arrays = {gi: out[nm] for gi, nm in want.items()}
    for v in ob.data.vertices:
        for g in v.groups:
            a = arrays.get(g.group)
            if a is not None:
                a[v.index] = g.weight
    return out


def key_from_positions(ob, name, positions, base=None, value=1.0):
    """A new shape key `name` (made from the basis, not the mix) whose offset from the basis is
    positions - base (base: the mix the positions were sculpted from); returns the key. An existing key
    of that name is replaced."""
    me = ob.data
    if me.shape_keys is None:
        ob.shape_key_add(name="Basis", from_mix=False)
    old = me.shape_keys.key_blocks.get(name)
    if old is not None:
        ob.shape_key_remove(old)
    basis = key_coords(me.shape_keys.reference_key)
    base = mix(ob) if base is None else np.asarray(base, float)
    kb = ob.shape_key_add(name=name, from_mix=False)
    co = (basis + (np.asarray(positions, float) - base)).astype(np.float32).ravel()
    (kb.points if hasattr(kb, "points") else kb.data).foreach_set("co", co)
    kb.slider_min, kb.slider_max = min(kb.slider_min, 0.0), max(kb.slider_max, 1.0)
    kb.value = value
    me.update()
    return kb


# --------------------------------------------------------------------------- self-test

def selftest():
    """The falloffs, linearity of the fields, smoothing and normals on a grid, and a key round trip on a
    scratch mesh: the key adds the sculpt on top of another key exactly."""
    import bpy
    R = {}
    t = np.linspace(0.0, 1.0, 11)
    for k in FALLOFFS:
        f = falloff(t, k)
        assert abs(f[0] - 1.0) < 1e-12 and f[-1] < 0.02 and np.all(np.diff(f) <= 1e-12), (k, f)
    assert abs(smoothstep(0.5, 0.0, 1.0) - 0.5) < 1e-12 and smoothstep(2.0, 1.0, 0.0) == 0.0
    # a 21 x 21 grid, 1 mm apart, in the z = 0 plane
    g = np.arange(21, dtype=float)
    X, Y = np.meshgrid(g, g)
    co = np.stack([X.ravel(), Y.ravel(), np.zeros(X.size)], axis=1)
    idx = np.arange(X.size).reshape(21, 21)
    quads = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    ls, lt, lv = np.arange(0, 4 * len(quads), 4), np.full(len(quads), 4), quads.ravel()
    nrm = vertex_normals(co, ls, lt, lv)
    assert np.allclose(nrm, [0.0, 0.0, 1.0]), "a flat grid's normals point up"
    c = (10.0, 10.0, 0.0)
    f1 = inflate_field(co, nrm, c, 5.0)
    assert np.allclose(2.5 * f1, soft_inflate(co.copy(), nrm, c, 5.0, 2.5) - co), "inflate is not linear"
    assert abs(f1[idx[10, 10], 2] - 1.0) < 1e-12 and f1[idx[10, 16], 2] == 0.0
    moved = soft_move(co.copy(), c, 5.0, (0.0, 0.0, 3.0))
    assert abs(moved[idx[10, 10], 2] - 3.0) < 1e-12
    sc = scale_field(co, (10.0, 10.0, 0.0), (1.0, 0.0, 0.0), np.ones(len(co)))
    assert np.allclose(sc[:, 0], co[:, 0] - 10.0)
    rot = soft_rotate(co.copy(), (10.0, 10.0, 0.0), (0.0, 0.0, 1.0), 90.0, np.ones(len(co)))
    assert np.allclose(rot[idx[10, 20]], (10.0, 20.0, 0.0)), rot[idx[10, 20]]
    w = line_weights(co, [(0.0, 10.0, 0.0), (20.0, 10.0, 0.0)], 3.0)
    assert w[idx[10, 5]] == 1.0 and w[idx[14, 5]] == 0.0
    adj = adjacency(len(co), edges_from_polys(ls, lt, lv))
    spike = co.copy()
    spike[idx[10, 10], 2] = 4.0
    laplacian_smooth(spike, adj, np.ones(len(co)), iterations=3, factor=0.5)
    assert 0.0 < spike[idx[10, 10], 2] < 4.0 and abs(spike[:, 2].sum() - 4.0) < 1.0
    flat = flatten_to_plane(co.copy() + [0, 0, 2.0], np.ones(len(co)), 0.0, blend=0.5)
    assert np.allclose(flat[:, 2], 1.0)
    # key round trip on a scratch object with another key active
    me = bpy.data.meshes.new("SelftestS.Grid")
    me.from_pydata(co.tolist(), [], quads.tolist())
    ob = bpy.data.objects.new("SelftestS.Grid", me)
    bpy.context.scene.collection.objects.link(ob)
    try:
        ob.shape_key_add(name="Basis", from_mix=False)
        other = ob.shape_key_add(name="other", from_mix=False)
        oc = key_coords(other)
        oc[:, 2] += 1.0
        other.data.foreach_set("co", oc.astype(np.float32).ravel())
        other.value = 0.5
        m0 = mix(ob)
        assert np.allclose(m0[:, 2], 0.5)
        sculpted = soft_move(m0.copy(), c, 5.0, (0.0, 0.0, 2.0))
        key_from_positions(ob, "SelftestS.Sculpt", sculpted, base=m0)
        assert np.allclose(mix(ob), sculpted, atol=1e-5), "the key does not add the sculpt on top of the mix"
        assert np.allclose(mix(ob, exclude=("SelftestS.Sculpt",)), m0, atol=1e-6)
        R["key_roundtrip_err"] = float(np.abs(mix(ob) - sculpted).max())
    finally:
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
    R["falloffs"] = list(FALLOFFS)
    return R
