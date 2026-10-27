"""Webbing: straps, keepers, loops, folded and tacked ends, PALS rows (spec 13 §3.3, §4.4, owner; spec 02
§4.7 item 4 and §4.10, spec 11 §4.7 item 6, spec 12's straps, spec 14 §3.2).

Millimetres and world space in the API, metres in Blender. Built on sweep.py (surface paths, rotation-
minimising frames, solid strips with folds, threading through slots) and gn_stitches.py (bar tacks, box-X,
running stitches), nothing duplicated:

* `strap()`: sweep.strip with the prototype's realism (research F §8, spec 02 §4.10): a seeded roll of up
  to `roll_deg` along the strap (sweep's twist), a lift of up to `z_jitter` (low-frequency noise, never
  into the surface), an optional sideways wander and sag. Its underside is the path (surface + standoff)
  and it is built solid, so there is no Solidify sign to get wrong (spec 18 §4.13 deviation 1).
* `webbing()`: one object of strips with `UV.Real` (metres, u along: spec 16 §5.1, what Webbing.Nylon.Black
  reads), the selvedge Bevel (0.6 mm, 3 segments, 60 deg, harden normals) and the material through
  lib/materials.py (the recipe id is an argument: the carrier's olive webbing will be another recipe).
* `keeper()`: a loop across a strap: flat tabs sewn on the surface either side, a bridge standing off by
  `standoff` over the strap(s) it holds; `Keeper.box_x()` the box-X stitches on its tabs.
* `loop()`: a pull loop: a webbing folded on itself, the two layers sewn flat for `tack` mm on the surface
  and opening above into a loop that leans back; `loop_tack()` its bar tack across both layers.
* `fold_tack()`: a bar tack across a strap's folded end (after sweep.fold_end).
* `pals_rows()`: PALS rows on a surface: one strip per row, sagging between the bar-tack columns (per-cell
  amplitude jitter, z jitter and roll), the tack frames and the cell centres and normals (spec 13's
  Carrier.Grid.json); `pals_tacks()` lays the bar tacks on the webbing object.
* `bartack`, `bartacks`, `running_stitch`, `box_x`: gn_stitches' layout, re-exported under spec 13's names.

A strap through hardware: place the piece (gear_hardware.frame_on / to_object), then
`sweep.thread(path, piece_object, [gear_hardware.through(piece, i, thickness=t, direction=..., wrap=...)])`
re-routes the strap's path through its slots before strap() sweeps it.
"""
import math

import numpy as np

from . import gn_stitches, sweep

MM = 0.001
bartack, bartacks, box_x, running_stitch = (gn_stitches.bartack, gn_stitches.bartacks, gn_stitches.box_x,
                                            gn_stitches.running)


def _surf(target):
    return target if isinstance(target, sweep.Surface) else sweep.Surface(target)


_seed = gn_stitches._seed


def _bays(s, stations, amp, jitter, seed, flat=0.0):
    """Sag lifts at arc lengths s: one bay amp x (1 +- jitter) x sin(pi t)^0.8 between consecutive stations
    (research F §1), the webbing held flat for `flat` mm either side of each station (under its bar tack),
    zero outside the first and last. Returns (lifts, amplitudes)."""
    st = np.sort(np.asarray(stations, float))
    rng = np.random.default_rng(_seed(seed) + 104729)
    a = amp * (1.0 + jitter * rng.uniform(-1.0, 1.0, max(len(st) - 1, 1)))
    out = np.zeros(len(s))
    for k in range(len(st) - 1):
        s0, s1 = st[k] + flat, st[k + 1] - flat
        if s1 <= s0:
            continue
        m = (s > s0) & (s < s1)
        t = (s[m] - s0) / (s1 - s0)
        out[m] = a[k] * np.sin(np.pi * t) ** 0.8
    return out, a


