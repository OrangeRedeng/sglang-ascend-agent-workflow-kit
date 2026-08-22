# Installation and deployment

The recommended entrypoint is the root `setup.sh` wizard. The older numbered WSL scripts remain implementation helpers and can still be run directly for advanced/manual deployment.

## Installation model

Installation has two independent decisions:

1. **Installation level** - which workflow/tooling components are deployed.
2. **Primary backend** - which model client handles `ai-task` by default.

Codex is offered as the default primary choice, but it is optional.

The installation architecture is provider-neutral, but the project is not domain-neutral: **SGLang + Ascend development correctness remains the primary objective**. Model selection never disables the NPU-specific skill, compatibility, profiling, or validation contracts in a workflow-enabled installation.

## Installation levels

### Light

Installs only the skill layer into the SGLang worktree:

- bundled SGLang workflow skills from this kit;
- selected upstream SGLang skills that already exist in the checkout;
- core Ascend/`torch_npu` expert skills linked from the supported Ascend skill repositories;
- a small version marker and Git exclude entry for `.agents/`.

Light does **not** install:

- Codex;
- OpenCode;
- `ai-task`;
- lifecycle hooks;
- Semble;
- Serena;
- BBuf and optional kernel-specific skill bundles;
- `.codex-artifacts/` runtime state.

Use Light when another agent/harness will consume the SGLang + Ascend skill layer directly. It may clone/update the upstream Ascend skill sources needed to populate that layer, but it installs no model client or orchestration runtime.

### Standard

Installs the normal development workflow:

- core workflow scripts, handoffs, Goals, and log reduction;
- `ai-task` and explicit tier wrappers;
- selected primary model client;
- Semble;
- GitHub CLI;
- core Ascend/torch_npu skills;
- provider-neutral `AGENTS.override.md`;
- Codex profiles/hooks/extension only when Codex is selected or explicitly installed;
- OpenCode only when a self-hosted/API backend is selected or configured.

### Full

Adds to Standard:

- BBuf skill repository and selected skills;
- `sgl-kernel-npu` checkout;
- optional AscendC/Triton/op-plugin skill bundle;
- Serena;
- no additional model harness by default; OpenCode is installed only when a self-hosted/API backend is selected or configured.

Full still does **not** force Codex. A self-hosted or API model can remain the primary backend.

### Custom

Prompts for each major component individually.

## Windows host preparation

