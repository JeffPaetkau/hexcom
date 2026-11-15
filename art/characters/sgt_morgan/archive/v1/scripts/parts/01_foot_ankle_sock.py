"""Part 01 — Foot, ankle and sock. Spec: spec/01_foot_ankle_sock.md. Builds on cache/body/rigged.blend (S1-S2,
with the MPFB foot targets of §4.1 already loaded by build_all.py's S1):

  on Body.Mesh   shape keys Foot.Sculpt (§4.2-4.3: the landmark sculpt, toes and nail beds) and Foot.Contact
                 (§4.7: the loaded foot, 0 at rest); vertex groups Foot.Region, Foot.Sole, Foot.PlantarContact,
                 Foot.ContactZone, Foot.NailBed.1-5, Foot.ScanKeep (§4.6, the geometric ones) and the material masks
                 Foot.Callus.*, Foot.Corn.L4, Foot.Rub.Achilles, Foot.Pressure, Foot.ToeRed, Foot.DorsumThin,
                 Foot.SSSScale; the material Body.Mat.Skin.Foot on Foot.Region's faces
  objects        Foot.L.Nail.1-5, Foot.R.Nail.1-5 in Foot.Nails (§4.4), Frame.Foot.L, Frame.Foot.R (§4.14),
                 Sock.L.Body, Sock.R.Body in Sock.Pair, Foot.<S>.SockTarget, Foot.<S>.Last and its markers in Foot.Lasts
  collection     Part01.FootAnkleSock

  blender -b cache/body/rigged.blend --python-exit-code 1 --python scripts/parts/01_foot_ankle_sock.py --
      [--rebuild] [--stage sculpt..contact] [--render] [--views p01.V1.L,p01.V2.L] [--quality form|look|eval]
      [--params FILE|JSON] [--check] [--from-cache] [--json]

Stages: sculpt, nails, masks, contact, frames, materials, sock, last and interfaces are built; guides (§4.5), hair
(§6.1) and weights (§7.2, with §7.4's sock attachment) are the later sessions' (§9.3) and only say so. The sculpt's
amounts are fitted by scripts/parts/p01/fit_sculpt.py and kept in scripts/parts/p01/params.json; the foot targets'
weights by fit_targets.py (read by S1).

  materials   the material masks of §4.6 (p01/matmasks.py) as Foot.* groups; spec 16's Skin.Foot on the foot's faces of
              Body.Mesh (Body.Mat.Skin.Foot, put back with the layer cache), Nail.Plate / .FreeEdge on the plates,
              the knit on the socks; materials.lint() (spec 18 §5.1)
  sock        Foot.<S>.SockTarget (hidden) and Sock.<S>.Body in Sock.Pair (p01/sock.py): rings of section hulls of the
              rendered foot with its nails, a membrane over the foot, 0.3 mm off; sock_* groups, UV.Real, Solidify,
              Subdivision and the knit's relief (Sock.GN.Knit)
  last        Foot.<S>.Last (hidden, bone-parented to foot.<S>) and its marker Empties in Foot.Lasts (p01/last.py)
  interfaces  the foot.* and sock.* keys of assets/interfaces.json (§7.1)

--render makes the closeup copies Foot.L.Isolate and Foot.R.Isolate after the cache is saved (§0 item 9,
§8.1: one foot alone, Subdivision render 3), gives them and the nails a placeholder skin for the Cycles tiers
(scripts/eval/lookdev_p01.py renders the foot in LookDev with spec 16's recipes), builds spec 17's hero scene in
this session for those tiers, and renders the part's presets (all but V6 unless --views names it) into
renders/01_foot/ with a contact sheet. The sock shows only in V7, the last only in V9; V6 renders render copies of
the lasts seated on the real boot's footbed at the hero headings (Foot.<S>.Last.Hero, spec 02 §0 items 2-3) and
lays their silhouettes on the reference boots (p01/v6_overlay.py). cli.py's --render has no hook for such a step,
so this script runs cli.run() itself.
"""
import json
import os
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/
from lib import cache, cli, env, interfaces, log, naming, replace  # noqa: E402
from lib import materials as M  # noqa: E402
from lib import sculpt as S  # noqa: E402
from lib.cli import Part  # noqa: E402
from parts.p01 import fields, footmetrics as fm, layers, nails, scanfit, scanref  # noqa: E402
from parts.p01 import last as LS  # noqa: E402
from parts.p01 import sock as SK  # noqa: E402
from parts.p01 import transfer as X  # noqa: E402

PART = Part(id="01", name="foot_ankle_sock", prefixes=("Foot.", "Sock.", "Frame.Foot."), keys=("foot.", "sock."),
            needs={"08": "Morgan.Rig"},
            provides=("Frame.Foot.L", "Frame.Foot.R", "Foot.L.Last", "Foot.R.Last", "Sock.L.Body", "Sock.R.Body"),
            stages=("sculpt", "nails", "masks", "contact", "frames",
                    "guides", "materials", "hair", "sock", "last", "weights", "interfaces"),
            presets="p01")
LATER = {"guides": "§4.5, session 2", "hair": "§6.1, session 2", "weights": "§7.2 and §7.4's sock attachment"}
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


def _transfer_cfg(ctx):
    """The scan transfer's settings (params.json "transfer" over transfer.DEFAULTS), with the scans' paths taken
    through lib/cache.asset, so the build's key carries the files' hashes (Jeff, 2026-10-17: the foot's large forms
    are a real foot's)."""
    cfg = X.config(ctx.params)
    if cfg.get("on"):
        sid = str(cfg["scan"])
        cfg["_paths"] = {c: cache.asset(scanref.ply_rel(sid, c), ctx) for c in ("mBW", str(cfg.get("loaded", "fBW")))}
    return cfg


def _ensure_transfer(ctx, body, st):
    """A stage run alone (--stage nails..frames) has no transfer record on the feet: the sculpt's positions are
    recomputed (about 2 s a foot) so the placement, the masks and the turned toe axes are the build's own."""
    cfg = st.get("transfer_cfg") or _transfer_cfg(ctx)
    st["transfer_cfg"] = cfg
    if cfg.get("on") and any(getattr(body.feet[s], "transfer", None) is None for s in fields.SIDES):
        body.positions(fields.amounts(ctx.params), fields.options(ctx.params), transfer=cfg)
    return cfg


# --------------------------------------------------------------------------- stages

