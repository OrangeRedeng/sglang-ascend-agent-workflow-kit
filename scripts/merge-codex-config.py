#!/usr/bin/env python3
"""Safely add/remove workflow-owned Codex config fragments without replacing user config."""
from __future__ import annotations

import argparse
from pathlib import Path
import re

START = "# >>> sglang-ascend-workflow-kit managed >>>"
END = "# <<< sglang-ascend-workflow-kit managed <<<"


def remove_managed(text: str) -> str:
    pattern = re.compile(rf"\n?{re.escape(START)}.*?{re.escape(END)}\n?", re.S)
    return pattern.sub("\n", text).rstrip() + ("\n" if text.strip() else "")


def has_table(text: str, table: str) -> bool:
    return re.search(rf"(?m)^\s*\[{re.escape(table)}\]\s*$", text) is not None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--enable-semble", action="store_true")
    ap.add_argument("--semble-version", default="")
    args = ap.parse_args()

    path = args.config.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    text = remove_managed(original)

    blocks: list[str] = []
    if args.enable_semble and not has_table(text, "mcp_servers.semble"):
        package = "semble[mcp]"
        if args.semble_version:
            package += f"=={args.semble_version}"
        blocks += [
            "[mcp_servers.semble]",
            'command = "uvx"',
            f'args = ["--from", "{package}", "semble"]',
            "enabled = true",
            "startup_timeout_sec = 120",
        ]

    if blocks:
        managed = START + "\n" + "\n".join(blocks) + "\n" + END + "\n"
        text = text.rstrip() + ("\n\n" if text.strip() else "") + managed

    # Preserve byte-for-byte user content whenever no managed change is needed.
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"Updated Codex config non-destructively: {path}")
    else:
        print(f"Preserved Codex config: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
