#!/usr/bin/env bash
set -euo pipefail
KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/sglang-workflow"
MANIFEST="$CONFIG_DIR/install.env"
LEVEL=""
WORKSPACE="${SGLANG:-$HOME/code/sglang}"
UPDATE_MODE=0
NON_INTERACTIVE=0
SKIP_POST_SETUP=0
NO_OPEN_VSCODE=0

usage(){ cat <<'TXT'
Usage: ./setup.sh [options]
  --level light|standard|full
  --workspace PATH
  --update
  --non-interactive
  --no-post-setup
  --no-open-vscode

v0.6.0 is intentionally narrow:
  - GitHub Copilot Chat is the primary UI
  - Codex Bridge uses ChatGPT/Codex subscription inside Copilot Chat
  - GLM Models uses BigModel China Coding Plan inside the same model picker
  - official OpenAI Codex extension/CLI remains a fallback
  - one shared AGENTS.md + .agents/skills + handoff/Goal workflow
  - no Kilo, OpenCode, Semble, Serena, or Codex-native GLM routing
TXT
}
while [[ $# -gt 0 ]]; do
  case "$1" in
    --level) LEVEL="${2:?}"; shift 2;;
    --level=*) LEVEL="${1#*=}"; shift;;
    --workspace) WORKSPACE="${2:?}"; shift 2;;
    --workspace=*) WORKSPACE="${1#*=}"; shift;;
    --update) UPDATE_MODE=1; shift;;
    --non-interactive) NON_INTERACTIVE=1; shift;;
    --no-post-setup) SKIP_POST_SETUP=1; shift;;
    --no-open-vscode) NO_OPEN_VSCODE=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1" >&2; usage; exit 2;;
  esac
done

if [[ $UPDATE_MODE == 1 && -f "$MANIFEST" ]]; then
  # Read only the two fields v0.5 still owns. Ignore legacy harness/provider fields.
  old_level="$(grep -E '^INSTALL_LEVEL=' "$MANIFEST" | tail -1 | cut -d= -f2- || true)"
  old_workspace="$(grep -E '^SGLANG_WORKSPACE=' "$MANIFEST" | tail -1 | cut -d= -f2- || true)"
  [[ -z "$LEVEL" && -n "$old_level" ]] && LEVEL="$old_level"
  if [[ -z "${SGLANG:-}" && -n "$old_workspace" ]]; then
    # shellcheck disable=SC2086
    eval "WORKSPACE=$old_workspace"
  fi
fi
[[ -z "$LEVEL" ]] && LEVEL=standard
case "$LEVEL" in light|standard|full) ;; *) echo "Invalid level: $LEVEL" >&2; exit 2;; esac

INSTALL_BASE_PACKAGES=0
INSTALL_GH=0
INSTALL_CODEX=0
INSTALL_VSCODE_CODEX=0
INSTALL_VSCODE_COPILOT=0
INSTALL_CODEX_BRIDGE=0
INSTALL_GLM_COPILOT=0
INSTALL_REPO_WORKFLOW=1
INSTALL_ASCEND_SKILLS=1
INSTALL_CANNBOT_SKILLS=0
INSTALL_KERNELHIVE_SKILLS=0
INSTALL_BBUF_SKILLS=0
INSTALL_KERNEL_REPO=0
INSTALL_KERNEL_SKILLS=0

case "$LEVEL" in
  light)
    ;;
  standard)
    INSTALL_BASE_PACKAGES=1
    INSTALL_GH=1
    INSTALL_CODEX=1
    INSTALL_VSCODE_CODEX=1
    INSTALL_VSCODE_COPILOT=1
    INSTALL_CODEX_BRIDGE=1
    INSTALL_GLM_COPILOT=1
    INSTALL_CANNBOT_SKILLS=1
    INSTALL_KERNEL_SKILLS=1
    ;;
  full)
    INSTALL_BASE_PACKAGES=1
    INSTALL_GH=1
    INSTALL_CODEX=1
    INSTALL_VSCODE_CODEX=1
    INSTALL_VSCODE_COPILOT=1
    INSTALL_CODEX_BRIDGE=1
    INSTALL_GLM_COPILOT=1
    INSTALL_CANNBOT_SKILLS=1
    INSTALL_KERNELHIVE_SKILLS=1
    INSTALL_BBUF_SKILLS=1
    INSTALL_KERNEL_REPO=1
    INSTALL_KERNEL_SKILLS=1
    ;;
esac

