"""assets/interfaces.json: the contract between parts (spec 18 D9, §4.3).

Each part writes only keys under its own prefixes (`rifle.*` for 15; `shirt.*` and `gaiter.*` for 10).
Readers name the keys they read, and the hashes of the values they got go into their cache key, so a
changed value marks every reader stale. The file is tracked, so it holds values only (no timestamps),
sorted, with floats rounded to 0.1 µm (values are in mm), and it is rewritten only when a value
changes: a diff shows a real change and nothing else.
"""
from . import cache, env, log

PATH = env.path("assets", "interfaces.json")
ROUND = 4  # decimals of a mm: far under any tolerance, and it hides float noise between machines
MISSING = "missing"


def _round(v):
    if isinstance(v, float):
        return round(v, ROUND) + 0.0  # + 0.0 turns -0.0 into 0.0
    if isinstance(v, dict):
        return {k: _round(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_round(x) for x in v]
    return v


def load(path=None):
    return cache.read_json(path or PATH) or {}


def value_hash(key, data=None):
    """A short hash of a key's current value, or "missing"; what a reader's cache key records."""
    data = load() if data is None else data
    return cache.sha256_bytes(cache.canonical(data[key]).encode())[:16] if key in data else MISSING


def _owns(part, key):
    return any(key.startswith(p) for p in part.keys)


def write(part, values, replace=False, path=None):
    """Publish a part's values; returns the keys that changed (none: the file is left alone).

    `replace` also drops the part's keys that `values` does not name (a renamed key must not linger)."""
    path = path or PATH
    bad = sorted(k for k in values if not _owns(part, k))
    if bad:
        raise ValueError(f"part {part.id} may write only keys under {part.keys}, not {bad}")
    values = {k: _round(log.jsonable(v)) for k, v in values.items()}
    with cache.locked(path):
        old = load(path)
        new = {k: v for k, v in old.items() if not (replace and _owns(part, k) and k not in values)}
        new.update(values)
        changed = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
        if changed:
            cache.write_json(path, new)
    return changed


def read(keys, path=None):
    """Values of the named keys.

    `keys` is a list (a key not published yet is a missing hard dependency, exit 3) or a dict of
    fallbacks (a missing key takes the spec's number and is logged as [FALLBACK]). The value hashes go
    into the reading build's key, so publishing the key later marks the reader stale."""
    from . import cli
    data = load(path)
    ctx = cli.active()
    out, missing = {}, []
    for k in keys:
        if k in data:
            out[k] = data[k]
        elif isinstance(keys, dict):
            out[k] = keys[k]
            msg = f"[FALLBACK] {k} = {keys[k]!r}: not in assets/interfaces.json yet"
            ctx.warn(msg) if ctx is not None else print(msg, flush=True)
        else:
            missing.append(k)
        if ctx is not None:
            ctx.reads["interfaces"][k] = value_hash(k, data)
    if missing:
        raise cli.MissingDependency(f"interface keys not published yet: {missing}")
    return out


def selftest():
    import os
    import shutil
    import threading
    from . import cli
    global PATH
    scratch = env.path("cache", "selftest", "interfaces")
    shutil.rmtree(scratch, ignore_errors=True)
    old, PATH = PATH, os.path.join(scratch, "interfaces.json")
    try:
        rifle = cli.Part(id="15", name="carbine", prefixes=("Rifle.",))
        carrier = cli.Part(id="13", name="plate_carrier", prefixes=("Carrier.", "Vest."))
        assert rifle.keys == ("rifle.",) and carrier.keys == ("carrier.", "vest.")
        changed = write(rifle, {"rifle.oal": 855.8, "rifle.section_handguard": (38.1, 49.3),
                                "rifle.frames": {"grip": (0.0, -169.00000001, -94.8)}, "rifle.zero": -0.00001})
        assert changed == ["rifle.frames", "rifle.oal", "rifle.section_handguard", "rifle.zero"], changed
        data = load()
        assert data["rifle.frames"]["grip"] == [0.0, -169.0, -94.8] and str(data["rifle.zero"]) == "0.0", data
        st = os.stat(PATH)
        assert write(rifle, {"rifle.oal": 855.80000001}) == [] and os.stat(PATH).st_mtime_ns == st.st_mtime_ns
        try:
            write(rifle, {"carrier.top_edge": 1475})
            raise AssertionError("a part wrote another part's key")
        except ValueError:
            pass
        write(carrier, {"carrier.top_edge": 1475, "vest.collider_offset": 31})
        h0 = value_hash("rifle.oal")
        assert write(rifle, {"rifle.oal": 856.0}, replace=True) == [
            "rifle.frames", "rifle.oal", "rifle.section_handguard", "rifle.zero"]
        assert value_hash("rifle.oal") != h0 and "carrier.top_edge" in load() and "rifle.frames" not in load()
        assert read(["rifle.oal"]) == {"rifle.oal": 856.0}
        assert read({"torso.ring.Hem": 1053, "rifle.oal": 0}) == {"torso.ring.Hem": 1053, "rifle.oal": 856.0}
        try:
            read(["torso.ring.Hem"])
            raise AssertionError("a missing key was not a missing dependency")
        except cli.MissingDependency:
            pass

        def publish(part, prefix):
            for i in range(10):
                write(part, {f"{prefix}n{i}": i})
        ts = [threading.Thread(target=publish, args=a) for a in ((rifle, "rifle."), (carrier, "carrier."))]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        data = load()
        assert all(f"rifle.n{i}" in data and f"carrier.n{i}" in data for i in range(10)), sorted(data)
        return {"keys": len(data)}
    finally:
        PATH = old
        shutil.rmtree(scratch, ignore_errors=True)
