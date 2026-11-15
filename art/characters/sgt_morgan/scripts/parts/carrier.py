"""Carrier, round 2: a JPC 2.0 class plate carrier, size Medium (SAPI Medium plates), with its front and rear
plate bags (bound edges), the front flap, the cummerbund, MIL-spec PALS rows on the front bag, the flap and the
cummerbund, the padded shoulder straps (pad, centre webbing, 38 mm ladder-lock, root, tail and keepers on the
front, a root on the rear), the hard admin panel, three single rifle-magazine pouches (flap, pull tab), a double
pistol-magazine carrier on the right flank, a small utility pouch on the left flank, and the radio pouch with
the radio top, its knobs, the bungee and the antenna behind the left shoulder. Notes: scripts/parts/carrier.md.

  "$SGT_BLENDER" -b --python scripts/parts/carrier.py [-- --no-render]
  -> cache/parts/carrier.blend (Part.Carrier), cache/parts/carrier.json, renders/carrier/*.png

Method: the plates are rigid multi-curve shells, so each bag's inner face is an analytic surface (a plane
fitted to the chest or back in the plate's area, bent by the SAPI curvatures R 254 across and R 457 along)
pushed out until it clears the shirt (and the gaiter's skirt) everywhere; the bag is a slab on that surface,
its top TOP_DROP below the suprasternal notch. The cummerbund follows convex hulls of the torso sections
(cloth bridges hollows), offset over the shirt; where it runs behind a bag it is clamped behind the bag's
inner face. The shoulder straps lie on the shoulders: at each station over the shoulder the surface under
the pad's whole width is sampled, the pad's cross-section is tilted to the trapezius' slope (not held
horizontal, which made round 1's yoke), and only along its length does it bridge hollows. They run in the
corridor shirt.STRAP, where the gaiter is pressed flat, so they lie on top of it. PALS rows are
lib.gear_webbing.pals_rows strips (25 mm webbing at 38 mm columns, 50.8 mm row pitch) laid on the bag, flap
and cummerbund surfaces; pouches and panels sit on the bags' outer faces over the webbing. Everything is
bound to Morgan.Rig by weights transferred from the body, with the arm bones collapsed into the clavicles
so the carrier follows the shoulder girdle, not the arms. Idempotent: it starts from base.blend every time.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gear_common as G  # noqa: E402
from shirt import STRAP  # noqa: E402  (the strap corridor the gaiter is pressed flat in)
from lib import gear_hardware as GH, gear_webbing as GW, sweep as SW  # noqa: E402

PART, TAG = "Carrier", "carrier"

# Real dimensions (mm); sources in carrier.md.
PLATE_W, PLATE_H = 241.0, 318.0          # SAPI Medium 9.5 x 12.5 in
PLATE_R_LAT, PLATE_R_LONG = 254.0, 457.0  # multi-curve
BAG_W, BAG_H = 285.0, 340.0              # plate + about 22 per side; top 8 above the plate
BAG_T = 31.0                             # back panel and foam 5 + plate 25 + front wall 1
CORNER_CLIP = 50.0                       # shooter's-cut corners, 45 deg
FLAP_W, FLAP_H, FLAP_T = 255.0, 34.0, 6.0          # JPC class flap carrying one PALS row; round 4: 42 -> 34 (see flap_to_waist)
REAR_RAISE = -25.0                       # rear bag top relative to the throat point (round 1: +15); 50 above the front
CB_H, CB_T = 150.0, 20.0                 # cummerbund: 3 PALS rows, padded
CB_RISE = 45.0                           # the band's rise from the front to the back (clears the belt there)
STRAP_X = STRAP["x"]                     # strap centre lines either side of the sternum (shirt.STRAP)
PAD_W, PAD_T = STRAP["w"], 8.0           # JPC class pad, 6 foam + 2 fabric
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
TOP_DROP = 52.0                          # front bag top below the notch (the clavicles' sternal ends); see carrier.md
PANEL_DROP = 6.0                         # admin panel top below the bag top (drawn flush; the binding shows)
POUCH_LIFT = 48.0                        # mag pouch bottoms above the bag bottom (drawn: one row between them
                                         # and the panel, two rows and the hem below)
PALS_W, PALS_T, PALS_COL, PALS_PITCH = 25.4, 1.3, 38.1, 50.8     # MIL-spec PALS (spec 13 §3.3)
BIND_R = 7.0                             # bound edge: 25 mm tape folded over the 14 mm margin
ROOT_X = 105.0                           # front strap roots reach the bag at |x| (the panel's ends)
LOCK = (52.0, 44.0, 4.0, 6.0)            # 38 mm ladder-lock: width, length, bar, thickness (spec 13 §3.6)

COL = {
    "cordura": "#463e34", "pouch": "#3b342b", "flap": "#51473a", "webbing": "#6d5f50", "pad": "#4f463b",
    "binding": "#1c1915", "panel": "#7d705c", "cummerbund": "#2f2a24", "hardware": "#4c4943",
    "radio_pouch": "#3a342c", "radio": "#1d1e1f", "brass": "#8a7550", "steel": "#777f85", "cap": "#151718",
    "poly_black": "#24211e", "poly_tan": "#816f5f", "mag": "#1e1d1c",
    "webbing_pals": "#4d4438", "webbing_cb": "#2a2520", "brass_dark": "#4a3f2c",
}
# Materials round (round 5, 2026-11-15; COL stays the solid-view colour): R000's olive 500D Cordura (made
# seamless) on the bag, flap, pads and cummerbund, 1000D on the pouches, matching olive webbing, black binding,
# the admin panel a lighter, dustier Cordura, polymer buckles, the radio's textured polymer, the brass antenna
# with its rubber cap, olive magazines' black PMAGs.
_CB = {"albedo_hex": "#3a362f"}
MATERIALS = {
    "Carrier.Mat.Cordura": ("Cordura.500D.OliveBrown", "Cordura", {}),
    "Carrier.Mat.Flap": ("Cordura.500D.OliveBrown", "Flap", {"albedo_hex": "#524a3f"}),
    "Carrier.Mat.Pad": ("Cordura.500D.OliveBrown", "Pad", {"albedo_hex": "#4a443a"}),
    "Carrier.Mat.Panel": ("Cordura.500D.OliveBrown", "Panel", {"albedo_hex": "#5a5244", "dust__amount": 1.1}),
    "Carrier.Mat.Cummerbund": ("Cordura.500D.OliveBrown", "Cummerbund", {"albedo_hex": "#403b33"}),
    "Carrier.Mat.Pouch": ("Cordura.1000D.OliveBrown", "Pouch", {}),
    "Carrier.Mat.RadioPouch": ("Cordura.1000D.OliveBrown", "RadioPouch", {"albedo_hex": "#413b33"}),
    "Carrier.Mat.Webbing": ("Webbing.Nylon.OliveBrown", "Webbing", {}),
    "Carrier.Mat.WebbingPals": ("Webbing.Nylon.OliveBrown", "WebbingPals", {"albedo_hex": "#464036"}),
    "Carrier.Mat.WebbingCb": ("Webbing.Nylon.OliveBrown", "WebbingCb", dict(_CB)),
    "Carrier.Mat.Binding": ("Webbing.Nylon.Black", "Binding", {"wear": "cordura.top"}),
    "Carrier.Mat.Hardware": ("Polymer.Black.Smooth", "Hardware", {}),
    "Carrier.Mat.PolyBlack": ("Polymer.Black.Textured", "PolyBlack", {}),
    "Carrier.Mat.PolyTan": ("Polymer.Tan.Moulded", "PolyTan", {}),
    "Carrier.Mat.Mag": ("Polymer.Black.Textured", "Mag", {"albedo_hex": "#2e2d2b"}),
    "Carrier.Mat.Radio": ("Polymer.Black.Textured", "Radio", {}),
    "Carrier.Mat.Brass": ("Metal.Brass.Aged", "Brass", {}),
    "Carrier.Mat.BrassDark": ("Metal.Brass.Aged", "BrassDark", {"f0": (0.22, 0.18, 0.11)}),
    "Carrier.Mat.Steel": ("Metal.Gunmetal", "Steel", {"f0": (0.40, 0.41, 0.42), "aniso": 0.0}),
    "Carrier.Mat.Cap": ("Rubber.Moulded.Black", "Cap", {}),
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
        # the gap along the centre line (|x| < 40), per 40 mm band from the top: where the bag stands off
        rows = {}
        for z0 in np.arange(z_top, z_bot_area, -40.0):
            m = (np.abs(S[:, 0]) < 40) & (S[:, 1] <= z0) & (S[:, 1] > z0 - 40)
            if m.any():
                rows[int(round(z0))] = round(float(np.median(gap[m])), 1)
        self.gap_stats["centre_by_z"] = rows

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


# --------------------------------------------------------------------------- round 2 helpers

def bake_matrix(ob):
    """Apply an object's matrix to its mesh (the binds and the checks expect world-space identity objects)."""
    from mathutils import Matrix
    ob.data.transform(ob.matrix_world)
    ob.matrix_world = Matrix.Identity(4)
    return ob


