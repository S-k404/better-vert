#!/usr/bin/env bash
# Batch-convert everything in ./input to Markdown in ./output, no browser needed.
#
# Usage:
#   ./scripts/convert.sh                  (converts ./input)
#   ./scripts/convert.sh ~/Desktop/docs   (copies that folder into ./input first)

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"
mkdir -p input output

# shellcheck source=lib/platform.sh
. "$SCRIPT_DIR/lib/platform.sh"
compose_available || { echo "Docker Compose is not available. Install Docker first." >&2; exit 1; }

# Git Bash/MSYS2 rewrites anything that looks like a Unix path ("/data/input")
# before handing it to docker.exe; the script below must arrive untouched.
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

if [ $# -gt 0 ]; then
  echo "Copying files from $1 into ./input..."
  cp -R "$1"/. input/
fi

echo "Running batch conversion inside Better VERT container..."
compose exec -T better-vert bash -c '
shopt -s nullglob globstar
for f in /data/input/**/*; do
  [ -f "$f" ] || continue
  base=$(basename "$f"); stem=${base%.*}; ext=${base##*.}
  out="/data/output/$stem.md"
  [ -e "$out" ] && out="/data/output/$stem-$ext.md"
  if markitdown "$f" > "$out" 2>/dev/null; then
    echo "  [OK]   $base -> $(basename "$out")"
  else
    rm -f "$out"; echo "  [FAIL] $base"
  fi
done'

echo "Done! Converted Markdown files are in ./output"
