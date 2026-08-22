#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
errors: list[str] = []


def require(path: str) -> None:
    p = ROOT / path
    if not p.exists():
        errors.append(f"missing required path: {path}")


for path in [
    "README.md",
    ".github/workflows/validate.yml",
    "VERSION",
    "CHANGELOG.md",
    "docs/VERSIONING.md",
    "scripts/kit-version.py",
    "scripts/package-release.sh",
    "PRINT_RULES.pdf",
    "LICENSE",
    "ACKNOWLEDGEMENTS.md",
    "CONTRIBUTING.md",
    "docs/INSTALLATION.md",
    "docs/VSCODE.md",
    "docs/AUTOMATION.md",
    "docs/WORKFLOW.md",
    "docs/TOOLING.md",
    "docs/MULTI_MODEL.md",
    "docs/MODELS.md",
    "setup.sh",
    "docs/ASCEND.md",
    "docs/TROUBLESHOOTING.md",
    "codex/config/config.toml",
    "codex/hooks.json",
    "opencode/opencode.json",
    "opencode/opencode.minimal.json",
    "opencode/models.env.example",
    "bin/cx-task",
    "bin/ai-task",
    "bin/local-task",
    "bin/cheap-task",
    "bin/strong-task",
    "bin/workflow-configure",
    "windows/00-preflight.ps1",
    "windows/01-bootstrap-windows.ps1",
    "wsl/02-bootstrap-wsl.sh",
    "wsl/03-setup-sglang-workspace.sh",
    "scripts/build_print_rules.py",
    "repo/.codex/scripts/extract-log-context.py",
    "repo/.codex/scripts/new-handoff.sh",
    "repo/.codex/templates/handoff.md",
    "repo/.codex/templates/goal/goal.md",
    "repo/.codex/scripts/resolve-handoff.py",
    "repo/.codex/scripts/handoff-status.py",
    "repo/.codex/scripts/migrate-artifacts.py",
    "repo/.codex/scripts/workflow-doctor.py",
    "codex/hooks/session_start.py",
    "wsl/06-update-existing-workspace.sh",
    "docs/UPDATING.md",
]:
    require(path)

try:
    with (ROOT / "codex/hooks.json").open(encoding="utf-8") as f:
        json.load(f)
except Exception as exc:
    errors.append(f"invalid codex/hooks.json: {exc}")

try:
    with (ROOT / "opencode/opencode.json").open(encoding="utf-8") as f:
        opencode_config = json.load(f)
    if "AGENTS.override.md" not in opencode_config.get("instructions", []):
        errors.append("opencode/opencode.json must load AGENTS.override.md")
    if "semble" not in opencode_config.get("mcp", {}):
        errors.append("opencode/opencode.json must configure Semble MCP")
except Exception as exc:
    errors.append(f"invalid opencode/opencode.json: {exc}")

for executable in ["setup.sh", "bin/cx-task", "bin/ai-task", "bin/local-task", "bin/cheap-task", "bin/strong-task", "bin/workflow-configure"]:
    path = ROOT / executable
    if path.exists() and not os.access(path, os.X_OK):
        errors.append(f"router is not executable: {executable}")

for p in sorted((ROOT / "codex/config").glob("*.toml")):
    try:
        with p.open("rb") as f:
            tomllib.load(f)
    except Exception as exc:
        errors.append(f"invalid TOML {p.relative_to(ROOT)}: {exc}")

main_config = ROOT / "codex/config/config.toml"
if main_config.exists():
    text = main_config.read_text(encoding="utf-8")
    if "startup_timeout_sec = 120" not in text:
        errors.append("Semble startup timeout must be 120 seconds in codex/config/config.toml")


