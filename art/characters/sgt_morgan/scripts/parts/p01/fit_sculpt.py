"""Spec 01 §4.2-§4.3: solve the amounts of the sculpt's pass A (fields.py) against the foot's dimensions in
spec 01 §3.1 and §3.3, and write them to scripts/parts/p01/params.json ("sculpt"):

  blender -b cache/body/rigged.blend --python scripts/parts/p01/fit_sculpt.py -- [--write] [--dry] [--iters 6]

Each field is a displacement linear in its amount, and pass B (the fixed toe rotations, knuckles, pulps,
bony landmarks and nail beds) is cheap numpy, so the whole sculpt is evaluated without the depsgraph and
measured with footmetrics on the prediction. The fit is Gauss-Newton with a bounded least-squares step
(lib/optim.bounded_lsq) and a halving line search; differences are taken at half a unit, which averages the
vertex-scale noise of extreme-based dimensions. The left foot is solved; the right takes the same amounts
(its asymmetries are fields.FIXED). --dry measures the current amounts without fitting.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(os.path.dirname(HERE))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
from lib import cache, log, measure, optim  # noqa: E402
from parts.p01 import fields, footmetrics as fm  # noqa: E402

PARAMS = os.path.join(HERE, "params.json")
BODY = "Body.Mesh"
L_TARGET = 274.7
# §3.3 as Jeff locked it on 2026-10-10 (from reference photos): the tips of the curled, shortened lesser toes,
# the 30 mm hallux (pass B widens it to that whatever toe1_w is) and the 16 mm toe 2; toes 3-5 keep their
# table widths here, since the closed webs that widen their bases in the build come after the fit's prediction.
# Jeff, 2026-10-15: the hallux 7 mm shorter (pass B's hallux_short_mm, so toe1_ext is not asked to do it), the
# foot 274.7 to its longest toe, the lesser toes' tips where they were (absolute)
TIP_Y = {1: -274.7, 2: -272.3556, 3: -262.26, 4: -250.134, 5: -232.4244}
TOE_W = {1: 30.0, 2: 16.0, 3: 16.0, 4: 15.0, 5: 14.5}
TOE_H = {1: 24.8, 2: 17.5, 3: 15.4, 4: 14.3, 5: 15.4}
# (metric, target, weight tolerance): spec 01 §3.1 and §3.3 (tight where ANSUR measured, looser where the
# spec estimated); the §8.2 tolerances are what measure() checks; the heel is H1 (Jeff, 2026-10-10). The shape
# pass (2026-10-14): the ball's breadth aimed 0.8 mm under spec 01's 105 because the build's toe separation (left out
# of the prediction) adds about 1 mm to it; the instep girth 246 (spec 01 §3.1 note)
RESIDUALS = [("foot_length", L_TARGET, 0.5), ("ball_length", 210.0, 1.0), ("ball_breadth", 104.2, 0.4),
             ("heel_breadth", 76.0, 0.7), ("heel_width_z10", 69.0, 1.0), ("heel_width_z20", 72.0, 1.0),
             ("heel_width_z30", 73.0, 1.0), ("bimalleolar", 76.0, 0.7), ("pternion_z", 30.0, 1.0),
             ("heel_ankle_circ", 353.0, 6.0), ("instep_circ", 246.0, 3.0), ("ball_circ", 259.0, 2.5),
             ("ankle_circ_min", 229.0, 2.0), ("dorsum_h50", 66.0, 1.0), ("dorsum_h60", 56.0, 1.0),
             ("dorsum_h70", 40.0, 1.0), ("arch_medial_45", 13.0, 1.0), ("lateral_clear_50", 4.0, 1.0)]
RESIDUALS += [("malleolus_lateral_z", 76.0, 1.0), ("malleolus_medial_z", 89.0, 1.0)]
# the plan outline (the shape pass, 2026-10-14, spec 01 §3.1 note), read on the subdivided surface (the probe): the
# midfoot's breadth at 50 % L 0.86 of the ball's, the 5th metatarsal head's corner where spec 01 puts the head
# (185 mm, 65.6 % L); the lateral border's bulge past its heel-to-head chord and the medial border's dip inside its
# chord are one-sided (PLAN_SIDED)
RESIDUALS += [("plan_b50", 90.0, 1.5), ("plan_head5_pct", 65.6, 2.0)]
PLAN_SIDED = (("plan_lat_bulge", None, 2.5, 0.7), ("plan_med_dip", 3.0, 6.0, 0.8))   # (metric, least, most, tol)
RESIDUALS += [(f"toe{k}_tip_y", y, 0.7) for k, y in TIP_Y.items()]
RESIDUALS += [(f"toe{k}_width", v, 0.7) for k, v in TOE_W.items()]
RESIDUALS += [(f"toe{k}_height", v, 0.7) for k, v in TOE_H.items()]


class AnkleProbe:
    """A temporary copy of one foot's region below z 220 with a Subdivision modifier, level 2: a prediction
    is written into it and read back subdivided, so the fit sees the malleoli as the closeups and measure()
    do (MakeHuman's 13 mm ankle quads lose half a small dome to subdivision)."""

    def __init__(self, body, side):
        import bpy
        foot = body.feet[side]
        rows = foot.R[foot.body & (body.co[foot.R, 2] < 220.0)]  # the skin only: MakeHuman's helpers stay out
        pos = {int(v): i for i, v in enumerate(rows)}
        ls, lt, lv = body.topo
        faces = []
        for p in range(len(ls)):
            vs = lv[ls[p]:ls[p] + lt[p]].tolist()
            if all(v in pos for v in vs):
                faces.append([pos[v] for v in vs])
        me = bpy.data.meshes.new("Foot.Fit.Ankle")
        me.from_pydata((body.co[rows] / 1000.0).tolist(), [], faces)
        self.ob = bpy.data.objects.new("Foot.Fit.Ankle", me)
        bpy.context.scene.collection.objects.link(self.ob)
        mod = self.ob.modifiers.new("Subdivision", "SUBSURF")
        mod.levels = mod.render_levels = 2
        self.rows = rows

    def read(self, co_mm):
        self.ob.data.vertices.foreach_set("co", (co_mm[self.rows] / 1000.0).astype(np.float32).ravel())
        self.ob.data.update()
        return measure.evaluate(self.ob, ("polys",))

    def remove(self):
        import bpy
        me = self.ob.data
        bpy.data.objects.remove(self.ob)
        bpy.data.meshes.remove(me)


def predicted(body, a, side="L", opts=None):
    """World mm of every body vertex with the sculpt of amounts a on one foot (pass B without the toes'
    separation, as the fit sees it)."""
    co = body.co.copy()
    foot = body.feet[side]
    co[foot.R] = foot.frame.to_w(body.sculpt_side(side, a, opts, separate=False))  # pass B as params.json sets it
    return co


def dump(path, body, a, probe, side="L", opts=None):
    """The prediction's subdivided surface (the probe's read) in frame F, mm, with its polygons, for sections and
    plan plots outside Blender (the shape pass, 2026-10-14)."""
    co = predicted(body, a, side, opts)
    fine = probe.read(co)
    f = fm.frame(fm.with_positions(body.m0, co), body.ix, side)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    np.savez_compressed(path, q=f.to_f(fine.co * 1000.0).astype(np.float32), loop_start=fine.loop_start,
                        loop_total=fine.loop_total, loop_vert=fine.loop_vert)


def evaluate(body, a, side="L", gaps=True, probe=None, opts=None):
    """The sculpted foot's metrics (and toe gaps) for amounts a, measured on the prediction; the malleoli on
    its subdivided surface when a probe is given."""
    co = predicted(body, a, side, opts)
    m = fm.with_positions(body.m0, co)
    v = fm.foot(m, body.ix, side)
    f = v.pop("_frame", None)
    if probe is not None:
        fine = probe.read(co)
        v.update(fm.ankle(fine, f))
        v.update(fm.heel_back(fine, f))
        v.update(fm.plan(fine, f, v["station_length"]))
    if gaps:
        v["gaps"] = fm.toe_gaps(m, body.ix, side)
    return v


PROMINENCE_MM, PROMINENCE_TOL = 3.0, 0.5  # each malleolus, and the heel behind the Achilles insertion,
                                          # stands at least 3 mm proud of what lies next to it


def residuals(v):
    r = []
    for k, t, tol in RESIDUALS:
        x = v.get(k)
        r.append(0.0 if x is None else (x - t) / tol)
    for k in ("malleolus_lateral_prom", "malleolus_medial_prom", "heel_prom"):  # one-sided
        x = v.get(k)
        r.append(0.0 if x is None else min(x - PROMINENCE_MM, 0.0) / PROMINENCE_TOL)
    for k, least, most, tol in PLAN_SIDED:
        x = v.get(k)
        if x is None:
            r.append(0.0)
            continue
        under = min(x - least, 0.0) if least is not None else 0.0
        over = max(x - most, 0.0) if most is not None else 0.0
        r.append((under + over) / tol)
    return np.array(r)  # (toe gaps are kept by pass B's separation, not fitted: they are not smooth)


PRIOR = 0.03  # weight of the pull toward fields.py's start values, per unit (mm or %)


def fit(body, a0, iters=6, step=0.5, damping=0.3, say=print, probe=None, opts=None, free=None):
    """Levenberg-Marquardt-style Gauss-Newton: the step solves the linearised residuals plus a weak prior
    toward the start values, damped toward the current amounts, inside the bounds, then halves until the
    true cost falls. `free` names the amounts to solve (default all); the others stay at a0's (the shape pass
    refits the midfoot and keeps Jeff's locked heel and toes, 2026-10-14)."""
    names = [k for k in fields.FIELD_NAMES if free is None or k in free]
    lo = np.array([fields.FIELDS[k][1] for k in names])
    hi = np.array([fields.FIELDS[k][2] for k in names])
    start = np.array([fields.FIELDS[k][3] for k in names])
    x = np.clip(np.array([a0[k] for k in names]), lo, hi)
    sq = np.sqrt(PRIOR)
    held = {k: v for k, v in a0.items() if k not in names}

    def at(vec):
        try:
            v = evaluate(body, dict(held, **dict(zip(names, vec))), probe=probe, opts=opts)
            r = np.concatenate([residuals(v), sq * (vec - start)])
            return v, r, float(r @ r)
        except (LookupError, ValueError, IndexError) as e:  # a shape the measurements cannot read
            return {"error": str(e)}, None, float("inf")

    v, r, f = at(x)
    trail = [{"iter": 0, "f": round(f, 4)}]
    say(f"start: f {f:.3f}")
    lam = damping
    for it in range(1, iters + 1):
        t = time.perf_counter()
        J = np.empty((len(r), len(x)))
        for j in range(len(x)):
            e = np.zeros(len(x))
            h = step if x[j] + step <= hi[j] else -step
            e[j] = h
            rj = at(x + e)[1]
            J[:, j] = 0.0 if rj is None else (rj - r) / h
        for _ in range(6):  # raise the damping until a step lowers the true cost
            sol = optim.bounded_lsq(J, J @ x - r, lo=lo, hi=hi, lam=lam, w0=x)
            xn = np.clip(sol["x"], lo, hi)
            vn, rn, fn = at(xn)
            if fn < f:
                lam = max(lam / 2.0, 1e-3)
                break
            lam *= 4.0
        else:
            say(f"iter {it}: no step lowers f ({f:.3f}); stopping")
            break
        d = xn - x
        x, v, r, f = xn, vn, rn, fn
        trail.append({"iter": it, "f": round(f, 4), "s": round(time.perf_counter() - t, 2), "damping": lam})
        say(f"iter {it}: f {f:.3f} ({time.perf_counter() - t:.1f} s, damping {lam:.3g}); at bounds "
            f"{[names[i] for i in optim.at_bound(x, lo, hi)]}")
        if np.max(np.abs(d)) < 0.05:
            break
    return dict(held, **dict(zip(names, x))), v, trail


def table(v, say=print):
    for k, t, tol in RESIDUALS:
        x = v.get(k)
        say(f"  {k:18s} {'-' if x is None else round(x, 2):>8}  target {t:8.2f}  {'' if x is None else round(x - t, 2)}")
    for k, least, most, tol in PLAN_SIDED:
        x = v.get(k)
        say(f"  {k:18s} {'-' if x is None else round(x, 2):>8}  band   {least} .. {most}")
    for k in ("plan_b40", "plan_b60", "plan_ball", "plan_head5_x", "plan_head1_pct", "plan_head1_x", "plan_widest_pct",
              "plan_widest", "plan_mid_ratio", "ball_length_lateral"):
        x = v.get(k)
        say(f"  {k:18s} {'-' if x is None else round(x, 2):>8}")
    say(f"  gaps {v.get('gaps')}")


def main(argv):
    import bpy
    ap = argparse.ArgumentParser(prog="fit_sculpt.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="write the amounts to scripts/parts/p01/params.json")
    ap.add_argument("--dry", action="store_true", help="measure the current amounts, fit nothing")
    ap.add_argument("--start", action="store_true", help="start from fields.py's start values, not params.json")
    ap.add_argument("--iters", type=int, default=6)
    ap.add_argument("--only", help="comma-separated amounts to solve, the rest held at params.json's")
    ap.add_argument("--set", help="JSON amounts merged over params.json's before the fit (or the dry read)")
    ap.add_argument("--dump", help="write the result's subdivided surface (frame F, mm) to this .npz")
    a = ap.parse_args(argv)
    ob = bpy.data.objects.get(BODY)
    if ob is None:
        print(f"[fit_sculpt] no {BODY}: open cache/body/rigged.blend", flush=True)
        return 3
    say = lambda msg: log.info("fit_sculpt", msg)  # noqa: E731
    t0 = time.perf_counter()
    body = fields.Body(ob, exclude=[k.name for k in (ob.data.shape_keys.key_blocks if ob.data.shape_keys else [])
                                    if k.name.startswith("Foot.")])
    say(f"read the body in {time.perf_counter() - t0:.2f} s")
    params = cache.read_json(PARAMS) or {}
    a0 = fields.amounts({} if a.start else params)
    if a.set:
        a0.update({k: float(v) for k, v in json.loads(a.set).items()})
    opts = fields.options(params)
    out = {}
    probe = AnkleProbe(body, "L")
    try:
        if a.dry:
            v = evaluate(body, a0, probe=probe, opts=opts)
            amounts = a0
        else:
            free = set(a.only.split(",")) if a.only else None
            unknown = sorted((free or set()) - set(fields.FIELD_NAMES))
            if unknown:
                raise SystemExit(f"[fit_sculpt] --only names unknown amounts {unknown}")
            amounts, v, trail = fit(body, a0, a.iters, say=say, probe=probe, opts=opts, free=free)
            out["trail"] = trail
        if a.dump:
            dump(a.dump, body, amounts, probe, opts=opts)
    finally:
        probe.remove()
    table(v, say)
    say("amounts: " + ", ".join(f"{k} {x:.2f}" for k, x in amounts.items()))
    out.update(amounts={k: round(float(x), 4) for k, x in amounts.items()}, seconds=round(time.perf_counter() - t0, 1),
               metrics={k: (round(x, 3) if isinstance(x, float) else x) for k, x in v.items()})
    if a.write and not a.dry:
        params["sculpt"] = out["amounts"]
        cache.write_json(PARAMS, params)
        say(f"wrote {len(out['amounts'])} amounts to scripts/parts/p01/params.json")
    print("RESULT " + log.dumps(out), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []))
