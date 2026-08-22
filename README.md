# SGLang + Ascend Agent Workflow Kit

A reproducible Windows 11 + WSL2 workflow for SGLang development with **replaceable model backends**. The installer can use Codex, a self-hosted OpenAI-compatible model, or an external OpenAI-compatible API as the primary agent. Codex is offered as the default choice, but it is optional.

The kit is built around one principle: **keep long-lived engineering state in Git and small artifacts, not in an ever-growing chat transcript**.

## Project priority: SGLang + Ascend engineering

The primary objective of this project is a **correct, reproducible SGLang + Ascend development workflow**. Replaceable model backends, token-cost routing, and self-hosted/API workers are supporting mechanisms; they must not weaken the SGLang/Ascend contracts. Regardless of the selected primary model, NPU work keeps the same version/runtime/workload preflight, targeted skill routing, profiling and benchmark gates, minimal-change discipline, and validation requirements. A cheaper model is never a substitute for missing hardware evidence or backend-specific verification.

**Current release:** `v0.2.0` - see [`CHANGELOG.md`](CHANGELOG.md).

## What this repository configures

- One interactive entrypoint: `./setup.sh`. It selects the installation level, primary model backend, optional workers, and routing policy, then installs/deploys the chosen components.
- Four installation levels: `light`, `standard`, `full`, and `custom`.
- A provider-neutral `ai-task` router. `AI_PRIMARY_BACKEND` can be `codex`, `local`, `cheap`, `strong`, or `none`; `AI_ROUTING_MODE` can be `primary` or `hybrid`.
- Optional Codex CLI/profiles/hooks and VS Code extension. Nothing Codex-specific is installed in `light`, and Codex can be omitted entirely from other levels.
- Optional OpenCode harness for self-hosted or external OpenAI-compatible models.
- Optional self-hosted endpoints such as vLLM, SGLang, llama.cpp, Ollama-compatible gateways, or another compatible server.
- Optional cloud API workers. Credentials live only in `~/.config/sglang-workflow/models.env`, which is mode `0600` and preserved across upgrades.
- Provider-neutral repo skills, handoffs, Goals, log reduction, Git-first retrieval, and session discipline. Historical `.codex/` paths are retained for compatibility, but most scripts in that directory are model-agnostic.
- Codex lifecycle hooks, when Codex is installed, can auto-discover matching open handoffs. Other agents use the same resolver explicitly.
- Semble, Serena, core Ascend skills, BBuf skills, and kernel-specific skill bundles according to installation level.

## Why use this workflow?

The main goal is to make **SGLang + Ascend development safer, more reproducible, and easier to resume**: establish the correct NPU/runtime baseline, load the owning expert skill, keep investigations bounded, validate the actual backend path, and preserve actionable state outside chat.

Token efficiency is a secondary but important benefit. The workflow avoids repeatedly paying for context the model no longer needs and lets optional workers handle bounded low-cost tasks without changing the engineering contract. The largest savings usually come from session lifecycle and retrieval discipline, not from making final answers terse.

