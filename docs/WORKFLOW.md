# Workflow

## Recommended interface

Use **VS Code + WSL + Codex extension** as the default daily workflow. Open SGLang with `cd ~/code/sglang && code .`, then work from the Codex sidebar. Use the CLI (`cx`, `cxh`, etc.) only when a terminal session is intentionally preferable. See [VS Code + Codex](VSCODE.md).

## Core rule

**Chat = working memory. Git = code state. Handoff/Goal files = durable memory.**

A new engineering objective normally gets a new Codex session. Long, evidence-driven experiments are the exception.

For what is automatic versus manual, see [Automation and enforcement](AUTOMATION.md).

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
  review             -> Sol/high   -> handoff if needed -> stop
  address findings   -> Terra      -> consume handoff   -> stop
  resolve conflicts  -> Terra      -> stop
  update description -> Luna       -> stop
```

### Same objective

- `/side` - a short detour that does not change the objective.
- `/compact` - reduce transcript size while continuing the same objective.
- `/fork` - explore an alternative from the same state; **not** a review-to-implementation handoff.

## 2. Review -> implementation handoff

### What is automatic

For report-only PR review, the local SGLang review skill now has a **MUST-create** handoff rule when all of the following are true:

1. Codex found actionable findings;
2. implementation is not being performed in the same review session;
3. those findings are not already authoritative unresolved GitHub review threads.

So this prompt is enough:

```text
Review PR #31320. Report only.
```

Expected result:

```text
Session A: review only
  -> actionable findings
  -> .codex/handoffs/pr-31320-review.md   (automatic by repo rule)
  -> stop

Session B: implementation
  -> GitHub unresolved threads if authoritative
     OR .codex/handoffs/pr-31320-review.md
  -> re-verify current HEAD
  -> implement only listed actionable findings
  -> targeted validation
  -> stop
```

The second session must not redo the broad PR review just to reconstruct context.

### Handoff contents

Keep only durable implementation information:

- source/PR and reviewed commit when known;
- severity/priority;
- file and symbol;
- root cause/problem;
- exact intended change;
- constraints/non-goals;
- minimal validation;
- material uncertainty only when it changes implementation.

Do **not** copy review narration, exploratory dead ends, long diffs, or chat history.

### Create one manually

Numeric PR:

```bash
.codex/scripts/new-handoff.sh 31320
# .codex/handoffs/pr-31320-review.md
```

Generic bounded investigation:

```bash
.codex/scripts/new-handoff.sh scheduler-rank-desync
# .codex/handoffs/scheduler-rank-desync.md
```

If there are no actionable findings, do not create an empty handoff.

If the authoritative findings already exist as unresolved GitHub review comments, use those in the new session rather than maintaining a duplicate local copy.

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

For the VS Code extension, Terra/medium comes from the main `~/.codex/config.toml`; switch to Sol/high in the extension UI for genuinely hard tasks.

CLI-only aliases:

```bash
cxl
cx
cxh
cxx
```

The CLI helper router also supports task kinds:

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
- performance experiments without an artifact ledger;
- large logs read without reduction;
- implementation sessions that redo an existing review instead of consuming a handoff.

Optimize the workflow only after observing an actual bottleneck; do not add many MCP/RAG tools at once.