def strap(path, width=25.0, thickness=1.3, *, quads_across=6, roll_deg=0.4, z_jitter=0.3, z_mm=30.0,
          wander=0.0, sag=0.0, seed=0, conform=True, uv_offset=None):
    """A webbing strap along a path (its underside; sweep.surface_path with the standoff, or a threaded
    path): sweep.strip with a seeded roll (`roll_deg`), a lift of 0..z_jitter mm varying over ~z_mm, a
    sideways wander and a sag (a number: one bay over the strap; (amplitude, pitch): bays; or per point).
    Returns a sweep.Strip (fold it with sweep.fold_end)."""
    seed = _seed(seed)
    s = path.s
    L = path.length
    per = L if path.closed else None
    lift = np.zeros(len(s))
    if z_jitter:
        lift += z_jitter * 0.5 * (1.0 + sweep.noise(s, _seed(seed) + 5, z_mm, per))
    if isinstance(sag, tuple):
        amp, pitch = sag
        lift += _bays(s, np.arange(0.0, L + pitch, pitch), amp, 0.2, seed)[0]
    elif np.ndim(sag) == 0 and sag:
        lift += float(sag) * np.sin(np.pi * np.clip(s / L, 0.0, 1.0)) ** 0.8
    elif np.ndim(sag) == 1:
        lift += np.asarray(sag, float)
    return sweep.strip(path, width, thickness, quads_across, twist_deg=roll_deg, sag=lift, seed=seed,
                       jitter=wander, conform=conform, uv_offset=uv_offset)


def _geometry(sweeps):
    V, F, UV = [], [], []
    for sw in sweeps:
        v, f, uv = sw.geometry()
        b = sum(len(x) for x in V)
        V.append(v)
        F.extend(tuple(i + b for i in x) for x in f)
        UV.extend(uv)
    return np.vstack(V), F, UV


def _link(name, data, scope, coll):
    import bpy
    if scope is not None:
        return scope.new_object(name, data, coll)
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old)
    ob = bpy.data.objects.new(name, data)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def webbing(name, strips, *, part, material="Webbing.Nylon.Black", bevel=0.6, segments=3, angle_deg=60.0,
            scope=None, coll=None, **overrides):
    """One object of one or more strips (sweep Strips or Tubes): a mesh in metres with UV.Real, shaded
    smooth, the selvedge Bevel (`bevel` mm, `segments`, limited to edges over `angle_deg`, harden normals;
    0 for none), and `material` (a catalogue ID, through lib/materials.py; None for none)."""
    import bpy
    from . import modifiers
    sweeps = strips if isinstance(strips, (list, tuple)) else [strips]
    v, f, uv = _geometry(sweeps)
    me = bpy.data.meshes.new(name)
    me.from_pydata((v * MM).tolist(), [], [list(x) for x in f])
    lay = me.uv_layers.new(name="UV.Real")
    lay.data.foreach_set("uv", np.concatenate(uv).astype(np.float32).ravel())
    me.shade_smooth()
    me.validate()
    me.update()
    ob = _link(name, me, scope, coll)
    if bevel:
        modifiers.bevel(ob, bevel, segments, angle_deg, 0.5, harden=True)
    if material:
        from . import materials
        materials.assign(ob, material, part=part, **overrides)
    ob["webbing_mm"] = [round(float(getattr(s, "width", 0.0)), 3) for s in sweeps]
    return ob


# --------------------------------------------------------------------------- keepers and loops

class Keeper:
    """A keeper loop: its path (underside), strip, the two tabs [(top centre, run direction)] and the
    strap direction it crosses."""

    def __init__(self, path, strip, tabs, along, size):
        self.path, self.strip, self.tabs, self.along, self.size = path, strip, tabs, along, size

    def box_x(self, keeper_ob, size=None, pitch=2.5, seed=0):
        """Box-X stitches on both tabs, laid on the keeper object's surface (spec 02 §4.8 item 4)."""
        sz = size or self.size
        return gn_stitches.Stitches.join([gn_stitches.box_x(keeper_ob, c, u, sz, pitch, seed=_seed(seed) + 3 * k)
                                          for k, (c, u) in enumerate(self.tabs)])


