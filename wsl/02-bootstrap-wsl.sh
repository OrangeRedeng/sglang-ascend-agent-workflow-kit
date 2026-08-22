#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/sglang-workflow"
STAMP="$(date +%Y%m%d-%H%M%S)"
KIT_VERSION="$(tr -d '[:space:]' < "$KIT_ROOT/VERSION")"

INSTALL_BASE_PACKAGES="${INSTALL_BASE_PACKAGES:-1}"
INSTALL_GH="${INSTALL_GH:-1}"
INSTALL_UV="${INSTALL_UV:-1}"
INSTALL_CODEX="${INSTALL_CODEX:-1}"
INSTALL_OPENCODE="${INSTALL_OPENCODE:-0}"
INSTALL_SEMBLE="${INSTALL_SEMBLE:-1}"
INSTALL_ROUTERS="${INSTALL_ROUTERS:-1}"
INSTALL_GLOBAL_CODEX="${INSTALL_GLOBAL_CODEX:-$INSTALL_CODEX}"
INSTALL_VSCODE_CODEX="${INSTALL_VSCODE_CODEX:-$INSTALL_CODEX}"

log() { printf '\n==> %s\n' "$*"; }
enabled() { [[ "${1:-0}" == 1 ]]; }
backup_if_exists() {
  local p="$1"
  if [[ -e "$p" || -L "$p" ]]; then
    cp -a "$p" "$p.bak-$STAMP"
    echo "Backup: $p.bak-$STAMP"
  fi
}

if enabled "$INSTALL_BASE_PACKAGES"; then
  log "Base packages"
  sudo apt-get update
  sudo apt-get install -y \
    build-essential cmake ninja-build clang lld ccache pkg-config \
    git git-lfs curl wget ca-certificates gnupg unzip zip jq ripgrep fd-find \
    python3 python3-venv python3-pip
  git lfs install
fi

mkdir -p "$CONFIG_DIR"
GLOBAL_MARKER="$CONFIG_DIR/workflow-kit-version"
INSTALLED_GLOBAL_VERSION="$(cat "$GLOBAL_MARKER" 2>/dev/null | tr -d '[:space:]' || true)"
if enabled "$INSTALL_GLOBAL_CODEX"; then
  legacy="$(cat "$CODEX_HOME/workflow-kit-version" 2>/dev/null | tr -d '[:space:]' || true)"
  [[ -z "$INSTALLED_GLOBAL_VERSION" ]] && INSTALLED_GLOBAL_VERSION="$legacy"
fi

log "Workflow-kit version preflight"
printf 'Installed global layer: %s\n' "${INSTALLED_GLOBAL_VERSION:-unversioned}"
printf 'Incoming kit:          %s\n' "$KIT_VERSION"
if [[ -n "$INSTALLED_GLOBAL_VERSION" ]]; then
  cmp="$(python3 "$KIT_ROOT/scripts/kit-version.py" compare "$INSTALLED_GLOBAL_VERSION" "$KIT_VERSION")" || exit 2
  if [[ "$cmp" == 1 && "${ALLOW_DOWNGRADE:-0}" != 1 ]]; then
    echo "ERROR: installed workflow layer $INSTALLED_GLOBAL_VERSION is newer than incoming $KIT_VERSION." >&2
    echo "Use ALLOW_DOWNGRADE=1 only for an intentional downgrade." >&2
    exit 2
  fi
fi

