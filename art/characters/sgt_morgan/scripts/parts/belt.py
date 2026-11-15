"""Belt, round 1 blockout: an HSGI Cobra class 1.75 in rigger belt with its AustriAlpin Cobra buckle, two
drop-leg rigs (hanger, platform, thigh straps): on the right thigh twin open-top polymer rifle-magazine
carriers with their spare PMAGs, on the left thigh a vertical double frag pouch and a micro hard case; and
a mid-ride belt holster at the right rear hip with the P9 sidearm (a P226-class pistol). Notes:
scripts/parts/belt.md.

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

PART, TAG = "Belt", "belt"

BELT_W, BELT_T = 44.5, 5.5                       # 1.75 in, two plies
WAIST_PLANE = ((0.0, 0.0, 1072.0), (0.0, -0.15, 1.0))   # the trousers' waist plane (trousers.py WAIST)
BELT_TOP_BELOW = 3.0                             # belt top 3 mm under the waistband's top edge
BUCKLE = (38.0, 10.0, 58.0)                      # along the belt, thick, across (Cobra FC45: 58 x 38 x 10)
BUCKLE_THETA = -9.0                              # deg: about 30 mm to his right of centre front
PLATFORM = {"R": {"theta": 28.0, "top": 852.0, "h": 205.0, "w": 150.0, "straps": (785.0, 682.0)},
            "L": {"theta": 58.0, "top": 866.0, "h": 205.0, "w": 176.0, "straps": (684.0,)}}
PLATFORM_T, PLATFORM_LIFT = 8.0, 3.6             # laminate thickness; inner face over the trousers (straps under)
STRAP_W, STRAP_T = 38.0, 2.0
HANGER_W, HANGER_T = 38.0, 1.6
MAG_CARRIER = (76.0, 42.0, 140.0)                # HSGI polymer TACO class, broad side out
MAG_PLATE = (47.0, 3.0, 128.0)
PMAG_PROUD, PMAG = 53.0, (66.0, 25.0)
FRAG = (72.0, 70.0, 195.0)                       # vertical double M67 footprint
CASE = (98.0, 62.0, 191.0)                       # Pelican 1030 class, stood on end, lid against the platform
HOLSTER_THETA = -122.0                           # deg round the belt: right rear hip
HOLSTER = (60.0, 50.0, 190.0)                    # along the belt, out, tall (Safariland 6378 ALS class, P226)
P9_SLIDE = (34.0, 30.0, 196.0)                   # P226: slide length 196, height about 34, width 30
P9_GRIP = (105.0, 32.0, 48.0)                    # grip length, width, depth

COL = {"belt": "#2a2724", "buckle": "#1b1b1c", "hanger_tan": "#736054", "hanger_black": "#1e1c1a",
       "platform": "#24221f", "strap": "#161515", "poly_black": "#24211e", "poly_tan": "#816f5f",
       "pmag": "#1e1d1c", "frag": "#463e34", "case": "#3a3e40", "holster": "#1f1d1c", "slide": "#4f5050",
       "frame": "#2c2c2c"}


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

        def s_of(z):
            return (top[2] - z) / (-d_t[2])
        s_top, s_bot = s_of(P["top"]), s_of(P["top"] - P["h"])
        # thigh straps first: bands round the clothed thigh (rays from 130 mm out: never from the other leg)
        straps = []
        for zs in P["straps"]:
            ss = s_of(zs)
            ring = G.LimbSurf(under_l, top, d_t, f_t, l_t, (-math.pi, math.pi), (ss - 24.0, ss + 24.0), nth=144,
                              ns=17, iters=2, rmax=lambda t: 140.0 + 80.0 * max(0.0, math.sin(t)))
            # (rays start 140 mm out on the medial side, never inside the other leg; 220 laterally, past the cargo pocket)
            ob = G.slab(f"Belt.Rig.{side}.Strap.{len(straps) + 1}", coll, ring.surf(0.6), None,
                        ss - STRAP_W / 2.0, ss + STRAP_W / 2.0, STRAP_T, M["strap"], nu=144, nv=8, bevel_mm=0.6,
                        closed_u=True)
            soft.append(ob)
            straps.append(ob)
        # the platform: over the trousers and the straps
        under_p = G.Under(list(under_l.layers) + [(G.objects_bvh(straps), 0.5)])
        leg = G.LimbSurf(under_p, top, d_t, f_t, l_t, (math.radians(P["theta"] - 75), math.radians(P["theta"] + 75)),
                         (s_top - 20.0, s_bot + 20.0), nth=44, ns=40, iters=12, rmax=260.0)
        r0 = float(leg.F(math.radians(P["theta"]), (s_top + s_bot) / 2.0)) + PLATFORM_LIFT
        th0 = math.radians(P["theta"])
        hw = P["w"] / 2.0

        def psurf(off):
            f = leg.surf(off)

            def g(u, v):
                return f(th0 + u / r0, v)
            return g
        plat = G.slab(f"Belt.Rig.{side}.Platform", coll, psurf(PLATFORM_LIFT), lambda v: (-hw, hw), s_top, s_bot,
                      PLATFORM_T, M["platform"], nu=16, nv=22, bevel_mm=3.0)
        bone = f"upperleg02.{side}"
        rigid.append((plat, bone))
        plat_under = G.Under([(G.objects_bvh([plat]), 0.0)])

        def on_plat(u, s, size, extra=0.0):
            """Frame of an item on the platform's outer face at (u mm across, s along the thigh): x across,
            y outward, z up the thigh."""
            p, nn = psurf(PLATFORM_LIFT + PLATFORM_T + 0.5 + extra)(u, s)
            up = -d_t - nn * np.dot(-d_t, nn)
            up = G.unit(up)
            xa = G.unit(np.cross(up, nn))
            Mx = np.eye(4)
            Mx[:3, :3] = np.column_stack([xa, nn, up])
            Mx[:3, 3] = p + nn * size[1] / 2.0
            return G.seat(plat_under, Mx, size, gap=0.5)
        if side == "R":
            for k, u in enumerate((-39.0, 39.0)):
                s_c = s_top + 8.0 + MAG_CARRIER[2] / 2.0
                Mc = on_plat(u, s_c, MAG_CARRIER)
                ob = G.rbox(f"Belt.Rig.R.Carrier.{k + 1}", coll, MAG_CARRIER, Mc, M["poly_black"], bevel_mm=5.0)
                rigid.append((ob, bone))
                Mp = Mc.copy()
                Mp[:3, 3] = Mc[:3, 3] + Mc[:3, 1] * (MAG_CARRIER[1] / 2.0 + MAG_PLATE[1] / 2.0 + 0.3)
                ob = G.rbox(f"Belt.Rig.R.Carrier.{k + 1}.Plate", coll, MAG_PLATE, Mp, M["poly_tan"], bevel_mm=1.2)
                rigid.append((ob, bone))
                Mm = Mc.copy()
                Mm[:3, 3] = Mc[:3, 3] + Mc[:3, 2] * (MAG_CARRIER[2] / 2.0 + PMAG_PROUD / 2.0 + 0.3)
                ob = G.rbox(f"Belt.Rig.R.Carrier.{k + 1}.PMAG", coll, (PMAG[0], PMAG[1], PMAG_PROUD), Mm, M["pmag"],
                            bevel_mm=3.0)
                rigid.append((ob, bone))
            hanger_mat = M["hanger_tan"]
        else:
            s_c = s_top + 6.0 + FRAG[2] / 2.0
            Mf = on_plat(-51.0, s_c, FRAG)
            Mfl = Mf.copy()
            Mfl[:3, 3] = Mf[:3, 3] + Mf[:3, 2] * (FRAG[2] / 2.0 - 15.0) + Mf[:3, 1] * 3.0
            ob = G.boxes("Belt.Rig.L.FragPouch", coll, [(FRAG, Mf), ((FRAG[0] + 2, FRAG[1] + 6, 50.0), Mfl)],
                         M["frag"], bevel_mm=8.0)
            rigid.append((ob, bone))
            Mc = on_plat(36.0, s_top + 6.0 + CASE[2] / 2.0, CASE)
            ob = G.rbox("Belt.Rig.L.Case", coll, CASE, Mc, M["case"], bevel_mm=7.0)
            rigid.append((ob, bone))
            hanger_mat = M["hanger_black"]
        # hanger: from the belt's lower edge above the platform down to the platform's top edge
        # it runs between the thigh and the magazines' tops and enters the platform's top edge from behind
        pt, nt = psurf(PLATFORM_LIFT + PLATFORM_T * 0.5 - HANGER_T * 0.5)(0.0, s_top - 2.0)
        az = math.degrees(math.atan2(pt[0] - centre[0], -(pt[1] - centre[1])))
        pb_, db, tb = belt_point(az, v=vc - BELT_W / 2.0 + 6.0, off=0.3)
        path = [pb_ + n * 10.0, pb_]
        for k in range(1, 15):
            q = pb_ + (pt - pb_) * k / 14.0
            hq, _ = under_l.hit(q + nt * 120.0, -nt, 240.0)
            if hq is not None:
                q = q + nt * max(0.0, np.dot(hq - q, nt) + 0.5)
            path.append(q)
        path = np.array(path)
        nrm = [db] * 2 + [nt] * (len(path) - 2)
        ob = G.strip(f"Belt.Rig.{side}.Hanger", coll, path, nrm, HANGER_W, HANGER_T, hanger_mat, bevel_mm=0.4)
        soft.append(ob)
        out[f"rig_{side}"] = {"theta_deg": P["theta"], "platform_z": [P["top"], P["top"] - P["h"]],
                              "platform_radius_mm": round(r0, 1), "straps_z": list(P["straps"]),
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
                gap=0.6)
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
