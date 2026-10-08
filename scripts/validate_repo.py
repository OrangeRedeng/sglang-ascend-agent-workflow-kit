#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []


def require(path: str) -> None:
    if not (ROOT / path).exists():
        errors.append(f"missing: {path}")


required = [
    "README.md", "VERSION", "CHANGELOG.md", "skills.lock.json", "setup.sh", ".github/workflows/validate.yml",
    "docs/INSTALLATION.md", "docs/VSCODE.md", "docs/MODELS.md", "docs/ASCEND.md", "docs/SKILLS.md",
    "docs/WORKFLOW.md", "docs/TROUBLESHOOTING.md", "docs/UPDATING.md", "docs/VERSIONING.md",
    "bin/workflow-codex", "bin/workflow-copilot", "bin/workflow-skills", "bin/workflow-handoffs", "bin/workflow-exp", "bin/workflow-setup",
    "codex/config/config.toml", "codex/hooks.json", "codex/hooks/post_tool_budget.py",
    "scripts/merge-codex-config.py", "scripts/merge-codex-hooks.py",
    "wsl/02-bootstrap-wsl.sh", "wsl/03-setup-sglang-workspace.sh", "wsl/04-install-ascend-kernel-skills-optional.sh", "wsl/06-update-existing-workspace.sh",
    "repo/AGENTS.md", "repo/.agents/skills/sglang-ascend-kernel-dev/SKILL.md", "repo/.agents/skills/sglang-npu-perf-experiment/SKILL.md",
    "repo/.codex/scripts/workflow-doctor.py", "repo/.codex/scripts/workflow-review-packet.py", "repo/.codex/scripts/extract-log-context.py",
    "repo/.codex/scripts/handoff-status.py", "repo/.codex/scripts/new-goal.sh",
]
for path in required:
    require(path)

for forbidden in [
    "docs/KILO.md", "docs/MULTI_MODEL.md", "opencode", "repo/.kilo", "repo/kilo.jsonc", "repo/AGENTS.override.md", "repo/.sembleignore",
    "bin/workflow-kilo", "bin/workflow-glm-copilot", "bin/ai-task", "bin/codex-glm", "bin/glm-task", "bin/local-task", "bin/cheap-task", "bin/strong-task",
    "bin/workflow-configure", "bin/workflow-provider-token", "codex/models.glm.json", "wsl/05-install-serena-optional.sh", "PRINT_RULES.pdf",
]:
    if (ROOT / forbidden).exists():
        errors.append(f"legacy/forbidden path still present: {forbidden}")

try:
    version = (ROOT / "VERSION").read_text().strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version):
        errors.append(f"invalid VERSION: {version}")
    if f"**Current release:** `v{version}`" not in (ROOT / "README.md").read_text():
        errors.append("README release mismatch")
    if not re.search(rf"^## \[{re.escape(version)}\]", (ROOT / "CHANGELOG.md").read_text(), re.M):
        errors.append("CHANGELOG release mismatch")
except Exception as exc:
    errors.append(f"version: {exc}")

try:
    base = tomllib.loads((ROOT / "codex/config/config.toml").read_text())
    for forbidden in ("model", "model_provider", "model_catalog_json"):
        if forbidden in base:
            errors.append(f"default Codex config must not own user {forbidden}")
except Exception as exc:
    errors.append(f"codex config: {exc}")

try:
    hooks = json.loads((ROOT / "codex/hooks.json").read_text())
    for name in ("SessionStart", "UserPromptSubmit", "PostToolUse"):
        if name not in hooks.get("hooks", {}):
            errors.append(f"codex/hooks.json missing {name}")
except Exception as exc:
    errors.append(f"hooks JSON: {exc}")

# Own skills must already satisfy the portable Agent Skills name contract.
for skill in sorted((ROOT / "repo/.agents/skills").glob("*/SKILL.md")):
    text = skill.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        errors.append(f"{skill.relative_to(ROOT)}: missing frontmatter")
        continue
    front = m.group(1)
    nm = re.search(r"(?m)^name:\s*['\"]?([^'\"\n]+)", front)
    desc = re.search(r"(?m)^description:\s*.+$", front)
    if not nm:
        errors.append(f"{skill.relative_to(ROOT)}: missing name")
    elif nm.group(1).strip() != skill.parent.name:
        errors.append(f"{skill.relative_to(ROOT)}: name must match directory")
    if not desc:
        errors.append(f"{skill.relative_to(ROOT)}: missing description")

