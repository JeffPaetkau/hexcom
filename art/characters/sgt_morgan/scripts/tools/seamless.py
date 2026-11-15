"""Make a painted swatch tile seamlessly by the half-offset blend (notes/research_canitcode.md: "a one-metre
patch painted by GPT, made seamless by a half-offset blend"), and report its statistics.

    "$SGT_PYIMG" -I scripts/tools/seamless.py gen/R000/cordura_olive_worn.png gen/R000/cordura_olive_worn_seamless.png

The image is rolled by half its size on both axes (its old edges meet in a cross through the middle, its
old centre now lies on the edges, which therefore tile), and the original is blended over the rolled copy
with a weight that is 1 on that cross and falls to 0 a quarter of the way out (a smooth cosine window),
so the edges come from the rolled copy (seamless by construction) and the middle from the original. Where
the two copies blend the weave would ghost, so the blend is done on the low frequencies only and the high
frequencies (weave, specks) are taken from whichever copy dominates, cut along the weight's 0.5 contour.
Prints the edge differences (left-right, top-bottom) against the mean neighbour difference, and the mean
colour and linear luminance the materials library normalises by (mat_catalogue.GEN_TEXTURES).
"""
import sys

import numpy as np
from PIL import Image, ImageFilter


def _lin(a):
    a = a / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def seam_stats(a):
    lr = np.abs(a[:, 0] - a[:, -1]).mean()
    tb = np.abs(a[0] - a[-1]).mean()
    nb = (np.abs(np.diff(a, axis=1)).mean() + np.abs(np.diff(a, axis=0)).mean()) / 2.0
    return lr, tb, nb


def make_seamless(img, blur_px=12):
    a = np.asarray(img.convert("RGB")).astype(np.float64)
    h, w, _ = a.shape
    r = np.roll(a, (h // 2, w // 2), axis=(0, 1))
    y = np.abs(np.arange(h) - h / 2.0) / (h / 2.0)       # 0 at the cross through the middle, 1 at the edges
    x = np.abs(np.arange(w) - w / 2.0) / (w / 2.0)
    wy = np.clip(1.0 - y / 0.5, 0.0, 1.0)                   # 1 on the cross, 0 a quarter of the way out
    wx = np.clip(1.0 - x / 0.5, 0.0, 1.0)
    wgt = np.maximum(0.5 - 0.5 * np.cos(np.pi * wy)[:, None], 0.5 - 0.5 * np.cos(np.pi * wx)[None, :])
    # the rolled copy tiles at its edges (they are the original's middle) but carries the original's old
    # edges as a seam on the cross through its middle; there the original (continuous in its middle) takes
    # over: wgt is the ORIGINAL's weight
    wgt = wgt[..., None]

    def low(arr):
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        return np.asarray(im.filter(ImageFilter.GaussianBlur(blur_px))).astype(np.float64)
    la, lr_ = low(a), low(r)
    lo = lr_ * (1.0 - wgt) + la * wgt
    # the detail switches copy over a narrow band about the weight's 0.5 contour (a blend there would ghost
    # the weave; a hard cut would draw a line)
    k = np.clip((wgt - 0.4) / 0.2, 0.0, 1.0)
    hi = (r - lr_) * (1.0 - k) + (a - la) * k
    out = lo + hi
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))


def main(src, dst):
    im = Image.open(src)
    a0 = np.asarray(im.convert("RGB")).astype(np.float64)
    out = make_seamless(im)
    out.save(dst)
    a1 = np.asarray(out).astype(np.float64)
    for tag, a in (("source", a0), ("seamless", a1)):
        lr, tb, nb = seam_stats(a)
        print(f"{tag:9s} edge diff L-R {lr:.1f}, T-B {tb:.1f}, neighbours {nb:.1f}")
    lin = _lin(a1)
    y = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    print("mean sRGB", a1.reshape(-1, 3).mean(0).round(1).tolist(), "mean linear", lin.reshape(-1, 3).mean(0).round(5).tolist(),
          "luminance mean", round(float(y.mean()), 5), "sd", round(float(y.std()), 5))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
