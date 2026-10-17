"""Part 01 — Foot, ankle and sock. Spec: spec/01_foot_ankle_sock.md. Builds on cache/body/rigged.blend (S1-S2,
with the MPFB foot targets of §4.1 already loaded by build_all.py's S1):

  on Body.Mesh   shape keys Foot.Sculpt (§4.2-4.3: the landmark sculpt, toes and nail beds) and Foot.Contact
                 (§4.7: the loaded foot, 0 at rest); vertex groups Foot.Region, Foot.Sole, Foot.PlantarContact,
                 Foot.ContactZone, Foot.NailBed.1-5 (§4.6, the geometric ones)
  objects        Foot.L.Nail.1-5, Foot.R.Nail.1-5 in Foot.Nails (§4.4), Frame.Foot.L, Frame.Foot.R (§4.14)
  collection     Part01.FootAnkleSock

  blender -b cache/body/rigged.blend --python-exit-code 1 --python scripts/parts/01_foot_ankle_sock.py --
      [--rebuild] [--stage sculpt..contact] [--render] [--views p01.V1.L,p01.V2.L] [--quality form|look|eval]
      [--params FILE|JSON] [--check] [--from-cache] [--json]

Stages: sculpt, nails, masks, contact, frames are built; guides (§4.5), materials (§5, spec 16's library),
hair (§6.1), sock (§4.10-4.11), last (§4.13), weights (§7.2) and interfaces (§7.1's foot.* keys) are the
later sessions' (§9.3) and only say so. The sculpt's amounts are fitted by scripts/parts/p01/fit_sculpt.py
and kept in scripts/parts/p01/params.json; the foot targets' weights by fit_targets.py (read by S1).

--render makes the closeup copies Foot.L.Isolate and Foot.R.Isolate after the cache is saved (§0 item 9,
§8.1: one foot alone, Subdivision render 3), gives them and the nails a placeholder skin until spec 16's
library exists, builds spec 17's hero scene in this session for the Cycles tiers (LookDev is not built), and
renders the part's presets (all but V6, which needs the boots, unless --views names it) into renders/01_foot/
with a contact sheet. cli.py's --render has no hook for such a step, so this script runs cli.run() itself.
"""
import json
import os
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/
from lib import cache, cli, env, log, naming, replace  # noqa: E402
from lib import sculpt as S  # noqa: E402
from lib.cli import Part  # noqa: E402
from parts.p01 import fields, footmetrics as fm, layers, nails, scanfit  # noqa: E402

PART = Part(id="01", name="foot_ankle_sock", prefixes=("Foot.", "Sock.", "Frame.Foot."), keys=("foot.", "sock."),
            needs={"08": "Morgan.Rig"},
            provides=("Frame.Foot.L", "Frame.Foot.R"),  # Foot.L.Last and Foot.R.Last join with the last stage
            stages=("sculpt", "nails", "masks", "contact", "frames",
                    "guides", "materials", "hair", "sock", "last", "weights", "interfaces"),
            presets="p01")
LATER = {"guides": "§4.5, session 2", "materials": "§5 on spec 16's library, session 2", "hair": "§6.1, session 2",
         "sock": "§4.10-4.11, session 3", "last": "§4.13, session 3", "weights": "§7.2, with the sock",
         "interfaces": "§7.1's foot.* keys, with the last"}
BODY, RIG = "Body.Mesh", "Morgan.Rig"
KEYS = ("Foot.Sculpt", "Foot.Contact")
RENDER_DIR = env.path("renders", "01_foot")
REGION_TOP_MM = 130.0   # §4.6: Foot.Region ends at MakeHuman's ankle seam ring
ISOLATE_TOP_MM = 300.0  # §8.1: the closeup copies keep the shin to z 300
LOOK_EXPOSURE = -1.5    # stops, for Cycles looks under the uncalibrated hero lights (render())


# --------------------------------------------------------------------------- helpers

def _body():
    import bpy
    ob = bpy.data.objects.get(BODY)
    if ob is None or ob.type != "MESH":
        raise cli.MissingDependency(f"{BODY} is not in this session: open cache/body/rigged.blend")
    return ob


def _drop(ob, *names):
    """Remove the part's own shape keys or vertex groups by name (a stage re-run replaces only its layer)."""
    sk = ob.data.shape_keys
    for n in names:
        if sk is not None and n in sk.key_blocks:
            ob.shape_key_remove(sk.key_blocks[n])
        g = ob.vertex_groups.get(n)
        if g is not None:
            ob.vertex_groups.remove(g)


