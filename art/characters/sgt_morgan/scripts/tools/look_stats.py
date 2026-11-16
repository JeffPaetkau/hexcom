"""Per-part brightness and hue of a look-loop render against the reference, and the neutral balance
(take 2, round 8's look pass). Image-tools Python (PIL, numpy), no Blender.

  "$SGT_PYIMG" -I scripts/tools/look_stats.py renders/look/v1 [--grade | --grade-json FILE] [--crops ...]
      [--sheet] [--label TEXT]

Reads <dir>/<crop>_cycles.png (AgX display values, transparent film) and <dir>/<crop>_mask.png (look_loop.py's
flat part colours). With --grade the Cycles image goes through scripts/eval/grade.py (grade.json, or the file
given) first, composited over the backdrop, as the critics will see it; the graded image is written beside it
as <crop>_graded.png. The reference crop is cut from ref/reference_full.png by the preset (tools/sheet.py).

For each part, over the render's own part mask eroded by 2 px (the drawn kit is placed a little differently,
so the reference under the mask is mostly but not only that part; belt and trousers least well):
  - the median luminance (Rec.709 Y of linear sRGB) of reference and render, and their ratio (ref / render);
  - the median linear colour of each, as an 8-bit hex and as chromaticity (r/g, b/g);
  - the same chromaticity over the lit third (the brightest of the part's pixels in each image, the warm key)
    and the shaded third (the darkest, the cool side and fill), so the warm/cool split can be judged.
The neutral gain is computed over the parts the reference shows as neutral or near-black (shirt, gloves,
carbine, boots): the per-channel linear gain, normalised to green, that maps the render's median colour onto
the reference's, for all pixels, the lit third and the shaded third. Written to <dir>/stats[_graded].json and
printed as a table.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
from eval import camera, grade as GR  # noqa: E402
from tools import sheet as SH  # noqa: E402
from tools.look_loop import MASK, CROPS  # noqa: E402

LUMA = np.array([0.2126, 0.7152, 0.0722])
NEUTRAL = ("shirt", "gloves", "carbine", "boots")
PARTS = ("trousers", "shirt", "boots", "gloves", "carrier", "armour", "belt", "carbine")


def lin(d):
    d = np.asarray(d, float)
    return np.where(d <= 0.04045, d / 12.92, ((d + 0.055) / 1.055) ** 2.4)


def enc(c):
    c = np.clip(np.asarray(c, float), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def hexs(c):
    return "#" + "".join(f"{int(round(float(v) * 255)):02x}" for v in enc(c))


def decode_mask(path):
    a = np.asarray(Image.open(path).convert("RGBA")).astype(float)
    parts = list(MASK)
    cols = np.array([enc(np.array(MASK[p]) / 255.0) * 255 for p in parts])
    d = ((a[..., None, :3] - cols[None, None]) ** 2).sum(-1)
    idx = d.argmin(-1)
    ok = (a[..., 3] > 250) & (d.min(-1) < 300)
    lab = np.full(idx.shape, "", dtype=object)
    for i, p in enumerate(parts):
        lab[(idx == i) & ok] = "body" if p == "head" else p
    return lab


def erode(m, n=2):
    for _ in range(n):
        e = m.copy()
        e[1:] &= m[:-1]
        e[:-1] &= m[1:]
        e[:, 1:] &= m[:, :-1]
        e[:, :-1] &= m[:, 1:]
        m = e
    return m


def stats(px, xs=None):
    """px: (N, 3) linear. Median colour, Y median, chromaticity; the lit band (luminance percentiles 65-95) and
    the shaded band (10-40, above the crushed blacks); with xs (each pixel's x relative to the part's median x
    in its crop) also the viewer's-left half (the key's side) and the viewer's-right half (the cool light's)."""
    if len(px) < 50:
        return None
    Y = px @ LUMA
    o = np.argsort(Y)
    n = len(o)
    lit_i, shade_i = o[int(0.65 * n):int(0.95 * n)], o[int(0.10 * n):int(0.40 * n)]

    def chroma(q):
        m = np.median(q, axis=0)
        return m, [round(float(m[0] / max(m[1], 1e-6)), 3), round(float(m[2] / max(m[1], 1e-6)), 3)]

    m, ch = chroma(px)
    ml, chl = chroma(px[lit_i])
    ms, chs = chroma(px[shade_i])
    side = {}
    if xs is not None:
        for nm, sel in (("key_side", xs < 0), ("cool_side", xs >= 0)):
            if sel.sum() > 50:
                side[nm] = chroma(px[sel])[1]
    return {**side, "n": int(len(px)), "Y": float(np.median(Y)), "hex": hexs(m), "chroma": ch, "lit_chroma": chl,
            "shade_chroma": chs, "lin": m.tolist(), "lit_lin": ml.tolist(), "shade_lin": ms.tolist(),
            "Y_p90": float(np.percentile(Y, 90)), "Y_p10": float(np.percentile(Y, 10))}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--grade", action="store_true")
    ap.add_argument("--grade-json", default=None)
    ap.add_argument("--crops", default="torso_vest,arm_R,arm_L,hands_rifle,belt_hips,legs_knees,boots_feet")
    ap.add_argument("--sheet", action="store_true", help="write <dir>/sheet_<crop>.png: reference | render")
    ap.add_argument("--label", default="")
    a = ap.parse_args(argv)
    graded = a.grade or a.grade_json
    gp = GR.load_params(a.grade_json) if a.grade_json else (GR.load_params() if graded else None)
    reg = camera.load_registry()
    acc = {p: {"ref": [], "ren": [], "x": []} for p in PARTS}
    per_crop = {}
    for lab in a.crops.split(","):
        cp, mp = (os.path.join(a.dir, f"{lab}_{k}.png") for k in ("cycles", "mask"))
        if not (os.path.exists(cp) and os.path.exists(mp)):
            continue
        img = GR.read_png(cp)
        if graded:
            ren8 = GR.grade_image(img, gp, backdrop=True)
            Image.fromarray(ren8).save(os.path.join(a.dir, f"{lab}_graded.png"))
            ren = ren8.astype(float) / 255.0
        else:
            ren = img[..., :3]
        ref_im, _ = SH.reference(reg.get(f"ref.{lab}"))
        ref = np.asarray(ref_im.convert("RGB").resize((ren.shape[1], ren.shape[0]), Image.LANCZOS)).astype(float) / 255
        L = decode_mask(mp)
        rl, nl = lin(ref), lin(ren)
        per_crop[lab] = {}
        for p in PARTS:
            m = erode(L == p)
            if m.sum() < 50:
                continue
            xs = np.nonzero(m)[1].astype(float)
            xs -= np.median(xs)
            acc[p]["ref"].append(rl[m])
            acc[p]["ren"].append(nl[m])
            acc[p]["x"].append(xs)
            per_crop[lab][p] = {"ref": stats(rl[m], xs), "ren": stats(nl[m], xs)}
        if a.sheet:
            show = Image.fromarray((ren * 255).astype(np.uint8)) if graded else SH.flat(Image.open(cp))
            s = Image.new("RGB", (ren.shape[1] * 2 + 8, ren.shape[0]), (0, 0, 0))
            s.paste(ref_im.convert("RGB").resize((ren.shape[1], ren.shape[0])), (0, 0))
            s.paste(show.convert("RGB"), (ren.shape[1] + 8, 0))
            d = ImageDraw.Draw(s)
            d.rectangle((0, 0, s.width, 28), fill=(0, 0, 0))
            d.text((8, 4), f"reference ref.{lab}", fill=(255, 255, 255), font=SH.font(20))
            d.text((ren.shape[1] + 16, 4), f"{a.label or os.path.basename(a.dir)} {'graded' if graded else 'ungraded'}",
                   fill=(255, 255, 255), font=SH.font(20))
            SH.fit(s, 2400).save(os.path.join(a.dir, f"sheet_{lab}{'_graded' if graded else ''}.png"))
    out = {"dir": a.dir, "graded": bool(graded), "parts": {}, "neutral": {}, "per_crop": per_crop}
    print(f"{'part':9} {'ratio':>5} {'ref hex':>8} {'ren hex':>8}  ref r/g b/g   ren r/g b/g | lit ref / ren      | shade ref / ren")
    for p in PARTS:
        if not acc[p]["ref"]:
            continue
        xs = np.concatenate(acc[p]["x"])
        R, N = stats(np.concatenate(acc[p]["ref"]), xs), stats(np.concatenate(acc[p]["ren"]), xs)
        out["parts"][p] = {"ref": R, "ren": N, "ratio": round(R["Y"] / max(N["Y"], 1e-6), 3)}
        print(f"{p:9} {R['Y'] / N['Y']:5.2f} {R['hex']:>8} {N['hex']:>8}  {R['chroma'][0]:.2f} {R['chroma'][1]:.2f}"
              f"   {N['chroma'][0]:.2f} {N['chroma'][1]:.2f} | {R['lit_chroma']} {N['lit_chroma']} | "
              f"{R['shade_chroma']} {N['shade_chroma']} | key side {R.get('key_side')} {N.get('key_side')} | cool side "
              f"{R.get('cool_side')} {N.get('cool_side')}")
    for band, key in (("all", "lin"), ("lit", "lit_lin"), ("shade", "shade_lin")):
        r = np.array([out["parts"][p]["ref"][key] for p in NEUTRAL if p in out["parts"]])
        n = np.array([out["parts"][p]["ren"][key] for p in NEUTRAL if p in out["parts"]])
        if not len(r):
            continue
        g = np.median(r / np.maximum(n, 1e-6), axis=0)
        out["neutral"][band] = [round(float(v / g[1]), 3) for v in g]
    print("neutral gain (linear, /G) over", ",".join(NEUTRAL), out["neutral"])
    with open(os.path.join(a.dir, f"stats{'_graded' if graded else ''}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