def keeper(target, centre, along, *, span=19.0, width=12.0, thickness=2.0, standoff=5.0, tab=8.0, ramp=3.0,
           quads_across=4, roll_deg=0.3, seed=0, step=0.5, lift=0.05, box=None):
    """A keeper across a strap running along `along` at `centre` (spec 02 §3.4: leather 18 x 12 x 2 standing
    5 off; spec 13's webbing keepers): a strip `width` wide run across the strap (n x along), flat tabs of
    `tab` mm on the surface at both ends, ramps of `ramp`, and a bridge `standoff` mm off the surface
    spanning `span` mm (the strap's width plus clearance; for two layers, their thickness and a gap). The
    underside sits `lift` mm above the surface. Returns a Keeper (box: the box-X size, default the tab
    less 2 by the width less 3)."""
    seed = _seed(seed)
    surf = _surf(target)
    q, n, _, _ = surf.nearest(np.asarray(centre, float))
    a = np.asarray(along, float)
    a = sweep._unit(a - (a @ n) * n)
    u = np.cross(n, a)
    total = span + 2.0 * (ramp + tab)
    base = sweep.surface_path(surf, [q - u * total / 2, q + u * total / 2], lift, step, smooth=False, path_sigma=1.0)
    s = base.s
    up = sweep._smoothstep(s, tab, tab + ramp) * sweep._smoothstep(total - s, tab, tab + ramp)
    P = base.lifted(standoff * up)
    P.on = 1.0 - up
    st = sweep.strip(P, width, thickness, quads_across, twist_deg=roll_deg, seed=seed, conform=True)
    S = gn_stitches._Sampler(base)
    tabs = []
    for t0 in (tab * 0.5, total - tab * 0.5):
        p, nn, _ = S(t0)
        tabs.append((p + nn * (lift + thickness), u))
    return Keeper(P, st, tabs, a, box or (max(tab - 2.0, 2.0), max(width - 3.0, 2.0)))


