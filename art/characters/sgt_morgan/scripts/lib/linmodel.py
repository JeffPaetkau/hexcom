"""The linear target model (spec 18 §4.8.4, §4.8.6, D3).

MPFB's targets are shape keys relative to their reference key, and Blender mixes relative keys linearly,
out = basis + Σ value_k (key_k − relative_key_k) (times the key's vertex-group weight, if it has one), so
every vertex is an exact linear function of the target weights: p(w) = p0 + Σ_k w_k D_k. Read once (≈ 2 ms a
key), the model predicts landmarks in microseconds and the whole mesh in about a millisecond, which is
what lets an optimiser try thousands of weight vectors between two depsgraph reads, and it gives the
optimisers an exact Jacobian.

Exact for detail targets. MPFB's macro sliders (gender, age, muscle, weight, height, proportions, ...) are
not linear in the slider values: each slider blends corner targets ($md-... keys) with weights that are
products of the other sliders' interpolation weights, and MPFB adds and removes corner keys as sliders
move. So the macro keys stay fixed at their current values, folded into p0, and refresh() re-linearises
after a macro change (reapply_macro_details costs under a millisecond when the corner targets are loaded
already and ≈ 0.2 s when one must be read from disk, measured 2026-10-10). stale() says when that is due.

Positions are the object's own vertices, in world mm through the object's matrix. The evaluated mesh
agrees exactly while the modifiers only mask vertices (MPFB's Hide helpers) or deform at rest; a posed
armature moves it away, by design: spec 06 fits in the rest frame. A key whose shape (not value) changes
needs build() again; the server drops its models after a build, load or restore.
"""
import time

import numpy as np

from . import measure

MM = 1000.0
MACRO_PREFIX = "$md"  # MPFB's macro-detail keys (its encoded names start so)


def _shape_keys(ob):
    if ob.type != "MESH" or ob.data.shape_keys is None:
        raise ValueError(f"{ob.name} has no shape keys to model")
    sk = ob.data.shape_keys
    if not sk.use_relative:
        raise ValueError(f"{ob.name}: absolute shape keys are not linear in their values")
    if ob.show_only_shape_key:
        raise ValueError(f"{ob.name}: a pinned shape key (show only) hides the mix the model describes")
    return sk


