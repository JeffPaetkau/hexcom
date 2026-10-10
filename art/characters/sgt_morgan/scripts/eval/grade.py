"""Display-referred grade, applied after the AgX view transform (spec 17 §5.6 and D7), numpy only.

The reference's grade lives in display values (teal shadows, warm highlights, crushed blacks), so it is
applied here and never in the compositor, where a black curve at linear 0.02 would crush everything
below display 23/255. The parameters are in grade.json, which also holds the flat backdrop colour that
transparent-film hero renders are composited over (spec 17 scope note), measured from the reference by
--measure-backdrop. Only graded images are compared with the reference.

  python scripts/eval/grade.py IN_ungraded.png [OUT.png] [--no-backdrop]
  python scripts/eval/grade.py --measure-backdrop          (writes the backdrop into grade.json)

render.py grades its Cycles renders inside Blender through the same functions: Blender has numpy but
no PIL, so PNGs are read through bpy there (cv2 or PIL elsewhere) and written by the small zlib writer
below, which needs only the standard library.
"""
import argparse
import json
import os
import struct
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(HERE))
GRADE_JSON = os.path.join(HERE, "grade.json")
REF = os.path.join(PROJECT_DIR, "ref", "reference_full.png")
DEFAULTS = {"lift": [0.985, 1.000, 1.025], "gain": [1.035, 1.000, 0.960], "saturation": 0.92, "black": 0.02,
            "backdrop": None}
LUMA = np.array([0.2126, 0.7152, 0.0722])   # Rec.709
# Either side of the figure (the figure box is x 620-1000, spec 17 §2.5), above the horizon (y 616) so the
# floor plane does not cover it, and clear of the UI panels (§2.6).
BACKDROP_BOXES = [(560, 0, 620, 616), (1000, 0, 1060, 616)]


def load_params(path=GRADE_JSON):
    p = dict(DEFAULTS)
    try:
        with open(path, encoding="utf-8") as f:
            p.update(json.load(f))
    except (OSError, ValueError):
        pass
    return p


def grade(D, p=None):
    """Display values D (..., 3) in [0, 1] to graded display values in [0, 1]: steps 1-3 of §5.6."""
    p = p or load_params()
    lift, gain = np.asarray(p["lift"], float), np.asarray(p["gain"], float)
    x = np.clip(((np.asarray(D, float) - 1.0) * (2.0 - lift) + 1.0) * gain, 0.0, 1.0)   # Blender's lift/gain form
    Y = (x @ LUMA)[..., None]
    x = Y + p["saturation"] * (x - Y)
    return np.clip((x - p["black"]) / (1.0 - p["black"]), 0.0, 1.0)


def quantise(x):
    """Step 4: to 8 bits, round half up, no dither."""
    return np.floor(np.asarray(x, np.float64) * 255.0 + 0.5).clip(0, 255).astype(np.uint8)


def grade_image(img, p=None, backdrop=True):
    """img: float (H, W, 3 or 4), display values after AgX in [0, 1], straight alpha. Returns uint8 RGB,
    graded, and composited over the flat backdrop when it has alpha (the graded backdrop is a display
    colour measured from the graded reference, so it is not graded again)."""
    p = p or load_params()
    x = grade(img[..., :3], p)
    if img.shape[-1] == 4 and backdrop:
        if p.get("backdrop") is None:
            raise ValueError("grade.json has no backdrop; run grade.py --measure-backdrop")
        a = np.clip(img[..., 3:4].astype(float), 0.0, 1.0)
        x = x * a + np.asarray(p["backdrop"], float) / 255.0 * (1.0 - a)
    return quantise(x)


# --------------------------------------------------------------------------- PNG in and out

def read_png(path):
    """A PNG as float32 (H, W, C) in [0, 1] at its full bit depth, straight alpha: through bpy inside
    Blender, else cv2 (16-bit), else PIL (8-bit precision only)."""
    try:
        import bpy
    except ImportError:
        bpy = None
    if bpy is not None:
        img = bpy.data.images.load(os.path.abspath(path), check_existing=False)
        try:
            img.colorspace_settings.name = "Non-Color"   # the stored values, no conversion
            img.alpha_mode = "CHANNEL_PACKED"            # never premultiplied
            w, h = img.size
            buf = np.empty(w * h * img.channels, np.float32)
            img.pixels.foreach_get(buf)
            return buf.reshape(h, w, img.channels)[::-1].copy()   # Blender's rows run bottom up
        finally:
            bpy.data.images.remove(img)
    try:
        import cv2
        a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if a is None:
            raise OSError(f"cannot read {path}")
        scale = 65535.0 if a.dtype == np.uint16 else 255.0
        if a.ndim == 3:
            a = a[..., [2, 1, 0, 3]] if a.shape[2] == 4 else a[..., ::-1]
        return a.astype(np.float32) / scale
    except ImportError:
        pass
    from PIL import Image
    im = Image.open(path)
    im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
    return np.asarray(im, np.float32) / 255.0


