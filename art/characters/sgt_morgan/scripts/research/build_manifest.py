#!/usr/bin/env python3
"""Build (and re-download from) the asset manifest for the Sgt. Morgan project.

  python3 -I build_manifest.py <assets_root> <contact_sheet.png>          # build/refresh manifest, verify maps, draw sheet
  python3 -I build_manifest.py <assets_root> --restore                     # setup mode: download anything missing/short, extract zips

Schema (assets/manifest.json, version 2): every asset lists its *files* with an exact download URL and byte size so a
fresh container can be restored without any API call. Zip files carry "extract": true. Assets fetched by hand
(Google Drive / JS-only download pages) carry "manual": true and a "source_page" so a human can refetch them.
Run with system python3 -I from OUTSIDE the asset folders (paths are passed as arguments only).
"""
import json, os, sys, time, zipfile, hashlib, urllib.request, concurrent.futures as cf

ROOT = os.path.abspath(sys.argv[1])
RESTORE = "--restore" in sys.argv
SHEET = next((a for a in sys.argv[2:] if a.endswith(".png")), None)
TEX, HDRI, MODELS = (os.path.join(ROOT, d) for d in ("textures", "hdri", "models"))
MAN_PATH = os.path.join(ROOT, "manifest.json")   # assets/manifest.json is whitelisted in .gitignore
UA = {"User-Agent": "sgt-morgan-research/1.0"}
ACG_LIC = {"license": "CC0 1.0", "license_url": "https://docs.ambientcg.com/license/"}
PH_LIC = {"license": "CC0 1.0", "license_url": "https://polyhaven.com/license"}

