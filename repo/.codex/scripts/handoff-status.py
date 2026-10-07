#!/usr/bin/env python3
"""Manage handoff lifecycle, including stale archival/GC."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess


def now_dt() -> datetime:
    return datetime.now(timezone.utc)


def now() -> str:
    return now_dt().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_root_from(path: Path) -> Path | None:
    cwd = path if path.is_dir() else path.parent
    try:
        v = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
        return Path(v).resolve() if v else None
    except Exception:
        return None


def git_head(path: Path) -> str:
    root = git_root_from(path)
    if not root:
        return ""
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def split_frontmatter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    meta = {}
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
    return meta, "\n".join(lines[end + 1 :]).lstrip("\n") + "\n"


def render(meta: dict, body: str) -> str:
    preferred = [
        "schema", "status", "kind", "pr", "branch", "repo", "worktree", "topic", "scope", "objective",
        "base_commit", "reviewed_head", "producer", "consumer", "created_at", "consumed_at", "consumed_head",
        "archived_at", "archive_reason",
    ]
    out = ["---"]
    seen = set()
    for key in preferred + [k for k in meta if k not in preferred]:
        if key in seen or key not in meta:
            continue
        seen.add(key)
        out.append(f"{key}: {meta[key]}")
    out += ["---", "", body.rstrip(), ""]
    return "\n".join(out)


def pointer_path(root: Path, meta: dict) -> Path:
    pr = meta.get("pr", "").lstrip("#")
    return root / ".codex-artifacts" / "handoffs" / (f".active-pr-{pr}.json" if pr else ".active-worktree.json")


def set_pointer(root: Path, handoff: Path, meta: dict) -> None:
    p = pointer_path(root, meta)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "schema": "codex-sglang-active-handoff/v1",
        "path": str(handoff.resolve()), "pr": meta.get("pr", ""), "topic": meta.get("topic", ""),
        "branch": meta.get("branch", ""), "reviewed_head": meta.get("reviewed_head", ""),
        "created_at": meta.get("created_at", ""),
    }, indent=2) + "\n", encoding="utf-8")


def clear_pointer_if_matching(root: Path, handoff: Path, meta: dict) -> None:
    p = pointer_path(root, meta)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        selected = Path(str(data.get("path", ""))).expanduser().resolve()
    except Exception:
        return
    if selected == handoff.resolve():
        p.unlink(missing_ok=True)


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def archive(path: Path, reason: str) -> None:
    meta, body = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
    meta.setdefault("schema", "codex-sglang-handoff/v2")
    meta.setdefault("producer", "unknown")
    meta.setdefault("consumer", "codex")
    meta["status"] = "archived"
    meta["archived_at"] = now()
    meta["archive_reason"] = reason
    root = git_root_from(path)
    if root:
        clear_pointer_if_matching(root, path, meta)
    path.write_text(render(meta, body), encoding="utf-8")


def run_gc(root: Path, hours: float, dry_run: bool) -> int:
    directory = root / ".codex-artifacts" / "handoffs"
    if not directory.is_dir():
        print("No handoff directory.")
        return 0
    archived = 0
    skipped = 0
    cutoff = now_dt()
    for path in sorted(directory.glob("*.md")):
        meta, _ = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        if meta.get("status", "open").lower() != "open":
            continue
        created = parse_time(meta.get("created_at", ""))
        if created is None:
            skipped += 1
            continue
        age = (cutoff - created).total_seconds() / 3600
        if age <= hours:
            continue
        reason = f"stale-open>{hours:g}h"
        if dry_run:
            print(f"would archive: {path} age={age:.1f}h")
        else:
            archive(path, reason)
            print(f"archived: {path} age={age:.1f}h")
        archived += 1
    print(f"gc: archived={archived} skipped_unparseable={skipped} threshold={hours:g}h")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="action", required=True)
    for action in ("consume", "reopen", "archive"):
        p = sub.add_parser(action)
        p.add_argument("handoff", type=Path)
        if action == "archive":
            p.add_argument("--reason", default="manual")
    gc = sub.add_parser("gc")
    gc.add_argument("--older-than-hours", type=float, default=48.0)
    gc.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.action == "gc":
        root = git_root_from(Path.cwd())
        if not root:
            raise SystemExit("Not inside a Git worktree")
        return run_gc(root, args.older_than_hours, args.dry_run)

    path = args.handoff.expanduser().resolve()
    if not path.is_file():
        ap.error(f"handoff not found: {path}")
    meta, body = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
    meta.setdefault("schema", "codex-sglang-handoff/v2")
    meta.setdefault("producer", "unknown")
    meta.setdefault("consumer", "codex")
    root = git_root_from(path)

    if args.action == "consume":
        meta["status"] = "consumed"
        meta["consumed_at"] = now()
        meta["consumed_head"] = git_head(path)
        if root:
            clear_pointer_if_matching(root, path, meta)
    elif args.action == "reopen":
        meta["status"] = "open"
        meta["consumed_at"] = ""
        meta["consumed_head"] = ""
        meta["archived_at"] = ""
        meta["archive_reason"] = ""
        if root:
            set_pointer(root, path, meta)
    else:
        meta["status"] = "archived"
        meta["archived_at"] = now()
        meta["archive_reason"] = args.reason
        if root:
            clear_pointer_if_matching(root, path, meta)

    path.write_text(render(meta, body), encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
