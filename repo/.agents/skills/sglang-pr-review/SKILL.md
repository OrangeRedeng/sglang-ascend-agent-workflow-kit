---
name: sglang-pr-review
description: Review an SGLang pull request for actionable correctness/regression findings without modifying code.
---
# SGLang PR review

1. Fetch PR metadata/base/head and start with changed filenames plus diff statistics. Do **not** ingest a huge whole-PR unified diff first.
2. Classify touched files into components/workstreams before deeper retrieval.
3. Load only applicable SGLang rules/skills.
4. Review **component-by-component / file-by-file**. Initial diff context should normally be about **20-30 lines per hunk**; expand only around suspicious code, relevant callers, invariants, or regression hypotheses.
5. **Never start** a broad review with multi-file `--unified=70`, `--unified=80`, or similar large-context diffs. For large PRs, use changed-file listing -> per-file patch/diff -> narrow source context.
6. Review: correctness/regressions -> backend portability -> NPU behavior if relevant -> state/concurrency -> duplication/dead code -> test value.
7. Keep a short coverage checklist for a large review so already-reviewed files/components are not repeatedly re-read.
8. Do not edit code. Do not report style-only noise unless it creates risk.
9. If actionable findings are discovered and they are not already authoritative unresolved GitHub review threads, **run `.codex/scripts/new-handoff.sh <N> [topic]` and write the findings into the resulting `.codex-artifacts/handoffs/` file before stopping**. Use a specific topic for component-scoped review, for example `.codex/scripts/new-handoff.sh 34855 fsdp-review`.
10. The handoff contains only actionable implementation data: severity, file/symbol, root cause, exact intended change, constraints, minimal validation, and material uncertainty. Preserve its metadata front matter and fill `scope`/`objective` when useful for resolver matching.
11. If no actionable findings exist, do not create an empty handoff. If GitHub threads are authoritative, do not duplicate them locally.
12. Stop after all changed code paths are covered; do not expand into unrelated cleanup.
