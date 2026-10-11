"""Build a blind critic packet (spec 18 §8.1.2): the images a critic judges, a brief generated from the
part's spec and the command line, and the packet's sha256 that every result must quote.

Image-tools Python (PIL; numpy only for a reference pair's diff), from the project folder:

  source cache/env.sh
  "$SGT_PYIMG" -I scripts/eval/critic/packet.py --out renders/01_foot/critic/r1 --part 01 --round 1 \
      --spec spec/01_foot_ankle_sock.md --render renders/01_foot/p01.V1f.L_eval.png [--render ...] \
      [--ref PRESET=crop.png] [--anchor cache/ref_feet/jeff_feet_photos.png --anchor-note TEXT] \
      [--zoom NAME=STEM:x0,y0,x1,y1[@k]] [--scope TEXT] [--declare TEXT]... [--questions 2,3,6] \
      [--section 3.3]... [--presets scripts/eval/presets/p01.json]... [--metrics m.json] [--measure m.json] \
      [--previous renders/01_foot/critic/r1] [--force]

A render's JSON sidecar (same stem) gives its preset, tier and scene; a preset registry gives the view's
note and its scale. A zoom's box is in its source render's pixels, STEM is that render's file stem, and
k defaults to 2. The critic sees only the packet, so nothing in it names a build, a method or a version:
the sources and the command line go to <out>.sources.json beside it. Packets hold renders and private
photographs, so they are written only into ignored folders under renders/, never ref/ or anything tracked.
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
MAX_SIDE = 2000  # §8.1.2; a critic's image reader only scales anything larger down again
# Words that tell a critic which build is meant to be the better one. "final" is a tier's name, and an
# upper-case V plus digits is a view (p01.V5), so only a lower-case v3 counts as a version.
VERSION_WORDS = {"fixed", "fix", "new", "old", "better", "improved", "before", "after", "prev",
                 "previous", "latest", "attempt"}
SEVERITIES = ("blocking", "major", "minor")
ANCHOR_NOTE = ("photographs of the real thing, the standard for what it looks like. They are not this man "
               "and no photograph matches a render's view: compare kind and character, not identity or pose.")


def die(msg):
    sys.exit(f"packet: {msg}")


def rel(path):
    try:
        return os.path.relpath(os.path.abspath(path), PROJECT).replace(os.sep, "/")
    except ValueError:  # another drive (Windows): only an absolute path names it
        return os.path.abspath(path).replace(os.sep, "/")


def neutral(name):
    tokens = [t for t in re.split(r"[^A-Za-z0-9]+", name) if t]
    bad = [t for t in tokens if t.lower() in VERSION_WORDS or re.fullmatch(r"v\d+", t)]
    if bad:
        die(f"{name}: names in a packet carry no version words ({', '.join(bad)})")
    return name


def guard(out):
    """Packets go only into ignored folders under renders/ (not renders/eval/, which is tracked)."""
    norm = os.path.normcase
    renders = os.path.join(PROJECT, "renders")
    inside = norm(os.path.commonpath([out, renders])) == norm(renders) and norm(out) != norm(renders)
    tracked = norm(os.path.commonpath([out, os.path.join(renders, "eval")])) == norm(os.path.join(renders, "eval"))
    if not inside or tracked:
        die(f"{rel(out)}: a packet goes in an ignored folder under renders/, never renders/eval/, ref/ or anything tracked")
    try:
        r = subprocess.run(["git", "check-ignore", "-q", out], cwd=PROJECT, capture_output=True, timeout=30)
        if r.returncode == 1:
            die(f"{rel(out)} is not ignored by git, and a packet holds renders and private photographs")
    except (OSError, subprocess.SubprocessError):
        pass  # no git here: the path rule above stands


def git_commit():
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT, capture_output=True,
                           text=True, timeout=30)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def packet_sha(folder):
    """sha256 over each file's relative path and sha256, sorted. results/ and the sha file are left out, so
    the critics' answers never change the digest they quote. tally.py holds the same definition."""
    names = []
    for root, dirs, files in os.walk(folder):
        if os.path.normcase(root) == os.path.normcase(folder):
            dirs[:] = [d for d in dirs if d != "results"]
        names += [os.path.relpath(os.path.join(root, f), folder).replace(os.sep, "/") for f in files]
    h = hashlib.sha256()
    for name in sorted(n for n in names if n != "packet.sha256"):
        with open(os.path.join(folder, name), "rb") as f:
            h.update(f"{name}\0{hashlib.sha256(f.read()).hexdigest()}\n".encode())
    return h.hexdigest()


