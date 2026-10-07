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
    "docs/INSTALLATION.md", "docs/VSCODE.md", "docs/MULTI_MODEL.md", "docs/MODELS.md", "docs/ASCEND.md", "docs/SKILLS.md",
    "docs/WORKFLOW.md", "docs/TOOLING.md", "docs/AUTOMATION.md", "docs/TROUBLESHOOTING.md", "docs/UPDATING.md", "docs/VERSIONING.md",
    "PRINT_RULES.pdf", "bin/ai-task", "bin/codex-glm", "bin/glm-task", "bin/workflow-configure", "bin/workflow-provider-token",
    "bin/workflow-skills", "bin/workflow-handoffs", "bin/workflow-exp", "codex/config/config.toml", "codex/models.glm.json", "codex/hooks.json",
    "codex/hooks/post_tool_budget.py", "scripts/merge-codex-config.py", "scripts/merge-codex-hooks.py", "opencode/models.env.example",
    "wsl/02-bootstrap-wsl.sh", "wsl/03-setup-sglang-workspace.sh", "wsl/04-install-ascend-kernel-skills-optional.sh", "wsl/06-update-existing-workspace.sh",
    "repo/AGENTS.override.md", "repo/.agents/skills/sglang-ascend-kernel-dev/SKILL.md", "repo/.agents/skills/sglang-npu-perf-experiment/SKILL.md",
    "repo/.codex/scripts/workflow-doctor.py", "repo/.codex/scripts/workflow-review-packet.py", "repo/.codex/scripts/extract-log-context.py",
    "repo/.codex/scripts/handoff-status.py", "repo/.codex/scripts/new-goal.sh",
]
for path in required:
    require(path)

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

for path in (ROOT / "codex/config").glob("*.toml"):
    try:
        tomllib.loads(path.read_text())
    except Exception as exc:
        errors.append(f"invalid TOML {path.relative_to(ROOT)}: {exc}")

try:
    base = tomllib.loads((ROOT / "codex/config/config.toml").read_text())
    for forbidden in ("model", "model_provider", "model_catalog_json"):
        if forbidden in base:
            errors.append(f"default Codex config must not own user {forbidden}")
except Exception:
    pass

for region, url in {"china": "https://open.bigmodel.cn/api/v1", "global": "https://api.z.ai/api/v1"}.items():
    for effort in ("low", "high", "max"):
        path = ROOT / f"codex/config/glm-{region}-{effort}.config.toml"
        require(str(path.relative_to(ROOT)))
        if path.exists():
            data = tomllib.loads(path.read_text())
            text = path.read_text()
            if data.get("model") != "glm-5.3":
                errors.append(f"{path.name}: model")
            if data.get("model_reasoning_effort") != effort:
                errors.append(f"{path.name}: effort")
            if url not in text or 'wire_api = "responses"' not in text:
                errors.append(f"{path.name}: endpoint/wire API")
            if "AI_GLM_API_KEY" in text or "experimental_bearer_token" in text:
                errors.append(f"{path.name}: secret must not be embedded")

try:
    models = json.loads((ROOT / "codex/models.glm.json").read_text())
    model = models["models"][0]
    if model["slug"] != "glm-5.3" or model["context_window"] != 1048576:
        errors.append("invalid GLM model catalog")
except Exception as exc:
    errors.append(f"GLM catalog: {exc}")

try:
    hooks = json.loads((ROOT / "codex/hooks.json").read_text())
    if "PostToolUse" not in hooks.get("hooks", {}):
        errors.append("codex/hooks.json missing PostToolUse governor")
except Exception as exc:
    errors.append(f"hooks JSON: {exc}")

try:
    lock = json.loads((ROOT / "skills.lock.json").read_text())
    if lock.get("schema") != "sglang-ascend-skill-sources/v2":
        errors.append("skills.lock schema must be v2")
    sources = lock["sources"]
    for name in ("cannbot-skills", "kernelhive-ascendc", "awesome-ascend-skills", "ascend-agent-skills"):
        source = sources.get(name)
        if not source:
            errors.append(f"skills.lock missing {name}")
            continue
        pin = str(source.get("commit", ""))
        if not re.fullmatch(r"[0-9a-f]{8,40}", pin):
            errors.append(f"skills.lock {name} is not pinned to immutable commit: {pin!r}")
        if not source.get("selected_skills"):
            errors.append(f"skills.lock {name} has no selected_skills")
        if source.get("commit") in {"main", "master", "HEAD"}:
            errors.append(f"skills.lock {name} uses floating ref")
