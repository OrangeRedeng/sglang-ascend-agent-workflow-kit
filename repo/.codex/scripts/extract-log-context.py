#!/usr/bin/env python3
"""Reduce large SGLang/Ascend logs before sending them to an LLM.

Keeps head/tail, matched lines with surrounding context, and a frequency summary.
Never modifies the original log.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re

DEFAULT_PATTERNS = [
    r"traceback", r"runtimeerror", r"error", r"exception", r"failed", r"fatal",
    r"hccl", r"acl", r"aicore", r"aicpu", r"ez\d+", r"oom", r"out of memory",
    r"nan", r"inf", r"timeout", r"hang", r"shape", r"dtype", r"unsupported",
    r"latency", r"throughput", r"tokens?/s", r"tok/s", r"memory",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("-C", "--context", type=int, default=12)
    ap.add_argument("--head", type=int, default=80)
    ap.add_argument("--tail", type=int, default=120)
    ap.add_argument("--max-matches", type=int, default=250)
    ap.add_argument("--pattern", action="append", default=[])
    args = ap.parse_args()

    text = args.log.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    patterns = DEFAULT_PATTERNS + args.pattern
    rx = re.compile("(?:" + "|".join(patterns) + ")", re.I)

    hits = [i for i, line in enumerate(lines) if rx.search(line)]
    hits = hits[: args.max_matches]

    keep = set(range(min(args.head, len(lines))))
    keep.update(range(max(0, len(lines) - args.tail), len(lines)))
    for i in hits:
        keep.update(range(max(0, i - args.context), min(len(lines), i + args.context + 1)))

    ordered = sorted(keep)
    out = []
    out.append(f"SOURCE: {args.log}")
    out.append(f"TOTAL_LINES: {len(lines)}")
    out.append(f"MATCHED_LINES: {len(hits)} (capped at {args.max_matches})")
    out.append("")

    freq = Counter()
    for i in hits:
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
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
        print(args.output)
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
