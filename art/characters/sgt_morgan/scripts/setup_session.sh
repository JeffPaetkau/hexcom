#!/usr/bin/env bash
# Rebuilds the Sgt. Morgan toolchain: spec/18_pipeline_evaluation.md §4.2.
# Runs on Linux cloud containers and in Git Bash on Jeff's Windows machine. Idempotent and
# resumable: each step checks what is present, verifies sizes and hashes, and can be re-run.
# Options: --no-ai --with-depth --with-3ddfa --with-godot --no-assets --prune --check
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
BL_VER=4.5.14; BL_SERIES=4.5
AI=1; DEPTH=0; DDFA=0; GODOT=0; ASSETS=1; PRUNE=0; CHECK=0
for a in "$@"; do case "$a" in
  --no-ai) AI=0 ;; --with-depth) DEPTH=1 ;; --with-3ddfa) DDFA=1 ;; --with-godot) GODOT=1 ;;
  --no-assets) ASSETS=0 ;; --prune) PRUNE=1 ;; --check) CHECK=1 ;;
  *) echo "unknown option: $a" >&2; exit 2 ;;
esac; done
T0=$(date +%s)
say() { printf '\n== %s\n' "$*"; }
case "$(uname -s)" in
  Linux*) OS=linux ;;
  MINGW*|MSYS*|CYGWIN*) OS=windows ;;
  *) echo "unsupported system: $(uname -s)" >&2; exit 2 ;;
esac
winpath() { if [ "$OS" = windows ]; then cygpath -w "$1"; else printf '%s' "$1"; fi; }
mkdir -p assets cache/tools cache/stamps cache/blender_user renders/eval deliver
# The project's Blender preferences, MPFB and its packs live in cache/blender_user, so Jeff's own
# Blender set-up is never touched and deleting cache/ resets everything (§4.2.1).
export BLENDER_USER_RESOURCES="$(winpath "$PROJECT_DIR/cache/blender_user")"

size_of() { wc -c < "$1" | tr -d ' '; }
fetch() {  # url dest bytes sha256: resumable download, verified by size and hash
  local url=$1 dest=$2 bytes=$3 sum=$4
  mkdir -p "$(dirname "$dest")"
  if [ ! -f "$dest" ] || [ "$(size_of "$dest")" != "$bytes" ]; then
    curl -fsSL --retry 4 --retry-delay 3 -C - -o "$dest" "$url" || curl -fsSL --retry 4 -o "$dest" "$url"
  fi
  [ "$(size_of "$dest")" = "$bytes" ] || { echo "size mismatch: $dest" >&2; rm -f "$dest"; return 1; }
  echo "$sum  $dest" | sha256sum -c --status - || { echo "hash mismatch: $dest" >&2; rm -f "$dest"; return 1; }
}

say "1. Blender $BL_VER"
BLENDER="${SGT_BLENDER:-}"
if [ -z "$BLENDER" ] && [ "$OS" = linux ]; then
  if [ "$(id -u)" = 0 ]; then BL_HOME=/opt/blender; else BL_HOME="$HOME/.local/opt"; fi
  BLENDER="$BL_HOME/blender-$BL_VER-linux-x64/blender"
  if [ ! -x "$BLENDER" ]; then
    ARCH="cache/tools/blender-$BL_VER-linux-x64.tar.xz"
    fetch "https://download.blender.org/release/Blender$BL_SERIES/blender-$BL_VER-linux-x64.tar.xz" "$ARCH" \
      378045212 9ba871ff2ecd36526b77432745980b7e6664ecd0c7ca11c48849073dcfe06da3
    mkdir -p "$BL_HOME"; tar -xJf "$ARCH" -C "$BL_HOME"; rm -f "$ARCH"
  fi
  [ "$(id -u)" != 0 ] || ln -sf "$BLENDER" /usr/local/bin/blender
