"""Belt, round 6: an HSGI Cobra class 1.75 in rigger belt with its AustriAlpin Cobra buckle, two drop-leg
rigs (hanger, bound platform, thigh straps with ladder-locks and their running ends): on the right thigh, turned
to face forward in the hero pose, twin open-top polymer rifle-magazine carriers (slotted tan plates, tension
screws, shock cord over the spare PMAGs, soft cord tails); on the left thigh the drawn double rifle-mag pouch (two
flapped olive cells); a flapped pouch on the belt at the right front hip; and a mid-ride belt holster at the right
rear hip with the P9 sidearm (a P226-class pistol), hung tilted to the hip. Notes: scripts/parts/belt.md.

  "$SGT_BLENDER" -b --python scripts/parts/belt.py [-- --no-render]
  -> cache/parts/belt.blend (Part.Belt), cache/parts/belt.json, renders/belt/*.png

Method: the belt is a closed band over the trousers' waistband (convex hull of the waist section in the
trousers' tilted waist plane); the thigh straps are bands round the clothed thighs; the platforms are
semi-rigid slabs over a smoothed surface round each thigh that clears the trousers and their cargo pockets.
Hard items sit on those surfaces. The belt, hangers and straps are bound by weights from the body; the
platforms with everything on them are skinned rigidly to the thigh bone (upperleg02); round 6: the holster, the
pistol, the buckle and the right front pouch are mounted on the belt and the ladder-locks on their straps
(gear_common.mount_bind: the carrier's weights at the mount point on every vertex). Idempotent: it starts from
base.blend every time.
"""
import json
import math
import os
import sys

import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gear_common as G  # noqa: E402
from lib import gear_hardware as GH  # noqa: E402

PART, TAG = "Belt", "belt"

BELT_W, BELT_T = 44.5, 5.5                       # 1.75 in, two plies
WAIST_PLANE = ((0.0, 0.0, 1072.0), (0.0, -0.15, 1.0))   # the trousers' waist plane (trousers.py WAIST)
BELT_TOP_BELOW = 3.0                             # belt top 3 mm under the waistband's top edge
BUCKLE = (38.0, 10.0, 58.0)                      # along the belt, thick, across (Cobra FC45: 58 x 38 x 10)
BUCKLE_THETA = -9.0                              # deg: about 30 mm to his right of centre front
# Round 2: the right rig 40 deg (about 7 cm) inboard so its carriers face forward in the hero pose (the posed
# right thigh is turned out 43 deg); the carriers lower so the straps cross them at a third and three quarters
# of their height, as drawn; the left block narrower (130 wide platform, slim case on its narrow face).
PLATFORM = {"R": {"theta": -12.0, "top": 832.0, "h": 180.0, "w": 158.0, "straps": (792.0, 716.0)},
            "L": {"theta": 30.0, "top": 878.0, "h": 200.0, "w": 148.0, "straps": (702.0,)}}
PLATFORM_T, PLATFORM_LIFT = 8.0, 6.0             # laminate thickness; inner face over the trousers (straps under)
STRAP_W, STRAP_T, STRAP_LIFT = 38.0, 2.0, 2.2
CARRIER_DROP = 15.0                              # carrier body top below the platform's top edge
HANGER_W, HANGER_T = 38.0, 1.6
MAG_CARRIER = (76.0, 42.0, 140.0)                # HSGI polymer TACO class, broad side out
MAG_PLATE = (47.0, 3.0, 128.0)
PMAG_PROUD, PMAG = 53.0, (66.0, 25.0)
MAG_POUCH = (64.0, 38.0, 172.0)                  # round 6: one cell of the left hip's double rifle-mag pouch (drawn: two
                                                 # tall flapped olive cells side by side; round 1-5 built a frag pouch and
                                                 # a hard case there, which the critics read as "a box beside a block")
MAG_POUCH_U = (-34.0, 34.0)                      # the two cells' centres across the left platform
FLAP_DROP = 48.0                                 # a flap's drop down the pouch face
RF_POUCH = (70.0, 36.0, 118.0)                   # round 6: the right front hip's flapped pouch on the belt (drawn there,
RF_THETA = -62.0                                 # above the thigh rig; missing until round 6)
LOCK_T = 3.5                                     # the ladder-locks' frame thickness (GH.ladder_lock(..., 3.5, ...))
HOLSTER_THETA = -122.0                           # deg round the belt: right rear hip
HOLSTER_GAP = 1.0                                # round 6: its back 1 mm off the belt and trousers (2.5, plus a pelvis-bone
                                                 # bind while the belt followed the thigh, left it hinged into the air)
HOLSTER = (60.0, 50.0, 190.0)                    # along the belt, out, tall (Safariland 6378 ALS class, P226)
P9_SLIDE = (34.0, 30.0, 196.0)                   # P226: slide length 196, height about 34, width 30
P9_GRIP = (105.0, 32.0, 48.0)                    # grip length, width, depth

