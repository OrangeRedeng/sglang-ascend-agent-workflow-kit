---
name: sglang-regression
description: Diagnose and fix an SGLang regression when a relevant commit, PR, good/bad boundary, or changed behavior is known.
---
# Regression workflow

1. Start with suspect diff (`git show --stat`, changed files/hunks) and direct callers/data flow.
2. Do not broadly scan the repository until this evidence is insufficient.
3. Classify shared vs backend-specific vs dependency behavior.
4. State one concrete root-cause hypothesis before editing.
5. Make the smallest fix preserving intended behavior.
6. Add a regression test only if it has independent guard value and is actually required.
7. Validate the original failing path first, then stop.
8. If the task is investigation/report-only and implementation is intentionally deferred, write a compact `.codex/handoffs/<slug>.md` before stopping when actionable next changes exist. Do not create one when the report has no actionable next step.
