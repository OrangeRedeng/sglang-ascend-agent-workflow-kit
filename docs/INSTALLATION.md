# Installation

## Existing installation

```bash
cd ~/code
rm -rf sglang-ascend-agent-workflow-kit-v0.6.0
unzip -q sglang-ascend-agent-workflow-kit-v0.6.0.zip -d sglang-ascend-agent-workflow-kit-v0.6.0
cd sglang-ascend-agent-workflow-kit-v0.6.0
chmod +x setup.sh wsl/*.sh bin/* scripts/*.sh scripts/*.py repo/.codex/scripts/*
./wsl/06-update-existing-workspace.sh
```

The updater preserves `~/.codex/config.toml`, removes old Kilo/OpenCode/legacy GLM-routing artifacts, installs the unified Copilot provider stack, canonicalizes shared skills and runs the doctor suite.

## Levels

- `light`: shared workflow + core skills only.
- `standard`: Copilot Chat + Codex Bridge + GLM provider + official Codex fallback + core Ascend + selected CANNBot skills.
- `full`: Standard + KernelHive + selected BBuf skills + `sgl-kernel-npu`.

## Account setup

Run:

```bash
workflow-copilot guide
```

Manual actions:

1. `Codex Bridge: Add ChatGPT Account` → profile `personal` → OAuth.
2. `Chat: Manage Language Models` → Add Models → Codex Bridge → profile `personal`.
3. `GLM: Set API Key` → BigModel China Coding Plan key.

Credentials remain in VS Code SecretStorage and are not written by the kit.

## Verify

```bash
cd ~/code/sglang
workflow-setup doctor --workspace "$PWD"
```
