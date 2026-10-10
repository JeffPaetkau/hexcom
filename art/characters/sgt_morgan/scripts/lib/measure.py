"""Measurement before rendering (spec 18 §4.8.4): landmarks, projection through the presets, girths and
sections, clearances, silhouettes and their IoU, stature and bounding boxes, the envelope every part's
measure() returns, and the term objectives the server's variants and optimise commands evaluate.

Millimetres in the API, metres in Blender. Every point a function takes or returns is in mm, world space;
meshes are read from the depsgraph in metres and converted at the edge. Measurements read the evaluated
mesh (shape keys, modifiers, pose), so they see what a render sees. evaluate() takes one read that several
measurements can share (each primitive accepts the Mesh it returns in place of an object): an objective
that measures twenty girths pays for one depsgraph read and about a millisecond a slice.

Landmarks name vertices of the object's own mesh, the indices MPFB, spec 06's tables and the linear target
model use. A Mask modifier (MPFB's "Hide helpers", a garment's Delete.* group) drops vertices from the
evaluated mesh but keeps the rest in order, so the evaluated-to-original index map is rebuilt from the
masks' vertex groups once per modifier stack and cached; any other modifier that changes the vertex count
is refused rather than guessed. forget() drops the caches (the server calls it after a build or restore).

Projection is spec 17's scripts/eval/camproj.py through camera.py's preset registry, so a pixel here is the
pixel the render harness writes. Silhouettes rasterise the projected triangles at pixel centres (span
filling: each triangle's row intervals, accumulated with one bincount and a cumulative sum), which is the
sampling rule of an unantialiased render and matches a 0.5 threshold of an antialiased one without bias;
the spec's lattice splat with a 3 x 3 closing is kept as method="splat" for comparison (§4.13, deviations).
"""
import copy
import glob
import importlib.util
import math
import os
import time

import numpy as np

from . import env, log
from eval import camera, camproj  # spec 17: camera maths and the preset registry, numpy only (no bpy at import)


def _io(name):
    """Spec 17's PNG and render modules, imported dynamically: a part's cache key hashes the modules its
    script imports (spec 18 §4.13), and reading or writing a mask is no input of a build."""
    import importlib
    return importlib.import_module(f"eval.{name}")

MM = 1000.0
GEOMETRY = ("MESH", "CURVE", "SURFACE", "META", "FONT")
NEED_ALL = ("tris", "polys", "orig")
# Modifiers that move vertices without adding, removing or reordering them: the evaluated mesh keeps the
# object's own vertex indices through these.
KEEP_TOPOLOGY = {"ARMATURE", "CAST", "CLOTH", "COLLISION", "CORRECTIVE_SMOOTH", "CURVE", "DATA_TRANSFER",
                 "DISPLACE", "HOOK", "LAPLACIANDEFORM", "LAPLACIANSMOOTH", "LATTICE", "MESH_CACHE",
                 "MESH_DEFORM", "NORMAL_EDIT", "SHRINKWRAP", "SIMPLE_DEFORM", "SMOOTH", "SOFT_BODY", "SURFACE",
                 "SURFACE_DEFORM", "TRIANGULATE", "UV_PROJECT", "UV_WARP", "VERTEX_WEIGHT_EDIT",
                 "VERTEX_WEIGHT_MIX", "VERTEX_WEIGHT_PROXIMITY", "WARP", "WAVE", "WEIGHTED_NORMAL"}
MASK_DIRS = (env.path("ref", "masks"), env.path("cache", "masks"))  # where sheet.py looks too
DECLARED = env.path("scripts", "eval", "declared_diffs.json")       # spec 18 §2.2's register
PRIMITIVES = ("landmarks", "project", "girth", "section", "clearance", "stature", "bbox", "silhouette")

_INDEX_MAPS, _GROUPS, _REFERENCES, _FILES, _TOPOLOGY = {}, {}, {}, {}, {}


def forget():
    """Drop every cache that describes the session's meshes (topology, index maps, group weights,
    references)."""
    for c in (_INDEX_MAPS, _GROUPS, _REFERENCES, _FILES, _TOPOLOGY):
        c.clear()


# --------------------------------------------------------------------------- objects and mesh reads

def obj(x):
    """A Blender object from an object or its name."""
    import bpy
    if isinstance(x, Mesh):
        x = x.name
    if isinstance(x, str):
        ob = bpy.data.objects.get(x)
        if ob is None:
            raise KeyError(f"no object {x!r}")
        return ob
    return x


def objects(spec=None, preset=None):
    """Objects from names or fnmatch patterns (a pattern may name a collection: then all its objects). By
    default every geometry object of the scene that renders, without Scene.* (spec 17's floor, cameras and
    probes) and without what the preset hides for its view."""
    import fnmatch
    import bpy
    scene = bpy.context.scene
    if spec is not None:
        out = []
        for item in [spec] if isinstance(spec, (str, Mesh)) or not hasattr(spec, "__iter__") else spec:
            if not isinstance(item, str):
                out.append(item)
                continue
            hits = [o for o in bpy.data.objects if fnmatch.fnmatchcase(o.name, item)]
            for c in bpy.data.collections:
                if fnmatch.fnmatchcase(c.name, item):
                    hits += [o for o in c.all_objects if o not in hits]
            if not hits:
                raise KeyError(f"no object or collection matches {item!r}")
            out += [o for o in hits if o not in out]
        return out
    hide = list((preset or {}).get("hide") or [])
    hidden_obs, hidden_colls = camera.hidden(hide, scene) if hide else ([], [])
    gone = set(hidden_obs)
    for c in hidden_colls:
        gone |= set(c.all_objects)
    layer = bpy.context.view_layer
    return [o for o in layer.objects if o.type in GEOMETRY and not o.hide_render and o not in gone
            and not o.name.startswith("Scene.") and not any(c.hide_render for c in o.users_collection)]


class Mesh:
    """One read of an object's evaluated mesh: world positions in metres (co), the triangles and polygon
    loops asked for, and orig, the object's own index of each evaluated vertex (None when they agree).
    Every primitive takes a Mesh in place of an object, so one read can serve many measurements."""

    def __init__(self, name, co, matrix, n_orig):
        self.name, self.co, self.matrix, self.n_orig = name, co, matrix, n_orig
        self.tris = self.loop_start = self.loop_total = self.loop_vert = self.loop_edge = None
        self.orig, self.have, self._topo, self._full = None, set(), {}, None

    @property
    def _ring(self):
        """Each polygon corner's next corner around its polygon, and its polygon (kept with the topology)."""
        if "ring" not in self._topo:
            nxt = np.arange(1, len(self.loop_vert) + 1)
            nxt[self.loop_start + self.loop_total - 1] = self.loop_start
            self._topo["ring"] = (nxt, np.repeat(np.arange(len(self.loop_start)), self.loop_total))
        return self._topo["ring"]

    def needs(self, need):
        missing = set(need) - self.have
        if missing:
            raise ValueError(f"this read of {self.name} lacks {sorted(missing)}; evaluate() it with them")
        return self

    def original(self):
        """Positions in the object's own vertex order (n_orig, 3), NaN where a mask removed the vertex."""
        self.needs(("orig",))
        if self.orig is None:
            return self.co
        if self._full is None:
            self._full = np.full((self.n_orig, 3), np.nan)
            self._full[self.orig] = self.co
        return self._full


def _ints(me, attr, coll, prop, n):
    """An int array of a mesh: from the generic attribute if Blender has it (twice as fast), else RNA."""
    a = np.empty(n, np.int32)
    at = me.attributes.get(attr) if attr else None
    if at is not None:
        at.data.foreach_get("value", a)
    else:
        getattr(me, coll).foreach_get(prop, a)
    return a.astype(np.int64)


