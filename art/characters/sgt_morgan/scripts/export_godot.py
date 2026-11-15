"""Export Sgt. Alex Morgan to one game-ready .glb for Godot, with a retargeted mocap walk and idle.

A FIRST LOOK, not the deliverable export (CLAUDE.md's glTF goal with baked textures stays open). See
scripts/export_godot.md for what is simplified and what is wrong.

Usage (from the project folder, after `source cache/env.sh`):

  "$SGT_BLENDER" -b --python scripts/export_godot.py -- [--stage all|mesh|anim] [--src cache/assembled.blend]
                 [--out ../../../game/characters/morgan/morgan.glb] [--budget 1.0] [--mesh cache/godot/morgan_mesh.blend]

  --src          the assembled .blend to read (a copy is fine: its relative image paths are re-resolved
                 against cache/, so a copy elsewhere does not bake the skin magenta)
  --mesh         the anim stage's input (the mesh stage's output by default)

  --stage mesh   cache/assembled.blend -> cache/godot/morgan_mesh.blend (rest pose, stripped, decimated,
                 baked, one mesh per part)
  --stage anim   cache/godot/morgan_mesh.blend -> retarget the CMU clips, write the .glb and
                 game/characters/morgan/morgan_motion.json
  --stage all    both (default)

It only READS cache/assembled.blend (built by scripts/assemble.py) and never writes into scripts/parts or
scripts/stages' outputs. Everything it makes goes to cache/godot/ and the game folder.

Mesh, per object of the assembled soldier, in the REST pose (Morgan.Rig pose_position = REST):
  - dropped: the scene (camera, lights, floor), the bare feet's nails and the socks (inside the boots),
    the MPFB eyebrow and eyelash cards (alpha cards; no alpha in this first look), meshes with no faces
    once their geometry-nodes modifier is gone (the boot stitches and tacks);
  - modifiers: Subdivision, Solidify, Bevel, Weighted Normal and Geometry Nodes are removed, Mask is
    applied, the Armature modifier is kept (skinning);
  - the carbine's objects (children of Carbine.Root, which is bone-parented to wrist.R) are skinned 100 % to
    wrist.R instead, so the glTF carries one skinned mesh; it stays where the rest-pose right hand puts it;
  - decimated (collapse) to a per-part triangle budget (PARTS below, times --budget);
  - one new UV map per part (Smart UV Project over all the part's objects together), and the part's own
    materials baked through it with Cycles into three textures: base colour, roughness and metallic
    (each BSDF in each node tree is swapped for an Emission of the input in question and baked as EMIT, so
    procedural prints, attribute masks, image textures and mix shaders all come through as colour);
    roughness and metallic are packed into one glTF metallicRoughness image (G, B);
  - one Principled material per part (double-sided, no normal map), all the part's objects joined into
    one mesh `Morgan.<Part>` skinned to Morgan.Rig.

Motion: the CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu; "free to use for any purpose",
including commercial games), in Bruce Hahne's MotionBuilder-friendly BVH conversion (each file's frame 1
is an added T-pose), mirrored at github.com/meshula/cmu-mocap. Downloaded into assets/mocap/cmu/ when
missing. Walk: 35_01 (subject 35, "walk"); idle: 77_02 ("standing"). Retarget by a bone map
(MAP below): for every mapped bone the source's world rotation change from its T-pose is applied to the
target bone after the target's rest (MPFB's A-pose) has been swung onto the source's T-pose bone
directions; twist bones, toes and the face follow their parents; the fingers take the hero pose's grip.
The walk is one gait cycle, in place (the hips' forward drift removed, their sway kept), looped by
spreading the end-to-start mismatch over the cycle; the feet are pinned to the ground every frame (the
lowest of each boot's heel and toe points at z = 0); the forward speed at which the planted foot stays
still is measured and written to morgan_motion.json for the game to move him at. Left/right are the
soldier's own.
"""
import json
import math
import os
import sys
import time
import urllib.request

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(SCRIPTS)
sys.path.insert(0, SCRIPTS)
from lib import env  # noqa: E402

CACHE = os.path.join(PROJECT, "cache", "godot")
MESH_BLEND = os.path.join(CACHE, "morgan_mesh.blend")
MOCAP = os.path.join(PROJECT, "assets", "mocap", "cmu")
HERO_JSON = os.path.join(SCRIPTS, "stages", "hero_pose.json")
DEFAULT_OUT = os.path.normpath(os.path.join(PROJECT, "..", "..", "..", "game", "characters", "morgan", "morgan.glb"))
CMU_URL = "https://raw.githubusercontent.com/meshula/cmu-mocap/master/data/{subject:03d}/{name}.bvh"

# part -> (collections it takes, texture size, triangle budget)
PARTS = {
    "Body": (["Body"], 2048, 16000),
    "Hair": (["Part.Head"], 512, 3000),
    "Trousers": (["Part.Trousers"], 2048, 12000),
    "Shirt": (["Part.Shirt"], 1024, 9000),
    "Boots": (["Part.Boots"], 1024, 10000),
    "Gloves": (["Part.Gloves"], 1024, 6000),
    "Carrier": (["Part.Carrier"], 1024, 14000),
    "Armour": (["Part.Armour"], 1024, 10000),
    "Belt": (["Part.Belt"], 1024, 8000),
    "Carbine": (["Part.Carbine"], 1024, 9000),
}
DROP_PREFIX = ("Scene.", "Foot.", "Sock.", "Body.Eyebrows", "Body.Eyelashes")
STRIP = {"SUBSURF", "SOLIDIFY", "BEVEL", "WEIGHTED_NORMAL", "NODES"}

FPS = 30
SRC_FPS = 120
WALK = ("35_01", 35)
IDLE = ("77_02", 77)
IDLE_SECONDS = 6.0

