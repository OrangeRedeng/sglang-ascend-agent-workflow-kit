#!/usr/bin/env python3
"""Resolve the most applicable open Codex handoff for the current Git worktree.

Resolution order:
1. exact current PR number;
2. exact current branch;
3. newest unconsumed handoff created for the same worktree;
4. if exactly one open handoff exists for the same repository, use it.

The script is intentionally dependency-free so hooks can call it cheaply.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone


def run(cmd: list[str], cwd: Path, timeout: float = 2.0) -> str:
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=timeout, check=False)
    except Exception:
        return ""
    return p.stdout.strip() if p.returncode == 0 else ""


def git_root(start: Path) -> Path | None:
    out = run(["git", "rev-parse", "--show-toplevel"], start)
    return Path(out).resolve() if out else None


def metadata(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def infer_pr(branch: str, root: Path, allow_gh: bool) -> str:
    # Common local branch forms: pr/owner/34855, pr-34855, issue/34855.
    m = re.search(r"(?:^|[/_-])(?:pr[/_-]?)?(\d{3,})$", branch, re.I)
    if m:
        return m.group(1)
    if allow_gh and run(["which", "gh"], root):
        return run(["gh", "pr", "view", "--json", "number", "--jq", ".number"], root, timeout=3.0)
    return ""


def parse_time(value: str, fallback: float) -> float:
    if value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    return fallback


def candidate_record(path: Path, root: Path) -> dict[str, object]:
    md = metadata(path)
    name = path.name
    if not md:
        m = re.match(r"pr-(\d+)-review\.md$", name)
        md = {
            "schema": "legacy",
            "status": "open",
            "kind": "pr-review" if m else "investigation",
            "pr": m.group(1) if m else "",
            "branch": "",
            "repo": "",
            "worktree": str(root),
            "created_at": "",
            "reviewed_head": "",
        }
    stat = path.stat()
    return {
        "path": str(path),
        "status": md.get("status", "open").lower(),
        "kind": md.get("kind", ""),
        "pr": md.get("pr", "").lstrip("#"),
        "branch": md.get("branch", ""),
        "repo": md.get("repo", ""),
        "worktree": md.get("worktree", ""),
        "created_at": md.get("created_at", ""),
        "reviewed_head": md.get("reviewed_head", ""),
        "mtime": stat.st_mtime,
    }


def resolve(root: Path, allow_gh: bool = True) -> dict[str, object]:
    artifact_dir = root / ".codex-artifacts" / "handoffs"
    branch = run(["git", "branch", "--show-current"], root)
    head = run(["git", "rev-parse", "HEAD"], root)
    repo = run(["git", "remote", "get-url", "origin"], root)
    pr = infer_pr(branch, root, allow_gh)

    result: dict[str, object] = {
        "root": str(root), "branch": branch, "head": head, "repo": repo, "pr": pr,
        "selected": None, "reason": "none", "confidence": "none", "candidates": [],
    }
    if not artifact_dir.is_dir():
        return result

    candidates = []
    for path in sorted(artifact_dir.glob("*.md")):
        rec = candidate_record(path, root)
        if rec["status"] != "open":
            continue
        # Handoffs from another repository are never fallback candidates.
        if rec["repo"] and repo and rec["repo"] != repo:
            continue
        candidates.append(rec)
    result["candidates"] = [c["path"] for c in candidates]
    if not candidates:
        return result

    if pr:
        exact = [c for c in candidates if str(c["pr"]) == pr]
        if exact:
            exact.sort(key=lambda c: parse_time(str(c["created_at"]), float(c["mtime"])), reverse=True)
            result.update(selected=exact[0]["path"], reason=f"current PR #{pr}", confidence="exact-pr")
            return result

    if branch:
        exact = [c for c in candidates if c["branch"] == branch]
        if exact:
            exact.sort(key=lambda c: parse_time(str(c["created_at"]), float(c["mtime"])), reverse=True)
            result.update(selected=exact[0]["path"], reason=f"current branch {branch}", confidence="exact-branch")
            return result

    same_worktree = [c for c in candidates if c["worktree"] and Path(str(c["worktree"])).resolve() == root]
    if same_worktree:
        same_worktree.sort(key=lambda c: parse_time(str(c["created_at"]), float(c["mtime"])), reverse=True)
        result.update(selected=same_worktree[0]["path"], reason="newest open handoff for this worktree", confidence="worktree-fallback")
        return result

    if len(candidates) == 1:
        result.update(selected=candidates[0]["path"], reason="only open handoff for this repository", confidence="single-repo-fallback")
        return result

    result["reason"] = "multiple open handoffs; no safe exact match"
    result["confidence"] = "ambiguous"
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", type=Path, default=Path.cwd())
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-gh", action="store_true", help="skip optional GitHub PR lookup")
    args = ap.parse_args()

    root = git_root(args.cwd.resolve())
    if root is None:
        payload = {"selected": None, "reason": "not a git worktree", "confidence": "none", "candidates": []}
        if args.json:
            print(json.dumps(payload))
        return 1

    payload = resolve(root, allow_gh=not args.no_gh)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    elif payload["selected"]:
        print(payload["selected"])
    elif payload["confidence"] == "ambiguous":
        print("No unique handoff match.", file=sys.stderr)
        for item in payload["candidates"]:
            print(f"- {item}", file=sys.stderr)
    return 0 if payload["selected"] else (2 if payload["confidence"] == "ambiguous" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
