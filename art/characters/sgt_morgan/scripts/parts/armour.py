"""Armour, round 6: the hard shells. Per side: a three-lame pauldron (cap and mid plate on foam liners, the cap
linked by webbing up over the carrier's strap pad, an elastic strap round the mid plate, the bicep band with its
elastic and a flat ladder-lock), a gauntlet-style forearm guard (a padded sleeve, a long shaped main shell over the
outer forearm from below the elbow and a wrist plate under its lip, rolled rims, a rib and grooves, foam under
each, two straps with ladder-locks), an elbow pad (a domed cap on a neoprene base on the point of the elbow,
straps round the upper arm and the forearm), and a faceted hard-cap knee pad (a padded base filling the dome, a
domed cap with a flat central plate, a stepped frame with slots, strap with a ladder-lock and a tan tail on the
medial side, the red tab on the lateral facet). Left only: the shield emblem plate on the cap and the IR strobe
on the mid plate. Notes: scripts/parts/armour.md.

  "$SGT_BLENDER" -b --python scripts/parts/armour.py [-- --no-render]
  -> cache/parts/armour.blend (Part.Armour), cache/parts/armour.json, renders/armour/*.png

Method: each shell is a slab over a smooth surface around a limb: the clothed limb's outermost radius is
sampled by rays toward (or from) the limb axis (the shoulder cap by rays toward the shoulder joint), smoothed
so a rigid shell bridges the folds, kept outside the raw surface, and offset by the padding under the shell.
The forearm plates use a straight (ruled) surface instead: per angle round the forearm, the radius is a
straight line along the forearm fitted to the clothed samples and raised until no sample is outside it, so
a plate is a straight shell, not a cone that flares with the sleeve. Rims, ribs, grooves and frame steps are
a thickness field over each slab (gear_common.edge_profile). The shoulder cap also clears the carrier's
shoulder-strap pads (cache/parts/carrier.blend, when it exists).

Rigging: the pauldron pieces are skinned 100 % to one bone (cap, its foam, link, rivets, emblem, tier 2 and
strobe: upperarm01 (the cap is turned back at rest, CAP_FWD, so the pose's inward-turned upper arm brings it
to the outside of the shoulder; bound to shoulder01 it stood off the adducted arm like a wing); bicep
band: upperarm02). Round 6: the guard plates, their foam and ladder-locks, the knee caps, tabs and ladder-locks
are MOUNTED on the skin at their centre (gear_common.mount_bind on Body.Mesh: the skin's weights there on every
vertex, one blended transform), so a knee cap follows the kneecap however the knee bends or the shin twists, and
a guard follows the forearm's twist. The guard sleeves and straps are bound by weights from the body with the
upper-arm bones folded into lowerarm01, so they move with the forearm and do not collapse into the elbow fold;
the elbow pad (cap and base) and its straps, the knee bases and straps by plain weights from the body.
Idempotent: it starts from base.blend every time.
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

PART, TAG = "Armour", "armour"

COL = {"shell": "#7b7064", "knee": "#6a6158", "black": "#1d1c1b", "emblem": "#a9b3bd", "mark": "#e6ebef",
       "strobe": "#9fb0bf", "strobe_body": "#333537", "tan": "#8a7560", "metal": "#5b5a58",
       "silver": "#9a948c", "red": "#a0545c", "foam": "#2a2927"}   # solid-view colours; Cycles uses MATERIALS
# Materials round (round 5, 2026-11-15): FDE-moulded shells painted dark grey, worn through to the tan on the
# rims and in chips (the reference's knee caps and pauldrons), the knee caps the most worn; neoprene sleeves,
# bases and straps; the emblem plate brushed blue-grey anodised with R003's mark (UV.Decal, decal_uv()); the
# strobe's frosted lens; gunmetal rivets, a brighter cam buckle, a red TPR tab, coyote strap tails.
MATERIALS = {
    "Armour.Mat.Shell": ("Polymer.Painted.Armour", "Shell", {}),
    # round 8: the knee caps keep round 5's tan moulding under the paint (the drawn caps' frames are worn to tan,
    # not to steel like the pauldrons' rims), chips near the edges and frames, not over the faces
    "Armour.Mat.Knee": ("Polymer.Painted.Armour", "Knee", {"edge__radius_mm": 3.5, "edge__width": 0.06,
                                                           "chips__cover": 0.01, "chips__edge_cover": 0.10,
                                                           "chips__noise_mm": 5.0, "dust__amount": 0.45,
                                                           "substrate__f0": None, "substrate__hex": "#7a705e",
                                                           "substrate__rough": 0.62, "substrate__primer": 0.0}),
    "Armour.Mat.Black": ("Neoprene.Black", "Black", {}),
    "Armour.Mat.Emblem": ("Decal.Emblem", "Emblem", {}),
    "Armour.Mat.Foam": ("Foam.ClosedCell.Black", "Foam", {}),
    "Armour.Mat.Metal": ("Metal.Gunmetal", "Metal", {}),
    "Armour.Mat.Silver": ("Metal.Gunmetal", "Silver", {"f0": (0.42, 0.42, 0.43), "rough_range": (0.30, 0.42),
                                                       "aniso": 0.0}),
    "Armour.Mat.Red": ("Polymer.Black.Smooth", "Red", {"albedo_hex": "#7a3f42", "rough": 0.55}),
    "Armour.Mat.Strobe": ("Lens.Strobe.Polycarbonate", "Strobe", {}),
    "Armour.Mat.Tan": ("Webbing.Nylon.Coyote", "Tan", {}),
}


def frame_wear(ob, urange, v0, v1, nu, nv, hw_fn, inner=(9.0, 12.5)):
    """The knee cap's raised frame as the point attribute `paint_wear` (1 on the frame, 0 on the centre panel
    2 mm below it), from the slab's own grid parameters (gear_common.grid_points: rows v, columns u over
    urange(v); inner then outer surface): e = distance to the outline (knee_field's), worn where e < 9-12.5 mm."""
    W = []
    for j in range(nv + 1):
        v = v0 + (v1 - v0) * j / nv
        a, b = urange(v)
        for u in np.linspace(a, b, nu + 1):
            e = min(hw_fn(v) - abs(u), v - v0, v1 - v)
            W.append(1.0 - G.smoothstep(e, inner[0], inner[1]))
    W = np.array(W, np.float32)
    me = ob.data
    if len(me.vertices) != 2 * len(W):
        return None
    att = me.attributes.get("paint_wear") or me.attributes.new("paint_wear", "FLOAT", "POINT")
    att.data.foreach_set("value", np.concatenate([W, W]))
    return round(float(W.mean()), 3)


def decal_uv(ob, uv="UV.Decal"):
    """A 0-1 planar UV over a plate for a decal (R003's emblem): the plate's principal axes, v up (toward
    the plate's highest rest z), u to the right as seen from outside (away from the body's mid-line), so the
    image is never mirrored."""
    me = ob.data
    M = np.array(ob.matrix_world)
    V = np.array([tuple(v.co) for v in me.vertices]) @ M[:3, :3].T + M[:3, 3]
    c = V.mean(0)
    _, _, W = np.linalg.svd(V - c, full_matrices=False)
    a_len, n = W[0], W[2]
    if np.dot(c[:2], n[:2]) < 0:                      # the plate's normal out from the body (sideways at the shoulder)
        n = -n
    up = a_len if a_len[2] >= 0 else -a_len
    right = np.cross(up, n)
    P = V - c
    pu, pv = P @ right, P @ up
    u = (pu - pu.min()) / max(np.ptp(pu), 1e-9)
    v = (pv - pv.min()) / max(np.ptp(pv), 1e-9)
    lay = me.uv_layers.get(uv) or me.uv_layers.new(name=uv)
    lv = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    lay.data.foreach_set("uv", np.stack([u[lv], v[lv]], 1).astype(np.float32).ravel())
    return {"width_mm": round(float(np.ptp(pu)) * 1000.0, 1), "height_mm": round(float(np.ptp(pv)) * 1000.0, 1)}

# Pauldron (mm; frame A: around the shoulder joint and the upper-arm axis)
CAP_PAD = 7.0                 # round 6: shirt to the cap's inner face, filled by a 6 mm foam liner (12 mm with no
                              # liner read as a card standing off the shoulder over a dark gap)
CAP_FOAM = 6.0
CAP_T = 3.0
CAP_W_TOP, CAP_W_BOT = 150.0, 122.0
CAP_Q = (-40.0, 50.0)         # deg from the cap's centre direction: top flange .. bottom lip (round 6: the flange
                              # stops short of the carrier's strap pad, -54 lifted the whole cap over it)
CAP_SMOOTH = 4                # round 6: the cap field's smoothing (10 flattened the cup into a plank)
CAP_LINK = 0.42               # rad above the cap's top edge: the webbing link up over the carrier's strap pad
CAP_UP = 1.3                  # the cap's centre: CAP_UP x up + down the arm (+ CAP_FWD x front), at rest
CAP_FWD = -0.25               # turned back at rest (round 1: 0.45 forward): the hero pose turns the upper arm
                              # in, so posed the cap faces out and up on the outside of the shoulder, as drawn
CAP_STRAP_CLEAR = 2.0         # over the carrier's shoulder-strap pads
EMBLEM_W, EMBLEM_H, EMBLEM_R = 58.0, 70.0, 10.0   # round 8 (m34): the drawn rounded-square emblem plate (was a 50 x 95 shield)
TIER2_S, TIER2_ARC = (76.0, 166.0), 140.0     # s along the arm below the joint; arc (mm) about the lateral line
TIER3_S, TIER3_DEG = (190.0, 238.0), 200.0
SHELL_PAD = 4.5               # round 6: over a 4 mm foam liner (6 with no liner stood off as a card)
SHELL_FOAM = 4.0
# Forearm guard: d from the elbow axis (mm). Round 6: a gauntlet, not rings: one long shaped main shell over the
# outer half of the forearm from below the elbow (d 96) and a wrist plate under its lower lip to the glove cuff,
# over a padded sleeve; nothing above d 84, so nothing crosses the elbow crease; the elbow carries its own pad.
SLEEVE_D, SLEEVE_T = (84.0, 258.0), 4.0
SLEEVE_FLEX_EXTRA = 40.0      # the sleeve's proximal edge 40 mm lower on the flexor side (clears the fold)
GUARD_FOAM = 4.0
# built distal first, the proximal plate laps over the next with a flared lip
# (name, d range, arc deg, wall, unused, edge curve mm: the proximal edge recedes this much at the plate's sides)
GUARD = [("Wrist", (204.0, 258.0), 150.0, 2.5, "lowerarm02", 8.0),
         ("Main", (96.0, 214.0), 160.0, 3.0, "lowerarm01", 30.0)]
GUARD_STRAP_W = 25.0
GUARD_STRAP_D = (122.0, 240.0)   # strap centres: on the main shell well below the elbow fold, on the wrist plate
# Elbow pad (round 6; the reference has one on the left elbow, m22): a domed hard cap on the point of the elbow
# over a neoprene base, held by straps round the upper arm and the forearm; the cap rides the skin's weights there
ELBOW_PAD = {"w": 70.0, "h": 80.0, "pad": 5.0, "base_t": 4.0, "t": 3.0, "lat": 0.35, "strap_up": 52.0,
             "strap_dn": 74.0, "strap_w": 18.0}
# Knee pad: unrolled octagon (u across, + lateral; v up), round 6: a faceted domed cap 150 x 164 (was 160 x 190
# in two lames, a tall flat plate whose upper lame gaped) with a flat central plate, on a padded base 12 larger
KNEE_HW, KNEE_HH = 75.0, 82.0
KNEE_BASE_T, KNEE_CAP_T, KNEE_DOME = 7.0, 3.5, 22.0
KNEE_FACET = (34.0, 26.0, 36.0)   # the facets' runs (mm) from the outline to the central plate: sides, top, bottom
KNEE_BASE_OFF = 1.6           # over the trousers' knee pocket
KNEE_DZ = -8.0                # cap centre relative to the knee joint (the pocket's centre)



def octagon_hw(v, hw=KNEE_HW, hh=KNEE_HH, lo=(52.0, 24.0), hi=(46.0, 24.0)):
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

    def __init__(self, under, g, c, e1, e2, p_rng, q_rng, n=30, rmax=240.0, smooth=10):
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
        self.F = Field(raw, ps, qs, smooth)

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


class StraightSurf:
    """A straight (ruled) shell surface round the forearm: for each angle theta (from e0 toward e1) the radius
    is a straight line in s, fitted to the outermost clothed samples over [s0, s1] and raised until no sample
    lies outside it; the line coefficients are smoothed round theta (and the bound re-applied). u is arc mm at
    the nominal radius r_nom, v = s."""

    def __init__(self, under, a, d, e0, e1, s0, s1, nth=72, ns=16, rmax=200.0):
        self.a, self.d, self.e0, self.e1 = np.asarray(a, float), d, e0, e1
        ths = np.linspace(-math.pi, math.pi, nth, endpoint=False)
        ss = np.linspace(s0, s1, ns)
        raw = np.array([[G.limb_radius(under, a, d, e0, e1, s, t, rmax, True)[0] for t in ths] for s in ss])
        raw = G.fill_nan(raw)
        A = np.vstack([np.ones(ns), ss]).T
        coef, *_ = np.linalg.lstsq(A, raw, rcond=None)          # (2, nth)
        for _ in range(3):
            coef[0] += np.max(raw - A @ coef, axis=0)
            # smooth round theta (circular), slopes and intercepts alike
            coef = 0.5 * coef + 0.25 * (np.roll(coef, 1, 1) + np.roll(coef, -1, 1))
        coef[0] += np.maximum(0.0, np.max(raw - A @ coef, axis=0))
        self.ths, self.coef, self.s0, self.s1 = ths, coef, s0, s1
        self.r_nom = float(np.mean(A @ coef))

    def radius(self, th, s):
        th = (th + math.pi) % (2 * math.pi) - math.pi
        c0 = np.interp(th, np.append(self.ths, math.pi), np.append(self.coef[0], self.coef[0][0]))
        c1 = np.interp(th, np.append(self.ths, math.pi), np.append(self.coef[1], self.coef[1][0]))
        return c0 + c1 * s

    def dirv(self, th):
        return math.cos(th) * self.e0 + math.sin(th) * self.e1

    def point(self, th, s, off):
        return self.a + self.d * s + self.dirv(th) * (self.radius(th, s) + off)

    def surf(self, off):
        r = self.r_nom

        def f(u, v):
            p = self.point(u / r, v, off)
            n = numeric_normal(lambda uu, vv: self.point(uu / r, vv, off), u, v, self.dirv(u / r))
            return p, n
        return f


def plate_t(wall, half_u, v0, v1, rib=False, grooves=False, bead=0.9):
    """Thickness field of a moulded plate over (u arc mm in [-half_u, half_u], v in [v0, v1]): rolled rim bead
    all round; optionally a central rib (14 wide, 2.5 proud, 45 deg flanks, ends rounded 7 mm from the
    plate's ends) and two grooves 1.2 deep at +-22 mm."""
    def f(u, v):
        e = min(half_u - abs(u), v - v0, v1 - v)
        t = wall + G.edge_profile(e, bead)
        if rib:
            end = min(v - v0, v1 - v) - 8.0
            if end > 0:
                h = 2.5 * G.smoothstep(end, 0.0, 7.0)
                t += h * (1.0 - G.smoothstep(abs(u), 7.0, 9.5))
        if grooves:
            for g0 in (-22.0, 22.0):
                if min(v - v0, v1 - v) > 12.0:
                    t -= 1.2 * (1.0 - G.smoothstep(abs(u - g0), 1.0, 2.2))
        return t
    return f


def main(render=True):
    import bpy
    body, rig = C.open_base()
    bd = C.body_data(body)
    clothing = G.load_clothing(rig)
    under_a, note_a = G.clothing_under(bd, clothing, "arm")
    under_t, _note_t = G.clothing_under(bd, clothing, "torso")
    under_l, note_l = G.clothing_under(bd, clothing, "leg")
    under_fa = G.Under(list(under_a.layers) + ([(G.objects_bvh(list(clothing["gloves"].all_objects)), 0.8)]
                                               if "gloves" in clothing else []))
    # the carrier's shoulder-strap pads: the cap lies over them (as drawn), clear by CAP_STRAP_CLEAR
    strap_layer, note_c = [], "no carrier cache"
    carrier = None
    if os.path.exists(os.path.join(C.PARTS_DIR, "carrier.blend")):
        carrier = C.load_part("carrier", rig)
        straps = [o for o in carrier.all_objects if o.type == "MESH" and o.name.startswith("Carrier.Strap.")]
        if straps:
            strap_layer = [(G.objects_bvh(straps), CAP_STRAP_CLEAR - CAP_PAD)]
            note_c = f"cap clears {len(straps)} carrier strap objects by {CAP_STRAP_CLEAR} mm"
    G.say("arm surface:", note_a, "| leg surface:", note_l, "|", note_c)
    coll = C.part_collection(PART)
    M = {k: G.mat(f"Armour.Mat.{k.title().replace('_', '')}", v) for k, v in COL.items()}
    out = {"under": {"arm": note_a, "leg": note_l, "carrier": note_c}}
    rigid = []      # (object, bone)
    soft = []       # (object, collapse map or None)
    mounts = []     # round 6: (object, rest point mm): mounted on the skin there (gear_common.mount_bind on Body.Mesh)

    for side, sgn in (("L", 1.0), ("R", -1.0)):
        S = {}
        gh = C.bone_mm(f"upperarm01.{side}")
        el = C.bone_mm(f"lowerarm01.{side}")
        wr = C.bone_mm(f"wrist.{side}")
        d_up, f_up, l_up = G.limb_frame(gh, el, side)

        # ------------------------------------------------ tiers 2 and 3 around the upper arm (first: the cap laps over)
        arm = LimbSurf(under_a, gh, d_up, l_up, f_up, (-math.pi, math.pi), (60.0, 280.0), nth=48, ns=24, iters=6,
                       outward=True)
        r2 = float(np.mean([arm.F(0.0, s) for s in TIER2_S])) + SHELL_PAD
        half2 = TIER2_ARC / 2.0
        t2_v0, t2_v1 = TIER2_S

        def t2_field(u, v):
            e = min(half2 - abs(u), v - t2_v0, t2_v1 - v)
            t = CAP_T + G.edge_profile(e, 0.9)
            # the recessed panel 70 x 28, 1.5 deep, 32 below the top edge
            du, dv = abs(u) - 35.0, abs(v - (t2_v0 + 32.0)) - 14.0
            if du < 0 and dv < 0:
                t -= 1.5 * G.smoothstep(min(-du, -dv), 0.0, 1.5)
            return t
        ob = G.slab(f"Pauldron.{side}.Tier2.Plate", coll, arm.surf(SHELL_PAD, r0=r2), lambda v: (-half2, half2),
                    t2_v0, t2_v1, CAP_T, M["shell"], nu=56, nv=40, bevel_mm=0.8, t_field_fn=t2_field)
        rigid.append((ob, f"upperarm01.{side}"))
        tier2 = ob
        # round 6: the foam liner under the plate (fills the stand-off), and an elastic strap round the inner arm
        ob = G.slab(f"Pauldron.{side}.Tier2.Foam", coll, arm.surf(SHELL_PAD - SHELL_FOAM + 0.2, r0=r2),
                    lambda v: (-half2 + 4.0, half2 - 4.0), t2_v0 + 4.0, t2_v1 - 4.0, SHELL_FOAM - 0.4, M["foam"],
                    nu=24, nv=8, bevel_mm=1.0)
        rigid.append((ob, f"upperarm01.{side}"))
        h2r = half2 / r2
        sm2 = 0.5 * (t2_v0 + t2_v1) + 10.0
        ob = G.slab(f"Pauldron.{side}.Tier2.Strap", coll, arm.surf(0.6), lambda v, a=h2r: (a - 0.12, 2 * math.pi - a + 0.12),
                    sm2 - 10.0, sm2 + 10.0, 1.6, M["black"], nu=24, nv=4, bevel_mm=0.5)
        soft.append((ob, None))
        if side == "L":
            # IR strobe 30 x 45 x 18 on the plate's outer face, toward its rear edge (as drawn)
            th = -0.5 * half2 / r2
            sm = (TIER2_S[0] + TIER2_S[1]) / 2.0 + 8.0
            p = arm.point(th, sm, SHELL_PAD + CAP_T + 0.4)
            n = arm.dirv(th)
            Ms = G.frame(p + n * 9.0, np.cross(d_up, n) * -1.0, n)
            Ms2 = np.eye(4)
            Ms2[:3, 0], Ms2[:3, 1], Ms2[:3, 2], Ms2[:3, 3] = Ms[:3, 0], -d_up, n, Ms[:3, 3]
            ob = G.rbox("Pauldron.L.Tier2.Strobe", coll, (30.0, 45.0, 18.0), Ms2, M["strobe"], bevel_mm=3.0)
            rigid.append((ob, "upperarm01.L"))
        half3 = math.radians(TIER3_DEG / 2.0)
        r3 = float(arm.F(0.0, 0.5 * (TIER3_S[0] + TIER3_S[1]))) + 2.5
        t3_v0, t3_v1, h3mm = TIER3_S[0], TIER3_S[1], half3 * r3

        def t3_field(u, v):
            e = min(h3mm - abs(u * r3), v - t3_v0, t3_v1 - v)
            t = 2.5 + G.edge_profile(e, 0.8, 2.5)
            vm = 0.5 * (t3_v0 + t3_v1)
            return t - 1.0 * (1.0 - G.smoothstep(abs(v - vm), 1.0, 2.2))      # the mid groove
        ob = G.slab(f"Pauldron.{side}.Tier3.Band", coll, arm.surf(2.5), lambda v: (-half3, half3),
                    t3_v0, t3_v1, 2.5, M["shell"], nu=64, nv=24, bevel_mm=0.6, t_field_fn=t3_field)
        rigid.append((ob, f"upperarm02.{side}"))
        ob = G.slab(f"Pauldron.{side}.Tier3.Elastic", coll, arm.surf(0.6),
                    lambda v: (half3 - 0.05, 2 * math.pi - half3 + 0.05), TIER3_S[0] + 6, TIER3_S[1] - 6, 1.8,
                    M["black"], nu=20, nv=4, bevel_mm=0.5)
        rigid.append((ob, f"upperarm02.{side}"))
        # cam buckle at the band's anterior end (where the elastic runs in): frame 36 x 30 x 11, lever on top
        # round 6: a flat gunmetal ladder-lock lying on the band's end, the elastic through it (the silver cam buckle
        # block stood 3-4 mm off the band and read as a loose clip)
        th_b = half3 - 0.10                                   # +theta is toward the front (e1 = f_up)
        sb = 0.5 * (TIER3_S[0] + TIER3_S[1])
        pb_ = arm.point(th_b, sb, 2.5 + 2.5 + 0.8 + 0.2)
        nb = arm.dirv(th_b)
        ob = G.hw_object(f"Pauldron.{side}.Tier3.Buckle", coll, GH.ladder_lock(30.0, 24.0, 3.0, 2.6, 2),
                         G.frame(pb_ + nb * 1.3, -d_up, nb), M["metal"])
        rigid.append((ob, f"upperarm02.{side}"))
        S["tier2_radius_mm"] = round(r2, 1)

        # ------------------------------------------------ pauldron tier 1: the cap, on the outside of the shoulder
        up = np.array([0.0, 0.0, 1.0])
        c = G.unit(CAP_UP * up + d_up + CAP_FWD * f_up)     # over the deltoid's top, on the outside
        e1 = G.unit(f_up - c * np.dot(f_up, c))    # across: toward the front
        e2 = G.unit(d_up - c * np.dot(d_up, c))    # down the arm
        qa, qb = math.radians(CAP_Q[0]), math.radians(CAP_Q[1])
        pw = math.radians(60.0)
        under_cap = G.Under(list(under_a.layers) + list(under_t.layers) + strap_layer +
                            [(G.objects_bvh([tier2]), 1.5 - CAP_PAD)])
        cap = CapSurf(under_cap, gh, c, e1, e2, (-pw, pw), (qa - CAP_LINK - 0.05, qb + 0.05), smooth=CAP_SMOOTH)
        r_cap = float(np.nanmean(cap.F.R)) + CAP_PAD

        def cap_hw(q, r=r_cap):
            t = (q - qa) / (qb - qa)
            w = CAP_W_TOP + (CAP_W_BOT - CAP_W_TOP) * t
            ch = max(0.0, 28.0 - (qb - q) * r)           # lower corners chamfered 28 at 45 deg
            ct = max(0.0, 14.0 - (q - qa) * r)           # upper corners rounded off 14
            return (w / 2.0 - ch - ct) / r

        def cap_field(p, q, r=r_cap):
            e = min((cap_hw(q) - abs(p)) * r, (q - qa) * r, (qb - q) * r)
            return CAP_T + G.edge_profile(e, 1.1, 4.0, 2.0)
        ob = G.slab(f"Pauldron.{side}.Tier1.Cap", coll, cap.surf(CAP_PAD), lambda q: (-cap_hw(q), cap_hw(q)), qa, qb,
                    CAP_T, M["shell"], nu=60, nv=70, bevel_mm=0.8, t_field_fn=cap_field)
        rigid.append((ob, f"upperarm01.{side}"))
        # round 6: the foam liner under the cap, and a webbing link from its top edge up over the strap pad
        ins = 5.0 / r_cap
        ob = G.slab(f"Pauldron.{side}.Tier1.Foam", coll, cap.surf(CAP_PAD - CAP_FOAM + 0.2),
                    lambda q: (-cap_hw(q) + ins, cap_hw(q) - ins), qa + ins, qb - ins, CAP_FOAM - 0.4, M["foam"],
                    nu=30, nv=30, bevel_mm=1.2)
        rigid.append((ob, f"upperarm01.{side}"))
        qs_l = np.linspace(qa + 12.0 / r_cap, qa - CAP_LINK, 14)
        lift_l = [CAP_PAD + CAP_T + 0.3 if q > qa + 1.0 / r_cap else 0.6 for q in qs_l]
        pts = [cap.surf(lf)(0.0, q) for q, lf in zip(qs_l, lift_l)]
        path = np.array([pp for pp, _ in pts])
        for k_ in range(1, len(path) - 1):
            path[k_] = 0.25 * path[k_ - 1] + 0.5 * path[k_] + 0.25 * path[k_ + 1]
        ob = G.strip(f"Pauldron.{side}.Tier1.Link", coll, path, [nn_ for _, nn_ in pts], 25.0, 1.6, M["black"],
                     bevel_mm=0.4)
        rigid.append((ob, f"upperarm01.{side}"))
        # two dome rivets (the drawn studs): on the top facet and low on the outer face
        for k, (pp, qq) in enumerate(((0.12, qa + 0.25 * (qb - qa)), (-0.06, qb - 16.0 / r_cap))):
            pt, nt = cap.surf(CAP_PAD + CAP_T + 0.1)(pp, qq)
            ob = G.hw_object(f"Pauldron.{side}.Tier1.Rivet.{k + 1}", coll, GH.rivet(7.0, 2.2), G.frame(pt, e1, nt),
                             M["metal"])
            rigid.append((ob, f"upperarm01.{side}"))
        S["cap_radius_mm"] = round(r_cap, 1)
        if side == "L":
            # the emblem: a rounded-square plate 1 mm proud on the cap's outer face, centred low on the cap.
            # Round 8 (critic m34): EMBLEM_W x EMBLEM_H with corners of EMBLEM_R, as drawn
            # (ref/zoom_armour_emblem_x16); it was a 50 x 95 shield tapering to a point, which with R003's
            # triangle outline read as "a pointed V or crown tab"
            qe = qa + (qb - qa) * 0.60
            r_emb = r_cap + CAP_PAD + CAP_T + 1.4      # the plate's own radius (round 8: r_cap made it 80 mm tall)
            he = 0.5 * EMBLEM_H / r_emb

            def emb_hw(q, r=r_cap, q0=qe - he, q1=qe + he, re=r_emb):
                d = min(q - q0, q1 - q) * re           # mm from the nearer end (top or bottom edge)
                k = EMBLEM_R - min(max(d, 0.0), EMBLEM_R)
                return (0.5 * EMBLEM_W - EMBLEM_R + float(np.sqrt(max(EMBLEM_R ** 2 - k ** 2, 0.0)))) / r
            ob = G.slab("Pauldron.L.Tier1.Emblem", coll, cap.surf(CAP_PAD + CAP_T + 1.4),
                        lambda q: (-emb_hw(q), emb_hw(q)), qe - he, qe + he, 1.0, M["emblem"], nu=10, nv=18,
                        bevel_mm=0.4)
            S["emblem_decal_uv"] = decal_uv(ob)
            rigid.append((ob, "upperarm01.L"))

        # ------------------------------------------------ forearm guard
        d_fa, f_fa, l_fa = G.limb_frame(el, wr, side)
        t_rad = G.unit(C.bone_mm(f"finger2-1.{side}") - C.bone_mm(f"finger5-1.{side}"))
        dors = np.cross(t_rad, d_fa) if side == "L" else np.cross(d_fa, t_rad)
        dors = G.unit(dors - d_fa * np.dot(dors, d_fa))
        e1f = G.unit(np.cross(d_fa, dors))
        fa = LimbSurf(under_fa, el, d_fa, dors, e1f, (-math.pi, math.pi), (40.0, 270.0), nth=48, ns=26, iters=4,
                      outward=True)
        sl_surf = fa.surf(0.5)

        def sleeve_surf(u, v):
            d0 = SLEEVE_D[0] + SLEEVE_FLEX_EXTRA * 0.5 * (1.0 - math.cos(u))     # dorsal 52 .. flexor 92
            return sl_surf(u, d0 + v * (SLEEVE_D[1] - d0))
        collapse = {f"upperarm01.{side}": f"lowerarm01.{side}", f"upperarm02.{side}": f"lowerarm01.{side}"}
        ob = G.slab(f"Guard.{side}.Sleeve", coll, sleeve_surf, None, 0.0, 1.0, SLEEVE_T, M["black"], nu=48, nv=20,
                    bevel_mm=1.0, closed_u=True)
        soft.append((ob, collapse))
        base_off = 0.5 + SLEEVE_T + GUARD_FOAM + 0.5
        built = {}          # name -> (StraightSurf, offset fn, wall, half arc mm, d range) of the plates built so far
        S["guard"] = {}
        for k, drng, arc, wall, bone, curve in GUARD:
            ss = StraightSurf(under_fa, el, d_fa, dors, e1f, drng[0] - 4.0, drng[1] + 4.0)
            half = math.radians(arc / 2.0) * ss.r_nom
            # lap over the plate below (built before) with a flared lip: the plate keeps base_off and only its
            # distal end rises, over 10 mm, to clear the lower plate's outer face, bead and 0.7 mm
            lo, extra = drng[1], 0.0
            for (s2, off2, wall2, half2_, d2) in built.values():
                lo_, hi_ = max(drng[0], d2[0]), min(drng[1], d2[1])
                if hi_ <= lo_:
                    continue
                lo = min(lo, lo_)
                for sv in np.linspace(lo_, hi_, 6):
                    for u in np.linspace(-half2_, half2_, 25):
                        th = u / s2.r_nom
                        extra = max(extra, s2.radius(th, sv) + off2(sv) + wall2 + 0.9 + 0.7 - ss.radius(th, sv)
                                    - base_off)

            def offf(v, lo=lo, extra=extra):
                return base_off + extra * G.smoothstep(v, lo - 10.0, lo)

            def dmap(u, w, drng=drng, half=half, curve=curve):
                d0 = drng[0] + curve * (u / half) ** 2          # the elbow band's edge recedes at its sides
                return d0 + w * (drng[1] - d0)

            def psurf(u, w, ss=ss, offf=offf, dmap=dmap):
                r = ss.r_nom

                def f(uu, ww):
                    d = dmap(uu, ww)
                    return ss.point(uu / r, d, offf(d))
                return f(u, w), numeric_normal(f, u, w, ss.dirv(u / r), h=0.02)

            rib = k == "Main"
            tf = plate_t(wall, half, drng[0], drng[1], rib=rib, grooves=rib)

            def tfield(u, w, tf=tf, dmap=dmap, drng=drng, half=half, curve=curve):
                d0 = drng[0] + curve * (u / half) ** 2
                return tf(u, dmap(u, w) - d0 + drng[0])
            ob = G.slab(f"Guard.{side}.{k}", coll, psurf, lambda w, h=half: (-h, h), 0.0, 1.0, wall, M["shell"],
                        nu=max(40, int(2 * half / 2.2)), nv=max(10, int((drng[1] - drng[0]) / 2.2)), bevel_mm=0.7,
                        t_field_fn=tfield)
            mid = el + d_fa * (0.5 * (drng[0] + drng[1]))
            hit, _n = under_fa.hit(mid + dors * 200.0, -dors, 200.0)
            gpt = hit if hit is not None else mid
            mounts.append((ob, gpt))
            # foam under the plate: a dark step under its lip
            hf = half - 4.0

            def fsurf(u, w, ss=ss, dmap=dmap):
                r = ss.r_nom

                def f(uu, ww):
                    return ss.point(uu / r, dmap(uu, ww), base_off - GUARD_FOAM + 0.2)
                return f(u, w), numeric_normal(f, u, w, ss.dirv(u / r), h=0.02)
            ob = G.slab(f"Guard.{side}.{k}.Foam", coll, fsurf, lambda w, h=hf: (-h, h), 0.06, 0.94, GUARD_FOAM - 0.4,
                        M["foam"], nu=20, nv=6, bevel_mm=1.0)
            mounts.append((ob, gpt))
            built[k] = (ss, offf, wall, half, drng)
            S["guard"][k] = {"d": list(drng), "arc_deg": arc, "lip_lift_mm": round(extra, 1),
                             "r_nom": round(ss.r_nom, 1)}
        # the two straps: 25 mm webbing round the flexor side over the sleeve, below the elbow fold (the upper
        # one under the upper plate's edges, the lower one on the wrist band), each through a ladder-lock
        # riveted on the plate's edge
        for k, dm in (("Main", GUARD_STRAP_D[0]), ("Wrist", GUARD_STRAP_D[1])):
            ss, offf, wall, half, drng = built[k]
            th_e = half / ss.r_nom
            ring = fa.surf(0.5 + SLEEVE_T + 0.3)
            ob = G.slab(f"Guard.{side}.Strap.{k}", coll, ring, lambda v, a=th_e: (a - 0.15, 2 * math.pi - a + 0.15),
                        dm - GUARD_STRAP_W / 2.0, dm + GUARD_STRAP_W / 2.0, 1.4, M["black"], nu=40, nv=4,
                        bevel_mm=0.4)
            soft.append((ob, collapse))
            r = ss.r_nom
            ul = half - 14.0

            def fo(uu, vv, ss=ss, offf=offf, wall=wall, r=r):
                return ss.point(uu / r, vv, offf(vv) + wall)
            pl = fo(ul, dm)
            nl = numeric_normal(fo, ul, dm, ss.dirv(ul / r))
            ob = G.hw_object(f"Guard.{side}.Strap.{k}.LadderLock", coll, GH.ladder_lock(32.0, 26.0, 3.0, 3.0, 2),
                             G.frame(pl + nl * 0.4, d_fa, nl), M["metal"])
            mounts.append((ob, pl))
        S["sleeve_d"] = [SLEEVE_D[0], SLEEVE_D[0] + SLEEVE_FLEX_EXTRA, SLEEVE_D[1]]

        # ------------------------------------------------ round 6: elbow pad (replaces round 1's fin and pad chips)
        E = ELBOW_PAD
        post = G.unit(-f_up + E["lat"] * l_up)               # the point of the elbow, a little to the outside
        post = G.unit(post - d_up * np.dot(post, d_up))
        e1e = G.unit(np.cross(d_up, post))
        under_e = G.Under(list(under_a.layers))
        ecap = CapSurf(under_e, el, post, e1e, d_up, (-1.05, 1.05), (-1.05, 1.05), n=28, smooth=4)
        r_e = float(np.nanmean(ecap.F.R))
        hw_e, hh_e = E["w"] / 2.0 / (r_e + E["pad"]), E["h"] / 2.0 / (r_e + E["pad"])

        def e_hw(q, hw=hw_e, hh=hh_e):
            t = abs(q) / hh
            return hw * math.sqrt(max(0.0, 1.0 - max(0.0, t - 0.55) ** 2 / 0.45 ** 2 * 0.6))

        def e_field(p, q, r=r_e + E["pad"]):
            e = min((e_hw(q) - abs(p)) * r, (hh_e - abs(q)) * r)
            return E["t"] + G.edge_profile(e, 1.0, 3.0, 1.5) - 1.2 * G.smoothstep(e, 10.0, 12.0)
        # soft-bound, both: a cap mounted as one piece on the elbow skin rotated with half the 107 deg fold and stood
        # off the flexed right elbow at its ends (first try of round 6); per-vertex weights let it wrap the point
        ob = G.slab(f"ElbowPad.{side}.Base", coll, ecap.surf(0.6), lambda q: (-e_hw(q) - 0.08, e_hw(q) + 0.08),
                    -hh_e - 0.08, hh_e + 0.08, E["base_t"], M["black"], nu=20, nv=22, bevel_mm=1.5)
        soft.append((ob, None))
        ob = G.slab(f"ElbowPad.{side}.Cap", coll, ecap.surf(0.6 + E["base_t"] + 0.3), lambda q: (-e_hw(q), e_hw(q)),
                    -hh_e, hh_e, E["t"], M["shell"], nu=40, nv=44, bevel_mm=0.7, t_field_fn=e_field)
        soft.append((ob, None))
        # the straps: round the upper arm above the joint and round the forearm below it
        for nm_s, a0, dd, s_c, coll_map in (("Up", gh, d_up, float(np.dot(el - gh, d_up)) - E["strap_up"],
                                             {f"lowerarm01.{side}": f"upperarm02.{side}"}),
                                            ("Down", el, d_fa, E["strap_dn"],
                                             {f"upperarm01.{side}": f"lowerarm01.{side}", f"upperarm02.{side}": f"lowerarm01.{side}"})):
            fr = G.limb_frame(a0, a0 + dd * 100.0, side)
            ring = LimbSurf(under_a, a0, dd, fr[1], fr[2], (-math.pi, math.pi), (s_c - 16.0, s_c + 16.0), nth=48,
                            ns=6, iters=3, outward=True)
            # on the flexed right arm the upper strap leaves out the front of the elbow (the crease, where the biceps
            # meets the forearm: a full ring there went 13 mm into the shirt): it runs round the back and sides only
            # and its ends lie in the fold; on the left arm, whose front shows, it stays a full ring
            if nm_s == "Up" and side == "R":
                ob = G.slab(f"ElbowPad.{side}.Strap.{nm_s}", coll, ring.surf(0.6), lambda v: (math.pi - 2.2, math.pi + 2.2),
                            s_c - E["strap_w"] / 2.0, s_c + E["strap_w"] / 2.0, 1.6, M["black"], nu=40, nv=3,
                            bevel_mm=0.4)
            else:
                ob = G.slab(f"ElbowPad.{side}.Strap.{nm_s}", coll, ring.surf(0.6), lambda v: (-math.pi, math.pi),
                            s_c - E["strap_w"] / 2.0, s_c + E["strap_w"] / 2.0, 1.6, M["black"], nu=48, nv=3,
                            bevel_mm=0.4, closed_u=True)
            soft.append((ob, coll_map))
        S["elbow_pad_radius_mm"] = round(r_e, 1)

        # ------------------------------------------------ knee pad: padded base, domed main cap, upper lame
        kn = C.bone_mm(f"lowerleg01.{side}")
        top = C.bone_mm(f"upperleg02.{side}")
        bot = C.bone_mm(f"lowerleg02.{side}")
        d_k, f_k, l_k = G.limb_frame(top, bot, side)
        s_kn = float(np.dot(kn - top, d_k))
        leg = LimbSurf(under_l, top, d_k, f_k, l_k, (-1.6, 1.6), (s_kn - 150.0, s_kn + 150.0), nth=36, ns=30,
                       iters=6)
        r_k = float(leg.F(0.0, s_kn)) + 2.0
        sc = s_kn - KNEE_DZ     # v up = -s; the cap centre KNEE_DZ (negative = below) from the joint

        def dome(u, v):
            # round 6: a faceted dome: planar ramps from the outline up to a flat central plate (the drawn cap's
            # facets), the edges between facets softened over 3 mm
            es = max(0.0, octagon_hw(v) - abs(u)) / KNEE_FACET[0]
            et = max(0.0, KNEE_HH - v) / KNEE_FACET[1]
            eb = max(0.0, v + KNEE_HH) / KNEE_FACET[2]
            k = 0.05
            m = -k * math.log(math.exp(-es / k) + math.exp(-et / k) + math.exp(-eb / k) + math.exp(-1.0 / k))
            return KNEE_DOME * max(0.0, m)

        def kvs(off, domed=False):
            base_f = leg.surf(off, r0=r_k)

            def f(u, v):
                p, n = base_f(u, sc - v)
                if domed:
                    h = dome(u, v)
                    p = p + n * h
                    # normal of the domed surface, numerically
                    n = numeric_normal(lambda uu, vv: base_f(uu, sc - vv)[0] + base_f(uu, sc - vv)[1] * dome(uu, vv),
                                       u, v, n)
                return p, n
            return f

        def knee_field(v0, v1, wall, ridge=True):
            def f(u, v):
                e = min(octagon_hw(v) - abs(u), v - v0, v1 - v)
                t = wall + G.edge_profile(e, 1.2, 2.5, 1.5)
                t -= 2.0 * G.smoothstep(e, 11.0, 13.5)                 # the centre panel, 2 mm below the frame
                if ridge and e > 13.5:
                    t += 1.6 * (1.0 - G.smoothstep(abs(u), 4.0, 8.0))  # the moulded centre ridge
                # round 6: the frame's slots (the drawn dark holes): three a side, 18 x 5, 1.6 deep
                if 3.5 < e < 10.0 and abs(u) > octagon_hw(v) - 11.0:
                    for vk in (-42.0, -4.0, 34.0):
                        if abs(v - vk) < 9.0:
                            t -= 1.6 * (1.0 - G.smoothstep(abs(v - vk), 7.0, 9.0)) * G.smoothstep(e, 3.5, 5.0) * \
                                (1.0 - G.smoothstep(e, 8.0, 10.0))
                return t
            return f
        mb = 12.0
        # round 6: the padded base fills the cap's dome (the foam a hard cap sits on), so the cap lies on it
        ob = G.slab(f"Kneepad.{side}.Base", coll, kvs(KNEE_BASE_OFF, True),
                    lambda v: (-octagon_hw(v) - mb, octagon_hw(v) + mb), -KNEE_HH - mb, KNEE_HH + mb, KNEE_BASE_T,
                    M["black"], nu=24, nv=28, bevel_mm=3.0, segments=3)
        soft.append((ob, None))                    # padded neoprene: follows the knee pocket
        cap_off = KNEE_BASE_OFF + KNEE_BASE_T + 0.8
        v0m, v1m = -KNEE_HH, KNEE_HH
        ob = G.slab(f"Kneepad.{side}.Cap", coll, kvs(cap_off, True), lambda v: (-octagon_hw(v), octagon_hw(v)),
                    v0m, v1m, KNEE_CAP_T, M["knee"], nu=64, nv=60, bevel_mm=0.8,
                    t_field_fn=knee_field(v0m, v1m, KNEE_CAP_T))
        S["cap_frame_share"] = frame_wear(ob, lambda v: (-octagon_hw(v), octagon_hw(v)), v0m, v1m, 64, 60, octagon_hw)
        # round 6: the cap rides the skin's weights at the kneecap (rigid on the shin, the round-5 caps swung off the
        # pocket wherever the knee bent or the shin twisted against the thigh: the right one gaped at the outer knee)
        kpoint, _n = kvs(0.0)(0.0, 0.0)
        mounts.append((ob, kpoint))
        # red tab on the lateral side facet (v 10 in the cap's frame), lying on it
        pt, nt = kvs(cap_off + KNEE_CAP_T + 0.2, True)(KNEE_HW - 9.0, 12.0)
        ob = G.rbox(f"Kneepad.{side}.Tab", coll, (30.0, 14.0, 3.0), G.frame(pt + nt * 1.6, -d_k, nt), M["red"],
                    bevel_mm=1.2)
        mounts.append((ob, kpoint))
        # strap: 38 mm elastic round the back of the knee; ladder-lock and tan tail on the medial side
        ring = LimbSurf(under_l, top, d_k, f_k, l_k, (-math.pi, math.pi), (s_kn - 30.0, s_kn + 40.0), nth=60,
                        ns=8, iters=3)
        th0 = (KNEE_HW + 6.0) / r_k
        s_st = s_kn + 10.0
        ob = G.slab(f"Kneepad.{side}.Strap", coll, ring.surf(1.4), lambda v: (th0, 2 * math.pi - th0 - 0.30),
                    s_st - 19.0, s_st + 19.0, 2.0, M["black"], nu=30, nv=3, bevel_mm=0.5)
        soft.append((ob, None))
        thl = -(th0 + 0.17)
        pl, nl = ring.surf(1.4 + 2.0 + 0.2)(thl, s_st)
        ob = G.hw_object(f"Kneepad.{side}.LadderLock", coll, GH.ladder_lock(50.0, 32.0, 4.0, 3.5, 2),
                         G.frame(pl + nl * 1.8, d_k, nl), M["metal"])
        mounts.append((ob, pl))      # round 6: on its strap (rigid on the shin it stood 6 mm off)
        ob = G.slab(f"Kneepad.{side}.Tail", coll, ring.surf(1.4 + 2.0 + 0.4), lambda v: (thl - 0.62, thl - 0.17),
                    s_st - 18.0, s_st + 18.0, 1.5, M["tan"], nu=10, nv=3, bevel_mm=0.4)
        soft.append((ob, None))
        S["knee_radius_mm"] = round(r_k, 1)
        S["knee_centre_z"] = round(float((top + d_k * sc)[2]), 1)
        out[side] = S

    if carrier is not None:
        for o in list(carrier.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(carrier)

    # ------------------------------------------------ bind
    for ob, bone in rigid:
        G.rigid_bind(ob, rig, bone)
    for ob, collapse in soft:
        G.soft_bind(ob, body, rig, collapse=collapse)
    out["mounted"] = {ob.name: G.mount_bind(ob, rig, body, pt, k=8) for ob, pt in mounts}
    out["rigid"] = {ob.name: bone for ob, bone in rigid}
    out["soft"] = [ob.name for ob, _c in soft]
    G.say(json.dumps({k: v for k, v in out.items() if k in ("L", "R")}))
    out["materials"] = C.library_pass(coll, PART, MATERIALS, side_dust={"L": 1.0, "R": 0.85}, say_tag=TAG)
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
