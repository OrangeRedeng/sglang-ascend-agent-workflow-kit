#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
STAMP="$(date +%Y%m%d-%H%M%S)"

log() { printf '\n==> %s\n' "$*"; }
backup_if_exists() {
  local p="$1"
  if [[ -e "$p" || -L "$p" ]]; then
    cp -a "$p" "$p.bak-$STAMP"
    echo "Backup: $p.bak-$STAMP"
  fi
}

log "Base packages"
sudo apt-get update
sudo apt-get install -y \
  build-essential cmake ninja-build clang lld ccache pkg-config \
  git git-lfs curl wget ca-certificates gnupg unzip zip jq ripgrep fd-find \
  python3 python3-venv python3-pip

git lfs install

log "GitHub CLI"
if ! command -v gh >/dev/null 2>&1; then
  (type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
    && sudo mkdir -p -m 755 /etc/apt/keyrings \
    && out=$(mktemp) && wget -nv -O "$out" https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    && cat "$out" | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
       | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && sudo apt update \
    && sudo apt install gh -y
fi

log "uv"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

log "Codex CLI"
# WSL may inherit the Windows npm shim via /mnt/c/...; that is not a valid
# Linux Codex installation and can fail with "node: not found".
codex_path="$(command -v codex 2>/dev/null || true)"
if [[ -z "$codex_path" || "$codex_path" == /mnt/c/* ]]; then
  if [[ -n "$codex_path" ]]; then
    echo "Ignoring Windows Codex shim in WSL: $codex_path"
  fi
  curl -fsSL --connect-timeout 15 https://chatgpt.com/codex/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
hash -r
codex_path="$(command -v codex 2>/dev/null || true)"
if [[ -z "$codex_path" || "$codex_path" == /mnt/c/* ]]; then
  cat >&2 <<'EOF'
Codex CLI is not installed correctly inside WSL.
If you use a Windows VPN, configure %USERPROFILE%\.wslconfig with:

[wsl2]
networkingMode=mirrored
dnsTunneling=true
autoProxy=true

Then run in PowerShell:
  wsl --shutdown

Restart Ubuntu and rerun this script.
EOF
  exit 1
fi

log "Semble"
if ! command -v semble >/dev/null 2>&1; then
  uv tool install semble
fi

log "Semble prewarm"
# Warm both the MCP package environment and the shared embedding/index cache.
# Failure is non-fatal because VPN or first-run network setup may still be in progress.
if ! timeout 180 uvx --from "semble[mcp]" semble --version >/dev/null 2>&1; then
  echo "Warning: Semble MCP prewarm did not finish; Codex will retry on first use." >&2
fi
if ! timeout 180 semble search "workflow bootstrap" "$KIT_ROOT" --top-k 1 >/dev/null 2>&1; then
  echo "Warning: Semble embedding/index prewarm did not finish; first search may be slower." >&2
fi

log "Codex configuration"
mkdir -p "$CODEX_HOME/hooks"
for f in config.toml sglang-lite.config.toml sglang.config.toml sglang-hard.config.toml sglang-xhigh.config.toml; do
  backup_if_exists "$CODEX_HOME/$f"
  cp "$KIT_ROOT/codex/config/$f" "$CODEX_HOME/$f"
done

# Pin the Semble MCP package in the installed Codex config to the exact CLI
# version we just installed. This follows Semble's current installer behavior
# and avoids fetching an arbitrary future package version on MCP startup.
semble_version="$(semble --version 2>/dev/null | awk '{print $NF}' || true)"
if [[ "$semble_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+ ]]; then
  sed -i "s#semble\[mcp\]#semble[mcp]==$semble_version#g" "$CODEX_HOME/config.toml"
  echo "Pinned Semble MCP to $semble_version in $CODEX_HOME/config.toml"
fi

backup_if_exists "$CODEX_HOME/AGENTS.md"
cp "$KIT_ROOT/codex/AGENTS.md" "$CODEX_HOME/AGENTS.md"
backup_if_exists "$CODEX_HOME/hooks.json"
cp "$KIT_ROOT/codex/hooks.json" "$CODEX_HOME/hooks.json"
for hook in prompt_guard.py session_start.py; do
  cp "$KIT_ROOT/codex/hooks/$hook" "$CODEX_HOME/hooks/$hook"
done
chmod +x "$CODEX_HOME/hooks/"*.py

log "CLI router"
mkdir -p "$HOME/.local/bin"
cp "$KIT_ROOT/bin/cx-task" "$HOME/.local/bin/cx-task"
chmod +x "$HOME/.local/bin/cx-task"

BASHRC="$HOME/.bashrc"
MARKER="# >>> codex-sglang-workflow-kit >>>"
if ! grep -Fq "$MARKER" "$BASHRC" 2>/dev/null; then
  cat >> "$BASHRC" <<'EOF'

# >>> codex-sglang-workflow-kit >>>
export PATH="$HOME/.local/bin:$PATH"
alias cx='codex --profile sglang'
alias cxl='codex --profile sglang-lite'
alias cxh='codex --profile sglang-hard'
alias cxx='codex --profile sglang-xhigh'
# <<< codex-sglang-workflow-kit <<<
EOF
fi

log "VS Code / Codex extension"
if command -v code >/dev/null 2>&1; then
  if ! code --list-extensions 2>/dev/null | grep -qi '^openai\.chatgpt$'; then
    echo "OpenAI.chatgpt is not visible to the current VS Code CLI; attempting installation."
    code --install-extension OpenAI.chatgpt --force || \
      echo "Warning: install OpenAI.chatgpt manually from the VS Code Extensions panel." >&2
  else
    echo "OpenAI.chatgpt extension detected."
  fi
else
  echo "Warning: VS Code 'code' CLI is not available inside WSL yet." >&2
  echo "Open VS Code on Windows with the Remote - WSL extension, then rerun verification." >&2
fi

log "Git conflict ergonomics"
git config --global rerere.enabled true
git config --global rerere.autoupdate true
git config --global merge.conflictStyle zdiff3

log "Verification"
command -v git
git --version
command -v gh
gh --version | head -n1
command -v rg
rg --version | head -n1
command -v uv
uv --version
codex_path="$(command -v codex)"
echo "$codex_path"
if [[ "$codex_path" == /mnt/c/* ]]; then
  echo "ERROR: Windows Codex shim is still first in WSL PATH: $codex_path" >&2
  exit 1
fi
codex --version
command -v semble

printf '
Done. Next:
  source ~/.bashrc
  gh auth login
  ./wsl/03-setup-sglang-workspace.sh   # run from the kit directory

Recommended daily UI after workspace setup:
  cd ~/code/sglang
  code .
  # confirm VS Code shows WSL: Ubuntu, then use the Codex sidebar

CLI remains optional:
  cx
'