def _sculpt_body(ob, st):
    """fields.Body of the body without this part's keys: the geometry the sculpt starts from."""
    if "body" not in st:
        st["body"] = fields.Body(ob, exclude=KEYS)
    return st["body"]


def _set_group(ob, name, weights, eps=1e-4):
    """A vertex group from per-vertex weights (only the non-zero ones are written)."""
    g = ob.vertex_groups.new(name=naming.check(name))
    import numpy as np
    w = np.round(np.asarray(weights, float), 4)
    for value in np.unique(w[w > eps]):
        g.add(np.nonzero(w == value)[0].tolist(), float(value), "REPLACE")
    return g


def _sculpted_world(ob):
    """World mm of every vertex with Foot.Sculpt on and Foot.Contact off (the rest foot)."""
    return S.mix(ob, exclude=("Foot.Contact",)) * 1000.0


# --------------------------------------------------------------------------- stages

def stage_sculpt(ctx, scope, ob, st):
    """§4.2-4.3: the landmark sculpt, toes and nail beds as the Foot.Sculpt key (basis + sculpt). The
    loaded foot is made from it, so a re-run of this stage alone wants contact after it (--stage sculpt..contact)."""
    _drop(ob, "Foot.Sculpt")
    body = _sculpt_body(ob, st)
    a = fields.amounts(ctx.params)
    co = body.positions(a, fields.options(ctx.params))
    S.key_from_positions(ob, "Foot.Sculpt", co / 1000.0, base=body.co / 1000.0)
    st["amounts"] = a
    for side in fields.SIDES:
        foot = body.feet[side]
        for what in ("mtp_lift", "webs_closed", "nail_shift", "contacts_resolved"):
            if getattr(foot, what, None):
                log.info("part 01", f"{side} {what}: {getattr(foot, what)}")


def stage_nails(ctx, scope, ob, st):
    """§4.4: one plate per nail, on its sculpted bed, riding its toe's distal bone."""
    import bpy
    scope.clear("Foot.L.Nail")
    scope.clear("Foot.R.Nail")
    coll = bpy.data.collections.get("Foot.Nails")
    if coll is None or coll.library is not None:
        coll = scope.collection("Foot.Nails")
    rig = bpy.data.objects[RIG]
    body = _sculpt_body(ob, st)
    co = _sculpted_world(ob) / 1000.0
    made = {}
    for side in fields.SIDES:
        foot = body.feet[side]
        tw = {k: sum(body.groups[g] for g in fm.toe_bones(k, side) if g in body.groups) for k in fields.TOES}
        faces = nails.nail_faces(ob, co, side, tw, body.groups["toenails"])
        for k in fields.TOES:
            if not faces[k]:
                ctx.warn(f"no nail bed on toe {k} of the {side} foot")
                continue
            T = foot.toe[k]
            axis = foot.frame.vec_to_w(T["a"])
            w, vis, fe, thick = nails.PLATES[k]
            name = naming.name("Foot", side, "Nail", str(k))
            me, dims, frame = nails.build_plate(name, ob, co, faces[k], axis, thick, fe, fields.NAIL_RADIUS[k],
                                                nails.CORNER_MM[k])
            nob = scope.new_object(name, me, coll)
            nails.finish(nob, thick)
            nails.parent_to_bone(nob, rig, f"{nails.DISTAL_BONE[k]}.{side}")
            nob["p01_axis"] = [float(v) for v in axis]
            nob["p01_frame"] = json.dumps({k2: v for k2, v in frame.items()})  # world mm, for measure()
            made[name] = {k2: round(v, 3) for k2, v in dims.items()}
    st["nails"] = made


def stage_masks(ctx, scope, ob, st):
    """§4.6, the geometric masks: the foot's region, the sole, the plantar contact zone and the nail beds.
    (The material masks, callus to hair density, come with the materials stage.)"""
    import numpy as np
    names = ["Foot.Region", "Foot.Sole", "Foot.PlantarContact", "Foot.ContactZone"] + [f"Foot.NailBed.{k}" for k in fields.TOES]
    _drop(ob, *names)
    body = _sculpt_body(ob, st)
    co = _sculpted_world(ob)
    nrm = S.vertex_normals(co, *body.topo)
    n = len(co)
    W = {nm: np.zeros(n) for nm in names}
    bodymask = np.zeros(n, bool)
    bodymask[body.m0.orig if body.m0.orig is not None else np.arange(n)] = True
    for side in fields.SIDES:
        foot = body.feet[side]
        R = foot.R[foot.body]
        z = co[R, 2]
        W["Foot.Region"][R] = (z < REGION_TOP_MM).astype(float)
        plantar = S.smoothstep(-nrm[R, 2], 0.3, 0.6)
        W["Foot.Sole"][R] = plantar * (1.0 - S.smoothstep(z, 8.0, 14.0))
        W["Foot.PlantarContact"][R] = 1.0 - S.smoothstep(z, 1.0, 4.0)
        W["Foot.ContactZone"][R] = 1.0 - S.smoothstep(z, 12.0, 20.0)
        rows = foot.nail_rows
        for k in fields.TOES:
            W[f"Foot.NailBed.{k}"][foot.R[rows[k]]] = 1.0
    for nm in names:
        _set_group(ob, nm, W[nm] * bodymask)


