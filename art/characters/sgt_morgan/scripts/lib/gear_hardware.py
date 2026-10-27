"""Hardware generators: eyelets, grommets, speed hooks, ladder-locks, tri-glides, D-rings, slide bars,
rivets, screw heads and aglets (spec 13 §3.6, owner; shared by specs 02, 11, 12, 14 and 15).

Millimetres in the API, each piece in its own frame: origin on the surface it is fitted to, +Z out of that
surface (an eyelet's or a grommet's axis, which is also the axis Metal.Gunmetal's anisotropy runs round),
+X the piece's own long or "up" direction as each generator says. `frame_on()` makes the 4 x 4 frame that
puts a piece on a surface (sweep.Surface: nearest point and smooth normal, X from a hint, seeded seat
error), `to_object()` makes the object (metres, the frame as its matrix), `row()` many objects sharing one
mesh (a die-punched eyelet row; each object keeps its own Z for the anisotropy), and `conform()` bends a
piece's base onto the curved surface it sits on (a quadratic fitted under its footprint: a flat 13 mm
plate floats 0.4 mm at its edges on a 50 mm shaft).

Topology, after the trap of the materials test boot (a 400-valent fan under a Subdivision cost minutes of
OpenSubdiv per render): nothing here is subdivided. Round parts are lathes of closed profiles (torus
topology, quads only: an eyelet's rolled lip runs into a pressed flange and down its barrel) or of
profiles that end at a small radius closed by one n-gon; flat parts are extruded outlines or grid slabs
(quads, n-gon caps on plates), their edges rounded by a Bevel modifier limited by angle, with harden
normals and a Weighted Normal on flat parts (not on crowned ones, where it drew facets), which rounds the
outline and the slot edges alike and leaves the grid's flat edges and the lathes' facets alone. Wire parts are sweep.py tubes with rounded tips. Every piece is a closed,
consistently outward-oriented manifold (signed volume checked).

Ladder-locks and tri-glides carry their slots and bars: `through(piece, i, ...)` gives sweep.thread()'s slot
dict for a strap of a given thickness passing through slot i in either direction, wrapping either bar,
centred or `snug` against it, and `over(piece, k)` a straight run flat across cross bar k, so a strap
threaded up-over-down hugs the bar instead of arching over it (a strap keeps the same face inside a bend:
its wraps alternate with each turn round a bar). Speed hooks carry the point the lace
wraps (`anchors["wrap"]`).

Dimensions default to the specs: spec 02 §3.4 (eyelet flange 10, hole 5.5, 0.7 proud, barrel 7, its rolled
lip r 0.85; speed hook wire 2.5 rising 7 over 180 deg at outer r 4.5, down 2, two dome rivets, tilted 20 deg
outward, on a 12 x 13 x 1 crowned plate with r 3 corners where spec 02 has 14 x 16 x 1.2 r 1.5 (E): see
speed_hook(); ladder-lock 18 along x 24 across x 3, two slots; aglet 20 x 4.5),
spec 13 §3.6 (#0 grommet hole 6.4, flange 11; ladder-lock 38 52 x 44 bars 4 x 6; slide bar 38 x 8 x 2; screw
heads), spec 14 §3.2 (tri-glide 38: 50 x 31 x 4, bars 4; D-ring).
"""
import json
import math

import numpy as np

from . import sweep

MM = 0.001


# --------------------------------------------------------------------------- the piece record

class Piece:
    """Hardware geometry in its own frame (mm): verts (V, 3), faces (index tuples), `bevel` (width mm,
    segments, angle_deg[, harden]) for the object's Bevel modifier or None (harden, default True, also adds
    harden normals and a Weighted Normal: right for flat faces, faceting on a crown), `slots` (dicts in the frame), `anchors`
    ({name: (point, axis)}), `kind` and `dims` (the defining dimensions, for reports)."""

    def __init__(self, verts, faces, *, bevel=None, slots=None, anchors=None, kind="", dims=None):
        self.verts = np.asarray(verts, float).reshape(-1, 3)
        self.faces = [tuple(int(i) for i in f) for f in faces]
        if self.faces and _signed_volume(self.verts, self.faces) < 0:
            self.faces = [f[::-1] for f in self.faces]
        self.bevel, self.slots, self.anchors = bevel, list(slots or []), dict(anchors or {})
        self.kind, self.dims = kind, dict(dims or {})

    @staticmethod
    def join(pieces, **kw):
        V, F = [], []
        for p in pieces:
            b = sum(len(v) for v in V)
            V.append(p.verts)
            F.extend(tuple(i + b for i in f) for f in p.faces)
        kw.setdefault("slots", [s for p in pieces for s in p.slots])
        kw.setdefault("anchors", {k: v for p in pieces for k, v in p.anchors.items()})
        return Piece(np.vstack(V), F, **kw)

    def transformed(self, M):
        """The piece moved by a 4 x 4 (mm) matrix: vertices, slots and anchors."""
        M = np.asarray(M, float)
        R, t = M[:3, :3], M[:3, 3]
        P = Piece(self.verts @ R.T + t, self.faces, bevel=self.bevel, kind=self.kind, dims=self.dims)
        P.slots = [dict(s, centre=R @ np.asarray(s["centre"]) + t,
                        **{k: R @ np.asarray(s[k]) for k in ("axis", "along", "across") if k in s}) for s in self.slots]
        P.anchors = {k: (R @ np.asarray(p) + t, R @ np.asarray(a)) for k, (p, a) in self.anchors.items()}
        return P

    def mirrored(self, axis="Y"):
        """The piece mirrored across its frame's plane normal to `axis` (the other stay's speed hook); the
        winding is turned back outward by the constructor's volume check."""
        S = np.eye(4)
        k = "XYZ".index(axis)
        S[k, k] = -1.0
        return self.transformed(S)

    def bbox(self):
        return self.verts.min(0), self.verts.max(0)

    def volume(self):
        return _signed_volume(self.verts, self.faces)

    def manifold(self):
        return _manifold(len(self.verts), self.faces)

    def mesh(self, name, smooth=True):
        import bpy
        me = bpy.data.meshes.new(name)
        me.from_pydata((self.verts * MM).tolist(), [], [list(f) for f in self.faces])
        if smooth:
            me.shade_smooth()
        me.validate()
        me.update()
        return me