def _topology(ob, me, need):
    """The evaluated mesh's triangles and polygon loops, cached per object while its element counts,
    modifier stack and a few spot-checked indices stay the same: reading them costs ≈ 20 ms on the MPFB
    body against 0.03 ms for the positions, and a shape key or parameter change never alters them. (A cached
    triangulation of an n-gon can differ from Blender's fresh one once the n-gon bends; quads split the same
    way whatever the positions.)"""
    L, P = len(me.loops), len(me.polygons)
    stack = tuple((md.name, md.type, md.show_viewport) for md in getattr(ob, "modifiers", ()))
    key = (ob.name, len(me.vertices), len(me.edges), P, L, stack)
    spot = tuple(me.loops[i].vertex_index for i in (0, L // 3, (2 * L) // 3, L - 1)) if L else ()
    spot += tuple(me.polygons[i].loop_total for i in (0, P // 2, P - 1)) if P else ()
    topo = _TOPOLOGY.get(key)
    if topo is None or topo["spot"] != spot:
        topo = _TOPOLOGY[key] = {"spot": spot}
    if "tris" in need and "tris" not in topo:
        t = np.empty(len(me.loop_triangles) * 3, np.int32)
        me.loop_triangles.foreach_get("vertices", t)
        topo["tris"] = t.reshape(-1, 3).astype(np.int64)
    if "polys" in need and "loop_vert" not in topo:
        topo.update(loop_start=_ints(me, None, "polygons", "loop_start", P),
                    loop_total=_ints(me, None, "polygons", "loop_total", P),
                    loop_vert=_ints(me, ".corner_vert", "loops", "vertex_index", L),
                    loop_edge=_ints(me, ".corner_edge", "loops", "edge_index", L))
    return topo


def evaluate(ob, need=NEED_ALL, depsgraph=None):
    """Read an object's evaluated mesh into a Mesh (positions always; "tris", "polys", "orig" on request)."""
    import bpy
    if isinstance(ob, Mesh):
        return ob.needs(need)
    ob = obj(ob)
    dg = depsgraph or bpy.context.evaluated_depsgraph_get()  # brings the depsgraph up to date first
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    if me is None:
        raise ValueError(f"{ob.name} ({ob.type}) has no mesh to measure")
    try:
        n = len(me.vertices)
        co = np.empty(n * 3, np.float32)
        me.attributes["position"].data.foreach_get("vector", co)  # 20 x faster than vertices' "co"
        M = np.array(ev.matrix_world, np.float64)
        m = Mesh(ob.name, co.reshape(-1, 3).astype(np.float64) @ M[:3, :3].T + M[:3, 3], M,
                 len(ob.data.vertices) if ob.type == "MESH" else n)
        need = set(need)
        if need & {"tris", "polys"}:
            m._topo = _topology(ob, me, need)
            m.tris = m._topo.get("tris")
            for k in ("loop_start", "loop_total", "loop_vert", "loop_edge"):
                setattr(m, k, m._topo.get(k))
        if "orig" in need:
            m.orig = original_index(ob, n)
        m.have = need
    finally:
        ev.to_mesh_clear()
    return m


def _read(x, cache=None, need=NEED_ALL):
    """A Mesh for an object or name, through a per-evaluation cache when one is given."""
    if isinstance(x, Mesh) or cache is None:
        return evaluate(x, need)
    name = obj(x).name
    if name not in cache:
        cache[name] = evaluate(name, NEED_ALL)
    return cache[name]


def group_weights(ob, name):
    """Each vertex's weight in a vertex group (0 outside it), cached per object, group and vertex count:
    Blender has no bulk read for weights, and a Python pass over the MPFB body's 19,158 vertices costs tens
    of milliseconds."""
    ob = obj(ob)
    key = (ob.name, ob.data.name, name, len(ob.data.vertices))
    hit = _GROUPS.get(key)
    if hit is None:
        hit = np.zeros(len(ob.data.vertices))
        vg = ob.vertex_groups.get(name)
        if vg is not None:
            gi = vg.index
            for v in ob.data.vertices:
                for g in v.groups:
                    if g.group == gi:
                        hit[v.index] = g.weight
                        break
        _GROUPS[key] = hit
    return hit


def original_index(ob, n_eval):
    """The object's own index of each evaluated vertex, or None when the counts agree (module doc)."""
    if ob.type != "MESH":
        return None
    n = len(ob.data.vertices)
    if n == n_eval:
        return None
    mods = [m for m in ob.modifiers if m.show_viewport]
    masks = [m for m in mods if m.type == "MASK"]
    odd = [m.name for m in mods if m.type not in KEEP_TOPOLOGY and m.type != "MASK"]
    odd += [m.name for m in masks if m.mode != "VERTEX_GROUP" or getattr(m, "use_smooth", False)]
    if odd or not masks:
        raise ValueError(f"{ob.name}: {n_eval} evaluated vertices against its own {n}, and the modifiers "
                         f"{odd or [m.name for m in mods]} change the topology in a way vertex landmarks cannot "
                         "follow; measure them before those modifiers")
    sig = (ob.name, ob.data.name, n,
           tuple((m.name, m.vertex_group, m.invert_vertex_group, round(m.threshold, 9)) for m in masks))
    keep = _INDEX_MAPS.get(sig)
    if keep is None:
        kept = np.ones(n, bool)
        for m in masks:  # Blender's Mask modifier keeps a vertex whose weight exceeds the threshold
            kept &= (group_weights(ob, m.vertex_group) > m.threshold) != m.invert_vertex_group
        keep = np.nonzero(kept)[0]
        _INDEX_MAPS[sig] = keep
    if len(keep) != n_eval:
        _INDEX_MAPS.pop(sig, None)
        raise ValueError(f"{ob.name}: the masks keep {len(keep)} vertices by their groups, the depsgraph "
                         f"has {n_eval}; a vertex group changed under a cached map, or a mask works otherwise")
    return keep


# --------------------------------------------------------------------------- landmarks and projection

def landmark_rows(ob, spec):
    """A landmark spec as sparse rows (names, idx, w, row): landmark row[k] takes w[k] times the object's
    own vertex idx[k], and each landmark's weights sum to 1, so a landmark is a fixed linear combination of
    vertices (which is what lets the linear target model predict it exactly).

    A spec maps names to: a vertex index; a list of indices (their mean); {"v": i}; {"verts": [...],
    "w": [...]} (a weighted mean); {"bary": [[i, a], [j, b], [k, c]]} (a barycentric point); or
    {"group": name, "min": 0.0} (the weighted centroid of a vertex group's members above min). A plain list
    of indices is a spec too, named by the indices."""
    ob = obj(ob)
    n = len(ob.data.vertices) if ob.type == "MESH" else None
    if not isinstance(spec, dict):
        idx = np.asarray(spec, np.int64).reshape(-1)
        if n is not None and len(idx) and (idx.min() < 0 or idx.max() >= n):
            raise ValueError(f"a landmark vertex index is out of range for {ob.name} ({n} vertices)")
        return [str(i) for i in idx.tolist()], idx, np.ones(len(idx)), np.arange(len(idx))
    names, rows = [], []
    for name, d in spec.items():
        if isinstance(d, (int, np.integer)):
            idx, w = [int(d)], [1.0]
        elif isinstance(d, (list, tuple)):
            idx, w = [int(i) for i in d], [1.0] * len(d)
        elif "v" in d or "vertex" in d:
            idx, w = [int(d.get("v", d.get("vertex")))], [1.0]
        elif "verts" in d:
            idx = [int(i) for i in d["verts"]]
            w = [float(x) for x in d.get("w") or [1.0] * len(idx)]
        elif "bary" in d:
            idx, w = [int(i) for i, _ in d["bary"]], [float(a) for _, a in d["bary"]]
        elif "group" in d:
            gw = group_weights(ob, d["group"])
            sel = np.nonzero(gw > float(d.get("min", 0.0)))[0]
            if not len(sel):
                raise ValueError(f"landmark {name}: vertex group {d['group']!r} of {ob.name} has no member "
                                 f"above {d.get('min', 0.0)}")
            idx, w = sel.tolist(), gw[sel].tolist()
        else:
            raise ValueError(f"landmark {name}: {d!r} is not a vertex, list, verts, bary or group spec")
        idx, w = np.asarray(idx, np.int64), np.asarray(w, float)
        if len(idx) != len(w) or not len(idx) or abs(w.sum()) < 1e-12:
            raise ValueError(f"landmark {name}: indices and weights do not match, or the weights sum to 0")
        if n is not None and (idx.min() < 0 or idx.max() >= n):
            raise ValueError(f"landmark {name}: vertex index out of range for {ob.name} ({n} vertices)")
        names.append(str(name))
        rows.append((idx, w / w.sum()))
    row = np.concatenate([np.full(len(i), k) for k, (i, _) in enumerate(rows)]) if rows else np.zeros(0, np.int64)
    return (names, np.concatenate([i for i, _ in rows]) if rows else np.zeros(0, np.int64),
            np.concatenate([w for _, w in rows]) if rows else np.zeros(0), row)


def combine(names, idx, w, row, pos):
    """Sparse landmark rows applied to positions (n, 3): (len(names), 3)."""
    P = pos[idx] * w[:, None]
    return np.stack([np.bincount(row, P[:, k], minlength=len(names)) for k in range(3)], axis=1)


def landmarks(ob, spec):
    """Named points on the evaluated mesh, world mm: {name: (3,)} for a dict spec, (N, 3) for a list."""
    m = evaluate(ob, ("orig",))
    names, idx, w, row = landmark_rows(m.name, spec)
    pos = m.original()
    out = combine(names, idx, w, row, pos) * MM
    bad = ~np.all(np.isfinite(out), axis=1)
    if bad.any():
        k = int(np.nonzero(bad)[0][0])
        hidden = [int(i) for i in idx[row == k] if not np.isfinite(pos[i, 0])]
        raise ValueError(f"landmark {names[k]}: vertices {hidden[:5]} of {m.name} are removed by a mask")
    return dict(zip(names, out)) if isinstance(spec, dict) else out


_REGISTRY = [None, None]


def registry():
    """camera.py's preset registry, re-read when a preset file changes."""
    files = sorted(glob.glob(os.path.join(camera.PRESET_DIR, "*.json")))
    sig = tuple((f, os.path.getmtime(f)) for f in files)
    if _REGISTRY[0] != sig:
        _REGISTRY[:] = [sig, camera.load_registry(files)]
    return _REGISTRY[1]


def preset_of(preset):
    return preset if isinstance(preset, dict) else registry().get(preset)


def camera_for(preset, scale=None, view=0):
    """The camproj.Camera a preset renders through, sized as the form tier renders it (its scale, or
    scale), for a preset name, a resolved preset dict, or a Camera (returned as it is)."""
    if isinstance(preset, camproj.Camera):
        return preset
    p = preset_of(preset)
    cam, r = p["camera"], p["render"]
    s = r.get("scale", 1) if scale is None else scale
    if cam["type"] == "hero":
        return camproj.HERO.crop(r.get("border_px") or (0, 0, camproj.W, camproj.H), s)
    pos, target, up = camera.placement(p, view)
    R = camproj.look_at_matrix(pos, target, up)
    w, h = (int(round(v * s)) for v in r["res"])
    sensor = float(cam.get("sensor_mm", camproj.SENSOR_MM))
    if cam["type"] == "ortho":
        return camproj.Camera.blender(pos, R, w, h, sensor=sensor, ortho_scale=cam["ortho_scale_mm"] / MM)
    return camproj.Camera.blender(pos, R, w, h, float(cam["lens_mm"]), sensor)


def project(points, preset, scale=None, view=0, depth=False):
    """Continuous pixels (x right, y down, the preset's own image) of points in mm: (N, 2), or (N, 3) with
    the depth along the optical axis in mm; a dict of points gives a dict."""
    cam = camera_for(preset, scale, view)
    names = list(points) if isinstance(points, dict) else None
    P = np.asarray([points[k] for k in names] if names else points, float).reshape(-1, 3) / MM
    xy, d = cam.project(P, depth=True)
    out = np.column_stack([xy, d * MM]) if depth else xy
    return dict(zip(names, out)) if names else out


# --------------------------------------------------------------------------- sections and girths

def plane_frame(plane):
    """(origin, normal, u, v) in metres for a plane given in mm: a number (the horizontal plane at that
    height), {"x"|"y"|"z": value} (the plane across that axis), {"point": p, "normal": n} or (p, n). u and v
    span the plane: +X and +Y for a horizontal plane, so section coordinates read as plan mm; on a
    vertical plane v points up."""
    if isinstance(plane, (int, float, np.number)):
        o, n = (0.0, 0.0, float(plane)), (0.0, 0.0, 1.0)
    elif isinstance(plane, dict) and "point" in plane:
        o, n = plane["point"], plane.get("normal", (0.0, 0.0, 1.0))
    elif isinstance(plane, dict):
        axes = [k for k in ("x", "y", "z") if k in plane]
        if len(axes) != 1:
            raise ValueError(f"plane {plane!r}: give one of x, y, z, or point and normal")
        o, n = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
        o["xyz".index(axes[0])] = float(plane[axes[0]])
        n["xyz".index(axes[0])] = 1.0
    else:
        o, n = plane
    o, n = np.asarray(o, float) / MM, np.asarray(n, float)
    n = n / math.sqrt(float(n @ n))

    def cross(p, q):  # np.cross costs tens of microseconds on 3-vectors
        return np.array([p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]])

    if abs(n[2]) >= 0.9:
        u = np.array([1.0, 0.0, 0.0]) - n[0] * n
        u /= math.sqrt(float(u @ u))
        v = cross(n, u)
    else:
        v = np.array([0.0, 0.0, 1.0]) - n[2] * n
        v /= math.sqrt(float(v @ v))
        u = cross(v, n)
    return o, n, u, v


def _ring(m):
    return m._ring


def _edges(m):
    """Each polygon edge's two vertices and the (up to) two polygons on it, built once per topology:
    (verts (E, 2), polys (E, 2) with −1 where a boundary edge has no second polygon)."""
    if "edges" not in m._topo:
        nxt, poly = m._ring
        E = int(m.loop_edge.max()) + 1 if len(m.loop_edge) else 0
        verts = np.full((E, 2), -1, np.int64)
        verts[m.loop_edge, 0] = m.loop_vert
        verts[m.loop_edge, 1] = m.loop_vert[nxt]
        order = np.argsort(m.loop_edge, kind="stable")
        e_sorted = m.loop_edge[order]
        first = np.ones(len(order), bool)
        first[1:] = e_sorted[1:] != e_sorted[:-1]
        polys = np.full((E, 2), -1, np.int64)
        polys[e_sorted[first], 0] = poly[order][first]
        second = np.zeros(len(order), bool)
        second[1:] = ~first[1:] & first[:-1]  # the second corner on an edge (a third, non-manifold, is ignored)
        polys[e_sorted[second], 1] = poly[order][second]
        m._topo["edges"] = (verts, polys)
    return m._topo["edges"]


def _chains(m, plane):
    """The plane's section of a Mesh as chains of points (metres) with a closed flag.

    Every polygon edge the plane crosses gives a point; the two crossings of each polygon are joined, so
    chains follow face adjacency through shared edges (a polygon crossed four or more times, a concave
    one, has its crossings paired in order along the cut). Only real mesh edges carry points, never a
    triangulation's diagonals, so a quad mesh gives the same points as slicing its edges directly (the
    cloud probe's method). A vertex on the plane counts as below it, which keeps every crossing a clean
    pair."""
    frame = plane_frame(plane)
    o, nrm = frame[0], frame[1]
    s = (m.co - o) @ nrm
    side = s > 0.0
    verts, polys = _edges(m)
    a, b = verts[:, 0], verts[:, 1]
    cut = np.nonzero((a >= 0) & (side[a] != side[b]))[0]
    if not len(cut):
        return [], frame
    pa, pb = a[cut], b[cut]
    t = s[pa] / (s[pa] - s[pb])
    P = m.co[pa] + (m.co[pb] - m.co[pa]) * t[:, None]
    at = {e: i for i, e in enumerate(cut.tolist())}
    pp = polys[cut]
    pe = np.concatenate([pp[:, 0], pp[:, 1]])
    ee = np.concatenate([cut, cut])
    keep = pe >= 0
    pe, ee = pe[keep], ee[keep]
    order = np.argsort(pe, kind="stable")
    pe, ee = pe[order], ee[order]
    starts = np.r_[0, np.flatnonzero(np.diff(pe)) + 1, len(pe)]
    sizes = np.diff(starts)
    links = {}

    def link(e1, e2):
        links.setdefault(e1, []).append(e2)
        links.setdefault(e2, []).append(e1)

    two = starts[:-1][sizes == 2]
    for e1, e2 in zip(ee[two].tolist(), ee[two + 1].tolist()):
        link(e1, e2)
    for g0, n_cut in zip(starts[:-1][sizes != 2].tolist(), sizes[sizes != 2].tolist()):
        es = ee[g0:g0 + n_cut].tolist()   # a concave polygon cut more than twice: pair along the cut
        q = P[[at[e] for e in es]]
        axis = int(np.argmax(q.max(0) - q.min(0)))
        es = [es[i] for i in np.argsort(q[:, axis])]
        for e1, e2 in zip(es[0::2], es[1::2]):
            link(e1, e2)
    chains, seen = [], set()
    for start in [e for e, nb in links.items() if len(nb) == 1] + list(links):
        if start in seen:
            continue
        chain, cur = [start], start
        seen.add(start)
        while True:
            nb = [e for e in links[cur] if e not in seen]
            if not nb:
                break
            cur = nb[0]
            seen.add(cur)
            chain.append(cur)
        closed = len(chain) > 2 and start in links[cur]
        chains.append((P[[at[e] for e in chain]], closed))
    return chains, frame


def _hull_perimeter(uv):
    """Perimeter of the convex hull of 2-D points (Andrew's monotone chain), what a tape measure reads."""
    pts = sorted(set(map(tuple, np.round(uv, 12).tolist())))
    if len(pts) < 3:
        return 2.0 * math.dist(pts[0], pts[-1]) if len(pts) == 2 else 0.0

    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1])
                                   - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0.0:
                h.pop()
            h.append(p)
        return h

    hull = half(pts)[:-1] + half(pts[::-1])[:-1]
    return sum(math.dist(hull[i], hull[i - 1]) for i in range(len(hull)))


def _inside(pt, poly):
    """Is a 2-D point inside a polygon (even-odd rule; an open chain is closed by its end points)?"""
    x, y = pt
    px, py = poly[:, 0], poly[:, 1]
    qx, qy = np.r_[px[1:], px[:1]], np.r_[py[1:], py[:1]]
    cross = (py > y) != (qy > y)
    with np.errstate(divide="ignore", invalid="ignore"):
        xs = px + (y - py) * (qx - px) / (qy - py)
    return bool(np.count_nonzero(cross & (x < xs)) % 2)


def _loop_record(P, closed, frame):
    o, _, u, v = frame
    d = P - o
    uv = np.stack([d @ u, d @ v], axis=1)
    path = np.vstack([P, P[:1]]) if closed else P
    length = float(np.linalg.norm(np.diff(path, axis=0), axis=1).sum())
    x, y = uv[:, 0], uv[:, 1]
    x1, y1 = np.r_[x[1:], x[:1]], np.r_[y[1:], y[:1]]
    c = x * y1 - x1 * y
    area2 = float(c.sum()) if closed else 0.0
    if closed and abs(area2) > 1e-18:
        centre = o + float(((x + x1) * c).sum()) / (3.0 * area2) * u + float(((y + y1) * c).sum()) / (3.0 * area2) * v
    else:
        centre = P.mean(axis=0)
    return {"points": P * MM, "uv": uv * MM, "closed": bool(closed), "n": len(P), "loop_mm": length * MM,
            "tape_mm": _hull_perimeter(uv) * MM, "area_mm2": abs(area2) / 2.0 * MM * MM, "centroid": centre * MM}


def section(ob, plane):
    """The plane's section of the evaluated mesh: one record per loop, longest first, each with points
    (world mm), uv (plane mm), closed, n, loop_mm (the true perimeter; an open chain's length), tape_mm (the
    convex-hull perimeter), area_mm2 and centroid; for comparison with a spec's profile table."""
    m = evaluate(ob, ("polys",))
    chains, frame = _chains(m, plane)
    return sorted((_loop_record(P, c, frame) for P, c in chains), key=lambda r: -r["loop_mm"])


def girth(ob, plane, around=None, kind="tape"):
    """The girth in mm of the section loop that encloses `around` (a point in mm, projected onto the
    plane; the innermost loop if several do), or of the longest loop without one. kind "tape" is the
    convex-hull perimeter, what a tape measure reads (the ANSUR convention); "loop" the true perimeter.
    A point that no loop encloses is an error naming the nearest loop, never a silent wrong loop."""
    if kind not in ("tape", "loop"):
        raise ValueError(f"girth kind {kind!r}: tape or loop")
    m = evaluate(ob, ("polys",))
    chains, frame = _chains(m, plane)
    if not chains:
        raise LookupError(f"the plane {plane!r} does not cut {m.name}")
    o, _, u, v = frame

    def length(P, closed):
        path = np.vstack([P, P[:1]]) if closed else P
        return float(np.linalg.norm(np.diff(path, axis=0), axis=1).sum())

    if around is None:
        P, closed = max(chains, key=lambda c: length(*c))
    else:
        q = np.asarray(around, float) / MM - o
        pt = np.array([q @ u, q @ v])
        uvs = [np.stack([(P - o) @ u, (P - o) @ v], axis=1) for P, _ in chains]
        hits = [(abs(_loop_record(P, True, frame)["area_mm2"]), k) for k, (P, _) in enumerate(chains)
                if _inside(pt, uvs[k])]
        if not hits:
            k = min(range(len(chains)), key=lambda k: np.min(np.linalg.norm(uvs[k] - pt, axis=1)))
            d = float(np.min(np.linalg.norm(uvs[k] - pt, axis=1))) * MM
            c = chains[k][0].mean(axis=0) * MM
            raise LookupError(f"no section loop of {m.name} at {plane!r} encloses {list(around)}; the nearest "
                              f"({len(chains[k][0])} points, centred near {np.round(c, 1).tolist()}) is {d:.1f} mm away")
        k = min(hits)[1]
        P, closed = chains[k]
        if kind == "tape":
            return float(_hull_perimeter(uvs[k]) * MM)
    if kind == "tape":
        return float(_hull_perimeter(np.stack([(P - o) @ u, (P - o) @ v], axis=1)) * MM)
    return length(P, closed) * MM


# --------------------------------------------------------------------------- clearance, stature, bbox

def _tree(m):
    """A world-space BVH of a Mesh read, kept with the read: building one for the MPFB body costs most of a
    clearance (tens of ms), so several clearances against one read share it."""
    if "bvh" not in m.__dict__:
        from mathutils.bvhtree import BVHTree
        m.bvh = BVHTree.FromPolygons(m.co.tolist(), m.tris.tolist(), all_triangles=True)
    return m.bvh


def clearance(a, b, max_mm=50.0):
    """How a's vertices sit against b's surface: min_mm, the smallest signed gap (negative inside b, by the
    normal of the nearest face), inside (a's vertices inside b), max_depth_mm, within (vertices nearer than
    max_mm), checked (those in reach of b's box) and overlaps (intersecting face pairs, BVH overlap). Trees
    are built in world space from the evaluated meshes, so the objects' scales and poses count."""
    from mathutils import Vector
    ma, mb = evaluate(a, ("tris",)), evaluate(b, ("tris",))
    tree_b = _tree(mb)
    lim = max_mm / MM
    lo, hi = mb.co.min(axis=0) - lim, mb.co.max(axis=0) + lim
    cand = np.nonzero(np.all((ma.co >= lo) & (ma.co <= hi), axis=1))[0]
    gaps, where = [], []
    for i in cand.tolist():
        c = Vector(ma.co[i])
        loc, nrm, _, dist = tree_b.find_nearest(c, lim)
        if loc is None:
            continue
        gaps.append(dist if (c - loc).dot(nrm) >= 0.0 else -dist)
        where.append(i)
    out = {"min_mm": None, "inside": 0, "max_depth_mm": 0.0, "within": len(gaps), "checked": len(cand),
           "overlaps": len(_tree(ma).overlap(tree_b)), "nearest": None}
    if gaps:
        g = np.asarray(gaps)
        k = int(np.argmin(g))
        out.update(min_mm=float(g[k] * MM), inside=int(np.count_nonzero(g < 0)),
                   max_depth_mm=float(max(0.0, -g.min()) * MM), nearest=ma.co[where[k]] * MM)
    return out


def stature(ob, rest=True):
    """Height in mm (top to bottom of the evaluated mesh), with every armature that deforms it put in its
    rest position for the read when rest (the export scale of D7 is 1800 / rest stature)."""
    ob = obj(ob)
    rigs = {md.object for md in ob.modifiers if md.type == "ARMATURE" and md.object and md.show_viewport}
    if ob.parent is not None and ob.parent.type == "ARMATURE":
        rigs.add(ob.parent)
    saved = [(r.data, r.data.pose_position) for r in rigs] if rest else []
    try:
        for data, _ in saved:
            data.pose_position = "REST"
        z = evaluate(ob, ()).co[:, 2]
    finally:
        for data, pos in saved:
            data.pose_position = pos
    return float((z.max() - z.min()) * MM)


def bbox(ob):
    """World bounding box of the evaluated mesh of one object or several, mm: min, max, size, centre."""
    many = isinstance(ob, (list, tuple))
    co = np.vstack([evaluate(o, ()).co for o in (ob if many else [ob])])
    lo, hi = co.min(axis=0) * MM, co.max(axis=0) * MM
    return {"min": lo, "max": hi, "size": hi - lo, "centre": (lo + hi) / 2.0}


# --------------------------------------------------------------------------- silhouettes

def _raster_span(xy, tris, w, h):
    """Pixels whose centres lie in a triangle (closed edges), by row spans: each triangle is cut into the
    rows its y-range covers, each row's x-interval comes from the edges that straddle the row's centre
    line, and the intervals are summed into the image with one bincount and a cumulative sum."""
    A, B, C = xy[tris[:, 0]], xy[tris[:, 1]], xy[tris[:, 2]]
    ys = np.stack([A[:, 1], B[:, 1], C[:, 1]], axis=1)
    xs = np.stack([A[:, 0], B[:, 0], C[:, 0]], axis=1)
    j0 = np.maximum(np.ceil(ys.min(axis=1) - 0.5), 0.0)
    j1 = np.minimum(np.floor(ys.max(axis=1) - 0.5), h - 1.0)
    keep = (j1 >= j0) & (xs.max(axis=1) >= 0.5) & (xs.min(axis=1) <= w - 0.5) & np.isfinite(ys).all(axis=1)
    out = np.zeros((h, w), bool)
    if not keep.any():
        return out
    A, B, C, j0, j1 = A[keep], B[keep], C[keep], j0[keep].astype(np.int64), j1[keep].astype(np.int64)
    count = j1 - j0 + 1
    tri = np.repeat(np.arange(len(count)), count)
    rows = j0[tri] + (np.arange(int(count.sum())) - np.repeat(np.cumsum(count) - count, count))
    yc = rows + 0.5
    xl = np.full(len(rows), np.inf)
    xr = np.full(len(rows), -np.inf)
    for P, Q in ((A, B), (B, C), (C, A)):
        py, qy, px, qx = P[tri, 1], Q[tri, 1], P[tri, 0], Q[tri, 0]
        ok = (np.minimum(py, qy) <= yc) & (yc <= np.maximum(py, qy)) & (py != qy)
        with np.errstate(divide="ignore", invalid="ignore"):
            x = px + (yc - py) * (qx - px) / (qy - py)
        xl = np.where(ok, np.minimum(xl, x), xl)
        xr = np.where(ok, np.maximum(xr, x), xr)
    with np.errstate(invalid="ignore"):
        i0 = np.maximum(np.ceil(xl - 0.5), 0.0)
        i1 = np.minimum(np.floor(xr - 0.5), w - 1.0)
    good = np.isfinite(i0) & np.isfinite(i1) & (i1 >= i0)
    rows, i0, i1 = rows[good], i0[good].astype(np.int64), i1[good].astype(np.int64)
    W1 = w + 1
    diff = (np.bincount(rows * W1 + i0, minlength=h * W1)
            - np.bincount(rows * W1 + i1 + 1, minlength=h * W1)).reshape(h, W1)
    return np.cumsum(diff, axis=1)[:, :w] > 0


_LATTICE = {}


def _raster_splat(xy, tris, w, h, step=0.7, chunk=2_000_000):
    """The spec's splat: barycentric lattice samples of each triangle no further apart than step px, the
    pixel under each sample set, then a 3 x 3 closing to fill the cracks between samples."""
    P = xy[tris]
    keep = ((P[:, :, 0].max(axis=1) >= 0) & (P[:, :, 0].min(axis=1) < w) & (P[:, :, 1].max(axis=1) >= 0)
            & (P[:, :, 1].min(axis=1) < h) & np.isfinite(P).all(axis=(1, 2)))
    P = P[keep]
    out = np.zeros((h, w), bool)
    e1, e2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
    longest = np.maximum(np.maximum(np.linalg.norm(e1, axis=1), np.linalg.norm(e2, axis=1)),
                         np.linalg.norm(P[:, 2] - P[:, 1], axis=1))
    L = np.clip(np.ceil(longest / step), 1, 1024).astype(np.int64)
    for lv in np.unique(L):
        if lv not in _LATTICE:
            i, j = np.mgrid[0:lv + 1, 0:lv + 1]
            sel = (i + j) <= lv
            _LATTICE[lv] = np.stack([i[sel], j[sel]], axis=1) / float(lv)
        ab = _LATTICE[lv]
        idx = np.nonzero(L == lv)[0]
        per = max(1, chunk // len(ab))
        for k in range(0, len(idx), per):
            s = idx[k:k + per]
            S = P[s, 0][:, None, :] + ab[None, :, 0:1] * e1[s][:, None, :] + ab[None, :, 1:2] * e2[s][:, None, :]
            X, Y = np.floor(S[..., 0]).astype(np.int64), np.floor(S[..., 1]).astype(np.int64)
            ok = (X >= 0) & (X < w) & (Y >= 0) & (Y < h)
            out[Y[ok], X[ok]] = True
    sq = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
    return _erode(_dilate(out, sq), sq)


def silhouette(objs=None, preset="ref.full", scale=None, method="span", view=0):
    """The boolean mask (h, w) of the objects (default: what renders, objects()) seen through a preset's
    camera at its form-tier size; method "span" (pixel centres, the default) or "splat" (§4.8.4)."""
    if method not in ("span", "splat"):
        raise ValueError(f"silhouette method {method!r}: span or splat")
    cam = camera_for(preset, scale, view)
    p = None if isinstance(preset, camproj.Camera) else preset_of(preset)
    obs = objs if isinstance(objs, Mesh) or (isinstance(objs, (list, tuple)) and objs
                                             and all(isinstance(o, Mesh) for o in objs)) else objects(objs, p)
    XY, T, off = [], [], 0
    for o in [obs] if isinstance(obs, Mesh) else obs:
        m = evaluate(o, ("tris",))
        xy, d = cam.project(m.co, depth=True)
        tris = m.tris if cam.ortho else m.tris[(d[m.tris] > 1e-4).all(axis=1)]  # in front of the lens
        XY.append(xy)
        T.append(tris + off)
        off += len(xy)
    if not T:
        return np.zeros((cam.height, cam.width), bool)
    xy, tris = np.vstack(XY), np.vstack(T)
    return (_raster_span if method == "span" else _raster_splat)(xy, tris, cam.width, cam.height)


# --------------------------------------------------------------------------- masks, bands, IoU

def _disk(r):
    return [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1) if dy * dy + dx * dx <= r * r]


def _dilate(m, offsets):
    """Binary dilation by a set of offsets. The image is padded by repeating its border pixels, so where a
    crop cuts through the figure the cut is not taken for a silhouette edge."""
    r = max(max(abs(dy), abs(dx)) for dy, dx in offsets)
    h, w = m.shape
    P = np.pad(m, r, mode="edge")
    out = np.zeros_like(m)
    for dy, dx in offsets:
        out |= P[r + dy:r + dy + h, r + dx:r + dx + w]
    return out


def _erode(m, offsets):
    return ~_dilate(~m, offsets)


def edge_band(ref, r=3):
    """Pixels within r px (Euclidean) of the reference's boundary on either side: the don't-care band (none
    along the image's own border, which a crop can cut through the figure)."""
    ref = np.asarray(ref, bool)
    out = np.zeros_like(ref)
    if r <= 0 or not ref.any():
        return out
    rows, cols = np.nonzero(ref.any(axis=1))[0], np.nonzero(ref.any(axis=0))[0]
    y0, y1 = max(rows[0] - r - 1, 0), min(rows[-1] + r + 2, ref.shape[0])
    x0, x1 = max(cols[0] - r - 1, 0), min(cols[-1] + r + 2, ref.shape[1])
    sub, D = ref[y0:y1, x0:x1], _disk(r)
    out[y0:y1, x0:x1] = _dilate(sub, D) & ~_erode(sub, D)
    return out


def _polygon_mask(poly, shape):
    """Pixels whose centres lie inside a polygon (even-odd), poly in that image's continuous pixels."""
    h, w = shape
    poly = np.asarray(poly, float)
    out = np.zeros(shape, bool)
    x0, x1 = max(int(np.floor(poly[:, 0].min())), 0), min(int(np.ceil(poly[:, 0].max())), w)
    y0, y1 = max(int(np.floor(poly[:, 1].min())), 0), min(int(np.ceil(poly[:, 1].max())), h)
    if x1 <= x0 or y1 <= y0:
        return out
    X, Y = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
    inside = np.zeros(X.shape, bool)
    for (ax, ay), (bx, by) in zip(poly, np.roll(poly, -1, axis=0)):
        if ay == by:
            continue
        cross = (ay > Y) != (by > Y)
        inside ^= cross & (X < ax + (Y - ay) * (bx - ax) / (by - ay))
    out[y0:y1, x0:x1] = inside
    return out


def _json_file(path):
    """A JSON file, cached by modification time (None if it is missing)."""
    try:
        mt = os.path.getmtime(path)
    except OSError:
        return None
    hit = _FILES.get(path)
    if hit is None or hit[0] != mt:
        from . import cache
        hit = (mt, cache.read_json(path))
        _FILES[path] = hit
    return hit[1]


def declared_polygons(metric="iou"):
    """The declared differences (spec 18 §2.2, scripts/eval/declared_diffs.json) that apply to a metric:
    [(id, polygon in full-frame px)]. The file is a list of entries or {"diffs": [...]}; absent, none."""
    data = _json_file(DECLARED)
    entries = data.get("diffs", data.get("declared", [])) if isinstance(data, dict) else (data or [])
    out = []
    for e in entries:
        m = e.get("metric", metric)
        metrics = m if isinstance(m, list) else str(m).split("|")
        if metric in metrics and e.get("polygon_px"):
            out.append((e.get("id"), e["polygon_px"]))
    return out


def declared_mask(shape, box=None, scale=1.0, which=True):
    """The pixels of an image of `shape` (a box of the hero frame at a scale) that the declared differences
    cover, and their ids. which: True for the register, or a list of full-frame polygons."""
    box = box or (0, 0, camproj.W, camproj.H)
    polys = declared_polygons() if which is True else [(None, p) for p in (which or [])]
    out, ids = np.zeros(shape, bool), []
    for pid, poly in polys:
        q = (np.asarray(poly, float) - np.asarray(box[:2], float)) * scale
        out |= _polygon_mask(q, shape)
        ids.append(pid)
    return out, ids


def _cut(full, box, s):
    """A full-frame mask cut to a box at a scale, sampled at the output pixel centres (nearest)."""
    x0, y0, x1, y1 = box
    w, h = camproj.box_size(box, s)
    xs = np.clip(np.floor(x0 + (np.arange(w) + 0.5) / s).astype(np.int64), 0, full.shape[1] - 1)
    ys = np.clip(np.floor(y0 + (np.arange(h) + 0.5) / s).astype(np.int64), 0, full.shape[0] - 1)
    return full[np.ix_(ys, xs)]


def read_mask(path):
    """A mask PNG as a boolean array (the first channel above half: 255 inside, threshold 127)."""
    a = _io("grade").read_png(path)
    return (a[..., 0] if a.ndim == 3 else a) > 0.5


class Reference:
    """A preset's reference silhouette at its render size, with the pixels the IoU leaves out precomputed:
    the ±band px edge band and the declared-difference polygons (spec 18 §2.1-2.2)."""

    def __init__(self, mask, care, info):
        self.mask, self.care, self.info = mask, care, info


def reference(preset, scale=None, band=3, declared=True):
    """The Reference for a hero-frame preset from the masks it names (ref/masks/<name>.png, else
    cache/masks/, their union), or None when it names none or none is on disk. Cached per files and args."""
    p = preset_of(preset)
    if p["camera"]["type"] != "hero" or not p.get("mask"):
        return None
    box = tuple(p["render"].get("border_px") or (0, 0, camproj.W, camproj.H))
    s = p["render"].get("scale", 1) if scale is None else scale
    paths = [next((os.path.join(d, n + ".png") for d in MASK_DIRS if os.path.isfile(os.path.join(d, n + ".png"))), None)
             for n in p["mask"]]
    paths = [q for q in paths if q]
    if not paths:
        return None
    stamp = tuple((q, os.path.getmtime(q)) for q in paths)
    dec = os.path.getmtime(DECLARED) if declared and os.path.isfile(DECLARED) else None
    key = (stamp, box, s, band, bool(declared), dec)
    hit = _REFERENCES.get(key)
    if hit is None:
        full = None
        for q in paths:
            m = read_mask(q)
            if m.shape != (camproj.H, camproj.W):
                raise ValueError(f"{q} is {m.shape[1]} x {m.shape[0]}; reference masks are full frames")
            full = m if full is None else full | m
        mask = _cut(full, box, s)
        bandm = edge_band(mask, band) if band else np.zeros_like(mask)
        decm, ids = declared_mask(mask.shape, box, s) if declared else (np.zeros_like(mask), [])
        info = {"masks": [os.path.relpath(q, env.PROJECT_DIR).replace(os.sep, "/") for q in paths],
                "box": list(box), "scale": s, "band": band, "band_px": int(bandm.sum()), "declared": ids,
                "declared_px": int(decm.sum()), "ref_px": int(mask.sum())}
        hit = Reference(mask, ~(bandm | decm), info)
        _REFERENCES[key] = hit
    return hit


def iou(mask, ref, band=3, declared=True, frame=None):
    """IoU of a mask against a reference outside the ±band px edge band and the declared differences, with
    precision (the mask's pixels that are right) and recall (the reference's pixels found). ref is a
    Reference (its band and declarations already set) or an array; for an array, frame = (box, scale) of
    the hero frame places the declared polygons (a full-frame array needs none)."""
    mask = np.asarray(mask, bool)
    if isinstance(ref, Reference):
        r, care, extra = ref.mask, ref.care, dict(ref.info)
    else:
        r = np.asarray(ref, bool)
        care, extra = np.ones_like(r), {"band": band}
        if band:
            b = edge_band(r, band)
            care &= ~b
            extra["band_px"] = int(b.sum())
        if declared:
            if frame is None and r.shape == (camproj.H, camproj.W):
                frame = ((0, 0, camproj.W, camproj.H), 1.0)
            if frame is not None:
                d, ids = declared_mask(r.shape, frame[0], frame[1], declared)
                care &= ~d
                extra.update(declared=ids, declared_px=int(d.sum()))
    if mask.shape != r.shape:
        raise ValueError(f"mask {mask.shape} and reference {r.shape} differ in size")
    m, rr = mask & care, r & care
    tp = int(np.count_nonzero(m & rr))
    fp, fn = int(np.count_nonzero(m)) - tp, int(np.count_nonzero(rr)) - tp
    out = {"iou": tp / (tp + fp + fn) if tp + fp + fn else 1.0, "precision": tp / (tp + fp) if tp + fp else 1.0,
           "recall": tp / (tp + fn) if tp + fn else 1.0, "tp": tp, "fp": fp, "fn": fn,
           "care_px": int(np.count_nonzero(care))}
    out.update({k: v for k, v in extra.items() if k in ("band", "band_px", "declared", "declared_px")})
    return out


def diff_image(mask, ref):
    """The p18.V2 silhouette map as RGB uint8: true positive grey, false positive red, false negative cyan,
    the edge band yellow, declared differences hatched magenta."""
    r = ref.mask if isinstance(ref, Reference) else np.asarray(ref, bool)
    care = ref.care if isinstance(ref, Reference) else np.ones_like(r)
    mask = np.asarray(mask, bool)
    out = np.zeros(r.shape + (3,), np.uint8)
    out[mask & r] = (128, 128, 128)
    out[mask & ~r] = (230, 40, 40)
    out[~mask & r] = (0, 220, 230)
    if isinstance(ref, Reference):
        band = edge_band(r, ref.info.get("band") or 0) if ref.info.get("band") else np.zeros_like(r)
        out[band & (mask | r)] = (230, 210, 0)
        dec = ~care & ~band
        yy, xx = np.indices(r.shape)
        out[dec & ((xx + yy) % 6 < 2)] = (220, 0, 220)
    return out


def silhouette_report(preset="ref.full", objects=None, method="span", scale=None, out=None, diff=None,
                      band=3, declared=True, view=0):
    """The server's silhouette command: the mask (timed), its pixel count and, when the preset names a
    reference mask that is on disk, the IoU against it; out writes the mask PNG and diff the V2 map."""
    grade = _io("grade")
    t = time.perf_counter()
    mask = silhouette(objects, preset, scale, method, view)
    ms = (time.perf_counter() - t) * 1e3
    p = preset_of(preset)
    res = {"preset": p["id"], "method": method, "size": [mask.shape[1], mask.shape[0]], "px": int(mask.sum()),
           "ms": round(ms, 2), "iou": None}
    ref = reference(p, scale, band, declared)
    if ref is not None:
        t = time.perf_counter()
        res["iou"] = iou(mask, ref)
        res["iou_ms"] = round((time.perf_counter() - t) * 1e3, 2)
        res["reference"] = ref.info
    else:
        res["reference"] = f"no reference mask for {p['id']} (it names {p.get('mask') or 'none'}; looked in ref/masks, cache/masks)"
    for key, path, img in (("out", out, lambda: (mask * 255).astype(np.uint8)),
                           ("diff", diff, lambda: diff_image(mask, ref))):
        if path and (key == "out" or ref is not None):
            full = path if os.path.isabs(path) else env.path(path)
            grade.write_png(full, img())
            res[key] = os.path.relpath(full, env.PROJECT_DIR).replace(os.sep, "/")
    return res


# --------------------------------------------------------------------------- envelope, dispatch, objectives

def envelope(metric, value, target=None, tol=None, unit="mm", source="", part=None):
    """One item of a part's measure() report in the §4.8.4 envelope {part, metric, value, target, tol, unit,
    pass, source}: cli.metric, here so a part imports one module for its measurements."""
    from . import cli
    return cli.metric(metric, value, target, tol, unit, source, part)


def call(fn, args=None, cache=None):
    """A primitive by name with JSON arguments (objects by name), the server's measure command and the term
    objectives' way in; the result is JSON-safe. cache maps object names to the reads that the calls of one
    evaluation share."""
    if fn not in PRIMITIVES:
        raise KeyError(f"no measurement {fn!r}; the primitives are {', '.join(PRIMITIVES)}")
    a = dict(args or {})
    if fn == "silhouette":
        if cache is not None and a.get("objects") is not None:
            a["objects"] = [_read(o, cache) for o in objects(a["objects"])]
        return log.jsonable(silhouette_report(**a))
    if fn == "stature":  # reads its own rest pose, never a cached posed read
        return stature(**a)
    for k in ("ob", "a", "b"):
        if k in a:
            a[k] = [_read(o, cache) for o in a[k]] if isinstance(a[k], list) else _read(a[k], cache)
    return log.jsonable(globals()[fn](**a))


def pick(value, path):
    """A dotted path into a result: "iou.iou", "max.2", a landmark's name ("nose" or "nose.1")."""
    for part in str(path).split(".") if path not in (None, "") else []:
        if isinstance(value, dict):
            value = value[part]
        else:
            value = value[int(part)]
    return value


def _flat(value, like=None):
    """A value as a flat float vector, a dict in the order of `like`'s keys (the target's)."""
    if isinstance(value, dict):
        keys = list(like) if isinstance(like, dict) else sorted(value)
        return np.concatenate([_flat(value[k], like[k] if isinstance(like, dict) else None) for k in keys])
    return np.asarray(value, float).reshape(-1)


def _part_objective(pid, name):
    path = env.path("scripts", "parts", f"p{str(pid).zfill(2)}", "objectives.py")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"part {pid} registers no objectives (no {os.path.relpath(path, env.PROJECT_DIR)})")
    key = ("objectives", path, os.path.getmtime(path))
    mod = _FILES.get(key)
    if mod is None:
        spec = importlib.util.spec_from_file_location(f"objectives_p{str(pid).zfill(2)}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _FILES[key] = mod
    fn = getattr(mod, name, None)
    if not callable(fn):
        raise KeyError(f"{os.path.relpath(path, env.PROJECT_DIR)} has no objective {name!r}")
    return fn


class Objective:
    """f = Σ weight · ((value − target) / tol)² over measurement terms (§4.8.5), on the session as it stands.

    A term is {"fn", "args", "metric", "target" | "min" | "max", "tol", "weight", "name"}: a primitive of
    call(), metric a dotted path into its result (pick()), and a target shaped like the value (a number, a
    list, a dict of landmarks); "min" and "max" make a one-sided term that costs nothing inside, e.g. a
    clearance of at least 1 mm. Or {"part": "06", "name": "jaw"}: the callable of that name in
    scripts/parts/p06/objectives.py, returning f, (f, values) or {"f", "values", "residuals"}. Terms share
    one mesh read per object per evaluation. Calling the objective returns {"f", "residuals", "values"};
    the residuals (weighted, divided by tol) are what Levenberg–Marquardt fits."""

    def __init__(self, terms):
        terms = terms.get("terms", [terms]) if isinstance(terms, dict) else list(terms)
        self.terms = []
        for i, t in enumerate(terms):
            t = dict(t)
            if "part" in t:
                t["_fn"] = _part_objective(t["part"], t["name"])
                t.setdefault("label", f"p{t['part']}.{t['name']}")
            else:
                if t.get("fn") not in PRIMITIVES:
                    raise ValueError(f"objective term {i}: fn {t.get('fn')!r} is not one of {PRIMITIVES}")
                if not any(k in t for k in ("target", "min", "max")):
                    raise ValueError(f"objective term {i} ({t['fn']}): give a target, min or max")
                t.setdefault("label", t.get("name") or f"{t['fn']}{i}")
            self.terms.append(t)

    def __call__(self):
        cache, values, res = {}, {}, []
        for t in self.terms:
            if "_fn" in t:
                out = t["_fn"]()
                if isinstance(out, dict):
                    f, vals, r = out["f"], out.get("values"), out.get("residuals")
                elif isinstance(out, tuple):
                    (f, vals), r = out, None
                else:
                    f, vals, r = out, None, None
                values[t["label"]] = vals if vals is not None else f
                res.append(np.asarray(r if r is not None else [math.sqrt(max(float(f), 0.0))], float))
                continue
            v = pick(call(t["fn"], t.get("args"), cache), t.get("metric"))
            values[t["label"]] = v
            tol, wgt = float(t.get("tol", 1.0)), float(t.get("weight", 1.0))
            if "target" in t:
                r = _flat(v, t["target"]) - _flat(t["target"], t["target"])
            else:
                x = _flat(v)
                r = np.zeros_like(x)
                if "min" in t:
                    r = np.minimum(x - float(t["min"]), 0.0)
                if "max" in t:
                    r = r + np.maximum(x - float(t["max"]), 0.0)
            res.append(r / tol * math.sqrt(wgt))
        r = np.concatenate(res) if res else np.zeros(0)
        return {"f": float(r @ r), "residuals": r, "values": log.jsonable(values)}


# --------------------------------------------------------------------------- self-test

# The cloud's "MPFB default male" (spec 18 §3.2: renders/research/mpfb_default.blend, built by
# scripts/research/mpfb_build_default.py): male, 32 years (age 0.553846), muscle 0.7, weight 0.5,
# proportions 0.5, cupsize and firmness 0.5, caucasian 1, then the height slider fitted to 1.85 m by two
# samples and a straight line (it lands on 0.576019 and 1828.4 mm, the slider not being linear) and the
# feet grounded. Its quoted girths: thigh 485 mm at z 700 and calf 361 mm at z 350, his left.
CLOUD_MACROS = {"gender": 1.0, "age": 0.5 + 0.5 * 7.0 / 65.0, "muscle": 0.7, "weight": 0.5, "proportions": 0.5,
                "height": 0.5, "cupsize": 0.5, "firmness": 0.5,
                "race": {"caucasian": 1.0, "asian": 0.0, "african": 0.0}}
CLOUD_GIRTHS = {"thigh_L_z700": (485.0, 700.0, (130.0, -38.0)), "calf_L_z350": (361.0, 350.0, (182.0, 1.0))}


def mpfb_human(name, macros=None, fit_height=1.85):
    """An MPFB human named `name` with the given macros and the cloud's height fit (None: MPFB is not
    installed in this session, e.g. a --factory-startup server). For self-tests; the caller removes it."""
    import bpy
    mod = "bl_ext.user_default.mpfb"
    try:
        if mod not in bpy.context.preferences.addons:
            bpy.ops.preferences.addon_enable(module=mod)
        from bl_ext.user_default.mpfb.entities.objectproperties import HumanObjectProperties
        from bl_ext.user_default.mpfb.services.humanservice import HumanService
        from bl_ext.user_default.mpfb.services.targetservice import TargetService
    except Exception:
        return None
    macro = TargetService.get_default_macro_info_dict()
    macro.update(copy.deepcopy(macros or CLOUD_MACROS))
    h = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                  feet_on_ground=True, scale=0.1, macro_detail_dict=macro)
    h.name = name
    if fit_height:
        def height():
            z = evaluate(h, ()).co[:, 2]
            return z.max() - z.min()
        h0 = height()
        HumanObjectProperties.set_value("height", 0.9, entity_reference=h)
        TargetService.reapply_macro_details(h)
        h1 = height()
        hm = max(0.0, min(1.0, 0.5 + (fit_height - h0) * 0.4 / (h1 - h0)))
        HumanObjectProperties.set_value("height", hm, entity_reference=h)
        TargetService.reapply_macro_details(h)
    h.location.z -= evaluate(h, ()).co[:, 2].min()
    bpy.context.view_layer.update()
    return h


