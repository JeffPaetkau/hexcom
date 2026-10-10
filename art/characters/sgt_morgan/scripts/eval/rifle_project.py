"""Project the real rifle geometry (spec 15, frame R) into the reference image, and back.

Reproduces the tables of spec/15_carbine.md §2.2:
  * forward: rifle-frame points (mm) -> full-image pixels of ref/reference_full.png,
    compared with the analysts' drawn landmarks;
  * inverse: drawn pixels -> the point where their camera ray meets a named rifle-frame
    plane X = const (used to place the tan paint patches on real surfaces).

Camera: analysis_consolidated.md §8 (W (0, -4500, 600) mm, rotation X 93.9 deg, 46 mm lens
on a 36 mm sensor, 1672 x 941). Rifle transform: spec/08_rig_pose.md §4.8 (before the
re-solve with spec 15's pins; expect shifts of <= 3 px after it).

Run with the system Python:  python3 -I scripts/eval/rifle_project.py
Why a script and not Blender: it needs no scene and runs in milliseconds, so the table can
be re-made whenever spec 08's transform changes.
"""
import numpy as np

# Reference camera (consolidated §8).
C = np.array([0.0, -4500.0, 600.0])
_a = np.radians(93.9)
RIGHT = np.array([1.0, 0.0, 0.0])
UP = np.array([0.0, np.cos(_a), np.sin(_a)])
FWD = np.array([0.0, np.sin(_a), -np.cos(_a)])
F = 46.0 / 36.0 * 1672.0
CX, CY = 836.0, 470.5

# Rifle frame R in world W (spec 08 §4.8).
O = np.array([-67.0, -346.0, 1014.0])
RX = np.array([-0.271, -0.883, 0.384])
RY = np.array([0.441, -0.468, -0.766])
RZ = np.array([0.856, -0.038, 0.516])


def to_world(p):
    x, y, z = p
    return O + x * RX + y * RY + z * RZ


def to_pixel(w):
    d = w - C
    xc, yc, zc = d @ RIGHT, d @ UP, d @ FWD
    return CX + F * xc / zc, CY - F * yc / zc


def ray_to_plane_x(u, v, xr):
    """Where the camera ray through pixel (u, v) meets the rifle-frame plane X = xr."""
    d = FWD + ((u - CX) / F) * RIGHT - ((v - CY) / F) * UP
    d /= np.linalg.norm(d)
    t = (xr - (C - O) @ RX) / (d @ RX)
    q = C + t * d - O
    return q @ RX, q @ RY, q @ RZ


# name, rifle-frame point (mm), drawn pixel or None
FORWARD = [
    ("butt pad centre", (0, -415, -46), (695, 268)),
    ("butt heel", (0, -428.6, 18), (706, 243)),
    ("butt toe", (0, -401, -112), (683, 296)),
    ("castle nut top", (0, -215, 20), (748, 300)),
    ("charging handle rear top", (0, -205, 25), (752, 312)),
    ("ejection port centre", (15.5, -58, 1.5), (790, 375)),
    ("port rear edge", (15.5, -96, 1.5), (778, 358)),
    ("port front edge", (15.5, -20, 1.5), (802, 392)),
    ("mag release", (16, -74, -38), (764, 384)),
    ("magwell front lip", (0, -12, -76), (790, 412)),
    ("magwell rear lip", (0, -86, -82), (760, 402)),
    ("mag floorplate centre", (0, -32, -197), (748, 455)),
    ("GripFrame (spec 15)", (0, -169.0, -94.8), (727, 352)),
    ("receiver face", (0, 0, 0), (793, 402)),
    ("light tail", (32, 10, 16), (813, 362)),
    ("light bezel", (32, 114, 16), (832, 394)),
    ("HandguardFrame", (0, 170, 0), (840, 467)),
    ("hole #1", (13.5, 105, -13.5), (822, 447)),
    ("hole #7", (13.5, 261, -13.5), (853, 510)),
    ("rail top Y255", (0, 255, 30.2), (872, 438)),
    ("handguard front MCMR-13", (0, 340.9, 0), (873, 512)),
    ("barrel shoulder / A2 rear", (0, 382.7, 0), (885, 548)),
    ("A2 front (muzzle)", (0, 427.2, 0), (903, 570)),
    ("T-2 top rear", (0, -174, 87), None),
    ("T-2 top front", (0, -106, 87), None),
]

# name, drawn pixel, plane X (mm)
INVERSE = [
    ("tan stripe upper rear", (752, 305), 15.5),
    ("tan stripe upper front", (775, 345), 15.5),
    ("lower tan mark", (774, 390), 16.0),
    ("magwell front patch", (792, 417), 14.5),
    ("stock frame centre", (741, 330), 22.0),
    ("stock stripe", (718, 281), 22.0),
    ("handguard patch 1", (809, 426), 19.05),
    ("handguard patch 2", (799, 408), 19.05),
    ("screw a", (851, 478), 19.05),
    ("screw b", (855, 486), 19.05),
    ("screw c", (860, 497), 19.05),
    ("carrier glint", (793, 384), 12.7),
]

if __name__ == "__main__":
    print("%-28s %-22s %-14s %-12s %s" % ("landmark", "R (mm)", "real px", "drawn px", "err px"))
    for name, p, drawn in FORWARD:
        u, v = to_pixel(to_world(np.array(p, float)))
        if drawn:
            e = ((u - drawn[0]) ** 2 + (v - drawn[1]) ** 2) ** 0.5
            print("%-28s %-22s (%5.0f,%4.0f)   (%4d,%4d)  %5.1f" % (name, p, u, v, drawn[0], drawn[1], e))
        else:
            print("%-28s %-22s (%5.0f,%4.0f)" % (name, p, u, v))
    print()
    for name, (u, v), xr in INVERSE:
        x, y, z = ray_to_plane_x(u, v, xr)
        print("%-28s px(%3d,%3d) on X=%6.2f -> Y %7.1f  Z %6.1f" % (name, u, v, xr, y, z))
