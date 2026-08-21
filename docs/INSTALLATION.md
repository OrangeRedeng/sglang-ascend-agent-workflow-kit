# Installation

## 1. Requirements

- Windows 11 with hardware virtualization enabled.
- Administrator access for the Windows bootstrap.
- Internet access from Windows and WSL.
- A GitHub account for `gh auth login`.

If a VPN is used on Windows, keep it enabled while testing the WSL network. The bootstrap configures WSL mirrored networking because it is more reliable than the default NAT path for many VPN setups.

## 2. Windows host setup

Open **Administrator PowerShell** in the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\windows\00-preflight.ps1
.\windows\01-bootstrap-windows.ps1
```

The bootstrap installs or verifies:

- Git for Windows;
- Visual Studio Code;
- VS Code WSL extension;
- OpenAI ChatGPT/Codex VS Code extension (recommended daily UI);
- WSL2 / Ubuntu;
- `%USERPROFILE%\.wslconfig` networking settings.

The WSL configuration is merged into the existing `[wsl2]` section rather than replacing unrelated user settings:

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true
autoProxy=true
```

After changing `.wslconfig`, WSL must be restarted:

```powershell
wsl --shutdown
```

### First WSL installation

If Windows requires a reboot, reboot before continuing. After reboot:

```powershell
wsl -l -v
```

If no Linux distribution is installed:

```powershell
wsl --install -d Ubuntu
```

Then:

```powershell
wsl --shutdown
wsl -d Ubuntu
```

Create the Linux username/password requested by Ubuntu.

## 3. WSL bootstrap

From Ubuntu, navigate to the extracted repository. Example for a repository on the Windows desktop:

```bash
cd /mnt/c/Users/<you>/Desktop/codex-sglang-workflow-kit
```

Run:

```bash
chmod +x wsl/*.sh bin/cx-task repo/.codex/scripts/*
./wsl/02-bootstrap-wsl.sh
source ~/.bashrc
```

The script installs:

- build tools (`cmake`, `ninja`, `clang`, `lld`, `ccache`);
- Git + Git LFS;
- GitHub CLI;
- `ripgrep`, `jq`, `fd`;
- `uv` / `uvx`;
- Linux Codex CLI;
- Semble;
- global Codex profiles, hooks, and aliases.

### Linux Codex path check

WSL may inherit a Windows npm shim from `/mnt/c/...`. The bootstrap rejects it. Verify:

```bash
which codex
codex --version
```

The path must be a Linux path such as `/usr/local/bin/codex` or `$HOME/.local/bin/codex`, **not** `/mnt/c/Users/.../npm/codex`.

## 4. GitHub authentication

```bash
gh auth login
```

If WSL cannot open the browser automatically, copy the device URL/code into the Windows browser. After success:

```bash
gh auth status
```

Do not rerun login after authentication has already succeeded.

## 5. Verify WSL networking

Especially when using a VPN:

```bash
getent ahostsv4 registry.npmjs.org
curl -4 -I --connect-timeout 10 https://registry.npmjs.org/
npm ping
```

If DNS resolves but HTTPS times out, see [Troubleshooting: WSL + VPN](TROUBLESHOOTING.md#wsl--vpn-dns-works-but-https-times-out).

## 6. Semble startup and prewarm

The Codex config uses:

```toml
[mcp_servers.semble]
command = "uvx"
args = ["--from", "semble[mcp]", "semble"]
enabled = true
startup_timeout_sec = 120
```

The WSL bootstrap prewarms the Semble CLI/MCP environment and pins the installed MCP package to the exact Semble CLI version in the user copy of `~/.codex/config.toml`. The repository template stays version-agnostic. The first semantic search can still take longer because the embedding model and repository index may need to be cached.

## 7. Create the SGLang workspace

Run from the kit directory:

```bash
./wsl/03-setup-sglang-workspace.sh
```

It creates or reuses:

```text
~/code/
├── sglang/
├── sgl-kernel-npu/
├── AI-Infra-Auto-Driven-SKILLS/
├── awesome-ascend-skills/
└── ascend-agent-skills/
```

Keep active development repositories in the Linux filesystem (`~/code/...`), not `/mnt/c/...`.

Then:

```bash
cd ~/code/sglang
code .
```

In VS Code, confirm `WSL: Ubuntu`, open the Codex sidebar, and start a new local session. See [VS Code + Codex](VSCODE.md).

CLI is optional and independent:

```bash
cx
```

## 8. Optional kernel-specific Ascend skills

Install only when the current work touches that layer:

```bash
./wsl/04-install-ascend-kernel-skills-optional.sh opplugin
./wsl/04-install-ascend-kernel-skills-optional.sh triton
./wsl/04-install-ascend-kernel-skills-optional.sh ascendc
```

## 9. Optional Serena

Do not install Serena immediately unless symbol navigation is already a known bottleneck. After using the base setup for a while:

```bash
./wsl/05-install-serena-optional.sh
```

Append `codex/config/serena.optional.toml` to `~/.codex/config.toml`, restart Codex, and use Serena primarily for callers/references/symbol structure.

## 10. VS Code extension validation

From Ubuntu:

```bash
cd ~/code/sglang
code .
```

In VS Code:

1. confirm the lower-left indicator says `WSL: Ubuntu`;
2. confirm the Codex/OpenAI extension is enabled;
3. open the Codex sidebar and start a **new local session**;
4. use the read-only verification prompt from [VS Code + Codex](VSCODE.md#4-verify-that-the-extension-sees-the-correct-workspace).

After changes to `~/.codex/config.toml` or `~/.codex/.env`, restart the extension/VS Code window and start a new session.

## 11. CLI validation (optional)

From `~/code/sglang`:

```bash
which codex
codex --version
which semble
find -L .agents/skills -maxdepth 2 -name SKILL.md -print | sort
```

Start Codex:

```bash
cx
```

Inside Codex, verify MCP status with `/mcp`.

## 12. Updating an existing installation

If this kit is already installed and you downloaded a newer archive, do not rerun the complete Windows/WSL bootstrap just to update workflow rules.

From the new kit directory in WSL:

```bash
./wsl/06-update-existing-workspace.sh
```

This updates hooks, repo-local rules/skills/scripts, migrates legacy mutable `.codex/{handoffs,goals,logs}` state into `.codex-artifacts/`, and preserves your SGLang Git branch/worktree.

Afterward reload the VS Code WSL window and start a **new Codex session** so `SessionStart` handoff discovery is active.

See [Updating](UPDATING.md).
