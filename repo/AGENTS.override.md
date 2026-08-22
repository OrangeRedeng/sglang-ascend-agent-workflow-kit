# SGLang local multi-model workflow

## Project priority - SGLang + Ascend correctness

This workflow exists first to make SGLang + Ascend engineering correct, reproducible, and efficient. Model-provider choice and token-cost optimization are subordinate to that goal. **MUST NOT** weaken or bypass repository rules, Ascend/`torch_npu` version and runtime preflight, hardware/backend verification, profiling/benchmark comparability gates, or minimal validation in order to use a cheaper/faster model. If required NPU evidence is unavailable, report the uncertainty or move validation to the correct Ascend host/CI environment instead of guessing.

The router selects an execution backend; it does not change the engineering contract. The same relevant `.agents/skills`, handoff/Goal state, search discipline, and Ascend hard gates apply to Codex, OpenCode, self-hosted, and API-backed agents.

The upstream repository's agent conventions live in `.claude/rules/` and `.claude/skills/`.
Load only the rules/skills relevant to the touched component; do not dump all of them into context.

## Scope and session discipline

- One objective per session unless this is a controlled evidence-driven Goal.
- **Same goal + same implementation strategy** -> continue the current session.
- **Same goal + a materially different implementation strategy** -> stop and continue in a **new session**. This includes replacing a many-file fix with a central fix, undoing the just-implemented approach, restoring upstream behavior after pursuing another approach, or changing the root-cause hypothesis.
- **New objective** -> new session.
- Use **one active editing-agent session per Git worktree**. This applies equally to Codex, OpenCode, self-hosted, and API-backed agents. If work must run in parallel, create another `git worktree`.
- PR review means report-only unless the prompt explicitly asks to edit.
- Conflict resolution means conflicts only; do not also refactor, address unrelated comments, or update docs.
- Address-review work means actionable feedback only.
- Stop when the requested objective and minimal validation are complete.

## Multi-model routing

`ai-task` is provider-neutral. The installer records a user-selected primary backend (`codex`, `local`, `cheap`, `strong`, or `none`) and a routing mode (`primary` or `hybrid`). Codex is the default choice offered by the installer, but it is not structurally required.

- `primary` mode: every automatic task goes to the selected primary backend. When Codex is primary, task kind selects lite/default/hard/xhigh Codex profiles.
- `hybrid` mode: bounded task classes may select configured local/cheap/strong workers; the selected primary remains a fallback. Codex participates as a fallback when it is primary or when `AI_ENABLE_CODEX_FALLBACK=1`.
- Explicit overrides (`local-task`, `cheap-task`, `strong-task`, `cx*`, or `ai-task --tier ...`) always bypass automatic selection.

All editing/review agents MUST follow this file and applicable `.agents/skills`, MUST NOT commit/push unless explicitly requested, and MUST use the same `.codex-artifacts/` handoff/Goal/log contracts when the workflow layer is installed. The `.codex/` directory name is retained for compatibility; its scripts/artifacts are model-agnostic unless a file explicitly documents Codex-specific hooks/configuration.

Do not treat provider fallback as semantic verification. If a worker is uncertain, record that uncertainty in the handoff and escalate deliberately.

## Mandatory implementation preflight

For any code-changing implementation/fix/address-review task, **before broad exploration**:

1. Run `python3 .codex/scripts/resolve-handoff.py --json`.
2. If it returns `selected`, **MUST** read that handoff first unless the current task is clearly unrelated.
3. Re-verify its findings against current HEAD; skip stale/already-fixed items.
4. Do **not** redo a broad PR review just to reconstruct context.
5. When every actionable item is completed or proven obsolete, mark the handoff consumed:
   `python3 .codex/scripts/handoff-status.py consume <handoff-path>`.
6. If work is only partially complete, leave the handoff `status: open` and update its actionable state rather than marking it consumed.

When Codex is installed, its `SessionStart` and `UserPromptSubmit` hooks also run this resolver automatically and inject the selected path into context. Other agents use the same preflight explicitly unless their harness provides an equivalent integration.

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

## PR review retrieval budget - mandatory

Broad PR review must be **bounded by changed components**, not by dumping a huge unified diff into context.

