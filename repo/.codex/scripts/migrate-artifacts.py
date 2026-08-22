#!/usr/bin/env python3
"""Migrate legacy mutable .codex/{handoffs,goals,logs} into .codex-artifacts/.

Also upgrades handoff front matter to v2 fields used by topic/freshness-aware discovery.
"""
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
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    if end is None:
        return {}, text
    return meta, "\n".join(lines[end + 1:]).lstrip("\n") + "\n"


def topic_from_name(name: str) -> str:
    stem = re.sub(r"\.md$", "", name, flags=re.I)
    return re.sub(r"^pr-\d+-", "", stem, flags=re.I) or "review"


def is_handoff_template(path: Path) -> bool:
    """Runtime handoff storage must never contain template markdown files."""
    return bool(re.match(r"^TEMPLATE(?:[-_.].*)?\.md$", path.name, re.I))


def render(meta: dict[str, str], body: str) -> str:
    preferred = [
        "schema", "status", "kind", "pr", "branch", "repo", "worktree",
        "topic", "scope", "objective", "base_commit", "reviewed_head", "created_at",
        "consumed_at", "consumed_head",
    ]
    keys = preferred + [k for k in meta if k not in preferred]
    out = ["---"]
    seen: set[str] = set()
    for key in keys:
        if key in seen or key not in meta:
            continue
        seen.add(key)
        out.append(f"{key}: {meta[key]}")
    out.extend(["---", "", body.rstrip(), ""])
    return "\n".join(out)


def upgrade_frontmatter(path: Path, root: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    meta, body = split_frontmatter(text)
    branch = run(["git", "branch", "--show-current"], root)
    repo = run(["git", "remote", "get-url", "origin"], root)

    pr_match = re.match(r"pr-(\d+)-(.+)\.md$", path.name)
    filename_pr = pr_match.group(1) if pr_match else ""
    topic = topic_from_name(path.name)

    if not meta:
        head_match = re.search(r"^Reviewed HEAD:\s*(\S+)", text, re.M)
        head = head_match.group(1) if head_match else run(["git", "rev-parse", "HEAD"], root)
        created = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        meta = {
            "schema": "codex-sglang-handoff/v2",
            "status": "open",
            "kind": "pr-review" if filename_pr else "investigation",
            "pr": filename_pr,
            "branch": branch,
            "repo": repo,
            "worktree": str(root),
            "topic": topic,
            "scope": "",
            "objective": "",
            "base_commit": "",
            "reviewed_head": head,
            "created_at": created,
            "consumed_at": "",
            "consumed_head": "",
        }
    else:
        meta["schema"] = "codex-sglang-handoff/v2"
        meta.setdefault("status", "open")
        meta.setdefault("kind", "pr-review" if filename_pr else "investigation")
        meta.setdefault("pr", filename_pr)
        meta.setdefault("branch", branch)
        meta.setdefault("repo", repo)
        meta.setdefault("worktree", str(root))
        meta.setdefault("topic", topic)
        meta.setdefault("scope", "")
        meta.setdefault("objective", "")
        meta.setdefault("base_commit", "")
        meta.setdefault("reviewed_head", "")
        meta.setdefault("created_at", "")
        meta.setdefault("consumed_at", "")
        meta.setdefault("consumed_head", "")

    path.write_text(render(meta, body), encoding="utf-8")


def copy_tree_contents(src: Path, dst: Path, skip_names: set[str] | None = None) -> int:
    if not src.is_dir():
        return 0
    skip_names = skip_names or set()
    count = 0
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in skip_names or (item.is_file() and is_handoff_template(item)):
            continue
        target = dst / item.name
        if target.exists():
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
    count += copy_tree_contents(legacy_h, target / "handoffs", {"TEMPLATE.md", "TEMPLATE-review.md"})
    count += copy_tree_contents(legacy_g, target / "goals", {"TEMPLATE"})
    count += copy_tree_contents(legacy_l, target / "logs")

    upgraded = 0
    for path in (target / "handoffs").glob("*.md"):
        if is_handoff_template(path):
            continue
        before = path.read_text(encoding="utf-8", errors="replace")
        upgrade_frontmatter(path, root)
        if path.read_text(encoding="utf-8", errors="replace") != before:
            upgraded += 1

    if args.remove_legacy:
        for path in (legacy_h, legacy_g, legacy_l):
            if path.exists():
                shutil.rmtree(path)

    print(f"Artifact root: {target}")
    print(f"Migrated/copied entries: {count}")
    print(f"Upgraded handoffs to v2 metadata: {upgraded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
