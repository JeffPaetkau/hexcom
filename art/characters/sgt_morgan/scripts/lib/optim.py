"""Optimisers for the fast loop (spec 18 §4.8.5), numpy only, so they run inside Blender and outside it.

  coordinate_descent   up to about 8 smooth parameters (a part's dimension knobs): cyclic, a golden-section
                       line search per parameter inside its bounds; stops when a cycle gains less than 1e-4
                       or after 30 cycles
  cmaes                5-60 parameters and non-smooth objectives (silhouette IoU, combined scores, MPFB
                       target searches): (μ/μ_w, λ)-CMA-ES after Hansen's tutorial (arXiv:1604.00772),
                       λ = 4 + ⌊3 ln n⌋, parameters normalised to [0, 1] by their bounds, σ0 = 0.25,
                       bounds by reflection, seeded
  levenberg_marquardt  residual fits (landmarks, girths): Δp = −(JᵀWJ + μI)⁻¹JᵀWr with J exact or by
                       forward differences (step 0.1), μ ×3 after a worse step and ÷2 after a better one,
                       steps clamped to ±0.15, bounds by clamping, at most 30 iterations
  bounded_lsq          anything the linear target model expresses exactly: min ‖W½(Jw − b)‖² + λ‖w − w0‖²
                       inside [lo, hi], by projected gradient with exact line searches, then an active-set
                       polish that lands on the optimum to rounding
  umeyama              the closed-form similarity (scale, rotation, translation; no reflection) that best maps
                       one point set onto another, the alignment step of §4.8.6's alternation

Each takes plain callables over numpy vectors and returns a dict: x, f, nfev, nit, converged, message and
at_bound, the parameters that ended on a bound, which §4.8.5 wants reported rather than accepted silently.
A callback, if given, sees every evaluation as {nfev, f, best, x} and ends the run by returning True.
"""
import math

import numpy as np

GOLD = (math.sqrt(5.0) - 1.0) / 2.0  # 0.618..., the golden-section ratio


class _Stop(Exception):
    """Raised inside an evaluation to end a run: the budget is spent or the callback asked."""


class _Counter:
    """Wraps an objective: counts evaluations, keeps the best point, enforces the budget, calls back. A NaN
    or infinite value counts as +inf, so a failed evaluation steers the search away instead of ending it."""

    def __init__(self, f, budget, callback=None):
        self.f, self.budget, self.callback = f, budget, callback
        self.n, self.best_x, self.best_f, self.why = 0, None, math.inf, None

    def __call__(self, x):
        if self.n >= self.budget:
            self.why = "budget spent"
            raise _Stop()
        v = float(self.f(x))
        if not math.isfinite(v):
            v = math.inf
        self.n += 1
        if v < self.best_f or self.best_x is None:
            self.best_f, self.best_x = v, np.array(x, float)
        if self.callback is not None and self.callback({"nfev": self.n, "f": v, "best": self.best_f, "x": x}):
            self.why = "stopped by the callback"
            raise _Stop()
        return v


def _box(x0, lo, hi, finite=False):
    """(lo, hi, x0 clipped into them) as float arrays; None bounds are infinite."""
    x = np.array(x0, float).reshape(-1)
    n = len(x)
    lo = np.full(n, -np.inf) if lo is None else np.broadcast_to(np.asarray(lo, float), (n,)).astype(float)
    hi = np.full(n, np.inf) if hi is None else np.broadcast_to(np.asarray(hi, float), (n,)).astype(float)
    if np.any(lo > hi):
        raise ValueError(f"a lower bound exceeds its upper bound: {np.nonzero(lo > hi)[0].tolist()}")
    if finite and not (np.all(np.isfinite(lo)) and np.all(np.isfinite(hi))):
        raise ValueError("this method needs finite bounds on every parameter")
    return lo, hi, np.clip(x, lo, hi)


def at_bound(x, lo, hi, rel=1e-6):
    """Indices of the parameters on a bound (within rel of the bound interval's width, or of 1 if open)."""
    x, lo, hi = (np.asarray(v, float) for v in (x, lo, hi))
    width = np.where(np.isfinite(hi - lo), hi - lo, 1.0)
    tol = rel * np.maximum(width, 1e-300)
    return [int(i) for i in np.nonzero((x <= lo + tol) | (x >= hi - tol))[0]]


