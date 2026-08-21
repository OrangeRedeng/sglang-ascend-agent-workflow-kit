#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <PR-number|slug>" >&2
  echo "Examples: $0 31320 | $0 scheduler-rank-desync" >&2
  exit 2
fi

ROOT="$(git rev-parse --show-toplevel)"
KEY="$1"
SRC="$ROOT/.codex/templates/handoff.md"
DST_DIR="$ROOT/.codex-artifacts/handoffs"
mkdir -p "$DST_DIR"

slugify() {
  printf '%s' "$1" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9._-' | sed -E 's/-+/-/g; s/^-//; s/-$//'
}

BRANCH="$(git branch --show-current 2>/dev/null || true)"
HEAD="$(git rev-parse HEAD 2>/dev/null || true)"
REPO="$(git remote get-url origin 2>/dev/null || true)"
BASE="$(git merge-base HEAD origin/main 2>/dev/null || true)"
CREATED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
WORKTREE="$ROOT"

if [[ "$KEY" =~ ^[0-9]+$ ]]; then
  PR="$KEY"
  KIND="pr-review"
  SOURCE="PR #${KEY} review"
  DST="$DST_DIR/pr-${KEY}-review.md"
else
  SLUG="$(slugify "$KEY")"
  [[ -n "$SLUG" ]] || { echo "Invalid handoff slug: $KEY" >&2; exit 2; }
  KIND="investigation"
  SOURCE="$SLUG"
  DST="$DST_DIR/${SLUG}.md"
  PR=""
  if [[ "$BRANCH" =~ ([0-9]{3,})$ ]]; then PR="${BASH_REMATCH[1]}"; fi
fi

[[ -f "$SRC" ]] || { echo "Missing template: $SRC" >&2; exit 1; }
[[ ! -e "$DST" ]] || { echo "Already exists: $DST" >&2; exit 1; }

{
  cat <<META
---
schema: codex-sglang-handoff/v1
status: open
kind: $KIND
pr: $PR
branch: $BRANCH
repo: $REPO
worktree: $WORKTREE
base_commit: $BASE
reviewed_head: $HEAD
created_at: $CREATED
consumed_at:
consumed_head:
---

META
  sed "s|Source: <PR / issue / investigation>|Source: ${SOURCE}|" "$SRC"
} > "$DST"

printf '%s\n' "$DST"