def _remove(*things):
    import bpy
    from . import replace
    doomed = []
    for x in things:
        if x is not None and x.name in bpy.data.objects:
            doomed += [x] + list(x.children_recursive)
    if doomed:
        bpy.data.batch_remove(doomed)
    replace.purge()


def _test_mesh(name, verts, faces):
    import bpy
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _cylinder(name, r=0.05, segments=64, z0=0.0, z1=0.2, x=0.0):
    a = np.arange(segments) * 2.0 * math.pi / segments
    ring = np.stack([x + r * np.cos(a), r * np.sin(a), np.zeros(segments)], axis=1)
    verts = np.vstack([ring + [0, 0, z0], ring + [0, 0, z1]])
    faces = [(i, (i + 1) % segments, segments + (i + 1) % segments, segments + i) for i in range(segments)]
    faces += [tuple(range(segments - 1, -1, -1)), tuple(range(segments, 2 * segments))]
    return _test_mesh(name, verts, faces)


def _box(name, centre, size):
    c, s = np.asarray(centre, float), np.asarray(size, float) / 2.0
    verts = [c + s * np.array([x, y, z]) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return _test_mesh(name, verts, faces)


class _SceneKept:
    """Put back a scene's camera, render, display and visibility settings after a self-test render, and
    remove the camera objects the harness made if the scene had none before."""

    RENDER = ("engine", "resolution_x", "resolution_y", "resolution_percentage", "use_border",
              "use_crop_to_border", "film_transparent", "filepath")
    SHADING = ("light", "studio_light", "color_type", "single_color", "show_cavity", "cavity_type",
               "cavity_ridge_factor", "cavity_valley_factor", "curvature_ridge_factor", "curvature_valley_factor",
               "show_shadows", "show_object_outline", "show_xray", "use_dof", "show_backface_culling")

    def __init__(self, scene, keep_visible):
        import bpy
        self.scene, self.bpy = scene, bpy
        self.saved = [(scene.render, k, getattr(scene.render, k)) for k in self.RENDER]
        self.saved += [(scene.display.shading, k, getattr(scene.display.shading, k)) for k in self.SHADING]
        self.saved += [(scene.display, "render_aa", scene.display.render_aa), (scene, "camera", scene.camera)]
        self.saved += [(scene.view_settings, k, getattr(scene.view_settings, k)) for k in ("view_transform", "look")]
        self.objs = set(bpy.data.objects.keys())
        self.colls = set(bpy.data.collections.keys())
        self.cams = set(bpy.data.cameras.keys())
        self.hidden = [o for o in scene.objects if o not in keep_visible and not o.hide_render]
        for o in self.hidden:
            o.hide_render = True

    def restore(self):
        bpy = self.bpy
        for owner, k, v in self.saved:
            try:
                setattr(owner, k, v)
            except (AttributeError, TypeError, ValueError):
                pass
        for o in self.hidden:
            o.hide_render = False
        new = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - self.objs]
        bpy.data.batch_remove(new + [bpy.data.collections[n] for n in set(bpy.data.collections.keys()) - self.colls]
                              + [bpy.data.cameras[n] for n in set(bpy.data.cameras.keys()) - self.cams])


