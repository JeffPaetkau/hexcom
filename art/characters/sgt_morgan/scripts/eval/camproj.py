"""Camera maths for the hero frame and its crops, numpy only (spec 17 §2.1, §4.3; spec 18 §4.8.2).

No bpy, so the overlay, the metrics, the contact sheets and Blender itself share one set of formulas
and a pixel means the same thing everywhere. Image coordinates are continuous, x right and y down
over the 1672 x 941 reference: pixel index p covers [p, p + 1) and has its centre at p + 0.5, so a
projected point is compared with reference pixel p at p + 0.5. Cameras follow Blender: they look down
their local -Z with +Y up, Euler angles are XYZ, and shift is in units of the fitted sensor side.

  python scripts/eval/camproj.py          (self-test of the numbers spec 17 and 18 quote)
"""
import math

import numpy as np

W, H = 1672, 941                                   # the reference frame
LENS_MM, SENSOR_MM = 46.0, 36.0                    # horizontal sensor fit
F_PX = LENS_MM / SENSOR_MM * W                     # 2136.44 px
CX, CY = W / 2.0, H / 2.0                          # principal point of the unshifted hero camera
HERO_LOC = (0.0, -4.50, 0.60)                      # metres
HERO_ROT_DEG = (93.9, 0.0, 0.0)                    # 3.9 degrees above level (D5: pitched, not shifted)
PITCH_DEG = HERO_ROT_DEG[0] - 90.0
FOCUS = (0.0, 0.0, 1.30)                           # Scene.Cam.Focus
CLIP = (0.05, 120.0)
HORIZON_Y = CY + F_PX * math.tan(math.radians(PITCH_DEG))   # 616.1


def euler_xyz(rx, ry, rz):
    """Blender's XYZ Euler (radians) as a matrix: X is applied first, so R = Rz Ry Rx."""
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def look_at_matrix(pos, target, up=(0.0, 0.0, 1.0)):
    """World-from-camera rotation for a camera at pos looking at target, `up` as the image's up."""
    pos, target, up = (np.asarray(v, float) for v in (pos, target, up))
    f = target - pos
    n = np.linalg.norm(f)
    if n < 1e-9:
        raise ValueError("camera position and target coincide")
    f /= n
    r = np.cross(f, up)
    if np.linalg.norm(r) < 1e-6:
        raise ValueError(f"up {tuple(up)} is parallel to the view direction {tuple(np.round(f, 3))}")
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return np.stack([r, u, -f], axis=1)            # columns: camera +X, +Y, +Z in world


