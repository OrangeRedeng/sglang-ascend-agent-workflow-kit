#!/usr/bin/env python3
"""Read, validate, and compare workflow-kit semantic versions."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def parse(version: str) -> tuple[int, int, int, tuple[tuple[int, object], ...]]:
    value = version.strip()
    match = SEMVER_RE.fullmatch(value)
    if not match:
        raise ValueError(f"not a valid SemVer version: {value!r}")
    major, minor, patch = (int(match.group(i)) for i in (1, 2, 3))
    prerelease = match.group(4)
    if prerelease is None:
        # A release sorts after any prerelease with the same core version.
        pre_key: tuple[tuple[int, object], ...] = ((2, ""),)
    else:
        parts: list[tuple[int, object]] = []
        for part in prerelease.split("."):
            if part.isdigit():
                if len(part) > 1 and part.startswith("0"):
                    raise ValueError(f"numeric prerelease identifier has a leading zero: {part!r}")
                parts.append((0, int(part)))
            else:
                parts.append((1, part))
        pre_key = tuple(parts)
    return major, minor, patch, pre_key


def compare(left: str, right: str) -> int:
    l = parse(left)
    r = parse(right)
    l_core, r_core = l[:3], r[:3]
    if l_core < r_core:
        return -1
    if l_core > r_core:
        return 1

    # SemVer prerelease ordering: numeric < non-numeric; shorter equal prefix < longer;
    # final release > prerelease.
    lp, rp = l[3], r[3]
    if lp == rp:
        return 0
    if lp == ((2, ""),):
        return 1
    if rp == ((2, ""),):
        return -1
    for a, b in zip(lp, rp):
        if a == b:
            continue
        if a[0] != b[0]:
            return -1 if a[0] < b[0] else 1
        return -1 if a[1] < b[1] else 1
    return -1 if len(lp) < len(rp) else 1


def read_version(root: Path) -> str:
    path = root / "VERSION"
    value = path.read_text(encoding="utf-8").strip()
    parse(value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_current = sub.add_parser("current", help="print VERSION from a kit checkout")
    p_current.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])

    p_compare = sub.add_parser("compare", help="compare two SemVer values; prints -1, 0, or 1")
    p_compare.add_argument("left")
    p_compare.add_argument("right")

    p_verify = sub.add_parser("verify", help="validate VERSION and matching CHANGELOG heading")
    p_verify.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])

    args = parser.parse_args()
    try:
        if args.command == "current":
            print(read_version(args.root.resolve()))
        elif args.command == "compare":
            print(compare(args.left, args.right))
        else:
            root = args.root.resolve()
            version = read_version(root)
            changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
            if not re.search(rf"^## \[{re.escape(version)}\](?:\s+-\s+\d{{4}}-\d{{2}}-\d{{2}})?\s*$", changelog, re.M):
                raise ValueError(f"CHANGELOG.md has no release heading for VERSION {version}")
            print(version)
    except (OSError, ValueError) as exc:
        print(f"version error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
