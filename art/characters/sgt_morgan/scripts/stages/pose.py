"""Round 0, stage 2: the hero pose as data, applied to Morgan.Rig (PLAN.md, round 0 step 2).

The pose itself is solved outside Blender by pose_solve.py (numpy + scipy on the rig's rest matrices,
which base.py writes into cache/stages/base.json) and stored in scripts/stages/hero_pose.json: bone ->
local rotation quaternion (w, x, y, z), the root bone's location, the carbine frame and the grip points.
This script applies it, checks Blender's posed joints against the solver's forward kinematics, adds the
carbine stand-in, and saves the posed file.

  "$SGT_BLENDER" -b cache/stages/base.blend --python scripts/stages/pose.py [-- --solve]
      --solve   re-run the solver first ("$SGT_PYIMG" -I scripts/stages/pose_solve.py); before it, round 2's
                contact data (cache/stages/contact.npz, pose_contact.py) is re-exported when a part cache it
                reads is newer
      --export  with --solve: re-export the contact data anyway (it samples the carrier in the current pose)
  -> cache/stages/pose.blend (Body + collection Pose: Pose.Carbine.Frame, an empty bone-parented to
     wrist.R, and Pose.Carbine.Proxy, a block carbine 840 mm long in that frame)
     cache/stages/pose_check.json (Blender vs solver joint positions)

From another script (inside Blender):
  sys.path.insert(0, "<project>/scripts/stages"); from pose import apply_hero_pose, add_carbine_proxy
  apply_hero_pose(bpy.data.objects["Morgan.Rig"])

Carbine frame convention (shared with the carbine part): origin on the bore axis directly above the
trigger, +X along the bore toward the muzzle, +Z up through the top rail, +Y to the gun's left.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
HERO_JSON = os.path.join(HERE, "hero_pose.json")
BASE_BLEND = os.path.join(PROJECT, "cache", "stages", "base.blend")
OUT_BLEND = os.path.join(PROJECT, "cache", "stages", "pose.blend")
CHECK_JSON = os.path.join(PROJECT, "cache", "stages", "pose_check.json")
RIG, COLL = "Morgan.Rig", "Pose"
FRAME, PROXY = "Pose.Carbine.Frame", "Pose.Carbine.Proxy"

# Block stand-in of an M4-pattern carbine in the carbine frame (mm): (name, x0, x1, y half, z0, z1,
# x shift of the bottom face for a raked part)
PROXY_BOXES = (
    ("stock", -295, -195, 22, -85, 12, 0),
    ("buffer_tube", -195, -140, 15, -22, 10, 0),
    ("receiver", -140, 115, 13, -45, 30, 0),
    ("pistol_grip", -95, -55, 16, -145, -45, -47),
    ("magazine", -20, 50, 12, -165, -45, 12),
    ("handguard", 115, 445, 22, -28, 27, 0),
    ("barrel", 445, 545, 10, -10, 10, 0),
)


# Round 3 (boots.md §8 item 7): the toes bend up at their MTP joints by the boots' last's toe spring, so the
# posed toes lie in the sprung toe box instead of through the sole. The proximal toe bones are leaves the solver
# does not fit (it seats heel, mt1 and mt5, which ride foot.*), so this moves nothing it solved; check() leaves
# the toes out.
TOE_SPRING_DEG = 12.0
TOE_BONES = tuple(f"toe{k}-1.{s}" for s in ("L", "R") for k in range(1, 6))
# What a solve depends on in base.json: the bones (rest heads, tails, parents) and the landmarks it fits, less
# the feet's (heel, toe, mt1, mt5), which only seat the feet on the footbeds and move with the foot stage while
# the bones do not (scripts/assemble.py re-solves only when this signature differs from the one recorded at the
# last solve, scripts/stages/hero_pose_basis.json; a full solve takes 25 min and is not reproducible).
BASIS_JSON = os.path.join(HERE, "hero_pose_basis.json")
BASE_JSON = os.path.join(PROJECT, "cache", "stages", "base.json")
FOOT_MARKS = ("heel_", "toe_", "mt1_", "mt5_")


def base_signature(path=BASE_JSON):
    """sha256 of what the solve reads from base.json (bones to 0.01 mm, landmarks but the feet's)."""
    import hashlib
    with open(path, encoding="utf-8") as f:
        b = json.load(f)
    bones = {n: [v["parent"], [round(x, 2) for x in v["head"]], [round(x, 2) for x in v["tail"]]]
             for n, v in sorted(b["bones"].items())}
    marks = {k: [round(x, 2) for x in v["rest_mm"]] for k, v in sorted(b["landmarks"].items())
             if not k.startswith(FOOT_MARKS)}
    blob = json.dumps({"bones": bones, "landmarks": marks}, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


def write_basis():
    with open(BASIS_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"doc": "pose.py base_signature() of the base.json hero_pose.json was solved on (scripts/assemble.py "
                          "re-solves only when it changes)", "base_signature": base_signature(),
                   "written": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=1)


def toe_spring(rig, deg=TOE_SPRING_DEG):
    """Turn each proximal toe bone up by deg about the foot's lateral axis (rest space), at its head (MTP)."""
    import math
    from mathutils import Quaternion, Vector
    for name in TOE_BONES:
        pb = rig.pose.bones.get(name)
        if pb is None:
            continue
        b = pb.bone
        d = (b.tail_local - b.head_local).normalized()
        axis = d.cross(Vector((0.0, 0.0, 1.0))).normalized()       # horizontal, across the toe
        q = Quaternion(axis, math.radians(deg))
        if (q @ d).z < d.z:                                         # the tip must rise
            q = Quaternion(axis, -math.radians(deg))
        R = b.matrix_local.to_3x3()
        pb.rotation_quaternion = (R.inverted() @ q.to_matrix() @ R).to_quaternion() @ pb.rotation_quaternion


def load_pose(path=HERO_JSON):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def apply_hero_pose(rig, path=HERO_JSON, data=None):
    """Pose `rig` (Morgan.Rig) into the hero pose: every pose bone reset to rest, then the stored local
    quaternions and the root location. Returns the pose data."""
    import bpy
    from mathutils import Quaternion, Vector
    data = data or load_pose(path)
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pb.location = (0.0, 0.0, 0.0)
        pb.scale = (1.0, 1.0, 1.0)
    for name, q in data["bones"].items():
        pb = rig.pose.bones.get(name)
        if pb is None:
            raise KeyError(f"{rig.name} has no bone {name!r}")
        pb.rotation_quaternion = Quaternion(q)
    rig.pose.bones[data["root_bone"]].location = Vector(data["root_location"])
    if TOE_SPRING_DEG:
        toe_spring(rig)
    bpy.context.view_layer.update()
    return data


def _proxy_mesh():
    import bpy
    verts, faces = [], []
    for _, x0, x1, hy, z0, z1, dx in PROXY_BOXES:
        b = len(verts)
        for z, sx in ((z0, dx), (z1, 0.0)):
            for x in (x0 + sx, x1 + sx):
                for y in (-hy, hy):
                    verts.append((x / 1000.0, y / 1000.0, z / 1000.0))
        # vertex order: bottom (x0,-y) (x0,+y) (x1,-y) (x1,+y), then the same on top
        faces += [(b + 0, b + 2, b + 3, b + 1), (b + 4, b + 5, b + 7, b + 6), (b + 0, b + 1, b + 5, b + 4),
                  (b + 2, b + 6, b + 7, b + 3), (b + 0, b + 4, b + 6, b + 2), (b + 1, b + 3, b + 7, b + 5)]
    me = bpy.data.meshes.get(PROXY) or bpy.data.meshes.new(PROXY)
    me.clear_geometry()
    me.from_pydata(verts, [], faces)
    me.update()
    return me


def add_carbine_proxy(rig, data=None):
    """Pose.Carbine.Frame (an empty, bone-parented to the stored hand bone at the solved matrix) and
    Pose.Carbine.Proxy (the block carbine, a child of the frame). The rig must already be posed."""
    import bpy
    from mathutils import Matrix
    data = data or load_pose()
    cf = data["carbine_frame"]
    coll = bpy.data.collections.get(COLL) or bpy.data.collections.new(COLL)
    if coll not in bpy.context.scene.collection.children_recursive:
        bpy.context.scene.collection.children.link(coll)
    for n in (PROXY, FRAME):
        ob = bpy.data.objects.get(n)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)
    frame = bpy.data.objects.new(FRAME, None)
    frame.empty_display_type, frame.empty_display_size = "ARROWS", 0.12
    coll.objects.link(frame)
    frame.parent = rig
    frame.parent_type = "BONE"
    frame.parent_bone = cf["parent_bone"]
    bpy.context.view_layer.update()
    frame.matrix_world = Matrix(cf["matrix_world"])
    proxy = bpy.data.objects.new(PROXY, _proxy_mesh())
    coll.objects.link(proxy)
    proxy.parent = frame
    proxy.matrix_parent_inverse = Matrix.Identity(4)
    proxy.matrix_basis = Matrix.Identity(4)
    m = bpy.data.materials.get("Pose.Mat.Carbine.Proxy") or bpy.data.materials.new("Pose.Mat.Carbine.Proxy")
    m.diffuse_color = (0.05, 0.05, 0.05, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.5
    proxy.data.materials.clear()
    proxy.data.materials.append(m)
    bpy.context.view_layer.update()
    return frame, proxy


def check(rig, data):
    """Blender's posed bone heads against the solver's forward kinematics (mm)."""
    import numpy as np
    errs = {}
    for name, p in data["joints_world_mm"].items():
        if TOE_SPRING_DEG and name.startswith("toe") and not name.split(".")[0].endswith("-1"):
            continue                                    # the toes' spring is not the solver's
        pb = rig.pose.bones[name]
        h = np.array(rig.matrix_world @ pb.head) * 1000.0
        errs[name] = float(np.linalg.norm(h - np.array(p)))
    worst = max(errs, key=errs.get)
    return {"max_mm": round(errs[worst], 4), "worst_bone": worst, "mean_mm": round(float(np.mean(list(errs.values()))), 4)}


def run_export(force=False):
    """Round 2: refresh cache/stages/contact.npz (the real surfaces the solver keeps the hands, arms and carbine
    on and out of) by running pose_contact.py in its own Blender process. Not imported here, on purpose: the
    part scripts import this module (common.apply_hero_pose), and assemble.py counts every module they import
    as an input of every part."""
    sys.path.insert(0, os.path.join(PROJECT, "scripts"))
    from lib import env
    args = ["-b", BASE_BLEND, "--python", os.path.join(HERE, "pose_contact.py"), "--", "--export"]
    cmd, environ = env.blender_cmd(args + ([] if force else ["--if-stale"]))
    r = subprocess.run(cmd, env=environ, cwd=PROJECT)
    if r.returncode:
        raise RuntimeError(f"contact export failed ({r.returncode})")


def run_solver():
    sys.path.insert(0, os.path.join(PROJECT, "scripts"))
    from lib import env
    py = os.environ.get("SGT_PYIMG") or env.load().get("pyimg")
    if not py:
        raise RuntimeError("no image Python (SGT_PYIMG or cache/env.json pyimg) to run pose_solve.py")
    if py.startswith("/") and os.name == "nt" and len(py) > 2 and py[2] == "/":   # Git Bash path /e/...
        py = py[1].upper() + ":" + py[2:]
    r = subprocess.run([py, "-I", os.path.join(HERE, "pose_solve.py")], cwd=PROJECT)
    if r.returncode:
        raise RuntimeError(f"pose_solve.py failed ({r.returncode})")


def main(argv):
    import bpy
    t0 = time.perf_counter()
    if "--solve" in argv:
        run_export(force="--export" in argv)
        run_solver()
        write_basis()
    rig = bpy.data.objects.get(RIG)
    if rig is None:
        raise RuntimeError(f"open {os.path.relpath(BASE_BLEND, PROJECT)} first: no {RIG}")
    data = apply_hero_pose(rig)
    add_carbine_proxy(rig, data)
    res = check(rig, data)
    res["seconds"] = round(time.perf_counter() - t0, 2)
    print("[pose] Blender vs solver joints:", json.dumps(res), flush=True)
    with open(CHECK_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    tmp = OUT_BLEND + ".tmp.blend"
    bpy.ops.wm.save_as_mainfile(filepath=tmp, copy=True, compress=False)
    os.replace(tmp, OUT_BLEND)
    if res["max_mm"] > 0.5:
        print(f"[pose] WARNING: Blender's pose differs from the solver's by {res['max_mm']} mm at {res['worst_bone']}")
        return 2
    return 0


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    try:
        rc = main(argv)
    except Exception:
        import traceback
        traceback.print_exc()
        rc = 1
    sys.stdout.flush()
    if rc:
        os._exit(rc)