# target bone -> (its direction end: a bone whose head ends the segment, or TAIL; None = no alignment),
# source joint, source end. The trunk, neck and head are not aligned: both rests stand upright there and
# the two skeletons put those joints at different anatomical points (CMU's Neck sits on Spine1), so
# matching segment directions bent him forward; the limbs are aligned (A-pose arms onto T-pose arms,
# MPFB's slightly bent rest legs onto straight ones).
MAP = {
    "root": (None, "Hips", None),
    "spine05": (None, "LowerBack", None),
    "spine03": (None, "Spine", None),
    "spine02": (None, "Spine1", None),
    "neck01": (None, "Neck", None),
    "neck02": (None, "Neck1", None),
    "head": (None, "Head", None),
}
for s, S in (("L", "Left"), ("R", "Right")):
    MAP.update({
        f"clavicle.{s}": (f"upperarm01.{s}", f"{S}Shoulder", f"{S}Arm"),
        f"upperarm01.{s}": (f"lowerarm01.{s}", f"{S}Arm", f"{S}ForeArm"),
        f"lowerarm01.{s}": (f"wrist.{s}", f"{S}ForeArm", f"{S}Hand"),
        f"wrist.{s}": (f"finger3-1.{s}", f"{S}Hand", f"{S}HandIndex1"),
        f"upperleg01.{s}": (f"lowerleg01.{s}", f"{S}UpLeg", f"{S}Leg"),
        f"lowerleg01.{s}": (f"foot.{s}", f"{S}Leg", f"{S}Foot"),
        f"foot.{s}": (f"toe3-1.{s}", f"{S}Foot", f"{S}ToeBase"),
    })


def say(*a):
    print("[export_godot]", *a, flush=True)


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = {"stage": "all", "src": os.path.join(PROJECT, "cache", "assembled.blend"), "out": DEFAULT_OUT, "budget": 1.0, "mesh": MESH_BLEND}
    i = 0
    while i < len(argv):
        k = argv[i].lstrip("-")
        o[k] = argv[i + 1]
        i += 2
    o["budget"] = float(o["budget"])
    return o


def override(objs, active):
    return bpy.context.temp_override(selected_objects=objs, selected_editable_objects=objs, active_object=active,
                                     object=active)


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


# =========================================================================================== mesh stage

def prepare(src):
    bpy.ops.wm.open_mainfile(filepath=src)
    # A copy of the .blend outside cache/ breaks its relative image paths (the MPFB skin, some library
    # maps), and a missing image bakes magenta: resolve them against cache/ as well.
    for im in bpy.data.images:
        if im.source == "FILE" and im.packed_file is None and im.filepath.startswith("//") \
                and not os.path.exists(bpy.path.abspath(im.filepath)):
            alt = os.path.join(PROJECT, "cache", im.filepath[2:].replace("\\", os.sep))
            if os.path.exists(alt):
                im.filepath = alt
                im.reload()
            else:
                say(f"image missing: {im.name} ({im.filepath})")
    rig = bpy.data.objects["Morgan.Rig"]
    rig.animation_data_clear()
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    rig.data.pose_position = "REST"
    bpy.context.view_layer.update()

    def unhide(lc):
        lc.exclude = False
        lc.hide_viewport = False
        for c in lc.children:
            unhide(c)
    unhide(bpy.context.view_layer.layer_collection)
    for c in bpy.data.collections:
        c.hide_viewport = False
    for o in bpy.data.objects:
        o.hide_viewport = False
        o.hide_set(False)
        if o.type == "MESH" and o.data.users > 1:
            o.data = o.data.copy()
    for o in list(bpy.data.objects):
        if o.name.startswith(DROP_PREFIX) or o.type in {"CAMERA", "LIGHT"} or (o.type == "MESH" and o.hide_render):
            bpy.data.objects.remove(o, do_unlink=True)

    # the carbine: skin each mesh 100 % to wrist.R where the rest-pose hand carries it
    for o in [o for o in bpy.data.objects if o.name.startswith("Carbine.")]:
        if o.type != "MESH":
            continue
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
        vg = o.vertex_groups.new(name="wrist.R")
        vg.add(range(len(o.data.vertices)), 1.0, "REPLACE")
        m = o.modifiers.new("Armature", "ARMATURE")
        m.object = rig
        o.modifiers.move(len(o.modifiers) - 1, 0)
        o.parent = rig
        o.matrix_parent_inverse = rig.matrix_world.inverted()
        o.matrix_world = mw
    for o in [o for o in bpy.data.objects if o.type == "EMPTY"]:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()

    # modifiers: strip, apply what is left besides the armature
    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        for m in list(o.modifiers):
            if m.type in STRIP:
                o.modifiers.remove(m)
        if o.data.shape_keys:
            with override([o], o):
                bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
        for m in list(o.modifiers):
            if m.type != "ARMATURE":
                with override([o], o):
                    bpy.ops.object.modifier_apply(modifier=m.name)
        if not any(m.type == "ARMATURE" for m in o.modifiers):
            m = o.modifiers.new("Armature", "ARMATURE")
            m.object = rig
        for m in o.modifiers:
            if m.type == "ARMATURE":
                m.object = rig
        if len(o.data.polygons) == 0:
            bpy.data.objects.remove(o, do_unlink=True)
    return rig


def part_objects():
    groups = {}
    for part, (colls, _, _) in PARTS.items():
        objs = []
        for cn in colls:
            c = bpy.data.collections.get(cn)
            if c:
                objs += [o for o in c.all_objects if o.type == "MESH" and o.name in bpy.data.objects]
        groups[part] = sorted(set(objs), key=lambda o: o.name)
    return groups


