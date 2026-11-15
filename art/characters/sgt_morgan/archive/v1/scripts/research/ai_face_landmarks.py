#!/usr/bin/env python3
"""Run MediaPipe FaceLandmarker (478 pts, 52 blendshapes, head pose matrix) on an image.

Usage:
  venv/bin/python -I ai_face_landmarks.py <image> <out_prefix>
Writes:
  <out_prefix>_landmarks.json  : normalized xy(z) landmarks, blendshapes, 4x4 head matrix,
                                 and a set of likeness ratios (pose-robust where possible)
  <out_prefix>_overlay.png     : landmarks drawn on the image
  <out_prefix>_mesh.obj        : the 478-vertex face mesh with MediaPipe canonical triangulation
                                 (x,y in image pixels, z in pixel-equivalent depth units)
"""
import sys, json, time, urllib.request, os
import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL = "/home/user/sgt_morgan/assets/ai/mediapipe/face_landmarker.task"
TESS_URL = ("https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/"
            "mediapipe/modules/face_geometry/data/canonical_face_model.obj")
CANON_OBJ = "/home/user/sgt_morgan/assets/ai/mediapipe/canonical_face_model.obj"

# Landmark indices (MediaPipe 468 topology)
IDX = dict(
    chin=152, forehead_top=10, nose_tip=1, nose_bridge=6, subnasale=2,
    left_eye_outer=263, left_eye_inner=362, right_eye_outer=33, right_eye_inner=133,
    left_eye_top=386, left_eye_bottom=374, right_eye_top=159, right_eye_bottom=145,
    mouth_left=291, mouth_right=61, upper_lip_top=0, lower_lip_bottom=17,
    upper_lip_bottom=13, lower_lip_top=14,
    nose_left_ala=358, nose_right_ala=129,
    left_cheek=454, right_cheek=234,  # face contour at ear level
    left_brow_inner=336, right_brow_inner=107, left_brow_outer=300, right_brow_outer=70,
    left_jaw=397, right_jaw=172,  # gonial-angle region on contour
)
# NOTE: MediaPipe "left" is the subject's left (image right for a frontal face).


def load_canonical_faces():
    if not os.path.exists(CANON_OBJ):
        urllib.request.urlretrieve(TESS_URL, CANON_OBJ)
    faces = []
    with open(CANON_OBJ) as f:
        for line in f:
            if line.startswith("f "):
                faces.append([int(p.split("/")[0]) for p in line.split()[1:]])
    return faces


def dist(a, b):
    return float(np.linalg.norm(a - b))


