---
name: sglang-ascend-kernel-dev
description: Route SGLang Ascend kernel implementation to the correct torch_npu, sgl-kernel-npu, CANN/AscendC, Triton, PyPTO or TileLang workflow with correctness and performance gates.
---
# SGLang Ascend kernel development

Use this skill when the task crosses from Python/backend orchestration into kernel/operator implementation.

1. Capture hardware generation, CANN, PyTorch, torch_npu, SGLang/sgl-kernel-npu commits, dtype/quantization, shapes/layout, graph/eager mode and the real workload.
2. Identify ownership before writing code: existing torch_npu op, op-plugin/custom op, sgl-kernel-npu, AscendC, Triton-Ascend, PyPTO, TileLang, or another CANN path.
3. Search for an existing optimized primitive first. Prefer reuse/fusion over a new custom kernel when it preserves semantics and performance.
4. Load only the smallest matching leaf skills. CANNBot architecture/env/tiling/API/debug/profiling skills are preferred for CANN-specific implementation. KernelHive generator/optimizer are experimental helpers and require their evaluator/paths to be explicitly configured before use.
5. Establish a Torch/reference semantic oracle and boundary cases before optimization.
6. Implement the smallest kernel change; do not move computation into Python/model bindings to fake a kernel implementation.
7. Validate compile -> correctness -> representative shapes/dtypes -> performance. Keep baseline/candidate environments identical.
8. For iterative performance work, use `sglang-npu-perf-experiment` and a Goal ledger. A microbenchmark win is not an end-to-end SGLang claim.
9. If a kernel path cannot be executed on the current host, produce a runnable remote-host validation command instead of guessing.