class LinearModel:
    """p(w) = p0 + Σ_k w_k D_k over an object's free shape keys (default: every key that is neither the
    reference nor an MPFB macro key), the other keys fixed at their values in p0."""

    def __init__(self, ob, keys=None):
        self.name = measure.obj(ob).name
        self._keys = list(keys) if keys is not None else None
        self.epoch = 0
        self.build()

    def object(self):
        return measure.obj(self.name)

    def _coords(self, kb):
        a = np.empty(self.n * 3, np.float32)
        # ShapeKey.points (Blender 4.1+) reads raw: 0.011 ms for the MPFB body against 2.5 ms through .data
        (kb.points if hasattr(kb, "points") else kb.data).foreach_get("co", a)
        return a.reshape(-1, 3).astype(np.float64)

    def _delta(self, ob, kb, read):
        d = read(kb) - read(kb.relative_key)
        if kb.vertex_group:
            d *= measure.group_weights(ob, kb.vertex_group)[:, None]
        return d

    def _signature(self, ob, sk):
        """What p0 and the matrix depend on: every key's name, mute, relative key and group, the fixed keys'
        values (the free keys' values are the variables), the vertex count and the object's matrix."""
        free = set(self.keys)
        keys = tuple((k.name, None if k.name in free else round(k.value, 12), k.mute, k.relative_key.name,
                      k.vertex_group) for k in sk.key_blocks)
        return keys, len(ob.data.vertices), tuple(np.round(np.array(ob.matrix_world), 12).ravel().tolist())

    def build(self):
        """Read the reference key and every key's coordinates: the free deltas D and the fixed part p0."""
        t = time.perf_counter()
        ob = self.object()
        sk = _shape_keys(ob)
        self.n = len(ob.data.vertices)
        ref = sk.reference_key
        names = [k.name for k in sk.key_blocks]
        keys = self._keys if self._keys is not None else [
            k.name for k in sk.key_blocks if k != ref and not k.name.startswith(MACRO_PREFIX)]
        missing = [k for k in keys if k not in names]
        if missing or ref.name in keys:
            raise ValueError(f"{ob.name}: {'no shape keys ' + str(missing) if missing else 'the reference key cannot be free'}")
        self.keys = keys
        cache = {}

        def read(kb):
            if kb.name not in cache:
                cache[kb.name] = self._coords(kb)
            return cache[kb.name]

        self.D = (np.stack([self._delta(ob, sk.key_blocks[k], read) for k in keys]) if keys
                  else np.zeros((0, self.n, 3)))
        self._fix(ob, sk, read)
        self.reads = len(cache)
        self.build_s = time.perf_counter() - t
        return self

    def _fix(self, ob, sk, read):
        p0 = read(sk.reference_key).copy()
        free = set(self.keys)
        for kb in sk.key_blocks:
            if kb == sk.reference_key or kb.name in free or kb.mute or kb.value == 0.0:
                continue
            p0 += kb.value * self._delta(ob, kb, read)
        self.p0 = p0
        self.matrix = M = np.array(ob.matrix_world, np.float64)
        self._p0w = (p0 @ M[:3, :3].T + M[:3, 3]) * MM    # world mm, for mesh(): the transform folded in
        self._Dw = self.D @ (M[:3, :3].T * MM)
        self.sig = self._signature(ob, sk)
        self.epoch += 1

    def stale(self):
        """Has a fixed key's value (an MPFB macro), the key set or the object's matrix changed since the last
        build or refresh?"""
        ob = self.object()
        return self._signature(ob, _shape_keys(ob)) != self.sig

    def refresh(self):
        """Re-linearise after a macro change: re-read the fixed keys and the matrix (the free deltas are kept
        unless a free key, its relative key or group, or the vertex count changed: then everything is read
        again). Returns True if anything changed."""
        ob = self.object()
        sk = _shape_keys(ob)
        sig = self._signature(ob, sk)
        if sig == self.sig:
            return False
        old = {k[0]: k for k in self.sig[0]}
        now = {k[0]: k for k in sig[0]}
        if sig[1] != self.sig[1] or any(old.get(k) != now.get(k) for k in self.keys):
            self.build()
            return True
        self.n = len(ob.data.vertices)
        cache = {}

        def read(kb):
            if kb.name not in cache:
                cache[kb.name] = self._coords(kb)
            return cache[kb.name]

        self._fix(ob, sk, read)
        return True

    def values(self):
        """The free keys' current values (the w the session holds)."""
        sk = self.object().data.shape_keys
        return np.array([sk.key_blocks[k].value for k in self.keys])

    def apply(self, w):
        """Set the free keys to w (through the parameter registry, which widens a slider to take the value)."""
        from . import params
        params.write({f"key:{self.name}:{k}": float(v) for k, v in zip(self.keys, np.asarray(w, float))},
                     bounds=False)

    def mesh(self, w=None):
        """Every vertex of the object's own mesh for weights w (default: the session's), world mm (n, 3)."""
        w = self.values() if w is None else np.asarray(w, float)
        return self._p0w + np.tensordot(w, self._Dw, axes=1)

    def rows(self, spec):
        """Landmarks of a measure.landmarks() spec as a Rows predictor (exact: landmarks are fixed linear
        combinations of vertices)."""
        return Rows(self, spec)

    def predict(self, w, spec):
        """Landmarks for weights w, world mm; for repeated calls keep model.rows(spec) and call its predict."""
        return Rows(self, spec).predict(w)


class Rows:
    """A landmark spec on a model: predict(w) gives (M, 3) mm in microseconds; J (3M, K) is the exact
    Jacobian in mm per unit weight, rows ordered x, y, z per landmark. Rebuilt by itself after the model
    re-linearises."""

    def __init__(self, model, spec):
        self.model, self.spec = model, spec
        self._make()

    def _make(self):
        m = self.model
        names, idx, w, row = measure.landmark_rows(m.object(), self.spec)
        uniq, col = np.unique(idx, return_inverse=True)
        C = np.zeros((len(names), len(uniq)))
        np.add.at(C, (row, col), w)
        R, t = m.matrix[:3, :3], m.matrix[:3, 3]
        self.names = names
        self.p0 = ((C @ m.p0[uniq]) @ R.T + t) * MM                                      # (M, 3)
        Dl = np.einsum("mu,kuc->kmc", C, m.D[:, uniq, :]) @ R.T * MM                     # (K, M, 3)
        self.Jt = np.ascontiguousarray(Dl.reshape(len(m.keys), -1))                       # (K, 3M)
        self.p0_flat = self.p0.reshape(-1)
        self.epoch = m.epoch

    @property
    def J(self):
        if self.epoch != self.model.epoch:
            self._make()
        return self.Jt.T

    def predict(self, w):
        if self.epoch != self.model.epoch:
            self._make()
        return (self.p0_flat + np.asarray(w, float) @ self.Jt).reshape(-1, 3)


# --------------------------------------------------------------------------- self-test

