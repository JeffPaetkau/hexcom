"""Armour, round 1 blockout: the hard shells. Per side: a three-lame pauldron (cap, mid plate, bicep band
with its elastic), a riot-class forearm guard (neoprene sleeve, elbow band, main plate, wrist band), a
small lateral elbow cap (fin and pad), and an external hard-cap knee pad (neoprene base, cap, strap) over
the trousers' knee-pad pocket. Left only: the shield emblem plate on the cap and the IR strobe on the mid
plate. Notes: scripts/parts/armour.md.

  "$SGT_BLENDER" -b --python scripts/parts/armour.py [-- --no-render]
  -> cache/parts/armour.blend (Part.Armour), cache/parts/armour.json, renders/armour/*.png

Method: each shell is a slab over a smooth surface around a limb: the clothed limb's outermost radius is
sampled by rays toward the limb axis (the shoulder cap by rays toward the shoulder joint), smoothed so a
rigid shell bridges the folds, kept outside the raw surface, and offset by the padding under the shell.
Rigid pieces are skinned 100 % to one bone (pauldron cap and mid plate: upperarm01; bicep band:
upperarm02; forearm elbow band and main plate: lowerarm01; wrist band: lowerarm02; elbow fin: upperarm02,
pad: lowerarm01; knee cap and base: lowerleg01). The neoprene sleeves and the knee straps are soft, bound
by weights from the body. Idempotent: it starts from base.blend every time.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gear_common as G  # noqa: E402

PART, TAG = "Armour", "armour"

COL = {"shell": "#7b7064", "knee": "#6a6158", "black": "#1d1c1b", "emblem": "#a9b3bd", "mark": "#e6ebef",
       "strobe": "#9fb0bf", "strobe_body": "#333537", "tan": "#8a7560"}

# Pauldron (mm; frame A: around the shoulder joint and the upper-arm axis)
CAP_PAD = 12.0                # shirt to the cap's inner face: 6 mm foam, its carrier and the cup's stand-off
CAP_T = 3.0
CAP_W_TOP, CAP_W_BOT = 125.0, 100.0
CAP_Q = (-60.0, 38.0)         # deg from the cap's centre direction: top flange .. bottom lip
CAP_FWD = 0.45                # the cap's centre turned toward the front of the shoulder (as drawn)
TIER2_S, TIER2_ARC = (88.0, 177.0), 115.0     # s along the arm below the joint; arc (mm) about the lateral line
TIER3_S, TIER3_DEG = (190.0, 238.0), 200.0
SHELL_PAD = 6.0
# Forearm guard: d from the elbow axis (mm)
SLEEVE_D, SLEEVE_T = (27.0, 255.0), 3.0
GUARD = {"Elbow": ((32.0, 66.0), 180.0, 2.5, 7.5), "Main": ((62.0, 224.0), 200.0, 3.0, 4.0),
         "Wrist": ((220.0, 252.0), 230.0, 2.5, 0.5)}    # (d range, arc deg, wall, radial lift over the foam)
GUARD_FOAM = 4.0
# Knee pad: unrolled octagon (u across, v up), cap 160 x 190 on a 4 mm base 12 mm larger
KNEE_HW, KNEE_HH = 80.0, 95.0
KNEE_BASE_T, KNEE_CAP_T, KNEE_DOME = 4.0, 3.5, 8.0
KNEE_DZ = -8.0                # cap centre relative to the knee joint (the pocket's centre)


def octagon_hw(v, hw=KNEE_HW, hh=KNEE_HH, lo=(62.8, 25.0), hi=(55.3, 25.0)):
    """Half width of the knee cap's octagon at height v (centre 0): bottom edge lo[0] wide rising over
    lo[1] to the full width, top edge hi[0] over hi[1]."""
    if v < -hh + lo[1]:
        t = (v + hh) / lo[1]
        return lo[0] + (hw - lo[0]) * max(0.0, min(1.0, t))
    if v > hh - hi[1]:
        t = (hh - v) / hi[1]
        return hi[0] + (hw - hi[0]) * max(0.0, min(1.0, t))
    return hw


Field, LimbSurf, numeric_normal = G.Field, G.LimbSurf, G.numeric_normal


class CapSurf:
    """The shoulder cap's surface: directions from the shoulder joint g, gnomonic about the centre direction
    c with e1 across (front-back) and e2 down the arm; P(p, q) = g + dir (R + off)."""

    def __init__(self, under, g, c, e1, e2, p_rng, q_rng, n=28, rmax=220.0):
        self.g, self.c, self.e1, self.e2 = np.asarray(g, float), c, e1, e2
        ps = np.linspace(p_rng[0], p_rng[1], n)
        qs = np.linspace(q_rng[0], q_rng[1], n)
        raw = np.full((n, n), np.nan)
        for j, q in enumerate(qs):
            for i, p in enumerate(ps):
                dr = self.dirv(p, q)
                hit, _n = under.hit(self.g + dr * rmax, -dr, rmax)
                if hit is not None:
                    raw[j, i] = float(np.dot(hit - self.g, dr))
        self.F = Field(raw, ps, qs, 10)

    def dirv(self, p, q):
        return G.unit(self.c + math.tan(p) * self.e1 + math.tan(q) * self.e2)

    def point(self, p, q, off):
        return self.g + self.dirv(p, q) * (self.F(p, q) + off)

    def surf(self, off):
        def f(u, v):
            p = self.point(u, v, off)
            n = numeric_normal(lambda uu, vv: self.point(uu, vv, off), u, v, self.dirv(u, v))
            return p, n
        return f


def main(render=True):
    import bpy
    body, rig = C.open_base()
    bd = C.body_data(body)
    clothing = G.load_clothing(rig)
    under_a, note_a = G.clothing_under(bd, clothing, "arm")
    under_l, note_l = G.clothing_under(bd, clothing, "leg")
    under_fa = G.Under(list(under_a.layers) + ([(G.objects_bvh(list(clothing["gloves"].all_objects)), 0.8)]
                                               if "gloves" in clothing else []))
    G.say("arm surface:", note_a, "| leg surface:", note_l, "| forearm: + gloves" if "gloves" in clothing else "")
    coll = C.part_collection(PART)
    M = {k: G.mat(f"Armour.Mat.{k.title().replace('_', '')}", v) for k, v in COL.items()}
    out = {"under": {"arm": note_a, "leg": note_l}}
    rigid = []      # (object, bone)
    soft = []

    for side, sgn in (("L", 1.0), ("R", -1.0)):
        S = {}
        gh = C.bone_mm(f"upperarm01.{side}")
        el = C.bone_mm(f"lowerarm01.{side}")
        wr = C.bone_mm(f"wrist.{side}")
        d_up, f_up, l_up = G.limb_frame(gh, el, side)

        # ------------------------------------------------ pauldron tier 1: the cap
        up = np.array([0.0, 0.0, 1.0])
        c = G.unit(up + d_up + CAP_FWD * f_up)     # between straight up and down the arm, turned forward
        e1 = G.unit(f_up - c * np.dot(f_up, c))    # across: toward the front
        e2 = G.unit(d_up - c * np.dot(d_up, c))    # down the arm
        qa, qb = math.radians(CAP_Q[0]), math.radians(CAP_Q[1])
        pw = math.radians(62.0)
        cap = CapSurf(under_a, gh, c, e1, e2, (-pw, pw), (qa - 0.05, qb + 0.05))
        r_cap = float(np.nanmean(cap.F.R)) + CAP_PAD

        def cap_hw(q, r=r_cap):
            t = (q - qa) / (qb - qa)
            w = CAP_W_TOP + (CAP_W_BOT - CAP_W_TOP) * t
            # lower corners chamfered 25 at 45 deg
            ch = max(0.0, 25.0 - (qb - q) * r)
            return ((w / 2.0 - ch) / r)
        ob = G.slab(f"Pauldron.{side}.Tier1.Cap", coll, cap.surf(CAP_PAD), lambda q: (-cap_hw(q), cap_hw(q)), qa, qb,
                    CAP_T, M["shell"], nu=22, nv=26, bevel_mm=1.2)
        rigid.append((ob, f"upperarm01.{side}"))
        S["cap_radius_mm"] = round(r_cap, 1)
        if side == "L":
            # shield emblem: a 50 x 95 plate 1 mm proud on the cap's outer face, centred low on the cap
            qe = qa + (qb - qa) * 0.62
            he = 47.5 / r_cap
            def emb_hw(q, r=r_cap, q0=qe - he, q1=qe + he):
                t = (q - q0) / (q1 - q0)               # 0 top .. 1 bottom point
                return (25.0 * (1.0 - 0.75 * max(0.0, t - 0.55) / 0.45)) / r
            ob = G.slab("Pauldron.L.Tier1.Emblem", coll, cap.surf(CAP_PAD + CAP_T + 1.5),
                        lambda q: (-emb_hw(q), emb_hw(q)), qe - he, qe + he, 1.0, M["emblem"], nu=8, nv=10,
                        bevel_mm=0.4)
            rigid.append((ob, "upperarm01.L"))

        # ------------------------------------------------ tiers 2 and 3 around the upper arm
        arm = LimbSurf(under_a, gh, d_up, l_up, f_up, (-math.pi, math.pi), (60.0, 280.0), nth=48, ns=24, iters=6,
                       outward=True)
        r2 = float(np.mean([arm.F(0.0, s) for s in TIER2_S])) + SHELL_PAD
        half2 = TIER2_ARC / 2.0
        ob = G.slab(f"Pauldron.{side}.Tier2.Plate", coll, arm.surf(SHELL_PAD, r0=r2), lambda v: (-half2, half2),
                    TIER2_S[0], TIER2_S[1], CAP_T, M["shell"], nu=14, nv=10, bevel_mm=1.2)
        rigid.append((ob, f"upperarm01.{side}"))
        if side == "L":
            # IR strobe 30 x 45 x 18 on the plate's outer face, toward the front
            th = -0.5 * half2 / r2          # toward the plate's rear edge, as drawn
            sm = (TIER2_S[0] + TIER2_S[1]) / 2.0 + 8.0
            p = arm.point(th, sm, SHELL_PAD + CAP_T + 0.4)
            n = arm.dirv(th)
            Ms = G.frame(p + n * 9.0, np.cross(d_up, n) * -1.0, n)
            Ms2 = np.eye(4)
            Ms2[:3, 0], Ms2[:3, 1], Ms2[:3, 2], Ms2[:3, 3] = Ms[:3, 0], -d_up, n, Ms[:3, 3]
            ob = G.rbox("Pauldron.L.Tier2.Strobe", coll, (30.0, 45.0, 18.0), Ms2, M["strobe"], bevel_mm=3.0)
            rigid.append((ob, "upperarm01.L"))
        half3 = math.radians(TIER3_DEG / 2.0)
        ob = G.slab(f"Pauldron.{side}.Tier3.Band", coll, arm.surf(2.5), lambda v: (-half3, half3),
                    TIER3_S[0], TIER3_S[1], 2.5, M["shell"], nu=30, nv=8, bevel_mm=1.0)
        rigid.append((ob, f"upperarm02.{side}"))
        ob = G.slab(f"Pauldron.{side}.Tier3.Elastic", coll, arm.surf(0.6),
                    lambda v: (half3 - 0.05, 2 * math.pi - half3 + 0.05), TIER3_S[0] + 6, TIER3_S[1] - 6, 1.8,
                    M["black"], nu=20, nv=4, bevel_mm=0.5)
        rigid.append((ob, f"upperarm02.{side}"))
        S["tier2_radius_mm"] = round(r2, 1)

        # ------------------------------------------------ forearm guard
        d_fa, f_fa, l_fa = G.limb_frame(el, wr, side)
        t_rad = G.unit(C.bone_mm(f"finger2-1.{side}") - C.bone_mm(f"finger5-1.{side}"))
        dors = np.cross(t_rad, d_fa) if side == "L" else np.cross(d_fa, t_rad)
        dors = G.unit(dors - d_fa * np.dot(dors, d_fa))
        e1f = G.unit(np.cross(d_fa, dors))
        fa = LimbSurf(under_fa, el, d_fa, dors, e1f, (-math.pi, math.pi), (15.0, 270.0), nth=48, ns=26, iters=4,
                      outward=True)
        ob = G.slab(f"Guard.{side}.Sleeve", coll, fa.surf(0.5), lambda v: (0.0, 2 * math.pi), SLEEVE_D[0], SLEEVE_D[1],
                    SLEEVE_T, M["black"], nu=40, nv=16, bevel_mm=1.0, closed_u=True)
        soft.append(ob)
        base_off = 0.5 + SLEEVE_T + GUARD_FOAM
        for k, (drng, arc, wall, lift) in GUARD.items():
            h = math.radians(arc / 2.0)
            ob = G.slab(f"Guard.{side}.{k}", coll, fa.surf(base_off + lift), lambda v, h=h: (-h, h), drng[0], drng[1],
                        wall, M["shell"], nu=26, nv=max(4, int((drng[1] - drng[0]) / 10)), bevel_mm=1.0)
            rigid.append((ob, f"lowerarm02.{side}" if k == "Wrist" else f"lowerarm01.{side}"))
        # foam under the plates (the step under each plate's edge), one piece on the main plate's footprint
        ob = G.slab(f"Guard.{side}.Foam", coll, fa.surf(0.5 + SLEEVE_T + 1.2), lambda v: (-1.6, 1.6), 40.0, 246.0,
                    GUARD_FOAM - 1.5, M["black"], nu=20, nv=12, bevel_mm=1.0)
        rigid.append((ob, f"lowerarm01.{side}"))

        # ------------------------------------------------ lateral elbow cap: fin on the humerus, pad on the forearm
        flex = G.unit(np.cross(d_up, d_fa))
        if np.dot(flex, np.array([sgn, 0.0, 1.0])) < 0:
            flex = -flex
        for nm, base_pt, size, bone in (("Fin", el - d_up * 18.0, (14.0, 40.0, 5.0), f"upperarm02.{side}"),
                                         ("Pad", el + d_fa * 20.0, (30.0, 28.0, 6.0), f"lowerarm01.{side}")):
            ax = d_up if nm == "Fin" else d_fa
            hit, _n = under_a.hit(base_pt + flex * 200.0, -flex, 200.0)
            p = hit if hit is not None else base_pt + flex * 45.0
            Mb = G.frame(p + flex * (size[2] / 2 + 3.0), np.cross(ax, flex), flex)
            Mb2 = np.eye(4)
            Mb2[:3, 0], Mb2[:3, 1], Mb2[:3, 2], Mb2[:3, 3] = Mb[:3, 0], ax, flex, Mb[:3, 3]
            Mb2 = G.seat(under_a, Mb2[:, [0, 2, 1, 3]], (size[0], size[2], size[1]), grid=3, gap=3.0)[:, [0, 2, 1, 3]]
            ob = G.rbox(f"ElbowCap.{side}.{nm}", coll, size, Mb2, M["shell"], bevel_mm=2.0)
            rigid.append((ob, bone))

        # ------------------------------------------------ knee pad
        kn = C.bone_mm(f"lowerleg01.{side}")
        top = C.bone_mm(f"upperleg02.{side}")
        bot = C.bone_mm(f"lowerleg02.{side}")
        d_k, f_k, l_k = G.limb_frame(top, bot, side)
        # axis point at the knee: the projection of the knee joint on the hip-ankle-ish line
        s_kn = float(np.dot(kn - top, d_k))
        leg = LimbSurf(under_l, top, d_k, f_k, l_k, (-1.6, 1.6), (s_kn - 150.0, s_kn + 150.0), nth=36, ns=30,
                       iters=6)
        r_k = float(leg.F(0.0, s_kn)) + 2.0
        sc = s_kn - KNEE_DZ     # v up = -s; the cap centre KNEE_DZ (negative = below) from the joint

        def kvs(off, dome=0.0):
            base_f = leg.surf(off, r0=r_k)

            def f(u, v):
                s = sc - v
                p, n = base_f(u, s)
                if dome:
                    du = max(0.0, 1.0 - (u / KNEE_HW) ** 2)
                    dv = max(0.0, 1.0 - (v / KNEE_HH) ** 2)
                    p = p + n * dome * du * dv
                return p, n
            return f
        ob = G.slab(f"Kneepad.{side}.Base", coll, kvs(0.6), lambda v: (-octagon_hw(v - 0) - 12.0, octagon_hw(v) + 12.0),
                    -KNEE_HH - 12.0, KNEE_HH + 12.0, KNEE_BASE_T, M["black"], nu=20, nv=24, bevel_mm=1.5)
        soft.append(ob)                         # neoprene: follows the knee pocket
        ob = G.slab(f"Kneepad.{side}.Cap", coll, kvs(0.6 + KNEE_BASE_T + 1.5, KNEE_DOME),
                    lambda v: (-octagon_hw(v), octagon_hw(v)), -KNEE_HH, KNEE_HH, KNEE_CAP_T, M["knee"], nu=20,
                    nv=24, bevel_mm=1.5)
        rigid.append((ob, f"lowerleg01.{side}"))
        # strap: 38 mm elastic round the back of the knee, from the base's lateral edge to its medial edge
        ring = LimbSurf(under_l, top, d_k, f_k, l_k, (-math.pi, math.pi), (s_kn - 30.0, s_kn + 30.0), nth=60,
                        ns=6, iters=3)
        th0 = (KNEE_HW + 6.0) / r_k
        ob = G.slab(f"Kneepad.{side}.Strap", coll, ring.surf(0.6), lambda v: (th0, 2 * math.pi - th0),
                    s_kn - 19.0 + 10.0, s_kn + 19.0 + 10.0, 2.0, M["black"], nu=30, nv=3, bevel_mm=0.5)
        soft.append(ob)
        S["knee_radius_mm"] = round(r_k, 1)
        S["knee_centre_z"] = round(float((top + d_k * sc)[2]), 1)
        out[side] = S

    # ------------------------------------------------ bind
    for ob, bone in rigid:
        G.rigid_bind(ob, rig, bone)
    for ob in soft:
        G.soft_bind(ob, body, rig)
    out["rigid"] = {ob.name: bone for ob, bone in rigid}
    out["soft"] = [ob.name for ob in soft]
    G.say(json.dumps({k: v for k, v in out.items() if k in ("L", "R")}))
    if render:
        rep = G.finish_part(TAG, coll, body, rig, clothing, (0.0, 0.0, 1000.0), 1900.0,
                            ["ref.arm_R", "ref.arm_L", "ref.legs_knees", "ref.soldier_full"], extra=out)
        out["check"] = rep
        with open(os.path.join(C.PARTS_DIR, f"{TAG}.json"), "w") as f:
            json.dump(out, f, indent=1)
    else:
        C.save_part(TAG, coll, extra=out)
    return out


if __name__ == "__main__":
    main(render="--no-render" not in C._argv())
