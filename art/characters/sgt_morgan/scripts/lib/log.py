"""JSON-lines logs and timers (spec 18 §4.3).

A log is one JSON object per line, appended with a single write so two processes logging to one
file interleave whole lines; a line cut short by a killed process is skipped on reading. Timers give
the `timings` of a part's RESULT line and the `ms` of a server reply.
"""
import contextlib
import json
import os
import time


def now():
    """UTC to the second, the evaluation log's `ts` format."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def info(tag, *args):
    print(f"[{tag}]", *args, flush=True)


def jsonable(x):
    """A JSON-safe copy: numpy scalars and arrays, mathutils vectors and sets become lists or numbers."""
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted(jsonable(v) for v in x)
    if hasattr(x, "tolist"):  # numpy
        return x.tolist()
    if hasattr(x, "to_list"):  # IDPropertyArray
        return x.to_list()
    try:  # mathutils Vector, Euler, Color, bpy_prop_array
        return [jsonable(v) for v in x]
    except TypeError:
        return repr(x)


def dumps(record, indent=None):
    return json.dumps(jsonable(record), indent=indent, separators=None if indent else (",", ":"))


def jsonl(path, record=None, **fields):
    """Append one record (with `ts` first) to a JSON-lines file; returns the record."""
    rec = {"ts": now()}
    rec.update(record or {})
    rec.update(fields)
    line = dumps(rec) + "\n"
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(line)
    return rec


def read_jsonl(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except ValueError:  # a line cut short by a killed writer
                    continue
    except OSError:
        pass
    return out


class Timer:
    """Named laps in seconds: `with t("build"): ...`; repeated names add up; `t.seconds` is the dict."""

    def __init__(self):
        self.t0 = time.perf_counter()
        self.seconds = {}

    @contextlib.contextmanager
    def __call__(self, name):
        t = time.perf_counter()
        try:
            yield
        finally:
            self.seconds[name] = round(self.seconds.get(name, 0.0) + time.perf_counter() - t, 4)

    def total(self):
        return round(time.perf_counter() - self.t0, 4)


def selftest():
    import tempfile
    path = os.path.join(tempfile.mkdtemp(prefix="sgt_log_"), "t.jsonl")
    jsonl(path, {"event": "a"}, n=1)
    jsonl(path, event="b", v=(1.5, 2))
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"event": "cut sho')  # a killed writer
    recs = read_jsonl(path)
    assert [r["event"] for r in recs] == ["a", "b"] and recs[1]["v"] == [1.5, 2], recs
    assert list(recs[0])[0] == "ts" and recs[0]["ts"].endswith("Z")
    t = Timer()
    with t("x"):
        time.sleep(0.01)
    with t("x"):
        pass
    assert 0.009 < t.seconds["x"] < 1.0 and t.total() >= t.seconds["x"]
    try:
        import numpy as np
        got = jsonable({"a": np.float32(0.5), "b": np.arange(3), "c": {2, 1}})
        assert got == {"a": 0.5, "b": [0, 1, 2], "c": [1, 2]}, got
    except ImportError:
        pass
    os.remove(path)
    return {"records": len(recs)}
