#!/usr/bin/env python3
"""Change handoff lifecycle metadata without altering the handoff body."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head(path: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path.parent,
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    meta: dict[str, str] = {}
    end = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    if end is None:
        return {}, text
    return meta, "\n".join(lines[end + 1:]).lstrip("\n") + "\n"


def render(meta: dict[str, str], body: str) -> str:
    preferred = [
        "schema", "status", "kind", "pr", "branch", "repo", "worktree",
        "base_commit", "reviewed_head", "created_at", "consumed_at", "consumed_head",
    ]
    keys = preferred + [k for k in meta if k not in preferred]
    out = ["---"]
    seen = set()
    for key in keys:
        if key in seen or key not in meta:
            continue
        seen.add(key)
        value = meta[key]
        out.append(f"{key}: {value}")
    out.extend(["---", "", body.rstrip(), ""])
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["consume", "reopen"])
    ap.add_argument("handoff", type=Path)
    args = ap.parse_args()

    path = args.handoff.expanduser().resolve()
    if not path.is_file():
        ap.error(f"handoff not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    meta, body = split_frontmatter(text)
    meta.setdefault("schema", "codex-sglang-handoff/v1")

    if args.action == "consume":
        meta["status"] = "consumed"
        meta["consumed_at"] = now()
        meta["consumed_head"] = git_head(path)
    else:
        meta["status"] = "open"
        meta["consumed_at"] = ""
        meta["consumed_head"] = ""

    path.write_text(render(meta, body), encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
