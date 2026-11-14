#!/usr/bin/env bash
# Assemble the Hugging Face Space folder in app/.space_build/ (git-ignored). Uploads nothing.
# Run from anywhere:  bash app/build_space.sh
set -euo pipefail

APP="$(cd "$(dirname "$0")" && pwd)"
OUT="$APP/.space_build"

rm -rf "${OUT:?}"
mkdir -p "$OUT/data"
cp "$APP/space/README.md" "$OUT/README.md"              # Space settings (YAML front-matter) + description
cp "$APP/app.py" "$APP/requirements.txt" "$OUT/"
cp "$APP/../data/predictions.csv" "$APP/../data/metrics.json" "$OUT/data/"

echo "Built $OUT:"
(cd "$OUT" && find . -type f | sort)
