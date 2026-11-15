"""Spec 01 §4.1: solve the weights of the MPFB foot targets that build_all.py's S1 loads, and write them to
scripts/parts/p01/params.json ("targets"). Run it on S2's output (the toes are found by the rig's deform
groups, which S2 imports; the rig at rest does not move the mesh), then rebuild S1-S2:

  blender -b cache/body/rigged.blend --python scripts/parts/p01/fit_targets.py -- [--write] [--check]
  python -I scripts/build_all.py --to S2

MPFB detail targets are shape keys, so the mesh is an exact linear function of their weights (spec 18 D3):
lib/linmodel predicts the whole mesh for a weight vector in about a millisecond, and the foot's dimensions are
measured on the prediction with the same code as the part's measure() (footmetrics.py). The dimensions are
not linear in the mesh (extremes, tape girths), so the fit is Gauss-Newton: a Jacobian by differences of
predictions, a bounded linear least-squares step (lib/optim.bounded_lsq), repeated until the weights settle;
the depsgraph then confirms. The left foot is solved and the right foot's targets take the same weights (the
pair's asymmetries are sculpted, §3.3). The residuals carry spec 01 §3.1's targets over tolerances: the four
the targets reach (length, ball breadth, the dorsum heights, the ankle girth) tightly, the heel and malleoli
loosely, since §4.2 sculpts the rest. --check only measures the body as it is.
"""
import argparse
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(os.path.dirname(HERE))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
from lib import cache, linmodel, log, optim  # noqa: E402
from parts.p01 import footmetrics as fm  # noqa: E402

PARAMS = os.path.join(HERE, "params.json")
BODY = "Body.Mesh"
# the free targets of the fit (the left side's; "{s}" is l or r) and the unsided ankle target
SIDED = ("{s}-foot-scale-depth-incr", "{s}-foot-scale-horiz-incr", "{s}-foot-scale-vert-decr")
UNSIDED = ("measure-ankle-circ-incr",)
# (metric, target mm, weight tolerance mm): spec 01 §3.1; heights and the toe as estimated there
RESIDUALS = (("foot_length", 282.0, 0.5), ("ball_breadth", 105.0, 1.0), ("ankle_circ_min", 229.0, 1.5),
             ("dorsum_h50", 66.0, 3.0), ("dorsum_h60", 56.0, 3.0), ("dorsum_h70", 40.0, 3.0),
             ("heel_breadth", 71.0, 4.0), ("bimalleolar", 76.0, 4.0), ("toe2_height", 16.0, 5.0))
# what S1 must hand on (the task's check): spec 01 §3.1 targets and §8.2 tolerances
CHECK = (("foot_length", 282.0, 3.0), ("ball_breadth", 105.0, 2.0), ("heel_breadth", 71.0, 2.0),
         ("bimalleolar", 76.0, 2.0), ("ankle_circ_min", 229.0, 6.0))


def _mpfb():
    import bpy
    mod = "bl_ext.user_default.mpfb"
    if mod not in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_enable(module=mod)
    from bl_ext.user_default.mpfb.services.targetservice import TargetService
    return TargetService


def ensure_targets(body):
    """The fit's targets as shape keys on the body (loaded at weight 0 if S1 did not load them):
    (free keys, {left key: right key})."""
    ts = _mpfb()
    have = {k.name for k in body.data.shape_keys.key_blocks}
    free, mirror = [], {}
    for name in [t.format(s="l") for t in SIDED] + list(UNSIDED):
        for n in ([name, "r" + name[1:]] if name.startswith("l-") else [name]):
            if n not in have:
                path = ts.target_full_path(n)
                if not path or os.path.basename(path).split(".")[0] != n:
                    raise FileNotFoundError(f"MPFB has no target {n!r}")
                ts.load_target(body, path, weight=0.0)
        free.append(name)
        if name.startswith("l-"):
            mirror[name] = "r" + name[1:]
    return free, mirror


def grounded(co, m):
    """S1 re-grounds the body on its lowest vertex after the targets: so does a prediction."""
    z0 = (co if m.orig is None else co[m.orig])[:, 2].min()
    out = co.copy()
    out[:, 2] -= z0
    return out


def measure_left(m, ix):
    return fm.foot(m, ix, "L", toes=True)


def residuals(vals):
    return np.array([(vals[k] - t) / tol for k, t, tol in RESIDUALS])