# ---------------------------------------------------------------- the spec

def spec_sections(path):
    """Headings outside code fences, each with its text up to the next heading of its level or above."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    heads, fence = [], False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else re.match(r"^(#{1,6})\s+(.*\S)\s*$", line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    out = []
    for k, (i, level, title) in enumerate(heads):
        end = next((j for j, lv, _ in heads[k + 1:] if lv <= level), len(lines))
        body = "\n".join(lines[i + 1:end]).strip()
        out.append({"title": title, "level": level, "body": re.sub(r"(\n\s*(-{3,}|\*{3,})\s*)+$", "", body)})
    return out


def find_section(sections, key):
    """By number ("3.3") or by a phrase of the title; specs share titles but not numbers."""
    plain = lambda s: s.replace("“", '"').replace("”", '"').lower()
    number = re.fullmatch(r"\d+(\.\d+)*", key)
    for s in sections:
        if number and (s["title"] == key or s["title"].startswith(key + " ")):
            return s
        if not number and plain(key) in plain(s["title"]):
            return s
    return None


def numbered(body):
    """The items of a numbered list, continuation lines folded in."""
    items, cur = [], None
    for line in body.splitlines():
        m = re.match(r"^(\d+)\.\s+(.*)", line)
        if m:
            cur = [int(m.group(1)), m.group(2).strip()]
            items.append(cur)
        elif cur and line.strip() and line[:1] in (" ", "\t"):
            cur[1] += " " + line.strip()
        elif line.strip():
            cur = None
    return [(n, t) for n, t in items]


# ---------------------------------------------------------------- images

def sidecar(png):
    path = os.path.splitext(png)[0] + ".json"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f), path
    return {}, None


def registry(paths):
    out = {}
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for p in json.load(f).get("presets", []):
                out[p["id"]] = p
    return out


def lookup(reg, preset):
    """A side's render (p01.V1.L) is described by its registry entry (p01.V1)."""
    return reg.get(preset) or reg.get(re.sub(r"\.[LR]$", "", preset)) or {}


def field_mm(entry):
    """Width of the view at the aim point: the scale a critic needs to judge a dimension by eye."""
    cam = entry.get("camera", {})
    if cam.get("type") == "ortho" and cam.get("ortho_scale_mm"):
        return float(cam["ortho_scale_mm"])
    if cam.get("lens_mm") and cam.get("pos_mm") and cam.get("target_mm"):
        return cam.get("sensor_mm", 36.0) / cam["lens_mm"] * math.dist(cam["pos_mm"], cam["target_mm"])
    return None


def lighting(sc):
    engine, tier = (sc.get("engine") or "").upper(), sc.get("tier")
    if engine == "BLENDER_WORKBENCH" or tier == "form":
        return "Clay: Workbench matcap, no materials; judge form here, not colour or material."
    scene = (sc.get("scene") or "").split(" ")[0].lower()
    where = {"lookdev": "LookDev studio (18 % grey cyclorama; key, fill and rim lights)",
             "hero": "the hero scene (the reference's key, cool side and world lights; a plain floor)"}
    eng = {"CYCLES": "Cycles", "BLENDER_EEVEE_NEXT": "EEVEE", "BLENDER_EEVEE": "EEVEE"}.get(engine, engine or "?")
    vt = [v for v in (sc.get("view_transform") or []) if v and v != "None"]
    bits = [eng] + ([f"{sc['samples']} samples"] if sc.get("samples") else []) + vt[-1:]
    bits += ["graded"] if sc.get("graded") else []
    return f"{where.get(scene, sc.get('scene') or 'scene not recorded')}; {', '.join(bits)}."


def fit(im):
    s = min(1.0, MAX_SIDE / max(im.size))
    return im if s == 1.0 else im.resize((round(im.size[0] * s), round(im.size[1] * s)), Image.LANCZOS)