def stage_sculpt(ctx, scope, ob, st):
    """§4.2-4.3: the landmark sculpt, toes and nail beds as the Foot.Sculpt key (basis + sculpt). The
    loaded foot is made from it, so a re-run of this stage alone wants contact after it (--stage sculpt..contact)."""
    _drop(ob, "Foot.Sculpt")
    body = _sculpt_body(ob, st)
    a = fields.amounts(ctx.params)
    cfg = st["transfer_cfg"] = _transfer_cfg(ctx)
    co = body.positions(a, fields.options(ctx.params), transfer=cfg)
    S.key_from_positions(ob, "Foot.Sculpt", co / 1000.0, base=body.co / 1000.0)
    st["amounts"] = a
    for side in fields.SIDES:
        foot = body.feet[side]
        for what in ("mtp_lift", "webs_closed", "nail_shift", "contacts_resolved"):
            if getattr(foot, what, None):
                log.info("part 01", f"{side} {what}: {getattr(foot, what)}")
        rec = getattr(foot, "transfer", None)
        if rec is not None:
            last = rec["fit"][-1]
            log.info("part 01", f"{side} transfer onto scan {cfg['scan']} mBW: {last['n']}/{last['of']} vertices on it, "
                     f"limit residual rms {last['rms']} max {last['max']} mm; keep {int((rec['keep'] > 0.5).sum())} "
                     f"vertices; prewarp {json.dumps(rec.get('prewarp'))}; leg {json.dumps(rec.get('leg'))}; "
                     f"close {json.dumps(rec.get('close'))}")


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
    _ensure_transfer(ctx, body, st)
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
            axis = foot.frame.vec_to_w((getattr(foot, "axis_now", None) or {}).get(k, T["a"]))
            w, vis, fe, thick = nails.PLATES[k]
            name = naming.name("Foot", side, "Nail", str(k))
            radius = (getattr(foot, "nail_radius", None) or fields.NAIL_RADIUS)[k]
            me, dims, frame = nails.build_plate(name, ob, co, faces[k], axis, thick, fe, radius,
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
    _drop(ob, *names, "Foot.ScanKeep")
    body = _sculpt_body(ob, st)
    cfg = _ensure_transfer(ctx, body, st)
    if cfg.get("on"):
        names.append("Foot.ScanKeep")   # the skin between the toes the scan transfer kept (transfer.keep_mask)
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
        if "Foot.ScanKeep" in W:
            W["Foot.ScanKeep"][foot.R] = foot.transfer["keep"]
    for nm in names:
        _set_group(ob, nm, W[nm] * bodymask)


def stage_contact(ctx, scope, ob, st):
    """§4.7: Foot.Contact, the loaded foot over the sculpted one (value 0 at rest; the pose sets 1.0 on the
    right and 0.85 on the left)."""
    _drop(ob, "Foot.Contact")
    body = _sculpt_body(ob, st)
    cfg = _ensure_transfer(ctx, body, st)
    rest = _sculpted_world(ob)
    loaded = rest.copy()
    for side in fields.SIDES:
        foot = body.feet[side]
        q = foot.frame.to_f(rest[foot.R])
        loaded[foot.R] = foot.frame.to_w(fields.contact(body, side, q, transfer=cfg))
        rec = getattr(foot, "transfer_loaded", None)
        if rec is not None:
            last = rec["fit"][-1]
            log.info("part 01", f"{side} loaded key from scan {cfg['scan']} {cfg.get('loaded', 'fBW')}: limit residual rms "
                     f"{last['rms']} max {last['max']} mm; leg {json.dumps(rec.get('leg'))}; laid on the seated scan by "
                     f"{json.dumps(body.reference(cfg, str(cfg.get('loaded', 'fBW'))).info.get('registered'))}")
    S.key_from_positions(ob, "Foot.Contact", loaded / 1000.0, base=rest / 1000.0, value=0.0)


def stage_frames(ctx, scope, ob, st):
    """§4.14: Frame.Foot.L/R, frame F of each sculpted foot as an Empty, for spec 17's presets."""
    from mathutils import Matrix
    scope.clear("Frame.Foot.L")
    scope.clear("Frame.Foot.R")
    m = fm.read(ob)
    ix = fm.index(ob, m)
    body = _sculpt_body(ob, st)
    cfg = _ensure_transfer(ctx, body, st)
    for side in fields.SIDES:
        f = fm.frame(m, ix, side)
        e = scope.new_object(naming.name("Frame", None, "Foot", side), None)
        e.empty_display_type, e.empty_display_size = "ARROWS", 0.06
        e.matrix_world = Matrix(f.matrix().tolist())
        e["p01_doc"] = "frame F (spec 01): origin at the pternion on the floor, +Z up, toes toward -Y"
        rec = getattr(body.feet[side], "transfer", None)
        if cfg.get("on") and rec is not None:
            # where the reference scan lies on this foot: world mm = M @ (x, y, z, 1) of a point in the scans' frame
            # (scanref.load's, the right foot mirrored back by frame F), for the trial's dense transfer and renders
            e["p01_scan"] = json.dumps({"id": str(cfg["scan"]), "rest": "mBW", "loaded": str(cfg.get("loaded", "fBW")),
                                        "M": _scan_matrix(body.feet[side], rec).round(6).tolist()})


def _scan_matrix(foot, rec):
    """4 x 4 (mm) taking the scans' frame onto the world for one foot: transfer.from_frame then frame F (F0, the
    basis foot's, in which the sculpt works) to world."""
    import numpy as np
    P = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    W = foot.frame.to_w(X.from_frame(P, rec["R"], rec["o"]))
    M = np.eye(4)
    M[:3, 3] = W[0]
    M[:3, :3] = (W[1:] - W[0]).T
    return M


def _joint_cubes(ob, side, co_world):
    """{cube name ("toe-1-1", "ankle", "foot-1", ...): world mm} of one side's MakeHuman joint cubes on the sculpted
    rest body: the transfer carries each toe's cubes with its skin (transfer.follow), so these are the toes' joints
    now (toe 5's moved back with it)."""
    import numpy as np
    sl = "l" if side == "L" else "r"
    pre = f"joint-{sl}-"
    names = [g.name for g in ob.vertex_groups if g.name.startswith(pre + "toe-") or g.name in (pre + "ankle", pre + "foot-1", pre + "foot-2")]
    W = S.group_weights_many(ob, names)
    out = {}
    for n in names:
        sel = W[n] > 0.5
        if sel.any():
            out[n[len(pre):]] = co_world[sel].mean(axis=0)
    return out


def _toe_line(m, ix, f, side, cubes_f):
    """The toes' line in F for the sock's regions: the 1st and 5th MTP joints and the hallux's and toe 5's tips."""
    import numpy as np
    co = m.co * 1000.0
    tips = {}
    for k in (1, 5):
        q = f.to_f(co[ix.toe[side][k]])
        tips[k] = q[np.argmin(q[:, 1])]
    return {"mtp1": tuple(cubes_f["toe-1-1"][:2]), "mtp5": tuple(cubes_f["toe-5-1"][:2]),
            "tip1": tuple(tips[1][:2]), "tip5": tuple(tips[5][:2])}


def _assign_sock_materials(sob):
    """Spec 16's knit on a sock: Knit.Sock.WoolNylon everywhere, its .Reinforced on the heel pocket and the toe cap
    (§3.6, §5.4; faces whose corners all weigh 0.5 or more in sock_heel or sock_toe)."""
    sob.data.materials.clear()
    M.assign(sob, "Knit.Sock.WoolNylon")
    for g in ("sock_heel", "sock_toe"):
        if sob.vertex_groups.get(g) is not None:
            M.assign(sob, "Knit.Sock.WoolNylon.Reinforced", faces=g)


# spec 01 §3.3: the lunula shows on the hallux (a 3.5 mm crescent) and faintly on toe 2; the right hallux carries an
# old trauma ridge 5 mm from the fold (the values lookdev_p01.py dressed the nails with)
LUNULA_MM = {1: 3.5, 2: 1.5}
RIDGE_MM = {("R", 1): 5.0}


def stage_materials(ctx, scope, ob, st):
    """§5 on spec 16's library: the material masks of §4.6 (callus, corn, rub, pressure, toe redness, thin dorsum,
    scatter scale) as Foot.* groups; Skin.Foot on the foot's faces of Body.Mesh (Body.Mat.Skin.Foot), Nail.Plate and
    Nail.FreeEdge on each plate (its nail_coords written), the knit on the socks if they exist yet (the sock stage
    assigns its own); then materials.lint() over them."""
    import numpy as np
    from parts.p01 import matmasks
    _drop(ob, *matmasks.NAMES)
    body = _sculpt_body(ob, st)
    co = _sculpted_world(ob)
    nrm = S.vertex_normals(co, *body.topo)
    n = len(co)
    W = {nm: np.zeros(n) for nm in matmasks.NAMES}
    bodymask = np.zeros(n, bool)
    bodymask[body.m0.orig if body.m0.orig is not None else np.arange(n)] = True
    for side in fields.SIDES:
        foot = body.feet[side]
        f = fm.frame(fm.with_positions(body.m0, co), body.ix, side)
        q = f.to_f(co[foot.R])
        nq = f.vec_to_f(nrm[foot.R])
        cubes = {k: f.to_f(v) for k, v in _joint_cubes(ob, side, co).items()}
        got = matmasks.masks(q, nq, foot.w, cubes, side)
        for nm, w in got.items():
            W[nm][foot.R] = w
    for nm in matmasks.NAMES:
        if nm == "Foot.Corn.L4" and not W[nm].any():
            continue
        _set_group(ob, nm, W[nm] * bodymask)
    M.ensure_groups()
    M.assign(ob, "Skin.Foot", part="Body", faces="Foot.Region")
    plates = sorted((o for o in __import__("bpy").data.objects if o.name.startswith(("Foot.L.Nail.", "Foot.R.Nail."))),
                    key=lambda o: o.name)
    for nob in plates:
        side, k = nob.name.split(".")[1], int(nob.name.split(".")[-1])
        w, vis, fe, thick = nails.PLATES[k]
        free = M.nail_coords(nob, vis, fe, lunula_mm=LUNULA_MM.get(k, 0.0), ridge_mm=RIDGE_MM.get((side, k), 0.0))
        nob.data.materials.clear()
        M.assign(nob, "Nail.Plate")
        M.assign(nob, "Nail.FreeEdge", faces=free)
        sol = nob.modifiers.get("Solidify")
        if sol is not None:
            sol.material_offset_rim = 0   # each rim takes its own face's material (the sides and root stay plate)
    socks = [o for o in __import__("bpy").data.objects if o.name in ("Sock.L.Body", "Sock.R.Body")]
    for sob in socks:
        _assign_sock_materials(sob)
    st["lint"] = _lint([ob] + plates + socks)


def _lint(objs):
    """materials.lint() over the part's materials on these objects: {"errors": [...], "warnings": [...]}."""
    issues = M.lint(list(objs))
    out = {"errors": sorted({f"{i.code} {i.target}: {i.message}" for i in issues if i.level == "error"}),
           "warnings": sorted({f"{i.code} {i.target}: {i.message}" for i in issues if i.level == "warning"})}
    for e in out["errors"]:
        log.info("part 01", f"lint error: {e}")
    return out


def stage_sock(ctx, scope, ob, st):
    """§4.10-4.11: Foot.<S>.SockTarget (the envelope the sock wraps, hidden) and Sock.<S>.Body (sock.py) on the rest
    foot's rendered surface with the nails; the regions as sock_* groups, UV.Real, the modifiers, the knit."""
    import bpy
    import numpy as np
    for p in ("Sock.L", "Sock.R", "Foot.L.SockTarget", "Foot.R.SockTarget"):
        scope.clear(p)
    pair = bpy.data.collections.get("Sock.Pair")
    if pair is None or pair.library is not None:
        pair = scope.collection("Sock.Pair")
    lasts = bpy.data.collections.get("Foot.Lasts")
    if lasts is None or lasts.library is not None:
        lasts = scope.collection("Foot.Lasts")
    m = fm.read(ob)
    ix = fm.index(ob, m)
    co = _sculpted_world(ob)
    group = SK.knit_group()
    st["sock"] = {}
    for side in fields.SIDES:
        f = fm.frame(m, ix, side)
        plates = [bpy.data.objects[n] for n in (f"Foot.{side}.Nail.{k}" for k in fields.TOES) if n in bpy.data.objects]
        V, T = SK.skin_read(ob, f, 0.0, plates)
        cubes = {k: f.to_f(v) for k, v in _joint_cubes(ob, side, co).items()}
        toe = _toe_line(m, ix, f, side, cubes)
        L = fm.foot(m, ix, side, toes=False)["foot_length"]
        res = SK.make(V, T, toe, L)
        tgt = scope.new_object(f"Foot.{side}.SockTarget", SK.build_mesh(f"Foot.{side}.SockTarget", res["target"], f, uv=False),
                               lasts)
        tgt.hide_render = True
        tgt.display_type = "WIRE"
        name = f"Sock.{side}.Body"
        sob = scope.new_object(name, SK.build_mesh(name, res["inner"], f), pair)
        reg = res["regions"]
        groups = {f"sock_{k}": v for k, v in reg.items()}
        groups["sock_thickness"] = res["thickness"] / SK.T_MAX
        SK.set_groups(sob, groups)
        for g in ("sock_shell", "sock_rim"):
            sob.vertex_groups.new(name=g)
        SK.add_modifiers(sob, group)
        sob["p01_doc"] = ("spec 01 §4.11: the sock's inner surface 0.3 mm off Foot.%s.SockTarget; rings x %d around "
                          "(ring 0 the cuff's top); modifiers Solidify (sock_thickness x 3 mm), Subdivision, Knit" % (side, SK.N_AROUND))
        sob["p01_rings"] = int(res["inner"].shape[0])
        sob["p01_kinds"] = json.dumps([k for k, _, _ in res["stations"]])
        sob["p01_corner"] = [float(c) for c in res["corner"]]
        _assign_sock_materials(sob)
        st["sock"][side] = {"rings": int(res["inner"].shape[0]), "corner": [round(c, 2) for c in res["corner"]],
                            "foot_length": L}
        log.info("part 01", f"{side} sock: {res['inner'].shape[0]} rings x {SK.N_AROUND}, fan corner "
                 f"{np.round(res['corner'], 1).tolist()}, target bridged up to "
                 f"{float((res['target'] - res['hull'])[..., 2].min()):.2f} mm under its hull")
    if "lint" in st or any(o.name.startswith("Body.Mat.") for o in ob.data.materials if o):
        st["lint"] = _lint([ob] + [o for o in bpy.data.objects if o.name.startswith(("Foot.L.Nail.", "Foot.R.Nail."))]
                           + [bpy.data.objects[f"Sock.{s}.Body"] for s in fields.SIDES])


def _malleoli(fine, f):
    """The malleoli on the rendered surface (§3.1, §8.2; footmetrics.ankle's apexes), as F points: the lateral apex,
    and the medial one where the profile has its peak, else (the scan: no apex on its medial profile) its widest
    point. Each point is the section's extreme at the apex's height within the bones' band."""
    import numpy as np
    a = fm.ankle(fine, f)
    out = {"resolved": int(a["malleoli_resolved"]), "medial_prom": float(a["malleolus_medial_prom"])}
    for key, sign in (("lateral", 1.0), ("medial", -1.0)):
        z = a[f"malleolus_{key}_z"]
        q = fm.horizontal(fine, f, z)
        q = q[(q[:, 1] >= -90.0) & (q[:, 1] <= -40.0)]
        p = q[np.argmax(sign * q[:, 0])]
        out[key] = np.array([p[0], p[1], z])
    return out


def stage_last(ctx, scope, ob, st):
    """§4.13 and §0 item 3: Foot.<S>.Last (last.py), from the rest foot loaded (Foot.Contact 1.0), the sock at its
    loaded thickness, the allowances, the insole plane, the toe box, the 12 degree toe spring; bone-parented to
    foot.<S>; its groups and marker Empties; hidden."""
    import bpy
    import numpy as np
    from mathutils import Matrix
    for side in fields.SIDES:
        scope.clear(f"Foot.{side}.Last")
    lasts = bpy.data.collections.get("Foot.Lasts")
    if lasts is None or lasts.library is not None:
        lasts = scope.collection("Foot.Lasts")
    rig = bpy.data.objects[RIG]
    m = fm.read(ob)
    ix = fm.index(ob, m)
    fine = fm.subdivided(ob)
    rest = _sculpted_world(ob)
    kb = ob.data.shape_keys.key_blocks.get("Foot.Contact")
    old = kb.value
    kb.value = 1.0
    loaded = S.mix(ob) * 1000.0
    kb.value = old
    beds = S.group_weights_many(ob, [f"Foot.NailBed.{k}" for k in fields.TOES])
    st["last"] = {}
    for side in fields.SIDES:
        f = fm.frame(m, ix, side)
        plates = [bpy.data.objects[n] for n in (f"Foot.{side}.Nail.{k}" for k in fields.TOES) if n in bpy.data.objects]
        shift = LS.nail_shift(ob, f, side, rest, loaded, beds)
        V, T = SK.skin_read(ob, f, 1.0, plates, shift)
        tree = SK.bvh(V, T)
        cubes = {k: f.to_f(v) for k, v in _joint_cubes(ob, side, rest).items()}
        toe = _toe_line(m, ix, f, side, cubes)
        v = fm.foot(m, ix, side, toes=False)
        Lf = v["foot_length"]
        b1, b5 = _ball_points(m, ix, f, side, cubes)
        z_b = LS.insole_z()
        sts, corner = SK.stations(V, top_z=LS.COLLAR_Z, fine_from=toe["tip5"][1] + 10.0)

        def off(G0, N0, kept):
            reg = SK.regions(G0, N0, Lf, toe, float(G0[..., 1].max()))
            t = SK.thickness(reg, loaded=True)
            a = LS.regions(G0, N0, Lf, float(0.5 * (b1[1] + b5[1])))
            return SK.OFFSET_MM + LS.FACET_MM + t + LS.ALLOW["ball_side"] * a["ball"] + LS.ALLOW["instep"] * a["instep"] \
                + LS.ALLOW["heel_side"] * a["heel"]

        # the toe allowance from the standing, socked toe (Jeff, 2026-10-27: "Reality"; §0 item 3 and §4.13 notes): the
        # loaded foot's toe with the sock's gap and toe thickness ahead of it; was the stated foot (038's scan at 274.3) + 15
        L_decl = float(scanref.LENGTH)
        sk_front = LS.socked_toe_y(V)
        G, kept, info = LS.build(V, T, sts, tree, off, sk_front - LS.TOE_ALLOWANCE, b1, b5, z_b,
                                 taper_from=toe["tip5"][1] + 10.0)
        name = f"Foot.{side}.Last"
        me = SK.build_mesh(name, G, f, face_list=LS.faces(G.shape[0], SK.N_AROUND), uv=False)
        lob = scope.new_object(name, me, lasts)
        groups = LS.groups(G, Lf, b1, b5, z_b)
        SK.set_groups(lob, groups)
        nails.parent_to_bone(lob, rig, f"foot.{side}")
        lob.hide_render = True
        lob["p01_doc"] = ("spec 01 §4.13: the rest foot loaded (Foot.Contact 1.0), socked at the loaded thickness, with "
                          "the allowances; insole plane z %.2f mm (frame F); length %.1f, the tip %.0f mm ahead of the "
                          "standing socked toe" % (z_b, info["length"], LS.TOE_ALLOWANCE))
        lob["p01_insole_z"] = float(z_b)
        lob["p01_socked_front_y"] = sk_front
        lob["p01_ball"] = json.dumps({"b1": [float(c) for c in b1], "b5": [float(c) for c in b5]})
        lob["p01_foot_length"] = L_decl
        lob["p01_foot_length_cage"] = float(Lf)
        lob["p01_kinds"] = json.dumps([k for k, _, _ in kept])
        mall = _malleoli(fine, f)
        tip = G.reshape(-1, 3)[np.argmin(G.reshape(-1, 3)[:, 1])]
        pt = G.reshape(-1, 3)[np.argmax(G.reshape(-1, 3)[:, 1])]
        marks = {"Pternion": (pt[0], pt[1], z_b), "Ball1": (b1[0], b1[1], z_b), "Ball5": (b5[0], b5[1], z_b),
                 "ToeTip": tuple(tip), "AnkleAxis.Medial": tuple(mall["medial"]),
                 "AnkleAxis.Lateral": tuple(mall["lateral"])}
        bpy.context.view_layer.update()
        for k, p in marks.items():
            e = scope.new_object(f"{name}.{k}", None, lasts)
            e.empty_display_type, e.empty_display_size = "SPHERE", 0.004
            w = f.to_w(np.asarray(p, float)) / 1000.0
            e.parent = lob
            e.matrix_parent_inverse = lob.matrix_world.inverted()
            e.matrix_world = Matrix.Translation(w.tolist())
            e["p01_frame_mm"] = [round(float(c), 4) for c in p]
        st["last"][side] = {"length": round(info["length"], 2), "k": round(info["k"], 4), "insole_z": z_b,
                            "medial_resolved": mall["resolved"], "socked_front_y": round(sk_front, 2)}
        log.info("part 01", f"{side} last: length {info['length']:.2f} (the tip {LS.TOE_ALLOWANCE} ahead of the standing "
                 f"socked toe at y {sk_front:.2f}; foot {L_decl:.2f}), toe box x{info['k']:.3f} from y "
                 f"{info['stretch_from']:.1f}, insole z {z_b:.2f}")


def _ball_points(m, ix, f, side, cubes_f):
    """The 1st metatarsal head's medial point and the 5th's lateral point (F): the foot's medial and lateral extremes
    (z 5-40, on the cage) across its 1st and 5th MTP joints, the joint cubes the rig's toes bend about. (§8.2's ball
    readings, the plan's widest points, fall 25-35 mm behind them on the transferred foot: 038's border bulges behind
    his heads.)"""
    import numpy as np
    q = f.to_f(m.co[ix.region[side]] * 1000.0)
    q = q[(q[:, 2] > 5.0) & (q[:, 2] < 40.0)]
    out = []
    for name, sign in (("toe-1-1", -1.0), ("toe-5-1", 1.0)):
        y = cubes_f[name][1]
        sl = q[np.abs(q[:, 1] - y) < 5.0]
        p = sl[np.argmax(sign * sl[:, 0])]
        out.append(np.array([p[0], y, p[2]]))
    return out[0], out[1]


# the bones spec 08 places from part 01's joints (§7.1): head and tail cubes on the sculpted rest body
JOINT_BONES = {"toe1-1": ("toe-1-1", "toe-1-2"), "toe1-2": ("toe-1-2", "toe-1-3")}
for _k in (2, 3, 4, 5):
    for _j in (1, 2, 3):
        JOINT_BONES[f"toe{_k}-{_j}"] = (f"toe-{_k}-{_j}", f"toe-{_k}-{_j + 1}")


def stage_interfaces(ctx, scope, ob, st):
    """§7.1: the foot.* and sock.* keys in assets/interfaces.json (world mm, rest pose): every toe bone's head and tail
    at the sculpted joints, the foot bone's head on the ankle axis through the malleoli (MPFB's ankle cube sits about
    20 mm below them: S1's vert-decr target, §4.1 note), heel, ball and toes_master; the ankle axis; the last's
    markers and its plane; the sock's top and thickness. Not under --check (it saves nothing)."""
    import bpy
    import numpy as np
    m = fm.read(ob)
    ix = fm.index(ob, m)
    fine = fm.subdivided(ob)
    co = _sculpted_world(ob)
    rig = bpy.data.objects[RIG]
    vals = {}

    def r(p):
        return [round(float(c), 4) for c in p]

    for side in fields.SIDES:
        f = fm.frame(m, ix, side)
        cubes = _joint_cubes(ob, side, co)
        pre = f"foot.{side}"
        for bone, (h, t) in JOINT_BONES.items():
            vals[f"{pre}.joint.{bone}.head"] = r(cubes[h])
            vals[f"{pre}.joint.{bone}.tail"] = r(cubes[t])
        mall = _malleoli(fine, f)
        med, lat = f.to_w(mall["medial"]), f.to_w(mall["lateral"])
        centre = 0.5 * (med + lat)
        d = lat - med
        vals[f"{pre}.ankle_axis"] = {"medial": r(med), "lateral": r(lat), "centre": r(centre),
                                     "direction": r(d / np.linalg.norm(d)), "medial_resolved": bool(mall["resolved"] == 2),
                                     "source": "spec 01 §7.1: the malleoli on the level-2 surface (footmetrics.ankle)"}
        tail = np.array(rig.data.bones[f"foot.{side}"].tail_local) * 1000.0
        vals[f"{pre}.joint.foot.head"] = r(centre)
        vals[f"{pre}.joint.foot.tail"] = r(tail)
        vals[f"{pre}.joint.lowerleg02.tail"] = r(centre)
        pt = f.to_w(np.array([0.0, 0.0, 0.0]))
        vals[f"{pre}.joint.heel.head"] = r(pt)
        vals[f"{pre}.joint.heel.tail"] = r(pt + np.array([0.0, 20.0, 0.0]))
        b1, b5 = _ball_points(m, ix, f, side, {k: f.to_f(p) for k, p in cubes.items()})
        b1w = f.to_w(b1)
        vals[f"{pre}.joint.ball.head"] = r(b1w)
        vals[f"{pre}.joint.ball.tail"] = r(b1w + np.array([20.0, 0.0, 0.0]))
        vals[f"{pre}.joint.toes_master.head"] = r(cubes["toe-1-1"])
        vals[f"{pre}.joint.toes_master.tail"] = r(cubes["toe-5-1"])
        vals[f"{pre}.frame"] = {"origin": r(f.o), "heading_deg": round(f.heading_deg(), 4)}
        lob = bpy.data.objects.get(f"Foot.{side}.Last")
        if lob is not None:
            for mk in ("Pternion", "Ball1", "Ball5", "ToeTip", "AnkleAxis.Medial", "AnkleAxis.Lateral"):
                e = bpy.data.objects.get(f"Foot.{side}.Last.{mk}")
                if e is not None:
                    vals[f"{pre}.last.{mk}"] = r(np.array(e.matrix_world.translation) * 1000.0)
            lm = np.array([lob.matrix_world @ vv.co for vv in lob.data.vertices]) * 1000.0
            lq = f.to_f(lm)
            vals[f"{pre}.last.insole_z"] = round(float(lob["p01_insole_z"]), 4)
            vals[f"{pre}.last.length"] = round(float(lq[:, 1].max() - lq[:, 1].min()), 4)
            vals[f"{pre}.last.toe_spring_deg"] = LS.TOE_SPRING_DEG
            vals[f"{pre}.last.collar_z"] = LS.COLLAR_Z
        sob = bpy.data.objects.get(f"Sock.{side}.Body")
        if sob is not None:
            vals[f"sock.{side}.top_z"] = SK.TOP_Z
            vals[f"sock.{side}.cuff_z"] = SK.CUFF_Z
            vals[f"sock.{side}.thickness_mm"] = dict(SK.THICK, sole_loaded=round(SK.THICK["sole"] * SK.LOADED_SOLE, 4),
                                                     gap=SK.OFFSET_MM)
    if ctx.args.check:
        st["interfaces"] = {"written": False, "keys": len(vals)}
        return
    changed = interfaces.write(PART, vals, replace=True)
    st["interfaces"] = {"written": True, "keys": len(vals), "changed": len(changed)}
    log.info("part 01", f"interfaces: {len(vals)} foot.* / sock.* keys, {len(changed)} changed")


def stage_later(name):
    def run(ctx, scope, ob, st):
        st.setdefault("later", []).append(f"{name} ({LATER[name]})")
    return run


STAGES = {"sculpt": stage_sculpt, "nails": stage_nails, "masks": stage_masks, "contact": stage_contact,
          "frames": stage_frames, "materials": stage_materials, "sock": stage_sock, "last": stage_last,
          "interfaces": stage_interfaces}
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
    for e in (st.get("lint") or {}).get("errors", []):
        ctx.warn(f"materials.lint: {e}")
    if (st.get("lint") or {}).get("warnings"):
        ctx.warn("materials.lint warnings: " + "; ".join(st["lint"]["warnings"]))
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


# The scan transfer (Jeff, 2026-10-17, spec 01 §0, §3.1 and §3.3 notes: "the foot's large forms are transferred from a
# CC0 scan"; transfer.py, params.json "transfer"): with it on, the targets below replace those above. They are the
# transferred foot's own readings (§8.2's definitions on the cage, the malleoli, heel and plan on the level-2 surface),
# 038's own where scan.py reads the same figure on the scan (scan_targets.json "scalars_unloaded" / "scalars_loaded"),
# with §8.2's tolerances, so a later build that drifts off the scan fails; the ANSUR and estimated values they replace
# are in the notes. Subject 038 seated, scaled to 274.3 mm
XSRC = "§0 (Jeff, 2026-10-17: the foot's large forms are transferred from a CC0 scan, subject 038)"
XFER_TIP_Y = {1: -275.1, 2: -275.2, 3: -264.8, 4: -251.2, 5: -224.5}   # the cage's tips (1-3 mm past the rendered
XFER_TOE_W = {1: 34.8, 2: 19.7, 3: 20.1, 4: 21.2, 5: 20.2}             # surface's); toe 5's base carried back 12 mm
XFER_TOE_H = {1: 30.2, 2: 17.6, 3: 17.2, 4: 19.9, 5: 18.7}
# round 3b's fixes (2026-10-27, §4.2 note): the hallux's wall laid against toe 2's along their length (transfer.close_pairs;
# they stood 1.5-3 mm apart at the tips), so both read wider in plan where they meet: the hallux 36.9 / 38.1 (left /
# right; the scan's toe line, which takes their fused cleft whole, reads 33-34), toe 2 21.5 / 22.0
XFER_TOE_W.update({1: 37.4, 2: 21.7})
XFER_TARGETS = {
    "ball_length": (189.5, 3.0, XSRC + ": the medial border's widest point, 20 mm behind ANSUR's first head (210)"),
    "heel_breadth": (67.9, 3.0, XSRC + ": 038's own 67.9 (scan.py's reading)"),
    "heel_widest": (67.3, 3.0, XSRC),
    "heel_width_z10": (62.9, 3.0, XSRC + ": 038's own"), "heel_width_z20": (66.1, 3.0, XSRC + ": 038's own"),
    "heel_width_z30": (60.8, 3.0, XSRC + ": 038's own"),
    "bimalleolar": (67.4, 2.0, XSRC + ": the scan's ankle (ANSUR 76)"),
    "malleolus_lateral_z": (84.2, 2.0, XSRC + " (ANSUR 76)"),
    "malleolus_medial_z": (None, None, XSRC + ": no apex on the scan's medial profile, its widest point read"),
    "heel_ankle_circ": (361.9, 6.0, XSRC + " (ANSUR 353)"),
    "instep_circ": (262.0, 6.0, XSRC + " (the estimate 246)"),
    "dorsum_h50": (86.8, 2.0, XSRC + ": the scan's high instep (the estimates 66 / 56 / 40)"),
    "dorsum_h60": (75.1, 2.0, XSRC), "dorsum_h70": (60.1, 2.0, XSRC),
    "arch_medial_45": (18.9, 3.0, XSRC + ": 038's own"),
    "lateral_clear_50": (1.1, 1.5, XSRC + ": 038's own"),
    "pternion_z": (33.7, 2.0, XSRC + ": 038's own"),
}
for _k in XFER_TIP_Y:
    XFER_TARGETS[f"toe{_k}_tip_y"] = (XFER_TIP_Y[_k], 2.0, XSRC + ": the scan's cascade (§3.3 note)")
    XFER_TARGETS[f"toe{_k}_width"] = (XFER_TOE_W[_k], 2.0, XSRC)
    XFER_TARGETS[f"toe{_k}_height"] = (XFER_TOE_H[_k], 2.0, XSRC)
XFER_PLAN_TARGETS = {
    "plan_b50": (82.3, 3.0, XSRC),
    "plan_mid_ratio": ([0.78, 0.86], None, XSRC + " (0.82-0.92 before)"),
    "plan_widest_pct": ([74.0, 86.0], None, XSRC + ": widest across the toes' bases (60-76 before)"),
}
# the toes pressed together as the scan's are (the hallux touches toe 2; Jeff's 4.5 mm gap gave way to the scan); a few
# cage vertices of a pressed pair read up to 0.2 mm inside the neighbour (fields.resolve_contacts' gap)
XFER_GAPS = {"1-2": ([-0.25, 3.0], XSRC + ": the hallux against toe 2, as the scan's"),
             "other": ([-0.25, 60.0], XSRC + ": touching, never crossing by more than the cage's 0.2 mm")}
XFER_CONTACT_ARCH = ([3.0, 8.0], XSRC + ": the cage reads 3.8 where the scan's own medial border drops 5.5")
# the last's length once its tip stands 15 mm ahead of the standing, socked toe (Jeff, 2026-10-27, "Reality"; §4.13 note;
# 289.3 before, the stated foot + 15)
LAST_LENGTH_MM = 297.0
SCAN_REF_RMS = {"plan": 1.5, "heel": 1.5, "sole": 1.0}   # the rendered surface against the scan it came from (mm)
# part 01's hallux plate on the scan's broad, flat-topped toe: built on §3.3's 19.5 x 13.8 bed it reads 20.9 x 16.7 with a
# 9.5 mm radius (its buried sides dive further off a flat dorsum; 19.6 x 15.4 and 11.0 on MakeHuman's rounder toe). A
# smaller bed or a wider arc tried for it (18.8 x 14.5, 14 mm) read 8.4 mm across and lost the free edge's reading. The
# rendered nails are the trial's (research/foot_hires, toes.PARAMS "nail1": 18.5 x 14.6)
XFER_NAIL1 = {"width": (20.9, 1.0), "length": (16.7, 1.0), "radius": (9.5, 1.5)}


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


def _evaluated_world(ob, on=None, levels=None):
    """World mm of an object's evaluated vertices with some modifiers switched (on: {name: bool}) and the
    Subdivision at `levels` for the read; everything put back."""
    import bpy
    import numpy as np
    saved = []
    try:
        for md in ob.modifiers:
            if on and md.name in on:
                saved.append((md, "show_viewport", md.show_viewport))
                md.show_viewport = on[md.name]
            if levels is not None and md.type == "SUBSURF":
                saved.append((md, "levels", md.levels))
                md.levels = levels
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        M = np.array(ev.matrix_world)
        ev.to_mesh_clear()
        return (co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]) * 1000.0
    finally:
        for md, k, v in reversed(saved):
            setattr(md, k, v)


