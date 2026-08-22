#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <PR-number|slug> [topic]" >&2
  echo "Examples:" >&2
  echo "  $0 31320" >&2
  echo "  $0 34855 fsdp-review" >&2
  echo "  $0 scheduler-rank-desync" >&2
  exit 2
fi

ROOT="$(git rev-parse --show-toplevel)"
KEY="$1"
TOPIC_ARG="${2:-}"
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
  TOPIC="$(slugify "${TOPIC_ARG:-review}")"
  [[ -n "$TOPIC" ]] || TOPIC="review"
  SOURCE="PR #${KEY} ${TOPIC}"
  DST="$DST_DIR/pr-${KEY}-${TOPIC}.md"
else
  SLUG="$(slugify "$KEY")"
  [[ -n "$SLUG" ]] || { echo "Invalid handoff slug: $KEY" >&2; exit 2; }
  KIND="investigation"
  TOPIC="$(slugify "${TOPIC_ARG:-$SLUG}")"
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
schema: codex-sglang-handoff/v2
status: open
kind: $KIND
pr: $PR
branch: $BRANCH
repo: $REPO
worktree: $WORKTREE
topic: $TOPIC
scope:
objective:
base_commit: $BASE
reviewed_head: $HEAD
producer: ${WORKFLOW_PRODUCER:-codex}
consumer: ${WORKFLOW_CONSUMER:-codex}
created_at: $CREATED
consumed_at:
consumed_head:
---

META
  sed "s|Source: <PR / issue / investigation>|Source: ${SOURCE}|" "$SRC"
} > "$DST"

# Record the handoff produced by the most recent review/investigation as the active
# continuation target. This avoids guessing among older OPEN handoffs for the same PR.
if [[ -n "$PR" ]]; then
  POINTER="$DST_DIR/.active-pr-${PR}.json"
else
  POINTER="$DST_DIR/.active-worktree.json"
fi
python3 - "$POINTER" "$DST" "$PR" "$TOPIC" "$BRANCH" "$HEAD" "$CREATED" <<'PY_POINTER'
import json
from pathlib import Path
import sys

pointer, handoff, pr, topic, branch, head, created = sys.argv[1:]
Path(pointer).write_text(json.dumps({
    "schema": "codex-sglang-active-handoff/v1",
    "path": str(Path(handoff).resolve()),
    "pr": pr,
    "topic": topic,
    "branch": branch,
    "reviewed_head": head,
    "created_at": created,
}, indent=2) + "\n", encoding="utf-8")
PY_POINTER

printf '%s\n' "$DST"