def _result(x, f, nfev, nit, converged, message, lo, hi, **extra):
    out = {"x": np.asarray(x, float), "f": float(f), "nfev": int(nfev), "nit": int(nit),
           "converged": bool(converged), "message": message, "at_bound": at_bound(x, lo, hi)}
    out.update(extra)
    return out


# --------------------------------------------------------------------------- coordinate descent

def _golden(g, a, b, tol):
    """Minimum of g on [a, b] by golden-section search to an interval of tol: (t, g(t))."""
    c, d = b - GOLD * (b - a), a + GOLD * (b - a)
    fc, fd = g(c), g(d)
    while b - a > tol:
        if fc <= fd:
            b, d, fd = d, c, fc
            c = b - GOLD * (b - a)
            fc = g(c)
        else:
            a, c, fc = c, d, fd
            d = a + GOLD * (b - a)
            fd = g(d)
    return (c, fc) if fc <= fd else (d, fd)


def coordinate_descent(f, x0, lo, hi, tol=1e-4, max_cycles=30, budget=2000, xtol=1e-4, callback=None):
    """Cyclic coordinate descent with a golden-section line search per parameter (§4.8.5).

    The first cycle searches each parameter's whole bound interval; later cycles search a window four times
    the parameter's last move (at least 100 xtol of its width), and the whole interval again whenever the
    best point lands on a window edge that is not a bound, so a settled parameter costs a few evaluations
    rather than a full search. When the best point lies within the line search's tolerance of a bound, the
    bound itself is tried, so a parameter that wants to leave its range ends exactly on it (and is reported
    in at_bound). Bounds must be finite. Stops when a cycle gains less than tol, after max_cycles cycles or
    when the budget is spent."""
    lo, hi, x = _box(x0, lo, hi, finite=True)
    width = hi - lo
    n = len(x)
    ev = _Counter(f, budget, callback)
    half = width.copy()
    cycles, converged, message = 0, False, f"{max_cycles} cycles"
    try:
        fx = ev(x)
        for cycles in range(1, max_cycles + 1):
            f_start = fx
            for i in range(n):
                if width[i] <= 0:
                    continue
                a, b = max(lo[i], x[i] - half[i]), min(hi[i], x[i] + half[i])
                step_tol = xtol * width[i]
                old = x[i]

                def g(t, i=i):
                    y = x.copy()
                    y[i] = t
                    return ev(y)

                t, ft = _golden(g, a, b, step_tol)
                for bound, inside in ((lo[i], a == lo[i]), (hi[i], b == hi[i])):
                    if inside and abs(t - bound) <= 2.0 * step_tol and t != bound:
                        fb = g(bound)
                        if fb <= ft:
                            t, ft = bound, fb
                if ft < fx:
                    x[i], fx = t, ft
                moved = abs(x[i] - old)
                on_window_edge = ((abs(t - a) <= 2.0 * step_tol and a > lo[i])
                                  or (abs(b - t) <= 2.0 * step_tol and b < hi[i]))
                half[i] = width[i] if on_window_edge else min(width[i], max(4.0 * moved, 100.0 * step_tol))
            if f_start - fx < tol:
                converged, message = True, f"a cycle gained less than {tol:g}"
                break
    except _Stop:
        message = ev.why
    return _result(ev.best_x if ev.best_x is not None else x, ev.best_f, ev.n, cycles, converged, message, lo, hi)


# --------------------------------------------------------------------------- CMA-ES

def _reflect(z):
    """Mirror points into [0, 1] (period 2), the bound handling of §4.8.5."""
    y = np.mod(z, 2.0)
    return np.where(y > 1.0, 2.0 - y, y)