def main(img_path, out_prefix):
    t0 = time.time()
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    opts = vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL),
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
        num_faces=1,
        min_face_detection_confidence=0.3,
    )
    det = vision.FaceLandmarker.create_from_options(opts)
    res = det.detect(mp_img)
    t1 = time.time()
    if not res.face_landmarks:
        print("NO FACE FOUND")
        return 2
    lm = res.face_landmarks[0]
    pts = np.array([[p.x, p.y, p.z] for p in lm], dtype=np.float64)  # normalized
    px = pts.copy()
    px[:, 0] *= w
    px[:, 1] *= h
    px[:, 2] *= w  # z is scaled roughly like x

    P = {k: px[v] for k, v in IDX.items()}
    face_h = dist(P["forehead_top"], P["chin"])
    ipd_outer = dist(P["left_eye_outer"], P["right_eye_outer"])
    ipd_inner = dist(P["left_eye_inner"], P["right_eye_inner"])
    face_w = dist(P["left_cheek"], P["right_cheek"])
    mouth_w = dist(P["mouth_left"], P["mouth_right"])
    nose_w = dist(P["nose_left_ala"], P["nose_right_ala"])
    nose_len = dist(P["nose_bridge"], P["nose_tip"])
    eye_to_chin = dist((P["left_eye_inner"] + P["right_eye_inner"]) / 2, P["chin"])
    eye_to_mouth = dist((P["left_eye_inner"] + P["right_eye_inner"]) / 2,
                        (P["upper_lip_top"] + P["lower_lip_bottom"]) / 2)
    nose_to_chin = dist(P["subnasale"], P["chin"])
    jaw_w = dist(P["left_jaw"], P["right_jaw"])
    eye_h = (dist(P["left_eye_top"], P["left_eye_bottom"]) + dist(P["right_eye_top"], P["right_eye_bottom"])) / 2
    eye_w = (dist(P["left_eye_outer"], P["left_eye_inner"]) + dist(P["right_eye_outer"], P["right_eye_inner"])) / 2
    lip_h = dist(P["upper_lip_top"], P["lower_lip_bottom"])
    ratios = {
        "face_width_over_height": face_w / face_h,
        "jaw_width_over_face_width": jaw_w / face_w,
        "ipd_inner_over_face_width": ipd_inner / face_w,
        "ipd_outer_over_face_width": ipd_outer / face_w,
        "mouth_width_over_ipd_outer": mouth_w / ipd_outer,
        "nose_width_over_ipd_inner": nose_w / ipd_inner,
        "nose_length_over_face_height": nose_len / face_h,
        "eye_to_mouth_over_face_height": eye_to_mouth / face_h,
        "nose_to_chin_over_face_height": nose_to_chin / face_h,
        "eye_to_chin_over_face_height": eye_to_chin / face_h,
        "eye_aspect_h_over_w": eye_h / eye_w,
        "lip_height_over_mouth_width": lip_h / mouth_w,
        "nose_length_over_nose_width": nose_len / nose_w,
    }
    mat = np.array(res.facial_transformation_matrixes[0]) if res.facial_transformation_matrixes else None
    pose = {}
    if mat is not None:
        R = mat[:3, :3]
        # ZYX euler (yaw about Y, pitch about X, roll about Z) in degrees
        yaw = np.degrees(np.arctan2(R[0, 2], R[2, 2]))
        pitch = np.degrees(np.arcsin(-R[1, 2]))
        roll = np.degrees(np.arctan2(R[1, 0], R[1, 1]))
        pose = {"yaw_deg": float(yaw), "pitch_deg": float(pitch), "roll_deg": float(roll)}
    bs = {c.category_name: float(c.score) for c in res.face_blendshapes[0]} if res.face_blendshapes else {}

    out = {
        "image": img_path, "width": w, "height": h,
        "runtime_s": t1 - t0,
        "model": MODEL,
        "landmarks_normalized_xyz": pts.tolist(),
        "landmarks_px_xyz": px.tolist(),
        "key_indices": IDX,
        "ratios": ratios,
        "head_pose_from_matrix": pose,
        "facial_transformation_matrix": mat.tolist() if mat is not None else None,
        "blendshapes": bs,
    }
    with open(out_prefix + "_landmarks.json", "w") as f:
        json.dump(out, f, indent=1)

    # overlay
    ov = img.copy()
    for i, p in enumerate(px):
        cv2.circle(ov, (int(p[0]), int(p[1])), 1, (0, 255, 0), -1)
    for k, v in IDX.items():
        p = px[v]
        cv2.circle(ov, (int(p[0]), int(p[1])), 3, (0, 0, 255), -1)
    cv2.imwrite(out_prefix + "_overlay.png", ov)

    # OBJ of the 468 tessellated landmarks (first 468; 10 iris points excluded)
    faces = load_canonical_faces()
    with open(out_prefix + "_mesh.obj", "w") as f:
        f.write("# MediaPipe face landmarks as mesh; x right, y down (image), z toward camera negative\n")
        for p in px[:468]:
            f.write(f"v {p[0]:.3f} {-p[1]:.3f} {-p[2]:.3f}\n")
        for face in faces:
            if max(face) <= 468:
                f.write("f " + " ".join(str(i) for i in face) + "\n")
    print(json.dumps({"runtime_s": round(t1 - t0, 3), "pose": pose, "ratios": ratios,
                      "top_blendshapes": sorted(bs.items(), key=lambda kv: -kv[1])[:8]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