def decimate(groups, budget):
    report = {}
    for part, objs in groups.items():
        before = sum(tris(o) for o in objs)
        target = PARTS[part][2] * budget
        ratio = min(1.0, target / max(before, 1))
        if ratio < 0.999:
            for o in objs:
                if tris(o) < 300:
                    continue
                m = o.modifiers.new("Decimate", "DECIMATE")
                m.decimate_type = "COLLAPSE"
                m.ratio = ratio
                m.use_collapse_triangulate = True
                with override([o], o):
                    bpy.ops.object.modifier_apply(modifier=m.name)
        after = sum(tris(o) for o in objs)
        report[part] = {"objects": len(objs), "tris_before": before, "tris_after": after}
        say(f"{part}: {len(objs)} objects, {before} -> {after} triangles")
    return report


def unwrap(objs):
    for o in objs:
        uv = o.data.uv_layers
        render = next((l.name for l in uv if l.active_render), None)
        bake = uv.new(name="Bake")
        uv.active = bake
        if render:
            uv[render].active_render = True
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")


BSDF_INPUTS = {  # node type -> (base colour, roughness, metallic) input names or constants
    "BSDF_PRINCIPLED": ("Base Color", "Roughness", "Metallic"),
    "BSDF_DIFFUSE": ("Color", 1.0, 0.0),
    "BSDF_GLOSSY": ("Color", "Roughness", 1.0),
    "BSDF_ANISOTROPIC": ("Color", "Roughness", 1.0),
    "BSDF_HAIR_PRINCIPLED": ("Color", "Roughness", 0.0),
    "BSDF_HAIR": ("Color", 0.6, 0.0),
    "SUBSURFACE_SCATTERING": ("Color", 0.5, 0.0),
    "BSDF_TRANSLUCENT": ("Color", 0.8, 0.0),
    "BSDF_SHEEN": ("Color", 0.9, 0.0),
    "BSDF_TRANSPARENT": ("Color", 0.5, 0.0),
    "BSDF_REFRACTION": ("Color", "Roughness", 0.0),
    "BSDF_GLASS": ("Color", "Roughness", 0.0),
    "EMISSION": ("Color", 1.0, 0.0),
}
CHANNELS = ("base", "rough", "metal")


def channel_copy(mat, ch, target, notes):
    """A copy of mat whose every BSDF is an Emission of channel ch, with an active image node on target."""
    m = mat.copy()
    m.name = f"{mat.name}.__{ch}"
    nt = m.node_tree
    found = rewire(nt, ch)
    for n in nt.nodes:
        if n.type == "OUTPUT_MATERIAL":
            for l in list(n.inputs["Displacement"].links):
                nt.links.remove(l)
    if found == 0:
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        v = {"base": tuple(mat.diffuse_color)[:3], "rough": (mat.roughness,) * 3, "metal": (mat.metallic,) * 3}[ch]
        em.inputs["Color"].default_value = (*v, 1.0)
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        notes.append(f"{mat.name}: no BSDF found; flat {ch} from the viewport settings")
    img = nt.nodes.new("ShaderNodeTexImage")
    img.image = target
    img.interpolation = "Closest"
    for n in nt.nodes:
        n.select = False
    img.select = True
    nt.nodes.active = img
    return m


def _has_bsdf(tree, seen=None):
    seen = seen or set()
    if tree is None or tree.name in seen:
        return False
    seen.add(tree.name)
    return any(n.type in BSDF_INPUTS or (n.type == "GROUP" and _has_bsdf(n.node_tree, seen)) for n in tree.nodes)


def rewire(nt, ch):
    """Swap every BSDF in a node tree (and in copies of the node groups that hold one) for an Emission of
    channel ch's input. Returns how many were swapped."""
    found = 0
    for n in list(nt.nodes):
        if n.type == "GROUP" and _has_bsdf(n.node_tree):
            g = n.node_tree.copy()
            g.name = f"{n.node_tree.name}.__{ch}"
            found += rewire(g, ch)
            n.node_tree = g
    for n in list(nt.nodes):
        spec = BSDF_INPUTS.get(n.type)
        if spec is None:
            continue
        found += 1
        what = spec[CHANNELS.index(ch)]
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 1.0
        sock = n.inputs.get(what) if isinstance(what, str) else None
        if sock is not None and sock.is_linked:
            nt.links.new(sock.links[0].from_socket, em.inputs["Color"])
        else:
            v = sock.default_value if sock is not None else what
            try:
                c = tuple(v)[:3]
            except TypeError:
                c = (float(v),) * 3
            em.inputs["Color"].default_value = (*c, 1.0)
        for l in list(n.outputs[0].links):
            nt.links.new(em.outputs[0], l.to_socket)
        nt.nodes.remove(n)
    return found


