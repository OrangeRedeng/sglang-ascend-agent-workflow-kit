#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
INSTALL_GLOBAL_CODEX="${INSTALL_GLOBAL_CODEX:-0}"

export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is required. Run setup.sh with Standard/Full or enable uv in Custom mode." >&2
  exit 1
fi

if ! command -v serena >/dev/null 2>&1; then
  uv tool install -p 3.13 serena-agent
fi

if [[ "$INSTALL_GLOBAL_CODEX" == 1 && -f "$CODEX_HOME/config.toml" ]]; then
  if ! grep -q '^\[mcp_servers\.serena\]' "$CODEX_HOME/config.toml"; then
    printf '\n' >> "$CODEX_HOME/config.toml"
    cat "$KIT_ROOT/codex/config/serena.optional.toml" >> "$CODEX_HOME/config.toml"
    echo "Enabled Serena MCP in $CODEX_HOME/config.toml"
  else
    echo "Serena MCP is already configured in $CODEX_HOME/config.toml"
  fi
fi

printf '\nSerena installed.\n'
printf 'The workspace setup will expose Serena to OpenCode when that harness is used.\n'
