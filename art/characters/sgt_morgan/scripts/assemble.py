"""The round's integration and evaluation (PLAN.md, take 2: "work, evaluate, integrate").

Usage (from the project folder, after `source cache/env.sh`):

  "$SGT_PYIMG" -I scripts/assemble.py --status
      the build order and what is fresh, stale (and why) or missing; builds nothing
  "$SGT_PYIMG" -I scripts/assemble.py --round 1 [--packet] [--no-cycles] [--samples 64]
      assemble from the caches as they are and evaluate into renders/round_01/
  "$SGT_PYIMG" -I scripts/assemble.py --round 2 --rebuild [--packet]
      first rebuild what is stale, each stage or part in its own Blender process, then evaluate
  "$SGT_PYIMG" -I scripts/assemble.py --rebuild shirt carrier       (or --rebuild all)
      rebuild the named items (and whatever depends on something rebuilt in this run)
  "$SGT_PYIMG" -I scripts/assemble.py --round 1 --sheets-only [--packet]
      recompose the sheets, the clash summary and the packet from the renders already made

Build order: base (scripts/stages/base.py -> cache/stages/base.blend), pose (scripts/stages/pose.py ->
cache/stages/pose.blend; with --solve when hero_pose.json is older than base.json or pose_solve.py), then the
parts: trousers, shirt, boots, gloves, carrier, armour, belt, carbine, head (if scripts/parts/head.py exists),
each scripts/parts/<part>.py -> cache/parts/<part>.blend (run with --no-render). An item is stale when its
script, a module it imports from scripts/ (found by reading the imports, transitively), a data file it reads,
or an item it fits to (DEPS below) is newer than its cache. Timestamps only; cache/assemble_record.json keeps
what was built when, how long it took and its log (cache/assemble_logs/<item>.log).

Assembly (one Blender process, scripts/assemble.py -- --blender): base.blend's rigged body; every part cache
appended (common.load_part points its Armature modifiers at Morgan.Rig); the hero pose (stages/pose.py
apply_hero_pose via common.apply_hero_pose); the carbine from cache/parts/carbine.blend with Carbine.Root
bone-parented to the posed wrist.R at hero_pose.json's carbine_frame (matrix_in_parent_bone, relative to the
posed pose_bone.matrix); the hero camera, the floor, the lights at 0.3 of spec 17's energy (as round 0) and the
world from scripts/eval/. Saved as cache/assembled.blend.

Evaluation, renders/round_NN/:
  <label>_clay.png, <label>_cycles.png, <label>_parts.png   every ref.* preset of scripts/eval/presets/ref.json
      (full = the 1672 x 941 hero frame, soldier_full, head_face, torso_vest, arm_R, arm_L, hands_rifle,
      belt_hips, legs_knees, boots_feet): Workbench clay, quick Cycles (64 spp, OIDN, AgX, then the display
      grade of scripts/eval/grade.py over the flat backdrop: the image the critics and the sheets see, round 8;
      the 16-bit ungraded render beside it as <label>_cycles_ungraded.png) and Workbench with one flat colour
      per part (which layer is where)
  <label>_compare.png       reference crop | clay | parts | Cycles
  <label>_overlay.png       reference and Cycles at 50 % | the reference alone; both with the render's
                            silhouette edge in cyan
  turn_<view>.png, turnaround.png   the posed soldier from the front, three-quarters, both sides and the back
                            (Workbench, one flat colour per part as in <label>_parts.png)
  standoff.json, standoff.md  hard gear standing off what it should sit on (round 6: a pouch hinged into the
                            air, a clip floating off its strap; see standoff_report)
  clashes.json, clashes.md  interpenetration in the hero pose between parts (body, clothing, gear, carbine;
                            a part's own objects are never tested against each other: their overlaps are designed)
  assembly.json             what was loaded and bound, pose and carbine checks, cache freshness, timings
  critic/                   with --packet: a blind critic packet of the whole soldier (scripts/eval/critic/
                            packet.py; the hero crops beside the reference crops); critics are not run here

Interpenetration test: every mesh is evaluated in the hero pose without Solidify and Subdivision (a garment's
outer surface). A vertex of part A counts as inside an object of part B when it is more than 0.5 mm inside:
  - B closed (no boundary edges): ray parity along two directions (orientation-free); depth = distance to B;
  - B open (a garment shell or the body): all of B's part's open meshes are merged into one surface (a shell
    with its pockets, pads and plates) and the vertex counts when the nearest point of that surface, within
    25 mm (50 for the body), lies on its inner side with the offset within 45 degrees of the face normal (so
    a hem's or a cuff's boundary never decides); depth = distance to the part's nearest surface.
Tested: every part's vertices against the body; the body's against closed objects; across parts, A against B
when B is closed, or when B is open and A is the outer layer (layer order ORDER below: body, boots, shirt and
head, trousers, gloves, belt, carrier, armour, carbine). An inner layer under an open outer one is expected.

Left/right are the soldier's own (CLAUDE.md).
"""
import argparse
import ast
import datetime
import json
import os
import shutil
import subprocess
import sys
import time

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(SCRIPTS)
for _p in (SCRIPTS, os.path.join(SCRIPTS, "parts"), os.path.join(SCRIPTS, "stages")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CACHE = os.path.join(PROJECT, "cache")
RECORD = os.path.join(CACHE, "assemble_record.json")
LOGS = os.path.join(CACHE, "assemble_logs")
ASSEMBLED = os.path.join(CACHE, "assembled.blend")
BASE_BLEND = os.path.join(CACHE, "stages", "base.blend")
BASE_JSON = os.path.join(CACHE, "stages", "base.json")
HERO_JSON = os.path.join(SCRIPTS, "stages", "hero_pose.json")
REF_PRESETS = os.path.join(SCRIPTS, "eval", "presets", "ref.json")
SEARCH = (SCRIPTS, os.path.join(SCRIPTS, "parts"), os.path.join(SCRIPTS, "stages"))

PARTS = ("boots", "trousers", "shirt", "gloves", "carrier", "armour", "belt", "carbine", "head")
# what each part fits to besides the base body (the caches its script reads while building)
DEPS = {"trousers": ["base", "boots"],  # round 10: the hems fall round the real boots
        "shirt": ["base"], "boots": ["base"], "gloves": ["base"],
        "carrier": ["base", "shirt", "trousers"], "armour": ["base", "shirt", "gloves", "trousers", "carrier"],
        "belt": ["base", "trousers"], "carbine": [], "head": ["base"]}
LAYER = {"body": "body", "trousers": "clothing", "shirt": "clothing", "boots": "clothing", "gloves": "clothing",
         "head": "clothing", "carrier": "gear", "armour": "gear", "belt": "gear", "carbine": "carbine"}
ORDER = {"body": 0.0, "boots": 1.0, "shirt": 1.1, "head": 1.1, "trousers": 1.2, "gloves": 1.3,
         "belt": 2.0, "carrier": 2.1, "armour": 2.2, "carbine": 3.0}
PART_CLAY = {"body": (0.78, 0.72, 0.66), "trousers": (0.47, 0.52, 0.36), "shirt": (0.44, 0.52, 0.66),
             "boots": (0.42, 0.30, 0.22), "gloves": (0.58, 0.42, 0.64), "carrier": (0.84, 0.62, 0.30),
             "armour": (0.30, 0.68, 0.68), "belt": (0.80, 0.34, 0.30), "carbine": (0.22, 0.22, 0.24),
             "head": (0.30, 0.22, 0.16)}
LIGHT_SCALE = 0.3          # round 0's choice: take 1 found spec 17's energies 3-5x too bright
THRESH_MM, CAP_MM, CAP_OPEN_MM, COS_IN = 0.5, 50.0, 25.0, -0.707
SPOT_MM = 120.0          # clash places are reported per cell of this size
TURN = {  # view -> unit direction from the soldier to the camera (he faces -Y, +X is his left)
    "front": (0.0, -1.0, 0.0), "threeq_R": (-0.707, -0.707, 0.0), "side_R": (-1.0, 0.0, 0.0),
    "back": (0.0, 1.0, 0.0), "side_L": (1.0, 0.0, 0.0), "threeq_L": (0.707, -0.707, 0.0)}


def rel(p):
    return os.path.relpath(p, PROJECT).replace(os.sep, "/")


def round_dir(n):
    return os.path.join(PROJECT, "renders", f"round_{n:02d}")


def stamp(t):
    return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")


# =========================================================================== freshness and rebuilds (no bpy)

def FOOT_INPUTS():
    """Round 3: base.py loads scripts/stages/foot.py by path (importlib; its package scripts/stages/foot/ has the
    same name), so the import scan cannot see it: the stage, what it imports and its data are base's inputs."""
    f = os.path.join(SCRIPTS, "stages", "foot.py")
    d = os.path.join(SCRIPTS, "stages", "foot")
    # its --render helpers (parts/common.py, which imports stages/pose.py) are not inputs of base.blend
    mods = [m for m in imported_modules(f) if os.path.normcase(os.path.join(SCRIPTS, "parts")) not in os.path.normcase(m)
            and os.path.basename(m) != "pose.py"]
    return [f] + mods + [os.path.join(d, n) for n in ("params.json", "scan_targets.json", "marks.py")]


def pose_needs_solve():
    """Round 3: re-solve the pose only when what the solve reads from base.json changed (pose.base_signature: the
    bones to 0.01 mm and the landmarks but the feet's), against scripts/stages/hero_pose_basis.json written at the
    last solve, or when pose_solve.py is newer than hero_pose.json; without a basis file, round 0-2's rule (base.json
    newer than hero_pose.json). A full solve is 25 min and not reproducible (README "Round 2"), and the foot stage
    rewrites base.json without moving a bone. Returns (bool, why)."""
    ht = os.path.getmtime(HERO_JSON) if os.path.exists(HERO_JSON) else 0
    solver = os.path.join(SCRIPTS, "stages", "pose_solve.py")
    if os.path.exists(solver) and os.path.getmtime(solver) > ht:
        return True, "pose_solve.py is newer than hero_pose.json"
    basis = os.path.join(SCRIPTS, "stages", "hero_pose_basis.json")
    if os.path.exists(basis) and os.path.exists(BASE_JSON):
        sp = os.path.join(SCRIPTS, "stages")
        if sp not in sys.path:
            sys.path.insert(0, sp)
        import pose as P
        with open(basis, encoding="utf-8") as f:
            was = json.load(f).get("base_signature")
        now = P.base_signature(BASE_JSON)
        return (now != was, "base.json's bones or solved landmarks changed" if now != was
                else "base.json's bones and solved landmarks unchanged (basis signature): hero_pose.json re-applied")
    if os.path.exists(BASE_JSON) and os.path.getmtime(BASE_JSON) > ht:
        return True, "base.json is newer than hero_pose.json (no basis file)"
    return False, "hero_pose.json is newer than base.json"


def items():
    """The build order: name, script, cache, data files read, deps, Blender argv builder."""
    out = [
        {"name": "base", "script": os.path.join(SCRIPTS, "stages", "base.py"), "out": BASE_BLEND,
         "data": [os.path.join(SCRIPTS, "parts", "head_fit.json")] + FOOT_INPUTS(), "deps": []},
        {"name": "pose", "script": os.path.join(SCRIPTS, "stages", "pose.py"),
         "out": os.path.join(CACHE, "stages", "pose.blend"), "data": [HERO_JSON], "deps": ["base"]},
    ]
    for p in PARTS:
        s = os.path.join(SCRIPTS, "parts", f"{p}.py")
        if p == "head" and os.path.exists(os.path.join(SCRIPTS, "parts", "head_build.py")):
            # head round 10: the part's build is head_build.py; head.py is in base.py's import closure (through
            # head_skin.py), so building from it would call the base stale at every edit of the head
            s = os.path.join(SCRIPTS, "parts", "head_build.py")
        if p == "head" and not os.path.exists(s):
            continue
        out.append({"name": p, "script": s, "out": os.path.join(CACHE, "parts", f"{p}.blend"), "data": [],
                    "deps": DEPS[p]})
    return out


def _module_file(name, here):
    bits = name.split(".")
    for d in (here,) + SEARCH:
        p = os.path.join(d, *bits)
        if os.path.isfile(p + ".py"):
            return p + ".py"
        if os.path.isfile(os.path.join(p, "__init__.py")):
            return os.path.join(p, "__init__.py")
    return None


def imported_modules(script):
    """Every module under scripts/ the script imports, transitively (imports inside functions included)."""
    seen, todo = set(), [script]
    while todo:
        f = todo.pop()
        try:
            with open(f, "rb") as fh:          # some take 1 modules are not UTF-8
                tree = ast.parse(fh.read().decode("utf-8", errors="replace"))
        except (OSError, SyntaxError):
            continue
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names += [node.module] + [f"{node.module}.{a.name}" for a in node.names]
        for n in names:
            m = _module_file(n, os.path.dirname(f))
            if m and os.path.normcase(m) != os.path.normcase(script) and m not in seen \
                    and os.path.normcase(m).startswith(os.path.normcase(SCRIPTS)):
                seen.add(m)
                todo.append(m)
    return sorted(seen)


def inputs_of(it, by_name):
    files = [it["script"]] + imported_modules(it["script"]) + it["data"]
    files += [by_name[d]["out"] for d in it["deps"] if d in by_name]
    return files


def freshness(it, by_name):
    """(state, reason, newest input): state fresh | stale | missing."""
    ins = [f for f in inputs_of(it, by_name) if os.path.exists(f)]
    newest = max(ins, key=os.path.getmtime) if ins else None
    if not os.path.exists(it["out"]):
        return "missing", "no cache", newest
    t = os.path.getmtime(it["out"])
    newer = [f for f in ins if os.path.getmtime(f) > t]
    if newer:
        f = max(newer, key=os.path.getmtime)
        more = f" (+{len(newer) - 1} more)" if len(newer) > 1 else ""
        return "stale", f"{rel(f)} {stamp(os.path.getmtime(f))} is newer than the cache {stamp(t)}{more}", f
    return "fresh", f"cache {stamp(t)}", newest


def status(quiet=False):
    its = items()
    by = {i["name"]: i for i in its}
    rows = []
    for it in its:
        st, why, _ = freshness(it, by)
        rows.append({"item": it["name"], "cache": rel(it["out"]), "state": st, "why": why,
                     "cache_time": stamp(os.path.getmtime(it["out"])) if os.path.exists(it["out"]) else None})
        if not quiet:
            print(f"[assemble] {it['name']:9s} {st:8s} {why}", flush=True)
    return rows


def load_record():
    try:
        with open(RECORD, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def blender_argv(it):
    from lib import env
    if it["name"] == "pose":
        args = ["-b", BASE_BLEND, "--python", it["script"]]
        solve, why = pose_needs_solve()
        print(f"[assemble] pose: {'re-solve' if solve else 'no re-solve'}: {why}", flush=True)
        if solve:
            args += ["--", "--solve"]
    elif it["name"] == "base":
        args = ["-b", "--python", it["script"]]
    else:
        args = ["-b", "--python", it["script"], "--", "--no-render"]
    return env.blender_cmd(args)


def rebuild(names):
    """names: [] = what is stale; ["all"]; or item names. Each item in its own Blender process, in build
    order; an item is also rebuilt when something it depends on was rebuilt in this run."""
    its = items()
    by = {i["name"]: i for i in its}
    unknown = [n for n in names if n != "all" and n not in by]
    if unknown:
        raise SystemExit(f"--rebuild: unknown item(s) {unknown}; known: {list(by)} or all")
    rec = load_record()
    os.makedirs(LOGS, exist_ok=True)
    done, report = set(), []
    for it in its:
        st, why, _ = freshness(it, by)
        want = ("all" in names or it["name"] in names or (not names and st != "fresh")
                or any(d in done for d in it["deps"]) or (it["name"] == "pose" and "base" in done))
        if not want:
            continue
        cmd, environ = blender_argv(it)
        log = os.path.join(LOGS, f"{it['name']}.log")
        print(f"[assemble] rebuild {it['name']} ({st}: {why})", flush=True)
        t = time.perf_counter()
        with open(log, "w", encoding="utf-8", errors="replace") as fh:
            r = subprocess.run(cmd, env=environ, cwd=PROJECT, stdout=fh, stderr=subprocess.STDOUT)
        sec = round(time.perf_counter() - t, 1)
        ok = r.returncode == 0 and os.path.exists(it["out"]) and freshness(it, by)[0] == "fresh"
        rec[it["name"]] = {"built": datetime.datetime.now().isoformat(timespec="seconds"), "seconds": sec,
                           "rc": r.returncode, "ok": ok, "argv": cmd[1:], "log": rel(log), "was": f"{st}: {why}"}
        with open(RECORD, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1)
        report.append((it["name"], sec, ok))
        print(f"[assemble]   {it['name']} {'ok' if ok else 'FAILED'} in {sec} s (log {rel(log)})", flush=True)
        if not ok:
            raise SystemExit(f"[assemble] {it['name']} failed (exit {r.returncode}); see {rel(log)}. Stopped: "
                             "the items after it would be built on a broken input.")
        done.add(it["name"])
    if not report:
        print("[assemble] nothing to rebuild", flush=True)
    return report


# =========================================================================== inside Blender

def place_carbine(rig, hero):
    """Append Part.Carbine and bone-parent Carbine.Root to the posed hand bone at carbine_frame. Returns
    (collection, check dict) or (None, None)."""
    import bpy
    import numpy as np
    from mathutils import Matrix
    path = os.path.join(CACHE, "parts", "carbine.blend")
    if not os.path.exists(path):
        return None, None
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == "Part.Carbine"]
    coll = dst.collections[0]
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    cf = hero["carbine_frame"]
    pb = rig.pose.bones[cf["parent_bone"]]
    M = rig.matrix_world @ pb.matrix @ Matrix(cf["matrix_in_parent_bone"])
    root = bpy.data.objects["Carbine.Root"]
    root.parent = rig
    root.parent_type = "BONE"
    root.parent_bone = cf["parent_bone"]
    bpy.context.view_layer.update()
    root.matrix_world = M
    bpy.context.view_layer.update()
    A, B = np.array(root.matrix_world), np.array(cf["matrix_world"])
    dt = float(np.linalg.norm(A[:3, 3] - B[:3, 3]) * 1000.0)
    Rr = A[:3, :3] @ B[:3, :3].T
    ang = float(np.degrees(np.arccos(np.clip((np.trace(Rr) - 1) / 2, -1, 1))))
    return coll, {"parent": f"{rig.name}:{cf['parent_bone']} (bone parent)", "objects": len(coll.all_objects),
                  "vs_stored_matrix_world": {"offset_mm": round(dt, 2), "angle_deg": round(ang, 3)},
                  "note": "matrix_world stored in hero_pose.json at solve time vs the frame rebuilt from the posed "
                          "wrist.R now; a difference means the rig changed since the solve"}


def bound_report(coll, rig):
    objs = [o for o in coll.all_objects if o.type == "MESH"]
    bad = []
    for o in objs:
        arm = any(m.type == "ARMATURE" and m.object == rig for m in o.modifiers)
        par, p = False, o.parent
        while p is not None:
            par = par or p == rig
            p = p.parent
        if not (arm or par):
            bad.append(o.name)
    return {"objects": len(objs), "bound": len(objs) - len(bad), "unbound": bad}


def pose_check(rig, hero):
    import numpy as np
    errs = {}
    for n, p in hero["joints_world_mm"].items():
        if n in rig.pose.bones:
            h = np.array(rig.matrix_world @ rig.pose.bones[n].head) * 1000.0
            errs[n] = float(np.linalg.norm(h - np.array(p)))
    w = max(errs, key=errs.get)
    return {"max_mm": round(errs[w], 2), "worst_bone": w, "mean_mm": round(float(np.mean(list(errs.values()))), 3),
            "note": "posed bone heads now vs the solver's joints_world_mm; nonzero means base.blend's rig changed "
                    "since hero_pose.json was solved"}


def mesh_data(ob):
    """Posed world mm, without Solidify/Subdivision: V, F, BVH, closed, bbox."""
    import numpy as np
    import common as C
    V, F = C.evaluated_world_mm(ob)
    if not len(V) or not F:
        return None
    E = {}
    for f in F:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            k = (a, b) if a < b else (b, a)
            E[k] = E.get(k, 0) + 1
    boundary = sum(1 for c in E.values() if c == 1)
    return {"name": ob.name, "V": V, "F": F, "bvh": C.bvh_from(V, F), "closed": boundary == 0,
            "boundary_edges": boundary, "lo": V.min(0), "hi": V.max(0)}


def _parity_inside(bvh, p):
    from mathutils import Vector
    for d in (Vector((0.2718, 0.5772, 0.7701)).normalized(), Vector((-0.6931, -0.1414, 0.7071)).normalized()):
        o, n = Vector(p), 0
        for _ in range(96):
            h = bvh.ray_cast(o, d)
            if h[0] is None:
                break
            n += 1
            o = h[0] + d * 0.01
        if n % 2 == 0:
            return False
    return True


def merged_open(datas, part):
    """One surface of all of a part's open meshes (a garment's shell with its pockets, pads and plates), so
    an open-shell depth is the distance to the part's nearest surface, never to a far accessory sheet."""
    import numpy as np
    import common as C
    op = [d for d in datas if not d["closed"]]
    if not op:
        return None
    Vs, Fs, owner, n = [], [], [], 0
    for d in op:
        Vs.append(d["V"])
        Fs += [tuple(i + n for i in f) for f in d["F"]]
        owner += [d["name"]] * len(d["F"])
        n += len(d["V"])
    V = np.concatenate(Vs)
    return {"name": part, "bvh": C.bvh_from(V, Fs), "owner": owner, "closed": False, "lo": V.min(0), "hi": V.max(0),
            "cap": CAP_MM if part == "body" else CAP_OPEN_MM}


def penetration(X, Y):
    """Vertices of mesh X more than THRESH_MM inside Y (a closed mesh, or a part's merged open surface).
    Returns {Y object name: [count, max depth, where]}."""
    import numpy as np
    from mathutils import Vector
    grow = THRESH_MM if Y["closed"] else Y["cap"]
    lo, hi = Y["lo"] - grow, Y["hi"] + grow
    cand = np.nonzero(np.all((X["V"] > lo) & (X["V"] < hi), axis=1))[0]
    res = {}
    for i in cand:
        p = X["V"][i]
        if Y["closed"]:
            loc, nrm, k, dist = Y["bvh"].find_nearest(Vector(p))
            if loc is None or dist <= THRESH_MM or not _parity_inside(Y["bvh"], p):
                continue
            yname = Y["name"]
        else:
            loc, nrm, k, dist = Y["bvh"].find_nearest(Vector(p), Y["cap"])
            if loc is None or dist <= THRESH_MM:
                continue
            if (Vector(p) - loc).dot(nrm) / dist > COS_IN:
                continue
            yname = Y["owner"][k]
        r = res.setdefault(yname, [0, 0.0, None, {}])
        r[0] += 1
        if dist > r[1]:
            r[1], r[2] = dist, [round(float(v)) for v in p]
        b = r[3].setdefault(tuple((p // SPOT_MM).astype(int)), [0, 0.0, None])
        b[0] += 1
        if dist > b[1]:
            b[1], b[2] = dist, [round(float(v)) for v in p]
    for r in res.values():   # the separate places: the deepest point of each SPOT_MM cell, deepest first
        r[3] = [{"at_mm": b[2], "count": b[0], "max_mm": round(b[1], 1)}
                for b in sorted(r[3].values(), key=lambda b: -b[1])][:5]
    return res


def clash_report(groups):
    """groups: {part: [objects]} including "body". Returns the clashes dict."""
    t0 = time.perf_counter()
    data = {}
    for part, objs in groups.items():
        data[part] = [d for d in (mesh_data(o) for o in objs if o.type == "MESH") if d is not None]
    surf = {p: [d for d in ds if d["closed"]] + [m for m in [merged_open(ds, p)] if m] for p, ds in data.items()}
    tests = {}
    names = list(data)
    for a in names:
        for b in names:
            if a == b:
                continue
            for X in data[a]:
                for Y in surf[b]:
                    if b == "body":
                        pass
                    elif a == "body":
                        if not Y["closed"]:
                            continue
                    elif not Y["closed"] and ORDER[a] <= ORDER[b]:
                        continue
                    for yname, r in penetration(X, Y).items():
                        key = f"{a} in {b}"
                        t = tests.setdefault(key, {"a": a, "b": b, "count": 0, "max_mm": 0.0, "pairs": []})
                        t["count"] += r[0]
                        t["max_mm"] = max(t["max_mm"], r[1])
                        t["pairs"].append({"x": X["name"], "y": yname, "count": r[0], "max_mm": round(r[1], 2),
                                           "at_mm": r[2], "y_closed": Y["closed"], "spots": r[3]})
    pairs = {}
    for key, t in tests.items():
        t["max_mm"] = round(t["max_mm"], 2)
        t["pairs"].sort(key=lambda q: (-q["max_mm"], -q["count"]))
        a, b = t["a"], t["b"]
        lo, hi = (a, b) if ORDER[a] <= ORDER[b] else (b, a)
        cat = f"{LAYER[lo]}-{LAYER[hi]}"
        pk = f"{lo}-{hi}"
        P = pairs.setdefault(pk, {"category": cat, "count": 0, "max_mm": 0.0, "directions": {}})
        P["count"] += t["count"]
        P["max_mm"] = max(P["max_mm"], t["max_mm"])
        P["directions"][key] = t
    objs = {p: [{"name": d["name"], "verts": int(len(d["V"])), "closed": d["closed"],
                 "boundary_edges": d["boundary_edges"]} for d in data[p]] for p in data}
    return {"threshold_mm": THRESH_MM, "open_cap_mm": CAP_OPEN_MM, "body_cap_mm": CAP_MM, "order": ORDER, "objects": objs,
            "pairs": dict(sorted(pairs.items(), key=lambda kv: -kv[1]["max_mm"])),
            "seconds": round(time.perf_counter() - t0, 1)}


STANDOFF_PARTS = ("boots", "gloves", "belt", "carrier", "armour")   # hard gear and hardware; garments are not tested
STANDOFF_MM, STANDOFF_TOUCH, STANDOFF_CAP, STANDOFF_COS = 5.0, 2.5, 60.0, 0.5
STANDOFF_SAMPLES = 700
STANDOFF_HOLD = 0.2          # a stand-off needs under this share of its attachment face touching (a knee cap moved 8 mm
                             # out still touched its base over 17 % of it with its sloping sides)
# objects whose gap to what lies under them is designed (object name, or a prefix ending in "." -> why); listed apart
STANDOFF_DESIGNED = {
    "Boot.L.Upper": "the last's allowances (toe room 15 mm ahead of the toes, 9.5 mm of ankle padding)",
    "Boot.R.Upper": "as Boot.L.Upper",
    "Boot.L.Sole": "the sole's top stands 4 mm under the footbed", "Boot.R.Sole": "as Boot.L.Sole",
    "Boot.L.Lugs": "moulded into the outsole; rays from their side walls look up past the sole's edge",
    "Boot.R.Lugs": "as Boot.L.Lugs",
    "Boot.L.Tongue": "the tongue's padding over the instep allowance", "Boot.R.Tongue": "as Boot.L.Tongue",
    "Boot.L.Collar": "a padded roll on the rim, attached by its edge; its inner face looks across the shaft's ease",
    "Boot.R.Collar": "as Boot.L.Collar",
    "Belt.Rig.R.Carrier.1.PMAG": "the spare magazine stands 53 mm proud of its carrier, above the platform's top",
    "Belt.Rig.R.Carrier.2.PMAG": "as Carrier.1.PMAG",
    "Belt.Rig.R.Carrier.1.Cord": "the shock cord stretched over the spare magazine's floor plate, anchored at both ends",
    "Belt.Rig.R.Carrier.2.Cord": "as Carrier.1.Cord",
    "Belt.Rig.L.Platform": "lifted 6 mm over the trousers and cargo pockets so the thigh straps run under it (PLATFORM_LIFT)",
    "Belt.Rig.R.Platform": "as Belt.Rig.L.Platform",
    "Belt.Rig.L.Hanger": "a webbing hanger spanning from the belt to the platform's top edge over the hip crease",
    "Belt.Rig.R.Hanger": "as Belt.Rig.L.Hanger",
    "Sock.": "a garment: it lies on the skin",
}


def surface_samples(V, F, n, seed=0):
    """n points spread over a mesh's faces by area (fan-triangulated), with their face normals: a coarse box has
    vertices only at its corners, and a vertex test reads a box resting on a curved surface by its middle as
    standing off at its corners."""
    import numpy as np
    T = np.array([(f[0], f[i], f[i + 1]) for f in F for i in range(1, len(f) - 1)])
    A, B, Cc = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    cr = np.cross(B - A, Cc - A)
    area = np.linalg.norm(cr, axis=1)
    keep = area > 1e-9
    T, A, B, Cc, cr, area = T[keep], A[keep], B[keep], Cc[keep], cr[keep], area[keep]
    rng = np.random.default_rng(seed)
    k = rng.choice(len(T), size=n, p=area / area.sum())
    r1, r2 = rng.random(n), rng.random(n)
    sq = np.sqrt(r1)
    P = (1 - sq)[:, None] * A[k] + (sq * (1 - r2))[:, None] * B[k] + (sq * r2)[:, None] * Cc[k]
    N = cr[k] / area[k][:, None]
    return P, N


def standoff_report(groups, parts=STANDOFF_PARTS, keep_all=False):
    """Parts that stand off whatever they should sit on (round 6; the clash test cannot see a part in the air).

    Per object of the tested parts, in the hero pose (Subdivision off, Solidify ON: the real surfaces, unlike the clash
    test), at STANDOFF_SAMPLES points spread over its faces by area (surface_samples), orientation-free (some meshes
    are wound inward):
      - the support direction of a vertex is the direction to the skin's nearest point; the sample's face normal line,
        signed to look that way, must lie within 60 degrees of it;
      - a ray along it whose first surface is the object itself starts on the object's far side (it crosses its
        own body) and is skipped; the others form the object's ATTACHMENT FACE, and their gap is the distance to
        the first surface of any other object (another part, another object of the same part, the body) within
        STANDOFF_CAP mm, else the cap;
      - the sample's clearance is the distance to the nearest surface of any other object (within STANDOFF_MM).
    Flagged:
      - "floats": no surface sample within STANDOFF_TOUCH (2.5 mm) of another object (a clip in the air, a
        ladder-lock lying over its strap);
      - "stands off": otherwise, when the median gap over the attachment face exceeds STANDOFF_MM, under 20 %
        (STANDOFF_HOLD) of that face is within STANDOFF_TOUCH, and the face holds at least 10 % of the samples (a pouch hinged out
        from the belt by one edge, a cap standing off the knee);
      - "dangles": a thin object (under 8 mm in its smallest extent: a cord, a rod) with 40 % or more of its
        samples further than STANDOFF_MM from anything (stiff tails hanging in the air).
    Designed gaps (STANDOFF_DESIGNED, with the reason) are listed apart. A heuristic: it finds the faults the
    critics found in round 5; a part sitting in the right place but in the wrong form passes."""
    import numpy as np
    from mathutils import Vector
    import common as C
    t0 = time.perf_counter()
    Vs, Fs, owner, n = [], [], [], 0
    datas = {}
    for part, objs in groups.items():
        for o in objs:
            if o.type != "MESH":
                continue
            V, F = C.evaluated_world_mm(o, disable=("SUBSURF",))     # the real surfaces: Solidify on
            if not len(V) or not F:
                continue
            datas[o.name] = (part, V, F)
            Vs.append(V)
            Fs += [tuple(i + n for i in f) for f in F]
            owner += [o.name] * len(F)
            n += len(V)
    allbvh = C.bvh_from(np.concatenate(Vs), Fs)
    Vb, Fb = next((V, F) for (part, V, F) in datas.values() if part == "body")
    body_bvh = C.bvh_from(Vb, Fb)
    out, designed, every = [], [], []
    for nm, (part, V, F) in datas.items():
        if part not in parts:
            continue
        Ps, Ns = surface_samples(V, F, STANDOFF_SAMPLES, seed=len(nm))
        idx = np.arange(len(Ps))
        gaps, near = [], []
        for i in idx:
            p, nv = Vector(Ps[i]), Vector(Ns[i])
            hits = [h for h in allbvh.find_nearest_range(p, STANDOFF_MM) if owner[h[2]] != nm]
            near.append(min(h[3] for h in hits) if hits else STANDOFF_MM + 1.0)
            loc, _nrm, _k, dist = body_bvh.find_nearest(p)
            if loc is None or dist < 1e-6 or nv.length < 0.5:
                continue
            d = (loc - p).normalized()
            if abs(d.dot(nv)) < STANDOFF_COS:
                continue                      # a side face: its normal looks past the body
            h = allbvh.ray_cast(p + d * 0.05, d, STANDOFF_CAP)
            if h[0] is not None and owner[h[2]] == nm:
                continue                      # the ray crosses the object's own body: its far side
            gaps.append(STANDOFF_CAP if h[0] is None else h[3] + 0.05)
        near = np.array(near)
        gaps = np.array(gaps)
        lo, hi = Ps.min(0), Ps.max(0)
        thin = float(np.min(hi - lo)) < 8.0
        rec = {"object": nm, "part": part, "samples": int(len(idx)), "attach_share": round(len(gaps) / len(idx), 2),
               "median_gap_mm": round(float(np.median(gaps)), 1) if len(gaps) else None,
               "attach_contact": round(float(np.mean(gaps <= STANDOFF_TOUCH)), 2) if len(gaps) else 0.0,
               "nearest_other_mm": round(float(near.min()), 1) if near.min() <= STANDOFF_MM else f">{STANDOFF_MM:g}",
               "contact_share": round(float(np.mean(near <= STANDOFF_TOUCH)), 2),
               "far_share": round(float(np.mean(near > STANDOFF_MM)), 2)}
        flags = []
        if near.min() > STANDOFF_TOUCH:
            flags.append("floats")
        elif len(gaps) >= 0.1 * len(idx) and np.median(gaps) > STANDOFF_MM and rec["attach_contact"] < STANDOFF_HOLD:
            flags.append("stands off")
        if thin and rec["far_share"] >= 0.4:
            flags.append("dangles")
        rec["flags"] = flags
        if keep_all:
            every.append(rec)
        why = next((w for k, w in STANDOFF_DESIGNED.items() if nm == k or (k.endswith(".") and nm.startswith(k))), None)
        if why and flags:
            rec["designed"] = why
            designed.append(rec)
        elif flags:
            out.append(rec)
    out.sort(key=lambda r: -(r["median_gap_mm"] or 99.0))
    return {"threshold_mm": STANDOFF_MM, "touch_mm": STANDOFF_TOUCH, "cap_mm": STANDOFF_CAP, "parts": list(parts), "standing_off": out,
            "designed": designed, "objects_tested": sum(1 for d in datas.values() if d[0] in parts),
            "seconds": round(time.perf_counter() - t0, 1), **({"all": every} if keep_all else {})}


def standoff_md(n):
    path = os.path.join(round_dir(n), "standoff.json")
    if not os.path.exists(path):
        return None
    S = json.load(open(path, encoding="utf-8"))
    L = [f"# Round {n}: parts standing off what they should sit on (hero pose)", "",
         f"Generated by `scripts/assemble.py` (`standoff_report`). Parts {', '.join(S['parts'])}: per object, the "
         "attachment face is the surface samples whose normal line looks toward the skin (rays crossing the object's own body "
         "skipped); the gap is the ray in the "
         f"skin's direction to any other object's surface (cap {S['cap_mm']:g} mm). Flags (see `standoff_report`): "
         f"floats (nothing within {S.get('touch_mm', 2.5):g} mm), stands off (median gap over the attachment face over "
         f"{S['threshold_mm']:g} mm with under 20 % of it touching), dangles (a thin object mostly over "
         f"{S['threshold_mm']:g} mm from anything). {S['objects_tested']} objects tested.", "",
         "| Object | Flags | Median gap over the attachment face (mm) | Attachment face share | Nearest other object (mm) | Share within 2.5 mm |",
         "|---|---|---:|---:|---:|---:|"]
    for r in S["standing_off"]:
        L.append(f"| {r['object']} | {', '.join(r['flags'])} | {r['median_gap_mm']} | {r['attach_share']} | "
                 f"{r['nearest_other_mm']} | {r['contact_share']} |")
    if not S["standing_off"]:
        L.append("| (none) | | | | | |")
    if S["designed"]:
        L += ["", "Designed gaps (not flagged): " + "; ".join(
            f"{r['object']} ({', '.join(r['flags'])}, median {r['median_gap_mm']}: {r['designed']})" for r in S["designed"])]
    L += ["", f"Test time {S['seconds']} s."]
    with open(os.path.join(round_dir(n), "standoff.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    return rel(os.path.join(round_dir(n), "standoff.md"))


def blender_main(argv):
    import bpy
    import numpy as np
    from mathutils import Matrix
    import common as C
    from eval import camera, camproj, grade as GR, render as R, scene as S
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--no-cycles", action="store_true")
    ap.add_argument("--no-clash", action="store_true")
    a = ap.parse_args(argv)
    out = round_dir(a.round)
    os.makedirs(out, exist_ok=True)
    T = {}
    t0 = time.perf_counter()
    stamps = {"base_blend": stamp(os.path.getmtime(BASE_BLEND)), "hero_pose_json": stamp(os.path.getmtime(HERO_JSON))}
    hero = json.load(open(HERO_JSON, encoding="utf-8"))
    body, rig = C.open_base()
    stamps["part_caches"] = {p: stamp(os.path.getmtime(os.path.join(CACHE, "parts", f"{p}.blend")))
                             for p in PARTS if os.path.exists(os.path.join(CACHE, "parts", f"{p}.blend"))}
    groups, loaded, bound = {"body": [body]}, {}, {}
    for p in PARTS:
        if p == "carbine" or not os.path.exists(os.path.join(CACHE, "parts", f"{p}.blend")):
            continue
        c = C.load_part(p, rig)
        if c is None:
            continue
        loaded[p] = c
        bound[p] = bound_report(c, rig)
        # render-only fuzz (the head's stubble strands and tear lines: ob["sgt_role"] == "render") is rooted in the
        # skin by design and stays out of the clash and stand-off reports
        groups[p] = [o for o in c.all_objects if o.type == "MESH" and o.get("sgt_role") != "render"]
    head_look = None
    if "head" in loaded and os.path.exists(os.path.join(SCRIPTS, "parts", "head_look.py")):
        # head round 10 (head.md §13): the head part's skin goes on Body.Mesh, base.py's eyes and brow and lash
        # cards give way to the part's, and its hair curves are parented to the head bone
        import head_look as HLK
        head_look = HLK.on_assemble(body, rig, loaded["head"])
        print("[assemble] head look:", json.dumps(head_look), flush=True)
    used = C.apply_hero_pose(rig)
    carb, carb_check = place_carbine(rig, hero)
    if carb is not None:
        loaded["carbine"] = carb
        groups["carbine"] = [o for o in carb.all_objects if o.type == "MESH"]
        bound["carbine"] = {"objects": len(groups["carbine"]), "bound": len(groups["carbine"]), "unbound": [],
                            "how": "children of Carbine.Root, bone-parented to wrist.R"}
    pchk = pose_check(rig, hero)
    T["assemble"] = round(time.perf_counter() - t0, 1)
    print("[assemble] loaded", list(loaded), "pose:", used, flush=True)

    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        if ob.name.startswith("Scene."):
            bpy.data.objects.remove(ob, do_unlink=True)
    camera.hero_camera(sc)
    floor = S.build_floor(sc)
    lights = S.build_lights(sc)
    for L in lights:
        L.data.energy *= LIGHT_SCALE
    S.build_world(sc, "hdri")
    S.colour_management(sc)
    rig.hide_render = True
    t = time.perf_counter()
    tmp = ASSEMBLED + ".tmp.blend"
    bpy.ops.wm.save_as_mainfile(filepath=tmp, copy=True, compress=True)
    os.replace(tmp, ASSEMBLED)
    T["save"] = round(time.perf_counter() - t, 1)
    print("[assemble] saved", rel(ASSEMBLED), flush=True)

    part_of = {o.name: p for p, objs in groups.items() for o in objs}
    shown = [o for o in sc.objects if o.type == "MESH" and not o.name.startswith("Scene.")]
    times = {}

    def wb(path, colour=None):
        R._set_tier(sc, "form")
        sh = sc.display.shading
        if colour:
            sh.color_type = "OBJECT"
            for o in shown:
                o.color = (*colour(o), 1.0)
        sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
        sc.render.film_transparent = True
        floor.hide_render = True
        tt = time.perf_counter()
        bpy.ops.render.render()
        R._save(sc, path, "PNG", "8", "RGBA")
        times[os.path.basename(path)] = round(time.perf_counter() - tt, 2)

    def cy(path):
        R._set_tier(sc, "look", samples=a.samples)
        sc.cycles.denoising_quality = "HIGH"
        S.colour_management(sc)
        sc.render.film_transparent = True
        floor.hide_render = False
        tt = time.perf_counter()
        bpy.ops.render.render()
        # round 8 (PLAN.md Decision 6): the evaluation's grade is applied here, so every sheet, overlay and
        # critic packet shows the graded frame; the ungraded render is kept beside it
        ung = path[:-4] + "_ungraded.png"
        R._save(sc, ung, "PNG", "16", "RGBA")
        GR.grade_file(ung, path)
        times[os.path.basename(path)] = round(time.perf_counter() - tt, 2)

    def part_colour(o):
        p = part_of.get(o.name, "body")
        return PART_CLAY.get(p, (0.5, 0.5, 0.5))

    reg = camera.load_registry()
    ids = [p["id"] for p in json.load(open(REF_PRESETS, encoding="utf-8"))["presets"] if p["id"].startswith("ref.")]
    t = time.perf_counter()
    for pid in ids:
        p = reg.get(pid)
        lab = p["label"]
        camera.apply(p, sc, percent=100)
        wb(os.path.join(out, f"{lab}_clay.png"))
        wb(os.path.join(out, f"{lab}_parts.png"), colour=part_colour)
        if not a.no_cycles:
            cy(os.path.join(out, f"{lab}_cycles.png"))
        print(f"[assemble] rendered {pid}", flush=True)
    T["hero_renders"] = round(time.perf_counter() - t, 1)

    # turnarounds: the posed figure's bounding box centre, 150 mm lens at 6 m, a tinted clay per object
    t = time.perf_counter()
    Vb, _ = C.evaluated_world_mm(body)
    allV = [Vb] + [C.evaluated_world_mm(o)[0] for p, objs in groups.items() if p != "body" for o in objs]
    allV = np.concatenate([v for v in allV if len(v)]) / 1000.0
    lo, hi = allV.min(0), allV.max(0)
    centre = (lo + hi) / 2.0
    pc = camera.preset_camera(sc)
    sc.camera = pc

    for name, d in TURN.items():
        pos = centre + np.array(d) * 6.0
        Rm = camproj.look_at_matrix(pos, centre)
        Mv = np.eye(4)
        Mv[:3, :3], Mv[:3, 3] = Rm, pos
        pc.matrix_world = Matrix(Mv.tolist())
        pc.data.type, pc.data.lens, pc.data.sensor_width, pc.data.sensor_fit = "PERSP", 150.0, 36.0, "HORIZONTAL"
        pc.data.shift_x = pc.data.shift_y = 0.0
        pc.data.clip_start, pc.data.clip_end = 0.05, 100.0
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 600, 1000, 100
        wb(os.path.join(out, f"turn_{name}.png"), colour=part_colour)
    T["turnarounds"] = round(time.perf_counter() - t, 1)

    clashes = None
    if not a.no_clash:
        print("[assemble] interpenetration ...", flush=True)
        clashes = clash_report(groups)
        clashes["pose"] = used
        with open(os.path.join(out, "clashes.json"), "w", encoding="utf-8") as f:
            json.dump(clashes, f, indent=1)
        T["clashes"] = clashes["seconds"]
        print("[assemble] stand-off ...", flush=True)
        so = standoff_report(groups)
        with open(os.path.join(out, "standoff.json"), "w", encoding="utf-8") as f:
            json.dump(so, f, indent=1)
        T["standoff"] = so["seconds"]
        print(f"[assemble] stand-off: {len(so['standing_off'])} objects over {STANDOFF_MM:g} mm", flush=True)
    info = {"round": a.round, "pose": used, "pose_check": pchk, "carbine": carb_check, "parts_loaded": list(loaded),
            "bound": bound, "head_look": head_look, "inputs_at_load": stamps, "assembled": rel(ASSEMBLED),
            "posed_bbox_mm": {"lo": [round(float(v) * 1000) for v in lo], "hi": [round(float(v) * 1000) for v in hi]},
            "cycles": None if a.no_cycles else {"samples": a.samples, "denoiser": "OIDN (HIGH)", "view": "AgX Medium High Contrast, graded (eval/grade.py)",
                                                "lights": f"scene.py x {LIGHT_SCALE}"},
            "render_seconds": times, "seconds": T, "total_seconds": round(time.perf_counter() - t0, 1)}
    with open(os.path.join(out, "assembly_blender.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=1)
    print("[assemble] blender done", json.dumps(T), flush=True)
    return 0


# =========================================================================== outside Blender: sheets, summary, packet

def compose(n):
    import numpy as np
    from PIL import Image, ImageDraw
    from eval import camera
    from tools import sheet as SH
    out = round_dir(n)
    reg = camera.load_registry()
    ids = [p["id"] for p in json.load(open(REF_PRESETS, encoding="utf-8"))["presets"] if p["id"].startswith("ref.")]
    made = []

    def label(im, text):
        h = max(26, im.height // 36)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, im.width, h), fill=(0, 0, 0))
        d.text((8, h // 8), text, fill=(255, 255, 255), font=SH.font(int(h * 0.7)))
        return im

    def edge(alpha, w):
        e = SH.edge(alpha)
        for _ in range(max(0, w - 1)):
            g = e.copy()
            g[1:] |= e[:-1]
            g[:-1] |= e[1:]
            g[:, 1:] |= e[:, :-1]
            g[:, :-1] |= e[:, 1:]
            e = g
        return e

    def row(panels, path, long_side=2400):
        """Panels side by side; wide ones (the full hero frame) in a grid two across."""
        w, h = panels[0].size
        cols = 2 if w > 1.3 * h and len(panels) > 2 else len(panels)
        rows = -(-len(panels) // cols)
        s = Image.new("RGB", (cols * w + 8 * (cols - 1), rows * h + 8 * (rows - 1)), (0, 0, 0))
        for i, p in enumerate(panels):
            s.paste(p, ((i % cols) * (w + 8), (i // cols) * (h + 8)))
        SH.fit(s, long_side).save(path)
        made.append(rel(path))

    for pid in ids:
        p = reg.get(pid)
        lab = p["label"]
        ref, _ = SH.reference(p)
        clay_p, cyc_p, parts_p = (os.path.join(out, f"{lab}_{k}.png") for k in ("clay", "cycles", "parts"))
        if not os.path.exists(clay_p):
            continue
        clay = Image.open(clay_p).convert("RGBA")
        if clay.size != ref.size:
            ref = ref.resize(clay.size, Image.LANCZOS)
        alpha = np.asarray(clay)[:, :, 3] > 127
        w = max(2, clay.height // 450)
        e = edge(alpha, w)
        panels = [label(ref.copy(), f"reference {pid}"), label(SH.flat(clay), "clay")]
        if os.path.exists(parts_p):
            panels.append(label(SH.flat(Image.open(parts_p)), "parts (one colour per part)"))
        cyc = SH.flat(Image.open(cyc_p)) if os.path.exists(cyc_p) else None
        if cyc is not None:
            panels.append(label(cyc.copy(), "Cycles 64 spp, graded"))
        row(panels, os.path.join(out, f"{lab}_compare.png"))
        over = Image.blend(ref, cyc if cyc is not None else SH.flat(clay), 0.5)
        oa = np.array(over)
        oa[e] = (0, 255, 255)
        ra = np.array(ref)
        ra[e] = (0, 255, 255)
        row([label(Image.fromarray(oa), "reference 50 % + render 50 %, cyan = render silhouette"),
             label(Image.fromarray(ra), "reference, cyan = render silhouette")], os.path.join(out, f"{lab}_overlay.png"))
    turns = [os.path.join(out, f"turn_{v}.png") for v in TURN]
    if all(os.path.exists(t) for t in turns):
        ims = [label(SH.flat(Image.open(t), bg=(60, 60, 64)), v) for t, v in zip(turns, TURN)]
        w, h = ims[0].size
        g = Image.new("RGB", (3 * w + 16, 2 * h + 8), (0, 0, 0))
        for i, im in enumerate(ims):
            g.paste(im, ((i % 3) * (w + 8), (i // 3) * (h + 8)))
        g.save(os.path.join(out, "turnaround.png"))
        made.append(rel(os.path.join(out, "turnaround.png")))
    return made


def clash_md(n):
    path = os.path.join(round_dir(n), "clashes.json")
    if not os.path.exists(path):
        return None
    C = json.load(open(path, encoding="utf-8"))
    L = [f"# Round {n}: interpenetration in the hero pose", "",
         f"Generated by `scripts/assemble.py` from `clashes.json`. A vertex counts when it is more than "
         f"{C['threshold_mm']} mm inside another part's mesh (Solidify and Subdivision off, so a garment is its "
         "outer surface). Closed meshes by ray parity, open shells by the side of the nearest face within "
         f"{C['open_cap_mm']:g} mm ({C['body_cap_mm']:g} for the body; a part's open meshes merged into one surface). Only pairs across parts; an inner layer under an open outer one is expected "
         "and not tested. \"A in B\" = vertices of A inside B.", "",
         "| Pair | Category | Vertices | Max depth (mm) | Worst object pair (posed position, mm) |",
         "|---|---|---:|---:|---|"]
    for pk, P in C["pairs"].items():
        worst = max((q for t in P["directions"].values() for q in t["pairs"]), key=lambda q: q["max_mm"])
        L.append(f"| {pk} | {P['category']} | {P['count']} | {P['max_mm']:.1f} | "
                 f"{worst['x']} in {worst['y']}: {worst['count']} verts, {worst['max_mm']:.1f} at {worst['at_mm']} |")
    L += ["", "## By direction and object", ""]
    for pk, P in C["pairs"].items():
        for key, t in P["directions"].items():
            L.append(f"- **{key}**: {t['count']} vertices, max {t['max_mm']:.1f} mm")
            for q in t["pairs"][:6]:
                sp = q.get("spots") or []
                where = "; ".join(f"{s['count']} to {s['max_mm']:.1f} at {s['at_mm']}" for s in sp[1:4])
                L.append(f"  - {q['x']} in {q['y']}{'' if q['y_closed'] else ' (open shell)'}: {q['count']}, "
                         f"max {q['max_mm']:.1f} at {q['at_mm']}" + (f"; also {where}" if where else ""))
            if len(t["pairs"]) > 6:
                L.append(f"  - and {len(t['pairs']) - 6} more object pairs")
    L += ["", f"Test time {C['seconds']} s. Objects and their vertex counts are in `clashes.json`."]
    with open(os.path.join(round_dir(n), "clashes.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    return rel(os.path.join(round_dir(n), "clashes.md"))


SOLDIER_SPEC = """# The whole soldier, round {round} blockout

Sgt. Alex Morgan with every part of his kit, assembled and posed in the reference's hero pose: the body,
combat shirt and neck gaiter, combat trousers, boots, gloves, plate carrier with pouches and radio, shoulder
pauldrons, forearm guards and knee pads, belt and leg rigs, and the carbine in both hands.

## What "perfect" looks like

A viewer comparing the hero frame with the reference sees the same man, in the same pose, wearing the same kit
in the same places at the same sizes and in the same materials, each layer resting on the one beneath it, the
carbine held the way the reference holds it.

## Pass criteria

1. The figure's proportions (height, head, shoulder width, limb lengths) are the reference man's, apart from the
   declared differences.
2. The silhouette in the hero view follows the reference's: stance, lean, arms, the line of the carbine.
3. Every item of kit is where the reference puts it, at a plausible real size.
4. Layers stack as real kit does; nothing passes through anything else; nothing floats off the body.

## Critic questions

1. Proportions: do the height, head size, shoulder width, torso length and limb lengths read as the man in the
   reference (allowing the declared differences)?
2. Silhouette: does the outline in the hero view match the reference's stance, lean, arm positions and the
   carbine's line?
3. Placement: is each item of kit (gaiter, carrier and its pouches, radio antenna, pauldrons, forearm guards,
   gloves, belt and leg rigs, knee pads, boots) where the reference puts it, at a believable real size?
4. Layering: do the layers stack the way real kit does (skin, shirt, trousers, boots, gloves, then carrier,
   belt and armour, then the carbine in the hands), with nothing passing through or floating off what is under it?
5. Mass: do the bulk of the clothing and kit and the man's build read as the reference's?
6. The hold: does the carbine sit in the hands and against the body as the reference shows, as a real hold?

## Known failure modes

- Garments passing through each other or the skin where joints bend (elbows, lower back, neck).
- Gear floating off the body or sunk into it; straps that do not reach what they hold.
- The carbine through the arm, the hand or the carrier; a hand that does not close on it.
- Items placed by the drawing where the drawing contradicts itself (the declared differences) judged as defects.
"""

DECLARE = [
    "Materials are a second pass (round 8; round 9 drapes the trousers and the upper sleeves by cloth simulation): "
    "library recipes, painted textures and wear masks, but no stitching "
    "texture, folds driven by the joints (elbow crooks, knee bends), decal detail beyond the emblem, or fine dirt.",
    "The legs follow real thigh lengths; the drawn thighs are about 28 % short, so the knees, knee pads, leg rigs "
    "and belt sit higher than drawn.",
    "The carbine is a real M4-pattern carbine at real size (855 mm): the drawn gun is shorter, with an oversized "
    "receiver, a rail far above the bore and several muzzle tubes. The right hand is on a real pistol grip, about "
    "110 mm behind the drawn one.",
    "The scene is only the matched camera, the key, side and world lights and a plain floor: no hangar, haze or "
    "depth of field. The Cycles views are colour-graded so that neutral surfaces match the reference's neutrals "
    "(a warm key and a cooler side light); judge hue and value against the reference directly.",
    "The face is a parametric head fitted toward the reference (round 10: procedural skin, strand stubble and hair "
    "curves); its expression is neutral.",
]


def make_packet(n, head_loaded):
    out = round_dir(n)
    src = os.path.join(out, "critic_src")
    os.makedirs(src, exist_ok=True)
    from PIL import Image
    from eval import camera
    from tools import sheet as SH
    reg = camera.load_registry()
    renders, refs = [], []
    ids = [p["id"] for p in json.load(open(REF_PRESETS, encoding="utf-8"))["presets"]
           if p["id"].startswith("ref.") and p["id"] != "ref.full"]
    jobs = [("ref.soldier_full", "clay", "form", "BLENDER_WORKBENCH")] + [(i, "cycles", "look", "CYCLES") for i in ids]
    for pid, kind, tier, engine in jobs:
        p = reg.get(pid)
        f = os.path.join(out, f"{p['label']}_{kind}.png")
        if not os.path.exists(f):
            continue
        dst = os.path.join(src, f"{p['label']}_{kind}.png")
        SH.flat(Image.open(f)).save(dst)
        sc = {"preset": pid, "label": p["label"], "tier": tier, "engine": engine, "scene": "hero",
              "samples": 64 if engine == "CYCLES" else None,
              "view_transform": ["AgX", "AgX - Medium High Contrast"] if engine == "CYCLES" else ["Standard"],
              "graded": True}
        with open(os.path.splitext(dst)[0] + ".json", "w", encoding="utf-8") as fh:
            json.dump(sc, fh, indent=1)
        renders.append(dst)
        if pid not in [r.split("=")[0] for r in refs]:
            refs.append(f"{pid}={os.path.join(PROJECT, p['compare'][0])}")
    for v in TURN:     # the views the reference never shows, for layering from behind and the sides
        f = os.path.join(out, f"turn_{v}.png")
        if not os.path.exists(f):
            continue
        dst = os.path.join(src, f"turn_{v}.png")
        SH.flat(Image.open(f), bg=(60, 60, 64)).save(dst)
        with open(os.path.splitext(dst)[0] + ".json", "w", encoding="utf-8") as fh:
            json.dump({"preset": f"turnaround.{v}", "label": f"posed soldier, {v.replace('_', ' ')}, one flat "
                       "colour per part", "tier": "form", "engine": "BLENDER_WORKBENCH", "scene": "hero"}, fh, indent=1)
        renders.append(dst)
    spec = os.path.join(out, "critic_spec.md")
    with open(spec, "w", encoding="utf-8", newline="\n") as f:
        f.write(SOLDIER_SPEC.format(round=n))
    declare = list(DECLARE)
    if not head_loaded:
        declare.append("No hair or stubble yet: the head part is not in this round's assembly.")
    argv = [sys.executable, "-I", os.path.join(SCRIPTS, "eval", "critic", "packet.py"),
            "--out", os.path.join(out, "critic"), "--part", "18", "--round", str(n), "--spec", spec,
            "--scope", "the whole soldier: proportions, silhouette, placement, layering, the hold, and the first "
                       "materials (values, colours, wear) against the reference; ignore fine surface detail",
            "--presets", REF_PRESETS, "--force"]
    for r in renders:
        argv += ["--render", r]
    for r in refs:
        argv += ["--ref", r]
    for d in declare:
        argv += ["--declare", d]
    r = subprocess.run(argv, cwd=PROJECT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout + r.stderr).strip()[-1500:]
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"     # a redirected stdout on Windows is cp1252 (round 8)
    print(out.encode(enc, "replace").decode(enc, "replace"), flush=True)
    if r.returncode:
        print(f"[assemble] packet.py failed (exit {r.returncode})", flush=True)
        return None
    return rel(os.path.join(out, "critic"))


def main(argv):
    ap = argparse.ArgumentParser(description="Integration and evaluation of a round (see the module doc).")
    ap.add_argument("--round", type=int, help="evaluate into renders/round_NN/")
    ap.add_argument("--rebuild", nargs="*", metavar="ITEM", help="rebuild what is stale (no names), the named "
                    "items, or all, before evaluating")
    ap.add_argument("--status", action="store_true", help="print the build order and freshness, then stop")
    ap.add_argument("--no-cycles", action="store_true")
    ap.add_argument("--no-clash", action="store_true")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--sheets-only", action="store_true", help="recompose from the renders already made")
    ap.add_argument("--packet", action="store_true", help="build the whole-soldier critic packet (no critics run)")
    a = ap.parse_args(argv)
    t0 = time.perf_counter()
    timing = {}
    rows = status()
    if a.status:
        return 0
    rebuilt = []
    if a.rebuild is not None:
        t = time.perf_counter()
        rebuilt = rebuild(a.rebuild)
        timing["rebuild"] = round(time.perf_counter() - t, 1)
        rows = status(quiet=True)
    if a.round is None:
        return 0
    out = round_dir(a.round)
    os.makedirs(out, exist_ok=True)
    stale = [r for r in rows if r["state"] != "fresh"]
    for r in stale:
        print(f"[assemble] WARNING {r['item']} is {r['state']}: {r['why']}", flush=True)
    if not a.sheets_only:
        from lib import env
        cmd, environ = env.blender_cmd(["-b", "--python", os.path.abspath(__file__), "--", "--blender",
                                        "--round", str(a.round), "--samples", str(a.samples)]
                                       + (["--no-cycles"] if a.no_cycles else [])
                                       + (["--no-clash"] if a.no_clash else []))
        log = os.path.join(out, "assemble_blender.log")
        t = time.perf_counter()
        with open(log, "w", encoding="utf-8", errors="replace") as fh:
            r = subprocess.run(cmd, env=environ, cwd=PROJECT, stdout=fh, stderr=subprocess.STDOUT)
        timing["blender"] = round(time.perf_counter() - t, 1)
        lines = [l for l in open(log, encoding="utf-8", errors="replace").read().splitlines()
                 if l.startswith(("[assemble]", "Traceback", "  File")) or "Error" in l]
        print("\n".join(lines[-30:]), flush=True)
        print(f"[assemble] Blender {timing['blender']} s, exit {r.returncode} (log {rel(log)})", flush=True)
        if r.returncode:
            return r.returncode
    t = time.perf_counter()
    made = compose(a.round)
    md = clash_md(a.round)
    smd = standoff_md(a.round)
    timing["sheets"] = round(time.perf_counter() - t, 1)
    bj = os.path.join(out, "assembly_blender.json")
    info = json.load(open(bj, encoding="utf-8")) if os.path.exists(bj) else {}
    packet = None
    if a.packet:
        t = time.perf_counter()
        packet = make_packet(a.round, "head" in info.get("parts_loaded", []))
        timing["packet"] = round(time.perf_counter() - t, 1)
    timing["total"] = round(time.perf_counter() - t0, 1)
    info.update({"freshness": rows, "rebuilt": [{"item": n, "seconds": s, "ok": ok} for n, s, ok in rebuilt],
                 "sheets": made, "clashes_md": md, "standoff_md": smd, "packet": packet, "driver_seconds": timing,
                 "missing_parts": [p for p in PARTS if not os.path.exists(os.path.join(CACHE, "parts", f"{p}.blend"))]})
    with open(os.path.join(out, "assembly.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=1)
    print(f"[assemble] round {a.round}: {len(made)} sheets, {md}, packet {packet}; {json.dumps(timing)}", flush=True)
    return 0


if __name__ == "__main__":
    in_blender = "bpy" in sys.modules
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ([] if in_blender else sys.argv[1:])
    if in_blender:
        try:
            rc = blender_main([x for x in args if x != "--blender"])
        except Exception:
            import traceback
            traceback.print_exc()
            rc = 1
        sys.stdout.flush()
        if rc:
            os._exit(rc)
    else:
        sys.exit(main(args))
