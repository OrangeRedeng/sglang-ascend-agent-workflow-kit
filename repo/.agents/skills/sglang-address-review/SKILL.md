---
name: sglang-address-review
description: Address actionable SGLang review findings or unresolved review comments with minimal scoped changes.
---
# Address review

1. Determine the authoritative findings:
   - unresolved GitHub review threads first, when they exist;
   - otherwise a matching/provided `.codex/handoffs/` file.
2. If a handoff is authoritative, read it before broad exploration. Do not redo a broad PR review.
3. Re-verify every finding against current HEAD; skip obsolete/already-fixed items.
4. Load applicable upstream rules/skills before modifying covered components.
5. Make the smallest change satisfying review intent; no unrelated refactor.
6. Run targeted validation only.
7. Re-check each finding against the resulting diff, update completion state in the handoff when practical, and stop.
