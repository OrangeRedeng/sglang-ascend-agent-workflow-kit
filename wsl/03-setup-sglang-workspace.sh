#!/usr/bin/env bash
set -euo pipefail
KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE_ROOT="${CODE_ROOT:-$HOME/code}"
SGLANG="${SGLANG:-$CODE_ROOT/sglang}"
KERNEL="$CODE_ROOT/sgl-kernel-npu"; BBUF="$CODE_ROOT/AI-Infra-Auto-Driven-SKILLS"
AWESOME="$CODE_ROOT/awesome-ascend-skills"; OFFICIAL="$CODE_ROOT/ascend-agent-skills"
CANNBOT="$CODE_ROOT/cannbot-skills"; KERNELHIVE="$CODE_ROOT/kernelhive-ascendc-skill"
enabled(){ [[ "${1:-0}" == 1 ]]; }
clone_repo(){ [[ -d "$2/.git" ]] || git clone "$1" "$2"; }
pin_source(){ WORKFLOW_SKILLS_LOCK="$KIT_ROOT/skills.lock.json" CODE_ROOT="$CODE_ROOT" python3 "$KIT_ROOT/bin/workflow-skills" install --only "$1"; }
link_exact(){
  local src="$1" name="$2"
  local dst="$SGLANG/.agents/skills/$name"
  [[ -f "$src/SKILL.md" ]] || return 0
  mkdir -p "$SGLANG/.agents/skills"
  if [[ -e "$dst" && ! -L "$dst" ]]; then
    echo "keep native skill: $name"
    return 0
  fi
  ln -sfn "$src" "$dst"
  echo "linked: $name"
}
find_link(){
  local root="$1" wanted="$2" f
  f="$(find "$root" -type f -name SKILL.md -path "*/$wanted/SKILL.md" -print -quit 2>/dev/null || true)"
  [[ -n "$f" ]] && link_exact "$(dirname "$f")" "$wanted" || echo "not found: $wanted"
}

mkdir -p "$CODE_ROOT"
clone_repo https://github.com/sgl-project/sglang.git "$SGLANG"
mkdir -p "$SGLANG/.agents/skills"

# Remove only legacy symlink aliases created by pre-v0.5 releases. Native dirs are untouched.
for p in "$SGLANG/.agents/skills"/{upstream-*,official-*,bbuf-*,cannbot-*,kernelhive-*,ascend-torch-npu,ascend-torch_npu,ascend-profiling-analysis,ascend-pytorch-profiling-collection,ascend-npu-op-benchmark}; do
  [[ -L "$p" ]] && rm -f "$p"
done

cp -a "$KIT_ROOT/repo/.agents/skills/." "$SGLANG/.agents/skills/"

# Reuse upstream SGLang skills only under their canonical name. Copilot and Codex
# both require skill directory name == SKILL.md frontmatter name.
for skill in babysit-pr-to-pass-ci ci-workflow-guide debug-cuda-crash debug-distributed-hang large-class-style env-var-conventions speculative-naming scripted-runtime-notes write-sglang-test; do
  link_exact "$SGLANG/.claude/skills/$skill" "$skill"
done

if enabled "${INSTALL_ASCEND_SKILLS:-1}"; then
  pin_source awesome-ascend-skills
  pin_source ascend-agent-skills
  for s in torch_npu profiling-analysis pytorch-profiling-collection npu-op-benchmark; do find_link "$AWESOME" "$s"; done
  for s in npu-adapter-reviewer ascend-profiling-anomaly hccl-test; do find_link "$OFFICIAL" "$s"; done
fi
if enabled "${INSTALL_CANNBOT_SKILLS:-0}"; then pin_source cannbot-skills; fi
if enabled "${INSTALL_KERNELHIVE_SKILLS:-0}"; then pin_source kernelhive-ascendc; fi
if enabled "${INSTALL_BBUF_SKILLS:-0}"; then
  pin_source bbuf
  for s in sglang-humanize-review model-pr-optimization-history llm-torch-profiler-analysis llm-pipeline-analysis sglang-prod-incident-triage; do find_link "$BBUF" "$s"; done
fi
enabled "${INSTALL_KERNEL_REPO:-0}" && clone_repo https://github.com/sgl-project/sgl-kernel-npu.git "$KERNEL"
if enabled "${INSTALL_KERNEL_SKILLS:-0}"; then "$KIT_ROOT/wsl/04-install-ascend-kernel-skills-optional.sh" all || true; fi

if enabled "${INSTALL_REPO_WORKFLOW:-1}"; then
  mkdir -p "$SGLANG/.codex/scripts" "$SGLANG/.codex-artifacts/handoffs" "$SGLANG/.codex-artifacts/goals" "$SGLANG/.codex-artifacts/logs" "$SGLANG/.codex-artifacts/reviews" "$SGLANG/.codex-artifacts/session-budget"
  cp "$KIT_ROOT/repo/AGENTS.md" "$SGLANG/AGENTS.md"
  cp -a "$KIT_ROOT/repo/.codex/." "$SGLANG/.codex/"
  chmod +x "$SGLANG/.codex/scripts/"*.sh "$SGLANG/.codex/scripts/"*.py
fi

# Remove v0.4 Kilo/OpenCode/search workspace artifacts created by the kit.
rm -rf "$SGLANG/.kilo"
rm -f "$SGLANG/kilo.jsonc" "$SGLANG/AGENTS.override.md" "$SGLANG/.sembleignore" "$SGLANG/opencode.json"

# Keep local workflow customization out of upstream SGLang changes.
EXCLUDE="$(git -C "$SGLANG" rev-parse --git-path info/exclude)"; [[ "$EXCLUDE" == /* ]] || EXCLUDE="$SGLANG/$EXCLUDE"
mkdir -p "$(dirname "$EXCLUDE")"; touch "$EXCLUDE"
python3 - "$EXCLUDE" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
lines=p.read_text().splitlines() if p.exists() else []
remove={'.kilo/','kilo.jsonc','AGENTS.override.md','.sembleignore','opencode.json'}
lines=[x for x in lines if x.strip() not in remove]
for item in ['.agents/','.codex/','.codex-artifacts/','AGENTS.md','.vscode/settings.json']:
    if item not in lines:
        lines.append(item)
p.write_text('\n'.join(lines).rstrip()+'\n')
PY

WORKFLOW_SKILLS_LOCK="$KIT_ROOT/skills.lock.json" SGLANG="$SGLANG" CODE_ROOT="$CODE_ROOT" python3 "$KIT_ROOT/bin/workflow-skills" dedupe --workspace "$SGLANG"
WORKFLOW_SKILLS_LOCK="$KIT_ROOT/skills.lock.json" SGLANG="$SGLANG" CODE_ROOT="$CODE_ROOT" python3 "$KIT_ROOT/bin/workflow-skills" snapshot || true
WORKFLOW_SKILLS_LOCK="$KIT_ROOT/skills.lock.json" SGLANG="$SGLANG" CODE_ROOT="$CODE_ROOT" python3 "$KIT_ROOT/bin/workflow-skills" index || true
echo "Workspace setup complete: $SGLANG"
