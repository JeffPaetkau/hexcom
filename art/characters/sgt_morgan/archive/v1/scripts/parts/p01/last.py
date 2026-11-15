"""The last of spec 01 §4.13 and §0 item 3: Foot.<S>.Last, the socked foot's envelope with the boot's allowances, the
interface object spec 02 builds the boot around and spec 08 stands on its footbed.

Built from the REST foot with Foot.Contact at its loaded 1.0 (the toes flat, as the rest foot holds them) and the sock
at its loaded thickness (the plantar 3.0 mm pressed to 1.8): the body's rendered surface and the nail plates (each
moved with its toe under the load), wrapped as the sock is (sock.py: rings of section hulls, then a membrane over the
foot), the obstacle standing off the skin by the sock's inner gap, its loaded thickness and the allowances of §4.13 (the
ball's sides +2 each, so +4 across; the instep +2; the heel's sides +1; the heel's back and the sole 0), with a stiffer
membrane than the sock's so the tendons, the malleoli's hollows and the toes' notches smooth out. Then the parts a
last has and a foot does not:

  bottom     the insole plane, z_b, the loaded sock's sole: each section across the foot takes its points' drop onto
             it (drawn in by a fifth of their height), so the bottom is flat from the heel seat to the toe and fills
             the arch, and the sides meet it at the feather line; the heel's underside is pressed onto it.
  toe box    the front 45 mm stretched forward along the foot so that the last's tip stands the toe allowance (15 mm,
             §0 item 3) ahead of the STANDING, SOCKED toe: the loaded foot's socked envelope (socked_front), in plan,
             after the toe spring (Jeff, 2026-10-27, "Reality": real boots leave 15-22 mm before the standing toe; the
             old 274.3 + 15 left about 7 ahead of the socked toe), the toes' envelope kept.
  toe spring the forefoot ahead of the ball line (the 1st and 5th metatarsal heads' points on the insole plane)
             turned up about it by 12 degrees, eased in over the first 30 mm (§4.13), so the last carries its own
             toe spring and the pose extends the toes by the same angle.
  collar     the last ends at z 210 (`last_collar`), closed by one face; the toe is closed by linking, as the sock.

Markers (Empties, children of the last): .Pternion (the last's most posterior point dropped onto the insole plane),
.Ball1, .Ball5 (the foot's 1st and 5th metatarsal heads' bulges dropped onto it: the three points spec 08 §4.7(e)
puts on the footbed), .ToeTip (the last's foremost point), .AnkleAxis.Medial, .AnkleAxis.Lateral (the malleoli).
"""
import math

import numpy as np

from lib import sculpt as S
from parts.p01 import sock as SK

COLLAR_Z = 210.0
ALLOW = {"ball_side": 2.0, "instep": 2.0, "heel_side": 1.0}      # mm, §4.13
FACET_MM = 0.15                     # the last's flat facets between its vertices: kept this far clear of the socked foot
TOE_ALLOWANCE = 15.0                 # mm, §0 item 3: the last's tip this far ahead of the standing, socked toe (Jeff,
                                     # 2026-10-27: "Reality"; was the stated foot length + 15, 289.3)
TOE_SPRING_DEG, SPRING_BLEND = 12.0, 30.0
STRETCH_FROM = 45.0                  # the toe box's stretch starts this far behind the socked foot's front
LAST_MEMBRANE = {"iters": 400, "length": 3.0}


def nail_shift(ob, frame, side, rest_co, loaded_co, groups):
    """{nail object name: F-mm translation} the loaded key gives each nail's bed (the mean of its bed's vertices),
    so the plates ride their toes under the load (they are bone-parented, not on the key)."""
    out = {}
    for k in (1, 2, 3, 4, 5):
        w = groups.get(f"Foot.NailBed.{k}")
        if w is None:
            continue
        sel = (w > 0.5) & (frame.s * rest_co[:, 0] > 0.0)   # the bed group holds both feet; +X is the left
        if not sel.any():
            continue
        d = frame.vec_to_f((loaded_co[sel] - rest_co[sel]).mean(axis=0))
        out[f"Foot.{side}.Nail.{k}"] = d
    return out