def stage_contact(ctx, scope, ob, st):
    """§4.7: Foot.Contact, the loaded foot over the sculpted one (value 0 at rest; the pose sets 1.0 on the
    right and 0.85 on the left)."""
    _drop(ob, "Foot.Contact")
    body = _sculpt_body(ob, st)
    rest = _sculpted_world(ob)
    loaded = rest.copy()
    for side in fields.SIDES:
        foot = body.feet[side]
        q = foot.frame.to_f(rest[foot.R])
        loaded[foot.R] = foot.frame.to_w(fields.contact(body, side, q))
    S.key_from_positions(ob, "Foot.Contact", loaded / 1000.0, base=rest / 1000.0, value=0.0)


def stage_frames(ctx, scope, ob, st):
    """§4.14: Frame.Foot.L/R, frame F of each sculpted foot as an Empty, for spec 17's presets."""
    from mathutils import Matrix
    scope.clear("Frame.Foot.L")
    scope.clear("Frame.Foot.R")
    m = fm.read(ob)
    ix = fm.index(ob, m)
    for side in fields.SIDES:
        f = fm.frame(m, ix, side)
        e = scope.new_object(naming.name("Frame", None, "Foot", side), None)
        e.empty_display_type, e.empty_display_size = "ARROWS", 0.06
        e.matrix_world = Matrix(f.matrix().tolist())
        e["p01_doc"] = "frame F (spec 01): origin at the pternion on the floor, +Z up, toes toward -Y"


def stage_later(name):
    def run(ctx, scope, ob, st):
        st.setdefault("later", []).append(f"{name} ({LATER[name]})")
    return run


STAGES = {"sculpt": stage_sculpt, "nails": stage_nails, "masks": stage_masks, "contact": stage_contact,
          "frames": stage_frames}
STAGES.update({k: stage_later(k) for k in LATER})


def build(ctx, args):
    ob = _body()
    st = {}
    with replace.part_scope(PART) as scope:
        if not ctx.partial:
            replace.body_layer(PART)  # every Foot.* key and group goes; the stages make them again
        for stage in ctx.stages(args):
            STAGES[stage](ctx, scope, ob, st)
    if st.get("later"):
        ctx.warn("not built yet (spec 01 §9.3's later sessions): " + "; ".join(st["later"]))
    rec = cache.save_part(PART)
    if rec is not None:
        layers.save(PART, ob, rec["key"])
        ctx.output(layers.path(PART))


# --------------------------------------------------------------------------- measure (§8.2)