# Version contract: root VERSION is SemVer, CHANGELOG contains it, and a pushed vX.Y.Z tag matches it.
version = ""
try:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?", version):
        errors.append(f"VERSION is not SemVer: {version!r}")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if not re.search(rf"^## \[{re.escape(version)}\]", changelog, re.M):
        errors.append(f"CHANGELOG.md has no release heading for VERSION {version}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if f"**Current release:** `v{version}`" not in readme:
        errors.append(f"README current release does not match VERSION v{version}")
except Exception as exc:
    errors.append(f"version metadata error: {exc}")

if os.environ.get("GITHUB_REF_TYPE") == "tag":
    tag = os.environ.get("GITHUB_REF_NAME", "")
    if tag.startswith("v") and version and tag != f"v{version}":
        errors.append(f"Git tag {tag} does not match VERSION v{version}")


contracts = {
    "repo/AGENTS.override.md": [
        "1 MiB",
        "10,000 lines",
        "MUST NOT",
        "Same goal + a materially different implementation strategy",
        "one active editing-agent session per Git worktree",
        "resolve-handoff.py --json",
        "**MUST** write a compact handoff",
        ".codex-artifacts/handoffs/",
        "active handoff pointer",
        "Project priority - SGLang + Ascend correctness",
        "Model-provider choice and token-cost optimization are subordinate",
    ],
    "repo/.agents/skills/sglang-pr-review/SKILL.md": [
        "new-handoff.sh <N>",
        ".codex-artifacts/handoffs/",
    ],
    "docs/VSCODE.md": [
        "recommended daily interface",
        "WSL: Ubuntu",
        "The current CLI conversation and the current extension conversation are separate sessions",
    ],
    "docs/AUTOMATION.md": [
        "Hard / hook-driven",
        "Instruction-enforced",
        "Large logs - automatic by rule",
        "Handoff discovery - automatic by hook",
    ],
    "README.md": [
        "Use Codex as the primary model?",
        "Installation levels",
        "Measured token reduction on SGLang sessions",
        "## Version tracking",
        "~/.config/sglang-workflow/install.env",
        "ai-task --dry-run review 34855",
        "~/.config/sglang-workflow/models.env",
        "./setup.sh --list-model-presets",
        "## Project priority: SGLang + Ascend engineering",
        "SGLang + core Ascend/`torch_npu` skill layer",
    ],

    "setup.sh": [
        "Select installation level:",
        "Use Codex as the primary model?",
        "--level light|standard|full|custom",
        "--list-model-presets",
        "INSTALL_MANIFEST",
        "AI_PRIMARY_BACKEND",
        "workflow-kit-version",
    ],
    "docs/MODELS.md": [
        "Pricing/status checked:",
        "DeepSeek V4",
        "Z.AI / GLM",
        "Kimi",
        "MiniMax",
        "Qwen3-Coder-Plus",
        "OpenRouter free models",
        "Self-hosted models",
        "SGLang + Ascend priority",
        "alibaba-payg",
    ],
    "docs/MULTI_MODEL.md": [
        "AI_PRIMARY_BACKEND",
        "AI_ROUTING_MODE=primary",
        "Provider fallback is not semantic verification",
        "workflow-configure",
        "ai-task --dry-run",
        "Routing invariant: SGLang + Ascend comes first",
        "user-selected primary backend is tried first",
    ],
    "bin/ai-task": [
        "OPENCODE_CONFIG_CONTENT",
        "WORKFLOW_PRODUCER",
        "AI_PRIMARY_BACKEND",
        "AI_ROUTING_MODE",
        "AI_ENABLE_CODEX_FALLBACK",
        "codex_tier_for_kind",
        "hard_primary_kinds",
        "version/runtime/workload baseline",
    ],
    "opencode/models.env.example": [
        "AI_PRIMARY_BACKEND=codex",
        "AI_ROUTING_MODE=primary",
        "AI_LOCAL_MODEL",
        "AI_CHEAP_MODEL",
        "AI_STRONG_MODEL",
    ],
    "repo/.codex/scripts/new-handoff.sh": [
        "producer: ${WORKFLOW_PRODUCER:-codex}",
        "consumer: ${WORKFLOW_CONSUMER:-codex}",
        ".active-pr-",
        "codex-sglang-active-handoff/v1",
    ],
    "repo/.codex/scripts/resolve-handoff.py": [
        "active-pointer",
        "no-active-pointer",
        "STALE_HOURS = 48",
        "is_handoff_template",
    ],
    "repo/.codex/scripts/migrate-artifacts.py": [
        "TEMPLATE-review.md",
        "is_handoff_template",
    ],
    "repo/.codex/scripts/workflow-doctor.py": [
        "hooks/list",
        "trust_status",
        "current_hash",
        "current hash NOT verified",
        "external_model_state",
        "External tiers:",
    ],
    "repo/.codex/scripts/handoff-status.py": [
        ".active-pr-",
        "clear_pointer_if_matching",
    ],
    "codex/hooks.json": [
        "SessionStart",
        "UserPromptSubmit",
        "session_start.py",
        "prompt_guard.py",
    ],
    ".github/workflows/validate.yml": [
        "bash -n setup.sh",
        "bin/local-task",
        "bin/workflow-configure",
        "python3 -m py_compile bin/ai-task bin/workflow-configure",
    ],
    "docs/ASCEND.md": [
        "This is the primary domain workflow of the project",
        "Model-backend invariant",
        "compatibility baseline",
        "silent fallback",
    ],
    "docs/WORKFLOW.md": [
        "selected primary backend is authoritative",
        "cost routing must never bypass the Ascend compatibility baseline",
        "PRIMARY first",
    ],
    "docs/UPDATING.md": [
        "06-update-existing-workspace.sh",
        "setup.sh --update",
        "install.env",
        "ALLOW_DOWNGRADE=1",
        "models.env",
    ],
    "docs/VERSIONING.md": [
        "Semantic Versioning",
        "workflow-kit-version",
        ".agents/.workflow-kit-version",
        "install.env",
        "kit-version-history.tsv",
    ],
    "windows/01-bootstrap-windows.ps1": [
        "Ensure-VSCodeExtension",
        "Model-specific VS Code extensions are installed later",
        "ms-vscode-remote.remote-wsl",
    ],
    "wsl/02-bootstrap-wsl.sh": [
        "workflow-kit-version",
        "KIT_VERSION",
        "INSTALL_CODEX",
        "INSTALL_OPENCODE",
        "models.env",
        "workflow-configure",
    ],
    "wsl/03-setup-sglang-workspace.sh": [
        "Bundled SGLang workflow skills",
        "Light installation complete",
        ".agents/.workflow-kit-version",
        'EXCLUDE="$SGLANG/$EXCLUDE"',
        "Provider-neutral repo workflow layer",
        "opencode.json",
        "awesome-ascend-skills",
        "SGLang + Ascend skill layer",
    ],
    "wsl/06-update-existing-workspace.sh": [
        "saved installation manifest",
        "setup.sh",
        "--update",
        "--workspace",
    ],
}
for rel, needles in contracts.items():
    path = ROOT / rel
    if path.exists():
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"missing workflow contract in {rel}: {needle}")

if errors:
    print("Repository validation failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print("Repository metadata, JSON, TOML, docs, and Semble timeout: OK")
