# CODEX + SGLANG / ASCEND - Daily Rules

**You describe the engineering objective. Hooks + repo rules handle the workflow.**

## Daily start

**Default UI:** `cd ~/code/sglang && code .` -> confirm **WSL: Ubuntu** -> Codex sidebar -> new local session.

## First decision

- **Same goal + same strategy** -> continue.
- **Same goal + new strategy** -> **NEW SESSION**.
- **New goal** -> **NEW SESSION**.
- **Parallel work** -> another `git worktree`; one active Codex session per worktree.

## Handoffs - path discovery is automatic

Review/investigation with actionable local findings:

`review -> .codex-artifacts/handoffs/... -> STOP`

New implementation session:

`SessionStart hook -> resolve PR/branch/worktree -> inject handoff path -> read -> re-verify -> patch -> consume`

You normally say only: **“Address the review findings.”**

Do not redo the broad review. When complete, handoff becomes `status: consumed` and is ignored by future discovery.

## Large log - MUST reduce first

If `>= 1 MiB` **or** `>= 10,000 lines`:

`size check -> extract-log-context.py -> .codex-artifacts/logs/*.focused.txt -> inspect focused -> narrow raw ranges only if needed`

**Never full-read/cat the raw log first.**

## Search routing

- Exact symbol/error/path -> `rg`.
- Known PR/commit -> `git show` / `git diff`.
- Model history -> `model-pr-history-knowledge`.
- Unknown concept/location -> **Semble**.
- Known symbol callers/references -> **Serena** (optional).
- Once the symbol is known -> stop broad semantic discovery.

## Model routing

- **Luna / low:** metadata, PR description, docs, mechanical.
- **Terra / medium:** default development.
- **Sol / high:** deep review, hard Ascend correctness, HCCL/NPUGraph/perf.
- **Sol / xhigh:** escalation only.

## Ascend hard gates

Record: `hardware | CANN | torch | torch_npu | sgl-kernel-npu | SGLang commit | graph/eager | dtype/quant | TP/DP/EP | workload | actual backend`.

STOP if baseline/candidate differ unexpectedly or a silent fallback changes backend.

## Do not spend a model turn

Decided `git push/status/fetch/switch` -> terminal.

Do not keep appending “instead / restore / undo the approach” to a long thread: **strategy reversal = new session**.

## STOP checklist

`objective complete? | diff minimal? | validation sufficient? | handoff/Goal state updated?`

**Static workflow:** `.codex/`  
**Writable runtime state:** `.codex-artifacts/`
