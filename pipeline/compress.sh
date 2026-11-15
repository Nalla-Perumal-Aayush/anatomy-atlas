#!/usr/bin/env bash
# Compress every <bundle>.raw.glb in a folder.
#   meshopt (default): smallest files, needs WebAssembly in the browser. Use for the real site.
#   draco: decoded in plain JavaScript in a worker. Use for hosts that block WebAssembly.
# Usage: pipeline/compress.sh <build folder> <out folder> [meshopt|draco]
set -euo pipefail
IN="$1"; OUT="$2"; MODE="${3:-meshopt}"
TOOLS="$(cd "$(dirname "$0")/../tools" && pwd)"
mkdir -p "$OUT"
for f in "$IN"/*.raw.glb; do
  b="$(basename "$f" .raw.glb)"
  ( cd "$TOOLS" && npx gltf-transform optimize "$f" "$OUT/$b.glb" \
      --compress "$MODE" --join false --flatten false --instance false --palette false \
      --texture-compress false --simplify true --simplify-error 0.0005 ) | tail -1
done
cp "$IN"/*.content.json "$IN/metadata.json" "$IN/manifest.json" "$OUT/"
