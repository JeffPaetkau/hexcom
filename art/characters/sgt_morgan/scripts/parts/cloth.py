"""Cloth helpers for the garments (round 9): a cut built as an implicit surface (a field of signed distances in
millimetres, meshed by surface nets), and Blender's cloth solver run headless on the rest body, with the result
cached by a hash of its inputs. Notes: scripts/parts/trousers.md section 8, shirt.md section 11.

    import cloth as K
    V, F = K.surface_nets(field, origin_mm, cell_mm)          # quads on the zero level of field (< 0 inside)
    d = K.convex_sd(P2, H)                                     # signed distance of 2-D points to a convex polygon
    Vs = K.simulate("trousers", V, F, colliders=[(Vb, Fb)], pin=w, move=D, frames=60, cloth=dict(...))

simulate() builds a temporary mesh object (metres), gives it a Cloth modifier (pins: a vertex group used as the
goal group, weight 1 = held), colliders as separate objects with a Collision modifier, steps the frames in order and
reads the last one. move: a displacement of the held vertices, applied by an animated shape key over move_frames
(held vertices follow the mesh under the cloth), so cloth built longer than its final span is pushed together and
buckles under gravity and self-collision: the hem's blousing pushed up onto the boot, a sleeve's cuff pushed up the
forearm into folds at the crook (with weak goals sliding along the sleeve). Cloth's rest_shape_key, tried first,
changed nothing in Blender 4.5 headless (the same solve with and without it gave identical vertices). The result is
stored in cache/cloth/<name>_<hash>.npz (the hash covers every input and setting), so a rebuild with
nothing changed skips the solve. Everything is in mm at the interface, metres inside Blender.
"""
import hashlib
import json
import os
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
CLOTH_CACHE = os.path.join(PROJECT, "cache", "cloth")
MM = 0.001

# NYCO 50/50 ripstop (a G3 class shell): stiffer in bending than a cotton jersey, light, little stretch.
RIPSTOP = {"quality": 8, "mass": 0.12, "air_damping": 1.5, "tension": 40.0, "compression": 40.0, "shear": 12.0,
           "bending": 2.5, "tension_damping": 6.0, "compression_damping": 6.0, "shear_damping": 6.0,
           "bending_damping": 0.6, "distance": 2.5, "self_distance": 2.0, "self_collision": True,
           "collision_quality": 3, "friction": 6.0, "pin_stiffness": 2.0, "gravity": 1.0}


def say(*a):
    print("[cloth]", *a, flush=True)


# --------------------------------------------------------------------------- implicit cut

def convex_sd(P, H):
    """Signed distance (mm) of 2-D points P (n, 2) to the convex polygon H (m, 2, counter-clockwise): negative
    inside."""
    P = np.asarray(P, float)
    A = np.asarray(H, float)
    B = np.roll(A, -1, 0)
    E = B - A
    L2 = np.maximum((E ** 2).sum(1), 1e-12)
    W = P[:, None, :] - A[None, :, :]
    t = np.clip((W * E[None]).sum(2) / L2[None], 0.0, 1.0)
    D = W - t[..., None] * E[None]
    d = np.sqrt((D ** 2).sum(2)).min(1)
    cross = E[None, :, 0] * W[..., 1] - E[None, :, 1] * W[..., 0]
    inside = (cross >= 0).all(1)
    return np.where(inside, -d, d)


