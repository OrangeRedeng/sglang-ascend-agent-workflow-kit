# Workflow

## Core model

**Chat = working memory. Git = code state. `.codex-artifacts/` = durable local workflow state.**

The workflow is optimized to keep each Codex session narrow while preserving actionable state between sessions.

## 1. Decide whether to continue the session

Use this rule before sending the next prompt:

```text
same goal + same strategy -> continue
same goal + new strategy  -> new session
new goal                  -> new session
```

Examples of **new strategy**:

- “Instead of changing every file, centralize the fix in the package initializer.”
- “Remove the guards we just added and restore the upstream condition.”
- “The root cause is not the backend selector; now investigate graph capture.”

These are expensive if appended to an already large implementation thread because the new turn still carries the abandoned approach.

### Atomic task examples

```text
PR review             -> session -> handoff if actionable -> stop
address findings      -> new session -> auto-discovered handoff -> patch -> stop
resolve conflicts     -> new session -> stop
update PR description -> new session -> stop
CI regression         -> new session -> handoff if implementation deferred -> stop
```

Use `/side` only for a small detour that does not change the objective or implementation strategy. `/fork` is not a review-to-implementation handoff.

## 2. Review -> implementation

### Review session

Prompt:

```text
Review PR #34855. Report only.
```

If actionable findings exist and GitHub unresolved review threads are not already the authoritative source, Codex creates:

```text
.codex-artifacts/handoffs/pr-34855-review.md
```

The handoff contains metadata plus compact implementation findings only.

### New implementation session

Prompt:

```text
Address the review findings.
```

You normally do **not** provide the handoff path.

Auto-discovery happens twice:

1. `SessionStart` hook resolves an open handoff for the current PR/branch/worktree and injects the path.
2. `UserPromptSubmit` repeats the check for implementation-like prompts.

The implementation agent then must:

```text
read selected handoff
  -> re-verify current HEAD
  -> skip stale/already-fixed findings
  -> implement only actionable items
  -> targeted validation
  -> re-check diff
  -> mark handoff consumed if complete
  -> stop
```

Manual diagnostic:

```bash
python3 .codex/scripts/resolve-handoff.py --json
```

## 3. Handoff metadata and status

New handoffs include:

```text
status
kind
PR
branch
repository
worktree
base commit
reviewed HEAD
creation time
consumed time / HEAD
```

This makes discovery deterministic enough to avoid selecting a handoff merely because its filename looks similar.

Discovery priority:

```text
current PR
  -> exact current branch
  -> newest OPEN handoff for the same worktree
  -> only OPEN handoff for the same repository
```

Consumed handoffs are ignored.

Manual lifecycle commands:

```bash
.codex/scripts/new-handoff.sh 34855
.codex/scripts/new-handoff.sh scheduler-rank-desync
python3 .codex/scripts/handoff-status.py consume <path>
python3 .codex/scripts/handoff-status.py reopen <path>
```

## 4. Runtime artifacts are separate from static workflow files

```text
.codex/
  scripts/
  templates/

.codex-artifacts/
  handoffs/
  goals/
  logs/
```

Why: `.codex/` may be protected/read-only in the VS Code Codex sandbox. Mutable state must have a writable destination.

Both directories are local workflow state and are excluded from upstream SGLang PRs through `.git/info/exclude`.

## 5. Large logs

If a local/downloaded log is at least 1 MiB or 10,000 lines:

```text
MUST check size first
MUST NOT full-read raw log first
MUST run reducer
MUST inspect focused artifact first
```

Command:

```bash
.codex/scripts/extract-log-context.py /path/to/log
```

Output:

```text
.codex-artifacts/logs/<name>.focused.txt
```

## 6. Long performance/kernel work

For genuinely iterative evidence-driven work:

```text
/plan
/goal <objective>
```

Then:

```bash
.codex/scripts/new-goal.sh <goal-slug>
```

State lives in:

```text
.codex-artifacts/goals/<goal>/
├── goal.md
├── environment.md
├── baseline.md
├── manifest.md
├── failed-directions.md
├── experiments/
└── artifacts/
```

One round = one hypothesis + one scoped change + correctness + same benchmark + artifact update.

## 7. One active session per worktree

Parallel Codex sessions must not share an editing worktree.

Use Git worktrees for parallel tasks:

```bash
git worktree add ../sglang-task-a <branch-a>
git worktree add ../sglang-task-b <branch-b>
```

Then open each worktree in a separate WSL VS Code window.

## 8. Model routing

```text
Luna / low
  metadata, PR description, mechanical docs/simple edits

Terra / medium
  default implementation, conflicts, review fixes, ordinary bugs/refactors

Sol / high
  deep review, hard NPU correctness, NPUGraph/HCCL/distributed, difficult performance

Sol / xhigh
  escalation only after a focused high-effort attempt failed
```

## 9. Search routing

```text
exact identifier/path/error -> rg
known PR/commit             -> git show / git diff
model-family history        -> model history skill
unknown conceptual location -> Semble
known symbol relationships  -> Serena (optional)
```

Stop semantic discovery once the concrete symbol/path is known.

## 10. Tests and Git

Do not create/modify tests by default. Add them only when explicitly requested, required by review/CI, or needed as a real regression guard.

Do not spend a model turn on decided Git operations such as `git push`; run them directly in the terminal.
