#!/usr/bin/env python3
"""Download selected CC0 PBR textures (ambientCG 2K-JPG zips + Poly Haven 2K JPG maps),
HDRIs (Poly Haven 2K .hdr) and glTF models (Poly Haven 1K) and write a manifest.
Run with system python3 -I from OUTSIDE the asset folders:
  python3 -I download_assets.py /home/user/sgt_morgan/assets
"""
import json, os, sys, time, zipfile, urllib.request, concurrent.futures as cf

ROOT = sys.argv[1]
TEX = os.path.join(ROOT, "textures"); HDRI = os.path.join(ROOT, "hdri"); MODELS = os.path.join(ROOT, "models")
for d in (TEX, HDRI, MODELS): os.makedirs(d, exist_ok=True)

# need-category -> list of (source, asset_id, note)
SELECTION = {
    "cordura_nylon_weave": [("acg", "Fabric048", "procedural polyester 'vest' weave, 40x40cm tile"),
                            ("acg", "Fabric061", "procedural rough synthetic weave, 40x40cm tile"),
                            ("ph", "book_pattern", "olive plain-woven cotton, 30cm tile (colour already close to vest)")],
    "ripstop_twill_fabric": [("ph", "denim_fabric_06", "dark worn twill, 25cm tile"),
                             ("acg", "Fabric082A", "fine grey smooth woven, procedural")],
    "fleece_knit": [("ph", "knitted_fleece", "brown knitted fleece, 27cm tile"),
                    ("ph", "polar_fleece", "cream polar fleece, 27cm tile")],
    "leather": [("acg", "Leather037", "dark brown clean full-grain (photo multi-angle)"),
                ("acg", "Leather032", "black scratched leather, 45cm tile")],
    "rubber": [("acg", "Rubber004", "black grainy gym rubber, 75cm tile")],
    "metal_dark_anodised_parkerised": [("acg", "Metal063", "aged dark glossy metal (approximated from photo)"),
                                       ("acg", "Metal046B", "black dirty metal, procedural"),
                                       ("acg", "Metal050C", "rough scratched aluminium, procedural")],
    "matte_polymer": [("acg", "Plastic012B", "black scratched plastic"),
                      ("acg", "Plastic018B", "grey dirty scratched plastic")],
    "worn_paint_over_metal": [("acg", "Metal027", "black powder-coated steel"),
                              ("ph", "blue_metal_plate", "scratched painted steel panel (photo, 2.5m tile)")],
    "grunge_masks": [("acg", "SurfaceImperfections015", "dust overlay"),
                     ("acg", "SurfaceImperfections017", "dirt overlay")],
    "concrete_floor": [("ph", "hangar_concrete_floor", "scratched/scuffed flat hangar floor, 2m tile"),
                       ("ph", "smooth_concrete_floor", "worn smooth concrete floor, 2m tile"),
                       ("acg", "Concrete048", "clean beige-grey concrete floor (photogrammetry)")],
}
HDRIS = ["empty_warehouse_01", "small_hangar_01", "autoshop_01"]
MODEL_IDS = ["service_pistol", "rubber_boots", "garden_gloves_01", "old_military_crate", "bolt_action_rifle_7_62"]
PH_MAPS = ["Diffuse", "nor_gl", "Rough", "Displacement", "AO", "arm", "Metal"]

UA = {"User-Agent": "sgt-morgan-research/1.0"}

def fetch(url, dest):
    t0 = time.time()
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk: break
            f.write(chunk)
    return os.path.getsize(dest), time.time() - t0

def api_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

def do_acg(aid, need, note):
    d = api_json("https://ambientcg.com/api/v2/full_json?id=%s&include=downloadData,tagData,dimensionsData" % aid)
    a = d["foundAssets"][0]
    dls = a["downloadFolders"]["default"]["downloadFiletypeCategories"]["zip"]["downloads"]
    two = [x for x in dls if x["attribute"] == "2K-JPG"][0]
    folder = os.path.join(TEX, aid); os.makedirs(folder, exist_ok=True)
    zpath = os.path.join(folder, two["fileName"])
    if not os.path.exists(zpath) or os.path.getsize(zpath) != two["size"]:
        size, dt = fetch(two["downloadLink"], zpath)
    else:
        size, dt = os.path.getsize(zpath), 0.0
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        # guard against path traversal
        for n in names:
            if n.startswith("/") or ".." in n: raise RuntimeError("bad zip member " + n)
        z.extractall(folder)
    maps = sorted(n for n in names if n.lower().endswith((".jpg", ".png")))
    return {"id": aid, "source": "ambientCG", "need": need, "note": note,
            "url": a["shortLink"], "download": two["downloadLink"], "zip_bytes": size, "dl_seconds": round(dt, 1),
            "license": "CC0 1.0 (https://docs.ambientcg.com/license/)", "creation_method": a.get("creationMethod"),
            "tags": a.get("tags"), "tile_cm": [a.get("dimensionX"), a.get("dimensionY")],
            "resolution": "2K", "folder": folder, "maps": maps}

