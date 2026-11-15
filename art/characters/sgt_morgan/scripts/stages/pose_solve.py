"""Round 0, stage 2a: solve the hero pose of Morgan.Rig against the reference (numpy + scipy, no Blender).

Forward kinematics of MPFB's `default` skeleton are rebuilt from the rest matrices that base.py writes
(cache/stages/base.json), exactly as Blender poses a bone: posed = posed_parent @ rest_parent^-1 @ rest
@ basis. 73 joint parameters (pelvis rotation and position, five spine, three neck and the head bone,
clavicles, shoulders, elbow hinges and forearm twists, wrists, hips, knee hinges, ankles) are fitted by
scipy's least_squares (trf, bounded) on

  * reprojection error, through take 1's matched hero camera (scripts/eval/camproj.py), of the joints
    and face points against the 2-D targets in TARGETS (MediaPipe on the reference and take 1's hand
    reading, ref_keypoints.json; the source of each is noted there);
  * the hands on the carbine: the carbine frame is solved first from two pins (butt pad and muzzle
    pixels, butt depth on the carrier, real length), then the wrist and the index and little knuckles
    of each hand are pulled to grip points in that frame (right hand on the pistol grip, left hand
    over the handguard, as the image shows);
  * the feet on the boots' footbeds (heel seat 36 mm, ball seat 24 mm above the floor: a real Zephyr
    class footbed, take 1's spec 02) at the image's headings (right 85 deg to his right, left 17 deg to
    his left of the camera axis, take 1's spec 08 D3);
  * anatomical priors with sigmas (each joint near rest, pelvis yaw -10, chest -5, head +20 world,
    knees 17 / 9 deg, knees facing 45 deg right / 12 deg left), joint limits as bounds and hinge
    ranges as penalties (no hyperextension), the centre of mass over the feet 55/45 right-heavy, and
    the arms kept outside the torso.

The image is one view, so depth comes from the priors and the hand/carbine geometry. Fingers are set
by curl tables (not fitted). Writes scripts/stages/hero_pose.json: bone -> rotation quaternion
(w, x, y, z) in the bone's local (pose basis) space, the root location, the carbine frame and grip
points, and the per-joint residuals.

  "$SGT_PYIMG" -I scripts/stages/pose_solve.py [--restarts N]
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))
from eval import camproj  # noqa: E402

BASE_JSON = os.path.join(PROJECT, "cache", "stages", "base.json")
KP_JSON = os.path.join(HERE, "ref_keypoints.json")
OUT_JSON = os.path.join(HERE, "hero_pose.json")
CAM = camproj.HERO
D = math.radians

# --------------------------------------------------------------------------- evidence

# 2-D targets (full-frame px) and sigmas. "mp" = MediaPipe heavy on the reference, "hand" = take 1's
# analysts (analysis_pose_proportions.md, analysis_consolidated.md). Joint centres, not outlines: the
# figure wears armour, a carrier and boots, so outline-based readings are moved inward where noted.
TARGETS = {
    # head: skin, read exactly
    "pupil_R": ("lm", (800.0, 77.0), 3.0, "hand: iris centre"),
    "pupil_L": ("lm", (832.0, 77.0), 3.0, "hand: iris centre"),
    "nose_tip": ("lm", (815.0, 90.0), 3.0, "hand: pronasale"),
    "chin": ("lm", (816.0, 131.0), 4.0, "hand: menton"),
    "ear_R": ("lm", (762.0, 98.0), 5.0, "hand: right ear box (753-770, 84-112) centre; drives the head yaw"),
    "skull_top": ("lm", (808.0, 24.0), 5.0, "hand: hair mass top y 20 less ~15 mm of hair"),
    # shoulders: MediaPipe reads the joint under the pauldrons (hand reading 675/935 is the pad edge);
    # height from the hand reading (GH centres y 200)
    "upperarm01.R": ("head", (714.0, 202.0), 8.0, "mp x, hand y"),
    "upperarm01.L": ("head", (898.0, 198.0), 8.0, "mp x, hand y"),
    # elbows: the hand reading is the outer pad/cap; the joint is ~30 mm inside it
    "lowerarm01.R": ("head", (641.0, 328.0), 8.0, "hand (632,328) moved 9 px in"),
    "lowerarm01.L": ("head", (946.0, 347.0), 10.0, "hand (958,352) cap moved in; mp (940,313) too high"),
    # wrists: glove cuffs (the carbine grip constrains them too)
    "wrist.R": ("head", (697.0, 345.0), 16.0, "mp = hand (cuff); the drawn grip sits ~110 mm forward of a real one"),
    "wrist.L": ("head", (878.0, 428.0), 14.0, "hand cuff box (865-885, 410-440)"),
    # hips: hidden; MediaPipe and take 1's spec 08 'real' hips (776,443)/(856,443) agree
    "upperleg01.R": ("head", (764.0, 448.0), 14.0, "mp (754,452) / spec 08 (776,443)"),
    "upperleg01.L": ("head", (857.0, 445.0), 14.0, "mp (859,446) / spec 08 (856,443)"),
    # knees: kneepad centres are below the joint; mp reads 25 px higher
    "lowerleg01.R": ("head", (724.0, 637.0), 10.0, "between hand pad centre (727,650) and mp (721,625)"),
    "lowerleg01.L": ("head", (891.0, 642.0), 10.0, "between hand (890,657) and mp (894,630)"),
    # ankles: in the boot the ankle axis is ~111 mm up (75 + footbed 36): 52 px above the soles
    "foot.R": ("head", (731.0, 843.0), 8.0, "x hand/mp, y sole 895 - 52"),
    "foot.L": ("head", (930.0, 853.0), 8.0, "x hand/mp, y sole 907 - 54"),
}

HEEL_SEAT, BALL_SEAT = 0.036, 0.024     # footbed heights (m), LOWA Zephyr class (take 1 spec 02 §3.1)
FOOT_HEADING = {"R": -85.0, "L": 17.0}  # toe direction, deg from the camera axis (-Y), + toward his left (+X)
KNEE_FACING = {"R": -45.0, "L": 12.0}
KNEE_FLEX = {"R": (17.0, 6.0), "L": (9.0, 5.0)}
ELBOW_FLEX = {"R": (97.0, 12.0), "L": (55.0, 12.0)}     # pose note §6 (R 95-100, L 55)
# Wrists (deg, relative to the rig's rest hand): flexion + toward the palm, deviation + toward the little
# finger (ulnar). Pose note §6: right extension 12 / ulnar 10, left flexion 10 / radial 10. Normal ranges
# (flexion 70 / extension 60, ulnar 30 / radial 20) are soft limits, so no wrist breaks to reach a grip.
WRIST = {"R": {"flex": (-12.0, 15.0), "dev": (10.0, 10.0)}, "L": {"flex": (10.0, 15.0), "dev": (-10.0, 10.0)}}
WRIST_LIMITS = {"flex": (-60.0, 70.0), "dev": (-20.0, 30.0)}
PELVIS = {"yaw": (-10.0, 6.0), "pitch": (2.0, 4.0), "roll": (0.0, 3.0)}
CHEST_YAW, HEAD_YAW = (-5.0, 5.0), (20.0, 10.0)
WEIGHT_RIGHT = 0.55

# The carbine (M4 pattern, 16 in barrel, 840 mm overall, stock collapsed one position). Its frame, the
# convention shared with the carbine part: origin on the bore axis directly above the trigger, +X along
# the bore to the muzzle, +Z up through the top rail, +Y to the gun's left. Points in mm in that frame.
CARBINE = {
    "length_mm": 840.0,
    "muzzle": (545.0, 0.0, 0.0),            # muzzle device end
    "butt_pad_centre": (-295.0, 0.0, -40.0),
    "receiver_face": (115.0, 0.0, 0.0),     # front of the upper receiver
    "pistol_grip": (-98.0, 0.0, -85.0),     # grip centreline at the middle finger
    "handguard": (285.0, 0.0, 0.0),         # left-hand station on the bore, 170 mm ahead of the receiver face
}
# The two pins, full-frame px (consolidated §7), and the butt pad's depth: on the carrier over the right
# pectoral (take 1 spec 08 §4.8 found Y -150 mm against its vest; this body is the same depth there).
PIN_BUTT, PIN_MUZZLE, BUTT_Y = (695.0, 268.0), (903.0, 570.0), -0.150
# In the main solve the carbine is free (6 parameters from that start): the butt pin is held at 4 px,
# the muzzle pin only at MUZZLE_SIGMA_PX, because the drawn carbine is shorter than a real one (77 cm
# projected; a real 840 mm gun on both pins points 25 deg at the camera and puts the left hand far
# forward of the drawn, in-plane left forearm); the butt pad rests on the carrier, CARRIER_MM in front
# of the right pectoral's skin along the chest's forward axis (shirt, pad, plate, bag, admin panel).
MUZZLE_SIGMA_PX, CARRIER_MM = 12.0, 50.0
# how tightly the hands hold their grip points (mm): wrist, knuckles. The hands must grip the carbine,
# so these outrank the drawn wrist and elbow pixels where the drawing (its grip ~110 mm forward of a
# real one) disagrees.
HAND_SIGMA_MM = {"wrist": 30.0, "knuckle": 6.0}
# The palms wrap their grips: the palm centre (55 % from the wrist to the knuckle line, 15 mm out to the
# palm side) lies on the grip's surface: (axis point, axis direction, radius) in the carbine frame, mm.
# The wrist itself is only loosely placed, so the hand may roll about its knuckle line on the grip.
PALM_CONTACT = {"R": ((-71.7, 0.0, -39.8), (-0.423, 0.0, -0.906), 22.0),   # pistol grip centreline
                "L": ((285.0, 0.0, 0.0), (1.0, 0.0, 0.0), 26.0)}           # handguard (bore) axis
# Hand placement on the carbine (gun frame, mm): knuckle-line midpoint K (index to little MCP heads),
# knuckle direction k (index -> little), hand axis a (wrist -> knuckles). The wrist, index MCP and
# little MCP targets follow from the rig's own hand dimensions.
GRIP_ANGLE = D(25.0)
_g = np.array([-math.sin(GRIP_ANGLE), 0.0, -math.cos(GRIP_ANGLE)])        # down the pistol grip
HANDS = {
    # right: knuckles on the grip's right side, index MCP level with the grip top, little 60 mm down;
    # the palm wraps the back strap, the wrist behind and right of the grip (dorsum to the camera)
    "R": {"K": (-63.0, -26.0, -86.0), "k": tuple(_g), "a": (0.86, 0.285, -0.40)},
    # left: overhand C-clamp; palm on the top/left facet, knuckles along the top-right edge, fingers over
    # the right side to the underside (their tips face the camera), index nearest the receiver,
    # wrist above the rail toward the body
    "L": {"K": (285.0, -26.0, 26.0), "k": (1.0, 0.0, 0.0), "a": (0.49, -0.65, -0.57)},
}
# Finger curls (deg, MCP / PIP / DIP), take 1's pose note §7 tables; thumbs approximate
CURLS = {
    "R": {"finger1": (25, 30, 25), "finger2": (-30, 0, 0), "finger3": (85, 95, 50), "finger4": (85, 95, 50),
          "finger5": (80, 90, 45)},
    "L": {"finger1": (10, 10, 15), "finger2": (60, 85, 45), "finger3": (62, 85, 45), "finger4": (65, 85, 45),
          "finger5": (70, 80, 40)},
}

# --------------------------------------------------------------------------- skeleton


class Skeleton:
    def __init__(self, base):
        B = base["bones"]
        self.names = list(B)
        self.parent = {n: B[n]["parent"] for n in self.names}
        self.rest = {}
        for n in self.names:
            m = np.array(B[n]["matrix"], float)
            m[:3, 3] /= 1000.0
            m[3] = (0.0, 0.0, 0.0, 1.0)
            self.rest[n] = m
        order, seen = [], set()

        def visit(n):
            if n in seen:
                return
            p = self.parent[n]
            if p:
                visit(p)
            seen.add(n)
            order.append(n)
        for n in self.names:
            visit(n)
        self.order = order
        self.rel = {n: (np.linalg.inv(self.rest[self.parent[n]]) @ self.rest[n]) if self.parent[n] else self.rest[n]
                    for n in self.names}
        self.tail_local = {n: np.linalg.inv(self.rest[n]) @ np.array([*np.array(B[n]["tail"]) / 1000.0, 1.0])
                           for n in self.names}
        self.lm = {}
        for k, v in base["landmarks"].items():
            b = v["bone"]
            self.lm[k] = (b, np.linalg.inv(self.rest[b]) @ np.array([*np.array(v["rest_mm"]) / 1000.0, 1.0]))

    def fk(self, basis, root_world=None):
        """Posed armature-space matrices. basis: {bone: 4x4}; root_world: the root's posed matrix."""
        P = {}
        for n in self.order:
            p = self.parent[n]
            if p is None:
                P[n] = root_world if root_world is not None else self.rest[n] @ basis.get(n, np.eye(4))
            else:
                b = basis.get(n)
                P[n] = P[p] @ self.rel[n] if b is None else P[p] @ self.rel[n] @ b
        return P


