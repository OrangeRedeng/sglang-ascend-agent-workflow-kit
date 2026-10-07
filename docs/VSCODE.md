# VS Code + Codex

The recommended daily interface is VS Code opened from the WSL SGLang worktree:

```bash
cd ~/code/sglang
code .
```

Confirm the bottom-left remote indicator is `WSL: Ubuntu` (or your WSL distribution). The OpenAI extension remains the primary UI and its native OpenAI model/reasoning controls remain untouched by GLM installation.

## Provider switching

OpenAI uses the normal default configuration and profiles `sglang-lite`, `sglang`, `sglang-hard`, and `sglang-xhigh`.

GLM uses isolated profiles because a provider switch must change both model and provider atomically. Use:

```text
cgl  GLM low
cg   GLM high
cgh  GLM high
cgx  GLM max
```

or:

```bash
codex-glm --effort max
```

This deliberately avoids replacing the default Codex model catalog with the GLM-only catalog.

The current CLI conversation and the current extension conversation are separate sessions. Use handoffs/Goals to transfer durable state instead of assuming one interface shares the other's transcript.

## Hooks

After installation or hook changes, run `/hooks` in Codex and review/approve `SessionStart`, `UserPromptSubmit`, and the new `PostToolUse` retrieval-budget hook. The workflow doctor reports structure but does not grant trust.
