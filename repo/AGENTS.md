# SGLang + Ascend local agent workflow

## Scope

This file is the shared project instruction layer for GitHub Copilot Chat (Codex Bridge + GLM) and the official OpenAI Codex fallback. Keep one source of truth: `AGENTS.md`, `.agents/skills/`, and `.codex-artifacts/`.

## Session discipline

- One objective per session unless the task is an explicit long-running Goal.
- Same goal + same strategy may continue; a materially different strategy starts a new session.
- One active editing agent per Git worktree. Use another `git worktree` for parallel editing.
- PR review is report-only unless editing is explicitly requested.
- Conflict resolution means conflicts only.
- Stop after the requested objective and minimal validation are complete.

## Retrieval budget

Measured history shows tool round-trips dominate input-token cost once large-log and giant-diff mistakes are controlled.

- Around 32 tool calls: stop broad discovery and consolidate evidence.
- Around 44 tool calls: checkpoint. For normal work, finish or write/update a handoff and rotate to a new session. For an active Goal, persist the experiment round first.
- Re-reading unchanged handoffs or `SKILL.md` files should be exceptional.
- Never bypass the budget by requesting a giant diff or raw multi-megabyte log in one tool call.

## Search and review

1. Exact path/symbol/error -> `rg` / direct navigation.
2. Known commit/PR -> `git show`, narrow `git diff`, bounded history.
3. Broad PR review -> first build one bounded packet:

```bash
python3 .codex/scripts/workflow-review-packet.py --base origin/main
# or
python3 .codex/scripts/workflow-review-packet.py --pr <N>
```

Then expand only around a concrete invariant, caller, or regression hypothesis.

## Large logs

Treat >=1 MiB or >=10,000 lines as large. Do not read the full log first.

```bash
python3 .codex/scripts/extract-log-context.py <log>
```

Inspect the bounded artifact first. Use `--expand <signature-id>` only for a concrete missing fact.

## Handoffs and Goals

Mutable workflow state lives under `.codex-artifacts/`; `.codex/` contains static scripts/templates.

Before broad implementation/fix/address-review work, resolve a relevant handoff:

```bash
python3 .codex/scripts/resolve-handoff.py --json --prompt "<task>"
```

Archive stale open handoffs with:

```bash
workflow-handoffs gc --older-than-hours 48
```

Long performance/kernel work uses `.codex-artifacts/goals/<goal>/` and numeric `results.jsonl` entries via `workflow-exp record`.

## Ascend/NPU work

Start with `sglang-ascend`; load only the leaf skill that owns the question. Use `sglang-ascend-kernel-dev` for operator/kernel implementation and `sglang-npu-perf-experiment` for iterative optimization.

Before version-sensitive diagnosis record hardware/device generation, NPU count, CANN, PyTorch, torch_npu, sgl-kernel-npu, SGLang commit, graph/eager mode, dtype/quantization, TP/DP/EP, HCCL/network configuration, model/workload, and actual backend path. Do not mechanically port CUDA/NCCL/stream/layout assumptions to Ascend/HCCL/NPUGraph.

For performance work, one round = one hypothesis + one scoped change + correctness + identical benchmark + artifact update. A microbenchmark win is not an end-to-end SGLang result.

## Tests and Git

- Do not create or modify tests by default. Add them only when explicitly requested, required by CI/review, or needed as a real regression guard.
- Do not commit or push unless explicitly requested.
- Pure push/status/fetch/switch belongs in the terminal when no reasoning is required.

## Model/UI split

- Primary UI: GitHub Copilot Chat. Use Codex Bridge for ChatGPT/Codex models and the dedicated GLM provider for BigModel China Coding Plan.
- Switch model and reasoning in the Copilot Chat model picker; keep Codex and GLM quota indicators visible in the status bar.
- Official OpenAI Codex remains a fallback when native Codex hooks/runtime behavior is required. Codex hooks do not execute when a Codex model is used through Copilot Chat.
- Both providers share this `AGENTS.md` and `.agents/skills/`.
- Kilo, OpenCode, Semble, Serena, and Codex-native GLM routing are intentionally not part of this workflow.
