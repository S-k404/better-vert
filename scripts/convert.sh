#!/usr/bin/env bash
# Batch-convert everything in ./input to Markdown in ./output, no browser needed.
# Incorporates File Converter batch functionality for Apple M5 Max.
#
# Usage:
#   ./scripts/convert.sh                  (converts ./input)
#   ./scripts/convert.sh ~/Desktop/docs   (copies that folder into ./input first)

set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"
mkdir -p input output

if [ $# -gt 0 ]; then
  echo "Copying files from $1 into ./input..."
  cp -R "$1"/. input/
fi

echo "Running batch conversion inside Better VERT container..."
docker compose exec -T better-vert bash -c '
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