def selftest():
    """§1.4 item 6 and §8.4 items 3-4: the 64-gon girth, IoU of a mask with itself, the cloud's girths on a
    real MPFB human, landmarks through its mask, clearance, and the silhouette against Workbench alpha."""
    import bpy
    grade, render = _io("grade"), _io("render")
    R, made = {}, []
    scratch = env.path("cache", "selftest", "measure")
    os.makedirs(scratch, exist_ok=True)
    try:
        # a 64-segment cylinder of radius 50 mm: the section is a regular 64-gon of circumradius 50 mm,
        # perimeter 6400 sin(π/64) = 314.033 mm (spec 18 §1.4 item 6 quotes 313.9 ± 0.1, which is no
        # polygon's perimeter here: 2π r is 314.159 and the inscribed 64-gon 314.033)
        cyl = _cylinder("SelftestM.Cylinder")
        made.append(cyl)
        want = 6400.0 * math.sin(math.pi / 64.0)
        t = time.perf_counter()
        tape = girth(cyl, 100.0)
        R["cylinder_tape_ms"] = round((time.perf_counter() - t) * 1e3, 3)
        loop = girth(cyl, 100.0, around=(0, 0, 100), kind="loop")
        R["cylinder64_girth_mm"] = {"tape": round(tape, 4), "loop": round(loop, 4), "exact": round(want, 4)}
        assert abs(tape - want) < 0.01 and abs(loop - want) < 0.01, R["cylinder64_girth_mm"]
        sec = section(cyl, {"point": (0, 0, 100), "normal": (0.0, 0.5, 1.0)})  # a tilted cut: an ellipse
        assert len(sec) == 1 and sec[0]["closed"] and sec[0]["loop_mm"] > want
        try:
            girth(cyl, 100.0, around=(200, 0, 100))
            raise AssertionError("a point outside every loop was measured")
        except LookupError:
            pass

        # IoU: a mask with itself is 1; a 3 px shift costs what spec 18 §2.1 says, and the band hides it
        yy, xx = np.indices((300, 200))
        disk = (xx - 100.0) ** 2 + (yy - 150.0) ** 2 < 80.0 ** 2
        same = iou(disk, disk)
        assert same["iou"] == 1.0 and same["precision"] == 1.0 and same["recall"] == 1.0
        shifted = np.roll(disk, 3, axis=1)
        R["iou_disk_shift3"] = {"no_band": round(iou(shifted, disk, band=0)["iou"], 4),
                                "band3": round(iou(shifted, disk, band=3)["iou"], 4)}
        assert R["iou_disk_shift3"]["band3"] > 0.999 > R["iou_disk_shift3"]["no_band"]
        poly = [[50, 50], [150, 50], [150, 100], [50, 100]]
        dm, _ = declared_mask(disk.shape, (0, 0, 200, 300), 1.0, which=[poly])
        assert dm.sum() == 100 * 50
        half = np.zeros((60, 80), bool)  # a figure cut by the image border: no band along the border
        half[:, :40] = True
        b = edge_band(half, 3)
        assert b[:, 37:43].all() and b.sum() == 60 * 6, b.sum()

        # clearance: a 100 mm cube 20 mm from a taller, wider box, then pushed 20 mm into it
        a = _box("SelftestM.BoxA", (0, 0, 0.5), (0.1, 0.1, 0.1))
        b = _box("SelftestM.BoxB", (0.12, 0, 0.5), (0.1, 0.2, 0.2))
        made += [a, b]
        t = time.perf_counter()
        c = clearance(a, b, max_mm=50)
        R["clearance_ms_cubes"] = round((time.perf_counter() - t) * 1e3, 2)
        assert abs(c["min_mm"] - 20.0) < 1e-3 and c["inside"] == 0 and c["overlaps"] == 0, c
        b.location.x = -0.04
        bpy.context.view_layer.update()
        c = clearance(a, b, max_mm=50)
        assert c["inside"] == 4 and abs(c["max_depth_mm"] - 20.0) < 1e-3 and c["overlaps"] > 0, c

        human = mpfb_human("SelftestM.Human")
        if human is None:
            R["mpfb"] = "MPFB is not enabled in this session: the human tests were skipped"
            return R
        made.append(human)
        from bl_ext.user_default.mpfb.entities.objectproperties import HumanObjectProperties
        R["mpfb_macros"] = dict(CLOUD_MACROS, height=round(HumanObjectProperties.get_value("height", entity_reference=human), 6))
        R["stature_mm"] = round(stature(human), 1)
        assert abs(R["stature_mm"] - 1828.4) < 0.5, R["stature_mm"]

        # the cloud's girths: thigh at z 700 and calf at z 350, his left (+X), tape
        m = evaluate(human)
        got = {k: girth(m, z, around=(x, y, z)) for k, (_, z, (x, y)) in CLOUD_GIRTHS.items()}
        t = time.perf_counter()  # warm: the edge table is built once per topology
        for f in np.linspace(0.0, 1.0, 20):  # up his left leg, from the calf to the thigh slice
            girth(m, 350.0 + 350.0 * f, around=(182.0 - 52.0 * f, 1.0 - 39.0 * f, 350.0 + 350.0 * f))
        R["girth_ms_per_slice"] = round((time.perf_counter() - t) * 1e3 / 20, 3)
        R["girths_mm"] = {k: {"here": round(v, 1), "cloud": CLOUD_GIRTHS[k][0]} for k, v in got.items()}
        for k, v in got.items():
            assert abs(v - CLOUD_GIRTHS[k][0]) < 1.0, R["girths_mm"]
        # the same as the cloud probe's method: every edge crossing at z, his left side, hull of the points
        E = np.unique(np.sort(np.stack([m.loop_vert, m.loop_vert[_ring(m)[0]]], 1), axis=1), axis=0)
        for k, (_, z, _) in CLOUD_GIRTHS.items():
            s = m.co[:, 2] - z / MM
            e = E[(s[E[:, 0]] * s[E[:, 1]]) < 0]
            q = m.co[e[:, 0]] + (m.co[e[:, 1]] - m.co[e[:, 0]]) * (s[e[:, 0]] / (s[e[:, 0]] - s[e[:, 1]]))[:, None]
            q = q[q[:, 0] > 0]
            assert abs(_hull_perimeter(q[:, :2]) * MM - got[k]) < 1e-6, k
        t = time.perf_counter()
        evaluate(human)
        R["evaluate_ms"] = round((time.perf_counter() - t) * 1e3, 2)

        # landmarks through the Hide helpers mask: the mapped positions equal the unmasked evaluation's
        n_orig = len(human.data.vertices)
        keep = original_index(human, len(m.co))
        R["vertices"] = {"own": n_orig, "evaluated": len(m.co), "triangles": len(m.tris)}
        hide = [md for md in human.modifiers if md.type == "MASK"]
        for md in hide:
            md.show_viewport = False
        try:
            full = evaluate(human, ())
        finally:
            for md in hide:
                md.show_viewport = True
        assert np.array_equal(full.co[keep], m.co), "the mask's index map is wrong"
        idx = keep[np.linspace(0, len(keep) - 1, 200).astype(int)]
        t = time.perf_counter()
        lm = landmarks(human, idx.tolist())
        R["landmarks_200_ms"] = round((time.perf_counter() - t) * 1e3, 2)
        assert np.allclose(lm, full.co[idx] * MM, atol=1e-9)
        masked = int(np.setdiff1d(np.arange(n_orig), keep)[0])
        try:
            landmarks(human, {"helper": masked})
            raise AssertionError("a masked vertex was measured")
        except ValueError:
            pass
        g = landmarks(human, {"body": {"group": "body"}})["body"]
        assert np.all(np.isfinite(g))
        # a parameter change, then the 200 landmarks through the depsgraph (§1.4 item 5: ≤ 20 ms)
        from . import params
        key = f"key:{human.name}:{human.data.shape_keys.key_blocks[1].name}"
        v0, times = params.read([key])[key], []
        for i in range(12):
            params.write({key: v0 + 0.01 * (1 + i % 2)})
            t = time.perf_counter()
            landmarks(human, idx.tolist())
            times.append((time.perf_counter() - t) * 1e3)
        params.write({key: v0})
        R["set_key_then_landmarks_200_ms"] = round(float(np.median(times)), 2)

        # clearance against the body: a 60 mm box 20 mm in front of his left thigh at z 700 (the section's
        # front is at y −119.7), both ways round
        box = _box("SelftestM.ThighBox", (0.13, -0.1697, 0.70), (0.06, 0.06, 0.06))
        made.append(box)
        t = time.perf_counter()
        c1 = clearance(box, human, max_mm=50)
        t1 = (time.perf_counter() - t) * 1e3
        t = time.perf_counter()
        c2 = clearance(human, box, max_mm=50)
        t2 = (time.perf_counter() - t) * 1e3
        R["clearance_body"] = {"box_to_body_mm": round(c1["min_mm"], 2), "body_to_box_mm": round(c2["min_mm"], 2),
                               "ms_box_to_body": round(t1, 1), "ms_body_to_box": round(t2, 1),
                               "body_vertices_checked": c2["checked"]}
        assert 0.0 < c2["min_mm"] <= 20.5 and c1["inside"] == c2["inside"] == 0 and c2["overlaps"] == 0, R["clearance_body"]

        # the envelope a part's measure() returns
        e = envelope("thigh_L_z700", got["thigh_L_z700"], 485.0, 1.0, source="spec 18 §3.2", part="18")
        assert e["pass"] and set(e) == {"part", "metric", "value", "target", "tol", "unit", "pass", "source"}, e
        # projection through a crop preset is camproj's hero projection cut to the box
        P = landmarks(human, idx[:5].tolist())
        box_px, s5 = preset_of("ref.head_face")["render"]["border_px"], preset_of("ref.head_face")["render"]["scale"]
        assert np.allclose(project(P, "ref.head_face"), camproj.to_crop(camproj.HERO.project(P / MM), box_px, s5))

        # an objective over the cloud girths: zero cost at the measured values
        obj_ = Objective([{"fn": "girth", "args": {"ob": human.name, "plane": z, "around": [x, y, z]},
                           "target": got[k], "tol": 1.0, "name": k} for k, (_, z, (x, y)) in CLOUD_GIRTHS.items()]
                         + [{"fn": "bbox", "args": {"ob": human.name}, "metric": "min.2", "min": -0.5, "max": 0.5}])
        res = obj_()
        assert res["f"] < 1e-12 and len(res["residuals"]) == 3, res

        # silhouette against Workbench alpha through the same presets (spec 18 §8.4 item 4)
        p1 = copy.deepcopy(preset_of("ref.soldier_full"))
        p1["render"]["scale"] = 1  # p18.V2's ×1 framing, 440 x 915
        scene = render.pick_scene(p1, "form")[0]
        if human.name not in scene.objects:
            scene.collection.objects.link(human)
        kept = _SceneKept(scene, {human})
        sil = {}
        try:
            for label, p, aas in (("soldier_x1", p1, ("8", "OFF")), ("head_x5", preset_of("ref.head_face"), ("8",))):
                cam = camera_for(p)
                t = time.perf_counter()
                xy = cam.project(m.co)
                proj_ms = (time.perf_counter() - t) * 1e3
                masks, times = {}, {}
                for meth in ("span", "splat"):
                    t = time.perf_counter()
                    masks[meth] = silhouette([m], p, method=meth)
                    times[meth] = round((time.perf_counter() - t) * 1e3, 1)
                row = {"size": [cam.width, cam.height], "project_ms": round(proj_ms, 3), "silhouette_ms": times}
                for aa in aas:
                    side = render.render_preset(p, tier="form", out_dir=scratch, stem=f"{label}_aa{aa}", aa=aa)
                    alpha = grade.read_png(env.path(side["outputs"]["png"]))[..., 3] > 0.5
                    for meth, mk in masks.items():
                        t = time.perf_counter()
                        v = iou(mk, alpha, band=0, declared=False)
                        row[f"iou_{meth}_vs_aa{aa}"] = round(v["iou"], 5)
                        row["iou_ms"] = round((time.perf_counter() - t) * 1e3, 2)
                    row[f"render_s_aa{aa}"] = side["seconds"]
                    if aa == "8":
                        grade.write_png(os.path.join(scratch, f"{label}_diff.png"), diff_image(masks["span"], alpha))
                sil[label] = row
        finally:
            kept.restore()
        R["silhouette"] = sil
        for label, row in sil.items():
            assert row["iou_span_vs_aa8"] >= 0.98, (label, row)

        # a reference mask from disk through a preset: the human's own full-frame silhouette written as a
        # scratch mask, cut to the soldier box at ×2 (its pixels doubled) and compared with the ×2 mask:
        # inside the ±3 px band they agree
        name = "selftest_measure"
        mask_png = os.path.join(MASK_DIRS[1], name + ".png")
        grade.write_png(mask_png, (silhouette([m], "ref.full") * 255).astype(np.uint8))
        try:
            p2 = copy.deepcopy(preset_of("ref.soldier_full"))
            p2["mask"] = [name]
            t = time.perf_counter()
            ref = reference(p2)
            ref_ms = (time.perf_counter() - t) * 1e3
            rep = silhouette_report(p2, [m], out="cache/selftest/measure/sil_x2.png", diff="cache/selftest/measure/sil_x2_diff.png")
            again = reference(p2)
            R["reference_x2"] = {"build_ms": round(ref_ms, 1), "ref_px": ref.info["ref_px"], "band_px": ref.info["band_px"],
                                 "iou": round(rep["iou"]["iou"], 5), "iou_ms": rep["iou_ms"], "silhouette_ms": rep["ms"],
                                 "iou_no_band": round(iou(silhouette([m], p2), ref.mask, band=0)["iou"], 5)}
            assert again is ref and rep["iou"]["iou"] > 0.999 and ref.mask.shape == (1830, 880), R["reference_x2"]
            assert iou(ref.mask, ref)["iou"] == 1.0  # §8.4 item 3: the reference with itself
        finally:
            os.remove(mask_png)
            forget()
        return R
    finally:
        _remove(*made)
