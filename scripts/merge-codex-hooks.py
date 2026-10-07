#!/usr/bin/env python3
"""Merge workflow hooks into ~/.codex/hooks.json while preserving unrelated user hooks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

KIT_COMMAND_MARKERS = (
    '"$HOME/.codex/hooks/session_start.py"',
    '"$HOME/.codex/hooks/prompt_guard.py"',
    '"$HOME/.codex/hooks/post_tool_budget.py"',
)


def is_kit_group(group: object) -> bool:
    if not isinstance(group, dict):
        return False
    for hook in group.get("hooks", []):
        if isinstance(hook, dict):
            cmd = str(hook.get("command", ""))
            if any(marker in cmd for marker in KIT_COMMAND_MARKERS):
                return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path)
    ap.add_argument("kit", type=Path)
    args = ap.parse_args()

    target = args.target.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except Exception as exc:
            raise SystemExit(f"Refusing to overwrite invalid existing hooks JSON {target}: {exc}")
    kit = json.loads(args.kit.read_text(encoding="utf-8"))

    out = dict(existing)
    hooks = out.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit(f"Existing hooks field is not an object: {target}")

    for event, kit_groups in kit.get("hooks", {}).items():
        current = hooks.get(event, [])
        if not isinstance(current, list):
            raise SystemExit(f"Existing hook event {event} is not an array: {target}")
        kept = [group for group in current if not is_kit_group(group)]
        hooks[event] = kept + kit_groups

    if "description" not in out:
        out["description"] = kit.get("description", "SGLang Ascend workflow hooks")
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Merged Codex hooks: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
