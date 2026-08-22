#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SGLANG="${SGLANG:-$HOME/code/sglang}"

cat <<EOF
Updating the workflow kit using the saved installation manifest.
Workspace: $SGLANG
EOF

exec "$KIT_ROOT/setup.sh" --update --workspace "$SGLANG"
