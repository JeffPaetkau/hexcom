"""Strongest period along each image axis (x = columns/U, y = rows/V) for chosen maps."""
import sys, os, numpy as np
from PIL import Image
root = sys.argv[1]
for label, rel, tile_mm in [
 ("cotton_jersey", "cotton_jersey/cotton_jersey_disp_2k.jpg", 264),
 ("knitted_fleece", "knitted_fleece/knitted_fleece_disp_2k.jpg", 266),
 ("poly_wool_herringbone", "poly_wool_herringbone/poly_wool_herringbone_disp_2k.jpg", 270),
 ("Fabric063", "Fabric063/Fabric063_2K-JPG_Displacement.jpg", 400),
 ("Fabric061", "Fabric061/Fabric061_2K-JPG_Displacement.jpg", 400),
 ("Leather032", "Leather032/Leather032_2K-JPG_Displacement.jpg", 450),
 ("Rubber004", "Rubber004/Rubber004_2K-JPG_Displacement.jpg", 750)]:
    a = np.asarray(Image.open(os.path.join(root, rel)).convert("L"), dtype=float)
    n = min(a.shape); a = a[:n, :n] - a[:n, :n].mean()
    # 1-D spectra: average |FFT| of rows (period along x) and of columns (period along y)
    win = np.hanning(n)
    sx = (np.abs(np.fft.rfft(a * win[None, :], axis=1))**2).mean(0)
    sy = (np.abs(np.fft.rfft(a * win[:, None], axis=0))**2).mean(1)
    res = []
    for name, s in (("x", sx), ("y", sy)):
        s = s.copy(); s[:8] = 0
        k = int(np.argmax(s))
        res.append(f"{name}: {k} rep/tile = {n/k:.1f}px = {tile_mm/k:.2f} mm")
    print(f"{label:22s} " + " | ".join(res))
