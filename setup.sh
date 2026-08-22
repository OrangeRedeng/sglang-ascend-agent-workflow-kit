#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/sglang-workflow"
INSTALL_MANIFEST="$CONFIG_DIR/install.env"
MODELS_CONFIG="$CONFIG_DIR/models.env"

LEVEL=""
PRIMARY=""
ROUTING="primary"
CODEX_FALLBACK=0
WORKSPACE="${SGLANG:-$HOME/code/sglang}"
NON_INTERACTIVE=0
UPDATE_MODE=0
ASSUME_DEFAULTS=0
WORKSPACE_EXPLICIT=0
CONFIGURE_LOCAL=0
CONFIGURE_CHEAP=0
CONFIGURE_STRONG=0
CHEAP_PRESET=""
STRONG_PRESET=""

usage() {
  cat <<'USAGE'
Usage: ./setup.sh [options]

Interactive setup is the default.

Options:
  --level light|standard|full|custom
  --primary codex|local|cheap|strong|api|none
  --routing primary|hybrid
  --workspace PATH
  --with-local             Configure the optional self-hosted slot
  --with-cheap             Configure the optional low-cost API slot
  --with-strong            Configure the optional stronger API slot
  --cheap-preset NAME      Apply a workflow-configure preset to the cheap slot
  --strong-preset NAME     Apply a workflow-configure preset to the strong slot
  --list-model-presets     Print available external-provider presets and exit
  --with-codex-fallback    Allow Codex fallback in hybrid mode when Codex is not primary
  --non-interactive        Do not ask questions; use flags/env/defaults
  --yes, -y                Accept default answers to confirmation prompts
  --update                 Replay the saved install manifest without changing model secrets
  -h, --help

Installation levels:
  light     SGLang + Ascend skills only. No model client, router, hooks, Semble, or runtime state.
  standard  Core workflow/router, selected primary model, Semble, and core Ascend skills.
  full      Standard plus extended skills, Serena, and optional kernel skill bundles.
  custom    Choose workflow/tooling components individually.

Unattended external-model deployment:
  Export AI_LOCAL_*, AI_CHEAP_*, or AI_STRONG_* values before running setup.
  API keys are written only to ~/.config/sglang-workflow/models.env (mode 0600).
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --level) LEVEL="${2:?missing value}"; shift 2 ;;
    --level=*) LEVEL="${1#*=}"; shift ;;
    --primary) PRIMARY="${2:?missing value}"; shift 2 ;;
    --primary=*) PRIMARY="${1#*=}"; shift ;;
    --routing) ROUTING="${2:?missing value}"; shift 2 ;;
    --routing=*) ROUTING="${1#*=}"; shift ;;
    --workspace) WORKSPACE="${2:?missing value}"; WORKSPACE_EXPLICIT=1; shift 2 ;;
    --workspace=*) WORKSPACE="${1#*=}"; WORKSPACE_EXPLICIT=1; shift ;;
    --with-local) CONFIGURE_LOCAL=1; shift ;;
    --with-cheap) CONFIGURE_CHEAP=1; shift ;;
    --with-strong) CONFIGURE_STRONG=1; shift ;;
    --cheap-preset) CHEAP_PRESET="${2:?missing value}"; CONFIGURE_CHEAP=1; shift 2 ;;
    --cheap-preset=*) CHEAP_PRESET="${1#*=}"; CONFIGURE_CHEAP=1; shift ;;
    --strong-preset) STRONG_PRESET="${2:?missing value}"; CONFIGURE_STRONG=1; shift 2 ;;
    --strong-preset=*) STRONG_PRESET="${1#*=}"; CONFIGURE_STRONG=1; shift ;;
    --list-model-presets) "$KIT_ROOT/bin/workflow-configure" --list-presets; exit 0 ;;
    --with-codex-fallback) CODEX_FALLBACK=1; shift ;;
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    --yes|-y) ASSUME_DEFAULTS=1; shift ;;
    --update) UPDATE_MODE=1; NON_INTERACTIVE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

