"""The standard part interface (spec 18 §4.4): the PART record, the command line, the context a build
runs in, the RESULT line and the exit codes.

  blender -b [input.blend] --python-exit-code 1 --python scripts/parts/NN_name.py -- [--rebuild]
      [--stage S | --stage S1..S2] [--render] [--views V1,V4] [--quality form|look|eval|cal|final]
      [--params FILE|JSON] [--seed 17] [--proxy 01,13] [--check] [--from-cache] [--json]

Exit codes: 0 pass, 2 a tolerance failed, 3 a hard dependency is missing, 4 a Blender or Python error
(a bad argument too: argparse's own exit 2 would read as a tolerance failure). Without --rebuild a part
whose cache is fresh is loaded rather than rebuilt; --check builds and measures but saves nothing.
main() is the script's entry point; run() does the same work and returns the RESULT dict without
exiting, so build_all.py and the server build parts in-process. Readers take the last stdout line that
starts with `RESULT `: on Windows Blender's own buffered output (its banner) is flushed after it.
"""
import argparse
import importlib
import importlib.util
import json
import os
import random
import re
import sys
import traceback
from dataclasses import dataclass, field

from . import env, log, naming

PASS, TOLERANCE, MISSING, ERROR = 0, 2, 3, 4
QUALITIES = ("form", "look", "eval", "cal", "final")
DEFAULT_SEED = 17


class MissingDependency(Exception):
    """A hard dependency is absent: exit 3, naming it (§4.7 rule 5)."""


class UsageError(Exception):
    """A bad command line: exit 4."""


@dataclass(frozen=True)
class Part:
    """A part's declaration (§4.4). Defaults: collection `PartNN.<Name>`; interface-key prefixes `keys`
    from the object prefixes with the first letter lowered (`Rifle.` -> `rifle.`); `script`
    scripts/parts/NN_name.py; `presets` pNN; `params` scripts/parts/pNN/params.json (if present)."""
    id: str
    name: str
    collection: str = ""
    prefixes: tuple = ()
    needs: dict = field(default_factory=dict)  # hard: {part id: the object it must provide}
    proxies: dict = field(default_factory=dict)  # soft: {part id: the stand-in this part builds}
    provides: tuple = ()
    stages: tuple = ()
    presets: str = ""
    params: str = ""
    keys: tuple = ()
    script: str = ""

    def __post_init__(self):
        if not re.match(r"^\d{2}$", self.id):
            raise ValueError(f"part id {self.id!r}: two digits, as in the spec numbers")
        if not re.match(r"^[a-z][a-z0-9_]*$", self.name):
            raise ValueError(f"part name {self.name!r}: lower case, underscores")
        if not self.prefixes:
            raise ValueError(f"part {self.id} declares no prefixes")
        put = object.__setattr__
        put(self, "prefixes", tuple(naming.check_prefix(p) for p in self.prefixes))
        put(self, "collection", naming.check(self.collection or naming.collection_name(self.id, self.name)))
        put(self, "keys", tuple(self.keys) or tuple(p[0].lower() + p[1:] for p in self.prefixes))
        put(self, "script", self.script or f"scripts/parts/{self.slug}.py")
        put(self, "presets", self.presets or f"p{self.id}")
        put(self, "params", self.params or f"scripts/parts/p{self.id}/params.json")
        put(self, "stages", tuple(self.stages))
        put(self, "provides", tuple(self.provides))
        if len(set(self.stages)) != len(self.stages):
            raise ValueError(f"part {self.id} repeats a stage name")

    @property
    def slug(self):
        return f"{self.id}_{self.name}"


# --------------------------------------------------------------------------- arguments