# §3.6's thickness at six probes (§8.2): (name, region, how the probe vertex is chosen on the base grid in F)
SOCK_PROBES = (("cuff", "cuff"), ("leg", "leg"), ("instep", "leg"), ("heel", "heel"), ("sole", "sole"), ("toe", "toe"))


def _sock_probe(G, kind, L, toe):
    """The base-grid vertex (ring, column) a thickness probe reads: the cuff and leg at z 244 / 160 on the lateral
    side, the instep on top at 50 % L, the heel on the back at z 25, the sole under 62 % L, the toe cap on top 12 mm
    behind the hallux's tip."""
    import numpy as np
    P = G.reshape(-1, 3)
    if kind == "cuff":
        w = -np.abs(P[:, 2] - 244.0) * 5 + P[:, 0]
    elif kind == "leg":
        w = -np.abs(P[:, 2] - 160.0) * 5 + P[:, 0]
    elif kind == "instep":
        w = np.where(np.abs(P[:, 1] + 0.5 * L) < 3.0, P[:, 2], -1e9)
    elif kind == "heel":
        w = -np.abs(P[:, 2] - 25.0) * 5 + P[:, 1]
    elif kind == "sole":
        w = -np.abs(P[:, 1] + 0.62 * L) * 5 - P[:, 2] - np.abs(P[:, 0])
    else:
        w = -np.abs(P[:, 1] - (toe["tip1"][1] + 12.0)) * 5 + P[:, 2]
    return int(np.argmax(w))


