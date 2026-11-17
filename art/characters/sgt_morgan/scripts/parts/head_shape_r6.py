"""Head shape round 6 (scripts/parts/head.md §14): a longer, leaner face, on top of round 5 (not wired).

Round 11's critics: "broad, flat and square ... where the reference has a long lean face ... hollow cheeks" (m2), "a
very wide square jaw; the head reads boxy" (m17). MediaPipe on the reference's hero crop and on round 11's
(scripts/tools/head_face_measure.py) agrees: at the same height the model's face is about 6 % wider at every level
(temples, zygomata, gonia: 9-13 crop px a side, 4-6 mm), and its chin sits 3 mm short under the mouth. So, as in
round 5, explicit symmetric displacement fields on the wired face (round 5's), skin vertices only:

  narrow   the head's sides come in towards the midline: x scaled by narrow_k beyond |x| 40 mm (ears and the skull
           behind them too, so the ears stay on the head), fading out under the jaw's border and round the eyeballs
  chin     the chin drops chin_mm
  hollow   the cheek under the zygoma sits in a further hollow_mm along the normal
  gonial   the mandible's angle is rounded: in and up
  brow_back, hood   the ridge goes back and the skin under it comes forward, so that the key reaches it
  browlift the brow's ridge rises 5 mm at the head and middle, 2 mm at the tail (the lid margin stays)

No helper geometry and no joint cube moves, so the rig, the eye bones and the MHCLO fits come out unchanged.
Developed in memory as a shape key on an opened base.blend; `head-shape.target` and base.py are untouched.

  "$SGT_BLENDER" -b --python scripts/parts/head_shape_r6.py -- --measure     # r5 against r6, cache/head_r6/measure.json
  "$SGT_BLENDER" -b --python scripts/parts/head_shape_r6.py -- --write       # scripts/parts/head-shape-r6.target
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
SCRIPTS = os.path.join(PROJECT, "scripts")
for p in (SCRIPTS, HERE, os.path.join(SCRIPTS, "stages")):
    if p not in sys.path:
        sys.path.insert(0, p)

WORK = os.path.join(PROJECT, "cache", "head_r6")
WIRED_TARGET = os.path.join(HERE, "head-shape.target")        # round 5's since round 11
R5_TARGET = os.path.join(HERE, "head-shape-r5.target")
R6_TARGET = os.path.join(HERE, "head-shape-r6.target")
R6_JSON = os.path.join(HERE, "head_shape_r6.json")

P6 = {
    "narrow_k": 0.015, "narrow_k_jaw": 0.035, "narrow_x0": 40.0, "narrow_x1": 66.0, "narrow_eye_r0": 11.0, "narrow_eye_r1": 23.0,
    "chin_mm": 2.5, "chin_sz": 14.0,
    "hollow_mm": 3.5, "hollow_sigma": 14.0,
    "temple_mm": 1.5, "temple_sigma": 13.0,
    "gonial_in_mm": 2.0, "gonial_up_mm": 2.0, "gonial_sigma": 12.0,
    "browlift_mm": ((0.0, 3.5), (13.0, 5.5), (41.5, 5.0), (55.7, 2.0), (70.0, 0.0)),      # (|x|, lift): in 5.5, mid 5.0, out 2.0
    "browlift_above": 32.0,
    "brow_back_mm": 3.5, "brow_back_sz": 5.0, "hood_mm": 2.0,
    "smooth_iters": 2,
}


def _ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def delta(C, bd, marks, P=P6):
    """The round-6 displacement of the wired (round 5) face, world mm, per Body.Mesh vertex."""
    import head as H
    import head_look as HL
    V, N, g = bd["V"], bd["N"], bd["groups"]
    region = H.head_region(bd) & bd["in_body"]
    face = region & (g["ears"] < 0.3)
    L = HL.landmarks(bd, marks)
    E = C.edges_of(bd["F"])
    parts = {}
    ax = np.abs(V[:, 0])
    sx = np.where(V[:, 0] >= 0, 1.0, -1.0)
    Vr = np.stack([-ax, V[:, 1], V[:, 2]], 1)
    ch, lb, mo, sn, pu = L["chin"], L["lip_bot"], L["mouth"], L["subnasale"], L["pupil"]
    zero = np.zeros(len(V))
    # --- narrow
    eye_c = np.array([-abs(pu[0]), pu[1] + 12.0, pu[2]])
    w = _ss(P["narrow_x0"], P["narrow_x1"], ax) * _ss(ch[2] - 5.0, ch[2] + 30.0, V[:, 2])
    w *= _ss(P["narrow_eye_r0"], P["narrow_eye_r1"], np.linalg.norm(Vr - eye_c, axis=1))
    kz = P["narrow_k_jaw"] + (P["narrow_k"] - P["narrow_k_jaw"]) * _ss(sn[2] - 10.0, pu[2] - 5.0, V[:, 2])   # more at the jaw than at the zygoma
    parts["narrow"] = np.stack([-kz * V[:, 0] * w, zero, zero], 1) * region[:, None]
    # --- temple: the temporal fossa, behind the orbit's lateral rim and above the zygomatic arch, sits in
    bo = L["brow_out"]
    tc = np.array([-abs(bo[0]) - 16.0, bo[1] + 22.0, bo[2] + 6.0])
    kk = np.argmin(np.where(face & (V[:, 0] < 0), np.linalg.norm(V - tc, axis=1), 1e9))
    w = np.exp(-0.5 * (np.linalg.norm(Vr - V[kk], axis=1) / P["temple_sigma"]) ** 2)
    parts["temple"] = -N * (w * P["temple_mm"])[:, None] * face[:, None]
    # --- chin: down
    w = np.exp(-0.5 * ((V[:, 2] - ch[2]) / P["chin_sz"]) ** 2) * _ss(58.0, 24.0, ax) * _ss(ch[1] + 45.0, ch[1] + 22.0, V[:, 1])
    w *= _ss(lb[2] + 1.0, lb[2] - 7.0, V[:, 2])
    parts["chin"] = np.stack([zero, zero, -P["chin_mm"] * w], 1) * face[:, None]
    # --- hollow: round 5's centre (under the zygoma, outside the mouth corner)
    c = np.array([mo[0] - 24.0, 0.0, 0.5 * (mo[2] + sn[2]) + 5.0])
    k = np.argmin(np.where(face & (V[:, 0] < 0), np.hypot(V[:, 0] - c[0], V[:, 2] - c[2]) + 0.5 * np.maximum(V[:, 1] + 60.0, 0), 1e9))
    c = V[k]
    w = np.exp(-0.5 * (np.linalg.norm(Vr - c, axis=1) / P["hollow_sigma"]) ** 2)
    parts["hollow"] = -N * (w * P["hollow_mm"])[:, None] * face[:, None]
    # --- gonial: the angle in and up
    ear = np.array(marks["ear_R"]["rest_mm"])
    gon = np.array([-abs(ear[0]) + 14.0, ear[1] + 3.0, ch[2] + 44.0])
    w = np.exp(-0.5 * (np.linalg.norm(Vr - gon, axis=1) / P["gonial_sigma"]) ** 2)
    parts["gonial"] = np.stack([-sx * P["gonial_in_mm"] * w, zero, P["gonial_up_mm"] * w], 1) * face[:, None]
    # --- browlift: the brow's ridge and the skin under it rise (the lower brow row is only 5-9 mm over the pupil on
    # round 5's face; the drawn one is 5 mm higher at the head and the middle, 2 mm at the tail). Nothing moves at
    # the lid's margin; the forehead above takes the lift up over browlift_above mm.
    bx = np.array([abs(L["brow_in"][0]), abs(L["brow_mid"][0]), abs(L["brow_out"][0])])
    zb = np.interp(ax, bx, [L["brow_in"][2], L["brow_mid"][2], L["brow_out"][2]])
    zl = pu[2] + 4.5 - 8.0 * ((ax - abs(pu[0])) / 15.0) ** 2            # about the upper lid's margin
    zl = np.maximum(zl, pu[2] - 14.0)
    xs_, am_ = zip(*P["browlift_mm"])
    w = _ss(0.5, 1.0, (V[:, 2] - zl) / np.maximum(zb - zl, 1.0) * 0.5 + 0.5) * (V[:, 2] <= zb) + (V[:, 2] > zb) * _ss(zb + P["browlift_above"], zb + 6.0, V[:, 2])
    w *= _ss(pu[1] + 45.0, pu[1] + 25.0, V[:, 1]) * (V[:, 2] > zl + 0.5)
    parts["browlift"] = np.stack([zero, zero, np.interp(ax, xs_, am_) * w], 1) * face[:, None]
    # --- brow_back, hood: the ridge stands 10 mm proud of the lid, so the skin under it faces down, away from the key
    # (37 degrees up), and renders as a dark band under the brow however high the brow sits. The ridge goes back and
    # the skin midway between ridge and lid comes forward: a steeper, lit slope.
    lat = _ss(6.0, 14.0, ax) * _ss(66.0, 54.0, ax) * _ss(pu[1] + 45.0, pu[1] + 25.0, V[:, 1])
    w = np.exp(-0.5 * ((V[:, 2] - zb) / P["brow_back_sz"]) ** 2) * lat
    parts["brow_back"] = np.stack([zero, P["brow_back_mm"] * w, zero], 1) * face[:, None]
    zm = 0.5 * (zb + zl)
    w = np.exp(-0.5 * ((V[:, 2] - zm) / np.maximum(0.3 * (zb - zl), 1.5)) ** 2) * lat * (V[:, 2] > zl + 1.0) * _ss(abs(L["eye_in"][0]) - 2.0, abs(L["eye_in"][0]) + 6.0, ax)
    parts["hood"] = np.stack([zero, -P["hood_mm"] * w, zero], 1) * face[:, None]
    D = sum(parts.values())
    for _ in range(P["smooth_iters"]):
        D = D + 0.5 * (C.smooth_field(D, E, iters=1, lam=1.0) - D) * region[:, None]
    D[~region] = 0.0
    stats = {k: {"max_mm": round(float(np.linalg.norm(v, axis=1).max()), 2), "verts": int((np.linalg.norm(v, axis=1) > 0.1).sum())} for k, v in parts.items()}
    stats["total"] = {"max_mm": round(float(np.linalg.norm(D, axis=1).max()), 2), "verts": int((np.linalg.norm(D, axis=1) > 0.05).sum())}
    return D, stats, L


def rest_measures(C, bd, marks):
    """Rest breadths and heights of the face on Body.Mesh as it is (mm)."""
    import head as H
    import head_look as HL
    V, g = bd["V"], bd["groups"]
    region = H.head_region(bd) & bd["in_body"] & (g["ears"] < 0.3)
    L = HL.landmarks(bd, marks)
    ch, pu, gl = L["chin"], L["pupil"], L["glabella"]
    ear = np.array(marks["ear_R"]["rest_mm"])
    out = {}

    def breadth(z, ymax, dz=3.0):
        s = region & (np.abs(V[:, 2] - z) < dz) & (V[:, 1] < ymax)
        return round(float(2 * np.abs(V[s, 0]).max()), 1) if s.any() else None
    out["bizygomatic"] = breadth(pu[2] - 14.0, ear[1] - 4.0)
    out["bigonial"] = breadth(ch[2] + 30.0, ear[1] + 6.0)
    out["bitemporal_at_brow"] = breadth(L["brow_mid_top"][2] + 8.0, ear[1] - 25.0)
    out["head_breadth_max"] = round(float(2 * np.abs(V[region, 0]).max()), 1)
    out["glabella_to_menton"] = round(float(gl[2] - ch[2]), 1)
    out["subnasale_to_menton"] = round(float(L["subnasale"][2] - ch[2]), 1)
    out["bizyg_over_glabella_menton"] = round(out["bizygomatic"] / out["glabella_to_menton"], 3)
    out["bigonial_over_bizyg"] = round(out["bigonial"] / out["bizygomatic"], 3)
    return out


def main(argv):
    import bpy
    import common as C
    import head as H
    import head_shape as HS
    import head_shape_r5 as R5
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(WORK, exist_ok=True)
    body, rig = C.open_base()
    bd = C.body_data(body)
    marks = C.base_json()["landmarks"]
    D, stats, L = delta(C, bd, marks)
    print("[r6] delta", json.dumps(stats), flush=True)
    rec = {"params": P6, "delta": stats, "base": "cache/stages/base.blend (round 5's face wired), scripts/stages/hero_pose.json"}
    if a.measure:
        rec["r5_rest"] = rest_measures(C, bd, marks)
        C.apply_hero_pose(rig)
        bpy.context.view_layer.update()
        rec["r5"] = R5.measure(C, body, rig, bd, marks, "r5")
        C.rest_pose(rig)
        R5.apply_dev(body, D, name="head-shape-r6-dev")
        bd6 = C.body_data(body)
        region = H.head_region(bd) & bd["in_body"]
        rec["flipped_vs_r5"] = R5.flips(bd["V"], bd6["V"], bd["F"], region)
        rec["applied_max_mm"] = round(float(np.linalg.norm(bd6["V"] - bd["V"], axis=1).max()), 2)
        rec["r6_rest"] = rest_measures(C, bd6, marks)
        C.apply_hero_pose(rig)
        bpy.context.view_layer.update()
        rec["r6"] = R5.measure(C, body, rig, bd6, marks, "r6")
        with open(os.path.join(WORK, "measure.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1)
        for k in ("r5_rest", "r6_rest", "r5", "r6"):
            print(f"[r6] {k}", json.dumps({kk: vv for kk, vv in rec[k].items() if kk != "jaw_band_px"}), flush=True)
        print("[r6] flipped", rec["flipped_vs_r5"], "applied max", rec["applied_max_mm"], flush=True)
    if a.write:
        n = len(bd["V"])
        if open(WIRED_TARGET, "rb").read() != open(R5_TARGET, "rb").read():
            raise SystemExit("[r6] head-shape.target is not round 5's: the delta here is meant for round 5's face")
        D5 = HS.read_target(n, R5_TARGET)
        HS.write_target(D5 + D, R6_TARGET, "head round 6 (head_shape_r6.py): round 5 plus the longer, leaner face")
        with open(R6_JSON, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1)
        print("[r6] wrote", R6_TARGET, flush=True)
    return 0


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
        rc = main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    except Exception:
        import traceback
        traceback.print_exc()
        rc = 1
    sys.stdout.flush()
    os._exit(rc)