class Camera:
    """A pinhole or orthographic camera sized in pixels, in Blender's conventions.

    R is the world-from-camera rotation (columns are the camera's axes in world), loc its position.
    Perspective cameras carry f_px; orthographic ones px_per_m. (cx, cy) is the principal point in
    continuous image coordinates, y down.
    """

    def __init__(self, R, loc, width, height, cx, cy, f_px=None, px_per_m=None):
        self.R = np.asarray(R, float)
        self.loc = np.asarray(loc, float)
        self.width, self.height = width, height
        self.cx, self.cy = float(cx), float(cy)
        self.f_px, self.px_per_m = f_px, px_per_m

    @classmethod
    def blender(cls, loc, rot, width, height, lens=50.0, sensor=36.0, fit="HORIZONTAL",
                shift_x=0.0, shift_y=0.0, ortho_scale=None):
        """From Blender's camera settings. rot is an XYZ Euler in radians or a 3 x 3 matrix; sensor is
        the size of the fitted side (sensor_width for HORIZONTAL and AUTO, sensor_height for VERTICAL)."""
        R = np.asarray(rot, float)
        if R.shape != (3, 3):
            R = euler_xyz(*rot)
        side = {"HORIZONTAL": width, "VERTICAL": height}.get(fit, max(width, height))
        cx = width / 2.0 - shift_x * side
        cy = height / 2.0 + shift_y * side
        if ortho_scale:
            return cls(R, loc, width, height, cx, cy, px_per_m=side / ortho_scale)
        return cls(R, loc, width, height, cx, cy, f_px=lens / sensor * side)

    @property
    def ortho(self):
        return self.px_per_m is not None

    def to_camera(self, P):
        """World points (N, 3) in camera coordinates (x right, y up, z back)."""
        return (np.atleast_2d(np.asarray(P, float)) - self.loc) @ self.R

    def project(self, P, depth=False):
        """World points (N, 3) to continuous pixels (N, 2); with depth=True also the distance along
        the optical axis (negative behind the camera)."""
        Pc = self.to_camera(P)
        d = -Pc[:, 2]
        if self.ortho:
            x = self.cx + Pc[:, 0] * self.px_per_m
            y = self.cy - Pc[:, 1] * self.px_per_m
        else:
            with np.errstate(divide="ignore", invalid="ignore"):
                x = self.cx + self.f_px * Pc[:, 0] / d
                y = self.cy - self.f_px * Pc[:, 1] / d
        xy = np.stack([x, y], axis=1)
        return (xy, d) if depth else xy

    def ray(self, xy):
        """Origins and unit directions (N, 3) of the rays through continuous pixels xy (N, 2)."""
        xy = np.atleast_2d(np.asarray(xy, float))
        n = len(xy)
        if self.ortho:
            o = np.stack([(xy[:, 0] - self.cx) / self.px_per_m, -(xy[:, 1] - self.cy) / self.px_per_m,
                          np.zeros(n)], axis=1)
            return self.loc + o @ self.R.T, np.tile(-self.R[:, 2], (n, 1))
        dc = np.stack([(xy[:, 0] - self.cx) / self.f_px, -(xy[:, 1] - self.cy) / self.f_px, -np.ones(n)], axis=1)
        dw = dc @ self.R.T
        return np.tile(self.loc, (n, 1)), dw / np.linalg.norm(dw, axis=1, keepdims=True)

    def floor_point(self, xy, z=0.0):
        """Where the rays through pixels xy meet the plane Z = z; NaN where they miss it in front."""
        o, d = self.ray(xy)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (z - o[:, 2]) / d[:, 2]
        P = o + d * t[:, None]
        P[~(t > 0)] = np.nan
        return P

    def crop(self, box, scale=1.0):
        """The equivalent crop camera of this one for box (x0, y0, x1, y1) at scale (spec 18 §4.8.2):
        same centre of projection and rotation, focal length and principal point rescaled."""
        x0, y0, x1, y1 = box
        if self.ortho:
            return Camera(self.R, self.loc, round((x1 - x0) * scale), round((y1 - y0) * scale),
                          (self.cx - x0) * scale, (self.cy - y0) * scale, px_per_m=self.px_per_m * scale)
        return Camera(self.R, self.loc, round((x1 - x0) * scale), round((y1 - y0) * scale),
                      (self.cx - x0) * scale, (self.cy - y0) * scale, f_px=self.f_px * scale)


def hero():
    """`Scene.Cam.Hero` (spec 17 §2.1): (0, -4.50, 0.60) m, rotation (93.9, 0, 0) deg, 46 mm on 36 mm."""
    return Camera.blender(HERO_LOC, [math.radians(a) for a in HERO_ROT_DEG], W, H, LENS_MM, SENSOR_MM)


HERO = hero()


def project(P):
    """World points through the hero camera, continuous pixels (spec 17 §4.3's formula)."""
    return HERO.project(P)


def floor_point(x, y):
    """The floor point (X, Y, 0) seen at continuous hero pixel (x, y)."""
    return HERO.floor_point([[x, y]])[0]


def box_size(box, scale=1.0):
    """Output size of a box at a scale, refusing fractional pixels (they would shift the crop)."""
    x0, y0, x1, y1 = box
    w, h = (x1 - x0) * scale, (y1 - y0) * scale
    if abs(w - round(w)) > 1e-6 or abs(h - round(h)) > 1e-6:
        raise ValueError(f"box {box} at scale {scale} gives {w} x {h} px; choose a scale with whole pixels")
    return int(round(w)), int(round(h))


def check_box(box, width=W, height=H):
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError(f"box {box} is not inside the {width} x {height} frame")