def _measure_sock(ob, sob, side, m, ix, add):
    """§8.2's sock checks: the top, the thickness at six probes (Solidify alone), the ribs' relief, the stitch pitch,
    the clearance of the inner surface (render level 2) from the skin and nails, the toes' clefts bridged."""
    import bpy
    import numpy as np
    from lib import measure as ME
    f = fm.frame(m, ix, side)
    plates = [bpy.data.objects[n] for n in (f"Foot.{side}.Nail.{k}" for k in fields.TOES) if n in bpy.data.objects]
    V, T = SK.skin_read(ob, f, 0.0, plates)
    tree = SK.bvh(V, T)
    n0 = len(sob.data.vertices)
    rings = int(sob["p01_rings"])
    kinds = json.loads(sob["p01_kinds"])
    G = f.to_f(np.array([v.co for v in sob.data.vertices]) * 1000.0).reshape(rings, SK.N_AROUND, 3)
    L = fm.foot(m, ix, side, toes=False)["foot_length"]
    co = _sculpted_world(ob)
    cubes = {k: f.to_f(p) for k, p in _joint_cubes(ob, side, co).items()}
    toe = _toe_line(m, ix, f, side, cubes)
    src = "§3.6 (Darn Tough T4033 class cushion boot sock)"
    full = f.to_f(_evaluated_world(sob))
    add(f"sock_top_z.{side}", round(float(full[:, 2].max()), 2), SK.TOP_Z, 1.0, src + ": the cuff's top")
    add(f"sock_cuff_height.{side}", round(SK.TOP_Z - SK.CUFF_Z, 2), 32.0, 1.0, src + ": the welt, folded double")
    sol = _evaluated_world(sob, on={"Subdivision": False, "Knit": False})
    if len(sol) >= 2 * n0:
        th = np.linalg.norm(sol[n0:2 * n0] - sol[:n0], axis=1)
        for name, reg in SOCK_PROBES:
            i = _sock_probe(G, name, L, toe)
            add(f"sock_thickness_{name}.{side}", round(float(th[i]), 3), SK.THICK[reg], 0.3,
                src + f": {name} (ray through the Solidify shell at ring {i // SK.N_AROUND})")
    # the ribs' relief on the outer shell at render level: the knit's displacement, leg and cuff
    on = _evaluated_world(sob, levels=2)
    off = _evaluated_world(sob, on={"Knit": False}, levels=2)
    if len(on) == len(off):
        d = np.linalg.norm(on - off, axis=1)
        z = f.to_f(off)[:, 2]
        for name, (z0, z1), want in (("leg", (110.0, 215.0), 2 * SK.RIB["leg"][1]),
                                     ("cuff", (234.0, 255.0), 2 * SK.RIB["cuff"][1])):
            sel = (z > z0) & (z < z1)
            if sel.any():
                add(f"sock_rib_relief_{name}.{side}", round(2.0 * float(np.percentile(d[sel], 99.5)), 3), want, 0.15,
                    "§3.6, §5.4: the %s rib's relief (geometry at render level 2)" % ("2x2" if name == "leg" else "1x1"))
    # the knit's stitch at the leg: 168 wales round the outer girth at z 160 (§3.6; §1.4 item 8's 1.5-1.8 mm pitch)
    try:
        loop = ME.girth(sob, 160.0, kind="loop")   # world z is frame F's
        add(f"sock_stitch_pitch.{side}", round(loop / SK.NEEDLES, 3), [1.5, 1.8], None,
            "§1.4 item 8 (§3.6, §4.11 note: %d wales): the outer girth at z 160 over the wales" % SK.NEEDLES)
        add(f"sock_girth_z160.{side}", round(loop, 1))
    except LookupError:
        pass
    # the inner surface as it renders (Subdivision 2 on the inner alone) against the skin and the nails
    inner = f.to_f(_evaluated_world(sob, on={"Solidify": False, "Knit": False}, levels=2))
    g = SK.signed_gaps(tree, inner)
    cand = np.nonzero(g < 0.0)[0]                       # the nearest face's side says inside: confirm by ray parity
    truly = cand[SK.inside_parity(tree, inner[cand])] if len(cand) else cand
    g[np.setdiff1d(cand, truly)] = np.abs(g[np.setdiff1d(cand, truly)])
    deep = int((g[truly] < -SK.INSIDE_MM).sum())
    g = g[np.isfinite(g)]
    add(f"sock_clearance_min.{side}", round(float(g.min()), 3), [-SK.INSIDE_MM, 1.0], None,
        "§1.4 item 8: no intersection with the skin or nails (the inner surface at render level 2, signed by ray parity)")
    add(f"sock_inside_vertices.{side}", deep, [0, 0], None,
        "§1.4 item 8 (deeper than %.2f mm under the skin)" % SK.INSIDE_MM, unit="")
    add(f"sock_clearance_p01.{side}", round(float(np.percentile(g, 1)), 3))
    # the toes' clefts bridged: the deepest point of the sock's sections across the toes inside their own hulls,
    # against the skin's own clefts there
    y0, y1 = min(toe["tip1"][1], toe["tip5"][1]), max(toe["mtp1"][1], toe["mtp5"][1])
    kept = [(k, np.array([0.0, float(G[i, :, 1].mean()), 0.0]), None) for i, k in enumerate(kinds)]
    add(f"sock_cleft_depth.{side}", round(SK.ring_concavity(G, kept, y0, y1), 3), [0.0, 2.0], None,
        "§1.4 item 8: no toe gaps through the sock (its sections across the toes dip at most 2 mm inside their hulls, "
        "where the skin's clefts are 14 deep: the toes show through as soft bumps, never as gaps)")
    add(f"skin_cleft_depth.{side}", round(SK.skin_cleft_depth(V, T, np.arange(y0 + 3.0, y1, 4.0)), 2))