def split_across(ob, longer=30.0, cuts=6):
    """Cut a strip's long cross edges (its width) so the skin weights can bend it across the shoulder in the
    pose; a 4-corner section stays a flat plank and the shoulder comes through its middle."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    long_e = [e for e in bm.edges if e.calc_length() * (1000.0 if e.calc_length() < 1.0 else 1.0) > longer]
    bmesh.ops.subdivide_edges(bm, edges=long_e, cuts=cuts, use_grid_fill=True)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def flat(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


def tube(name, coll, pts, radius, mat, closed=False, sides=10, squash=None):
    """A round (or squashed) tube along points (mm): bindings, bungee cord."""
    P = SW.Path(np.asarray(pts, float), closed=closed).resampled(3.0)
    ob = SW.Tube(P, radius, sides=sides, squash=squash, caps=not closed).to_object(name, coll)
    return flat(ob, mat)


def bag_outline(zt, zb, hw_fn, n=12):
    """The bag's outline in (u, v), counter-clockwise from the bottom centre (the top corners clipped, the
    bottom corners rounded by bag_halfw)."""
    vs = np.linspace(zb + 0.5, zt - 0.5, 70)
    right = [(hw_fn(v), v) for v in vs]
    left = [(-hw_fn(v), v) for v in vs[::-1]]
    top = [(u, zt) for u in np.linspace(right[-1][0], -right[-1][0], n)[1:-1]]
    bot_r = [(u, zb) for u in np.linspace(0.0, right[0][0], n)[:-1]]
    bot_l = [(u, zb) for u in np.linspace(left[-1][0], 0.0, n)[1:]]
    return bot_r + right + top + left + bot_l


def binding(name, coll, bag, outline, thick_fn, mat):
    """The bound edge: a tube of BIND_R round the bag's outline at its mid-thickness (the bag's margin is 14
    thick, so the tape reads as a rolled edge 15 thick, proud of both faces)."""
    pts = [bag.point(u, v, 0.5 * thick_fn(u, v) + 1.0)[0] for (u, v) in outline]   # proud of the outer face, not the inner
    return tube(name, coll, pts, BIND_R, mat, closed=True, sides=10)


def pals(name, coll, target_ob, rows, ncell, mat, seed=0, start=0.0):
    """PALS rows (lib.gear_webbing.pals_rows) on the target object's surface: rows are control points (mm)
    along each row; ncell cells of PALS_COL each, the first column `start` mm from the row's start."""
    surf = SW.Surface(target_ob)
    cols = start + np.arange(ncell + 1) * PALS_COL
    res = GW.pals_rows(surf, rows, cols, width=PALS_W, thickness=PALS_T, sag=3.0, seed=seed, step=2.0)
    strips = res["strips"]
    ob = GW.webbing(name, strips, part="carrier", material=None, coll=coll)
    flat(ob, mat)
    return ob, res