# Detail targets from the cloud's v2 build (scripts/research/mpfb_build_v2.py): face, neck and shoulders.
DETAIL_TARGETS = ("chin-width-incr", "chin-prominent-incr", "chin-bones-incr", "head-square", "nose-width1-decr",
                  "nose-hump-incr", "l-cheek-bones-incr", "r-cheek-bones-incr", "mouth-scale-horiz-incr",
                  "measure-shoulder-dist-incr", "measure-neck-circ-incr")


def selftest():
    """§8.4 item 5: the model against the depsgraph on a real MPFB human (≤ 0.01 mm), its costs, and a macro
    change: the stale model is off, refresh() makes it exact again (the macro set through params' macro:
    adapter)."""
    from . import params
    R = {}
    human = measure.mpfb_human("SelftestL.Human")
    if human is None:
        return {"mpfb": "MPFB is not enabled in this session: skipped"}
    try:
        from bl_ext.user_default.mpfb.services.targetservice import TargetService
        loaded = []
        for name in DETAIL_TARGETS:
            path = TargetService.target_full_path(name)
            if path:
                loaded.append(TargetService.load_target(human, path, weight=0.0).name)
        R["detail_targets"] = len(loaded)
        assert len(loaded) >= 8, loaded
        model = LinearModel(human)
        R["build_ms"] = round(model.build_s * 1e3, 1)
        R["build_ms_per_key_read"] = round(model.build_s * 1e3 / model.reads, 2)
        R["keys"] = {"free": len(model.keys), "fixed_macro": len(human.data.shape_keys.key_blocks) - 1 - len(model.keys)}
        assert sorted(model.keys) == sorted(loaded), (model.keys, loaded)

        n_eval = len(measure.evaluate(human, ()).co)
        keep = measure.original_index(human, n_eval)
        lm = keep[np.linspace(0, len(keep) - 1, 120).astype(int)].tolist()  # 120 landmarks the mask keeps
        rows = model.rows(lm)
        rng = np.random.default_rng(17)

        def errors(w):
            m = measure.evaluate(human)
            actual = m.original()[keep] * MM
            mesh = float(np.max(np.abs(model.mesh(w)[keep] - actual)))
            lmk = float(np.max(np.abs(rows.predict(w) - measure.landmarks(human, lm))))
            return mesh, lmk

        errs = []
        for _ in range(3):
            w = rng.uniform(-0.5, 1.0, len(model.keys))
            model.apply(w)
            errs.append(errors(w))
        R["max_err_mm"] = {"mesh": max(e[0] for e in errs), "landmarks_120": max(e[1] for e in errs)}
        assert max(max(e) for e in errs) <= 0.01, errs

        w = model.values()
        t = time.perf_counter()
        for _ in range(2000):
            rows.predict(w)
        R["predict_120_landmarks_us"] = round((time.perf_counter() - t) / 2000 * 1e6, 2)
        t = time.perf_counter()
        for _ in range(20):
            model.mesh(w)
        R["predict_mesh_ms"] = round((time.perf_counter() - t) / 20 * 1e3, 3)
        J = rows.J
        assert J.shape == (3 * len(lm), len(model.keys))
        e0 = np.zeros(len(model.keys))
        e0[0] = 1.0
        assert np.allclose(rows.predict(w + e0) - rows.predict(w), J[:, 0].reshape(-1, 3))

        # a macro change through params' macro: adapter: muscle 0.7 -> 0.45 crosses 0.5, so MPFB loads new
        # corner targets; the stale model is off by millimetres until refresh()
        t = time.perf_counter()
        params.write({f"macro:{human.name}:muscle": 0.45})
        R["reapply_new_corner_targets_s"] = round(time.perf_counter() - t, 3)
        assert abs(params.read([f"macro:{human.name}:muscle"])[f"macro:{human.name}:muscle"] - 0.45) < 1e-6  # float32
        assert model.stale()
        R["stale_err_mm"] = round(errors(w)[0], 2)
        t = time.perf_counter()
        assert model.refresh()
        R["refresh_ms"] = round((time.perf_counter() - t) * 1e3, 1)
        after = errors(w)
        R["max_err_after_refresh_mm"] = max(after)
        assert R["stale_err_mm"] > 0.1 and max(after) <= 0.01, (R["stale_err_mm"], after)
        t = time.perf_counter()
        params.write({f"macro:{human.name}:muscle": 0.44})  # the corner targets are loaded now
        R["reapply_loaded_ms"] = round((time.perf_counter() - t) * 1e3, 2)
        assert model.refresh() and max(errors(w)) <= 0.01
        return R
    finally:
        measure._remove(human)
