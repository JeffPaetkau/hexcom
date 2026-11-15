"""Belt, round 2: an HSGI Cobra class 1.75 in rigger belt with its AustriAlpin Cobra buckle, two drop-leg
rigs (hanger, bound platform, thigh straps with ladder-locks): on the right thigh, turned to face forward in
the hero pose, twin open-top polymer rifle-magazine carriers (slotted tan plates, tension screws, shock cord
over the spare PMAGs, cord tails); on the left thigh a vertical double frag pouch (flap, snap, webbing rows)
and a slim hard case (lip, latch, elastic cradle bands); and a mid-ride belt holster at the right rear hip
with the P9 sidearm (a P226-class pistol). Notes: scripts/parts/belt.md.

  "$SGT_BLENDER" -b --python scripts/parts/belt.py [-- --no-render]
  -> cache/parts/belt.blend (Part.Belt), cache/parts/belt.json, renders/belt/*.png

Method: the belt is a closed band over the trousers' waistband (convex hull of the waist section in the
trousers' tilted waist plane); the thigh straps are bands round the clothed thighs; the platforms are
semi-rigid slabs over a smoothed surface round each thigh that clears the trousers and their cargo pockets.
Hard items sit on those surfaces. The belt, hangers and straps are bound by weights from the body; the
platforms with everything on them are skinned rigidly to the thigh bone (upperleg02), the holster and the
pistol to the bone that rules the hip under them. Idempotent: it starts from base.blend every time.
"""
import json
import math
import os
import sys

import numpy as np

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
            "L": {"theta": 30.0, "top": 878.0, "h": 200.0, "w": 132.0, "straps": (702.0,), "frag_u": -30.0,
                  "case_u": 39.0}}
