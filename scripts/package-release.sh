#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
OUT_DIR="${1:-$ROOT/dist}"
NAME="codex-sglang-workflow-kit-v${VERSION}.zip"
OUT="$OUT_DIR/$NAME"

python3 "$ROOT/scripts/kit-version.py" verify --root "$ROOT"
python3 "$ROOT/scripts/validate_repo.py"

mkdir -p "$OUT_DIR"
rm -f "$OUT" "$OUT.sha256"

(
  cd "$ROOT"
  zip -qr "$OUT" . \
    -x '.git/*' 'dist/*' '__pycache__/*' '*/__pycache__/*' '*.pyc' '*.pyo' \
       '_render*/*' '_tmp*/*' '*.zip'
)

(cd "$OUT_DIR" && sha256sum "$NAME" > "$NAME.sha256")
printf 'Release archive: %s\n' "$OUT"
printf 'Checksum:        %s\n' "$OUT.sha256"
