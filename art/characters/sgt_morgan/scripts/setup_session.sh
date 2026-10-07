#!/usr/bin/env bash
# Rebuilds the toolchain in a fresh cloud container.
# Idempotent: safe to re-run. Takes ~2 min for Blender; asset downloads are added
# by later steps of the project (see assets/manifest.json).
set -euo pipefail

BLENDER_VER="4.5.14"
BLENDER_DIR="/opt/blender/blender-${BLENDER_VER}-linux-x64"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== Blender ${BLENDER_VER}"
if [ ! -x "${BLENDER_DIR}/blender" ]; then
  mkdir -p /opt/blender
  cd /opt/blender
  curl -sS -L --retry 4 --retry-delay 3 \
    -o "blender-${BLENDER_VER}-linux-x64.tar.xz" \
    "https://download.blender.org/release/Blender${BLENDER_VER%.*}/blender-${BLENDER_VER}-linux-x64.tar.xz"
  tar -xJf "blender-${BLENDER_VER}-linux-x64.tar.xz"
  rm -f "blender-${BLENDER_VER}-linux-x64.tar.xz"
fi
ln -sf "${BLENDER_DIR}/blender" /usr/local/bin/blender
blender --version | head -1

echo "== Python deps (system python3 for image tooling)"
python3 -m pip install --quiet --disable-pip-version-check pillow numpy >/dev/null 2>&1 || true

# TODO(research): MPFB2 extension install + MakeHuman asset packs (see notes/research_generators.md)
# PBR textures, HDRIs and CC0 models: restore from the manifest (about 700 MB; see notes/research_assets.md).
# Idempotent: downloads only files that are missing or have the wrong size, then extracts zips.
if [ -f "${PROJECT_DIR}/assets/manifest.json" ]; then
  python3 -I "${PROJECT_DIR}/scripts/research/build_manifest.py" "${PROJECT_DIR}/assets" --restore || echo "WARN: some assets failed to restore"
fi
# TODO(research): AI helper venv (face landmarks / reconstruction) (see notes/research_ai_helpers.md)

mkdir -p "${PROJECT_DIR}"/{assets,renders}
echo "== setup complete"
