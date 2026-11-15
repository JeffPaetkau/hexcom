"""The scan transfer's deviation from its scan (2026-10-17; notes/research_foot_hires.md "Scan transfer"): a run.py --save
skin of the trial put back into the scans' frame by part 01's placement (Frame.Foot.L's "p01_scan"), then

  * scanfit's sections (plan, heel, sole) on it against the scan's own (scan_targets.json "per_scan") and the three
    men's mean;
  * every vertex's distance from the scan's surface, by zone: transferred (Foot.ScanKeep under 0.05, below the blend),
    the blend into the leg, the kept skin between the toes (ScanKeep over 0.5, where ours is meant to differ), and
    within the transferred zone the toes, the sole, the heel, the dorsum and the ankle.

  blender -b cache/body/rigged.blend --python scripts/research/foot_hires/xferdev.py -- cache/research/foot_hires/<run>.npz
      [--out renders/research/foot_hires/scan_transfer/deviation.json]
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import common as C  # noqa: E402


def main(argv):
    import argparse
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from lib import cache
    from parts.p01 import scanfit as SF, transfer as X
    ap = argparse.ArgumentParser()
    ap.add_argument("skin")
    ap.add_argument("--out", default=os.path.join(C.OUT, "scan_transfer", "deviation.json"))
    a = ap.parse_args(argv)
    part = C.part_module()
    cache.load_part(part.PART)
    bpy.context.view_layer.update()
    fr = bpy.data.objects["Frame.Foot.L"]
    rec = json.loads(fr["p01_scan"])
    M = np.array(rec["M"], float)
    Minv = np.linalg.inv(M)
    z = np.load(a.skin if os.path.isabs(a.skin) else C.env.path(a.skin))
    co = z["skin_co"].astype(float)
    q = co @ Minv[:3, :3].T + Minv[:3, 3]                 # the skin in the scans' frame
    f = z["skin_faces"].astype(np.int64)
    T = np.concatenate([f[:, [0, 1, 2]], f[:, [0, 2, 3]]])
    T = T[(T >= 0).all(axis=1)]
    keep = z["scan_keep"].astype(float) if "scan_keep" in z.files else np.zeros(len(q))
    toes = z["toe_w"].astype(float).max(axis=1)
    ref = X.load_reference(rec["id"], rec.get("rest", "mBW"))
    tree = BVHTree.FromPolygons(ref.q.tolist(), ref.T.tolist(), all_triangles=True)
    out = {"skin": os.path.relpath(a.skin, C.env.PROJECT_DIR).replace(os.sep, "/") if os.path.isabs(a.skin) else a.skin,
           "scan": rec["id"]}
    # sections (scanfit's own measures, in the scans' frame as placed: no re-zeroing)
    sel = q[:, 2] < 220.0
    used = np.nonzero(sel)[0]
    remap = np.full(len(q), -1, np.int64)
    remap[used] = np.arange(len(used))
    Ts = remap[T]
    Ts = Ts[(Ts >= 0).all(axis=1)]
    meas = SF.measures(q[used], Ts, pts=q[used])
    tg = SF.load_targets()
    out["sections_vs_scan"] = SF.report(meas, {"values": tg["per_scan"][rec["id"]]})
    out["sections_vs_mean"] = SF.report(meas, tg)
    # the scan's own sections, read the same way on its sampled surface, against the mean (how far one man is from three)
    out["scan_vs_mean"] = SF.report(SF.measures(ref.q, ref.T), tg)
    # distances from the scan's surface (signed: + outside)
    zone = q[:, 2] < 120.0
    idx = np.nonzero(zone)[0]
    d = np.empty(len(idx))
    for j, i in enumerate(idx.tolist()):
        loc, nrm, fi, dist = tree.find_nearest(Vector(q[i]))
        d[j] = dist if (Vector(q[i]) - loc).dot(nrm) >= 0.0 else -dist
    k, zz, toe = keep[idx], q[idx, 2], toes[idx]

    def stats(m):
        s = d[m]
        if not len(s):
            return None
        return {"n": int(len(s)), "rms": round(float(np.sqrt(np.mean(s ** 2))), 3), "mean": round(float(s.mean()), 3),
                "p95_abs": round(float(np.percentile(np.abs(s), 95)), 3), "max_abs": round(float(np.abs(s).max()), 2)}
    tr = (k < 0.05) & (zz < 95.0)
    yy = q[idx, 1]
    out["distance_mm"] = {
        "transferred": stats(tr),
        "transferred_toes": stats(tr & (toe > 0.5)),
        "transferred_sole_z_under_8": stats(tr & (toe < 0.5) & (zz < 8.0)),
        "transferred_heel_behind_y_-70": stats(tr & (toe < 0.5) & (yy > -70.0) & (zz >= 8.0)),
        "transferred_dorsum_and_sides": stats(tr & (toe < 0.5) & (yy <= -70.0) & (zz >= 8.0)),
        "transferred_ankle_z_60_95": stats(tr & (zz >= 60.0)),
        "blend_z_95_120": stats((k < 0.05) & (zz >= 95.0)),
        "keep_fading_0.05_0.5": stats((k >= 0.05) & (k <= 0.5)),
        "kept_between_toes_over_0.5": stats(k > 0.5),
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    C.write_json(a.out, out)
    print("RESULT " + json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []))