def fit(body, free, iters=8, step=0.02, say=print):
    """Gauss-Newton on the linear model's predictions; returns (weights, metrics, log)."""
    model = linmodel.LinearModel(body, keys=free)
    m0 = fm.read(body)
    ix = fm.index(body, m0)

    def at(w):
        return measure_left(fm.with_positions(m0, grounded(model.mesh(w), m0)), ix)

    w = np.clip(model.values(), 0.0, 1.0)
    trail = []
    for it in range(iters):
        t = time.perf_counter()
        v0 = at(w)
        r0 = residuals(v0)
        J = np.column_stack([(residuals(at(w + step * e)) - r0) / step for e in np.eye(len(w))])
        sol = optim.bounded_lsq(J, J @ w - r0, lo=0.0, hi=1.0, lam=1e-4, w0=w)
        w_new = sol["x"]
        trail.append({"iter": it, "f": float(r0 @ r0), "w": w.round(5).tolist(), "s": round(time.perf_counter() - t, 3)})
        say(f"iter {it}: f {r0 @ r0:.4f}, weights {dict(zip(free, np.round(w, 4)))}")
        if np.max(np.abs(w_new - w)) < 1e-4:
            w = w_new
            break
        w = w_new
    v = at(w)
    trail.append({"iter": "final", "f": float(residuals(v) @ residuals(v)), "w": w.round(5).tolist()})
    return w, v, trail, model


def depsgraph_metrics(body):
    """The foot as the depsgraph has it, re-grounded as S1 would."""
    m = fm.read(body)
    ix = fm.index(body, m)
    z0 = (m.co[:, 2].min()) * 1000.0
    if abs(z0) > 1e-3:
        co = m.original() * 1000.0
        m = fm.with_positions(m, grounded(np.nan_to_num(co, nan=1e9), m))
    return {s: fm.foot(m, ix, s, toes=True) for s in ("L", "R")}


def report(metrics, say=print):
    rows, ok = [], True
    for k, t, tol in CHECK:
        for s in ("L", "R"):
            v = metrics[s].get(k)
            p = v is not None and abs(v - t) <= tol
            ok &= bool(p)
            rows.append({"side": s, "metric": k, "value": None if v is None else round(v, 2), "target": t, "tol": tol,
                         "pass": bool(p)})
            say(f"  {s} {k:16s} {v if v is None else round(v, 2):>8} target {t} +/- {tol}  {'pass' if p else 'FAIL'}")
    return ok, rows


def main(argv):
    import bpy
    ap = argparse.ArgumentParser(prog="fit_targets.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="write the weights to scripts/parts/p01/params.json")
    ap.add_argument("--check", action="store_true", help="only measure the body as it is")
    a = ap.parse_args(argv)
    body = bpy.data.objects.get(BODY)
    if body is None:
        print(f"[fit_targets] no {BODY} in this file: open cache/body/rigged.blend", flush=True)
        return 3
    say = lambda msg: log.info("fit_targets", msg)  # noqa: E731
    out = {}
    if not a.check:
        free, mirror = ensure_targets(body)
        t = time.perf_counter()
        w, pred, trail, model = fit(body, free, say=say)
        out.update(seconds=round(time.perf_counter() - t, 2), trail=trail,
                   weights={k: round(float(x), 6) for k, x in zip(free, w)})
        model.apply(w)
        kb = body.data.shape_keys.key_blocks
        for left, right in mirror.items():
            kb[right].slider_min, kb[right].slider_max = 0.0, 1.0
            kb[right].value = kb[left].value
        bpy.context.view_layer.update()
        say(f"solved in {out['seconds']} s: {out['weights']}")
    metrics = depsgraph_metrics(body)
    say("the foot, measured through the depsgraph (spec 01 §3.1, §8.2 tolerances):")
    ok, rows = report(metrics, say)
    out.update(check=rows, passed=ok,
               metrics={s: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if not k.startswith("_")}
                        for s, r in metrics.items()})
    if a.write and not a.check:
        data = cache.read_json(PARAMS) or {}
        targets = {}
        for k, x in out["weights"].items():
            targets[k] = round(float(x), 6)
            if k.startswith("l-"):
                targets["r" + k[1:]] = round(float(x), 6)
        data["targets"] = dict(sorted(targets.items()))
        cache.write_json(PARAMS, data)
        say(f"wrote {os.path.relpath(PARAMS, os.path.dirname(SCRIPTS))}: {data['targets']}")
    print("RESULT " + log.dumps(out), flush=True)
    return 0 if ok or not a.check else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []))
