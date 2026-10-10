"""Reference masks from recipes (spec 17 §4.11), numpy only: the masks that need no AI model.

  python scripts/eval/masks.py [--out ref/masks] [boot_R boot_L ui soldier_full]

Recipes. boot_R and boot_L follow spec 02 §8.2: luminance below 110 inside each boot's box (his right
boot (610,750)-(790,935), his left (860,750)-(1010,935)), without the floor reflection below the sole
line (y > 896 right, y > 908 left) and without the trouser cuff above y 806; then the largest connected
region with its holes filled, because a threshold alone leaves pinholes in the lit leather and specks
in the floor's dark seams. ui is the union of the UI boxes of ui_mask.json (§2.6). soldier_full pastes
the rembg u2net matte back into the frame at (580, 20) at half scale (spec 17 §4.11) when the matte is
there, and otherwise says how to make it. Masks are full-frame 8-bit greys, 255 inside; the spec keeps
them in ref/masks/ (committed); scratch runs can write to cache/masks/, where the sheets also look.
Render masks from Cryptomatte (the other half of §4.11) are not written yet.
"""
import argparse
import json
import os
import sys
from collections import deque

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(HERE))  # scripts/
from lib import env  # noqa: E402
from eval import camproj, grade  # noqa: E402

REF = env.path("ref", "reference_full.png")
MATTE = env.path("assets", "ai", "rembg_out", "soldier_full_u2net_mask.png")
BOOTS = {  # spec 02 §8.2: box, reflection cut (rows below), cuff cut (rows above)
    "boot_R": {"box": (610, 750, 790, 935), "below": 896, "above": 806},
    "boot_L": {"box": (860, 750, 1010, 935), "below": 908, "above": 806},
}
LUM_MAX = 110


def luminance(rgb8):
    return rgb8[..., :3] @ np.array([0.2126, 0.7152, 0.0722])


def largest_region(m):
    """The largest 4-connected region of a boolean mask, holes filled."""
    h, w = m.shape
    label = np.zeros((h, w), np.int32)
    best, best_n, n = 0, 0, 0
    for y0, x0 in zip(*np.nonzero(m)):
        if label[y0, x0]:
            continue
        n += 1
        label[y0, x0] = n
        q, size = deque([(y0, x0)]), 0
        while q:
            y, x = q.popleft()
            size += 1
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not label[yy, xx]:
                    label[yy, xx] = n
                    q.append((yy, xx))
        if size > best_n:
            best, best_n = n, size
    keep = label == best
    # holes: background not reachable from the border
    outside = np.zeros((h, w), bool)
    q = deque([(y, x) for y in range(h) for x in (0, w - 1) if not keep[y, x]] +
              [(y, x) for x in range(w) for y in (0, h - 1) if not keep[y, x]])
    for y, x in q:
        outside[y, x] = True
    while q:
        y, x = q.popleft()
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < h and 0 <= xx < w and not keep[yy, xx] and not outside[yy, xx]:
                outside[yy, xx] = True
                q.append((yy, xx))
    return ~outside


def boot_mask(name, ref=None):
    r = BOOTS[name]
    ref = ref if ref is not None else grade.read_png(REF)[..., :3] * 255.0
    x0, y0, x1, y1 = r["box"]
    lum = luminance(ref[y0:y1, x0:x1])
    rows = np.arange(y0, y1)[:, None]
    m = (lum < LUM_MAX) & (rows <= r["below"]) & (rows >= r["above"])
    out = np.zeros((camproj.H, camproj.W), bool)
    out[y0:y1, x0:x1] = largest_region(m)
    return out


def ui_mask():
    with open(os.path.join(HERE, "ui_mask.json"), encoding="utf-8") as f:
        boxes = json.load(f)["boxes"]
    out = np.zeros((camproj.H, camproj.W), bool)
    for x0, y0, x1, y1 in boxes.values():
        out[y0:y1 + 1, x0:x1 + 1] = True   # inclusive boxes
    return out


def soldier_mask():
    if not os.path.exists(MATTE):
        raise FileNotFoundError(f"{os.path.relpath(MATTE, env.PROJECT_DIR)} is missing: run rembg (u2net) on "
                                "ref/crop_soldier_full.png (scripts/research/ai_rembg.py) first")
    from PIL import Image
    m = np.asarray(Image.open(MATTE).convert("L").resize((440, 915), Image.LANCZOS)) > 127
    out = np.zeros((camproj.H, camproj.W), bool)
    out[20:935, 580:1020] = m
    return out


def write(mask, path):
    grade.write_png(path, (mask * 255).astype(np.uint8))
    return path


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("names", nargs="*", default=["boot_R", "boot_L", "ui"])
    ap.add_argument("--out", default="ref/masks", help="folder, project-relative (cache/masks for scratch)")
    a = ap.parse_args(argv)
    out = env.path(a.out)
    os.makedirs(out, exist_ok=True)
    ref = grade.read_png(REF)[..., :3] * 255.0
    for name in a.names:
        if name in BOOTS:
            m = boot_mask(name, ref)
        elif name == "ui":
            m = ui_mask()
        elif name == "soldier_full":
            m = soldier_mask()
        else:
            ap.error(f"no recipe for {name!r}")
        path = write(m, os.path.join(out, name + ".png"))
        print(f"{name}: {int(m.sum())} px -> {os.path.relpath(path, env.PROJECT_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
