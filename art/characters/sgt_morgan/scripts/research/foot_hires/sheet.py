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


def pairs(before, after, views, tier, out_dir, cell=1024, labels=("before", "after"), title=None):
    """The shape pass (2026-10-14): each view's before and after side by side at the same scale (both renders of
    one preset at one resolution, scaled alike), one image a view, and one overview of them all (a row a view)."""
    f, big = font(24), font(30)
    os.makedirs(out_dir, exist_ok=True)
    made = []
    for view in views:
        ims = [load(run, view, tier) for run in (before, after)]
        if any(im is None for im in ims):
            continue
        sheet = Image.new("RGB", (2 * cell + 10, cell + 44), (20, 20, 20))
        d = ImageDraw.Draw(sheet)
        for i, im in enumerate(ims):
            sheet.paste(im.resize((cell, cell), Image.LANCZOS), (i * (cell + 10), 0))
            d.text((i * (cell + 10) + 10, cell + 8), f"{labels[i]} | {view} ({tier})", fill=(230, 230, 230), font=f)
        path = os.path.join(out_dir, f"sbs_{view}_{tier}.png")
        sheet.save(path)
        made.append((view, path))
    small = cell // 2
    ov = Image.new("RGB", (2 * small + 10, len(made) * (small + 6) + 50), (20, 20, 20))
    d = ImageDraw.Draw(ov)
    d.text((10, 10), title or f"{labels[0]} (left) | {labels[1]} (right)", fill=(240, 240, 240), font=big)
    for r, (view, path) in enumerate(made):
        im = Image.open(path).convert("RGB")
        ov.paste(im.resize((2 * small + 10, int((2 * small + 10) * im.size[1] / im.size[0])), Image.LANCZOS),
                 (0, 50 + r * (small + 6)))
    path = os.path.join(out_dir, f"sbs_overview_{tier}.png")
    ov.save(path)
    return [p for _, p in made] + [path]


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("pairs")
    pr.add_argument("--before", required=True)
    pr.add_argument("--after", required=True)
    pr.add_argument("--views", required=True)
    pr.add_argument("--tier", default="form")
    pr.add_argument("--out", required=True, help="a folder")
    pr.add_argument("--labels", nargs=2, default=["before", "after"])
    pr.add_argument("--cell", type=int, default=1024)
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
    if a.cmd == "pairs":
        for p in pairs(a.before, a.after, a.views.split(","), a.tier, a.out, a.cell, tuple(a.labels)):
            print(p)
        return
    if a.cmd == "grid":
        crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
        print(grid(a.runs, a.views.split(","), a.tier, a.out, a.cell, crop, a.labels))
    else:
        print(critic(a.run, a.tier, a.out, ref=not a.no_ref, title=a.title))


if __name__ == "__main__":
    main(sys.argv[1:])