1. Start with PR metadata plus `--stat`, `--name-only`, or changed-filename listing.
2. Classify changed files/components and load only their applicable rules/skills.
3. Review per file or per component. Initial diff context should normally be about **20-30 lines per hunk**.
4. **MUST NOT** request multi-file diffs with `--unified=70`, `--unified=80`, or similarly large context as the first review step.
5. Expand source/diff context only around a suspicious hunk, caller, invariant, or regression hypothesis.
6. For very large PRs, maintain a short reviewed-files/checklist artifact rather than repeatedly re-reading the whole diff.
7. Stop retrieval for a component once its changed code paths and relevant callers/invariants are covered.

The goal is complete review coverage with small targeted retrieval, not maximum text ingestion.

## Large-log contract - mandatory

Treat a log as large when it is at least **1 MiB** or **10,000 lines**. If size is unknown but the log is clearly large/repetitive, treat it as large.

For a large local or downloaded CI/NPU log:

1. Check size/line count without reading the body (`wc -c`, `wc -l`, `stat`, or equivalent).
2. **MUST NOT** `cat`, `Get-Content`, or otherwise read the whole raw log first.
3. **MUST** run `.codex/scripts/extract-log-context.py <log-file>` first.
4. Read the generated focused artifact under `.codex-artifacts/logs/`.
5. Read raw-log ranges only when the focused artifact identifies a concrete missing fact/window that requires them.
6. Preserve the original log unchanged.

If a huge log is already present in conversation context, do not quote/replay it or request it again. Work from the available high-signal sections and use a local/downloaded copy with the reducer when further inspection is needed.

## Handoff contract

Handoffs transfer **decisions and actionable findings**, not the review transcript. Mutable runtime state lives in `.codex-artifacts/`; `.codex/` contains only static scripts/templates and may be read-only in the VS Code sandbox.

### Produce a handoff

Before ending a report-only PR review or bounded investigation:

- If there are actionable findings/next changes and they are **not already represented by authoritative unresolved GitHub review threads**, **MUST** write a compact handoff under `.codex-artifacts/handoffs/`.
- For PR review, prefer `.codex-artifacts/handoffs/pr-<N>-review.md` via `.codex/scripts/new-handoff.sh <N>`.
- For a non-PR investigation, use `.codex/scripts/new-handoff.sh <short-slug>`.
- If there are no actionable findings, do not create an empty handoff.
- If GitHub unresolved review threads are the authoritative record, do not duplicate them into a local handoff.

Every new handoff carries metadata used by auto-discovery: `status`, `kind`, PR, branch, repository, worktree, `topic`, optional `scope`/`objective`, reviewed HEAD, `producer`/`consumer`, and creation time. Prefer `.codex/scripts/new-handoff.sh <PR> <topic>` for component-specific findings. The helper also records an **active handoff pointer** for that PR/worktree so a later generic `Address #<PR> review` continues the handoff just produced instead of guessing among older open handoffs.

Every handoff body contains only:
- severity/priority;
- file and symbol;
- root cause/problem;
- exact intended change;
- constraints/non-goals;
- minimal validation;
- unresolved uncertainty only if it affects implementation.

### Consume a handoff

- Auto-discovery first uses the fresh **active handoff pointer** written by the latest review/investigation, then repository + PR/branch/worktree evidence, **task-topic overlap**, and freshness. A generic continuation without an active pointer does not silently resurrect an arbitrary older open handoff.
- A handoff is stale for auto-selection when it is older than **48 hours**, its reviewed HEAD is not an ancestor of current HEAD, or current HEAD is more than **50 commits** ahead. Stale handoffs remain available for manual inspection but are not silently injected.
- `status: consumed` handoffs are ignored by normal discovery; consuming the active handoff clears its pointer, while explicitly reopening it restores the pointer.
- Re-check each item against current HEAD and resulting diff.
- Mark consumed only after all actionable items are completed or obsolete.

Do not use `/fork` as a review-to-implementation handoff; a new session + compact handoff is preferred.

## Durable runtime state

```text
.codex/                    static scripts/templates; safe if read-only
.codex-artifacts/          mutable local state; git-excluded and writable
  handoffs/
  goals/
  logs/
```

Long performance/kernel Goals belong under `.codex-artifacts/goals/` and are created with `.codex/scripts/new-goal.sh <slug>`.

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