def bake_part(part, objs, size, notes):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    dev = env.use_device(scene)
    scene.cycles.samples = 4
    scene.cycles.use_denoising = False
    scene.render.bake.margin = 6
    scene.render.bake.use_clear = False
    originals = {o.name: [s.material for s in o.material_slots] for o in objs}
    images = {}
    for ch in CHANNELS:
        img = bpy.data.images.new(f"Morgan.{part}.{ch}", size, size, alpha=False, float_buffer=False)
        img.generated_color = {"base": (0.5, 0.5, 0.5, 1), "rough": (0.7, 0.7, 0.7, 1), "metal": (0, 0, 0, 1)}[ch]
        if ch != "base":
            img.colorspace_settings.name = "Non-Color"
        copies = {}
        for o in objs:
            if not o.material_slots:
                o.data.materials.append(bpy.data.materials.new(f"{o.name}.Plain"))
                originals[o.name] = [o.material_slots[0].material]
            for i, s in enumerate(o.material_slots):
                src = originals[o.name][i] or bpy.data.materials.new(f"{o.name}.Plain{i}")
                if not src.use_nodes:
                    src.use_nodes = True
                if src.name not in copies:
                    copies[src.name] = channel_copy(src, ch, img, notes if ch == "base" else [])
                s.material = copies[src.name]
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        t0 = time.time()
        bpy.ops.object.bake(type="EMIT", margin=6, use_clear=False)
        say(f"  baked {part} {ch} {size}px on {dev} in {time.time() - t0:.1f}s")
        img.pack()
        images[ch] = img
        for c in copies.values():
            bpy.data.materials.remove(c)
    # pack roughness (G) and metallic (B) into one metallicRoughness image
    orm = bpy.data.images.new(f"Morgan.{part}.orm", size, size, alpha=False)
    orm.colorspace_settings.name = "Non-Color"
    px = np.empty(size * size * 4, dtype=np.float32)
    images["rough"].pixels.foreach_get(px)
    rough = px.reshape(-1, 4)[:, 0].copy()
    images["metal"].pixels.foreach_get(px)
    metal = px.reshape(-1, 4)[:, 0].copy()
    out = np.ones((size * size, 4), dtype=np.float32)
    out[:, 1], out[:, 2] = rough, metal
    orm.pixels.foreach_set(out.ravel())
    orm.pack()
    base = images["base"]
    stats = {"base_mean_srgb": [round(float(x), 3) for x in _mean(base)], "rough_mean": round(float(rough.mean()), 3),
             "metal_mean": round(float(metal.mean()), 3)}
    bpy.data.images.remove(images["rough"])
    bpy.data.images.remove(images["metal"])
    return base, orm, stats


def _mean(img):
    px = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(-1, 4)[:, :3].mean(axis=0)


