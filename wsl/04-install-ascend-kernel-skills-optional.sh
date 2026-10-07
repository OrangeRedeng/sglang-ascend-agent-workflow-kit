#!/usr/bin/env bash
set -euo pipefail
CODE_ROOT="${CODE_ROOT:-$HOME/code}"; SGLANG="${SGLANG:-$CODE_ROOT/sglang}"
AWESOME="$CODE_ROOT/awesome-ascend-skills"; OFFICIAL="$CODE_ROOT/ascend-agent-skills"; CANNBOT="$CODE_ROOT/cannbot-skills"; KERNELHIVE="$CODE_ROOT/kernelhive-ascendc-skill"
link(){ [[ -f "$1/SKILL.md" ]] || return 1; mkdir -p "$SGLANG/.agents/skills"; ln -sfn "$1" "$SGLANG/.agents/skills/$2"; echo "linked: $2"; }
find_link(){ local f; f="$(find "$1" -type f -name SKILL.md -path "*/$2/SKILL.md" -print -quit 2>/dev/null || true)"; [[ -n "$f" ]] && link "$(dirname "$f")" "$3$2" || echo "missing: $2"; }
mode="${1:-}"
case "$mode" in
  opplugin) find_link "$AWESOME" ascend-opplugin ascend- ;;
  triton)
    find_link "$AWESOME" triton-ascend-migration ascend-
    for s in triton-operator-env-config triton-operator-code-review triton-operator-precision-eval triton-operator-performance-eval triton-operator-performance-optim; do find_link "$OFFICIAL" "$s" official-; done ;;
  ascendc)
    find_link "$AWESOME" ascendc ascend-
    for s in ascendc-operator-design ascendc-operator-compile-debug ascendc-operator-frame-adapter-torch ascendc-operator-precision-eval; do find_link "$OFFICIAL" "$s" official-; done ;;
  cannbot)
    for s in npu-arch ascendc-api-best-practices ascendc-docs-search ascendc-env-check ascendc-tiling-design ascendc-precision-debug ascendc-runtime-debug ascendc-crash-debug ascendc-sync-audit ascendc-code-review ascendc-direct-invoke-template ops-profiling ops-precision-standard; do find_link "$CANNBOT" "$s" cannbot-; done ;;
  kernelhive)
    for s in ascend-kernel-generator ascend-npu-migration ascend-doc-update; do find_link "$KERNELHIVE" "$s" kernelhive-; done
    echo 'KernelHive ascend-kernel-optimization is intentionally not auto-linked: adapt its evaluator/output/LLM defaults first.' ;;
  all)
    "$0" opplugin || true; "$0" triton || true; "$0" ascendc || true
    [[ -d "$CANNBOT/.git" ]] && "$0" cannbot || true
    [[ -d "$KERNELHIVE/.git" ]] && "$0" kernelhive || true ;;
  *) echo "Usage: $0 opplugin|triton|ascendc|cannbot|kernelhive|all" >&2; exit 2 ;;
esac