| Mechanism | What it changes | Expected token impact | Usability impact |
|---|---|---:|---|
| **New objective -> new session** | Stops unrelated history from following the next task | **Very high** for long sessions | Cleaner scope; fewer accidental side quests |
| **Handoff artifacts + resolver** | Record local actionable findings; an active pointer connects the latest review to the next implementation, while topic + HEAD freshness prevent stale fallback | **High** when one task feeds another | Generic `Address #PR review` prompts no longer need a path and do not guess among old handoffs |
| **Goal + experiment ledger** | Keeps benchmark state, hypotheses, failures, and next steps in files instead of chat history | **High** for multi-round performance work | Long optimization loops become reproducible and resumable |
| **Multi-model routing** | Uses a user-selected primary backend and optional task-specific workers without hard-wiring the workflow to one provider | **Direct Plus/API cost reduction** | Backends can be swapped without rewriting workflow rules |
| **Session/prompt hooks** | Auto-discover matching open handoffs at session start and implementation prompts; also block standalone `git push`-style turns | **High** when review feeds implementation; avoids repeated discovery | Handoffs become mostly path-free after one-time hook trust approval |
| **Targeted `rg` / Git first** | Uses exact search when an identifier, error, path, PR, or commit is already known | **Medium to high** | Faster navigation; less tool wandering |
| **Semble** | Returns small semantic code chunks for conceptual questions instead of grep + full-file reads | **Potentially high retrieval savings** | Natural-language code discovery when the symbol/path is unknown |
| **Serena (optional)** | Uses LSP-backed symbol relationships for callers, references, implementations, and refactors | **Medium**, especially in large cross-file tasks | IDE-like navigation and safer structural edits |
| **Log reduction** | For local/downloaded logs >= 1 MiB or >= 10k lines, repo rules require focused reduction before any full raw-log read | **High for large logs** | Faster triage; less irrelevant output to inspect |
| **Task-specific skills** | Reuses bounded workflows for PR review, regressions, Ascend profiling, HCCL, `torch_npu`, etc. | **Indirect but often significant** | Fewer repeated instructions and fewer wrong investigation branches |
| **Stop rules** | Ends the session once the requested change and minimal validation are complete | **Medium to high** | Prevents cleanup/refactor/review expansion after the task is already solved |

### Measured token reduction on SGLang sessions

The workflow has also been tested against real SGLang/Codex session logs. These numbers measure **processed input tokens**, not billing units and not a guaranteed subscription-quota reduction. Task mix differs between days, so treat the comparison as an observed engineering signal rather than a controlled benchmark.

| Session corpus | Sessions | Mean input / session | Median input / session | Mean reduction vs old workflow | Mean input saved / session |
|---|---:|---:|---:|---:|---:|
| **Old workflow baseline** | 44 | ~24.10M | ~7.70M | - | - |
| **First day with workflow (20 Aug 2026)** | 14 | ~2.71M | ~1.44M | **~88.8%** | **~21.39M** |
| **Latest workflow (21-22 Aug 2026)** | 25 | **~1.98M** | **~1.16M** | **~91.8%** | **~22.12M** |

A normalized way to read the latest result: **25 sessions at the historical mean would process about 602.5M input tokens; the observed 25-session corpus processed about 49.4M**. That is roughly **553M fewer processed input tokens (~91.8%)** at the per-session mean. This is not a claim that the kit causally saves exactly 553M tokens for every 25 tasks; the old corpus contained several pathological long sessions and the workloads are not identical.

The latest revision also improved over the first workflow day: mean input fell from ~2.71M to ~1.98M per session (**~26.9% lower**), while user turns/session and tool calls/session also decreased. The largest remaining token hotspot was broad PR review, which is why this version adds a bounded per-component review retrieval rule.

### Where the token savings actually come from

A useful mental model is:

```text
total agent cost
  = model choice
  x context repeatedly processed
  + tool/retrieval context
  + generated output
```

For repository work, **repeated input/context is often the dominant term**. That is why this kit prioritizes:

1. **shorter task lifetimes**, not merely shorter prompts;
2. **small auto-discovered handoff files**, not `/fork`-style duplication of a long transcript;
3. **targeted retrieval**, not repeatedly reading large files and logs;
4. **a replaceable primary backend plus optional lower-cost workers**, with deliberate escalation to the backend you trust for the task.

Semble reports roughly **99% fewer retrieval tokens than grep+read in its own benchmark at comparable recall**. Treat this as a retrieval benchmark, not a promise of 99% lower end-to-end Codex usage: model reasoning, Git operations, tests, and later tool calls still consume context.

Serena has a different benefit. It is not primarily a semantic-search replacement; once a concrete symbol is known, it can answer structural questions such as callers/references directly through language-server information. This often replaces several `rg -> read -> rg -> read` steps with one symbol-aware lookup.

### What happens automatically?

The kit distinguishes three enforcement levels:

