#!/usr/bin/env python3
"""Reduce large SGLang/Ascend logs before sending them to an LLM.

Keeps head/tail, matched lines with surrounding context, and a frequency summary.
The original log is never modified. By default the focused output is written to
.codex-artifacts/logs/<name>.focused.txt so a model tool call does not dump the reduced
log itself into conversation context.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import subprocess

DEFAULT_PATTERNS = [
    r"traceback", r"runtimeerror", r"error", r"exception", r"failed", r"fatal",
    r"hccl", r"acl", r"aicore", r"aicpu", r"ez\d+", r"oom", r"out of memory",
    r"nan", r"inf", r"timeout", r"hang", r"shape", r"dtype", r"unsupported",
    r"latency", r"throughput", r"tokens?/s", r"tok/s", r"memory",
]


def git_root() -> Path | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None
    return Path(out) if out else None


def safe_name(path: Path) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", path.name).strip("-.")
    return name or "log"


def default_output(log: Path) -> Path:
    root = git_root()
    if root is not None:
        return root / ".codex-artifacts" / "logs" / f"{safe_name(log)}.focused.txt"
    return log.with_name(f"{log.name}.focused.txt")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--stdout", action="store_true", help="print focused log instead of writing an artifact")
    ap.add_argument("-C", "--context", type=int, default=8)
    ap.add_argument("--head", type=int, default=60)
    ap.add_argument("--tail", type=int, default=80)
    ap.add_argument("--max-matches", type=int, default=120)
    ap.add_argument("--pattern", action="append", default=[])
    args = ap.parse_args()

    log = args.log.expanduser().resolve()
    if not log.is_file():
        ap.error(f"log file not found: {log}")

    text = log.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    patterns = DEFAULT_PATTERNS + args.pattern
    rx = re.compile("(?:" + "|".join(patterns) + ")", re.I)

    all_hits = [i for i, line in enumerate(lines) if rx.search(line)]
    hits = all_hits[: args.max_matches]

    keep = set(range(min(args.head, len(lines))))
    keep.update(range(max(0, len(lines) - args.tail), len(lines)))
    for i in hits:
        keep.update(range(max(0, i - args.context), min(len(lines), i + args.context + 1)))

    ordered = sorted(keep)
    out: list[str] = []
    out.append(f"SOURCE: {log}")
    out.append(f"SOURCE_BYTES: {log.stat().st_size}")
    out.append(f"TOTAL_LINES: {len(lines)}")
    out.append(f"MATCHED_LINES_TOTAL: {len(all_hits)}")
    out.append(f"MATCHED_LINES_INCLUDED: {len(hits)} (cap {args.max_matches})")
    out.append("")

    freq = Counter()
    for i in all_hits:
        low = lines[i].lower()
        for p in patterns:
            if re.search(p, low, re.I):
                freq[p] += 1
    out.append("=== MATCH FREQUENCY ===")
    for key, count in freq.most_common(30):
        out.append(f"{count:6d}  {key}")
    out.append("")
    out.append("=== FOCUSED LOG ===")

    prev = None
    for i in ordered:
        if prev is not None and i > prev + 1:
            out.append(f"... omitted {i - prev - 1} lines ...")
        out.append(f"{i+1:8d}: {lines[i]}")
        prev = i

    result = "\n".join(out) + "\n"

    if args.stdout:
        print(result, end="")
        return 0

    output = (args.output or default_output(log)).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding="utf-8")

    print(f"Focused log: {output}")
    print(f"Source: {log.stat().st_size} bytes, {len(lines)} lines")
    print(f"Matches: {len(all_hits)} total, {len(hits)} included")
    print("Next: inspect the focused artifact first; read raw ranges only if a concrete fact is missing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
