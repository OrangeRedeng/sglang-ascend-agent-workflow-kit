# Ascend / NPU workflow

The repository adds a thin SGLang-specific routing layer over existing SGLang, Ascend, and `torch_npu` skills. The goal is to load the smallest relevant expert workflow instead of putting every NPU rule into every session.

## Compatibility baseline

Before version-sensitive diagnosis or benchmarking, record:

```text
hardware/device generation
NPU count
CANN
PyTorch
torch_npu
sgl-kernel-npu commit/version
SGLang commit
graph/eager mode
dtype / quantization
TP / DP / EP
HCCL/network configuration
model/workload
actual backend path
```

Do not upgrade CANN or `torch_npu` merely because a newer release exists. Use the versions required by the branch, CI image, container, or target Ascend host.

## Core routing

The workspace setup links selected leaf skills into `sglang/.agents/skills/`:

```text
SGLang orchestration/backend dispatch
  -> sglang-ascend + current SGLang rules

torch_npu API/runtime/stream/memory/graph/format semantics
  -> ascend-torch-npu

collect PyTorch/NPU profile
  -> ascend-pytorch-profiling-collection

analyze profile artifacts
  -> ascend-profiling-analysis

single operator/kernel benchmark
  -> ascend-npu-op-benchmark

GPU/CUDA -> NPU adaptation review
  -> official-npu-adapter-reviewer

unexplained profiling anomaly
  -> official-ascend-profiling-anomaly

HCCL correctness/performance
  -> official-hccl-test
```

Do not activate all of them in parallel for one question.

## Optional kernel-specific skills

Only install when a task touches that implementation layer:

```bash
./wsl/04-install-ascend-kernel-skills-optional.sh opplugin
./wsl/04-install-ascend-kernel-skills-optional.sh triton
./wsl/04-install-ascend-kernel-skills-optional.sh ascendc
```

### op-plugin

Use for custom PyTorch/`torch_npu` operator integration.

### Triton-Ascend

Use when actually editing or profiling Triton-Ascend kernels. Do not load Triton development workflows for ordinary Python NPU backend changes.

### AscendC

Use only when the task enters AscendC/CANN custom operator implementation, tiling, kernel compilation, precision validation, or framework integration.

## Regression workflow

1. Establish good/bad commit, suspect PR, or dependency boundary.
2. Inspect changed NPU-relevant files first.
3. Classify ownership: shared SGLang, NPU backend, `torch_npu`, `sgl-kernel-npu`, NPUGraph, HCCL, dependency compatibility, or model adaptation.
4. Check dependency changes before compensating in application code.
5. State a concrete root-cause hypothesis before editing.
6. Make the smallest backend-correct change.
7. Validate the original failing NPU path first.

CUDA can be a semantic reference where contracts should match, but do not mechanically port CUDA/NCCL/stream/graph/layout assumptions to Ascend/HCCL/NPUGraph.

## Performance workflow

Before every comparison, ensure baseline and candidate match on all variables except the tested change.

**Hard stop** when any of these differ unexpectedly:

- unrelated Git commits;
- CANN / PyTorch / `torch_npu`;
- hardware/NPU count;
- dtype/quantization;
- TP/DP/EP;
- graph/eager state;
- warmup/run count/workload;
- attention/backend path;
- silent fallback.

Preferred optimization order:

```text
remove redundant work
-> synchronization
-> allocation/memory reuse
-> graph capture
-> existing optimized op
-> fusion
-> new custom kernel
```

One round = one hypothesis + one scoped patch + correctness + identical benchmark + artifact update.

A microbenchmark win is not an end-to-end SGLang result until the same real serving workload confirms it.

## Profiling

Use the dedicated collection skill before changing profiler flags ad hoc. Analyze generated artifacts with the profiling-analysis skill; use the anomaly skill only when normal analysis does not explain the behavior.

Do not ask several profiler skills to analyze the same artifact in parallel.

## Remote Ascend hosts

Local WSL can remain the development/navigation environment while runtime validation happens on an Ascend server or CI host. Always record the remote environment in `.codex/goals/<goal>/environment.md` so local assumptions do not leak into NPU conclusions.
