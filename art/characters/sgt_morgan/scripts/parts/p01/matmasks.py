"""The material masks of spec 01 §3.4 and §4.6 on Body.Mesh: the layers spec 16's Skin.Foot reads by name (callus at
the heel rim, the ball, the 5th MTP and the hallux's IP; the left 4th toe's corn; the Achilles rub; the pressure pink;
the toes' redness; the thin dorsum; the scatter scale). Each is the smoothstep of a distance to a shape placed on this
foot's own landmarks (its joint cubes, which follow the scan-transferred toes, and its pternion), not on §3.4's
coordinates for the 285 mm foot of the first draft, so they sit where this foot's bones are. Frame F mm; the right
foot reads the same in its mirrored frame.
"""
import numpy as np

from lib import sculpt as S

NAMES = ("Foot.Callus.Heel", "Foot.Callus.Ball", "Foot.Callus.MTP5", "Foot.Callus.Hallux", "Foot.Corn.L4",
         "Foot.Rub.Achilles", "Foot.Pressure", "Foot.ToeRed", "Foot.DorsumThin", "Foot.SSSScale")


def _ell(q, c, r):
    """1 inside an ellipsoid of semi-axes r about c, falling to 0 between 0.6 and 1.0 of it."""
    d = np.sqrt((((q - np.asarray(c, float)) / np.asarray(r, float)) ** 2).sum(axis=1))
    return 1.0 - S.smoothstep(d, 0.6, 1.0)


def landmarks(q_cubes):
    """{name: F point} from the joint cubes' centroids ({"toe-1-1": (x, y, z), ...})."""
    return {k: np.asarray(v, float) for k, v in q_cubes.items()}


def masks(q, nrm, toe_w, joints, side):
    """{mask name: weights} for one foot's region: q (n, 3) F mm, nrm (n, 3) F normals, toe_w {k: (n,)} each toe's
    deform weight (summed over its bones), joints {cube name: F point}."""
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    sm = S.smoothstep
    toes = np.clip(sum(toe_w.values()), 0.0, 1.0)
    plantar = sm(-nrm[:, 2], 0.3, 0.6) * (1.0 - sm(z, 8.0, 14.0))
    out = {}
    # the heel rim (§3.4 callus 1): the outer 15 mm of the heel's underside, from the medial back round the back to
    # the lateral side, up to z 12
    heel = q[(y > -60.0) & (z < 12.0)]
    xc = float(0.5 * (heel[:, 0].min() + heel[:, 0].max())) if len(heel) else 0.0
    yc = -30.0
    th = np.degrees(np.arctan2(x - xc, y - yc))
    r = np.hypot(x - xc, y - yc)
    ang = sm(th, -60.0, -45.0) * (1.0 - sm(th, 90.0, 105.0))
    out["Foot.Callus.Heel"] = ang * sm(r, 15.0, 21.0) * (1.0 - sm(z, 10.0, 14.0)) * (y > -70.0)
    m1, m2, m5 = joints["toe-1-1"], joints["toe-2-1"], joints["toe-5-1"]
    # under the 1st-2nd metatarsal heads (callus 2): a 32 x 22 ellipse, on the sole
    cb = np.array([0.6 * m1[0] + 0.4 * m2[0], 0.5 * (m1[1] + m2[1]), 0.0])
    out["Foot.Callus.Ball"] = _ell(q, cb, (16.0, 11.0, 7.0)) * plantar
    # the lateral 5th MTP (callus 3), wrapping onto the border
    lat5 = q[(np.abs(y - m5[1]) < 6.0) & (z < 25.0)]
    x5 = float(lat5[:, 0].max()) if len(lat5) else m5[0] + 8.0
    out["Foot.Callus.MTP5"] = _ell(q, (x5, m5[1], 5.0), (10.0, 10.0, 9.0))
    # the medial hallux IP (callus 4, the pinch callus): 14 x 10 on the medial side of the joint
    ip = joints["toe-1-2"]
    med = q[(np.abs(y - ip[1]) < 4.0) & (toe_w[1] > 0.5)]
    xm = float(med[:, 0].min()) if len(med) else ip[0] - 15.0
    out["Foot.Callus.Hallux"] = _ell(q, (xm, ip[1], 10.0), (6.0, 7.0, 5.0)) * (toe_w[1] > 0.3)
    # the left 4th toe's dorsal corn over its PIP (§3.3's asymmetry)
    if side == "L":
        pip = joints["toe-4-2"]
        top = q[(np.hypot(x - pip[0], y - pip[1]) < 4.0) & (toe_w[4] > 0.5)]
        zt = float(top[:, 2].max()) if len(top) else pip[2] + 7.0
        out["Foot.Corn.L4"] = _ell(q, (pip[0], pip[1], zt), (3.5, 3.5, 3.0)) * (toe_w[4] > 0.3)
    # the Achilles rub (sock-and-boot friction): an oval 22 x 30 over z 45-70 at the back
    back = q[(np.abs(z - 57.0) < 3.0) & (np.abs(x - xc) < 10.0)]
    yb = float(back[:, 1].max()) if len(back) else 0.0
    out["Foot.Rub.Achilles"] = _ell(q, (xc, yb, 57.0), (11.0, 9.0, 15.0)) * sm(nrm[:, 1], 0.2, 0.5)
    # pressure pink: the heel's centre, the ball, the toes' pads
    ball = _ell(q, (0.5 * (m1[0] + m5[0]), 0.5 * (m1[1] + m5[1]) - 4.0, 0.0), (45.0, 18.0, 8.0))
    pads = np.zeros(len(q))
    for k, w in toe_w.items():
        mt, tip = joints.get(f"toe-{k}-1"), joints.get(f"toe-{k}-{3 if k == 1 else 4}")
        if mt is None or tip is None:
            continue
        a = tip[:2] - mt[:2]
        t = ((q[:, :2] - mt[:2]) @ a) / max(float(a @ a), 1e-9)
        pads = np.maximum(pads, w * sm(t, 0.55, 0.8))
    out["Foot.Pressure"] = np.maximum(np.maximum(_ell(q, (xc, yc, 0.0), (27.0, 24.0, 8.0)), ball), pads) * plantar
    # the toes' redness: the distal 60 % of each toe, full at the tips
    red = np.zeros(len(q))
    for k, w in toe_w.items():
        mt, tip = joints.get(f"toe-{k}-1"), joints.get(f"toe-{k}-{3 if k == 1 else 4}")
        if mt is None or tip is None:
            continue
        a = tip[:2] - mt[:2]
        t = ((q[:, :2] - mt[:2]) @ a) / max(float(a @ a), 1e-9)
        red = np.maximum(red, w * sm(t, 0.4, 1.05))
    out["Foot.ToeRed"] = red
    # the thin skin of the dorsum and ankle, above z 20, the toes left out
    out["Foot.DorsumThin"] = sm(z, 18.0, 24.0) * (1.0 - toes) * (1.0 - plantar)
    # the scatter's scale: 0.65 on the toes (no glow), 0.7 on the sole, 1 elsewhere
    out["Foot.SSSScale"] = 1.0 - 0.35 * toes - 0.3 * plantar * (1.0 - toes)
    return out