elif [ -z "$BLENDER" ]; then
  # An installed Blender 4.5 is used first (on Jeff's machine the MSI install, upgraded in place
  # to 4.5.14 on 2026-10-10); a portable copy is fetched only where no 4.5 is installed.
  LAD="$(cygpath -u "$LOCALAPPDATA")"
  for c in "/c/Program Files/Blender Foundation/Blender $BL_SERIES/blender.exe" \
           "$LAD/sgt_morgan/blender-$BL_VER-windows-x64/blender.exe"; do
    if [ -x "$c" ]; then BLENDER="$c"; break; fi
  done
  if [ -z "$BLENDER" ]; then
    ARCH="cache/tools/blender-$BL_VER-windows-x64.zip"
    fetch "https://download.blender.org/release/Blender$BL_SERIES/blender-$BL_VER-windows-x64.zip" "$ARCH" \
      398661046 b9533d2397ac1984db4466fb23a7a4649391cca93f6e84209f9bcc60d071c8b9
    mkdir -p "$LAD/sgt_morgan"
    /c/Windows/System32/tar.exe -xf "$(cygpath -w "$ARCH")" -C "$(cygpath -w "$LAD/sgt_morgan")"
    rm -f "$ARCH"; BLENDER="$LAD/sgt_morgan/blender-$BL_VER-windows-x64/blender.exe"
  fi
fi
BL_VERSION="$("$BLENDER" -b --factory-startup --version 2>/dev/null | head -1 | tr -d '\r')"
case "$BL_VERSION" in
  "Blender $BL_VER"*) echo "$BL_VERSION" ;;
  "Blender $BL_SERIES."*) echo "WARN: $BL_VERSION; the project was measured on $BL_VER (on Windows the $BL_VER MSI from download.blender.org upgrades an installed $BL_SERIES in place)" ;;
  *) echo "need Blender $BL_SERIES, found: $BL_VERSION" >&2; exit 3 ;;
esac
BL_ROOT="$(dirname "$(readlink -f "$BLENDER")")/$BL_SERIES/python/bin"
if [ "$OS" = windows ]; then BL_PY="$BL_ROOT/python.exe"; else BL_PY="$(ls -d "$BL_ROOT"/python3.* 2>/dev/null | head -1 || true)"; fi

say "2. Python for the setup tools"
if [ "$OS" = linux ] && command -v python3 >/dev/null; then PY=python3; else PY="$BL_PY"; fi
"$PY" -I -c 'import ssl, hashlib, zipfile, json' || { echo "no usable Python for setup" >&2; exit 3; }

say "3. Cycles device"
# captured, not tee'd to /dev/stderr: in Git Bash that reopens a redirected log and truncates it
PROBE="$("$BLENDER" -b --factory-startup --python scripts/setup/gpu_probe.py 2>/dev/null | tr -d '\r' || true)"
printf '%s\n' "$PROBE" | grep '^\[gpu\]' || true
DEVICE="$(printf '%s\n' "$PROBE" | sed -n 's/^SGT_DEVICE=//p' | tail -1)"
DEVICE="${DEVICE:-CPU}"; echo "device: $DEVICE"

say "4. MPFB 2.0.17 and the MakeHuman packs (598 MB)"
"$PY" -I scripts/setup/fetch.py list --root . --list scripts/setup/downloads.json --group mpfb --jobs 4
# not --factory-startup: the install saves preferences, and they are the project's own (cache/blender_user)
"$BLENDER" -b --python-exit-code 1 --python scripts/setup/mpfb_install.py -- \
  --zip assets/mpfb/add-on-mpfb-v2.0.17.zip --packs assets/mpfb/packs --report cache/stamps/mpfb.json

if [ "$ASSETS" = 1 ]; then
  say "5. Textures, HDRIs and reference models (assets/manifest.json, 713 MB)"
  "$PY" -I scripts/setup/fetch.py manifest --root assets --manifest assets/manifest.json --jobs 4
fi

