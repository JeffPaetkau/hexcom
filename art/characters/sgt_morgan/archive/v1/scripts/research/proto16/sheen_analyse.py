import bpy, sys, os, numpy as np
out = sys.argv[sys.argv.index("--")+1]; name = sys.argv[sys.argv.index("--")+2]
img = bpy.data.images.load(os.path.join(out, name))
W, H = img.size; px = np.array(img.pixels[:]).reshape(H, W, 4)[..., :3]
Y = 0.2126*px[...,0] + 0.7152*px[...,1] + 0.0722*px[...,2]
weights = [0.0, 0.04, 0.08, 0.12, 0.20, 0.35]
yy, xx = np.mgrid[0:H, 0:W]
for row in range(2):
    vals = []
    for i in range(6):
        cx = W/2 + (-0.6 + i*0.24) * 480; cy = (H - 1) - (H/2 + (0.12 - row*0.24) * 480)  # image rows bottom-up in pixels[]
        r = np.hypot(xx-cx, yy-cy) / (0.1*480); ang = np.degrees(np.arctan2(yy-cy, xx-cx))
        core = Y[r < 0.5].mean(); allm = Y[r < 0.97].mean()
        litrim = Y[(r > 0.85) & (r < 0.97) & (ang > 100) & (ang < 170)].mean()
        vals.append((core, litrim, allm))
    c0, l0, a0 = vals[0]
    print("ROW", ["white","tint"][row], " | ".join(f"{weights[i]}: core x{v[0]/c0:.2f} litrim x{v[1]/l0:.2f} disc x{v[2]/a0:.2f}" for i, v in enumerate(vals)))
