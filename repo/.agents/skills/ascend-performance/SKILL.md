---
name: ascend-performance
description: Run a controlled SGLang Ascend performance investigation and delegate profile collection/analysis or op benchmarking to dedicated Ascend skills.
---
# Ascend performance

Record hardware/count, CANN, torch, torch_npu, sgl-kernel-npu, SGLang commit, model, dtype/quant, TP/DP/EP, graph/eager, backend path, ISL/OSL/concurrency/batch/warmup. HARD STOP if baseline/candidate differ unexpectedly or if the candidate silently uses another path.

Use specialized leaf skills for profiling collection, analysis, anomaly investigation, operator benchmarking, or HCCL. Do not ask all profiling skills to analyze the same evidence in parallel.

Classify bottleneck: host/scheduler, kernel compute, bandwidth, launch overhead, graph break/capture, HCCL, MoE dispatch/combine, synchronization, allocator/memory. Optimize in order: remove redundant work -> synchronization -> allocation -> graph capture -> existing optimized op -> fusion -> new custom kernel.

One round = one hypothesis + one scoped change + correctness + identical benchmark + artifact record. A microbenchmark speedup is not an E2E SGLang claim.
