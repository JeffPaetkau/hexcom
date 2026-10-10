"""Assemble the character in stages (spec 18 §4.6): S0 env to S13 export, each stage in a fresh Blender
process that opens the previous stage's output, recorded in the build journal (cache/build_state.json)
so that an interrupted build resumes where it stopped and a stage whose inputs did not change is skipped.

Built so far (2026-10-10), in cut-down form:
  S0 env        cache/env.json, the Blender and MPFB versions, free disk
  S1 body.base  the MPFB human at the macro values of specs 03 and 04, height fitted to the rest stature,
                re-grounded on its lowest vertex and centred between the ankle joints, facing -Y;
                no proportion solver, remap or re-loop yet          -> cache/body/base.blend
  S2 rig.fit    MPFB's `default` rig with its own weights; no added bones, rolls or weight clean-up yet
                (spec 08 §4.2-4.4)                       -> cache/body/rigged.blend, bones.json
Every later stage stops the run with exit 5 and says that it is not built yet.

  python -I scripts/build_all.py [--to S] [--from S] [--only S] [--force] [--dry-run] [--parts 02,09]
         [--proxy-missing] [--jobs 1|2] [--quality form|look|eval|cal|final] [--server NAME]
  ($SGT_PYIMG on Windows, where python3 is a Store stub; the driver needs only the standard library)
  blender -b [input.blend] --python-exit-code 1 --python scripts/build_all.py -- --exec S1   (one stage)

Stages are named by id or by name (S2 or rig.fit). A stage is fresh when the journal holds it done with
the key computed now (this script, the library modules it imports, the stage's parameters, the key of
its input stage, the Blender and MPFB versions) and its outputs exist; --dry-run says why one is stale.
Exit codes: 0 done, 2 a tolerance failed, 3 a missing input, 4 an error, 5 a stage not built yet.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)  # python -I leaves the script's folder off the path
from lib import cache, env, log, naming  # noqa: E402

THIS = os.path.abspath(__file__)
PASS, TOLERANCE, MISSING, ERROR, NOT_BUILT = 0, 2, 3, 4, 5
BODY_DIR = env.path("cache", "body")
LOG_DIR = env.path("cache", "build")
BODY, RIG, BODY_COLL = "Body.Mesh", "Morgan.Rig", "Body"  # spec 18 §7.1: Character/Body holds these two
QUALITIES = ("form", "look", "eval", "cal", "final")

# (id, name, specs, what the full stage does): spec 18 §4.6
STAGES = (
    ("S0", "env", "18", "checks cache/env.json, versions, free disk"),
    ("S1", "body.base", "03, 04", "MPFB human, macro and detail targets, proportion solver, bake, remap, re-loop"),
    ("S2", "rig.fit", "08 (05 joint fix, 03 patella)", "rig fit, added bones, rolls, weight clean-up, bones.json"),
    ("S3", "body.regions", "04, 03, 01, 05, 06", "region sculpts, relief and mask bakes, nails, eyes, teeth, the foot last"),
    ("S4", "parts.rest", "15, 02, 13, 12, 14, 11, 10, 09, 07", "every part built on the rest body"),
    ("S5", "weights.rest", "08 §6", "weight transfer for skinned garments, overrides, finalize_weights"),
    ("S6", "pose", "08 §4.7-4.9", "rifle two-pin solve, arm IK, finger contact solve, bake to Hero.Pose"),
    ("S7", "simulate", "09, 10", "trousers, sleeves, gaiter relax; stability checks"),
    ("S8", "bake.cloth", "08 §6", "apply, detail passes, SurfaceDeform binds to Body.Mesh.Posed"),
    ("S9", "attach", "08 §7, 11, 12, 13, 14", "gear on the posed body, compressions, glove push-out, strap bites"),
    ("S10", "materials", "16", "recipes assigned, materials.lint(), wear masks"),
    ("S11", "assemble", "18", "the Character collection; hero and rest assemblies"),
    ("S12", "evaluate", "17, 18", "renders, metrics and critic packets of the requested parts"),
    ("S13", "export", "08 §7.6, 16 §5.4, 18 §4.10", "export copies, atlas bakes, LODs, glTF, validation"),
)
IDS = [s[0] for s in STAGES]
NAMES = {s[1]: s[0] for s in STAGES}

# --------------------------------------------------------------------------- S1 and S2 parameters

def age_macro(years):
    """MakeHuman's age macro: 0 = 1 y, 0.1875 = 11 y, 0.5 = 25 y, 1 = 90 y (piecewise linear)."""
    return 0.5 * (years - 1.0) / 24.0 if years <= 25.0 else 0.5 + 0.5 * (years - 25.0) / 65.0