def side_by_side(left, right):
    im = Image.new("RGB", (left.size[0] + right.size[0], max(left.size[1], right.size[1])), (0, 0, 0))
    im.paste(left, (0, 0))
    im.paste(right, (left.size[0], 0))
    return im


def lstar(im):
    import numpy as np
    a = np.asarray(im.convert("RGB"), dtype=np.float64) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    y = lin @ np.array([0.2126, 0.7152, 0.0722])
    f = np.where(y > (6 / 29) ** 3, np.cbrt(y), y / (3 * (6 / 29) ** 2) + 4 / 29)
    return 116 * f - 16


def diff_image(ref, render):
    """|ΔL*| from 0 to 30 as black, red, yellow, white (§8.1.2)."""
    import numpy as np
    d = np.clip(np.abs(lstar(render) - lstar(ref)) / 30.0, 0, 1)
    rgb = np.stack([np.clip(d * 3, 0, 1), np.clip(d * 3 - 1, 0, 1), np.clip(d * 3 - 2, 0, 1)], -1)
    return Image.fromarray((rgb * 255).astype(np.uint8))


def failing(path):
    """Names of the items marked "pass": false anywhere in a metrics or measure file (§8.1.5 rule 1)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    bad = []

    def walk(x):
        if isinstance(x, dict):
            if x.get("pass") is False:
                bad.append(str(x.get("metric") or x.get("name") or x.get("id") or "?"))
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(data)
    return bad


def claims_from(previous, part):
    """The previous round's located defects as claims to verify: id, place, one line, never a score."""
    path = os.path.join(previous, "results", "tally.json")
    if not os.path.exists(path):
        die(f"--previous {previous}: no results/tally.json there (run tally.py on that round first)")
    with open(path, encoding="utf-8") as f:
        t = json.load(f)
    if t.get("part") != part:
        die(f"--previous {previous} is part {t.get('part')}, not {part}")
    out = []
    for item in t.get("merged", []):
        if item.get("severity") not in SEVERITIES:
            continue
        loc = (item.get("locations") or [None])[0]
        where = f"`{loc['image']}` {loc['box_px']}" if loc else "no single place"
        what = item["text"] if len(item["text"]) <= 160 else item["text"][:157].rstrip() + "..."
        out.append({"id": f"r{t['round']}.{item['id']}", "where": where, "what": what})
    return out


# ---------------------------------------------------------------- the packet

