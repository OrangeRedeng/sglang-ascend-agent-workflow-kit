---
name: sglang-npu-perf-experiment
description: Run reproducible multi-round SGLang Ascend performance experiments with one hypothesis per round and a persistent Goal ledger.
---
# SGLang NPU performance experiment

Create or reuse `.codex-artifacts/goals/<slug>/` via `.codex/scripts/new-goal.sh <slug>`. A new Goal gets `.active`, `results.jsonl`, Markdown experiment templates and an automatic environment capture attempt.

Before the first comparison record hardware/count, CANN, torch, torch_npu, SGLang and sgl-kernel-npu commits, model, quantization/KV cache, TP/DP/EP, graph mode, backend path, launch command, benchmark command, warmup/run count and target metrics.

Each round has exactly one primary hypothesis and one scoped candidate change. Record human reasoning in `experiments/NNN.md`, and append machine-readable metrics with:

```bash
workflow-exp record <goal> --id <N> --baseline-sha <sha> --candidate-sha <sha> \
  --command '<exact benchmark command>' --metric ttft_ms=... --metric prefill_tps=... \
  --decision keep|reject|inconclusive
```

Reject a result when environment/workload/backend changed unexpectedly. Preserve failed directions so they are not retried without new evidence. `workflow-exp best <goal> --metric <name> [--lower-is-better]` can identify the best non-rejected recorded result without rereading every experiment transcript.

Prefer measurements in this order: original serving workload -> targeted profiler -> isolated operator microbenchmark. Use the microbenchmark to explain an E2E result, not replace it.

For long-context/MoE experiments report TTFT/prefill separately from decode/ITL/throughput, and record TP/EP routing/communication topology. Do not claim speedup from a single run.

When the session governor reaches its checkpoint threshold, persist the current round and next step to the Goal, then prefer a new Codex session for the next round instead of carrying a growing conversation indefinitely.