# Jeff's lock of 2026-10-10, from reference photos (§3.3, §4.3 notes): the tips of the curled, shortened lesser
# toes (the left foot's, as built; the right 2nd toe stays 1.5 shorter), the 30 mm hallux and the slim toe 2;
# toes 3-4 measure wider than the §3.3 table where a closed web joins them to their neighbour, and the
# hallux deeper where it was thickened with its width. Jeff, 2026-10-15 (§3.3 note): "toe 2 looks right; it is the
# big toe that is too long": the hallux 7 mm shorter, so the foot is 274.7 to its longest toe, the lesser toes'
# tips where they were (absolute, no longer shares of the length); toe 5 rolled onto its side measures the §3.3
# table's 14.5 across
# The scan-driven pass (2026-10-16, §3.3 note): toes 3-5 most of the way to three real men's cascade (scaled to this
# length they end 4, 14 and 33 mm behind toe 2; here 10, 22 and 40 before), the lesser toes plumper (fit_sculpt.py)
TIP_Y = {1: -274.7, 2: -272.3556, 3: -265.5, 4: -255.5, 5: -235.5}
TOE_W = {1: 30.0, 2: 16.6, 3: 17.0, 4: 17.2, 5: 15.0}
TOE_H = {1: 24.8, 2: 18.0, 3: 16.5, 4: 15.5, 5: 16.5}
L_TARGET = 274.7
# metric: (target, tolerance, source); spec 01 §3.1 and §3.3 targets, §8.2 tolerances (lengths 3, widths and
# heights 2, girths 6, toe tips 2, nails 1 and 0.2); (E) marks the spec's own estimates
TARGETS = {
    "foot_length": (L_TARGET, 3.0, "§3.1 ANSUR, §3.3 (Jeff 2026-10-15: the shorter hallux)"),
    "ball_length": (210.0, 3.0, "§3.1 ANSUR"),
    "ball_breadth": (105.0, 2.0, "§3.1 ANSUR"),
    # heel H1 (Jeff, 2026-10-10: round at the back, widest at 18 % L, breadth 76, 69 / 72 / 73 at z 10 / 20 / 30 at
    # 15 % L) gave way in the scan-driven pass (2026-10-16, §3.1 note) to three real men's unloaded heels scaled to
    # this length (scanfit.py, scan_targets.json: breadth 68.3, 58.6 / 63.6 / 60.8 at 15 % L): H1 was 6-12 mm wider
    # there, a bulb that narrowed into a neck above the pad where real heels are a bell. Read on the cage (§8.2),
    # which stands 1-2 mm outside the rendered surface
    "heel_breadth": (70.0, 3.0, "§3.1 (scans 2026-10-16: 68.3, cage +1.5)"),
    "heel_widest": (70.0, 3.0, "§3.1 (scans 2026-10-16)"),
    "heel_width_z10": (60.0, 3.0, "§3.1 (scans 2026-10-16: 58.6)"), "heel_width_z20": (64.5, 3.0, "§3.1 (scans: 63.6)"),
    "heel_width_z30": (62.0, 3.0, "§3.1 (scans 2026-10-16: 60.8)"), "bimalleolar": (76.0, 2.0, "§3.1 ANSUR"),
    "malleolus_lateral_z": (76.0, 2.0, "§3.1 ANSUR"), "malleolus_medial_z": (89.0, 2.0, "§3.1 (E)"),
    "ankle_circ_min": (229.0, 6.0, "§3.1 ANSUR"), "heel_ankle_circ": (353.0, 6.0, "§3.1 ANSUR"),
    # the instep's 263 (E) assumed a midfoot about 100 wide, the paddle Jeff saw from above; a midfoot of the plan
    # outline's breadth tapes 240-250 in this vertical plane (§3.1 note 2026-10-14)
    "ball_circ": (259.0, 6.0, "§3.1 ANSUR"), "instep_circ": (246.0, 6.0, "§3.1 (E, 2026-10-14)"),
    "dorsum_h50": (66.0, 2.0, "§3.1 (E)"), "dorsum_h60": (56.0, 2.0, "§3.1 (E)"), "dorsum_h70": (40.0, 2.0, "§3.1 (E)"),
    # the scan-driven pass (2026-10-16, §3.1 note): the rest foot is the scans' unloaded one (seated, a tenth of the
    # weight): the medial border 15.6 (9.5 loaded: §3.1's 13 was a standing estimate), the lateral border on the floor
    # (0.9 both; the 4 was an estimate)
    "arch_medial_45": (16.0, 3.0, "§3.1 (scans 2026-10-16: 15.6 unloaded)"),
    "lateral_clear_50": (1.0, 1.5, "§3.1 (scans 2026-10-16: 0.9)"),
    "pternion_z": (30.0, 2.0, "§3.1 (E)"),
}
# the plan outline seen from above (the shape pass, 2026-10-14, §3.1 note; footmetrics.plan on the subdivided
# surface): the midfoot 0.86 of the ball's breadth, the foot widest across the metatarsal heads, the lateral border
# straight from the heel to the 5th head, the medial border dipping in along the first metatarsal. (target, band or
# tolerance, source); a band is [least, most]
# (the scan-driven pass, 2026-10-16: the midfoot's breadth at 50 % L 88.2 on the three men's scans, their lateral
# borders 1.1, 4.6 and 5.3 off the chord, their medial 2.7-7.6 inside it)
PLAN_TARGETS = {
    "plan_b50": (88.0, 3.0, "§3.1 (scans 2026-10-16: 88.2)"),
    "plan_mid_ratio": ([0.82, 0.92], None, "§3.1 (D, 2026-10-14: the midfoot's breadth over the heads')"),
    "plan_widest_pct": ([60.0, 76.0], None, "§3.1 (D, 2026-10-14: widest across the heads)"),
    "plan_lat_bulge": ([-2.0, 6.0], None, "§3.1 (scans 2026-10-16: the lateral border off its heel-to-head chord)"),
    "plan_med_dip": ([2.0, 8.0], None, "§3.1 (scans 2026-10-16: the medial border inside its heel-to-head chord)"),
}
PLAN_REPORTED = ("plan_b40", "plan_b60", "plan_ball", "plan_head5_pct", "plan_head1_pct", "plan_widest")
for _k, _y in TIP_Y.items():
    TARGETS[f"toe{_k}_tip_y"] = (_y, 2.0, "§3.3")
    TARGETS[f"toe{_k}_width"] = (TOE_W[_k], 2.0, "§3.3")
    TARGETS[f"toe{_k}_height"] = (TOE_H[_k], 2.0, "§3.3 (thickness at the IP/PIP)")


