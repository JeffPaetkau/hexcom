"""Part 01's layers on Body.Mesh, cached beside the part's .blend as cache/parts/01_foot_ankle_sock.layer.npz.

Spec 18 §4.5 gives body-region parts a layer cache (their shape keys and vertex groups on the shared body,
keyed by the body's topology) and lib/cache.py a layer_apply() to restore it; that is not built yet, and a
part cache alone would bring back the nails and frames but not the sculpt. Until it is, this module keeps
the layers and the part script restores them when its cache is fresh, so a run that loads the cache
measures and renders the same foot a build makes. digest() is the idempotency check's hash of the layers
(spec 18 §4.7 rule 1, the shared body's counterpart of cache.mesh_hash).
"""
import hashlib
import io
import json
import os

import numpy as np

from lib import cache, naming
from lib import sculpt as S


def path(part):
    return cache.part_path(part)[:-len(".blend")] + ".layer.npz"


def topology_hash(ob):
    """sha256 of the body's vertex count and polygon corners: a layer fits only the topology it was made on."""
    ls, lt, lv = S.topology(ob.data)
    h = hashlib.sha256(str(len(ob.data.vertices)).encode())
    for a in (lt.astype("<i4"), lv.astype("<i4")):
        h.update(a.tobytes())
    return h.hexdigest()


def _owned_keys(ob, part):
    sk = ob.data.shape_keys
    return [k for k in sk.key_blocks if naming.owned(k.name, part.prefixes)] if sk else []


def _owned_groups(ob, part):
    return [g for g in ob.vertex_groups if naming.owned(g.name, part.prefixes)]


def read(ob, part):
    """The part's layers: {"keys": {name: (meta, offsets from the basis (n, 3) float32)}, "groups": {name:
    weights (n,) float32}}."""
    basis = S.key_coords(ob.data.shape_keys.reference_key) if ob.data.shape_keys else None
    keys = {}
    for kb in _owned_keys(ob, part):
        meta = {"value": kb.value, "min": kb.slider_min, "max": kb.slider_max, "relative": kb.relative_key.name,
                "group": kb.vertex_group, "mute": kb.mute}
        keys[kb.name] = (meta, (S.key_coords(kb) - basis).astype(np.float32))
    names = [g.name for g in _owned_groups(ob, part)]
    groups = {n: w.astype(np.float32) for n, w in S.group_weights_many(ob, names).items()}
    return {"keys": keys, "groups": groups}


def digest(ob, part):
    """sha256 of the part's layers on the body: key offsets rounded to 0.01 mm, weights to 1e-4."""
    lay = read(ob, part)
    h = hashlib.sha256()
    for name in sorted(lay["keys"]):
        meta, off = lay["keys"][name]
        h.update(name.encode())
        h.update(np.round(off.astype(np.float64) * 1e5).astype("<i8").tobytes())
    for name in sorted(lay["groups"]):
        h.update(name.encode())
        h.update(np.round(lay["groups"][name].astype(np.float64) * 1e4).astype("<i8").tobytes())
    return h.hexdigest()


def save(part, ob, key):
    """Write the layers next to the part's cache (atomically), tagged with the cache key they belong to."""
    lay = read(ob, part)
    arrays, meta = {}, {"key": key, "topology": topology_hash(ob), "keys": {}, "groups": []}
    for i, (name, (m, off)) in enumerate(sorted(lay["keys"].items())):
        arrays[f"k{i}"] = off
        meta["keys"][name] = dict(m, array=f"k{i}", order=i)
    for i, (name, w) in enumerate(sorted(lay["groups"].items())):
        nz = np.nonzero(w)[0]
        arrays[f"gi{i}"], arrays[f"gw{i}"] = nz.astype(np.int32), w[nz]
        meta["groups"].append(name)
    buf = io.BytesIO()
    np.savez_compressed(buf, meta=np.frombuffer(json.dumps(meta).encode(), np.uint8), **arrays)
    cache.write_bytes(path(part), buf.getvalue())
    return path(part)


def load_meta(part):
    p = path(part)
    if not os.path.isfile(p):
        return None
    with np.load(p) as z:
        return json.loads(bytes(z["meta"]).decode())


def apply(part, ob):
    """Put the cached layers back on the body (replacing any of the part's own); False if there is no
    cache or it was made on another topology."""
    p = path(part)
    if not os.path.isfile(p):
        return False
    with np.load(p) as z:
        meta = json.loads(bytes(z["meta"]).decode())
        if meta["topology"] != topology_hash(ob):
            return False
        for kb in _owned_keys(ob, part):
            ob.shape_key_remove(kb)
        for g in _owned_groups(ob, part):
            ob.vertex_groups.remove(g)
        if ob.data.shape_keys is None:
            ob.shape_key_add(name="Basis", from_mix=False)
        basis = S.key_coords(ob.data.shape_keys.reference_key)
        for name, m in sorted(meta["keys"].items(), key=lambda kv: kv[1]["order"]):
            kb = ob.shape_key_add(name=name, from_mix=False)
            co = (basis + z[m["array"]].astype(np.float64)).astype(np.float32).ravel()
            (kb.points if hasattr(kb, "points") else kb.data).foreach_set("co", co)
            kb.slider_min, kb.slider_max, kb.value, kb.mute = m["min"], m["max"], m["value"], m["mute"]
            if m["relative"] in ob.data.shape_keys.key_blocks:
                kb.relative_key = ob.data.shape_keys.key_blocks[m["relative"]]
            kb.vertex_group = m["group"] or ""
        for i, name in enumerate(meta["groups"]):
            g = ob.vertex_groups.new(name=name)
            idx, w = z[f"gi{i}"], z[f"gw{i}"]
            for value in np.unique(w):
                g.add(idx[w == value].tolist(), float(value), "REPLACE")
    ob.data.update()
    return True