def _last_bvh(lob):
    import numpy as np
    from mathutils.bvhtree import BVHTree
    me = lob.data
    me.calc_loop_triangles()
    tris = np.empty(len(me.loop_triangles) * 3, np.int64)
    me.loop_triangles.foreach_get("vertices", tris)
    co = np.array([lob.matrix_world @ v.co for v in me.vertices]) * 1000.0
    return co, tris.reshape(-1, 3)


def _measure_last(ob, lob, side, m, ix, add):
    """§8.2's last checks: its length and toe allowance, the room ahead of the loaded toes, the toe spring, the flat
    insole and the markers on it, the collar, the allowances over the loaded socked foot (rebuilt here from the same
    pieces: sock.py's envelope on the loaded surface at the loaded thickness) and that foot inside the last behind
    the ball line, and its girths."""
    import bpy
    import numpy as np
    from lib import measure as ME
    f = fm.frame(m, ix, side)
    co_w, tris = _last_bvh(lob)
    q = f.to_f(co_w)
    if f.s < 0:
        tris = tris[:, [0, 2, 1]]
    Lf = float(lob["p01_foot_length"])
    Lc = float(lob.get("p01_foot_length_cage", Lf))
    z_b = float(lob["p01_insole_z"])
    ball = json.loads(lob["p01_ball"])
    b1, b5 = np.array(ball["b1"]), np.array(ball["b5"])
    src = "§4.13, §0 item 3"
    length = float(q[:, 1].max() - q[:, 1].min())
    plates = [bpy.data.objects[n] for n in (f"Foot.{side}.Nail.{k}" for k in fields.TOES) if n in bpy.data.objects]
    rest = _sculpted_world(ob)
    kb = ob.data.shape_keys.key_blocks["Foot.Contact"]
    old = kb.value
    kb.value = 1.0
    loaded = S.mix(ob) * 1000.0
    kb.value = old
    beds = S.group_weights_many(ob, [f"Foot.NailBed.{k}" for k in fields.TOES])
    V1, T1 = SK.skin_read(ob, f, 1.0, plates, LS.nail_shift(ob, f, side, rest, loaded, beds))
    room = float(V1[:, 1].min() - q[:, 1].min())
    add(f"last_toe_room_loaded.{side}", round(room, 2), source=src + ": the last's tip ahead of the loaded foot's "
        "rendered toe (real boots leave 15-22 before the longest toe, research_dimensions §2)")
    rings = len(q) // SK.N_AROUND
    G = q[:rings * SK.N_AROUND].reshape(rings, SK.N_AROUND, 3)
    N = SK.grid_normals(G).reshape(-1, 3)
    Q = G.reshape(-1, 3)
    p, t, nrm = LS.ball_line(b1, b5)
    d = (Q[:, :2] - p) @ nrm
    bottom = N[:, 2] < -0.9
    ang = LS.spring_angle(Q[bottom], b1, b5, z_b)
    add(f"last_toe_spring_deg.{side}", None if ang is None else round(ang, 2), LS.TOE_SPRING_DEG, 0.5,
        src + ": the bottom's slope ahead of the 30 mm bend")
    kinds = json.loads(lob["p01_kinds"])
    foot_rows = np.repeat(np.array([k == "foot" for k in kinds]), SK.N_AROUND)
    flat = bottom & (d < -2.0) & foot_rows & (Q[:, 2] < z_b + 1.0)
    add(f"last_insole_flat.{side}", round(float(np.abs(Q[flat, 2] - z_b).max()), 3), [0.0, 0.05], None,
        src + ": the bottom of the sections across the foot, behind the ball line, on the insole plane")
    add(f"last_insole_points.{side}", int(flat.sum()), [200, 5000], None, src + ": the flat bottom's extent (vertices)",
        unit="")
    zs = []
    for mk in ("Pternion", "Ball1", "Ball5"):
        e = bpy.data.objects.get(f"Foot.{side}.Last.{mk}")
        if e is not None:
            zs.append(abs(float(f.to_f(np.array(e.matrix_world.translation) * 1000.0)[2]) - z_b))
    add(f"last_markers_off_plane.{side}", round(max(zs), 4) if zs else None, [0.0, 0.01], None,
        "§0 item 14, spec 08 §4.7(e): .Pternion, .Ball1, .Ball5 on the insole plane")
    add(f"last_collar_z.{side}", round(float(q[:, 2].max()), 2), LS.COLLAR_Z, 0.5, src + ": last_collar")
    add(f"last_insole_z.{side}", round(z_b, 3), unit="mm")
    # the loaded socked foot: the sock's envelope at the loaded thickness, the reference for the allowances
    tree1 = SK.bvh(V1, T1)
    co = _sculpted_world(ob)
    cubes = {k: f.to_f(pp) for k, pp in _joint_cubes(ob, side, co).items()}
    toe = _toe_line(m, ix, f, side, cubes)
    Sk = LS.socked_envelope(V1, T1, tree1, toe, Lc)
    # the toe allowance from the standing, socked toe (Jeff, 2026-10-27: "Reality"; was the stated foot length + 15,
    # 289.3, which left about 7 mm ahead of this toe and 9.7 ahead of the bare one)
    sock_room = float(LS.socked_toe_y(V1) - q[:, 1].min())
    add(f"last_toe_allowance.{side}", round(sock_room, 2), LS.TOE_ALLOWANCE, 0.5,
        src + " (Jeff, 2026-10-27: reality): the last's tip ahead of the standing socked toe, in plan")
    add(f"last_length.{side}", round(length, 2), LAST_LENGTH_MM, 1.0,
        src + " (Jeff, 2026-10-27): 15 mm ahead of the standing socked toe; spec 02 §0 item 1 note")

    def ext(P, sel, axis):
        return float(P[sel, axis].max() - P[sel, axis].min()) if sel.any() else None

    yb = float(0.5 * (b1[1] + b5[1]))
    for name, fn, want, tol in (
            ("ball_breadth", lambda P: ext(P, (np.abs(P[:, 1] - yb) < 8.0) & (P[:, 2] < 40.0), 0), 2 * LS.ALLOW["ball_side"], 1.5),
            ("instep_height", lambda P: float(P[np.abs(P[:, 1] + 0.5 * Lc) < 2.0, 2].max()), LS.ALLOW["instep"], 1.0),
            ("heel_width", lambda P: ext(P, (np.abs(P[:, 1] + 0.15 * Lc) < 2.0) & (np.abs(P[:, 2] - 20.0) < 3.0), 0),
             2 * LS.ALLOW["heel_side"], 1.0),
            ("heel_back", lambda P: float(P[(P[:, 2] > 5.0) & (P[:, 2] < 60.0), 1].max()), 0.0, 0.7)):
        a, b = fn(Q), fn(Sk)
        add(f"last_allow_{name}.{side}", None if a is None or b is None else round(a - b, 2), want, tol,
            src + f": the last over the loaded socked foot ({name.replace('_', ' ')})")
    from mathutils.bvhtree import BVHTree
    tl = BVHTree.FromPolygons(Q.tolist(), tris.tolist(), all_triangles=True)
    behind = Sk[((Sk[:, :2] - p) @ nrm) < -5.0]
    gaps = -SK.signed_gaps(tl, behind)   # inside the last is positive
    gaps = gaps[np.isfinite(gaps)]
    add(f"last_contains_sock.{side}", round(float(gaps.min()), 3), [-0.1, 30.0], None,
        src + ": the loaded socked foot behind the ball line inside the last (least depth, mm)")
    # seated on the real boot's footbed (spec 02 §0 item 2: heel seat 36, ball seat 24, about .Ball1-.Ball5): the pitch and
    # the ankle's height are readbacks (spec 02: about 4-4.5 degrees and 113)
    try:
        _, deg, ank = seated_last(lob, side)
        add(f"last_seat_pitch_deg.{side}", round(deg, 2), [3.5, 5.0], None,
            "spec 02 §0 item 2 (2026-10-27): the last turned heel-up until the seats 36 / 24 hold, about 4-4.5 degrees")
        add(f"last_seat_ankle_h.{side}", round(float(ank[2]), 1), source="spec 02 §0 item 3: the ankle axis's height "
            "in the hero pose, a readback (about 113)")
    except KeyError:
        pass
    for name, plane in (("ball", {"point": f.to_w(np.array([p[0], p[1], 20.0])), "normal": f.vec_to_w(np.array([nrm[0], nrm[1], 0.0]))}),
                        ("instep", {"point": f.to_w(np.array([0.0, -0.5 * Lc, 30.0])), "normal": f.ey})):
        try:
            add(f"last_girth_{name}.{side}", round(ME.girth(lob, plane, kind="tape"), 1))
        except LookupError:
            pass


