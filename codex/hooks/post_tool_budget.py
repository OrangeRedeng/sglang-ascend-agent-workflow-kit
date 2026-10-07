#!/usr/bin/env python3
"""Codex PostToolUse governor based on measured SGLang session behavior.

It never blocks a completed tool call. It records lightweight per-session state and
injects concise guidance only at evidence-based thresholds or first duplicate reads.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

SOFT_DEFAULT = 32
CHECKPOINT_DEFAULT = 44


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_root(cwd: Path) -> Path | None:
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=cwd, text=True, stderr=subprocess.DEVNULL
        ).strip()
        return Path(value).resolve() if value else None
    except Exception:
        return None


def state_path(root: Path | None, session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", session_id)[:160] or "unknown"
    if root:
        base = root / ".codex-artifacts" / "session-budget"
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "sglang-workflow" / "session-budget"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{safe}.json"


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def atomic_write(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def command_text(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "path", "file_path"):
            if key in tool_input:
                return str(tool_input[key])
        return json.dumps(tool_input, sort_keys=True)
    return str(tool_input or "")


def referenced_paths(command: str, kind: str) -> list[str]:
    if kind == "skill":
        rx = r"(?:^|[\s'\"])([^\s'\"]*SKILL\.md)(?=$|[\s'\"])"
    else:
        rx = r"(?:^|[\s'\"])([^\s'\"]*(?:handoffs?/[^\s'\"]+\.md|pr-\d+[^\s'\"]*\.md))(?=$|[\s'\"])"
    return sorted(set(re.findall(rx, command, flags=re.I)))


def file_identity(item: str, cwd: Path, root: Path | None) -> tuple[str, str]:
    raw = Path(item).expanduser()
    candidates = [raw] if raw.is_absolute() else [cwd / raw] + ([root / raw] if root else [])
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
            if resolved.is_file() and resolved.stat().st_size <= 2 * 1024 * 1024:
                digest = hashlib.sha1(resolved.read_bytes()).hexdigest()[:12]
                return str(resolved), digest
        except Exception:
            pass
    return item, "unknown"


def is_read_command(command: str) -> bool:
    return bool(re.search(r"(?:^|[;&|]\s*|\b)(?:cat|sed|head|tail|less|python3?)\b", command))


def active_goal(root: Path | None) -> bool:
    if not root:
        return False
    goals = root / ".codex-artifacts" / "goals"
    if not goals.is_dir():
        return False
    for goal in goals.iterdir():
        if goal.is_dir() and (goal / "goal.md").is_file():
            # Any explicit active marker wins. Legacy goals without markers are not assumed active.
            if (goal / ".active").exists():
                return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    session_id = str(payload.get("session_id") or "unknown")
    cwd = Path(str(payload.get("cwd") or os.getcwd())).expanduser()
    root = git_root(cwd)
    path = state_path(root, session_id)
    state = load(path)
    state.setdefault("schema", "sglang-workflow-session-budget/v1")
    state.setdefault("session_id", session_id)
    state.setdefault("created_at", now())
    state["updated_at"] = now()
    state["calls"] = int(state.get("calls", 0)) + 1
    tool = str(payload.get("tool_name") or "unknown")
    by_tool = state.setdefault("by_tool", {})
    by_tool[tool] = int(by_tool.get(tool, 0)) + 1

    command = command_text(payload)
    messages: list[str] = []

    if is_read_command(command):
        for category in ("skill", "handoff"):
            store = state.setdefault(f"{category}_reads", {})
            warned = state.setdefault(f"{category}_duplicate_warned", {})
            for item in referenced_paths(command, category):
                resolved, version = file_identity(item, cwd, root)
                identity = hashlib.sha1(f"{resolved}|{version}".encode("utf-8")).hexdigest()[:12]
                count = int(store.get(identity, 0)) + 1
                store[identity] = count
                if count == 2 and not warned.get(identity):
                    warned[identity] = True
                    messages.append(
                        f"Retrieval budget: unchanged {category} file appears to be read again in this session ({resolved}, hash {version}). "
                        "Reuse the earlier extracted facts unless a specific missing section is required."
                    )

    if re.search(r"\bgit\s+diff\b[^\n]*(?:--unified=(?:[5-9]\d|\d{3,})|-U(?:[5-9]\d|\d{3,}))", command):
        state["large_diff_attempts"] = int(state.get("large_diff_attempts", 0)) + 1
        messages.append(
            "Retrieval budget: avoid a broad high-context diff. Start from changed filenames/stat and inspect bounded component hunks (~20–30 lines), expanding only suspicious regions."
        )

    if re.search(r"\b(?:cat|less)\s+[^;&|\n]*\.log\b", command, re.I):
        state["raw_log_attempts"] = int(state.get("raw_log_attempts", 0)) + 1
        messages.append(
            "Large-log policy reminder: check size first; for >=1 MiB or >=10,000 lines run .codex/scripts/extract-log-context.py before reading raw log content."
        )

    soft = int(os.environ.get("SGLANG_WORKFLOW_TOOL_SOFT_LIMIT", SOFT_DEFAULT))
    checkpoint = int(os.environ.get("SGLANG_WORKFLOW_TOOL_CHECKPOINT_LIMIT", CHECKPOINT_DEFAULT))
    calls = int(state["calls"])
    if calls >= soft and not state.get("soft_warned"):
        state["soft_warned"] = True
        messages.append(
            f"Session retrieval budget reached {calls} tool calls. Consolidate findings now: stop broad discovery, reuse already-read evidence, and finish the current bounded objective with minimal additional retrieval."
        )
    if calls >= checkpoint and not state.get("checkpoint_warned"):
        state["checkpoint_warned"] = True
        if active_goal(root):
            messages.append(
                f"Session checkpoint at {calls} tool calls. This worktree has an active Goal: persist the current hypothesis, exact command/result, decision and next step to the Goal ledger, then prefer a new Codex session for the next experiment round."
            )
        else:
            messages.append(
                f"Session checkpoint at {calls} tool calls. If the objective is not already complete, write/update a compact handoff and continue the same strategy in a new session. Do not start another broad exploration cycle here."
            )

    atomic_write(path, state)
    if messages:
        print(json.dumps({"systemMessage": "\n\n".join(messages)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
