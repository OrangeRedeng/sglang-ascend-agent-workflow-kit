#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <goal-slug>" >&2
  exit 2
fi
ROOT="$(git rev-parse --show-toplevel)"
SLUG="$1"
SRC="$ROOT/.codex/goals/TEMPLATE"
DST="$ROOT/.codex/goals/$SLUG"
if [[ -e "$DST" ]]; then
  echo "Already exists: $DST" >&2
  exit 1
fi
mkdir -p "$DST"
cp -a "$SRC/." "$DST/"
cp "$SRC/experiments/000-template.md" "$DST/experiments/001.md"
rm -f "$DST/experiments/000-template.md"
mkdir -p "$DST/artifacts"
echo "$DST"