def crop_params(box, scale=1.0, lens=LENS_MM, sensor=SENSOR_MM, width=W, cx=CX, cy=CY):
    """Blender settings of the equivalent crop camera (spec 18 §4.8.2) for a box of the hero frame:
    lens' = lens * W / w, shift in units of the crop width under horizontal fit, resolution (w s, h s)."""
    check_box(box)
    x0, y0, x1, y1 = box
    w = x1 - x0
    return {"lens": lens * width / w, "sensor": sensor, "fit": "HORIZONTAL",
            "shift_x": ((x0 + x1) / 2.0 - cx) / w, "shift_y": (cy - (y0 + y1) / 2.0) / w,
            "res": box_size(box, scale)}


def border_params(box, width=W, height=H):
    """Blender's render border for a box (x1, y1 exclusive), as fractions with y up (spec 17 §4.3)."""
    check_box(box, width, height)
    x0, y0, x1, y1 = box
    return {"min_x": x0 / width, "max_x": x1 / width, "min_y": (height - y1) / height, "max_y": (height - y0) / height}


def to_crop(xy, box, scale=1.0):
    """Full-frame continuous pixels to the crop's continuous pixels."""
    return (np.asarray(xy, float) - np.array(box[:2], float)) * scale


def selftest():
    """The numbers the specs quote, checked without Blender (the bpy comparison is camera.py's)."""
    R = {}
    R["f_px"] = round(F_PX, 2)
    assert abs(F_PX - 2136.4) < 0.1
    R["horizon_y"] = round(HORIZON_Y, 2)
    assert abs(HORIZON_Y - 616.1) < 0.05, HORIZON_Y
    far = HERO.project([[0.0, 1e6, HERO_LOC[2]]])[0]
    assert abs(far[1] - HORIZON_Y) < 0.01
    lamp = HERO.project([[1.50, 7.00, 1.70]])[0]             # landing lamp, spec 17 §1.4 item 1
    R["landing_lamp"] = [round(v, 2) for v in lamp]
    assert abs(lamp[0] - 1113.5) < 0.5 and abs(lamp[1] - 412.2) < 0.5, lamp
    origin = HERO.project([[0.0, 0.0, 0.0]])[0]               # the floor under the origin, §2.1 table
    R["origin_floor_y"] = round(origin[1], 2)
    assert abs(origin[1] - 905.0) < 0.5
    for y, Y in ((941, -0.49), (850, 1.05), (746, 5.46), (690, 12.98)):
        P = floor_point(836.0, float(y))
        assert abs(P[1] - Y) < 0.01, (y, P)
        assert np.allclose(HERO.project([P])[0], (836.0, y), atol=1e-6)
    cp = crop_params((715, 30, 885, 200), 5)                  # p18.V1: ref.head_face
    R["head_face_crop"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in cp.items()}
    assert abs(cp["lens"] - 452.42) < 0.01 and abs(cp["shift_x"] + 0.2118) < 1e-4 and abs(cp["shift_y"] - 2.0912) < 1e-4
    assert cp["res"] == (850, 850)
    cp = crop_params((580, 20, 1020, 935), 1)                 # p18.V2: ref.soldier_full at x1
    assert abs(cp["lens"] - 174.80) < 0.01 and abs(cp["shift_x"] + 0.0818) < 1e-4 and abs(cp["shift_y"] + 0.0159) < 1e-4
    # the equivalent camera rebuilt from its Blender settings agrees with the cropped hero projection
    rng = np.random.default_rng(17)
    P = np.stack([rng.uniform(-1, 1, 50), rng.uniform(-1, 3, 50), rng.uniform(0, 2, 50)], axis=1)
    for box, s in (((715, 30, 885, 200), 5), ((610, 750, 1010, 935), 3), ((580, 20, 1020, 935), 2)):
        cp = crop_params(box, s)
        cam = Camera.blender(HERO_LOC, [math.radians(a) for a in HERO_ROT_DEG], *cp["res"], cp["lens"],
                             cp["sensor"], cp["fit"], cp["shift_x"], cp["shift_y"])
        err = np.abs(cam.project(P) - to_crop(HERO.project(P), box, s)).max()
        assert err < 1e-6, (box, err)
        assert np.abs(HERO.crop(box, s).project(P) - cam.project(P)).max() < 1e-6
    R["border_boots"] = border_params((610, 750, 1010, 935))
    return R


if __name__ == "__main__":
    import json
    print(json.dumps(selftest(), indent=1))
    print("camproj selftest: ok")
