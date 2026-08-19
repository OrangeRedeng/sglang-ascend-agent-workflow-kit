---
name: sglang-resolve-conflicts
description: Resolve SGLang merge/rebase conflicts while preserving upstream and PR intent, without unrelated work.
---
# Resolve conflicts

1. Inspect `git status --short`, unresolved filenames, base/head/merge-base and only conflicted hunks first.
2. Reconstruct upstream intent and PR intent; never choose ours/theirs mechanically.
3. Use bounded history only when intent is unclear.
4. Do not address unrelated review comments, refactor, update docs/description, or add tests solely for conflict resolution.
5. Ensure no conflict markers remain; run `git diff --check` and minimal relevant validation.
6. Stop. Do not push unless the current prompt explicitly asks.
