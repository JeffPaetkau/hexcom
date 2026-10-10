"""Install MPFB 2.0.17 and the MakeHuman packs into the project's Blender user resources.

Run by scripts/setup_session.sh with BLENDER_USER_RESOURCES pointing at cache/blender_user, so
Jeff's own Blender preferences and add-ons are never touched (spec 18 §4.2.1, §4.2.3):

  blender -b --python-exit-code 1 --python scripts/setup/mpfb_install.py -- \
      --zip assets/mpfb/add-on-mpfb-v2.0.17.zip --packs assets/mpfb/packs --report cache/stamps/mpfb.json

Idempotent: the extension is installed only if its manifest is absent, and a pack is extracted only
if MPFB's data directory has no packs/<name>.json for it. Exits non-zero on failure.
"""
import argparse
import glob
import json
import os
import sys
import time
import zipfile

import bpy

MODULE = "bl_ext.user_default.mpfb"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--zip", required=True)
    p.add_argument("--packs", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args(argv)
    t0 = time.time()

    ext_dir = bpy.utils.user_resource('EXTENSIONS')
    manifest = os.path.join(ext_dir, "user_default", "mpfb", "blender_manifest.toml")
    print("user extensions:", ext_dir)
    if not os.path.exists(manifest):
        res = bpy.ops.extensions.package_install_files(
            filepath=os.path.abspath(a.zip), repo="user_default", enable_on_install=True, overwrite=True)
        print("package_install_files:", res)
    if MODULE not in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_enable(module=MODULE)
    bpy.ops.wm.save_userpref()

    from bl_ext.user_default.mpfb.services.assetservice import AssetService
    from bl_ext.user_default.mpfb.services.locationservice import LocationService
    data = LocationService.get_user_data()
    os.makedirs(data, exist_ok=True)
    print("MPFB user data:", data)

    extracted = []
    for zp in sorted(glob.glob(os.path.join(a.packs, "*_cc0.zip"))):
        name = os.path.basename(zp)[:-len("_cc0.zip")]
        if os.path.exists(os.path.join(data, "packs", name + ".json")):
            continue
        with zipfile.ZipFile(zp) as z:
            root = os.path.abspath(data)
            for n in z.namelist():
                t = os.path.abspath(os.path.join(root, n))
                if not t.startswith(root + os.sep):
                    raise RuntimeError(f"zip member escapes the data folder: {n}")
            z.extractall(root)
        extracted.append(name)
        print("extracted pack:", name)

    installed = AssetService.system_assets_pack_is_installed()
    packs = sorted(AssetService.get_pack_names())
    report = {
        "blender": bpy.app.version_string,
        "extension_dir": os.path.dirname(manifest),
        "user_data": data,
        "system_assets_installed": bool(installed),
        "packs": packs,
        "extracted_this_run": extracted,
        "seconds": round(time.time() - t0, 1),
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
    with open(a.report, "w", newline="\n") as f:
        json.dump(report, f, indent=1)
    print("system assets installed:", installed)
    print("packs (%d): %s" % (len(packs), ", ".join(packs)))
    if not installed or len(packs) < 11:
        print("MPFB install incomplete", file=sys.stderr)
        sys.exit(1)


main()
