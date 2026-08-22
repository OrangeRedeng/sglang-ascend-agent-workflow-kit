# VS Code + Codex extension

This is the **recommended daily interface** for this workflow kit.

The intended architecture is:

```text
Windows 11
  -> VS Code
      -> WSL: Ubuntu
          -> ~/code/sglang
              -> Codex extension (primary UI)
              -> ~/.codex/config.toml
              -> AGENTS.override.md
              -> .agents/skills/
              -> Semble MCP
              -> .codex/ (static workflow)
              -> .codex-artifacts/ (writable handoffs/goals/logs)
```

The Codex CLI remains installed because it is useful for diagnostics, terminal-first work, SSH/remote use, and profile aliases. It is **not required** to keep a second CLI session running when using the extension.

## 1. Open the repository from WSL

From Ubuntu:

```bash
cd ~/code/sglang
code .
```

Do not open the project from `C:\...` or `/mnt/c/...` for normal SGLang work. Keep the checkout under the Linux filesystem (`~/code/sglang`) and launch VS Code from that WSL directory.

In VS Code, the lower-left remote indicator should show:

```text
WSL: Ubuntu
```

The opened folder should correspond to:

```text
/home/<user>/code/sglang
```

## 2. Verify the extension

The Windows bootstrap installs:

```text
ms-vscode-remote.remote-wsl
OpenAI.chatgpt
```

The workspace setup also performs a best-effort check/install of `OpenAI.chatgpt` through the `code` CLI.

In VS Code:

1. Open **Extensions**.
2. Search for **OpenAI ChatGPT / Codex**.
3. Confirm it is enabled for the current VS Code window.
4. Open the Codex sidebar.
5. Start a **new local session**.

If VS Code offers an `Install in WSL: Ubuntu` action for the extension, accept it. Extension placement can depend on the current VS Code/extension version; the important requirement is that Codex is available in the WSL workspace window.

## 3. What configuration is shared with the extension?

The workflow is intentionally split into a **shared layer** and a **CLI-only convenience layer**.

### Shared by extension and CLI

When the extension is running in the WSL workspace, the important durable configuration is:

```text
~/.codex/config.toml
~/code/sglang/AGENTS.override.md
~/code/sglang/.agents/skills/
~/code/sglang/.codex/
```

This gives the extension the same default model configuration, Semble MCP configuration, repository instructions, search routing, large-log policy, automatic handoff discovery hooks, handoff lifecycle, and SGLang/Ascend skills.

After changing `~/.codex/config.toml` or `~/.codex/.env`, restart the Codex extension/VS Code window and start a new session. OpenAI documents this restart/new-session requirement for Codex IDE configuration changes.

### CLI-only conveniences

These shell aliases are **not VS Code extension profiles**:

```text
cxl -> Luna / low
cx  -> Terra / medium
cxh -> Sol / high
cxx -> Sol / xhigh
```

They only choose a Codex CLI profile.

For the extension:

- default: Terra / medium from `~/.codex/config.toml`;
- difficult review / hard NPU correctness / distributed / performance: switch to Sol / high in the Codex UI;
- xhigh: escalation only.

The current CLI conversation and the current extension conversation are separate sessions. Starting `cx` does not attach the CLI transcript to the sidebar.

## 4. Verify that the extension sees the correct workspace

Use a safe first prompt:

```text
Inspect this workspace without modifying anything.

Report:
- repository root
- active repository instructions
- available project skills
- configured MCP servers
- current model and reasoning effort
```

Expected signals:

```text
repository root: /home/<user>/code/sglang
instructions: AGENTS.override.md / Codex instructions
skills: repo-local SGLang/Ascend skills
MCP: semble
model: gpt-5.6-terra, medium (unless manually changed)
```

If the repository root is `/mnt/c/WINDOWS/system32` or another Windows path, close that Codex session and reopen the SGLang folder from WSL.

## 5. Semble in the extension

Semble is configured globally in:

```text
~/.codex/config.toml
```

with a 120-second startup timeout. The bootstrap also prewarms the Semble environment.

You normally do **not** prompt `use Semble`. Repository instructions route conceptual search to Semble automatically.

If the extension reports an MCP startup error:

```bash
uvx --from "semble[mcp]" semble --version
cd ~/code/sglang
semble search "attention backend selection" . --top-k 1
```

Then restart the Codex extension and start a new session.

## 6. Extension-first daily usage

Typical start:

```bash
cd ~/code/sglang
code .
```

Then use the Codex sidebar for review, implementation, CI/debug, handoffs, and performance work.

Use the integrated terminal directly for decided commands that require no reasoning:

```bash
git status
git fetch --prune
git push
```

Use CLI only when it is specifically useful:

```bash
cx          # independent Terra/medium CLI session
cxh         # independent Sol/high CLI session
codex       # diagnostics / direct CLI
```

## 7. What remains automatic in the extension?

Repo-driven behavior does not require extra prompt boilerplate:

```text
exact identifier/path/error -> rg/direct navigation
unknown concept             -> Semble
large log                   -> reducer MUST run first
report-only review          -> handoff MUST be written when required
implementation session      -> hooks auto-discover handoff -> consume it; do not redo broad review
Ascend task                 -> route to relevant NPU skills
```

Handoff **discovery** is hook-driven: `SessionStart` and `UserPromptSubmit` resolve and inject the matching open handoff path. Handoff creation/consumption, log reduction, and search routing remain instruction-enforced through repository rules/skills.

CLI-specific aliases are not automatic in the extension. Hook behavior can depend on the Codex client/version, so do not rely on the standalone `git push` hook as the only protection in the IDE; the workflow rule still says to run decided Git operations directly in the terminal.

## 8. One active session per worktree

Do not run two Codex editing/review sessions against the same SGLang worktree. If you need parallel work, create another Git worktree and open it in a separate WSL VS Code window. This prevents races in Git state, local diffs and handoff state.

## 9. Multi-model companion workflow

The Codex sidebar remains the recommended interactive UI for Codex. `ai-task` is a separate CLI companion that can run self-hosted or external models through OpenCode in the same WSL worktree.

Typical split:

```text
terminal: ai-task review 34855
             -> external worker writes compact handoff

VS Code: start a new Codex session
             -> SessionStart resolves the handoff
             -> verify / implement / consume
```

Do not run an editing OpenCode worker and an editing Codex session concurrently in the same worktree. Use a separate `git worktree` for parallel editing.

See [Multi-model routing](MULTI_MODEL.md).