def rot4(R):
    m = np.eye(4)
    m[:3, :3] = R
    return m


def rv(v):
    return Rot.from_rotvec(v).as_matrix()


# --------------------------------------------------------------------------- the carbine

def carbine_frame():
    """World (rig) matrix of the carbine frame from the two pins (spec 08 §4.8's solve, 840 mm)."""
    o, d = CAM.ray([PIN_BUTT])
    t = (BUTT_Y - o[0, 1]) / d[0, 1]
    B = o[0] + d[0] * t
    butt_c = np.array(CARBINE["butt_pad_centre"]) / 1000.0
    muz_c = np.array(CARBINE["muzzle"]) / 1000.0
    # take 1's nominal axes (spec 08 §4.8) in this convention as the start: X = bore, Y = gun's left, Z = up
    X0 = np.array([0.441, -0.468, -0.766])
    Z0 = np.array([0.856, -0.038, 0.516])
    R0 = np.stack([X0, np.cross(Z0, X0), Z0], axis=1)
    U, _, Vt = np.linalg.svd(R0)
    R0 = U @ Vt
    cam = np.asarray(camproj.HERO_LOC)

    def frame(v):
        R = Rot.from_rotvec(v).as_matrix() @ R0
        O = B - R @ butt_c
        return R, O

    def res(v):
        R, O = frame(v)
        M = O + R @ muz_c
        px = CAM.project([M])[0]
        bore = R[:, 0]
        view = (O - cam) / np.linalg.norm(O - cam)
        right = -R[:, 1]
        return [(px[0] - PIN_MUZZLE[0]), (px[1] - PIN_MUZZLE[1]), 100.0 * float(right @ np.cross(bore, view))]
    sol = least_squares(res, np.zeros(3), xtol=1e-12, ftol=1e-12)
    R, O = frame(sol.x)
    if R[:, 1] @ (cam - O) > 0:  # the gun's right side (-Y) must face the camera
        raise RuntimeError("carbine solve flipped: its left side faces the camera")
    M = np.eye(4)
    M[:3, :3], M[:3, 3] = R, O
    return M, sol