ask_yes_no() {
  local prompt="$1" default="${2:-yes}" answer suffix
  if [[ "$ASSUME_DEFAULTS" == 1 || "$NON_INTERACTIVE" == 1 || ! -t 0 ]]; then
    [[ "$default" == yes ]]
    return
  fi
  if [[ "$default" == yes ]]; then suffix="[Y/n]"; else suffix="[y/N]"; fi
  while true; do
    read -r -p "$prompt $suffix " answer
    answer="${answer,,}"
    [[ -z "$answer" ]] && answer="$default"
    case "$answer" in
      y|yes) return 0 ;;
      n|no) return 1 ;;
      *) echo "Please answer yes or no." ;;
    esac
  done
}

ask_value() {
  local prompt="$1" default="${2:-}" value
  if [[ "$NON_INTERACTIVE" == 1 || ! -t 0 ]]; then
    printf '%s' "$default"
    return
  fi
  if [[ -n "$default" ]]; then
    read -r -p "$prompt [$default] " value
  else
    read -r -p "$prompt " value
  fi
  printf '%s' "${value:-$default}"
}

normalize_primary() {
  case "$1" in
    api) printf 'strong' ;;
    codex|local|cheap|strong|none) printf '%s' "$1" ;;
    *) return 1 ;;
  esac
}

# Component flags persisted in install.env. Initialize before any manifest is read.
INSTALL_BASE_PACKAGES=0
INSTALL_GH=0
INSTALL_UV=0
INSTALL_CODEX=0
INSTALL_OPENCODE=0
INSTALL_SEMBLE=0
INSTALL_ROUTERS=0
INSTALL_GLOBAL_CODEX=0
INSTALL_REPO_WORKFLOW=0
INSTALL_ASCEND_SKILLS=0
INSTALL_BBUF_SKILLS=0
INSTALL_KERNEL_REPO=0
INSTALL_KERNEL_SKILLS=0
INSTALL_SERENA=0
INSTALL_VSCODE_CODEX=0

if [[ "$UPDATE_MODE" == 1 ]]; then
  if [[ ! -f "$INSTALL_MANIFEST" ]]; then
    echo "ERROR: no saved install manifest was found at $INSTALL_MANIFEST." >&2
    echo "Run ./setup.sh once interactively, or run a fresh non-interactive setup with explicit flags." >&2
    exit 2
  fi
  requested_workspace="$WORKSPACE"
  # install.env contains no secrets and is generated by this installer.
  # shellcheck disable=SC1090
  source "$INSTALL_MANIFEST"
  LEVEL="${INSTALL_LEVEL:-standard}"
  # v0.2.0 final contract: Light means SGLang + Ascend skills only.
  # Older pre-release manifests may have recorded INSTALL_ASCEND_SKILLS=0.
  if [[ "$LEVEL" == light ]]; then INSTALL_ASCEND_SKILLS=1; fi
  PRIMARY="${AI_PRIMARY_BACKEND:-codex}"
  ROUTING="${AI_ROUTING_MODE:-primary}"
  CODEX_FALLBACK="${AI_ENABLE_CODEX_FALLBACK:-0}"
  if [[ "$WORKSPACE_EXPLICIT" == 1 ]]; then
    WORKSPACE="$requested_workspace"
  else
    WORKSPACE="${SGLANG_WORKSPACE:-$WORKSPACE}"
  fi
else
  if [[ -z "$LEVEL" ]]; then
    if [[ "$NON_INTERACTIVE" == 1 || ! -t 0 ]]; then
      LEVEL=standard
    else
      cat <<'EOF_LEVEL'

Select installation level:
  1) Light    - SGLang + Ascend skills only; no model client, router, hooks, or MCP tools
  2) Standard - core workflow + selected primary model + Semble + core Ascend skills
  3) Full     - Standard + extended skills + Serena + kernel skill bundle
  4) Custom   - choose components individually