# ---- selection: need -> [(source, id, note, status)]  status: "primary" | "alt" | "rejected" ------------------------
SEL = [
 # Cordura / ballistic nylon (plate carrier, pouches, webbing)
 ("cordura_nylon_weave", "acg", "Fabric063", "dark olive-brown tight weave; closest colour+scale match to the coyote/OD vest in ref", "primary"),
 ("cordura_nylon_weave", "acg", "Fabric061", "grey basket weave with fibre fuzz; good normal/rough for 1000D nylon, tint colour", "alt"),
 ("cordura_nylon_weave", "acg", "Fabric066", "grey plain weave, finer than 061; good for 500D pouches, tint colour", "alt"),
 ("cordura_nylon_weave", "ph", "book_pattern", "olive plain-woven cotton book cloth (col1 olive, col2 maroon); colour already vest-like", "alt"),
 ("cordura_nylon_weave", "acg", "Fabric048", "REJECTED: procedural quilted white polyester squares, not a weave", "rejected"),
 ("cordura_nylon_weave", "3dt", "3dtextures_Fabric_Nylon_Weave_001", "1K chunky orange basket weave; only useful as a webbing normal map; fetched by hand from Google Drive", "alt"),
 # Webbing straps
 ("webbing_strap", "ph", "poly_wool_herringbone", "grey herringbone twill - matches 25 mm webbing weave direction/scale when tiled ~2.5 cm", "primary"),
 # Ripstop / twill (combat shirt torso + sleeves, trousers)
 ("ripstop_twill_fabric", "ph", "denim_fabric_05", "dark grey matte twill, 27 cm tile; trouser base, add procedural ripstop grid", "primary"),
 ("ripstop_twill_fabric", "ph", "denim_fabric_06", "dark worn twill, 25 cm tile", "alt"),
 ("ripstop_twill_fabric", "acg", "Fabric082A", "fine grey smooth woven (procedural); shirt sleeves", "alt"),
 ("ripstop_twill_fabric", "ph", "cotton_jersey", "beige matte knit jersey; combat-shirt stretch torso under the carrier", "alt"),
 # Fleece / knit
 ("fleece_knit", "ph", "knitted_fleece", "brown knitted fleece, 27 cm tile; neck gaiter", "primary"),
 ("fleece_knit", "ph", "polar_fleece", "cream polar fleece, 27 cm tile", "alt"),
 # Leather
 ("leather", "acg", "Leather032", "black scratched leather, 45 cm tile; boots", "primary"),
 ("leather", "acg", "Leather037", "dark brown clean full-grain (multi-angle photo); glove palms, tint", "alt"),
 # Rubber
 ("rubber", "acg", "Rubber004", "black grainy rubber, 75 cm tile; soles/grips", "primary"),
 # Dark metal (rifle)
 ("metal_dark_anodised_parkerised", "acg", "Metal038", "dark scratched steel, glossy; parkerised receiver/barrel base", "primary"),
 ("metal_dark_anodised_parkerised", "acg", "Metal063", "aged dark glossy metal (photo approx)", "alt"),
 ("metal_dark_anodised_parkerised", "acg", "Metal046B", "black dirty metal, procedural", "alt"),
 ("metal_dark_anodised_parkerised", "acg", "Metal050C", "rough scratched aluminium (near-white albedo = bare metal F0); tint for anodising", "alt"),
 # Matte polymer
 ("matte_polymer", "acg", "Plastic012B", "black scratched plastic; magazine, grip, kneepads", "primary"),
 ("matte_polymer", "acg", "Plastic018B", "grey dirty scratched plastic; pauldron plates", "alt"),
 # Worn paint over metal
 ("worn_paint_over_metal", "acg", "Metal027", "black powder-coated steel", "primary"),
 ("worn_paint_over_metal", "ph", "blue_metal_plate", "scratched painted steel panel (photo, 2.5 m tile) - scratch mask source", "alt"),
 # Grunge masks
 ("grunge_masks", "acg", "SurfaceImperfections015", "dust overlay with opacity", "primary"),
 ("grunge_masks", "acg", "SurfaceImperfections017", "dirt speckle overlay with opacity", "alt"),
 # Floor
 ("concrete_floor", "ph", "concrete_floor_worn_001", "grey worn plain concrete floor, 3 m tile; closest to the ref's dusty polished floor", "primary"),
 ("concrete_floor", "ph", "hangar_concrete_floor", "dark scratched flat hangar floor, 2 m tile", "alt"),
 ("concrete_floor", "ph", "smooth_concrete_floor", "orange-brown worn smooth floor - colour too warm", "alt"),
 ("concrete_floor", "acg", "Concrete048", "clean beige-grey indoor concrete (photogrammetry) - too clean/light", "alt"),
 ("concrete_floor", "cgb", "cgbookcase_PolishedConcrete01", "polished concrete 2K PNG (BaseColor/Height/Normal-DX/Roughness, RGBA); blend its roughness/normal under concrete_floor_worn_001 colour for the reflective finish seen in ref", "alt"),
]
CGB = {"cgbookcase_PolishedConcrete01": ("PolishedConcrete01_MR_2K.zip", "https://cgbookcase-volume.b-cdn.net/t/PolishedConcrete01_MR_2K.zip", 14325870,
                                         "https://www.cgbookcase.com/textures/polished-concrete-01")}
CGB_HEADERS = {"Referer": "https://www.cgbookcase.com/"}   # the b-cdn.net origin answers 403 without it
HDRIS = [("empty_warehouse_01", "primary", "derelict warehouse, fluorescent + daylight, concrete; 16 EV; closest to the hangar backdrop"),
         ("small_hangar_01", "alt", "aircraft hangar, natural light, low contrast; 12 EV"),
         ("autoshop_01", "alt", "garage/workshop artificial light; 8 EV")]
PH_MODELS = [("service_pistol", "pistol reference (vintage semi-auto, 1K)"), ("rubber_boots", "boot-shaped base mesh, 1K, two material variants"),
             ("garden_gloves_01", "glove base mesh"), ("old_military_crate", "scene prop"), ("bolt_action_rifle_7_62", "rifle material/scale reference")]
TBM = ["pouch_01", "pouch_02", "safety_helmet", "wellington_boot", "seatbelt_clip", "watch_strap_buckle"]
OGA = [("oga_m4a1_nisu", "https://opengameart.org/content/m4a1-assault-rifle", "https://opengameart.org/sites/default/files/m4a1_0.zip", "m4a1_0.zip",
        "M4A1 FBX, 5159 verts/9236 tris, 2K PBR PNGs (base colour, normal, rough, metal, height); mid-poly, good blockout/proportion reference", "nisu"),
       ("oga_m4a1_lowpoly_mallninjamax", "https://opengameart.org/content/low-poly-m4a1", "https://opengameart.org/sites/default/files/m4a1.zip", "m4a1.zip",
        "167-tri hand-painted low-poly M4A1 (.blend + FBX); silhouette reference only", "MallNinjaMax")]