def _signed_volume(v, faces):
    return sweep._signed_volume(np.asarray(v, float), faces)


def _manifold(nv, faces):
    a = np.concatenate([np.asarray(f, np.int64) for f in faces])
    b = np.concatenate([np.roll(np.asarray(f, np.int64), -1) for f in faces])
    fwd, rev = a * nv + b, b * nv + a
    return bool(len(np.unique(fwd)) == len(fwd) and np.isin(rev, fwd).all())


# --------------------------------------------------------------------------- builders

def lathe(profile, segments=32, *, closed=True, hexagon=None):
    """A surface of revolution about Z of a profile [(r, z)]: closed (a loop, torus topology, quads only)
    or open from end to end with each end ring closed by one n-gon (end radii small). hexagon: (indices,
    across-flats mm) maps those profile points onto a hexagon about Z (a socket; segments a multiple of 6)."""
    P = np.asarray(profile, float)
    m = len(P)
    a = 2.0 * np.pi * np.arange(segments) / segments
    r = np.repeat(P[:, :1], segments, 1)
    if hexagon is not None:
        idx, flats = hexagon
        if segments % 6:
            raise ValueError("a hexagon needs segments in multiples of 6")
        k = 0.5 * flats / np.cos(np.mod(a, np.pi / 3.0) - np.pi / 6.0)   # vertices at 0, 60, ...
        for i in idx:
            r[i] = k
    V = np.stack([r * np.cos(a)[None, :], r * np.sin(a)[None, :], np.repeat(P[:, 1:2], segments, 1)], -1).reshape(-1, 3)
    F = []
    rows = m if closed else m - 1
    for i in range(rows):
        i2 = (i + 1) % m
        for j in range(segments):
            j2 = (j + 1) % segments
            F.append((i * segments + j, i * segments + j2, i2 * segments + j2, i2 * segments + j))
    if not closed:   # the first ring's cap runs against the side faces' edges there, the last's with them
        F.append(tuple(range(segments))[::-1])
        F.append(tuple((m - 1) * segments + j for j in range(segments)))
    return V, F


def _orient(V, F):
    return F if _signed_volume(V, F) >= 0 else [f[::-1] for f in F]


def rounded_rect(w, h, r, per_corner=6, centre=(0.0, 0.0)):
    """A rounded rectangle outline (w x h, corner radius r), counter-clockwise, (K, 2) mm."""
    r = min(r, 0.5 * min(w, h) - 1e-6)
    cx, cy = centre
    out = []
    for (sx, sy, a0) in ((1, 1, 0.0), (-1, 1, 90.0), (-1, -1, 180.0), (1, -1, 270.0)):
        c = (cx + sx * (w / 2 - r), cy + sy * (h / 2 - r))
        for a in np.radians(a0 + np.linspace(0.0, 90.0, per_corner)):
            out.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return np.array(out)


def slab(outline, z0, z1):
    """An outline (K, 2) extruded from z0 to z1: two n-gon caps and K quads. Returns (V, F)."""
    O = np.asarray(outline, float)
    k = len(O)
    V = np.vstack([np.c_[O, np.full(k, z0)], np.c_[O, np.full(k, z1)]])
    F = [tuple(range(k))[::-1], tuple(range(k, 2 * k))]
    F += [(j, (j + 1) % k, k + (j + 1) % k, k + j) for j in range(k)]
    return V, _orient(V, F)


def grid_solid(xs, ys, solid, thickness, z=None):
    """A slab over the solid cells of a rectilinear grid: cell (i, j) spans xs[i]..xs[i+1] by ys[j]..ys[j+1];
    `solid` (nx, ny) booleans; thickness centred on z(x, y) (default 0). Top and bottom quads per cell and
    walls where a solid cell meets an open one: a closed manifold of quads (no two solid cells may touch
    only at a corner). Returns (V, F)."""
    xs, ys, S = np.asarray(xs, float), np.asarray(ys, float), np.asarray(solid, bool)
    nx, ny = len(xs) - 1, len(ys) - 1
    zf = z or (lambda x, y: 0.0)
    index, V = {}, []

    def v(i, j, top):
        key = (i, j, top)
        if key not in index:
            zc = zf(xs[i], ys[j])
            index[key] = len(V)
            V.append((xs[i], ys[j], zc + (0.5 if top else -0.5) * thickness))
        return index[key]

    def open_(i, j):
        return not (0 <= i < nx and 0 <= j < ny and S[i, j])

    F = []
    for i in range(nx):
        for j in range(ny):
            if not S[i, j]:
                continue
            F.append((v(i, j, 1), v(i + 1, j, 1), v(i + 1, j + 1, 1), v(i, j + 1, 1)))
            F.append((v(i, j + 1, 0), v(i + 1, j + 1, 0), v(i + 1, j, 0), v(i, j, 0)))
            if open_(i, j - 1):
                F.append((v(i, j, 0), v(i + 1, j, 0), v(i + 1, j, 1), v(i, j, 1)))
            if open_(i, j + 1):
                F.append((v(i + 1, j + 1, 0), v(i, j + 1, 0), v(i, j + 1, 1), v(i + 1, j + 1, 1)))
            if open_(i - 1, j):
                F.append((v(i, j + 1, 0), v(i, j, 0), v(i, j, 1), v(i, j + 1, 1)))
            if open_(i + 1, j):
                F.append((v(i + 1, j, 0), v(i + 1, j + 1, 0), v(i + 1, j + 1, 1), v(i + 1, j, 1)))
    return np.array(V), F


