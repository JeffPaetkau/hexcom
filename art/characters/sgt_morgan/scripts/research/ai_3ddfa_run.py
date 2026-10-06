#!/usr/bin/env python3
"""Run 3DDFA_V2 (MobileNet-V1, 120x120, BFM 40 shape + 10 exp) on a face image WITHOUT the
Cython FaceBoxes/Sim3DR extensions: face box comes from a JSON of MediaPipe landmarks (or a
manual bbox), rendering is done by projecting vertices with OpenCV.

Usage:
  venv/bin/python -I ai_3ddfa_run.py <image> <out_prefix> [--bbox x1,y1,x2,y2 | --mp-json landmarks.json]
Writes:
  <out_prefix>_dense.obj   38365-vertex BFM mesh, image-pixel units, y up, z toward camera, vertex colors
  <out_prefix>_lm68.json   68 sparse landmarks (px), pose (yaw/pitch/roll), 62 params (12 pose + 40 shp + 10 exp)
  <out_prefix>_overlay.png dense vertex splat + 68 landmarks + bbox drawn on the image
"""
import sys, os, json, time, argparse
import numpy as np
import cv2
import yaml

REPO = "/home/user/sgt_morgan/assets/ai/3ddfa_v2/repo"
sys.path.insert(0, REPO)  # downloaded code; cwd stays outside the repo

import torch  # noqa: E402
torch.set_num_threads(4)
from TDDFA import TDDFA  # noqa: E402
from utils.pose import calc_pose  # noqa: E402
from utils.tddfa_util import _parse_param  # noqa: E402


def bbox_from_mp(json_path):
    with open(json_path) as f:
        d = json.load(f)
    px = np.array(d["landmarks_px_xyz"])[:468, :2]
    x1, y1 = px.min(0)
    x2, y2 = px.max(0)
    # FaceBoxes-style boxes are a bit tighter than the mesh contour at the top (hairline) – keep as is
    return [float(x1), float(y1), float(x2), float(y2)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("out_prefix")
    ap.add_argument("--bbox", default=None)
    ap.add_argument("--mp-json", default=None)
    ap.add_argument("--cfg", default="mb1_120x120")
    a = ap.parse_args()

    img = cv2.imread(a.image)
    h, w = img.shape[:2]
    if a.bbox:
        bbox = [float(v) for v in a.bbox.split(",")]
    elif a.mp_json:
        bbox = bbox_from_mp(a.mp_json)
    else:
        casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = casc.detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.1, 5)
        if len(faces) == 0:
            print("no face from Haar; pass --bbox")
            return 2
        x, y, bw, bh = max(faces, key=lambda r: r[2] * r[3])
        bbox = [float(x), float(y), float(x + bw), float(y + bh)]
    print("bbox", bbox)

    cfg = yaml.safe_load(open(os.path.join(REPO, "configs", a.cfg + ".yml")))
    cfg["checkpoint_fp"] = os.path.join(REPO, cfg["checkpoint_fp"])
    cfg["bfm_fp"] = os.path.join(REPO, cfg["bfm_fp"])
    t0 = time.time()
    tddfa = TDDFA(gpu_mode=False, **cfg)
    t1 = time.time()
    param_lst, roi_box_lst = tddfa(img, [bbox])
    ver_dense = tddfa.recon_vers(param_lst, roi_box_lst, dense_flag=True)[0]   # 3 x 38365
    ver_sparse = tddfa.recon_vers(param_lst, roi_box_lst, dense_flag=False)[0]  # 3 x 68
    t2 = time.time()
    param = param_lst[0]
    P, pose = calc_pose(param)  # pose = [yaw, pitch, roll] degrees
    R, offset, alpha_shp, alpha_exp = _parse_param(param)
    tri = tddfa.tri  # (n_tri, 3), zero-based

    # --- OBJ with vertex colors sampled from the image ---
    xs = np.clip(np.round(ver_dense[0]).astype(int), 0, w - 1)
    ys = np.clip(np.round(ver_dense[1]).astype(int), 0, h - 1)
    cols = img[ys, xs][:, ::-1] / 255.0  # BGR->RGB
    with open(a.out_prefix + "_dense.obj", "w") as f:
        f.write(f"# 3DDFA_V2 dense BFM mesh from {a.image}; units=image px; y flipped up; z toward camera\n")
        for i in range(ver_dense.shape[1]):
            x, y, z = ver_dense[:, i]
            r, g, b = cols[i]
            f.write(f"v {x:.3f} {h - y:.3f} {z:.3f} {r:.4f} {g:.4f} {b:.4f}\n")
        for t in tri:
            # 3DDFA tri winding: reverse for outward normals after the y flip
            f.write(f"f {t[2] + 1} {t[1] + 1} {t[0] + 1}\n")

    # --- overlay ---
    ov = img.copy()
    cv2.rectangle(ov, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (255, 200, 0), 2)
    rb = roi_box_lst[0]
    cv2.rectangle(ov, (int(rb[0]), int(rb[1])), (int(rb[2]), int(rb[3])), (0, 200, 255), 1)
    zs = ver_dense[2]
    zn = (zs - zs.min()) / (zs.max() - zs.min() + 1e-6)
    for i in range(0, ver_dense.shape[1], 6):
        c = int(zn[i] * 255)
        cv2.circle(ov, (int(ver_dense[0, i]), int(ver_dense[1, i])), 1, (255 - c, 60, c), -1)
    for i in range(ver_sparse.shape[1]):
        cv2.circle(ov, (int(ver_sparse[0, i]), int(ver_sparse[1, i])), 3, (0, 255, 0), -1)
    cv2.putText(ov, f"yaw {pose[0]:.1f} pitch {pose[1]:.1f} roll {pose[2]:.1f}", (10, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imwrite(a.out_prefix + "_overlay.png", ov)

    # --- side view render of the dense mesh (orthographic, x->depth) to judge profile ---
    side = np.zeros((h, w, 3), np.uint8)
    zc = ver_dense[2] - ver_dense[2].mean()
    for i in range(ver_dense.shape[1]):
        X = int(w / 2 + zc[i])  # depth becomes horizontal
        Y = int(ver_dense[1, i])
        if 0 <= X < w and 0 <= Y < h:
            side[Y, X] = (int(cols[i][2] * 255), int(cols[i][1] * 255), int(cols[i][0] * 255))
    cv2.imwrite(a.out_prefix + "_sideview.png", side)

    out = {
        "image": a.image, "bbox_used": bbox, "roi_box": [float(v) for v in rb],
        "model_load_s": t1 - t0, "infer_and_recon_s": t2 - t1,
        "pose_yaw_pitch_roll_deg": [float(v) for v in pose],
        "landmarks68_px_xyz": ver_sparse.T.tolist(),
        "param62": param.tolist(), "alpha_shp40": alpha_shp.flatten().tolist(),
        "alpha_exp10": alpha_exp.flatten().tolist(),
        "n_vertices": int(ver_dense.shape[1]), "n_tris": int(tri.shape[0]),
        "dense_bbox_px": [float(ver_dense[0].min()), float(ver_dense[1].min()),
                          float(ver_dense[0].max()), float(ver_dense[1].max())],
        "dense_depth_range_px": float(ver_dense[2].max() - ver_dense[2].min()),
    }
    with open(a.out_prefix + "_lm68.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("landmarks68_px_xyz", "param62")}, indent=1))


if __name__ == "__main__":
    sys.exit(main() or 0)
