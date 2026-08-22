#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE_ROOT="${CODE_ROOT:-$HOME/code}"
SGLANG="${SGLANG:-$CODE_ROOT/sglang}"
KERNEL="${KERNEL:-$CODE_ROOT/sgl-kernel-npu}"
BBUF="${BBUF:-$CODE_ROOT/AI-Infra-Auto-Driven-SKILLS}"
ASCEND_AWESOME="${ASCEND_AWESOME:-$CODE_ROOT/awesome-ascend-skills}"
ASCEND_OFFICIAL="${ASCEND_OFFICIAL:-$CODE_ROOT/ascend-agent-skills}"
KIT_VERSION="$(tr -d '[:space:]' < "$KIT_ROOT/VERSION")"
INSTALL_LEVEL="${INSTALL_LEVEL:-standard}"
INSTALL_REPO_WORKFLOW="${INSTALL_REPO_WORKFLOW:-1}"
INSTALL_ASCEND_SKILLS="${INSTALL_ASCEND_SKILLS:-1}"
INSTALL_BBUF_SKILLS="${INSTALL_BBUF_SKILLS:-0}"
INSTALL_KERNEL_REPO="${INSTALL_KERNEL_REPO:-0}"
INSTALL_KERNEL_SKILLS="${INSTALL_KERNEL_SKILLS:-0}"
INSTALL_VSCODE_CODEX="${INSTALL_VSCODE_CODEX:-0}"
INSTALL_SEMBLE="${INSTALL_SEMBLE:-1}"
INSTALL_SERENA="${INSTALL_SERENA:-0}"
WORKFLOW_ACTION="${WORKFLOW_ACTION:-install}"

log() { printf '\n==> %s\n' "$*"; }
enabled() { [[ "${1:-0}" == 1 ]]; }
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
    mkdir -p "$SGLANG/.agents/skills"
    ln -sfn "$src" "$SGLANG/.agents/skills/$name"
    echo "linked: $name -> $src"
  else
    echo "missing (skipped): $src"
  fi
}

mkdir -p "$CODE_ROOT"
log "SGLang repository"
clone_if_missing https://github.com/sgl-project/sglang.git "$SGLANG"

PREVIOUS_WORKSPACE_VERSION="$(cat "$SGLANG/.agents/.workflow-kit-version" 2>/dev/null | tr -d '[:space:]' || true)"
if [[ -z "$PREVIOUS_WORKSPACE_VERSION" ]]; then
  PREVIOUS_WORKSPACE_VERSION="$(cat "$SGLANG/.codex/KIT_VERSION" 2>/dev/null | tr -d '[:space:]' || true)"
fi
if [[ -n "$PREVIOUS_WORKSPACE_VERSION" ]]; then
  cmp="$(python3 "$KIT_ROOT/scripts/kit-version.py" compare "$PREVIOUS_WORKSPACE_VERSION" "$KIT_VERSION")" || exit 2
  if [[ "$cmp" == 1 && "${ALLOW_DOWNGRADE:-0}" != 1 ]]; then
    echo "ERROR: installed workspace workflow $PREVIOUS_WORKSPACE_VERSION is newer than incoming $KIT_VERSION." >&2
    echo "Use ALLOW_DOWNGRADE=1 only for an intentional downgrade." >&2
    exit 2
  fi
fi

log "Bundled SGLang workflow skills"
mkdir -p "$SGLANG/.agents/skills"
cp -a "$KIT_ROOT/repo/.agents/skills/." "$SGLANG/.agents/skills/"

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

