#!/usr/bin/env bash
set -euo pipefail
KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/sglang-workflow"
STAMP="$(date +%Y%m%d-%H%M%S)"
enabled(){ [[ "${1:-0}" == 1 ]]; }
backup(){ [[ -e "$1" || -L "$1" ]] && cp -a "$1" "$1.bak-$STAMP" || true; }

if enabled "${INSTALL_BASE_PACKAGES:-1}"; then
  sudo apt-get update
  sudo apt-get install -y build-essential cmake ninja-build clang lld ccache pkg-config git git-lfs curl wget ca-certificates gnupg unzip zip jq ripgrep fd-find python3 python3-venv python3-pip
  git lfs install
fi
mkdir -p "$CONFIG_DIR" "$HOME/.local/bin"
if enabled "${INSTALL_GH:-1}" && ! command -v gh >/dev/null 2>&1; then sudo apt-get install -y gh || true; fi
if enabled "${INSTALL_UV:-0}" || enabled "${INSTALL_SEMBLE:-0}"; then
  command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
if enabled "${INSTALL_CODEX:-1}"; then
  codex_path="$(command -v codex 2>/dev/null || true)"
  if [[ -z "$codex_path" || "$codex_path" == /mnt/c/* ]]; then curl -fsSL --connect-timeout 20 https://chatgpt.com/codex/install.sh | sh; fi
  export PATH="$HOME/.local/bin:$PATH"; hash -r
  command -v codex >/dev/null 2>&1 || { echo 'Codex install failed' >&2; exit 1; }
fi
if enabled "${INSTALL_OPENCODE:-0}"; then
  command -v opencode >/dev/null 2>&1 || curl -fsSL https://opencode.ai/install | bash
  export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"
  command -v opencode >/dev/null 2>&1 || { echo 'OpenCode install failed' >&2; exit 1; }
fi
if enabled "${INSTALL_SEMBLE:-0}"; then
  command -v semble >/dev/null 2>&1 || uv tool install semble
  timeout 180 uvx --from 'semble[mcp]' semble --version >/dev/null 2>&1 || true
fi
if enabled "${INSTALL_ROUTERS:-1}"; then
  for f in cx-task ai-task local-task cheap-task strong-task glm-task codex-glm workflow-configure workflow-provider-token workflow-skills workflow-handoffs workflow-exp; do
    install -m 0755 "$KIT_ROOT/bin/$f" "$HOME/.local/bin/$f"
  done
  cp "$KIT_ROOT/skills.lock.json" "$CONFIG_DIR/skills.lock.json"
  [[ -f "$CONFIG_DIR/models.env" ]] || { cp "$KIT_ROOT/opencode/models.env.example" "$CONFIG_DIR/models.env"; chmod 600 "$CONFIG_DIR/models.env"; }
fi

if enabled "${INSTALL_GLOBAL_CODEX:-${INSTALL_CODEX:-1}}"; then
  mkdir -p "$CODEX_HOME/hooks"

  # P0: never replace user-owned Codex global configuration. This preserves
  # current model/reasoning, project trust, hook trust hashes, memories and MCPs.
  if [[ ! -e "$CODEX_HOME/config.toml" ]]; then
    cp "$KIT_ROOT/codex/config/config.toml" "$CODEX_HOME/config.toml"
  fi
  semble_version=""
  if enabled "${INSTALL_SEMBLE:-0}" && command -v semble >/dev/null 2>&1; then
    semble_version="$(semble --version 2>/dev/null | awk '{print $NF}' || true)"
    [[ "$semble_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+ ]] || semble_version=""
  fi
  args=("$CODEX_HOME/config.toml")
  if enabled "${INSTALL_SEMBLE:-0}"; then args+=(--enable-semble); [[ -n "$semble_version" ]] && args+=(--semble-version "$semble_version"); fi
  python3 "$KIT_ROOT/scripts/merge-codex-config.py" "${args[@]}"

  # Kit-owned CLI profiles are isolated from the user's default OpenAI model/provider.
  for f in sglang-lite.config.toml sglang.config.toml sglang-hard.config.toml sglang-xhigh.config.toml; do
    cp "$KIT_ROOT/codex/config/$f" "$CODEX_HOME/$f"
  done
  cp "$KIT_ROOT/codex/models.glm.json" "$CODEX_HOME/models.glm.json"
  helper="$HOME/.local/bin/workflow-provider-token"
  for src in "$KIT_ROOT"/codex/config/glm-*.config.toml; do
    dst="$CODEX_HOME/$(basename "$src")"
    sed "s|__TOKEN_HELPER__|$helper|g" "$src" > "$dst"
  done

  # Do not overwrite a user-authored global AGENTS.md. Workspace rules remain authoritative.
  if [[ ! -e "$CODEX_HOME/AGENTS.md" ]]; then cp "$KIT_ROOT/codex/AGENTS.md" "$CODEX_HOME/AGENTS.md"; fi

  # Preserve unrelated hooks and stable existing hook entries so their trust hashes remain valid.
  python3 "$KIT_ROOT/scripts/merge-codex-hooks.py" "$CODEX_HOME/hooks.json" "$KIT_ROOT/codex/hooks.json"
  cp "$KIT_ROOT"/codex/hooks/*.py "$CODEX_HOME/hooks/"
  chmod +x "$CODEX_HOME/hooks/"*.py
  printf '%s\n' "$(tr -d '[:space:]' < "$KIT_ROOT/VERSION")" > "$CODEX_HOME/workflow-kit-version"
fi

python3 - "$HOME/.bashrc" "${INSTALL_CODEX:-0}" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); codex=sys.argv[2]=='1'; text=p.read_text() if p.exists() else ''
a='# >>> codex-sglang-workflow-kit >>>'; b='# <<< codex-sglang-workflow-kit <<<'
if a in text and b in text:
    text=text.split(a,1)[0].rstrip()+'\n\n'+text.split(b,1)[1].lstrip('\n')
lines=[a,'export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"']
if codex:
    lines += ["alias cx='codex --profile sglang'","alias cxl='codex --profile sglang-lite'","alias cxh='codex --profile sglang-hard'","alias cxx='codex --profile sglang-xhigh'"]
    lines += ["alias cg='codex-glm --effort high'","alias cgl='codex-glm --effort low'","alias cgh='codex-glm --effort high'","alias cgx='codex-glm --effort max'"]
lines.append(b)
p.write_text(text.rstrip()+'\n\n'+'\n'.join(lines)+'\n')
PY

if enabled "${INSTALL_VSCODE_CODEX:-${INSTALL_CODEX:-0}}" && command -v code >/dev/null 2>&1; then
  code --list-extensions 2>/dev/null | grep -qi '^openai\.chatgpt$' || code --install-extension OpenAI.chatgpt --force || true
fi

git config --global rerere.enabled true
git config --global rerere.autoupdate true
git config --global merge.conflictStyle zdiff3
