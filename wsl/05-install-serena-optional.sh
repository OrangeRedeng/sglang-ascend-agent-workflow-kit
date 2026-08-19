#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Run 02-bootstrap-wsl.sh first." >&2
  exit 1
fi

if ! command -v serena >/dev/null 2>&1; then
  # Serena currently recommends a recent Python; uv manages it for the tool.
  uv tool install -p 3.13 serena-agent
fi

printf '\nSerena installed.\n'
printf 'Append codex/config/serena.optional.toml to ~/.codex/config.toml, then restart Codex.\n'
printf 'Use Serena for callers/references/symbol structure, not as a replacement for rg.\n'
