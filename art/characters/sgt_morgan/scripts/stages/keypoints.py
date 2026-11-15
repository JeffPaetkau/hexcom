"""2D pose keypoints of the soldier in the reference, for the hero-pose solve (round 0).

MediaPipe's pose landmarker (heavy) runs on the soldier's box of `ref/reference_full.png`, padded and
upscaled, at a few scales; the landmarks are mapped back to full-frame pixels and averaged over the
runs, with their spread kept as an uncertainty. Take 1's hand-read landmarks
(archive/v1/notes/analysis_pose_proportions.md and analysis_consolidated.md) are stored beside them,
because the network reads a figure in bulky armour by its outline: where they disagree the solve
weighs the hand reading (pose.py says which it uses per joint).

  "$SGT_PYIMG" -I scripts/stages/keypoints.py           -> scripts/stages/ref_keypoints.json

Needs assets/ai/mediapipe/pose_landmarker_heavy.task (storage.googleapis.com/mediapipe-models/
pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task).
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
REF = os.path.join(PROJECT, "ref", "reference_full.png")
MODEL = os.path.join(PROJECT, "assets", "ai", "mediapipe", "pose_landmarker_heavy.task")
OUT = os.path.join(HERE, "ref_keypoints.json")
BOX = (520, 0, 1080, 941)          # the soldier (x 580-1020) with room either side
SCALES = (1.0, 1.5, 2.0)

NAMES = ["nose", "eye_inner_l", "eye_l", "eye_outer_l", "eye_inner_r", "eye_r", "eye_outer_r", "ear_l", "ear_r",
         "mouth_l", "mouth_r", "shoulder_l", "shoulder_r", "elbow_l", "elbow_r", "wrist_l", "wrist_r",
         "pinky_l", "pinky_r", "index_l", "index_r", "thumb_l", "thumb_r", "hip_l", "hip_r", "knee_l", "knee_r",
         "ankle_l", "ankle_r", "heel_l", "heel_r", "foot_index_l", "foot_index_r"]
# MediaPipe's "left" is the person's own left, as here (CLAUDE.md rule 1).

# Take 1's hand reading (full-frame px; soldier's own sides), the joint centres the analysts placed.
HAND = {
    "skull_top": (808, 20), "eye_r": (800, 77), "eye_l": (832, 77), "nose": (815, 90), "chin": (816, 131),
    "ear_r": (762, 98),
    "shoulder_r": (675, 200), "shoulder_l": (935, 200), "elbow_r": (632, 328), "elbow_l": (958, 352),
    "wrist_r": (698, 345), "wrist_l": (870, 440),
    "hip_r_drawn": (768, 505), "hip_l_drawn": (862, 505),
    "knee_r": (727, 650), "knee_l": (890, 657), "ankle_r": (732, 855), "ankle_l": (928, 858),
    "toe_r": (631, 884), "heel_r": (767, 892), "toe_l": (950, 907), "heel_l": (910, 897),
    "sole_r": (740, 895), "sole_l": (928, 907),
    "r_index_mcp": (727, 355), "r_index_tip": (750, 398), "l_palm": (840, 460), "l_thumb_tip": (846, 447),
    "carbine_butt": (695, 268), "carbine_muzzle": (903, 570), "carbine_grip": (740, 395),
    "carbine_handguard_rear": (793, 402), "carbine_handguard_front": (873, 512),
}


def run():
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode
    im = Image.open(REF).convert("RGB").crop(BOX)
    opts = PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODEL), running_mode=RunningMode.IMAGE,
                                 num_poses=1, min_pose_detection_confidence=0.3, min_pose_presence_confidence=0.3)
    runs = []
    with PoseLandmarker.create_from_options(opts) as lm:
        for s in SCALES:
            w, h = round(im.width * s), round(im.height * s)
            arr = np.asarray(im.resize((w, h), Image.LANCZOS))
            res = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(arr)))
            if not res.pose_landmarks:
                print(f"scale {s}: no pose")
                continue
            pts = [(BOX[0] + p.x * im.width, BOX[1] + p.y * im.height, p.visibility) for p in res.pose_landmarks[0]]
            runs.append(np.array(pts))
            print(f"scale {s}: {len(pts)} landmarks")
    if not runs:
        raise SystemExit("MediaPipe found no pose")
    A = np.stack(runs)
    mean, sd = A[:, :, :2].mean(0), A[:, :, :2].std(0).max(axis=1)
    vis = A[:, :, 2].mean(0)
    mpk = {n: {"xy": [round(float(mean[i, 0]), 1), round(float(mean[i, 1]), 1)], "sd_px": round(float(sd[i]), 1),
               "visibility": round(float(vis[i]), 3)} for i, n in enumerate(NAMES)}
    diff = {n: round(float(np.hypot(*(np.array(mpk[n]["xy"]) - HAND[n]))), 1) for n in NAMES if n in HAND}
    out = {"doc": __doc__.split("\n\n")[0], "image": "ref/reference_full.png", "box": BOX, "scales": SCALES,
           "convention": "full-frame continuous px, x right, y down; soldier's own left/right",
           "mediapipe": mpk, "hand": {k: list(v) for k, v in HAND.items()}, "mediapipe_vs_hand_px": diff}
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
    for n, d in diff.items():
        print(f"{n:12s} mediapipe {mpk[n]['xy']} hand {HAND[n]} diff {d} px (sd {mpk[n]['sd_px']})")
    return 0


if __name__ == "__main__":
    sys.exit(run())