- **Hard/hook-driven after trust approval:** code runs before the model session/turn. Handoff **discovery** is automatic through `SessionStart`/`UserPromptSubmit` hooks, and standalone `git push` prompts are blocked before a model call. Codex deliberately does not execute untrusted user hooks, so approve both hooks once with `/hooks`.
- **Instruction-enforced:** `AGENTS.override.md` and task skills use **MUST** rules. Large-log reduction, handoff creation/consumption, strategy-reversal session splitting, and one-session-per-worktree discipline are in this category.
- **Manual/optional:** capabilities such as Serena or optional AscendC/Triton skill bundles are enabled only when you choose to install/use them.

Examples:

```text
Analyze /tmp/npu-ci.log and find the root cause.
```

For a large local/downloaded log, the active agent should check its size, run `.codex/scripts/extract-log-context.py`, read the focused artifact, and only then inspect narrow raw ranges if necessary.

```text
Review PR #31320. Report only.
```

If actionable local findings exist and unresolved GitHub review threads are not already authoritative, the review skill writes `.codex-artifacts/handoffs/pr-31320-review.md` (or a topic-specific file such as `pr-31320-fsdp-review.md`). In the next session the trusted hooks prefer the active handoff pointer produced by that review, then use repository/PR/branch/worktree + task topic + HEAD freshness as bounded fallback evidence. The implementation agent consumes the selected handoff instead of repeating the broad review. After consumption the active pointer is cleared, so an older unrelated open handoff is not silently promoted.

See [Automation and enforcement](docs/AUTOMATION.md) for the exact contracts and thresholds.

### Convenience and reliability gains

The workflow also improves development quality even when token savings are small:

- **Less goal drift:** PR review, conflict resolution, implementation, and CI triage do not silently merge into one giant task.
- **Better reproducibility:** performance experiments retain workload, versions, baseline, rejected directions, and artifacts.
- **Safer Ascend work:** benchmark and profiling skills enforce environment, backend, graph, precision, and distributed-mode gates before conclusions are accepted.
- **Faster onboarding:** `AGENTS.override.md` and skills encode the search order and repository conventions once, so they do not have to be repeated in every prompt.
- **Better recovery:** a fresh agent session can resume from Git + an auto-discovered compact handoff/Goal artifact without replaying the full investigation transcript.
- **Safer parallel work:** the workflow explicitly requires one active editing-agent session per Git worktree; real parallelism uses `git worktree` instead of shared mutable state.
- **Cheaper reversals:** changing implementation strategy is treated as a new session boundary so abandoned approaches stop inflating later turns.

### What this kit does *not* claim

There is no fixed percentage of end-to-end token savings. The effect depends on task length, model, repository size, amount of tool use, and how disciplined the session boundaries are. For a one-shot edit, the difference may be small. For a 50- or 200-turn debugging/performance thread, lifecycle discipline can dominate every other optimization.

## Installation levels

The installation level controls **tooling**, while the primary backend is selected independently. For example, `standard + Codex`, `standard + self-hosted`, and `full + external API` are all valid.

| Level | Installs | Model requirement |
|---|---|---|
| **Light** | SGLang + core Ascend/`torch_npu` skill layer only | None |
| **Standard** | Core workflow/router, selected primary client, Semble, core Ascend skills, GitHub CLI | Codex, self-hosted/API, or none |
| **Full** | Standard + BBuf skills, sgl-kernel-npu, all optional kernel skills, and Serena | Any primary backend; Codex and OpenCode remain optional |
| **Custom** | Component-by-component selection | Any or none |

`light` deliberately does **not** install Codex, OpenCode, hooks, routers, Semble, Serena, or mutable workflow state. It installs the bundled SGLang skills plus the core Ascend/`torch_npu` expert skills in the SGLang worktree.

## Quick start

### 1. Windows host (recommended for a new machine)

