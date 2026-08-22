#!/usr/bin/env bash
set -euo pipefail

CODE_ROOT="${CODE_ROOT:-$HOME/code}"
SGLANG="${SGLANG:-$CODE_ROOT/sglang}"
ASCEND_AWESOME="${ASCEND_AWESOME:-$CODE_ROOT/awesome-ascend-skills}"
ASCEND_OFFICIAL="${ASCEND_OFFICIAL:-$CODE_ROOT/ascend-agent-skills}"

usage() {
  cat <<'EOF'
Usage:
  04-install-ascend-kernel-skills-optional.sh opplugin
  04-install-ascend-kernel-skills-optional.sh triton
  04-install-ascend-kernel-skills-optional.sh ascendc
  04-install-ascend-kernel-skills-optional.sh all

Install these only when your work actually touches that layer.
EOF
}
link_skill() {
  local src="$1" name="$2"
  if [[ -d "$src" && -f "$src/SKILL.md" ]]; then
    mkdir -p "$SGLANG/.agents/skills"
    ln -sfn "$src" "$SGLANG/.agents/skills/$name"
    echo "linked: $name"
  else
    echo "missing: $src" >&2
    return 1
  fi
}

[[ -d "$SGLANG/.git" ]] || { echo "Run 03-setup-sglang-workspace.sh first." >&2; exit 1; }
mode="${1:-}"
case "$mode" in
  opplugin)
    link_skill "$ASCEND_AWESOME/skills/ops/ascend-opplugin" "ascend-opplugin"
    ;;
  triton)
    link_skill "$ASCEND_AWESOME/skills/ops/triton-ascend-migration" "ascend-triton-migration"
    for s in triton-operator-env-config triton-operator-code-review triton-operator-precision-eval triton-operator-performance-eval triton-operator-performance-optim; do
      link_skill "$ASCEND_OFFICIAL/skills/$s" "official-$s"
    done
    ;;
  ascendc)
    # High-level workflow + selected official leaf skills.
    link_skill "$ASCEND_AWESOME/skills/ops/ascendc" "ascendc"
    for s in ascendc-operator-design ascendc-operator-compile-debug ascendc-operator-frame-adapter-torch ascendc-operator-precision-eval; do
      link_skill "$ASCEND_OFFICIAL/skills/$s" "official-$s"
    done
    ;;
  all)
    "$0" opplugin
    "$0" triton
    "$0" ascendc
    ;;
  -h|--help|help|'') usage ;;
  *) echo "Unknown mode: $mode" >&2; usage; exit 2 ;;
esac