class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def parser():
    p = _Parser(prog="blender -b --python scripts/parts/NN_name.py --", description=__doc__.split("\n\n")[0])
    p.add_argument("--rebuild", action="store_true", help="ignore the part cache and rebuild every stage")
    p.add_argument("--stage", default="", help="one stage, or a range S1..S2; earlier stages come from the cache")
    p.add_argument("--render", action="store_true", help="render the views after building")
    p.add_argument("--views", default="", help="preset ids or labels, comma-separated (default: all)")
    p.add_argument("--quality", default="form", choices=QUALITIES, help="spec 17's render tier")
    p.add_argument("--params", default="", help="a JSON object or file merged over pNN/params.json")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED, help="feeds every random draw")
    p.add_argument("--proxy", default="", help="force the declared stand-ins for these part ids")
    p.add_argument("--check", action="store_true", help="build and measure, assert tolerances, save nothing")
    p.add_argument("--from-cache", action="store_true", help="load the cached part, then only render or measure")
    p.add_argument("--json", action="store_true", help="print RESULT {json} as the last line")
    return p


def parse(argv=()):
    a = parser().parse_args(list(argv))
    if a.stage and a.rebuild:
        raise UsageError("--stage runs some stages on the cached part; --rebuild runs them all: pick one")
    if a.from_cache and (a.rebuild or a.stage or a.check):
        raise UsageError("--from-cache only loads; it cannot be combined with --rebuild, --stage or --check")
    return a


def _merge(base, over):
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_params(part, override=""):
    """pNN/params.json with --params merged over it (nested objects merge key by key)."""
    from . import cache
    base = cache.read_json(env.path(part.params)) or {}
    if not override:
        return base
    if override.lstrip().startswith("{"):
        try:
            extra = json.loads(override)
        except ValueError as e:
            raise UsageError(f"--params is not valid JSON: {e}") from None
    else:
        extra = cache.read_json(override if os.path.isabs(override) else env.path(override))
        if extra is None:
            raise UsageError(f"--params: cannot read {override}")
    if not isinstance(extra, dict):
        raise UsageError("--params must be a JSON object")
    return _merge(base, extra)


# --------------------------------------------------------------------------- the build context

_active = []  # contexts of runs in progress, innermost last
# part id -> the Context of its last successful run in this process; kept over the server's reloads
LAST = globals().get("LAST", {})


def active():
    """The Context of the build in progress, for save_part, interfaces.read and cache.asset."""
    return _active[-1] if _active else None


def _present(name):
    import bpy
    return any(getattr(bpy.data, t).get(name) is not None
               for t in ("objects", "collections", "armatures", "meshes", "cameras", "node_groups", "images"))