def gun_point(M, p_mm):
    return M[:3, :3] @ (np.asarray(p_mm, float) / 1000.0) + M[:3, 3]


# --------------------------------------------------------------------------- the model


class Model:
    def __init__(self, base, kp):
        self.sk = sk = Skeleton(base)
        self.base = base
        R = {n: sk.rest[n][:3, :3] for n in sk.names}
        self.R = R
        H = {n: sk.rest[n][:3, 3] for n in sk.names}
        self.H = H
        # parameter blocks
        self.blocks = [("root", "root", 6)]
        for n in ("spine05", "spine04", "spine03", "spine02", "spine01", "neck01", "neck02", "neck03", "head",
                  "clavicle.L", "clavicle.R", "upperarm01.L", "upperarm01.R", "wrist.L", "wrist.R",
                  "upperleg01.L", "upperleg01.R", "foot.L", "foot.R"):
            self.blocks.append((n, "rv3", 3))
        for s in ("L", "R"):
            self.blocks += [(f"lowerarm01.{s}", "hinge", 2), (f"lowerarm02.{s}", "twist", 1),
                            (f"lowerleg01.{s}", "hinge", 2)]
        self.blocks.append(("carbine", "gun", 6))      # rotation and offset from the two-pin solution
        self.slices, i = {}, 0
        for n, kind, k in self.blocks:
            self.slices[n] = (slice(i, i + k), kind)
            i += k
        self.n = i
        # hinge axes in each bone's local frame: elbow from the rest bend, knee = world +X (flexion
        # swings the ankle backward, +Y)
        self.hinge = {}
        for s in ("L", "R"):
            u = H[f"lowerarm01.{s}"] - H[f"upperarm01.{s}"]
            f = H[f"wrist.{s}"] - H[f"lowerarm01.{s}"]
            nrm = np.cross(u, f)
            nrm /= np.linalg.norm(nrm)
            self.hinge[f"lowerarm01.{s}"] = R[f"lowerarm01.{s}"].T @ nrm
            self.hinge[f"lowerleg01.{s}"] = R[f"lowerleg01.{s}"].T @ np.array([1.0, 0.0, 0.0])
        self.wrist_rest = {s: self.wrist_angles_from(H, s) for s in "LR"}
        self.rest_elbow = {s: self.angle(H[f"upperarm01.{s}"], H[f"lowerarm01.{s}"], H[f"wrist.{s}"]) for s in "LR"}
        # anterior axis of each shank in its local frame (the local axis closest to world -Y at rest)
        self.knee_front = {}
        for s in "LR":
            Rl = R[f"lowerleg01.{s}"]
            cand = [Rl[:, 0], -Rl[:, 0], Rl[:, 2], -Rl[:, 2]]
            best = max(range(4), key=lambda j: cand[j] @ np.array([0, -1.0, 0]))
            self.knee_front[s] = (Rl.T @ cand[best])
        # the carbine (its start: the two-pin solution) and the hand targets in its frame
        self.gun0, self.gun_sol = carbine_frame()
        self._G = None
        self.hand_local = {}
        for s in "LR":
            h = HANDS[s]
            K = np.array(h["K"]) / 1000.0
            a = np.array(h["a"], float)
            a /= np.linalg.norm(a)
            k = np.array(h["k"], float)
            k -= a * (a @ k)
            k /= np.linalg.norm(k)
            # the rig's own hand: knuckle span and wrist-to-knuckle-line distance
            i2, i5, w = H[f"finger2-1.{s}"], H[f"finger5-1.{s}"], H[f"wrist.{s}"]
            span = np.linalg.norm(i5 - i2)
            reach = np.linalg.norm((i2 + i5) / 2 - w)
            self.hand_local[s] = {f"wrist.{s}": K - a * reach, f"finger2-1.{s}": K - k * span / 2,
                                  f"finger5-1.{s}": K + k * span / 2}
        self.kp = kp
        self.lm_rest_z = {k: v["rest_mm"][2] / 1000.0 for k, v in base["landmarks"].items()}
        self.root = sk.names[0] if sk.parent[sk.names[0]] is None else [n for n in sk.names if sk.parent[n] is None][0]

    @staticmethod
    def angle(a, b, c):
        u, v = b - a, c - b
        return math.degrees(math.acos(max(-1.0, min(1.0, u @ v / (np.linalg.norm(u) * np.linalg.norm(v))))))

    def basis(self, x):
        out, root_world = {}, None
        for n, (sl, kind) in self.slices.items():
            v = x[sl]
            if kind == "root":
                h = self.H[n]
                Rw = rv(v[:3])
                M = np.eye(4)
                M[:3, :3] = Rw
                M[:3, 3] = h - Rw @ h + v[3:6]
                root_world = M @ self.sk.rest[n]
            elif kind == "rv3":
                out[n] = rot4(rv(v))
            elif kind == "hinge":
                out[n] = rot4(rv(self.hinge[n] * v[0]) @ rv(np.array([0.0, v[1], 0.0])))
            elif kind == "twist":
                out[n] = rot4(rv(np.array([0.0, v[0], 0.0])))
        return out, root_world

    def gun(self, x):
        v = x[self.slices["carbine"][0]]
        M = np.eye(4)
        M[:3, :3] = rv(v[:3]) @ self.gun0[:3, :3]
        M[:3, 3] = self.gun0[:3, 3] + v[3:6]
        return M

    def hand_targets(self, G):
        return {s: {b: G[:3, :3] @ p + G[:3, 3] for b, p in self.hand_local[s].items()} for s in "LR"}

    def pose(self, x):
        b, rw = self.basis(x)
        return self.sk.fk(b, rw), b, rw

    def point(self, P, name):
        if name in self.sk.lm:
            bone, loc = self.sk.lm[name]
            return (P[bone] @ loc)[:3]
        return P[name][:3, 3]

    def heading(self, P, s):
        d = self.point(P, f"toe_{s}") - self.point(P, f"heel_{s}")
        return math.degrees(math.atan2(d[0], -d[1]))

    def yaw_of(self, P, bone):
        """World yaw (deg, + toward his left) and pitch (deg, + forward) of a bone's rest forward axis."""
        Rp = P[bone][:3, :3] @ self.R[bone].T
        f = Rp @ np.array([0, -1.0, 0])
        up = Rp @ np.array([0, 0, 1.0])
        return math.degrees(math.atan2(f[0], -f[1])), math.degrees(math.atan2(-up[1], up[2])), math.degrees(math.atan2(up[0], up[2]))

    @staticmethod
    def wrist_angles_from(J, s):
        """(flexion, deviation) of the hand against the forearm, deg, from joint positions J[bone]."""
        f = J[f"wrist.{s}"] - J[f"lowerarm01.{s}"]
        f /= np.linalg.norm(f)
        h = J[f"finger3-1.{s}"] - J[f"wrist.{s}"]
        h /= np.linalg.norm(h)
        k = J[f"finger5-1.{s}"] - J[f"finger2-1.{s}"]
        k -= f * (k @ f)
        k /= np.linalg.norm(k)
        n = np.cross(f, k) if s == "R" else -np.cross(f, k)      # palm side, perpendicular to the forearm
        return math.degrees(math.atan2(h @ n, h @ f)), math.degrees(math.atan2(h @ k, h @ f))

    def wrist_angles(self, P, s):
        J = {b: P[b][:3, 3] for b in (f"wrist.{s}", f"lowerarm01.{s}", f"finger3-1.{s}", f"finger5-1.{s}", f"finger2-1.{s}")}
        fl, dv = self.wrist_angles_from(J, s)
        return fl - self.wrist_rest[s][0], dv - self.wrist_rest[s][1]

    def knee_flex(self, P, s):
        h, k, a = (P[n][:3, 3] for n in (f"upperleg01.{s}", f"lowerleg01.{s}", f"foot.{s}"))
        ang = self.angle(h, k, a)
        front = P[f"lowerleg01.{s}"][:3, :3] @ self.knee_front[s]
        # knee forward of the hip-ankle line = flexion
        sign = 1.0 if (k - (h + a) / 2) @ front > 0 else -1.0
        return sign * ang

    def knee_facing(self, P, s):
        f = P[f"lowerleg01.{s}"][:3, :3] @ self.knee_front[s]
        return math.degrees(math.atan2(f[0], -f[1]))

    def com(self, P):
        """Rough centre of mass (Dempster-style segment shares) with the carbine at 3.4 kg on 80 kg."""
        pts = [("root", 0.142), ("spine03", 0.139), ("spine01", 0.216), ("head", 0.081)]
        for s in "LR":
            pts += [(f"upperarm02.{s}", 0.028), (f"lowerarm02.{s}", 0.022), (f"upperleg02.{s}", 0.100),
                    (f"lowerleg02.{s}", 0.0465), (f"foot.{s}", 0.0145)]
        m = sum(w for _, w in pts)
        c = sum(P[n][:3, 3] * w for n, w in pts) / m
        g = gun_point(self._G if self._G is not None else self.gun0, (100.0, 0.0, -30.0))
        return (c * 80.0 + g * 3.4) / 83.4

    def residuals(self, x, detail=False):
        P, _, _ = self.pose(x)
        r, info = [], {}

        def add(name, val, sigma):
            r.append(val / sigma)
            if detail:
                info[name] = val
        # 1. reprojection
        names = list(TARGETS)
        pts = np.array([self.point(P, n) for n in names])
        px = CAM.project(pts)
        for n, p in zip(names, px):
            _, tgt, sig, _ = TARGETS[n]
            add(f"px:{n}:x", p[0] - tgt[0], sig)
            add(f"px:{n}:y", p[1] - tgt[1], sig)
        # 2. the carbine on its pins and against the carrier, and the hands on the carbine
        G = self.gun(x)
        self._G = G
        bp, mp = CAM.project([gun_point(G, CARBINE["butt_pad_centre"]), gun_point(G, CARBINE["muzzle"])])
        add("gun:butt_px:x", bp[0] - PIN_BUTT[0], 4.0)
        add("gun:butt_px:y", bp[1] - PIN_BUTT[1], 4.0)
        add("gun:muzzle_px:x", mp[0] - PIN_MUZZLE[0], MUZZLE_SIGMA_PX)
        add("gun:muzzle_px:y", mp[1] - PIN_MUZZLE[1], MUZZLE_SIGMA_PX)
        view = G[:3, 3] - np.asarray(camproj.HERO_LOC)
        view /= np.linalg.norm(view)
        add("gun:roll", math.degrees(math.asin(max(-1.0, min(1.0, float(-G[:3, 1] @ np.cross(G[:3, 0], view)))))), 10.0)
        Rc = P["spine02"][:3, :3] @ self.R["spine02"].T
        fwd = Rc @ np.array([0.0, -1.0, 0.0])
        gap = (gun_point(G, CARBINE["butt_pad_centre"]) - self.point(P, "pec_R")) @ fwd
        add("gun:butt_on_carrier", (gap - CARRIER_MM / 1000.0) * 1000.0, 12.0)
        for s in "LR":
            W, i2, i5 = (P[b][:3, 3] for b in (f"wrist.{s}", f"finger2-1.{s}", f"finger5-1.{s}"))
            K = (i2 + i5) / 2
            n = np.cross(K - W, i5 - i2) * (1.0 if s == "R" else -1.0)
            n /= np.linalg.norm(n)
            pc = W + 0.55 * (K - W) + n * 0.015
            o, a, rad = PALM_CONTACT[s]
            o, a = gun_point(G, o), G[:3, :3] @ np.array(a)
            v = pc - o
            dist = np.linalg.norm(v - a * (v @ a))
            add(f"hand:palm_on_grip_{s}", (dist - rad / 1000.0) * 1000.0, 6.0)
            # and the palm faces the grip axis
            toward = -(v - a * (v @ a)) / max(dist, 1e-6)
            add(f"hand:palm_faces_grip_{s}", math.degrees(math.acos(max(-1.0, min(1.0, float(n @ toward))))), 25.0)
        for s, T in self.hand_targets(G).items():
            for bone, t in T.items():
                d = P[bone][:3, 3] - t
                for j in range(3):
                    add(f"hand:{bone}:{'xyz'[j]}", d[j] * 1000.0, HAND_SIGMA_MM["wrist" if bone.startswith("wrist") else "knuckle"])
        # 3. feet on the footbeds, at the headings
        for s in "LR":
            # each point keeps its rest height above the sole, raised onto the footbed
            for k, seat in (("heel", HEEL_SEAT), ("mt1", BALL_SEAT), ("mt5", BALL_SEAT)):
                n = f"{k}_{s}"
                add(f"foot:{n}_z", (self.point(P, n)[2] - seat - self.lm_rest_z[n]) * 1000, 3.0)
            add(f"foot:{s}:heading", self.heading(P, s) - FOOT_HEADING[s], 6.0)
        # 4. posture priors
        y, p, rl = self.yaw_of(P, self.root)
        add("prior:pelvis_yaw", y - PELVIS["yaw"][0], PELVIS["yaw"][1])
        add("prior:pelvis_pitch", p - PELVIS["pitch"][0], PELVIS["pitch"][1])
        add("prior:pelvis_roll", rl - PELVIS["roll"][0], PELVIS["roll"][1])
        y, p, rl = self.yaw_of(P, "spine01")
        add("prior:chest_yaw", y - CHEST_YAW[0], CHEST_YAW[1])
        add("prior:chest_pitch", p - 0.0, 6.0)
        add("prior:chest_roll", rl, 3.0)
        y, p, rl = self.yaw_of(P, "head")
        add("prior:head_yaw", y - HEAD_YAW[0], HEAD_YAW[1])
        add("prior:head_roll", rl, 4.0)
        for s in "LR":
            kf = self.knee_flex(P, s)
            add(f"prior:knee_flex_{s}", kf - KNEE_FLEX[s][0], KNEE_FLEX[s][1])
            add(f"limit:knee_hyper_{s}", min(0.0, kf - 3.0), 0.5)
            add(f"prior:knee_facing_{s}", self.knee_facing(P, s) - KNEE_FACING[s], 15.0)
            ef = self.angle(P[f"upperarm01.{s}"][:3, 3], P[f"lowerarm01.{s}"][:3, 3], P[f"wrist.{s}"][:3, 3])
            add(f"limit:elbow_{s}", min(0.0, ef - 10.0) + max(0.0, ef - 145.0), 0.5)
            add(f"prior:elbow_flex_{s}", ef - ELBOW_FLEX[s][0], ELBOW_FLEX[s][1])
            wf, wd = self.wrist_angles(P, s)
            add(f"prior:wrist_flex_{s}", wf - WRIST[s]["flex"][0], WRIST[s]["flex"][1])
            add(f"prior:wrist_dev_{s}", wd - WRIST[s]["dev"][0], WRIST[s]["dev"][1])
            for nm, v in (("flex", wf), ("dev", wd)):
                lo_, hi_ = WRIST_LIMITS[nm]
                add(f"limit:wrist_{nm}_{s}", min(0.0, v - lo_) + max(0.0, v - hi_), 1.0)
        # stance: the left foot 10-20 cm nearer the camera (consolidated §1)
        add("prior:stance_depth", (P["foot.L"][1, 3] - P["foot.R"][1, 3] + 0.15) * 1000, 60.0)
        # centre of mass over the support, 55 % toward the right ankle
        c = self.com(P)
        aL, aR = P["foot.L"][:3, 3], P["foot.R"][:3, 3]
        sup = aR * WEIGHT_RIGHT + aL * (1 - WEIGHT_RIGHT)
        add("prior:com_x", (c[0] - sup[0]) * 1000, 25.0)
        add("prior:com_y", (c[1] - (aL[1] + aR[1]) / 2 + 0.03) * 1000, 30.0)
        # arms outside the torso: elbows and wrists outside an ellipse about the chest
        Rc = P["spine02"][:3, :3] @ self.R["spine02"].T
        cc = P["spine02"][:3, 3]
        for s in "LR":
            for j in (f"lowerarm01.{s}", f"wrist.{s}"):
                q = Rc.T @ (P[j][:3, 3] - cc)
                e = math.hypot(q[0] / 0.20, q[1] / 0.15)
                add(f"limit:inside_{j}", min(0.0, e - 1.0) * 100.0, 5.0)
        # 5. joint priors (each near rest), in degrees
        sig = {"spine05": 4, "spine04": 4, "spine03": 4, "spine02": 4, "spine01": 4, "neck01": 6, "neck02": 6,
               "neck03": 6, "head": 15, "clavicle.L": 8, "clavicle.R": 8, "upperarm01.L": 70, "upperarm01.R": 70,
               "wrist.L": 25, "wrist.R": 25, "upperleg01.L": 30, "upperleg01.R": 30, "foot.L": 25, "foot.R": 25}
        for n, (sl, kind) in self.slices.items():
            v = np.degrees(x[sl])
            if kind == "rv3":
                for j in range(3):
                    add(f"joint:{n}:{j}", v[j], sig[n])
            elif kind == "hinge":
                add(f"joint:{n}:twist", v[1], 15.0)
            elif kind == "twist":
                add(f"joint:{n}:twist", v[0], 80.0)
            elif kind == "root":
                add("joint:root:offset_z", x[sl][5] * 1000, 200.0)
        out = np.array(r)
        return (out, info, P) if detail else out

    def bounds(self):
        lo, hi = np.full(self.n, -np.inf), np.full(self.n, np.inf)
        lim = {"spine05": 0.2, "spine04": 0.25, "spine03": 0.25, "spine02": 0.25, "spine01": 0.25, "neck01": 0.35,
               "neck02": 0.35, "neck03": 0.35, "head": 0.8, "clavicle.L": 0.4, "clavicle.R": 0.4,
               "upperarm01.L": 2.8, "upperarm01.R": 2.8, "wrist.L": 1.1, "wrist.R": 1.1, "upperleg01.L": 1.2,
               "upperleg01.R": 1.2, "foot.L": 0.8, "foot.R": 0.8}
        for n, (sl, kind) in self.slices.items():
            i = sl.start
            if kind == "root":
                lo[i:i + 3], hi[i:i + 3] = -0.5, 0.5
                lo[i + 3:i + 6], hi[i + 3:i + 6] = -0.4, 0.4
            elif kind == "rv3":
                lo[i:i + 3], hi[i:i + 3] = -lim[n], lim[n]
            elif kind == "hinge":
                if n.startswith("lowerarm"):
                    r0 = self.rest_elbow[n[-1]]
                    lo[i], hi[i] = D(5.0 - r0), D(150.0 - r0)
                else:
                    lo[i], hi[i] = D(-6.0), D(60.0)
                lo[i + 1], hi[i + 1] = D(-35.0), D(35.0)
            elif kind == "twist":
                lo[i], hi[i] = D(-110.0), D(110.0)
            elif kind == "gun":
                lo[i:i + 3], hi[i:i + 3] = -0.6, 0.6
                lo[i + 3:i + 6], hi[i + 3:i + 6] = -0.25, 0.25
        return lo, hi