# Specs 03 §4.1 and 04 §4.1 (the same macro values in both): a lean, muscular 40-year-old man.
MACRO = {"gender": 1.0, "age": round(age_macro(40.0), 6), "muscle": 0.70, "weight": 0.45, "proportions": 0.5,
         "cupsize": 0.5, "firmness": 0.5, "race": {"caucasian": 1.0, "asian": 0.0, "african": 0.0}}
# Rest stature, barefoot, skull top to sole. Jeff, 2026-10-10 (spec 01 §10.2 Q7): the figure matches the
# drawing, whose posed skull top stands 1855 mm above the floor; in boots the feet stand on the footbeds
# (+42 mm) and the pose costs 22 mm, so the rest stature is 1855 - 42 + 22 = 1835.
STATURE_MM, STATURE_TOL_MM = 1835.0, 0.25
HEIGHT_START = 0.583  # spec 03 §4.1's start value for 1855; the fit moves it
S1_PARAMS = {"macro": MACRO, "stature_mm": STATURE_MM, "tol_mm": STATURE_TOL_MM, "height_start": HEIGHT_START,
             "create": {"mask_helpers": True, "detailed_helpers": True, "extra_vertex_groups": True,
                        "feet_on_ground": True, "scale": 0.1},
             "origin": "floor under the midpoint of the ankle joint cubes"}
S2_PARAMS = {"rig": "default", "import_weights": True}
PARAMS = {"S1": S1_PARAMS, "S2": S2_PARAMS}
INPUTS = {"S2": os.path.join(BODY_DIR, "base.blend")}  # the .blend a stage's Blender opens
OUTPUTS = {"S1": [os.path.join(BODY_DIR, n) for n in ("base.blend", "base.json")],
           "S2": [os.path.join(BODY_DIR, n) for n in ("rigged.blend", "rigged.json", "bones.json")]}
BUILT = ("S0", "S1", "S2")

# Spec 08 §3.1 and §4.1, rest pose: what the finished S1-S2 will have to give. The cut-down body has
# no proportion solver yet, so S2 reports these and does not fail on them.
JOINT_TARGETS_MM = {"upperleg01.L head z (hip centre)": ("upperleg01.L", "head", 963.0),
                    "lowerleg01.L head z (knee axis)": ("lowerleg01.L", "head", 526.0),
                    "foot.L head z (ankle axis)": ("foot.L", "head", 80.0),
                    "upperarm01.L head z (GH centre)": ("upperarm01.L", "head", 1476.0),
                    "eye.L head z": ("eye.L", "head", 1740.0),
                    "head tail z (skull top less scalp)": ("head", "tail", 1835.0)}


class Usage(Exception):
    """A bad command line: exit 4, never argparse's 2, which here means a failed tolerance."""


def stage_id(s):
    if s in IDS:
        return s
    if s in NAMES:
        return NAMES[s]
    raise Usage(f"unknown stage {s!r}: one of {', '.join(f'{i} {n}' for i, n, _, _ in STAGES)}")


def describe(sid):
    return f"{sid} {STAGES[IDS.index(sid)][1]}"


def rel(path):
    return os.path.relpath(path, env.PROJECT_DIR).replace(os.sep, "/")


# --------------------------------------------------------------------------- S0 (in the driver)

