---
name: sglang-address-review
description: Address actionable SGLang review findings or unresolved review comments with minimal scoped changes.
---
# Address review

1. Determine the authoritative findings: GitHub unresolved threads or a provided `.codex/handoffs/` file.
2. Re-verify every finding against current HEAD; skip obsolete/already-fixed items.
3. Load applicable upstream rules/skills before modifying covered components.
4. Make the smallest change satisfying review intent; no unrelated refactor.
5. Run targeted validation only.
6. Re-check each finding against the resulting diff and stop.