def _tube_piece(points, radius, sides=16, *, closed=False, round_ends=True):
    """A wire along points (mm): a sweep.py tube, its ends rounded over one radius when open."""
    P = np.asarray(points, float)
    path = sweep.Path(P, closed=closed).resampled(max(radius / 3.0, 0.15))
    r = np.full(len(path), float(radius))
    if round_ends and not closed:
        s = path.s
        L = s[-1]
        for d in (s, L - s):
            near = d < radius
            r[near] = np.minimum(r[near], radius * np.sqrt(np.clip(1.0 - ((radius - d[near]) / radius) ** 2, 0.02, 1.0)))
    tb = sweep.tube(path, r, sides)
    return tb.verts, tb.faces


def _resample_poly(pts, step):
    out, _ = sweep._resample(np.asarray(pts, float), step)
    return out


# --------------------------------------------------------------------------- round parts

def eyelet(flange_d=10.0, hole_d=5.5, proud=0.7, roll=0.85, barrel_d=7.0, depth=5.9, *, edge=0.3, sunk=0.15,
           segments=32):
    """A rolled eyelet (spec 02 §3.4; a two-piece eyelet as a boot's die sets it): the barrel's top rolled
    outward over a lip of radius `roll` whose crown stands `proud` above the surface (z 0), running into a
    pressed flange that falls in a convex shoulder to its thin outer edge (diameter flange_d, `edge` thick
    there, rounded, `sunk` into the leather, so only edge - sunk of it shows: a thick edge read as a washer
    laid on the leather), a hole of hole_d; the barrel (outer diameter barrel_d) runs `depth` below and
    the hidden underside closes the profile. Quads only. (A revolved torus, the first try, read as an O-ring
    lying on the leather; a flat washer would read as a washer.)"""
    R, ri = flange_d / 2.0, hole_d / 2.0
    rb = max(barrel_d / 2.0, ri + 0.3)
    lip_c = (ri + roll, proud - roll)
    prof = [(ri, -depth), (ri, lip_c[1] - 0.6 * roll)]
    prof += [(lip_c[0] + roll * math.cos(t), lip_c[1] + roll * math.sin(t))
             for t in np.radians(np.linspace(180.0, 90.0, 8))]
    # the flange's crown: from the lip's top down to the edge's top, convex (a pressed dome)
    er = 0.5 * edge
    z_edge = edge - sunk
    r0, r1 = lip_c[0], R - er
    for u in np.linspace(0.0, 1.0, 9)[1:]:
        prof.append((r0 + (r1 - r0) * u, z_edge + (proud - z_edge) * (1.0 - u * u) ** 0.8))
    ec = (R - er, z_edge - er)
    prof += [(ec[0] + er * math.cos(t), ec[1] + er * math.sin(t)) for t in np.radians(np.linspace(60.0, -90.0, 6))]
    prof += [(rb + 0.4, z_edge - edge), (rb, z_edge - edge - 0.3), (rb, -depth)]
    V, F = lathe(prof, segments)
    return Piece(V, F, kind="eyelet", dims={"flange_d": flange_d, "hole_d": hole_d, "proud": proud,
                                           "roll": roll, "edge": edge, "barrel_d": barrel_d})


def grommet(hole_d=6.4, flange_d=11.0, proud=0.8, roll=0.9, depth=3.0, *, washer=True, washer_d=None,
            segments=36):
    """A #0 grommet (spec 13 §3.6: hole 6.4, flange 11): an eyelet's rolled rim and barrel through `depth` mm
    of fabric, and with `washer` the toothless back washer seen from the inside (its face at z -depth)."""
    g = eyelet(flange_d, hole_d, proud, roll, hole_d + 1.0, depth, segments=segments)
    parts = [g]
    if washer:
        wd = washer_d or flange_d * 1.05
        prof = [(hole_d / 2 + 0.2, -depth + 0.1), (wd / 2 - 0.3, -depth + 0.05), (wd / 2, -depth - 0.25),
                (wd / 2 - 0.3, -depth - 0.55), (hole_d / 2 + 0.6, -depth - 0.6), (hole_d / 2 + 0.2, -depth - 0.3)]
        V, F = lathe(prof, segments)
        parts.append(Piece(V, F))
    return Piece.join(parts, kind="grommet", dims={"hole_d": hole_d, "flange_d": flange_d, "proud": proud})


def rivet(d=3.0, h=0.8, *, skirt=0.4, squareness=2.6, segments=24, arc=8):
    """A dome rivet head Ø d standing h above the surface, sunk `skirt` below it (hidden)."""
    R = d / 2.0
    e = 2.0 / squareness
    th = np.radians(np.linspace(88.0, 0.0, arc))
    dome = np.c_[R * np.cos(th) ** e, h * np.sin(th) ** e]
    prof = [tuple(p) for p in dome] + [(R, -skirt), (0.05 * R, -skirt)]
    V, F = lathe(prof, segments, closed=False)
    return Piece(V, F, kind="rivet", dims={"d": d, "h": h})


def screw_head(d=7.0, h=1.8, *, kind="button", socket=2.5, socket_depth=1.2, skirt=0.3, segments=48, arc=9):
    """A screw head Ø d, h proud: 'button' (ISO 7380 low dome) or 'dome' (a taller round head), with a hex
    socket `socket` mm across flats (0 for none) `socket_depth` deep (spec 13 §4.5's panel screws)."""
    R = d / 2.0
    e = 2.0 / (3.2 if kind == "button" else 2.2)
    rs = 0.5 * socket / math.cos(math.pi / 6) if socket else 0.0
    th = np.radians(np.linspace(85.0 if not socket else math.degrees(math.acos(min(rs / R, 0.99) ** (1 / e))),
                                0.0, arc))
    dome = np.c_[R * np.cos(th) ** e, h * np.sin(th) ** e]
    if socket:
        top = float(dome[0, 1])
        prof = [(0.05, top - socket_depth), (rs, top - socket_depth), (rs, top - 0.2)]
        prof += [tuple(p) for p in dome] + [(R, -skirt), (0.05, -skirt)]
        V, F = lathe(prof, segments, closed=False, hexagon=((1, 2, 3), socket))
    else:
        prof = [tuple(p) for p in dome] + [(R, -skirt), (0.05 * R, -skirt)]
        V, F = lathe(prof, segments, closed=False)
    return Piece(V, F, kind="screw_head", dims={"d": d, "h": h, "socket": socket})