def blender_version():
    """'4.5.14' from `blender --version`, or None when Blender does not start."""
    try:
        p = env.run_blender(["--version"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"Blender (\d+\.\d+\.\d+)", p.stdout or "")
    return m.group(1) if m else None


def stage_env():
    """S0: the recorded environment, the tool versions and the disk; (ok, summary)."""
    problems, notes = [], []
    rec = env.load()
    if not os.path.isfile(env.ENV_JSON):
        problems.append("cache/env.json is missing: run bash scripts/setup_session.sh")
    exe = env.blender_exe()
    bv = blender_version()
    if bv is None:
        problems.append(f"Blender does not start: {exe}")
    elif not bv.startswith("4.5."):
        problems.append(f"Blender {bv}: the pipeline is built and measured on 4.5 LTS (spec 18 §3.1)")
    elif bv != "4.5.14":
        notes.append(f"Blender {bv}, not the 4.5.14 the specs measured")
    mv = cache.mpfb_version()
    if mv == "absent":
        problems.append(f"MPFB is not installed in {env.user_resources()}: run bash scripts/setup_session.sh")
    elif mv != "2.0.17":
        notes.append(f"MPFB {mv}, not the 2.0.17 the specs measured")
    free_gb = shutil.disk_usage(env.PROJECT_DIR).free / 1e9
    if free_gb < 5.0:
        problems.append(f"{free_gb:.1f} GB free; the caches need about 5 GB (spec 18 §4.6)")
    summary = {"blender": bv, "blender_exe": exe, "mpfb": mv, "device": env.device(), "os": rec.get("os"),
               "free_gb": round(free_gb, 1), "env_json": os.path.isfile(env.ENV_JSON), "problems": problems,
               "notes": notes}
    return not problems, summary


# --------------------------------------------------------------------------- Blender helpers (S1, S2)

class _Mpfb:
    """MPFB's services, enabled in this session (the extension lives in the project's user resources)."""

    def __init__(self):
        import bpy
        mod = "bl_ext.user_default.mpfb"
        if mod not in bpy.context.preferences.addons:
            bpy.ops.preferences.addon_enable(module=mod)
        from bl_ext.user_default.mpfb.services.humanservice import HumanService
        from bl_ext.user_default.mpfb.services.targetservice import TargetService
        from bl_ext.user_default.mpfb.entities.objectproperties import HumanObjectProperties
        self.human, self.targets, self.props = HumanService, TargetService, HumanObjectProperties


def evaluated_co(ob, helpers=False):
    """World coordinates (m) of the evaluated mesh as an (n, 3) array. MPFB's targets are shape keys, so
    the mesh's own vertices never move: always measure the evaluated mesh. With helpers=True the MASK
    modifiers are switched off for the read, so the helper geometry (the joint cubes) is there and the
    indices are the mesh's own; otherwise only the `body` group's vertices are."""
    import bpy
    import numpy as np
    masks = [m for m in ob.modifiers if m.type == "MASK"] if helpers else []
    saved = [(m, m.show_viewport) for m in masks]
    for m in masks:
        m.show_viewport = False
    try:
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        ev.to_mesh_clear()
    finally:
        for m, v in saved:
            m.show_viewport = v
    mw = np.array(ob.matrix_world)
    return co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]


def group_indices(ob, name, min_weight=0.5):
    g = ob.vertex_groups.get(name)
    if g is None:
        raise KeyError(f"{ob.name} has no vertex group {name!r}")
    gi = g.index
    return [v.index for v in ob.data.vertices if any(e.group == gi and e.weight > min_weight for e in v.groups)]


def stature_mm(ob):
    """Skull top to sole of the evaluated body, mm (the helpers are masked, so this is the body alone)."""
    co = evaluated_co(ob)
    return float(co[:, 2].max() - co[:, 2].min()) * 1000.0


def save_blend(path):
    """Save the session to `path` atomically, as a copy (the session keeps its own file name)."""
    import bpy
    with cache.atomic(path) as tmp:
        bpy.ops.wm.save_as_mainfile(filepath=tmp, copy=True, compress=False)
    return path


def body_collection(scene, ob):
    """Put ob into the `Body` collection only (spec 18 §7.1 names it so inside Character)."""
    import bpy
    coll = bpy.data.collections.get(BODY_COLL)
    if coll is None:
        coll = bpy.data.collections.new(naming.check(BODY_COLL))
    if coll not in scene.collection.children_recursive:
        scene.collection.children.link(coll)
    for c in list(ob.users_collection):
        if c != coll:
            c.objects.unlink(ob)
    if ob.name not in coll.objects:
        coll.objects.link(ob)
    return coll


