# SGLang Ascend Agent Workflow Kit

**Current release:** `v0.6.0`

Focused local workflow for SGLang + Ascend NPU development in WSL/VS Code.

The daily UI is intentionally one place:

```text
VS Code / WSL
└── GitHub Copilot Chat
    ├── Codex Bridge
    │   └── ChatGPT/Codex subscription + reasoning + 5h/weekly quota
    └── GLM Models for GitHub Copilot Chat
        └── BigModel China Coding Plan + Low/High/Max + quota

Fallback
└── official OpenAI Codex extension + native Codex hooks

Shared project layer
├── AGENTS.md
├── .agents/skills/
└── .codex-artifacts/{handoffs,goals,logs,reviews}
```

Kilo, OpenCode, Semble, Serena and Codex-native GLM routing are not part of the runtime workflow.

## Update an existing installation

```bash
cd ~/code
rm -rf sglang-ascend-agent-workflow-kit-v0.6.0
unzip -q sglang-ascend-agent-workflow-kit-v0.6.0.zip -d sglang-ascend-agent-workflow-kit-v0.6.0
cd sglang-ascend-agent-workflow-kit-v0.6.0
chmod +x setup.sh wsl/*.sh bin/* scripts/*.sh scripts/*.py repo/.codex/scripts/*
./wsl/06-update-existing-workspace.sh
```

`standard` installs:

- GitHub Copilot Chat;
- Codex Bridge for Copilot Chat;
- GLM Models for GitHub Copilot Chat;
- official OpenAI Codex extension/CLI as fallback;
- shared SGLang/Ascend workflow and core Ascend/CANNBot skills.

The updater configures everything that can be configured safely and runs the doctor automatically.

## Two manual account steps

After setup, run:

```bash
workflow-copilot guide
```

Then in VS Code:

1. `Codex Bridge: Add ChatGPT Account` → profile `personal` → complete ChatGPT OAuth.
2. `Chat: Manage Language Models` → `Add Models` → `Codex Bridge` → use profile `personal` and enable the Codex models you want.
3. `GLM: Set API Key` → paste the BigModel China Coding Plan key.

After that, both model families are selected from the same Copilot Chat model picker. Reasoning controls are model-specific. Codex Bridge and GLM each expose their own quota status item.

## Verify

```bash
cd ~/code/sglang
workflow-setup doctor --workspace "$PWD"
```

Or inspect only the unified UI layer:

```bash
workflow-copilot status --workspace ~/code/sglang
workflow-copilot doctor --workspace ~/code/sglang
```

The doctor verifies VS Code version, all four required extensions, workspace provider settings, root `AGENTS.md`, canonical Agent Skills, pinned sources and removal of old harness clutter. OAuth/API secrets remain intentionally opaque because VS Code stores them in SecretStorage.

## Daily use

Use Copilot Chat for both providers:

- Codex Bridge for OpenAI/Codex work;
- GLM for mechanical coding, docs, first-pass exploration and other tasks where you want to spend the GLM Coding Plan quota;
- switch to stronger Codex reasoning for high-risk Ascend correctness, HCCL/TP/EP/SP, MegaMoE and final kernel/performance review.

Use the official Codex extension only when you specifically need native Codex hooks/runtime behavior.

See `docs/INSTALLATION.md`, `docs/VSCODE.md`, `docs/MODELS.md`, `docs/SKILLS.md`, and `docs/WORKFLOW.md`.