def measure(ctx, args):
    """§8.2 on the evaluated body at rest (Foot.Contact 0) and loaded (1.0), in spec 18's envelope."""
    import bpy
    ob = _body()
    out = []

    def add(name, value, target=None, tol=None, source="", unit="mm"):
        out.append(cli.metric(name, value, target, tol, unit, "spec 01 " + source if source else "", PART.id))

    xcfg = X.config(ctx.params)
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
            add(f"heel_prom.{side}", round(v["heel_prom"], 2), [0.5, 15.0] if xcfg.get("on") else [3.0, 15.0], None,
                XSRC + ": 038's Achilles fills out to its heel (3-15 before)" if xcfg.get("on")
                else "§3.2 (the calcaneus behind the Achilles insertion)")
            # the scan-driven pass (2026-10-16, §3.1 note): the rendered surface against three real men's unloaded feet
            # (scanfit.py): each family's RMS deviation from their mean sections; the build before the pass read plan
            # 2.1, heel 3.8, sole 4.0
            if SCAN_TARGETS is not None:
                meas = _scan_measures(fine, f, m, ix, side)
                for fam, d in scanfit.report(meas, SCAN_TARGETS).items():
                    add(f"scan_{fam}_rms.{side}", d["rms"], [0.0, SCAN_RMS[fam]], None,
                        f"§3.1 (scans 2026-10-16; worst {d['max']} at {d['at']})")
                # the scan transfer (Jeff, 2026-10-17, §0 note): the rendered surface against the one scan it was
                # transferred from, the same sections (scanfit.measures on the subject's own unloaded scan)
                own = (SCAN_TARGETS.get("per_scan") or {}).get(str(xcfg["scan"])) if xcfg.get("on") else None
                if own:
                    for fam, d in scanfit.report(meas, {"values": own}).items():
                        add(f"scan_ref_{fam}_rms.{side}", d["rms"], [0.0, SCAN_REF_RMS[fam]], None,
                            f"§0 (Jeff 2026-10-17: transferred from scan {xcfg['scan']}; worst {d['max']} at {d['at']})")
            rest[side] = v
            for k, (t, tol, src) in dict(TARGETS, **(XFER_TARGETS if xcfg.get("on") else {})).items():
                if k == "toe2_tip_y" and side == "R" and not xcfg.get("on"):
                    t = t + 1.5  # the right 2nd toe is 1.5 mm shorter (§3.3; one man's scan for both since 2026-10-17)
                add(f"{k}.{side}", None if v.get(k) is None else round(v[k], 2), t, tol, src)
            if xcfg.get("on"):
                add(f"malleoli_resolved.{side}", v.get("malleoli_resolved"), unit="")
            for k, (t, tol, src) in dict(PLAN_TARGETS, **(XFER_PLAN_TARGETS if xcfg.get("on") else {})).items():
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
                if xcfg.get("on"):
                    band, why = XFER_GAPS.get(pair, XFER_GAPS["other"])
                add(f"toe_gap_{pair}.{side}", None if g is None else round(g, 2), band, None, why)
            add(f"heading_deg.{side}", round(v["heading_deg"], 2), unit="deg")
        for nob in sorted((o for o in bpy.data.objects if o.name.startswith(("Foot.L.Nail.", "Foot.R.Nail."))),
                          key=lambda o: o.name):
            k = int(nob.name.split(".")[-1])
            w, vis, fe, thick = nails.PLATES[k]
            d = _nail_dims(nob)
            side = nob.name.split(".")[1]
            xn = XFER_NAIL1 if (k == 1 and xcfg.get("on")) else {}
            add(f"nail{k}_width.{side}", round(d["width"], 2), *(xn.get("width") or (w, 1.0)),
                XSRC + ": the plate on the broad hallux" if xn else "§3.3")
            add(f"nail{k}_length.{side}", round(d["length"], 2), *(xn.get("length") or (vis, 1.0)),
                XSRC + ": the plate on the broad hallux" if xn else "§3.3 (visible, with the free edge)")
            add(f"nail{k}_thickness.{side}", round(d["thickness"], 2), thick, 0.2, "§3.3")
            add(f"nail{k}_edge_thickness.{side}", None if d["edge_thickness"] is None else round(d["edge_thickness"], 2),
                thick, 0.2, "§3.3 (0.5 mm inside the free edge, on the rendered surface)")
            add(f"nail{k}_radius.{side}", None if d["radius"] is None else round(d["radius"], 2),
                *(xn.get("radius") or (fields.NAIL_RADIUS[k], 1.5)),
                XSRC + ": the plate on the broad hallux" if xn else "§3.3 (transverse, across the middle third)")
        for side in fields.SIDES:
            sob = bpy.data.objects.get(f"Sock.{side}.Body")
            if sob is not None:
                _measure_sock(ob, sob, side, m, ix, add)
            lob = bpy.data.objects.get(f"Foot.{side}.Last")
            if lob is not None:
                _measure_last(ob, lob, side, m, ix, add)
        # spec 18 §5.1: materials.lint() at the end of every build; an error fails the part
        if any(mt is not None and mt.name == "Body.Mat.Skin.Foot" for mt in ob.data.materials):
            res = _lint([ob] + [o for o in bpy.data.objects if o.name.startswith(("Foot.L.Nail.", "Foot.R.Nail.",
                                                                                   "Sock.L.Body", "Sock.R.Body"))])
            add("lint_errors", len(res["errors"]), [0, 0], None, "spec 18 §5.1, spec 16 §7.5", unit="")
            add("lint_warnings", len(res["warnings"]), unit="")
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
                band, why = XFER_CONTACT_ARCH if xcfg.get("on") else ([4.5, 8.0], "§1.4 item 7 (scans 2026-10-16: 6.2, 5.5-8.7)")
                add(f"contact_arch_drop.{side}", round(rest[side]["arch_medial_45"] - v1["arch_medial_45"], 2),
                    band, None, why)
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