def cmaes(f, x0, lo, hi, sigma0=0.25, seed=17, budget=2000, popsize=None, ftarget=-math.inf, tolx=1e-11,
          tolfun=1e-12, active=True, callback=None):
    """(μ/μ_w, λ)-CMA-ES after Hansen's tutorial (arXiv:1604.00772, Fig. 6 and Table 1).

    The search runs on z in [0, 1]ⁿ, x = lo + (hi − lo) z, so σ0 = 0.25 means a quarter of every range.
    A sample outside the box is mirrored back in (period 2) to be evaluated, while the update uses the
    sample as drawn: the search then sees a folded objective whose optimum on a bound is an ordinary
    minimum, which it reaches with a shrinking step. (Updating with the mirrored points instead stalls on a
    bound: the mean creeps toward it, the evolution path grows and σ with it.) The result is the best
    mirrored point. Weighted recombination over the best μ = ⌊λ/2⌋, cumulative
    step-size adaptation, rank-one and rank-μ covariance updates with the h_σ stall, the eigendecomposition
    refreshed lazily. With active (the tutorial's Table 1 default) the worst λ − μ samples enter the rank-μ
    update with negative weights, rescaled by n / ‖C^-½ y‖² so C stays positive definite; it shortens the
    run on ill-conditioned valleys. Measured on 10-D Rosenbrock from the origin, seeds 1-40, to 1e-6: in De
    Jong's box [−2.048, 2.048]¹⁰ 39 runs succeed, median 4,830 evaluations (3,890-5,800), without it 37,
    median 5,890 (4,530-7,630); in [−5, 5]¹⁰ 39, median 5,030 (4,180-6,590), without it 35, median 5,660
    (5,040-8,700). The misses settle in Rosenbrock's local minimum near x₁ = −1.
    Seeded with numpy's default_rng(seed). Stops at ftarget, when the budget cannot fund
    another generation, when σ times the largest axis falls below tolx (in [0, 1] units), when the best values
    of the last 10 + ⌈30n/λ⌉ generations and the current generation's values all lie within tolfun, or when
    the covariance's condition number passes 1e14."""
    lo, hi, x = _box(x0, lo, hi, finite=True)
    span = hi - lo
    if np.any(span <= 0):
        raise ValueError("cmaes needs lo < hi for every parameter (fix a parameter by leaving it out)")
    n = len(x)
    ev = _Counter(f, budget, callback)
    lam = int(popsize or 4 + math.floor(3.0 * math.log(n)))
    mu = lam // 2
    wp = math.log((lam + 1) / 2.0) - np.log(np.arange(1, lam + 1))   # w'_i of Table 1, positive for i ≤ μ
    pos, neg = wp[:mu], wp[mu:]
    mueff = float(pos.sum() ** 2 / np.sum(pos ** 2))
    cc = (4.0 + mueff / n) / (n + 4.0 + 2.0 * mueff / n)
    cs = (mueff + 2.0) / (n + mueff + 5.0)
    c1 = 2.0 / ((n + 1.3) ** 2 + mueff)
    cmu = min(1.0 - c1, 2.0 * (mueff - 2.0 + 1.0 / mueff) / ((n + 2.0) ** 2 + mueff))
    damps = 1.0 + 2.0 * max(0.0, math.sqrt((mueff - 1.0) / (n + 1.0)) - 1.0) + cs
    chi_n = math.sqrt(n) * (1.0 - 1.0 / (4.0 * n) + 1.0 / (21.0 * n * n))
    w = pos / pos.sum()                                                # recombination weights, sum 1
    if active and len(neg) and np.any(neg < 0):
        mueff_neg = float(neg.sum() ** 2 / np.sum(neg ** 2))
        cap = min(1.0 + c1 / cmu, 1.0 + 2.0 * mueff_neg / (mueff + 2.0), (1.0 - c1 - cmu) / (n * cmu))
        w_all = np.concatenate([w, cap * neg / np.abs(neg).sum()])   # negative weights sum to −cap
    else:
        w_all = np.concatenate([w, np.zeros(lam - mu)])
    rng = np.random.default_rng(seed)

    m = (x - lo) / span
    sigma = float(sigma0)
    pc, ps = np.zeros(n), np.zeros(n)
    B, D = np.eye(n), np.ones(n)
    C, inv_sqrt_C = np.eye(n), np.eye(n)
    eigen_at, gen = 0, 0
    history = []  # best value of each generation, for tolfun
    window = 10 + int(math.ceil(30.0 * n / lam))
    converged, message = False, "budget spent"
    try:
        while ev.n + lam <= budget:
            gen += 1
            Z = rng.standard_normal((lam, n))
            Y = Z @ (B * D).T                       # rows ~ N(0, C)
            G = m + sigma * Y                       # the samples as drawn ...
            fit = np.array([ev(lo + span * xi) for xi in _reflect(G)])   # ... evaluated mirrored into the box
            order = np.argsort(fit, kind="stable")
            history.append(float(fit[order[0]]))
            m_old = m
            m = w @ G[order[:mu]]
            y_w = (m - m_old) / sigma
            ps = (1.0 - cs) * ps + math.sqrt(cs * (2.0 - cs) * mueff) * (inv_sqrt_C @ y_w)
            h_sig = float(np.linalg.norm(ps) / math.sqrt(1.0 - (1.0 - cs) ** (2.0 * ev.n / lam)) / chi_n
                          < 1.4 + 2.0 / (n + 1.0))
            pc = (1.0 - cc) * pc + h_sig * math.sqrt(cc * (2.0 - cc) * mueff) * y_w
            ys = Y[order]                                       # every sample's step, best first
            wo = w_all.copy()
            if active:
                bad = wo < 0                                    # rescaled so the negative update stays bounded
                wo[bad] *= n / np.maximum(np.sum((ys[bad] @ inv_sqrt_C) ** 2, axis=1), 1e-300)
            C = ((1.0 + c1 * (1.0 - h_sig) * cc * (2.0 - cc) - c1 - cmu * w_all.sum()) * C
                 + c1 * np.outer(pc, pc) + cmu * (ys.T * wo) @ ys)
            sigma *= math.exp((cs / damps) * (np.linalg.norm(ps) / chi_n - 1.0))
            if ev.n - eigen_at > lam / (c1 + cmu) / n / 10.0:
                eigen_at = ev.n
                C = np.triu(C) + np.triu(C, 1).T
                d2, B = np.linalg.eigh(C)
                D = np.sqrt(np.maximum(d2, 1e-300))
                inv_sqrt_C = (B / D) @ B.T
            if ev.best_f <= ftarget:
                converged, message = True, f"reached ftarget {ftarget:g}"
                break
            if sigma * D.max() < tolx:
                converged, message = True, f"step below tolx {tolx:g}"
                break
            if (len(history) >= window and max(history[-window:]) - min(history[-window:]) < tolfun
                    and fit.max() - fit.min() < tolfun):
                converged, message = True, f"values flat within tolfun {tolfun:g}"
                break
            if D.max() > 1e7 * D.min():
                message = "covariance condition number passed 1e14"
                break
    except _Stop:
        message = ev.why
    best = ev.best_x if ev.best_x is not None else lo + span * _reflect(m)  # a budget below one generation
    return _result(best, ev.best_f, ev.n, gen, converged, message, lo, hi, sigma=float(sigma), popsize=lam)


