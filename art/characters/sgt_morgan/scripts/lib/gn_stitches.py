"""Stitches, bar tacks and seam ridges (spec 09 §4.10 and §5.6, spec 02 §4.9, spec 11 §4.8, spec 13 §3.3 and
§4.4, spec 14 §4.8; it absorbs spec 11's planned stitch.py).

Millimetres and world space in the API, metres in Blender. Two layers:

* **Layout** (numpy, on sweep.py's surface paths): needle holes. A `Stitches` record holds one thread segment
  per stitch: the two holes it runs between (p0, p1, on the surface), the surface normal there and an extra
  sink per stitch. Paths come from control points (`seam_path`, sweep.surface_path) or from a mesh's boolean
  edge attribute (`seam_paths`: the flagged edges chained into open and closed polylines and laid on the
  surface); `offset_row()` moves a path across itself along the surface. `running()` lays a running stitch
  at a pitch (stitch + gap) with seeded imperfection: the row wanders sideways (low-frequency noise), each
  stitch turns a little about the normal (yaw), shifts sideways, varies its length, and a few sink deeper
  (spec 02 §4.15 item 4); the hole pitch itself stays regular, as a machine makes it. `rows()` is the same on
  rows offset across the path (double-needle rows), `zigzag()` legs alternating across a path (bindings,
  overlock), `bartack()` a satin zigzag over a short base (a leg every 0.3 mm by default, one pass),
  `box_x()` a box with both diagonals, `bartacks()` many tacks from frames. `Stitches.clear_of()` drops the
  stitches under a tack.
* **Geometry** (Geometry Nodes): `stitch_object()` writes the holes as a carrier mesh, one edge per stitch
  with the attributes `stitch_n` (normal) and `stitch_sink` (m), and puts the part's node group
  `<Part>.GN.Stitches` on it. The group builds one thread (a curve of `Rings` points across the edge, `Sides`
  around, radius `Radius`: its middle `Sink` into the surface, `Bow` higher than its ends, the last eighth
  diving `Dive` further so each stitch ends in its hole, the ends tapered to `Taper`), instances it on every
  edge (X along the edge, Z along the normal, scaled to the edge's length; `Flat` squashes its section for
  a satin), realises it with `UV.Real` (u
  along the stitch in metres, v round it) and its `Material` input (the realised thread is new geometry,
  so the carrier's own slot would not reach it), and drops everything when `LOD` is 1 or more
  (spec 09's switch; spec 13 keeps stitches and bar tacks in objects of their own so a game LOD drops them).
  Because the carrier is a plain mesh, a SurfaceDeform on it carries the stitches with the panel they sit on.
  `tack_object()` is stitch_object() with the bar-tack thread (flattened legs, barely bowed or diving).
* **Seam ridges**, two ways. `welt()` sweeps a lens-shaped ridge of its own along the seam (a parabola
  standing `height` over the surface, `width` wide where it meets it in a crease, tapering at the ends):
  independent of the panel's resolution, so it is the one for boots and gloves. `ridge()` puts `<Part>.GN.SeamRidge` on a panel: a guide mesh of the seam centre lines (edges, not
  rendered) and a displacement along the normal by the distance d to the nearest guide edge, height x
  smoothstep(half width -> 0, d) less a gaussian valley at the stitch rows (spec 09's 1.2 x smoothstep(4 -> 0)
  - 0.4 x gauss(d - 3.2, 0.4)). Put it after the Subdivision and lay the stitches on the evaluated panel
  with the ridge on, so they ride it; it needs vertices a few tenths of a mm apart across the ridge (on the
  materials test boot's 0.6 mm render mesh a 2.5 mm ridge came out as a sawtooth band), so it suits dense
  cloth rather than a boot upper.

Thread defaults are spec 02's (Tex 70: r 0.20, 6 sides, sunk 0.10 at the middle, bowed 0.15, pitch 3.4 =
2.6 + 0.8); spec 09 uses r 0.165, sink 0.15, pitch 3.6; spec 13 r 0.15-0.30, pitch 3.6, bar tacks 3 x 22 at
1.05. The thread's material is the caller's through lib/materials.py (`Thread.Bonded.Black`).

`--lod bump` (spec 09 §5.6): LOD 1 drops the thread geometry; `seam_fields()` writes the shader's inputs on
the panel (`stitch_d`, signed distance across the nearest row, and `stitch_s`, arc length along it, in mm,
as point attributes that interpolate through a Subdivision), and `bump_group()` is the shader group that
turns them into a dashed thread height and mask at the same gauge and pitch. The library's recipes do not
read it yet (spec 16 has no stitch layer): wiring it into a recipe is spec 16's.
"""
import math

import numpy as np

from . import sweep

MM = 0.001
GROUP_VERSION = 5
RIDGE_VERSION = 1
BUMP_GROUP = "Lib.Stitch.Bump"
BUMP_VERSION = 1


# --------------------------------------------------------------------------- the layout record

class Stitches:
    """Thread segments in world mm: p0, p1 (N, 3) the holes, n (N, 3) the surface normal, sink (N,) extra
    sink (mm; negative lifts, as the return pass of a bar tack rides on the first)."""

    def __init__(self, p0=None, p1=None, n=None, sink=None):
        self.p0 = np.zeros((0, 3)) if p0 is None else np.asarray(p0, float).reshape(-1, 3)
        self.p1 = np.zeros((0, 3)) if p1 is None else np.asarray(p1, float).reshape(-1, 3)
        k = len(self.p0)
        self.n = np.tile([0.0, 0.0, 1.0], (k, 1)) if n is None else sweep._unit(np.asarray(n, float).reshape(-1, 3))
        self.sink = np.zeros(k) if sink is None else np.broadcast_to(np.asarray(sink, float), (k,)).copy()
        if not (len(self.p1) == len(self.n) == len(self.sink) == k):
            raise ValueError("p0, p1, n and sink need one row per stitch")

    def __len__(self):
        return len(self.p0)

    def __add__(self, other):
        return Stitches.join([self, other])

    @staticmethod
    def join(parts):
        parts = [p for p in parts if p is not None and len(p)]
        if not parts:
            return Stitches()
        return Stitches(np.vstack([p.p0 for p in parts]), np.vstack([p.p1 for p in parts]),
                        np.vstack([p.n for p in parts]), np.concatenate([p.sink for p in parts]))

    def select(self, mask):
        """The stitches where mask is true (e.g. those clear of a bar tack)."""
        m = np.asarray(mask, bool)
        return Stitches(self.p0[m], self.p1[m], self.n[m], self.sink[m])

    def clear_of(self, centre, radius):
        """The stitches whose middles lie farther than `radius` mm from `centre`."""
        return self.select(np.linalg.norm(self.mid() - np.asarray(centre, float), axis=1) > radius)

    def lengths(self):
        return np.linalg.norm(self.p1 - self.p0, axis=1)

    def mid(self):
        return 0.5 * (self.p0 + self.p1)

    def directions(self):
        return sweep._unit(self.p1 - self.p0)

    def thread_mm(self):
        """Visible thread in all (mm)."""
        return float(self.lengths().sum())


# --------------------------------------------------------------------------- paths

def _surf(target):
    return target if isinstance(target, sweep.Surface) else sweep.Surface(target)


def _seed(seed):
    """Any integer as a non-negative seed (numpy refuses negative ones; a part may seed by an angle)."""
    return int(seed) % 2147483647


def seam_path(target, points, *, closed=False, step=1.0, standoff=0.0, max_dist=None):
    """A seam line through control points (mm, world) laid on the target's surface (sweep.surface_path):
    a Path of points every ~step mm with the smooth surface normals."""
    return sweep.surface_path(_surf(target), points, standoff, step, closed=closed, max_dist=max_dist)


