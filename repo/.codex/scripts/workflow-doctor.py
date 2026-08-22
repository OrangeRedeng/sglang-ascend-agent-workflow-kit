#!/usr/bin/env python3
"""Check the local SGLang multi-model workflow installation.

The doctor also reports OpenCode/router configuration without printing API keys.
It never grants hook trust. When a local Codex binary is available it asks
Codex itself for `hooks/list`, which exposes each hook's current hash and effective
trust status. If runtime inspection is unavailable, it falls back to reporting only
whether a stored trust entry exists and explicitly marks that result as unverified.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import select
import shutil
import subprocess
import sys
import time
import tomllib
from typing import Any

EXPECTED_EVENTS = {
    "session_start": "SessionStart",
    "user_prompt_submit": "UserPromptSubmit",
}


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=5,
            check=False,
        )
        return p.returncode, p.stdout.strip()
    except Exception as exc:
        return 1, str(exc)


def git_root(start: Path) -> Path | None:
    rc, out = run(["git", "rev-parse", "--show-toplevel"], start)
    return Path(out).resolve() if rc == 0 and out else None


def read_marker(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def stored_hook_trust(config_path: Path, hooks_path: Path) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    data: dict[str, Any] = {}
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    states = data.get("hooks", {}).get("state", {}) if isinstance(data, dict) else {}
    source = str(hooks_path.resolve())
    for event in EXPECTED_EVENTS:
        key = f"{source}:{event}:0:0"
        state = states.get(key, {}) if isinstance(states, dict) else {}
        trusted_hash = state.get("trusted_hash", "") if isinstance(state, dict) else ""
        enabled = not (isinstance(state, dict) and state.get("enabled") is False)
        result[event] = {
            "key": key,
            "stored_trusted_hash": trusted_hash or None,
            "trust_entry_present": bool(trusted_hash),
            "enabled_in_stored_state": enabled,
        }
    return result



def external_model_state() -> dict[str, object]:
    config = Path.home() / ".config" / "sglang-workflow" / "models.env"
    values: dict[str, str] = {}
    if config.is_file():
        for raw in config.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    tiers: dict[str, dict[str, object]] = {}
    for tier in ("LOCAL", "CHEAP", "STRONG"):
        base = values.get(f"AI_{tier}_BASE_URL", "")
        model = values.get(f"AI_{tier}_MODEL", "")
        tiers[tier.lower()] = {
            "configured": bool(base and model),
            "base_url": base or None,
            "model": model or None,
        }
    return {
        "opencode_available": shutil.which("opencode") is not None,
        "project_config_exists": False,
        "models_env_exists": config.is_file(),
        "models_env_path": str(config),
        "primary_backend": values.get("AI_PRIMARY_BACKEND", "codex") or "codex",
        "routing_mode": values.get("AI_ROUTING_MODE", "primary") or "primary",
        "codex_fallback": values.get("AI_ENABLE_CODEX_FALLBACK", "0").lower() in {"1", "true", "yes", "on"},
        "tiers": tiers,
    }

def _send(proc: subprocess.Popen[str], payload: dict[str, object]) -> None:
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
    proc.stdin.flush()


def _read_response(proc: subprocess.Popen[str], request_id: int, timeout: float) -> dict[str, Any]:
    assert proc.stdout is not None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        remaining = max(0.0, deadline - time.monotonic())
        ready, _, _ = select.select([proc.stdout], [], [], remaining)
        if not ready:
            break
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                break
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if message.get("id") == request_id:
            return message
    raise TimeoutError(f"timed out waiting for Codex app-server response id={request_id}")


def query_runtime_hooks(root: Path, stored: dict[str, dict[str, object]]) -> dict[str, object]:
    codex = shutil.which("codex")
    if not codex:
        return {"available": False, "error": "codex binary not found", "events": {}}

    proc: subprocess.Popen[str] | None = None
    try:
        proc = subprocess.Popen(
            [codex, "app-server"],
            cwd=root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        _send(
            proc,
            {
                "method": "initialize",
                "id": 1,
                "params": {
                    "clientInfo": {
                        "name": "workflow-doctor",
                        "title": "Workflow Doctor",
                        "version": read_marker(root / ".codex" / "KIT_VERSION") or "unknown",
                    }
                },
            },
        )
        init = _read_response(proc, 1, 8.0)
        if "error" in init:
            raise RuntimeError(f"initialize failed: {init['error']}")
        _send(proc, {"method": "initialized"})
        _send(proc, {"method": "hooks/list", "id": 2, "params": {"cwds": [str(root)]}})
        response = _read_response(proc, 2, 8.0)
        if "error" in response:
            raise RuntimeError(f"hooks/list failed: {response['error']}")

        result = response.get("result", {})
        entries = result.get("data", []) if isinstance(result, dict) else []
        hooks: list[dict[str, Any]] = []
        for entry in entries if isinstance(entries, list) else []:
            if not isinstance(entry, dict):
                continue
            entry_cwd = Path(str(entry.get("cwd", root))).expanduser()
            try:
                entry_matches = entry_cwd.resolve() == root
            except OSError:
                entry_matches = str(entry_cwd) == str(root)
            if entry_matches:
                raw_hooks = entry.get("hooks", [])
                if isinstance(raw_hooks, list):
                    hooks.extend(h for h in raw_hooks if isinstance(h, dict))

        events: dict[str, dict[str, object]] = {}
        for event, expected_name in EXPECTED_EVENTS.items():
            expected_key = str(stored[event]["key"])
            hook = next((h for h in hooks if h.get("key") == expected_key), None)
            if hook is None:
                hook = next(
                    (
                        h for h in hooks
                        if str(h.get("eventName", "")).lower() == expected_name.lower()
                        and str(h.get("sourcePath", "")).endswith("/.codex/hooks.json")
                    ),
                    None,
                )
            if hook is None:
                events[event] = {
                    "found": False,
                    "enabled": False,
                    "trust_status": "Missing",
                    "current_hash": None,
                    "stored_hash_matches_current": False,
                }
                continue

            current_hash = hook.get("currentHash") or hook.get("current_hash")
            trust_status = str(hook.get("trustStatus") or hook.get("trust_status") or "Unknown")
            enabled = bool(hook.get("enabled", True))
            stored_hash = stored[event].get("stored_trusted_hash")
            events[event] = {
                "found": True,
                "enabled": enabled,
                "trust_status": trust_status,
                "current_hash": current_hash,
                "stored_hash_matches_current": bool(current_hash and stored_hash == current_hash),
            }
        return {"available": True, "error": None, "events": events}
    except Exception as exc:
        return {"available": False, "error": str(exc), "events": {}}
    finally:
        if proc is not None:
            try:
                if proc.stdin:
                    proc.stdin.close()
                proc.terminate()
                proc.wait(timeout=1)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", type=Path, default=Path.cwd())
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = git_root(args.cwd.resolve())
    if root is None:
        print("Not inside a Git worktree.", file=sys.stderr)
        return 2

    codex_home = Path.home() / ".codex"
    hooks_path = codex_home / "hooks.json"
    config_path = codex_home / "config.toml"

    global_version = read_marker(Path.home() / ".config" / "sglang-workflow" / "workflow-kit-version")
    if not global_version:
        global_version = read_marker(codex_home / "workflow-kit-version")
    workspace_version = read_marker(root / ".agents" / ".workflow-kit-version")
    if not workspace_version:
        workspace_version = read_marker(root / ".codex" / "KIT_VERSION")

    external = external_model_state()
    primary_backend = str(external.get("primary_backend", "codex"))
    codex_installed = shutil.which("codex") is not None and config_path.is_file()
    codex_expected = primary_backend == "codex" or codex_installed

    checks: dict[str, object] = {
        "root": str(root),
        "artifact_dir_exists": (root / ".codex-artifacts").is_dir(),
        "hooks_json_exists": hooks_path.is_file(),
        "config_exists": config_path.is_file(),
        "codex_installed": codex_installed,
        "codex_expected": codex_expected,
        "versions": {
            "global": global_version or None,
            "workspace": workspace_version or None,
            "in_sync": bool(global_version and workspace_version and global_version == workspace_version),
        },
    }
    external["project_config_exists"] = (root / "opencode.json").is_file()
    checks["external_models"] = external

    rc, ignored_out = run(["git", "check-ignore", "-v", ".codex-artifacts/"], root)
    checks["artifact_dir_git_ignored"] = rc == 0
    checks["artifact_ignore_rule"] = ignored_out if rc == 0 else ""

    stored = stored_hook_trust(config_path, hooks_path) if codex_expected else {}
    checks["hook_trust_stored"] = stored
    runtime = query_runtime_hooks(root, stored) if codex_expected else {"available": False, "error": "Codex not selected/installed", "events": {}}
    checks["hook_runtime"] = runtime

    resolver = root / ".codex" / "scripts" / "resolve-handoff.py"
    if resolver.is_file():
        rc, out = run([sys.executable, str(resolver), "--cwd", str(root), "--json", "--no-gh"], root)
        try:
            checks["handoff_resolver"] = json.loads(out)
        except Exception:
            checks["handoff_resolver"] = {"error": out, "exit_code": rc}
    else:
        checks["handoff_resolver"] = {"error": "resolver missing"}

    if args.json:
        print(json.dumps(checks, ensure_ascii=False, indent=2))
    else:
        print(f"Workflow root: {root}")
        versions = checks["versions"]
        version_ok = bool(versions["in_sync"])
        print(
            f"[{'OK' if version_ok else 'WARN'}] workflow-kit version: "
            f"global={versions['global'] or 'unversioned'}, "
            f"workspace={versions['workspace'] or 'unversioned'}"
        )
        print(f"[{'OK' if checks['artifact_dir_git_ignored'] else 'FAIL'}] .codex-artifacts/ is Git-ignored")
        if codex_expected:
            print(f"[{'OK' if checks['hooks_json_exists'] else 'FAIL'}] ~/.codex/hooks.json exists")
            print(f"[{'OK' if checks['config_exists'] else 'FAIL'}] ~/.codex/config.toml exists")
        else:
            print("[OK] Codex-specific global config not required for the selected primary backend")
        external_state = checks["external_models"]
        assert isinstance(external_state, dict)
        print(f"Primary backend: {external_state.get('primary_backend')} | routing: {external_state.get('routing_mode')}")
        external_needed = external_state.get('primary_backend') in {'local', 'cheap', 'strong'} or any(
            isinstance(v, dict) and v.get('configured') for v in external_state.get('tiers', {}).values()
        )
        print(f"[{'OK' if external_state['project_config_exists'] else 'WARN'}] opencode.json exists in worktree")
        marker = 'OK' if external_state['opencode_available'] else ('FAIL' if external_needed else 'INFO')
        print(f"[{marker}] OpenCode executable {'available' if external_state['opencode_available'] else 'not installed'}")
        tiers = external_state.get("tiers", {})
        assert isinstance(tiers, dict)
        tier_summary = ", ".join(
            f"{name}={'configured' if isinstance(state, dict) and state.get('configured') else 'off'}"
            for name, state in tiers.items()
        )
        print(f"External tiers: {tier_summary}")
        if not external_state.get("models_env_exists"):
            print(f"[WARN] external model config missing: {external_state['models_env_path']}")

        if codex_expected and runtime["available"]:
            runtime_events = runtime["events"]
            assert isinstance(runtime_events, dict)
            for event in EXPECTED_EVENTS:
                state = runtime_events.get(event, {})
                assert isinstance(state, dict)
                status = str(state.get("trust_status", "Unknown"))
                status_display = status[:1].upper() + status[1:] if status else "Unknown"
                enabled = bool(state.get("enabled", False))
                trusted = status.lower() in {"trusted", "managed"}
                marker = "OK" if trusted and enabled else "WARN"
                detail = f"{status_display}, {'enabled' if enabled else 'disabled'}"
                if status.lower() == "modified":
                    detail += "; current hook hash differs from the trusted hash"
                print(f"[{marker}] {event}: {detail}")
        elif codex_expected:
            print(f"[WARN] Codex runtime hook inspection unavailable: {runtime['error']}")
            for event, state in stored.items():
                stored_status = "stored trust entry present" if state["trust_entry_present"] else "no stored trust entry"
                enabled = "enabled in stored state" if state["enabled_in_stored_state"] else "disabled in stored state"
                print(f"[WARN] {event}: {stored_status}, {enabled}; current hash NOT verified")
            print("       Run /hooks in Codex for authoritative trust status.")

        resolver_state = checks.get("handoff_resolver", {})
        if isinstance(resolver_state, dict):
            print(f"Handoff resolver: {resolver_state.get('confidence', 'unknown')} - {resolver_state.get('reason', '')}")
            for stale in resolver_state.get("stale_candidates", [])[:5]:
                print(f"  stale: {stale.get('path')} ({', '.join(stale.get('reasons', []))})")

        if codex_expected and runtime["available"]:
            runtime_events = runtime["events"]
            assert isinstance(runtime_events, dict)
            needs_review = any(
                not (
                    str(runtime_events.get(event, {}).get("trust_status", "")).lower() in {"trusted", "managed"}
                    and bool(runtime_events.get(event, {}).get("enabled", False))
                )
                for event in EXPECTED_EVENTS
            )
            if needs_review:
                print("\nHook trust is intentionally not changed by this script.")
                print("Open Codex CLI in this worktree, run /hooks, and approve/enable both SessionStart and UserPromptSubmit.")
                print("Then reload the VS Code WSL window and start a new Codex session.")

    structural_ok = bool(
        checks["artifact_dir_git_ignored"]
        and checks["versions"]["in_sync"]
        and (not codex_expected or (checks["hooks_json_exists"] and checks["config_exists"]))
    )
    runtime_ok = True
    if codex_expected and runtime["available"]:
        runtime_events = runtime["events"]
        assert isinstance(runtime_events, dict)
        runtime_ok = all(
            str(runtime_events.get(event, {}).get("trust_status", "")).lower() in {"trusted", "managed"}
            and bool(runtime_events.get(event, {}).get("enabled", False))
            for event in EXPECTED_EVENTS
        )
    return 0 if structural_ok and runtime_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
