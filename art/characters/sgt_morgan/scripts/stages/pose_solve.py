"""Round 0 (and 2), stage 2a: solve the hero pose of Morgan.Rig against the reference (numpy + scipy, no Blender).

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

The image is one view, so depth comes from the priors and the hand/carbine geometry. Round 2 adds the
real surfaces (README "Round 2"): the carbine and carrier as signed distance fields and the gloves,
sleeves and forearm guards as skinned point sets (cache/stages/contact.npz, pose_contact.py), with
non-penetration, the palms on their grips, the butt pad on the carrier, the right hand first placed on
the grip as a rigid body (place_hand), the fingers fitted to the grip surfaces (fit_fingers, replacing the
curl tables) and a face term (MediaPipe's face landmarks, face_targets.json). Writes
scripts/stages/hero_pose.json: bone -> rotation quaternion (w, x, y, z) in the bone's local (pose basis)
space, the root location, the carbine frame and grip points, the per-joint residuals, the contact
distances per stage and the fitted finger angles.

  "$SGT_PYIMG" -I scripts/stages/pose_solve.py [--restarts N] [--no-contact] [--refit-fingers]
      (about 25 minutes with contact; --no-contact is round 1's objective, 10 s)
  "$SGT_PYIMG" -I scripts/stages/pose_solve.py --continue-from <state.npz> [--place-left]
      (round 7: from a saved state; --place-left first fits the left arm and fingers round the handguard)
  "$SGT_PYIMG" -I scripts/stages/pose_solve.py --continue-from <state.npz> --hold
      (round 11: the left hand cradling the handguard from below, HOLD; README "Round 11: the hold")
  "$SGT_PYIMG" -I scripts/stages/pose_solve.py --face-targets      (rebuild face_targets.json from head.py's fit)
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
FACE_JSON = os.path.join(HERE, "face_targets.json")
CONTACT_NPZ = os.path.join(PROJECT, "cache", "stages", "contact.npz")
SDF_NPZ = os.path.join(PROJECT, "cache", "stages", "contact_sdf.npz")
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

# Round 7 (critic m15, the head turned less than drawn): with the face term on (MediaPipe's ~400 landmarks), the hand
# read single pixels of the pupils, nose tip and menton count the same evidence twice and the skull top is a guess
# through the hair (its 12-17 px residual held the head back). On the round-4 face, the face term alone wants 18.2 deg
# of yaw at 1.02 px RMS; with these four at full weight it settled at 14.2 (1.28 px). Their sigmas are multiplied by
# these factors while the face term is on; the right ear (MediaPipe has no ear) keeps its own.
FACE_SUPERSEDES = {"pupil_R": 3.0, "pupil_L": 3.0, "nose_tip": 3.0, "chin": 3.0, "skull_top": 2.0}

HEEL_SEAT, BALL_SEAT = 0.036, 0.024    # footbed heights (m), LOWA Zephyr class (take 1 spec 02 §3.1)
# the left foot: 17 in round 0 (spec 08 D3); round 2 projects the boot toe through the hero camera and the
# drawn toe matches about 5 (at 17 the toe landed ~6 cm past the drawn one, to his left)
# Round 7 (critic m16: the right leg turned out ~70 deg, the knee pad facing out): the drawing's right boot is in
# profile (85-100 deg) while its knee pad faces only ~25-45 deg out, which no comfortable leg does. Round 4 reached
# the boot's heading by twisting the foot 39 deg against the shank and the tibia 12 deg (hip 27). Reality wins: each
# joint stays in a comfortable standing range (LEG_LIMITS, from the rest leg: hip external rotation to 35, the tibia
# to 12, the foot (ankle and subtalar, with the ~10 deg toe-out of normal tibial torsion) to 15), the knee faces about
# 30 deg to his right (the pelvis's -9 and ~16 of hip turn-out: "roughly forward"), and the right boot turns out about
# 50 deg: still clearly more in profile than the left (+5), no longer a full profile.
FOOT_HEADING = {"R": -50.0, "L": 5.0}  # toe direction, deg from the camera axis (-Y), + toward his left (+X); round 4: R -85
KNEE_FACING = {"R": -30.0, "L": 12.0}  # round 4: R -45
KNEE_FACING_SIGMA = {"R": 8.0, "L": 15.0}   # round 4: 15 both
LEG_LIMITS = {"hip": (-15.0, 35.0), "knee": (-12.0, 12.0), "foot": (-12.0, 15.0)}   # deg, + external (leg_turn)
LEG_PRIOR = {"knee": (5.0, 6.0), "foot": (10.0, 6.0)}                                 # deg: mean, sigma
KNEE_FLEX = {"R": (17.0, 6.0), "L": (9.0, 5.0)}
ELBOW_FLEX = {"R": (88.0, 10.0), "L": (55.0, 12.0)}     # pose note §6 (R 95-100, L 55); round 2: R 88 (the 102 deg elbow pinched the shirt and guard; see README)
# Wrists (deg, relative to the rig's rest hand): flexion + toward the palm, deviation + toward the little
# finger (ulnar). Pose note §6: right extension 12 / ulnar 10, left flexion 10 / radial 10. Normal ranges
# (flexion 70 / extension 60, ulnar 30 / radial 20) are soft limits, so no wrist breaks to reach a grip.
WRIST = {"R": {"flex": (-12.0, 15.0), "dev": (10.0, 10.0)}, "L": {"flex": (10.0, 15.0), "dev": (-10.0, 10.0)}}
WRIST_LIMITS = {"flex": (-60.0, 70.0), "dev": (-20.0, 30.0)}
PELVIS = {"yaw": (-10.0, 6.0), "pitch": (2.0, 4.0), "roll": (0.0, 3.0)}
CHEST_YAW, HEAD_YAW = (-5.0, 5.0), (20.0, 6.0)     # round 4: head yaw sigma 10 -> 6 (the drawing reads ~20; round 2 took 13.7)
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
# round 2: the targets come from place_hand() (the hand resting on the real grip), so they are held tighter
HAND_SIGMA_MM = {"wrist": 30.0, "knuckle": 6.0, "wrist_contact": 12.0, "knuckle_contact": 6.0}
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


# --------------------------------------------------------------------------- contact (round 2)
#
# The real surfaces, from cache/stages/contact.npz (pose_contact.py --export): the carbine's and the carrier's
# inside/outside voxels become signed distance fields (mm, negative inside); the hands' outer surface (the
# glove shells with their knuckle guards and pads, 1.8 mm over the skin), the shirt sleeves and the forearm
# guards are point sets skinned exactly as Blender skins them (linear blend, the parts' own weights).

CONTACT = {
    "pen_sigma_mm": 0.5,          # non-penetration: a point inside by more than its margin costs (depth / 0.5)^2
    "margin_hand_gun_mm": 0.5,    # glove surface to the carbine
    "margin_arm_gun_mm": 1.0,     # sleeve, guard and glove cuff to the carbine
    "margin_carrier_mm": 0.5,     # anything to the carrier
    "touch_mm": 0.8, "touch_sigma_mm": 1.0, "touch_k": 12,    # palm on its grip: mean of the 12 closest points
    # the carbine against the carrier: 2 mm, and the butt pad 3 mm off it by the field, because the carrier's
    # 1.5 mm field, smoothed, rounds the bag's bound corners (the clash test found the pad 2.8 mm into the bag's
    # top-right corner where the field said 1.3 mm clear)
    "margin_carbine_carrier_mm": 2.0,
    "butt_touch_mm": 3.0, "butt_sigma_mm": 0.8, "butt_k": 8,  # butt pad on the carrier's face
    "face_sigma_px": 2.0, "face_equiv": 20.0,   # the face's ~400 landmarks weigh as 20 points at 2 px
}
# Round 7 (critics m39, m47): the reference's stock is pinned under the right arm against the chest, its butt in
# the shoulder's pocket on the carrier and the inner upper arm and elbow closed on its side, so the carbine is braced
# by the arm, not carried by the hands alone. Round 4's arm hung 6 mm (forearm guard) to 80+ mm (upper arm) off it.
# The mean of the k nearest upper-arm and elbow points (sleeve and arm armour) to the stock (gun x behind -160 mm:
# the stock and the buffer tube's rear, not the receiver or the grip) is held at touch_mm.
STOCK_PIN = {"on": True, "x_max_mm": -160.0, "touch_mm": 1.0, "sigma_mm": 1.5, "k": 12}
HAND_CORE = ("wrist", "metacarpal", "finger1-1")     # the palm and the thenar: what the palm terms use
CHAINS = ("finger1", "finger2", "finger3", "finger4", "finger5")


# the trigger guard's opening (gun frame, side view x, z mm; convex, counter-clockwise), see _sdf_from_occ
TRIGGER_KEEPOUT_XZ = ((-36.0, -66.0), (-16.0, -86.0), (28.0, -86.0), (28.0, -46.0), (-26.0, -46.0))


def _sdf_from_occ(occ, h, fill_slices=False, lo3=(0.0, 0.0, 0.0)):
    from scipy import ndimage as ndi
    if fill_slices:        # the carbine: close slots (r 4 voxels) and fill hollows (the handguard) per x slice
        r = 4
        yy, zz = np.mgrid[-r:r + 1, -r:r + 1]
        st = (yy ** 2 + zz ** 2 <= r * r)[None]
        occ = ndi.binary_closing(np.pad(occ, ((0, 0), (r, r), (r, r))), structure=st)[:, r:-r, r:-r] | occ
        occ = ndi.binary_fill_holes(occ, structure=np.array([[[0, 1, 0], [1, 1, 1], [0, 1, 0]]], bool))
        # the trigger guard's opening is a keep-out volume (trigger discipline for every finger: round 2's first
        # fit curled the right middle finger into it, onto the guard's rear leg, where no glove point was
        # inside the thin bar). A side-view polygon (gun frame x, z mm, round 2's guard: rear leg from the grip
        # front at z -66 down to -86, bottom bar at -87, front leg at x +26) across the lower's width (+-13 mm).
        ii, jj, kk = np.meshgrid(*(np.arange(n) for n in occ.shape), indexing="ij", sparse=True)
        X, Y, Z = (lo3[0] + (ii + 0.5) * h, lo3[1] + (jj + 0.5) * h, lo3[2] + (kk + 0.5) * h)
        poly = np.array(TRIGGER_KEEPOUT_XZ)
        inside = np.ones(np.broadcast_shapes(X.shape, Z.shape), bool)
        for a, b in zip(poly, np.roll(poly, -1, axis=0)):          # convex, counter-clockwise in (x, z)
            inside &= (b[0] - a[0]) * (Z - a[1]) - (b[1] - a[1]) * (X - a[0]) >= 0
        occ = occ | (inside & (np.abs(Y) <= 13.0))
    din = ndi.distance_transform_edt(occ)
    dout = ndi.distance_transform_edt(~occ)
    sdf = np.where(occ, -(din - 0.5), dout - 0.5) * h
    # smoothed one voxel: a voxel distance field's gradient jumps from cell to cell (ridges, quantization),
    # which made the cost rough at the 0.01 mm scale and stalled the trust region
    sdf = ndi.gaussian_filter(np.clip(sdf, -40.0, 80.0), 1.0)
    return sdf.astype(np.float32), occ


class Contact:
    def __init__(self, model):
        from scipy import ndimage as ndi
        self.ndi = ndi
        d = np.load(CONTACT_NPZ)
        self.m = model
        names = [str(n) for n in d["bone_names"]]
        sk = model.sk
        self.bnames = names
        self.restinv = [np.linalg.inv(sk.rest[n]) for n in names]
        if os.path.exists(SDF_NPZ) and os.path.getmtime(SDF_NPZ) > os.path.getmtime(CONTACT_NPZ):
            s = np.load(SDF_NPZ)
            self.gun_sdf, self.car_sdf, self.gun_surf = s["gun"], s["car"], s["gun_surf"]
        else:
            t = time.perf_counter()
            occ = np.unpackbits(d["carbine_occ"])[:int(np.prod(d["carbine_shape"]))].reshape(d["carbine_shape"]).astype(bool)
            self.gun_sdf, occf = _sdf_from_occ(occ, float(d["carbine_h"]), fill_slices=True, lo3=d["carbine_lo"])
            occ = np.unpackbits(d["carrier_occ"])[:int(np.prod(d["carrier_shape"]))].reshape(d["carrier_shape"]).astype(bool)
            self.car_sdf, _ = _sdf_from_occ(occ, float(d["carrier_h"]))
            # the carbine's surface as points (its filled outer boundary voxels, about one per 9 mm2)
            surf = occf & ~ndi.binary_erosion(occf)
            ijk = np.argwhere(surf)
            rng = np.random.default_rng(3)
            ijk = ijk[rng.random(len(ijk)) < 0.12]
            self.gun_surf = (d["carbine_lo"] + (ijk + 0.5) * float(d["carbine_h"])).astype(np.float32)
            np.savez(SDF_NPZ, gun=self.gun_sdf, car=self.car_sdf, gun_surf=self.gun_surf)
            print(f"contact: signed distance fields built in {time.perf_counter() - t:.1f} s", flush=True)
        # float64: map_coordinates returns the grid's type, and float32 rounding (1e-6 mm on a 10 mm distance,
        # summed over thousands of points) swamped the finite-difference Jacobian (round 2's first solves stalled)
        self.gun_sdf, self.car_sdf = self.gun_sdf.astype(np.float64), self.car_sdf.astype(np.float64)
        self.gun_lo, self.gun_h = d["carbine_lo"], float(d["carbine_h"])
        self.car_lo, self.car_h = d["carrier_lo"], float(d["carrier_h"])
        self.car_bone = str(d["carrier_ref_bone"])
        self.car_M0 = d["carrier_ref_matrix_mm"]
        # the butt pad's rear face (carbine frame, mm): the pad's vertices within 2 mm of its rearmost plane (the
        # pad's thinnest axis, by PCA, is its face normal; rear = toward -x), at most 60 of them
        bp = d["carbine_buttpad_V"].astype(float)
        c = bp.mean(0)
        nrm = np.linalg.svd(bp - c)[2][-1]
        nrm = nrm if nrm[0] < 0 else -nrm
        h_ = (bp - c) @ nrm
        rear = bp[h_ > h_.max() - 2.0]
        self.butt = rear[np.linspace(0, len(rear) - 1, min(60, len(rear))).astype(int)]
        self.gun_surf = self.gun_surf[self.gun_surf[:, 0] < 120.0]    # only the rear half can reach the carrier
        # point sets
        self.sets = {}
        for key in ("glove_L", "glove_R", "guard_L", "guard_R", "sleeve_L", "sleeve_R", "armarm_L", "armarm_R",
                    "skin_L", "skin_R", "face"):
            if f"pts_{key}_V" not in d:
                continue
            V = d[f"pts_{key}_V"].astype(float) / 1000.0
            bi, bw = d[f"pts_{key}_bi"], d[f"pts_{key}_bw"].astype(float)
            dom = [names[i] for i in bi[:, 0]]
            self.sets[key] = {"V": np.c_[V, np.ones(len(V))], "bi": bi, "bw": bw, "N": d[f"pts_{key}_N"].astype(float),
                              "dom": np.array(dom), "obj": d[f"pts_{key}_obj"],
                              # while the body is solved, a subset (speed); the report and the fingers use all
                              "sub": np.arange(len(V)) % {"glove": 2, "guard": 6}.get(key[:5], 3) == 0}
        self.subsample = True
        for s in "LR":
            g = self.sets[f"glove_{s}"]
            g["core"] = np.array([n.startswith(HAND_CORE) for n in g["dom"]])
            g["chain"] = np.array([next((c for c in CHAINS if n.startswith(c + "-")), "palm") for n in g["dom"]])
            g["chain"][np.array([n.startswith("finger1-1") for n in g["dom"]])] = "palm"
            # palm side at rest: the normal against the rest palm normal (out of the palm)
            H = model.H
            w, i2, i5, m3 = H[f"wrist.{s}"], H[f"finger2-1.{s}"], H[f"finger5-1.{s}"], H[f"finger3-1.{s}"]
            a_ = (m3 - w) / np.linalg.norm(m3 - w)
            k_ = (i5 - i2) / np.linalg.norm(i5 - i2)
            n = np.cross(a_, k_) if s == "R" else -np.cross(a_, k_)
            n /= np.linalg.norm(n)
            g["palmar"] = g["N"] @ n > 0.35
            # round 11 (HOLD): the palm centre's points (palm side, on the metacarpals) and the points the rail term
            # watches (fingers 2-5, every second point)
            g["palmc"] = g["palmar"] & np.array([d_.startswith("metacarpal") for d_ in g["dom"]])
            g["railset"] = np.isin(g["chain"], CHAINS[1:]) & (np.arange(len(g["dom"])) % 2 == 0)
            sk_ = self.sets[f"skin_{s}"]
            sk_["chain"] = np.array([next((c for c in CHAINS if n_.startswith(c + "-")), "palm") for n_ in sk_["dom"]])
            sk_["chain"][np.array([n_.startswith("finger1-1") for n_ in sk_["dom"]])] = "palm"
            # the sleeve and guard points that can meet the carrier: the lower upper arm down (not the shoulder,
            # which the straps lie on by design)
            for key in (f"sleeve_{s}", f"guard_{s}", f"armarm_{s}"):
                if key not in self.sets:
                    continue
                q = self.sets[key]
                q["arm"] = np.array([n_.startswith(("upperarm02", "lowerarm", "wrist")) for n_ in q["dom"]])
                # round 7: what can pin the stock: the upper arm and the elbow (STOCK_PIN)
                q["pin"] = np.array([n_.startswith(("upperarm01", "upperarm02", "lowerarm01")) for n_ in q["dom"]])
        if "face" in self.sets and os.path.exists(FACE_JSON):
            fj = json.load(open(FACE_JSON, encoding="utf-8"))
            vid = {v: i for i, v in enumerate(fj["vertex_ids"])}
            self.face_idx = np.array([[vid[v] for v in L["verts"]] for L in fj["landmarks"]])
            self.face_bary = np.array([L["bary"] for L in fj["landmarks"]])
            self.face_ref = np.array([L["ref_px"] for L in fj["landmarks"]])
            self.face_w = np.array([L["weight"] for L in fj["landmarks"]])
        else:
            self.face_idx = None

    def mats(self, P):
        return np.stack([P[n] @ ri for n, ri in zip(self.bnames, self.restinv)])

    def lbs(self, key, Ms, sel=None):
        s = self.sets[key]
        V, bi, bw = s["V"], s["bi"], s["bw"]
        if sel is not None:
            V, bi, bw = V[sel], bi[sel], bw[sel]
        out = np.zeros((len(V), 3))
        for c in range(4):
            M = Ms[bi[:, c]]
            out += bw[:, c, None] * np.einsum("nij,nj->ni", M[:, :3, :], V)
        return out

    def _lookup(self, grid, lo, h, pts_mm):
        q = ((pts_mm - lo) / h - 0.5).T
        return self.ndi.map_coordinates(grid, q, order=1, mode="constant", cval=80.0)   # outside the grid: clear

    def gun_d(self, pts_m, G):
        loc = (pts_m - G[:3, 3]) @ G[:3, :3]
        return self._lookup(self.gun_sdf, self.gun_lo, self.gun_h, loc * 1000.0)

    def car_frame(self, P):
        M = P[self.car_bone].copy()
        M[:3, 3] *= 1000.0
        return self.car_M0 @ np.linalg.inv(M)          # posed world mm -> the carrier's export frame

    def car_d(self, pts_m, P, T=None):
        T = self.car_frame(P) if T is None else T
        q = pts_m * 1000.0 @ T[:3, :3].T + T[:3, 3]
        return self._lookup(self.car_sdf, self.car_lo, self.car_h, q)

    def gun_world(self, pts_mm, G):
        return pts_mm / 1000.0 @ G[:3, :3].T + G[:3, 3]


def softplus(z, tau=0.25):
    """A smooth hinge max(0, z) (mm): tau log(1 + e^(z / tau)); 0.17 mm at z = 0, under 0.005 beyond 1 mm clear."""
    return tau * np.logaddexp(0.0, np.asarray(z) / tau)


def kmin_mean(d, k):
    k = min(k, len(d))
    return float(np.mean(np.partition(d, k - 1)[:k]))


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
        self.thigh_front = {}       # round 7: the thigh's anterior axis, as the shank's
        for s in "LR":
            Rl = R[f"upperleg01.{s}"]
            cand = [Rl[:, 0], -Rl[:, 0], Rl[:, 2], -Rl[:, 2]]
            best = max(range(4), key=lambda j: cand[j] @ np.array([0, -1.0, 0]))
            self.thigh_front[s] = (Rl.T @ cand[best])
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
        # round 2: the real surfaces (set by solve()); finger rotations held fixed while the body is solved
        self.contact, self.finger_basis, self.contact_full = None, {}, False
        self.gun_pen = True        # False: the hands and arms may pass through the carbine (the reach stage)
        self.hand_skip = set()     # round 7: sides whose hand targets are switched off (place_left_arm)
        self.root = sk.names[0] if sk.parent[sk.names[0]] is None else [n for n in sk.names if sk.parent[n] is None][0]
        # round 7: the legs' rotations at rest (the bones' rolls put the thigh's axis ~9 deg off the shank's), so
        # the readback and the limits measure from the rest leg
        b0, rw0 = self.basis(np.zeros(self.n))
        P0 = sk.fk(b0, rw0)
        self.leg_rest = {s: self.leg_rotations(P0, s) for s in "LR"}

    def leg_turn(self, P, s):
        """(hip, knee, foot) external rotation from the rest leg, deg (leg_rotations less the rest's)."""
        return tuple(a - b for a, b in zip(self.leg_rotations(P, s), self.leg_rest[s]))

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
        b.update(self.finger_basis)
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

    def leg_rotations(self, P, s):
        """Round 7: the leg's turn-out split by joint (deg, + = external rotation, the toe or kneecap turned away
        from the midline): the hip (the thigh's front against the pelvis's, about the femur), the knee (the shank's
        front against the thigh's, about the shank) and the foot (its heel-to-toe line against the shank's front,
        seen from above: the ankle and subtalar joints). Their sum is about the foot's heading against the pelvis."""
        sg = 1.0 if s == "R" else -1.0

        def about(u, a, b):
            u = u / np.linalg.norm(u)
            a = a - u * (a @ u)
            b = b - u * (b @ u)
            return math.degrees(math.atan2(float(u @ np.cross(a, b)), float(a @ b)))
        Rp = P[self.root][:3, :3] @ self.R[self.root].T
        pf = Rp @ np.array([0.0, -1.0, 0.0])
        h, k, a = (P[n][:3, 3] for n in (f"upperleg01.{s}", f"lowerleg01.{s}", f"foot.{s}"))
        tf = P[f"upperleg01.{s}"][:3, :3] @ self.thigh_front[s]
        kf = P[f"lowerleg01.{s}"][:3, :3] @ self.knee_front[s]
        hip = sg * about(k - h, pf, tf)
        knee = sg * about(a - k, tf, kf)
        toe = self.point(P, f"toe_{s}") - self.point(P, f"heel_{s}")
        foot = sg * about(np.array([0.0, 0.0, -1.0]), kf, toe)
        return hip, knee, foot

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
                self.last_norm[name] = val / sigma
        if detail:
            self.last_norm = {}
        # 1. reprojection
        names = list(TARGETS)
        pts = np.array([self.point(P, n) for n in names])
        px = CAM.project(pts)
        face_on = self.contact is not None and self.contact.face_idx is not None
        for n, p in zip(names, px):
            _, tgt, sig, _ = TARGETS[n]
            if face_on:
                sig *= FACE_SUPERSEDES.get(n, 1.0)
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
        if self.contact is None:
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
            if self.contact is None:
                add(f"hand:palm_on_grip_{s}", (dist - rad / 1000.0) * 1000.0, 6.0)
            # and the palm faces the grip axis
            toward = -(v - a * (v @ a)) / max(dist, 1e-6)
            if self.contact is None:     # round 2: place_hand() sets the hand's orientation on the real grip
                add(f"hand:palm_faces_grip_{s}", math.degrees(math.acos(max(-1.0, min(1.0, float(n @ toward))))), 25.0)
        for s, T in self.hand_targets(G).items():
            for bone, t in T.items():
                d = P[bone][:3, 3] - t
                for j in range(3):
                    sg = HAND_SIGMA_MM["wrist" if bone.startswith("wrist") else "knuckle"]
                    if self.contact is not None:
                        sg = HAND_SIGMA_MM["wrist_contact" if bone.startswith("wrist") else "knuckle_contact"]
                    # round 7: place_left_arm fits the left hand to the gun itself, without the old target
                    add(f"hand:{bone}:{'xyz'[j]}", 0.0 if s in self.hand_skip else d[j] * 1000.0, sg)
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
            add(f"prior:knee_facing_{s}", self.knee_facing(P, s) - KNEE_FACING[s], KNEE_FACING_SIGMA[s])
            # round 7: each joint of the leg within its comfortable standing range
            for nm, v in zip(("hip", "knee", "foot"), self.leg_turn(P, s)):
                lo_, hi_ = LEG_LIMITS[nm]
                add(f"limit:leg_{nm}_rot_{s}", min(0.0, v - lo_) + max(0.0, v - hi_), 1.0)
                if nm in LEG_PRIOR:
                    add(f"prior:leg_{nm}_rot_{s}", v - LEG_PRIOR[nm][0], LEG_PRIOR[nm][1])
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
        # 6. round 2: the real surfaces
        if self.contact is not None:
            self.contact_terms(P, G, add, r, detail, info)
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

    def contact_terms(self, P, G, add, r, detail, info):
        """Contact and non-penetration against the real carbine and carrier, and the face landmarks."""
        C_, K = self.contact, CONTACT
        Ms = C_.mats(P)
        Tc = C_.car_frame(P)
        pen = K["pen_sigma_mm"]

        def hinge(name, d, margin):
            if not self.gun_pen and "_in_carbine" in name:
                return
            v = softplus(margin - d) / pen
            r.extend(v.tolist())
            if detail:
                info[name] = round(float(max(0.0, -d.min())) if len(d) else 0.0, 2)   # deepest penetration, mm
                info[name + ":min_mm"] = round(float(d.min()), 2) if len(d) else None
        sub = C_.subsample
        for s in "LR":
            g = C_.sets[f"glove_{s}"]
            sel = np.ones(len(g["V"]), bool) if self.contact_full else g["core"].copy()
            if sub:
                sel &= g["sub"] | (g["core"] & g["palmar"])
            X = C_.lbs(f"glove_{s}", Ms, sel)
            dg = C_.gun_d(X, G)
            hinge(f"pen:glove_{s}_in_carbine", dg, K["margin_hand_gun_mm"])
            hinge(f"pen:glove_{s}_in_carrier", C_.car_d(X, P, Tc), K["margin_carrier_mm"])
            # the palm on its grip: the mean of its closest points' distances
            palm = (g["core"] & g["palmar"])[sel]
            add(f"touch:palm_{s}", kmin_mean(dg[palm], K["touch_k"]) - K["touch_mm"], K["touch_sigma_mm"])
            pin_d = []
            for key in (f"sleeve_{s}", f"guard_{s}", f"armarm_{s}"):
                if key not in C_.sets:
                    continue
                q = C_.sets[key]
                sel = q["sub"] if sub else np.ones(len(q["V"]), bool)
                Y = C_.lbs(key, Ms, sel)
                dY = C_.gun_d(Y, G)
                hinge(f"pen:{key}_in_carbine", dY, K["margin_arm_gun_mm"])
                hinge(f"pen:{key}_in_carrier", C_.car_d(Y[q["arm"][sel]], P, Tc), K["margin_carrier_mm"])
                if s == "R" and key != f"guard_{s}":
                    # round 7: the distance to the stock of the upper arm's and elbow's outer surface; a point
                    # beside the receiver (gun x past STOCK_PIN's end) counts as that much farther
                    pm = q["pin"][sel]
                    gx = ((Y[pm] - G[:3, 3]) @ G[:3, 0]) * 1000.0
                    pin_d.append(dY[pm] + softplus(gx - STOCK_PIN["x_max_mm"], 2.0))
            if s == "R" and pin_d and STOCK_PIN["on"]:
                # the stock pinned under the right arm (critics m39, m47): the butt in the shoulder's pocket on the
                # carrier (touch:butt_on_carrier) and the arm closed on the stock's side, so the carbine is braced
                v = kmin_mean(np.concatenate(pin_d), STOCK_PIN["k"])
                add("touch:stock_under_arm_R", v - STOCK_PIN["touch_mm"], STOCK_PIN["sigma_mm"])
        if HOLD["on"]:
            v, hinfo = self.hold_terms(P, G, Ms)
            r.extend(v.tolist())
            if detail:
                info.update(hinfo)
        # the carbine clear of the carrier (pouches, bag), the butt pad on its face
        S = C_.gun_world(C_.gun_surf[::2] if sub else C_.gun_surf, G)
        hinge("pen:carbine_in_carrier", C_.car_d(S, P, Tc), K["margin_carbine_carrier_mm"])
        db = C_.car_d(C_.gun_world(C_.butt, G), P, Tc)
        add("touch:butt_on_carrier", kmin_mean(db, K["butt_k"]) - K["butt_touch_mm"], K["butt_sigma_mm"])
        # the face: MediaPipe's landmarks on the reference against the same mesh points on the model
        if C_.face_idx is not None:
            F = C_.lbs("face", Ms)
            pts = np.einsum("lk,lkj->lj", C_.face_bary, F[C_.face_idx])
            px = CAM.project(pts)
            sig = K["face_sigma_px"] * math.sqrt(len(px) / K["face_equiv"]) / C_.face_w
            e = px - C_.face_ref
            r.extend((e[:, 0] / sig).tolist())
            r.extend((e[:, 1] / sig).tolist())
            if detail:
                info["face:rms_px"] = round(float(np.sqrt(np.mean(np.sum(e ** 2, 1)))), 2)
                info["face:mean_dx_dy_px"] = [round(float(v), 2) for v in e.mean(0)]

    def hold_terms(self, P, G, Ms=None):
        """Round 11 (HOLD): the left palm under the handguard. Residuals (fixed length) and a readback: the palm centre's
        station along the handguard, its place under it, the palm normal up into it, and fingers 2-5 kept off the rail."""
        C_, H_ = self.contact, HOLD
        Ms = C_.mats(P) if Ms is None else Ms
        g = C_.sets["glove_L"]
        pc = ((C_.lbs("glove_L", Ms, g["palmc"]) - G[:3, 3]) @ G[:3, :3]).mean(0) * 1000.0
        W, i2, i5 = (P[b][:3, 3] for b in ("wrist.L", "finger2-1.L", "finger5-1.L"))
        n = -np.cross((i2 + i5) / 2 - W, i5 - i2)
        nG = G[:3, :3].T @ (n / np.linalg.norm(n))
        ang = math.degrees(math.acos(max(-1.0, min(1.0, float(nG @ np.array(H_["palm_up"]))))))
        ps = H_["palm_pos_sigma_mm"]
        out = [(pc[0] - H_["station_x_mm"]) / H_["station_sigma_mm"],
               float(softplus(ang - H_["palm_up_tol_deg"], 1.0)) / H_["palm_up_sigma_deg"],
               float(softplus(H_["palm_y_mm"][0] - pc[1], 0.5)) / ps, float(softplus(pc[1] - H_["palm_y_mm"][1], 0.5)) / ps,
               float(softplus(pc[2] - H_["palm_z_max_mm"], 0.5)) / ps]
        K = (G[:3, :3].T @ ((i2 + i5) / 2 - G[:3, 3])) * 1000.0
        a = G[:3, :3].T @ (P["finger3-1.L"][:3, 3] - W)
        aang = math.degrees(math.acos(max(-1.0, min(1.0, float(a @ np.array(H_["axis"]) / np.linalg.norm(a))))))
        ks = H_["knuckle_sigma_mm"]
        out += [float(softplus(K[1] - H_["knuckle_y_max_mm"], 0.5)) / ks,
                float(softplus(H_["knuckle_z_min_mm"] - K[2], 0.5)) / ks,
                float(softplus(aang - H_["axis_tol_deg"], 1.0)) / H_["axis_sigma_deg"]]
        Lr = (C_.lbs("glove_L", Ms, g["railset"]) - G[:3, 3]) @ G[:3, :3] * 1000.0
        w = (np.clip((Lr[:, 0] - 110.0) / 10.0, 0, 1) * np.clip((470.0 - Lr[:, 0]) / 10.0, 0, 1)
             * np.clip((16.0 - np.abs(Lr[:, 1])) / 4.0, 0, 1))
        rail = w * softplus(Lr[:, 2] - H_["rail_z_mm"], 0.5) / H_["rail_sigma_mm"] * (1.0 if H_["rail_on"] else 0.0)
        info = {"hold:palm_centre_gun_mm": [round(float(c), 1) for c in pc],
                "hold:palm_normal_gun": [round(float(c), 3) for c in nG],
                "hold:palm_normal_off_up_deg": round(ang, 1),
                "hold:knuckles_gun_mm": [round(float(c), 1) for c in K], "hold:hand_axis_off_deg": round(aang, 1),
                "hold:rail_max_z_mm": round(float((Lr[:, 2] * (w > 0.5)).max()), 1) if (w > 0.5).any() else None}
        return np.r_[out, rail], info

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


# Finger fit (round 2): each finger's MCP flexion and spread, PIP and DIP flexion (the thumb: two axes at its
# base) fitted so every phalanx's glove surface touches the grip without entering it, the gloves stay out of
# the other fingers' and the palm's skin, and the curls stay near the tables above (weakly). The right index
# lies straight along the receiver above the trigger guard (trigger discipline).
FINGER = {
    "touch_mm": 0.6, "touch_k": 4,
    # phalanges that rest on the gun, and how firmly (sigma, mm)
    # round 11: the right ring and little proximal phalanges at 1 mm (they stood 3.5-4 mm off the grip: a loose fist)
    "touch": {"R": {"finger3": (2.0, 2.0, 2.0), "finger4": (1.0, 2.0, 2.0), "finger5": (1.0, 2.0, 2.0),
                    "finger2": (None, 3.0, 3.0), "finger1": (None, 2.0, 2.0)},
              "L": {"finger2": (3.0, 2.0, 2.0), "finger3": (3.0, 2.0, 2.0), "finger4": (3.0, 2.0, 2.0),
                    "finger5": (3.0, 2.0, 2.0), "finger1": (None, 3.0, 3.0)}},
    "self_margin_mm": 0.6,       # a glove point to another finger's (or the palm's) skin
    "prior_sigma_deg": 30.0, "spread_sigma_deg": 4.0, "dip_pip_ratio": 0.7, "dip_sigma_deg": 12.0,
    # neighbouring fingers curl alike (MCP and PIP; not the right index, which lies along the receiver): without
    # it the left hand's fingers splayed and curled each its own way over the handguard
    "neighbour_sigma_deg": 15.0,
    "index_floor_mm": -52.0,     # right index: its glove above the lower receiver's bottom at the trigger (z -54; the guard hangs below)
    "index_straight_sigma_deg": 8.0,
    "thumb_sigma_deg": 15.0,     # the thumb stays near its table pose (round 2's first fit lifted the right one into the air)
}
# Round 4, the grasp (the reference: the right hand a closed fist on the pistol grip, the fingers wrapped round the
# grip's front strap, the thumb round its far side, the index straight along the receiver; the left hand over the
# handguard with the fingers curled under it). Round 2's fit only asked each phalanx to touch the gun, and with the
# hand turned 30 deg on the grip the fingers touched it nearly open. Each entry holds the mean of a finger's distal
# glove points (gun frame, mm) beyond a bound: (axis, bound, +1 = at least / -1 = at most, sigma mm), one hinge each.
GRASP = {
    "R": {"finger3": [("y", 4.0, +1, 2.0)], "finger4": [("y", 4.0, +1, 2.0)], "finger5": [("y", 2.0, +1, 2.0)],
          # the thumb round the grip's far (left, +Y) side below the receiver, not along the receiver's wall
          "finger1": [("y", 6.0, +1, 2.0), ("z", -46.0, -1, 3.0)]},
    # the tips curled under the handguard (octagon 38.1 across the flats, 19 to a flat: its 4:30 bevel spans z -8 to
    # -19 on the camera side, y < 0): below its middle, in toward its bottom flat, and not hanging below it (a first
    # try with only "z below -9" let the fingers hang straight down the right face past the bottom)
    "L": {f: [("z", -10.0, -1, 2.0), ("z", -27.0, +1, 2.0), ("y", -15.0, +1, 2.0)]
          for f in ("finger2", "finger3", "finger4", "finger5")},
}
# Round 11, the hold (Jeff: "the left hand is wrong. It should be cupping the rifle underneath not on top"; critics r9 m29,
# m32, m47, r10 m3, m15, D6, r11 C1 D3 blocking). The reference's left hand cradles the handguard from below: the palm under
# it facing up, the wrist on the gun's left (his body's side), the fingers curled round the gun's right face (the camera
# side, the side away from him) with their tips on that face, the thumb along the gun's left side or over its top on that
# side. From the hero camera a hand over the handguard and one under it project to nearly the same keypoints (the
# single-view depth case, notes/research_canitcode.md), so the grasp itself is constrained (HOLD, gun frame): the
# fingertips on the lower half of the right face (y -25 to -11, within ~6 mm of its flat at -18.5; z -17 to +2: with
# z up to +10 the first hold curled them to the face's top edge, where the drawing shows them at its lower edge), the thumb's
# tip on the gun's left half near its face; the palm terms are in HOLD.
GRASP_UNDER_L = {**{f: [("y", -11.0, -1, 2.0), ("y", -25.0, +1, 2.0), ("z", 2.0, -1, 2.0), ("z", -17.0, +1, 2.0)]
                    for f in ("finger2", "finger3", "finger4", "finger5")},
                 # the thumb's tip on the gun's left half and near its left face (+18.5): a first placement left it
                 # pointing at the muzzle 69 mm out in the air
                 "finger1": [("y", 3.0, +1, 3.0), ("y", 28.0, -1, 3.0)]}
HOLD = {
    "on": False,               # set by --hold (round 11): GRASP["L"] becomes GRASP_UNDER_L and the palm terms below apply
    "rail_on": True,           # off while place_left_under aims the arm with the fingers fixed at a wrap
    # the palm centre (the mean of the glove's palm-side metacarpal points, gun frame, mm) along the handguard: the drawn
    # hand is 0.53 of the way from the receiver face to the drawn handguard's front (0.37 of the way to the muzzle), on
    # the real MCMR-13 (x 117 to 457) x 297 (277); round 7's was 252
    "station_x_mm": 290.0, "station_sigma_mm": 2.0,
    # under the handguard (octagon 38.1 across the flats, bottom flat at z -19.05, 17 wide): the palm centre below z -14,
    # between y -6 and +16 (the bottom flat and the gun's left lower bevel, where a palm cupping from his side rests)
    "palm_y_mm": (-6.0, 16.0), "palm_z_max_mm": -14.0, "palm_pos_sigma_mm": 1.0,
    # the palm normal (out of the palm) points up into the handguard: within palm_up_tol_deg of palm_up (gun +Z leaned
    # 15 deg toward the camera side, as a palm on the left lower bevel faces)
    "palm_up": (0.0, -0.2588, 0.9659), "palm_up_tol_deg": 20.0, "palm_up_sigma_deg": 2.0,
    # no glove of fingers 2-5 at the rail: points over the handguard (x 120-460) within 14 mm of its top centre line may
    # not rise above z +15 (the rail's base is the octagon's top flat at +19; the slots and teeth to +26.5)
    "rail_z_mm": 15.0, "rail_sigma_mm": 1.0,
    # the hand across the handguard, not hanging under it: the knuckle line (index to little MCP centres) beside the
    # gun's right lower corner (y at most -14, z at least -40: the palm is flat, so its bone line runs ~15 mm under the
    # palm's skin and the knuckles cannot rise to the corner itself), so the fingers rise up the right face, and the hand's axis
    # (wrist to middle MCP) within axis_tol_deg of gun -Y (a first aim without these hung the hand under the gun, the
    # knuckles 51 mm below the bore and the fingers pointing at the muzzle)
    "knuckle_y_max_mm": -14.0, "knuckle_z_min_mm": -40.0, "knuckle_sigma_mm": 1.5,
    "axis": (0.0, -1.0, 0.0), "axis_tol_deg": 35.0, "axis_sigma_deg": 2.5,
    # the arm-only placement (place_left_under): starts over the forearm's twist, the gun's surfaces off (the hand passes
    # through the handguard to get under it), then on
    "twist_starts_deg": (-100.0, -50.0, 0.0, 50.0, 100.0), "aim_nfev": 60,
    "curl_starts": ((40.0, 60.0), (60.0, 80.0)),     # place_left_arm's finger starts (MCP, PIP) under the handguard
}
FINGER_BOUNDS = {1: (-35.0, 95.0), 2: (0.0, 110.0), 3: (0.0, 85.0)}
THUMB_BOUNDS = {1: (-40.0, 80.0), 2: (-20.0, 80.0), 3: (-10.0, 85.0)}


def finger_axes(model, s):
    """bone -> [(local axis, kind)] for the finger chains of side s (rest geometry, as finger_basis)."""
    sk, H, R = model.sk, model.H, model.R
    w, i2, i5, m3 = H[f"wrist.{s}"], H[f"finger2-1.{s}"], H[f"finger5-1.{s}"], H[f"finger3-1.{s}"]
    a = (m3 - w) / np.linalg.norm(m3 - w)
    k = (i5 - i2) / np.linalg.norm(i5 - i2)
    n = np.cross(a, k) if s == "R" else -np.cross(a, k)
    n /= np.linalg.norm(n)
    out = {}
    for f in CHAINS:
        for j in (1, 2, 3):
            b = f"{f}-{j}.{s}"
            y = sk.tail_local[b][:3]
            y = R[b] @ (y / np.linalg.norm(y))
            if f == "finger1":
                ax = np.cross(y, n - 0.6 * k)
            else:
                ax = np.cross(y, n)
            ax /= np.linalg.norm(ax)
            axes = [(R[b].T @ ax, "flex")]
            if j == 1:
                sp = np.cross(y, ax) if f == "finger1" else n - y * (n @ y)
                sp /= np.linalg.norm(sp)
                axes.append((R[b].T @ sp, "spread"))
            out[b] = axes
    return out


def fit_fingers(model, x, side, verbose=True):
    """Fit side's finger rotations with the body at x (model.contact set). Updates model.finger_basis."""
    from scipy.spatial import cKDTree
    C_, Fk = model.contact, FINGER
    axes = finger_axes(model, side)
    layout = []          # (bone, axis, kind, table deg, bounds)
    for b, al in axes.items():
        f, j = b.split(".")[0].split("-")
        j = int(j)
        tab = CURLS[side][f][j - 1]
        for ax, kind in al:
            lo_, hi_ = (THUMB_BOUNDS if f == "finger1" else FINGER_BOUNDS)[j] if kind == "flex" else (-25.0, 25.0)
            if kind == "spread" and f == "finger1":
                lo_, hi_ = -40.0, 40.0
            layout.append((b, ax, kind, float(tab) if kind == "flex" else 0.0, (lo_, hi_)))
    g = C_.sets[f"glove_{side}"]
    sk_ = C_.sets[f"skin_{side}"]
    fing = g["chain"] != "palm"
    gidx = np.nonzero(fing)[0]
    gdom, gchain = g["dom"][gidx], g["chain"][gidx]
    gprox = np.array([d.split(".")[0].endswith("-1") for d in gdom])
    sk_bi0 = sk_["bi"][:, 0]
    # Self contact. Finger against finger: each phalanx's skin as a cylinder about its bone (radius: the 80th
    # percentile of its skin's distance to the bone at rest; the joint ends left out, where the webs are), and
    # each glove point of another finger kept outside it. Finger against palm: the middle and distal
    # phalanges' glove against the palm's skin (nearest skin point within 6 mm, signed by its normal).
    # (A nearest-vertex sign alone fails between fingers: at rest it put 70 glove points 16 mm "inside".)
    sk = model.sk
    fbones = [f"{f}-{j}.{side}" for f in CHAINS for j in (1, 2, 3)]
    Srest = sk_["V"][:, :3]
    cyl = {}
    for b in fbones:
        h0 = sk.rest[b][:3, 3]
        t1 = (sk.rest[b] @ sk.tail_local[b])[:3]
        m_ = sk_["dom"] == b
        if not m_.any():
            continue
        u = t1 - h0
        L2 = u @ u
        tt = np.clip((Srest[m_] - h0) @ u / L2, 0, 1)
        dd = np.linalg.norm(Srest[m_] - (h0 + tt[:, None] * u), axis=1)
        r80 = float(np.percentile(dd, 80)) * 1000.0
        # no tighter than the rest pose allows: there the gloves are clear of the skin (gloves.md), so the
        # cylinder may not reach the other fingers' glove points at rest
        Gr = g["V"][gidx][gchain != b.split("-")[0], :3]
        tg = (Gr - h0) @ u / L2
        dg_ = np.linalg.norm(Gr - (h0 + tg[:, None] * u), axis=1)[(tg > 0.06) & (tg < 1.04)] * 1000.0
        cyl[b] = min(r80, float(dg_.min()) - Fk["self_margin_mm"] - 0.2) if len(dg_) else r80
    palm_pool = np.nonzero(sk_["chain"] == "palm")[0]
    tip_glove = np.array([(d.split(".")[0][-1] in "23") and not d.startswith("finger1") for d in gdom])
    touch = []
    for f, sigs in Fk["touch"][side].items():
        for j, sg in zip((1, 2, 3), sigs):
            if sg is None:
                continue
            b = f"{f}-{j}.{side}"
            m = gdom == b
            if f != "finger1":
                m &= g["palmar"][gidx]
            if m.any():
                touch.append((b, np.nonzero(m)[0], sg))
    idx_pts = np.nonzero(np.isin(gdom, [f"finger2-2.{side}", f"finger2-3.{side}"]))[0] if side == "R" else None
    grasp = [(f, np.nonzero(gdom == f"{f}-3.{side}")[0], terms) for f, terms in GRASP.get(side, {}).items()]
    grasp = [g_ for g_ in grasp if len(g_[1])]
    rail_pts = (np.nonzero(np.isin(gchain, CHAINS[1:]) & (np.arange(len(gchain)) % 2 == 0))[0]
                if side == "L" and HOLD["on"] else None)
    G = model.gun(x)
    base_b, rw = model.basis(x)
    keep = {k: v for k, v in model.finger_basis.items() if not k.endswith("." + side)}

    def basis_of(t):
        fb = {}
        for (b, ax, kind, _, _), v in zip(layout, t):
            m = rv(ax * D(v))
            fb[b] = m if b not in fb else fb[b] @ m
        return {b: rot4(m) for b, m in fb.items()}

    def res(t, detail=False):
        bb = dict(base_b)
        bb.update(keep)
        bb.update(basis_of(t))
        P = model.sk.fk(bb, rw)
        Ms = C_.mats(P)
        X = C_.lbs(f"glove_{side}", Ms, fing)
        dg = C_.gun_d(X, G)
        out = list(softplus(Fk_m - dg) / CONTACT["pen_sigma_mm"])
        info = {}
        for b, ii, sg in touch:
            v = kmin_mean(dg[ii], Fk["touch_k"])
            out.append((v - Fk["touch_mm"]) / sg)
            info[b] = round(v, 2)
        # self contact: the glove of each finger against the other fingers' (and, past the proximal
        # phalanx, the palm's) skin
        dself = np.full(len(X), 50.0)
        for b, rad in cyl.items():
            h0 = P[b][:3, 3]
            u = (P[b] @ sk.tail_local[b])[:3] - h0
            m = gchain != b.split("-")[0]
            tt = (X[m] - h0) @ u / (u @ u)
            dd = np.linalg.norm(X[m] - (h0 + tt[:, None] * u), axis=1) * 1000.0 - rad
            w = np.clip((tt - 0.06) / 0.08, 0, 1) * np.clip((1.04 - tt) / 0.06, 0, 1)   # fades out at the ends
            dd = dd * w + 50.0 * (1 - w)
            dself[m] = np.minimum(dself[m], dd)
        S = C_.lbs(f"skin_{side}", Ms, palm_pool)
        Ns = np.einsum("nij,nj->ni", Ms[sk_bi0[palm_pool]][:, :3, :3], sk_["N"][palm_pool])
        dist, nn = cKDTree(S).query(X[tip_glove])
        dp = np.einsum("ij,ij->i", (X[tip_glove] - S[nn]) * 1000.0, Ns[nn])
        w = np.clip((8.0 - dist * 1000.0) / 3.0, 0, 1)          # only the palm skin within 5-8 mm counts
        dp = dp * w + 50.0 * (1 - w)
        dself[tip_glove] = np.minimum(dself[tip_glove], dp)
        out += list(softplus(Fk["self_margin_mm"] - dself) / CONTACT["pen_sigma_mm"])
        info["self_min_mm"] = round(float(dself.min()), 2)
        info["gun_min_mm"] = round(float(dg.min()), 2)
        if detail:
            ig, js = int(np.argmin(dg)), int(np.argmin(dself))
            info["gun_worst"] = (str(gdom[ig]), int((dg < -0.5).sum()))
            info["self_worst"] = (str(gdom[js]), int((dself < 0.0).sum()))
        if grasp:
            for f, ii, terms in grasp:
                q = ((X[ii] - G[:3, 3]) @ G[:3, :3]).mean(0) * 1000.0
                for ax, bound, sgn, sg in terms:
                    v = q["xyz".index(ax)]
                    out.append(float(softplus(sgn * (bound - v), 0.5)) / sg)
                info[f"grasp:{f}"] = [round(float(c), 1) for c in q]
        if rail_pts is not None:          # round 11 (HOLD): fingers 2-5 off the rail
            Lr = (X[rail_pts] - G[:3, 3]) @ G[:3, :3] * 1000.0
            w = (np.clip((Lr[:, 0] - 110.0) / 10.0, 0, 1) * np.clip((470.0 - Lr[:, 0]) / 10.0, 0, 1)
                 * np.clip((16.0 - np.abs(Lr[:, 1])) / 4.0, 0, 1))
            out += list(w * softplus(Lr[:, 2] - HOLD["rail_z_mm"], 0.5) / HOLD["rail_sigma_mm"])
            info["rail_max_z_mm"] = round(float(Lr[w > 0.5, 2].max()), 1) if (w > 0.5).any() else None
        if idx_pts is not None:
            z = ((X[idx_pts] - G[:3, 3]) @ G[:3, :3])[:, 2] * 1000.0
            out += list(np.maximum(0.0, Fk["index_floor_mm"] - z) / 1.0)
            info["index_lowest_z_mm"] = round(float(z.min()), 1)
        # priors
        vals = {}
        for (b, ax, kind, tab, _), v in zip(layout, t):
            vals[(b, kind)] = v
            if kind == "flex":
                sgp = Fk["prior_sigma_deg"]
                if side == "R" and b.startswith("finger2-") and not b.startswith("finger2-1"):
                    sgp = Fk["index_straight_sigma_deg"]
                if b.startswith("finger1-"):
                    sgp = Fk["thumb_sigma_deg"]
                out.append((v - tab) / sgp)
            else:
                out.append(v / (Fk["thumb_sigma_deg"] if b.startswith("finger1-") else Fk["spread_sigma_deg"]))
        for f in CHAINS[1:]:
            pip, dip = vals[(f"{f}-2.{side}", "flex")], vals[(f"{f}-3.{side}", "flex")]
            out.append((dip - Fk["dip_pip_ratio"] * pip) / Fk["dip_sigma_deg"])
        for a_, b_ in (("finger2", "finger3"), ("finger3", "finger4"), ("finger4", "finger5")):
            if side == "R" and a_ == "finger2":
                continue
            for j in (1, 2):
                out.append((vals[(f"{a_}-{j}.{side}", "flex")] - vals[(f"{b_}-{j}.{side}", "flex")]) / Fk["neighbour_sigma_deg"])
        return (np.array(out), info) if detail else np.array(out)
    Fk_m = CONTACT["margin_hand_gun_mm"]
    lo = np.array([L[4][0] for L in layout])
    hi = np.array([L[4][1] for L in layout])
    # several starts: the tables (or the last fit), and the fingers nearly open and half closed, from outside
    # the gun, so they close onto its surface (from the tables, already inside, a finger can only be pushed
    # out the wrong side: round 2's left middle phalanges stuck 5.7 mm inside the handguard that way)
    table = np.array([L[3] for L in layout])
    starts = [table, np.array([0.0 if L[2] == "spread" else 0.15 * L[3] for L in layout]),
              np.array([0.0 if L[2] == "spread" else 0.5 * L[3] for L in layout])]
    prev = getattr(model, "finger_params", {}).get(side)
    if prev is not None:
        starts.insert(0, prev)
    _, info0 = res(np.clip(starts[0], lo + 1e-6, hi - 1e-6), True)
    sol = None
    for t0 in starts:
        t0 = np.clip(t0, lo + 1e-6, hi - 1e-6)
        s_ = least_squares(res, t0, bounds=(lo, hi), x_scale=10.0, diff_step=1e-5, max_nfev=400, xtol=1e-8, ftol=1e-8)
        if sol is None or s_.cost < sol.cost:
            sol = s_
    # and the thumb lifted off and swung either way from the best (the thumb tip met the rail from inside)
    for sw in (-25.0, 25.0):
        t0 = sol.x.copy()
        for i, L in enumerate(layout):
            if L[0].startswith("finger1-"):
                t0[i] = sw if L[2] == "spread" else (-15.0 if L[0].startswith("finger1-1") else 0.0)
        s_ = least_squares(res, np.clip(t0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi), x_scale=10.0, diff_step=1e-5,
                           max_nfev=400, xtol=1e-8, ftol=1e-8)
        if s_.cost < sol.cost:
            sol = s_
    _, info1 = res(sol.x, True)
    model.finger_basis = {**keep, **basis_of(sol.x)}
    model.finger_params = {**getattr(model, "finger_params", {}), side: sol.x}
    curls = {}
    for (b, ax, kind, tab, _), v in zip(layout, sol.x):
        curls.setdefault(b.split(".")[0], {})[kind] = round(float(v), 1)
    if verbose:
        print(f"fingers {side}: cost {sol.cost:.2f} ({sol.nfev} ev); before {info0}; after {info1}", flush=True)
    return {"curls_deg": curls, "contact_mm": info1, "cost": round(float(sol.cost), 3)}


# The grip each hand holds, as an axis in the gun frame (point mm, direction), for place_hand's starts
GRIP_AXIS = {"R": ((-71.7, 0.0, -39.8), (-0.423, 0.0, -0.906)),     # down the A2 grip, raked 25 deg
             "L": ((285.0, 0.0, 0.0), (1.0, 0.0, 0.0))}             # the bore, under the handguard
PLACE = {"turns_deg": (-45.0, -30.0, -15.0, 0.0, 15.0, 30.0), "slides_mm": (-10.0, 0.0, 10.0),
         "move_sigma_mm": 40.0, "forearm_reach_mm": 90.0,
         # the grasp: the knuckle line along the grip's axis, at the design distance from it and the design
         # height on it (HANDS), so the grip stays in the hand; the hand is free to turn about the grip
         "knuckle_angle_sigma_deg": 12.0, "knuckle_dist_sigma_mm": 4.0, "knuckle_along_sigma_mm": 8.0}


def place_hand(model, x, side):
    """The hand as a rigid body on the carbine (round 2). The palm and thenar (the glove's wrist, metacarpal
    and thumb-base points) with the first 90 mm of the forearm behind the wrist (sleeve, guard) are turned
    about the grip's axis and slid along it from several starts, then fitted (6 degrees of freedom) so they
    touch the grip without entering the gun or the carrier; the best becomes the target (wrist, index and
    little knuckles in the gun frame) the body solve pulls the hand to. Solving this alone first keeps the
    whole-body solve out of the local minimum where the hand straddles the gun (round 2's first attempt: the
    right thenar and wrist 12-15 mm inside the stock's front strut, which hangs 40 mm behind the grip, the
    wrist jammed at 38 deg ulnar)."""
    C_, K, Pp = model.contact, CONTACT, PLACE
    P, _, _ = model.pose(x)
    G = model.gun(x)
    Ms = C_.mats(P)
    g = C_.sets[f"glove_{side}"]
    core = g["core"]
    X = C_.lbs(f"glove_{side}", Ms, core)
    palm = g["palmar"][core]
    W0 = P[f"wrist.{side}"][:3, 3]
    fore = []
    for key in (f"sleeve_{side}", f"guard_{side}"):
        q = C_.sets[key]
        Y = C_.lbs(key, Ms, q["sub"])
        fore.append(Y[np.linalg.norm(Y - W0, axis=1) < Pp["forearm_reach_mm"] / 1000.0])
    F = np.concatenate(fore)
    Gi = np.linalg.inv(G)
    to_gun = lambda A: A @ Gi[:3, :3].T + Gi[:3, 3]
    L0, F0 = to_gun(X), to_gun(F)
    bones = (f"wrist.{side}", f"finger2-1.{side}", f"finger5-1.{side}")
    J0 = np.array([(Gi @ P[b])[:3, 3] for b in bones])
    c0 = L0.mean(0)
    ga, gd = np.array(GRIP_AXIS[side][0]) / 1000.0, np.array(GRIP_AXIS[side][1])
    Kd = np.array(HANDS[side]["K"]) / 1000.0 - ga
    k_along = float(Kd @ gd)
    k_dist = float(np.linalg.norm(Kd - gd * k_along))

    def start(turn, slide):
        R = rv(gd * D(turn))
        return lambda pts: (pts - ga) @ R.T + ga + gd * slide / 1000.0

    def moved(v, pts, s0):
        q = s0(pts)
        c = s0(c0[None])[0]
        return (q - c) @ rv(v[:3]).T + c + v[3:] / 1000.0

    def res(v, s0, total):
        L = moved(v, L0, s0)
        Wd = L @ G[:3, :3].T + G[:3, 3]
        dg = C_.gun_d(Wd, G)
        Fw = moved(v, F0, s0) @ G[:3, :3].T + G[:3, 3]
        out = list(softplus(K["margin_hand_gun_mm"] - dg) / K["pen_sigma_mm"])
        out += list(softplus(K["margin_arm_gun_mm"] - C_.gun_d(Fw, G)) / K["pen_sigma_mm"])
        out += list(softplus(K["margin_carrier_mm"] - C_.car_d(np.r_[Wd, Fw], P)) / K["pen_sigma_mm"])
        out.append((kmin_mean(dg[palm], K["touch_k"]) - K["touch_mm"]) / K["touch_sigma_mm"])
        # how far from where the keypoints put the hand: the wrist and the knuckles, all told
        J = moved(v, J0, s0)
        out += list(((J - J0) * 1000.0 / Pp["move_sigma_mm"]).ravel())
        # the grasp
        kd = J[2] - J[1]
        kd /= np.linalg.norm(kd)
        out.append(math.degrees(math.acos(min(1.0, float(kd @ gd)))) / Pp["knuckle_angle_sigma_deg"])
        Km = (J[1] + J[2]) / 2 - ga
        out.append((np.linalg.norm(Km - gd * (Km @ gd)) - k_dist) * 1000.0 / Pp["knuckle_dist_sigma_mm"])
        out.append((Km @ gd - k_along) * 1000.0 / Pp["knuckle_along_sigma_mm"])
        return np.array(out)
    best = None
    for turn in Pp["turns_deg"]:
        for slide in Pp["slides_mm"]:
            s0 = start(turn, slide)
            sol = least_squares(res, np.zeros(6), args=(s0, False), diff_step=1e-5, max_nfev=150, xtol=1e-9, ftol=1e-9)
            if best is None or sol.cost < best[0].cost:
                best = (sol, s0, turn, slide)
    sol, s0, turn, slide = best
    L = moved(sol.x, L0, s0) @ G[:3, :3].T + G[:3, 3]
    dg = C_.gun_d(L, G)
    Fw = moved(sol.x, F0, s0) @ G[:3, :3].T + G[:3, 3]
    J = moved(sol.x, J0, s0)
    model.hand_local[side] = dict(zip(bones, J))
    out = {"start_turn_deg": turn, "start_slide_mm": slide, "cost": round(float(sol.cost), 2),
           "wrist_moved_mm": round(float(np.linalg.norm(J[0] - J0[0]) * 1000), 1),
           "palm_min_mm": round(float(dg.min()), 2), "palm_touch_mm": round(kmin_mean(dg[palm], K["touch_k"]), 2),
           "forearm_min_mm": round(float(C_.gun_d(Fw, G).min()), 2)}
    print(f"hand {side} placed on the carbine: {out}", flush=True)
    return out


# Round 7, the left hand's wrap (critics: the left hand still reads open on the handguard). Round 4 left the knuckles
# 40 mm above the bore with the palm flat on the top rail; from there the fingers (proximal phalanx ~45 mm, middle ~28)
# reach only down the right face, and fit_fingers could not curl them under (README "Round 4"). Tried first, and
# dropped (README "Round 7"): (1) place_hand's rigid placement with the table curls: the table hook fits round the
# handguard near no design, the fit hung the hand under the gun; (2) a free hand with its fingers fitted round the
# handguard from a grid of designs: it found a clean wrap (palm on the camera face, the tips under the bottom flat),
# but out of the arm's reach: the body solve left the wrist 43 mm off it at the radial limit, the fingers 6-26 mm off
# the gun and the thumb in the rail.
# So the hand is placed through the arm: the left clavicle, shoulder, elbow, forearm twist and wrist (12) and the left
# fingers (20) are fitted together under the whole solve's residuals (keypoints, priors, wrist limits, contact), with
# the old left-hand targets off, plus the grasp: the tips in GRASP["L"]'s band, each finger's front on the gun, the
# curls near a wrap (MCP / PIP from LEFT_ARM's starts, DIP 0.65 PIP).
LEFT_ARM = {"bones": ("clavicle.L", "upperarm01.L", "lowerarm01.L", "lowerarm02.L", "wrist.L"),
            "starts": ((30.0, 90.0), (45.0, 90.0)), "nfev": (60, 80), "curl_sigma_deg": 25.0, "thumb_sigma_deg": 30.0}


def place_left_arm(model, x, verbose=True):
    """Fit the left arm and fingers so the hand wraps the handguard (LEFT_ARM). Returns the new x; sets
    model.hand_local["L"] to the fitted wrist and knuckles (gun frame), model.finger_params["L"], the left fingers
    in model.finger_basis."""
    side, C_, A = "L", model.contact, LEFT_ARM
    idx = np.concatenate([np.arange(model.slices[b][0].start, model.slices[b][0].stop) for b in A["bones"]])
    na = len(idx)
    axes = finger_axes(model, side)
    layout = []
    for b, al in axes.items():
        f, j = b.split(".")[0].split("-")
        j = int(j)
        for ax, kind in al:
            lo_, hi_ = (THUMB_BOUNDS if f == "finger1" else FINGER_BOUNDS)[j] if kind == "flex" else (-25.0, 25.0)
            if kind == "spread" and f == "finger1":
                lo_, hi_ = -40.0, 40.0
            layout.append((b, ax, kind, (f, j), (lo_, hi_)))
    keep = {k: v for k, v in model.finger_basis.items() if not k.endswith("." + side)}
    g = C_.sets[f"glove_{side}"]
    gsel = np.isin(g["chain"], CHAINS[1:]) & (g["palmar"] | np.array([d.split(".")[0].endswith("-3") for d in g["dom"]]))
    gsel |= g["dom"] == f"finger1-3.{side}"       # round 11: GRASP_UNDER_L places the thumb's tip too
    dom, chain, palmar = g["dom"][gsel], g["chain"][gsel], g["palmar"][gsel]
    grasp = [(np.nonzero(dom == f"{f}-3.{side}")[0], terms) for f, terms in GRASP[side].items()]
    touch = [np.nonzero((chain == f) & palmar)[0] for f in CHAINS[1:]]
    lo_b, hi_b = model.bounds()
    lo_t, hi_t = np.array([L[4][0] for L in layout]), np.array([L[4][1] for L in layout])
    lo, hi = np.r_[lo_b[idx], lo_t], np.r_[hi_b[idx], hi_t]

    def basis_of(t):
        fb = {}
        for (b, ax, kind, _, _), v in zip(layout, t):
            m = rv(ax * D(v))
            fb[b] = m if b not in fb else fb[b] @ m
        return {b: rot4(m) for b, m in fb.items()}

    def tab_of(mcp, pip):
        curl = {"finger2": (mcp, pip, 0.65 * pip), "finger3": (mcp, pip, 0.65 * pip),
                "finger4": (mcp + 3.0, pip, 0.65 * pip), "finger5": (mcp + 5.0, pip - 5.0, 0.65 * (pip - 5.0))}
        return np.array([(curl.get(fj[0], CURLS[side][fj[0]])[fj[1] - 1] if kind == "flex" else 0.0)
                         for (_, _, kind, fj, _) in layout])

    def extra(xx, t, tab, detail=False):
        P, _, _ = model.pose(xx)
        G = model.gun(xx)
        X = C_.lbs(f"glove_{side}", C_.mats(P), gsel)
        dg = C_.gun_d(X, G)
        Lg = (X - G[:3, 3]) @ G[:3, :3] * 1000.0
        out, tips = [], {}
        for ii in touch:
            out.append((kmin_mean(dg[ii], 4) - FINGER["touch_mm"]) / 3.0)
        for (ii, terms), f in zip(grasp, GRASP[side]):
            q = Lg[ii].mean(0)
            tips[f] = [round(float(c), 1) for c in q]
            for ax, bound, sgn, sg in terms:
                out.append(float(softplus(sgn * (bound - q["xyz".index(ax)]), 0.5)) / sg)
        vals = {}
        for (b, ax, kind, _, _), val, tb in zip(layout, t, tab):
            vals[(b, kind)] = val
            th_ = b.startswith("finger1-")
            if kind == "flex":
                out.append((val - tb) / (A["thumb_sigma_deg"] if th_ else A["curl_sigma_deg"]))
            else:
                out.append(val / (A["thumb_sigma_deg"] if th_ else FINGER["spread_sigma_deg"]))
        for f in CHAINS[1:]:
            pip, dip = vals[(f"{f}-2.{side}", "flex")], vals[(f"{f}-3.{side}", "flex")]
            out.append((dip - FINGER["dip_pip_ratio"] * pip) / FINGER["dip_sigma_deg"])
        for a2, b2 in (("finger2", "finger3"), ("finger3", "finger4"), ("finger4", "finger5")):
            for j in (1, 2):
                out.append((vals[(f"{a2}-{j}.{side}", "flex")] - vals[(f"{b2}-{j}.{side}", "flex")])
                           / FINGER["neighbour_sigma_deg"])
        if detail:
            return np.array(out), {"tips_gun_mm": tips, "finger_front_to_gun_mm": [round(kmin_mean(dg[ii], 4), 1) for ii in touch]}
        return np.array(out)

    def res(p, tab):
        xx = x.copy()
        xx[idx] = p[:na]
        model.finger_basis = {**keep, **basis_of(p[na:])}
        return np.r_[model.residuals(xx), extra(xx, p[na:], tab)]
    old_full, old_skip, sig_final = model.contact_full, set(model.hand_skip), CONTACT["pen_sigma_mm"]
    model.contact_full, model.hand_skip = True, {side}
    best = None
    t_start = time.perf_counter()
    for mcp, pip in (HOLD["curl_starts"] if HOLD["on"] else A["starts"]):
        tab = tab_of(mcp, pip)
        p = np.clip(np.r_[x[idx], tab], lo + 1e-6, hi - 1e-6)
        for sig, nf in zip((3.0, sig_final), A["nfev"]):
            CONTACT["pen_sigma_mm"] = sig
            sol = least_squares(res, p, args=(tab,), bounds=(lo, hi), x_scale="jac", diff_step=1e-5, max_nfev=nf,
                                xtol=1e-8, ftol=1e-8)
            p = sol.x
        CONTACT["pen_sigma_mm"] = sig_final
        if verbose:
            xx = x.copy()
            xx[idx] = sol.x[:na]
            model.finger_basis = {**keep, **basis_of(sol.x[na:])}
            print(f"  left arm from curls {mcp}/{pip}: cost {sol.cost:.2f} ({time.perf_counter() - t_start:.0f} s), "
                  f"{extra(xx, sol.x[na:], tab, True)[1]}", flush=True)
        if best is None or sol.cost < best[0].cost:
            best = (sol, tab, (mcp, pip))
    sol, tab, start = best
    model.contact_full, model.hand_skip = old_full, old_skip
    x = x.copy()
    x[idx] = sol.x[:na]
    t = sol.x[na:]
    model.finger_basis = {**keep, **basis_of(t)}
    model.finger_params = {**getattr(model, "finger_params", {}), side: t.copy()}
    P, _, _ = model.pose(x)
    G = model.gun(x)
    Gi = np.linalg.inv(G)
    bones = (f"wrist.{side}", f"finger2-1.{side}", f"finger5-1.{side}")
    model.hand_local[side] = {b: (Gi @ P[b])[:3, 3] for b in bones}
    _, info = extra(x, t, tab, True)
    out = {"start_curls": start, "cost": round(float(sol.cost), 2), **info,
           "wrist_flex_dev_deg": [round(v, 1) for v in model.wrist_angles(P, side)],
           "hand_targets_gun_mm": {b: [round(float(c) * 1000, 1) for c in v] for b, v in model.hand_local[side].items()}}
    print(f"left arm placed: {out}", flush=True)
    return x, out


def place_left_under(model, x, verbose=True):
    """Round 11 (HOLD): bring the left hand under the handguard before place_left_arm. From the overhand hold a local
    fit cannot get there (the forearm must turn over and the hand pass through the gun), so the left arm alone
    (clavicle, shoulder, elbow, forearm twist, wrist: 12) is fitted from several forearm twists, the fingers at a
    wrap (HOLD curl_starts[0]), with the whole solve's residuals but the carbine's non-penetration off and the hold's
    palm terms on; the best becomes place_left_arm's start. Returns x."""
    side, A = "L", LEFT_ARM
    idx = np.concatenate([np.arange(model.slices[b][0].start, model.slices[b][0].stop) for b in A["bones"]])
    lo_b, hi_b = model.bounds()
    lo, hi = lo_b[idx], hi_b[idx]
    tw = model.slices["lowerarm02.L"][0].start
    wr = model.slices["wrist.L"][0]
    # the fingers at a wrap while the arm is aimed
    axes = finger_axes(model, side)
    mcp, pip = HOLD["curl_starts"][0]
    curl = {"finger2": (mcp, pip, 0.65 * pip), "finger3": (mcp, pip, 0.65 * pip), "finger4": (mcp + 3, pip, 0.65 * pip),
            "finger5": (mcp + 5, pip - 5, 0.65 * (pip - 5))}
    fb = {}
    for b, al in axes.items():
        f, j = b.split(".")[0].split("-")
        for ax, kind in al:
            if kind == "flex":
                fb[b] = rot4(rv(ax * D(curl.get(f, CURLS[side][f])[int(j) - 1])))
    keep = {k: v for k, v in model.finger_basis.items() if not k.endswith("." + side)}
    old = (model.contact_full, set(model.hand_skip), model.gun_pen, dict(model.finger_basis))
    model.contact_full, model.hand_skip, model.gun_pen = False, {side}, False
    model.finger_basis = {**keep, **fb}
    HOLD["rail_on"] = False

    def res(p):
        xx = x.copy()
        xx[idx] = p
        return model.residuals(xx)
    best, t0, tried = None, time.perf_counter(), []
    for t in HOLD["twist_starts_deg"]:
        p = x[idx].copy()
        p[int(np.nonzero(idx == tw)[0][0])] = D(t)
        p[np.isin(idx, np.arange(wr.start, wr.stop))] = 0.0
        p = np.clip(p, lo + 1e-6, hi - 1e-6)
        sol = least_squares(res, p, bounds=(lo, hi), x_scale="jac", diff_step=1e-5, max_nfev=HOLD["aim_nfev"],
                            xtol=1e-8, ftol=1e-8)
        xx = x.copy()
        xx[idx] = sol.x
        _, info, _ = model.residuals(xx, detail=True)
        tried.append({"twist_start_deg": t, "cost": round(float(sol.cost), 1),
                      "palm_centre_gun_mm": info.get("hold:palm_centre_gun_mm"),
                      "palm_normal_off_up_deg": info.get("hold:palm_normal_off_up_deg")})
        if verbose:
            print(f"  left hand aimed under from twist {t}: {tried[-1]} ({time.perf_counter() - t0:.0f} s)", flush=True)
        if best is None or sol.cost < best.cost:
            best = sol
    model.contact_full, model.hand_skip, model.gun_pen, model.finger_basis = old
    HOLD["rail_on"] = True
    x = x.copy()
    x[idx] = best.x
    return x, tried


def hand_targets_npz(model):
    """Round 7: the left hand's targets (gun frame, m: wrist, index and little MCP) for a saved solver state."""
    return {"hand_L": np.array([model.hand_local["L"][b] for b in ("wrist.L", "finger2-1.L", "finger5-1.L")])}


def joint_px(model, x):
    P, _, _ = model.pose(x)
    out = {}
    for n, (src, tgt, sig, note) in TARGETS.items():
        p = CAM.project([model.point(P, n)])[0]
        out[n] = round(float(math.hypot(p[0] - tgt[0], p[1] - tgt[1])), 1)
    return out


def cost_by_term(model, x):
    """The solve's total cost at x, and the round-1 objective (keypoints, priors, no surfaces) at the same x."""
    r = model.residuals(x)
    c, model.contact = model.contact, None
    r0 = model.residuals(x)
    model.contact = c
    return {"total": round(0.5 * float(r @ r), 2), "round1_objective": round(0.5 * float(r0 @ r0), 2)}


def contact_report(model, x):
    sub, model.contact.subsample = model.contact.subsample, False
    _, info, _ = model.residuals(x, detail=True)
    model.contact.subsample = sub
    return {k: v for k, v in info.items() if k.startswith(("pen:", "touch:", "face:", "hold:"))}


def solve(restarts=3, seed=7, contact=True, refit_fingers=False, continue_from=None, place_left=False, hold=False):
    if hold:        # round 11: the left hand under the handguard (HOLD, GRASP_UNDER_L, place_left_under)
        HOLD["on"] = True
        GRASP["L"] = GRASP_UNDER_L
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
    x = best.x
    stages = {"keypoints_only": {"cost": round(float(best.cost), 3), "joints_px": joint_px(model, x)}}
    fingers_out = None
    if contact and os.path.exists(CONTACT_NPZ):
        # round 2: from the keypoint solution, add the real surfaces. The body first with the palms only (the
        # table curls go through the grip), then the fingers on the grip, then the body with the whole glove,
        # then the fingers again.
        model.contact = Contact(model)
        model.finger_basis = finger_basis(model, None)
        model.contact_full = True
        stages["keypoints_only"]["contact"] = contact_report(model, x)
        model.contact_full = False
        stages["place_hand"] = {"R": place_hand(model, x, "R")}
        if refit_fingers:
            # the body as the last full solve left it (cache/stages/pose_x_pass1.npz), only the fingers again
            z = np.load(os.path.join(PROJECT, "cache", "stages", "pose_x_pass1.npz"))
            x = z["x"]
            model.finger_params = {s: z[f"fp_{s}"] for s in "LR" if f"fp_{s}" in z}
            model.contact_full = True
            fingers_out = {s: fit_fingers(model, x, s) for s in "RL"}
            fingers_out = {s: fit_fingers(model, x, s) for s in "RL"}     # each side sees the other's final fingers
            sol = best
            stages["fingers_refit_on"] = "cache/stages/pose_x_pass1.npz"


        def run(label, nfev=300):
            sol = least_squares(model.residuals, np.clip(x, lo + 1e-9, hi - 1e-9), bounds=(lo, hi), x_scale="jac",
                                diff_step=1e-5, max_nfev=nfev, xtol=1e-8, ftol=1e-8, method="trf")
            print(f"{label}: cost {sol.cost:.2f} ({sol.nfev} evaluations, {time.perf_counter() - t0:.0f} s)", flush=True)
            return sol
        if continue_from:
            # from a saved full solve (its body and fingers): the fingers, one whole-glove pass, the fingers
            z = np.load(continue_from)
            x = z["x"]
            model.finger_params = {s: z[f"fp_{s}"] for s in "LR" if f"fp_{s}" in z}
            if "hand_L" in z.files and not (place_left or hold):      # round 7: the left hand's targets from place_left_arm
                model.hand_local["L"] = dict(zip(("wrist.L", "finger2-1.L", "finger5-1.L"), z["hand_L"]))
                stages["hand_L_targets_from"] = os.path.relpath(continue_from, PROJECT).replace(os.sep, "/")
            model.contact_full = True
            if place_left or hold:
                # round 7: the left arm and fingers fitted round the handguard (place_left_arm), the right fingers
                # refit, then the body at a soft penetration sigma before the usual fingers / whole glove / fingers.
                # Round 11 (--hold): first the left arm aimed under the handguard (place_left_under)
                if hold:
                    x, stages["hold_aim"] = place_left_under(model, x)
                x, stages["place_hand"]["L"] = place_left_arm(model, x)
                fingers_out = {"R": fit_fingers(model, x, "R")}
                sig_final = CONTACT["pen_sigma_mm"]
                CONTACT["pen_sigma_mm"] = 2.0
                x = run("continued: contact, pen sigma 2.0", 80).x
                CONTACT["pen_sigma_mm"] = sig_final
                np.savez(os.path.join(PROJECT, "cache", "stages", "pose_x_left.npz"), x=x,
                         **{f"fp_{k}": v for k, v in getattr(model, "finger_params", {}).items()}, **hand_targets_npz(model))
            fingers_out = {s: fit_fingers(model, x, s) for s in "RL"}
            sol = run("continued: whole glove", 150)
            x = sol.x
            np.savez(os.path.join(PROJECT, "cache", "stages", "pose_x_pass1.npz"), x=x,
                     **{f"fp_{k}": v for k, v in getattr(model, "finger_params", {}).items()}, **hand_targets_npz(model))
            fingers_out = {s: fit_fingers(model, x, s) for s in "RL"}
            stages["continued_from"] = os.path.relpath(continue_from, PROJECT).replace(os.sep, "/")
        if not refit_fingers and not continue_from:
            def run(label, nfev=300):
                sol = least_squares(model.residuals, np.clip(x, lo + 1e-9, hi - 1e-9), bounds=(lo, hi), x_scale="jac",
                                    diff_step=1e-5, max_nfev=nfev, xtol=1e-8, ftol=1e-8, method="trf")
                print(f"{label}: cost {sol.cost:.2f} ({sol.nfev} evaluations, {time.perf_counter() - t0:.0f} s)", flush=True)
                return sol
            # reach: the arm to the placed hand, free to pass through the gun (it must, to get there)
            model.gun_pen = False
            x = run("reach (no carbine penetration)", 100).x
            model.gun_pen = True
            # then the surfaces, stiffening (a stiff start traps the hands; CONTACT's sigma is the last)
            sig_final = CONTACT["pen_sigma_mm"]
            for sig in (2.0, sig_final):
                CONTACT["pen_sigma_mm"] = sig
                sol = run(f"contact, palms, pen sigma {sig}", 120)
                x = sol.x
            for it in range(2):
                fingers_out = {s: fit_fingers(model, x, s) for s in "RL"}
                model.contact_full = True
                sol = run(f"contact pass {it}, whole glove", 150)
                x = sol.x
                np.savez(os.path.join(PROJECT, "cache", "stages", f"pose_x_pass{it}.npz"), x=x,
                         **{f"fp_{k}": v for k, v in getattr(model, "finger_params", {}).items()}, **hand_targets_npz(model))
                rep_ = contact_report(model, x)
                print("  ", {k: v for k, v in rep_.items() if not k.endswith(":min_mm")}, flush=True)
                print("   cost by term:", cost_by_term(model, x), flush=True)
            fingers_out = {s: fit_fingers(model, x, s) for s in "RL"}
        best = sol
        stages["contact"] = {"cost": round(float(sol.cost), 3), "joints_px": joint_px(model, x),
                             "contact": contact_report(model, x)}
    secs = time.perf_counter() - t0
    r, info, P = model.residuals(x, detail=True)
    basis, root_world = model.basis(x)
    basis.update(model.finger_basis or finger_basis(model, P))
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
        "leg_turn_hip_knee_foot_deg": {s: [round(v, 1) for v in model.leg_turn(P, s)] for s in "LR"},
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
        "residual_terms": {k: (round(float(v), 2) if isinstance(v, (int, float, np.floating)) else v)
                           for k, v in info.items() if not k.startswith("joint:")},
        "stages": stages,
        "fingers": fingers_out,
        "solve": {"cost": round(0.5 * float(r @ r), 3), "params": model.n, "residuals": int(len(r)),
                  "restarts": restarts, "seconds": round(secs, 1), "status": best.message},
        "finger_curls_deg": CURLS if fingers_out is None else {s: v["curls_deg"] for s, v in fingers_out.items()},
    }
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"joints_residual_px": {n: j["residual_px"] for n, j in joints.items()}, **readback,
                      "solve": out["solve"]}, indent=1))
    return 0


