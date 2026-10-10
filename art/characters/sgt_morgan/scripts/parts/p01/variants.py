"""Part 01's foot in variants, for Jeff to choose between: each variant a params override (merged over
p01/params.json, as --params is) built with --check, so nothing is saved and the part's cache is untouched;
its closeup copies rendered through spec 17's harness, measured, and laid out by scripts/tools/sheet.py as
one contact sheet, a row per variant and a column per view (five columns, the width sheet.py fills).

  blender -b cache/body/rigged.blend --python scripts/parts/p01/variants.py -- toes|heel [--quality form]

Writes renders/01_foot/variants/<sheet>/<variant>_<preset>_<tier>.png, <sheet>.json (the overrides and what
was measured) and renders/01_foot/sheets/<sheet>_variants.png. The variants of 2026-10-10:

  toes  current; B the webs forward to spec 01 §3.2 (or 4.5 mm forward where already there), the toes
        allowed to touch (gap 0.2 mm); C B with the lesser toes flexed 15 degrees at the PIP and 5 at the
        DIP (the fifth 20 and 8), extended at the MTP so the pads stay on the floor; D C at 25 degrees (the
        fifth 30); E C with the middle phalanges of toes 2-4 3-4 mm shorter.
  heel  current; H1 the heel round at the back and widest at 15-18 % L, z10/z20/z30 widths 69/72/73 and a
        breadth of 74; H2 H1 at 76 (z10 71); H3 H1 loaded (Foot.Contact 1.0). The heel's amounts are solved
        here against those outlines (the fields are linear in them); the malleoli, the Achilles and the
        back profile are not touched (the heel fields only widen about the heel's centre line, below z 70).
"""
import argparse
import importlib
import importlib.util
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(os.path.dirname(HERE))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
from lib import cache, cli, env, log, measure, optim  # noqa: E402
from parts.p01 import fields, footmetrics as fm, nails  # noqa: E402

PART_SCRIPT = os.path.join(SCRIPTS, "parts", "01_foot_ankle_sock.py")
OUT = env.path("renders", "01_foot", "variants")
SHEETS = env.path("renders", "01_foot", "sheets")
L = 282.0
SPEC_WEBS = {"1-2": -231.1, "2-3": -235.0, "3-4": -231.1, "4-5": -223.4}  # §3.2 at 282 mm (§0 item 1)
SPEC_TIPS = {k: -L * s for k, s in {1: 1.0, 2: 0.985, 3: 0.95, 4: 0.905, 5: 0.83}.items()}

VIEWS = {"toes": ["p01.V1f.L", "p01.V1f.R", "p01.V5f.L", "p01.V2.L", "p01.V4.L"],
         "heel": ["p01.V4.L", "p01.V4.L#heel", "p01.V8.L", "p01.V3.L", "p01.V1f.L"],
         # the first column: Jeff's reference photos on the first row, a closeup of the hallux on the others
         "hallux": ["p01.V5f.L#hallux", "p01.V1f.L", "p01.V1f.R", "p01.V5f.L", "p01.V4.L"],
         # the default build alone (Jeff's lock of 2026-10-10)
         "locked": ["p01.V1f.L", "p01.V1f.R", "p01.V5f.L", "p01.V2.L", "p01.V3.L", "p01.V4.L", "p01.V8.L"]}