class Context:
    """What build() and measure() receive: the part, its merged params, the seed, its dependencies as
    resolved (proxies included), and the records that go into the cache key and the RESULT line."""

    def __init__(self, part, args, timer=None):
        self.part, self.args = part, args
        self.seed = args.seed
        self.params = load_params(part, args.params)
        self.partial = bool(args.stage)
        self.deps = {}  # part id -> its cache key, "session" or "proxy:<name>"
        self.proxied = {}  # part id -> the stand-in the build must make
        self.reads = {"manifest": {}, "interfaces": {}}
        self.outputs, self.warnings, self.stages_run = [], [], []
        self.cache = None  # built and saved, fresh, loaded, or unsaved
        self.key = None
        self.timer = timer or log.Timer()
        self.selected = self._select(args.stage)  # checked now, before anything is removed

    def _select(self, spec):
        names = list(self.part.stages)
        if not spec:
            return names
        first, _, last = spec.partition("..")
        last = last or first
        for s in (first, last):
            if s not in names:
                raise UsageError(f"part {self.part.id} has no stage {s!r}; its stages are {names}")
        i, j = names.index(first), names.index(last)
        if j < i:
            raise UsageError(f"--stage {spec}: {last} comes before {first}")
        return names[i:j + 1]

    def warn(self, msg):
        self.warnings.append(msg)
        log.info(f"part {self.part.id}", msg)

    def output(self, path):
        self.outputs.append(os.path.relpath(path, env.PROJECT_DIR).replace(os.sep, "/"))

    def saved(self, rec, files):
        self.cache, self.key = "saved", rec["key"]
        for f in files:
            self.output(f)

    def proxy(self, dep):
        """The stand-in to build for dependency `dep`, or None when the real one is here."""
        return self.proxied.get(dep)

    def stages(self, args=None):
        """The stages to run, each timed. --stage S or S1..S2 first loads the part's saved cache, so the
        earlier stages' results are there; each stage then replaces only its own objects (Scope.clear)."""
        names = self._select((args or self.args).stage)
        if self.partial:
            from . import cache
            cache.load_part(self.part)
        for s in names:
            self.stages_run.append(s)
            with self.timer(f"stage {s}"):
                yield s

    def resolve(self):
        """Each dependency from this session, else from its part cache (linked, read-only), else its
        declared proxy; a hard one with none of these is exit 3."""
        from . import cache
        forced = [d for d in self.args.proxy.split(",") if d]
        unknown = [d for d in forced if d not in self.part.proxies]
        if unknown:
            raise UsageError(f"--proxy {','.join(unknown)}: part {self.part.id} declares stand-ins only for "
                             f"{sorted(self.part.proxies) or 'nothing'}")
        for dep in sorted(set(self.part.needs) | set(self.part.proxies)):
            want = self.part.needs.get(dep)
            rec = cache.read_key(dep) or {}
            if dep in forced:
                self._proxy(dep, "forced by --proxy")
            elif want and _present(want):
                self.deps[dep] = rec.get("key") or "session"
            elif cache.part_path(dep):
                cache.load_part(dep, link=True)
                if want and not _present(want):
                    raise MissingDependency(f"part {dep}'s cache does not hold {want}")
                self.deps[dep] = rec.get("key") or "unversioned"
            elif dep in self.part.proxies:
                self._proxy(dep, "no cache")
            else:
                raise MissingDependency(f"part {dep} ({want}): not in this session and no cache/parts/{dep}_*.blend")

    def _proxy(self, dep, why):
        name = self.part.proxies[dep]
        self.proxied[dep] = name
        self.deps[dep] = f"proxy:{name}"
        self.warn(f"proxy: dependency {dep} is the stand-in {name} ({why})")


# --------------------------------------------------------------------------- measurements

def _passes(value, target, tol):
    try:
        if isinstance(target, (list, tuple)) and len(target) == 2 and tol is None:
            return bool(target[0] <= value <= target[1])
        if target is None or tol is None:
            return None
        if isinstance(value, (list, tuple)):
            return bool(max(abs(v - t) for v, t in zip(value, target)) <= tol)
        return bool(abs(value - target) <= tol)
    except TypeError:
        return None


def metric(name, value, target=None, tol=None, unit="mm", source="", part=None):
    """One measure() item in the §4.8.4 envelope. Pass is |value - target| <= tol (the largest
    component for a vector), lo <= value <= hi for a [lo, hi] target, None when there is no tolerance."""
    return {"part": part, "metric": name, "value": value, "target": target, "tol": tol, "unit": unit,
            "pass": _passes(value, target, tol), "source": source}


def envelopes(part, out):
    """measure()'s return as a list of envelopes: a list of them, or {name: envelope or bare value}."""
    if out is None:
        return []
    items = out if isinstance(out, list) else [
        dict(v, metric=k) if isinstance(v, dict) else {"metric": k, "value": v} for k, v in out.items()]
    res = []
    for m in items:
        m = dict(m)
        m["part"] = m.get("part") or part.id
        for k in ("target", "tol", "unit", "source"):
            m.setdefault(k, None)
        if "pass" not in m:
            m["pass"] = _passes(m.get("value"), m["target"], m["tol"])
        res.append(log.jsonable(m))
    return res


# --------------------------------------------------------------------------- running a part

