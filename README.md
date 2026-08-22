# Codex + SGLang + Ascend Workflow Kit

A reproducible Windows 11 + WSL2 workflow for using OpenAI Codex on SGLang development, with focused support for Ascend NPU, `torch_npu`, profiling, PR review, CI triage, regressions, and performance work.

The kit is built around one principle: **keep long-lived engineering state in Git and small artifacts, not in an ever-growing chat transcript**.

**Current release:** `v0.1.0` — see [`CHANGELOG.md`](CHANGELOG.md).

## What this repository configures

- Windows 11 + WSL2 Ubuntu with VPN-friendly mirrored networking.
- Codex VS Code extension as the recommended daily UI, backed by the same WSL Codex configuration, repo instructions, skills, and MCP servers.
- Codex CLI profiles for terminal-first, remote, and diagnostic work.
- Codex `SessionStart`/`UserPromptSubmit` hooks that auto-discover matching open handoffs and inject their path into the new implementation session, plus a guard that blocks wasteful standalone `git push` prompts. User-installed command hooks must be explicitly trusted once in Codex before they execute.
- Semble MCP for conceptual code search, with a longer startup timeout and first-run prewarm.
- Optional Serena MCP for symbol-aware callers/references/refactoring.
- SGLang-local session, handoff, Goal, CI, log-analysis, and Ascend skills.
- Selected upstream SGLang, Ascend, `torch_npu`, profiling, and model-history skills.

## Why use this workflow?

The goal is not to make every prompt shorter. The main goal is to **avoid repeatedly paying for context that the model no longer needs** and to make the agent choose a cheaper, more precise path to the answer.

The largest savings usually come from session lifecycle and retrieval discipline, not from making final answers terse. Long coding sessions repeatedly carry prior conversation and tool context forward; a small new request can therefore be much more expensive than it looks.

| Mechanism | What it changes | Expected token impact | Usability impact |
|---|---|---:|---|
| **New objective -> new session** | Stops unrelated history from following the next task | **Very high** for long sessions | Cleaner scope; fewer accidental side quests |
| **Handoff artifacts + resolver** | Record local actionable findings; an active pointer connects the latest review to the next implementation, while topic + HEAD freshness prevent stale fallback | **High** when one task feeds another | Generic `Address #PR review` prompts no longer need a path and do not guess among old handoffs |
| **Goal + experiment ledger** | Keeps benchmark state, hypotheses, failures, and next steps in files instead of chat history | **High** for multi-round performance work | Long optimization loops become reproducible and resumable |
| **Model routing** | Uses Luna/Terra for routine work and Sol only where deeper reasoning is justified | **Direct cost reduction** | Less manual model switching; expensive reasoning is reserved for hard work |
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
4. **lower-cost models for mechanical work**, with deliberate escalation for correctness/performance problems.

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

For a large local/downloaded log, Codex should check its size, run `.codex/scripts/extract-log-context.py`, read the focused artifact, and only then inspect narrow raw ranges if necessary.

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
- **Better recovery:** a fresh Codex session can resume from Git + an auto-discovered compact handoff/Goal artifact without replaying the full investigation transcript.
- **Safer parallel work:** the workflow explicitly requires one active Codex session per Git worktree; real parallelism uses `git worktree` instead of shared mutable state.
- **Cheaper reversals:** changing implementation strategy is treated as a new session boundary so abandoned approaches stop inflating later turns.

### What this kit does *not* claim

There is no fixed percentage of end-to-end token savings. The effect depends on task length, model, repository size, amount of tool use, and how disciplined the session boundaries are. For a one-shot edit, the difference may be small. For a 50- or 200-turn debugging/performance thread, lifecycle discipline can dominate every other optimization.

## Quick start

### 1. Windows PowerShell (Administrator)

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\windows\00-preflight.ps1
.\windows\01-bootstrap-windows.ps1
```

If Windows asks for a reboot, reboot first. Then:

```powershell
wsl -l -v
```

If no distribution is installed:

```powershell
wsl --install -d Ubuntu
```

Start Ubuntu:

```powershell
wsl --shutdown
wsl -d Ubuntu
```

### 2. Inside Ubuntu / WSL

From the extracted repository directory:

```bash
chmod +x wsl/*.sh bin/cx-task repo/.codex/scripts/*
./wsl/02-bootstrap-wsl.sh
source ~/.bashrc
gh auth login
```

Then create the SGLang workspace:

```bash
./wsl/03-setup-sglang-workspace.sh
cd ~/code/sglang
```

Approve the two user lifecycle hooks once (Codex intentionally does not auto-trust unmanaged command hooks):

```text
cx
/hooks
# approve/enable SessionStart and UserPromptSubmit, then exit
```

Then verify the installation and open VS Code:

```bash
python3 .codex/scripts/workflow-doctor.py
code .
```

### Recommended daily workflow: VS Code extension

Open the repository with `code .` **from WSL**. In VS Code, confirm the lower-left remote indicator says `WSL: Ubuntu`, then open the Codex sidebar and start a new local session. The extension uses the WSL-side Codex configuration (`~/.codex/config.toml`) after restart/new session, so the default remains Terra/medium with Semble MCP and the repository rules/skills.

Do not run `cx` just to “connect Codex to VS Code”. The extension and CLI are separate clients. Use the extension as the default UI; use `cx` only when you intentionally want a terminal Codex session.

CLI profiles:

```text
cxl  -> Luna / low       cheap, mechanical work
cx   -> Terra / medium   default development
cxh  -> Sol / high       deep review, hard NPU/debug/perf
cxx  -> Sol / xhigh      escalation only
```

## Version tracking

The kit tracks the version of both installed layers:

```text
~/.codex/workflow-kit-version       global hook bundle
~/code/sglang/.codex/KIT_VERSION    repo-local workflow layer
```

Check the effective installation from the SGLang worktree:

```bash
python3 .codex/scripts/workflow-doctor.py
```

`wsl/06-update-existing-workspace.sh` prints the installed and incoming versions before changing anything, refuses accidental downgrades, records the successful version in both markers, and appends local update history to `.codex-artifacts/kit-version-history.tsv`. Release history is kept in [`CHANGELOG.md`](CHANGELOG.md); `scripts/package-release.sh` creates a versioned ZIP + SHA-256 sidecar. Details are in [Version tracking](docs/VERSIONING.md).

## Documentation

- [Installation](docs/INSTALLATION.md) - Windows, WSL, VPN, Codex, Semble, workspace setup.
- [VS Code + Codex](docs/VSCODE.md) - recommended extension-first workflow and verification.
- [Automation](docs/AUTOMATION.md) - what happens automatically, what is instruction-enforced, and what remains manual.
- [Workflow](docs/WORKFLOW.md) - session boundaries, automatic handoffs, Goals, worktrees, model routing, tests, Git discipline.
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
├── windows/               # Windows host bootstrap
├── wsl/                   # WSL + workspace bootstrap
├── codex/                 # global Codex config/profiles/hooks
├── repo/                  # files copied into local SGLang checkout
├── bin/                   # task/profile router
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
