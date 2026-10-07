# SGLang + Ascend Agent Workflow Kit

A reproducible Windows 11 + WSL2 workflow for SGLang development on Ascend NPU. Codex/OpenAI remains the primary daily interface, GLM Coding Plan can run through isolated Codex profiles, and OpenCode stays optional for separate external/self-hosted workers.

The central rule is unchanged: durable engineering state belongs in Git and compact artifacts, not in an ever-growing chat transcript.

**Current release:** `v0.3.1`

## Why v0.3.1

Analysis of 127 real Codex rollout sessions showed that the original workflow already eliminated most giant-diff and raw-log failures. The new dominant cost was repeated model/tool round trips: a minority of 40+ tool-call sessions consumed most recorded input tokens. v0.3.1 therefore optimizes retrieval/session lifecycle rather than adding another general-purpose agent harness.

Key changes:

- Non-destructive Codex upgrade: existing `~/.codex/config.toml` is never replaced. User model/reasoning selection, project trust, hook trust hashes, memories and unrelated MCP configuration survive upgrades.
- Hook merge instead of replacement; existing SessionStart/UserPromptSubmit definitions stay stable and a `PostToolUse` retrieval-budget governor is added.
- Evidence-based session budget: soft consolidation around 32 tool calls and checkpoint guidance around 44; no blind hard-stop for active performance Goals.
- `extract-log-context.py` v2: repeated error-signature clustering, ~32 KiB / 400-line default cap and targeted `--expand <signature>` second-stage retrieval.
- `workflow-review-packet.py`: one bounded PR/component packet before iterative review, reducing repeated `git diff`/`rg` round trips.
- `workflow-handoffs gc`: stale open handoffs become `archived` and matching pointers are cleared without deleting audit history.
- `workflow-exp`: machine-readable `results.jsonl` for NPU/performance Goals.
- External skill sources are pinned to immutable commits; `workflow-skills status` reports pin drift and `update --only SOURCE` is explicitly opt-in.
- Standard install no longer includes Semble. Semble and Serena are Full/Custom optional tools because the measured corpus showed no actual calls.
- Direct migration from legacy v0.1.x installs that predate `install.env`.

## Recommended installation

```bash
chmod +x setup.sh wsl/*.sh bin/* repo/.codex/scripts/* scripts/*.py
./setup.sh --level full --primary codex --enable-glm --glm-region china
```

For the lighter default without speculative search tooling:

```bash
./setup.sh --level standard --primary codex --enable-glm --glm-region china
```

The GLM Coding Plan key is stored only in:

```text
~/.config/sglang-workflow/models.env
```

with mode `0600`. It is not embedded in Codex TOML profiles.

## Updating an existing install

For v0.1.x, v0.2.x or v0.3.0:

```bash
chmod +x wsl/*.sh scripts/*.sh scripts/*.py repo/.codex/scripts/*
./wsl/06-update-existing-workspace.sh
```

If a v0.1.x install has no `~/.config/sglang-workflow/install.env`, the updater creates a conservative migration manifest from observable installed components. It does not overwrite the current Codex global configuration.

After a hook change, open a new Codex session and review `/hooks`; Codex deliberately requires trust for unmanaged command hooks.

## Daily UI and provider switching

Open the SGLang worktree through WSL:

```bash
cd ~/code/sglang
code .
```

OpenAI shortcuts:

```text
cxl   OpenAI light
cx    OpenAI default
cxh   OpenAI high
cxx   OpenAI xhigh
```

GLM shortcuts when configured:

```text
cgl   GLM low
cg    GLM high
cgh   GLM high
cgx   GLM max
```

GLM profiles are isolated from the user's default OpenAI provider/model configuration. The OpenAI VS Code extension therefore remains the normal UI and keeps its ordinary model/reasoning controls.

## Router

```bash
ai-task docs "Update documentation"
ai-task review 34855
ai-task npu "Investigate graph mismatch"
ai-task kernel "Optimize the fused MoE kernel"
ai-task --dry-run perf "Compare two implementations"
```

Codex provider policy:

```text
AI_CODEX_ROUTING=balanced   GLM for bounded/general work; OpenAI hard profile for NPU/perf/kernel/verify
AI_CODEX_ROUTING=openai     always use bundled OpenAI profiles
AI_CODEX_ROUTING=glm        prefer GLM when configured
```

`local`, `cheap` and `strong` remain optional OpenCode tiers. GLM Coding Plan does not require OpenCode.

## Installation levels