SCAN_TARGETS = scanfit.load_targets()
SCAN_RMS = {"plan": 3.5, "heel": 3.0, "sole": 2.5}   # mm: the most each family's RMS may read (the scan-driven pass;
# the plan's worst stations are 75-80 % L, where toes 4 and 5 sit 6-9 mm inside the scans': X3's toes and the 4.5 mm
# gap between the hallux and toe 2, which turns toes 2-5 outward, §3.1 note)


def _scan_measures(fine, f, m, ix, side):
    """scanfit's measures on the body's subdivided read for one foot, in the scans' frame (fit_sculpt.scan_measures,
    on the whole body: this foot's triangles below z 220 kept)."""
    import numpy as np
    q = f.to_f(fine.co * 1000.0)
    T = scanfit.triangles(fine.loop_start, fine.loop_total, fine.loop_vert)
    ok = (np.abs(q[:, 0]) < 90.0) & (q[:, 1] > -320.0) & (q[:, 1] < 60.0) & (q[:, 2] < 220.0)
    T = T[ok[T].all(axis=1)]
    used = np.unique(T)
    remap = np.full(len(q), -1, np.int64)
    remap[used] = np.arange(len(used))
    t2 = f.to_f(m.co[ix.toe_distal[side][2]] * 1000.0)
    qs, _ = scanfit.rezero(q[used], t2[np.argmin(t2[:, 1])])
    return scanfit.measures(qs, remap[T])


def _nail_dims(nob):
    """A plate's width and visible length (mm) across and along its toe, from its own mesh; its transverse
    radius across the middle; and its thickness just inside the free edge on the rendered (solidified,
    subdivided) surface."""
    import numpy as np
    co = np.array([v.co for v in nob.data.vertices]) * 1000.0
    a = np.array(nob["p01_axis"], float)
    nrm = fields.plane_normal(co, np.array([0.0, 0.0, 1.0]))
    a = a - (a @ nrm) * nrm
    a /= np.linalg.norm(a)
    b = np.cross(nrm, a)
    sol = nob.modifiers.get("Solidify")
    frame = json.loads(nob["p01_frame"]) if "p01_frame" in nob else None
    return {"width": float((co @ b).max() - (co @ b).min()), "length": float((co @ a).max() - (co @ a).min()),
            "thickness": sol.thickness * 1000.0 if sol else 0.0,
            "radius": nails.transverse_radius(co, np.array(nob["p01_axis"], float)),
            "edge_thickness": nails.free_edge_thickness(nob, frame) if frame else None}


