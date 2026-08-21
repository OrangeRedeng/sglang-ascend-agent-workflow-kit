#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SGLANG="${SGLANG:-$HOME/code/sglang}"
STAMP="$(date +%Y%m%d-%H%M%S)"

log() { printf '\n==> %s\n' "$*"; }
backup_if_exists() {
  local p="$1"
  if [[ -e "$p" || -L "$p" ]]; then
    cp -a "$p" "$p.bak-$STAMP"
    echo "Backup: $p.bak-$STAMP"
  fi
}

git -C "$SGLANG" rev-parse --show-toplevel >/dev/null 2>&1 || { echo "SGLang Git worktree not found: $SGLANG" >&2; exit 1; }

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

log "Update static repo-local workflow layer"
cp "$KIT_ROOT/repo/AGENTS.override.md" "$SGLANG/AGENTS.override.md"
cp "$KIT_ROOT/repo/.sembleignore" "$SGLANG/.sembleignore"
mkdir -p "$SGLANG/.codex" "$SGLANG/.agents/skills" "$SGLANG/.codex-artifacts/handoffs" "$SGLANG/.codex-artifacts/goals" "$SGLANG/.codex-artifacts/logs"
cp -a "$KIT_ROOT/repo/.codex/." "$SGLANG/.codex/"
cp -a "$KIT_ROOT/repo/.agents/skills/." "$SGLANG/.agents/skills/"
chmod +x "$SGLANG/.codex/scripts/"*.sh "$SGLANG/.codex/scripts/"*.py

log "Keep workflow state out of upstream PRs"
EXCLUDE="$(git -C "$SGLANG" rev-parse --git-path info/exclude)"
mkdir -p "$(dirname "$EXCLUDE")"
touch "$EXCLUDE"
for entry in ".agents/" ".codex/" ".codex-artifacts/" "AGENTS.override.md" ".sembleignore"; do
  grep -Fxq "$entry" "$EXCLUDE" || echo "$entry" >> "$EXCLUDE"
done

log "Verify handoff resolver"
cd "$SGLANG"
python3 .codex/scripts/resolve-handoff.py --json --no-gh || true

cat <<EOF2

Update complete.

IMPORTANT:
1. Close/reload the VS Code WSL window so the new hooks.json is re-read.
2. Reopen:
     cd $SGLANG
     code .
3. Start a NEW Codex local session.
4. Open handoffs now live in:
     $SGLANG/.codex-artifacts/handoffs/
5. You no longer need to type a handoff path for normal implementation/address-review prompts.
EOF2
