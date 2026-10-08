# Ascend / NPU workflow

Before version-sensitive diagnosis capture device generation/count, CANN, PyTorch, torch_npu, SGLang SHA, sgl-kernel-npu SHA when relevant, graph/eager mode, dtype/quantization, TP/DP/EP, HCCL/network settings, model/workload, and actual backend path.

Use `sglang-ascend` as the entry skill, `sglang-ascend-kernel-dev` for kernel/operator implementation, and `sglang-npu-perf-experiment` for iterative performance work.

One performance round should contain one hypothesis, one scoped change, correctness evidence, an identical benchmark, and an artifact update. Compare TTFT/prefill/decode separately. A microbenchmark improvement is not an end-to-end result.

CANNBot is installed in Standard for selected kernel/debug/profiling skills. KernelHive remains Full-only/experimental because some upstream workflows assume their own evaluator/output paths.