def _render(ctx):
    """--render: spec 17's harness renders the --views, else every preset the part owns, at --quality,
    into renders/<part>/ with a sidecar each; until the harness exists the run says so."""
    if not os.path.isfile(env.path("scripts", "eval", "render.py")):
        ctx.warn("--render: scripts/eval/render.py is not written yet; nothing rendered")
        return
    env.bootstrap()
    harness = importlib.import_module("eval.render")  # import_module: `import eval` would shadow eval()
    camera = importlib.import_module("eval.camera")
    names = [v for v in ctx.args.views.split(",") if v] or camera.load_registry().owner_ids(ctx.part.id)
    if not names:
        ctx.warn(f"--render: no presets owned by part {ctx.part.id} in scripts/eval/presets; nothing rendered")
    for n in names:
        side = harness.render_preset(n, tier=ctx.args.quality)
        for p in (side or {}).get("outputs", {}).values():
            ctx.output(env.path(p))


def run(part, build, measure=None, argv=()):
    """Build (or load) and measure a part as the arguments say; returns the RESULT dict, never exits."""
    from . import cache
    timer = log.Timer()
    res = {"part": part.id, "name": part.name, "status": "error", "exit": ERROR}
    ctx = None
    try:
        args = parse(argv)
        ctx = Context(part, args, timer)
        _active.append(ctx)
        random.seed(args.seed)
        try:
            import numpy
            numpy.random.seed(args.seed)  # a part should use its own generator; this catches one that does not
        except ImportError:
            pass
        with timer("deps"):
            ctx.resolve()
        if args.from_cache:
            with timer("load"):
                cache.load_part(part)
            ctx.cache = "loaded"
        else:
            forced = next((f"--{f}" for f in ("rebuild", "stage", "check") if getattr(args, f)), None)
            ok, why = (False, [forced]) if forced else cache.fresh(part, ctx)
            if ok:
                with timer("load"):
                    cache.load_part(part)
                ctx.cache, ctx.key = "fresh", (cache.read_key(part) or {}).get("key")
            else:
                res["stale"] = why
                with timer("build"):
                    build(ctx, args)
                ctx.cache = ctx.cache or "unsaved"
        missing = [n for n in part.provides if not _present(n)]
        if missing:
            raise RuntimeError(f"part {part.id} did not make what it provides: {missing}")
        if args.render:
            with timer("render"):
                _render(ctx)
        metrics = []
        if measure is not None:
            with timer("measure"):
                metrics = envelopes(part, measure(ctx, args))
        failed = [m["metric"] for m in metrics if m.get("pass") is False]
        res.update(status="tolerance" if failed else "pass", exit=TOLERANCE if failed else PASS,
                   metrics=metrics, failed=failed)
        LAST[part.id] = ctx
    except MissingDependency as e:
        res.update(status="missing", exit=MISSING, error=str(e))
    except UsageError as e:
        res.update(status="usage", exit=ERROR, error=str(e))
    except SystemExit as e:  # --help, or a part calling sys.exit: the server must outlive it
        code = e.code if isinstance(e.code, int) else ERROR
        res.update(status="exit", exit=code, error=None if code == 0 else f"sys.exit({e.code!r}) in the part")
    except Exception as e:
        res.update(status="error", exit=ERROR, error=f"{type(e).__name__}: {e}",
                   trace=traceback.format_exc(limit=-8))
    finally:
        if ctx is not None and ctx in _active:
            _active.remove(ctx)
    if ctx is not None:
        res.update(cache=ctx.cache, key=ctx.key, seed=ctx.seed, stages=ctx.stages_run, deps=ctx.deps,
                   proxies=ctx.proxied, outputs=ctx.outputs, warnings=ctx.warnings)
    res["timings"] = dict(timer.seconds, total=timer.total())
    return res


