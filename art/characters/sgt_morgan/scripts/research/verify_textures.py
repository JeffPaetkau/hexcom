#!/usr/bin/env python3
"""Open every downloaded texture/model map with PIL, report resolution/mode, build a colour-map
contact sheet and update manifest.json with per-map resolutions.
Usage: python3 -I verify_textures.py <assets_root> <contact_sheet.png>
"""
import json, os, sys, glob
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = 400_000_000

ROOT, SHEET = sys.argv[1], sys.argv[2]
TEX = os.path.join(ROOT, "textures")
man_path = os.path.join(TEX, "manifest.json")
man = json.load(open(man_path))

def classify(name):
    n = name.lower()
    if any(k in n for k in ("_color", "_diff", "albedo", "basecolor")): return "color"
    if "nor_gl" in n or "normalgl" in n: return "normal_gl"
    if "nor_dx" in n or "normaldx" in n: return "normal_dx"
    if "rough" in n: return "roughness"
    if "_disp" in n or "displacement" in n: return "displacement"
    if "ambientocclusion" in n or n.endswith("_ao_2k.jpg") or "_ao" in n: return "ao"
    if "_arm" in n: return "arm(ao,rough,metal)"
    if "metal" in n: return "metalness"
    if "opacity" in n: return "opacity"
    if "emission" in n: return "emission"
    return "other"

report, colour_tiles, bad = [], [], []
for t in man["textures"]:
    folder = t["folder"]
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png")))
    t["map_report"] = {}
    for f in files:
        p = os.path.join(folder, f)
        try:
            with Image.open(p) as im:
                im.load()
                kind = classify(f)
                t["map_report"][f] = {"kind": kind, "size": list(im.size), "mode": im.mode}
                report.append((t["id"], f, kind, im.size, im.mode))
                if kind == "color":
                    colour_tiles.append((t["need"], t["id"], p))
        except Exception as e:
            bad.append((p, repr(e))); t["map_report"][f] = {"error": repr(e)}
    kinds = sorted({v.get("kind") for v in t["map_report"].values() if "kind" in v})
    t["map_kinds"] = kinds
    sizes = sorted({tuple(v["size"]) for v in t["map_report"].values() if "size" in v})
    t["resolution_px"] = [list(s) for s in sizes]

# also check model textures open
for m in man.get("models", []):
    texdir = os.path.join(m["folder"], "textures")
    m["texture_report"] = {}
    for f in sorted(os.listdir(texdir)) if os.path.isdir(texdir) else []:
        try:
            with Image.open(os.path.join(texdir, f)) as im:
                im.load(); m["texture_report"][f] = list(im.size)
        except Exception as e:
            bad.append((os.path.join(texdir, f), repr(e)))

json.dump(man, open(man_path, "w"), indent=1)

for r in report: print(f"{r[0]:<26} {r[1]:<52} {r[2]:<20} {r[3][0]}x{r[3][1]} {r[4]}")
print("\nBAD:", bad)

# --- contact sheet of colour maps, grouped by need ---
colour_tiles.sort()
TILE, PAD, LABEL = 300, 10, 34
cols = 6
rows = (len(colour_tiles) + cols - 1) // cols
W = cols * (TILE + PAD) + PAD
H = rows * (TILE + LABEL + PAD) + PAD
sheet = Image.new("RGB", (W, H), (28, 28, 30))
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
except Exception:
    font = font_b = ImageFont.load_default()
for i, (need, aid, p) in enumerate(colour_tiles):
    r, c = divmod(i, cols)
    x = PAD + c * (TILE + PAD); y = PAD + r * (TILE + LABEL + PAD)
    with Image.open(p) as im:
        im = im.convert("RGB")
        # show the tile twice: full tile (left) and a 25% crop (right) so weave scale is visible
        full = im.resize((TILE // 2, TILE // 2), Image.LANCZOS)
        w, h = im.size
        crop = im.crop((0, 0, w // 4, h // 4)).resize((TILE // 2, TILE // 2), Image.LANCZOS)
        full2 = im.resize((TILE, TILE // 2), Image.LANCZOS)
    sheet.paste(full2, (x, y))
    sheet.paste(full, (x, y + TILE // 2))
    sheet.paste(crop, (x + TILE // 2, y + TILE // 2))
    draw.text((x, y + TILE + 2), aid, fill=(240, 240, 240), font=font_b)
    draw.text((x, y + TILE + 17), need, fill=(170, 200, 230), font=font)
sheet.save(SHEET)
print("contact sheet", SHEET, sheet.size, len(colour_tiles), "colour maps")
