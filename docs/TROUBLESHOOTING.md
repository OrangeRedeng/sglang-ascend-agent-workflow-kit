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