def main(part, build, measure=None):
    """The part script's entry point: run, report, exit with the code."""
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    res = run(part, build, measure, argv)
    if "--json" in argv:
        print("RESULT " + log.dumps(res), flush=True)
    else:
        print(f"[part {part.id}] {res['status']} (exit {res['exit']}), cache {res.get('cache')}, "
              f"{res['timings']['total']} s", flush=True)
        for w in res.get("warnings", []):
            print(f"[part {part.id}] warning: {w}", flush=True)
        for m in res.get("metrics", []):
            if m.get("pass") is False:
                print(f"[part {part.id}] FAIL {m['metric']} = {m['value']} (target {m['target']} +/- {m['tol']})")
        if res.get("error"):
            print(res.get("trace") or res["error"], flush=True)
    sys.stdout.flush()
    sys.exit(res["exit"])


# --------------------------------------------------------------------------- self-test

# A scratch part for the selftests here and in bl.py: two stages, a size parameter (20 mm passes, the
# tolerance is ±1), `explode` to raise, and its cache in a scratch folder.
TEST_PART = '''"""A scratch part written by a selftest (lib/cli.py TEST_PART)."""
import sys
sys.path.insert(0, {scripts!r})
from lib import cache, cli, replace
cache.PARTS_DIR = {parts!r}
PART = cli.Part(id="95", name="cli_selftest", prefixes=("SelftestK.",), stages=("base", "detail"),
                script={script!r})
BUILDS = []


def build(ctx, args):
    import bpy
    BUILDS.append(1)
    if ctx.params.get("explode"):
        raise ZeroDivisionError("asked to")
    with replace.part_scope(PART) as scope:
        for stage in ctx.stages(args):
            if stage == "base":
                scope.clear("SelftestK.Base")
                me = bpy.data.meshes.new("SelftestK.Base")
                s = ctx.params.get("size_mm", 20) / 1000
                me.from_pydata([(0, 0, 0), (s, 0, 0), (0, s, 0)], [], [(0, 1, 2)])
                scope.new_object("SelftestK.Base", me)
            elif stage == "detail":
                scope.clear("SelftestK.Detail")
                scope.new_object("SelftestK.Detail", None)
    cache.save_part(PART)


def measure(ctx, args):
    import bpy
    ob = bpy.data.objects["SelftestK.Base"]
    size = max(v.co.x for v in ob.data.vertices) * 1000
    return [cli.metric("size", size, target=20, tol=1, source="selftest")]


if __name__ == "__main__":
    cli.main(PART, build, measure)
'''


