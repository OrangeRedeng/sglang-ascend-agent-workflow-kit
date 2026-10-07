#!/usr/bin/env python3
"""Codex UserPromptSubmit guard and task-aware handoff injector."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys


def normalize(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[.!]+$", "", s).strip()
    return re.sub(r"\s+", " ", s)


def implementation_like(prompt: str) -> bool:
    positive = re.compile(
        r"\b(address|fix|implement|apply|patch|resolve|change|update|modify|port|remove|restore|"
        r"correct|handle|make|refactor|adapt|follow[- ]?up)\b",
        re.I,
    )
    report_only = re.compile(
        r"\b(review|analy[sz]e|investigate|report|summari[sz]e|explain|describe|triage)\b",
        re.I,
    )
    if re.search(r"\b(address|fix|implement|apply|patch|resolve)\b", prompt, re.I):
        return True
    return bool(positive.search(prompt)) and not bool(report_only.search(prompt))


def resolve(cwd: Path, prompt: str) -> dict | None:
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=cwd, text=True,
            stderr=subprocess.DEVNULL, timeout=2,
        ).strip()
    except Exception:
        return None
    script = Path(root) / ".codex" / "scripts" / "resolve-handoff.py"
    if not script.is_file():
        return None
    try:
        p = subprocess.run(
            [sys.executable, str(script), "--cwd", root, "--json", "--prompt", prompt],
            cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=5, check=False,
        )
        return json.loads(p.stdout) if p.stdout.strip() else None
    except Exception:
        return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    raw_prompt = str(payload.get("prompt", ""))
    prompt = normalize(raw_prompt)
    blocked = {"push", "git push", "push it", "push this", "push it please", "please push"}
    if prompt in blocked:
        print(json.dumps({"decision": "block", "reason": "Use the terminal directly for git push; do not spend a Codex turn on a pure push. If reasoning/validation is required before pushing, rewrite the prompt to describe it."}))
        return 0
    if not implementation_like(raw_prompt) or payload.get("agent_id"):
        return 0
    cwd = Path(str(payload.get("cwd") or ".")).expanduser()
    result = resolve(cwd, raw_prompt)
    if not result:
        return 0
    selected = result.get("selected")
    if selected:
        context = (
            f"Implementation preflight: handoff auto-discovery selected {selected} "
            f"({result.get('confidence')}: {result.get('reason')}). MUST read it before broad exploration, "
            "re-verify it against current HEAD, implement only applicable actionable items, and do not redo the broad review. "
            f"If all items are completed/obsolete, mark it consumed with `python3 .codex/scripts/handoff-status.py consume {selected}`. "
            "If this prompt is genuinely unrelated to that handoff, ignore it and continue normally."
        )
        print(json.dumps({"suppressOutput": True,"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":context}}))
    elif result.get("candidates") and (str(result.get("confidence", "")).startswith("ambiguous") or result.get("confidence") in {"topic-mismatch", "stale-only", "no-active-pointer"}):
        candidates = ", ".join(result.get("candidates", [])[:5])
        print(json.dumps({"suppressOutput":True,"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":f"Implementation preflight did not find a safe automatic handoff match ({result.get('confidence')}: {result.get('reason')}). Candidates: {candidates}. Do not consume a stale/unrelated handoff."}}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