# --------------------------------------------------------------------------- S1 body.base

def fit_height(mpfb, body, target_mm, tol_mm, h0, say):
    """Solve MPFB's height macro for the evaluated stature target ± tol.

    The macro blends corner targets piecewise, so stature is monotonic in it but kinked: a plain secant
    can stall at a kink (it did at weight 0.60), so the root is bracketed first and then closed by the
    Illinois variant of false position, which always converges inside the bracket.
    Returns (macro, stature, evaluations, seconds per reapply_macro_details)."""
    t_apply, seen = [], []

    def at(h):
        t = time.perf_counter()
        mpfb.props.set_value("height", h, entity_reference=body)
        mpfb.targets.reapply_macro_details(body)
        t_apply.append(time.perf_counter() - t)
        s = stature_mm(body)
        seen.append((h, s))
        say(f"height macro {h:.5f} -> stature {s:.3f} mm")
        return s - target_mm

    a, fa = h0, at(h0)
    step = 0.05 if fa < 0 else -0.05
    b, fb = a, fa
    while abs(fb) > tol_mm and fa * fb > 0:  # walk until the target is bracketed
        a, fa = b, fb
        b = min(1.0, max(0.0, b + step))
        if b == a:
            raise RuntimeError(f"stature {target_mm} mm is out of the height macro's range")
        fb = at(b)
        step *= 2.0
    for _ in range(30):
        if abs(fb) <= tol_mm:
            break
        c = b - fb * (b - a) / (fb - fa)
        fc = at(c)
        if fc * fb < 0:  # the root lies between b and c: the old b becomes the other end
            a, fa = b, fb
        else:  # a is kept again: halve its value so the next step moves toward it (Illinois)
            fa /= 2.0
        b, fb = c, fc
    h, s = min(seen, key=lambda hs: abs(hs[1] - target_mm))
    if h != seen[-1][0]:
        at(h)
    return h, s, len(seen), round(sum(t_apply) / len(t_apply), 3)


def ground_and_centre(body, say):
    """Move the body so its lowest vertex is on z 0 and the midpoint of its ankle joint cubes is over the
    origin (CLAUDE.md: the origin is on the floor midway between the feet), baking the move into the mesh
    and every shape key so the object stays at the origin with an identity matrix (spec 08 §4.1)."""
    import bpy
    import numpy as np
    from lib import ctx as bctx
    co = evaluated_co(body, helpers=True)
    body_idx = np.array(group_indices(body, "body"))
    ankles = {s: co[group_indices(body, f"joint-{s}-ankle")].mean(axis=0) for s in ("l", "r")}
    mid = (ankles["l"] + ankles["r"]) / 2.0
    z0 = float(co[body_idx, 2].min())
    move = np.array([-mid[0], -mid[1], -z0])
    body.location = tuple(np.array(body.location) + move)
    bctx.set_active(body)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    co = evaluated_co(body, helpers=True)
    ankles = {s: co[group_indices(body, f"joint-{s}-ankle")].mean(axis=0) for s in ("l", "r")}
    feet = co[body_idx][co[body_idx, 2] < 0.04]
    left = feet[feet[:, 0] > 0]
    toe_y, heel_y = float(left[:, 1].min()), float(left[:, 1].max())
    out = {"moved_mm": [round(float(v) * 1000, 3) for v in move],
           "lowest_z_mm": round(float(co[body_idx, 2].min()) * 1000, 4),
           "ankle_l_mm": [round(float(v) * 1000, 2) for v in ankles["l"]],
           "ankle_r_mm": [round(float(v) * 1000, 2) for v in ankles["r"]],
           "left_toe_y_mm": round(toe_y * 1000, 2), "left_heel_y_mm": round(heel_y * 1000, 2),
           "faces_minus_y": bool(toe_y < ankles["l"][1] - 0.1 < heel_y)}
    say(f"moved {out['moved_mm']} mm; ankles L {out['ankle_l_mm']} R {out['ankle_r_mm']}; "
        f"left toe y {out['left_toe_y_mm']}, heel y {out['left_heel_y_mm']}")
    if not out["faces_minus_y"]:
        raise RuntimeError(f"the body does not face -Y (toes at y {toe_y:.3f} m, ankle {ankles['l'][1]:.3f} m)")
    return out


