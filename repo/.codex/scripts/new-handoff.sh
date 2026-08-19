#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <PR-number>" >&2
  exit 2
fi
ROOT="$(git rev-parse --show-toplevel)"
PR="$1"
DST="$ROOT/.codex/handoffs/pr-${PR}-review.md"
SRC="$ROOT/.codex/handoffs/TEMPLATE-review.md"
mkdir -p "$(dirname "$DST")"
if [[ -e "$DST" ]]; then
  echo "Already exists: $DST" >&2
  exit 1
fi
cp "$SRC" "$DST"
sed -i "s/#<number>/#${PR}/g" "$DST"
echo "$DST"