# --------------------------------------------------------------------------- Levenberg–Marquardt

def fd_jacobian(residuals, p, r0, lo, hi, step=0.1):
    """Forward differences, stepping backwards at an upper bound: (m, n) for residuals of m values."""
    p = np.asarray(p, float)
    steps = np.broadcast_to(np.asarray(step, float), p.shape)
    J = np.empty((len(r0), len(p)))
    for j in range(len(p)):
        h = steps[j] if p[j] + steps[j] <= hi[j] else -steps[j]
        q = p.copy()
        q[j] += h
        J[:, j] = (np.asarray(residuals(q), float) - r0) / h
    return J


def levenberg_marquardt(residuals, p0, jac=None, lo=None, hi=None, weights=None, max_iter=30, fd_step=0.1,
                        clamp=0.15, mu0=1e-3, ftol=1e-12, gtol=1e-12, budget=100000, callback=None):
    """Weighted Levenberg–Marquardt (§4.8.5): minimises rᵀWr with Δp = −(JᵀWJ + μI)⁻¹JᵀWr.

    μ starts at mu0 times the largest diagonal entry of JᵀWJ (Marquardt's scaling), triples after a step
    that would raise the cost (the step is then re-solved, the Jacobian kept) and halves after one that
    lowers it. Every step is clamped to ±clamp per parameter and the result clipped into the bounds.
    jac(p) gives J exactly (the linear target model); without it J comes from forward differences of
    fd_step. f in the result is the weighted sum of squares; residuals holds the final r."""
    lo, hi, p = _box(p0, lo, hi)
    n = len(p)
    calls = [0]

    def res(q):
        if calls[0] >= budget:
            raise _Stop()
        calls[0] += 1
        return np.asarray(residuals(q), float).reshape(-1)

    r = res(p)
    W = np.ones(len(r)) if weights is None else np.broadcast_to(np.asarray(weights, float), r.shape).astype(float)

    def cost(v):
        return float(v @ (W * v))

    def jacobian(q, rq):
        if jac is not None:
            return np.asarray(jac(q), float).reshape(len(rq), n)
        J = fd_jacobian(res, q, rq, lo, hi, fd_step)
        return J

    c = cost(r)
    it, converged, message = 0, False, f"{max_iter} iterations"
    try:
        J = jacobian(p, r)
        A = J.T @ (W[:, None] * J)
        mu = mu0 * max(float(np.max(np.diag(A))), 1e-12)
        for it in range(1, max_iter + 1):
            g = J.T @ (W * r)
            if np.max(np.abs(g)) <= gtol:
                converged, message = True, "gradient below gtol"
                break
            A = J.T @ (W[:, None] * J)
            while True:
                try:
                    dp = -np.linalg.solve(A + mu * np.eye(n), g)
                except np.linalg.LinAlgError:
                    dp = -np.linalg.lstsq(A + mu * np.eye(n), g, rcond=None)[0]
                if clamp:
                    dp = np.clip(dp, -clamp, clamp)
                pn = np.clip(p + dp, lo, hi)
                if np.max(np.abs(pn - p)) <= 1e-15 * (1.0 + np.max(np.abs(p))):
                    converged, message = True, "no step possible inside the bounds"
                    break
                rn = res(pn)
                cn = cost(rn)
                if cn < c:
                    break
                mu *= 3.0
                if mu > 1e20:
                    converged, message = True, "no lower cost nearby (μ past 1e20)"
                    break
            if converged:
                break
            gain = c - cn
            p, r, c = pn, rn, cn
            mu = max(mu / 2.0, 1e-300)
            if callback is not None and callback({"nfev": calls[0], "f": c, "best": c, "x": p}):
                message = "stopped by the callback"
                break
            if gain <= ftol * max(c + gain, 1e-300):
                converged, message = True, "cost change below ftol"
                break
            J = jacobian(p, r)
    except _Stop:
        message = "budget spent"
    return _result(p, c, calls[0], it, converged, message, lo, hi, residuals=r)