try:
    lock = json.loads((ROOT / "skills.lock.json").read_text())
    if lock.get("schema") != "sglang-ascend-skill-sources/v2":
        errors.append("skills.lock schema must be v2")
    for name in ("awesome-ascend-skills", "ascend-agent-skills", "cannbot-skills", "kernelhive-ascendc", "bbuf"):
        source = lock.get("sources", {}).get(name)
        if not source:
            errors.append(f"skills.lock missing {name}")
            continue
        pin = str(source.get("commit", ""))
        if not re.fullmatch(r"[0-9a-f]{8,40}", pin):
            errors.append(f"skills.lock {name} is not pinned: {pin!r}")
        if not source.get("selected_skills"):
            errors.append(f"skills.lock {name} has no selected_skills")
except Exception as exc:
    errors.append(f"skills.lock: {exc}")

executables = [
    "setup.sh", "bin/workflow-codex", "bin/workflow-copilot", "bin/workflow-skills", "bin/workflow-handoffs", "bin/workflow-exp", "bin/workflow-setup",
    "wsl/02-bootstrap-wsl.sh", "wsl/03-setup-sglang-workspace.sh", "wsl/04-install-ascend-kernel-skills-optional.sh", "wsl/06-update-existing-workspace.sh",
    "scripts/merge-codex-config.py", "scripts/merge-codex-hooks.py", "scripts/package-release.sh", "codex/hooks/post_tool_budget.py",
    "repo/.codex/scripts/workflow-review-packet.py", "repo/.codex/scripts/extract-log-context.py",
]
for path in executables:
    if (ROOT / path).exists() and not os.access(ROOT / path, os.X_OK):
        errors.append(f"not executable: {path}")

contracts = {
    "setup.sh": ["Primary UI:", "Codex Bridge:", "GLM Copilot provider:", "Official Codex fallback:", "workflow-setup"],
    "wsl/02-bootstrap-wsl.sh": ["workflow-copilot", "OpenAI.chatgpt", "GitHub.copilot-chat", "grikomsn.openai-oauth-copilot-chat", "yijiazhen-qi.glm-for-github-copilot-chat", "removed legacy Kilo"],
    "wsl/03-setup-sglang-workspace.sh": ["cp \"$KIT_ROOT/repo/AGENTS.md\"", "link_exact", "directory name == SKILL.md frontmatter name", "rm -rf \"$SGLANG/.kilo\"", "'.vscode/settings.json'"],
    "bin/workflow-copilot": ["grikomsn.openai-oauth-copilot-chat", "glm-copilot.apiMode", '"coding-plan"', "glm-copilot.region", '"china"', "openaiCodex.showUsageStatusBar", "Codex Bridge: Add ChatGPT Account", "GLM: Set API Key"],
    "repo/AGENTS.md": ["One active editing agent per Git worktree", ">=1 MiB", "workflow-review-packet.py", "sglang-ascend-kernel-dev", "sglang-npu-perf-experiment"],
    "repo/.codex/scripts/extract-log-context.py": ["default=32768", "default=400", "--expand", "normalize_signature"],
    "repo/.codex/scripts/workflow-review-packet.py": ["DEFAULT_MAX_BYTES = 98304", "--unified=", ".codex-artifacts", "reviews"],
    "codex/hooks/post_tool_budget.py": ["SOFT_DEFAULT = 32", "CHECKPOINT_DEFAULT = 44", "session-budget"],
    "README.md": ["GitHub Copilot Chat", "Codex Bridge", "GLM Models for GitHub Copilot Chat", "workflow-copilot", "AGENTS.md", ".agents/skills/"],
}
for rel, needles in contracts.items():
    path = ROOT / rel
    if not path.exists():
        continue
    text = path.read_text()
    for needle in needles:
        if needle not in text:
            errors.append(f"{rel}: missing contract {needle}")

bootstrap = (ROOT / "wsl/02-bootstrap-wsl.sh").read_text()
if re.search(r"npm\s+install\s+-g\s+@openai/codex", bootstrap):
    errors.append("bootstrap must not root/global-update Codex")
if "merge-codex-hooks.py" not in bootstrap:
    errors.append("bootstrap does not merge hooks")
if 'cp "$KIT_ROOT/codex/hooks.json" "$CODEX_HOME/hooks.json"' in bootstrap:
    errors.append("bootstrap destructively copies hooks")

workspace = (ROOT / "wsl/03-setup-sglang-workspace.sh").read_text()
if re.search(r">\s*\"\$SGLANG/\.agents/\.workflow-kit-version\"", workspace) or re.search(r">\s*\"\$SGLANG/\.codex/KIT_VERSION\"", workspace):
    errors.append("workspace layer writes version markers before transaction completes")

if errors:
    print("Repository validation failed:", file=sys.stderr)
    for error in errors:
        print("- " + error, file=sys.stderr)
    raise SystemExit(1)
print("Repository metadata, unified Copilot UI, Codex Bridge + GLM providers, canonical Agent Skills, bounded retrieval, and legacy cleanup: OK")
