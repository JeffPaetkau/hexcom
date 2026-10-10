"""Part caches, content keys, atomic writes and the build journal (spec 18 §4.5, §4.7).

A part's cache is cache/parts/NN_name.blend, holding only the part's own data-blocks (written
uncompressed with bpy.data.libraries.write, which expands what they point at), and NN_name.key.json
beside it. The key is a sha256 over every input of the build: the part script and every module under
scripts/ it imports, its parameters, the seed, its dependencies' keys, the manifest files and
interface keys it read, and the Blender and MPFB versions. A part is stale when the key recomputed
now differs from the stored one, and fresh() names the inputs that changed.

The file helpers need no Blender, so plain-Python tools use them too.
"""
import ast
import contextlib
import glob
import hashlib
import json
import os
import re
import time

from . import env, log

PARTS_DIR = env.path("cache", "parts")
JOURNAL = env.path("cache", "build_state.json")
MANIFEST = env.path("assets", "manifest.json")


# --------------------------------------------------------------------------- files

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path, text=False):
    """Hex digest of a file; sources are hashed with LF line ends, so git's eol setting cannot move a key."""
    with open(path, "rb") as f:
        data = f.read()
    return sha256_bytes(data.replace(b"\r\n", b"\n") if text else data)


def canonical(obj):
    """The JSON text that keys hash: sorted keys, no spaces, ASCII only."""
    return json.dumps(log.jsonable(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _replace(src, dst):
    # Windows refuses to replace a file another process has open for a moment (a viewer, a scanner)
    for attempt in range(10):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if os.name != "nt" or attempt == 9:
                raise
            time.sleep(0.05)


@contextlib.contextmanager
def atomic(path):
    """Yield a temporary name beside `path` that replaces `path` on success and is removed on error.

    For writers that need a file name (libraries.write, renders). A killed process leaves the old file
    or the new one, never half of one (§4.7 rule 3). The extension is kept so Blender accepts the name."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    root, ext = os.path.splitext(path)
    tmp = f"{root}.tmp{os.getpid()}{ext}"
    try:
        yield tmp
        _replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def write_bytes(path, data):
    with atomic(path) as tmp:
        with open(tmp, "wb") as f:
            f.write(data)


def write_json(path, obj, indent=1):
    write_bytes(path, (json.dumps(log.jsonable(obj), indent=indent, sort_keys=True) + "\n").encode("utf-8"))


def read_json(path, default=None):
    """The file's JSON, or `default` if it is missing or unreadable as JSON.

    On Windows a file just replaced can be held for a moment by a scanner or indexer; that is retried
    like `_replace`, and raised if it persists, because answering `default` there would let a
    read-modify-write (the journal, interfaces.json) rebuild the file from nothing."""
    for attempt in range(10):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return default
        except PermissionError:
            if os.name != "nt" or attempt == 9:
                raise
            time.sleep(0.05)
        except (OSError, ValueError):
            return default


@contextlib.contextmanager
def locked(path, timeout=30.0, stale=120.0):
    """An exclusive lock file beside `path`, for read-modify-write by two agents' processes."""
    lock = path + ".lock"
    os.makedirs(os.path.dirname(os.path.abspath(lock)), exist_ok=True)
    t0 = time.time()
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except (FileExistsError, PermissionError) as e:
            # Windows answers PermissionError, not FileExistsError, while the last holder's delete of
            # the lock file is still pending: the lock is busy, not forbidden
            if isinstance(e, PermissionError) and os.name != "nt":
                raise
            try:
                if time.time() - os.path.getmtime(lock) > stale:  # its holder was killed
                    os.remove(lock)
                    continue
            except OSError:
                continue
            if time.time() - t0 > timeout:
                raise TimeoutError(f"lock held for {timeout} s: {lock}")
            time.sleep(0.02)
    try:
        yield
    finally:
        try:
            os.remove(lock)
        except OSError:
            pass


# --------------------------------------------------------------------------- imports, for the key

def _norm(p):
    return os.path.normcase(os.path.normpath(os.path.abspath(p)))


def direct_imports(path):
    """Files under scripts/ that one source file imports: absolute, relative and from-imports,
    including those inside functions. Dynamic imports (importlib) are not seen."""
    with open(path, "rb") as f:
        tree = ast.parse(f.read(), path)
    here = os.path.dirname(os.path.abspath(path))
    found = set()

    def add(base, dotted):
        parts = [p for p in dotted.split(".") if p and p != "*"]
        for i in range(1, len(parts) + 1):  # the package __init__ files on the way count too
            stem = os.path.join(base, *parts[:i])
            for c in (stem + ".py", os.path.join(stem, "__init__.py")):
                if os.path.isfile(c):
                    found.add(_norm(c))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                for base in (env.SCRIPTS_DIR, here):
                    add(base, a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = here
                for _ in range(node.level - 1):
                    base = os.path.dirname(base)
                bases = [base]
                if os.path.isfile(os.path.join(base, "__init__.py")):
                    found.add(_norm(os.path.join(base, "__init__.py")))
            else:
                bases = [env.SCRIPTS_DIR, here]
            mod = node.module or ""
            for base in bases:
                if mod:
                    add(base, mod)
                for a in node.names:
                    add(base, f"{mod}.{a.name}" if mod else a.name)
    scripts = _norm(env.SCRIPTS_DIR) + os.sep
    me = _norm(path)
    return {f for f in found if f.startswith(scripts) and f != me}


def imports(path):
    """Every file under scripts/ reachable from `path` through its imports."""
    seen, todo = set(), [_norm(path)]
    while todo:
        for f in direct_imports(todo.pop()):
            if f not in seen:
                seen.add(f)
                todo.append(f)
    seen.discard(_norm(path))
    return seen


def rel(path):
    """A path relative to scripts/ with forward slashes: the same on both machines."""
    return os.path.relpath(path, env.SCRIPTS_DIR).replace(os.sep, "/")


# --------------------------------------------------------------------------- versions, manifest

def blender_version():
    try:
        import bpy
        return bpy.app.version_string
    except ImportError:
        return env.load().get("blender_version", "unknown")


def mpfb_version():
    """MPFB's version from its extension manifest (no need to enable it)."""
    p = os.path.join(env.user_resources(), "extensions", "user_default", "mpfb", "blender_manifest.toml")
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'\s*version\s*=\s*"([^"]+)"', line)
                if m:
                    return m.group(1)
    except OSError:
        pass
    return "absent"


_manifest = None


def manifest_entry(rel_path):
    """The manifest record behind a file under assets/ (an extracted file maps to its archive)."""
    global _manifest
    if _manifest is None:
        _manifest = {}
        for a in (read_json(MANIFEST) or {}).get("assets", []):
            for fi in a.get("files", []):
                _manifest[fi["path"]] = fi
                for x in fi.get("extracted") or []:
                    _manifest.setdefault(x, fi)
    return _manifest.get(rel_path.replace("\\", "/"))


def asset_hash(rel_path):
    fi = manifest_entry(rel_path)
    if fi is None:
        p = env.path("assets", rel_path)
        return f"unlisted:{os.path.getsize(p)}" if os.path.exists(p) else "missing"
    for algo in ("sha256", "sha512", "md5"):
        if fi.get(algo):
            return f"{algo}:{fi[algo]}"
    return f"bytes:{fi.get('bytes')}"


def _active():
    from . import cli
    return cli.active()


def asset(rel_path, ctx=None):
    """Absolute path of a file under assets/; the build reading it gets its manifest hash in its key."""
    rel_path = rel_path.replace("\\", "/")
    ctx = ctx or _active()
    if ctx is not None:
        ctx.reads["manifest"][rel_path] = asset_hash(rel_path)
    return env.path("assets", rel_path)


# --------------------------------------------------------------------------- keys

def part_path(part, ext=".blend"):
    """cache/parts/NN_name.blend for a Part; for a bare id, whichever NN_*.blend exists, else None."""
    if isinstance(part, str):
        hits = [h for h in sorted(glob.glob(os.path.join(PARTS_DIR, f"{part}_*{ext}"))) if ".tmp" not in h]
        return hits[0] if hits else None
    return os.path.join(PARTS_DIR, part.slug + ext)


def key_path(part):
    p = part_path(part)
    return p[:-len(".blend")] + ".key.json" if p else None


def read_key(part):
    p = key_path(part)
    return read_json(p) if p else None


def inputs(part, ctx, reads):
    """Everything a build depends on, each as a hash or a short value (§4.5, Cache key).

    `reads` holds the manifest files and interface keys the build read, with the hashes they had then."""
    script = env.path(part.script)
    return {
        "script": sha256_file(script, text=True),
        "modules": {rel(f): sha256_file(f, text=True) for f in sorted(imports(script))},
        "params": sha256_bytes(canonical(ctx.params).encode()),
        "seed": ctx.seed,
        "deps": dict(sorted(ctx.deps.items())),
        "manifest": dict(sorted(reads.get("manifest", {}).items())),
        "interfaces": dict(sorted(reads.get("interfaces", {}).items())),
        "blender": blender_version(),
        "mpfb": mpfb_version(),
    }


def key_of(inp):
    return sha256_bytes(canonical(inp).encode())


def key(part, ctx):
    """The cache key of the build `ctx` describes, with the reads it has made so far (§4.5)."""
    return key_of(inputs(part, ctx, ctx.reads))


def current_reads(stored_inputs):
    """The hashes now of the manifest files and interface keys a stored build read."""
    from . import interfaces
    data = interfaces.load() if stored_inputs.get("interfaces") else {}
    return {"manifest": {p: asset_hash(p) for p in stored_inputs.get("manifest", {})},
            "interfaces": {k: interfaces.value_hash(k, data) for k in stored_inputs.get("interfaces", {})}}


def diff_inputs(old, new):
    out = []
    for k in sorted(set(old) | set(new)):
        a, b = old.get(k), new.get(k)
        if a == b:
            continue
        if isinstance(a, dict) and isinstance(b, dict):
            out.append(f"{k}: " + ", ".join(sorted(n for n in set(a) | set(b) if a.get(n) != b.get(n))))
        else:
            out.append(k)
    return out


def fresh(part, ctx):
    """(True, []) if the cache was built from exactly the inputs present now, else (False, reasons)."""
    stored, blend = read_key(part), part_path(part)
    if not stored or not os.path.isfile(blend):
        return False, ["no cache"]
    if stored.get("partial"):
        return False, ["the last build ran only some stages (--stage)"]
    if stored.get("manual"):
        return False, ["saved from a live session, not by a build"]
    if os.path.getsize(blend) != stored.get("bytes"):
        return False, ["the .blend changed after its key was written"]
    old = stored.get("inputs", {})
    reasons = diff_inputs(old, inputs(part, ctx, current_reads(old)))
    return not reasons, reasons


# --------------------------------------------------------------------------- save and load

def mesh_hash(ob):
    """sha256 of an object's world-space vertices rounded to 0.01 mm and its faces (§4.7 rule 8);
    for other object types, of its type and world matrix."""
    import numpy as np
    m = np.array(ob.matrix_world, dtype=np.float64)
    h = hashlib.sha256(ob.type.encode())
    if ob.type != "MESH":
        h.update(np.round(m * 1e5).astype("<i8").tobytes())
        return h.hexdigest()
    me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3).astype(np.float64) @ m[:3, :3].T + m[:3, 3]
    start = np.empty(len(me.polygons), np.int32)
    total = np.empty(len(me.polygons), np.int32)
    verts = np.empty(len(me.loops), np.int32)
    me.polygons.foreach_get("loop_start", start)
    me.polygons.foreach_get("loop_total", total)
    me.loops.foreach_get("vertex_index", verts)
    for a in (np.round(co * 1e5).astype("<i8"), start.astype("<i4"), total.astype("<i4"), verts.astype("<i4")):
        h.update(a.tobytes())
    return h.hexdigest()


def save_part(part, ctx=None, manual=False):
    """Write the part's data-blocks to cache/parts/NN_name.blend and its key beside it.

    Skipped under --check, which saves nothing. The old key is deleted first and the new one written
    last, so a killed save leaves no key and the part reads as stale. `manual` (a save from a live
    server session) writes no key inputs, so the cache never counts as fresh."""
    import bpy
    from . import replace
    t0 = time.perf_counter()
    ctx = ctx if ctx is not None else _active()
    if ctx is not None and ctx.args.check:
        return None
    coll = replace.local("collections", part.collection)
    if coll is None:
        raise RuntimeError(f"part {part.id} has no collection {part.collection} to save")
    bpy.context.view_layer.update()  # matrix_world of new objects is stale until the depsgraph runs
    blend, kp = part_path(part), key_path(part)
    if os.path.exists(kp):
        os.remove(kp)
    with atomic(blend) as tmp:
        bpy.data.libraries.write(tmp, {coll} | set(replace.owned_ids(part)),
                                 path_remap="RELATIVE_ALL", compress=False)
    manual = manual or ctx is None
    inp = {} if manual else inputs(part, ctx, ctx.reads)
    rec = {"part": part.id, "slug": part.slug, "collection": part.collection,
           "key": None if manual else key_of(inp), "partial": bool(ctx and ctx.partial), "manual": manual,
           "inputs": inp, "blend": os.path.basename(blend), "bytes": os.path.getsize(blend),
           "objects": {o.name: mesh_hash(o) for o in sorted(coll.all_objects, key=lambda o: o.name)},
           "written": log.now(), "seconds": round(time.perf_counter() - t0, 4)}
    write_json(kp, rec)
    if ctx is not None:
        ctx.saved(rec, [blend, kp])
    return rec


def load_part(part, link=False):
    """Make the cached part this session's copy of it; returns its collection.

    Append (the default) empties the part's local collection and moves the cached objects into it, so
    the collection keeps its place in the scene; data the cache carried from other parts (the rig an
    Armature modifier points at) is mapped back onto the session's own copy. Link brings the cached
    collection in read-only under `Parts`, for neighbours a part only reads; `part` may then be an id."""
    import bpy
    from . import replace
    pid = part if isinstance(part, str) else part.id
    path = part_path(part)
    if not path or not os.path.isfile(path):
        from . import cli
        raise cli.MissingDependency(f"no cache for part {pid} in {os.path.relpath(PARTS_DIR, env.PROJECT_DIR)}")
    with bpy.data.libraries.load(path) as (src, _):
        names = [n for n in src.collections if re.match(rf"^Part{pid}\.[A-Za-z0-9]+$", n)]
    if len(names) != 1:
        raise RuntimeError(f"{path} should hold one Part{pid}.* collection, has {names}")
    name = names[0]
    if link:
        lib = next((lb for lb in bpy.data.libraries if _norm(bpy.path.abspath(lb.filepath)) == _norm(path)), None)
        if lib is not None:
            lib.reload()
        coll = next((c for c in bpy.data.collections if c.name == name and c.library is not None
                     and _norm(bpy.path.abspath(c.library.filepath)) == _norm(path)), None)
        if coll is None:
            with bpy.data.libraries.load(path, link=True, relative=True) as (_, dst):
                dst.collections = [name]
            coll = dst.collections[0]
        parent = replace.parts_collection()
        if not any(c == coll for c in parent.children):
            parent.children.link(coll)
        return coll
    if isinstance(part, str):
        raise TypeError("appending a part needs its Part record (for its prefixes), not an id")
    coll = replace.ensure_collection(part)
    replace.remove(part)
    before = replace.local_ids()
    with bpy.data.libraries.load(path) as (_, dst):
        dst.collections = [name]
    shell = dst.collections[0]
    for ob in list(shell.objects):
        coll.objects.link(ob)
    for ch in list(shell.children):
        coll.children.link(ch)
    bpy.data.collections.remove(shell)
    remapped, kept = replace.relink_foreign(part, before)
    ctx = _active()
    if kept and ctx is not None:
        ctx.warn(f"part {pid}'s cache brought data outside its prefixes: {kept}")
    return coll


# --------------------------------------------------------------------------- the build journal

class Journal:
    """build_all.py's journal (§4.7 rule 4): a stage is `running` before it starts and `done` with its
    key and outputs after; one found `running` was interrupted and runs again from its input cache."""

    def __init__(self, path=None):
        self.path = path or JOURNAL

    def stages(self):
        return (read_json(self.path) or {}).get("stages", {})

    def state(self, stage):
        return self.stages().get(stage, {})

    def done(self, stage, key=None):
        s = self.state(stage)
        return s.get("state") == "done" and (key is None or s.get("key") == key)

    def mark(self, stage, state, **info):
        with locked(self.path):
            data = read_json(self.path) or {}
            data.setdefault("stages", {})[stage] = dict(state=state, ts=log.now(), **info)
            write_json(self.path, data)

    @contextlib.contextmanager
    def stage(self, stage, key=None):
        """`with journal.stage("S3", key) as rec: ... rec["outputs"].append(path)`."""
        self.mark(stage, "running", key=key)
        rec = {"outputs": []}
        try:
            yield rec
        except BaseException as e:
            self.mark(stage, "failed", key=key, error=repr(e)[:500])
            raise
        self.mark(stage, "done", key=key, outputs=rec["outputs"])


# --------------------------------------------------------------------------- self-test

def selftest():
    import shutil
    import threading
    import bpy
    from . import cli, interfaces, replace
    global PARTS_DIR
    scratch = env.path("cache", "selftest", "cache")
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    old_dir, PARTS_DIR = PARTS_DIR, os.path.join(scratch, "parts")
    old_interfaces = interfaces.PATH
    out = {}
    try:
        # atomic writes: a failed writer leaves the old file and no temporary
        p = os.path.join(scratch, "a.json")
        write_json(p, {"a": 1})
        try:
            with atomic(p) as tmp:
                with open(tmp, "w") as f:
                    f.write("half")
                raise KeyError("killed")
        except KeyError:
            pass
        assert read_json(p) == {"a": 1} and os.listdir(scratch) == ["a.json"], os.listdir(scratch)

        # the lock serialises read-modify-write from several writers
        c = os.path.join(scratch, "count.json")
        write_json(c, {"n": 0})

        def bump():
            for _ in range(15):
                with locked(c):
                    write_json(c, {"n": read_json(c)["n"] + 1})
        threads = [threading.Thread(target=bump) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert read_json(c) == {"n": 45}, read_json(c)

        # the import closure the key hashes
        mods = {rel(f) for f in imports(env.path("scripts", "lib", "cli.py"))}
        assert {"lib/__init__.py", "lib/env.py", "lib/log.py", "lib/cache.py", "lib/naming.py"} <= mods, mods
        assert "lib/cli.py" not in mods
        out["cli_imports"] = sorted(mods)

        # journal
        j = Journal(os.path.join(scratch, "build_state.json"))
        with j.stage("S1", key="k1") as r:
            r["outputs"].append("cache/body/base.blend")
        try:
            with j.stage("S2", key="k2"):
                raise ValueError("boom")
        except ValueError:
            pass
        j.mark("S3", "running", key="k3")  # a killed process
        assert j.done("S1", "k1") and not j.done("S1", "other") and not j.done("S2") and not j.done("S3")
        assert j.state("S2")["state"] == "failed" and j.state("S1")["outputs"] == ["cache/body/base.blend"]

        # manifest entries: an extracted texture maps to its archive's hash
        if os.path.exists(MANIFEST):
            some = next((x for a in read_json(MANIFEST)["assets"] for fi in a.get("files", [])
                         for x in (fi.get("extracted") or [])), None)
            if some:
                assert asset_hash(some).split(":")[0] in ("sha256", "md5", "sha512"), asset_hash(some)
        assert asset_hash("no/such/file.png") == "missing"

        # save, fresh, load: a scratch part with its own script file
        src = os.path.join(scratch, "96_cache_selftest.py")
        with open(src, "w", newline="\n") as f:
            f.write("from lib import naming\nVALUE = 1\n")
        part = cli.Part(id="96", name="cache_selftest", prefixes=("SelftestC.",),
                        script=os.path.relpath(src, env.PROJECT_DIR))
        rig_data = bpy.data.armatures.new("SelftestX.Rig")
        rig = bpy.data.objects.new("SelftestX.Rig", rig_data)  # another part's object the cache points at
        bpy.context.scene.collection.objects.link(rig)
        ctx = cli.Context(part, cli.parse([]))
        interfaces.PATH = os.path.join(scratch, "interfaces.json")
        rifle = cli.Part(id="15", name="carbine", prefixes=("Rifle.",))
        interfaces.write(rifle, {"rifle.oal": 855.8})
        ctx.reads["interfaces"]["rifle.oal"] = interfaces.value_hash("rifle.oal")  # as interfaces.read records it
        with replace.part_scope(part) as scope:
            me = bpy.data.meshes.new("SelftestC.Tri")
            me.from_pydata([(0.1, 0, 0), (1, 0, 0), (0, 1, 0.25)], [], [(0, 1, 2)])
            ob = scope.new_object("SelftestC.Tri", me)
            ob.location = (0, 0, 0.5)
            ob.modifiers.new("Rig", "ARMATURE").object = rig
        rec = save_part(part, ctx)
        assert os.path.isfile(part_path(part)) and rec["key"] and rec["objects"]["SelftestC.Tri"]
        assert fresh(part, ctx) == (True, []), fresh(part, ctx)
        ctx.params = {"lug_depth_mm": 4.0}
        ok, why = fresh(part, ctx)
        assert not ok and why == ["params"], why
        ctx.params = {}
        interfaces.write(rifle, {"rifle.oal": 856.0})  # a neighbour publishes a new value: this reader is stale
        ok, why = fresh(part, ctx)
        assert not ok and why == ["interfaces: rifle.oal"], why
        interfaces.write(rifle, {"rifle.oal": 855.8})
        assert fresh(part, ctx)[0]
        with open(src, "a", newline="\n") as f:
            f.write("VALUE = 2\n")
        ok, why = fresh(part, ctx)
        assert not ok and why == ["script"], why
        h0 = rec["objects"]["SelftestC.Tri"]
        ob.data.vertices[0].co.x += 0.000001  # 1 µm: inside the 0.01 mm rounding
        bpy.context.view_layer.update()
        assert mesh_hash(ob) == h0
        load_part(part)
        ob = bpy.data.objects["SelftestC.Tri"]
        bpy.context.view_layer.update()
        assert mesh_hash(ob) == h0 and ob.modifiers["Rig"].object == rig, "load did not restore the part"
        assert "SelftestX.Rig.001" not in bpy.data.objects, "the cache's copy of the rig was not remapped"
        ob.data.vertices[0].co.x += 0.00002  # 0.02 mm: a real change
        bpy.context.view_layer.update()
        assert mesh_hash(ob) != h0
        linked = load_part("96", link=True)
        assert linked.library is not None and any(c == linked for c in replace.parts_collection().children)
        out.update(key=rec["key"][:12], blend_bytes=rec["bytes"], save_s=rec["seconds"])
        return out
    finally:
        PARTS_DIR, interfaces.PATH = old_dir, old_interfaces
        replace.remove(cli.Part(id="96", name="cache_selftest", prefixes=("SelftestC.",)))
        doomed = [c for c in bpy.data.collections if c.name.startswith("Part96.") and c.library is None]
        doomed += [o for o in bpy.data.objects if o.name.startswith("SelftestX.") and o.library is None]
        bpy.data.batch_remove(doomed)
        for lb in [lb for lb in bpy.data.libraries if "selftest" in lb.filepath]:
            bpy.data.libraries.remove(lb)
        replace.purge()
        shutil.rmtree(scratch, ignore_errors=True)