def finger_basis(model, P):
    """Finger curls as local rotations about the axis that closes each phalanx toward the palm."""
    sk, H, R = model.sk, model.H, model.R
    out = {}
    for s in "LR":
        w, i2, i5, m3 = H[f"wrist.{s}"], H[f"finger2-1.{s}"], H[f"finger5-1.{s}"], H[f"finger3-1.{s}"]
        a = (m3 - w) / np.linalg.norm(m3 - w)
        k = (i5 - i2) / np.linalg.norm(i5 - i2)
        n = np.cross(a, k) if s == "R" else -np.cross(a, k)       # palm normal (rest)
        n /= np.linalg.norm(n)
        for f, (c1, c2, c3) in CURLS[s].items():
            for j, c in zip((1, 2, 3), (c1, c2, c3)):
                b = f"{f}-{j}.{s}"
                if b not in R:
                    continue
                y = (sk.tail_local[b][:3])
                y = R[b] @ (y / np.linalg.norm(y))
                ax = np.cross(y, n)                       # rotating y about y x n moves it toward n
                if np.linalg.norm(ax) < 1e-6:
                    continue
                ax /= np.linalg.norm(ax)
                if f == "finger1":                        # the thumb closes across the palm, toward the index
                    ax = np.cross(y, (n + 0.6 * -k * (1 if s == "R" else 1)))
                    ax /= np.linalg.norm(ax)
                out[b] = rot4(rv(R[b].T @ ax * D(c)))
    return out


