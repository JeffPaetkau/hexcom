import sys
from PIL import Image, ImageDraw, ImageOps
import numpy as np
src = sys.argv[1]; out = sys.argv[2]
im = Image.open(src).convert("RGB"); a = np.asarray(im).astype(int)
lum = (a[...,0]*299 + a[...,1]*587 + a[...,2]*114)//1000
# 1) silhouette: for columns 755..850 find topmost row in 8..60 with lum>28 (background ~11)
print("col  top_y  (hair silhouette top per column, lum>28)")
tops = {}
for x in range(755, 851):
    col = lum[8:60, x]
    idx = np.where(col > 28)[0]
    tops[x] = 8 + idx[0] if len(idx) else None
row = []
for x in range(755, 851):
    row.append(f"{x}:{tops[x]}")
print(" ".join(row))
# local minima (peaks upward = smaller y) with prominence >=2 px
ys = np.array([tops[x] if tops[x] is not None else 99 for x in range(755,851)])
peaks = []
for i in range(2, len(ys)-2):
    if ys[i] <= ys[i-1] and ys[i] <= ys[i+1] and ys[i] < 99:
        left = max(ys[max(0,i-6):i]); right = max(ys[i+1:i+7])
        prom = min(left, right) - ys[i]
        if prom >= 2:
            peaks.append((755+i, int(ys[i]), int(prom)))
# merge peaks within 3 px
merged = []
for p in peaks:
    if merged and p[0]-merged[-1][0] <= 3:
        if p[1] < merged[-1][1]: merged[-1] = p
    else: merged.append(p)
print("silhouette spikes (x, top_y, prominence_px):", merged, "count", len(merged))
# 2) hairline: for columns 770..845 find lowest hair row (transition to skin) between 30 and 70: skin is lum>120 and reddish
print("hairline per column (first row from y=30 where R>150 and R-B>40):")
hl = []
for x in range(770, 846, 5):
    for y in range(30, 75):
        r,g,b = a[y,x]
        if r > 150 and r-b > 40:
            hl.append(f"{x}:{y}"); break
print(" ".join(hl))
# 3) zone colour stats
def stats(name, x0,y0,x1,y1):
    reg = a[y0:y1, x0:x1].reshape(-1,3); l = lum[y0:y1, x0:x1].ravel()
    m = reg.mean(0); p = np.percentile(l,[5,25,50,75,95])
    print(f"{name:34s} mean #{int(m[0]):02x}{int(m[1]):02x}{int(m[2]):02x} lum p5/25/50/75/95 {p.astype(int).tolist()}")
stats("hair top mass 775-840 x 22-40", 775,22,840,40)
stats("hair fringe lit 775-800 x 30-46", 775,30,800,46)
stats("hair right upper side 762-778 x 48-60", 762,48,778,60)
stats("hair right temple fade 757-772 x 62-78", 757,62,772,78)
stats("hair right fade at ear top 755-768 x 78-86", 755,78,768,86)
stats("skin right temple 776-784 x 66-76", 776,66,784,76)
stats("hair left side shadow 838-848 x 44-60", 838,44,848,60)
stats("hair left temple 840-848 x 60-75", 840,60,848,75)
stats("brow right body 790-805 x 69-73", 790,69,805,73)
stats("brow left body 822-838 x 69-73", 822,69,838,73)
stats("forehead above brow 790-806 x 60-66", 790,60,806,66)
stats("chin pad stubble 808-826 x 116-128", 808,116,826,128)
stats("soul patch 811-821 x 112-118", 811,112,821,118)
stats("moustache 806-826 x 100-106", 806,100,826,106)
stats("right jaw stubble 774-790 x 112-124", 774,112,790,124)
stats("right cheek mid (medium) 782-796 x 104-112", 782,104,796,112)
stats("right cheek upper (bare) 782-796 x 92-100", 782,92,796,100)
stats("under-jaw neck stubble 782-810 x 130-140", 782,130,810,140)
stats("neck below 790-810 x 142-150", 790,142,810,150)
# 4) zooms
def zoom(box, scale, name, grid=5):
    c = im.crop(box).resize(((box[2]-box[0])*scale, (box[3]-box[1])*scale), Image.NEAREST)
    d = ImageDraw.Draw(c)
    for gx in range(box[0] - box[0]%grid, box[2]+1, grid):
        X = (gx-box[0])*scale; d.line([(X,0),(X,c.height)], fill=(255,0,0) if gx%10==0 else (255,255,255), width=1)
        if gx%10==0: d.text((X+2,2), str(gx), fill=(255,255,0))
    for gy in range(box[1] - box[1]%grid, box[3]+1, grid):
        Y = (gy-box[1])*scale; d.line([(0,Y),(c.width,Y)], fill=(255,0,0) if gy%10==0 else (255,255,255), width=1)
        if gy%10==0: d.text((2,Y+2), str(gy), fill=(255,255,0))
    c.save(f"{out}/zoom_hair07_{name}.png")
zoom((750,8,860,56), 10, "top_silhouette_x10")
zoom((750,40,790,100), 12, "rtemple_fade_x12")
# autocontrast hair for strand direction
c = im.crop((755,12,850,58)); c = ImageOps.autocontrast(c, cutoff=2).resize((95*8,46*8), Image.LANCZOS); c.save(f"{out}/zoom_hair07_strands_contrast_x8.png")
c = im.crop((770,96,850,146)); c = ImageOps.autocontrast(c, cutoff=2).resize((80*8,50*8), Image.LANCZOS); c.save(f"{out}/zoom_hair07_stubble_contrast_x8.png")
c = im.crop((780,62,850,82)); c = c.resize((70*12,20*12), Image.LANCZOS); c.save(f"{out}/zoom_hair07_brows_lashes_x12.png")
print("zooms written")
