#!/usr/bin/env bash
set -euo pipefail
KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/sglang-workflow"
MANIFEST="$CONFIG_DIR/install.env"
WORKSPACE="${SGLANG:-$HOME/code/sglang}"

# v0.1.x did not have install.env. Build a conservative migration manifest from
# observable installed state instead of forcing the user through a fresh bootstrap.
if [[ ! -f "$MANIFEST" ]]; then
  legacy="$(cat "$HOME/.codex/workflow-kit-version" 2>/dev/null || cat "$CONFIG_DIR/workflow-kit-version" 2>/dev/null || true)"
  if [[ -z "$legacy" && ! -d "$WORKSPACE/.codex" ]]; then
    echo 'No saved installation manifest or recognizable legacy workflow installation; run setup.sh first.' >&2
    exit 2
  fi
  mkdir -p "$CONFIG_DIR"
  semble=0; command -v semble >/dev/null 2>&1 && semble=1
  [[ -f "$HOME/.codex/config.toml" ]] && grep -q '^\[mcp_servers\.semble\]' "$HOME/.codex/config.toml" && semble=1
  bbuf=0; [[ -d "$HOME/code/AI-Infra-Auto-Driven-SKILLS/.git" ]] && bbuf=1
  kernel=0; [[ -d "$HOME/code/sgl-kernel-npu/.git" ]] && kernel=1
  cannbot=0; [[ -d "$HOME/code/cannbot-skills/.git" ]] && cannbot=1
  kernelhive=0; [[ -d "$HOME/code/kernelhive-ascendc-skill/.git" ]] && kernelhive=1
  serena=0; command -v serena >/dev/null 2>&1 && serena=1
  cat > "$MANIFEST" <<EOF
INSTALL_LEVEL=standard
SGLANG_WORKSPACE=$(printf '%q' "$WORKSPACE")
AI_PRIMARY_BACKEND=codex
AI_ROUTING_MODE=primary
INSTALL_BASE_PACKAGES=1
INSTALL_GH=1
INSTALL_UV=$([[ $semble == 1 || $serena == 1 ]] && echo 1 || echo 0)
INSTALL_CODEX=1
INSTALL_OPENCODE=0
INSTALL_SEMBLE=$semble
INSTALL_ROUTERS=1
INSTALL_GLOBAL_CODEX=1
INSTALL_REPO_WORKFLOW=1
INSTALL_ASCEND_SKILLS=1
INSTALL_BBUF_SKILLS=$bbuf
INSTALL_KERNEL_REPO=$kernel
INSTALL_KERNEL_SKILLS=$([[ $cannbot == 1 || $kernelhive == 1 ]] && echo 1 || echo 0)
INSTALL_CANNBOT_SKILLS=$cannbot
INSTALL_KERNELHIVE_SKILLS=$kernelhive
INSTALL_SERENA=$serena
INSTALL_VSCODE_CODEX=1
INSTALL_GLM=0
EOF
  chmod 600 "$MANIFEST"
  echo "Created migration manifest from legacy installation ${legacy:-unknown}: $MANIFEST"
fi
args=(--update)
[[ -n "${SGLANG:-}" ]] && args+=(--workspace "$SGLANG")
exec "$KIT_ROOT/setup.sh" "${args[@]}"
