# CODEX + SGLANG / ASCEND - Daily Rules

**You describe the engineering objective. Repo rules/skills handle the workflow.**

## Daily start

**Default UI:** `cd ~/code/sglang && code .` -> confirm **WSL: Ubuntu** -> Codex sidebar -> new local session.

`cx/cxh/...` are independent CLI sessions, not a way to connect Codex to VS Code.

## Start here - 4 questions

1. **New objective?** -> New session.
2. **Review found actionable local issues?** -> Handoff is written before STOP; implementation uses a new session.
3. **Large local/downloaded log?** -> Reducer runs before any full raw-log read.
4. **Just Git plumbing?** `push/status/fetch/switch` -> terminal, not a model turn.

## Automatic by repo rule (no extra prompt text)

### LARGE LOG - MUST REDUCE FIRST

If `>= 1 MiB` **or** `>= 10,000 lines`:

`size check -> extract-log-context.py -> .codex/logs/*.focused.txt -> inspect focused artifact -> raw ranges only if needed`

**Never:** `cat` / full `Get-Content` / full raw-log read first.

### REVIEW -> HANDOFF -> NEW SESSION

If report-only review/investigation finds actionable issues and GitHub threads are not already authoritative:

`review -> .codex/handoffs/... -> STOP -> new implementation session -> re-verify -> patch`

Implementation **does not redo the broad review**.

Handoff stores only: `severity | file/symbol | root cause | intended change | constraints | validation`.

## Search routing

- Exact symbol/error/path -> `rg`.
- Known PR/commit -> `git show` / `git diff`.
- Model optimization history -> `model-pr-history-knowledge`.
- Unknown concept/location -> **Semble**.
- Known symbol + callers/references -> **Serena** (optional).
- Once a concrete symbol is found -> stop broad semantic discovery.

## Session + model routing

- **Luna / low:** metadata, PR description, docs, mechanical edits.
- **Terra / medium:** default development, conflicts, comments, normal bugs/refactors.
- **Sol / high:** deep review, hard Ascend correctness, HCCL/NPUGraph/perf root cause.
- **Sol / xhigh:** escalation only after focused high-effort work fails.

`review -> handoff -> new implementation session` | long perf/kernel loop -> `/plan` + `/goal` + `.codex/goals/`

## Ascend / NPU hard gates

Record before version-sensitive diagnosis/benchmark:

`hardware | CANN | torch | torch_npu | sgl-kernel-npu | SGLang commit | graph/eager | dtype/quant | TP/DP/EP | workload | actual backend`

STOP if baseline/candidate differ by unrelated variables or a silent fallback changes the backend.

CUDA/NCCL/graph/stream assumptions are **not** automatically valid for Ascend/HCCL/NPUGraph.

Kernel microbenchmark win != E2E SGLang win.

## STOP rules

Before ending: `objective complete? | diff minimal? | validation sufficient? | handoff/Goal updated if needed?`

Do not add unrelated cleanup/docs/tests/refactors after the objective is solved.
Tests only when explicitly requested, required by review/CI, or needed as a real regression guard.

**VS Code extension:** Terra/medium default; switch to Sol/high in UI for hard work.

**CLI optional:** `cxl` Luna | `cx` Terra | `cxh` Sol/high | `cxx` Sol/xhigh

**Chat = working memory. Git = code state. Handoff/Goal files = durable memory. NEW OBJECTIVE = NEW SESSION.**