def _chains(edges):
    """Edges (E, 2) chained into polylines: [(vertex indices, closed)], split at branch vertices."""
    adj = {}
    for a, b in edges:
        adj.setdefault(int(a), []).append(int(b))
        adj.setdefault(int(b), []).append(int(a))
    used, out = set(), []

    def key(a, b):
        return (a, b) if a < b else (b, a)

    def walk(v0, v1):
        chain, prev, cur = [v0, v1], v0, v1
        used.add(key(v0, v1))
        while len(adj[cur]) == 2:
            nxt = adj[cur][0] if adj[cur][1] == prev else adj[cur][1]
            if key(cur, nxt) in used:
                break
            used.add(key(cur, nxt))
            chain.append(nxt)
            prev, cur = cur, nxt
        return chain

    for v in sorted(adj):   # open chains start at ends and branch points
        if len(adj[v]) != 2:
            for w in adj[v]:
                if key(v, w) not in used:
                    out.append((walk(v, w), False))
    for v in sorted(adj):   # what is left are loops
        for w in adj[v]:
            if key(v, w) not in used:
                c = walk(v, w)
                closed = c[-1] == c[0]
                out.append((c[:-1] if closed else c, closed))
    return out


def seam_paths(ob, attribute="seam", target=None, *, step=1.0, smooth=True, min_mm=2.0):
    """The paths of a mesh's boolean edge attribute (spec 09: the `seam` edges): its flagged edges chained
    into open and closed polylines (split where three or more meet), in world mm, each laid on the target's
    surface (default the object itself, evaluated) by sweep.surface_path, smoothed through the base mesh's
    vertices so the line follows a subdivided surface. Returns [Path]."""
    me = ob.data
    att = me.attributes.get(attribute)
    if att is None or att.domain != "EDGE":
        raise KeyError(f"{ob.name} has no edge attribute {attribute!r}")
    flag = np.zeros(len(me.edges), bool)
    att.data.foreach_get("value", flag)
    ev = np.empty(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", ev)
    ev = ev.reshape(-1, 2)[flag]
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    M = np.array(ob.matrix_world, float)
    co = (co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]) / MM
    surf = _surf(target if target is not None else ob)
    out = []
    for idx, closed in _chains(ev):
        pts = co[idx]
        if len(pts) < 2 or (not closed and np.linalg.norm(np.diff(pts, axis=0), axis=1).sum() < min_mm):
            continue
        out.append(sweep.surface_path(surf, pts, 0.0, step, closed=closed, smooth=smooth))
    return out


def offset_row(path, offset, target=None, *, step=None):
    """The path moved `offset` mm across itself along the surface (+ toward B = T x N, to the right of the
    direction of travel seen from outside), laid back on the surface. Returns a Path."""
    if not offset:
        return path
    surf = _surf(target if target is not None else path.surface)
    T, N, B = sweep.rmf_frames(path)
    step = step or float(np.median(np.linalg.norm(np.diff(path.co, axis=0), axis=1)))
    pts = path.co - N * path.standoff + B * float(offset)
    return sweep.surface_path(surf, pts, 0.0, step, closed=path.closed, path_sigma=max(step, 1.0))


class _Sampler:
    """Points, normals and across-vectors of a path at arc lengths (wrapped when closed)."""

    def __init__(self, path):
        P = path
        T, N, B = sweep.rmf_frames(P)
        co, s = P.co - P.normal * P.standoff, P.s
        self.closed, self.L = P.closed, P.length
        if P.closed:
            co, N, B = np.vstack([co, co[:1]]), np.vstack([N, N[:1]]), np.vstack([B, B[:1]])
            s = np.concatenate([s, [self.L]])
        self.co, self.N, self.B, self.s = co, N, B, s

    def __call__(self, t):
        t = np.asarray(t, float)
        t = np.mod(t, self.L) if self.closed else np.clip(t, 0.0, self.s[-1])
        f = lambda A: np.stack([np.interp(t, self.s, A[:, k]) for k in range(3)], -1)
        n = sweep._unit(f(self.N))
        b = f(self.B)
        b = sweep._unit(b - np.sum(b * n, -1, keepdims=True) * n)
        return f(self.co), n, b


def _rotate(v, axis, ang):
    """Rodrigues: rotate vectors v (K, 3) about unit axes (K, 3) by angles (K,) radians."""
    c, s = np.cos(ang)[:, None], np.sin(ang)[:, None]
    return v * c + np.cross(axis, v) * s + axis * np.sum(axis * v, 1, keepdims=True) * (1 - c)


def _segments(pa, na, ba, pb, nb, rng, yaw_deg, offset, deep_share, deep_mm):
    """Stitches from hole pairs with per-stitch yaw about the normal and a sideways shift; a share sunk deeper."""
    k = len(pa)
    n = sweep._unit(na + nb)
    mid = 0.5 * (pa + pb)
    yaw = np.radians(yaw_deg) * rng.uniform(-1.0, 1.0, k)
    half = _rotate(0.5 * (pb - pa), n, yaw)
    mid = mid + ba * (offset * rng.uniform(-1.0, 1.0, k))[:, None]
    sink = np.where(rng.random(k) < deep_share, deep_mm * rng.uniform(0.5, 1.0, k), 0.0)
    return Stitches(mid - half, mid + half, n, sink)


def running(path, pitch=3.4, gap=0.8, *, seed=0, start=None, margin=None, yaw_deg=3.0, offset=0.06,
            wander=0.3, wander_mm=45.0, length_jitter=0.03, deep_share=0.06, deep_mm=0.08, sink=0.0):
    """A running stitch along a path: holes every `pitch` mm, each stitch `pitch - gap` long between them.
    An open path's stitches are centred on it with `margin` mm free at the ends (default half a gap), or
    start `start` mm from its start; a closed path takes a whole number of pitches round. Imperfection
    (seeded): the row wanders sideways by up to `wander` mm (noise over `wander_mm`), each stitch turns up
    to `yaw_deg` about the normal, shifts up to `offset` across and varies its length by `length_jitter`,
    and `deep_share` of the stitches sink `deep_mm` deeper (spec 02 §4.15). `sink` adds to every stitch.
    Returns Stitches."""
    rng = np.random.default_rng(_seed(seed) * 7919 + 101)
    S = _Sampler(path)
    L = S.L
    run = pitch - gap
    if path.closed:
        k = max(int(round(L / pitch)), 3)
        p = L / k
        a = (0.0 if start is None else float(start)) + p * np.arange(k)
        run = p - gap
    else:
        m = 0.5 * gap if margin is None else float(margin)
        if start is not None:
            k = int(math.floor((L - float(start) - m + gap) / pitch))
            a0 = float(start)
        else:
            k = int(math.floor((L - 2 * m + gap) / pitch))
            a0 = 0.5 * (L - (k * pitch - gap))
        if k < 1:
            return Stitches()
        a = a0 + pitch * np.arange(k)
    b = a + run * (1.0 + length_jitter * rng.uniform(-1.0, 1.0, len(a)))
    pa, na, ba = S(a)
    pb, nb, bb = S(b)
    if wander:
        per = L if path.closed else None
        wa = wander * sweep.noise(a, _seed(seed) + 31, wander_mm, per)
        wb = wander * sweep.noise(np.mod(b, L) if path.closed else b, _seed(seed) + 31, wander_mm, per)
        pa, pb = pa + ba * wa[:, None], pb + bb * wb[:, None]
    st = _segments(pa, na, ba, pb, nb, rng, yaw_deg, offset, deep_share, deep_mm)
    st.sink += sink
    return st