def regions(G, N, L, ball_y):
    """Allowance weights per grid vertex (F): the ball's sides about the metatarsal heads' line, the instep's top,
    the heel's sides."""
    x, y, z = G[..., 0], G[..., 1], G[..., 2]
    nx, nz = N[..., 0], N[..., 2]
    sm = S.smoothstep
    side = sm(np.abs(nx), 0.45, 0.75) * (z < 60.0)
    ball = side * np.exp(-((y - ball_y) / 22.0) ** 2)
    instep = sm(nz, 0.4, 0.7) * sm(-y, 0.30 * L, 0.40 * L) * (1.0 - sm(-y, 0.66 * L, 0.74 * L)) * (z > 25.0)
    heel = side * (1.0 - sm(-y, 0.25 * L, 0.33 * L)) * (z < 50.0)
    return {"ball": ball, "instep": instep, "heel": heel}


def flatten_bottom(G, N, z_b, snap=1.5):
    """The insole plane: the underside within `snap` mm of z_b pressed onto it, nothing below it. (The sections across
    the foot were hulled with their points' drop onto the floor, sock.ring_points' `bottom`, before the membrane, so
    their bottoms are flat already and fill the arch; this takes the heel's, whose sock is thinner, down to the same
    plane.)"""
    out = G.copy()
    z = out[..., 2]
    down = N[..., 2] < -0.7
    out[..., 2] = np.where(down & (z < z_b + snap), z_b, np.maximum(z, z_b))
    return out


def stretch(G, y_from, k):
    """The toe box: y ahead of y_from scaled by k about it (k > 1 lengthens)."""
    out = G.copy()
    y = out[..., 1]
    ahead = y < y_from
    out[..., 1] = np.where(ahead, y_from + (y - y_from) * k, y)
    return out


def ball_line(b1, b5):
    """The metatarsal heads' line in plan: (point, unit direction, unit normal toward the toes) in F."""
    p = np.array(b1[:2], float)
    t = np.array(b5[:2], float) - p
    t /= np.linalg.norm(t)
    nrm = np.array([t[1], -t[0]])
    if nrm[1] > 0.0:
        nrm = -nrm
    return p, t, nrm


def toe_spring(G, b1, b5, z_b, deg=TOE_SPRING_DEG, blend=SPRING_BLEND):
    """Turn the forefoot up about the ball line on the insole plane: a point d mm ahead of it turns by
    deg x smoothstep(d / blend) about the line (the bend eased over the first `blend` mm)."""
    p, t, nrm = ball_line(b1, b5)
    P = G.reshape(-1, 3)
    d = (P[:, :2] - p) @ nrm
    ang = np.radians(deg) * S.smoothstep(d, 0.0, blend)
    # in the plane across the line: s along nrm (toward the toes), h up from the insole plane
    s, h = d, P[:, 2] - z_b
    c, sn = np.cos(ang), np.sin(ang)
    s2, h2 = s * c - h * sn, s * sn + h * c
    # a turn upward: the toes rise, so the forward coordinate turns toward +z
    out = P.copy()
    out[:, :2] = P[:, :2] + np.outer(s2 - s, nrm)
    out[:, 2] = z_b + h2
    return out.reshape(G.shape)


def spring_angle(G_bottom_pts, b1, b5, z_b, blend=SPRING_BLEND):
    """The bottom's slope ahead of the bend (degrees): a line fitted to the bottom points more than blend + 5 mm
    ahead of the ball line."""
    p, t, nrm = ball_line(b1, b5)
    d = (G_bottom_pts[:, :2] - p) @ nrm
    sel = (d > blend + 5.0) & (d < d.max() - 15.0)   # the flat of the toe box, not its rounded front
    if sel.sum() < 3:
        return None
    A = np.stack([d[sel], np.ones(sel.sum())], axis=1)
    k, _ = np.linalg.lstsq(A, G_bottom_pts[sel, 2], rcond=None)[0]
    return math.degrees(math.atan(k))