# --------------------------------------------------------------------------- bounded linear least squares

def bounded_lsq(J, b, lo=None, hi=None, weights=None, lam=0.0, w0=None, x0=None, pg_iter=50, max_iter=500,
                tol=1e-12):
    """min ‖W½(Jw − b)‖² + λ‖w − w0‖² subject to lo ≤ w ≤ hi (§4.8.5; the solve of §4.8.6).

    As a quadratic ½wᵀHw − gᵀw with H = JᵀWJ + λI and g = JᵀWb + λw0. Phase one is projected gradient:
    the steepest-descent direction with the variables that would leave the box held back, the exact
    minimiser along it, then a projected search halving that step until the projected point lowers the
    cost; it finds the active set quickly. Phase two is a primal active-set method on the bounds: solve for
    the free variables with the active ones fixed, step toward that solution until a bound is hit, and free
    the active variable whose multiplier has the wrong sign; it ends on the exact optimum (the KKT
    conditions to rounding). weights are per-row weights W; f in the result is the full objective."""
    J = np.atleast_2d(np.asarray(J, float))
    m, n = J.shape
    b = np.asarray(b, float).reshape(m)
    Wr = np.ones(m) if weights is None else np.broadcast_to(np.asarray(weights, float), (m,)).astype(float)
    w0 = np.zeros(n) if w0 is None else np.broadcast_to(np.asarray(w0, float), (n,)).astype(float)
    lo, hi, x = _box(w0 if x0 is None else x0, lo, hi)
    H = J.T @ (Wr[:, None] * J) + lam * np.eye(n)
    g = J.T @ (Wr * b) + lam * w0
    scale = 1.0 + float(np.max(np.abs(g)))

    def q(v):
        return 0.5 * float(v @ H @ v) - float(g @ v)

    pg = 0
    for pg in range(1, pg_iter + 1):
        grad = H @ x - g
        d = -grad
        d[(x <= lo) & (d < 0)] = 0.0
        d[(x >= hi) & (d > 0)] = 0.0
        if np.max(np.abs(d)) <= tol * scale:
            break
        dHd = float(d @ H @ d)
        t = float(d @ d) / dHd if dHd > 0 else 1.0
        q0 = q(x)
        for _ in range(60):
            xn = np.clip(x + t * d, lo, hi)
            if q(xn) <= q0 + 1e-4 * float(grad @ (xn - x)):
                break
            t *= 0.5
        before = (x <= lo) | (x >= hi)
        x = xn
        if pg > 2 and np.array_equal(before, (x <= lo) | (x >= hi)):
            break  # the active set has settled: the polish does the rest exactly

    active = (x <= lo) | (x >= hi)
    it, kkt = 0, math.inf
    for it in range(1, max_iter + 1):
        F = ~active
        if F.any():
            rhs = g[F] - H[np.ix_(F, ~F)] @ x[~F]
            try:
                sol = np.linalg.solve(H[np.ix_(F, F)], rhs)
            except np.linalg.LinAlgError:
                sol = np.linalg.lstsq(H[np.ix_(F, F)], rhs, rcond=None)[0]
            xf = x[F]
            out = (sol < lo[F]) | (sol > hi[F])
            if out.any():
                d = sol - xf
                with np.errstate(divide="ignore", invalid="ignore"):
                    alpha = np.where(d < 0, (lo[F] - xf) / d, np.where(d > 0, (hi[F] - xf) / d, np.inf))
                alpha = np.where(out, alpha, np.inf)
                k = int(np.argmin(alpha))
                a = float(np.clip(alpha[k], 0.0, 1.0))
                x[F] = np.clip(xf + a * d, lo[F], hi[F])
                idx = np.nonzero(F)[0][k]
                x[idx] = lo[idx] if d[k] < 0 else hi[idx]
                active = active | (x <= lo) | (x >= hi)
                continue
            x[F] = sol
        grad = H @ x - g
        at_lo, at_hi = active & (x <= lo), active & (x >= hi)
        viol = np.zeros(n)
        viol[at_lo] = np.maximum(-grad[at_lo], 0.0)   # at a lower bound the gradient must point inward (≥ 0)
        viol[at_hi] = np.maximum(grad[at_hi], 0.0)
        viol[lo == hi] = 0.0                           # a fixed variable has no multiplier sign
        free_err = float(np.max(np.abs(grad[~active]))) if (~active).any() else 0.0
        worst = int(np.argmax(viol))
        kkt = max(float(viol[worst]), free_err)
        if viol[worst] <= 1e-10 * scale:
            break
        active[worst] = False
    r = J @ x - b
    f = float(r @ (Wr * r)) + lam * float((x - w0) @ (x - w0))
    return _result(x, f, 0, it, kkt <= 1e-8 * scale, f"KKT residual {kkt:.2e}", lo, hi,
                   pg_iter=pg, kkt=kkt, active=[int(i) for i in np.nonzero(active)[0]])


