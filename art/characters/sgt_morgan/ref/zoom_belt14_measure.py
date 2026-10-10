"""Spec 14 helper: gridded zooms of the belt and drop-leg rigs plus luminance profiles.
Run with the system interpreter:  python3 -I ref/zoom_belt14_measure.py
Writes ref/zoom_belt14_*.png (grid lines every 10 full-image px, labelled)."""
from PIL import Image, ImageDraw
import numpy as np
SRC = '/home/user/sgt_morgan/ref/reference_full.png'
im = Image.open(SRC).convert('RGB')
a = np.asarray(im).astype(int)

def grid_zoom(box, scale, out, step=10):
    x0, y0, x1, y1 = box
    crop = im.crop(box).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    for x in range((x0 // step + 1) * step, x1, step):
        X = (x - x0) * scale
        d.line([(X, 0), (X, crop.height)], fill=(255, 255, 0) if x % 50 == 0 else (120, 120, 0), width=1)
        if x % 50 == 0:
            d.text((X + 2, 2), str(x), fill=(255, 255, 0))
    for y in range((y0 // step + 1) * step, y1, step):
        Y = (y - y0) * scale
        d.line([(0, Y), (crop.width, Y)], fill=(0, 255, 255) if y % 50 == 0 else (0, 120, 120), width=1)
        if y % 50 == 0:
            d.text((2, Y + 2), str(y), fill=(0, 255, 255))
    crop.save(out)
    print('wrote', out, crop.size)

grid_zoom((650, 470, 810, 615), 6, '/home/user/sgt_morgan/ref/zoom_belt14_rrig_grid_x6.png')
grid_zoom((820, 450, 980, 600), 6, '/home/user/sgt_morgan/ref/zoom_belt14_lrig_grid_x6.png')
grid_zoom((670, 385, 740, 480), 8, '/home/user/sgt_morgan/ref/zoom_belt14_upperpouch_grid_x8.png')
grid_zoom((690, 465, 900, 525), 6, '/home/user/sgt_morgan/ref/zoom_belt14_belt_grid_x6.png')

# edge finder: horizontal luminance profile with gradient peaks (tube edges)
def edges(y, x0, x1, thresh=25):
    lum = a[y - 1:y + 2, x0:x1].mean(axis=(0, 2))
    g = np.diff(lum)
    peaks = [(x0 + i, int(g[i])) for i in range(len(g)) if abs(g[i]) >= thresh]
    print('y=%d edges (x, dLum):' % y, peaks)
for y in (495, 515, 540, 565):
    edges(y, 655, 745)
for y in (475, 495, 520, 545):
    edges(y, 895, 970)
