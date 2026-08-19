# CODEX + SGLANG / ASCEND - Quick Reference

**Goal:** reduce unnecessary turns and context without losing engineering continuity.

## Before every prompt - take 15 seconds

1. **New objective?** Yes -> new session. Do not carry the old transcript.
2. **Review -> implementation?** Write a compact handoff -> new session. Do not use `/fork`.
3. **One long performance/kernel goal?** `/plan -> /goal` + artifact ledger. Chat = working memory.
4. **Just a Git command?** `push/status/fetch/switch` -> terminal, not the model.

## 1. Session lifecycle

- **Atomic:** conflict, comment, CI fix, description -> new short session -> STOP.
- **Handoff:** review/investigation -> `.codex/handoffs/...` -> new implementation session.
- **Goal:** evidence-driven performance/kernel loop -> `.codex/goals/...` + artifact ledger.
- **Same goal:** `/compact` as history grows; `/side` for a short detour; `/fork` only for alternatives.

## 2. Model routing

- **Luna / low:** PR description, metadata, docs, mechanical edits.
- **Terra / medium:** default - conflicts, comments, ordinary bugs and refactors.
- **Sol / high:** deep review, hard feature, Ascend correctness, HCCL/NPUGraph/performance root cause.
- **Sol / xhigh:** escalate only after focused investigation fails.
- **Rule:** do not start routine work on Sol/xhigh "just in case".

## 3. Search routing

- Exact symbol/error/path -> `rg`.
- Known commit/PR -> `git show`, `git diff`, bounded `git log`.
- Model history -> `model-pr-history-knowledge`.
- Unknown concept/location -> Semble.
- Callers/references -> Serena, only when actually needed.
- Huge log -> reduce/grep context first; read the full log only on demand.

## 4. Do not spend an LLM turn

- `git push/status/fetch/switch` and a simple `pull`, when the decision is already made -> terminal.
- Do not send `push`, `continue`, or `update` as standalone prompts in a long thread.
- Do not do cleanup/docs/comments/refactors "while you are here" after the current objective is complete.
- Do not create or modify tests by default; only for an explicit request, review/CI requirement, or a real regression guard.
- UserPromptSubmit guard blocks a standalone `push` before a model call.

## 5. Ascend / NPU hard gates

Before diagnosis/benchmarking, record:

`hardware | CANN | torch | torch_npu | sgl-kernel-npu | SGLang commit | graph/eager | dtype/quant | TP/DP/EP | workload | backend path`

- STOP the benchmark if baseline/candidate differ by more than the tested variable or there is a silent fallback.
- Do not mechanically transfer CUDA/NCCL/graph/stream/layout/dtype assumptions to NPU.
- Kernel microbenchmark win != E2E SGLang win; confirm with a real-model benchmark.

## 6. Finish + quick commands

Before STOP: objective complete? diff minimal? validation sufficient? caveats recorded?

- `cxl` Luna | `cx` Terra | `cxh` Sol/high | `cxx` Sol/xhigh
- `/review` `/side` `/compact` `/goal` `/usage weekly` `/status`

**Core rule:** Chat = working memory. Git = code state. Handoff/Goal files = durable memory. **NEW OBJECTIVE = NEW SESSION.**