except Exception as exc:
    errors.append(f"skills.lock: {exc}")

executables = [
    "setup.sh", "bin/ai-task", "bin/codex-glm", "bin/glm-task", "bin/workflow-configure", "bin/workflow-provider-token",
    "bin/workflow-skills", "bin/workflow-handoffs", "bin/workflow-exp", "wsl/02-bootstrap-wsl.sh", "wsl/03-setup-sglang-workspace.sh",
    "wsl/04-install-ascend-kernel-skills-optional.sh", "wsl/06-update-existing-workspace.sh", "scripts/merge-codex-config.py", "scripts/merge-codex-hooks.py",
    "codex/hooks/post_tool_budget.py", "repo/.codex/scripts/workflow-review-packet.py", "repo/.codex/scripts/extract-log-context.py",
]
for path in executables:
    if (ROOT / path).exists() and not os.access(ROOT / path, os.X_OK):
        errors.append(f"not executable: {path}")

contracts = {
    "wsl/02-bootstrap-wsl.sh": [
        "merge-codex-config.py", "merge-codex-hooks.py", "codex/hooks/*.py", "workflow-handoffs", "workflow-exp",
    ],
    "setup.sh": [
        "Standard - Codex-first workflow + core Ascend skills (Semble/Serena optional)", "INSTALL_SEMBLE=0", "INSTALL_GLM",
    ],
    "codex/hooks/post_tool_budget.py": [
        "SOFT_DEFAULT = 32", "CHECKPOINT_DEFAULT = 44", "systemMessage", "session-budget", "file_identity",
    ],
    "repo/.codex/scripts/extract-log-context.py": [
        "default=32768", "default=400", "--expand", "UNIQUE_SIGNATURES", "normalize_signature",
    ],
    "repo/.codex/scripts/workflow-review-packet.py": [
        "DEFAULT_MAX_BYTES = 98304", "--unified=", ".codex-artifacts", "reviews",
    ],
    "repo/.codex/scripts/handoff-status.py": ["archived", "archive_reason", "older-than-hours", "gc"],
    "repo/AGENTS.override.md": [
        "one active editing-agent session per Git worktree", ">=1 MiB", "sglang-ascend-kernel-dev", "sglang-npu-perf-experiment",
        "Measured retrieval budget", "workflow-review-packet.py", "workflow-handoffs gc", "workflow-exp record",
    ],
    "README.md": [
        "OpenCode stays optional", "workflow-skills status", "GLM Coding Plan", "PostToolUse", "workflow-review-packet.py",
        "Standard | Codex-first workflow + OpenAI extension + core Ascend skills; Semble/Serena off",
    ],
    "wsl/06-update-existing-workspace.sh": ["v0.1.x", "Created migration manifest", "install.env"],
    "bin/workflow-skills": ["checkout", "--detach", "update requires at least one --only SOURCE", ".skills-index.json"],
}
for rel, needles in contracts.items():
    path = ROOT / rel
    if path.exists():
        text = path.read_text()
        for needle in needles:
            if needle not in text:
                errors.append(f"{rel}: missing contract {needle}")

# Destructive upgrade regressions must never return. Fresh-only config creation is allowed.
bootstrap = (ROOT / "wsl/02-bootstrap-wsl.sh").read_text() if (ROOT / "wsl/02-bootstrap-wsl.sh").exists() else ""
if 'if [[ ! -e "$CODEX_HOME/config.toml" ]]' not in bootstrap or "merge-codex-config.py" not in bootstrap:
    errors.append("bootstrap lacks guarded/non-destructive config creation")
if 'backup "$CODEX_HOME/config.toml"' in bootstrap:
    errors.append("bootstrap still uses legacy replace-style config backup path")
if 'cp "$KIT_ROOT/codex/hooks.json" "$CODEX_HOME/hooks.json"' in bootstrap:
    errors.append("bootstrap destructively copies hooks.json")
if "merge-codex-hooks.py" not in bootstrap:
    errors.append("bootstrap does not merge hooks")

if errors:
    print("Repository validation failed:", file=sys.stderr)
    for error in errors:
        print("- " + error, file=sys.stderr)
    raise SystemExit(1)
print("Repository metadata, non-destructive Codex migration, retrieval governor, bounded reducers, skill pins, and provider isolation: OK")
