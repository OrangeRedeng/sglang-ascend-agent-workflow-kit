#!/usr/bin/env python3
"""Migrate legacy mutable .codex/{handoffs,goals,logs} into .codex-artifacts/."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import subprocess


def run(cmd: list[str], cwd: Path) -> str:
    try:
        return subprocess.check_output(cmd, cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def add_frontmatter(path: Path, root: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---\n"):
        return
    pr_match = re.match(r"pr-(\d+)-review\.md$", path.name)
    pr = pr_match.group(1) if pr_match else ""
    branch = run(["git", "branch", "--show-current"], root)
    repo = run(["git", "remote", "get-url", "origin"], root)
    head_match = re.search(r"^Reviewed HEAD:\s*(\S+)", text, re.M)
    head = head_match.group(1) if head_match else run(["git", "rev-parse", "HEAD"], root)
    created = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    meta = (
        "---\n"
        "schema: codex-sglang-handoff/v1\n"
        "status: open\n"
        f"kind: {'pr-review' if pr else 'investigation'}\n"
        f"pr: {pr}\n"
        f"branch: {branch}\n"
        f"repo: {repo}\n"
        f"worktree: {root}\n"
        "base_commit: \n"
        f"reviewed_head: {head}\n"
        f"created_at: {created}\n"
        "consumed_at: \n"
        "consumed_head: \n"
        "---\n\n"
    )
    path.write_text(meta + text, encoding="utf-8")


def copy_tree_contents(src: Path, dst: Path, skip_names: set[str] | None = None) -> int:
    if not src.is_dir():
        return 0
    skip_names = skip_names or set()
    count = 0
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in skip_names:
            continue
        target = dst / item.name
        if target.exists():
            # Keep the newer existing artifact rather than overwrite blindly.
            if item.is_file() and target.is_file() and item.stat().st_mtime > target.stat().st_mtime:
                shutil.copy2(item, target)
            continue
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
        count += 1
    return count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--remove-legacy", action="store_true")
    args = ap.parse_args()
    root = Path(run(["git", "rev-parse", "--show-toplevel"], args.root.resolve()) or args.root.resolve())
    target = root / ".codex-artifacts"
    (target / "handoffs").mkdir(parents=True, exist_ok=True)
    (target / "goals").mkdir(parents=True, exist_ok=True)
    (target / "logs").mkdir(parents=True, exist_ok=True)

    legacy_h = root / ".codex" / "handoffs"
    legacy_g = root / ".codex" / "goals"
    legacy_l = root / ".codex" / "logs"

    count = 0
    count += copy_tree_contents(legacy_h, target / "handoffs", {"TEMPLATE.md"})
    count += copy_tree_contents(legacy_g, target / "goals", {"TEMPLATE"})
    count += copy_tree_contents(legacy_l, target / "logs")

    for path in (target / "handoffs").glob("*.md"):
        add_frontmatter(path, root)

    if args.remove_legacy:
        for path in (legacy_h, legacy_g, legacy_l):
            if path.exists():
                shutil.rmtree(path)

    print(f"Artifact root: {target}")
    print(f"Migrated/copied entries: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
