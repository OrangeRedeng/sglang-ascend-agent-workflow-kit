#!/usr/bin/env python3
"""Bounded two-stage reducer for large SGLang/Ascend logs.

Default output is intentionally small (32 KiB / 400 lines). Repeated errors are
clustered by normalized signature. Use --expand <signature-id-or-text> only when
the first-stage artifact identifies a concrete missing window.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re
import subprocess

DEFAULT_PATTERNS = [
    r"traceback", r"runtimeerror", r"error", r"exception", r"failed", r"fatal",
    r"hccl", r"acl", r"aicore", r"aicpu", r"ez\d+", r"oom", r"out of memory",
    r"\bnan\b", r"\binf\b", r"timeout", r"hang", r"shape", r"dtype", r"unsupported",
    r"latency", r"throughput", r"tokens?/s", r"tok/s", r"memory",
]

TIMESTAMP_RX = re.compile(r"(?:\b\d{4}-\d\d-\d\d[T ][0-9:.+-Z]+\b|\b\d\d:\d\d:\d\d(?:\.\d+)?\b)")
HEX_RX = re.compile(r"0x[0-9a-fA-F]+")
RANK_RX = re.compile(r"(?:\[?rank\s*[=:]?\s*\d+\]?|\[\d+\])", re.I)
NUMBER_RX = re.compile(r"(?<![A-Za-z])\d+(?![A-Za-z])")
SPACE_RX = re.compile(r"\s+")


def git_root() -> Path | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None
    return Path(out) if out else None


def safe_name(path: Path) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", path.name).strip("-.")
    return name or "log"


def default_output(log: Path) -> Path:
    root = git_root()
    return (root / ".codex-artifacts" / "logs" / f"{safe_name(log)}.focused.txt") if root else log.with_name(f"{log.name}.focused.txt")


def normalize_signature(line: str) -> str:
    text = TIMESTAMP_RX.sub("<TS>", line)
    text = RANK_RX.sub("<RANK>", text)
    text = HEX_RX.sub("<HEX>", text)
    text = NUMBER_RX.sub("<N>", text)
    text = SPACE_RX.sub(" ", text).strip()
    return text[:500]


def sig_id(signature: str) -> str:
    return hashlib.sha1(signature.encode("utf-8", "replace")).hexdigest()[:10]


@dataclass
class Sample:
    center: int
    rows: list[tuple[int, str]] = field(default_factory=list)
    remaining: int = 0


@dataclass
class Signature:
    text: str
    count: int = 0
    first_line: int = 0
    last_line: int = 0
    samples: list[Sample] = field(default_factory=list)


def analyze(log: Path, rx: re.Pattern[str], context: int, sample_limit: int, head_n: int, tail_n: int):
    signatures: dict[str, Signature] = {}
    pattern_freq: Counter[str] = Counter()
    head: list[tuple[int, str]] = []
    tail: deque[tuple[int, str]] = deque(maxlen=tail_n)
    before: deque[tuple[int, str]] = deque(maxlen=context)
    active: list[Sample] = []
    total_lines = 0
    matched = 0

    with log.open("r", encoding="utf-8", errors="replace") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.rstrip("\n\r")
            total_lines = lineno
            if lineno <= head_n:
                head.append((lineno, line))
            tail.append((lineno, line))

            # Complete post-context of previously selected samples.
            still: list[Sample] = []
            for sample in active:
                if sample.remaining > 0:
                    sample.rows.append((lineno, line))
                    sample.remaining -= 1
                if sample.remaining > 0:
                    still.append(sample)
            active = still

            if rx.search(line):
                matched += 1
                normalized = normalize_signature(line)
                key = sig_id(normalized)
                entry = signatures.setdefault(key, Signature(normalized))
                entry.count += 1
                entry.first_line = entry.first_line or lineno
                entry.last_line = lineno
                if len(entry.samples) < sample_limit:
                    last_center = entry.samples[-1].center if entry.samples else -10**9
                    if lineno - last_center > max(2 * context + 1, 8):
                        rows = list(before) + [(lineno, line)]
                        sample = Sample(center=lineno, rows=rows, remaining=context)
                        entry.samples.append(sample)
                        if context:
                            active.append(sample)
                lower = line.lower()
                for token in DEFAULT_PATTERNS:
                    try:
                        if re.search(token, lower, re.I):
                            pattern_freq[token] += 1
                    except re.error:
                        pass
            before.append((lineno, line))
    return total_lines, matched, signatures, pattern_freq, head, list(tail)


def append_bounded(lines: list[str], text: str, max_lines: int, max_bytes: int) -> bool:
    candidate = text + "\n"
    current_bytes = sum(len(x.encode("utf-8", "replace")) + 1 for x in lines)
    if len(lines) >= max_lines or current_bytes + len(candidate.encode("utf-8", "replace")) > max_bytes:
        return False
    lines.append(text)
    return True


def render_rows(out: list[str], rows: list[tuple[int, str]], max_lines: int, max_bytes: int) -> bool:
    prev = None
    for lineno, text in rows:
        if prev is not None and lineno > prev + 1:
            if not append_bounded(out, f"... omitted {lineno - prev - 1} lines ...", max_lines, max_bytes):
                return False
        if not append_bounded(out, f"{lineno:8d}: {text}", max_lines, max_bytes):
            return False
        prev = lineno
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--stdout", action="store_true")
    ap.add_argument("-C", "--context", type=int, default=4)
    ap.add_argument("--head", type=int, default=30)
    ap.add_argument("--tail", type=int, default=40)
    ap.add_argument("--samples-per-signature", type=int, default=2)
    ap.add_argument("--max-signatures", type=int, default=20)
    ap.add_argument("--max-lines", type=int, default=400)
    ap.add_argument("--max-bytes", type=int, default=32768)
    ap.add_argument("--pattern", action="append", default=[])
    ap.add_argument("--expand", default="", help="signature id or text fragment to expand")
    args = ap.parse_args()

    log = args.log.expanduser().resolve()
    if not log.is_file():
        ap.error(f"log file not found: {log}")
    patterns = DEFAULT_PATTERNS + args.pattern
    rx = re.compile("(?:" + "|".join(patterns) + ")", re.I)
    total_lines, matched, signatures, freq, head, tail = analyze(
        log, rx, max(0, args.context), max(1, args.samples_per_signature), max(0, args.head), max(0, args.tail)
    )

    ranked = sorted(signatures.items(), key=lambda kv: (-kv[1].count, kv[1].first_line))
    if args.expand:
        needle = args.expand.lower()
        ranked = [kv for kv in ranked if kv[0].lower().startswith(needle) or needle in kv[1].text.lower()]
        if not ranked:
            raise SystemExit(f"No signature matched --expand {args.expand!r}")

    out: list[str] = []
    meta = [
        f"SOURCE: {log}",
        f"SOURCE_BYTES: {log.stat().st_size}",
        f"TOTAL_LINES: {total_lines}",
        f"MATCHED_LINES_TOTAL: {matched}",
        f"UNIQUE_SIGNATURES: {len(signatures)}",
        f"OUTPUT_CAP_BYTES: {args.max_bytes}",
        f"OUTPUT_CAP_LINES: {args.max_lines}",
        "",
        "=== ERROR / SIGNAL SIGNATURES ===",
    ]
    for row in meta:
        append_bounded(out, row, args.max_lines, args.max_bytes)

    for key, entry in ranked[: args.max_signatures]:
        if not append_bounded(
            out,
            f"{key} count={entry.count} first={entry.first_line} last={entry.last_line} :: {entry.text}",
            args.max_lines,
            args.max_bytes,
        ):
            break

    append_bounded(out, "", args.max_lines, args.max_bytes)
    append_bounded(out, "=== MATCH FREQUENCY ===", args.max_lines, args.max_bytes)
    for pattern, count in freq.most_common(20):
        if not append_bounded(out, f"{count:7d}  {pattern}", args.max_lines, args.max_bytes):
            break

    if not args.expand:
        append_bounded(out, "", args.max_lines, args.max_bytes)
        append_bounded(out, "=== LOG HEAD ===", args.max_lines, args.max_bytes)
        render_rows(out, head, args.max_lines, args.max_bytes)

    append_bounded(out, "", args.max_lines, args.max_bytes)
    append_bounded(out, "=== REPRESENTATIVE WINDOWS ===", args.max_lines, args.max_bytes)
    for key, entry in ranked[: args.max_signatures]:
        if not append_bounded(out, f"--- signature {key} count={entry.count} ---", args.max_lines, args.max_bytes):
            break
        for sample in entry.samples:
            if not render_rows(out, sample.rows, args.max_lines, args.max_bytes):
                break

    if not args.expand:
        append_bounded(out, "", args.max_lines, args.max_bytes)
        append_bounded(out, "=== LOG TAIL ===", args.max_lines, args.max_bytes)
        render_rows(out, tail, args.max_lines, args.max_bytes)

    append_bounded(out, "", args.max_lines, args.max_bytes)
    append_bounded(
        out,
        "EXPAND: rerun with --expand <signature-id> only if a specific signature needs more context.",
        args.max_lines,
        args.max_bytes,
    )
    result = "\n".join(out).rstrip() + "\n"

    if args.stdout:
        print(result, end="")
        return 0
    output = (args.output or default_output(log)).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding="utf-8")
    print(f"Focused log: {output}")
    print(f"Source: {log.stat().st_size} bytes, {total_lines} lines")
    print(f"Matches: {matched}; signatures: {len(signatures)}; output: {len(result.encode('utf-8'))} bytes / {len(out)} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
