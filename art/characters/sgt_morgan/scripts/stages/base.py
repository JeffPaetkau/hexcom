"""Round 0, stage 1: the base body (PLAN.md, "Round 0: the body and the pose").

An MPFB 2.0.17 male at the drawing's lean V-taper build, 40 years old, height macro fitted so the rest
stature (skull top to sole, barefoot) is 1835 mm, re-grounded on its lowest vertex and centred between
the ankle joint cubes, facing -Y with +X his left (CLAUDE.md rule 2); MPFB's `default` skeleton (163
bones) with MPFB's own weights; MPFB's middle-aged Caucasian male skin, toned; eyes, eyebrows and eyelashes (cheap
MHCLO assets); no hair, no clothes. Take 1's build_all.py stages S1 and S2 (archive/v1/scripts/
build_all.py) without part 01's foot targets.

  "$SGT_BLENDER" -b --python scripts/stages/base.py [-- --render]
  -> cache/stages/base.blend   objects Body.Mesh and Morgan.Rig (and Body.Eyes, Body.Eyebrows,
                               Body.Eyelashes) in collection Body
     cache/stages/base.json    stature, macros, targets, key girths and breadths, every bone's rest
                               head/tail/matrix (mm, rig space = world) and the landmarks pose.py fits

--render adds the body part's rest clay views (renders/body/body_rest_*.png, body_chest_rest_*.png).

Round 1 (scripts/parts/body.md, head.md): the chest, neck and limb targets of the body part; the face
targets that scripts/parts/head.py --fit writes to scripts/parts/head_fit.json; MPFB's skin material toned
to the reference; the eye, eyelash and eyebrow material fixes.

Idempotent: it starts from an empty file every time.
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

OUT_DIR = os.path.join(PROJECT, "cache", "stages")
OUT_BLEND = os.path.join(OUT_DIR, "base.blend")
OUT_JSON = os.path.join(OUT_DIR, "base.json")
BODY, RIG, COLL = "Body.Mesh", "Morgan.Rig", "Body"


def age_macro(years):
    """MakeHuman's age macro: 0 = 1 y, 0.1875 = 11 y, 0.5 = 25 y, 1 = 90 y (piecewise linear)."""
    return 0.5 * (years - 1.0) / 24.0 if years <= 25.0 else 0.5 + 0.5 * (years - 25.0) / 65.0


# Take 1's macros (specs 03/04 §4.1): a lean, muscular 40-year-old man.
MACRO = {"gender": 1.0, "age": round(age_macro(40.0), 6), "muscle": 0.70, "weight": 0.45, "proportions": 0.5,
         "cupsize": 0.5, "firmness": 0.5, "race": {"caucasian": 1.0, "asian": 0.0, "african": 0.0}}