EOF_LEVEL
      choice="$(ask_value "Selection:" "2")"
      case "$choice" in
        1|light) LEVEL=light ;;
        2|standard) LEVEL=standard ;;
        3|full) LEVEL=full ;;
        4|custom) LEVEL=custom ;;
        *) echo "Invalid installation level selection." >&2; exit 2 ;;
      esac
    fi
  fi

  case "$LEVEL" in
    light)
      PRIMARY=none
      ROUTING=primary
      CODEX_FALLBACK=0
      # Light is skills-only, but SGLang + Ascend skills are the core product.
      INSTALL_ASCEND_SKILLS=1
      ;;
    standard)
      INSTALL_BASE_PACKAGES=1
      INSTALL_GH=1
      INSTALL_UV=1
      INSTALL_SEMBLE=1
      INSTALL_ROUTERS=1
      INSTALL_REPO_WORKFLOW=1
      INSTALL_ASCEND_SKILLS=1
      ;;
    full)
      INSTALL_BASE_PACKAGES=1
      INSTALL_GH=1
      INSTALL_UV=1
      INSTALL_SEMBLE=1
      INSTALL_ROUTERS=1
      INSTALL_REPO_WORKFLOW=1
      INSTALL_ASCEND_SKILLS=1
      INSTALL_BBUF_SKILLS=1
      INSTALL_KERNEL_REPO=1
      INSTALL_KERNEL_SKILLS=1
      INSTALL_SERENA=1
      # OpenCode remains optional. It is installed only if an external backend is selected/configured.
      ;;
    custom)
      if ask_yes_no "Install base build/development packages?" yes; then INSTALL_BASE_PACKAGES=1; fi
      if ask_yes_no "Install GitHub CLI?" yes; then INSTALL_GH=1; fi
      if ask_yes_no "Install uv?" yes; then INSTALL_UV=1; fi
      if ask_yes_no "Install Semble semantic retrieval?" yes; then INSTALL_SEMBLE=1; INSTALL_UV=1; fi
      if ask_yes_no "Install the workflow router and handoff/log tooling?" yes; then INSTALL_ROUTERS=1; INSTALL_REPO_WORKFLOW=1; fi
      if ask_yes_no "Install core Ascend/torch_npu skills?" yes; then INSTALL_ASCEND_SKILLS=1; fi
      if ask_yes_no "Install BBuf extended skills?" no; then INSTALL_BBUF_SKILLS=1; fi
      if ask_yes_no "Clone sgl-kernel-npu and install optional kernel skills?" no; then
        INSTALL_KERNEL_REPO=1; INSTALL_KERNEL_SKILLS=1; INSTALL_ASCEND_SKILLS=1
      fi
      if ask_yes_no "Install Serena symbol-aware tooling?" no; then INSTALL_SERENA=1; INSTALL_UV=1; fi
      ;;
    *) echo "Invalid installation level: $LEVEL" >&2; exit 2 ;;
  esac

  if [[ "$LEVEL" != light ]]; then
    if [[ -z "$PRIMARY" ]]; then
      if ask_yes_no "Use Codex as the primary model?" yes; then
        PRIMARY=codex
      elif [[ "$NON_INTERACTIVE" == 1 || ! -t 0 ]]; then
        PRIMARY=none
      else
        cat <<'EOF_PRIMARY'
Choose the primary backend:
  1) Self-hosted OpenAI-compatible model
  2) External OpenAI-compatible API (strong slot)
  3) Low-cost external OpenAI-compatible API (cheap slot)
  4) No primary model backend
