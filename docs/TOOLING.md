# Tooling

Use the smallest mechanism that answers the question.

- Exact path/symbol/error: `rg` / direct file navigation.
- Known PR/commit: bounded Git/GitHub metadata and diff.
- Broad PR review: `.codex/scripts/workflow-review-packet.py` first.
- Large log: `.codex/scripts/extract-log-context.py` first.
- Conceptual unknown location: Semble if installed.
- Known symbol/caller graph: Serena if installed.
- Handoff lifecycle: `workflow-handoffs`.
- Performance result ledger: `workflow-exp`.
- External skill revision/index: `workflow-skills`.

Semble and Serena are optional in v0.3.1. They are not installed by Standard because the measured 127-session corpus showed zero actual calls; add them only when their retrieval mode solves a real repeated bottleneck.

The PostToolUse governor is intentionally lightweight and local. It stores counters/digests, not tool output bodies.