Run PowerShell as Administrator:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\windows\00-preflight.ps1
.\windows\01-bootstrap-windows.ps1
```

The Windows bootstrap installs host prerequisites, VS Code, Remote - WSL, and WSL networking configuration. It deliberately does not install the OpenAI/Codex extension because the model backend is selected later inside the WSL setup wizard.

If Windows requests a reboot, reboot before continuing.

## Interactive WSL setup

Inside Ubuntu/WSL, from the extracted kit directory:

```bash
chmod +x setup.sh wsl/*.sh bin/* repo/.codex/scripts/*
./setup.sh
```

The wizard is English-only and starts by selecting an installation level. For Standard/Full/Custom, the primary model question is explicit:

```text
Use Codex as the primary model? [Y/n]
```

If `yes`, Codex is installed/configured and `AI_PRIMARY_BACKEND=codex`.

If `no`, choose:

```text
1) Self-hosted OpenAI-compatible model
2) External OpenAI-compatible API (strong slot)
3) Low-cost external OpenAI-compatible API (cheap slot)
4) No primary model backend
```

If Codex is not primary, the wizard can still install Codex as an optional backend. It does not become an automatic fallback unless that behavior is explicitly enabled.

The wizard can also configure optional self-hosted, cheap API, and strong API slots. API keys are entered with hidden terminal input and stored only in:

```text
~/.config/sglang-workflow/models.env
```

Permissions are set to `0600`.

## Saved installation manifest

The setup topology is stored separately from secrets:

```text
~/.config/sglang-workflow/install.env
```

It records:

- installation level;
- workspace path;
- primary backend;
- routing mode;
- installed component flags.

It does **not** contain API keys or endpoint credentials. Upgrades use this manifest to redeploy the same topology without repeating every question.

## Primary backend and routing mode

The model configuration contains:

```bash
AI_PRIMARY_BACKEND=codex
AI_ROUTING_MODE=primary
AI_ENABLE_CODEX_FALLBACK=0
```

Valid primary values:

```text
codex
local
cheap
strong
none
```

`primary` is the default routing mode. Every automatic task uses the selected primary backend. When Codex is primary, task kind maps to the appropriate Codex profile.

`hybrid` is opt-in. It can select configured local/cheap/strong tiers by task class. If another backend is primary, Codex is included only when:

```bash
AI_ENABLE_CODEX_FALLBACK=1
```

This makes Codex replaceable instead of a hard-coded terminal tier.

## Non-interactive deployment

Codex-first Standard install:

```bash
./setup.sh \
  --level standard \
  --primary codex \
  --routing primary \
  --non-interactive \
  --yes
```

Skills-only deployment:

```bash
./setup.sh --level light --non-interactive --yes
```

Self-hosted primary:

```bash
export AI_LOCAL_BASE_URL=http://server:8000/v1
export AI_LOCAL_MODEL=your-coder-model
export AI_LOCAL_API_KEY=not-needed
./setup.sh \
  --level standard \
  --primary local \
  --routing primary \
  --non-interactive \
  --yes
```

External API primary with a built-in preset:

```bash
export AI_STRONG_API_KEY=your-api-key
./setup.sh \
  --level full \
  --primary strong \
  --strong-preset deepseek \
  --routing primary \
  --non-interactive \
  --yes
```

List provider presets before unattended deployment:

```bash
./setup.sh --list-model-presets
```

For custom providers, export `AI_CHEAP_*` or `AI_STRONG_*` (`BASE_URL`, `MODEL`, and `API_KEY`) before setup. Secrets are copied into `models.env` with mode `0600`; they are not written to `install.env`.

Alternative workspace:

```bash
./setup.sh --workspace /path/to/sglang
```

## Provider presets

`workflow-configure` and `setup.sh` include convenience presets for public endpoint/model metadata. The router itself remains vendor-neutral. Current presets include DeepSeek, Z.AI/GLM, Kimi Code, MiniMax, OpenRouter Free, Alibaba Cloud Coding Plan, and Alibaba Model Studio Qwen Coder PAYG.

```bash
workflow-configure --list-presets
./setup.sh --list-model-presets
```

Prices, free tiers, model IDs, and source links are documented in [Models, pricing, and free options](MODELS.md). Provider offerings change, so treat the preset as configuration convenience rather than a pricing guarantee.

## Reconfigure models later

```bash
workflow-configure
```

This asks again which primary model should be used, can configure optional workers, and updates only `models.env`. It does not reinstall the entire toolchain.

Inspect routing without consuming model tokens:

```bash
ai-task --dry-run docs "Update documentation"
ai-task --dry-run bug "Investigate regression"
ai-task --dry-run review 34855
ai-task --dry-run npu "Investigate graph mismatch"
```

## Codex-specific post-install step

Only when Codex is installed, open Codex CLI once and approve the lifecycle hooks:

```text
cx
/hooks
```

Approve/enable both `SessionStart` and `UserPromptSubmit`, exit Codex, and restart the VS Code WSL window/session.

Verify:

```bash
cd ~/code/sglang
python3 .codex/scripts/workflow-doctor.py
```

## Low-level scripts

The setup wizard orchestrates:

```text
wsl/02-bootstrap-wsl.sh
wsl/03-setup-sglang-workspace.sh
wsl/04-install-ascend-kernel-skills-optional.sh
wsl/05-install-serena-optional.sh
```

They accept `INSTALL_*` environment flags and are mainly useful for CI, debugging, or custom deployment automation. Normal installation should use `./setup.sh`.
