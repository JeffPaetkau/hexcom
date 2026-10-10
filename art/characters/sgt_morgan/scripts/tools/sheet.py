"""Contact sheets, pairs and onion skins against the reference (spec 18 §4.8.3; p18.V1 and V4).

The reference is cut from ref/reference_full.png at the preset's box and scale with PIL's LANCZOS,
which reproduces the ref/crop_*.png files pixel for pixel, so it always matches the render's size. The
reference silhouette, from the masks the preset names (ref/masks/<name>.png, or cache/masks/ for
scratch masks; the union when it names several), is drawn as a 1 px cyan edge over every render so a
form variant can be judged against the reference outline at a glance. Renders with alpha (the form
tier) are shown over dark grey. Image-tools Python with PIL and numpy, no Blender.

  python -I scripts/tools/sheet.py sheet --preset ref.head_face --images a.png b.png [--labels "jaw +0.08" ...]
  python -I scripts/tools/sheet.py sheet --variants run.json     ({"preset", "variants": [{"image", "params",
                                                                  "metrics", "objective"}]}, the server's output)
  python -I scripts/tools/sheet.py pair  --preset ref.boots_feet --image render.png
  python -I scripts/tools/sheet.py onion --preset ref.boots_feet --image render.png [--alpha 0.5]

Sheets: cell 1 is the reference in a cyan frame, then the variants sorted by objective (lowest first),
each labelled with its name or parameter deltas and up to three metrics; cells at most 420 px on the long
side, the sheet at most 2400 px wide (the Read tool shows it whole); written to
renders/<part>/sheets/<run>.png with a .json beside it. Pairs and onions go beside the render
(<image>_pair.png, <image>_onion.png), at most 2000 px on the long side (p18.V4).
"""
import argparse
import datetime
import json
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
from lib import env  # noqa: E402
from eval import camera, camproj  # noqa: E402

CYAN = (0, 255, 255)
BG = (40, 40, 40)
CELL, SHEET_W, PAIR_MAX, GAP = 420, 2400, 2000, 8
MASK_DIRS = (env.path("ref", "masks"), env.path("cache", "masks"))


def font(size=14):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow before 10.1 has only the bitmap font
        return ImageFont.load_default()


def reference(p):
    """The reference at the render's size for a preset: (RGB image, description)."""
    r, cam = p["render"], p["camera"]
    if cam["type"] == "hero":
        full = Image.open(env.path("ref", "reference_full.png")).convert("RGB")
        box, s = r.get("border_px") or (0, 0, camproj.W, camproj.H), r.get("scale", 1)
        size = camproj.box_size(box, s)
        crop = full.crop(tuple(box))
        return (crop if size == crop.size else crop.resize(size, Image.LANCZOS)), {"box": list(box), "scale": s}
    if p["compare"]:
        return Image.open(env.path(p["compare"][0])).convert("RGB"), {"file": p["compare"][0]}
    return None, {}


def ref_mask(p, size):
    """The union of the preset's reference masks, cut and scaled to size (bool array), or None."""
    cam, r = p["camera"], p["render"]
    if cam["type"] != "hero" or not p.get("mask"):
        return None, []
    box = r.get("border_px") or (0, 0, camproj.W, camproj.H)
    out, used = None, []
    for name in p["mask"]:
        path = next((os.path.join(d, name + ".png") for d in MASK_DIRS if os.path.exists(os.path.join(d, name + ".png"))), None)
        if path is None:
            continue
        m = Image.open(path).convert("L").crop(tuple(box)).resize(size, Image.BILINEAR)
        m = np.asarray(m) > 127
        out = m if out is None else (out | m)
        used.append(os.path.relpath(path, env.PROJECT_DIR).replace(os.sep, "/"))
    return out, used


def edge(m):
    """The 1 px inner boundary of a boolean mask."""
    e = np.zeros_like(m)
    inner = m.copy()
    inner[1:] &= m[:-1]
    inner[:-1] &= m[1:]
    inner[:, 1:] &= m[:, :-1]
    inner[:, :-1] &= m[:, 1:]
    e[:] = m & ~inner
    return e


