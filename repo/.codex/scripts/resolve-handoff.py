#!/usr/bin/env python3
"""Resolve the safest applicable OPEN Codex handoff for the current Git worktree.

Resolution is deliberately conservative:
1. same repository only;
2. current PR / branch / worktree evidence;
3. task-topic overlap when the user prompt is available;
4. freshness of reviewed HEAD and handoff age;
5. never silently pick among multiple unrelated same-PR handoffs.

The script is dependency-free so SessionStart/UserPromptSubmit hooks can call it cheaply.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

STALE_HOURS = 48
STALE_COMMIT_DISTANCE = 50

STOPWORDS = {
    "a", "an", "and", "apply", "address", "change", "changes", "correct", "do", "fix",
    "for", "from", "handle", "implement", "in", "it", "make", "modify", "of", "on",
    "patch", "please", "port", "pr", "remove", "resolve", "restore", "review", "reviews",
    "the", "this", "to", "update", "with", "work", "findings", "finding", "new", "current",
}


def run(cmd: list[str], cwd: Path, timeout: float = 2.0) -> str:
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
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
        return run(
            ["gh", "pr", "view", "--json", "number", "--jq", ".number"],
            root,
            timeout=3.0,
        )
    return ""


def parse_time(value: str, fallback: float) -> float:
    if value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    return fallback


def tokenize(value: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9_]{2,}", value.lower()))
    return {t for t in tokens if t not in STOPWORDS and not t.isdigit()}


def topic_from_name(name: str) -> str:
    stem = re.sub(r"\.md$", "", name, flags=re.I)
    stem = re.sub(r"^pr-\d+-", "", stem, flags=re.I)
    return stem


def git_distance(root: Path, reviewed_head: str, head: str) -> tuple[int | None, bool | None]:
    if not reviewed_head or not head or reviewed_head == head:
        return (0 if reviewed_head and head else None, True if reviewed_head == head and head else None)
    exists = run(["git", "cat-file", "-t", reviewed_head], root)
    if not exists:
        return None, None
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", reviewed_head, head],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    if not ancestor:
        return None, False
    count = run(["git", "rev-list", "--count", f"{reviewed_head}..{head}"], root)
    try:
        return int(count), True
    except ValueError:
        return None, True


def candidate_record(path: Path, root: Path, head: str, now_ts: float) -> dict[str, object]:
    md = metadata(path)
    name = path.name
    if not md:
        m = re.match(r"pr-(\d+)-(.+)\.md$", name)
        topic = m.group(2) if m else topic_from_name(name)
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
            "topic": topic,
            "scope": "",
            "objective": "",
        }
    stat = path.stat()
    created_ts = parse_time(md.get("created_at", ""), stat.st_mtime)
    age_hours = max(0.0, (now_ts - created_ts) / 3600.0)
    reviewed_head = md.get("reviewed_head", "")
    distance, ancestor = git_distance(root, reviewed_head, head)
    stale_reasons: list[str] = []
    if age_hours > STALE_HOURS:
        stale_reasons.append(f"age>{STALE_HOURS}h")
    if ancestor is False:
        stale_reasons.append("reviewed_head_not_ancestor")
    if distance is not None and distance > STALE_COMMIT_DISTANCE:
        stale_reasons.append(f"head_distance>{STALE_COMMIT_DISTANCE}")

    topic = md.get("topic", "") or topic_from_name(name)
    scope = md.get("scope", "")
    objective = md.get("objective", "")
    candidate_terms = tokenize(" ".join([topic, scope, objective, topic_from_name(name)]))

    return {
        "path": str(path),
        "status": md.get("status", "open").lower(),
        "kind": md.get("kind", ""),
        "pr": md.get("pr", "").lstrip("#"),
        "branch": md.get("branch", ""),
        "repo": md.get("repo", ""),
        "worktree": md.get("worktree", ""),
        "created_at": md.get("created_at", ""),
        "reviewed_head": reviewed_head,
        "topic": topic,
        "scope": scope,
        "objective": objective,
        "terms": sorted(candidate_terms),
        "mtime": stat.st_mtime,
        "age_hours": round(age_hours, 2),
        "head_distance": distance,
        "reviewed_head_is_ancestor": ancestor,
        "stale": bool(stale_reasons),
        "stale_reasons": stale_reasons,
    }


def rank_topic(candidates: list[dict[str, object]], prompt_terms: set[str]) -> tuple[list[dict[str, object]], int]:
    if not prompt_terms:
        return [], 0
    scored: list[tuple[int, dict[str, object]]] = []
    for c in candidates:
        terms = set(c.get("terms", []))
        score = len(prompt_terms & terms)
        if score:
            scored.append((score, c))
    if not scored:
        return [], 0
    best = max(score for score, _ in scored)
    return [c for score, c in scored if score == best], best


def load_active_pointer(path: Path) -> dict[str, object] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) and data.get("path") else None


def newest(candidates: list[dict[str, object]]) -> dict[str, object]:
    return sorted(
        candidates,
        key=lambda c: parse_time(str(c["created_at"]), float(c["mtime"])),
        reverse=True,
    )[0]


def choose_from_group(
    group: list[dict[str, object]],
    prompt_terms: set[str],
    generic_prompt: bool,
    prompt_present: bool,
    reason_prefix: str,
    confidence: str,
) -> tuple[dict[str, object] | None, str, str]:
    fresh = [c for c in group if not c["stale"]]
    if not fresh:
        return None, f"{reason_prefix}; matching OPEN handoff(s) are stale", "stale-only"
    pool = fresh

    topic_matches, score = rank_topic(pool, prompt_terms)
    if len(topic_matches) == 1:
        c = topic_matches[0]
        return c, f"{reason_prefix}; topic match score={score}", f"{confidence}-topic"
    if len(topic_matches) > 1:
        c = newest(topic_matches)
        return c, f"{reason_prefix}; tied topic match score={score}, newest", f"{confidence}-topic-tie"

    if len(pool) == 1:
        # Without an active pointer, SessionStart/generic prompts contain no evidence that this
        # particular old OPEN handoff is the intended continuation. Do not resurrect it silently.
        if not prompt_present or generic_prompt:
            return None, f"{reason_prefix}; no active handoff pointer for a generic continuation", "no-active-pointer"
        return None, f"{reason_prefix}; only candidate has no task-topic overlap", "topic-mismatch"

    if not prompt_present:
        return None, f"{reason_prefix}; multiple open handoffs, wait for task-topic evidence", "ambiguous-no-prompt"

    if generic_prompt:
        return None, f"{reason_prefix}; generic continuation requires an active handoff pointer", "no-active-pointer"

    return None, f"{reason_prefix}; multiple open handoffs and no task-topic match", "ambiguous-topic"


def resolve(root: Path, allow_gh: bool = True, prompt: str = "") -> dict[str, object]:
    artifact_dir = root / ".codex-artifacts" / "handoffs"
    branch = run(["git", "branch", "--show-current"], root)
    head = run(["git", "rev-parse", "HEAD"], root)
    repo = run(["git", "remote", "get-url", "origin"], root)
    pr = infer_pr(branch, root, allow_gh)
    prompt_terms = tokenize(prompt)
    prompt_present = bool(prompt.strip())
    # Generic address/fix prompts intentionally contain no useful topic after stopword removal.
    generic_prompt = prompt_present and not prompt_terms
    now_ts = datetime.now(timezone.utc).timestamp()

    result: dict[str, object] = {
        "root": str(root),
        "branch": branch,
        "head": head,
        "repo": repo,
        "pr": pr,
        "prompt_terms": sorted(prompt_terms),
        "selected": None,
        "reason": "none",
        "confidence": "none",
        "candidates": [],
        "stale_candidates": [],
        "active_pointer": None,
        "policy": {"stale_hours": STALE_HOURS, "stale_commit_distance": STALE_COMMIT_DISTANCE},
    }
    if not artifact_dir.is_dir():
        return result

    candidates = []
    for path in sorted(artifact_dir.glob("*.md")):
        rec = candidate_record(path, root, head, now_ts)
        if rec["status"] != "open":
            continue
        if rec["repo"] and repo and rec["repo"] != repo:
            continue
        candidates.append(rec)
    result["candidates"] = [c["path"] for c in candidates]
    result["stale_candidates"] = [
        {"path": c["path"], "reasons": c["stale_reasons"]} for c in candidates if c["stale"]
    ]
    if not candidates:
        return result

    # Prefer the handoff explicitly activated by the most recent review/investigation.
    # Generic continuation prompts should never guess among arbitrary historical OPEN handoffs.
    pointer_paths = []
    if pr:
        pointer_paths.append(artifact_dir / f".active-pr-{pr}.json")
    pointer_paths.append(artifact_dir / ".active-worktree.json")
    by_path = {str(Path(str(c["path"])).resolve()): c for c in candidates}
    for pointer_path in pointer_paths:
        pointer = load_active_pointer(pointer_path)
        if not pointer:
            continue
        selected_path = str(Path(str(pointer["path"])).expanduser().resolve())
        candidate = by_path.get(selected_path)
        if candidate is None or candidate["stale"]:
            continue
        # An explicit topic in the current prompt may override a mismatching active pointer.
        if prompt_terms and not generic_prompt:
            overlap = len(prompt_terms & set(candidate.get("terms", [])))
            if overlap == 0:
                continue
        result.update(
            selected=candidate["path"],
            reason=f"active handoff pointer {pointer_path.name}",
            confidence="active-pointer",
            active_pointer=str(pointer_path),
        )
        return result

    if pr:
        exact = [c for c in candidates if str(c["pr"]) == pr]
        if exact:
            selected, reason, confidence = choose_from_group(
                exact, prompt_terms, generic_prompt, prompt_present, f"current PR #{pr}", "exact-pr"
            )
            if selected:
                result.update(selected=selected["path"], reason=reason, confidence=confidence)
            else:
                result.update(reason=reason, confidence=confidence)
            return result

    if branch:
        exact = [c for c in candidates if c["branch"] == branch]
        if exact:
            selected, reason, confidence = choose_from_group(
                exact, prompt_terms, generic_prompt, prompt_present, f"current branch {branch}", "exact-branch"
            )
            if selected:
                result.update(selected=selected["path"], reason=reason, confidence=confidence)
            else:
                result.update(reason=reason, confidence=confidence)
            return result

    same_worktree = [
        c for c in candidates
        if c["worktree"] and Path(str(c["worktree"])).resolve() == root
    ]
    if same_worktree:
        selected, reason, confidence = choose_from_group(
            same_worktree,
            prompt_terms,
            generic_prompt,
            prompt_present,
            "same worktree",
            "worktree-fallback",
        )
        if selected:
            result.update(selected=selected["path"], reason=reason, confidence=confidence)
        else:
            result.update(reason=reason, confidence=confidence)
        return result

    result["reason"] = "multiple/no safely applicable open handoffs"
    result["confidence"] = "ambiguous"
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", type=Path, default=Path.cwd())
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-gh", action="store_true", help="skip optional GitHub PR lookup")
    ap.add_argument("--prompt", default="", help="current user task; enables topic-aware matching")
    args = ap.parse_args()

    root = git_root(args.cwd.resolve())
    if root is None:
        payload = {
            "selected": None,
            "reason": "not a git worktree",
            "confidence": "none",
            "candidates": [],
            "stale_candidates": [],
        }
        if args.json:
            print(json.dumps(payload))
        return 1

    payload = resolve(root, allow_gh=not args.no_gh, prompt=args.prompt)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    elif payload["selected"]:
        print(payload["selected"])
    elif str(payload["confidence"]).startswith("ambiguous") or payload["confidence"] == "topic-mismatch":
        print(f"No safe handoff match: {payload['reason']}", file=sys.stderr)
        for item in payload["candidates"]:
            print(f"- {item}", file=sys.stderr)
    return 0 if payload["selected"] else (2 if payload["candidates"] else 1)


if __name__ == "__main__":
    raise SystemExit(main())