PH_MAPS = ["Diffuse", "nor_gl", "Rough", "Displacement", "AO", "arm", "Metal"]
# TheBaseMesh: the Wix product page of each asset (https://www.thebasemesh.com/product-page/<slug>) embeds the
# hashed archive URL; recovered 2026-10-06 and verified by sha256 against the hand-downloaded zips.
TBM_URLS = {"pouch_01": "https://www.thebasemesh.com/_files/archives/b36d2d_bc758246f9c3478a87a2045bae3d04ce.zip",
            "pouch_02": "https://www.thebasemesh.com/_files/archives/b36d2d_83634159ebb545afb63f7707cc8df63e.zip",
            "safety_helmet": "https://www.thebasemesh.com/_files/archives/b36d2d_2be2c461ff2a4e49924c3591c8669168.zip",
            "wellington_boot": "https://www.thebasemesh.com/_files/archives/b36d2d_8c197c28bcf140fca9d9d7e45a9a2f69.zip",
            "seatbelt_clip": "https://www.thebasemesh.com/_files/archives/b36d2d_692f118fb7a84f218d98d11a5d99f7cd.zip",
            "watch_strap_buckle": "https://www.thebasemesh.com/_files/archives/b36d2d_64c19677f8534b8a9dfc35ad709a02dc.zip"}
TBM_SLUG = {"pouch_01": "pouch-01", "pouch_02": "pouch-02", "safety_helmet": "safety-helmet", "wellington_boot": "wellington-boot",
            "seatbelt_clip": "seatbelt-clip", "watch_strap_buckle": "watch-strap-buckle"}
# 3dtextures.me Fabric_Nylon_Weave_001: Google Drive *file* ids (the folder itself is JS-only, but single files download
# with drive.usercontent.google.com; verified by sha256 2026-10-06).
GDRIVE_FILES = {"Fabric_Nylon_weave_001_ambientOcclusion.jpg": ("1XkbQ84_mKV3W507HA0bTk5EtIyBmch-B", 324232),
                "Fabric_Nylon_weave_001_basecolor.jpg": ("1lgqC2teDhvncF-fyfd8ddEJQ0XVq89Gf", 202412),
                "Fabric_Nylon_weave_001_height.png": ("1DvmYO-HtVh8ZnkrTPrT30OhjRvpnteYk", 213965),
                "Fabric_Nylon_weave_001_normal.jpg": ("1mKz818FBSEXLrWx5z3py3qq8L5zhknob", 368633),
                "Fabric_Nylon_weave_001_opacity.jpg": ("1G2f5jOfQuDOMC1OwcAse2d53RehG2Ugz", 40742),
                "Fabric_Nylon_weave_001_roughness.jpg": ("1h6HBlA6383WcjFIlUMVSh8swDFD9T4Yn", 241750),
                "Material_1561.jpg": ("1zFGrOXp-K0UwTUtTsBh9-oZ8_aOwNGhV", 121344)}
GDRIVE_URL = "https://drive.usercontent.google.com/download?id=%s&export=download&confirm=t"
GDRIVE_HEADERS = {"User-Agent": "Mozilla/5.0"}


