#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SGLANG="${SGLANG:-$HOME/code/sglang}"
STAMP="$(date +%Y%m%d-%H%M%S)"
KIT_VERSION="$(tr -d '[:space:]' < "$KIT_ROOT/VERSION")"

log() { printf '\n==> %s\n' "$*"; }
backup_if_exists() {
  local p="$1"
  if [[ -e "$p" || -L "$p" ]]; then
    cp -a "$p" "$p.bak-$STAMP"
    echo "Backup: $p.bak-$STAMP"
  fi
}

git -C "$SGLANG" rev-parse --show-toplevel >/dev/null 2>&1 || { echo "SGLang Git worktree not found: $SGLANG" >&2; exit 1; }

GLOBAL_VERSION="$(cat "$CODEX_HOME/workflow-kit-version" 2>/dev/null | tr -d '[:space:]' || true)"
WORKSPACE_VERSION="$(cat "$SGLANG/.codex/KIT_VERSION" 2>/dev/null | tr -d '[:space:]' || true)"

log "Workflow-kit version preflight"
printf 'Global Codex layer: %s\n' "${GLOBAL_VERSION:-unversioned}"
printf 'Workspace layer:    %s\n' "${WORKSPACE_VERSION:-unversioned}"
printf 'Incoming kit:       %s\n' "$KIT_VERSION"

for installed in "$GLOBAL_VERSION" "$WORKSPACE_VERSION"; do
  [[ -z "$installed" ]] && continue
  cmp="$(python3 "$KIT_ROOT/scripts/kit-version.py" compare "$installed" "$KIT_VERSION")" || exit 2
  if [[ "$cmp" == "1" && "${ALLOW_DOWNGRADE:-0}" != "1" ]]; then
    echo "ERROR: installed workflow-kit version $installed is newer than incoming $KIT_VERSION." >&2
    echo "Use ALLOW_DOWNGRADE=1 only for an intentional downgrade." >&2
    exit 2
  fi
done

log "Back up global Codex hook configuration"
mkdir -p "$CODEX_HOME/hooks"
backup_if_exists "$CODEX_HOME/hooks.json"
cp "$KIT_ROOT/codex/hooks.json" "$CODEX_HOME/hooks.json"
for hook in prompt_guard.py session_start.py; do
  backup_if_exists "$CODEX_HOME/hooks/$hook"
  cp "$KIT_ROOT/codex/hooks/$hook" "$CODEX_HOME/hooks/$hook"
done
chmod +x "$CODEX_HOME/hooks/"*.py

log "Migrate mutable workflow artifacts"
# Install the migration helper temporarily if the current checkout predates it.
mkdir -p "$SGLANG/.codex/scripts"
cp "$KIT_ROOT/repo/.codex/scripts/migrate-artifacts.py" "$SGLANG/.codex/scripts/migrate-artifacts.py"
chmod +x "$SGLANG/.codex/scripts/migrate-artifacts.py"
python3 "$SGLANG/.codex/scripts/migrate-artifacts.py" --root "$SGLANG" --remove-legacy

# v0.1.1 cleanup: old releases could accidentally migrate template markdown into runtime state.
find "$SGLANG/.codex-artifacts/handoffs" -maxdepth 1 -type f \
  -iname 'TEMPLATE*.md' -print -delete 2>/dev/null || true

log "Update static repo-local workflow layer"
cp "$KIT_ROOT/repo/AGENTS.override.md" "$SGLANG/AGENTS.override.md"
cp "$KIT_ROOT/repo/.sembleignore" "$SGLANG/.sembleignore"
mkdir -p "$SGLANG/.codex" "$SGLANG/.agents/skills" "$SGLANG/.codex-artifacts/handoffs" "$SGLANG/.codex-artifacts/goals" "$SGLANG/.codex-artifacts/logs"
cp -a "$KIT_ROOT/repo/.codex/." "$SGLANG/.codex/"
cp -a "$KIT_ROOT/repo/.agents/skills/." "$SGLANG/.agents/skills/"
chmod +x "$SGLANG/.codex/scripts/"*.sh "$SGLANG/.codex/scripts/"*.py

log "Keep workflow state out of upstream PRs"
EXCLUDE="$(git -C "$SGLANG" rev-parse --git-path info/exclude)"
# `git rev-parse --git-path` may return a path relative to the worktree.
# Resolve it against SGLANG rather than the kit's current working directory.
if [[ "$EXCLUDE" != /* ]]; then
  EXCLUDE="$SGLANG/$EXCLUDE"
fi
mkdir -p "$(dirname "$EXCLUDE")"
touch "$EXCLUDE"
for entry in ".agents/" ".codex/" ".codex-artifacts/" "AGENTS.override.md" ".sembleignore"; do
  grep -Fxq "$entry" "$EXCLUDE" || echo "$entry" >> "$EXCLUDE"
done

# Fail fast if runtime state could leak into an upstream PR.
if ! (cd "$SGLANG" && git check-ignore -q .codex-artifacts/); then
  echo "ERROR: .codex-artifacts/ is not ignored by Git after setup." >&2
  echo "Expected exclude file: $EXCLUDE" >&2
  exit 1
fi
echo "Verified: .codex-artifacts/ is Git-ignored."

log "Record installed workflow-kit version"
printf '%s\n' "$KIT_VERSION" > "$CODEX_HOME/workflow-kit-version"
printf '%s\n' "$KIT_VERSION" > "$SGLANG/.codex/KIT_VERSION"
mkdir -p "$SGLANG/.codex-artifacts"
VERSION_HISTORY="$SGLANG/.codex-artifacts/kit-version-history.tsv"
if [[ ! -s "$VERSION_HISTORY" ]]; then
  printf 'timestamp_utc\taction\tprevious_version\tnew_version\n' > "$VERSION_HISTORY"
fi
printf '%s\t%s\t%s\t%s\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  "update" \
  "${WORKSPACE_VERSION:-unversioned}" \
  "$KIT_VERSION" \
  >> "$VERSION_HISTORY"
echo "Recorded global + workspace version: $KIT_VERSION"

log "Verify workflow"
cd "$SGLANG"
python3 .codex/scripts/resolve-handoff.py --json --no-gh || true
python3 .codex/scripts/workflow-doctor.py || true

cat <<EOF2

Update complete: ${WORKSPACE_VERSION:-unversioned} -> $KIT_VERSION

IMPORTANT:
1. Close/reload the VS Code WSL window so the new hooks.json is re-read.
2. Reopen:
     cd $SGLANG
     code .
3. Start a NEW Codex local session.
4. Open handoffs now live in:
     $SGLANG/.codex-artifacts/handoffs/
5. You no longer need to type a handoff path for normal implementation/address-review prompts.
6. Hook trust is intentionally NOT granted by this updater. Because hooks may have changed, verify them once:
     cd $SGLANG
     cx
     /hooks
   Approve/enable BOTH SessionStart and UserPromptSubmit, then exit Codex and reload VS Code.
7. Re-check any time with:
     python3 .codex/scripts/workflow-doctor.py
EOF2
