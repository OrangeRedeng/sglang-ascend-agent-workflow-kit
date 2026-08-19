#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE_ROOT="${CODE_ROOT:-$HOME/code}"
SGLANG="$CODE_ROOT/sglang"
KERNEL="$CODE_ROOT/sgl-kernel-npu"
BBUF="$CODE_ROOT/AI-Infra-Auto-Driven-SKILLS"
ASCEND_AWESOME="$CODE_ROOT/awesome-ascend-skills"
ASCEND_OFFICIAL="$CODE_ROOT/ascend-agent-skills"

log() { printf '\n==> %s\n' "$*"; }
clone_if_missing() {
  local url="$1" dest="$2"
  if [[ ! -d "$dest/.git" ]]; then
    git clone "$url" "$dest"
  else
    echo "Exists: $dest"
  fi
}
link_skill() {
  local src="$1" name="$2"
  if [[ -d "$src" && -f "$src/SKILL.md" ]]; then
    ln -sfn "$src" "$SGLANG/.agents/skills/$name"
    echo "linked: $name -> $src"
  else
    echo "missing (skipped): $src"
  fi
}

mkdir -p "$CODE_ROOT"

log "Repositories"
clone_if_missing https://github.com/sgl-project/sglang.git "$SGLANG"
clone_if_missing https://github.com/sgl-project/sgl-kernel-npu.git "$KERNEL"
clone_if_missing https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS.git "$BBUF"
clone_if_missing https://github.com/ascend-ai-coding/awesome-ascend-skills.git "$ASCEND_AWESOME"
clone_if_missing https://github.com/Ascend/agent-skills.git "$ASCEND_OFFICIAL"

log "Repo-local Codex layer"
mkdir -p "$SGLANG/.agents/skills" "$SGLANG/.codex"
cp "$KIT_ROOT/repo/AGENTS.override.md" "$SGLANG/AGENTS.override.md"
cp "$KIT_ROOT/repo/.sembleignore" "$SGLANG/.sembleignore"
cp -a "$KIT_ROOT/repo/.codex/." "$SGLANG/.codex/"
cp -a "$KIT_ROOT/repo/.agents/skills/." "$SGLANG/.agents/skills/"
chmod +x "$SGLANG/.codex/scripts/"*.sh "$SGLANG/.codex/scripts/"*.py

log "Keep local workflow files out of upstream PRs"
touch "$SGLANG/.git/info/exclude"
for entry in ".agents/" ".codex/" "AGENTS.override.md" ".sembleignore"; do
  grep -Fxq "$entry" "$SGLANG/.git/info/exclude" || echo "$entry" >> "$SGLANG/.git/info/exclude"
done

log "Selected upstream SGLang skills"
for skill in \
  babysit-pr-to-pass-ci \
  ci-workflow-guide \
  debug-cuda-crash \
  debug-distributed-hang \
  large-class-style \
  env-var-conventions \
  speculative-naming \
  scripted-runtime-notes \
  write-sglang-test
do
  link_skill "$SGLANG/.claude/skills/$skill" "upstream-$skill"
done

log "Selected BBuf skills"
for wanted in \
  sglang-humanize-review \
  model-pr-optimization-history \
  llm-torch-profiler-analysis \
  llm-pipeline-analysis \
  sglang-prod-incident-triage
do
  found="$(find "$BBUF" -type f -name SKILL.md -path "*/$wanted/SKILL.md" -print -quit 2>/dev/null || true)"
  if [[ -n "$found" ]]; then
    link_skill "$(dirname "$found")" "bbuf-$wanted"
  else
    echo "not found (skipped): $wanted"
  fi
done

log "Core Ascend/torch_npu leaf skills"
# Community aggregator: concrete torch_npu / profiling / op workflows.
link_skill "$ASCEND_AWESOME/skills/base/torch_npu" "ascend-torch-npu"
link_skill "$ASCEND_AWESOME/skills/profiling/profiling-analysis" "ascend-profiling-analysis"
link_skill "$ASCEND_AWESOME/skills/profiling/pytorch-profiling-collection" "ascend-pytorch-profiling-collection"
link_skill "$ASCEND_AWESOME/skills/ops/npu-op-benchmark" "ascend-npu-op-benchmark"

# Official Ascend skills: migration review, anomaly analysis, communication validation.
link_skill "$ASCEND_OFFICIAL/skills/npu-adapter-reviewer" "official-npu-adapter-reviewer"
link_skill "$ASCEND_OFFICIAL/skills/ascend-profiling-anomaly" "official-ascend-profiling-anomaly"
link_skill "$ASCEND_OFFICIAL/skills/hccl-test" "official-hccl-test"

log "Verification"
cd "$SGLANG"
printf 'Repo: %s\n' "$(git remote get-url origin)"
printf 'Branch: %s\n' "$(git branch --show-current)"
printf '\nSkills:\n'
find -L .agents/skills -maxdepth 2 -name SKILL.md -print | sort

printf '\nReady. Open with:\n  cd %q\n  code .\n\nStart default Codex:\n  cx\n' "$SGLANG"
printf '\nOptional kernel-specific skills:\n  %s/wsl/04-install-ascend-kernel-skills-optional.sh --help\n' "$KIT_ROOT"