def rows(path, offsets, pitch=3.4, gap=0.8, *, target=None, seed=0, stagger=True, **kw):
    """Running stitches on rows offset across the path along the surface (offsets in mm, + to the right):
    spec 09's double-needle rows (-3.2, +3.2), spec 02's rows at 1.5 and 5.5 from an edge. Each row takes
    its own seed; with `stagger` the rows' holes are offset by a fraction of a pitch, as two needles never
    sit exactly abreast after a curve. Returns Stitches."""
    out = []
    rng = np.random.default_rng(_seed(seed) + 7)
    for i, d in enumerate(offsets):
        row = offset_row(path, d, target)
        st = None if not stagger or path.closed else 0.5 * gap + rng.uniform(0.0, 0.35) * pitch
        out.append(running(row, pitch, gap, seed=_seed(seed) + 17 * (i + 1), start=st, **kw))
    return Stitches.join(out)


def zigzag(path, width, pitch, *, seed=0, gap=0.1, yaw_deg=2.0, offset=0.03, wander=0.15, phase=0.0,
           deep_share=0.0, deep_mm=0.0, sink=0.0):
    """A zigzag along a path: holes alternately `width`/2 either side of it, `pitch` mm apart per full V (two
    legs), each leg a stitch between consecutive holes shortened by `gap`. A collar binding's 2 mm zigzag,
    an overlock, or a bar tack's satin. phase: the first hole's offset along the path in pitches."""
    rng = np.random.default_rng(_seed(seed) * 7919 + 211)
    S = _Sampler(path)
    L = S.L
    half = 0.5 * pitch
    if path.closed:
        k = max(2 * int(round(L / pitch)), 4)
        t = phase * pitch + (L / k) * np.arange(k + 1)
    else:
        k = int(math.floor((L - 1e-9) / half))
        if k < 1:
            return Stitches()
        t = 0.5 * (L - k * half) + phase * pitch + half * np.arange(k + 1)
        t = t[t <= L + 1e-9]
    p, n, b = S(t)
    side = np.where(np.arange(len(t)) % 2 == 0, 1.0, -1.0)
    w = 0.5 * width * side
    if wander:
        w = w + wander * sweep.noise(t, _seed(seed) + 47, 30.0, L if path.closed else None)
    h = p + b * w[:, None]
    pa, pb = h[:-1], h[1:]
    d = sweep._unit(pb - pa)
    pa, pb = pa + d * (0.5 * gap), pb - d * (0.5 * gap)
    st = _segments(pa, n[:-1], b[:-1], pb, n[1:], rng, yaw_deg, offset, deep_share, deep_mm)
    st.sink += sink
    return st


def _straight(target, centre, along, length, step=0.25):
    """A straight path of `length` mm through the centre along `along` (projected on the tangent plane)."""
    surf = _surf(target)
    q, n, _, _ = surf.nearest(np.asarray(centre, float))
    a = np.asarray(along, float)
    a = sweep._unit(a - (a @ n) * n)
    return sweep.surface_path(surf, [q - a * length / 2, q + a * length / 2], 0.0, step, smooth=False,
                              path_sigma=0.5), surf


def bartack(target, centre, along, length=10.0, width=2.5, pitch=0.6, *, passes=1, seed=0, lift=0.12):
    """A bar tack: a satin zigzag `width` mm across over a straight base `length` mm long along `along` (a
    world direction, projected on the surface at the centre), a full V every `pitch` mm, so the legs lie
    pitch/2 apart nearly parallel. passes 2 adds a return pass a quarter pitch out of phase, `lift` mm
    higher; it crosses the first at twice the legs' slant, which read as a coiled spring on the test boot,
    so one pass is the default. The default pitch 0.6 lays a leg every 0.3 mm, overlapping a Ø 0.4
    thread a little: a satin block, as real tacks are (28-42 stitches in 10-16 mm; spec 09's 28 in 10 is
    0.36 a stitch). Spec 02's 1.3 (E) left gaps between the legs and read as a zigzag; spec 13: 3 x 22 at
    1.05 (42 legs);
    spec 09: 10 x 2.5. Render them with tack_object(). Returns Stitches."""
    base, _ = _straight(target, centre, along, length)
    out = [zigzag(base, width, pitch, seed=seed, gap=0.05, wander=0.04, offset=0.02, yaw_deg=1.0)]
    if passes > 1:
        out.append(zigzag(base.reversed(), width * 0.96, pitch, seed=_seed(seed) + 1, gap=0.05, wander=0.04,
                          offset=0.02, yaw_deg=1.0, phase=0.25, sink=-lift))
    return Stitches.join(out)


def bartacks(target, frames, length=10.0, width=2.5, pitch=0.6, *, seed=0, **kw):
    """Bar tacks at frames [(centre, along)] on one target (PALS columns, strap ends). Returns Stitches."""
    surf = _surf(target)
    return Stitches.join([bartack(surf, c, a, length, width, pitch, seed=_seed(seed) + 13 * i, **kw)
                          for i, (c, a) in enumerate(frames)])


def box_x(target, centre, along, size=(15.0, 10.0), pitch=2.5, gap=0.5, *, seed=0, **kw):
    """A box stitch with both diagonals (strap keepers, hanger ends): a `size` = (along, across) mm
    rectangle centred on the surface point nearest `centre`, its first side along `along`, each side and
    diagonal a running stitch laid on the surface. Returns Stitches."""
    surf = _surf(target)
    q, n, _, _ = surf.nearest(np.asarray(centre, float))
    a = np.asarray(along, float)
    a = sweep._unit(a - (a @ n) * n)
    b = np.cross(n, a)
    u, v = size[0] / 2.0, size[1] / 2.0
    c = [q - a * u - b * v, q + a * u - b * v, q + a * u + b * v, q - a * u + b * v]
    out = []
    for i, (p0, p1) in enumerate([(c[0], c[1]), (c[1], c[2]), (c[2], c[3]), (c[3], c[0]), (c[0], c[2]),
                                  (c[1], c[3])]):
        line = sweep.surface_path(surf, [p0, p1], 0.0, 0.25, smooth=False, path_sigma=0.5)
        out.append(running(line, pitch, gap, seed=_seed(seed) + 5 * i, margin=0.15, wander=0.05, yaw_deg=1.5,
                           sink=0.02 * i, **kw))
    return Stitches.join(out)


def stitch_along(source, pitch=3.4, gap=0.8, *, target=None, offsets=(0.0,), seed=0, **kw):
    """Spec 11's stitch_along(curve_or_vgroup, pitch, gap, ...): running rows along a Path, control points
    (with target), or (object, edge attribute name). Radius and sink belong to stitch_object()."""
    if isinstance(source, sweep.Path):
        paths = [source]
    elif isinstance(source, tuple) and len(source) == 2 and isinstance(source[1], str):
        paths = seam_paths(source[0], source[1], target)
    else:
        paths = [seam_path(target, source)]
    return Stitches.join([rows(p, offsets, pitch, gap, target=target, seed=_seed(seed) + 101 * i, **kw)
                          for i, p in enumerate(paths)])


# --------------------------------------------------------------------------- node trees

class _Tree:
    """A small builder for node trees: nodes with properties, links from sockets or constants."""

    def __init__(self, ng):
        self.ng, self.x = ng, 0

    def node(self, kind, inputs=None, **props):
        nd = self.ng.nodes.new(kind)
        for k, v in props.items():
            setattr(nd, k, v)
        nd.location = (self.x, 0)
        self.x += 180
        for k, v in (inputs or {}).items():
            self.put(nd.inputs[k] if isinstance(k, (int, str)) else k, v)
        return nd

    def put(self, sock, v):
        if v is None:
            return
        if hasattr(v, "is_output") or (hasattr(v, "links") and hasattr(v, "node")):
            self.ng.links.new(v, sock)
        else:
            sock.default_value = v

    def math(self, op, a, b=None, c=None):
        nd = self.node("ShaderNodeMath", operation=op)
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self.put(nd.inputs[i], v)
        return nd.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        nd = self.node("ShaderNodeVectorMath", operation=op)
        self.put(nd.inputs[0], a)
        if b is not None:
            self.put(nd.inputs[1], b)
        if scale is not None:
            self.put(nd.inputs["Scale"], scale)
        return nd.outputs["Value" if op in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else "Vector"]

    def xyz(self, x=0.0, y=0.0, z=0.0):
        return self.node("ShaderNodeCombineXYZ", {"X": x, "Y": y, "Z": z}).outputs[0]

    def named(self, name, data_type="FLOAT"):
        return self.node("GeometryNodeInputNamedAttribute", {"Name": name}, data_type=data_type).outputs["Attribute"]

    def store(self, geo, name, value, data_type="FLOAT", domain="POINT"):
        return self.node("GeometryNodeStoreNamedAttribute", {"Geometry": geo, "Name": name, "Value": value},
                         data_type=data_type, domain=domain).outputs[0]


