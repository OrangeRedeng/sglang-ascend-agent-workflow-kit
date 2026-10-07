#!/usr/bin/env bash
set -euo pipefail
command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
command -v serena >/dev/null 2>&1 || uv tool install --from git+https://github.com/oraios/serena serena-agent
command -v serena >/dev/null 2>&1 || { echo 'Serena executable not found after install' >&2; exit 1; }