def faces(rings, n):
    """The sock's quads and toe linking, with one n-gon closing the collar (the top ring)."""
    F = SK.faces(rings, n)
    F.append(tuple(range(n - 1, -1, -1)))
    return F


def build(V, T, kept_sts, tree, off, front_y, b1, b5, z_b, taper_from=None):
    """The last's grid in F (rings, n, 3) from the loaded foot's surface: the hull rings, the stiff membrane at the
    per-vertex offset `off` (a (rings, n) array, or a function of the hull grid and its normals), the bottom, the toe
    box stretched until its foremost point lies at y `front_y` (plan, after the toe spring: the standing socked toe's
    front less TOE_ALLOWANCE), the toe spring. Returns (grid, info)."""
    G0, kept = SK.tube(V, T, kept_sts, bottom=0.0, taper_from=taper_from)
    N0 = SK.grid_normals(G0)
    hmin = SK.obstacle(tree, G0, N0)
    o = off(G0, N0, kept) if callable(off) else off
    h = SK.membrane(G0, N0, hmin, o, iters=LAST_MEMBRANE["iters"], length=LAST_MEMBRANE["length"])
    G = G0 + h[..., None] * N0
    G = flatten_bottom(G, SK.grid_normals(G), z_b)
    y_back = float(G[..., 1].max())
    y_front = float(G[..., 1].min())
    y_from = y_front + STRETCH_FROM
    k = 1.0
    for _ in range(8):
        Gs = toe_spring(stretch(G, y_from, k), b1, b5, z_b)
        err = float(Gs[..., 1].min()) - front_y       # > 0: the tip still behind where it should be
        if abs(err) < 0.02:
            break
        k += err / STRETCH_FROM
    length = float(Gs[..., 1].max() - Gs[..., 1].min())
    info = {"k": k, "stretch_from": y_from, "length": length, "y_back": y_back, "front_before": y_front,
            "front": float(Gs[..., 1].min()), "front_want": float(front_y)}
    return Gs, kept, info


def socked_envelope(V, T, tree, toe, L, collar_z=COLLAR_Z):
    """The loaded socked foot, the reference for the allowances: the loaded skin with its nails (V, T, F mm; tree its
    BVH) wrapped as the sock wraps it, at the sock's inner gap and its loaded thickness (sock.py's own membrane, not
    the last's stiffer one). Returns its points (n, 3, F mm). Its rings stop 1.6 mm short of the toes' tips (the sock's
    toe is closed by linking), so its front is not the socked toe's: socked_toe_y is."""
    sts, _ = SK.stations(V, top_z=collar_z, fine_from=toe["tip5"][1] + 10.0)
    G0, _ = SK.tube(V, T, sts, taper_from=toe["tip5"][1] + 10.0)
    N0 = SK.grid_normals(G0)
    reg = SK.regions(G0, N0, L, toe, float(G0[..., 1].max()))
    h = SK.membrane(G0, N0, SK.obstacle(tree, G0, N0), SK.OFFSET_MM + SK.thickness(reg, loaded=True),
                    length=SK.toe_cap_length_weight(G0, toe))
    return (G0 + h[..., None] * N0).reshape(-1, 3)


def socked_toe_y(V):
    """The standing, socked toe's front (y, F mm), where the toe allowance is measured from (Jeff, 2026-10-27): the
    loaded skin's foremost point (V: the loaded rendered surface with its nails) ahead by the sock's inner gap and its
    toe's thickness (the reinforced toe, 2.2 mm: the front of the toe is not under load)."""
    return float(np.asarray(V)[:, 1].min()) - (SK.OFFSET_MM + SK.THICK["toe"])