# --------------------------------------------------------------------------- similarity alignment

def umeyama(src, dst, weights=None, scale=True):
    """The similarity dst ≈ s R src + t minimising the (weighted) squared distances, by Umeyama's closed
    form (IEEE PAMI 13(4), 1991), with det R = +1 (no reflection). §4.8.6 aligns the 3DDFA points onto the
    model's landmarks with it on the stable set before each weight solve. Returns {s, R, t, rms}, rms in the
    points' units; apply with s * src @ R.T + t."""
    X, Y = np.asarray(src, float), np.asarray(dst, float)
    if X.shape != Y.shape or X.ndim != 2 or len(X) < X.shape[1]:
        raise ValueError(f"umeyama needs two (N, d) point sets of one shape with N ≥ d, got {X.shape}, {Y.shape}")
    w = np.ones(len(X)) if weights is None else np.asarray(weights, float).reshape(-1)
    w = w / w.sum()
    mx, my = w @ X, w @ Y
    Xc, Yc = X - mx, Y - my
    S = (Yc * w[:, None]).T @ Xc
    U, D, Vt = np.linalg.svd(S)
    E = np.ones(len(D))
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        E[-1] = -1.0
    R = (U * E) @ Vt
    var = float(w @ np.sum(Xc ** 2, axis=1))
    s = float(D @ E) / var if scale and var > 0 else 1.0
    t = my - s * R @ mx
    r = Y - (s * X @ R.T + t)
    return {"s": s, "R": R, "t": t, "rms": float(np.sqrt(w @ np.sum(r ** 2, axis=1)))}