def game_material(part, base, orm):
    m = bpy.data.materials.new(f"Morgan.{part}")
    m.use_nodes = True
    m.use_backface_culling = False
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    tb = nt.nodes.new("ShaderNodeTexImage")
    tb.image = base
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = orm
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(uv.outputs[0], tb.inputs["Vector"])
    nt.links.new(uv.outputs[0], to.inputs["Vector"])
    nt.links.new(tb.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(to.outputs["Color"], sep.inputs[0])
    nt.links.new(sep.outputs[1], bsdf.inputs["Roughness"])
    nt.links.new(sep.outputs[2], bsdf.inputs["Metallic"])
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return m


def join_part(part, objs, mat, rig):
    for o in objs:
        uv = o.data.uv_layers
        for l in [l for l in uv if l.name != "Bake"]:
            uv.remove(l)
        uv["Bake"].name = "UVMap"
        o.data.materials.clear()
        o.data.materials.append(mat)
    active = objs[0]
    if len(objs) > 1:
        with override(objs, active):
            bpy.ops.object.join()
    active.name = active.data.name = f"Morgan.{part}"
    for m in active.modifiers:
        if m.type == "ARMATURE":
            m.object = rig
    return active


def mesh_stage(src, budget):
    os.makedirs(CACHE, exist_ok=True)
    t0 = time.time()
    rig = prepare(src)
    groups = part_objects()
    leftover = [o.name for o in bpy.data.objects if o.type == "MESH" and not any(o in g for g in groups.values())]
    for n in leftover:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    report = {"source": src, "dropped_unassigned": leftover, "parts": decimate(groups, budget)}
    notes = []
    for part, objs in groups.items():
        if not objs:
            continue
        unwrap(objs)
        base, orm, stats = bake_part(part, objs, PARTS[part][1], notes)
        report["parts"][part].update(stats, texture=PARTS[part][1])
        join_part(part, objs, game_material(part, base, orm), rig)
    for m in list(bpy.data.materials):
        if not m.name.startswith("Morgan.") and m.users == 0:
            bpy.data.materials.remove(m)
    report["material_notes"] = sorted(set(notes))
    report["total_tris"] = sum(tris(o) for o in bpy.data.objects if o.type == "MESH")
    report["seconds"] = round(time.time() - t0, 1)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.ops.wm.save_as_mainfile(filepath=MESH_BLEND, compress=True)
    json.dump(report, open(os.path.join(CACHE, "mesh_report.json"), "w"), indent=1)
    say(f"mesh stage: {report['total_tris']} triangles, {report['seconds']} s -> {MESH_BLEND}")


# =========================================================================================== anim stage

def fetch(name, subject):
    os.makedirs(MOCAP, exist_ok=True)
    path = os.path.join(MOCAP, f"{name}.bvh")
    if not os.path.exists(path):
        url = CMU_URL.format(subject=subject, name=name)
        say(f"downloading {url}")
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read()
        if not data.startswith(b"HIERARCHY"):
            raise RuntimeError(f"{url} is not a BVH file")
        open(path, "wb").write(data)
    return path


def load_bvh(path):
    before = set(bpy.data.objects)
    bpy.ops.import_anim.bvh(filepath=path, target="ARMATURE", global_scale=1.0, frame_start=1, use_fps_scale=False,
                            update_scene_fps=False, update_scene_duration=False, use_cyclic=False,
                            rotate_mode="NATIVE", axis_forward="-Z", axis_up="Y")
    src = next(o for o in bpy.data.objects if o not in before)
    act = src.animation_data.action
    last = int(max(k.co[0] for fc in _fcurves(act) for k in fc.keyframe_points))
    return src, last


def _fcurves(act):
    if hasattr(act, "fcurves") and len(act.fcurves):
        return act.fcurves
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out += list(bag.fcurves)
    return out


def sample_source(src, frames):
    """World rotations (3x3) and joint heads of every source bone at each frame (scene frame numbers)."""
    names = [b.name for b in src.data.bones]
    rots = {n: [] for n in names}
    pos = {n: [] for n in names}
    tails = {n: [] for n in names}
    sc = bpy.context.scene
    for f in frames:
        sc.frame_set(int(f))
        mw = src.matrix_world
        for n in names:
            pb = src.pose.bones[n]
            m = mw @ pb.matrix
            rots[n].append(m.to_3x3().normalized())
            pos[n].append(mw @ pb.head)
            tails[n].append(mw @ pb.tail)
    return rots, pos, tails


def facing_of(pos, i):
    left = pos["LeftUpLeg"][i] - pos["RightUpLeg"][i]
    left.z = 0
    fwd = left.normalized().cross(Vector((0, 0, 1)))
    return fwd


def heading_rotation(src_dir, dst=Vector((0, -1, 0))):
    a = math.atan2(src_dir.y, src_dir.x)
    b = math.atan2(dst.y, dst.x)
    return Matrix.Rotation(b - a, 3, "Z")


class Target:
    def __init__(self, rig):
        self.rig = rig
        self.bones = rig.data.bones
        self.order = []

        def walk(b):
            self.order.append(b.name)
            for c in b.children:
                walk(c)
        for b in self.bones:
            if b.parent is None:
                walk(b)
        self.rest = {b.name: b.matrix_local.copy() for b in self.bones}
        self.rel = {b.name: (self.rest[b.parent.name].inverted() @ self.rest[b.name]) if b.parent else self.rest[b.name]
                    for b in self.bones}

    def head(self, n):
        return self.rest[n].translation.copy()

    def tail(self, n):
        return self.bones[n].tail_local.copy()

    def fk(self, basis):
        """Armature-space posed matrices for every bone given {name: basis 4x4} (missing = identity)."""
        posed = {}
        for n in self.order:
            b = self.bones[n]
            B = basis.get(n, Matrix.Identity(4))
            posed[n] = (posed[b.parent.name] @ self.rel[n] @ B) if b.parent else (self.rel[n] @ B)
        return posed


def retarget(tgt, src, s_frames, hero_fingers, travel_dir=None):
    """Bake the source frames onto the target: returns a list of {bone: basis 4x4} and per-frame root positions."""
    rots, pos, tails = sample_source(src, [1] + list(s_frames))
    # index 0 is the T-pose (frame 1)
    up = Vector((0, 0, 1))
    f_rest = facing_of(pos, 0)
    G_rest = heading_rotation(f_rest)
    if travel_dir is None:
        fw = Vector((0, 0, 0))
        for i in range(1, len(s_frames) + 1):
            fw += facing_of(pos, i)
        travel_dir = fw.normalized()
    G_walk = heading_rotation(travel_dir)

    def src_end(n, end, i):
        return (tails[n][i] if end == "TAIL" else pos[end][i])

    aligned = {}
    for t, (tend, s, send) in MAP.items():
        T_rest = tgt.rest[t].to_3x3()
        if tend is None:
            aligned[t] = T_rest
            continue
        d_t = ((tgt.tail(t) if tend == "TAIL" else tgt.head(tend)) - tgt.head(t)).normalized()
        seg = G_rest @ (src_end(s, send, 0) - pos[s][0])
        if seg.length < 1e-6:
            raise RuntimeError(f"source segment {s} -> {send} has no length; map it to another end joint")
        d_s = seg.normalized()
        C = d_t.rotation_difference(d_s).to_matrix()
        aligned[t] = C @ T_rest
    S_rest_inv = {s: rots[s][0].inverted() for (_, s, _) in MAP.values()}

    # scale from leg lengths
    def leglen_src(i):
        return (pos["LeftUpLeg"][i] - pos["LeftLeg"][i]).length + (pos["LeftLeg"][i] - pos["LeftFoot"][i]).length
    leg_t = (tgt.head("upperleg01.L") - tgt.head("lowerleg01.L")).length + \
        (tgt.head("lowerleg01.L") - tgt.head("foot.L")).length
    scale = leg_t / leglen_src(0)

    frames = []
    hips0 = pos["Hips"][0]
    root_rest = tgt.head("root")
    for i in range(1, len(s_frames) + 1):
        world = {}
        for t, (_, s, _) in MAP.items():
            world[t] = G_walk @ rots[s][i] @ S_rest_inv[s] @ G_rest.inverted() @ aligned[t]
        root_pos = root_rest + scale * (G_walk @ (pos["Hips"][i] - hips0))
        basis = {}
        posed = {}
        for n in tgt.order:
            b = tgt.bones[n]
            if n in hero_fingers:
                basis[n] = hero_fingers[n].to_matrix().to_4x4()
            if n in world:
                if b.parent is None:
                    P = Matrix.Translation(root_pos) @ world[n].to_4x4()
                    basis[n] = tgt.rel[n].inverted() @ P
                else:
                    loc = (posed[b.parent.name] @ tgt.rel[n]).translation
                    P = Matrix.Translation(loc) @ world[n].to_4x4()
                    basis[n] = tgt.rel[n].inverted() @ posed[b.parent.name].inverted() @ P
            B = basis.get(n, Matrix.Identity(4))
            posed[n] = (posed[b.parent.name] @ tgt.rel[n] @ B) if b.parent else (tgt.rel[n] @ B)
        frames.append(basis)
    return frames, scale, G_walk


def contact_points(tgt, boots):
    """Each boot's heel and toe sole points, in its foot bone's rest frame."""
    me = boots.data
    co = np.array([v.co for v in me.vertices]) @ np.array(boots.matrix_world.to_3x3()).T + np.array(boots.matrix_world.translation)
    pts = {}
    for side, sign in (("L", 1), ("R", -1)):
        sel = co[co[:, 0] * sign > 0.02]
        zmin = sel[:, 2].min()
        sole = sel[sel[:, 2] < zmin + 0.012]
        heel = sole[sole[:, 1].argmax()]
        toe = sole[sole[:, 1].argmin()]
        inv = tgt.rest[f"foot.{side}"].inverted()
        pts[side] = [inv @ Vector(heel), inv @ Vector(toe)]
        say(f"boot {side}: sole z {zmin * 1000:.1f} mm, heel {Vector(heel)}, toe {Vector(toe)}")
    return pts, float(min(co[:, 2]))


def ground(tgt, frames, pts):
    """Pin the lowest sole point to z = 0 each frame; returns contact info per frame."""
    info = []
    for basis in frames:
        posed = tgt.fk(basis)
        world = {s: [posed[f"foot.{s}"] @ p for p in pts[s]] for s in pts}
        low = min(p.z for s in world for p in world[s])
        r = basis["root"]
        P = tgt.rel["root"] @ r
        P = Matrix.Translation((0, 0, -low)) @ P
        basis["root"] = tgt.rel["root"].inverted() @ P
        for s in world:
            for p in world[s]:
                p.z -= low
        info.append(world)
    return info


def contacts(tgt, basis, pts):
    posed = tgt.fk(basis)
    return {s: [posed[f"foot.{s}"] @ p for p in pts[s]] for s in pts}


def leg_lift(tgt, basis, side, dz):
    """Two-bone IK: move the ankle of one leg up by dz (m), keeping the knee's bend plane and the foot's
    orientation; rewrites the basis of upperleg01, lowerleg01 and foot."""
    posed = tgt.fk(basis)
    ul, ll, ft = f"upperleg01.{side}", f"lowerleg01.{side}", f"foot.{side}"
    H, K, A = posed[ul].translation, posed[ll].translation, posed[ft].translation
    T = A + Vector((0, 0, dz))
    l1, l2 = (K - H).length, (A - K).length
    d = min((T - H).length, l1 + l2 - 1e-4)
    u = (T - H).normalized()
    T = H + u * d
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    w = (K - H) - u * (K - H).dot(u)
    if w.length < 1e-6:
        return
    K2 = H + u * a + w.normalized() * h

    def about(p, R):
        return Matrix.Translation(p) @ R.to_4x4() @ Matrix.Translation(-p)
    R1 = (K - H).rotation_difference(K2 - H).to_matrix()
    M1 = about(H, R1)
    Mth = M1 @ posed[ul]
    Msh = M1 @ posed[ll]
    A1 = M1 @ A
    R2 = (A1 - K2).rotation_difference(T - K2).to_matrix()
    Msh = about(K2, R2) @ Msh
    Mft = Matrix.Translation(T) @ posed[ft].to_3x3().to_4x4()
    bones = tgt.bones
    I = Matrix.Identity(4)
    basis[ul] = tgt.rel[ul].inverted() @ posed[bones[ul].parent.name].inverted() @ Mth
    # the twist bones between thigh and shin and between shin and foot keep their basis
    mid = bones[ll].parent.name
    posed_mid = Mth @ tgt.rel[mid] @ basis.get(mid, I) if bones[mid].parent.name == ul else None
    if posed_mid is None:
        return
    basis[ll] = tgt.rel[ll].inverted() @ posed_mid.inverted() @ Msh
    mid2 = bones[ft].parent.name
    if bones[mid2].parent.name != ll:
        return
    posed_mid2 = Msh @ tgt.rel[mid2] @ basis.get(mid2, I)
    basis[ft] = tgt.rel[ft].inverted() @ posed_mid2.inverted() @ Mft


def clean_feet(tgt, frames, pts, v, fps=FPS, near=0.04, fast=0.35, clearance=0.012):
    """For a looped, in-place walk moving at v: pin the ground to the sole point that is still (the
    slowest of those within `near` of the lowest) rather than to the lowest, smooth that over three frames,
    then lift any sole point that is moving faster than `fast` m/s but lower than `clearance` with leg IK,
    so a foot that arrives early skims in rather than skating on the ground. frames[-1] == frames[0]."""
    N = len(frames) - 1

    def world(P, k, s, j):
        p = P[k % N][s][j]
        return Vector((p.x, p.y - v * k / fps, p.z))

    def speeds(P):
        sp = []
        for k in range(N):
            sp.append({s: [((world(P, k + 1, s, j) - world(P, k - 1, s, j)).xy.length * fps / 2) for j in range(2)]
                       for s in pts})
        return sp
    P = [contacts(tgt, frames[k], pts) for k in range(N)]
    sp = speeds(P)
    dz = []
    for k in range(N):
        cand = [(P[k][s][j].z, sp[k][s][j]) for s in pts for j in range(2)]
        low = min(z for z, _ in cand)
        z_support = min((c for c in cand if c[0] <= low + near), key=lambda c: c[1])[0]
        dz.append(-z_support)
    dz = [(dz[(k - 1) % N] + 2 * dz[k] + dz[(k + 1) % N]) / 4 for k in range(N)]
    R = tgt.rel["root"]
    for k in range(N):
        frames[k]["root"] = R.inverted() @ Matrix.Translation((0, 0, dz[k])) @ R @ frames[k]["root"]
    P = [contacts(tgt, frames[k], pts) for k in range(N)]
    sp = speeds(P)
    lifted = 0
    for k in range(N):
        for s in pts:
            low = [P[k][s][j].z for j in range(2) if sp[k][s][j] > fast]
            if low and min(low) < clearance:
                leg_lift(tgt, frames[k], s, clearance - min(low))
                lifted += 1
    frames[N] = {n: B.copy() for n, B in frames[0].items()}
    say(f"  feet: ground pinned to the still sole point, {lifted} foot-frames lifted clear")
    return [contacts(tgt, frames[k], pts) for k in range(N + 1)]


def make_loop(frames, n_blend=None):
    """Spread the mismatch between frame N (a copy of the next cycle's start) and frame 0 over the cycle,
    and remove the root's linear horizontal drift. frames has N+1 entries; returns N+1 with last == first."""
    N = len(frames) - 1
    first, last = frames[0], frames[N]
    out = []
    drift = last["root"].translation - first["root"].translation
    for k, basis in enumerate(frames):
        u = k / N
        nb = {}
        for n, B in basis.items():
            q = B.to_quaternion()
            if n in first and n in last:
                d = last[n].to_quaternion() @ first[n].to_quaternion().inverted()
                q = Quaternion((1, 0, 0, 0)).slerp(d.inverted(), u) @ q
            t = B.translation.copy()
            if n == "root":
                t = t - drift * u
            nb[n] = Matrix.Translation(t) @ q.to_matrix().to_4x4()
        out.append(nb)
    out[N] = {n: B.copy() for n, B in out[0].items()}
    return out, drift


def center_root(tgt, frames):
    """In place: the hips' sway stays, their mean horizontal offset from the rest position goes."""
    R = tgt.rel["root"]
    arm = [(R @ f["root"]).translation for f in frames]
    mean = sum(arm, Vector()) / len(arm) - tgt.head("root")
    for basis in frames:
        P = Matrix.Translation((-mean.x, -mean.y, 0)) @ R @ basis["root"]
        basis["root"] = R.inverted() @ P


def gait_cycle(src, last):
    """Two successive plants of the left foot (its speed drops under a threshold) at 120 fps."""
    frames = list(range(2, last + 1))
    _, pos, _ = sample_source(src, frames)
    # The ankle's speed is too noisy at 120 fps to threshold; its height is not: a plant is where the
    # left ankle comes down through a quarter of its swing height.
    p = np.array([[v.x, v.y, v.z] for v in pos["LeftFoot"]])
    hips = np.array([[v.x, v.y] for v in pos["Hips"]])
    v_hips = np.linalg.norm(hips[-1] - hips[0]) / (len(frames) / SRC_FPS)
    z = p[:, 2]
    thr = z.min() + 0.25 * (z.max() - z.min())
    starts = [i for i in range(1, len(z)) if z[i] <= thr < z[i - 1]]
    # skip the start-up: take the last two plants that are a full cycle apart
    best = None
    for a, b in zip(starts, starts[1:]):
        if 0.7 * SRC_FPS < b - a < 1.6 * SRC_FPS:
            best = (a, b)
    if best is None:
        raise RuntimeError(f"no gait cycle found in the walk; plants at {starts}")
    a, b = best
    travel = Vector((hips[-1][0] - hips[0][0], hips[-1][1] - hips[0][1], 0)).normalized()
    return frames[a], frames[b], travel, v_hips


def quiet_window(src, last, seconds):
    """The idle window (seconds long) where the hips move least and the ends match best."""
    step = SRC_FPS // FPS
    frames = list(range(2, last + 1, step))
    rots, pos, _ = sample_source(src, frames)
    hips = np.array([[v.x, v.y, v.z] for v in pos["Hips"]])
    n = int(seconds * FPS)
    best, best_i = 1e9, 0
    for i in range(0, len(frames) - n - 1, 3):
        seg = hips[i:i + n + 1]
        wander = np.ptp(seg[:, 0]) + np.ptp(seg[:, 1])
        ends = np.linalg.norm(seg[-1] - seg[0])
        ang = sum(rots[j][i].to_quaternion().rotation_difference(rots[j][i + n].to_quaternion()).angle
                  for j in ("Hips", "Spine1", "Head", "LeftArm", "RightArm", "LeftUpLeg", "RightUpLeg"))
        score = wander + 2 * ends + 0.05 * ang
        if score < best:
            best, best_i = score, i
    return frames[best_i], frames[best_i + n], best


def key_action(rig, name, frames, bones):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = act
    prev = {}
    for k, basis in enumerate(frames):
        for n in bones:
            pb = rig.pose.bones[n]
            B = basis.get(n, Matrix.Identity(4))
            q = B.to_quaternion()
            if n in prev and prev[n].dot(q) < 0:
                q = -q
            prev[n] = q
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=k, group=n)
            if n == "root":
                pb.location = B.translation
                pb.keyframe_insert("location", frame=k, group=n)
    for fc in _fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    rig.animation_data.action = None
    track = rig.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, 0, act)
    track.mute = True
    return act