PHOTOS = env.path("cache", "ref_feet", "jeff_feet_photos.png")  # Jeff's, never in ref/ or committed
# what the sheet shows of each 2048 px render: (left, top, right, bottom) as shares of the frame, for the
# left side (the right mirrored); a view written "id#name" is another crop of id's render; the full renders
# stay beside the crops
CROPS = {"toes": {"p01.V1f": (0.24, 0.32, 0.80, 0.86), "p01.V5f": (0.12, 0.16, 0.96, 0.70),
                  "p01.V2": (0.48, 0.28, 1.0, 0.74), "p01.V4": (0.22, 0.10, 0.78, 0.92)},
         "heel": {"p01.V4": (0.22, 0.10, 0.78, 0.92), "p01.V4#heel": (0.30, 0.08, 0.70, 0.48),
                  "p01.V8": (0.18, 0.10, 0.82, 0.90), "p01.V3": (0.40, 0.12, 1.0, 0.74),
                  "p01.V1f": (0.22, 0.0, 0.82, 0.86)},
         "hallux": {"p01.V5f#hallux": (0.14, 0.30, 0.60, 0.68), "p01.V1f": (0.24, 0.32, 0.80, 0.86),
                    "p01.V5f": (0.12, 0.16, 0.96, 0.70), "p01.V4": (0.22, 0.10, 0.78, 0.92)},
         "locked": {"p01.V1f": (0.22, 0.0, 0.82, 0.86), "p01.V5f": (0.12, 0.16, 0.96, 0.70),
                    "p01.V2": (0.0, 0.08, 1.0, 0.78), "p01.V3": (0.0, 0.08, 1.0, 0.78),
                    "p01.V4": (0.22, 0.10, 0.78, 0.92), "p01.V8": (0.18, 0.10, 0.82, 0.90)}}

# Jeff, 2026-10-10: the lesser toes of variant E, curled to D's level and more (his photos: raised knuckles,
# tips down), the 4-5 web at -218 so the fifth toe is not fused, the 1-2 cleft left open; the hallux nearly
# straight (IP 5); heel H1 (provisional), its amounts as solved for the heel sheet
H1_SCULPT = {"heel_back_w": 20.8327, "heel_end_w": 17.9599, "heel_fore_w": -2.2884, "heel_low_w": 0.7107,
             "heel_mid_w": 16.9746, "heel_top_w": 0.1942}
BASE_FIXED = {"toe_curl_deg": {"2": 25.0, "3": 25.0, "4": 25.0, "5": 32.0},
              "toe_dip_deg": {"2": 8.0, "3": 8.0, "4": 8.0, "5": 10.0}, "hallux_ip_deg": 5.0,
              "toe_mtp_floor": True, "toe_mid_short_mm": {"2": 3.0, "3": 3.5, "4": 4.0},
              "toe_gather": True, "toe_gap_mm": 0.3, "toe_gap_pairs": {"1-2": [1.5, 1.0e6]},
              "web_y": {"2-3": -235.0, "3-4": -231.1, "4-5": -218.0}}

# heel outlines (width across the foot, mm, at y_F and z): H1 is round at the back (near a semicircle
# behind 10 % L), widest at 15-18 % L and 69/72/73 at z 10/20/30 at 15 % L; H2 is H1 scaled to a 76 breadth
H1 = {"y": (-10.0, -14.0, -20.0, -28.0, -35.0, -42.0, -50.0, -56.0, -62.0, -70.0),
      10.0: (None, None, 53.0, 62.0, 66.5, 69.0, 69.5, 68.5, 66.0, 59.0),
      20.0: (44.0, 52.0, 61.0, 68.0, 71.0, 72.0, 73.0, 72.5, 71.5, 70.3),
      30.0: (45.0, 53.0, 62.0, 69.0, 72.0, 73.0, 73.5, 73.0, 72.0, 69.8),
      "breadth": 74.0}
HEEL_FIELDS = {"heel_end_w": (-10.0, 60.0), "heel_back_w": (-10.0, 45.0), "heel_mid_w": (-10.0, 40.0),
               "heel_fore_w": (-15.0, 20.0), "heel_low_w": (-10.0, 30.0), "heel_top_w": (-20.0, 20.0)}


def scaled(outline, s, s10=None):
    out = {"y": outline["y"], "breadth": outline["breadth"] * s}
    for z in (10.0, 20.0, 30.0):
        k = s10 if (z == 10.0 and s10) else s
        out[z] = tuple(None if w is None else w * k for w in outline[z])
    return out


H2 = scaled(H1, 76.0 / 74.0, 71.0 / 69.0)