def api(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return json.load(r)
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(2 * (i + 1))


def fetch(url, dest, headers=None):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    t0 = time.time()
    with urllib.request.urlopen(urllib.request.Request(url, headers={**UA, **(headers or {})}), timeout=900) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk: break
            f.write(chunk)
    return os.path.getsize(dest), time.time() - t0


def safe_extract(zpath, folder):
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            if n.startswith("/") or ".." in n: raise RuntimeError("bad zip member " + n)
        z.extractall(folder)
        return z.namelist()


def ensure(fileinfo):
    """Download a file entry if missing or wrong size; extract if zip. Returns (downloaded_bool, seconds)."""
    dest = os.path.join(ROOT, fileinfo["path"])
    ok = os.path.exists(dest) and (fileinfo.get("bytes") in (None, os.path.getsize(dest)))
    dl, dt = False, 0.0
    if not ok:
        if not fileinfo.get("url"):
            print("MISSING (manual asset, no URL):", fileinfo["path"]); return False, 0.0
        size, dt = fetch(fileinfo["url"], dest, fileinfo.get("headers")); dl = True
        if fileinfo.get("bytes") not in (None, size):
            print(f"WARN size mismatch {fileinfo['path']}: expected {fileinfo.get('bytes')} got {size}")
    if fileinfo.get("extract") and (dl or not all(os.path.exists(os.path.join(ROOT, p)) for p in fileinfo.get("extracted", [])[:1])):
        safe_extract(dest, os.path.dirname(dest))
    return dl, dt


def rel(p): return os.path.relpath(p, ROOT)


def classify(name):
    n = name.lower()
    if any(k in n for k in ("_color", "_diff", "_col1", "_col2", "_col_", "basecolor", "base_color", "albedo")): return "color"
    if "nor_gl" in n or "normalgl" in n: return "normal_gl"
    if "nor_dx" in n or "normaldx" in n or n.endswith("_normal.jpg") or n.endswith("_normal.png"): return "normal_dx"
    if "rough" in n: return "roughness"
    if "_disp" in n or "displacement" in n or "height" in n: return "displacement"
    if "ambientocclusion" in n or "_ao_" in n or n.endswith("_ao.jpg"): return "ao"
    if "_arm" in n: return "arm(ao,rough,metal)"
    if "metal" in n: return "metalness"
    if "opacity" in n: return "opacity"
    if n.endswith(".png") and "_" not in n.rsplit("/", 1)[-1]: return "preview"
    return "other"


# ------------------------------------------------------------------ builders
def build_acg(ids):
    d = api("https://ambientcg.com/api/v2/full_json?id=%s&include=downloadData,tagData,dimensionsData" % ",".join(ids))
    out = {}
    for a in d["foundAssets"]:
        dls = a["downloadFolders"]["default"]["downloadFiletypeCategories"]["zip"]["downloads"]
        two = [x for x in dls if x["attribute"] == "2K-JPG"][0]
        folder = os.path.join(TEX, a["assetId"])
        out[a["assetId"]] = {
            "id": a["assetId"], "kind": "texture", "source": "ambientCG", "source_page": a["shortLink"], **ACG_LIC,
            "creation_method": a.get("creationMethod"), "tags": a.get("tags"), "tile_cm": [a.get("dimensionX"), a.get("dimensionY")],
            "resolution": "2K", "folder": rel(folder),
            "files": [{"path": rel(os.path.join(folder, two["fileName"])), "url": two["downloadLink"], "bytes": two["size"], "extract": True}]}
    return out


def build_ph_texture(aid):
    files, info = api("https://api.polyhaven.com/files/%s" % aid), api("https://api.polyhaven.com/info/%s" % aid)
    folder = os.path.join(TEX, aid); fl = []
    for m in PH_MAPS:
        if m in files and "2k" in files[m] and "jpg" in files[m]["2k"]:
            e = files[m]["2k"]["jpg"]
            fl.append({"path": rel(os.path.join(folder, os.path.basename(e["url"]))), "url": e["url"], "bytes": e["size"], "md5": e.get("md5")})
    return {"id": aid, "kind": "texture", "source": "Poly Haven", "source_page": "https://polyhaven.com/a/" + aid, **PH_LIC,
            "authors": info.get("authors"), "tags": info.get("tags"), "tile_cm": [round(x / 10, 1) for x in info.get("dimensions", [0, 0])],
            "resolution": "2K", "folder": rel(folder), "files": fl}


def build_hdri(hid, status, note):
    files, info = api("https://api.polyhaven.com/files/%s" % hid), api("https://api.polyhaven.com/info/%s" % hid)
    e = files["hdri"]["2k"]["hdr"]
    return {"id": hid, "kind": "hdri", "need": "environment_hdri", "status": status, "note": note, "source": "Poly Haven",
            "source_page": "https://polyhaven.com/a/" + hid, **PH_LIC, "authors": info.get("authors"), "tags": info.get("tags"),
            "categories": info.get("categories"), "evs_cap": info.get("evs_cap"), "whitebalance": info.get("whitebalance"), "resolution": "2K",
            "folder": rel(HDRI), "files": [{"path": rel(os.path.join(HDRI, os.path.basename(e["url"]))), "url": e["url"], "bytes": e["size"], "md5": e.get("md5")}]}


def build_ph_model(mid, note):
    files, info = api("https://api.polyhaven.com/files/%s" % mid), api("https://api.polyhaven.com/info/%s" % mid)
    g = files["gltf"]["1k"]["gltf"]; folder = os.path.join(MODELS, mid)
    fl = [{"path": rel(os.path.join(folder, os.path.basename(g["url"]))), "url": g["url"], "bytes": g["size"], "md5": g.get("md5")}]
    for r_, inc in g.get("include", {}).items():
        if ".." in r_ or r_.startswith("/"): continue
        fl.append({"path": rel(os.path.join(folder, r_)), "url": inc["url"], "bytes": inc["size"], "md5": inc.get("md5")})
    return {"id": mid, "kind": "model", "need": "model_reference", "status": "alt", "note": note, "format": "glTF 2.0 + 1K JPG",
            "source": "Poly Haven", "source_page": "https://polyhaven.com/a/" + mid, **PH_LIC, "authors": info.get("authors"),
            "tags": info.get("tags"), "categories": info.get("categories"), "folder": rel(folder), "files": fl}


def local_files(folder, exts):
    out = []
    for dp, _, names in os.walk(folder):
        for n in sorted(names):
            if n.lower().endswith(exts):
                p = os.path.join(dp, n); out.append({"path": rel(p), "url": None, "bytes": os.path.getsize(p)})
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ main
t_all = time.time()
if RESTORE:
    man = json.load(open(MAN_PATH))
    n_dl, errs = 0, []
    for a in man["assets"]:
        if a.get("status") == "rejected": continue
        for f in a["files"]:
            try:
                dl, dt = ensure(f); n_dl += dl
                if dl: print(f"restored {f['path']} {f['bytes'] / 1e6:.1f} MB {dt:.1f}s")
            except Exception as e:
                errs.append((f["path"], repr(e))); print("FAIL", f["path"], repr(e))
    print(f"restore done: {n_dl} files downloaded, {len(errs)} errors, {time.time() - t_all:.1f}s"); sys.exit(1 if errs else 0)

assets = []
acg_ids = sorted({aid for _, src, aid, _, _ in SEL if src == "acg"})
acg = build_acg(acg_ids)
with cf.ThreadPoolExecutor(6) as ex:
    ph_tex = dict(zip([aid for _, src, aid, _, _ in SEL if src == "ph"], ex.map(build_ph_texture, [aid for _, src, aid, _, _ in SEL if src == "ph"])))
    hdris = list(ex.map(lambda h: build_hdri(*h), HDRIS))
    ph_models = list(ex.map(lambda m: build_ph_model(*m), PH_MODELS))
for need, src, aid, note, status in SEL:
    if src == "acg": a = dict(acg[aid])
    elif src == "ph": a = dict(ph_tex[aid])
    elif src == "cgb":
        zname, url, size, page = CGB[aid]; folder = os.path.join(TEX, aid)
        a = {"id": aid, "kind": "texture", "source": "cgbookcase.com", "source_page": page, "license": "CC0 1.0",
             "license_url": "https://www.cgbookcase.com/about", "resolution": "2K", "folder": rel(folder),
             "files": [{"path": rel(os.path.join(folder, zname)), "url": url, "bytes": size, "extract": True, "headers": CGB_HEADERS}]}
    else:  # 3dtextures, fetched by hand
        folder = os.path.join(TEX, aid)
        a = {"id": aid, "kind": "texture", "source": "3dtextures.me",
             "source_page": "https://3dtextures.me/2020/06/11/fabric-nylon-weave-001/",
             "drive_folder": "https://drive.google.com/drive/folders/1iVCAQn3VTrUD9tUKHldrv1zMIdB0BjNB",
             "license": "CC0 1.0 (site states all textures CC0)", "license_url": "https://3dtextures.me/about/", "resolution": "1K",
             "folder": rel(folder),
             "files": [{"path": rel(os.path.join(folder, n)), "url": GDRIVE_URL % gid, "bytes": size, "headers": GDRIVE_HEADERS}
                       for n, (gid, size) in sorted(GDRIVE_FILES.items())]}
    a.update({"need": need, "note": note, "status": status})
    assets.append(a)
assets += hdris + ph_models
for t in TBM:
    folder = os.path.join(MODELS, "thebasemesh", t)
    zp = os.path.join(folder, t + ".zip")
    fl = [{"path": rel(zp), "url": TBM_URLS[t], "bytes": os.path.getsize(zp), "extract": True, "sha256": sha256(zp),
           "extracted": [rel(os.path.join(folder, n)) for n in zipfile.ZipFile(zp).namelist() if not n.endswith("/")]}]
    assets.append({"id": "thebasemesh_" + t, "kind": "model", "need": "model_base_mesh", "status": "alt",
                   "note": "TheBaseMesh CC0 base mesh (quads, UV'd, no materials); zip = fbx+glb+obj",
                   "format": "zip with glb/fbx/obj", "source": "thebasemesh.com",
                   "source_page": "https://www.thebasemesh.com/product-page/" + TBM_SLUG[t],
                   "license": "CC0 1.0 (FAQ: 'You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission')",
                   "license_url": "https://www.thebasemesh.com/faq", "folder": rel(folder), "files": fl})
for mid, page, url, zname, note, author in OGA:
    folder = os.path.join(MODELS, mid); zp = os.path.join(folder, zname)
    extracted = [rel(os.path.join(folder, n)) for n in zipfile.ZipFile(zp).namelist() if not n.endswith("/")]
    assets.append({"id": mid, "kind": "model", "need": "model_reference_rifle", "status": "alt", "note": note, "authors": [author],
                   "format": "zip (FBX + PNG textures)", "source": "OpenGameArt", "source_page": page, "license": "CC0 1.0",
                   "license_url": "https://creativecommons.org/publicdomain/zero/1.0/", "folder": rel(folder),
                   "files": [{"path": rel(zp), "url": url, "bytes": os.path.getsize(zp), "extract": True, "extracted": extracted}]})

# ---- ensure files present, extract zips, verify images --------------------------------------------------------------
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = 400_000_000
bad, dl_log = [], []
for a in assets:
    if a.get("status") == "rejected" and not all(os.path.exists(os.path.join(ROOT, f["path"])) for f in a["files"]): continue
    for f in a["files"]:
        try:
            dl, dt = ensure(f)
            if dl: dl_log.append((f["path"], f["bytes"], round(dt, 1)))
            if f.get("extract"):
                names = safe_extract(os.path.join(ROOT, f["path"]), os.path.join(ROOT, a["folder"])) if not f.get("extracted") else None
                if names: f["extracted"] = [rel(os.path.join(ROOT, a["folder"], n)) for n in names if not n.endswith("/")]
        except Exception as e:
            bad.append((f["path"], repr(e)))
    if a["kind"] == "texture":
        folder = os.path.join(ROOT, a["folder"]); a["maps"] = {}
        for n in sorted(os.listdir(folder)):
            if n.lower().endswith((".jpg", ".png")):
                try:
                    with Image.open(os.path.join(folder, n)) as im:
                        im.load(); a["maps"][n] = {"kind": classify(n), "px": list(im.size), "mode": im.mode}
                except Exception as e:
                    bad.append((os.path.join(a["folder"], n), repr(e)))
        a["map_kinds"] = sorted({v["kind"] for v in a["maps"].values()})
        a["resolution_px"] = sorted({tuple(v["px"]) for v in a["maps"].values() if v["kind"] not in ("preview",)})
        a["resolution_px"] = [list(s) for s in a["resolution_px"]]
    a["total_bytes"] = sum(f.get("bytes") or 0 for f in a["files"])

IMPORT_JSON = os.path.join(os.path.dirname(ROOT), "renders", "research", "model_import_test.json")
if os.path.exists(IMPORT_JSON):   # produced by: blender -b --python scripts/research/model_import_test.py -- assets/models renders/research/model_import_test.json
    imp = json.load(open(IMPORT_JSON))
    for a in assets:
        if a["kind"] != "model": continue
        sub = os.path.relpath(os.path.join(ROOT, a["folder"]), MODELS)
        rows = [r for r in imp if r["file"].startswith(sub + "/") or r["file"].startswith(sub + os.sep)]
        if rows:
            a["import_test"] = [{k: r[k] for k in ("file", "ok", "seconds", "objects", "verts", "tris", "quads", "ngons", "dims_m", "has_uv", "materials", "images") if k in r} for r in rows]

man = {"schema": 2, "generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "assets_root": "assets/ (paths below are relative to it)",
       "restore_command": "python3 -I scripts/research/build_manifest.py assets --restore",
       "counts": {k: sum(1 for a in assets if a["kind"] == k) for k in ("texture", "hdri", "model")},
       "total_bytes": sum(a["total_bytes"] for a in assets), "downloaded_this_run": dl_log, "errors": bad, "assets": assets}
json.dump(man, open(MAN_PATH, "w"), indent=1)
print(f"wrote {MAN_PATH}: {man['counts']} total {man['total_bytes'] / 1e6:.0f} MB, {len(dl_log)} downloads, {len(bad)} errors, {time.time() - t_all:.1f}s")
for b in bad: print("BAD", b)
for a in assets:
    if a["kind"] == "texture":
        print(f"{a['status']:<8} {a['need']:<32} {a['id']:<34} {a['source']:<12} px={a['resolution_px']} kinds={a['map_kinds']}")

# ---- contact sheet of colour maps, grouped by need -------------------------------------------------------------------
if SHEET:
    tiles = []
    for a in assets:
        if a["kind"] != "texture": continue
        cols_ = [n for n, v in a["maps"].items() if v["kind"] == "color"]
        for n in cols_[:1] if a["id"] != "book_pattern" else cols_[:1]:
            tiles.append((a["need"], a["status"], a["id"], os.path.join(ROOT, a["folder"], n), a.get("tile_cm")))
    order = {"primary": 0, "alt": 1, "rejected": 2}
    tiles.sort(key=lambda t: (t[0], order[t[1]], t[2]))
    TILE, PAD, LABEL, cols = 300, 10, 48, 6
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (TILE + PAD) + PAD, rows * (TILE + LABEL + PAD) + PAD), (28, 28, 30))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except Exception:
        font = font_b = ImageFont.load_default()
    for i, (need, status, aid, p, tile_cm) in enumerate(tiles):
        r, c = divmod(i, cols); x = PAD + c * (TILE + PAD); y = PAD + r * (TILE + LABEL + PAD)
        with Image.open(p) as im:
            im = im.convert("RGB"); w, h = im.size
            sheet.paste(im.resize((TILE, TILE // 2), Image.LANCZOS), (x, y))                       # whole tile, squashed
            sheet.paste(im.resize((TILE // 2, TILE // 2), Image.LANCZOS), (x, y + TILE // 2))      # whole tile
            sheet.paste(im.crop((0, 0, w // 4, h // 4)).resize((TILE // 2, TILE // 2), Image.LANCZOS), (x + TILE // 2, y + TILE // 2))  # 25% crop
        col = {"primary": (120, 230, 140), "alt": (230, 230, 230), "rejected": (240, 100, 100)}[status]
        draw.text((x, y + TILE + 2), f"{aid}  [{status}]", fill=col, font=font_b)
        draw.text((x, y + TILE + 19), need, fill=(170, 200, 230), font=font)
        draw.text((x, y + TILE + 34), f"tile {tile_cm} cm   left: full tile / right: 25% crop" if tile_cm else "left: full tile / right: 25% crop", fill=(150, 150, 150), font=font)
    os.makedirs(os.path.dirname(SHEET), exist_ok=True); sheet.save(SHEET)
    print("contact sheet", SHEET, sheet.size, len(tiles), "colour maps")
