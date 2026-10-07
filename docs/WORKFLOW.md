# Workflow

## Session lifecycle

```text
NEW OBJECTIVE -> NEW SESSION
SAME GOAL + NEW IMPLEMENTATION STRATEGY -> NEW SESSION
SAME GOAL + SAME STRATEGY -> continue, but checkpoint when retrieval budget grows
ONE ACTIVE EDITING AGENT SESSION PER GIT WORKTREE
```

Measured rollout data showed that long high-tool-call sessions became the largest remaining input-token hotspot. v0.3.1 therefore adds a session/retrieval governor. Its warnings are guardrails, not substitutes for engineering judgment.

## Implementation continuation

For code-changing work:

```bash
python3 .codex/scripts/resolve-handoff.py --json --prompt '<task>'
```

Use a selected fresh handoff, re-verify against HEAD, and avoid reconstructing the previous review. Mark consumed only after all actionable items are completed/obsolete.

## PR review

For a broad PR use the deterministic review packet first. It creates changed-file/component coverage and narrow diffs in one bounded artifact. Expand only suspicious regions. Do not replace many round trips with one giant unbounded diff.

## Large logs

Check size without reading content. At >=1 MiB or >=10,000 lines, run the reducer first. First-stage output is bounded; expand only a specific normalized signature when needed.

## Long performance work

Use Goal artifacts. One experiment round = one hypothesis + one scoped change + correctness + identical benchmark + decision. Numeric metrics go to `results.jsonl` via `workflow-exp`, human rationale remains in Markdown. When the session becomes retrieval-heavy, persist state and continue the next round in a new session rather than carrying the full conversation.