PLATFORM_T, PLATFORM_LIFT = 8.0, 6.0             # laminate thickness; inner face over the trousers (straps under)
STRAP_W, STRAP_T, STRAP_LIFT = 38.0, 2.0, 2.2
CARRIER_DROP = 15.0                              # carrier body top below the platform's top edge
HANGER_W, HANGER_T = 38.0, 1.6
MAG_CARRIER = (76.0, 42.0, 140.0)                # HSGI polymer TACO class, broad side out
MAG_PLATE = (47.0, 3.0, 128.0)
PMAG_PROUD, PMAG = 53.0, (66.0, 25.0)
FRAG = (70.0, 66.0, 182.0)                       # vertical double M67 footprint (two 64 mm grenades + walls)
FLAP_DROP = 48.0                                 # the flap's drop down the pouch face
CASE = (52.0, 46.0, 178.0)                       # slim polymer utility case, narrow face to the camera (drawn 51 wide)
HOLSTER_THETA = -122.0                           # deg round the belt: right rear hip
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
    rigid, soft = [], []

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
    soft.append(ob)

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
                        b0 = ctr - up * (MAG_CARRIER[2] / 2.0 - 2.0) + xa * sx + nn * (MAG_CARRIER[1] / 2.0 - 6.0)
                        tail = [b0, b0 - up * 25.0 + nn * 2.0, b0 - up * 52.0 + nn * 3.0 + xa * (sx * 0.15)]
                        ob = G.tube(f"{nm}.Tail.{j + 1}", coll, tail, 2.0, M["strap"], sides=8, step=3.0)
                        rigid.append((ob, bone))
                        ob = G.cyl(f"{nm}.CordEnd.{j + 1}", coll, tail[-1], -up, 4.0, 16.0, M["tan_metal"], n=12,
                                   bevel_mm=0.8)
                        rigid.append((ob, bone))
            hanger_mat = M["hanger_tan"]
        else:
            # vertical double frag pouch: body, piping-round edges, an L-shaped flap with a snap, two webbing rows
            s_c = s_top + 8.0 + FRAG[2] / 2.0
            Mf = on_plat(P["frag_u"], s_c, FRAG, square=0.5)
            xa, nn, up, ctr = Mf[:3, 0], Mf[:3, 1], Mf[:3, 2], Mf[:3, 3]
            ob = G.rbox("Belt.Rig.L.FragPouch", coll, FRAG, Mf, M["frag"], bevel_mm=9.0, taper=(0.96, 0.97))
            rigid.append((ob, bone))
            ftop = ctr + up * (FRAG[2] / 2.0)
            ob = G.boxes("Belt.Rig.L.FragPouch.Flap", coll,
                         [((FRAG[0] + 3.0, FRAG[1] + 4.0, 7.0), _frame(ftop + up * 2.5 + nn * 1.0, xa, nn, up)),
                          ((FRAG[0] + 3.0, 6.0, FLAP_DROP), _frame(ftop + nn * (FRAG[1] / 2.0 + 2.0) - up * (FLAP_DROP / 2.0 - 4.0), xa, nn, up))],
                         M["frag"], bevel_mm=2.5)
            rigid.append((ob, bone))
            ob = G.cyl("Belt.Rig.L.FragPouch.Snap", coll, ftop + nn * (FRAG[1] / 2.0 + 4.6) - up * (FLAP_DROP - 15.0),
                       nn, 7.75, 2.0, M["steel"], n=20, bevel_mm=0.6, dome=1.0)
            rigid.append((ob, bone))
            for j, zr in enumerate((95.0, 133.0)):
                ob = G.rbox(f"Belt.Rig.L.FragPouch.PALS.{j + 1}", coll, (FRAG[0] + 1.0, 1.6, 25.0),
                            _frame(ftop + nn * (FRAG[1] / 2.0 + 0.6) - up * zr, xa, nn, up), M["strap"], bevel_mm=0.5)
                rigid.append((ob, bone))
            # slim hard case: base and lid with a parting-line lip, a latch, two elastic cradle bands
            Mc = on_plat(P["case_u"], s_top + 8.0 + CASE[2] / 2.0, CASE, square=0.5)
            xa, nn, up, ctr = Mc[:3, 0], Mc[:3, 1], Mc[:3, 2], Mc[:3, 3]
            ob = G.rbox("Belt.Rig.L.Case", coll, CASE, Mc, M["case"], bevel_mm=6.0)
            rigid.append((ob, bone))
            lid_y = CASE[1] / 2.0 - 16.0
            ob = G.rbox("Belt.Rig.L.Case.Lip", coll, (CASE[0] + 3.0, 4.0, CASE[2] + 3.0),
                        _frame(ctr + nn * lid_y, xa, nn, up), M["case"], bevel_mm=1.5)
            rigid.append((ob, bone))
            ob = G.rbox("Belt.Rig.L.Case.Latch", coll, (8.0, 16.0, 30.0),
                        _frame(ctr - xa * (CASE[0] / 2.0 + 3.0) + nn * lid_y, xa, nn, up), M["case_dark"], bevel_mm=1.5)
            rigid.append((ob, bone))
            for j, zb in enumerate((60.0, 140.0)):
                ob = G.rbox(f"Belt.Rig.L.Case.Band.{j + 1}", coll, (CASE[0] + 4.4, CASE[1] + 2.2, 25.0),
                            _frame(ctr + nn * 1.1 + up * (CASE[2] / 2.0 - zb), xa, nn, up), M["strap"], bevel_mm=1.2)
                rigid.append((ob, bone))
            hanger_mat = M["hanger_black"]
        # ladder-locks on the thigh straps, on the running end at the platform's medial edge (right) or at the
        # medial front of the thigh (left), the frame tangent to the thigh
        for j, (ring, ss) in enumerate(rings):
            thl = th0 - (hw + 32.0) / r0 if side == "R" else math.radians(-30.0)
            pl, nl = ring.surf(STRAP_LIFT + STRAP_T + 0.3)(thl, ss)
            ob = G.hw_object(f"Belt.Rig.{side}.LadderLock.{j + 1}", coll, GH.ladder_lock(50.0, 32.0, 4.0, 3.5, 2),
                             G.frame(pl + nl * 5.0, -d_t, nl), M["metal"])
            rigid.append((ob, bone))
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
    fwd = t                                             # +theta on his right side runs toward the front
    up = n
    Mh = np.eye(4)
    Mh[:3, :3] = np.column_stack([fwd, d, up])
    top_off = BELT_W / 2.0 + 3.0
    Mh[:3, 3] = p + d * (HOLSTER[1] / 2.0 + 1.0) + up * (top_off - HOLSTER[2] / 2.0)
    Mh = G.seat(G.Under([(G.objects_bvh([belt]), 0.6)] + list(under_w.layers) + list(under_l.layers)), Mh, HOLSTER,
                gap=2.5)
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
    hb = G.dominant_bone(bd, p, allowed={"pelvis.R", "spine05", "upperleg01.R", "root"})
    rigid.append((hol, hb))
    rigid.append((p9, hb))
    out["holster"] = {"theta_deg": HOLSTER_THETA, "centre": [round(float(v)) for v in Mh[:3, 3]], "bone": hb}

    # ---------------------------------------------------------------- bind
    for ob, bone in rigid:
        G.rigid_bind(ob, rig, bone)
    for ob in soft:
        G.soft_bind(ob, body, rig)
    out["rigid"] = {ob.name: bone for ob, bone in rigid}
    out["soft"] = [ob.name for ob in soft]
    G.say(json.dumps({k: v for k, v in out.items() if k not in ("rigid", "soft")}))
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
