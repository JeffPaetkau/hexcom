"""Contact sheets for the trial (image-tools Python with PIL, not Blender): runs as rows, views as columns,
or one run's views in a grid with a reference panel, as the critic sheets want.

  python -I scripts/research/foot_hires/sheet.py grid --runs base fields_v1 --views hr.front,hr.hallux
      --tier form --out renders/research/foot_hires/compare.png [--cell 640] [--crop x0,y0,x1,y1]
  python -I scripts/research/foot_hires/sheet.py critic --run fields_final --tier eval
      --out renders/research/foot_hires/critic_sheet.png [--ref]

Form renders (alpha) are put over dark grey. --crop takes a box in the 2048 px frame before scaling.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(PROJECT, "renders", "research", "foot_hires")
REF = os.path.join(PROJECT, "cache", "ref_feet", "jeff_feet_photos.png")
BG = (36, 36, 36)


def font(size=18):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def load(run, view, tier, crop=None):
    path = os.path.join(OUT, run, f"{view}_{tier}.png")
    if not os.path.exists(path):
        return None
    im = Image.open(path)
    if im.mode == "RGBA":
        bg = Image.new("RGBA", im.size, BG + (255,))
        bg.alpha_composite(im)
        im = bg
    im = im.convert("RGB")
    if crop:
        im = im.crop(crop)
    return im


def grid(runs, views, tier, out, cell=640, crop=None, labels=None):
    f = font(20)
    W = len(views) * cell
    H = len(runs) * (cell + 30)
    sheet = Image.new("RGB", (W, H), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for r, run in enumerate(runs):
        for c, view in enumerate(views):
            im = load(run, view, tier, crop)
            x, y = c * cell, r * (cell + 30)
            if im is not None:
                sheet.paste(im.resize((cell, int(cell * im.size[1] / im.size[0])), Image.LANCZOS), (x, y))
            d.text((x + 6, y + cell + 4), f"{(labels or runs)[r]} | {view}", fill=(230, 230, 230), font=f)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    return out


def critic(run, tier, out, views=None, ref=True, cell=900, title=None):
    """The critic's sheet: the region's views in a grid, the hallux closeup larger, Jeff's photos beside."""
    views = views or ["hr.front", "hr.top34", "hr.medial", "hr.plantar", "hr.toe2"]
    f, big = font(22), font(30)
    close = load(run, "hr.hallux", tier)
    cols = 3
    rows = (len(views) + cols - 1) // cols
    side = 2 * cell
    W = cols * cell + side
    H = max(rows * (cell + 34), side + 34 + (cell if ref else 0)) + 60
    sheet = Image.new("RGB", (W, H), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    d.text((12, 12), title or f"{run} ({tier})", fill=(240, 240, 240), font=big)
    for i, view in enumerate(views):
        im = load(run, view, tier)
        x, y = (i % cols) * cell, 60 + (i // cols) * (cell + 34)
        if im is not None:
            sheet.paste(im.resize((cell, cell), Image.LANCZOS), (x, y))
        d.text((x + 8, y + cell + 6), view, fill=(220, 220, 220), font=f)
    if close is not None:
        sheet.paste(close.resize((side, side), Image.LANCZOS), (cols * cell, 60))
        d.text((cols * cell + 8, 60 + side + 6), "hr.hallux (2048 px closeup)", fill=(220, 220, 220), font=f)
    if ref and os.path.exists(REF):
        im = Image.open(REF).convert("RGB")
        w = side
        im = im.resize((w, int(w * im.size[1] / im.size[0])), Image.LANCZOS)
        sheet.paste(im, (cols * cell, 60 + side + 40))
        d.text((cols * cell + 8, 60 + side + 44 + im.size[1]), "reference: Jeff's photos of men's feet",
               fill=(220, 220, 220), font=f)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grid")
    g.add_argument("--runs", nargs="+", required=True)
    g.add_argument("--labels", nargs="+")
    g.add_argument("--views", required=True)
    g.add_argument("--tier", default="form")
    g.add_argument("--out", required=True)
    g.add_argument("--cell", type=int, default=640)
    g.add_argument("--crop")
    c = sub.add_parser("critic")
    c.add_argument("--run", required=True)
    c.add_argument("--tier", default="eval")
    c.add_argument("--out", required=True)
    c.add_argument("--no-ref", action="store_true")
    c.add_argument("--title")
    a = ap.parse_args(argv)
    if a.cmd == "grid":
        crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
        print(grid(a.runs, a.views.split(","), a.tier, a.out, a.cell, crop, a.labels))
    else:
        print(critic(a.run, a.tier, a.out, ref=not a.no_ref, title=a.title))


if __name__ == "__main__":
    main(sys.argv[1:])