def smin(a, b, k):
    """Polynomial smooth minimum: min(a, b) rounded over a width k (k = 0: the plain minimum). k may be an array."""
    k = np.maximum(np.asarray(k, float), 1e-9)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def surface_nets(f, origin, h):
    """Naive surface nets on a sampled field f (nx, ny, nz), negative inside, grid point (i, j, k) at origin + h
    (i, j, k). One vertex per cell the surface crosses (the mean of its edges' crossings), one quad per grid edge
    the surface crosses, oriented outward. Returns V (mm), F (list of 4-tuples)."""
    f = np.asarray(f, float)
    nx, ny, nz = f.shape
    s = f < 0
    corners = [(dx, dy, dz) for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]
    cs = np.stack([s[dx:nx - 1 + dx, dy:ny - 1 + dy, dz:nz - 1 + dz] for dx, dy, dz in corners], -1)
    active = cs.any(-1) & ~cs.all(-1)
    cells = np.argwhere(active)
    idx = -np.ones(active.shape, np.int64)
    idx[tuple(cells.T)] = np.arange(len(cells))
    acc = np.zeros((len(cells), 3))
    cnt = np.zeros(len(cells))
    ci, cj, ck = cells.T
    for a in range(8):
        for b in range(a + 1, 8):
            ca, cb = np.array(corners[a]), np.array(corners[b])
            if np.abs(ca - cb).sum() != 1:
                continue
            fa = f[ci + ca[0], cj + ca[1], ck + ca[2]]
            fb = f[ci + cb[0], cj + cb[1], ck + cb[2]]
            m = (fa < 0) != (fb < 0)
            t = fa[m] / (fa[m] - fb[m])
            acc[m] += ca[None] + t[:, None] * (cb - ca)[None]
            cnt[m] += 1
    V = np.asarray(origin, float) + (cells + acc / np.maximum(cnt, 1)[:, None]) * h
    F = []
    # x edges: between (i,j,k) and (i+1,j,k); the 4 cells around it share (i) and j-1..j, k-1..k
    for axis in range(3):
        sl0 = [slice(None)] * 3
        sl1 = [slice(None)] * 3
        sl0[axis] = slice(0, -1)
        sl1[axis] = slice(1, None)
        s0, s1 = s[tuple(sl0)], s[tuple(sl1)]
        e = np.argwhere(s0 != s1)
        u, v = [ax for ax in range(3) if ax != axis]
        if axis == 1:
            u, v = 2, 0                                   # keep (u, v, axis) right-handed
        ok = (e[:, u] >= 1) & (e[:, v] >= 1) & (e[:, u] <= f.shape[u] - 2) & (e[:, v] <= f.shape[v] - 2)
        e = e[ok]
        inside_low = s0[tuple(e.T)]

        def cell(du, dv):
            c = e.copy()
            c[:, u] -= du
            c[:, v] -= dv
            return idx[tuple(c.T)]
        q = np.stack([cell(1, 1), cell(0, 1), cell(0, 0), cell(1, 0)], 1)
        good = (q >= 0).all(1)
        q, inside_low = q[good], inside_low[good]
        q[~inside_low] = q[~inside_low][:, ::-1]
        F.extend(map(tuple, q.tolist()))
    return V, F


def grid(lo, hi, h):
    """Grid axes (mm) covering lo..hi with spacing h; returns (xs, ys, zs), origin."""
    axes = [np.arange(a, b + h, h) for a, b in zip(lo, hi)]
    return axes, np.array([ax[0] for ax in axes])


# --------------------------------------------------------------------------- simulation

def _hash(*arrays, extra=None):
    hs = hashlib.sha1()
    for a in arrays:
        if a is None:
            hs.update(b"none")
            continue
        a = np.ascontiguousarray(np.round(np.asarray(a, float), 3) if np.asarray(a).dtype.kind == "f" else np.asarray(a))
        hs.update(str(a.shape).encode())
        hs.update(a.tobytes())
    hs.update(json.dumps(extra, sort_keys=True, default=str).encode())
    return hs.hexdigest()[:16]


def _flat(F):
    """Polygons as one integer array (each polygon's size, then its indices), for hashing."""
    return np.array([x for f in F for x in (len(f), *f)], np.int64)