def crop_png(src, dst, box):
    """Write the part of a PNG inside box (left, top, right, bottom as shares of the frame) to dst, with
    Blender's image API (the image-tools Python is not in this process); the pixels go across as stored."""
    import bpy
    im = bpy.data.images.load(src, check_existing=False)
    out = None
    try:
        w, h = im.size
        c = im.channels
        a = np.empty(w * h * c, np.float32)
        im.pixels.foreach_get(a)
        a = a.reshape(h, w, c)  # rows bottom-up
        x0, y0, x1, y1 = box
        r0, r1 = int(round((1.0 - y1) * h)), int(round((1.0 - y0) * h))
        c0, c1 = int(round(x0 * w)), int(round(x1 * w))
        sub = np.ascontiguousarray(a[r0:r1, c0:c1])
        out = bpy.data.images.new("P01.Crop", c1 - c0, r1 - r0, alpha=(c == 4))
        if c != 4:
            sub = np.concatenate([sub, np.ones(sub.shape[:2] + (1,), np.float32)], axis=2)
        out.pixels.foreach_set(sub.ravel())
        out.filepath_raw = dst
        out.file_format = "PNG"
        out.save()
    finally:
        bpy.data.images.remove(im)
        if out is not None:
            bpy.data.images.remove(out)
    return dst


