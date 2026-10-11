"""Tally a critic round (spec 18 §8.1.4, §8.1.5, §8.3): check each critic's result against schema.json and the
packet, apply the pass rule, merge the three critics' defects and ranked lists into one deduplicated list by
severity, write results/tally.json and results/tally.md, and append the round to renders/eval/log.jsonl,
regenerating renders/eval/log.md from it.

Image-tools Python (standard library only), from the project folder:

  source cache/env.sh
  "$SGT_PYIMG" -I scripts/eval/critic/tally.py renders/01_foot/critic/r1           # tally and log
  "$SGT_PYIMG" -I scripts/eval/critic/tally.py renders/01_foot/critic/r1 --check   # validate what is there

  --check     validate the results present and stop; writes nothing
  --dry-run   tally and print; writes nothing
  --log-dir   log somewhere other than renders/eval (for tests)
  --session, --agent, --machine, --next   the log line's fields of those names

Exit 1 when a result is invalid; the errors are printed so the critic can be asked once more (§8.1.4).
The merge is lexical and conservative: it joins wordings that share most of their words, or boxes that
overlap in one view and share some words, and never two defects of one critic, so near-duplicates in
different words stay apart rather than distinct defects being lost.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
LOG_DIR = os.path.join(PROJECT, "renders", "eval")
CRITICS = {"C1": "fidelity", "C2": "reality", "C3": "craft"}
SEVERITIES = ("blocking", "major", "minor")
GROUPS = SEVERITIES + ("unrated",)
TAG = re.compile(r"^\s*\[([A-Za-z0-9_.-]+)\]\s*")
STOP = set("""the a an and or of to in on at is are was be been it its this that these those with as by for from
not no but than too very into onto over under there their they them which what where when how has have had
does do one two all any some more most less much little like looks look reads read seen see visible shows
show should would could also only just still each both other same here""".split())
NEXT = {"accept": "milestone images: the passing round's pairs to renders/eval/",
        "revise": "fix the merged list, blocking and major first, then round {n}",
        "repeat": "the same packet to three fresh critics (§8.1.5 rule 4)",
        "ask Jeff": "the scores spread twice on one packet: Jeff decides",
        "escalate": "five rounds failed: the part stops until Jeff answers",
        "metrics fail": "fix the failing metrics; no critics until they pass"}

# The validator knows exactly these keywords and refuses a schema with others, so a keyword added to
# schema.json can never be silently ignored.
KNOWN = {"$schema", "$id", "title", "description", "type", "required", "properties", "additionalProperties",
         "enum", "pattern", "minimum", "maximum", "maxLength", "items", "minItems", "maxItems"}
TYPES = {"object": lambda v: isinstance(v, dict), "array": lambda v: isinstance(v, list),
         "string": lambda v: isinstance(v, str), "boolean": lambda v: isinstance(v, bool),
         "integer": lambda v: (isinstance(v, int) and not isinstance(v, bool))
         or (isinstance(v, float) and v.is_integer()),
         "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)}


def schema_errors(value, schema, path="$"):
    unknown = set(schema) - KNOWN
    if unknown:
        sys.exit(f"tally: schema.json uses keywords this validator does not know: {sorted(unknown)}")
    t = schema.get("type")
    if t and not TYPES[t](value):
        return [f"{path}: expected {t}"]
    errs = []
    if "enum" in schema and not any(value == e and type(value) is type(e) for e in schema["enum"]):
        errs.append(f"{path}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errs.append(f"{path}: {value!r} does not match {schema['pattern']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errs.append(f"{path}: {len(value)} characters, at most {schema['maxLength']}")
    if TYPES["number"](value):
        if "minimum" in schema and value < schema["minimum"]:
            errs.append(f"{path}: {value} is below {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errs.append(f"{path}: {value} is above {schema['maximum']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errs.append(f"{path}: {len(value)} items, at least {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errs.append(f"{path}: {len(value)} items, at most {schema['maxItems']}")
        for i, v in enumerate(value):
            errs += schema_errors(v, schema.get("items", {}), f"{path}[{i}]")
    if isinstance(value, dict):
        errs += [f"{path}: missing {k!r}" for k in schema.get("required", []) if k not in value]
        props = schema.get("properties", {})
        for k, v in value.items():
            if k in props:
                errs += schema_errors(v, props[k], f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: unknown key {k!r}")
    return errs


def packet_sha(folder):
    """The same definition as packet.py's: sha256 over each file's path and sha256, sorted, without
    results/ and the sha file."""
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


def rel(path):
    try:
        return os.path.relpath(os.path.abspath(path), PROJECT).replace(os.sep, "/")
    except ValueError:  # another drive (Windows): only an absolute path names it
        return os.path.abspath(path).replace(os.sep, "/")


def git_commit():
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT, capture_output=True,
                           text=True, timeout=30)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


# ---------------------------------------------------------------- checking one result

def image_of(packet, name):
    """A defect names a packet image by file; a bare preset id is taken as that preset's first view."""
    for im in packet["images"]:
        if name in (im["file"], im["file"][:-4]):
            return im
    return next((im for im in packet["images"] if im.get("preset") == name and im["kind"] == "pair"), None)