# The drawing's V-taper (bare bideltoid ~ 60 cm, hips 35 cm, waist:hip 0.88) and real arm segments.
# MPFB's default male puts the elbow 268 mm below the shoulder joint (ANSUR ~ 330-340); the upper-arm
# length target restores most of it. Values chosen by measuring (base.json "measure") against
# analysis_pose_proportions.md §4 and research_dimensions.md, not by eye. None of the targets below the
# first five moves a joint cube (checked: 0.0 mm), so the hero pose's joints are those of round 0.
BODY_TARGETS = {
    "torso-vshape-incr": 0.50,
    "measure-shoulder-dist-incr": 0.20,
    "hip-scale-horiz-decr": 0.15,
    "measure-waist-circ-decr": 0.10,
    "measure-upperarm-length-incr": 1.00,
    # Round 1 (body part, scripts/parts/body.md): a lean, fit man's chest instead of MPFB's soft rounded
    # mound. The pectoral muscle carries the shape (0.3 -> 0.7), its mass moves up (breast-trans-up), the
    # breast fullness and the nipples go (bust-circ-decr, nipple size/point), and the lats (dorsi) put the
    # girth back: chest girth 990 against round 0's 993, with a 15 mm step at the pectoral's lower edge.
    "torso-muscle-pectoral-incr": 0.70,
    "breast-trans-up": 0.50,
    "measure-bust-circ-decr": 0.30,
    "nipple-size-decr": 0.60,
    "nipple-point-decr": 0.30,
    "torso-muscle-dorsi-incr": 0.50,
    # The neck (tape square to the neck axis under the larynx, measure()): round 0 read 405 with 0.3; the
    # fitted face widens the upper neck by about 15 mm on its own, so 0.1 gives 409 (ANSUR II mean about 397,
    # a muscular neck a little over). Arms (upper arm 318 -> 338, forearm
    # 247 -> 275: round 0's forearm was below ANSUR's 5th percentile) and legs (thigh 546 -> 554).
    "measure-neck-circ-incr": 0.10,
    "l-upperarm-muscle-incr": 0.70,
    "r-upperarm-muscle-incr": 0.70,
    "l-lowerarm-muscle-incr": 0.60,
    "r-lowerarm-muscle-incr": 0.60,
    "l-upperleg-muscle-incr": 0.40,
    "r-upperleg-muscle-incr": 0.40,
    "l-lowerleg-muscle-incr": 0.15,
    "r-lowerleg-muscle-incr": 0.15,
}
# The face: MPFB face/head targets fitted by scripts/parts/head.py --fit (least squares on MediaPipe's
# landmarks through the hero camera; scripts/parts/head.md). base.py applies them like the body targets,
# so the eye bones and the landmarks pose.py fits follow the fitted face. SGT_BASE_NO_FACE=1 skips them.
HEAD_FIT = os.path.join(PROJECT, "scripts", "parts", "head_fit.json")
# Skin: MPFB's middle-aged Caucasian male texture as an ENHANCED_SSS material, toned towards the
# reference's albedo (analysis_face_grooming.md §7: base #b98670) by a multiply in its colour chain (the
# group's own colorMix node switched to MULTIPLY); the viewport colour (what Workbench shows) is that albedo.
SKIN_MHMAT = "middleage_caucasian_male/middleage_caucasian_male.mhmat"
# Calibrated once (head part, round 1): the analysis's #b98670 rendered through the hero camera under the
# evaluation lights came out brighter and more orange than the reference's lit cheek, forehead and nose
# (render/reference linear ratios R 0.83, G 0.84, B 1.01), so the albedo was scaled by them.
SKIN_ALBEDO = "#ab7d71"
# The tone is measured, not chosen: the albedo divided by the texture's mean over the face (base.json "skin").
# Eyes (body brief): MPFB's procedural eye shows blue irises in Cycles and plain white in Workbench, and the
# eyelash and eyebrow cards showed red (their viewport colour) round the eyes. Iris per the analysis:
# dark warm brown-grey, sclera never white in this light.
IRIS_MAJOR, IRIS_MINOR, SCLERA = "#5b4a3e", "#3a2d26", "#d9d0c8"
# Workbench draws the lash cards solid: a dark lash colour there reads as heavy eyeliner wings, so their
# viewport colour is the skin's (they vanish in Workbench); Cycles uses the lash texture.
LASH_RGB, BROW_RGB = "#a97a66", "#3b2a22"
IRIS_DEG = 34.0                       # half-angle of the iris cap on the eyeball (iris 12 mm on a 24 mm ball: 30)
STATURE_MM, STATURE_TOL_MM, HEIGHT_START = 1835.0, 0.25, 0.583
ASSETS = (("eyes", "high-poly/high-poly.mhclo", "PROCEDURAL_EYES", "Body.Eyes"),
          ("eyebrows", "eyebrow001/eyebrow001.mhclo", "MAKESKIN", "Body.Eyebrows"),
          ("eyelashes", "eyelashes02/eyelashes02.mhclo", "MAKESKIN", "Body.Eyelashes"))


def say(*a):
    print("[base]", *a, flush=True)


class Mpfb:
    def __init__(self):
        import bpy
        mod = "bl_ext.user_default.mpfb"
        if mod not in bpy.context.preferences.addons:
            bpy.ops.preferences.addon_enable(module=mod)
        from bl_ext.user_default.mpfb.services.humanservice import HumanService
        from bl_ext.user_default.mpfb.services.targetservice import TargetService
        from bl_ext.user_default.mpfb.services.assetservice import AssetService
        from bl_ext.user_default.mpfb.entities.objectproperties import HumanObjectProperties
        self.human, self.targets, self.assets, self.props = HumanService, TargetService, AssetService, HumanObjectProperties