def aglet(length=20.0, d=4.5, *, lace_d=4.0, segments=24):
    """A polymer aglet (spec 02 §3.4: 20 x Ø 4.5): +Z along it from the lace end (z 0, the lace runs in
    toward -Z) to a rounded tip; a slight crimp waist a third of the way along."""
    R, rl = d / 2.0, lace_d / 2.0
    tip = np.radians(np.linspace(0.0, 85.0, 7))
    prof = [(0.05, 0.0), (rl * 0.95, 0.0), (R * 0.96, 0.35), (R, 1.0), (R * 0.97, length * 0.33),
            (R, length * 0.45)]
    prof += [(R * math.cos(t) ** 0.8, length - R * 0.7 + R * 0.7 * math.sin(t)) for t in tip]
    V, F = lathe(prof, segments, closed=False)
    return Piece(V, F, kind="aglet", dims={"length": length, "d": d})


# --------------------------------------------------------------------------- hooks and rings

def crowned_plate(w, h, t, corner_r, *, crown=0.3, edge=0.6, rings=6, per_corner=6):
    """A pressed plate w x h (mm, centred, in XY) whose top rises from `edge` x t at its rounded outline to
    t + crown in the middle (a slight dome over inset rings, an n-gon at the crown), flat underneath at z 0.
    Returns (V, F)."""
    out = rounded_rect(w, h, corner_r, per_corner)
    k = len(out)
    span = 0.42 * min(w, h)
    V = [np.c_[out, np.zeros(k)]]
    for i in range(rings + 1):
        d = span * i / rings
        u = i / rings
        ww, hh = w - 2 * d, h - 2 * d
        ring = rounded_rect(ww, hh, corner_r + (0.5 * min(ww, hh) - corner_r) * u, per_corner)
        V.append(np.c_[ring, np.full(k, edge * t + (t * (1 - edge) + crown) * (1 - (1 - u) ** 2))])
    V = np.vstack(V)
    F = [tuple(range(k))[::-1]]
    for i in range(rings + 1):
        a, b = i * k, (i + 1) * k
        F += [(a + j, a + (j + 1) % k, b + (j + 1) % k, b + j) for j in range(k)]
    F.append(tuple(range((rings + 1) * k, (rings + 2) * k)))
    return V, _orient(V, F)


def speed_hook(plate=(12.0, 13.0, 1.0), corner_r=3.0, wire_d=2.5, rise=7.0, outer_r=4.5, drop=2.0, *,
               tilt_deg=20.0, crown=0.3, rivet_d=2.8, rivet_h=0.7, bevel=0.35, sides=16):
    """A plate-mounted speed hook (spec 02 §3.4, §4.8 item 2): a pressed plate (12 along +X, the stay's
    upward direction, x 13 across, +Y toward the throat; r 3 corners, crowned 0.3, thinner at its edge) with
    a wire hook rising `rise` from the plate's throat edge, over 180 deg (outer radius `outer_r`) toward +X
    and down `drop`, so its mouth opens upward (+X) with the tip clear of the surface; the hook tilted
    `tilt_deg` outward about Y; two dome rivets at the plate's outer corners. anchors["wrap"]: where the lace
    wraps the post (axis +Y). Spec 02's plate is 14 x 16 x 1.2 with r 1.5 corners (E); flat and that large it
    read as a tag screwed to the stay beside a small hook, so the default is smaller, rounder and crowned."""
    px, py, pt = plate
    wr = wire_d / 2.0
    Rc = outer_r - wr
    V0, F0 = crowned_plate(px, py, pt, corner_r, crown=crown)
    parts = [Piece(V0, F0)]
    x0, y0 = -Rc, py / 2.0 - wr - 0.9
    arc = np.radians(np.linspace(180.0, 0.0, 25))
    pts = [(x0, y0, pt * 0.5), (x0, y0, pt + rise * 0.5)]
    pts += [(x0 + Rc + Rc * math.cos(t), y0, pt + rise + Rc * math.sin(t)) for t in arc]
    pts += [(x0 + 2 * Rc, y0, pt + rise - drop)]
    P = _resample_poly(pts, 0.25)
    a = math.radians(-tilt_deg)   # about +Y through the post's foot: the mouth (+X) turns toward +Z
    Ry = np.array([[math.cos(a), 0.0, math.sin(a)], [0.0, 1.0, 0.0], [-math.sin(a), 0.0, math.cos(a)]])
    pivot = np.array([x0, y0, pt])
    P = (P - pivot) @ Ry.T + pivot
    Vh, Fh = _tube_piece(P, wr, sides)
    parts.append(Piece(Vh, Fh))
    for sx in (-1.0, 1.0):
        rx, ry = sx * (px / 2 - rivet_d / 2 - 1.3), -(py / 2 - rivet_d / 2 - 1.3)
        rv = rivet(rivet_d, rivet_h).transformed(_translate((rx, ry, pt + 0.5 * crown)))
        parts.append(rv)
    wrap = (np.array([x0 + Rc, y0, pt + rise - Rc * 0.3]) - pivot) @ Ry.T + pivot
    tip_z = float(P[-1, 2]) - wr
    return Piece.join(parts, bevel=(bevel, 2, 40.0, False), kind="speed_hook",
                      anchors={"wrap": (wrap, np.array([0.0, 1.0, 0.0]))},
                      dims={"plate": plate, "wire_d": wire_d, "rise": rise, "outer_r": outer_r, "drop": drop,
                            "tilt_deg": tilt_deg, "tip_clear_mm": round(tip_z, 3),
                            "mouth_mm": round(2 * Rc - wire_d, 3)})


def _translate(t):
    M = np.eye(4)
    M[:3, 3] = t
    return M