def _interface(ng, sockets):
    it = ng.interface
    for name, io, kind, default, lo, hi in sockets:
        s = it.new_socket(name, in_out=io, socket_type=kind)
        if default is not None:
            s.default_value = default
        if lo is not None:
            s.min_value = lo
        if hi is not None:
            s.max_value = hi
    return {s.name: s.identifier for s in it.items_tree if getattr(s, "in_out", None) == "INPUT"}


def _fresh_group(name, version, kind="GeometryNodeTree"):
    import bpy
    ng = bpy.data.node_groups.get(name)
    if ng is not None and ng.get("version") == version and ng.library is None:
        return ng, False
    if ng is None:
        ng = bpy.data.node_groups.new(name, kind)
    else:   # rebuilt in place, so the modifiers that use it keep it
        ng.nodes.clear()
        ng.interface.clear()
    ng["version"] = version
    return ng, True


STITCH_INPUTS = [("Geometry", "INPUT", "NodeSocketGeometry", None, None, None),
                 ("Radius", "INPUT", "NodeSocketFloat", 0.0002, 0.0, None),
                 ("Sides", "INPUT", "NodeSocketInt", 6, 3, 32),
                 ("Rings", "INPUT", "NodeSocketInt", 7, 3, 33),
                 ("Sink", "INPUT", "NodeSocketFloat", 0.0001, None, None),
                 ("Bow", "INPUT", "NodeSocketFloat", 0.00015, None, None),
                 ("Dive", "INPUT", "NodeSocketFloat", 0.0002, None, None),
                 ("Taper", "INPUT", "NodeSocketFloat", 0.7, 0.05, 1.0),
                 ("Flat", "INPUT", "NodeSocketFloat", 1.0, 0.2, 1.0),
                 ("LOD", "INPUT", "NodeSocketInt", 0, 0, 9),
                 ("Material", "INPUT", "NodeSocketMaterial", None, None, None),
                 ("Geometry", "OUTPUT", "NodeSocketGeometry", None, None, None)]


def stitch_group(part):
    """`<Part>.GN.Stitches` (built once per part, rebuilt in place when GROUP_VERSION changes): the thread
    instanced on every edge of a carrier mesh (see the module docstring). Inputs in metres."""
    ng, fresh = _fresh_group(f"{part}.GN.Stitches", GROUP_VERSION)
    if not fresh:
        return ng
    ng.is_modifier = True
    _interface(ng, STITCH_INPUTS)
    t = _Tree(ng)
    gi = t.node("NodeGroupInput")
    R, sides, rings = gi.outputs["Radius"], gi.outputs["Sides"], gi.outputs["Rings"]
    # the unit thread along X from -0.5 to 0.5, a straight tube first (radius tapering to the ends), then
    # flattened by Flat (a thread under tension in a satin spreads) and bent: its middle Radius x Flat - Sink
    # over the surface, its ends Bow lower, the last eighth diving Dive more
    # (a = |2x|; drop = Bow a^2 + Dive max(0, (a - 0.75) / 0.25)^2)
    line = t.node("GeometryNodeCurvePrimitiveLine", {"Start": (-0.5, 0.0, 0.0), "End": (0.5, 0.0, 0.0)})
    line = t.node("GeometryNodeResampleCurve", {"Curve": line.outputs[0], "Count": rings}, mode="COUNT")
    x = t.node("ShaderNodeSeparateXYZ", {0: t.node("GeometryNodeInputPosition").outputs[0]}).outputs["X"]
    a = t.math("ABSOLUTE", t.math("MULTIPLY", x, 2.0))
    ends = t.math("MAXIMUM", t.math("DIVIDE", t.math("SUBTRACT", a, 0.6), 0.4), 0.0)
    rad = t.math("SUBTRACT", 1.0, t.math("MULTIPLY", t.math("SUBTRACT", 1.0, gi.outputs["Taper"]),
                                         t.math("MULTIPLY", ends, ends)))
    line = t.node("GeometryNodeSetCurveRadius", {"Curve": line.outputs[0], "Radius": rad})
    fac = t.node("GeometryNodeSplineParameter").outputs["Factor"]
    line = t.store(line.outputs[0], "lib_u", fac)
    prof = t.node("GeometryNodeCurvePrimitiveCircle", {"Resolution": sides, "Radius": R}, mode="RADIUS")
    prof = t.store(prof.outputs["Curve"], "lib_v", t.node("GeometryNodeSplineParameter").outputs["Factor"])
    unit = t.node("GeometryNodeCurveToMesh", {"Curve": line, "Profile Curve": prof, "Fill Caps": True})
    unit = t.node("GeometryNodeTransform", {"Geometry": unit.outputs[0], "Scale": t.xyz(1.0, 1.0, gi.outputs["Flat"])})
    xm = t.node("ShaderNodeSeparateXYZ", {0: t.node("GeometryNodeInputPosition").outputs[0]}).outputs["X"]
    am = t.math("ABSOLUTE", t.math("MULTIPLY", xm, 2.0))
    tail = t.math("MAXIMUM", t.math("DIVIDE", t.math("SUBTRACT", am, 0.75), 0.25), 0.0)
    drop = t.math("ADD", t.math("MULTIPLY", gi.outputs["Bow"], t.math("MULTIPLY", am, am)),
                  t.math("MULTIPLY", gi.outputs["Dive"], t.math("MULTIPLY", tail, tail)))
    z = t.math("SUBTRACT", t.math("SUBTRACT", t.math("MULTIPLY", R, gi.outputs["Flat"]), gi.outputs["Sink"]), drop)
    unit = t.node("GeometryNodeSetPosition", {"Geometry": unit.outputs[0], "Offset": t.xyz(z=z)})
    unit = t.node("GeometryNodeSetShadeSmooth", {"Geometry": unit.outputs[0], "Shade Smooth": True})
    # the carrier: per edge its direction (stored before the edges become points), normal and sink
    ev = t.node("GeometryNodeInputMeshEdgeVertices")
    d = t.vmath("SUBTRACT", ev.outputs["Position 2"], ev.outputs["Position 1"])
    car = t.store(gi.outputs["Geometry"], "lib_d", d, "FLOAT_VECTOR", "EDGE")
    pts = t.node("GeometryNodeMeshToPoints", {"Mesh": car}, mode="EDGES").outputs[0]
    dvec, nrm = t.named("lib_d", "FLOAT_VECTOR"), t.named("stitch_n", "FLOAT_VECTOR")
    pts = t.node("GeometryNodeSetPosition", {"Geometry": pts, "Offset": t.vmath(
        "SCALE", nrm, scale=t.math("MULTIPLY", t.named("stitch_sink"), -1.0))}).outputs[0]
    length = t.vmath("LENGTH", dvec)
    pts = t.store(pts, "lib_len", length)
    rot = t.node("FunctionNodeAxesToRotation", {"Primary Axis": dvec, "Secondary Axis": nrm},
                 primary_axis="X", secondary_axis="Z").outputs[0]
    inst = t.node("GeometryNodeInstanceOnPoints", {"Points": pts, "Instance": unit.outputs[0], "Rotation": rot,
                                                   "Scale": t.xyz(length, 1.0, 1.0)})
    geo = t.node("GeometryNodeRealizeInstances", {"Geometry": inst.outputs[0]}).outputs[0]
    circ = t.math("MULTIPLY", R, 2.0 * math.pi)
    uv = t.xyz(t.math("MULTIPLY", t.named("lib_u"), t.named("lib_len")), t.math("MULTIPLY", t.named("lib_v"), circ))
    geo = t.store(geo, "UV.Real", uv, "FLOAT2", "CORNER")
    geo = t.node("GeometryNodeRemoveAttribute", {"Geometry": geo, "Name": "lib_*"}, pattern_mode="WILDCARD").outputs[0]
    for nm in ("stitch_n", "stitch_sink"):
        geo = t.node("GeometryNodeRemoveAttribute", {"Geometry": geo, "Name": nm}).outputs[0]
    # the realised thread is new geometry with no material list of its own: set the material on it (the
    # carrier's slot alone would not reach the evaluated mesh)
    geo = t.node("GeometryNodeSetMaterial", {"Geometry": geo, "Material": gi.outputs["Material"]}).outputs[0]
    drop_all = t.node("FunctionNodeCompare", {2: gi.outputs["LOD"], 3: 1}, data_type="INT",
                      operation="GREATER_EQUAL").outputs[0]
    sw = t.node("GeometryNodeSwitch", {"Switch": drop_all, "False": geo}, input_type="GEOMETRY")
    go = t.node("NodeGroupOutput")
    ng.links.new(sw.outputs[0], go.inputs[0])
    return ng