cat <<PLAN
Installation plan
-----------------
Level:                 $LEVEL
Workspace:             $WORKSPACE
Primary UI:             GitHub Copilot Chat
Codex Bridge:           $INSTALL_CODEX_BRIDGE
GLM Copilot provider:   $INSTALL_GLM_COPILOT
Official Codex fallback:$INSTALL_VSCODE_CODEX
Core Ascend skills:    $INSTALL_ASCEND_SKILLS
CANNBot skills:        $INSTALL_CANNBOT_SKILLS
KernelHive skills:     $INSTALL_KERNELHIVE_SKILLS
BBuf skills:           $INSTALL_BBUF_SKILLS
Kilo/OpenCode/Search:  removed
PLAN

mkdir -p "$CONFIG_DIR"
export INSTALL_BASE_PACKAGES INSTALL_GH INSTALL_CODEX INSTALL_VSCODE_CODEX INSTALL_VSCODE_COPILOT INSTALL_CODEX_BRIDGE INSTALL_GLM_COPILOT
export INSTALL_REPO_WORKFLOW INSTALL_ASCEND_SKILLS INSTALL_CANNBOT_SKILLS INSTALL_KERNELHIVE_SKILLS INSTALL_BBUF_SKILLS INSTALL_KERNEL_REPO INSTALL_KERNEL_SKILLS
export INSTALL_LEVEL="$LEVEL" SGLANG="$WORKSPACE"

"$KIT_ROOT/wsl/02-bootstrap-wsl.sh"
"$KIT_ROOT/wsl/03-setup-sglang-workspace.sh"

VER="$(tr -d '[:space:]' < "$KIT_ROOT/VERSION")"
GLOBAL_MARKER="$CONFIG_DIR/workflow-kit-version"
CODEX_MARKER="${CODEX_HOME:-$HOME/.codex}/workflow-kit-version"
AGENTS_MARKER="$WORKSPACE/.agents/.workflow-kit-version"
WORKSPACE_MARKER="$WORKSPACE/.codex/KIT_VERSION"
mkdir -p "${CODEX_HOME:-$HOME/.codex}" "$WORKSPACE/.agents" "$WORKSPACE/.codex"

marker_snapshot="$(mktemp)"
python3 - "$marker_snapshot" "$GLOBAL_MARKER" "$CODEX_MARKER" "$AGENTS_MARKER" "$WORKSPACE_MARKER" <<'PYMARK'
from pathlib import Path
import json,sys
out={}
for raw in sys.argv[2:]:
    p=Path(raw)
    out[raw]=p.read_text() if p.is_file() else None
Path(sys.argv[1]).write_text(json.dumps(out))
PYMARK
restore_markers(){
  python3 - "$marker_snapshot" <<'PYMARK'
from pathlib import Path
import json,sys
state=json.loads(Path(sys.argv[1]).read_text())
for raw,value in state.items():
    p=Path(raw)
    if value is None:
        p.unlink(missing_ok=True)
    else:
        p.parent.mkdir(parents=True,exist_ok=True); p.write_text(value)
PYMARK
}

printf '%s\n' "$VER" > "$GLOBAL_MARKER"
printf '%s\n' "$VER" > "$CODEX_MARKER"
printf '%s\n' "$VER" > "$AGENTS_MARKER"
printf '%s\n' "$VER" > "$WORKSPACE_MARKER"

echo "Setup complete: $WORKSPACE"
if [[ $SKIP_POST_SETUP == 0 && "${WORKFLOW_SKIP_POST_SETUP:-0}" != 1 ]]; then
  args=(setup --workspace "$WORKSPACE")
  [[ $NO_OPEN_VSCODE == 1 || "${WORKFLOW_NO_OPEN_VSCODE:-0}" == 1 ]] && args+=(--no-open-vscode)
  if ! "$KIT_ROOT/bin/workflow-setup" "${args[@]}"; then
    restore_markers
    rm -f "$marker_snapshot"
    echo "Post-setup validation failed; version markers were restored." >&2
    exit 1
  fi
else
  echo "Post-setup skipped. Run: workflow-setup setup --workspace '$WORKSPACE'"
fi
rm -f "$marker_snapshot"

# Persist the minimal manifest only after all requested setup/doctor stages succeed.
cat > "$MANIFEST.tmp" <<EOF
INSTALL_LEVEL=$LEVEL
SGLANG_WORKSPACE=$(printf '%q' "$WORKSPACE")
EOF
chmod 600 "$MANIFEST.tmp"
mv "$MANIFEST.tmp" "$MANIFEST"