def ladder_lock(name, coll, origin, across, normal, mat):
    """The 38 mm ladder-lock (lib.gear_hardware.ladder_lock 52 x 44 x 6, slots across) at origin, its width
    along `across`, its run along normal x across, standing on the surface with the given normal."""
    w, ln, bar, t = LOCK
    piece = GH.ladder_lock(w, ln, bar, t, 2, end_bar=15.0)
    Mx = G.frame(np.asarray(origin, float) + G.unit(normal) * (t / 2.0), across, normal)
    ob = GH.to_object(name, piece, matrix=Mx, material=None, coll=coll)
    bake_matrix(ob)
    return flat(ob, mat)


def strap_profile(under, x, sgn, c, phis, width, clear=3.0):
    """The pad's underside over the shoulder in the plane x: for each station angle phi (in the y-z plane round
    c, 0 = straight up, + toward the back) the surface under the pad's whole width is sampled; the pad's
    cross-section tilts to the surface's slope across it (least squares, smoothed along the strap) and rides
    on the highest sample. Returns centre points, pad normals and the slope per station."""
    dxs = np.linspace(-width / 2.0, width / 2.0, 7)
    R = np.full((len(phis), len(dxs)), np.nan)
    for k, ph in enumerate(phis):
        dv = np.array([0.0, math.sin(ph), math.cos(ph)])
        for j, dx in enumerate(dxs):
            cc = c + np.array([sgn * dx, 0.0, 0.0])
            p, _n = under.hit(cc + dv * 350.0, -dv, 350.0)
            if p is not None:
                R[k, j] = float(np.dot(p - cc, dv))
    slope = np.zeros(len(phis))
    for k in range(len(phis)):
        ok = ~np.isnan(R[k])
        if ok.sum() >= 3:
            slope[k] = np.polyfit(dxs[ok], R[k, ok], 1)[0]
    ker = np.ones(9) / 9.0
    slope = np.convolve(np.pad(slope, 4, mode="edge"), ker, mode="valid")
    slope = np.clip(slope, -0.9, 0.9)
    r0 = np.nanmax(R - slope[:, None] * dxs[None, :], axis=1) + clear
    # along its length the pad bridges hollows: the convex hull of the centre line in the y-z plane
    Q = np.array([(c[1] + math.sin(ph) * r, c[2] + math.cos(ph) * r) for ph, r in zip(phis, r0) if not np.isnan(r)])
    ang = np.arctan2(np.cos(phis), np.sin(phis))
    rh = G.convex_radii(c[1], c[2], Q, ang)
    rh = np.where(np.isnan(rh), r0, np.maximum(rh, r0))
    pts, nrm = [], []
    xa = np.array([sgn, 0.0, 0.0])
    for ph, r, b in zip(phis, rh, slope):
        dv = np.array([0.0, math.sin(ph), math.cos(ph)])
        pts.append(c + dv * r)
        nrm.append(G.unit(dv - b * xa))
    return np.array(pts), np.array(nrm), slope