| Level | Installs |
|---|---|
| Light | SGLang + bundled/core Ascend skill layer only |
| Standard | Codex-first workflow + OpenAI extension + core Ascend skills; Semble/Serena off |
| Full | Standard + Semble + CANNBot + selected KernelHive skills + `sgl-kernel-npu` + BBuf + Serena |
| Custom | Component-by-component selection; Semble/Serena default to no |

## Retrieval/session controls

The `PostToolUse` hook keeps tiny per-session counters under `.codex-artifacts/session-budget/`. It does not block completed tools. It only injects concise guidance at thresholds and on the first repeated read of an unchanged handoff/`SKILL.md`.

Broad review:

```bash
python3 .codex/scripts/workflow-review-packet.py --pr 34855
# or
python3 .codex/scripts/workflow-review-packet.py --base origin/main
```

Large logs:

```bash
python3 .codex/scripts/extract-log-context.py run.log
python3 .codex/scripts/extract-log-context.py run.log --expand <signature-id>
```

Stale handoffs:

```bash
workflow-handoffs gc --older-than-hours 48 --dry-run
workflow-handoffs gc --older-than-hours 48
```

## Performance Goals

```bash
.codex/scripts/new-goal.sh a5-megamoe-prefill
workflow-exp record a5-megamoe-prefill --id 001 \
  --baseline-sha <sha> --candidate-sha <sha> \
  --command '<exact benchmark command>' \
  --metric ttft_ms=8123 --metric prefill_tps=14520 --decision keep
workflow-exp best a5-megamoe-prefill --metric ttft_ms --lower-is-better
```

Each Goal keeps human-readable experiment notes plus a machine-readable `results.jsonl`. This lets a new session continue from the compact ledger instead of replaying the previous chat.

## Ascend skill stack

```text
SGLang/NPU question
  -> sglang-ascend
     -> torch_npu / profiling / HCCL / adapter leaf skill
     -> sglang-ascend-kernel-dev
        -> CANNBot / AscendC / Triton / op-plugin / KernelHive as appropriate
     -> sglang-npu-perf-experiment
```

CANNBot and KernelHive are external repositories; they are not vendored. Release pins live in `skills.lock.json`.

```bash
workflow-skills status
workflow-skills snapshot
workflow-skills index
workflow-skills update --only cannbot-skills   # explicit advance of private installed lock
```

`workflow-skills install` checks out the locked commit in detached HEAD state and validates selected `SKILL.md` entries. `.agents/.skills-resolved.json` records the exact installed SHA; `.agents/.skills-index.json` provides a compact ownership/index layer for agents.

## Engineering invariants

For version-sensitive Ascend work record hardware, NPU count, CANN, PyTorch, `torch_npu`, `sgl-kernel-npu`, SGLang commit, graph/eager mode, precision/quantization, TP/DP/EP, HCCL/network settings, workload and actual backend path. Reject performance comparisons when these differ unexpectedly.

Large logs (`>=1 MiB` or `>=10,000` lines) must be reduced before raw reading. Report-only reviews/investigations with actionable findings produce compact handoffs. One active editing-agent session per Git worktree remains mandatory.

## Doctor

```bash
python3 .codex/scripts/workflow-doctor.py
python3 .codex/scripts/workflow-doctor.py --online   # optional tiny GLM Responses smoke test
```

The doctor never changes hook trust. After installing/changing hooks, use `/hooks` in Codex.

## Documentation

- [Installation](docs/INSTALLATION.md)
- [VS Code + Codex](docs/VSCODE.md)
- [Multi-model / GLM routing](docs/MULTI_MODEL.md)
- [Models](docs/MODELS.md)
- [Ascend/NPU](docs/ASCEND.md)
- [Skill sources](docs/SKILLS.md)
- [Workflow](docs/WORKFLOW.md)
- [Tooling](docs/TOOLING.md)
- [Automation](docs/AUTOMATION.md)
- [Updating](docs/UPDATING.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Versioning](docs/VERSIONING.md)

## Validation

```bash
bash -n setup.sh wsl/*.sh bin/cx-task bin/glm-task bin/local-task bin/cheap-task bin/strong-task bin/workflow-handoffs repo/.codex/scripts/*.sh scripts/package-release.sh
python3 -m py_compile bin/ai-task bin/codex-glm bin/workflow-configure bin/workflow-provider-token bin/workflow-skills bin/workflow-exp codex/hooks/*.py repo/.codex/scripts/*.py scripts/*.py
python3 scripts/validate_repo.py
```

This project configures development tooling. It does not install CANN, Ascend drivers/firmware, or the target `torch_npu` runtime. External skill repositories remain governed by their own licenses.
