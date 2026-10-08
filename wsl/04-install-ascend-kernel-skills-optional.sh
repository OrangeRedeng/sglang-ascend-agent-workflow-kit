#!/usr/bin/env bash
set -euo pipefail
CODE_ROOT="${CODE_ROOT:-$HOME/code}"; SGLANG="${SGLANG:-$CODE_ROOT/sglang}"
AWESOME="$CODE_ROOT/awesome-ascend-skills"; OFFICIAL="$CODE_ROOT/ascend-agent-skills"; CANNBOT="$CODE_ROOT/cannbot-skills"; KERNELHIVE="$CODE_ROOT/kernelhive-ascendc-skill"
link_exact(){
  local src="$1" name="$2"
  local dst="$SGLANG/.agents/skills/$name"
  [[ -f "$src/SKILL.md" ]] || return 1
  mkdir -p "$SGLANG/.agents/skills"
  if [[ -e "$dst" && ! -L "$dst" ]]; then
    echo "keep native skill: $name"
    return 0
  fi
  ln -sfn "$src" "$dst"
  echo "linked: $name"
}
find_link(){
  local root="$1" name="$2" f
  f="$(find "$root" -type f -name SKILL.md -path "*/$name/SKILL.md" -print -quit 2>/dev/null || true)"
  [[ -n "$f" ]] && link_exact "$(dirname "$f")" "$name" || echo "missing: $name"
}
mode="${1:-}"
case "$mode" in
  opplugin) find_link "$AWESOME" ascend-opplugin ;;
  triton)
    find_link "$AWESOME" triton-ascend-migration
    for s in triton-operator-env-config triton-operator-code-review triton-operator-precision-eval triton-operator-performance-eval triton-operator-performance-optim; do find_link "$OFFICIAL" "$s"; done ;;
  ascendc)
    find_link "$AWESOME" ascendc
    for s in ascendc-operator-design ascendc-operator-project-init ascendc-operator-code-gen ascendc-operator-compile-debug ascendc-operator-precision-debug ascendc-operator-precision-eval ascendc-operator-performance-eval ascendc-operator-performance-optim ascendc-operator-code-review; do find_link "$OFFICIAL" "$s"; done ;;
  cannbot)
    for s in npu-arch ascendc-api-best-practices ascendc-docs-search ascendc-env-check ascendc-tiling-design ascendc-precision-debug ascendc-runtime-debug ascendc-crash-debug ascendc-sync-audit ascendc-code-review ascendc-direct-invoke-template ops-profiling ops-precision-standard; do find_link "$CANNBOT" "$s"; done ;;
  kernelhive)
    for s in ascend-kernel-generator ascend-npu-migration ascend-doc-update; do find_link "$KERNELHIVE" "$s"; done
    echo 'KernelHive ascend-kernel-optimization remains excluded: its evaluator/output/LLM assumptions require adaptation.' ;;
  all)
    "$0" opplugin || true; "$0" triton || true; "$0" ascendc || true
    [[ -d "$CANNBOT/.git" ]] && "$0" cannbot || true
    [[ -d "$KERNELHIVE/.git" ]] && "$0" kernelhive || true ;;
  *) echo "Usage: $0 opplugin|triton|ascendc|cannbot|kernelhive|all" >&2; exit 2 ;;
esac