COL = {"belt": "#2a2724", "buckle": "#1b1b1c", "hanger_tan": "#736054", "hanger_black": "#1e1c1a",
       "platform": "#24221f", "strap": "#161515", "poly_black": "#24211e", "poly_tan": "#816f5f",
       "pmag": "#1e1d1c", "frag": "#463e34", "case": "#3a3e40", "holster": "#1f1d1c", "slide": "#4f5050",
       "frame": "#2c2c2c", "metal": "#3b3a38", "steel": "#8d8a85", "tan_metal": "#8a7350", "case_dark": "#232526"}
# Materials round (round 5, 2026-11-15; COL stays the solid-view colour): black nylon rigger belt and straps,
# black Cordura platforms, textured black polymer carrier bodies, holster and case, the magazine carriers' tan
# moulded plates, gunmetal hardware, coyote and black hangers, olive Cordura frag pouch. The left rig dustier.
_KIT = {"wear": "belt.kit", "dust__amount": 0.5}
MATERIALS = {
    "Belt.Mat.Belt": ("Webbing.Nylon.Black", "Belt", dict(_KIT)),
    "Belt.Mat.Strap": ("Webbing.Nylon.Black", "Strap", dict(_KIT)),
    "Belt.Mat.HangerBlack": ("Webbing.Nylon.Black", "HangerBlack", dict(_KIT)),
    "Belt.Mat.HangerTan": ("Webbing.Nylon.Coyote", "HangerTan", {}),
    "Belt.Mat.Platform": ("Cordura.500D.Black", "Platform", dict(_KIT)),
    "Belt.Mat.Frag": ("Cordura.500D.OliveBrown", "Frag", {}),
    "Belt.Mat.PolyBlack": ("Polymer.Black.Textured", "PolyBlack", {"dust__amount": 0.2}),
    "Belt.Mat.Holster": ("Polymer.Black.Textured", "Holster", {}),
    "Belt.Mat.Pmag": ("Polymer.Black.Textured", "Pmag", {"albedo_hex": "#2e2d2b"}),
    "Belt.Mat.Case": ("Polymer.Black.Textured", "Case", {"albedo_hex": "#34383a"}),
    "Belt.Mat.CaseDark": ("Polymer.Black.Textured", "CaseDark", {}),
    "Belt.Mat.PolyTan": ("Polymer.Tan.Moulded", "PolyTan", {"albedo_hex": "#3e382f"}),
    "Belt.Mat.TanMetal": ("Polymer.Tan.Moulded", "TanMetal", {"rough": 0.45}),
    "Belt.Mat.Buckle": ("Metal.Gunmetal", "Buckle", {}),
    "Belt.Mat.Metal": ("Metal.Gunmetal", "Metal", {}),
    "Belt.Mat.Slide": ("Metal.Gunmetal", "Slide", {}),
    "Belt.Mat.Steel": ("Metal.Gunmetal", "Steel", {"f0": (0.40, 0.40, 0.41), "aniso": 0.0}),
    "Belt.Mat.Frame": ("Polymer.Black.Textured", "Frame", {}),
}


def _frame(origin, xa, nn, up):
    """4 x 4 with columns x = xa, y = nn (outward), z = up at origin (the items' frame on a platform)."""
    M = np.eye(4)
    M[:3, :3] = np.column_stack([xa, nn, up])
    M[:3, 3] = origin
    return M


def plate_frame(origin, xa, up, nn):
    """4 x 4 for a lib.gear_hardware piece lying on a face: x across, y up, z out of the face."""
    M = np.eye(4)
    M[:3, :3] = np.column_stack([xa, up, nn])
    M[:3, 3] = origin
    return M


def slotted_plate():
    """The carriers' tan face plate, 47 x 128 x 3 (x across, y up, z out), with three 25 x 6 slots 45, 73
    and 101 mm below its top (spec 14 section 3.4), as a lib.gear_hardware grid solid."""
    w, h, t = MAG_PLATE[0], MAG_PLATE[2], MAG_PLATE[1]
    xs = [-w / 2, -12.5, 12.5, w / 2]
    ys = [-h / 2]
    for c in (101.0, 73.0, 45.0):
        yc = h / 2 - c
        ys += [yc - 3.0, yc + 3.0]
    ys.append(h / 2)
    S = np.ones((3, len(ys) - 1), bool)
    for j in (1, 3, 5):
        S[1, j] = False
    V, F = GH.grid_solid(xs, ys, S, t)
    return GH.Piece(V, F, bevel=(0.8, 2, 30.0), kind="plate", dims={"w": w, "h": h, "t": t})