EOF_PRIMARY
        choice="$(ask_value "Selection:" "1")"
        case "$choice" in
          1|local) PRIMARY=local ;;
          2|api|strong) PRIMARY=strong ;;
          3|cheap) PRIMARY=cheap ;;
          4|none) PRIMARY=none ;;
          *) echo "Invalid primary backend selection." >&2; exit 2 ;;
        esac
      fi
    fi
    PRIMARY="$(normalize_primary "$PRIMARY")" || { echo "Invalid primary backend: $PRIMARY" >&2; exit 2; }
    case "$ROUTING" in primary|hybrid) ;; *) echo "Invalid routing mode: $ROUTING" >&2; exit 2 ;; esac

    case "$PRIMARY" in
      codex)
        INSTALL_CODEX=1; INSTALL_GLOBAL_CODEX=1; INSTALL_VSCODE_CODEX=1
        ;;
      local)
        INSTALL_OPENCODE=1
        if ask_yes_no "Install Codex as an optional backend?" no; then
          INSTALL_CODEX=1; INSTALL_GLOBAL_CODEX=1; INSTALL_VSCODE_CODEX=1
          if [[ "$ROUTING" == hybrid ]] && ask_yes_no "Use Codex as an automatic hybrid fallback?" no; then CODEX_FALLBACK=1; fi
        fi
        ;;
      cheap|strong)
        INSTALL_OPENCODE=1
        if ask_yes_no "Install Codex as an optional backend?" no; then
          INSTALL_CODEX=1; INSTALL_GLOBAL_CODEX=1; INSTALL_VSCODE_CODEX=1
          if [[ "$ROUTING" == hybrid ]] && ask_yes_no "Use Codex as an automatic hybrid fallback?" no; then CODEX_FALLBACK=1; fi
        fi
        ;;
      none)
        if ask_yes_no "Install Codex as an optional backend?" no; then
          INSTALL_CODEX=1; INSTALL_GLOBAL_CODEX=1; INSTALL_VSCODE_CODEX=1
        fi
        ;;
    esac

    # Optional worker prompts are skipped for explicit unattended flags, but remain available interactively.
    if [[ "$NON_INTERACTIVE" != 1 && -t 0 ]]; then
      if [[ "$PRIMARY" != local && "$CONFIGURE_LOCAL" != 1 ]] && ask_yes_no "Configure an optional self-hosted worker?" no; then CONFIGURE_LOCAL=1; fi
      if [[ "$PRIMARY" != cheap && "$CONFIGURE_CHEAP" != 1 ]] && ask_yes_no "Configure an optional low-cost API worker?" no; then CONFIGURE_CHEAP=1; fi
      if [[ "$PRIMARY" != strong && "$CONFIGURE_STRONG" != 1 ]] && ask_yes_no "Configure an optional stronger API worker?" no; then CONFIGURE_STRONG=1; fi
      if [[ "$PRIMARY" != none && "$ROUTING" == primary ]] && \
         [[ "$CONFIGURE_LOCAL" == 1 || "$CONFIGURE_CHEAP" == 1 || "$CONFIGURE_STRONG" == 1 ]] && \
         ask_yes_no "Enable hybrid automatic routing between configured backends?" no; then
        ROUTING=hybrid
      fi
    fi

    if [[ "$CONFIGURE_LOCAL" == 1 || "$CONFIGURE_CHEAP" == 1 || "$CONFIGURE_STRONG" == 1 ]]; then
      INSTALL_OPENCODE=1
    fi
    if [[ "$PRIMARY" == local ]]; then CONFIGURE_LOCAL=1; fi
    if [[ "$PRIMARY" == cheap ]]; then CONFIGURE_CHEAP=1; fi
    if [[ "$PRIMARY" == strong ]]; then CONFIGURE_STRONG=1; fi
  fi
fi