def d_ring(width=25.0, height=18.0, wire_d=3.0, *, corner_r=3.0, sides=16):
    """A D-ring lying in its frame's XY plane: the straight bar along X at y 0 (where a tab wraps it), the
    bow toward +Y; inside width `width`, inside height `height`, wire Ø wire_d."""
    w = width / 2.0 + wire_d / 2.0
    h = height + wire_d / 2.0
    y0 = -wire_d / 2.0
    a = w - corner_r
    ctrl = [(-a, y0), (0.0, y0), (a, y0), (w, y0 + corner_r), (w * 0.92, y0 + 0.62 * h), (w * 0.55, y0 + 0.93 * h),
            (0.0, y0 + h), (-w * 0.55, y0 + 0.93 * h), (-w * 0.92, y0 + 0.62 * h), (-w, y0 + corner_r)]
    co, _ = sweep.catmull_rom(np.c_[np.array(ctrl), np.zeros(len(ctrl))], closed=True, per_mm=2.0)
    V, F = _tube_piece(co, wire_d / 2.0, sides, closed=True)
    return Piece(V, F, kind="d_ring", dims={"width": width, "height": height, "wire_d": wire_d})


# --------------------------------------------------------------------------- frames with slots

def ladder_lock(width=24.0, length=18.0, bar=3.0, thickness=3.0, slots=2, *, arch=1.5, edge_r=1.2,
                end_bar=None, cells=1.5):
    """A ladder-lock (or, with arch 0, a tri-glide): a frame `width` across (X, the strap's width) by
    `length` along (Y, the strap's run) by `thickness`, side bars and cross bars `bar` wide (the end bars
    `end_bar`), `slots` slots between the cross bars, the frame bowed `arch` mm along Y (the middle bars
    stand higher, as a stamped lock's do), all edges rounded by a Bevel of `edge_r`. Spec 02's boot lock is
    the default (18 x 24 x 3); spec 13's 38 mm lock: ladder_lock(52, 44, 4, 6); spec 14's: (50, 32, 4, 3.5).
    Slots: centre, axis +Z (through the frame), along +Y, across +X, size (across, along)."""
    eb = bar if end_bar is None else end_bar
    nbar = slots + 1
    gap = (length - 2 * eb - (nbar - 2) * bar) / slots
    if gap <= 0.5 or width - 2 * bar <= 1.0:
        raise ValueError(f"no room for {slots} slots in {length} x {width} with {bar} mm bars")
    yb = [-length / 2.0]
    for k in range(slots):
        yb.append(yb[-1] + (eb if k == 0 else bar))
        yb.append(yb[-1] + gap)
    yb.append(length / 2.0)
    ys = [yb[0]]
    for y0, y1 in zip(yb[:-1], yb[1:]):
        n = max(1, int(round((y1 - y0) / cells)))
        ys += list(np.linspace(y0, y1, n + 1)[1:])
    xs = [-width / 2, -width / 2 + bar]
    n = max(1, int(round((width - 2 * bar) / (2 * cells))))
    xs += list(np.linspace(-width / 2 + bar, width / 2 - bar, n + 1)[1:]) + [width / 2]
    xs, ys = np.array(xs), np.array(ys)
    xc, yc = 0.5 * (xs[:-1] + xs[1:]), 0.5 * (ys[:-1] + ys[1:])
    in_bar = np.zeros(len(yc), bool)
    for k in range(0, len(yb) - 1, 2):
        in_bar |= (yc > yb[k]) & (yc < yb[k + 1])
    side = (xc < -width / 2 + bar) | (xc > width / 2 - bar)
    S = side[:, None] | in_bar[None, :]

    def zf(x, y):
        return arch * (1.0 - (2.0 * y / length) ** 2)

    V, F = grid_solid(xs, ys, S, thickness, zf)
    sl = []
    for k in range(slots):
        y0, y1 = yb[2 * k + 1], yb[2 * k + 2]
        c = 0.5 * (y0 + y1)
        sl.append({"centre": np.array([0.0, c, zf(0.0, c)]), "axis": np.array([0.0, 0.0, 1.0]),
                   "along": np.array([0.0, 1.0, 0.0]), "across": np.array([1.0, 0.0, 0.0]),
                   "size": (width - 2 * bar, y1 - y0), "depth": thickness})
    anchors = {}   # the cross bars' top centres ("bar.0" the -Y end bar), axis along Y, for over()
    for k in range(slots + 1):
        y0, y1 = yb[2 * k], yb[2 * k + 1]
        c = 0.5 * (y0 + y1)
        anchors[f"bar.{k}"] = (np.array([0.0, c, zf(0.0, c) + thickness / 2.0]), np.array([0.0, 1.0, 0.0]))
    bars = [round(float(yb[2 * k + 1] - yb[2 * k]), 4) for k in range(slots + 1)]
    return Piece(V, F, bevel=(edge_r, 3, 30.0), slots=sl, anchors=anchors, kind="ladder_lock" if arch else "tri_glide",
                 dims={"width": width, "length": length, "bar": bar, "thickness": thickness, "slots": slots,
                       "arch": arch, "slot_gap": round(gap, 3), "bars": bars})


def tri_glide(width=50.0, length=31.0, bar=4.0, thickness=4.0, *, edge_r=1.4):
    """A tri-glide (spec 14 §3.2: 38 mm, 50 x 31 x 4, bars 4): a flat two-slot frame."""
    return ladder_lock(width, length, bar, thickness, 2, arch=0.0, edge_r=edge_r, cells=2.0)


def through(piece, i, *, thickness=1.5, direction=1, wrap=1, snug=False, clearance=0.15):
    """sweep.thread()'s slot dict for a strap of `thickness` through slot i of a piece (in the piece's
    frame; pass the piece's placed object or frame matrix as thread()'s hardware): direction +1 travels
    along the slot's axis (+Z, out of the frame's underside toward its top), -1 against it; wrap +1 has the
    strap's thickness grow toward +Y (it wraps the bar on the -Y side of the slot), -1 toward -Y. The
    path given to thread() is the strap's underside: centred in the slot, or with `snug` against the wall
    of the bar it wraps (`clearance` off it), as a strap pulled tight lies. A strap keeps the same face
    inside a bend, so its wraps alternate with each turn of direction round a bar."""
    s = piece.slots[i]
    up = wrap * np.asarray(s["along"], float)
    c = np.asarray(s["centre"], float)
    if snug:
        c = c - up * (0.5 * float(s["size"][1]) - clearance)
    else:
        c = c - up * (thickness / 2.0)
    return {"centre": c, "axis": direction * np.asarray(s["axis"], float), "up": up, "depth": float(s["depth"])}