def flap_to_waist(ob, trousers, z_top, z_hem, ramp_end=12.0):
    """Round 4: blend the weights of ob's vertices below z_top (the bag's bottom edge, mm) toward those of the nearest
    vertex of the trousers' shell (rest): none at z_top, all of them from ramp_end mm above the hem down (smoothstep
    between). Returns how many vertices changed."""
    from mathutils import kdtree
    me = ob.data
    zs = np.array([v.co.z for v in me.vertices]) * 1000.0
    sel = np.nonzero(zs < z_top)[0]
    if not len(sel):
        return 0
    tv = trousers.data.vertices
    mt = trousers.matrix_basis
    kd = kdtree.KDTree(len(tv))
    for v in tv:
        kd.insert(mt @ v.co, v.index)
    kd.balance()
    tnames = {g.index: g.name for g in trousers.vertex_groups}
    onames = {g.index: g.name for g in ob.vertex_groups}
    a, b = z_top, z_hem + ramp_end
    for i in sel:
        v = me.vertices[int(i)]
        t = min(max((a - zs[i]) / (a - b), 0.0), 1.0)
        sm = t * t * (3 - 2 * t)
        own = {onames[e.group]: e.weight for e in v.groups}
        _, j, _ = kd.find(ob.matrix_basis @ v.co)
        their = {tnames[e.group]: e.weight for e in tv[j].groups}
        st = sum(their.values()) or 1.0
        so = sum(own.values()) or 1.0
        new = {}
        for k, w in own.items():
            new[k] = new.get(k, 0.0) + (1 - sm) * w / so
        for k, w in their.items():
            new[k] = new.get(k, 0.0) + sm * w / st
        for k, w in new.items():
            g = ob.vertex_groups.get(k) or ob.vertex_groups.new(name=k)
            if w > 1e-4:
                g.add([int(i)], float(w), "REPLACE")
            elif k in own:
                g.remove([int(i)])
    return int(len(sel))