if enabled "$INSTALL_GH"; then
  log "GitHub CLI"
  if ! command -v gh >/dev/null 2>&1; then
    (type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
      && sudo mkdir -p -m 755 /etc/apt/keyrings \
      && out=$(mktemp) && wget -nv -O "$out" https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      && cat "$out" | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null \
      && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
      && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
         | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null \
      && sudo apt update \
      && sudo apt install gh -y
  fi
fi

if enabled "$INSTALL_UV" || enabled "$INSTALL_SEMBLE"; then
  log "uv"
  if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi
  export PATH="$HOME/.local/bin:$PATH"
fi

if enabled "$INSTALL_CODEX"; then
  log "Codex CLI"
  codex_path="$(command -v codex 2>/dev/null || true)"
  if [[ -z "$codex_path" || "$codex_path" == /mnt/c/* ]]; then
    [[ -n "$codex_path" ]] && echo "Ignoring Windows Codex shim in WSL: $codex_path"
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

Restart Ubuntu and rerun setup.
EOF
    exit 1
  fi
fi

if enabled "$INSTALL_OPENCODE"; then
  log "OpenCode model harness"
  if ! command -v opencode >/dev/null 2>&1; then
    curl -fsSL https://opencode.ai/install | bash
  fi
  export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"
  hash -r
  command -v opencode >/dev/null 2>&1 || { echo "ERROR: OpenCode installation did not produce an executable on PATH." >&2; exit 1; }
fi

if enabled "$INSTALL_SEMBLE"; then
  log "Semble"
  if ! command -v semble >/dev/null 2>&1; then
    uv tool install semble
  fi
  log "Semble prewarm"
  if ! timeout 180 uvx --from "semble[mcp]" semble --version >/dev/null 2>&1; then
    echo "Warning: Semble MCP prewarm did not finish; the first model session will retry." >&2
  fi
  if ! timeout 180 semble search "workflow bootstrap" "$KIT_ROOT" --top-k 1 >/dev/null 2>&1; then
    echo "Warning: Semble embedding/index prewarm did not finish; the first search may be slower." >&2
  fi
fi

if enabled "$INSTALL_GLOBAL_CODEX"; then
  log "Codex configuration and lifecycle hooks"
  mkdir -p "$CODEX_HOME/hooks"
  for f in config.toml sglang-lite.config.toml sglang.config.toml sglang-hard.config.toml sglang-xhigh.config.toml; do
    backup_if_exists "$CODEX_HOME/$f"
    cp "$KIT_ROOT/codex/config/$f" "$CODEX_HOME/$f"
  done
  if enabled "$INSTALL_SEMBLE" && command -v semble >/dev/null 2>&1; then
    semble_version="$(semble --version 2>/dev/null | awk '{print $NF}' || true)"
    if [[ "$semble_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+ ]]; then
      sed -i "s#semble\[mcp\]#semble[mcp]==$semble_version#g" "$CODEX_HOME/config.toml"
      echo "Pinned Semble MCP to $semble_version in $CODEX_HOME/config.toml"
    fi
  elif ! enabled "$INSTALL_SEMBLE"; then
    # Avoid a broken mandatory MCP when Semble was intentionally omitted.
    python3 - "$CODEX_HOME/config.toml" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); text=p.read_text(encoding='utf-8')
marker='\n[mcp_servers.semble]\n'
if marker in text:
    text=text.split(marker,1)[0].rstrip()+"\n"
p.write_text(text,encoding='utf-8')
PY
  fi
  backup_if_exists "$CODEX_HOME/AGENTS.md"
  cp "$KIT_ROOT/codex/AGENTS.md" "$CODEX_HOME/AGENTS.md"
  backup_if_exists "$CODEX_HOME/hooks.json"
  cp "$KIT_ROOT/codex/hooks.json" "$CODEX_HOME/hooks.json"
  for hook in prompt_guard.py session_start.py; do
    cp "$KIT_ROOT/codex/hooks/$hook" "$CODEX_HOME/hooks/$hook"
  done
  chmod +x "$CODEX_HOME/hooks/"*.py
  printf '%s\n' "$KIT_VERSION" > "$CODEX_HOME/workflow-kit-version"
fi

if enabled "$INSTALL_ROUTERS"; then
  log "Workflow CLI"
  mkdir -p "$HOME/.local/bin" "$CONFIG_DIR"
  for tool in cx-task ai-task local-task cheap-task strong-task workflow-configure; do
    cp "$KIT_ROOT/bin/$tool" "$HOME/.local/bin/$tool"
    chmod +x "$HOME/.local/bin/$tool"
  done
  if [[ ! -f "$CONFIG_DIR/models.env" ]]; then
    cp "$KIT_ROOT/opencode/models.env.example" "$CONFIG_DIR/models.env"
    chmod 600 "$CONFIG_DIR/models.env"
    echo "Created model configuration: $CONFIG_DIR/models.env"
  else
    echo "Preserved model configuration: $CONFIG_DIR/models.env"
  fi
fi

BASHRC="$HOME/.bashrc"
MARKER="# >>> codex-sglang-workflow-kit >>>"
if enabled "$INSTALL_ROUTERS" || enabled "$INSTALL_CODEX" || enabled "$INSTALL_OPENCODE"; then
  # Replace the managed block so profile changes are idempotent.
  python3 - "$BASHRC" "$INSTALL_CODEX" "$INSTALL_OPENCODE" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); codex=sys.argv[2]=='1'; opencode=sys.argv[3]=='1'
text=p.read_text(encoding='utf-8') if p.exists() else ''
start='# >>> codex-sglang-workflow-kit >>>'; end='# <<< codex-sglang-workflow-kit <<<'
if start in text and end in text:
    before=text.split(start,1)[0].rstrip()
    after=text.split(end,1)[1].lstrip('\n')
    text=before+'\n\n'+after if after else before+'\n'
lines=[start, 'export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"']
if codex:
    lines += ["alias cx='codex --profile sglang'", "alias cxl='codex --profile sglang-lite'", "alias cxh='codex --profile sglang-hard'", "alias cxx='codex --profile sglang-xhigh'"]
lines.append(end)
block='\n'.join(lines)
text=text.rstrip()+"\n\n"+block+"\n"
p.write_text(text,encoding='utf-8')
PY
fi

if enabled "$INSTALL_VSCODE_CODEX"; then
  log "VS Code Codex extension"
  if command -v code >/dev/null 2>&1; then
    if ! code --list-extensions 2>/dev/null | grep -qi '^openai\.chatgpt$'; then
      code --install-extension OpenAI.chatgpt --force || echo "Warning: install OpenAI.chatgpt manually from the VS Code Extensions panel." >&2
    fi
  else
    echo "Warning: VS Code 'code' CLI is not available inside WSL." >&2
  fi
fi

log "Git conflict ergonomics"
git config --global rerere.enabled true
git config --global rerere.autoupdate true
git config --global merge.conflictStyle zdiff3

printf '%s\n' "$KIT_VERSION" > "$GLOBAL_MARKER"

echo
log "Verification"
command -v git >/dev/null && git --version
if enabled "$INSTALL_GH"; then command -v gh && gh --version | head -n1; fi
if enabled "$INSTALL_UV"; then command -v uv && uv --version; fi
if enabled "$INSTALL_CODEX"; then command -v codex && codex --version; fi
if enabled "$INSTALL_SEMBLE"; then command -v semble; fi
if enabled "$INSTALL_OPENCODE"; then command -v opencode && opencode --version || true; fi
if enabled "$INSTALL_ROUTERS"; then command -v ai-task >/dev/null || true; fi

cat <<'EOF'

WSL bootstrap complete.
The workspace layer is installed by wsl/03-setup-sglang-workspace.sh (normally called by setup.sh).
EOF