# --------------------------------------------------------------------------- self-test

def rosenbrock(x):
    x = np.asarray(x, float)
    return float(np.sum(100.0 * (x[1:] - x[:-1] ** 2) ** 2 + (1.0 - x[:-1]) ** 2))


def _similarity(p, pts):
    """The 3-parameter similarity of the LM self-test: scale s, rotation θ, then a shift t along x."""
    s, th, t = p
    c, si = math.cos(th), math.sin(th)
    return s * (pts @ np.array([[c, si], [-si, c]])) + np.array([t, 0.0])


def selftest():
    """The benchmarks of §4.8.5 (§1.4 item 7), with numbers to report."""
    import time
    R = {}

    # CMA-ES: 10-D Rosenbrock to 1e-6 within 6,000 evaluations, from the origin in De Jong's box
    n = 10
    t = time.perf_counter()
    r = cmaes(rosenbrock, np.zeros(n), -2.048, 2.048, sigma0=0.25, seed=17, budget=6000, ftarget=1e-6)
    R["cmaes_rosenbrock10"] = {"f": r["f"], "nfev": r["nfev"], "generations": r["nit"], "message": r["message"],
                               "max_err_x": float(np.max(np.abs(r["x"] - 1.0))), "s": round(time.perf_counter() - t, 3)}
    assert r["f"] <= 1e-6 and r["nfev"] <= 6000, R["cmaes_rosenbrock10"]
    # bounds by reflection: an optimum outside the box ends on the bound and is reported
    r = cmaes(lambda x: float(np.sum((x - 2.0) ** 2)), np.zeros(5), -1.0, 1.0, seed=17, budget=2000)
    assert np.allclose(r["x"], 1.0, atol=1e-3) and r["at_bound"] == list(range(5)), r
    # seeded: the same seed gives the same run
    a = cmaes(rosenbrock, np.zeros(4), -2.0, 2.0, seed=3, budget=300)
    b = cmaes(rosenbrock, np.zeros(4), -2.0, 2.0, seed=3, budget=300)
    assert a["f"] == b["f"] and np.array_equal(a["x"], b["x"])

    # bounded linear least squares: random J 204 x 60 recovers known weights to 1e-4 ...
    rng = np.random.default_rng(17)
    J = rng.standard_normal((204, 60))
    w_true = rng.uniform(-0.8, 0.8, 60)
    t = time.perf_counter()
    r = bounded_lsq(J, J @ w_true, -1.0, 1.0)
    ms = (time.perf_counter() - t) * 1e3
    err = float(np.max(np.abs(r["x"] - w_true)))
    R["lsq_interior"] = {"max_err": err, "ms": round(ms, 2), "kkt": r["kkt"]}
    assert err <= 1e-4 and not r["at_bound"], R["lsq_interior"]
    # ... and when the data push ten of them against their bounds: b is built so that the KKT conditions
    # hold at w_true with multipliers of the right sign, so w_true is the constrained optimum
    w_b = w_true.copy()
    pinned = rng.choice(60, 10, replace=False)
    w_b[pinned] = np.where(rng.random(10) < 0.5, -1.0, 1.0)
    mult = np.zeros(60)
    mult[pinned] = np.where(w_b[pinned] < 0, 1.0, -1.0) * rng.uniform(0.5, 2.0, 10)  # grad at w_true
    r_extra = J @ np.linalg.solve(J.T @ J, mult)                                    # Jᵀ r_extra = mult
    t = time.perf_counter()
    r = bounded_lsq(J, J @ w_b - r_extra, -1.0, 1.0)
    ms = (time.perf_counter() - t) * 1e3
    err = float(np.max(np.abs(r["x"] - w_b)))
    R["lsq_on_bounds"] = {"max_err": err, "ms": round(ms, 2), "at_bound": len(r["at_bound"]), "kkt": r["kkt"],
                          "pg_iter": r["pg_iter"], "polish_iter": r["nit"]}
    assert err <= 1e-4 and sorted(r["at_bound"]) == sorted(int(i) for i in pinned), R["lsq_on_bounds"]
    # row weights and a ridge toward w0, nothing binding: the dense normal equations
    Wr = rng.uniform(0.5, 1.0, 204)
    w0 = rng.uniform(-0.2, 0.2, 60)
    b = J @ w_true + 0.01 * rng.standard_normal(204)
    r = bounded_lsq(J, b, -10.0, 10.0, weights=Wr, lam=0.1, w0=w0)
    ref = np.linalg.solve(J.T @ (Wr[:, None] * J) + 0.1 * np.eye(60), J.T @ (Wr * b) + 0.1 * w0)
    assert np.max(np.abs(r["x"] - ref)) <= 1e-9, np.max(np.abs(r["x"] - ref))

    # Levenberg–Marquardt: a known 3-parameter similarity (scale, rotation, shift along x) from 20 points
    pts = rng.uniform(-1.0, 1.0, (20, 2))
    truth = np.array([1.2, 0.35, 0.4])
    target = _similarity(truth, pts)

    def residuals(p):
        return (_similarity(p, pts) - target).ravel()

    r = levenberg_marquardt(residuals, [1.0, 0.0, 0.0])
    R["lm_similarity"] = {"iterations": r["nit"], "nfev": r["nfev"], "max_err": float(np.max(np.abs(r["x"] - truth))),
                          "cost": r["f"], "message": r["message"]}
    assert np.max(np.abs(r["x"] - truth)) <= 1e-6 and r["nit"] <= 30, R["lm_similarity"]
    # with a bound that cuts the true scale off: it ends on the bound and says so
    r = levenberg_marquardt(residuals, [1.0, 0.0, 0.0], lo=[0.5, -1, -1], hi=[1.1, 1, 1])
    assert abs(r["x"][0] - 1.1) < 1e-12 and r["at_bound"] == [0], r

    # coordinate descent: a smooth bounded objective whose optimum lies outside the box in one parameter
    c = np.array([0.3, -0.5, 2.5, 0.1])

    def bowl(x):
        return float(np.sum((x - c) ** 2 * np.array([1.0, 3.0, 0.5, 2.0])) + 0.5 * (x[0] - c[0]) * (x[1] - c[1]))

    r = coordinate_descent(bowl, np.zeros(4), -1.0, 1.0)
    want = np.array([0.3, -0.5, 1.0, 0.1])
    R["cd_bowl"] = {"nfev": r["nfev"], "cycles": r["nit"], "max_err": float(np.max(np.abs(r["x"] - want))),
                    "at_bound": r["at_bound"], "message": r["message"]}
    assert np.max(np.abs(r["x"] - want)) <= 2e-3 and r["at_bound"] == [2] and r["nfev"] <= 2000, R["cd_bowl"]

    # Umeyama: a known 3-D similarity is recovered exactly; mirrored data still give a proper rotation
    q, _ = np.linalg.qr(rng.standard_normal((3, 3)))
    q *= np.sign(np.linalg.det(q))
    src = rng.uniform(-100.0, 100.0, (68, 3))
    a = umeyama(src, 1.3 * src @ q.T + np.array([5.0, -2.0, 30.0]))
    R["umeyama"] = {"scale_err": abs(a["s"] - 1.3), "rot_err": float(np.max(np.abs(a["R"] - q))), "rms": a["rms"]}
    assert abs(a["s"] - 1.3) < 1e-12 and np.max(np.abs(a["R"] - q)) < 1e-12 and a["rms"] < 1e-9, R["umeyama"]
    m = umeyama(src, src * np.array([-1.0, 1.0, 1.0]))
    assert abs(np.linalg.det(m["R"]) - 1.0) < 1e-12 and m["rms"] > 1.0
    return R


if __name__ == "__main__":
    import json
    print(json.dumps(selftest(), indent=1, default=float))