def flapped_pouch(nm, coll, size, Mf, mat, snap_mat, strap_mat, rows=(), drop=FLAP_DROP):
    """Round 6: a Cordura pouch cell standing on its back face (frame Mf: x across, y out, z up, centre of the
    body): the body, an L flap (a lid over the top and a drop down the face, both hugging the body), a snap on
    the drop and webbing rows flush on the face. Returns the objects."""
    xa, nn, up, ctr = Mf[:3, 0], Mf[:3, 1], Mf[:3, 2], Mf[:3, 3]
    w, d, h = size
    out = [G.rbox(nm, coll, size, Mf, mat, bevel_mm=7.0, taper=(0.97, 0.98))]
    top = ctr + up * (h / 2.0)
    out.append(G.boxes(f"{nm}.Flap", coll,
                       [((w + 2.0, d + 2.5, 6.0), _frame(top + up * 2.0 + nn * 0.6, xa, nn, up)),
                        ((w + 2.0, 5.0, drop), _frame(top + nn * (d / 2.0 + 1.6) - up * (drop / 2.0 - 3.0), xa, nn, up))],
                       mat, bevel_mm=2.0))
    out.append(G.cyl(f"{nm}.Snap", coll, top + nn * (d / 2.0 + 4.0) - up * (drop - 13.0), nn, 6.5, 1.8, snap_mat,
                     n=20, bevel_mm=0.6, dome=1.0))
    for j, zr in enumerate(rows):
        out.append(G.rbox(f"{nm}.PALS.{j + 1}", coll, (w * 0.97 + 1.0, 1.6, 25.0),
                          _frame(top + nn * (d / 2.0 * 0.98 + 0.5) - up * zr, xa, nn, up), strap_mat, bevel_mm=0.5))
    return out


def hang_frame(p, d, t, n, size, top_off, under, drop=None):
    """Round 6: the frame of an item hanging from the belt (holster, pouch): its top `top_off` above the belt's
    mid line at p, its back face lying on the belt there AND on what lies under its lower part (the hip, a cargo
    pocket), so it tilts with the body instead of standing straight down and touching at one point. Columns: x
    along the belt (t), y outward, z up the item."""
    drop = drop if drop is not None else 0.8 * size[2]
    q0 = p - n * drop
    lo, _nl = under.hit(q0 + d * 200.0, -d, 400.0)
    ax = n if lo is None else G.unit(p - lo)
    ax = G.unit(ax) if np.dot(ax, n) > 0.5 else n            # never more than 60 deg off the waist plane's normal
    dd = G.unit(d - ax * np.dot(d, ax))
    xx = G.unit(np.cross(dd, ax))
    if np.dot(xx, t) < 0:
        xx = -xx
    M = np.eye(4)
    M[:3, :3] = np.column_stack([xx, dd, ax])
    M[:3, 3] = p + dd * (size[1] / 2.0 + 1.0) + ax * (top_off - size[2] / 2.0)
    return M


def settle(M, size, bvh, gap, grid=7):
    """Round 6: lay a hanging item's back face on the real surfaces under it (belt, trousers with their pockets;
    Solidify on): rays from the back face inward find the nearest contact in its upper and its lower third; the
    item's axis is turned to the line through the two and then moved in until the closest point is `gap` off.
    G.seat against an offset plane of layers left the round-5 holster 6-12 mm off the belt."""
    M = np.array(M, float)
    for _ in range(2):
        xx, dd, ax, c = M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3]
        top, bot, allh = None, None, []
        for a in np.linspace(-0.4, 0.4, grid):
            for b in np.linspace(-0.48, 0.48, grid):
                q = c - dd * size[1] / 2.0 + xx * a * size[0] + ax * b * size[2]
                h = bvh.ray_cast(Vector(q + dd * 30.0), Vector(-dd), 150.0)
                if h[0] is None:
                    continue
                dist = h[3] - 30.0
                allh.append(dist)
                if b > 0.15 and (top is None or dist < top[0]):
                    top = (dist, np.array(h[0]))
                if b < -0.15 and (bot is None or dist < bot[0]):
                    bot = (dist, np.array(h[0]))
        if top is not None and bot is not None:
            an = G.unit(top[1] - bot[1])
            if np.dot(an, ax) > 0.8:
                dn = G.unit(dd - an * np.dot(dd, an))
                xn = G.unit(np.cross(dn, an))
                if np.dot(xn, xx) < 0:
                    xn = -xn
                M[:3, 0], M[:3, 1], M[:3, 2] = xn, dn, an
        if allh:
            M[:3, 3] = M[:3, 3] - M[:3, 1] * (min(allh) - gap)
    return M


def belt_frame():
    co, no = WAIST_PLANE
    n = G.unit(no)
    ey = G.unit(np.array([0.0, 1.0, 0.0]) - n * n[1])
    ex = np.cross(ey, n)
    if ex[0] < 0:
        ex = -ex
    return np.asarray(co, float), n, ex, ey


