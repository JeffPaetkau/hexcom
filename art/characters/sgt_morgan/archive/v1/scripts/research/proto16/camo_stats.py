"""Blotch statistics of a camo bake at reference scale (spec 09 §2.3 method), albedo and display-equivalent.
Usage: python3 -I camo_stats.py <png at 4.72 px/cm> <tone hexes comma> [E]"""
import sys, numpy as np
from PIL import Image, ImageFilter
from collections import deque
sys.path.insert(0, '.')
from colour_util import h2l
png, tones = sys.argv[1], sys.argv[2].split(',')
E = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
im = np.asarray(Image.open(png).convert('RGB')).astype(float) / 255.0
lin = np.where(im <= 0.04045, im/12.92, ((im+0.055)/1.055)**2.4)
# AgX MHC grey table (spec 17 §3.5), scene -> display/255, then the grade's black crush
xs = np.log([0.003,0.005,0.01,0.02,0.03,0.05,0.08,0.12,0.18,0.25,0.35,0.5,0.7,1.0,1.5,2.0,4.0,8.0])
ys = np.array([1,3,10,23,33,49,70,92,118,139,160,178,194,208,221,229,244,255])/255.0
def disp(s):
    d = np.interp(np.log(np.clip(s, 1e-4, 8.0)), xs, ys)
    return np.clip((d - 0.02)/0.98, 0, 1)
dsp = disp(lin * E)
def lum(a): return 255*(0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2])
def label(mask):
    H, W = mask.shape; lab = np.zeros((H, W), int); n = 0; sizes = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and lab[y, x] == 0:
                n += 1; q = deque([(y, x)]); lab[y, x] = n; s = 0
                while q:
                    cy, cx = q.popleft(); s += 1
                    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny, nx = cy+dy, cx+dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and lab[ny, nx] == 0:
                            lab[ny, nx] = n; q.append((ny, nx))
                sizes.append(s)
    return sizes
rng = np.random.default_rng(3)
def stats(L, tag):
    rows = {'light': [], 'dark': []}; con = []
    for k in range(16):
        ww, hh = (90, 35) if k % 2 == 0 else (70, 85)
        x0 = rng.integers(0, L.shape[1]-ww); y0 = rng.integers(0, L.shape[0]-hh)
        sub = L[y0:y0+hh, x0:x0+ww]
        base = np.asarray(Image.fromarray(np.clip(sub,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(12))).astype(float)
        hp = sub - base
        for name, mask in (('light', hp > np.percentile(hp, 70)), ('dark', hp < np.percentile(hp, 30))):
            sz = [s for s in label(mask) if s >= 10]
            if sz:
                eq = np.array([2*np.sqrt(s/np.pi) for s in sz]) * 2.12
                rows[name].append((np.percentile(eq, 25), np.median(eq), np.percentile(eq, 75), eq.max()))
        con.append((np.percentile(hp, 90) - np.percentile(hp, 10)) / max(sub.mean(), 1) * 100)
    for name in ('light', 'dark'):
        a = np.array(rows[name]); m = np.median(a, axis=0)
        print(f"{tag:8s} {name:5s} eq-diam mm p25/50/75/max (median over 16 windows) = {m[0]:.0f}/{m[1]:.0f}/{m[2]:.0f}/{m[3]:.0f}  (window medians range {a[:,1].min():.0f}-{a[:,1].max():.0f})")
    print(f"{tag:8s} contrast median {np.median(con):.0f}% (range {min(con):.0f}-{max(con):.0f}%)")
stats(lum(im), 'albedo')
stats(lum(dsp), f'disp E{E}')
T = np.array([h2l(h) for h in tones])
d = ((lin[..., None, :] - T[None, None])**2).sum(-1)
ids = d.argmin(-1)
print("tone fractions % (nearest tone, linear):", [round(float((ids == k).mean()*100)) for k in range(4)])
print("albedo luminance mean (linear Y):", round(float((0.2126*lin[...,0]+0.7152*lin[...,1]+0.0722*lin[...,2]).mean()), 4))