def stage_body_base(say):
    """S1, cut down: no proportion solver, remap or re-loop yet (specs 03 §4.2, 04 §4.2-4.3)."""
    import bpy
    t0 = time.perf_counter()
    bpy.ops.wm.read_factory_settings(use_empty=True)  # preferences reset in memory only; MPFB is re-enabled
    mpfb = _Mpfb()
    macro = mpfb.targets.get_default_macro_info_dict()
    macro.update({k: v for k, v in MACRO.items() if k != "race"})
    macro["race"] = dict(MACRO["race"])
    macro["height"] = HEIGHT_START
    body = mpfb.human.create_human(macro_detail_dict=macro, **S1_PARAMS["create"])
    body.name = body.data.name = naming.check(BODY)
    say(f"create_human: {len(body.data.vertices)} vertices, "
        f"{len(body.data.shape_keys.key_blocks) if body.data.shape_keys else 0} shape keys, "
        f"{len(body.vertex_groups)} vertex groups, {time.perf_counter() - t0:.1f} s")
    h, s, n, t_apply = fit_height(mpfb, body, STATURE_MM, STATURE_TOL_MM, HEIGHT_START, say)
    placed = ground_and_centre(body, say)
    final = stature_mm(body)
    body_collection(bpy.context.scene, body)
    out = OUTPUTS["S1"][0]
    save_blend(out)
    macros = {k: (dict(v) if isinstance(v, dict) else v) for k, v in macro.items()}
    macros["height"] = round(h, 6)
    summary = {"stage": "S1", "macro": macros, "stature_mm": round(final, 3), "stature_target_mm": STATURE_MM,
               "stature_tol_mm": STATURE_TOL_MM, "height_iterations": n, "reapply_macro_details_s": t_apply,
               "placement": placed, "vertices": len(body.data.vertices),
               "body_vertices": len(group_indices(body, "body")),
               "shape_keys": [k.name for k in body.data.shape_keys.key_blocks] if body.data.shape_keys else [],
               "vertex_groups": len(body.vertex_groups), "modifiers": [m.name for m in body.modifiers],
               "blender": bpy.app.version_string, "mpfb": cache.mpfb_version(), "written": log.now(),
               "seconds": round(time.perf_counter() - t0, 2),
               "not_yet": "no proportion solver, remap or re-loop (specs 03 §4.2, 04 §4.2-4.3)"}
    cache.write_json(OUTPUTS["S1"][1], summary)
    status = PASS if abs(final - STATURE_MM) <= STATURE_TOL_MM else TOLERANCE
    if status != PASS:
        say(f"stature {final:.2f} mm is outside {STATURE_MM} +/- {STATURE_TOL_MM}")
    return status, summary


# --------------------------------------------------------------------------- S2 rig.fit

def dump_bones(rig):
    """Every bone's head, tail, length (mm, world), roll and rest axes, for bones.json (spec 08 §4.1)."""
    import math
    import bpy
    mw = rig.matrix_world
    bones = {}
    for b in rig.data.bones:
        m = b.matrix_local.to_3x3()
        try:
            roll = math.degrees(bpy.types.Bone.AxisRollFromMatrix(m)[1])
        except (TypeError, ValueError, AttributeError):
            roll = None
        bones[b.name] = {"parent": b.parent.name if b.parent else None, "deform": b.use_deform,
                         "head": [round(v * 1000, 3) for v in mw @ b.head_local],
                         "tail": [round(v * 1000, 3) for v in mw @ b.tail_local],
                         "length": round(b.length * 1000, 3), "roll_deg": None if roll is None else round(roll, 4),
                         "x_axis": [round(v, 6) for v in m.col[0]], "y_axis": [round(v, 6) for v in m.col[1]],
                         "z_axis": [round(v, 6) for v in m.col[2]]}
    return bones


