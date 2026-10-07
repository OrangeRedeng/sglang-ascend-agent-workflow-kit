# Ascend / NPU workflow

This is the primary domain workflow of the project. Model/provider routing is subordinate to SGLang + Ascend correctness.

## Compatibility baseline

Before version-sensitive diagnosis or benchmarking record hardware/device generation, NPU count, CANN, PyTorch, `torch_npu`, `sgl-kernel-npu` commit/version, SGLang commit, graph/eager mode, dtype/quantization, TP/DP/EP, HCCL/network settings, model/workload, and actual backend path.

Hard-stop a comparison when any of these differ unexpectedly or a silent fallback changes the path.

## Core routing

- `sglang-ascend`: top-level ownership router.
- `ascend-torch-npu`: torch_npu API/runtime/stream/memory/graph/layout semantics.
- profiling collection/analysis leaf skills.
- operator benchmark skill.
- official NPU adapter, profiling anomaly and HCCL skills.
- `sglang-ascend-kernel-dev`: kernel/operator implementation router.
- `sglang-npu-perf-experiment`: controlled multi-round optimization.

## CANNBot

The full profile links curated CANNBot skills when available: `npu-arch`, API best practices/docs search, environment check, tiling design, precision/runtime/crash/sync debugging, code review, direct invoke template, profiling and precision standards.

## KernelHive

The full profile links `ascend-kernel-generator`, `ascend-npu-migration`, and `ascend-doc-update`. `ascend-kernel-optimization` is intentionally excluded from automatic linking until its environment-specific evaluator/output/LLM defaults are adapted locally.

## Performance workflow

Optimize in the order: redundant work -> synchronization -> allocation/reuse -> graph capture -> existing optimized op -> fusion -> new custom kernel. One round = one hypothesis + one scoped change + correctness + identical benchmark + artifact update. A kernel-local win is not an E2E serving result until the real workload confirms it.

Never mechanically port CUDA/NCCL/stream/graph/layout assumptions to Ascend/HCCL/NPUGraph.