def loop(target, root, up, *, rise=40.0, tack=15.0, opening=8.0, lean_deg=20.0, width=20.0, thickness=1.3,
         gap=0.2, quads_across=6, roll_deg=0.3, seed=0, step=0.5, lift=0.05):
    """A pull loop (spec 02 §4.7 item 4: 20 x 1.3, standing 25 above the rim, folded 15 under the binding;
    spec 11's glove loop lies flat: lean 80-90): a webbing folded on itself whose two layers lie flat on the
    surface from `root` up (`up`, projected on the surface) for `tack` mm, then part into a loop `opening`
    mm wide inside, reaching `rise` mm above the root, leaning back (outward) by `lean_deg` about the top
    of the tack. In the plane of the root's normal and `up`. Returns a sweep.Strip (its `.tack`: the bar
    tack's centre, across direction and length along the loop)."""
    seed = _seed(seed)
    surf = _surf(target)
    q, n, _, _ = surf.nearest(np.asarray(root, float))
    u = np.asarray(up, float)
    u = sweep._unit(u - (u @ n) * n)
    t = thickness
    R0 = opening / 2.0 + t
    x_out = 2.0 * t + gap
    top = rise - t
    pts = [(0.0, y) for y in np.arange(0.0, top - R0, step)]
    pts += [(R0 + R0 * math.cos(th), top - R0 + R0 * math.sin(th)) for th in np.radians(np.linspace(180.0, 0.0, 37))]
    h = sweep._blend(np.array([2 * R0, top - R0, 0.0]), np.array([0.0, -1.0, 0.0]), np.array([x_out, tack, 0.0]),
                     np.array([0.0, -1.0, 0.0]), step)
    pts += [(p[0], p[1]) for p in h]
    pts += [(x_out, y) for y in np.arange(tack - step, -1e-9, -step)]
    X = np.array(pts)
    lean = math.radians(lean_deg)
    above = X[:, 1] > tack
    rel = X[above] - (0.0, tack)
    w = np.clip((X[above, 1] - tack) / max(top - tack, 1e-6), 0.0, 1.0) ** 0.5   # the fold eases into the lean
    ang = lean * w
    X[above] = np.c_[rel[:, 0] * np.cos(ang) + rel[:, 1] * np.sin(ang),
                     -rel[:, 0] * np.sin(ang) + rel[:, 1] * np.cos(ang)] + (0.0, tack)
    co = q[None] + n[None] * (X[:, :1] + lift) + u[None] * X[:, 1:2]
    T = np.gradient(X, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    Nx = np.c_[T[:, 1], -T[:, 0]]   # in-plane, toward the loop's inside: +n on the inner leg, -n on the outer
    nrm = n[None] * Nx[:, :1] + u[None] * Nx[:, 1:2]
    on = (X[:, 1] <= tack + 1e-6).astype(float)
    P = sweep.Path(co, nrm, True, on, False, surf, lift)
    st = sweep.strip(P, width, thickness, quads_across, twist_deg=roll_deg, seed=seed, conform=True)
    st.tack = (q + n * (lift + 2 * t + gap), np.cross(n, u), tack)
    return st


def loop_tack(strip_ob, loop_strip, *, length=None, width=4.0, pitch=0.6, at=0.6, seed=0):
    """The bar tack across a pull loop's two layers (spec 02: 20 x 4), `at` of the tack length up from the
    root, `length` across (default the webbing width less 3), on the loop object's surface."""
    c, across, tack = loop_strip.tack
    upv = sweep._unit(np.cross(across, loop_strip.path.normal[0]))
    if upv @ (loop_strip.path.co[min(5, len(loop_strip.path) - 1)] - loop_strip.path.co[0]) < 0:
        upv = -upv
    centre = c + upv * (at * tack) + loop_strip.path.normal[0] * 1.0
    return gn_stitches.bartack(strip_ob, centre, across, length or loop_strip.width - 3.0, width, pitch, seed=seed)


def fold_tack(strip_ob, strip, *, at="end", length=None, width=4.0, pitch=0.6, from_end=None, seed=0):
    """A bar tack across a strap's folded end (sweep.fold_end first; spec 02: 12 x 4 on the tail, 1.3
    pitch): centred `from_end` mm from the end (default half the fold), `length` across (default the
    width less 3), on the strap object's surface over the doubled layer."""
    fold = next((f for f in strip.folds if f[0] in (at, "both")), None)
    if fold is None:
        raise ValueError(f"the strip has no fold at its {at}")
    _, flen, fgap = fold
    P = strip.path
    T, N, B = sweep.rmf_frames(P)
    s = P.s
    d = (from_end if from_end is not None else 0.5 * flen)
    i = int(np.argmin(np.abs(s - (s[-1] - d if at == "end" else d))))
    top = P.co[i] + N[i] * (2.0 * strip.thickness + fgap + 1.0)
    return gn_stitches.bartack(strip_ob, top, B[i], length or strip.width - 3.0, width, pitch, seed=seed)


# --------------------------------------------------------------------------- PALS

def pals_rows(target, rows, cols, *, width=25.4, thickness=1.3, sag=3.5, sag_jitter=0.2, z_jitter=0.5,
              roll_jitter=0.4, quads_across=6, step=1.0, lift=0.05, flat=2.0, seed=0):
    """PALS rows (spec 13 §3.3, §4.4; research F §1): rows are control points (world mm) along each row on
    the target; cols the arc lengths (mm from each row's start) of the bar-tack columns, one list for all
    rows or one per row. Each row is one strip that lies on the surface at the columns (flat for `flat` mm
    either side, under the 3 mm tack) and sags `sag` mm (x (1 +- sag_jitter) per cell, seeded) between
    them, with a z jitter of up to `z_jitter` inside the
    cells and a roll of up to `roll_jitter` deg. Returns {"strips", "paths", "tacks": [(centre on the
    webbing top, across)], "cells": [{"row", "col", "centre", "normal", "sag"}]}."""
    surf = _surf(target)
    per_row = len(cols) == len(rows) and np.ndim(cols[0]) == 1
    out = {"strips": [], "paths": [], "tacks": [], "cells": []}
    for r, pts in enumerate(rows):
        P = sweep.surface_path(surf, pts, lift, step)
        st = np.asarray(cols[r] if per_row else cols, float)
        st = st[(st >= 0.0) & (st <= P.length)]
        s = P.s
        bay, amps = _bays(s, st, sag, sag_jitter, _seed(seed) + 31 * r, flat)
        env = np.zeros(len(s))
        for k in range(len(st) - 1):
            s0, s1 = st[k] + flat, st[k + 1] - flat
            m = (s > s0) & (s < s1)
            env[m] = np.sin(np.pi * (s[m] - s0) / (s1 - s0))
        zj = z_jitter * 0.5 * (1.0 + sweep.noise(s, _seed(seed) + 7 * r + 3, 20.0)) * env
        strip = sweep.strip(P, width, thickness, quads_across, twist_deg=roll_jitter, sag=bay + zj,
                            seed=_seed(seed) + r, conform=True)
        out["strips"].append(strip)
        out["paths"].append(P)
        T, N, B = sweep.rmf_frames(P)
        S = gn_stitches._Sampler(P)
        for c in st:
            p, nn, b = S(c)
            out["tacks"].append((p + nn * (lift + thickness), b))
        for k in range(len(st) - 1):
            p, nn, _ = S(0.5 * (st[k] + st[k + 1]))
            out["cells"].append({"row": r, "col": k, "centre": (p + nn * (lift + thickness + amps[k])).tolist(),
                                 "normal": nn.tolist(), "sag": float(amps[k])})
    return out


def pals_tacks(webbing_ob, rows_out, *, length=22.0, width=3.0, pitch=1.05, seed=0):
    """The bar tacks of pals_rows() laid on the webbing object (spec 13: 3 x 22, 21 V's at 1.05)."""
    return gn_stitches.bartacks(webbing_ob, rows_out["tacks"], length, width, pitch, seed=seed)


# --------------------------------------------------------------------------- self-test

def selftest():
    """A strap round a cylinder (closed, manifold, seated: no penetration, lift within the jitter, UV.Real
    along it), the webbing object (bevel on the stack, UV, material slot), a keeper (tabs on the surface,
    bridge at the standoff, box-X on its tabs), a pull loop (both layers on the surface, the loop's height
    and opening, no penetration), a folded tail with its bar tack, and PALS rows on a plane (sag at the cell
    middles, flat at the columns, tacks on the webbing)."""
    import bpy
    R, made = {}, []
    try:
        cyl = sweep._cylinder_object("SelftestWb.Cylinder", r=55.0, h=220.0)
        made.append(cyl)
        surf = sweep.Surface(cyl)
        ang = 2 * np.pi * np.arange(12) / 12
        ring = sweep.surface_path(surf, np.stack([62 * np.cos(ang), 62 * np.sin(ang), np.full(12, 158.0)], 1),
                                  standoff=1.0, step=1.0, closed=True)
        st = strap(ring, 15.0, 1.5, roll_deg=0.4, z_jitter=0.3, seed=4)
        rv = np.linalg.norm(st.verts[:, :2], axis=1)
        pen = sweep.penetration(st, surf)
        assert st.manifold() and pen["inside"] == 0, pen
        assert rv.min() > 55.9 and rv.max() < 55.0 + 1.0 + 0.3 + 1.5 + 0.2, (rv.min(), rv.max())
        R["strap"] = {"faces": len(st.faces), "r_mm": [round(float(rv.min()), 3), round(float(rv.max()), 3)]}

        ob = webbing("SelftestWb.Strap", [st], part="SelftestWb", material=None)
        made.append(ob)
        assert [m.type for m in ob.modifiers] == ["BEVEL"] and ob.data.uv_layers.get("UV.Real") is not None
        us = np.empty(len(ob.data.uv_layers["UV.Real"].data) * 2)
        ob.data.uv_layers["UV.Real"].data.foreach_get("uv", us)
        assert abs(np.ptp(us[0::2]) - ring.length * MM) < 0.001, (np.ptp(us[0::2]), ring.length)

        # a keeper over the strap at 72 deg: tabs on the surface, bridge 5 off
        c = np.array([62 * math.cos(1.2566), 62 * math.sin(1.2566), 158.0])
        tangent = np.array([-math.sin(1.2566), math.cos(1.2566), 0.0])
        kp = keeper(surf, c, tangent, span=19.0, width=12.0, thickness=2.0, standoff=5.0)
        kv = kp.strip.verts
        sd = surf.signed_distance(kv)
        assert kp.strip.manifold() and sd.min() > -0.05 and abs(sd.max() - (5.0 + 2.0 + 0.05)) < 0.5, (sd.min(), sd.max())
        kob = webbing("SelftestWb.Keeper", [kp.strip], part="SelftestWb", material=None, bevel=0.5)
        made.append(kob)
        bx = kp.box_x(kob)
        dz = sweep.Surface(kob).signed_distance(bx.mid())
        assert len(bx) > 15 and np.abs(dz).max() < 0.1, (len(bx), np.abs(dz).max())
        R["keeper"] = {"faces": len(kp.strip.faces), "bridge_mm": round(float(sd.max()), 3), "box_x": len(bx)}

        # a pull loop at the back: up +Z from z 190, rising 40, opening 8
        lp = loop(surf, (-56.0, 0.0, 190.0), (0.0, 0.0, 1.0), rise=40.0, tack=15.0, opening=8.0, lean_deg=20.0)
        lv = lp.verts
        sd = surf.signed_distance(lv)
        assert lp.manifold() and sd.min() > -0.1, sd.min()
        zt = lv[:, 2].max() - 190.0
        assert 30.0 < zt < 40.5, zt   # leaning back shortens its rise
        lob = webbing("SelftestWb.Loop", [lp], part="SelftestWb", material=None)
        made.append(lob)
        lt = loop_tack(lob, lp)
        assert len(lt) > 20
        R["loop"] = {"faces": len(lp.faces), "rise_mm": round(float(zt), 2), "tack_legs": len(lt)}

        # a tail folded 10 and tacked (spec 02 §4.10)
        tail = sweep.surface_path(surf, [(62 * math.cos(a), 62 * math.sin(a), 140.0) for a in (0.3, 0.6, 0.9)],
                                  standoff=1.0, step=0.5)
        ts = strap(tail, 15.0, 1.5, seed=2)
        sweep.fold_end(ts, 10.0)
        tob = webbing("SelftestWb.Tail", [ts], part="SelftestWb", material=None)
        made.append(tob)
        ft = fold_tack(tob, ts)
        dz = sweep.Surface(tob).signed_distance(ft.mid())
        assert ts.manifold() and len(ft) > 10 and np.abs(dz).max() < 0.2, np.abs(dz).max()
        R["fold_tack"] = {"legs": len(ft)}

        # PALS: three rows on a plane, columns every 38.1
        plane = sweep._plane_object("SelftestWb.Plane", size=300.0)
        made.append(plane)
        rows = [[(-100.0, y, 0.0), (100.0, y, 0.0)] for y in (-38.1, 0.0, 38.1)]
        cols = list(np.arange(5.0, 200.0, 38.1))
        res = pals_rows(plane, rows, cols, seed=1)
        assert len(res["strips"]) == 3 and len(res["tacks"]) == 3 * len(cols) and len(res["cells"]) == 3 * (len(cols) - 1)
        top = []
        for cell in res["cells"]:
            p = np.array(cell["centre"])
            top.append(p[2] - 1.3 - 0.05)
        top = np.array(top)
        assert np.all(top > 3.5 * 0.79) and np.all(top < 3.5 * 1.21), top
        pob = webbing("SelftestWb.Pals", res["strips"], part="SelftestWb", material=None)
        made.append(pob)
        tk = pals_tacks(pob, res)
        z = np.vstack([tk.p0, tk.p1])[:, 2]
        assert np.all(np.abs(z - 1.35) < 0.25), (z.min(), z.max())
        R["pals"] = {"cells": len(res["cells"]), "sag_mm": [round(float(top.min()), 2), round(float(top.max()), 2)],
                     "tack_legs": len(tk)}
        return R
    finally:
        for o in made:
            data = o.data
            bpy.data.objects.remove(o)
            if data is not None and data.users == 0:
                bpy.data.meshes.remove(data)