def build_face_targets(tag="after"):
    """scripts/stages/face_targets.json: MediaPipe's face landmarks on the reference, each tied to the body-mesh
    point MediaPipe found for the same landmark on the model's head render (head.py's correspondences:
    cache/parts/head_fit/<tag>/, raycast through the hero camera onto the posed head mesh it was rendered
    from). The face term in the solve reprojects those mesh points (skinned with the body's own weights)."""
    sys.path.insert(0, os.path.join(PROJECT, "scripts", "parts"))
    import head as Hd
    d = os.path.join(Hd.WORK, tag)
    E = dict(np.load(os.path.join(d, "export.npz")))
    ref_xy = Hd.mp_landmarks(Hd.REF_CROP)
    mod_xy = Hd.mp_landmarks(os.path.join(d, "model_head_grey.png"))
    use = [i for i in range(468) if i not in Hd.FOREHEAD and i not in Hd.CHIN_BOTTOM]
    hits = Hd.raycast(CAM, mod_xy[use], E["P0"], E["tris"])
    med = float(np.median([h[2] for h in hits if h is not None]))
    oval = set(Hd.JAW_OVAL)
    marks, vids = [], set()
    for i, h in zip(use, hits):
        if h is None or h[2] > med + 40.0:
            continue
        tri = [int(E["idx"][v]) for v in E["tris"][h[0]]]
        vids.update(tri)
        marks.append({"mp": i, "verts": tri, "bary": [round(float(b), 6) for b in h[1]],
                      "ref_px": [round(float(v), 2) for v in ref_xy[i]], "weight": 1.5 if i in oval else 1.0})
    out = {"doc": "Face landmarks for pose_solve.py's face term: MediaPipe on ref/crop_head_face.png (ref_px, full "
                  "frame) and the Body.Mesh point (3 vertex ids + barycentric) MediaPipe found for the same landmark "
                  f"on the model's head render (cache/parts/head_fit/{tag}, head.py). Forehead rows, iris and chin-"
                  "bottom points left out as in head.py. Written by pose_solve.py --face-targets.",
           "source": tag, "landmarks": marks, "vertex_ids": sorted(vids)}
    with open(FACE_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=0)
    print(f"face targets: {len(marks)} landmarks on {len(vids)} vertices -> {os.path.relpath(FACE_JSON, PROJECT)}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--restarts", type=int, default=3)
    ap.add_argument("--face-targets", action="store_true", help="rebuild face_targets.json from head.py's fit")
    ap.add_argument("--no-contact", action="store_true", help="round 1's objective only (no surfaces, table curls)")
    ap.add_argument("--continue-from", help="a saved solve (cache/stages/pose_x_pass1.npz form): fingers, one "
                                           "whole-glove body pass, fingers")
    ap.add_argument("--refit-fingers", action="store_true",
                    help="keep the body of the last full solve (cache/stages/pose_x_pass1.npz), fit only the fingers")
    ap.add_argument("--place-left", action="store_true",
                    help="with --continue-from (round 7): fit the left arm and fingers round the handguard first")
    ap.add_argument("--hold", action="store_true",
                    help="with --continue-from (round 11): the left hand under the handguard (HOLD), aimed, then placed")
    a = ap.parse_args()
    if a.face_targets:
        sys.exit(build_face_targets())
    sys.exit(solve(a.restarts, contact=not a.no_contact, refit_fingers=a.refit_fingers, continue_from=a.continue_from,
                   place_left=a.place_left, hold=a.hold))
