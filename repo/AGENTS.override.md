# SGLang local Codex workflow

The upstream repository's agent conventions live in `.claude/rules/` and `.claude/skills/`.
Load only the rules/skills relevant to the touched component; do not dump all of them into context.

## Scope discipline

- One objective per session unless this is a controlled evidence-driven Goal.
- PR review means report-only unless the prompt explicitly asks to edit.
- Conflict resolution means conflicts only; do not also refactor, address unrelated comments, or update docs.
- Address-review work means actionable feedback only.
- Stop when the requested objective and minimal validation are complete.

## SGLang rules

- For Python changes, consult `.claude/rules/general-code-style.md` when relevant.
- Before modifying a component covered by `.claude/rules/modify-component-must-read.md`, read it and only the referenced skill/rule.
- Before adding/modifying tests, read `.claude/rules/unit-test-admission.md`.
- Repository-specific rules override generic personal preferences.

## Search strategy

1. Exact path/symbol/error -> `rg` / direct file navigation.
2. Known commit/PR -> `git show` / `git diff` / bounded history.
3. Model-specific historical question -> model-history skill if available.
4. Unknown conceptual implementation location -> Semble.
5. Known symbol and need callers/references -> Serena if installed.
6. Large log -> `.codex/scripts/extract-log-context.py` before full-log reading.

Do not semantic-search an exact identifier when `rg` can answer it directly.
Do not read an entire large file when a narrow range/function is enough.

## Review -> implementation handoff

For Codex-generated review findings, write only actionable items to `.codex/handoffs/`:
- severity;
- file/symbol;
- root cause/problem;
- intended change;
- constraints;
- minimal validation.

Do not carry full review narration into the implementation session.

## Ascend NPU

For Ascend/NPU, torch_npu, HCCL, NPUGraph, `python/sglang/srt/hardware_backend/npu/`, or `sgl-kernel-npu`, start with `sglang-ascend` and load only the leaf skill that owns the question.

Core leaf skills installed by the workspace setup:
- `ascend-torch-npu` — torch_npu API/runtime/streams/memory/graph/formats;
- `ascend-pytorch-profiling-collection` — collect profiling correctly;
- `ascend-profiling-analysis` — analyze profiling artifacts;
- `ascend-npu-op-benchmark` — isolated operator/kernel benchmark;
- `official-npu-adapter-reviewer` — GPU/CUDA -> NPU adaptation review;
- `official-ascend-profiling-anomaly` — unexplained profiling anomalies;
- `official-hccl-test` — HCCL communication tests.

Optional AscendC/Triton/op-plugin skills should be loaded only for tasks that actually touch those layers.

Before version-sensitive diagnosis establish:
- hardware/device generation;
- CANN;
- PyTorch;
- torch_npu;
- sgl-kernel-npu version/commit;
- SGLang commit;
- eager/graph mode;
- dtype/quantization;
- TP/DP/EP/HCCL configuration;
- exact workload and actual backend path.

Do not mechanically port CUDA/NCCL/graph/stream assumptions to Ascend/HCCL/NPUGraph.

## Performance / kernel work

Use fixed baseline and workload. Hard-stop if environment or backend path is not comparable.
One round = one hypothesis + one scoped change + correctness + same benchmark + artifact record.
Kernel-local speedup is not an E2E SGLang claim until a real serving workload validates it.

## Tests

Do not create/modify tests by default. Do so only for explicit request, explicit review/CI requirement, or a real regression guard. Follow upstream unit-test admission rules.

## Git

Do not push or commit unless explicitly requested by the current prompt. Pure push/status/switch/fetch belongs in the terminal.