def write_png(path, a):
    """An 8-bit grey, RGB or RGBA PNG from a uint8 array, with the standard library only."""
    a = np.ascontiguousarray(a, np.uint8)
    h, w = a.shape[:2]
    c = 1 if a.ndim == 2 else a.shape[2]
    rows = a.reshape(h, w * c).astype(np.int16)
    up = (rows - np.vstack([np.zeros((1, w * c), np.int16), rows[:-1]])) % 256   # PNG filter 2 (Up)
    raw = np.empty((h, w * c + 1), np.uint8)
    raw[:, 0], raw[:, 1:] = 2, up

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, {1: 0, 3: 2, 4: 6}[c], 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw.tobytes(), 6)) + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)


def grade_file(src, dst, p=None, backdrop=True):
    out = grade_image(read_png(src), p, backdrop)
    write_png(dst, out)
    return out


def measure_backdrop(ref=REF, boxes=BACKDROP_BOXES):
    """Mean display colour of the reference background beside the figure (8-bit, rounded to 0.1)."""
    a = read_png(ref)[..., :3] * 255.0
    px = np.concatenate([a[y0:y1, x0:x1].reshape(-1, 3) for x0, y0, x1, y1 in boxes])
    return [round(float(v), 1) for v in px.mean(axis=0)], [round(float(v), 1) for v in px.std(axis=0)]


def selftest():
    p = dict(DEFAULTS, backdrop=[30, 33, 36])
    g = grade(np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.0, 1.0, 1.0]]), p)
    assert np.all(g[0] <= 0.03) and g[0][2] > g[0][0]          # teal-leaning, crushed blacks
    assert g[2][0] > 0.999 and g[2][2] < 0.97                    # warm highlights
    q = quantise(np.array([0.5 / 255, 1.5 / 255, 254.5 / 255]))
    assert list(q) == [1, 2, 255], q                             # round half up
    img = np.zeros((2, 2, 4), np.float32)
    assert grade_image(img, p).tolist()[0][0] == [30, 33, 36]    # transparent shows the backdrop
    return {"grade_black": g[0].round(4).tolist(), "grade_mid": g[1].round(4).tolist(), "grade_white": g[2].round(4).tolist()}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src", nargs="?", help="ungraded PNG (after the view transform)")
    ap.add_argument("dst", nargs="?", help="graded PNG (default: src with _ungraded removed, or _graded added)")
    ap.add_argument("--no-backdrop", action="store_true", help="keep alpha out of it: grade RGB only")
    ap.add_argument("--measure-backdrop", action="store_true", help="measure the backdrop and write grade.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        print(json.dumps(selftest()))
    if a.measure_backdrop:
        mean, sd = measure_backdrop()
        p = load_params()
        p.update(backdrop=mean, backdrop_sd=sd,
                 backdrop_source={"ref": "ref/reference_full.png", "boxes": BACKDROP_BOXES, "stat": "mean of 8-bit display values"})
        p.setdefault("doc", "Display grade of spec 17 §5.6 (lift and gain in Blender's form, saturation about "
                            "Rec.709 luma, black crush) and the flat backdrop (8-bit display) that transparent-film "
                            "hero renders are composited over; grade.py --measure-backdrop rewrites the backdrop.")
        with open(GRADE_JSON, "w", encoding="utf-8") as f:
            keys = ["doc"] + [k for k in p if k != "doc"]
            f.write("{\n" + ",\n".join(f" {json.dumps(k)}: {json.dumps(p[k], ensure_ascii=False)}" for k in keys) + "\n}\n")
        print(f"backdrop {mean} (sd {sd}) -> {os.path.relpath(GRADE_JSON, PROJECT_DIR)}")
    if a.src:
        dst = a.dst or (a.src.replace("_ungraded.png", ".png") if a.src.endswith("_ungraded.png") else a.src[:-4] + "_graded.png")
        grade_file(a.src, dst, backdrop=not a.no_backdrop)
        print(dst)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]))