def slide_report(info, v, fps=FPS):
    """How far a sole point (each heel and toe on its own) slides on the ground while it is down, once the
    body travels forward at v (m/s): the worst and the mean over its contacts, metres."""
    runs = []
    for side in ("L", "R"):
        for j in range(2):
            run = []
            for k, w in enumerate(info + [None]):
                pt = w[side][j] if w is not None else None
                if pt is not None and pt.z < 0.01:
                    q = pt + Vector((0, -v * k / fps, 0))
                    run.append(Vector((q.x, q.y)))
                else:
                    if len(run) > 2:
                        runs.append(max((p - run[0]).length for p in run))
                    run = []
    return (max(runs), sum(runs) / len(runs)) if runs else (0.0, 0.0)


def planted_speed(info, fps=FPS):
    sp = []
    for side in ("L", "R"):
        for k in range(1, len(info)):
            a = min(info[k - 1][side], key=lambda p: p.z)
            b = min(info[k][side], key=lambda p: p.z)
            if a.z < 0.005 and b.z < 0.005:
                sp.append((b.y - a.y) * fps)  # in place, a planted foot slides back (+Y) as fast as he walks
    return float(np.median(sp)) if sp else 0.0


def anim_stage(out_path, mesh_blend=MESH_BLEND):
    bpy.ops.wm.open_mainfile(filepath=mesh_blend)
    rig = bpy.data.objects["Morgan.Rig"]
    rig.animation_data_clear()
    rig.data.pose_position = "POSE"
    tgt = Target(rig)
    hero = json.load(open(HERO_JSON))
    fingers = {n: Quaternion(q) for n, q in hero["bones"].items() if n.startswith(("finger", "metacarpal"))}
    pts, sole_z = contact_points(tgt, bpy.data.objects["Morgan.Boots"])
    keyed = sorted(set(MAP) | set(fingers))
    motion = {"source": "CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), BVH by B. Hahne via "
                        "github.com/meshula/cmu-mocap", "fps": FPS, "in_place": True}

    # walk
    src, last = load_bvh(fetch(*WALK))
    a, b, travel, v_src = gait_cycle(src, last)
    step = (b - a) / round((b - a) / (SRC_FPS / FPS))
    s_frames = [a + round(k * step) for k in range(round((b - a) / step) + 1)]
    frames, scale, _ = retarget(tgt, src, s_frames, fingers, travel_dir=travel)
    frames, drift = make_loop(frames)
    center_root(tgt, frames)
    info = ground(tgt, frames, pts)
    v = planted_speed(info)
    info = clean_feet(tgt, frames, pts, v)
    json.dump([{s: [[round(c, 4) for c in p] for p in w[s]] for s in w} for w in info],
              open(os.path.join(CACHE, "walk_contacts.json"), "w"))
    worst, mean = slide_report(info, v)
    say(f"walk {WALK[0]}: source frames {a}-{b} ({(b - a) / SRC_FPS:.2f} s), scale {scale:.3f}, "
        f"hips drift over the cycle {drift.length:.3f} m, planted-foot speed {v:.3f} m/s, "
        f"slide worst {worst * 100:.1f} cm mean {mean * 100:.1f} cm")
    key_action(rig, "Walk", frames, keyed)
    motion["walk"] = {"clip": WALK[0], "source_frames_120fps": [a, b], "frames": len(frames) - 1,
                      "seconds": (len(frames) - 1) / FPS, "speed_mps": round(v, 4),
                      "hips_drift_speed_mps": round(drift.length / ((len(frames) - 1) / FPS), 4),
                      "slide_cm_worst": round(worst * 100, 1), "slide_cm_mean": round(mean * 100, 1),
                      "scale": round(scale, 4)}
    src_action = src.animation_data.action
    bpy.data.objects.remove(src, do_unlink=True)
    bpy.data.actions.remove(src_action)

    # idle
    src, last = load_bvh(fetch(*IDLE))
    a, b, score = quiet_window(src, last, IDLE_SECONDS)
    s_frames = list(range(a, b + 1, SRC_FPS // FPS))
    frames, scale_i, _ = retarget(tgt, src, s_frames, fingers)
    frames, drift = make_loop(frames)
    # in place: the hips' sway stays, their mean horizontal offset from the rest goes (basis space of root)
    center_root(tgt, frames)
    ground(tgt, frames, pts)
    key_action(rig, "Idle", frames, keyed)
    say(f"idle {IDLE[0]}: source frames {a}-{b} ({(b - a) / SRC_FPS:.1f} s), score {score:.3f}")
    motion["idle"] = {"clip": IDLE[0], "source_frames_120fps": [a, b], "frames": len(frames) - 1,
                      "seconds": (len(frames) - 1) / FPS}
    src_action = src.animation_data.action
    bpy.data.objects.remove(src, do_unlink=True)
    bpy.data.actions.remove(src_action)

    # height in the rest pose, boots on: for the game's scale to the rules' standing man
    zs = [(o.matrix_world @ v.co).z for n in ("Morgan.Body", "Morgan.Hair") if (o := bpy.data.objects.get(n))
          for v in o.data.vertices]
    motion["rest_height_m"] = round(max(zs) - sole_z, 4)
    motion["rest_sole_z_m"] = round(sole_z, 4)

    # rest pose for export; the actions ride on muted NLA tracks
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.scene.frame_set(0)
    bpy.context.scene.render.fps = FPS
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.export_scene.gltf(
        filepath=out_path, export_format="GLB", use_selection=False, export_apply=False,
        export_texcoords=True, export_normals=True, export_tangents=False, export_materials="EXPORT",
        export_image_format="AUTO", export_yup=True, export_skins=True, export_all_influences=False,
        export_morph=False, export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
        export_frame_range=False, export_nla_strips=True, export_anim_single_armature=True,
        export_reset_pose_bones=True, export_rest_position_armature=True, export_def_bones=False,
        export_optimize_animation_size=False, export_cameras=False, export_lights=False)
    mesh_report = json.load(open(os.path.join(CACHE, "mesh_report.json")))
    motion["triangles"] = mesh_report["total_tris"]
    motion["glb_bytes"] = os.path.getsize(out_path)
    json.dump(motion, open(os.path.join(os.path.dirname(out_path), "morgan_motion.json"), "w"), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CACHE, "morgan_anim.blend"), compress=True)
    say(f"wrote {out_path} ({motion['glb_bytes'] / 1e6:.1f} MB), rest height {motion['rest_height_m']} m")


def main():
    o = args()
    if o["stage"] in ("all", "mesh"):
        mesh_stage(os.path.abspath(o["src"]), o["budget"])
    if o["stage"] in ("all", "anim"):
        anim_stage(os.path.abspath(o["out"]), os.path.abspath(o["mesh"]))


if __name__ == "__main__":
    main()
