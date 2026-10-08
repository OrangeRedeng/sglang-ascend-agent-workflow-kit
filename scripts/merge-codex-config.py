#!/usr/bin/env python3
"""Remove workflow-kit managed Codex fragments while preserving user configuration."""
from __future__ import annotations

import argparse
from pathlib import Path
import re

START = "# >>> sglang-ascend-workflow-kit managed >>>"
END = "# <<< sglang-ascend-workflow-kit managed <<<"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    args = ap.parse_args()
    path = args.config.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(rf"\n?{re.escape(START)}.*?{re.escape(END)}\n?", re.S)
    text = pattern.sub("\n", original)
    if text != original:
        path.write_text(text.rstrip() + ("\n" if text.strip() else ""), encoding="utf-8")
        print(f"Removed legacy workflow-managed Codex block: {path}")
    else:
        print(f"Preserved Codex config: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
