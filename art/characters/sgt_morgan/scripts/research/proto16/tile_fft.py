"""Measure dominant spatial periods of CC0 texture maps (FFT of a height-like channel).
Usage: python3 -I tile_fft.py <textures_root>"""
import sys, os, numpy as np
from PIL import Image
root = sys.argv[1]
sets = [  # (label, relative file, native tile mm or None, channel)
 ("Fabric063 disp", "Fabric063/Fabric063_2K-JPG_Displacement.jpg", 400, "L"),
 ("Fabric061 disp", "Fabric061/Fabric061_2K-JPG_Displacement.jpg", 400, "L"),
 ("Fabric066 disp", "Fabric066/Fabric066_2K-JPG_Displacement.jpg", 400, "L"),
 ("cotton_jersey disp", "cotton_jersey/cotton_jersey_disp_2k.jpg", 264, "L"),
 ("knitted_fleece disp", "knitted_fleece/knitted_fleece_disp_2k.jpg", 266, "L"),
 ("poly_wool_herringbone disp", "poly_wool_herringbone/poly_wool_herringbone_disp_2k.jpg", 270, "L"),
 ("denim_fabric_05 disp", "denim_fabric_05/denim_fabric_05_disp_2k.jpg", 270, "L"),
 ("nylon_weave_3dt height", "3dtextures_Fabric_Nylon_Weave_001/Fabric_Nylon_weave_001_height.png", None, "L"),
 ("Leather032 disp", "Leather032/Leather032_2K-JPG_Displacement.jpg", 450, "L"),
 ("Leather037 disp", "Leather037/Leather037_2K-JPG_Displacement.jpg", None, "L"),
 ("Rubber004 disp", "Rubber004/Rubber004_2K-JPG_Displacement.jpg", 750, "L"),
 ("Plastic012B disp", "Plastic012B/Plastic012B_2K-JPG_Displacement.jpg", None, "L"),
 ("Plastic018B disp", "Plastic018B/Plastic018B_2K-JPG_Displacement.jpg", None, "L"),
]
for label, rel, tile_mm, ch in sets:
    p = os.path.join(root, rel)
    if not os.path.exists(p):
        print(f"{label:28s} MISSING {rel}"); continue
    im = Image.open(p).convert("L")
    a = np.asarray(im, dtype=np.float64)
    n = min(a.shape); a = a[:n, :n]
    a -= a.mean()
    w = np.hanning(n)[:, None] * np.hanning(n)[None, :]
    F = np.abs(np.fft.fftshift(np.fft.fft2(a * w)))**2
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c)
    F[r < 6] = 0  # drop DC and the lowest frequencies (> n/6 px periods)
    # top 3 distinct peaks (frequency index -> repeats per tile)
    flat = np.argsort(F.ravel())[::-1]
    peaks = []
    for idx in flat[:4000]:
        y, x = divmod(idx, n)
        fy, fx = y - c, x - c
        if fy < 0 or (fy == 0 and fx < 0):
            continue  # use half-plane
        if any(abs(fy - py) <= 3 and abs(fx - px) <= 3 for py, px in peaks):
            continue
        peaks.append((fy, fx))
        if len(peaks) == 3: break
    # radial power: frequency of max of radially averaged spectrum
    rb = r.astype(int)
    prof = np.bincount(rb.ravel(), F.ravel()) / np.maximum(np.bincount(rb.ravel()), 1)
    rmax = int(np.argmax(prof[6:n//2])) + 6
    out = []
    for fy, fx in peaks:
        f = np.hypot(fy, fx); ang = np.degrees(np.arctan2(fy, fx))
        per_px = n / f
        s = f"rep/tile {f:6.1f} per {per_px:6.1f}px ang {ang:5.0f}"
        if tile_mm: s += f" = {tile_mm/f:5.2f} mm"
        out.append(s)
    rad = f"radial peak {rmax} rep/tile ({n/rmax:.1f}px" + (f", {tile_mm/rmax:.2f} mm)" if tile_mm else ")")
    print(f"{label:28s} n={n} | " + " | ".join(out) + " | " + rad)