Run PowerShell as Administrator:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\windows\00-preflight.ps1
.\windows\01-bootstrap-windows.ps1
```

The Windows bootstrap installs Git, VS Code, Remote - WSL, and WSL networking prerequisites. It **does not install the Codex extension automatically** because the primary backend has not been selected yet.

If WSL asks for a reboot, reboot and start Ubuntu normally.

### 2. Run the setup wizard inside Ubuntu / WSL

From the extracted kit directory:

```bash
chmod +x setup.sh wsl/*.sh bin/* repo/.codex/scripts/*
./setup.sh
```

All installer questions are in English. The wizard first asks for the installation level. For every level except `light`, it then asks explicitly:

```text
Use Codex as the primary model? [Y/n]
```

If the answer is `no`, select a self-hosted OpenAI-compatible model, a stronger external API slot, a low-cost external API slot, or no model backend. Codex can still be installed later as an optional fallback. External API keys and self-hosted endpoints are never required for a Codex-only installation.

Typical choices:

```text
Light    -> SGLang + Ascend skills only
Standard -> core workflow; Codex is the default primary choice
Full     -> extended tooling/skills; primary backend is still selectable
Custom   -> select every component yourself
```

The wizard automatically clones/prepares the SGLang workspace, installs the selected clients/tools, writes the install manifest, configures routing, and performs verification.

### Non-interactive deployment

For reproducible setup:

```bash
./setup.sh --level standard --primary codex --routing primary --non-interactive --yes
```

Self-hosted primary:

```bash
export AI_LOCAL_BASE_URL=http://server:8000/v1
export AI_LOCAL_MODEL=your-coder-model
export AI_LOCAL_API_KEY=not-needed
./setup.sh --level standard --primary local --routing primary --non-interactive --yes
```

Full install with DeepSeek as the stronger external primary:

```bash
export AI_STRONG_API_KEY=your-api-key
./setup.sh --level full --primary strong --strong-preset deepseek --routing primary --non-interactive --yes
```

List built-in provider presets:

```bash
./setup.sh --list-model-presets
```

### Primary vs hybrid routing

The safe default is:

```text
AI_ROUTING_MODE=primary
```

Every `ai-task` request goes to the selected primary backend. If Codex is primary, the task kind still selects `sglang-lite`, `sglang`, `sglang-hard`, or `sglang-xhigh`.

`hybrid` mode is optional. It allows configured local/cheap/strong workers to be selected by task class. If Codex is **not** primary, Codex is not silently privileged; it is used as a hybrid fallback only when `AI_ENABLE_CODEX_FALLBACK=1`.

Inspect without a model call:

```bash
ai-task --dry-run docs "Update documentation"
ai-task --dry-run review 34855
ai-task --dry-run npu "Investigate graph mismatch"
```

Reconfigure at any time:

```bash
workflow-configure
```

### Daily UI

If Codex was selected/installed:

```bash
cd ~/code/sglang
code .
```

Approve `SessionStart` and `UserPromptSubmit` once through Codex `/hooks` after installation or hook changes. If Codex was not installed, use the selected OpenCode/self-hosted/API workflow instead; the repository skills and artifact contracts remain the same.

CLI examples:

```text
ai-task bug "..."          automatic selection
ai-task --tier primary ...  force configured primary
local-task ...              force self-hosted slot
cheap-task ...              force cheap API slot
strong-task ...             force strong API slot
cxl / cx / cxh / cxx        available only when Codex is installed
```

## Version tracking

The kit tracks provider-neutral installation state first:

```text
~/.config/sglang-workflow/workflow-kit-version   global kit marker
~/.config/sglang-workflow/install.env             non-secret install topology
~/code/sglang/.agents/.workflow-kit-version       workspace skill-layer marker
```

Core workflow installations also keep `~/code/sglang/.codex/KIT_VERSION` for compatibility. Codex installations additionally keep `~/.codex/workflow-kit-version`.

Check the effective installation from the SGLang worktree:

```bash
python3 .codex/scripts/workflow-doctor.py
```

When the local Codex app-server is available, the doctor also uses Codex `hooks/list` to verify the **effective current hook trust status/hash**, so a changed hook is reported as `Modified` instead of being incorrectly marked OK merely because an old `trusted_hash` entry exists. The doctor never grants hook trust; use `/hooks` for approval.

`wsl/06-update-existing-workspace.sh` replays the saved install topology, refuses accidental downgrades through the versioned workspace/global layers, records the successful version markers, and appends local update history to `.codex-artifacts/kit-version-history.tsv`. Release history is kept in [`CHANGELOG.md`](CHANGELOG.md); `scripts/package-release.sh` creates a versioned ZIP + SHA-256 sidecar. Details are in [Version tracking](docs/VERSIONING.md).

## Documentation

- [Models, pricing, and free options](docs/MODELS.md) - current model/provider options, reference prices, free tiers, and self-hosted guidance.
- [Installation](docs/INSTALLATION.md) - Windows, WSL, VPN, Codex, Semble, workspace setup.
- [VS Code + Codex](docs/VSCODE.md) - recommended extension-first workflow and verification.
- [Automation](docs/AUTOMATION.md) - what happens automatically, what is instruction-enforced, and what remains manual.
- [Workflow](docs/WORKFLOW.md) - session boundaries, automatic handoffs, Goals, worktrees, model routing, tests, Git discipline.
- [Multi-model routing](docs/MULTI_MODEL.md) - self-hosted/OpenCode setup, external tiers, router policy, overrides, and escalation.
- [Tooling](docs/TOOLING.md) - `rg`, Git, Semble, Serena, model-history skills, prompt guard.
- [Ascend / NPU](docs/ASCEND.md) - `torch_npu`, profiling, HCCL, Triton, AscendC, benchmark gates.
- [Troubleshooting](docs/TROUBLESHOOTING.md) - WSL, VPN/DNS, Windows Codex shim, Semble timeout, GitHub auth, handoff discovery.
- [Updating](docs/UPDATING.md) - upgrade an already configured SGLang workspace without reinstalling everything.
- [Version tracking](docs/VERSIONING.md) - SemVer, installed-version markers, downgrade protection, and release tags.
- [Contributing](CONTRIBUTING.md) - repository development and validation rules.
- [Acknowledgements](ACKNOWLEDGEMENTS.md) - upstream projects and inspirations.

The printable one-page daily reference is [PRINT_RULES.pdf](PRINT_RULES.pdf).

## Repository layout

```text
.
├── README.md
├── VERSION
├── CHANGELOG.md
├── PRINT_RULES.pdf
├── ACKNOWLEDGEMENTS.md
├── CONTRIBUTING.md
├── LICENSE
├── setup.sh               # interactive/non-interactive installer and deployment entrypoint
├── windows/               # Windows host bootstrap
├── wsl/                   # WSL + workspace bootstrap
├── codex/                 # optional Codex config/profiles/hooks
├── opencode/              # optional OpenCode config + model env template
├── repo/                  # files copied into local SGLang checkout
├── bin/                   # Codex and multi-model task routers
├── scripts/               # repository validation helper
├── docs/                  # user documentation
│   └── source/            # editable source for PRINT_RULES.pdf
└── .github/workflows/     # repository validation
```

## Publishing as a Git repository

The archive intentionally does **not** contain a `.git/` directory. After extracting it:

```bash
git init
git add .
git commit -m "Initial workflow kit"
```

Then add your remote and push normally.

## Scope and safety

This project configures development tooling. It does **not** install CANN, Ascend drivers/firmware, or a target `torch_npu` runtime. NPU runtime versions must match the actual SGLang branch, CI image, container, or Ascend host being tested.

External skill repositories are cloned at setup time; their contents are not vendored into this repository and remain under their respective licenses.

This project is independent and is not affiliated with or endorsed by OpenAI, the SGLang project, Huawei/Ascend, MinishLab, or the other acknowledged upstream projects.

## License

MIT. See [LICENSE](LICENSE).