def flat(im, bg=BG):
    """RGB for display: an image with alpha goes over a flat grey."""
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        base = Image.new("RGBA", im.size, bg + (255,))
        return Image.alpha_composite(base, im).convert("RGB")
    return im.convert("RGB")


def with_edge(im, m):
    """Draw the mask's edge in cyan over an RGB image of the same size (or scaled to it)."""
    if m is None:
        return im
    if m.shape[::-1] != im.size:
        m = np.asarray(Image.fromarray(m.astype(np.uint8) * 255).resize(im.size, Image.BILINEAR)) > 127
    a = np.array(im)
    a[edge(m)] = CYAN
    return Image.fromarray(a)


def fit(im, long_side):
    s = min(1.0, long_side / max(im.size))
    return im if s >= 1.0 else im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def _label_lines(v):
    lines = [v.get("label") or os.path.splitext(os.path.basename(v["image"]))[0]]
    params = v.get("params") or {}
    if params:
        lines.append("  ".join(f"{k} {val:+.3g}" if isinstance(val, (int, float)) else f"{k} {val}" for k, val in params.items()))
    metrics = list((v.get("metrics") or {}).items())[:3]
    if metrics:
        lines.append(" · ".join(f"{k} {val:.3g}" if isinstance(val, float) else f"{k} {val}" for k, val in metrics))
    return lines


def cell(im, lines, f, frame=None):
    pad, lh = 4, f.size + 4 if hasattr(f, "size") else 15
    out = Image.new("RGB", (im.width, im.height + pad * 2 + lh * len(lines)), (16, 16, 16))
    out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    for i, t in enumerate(lines):
        d.text((pad, im.height + pad + i * lh), t, fill=(230, 230, 230), font=f)
    if frame:
        d.rectangle([0, 0, im.width - 1, im.height - 1], outline=frame, width=2)
    return out


