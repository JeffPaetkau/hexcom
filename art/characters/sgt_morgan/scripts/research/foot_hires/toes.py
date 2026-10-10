"""The region's anatomy for the trial: toe segment frames from the joints, the target dimensions, and small
field helpers. Frame F millimetres throughout (left foot: +X lateral, toes toward -Y).

A segment frame has its origin at the proximal joint, `a` along the bone toward the next joint (or the
tip), `n` dorsal (the world's up made perpendicular to `a`, then rolled) and `b = n x a`, lateral. Points
are read as (t, u, h): along, across (lateral +) and up.
"""
import math

import numpy as np

# The trial's targets (mm). Spec 01 §3.3 for the nails and pulps, Jeff's X3 for the hallux breadth and the
# 1-2 gap (an indication, 2026-10-10); a key can be overridden from run.py's --params.
PARAMS = {
    "level": 5,           # Catmull-Clark level of the dense copy: 0.16-0.19 mm on the toes
    # method (a)'s large forms (macro.py), mm
    "pulp1": 2.4, "pulp2": 1.4,          # the pulps' fullness under and around the tips
    "tip1": 2.0, "tip2": 1.0,            # the pulps' noses carried forward under the free edges
    "droop1": 2.2, "droop2": 1.0,        # the tips' dorsum turned down toward the nose
    "square1": 0.07, "square2": 0.06,    # the distal sections' corners pushed out (share of their radius)
    "spade1": 0.07,                      # the hallux's end widened (share of its half-breadth)
    "web_sdf": 1,                        # the 1-2 web by a projected closing (method_fields.web_by_closing)
    "fair_dorsum": 250,                   # Taubin passes over the distal segments' dorsum before the nails
    "ip_shift": 3.0,                     # the hallux IP's creases this far distal of MakeHuman's joint cube
    "mtp_prom": 2.6, "mt_head": 0.8,     # the first MTP prominence (inner border) and the head's knuckle
    "ehl": 1.0, "edl": 0.6,              # the long extensor tendons onto the hallux and toe 2
    "web_fair": 0, "web_y": -229.0,      # Taubin passes over the 1-2 cleft's floor, behind y_F web_y
    "web_r": 2.4,                        # method (b): the closing's radius over the 1-2 cleft's floor
    "voxel": 0.2,                        # method (b): the field's voxel (mm)
    "crease_scale": 1.0,
    # nails: visible width and length (proximal fold to free-edge tip), free edge beyond the bed, plate
    # thickness at the root and at the free edge, transverse radius, the plate hidden under each lateral
    # fold and under the proximal fold, the pulp left beyond the free edge in plan
    "nail1": {"width": 18.5, "length": 17.5, "free_edge": 1.3, "thick_root": 0.55, "thick_edge": 0.75,
              "radius": 12.0, "hidden_side": 1.1, "root": 4.5, "tip_margin": 3.0, "roll_deg": -5.0,
              "fold_prox": 0.22, "fold_lat": 0.5, "prox_width": 2.6, "lat_width": 1.2, "corner": 2.8,
              "fold_back_prox": 3.0},
    "nail2": {"width": 10.5, "length": 10.0, "free_edge": 0.9, "thick_root": 0.4, "thick_edge": 0.55,
              "radius": 6.5, "hidden_side": 0.7, "root": 2.8, "tip_margin": 1.8, "roll_deg": 0.0,
              "fold_prox": 0.16, "fold_lat": 0.32, "prox_width": 1.6, "lat_width": 0.7, "corner": 1.8,
              "fold_back_prox": 2.0},
}


class Seg:
    """A toe segment's frame in F."""

    def __init__(self, origin, end, roll_deg=0.0, up=(0.0, 0.0, 1.0)):
        self.o = np.asarray(origin, float)
        d = np.asarray(end, float) - self.o
        self.length = float(np.linalg.norm(d))
        a = d / self.length
        up = np.asarray(up, float)
        n = up - (up @ a) * a
        n /= np.linalg.norm(n)
        if roll_deg:
            n = rotate(n, a, roll_deg)
        self.a, self.n = a, n
        self.b = np.cross(n, a)   # lateral for the left foot (checked by the caller's sign test)
        if self.b[0] < 0.0:
            raise ValueError("segment frame: b is not lateral (+x); the frame assumes the left foot")

    def local(self, q):
        d = np.asarray(q, float) - self.o
        return d @ self.a, d @ self.b, d @ self.n

    def point(self, t, u, h):
        return self.o + np.multiply.outer(t, self.a) + np.multiply.outer(u, self.b) + np.multiply.outer(h, self.n)

    def vec(self, da, db, dn):
        return np.multiply.outer(da, self.a) + np.multiply.outer(db, self.b) + np.multiply.outer(dn, self.n)


def rotate(v, axis, deg):
    """Rodrigues: v turned about a unit axis by deg (right hand)."""
    k = np.asarray(axis, float) / np.linalg.norm(axis)
    th = math.radians(deg)
    v = np.asarray(v, float)
    return v * math.cos(th) + np.cross(k, v) * math.sin(th) + k * (k @ v) * (1.0 - math.cos(th))


def segments(J):
    """The region's segment frames from the joints (common.joints): hallux proximal and distal, toe 2's
    three, toe 3's distal (for the crowding check)."""
    return {
        "h1": Seg(J["toe-1-1"], J["toe-1-2"]), "h2": Seg(J["toe-1-2"], J["toe-1-3"]),
        "t2p": Seg(J["toe-2-1"], J["toe-2-2"]), "t2m": Seg(J["toe-2-2"], J["toe-2-3"]),
        "t2d": Seg(J["toe-2-3"], J["toe-2-4"]), "t3d": Seg(J["toe-3-3"], J["toe-3-4"]),
    }


def merged(params):
    """PARAMS with overrides: a key's dict is merged one level deep."""
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in PARAMS.items()}
    for k, v in (params or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


# --------------------------------------------------------------------------- 1-D profiles

def smoothstep(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def window(x, a0, a1, b1, b0):
    """0 outside [a0, b0], 1 inside [a1, b1], smooth between."""
    return smoothstep(x, a0, a1) * (1.0 - smoothstep(x, b1, b0))


def gauss(x, sigma):
    return np.exp(-0.5 * (np.asarray(x, float) / sigma) ** 2)


def roll(x):
    """A quarter circle from (0, 0) to (1, 1): vertical at 0, flat at 1 (a fold's lip rising from the plate)."""
    x = np.clip(np.asarray(x, float), 0.0, 1.0)
    return np.sqrt(np.maximum(1.0 - (1.0 - x) ** 2, 0.0))