case "$LEVEL" in light|standard|full|custom) ;; *) echo "Invalid installation level: $LEVEL" >&2; exit 2 ;; esac
PRIMARY="$(normalize_primary "$PRIMARY")" || { echo "Invalid primary backend: $PRIMARY" >&2; exit 2; }
case "$ROUTING" in primary|hybrid) ;; *) echo "Invalid routing mode: $ROUTING" >&2; exit 2 ;; esac
[[ "$WORKSPACE" = /* ]] || WORKSPACE="$(pwd)/$WORKSPACE"
[[ "$INSTALL_SEMBLE" == 1 || "$INSTALL_SERENA" == 1 ]] && INSTALL_UV=1
if [[ "$PRIMARY" == local || "$PRIMARY" == cheap || "$PRIMARY" == strong ]]; then
  INSTALL_OPENCODE=1
  # External primary selection is meaningful only with the provider-neutral router/config layer.
  INSTALL_ROUTERS=1
  INSTALL_REPO_WORKFLOW=1
fi
if [[ "$PRIMARY" != codex && "$CODEX_FALLBACK" == 1 ]]; then
  INSTALL_CODEX=1
  INSTALL_GLOBAL_CODEX=1
  INSTALL_VSCODE_CODEX=1
fi

mkdir -p "$CONFIG_DIR"

cat <<EOF_PLAN

Installation plan
-----------------
Level:              $LEVEL
Workspace:          $WORKSPACE
Primary backend:    $PRIMARY
Routing mode:       $ROUTING
Codex fallback:     $CODEX_FALLBACK
Codex CLI/config:   $INSTALL_CODEX
OpenCode harness:   $INSTALL_OPENCODE
Workflow router:    $INSTALL_ROUTERS
Semble:             $INSTALL_SEMBLE
Core Ascend skills: $INSTALL_ASCEND_SKILLS
Extended BBuf:      $INSTALL_BBUF_SKILLS
Kernel skills:      $INSTALL_KERNEL_SKILLS
Serena:             $INSTALL_SERENA
EOF_PLAN

if [[ "$UPDATE_MODE" != 1 ]] && ! ask_yes_no "Apply this installation plan?" yes; then
  echo "Setup cancelled."
  exit 0
fi

# Light still needs Git to obtain/use the SGLang checkout and install skill files.
if ! command -v git >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y git
  else
    echo "ERROR: git is required." >&2
    exit 1
  fi
fi

export INSTALL_BASE_PACKAGES INSTALL_GH INSTALL_UV INSTALL_CODEX INSTALL_OPENCODE INSTALL_SEMBLE
export INSTALL_ROUTERS INSTALL_GLOBAL_CODEX INSTALL_VSCODE_CODEX INSTALL_SERENA
export INSTALL_REPO_WORKFLOW INSTALL_ASCEND_SKILLS INSTALL_BBUF_SKILLS INSTALL_KERNEL_REPO INSTALL_KERNEL_SKILLS
export INSTALL_LEVEL="$LEVEL" SGLANG="$WORKSPACE" WORKFLOW_ACTION="$([[ "$UPDATE_MODE" == 1 ]] && echo update || echo install)"

if [[ "$LEVEL" != light ]]; then
  "$KIT_ROOT/wsl/02-bootstrap-wsl.sh"
  if [[ "$INSTALL_SERENA" == 1 ]]; then
    "$KIT_ROOT/wsl/05-install-serena-optional.sh"
  fi
fi
"$KIT_ROOT/wsl/03-setup-sglang-workspace.sh"

update_model_metadata() {
  python3 - "$MODELS_CONFIG" "$PRIMARY" "$ROUTING" "$CODEX_FALLBACK" <<'PY'
from pathlib import Path
import shlex, sys
p=Path(sys.argv[1]); primary=sys.argv[2]; routing=sys.argv[3]; fallback=sys.argv[4]
lines=p.read_text(encoding='utf-8').splitlines() if p.exists() else []
updates={
    'AI_PRIMARY_BACKEND': primary,
    'AI_ROUTING_MODE': routing,
    'AI_ENABLE_CODEX_FALLBACK': '1' if fallback in {'1','true','yes','on'} else '0',
}
seen=set(); out=[]
for line in lines:
    stripped=line.lstrip()
    if '=' in line and not stripped.startswith('#'):
        k=line.split('=',1)[0].strip()
        if k in updates:
            out.append(f'{k}={shlex.quote(updates[k])}'); seen.add(k); continue
    out.append(line)
for k,v in updates.items():
    if k not in seen: out.append(f'{k}={shlex.quote(v)}')
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text('\n'.join(out).rstrip()+'\n',encoding='utf-8')
p.chmod(0o600)
PY
}

if [[ "$INSTALL_ROUTERS" == 1 ]]; then
  if [[ ! -f "$MODELS_CONFIG" ]]; then
    cp "$KIT_ROOT/opencode/models.env.example" "$MODELS_CONFIG"
    chmod 600 "$MODELS_CONFIG"
  fi
  update_model_metadata
fi

configure_slot() {
  local slot="$1" preset="" args=(--slot "$1")
  case "$slot" in
    cheap) preset="$CHEAP_PRESET" ;;
    strong) preset="$STRONG_PRESET" ;;
  esac
  [[ -n "$preset" ]] && args+=(--preset "$preset")
  if [[ "$NON_INTERACTIVE" == 1 || ! -t 0 ]]; then args+=(--non-interactive); fi
  "$KIT_ROOT/bin/workflow-configure" "${args[@]}"
}

if [[ "$UPDATE_MODE" != 1 && "$INSTALL_ROUTERS" == 1 ]]; then
  [[ "$CONFIGURE_LOCAL" == 1 ]] && configure_slot local
  [[ "$CONFIGURE_CHEAP" == 1 ]] && configure_slot cheap
  [[ "$CONFIGURE_STRONG" == 1 ]] && configure_slot strong
  # Slot configuration rewrites models.env; reassert primary/routing metadata afterwards.
  update_model_metadata
fi

# Persist installation topology only; never store model API keys in this file.
python3 - "$INSTALL_MANIFEST" "$LEVEL" "$WORKSPACE" "$PRIMARY" "$ROUTING" "$CODEX_FALLBACK" \
  "$INSTALL_BASE_PACKAGES" "$INSTALL_GH" "$INSTALL_UV" "$INSTALL_CODEX" "$INSTALL_OPENCODE" \
  "$INSTALL_SEMBLE" "$INSTALL_ROUTERS" "$INSTALL_GLOBAL_CODEX" "$INSTALL_REPO_WORKFLOW" \
  "$INSTALL_ASCEND_SKILLS" "$INSTALL_BBUF_SKILLS" "$INSTALL_KERNEL_REPO" "$INSTALL_KERNEL_SKILLS" \
  "$INSTALL_SERENA" "$INSTALL_VSCODE_CODEX" <<'PY'
from pathlib import Path
import shlex, sys
(
    manifest, level, workspace, primary, routing, fallback, base, gh, uv, codex, opencode,
    semble, routers, global_codex, repo_workflow, ascend, bbuf, kernel_repo, kernel_skills,
    serena, vscode_codex,
) = sys.argv[1:]
values = {
    "INSTALL_LEVEL": level,
    "SGLANG_WORKSPACE": workspace,
    "AI_PRIMARY_BACKEND": primary,
    "AI_ROUTING_MODE": routing,
    "AI_ENABLE_CODEX_FALLBACK": fallback,
    "INSTALL_BASE_PACKAGES": base,
    "INSTALL_GH": gh,
    "INSTALL_UV": uv,
    "INSTALL_CODEX": codex,
    "INSTALL_OPENCODE": opencode,
    "INSTALL_SEMBLE": semble,
    "INSTALL_ROUTERS": routers,
    "INSTALL_GLOBAL_CODEX": global_codex,
    "INSTALL_REPO_WORKFLOW": repo_workflow,
    "INSTALL_ASCEND_SKILLS": ascend,
    "INSTALL_BBUF_SKILLS": bbuf,
    "INSTALL_KERNEL_REPO": kernel_repo,
    "INSTALL_KERNEL_SKILLS": kernel_skills,
    "INSTALL_SERENA": serena,
    "INSTALL_VSCODE_CODEX": vscode_codex,
}
p = Path(manifest)
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("".join(f"{k}={shlex.quote(v)}\n" for k, v in values.items()), encoding="utf-8")
p.chmod(0o600)
PY

# Universal marker exists even for the skills-only Light profile.
printf '%s\n' "$(tr -d '[:space:]' < "$KIT_ROOT/VERSION")" > "$CONFIG_DIR/workflow-kit-version"

cat <<EOF_DONE

Setup complete.
Install manifest: $INSTALL_MANIFEST
Workspace:        $WORKSPACE
EOF_DONE
if [[ "$INSTALL_ROUTERS" == 1 ]]; then
  echo "Model config:      $MODELS_CONFIG"
  echo "Routing check:     ai-task --dry-run review 34855"
  echo "Reconfigure:       workflow-configure"
fi
if [[ "$INSTALL_CODEX" == 1 ]]; then
  cat <<'EOF_CODEX'
Codex hooks require one-time trust approval after installation or hook changes:
  cx
  /hooks
Approve SessionStart and UserPromptSubmit, then restart the Codex session.
EOF_CODEX
fi
