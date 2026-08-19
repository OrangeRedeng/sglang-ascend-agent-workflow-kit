---
name: ascend-performance
description: Run a controlled SGLang Ascend performance investigation and delegate profile collection/analysis or op benchmarking to dedicated Ascend skills.
---
# Ascend performance

## Preflight

Record hardware/count, CANN, torch, torch_npu, sgl-kernel-npu, SGLang commit, model, dtype/quant, TP/DP/EP, graph/eager, backend path, ISL/OSL/concurrency/batch/warmup.

**HARD STOP** if baseline/candidate differ unexpectedly in any of these or if the candidate silently uses another/fallback path.

## Use specialized leaf skills

- Need a profile -> use `ascend-pytorch-profiling-collection` when installed.
- Have profile artifacts -> use `ascend-profiling-analysis` when installed.
- Profile looks inconsistent/unexplained -> use `official-ascend-profiling-anomaly` when installed.
- Need one operator/kernel timing -> use `ascend-npu-op-benchmark` when installed.
- Suspect HCCL -> use `official-hccl-test` when installed.

Do not ask all profiling skills to analyze the same evidence in parallel.

## Investigation loop

Classify bottleneck: host/scheduler, kernel compute, bandwidth, launch overhead, graph break/capture, HCCL, MoE dispatch/combine, synchronization, allocator/memory.

Optimize in order: remove redundant work -> synchronization -> allocation -> graph capture -> existing optimized op -> fusion -> new custom kernel.

One round = one hypothesis + one scoped change + correctness + identical benchmark + artifact record.

A microbenchmark speedup is not an E2E SGLang claim. Confirm with the fixed real serving workload before declaring success.