def sheet(p, variants, out_png, title=None):
    t0 = time.time()
    ref, ref_info = reference(p)
    size = ref.size if ref is not None else Image.open(variants[0]["image"]).size
    m, used = ref_mask(p, size)
    variants = sorted(variants, key=lambda v: (v.get("objective") is None, v.get("objective") or 0.0))
    f = font(14)
    cells = []
    if ref is not None:
        r = fit(ref, CELL)
        cells.append(cell(with_edge(r, m), ["reference", title or p["id"]], f, frame=CYAN))
    for v in variants:
        im = fit(flat(Image.open(v["image"])), CELL)
        cells.append(cell(with_edge(im, m), _label_lines(v), f))
    cw, ch = max(c.width for c in cells), max(c.height for c in cells)
    cols = max(1, min(len(cells), (SHEET_W - GAP) // (cw + GAP)))
    rows = -(-len(cells) // cols)
    out = Image.new("RGB", (cols * (cw + GAP) + GAP, rows * (ch + GAP) + GAP), (8, 8, 8))
    for i, c in enumerate(cells):
        out.paste(c, (GAP + (i % cols) * (cw + GAP), GAP + (i // cols) * (ch + GAP)))
    os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
    out.save(out_png)
    meta = {"preset": p["id"], "reference": ref_info, "masks": used, "sheet_size": list(out.size), "cell": [cw, ch],
            "cells": [{"image": os.path.relpath(v["image"], env.PROJECT_DIR).replace(os.sep, "/"), "label": _label_lines(v),
                       "objective": v.get("objective")} for v in variants],
            "seconds": round(time.time() - t0, 3)}
    with open(os.path.splitext(out_png)[0] + ".json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    return meta


def _render_at(p, image):
    ref, _ = reference(p)
    im = flat(Image.open(image))
    if ref is None:
        raise SystemExit(f"{p['id']} has no reference to compare with")
    if im.size != ref.size:
        print(f"[sheet] {os.path.basename(image)} is {im.size}, the reference {ref.size}: resized to match", flush=True)
        im = im.resize(ref.size, Image.LANCZOS)
    m, used = ref_mask(p, ref.size)
    return ref, im, m, used


def pair(p, image, out_png, show_edge=True):
    ref, im, m, used = _render_at(p, image)
    f = font(max(14, ref.height // 40))
    out = Image.new("RGB", (ref.width * 2 + GAP, ref.height), (8, 8, 8))
    out.paste(ref, (0, 0))
    out.paste(with_edge(im, m) if show_edge else im, (ref.width + GAP, 0))
    d = ImageDraw.Draw(out)
    for x, t in ((6, "reference"), (ref.width + GAP + 6, "render")):
        d.text((x, 4), t, fill=CYAN, font=f, stroke_width=2, stroke_fill=(0, 0, 0))
    out = fit(out, PAIR_MAX)
    out.save(out_png)
    return {"pair": out_png, "size": list(out.size), "masks": used}


def onion(p, image, out_png, alpha=0.5, show_edge=True):
    ref, im, m, used = _render_at(p, image)
    out = Image.blend(ref, im, alpha)
    out = fit(with_edge(out, m) if show_edge else out, PAIR_MAX)
    out.save(out_png)
    return {"onion": out_png, "size": list(out.size), "masks": used, "alpha": alpha}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("mode", choices=("sheet", "pair", "onion"))
    ap.add_argument("--preset", help="preset id or name (a variants file may name it instead)")
    ap.add_argument("--images", nargs="+", default=[], help="variant images (sheet)")
    ap.add_argument("--labels", nargs="+", default=[], help="one label per image (sheet)")
    ap.add_argument("--variants", help="JSON of variants with params, metrics and objective (sheet)")
    ap.add_argument("--image", help="the render (pair, onion)")
    ap.add_argument("--out", help="output PNG (default: see the module doc)")
    ap.add_argument("--run", help="sheet name (default: the time)")
    ap.add_argument("--title")
    ap.add_argument("--alpha", type=float, default=0.5, help="onion: weight of the render")
    ap.add_argument("--no-edge", action="store_true", help="do not draw the reference silhouette")
    a = ap.parse_args(argv)
    reg = camera.load_registry()
    variants = []
    if a.variants:
        with open(a.variants, encoding="utf-8") as fh:
            data = json.load(fh)
        a.preset = a.preset or data.get("preset")
        base = os.path.dirname(os.path.abspath(a.variants))
        for v in data.get("variants", []):
            v = dict(v)
            v["image"] = v["image"] if os.path.isabs(v["image"]) or os.path.exists(v["image"]) else os.path.join(base, v["image"])
            variants.append(v)
    if not a.preset:
        ap.error("--preset is needed")
    p = reg.get(a.preset)
    if a.mode == "sheet":
        labels = a.labels + [None] * (len(a.images) - len(a.labels))
        variants += [{"image": im, "label": lab} for im, lab in zip(a.images, labels)]
        if not variants:
            ap.error("sheet needs --images or --variants")
        run = a.run or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out = a.out or os.path.join(camera.part_dir(p.get("owner")), "sheets", f"{run}.png")
        meta = sheet(p, variants, out, a.title)
        print(f"[sheet] {len(meta['cells'])} variants, {meta['sheet_size'][0]} x {meta['sheet_size'][1]} px, "
              f"masks {meta['masks'] or 'none found'}, {meta['seconds']} s -> {os.path.relpath(out, env.PROJECT_DIR)}")
        return 0
    if not a.image:
        ap.error(f"{a.mode} needs --image")
    out = a.out or os.path.splitext(a.image)[0] + f"_{a.mode}.png"
    res = (pair(p, a.image, out, not a.no_edge) if a.mode == "pair"
           else onion(p, a.image, out, a.alpha, not a.no_edge))
    print(f"[sheet] {a.mode} {res['size'][0]} x {res['size'][1]} px, masks {res['masks'] or 'none found'} -> "
          f"{os.path.relpath(out, env.PROJECT_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
