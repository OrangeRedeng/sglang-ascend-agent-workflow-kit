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
6. Large local/downloaded log -> size check, then focused reduction before raw-log reading.

Once a concrete symbol is found, stop broad semantic discovery and switch to direct/symbol-aware navigation.
Do not semantic-search an exact identifier when `rg` can answer it directly.
Do not read an entire large file when a narrow range/function is enough.

## Large-log contract - mandatory

Treat a log as large when it is at least **1 MiB** or **10,000 lines**. If size is unknown but the log is clearly large/repetitive, treat it as large.

For a large local or downloaded CI/NPU log:

1. Check size/line count without reading the body (`wc -c`, `wc -l`, `stat`, or equivalent).
2. **MUST NOT** `cat`, `Get-Content`, or otherwise read the whole raw log first.
3. **MUST** run `.codex/scripts/extract-log-context.py <log-file>` first.
4. Read the generated focused artifact under `.codex/logs/`.
5. Read raw-log ranges only when the focused artifact identifies a concrete missing fact/window that requires them.
6. Preserve the original log unchanged.

If a huge log is already present in conversation context, do not quote/replay it or request it again. Work from the available high-signal sections and use a local/downloaded copy with the reducer when further inspection is needed.

## Handoff contract - mandatory when findings are local

Handoffs transfer **decisions and actionable findings**, not the review transcript.

### Produce a handoff

Before ending a report-only PR review or bounded investigation:

- If there are actionable findings/next changes and they are **not already represented by authoritative unresolved GitHub review threads**, **MUST** write a compact handoff to `.codex/handoffs/`.
- For PR review, prefer `.codex/handoffs/pr-<N>-review.md`.
- For a non-PR investigation, use a short descriptive slug such as `.codex/handoffs/scheduler-rank-desync.md`.
- If there are no actionable findings, do not create an empty handoff.
- If GitHub unresolved review threads are the authoritative record, do not duplicate them into a local handoff.

Every handoff must contain only:
- source/PR and reviewed commit when known;
- severity/priority;
- file and symbol;
- root cause/problem;
- exact intended change;
- constraints/non-goals;
- minimal validation;
- unresolved uncertainty only if it affects implementation.

### Consume a handoff

When starting implementation/address-review work:

1. If authoritative unresolved GitHub review threads exist, use them first.
2. Otherwise, if a matching `.codex/handoffs/` file exists or is named in the prompt, **MUST** read it before broad exploration.
3. Re-verify each finding against current HEAD; skip stale/already-fixed items.
4. Implement only the actionable items. **Do not perform another broad PR review.**
5. Re-check each item against the resulting diff and record completion in the handoff when practical.

Do not use `/fork` as a review-to-implementation handoff; a new session + compact handoff is preferred.

## Ascend NPU

For Ascend/NPU, torch_npu, HCCL, NPUGraph, `python/sglang/srt/hardware_backend/npu/`, or `sgl-kernel-npu`, start with `sglang-ascend` and load only the leaf skill that owns the question.

Core leaf skills installed by the workspace setup:
- `ascend-torch-npu` - torch_npu API/runtime/streams/memory/graph/formats;
- `ascend-pytorch-profiling-collection` - collect profiling correctly;
- `ascend-profiling-analysis` - analyze profiling artifacts;
- `ascend-npu-op-benchmark` - isolated operator/kernel benchmark;
- `official-npu-adapter-reviewer` - GPU/CUDA -> NPU adaptation review;
- `official-ascend-profiling-anomaly` - unexplained profiling anomalies;
- `official-hccl-test` - HCCL communication tests.

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