def over(piece, k, *, direction=1, gap=0.15, under=False, thickness=1.5):
    """sweep.thread()'s slot dict for a strap lying across cross bar k of a ladder-lock or tri-glide (bar 0
    the -Y end bar), so the strap hugs the bar instead of arching over it: a straight run the bar's width
    long, `gap` mm over its top (or, with `under`, below its underside), travelling +Y (direction +1) or
    -Y, its thickness growing away from the bar. Put it between the two slots' entries in thread()."""
    top, ax = piece.anchors[f"bar.{k}"]
    w = float(piece.dims["bars"][k])
    z = np.array([0.0, 0.0, 1.0])
    if under:
        depth = float(piece.dims.get("thickness", 3.0))
        return {"centre": top - z * (depth + gap), "axis": direction * ax, "up": -z, "depth": w}
    return {"centre": top + z * gap, "axis": direction * ax, "up": z, "depth": w}


def slide_bar(length=38.0, width=8.0, thickness=2.0, *, corner_r=1.5, edge_r=0.6):
    """A flat steel slide (keeper) bar (spec 13 §3.6: 38 x 8 x 2 under a strap keeper), along X."""
    V, F = slab(rounded_rect(length, width, corner_r), -thickness / 2, thickness / 2)
    return Piece(V, F, bevel=(edge_r, 2, 30.0), kind="slide_bar",
                 dims={"length": length, "width": width, "thickness": thickness})


# --------------------------------------------------------------------------- placing and objects

def frame_on(surface, point, x_hint, *, lift=0.0, spin_deg=0.0, seed=None, seat_mm=0.0, tilt_deg=0.0):
    """The 4 x 4 frame (mm) that puts a piece on a surface: origin at the surface point nearest `point`
    (plus `lift` along the normal), +Z the smooth normal, +X the hint projected on the tangent plane and
    turned `spin_deg` about Z. With a seed, a seat error: up to `seat_mm` across the surface and a tilt of
    up to `tilt_deg` about a random tangent axis (spec 02 §4.8: each eyelet within ±0.3 mm, ±3°)."""
    surf = surface if isinstance(surface, sweep.Surface) else sweep.Surface(surface)
    q, n, _, _ = surf.nearest(np.asarray(point, float))
    x = np.asarray(x_hint, float)
    x = sweep._unit(x - (x @ n) * n)
    if seed is not None and (seat_mm or tilt_deg):
        rng = np.random.default_rng((int(seed) % 2147483647) * 31 + 7)
        y = np.cross(n, x)
        q, n = surf.nearest(q + seat_mm * rng.uniform(-1, 1) * x + seat_mm * rng.uniform(-1, 1) * y)[:2]
        x = sweep._unit(x - (x @ n) * n)
        ax = sweep._unit(np.cross(n, x) * rng.uniform(-1, 1) + x * rng.uniform(-1, 1))
        ang = math.radians(tilt_deg) * rng.uniform(-1, 1)
        rot = lambda v: v * math.cos(ang) + np.cross(ax, v) * math.sin(ang) + ax * (ax @ v) * (1 - math.cos(ang))
        n, x = sweep._unit(rot(n)), sweep._unit(rot(x))
    if spin_deg:
        a = math.radians(spin_deg)
        y = np.cross(n, x)
        x = x * math.cos(a) + y * math.sin(a)
    y = np.cross(n, x)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, n, q + n * lift
    return M


def conform(piece, surface, frame, *, reach=20.0, smooth=True):
    """The piece with every vertex moved along its frame's Z by the height of the surface under it (a ray
    from `reach` mm above along -Z), so a flat base sits on a curved one: a 16 mm hook plate across a
    shaft of r 50 floats 0.6 mm at its edges otherwise, an eyelet's flange 0.25. Slots and anchors move
    with the height at their centres. frame: the 4 x 4 (mm) the piece will be placed with. smooth: fit the
    heights with a quadratic (a piece spans a few mm of a smooth surface; following a faceted mesh's flats
    rippled an eyelet's flange on the materials test boot)."""
    surf = surface if isinstance(surface, sweep.Surface) else sweep.Surface(surface)
    M = np.asarray(frame, float)
    R, t = M[:3, :3], M[:3, 3]
    Z = R[:, 2]

    def height(x, y):
        o = t + R @ np.array([x, y, reach])
        h = surf.ray(o, -Z, 3.0 * reach)
        return 0.0 if h is None else float((h[0] - t) @ Z)

    keys = np.round(piece.verts[:, :2], 2)
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    hu = np.array([height(x, y) for x, y in uniq])
    if smooth and len(uniq) >= 12:
        x, y = uniq[:, 0], uniq[:, 1]
        A = np.c_[np.ones(len(x)), x, y, x * x, x * y, y * y]
        coef = np.linalg.lstsq(A, hu, rcond=None)[0]
        fit = lambda x, y: float(np.array([1.0, x, y, x * x, x * y, y * y]) @ coef)
        hu = A @ coef
        height = fit   # slots and anchors take the fitted surface too
    hz = hu[inv.ravel()]
    P = Piece(piece.verts + np.c_[np.zeros((len(hz), 2)), hz], piece.faces, bevel=piece.bevel, kind=piece.kind,
              dims=dict(piece.dims, conformed=True))
    P.slots = [dict(s, centre=np.asarray(s["centre"]) + [0.0, 0.0, height(*np.asarray(s["centre"])[:2])])
               for s in piece.slots]
    P.anchors = {k: (np.asarray(p) + [0.0, 0.0, height(*np.asarray(p)[:2])], a) for k, (p, a) in piece.anchors.items()}
    return P


def matrix_m(M):
    """A frame in mm as a mathutils Matrix in metres (rotation kept, translation scaled)."""
    from mathutils import Matrix
    M = np.array(M, float)
    M[:3, 3] *= MM
    return Matrix(M.tolist())


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


