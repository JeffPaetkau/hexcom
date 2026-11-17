"""Face proportions from MediaPipe on head crops (head round 11b, head.md section 14): the reference's hero crop,
the model's hero crop, R001's views. 2D ratios in each image's own pixels, so the same view compares directly.

  "$SGT_PYIMG" -I scripts/tools/head_face_measure.py name=png [name=png ...] [--json out.json]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MP_MODEL = os.path.join(PROJECT, "assets", "ai", "mediapipe", "face_landmarker.task")
_DET = None


def detect(png):
    global _DET
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
    if _DET is None:
        _DET = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_buffer=open(MP_MODEL, "rb").read()), num_faces=1,
            output_face_blendshapes=True))
    im = Image.open(png).convert("RGB")
    arr = np.ascontiguousarray(np.array(im))
    res = _DET.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=arr))
    if not res.face_landmarks:
        return None, None, arr
    h, w = arr.shape[:2]
    bs = {c.category_name: round(c.score, 3) for c in res.face_blendshapes[0]} if res.face_blendshapes else {}
    return np.array([(p.x * w, p.y * h) for p in res.face_landmarks[0]]), bs, arr


def hairline(arr, P):
    """Along the face's own up axis (chin 152 -> glabella 9), from the glabella upward: the first point where the
    luminance falls under the midpoint of the forehead's and the hair's levels. Returned as a distance in px."""
    up = P[9] - P[152]
    L = np.linalg.norm(up)
    up = up / L
    lum = arr.astype(float) @ np.array([0.2126, 0.7152, 0.0722])
    h, w = lum.shape
    out = {}
    for name, off in (("mid", 0.0), ("near", -0.22), ("far", 0.22)):
        side = np.array([up[1], -up[0]]) * off * L          # lateral offset, + = image right
        prof = []
        for t in np.arange(0.0, 1.2 * L, 0.5):
            q = P[9] + side + up * t
            x, y = int(round(q[0])), int(round(q[1]))
            if not (0 <= x < w and 0 <= y < h):
                break
            prof.append(lum[max(0, y - 1):y + 2, max(0, x - 1):x + 2].mean())
        prof = np.array(prof)
        if len(prof) < 20:
            out[name] = None
            continue
        skin = np.median(prof[int(0.1 * L / 0.5):int(0.3 * L / 0.5)])
        hair = np.percentile(prof[int(0.3 * L / 0.5):], 10)
        thr = 0.5 * (skin + hair)
        k = np.where(prof[int(0.2 * L / 0.5):] < thr)[0]
        out[name] = float((k[0] + int(0.2 * L / 0.5)) * 0.5) if len(k) else None
    return out


def measures(P, arr):
    d = lambda a, b: float(np.linalg.norm(P[a] - P[b]))
    up = (P[9] - P[152]) / np.linalg.norm(P[9] - P[152])
    v = lambda a, b: float((P[a] - P[b]) @ up)               # how far a sits above b along the face's up axis
    m = {}
    brow_y = 0.5 * (P[105] + P[334])                          # mid-brow, upper row
    chin = P[152]
    brow_chin = float((brow_y - chin) @ up)
    m["face_w_over_h"] = d(234, 454) / d(10, 152)
    m["bizyg_over_browchin"] = d(234, 454) / brow_chin
    m["bigonial_over_bizyg"] = d(172, 397) / d(234, 454)
    m["jaw58_288_over_bizyg"] = d(58, 288) / d(234, 454)
    m["chin_w_over_bizyg"] = d(176, 400) / d(234, 454)
    hl = hairline(arr, P)
    for k, t in hl.items():
        m[f"browhair_over_browchin_{k}"] = None if t is None else (t - float((brow_y - P[9]) @ up)) / brow_chin
    for side, (o, i, top, bot, bl, bu_in, bu_mid, bu_out) in (("near_R", (33, 133, 159, 145, 52, 55, 105, 70)), ("far_L", (263, 362, 386, 374, 282, 285, 334, 300))):
        ew = d(o, i)
        m[f"eye_aperture_{side}"] = d(top, bot) / ew
        m[f"browlow_to_lid_{side}"] = v(bl, top) / ew        # lower brow row above the upper lid margin
        m[f"browtop_to_lid_{side}"] = v(bu_mid, top) / ew
        # arch: mid-brow above the line from the inner to the outer brow point, over the brow's length
        a, b, c = P[bu_in], P[bu_out], P[bu_mid]
        ab = b - a
        m[f"brow_arch_{side}"] = float(abs(ab[0] * (c - a)[1] - ab[1] * (c - a)[0]) / (ab @ ab))
        m[f"brow_tilt_{side}"] = (v(bu_out, bu_in)) / ew      # + = the tail higher than the head
    m["nose_len_over_browchin"] = v(9, 2) / brow_chin
    m["lowerface_over_browchin"] = v(2, 152) / brow_chin
    m["mouth_w_over_bizyg"] = d(61, 291) / d(234, 454)
    return {k: (None if x is None else round(x, 3)) for k, x in m.items()}


def main(argv):
    out = {}
    js = None
    if "--json" in argv:
        i = argv.index("--json")
        js = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    for a in argv:
        name, png = a.split("=", 1)
        P, bs, arr = detect(png)
        if P is None:
            print(name, "no face")
            continue
        out[name] = measures(P, arr)
        out[name]["_bs"] = {k: bs[k] for k in ("browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight", "eyeSquintLeft", "eyeSquintRight", "eyeBlinkLeft", "eyeBlinkRight", "eyeWideLeft", "eyeWideRight") if k in bs}
    keys = [k for k in next(iter(out.values())) if not k.startswith("_")]
    names = list(out)
    print(f"{'measure':34s}" + "".join(f"{n:>12s}" for n in names))
    for k in keys:
        print(f"{k:34s}" + "".join(f"{str(out[n].get(k)):>12s}" for n in names))
    for n in names:
        print(n, out[n]["_bs"])
    if js:
        json.dump(out, open(js, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])


# --------------------------------------------------------------------------- skin colour at landmark patches
PATCH = {"forehead": (151,), "nose_dorsum": (197,), "near_cheek_lit": (50, 205), "near_zygoma": (116, 117), "under_eye_near": (119, 230),
         "near_jaw_halflit": (172, 136, 150), "near_lower_cheek": (213, 192), "chin_pad": (175, 199), "moustache": (164,),
         "far_cheek_shadow": (280, 425), "under_eye_far": (348, 450), "far_jaw": (365, 379), "temple_near": (21, 71),
         "under_brow_near": (52, 159), "under_brow_far": (282, 386), "upper_lid_near": (159, 160, 158), "glabella": (9,)}


def colours(P, arr, r=9):
    import colorsys
    s = arr.shape[1] / 850.0
    out = {}
    for k, ids in PATCH.items():
        c = P[list(ids)].mean(0)
        x, y, q = int(round(c[0])), int(round(c[1])), max(2, int(round(r * s)))
        px = arr[max(0, y - q):y + q + 1, max(0, x - q):x + q + 1].reshape(-1, 3).astype(float)
        m = px.mean(0)
        h, sat, v = colorsys.rgb_to_hsv(*(m / 255.0))
        out[k] = {"hex": "#%02x%02x%02x" % tuple(int(round(t)) for t in m), "hue": round(h * 360.0, 1), "sat": round(sat, 3), "val": round(v, 3)}
    return out


def colour_main(argv):
    res = {}
    for a in argv:
        name, png = a.split("=", 1)
        P, _, arr = detect(png)
        res[name] = colours(P, arr)
    names = list(res)
    print(f"{'patch':20s}" + "".join(f"{n:>30s}" for n in names))
    for k in PATCH:
        print(f"{k:20s}" + "".join(f"{res[n][k]['hex'] + ' h%5.1f s%.2f v%.2f' % (res[n][k]['hue'], res[n][k]['sat'], res[n][k]['val']):>30s}" for n in names))
    return res
