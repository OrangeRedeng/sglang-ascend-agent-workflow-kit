#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <PR-number|slug>" >&2
  echo "Examples:" >&2
  echo "  $0 31320" >&2
  echo "  $0 scheduler-rank-desync" >&2
  exit 2
fi

ROOT="$(git rev-parse --show-toplevel)"
KEY="$1"
SRC="$ROOT/.codex/handoffs/TEMPLATE.md"

if [[ "$KEY" =~ ^[0-9]+$ ]]; then
  DST="$ROOT/.codex/handoffs/pr-${KEY}-review.md"
  SOURCE="PR #${KEY} review"
  PR="#${KEY}"
else
  SLUG="$(printf '%s' "$KEY" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9._-' | sed -E 's/-+/-/g; s/^-//; s/-$//')"
  if [[ -z "$SLUG" ]]; then
    echo "Invalid handoff slug: $KEY" >&2
    exit 2
  fi
  DST="$ROOT/.codex/handoffs/${SLUG}.md"
  SOURCE="$SLUG"
  PR="n/a"
fi

mkdir -p "$(dirname "$DST")"
if [[ -e "$DST" ]]; then
  echo "Already exists: $DST" >&2
  exit 1
fi

cp "$SRC" "$DST"
DATE="$(date +%F)"
HEAD="$(git rev-parse --short HEAD 2>/dev/null || true)"
sed -i \
  -e "s|Source: <PR / issue / investigation>|Source: ${SOURCE}|" \
  -e "s|PR: <#number or n/a>|PR: ${PR}|" \
  -e "s|Reviewed HEAD: <sha>|Reviewed HEAD: ${HEAD:-unknown}|" \
  -e "s|Date: <date>|Date: ${DATE}|" \
  "$DST"

echo "$DST"