def evaluated_co(ob, helpers=False):
    """World coordinates of the evaluated mesh (MPFB targets are shape keys: always read the evaluated
    mesh). helpers=True switches the MASK modifiers off so the joint cubes are there."""
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
    g = ob.vertex_groups[name]
    gi = g.index
    return [v.index for v in ob.data.vertices if any(e.group == gi and e.weight > min_weight for e in v.groups)]


def stature_mm(ob):
    co = evaluated_co(ob)
    return float(co[:, 2].max() - co[:, 2].min()) * 1000.0


def fit_height(mpfb, body, target, tol, h0):
    """Bracket, then Illinois false position on the height macro (take 1's S1: the macro is kinked)."""
    seen = []

    def at(h):
        mpfb.props.set_value("height", h, entity_reference=body)
        mpfb.targets.reapply_macro_details(body)
        s = stature_mm(body)
        seen.append((h, s))
        say(f"height macro {h:.5f} -> stature {s:.3f} mm")
        return s - target

    a, fa = h0, at(h0)
    step = 0.05 if fa < 0 else -0.05
    b, fb = a, fa
    while abs(fb) > tol and fa * fb > 0:
        a, fa = b, fb
        b = min(1.0, max(0.0, b + step))
        if b == a:
            raise RuntimeError("stature out of the height macro's range")
        fb = at(b)
        step *= 2.0
    for _ in range(30):
        if abs(fb) <= tol:
            break
        c = b - fb * (b - a) / (fb - fa)
        fc = at(c)
        if fc * fb < 0:
            a, fa = b, fb
        else:
            fa /= 2.0
        b, fb = c, fc
    h, s = min(seen, key=lambda hs: abs(hs[1] - target))
    if h != seen[-1][0]:
        at(h)
    return h, s, len(seen)


def ground_and_centre(body):
    """Lowest vertex on z 0, the ankle joint cubes' midpoint over the origin, baked into the mesh."""
    import bpy
    import numpy as np
    from lib import ctx as bctx
    co = evaluated_co(body, helpers=True)
    bidx = np.array(group_indices(body, "body"))
    ank = {s: co[group_indices(body, f"joint-{s}-ankle")].mean(axis=0) for s in ("l", "r")}
    mid = (ank["l"] + ank["r"]) / 2.0
    move = np.array([-mid[0], -mid[1], -float(co[bidx, 2].min())])
    body.location = tuple(np.array(body.location) + move)
    bctx.set_active(body)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    return [round(float(v) * 1000, 2) for v in move]


def body_collection(ob):
    import bpy
    coll = bpy.data.collections.get(COLL) or bpy.data.collections.new(COLL)
    if coll not in bpy.context.scene.collection.children_recursive:
        bpy.context.scene.collection.children.link(coll)
    for c in list(ob.users_collection):
        if c != coll:
            c.objects.unlink(ob)
    if ob.name not in coll.objects:
        coll.objects.link(ob)


# --------------------------------------------------------------------------- measurement

def hull_perimeter(pts):
    """Perimeter of the 2-D convex hull (Andrew's monotone chain): a tape measure's girth."""
    pts = sorted(set(map(tuple, pts)))
    if len(pts) < 3:
        return 0.0

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    h = lo[:-1] + hi[:-1]
    return sum(math.dist(h[i], h[(i + 1) % len(h)]) for i in range(len(h)))


def evaluated_edges(ob):
    """Edge vertex pairs of the evaluated mesh (helpers masked), matching evaluated_co(ob)."""
    import bpy
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    e = np.empty(len(me.edges) * 2, dtype=np.int64)
    me.edges.foreach_get("vertices", e)
    ev.to_mesh_clear()
    return e.reshape(-1, 2)


def section(co, edges, c, d, sel):
    """Points where the mesh edges cross the plane through c with normal d (edges with an end in sel)."""
    import numpy as np
    s = (co - c) @ d
    a, b = edges[:, 0], edges[:, 1]
    cross = (s[a] * s[b] < 0) & (sel[a] | sel[b])
    a, b = a[cross], b[cross]
    t = s[a] / (s[a] - s[b])
    return co[a] + (co[b] - co[a]) * t[:, None]


