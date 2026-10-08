#!/usr/bin/env bash
set -euo pipefail
KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/sglang-workflow"
enabled(){ [[ "${1:-0}" == 1 ]]; }

if enabled "${INSTALL_BASE_PACKAGES:-1}"; then
  sudo apt-get update
  sudo apt-get install -y build-essential cmake ninja-build clang lld ccache pkg-config git git-lfs curl wget ca-certificates gnupg unzip zip jq ripgrep fd-find python3 python3-venv python3-pip
  git lfs install
fi
mkdir -p "$CONFIG_DIR" "$HOME/.local/bin" "$HOME/.local/npm/bin"
export PATH="$HOME/.local/npm/bin:$HOME/.local/bin:$PATH"
hash -r

if enabled "${INSTALL_GH:-1}" && ! command -v gh >/dev/null 2>&1; then
  sudo apt-get install -y gh || true
fi

if enabled "${INSTALL_CODEX:-1}"; then
  codex_path="$(command -v codex 2>/dev/null || true)"
  if [[ -z "$codex_path" || "$codex_path" == /mnt/c/* ]] || ! timeout 20 codex --version >/dev/null 2>&1; then
    echo "Codex CLI is missing/broken in WSL; installing user-local copy."
    "$KIT_ROOT/bin/workflow-codex" repair || echo "WARNING: Codex CLI repair failed; VS Code extension setup continues." >&2
    export PATH="$HOME/.local/npm/bin:$HOME/.local/bin:$PATH"
    hash -r
  fi
fi

# Install only workflow commands that remain part of v0.5.
for f in workflow-codex workflow-copilot workflow-skills workflow-handoffs workflow-exp workflow-setup; do
  install -m 0755 "$KIT_ROOT/bin/$f" "$HOME/.local/bin/$f"
done
cp "$KIT_ROOT/skills.lock.json" "$CONFIG_DIR/skills.lock.json"

mkdir -p "$CODEX_HOME/hooks"
if [[ ! -e "$CODEX_HOME/config.toml" ]]; then
  cp "$KIT_ROOT/codex/config/config.toml" "$CODEX_HOME/config.toml"
fi
# Removes only the old kit-managed block (including kit-owned Semble). User config stays intact.
python3 "$KIT_ROOT/scripts/merge-codex-config.py" "$CODEX_HOME/config.toml"
[[ -e "$CODEX_HOME/AGENTS.md" ]] || cp "$KIT_ROOT/codex/AGENTS.md" "$CODEX_HOME/AGENTS.md"
python3 "$KIT_ROOT/scripts/merge-codex-hooks.py" "$CODEX_HOME/hooks.json" "$KIT_ROOT/codex/hooks.json"
cp "$KIT_ROOT"/codex/hooks/*.py "$CODEX_HOME/hooks/"
chmod +x "$CODEX_HOME/hooks/"*.py

# Remove v0.3/v0.4 Codex-native GLM artifacts. GLM now lives only in Copilot Chat.
rm -f "$CODEX_HOME"/glm-*.config.toml "$CODEX_HOME/models.glm.json"

# Remove legacy kit entry points from ~/.local/bin.
for f in ai-task cheap-task codex-glm cx-task glm-task local-task strong-task workflow-configure workflow-kilo workflow-provider-token workflow-glm-copilot; do
  rm -f "$HOME/.local/bin/$f"
done

# Remove the Kilo VS Code extension and user-local CLI installed by v0.4.x.
if command -v code >/dev/null 2>&1; then
  if code --list-extensions 2>/dev/null | grep -qi '^kilocode\.kilo-code$'; then
    code --uninstall-extension kilocode.kilo-code >/dev/null 2>&1 || true
    echo "removed legacy Kilo VS Code extension"
  fi
fi
if [[ -d "$HOME/.local/npm/lib/node_modules/@kilocode/cli" ]]; then
  npm uninstall --global --prefix "$HOME/.local/npm" @kilocode/cli >/dev/null 2>&1 || true
  echo "removed legacy Kilo CLI"
fi

# Semble/Serena are no longer workflow dependencies. Remove tools only when they are
# present in uv's managed tool list; unrelated system installs are left untouched.
if command -v uv >/dev/null 2>&1; then
  uv tool uninstall semble >/dev/null 2>&1 || true
  uv tool uninstall serena-agent >/dev/null 2>&1 || true
fi

python3 - "$HOME/.bashrc" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); text=p.read_text() if p.exists() else ''
blocks=[
('# >>> codex-sglang-workflow-kit >>>','# <<< codex-sglang-workflow-kit <<<'),
('# >>> sglang-workflow-codex-user-prefix >>>','# <<< sglang-workflow-codex-user-prefix <<<'),
]
for a,b in blocks:
    if a in text and b in text:
        text=text.split(a,1)[0].rstrip()+'\n\n'+text.split(b,1)[1].lstrip('\n')
a,b=blocks[0]
managed='\n'.join([
    a,
    'export PATH="$HOME/.local/npm/bin:$HOME/.local/bin:$PATH"',
    "alias cx='codex'",
    b,
])
p.write_text(text.rstrip()+'\n\n'+managed+'\n')
PY

if command -v code >/dev/null 2>&1; then
  if enabled "${INSTALL_VSCODE_CODEX:-${INSTALL_CODEX:-0}}"; then
    code --list-extensions 2>/dev/null | grep -qi '^openai\.chatgpt$' || code --install-extension OpenAI.chatgpt --force || true
  fi
  if enabled "${INSTALL_VSCODE_COPILOT:-0}"; then
    code --list-extensions 2>/dev/null | grep -qi '^github\.copilot-chat$' || code --install-extension GitHub.copilot-chat --force || true
  fi
  if enabled "${INSTALL_CODEX_BRIDGE:-0}"; then
    code --list-extensions 2>/dev/null | grep -qi '^grikomsn\.openai-oauth-copilot-chat$' || code --install-extension grikomsn.openai-oauth-copilot-chat --force || true
  fi
  if enabled "${INSTALL_GLM_COPILOT:-0}"; then
    code --list-extensions 2>/dev/null | grep -qi '^yijiazhen-qi\.glm-for-github-copilot-chat$' || code --install-extension yijiazhen-qi.glm-for-github-copilot-chat --force || true
  fi
fi

git config --global rerere.enabled true
git config --global rerere.autoupdate true
git config --global merge.conflictStyle zdiff3