# SGLang + Ascend is the primary project purpose. Even the Light profile is
# skills-only rather than "bundled-skills-only": it installs the core Ascend
# expert skill sources without installing a model client, router, MCP server,
# hooks, or mutable workflow state.
if enabled "$INSTALL_ASCEND_SKILLS"; then
  log "Ascend skill repositories"
  clone_if_missing https://github.com/ascend-ai-coding/awesome-ascend-skills.git "$ASCEND_AWESOME"
  clone_if_missing https://github.com/Ascend/agent-skills.git "$ASCEND_OFFICIAL"

  log "Core Ascend/torch_npu leaf skills"
  link_skill "$ASCEND_AWESOME/skills/base/torch_npu" "ascend-torch-npu"
  link_skill "$ASCEND_AWESOME/skills/profiling/profiling-analysis" "ascend-profiling-analysis"
  link_skill "$ASCEND_AWESOME/skills/profiling/pytorch-profiling-collection" "ascend-pytorch-profiling-collection"
  link_skill "$ASCEND_AWESOME/skills/ops/npu-op-benchmark" "ascend-npu-op-benchmark"
  link_skill "$ASCEND_OFFICIAL/skills/npu-adapter-reviewer" "official-npu-adapter-reviewer"
  link_skill "$ASCEND_OFFICIAL/skills/ascend-profiling-anomaly" "official-ascend-profiling-anomaly"
  link_skill "$ASCEND_OFFICIAL/skills/hccl-test" "official-hccl-test"
fi

