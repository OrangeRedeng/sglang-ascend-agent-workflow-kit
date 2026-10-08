#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def run(cmd: list[str], cwd: Path, timeout: int = 12) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return p.returncode, p.stdout.strip()
    except Exception as exc:
        return 1, str(exc)


def hook_commands(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: list[str] = []
    for groups in data.get("hooks", {}).values():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            for hook in group.get("hooks", []):
                if isinstance(hook, dict) and hook.get("command"):
                    out.append(str(hook["command"]))
    return out


def extensions(root: Path) -> tuple[bool, set[str], str]:
    code = shutil.which("code")
    if not code:
        return False, set(), "code command unavailable"
    rc, out = run([code, "--list-extensions"], root, timeout=45)
    if rc:
        return False, set(), out or "extension query failed"
    return True, {x.strip().lower() for x in out.splitlines() if x.strip()}, ""


def skill_health(root: Path) -> tuple[int, list[str]]:
    base = root / ".agents/skills"
    if not base.is_dir():
        return 0, ["missing .agents/skills"]
    issues: list[str] = []
    names: dict[str, Path] = {}
    count = 0
    for child in sorted(base.iterdir()):
        skill = child / "SKILL.md"
        if not skill.is_file():
            continue
        count += 1
        text = skill.read_text(encoding="utf-8", errors="replace")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
        if not m:
            issues.append(f"{child.name}: missing frontmatter")
            continue
        front = m.group(1)
        nm = re.search(r"(?m)^name:\s*['\"]?([^'\"\n]+)", front)
        desc = re.search(r"(?m)^description:\s*.+$", front)
        if not nm:
            issues.append(f"{child.name}: missing name")
            continue
        name = nm.group(1).strip()
        if name != child.name:
            issues.append(f"{child.name}: name={name!r}; directory must match for Codex/Copilot portability")
        if not desc:
            issues.append(f"{child.name}: missing description")
        if name in names and names[name] != child:
            issues.append(f"duplicate skill name {name}: {names[name]} and {child}")
        names[name] = child
    return count, issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", type=Path, default=Path.cwd())
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rc, root_s = run(["git", "rev-parse", "--show-toplevel"], args.cwd.resolve())
    if rc:
        print("Not inside a Git worktree.", file=sys.stderr)
        return 2
    root = Path(root_s)
    home = Path.home()
    cfgdir = Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config"))) / "sglang-workflow"

    def read_marker(path: Path) -> str:
        return path.read_text().strip() if path.is_file() else ""

    versions = {
        "global": read_marker(cfgdir / "workflow-kit-version"),
        "workspace": read_marker(root / ".agents/.workflow-kit-version"),
        "codex": read_marker(root / ".codex/KIT_VERSION"),
    }
    versions_ok = bool(versions["global"] and len(set(versions.values())) == 1)
    ignore_rc, ignore_out = run(["git", "check-ignore", "-v", ".codex-artifacts/"], root)

    codex_path = shutil.which("codex")
    codex_ok = False
    codex_detail = "missing"
    if codex_path:
        crc, cout = run([codex_path, "--version"], root, timeout=20)
        codex_ok = crc == 0 and not codex_path.startswith("/mnt/c/")
        codex_detail = cout.splitlines()[-1] if cout else f"exit={crc}"

    hook_file = home / ".codex/hooks.json"
    commands = hook_commands(hook_file)
    hooks = {
        "session_start": any("session_start.py" in x for x in commands),
        "prompt_guard": any("prompt_guard.py" in x for x in commands),
        "post_tool_budget": any("post_tool_budget.py" in x for x in commands),
    }

    ext_ok, exts, ext_detail = extensions(root)
    ext_state = {
        "openai_codex": "openai.chatgpt" in exts,
        "copilot_chat": "github.copilot-chat" in exts,
        "codex_bridge": "grikomsn.openai-oauth-copilot-chat" in exts,
        "glm_copilot": "yijiazhen-qi.glm-for-github-copilot-chat" in exts,
        "kilo_absent": "kilocode.kilo-code" not in exts,
    }

    skill_count, skill_issues = skill_health(root)
    legacy_paths = [p for p in (".kilo", "kilo.jsonc", "AGENTS.override.md", ".sembleignore", "opencode.json") if (root / p).exists() or (root / p).is_symlink()]

    checks = {
        "root": str(root),
        "versions": versions,
        "versions_in_sync": versions_ok,
        "artifacts_ignored": ignore_rc == 0,
        "artifact_ignore_rule": ignore_out,
        "codex": {"path": codex_path, "healthy": codex_ok, "detail": codex_detail},
        "hooks": hooks,
        "extensions_query_ok": ext_ok,
        "extensions_query_detail": ext_detail,
        "extensions": ext_state,
        "agents_md": (root / "AGENTS.md").is_file(),
        "skill_count": skill_count,
        "skill_issues": skill_issues,
        "skills_snapshot": (root / ".agents/.skills-resolved.json").is_file(),
        "skills_index": (root / ".agents/.skills-index.json").is_file(),
        "legacy_workspace_paths": legacy_paths,
        "review_packet": (root / ".codex/scripts/workflow-review-packet.py").is_file(),
        "log_reducer": (root / ".codex/scripts/extract-log-context.py").is_file(),
    }

    ok = (
        versions_ok
        and checks["artifacts_ignored"]
        and all(hooks.values())
        and checks["agents_md"]
        and skill_count > 0
        and not skill_issues
        and not legacy_paths
        and (not ext_ok or all(ext_state.values()))
    )

    if args.json:
        print(json.dumps(checks, indent=2, ensure_ascii=False))
        return 0 if ok else 1

    print(f"Workflow root: {root}")
    print(f"[{'OK' if versions_ok else 'FAIL'}] versions: " + ", ".join(f"{k}={v or '-'}" for k,v in versions.items()))
    print(f"[{'OK' if checks['artifacts_ignored'] else 'FAIL'}] .codex-artifacts/ is Git-ignored")
    print(f"[{'OK' if codex_ok else 'WARN'}] Codex WSL CLI: {codex_path or 'missing'} :: {codex_detail}")
    print(f"[{'OK' if all(hooks.values()) else 'FAIL'}] Codex hooks: " + ", ".join(f"{k}={'on' if v else 'missing'}" for k,v in hooks.items()))
    if ext_ok:
        print(f"[{'OK' if ext_state['openai_codex'] else 'FAIL'}] OpenAI Codex VS Code extension")
        print(f"[{'OK' if ext_state['copilot_chat'] else 'FAIL'}] GitHub Copilot Chat extension")
        print(f"[{'OK' if ext_state['codex_bridge'] else 'FAIL'}] Codex Bridge extension")
        print(f"[{'OK' if ext_state['glm_copilot'] else 'FAIL'}] GLM for Copilot Chat extension")
        print(f"[{'OK' if ext_state['kilo_absent'] else 'FAIL'}] Kilo extension absent")
    else:
        print(f"[INFO] VS Code extension query unavailable: {ext_detail}")
    print(f"[{'OK' if checks['agents_md'] else 'FAIL'}] shared root AGENTS.md")
    print(f"[{'OK' if skill_count > 0 and not skill_issues else 'FAIL'}] shared skills: {skill_count}")
    for issue in skill_issues:
        print(f"  - {issue}")
    print(f"[{'OK' if not legacy_paths else 'FAIL'}] legacy Kilo/OpenCode/search workspace files removed" + (f": {', '.join(legacy_paths)}" if legacy_paths else ""))
    print(f"[{'OK' if checks['skills_snapshot'] else 'INFO'}] pinned skill snapshot")
    print(f"[{'OK' if checks['skills_index'] else 'INFO'}] generated skill index")
    print("Codex Bridge OAuth/profile and GLM API key are intentionally not readable by this doctor because VS Code stores them in SecretStorage/UI state.")
    print("Use workflow-copilot guide for the remaining account steps. Native Codex hooks apply only in the official Codex fallback.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
