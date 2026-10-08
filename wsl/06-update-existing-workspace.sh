#!/usr/bin/env bash
set -euo pipefail
KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/sglang-workflow"
MANIFEST="$CONFIG_DIR/install.env"
WORKSPACE="${SGLANG:-$HOME/code/sglang}"

# Legacy releases may have a large manifest. v0.5 only needs level + workspace;
# setup.sh reads those fields and rewrites a minimal manifest on success.
if [[ ! -f "$MANIFEST" ]]; then
  legacy="$(cat "$HOME/.codex/workflow-kit-version" 2>/dev/null || cat "$CONFIG_DIR/workflow-kit-version" 2>/dev/null || true)"
  if [[ -z "$legacy" && ! -d "$WORKSPACE/.codex" ]]; then
    echo 'No existing workflow installation detected; run setup.sh first.' >&2
    exit 2
  fi
  mkdir -p "$CONFIG_DIR"
  cat > "$MANIFEST" <<EOF
INSTALL_LEVEL=standard
SGLANG_WORKSPACE=$(printf '%q' "$WORKSPACE")
EOF
  chmod 600 "$MANIFEST"
  echo "Created minimal migration manifest from ${legacy:-legacy installation}: $MANIFEST"
fi
exec "$KIT_ROOT/setup.sh" --update