def main(render=True):
    import bpy
    body, rig = C.open_base()
    bd = C.body_data(body)
    clothing = G.load_clothing(rig)
    under_t, note_t = G.clothing_under(bd, clothing, "torso")
    under_w, _note_w = G.clothing_under(bd, clothing, "waist")
    under_cb = G.Under(under_t.layers + under_w.layers)     # the cummerbund rides over the trousers' waistband
    G.say("torso surface:", note_t)
    coll = C.part_collection(PART)
    M = {k: G.mat(f"Carrier.Mat.{k.title().replace('_', '')}", v) for k, v in COL.items()}
    nz_mid, ny = notch_z(bd)            # round 1's estimate: the deepest point of the front midline (the throat)
    # the suprasternal notch proper lies between the clavicles' sternal ends (ANSUR II: suprasternale height
    # 0.818 x stature = 1500 for this man; the throat point above it was round 1's error)
    nz = 0.5 * (C.bone_mm("clavicle.L")[2] + C.bone_mm("clavicle.R")[2])
    G.say(f"suprasternal notch z {nz:.0f} y {ny:.0f}")
    out = {"notch_mm": [round(float(nz), 1), round(float(ny), 1)], "throat_midline_mm": round(float(nz_mid), 1),
           "under": note_t}

    # ---------------------------------------------------------------- plate bags
    zt_f = nz - TOP_DROP                # bag top below the notch (the plate's top 60 below it, as drawn)
    zb_f = zt_f - BAG_H
    hem = zb_f - FLAP_H
    front = PlateBag(under_t, -1, zt_f, zb_f + 10.0, BAG_W / 2.0)   # the rigid plate; the soft flap follows below
    zt_r = nz_mid + REAR_RAISE          # the rear bag: 50 above the front's top, overlapping the cummerbund
    zb_r = zt_r - BAG_H
    rear = PlateBag(under_t, +1, zt_r, zb_r, BAG_W / 2.0)
    out["front_bag"] = {"top": zt_f, "bottom": zb_f, "hem": hem, "tilt_dw_dz": round(front.b, 3),
                        "gap_to_shirt": front.gap_stats}
    out["front_bag"]["drop_below_notch"] = TOP_DROP
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
    def flap_follow(P, N, UV):
        """The flap is soft: where the belly stands proud of the plate's surface it lies on the shirt instead."""
        P = P.copy()
        for idx in np.ndindex(P.shape[:2]):
            q, _n = under_cb.hit(P[idx] + N[idx] * 80.0, -N[idx], 160.0)
            if q is not None:
                dpt = float(np.dot(q - P[idx], N[idx])) + CLR
                if dpt > 0:
                    P[idx] = P[idx] + N[idx] * dpt
        return P, N
    flap = G.slab("Carrier.Front.Flap", coll, front.surf(), lambda v: (-FLAP_W / 2, FLAP_W / 2), hem, zb_f + 15.0,
                  FLAP_T, M["cordura"], nu=24, nv=6, bevel_mm=2.5, post=flap_follow)
    bag_f = G.join(bag_f, [flap])               # the flap is sewn under the bag's bottom edge: one item
    tf_f, tf_r = taper(zt_f), taper(zt_r)
    # bound edges: the bags' outlines and the flap's hem (black tape)
    binding("Carrier.Front.Binding", coll, front, bag_outline(zt_f, zb_f, lambda v: bag_halfw(v, zt_f)), tf_f,
            M["binding"])
    binding("Carrier.Rear.Binding", coll, rear, bag_outline(zt_r, zb_r, lambda v: bag_halfw(v, zt_r)), tf_r,
            M["binding"])
    lay_bag = G.Under([(G.objects_bvh([bag_f]), 0.0)])
    hem_pts = []
    for u in np.linspace(-FLAP_W / 2 + 4, FLAP_W / 2 - 4, 40):
        p0, n0 = front.point(u, hem + 1.5, 0.0)
        q, _ = lay_bag.hit(p0 + n0 * 120.0, -n0, 200.0)          # the flap's outer face (it follows the belly)
        hem_pts.append((q if q is not None else p0 + n0 * FLAP_T) - n0 * FLAP_T / 2.0)
    tube("Carrier.Front.Flap.Binding", coll, hem_pts, 4.5, M["binding"], sides=10)

    # ---------------------------------------------------------------- PALS on the front bag and the flap
    # rows from the bottom up at 50.8 pitch, 25 mm above the bag's bottom edge, up to the panel's lower edge;
    # 7 cells (266) across the bag, 6 (228) across the flap
    pals_rows_z = [zb_f + 25.0 + PALS_PITCH * k for k in range(8)]
    pals_rows_z = [z for z in pals_rows_z if z + PALS_W / 2 < zt_f - PANEL_DROP - PANEL[1] - 2.0]
    half = 3.5 * PALS_COL

    def bag_row(z, hw, n=24):
        return [front.point(u, z, tf_f(u, z))[0] for u in np.linspace(-hw - 2.0, hw + 2.0, n)]
    pals_f, res_f = pals("Carrier.Front.PALS", coll, bag_f, [bag_row(z, half) for z in pals_rows_z], 7,
                         M["webbing_pals"], seed=11, start=2.0)
    flap_z = hem + FLAP_H / 2.0 - 1.0
    flap_row = []
    for u in np.linspace(-3 * PALS_COL - 2, 3 * PALS_COL + 2, 20):
        p0, n0 = front.point(u, flap_z, 0.0)
        q, _ = lay_bag.hit(p0 + n0 * 120.0, -n0, 200.0)          # the flap's outer face (it may follow the belly)
        flap_row.append(q if q is not None else front.point(u, flap_z, FLAP_T)[0])
    pals_fl, _ = pals("Carrier.Front.Flap.PALS", coll, bag_f, [flap_row], 6, M["webbing_pals"], seed=12, start=2.0)
    out["pals_front"] = {"rows_z": [round(z) for z in pals_rows_z], "flap_row_z": round(flap_z), "cells": [7, 6],
                         "webbing": [PALS_W, PALS_T], "column_pitch": PALS_COL, "row_pitch": PALS_PITCH}

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

    cb_grid = {}
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        # angular extent at mid height: from 25 mm behind the front bag's edge to 25 mm behind the rear bag's
        zm = (zc0 + zc1) / 2
        th_all = np.radians(np.linspace(0.5, 179.5, 360))
        R = torso_ring(under_cb, zm, cy, sgn * th_all)
        x = np.sin(th_all) * R
        yv = cy - np.cos(th_all) * R
        fh = max(front_halfw(zm) - 25.0, 0.0)
        rh = max(rear_halfw(zc1 - 10) - 25.0, 0.0)
        i0 = int(np.argmax((x >= fh) & (yv < cy)))
        back = np.nonzero((x >= rh) & (yv > cy))[0]
        i1 = int(back[-1]) if len(back) else len(th_all) - 1
        thetas = sgn * np.linspace(th_all[i0], th_all[i1], nth)
        Pin, Pout = [], []
        # the band rises toward the back (CB_RISE), where the belt and the trousers' waist ride higher
        wb = np.clip(((1.0 - np.cos(np.abs(thetas))) / 2.0 - 0.35) / 0.55, 0.0, 1.0)
        wb = wb * wb * (3 - 2 * wb)
        for z in zrows:
            R0 = G.fill_nan(torso_ring(under_cb, z, cy, thetas)[None])[0]
            R1 = G.fill_nan(torso_ring(under_cb, z + CB_RISE, cy, thetas)[None])[0]
            Rz = R0 * (1 - wb) + R1 * wb
            d = np.column_stack([np.sin(thetas), -np.cos(thetas), np.zeros(nth)])
            c = np.column_stack([np.zeros(nth), np.full(nth, cy), z + CB_RISE * wb])
            pin = c + d * (Rz[:, None] + 1.0)
            pout = c + d * (Rz[:, None] + 1.0 + CB_T)
            # behind the front bag / flap and the rear bag: keep both faces behind the bag's inner face
            for arr in (pin, pout):
                for k in range(nth):
                    px, py, pz = arr[k]
                    if py < cy and abs(px) < front_halfw(pz) and pz >= zb_f:   # the flap laps over the ends
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
        cb_grid[side] = (Pout, zrows)
    out["cummerbund"] = {"z": [round(zc0), round(zc1)], "thick": CB_T}

    # ---------------------------------------------------------------- admin panel (moulded to the bag face)
    pw, ph, pt = PANEL
    pzc = zt_f - PANEL_DROP - ph / 2.0
    pxc = -5.0
    ca, sa = math.cos(math.radians(-PANEL_CANT)), math.sin(math.radians(-PANEL_CANT))
    sf_out = front.surf(BAG_T + 0.3)

    def panel_surf(u, v):
        return sf_out(pxc + u * ca - v * sa, pzc + u * sa + v * ca)
    G.slab("Carrier.Front.Panel", coll, panel_surf, lambda v: (-pw / 2, pw / 2), -ph / 2, ph / 2, pt, M["panel"],
           nu=16, nv=8, bevel_mm=3.0, segments=2)
    out["panel"] = {"centre_xz": [pxc, round(pzc)], "size": PANEL, "cant_deg": PANEL_CANT}

    # ---------------------------------------------------------------- magazine pouches
    # each: the body, the flap (over the top and 44 down the front) and the pull tab down its centre; standing
    # on the PALS
    pz0 = zb_f + POUCH_LIFT
    pcz = pz0 + POUCH[2] / 2.0
    lift = BAG_T + PALS_T + 3.5 + 0.5          # over the webbing and its sag
    for i, x in enumerate(POUCH_X):
        p, n = front.point(x, pcz, lift)
        up = G.unit(np.array([0.0, 0.0, 1.0]) - n * n[2])
        xa = G.unit(np.cross(up, n))
        R3 = np.column_stack([xa, n, up])

        def Mat(c):
            Mx = np.eye(4)
            Mx[:3, :3] = R3
            Mx[:3, 3] = c
            return Mx
        bw, bd, bh = POUCH
        body_m = Mat(p + n * bd / 2.0)
        top = Mat(p + n * (bd / 2.0 + 1.0) + up * (bh / 2.0 + 5.0))                      # flap over the top
        front_fl = Mat(p + n * (bd + 2.5) + up * (bh / 2.0 - 16.0))                       # flap down the front
        G.boxes(f"Carrier.Pouch.{i + 1}", coll, [(POUCH, body_m), ((bw + 3.0, bd + 6.0, 12.0), top),
                                                 ((bw + 3.0, 5.0, 44.0), front_fl)], M["pouch"], bevel_mm=4.0)
        ob = bpy.data.objects[f"Carrier.Pouch.{i + 1}"]
        # pull tab: webbing from the flap top down its front to 22 below the flap edge
        tab = [p + n * (bd + 6.0) + up * (bh / 2.0 + 6.0), p + n * (bd + 5.6) + up * (bh / 2.0 - 10.0),
               p + n * (bd + 5.3) + up * (bh / 2.0 - 40.0), p + n * (bd + 3.0) + up * (bh / 2.0 - 60.0)]
        tb = G.strip(f"Carrier.Pouch.{i + 1}.Tab", coll, np.array(tab), [n] * 4, 20.0, 2.4, M["webbing"], bevel_mm=0.6)
        G.join(ob, [tb])
    out["mag_pouches"] = {"x": POUCH_X, "z": [round(pz0), round(pz0 + POUCH[2] + 11)], "body": POUCH,
                          "flap": "over the top, 44 down the front, 20 mm pull tab to 22 below its edge"}

    # ---------------------------------------------------------------- shoulder straps
    panel_ob = bpy.data.objects["Carrier.Front.Panel"]
    lay_front = G.Under([(G.objects_bvh([bag_f, panel_ob, pals_f]), 0.6)] + under_t.layers)
    strap_out = {}
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        x = sgn * STRAP_X
        c = np.array([x, 0.0, nz_mid - 60.0])
        phis = np.radians(np.linspace(-115, 115, 116))
        pts, nrm, slope = strap_profile(under_t, x, sgn, c, phis, PAD_W)
        ztop_r = zt_r - max(0.0, abs(x) - (BAG_W / 2 - CORNER_CLIP))
        # the pad: from 45 mm above the front bag's top (room for the adjuster) over to 15 above the rear bag's
        keep = ((pts[:, 1] < c[1]) & (pts[:, 2] > zt_f + 45.0)) | ((pts[:, 1] >= c[1]) & (pts[:, 2] > ztop_r + 15.0))
        idx = np.nonzero(keep)[0]
        idx = np.arange(idx.min(), idx.max() + 1)
        arc, an = pts[idx], nrm[idx]
        pad = split_across(G.strip(f"Carrier.Strap.{side}.Pad", coll, arc, an, PAD_W, PAD_T, M["pad"], bevel_mm=2.5))
        # the 38 mm webbing sewn down the pad's centre
        web = G.strip(f"Carrier.Strap.{side}.Web", coll, arc + an * PAD_T, an, ROOT_W, 1.5, M["webbing"], bevel_mm=0.5)
        # front: webbing from the pad's end down the upper chest to the bag's top edge at ROOT_X and down the
        # bag face (the root, sewn into the bag) to 95 below the bag's top; laid on the outermost surface
        x_end = sgn * ROOT_X
        p_end = arc[0] + an[0] * (PAD_T * 0.5)
        zs = np.linspace(p_end[2] - 6.0, zt_f - 95.0, 34)
        path, pn = [p_end], [an[0]]
        for z in zs:
            t = (p_end[2] - z) / max(p_end[2] - zs[-1], 1.0)
            xx = x + (x_end - x) * min(t * 1.6, 1.0)
            best = None
            for dx in (-ROOT_W / 2, 0.0, ROOT_W / 2):
                q, qn = lay_front.hit(np.array([xx + dx, -600.0, z]), np.array([0.0, 1.0, 0.0]), 900.0)
                if q is not None and (best is None or q[1] < best[0][1]):
                    best = (q, qn)
            if best is None:
                continue
            q = best[0].copy()
            q[0] = xx
            path.append(q + best[1] * 0.5)
            pn.append(best[1])
        path = np.array(path)
        for _ in range(3):                       # the strap bridges the step at the bag's top edge
            path[1:-1] = 0.25 * path[:-2] + 0.5 * path[1:-1] + 0.25 * path[2:]
        pn = [G.unit(v) for v in np.array(pn)]
        root = G.strip(f"Carrier.Strap.{side}.Root", coll, path, pn, ROOT_W, ROOT_T, M["webbing"], bevel_mm=0.5)
        # ladder-lock 30 mm down the run from the pad's end
        seg = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
        kl = max(int(np.searchsorted(seg, 30.0)), 1)
        tl = G.unit(path[min(kl + 1, len(path) - 1)] - path[kl - 1])
        nl = G.unit(pn[kl] - tl * np.dot(pn[kl], tl))
        ladder_lock(f"Carrier.Strap.{side}.LadderLock", coll, path[kl] + nl * ROOT_T, np.cross(tl, nl), nl,
                    M["hardware"])
        # the loose tail: out of the lock, down over the root for 110 mm, through two keepers
        kt = min(int(np.searchsorted(seg, seg[kl] + 110.0)), len(path) - 1)
        tail_p = path[kl:kt + 1] + np.array(pn[kl:kt + 1]) * (ROOT_T + 0.4)
        tail_p[0] = tail_p[0] + nl * (LOCK[3] - 1.0)
        tail = G.strip(f"Carrier.Strap.{side}.Tail", coll, tail_p, pn[kl:kt + 1], ROOT_W - 2.0, 1.5, M["webbing"],
                       bevel_mm=0.5)
        keepers = []
        for kk, at in enumerate((seg[kl] + 62.0, seg[kl] + 98.0)):
            j = min(max(int(np.searchsorted(seg, at)), 1), len(path) - 2)
            tj = G.unit(path[j + 1] - path[j - 1])
            nj = G.unit(pn[j] - tj * np.dot(pn[j], tj))
            Mk = G.frame(path[j] + nj * (ROOT_T + 1.5 + 1.2), np.cross(tj, nj), nj)
            keepers.append(G.rbox(f"Carrier.Strap.{side}.Keeper.{kk + 1}", coll, (ROOT_W + 6.0, 16.0, 2.4), Mk,
                                  M["webbing"], bevel_mm=0.8))
        G.join(root, [tail] + keepers)
        # rear root down the rear bag face
        rr = [arc[-1]]
        for z in np.linspace(ztop_r - 6.0, zt_r - 70.0, 6):
            rr.append(rear.point(x, z, tf_r(x, z) + 0.6)[0])
        rr = np.array(rr)
        rrn = [an[-1]] + [rear.point(p[0], min(p[2], ztop_r), 0.0)[1] for p in rr[1:]]
        G.strip(f"Carrier.Strap.{side}.RearRoot", coll, rr, rrn, ROOT_W, ROOT_T, M["webbing"], bevel_mm=0.5)
        G.join(pad, [web])
        strap_out[side] = {"pad_top_z": round(float((arc + an * PAD_T)[:, 2].max())),
                           "slope_over_top": round(float(slope[len(slope) // 2]), 3),
                           "lock_centre": [round(float(v)) for v in path[kl]]}
    out["straps"] = {"x": STRAP_X, "pad": [PAD_W, PAD_T], "root": [ROOT_W, ROOT_T], "root_x": ROOT_X,
                     "lock": LOCK, **strap_out}

    # ---------------------------------------------------------------- PALS on the cummerbund (3 rows a side)
    for side, (Pout_s, zr) in cb_grid.items():
        rows_pts = []
        for zq in (zc0 + 25.0, zc0 + 75.0, zc0 + 125.0):
            j = float(np.interp(zq, zr, np.arange(len(zr))))
            j0 = int(min(math.floor(j), len(zr) - 2))
            f = j - j0
            row = (1 - f) * Pout_s[j0] + f * Pout_s[j0 + 1]
            rows_pts.append(row[::3])
        pals(f"Carrier.Cummerbund.{side}.PALS", coll, bpy.data.objects[f"Carrier.Cummerbund.{side}"], rows_pts, 6,
             M["webbing_cb"], seed=21 if side == "L" else 22, start=22.0)

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

    # radio pouch behind the left shoulder, radio top with knobs, the bungee over it, and the antenna
    rz = nz_mid + 15.0 - BAG_H + 125.0      # the radio stays at round 1's height (the antenna as drawn)
    Mr, pr, nr, xr = on_side(RADIO_THETA, rz, RADIO_POUCH)
    pouch = G.rbox("Carrier.Radio.Pouch", coll, RADIO_POUCH, Mr, M["radio_pouch"], bevel_mm=8.0)
    top = Mr[:3, 3] + np.array([0.0, 0.0, RADIO_POUCH[2] / 2.0])
    Mtop = Mr.copy()
    Mtop[:3, 3] = top + np.array([0.0, 0.0, 9.0])
    G.rbox("Carrier.Radio.Body", coll, (66.0, 40.0, 18.0), Mtop, M["radio"], bevel_mm=4.0)
    fwd = 1 if xr[1] < 0 else -1
    base = top + np.array([0.0, 0.0, 18.0]) + xr * 18.0 * fwd
    for kk, (du, dd) in enumerate(((-16.0, -6.0), (2.0, 8.0))):       # volume and channel knobs
        G.cyl(f"Carrier.Radio.Knob.{kk + 1}", coll, top + np.array([0.0, 0.0, 18.0]) + xr * du * fwd + Mr[:3, 1] * dd,
              np.array([0.0, 0.0, 1.0]), 8.0, 12.0, M["radio"], n=16)
    bung = [Mr[:3, 3] + Mr[:3, 1] * (RADIO_POUCH[1] / 2.0 + 1.5) + xr * u + np.array([0.0, 0.0, RADIO_POUCH[2] / 2.0 + h])
            for u, h in ((-34, -30), (-20, 4), (0, 12), (20, 4), (34, -30))]
    tube("Carrier.Radio.Bungee", coll, bung, 2.0, M["binding"], sides=8)
    ax = G.unit(np.array([0.0, math.sin(math.radians(5.0)), math.cos(math.radians(5.0))]))
    G.cyl("Carrier.Radio.Antenna.Steel", coll, base, ax, 13.0, 60.0, M["steel"])
    G.cyl("Carrier.Radio.Antenna.Brass", coll, base + ax * 60.0, ax, 15.0, 38.0, M["brass"])
    G.cyl("Carrier.Radio.Antenna.Groove", coll, base + ax * 98.0, ax, 14.2, 2.0, M["brass_dark"])
    G.cyl("Carrier.Radio.Antenna.Brass2", coll, base + ax * 100.0, ax, 15.0, 15.0, M["brass"])
    G.cyl("Carrier.Radio.Antenna.Cap", coll, base + ax * 115.0, ax, 16.0, 22.0, M["cap"], dome=16.0)
    ant_top = base + ax * 153.0
    G.join(pouch, [bpy.data.objects[n] for n in (
        "Carrier.Radio.Body", "Carrier.Radio.Knob.1", "Carrier.Radio.Knob.2", "Carrier.Radio.Bungee",
        "Carrier.Radio.Antenna.Steel", "Carrier.Radio.Antenna.Brass", "Carrier.Radio.Antenna.Groove",
        "Carrier.Radio.Antenna.Brass2", "Carrier.Radio.Antenna.Cap")])
    out["radio"] = {"pouch_centre": [round(float(v)) for v in Mr[:3, 3]], "antenna_base": [round(float(v)) for v in base],
                    "antenna_top": [round(float(v)) for v in ant_top], "theta_deg": RADIO_THETA}
    G.say("radio", out["radio"])

    # double pistol-magazine carrier on the right flank, on the cummerbund's rows (round 1 hung it below
    # them, into the belt)
    Mp, pp, np_, xp = on_side(290.0, zc0 + 58.0, PISTOL_POUCH)
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
    # the shoulder straps lie on the shirt and gaiter over the trapezius: they take their weights from the
    # shirt (so they move with the surface they lie on; from the skin 15 mm below, the posed shoulder came
    # up through them) and keep shoulder01, losing only the arm proper
    collapse_strap = {k: v for k, v in collapse.items() if not k.startswith("shoulder01")}
    shell = bpy.data.objects.get("Shirt.Shell")
    for ob in list(coll.all_objects):
        if ob.name.startswith("Carrier.Strap.") and shell is not None:
            G.soft_bind(ob, shell, rig, collapse=collapse_strap)
            ob["sgt_bind"] = "weights from Shirt.Shell"
        else:
            G.soft_bind(ob, body, rig, collapse=collapse)
    # round 4: the flap lies on the trousers' waistband, so its weights pass from the bag's (the spine) at the bag's
    # bottom edge to the waistband's (the pelvis) toward its hem; skinned from the belly alone, the posed waistband
    # came 12.8 mm up through the flap and its hem binding (rounds 2-3 clash, posed only)
    tr = bpy.data.objects.get("Trousers.Shell")
    if tr is not None:
        out["flap_weights"] = {n: flap_to_waist(bpy.data.objects[n], tr, zb_f, hem)
                               for n in ("Carrier.Front.Bag", "Carrier.Front.Flap.Binding", "Carrier.Front.Flap.PALS")
                               if n in bpy.data.objects}
        G.say("flap weights from the trousers' waistband:", out["flap_weights"])
    out["objects"] = sorted(o.name for o in coll.all_objects)
    out["materials"] = C.library_pass(coll, PART, MATERIALS, side_dust={"L": 1.0, "R": 0.9}, say_tag=TAG)
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