def stage_rig_fit(say):
    """S2, cut down: MPFB's default rig and weights only (spec 08 §4.1); no added bones (§4.2), canonical
    rolls (§4.3) or weight clean-up (§4.4) yet."""
    import bpy
    from mathutils import Matrix
    from lib import ctx as bctx
    t0 = time.perf_counter()
    body = bpy.data.objects.get(BODY)
    if body is None:
        raise FileNotFoundError(f"{rel(INPUTS['S2'])} holds no {BODY}: run S1")
    mpfb = _Mpfb()
    bctx.set_active(body)
    rig = mpfb.human.add_builtin_rig(body, S2_PARAMS["rig"], import_weights=S2_PARAMS["import_weights"])
    rig.name = rig.data.name = naming.check(RIG)
    rig.location = (0.0, 0.0, 0.0)  # MPFB copies the mesh's location to the rig; both are at the origin here
    body.location = (0.0, 0.0, 0.0)
    # MPFB puts its Armature modifier first; spec 08 §4.4 keeps the helper mask first, so the skinning
    # never deforms the helper geometry it is about to drop
    names = [m.name for m in body.modifiers]
    if "Hide helpers" in names and names.index("Hide helpers") > 0:
        with bctx.override(object=body):
            bpy.ops.object.modifier_move_to_index(modifier="Hide helpers", index=0)
    bpy.context.view_layer.update()
    ident = Matrix.Identity(4)
    for ob in (rig, body):
        err = max(abs(a - b) for ra, rb in zip(ob.matrix_world, ident) for a, b in zip(ra, rb))
        if err > 1e-9:
            raise RuntimeError(f"{ob.name}'s world matrix is not the identity (off by {err})")
    body_collection(bpy.context.scene, rig)
    bones = dump_bones(rig)
    cache.write_json(OUTPUTS["S2"][2], {"rig": RIG, "body": BODY, "units": "mm, world (the rig is at the origin)",
                                        "count": len(bones), "bones": bones})
    joints = {}
    for label, (bone, end, target) in JOINT_TARGETS_MM.items():
        if bone in bones:
            z = bones[bone][end][2]
            joints[label] = {"value": round(z, 1), "target": target, "delta": round(z - target, 1)}
    say(f"{len(bones)} bones, {sum(1 for b in bones.values() if b['deform'])} deforming; "
        f"armature modifier on {BODY}: {[m.name for m in body.modifiers if m.type == 'ARMATURE']}")
    for label, j in joints.items():
        say(f"  {label}: {j['value']} (spec 08: {j['target']}, {j['delta']:+.1f})")
    save_blend(OUTPUTS["S2"][0])
    summary = {"stage": "S2", "rig": RIG, "bones": len(bones),
               "deform_bones": sum(1 for b in bones.values() if b["deform"]),
               "vertex_groups": len(body.vertex_groups), "modifiers": [m.name for m in body.modifiers],
               "joints_vs_spec08": joints, "blender": bpy.app.version_string, "mpfb": cache.mpfb_version(),
               "written": log.now(), "seconds": round(time.perf_counter() - t0, 2),
               "not_yet": "no added bones, canonical rolls or weight clean-up (spec 08 §4.2-4.4)"}
    cache.write_json(OUTPUTS["S2"][1], summary)
    return PASS, summary


EXEC = {"S1": stage_body_base, "S2": stage_rig_fit}


def execute(sid):
    """Inside Blender: run one stage and print its RESULT line; the exit code says how it went."""
    def say(msg):
        log.info(f"build_all {sid}", msg)
    try:
        status, summary = EXEC[sid](say)
        res = {"stage": sid, "status": "done" if status == PASS else "tolerance", "exit": status,
               "outputs": [rel(p) for p in OUTPUTS[sid]], "summary": summary}
    except FileNotFoundError as e:
        status, res = MISSING, {"stage": sid, "status": "missing", "exit": MISSING, "error": str(e)}
    except Exception as e:  # reported to the driver; the traceback goes to the stage log
        import traceback
        traceback.print_exc()
        status, res = ERROR, {"stage": sid, "status": "error", "exit": ERROR, "error": f"{type(e).__name__}: {e}"}
    print("RESULT " + log.dumps(res), flush=True)
    return status