def parse(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="packet folder, e.g. renders/01_foot/critic/r1")
    ap.add_argument("--part", required=True, help="two digits, 01 to 18")
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--spec", required=True, help="the part's spec, e.g. spec/01_foot_ankle_sock.md")
    ap.add_argument("--render", action="append", required=True, help="a render PNG; repeat, in viewing order")
    ap.add_argument("--ref", action="append", default=[], metavar="PRESET=PATH",
                    help="reference crop for a preset's renders: pair, onion and diff")
    ap.add_argument("--anchor", help="external reference image for a part the reference never shows (C1's anchor)")
    ap.add_argument("--anchor-note", default=ANCHOR_NOTE)
    ap.add_argument("--zoom", action="append", default=[], metavar="NAME=STEM:x0,y0,x1,y1[@k]")
    ap.add_argument("--scope", help="what this round judges, if less than the whole part")
    ap.add_argument("--declare", action="append", default=[], help="a declared difference; repeat")
    ap.add_argument("--questions", help="the spec's critic questions to score, e.g. 2,3,6 (default all)")
    ap.add_argument("--section", action="append", default=[], help="another spec section for the brief, by number or title")
    ap.add_argument("--presets", action="append", default=[], help="a preset registry JSON: view notes and scale")
    ap.add_argument("--metrics", help="metrics.json (§8.2)")
    ap.add_argument("--measure", help="the part's measure.json")
    ap.add_argument("--previous", help="the previous round's packet; its defects become claims to verify")
    ap.add_argument("--force", action="store_true", help="replace an existing packet, results and all")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"0[1-9]|1[0-8]", a.part):
        die("--part is two digits, 01 to 18")
    if not 1 <= a.round <= 5:
        die("--round is 1 to 5 (§8.1.5: at most five rounds)")
    return a


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    argv = sys.argv[1:] if argv is None else argv
    a = parse(argv)
    out = os.path.abspath(a.out)
    guard(out)
    sections = spec_sections(a.spec)
    part_title = next((s["title"] for s in sections if s["level"] == 1), os.path.basename(a.spec))
    reg = registry(a.presets)

    renders, by_stem = [], {}
    for path in a.render:
        if not os.path.exists(path):
            die(f"--render {path}: no such file")
        sc, sc_path = sidecar(path)
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem in by_stem:
            die(f"--render {path}: a second render with the stem {stem}")
        head, _, tail = stem.rpartition("_")
        r = {"path": path, "stem": neutral(stem), "preset": sc.get("preset") or head or stem,
             "tier": sc.get("tier") or tail, "sc": sc, "sc_path": sc_path}
        renders.append(r)
        by_stem[stem] = r
    refs = {}
    for spec in a.ref:
        preset, _, path = spec.partition("=")
        if not path or not os.path.exists(path):
            die(f"--ref {spec}: expected PRESET=PATH to an existing image")
        refs[preset] = path
    zooms = []
    for spec in a.zoom:
        m = re.fullmatch(r"([A-Za-z0-9_-]+)=([^:]+):(\d+),(\d+),(\d+),(\d+)(?:@([0-9.]+))?", spec)
        if not m or m.group(2) not in by_stem:
            die(f"--zoom {spec}: expected NAME=STEM:x0,y0,x1,y1[@k] with STEM one of the renders' stems")
        zooms.append((neutral(m.group(1)), by_stem[m.group(2)], tuple(int(m.group(i)) for i in range(3, 7)),
                      float(m.group(7) or 2)))
    for path in (a.metrics, a.measure):
        if path and failing(path):
            die(f"{path}: failing metrics {', '.join(failing(path))}; a round is not sent to the critics "
                f"while any automatic metric fails (§8.1.5 rule 1)")
    claims = claims_from(a.previous, a.part) if a.previous else []

    if os.path.exists(out):
        if not a.force:
            die(f"{rel(out)} exists; --force replaces it (and any results in it)")
        if not os.path.exists(os.path.join(out, "packet.json")):
            die(f"{rel(out)} exists and is not a packet; not removing it")
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "results"))

    images, sources = [], []

    def save(im, name, entry, source=None):
        im.save(os.path.join(out, neutral(name)))
        entry = dict(entry, file=name, size=list(im.size))
        images.append(entry)
        if source:
            sources.append(dict(source, file=name))
        return entry

    # Views: the reference crop on the left when there is one (§8.1.2), else the render alone.
    for r in renders:
        im = Image.open(r["path"]).convert("RGB")
        r["size"] = im.size
        entry = lookup(reg, r["preset"])
        fmm = field_mm(entry)
        r["px_mm"] = im.size[0] / fmm if fmm else None
        view = f"view {r['preset']}" + (f" ({r['sc']['label']})" if r["sc"].get("label") else "")
        r["text"] = view + (f": {entry['note'].rstrip('.')}" if entry.get("note") else "")
        source = {"source": rel(r["path"]), "sidecar": rel(r["sc_path"]) if r["sc_path"] else None,
                  "render_commit": r["sc"].get("commit"), "build_hash": r["sc"].get("build_hash"),
                  "time_utc": r["sc"].get("time_utc")}
        ref_path = refs.get(r["preset"])
        if ref_path is None:
            pair = fit(im)
            s = im.size[0] / pair.size[0]
            r["map"] = [0.0, 0.0, s, im.size[1] / pair.size[1]]
            how = "The render alone: the reference image never shows this."
        else:
            ref = Image.open(ref_path).convert("RGB")
            if abs(ref.size[0] / ref.size[1] - im.size[0] / im.size[1]) > 0.01:
                die(f"--ref {r['preset']}: the crop's aspect differs from the render's; cut it at the preset's box")
            r["ref"] = ref = ref.resize(im.size, Image.LANCZOS)
            pair = fit(side_by_side(ref, im))
            s = 2 * im.size[0] / pair.size[0]
            r["map"] = [-float(im.size[0]), 0.0, s, im.size[1] / pair.size[1]]
            how = "Reference crop on the left, render on the right, at one size and scale."
        scale = f" In this image about {r['px_mm'] / s:.1f} px/mm at the aim point." if r["px_mm"] else ""
        r["pair"] = save(pair, f"pair_{r['stem']}.png",
                         {"kind": "pair", "preset": r["preset"], "tier": r["tier"], "frame": r["preset"],
                          "map": r["map"], "text": f"{r['text']}.{scale} {how} {lighting(r['sc'])}"}, source)
        if ref_path is not None and r["tier"] != "form":  # a clay render has no colour to compare
            onion = fit(Image.blend(r["ref"], im, 0.5))
            same = [0.0, 0.0, im.size[0] / onion.size[0], im.size[1] / onion.size[1]]
            save(onion, f"onion_{r['stem']}.png",
                 {"kind": "onion", "preset": r["preset"], "tier": r["tier"], "frame": r["preset"], "map": same,
                  "text": f"{view}: reference and render blended half and half."})
            save(fit(diff_image(r["ref"], im)), f"diff_{r['stem']}.png",
                 {"kind": "diff", "preset": r["preset"], "tier": r["tier"], "frame": r["preset"], "map": same,
                  "text": f"{view}: |ΔL*| between reference and render, black 0 to white 30."})

    # Zooms: cut from the source render at its own resolution, so they show what the pair's scaling hides.
    for name, r, box, k in zooms:
        x0, y0, x1, y1 = box
        w, h = r["size"]
        if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
            die(f"--zoom {name}: box {box} is not inside {r['stem']} ({w} x {h})")
        im = Image.open(r["path"]).convert("RGB").crop(box)
        im = im.resize((round(im.size[0] * k), round(im.size[1] * k)), Image.LANCZOS)
        ox = float(x0)
        if "ref" in r:
            im = side_by_side(r["ref"].crop(box).resize(im.size, Image.LANCZOS), im)
            ox = x0 - (x1 - x0)
        if max(im.size) > MAX_SIDE:
            die(f"--zoom {name}: {im.size[0]} x {im.size[1]} px at x{k:g}; a box of at most "
                f"{int(MAX_SIDE / k / (2 if 'ref' in r else 1))} px keeps it within {MAX_SIDE}")
        pm = r["map"]
        in_pair = [round((x0 - pm[0]) / pm[2]), round((y0 - pm[1]) / pm[3]),
                   round((x1 - pm[0]) / pm[2]), round((y1 - pm[1]) / pm[3])]
        scale = f" In this image about {r['px_mm'] * k:.0f} px/mm." if r["px_mm"] else ""
        save(im, f"zoom_{r['stem']}_{name}.png",
             {"kind": "zoom", "preset": r["preset"], "tier": r["tier"], "frame": r["preset"],
              "map": [ox, float(y0), 1 / k, 1 / k], "region": name,
              "text": f"x{k:g} of `{r['pair']['file']}`, its box {in_pair}: {name}.{scale}"})

    anchor = None
    if a.anchor:
        stem = os.path.splitext(os.path.basename(a.anchor))[0]
        anchor = save(fit(Image.open(a.anchor).convert("RGB")), f"anchor_{stem}.png",
                      {"kind": "anchor", "text": f"C1's anchor: {a.anchor_note}"},
                      {"source": rel(a.anchor)})
    extras = []
    for path, name in ((a.metrics, "metrics.json"), (a.measure, "measure.json")):
        if path:
            shutil.copyfile(path, os.path.join(out, name))
            extras.append(name)
            sources.append({"file": name, "source": rel(path)})

    # The brief: the spec's own words by heading, plus the scope and declared differences given here.
    picked = None
    if a.questions:
        picked = sorted({int(n) for n in a.questions.split(",") if n.strip()})
    qsec = find_section(sections, "Critic questions")
    questions = numbered(qsec["body"]) if qsec else []
    if picked and not set(picked) <= {n for n, _ in questions}:
        die(f"--questions {a.questions}: the spec's critic questions are numbered "
            f"{', '.join(str(n) for n, _ in questions) or 'nowhere'}")
    scored = [(n, t) for n, t in questions if picked is None or n in picked]
    spec_name = os.path.splitext(os.path.basename(a.spec))[0]
    L = [f"# Critic brief: part {a.part}, round {a.round}", "",
         f"Generated by `scripts/eval/critic/packet.py` from `{rel(a.spec)}` ({part_title}) and the packet's "
         "command line; never edited by hand.", "", "## Scope", ""]
    if a.scope:
        L += [f"Judge only this: {a.scope}. Everything else in the images is context: do not score it, and "
              "mention it only where it spoils the judgement of the scope.", ""]
    else:
        L += ["The whole part, as the spec's extracts below describe it.", ""]
    L += ["## Declared differences", ""]
    if a.declare:
        L += ["Known departures in this round. They are not defects: do not score them or list them, but say "
              "so if one of them hides or distorts something inside the scope.", ""]
        L += [f"- {d}" for d in a.declare] + [""]
    else:
        L += ["None.", ""]
    L += ["## Images", "",
          "Open every one with the Read tool before scoring. A defect's box is [x0, y0, x1, y1] in the pixels of "
          "the image it names; the sizes are given because your view of an image may be scaled.", ""]
    L += [f"- `{im['file']}` ({im['size'][0]} x {im['size'][1]} px): {im['text']}" for im in images]
    if extras:
        L += ["", "Also read " + " and ".join(f"`{e}`" for e in extras) + " (the automatic measurements)."]
    L += [""]
    missing = []
    for key in ['What "perfect" looks like', "Pass criteria"] + a.section:
        s = find_section(sections, key)
        if s is None:
            missing.append(key)
            continue
        L += [f"## From the spec: {s['title']}", "", s["body"], ""]
    L += ["## Questions to score", ""]
    if qsec:
        L += [f"From the spec's \"{qsec['title']}\". Score each question listed here from 1 to 10 with the "
              "anchors of your instructions, under its id; leave none out and add none.", ""]
        L += [f"- **Q{n}**: {t}" for n, t in scored]
        kept = {n for n, _ in scored}
        rest = [f"Q{n}" for n, _ in questions if n not in kept]
        if rest:
            L += ["", f"Outside this round's scope and not scored: {', '.join(rest)}."]
    else:
        L += ["The spec has no numbered critic questions: give the overall score only."]
    L += [""]
    s = find_section(sections, "Known failure modes")
    if s:
        L += [f"## From the spec: {s['title']}", "", s["body"], ""]
    L += ["## Claims to verify", ""]
    if claims:
        L += ["The previous round's defects, as claims. Check each in this packet and answer every one in "
              "`verified_claims`: fixed true or false.", ""]
        L += [f"- **{c['id']}** at {c['where']}: {c['what']}" for c in claims]
    else:
        L += ["None: there is no previous round."]
    with open(os.path.join(out, "brief.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")

    packet = {"part": a.part, "round": a.round, "spec": rel(a.spec), "scope": a.scope, "declared": a.declare,
              "questions": [f"Q{n}" for n, _ in scored], "claims": [c["id"] for c in claims],
              "presets": list(dict.fromkeys(r["preset"] for r in renders)),
              "tiers": list(dict.fromkeys(r["tier"] for r in renders)),
              "metrics": "metrics.json" if a.metrics else None, "measure": "measure.json" if a.measure else None,
              "images": [{k: v for k, v in im.items() if k != "text"} for im in images]}
    with open(os.path.join(out, "packet.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(packet, f, indent=1, ensure_ascii=False)
        f.write("\n")
    sha = packet_sha(out)
    with open(os.path.join(out, "packet.sha256"), "w", encoding="utf-8", newline="\n") as f:
        f.write(sha + "\n")

    provenance = {"packet": rel(out) + "/", "sha256": sha, "spec": rel(a.spec), "commit": git_commit(),
                  "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "argv": argv,
                  "previous": rel(a.previous) if a.previous else None, "files": sources,
                  "refs": {k: rel(v) for k, v in refs.items()}, "missing_sections": missing}
    with open(out + ".sources.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(provenance, f, indent=1, ensure_ascii=False)
        f.write("\n")
    for key in missing:
        print(f"packet: warning: the spec has no section titled like '{key}'; left out of the brief")
    print(f"packet: {rel(out)}/  {len(images)} images, {len(scored)} questions, {len(claims)} claims")
    print(f"packet: sha256 {sha}")
    return out


if __name__ == "__main__":
    main()
