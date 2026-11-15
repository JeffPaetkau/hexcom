"""Carrier, round 1 blockout: a JPC 2.0 class plate carrier, size Medium (SAPI Medium plates), with its
front and rear plate bags, the front flap, the cummerbund, the padded shoulder straps and their front
roots and adjusters, the hard admin panel, four single rifle-magazine pouches, a double pistol-magazine
carrier on the right flank, a small utility pouch on the left flank, and the radio pouch with the antenna
behind the left shoulder. Notes: scripts/parts/carrier.md.

  "$SGT_BLENDER" -b --python scripts/parts/carrier.py [-- --no-render]
  -> cache/parts/carrier.blend (Part.Carrier), cache/parts/carrier.json, renders/carrier/*.png

Method: the plates are rigid multi-curve shells, so each bag's inner face is an analytic surface (a plane
fitted to the chest or back in the plate's area, bent by the SAPI curvatures R 254 across and R 457 along)
pushed out until it clears the shirt everywhere; the bag is a slab on that surface. The cummerbund and
straps follow convex hulls of the torso sections (cloth bridges hollows), offset over the shirt; where the
cummerbund runs behind a bag it is clamped behind the bag's inner face. Pouches and panels are placed on
the bags' outer faces. Everything is bound to Morgan.Rig by weights transferred from the body, with the
arm bones collapsed into the clavicles so the carrier follows the shoulder girdle, not the arms.
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

PART, TAG = "Carrier", "carrier"

# Real dimensions (mm); sources in carrier.md.
PLATE_W, PLATE_H = 241.0, 318.0          # SAPI Medium 9.5 x 12.5 in
PLATE_R_LAT, PLATE_R_LONG = 254.0, 457.0  # multi-curve
BAG_W, BAG_H = 285.0, 340.0              # plate + about 22 per side; top 8 above the plate
BAG_T = 31.0                             # back panel and foam 5 + plate 25 + front wall 1
CORNER_CLIP = 50.0                       # shooter's-cut corners, 45 deg
FLAP_W, FLAP_H, FLAP_T = 255.0, 60.0, 6.0
REAR_RAISE = 15.0                        # the rear bag sits a little higher than the front
CB_H, CB_T = 150.0, 20.0                 # cummerbund: 3 PALS rows, padded
STRAP_X = 125.0                          # strap centre lines either side of the sternum (outside the gaiter)
PAD_W, PAD_T = 70.0, 8.0
ROOT_W, ROOT_T = 38.0, 2.0
PANEL = (175.0, 90.0, 8.0)               # hard admin panel (drawn), canted 2.6 deg, right end up
PANEL_CANT = 2.6
POUCH = (62.0, 32.0, 158.0)              # slim single 5.56 pouch body (Esstac KYWI single class)
POUCH_FLAP = (64.0, 36.0, 24.0)
POUCH_X = (-20.0, 46.0, 112.0)          # three, as drawn; the carbine stock lies where a fourth would be
RADIO_POUCH = (76.0, 57.0, 229.0)        # Fight Light class pouch for a PRC-152 class radio
RADIO_THETA = 128.0                      # deg around the torso from the front toward his left
PISTOL_POUCH = (100.0, 38.0, 105.0)      # double pistol-magazine polymer carrier
UTIL_POUCH = (50.0, 30.0, 70.0)
CLR = 2.0                                # bag inner face over the shirt

COL = {
    "cordura": "#463e34", "pouch": "#3b342b", "flap": "#51473a", "webbing": "#6d5f50", "pad": "#4f463b",
    "binding": "#1c1915", "panel": "#7d705c", "cummerbund": "#2f2a24", "hardware": "#4c4943",
    "radio_pouch": "#3a342c", "radio": "#1d1e1f", "brass": "#8a7550", "steel": "#777f85", "cap": "#151718",
    "poly_black": "#24211e", "poly_tan": "#816f5f", "mag": "#1e1d1c",
}


def notch_z(bd):
    """Suprasternal notch: the deepest point of the front midline between chest and neck (mm)."""
    V, ib = bd["V"], bd["in_body"]
    best = None
    for z in np.arange(1470, 1580, 2.0):
        s = ib & (np.abs(V[:, 0]) < 8) & (np.abs(V[:, 2] - z) < 2.5) & (V[:, 1] < 0)
        if s.any():
            y = V[s, 1].min()
            if best is None or y > best[1]:
                best = (z, y)
    return best


class PlateBag:
    """A plate bag's inner surface: depth w = s_out * y (outward positive), w_in(x, z) = A + b (z - zc) -
    x^2 / 2R_lat - (z - zc)^2 / 2R_long, A set so the surface clears the clothing by CLR everywhere over the
    bag's area. s_out = -1 front, +1 rear."""

    def __init__(self, under, s_out, z_top, z_bot_area, halfw):
        self.s, self.zt = s_out, z_top
        self.zc = z_top - 8.0 - PLATE_H / 2.0
        xs = np.arange(-halfw, halfw + 0.1, 8.0)
        zs = np.arange(z_bot_area, z_top + 0.1, 8.0)
        S = []
        for z in zs:
            for x in xs:
                p, _n = under.hit((x, s_out * 600.0, z), (0.0, -s_out, 0.0), 900.0)
                if p is not None:
                    S.append((x, z, s_out * p[1]))
        S = np.array(S)
        plate = (np.abs(S[:, 0]) < PLATE_W / 2) & (S[:, 1] > self.zc - PLATE_H / 2) & (S[:, 1] < self.zc + PLATE_H / 2)
        dz = S[:, 1] - self.zc
        curv = S[:, 0] ** 2 / (2 * PLATE_R_LAT) + dz ** 2 / (2 * PLATE_R_LONG)
        # the plate's pitch: the one that lies closest to the chest over the plate's area while clearing it
        # everywhere over the bag (a plate rests on the most prominent points and hangs from the straps)
        best = None
        for b in np.linspace(-0.8, 0.8, 321):
            A = np.max(S[:, 2] + CLR - b * dz + curv)
            g = (A + b * dz - curv) - S[:, 2]
            m = float(g[plate].mean())
            if best is None or m < best[0]:
                best = (m, b, A)
        self.b, self.A = float(best[1]), float(best[2])
        gap = (self.A + self.b * dz - curv) - S[:, 2]
        self.gap_stats = {"min": round(float(gap.min()), 1), "p50": round(float(np.median(gap)), 1),
                          "max": round(float(gap.max()), 1)}

    def w_in(self, x, z):
        dz = z - self.zc
        return self.A + self.b * dz - x * x / (2 * PLATE_R_LAT) - dz * dz / (2 * PLATE_R_LONG)

    def point(self, x, z, off=0.0):
        """Point on the inner surface (off = 0) or off mm outward along its normal, and the normal."""
        w = self.w_in(x, z)
        dwdx = -x / PLATE_R_LAT
        dwdz = self.b - (z - self.zc) / PLATE_R_LONG
        n = G.unit(np.array([-dwdx, self.s, -dwdz]))
        p = np.array([x, self.s * w, z])
        return p + n * off, n

    def surf(self, off=0.0):
        return lambda u, v: self.point(u, v, off)


