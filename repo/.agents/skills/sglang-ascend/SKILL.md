---
name: sglang-ascend
description: Route SGLang Ascend NPU work to the correct SGLang, torch_npu, profiling, HCCL, Triton, AscendC, or custom-op workflow.
---
# SGLang Ascend/NPU router

Use for `hardware_backend/npu`, `torch_npu`, HCCL, NPUGraph, Ascend attention, NPU quantization/LoRA, `sgl-kernel-npu`, NPU CI/model support.

## First: capture the compatibility baseline

For version-sensitive diagnosis record hardware/device, CANN, torch, torch_npu, sgl-kernel-npu version/commit, SGLang commit, eager/graph mode, dtype/quantization, TP/DP/EP/HCCL and exact workload/backend path.

Use the versions pinned by the target branch/container/CI. Do not upgrade dependencies just because a newer release exists.

## Then route by ownership

- SGLang orchestration / backend dispatch -> SGLang code + relevant upstream `.claude` rule/skill.
- `torch_npu` API, memory, streams/events, graph, formats or framework contract -> `ascend-torch-npu` if installed.
- collect PyTorch/NPU profiling -> `ascend-pytorch-profiling-collection` if installed.
- analyze profiling artifacts -> `ascend-profiling-analysis` if installed.
- single-op benchmark -> `ascend-npu-op-benchmark` if installed.
- GPU/CUDA -> NPU adaptation review -> `official-npu-adapter-reviewer` if installed.
- unexplained NPU profiling anomaly -> `official-ascend-profiling-anomaly` if installed.
- HCCL communication validation/performance -> `official-hccl-test` if installed.
- custom PyTorch operator integration -> optional `ascend-opplugin` skill if installed.
- Triton-Ascend kernel work -> optional Triton skill only for the current task.
- AscendC kernel work -> optional AscendC skill only for the current task.
- optimized SGLang custom kernel implementation -> inspect `sgl-kernel-npu` before changing generic SGLang code.

Do not load every NPU skill at once. Use the smallest leaf skill that owns the question.

Do not mechanically translate CUDA/NCCL/graph/stream/layout/dtype assumptions to Ascend/HCCL/NPUGraph. Prefer backend-local changes and preserve other backends.