def _finish(ob, piece, material, part, overrides):
    from . import modifiers
    if piece.bevel:
        w, seg, ang, *rest = piece.bevel
        hard = rest[0] if rest else True   # flat parts: harden + Weighted Normal; crowned ones stay smooth
        modifiers.bevel(ob, w, seg, ang, harden=hard)
        if hard:
            modifiers.weighted_normal(ob)
    if material:
        from . import materials
        materials.assign(ob, material, part=part, **overrides)
    ob["hardware"] = piece.kind
    ob["dims"] = json.dumps(piece.dims, default=float)
    if piece.slots:
        ob["slots"] = json.dumps([{k: (np.asarray(v).tolist() if isinstance(v, np.ndarray) else v)
                                   for k, v in s.items()} for s in piece.slots])


def to_object(name, piece, *, matrix=None, material=None, part=None, scope=None, coll=None, data=None,
              **overrides):
    """The piece as an object: its mesh (metres, in its own frame), the frame (mm 4 x 4, frame_on()) as the
    object's matrix, the Bevel and Weighted Normal it asks for, the material (a catalogue ID through
    lib/materials.py) and its dims and slots as properties. data: a mesh to share instead of a new one."""
    me = data if data is not None else piece.mesh(name)
    ob = _link(name, me, scope, coll)
    if matrix is not None:
        ob.matrix_world = matrix_m(matrix)
    _finish(ob, piece, material, part, overrides)
    return ob


def row(prefix, piece, frames, *, material=None, part=None, scope=None, coll=None, surface=None, **overrides):
    """Objects `<prefix>.1`, `.2`, ... one per frame (a row of eyelets or hooks): sharing one mesh, or with
    `surface` each conformed to it (conform()) in a mesh of its own."""
    if surface is not None:
        return [to_object(f"{prefix}.{k + 1}", conform(piece, surface, M), matrix=M, material=material, part=part,
                          scope=scope, coll=coll, **overrides) for k, M in enumerate(frames)]
    me = piece.mesh(prefix)
    obs = [to_object(f"{prefix}.{k + 1}", piece, matrix=M, material=material, part=part, scope=scope,
                     coll=coll, data=me, **overrides) for k, M in enumerate(frames)]
    me.name = prefix
    return obs


def slot_frame(ob, i):
    """Slot i of a placed hardware object in world mm (centre, axis, along, across)."""
    s = json.loads(ob["slots"])[i]
    M = np.array(ob.matrix_world, float)
    R, t = M[:3, :3], M[:3, 3] / MM
    return {k: (R @ np.asarray(s[k]) + (t if k == "centre" else 0.0)) for k in ("centre", "axis", "along", "across")}


# --------------------------------------------------------------------------- self-test

