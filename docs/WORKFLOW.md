# Workflow

## Core rule

**Chat = working memory. Git = code state. Handoff/Goal files = durable memory.**

A new engineering objective normally gets a new Codex session. Long, evidence-driven experiments are the exception.

## 1. Session boundaries

Use a new session for each atomic objective:

- PR review;
- resolve merge/rebase conflicts;
- address review comments;
- update PR description;
- fix one CI failure;
- investigate one bounded regression;
- perform one scoped refactor.

Do not treat one PR as one permanent conversation.

Example:

```text
PR #31320
  review             -> Sol/high   -> stop
  address findings   -> Terra      -> stop
  resolve conflicts  -> Terra      -> stop
  update description -> Luna       -> stop
```

### Same objective

- `/side` - a short detour that does not change the objective.
- `/compact` - reduce transcript size while continuing the same objective.
- `/fork` - explore an alternative from the same state; not a cheap review-to-implementation handoff.

## 2. Review -> implementation handoff

When Codex itself discovers findings that are not already represented as GitHub review threads:

```text
Session A: review only
  -> .codex/handoffs/pr-<N>-review.md
  -> stop

Session B: read the handoff
  -> implement actionable findings
  -> re-check each finding
  -> stop
```

Create a handoff template with:

```bash
.codex/scripts/new-handoff.sh <PR-number>
```

The handoff should contain only severity, file/symbol, root cause/problem, required change, constraints, and minimal validation.

If the authoritative findings already exist as unresolved GitHub review comments, prefer reading those in the new session instead of duplicating them in a local handoff.

## 3. Long performance/kernel work -> Goal + artifacts

For multi-round performance optimization, kernel work, or an unknown regression that genuinely needs iterative evidence:

```text
/plan
/goal <objective>
```

Create the durable ledger:

```bash
.codex/scripts/new-goal.sh <goal-slug>
```

Structure:

```text
.codex/goals/<goal>/
├── goal.md
├── environment.md
├── baseline.md
├── manifest.md
├── failed-directions.md
├── experiments/
└── artifacts/
```

One experiment round should contain one hypothesis, one scoped change, correctness evidence, the same benchmark, and an artifact update.

## 4. Model routing

```text
Luna / low
  PR descriptions, metadata, docs, mechanical edits.

Terra / medium
  default development: conflicts, review-comment fixes, ordinary bugs/refactors.

Sol / high
  deep PR review, difficult feature work, hard Ascend correctness,
  HCCL/NPUGraph/distributed/performance root-cause work.

Sol / xhigh
  escalation only after a focused high-effort investigation fails.
```

Aliases:

```bash
cxl
cx
cxh
cxx
```

The helper router also supports task kinds:

```bash
cx-task review
cx-task conflict
cx-task npu
cx-task docs
```

## 5. Do not spend a model turn on decided shell operations

When no reasoning is needed, run directly in the terminal:

```bash
git push
git status
git switch <branch>
git fetch --prune
```

The included `UserPromptSubmit` hook blocks standalone prompts such as `push` or `git push` before a model call.

A request such as `resolve conflicts, validate the diff, then push` is different: push is part of a reasoning task and is not blocked.

## 6. Scope discipline

- Make the smallest change that solves the current objective.
- Do not add unrelated cleanup/refactoring/docs while already in a file.
- PR review is report-only unless editing is explicitly requested.
- Conflict resolution is conflict resolution only.
- Stop when the objective and minimal validation are complete.

## 7. Tests

Do not create or modify tests by default.

Tests are appropriate when:

1. explicitly requested;
2. explicitly required by review/CI;
3. a real regression guard is necessary to demonstrate the fix.

For SGLang, consult upstream `.claude/rules/unit-test-admission.md` before adding or modifying tests.

## 8. Weekly workflow check

Use `/usage` periodically and watch for:

- number of turns per objective;
- repeated reads/searches of the same context;
- unnecessary xhigh use;
- trivial Git prompts;
- performance experiments without an artifact ledger.

Optimize the workflow only after observing an actual bottleneck; do not add many MCP/RAG tools at once.
