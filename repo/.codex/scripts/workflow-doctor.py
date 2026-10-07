#!/usr/bin/env python3
"""Check the installed SGLang workflow without exposing credentials."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


def run(cmd: list[str], cwd: Path, timeout: int = 8):
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return p.returncode, p.stdout.strip()
    except Exception as exc:
        return 1, str(exc)


def read_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.is_file():
        return data
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if value[:1] in {'"', "'"}:
            try:
                value = shlex.split(value)[0]
            except Exception:
                pass
        data[key.strip()] = value
    return data


def hook_commands(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    commands = []
    for groups in data.get("hooks", {}).values():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            for hook in group.get("hooks", []):
                if isinstance(hook, dict) and hook.get("command"):
                    commands.append(str(hook["command"]))
    return commands


def glm_smoke(models: dict[str, str]) -> tuple[bool, str]:
    base = models.get("AI_GLM_BASE_URL", "").rstrip("/")
    key = models.get("AI_GLM_API_KEY", "")
    model = models.get("AI_GLM_MODEL", "glm-5.3")
    if not base or not key:
        return False, "GLM endpoint/key is not configured"
    url = base + "/responses"
    body = json.dumps({"model": model, "input": "Reply with OK only.", "max_output_tokens": 16}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "sglang-workflow-doctor/0.3.1",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            raw = response.read(4096)
            if 200 <= response.status < 300:
                try:
                    parsed = json.loads(raw)
                    rid = parsed.get("id") or parsed.get("object") or "response"
                except Exception:
                    rid = "response"
                return True, f"HTTP {response.status} ({rid})"
            return False, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        # Never include response body because providers may echo request metadata.
        return False, f"HTTP {exc.code}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", type=Path, default=Path.cwd())
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--online", action="store_true", help="perform a small GLM Responses API smoke test when GLM is enabled")
    args = ap.parse_args()

    rc, root_s = run(["git", "rev-parse", "--show-toplevel"], args.cwd.resolve())
    if rc:
        print("Not inside a Git worktree.", file=sys.stderr)
        return 2
    root = Path(root_s)
    home = Path.home()
    cfgdir = Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config"))) / "sglang-workflow"
    models = read_env(cfgdir / "models.env")
    global_v = (cfgdir / "workflow-kit-version").read_text().strip() if (cfgdir / "workflow-kit-version").is_file() else ""
    ws_v = (root / ".agents/.workflow-kit-version").read_text().strip() if (root / ".agents/.workflow-kit-version").is_file() else ""
    ignore_rc, ignore_out = run(["git", "check-ignore", "-v", ".codex-artifacts/"], root)

    glm_enabled = models.get("AI_GLM_ENABLED", "0").lower() in {"1", "true", "yes", "on"}
    region = models.get("AI_GLM_REGION", "china")
    effort_profiles = [home / ".codex" / f"glm-{region}-{effort}.config.toml" for effort in ("low", "high", "max")]
    external = {}
    for tier in ("local", "cheap", "strong"):
        prefix = f"AI_{tier.upper()}_"
        external[tier] = bool(models.get(prefix + "BASE_URL") and models.get(prefix + "MODEL"))

    hook_file = home / ".codex/hooks.json"
    commands = hook_commands(hook_file)
    budget_hook = any("post_tool_budget.py" in command for command in commands)
    session_hook = any("session_start.py" in command for command in commands)
    prompt_hook = any("prompt_guard.py" in command for command in commands)

    state_dir = root / ".codex-artifacts/session-budget"
    budget_states = len(list(state_dir.glob("*.json"))) if state_dir.is_dir() else 0
    stale_open = 0
    handoff_dir = root / ".codex-artifacts/handoffs"
    if handoff_dir.is_dir():
        for path in handoff_dir.glob("*.md"):
            head = path.read_text(encoding="utf-8", errors="replace")[:2000]
            if "status: open" in head:
                stale_open += 1

    checks = {
        "root": str(root),
        "versions": {"global": global_v or None, "workspace": ws_v or None, "in_sync": bool(global_v and ws_v and global_v == ws_v)},
        "artifact_dir_git_ignored": ignore_rc == 0,
        "artifact_ignore_rule": ignore_out if ignore_rc == 0 else "",
        "codex_available": shutil.which("codex") is not None,
        "opencode_available": shutil.which("opencode") is not None,
        "semble_available": shutil.which("semble") is not None,
        "primary_harness": models.get("AI_PRIMARY_HARNESS", "codex"),
        "codex_routing": models.get("AI_CODEX_ROUTING", "balanced"),
        "glm": {
            "enabled": glm_enabled, "region": region, "model": models.get("AI_GLM_MODEL", "glm-5.3"),
            "key_present": bool(models.get("AI_GLM_API_KEY")), "catalog_exists": (home / ".codex/models.glm.json").is_file(),
            "profiles_exist": all(path.is_file() for path in effort_profiles),
        },
        "external_tiers": external,
        "skills_lock_exists": (cfgdir / "skills.lock.json").is_file(),
        "skills_snapshot_exists": (root / ".agents/.skills-resolved.json").is_file(),
        "skills_index_exists": (root / ".agents/.skills-index.json").is_file(),
        "hooks": {"file_exists": hook_file.is_file(), "session_start": session_hook, "prompt_guard": prompt_hook, "post_tool_budget": budget_hook},
        "session_budget_state_files": budget_states,
        "open_handoff_files": stale_open,
        "resolver_exists": (root / ".codex/scripts/resolve-handoff.py").is_file(),
        "review_packet_exists": (root / ".codex/scripts/workflow-review-packet.py").is_file(),
        "log_reducer_exists": (root / ".codex/scripts/extract-log-context.py").is_file(),
    }

    online_ok = True
    if args.online and glm_enabled:
        online_ok, detail = glm_smoke(models)
        checks["glm"]["online_smoke"] = {"ok": online_ok, "detail": detail}

    ok = checks["artifact_dir_git_ignored"] and checks["versions"]["in_sync"] and budget_hook and session_hook and prompt_hook
    if glm_enabled:
        ok = ok and checks["codex_available"] and checks["glm"]["key_present"] and checks["glm"]["catalog_exists"] and checks["glm"]["profiles_exist"] and online_ok

    if args.json:
        print(json.dumps(checks, indent=2, ensure_ascii=False))
    else:
        print(f"Workflow root: {root}")
        print(f"[{'OK' if checks['versions']['in_sync'] else 'WARN'}] workflow-kit version: global={global_v or 'unversioned'} workspace={ws_v or 'unversioned'}")
        print(f"[{'OK' if checks['artifact_dir_git_ignored'] else 'FAIL'}] .codex-artifacts/ is Git-ignored")
        print(f"[{'OK' if checks['codex_available'] else 'WARN'}] Codex executable")
        print(f"[{'OK' if budget_hook else 'FAIL'}] PostToolUse retrieval-budget hook")
        print(f"[{'OK' if checks['skills_snapshot_exists'] else 'INFO'}] external skill commit snapshot")
        print(f"[{'OK' if checks['skills_index_exists'] else 'INFO'}] generated skill index")
        print(f"Session budget state files: {budget_states}; open handoffs: {stale_open}")
        print(f"Semble: {'installed (optional)' if checks['semble_available'] else 'off (expected for Standard)'}")
        g = checks["glm"]
        print(f"GLM: {'enabled' if g['enabled'] else 'off'} region={g['region']} model={g['model']} key={'present' if g['key_present'] else 'missing'} profiles={'OK' if g['profiles_exist'] else 'missing'}")
        if args.online and glm_enabled:
            smoke = g["online_smoke"]
            print(f"[{'OK' if smoke['ok'] else 'FAIL'}] GLM online smoke: {smoke['detail']}")
        print("External tiers: " + ", ".join(f"{k}={'configured' if v else 'off'}" for k, v in external.items()))
        print("Hook trust is not changed by workflow-doctor; after hook changes review /hooks in Codex.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