def clip(box, im):
    w, h = im["size"]
    x0, y0, x1, y1 = box
    return [max(0, min(w, x0)), max(0, min(h, y0)), max(0, min(w, x1)), max(0, min(h, y1))]


def check(name, result, packet, sha, schema):
    errors = schema_errors(result, schema)
    if errors:
        return errors, []
    warns = []
    expect = {"critic": name, "lens": CRITICS[name], "part": packet["part"], "round": packet["round"]}
    errors += [f"{k} is {result[k]!r}, expected {v!r}" for k, v in expect.items() if result[k] != v]
    if result["packet_sha"] != sha:
        errors.append("packet_sha is not this packet's: copy it from packet.sha256")
    got = [q["id"] for q in result["questions"]]
    errors += [f"question {q} is not scored" for q in packet["questions"] if q not in got]
    for q in dict.fromkeys(got):
        if q not in packet["questions"]:
            errors.append(f"question {q} is not one of this round's ({', '.join(packet['questions']) or 'none'})")
        elif got.count(q) > 1:
            errors.append(f"question {q} is scored twice")
    ids = [d["id"] for d in result["defects"]]
    errors += [f"defect id {i} is used twice" for i in dict.fromkeys(ids) if ids.count(i) > 1]
    for d in result["defects"]:
        im = image_of(packet, d["preset"])
        x0, y0, x1, y1 = d["box_px"]
        if im is None:
            errors.append(f"defect {d['id']}: {d['preset']!r} is not an image of this packet (give its file name)")
        elif x0 >= x1 or y0 >= y1:
            errors.append(f"defect {d['id']}: box {d['box_px']} is empty (need x0 < x1 and y0 < y1)")
        elif clip(d["box_px"], im) != d["box_px"]:
            warns.append(f"defect {d['id']}: box {d['box_px']} runs outside {im['file']} {im['size']}; clipped")
    answered = [c["id"] for c in result.get("verified_claims", [])]
    errors += [f"claim {c} is not answered in verified_claims" for c in packet["claims"] if c not in answered]
    errors += [f"verified_claims: {c} is not a claim of this packet" for c in answered if c not in packet["claims"]]
    for i, item in enumerate(result["ranked"], 1):
        m = TAG.match(item)
        if m and m.group(1) not in ids:
            warns.append(f"ranked item {i} names {m.group(1)}, which is not one of the defects; read as free-form")
    blocking = any(d["severity"] == "blocking" for d in result["defects"])
    if result["pass"] != (result["overall"] >= 8 and not blocking):
        warns.append(f"pass is {result['pass']} with overall {result['overall']} and "
                     f"{'a' if blocking else 'no'} blocking defect; the round's rule decides anyway")
    return errors, warns


# ---------------------------------------------------------------- merging the three

def words(text):
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if len(w) < 3 or w in STOP:
            continue
        for suffix in ("ing", "ed", "es", "s"):
            if len(w) > 4 and w.endswith(suffix):
                w = w[:-len(suffix)]
                break
        out.add(w)
    return out


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def overlap(a, b):
    """Intersection over the smaller box: a tight zoom box inside a loose view box counts as the same place."""
    if not a or not b:
        return 0.0
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return w * h / small if small > 0 else 0.0


def to_frame(im, box):
    """A box in a packet image, in its source render's pixels, so a view, its clay twin and its zooms compare."""
    if not im.get("map"):
        return None
    ox, oy, sx, sy = im["map"]
    return [ox + box[0] * sx, oy + box[1] * sy, ox + box[2] * sx, oy + box[3] * sy]


