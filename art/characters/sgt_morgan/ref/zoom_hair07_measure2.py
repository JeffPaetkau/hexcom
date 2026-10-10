import sys
from PIL import Image
import numpy as np
im = Image.open(sys.argv[1]).convert("RGB"); a = np.asarray(im).astype(int)
lum = (a[...,0]*299 + a[...,1]*587 + a[...,2]*114)//1000
ys = []
for x in range(755, 851):
    col = lum[8:60, x]; idx = np.where(col > 28)[0]
    ys.append(8 + idx[0] if len(idx) else 99)
ys = np.array(ys)
for prom_min, win in ((1,3),(1,4),(2,4)):
    peaks=[]
    for i in range(1,len(ys)-1):
        if ys[i] <= ys[i-1] and ys[i] <= ys[i+1] and ys[i] < 60:
            left = max(ys[max(0,i-win):i]); right = max(ys[i+1:i+1+win])
            prom = min(left,right)-ys[i]
            if prom >= prom_min: peaks.append((755+i,int(ys[i]),int(prom)))
    merged=[]
    for p in peaks:
        if merged and p[0]-merged[-1][0] <= 2:
            if p[1] < merged[-1][1]: merged[-1]=p
        else: merged.append(p)
    print(f"prom>={prom_min} win={win}: {len(merged)}", merged)
# hair mass extents per row (lum>28 within x 740..870) -> head-top outline
print("row: leftmost..rightmost hair/head pixel (lum>28), width px")
for y in range(12, 60, 2):
    r = lum[y, 740:870]; idx = np.where(r > 28)[0]
    if len(idx): print(y, 740+idx[0], 740+idx[-1], idx[-1]-idx[0])
# sideburn / fade bottom: along x=758..770, find where hair (lum<140 and not background) ends going down from y=60 to 100
print("fade column scans (y: lum) x=760,764,768,772")
for x in (760,764,768,772):
    print(x, [(y,int(lum[y,x])) for y in range(56,100,4)])
# brow: per column thickness (rows with lum<110 between y 64 and 80) for right brow x 784..812 and left 816..846
print("right brow thickness per col (x: rows)")
for x in range(784,813,2):
    rows=[y for y in range(64,80) if lum[y,x]<110]
    print(x, rows[0] if rows else None, rows[-1] if rows else None, len(rows), end=" | ")
print()
print("left brow thickness per col")
for x in range(816,847,2):
    rows=[y for y in range(64,80) if lum[y,x]<110]
    print(x, rows[0] if rows else None, rows[-1] if rows else None, len(rows), end=" | ")
print()
