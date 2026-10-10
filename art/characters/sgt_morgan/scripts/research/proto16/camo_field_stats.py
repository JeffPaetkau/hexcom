"""Quantiles and edge statistics of the baked camo field F (2 m square at 1024 px). Run in Blender."""
import bpy, sys, os, json, numpy as np
out = sys.argv[sys.argv.index("--")+1]
img = bpy.data.images.load(os.path.join(out, "F_2m.exr"))
w, h = img.size
F = np.array(img.pixels[:], dtype=np.float64).reshape(h, w, 4)[..., 0]
mm_per_px = 2000.0 / w  # 2 m plane, UV 0..1
q = np.quantile(F, [0.30, 0.65, 0.90])
gy, gx = np.gradient(F, mm_per_px)
g = np.hypot(gx, gy)
res = {"mean": float(F.mean()), "std": float(F.std()), "min": float(F.min()), "max": float(F.max()),
       "q30_65_90": [round(float(x), 4) for x in q]}
for k, t in enumerate(q):
    band = np.abs(F - t) < 0.002
    res[f"grad_at_cut{k+1}_per_mm_p25_50_75"] = [round(float(x), 5) for x in np.percentile(g[band], [25, 50, 75])]
print("FIELD", json.dumps(res))
json.dump(res, open(os.path.join(out, "field_stats.json"), "w"))