RIDGE_INPUTS = [("Geometry", "INPUT", "NodeSocketGeometry", None, None, None),
                ("Guides", "INPUT", "NodeSocketObject", None, None, None),
                ("Height", "INPUT", "NodeSocketFloat", 0.0008, None, None),
                ("Half Width", "INPUT", "NodeSocketFloat", 0.00125, 0.0, None),
                ("Valley Depth", "INPUT", "NodeSocketFloat", 0.0, None, None),
                ("Valley Offset", "INPUT", "NodeSocketFloat", 0.0032, 0.0, None),
                ("Valley Sigma", "INPUT", "NodeSocketFloat", 0.0004, 1e-6, None),
                ("Geometry", "OUTPUT", "NodeSocketGeometry", None, None, None)]


def ridge_group(part):
    """`<Part>.GN.SeamRidge`: the panel displaced along its normals by the seam profile of the distance to
    the nearest edge of the Guides object (see the module docstring). Inputs in metres."""
    ng, fresh = _fresh_group(f"{part}.GN.SeamRidge", RIDGE_VERSION)
    if not fresh:
        return ng
    ng.is_modifier = True
    _interface(ng, RIDGE_INPUTS)
    t = _Tree(ng)
    gi = t.node("NodeGroupInput")
    info = t.node("GeometryNodeObjectInfo", {"Object": gi.outputs["Guides"]}, transform_space="RELATIVE")
    prox = t.node("GeometryNodeProximity", {"Geometry": info.outputs["Geometry"],
                                            "Sample Position": t.node("GeometryNodeInputPosition").outputs[0]},
                  target_element="EDGES")
    d = prox.outputs["Distance"]
    h = t.node("ShaderNodeMapRange", {"Value": d, "From Min": 0.0, "From Max": gi.outputs["Half Width"],
                                      "To Min": gi.outputs["Height"], "To Max": 0.0},
               interpolation_type="SMOOTHSTEP", clamp=True).outputs["Result"]
    q = t.math("DIVIDE", t.math("SUBTRACT", d, gi.outputs["Valley Offset"]), gi.outputs["Valley Sigma"])
    valley = t.math("MULTIPLY", gi.outputs["Valley Depth"], t.math("EXPONENT", t.math("MULTIPLY", t.math(
        "MULTIPLY", q, q), -0.5)))
    off = t.math("MULTIPLY", t.math("SUBTRACT", h, valley), prox.outputs["Is Valid"])
    nrm = t.node("GeometryNodeInputNormal").outputs["Normal"]
    sp = t.node("GeometryNodeSetPosition", {"Geometry": gi.outputs["Geometry"], "Offset": t.vmath("SCALE", nrm, scale=off)})
    go = t.node("NodeGroupOutput")
    ng.links.new(sp.outputs[0], go.inputs[0])
    return ng


def _inputs(ng):
    return {s.name: s.identifier for s in ng.interface.items_tree if getattr(s, "in_out", None) == "INPUT"}


def _set_inputs(mod, values):
    ids = _inputs(mod.node_group)
    for k, v in values.items():
        if k not in ids:
            raise KeyError(f"{mod.node_group.name} has no input {k!r}")
        mod[ids[k]] = v
    mod.id_data.update_tag()


# --------------------------------------------------------------------------- objects

def _link(name, data, scope, coll):
    import bpy
    if scope is not None:
        return scope.new_object(name, data, coll)
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old)
    ob = bpy.data.objects.new(name, data)
    if data is not None and data.users == 1:
        data.name = name
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def carrier_mesh(name, stitches):
    """The carrier mesh (metres): an edge per stitch, attributes stitch_n and stitch_sink (m)."""
    import bpy
    k = len(stitches)
    v = np.empty((2 * k, 3))
    v[0::2], v[1::2] = stitches.p0 * MM, stitches.p1 * MM
    me = bpy.data.meshes.new(name)
    me.vertices.add(2 * k)
    me.vertices.foreach_set("co", v.astype(np.float32).ravel())
    me.edges.add(k)
    me.edges.foreach_set("vertices", np.arange(2 * k, dtype=np.int32))
    n = np.repeat(stitches.n, 2, axis=0)
    a = me.attributes.new("stitch_n", "FLOAT_VECTOR", "POINT")
    a.data.foreach_set("vector", n.astype(np.float32).ravel())
    s = me.attributes.new("stitch_sink", "FLOAT", "POINT")
    s.data.foreach_set("value", (np.repeat(stitches.sink, 2) * MM).astype(np.float32))
    me.update()
    return me


def stitch_object(name, stitches, *, part, radius=0.2, sides=6, rings=7, sink=0.1, bow=0.15, dive=None,
                  taper=0.7, flat=1.0, lod=0, material="Thread.Bonded.Black", scope=None, coll=None, **overrides):
    """The stitches as an object: the carrier mesh with `<part>.GN.Stitches` (mm here, metres on the
    modifier). dive (default: enough that each end's top meets the surface) is the extra drop of the last
    eighth into the hole; flat squashes the thread's section along the normal (a satin's flattened legs). material: a catalogue ID put on slot 0 through lib/materials.py (None: none).
    scope: replace.part_scope's Scope (else linked to coll, the scene's collection by default)."""
    if dive is None:
        dive = max(0.0, (radius * flat - sink) - bow + taper * radius * flat)
    me = carrier_mesh(name, stitches)
    ob = _link(name, me, scope, coll)
    mod = ob.modifiers.new("Stitches", "NODES")
    mod.node_group = stitch_group(part)
    _set_inputs(mod, {"Radius": radius * MM, "Sides": int(sides), "Rings": int(rings), "Sink": sink * MM,
                      "Bow": bow * MM, "Dive": dive * MM, "Taper": float(taper), "Flat": float(flat),
                      "LOD": int(lod)})
    if material:
        from . import materials
        mat = materials.assign(ob, material, part=part, **overrides)
        _set_inputs(mod, {"Material": mat})
    ob["stitches"] = len(stitches)
    ob["thread_mm"] = round(stitches.thread_mm(), 1)
    return ob


TACK = {"sink": 0.05, "bow": 0.03, "dive": 0.05, "taper": 0.9, "flat": 0.55}   # satin legs: flat, barely diving


