# Workflow

The durable workflow is independent of model UI:

```text
Chat/session = working memory
Git          = code state
Handoff      = bounded task state
Goal         = long experiment state
```

Use one active editing agent per worktree.

For broad PR review, generate one bounded review packet before iterative exploration:

```bash
python3 .codex/scripts/workflow-review-packet.py --base origin/main
```

For large logs:

```bash
python3 .codex/scripts/extract-log-context.py <log>
```

For handoffs:

```bash
python3 .codex/scripts/resolve-handoff.py --json --prompt "<task>"
workflow-handoffs gc --older-than-hours 48
```

For performance/kernel Goals, record exact commands, environment, SHAs, correctness evidence, and numeric results in `results.jsonl` through `workflow-exp`.

The 32/44-call retrieval discipline is shared in `AGENTS.md`. The official Codex fallback additionally enforces it with `PostToolUse`; Codex Bridge and GLM run under the Copilot Chat harness, so native Codex hooks do not execute there.
