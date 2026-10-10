"""sRGB <-> linear helpers for the spec tables (system python)."""
import numpy as np
def h2l(h):
    c = np.array([int(h[i:i+2], 16)/255 for i in (1,3,5)])
    return np.where(c <= 0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
def l2h(l):
    l = np.clip(np.asarray(l, float), 0, 1)
    c = np.where(l <= 0.0031308, 12.92*l, 1.055*l**(1/2.4)-0.055)
    return "#" + "".join(f"{int(round(x*255)):02x}" for x in c)
def Y(l): return float(0.2126*l[0]+0.7152*l[1]+0.0722*l[2])
def scale_to_Y(h, y):
    l = h2l(h); return l * (y / Y(l))
