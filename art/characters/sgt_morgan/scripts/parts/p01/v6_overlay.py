"""Spec 01's V6 check (§1.3, §8.2): the seated, posed last's silhouette from the hero camera against the reference
boot's (spec 17's mask recipe, cache/masks/boot_<S>.png or ref/masks/), a figure and the numbers.

  python -I scripts/parts/p01/v6_overlay.py RENDER.png MASK.png X0 Y0 X1 Y1 SCALE OUT.png [ROW_LO ROW_HI]

The render is a crop of the hero frame, the box (X0, Y0)-(X1, Y1) at SCALE (render.py's equivalent camera); its alpha
is the last's silhouette. Rows above ROW_LO (the trouser cuff) and below ROW_HI (the sole line) are left out: the mask
stops there. Prints a JSON line: the share of the last's pixels inside the boot (full-frame pixels), the largest
excursion outside it in px, and the boot's pixels the last leaves free.
"""
import json
import sys

import numpy as np
from PIL import Image


def main(argv):
    render, mask, x0, y0, x1, y1, scale, out = argv[:8]
    x0, y0, x1, y1, scale = int(x0), int(y0), int(x1), int(y1), float(scale)
    lo, hi = (int(argv[8]), int(argv[9])) if len(argv) > 9 else (y0, y1)
    im = Image.open(render).convert("RGBA")
    w, h = x1 - x0, y1 - y0
    a = np.array(im.resize((w, h), Image.BILINEAR))[..., 3] > 127
    m = np.array(Image.open(mask).convert("L"))[y0:y1, x0:x1] > 127
    rows = np.arange(y0, y1)[:, None] * np.ones((1, w), bool)
    band = (rows >= lo) & (rows <= hi)
    last, boot = a & band, m & band
    inside = (last & boot).sum() / max(last.sum(), 1)
    # excursion: the distance (px) of each last pixel outside the boot to the nearest boot pixel
    out_px = np.argwhere(last & ~boot)
    bp = np.argwhere(boot)
    worst = 0.0
    if len(out_px) and len(bp):
        for i in range(0, len(out_px), 2000):
            d = np.sqrt(((out_px[i:i + 2000, None, :] - bp[None, :, :]) ** 2).sum(-1)).min(axis=1)
            worst = max(worst, float(d.max()))
    free = (boot & ~last).sum() / max(boot.sum(), 1)
    ref = Image.open("ref/reference_full.png").convert("RGB")   # run from the project folder
    crop = ref.crop((x0, y0, x1, y1)).resize((int(w * scale), int(h * scale)), Image.BICUBIC)
    big = np.array(crop).astype(float)
    A = np.array(im)[..., 3] > 127
    M = np.array(Image.fromarray(m.astype(np.uint8) * 255).resize(A.shape[::-1], Image.NEAREST)) > 127
    big[A] = 0.55 * big[A] + 0.45 * np.array([60.0, 200.0, 255.0])
    edge = M ^ np.roll(M, 1, axis=0) | M ^ np.roll(M, 1, axis=1)
    big[edge] = [255.0, 80.0, 40.0]
    Image.fromarray(np.clip(big, 0, 255).astype(np.uint8)).save(out)
    print(json.dumps({"inside": round(float(inside), 4), "worst_px": round(worst, 2), "boot_free": round(float(free), 4),
                      "last_px": int(last.sum()), "boot_px": int(boot.sum()), "overlay": out}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
