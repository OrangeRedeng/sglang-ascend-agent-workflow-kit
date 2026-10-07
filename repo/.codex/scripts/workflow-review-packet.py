#!/usr/bin/env python3
"""Build one bounded PR/review context packet to reduce iterative retrieval round trips."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess

DEFAULT_MAX_BYTES = 98304
DEFAULT_CONTEXT = 25


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return p.returncode, p.stdout


def git_root() -> Path:
    p = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL).strip()
    return Path(p).resolve()


def sanitize(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.") or "working-tree"


def changed_files(root: Path, base: str | None, pr: str | None) -> list[str]:
    if pr:
        rc, out = run(["gh", "pr", "diff", pr, "--name-only"], root)
        if rc == 0:
            return [x.strip() for x in out.splitlines() if x.strip()]
    cmd = ["git", "diff", "--name-only"]
    if base:
        cmd.append(f"{base}...HEAD")
    else:
        cmd.append("HEAD")
    rc, out = run(cmd, root)
    if rc != 0:
        raise SystemExit(out.strip() or "git diff --name-only failed")
    return [x.strip() for x in out.splitlines() if x.strip()]


def classify(path: str) -> str:
    p = path.lower()
    if "/npu/" in p or "ascend" in p or "torch_npu" in p:
        return "Ascend/NPU"
    if "kernel" in p or p.endswith((".cpp", ".cu", ".cuh")):
        return "kernel/native"
    if "test" in p or "/tests/" in p:
        return "tests"
    if p.endswith((".md", ".rst")) or "/docs/" in p:
        return "docs"
    if "/scheduler" in p or "scheduler" in p:
        return "scheduler/runtime"
    return "general"


def diff_for_file(root: Path, path: str, base: str | None, pr_patch: str | None, context: int) -> str:
    if pr_patch is not None:
        marker = f"diff --git a/{path} b/{path}"
        if marker not in pr_patch:
            return ""
        part = pr_patch.split(marker, 1)[1]
        part = marker + part
        next_idx = part.find("\ndiff --git ", len(marker))
        if next_idx >= 0:
            part = part[:next_idx]
        return part
    cmd = ["git", "diff", f"--unified={context}"]
    if base:
        cmd.append(f"{base}...HEAD")
    else:
        cmd.append("HEAD")
    cmd += ["--", path]
    return run(cmd, root)[1]


def append(out: list[str], text: str, max_bytes: int) -> bool:
    used = sum(len(x.encode("utf-8", "replace")) + 1 for x in out)
    size = len(text.encode("utf-8", "replace")) + 1
    if used + size > max_bytes:
        return False
    out.append(text)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="base ref, e.g. origin/main")
    ap.add_argument("--pr", help="GitHub PR number")
    ap.add_argument("--context", type=int, default=DEFAULT_CONTEXT)
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    root = git_root()
    files = changed_files(root, args.base, args.pr)
    ident = f"pr-{args.pr}" if args.pr else sanitize(args.base or "working-tree")
    output = args.output or root / ".codex-artifacts" / "reviews" / f"{ident}-packet.md"
    output.parent.mkdir(parents=True, exist_ok=True)

    stat_cmd = ["git", "diff", "--stat"]
    if args.base:
        stat_cmd.append(f"{args.base}...HEAD")
    else:
        stat_cmd.append("HEAD")
    stat = run(stat_cmd, root)[1].strip() if not args.pr else ""
    pr_patch = None
    if args.pr:
        rc, pr_patch = run(["gh", "pr", "diff", args.pr, "--patch"], root)
        if rc != 0:
            raise SystemExit(pr_patch.strip() or f"gh pr diff {args.pr} failed")

    groups: dict[str, list[str]] = {}
    for path in files:
        groups.setdefault(classify(path), []).append(path)

    out: list[str] = [
        f"# Review packet — {ident}",
        "",
        f"Repository: `{root}`",
        f"Changed files: {len(files)}",
        f"Diff context per hunk: {args.context}",
        f"Packet cap: {args.max_bytes} bytes",
        "",
        "## Changed components",
    ]
    for group, items in sorted(groups.items()):
        append(out, f"- **{group}**: {len(items)} file(s)", args.max_bytes)
        for path in items:
            append(out, f"  - `{path}`", args.max_bytes)

    if stat:
        append(out, "", args.max_bytes)
        append(out, "## Stat", args.max_bytes)
        append(out, "```text", args.max_bytes)
        for line in stat.splitlines():
            if not append(out, line, args.max_bytes):
                break
        append(out, "```", args.max_bytes)

    append(out, "", args.max_bytes)
    append(out, "## Bounded diffs", args.max_bytes)
    omitted: list[str] = []
    for path in files:
        patch = diff_for_file(root, path, args.base, pr_patch, max(0, args.context)).strip()
        if not patch:
            continue
        if not append(out, f"\n### `{path}`", args.max_bytes):
            omitted.append(path)
            continue
        if not append(out, "```diff", args.max_bytes):
            omitted.append(path)
            continue
        complete = True
        for line in patch.splitlines():
            if not append(out, line, args.max_bytes):
                complete = False
                break
        append(out, "```", args.max_bytes)
        if not complete:
            omitted.append(path)
            break

    if omitted:
        append(out, "", args.max_bytes)
        append(out, "## Truncation", args.max_bytes)
        append(out, "Packet hit its hard byte cap. Inspect only the omitted/suspicious files below next:", args.max_bytes)
        for path in omitted:
            append(out, f"- `{path}`", args.max_bytes)

    append(out, "", args.max_bytes)
    append(out, "## Review discipline", args.max_bytes)
    append(out, "Use this packet as the first pass. Expand source/diff context only around a concrete suspicious hunk, caller, invariant, or regression hypothesis. Do not regenerate a giant unified diff.", args.max_bytes)

    output.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(output)
    print(f"files={len(files)} bytes={output.stat().st_size} omitted={len(omitted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
