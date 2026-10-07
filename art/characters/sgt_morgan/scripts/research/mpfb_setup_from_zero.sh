#!/usr/bin/env bash
# Install MPFB 2.0.17 + MakeHuman CC0 asset packs into Blender 4.5 headless. Idempotent/resumable.
# Requires: blender on PATH (4.5.x), curl, unzip. ~600 MB download, ~700 MB on disk after extraction.
# Usage: scripts/research/mpfb_setup_from_zero.sh [ASSET_DIR]   (default /home/user/sgt_morgan/assets/mpfb)
set -euo pipefail
ASSET_DIR="${1:-/home/user/sgt_morgan/assets/mpfb}"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BL_VER="$(blender -b --version 2>/dev/null | head -1 | sed -E 's/Blender ([0-9]+\.[0-9]+).*/\1/')"   # e.g. 4.5
EXT_ZIP_URL="https://extensions.blender.org/download/sha256:4f0a879d64a39bf646fbf5f53601ac678855da329d650617dca5737548239a87/add-on-mpfb-v2.0.17.zip"
EXT_ZIP="$ASSET_DIR/add-on-mpfb-v2.0.17.zip"; EXT_SIZE=45031536
# MPFB user data dir for Blender 4.5 (LocationService.get_user_data()):
USERDATA="$HOME/.config/blender/$BL_VER/extensions/.user/user_default/mpfb/data"
BASE="https://files.makehumancommunity.org/asset_packs"   # mirror: https://files2.makehumancommunity.org/asset_packs
# name:bytes (Content-Length verified 2026-10-06)
PACKS="makehuman_system_assets:280737770 skins02:76112708 bodyparts05:6616507 eyebrows01:11477790 eyelashes01:3493692 pants01:21908723 shirts01:24479483 shoes01:82953569 gloves01:3192691 hats02:24018546 equipment01:18111388"

mkdir -p "$ASSET_DIR/packs"
fetch() {  # url dest expected_bytes
  local url="$1" dest="$2" want="$3"
  if [ -f "$dest" ] && [ "$(stat -c %s "$dest")" = "$want" ]; then echo "  have $(basename "$dest")"; return; fi
  echo "  downloading $(basename "$dest") ($want bytes)"
  curl -sS -L --retry 4 --retry-delay 3 -C - -o "$dest" "$url"
  [ "$(stat -c %s "$dest")" = "$want" ] || { echo "size mismatch for $dest"; exit 1; }
}

echo "== 1. MPFB extension zip"
fetch "$EXT_ZIP_URL" "$EXT_ZIP" "$EXT_SIZE"

echo "== 2. install + enable extension (bl_ext.user_default.mpfb), save userpref"
if [ ! -f "$HOME/.config/blender/$BL_VER/extensions/user_default/mpfb/blender_manifest.toml" ]; then
  blender -b --python "$SCRIPTS_DIR/mpfb_install.py" -- "$EXT_ZIP" 2>&1 | grep -E "package_install|addon_enable|enabled addons|saved userpref|Error" || true
else
  echo "  already installed"
fi

echo "== 3. asset packs -> $USERDATA"
mkdir -p "$USERDATA"
for p in $PACKS; do
  name="${p%%:*}"; bytes="${p##*:}"
  fetch "$BASE/$name/${name}_cc0.zip" "$ASSET_DIR/packs/${name}_cc0.zip" "$bytes"
  if [ ! -f "$USERDATA/packs/$name.json" ]; then
    echo "  extracting $name"
    unzip -q -o "$ASSET_DIR/packs/${name}_cc0.zip" -d "$USERDATA"     # zips have skins/ eyes/ clothes/ packs/ at root
  fi
done

echo "== 4. verify"
blender -b --python-expr "
import bpy
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.assetservice import AssetService
from bl_ext.user_default.mpfb.services.locationservice import LocationService
print('MPFB user data:', LocationService.get_user_data())
print('system assets installed:', AssetService.system_assets_pack_is_installed())
print('packs:', AssetService.get_pack_names())
" 2>&1 | grep -E "MPFB user data|system assets|packs:"
echo "== MPFB setup complete"
