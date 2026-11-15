"""Invert spec 17's display chain (AgX 'Medium High Contrast' via Blender's OCIO, then the grade of 17 §5.6)
for lit reference hexes -> scene-linear Rec.709 radiance. Run inside Blender (PyOpenColorIO)."""
import bpy, os, sys, numpy as np
import PyOpenColorIO as OCIO
cfgp = os.path.join(bpy.utils.resource_path('LOCAL'), 'datafiles', 'colormanagement', 'config.ocio')
cfg = OCIO.Config.CreateFromFile(cfgp)
names = [cs.getName() for cs in cfg.getColorSpaces()]
src = 'Linear Rec.709' if 'Linear Rec.709' in names else names[0]
looks = [l.getName() for l in cfg.getLooks()]
print("CFG", cfgp, "SRC", src, "LOOKS", [l for l in looks if 'AgX' in l])
def proc(look):
    t = OCIO.DisplayViewTransform(); t.setSrc(src); t.setDisplay('sRGB'); t.setView('AgX')
    lv = OCIO.LegacyViewingPipeline(); lv.setDisplayViewTransform(t)
    lv.setLooksOverrideEnabled(True); lv.setLooksOverride(look)
    return lv.getProcessor(cfg).getDefaultCPUProcessor()
P = proc('AgX - Medium High Contrast')
def agx(rgb):
    a = np.array(rgb, dtype=np.float32).reshape(1, 3).copy()
    P.applyRGB(a); return a.reshape(3).astype(float)
lift = np.array([0.985, 1.0, 1.025]); gain = np.array([1.035, 1.0, 0.960])
def grade(d):
    x = ((d - 1.0) * (2.0 - lift) + 1.0) * gain
    x = np.clip(x, 0, 1)
    Y = 0.2126 * x[0] + 0.7152 * x[1] + 0.0722 * x[2]
    x = Y + 0.92 * (x - Y)
    return np.clip((x - 0.02) / 0.98, 0, 1)
def chain(s): return grade(agx(s))
# check the grey table of spec 17 (MHC, before grade)
for g in (0.01, 0.02, 0.05, 0.18, 0.5, 1.0):
    print("GREY", g, round(float(agx([g, g, g])[1]) * 255, 1))
def inv(hexs):
    t = np.array([int(hexs[i:i+2], 16) for i in (1, 3, 5)], float) / 255.0
    s = np.full(3, 0.05)
    for it in range(40):
        f = chain(s) - t
        J = np.zeros((3, 3)); h = 1e-4
        for j in range(3):
            ds = np.zeros(3); ds[j] = max(h, s[j] * 1e-3)
            J[:, j] = (chain(s + ds) - chain(s)) / ds[j]
        try: step = np.linalg.solve(J, f)
        except np.linalg.LinAlgError: break
        s = np.clip(s - step, 1e-5, 50)
        if np.abs(f).max() < 2e-4: break
    return s, chain(s) * 255
targets = sys.argv[sys.argv.index("--") + 1].split(",")
for h in targets:
    s, d = inv(h)
    Y = 0.2126 * s[0] + 0.7152 * s[1] + 0.0722 * s[2]
    print(f"INV {h} -> scene ({s[0]:.4f}, {s[1]:.4f}, {s[2]:.4f}) Y {Y:.4f}  check {d.round(1)}")