def part_module():
    spec = importlib.util.spec_from_file_location("p01_part_script", PART_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- measuring a built variant

def nail_dims(side):
    """{toe: width, visible length and transverse radius} of one side's nail plates (mm)."""
    import bpy
    out = {}
    for k in fields.TOES:
        ob = bpy.data.objects.get(f"Foot.{side}.Nail.{k}")
        if ob is None:
            continue
        co = np.array([v.co for v in ob.data.vertices]) * 1000.0
        a = np.array(ob["p01_axis"], float)
        nrm = fields.plane_normal(co, np.array([0.0, 0.0, 1.0]))
        a2 = a - (a @ nrm) * nrm
        a2 /= np.linalg.norm(a2)
        b = np.cross(nrm, a2)
        frame = json.loads(ob["p01_frame"]) if "p01_frame" in ob else None
        out[k] = {"width": float((co @ b).max() - (co @ b).min()), "length": float((co @ a2).max() - (co @ a2).min()),
                  "radius": nails.transverse_radius(co, a),
                  "edge_thickness": nails.free_edge_thickness(ob, frame) if frame else None}
    return out


def measure_foot(ob, contact=0.0):
    """What the sheets are judged by: per side the webs and visible toe lengths, the tips, the gaps, the toe
    widths and heights, and the heel outline (at the given Foot.Contact)."""
    kb = ob.data.shape_keys.key_blocks.get("Foot.Contact")
    old = kb.value if kb else None
    out = {}
    try:
        if kb:
            kb.value = contact
        measure.forget()
        m = fm.read(ob)
        ix = fm.index(ob, m)
        for side in fields.SIDES:
            f = fm.frame(m, ix, side)
            v = fm.foot(m, ix, side)
            v.pop("_frame", None)
            w = fm.webs(m, ix, side, f)
            outline, widest = fm.heel_outline(m, f)
            out[side] = {
                "webs": {p: w[p] for p in SPEC_WEBS}, "visible": w["visible"], "tips": w["tips"],
                "gaps": fm.toe_gaps(m, ix, side), "gap_1_2_tips": fm.hallux_gap(m, ix, side, f),
                "nails": nail_dims(side),
                "toes": {k: {"width": v.get(f"toe{k}_width"), "height": v.get(f"toe{k}_height")} for k in fields.TOES},
                "heel": {"breadth": v.get("heel_breadth"), "z10": v.get("heel_width_z10"), "z20": v.get("heel_width_z20"),
                         "z30": v.get("heel_width_z30"), "widest_y": widest[0], "widest": widest[1],
                         "widest_share": None if widest[0] is None else -widest[0] / L,
                         "outline": {f"{y:g}@{z:g}": (None if x is None else round(x, 1)) for (y, z), x in outline.items()}},
                "foot_length": v.get("foot_length"), "ball_breadth": v.get("ball_breadth"),
                "pternion_z": v.get("pternion_z"), "malleolus_lateral_z": v.get("malleolus_lateral_z"),
                "malleolus_medial_z": v.get("malleolus_medial_z"),
            }
    finally:
        if kb:
            kb.value = old
    return out


# --------------------------------------------------------------------------- the heel's amounts for an outline

def _widths(m, f, ys, zs):
    """{(y, z): width} with one section per height (fm.width_at cuts a section for every station)."""
    out = {}
    for z in zs:
        lp = fm.loops(m, f, float(z))
        for y in ys:
            xs = []
            for p, closed in lp:
                P = np.vstack([p, p[:1]]) if closed else p
                a, b = P[:-1], P[1:]
                da, db = a[:, 1] - y, b[:, 1] - y
                hit = (da * db <= 0.0) & (da != db)
                t = da[hit] / (da[hit] - db[hit])
                xs += (a[hit, 0] + t * (b[hit, 0] - a[hit, 0])).tolist()
            out[(y, z)] = max(xs) - min(xs) if len(xs) >= 2 else None
    return out


def solve_heel(body, a0, opts, outline, say=print, iters=4, breadth_tol=0.4):
    """The heel fields' amounts that give `outline` on the left foot (the right takes the same): bounded
    least squares on the widths and the breadth, the Jacobian by differences of one per cent (the fields are
    linear; pass B moves the heel little), a weak pull toward the current amounts."""
    names = list(HEEL_FIELDS)
    lo = np.array([HEEL_FIELDS[k][0] for k in names])
    hi = np.array([HEEL_FIELDS[k][1] for k in names])
    x = np.array([a0[k] for k in names], float)
    ys = outline["y"]
    zs = (10.0, 20.0, 30.0)
    foot = body.feet["L"]

    def resid(vec):
        a = dict(a0, **dict(zip(names, vec)))
        q = body.sculpt_side("L", a, opts, separate=False)
        co = body.co.copy()
        co[foot.R] = foot.frame.to_w(q)
        m = fm.with_positions(body.m0, co)
        f = fm.frame(m, body.ix, "L")
        W = _widths(m, f, ys, zs)
        r = []
        for z in zs:
            for y, t in zip(ys, outline[z]):
                if t is not None and W[(y, z)] is not None:
                    r.append(W[(y, z)] - t)
        b, _, _ = fm.breadth(m, f, (-60.0, 5.0), np.arange(4.0, 45.0, 4.0))
        r.append((b - outline["breadth"]) / breadth_tol)
        return np.array(r)

    r = resid(x)
    say(f"heel solve: start rms {np.sqrt(np.mean(r * r)):.2f} mm")
    for it in range(iters):
        J = np.empty((len(r), len(x)))
        for j in range(len(x)):
            e = np.zeros(len(x))
            e[j] = 1.0
            J[:, j] = resid(x + e) - r
        sol = optim.bounded_lsq(J, J @ x - r, lo=lo, hi=hi, lam=0.01, w0=x)
        step = np.clip(sol["x"], lo, hi) - x
        for _ in range(5):  # the widths are read off a cage: halve a step that does not lower the misfit
            xn = x + step
            rn = resid(xn)
            if rn @ rn < r @ r:
                break
            step = step / 2.0
        else:
            say(f"heel solve: no step lowers the misfit; stopping at rms {np.sqrt(np.mean(r * r)):.2f} mm")
            break
        say(f"heel solve: iteration {it + 1} rms {np.sqrt(np.mean(rn * rn)):.2f} mm; "
            + ", ".join(f"{k} {v:.1f}" for k, v in zip(names, xn)))
        done = np.max(np.abs(xn - x)) < 0.2
        x, r = xn, rn
        if done:
            break
    return {k: round(float(v), 4) for k, v in zip(names, x)}


# --------------------------------------------------------------------------- the variants

def toe_variants(current):
    """The toe sheet's overrides; B's webs from the current build's (spec 01 §3.2's, or 4.5 mm forward)."""
    now = current["L"]["webs"]
    web_y = {p: round(min(SPEC_WEBS[p], (now[p]["saddle_y"] or SPEC_WEBS[p]) - 4.5), 1) for p in SPEC_WEBS}
    B = {"fixed": {"toe_gap_mm": 0.3, "toe_gather": True, "web_y": web_y}}
    curl = {"toe_mtp_floor": True, "toe_dip_deg": {"2": 5.0, "3": 5.0, "4": 5.0, "5": 8.0}}
    C = {"fixed": dict(B["fixed"], toe_curl_deg={"2": 15.0, "3": 15.0, "4": 15.0, "5": 20.0}, **curl)}
    D = {"fixed": dict(B["fixed"], toe_curl_deg={"2": 25.0, "3": 25.0, "4": 25.0, "5": 30.0}, **curl)}
    E = {"fixed": dict(C["fixed"], toe_mid_short_mm={"2": 3.0, "3": 3.5, "4": 4.0})}
    return [("current", "current", {}, 0.0),
            ("B", "B: webs to spec, touching", B, 0.0),
            ("C", "C: B + PIP 15, DIP 5 (5th 20/8)", C, 0.0),
            ("D", "D: C at PIP 25 (5th 30)", D, 0.0),
            ("E", "E: C, mid phalanges 2-4 -3/-3.5/-4", E, 0.0)]


def hallux_variants():
    """The hallux sheet's overrides (Jeff, 2026-10-10, from his reference photos): on the new base, the
    hallux broadened with its nail (the §3.3 proportions and 11 mm transverse radius kept) and set apart
    from toes 2-5, which move as a group; the hallux's valgus eased a little."""
    def v(name, label, width=0.0, nail=None, gap=None, valgus=None, toe2_w=None, curl=None):
        fx = json.loads(json.dumps(BASE_FIXED))
        if width:
            fx["hallux_width_mm"] = width
        if nail:
            fx["nail_size"] = {"1": nail}
        if gap is not None:
            fx["toe_gap_pairs"] = {"1-2": [gap, gap]}
        if valgus:
            fx["hallux_valgus_deg"] = valgus
        if curl:
            fx["toe_curl_deg"] = curl
        over = {"fixed": fx, "sculpt": dict(H1_SCULPT)}
        if toe2_w is not None:
            over["sculpt"]["toe2_w"] = toe2_w
        return name, label, over, 0.0

    x2 = dict(width=30.0, nail=[19.5, 18.35], gap=4.5, valgus={"L": 7.5, "R": 5.5})
    return [v("base", "base: E curled 25/8 (5th 32/10), web 4-5 -218, 1-2 open, H1"),
            v("X1", "X1: hallux 28.5, nail 18.5, 1-2 gap 3", 28.5, [18.5, 17.4], 3.0, {"L": 8.0, "R": 6.0}),
            v("X2", "X2: hallux 30, nail 19.5, 1-2 gap 4.5", **x2),
            v("X3", "X3: X2, toe 2 slimmed to 16", toe2_w=-10.06, **x2),
            v("X2c", "X2c: X2, PIP 35 (5th 40)", curl={"2": 35.0, "3": 35.0, "4": 35.0, "5": 40.0}, **x2)]


def heel_variants(mod, ob, say):
    """The heel sheet's overrides: the amounts solved for H1 and H2 on the current body."""
    import bpy  # noqa: F401
    params = cli.load_params(mod.PART)
    body = fields.Body(ob, exclude=mod.KEYS)
    a0 = fields.amounts(params)
    opts = fields.options(params)
    h1 = solve_heel(body, a0, opts, H1, say)
    h2 = solve_heel(body, a0, opts, H2, say)
    return [("current", "current", {}, 0.0),
            ("H1", "H1: round back, 69/72/73, 74", {"sculpt": h1}, 0.0),
            ("H2", "H2: H1 at 76 (z10 71)", {"sculpt": h2}, 0.0),
            ("H3", "H3: H1 loaded (Foot.Contact 1)", {"sculpt": h1}, 1.0)]


def run(sheet, quality="form", say=None):
    import bpy
    say = say or (lambda msg: log.info("variants", msg))
    env.bootstrap()
    render = importlib.import_module("eval.render")
    mod = part_module()
    ob = bpy.data.objects[mod.BODY]
    out_dir = os.path.join(OUT, sheet)
    os.makedirs(out_dir, exist_ok=True)
    record = {"sheet": sheet, "views": VIEWS[sheet], "quality": quality, "variants": []}
    images, labels = [], []

    def build(name, override, contact):
        t = time.perf_counter()
        res = cli.run(mod.PART, mod.build, None, ["--check", "--params", json.dumps(override)])
        if res["exit"] not in (cli.PASS, cli.TOLERANCE):
            raise RuntimeError(f"variant {name}: {res.get('error')}\n{res.get('trace')}")
        kb = ob.data.shape_keys.key_blocks["Foot.Contact"]
        kb.value = contact
        mod.isolate_copies(ob)
        say(f"{name}: built in {time.perf_counter() - t:.1f} s")

    if sheet == "hallux":
        variants = hallux_variants()
        current = None
    elif sheet == "locked":
        variants = [("locked", "X3 + H1, locked 2026-10-10", {}, 0.0)]
        current = None
    else:
        build("current", {}, 0.0)
        current = measure_foot(ob)
        variants = toe_variants(current) if sheet == "toes" else heel_variants(mod, ob, say)
    for row, (name, label, override, contact) in enumerate(variants):
        if name != "current":
            build(name, override, contact)
        got = current if (name == "current" and contact == 0.0) else measure_foot(ob, contact)
        rec = {"name": name, "label": label, "params": override, "contact": contact, "measured": got,
               "renders": []}
        done = {}
        for view in VIEWS[sheet]:
            pid, _, cut = view.partition("#")
            if sheet == "hallux" and row == 0 and cut == "hallux" and os.path.isfile(PHOTOS):
                images.append(PHOTOS)  # the reference cell: Jeff's photos of real men's feet
                labels.append("reference: Jeff's photos of men's feet")
                continue
            if pid not in done:
                side = render.render_preset(pid, tier=quality, out_dir=out_dir, stem=f"{name}_{pid}_{quality}")
                done[pid] = env.path(side["outputs"]["png"])
                rec["renders"].append(os.path.relpath(done[pid], env.PROJECT_DIR).replace(os.sep, "/"))
            png = done[pid]
            base, s = pid.rsplit(".", 1)
            box = CROPS[sheet].get(base + (f"#{cut}" if cut else ""))
            if box is not None:
                if s == "R":
                    box = (1.0 - box[2], box[1], 1.0 - box[0], box[3])
                png = crop_png(png, png[:-4] + (f"_{cut}" if cut else "") + "_crop.png", box)
            images.append(png)
            labels.append(f"{label} | {view.split('.', 1)[1]}")
        record["variants"].append(rec)
        say(f"{name}: rendered {len(VIEWS[sheet])} views")
    ob.data.shape_keys.key_blocks["Foot.Contact"].value = 0.0
    cache.write_json(os.path.join(out_dir, f"{sheet}.json"), log.jsonable(record))
    pyimg = env.load().get("pyimg")
    sheet_png = os.path.join(SHEETS, f"{sheet}_variants.png")
    if pyimg:
        cmd = [pyimg, "-I", env.path("scripts", "tools", "sheet.py"), "sheet", "--preset", VIEWS[sheet][0].partition("#")[0],
               "--out", sheet_png, "--title", f"part 01 {sheet} variants", "--images"] + images + ["--labels"] + labels
        p = subprocess.run(cmd, cwd=env.PROJECT_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")
        say((p.stdout + p.stderr).strip()[-400:])
    return record, sheet_png


def main(argv):
    ap = argparse.ArgumentParser(prog="variants.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("sheet", choices=tuple(VIEWS))
    ap.add_argument("--quality", default="form", choices=cli.QUALITIES)
    a = ap.parse_args(argv)
    t = time.perf_counter()
    record, png = run(a.sheet, a.quality)
    print("RESULT " + log.dumps({"sheet": os.path.relpath(png, env.PROJECT_DIR).replace(os.sep, "/"),
                                 "seconds": round(time.perf_counter() - t, 1),
                                 "variants": [v["name"] for v in record["variants"]]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []))
