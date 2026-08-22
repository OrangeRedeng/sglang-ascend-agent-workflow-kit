# Automation and enforcement

**Project invariant:** automation exists to reinforce the SGLang + Ascend engineering workflow. Model/provider routing must not bypass NPU compatibility, profiling, benchmark-comparability, or runtime-validation gates.

This page answers one practical question: **what happens automatically, and what must you put in the prompt?**

The default rule is: describe the engineering objective. Do not repeat the workflow machinery in every prompt.

## Enforcement levels

| Level | Meaning | Current examples |
|---|---|---|
| **Hard / hook-driven** | Code runs before the model turn/session and injects or blocks workflow state | automatic handoff discovery; standalone `git push` prompt guard |
| **Instruction-enforced** | `AGENTS.override.md` / `SKILL.md` says the model **MUST** perform a step | large-log reducer, handoff creation, handoff consumption/marking, search routing, strategy-reversal session split |
| **Manual / optional** | Human explicitly enables/uses it | Serena, optional Triton/AscendC skills, creating a parallel Git worktree |

The Codex VS Code extension and CLI both use the installed hook configuration when supported by the running Codex build. This kit installs the same hooks under `~/.codex/hooks.json` and `~/.codex/hooks/`.

## Handoff discovery - automatic by hook

You no longer need to type a handoff path in a normal implementation session.

A handoff created by a review/investigation lives under:

```text
.codex-artifacts/handoffs/
```

New handoffs carry metadata such as:

```yaml
status: open
kind: pr-review
pr: 34855
branch: pr/owner/34855
repo: <origin URL>
worktree: /home/user/code/sglang
reviewed_head: <sha>
created_at: <UTC timestamp>
```

### What happens at session start

The installed `SessionStart` hook runs the local resolver:

```text
new Codex session
  -> .codex/scripts/resolve-handoff.py
  -> current PR match
     else current branch match
     else newest open handoff for this worktree
     else only open handoff for this repository
  -> selected path is injected into Codex context
```

The hook injects only the **path + instruction**, not the full handoff body, so startup context stays small.

### What happens on an implementation-like prompt

`UserPromptSubmit` performs a second task-aware check for prompts such as:

```text
Address the review findings.
Fix the remaining regression.
Apply the requested changes.
```

If an open handoff matches, the path is injected again with a stronger instruction: read it before broad exploration and do not redo the broad review.

So this is sufficient:

```text
Address the findings from the review.
```

You should not need:

```text
Address .codex-artifacts/handoffs/pr-34855-review.md
```

### Handoff lifecycle

After all actionable items are completed or proven obsolete:

```bash
python3 .codex/scripts/handoff-status.py consume \
  .codex-artifacts/handoffs/pr-34855-review.md
```

The address-review rule requires Codex to do this automatically when completion is clear.

Consumed handoffs are ignored by normal resolver discovery. New handoffs created by `new-handoff.sh` also become the **active continuation target** for their PR/worktree. Generic continuation prompts use that pointer; consuming the handoff clears it, so an older unrelated open handoff is not silently promoted as the next task.

If implementation is only partial, keep `status: open`.

Manual resolver diagnostics:

```bash
python3 .codex/scripts/resolve-handoff.py --json
```

Manual reopen:

```bash
python3 .codex/scripts/handoff-status.py reopen <handoff.md>
```

## Handoff creation - automatic by instruction

For a report-only PR review or bounded investigation, if actionable findings exist and unresolved GitHub review threads are not already the authoritative record, Codex **MUST** create a handoff before stopping.

PR example:

```bash
.codex/scripts/new-handoff.sh 34855
```

Generic investigation:

```bash
.codex/scripts/new-handoff.sh scheduler-rank-desync
```

The user does not need to request handoff creation explicitly.

## Mutable state location

Runtime artifacts deliberately do **not** live under `.codex/`:

```text
.codex/                    static scripts/templates
.codex-artifacts/          mutable local state
  handoffs/
  goals/
  logs/
```

This matters for the VS Code Codex sandbox, where `.codex/` may be protected/read-only. `.codex-artifacts/` is created as writable local state and excluded through `.git/info/exclude`.

## Large logs - automatic by rule

For a local/downloaded log:

```text
>= 1 MiB OR >= 10,000 lines
```

Codex must:

```text
size check
  -> MUST NOT full-read raw log
  -> .codex/scripts/extract-log-context.py <log>
  -> .codex-artifacts/logs/<name>.focused.txt
  -> inspect focused artifact
  -> narrow raw ranges only if a concrete fact is still missing
```

Normal prompt:

```text
Analyze /tmp/npu-ci.log and find the root cause.
```

No `use the reducer` wording is required.

## Session lifecycle - automatic rule, not automatic session creation

Codex cannot silently move your current conversation into a new user-visible session. The rule therefore tells the agent when to stop and tells you to continue in a new session.

```text
same goal + same strategy -> continue
same goal + new strategy  -> NEW SESSION
new goal                  -> NEW SESSION
```

A strategy reversal includes:

- undoing the approach just implemented;
- changing from broad per-file edits to a centralized implementation;
- restoring upstream behavior after pursuing a different design;
- changing the root-cause hypothesis enough that prior exploration is no longer the right working context.

## Parallel sessions

Use **one active editing-agent session per Git worktree**, regardless of model provider.

If two tasks need to run concurrently, create separate worktrees:

```bash
git worktree add ../sglang-pr34855 <branch>
git worktree add ../sglang-ci-analysis <branch-or-commit>
```

Do not run two editing/review sessions against the same worktree: Git state, local diffs and handoff state can race.

## Search routing - automatic by instruction

```text
exact path/symbol/error -> rg/direct navigation
known PR/commit         -> git show/diff
model-history question  -> model-pr-history skill
unknown concept         -> Semble
known symbol relations  -> Serena (if installed)
```

Once a concrete symbol is identified, semantic discovery should stop unless new evidence requires it.

## Goal artifacts - intentionally explicit

Long performance/kernel loops use:

```text
/plan
/goal <objective>
```

and:

```bash
.codex/scripts/new-goal.sh <slug>
```

Runtime state is written to:

```text
.codex-artifacts/goals/<slug>/
```

Ordinary fixes should not pay this ceremony.

## What should be in the prompt?

Prefer:

```text
Review PR #31320. Report only.
```

```text
Address the review findings.
```

```text
Analyze this NPU CI log and identify the root cause.
```

Avoid repeating:

```text
use rg first; use Semble later; reduce logs; find the handoff; do not rereview...
```

Those rules belong to the repository workflow layer.

## Multi-model routing - automatic by CLI policy

`ai-task` adds a deterministic model-routing layer before a session starts. It chooses among configured `local`, `cheap`, and `strong` OpenCode tiers or a Codex profile based on the task kind. Unconfigured external tiers are skipped. For review, verification, Ascend/NPU, distributed, kernel, performance, and deep-reasoning task classes, the selected primary backend is always tried first. When that primary is Codex, the matching hard/xhigh Codex profile is used; when the primary is external, that exact backend remains first and Codex is available only when explicitly enabled as a fallback.

This is routing, not automatic correctness escalation. If an external worker actually starts and cannot solve the task, preserve its useful evidence in a handoff and escalate deliberately rather than silently retrying progressively more expensive models.

See [Multi-model routing](MULTI_MODEL.md).