def do_ph_texture(aid, need, note):
    files = api_json("https://api.polyhaven.com/files/%s" % aid)
    info = api_json("https://api.polyhaven.com/info/%s" % aid)
    folder = os.path.join(TEX, aid); os.makedirs(folder, exist_ok=True)
    maps, total, dt_total = [], 0, 0.0
    for m in PH_MAPS:
        if m in files and "2k" in files[m] and "jpg" in files[m]["2k"]:
            url = files[m]["2k"]["jpg"]["url"]
            dest = os.path.join(folder, os.path.basename(url))
            if not os.path.exists(dest):
                size, dt = fetch(url, dest); total += size; dt_total += dt
            maps.append(os.path.basename(dest))
    return {"id": aid, "source": "Poly Haven", "need": need, "note": note,
            "url": "https://polyhaven.com/a/" + aid, "download": "https://api.polyhaven.com/files/" + aid,
            "zip_bytes": total, "dl_seconds": round(dt_total, 1),
            "license": "CC0 1.0 (https://polyhaven.com/license)", "authors": info.get("authors"),
            "tags": info.get("tags"), "tile_cm": [round(x / 10, 1) for x in info.get("dimensions", [0, 0])],
            "resolution": "2K", "folder": folder, "maps": maps}

def do_hdri(hid):
    files = api_json("https://api.polyhaven.com/files/%s" % hid)
    info = api_json("https://api.polyhaven.com/info/%s" % hid)
    url = files["hdri"]["2k"]["hdr"]["url"]
    dest = os.path.join(HDRI, os.path.basename(url))
    size, dt = fetch(url, dest) if not os.path.exists(dest) else (os.path.getsize(dest), 0.0)
    return {"id": hid, "source": "Poly Haven", "type": "hdri", "url": "https://polyhaven.com/a/" + hid,
            "download": url, "bytes": size, "dl_seconds": round(dt, 1), "license": "CC0 1.0",
            "tags": info.get("tags"), "categories": info.get("categories"), "evs_cap": info.get("evs_cap"),
            "whitebalance": info.get("whitebalance"), "authors": info.get("authors"), "path": dest}

def do_model(mid):
    files = api_json("https://api.polyhaven.com/files/%s" % mid)
    info = api_json("https://api.polyhaven.com/info/%s" % mid)
    g = files["gltf"]["1k"]["gltf"]
    folder = os.path.join(MODELS, mid); os.makedirs(os.path.join(folder, "textures"), exist_ok=True)
    total, dt_total = 0, 0.0
    size, dt = fetch(g["url"], os.path.join(folder, os.path.basename(g["url"]))); total += size; dt_total += dt
    for rel, inc in g.get("include", {}).items():
        if ".." in rel or rel.startswith("/"): continue
        dest = os.path.join(folder, rel); os.makedirs(os.path.dirname(dest), exist_ok=True)
        size, dt = fetch(inc["url"], dest); total += size; dt_total += dt
    return {"id": mid, "source": "Poly Haven", "type": "model", "url": "https://polyhaven.com/a/" + mid,
            "format": "glTF 2.0 + 1K JPG textures", "bytes": total, "dl_seconds": round(dt_total, 1),
            "license": "CC0 1.0", "tags": info.get("tags"), "categories": info.get("categories"),
            "authors": info.get("authors"), "folder": folder, "files": sorted(os.listdir(folder))}

jobs = []
for need, items in SELECTION.items():
    for src, aid, note in items:
        jobs.append((do_acg if src == "acg" else do_ph_texture, (aid, need, note)))
for h in HDRIS: jobs.append((do_hdri, (h,)))
for m in MODEL_IDS: jobs.append((do_model, (m,)))

t_all = time.time()
results, errors = [], []
with cf.ThreadPoolExecutor(max_workers=4) as ex:
    futs = {ex.submit(fn, *args): (fn.__name__, args) for fn, args in jobs}
    for fut in cf.as_completed(futs):
        name, args = futs[fut]
        try:
            r = fut.result(); results.append(r)
            print(f"OK   {name:<14} {args[0]:<26} {r.get('zip_bytes', r.get('bytes', 0)) / 1e6:6.1f} MB  {r.get('dl_seconds')}s", flush=True)
        except Exception as e:
            errors.append({"job": name, "args": list(args), "error": repr(e)})
            print(f"FAIL {name:<14} {args[0]:<26} {e!r}", flush=True)

manifest = {
    "generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    "total_seconds": round(time.time() - t_all, 1),
    "textures": sorted([r for r in results if r.get("maps") is not None], key=lambda r: (r["need"], r["id"])),
    "hdris": [r for r in results if r.get("type") == "hdri"],
    "models": [r for r in results if r.get("type") == "model"],
    "errors": errors,
}
json.dump(manifest, open(os.path.join(TEX, "manifest.json"), "w"), indent=1)
print("wrote", os.path.join(TEX, "manifest.json"), "in", manifest["total_seconds"], "s; errors:", len(errors))
