# Codex + SGLang + Ascend Workflow Kit

A reproducible Windows 11 + WSL2 workflow for using OpenAI Codex on SGLang development, with focused support for Ascend NPU, `torch_npu`, profiling, PR review, CI triage, regressions, and performance work.

The kit is built around one principle: **keep long-lived engineering state in Git and small artifacts, not in an ever-growing chat transcript**.

## What this repository configures

- Windows 11 + WSL2 Ubuntu with VPN-friendly mirrored networking.
- Codex CLI profiles for routine, deep-review, and escalation work.
- A prompt guard that blocks wasteful standalone `git push` prompts.
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
| **Handoff artifacts** | Transfers only actionable findings between review/debug/implementation sessions | **High** when one task feeds another | Review and implementation stay independent but connected |
| **Goal + experiment ledger** | Keeps benchmark state, hypotheses, failures, and next steps in files instead of chat history | **High** for multi-round performance work | Long optimization loops become reproducible and resumable |
| **Model routing** | Uses Luna/Terra for routine work and Sol only where deeper reasoning is justified | **Direct cost reduction** | Less manual model switching; expensive reasoning is reserved for hard work |
| **Prompt guard** | Blocks standalone `git push`-style prompts before they become model turns | **High per avoided trivial turn in a long session** | Simple Git actions stay in the terminal where they belong |
| **Targeted `rg` / Git first** | Uses exact search when an identifier, error, path, PR, or commit is already known | **Medium to high** | Faster navigation; less tool wandering |
| **Semble** | Returns small semantic code chunks for conceptual questions instead of grep + full-file reads | **Potentially high retrieval savings** | Natural-language code discovery when the symbol/path is unknown |
| **Serena (optional)** | Uses LSP-backed symbol relationships for callers, references, implementations, and refactors | **Medium**, especially in large cross-file tasks | IDE-like navigation and safer structural edits |
| **Log reduction** | Extracts errors, metrics, and nearby context before giving large CI/profiler logs to the model | **High for large logs** | Faster triage; less irrelevant output to inspect |
| **Task-specific skills** | Reuses bounded workflows for PR review, regressions, Ascend profiling, HCCL, `torch_npu`, etc. | **Indirect but often significant** | Fewer repeated instructions and fewer wrong investigation branches |
| **Stop rules** | Ends the session once the requested change and minimal validation are complete | **Medium to high** | Prevents cleanup/refactor/review expansion after the task is already solved |

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
2. **small handoff files**, not `/fork`-style duplication of a long transcript;
3. **targeted retrieval**, not repeatedly reading large files and logs;
4. **lower-cost models for mechanical work**, with deliberate escalation for correctness/performance problems.

Semble reports roughly **99% fewer retrieval tokens than grep+read in its own benchmark at comparable recall**. Treat this as a retrieval benchmark, not a promise of 99% lower end-to-end Codex usage: model reasoning, Git operations, tests, and later tool calls still consume context.

Serena has a different benefit. It is not primarily a semantic-search replacement; once a concrete symbol is known, it can answer structural questions such as callers/references directly through language-server information. This often replaces several `rg -> read -> rg -> read` steps with one symbol-aware lookup.

### Convenience and reliability gains

The workflow also improves development quality even when token savings are small:

- **Less goal drift:** PR review, conflict resolution, implementation, and CI triage do not silently merge into one giant task.
- **Better reproducibility:** performance experiments retain workload, versions, baseline, rejected directions, and artifacts.
- **Safer Ascend work:** benchmark and profiling skills enforce environment, backend, graph, precision, and distributed-mode gates before conclusions are accepted.
- **Faster onboarding:** `AGENTS.override.md` and skills encode the search order and repository conventions once, so they do not have to be repeated in every prompt.
- **Better recovery:** a fresh Codex session can resume from Git + a compact handoff/Goal artifact without replaying the full investigation transcript.

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
code .
```

Start Codex from the SGLang repository, not from `C:\Windows\System32` or another unrelated directory:

```bash
cx
```

Profiles:

```text
cxl  -> Luna / low       cheap, mechanical work
cx   -> Terra / medium   default development
cxh  -> Sol / high       deep review, hard NPU/debug/perf
cxx  -> Sol / xhigh      escalation only
```

## Documentation

- [Installation](docs/INSTALLATION.md) - Windows, WSL, VPN, Codex, Semble, workspace setup.
- [Workflow](docs/WORKFLOW.md) - session boundaries, handoffs, Goals, model routing, tests, Git discipline.
- [Tooling](docs/TOOLING.md) - `rg`, Git, Semble, Serena, model-history skills, prompt guard.
- [Ascend / NPU](docs/ASCEND.md) - `torch_npu`, profiling, HCCL, Triton, AscendC, benchmark gates.
- [Troubleshooting](docs/TROUBLESHOOTING.md) - WSL, VPN/DNS, Windows Codex shim, Semble timeout, GitHub auth.
- [Contributing](CONTRIBUTING.md) - repository development and validation rules.
- [Acknowledgements](ACKNOWLEDGEMENTS.md) - upstream projects and inspirations.

The printable one-page daily reference is [PRINT_RULES.pdf](PRINT_RULES.pdf).

## Repository layout

```text
.
├── README.md
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
