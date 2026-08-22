---
name: sglang-address-review
description: Address actionable SGLang review findings or unresolved review comments with minimal scoped changes.
---
# Address review

1. Before broad exploration run `python3 .codex/scripts/resolve-handoff.py --json --prompt "<current task>"` even if the user did not name a handoff. Hooks normally do this automatically; this is the fallback check.
2. Determine the authoritative findings:
   - unresolved GitHub review threads first when they are the maintained source of truth;
   - otherwise the auto-discovered `.codex-artifacts/handoffs/` file.
3. If a handoff is selected, read it first. Do not redo a broad PR review. Never silently consume a resolver candidate marked stale, ambiguous, topic-mismatched, or lacking an active pointer for a generic continuation.
4. Re-verify every finding against current HEAD; skip obsolete/already-fixed items.
5. Load applicable upstream rules/skills before modifying covered components.
6. Make the smallest change satisfying review intent; no unrelated refactor.
7. Run targeted validation only.
8. Re-check each finding against the resulting diff.
9. If every handoff item is completed or obsolete, run `python3 .codex/scripts/handoff-status.py consume <path>`. If work is partial, keep it open.
10. Stop.