def solve(restarts=3, seed=7):
    with open(BASE_JSON, encoding="utf-8") as f:
        base = json.load(f)
    with open(KP_JSON, encoding="utf-8") as f:
        kp = json.load(f)
    model = Model(base, kp)
    lo, hi = model.bounds()
    rng = np.random.default_rng(seed)
    best = None
    t0 = time.perf_counter()
    for k in range(restarts):
        x0 = np.zeros(model.n)
        # start the arms forward and in, toward the carbine, with random spread
        for s, sx in (("R", 1.0), ("L", -1.0)):
            sl = model.slices[f"upperarm01.{s}"][0]
            x0[sl] = rng.normal(0, 0.6, 3) if k else 0.0
            sl = model.slices[f"lowerarm01.{s}"][0]
            x0[sl.start] = D(40.0) if k else 0.0
        x0 = np.clip(x0, lo + 1e-6, hi - 1e-6)
        sol = least_squares(model.residuals, x0, bounds=(lo, hi), x_scale="jac", max_nfev=4000, xtol=1e-10,
                            ftol=1e-10, method="trf")
        print(f"start {k}: cost {sol.cost:.2f} ({sol.nfev} evaluations)", flush=True)
        if best is None or sol.cost < best.cost:
            best = sol
    secs = time.perf_counter() - t0
    x = best.x
    r, info, P = model.residuals(x, detail=True)
    basis, root_world = model.basis(x)
    fingers = finger_basis(model, P)
    basis.update(fingers)
    P = model.sk.fk(basis, root_world)
    root = model.root
    root_basis = np.linalg.inv(model.sk.rest[root]) @ root_world
    bones = {}
    for n in model.sk.names:
        m = root_basis if n == root else basis.get(n)
        if m is None:
            continue
        q = Rot.from_matrix(m[:3, :3]).as_quat()            # x, y, z, w
        if q[3] < 0:
            q = -q
        bones[n] = [round(float(q[3]), 8), round(float(q[0]), 8), round(float(q[1]), 8), round(float(q[2]), 8)]
    # per-joint residuals (px) and readbacks
    joints = {}
    for n, (src, tgt, sig, note) in TARGETS.items():
        p = CAM.project([model.point(P, n)])[0]
        joints[n] = {"target_px": list(tgt), "fit_px": [round(float(p[0]), 1), round(float(p[1]), 1)],
                     "residual_px": round(float(math.hypot(p[0] - tgt[0], p[1] - tgt[1])), 1), "sigma_px": sig,
                     "source": note}
    hands = {}
    for s in "LR":
        for bone, T in model.hand_targets(model.gun(x))[s].items():
            hands[bone] = round(float(np.linalg.norm(P[bone][:3, 3] - T)) * 1000, 1)
    readback = {
        "pelvis_yaw_pitch_roll_deg": [round(v, 1) for v in model.yaw_of(P, root)],
        "chest_yaw_pitch_roll_deg": [round(v, 1) for v in model.yaw_of(P, "spine01")],
        "head_yaw_pitch_roll_deg": [round(v, 1) for v in model.yaw_of(P, "head")],
        "knee_flex_deg": {s: round(model.knee_flex(P, s), 1) for s in "LR"},
        "knee_facing_deg": {s: round(model.knee_facing(P, s), 1) for s in "LR"},
        "elbow_flex_deg": {s: round(model.angle(P[f"upperarm01.{s}"][:3, 3], P[f"lowerarm01.{s}"][:3, 3],
                                                P[f"wrist.{s}"][:3, 3]), 1) for s in "LR"},
        "foot_heading_deg": {s: round(model.heading(P, s), 1) for s in "LR"},
        "wrist_flex_dev_deg": {s: [round(v, 1) for v in model.wrist_angles(P, s)] for s in "LR"},
        "foot_points_z_mm": {k: round(float(model.point(P, k)[2]) * 1000, 1) for k in
                             ("heel_L", "mt1_L", "mt5_L", "toe_L", "heel_R", "mt1_R", "mt5_R", "toe_R")},
        "ankles_mm": {s: [round(float(v) * 1000, 1) for v in P[f"foot.{s}"][:3, 3]] for s in "LR"},
        "pelvis_mm": [round(float(v) * 1000, 1) for v in P[root][:3, 3]],
        "com_mm": [round(float(v) * 1000, 1) for v in model.com(P)],
        "skull_top_z_mm": round(float(model.point(P, "skull_top")[2]) * 1000, 1),
        "hand_target_error_mm": hands,
    }
    gun = model.gun(x)
    wrist = P["wrist.R"]
    gun_in_wrist = np.linalg.inv(wrist) @ gun
    out = {
        "doc": "Hero pose of Morgan.Rig (round 0). bones: local pose-basis rotation quaternions (w, x, y, z); "
               "root_location: the root bone's basis location (its local rest frame, m). Apply with "
               "scripts/stages/pose.py apply_hero_pose(rig). Written by scripts/stages/pose_solve.py.",
        "rig": "Morgan.Rig", "space": "rig (= world: the rig sits at the origin with an identity matrix)",
        "root_bone": root,
        "root_location": [round(float(v), 6) for v in root_basis[:3, 3]],
        "pelvis_world_m": [round(float(v), 6) for v in P[root][:3, 3]],
        "bones": bones,
        "joints_world_mm": {n: [round(float(v) * 1000, 2) for v in P[n][:3, 3]] for n in model.sk.names},
        "carbine_frame": {
            "convention": "origin on the bore axis directly above the trigger; +X along the bore to the muzzle, "
                          "+Z up through the top rail, +Y to the gun's left; metres",
            "matrix_world": [[round(float(v), 7) for v in row] for row in gun],
            "parent_bone": "wrist.R",
            "matrix_in_parent_bone": [[round(float(v), 7) for v in row] for row in gun_in_wrist],
            "points_mm": {k: list(v) for k, v in CARBINE.items() if k != "length_mm"},
            "length_mm": CARBINE["length_mm"],
            "grip_points_mm": {"pistol_grip": list(CARBINE["pistol_grip"]), "handguard": list(CARBINE["handguard"])},
            "hand_targets_mm": {s: {b: [round(float(v) * 1000, 1) for v in p] for b, p in model.hand_local[s].items()}
                                for s in "LR"},
            "pins_px": {"butt_pad_centre": list(PIN_BUTT), "muzzle": list(PIN_MUZZLE), "butt_depth_y_m": BUTT_Y},
        },
        "joints_px": joints,
        "readback": readback,
        "residual_terms": {k: round(float(v), 2) for k, v in info.items() if not k.startswith("joint:")},
        "solve": {"cost": round(float(best.cost), 3), "params": model.n, "residuals": int(len(r)),
                  "restarts": restarts, "seconds": round(secs, 1), "status": best.message},
        "finger_curls_deg": CURLS,
    }
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"joints_residual_px": {n: j["residual_px"] for n, j in joints.items()}, **readback,
                      "solve": out["solve"]}, indent=1))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--restarts", type=int, default=3)
    a = ap.parse_args()
    sys.exit(solve(a.restarts))