def selftest():
    import json
    import shutil
    import subprocess
    import bpy
    from . import cache
    for bad in (dict(id="2", name="x", prefixes=("X.",)), dict(id="02", name="X", prefixes=("X.",)),
                dict(id="02", name="x", prefixes=("x.",)), dict(id="02", name="x")):
        try:
            Part(**bad)
            raise AssertionError(f"accepted {bad}")
        except ValueError:
            pass
    p = Part(id="02", name="boots", prefixes=("Boot.",))
    assert (p.collection, p.keys, p.script, p.presets) == (
        "Part02.Boots", ("boot.",), "scripts/parts/02_boots.py", "p02")
    for argv in (["--stage", "a", "--rebuild"], ["--quality", "bogus"], ["--from-cache", "--check"], ["--nope"]):
        try:
            parse(argv)
            raise AssertionError(f"parsed {argv}")
        except UsageError:
            pass
    assert metric("w", 20.4, 20, 0.5)["pass"] and not metric("w", 21, 20, 0.5)["pass"]
    assert metric("w", 3, [1, 5])["pass"] and metric("w", 3)["pass"] is None
    assert metric("v", [1.0, 2.2], [1, 2], 0.25)["pass"]

    scratch = env.path("cache", "selftest", "cli")
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    src = os.path.join(scratch, "95_cli_selftest.py")
    with open(src, "w", newline="\n") as f:
        f.write(TEST_PART.format(scripts=env.SCRIPTS_DIR, parts=os.path.join(scratch, "parts"),
                                    script=os.path.relpath(src, env.PROJECT_DIR).replace(os.sep, "/")))
    old_dir = cache.PARTS_DIR
    spec = importlib.util.spec_from_file_location("selftest_part_95", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # sets cache.PARTS_DIR to the scratch folder
    part, out = mod.PART, {}
    try:
        def go(*argv):
            return run(part, mod.build, mod.measure, argv)
        r = go("--json")
        assert r["status"] == "pass" and r["cache"] == "saved" and r["stages"] == ["base", "detail"], r
        key = r["key"]
        r = go()
        assert r["cache"] == "fresh" and r["key"] == key and len(mod.BUILDS) == 1, (r, mod.BUILDS)
        r = go("--params", '{"size_mm": 30}')
        assert r["exit"] == TOLERANCE and r["failed"] == ["size"] and r["stale"] == ["params"], r
        r = go("--check")
        assert r["cache"] == "unsaved" and r["exit"] == PASS and (cache.read_key(part) or {}).get("key") != key
        r = go()
        assert r["cache"] == "saved" and r["key"] == key, r  # the size 30 cache was stale; rebuilt
        hashes = cache.read_key(part)["objects"]
        r = go("--stage", "detail")
        assert r["stages"] == ["detail"] and cache.read_key(part)["partial"], r
        assert cache.fresh(part, Context(part, parse([])))[0] is False
        r = go("--rebuild")
        assert cache.read_key(part)["objects"] == hashes and not cache.read_key(part)["partial"], "not idempotent"
        assert go("--params", '{"explode": true}')["exit"] == ERROR
        r = go("--stage", "nope")
        assert r["status"] == "usage" and r["exit"] == ERROR, r

        hard = Part(id="94", name="dep_selftest", prefixes=("SelftestD.",), needs={"93": "SelftestNo.Thing"},
                    script=part.script)
        r = run(hard, lambda c, a: None, None, ())
        assert r["exit"] == MISSING and "SelftestNo.Thing" in r["error"], r
        soft = Part(id="94", name="dep_selftest", prefixes=("SelftestD.",), needs={"93": "SelftestNo.Thing"},
                    proxies={"93": "stand_in_thing"}, script=part.script)
        r = run(soft, lambda c, a: None, None, ("--check",))
        assert r["exit"] == PASS and r["proxies"] == {"93": "stand_in_thing"} and r["warnings"], r
        assert run(soft, lambda c, a: None, None, ("--proxy", "92"))["status"] == "usage"
        promise = Part(id="94", name="dep_selftest", prefixes=("SelftestD.",), provides=("SelftestD.Gone",),
                       script=part.script)
        assert "did not make" in run(promise, lambda c, a: None, None, ("--check",))["error"]

        # the real command line in a fresh Blender: exit code and the RESULT line
        argv, environ = env.blender_cmd(["-b", "--factory-startup", "--python-exit-code", "1",
                                         "--python", src, "--", "--json", "--params", '{"size_mm": 25}'])
        argv[0] = bpy.app.binary_path
        p = subprocess.run(argv, env=environ, cwd=env.PROJECT_DIR, capture_output=True, encoding="utf-8",
                           errors="replace", timeout=120)
        lines = [ln for ln in p.stdout.splitlines() if ln.startswith("RESULT ")]
        assert p.returncode == TOLERANCE and lines, (p.returncode, p.stdout[-2000:], p.stderr[-2000:])
        sub = json.loads(lines[-1][len("RESULT "):])
        assert sub["status"] == "tolerance" and abs(sub["metrics"][0]["value"] - 25.0) < 1e-3, sub
        out.update(subprocess_exit=p.returncode,
                   last_line_is_result=p.stdout.rstrip().splitlines()[-1].startswith("RESULT "))
        return out
    finally:
        cache.PARTS_DIR = old_dir
        from . import replace
        replace.remove(part)
        coll = replace.local("collections", part.collection)
        if coll is not None:
            bpy.data.collections.remove(coll)
        replace.purge()
        shutil.rmtree(scratch, ignore_errors=True)