def main(render=True):
    import bpy
    body, rig = C.open_base()
    bd = C.body_data(body)
    clothing = G.load_clothing(rig)
    under_w, note_w = G.clothing_under(bd, clothing, "waist")
    under_l, note_l = G.clothing_under(bd, clothing, "leg")
    G.say("waist:", note_w, "| legs:", note_l)
    coll = C.part_collection(PART)
    M = {k: G.mat(f"Belt.Mat.{k.title().replace('_', '')}", v) for k, v in COL.items()}
    out = {"under": {"waist": note_w, "legs": note_l}}
    rigid, soft, mounts = [], [], []     # mounts: (object, the soft-bound carrier it sits on, rest point mm)

    # ---------------------------------------------------------------- belt band
    co, n, ex, ey = belt_frame()
    vc = -BELT_TOP_BELOW - BELT_W / 2.0                  # belt centre offset along the plane normal
    pf, _ = under_w.hit(co + n * vc - ey * 600.0, ey)
    pb, _ = under_w.hit(co + n * vc + ey * 600.0, -ey)
    cy = (np.dot(pf - co, ey) + np.dot(pb - co, ey)) / 2.0
    centre = co + ey * cy

    def dir_b(th):
        return math.sin(th) * ex - math.cos(th) * ey

    ths = np.linspace(0, 2 * math.pi, 96, endpoint=False)
    vs = np.linspace(vc - BELT_W / 2.0, vc + BELT_W / 2.0, 5)
    R = []
    for v in vs:
        o = centre + n * v
        Q = []
        for th in np.linspace(0, 2 * math.pi, 180, endpoint=False):
            d = dir_b(th)
            p, _ = under_w.hit(o + d * 450.0, -d, 450.0)
            if p is not None:
                Q.append((np.dot(p - o, ex), np.dot(p - o, ey)))
        Q = np.array(Q)
        ang = np.arctan2(-np.cos(ths), np.sin(ths))
        R.append(G.convex_radii(0.0, 0.0, Q, ang))
    R = G.fill_nan(np.array(R))
    rmax_row = R.max(0)                                  # a stiff belt: the widest row everywhere
    Pin = np.array([[centre + n * v + dir_b(th) * (r + 1.0) for th, r in zip(ths, rmax_row)] for v in vs])
    Pout = np.array([[centre + n * v + dir_b(th) * (r + 1.0 + BELT_T) for th, r in zip(ths, rmax_row)] for v in vs])
    V, F = G.slab_from_grid(Pin, np.zeros_like(Pin), 0.0, closed_u=True, outer=Pout)
    belt = G.new_mesh("Belt.Belt", V, F, coll, M["belt"], bevel_mm=1.5)
    soft.append(belt)
    girth = float(np.sum(np.linalg.norm(np.diff(np.vstack([Pin[2], Pin[2][:1]]), axis=0), axis=1)))
    out["belt"] = {"inner_girth_mm": round(girth), "front_top_z": round(float((centre + n * (vc + BELT_W / 2) +
                                                                               dir_b(0) * rmax_row[0])[2]))}

    def belt_point(th_deg, v=vc, off=0.0):
        th = math.radians(th_deg)
        r = float(np.interp(th % (2 * math.pi), np.append(ths, 2 * math.pi), np.append(rmax_row, rmax_row[0])))
        d = dir_b(th)
        t = math.cos(th) * ex + math.sin(th) * ey         # tangent toward +theta
        return centre + n * v + d * (r + 1.0 + BELT_T + off), d, t

    # buckle
    p, d, t = belt_point(BUCKLE_THETA, off=BUCKLE[1] / 2.0 + 0.4)
    Mb = np.eye(4)
    Mb[:3, :3] = np.column_stack([t, d, n])
    Mb[:3, 3] = p
    Mb = G.seat(G.Under([(G.objects_bvh([belt]), 0.0)]), Mb, BUCKLE, gap=0.4)
    ob = G.rbox("Belt.Buckle", coll, BUCKLE, Mb, M["buckle"], bevel_mm=2.0)
    mounts.append((ob, belt, Mb[:3, 3]))       # round 6: rides the belt as one piece (soft-bound it sheared 4 mm off it)

    # ---------------------------------------------------------------- drop-leg rigs
    for side, sgn in (("R", -1.0), ("L", 1.0)):
        P = PLATFORM[side]
        top = C.bone_mm(f"upperleg02.{side}")
        kn = C.bone_mm(f"lowerleg01.{side}")
        d_t, f_t, l_t = G.limb_frame(top, kn, side)
        bone = f"upperleg02.{side}"

        def s_of(z):
            return (top[2] - z) / (-d_t[2])
        s_top, s_bot = s_of(P["top"]), s_of(P["top"] - P["h"])
        th0 = math.radians(P["theta"])
        # thigh straps first: bands round the clothed thigh (this leg's trousers and skin only)
        keep = C.weight_sum(bd, lambda nm, sd=side: C.is_leg(nm) and nm.endswith(f".{sd}")) > 0.3
        layers = [(G.skin_bvh(bd, keep), 2.0)]
        if "trousers" in clothing:
            layers.insert(0, (G.region_bvh(bd, list(clothing["trousers"].all_objects), keep), 0.8))
        under_side = G.Under(layers)
        straps, rings = [], []
        for zs in P["straps"]:
            ss = s_of(zs)
            ring = G.LimbSurf(under_side, top, d_t, f_t, l_t, (-math.pi, math.pi), (ss - 24.0, ss + 24.0), nth=144,
                              ns=17, iters=2, rmax=220.0)
            # (round 2: inward rays against this leg's trousers, pockets and skin only; round 1's rays from 140 mm
            # out on the medial side met the other thigh near the crotch and made a spike)
            ob = G.slab(f"Belt.Rig.{side}.Strap.{len(straps) + 1}", coll, ring.surf(STRAP_LIFT), None,
                        ss - STRAP_W / 2.0, ss + STRAP_W / 2.0, STRAP_T, M["strap"], nu=144, nv=8, bevel_mm=0.6,
                        closed_u=True)
            soft.append(ob)
            straps.append(ob)
            rings.append((ring, ss))
        # the platform: over the trousers (shell and cargo pockets) and the straps
        under_p = G.Under(list(under_l.layers) + [(G.objects_bvh(straps), 0.5)])
        leg = G.LimbSurf(under_p, top, d_t, f_t, l_t, (th0 - math.radians(80), th0 + math.radians(80)),
                         (s_top - 20.0, s_bot + 20.0), nth=64, ns=50, iters=12, rmax=260.0)
        r0 = float(leg.F(th0, (s_top + s_bot) / 2.0)) + PLATFORM_LIFT
        hw = P["w"] / 2.0

        def psurf(off):
            f = leg.surf(off)

            def g(u, v):
                return f(th0 + u / r0, v)
            return g

        def corner_hw(v, hw=hw):
            """The platform's outline: corners rounded 15 mm."""
            e = min(v - s_top, s_bot - v)
            if e >= 15.0:
                return hw
            return hw - 15.0 + math.sqrt(max(0.0, 225.0 - (15.0 - e) ** 2))
        plat = G.slab(f"Belt.Rig.{side}.Platform", coll, psurf(PLATFORM_LIFT), lambda v: (-corner_hw(v), corner_hw(v)),
                      s_top, s_bot, PLATFORM_T, M["platform"], nu=24, nv=30, bevel_mm=3.0)
        rigid.append((plat, bone))
        # bound edge: 12 mm tape rolled over the platform's rim
        vs_ = np.linspace(s_top, s_bot, 40)
        uv = ([(corner_hw(v), v) for v in vs_] + [(u, s_bot) for u in np.linspace(corner_hw(s_bot), -corner_hw(s_bot), 24)[1:-1]]
              + [(-corner_hw(v), v) for v in vs_[::-1]] + [(u, s_top) for u in np.linspace(-corner_hw(s_top), corner_hw(s_top), 24)[1:-1]])
        rim = [psurf(PLATFORM_LIFT + PLATFORM_T * 0.5)(u, v)[0] for (u, v) in uv]
        ob = G.tube(f"Belt.Rig.{side}.Platform.Binding", coll, rim, PLATFORM_T * 0.5 + 0.8, M["strap"], closed=True,
                    sides=8)
        rigid.append((ob, bone))
        plat_under = G.Under([(G.objects_bvh([plat]), 0.0)])
        n_c = psurf(PLATFORM_LIFT + PLATFORM_T)(0.0, 0.5 * (s_top + s_bot))[1]

        def on_plat(u, s, size, extra=0.0, square=0.5):
            """Frame of an item on the platform's outer face at (u mm across, s along the thigh): x across,
            y outward (the local normal turned `square` of the way to the platform's centre normal, so the
            items face one way, as drawn), z up the thigh; seated clear of the platform."""
            p, nn = psurf(PLATFORM_LIFT + PLATFORM_T + 0.5 + extra)(u, s)
            nn = G.unit((1.0 - square) * nn + square * n_c)
            up = G.unit(-d_t - nn * np.dot(-d_t, nn))
            xa = G.unit(np.cross(up, nn))
            Mx = np.eye(4)
            Mx[:3, :3] = np.column_stack([xa, nn, up])
            Mx[:3, 3] = p + nn * size[1] / 2.0
            return G.seat(plat_under, Mx, size, gap=0.5)
        if side == "R":
            for k, u in enumerate((-39.0, 39.0)):
                nm = f"Belt.Rig.R.Carrier.{k + 1}"
                s_c = s_top + CARRIER_DROP + MAG_CARRIER[2] / 2.0
                Mc = on_plat(u, s_c, MAG_CARRIER, square=0.65)
                xa, nn, up, ctr = Mc[:3, 0], Mc[:3, 1], Mc[:3, 2], Mc[:3, 3]
                ob = G.rbox(nm, coll, MAG_CARRIER, Mc, M["poly_black"], bevel_mm=5.0)
                rigid.append((ob, bone))
                # tan face plate 47 x 128 x 3 with three 25 x 6 slots, standing 1.5 proud on its spacer
                py = MAG_CARRIER[1] / 2.0 + 1.5 + MAG_PLATE[1] / 2.0
                pc = ctr + nn * py + up * (MAG_CARRIER[2] / 2.0 - 6.0 - MAG_PLATE[2] / 2.0)
                ob = G.hw_object(f"{nm}.Plate", coll, slotted_plate(), plate_frame(pc, xa, up, nn), M["poly_tan"])
                rigid.append((ob, bone))
                ob = G.rbox(f"{nm}.Spacer", coll, (MAG_PLATE[0] - 4.0, 1.6, MAG_PLATE[2] - 4.0),
                            _frame(ctr + nn * (MAG_CARRIER[1] / 2.0 + 0.7) + up * (MAG_CARRIER[2] / 2.0 - 6.0 - MAG_PLATE[2] / 2.0), xa, nn, up),
                            M["poly_black"], bevel_mm=0.6)
                rigid.append((ob, bone))
                # tension screw (dome, 8 mm) 25 below the plate top
                ps = pc + nn * (MAG_PLATE[1] / 2.0) + up * (MAG_PLATE[2] / 2.0 - 25.0)
                ob = G.hw_object(f"{nm}.Screw", coll, GH.screw_head(8.0, 2.5, kind="dome", socket=0), plate_frame(ps, xa, up, nn),
                                 M["steel"])
                rigid.append((ob, bone))
                # the spare PMAG, 53 proud, with its floor plate
                mtop = ctr + up * (MAG_CARRIER[2] / 2.0)
                ob = G.boxes(f"{nm}.PMAG", coll,
                             [((PMAG[0], PMAG[1], PMAG_PROUD), _frame(mtop + up * (PMAG_PROUD / 2.0 - 2.0), xa, nn, up)),
                              ((PMAG[0] + 4.0, PMAG[1] + 4.0, 8.0), _frame(mtop + up * (PMAG_PROUD - 4.0), xa, nn, up))],
                             M["pmag"], bevel_mm=2.0)
                rigid.append((ob, bone))
                # shock cord: a loop over the magazine's floor plate from the carrier's sides
                yy = 4.0
                loop = [ctr + xa * (sg * (MAG_CARRIER[0] / 2.0 + 2.0)) + nn * yy + up * (MAG_CARRIER[2] / 2.0 - 30.0)
                        for sg in (-1,)]
                loop += [mtop + xa * (-MAG_CARRIER[0] / 2.0 - 1.0) + nn * yy + up * 8.0,
                         mtop + xa * (-PMAG[0] / 2.0 - 3.5) + nn * yy + up * (PMAG_PROUD + 3.0),
                         mtop + nn * yy + up * (PMAG_PROUD + 3.0),
                         mtop + xa * (PMAG[0] / 2.0 + 3.5) + nn * yy + up * (PMAG_PROUD + 3.0),
                         mtop + xa * (MAG_CARRIER[0] / 2.0 + 1.0) + nn * yy + up * 8.0,
                         ctr + xa * (MAG_CARRIER[0] / 2.0 + 2.0) + nn * yy + up * (MAG_CARRIER[2] / 2.0 - 30.0)]
                ob = G.tube(f"{nm}.Cord", coll, loop, 2.0, M["strap"], sides=8, step=3.0)
                rigid.append((ob, bone))
                if k == 1:
                    # the outer carrier's cord tails below it, with cord ends (the drawn tan tips)
                    for j, sx in enumerate((-12.0, 12.0)):
                        # round 6: short soft tails that droop back onto the platform (52 mm rods stood in the air)
                        b0 = ctr - up * (MAG_CARRIER[2] / 2.0 - 2.0) + xa * sx + nn * (MAG_CARRIER[1] / 2.0 - 8.0)
                        back = MAG_CARRIER[1] - 8.0 + 0.5 - 2.0 - 0.3       # under the carrier, back to the platform face
                        tail = [b0, b0 - up * 4.0 - nn * (0.35 * back), b0 - up * 10.0 - nn * (0.75 * back) + xa * (sx * 0.05),
                                b0 - up * 20.0 - nn * back + xa * (sx * 0.1)]
                        ob = G.tube(f"{nm}.Tail.{j + 1}", coll, tail, 2.0, M["strap"], sides=8, step=1.5)
                        rigid.append((ob, bone))
                        ob = G.cyl(f"{nm}.CordEnd.{j + 1}", coll, tail[-1] + nn * 2.2, -up, 4.0, 12.0, M["tan_metal"],
                                   n=12, bevel_mm=0.8)
                        rigid.append((ob, bone))
            hanger_mat = M["hanger_tan"]
        else:
            # round 6: the drawn double rifle-mag pouch: two tall flapped olive cells side by side on the platform
            for k, u in enumerate(MAG_POUCH_U):
                Mf = on_plat(u, s_top + 6.0 + MAG_POUCH[2] / 2.0, MAG_POUCH, square=0.5)
                for ob in flapped_pouch(f"Belt.Rig.L.MagPouch.{k + 1}", coll, MAG_POUCH, Mf, M["frag"], M["steel"],
                                        M["strap"], rows=(96.0, 134.0)):
                    rigid.append((ob, bone))
            hanger_mat = M["hanger_black"]
        # ladder-locks on the thigh straps, on the running end at the platform's medial edge (right) or at the
        # medial front of the thigh (left), the frame tangent to the thigh
        for j, (ring, ss) in enumerate(rings):
            thl = th0 - (hw + 32.0) / r0 if side == "R" else math.radians(-30.0)
            # round 6: the frame lies on the strap (its centre was 5 mm out: it stood 3-4 mm off the strap and read as
            # an empty slider), and the strap's running end comes up through it over the centre bar and runs on,
            # away from the platform, as a doubled tail lying on the strap
            pl, nl = ring.surf(STRAP_LIFT + STRAP_T + 0.2)(thl, ss)
            ob = G.hw_object(f"Belt.Rig.{side}.LadderLock.{j + 1}", coll, GH.ladder_lock(50.0, 32.0, 4.0, LOCK_T, 2),
                             G.frame(pl + nl * (LOCK_T / 2.0), -d_t, nl), M["metal"])
            mounts.append((ob, straps[j], pl))
            r_ring = float(np.linalg.norm(pl - (top + d_t * ss)))
            sgn_run = -1.0 if side == "R" else 1.0
            offs = np.linspace(-6.0, 70.0, 16)
            th_t = thl + sgn_run * offs / max(r_ring, 1.0)
            tp = [ring.surf(STRAP_LIFT + STRAP_T + 0.15)(th, ss) for th in th_t]
            lift_t = [LOCK_T + 0.3 if abs(k) < 14.0 else 0.15 for k in offs]
            path = np.array([q + n_ * lt for (q, n_), lt in zip(tp, lift_t)])
            for k_ in range(1, len(path) - 1):          # ease the climb over the frame
                path[k_] = 0.25 * path[k_ - 1] + 0.5 * path[k_] + 0.25 * path[k_ + 1]
            ob = G.strip(f"Belt.Rig.{side}.Strap.{j + 1}.Tail", coll, path, [n_ for _, n_ in tp], STRAP_W - 2.0, 1.8,
                         M["strap"], bevel_mm=0.4)
            soft.append(ob)
        # hanger: from the belt's lower edge above the platform down to the platform's top edge
        # it runs between the thigh and the items' tops and enters the platform's top edge from behind
        pt, nt = psurf(PLATFORM_LIFT + PLATFORM_T * 0.5 - HANGER_T * 0.5)(0.0, s_top - 2.0)
        az = math.degrees(math.atan2(pt[0] - centre[0], -(pt[1] - centre[1])))
        pb_, db, tb = belt_point(az, v=vc - BELT_W / 2.0 + 6.0, off=0.3)
        path = [pb_ + n * 10.0, pb_]
        for k in range(1, 15):
            q = pb_ + (pt - pb_) * k / 14.0
            hq, _ = under_l.hit(q + nt * 120.0, -nt, 240.0)
            if hq is not None:
                q = q + nt * max(0.0, np.dot(hq - q, nt) + 1.0)
            path.append(q)
        path = np.array(path)
        nrm = [db] * 2 + [nt] * (len(path) - 2)
        ob = G.strip(f"Belt.Rig.{side}.Hanger", coll, path, nrm, HANGER_W, HANGER_T, hanger_mat, bevel_mm=0.4)
        soft.append(ob)
        out[f"rig_{side}"] = {"theta_deg": P["theta"], "platform_z": [P["top"], P["top"] - P["h"]],
                              "platform_w": P["w"], "platform_radius_mm": round(r0, 1), "straps_z": list(P["straps"]),
                              "bone": bone}

    # ---------------------------------------------------------------- holster and P9 at the right rear hip
    p, d, t = belt_point(HOLSTER_THETA, off=0.0)
    top_off = BELT_W / 2.0 + 3.0
    under_h = G.Under([(G.objects_bvh([belt]), 0.6)] + list(under_w.layers) + list(under_l.layers))
    Mh = hang_frame(p, d, t, n, HOLSTER, top_off, under_h)
    Mh = G.seat(under_h, Mh, HOLSTER, gap=HOLSTER_GAP)
    real = G.objects_bvh([belt] + (list(clothing["trousers"].all_objects) if "trousers" in clothing else []))
    Mh = settle(Mh, HOLSTER, real, HOLSTER_GAP)
    fwd, d, up = Mh[:3, 0], Mh[:3, 1], Mh[:3, 2]           # +x on his right side runs toward the front
    hol = G.rbox("Belt.Holster", coll, HOLSTER, Mh, M["holster"], bevel_mm=6.0)
    # open the holster's mouth (the top face) so the pistol sits inside it, and give it walls
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(hol.data)
    zc = Mh[:3, 3]
    topf = [f for f in bm.faces if np.dot(np.array(f.calc_center_median()) * 1000.0 - zc, up) > HOLSTER[2] / 2.0 - 0.5]
    bmesh.ops.delete(bm, geom=topf, context="FACES_ONLY")
    bm.to_mesh(hol.data)
    bm.free()
    hol.modifiers.clear()
    G.C.add_mod(hol, "SOLIDIFY", "Solidify", thickness=2.5 * G.MM, offset=-1.0, use_even_offset=True, use_rim=True)
    bw = hol.modifiers.new("Bevel", "BEVEL")
    bw.width, bw.segments, bw.limit_method = 1.5 * G.MM, 2, "ANGLE"
    # pistol, muzzle down: slide inside the holster, its rear 16 mm and the grip above the mouth
    slide_c = Mh[:3, 3] + up * (HOLSTER[2] / 2.0 + 16.0 - P9_SLIDE[2] / 2.0)
    Ms = np.eye(4)
    Ms[:3, :3] = np.column_stack([fwd, d, up])
    Ms[:3, 3] = slide_c
    g_ax = G.unit(-fwd * math.cos(math.radians(14.0)) + up * math.sin(math.radians(14.0)))   # rearward, raked
    g_base = slide_c + up * (P9_SLIDE[2] / 2.0 + 10.0) - fwd * 6.0
    Mg = np.eye(4)
    Mg[:3, :3] = np.column_stack([g_ax, d, np.cross(g_ax, d)])
    Mg[:3, 3] = g_base + g_ax * (P9_GRIP[0] / 2.0 + 4.0)
    p9 = G.boxes("Belt.P9", coll, [((P9_SLIDE[0], P9_SLIDE[1], P9_SLIDE[2]), Ms), (P9_GRIP, Mg)], M["slide"],
                 bevel_mm=3.0)
    # round 6: bound by weights like the belt and the trousers under it (rigid on pelvis.R, round 1-5, it stayed while
    # the hip under it followed the turned-out thigh; mounted on the belt, the first try, its lower half still met
    # the hip or left it): the kydex bends a little over the hip in the pose, hidden at the rear
    soft.append(hol)
    soft.append(p9)
    out["holster"] = {"theta_deg": HOLSTER_THETA, "centre": [round(float(v)) for v in Mh[:3, 3]], "bind": "weights"}

    # ---------------------------------------------------------------- round 6: the right front hip pouch on the belt
    p, d, t = belt_point(RF_THETA, off=0.0)
    under_r = G.Under([(G.objects_bvh([belt]), 0.4)] + list(under_w.layers) + list(under_l.layers))
    Mr = hang_frame(p, d, t, n, RF_POUCH, BELT_W / 2.0 + 4.0, under_r)
    Mr = G.seat(under_r, Mr, RF_POUCH, gap=0.6)
    Mr = settle(Mr, RF_POUCH, real, 0.6)
    for ob in flapped_pouch("Belt.Pouch.RF", coll, RF_POUCH, Mr, M["frag"], M["steel"], M["strap"], rows=(52.0,),
                            drop=40.0):
        soft.append(ob)              # a Cordura pouch over the hip: weights, so the hip never pushes into it
    out["pouch_rf"] = {"theta_deg": RF_THETA, "centre": [round(float(v)) for v in Mr[:3, 3]], "bind": "weights"}

    # ---------------------------------------------------------------- bind
    for ob in soft:
        G.soft_bind(ob, body, rig)
    for ob, bone in rigid:
        G.rigid_bind(ob, rig, bone)
    out["mounted"] = {}
    for ob, carrier, pt in mounts:
        out["mounted"][ob.name] = {"on": carrier.name, "weights": G.mount_bind(ob, rig, carrier, pt)}
    out["rigid"] = {ob.name: bone for ob, bone in rigid}
    out["soft"] = [ob.name for ob in soft]
    G.say(json.dumps({k: v for k, v in out.items() if k not in ("rigid", "soft", "mounted")}))
    out["materials"] = C.library_pass(coll, PART, MATERIALS, side_dust={"L": 1.0, "R": 0.8}, say_tag=TAG)
    if render:
        rep = G.finish_part(TAG, coll, body, rig, clothing, (0.0, 0.0, 860.0), 900.0,
                            ["ref.belt_hips", "ref.legs_knees", "ref.soldier_full"], extra=out)
        out["check"] = rep
        with open(os.path.join(C.PARTS_DIR, f"{TAG}.json"), "w") as f:
            json.dump(out, f, indent=1)
    else:
        C.save_part(TAG, coll, extra=out)
    return out


if __name__ == "__main__":
    main(render="--no-render" not in C._argv())