def seated_last(lob, side):
    """The last's vertices seated on the boot's footbed (last.seat) in its frame F, the seat angle and the seated ankle
    centre (F mm): the numbers spec 02 builds on and V6 renders."""
    import bpy
    import numpy as np
    ob = _body()
    m = fm.read(ob)
    ix = fm.index(ob, m)
    f = fm.frame(m, ix, side)
    q = f.to_f(np.array([lob.matrix_world @ v.co for v in lob.data.vertices]) * 1000.0)
    ball = json.loads(lob["p01_ball"])
    mk = {k: np.array(bpy.data.objects[f"Foot.{side}.Last.{k}"]["p01_frame_mm"], float)
          for k in ("Pternion", "AnkleAxis.Medial", "AnkleAxis.Lateral")}
    z_b = float(lob["p01_insole_z"])
    b1, b5 = np.array(ball["b1"]), np.array(ball["b5"])
    qs, deg = LS.seat(q, b1, b5, mk["Pternion"], z_b)
    ank, _ = LS.seat(0.5 * (mk["AnkleAxis.Medial"] + mk["AnkleAxis.Lateral"])[None], b1, b5, mk["Pternion"], z_b)
    return qs, deg, ank[0]


def hero_lasts():
    """Foot.<S>.Last.Hero: render copies of the lasts seated on the real boot's footbed (spec 02 §0 items 2-3: heel seat
    36, ball seat 24, turned about .Ball1-.Ball5) at the hero headings and ankle positions (spec 01 §7.3), for V6; made
    after the cache is saved, never cached. Returns {side: (object, seat degrees, ankle height mm)}."""
    import bpy
    import numpy as np
    coll = replace.ensure_collection(PART)
    out = {}
    for side in fields.SIDES:
        lob = bpy.data.objects.get(f"Foot.{side}.Last")
        if lob is None:
            continue
        name = f"Foot.{side}.Last.Hero"
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old)
        qs, deg, ank = seated_last(lob, side)
        fh = LS.hero_frame(side, ank)
        me = lob.data.copy()
        me.name = name
        me.vertices.foreach_set("co", np.asarray(fh.to_w(qs) / 1000.0, np.float32).ravel())
        me.update()
        cp = bpy.data.objects.new(name, me)
        coll.objects.link(cp)
        out[side] = (cp, deg, float(ank[2]))
        log.info("part 01", f"V6: {name} seated {deg:.2f} deg heel-up, ankle centre h {ank[2]:.1f}")
    return out