def merge(results, packet):
    items = []
    for c in sorted(results):
        own = {}
        for d in results[c]["defects"]:
            im = image_of(packet, d["preset"])
            box = clip(d["box_px"], im)
            own[d["id"]] = x = {"critic": c, "kind": "defect", "severity": d["severity"], "text": d["what"],
                                "fix": d.get("fix"), "spec_ref": d.get("spec_ref"), "image": im["file"], "box": box,
                                "frame": im.get("frame"), "src": to_frame(im, box), "rank": None, "said": []}
            items.append(x)
        for i, text in enumerate(results[c]["ranked"], 1):
            m = TAG.match(text)
            body = text[m.end():] if m else text
            if m and m.group(1) in own:  # the critic's own link: its ranked wording of that defect
                d = own[m.group(1)]
                d["rank"] = d["rank"] or i
                d["said"].append(body)
            else:
                items.append({"critic": c, "kind": "ranked", "text": body, "rank": i, "frame": None, "src": None,
                              "said": []})
    for x in items:
        x["words"] = words(" ".join([x["text"]] + x["said"]))
    pairs = []
    for i, j in combinations(range(len(items)), 2):
        a, b = items[i], items[j]
        if a["critic"] == b["critic"] and a["kind"] == b["kind"]:
            continue  # a critic's own items are distinct by intent
        sim = jaccard(a["words"], b["words"])
        place = (a["kind"] == b["kind"] == "defect" and a["frame"] is not None and a["frame"] == b["frame"]
                 and overlap(a["src"], b["src"]) >= 0.5)
        if sim >= 0.5 or (place and sim >= 0.2):
            pairs.append((sim + (0.5 if place else 0.0), i, j))
    root = list(range(len(items)))
    members = {i: [i] for i in range(len(items))}

    def find(i):
        while root[i] != i:
            i = root[i]
        return i
    for _, i, j in sorted(pairs, key=lambda p: -p[0]):
        a, b = find(i), find(j)
        if a == b:
            continue
        ca = {items[k]["critic"] for k in members[a] if items[k]["kind"] == "defect"}
        cb = {items[k]["critic"] for k in members[b] if items[k]["kind"] == "defect"}
        if ca & cb:
            continue  # never two defects of one critic in one item
        root[b] = a
        members[a] += members.pop(b)

    merged = []
    for first, ks in sorted((min(ks), ks) for ks in members.values()):
        its = [items[k] for k in sorted(ks)]
        defects = [x for x in its if x["kind"] == "defect"]
        ranks = {}
        for x in its:
            if x["rank"]:
                ranks[x["critic"]] = min(ranks.get(x["critic"], x["rank"]), x["rank"])
        lead = min(its, key=lambda x: (x["rank"] or 99, SEVERITIES.index(x["severity"]) if defects and
                                       x["kind"] == "defect" else 9))
        text = lead["text"] if lead["kind"] == "ranked" else (lead["said"] or [lead["text"]])[0]
        wordings = list(dict.fromkeys(s for x in its for s in (x["said"] + [x["text"]])))
        merged.append({
            "severity": min((x["severity"] for x in defects), key=SEVERITIES.index, default="unrated"),
            "critics": sorted({x["critic"] for x in its}), "text": text,
            "also": [w for w in wordings if w != text],
            "locations": [{"critic": x["critic"], "severity": x["severity"], "image": x["image"], "box_px": x["box"]}
                          for x in defects],
            "fixes": list(dict.fromkeys(x["fix"] for x in defects if x["fix"])),
            "spec_refs": list(dict.fromkeys(x["spec_ref"] for x in defects if x["spec_ref"])),
            "ranks": dict(sorted(ranks.items())), "_order": (min(ranks.values(), default=99), first)})
    # Within a severity: raised by more critics first, then by how high any critic ranked it.
    merged.sort(key=lambda m: (GROUPS.index(m["severity"]), -len(m["critics"]), m["_order"]))
    for n, m in enumerate(merged, 1):
        m["id"] = f"m{n}"
        del m["_order"]
    return [dict(id=m.pop("id"), **m) for m in merged]


# ---------------------------------------------------------------- the round

def metrics_state(folder, packet):
    failing, summary = [], {}
    for key in ("metrics", "measure"):
        if not packet.get(key):
            continue
        with open(os.path.join(folder, packet[key]), encoding="utf-8") as f:
            data = json.load(f)
        flags = []

        def walk(x):
            if isinstance(x, dict):
                if isinstance(x.get("pass"), bool):
                    flags.append((str(x.get("metric") or x.get("name") or x.get("id") or "?"), x["pass"]))
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(data)
        failing += [n for n, ok in flags if not ok]
        if key == "measure":
            summary["measure_pass"] = f"{sum(ok for _, ok in flags)}/{len(flags)}"
        elif isinstance(data, dict) and isinstance(data.get("summary"), dict):
            summary.update(data["summary"])
    return failing, summary or None


