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
6. If requested, write a compact handoff with severity, file/symbol, root cause, required change, constraints and validation.
7. Stop after all changed code paths are covered.