def tack_object(name, stitches, *, part, radius=0.2, **kw):
    """stitch_object() with the bar-tack thread: legs flattened to 0.55 of their round section and lying
    side by side, their ends only just diving (round, bowed and diving like a running stitch's, the legs of
    a tack read as the coils of a spring)."""
    return stitch_object(name, stitches, part=part, radius=radius, **{**TACK, **kw})


# --------------------------------------------------------------------------- seam welts

class Welt(sweep.Sweep):
    """A seam welt: a lens-shaped ridge swept along a path on the surface (see welt())."""

    smooth = True

    def __init__(self, path, width=2.5, height=0.8, sink=0.3, taper=4.0, across=8, offset=0.0, seed=0,
                 wobble=0.08):
        super().__init__()
        self.path, self.width, self.height, self.sink = path, float(width), float(height), float(sink)
        self.taper, self.across, self.offset, self.seed, self.wobble = float(taper), int(across), float(offset), seed, float(wobble)

    def _build(self):
        P = self.path
        T, N, B = sweep.rmf_frames(P)
        base = P.co - P.normal * P.standoff
        s, L = P.s, P.length
        per = L if P.closed else None
        f = np.ones(len(s)) if P.closed or not self.taper else \
            np.maximum(sweep._smoothstep(s, 0.0, self.taper) * sweep._smoothstep(L - s, 0.0, self.taper), 0.04)
        # the height varies a little along the seam (the leather's pull), seeded
        h = self.height * (1.0 + self.wobble * sweep.noise(s, _seed(self.seed) + 61, 18.0, per))
        # the section: a parabola standing h over the surface where it is `width` wide, carried on to -sink
        # beyond (half-width a), a flat bottom a little lower: it meets the panel in a crease. The taper
        # scales the whole section (heights by f, the width by 0.12 + 0.88 f), so the ends fade to a point.
        n = self.across
        x = np.linspace(-1.0, 1.0, n + 1)
        a = 0.5 * self.width * math.sqrt((self.height + self.sink) / self.height)
        top_z = f[:, None] * ((h[:, None] + self.sink) * (1.0 - x[None, :] ** 2) - self.sink)
        X = x[None, :] * (a * (0.12 + 0.88 * f))[:, None]
        c = base + B * self.offset
        top = c[:, None, :] + X[..., None] * B[:, None, :] + top_z[..., None] * N[:, None, :]
        bot = (c[:, None, :] + X[:, ::-1, None] * B[:, None, :] - (f * (self.sink + 0.15))[:, None, None] * N[:, None, :])
        rings = np.concatenate([top, bot], axis=1)
        K = 2 * (n + 1)
        seg = np.linalg.norm(np.diff(np.vstack([rings[len(rings) // 2], rings[len(rings) // 2][:1]]), axis=0), axis=1)
        perim = np.concatenate([[0.0], np.cumsum(seg)])
        caps = []
        if not P.closed:
            cap = [(j, j + 1, K - 2 - j, K - 1 - j) for j in range(n)]
            for i, sgn in ((0, -1.0), (len(rings) - 1, 1.0)):
                def fn(k, ui=s[i]):
                    return (ui, perim[k])
                caps.append((i, cap if sgn < 0 else [q[::-1] for q in cap], fn))
        return sweep._sweep_rings(rings, perim, s, P.closed, caps)


def welt(path, width=2.5, height=0.8, *, sink=0.3, taper=4.0, offset=0.0, across=8, seed=0, wobble=0.08):
    """A felled seam's ridge or a lapped edge as geometry of its own (spec 02 §4.9 (a): 0.8 x 2.5): a
    parabolic section `height` mm over the surface and `width` mm wide where it meets it, sunk `sink`
    below (so it meets the panel in a crease, never a coplanar band), tapering over `taper` mm at an open
    path's ends, its height varying by +-`wobble` along the seam, `offset` mm across the path (+ to its
    right). Unlike ridge(), it does not depend on the panel's resolution: the GN ridge on the materials test
    boot's 0.6 mm render mesh came out as a sawtooth band. Give it the panel's material. Returns a Welt
    (a sweep: .to_object(name, coll, scope) makes the object with UV.Real)."""
    return Welt(path, width, height, sink, taper, across, offset, seed, wobble)


def set_lod(objs, lod):
    """LOD on every `*.GN.Stitches` modifier of the objects: 0 the thread, 1 none (the shader's bump)."""
    for ob in objs:
        for m in ob.modifiers:
            if m.type == "NODES" and m.node_group and m.node_group.name.endswith(".GN.Stitches"):
                _set_inputs(m, {"LOD": int(lod)})


def drive_lod(objs, prop="stitch_lod", scene=None):
    """Drive the LOD input from a scene property (spec 09's `trousers_lod`), made at 0 if missing."""
    import bpy
    scene = scene or bpy.context.scene
    if prop not in scene:
        scene[prop] = 0
    for ob in objs:
        for m in ob.modifiers:
            if m.type == "NODES" and m.node_group and m.node_group.name.endswith(".GN.Stitches"):
                ident = _inputs(m.node_group)["LOD"]
                fc = m.driver_add(f'["{ident}"]')
                fc.driver.type = "AVERAGE"
                var = fc.driver.variables.new()
                var.targets[0].id_type = "SCENE"
                var.targets[0].id = scene
                var.targets[0].data_path = f'["{prop}"]'


def guide_object(name, paths, *, scope=None, coll=None):
    """A mesh of edges along the paths (world, metres; standoff removed), not rendered: the seam centre
    lines for ridge() and for drawing."""
    import bpy
    V, E = [], []
    for p in paths:
        co = (p.co - p.normal * p.standoff) * MM
        b = len(V)
        V.extend(co.tolist())
        E.extend((b + i, b + i + 1) for i in range(len(co) - 1))
        if p.closed:
            E.append((b + len(co) - 1, b))
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, E, [])
    me.update()
    ob = _link(name, me, scope, coll)
    ob.hide_render = True
    ob.display_type = "WIRE"
    return ob


def ridge(ob, guides, *, part, height=0.8, width=2.5, valley=0.0, valley_offset=0.0, valley_sigma=0.4,
          name="SeamRidge", guide_name=None, scope=None, coll=None):
    """A seam ridge on a panel (spec 02 §4.9 (a), spec 09 §4.10): guides is a guide object or Paths (a guide
    object `<ob>.SeamGuide` is made); the ridge is `height` mm tall over `width` mm, less a gaussian valley
    `valley` deep at `valley_offset` mm either side (sigma `valley_sigma`). Added (or updated) last on the
    stack. Returns the modifier."""
    if not hasattr(guides, "type"):
        guides = guide_object(guide_name or f"{ob.name}.SeamGuide", list(guides), scope=scope, coll=coll)
    m = ob.modifiers.get(name)
    if m is None or m.type != "NODES":
        if m is not None:
            ob.modifiers.remove(m)
        m = ob.modifiers.new(name, "NODES")
    m.node_group = ridge_group(part)
    _set_inputs(m, {"Guides": guides, "Height": height * MM, "Half Width": 0.5 * width * MM,
                    "Valley Depth": valley * MM, "Valley Offset": valley_offset * MM,
                    "Valley Sigma": valley_sigma * MM})
    return m


# --------------------------------------------------------------------------- the shader-level LOD (spec 09 §5.6)

def seam_fields(ob, row_paths, *, reach=12.0, prefix="stitch"):
    """Write the stitch bump's inputs on a panel's base mesh: `<prefix>_d` (signed distance across the
    nearest row, mm, + to the row's right) and `<prefix>_s` (arc length along it, mm), point attributes,
    for vertices within `reach` mm of a row (others get d = reach). Returns the number of vertices reached."""
    me = ob.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    M = np.array(ob.matrix_world, float)
    co = (co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]) / MM
    best = np.full(len(co), np.inf)
    d_out = np.full(len(co), float(reach))
    s_out = np.zeros(len(co))
    for P in row_paths:
        T, N, B = sweep.rmf_frames(P)
        q = P.co - P.normal * P.standoff
        s = P.s
        for i in range(len(q) - (0 if P.closed else 1)):
            j = (i + 1) % len(q)
            a, b = q[i], q[j]
            ab = b - a
            L2 = max(ab @ ab, 1e-12)
            t = np.clip(((co - a) @ ab) / L2, 0.0, 1.0)
            foot = a + t[:, None] * ab
            dist = np.linalg.norm(co - foot, axis=1)
            hit = (dist < best) & (dist < reach)
            if not hit.any():
                continue
            best[hit] = dist[hit]
            side = np.sign(np.sum((co[hit] - foot[hit]) * B[i], 1))
            d_out[hit] = side * dist[hit]
            sj = s[j] if j > i else P.length
            s_out[hit] = s[i] + t[hit] * (sj - s[i])
    for nm, val in ((f"{prefix}_d", d_out), (f"{prefix}_s", s_out)):
        att = me.attributes.get(nm) or me.attributes.new(nm, "FLOAT", "POINT")
        att.data.foreach_set("value", val.astype(np.float32))
    me.update()
    return int(np.isfinite(best).sum())


def bump_group():
    """`Lib.Stitch.Bump` (a shader group): from the panel's stitch_d and stitch_s and the row offsets, a
    thread height (m) and a mask, dashed at Pitch with stitches of Length, as wide as the thread (spec 09
    §5.6: rows at +-Offset, frac(s / pitch) < length / pitch). For a recipe's height chain (spec 16's)."""
    ng, fresh = _fresh_group(BUMP_GROUP, BUMP_VERSION, "ShaderNodeTree")
    if not fresh:
        return ng
    _interface(ng, [("Pitch mm", "INPUT", "NodeSocketFloat", 3.4, 0.1, None),
                    ("Length mm", "INPUT", "NodeSocketFloat", 2.6, 0.1, None),
                    ("Offset mm", "INPUT", "NodeSocketFloat", 0.0, 0.0, None),
                    ("Radius mm", "INPUT", "NodeSocketFloat", 0.2, 0.01, None),
                    ("Height", "OUTPUT", "NodeSocketFloat", None, None, None),
                    ("Mask", "OUTPUT", "NodeSocketFloat", None, None, None)])
    t = _Tree(ng)
    gi = t.node("NodeGroupInput")
    d = t.node("ShaderNodeAttribute", attribute_name="stitch_d").outputs["Fac"]
    s = t.node("ShaderNodeAttribute", attribute_name="stitch_s").outputs["Fac"]
    across = t.math("DIVIDE", t.math("SUBTRACT", t.math("ABSOLUTE", d), gi.outputs["Offset mm"]), gi.outputs["Radius mm"])
    prof = t.math("SQRT", t.math("MAXIMUM", t.math("SUBTRACT", 1.0, t.math("MULTIPLY", across, across)), 0.0))
    ph = t.math("FRACT", t.math("DIVIDE", s, gi.outputs["Pitch mm"]))
    ln = t.math("DIVIDE", gi.outputs["Length mm"], gi.outputs["Pitch mm"])
    u = t.math("DIVIDE", ph, ln)
    dash = t.math("MULTIPLY", t.math("LESS_THAN", ph, ln), t.math("SINE", t.math("MULTIPLY", t.math("MINIMUM", u, 1.0), math.pi)))
    mask = t.math("MULTIPLY", prof, dash)
    h = t.math("MULTIPLY", t.math("MULTIPLY", mask, gi.outputs["Radius mm"]), MM)
    go = t.node("NodeGroupOutput")
    ng.links.new(h, go.inputs["Height"])
    ng.links.new(mask, go.inputs["Mask"])
    return ng


# --------------------------------------------------------------------------- self-test

def _evaluated(ob):
    import bpy
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        M = np.array(ob.matrix_world, float)
        co = (co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]) / MM
        return {"co": co, "faces": len(me.polygons), "uv": [u.name for u in me.uv_layers],
                "mat": [m.name for m in me.materials if m is not None]}
    finally:
        ev.to_mesh_clear()


def _grid_object(name, n=60, size=120.0, bend_r=None):
    """A grid (size mm square, n quads a side) in XY, optionally bent round a cylinder of radius bend_r
    about the Y axis (a curved panel), normals +Z."""
    import bpy
    g = np.linspace(-size / 2, size / 2, n + 1)
    X, Y = np.meshgrid(g, g)
    Z = np.zeros_like(X)
    if bend_r:
        th = X / bend_r
        X, Z = bend_r * np.sin(th), bend_r * np.cos(th) - bend_r
    V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1) * MM
    idx = np.arange(X.size).reshape(n + 1, n + 1)
    F = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], F.tolist())
    me.shade_smooth()
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def selftest():
    """Layout on a curved panel (pitch, stitch length, holes on the surface, rows across, zigzag width, bar
    tack and box extents, seeds repeat), edge-attribute chains (open, closed, branched), the GN thread
    (counts, height over the surface, UV.Real, material, LOD), the ridge's profile, the bump fields."""
    import bpy
    R, made, groups = {}, [], []
    try:
        panel = _grid_object("SelftestSt.Panel", n=80, size=120.0, bend_r=60.0)
        made.append(panel)
        surf = sweep.Surface(panel)
        seam = seam_path(surf, [(-40.0, -45.0, 30.0), (0.0, 0.0, 30.0), (30.0, 45.0, 30.0)], step=1.0)
        L = seam.length
        st = running(seam, 3.4, 0.8, seed=3)
        k = int(math.floor((L - 0.8 + 0.8) / 3.4))
        lens = st.lengths()
        assert len(st) == k and abs(lens.mean() - 2.6) < 0.05 and lens.std() < 0.1, (len(st), k, lens.mean())
        gaps = np.linalg.norm(st.p0[1:] - st.p1[:-1], axis=1)
        assert abs(gaps.mean() - 0.8) < 0.12, gaps.mean()
        dev = np.abs(surf.signed_distance(np.vstack([st.p0, st.p1])))
        assert dev.max() < 0.03, dev.max()   # yaw and wander move the holes in the tangent plane only
        st2 = running(seam, 3.4, 0.8, seed=3)
        assert np.array_equal(st.p0, st2.p0), "a seed does not repeat"
        R["running"] = {"stitches": len(st), "length_mm": round(float(lens.mean()), 3),
                        "gap_mm": round(float(gaps.mean()), 3), "off_surface_mm": round(float(dev.max()), 4)}

        # double-needle rows +-3.2 along the surface: each row's holes lie 3.2 from the seam line
        dbl = rows(seam, (-3.2, 3.2), 3.6, 1.0, seed=5, wander=0.0, yaw_deg=0.0, offset=0.0)
        mid = dbl.mid()
        dist = np.array([np.linalg.norm(seam.co - m, axis=1).min() for m in mid])
        inner = (mid[:, 1] > -38) & (mid[:, 1] < 38)
        assert np.all(np.abs(dist[inner] - 3.2) < 0.08), (dist[inner].min(), dist[inner].max())
        R["double_row_offset_mm"] = [round(float(dist[inner].min()), 3), round(float(dist[inner].max()), 3)]

        # a closed ring round the bent panel's dome takes a whole number of pitches
        ring_c = [(20 * math.cos(a), 20 * math.sin(a), 30.0) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
        ring = seam_path(surf, ring_c, closed=True)
        rs = running(ring, 3.4, 0.8, seed=1)
        assert abs(len(rs) * 3.4 - ring.length) < 3.4 * 0.5 + 1e-6

        # zigzag and bar tack: legs alternate across the width; extents
        zz = zigzag(seam, 2.0, 3.4, seed=2, wander=0.0, offset=0.0, yaw_deg=0.0)
        T, N, B = sweep.rmf_frames(seam)
        across = []
        for p in zz.p0[5:-5]:
            i = int(np.argmin(np.linalg.norm(seam.co - p, axis=1)))
            across.append((p - seam.co[i]) @ B[i])
        across = np.abs(np.array(across))
        assert np.all(np.abs(across - 1.0) < 0.1), (across.min(), across.max())
        bt = bartack(surf, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 22.0, 3.0, 1.05, seed=4)
        ext_y = np.ptp(np.vstack([bt.p0, bt.p1])[:, 1])
        ext_x = np.ptp(np.vstack([bt.p0, bt.p1])[:, 0])
        assert 20.5 < ext_y < 22.5 and 2.6 < ext_x < 3.3, (ext_y, ext_x)
        assert 39 <= len(bt) <= 43, len(bt)   # spec 13: 21 V's at 1.05 over 22 mm, 42 stitches, one pass
        assert len(bartack(surf, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 22.0, 3.0, 1.05, passes=2)) > 78
        bx = box_x(surf, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (15.0, 10.0), 2.5)
        assert len(bx) > 25 and np.ptp(bx.mid()[:, 1]) < 10.5
        R["bartack"] = {"legs": len(bt), "extent_mm": [round(float(ext_x), 2), round(float(ext_y), 2)],
                        "box_x_stitches": len(bx)}

        # chains of an edge attribute: an open line, a closed square and a T (split at its branch point)
        chains = _chains(np.array([(0, 1), (1, 2), (2, 3), (10, 11), (11, 12), (12, 13), (13, 10),
                                   (20, 21), (21, 22), (21, 23)]))
        kinds = sorted((len(c), cl) for c, cl in chains)
        assert kinds == [(2, False), (2, False), (2, False), (4, False), (4, True)], kinds
        me = panel.data
        flag = me.attributes.new("seam", "BOOLEAN", "EDGE")
        ev = np.empty(len(me.edges) * 2, np.int64)
        me.edges.foreach_get("vertices", ev)
        ev = ev.reshape(-1, 2)
        co = np.array([v.co for v in me.vertices]) / MM
        on = (np.abs(co[ev[:, 0], 1]) < 0.01) & (np.abs(co[ev[:, 1], 1]) < 0.01)   # the row at y 0
        flag.data.foreach_set("value", on)
        sp = seam_paths(panel, "seam")
        assert len(sp) == 1 and abs(sp[0].length - 120.0) < 1.0, [p.length for p in sp]   # the arc, bent

        # the GN thread: counts, height of the middle above the surface, UV.Real, material, LOD
        ob = stitch_object("SelftestSt.Stitches", st, part="SelftestSt", radius=0.2, sink=0.1, bow=0.15,
                           material=None)
        made.append(ob)
        groups.append(ob.modifiers["Stitches"].node_group)
        e = _evaluated(ob)
        per = 7 * 6 + 0   # rings x sides (the caps add faces, not vertices)
        assert len(e["co"]) == len(st) * per, (len(e["co"]), len(st) * per)
        assert "UV.Real" in e["uv"], e["uv"]
        sd = surf.signed_distance(e["co"])
        top, low = float(sd.max()), float(sd.min())
        assert 0.26 < top < 0.31 and low < -0.15, (top, low)   # the middle's top r - sink + r = 0.3; the ends dive
        _set_inputs(ob.modifiers["Stitches"], {"LOD": 1})
        assert len(_evaluated(ob)["co"]) == 0
        _set_inputs(ob.modifiers["Stitches"], {"LOD": 0})
        R["thread"] = {"vertices": len(e["co"]), "faces": e["faces"], "top_mm": round(top, 3), "end_mm": round(low, 3)}

        # the ridge on a flat grid: full height on the guide, nothing beyond the half width, the valley
        flat = _grid_object("SelftestSt.Flat", n=120, size=60.0)
        made.append(flat)
        line = sweep.Path(np.stack([np.zeros(61), np.linspace(-30, 30, 61), np.zeros(61)], 1),
                          np.tile([0.0, 0.0, 1.0], (61, 1)))
        ridge(flat, [line], part="SelftestSt", height=0.8, width=4.0, valley=0.3, valley_offset=3.0,
              valley_sigma=0.4)
        guide = bpy.data.objects["SelftestSt.Flat.SeamGuide"]
        made.append(guide)
        groups.append(flat.modifiers["SeamRidge"].node_group)
        z = _evaluated(flat)["co"]
        x0 = np.abs(z[:, 0]) < 1e-3
        x3 = np.abs(np.abs(z[:, 0]) - 3.0) < 1e-3
        x10 = np.abs(np.abs(z[:, 0]) - 10.0) < 1e-3
        assert np.allclose(z[x0, 2], 0.8, atol=1e-4) and np.allclose(z[x10, 2], 0.0, atol=1e-4)
        assert np.allclose(z[x3, 2], -0.3, atol=0.01), z[x3, 2]
        R["ridge_mm"] = {"crest": round(float(z[x0, 2].mean()), 4), "valley": round(float(z[x3, 2].mean()), 4)}

        # the welt: closed, 0.8 over the surface at its middle, 2.5 wide where it meets it, tapered ends
        wl = welt(line, 2.5, 0.8, sink=0.3, taper=4.0, wobble=0.0)
        wv = wl.verts
        mid = np.abs(wv[:, 1]) < 10.0
        above = mid & (wv[:, 2] > 1e-6)
        assert wl.manifold() and wl.volume() > 0
        assert abs(wv[mid, 2].max() - 0.8) < 0.01 and abs(2 * np.abs(wv[above, 0]).max() - 2.5) < 0.35, \
            (wv[mid, 2].max(), np.abs(wv[above, 0]).max())
        assert wv[np.abs(wv[:, 1]) > 29.9, 2].max() < 0.05   # the ends taper to nothing
        assert np.abs(wv[:, 0]).max() < 2.0 and np.abs(wv[:, 1]).max() < 30.01 and wv[:, 2].min() > -0.5
        R["welt"] = {"faces": len(wl.faces), "crest_mm": round(float(wv[mid, 2].max()), 3)}
        tko = tack_object("SelftestSt.Tack", bt, part="SelftestSt", material=None)
        made.append(tko)
        et = _evaluated(tko)
        assert len(et["co"]) == len(bt) * 42 and np.ptp(et["co"][:, 1]) < 23.0

        # bump fields: signed distance and arc length beside the line
        n = seam_fields(flat, [line], reach=5.0)
        d = np.empty(len(flat.data.vertices))
        flat.data.attributes["stitch_d"].data.foreach_get("value", d)
        s = np.empty(len(flat.data.vertices))
        flat.data.attributes["stitch_s"].data.foreach_get("value", s)
        cx = np.array([v.co for v in flat.data.vertices]) / MM
        near = np.abs(cx[:, 0]) < 4.9
        assert np.allclose(np.abs(d[near]), np.abs(cx[near, 0]), atol=1e-3)
        assert np.allclose(s[near], cx[near, 1] + 30.0, atol=1e-3)
        assert np.all(np.sign(d[near & (cx[:, 0] > 0.1)]) == np.sign(d[near & (cx[:, 0] > 0.1)][0]))
        bg = bump_group()
        R["bump_fields"] = {"vertices": n, "group": bg.name}
        return R
    finally:
        for o in made:
            data = o.data
            bpy.data.objects.remove(o)
            if data is not None and data.users == 0:
                bpy.data.meshes.remove(data)
        for g in groups + [bpy.data.node_groups.get(BUMP_GROUP)]:
            if g is not None and g.users == 0 and g.name.startswith(("SelftestSt.", BUMP_GROUP)):
                bpy.data.node_groups.remove(g)
