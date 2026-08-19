# Automation and enforcement

This page answers a practical question: **what happens automatically, and what still needs to be written in the prompt?**

The short answer is: routine prompts should describe the engineering objective, not the workflow machinery. The repository rules and skills decide how to search, when to reduce logs, and when to create/consume handoffs.

## Three levels of automation

| Level | Meaning | Examples in this kit |
|---|---|---|
| **Hard-enforced** | Code/hook blocks or performs the behavior before/without a model turn | standalone `git push` prompt guard |
| **Instruction-enforced** | `AGENTS.override.md` / `SKILL.md` says the model **MUST** follow the behavior | large-log reduction, handoff creation/consumption, search routing |
| **Manual / optional** | A human chooses to enable or invoke the capability | Serena installation, optional AscendC/Triton skills |

Instruction-enforced behavior is automatic in normal Codex use, but it is not a shell-level security boundary. The model is responsible for obeying the repo instructions.

## Extension vs CLI

The recommended UI is the Codex VS Code extension in a `WSL: Ubuntu` window. Repository instructions, repo-local skills, handoff/Goal files, and the WSL-side Semble MCP configuration are intended to apply there as well as in CLI sessions.

| Mechanism | VS Code extension | CLI | Notes |
|---|---|---|---|
| `AGENTS.override.md` / repo skills | Yes | Yes | Instruction layer; no prompt boilerplate needed |
| Semble MCP from `~/.codex/config.toml` | Yes, after restart/new session | Yes | Same WSL Codex configuration |
| Large-log reduction rule | Yes | Yes | Instruction-enforced |
| Review handoff create/consume rule | Yes | Yes | Instruction-enforced |
| `cxl/cx/cxh/cxx` aliases | No | Yes | Shell aliases only |
| prompt-guard hook | Client/version dependent | Reference path | Do not rely on it as the only IDE safeguard |

The extension and CLI do **not** share a live conversation. Opening `cx` does not connect that CLI session to the VS Code sidebar.

## Large logs - automatic by rule

You normally write only the task:

```text
Analyze /tmp/npu-ci.log and find the root cause.
```

You do **not** need to add:

```text
Use extract-log-context.py first.
```

Expected flow for a local/downloaded log:

```text
prompt references log
  -> Codex checks file size / line count without reading the body
  -> if >= 1 MiB OR >= 10,000 lines: raw full read is forbidden by rule
  -> .codex/scripts/extract-log-context.py <log>
  -> .codex/logs/<name>.focused.txt
  -> Codex reads focused artifact
  -> raw log is read only in narrow ranges when a concrete fact is missing
```

The reducer now writes the focused log to a file by default instead of printing hundreds/thousands of reduced lines into the model tool output.

Manual use is still available:

```bash
cd ~/code/sglang
.codex/scripts/extract-log-context.py /tmp/npu-ci.log
```

Typical output:

```text
Focused log: /home/user/code/sglang/.codex/logs/npu-ci.log.focused.txt
Source: 7342812 bytes, 68144 lines
Matches: 407 total, 120 included
```

Then inspect the focused file, not the raw multi-megabyte log.

### What counts as "large"?

The default contract is:

```text
>= 1 MiB OR >= 10,000 lines
```

A smaller but extremely repetitive/profiler-style log may still be reduced first.

## Handoffs - automatic by rule

A handoff exists to move **actionable state** to a new session without carrying the review/investigation transcript.

### Review session

A normal prompt can remain short:

```text
Review PR #31320. Report only.
```

If Codex finds actionable issues and those issues are not already authoritative unresolved GitHub review threads, the PR-review skill **must** create:

```text
.codex/handoffs/pr-31320-review.md
```

before the review session ends.

If the review finds no actionable issue, no empty handoff is created.

If the authoritative findings already live in GitHub unresolved review threads, those threads remain the source of truth and a duplicate local handoff is not required.

### Implementation session

A new session can then receive a short objective:

```text
Address the findings from PR #31320 review.
```

Expected flow:

```text
new implementation session
  -> unresolved GitHub review threads if authoritative
     OR matching .codex/handoffs/pr-31320-review.md
  -> re-verify findings against current HEAD
  -> implement only actionable findings
  -> targeted validation
  -> re-check findings against diff
  -> stop
```

The implementation session must **not** redo the broad PR review just to reconstruct context.

### Non-PR investigation handoff

For a bounded investigation where implementation is intentionally deferred:

```bash
.codex/scripts/new-handoff.sh scheduler-rank-desync
```

creates:

```text
.codex/handoffs/scheduler-rank-desync.md
```

Numeric arguments retain the PR convention:

```bash
.codex/scripts/new-handoff.sh 31320
# -> .codex/handoffs/pr-31320-review.md
```

## Search routing - automatic by instruction

You normally ask the engineering question, for example:

```text
Find why the NPU attention backend is selected incorrectly during decode.
```

The repo rule routes retrieval roughly as follows:

```text
exact symbol/path/error -> rg
known PR/commit         -> git show/diff
model history           -> model-pr-history-knowledge
unknown concept         -> Semble
known symbol relations  -> Serena (if installed)
```

You only need to name a tool explicitly when the method itself is part of the task, for example "use Serena to enumerate all callers before editing".

## Goal artifacts - model-guided, intentionally explicit

Long performance/kernel loops should use a Goal and durable ledger. This is not forced for ordinary fixes because it would create unnecessary ceremony.

Use it when the task is genuinely iterative:

```text
/plan
/goal <objective>
```

and create the artifact structure with:

```bash
.codex/scripts/new-goal.sh <goal-slug>
```

## What should be in your prompt?

Prefer this:

```text
Analyze the attached NPU CI log and identify the root cause.
```

```text
Review PR #31320. Report only.
```

```text
Address the findings from PR #31320 review.
```

Avoid repeating infrastructure instructions such as:

```text
Use rg first, then Semble, reduce large logs, create a handoff, do not reread the review...
```

Those policies belong in the repository rules/skills and are already encoded there.
