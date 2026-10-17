"""The dense skin laid on the scan (the scan transfer, 2026-10-17; notes/research_foot_hires.md "Scan transfer").

Part 01 transfers the foot's large forms from subject 038's scan onto its cage (scripts/parts/p01/transfer.py), whose
quads (4 mm on the toes, 10-20 mm on the foot and ankle) carry the scan to within about a millimetre at their limit
points and round off what lies between them: the heel pad's rim, the arch's edge, the ball's crescent, the tendons and
the malleoli. Here the trial's dense copy (0.1-0.4 mm) is laid on the scan itself, with part 01's masks and placement:

  * where: the scan's frame onto this foot by the matrix part 01 stored on Frame.Foot.L ("p01_scan"), so the dense
    skin meets the very surface its cage was fitted to;
  * what: every vertex's nearest point on the scan (no further than `max_dist`, facing within ~70 degrees), lifted off
    the scan's 1.5 mm facets onto their Phong patch (`phong`), so no facet prints in clay;
  * how much: all of it below blend_z[0], none above blend_z[1] (a smootherstep share between: the dense skin there
    is the cage's, which part 01 has already eased from the scan into the leg; fading the data's weight instead, as
    the cage does, left the dense skin on the scan until its weight was gone and creased it round the ankle at the
    cut, xfer4); nothing where part 01's Foot.ScanKeep group is 1 (the skin between the toes, ours), fading with it;
  * smoothly: the displacement solved as part 01's (transfer.Solver, no limit stencil: a dense skin is its own limit),
    its smoothness weighted by edge length so it acts over about `smooth_mm` whatever the local spacing, which also
    carries the kept zones along with the toes they lie between; `iters` passes, each with fresh nearest points.

Runs in the stage (method_fields.build) right after the curled toes' folds are closed, before the nails, creases,
veins, tendons and hair, which stay the trial's.
"""
import json
import math
import os
import sys

import numpy as np

import common as C

SCRIPTS = os.path.dirname(os.path.dirname(C.HERE))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

SCAN_TRANSFER = {"on": 1, "iters": 2, "phong": 0.75, "smooth_mm": 0.9, "max_dist": 5.0, "facing": 0.3,
                 "blend_z": [95.0, 125.0], "keep_group": "Foot.ScanKeep", "cg_iters": 400}


def _cfg(P):
    out = dict(SCAN_TRANSFER)
    out.update(P.get("scan_transfer") or {})
    return out


def placement(frame_name="Frame.Foot.L"):
    """Part 01's record of where its reference scan lies on this foot: (scan id, 4 x 4 scans' frame -> world, mm)."""
    import bpy
    fr = bpy.data.objects.get(frame_name)
    if fr is None or "p01_scan" not in fr:
        return None, None
    rec = json.loads(fr["p01_scan"])
    return rec, np.array(rec["M"], float)


class _Dense:
    """The dense skin as transfer.Solver reads a cage: its edges, every vertex its own limit."""

    def __init__(self, n, edges):
        self.n = n
        self.edges = np.asarray(edges, np.int64)
        self.interior = np.ones(n, bool)
        idx = np.arange(n)
        self.S = (idx, idx, np.ones(n))


def apply(ctx, q, topo, P, report=None):
    """The dense skin (frame F, mm) laid on the scan. Returns positions."""
    from parts.p01 import transfer as X
    cfg = _cfg(P)
    if not cfg.get("on"):
        return q
    rec, M = placement()
    if rec is None:
        if report is not None:
            report["scan_transfer"] = "part 01 has no scan placement (its transfer is off): skipped"
        return q
    ref = X.load_reference(rec["id"], rec.get("rest", "mBW"))
    # the scan into this foot's frame F: scans' frame -> world (part 01's matrix) -> F
    w = ref.q @ M[:3, :3].T + M[:3, 3]
    sq = ctx.frame.to_f(w)
    T = ref.T if np.linalg.det(M[:3, :3]) > 0 else ref.T[:, ::-1]
    surf = X.Surface(sq, T)
    keep = np.clip(C.group(ctx.skin, cfg["keep_group"]), 0.0, 1.0)
    edges, lengths = C.edge_lengths(ctx.skin)
    dense = _Dense(len(q), edges)
    z = q[:, 2]
    blend = 1.0 - X.smootherstep(z, *cfg["blend_z"])
    free = z < cfg["blend_z"][1] + 15.0
    # the smoothness term per edge (h0 / l)^2 with h0 1 mm, so its reach is smooth_mm whatever the spacing (energy:
    # sum |U - g|^2 over vertices ~ integral / l^2, sum w |dU|^2 over edges ~ 2 integral |grad U|^2: length^2 = 2 mu)
    ew = np.clip((1.0 / np.maximum(lengths, 1e-3)) ** 2, 0.0, 400.0)
    mu = 0.5 * cfg["smooth_mm"] ** 2
    sol = X.Solver(dense, free, limit=False, edge_w=ew)
    act = np.nonzero(free & (keep < 0.999) & (blend > 0.0))[0]
    U = np.zeros_like(q)
    nrm = C.vertex_normals(q, topo)
    rep = []
    for it in range(int(cfg["iters"])):
        cur = q + U
        nrm = C.vertex_normals(cur, topo)
        Cp, N, D = surf.nearest(cur[act], phong=cfg["phong"])
        ok = (D < cfg["max_dist"]) & (np.einsum("ij,ij->i", nrm[act], N) > cfg["facing"])
        wgt = np.zeros(len(q))
        g = np.zeros_like(q)
        a_ok = act[ok]
        wgt[a_ok] = 1.0 - keep[a_ok]
        g[a_ok] = blend[a_ok, None] * (Cp[ok] - q[a_ok])   # toward the blended point, from where the skin began
        held = free & (blend <= 0.0)                       # over the cut the dense skin stays the cage's
        wgt[held], g[held] = 1.0, 0.0
        U = sol.solve(wgt, g, mu, U, iters=int(cfg["cg_iters"]))
        full = a_ok[(keep[a_ok] < 0.05) & (blend[a_ok] > 0.999)]
        res = np.linalg.norm((q + U)[full] - (q[full] + g[full]), axis=1)
        Cf, Nf, Df = surf.nearest((q + U)[full[::25]], phong=cfg["phong"])
        rep.append({"it": it, "on_scan": int(ok.sum()), "of": int(len(act)),
                    "moved_rms": round(float(np.sqrt(np.mean(np.sum(U[a_ok] ** 2, 1)))), 3),
                    "residual_rms": round(float(np.sqrt(np.mean(res ** 2))), 3),
                    "off_scan_rms": round(float(np.sqrt(np.mean(Df ** 2))), 3),
                    "off_scan_p95": round(float(np.percentile(Df, 95)), 3)})
    if report is not None:
        report["scan_transfer"] = {"scan": rec["id"], "passes": rep, "kept": int((keep > 0.5).sum()),
                                   "moved_max": round(float(np.linalg.norm(U, axis=1).max()), 2)}
    return q + U