def measure(ctx, args):
    """§8.2 on the evaluated body at rest (Foot.Contact 0) and loaded (1.0), in spec 18's envelope."""
    import bpy
    ob = _body()
    out = []

    def add(name, value, target=None, tol=None, source="", unit="mm"):
        out.append(cli.metric(name, value, target, tol, unit, "spec 01 " + source if source else "", PART.id))

    sk = ob.data.shape_keys
    contact = sk.key_blocks.get("Foot.Contact") if sk else None
    old = contact.value if contact else None
    try:
        if contact:
            contact.value = 0.0
        m = fm.read(ob)
        ix = fm.index(ob, m)
        fine = fm.subdivided(ob)  # the malleoli are read on the surface the closeups render (fm.subdivided)
        rest = {}
        for side in fields.SIDES:
            v = fm.foot(m, ix, side)
            f = v.pop("_frame")
            add(f"bimalleolar_cage.{side}", round(v["bimalleolar"], 2), unit="mm")
            v.update(fm.ankle(fine, f))       # the malleoli and the heel's apex on the rendered surface: the
            v.update(fm.heel_back(fine, f))   # cage's 13 mm rows would quantise them (fm.subdivided)
            v.update(fm.plan(fine, f, v["station_length"]))   # the plan outline, on the rendered surface too
            add(f"heel_prom.{side}", round(v["heel_prom"], 2), [3.0, 15.0], None,
                "§3.2 (the calcaneus behind the Achilles insertion)")
            # the scan-driven pass (2026-10-16, §3.1 note): the rendered surface against three real men's unloaded feet
            # (scanfit.py): each family's RMS deviation from their mean sections; the build before the pass read plan
            # 2.1, heel 3.8, sole 4.0
            if SCAN_TARGETS is not None:
                for fam, d in scanfit.report(_scan_measures(fine, f, m, ix, side), SCAN_TARGETS).items():
                    add(f"scan_{fam}_rms.{side}", d["rms"], [0.0, SCAN_RMS[fam]], None,
                        f"§3.1 (scans 2026-10-16; worst {d['max']} at {d['at']})")
            rest[side] = v
            for k, (t, tol, src) in TARGETS.items():
                if k == "toe2_tip_y" and side == "R":
                    t = t + 1.5  # the right 2nd toe is 1.5 mm shorter (§3.3)
                add(f"{k}.{side}", None if v.get(k) is None else round(v[k], 2), t, tol, src)
            for k, (t, tol, src) in PLAN_TARGETS.items():
                add(f"{k}.{side}", None if v.get(k) is None else round(v[k], 3), t, tol, src,
                    unit="" if k == "plan_mid_ratio" else ("%" if k.endswith("_pct") else "mm"))
            for k in PLAN_REPORTED:
                add(f"{k}.{side}", None if v.get(k) is None else round(v[k], 2),
                    unit="%" if k.endswith("_pct") else "mm")
            add(f"ball_length_lateral.{side}", None if v.get("ball_length_lateral") is None
                else round(v["ball_length_lateral"], 2), unit="mm")
            for pair, g in fm.toe_gaps(m, ix, side).items():
                # Jeff, 2026-10-10: the lesser toes touch but never cross; the hallux stands about 4.5 mm off toe 2
                band, why = ([3.0, 6.5], "§4.3 (the hallux apart: about 4.5)") if pair == "1-2" else \
                    ([0.1, 60.0], "§4.3 (touching, never crossing)")
                add(f"toe_gap_{pair}.{side}", None if g is None else round(g, 2), band, None, why)
            add(f"heading_deg.{side}", round(v["heading_deg"], 2), unit="deg")
        for nob in sorted((o for o in bpy.data.objects if o.name.startswith(("Foot.L.Nail.", "Foot.R.Nail."))),
                          key=lambda o: o.name):
            k = int(nob.name.split(".")[-1])
            w, vis, fe, thick = nails.PLATES[k]
            d = _nail_dims(nob)
            side = nob.name.split(".")[1]
            add(f"nail{k}_width.{side}", round(d["width"], 2), w, 1.0, "§3.3")
            add(f"nail{k}_length.{side}", round(d["length"], 2), vis, 1.0, "§3.3 (visible, with the free edge)")
            add(f"nail{k}_thickness.{side}", round(d["thickness"], 2), thick, 0.2, "§3.3")
            add(f"nail{k}_edge_thickness.{side}", None if d["edge_thickness"] is None else round(d["edge_thickness"], 2),
                thick, 0.2, "§3.3 (0.5 mm inside the free edge, on the rendered surface)")
            add(f"nail{k}_radius.{side}", None if d["radius"] is None else round(d["radius"], 2),
                fields.NAIL_RADIUS[k], 1.5, "§3.3 (transverse, across the middle third)")
        if contact:
            contact.value = 1.0
            m1 = fm.read(ob)
            for side in fields.SIDES:
                f0 = fm.frame(m, ix, side)
                v1 = fm.foot(m1, ix, side, toes=False)
                # the heel pad's width 10 mm above the floor, loaded against rest (§3.5: +3.5 mm); lower down
                # the flattened contact patch dominates and higher up the pad does not bulge
                w0 = fm.breadth(m, f0, (-60.0, 5.0), [10.0])[0]
                w1 = fm.breadth(m1, f0, (-60.0, 5.0), [10.0])[0]
                add(f"contact_heel_spread.{side}", round(w1 - w0, 2), [5.0, 11.0], None,
                    "§1.4 item 7 (scans 2026-10-16: 5.7-10.5; heel width at z 10, loaded against rest)")
                add(f"contact_arch_drop.{side}", round(rest[side]["arch_medial_45"] - v1["arch_medial_45"], 2),
                    [4.5, 8.0], None, "§1.4 item 7 (scans 2026-10-16: 6.2, 5.5-8.7)")
                co1 = m1.co[ix.region[side]] * 1000.0
                add(f"contact_floor_min_z.{side}", round(float(co1[:, 2].min()), 3), [-0.05, 0.05], None,
                    "§1.4 item 7 (no sinking, no hovering)")
                patch = int((co1[:, 2] < 0.05).sum())
                add(f"contact_patch_vertices.{side}", patch, [60, 2000], None, "§1.4 item 7 (a flat patch)", unit="")
    finally:
        if contact:
            contact.value = old
    add("layers_sha256", layers.digest(ob, PART)[:16], unit="")
    return out