def tape(P, c, d):
    """Convex-hull perimeter (mm) of section points P in the plane (c, d)."""
    import numpy as np
    if len(P) < 3:
        return 0.0
    u = np.cross(d, [0, 0, 1.0]) if abs(d[2]) < 0.9 else np.cross(d, [1.0, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    rel = P - c
    return round(hull_perimeter([(float(p @ u), float(p @ v)) for p in rel]) * 1000, 1)


def measure(body, rig):
    """Key girths (convex hull of an exact plane section, i.e. a tape measure, mm) and breadths on the rest
    body, and segment lengths and joint heights from the rig."""
    import numpy as np
    co = evaluated_co(body)
    edges = evaluated_edges(body)
    me = body.data
    bidx = np.array(group_indices(body, "body"))
    if len(bidx) != len(co):
        raise RuntimeError(f"evaluated mesh has {len(co)} vertices, body group {len(bidx)}")
    bones = {b.name for b in rig.data.bones}
    vg = {g.index: g.name for g in body.vertex_groups}
    dom = []
    for i in bidx:
        gs = [(e.weight, vg[e.group]) for e in me.vertices[i].groups if vg[e.group] in bones]
        dom.append(max(gs)[1] if gs else "")
    dom = np.array(dom)
    B = {b.name: b for b in rig.data.bones}
    Z = np.array([0, 0, 1.0])

    def head(n):
        return np.array(B[n].head_local)

    def has(*prefixes, side=""):
        return np.array([d.startswith(prefixes) and d.endswith(side) for d in dom])

    trunk = has("spine", "pelvis", "root", "breast", "clavicle", "neck")
    neck = has("neck", "head", "spine01", "clavicle")
    legs = has("upperleg")

    def zgirth(z, sel):
        c = np.array([0, 0, z])
        return tape(section(co, edges, c, Z, sel), c, Z)

    def limb(a, b, sel, frac):
        a, b = head(a), head(b)
        d = (b - a) / np.linalg.norm(b - a)
        c = a + (b - a) * frac
        P = section(co, edges, c, d, sel)
        P = P[np.linalg.norm(P - c, axis=1) < 0.12]
        return tape(P, c, d)

    def zbreadth(z, sel, axis=0):
        c = np.array([0, 0, z])
        P = section(co, edges, c, Z, sel)
        return round(float(np.ptp(P[:, axis])) * 1000, 1) if len(P) else 0.0

    z_neck = (head("neck02")[2] + head("neck03")[2]) / 2
    z_chest = head("spine02")[2] + 0.12
    waist = min((zgirth(z, trunk), z) for z in np.linspace(head("spine04")[2] - 0.05, head("spine02")[2], 25))
    z_hip = head("upperleg01.L")[2] - 0.08
    hips = max((zgirth(z, trunk | legs), z) for z in np.linspace(z_hip - 0.05, z_hip + 0.05, 11))
    z_delt = head("upperarm01.L")[2] - 0.03
    # neck: a tape square to the neck axis (neck01 -> neck03) 10 mm below neck02, under the larynx. Round 0's
    # horizontal plane midway between neck02 and neck03 read 386 there, but once the face targets lengthened
    # the jaw (round 1) it cut through the chin and read 466; it is kept as neck_horizontal_old for comparison.
    n1, n3 = head("neck01"), head("neck03")
    dn = (n3 - n1) / np.linalg.norm(n3 - n1)
    cn = head("neck02") - dn * 0.010
    Pn = section(co, edges, cn, dn, neck)
    Pn = Pn[np.linalg.norm(Pn - cn, axis=1) < 0.10]
    out = {
        "stature_mm": round(float(co[:, 2].max() - co[:, 2].min()) * 1000, 2),
        "girth_mm": {
            "neck": tape(Pn, cn, dn),
            "neck_horizontal_old": zgirth(z_neck, neck),
            "chest": zgirth(z_chest, trunk),
            "waist_min": waist[0], "waist_z_mm": round(waist[1] * 1000),
            "hip": hips[0], "hip_z_mm": round(hips[1] * 1000),
            "upper_arm_L": limb("upperarm01.L", "lowerarm01.L", has("upperarm", side=".L"), 0.55),
            "forearm_L": limb("lowerarm01.L", "wrist.L", has("lowerarm", side=".L"), 0.25),
            "thigh_L": limb("upperleg01.L", "lowerleg01.L", has("upperleg", side=".L"), 0.25),
            "calf_L": limb("lowerleg01.L", "foot.L", has("lowerleg", side=".L"), 0.3),
        },
        "breadth_mm": {
            "bideltoid_A_pose": zbreadth(z_delt, trunk | has("upperarm", "shoulder", "clavicle")),
            "chest": zbreadth(z_chest, trunk),
            "waist": zbreadth(waist[1], trunk),
            "hip": zbreadth(hips[1], trunk | legs),
            "chest_depth": zbreadth(z_chest, trunk, axis=1),
        },
        "segment_mm": {
            "gh_to_elbow_L": round(float(np.linalg.norm(head("lowerarm01.L") - head("upperarm01.L"))) * 1000, 1),
            "elbow_to_wrist_L": round(float(np.linalg.norm(head("wrist.L") - head("lowerarm01.L"))) * 1000, 1),
            "wrist_to_mcp3_L": round(float(np.linalg.norm(head("finger3-1.L") - head("wrist.L"))) * 1000, 1),
            "hip_to_knee_L": round(float(np.linalg.norm(head("lowerleg01.L") - head("upperleg01.L"))) * 1000, 1),
            "knee_to_ankle_L": round(float(np.linalg.norm(head("foot.L") - head("lowerleg01.L"))) * 1000, 1),
            "gh_width": round(float(head("upperarm01.L")[0] - head("upperarm01.R")[0]) * 1000, 1),
            "hip_joint_width": round(float(head("upperleg01.L")[0] - head("upperleg01.R")[0]) * 1000, 1),
        },
        "joint_z_mm": {n: round(float(head(b)[2]) * 1000, 1) for n, b in
                       (("hip", "upperleg01.L"), ("knee", "lowerleg01.L"), ("ankle", "foot.L"), ("gh", "upperarm01.L"),
                        ("elbow", "lowerarm01.L"), ("eye", "eye.L"))},
    }
    return out


def landmarks(body, rig):
    """Rest positions (mm) of the surface points pose.py fits, each with the bone it rides rigidly."""
    import numpy as np
    co = evaluated_co(body)
    B = {b.name: b for b in rig.data.bones}
    hz = np.array(B["head"].head_local)
    head_pts = co[co[:, 2] > hz[2] + 0.01]
    face = co[(co[:, 2] > hz[2] - 0.12) & (np.abs(co[:, 0]) < 0.012)]
    nose = face[np.argmin(face[:, 1] - 0.0 * face[:, 2])]          # most forward midline point: pronasale
    below = face[face[:, 2] < nose[2] - 0.03]
    chin_front = below[np.argmin(below[:, 1])]                      # pogonion
    menton = below[(below[:, 1] < chin_front[1] + 0.025)]
    menton = menton[np.argmin(menton[:, 2])]
    top = head_pts[np.argmax(head_pts[:, 2])]
    L = {"skull_top": (top, "head"), "nose_tip": (nose, "head"), "chin": (menton, "head")}
    # the right pectoral's most forward skin point (the carrier and the carbine's butt rest over it)
    pec = co[(co[:, 0] > -0.17) & (co[:, 0] < -0.09) & (np.abs(co[:, 2] - (hz[2] - 0.40)) < 0.04)]
    L["pec_R"] = (pec[np.argmin(pec[:, 1])], "spine02")
    bidx = np.array(group_indices(body, "body"))
    ears = np.isin(bidx, group_indices(body, "ears"))
    for s, sign in (("L", 1), ("R", -1)):
        e = co[ears & (co[:, 0] * sign > 0)]
        L[f"ear_{s}"] = (e.mean(axis=0), "head")          # the ear's centroid, about the concha
    for s in ("L", "R"):
        e = np.array(B[f"eye.{s}"].head_local)
        # pupil: the front of the eyeball, ~12 mm forward of its centre
        L[f"pupil_{s}"] = (e + np.array([0, -0.012, 0]), "head")
    # feet: heel back-bottom, big-toe tip, 5th-metatarsal-head bottom (sole plane), riding foot.*
    for s, sign in (("L", 1), ("R", -1)):
        side = co[(co[:, 0] * sign > 0.03) & (co[:, 2] < 0.10)]
        heel = side[side[:, 2] < 0.02]
        heel = heel[np.argmax(heel[:, 1])]
        toe = side[np.argmin(side[:, 1])]
        lat = side[(side[:, 2] < 0.012) & (side[:, 1] < heel[1] - 0.15) & (side[:, 1] > toe[1] + 0.03)]
        lat = lat[np.argmax(lat[:, 0] * sign)]
        med = side[(side[:, 2] < 0.012) & (side[:, 1] < heel[1] - 0.15) & (side[:, 1] > toe[1] + 0.03)]
        med = med[np.argmin(med[:, 0] * sign)]
        L[f"heel_{s}"] = (heel, f"foot.{s}")
        L[f"toe_{s}"] = (toe, f"foot.{s}")
        L[f"mt5_{s}"] = (lat, f"foot.{s}")
        L[f"mt1_{s}"] = (med, f"foot.{s}")
    return {k: {"rest_mm": [round(float(v) * 1000, 2) for v in p], "bone": b} for k, (p, b) in L.items()}


def dump_bones(rig):
    out = {}
    for b in rig.data.bones:
        m = b.matrix_local
        out[b.name] = {"parent": b.parent.name if b.parent else None,
                       "head": [round(v * 1000, 3) for v in b.head_local],
                       "tail": [round(v * 1000, 3) for v in b.tail_local],
                       "matrix": [[round(m[i][j] * 1000, 4) if (j == 3 and i < 3) else round(m[i][j], 7) for j in range(4)] for i in range(4)],
                       "inherit": [b.use_inherit_rotation, b.inherit_scale, b.use_local_location, b.use_connect]}
    return out


# --------------------------------------------------------------------------- face targets and materials

def face_targets():
    """head.py --fit's MPFB face/head target weights ({} without the file or with SGT_BASE_NO_FACE)."""
    if os.environ.get("SGT_BASE_NO_FACE") or not os.path.exists(HEAD_FIT):
        return {}
    with open(HEAD_FIT, encoding="utf-8") as f:
        d = json.load(f)
    return {k: float(v) for k, v in d["targets"].items() if abs(float(v)) >= 1e-3}


def srgb_lin(h):
    c = [int(h.lstrip("#")[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def lin_srgb_hex(c):
    out = []
    for v in c:
        v = max(0.0, min(1.0, float(v)))
        out.append(12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055)
    return "#" + "".join(f"{round(v * 255):02x}" for v in out)


def skin_material(mpfb, body):
    """MPFB's ENHANCED_SSS skin on Body.Mesh (one material, Body.Skin), its diffuse texture multiplied by a
    tone that takes the texture's mean over the face (the UVs of the skin weighted to the head bone) to
    SKIN_ALBEDO. Returns the means before and after and the tone, for base.json."""
    import numpy as np
    p = mpfb.assets.find_asset_absolute_path(SKIN_MHMAT, asset_subdir="skins")
    if p is None:
        raise FileNotFoundError(f"MPFB has no skin {SKIN_MHMAT}")
    mpfb.human.set_character_skin(p, body, skin_type="ENHANCED_SSS", material_instances=False)
    mat = body.data.materials[0]
    mat.name = "Body.Skin"
    grp = next(n for n in mat.node_tree.nodes if n.type == "GROUP")
    inner = grp.node_tree
    inner.name = "Body.Skin.Group"
    mat.diffuse_color = (*srgb_lin(SKIN_ALBEDO), 1.0)
    img = inner.nodes["DiffuseTexture"].image
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    me = body.data
    uv = me.uv_layers.active.data
    gi = body.vertex_groups["head"].index
    head_v = {v.index for v in me.vertices if any(e.group == gi and e.weight > 0.9 for e in v.groups)}
    uvs = np.array([uv[li].uv[:] for poly in me.polygons for li in poly.loop_indices
                    if me.loops[li].vertex_index in head_v])
    xs = np.clip((uvs[:, 0] * w).astype(int), 0, w - 1)
    ys = np.clip((uvs[:, 1] * h).astype(int), 0, h - 1)
    col = px[ys, xs, :3][px[ys, xs, 3] > 0.5].mean(axis=0)
    tone = np.clip(np.array(srgb_lin(SKIN_ALBEDO)) / np.maximum(col, 1e-4), 0.0, 1.5)
    inner.nodes["Mix"].blend_type = "MULTIPLY"
    grp.inputs["colorMixIn"].default_value = (*[float(v) for v in tone], 1.0)
    grp.inputs["colorMixInStrength"].default_value = 1.0
    toned = col * tone
    return {"material": mat.name, "mhmat": SKIN_MHMAT, "tone_linear": [round(float(v), 4) for v in tone],
            "target_albedo": SKIN_ALBEDO,
            "face_texture_mean": lin_srgb_hex(col), "face_texture_mean_toned": lin_srgb_hex(toned),
            "viewport_colour": SKIN_ALBEDO}


def eye_materials(eyes, lashes, brows):
    """The eye fixes (body brief). EnhancedEye's iris colours become the reference's brown-grey and its
    white an off-white; the viewport colours (Workbench) become sclera off-white and, on a second material
    slot holding the iris faces (within IRIS_DEG of each eye's forward axis), the iris brown. The second
    slot's material is a copy with the same node settings, so Cycles renders both slots alike. The lash and
    brow cards get dark brown viewport colours (their red viewport colour made the red rims)."""
    import numpy as np
    out = {}
    if eyes is not None and eyes.data.materials:
        m = eyes.data.materials[0]
        m.name = "Body.Eyes.Sclera"
        grp = next((n for n in m.node_tree.nodes if n.type == "GROUP"), None)
        if grp is not None:
            for k, v in (("IrisMajorColor", IRIS_MAJOR), ("IrisMinorColor", IRIS_MINOR), ("EyeWhiteColor", SCLERA)):
                if k in grp.inputs:
                    grp.inputs[k].default_value = (*srgb_lin(v), 1.0)
        m.diffuse_color = (*srgb_lin(SCLERA), 1.0)
        iris = m.copy()
        iris.name = "Body.Eyes.Iris"
        iris.diffuse_color = (*srgb_lin(IRIS_MAJOR), 1.0)
        eyes.data.materials.append(iris)
        me = eyes.data
        mw = np.array(eyes.matrix_world)
        co = np.array([v.co[:] for v in me.vertices]) @ mw[:3, :3].T + mw[:3, 3]
        n_iris = 0
        for side in (1, -1):
            sel = co[:, 0] * side > 0
            c = (co[sel].min(0) + co[sel].max(0)) / 2.0
            for poly in me.polygons:
                fc = co[list(poly.vertices)].mean(0)
                if fc[0] * side <= 0:
                    continue
                d = fc - c
                d /= np.linalg.norm(d) + 1e-12
                if -d[1] > math.cos(math.radians(IRIS_DEG)):
                    poly.material_index = 1
                    n_iris += 1
        out["eyes"] = {"iris": IRIS_MAJOR, "iris_minor": IRIS_MINOR, "sclera": SCLERA, "iris_faces": n_iris}
    for ob, hexc in ((lashes, LASH_RGB), (brows, BROW_RGB)):
        if ob is not None:
            for m in ob.data.materials:
                m.diffuse_color = (*srgb_lin(hexc), 1.0)
            out[ob.name] = hexc
    return out


def render_rest():
    """Rest clay views of the body for the body part (scripts/parts/common.py render_rest_views):
    renders/body/body_rest_{front,side,threequarter}.png and body_chest_rest_*.png."""
    import bpy
    sys.path.insert(0, os.path.join(PROJECT, "scripts", "parts"))
    import common as C
    C.rest_pose(bpy.data.objects[RIG])
    out = os.path.join(PROJECT, "renders", "body")
    C.render_rest_views("body", [], (0, 0, 920), 1950, out_dir=out)
    C.render_rest_views("body_chest", [], (0, 0, 1330), 600, out_dir=out)


def main():
    import bpy
    from mathutils import Matrix
    from lib import ctx as bctx
    t0 = time.perf_counter()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mpfb = Mpfb()
    macro = mpfb.targets.get_default_macro_info_dict()
    macro.update({k: v for k, v in MACRO.items() if k != "race"})
    macro["race"] = dict(MACRO["race"])
    macro["height"] = HEIGHT_START
    body = mpfb.human.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                   feet_on_ground=True, scale=0.1, macro_detail_dict=macro)
    body.name = body.data.name = BODY
    loaded = {}
    for name, w in ({} if os.environ.get("SGT_BASE_NO_TARGETS") else BODY_TARGETS).items():
        path = mpfb.targets.target_full_path(name)
        if not path or os.path.basename(path).split(".")[0] != name:
            raise FileNotFoundError(f"MPFB has no target {name!r}")
        kb = mpfb.targets.load_target(body, path, weight=w)
        loaded[kb.name] = round(float(kb.value), 4)
    say(f"body targets {loaded}")
    face = {}
    for name, w in face_targets().items():
        path = mpfb.targets.target_full_path(name)
        if not path or os.path.basename(path).split(".")[0] != name:
            raise FileNotFoundError(f"MPFB has no target {name!r} (head_fit.json)")
        kb = mpfb.targets.load_target(body, path, weight=w)
        face[kb.name] = round(float(kb.value), 4)
    say(f"face targets ({len(face)}) {face}")
    h, s, n = fit_height(mpfb, body, STATURE_MM, STATURE_TOL_MM, HEIGHT_START)
    moved = ground_and_centre(body)
    body_collection(body)
    bctx.set_active(body)
    rig = mpfb.human.add_builtin_rig(body, "default", import_weights=True)
    rig.name = rig.data.name = RIG
    rig.location = body.location = (0.0, 0.0, 0.0)
    names = [m.name for m in body.modifiers]
    if "Hide helpers" in names and names.index("Hide helpers") > 0:
        with bctx.override(object=body):
            bpy.ops.object.modifier_move_to_index(modifier="Hide helpers", index=0)
    body_collection(rig)
    added = {}
    for subdir, frag, mat, name in ASSETS:
        p = mpfb.assets.find_asset_absolute_path(frag, asset_subdir=subdir)
        if p is None:
            say(f"no {subdir} asset {frag}: skipped")
            continue
        ob = mpfb.human.add_mhclo_asset(p, body, asset_type=subdir, subdiv_levels=0, material_type=mat)
        ob.name = name
        body_collection(ob)
        added[name] = len(ob.data.vertices)
    skin = skin_material(mpfb, body)
    get = bpy.data.objects.get
    skin["eyes"] = eye_materials(get("Body.Eyes"), get("Body.Eyelashes"), get("Body.Eyebrows"))
    bpy.context.view_layer.update()
    ident = Matrix.Identity(4)
    for ob in (rig, body):
        err = max(abs(a - b) for ra, rb in zip(ob.matrix_world, ident) for a, b in zip(ra, rb))
        if err > 1e-9:
            raise RuntimeError(f"{ob.name}'s world matrix is not the identity")
    meas = measure(body, rig)
    marks = landmarks(body, rig)
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = OUT_BLEND + ".tmp.blend"
    bpy.ops.wm.save_as_mainfile(filepath=tmp, copy=True, compress=False)
    os.replace(tmp, OUT_BLEND)
    macros = {k: (dict(v) if isinstance(v, dict) else v) for k, v in macro.items()}
    macros["height"] = round(h, 6)
    summary = {"stage": "round0.base", "body": BODY, "rig": RIG, "collection": COLL,
               "units": "mm; rig space = world (rig and body at the origin, identity)",
               "macro": macros, "body_targets": loaded, "face_targets": face,
               "face_fit": "scripts/parts/head_fit.json" if face else None, "skin": skin, "stature_mm": round(stature_mm(body), 3),
               "stature_target_mm": STATURE_MM, "height_iterations": n, "moved_mm": moved,
               "assets": added, "measure": meas, "landmarks": marks,
               "blender": bpy.app.version_string, "seconds": round(time.perf_counter() - t0, 2),
               "bones": dump_bones(rig)}
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1)
    say(json.dumps({k: summary[k] for k in ("stature_mm", "assets", "seconds")}))
    say(json.dumps(meas, indent=1))
    if "--render" in sys.argv:
        render_rest()
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception:
        import traceback
        traceback.print_exc()
        rc = 1
    sys.stdout.flush()
    os._exit(rc) if rc else None