def tally(folder, packet, sha, results, attempt):
    overall = {c: int(results[c]["overall"]) for c in sorted(results)}
    scores = sorted(overall.values())
    median, spread = scores[len(scores) // 2], scores[-1] - scores[0]
    blocking = sum(d["severity"] == "blocking" for r in results.values() for d in r["defects"])
    failing, metrics = metrics_state(folder, packet)
    passed = not failing and median >= 8 and blocking == 0
    if failing:
        decision = "metrics fail"
    elif spread >= 4:
        decision = "repeat" if attempt == 1 else "ask Jeff"
    elif passed:
        decision = "accept"
    elif packet["round"] >= 5:
        decision = "escalate"
    else:
        decision = "revise"
    questions = {q: {c: next(int(x["score"]) for x in results[c]["questions"] if x["id"] == q) for c in sorted(results)}
                 for q in packet["questions"]}
    claims = {cl: {c: next(v["fixed"] for v in results[c].get("verified_claims", []) if v["id"] == cl)
                   for c in sorted(results)} for cl in packet["claims"]}
    critics = {c: {"lens": CRITICS[c], "model": results[c]["model"], "overall": overall[c],
                   "pass": results[c]["pass"], "confidence": results[c].get("confidence"),
                   **{k: sum(d["severity"] == s for d in results[c]["defects"])
                      for k, s in (("blocking", "blocking"), ("majors", "major"), ("minors", "minor"))}}
               for c in sorted(results)}
    return {"part": packet["part"], "round": packet["round"], "attempt": attempt, "packet": rel(folder) + "/",
            "packet_sha": sha, "scope": packet.get("scope"), "critics": critics, "median": median,
            "spread": spread, "blocking": blocking, "metrics": metrics, "failing_metrics": failing,
            "pass": passed, "decision": decision, "questions": questions, "claims": claims,
            "merged": merge(results, packet)}


def tally_md(t):
    crit = ", ".join(f"{c} {v['lens']} {v['overall']}" for c, v in t["critics"].items())
    metrics = (f"failing: {', '.join(t['failing_metrics'])}" if t["failing_metrics"]
               else "in tolerance" if t["metrics"] else "none in the packet")
    L = [f"# Tally: part {t['part']}, round {t['round']}" + (f", attempt {t['attempt']}" if t["attempt"] > 1 else ""),
         "", f"Packet `{t['packet']}`, sha {t['packet_sha'][:12]}. Scope: {t['scope'] or 'the whole part'}.", "",
         f"**{'PASS' if t['pass'] else 'FAIL'}**, decision **{t['decision']}**: median {t['median']} ({crit}; "
         f"spread {t['spread']}), {t['blocking']} blocking, metrics {metrics}.", ""]
    names = list(t["critics"])
    if t["questions"]:
        L += ["| Question | " + " | ".join(names) + " | Min | Mean |", "|---" * (len(names) + 3) + "|"]
        rows = list(t["questions"].items()) + [("Overall", {c: v["overall"] for c, v in t["critics"].items()})]
        for q, s in rows:
            vals = [s[c] for c in names]
            L.append(f"| {q} | " + " | ".join(map(str, vals)) + f" | {min(vals)} | {sum(vals) / len(vals):.1f} |")
    for group in GROUPS:
        items = [m for m in t["merged"] if m["severity"] == group]
        if not items:
            continue
        L += ["", f"## {group.capitalize()}" + (": free-form, no located defect" if group == "unrated" else ""), ""]
        for m in items:
            L.append(f"- **{m['id']}** [{', '.join(m['critics'])}] {m['text']}")
            if m["locations"]:
                L.append("  - at " + "; ".join(f"{x['critic']} {x['severity']} `{x['image']}` {x['box_px']}"
                                               for x in m["locations"]))
            if m["ranks"]:
                L.append("  - ranked " + ", ".join(f"{c} #{r}" for c, r in m["ranks"].items()))
            L += [f"  - fix: {f}" for f in m["fixes"]]
            if m["spec_refs"]:
                L.append("  - spec " + ", ".join(m["spec_refs"]))
            L += [f"  - also: {w}" for w in m["also"]]
    if t["claims"]:
        L += ["", "## Claims from the previous round", "", "| Claim | " + " | ".join(names) + " |",
              "|---" * (len(names) + 1) + "|"]
        L += [f"| {cl} | " + " | ".join("fixed" if v[c] else "open" for c in names) + " |"
              for cl, v in t["claims"].items()]
    return "\n".join(L) + "\n"


def log_line(t, a, meta, event="critic", **over):
    """One event, at most 2 KB (§8.3). "open" carries the top five merged items so that log.md, which lists
    them, is a function of the tracked log alone; the packets themselves are not tracked. meta is
    packet.json; `over` replaces fields, as the escalation line does with the best round's packet."""
    line = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "session": a.session,
            "agent": a.agent, "machine": a.machine, "commit": git_commit(), "part": t["part"], "event": event,
            "round": t["round"], "tier": "+".join(meta.get("tiers") or []) or None,
            "presets": meta.get("presets", []), "metrics": t["metrics"],
            "critics": [{"lens": v["lens"], "overall": v["overall"], "blocking": v["blocking"],
                         "majors": v["majors"], "minors": v["minors"]} for v in t["critics"].values()],
            "median": t["median"], "pass": t["pass"], "decision": t["decision"],
            "next": a.next or NEXT[t["decision"]].format(n=t["round"] + 1), "packet": t["packet"]}
    line.update(over)
    line["open"] = [f"{m['severity']}: {m['text']}" for m in t["merged"] if m["severity"] in SEVERITIES][:5]
    for width in (100, 70, 40):
        line["open"] = [o if len(o) <= width else o[:width - 3].rstrip() + "..." for o in line["open"]]
        if len(json.dumps(line, ensure_ascii=False).encode()) <= 2048:
            break
    while line["open"] and len(json.dumps(line, ensure_ascii=False).encode()) > 2048:
        line["open"].pop()
    return line


