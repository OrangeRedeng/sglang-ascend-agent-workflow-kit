# Troubleshooting

## WSL command exists but no Ubuntu distribution is installed

Symptom:

```text
Windows Subsystem for Linux has no installed distributions
```

After any required Windows reboot:

```powershell
wsl -l -v
wsl --install -d Ubuntu
wsl --shutdown
wsl -d Ubuntu
```

Create the Linux user on first launch.

## WSL + VPN: DNS works but HTTPS times out

Typical symptoms:

```text
getent ahostsv4 registry.npmjs.org   # returns addresses
curl -4 https://registry.npmjs.org/ # times out
npm                                  # ETIMEDOUT / EAI_AGAIN
```

Use mirrored networking in `%USERPROFILE%\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true
autoProxy=true
```

Apply it:

```powershell
wsl --shutdown
wsl -d Ubuntu
```

Retest:

```bash
getent ahostsv4 registry.npmjs.org
curl -4 -I --connect-timeout 10 https://registry.npmjs.org/
npm ping
```

Do not start by hardcoding public DNS servers in `/etc/resolv.conf` when DNS already resolves; that does not fix a broken HTTPS route through the VPN.

## Codex resolves to a Windows npm shim inside WSL

Bad path:

```text
/mnt/c/Users/<you>/AppData/Roaming/npm/codex
```

This can fail with `exec: node: not found` or use the wrong runtime.

The WSL bootstrap rejects this path and installs a Linux Codex CLI. Verify:

```bash
type -a codex
which codex
codex --version
```

The first path must be Linux-native.

## Semble MCP startup timeout

Symptom:

```text
MCP client for `semble` timed out after 30 seconds
```

The repository config sets:

```toml
startup_timeout_sec = 120
```

Prewarm manually if needed:

```bash
uvx --from "semble[mcp]" semble --version
semble search "workflow bootstrap" . --top-k 1
```

Then restart Codex and check `/mcp`.

The first semantic search may download/cache an embedding model and build the repository index.

## `gh auth login` cannot open a browser from WSL

This warning is not fatal:

```text
Failed opening a web browser ... wslview not found
```

Copy the displayed device URL/code into the Windows browser. Verify afterward:

```bash
gh auth status
```

## GitHub CLI says credentials are stored in plain text

This is separate from Codex/WSL networking. `gh auth login` may use its local credential storage when no compatible credential helper is available. Review `gh auth status` and GitHub CLI credential-storage documentation if you want to change the storage backend.

## `winget` reports installer exit code 1 for Git or VS Code

If the preflight already shows valid `git`/`code` paths and the extensions install correctly, `winget` may simply be failing an attempted upgrade of an existing installation. Verify manually:

```powershell
git --version
code --version
```

Then continue if both commands work.

## PowerShell execution policy prompt

The documented command changes policy only for the current PowerShell process:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Confirm the prompt if Windows asks. Closing that PowerShell window discards the process-scoped setting.

## Codex starts in `/mnt/c/WINDOWS/system32`

Codex uses the current working directory as workspace context. Exit and start it from the project:

```bash
cd ~/code/sglang
cx
```

Do not perform SGLang work from `System32`.


## VS Code opens SGLang without `WSL: Ubuntu`

Close that window and reopen from Ubuntu:

```bash
cd ~/code/sglang
code .
```

The lower-left VS Code remote indicator should show `WSL: Ubuntu`. The repository should be under `/home/<user>/code/sglang`, not `/mnt/c/...`.

## Codex extension is missing or disabled

The Windows bootstrap installs `OpenAI.chatgpt`. Verify on Windows:

```powershell
code --list-extensions | Select-String -Pattern "openai.chatgpt" -CaseSensitive:$false
```

If it is missing:

```powershell
code --install-extension OpenAI.chatgpt --force
```

Then reopen the SGLang WSL window. If VS Code offers **Install in WSL: Ubuntu**, accept it.

## Codex extension does not see the WSL config or Semble

Confirm these files/commands from the integrated WSL terminal:

```bash
pwd
ls -l ~/.codex/config.toml
which semble
```

`pwd` should be under `~/code/sglang`. After changing `~/.codex/config.toml` or `~/.codex/.env`, restart the Codex extension/VS Code window and start a new local session.

If Semble still fails:

```bash
uvx --from "semble[mcp]" semble --version
semble search "attention backend selection" ~/code/sglang --top-k 1
```

Then restart the extension again.

## `cx` works but the VS Code sidebar looks unrelated

This is expected if both are open: CLI and extension are separate clients/sessions. Do not use `cx` as a way to attach Codex to VS Code. For the recommended workflow, open `code .` from `~/code/sglang` and use a new local session in the Codex sidebar.

## Handoff exists but Codex does not discover it automatically

First verify the resolver directly from the SGLang worktree:

```bash
cd ~/code/sglang
python3 .codex/scripts/resolve-handoff.py --json
```

If `selected` is populated, the local metadata match works. Reload the VS Code WSL window and start a **new Codex session** so the updated `SessionStart` hook is loaded.

Check global hook installation:

```bash
cat ~/.codex/hooks.json
ls -l ~/.codex/hooks/session_start.py ~/.codex/hooks/prompt_guard.py
```

The hook config should contain both `SessionStart` and `UserPromptSubmit`.

If `selected` is empty, list open handoffs:

```bash
ls -la .codex-artifacts/handoffs/
```

Legacy handoffs under `.codex/handoffs/` should be migrated by:

```bash
./wsl/06-update-existing-workspace.sh
```

## Reducer fails because `.codex` is read-only

Current versions write mutable output to:

```text
.codex-artifacts/logs/
```

not `.codex/logs/`.

If an old script still tries to write under `.codex/logs/`, update the installed workflow:

```bash
./wsl/06-update-existing-workspace.sh
```

Then verify:

```bash
grep -n 'codex-artifacts' ~/code/sglang/.codex/scripts/extract-log-context.py
```

## Multiple Codex sessions changed the same worktree

Do not continue both sessions. Keep one active session and inspect `git status`/`git diff` before proceeding.

For future parallel work use separate Git worktrees:

```bash
git worktree add ../sglang-task-a <branch-a>
git worktree add ../sglang-task-b <branch-b>
```

Open each worktree in its own WSL VS Code window.
