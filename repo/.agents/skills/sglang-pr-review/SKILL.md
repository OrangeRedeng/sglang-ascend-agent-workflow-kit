---
name: sglang-pr-review
description: Review an SGLang pull request for actionable correctness/regression findings without modifying code.
---
# SGLang PR review

1. Fetch PR metadata, base/head, changed filenames and diff.
2. Classify touched components before broad exploration.
3. Load only applicable SGLang rules/skills.
4. Review: correctness/regressions -> backend portability -> NPU behavior if relevant -> state/concurrency -> duplication/dead code -> test value.
5. Do not edit code. Do not report style-only noise unless it creates risk.
6. If actionable findings are discovered and they are not already authoritative unresolved GitHub review threads, **write `.codex/handoffs/pr-<N>-review.md` before stopping**. Use `.codex/scripts/new-handoff.sh <N>` if needed.
7. The handoff contains only actionable implementation data: severity, file/symbol, root cause, exact intended change, constraints, minimal validation, and material uncertainty.
8. If no actionable findings exist, do not create an empty handoff. If GitHub threads are authoritative, do not duplicate them locally.
9. Stop after all changed code paths are covered.
