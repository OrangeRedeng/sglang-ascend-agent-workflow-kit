# Troubleshooting

## Copilot Chat does not show Codex

```bash
workflow-copilot configure --workspace ~/code/sglang
workflow-copilot doctor --workspace ~/code/sglang
```

Then run `Codex Bridge: Add ChatGPT Account`, complete OAuth with profile `personal`, and add a Codex Bridge entry from `Chat: Manage Language Models -> Add Models` using the same profile ID.

## Codex quota is not visible

Confirm `openaiCodex.showUsageStatusBar=true` in the workspace settings, then run `Codex Bridge: Show Usage` or click the Codex Bridge status-bar item after authentication.

## GLM models do not appear

Run `GLM: Set API Key`. The workspace must contain:

```text
glm-copilot.apiMode = coding-plan
glm-copilot.region  = china
```

If authentication fails, clear and re-enter the secret with the extension commands. Do not configure a generic PAYG endpoint.

## VS Code version failure

The current GLM provider requires VS Code 1.127+ and Codex Bridge requires 1.125+. Update VS Code, reopen the folder through WSL, and rerun `workflow-copilot doctor`.

## `codex` resolves to Windows or is broken

The official Codex extension is only a fallback, but the CLI can be repaired safely:

```bash
workflow-codex repair
workflow-codex doctor
```

The managed WSL copy lives under `~/.local/npm/bin` and does not require `sudo npm install -g`.

## Skill does not appear

```bash
workflow-skills dedupe --workspace ~/code/sglang
workflow-setup doctor --workspace ~/code/sglang
```

The skill directory name must exactly match the `name:` in `SKILL.md`.

## Kilo/OpenCode leftovers

They are not used. Rerun the updater; it removes kit-created Kilo workspace files, Kilo extension/CLI, old provider routers and legacy commands.

## Native Codex hooks

Codex-specific hooks do not run through Codex Bridge because the agent harness is Copilot Chat. If a task needs those hooks, use the official Codex extension and review `/hooks` after hook changes.