def bag_halfw(z, z_top, w=BAG_W, h=BAG_H, clip=CORNER_CLIP, r=20.0):
    hw = w / 2.0
    z_bot = z_top - h
    if z > z_top - clip:
        return max(hw - clip + (z_top - z), 5.0) if z <= z_top else hw - clip
    if z < z_bot + r:
        dz = r - (z - z_bot)
        return hw - (r - math.sqrt(max(r * r - dz * dz, 0.0)))
    return hw


def torso_ring(under, z, cy, thetas, rmax=420.0):
    """Convex hull radii of the clothed torso section at height z around (0, cy), at angles thetas
    (0 = front -Y, +90 = his left +X)."""
    Q = []
    for th in np.linspace(0, 2 * math.pi, 144, endpoint=False):
        d = np.array([math.sin(th), -math.cos(th), 0.0])
        c = np.array([0.0, cy, z])
        p, _n = under.hit(c + d * rmax, -d, rmax)
        if p is not None:
            Q.append((p[0], p[1]))
    Q = np.array(Q)
    xs, ys = np.sin(thetas), -np.cos(thetas)
    # convex_radii uses angles measured in the standard (x, y) plane
    ang = np.arctan2(ys, xs)
    return G.convex_radii(0.0, cy, Q, ang)


def main(render=True):
    import bpy
    body, rig = C.open_base()
    bd = C.body_data(body)
    clothing = G.load_clothing(rig)
    under_t, note_t = G.clothing_under(bd, clothing, "torso")
    G.say("torso surface:", note_t)
    coll = C.part_collection(PART)
    M = {k: G.mat(f"Carrier.Mat.{k.title().replace('_', '')}", v) for k, v in COL.items()}
    nz, ny = notch_z(bd)
    G.say(f"suprasternal notch z {nz:.0f} y {ny:.0f}")
    out = {"notch_mm": [round(float(nz), 1), round(float(ny), 1)], "under": note_t}

    # ---------------------------------------------------------------- plate bags
    zt_f = nz                           # bag top at the notch, plate top 8 below it
    zb_f = zt_f - BAG_H
    hem = zb_f - FLAP_H
    front = PlateBag(under_t, -1, zt_f, hem, BAG_W / 2.0)
    zt_r = zt_f + REAR_RAISE
    zb_r = zt_r - BAG_H
    rear = PlateBag(under_t, +1, zt_r, zb_r, BAG_W / 2.0)
    out["front_bag"] = {"top": zt_f, "bottom": zb_f, "hem": hem, "tilt_dw_dz": round(front.b, 3),
                        "gap_to_shirt": front.gap_stats}
    out["rear_bag"] = {"top": zt_r, "bottom": zb_r, "tilt_dw_dz": round(rear.b, 3), "gap_to_shirt": rear.gap_stats}
    G.say("front bag", out["front_bag"], "rear bag", out["rear_bag"])

    def hw_f(v):
        h = bag_halfw(v, zt_f)
        return (-h, h)

    def hw_r(v):
        h = bag_halfw(v, zt_r)
        return (-h, h)
    def taper(zt):
        """Bag thickness: the full 31 over the plate, falling to 14 at the bag's margin (fabric and foam)."""
        zpc = zt - 8.0 - PLATE_H / 2.0

        def f(u, v):
            ex = max(abs(u) - (PLATE_W / 2.0 - 6.0), 0.0)
            ez = max(abs(v - zpc) - (PLATE_H / 2.0 - 6.0), 0.0)
            # shooter's cut: the plate's corners are clipped like the bag's
            ec = max((abs(u) + (v - zt + 8.0)) - (PLATE_W / 2.0 - CORNER_CLIP + 2.0), 0.0) / math.sqrt(2)
            e = max(ex, ez, ec)
            return BAG_T - (BAG_T - 14.0) * min(e / 16.0, 1.0)
        return f
    bag_f = G.slab("Carrier.Front.Bag", coll, front.surf(), hw_f, zb_f, zt_f, BAG_T, M["cordura"], nu=36, nv=40,
                   bevel_mm=6.0, segments=3, t_field_fn=taper(zt_f))
    bag_r = G.slab("Carrier.Rear.Bag", coll, rear.surf(), hw_r, zb_r, zt_r, BAG_T, M["cordura"], nu=36, nv=40,
                   bevel_mm=6.0, segments=3, t_field_fn=taper(zt_r))
    flap = G.slab("Carrier.Front.Flap", coll, front.surf(), lambda v: (-FLAP_W / 2, FLAP_W / 2), hem, zb_f + 15.0,
                  FLAP_T, M["cordura"], nu=24, nv=6, bevel_mm=2.5)
    bag_f = G.join(bag_f, [flap])               # the flap is sewn under the bag's bottom edge: one item

    # ---------------------------------------------------------------- cummerbund (left and right halves)
    zc0, zc1 = hem + 2.0, hem + 2.0 + CB_H
    # torso centre line (y) at the cummerbund: midway between front and back
    ys = []
    for z in (zc0, (zc0 + zc1) / 2, zc1):
        pf, _ = under_t.hit((0, -600, z), (0, 1, 0))
        pb, _ = under_t.hit((0, 600, z), (0, -1, 0))
        ys.append((pf[1] + pb[1]) / 2.0)
    cy = float(np.mean(ys))
    nth = 72
    rows = 8
    zrows = np.linspace(zc0, zc1, rows + 1)

    def front_halfw(z):
        if zb_f <= z <= zt_f:
            return bag_halfw(z, zt_f)
        if hem <= z < zb_f:
            return FLAP_W / 2.0
        return 0.0

    def rear_halfw(z):
        return bag_halfw(z, zt_r) if zb_r <= z <= zt_r else 0.0

    for side, sgn in (("L", 1.0), ("R", -1.0)):
        # angular extent at mid height: from 25 mm behind the front bag's edge to 25 mm behind the rear bag's
        zm = (zc0 + zc1) / 2
        th_all = np.radians(np.linspace(0.5, 179.5, 360))
        R = torso_ring(under_t, zm, cy, sgn * th_all)
        x = np.sin(th_all) * R
        yv = cy - np.cos(th_all) * R
        fh = max(front_halfw(zm) - 25.0, 0.0)
        rh = max(rear_halfw(zc1 - 10) - 25.0, 0.0)
        i0 = int(np.argmax((x >= fh) & (yv < cy)))
        back = np.nonzero((x >= rh) & (yv > cy))[0]
        i1 = int(back[-1]) if len(back) else len(th_all) - 1
        thetas = sgn * np.linspace(th_all[i0], th_all[i1], nth)
        Pin, Pout = [], []
        for z in zrows:
            Rz = torso_ring(under_t, z, cy, thetas)
            Rz = G.fill_nan(Rz[None])[0]
            d = np.column_stack([np.sin(thetas), -np.cos(thetas), np.zeros(nth)])
            c = np.array([0.0, cy, z])
            pin = c + d * (Rz[:, None] + 1.0)
            pout = c + d * (Rz[:, None] + 1.0 + CB_T)
            # behind the front bag / flap and the rear bag: keep both faces behind the bag's inner face
            for arr in (pin, pout):
                for k in range(nth):
                    px, py, pz = arr[k]
                    if py < cy and abs(px) < front_halfw(pz):
                        lim = -(front.w_in(px, pz) - 0.8)
                        arr[k, 1] = max(py, lim)
                    if py > cy and abs(px) < rear_halfw(pz):
                        lim = rear.w_in(px, pz) - 0.8
                        arr[k, 1] = min(py, lim)
            Pin.append(pin)
            Pout.append(pout)
        Pin, Pout = np.array(Pin), np.array(Pout)
        V, F = G.slab_from_grid(Pin, np.zeros_like(Pin), 0.0, outer=Pout)
        G.new_mesh(f"Carrier.Cummerbund.{side}", V, F, coll, M["cummerbund"], bevel_mm=4.0)
    out["cummerbund"] = {"z": [round(zc0), round(zc1)], "thick": CB_T}

    # ---------------------------------------------------------------- admin panel (moulded to the bag face)
    pw, ph, pt = PANEL
    pzc = zt_f - 24.0 - ph / 2.0
    pxc = -5.0
    ca, sa = math.cos(math.radians(-PANEL_CANT)), math.sin(math.radians(-PANEL_CANT))
    sf_out = front.surf(BAG_T + 0.3)

    def panel_surf(u, v):
        return sf_out(pxc + u * ca - v * sa, pzc + u * sa + v * ca)
    G.slab("Carrier.Front.Panel", coll, panel_surf, lambda v: (-pw / 2, pw / 2), -ph / 2, ph / 2, pt, M["panel"],
           nu=16, nv=8, bevel_mm=3.0, segments=2)
    out["panel"] = {"centre_xz": [pxc, round(pzc)], "size": PANEL, "cant_deg": PANEL_CANT}

    # ---------------------------------------------------------------- magazine pouches
    pz0 = zb_f + 37.0                     # pouch bottoms well above the hem (as drawn); clears the posed carbine
    pcz = pz0 + POUCH[2] / 2.0
    for i, x in enumerate(POUCH_X):
        p, n = front.point(x, pcz, BAG_T + 0.3)
        # pouch axes: width along x, height along world up projected, depth along the normal
        up = G.unit(np.array([0.0, 0.0, 1.0]) - n * n[2])
        xa = G.unit(np.cross(up, n))
        R3 = np.column_stack([xa, n, up])
        Mb = np.eye(4)
        Mb[:3, :3] = R3
        Mb[:3, 3] = p + n * POUCH[1] / 2.0
        Mfl = np.eye(4)
        Mfl[:3, :3] = R3
        Mfl[:3, 3] = p + n * (POUCH_FLAP[1] / 2.0) + up * (POUCH[2] / 2.0 + 4.0)
        G.boxes(f"Carrier.Pouch.{i + 1}", coll, [(POUCH, Mb), (POUCH_FLAP, Mfl)], M["pouch"], bevel_mm=6.0)
    out["mag_pouches"] = {"x": POUCH_X, "z": [round(pz0), round(pz0 + POUCH[2] + 4 + POUCH_FLAP[2] / 2)],
                          "body": POUCH, "flap": POUCH_FLAP}

    # ---------------------------------------------------------------- shoulder straps
    straps = {}
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        x = sgn * STRAP_X
        c = np.array([x, 0.0, zt_f - 60.0])
        # convex hull of the torso (shoulder, trapezius, neck base) in the plane x = const
        Q = []
        phis = np.radians(np.linspace(-120, 120, 121))
        for ph in phis:
            d = np.array([0.0, math.sin(ph), math.cos(ph)])
            best = None
            for dx in (-PAD_W / 2, -PAD_W / 4, 0.0, PAD_W / 4, PAD_W / 2):   # over the gaiter where it lies under the pad
                cc = c + np.array([sgn * dx, 0.0, 0.0])
                p, _n = under_t.hit(cc + d * 350.0, -d, 350.0)
                if p is not None:
                    r = float(np.dot(p - cc, d))
                    best = r if best is None else max(best, r)
            if best is not None:
                q = c + d * best
                Q.append((q[1], q[2]))
        Q = np.array(Q)
        ang = np.arctan2(np.cos(phis), np.sin(phis))     # (y, z) plane angle of each phi
        Rr = G.convex_radii(c[1], c[2], Q, ang)
        pts = np.array([c + np.array([0.0, math.sin(ph), math.cos(ph)]) * (r + 1.0) for ph, r in zip(phis, Rr)
                        if not np.isnan(r)])
        # keep the arc between 15 mm above the front bag's top and 15 mm above the rear bag's top
        ztop_f = zt_f - max(0.0, abs(x) - (BAG_W / 2 - CORNER_CLIP))
        ztop_r = zt_r - max(0.0, abs(x) - (BAG_W / 2 - CORNER_CLIP))
        keep = ((pts[:, 1] < c[1]) & (pts[:, 2] > ztop_f + 15.0)) | ((pts[:, 1] >= c[1]) & (pts[:, 2] > ztop_r + 15.0))
        arc = pts[keep]
        nrm = [G.unit(p - c) for p in arc]
        G.strip(f"Carrier.Strap.{side}.Pad", coll, arc, nrm, PAD_W, PAD_T, M["pad"], bevel_mm=2.5)
        # front root: from the pad's front end over the bag's top edge and down the bag face to z 1430
        # the highest point of the bag's top edge under the strap's width (the top corners are clipped)
        ztop_hi = zt_f - max(0.0, abs(x) - ROOT_W / 2 - (BAG_W / 2 - CORNER_CLIP))
        root = [arc[0] + np.array([0.0, -2.0, 0.0]), front.point(x, ztop_hi, BAG_T + 2.0)[0] + np.array([0.0, 0.0, 5.0])]
        for z in np.linspace(ztop_hi - 12.0, zt_f - 95.0, 8):
            root.append(front.point(x, z, BAG_T + 0.6)[0])
        root = np.array(root)
        rn = [front.point(p[0], min(p[2], ztop_f), 0.0)[1] for p in root]
        rn[0] = rn[1] = G.unit(np.array([0.0, -0.4, 1.0]))
        straps[side] = (root, rn)
        # ladder-lock (38 mm) at the pad's front end
        k = 4                                   # its centre 4 stations (about 25 mm) up the pad from the end
        t0 = G.unit(arc[k + 1] - arc[k - 1])
        n0 = G.unit((arc[k] - c) - t0 * np.dot(arc[k] - c, t0))
        Ml = G.frame(arc[k] + n0 * (PAD_T + 4.0), np.cross(t0, n0), n0)
        G.rbox(f"Carrier.Strap.{side}.LadderLock", coll, (52.0, 44.0, 6.0), Ml, M["hardware"], bevel_mm=1.5)
        # rear root down the rear bag face
        rr = [arc[-1]]
        for z in np.linspace(ztop_r - 6.0, zt_r - 70.0, 5):
            rr.append(rear.point(x, z, BAG_T + 0.6)[0])
        rr = np.array(rr)
        rrn = [rear.point(p[0], min(p[2], ztop_r), 0.0)[1] for p in rr]
        G.strip(f"Carrier.Strap.{side}.RearRoot", coll, rr, rrn, ROOT_W, ROOT_T, M["webbing"], bevel_mm=0.5)
    # the front roots lie over the panel where they cross it: lift them onto the outermost carrier surface
    panel_ob = bpy.data.objects["Carrier.Front.Panel"]
    lay = G.Under([(G.objects_bvh([bag_f, panel_ob]), 0.6)])
    for side, (root, rn) in straps.items():
        R2 = [root[0], root[1]]
        for p, n in zip(root[2:], rn[2:]):
            # the outermost surface under the strap's whole width (the bag thins at the shooter's cut)
            best = None
            for dx in (-ROOT_W / 2, 0.0, ROOT_W / 2):
                q, _ = lay.hit(p + n * 60.0 + np.array([dx, 0.0, 0.0]), -n, 120.0)
                if q is not None:
                    dpt = float(np.dot(q - p, n))
                    best = dpt if best is None else max(best, dpt)
            R2.append(p + n * best if best is not None else p)
        G.strip(f"Carrier.Strap.{side}.Root", coll, np.array(R2), rn, ROOT_W, ROOT_T, M["webbing"], bevel_mm=0.5)
    out["straps"] = {"x": STRAP_X, "pad": [PAD_W, PAD_T], "root": [ROOT_W, ROOT_T]}

    # ---------------------------------------------------------------- side and back items on the cummerbund
    carrier_now = [o for o in coll.all_objects if o.name.startswith(("Carrier.Cummerbund", "Carrier.Rear.Bag",
                                                                     "Carrier.Front.Bag"))]
    lay_side = G.Under([(G.objects_bvh(carrier_now), 0.8)] + under_t.layers)

    def on_side(theta_deg, zc, size):
        th = math.radians(theta_deg)
        d = np.array([math.sin(th), -math.cos(th), 0.0])
        c = np.array([0.0, cy, zc])
        p, n = lay_side.hit(c + d * 500.0, -d, 500.0)
        n = G.unit(np.array([n[0], n[1], 0.0]))
        up = np.array([0.0, 0.0, 1.0])
        xa = G.unit(np.cross(up, n))
        Mx = np.eye(4)
        Mx[:3, :3] = np.column_stack([xa, n, up])
        Mx[:3, 3] = p + n * size[1] / 2.0
        Mx = G.seat(lay_side, Mx, size)
        return Mx, p, n, xa

    # radio pouch behind the left shoulder, radio top and antenna
    rz = zb_r + 125.0
    Mr, pr, nr, xr = on_side(RADIO_THETA, rz, RADIO_POUCH)
    G.rbox("Carrier.Radio.Pouch", coll, RADIO_POUCH, Mr, M["radio_pouch"], bevel_mm=8.0)
    top = Mr[:3, 3] + np.array([0.0, 0.0, RADIO_POUCH[2] / 2.0])
    Mtop = Mr.copy()
    Mtop[:3, 3] = top + np.array([0.0, 0.0, 9.0])
    G.rbox("Carrier.Radio.Body", coll, (66.0, 40.0, 18.0), Mtop, M["radio"], bevel_mm=4.0)
    # antenna on the radio top, outer-front corner, leaning 5 deg back
    base = top + np.array([0.0, 0.0, 18.0]) + xr * 18.0 * (1 if xr[1] < 0 else -1)
    ax = G.unit(np.array([0.0, math.sin(math.radians(5.0)), math.cos(math.radians(5.0))]))
    G.cyl("Carrier.Radio.Antenna.Steel", coll, base, ax, 13.0, 60.0, M["steel"])
    G.cyl("Carrier.Radio.Antenna.Brass", coll, base + ax * 60.0, ax, 15.0, 55.0, M["brass"])
    G.cyl("Carrier.Radio.Antenna.Cap", coll, base + ax * 115.0, ax, 16.0, 22.0, M["cap"], dome=16.0)
    ant_top = base + ax * 153.0
    G.join(bpy.data.objects["Carrier.Radio.Pouch"], [bpy.data.objects[n] for n in (
        "Carrier.Radio.Body", "Carrier.Radio.Antenna.Steel", "Carrier.Radio.Antenna.Brass", "Carrier.Radio.Antenna.Cap")])
    out["radio"] = {"pouch_centre": [round(float(v)) for v in Mr[:3, 3]], "antenna_base": [round(float(v)) for v in base],
                    "antenna_top": [round(float(v)) for v in ant_top], "theta_deg": RADIO_THETA}
    G.say("radio", out["radio"])

    # double pistol-magazine carrier on the right flank (hangs from the cummerbund's lower rows)
    Mp, pp, np_, xp = on_side(290.0, zc0 - 12.0, PISTOL_POUCH)   # hangs from the lowest row, in front of the belt
    G.rbox("Carrier.PistolMags.Body", coll, PISTOL_POUCH, Mp, M["poly_black"], bevel_mm=4.0)
    for k, du in enumerate((-24.0, 24.0)):
        Mq = Mp.copy()
        Mq[:3, 3] = Mp[:3, 3] + xp * du + np_ * (PISTOL_POUCH[1] / 2.0 + 1.7) + np.array([0, 0, -2.0])
        G.rbox(f"Carrier.PistolMags.Plate.{k + 1}", coll, (40.0, 3.0, 92.0), Mq, M["poly_tan"], bevel_mm=1.2)
        Mm = Mp.copy()
        Mm[:3, 3] = Mp[:3, 3] + xp * du + np.array([0, 0, PISTOL_POUCH[2] / 2.0 + 11.8])
        G.rbox(f"Carrier.PistolMags.Mag.{k + 1}", coll, (34.0, 16.0, 23.0), Mm, M["mag"], bevel_mm=2.0)
    out["pistol_mags"] = {"centre": [round(float(v)) for v in Mp[:3, 3]], "size": PISTOL_POUCH}

    # small utility pouch on the left flank, forward column
    Mu, *_ = on_side(78.0, zc1 - 45.0, UTIL_POUCH)
    G.rbox("Carrier.UtilPouch.L", coll, UTIL_POUCH, Mu, M["pouch"], bevel_mm=5.0)

    # ---------------------------------------------------------------- bind and finish
    collapse = G.arms_to_clavicle()
    for ob in list(coll.all_objects):
        G.soft_bind(ob, body, rig, collapse=collapse)
    out["objects"] = sorted(o.name for o in coll.all_objects)
    if render:
        rep = G.finish_part(TAG, coll, body, rig, clothing, (0.0, 0.0, 1330.0), 760.0,
                            ["ref.torso_vest", "ref.soldier_full"], extra=out)
        out["check"] = rep
        with open(os.path.join(C.PARTS_DIR, f"{TAG}.json"), "w") as f:
            json.dump(out, f, indent=1)
    else:
        C.save_part(TAG, coll, extra=out)
    return out


if __name__ == "__main__":
    main(render="--no-render" not in C._argv())
