# SGLang + Ascend daily rules

- New objective or materially new strategy -> new session.
- One editing agent per Git worktree.
- Large log >=1 MiB or >=10,000 lines -> reduce before raw read.
- Implementation -> resolve/read applicable handoff first.
- Ascend version-sensitive work -> capture hardware/CANN/torch/torch_npu/SGLang/parallelism/workload/backend baseline.
- Performance -> one hypothesis + one change + correctness + identical benchmark + artifact.
- OpenAI remains default Codex provider; GLM uses isolated profiles.
- `balanced`: routine work may use GLM; hard NPU/perf/kernel/verify stays OpenAI hard by default.
- Kernel work -> `sglang-ascend-kernel-dev`; multi-round optimization -> `sglang-npu-perf-experiment`.
- Do not push/commit unless explicitly requested.