# --------------------------------------------------------------------------- rendering (§8.1)

def isolate_copies(ob):
    """Foot.L.Isolate and Foot.R.Isolate: one foot of the evaluated body, cut below z 300, smooth, with a
    render subdivision of 3 (§0 item 9, §8.1); made after the cache is saved, so they never enter it."""
    import bmesh
    import bpy
    coll = replace.ensure_collection(PART)
    dg = bpy.context.evaluated_depsgraph_get()
    made = []
    for side, s in (("L", 1.0), ("R", -1.0)):
        name = f"Foot.{side}.Isolate"
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old)
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        me.name = name
        bm = bmesh.new()
        bm.from_mesh(me)
        kill = [v for v in bm.verts if not (s * v.co.x > 0.04 and v.co.z < ISOLATE_TOP_MM / 1000.0)]
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        cp = bpy.data.objects.new(name, me)
        coll.objects.link(cp)
        sub = cp.modifiers.new("Subdivision", "SUBSURF")
        sub.levels, sub.render_levels = 1, 3
        sub.quality = 4
        made.append(cp)
    return made


def placeholder_materials(objs, nail_objs):
    """A plain skin and nail for Cycles looks until spec 16's library exists (§0 item 7): §3.4's dorsum
    albedo with a random-walk scatter of spec 16's core radii, and a pale, glossy plate."""
    import bpy

    def lin(h):
        c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1.0,)

    def mat(name, colour, rough, sss=0.0, radius=(1.0, 0.2, 0.1), scale=0.003, coat=0.0):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        p = m.node_tree.nodes.get("Principled BSDF")
        p.inputs["Base Color"].default_value = lin(colour)
        p.inputs["Roughness"].default_value = rough
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = radius
        p.inputs["Subsurface Scale"].default_value = scale
        p.inputs["Coat Weight"].default_value = coat
        return m

    skin = mat("Foot.Mat.Placeholder.Skin", "b6886f", 0.45, sss=1.0, scale=0.0032)
    # §3.4: the bed #d49a88 seen through a pale plate #e9dfd6, mixed, glossy (spec 16's Nail.Plate comes later)
    nail = mat("Foot.Mat.Placeholder.Nail", "dcb2a4", 0.2, sss=0.5, radius=(1.0, 0.45, 0.35), scale=0.001, coat=0.6)
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(skin)
    for o in nail_objs:
        if not o.data.materials:
            o.data.materials.append(nail)


