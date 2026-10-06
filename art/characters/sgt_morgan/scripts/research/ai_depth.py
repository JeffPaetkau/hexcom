#!/usr/bin/env python3
"""Depth Anything V2 Small (HF transformers, CPU) on an image.

Usage: venv/bin/python -I ai_depth.py <image> <out_prefix>
Writes <out_prefix>_depth16.png (16-bit, relative inverse depth, larger = nearer),
       <out_prefix>_depth_vis.png (8-bit colormap preview).
"""
import sys, time
import numpy as np
import torch
from PIL import Image
import cv2

MODEL_DIR = "/home/user/sgt_morgan/assets/ai/depth_anything_v2_small"


def main(img_path, out_prefix):
    from transformers import AutoImageProcessor, AutoModelForDepthEstimation
    torch.set_num_threads(4)
    t0 = time.time()
    proc = AutoImageProcessor.from_pretrained(MODEL_DIR)
    model = AutoModelForDepthEstimation.from_pretrained(MODEL_DIR).eval()
    t1 = time.time()
    img = Image.open(img_path).convert("RGB")
    inputs = proc(images=img, return_tensors="pt")
    with torch.no_grad():
        out = model(**inputs)
    pred = out.predicted_depth  # (1, H', W') relative inverse depth
    pred = torch.nn.functional.interpolate(pred.unsqueeze(1), size=img.size[::-1],
                                           mode="bicubic", align_corners=False)[0, 0].numpy()
    t2 = time.time()
    d = (pred - pred.min()) / (pred.max() - pred.min() + 1e-8)
    cv2.imwrite(out_prefix + "_depth16.png", (d * 65535).astype(np.uint16))
    vis = cv2.applyColorMap((d * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    cv2.imwrite(out_prefix + "_depth_vis.png", vis)
    print(f"load {t1-t0:.1f}s, infer+resize {t2-t1:.1f}s, input tensor {tuple(inputs['pixel_values'].shape)}, "
          f"raw pred {tuple(out.predicted_depth.shape)}, out {img.size}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
