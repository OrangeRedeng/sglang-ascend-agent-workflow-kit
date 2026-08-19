#!/usr/bin/env python3
"""Codex UserPromptSubmit guard for high-cost trivial control turns."""

from __future__ import annotations

import json
import re
import sys


def normalize(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[.!]+$", "", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    prompt = normalize(str(payload.get("prompt", "")))
    blocked = {
        "push",
        "git push",
        "push it",
        "push this",
        "push it please",
        "please push",
    }

    if prompt in blocked:
        print(json.dumps({
            "decision": "block",
            "reason": (
                "Use the terminal directly for git push; do not spend a Codex turn "
                "on a pure push. If you actually need reasoning before pushing, rewrite "
                "the prompt to describe the validation/decision required."
            ),
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
