# Installation

## Recommended

```bash
chmod +x setup.sh wsl/*.sh bin/* repo/.codex/scripts/* scripts/*.py
./setup.sh --level standard --primary codex --enable-glm --glm-region china
```

`standard` keeps Codex/OpenAI + the OpenAI VS Code extension as the daily interface and installs the workflow/handoff/core Ascend layer. Semble and Serena are intentionally not installed by Standard in v0.3.1.

Use `--level full` when you also want Semble, Serena, CANNBot, selected KernelHive skills, BBuf skills and `sgl-kernel-npu`.

## Levels

- `light`: SGLang + bundled/core Ascend skills; no model client/router/hooks.
- `standard`: Codex-first workflow, OpenAI extension, router, handoffs, core Ascend skills.
- `full`: Standard + Semble + Serena + CANNBot + selected KernelHive + BBuf + kernel repo.
- `custom`: choose each component; Semble/Serena default to no.

## GLM Coding Plan

```bash
workflow-configure --enable-glm --glm-region china
# or global
workflow-configure --enable-glm --glm-region global
```

The secret is stored only in `~/.config/sglang-workflow/models.env` (0600). Codex GLM profiles obtain the token through `workflow-provider-token`; TOML files contain no API key.

## Existing Codex configuration

v0.3.1 does not replace `~/.codex/config.toml`. On a fresh machine it creates only a minimal file if none exists. On an existing setup it preserves user model/reasoning settings, project trust, hook trust hashes, memories and unrelated MCP servers.

Hook installation is also merged. After new/changed hook definitions, launch Codex and review `/hooks`.

## External skill pins

`skills.lock.json` contains immutable commit pins. Setup checks out those commits in detached HEAD state and validates selected skills. Use:

```bash
workflow-skills status
workflow-skills snapshot
workflow-skills index
```

Advancing a dependency is deliberately explicit:

```bash
workflow-skills update --only cannbot-skills
```

This updates the private installed lock under `~/.config/sglang-workflow/`; release pins in the repository remain unchanged until deliberately committed in a new kit release.
