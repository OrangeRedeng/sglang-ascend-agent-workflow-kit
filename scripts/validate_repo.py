#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
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
    "repo/.codex/handoffs/TEMPLATE.md",
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


contracts = {
    "repo/AGENTS.override.md": [
        "1 MiB",
        "10,000 lines",
        "MUST NOT",
        "**MUST** write a compact handoff",
        "Do not perform another broad PR review",
    ],
    "repo/.agents/skills/sglang-pr-review/SKILL.md": [
        "write `.codex/handoffs/pr-<N>-review.md` before stopping",
    ],
    "docs/VSCODE.md": [
        "recommended daily interface",
        "WSL: Ubuntu",
        "The current CLI conversation and the current extension conversation are separate sessions",
    ],
    "docs/AUTOMATION.md": [
        "Hard-enforced",
        "Instruction-enforced",
        "Large logs - automatic by rule",
        "Handoffs - automatic by rule",
        "Extension vs CLI",
    ],
    "README.md": [
        "Recommended daily workflow: VS Code extension",
        "Do not run `cx` just to",
    ],
    "windows/01-bootstrap-windows.ps1": [
        "Ensure-VSCodeExtension",
        "OpenAI.chatgpt",
        "ms-vscode-remote.remote-wsl",
    ],
    "wsl/03-setup-sglang-workspace.sh": [
        "VS Code Codex extension",
        "start a new local session",
        "CLI is optional and independent",
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
