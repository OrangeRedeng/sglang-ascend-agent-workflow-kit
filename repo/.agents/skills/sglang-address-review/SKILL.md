---
name: sglang-address-review
description: Address actionable SGLang review findings or unresolved review comments with minimal scoped changes.
---
# Address review

1. Before broad exploration run `python3 .codex/scripts/resolve-handoff.py --json --prompt "<current task>"`.
2. Determine authoritative findings: unresolved GitHub review threads first, otherwise the auto-discovered handoff.
3. If a handoff is selected, read it first and do not redo broad review.
4. Re-verify every finding against current HEAD.
5. Load applicable upstream rules/skills before modifying covered components.
6. Make the smallest change satisfying review intent.
7. Run targeted validation only.
8. Re-check each finding against the resulting diff.
9. Consume the handoff only when every item is completed or obsolete.
10. Stop.
