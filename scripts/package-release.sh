#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; VER="$(tr -d '[:space:]' < "$ROOT/VERSION")"; OUT="$ROOT/dist"; NAME="sglang-ascend-agent-workflow-kit-v$VER"
mkdir -p "$OUT"; rm -f "$OUT/$NAME.zip" "$OUT/$NAME.zip.sha256"
(cd "$ROOT" && zip -qr "$OUT/$NAME.zip" . -x '.git/*' 'dist/*' '__pycache__/*' '*.pyc')
(cd "$OUT" && sha256sum "$NAME.zip" > "$NAME.zip.sha256")
echo "$OUT/$NAME.zip"
