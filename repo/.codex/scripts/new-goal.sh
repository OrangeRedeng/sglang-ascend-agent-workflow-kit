#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <goal-slug>" >&2
  exit 2
fi
ROOT="$(git rev-parse --show-toplevel)"
SLUG="$(printf '%s' "$1" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9._-' | sed -E 's/-+/-/g; s/^-//; s/-$//')"
[[ -n "$SLUG" ]] || { echo "Invalid goal slug" >&2; exit 2; }
SRC="$ROOT/.codex/templates/goal"
DST="$ROOT/.codex-artifacts/goals/$SLUG"
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