def _v6_overlay(pyimg, p, side):
    """The V6 numbers and figure (p01/v6_overlay.py) for one hero crop: the seated last against the reference boot."""
    s = "R" if p["id"].endswith(".R") else "L"
    mask = next((m for m in (env.path("ref", "masks", f"boot_{s}.png"), env.path("cache", "masks", f"boot_{s}.png"))
                 if os.path.isfile(m)), None)
    if mask is None:
        return None
    x0, y0, x1, y1 = p["render"]["border_px"]
    cut = {"R": (806, 896), "L": (806, 908)}[s]     # eval/masks.py: the cuff above, the sole line below
    png = env.path(side["outputs"]["png"])
    out = png[:-4] + "_overlay.png"
    cmd = [pyimg, "-I", env.path("scripts", "parts", "p01", "v6_overlay.py"), png, mask, str(x0), str(y0), str(x1),
           str(y1), str(p["render"].get("scale", 1)), out, str(cut[0]), str(cut[1])]
    r = subprocess.run(cmd, cwd=env.PROJECT_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        res = json.loads([ln for ln in r.stdout.splitlines() if ln.startswith("{")][-1])
    except (IndexError, ValueError):
        log.info("part 01", f"V6 overlay failed: {r.stdout[-300:]} {r.stderr[-300:]}")
        return None
    res["overlay"] = os.path.relpath(out, env.PROJECT_DIR).replace(os.sep, "/")
    log.info("part 01", "V6 %s: %s" % (p["id"], json.dumps(res)))
    cache.write_json(out[:-4] + ".json", res)
    return res


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
    socks = [o for o in bpy.data.objects if o.name in ("Sock.L.Body", "Sock.R.Body")]
    lasts = [o for o in bpy.data.objects if o.name in ("Foot.L.Last", "Foot.R.Last")]
    heroes = hero_lasts() if any(reg.get(n)["id"].startswith("p01.V6") for n in names) else {}
    hero_names = {h[0].name for h in heroes.values()}
    others = [o for o in bpy.data.objects if o.type == "MESH" and o.name not in hero_names]
    saved = [(o, o.hide_render) for o in others]
    pyimg = env.load().get("pyimg")
    v6 = {}
    try:
        for n in names:
            # §8.1's variants: bare (V1-V5, V8, the ortho views), sock (V7), the last (V9); V6 shows the seated hero
            # lasts alone (the body and everything else stand at rest, elsewhere in the frame)
            pid = reg.get(n)["id"]
            for o, h in saved:
                o.hide_render = h
            for o in socks:
                o.hide_render = not pid.startswith("p01.V7")
            for o in lasts:
                o.hide_render = not pid.startswith("p01.V9")
            for cp, _, _ in heroes.values():
                cp.hide_render = not pid.startswith("p01.V6")
            if pid.startswith("p01.V6"):
                for o in others:
                    o.hide_render = True
            side = harness.render_preset(n, tier=tier, scene_name=scene_name)
            sides.append(side)
            outputs.append(env.path(side["outputs"]["png"]))
            log.info("part 01", f"rendered {side['preset']} {tier} in {side['seconds']:.2f} s -> {side['outputs']['png']}")
            if pid.startswith("p01.V6") and pyimg and tier == "form":
                v6[pid] = _v6_overlay(pyimg, reg.get(n), side)
    finally:
        for o, h in saved:
            o.hide_render = h
        for cp, _, _ in heroes.values():
            cp.hide_render = True
    for pid, r in v6.items():
        if r:
            outputs.append(env.path(r["overlay"]))
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


def _body_material(ob):
    """The materials stage's Skin.Foot on the foot's faces of Body.Mesh, put back with the layers: a material slot of
    the shared body is not in the part's cache, nor in its layer cache."""
    if ob.vertex_groups.get("Foot.Region") is not None:
        M.ensure_groups()
        M.assign(ob, "Skin.Foot", part="Body", faces="Foot.Region")


def _restore_layers(argv):
    """When the part's cache is fresh, put its body layers back (lib/cache has no layer_apply yet); when the
    cache is fresh but its layers are missing, rebuild. --stage runs on the cached part, so its layers come
    back too (a stage replaces only its own). Returns the arguments to run with."""
    try:
        a = cli.parse(argv)
    except cli.UsageError:
        return argv
    if a.stage:
        if layers.apply(PART, _body()):
            _body_material(_body())
        else:
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
        _body_material(_body())
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