AIPY=""
if [ "$AI" = 1 ]; then
  say "6. AI helpers (MediaPipe, rembg; Depth Anything with --with-depth)"
  VENV=assets/ai/venv
  if [ "$OS" = linux ]; then AIPY="$VENV/bin/python"; else AIPY="$VENV/Scripts/python.exe"; fi
  [ -x "$AIPY" ] || "$PY" -m venv "$VENV"
  REQS="scripts/setup/requirements-ai.txt"; [ "$DEPTH" = 0 ] || REQS="$REQS scripts/setup/requirements-depth.txt"
  STAMP="cache/stamps/venv-$(cat $REQS | sha256sum | cut -c1-12)"
  if [ ! -f "$STAMP" ]; then
    for r in $REQS; do "$AIPY" -m pip install --quiet --disable-pip-version-check -r "$r"; done
    touch "$STAMP"
  fi
  # not GROUPS: bash keeps the user's group ids in GROUPS and silently ignores assignments to it
  AI_GROUPS=ai; [ "$DEPTH" = 0 ] || AI_GROUPS=ai,depth
  "$PY" -I scripts/setup/fetch.py list --root . --list scripts/setup/downloads.json --group "$AI_GROUPS" --jobs 4
  if [ "$DDFA" = 1 ] && [ ! -d assets/ai/3ddfa_v2/repo ]; then
    git clone --quiet https://github.com/cleardusk/3DDFA_V2.git assets/ai/3ddfa_v2/repo
    git -C assets/ai/3ddfa_v2/repo checkout --quiet 1b6c676
    rm -rf assets/ai/3ddfa_v2/repo/.git assets/ai/3ddfa_v2/repo/examples assets/ai/3ddfa_v2/repo/docs
  fi
fi

# image tools (contact sheets, overlays, metrics) need PIL and numpy
PYIMG=""
for c in python3 "$AIPY"; do
  if [ -n "$c" ] && "$c" -I -c 'import PIL, numpy' 2>/dev/null; then PYIMG="$c"; break; fi
done
if [ -z "$PYIMG" ]; then
  [ -x .venv/bin/python ] || [ -x .venv/Scripts/python.exe ] || "$PY" -m venv .venv
  if [ "$OS" = linux ]; then PYIMG=.venv/bin/python; else PYIMG=.venv/Scripts/python.exe; fi
  "$PYIMG" -m pip install --quiet --disable-pip-version-check pillow==12.3.0 numpy
fi

GODOT_BIN=""
if [ "$GODOT" = 1 ]; then
  say "7. Godot 4.7.2 for import checks"
  if [ "$OS" = linux ]; then
    "$PY" -I scripts/setup/fetch.py list --root . --list scripts/setup/downloads.json --group godot
    GODOT_BIN="$PROJECT_DIR/cache/tools/godot/Godot_v4.7.2-stable_linux.x86_64"; chmod +x "$GODOT_BIN"
  else
    GODOT_BIN="$(ls "$(cygpath -u "$LOCALAPPDATA")"/Microsoft/WinGet/Packages/GodotEngine.GodotEngine.Mono*/*/Godot_v4.7.2-stable_mono_win64_console.exe 2>/dev/null | head -1 || true)"
  fi
  [ -n "$GODOT_BIN" ] || echo "WARN: Godot 4.7.2 not found; export import checks will be skipped"
fi

if [ "$PRUNE" = 1 ]; then
  say "prune: research leftovers (research E §9)"
  rm -rf assets/ai/sd_turbo assets/ai/triposr assets/ai/rembg_models/models/bria-rmbg \
         assets/ai/mediapipe/selfie_multiclass_256x256.tflite
fi

say "8. Environment record (cache/env.json, cache/env.sh)"
"$PY" -I scripts/setup/fetch.py env --root . --os "$OS" --blender "$(winpath "$BLENDER")" \
  --user-resources "$BLENDER_USER_RESOURCES" --pyimg "$PYIMG" --aipy "$AIPY" \
  --godot "$([ -z "$GODOT_BIN" ] || winpath "$GODOT_BIN")" --device "$DEVICE"

if [ "$CHECK" = 1 ]; then
  say "9. Smoke test"
  "$BLENDER" -b --python-exit-code 1 --python scripts/setup/smoke.py -- --out cache/stamps/smoke.png
  [ ! -f scripts/tools/bl.py ] || "$PYIMG" -I scripts/tools/bl.py selftest   # start a server, ping, one Workbench crop, stop
  [ -z "$AIPY" ] || "$AIPY" -I -c 'import mediapipe, rembg; print("mediapipe", mediapipe.__version__)'
fi
du -sh assets cache 2>/dev/null || true
echo "setup complete in $(( $(date +%s) - T0 )) s"
