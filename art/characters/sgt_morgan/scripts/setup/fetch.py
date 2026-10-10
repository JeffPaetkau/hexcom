"""Verified, resumable downloads for the Sgt. Morgan toolchain (spec 18 §4.2.3).

Standard library only, so it runs on Blender's bundled Python on Windows as well as the cloud's
python3. Subcommands:

  list      --root . --list scripts/setup/downloads.json --group mpfb[,ai,...] [--jobs 4]
  manifest  --root assets --manifest assets/manifest.json [--jobs 4] [--record-hashes]
  env       --root . --os windows --blender <exe> --user-resources <dir> [--pyimg ..] [--aipy ..]
            [--godot ..] [--device OPTIX|CUDA|HIP|CPU]

Every file is checked by size and then by hash (sha256, sha512 or md5). A verified file gets a
stamp, cache/stamps/<hash12>.ok, holding its size and mtime, so a re-run skips the hashing of
files that have not changed. Zips are extracted with a path-traversal check.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.request
import zipfile

UA = {"User-Agent": "Mozilla/5.0 (sgt_morgan setup)"}
CTX = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or None)
STAMPS = None  # set in main: <project>/cache/stamps


def log(*a):
    print(*a, flush=True)


def digest(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expected_hash(entry):
    for algo in ("sha256", "sha512", "md5"):
        if entry.get(algo):
            return algo, entry[algo].lower()
    return None, None


def stamp_path(algo, value):
    return os.path.join(STAMPS, f"{algo}-{value[:12]}.ok")


def stamped(path, algo, value):
    """True if the file was verified before and has not changed since (size and mtime)."""
    sp = stamp_path(algo, value)
    if not os.path.exists(sp):
        return False
    try:
        with open(sp) as f:
            s = json.load(f)
        st = os.stat(path)
        return s["bytes"] == st.st_size and abs(s["mtime"] - st.st_mtime) < 1e-3
    except (OSError, ValueError, KeyError):
        return False


def stamp(path, algo, value):
    os.makedirs(STAMPS, exist_ok=True)
    st = os.stat(path)
    with open(stamp_path(algo, value), "w") as f:
        json.dump({"path": path, "bytes": st.st_size, "mtime": st.st_mtime}, f)


def download(urls, dest, nbytes, headers=None, tries=4):
    """Resumable download (HTTP Range) into dest; tries each URL in turn."""
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    part = dest + ".part"
    last = None
    for url in urls:
        for attempt in range(tries):
            have = os.path.getsize(part) if os.path.exists(part) else 0
            if nbytes and have > nbytes:
                os.remove(part)
                have = 0
            h = dict(UA, **(headers or {}))
            if have:
                h["Range"] = f"bytes={have}-"
            try:
                req = urllib.request.Request(url, headers=h)
                with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
                    mode = "ab" if have and r.status == 206 else "wb"
                    with open(part, mode) as f:
                        shutil.copyfileobj(r, f, 1 << 20)
                if not nbytes or os.path.getsize(part) == nbytes:
                    os.replace(part, dest)
                    return
                last = f"short download {os.path.getsize(part)} of {nbytes}"
            except urllib.error.HTTPError as e:
                last = e
                if e.code == 416:  # the range is past the end: start again
                    os.remove(part)
                elif e.code in (403, 404):
                    break
            except (urllib.error.URLError, OSError) as e:
                last = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"download failed: {dest}: {last}")


def safe_extract(zpath, folder):
    folder = os.path.abspath(folder)
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            target = os.path.abspath(os.path.join(folder, n))
            if not (target == folder or target.startswith(folder + os.sep)):
                raise RuntimeError(f"zip member escapes the folder: {n}")
        z.extractall(folder)
        return z.namelist()


def ensure(entry, dest, extract_to=None, marker=None):
    """Download if missing or the wrong size, verify, extract. Returns 'have', 'got' or raises."""
    nbytes = entry.get("bytes")
    algo, value = expected_hash(entry)
    got = False
    if not (os.path.exists(dest) and (nbytes is None or os.path.getsize(dest) == nbytes)):
        urls = [entry["url"]] + ([entry["mirror"]] if entry.get("mirror") else [])
        t0 = time.time()
        download(urls, dest, nbytes, entry.get("headers"))
        got = True
        log(f"  got  {os.path.relpath(dest)}  {os.path.getsize(dest) / 1e6:.1f} MB  {time.time() - t0:.0f} s")
    if nbytes is not None and os.path.getsize(dest) != nbytes:
        raise RuntimeError(f"size mismatch: {dest}")
    if algo and not stamped(dest, algo, value):
        if digest(dest, algo) != value:
            os.remove(dest)
            raise RuntimeError(f"{algo} mismatch: {dest} (deleted; re-run to fetch again)")
        stamp(dest, algo, value)
    if extract_to and (got or (marker and not os.path.exists(marker))):
        safe_extract(dest, extract_to)
        log(f"  extracted {os.path.relpath(dest)}")
    return "got" if got else "have"


def run_jobs(jobs, n):
    errors = []
    with cf.ThreadPoolExecutor(max_workers=n) as ex:
        futs = {ex.submit(fn): label for label, fn in jobs}
        for fut in cf.as_completed(futs):
            try:
                fut.result()
            except Exception as e:  # report every failure, then fail once at the end
                errors.append((futs[fut], str(e)))
                log(f"  FAIL {futs[fut]}: {e}")
    return errors


def cmd_list(a):
    with open(a.list) as f:
        entries = json.load(f)["files"]
    groups = set(a.group.split(","))
    jobs = []
    for e in entries:
        if e["group"] not in groups:
            continue
        dest = os.path.join(a.root, e["dest"])
        extract_to = os.path.join(a.root, e["extract"]) if e.get("extract") else None
        marker = os.path.join(a.root, e["marker"]) if e.get("marker") else None
        jobs.append((e["dest"], lambda e=e, d=dest, x=extract_to, m=marker: ensure(e, d, x, m)))
    errors = run_jobs(jobs, a.jobs)
    log(f"  {a.group}: {len(jobs) - len(errors)} of {len(jobs)} files verified")
    return 1 if errors else 0


def cmd_manifest(a):
    with open(a.manifest) as f:
        man = json.load(f)
    jobs, files = [], []
    for asset in man["assets"]:
        if asset.get("status") == "rejected":
            continue
        for fi in asset["files"]:
            dest = os.path.join(a.root, fi["path"])
            extract_to = os.path.dirname(dest) if fi.get("extract") else None
            ex = fi.get("extracted") or []
            marker = os.path.join(a.root, ex[0]) if ex else None  # no list: extract only after a download
            files.append((fi, dest))
            if not fi.get("url"):
                if not os.path.exists(dest):
                    log(f"  MISSING (manual asset, no URL): {fi['path']}")
                continue
            jobs.append((fi["path"], lambda fi=fi, d=dest, x=extract_to, m=marker: ensure(fi, d, x, m)))
    errors = run_jobs(jobs, a.jobs)
    log(f"  manifest: {len(jobs) - len(errors)} of {len(jobs)} files verified")
    if a.record_hashes and not errors:
        n = 0
        for fi, dest in files:
            if not expected_hash(fi)[0] and os.path.exists(dest):
                fi["sha256"] = digest(dest, "sha256")
                n += 1
        if n:
            man["schema"] = 3
            man["restore_command"] = "bash scripts/setup_session.sh (fetch.py manifest)"
            with open(a.manifest, "w", encoding="utf-8", newline="\n") as f:
                json.dump(man, f, indent=1, ensure_ascii=False)
                f.write("\n")
            log(f"  recorded sha256 for {n} files; manifest is now schema 3")
    return 1 if errors else 0


def cmd_env(a):
    root = os.path.abspath(a.root)
    env = {
        "project_dir": root,
        "os": a.os,
        "blender": a.blender,
        "blender_user_resources": a.user_resources,
        "pyimg": os.path.abspath(a.pyimg) if a.pyimg and os.path.exists(a.pyimg) else a.pyimg,
        "aipy": os.path.abspath(a.aipy) if a.aipy and os.path.exists(a.aipy) else a.aipy,
        "godot": a.godot,
        "device": a.device,
        "threads": os.cpu_count(),
        "written": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    os.makedirs(os.path.join(root, "cache"), exist_ok=True)
    with open(os.path.join(root, "cache", "env.json"), "w", newline="\n") as f:
        json.dump(env, f, indent=1)
        f.write("\n")

    def sh(v):
        return "'" + str(v or "").replace("'", "'\\''") + "'"

    def posix(p):  # paths for Git Bash: C:\x\y -> /c/x/y
        p = str(p or "")
        if len(p) > 2 and p[1] == ":":
            p = "/" + p[0].lower() + p[2:].replace("\\", "/")
        return p

    lines = [
        "# written by scripts/setup/fetch.py env; source it before running pipeline commands by hand",
        f"export SGT_PROJECT_DIR={sh(posix(root))}",
        f"export SGT_BLENDER={sh(posix(a.blender))}",
        f"export BLENDER_USER_RESOURCES={sh(a.user_resources)}",
        f"export SGT_PYIMG={sh(posix(env['pyimg']))}",
        f"export SGT_AIPY={sh(posix(env['aipy']))}",
        f"export SGT_GODOT={sh(posix(a.godot))}",
        f": \"${{SGT_DEVICE:={a.device or 'CPU'}}}\"; export SGT_DEVICE",
    ]
    with open(os.path.join(root, "cache", "env.sh"), "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    log("  wrote cache/env.json and cache/env.sh")
    return 0


def main():
    global STAMPS
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("list")
    pl.add_argument("--root", default=".")
    pl.add_argument("--list", required=True)
    pl.add_argument("--group", required=True)
    pl.add_argument("--jobs", type=int, default=4)
    pm = sub.add_parser("manifest")
    pm.add_argument("--root", default="assets")
    pm.add_argument("--manifest", default="assets/manifest.json")
    pm.add_argument("--jobs", type=int, default=4)
    pm.add_argument("--record-hashes", action="store_true")
    pe = sub.add_parser("env")
    pe.add_argument("--root", default=".")
    pe.add_argument("--os", required=True)
    pe.add_argument("--blender", required=True)
    pe.add_argument("--user-resources", required=True)
    pe.add_argument("--pyimg", default="")
    pe.add_argument("--aipy", default="")
    pe.add_argument("--godot", default="")
    pe.add_argument("--device", default="")
    a = p.parse_args()
    # the stamps live with the project's other rebuildable state, whatever --root is
    project = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    STAMPS = os.path.join(project, "cache", "stamps")
    sys.exit({"list": cmd_list, "manifest": cmd_manifest, "env": cmd_env}[a.cmd](a))


if __name__ == "__main__":
    main()
