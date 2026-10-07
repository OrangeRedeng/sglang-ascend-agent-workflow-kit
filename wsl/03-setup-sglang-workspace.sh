#!/usr/bin/env bash
set -euo pipefail
KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE_ROOT="${CODE_ROOT:-$HOME/code}"
SGLANG="${SGLANG:-$CODE_ROOT/sglang}"
KERNEL="$CODE_ROOT/sgl-kernel-npu"; BBUF="$CODE_ROOT/AI-Infra-Auto-Driven-SKILLS"
AWESOME="$CODE_ROOT/awesome-ascend-skills"; OFFICIAL="$CODE_ROOT/ascend-agent-skills"
CANNBOT="$CODE_ROOT/cannbot-skills"; KERNELHIVE="$CODE_ROOT/kernelhive-ascendc-skill"
VER="$(tr -d '[:space:]' < "$KIT_ROOT/VERSION")"
enabled(){ [[ "${1:-0}" == 1 ]]; }
clone_repo(){ [[ -d "$2/.git" ]] || git clone "$1" "$2"; }
link(){ local s="$1" n="$2"; [[ -f "$s/SKILL.md" ]] || return 0; mkdir -p "$SGLANG/.agents/skills"; ln -sfn "$s" "$SGLANG/.agents/skills/$n"; echo "linked: $n"; }
find_link(){ local root="$1" wanted="$2" prefix="$3" f; f="$(find "$root" -type f -name SKILL.md -path "*/$wanted/SKILL.md" -print -quit 2>/dev/null || true)"; [[ -n "$f" ]] && link "$(dirname "$f")" "$prefix$wanted" || echo "not found: $wanted"; }
pin_source(){ WORKFLOW_SKILLS_LOCK="$KIT_ROOT/skills.lock.json" CODE_ROOT="$CODE_ROOT" python3 "$KIT_ROOT/bin/workflow-skills" install --only "$1"; }

mkdir -p "$CODE_ROOT"
clone_repo https://github.com/sgl-project/sglang.git "$SGLANG"
mkdir -p "$SGLANG/.agents/skills"
cp -a "$KIT_ROOT/repo/.agents/skills/." "$SGLANG/.agents/skills/"
for skill in babysit-pr-to-pass-ci ci-workflow-guide debug-cuda-crash debug-distributed-hang large-class-style env-var-conventions speculative-naming scripted-runtime-notes write-sglang-test; do
  link "$SGLANG/.claude/skills/$skill" "upstream-$skill"
done

if enabled "${INSTALL_ASCEND_SKILLS:-1}"; then
  pin_source awesome-ascend-skills
  pin_source ascend-agent-skills
  find_link "$AWESOME" torch_npu ascend-
  find_link "$AWESOME" profiling-analysis ascend-
  find_link "$AWESOME" pytorch-profiling-collection ascend-
  find_link "$AWESOME" npu-op-benchmark ascend-
  for s in npu-adapter-reviewer ascend-profiling-anomaly hccl-test; do find_link "$OFFICIAL" "$s" official-; done
fi
if enabled "${INSTALL_BBUF_SKILLS:-0}"; then
  pin_source bbuf
  for s in sglang-humanize-review model-pr-optimization-history llm-torch-profiler-analysis llm-pipeline-analysis sglang-prod-incident-triage; do find_link "$BBUF" "$s" bbuf-; done
fi
enabled "${INSTALL_KERNEL_REPO:-0}" && clone_repo https://github.com/sgl-project/sgl-kernel-npu.git "$KERNEL"
enabled "${INSTALL_CANNBOT_SKILLS:-0}" && pin_source cannbot-skills
enabled "${INSTALL_KERNELHIVE_SKILLS:-0}" && pin_source kernelhive-ascendc
if enabled "${INSTALL_KERNEL_SKILLS:-0}"; then "$KIT_ROOT/wsl/04-install-ascend-kernel-skills-optional.sh" all || true; fi

if enabled "${INSTALL_REPO_WORKFLOW:-1}"; then
  mkdir -p "$SGLANG/.codex/scripts" "$SGLANG/.codex-artifacts/handoffs" "$SGLANG/.codex-artifacts/goals" "$SGLANG/.codex-artifacts/logs" "$SGLANG/.codex-artifacts/reviews" "$SGLANG/.codex-artifacts/session-budget"
  cp "$KIT_ROOT/repo/AGENTS.override.md" "$SGLANG/AGENTS.override.md"
  cp "$KIT_ROOT/repo/.sembleignore" "$SGLANG/.sembleignore"
  cp -a "$KIT_ROOT/repo/.codex/." "$SGLANG/.codex/"
  chmod +x "$SGLANG/.codex/scripts/"*.sh "$SGLANG/.codex/scripts/"*.py
  if enabled "${INSTALL_OPENCODE:-0}"; then cp "$KIT_ROOT/opencode/opencode.minimal.json" "$SGLANG/opencode.json"; fi
fi
printf '%s\n' "$VER" > "$SGLANG/.agents/.workflow-kit-version"
enabled "${INSTALL_REPO_WORKFLOW:-1}" && printf '%s\n' "$VER" > "$SGLANG/.codex/KIT_VERSION"
EXCLUDE="$(git -C "$SGLANG" rev-parse --git-path info/exclude)"; [[ "$EXCLUDE" == /* ]] || EXCLUDE="$SGLANG/$EXCLUDE"
mkdir -p "$(dirname "$EXCLUDE")"; touch "$EXCLUDE"
for e in '.agents/' '.codex/' '.codex-artifacts/' 'AGENTS.override.md' '.sembleignore' 'opencode.json'; do grep -Fxq "$e" "$EXCLUDE" || echo "$e" >> "$EXCLUDE"; done
WORKFLOW_SKILLS_LOCK="$KIT_ROOT/skills.lock.json" SGLANG="$SGLANG" CODE_ROOT="$CODE_ROOT" python3 "$KIT_ROOT/bin/workflow-skills" snapshot || true
WORKFLOW_SKILLS_LOCK="$KIT_ROOT/skills.lock.json" SGLANG="$SGLANG" CODE_ROOT="$CODE_ROOT" python3 "$KIT_ROOT/bin/workflow-skills" index || true
echo "Workspace setup complete: $SGLANG"