# --------------------------------------------------------------------------- the driver

def versions(env_summary):
    return {"blender": env_summary.get("blender"), "mpfb": env_summary.get("mpfb")}


def stage_inputs(sid, prev_key, vers):
    """What a stage's key hashes (spec 18 §4.5, Cache key, applied to a build stage)."""
    return {"stage": sid, "script": cache.sha256_file(THIS, text=True),
            "modules": {cache.rel(f): cache.sha256_file(f, text=True) for f in sorted(cache.imports(THIS))},
            "params": PARAMS.get(sid), "input": prev_key, "blender": vers["blender"], "mpfb": vers["mpfb"]}


def stale_reasons(journal, sid, key, inp):
    st = journal.state(sid)
    if not st:
        return ["never built"]
    if st.get("state") != "done":
        return [f"last run {st.get('state')}"]
    reasons = []
    if st.get("key") != key:
        reasons += cache.diff_inputs(st.get("inputs") or {}, inp) or ["key changed"]
    missing = [rel(p) for p in OUTPUTS.get(sid, []) if not os.path.isfile(p)]
    if missing:
        reasons.append("missing " + ", ".join(missing))
    return reasons


def run_stage(sid):
    """One stage in a fresh Blender that opens the stage's input; (exit code, RESULT dict or None)."""
    inp = INPUTS.get(sid)
    if inp and not os.path.isfile(inp):
        return MISSING, {"error": f"{rel(inp)} is missing: run the stage before {describe(sid)}"}
    argv = ["-b"] + ([inp] if inp else []) + ["--python-exit-code", "1", "--python", THIS, "--", "--exec", sid]
    cmd, environ = env.blender_cmd(argv)
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"{sid}.log")
    result, tail = None, []
    with open(log_path, "w", encoding="utf-8", newline="\n") as lf:
        p = subprocess.Popen(cmd, env=environ, cwd=env.PROJECT_DIR, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        for line in p.stdout:
            lf.write(line)
            tail = (tail + [line.rstrip()])[-40:]
            if line.startswith("RESULT "):
                result = line[len("RESULT "):]  # the last one wins: Blender's own output may follow it
            elif line.startswith(f"[build_all {sid}]"):
                print(line.rstrip(), flush=True)
        rc = p.wait()
    res = None
    if result:
        try:
            res = json.loads(result)
        except ValueError:
            res = None
    if res is None:
        print("\n".join(tail), flush=True)
        return (rc or ERROR), {"error": f"no RESULT line from Blender (exit {rc}); log {rel(log_path)}"}
    if res.get("exit") != PASS:
        print("\n".join(tail[-15:]), flush=True)
    res["log"] = rel(log_path)
    return res.get("exit", rc), res


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Usage(message)


def parse(argv):
    ap = _Parser(prog="build_all.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--from", dest="start", default="S0", help="first stage (id or name; default S0)")
    ap.add_argument("--to", dest="stop", default="S13", help="last stage (default S13 export)")
    ap.add_argument("--only", help="run this stage alone (its input must exist)")
    ap.add_argument("--parts", default="", help="parts for S3, S4 and S12, e.g. 02,09 (default all)")
    ap.add_argument("--force", action="store_true", help="re-run the selected stages even when fresh")
    ap.add_argument("--dry-run", action="store_true", help="say what would run and why; run nothing")
    ap.add_argument("--proxy-missing", action="store_true", help="parts use declared proxies for absent dependencies")
    ap.add_argument("--jobs", type=int, choices=(1, 2), default=1, help="independent parts of S3 and S4 in parallel")
    ap.add_argument("--quality", choices=QUALITIES, default="form", help="spec 17's render tier for S12")
    ap.add_argument("--server", help="run stages inside a warm server instead of fresh processes")
    ap.add_argument("--exec", dest="exec_stage", help=argparse.SUPPRESS)  # one stage, inside Blender
    return ap.parse_args(argv)


def drive(a):
    for out in (sys.stdout, sys.stderr):
        try:
            out.reconfigure(errors="backslashreplace")  # a cp1252 console must not stop a build over a dash
        except (AttributeError, ValueError):
            pass
    first, last = (stage_id(a.only),) * 2 if a.only else (stage_id(a.start), stage_id(a.stop))
    if IDS.index(last) < IDS.index(first):
        raise Usage(f"--to {last} comes before --from {first}")
    todo = IDS[IDS.index(first):IDS.index(last) + 1]
    for flag, used, stages in (("--parts", a.parts, "S3, S4, S12"), ("--proxy-missing", a.proxy_missing, "S3, S4"),
                               ("--jobs", a.jobs != 1, "S3, S4"), ("--quality", a.quality != "form", "S12")):
        if used:
            print(f"[build_all] {flag} applies to {stages}, which are not built yet: ignored")
    if a.server:
        print("[build_all] --server is not built yet: every stage runs in a fresh Blender process")
    journal = cache.Journal()
    t0 = time.perf_counter()
    ok, env_summary = stage_env()  # S0 always runs: the other stages' keys need its versions
    if "S0" in todo:
        for n in env_summary["notes"]:
            print(f"[build_all] S0 env: note: {n}")
        print(f"[build_all] S0 env: Blender {env_summary['blender']}, MPFB {env_summary['mpfb']}, "
              f"device {env_summary['device']}, {env_summary['free_gb']} GB free" + ("" if ok else ": FAILED"))
        if not a.dry_run:
            journal.mark("S0", "done" if ok else "failed", key=None, summary=env_summary)
    if not ok:
        for p in env_summary["problems"]:
            print(f"[build_all] S0 env: {p}")
        return MISSING
    vers = versions(env_summary)
    prev = None
    for sid in IDS[1:]:
        if IDS.index(sid) > IDS.index(last):
            break
        if sid not in BUILT:
            if sid in todo:
                i, n, specs, does = STAGES[IDS.index(sid)]
                print(f"[build_all] {i} {n} (specs {specs}: {does}): not built yet. Stages built so far: "
                      f"{', '.join(describe(s) for s in BUILT)}. Stopping.")
                return NOT_BUILT
            break
        inp = stage_inputs(sid, prev, vers)
        key = cache.key_of(inp)
        prev = key
        if sid not in todo:
            continue
        why = stale_reasons(journal, sid, key, inp)
        if a.dry_run:
            if why or a.force:
                print(f"[build_all] {describe(sid)}: would run: {'; '.join(why) or '--force'}")
            else:
                print(f"[build_all] {describe(sid)}: fresh (key {key[:12]})")
            continue
        if not why and not a.force:
            print(f"[build_all] {describe(sid)}: fresh (key {key[:12]}), skipped")
            continue
        print(f"[build_all] {describe(sid)}: running ({'; '.join(why) or '--force'})", flush=True)
        t = time.perf_counter()
        journal.mark(sid, "running", key=key, inputs=inp)
        try:
            code, res = run_stage(sid)
        except BaseException as e:
            journal.mark(sid, "failed", key=key, inputs=inp, error=repr(e)[:500])
            raise
        secs = round(time.perf_counter() - t, 1)
        if code != PASS:
            journal.mark(sid, "failed", key=key, inputs=inp, error=(res or {}).get("error"), exit=code)
            print(f"[build_all] {describe(sid)}: failed (exit {code}) after {secs} s: {(res or {}).get('error')}")
            return code
        journal.mark(sid, "done", key=key, inputs=inp, outputs=res.get("outputs", []), seconds=secs)
        print(f"[build_all] {describe(sid)}: done in {secs} s -> {', '.join(res.get('outputs', []))}")
    print(f"[build_all] {first}..{last}: done in {time.perf_counter() - t0:.1f} s")
    return PASS


def main():
    in_blender = "bpy" in sys.modules or os.path.basename(sys.executable).lower().startswith("blender")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ([] if in_blender else sys.argv[1:])
    try:
        a = parse(argv)
        if a.exec_stage:
            sid = stage_id(a.exec_stage)
            if sid not in EXEC:
                raise Usage(f"{describe(sid)} has no Blender stage")
            return execute(sid)
        return drive(a)
    except Usage as e:
        print(f"[build_all] {e}", flush=True)
        return ERROR


if __name__ == "__main__":
    sys.exit(main())