if [[ "$INSTALL_LEVEL" == light ]]; then
  printf '%s\n' "$KIT_VERSION" > "$SGLANG/.agents/.workflow-kit-version"
  EXCLUDE="$(git -C "$SGLANG" rev-parse --git-path info/exclude)"
  [[ "$EXCLUDE" == /* ]] || EXCLUDE="$SGLANG/$EXCLUDE"
  mkdir -p "$(dirname "$EXCLUDE")"; touch "$EXCLUDE"
  grep -Fxq ".agents/" "$EXCLUDE" || echo ".agents/" >> "$EXCLUDE"
  cat <<EOF

Light installation complete.
Installed only the SGLang + Ascend skill layer into:
  $SGLANG/.agents/skills/
No Codex/OpenCode client, router, hooks, Semble, Serena, or mutable workflow state was installed by this level.
EOF
  exit 0
fi

if enabled "$INSTALL_KERNEL_REPO"; then
  log "SGLang NPU kernel repository"
  clone_if_missing https://github.com/sgl-project/sgl-kernel-npu.git "$KERNEL"
fi

if enabled "$INSTALL_BBUF_SKILLS"; then
  log "BBuf skill repository"
  clone_if_missing https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS.git "$BBUF"
fi

if enabled "$INSTALL_REPO_WORKFLOW"; then
  log "Provider-neutral repo workflow layer"
  mkdir -p "$SGLANG/.codex/scripts" "$SGLANG/.codex-artifacts/handoffs" "$SGLANG/.codex-artifacts/goals" "$SGLANG/.codex-artifacts/logs"
  if [[ -d "$SGLANG/.codex/handoffs" || -d "$SGLANG/.codex/goals" || -d "$SGLANG/.codex/logs" ]]; then
    cp "$KIT_ROOT/repo/.codex/scripts/migrate-artifacts.py" "$SGLANG/.codex/scripts/migrate-artifacts.py"
    chmod +x "$SGLANG/.codex/scripts/migrate-artifacts.py"
    python3 "$SGLANG/.codex/scripts/migrate-artifacts.py" --root "$SGLANG" --remove-legacy
  fi
  cp "$KIT_ROOT/repo/AGENTS.override.md" "$SGLANG/AGENTS.override.md"
  cp "$KIT_ROOT/repo/.sembleignore" "$SGLANG/.sembleignore"
  cp "$KIT_ROOT/opencode/opencode.minimal.json" "$SGLANG/opencode.json"
  python3 - "$SGLANG/opencode.json" "$INSTALL_SEMBLE" "$INSTALL_SERENA" <<'PYCFG'
from pathlib import Path
import json, sys
p=Path(sys.argv[1]); use_semble=sys.argv[2]=='1'; use_serena=sys.argv[3]=='1'
data=json.loads(p.read_text(encoding='utf-8'))
mcp={}
if use_semble:
    mcp['semble']={
        'type':'local',
        'command':['uvx','--from','semble[mcp]','semble'],
        'enabled':True,
        'timeout':120000,
    }
if use_serena:
    mcp['serena']={
        'type':'local',
        'command':['serena','start-mcp-server','--project-from-cwd','--context=oaicompat-agent'],
        'enabled':True,
        'timeout':60000,
    }
if mcp:
    data['mcp']=mcp
p.write_text(json.dumps(data, indent=2)+"\n",encoding='utf-8')
PYCFG
  cp -a "$KIT_ROOT/repo/.codex/." "$SGLANG/.codex/"
  chmod +x "$SGLANG/.codex/scripts/"*.sh "$SGLANG/.codex/scripts/"*.py
fi

if enabled "$INSTALL_BBUF_SKILLS"; then
  log "Selected BBuf skills"
  for wanted in \
    sglang-humanize-review \
    model-pr-optimization-history \
    llm-torch-profiler-analysis \
    llm-pipeline-analysis \
    sglang-prod-incident-triage
  do
    found="$(find "$BBUF" -type f -name SKILL.md -path "*/$wanted/SKILL.md" -print -quit 2>/dev/null || true)"
    if [[ -n "$found" ]]; then link_skill "$(dirname "$found")" "bbuf-$wanted"; else echo "not found (skipped): $wanted"; fi
  done
fi

if enabled "$INSTALL_KERNEL_SKILLS"; then
  log "Optional kernel skill bundle"
  "$KIT_ROOT/wsl/04-install-ascend-kernel-skills-optional.sh" all || echo "Warning: some optional kernel skills were unavailable." >&2
fi

log "Keep workflow state out of upstream PRs"
EXCLUDE="$(git -C "$SGLANG" rev-parse --git-path info/exclude)"
[[ "$EXCLUDE" == /* ]] || EXCLUDE="$SGLANG/$EXCLUDE"
mkdir -p "$(dirname "$EXCLUDE")"; touch "$EXCLUDE"
for entry in ".agents/"; do grep -Fxq "$entry" "$EXCLUDE" || echo "$entry" >> "$EXCLUDE"; done
if enabled "$INSTALL_REPO_WORKFLOW"; then
  for entry in ".codex/" ".codex-artifacts/" "AGENTS.override.md" ".sembleignore" "opencode.json"; do
    grep -Fxq "$entry" "$EXCLUDE" || echo "$entry" >> "$EXCLUDE"
  done
  if ! (cd "$SGLANG" && git check-ignore -q .codex-artifacts/); then
    echo "ERROR: .codex-artifacts/ is not ignored by Git after setup." >&2
    exit 1
  fi
fi

printf '%s\n' "$KIT_VERSION" > "$SGLANG/.agents/.workflow-kit-version"
if enabled "$INSTALL_REPO_WORKFLOW"; then
  printf '%s\n' "$KIT_VERSION" > "$SGLANG/.codex/KIT_VERSION"
  mkdir -p "$SGLANG/.codex-artifacts"
  VERSION_HISTORY="$SGLANG/.codex-artifacts/kit-version-history.tsv"
  if [[ ! -s "$VERSION_HISTORY" ]]; then printf 'timestamp_utc\taction\tprevious_version\tnew_version\n' > "$VERSION_HISTORY"; fi
  printf '%s\t%s\t%s\t%s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$WORKFLOW_ACTION" "${PREVIOUS_WORKSPACE_VERSION:-unversioned}" "$KIT_VERSION" >> "$VERSION_HISTORY"
fi

if enabled "$INSTALL_VSCODE_CODEX"; then
  log "VS Code Codex extension"
  if command -v code >/dev/null 2>&1; then
    if ! code --list-extensions 2>/dev/null | grep -qi '^openai\.chatgpt$'; then
      code --install-extension OpenAI.chatgpt --force || echo "Warning: install OpenAI.chatgpt from the VS Code Extensions panel." >&2
    fi
  else
    echo "Warning: 'code' CLI not found. Install VS Code + Remote - WSL on Windows." >&2
  fi
fi

log "Verification"
cd "$SGLANG"
printf 'Repo:   %s\n' "$(git remote get-url origin)"
printf 'Branch: %s\n' "$(git branch --show-current)"
printf 'Skills: %s\n' "$(find -L .agents/skills -maxdepth 2 -name SKILL.md | wc -l)"
if enabled "$INSTALL_REPO_WORKFLOW"; then
  printf '\nWorkflow doctor:\n  cd %q\n  python3 .codex/scripts/workflow-doctor.py\n' "$SGLANG"
fi
printf '\nWorkspace setup complete: %s\n' "$SGLANG"