def _mesh_ob(name, V_mm, F):
    import bpy
    me = bpy.data.meshes.new(name)
    me.from_pydata((np.asarray(V_mm) * MM).tolist(), [], [list(f) for f in F])
    me.validate(clean_customdata=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def simulate(name, V, F, colliders=(), pin=None, move=None, move_frames=25, frames=60, cloth=None, self_group=None,
             use_cache=True):
    """Run Blender's cloth solver on the mesh (V mm, F) and return the last frame's vertices (mm).

    colliders: [(V mm, F)] static collision meshes (the rest body, a boot proxy). pin: per-vertex goal weights
    (0..1, 1 = held where it is). move: per-vertex displacement (mm) of the held vertices, reached linearly at frame
    move_frames and kept. self_group: per-vertex 0/1, where self-collision applies (None: everywhere, when on).
    cloth: overrides of RIPSTOP. Cached in cache/cloth/<name>_<hash>.npz."""
    import bpy
    cfg = dict(RIPSTOP, **(cloth or {}))
    F = [tuple(int(i) for i in f) for f in F]
    key = _hash(V, _flat(F), pin, move, self_group, *[c[0] for c in colliders], *[_flat(c[1]) for c in colliders],
                extra={"frames": frames, "move_frames": move_frames, "cfg": cfg, "v": 3})
    path = os.path.join(CLOTH_CACHE, f"{name}_{key}.npz")
    if use_cache and os.path.exists(path):
        say(f"{name}: cached solve {os.path.relpath(path, PROJECT)}")
        return np.load(path)["V"]
    t0 = time.time()
    sc = bpy.context.scene
    made = []
    for k, (Vc, Fc) in enumerate(colliders):
        oc = _mesh_ob(f"Aux.Collider.{k}", Vc, Fc)
        cm = oc.modifiers.new("Collision", "COLLISION")
        oc.collision.thickness_outer = 0.0015
        oc.collision.thickness_inner = 0.004
        oc.collision.cloth_friction = cfg["friction"]
        oc.collision.damping = 0.0
        made.append(oc)
    ob = _mesh_ob(f"Aux.Cloth.{name}", V, F)
    made.append(ob)
    if move is not None:
        ob.shape_key_add(name="Basis", from_mix=False)
        km = ob.shape_key_add(name="Move", from_mix=False)
        km.data.foreach_set("co", ((np.asarray(V, float) + np.asarray(move, float)) * MM).ravel())
        km.value = 0.0
        km.keyframe_insert("value", frame=1)
        km.value = 1.0
        km.keyframe_insert("value", frame=move_frames)
        for fc in ob.data.shape_keys.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    m = ob.modifiers.new("Cloth", "CLOTH")
    st, co = m.settings, m.collision_settings
    st.quality = cfg["quality"]
    st.mass = cfg["mass"]
    st.air_damping = cfg["air_damping"]
    st.tension_stiffness, st.compression_stiffness = cfg["tension"], cfg["compression"]
    st.shear_stiffness, st.bending_stiffness = cfg["shear"], cfg["bending"]
    st.tension_damping, st.compression_damping = cfg["tension_damping"], cfg["compression_damping"]
    st.shear_damping, st.bending_damping = cfg["shear_damping"], cfg["bending_damping"]
    st.effector_weights.gravity = cfg["gravity"]
    if pin is not None:
        g = ob.vertex_groups.new(name="Pin")
        w = np.clip(np.asarray(pin, float), 0, 1)
        for val in np.unique(np.round(w[w > 1e-3], 3)):
            g.add(np.nonzero(np.abs(np.round(w, 3) - val) < 1e-9)[0].tolist(), float(val), "REPLACE")
        st.vertex_group_mass = "Pin"
        st.pin_stiffness = cfg["pin_stiffness"]
    co.collision_quality = cfg["collision_quality"]
    co.distance_min = cfg["distance"] * MM
    co.use_self_collision = bool(cfg["self_collision"])
    co.self_distance_min = cfg["self_distance"] * MM
    co.self_friction = 5.0
    if self_group is not None and cfg["self_collision"]:
        g = ob.vertex_groups.new(name="Self")
        g.add(np.nonzero(np.asarray(self_group) > 0.5)[0].tolist(), 1.0, "REPLACE")
        co.vertex_group_self_collisions = "Self"
    sc.frame_start, sc.frame_end = 1, frames
    m.point_cache.frame_start, m.point_cache.frame_end = 1, frames
    for fr in range(1, frames + 1):
        sc.frame_set(fr)
        if fr % 10 == 0:
            say(f"{name}: frame {fr}/{frames} ({time.time() - t0:.0f} s)")
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    out = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", out)
    ev.to_mesh_clear()
    out = out.reshape(-1, 3) / MM
    sc.frame_set(1)
    for o in made:
        mesh = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.meshes.remove(mesh)
    os.makedirs(CLOTH_CACHE, exist_ok=True)
    np.savez_compressed(path, V=out)
    say(f"{name}: solved {len(V)} verts, {frames} frames in {time.time() - t0:.0f} s -> {os.path.relpath(path, PROJECT)}")
    return out
