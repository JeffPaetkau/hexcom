"""The emblem's inner mark from R003 (critic m34, round 8): gen/R003/emblem_mask.png without its outer triangle.

The drawn shoulder plate carries only a light mark (an X under a chevron) on the blue-grey plate; R003 drew the
same mark inside a light triangular outline, which the decal printed as a light pointed outline inside the
plate's rim (the critics read a "pointed V or crown tab"). This keeps R003's light pixels that lie inside the
outline's inner edge (a polygon through the inner corners of the triangle, shrunk 5 px) or in the chevron
above it, and writes gen/R003/emblem_mask_inner.png (same size, grey 0-237 like the source). Where the X's
upper arms flare into the outline's top bars the polygon's straight top edge keeps the flare, so the arms run
out toward the corners as on the drawn plate. Image-tools Python:

  "$SGT_PYIMG" -I scripts/tools/emblem_inner.py
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(PROJECT, "gen", "R003", "emblem_mask.png")
DST = os.path.join(PROJECT, "gen", "R003", "emblem_mask_inner.png")
# the outline's inner edge, measured on the 1254 px mask (rows 482-1075): its two upper inner corners and
# the inner apex; the top edge runs to the X's tips (y 460) so the arms keep their flare
INNER = [(342, 482), (548, 452), (627, 570), (706, 452), (912, 482), (627, 1075)]
CHEVRON = (440, 100, 815, 412)      # the chevron's box (its own component above the outline's top bars)
SHRINK = 5


def main():
    src = Image.open(SRC).convert("L")
    a = np.asarray(src).astype(np.float32)
    c = np.array(INNER, float)
    centre = c.mean(axis=0)
    poly = [tuple(p + (centre - p) / np.linalg.norm(centre - p) * SHRINK) for p in c]
    keep = Image.new("L", src.size, 0)
    d = ImageDraw.Draw(keep)
    d.polygon(poly, fill=255)
    d.rectangle(CHEVRON, fill=255)
    out = np.where(np.asarray(keep) > 127, a, 0.0)
    Image.fromarray(out.astype(np.uint8)).save(DST)
    m = out > 128
    ys, xs = np.nonzero(m)
    print(f"{os.path.relpath(DST, PROJECT)}: mark bbox x {xs.min()}-{xs.max()}, y {ys.min()}-{ys.max()} "
          f"(of {a.shape[1]} x {a.shape[0]}); light pixels {m.mean():.3f} (source {(a > 128).mean():.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
