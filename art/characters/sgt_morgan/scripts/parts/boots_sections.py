"""Plot the boots' section data (cache/parts/<tag>_sections.json, written by boots.py) as renders/boots/sections_<side>.png:
the long section through the 2nd toe's axis and the cross sections at the ball line and the heel, in frame F (take 1
spec 01's foot frame: origin the pternion on the floor, toes toward -y): the loaded bare foot (red), the last (blue)
and the upper's outer surface (grey), with the toe room, the insole plane and the clearances written on.

  "$SGT_PYIMG" -I scripts/parts/boots_sections.py [--tag boots]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))


def main():
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "boots"
    d = json.load(open(os.path.join(PROJECT, "cache", "parts", f"{tag}_sections.json")))
    out_dir = os.path.join(PROJECT, "renders", "boots")
    for side, o in d.items():
        panels = [("long_x0", "long section x 0 (y back, z up)", 2.6), ("ball", f"across the ball line y {o['ball']['at']}", 4.0),
                  ("heel", "across the heel y -35", 4.0)]
        W, H = 2400, 900
        img = Image.new("RGB", (W, H), (245, 245, 242))
        dr = ImageDraw.Draw(img)
        x0 = 20
        for key, title, sc in panels:
            sec = o[key]
            pw = 1100 if key == "long_x0" else 600
            allp = np.array(sec["skin"] + sec["last"] + sec["upper"])
            cx = 0.5 * (allp[:, 0].min() + allp[:, 0].max())
            base = H - 80
            def to_px(p):
                return (x0 + pw / 2 + (p[0] - cx) * sc * (-1 if key == "long_x0" else 1), base - (p[1] + 40) * sc)
            for name, col, r in (("upper", (120, 120, 120), 2), ("last", (40, 90, 220), 2), ("skin", (210, 60, 50), 1)):
                for p in sec[name]:
                    x, y = to_px(p)
                    dr.ellipse([x - r, y - r, x + r, y + r], fill=col)
            yz = to_px((cx, o["insole_z"]))[1]
            dr.line([x0, yz, x0 + pw, yz], fill=(0, 150, 0))
            dr.text((x0 + 6, 10), title, fill=(0, 0, 0))
            if key == "long_x0":
                sk, la = np.array(sec["skin"]), np.array(sec["last"])
                front_sk, front_la = sk[:, 0].min(), la[:, 0].min()
                dr.text((x0 + 6, 28), f"toe room on this line: {front_sk - front_la:.1f} mm (last tip y {front_la:.1f}, bare toe "
                                      f"y {front_sk:.1f}); last length {o['measure']['last_length_mm']}; toe spring "
                                      f"{o['measure']['toe_spring_deg_read']} deg; green: insole plane", fill=(0, 0, 0))
            x0 += pw + 30
        dr.text((20, H - 30), f"{side} foot, frame F, mm. red: loaded bare foot; blue: last; grey: upper outer", fill=(0, 0, 0))
        p = os.path.join(out_dir, f"sections_{side}.png")
        img.save(p)
        print(p)


if __name__ == "__main__":
    main()