def render(args, ctx_views, tier):
    """The part's views at a tier into renders/01_foot/, and a contact sheet of them; returns file paths."""
    import bpy
    env.bootstrap()
    import importlib
    harness = importlib.import_module("eval.render")
    camera = importlib.import_module("eval.camera")
    reg = camera.load_registry()
    names = [v for v in ctx_views.split(",") if v] or [i for i in reg.owner_ids(PART.id) if not i.startswith("p01.V6")]
    ob = _body()
    copies = isolate_copies(ob)
    nail_objs = [o for o in bpy.data.objects if o.name.startswith(("Foot.L.Nail.", "Foot.R.Nail."))]
    scene_name = None
    if tier != "form":
        placeholder_materials(copies, nail_objs)
        scene = importlib.import_module("eval.scene")
        built = scene.build(proxy=False, character=None, world="hdri")  # spec 17's lights and floor, here
        # spec 17 §4.14: the nominal hero lights read 3-5 x too bright until calibration stage A; these looks
        # judge shape, not colour, so they are taken 1.5 stops down (the sidecar records the scene, not this)
        bpy.data.scenes[built["scene"]].view_settings.exposure = LOOK_EXPOSURE
        scene_name = "hero"
    outputs, sides = [], []
    for n in names:
        side = harness.render_preset(n, tier=tier, scene_name=scene_name)
        sides.append(side)
        outputs.append(env.path(side["outputs"]["png"]))
        log.info("part 01", f"rendered {side['preset']} {tier} in {side['seconds']:.2f} s -> {side['outputs']['png']}")
    sheet = None
    pyimg = env.load().get("pyimg")
    if pyimg and outputs:
        run = f"p01_{tier}_{time.strftime('%Y%m%d_%H%M%S')}"
        cmd = [pyimg, "-I", env.path("scripts", "tools", "sheet.py"), "sheet", "--preset", names[0], "--run", run,
               "--title", f"part 01 {tier}", "--images"] + outputs + ["--labels"] + [s["preset"] for s in sides]
        p = subprocess.run(cmd, cwd=env.PROJECT_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")
        sheet = os.path.join(RENDER_DIR, "sheets", f"{run}.png")
        if p.returncode != 0 or not os.path.isfile(sheet):
            log.info("part 01", f"sheet failed: {p.stdout[-400:]} {p.stderr[-400:]}")
            sheet = None
    return outputs + ([sheet] if sheet else []), sides


# --------------------------------------------------------------------------- the command line

def _body_signature():
    """sha256 of the body this part builds on (its basis and topology): the part's cache key must change
    when S1-S2 change the body, and the dependency record (`08: session`) does not say so."""
    import hashlib
    import numpy as np
    ob = _body()
    h = hashlib.sha256(layers.topology_hash(ob).encode())
    for kb in ob.data.shape_keys.key_blocks if ob.data.shape_keys else []:
        if naming.owned(kb.name, PART.prefixes):
            continue
        h.update(kb.name.encode())
        h.update(np.round(S.key_coords(kb) * 1e5).astype("<i8").tobytes())
        h.update(np.float64(kb.value).tobytes())
    return h.hexdigest()[:16]


def _with_body_param(argv):
    """argv with the body's signature merged into --params (so it enters the cache key)."""
    argv = list(argv)
    extra = {}
    if "--params" in argv:
        i = argv.index("--params")
        raw = argv[i + 1]
        extra = json.loads(raw) if raw.lstrip().startswith("{") else (cache.read_json(env.path(raw)) or {})
        del argv[i:i + 2]
    extra["body"] = _body_signature()
    return argv + ["--params", json.dumps(extra, sort_keys=True)]


def _restore_layers(argv):
    """When the part's cache is fresh, put its body layers back (lib/cache has no layer_apply yet); when the
    cache is fresh but its layers are missing, rebuild. --stage runs on the cached part, so its layers come
    back too (a stage replaces only its own). Returns the arguments to run with."""
    try:
        a = cli.parse(argv)
    except cli.UsageError:
        return argv
    if a.stage:
        if not layers.apply(PART, _body()):
            print(f"[part {PART.id}] warning: --stage without a layer cache ({os.path.relpath(layers.path(PART), env.PROJECT_DIR)}):"
                  " the stage starts from the unsculpted body", flush=True)
        return argv
    if a.rebuild or a.check:
        return argv
    ctx = cli.Context(PART, a)
    try:
        ctx.resolve()
    except cli.MissingDependency:
        return argv
    ok, _ = cache.fresh(PART, ctx)
    if not ok and not a.from_cache:
        return argv
    stored = (cache.read_key(PART) or {}).get("key")
    meta = layers.load_meta(PART)
    if meta and meta.get("key") == stored and layers.apply(PART, _body()):
        return argv
    return argv if a.from_cache else argv + ["--rebuild"]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    want_render = "--render" in argv
    argv = _with_body_param([x for x in argv if x != "--render"])
    argv = _restore_layers(argv)
    res = cli.run(PART, build, measure, argv)
    if res.get("metrics"):
        os.makedirs(RENDER_DIR, exist_ok=True)
        cache.write_json(os.path.join(RENDER_DIR, "measure.json"),
                         {"part": PART.id, "written": log.now(), "cache": res.get("cache"), "key": res.get("key"),
                          "metrics": res["metrics"], "failed": res.get("failed", [])})
    if want_render and res.get("exit") in (cli.PASS, cli.TOLERANCE):
        t = time.perf_counter()
        a = cli.parse(argv)
        try:
            files, _ = render(a, a.views, a.quality)
            res.setdefault("outputs", []).extend(os.path.relpath(f, env.PROJECT_DIR).replace(os.sep, "/") for f in files)
        except Exception as e:  # a render failure is reported, the build stands
            import traceback
            traceback.print_exc()
            res.setdefault("warnings", []).append(f"render failed: {type(e).__name__}: {e}")
        res.setdefault("timings", {})["render"] = round(time.perf_counter() - t, 3)
    if "--json" in argv:
        print("RESULT " + log.dumps(res), flush=True)
    else:
        print(f"[part {PART.id}] {res['status']} (exit {res['exit']}), cache {res.get('cache')}, "
              f"{res.get('timings', {}).get('total')} s", flush=True)
        for w in res.get("warnings", []):
            print(f"[part {PART.id}] warning: {w}", flush=True)
        for m in res.get("metrics", []):
            if m.get("pass") is False:
                print(f"[part {PART.id}] FAIL {m['metric']} = {m['value']} (target {m['target']} +/- {m['tol']})")
        if res.get("error"):
            print(res.get("trace") or res["error"], flush=True)
    sys.stdout.flush()
    sys.exit(res["exit"])


if __name__ == "__main__":
    main()
