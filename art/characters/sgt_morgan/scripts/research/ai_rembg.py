#!/usr/bin/env python3
"""rembg via Python API (CLI has incomplete deps under py3.13).
Usage: U2NET_HOME=<models dir> venv/bin/python -I ai_rembg.py <image> <out_prefix> [model]
Writes <out_prefix>_<model>_cutout.png (RGBA) and <out_prefix>_<model>_mask.png (L).
"""
import sys, time
from PIL import Image
from rembg import remove, new_session

img_path, out_prefix = sys.argv[1], sys.argv[2]
model = sys.argv[3] if len(sys.argv) > 3 else "u2net"
t0 = time.time()
sess = new_session(model)
t1 = time.time()
img = Image.open(img_path).convert("RGB")
cut = remove(img, session=sess)
mask = remove(img, session=sess, only_mask=True)
t2 = time.time()
cut.save(f"{out_prefix}_{model}_cutout.png")
mask.save(f"{out_prefix}_{model}_mask.png")
print(f"model={model} session(load/download) {t1-t0:.1f}s, 2 inferences {t2-t1:.1f}s, size {img.size}")
