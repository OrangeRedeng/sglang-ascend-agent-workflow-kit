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
    "docs/ASCEND.md",
    "docs/TROUBLESHOOTING.md",
    "codex/config/config.toml",
    "codex/hooks.json",
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
        "one active Codex session per Git worktree",
        "resolve-handoff.py --json",
        "**MUST** write a compact handoff",
        ".codex-artifacts/handoffs/",
        "active handoff pointer",
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
        "Recommended daily workflow: VS Code extension",
        "Do not run `cx` just to",
        "Measured token reduction on SGLang sessions",
        "## Version tracking",
        "~/.codex/workflow-kit-version",
    ],

    "repo/.codex/scripts/new-handoff.sh": [
        ".active-pr-",
        "codex-sglang-active-handoff/v1",
    ],
    "repo/.codex/scripts/resolve-handoff.py": [
        "active-pointer",
        "no-active-pointer",
        "STALE_HOURS = 48",
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
    "docs/UPDATING.md": [
        "06-update-existing-workspace.sh",
        ".codex-artifacts/handoffs/",
        "start a **new local Codex session**",
        "ALLOW_DOWNGRADE=1",
        "kit-version-history.tsv",
    ],
    "docs/VERSIONING.md": [
        "Semantic Versioning",
        "workflow-kit-version",
        ".codex/KIT_VERSION",
        "kit-version-history.tsv",
    ],
    "windows/01-bootstrap-windows.ps1": [
        "Ensure-VSCodeExtension",
        "OpenAI.chatgpt",
        "ms-vscode-remote.remote-wsl",
    ],
    "wsl/02-bootstrap-wsl.sh": [
        "workflow-kit-version",
        "KIT_VERSION",
    ],
    "wsl/03-setup-sglang-workspace.sh": [
        "VS Code Codex extension",
        "start a new local session",
        "CLI is optional and independent",
        ".codex/KIT_VERSION",
        'EXCLUDE="$SGLANG/$EXCLUDE"',
    ],
    "wsl/06-update-existing-workspace.sh": [
        "ALLOW_DOWNGRADE",
        "workflow-kit-version",
        ".codex/KIT_VERSION",
        "kit-version-history.tsv",
        'EXCLUDE="$SGLANG/$EXCLUDE"',
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