def part_title(part):
    for path in sorted(glob.glob(os.path.join(PROJECT, "spec", f"{part}_*.md"))):
        with open(path, encoding="utf-8") as f:
            m = re.match(r"#\s*Part\s+\d+\s*[—–-]+\s*(.+)", f.readline())
        if m:
            return f"{part} {m.group(1).strip()}"
    return part


def log_md(lines):
    """The whole of log.md from the JSON lines (§8.3), deterministic, so a known log reproduces it."""
    fmt = lambda v: "—" if v is None else f"{v:g}" if isinstance(v, (int, float)) else str(v)
    head = ["# Evaluation log", "", "Regenerated by `scripts/eval/critic/tally.py` from `log.jsonl` after every "
            "round (spec 18 §8.3); never edit it by hand.", "", "| Part | Status | Rounds | Last | Median |",
            "|---|---|---|---|---|"]
    body = []
    for part in sorted({l["part"] for l in lines}):
        ev = [l for l in lines if l["part"] == part]
        critic = [l for l in ev if l["event"] == "critic"]
        deciding = [l for l in ev if l["event"] in ("critic", "acceptance", "escalation")]
        last = deciding[-1] if deciding else ev[-1]
        status = ("ESCALATED" if last["event"] == "escalation" else
                  "PASS" if last["event"] == "acceptance" or last.get("decision") == "accept" else "IN PROGRESS")
        title = part_title(part)
        head.append(f"| {title} | {status} | {len({l.get('packet') for l in critic})} | {ev[-1]['ts'][:10]} | "
                    f"{fmt(critic[-1]['median']) if critic else '—'} |")
        body += ["", f"## {title}", "", "| Date | Round | Tier | IoU | max ΔE00 | max landmark px | C1/C2/C3 | Median "
                 "| Blocking | Result | Packet |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for l in ev:
            m = l.get("metrics") or {}
            cs = {c["lens"]: c for c in l.get("critics") or []}
            scores = "/".join(fmt(cs[x]["overall"]) if x in cs else "—" for x in CRITICS.values())
            blocking = fmt(sum(c["blocking"] for c in cs.values())) if cs else "—"
            result = l.get("decision") or ""
            if l["event"] != "critic":
                result = f"{l['event']}" + (f": {result}" if result else "")
            body.append(f"| {l['ts'][:10]} | {fmt(l.get('round'))} | {l.get('tier') or '—'} | {fmt(m.get('iou'))} | "
                        f"{fmt(m.get('de00_max'))} | {fmt(m.get('lm_px_max'))} | {scores} | {fmt(l.get('median'))} | "
                        f"{blocking} | {result} | `{l.get('packet') or ''}` |")
        opened = critic[-1].get("open") if critic else None
        body += ["", "Open defects of the latest round, by severity:" if opened else "No open defects recorded.", ""]
        body += [f"- {o}" for o in opened or []]
    return "\n".join(head + body) + "\n"


def write_log(lines_new, log_dir):
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, "log.jsonl")
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        for line in lines_new:
            f.write(json.dumps(line, ensure_ascii=False, separators=(",", ":")) + "\n")
    with open(path, encoding="utf-8") as f:
        lines = [json.loads(s) for s in f if s.strip()]
    with open(os.path.join(log_dir, "log.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(log_md(lines))
    return lines


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("packet")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log-dir", default=LOG_DIR)
    ap.add_argument("--session", default=os.environ.get("SGT_SESSION", "local"))
    ap.add_argument("--agent", default=os.environ.get("SGT_AGENT", "main"))
    ap.add_argument("--machine", default="workstation" if sys.platform == "win32" else "cloud")
    ap.add_argument("--next")
    a = ap.parse_args(argv)
    folder = os.path.abspath(a.packet)
    out = os.path.join(folder, "results")
    with open(os.path.join(folder, "packet.json"), encoding="utf-8") as f:
        packet = json.load(f)
    with open(os.path.join(folder, "packet.sha256"), encoding="utf-8") as f:
        sha = f.read().split()[0]
    if packet_sha(folder) != sha:
        sys.exit("tally: the packet changed after it was built; rebuild it and run the critics again")
    with open(os.path.join(HERE, "schema.json"), encoding="utf-8") as f:
        schema = json.load(f)

    results, bad = {}, False
    for c in CRITICS:
        path = os.path.join(out, f"{c}.json")
        if not os.path.exists(path):
            if not a.check:
                print(f"{c}.json: missing")
                bad = True
            continue
        try:
            with open(path, encoding="utf-8-sig") as f:
                result = json.load(f)
        except (OSError, ValueError) as e:
            print(f"{c}.json: INVALID\n  - not JSON: {e}")
            bad = True
            continue
        errors, warns = check(c, result, packet, sha, schema)
        print(f"{c}.json: {'INVALID' if errors else 'valid'}")
        print("".join(f"  - {e}\n" for e in errors) + "".join(f"  - warning: {w}\n" for w in warns), end="")
        bad = bad or bool(errors)
        if not errors:
            results[c] = result
    if a.check:
        if not results and not bad:
            print("tally: no results to check")
        return 1 if bad else 0
    if bad:
        print("tally: nothing tallied; ask each critic above once more, with its errors")
        return 1
    if os.path.exists(os.path.join(out, "tally.json")):
        sys.exit("tally: this attempt is already tallied (results/tally.json); the log has its line")

    attempt = 2 if os.path.isdir(os.path.join(out, "attempt1")) else 1
    t = tally(folder, packet, sha, results, attempt)
    lines = [log_line(t, a, packet)]
    if t["decision"] == "escalate":
        # §8.1.5 rule 3: the best round's packet and the open defects, for the question to Jeff.
        path = os.path.join(a.log_dir, "log.jsonl")
        past = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                past = [json.loads(s) for s in f if s.strip()]
        rounds = [l for l in past + lines if l["part"] == t["part"] and l["event"] == "critic"]
        best = max(reversed(rounds), key=lambda l: l["median"])
        lines.append(log_line(t, a, packet, "escalation", packet=best["packet"], decision="ask Jeff",
                              next="a question to Jeff in the session log; nobody iterates on the part until he answers"))
    md = tally_md(t)
    if a.dry_run:
        print(md)
        print("\n".join(json.dumps(l, ensure_ascii=False) for l in lines))
        return 0
    with open(os.path.join(out, "tally.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(t, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(out, "tally.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    write_log(lines, a.log_dir)
    where = out
    if t["decision"] == "repeat":
        # The fresh critics write results/C*.json again; this attempt moves aside so its tally stands.
        where = os.path.join(out, "attempt1")
        os.makedirs(where)
        for name in [f"{c}.json" for c in CRITICS] + ["tally.json", "tally.md"]:
            shutil.move(os.path.join(out, name), os.path.join(where, name))
    print(f"tally: {'PASS' if t['pass'] else 'FAIL'}, decision {t['decision']}, median {t['median']}, "
          f"spread {t['spread']}, {t['blocking']} blocking, {len(t['merged'])} merged items")
    print(f"tally: {rel(os.path.join(where, 'tally.md'))}; logged to {rel(a.log_dir)}/log.jsonl and log.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