def insole_z():
    """The insole plane's height in frame F (mm): the loaded sock's outer sole, the gap and the pressed 1.8 mm under
    the floor the bare foot stands on."""
    return -(SK.OFFSET_MM + SK.THICK["sole"] * SK.LOADED_SOLE)


def groups(G, L, b1, b5, z_b):
    """§4.13's groups on the last's grid: last_heel (the seat and counter, behind 25 % L), last_ball (20 mm either side
    of the ball line), last_toe (ahead of it), last_instep (the top over 35-70 % L), last_collar (the ring at z 210)."""
    sm = S.smoothstep
    p, t, nrm = ball_line(b1, b5)
    d = (G[..., :2] - p) @ nrm
    y, z = G[..., 1], G[..., 2]
    N = SK.grid_normals(G)
    return {"last_heel": 1.0 - sm(-y, 0.23 * L, 0.27 * L),
            "last_ball": 1.0 - sm(np.abs(d), 18.0, 22.0),
            "last_toe": sm(d, 18.0, 22.0),
            "last_instep": sm(N[..., 2], 0.35, 0.6) * sm(-y, 0.33 * L, 0.37 * L) * (1.0 - sm(-y, 0.68 * L, 0.72 * L)),
            "last_collar": sm(z, COLLAR_Z - 6.0, COLLAR_Z - 2.0)}


# spec 02 §0 items 2-3 (2026-10-27): the real boot's seats (Lowa Zephyr: heel stack 36.3, forefoot 23.7 with the insole)
HEEL_SEAT, BALL_SEAT = 36.0, 24.0
HEEL_SEAT_AHEAD = 30.0               # the heel seat point, this far ahead of .Pternion (spec 02 §3.1)
# spec 01 §7.3 (spec 08 owns them): the hero headings and the ankle centres in plan, world mm
HERO = {"R": {"heading_deg": 85.0, "toward": -1.0, "ankle_xy": (-208.0, 75.0)},
        "L": {"heading_deg": 17.0, "toward": 1.0, "ankle_xy": (208.0, -75.0)}}


def seat(q, b1, b5, pternion, z_b, heel=HEEL_SEAT, ball=BALL_SEAT, ahead=HEEL_SEAT_AHEAD):
    """The last on the boot's footbed (spec 02 §4.1 step 2, 2026-10-27): turned heel-up about the line through .Ball1 and
    .Ball5 until its insole plane stands heel - ball mm higher at the heel seat point than on the line, then lifted so
    the line sits at `ball` and that point at `heel`. q (n, 3) frame F mm; returns (seated q, the angle in degrees)."""
    p, t, nrm = ball_line(b1, b5)
    H = np.array([pternion[0], pternion[1] - ahead])
    dH = float((H - p) @ nrm)
    a = math.asin((heel - ball) / abs(dH))
    q = np.asarray(q, float)
    s = (q[:, :2] - p) @ nrm
    h = q[:, 2] - z_b
    s2, h2 = s * math.cos(a) + h * math.sin(a), h * math.cos(a) - s * math.sin(a)
    out = q.copy()
    out[:, :2] = q[:, :2] + np.outer(s2 - s, nrm)
    out[:, 2] = ball + h2
    return out, math.degrees(a)


def hero_frame(side, ankle_f_seated):
    """Frame F of the posed foot: the hero heading, its origin set so the seated ankle centre lands on its plan
    position (spec 01 §7.3)."""
    from parts.p01 import footmetrics as fm
    hv = HERO[side]
    ang = math.radians(hv["heading_deg"])
    heading = np.array([hv["toward"] * math.sin(ang), -math.cos(ang), 0.0])
    f0 = fm.Frame(np.zeros(3), heading, side)
    a = f0.to_w(np.asarray(ankle_f_seated, float))
    tx, ty = hv["ankle_xy"]
    return fm.Frame(np.array([tx - a[0], ty - a[1], 0.0]), heading, side)