def selftest():
    """Every generator closed and outward (signed volume), quads where promised, the defining dimensions
    met (eyelet flange and hole, proud height; hook plate, tip clearance and mouth; lock frame and slots;
    socket flats); a strap threaded through a placed ladder-lock that does not enter it; a frame on a
    cylinder (origin on it, Z its normal); an object with its Bevel and Weighted Normal."""
    import bpy
    R, made = {}, []
    try:
        e = eyelet()
        r = np.linalg.norm(e.verts[:, :2], axis=1)
        top = e.verts[:, 2].max()
        assert e.manifold() and e.volume() > 0 and all(len(f) == 4 for f in e.faces)
        assert abs(r.max() - 5.0) < 0.02 and abs(r.min() - 2.75) < 1e-6 and abs(top - 0.7) < 0.01, \
            (r.max(), r.min(), top)
        R["eyelet"] = {"faces": len(e.faces), "outer_d": round(2 * float(r.max()), 3),
                       "hole_d": round(2 * float(r.min()), 3), "proud": round(float(top), 3)}
        g = grommet()
        assert g.manifold() and g.volume() > 0   # two closed shells: the eyelet part and the washer
        R["grommet_faces"] = len(g.faces)

        h = speed_hook(tilt_deg=0.0)
        lo, hi = h.bbox()
        assert h.manifold() and h.volume() > 0   # plate, wire and rivets: closed shells that overlap
        assert abs(h.dims["tip_clear_mm"] - (1.0 + 7.0 - 2.0 - 1.25)) < 0.05, h.dims   # 4.75 above the surface
        assert abs(h.dims["mouth_mm"] - 4.0) < 1e-6 and abs(hi[2] - (1.0 + 7.0 + 4.5)) < 0.15, (hi, h.dims)
        assert np.allclose(hi[:2] - lo[:2], (12.0, 13.0), atol=0.5) or hi[0] - lo[0] > 12.0
        ht = speed_hook()
        assert ht.anchors["wrap"][0][2] > 4.0
        R["speed_hook"] = {"faces": len(ht.faces), "tip_clear_mm": h.dims["tip_clear_mm"],
                           "mouth_mm": h.dims["mouth_mm"], "height_mm": round(float(hi[2]), 2)}

        lk = ladder_lock()
        lo, hi = lk.bbox()
        assert lk.manifold() and lk.volume() > 0 and all(len(f) == 4 for f in lk.faces)
        assert np.allclose(hi[:2] - lo[:2], (24.0, 18.0), atol=1e-6) and len(lk.slots) == 2
        vol = 3.0 * (24 * 18 - 2 * lk.slots[0]["size"][0] * lk.slots[0]["size"][1])
        assert abs(lk.volume() / vol - 1) < 0.02, (lk.volume(), vol)   # the arch shears, it keeps the volume
        tg = tri_glide()
        assert tg.manifold() and abs(tg.bbox()[1][2] - 2.0) < 1e-9
        R["ladder_lock"] = {"faces": len(lk.faces), "slot_mm": [round(float(x), 2) for x in lk.slots[0]["size"]],
                            "volume_ratio": round(lk.volume() / vol, 4)}

        dr = d_ring()
        assert dr.manifold() and dr.volume() > 0
        sb = slide_bar()
        assert sb.manifold() and np.allclose(sb.bbox()[1] - sb.bbox()[0], (38, 8, 2), atol=1e-6)
        rv = rivet()
        assert rv.manifold() and abs(rv.verts[:, 2].max() - 0.8) < 0.02
        sh = screw_head(socket=2.5)
        assert sh.manifold()
        ring = sh.verts.reshape(-1, 48, 3)[1]   # the socket floor's ring: a hexagon 2.5 across flats
        rr = np.linalg.norm(ring[:, :2], axis=1)
        assert abs(rr.min() - 1.25) < 1e-6 and abs(rr.max() - 1.25 / math.cos(math.pi / 6)) < 1e-6
        ag = aglet()
        assert ag.manifold() and abs(ag.verts[:, 2].max() - 20.0) < 0.05
        R["small"] = {"d_ring": len(dr.faces), "slide_bar": len(sb.faces), "rivet": len(rv.faces),
                      "screw_head": len(sh.faces), "aglet": len(ag.faces)}

        # a frame on a cylinder r 50: origin on it, Z its normal, X the hint's tangent part
        cyl = sweep._cylinder_object("SelftestHw.Cylinder")
        made.append(cyl)
        surf = sweep.Surface(cyl)
        M = frame_on(surf, (60.0, 0.0, 100.0), (0.0, 0.3, 1.0))
        assert abs(np.linalg.norm(M[:2, 3]) - 50.0) < 0.01 and M[:3, 2] @ np.array([1.0, 0, 0]) > 0.999
        assert abs(M[:3, 0] @ M[:3, 2]) < 1e-9 and M[:3, 0] @ np.array([0, 0, 1.0]) > 0.95
        Mj = frame_on(surf, (60.0, 0.0, 100.0), (0.0, 0.0, 1.0), seed=3, seat_mm=0.3, tilt_deg=3.0)
        tilt = math.degrees(math.acos(min(1.0, Mj[:3, 2] @ sweep._unit(np.r_[Mj[:2, 3], 0.0]))))
        assert tilt < 3.2 and np.linalg.norm(Mj[:3, 3] - M[:3, 3]) < 0.6, (tilt,)

        # a strap threaded through a ladder-lock 10 mm above a plane: up through slot 1, over the middle
        # bar, down through slot 0; the strap must not enter the frame
        plane = sweep._plane_object("SelftestHw.Plane")
        made.append(plane)
        F = np.eye(4)
        F[:3, 3] = (0.0, 0.0, 10.0)
        lock = to_object("SelftestHw.Lock", lk, matrix=F)
        made.append(lock)
        path = sweep.surface_path(plane, [(0.0, 60.0, 0.0), (0.0, -60.0, 0.0)], standoff=0.3, step=0.5)
        slots = [through(lk, 1, thickness=1.5, direction=1, wrap=1), through(lk, 0, thickness=1.5, direction=-1, wrap=-1)]
        tp = sweep.thread(path, F, slots, lead=20.0, clear=1.5)
        strap = sweep.strip(tp, 15.0, 1.5, 6)
        pen = sweep.penetration(strap, lock)
        assert strap.manifold() and pen["max_mm"] < 0.35, pen
        # pulled tight: snug in the slots and flat across the middle bar (over()), 0.15 over its top
        tight = [through(lk, 1, direction=1, wrap=1, snug=True), over(lk, 1, direction=-1),
                 through(lk, 0, direction=-1, wrap=-1, snug=True)]
        tt = sweep.thread(path, F, tight, lead=20.0)
        st2 = sweep.strip(tt, 15.0, 1.5, 6)
        pen2 = sweep.penetration(st2, lock)
        top_bar = (F @ np.r_[lk.anchors["bar.1"][0], 1.0])[2]
        hump = float(tt.co[np.abs(tt.co[:, 1]) < 1.0, 2].max() - top_bar)
        assert st2.manifold() and pen2["max_mm"] < 0.35 and 0.0 < hump < 0.6, (pen2, hump)
        R["thread_lock"] = {"strap_vertices": pen["of"], "inside": pen["inside"], "max_mm": round(pen["max_mm"], 3),
                            "tight_over_bar_mm": round(hump, 3), "tight_inside_mm": round(pen2["max_mm"], 3)}

        # the object: bevel and weighted normal on the stack, the bevel rounding the frame's edges
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = lock.evaluated_get(dg)
        me = ev.to_mesh()
        n_eval = len(me.polygons)
        ev.to_mesh_clear()
        assert [m.type for m in lock.modifiers] == ["BEVEL", "WEIGHTED_NORMAL"] and n_eval > 2 * len(lk.faces)
        assert len(json.loads(lock["slots"])) == 2 and slot_frame(lock, 0)["centre"][2] > 5.0
        obs = row("SelftestHw.Eyelet", eyelet(), [M, Mj])
        made += obs
        assert obs[0].data == obs[1].data and obs[0].data.name == "SelftestHw.Eyelet"
        R["objects"] = {"lock_faces_evaluated": n_eval}

        # conform: a hook plate across the cylinder's curve (13 mm across on r 50) sits on it at its edges
        Mh = frame_on(surf, (60.0, 0.0, 100.0), (0.0, 0.0, 1.0))
        flat, bent = speed_hook(), conform(speed_hook(), surf, Mh)
        base = np.abs(flat.verts[:, 2]) < 1e-9   # the plate's underside
        W = lambda P: P.verts[base] @ Mh[:3, :3].T + Mh[:3, 3]
        gap_flat = float(np.abs(surf.signed_distance(W(flat))).max())
        gap_bent = float(np.abs(surf.signed_distance(W(bent))).max())
        assert gap_flat > 0.3 and gap_bent < 0.05, (gap_flat, gap_bent)   # 13 across on r 50: 0.42
        assert bent.manifold() and bent.dims.get("conformed")
        R["conform_mm"] = {"flat": round(gap_flat, 3), "conformed": round(gap_bent, 4)}
        return R
    finally:
        meshes = {o.data for o in made if o.data is not None}
        for o in made:
            bpy.data.objects.remove(o)
        for me in meshes:
            if me.users == 0:
                bpy.data.meshes.remove(me)
