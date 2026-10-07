# SGLang local multi-model workflow

## Project priority - SGLang + Ascend correctness

This workflow exists first to make SGLang + Ascend engineering correct, reproducible, and efficient. Provider choice and subscription cost are subordinate. Never bypass runtime/version/backend/profiling/benchmark gates to use a cheaper model.

Codex is the preferred harness. OpenAI is the default Codex provider. GLM Coding Plan is an optional Codex provider selected by profile/router; OpenCode is optional and only needed for separate external worker tiers. The engineering contract is identical across providers.

## Scope and session discipline

- One objective per session unless this is a controlled Goal.
- Same goal + same implementation strategy -> continue.
- Same goal + a materially different implementation strategy -> new session.
- New objective -> new session.
- Use one active editing-agent session per Git worktree. Parallel editing requires another `git worktree`.
- PR review is report-only unless editing is explicitly requested.
- Conflict resolution means conflicts only.
- Stop after the objective and minimal validation are complete.

### Measured retrieval budget

Historical rollout analysis showed that tool-call round trips, not answer verbosity, became the dominant input-token cost after the original workflow improvements. The installed `PostToolUse` governor tracks this per `session_id` without blocking completed tools.

- Around 32 tool calls: consolidate evidence; stop broad discovery and reuse already-read context.
- Around 44 tool calls: checkpoint. For normal work, finish or write/update a handoff and continue the same strategy in a new session. For an active Goal, persist the experiment round and rotate sessions when practical.
- Re-reading an unchanged handoff or `SKILL.md` should be exceptional. Reuse extracted facts unless a specific missing section is needed.
- Do not defeat the governor by batching giant diffs/logs into one call. Retrieval must remain bounded.

## Provider routing

`ai-task` separates harness/provider choice from engineering rules.

- `AI_PRIMARY_HARNESS=codex` keeps the OpenAI/Codex extension as the daily UI.
- `AI_CODEX_ROUTING=balanced` uses GLM for bounded/general coding when configured while keeping hard Ascend/NPU/distributed/performance/kernel/verification classes on the OpenAI hard profile.
- `AI_CODEX_ROUTING=openai` always uses OpenAI Codex profiles.
- `AI_CODEX_ROUTING=glm` prefers GLM profiles when available.
- `local`, `cheap`, and `strong` are optional OpenCode workers. Provider fallback is not semantic verification.
- Explicit `--tier` overrides routing, not engineering gates.

## Mandatory implementation preflight

For code-changing implementation/fix/address-review work, before broad exploration run `python3 .codex/scripts/resolve-handoff.py --json --prompt "<task>"`. Read a selected handoff first, re-verify it against current HEAD, and do not redo the broad review. Consume it only after all actionable items are completed or obsolete.

## Search strategy

1. Exact path/symbol/error -> `rg` / direct navigation.
2. Known commit/PR -> `git show` / `git diff` / bounded history.
3. Unknown conceptual implementation location -> Semble **only if installed and actually useful**.
4. Known symbol needing callers/references -> Serena **only if installed and needed**.
5. Large local/downloaded log -> size check, then `.codex/scripts/extract-log-context.py` before raw-log reading.

Once a concrete symbol is found, stop broad semantic discovery. Semble and Serena are optional because longitudinal workflow data showed no actual calls across the measured corpus.

## PR review retrieval budget

For a broad review, prefer one deterministic first-pass packet:

```bash
python3 .codex/scripts/workflow-review-packet.py --base origin/main
# or
python3 .codex/scripts/workflow-review-packet.py --pr <N>
```

The packet is capped and uses narrow hunks. Start from its changed-file/component index, then expand only around a concrete invariant/caller/regression hypothesis. Do not regenerate a giant multi-file diff. Maintain a short coverage checklist for large reviews.

## Large-log contract - mandatory

Treat >=1 MiB or >=10,000 lines as large. Do not `cat` the full log first. Run `.codex/scripts/extract-log-context.py <log>`, inspect the bounded focused artifact, then read narrow raw ranges only for a concrete missing fact. The reducer clusters repeated error signatures and defaults to a ~32 KiB / 400-line cap. If a specific signature needs more context, rerun with `--expand <signature-id>`. Preserve the original log.

## Handoffs and durable state

Report-only review/investigation with actionable findings must create a compact handoff under `.codex-artifacts/handoffs/` unless authoritative unresolved GitHub review threads already hold those findings. Handoffs contain severity, file/symbol, root cause, exact intended change, constraints, minimal validation, and material uncertainty only.

Mutable state lives under `.codex-artifacts/`; `.codex/` contains static scripts/templates. Long performance/kernel work uses `.codex-artifacts/goals/<goal>/`.

Stale open handoffs are not normal active context. Periodically run:

```bash
workflow-handoffs gc --older-than-hours 48
```

This marks stale open handoffs `archived` and clears matching active pointers without deleting audit history.

## Ascend/NPU routing

Start with `sglang-ascend`; load only the leaf skill that owns the question. For kernel/operator implementation route through `sglang-ascend-kernel-dev`. For iterative optimization use `sglang-npu-perf-experiment`.

Core sources include `torch_npu`, profiling, op benchmark, HCCL/adaptation skills. Optional kernel sources include CANNBot, AscendC/Triton/op-plugin skills, and KernelHive. KernelHive `ascend-kernel-optimization` is experimental and must not be used until its evaluator/output paths and LLM settings are adapted to the current environment.

Before version-sensitive diagnosis record hardware/device generation, NPU count, CANN, PyTorch, torch_npu, sgl-kernel-npu, SGLang commit, graph/eager mode, dtype/quantization, TP/DP/EP, HCCL/network configuration, model/workload, and actual backend path. Do not mechanically port CUDA/NCCL/stream/graph/layout assumptions to Ascend/HCCL/NPUGraph.

## Performance/kernel work

Hard-stop when baseline and candidate differ unexpectedly in runtime, hardware, precision, parallelism, graph state, workload, or backend path. One round = one hypothesis + one scoped patch + correctness + identical benchmark + artifact update. Prefer remove redundant work -> synchronization -> allocation/reuse -> graph capture -> existing optimized op -> fusion -> new custom kernel. A microbenchmark win is not an end-to-end SGLang result.

For a Goal, record numeric results in `results.jsonl` with `workflow-exp record`; preserve exact launch/benchmark commands and candidate/baseline SHAs. Before crossing to a new implementation strategy, checkpoint the Goal and start a new agent session.

## Tests and Git

Do not create or modify tests by default; only when explicitly requested, required by review/CI, or needed as a real regression guard. Do not commit or push unless explicitly requested. Pure push/status/fetch/switch belongs in the terminal.
