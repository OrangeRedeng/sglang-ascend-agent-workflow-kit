#!/usr/bin/env bash
set -euo pipefail
KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/sglang-workflow"
INSTALL_MANIFEST="$CONFIG_DIR/install.env"
MODELS_CONFIG="$CONFIG_DIR/models.env"
LEVEL=""; PRIMARY=""; ROUTING="primary"; WORKSPACE="${SGLANG:-$HOME/code/sglang}"
NON_INTERACTIVE=0; ASSUME_DEFAULTS=0; UPDATE_MODE=0; ENABLE_GLM=""; GLM_REGION="china"; GLM_ROUTING="balanced"
WITH_LOCAL=0; WITH_CHEAP=0; WITH_STRONG=0; CHEAP_PRESET=""; STRONG_PRESET=""

usage(){ cat <<'TXT'
Usage: ./setup.sh [options]
  --level light|standard|full|custom
  --primary codex|local|cheap|strong|none
  --routing primary|hybrid
  --workspace PATH
  --enable-glm | --disable-glm
  --glm-region china|global
  --glm-routing balanced|openai|glm
  --with-local | --with-cheap | --with-strong
  --cheap-preset NAME | --strong-preset NAME
  --list-model-presets
  --non-interactive
  --yes, -y
  --update

v0.3.1 default: Codex/OpenAI remains the daily harness. GLM Coding Plan is an optional
Codex provider. OpenCode is installed only for local/cheap/strong external tiers.
TXT
}
while [[ $# -gt 0 ]]; do case "$1" in
  --level) LEVEL="${2:?}"; shift 2;; --level=*) LEVEL="${1#*=}"; shift;;
  --primary) PRIMARY="${2:?}"; shift 2;; --primary=*) PRIMARY="${1#*=}"; shift;;
  --routing) ROUTING="${2:?}"; shift 2;; --routing=*) ROUTING="${1#*=}"; shift;;
  --workspace) WORKSPACE="${2:?}"; shift 2;; --workspace=*) WORKSPACE="${1#*=}"; shift;;
  --enable-glm) ENABLE_GLM=1; shift;; --disable-glm) ENABLE_GLM=0; shift;;
  --glm-region) GLM_REGION="${2:?}"; shift 2;; --glm-region=*) GLM_REGION="${1#*=}"; shift;;
  --glm-routing) GLM_ROUTING="${2:?}"; shift 2;; --glm-routing=*) GLM_ROUTING="${1#*=}"; shift;;
  --with-local) WITH_LOCAL=1; shift;; --with-cheap) WITH_CHEAP=1; shift;; --with-strong) WITH_STRONG=1; shift;;
  --cheap-preset) CHEAP_PRESET="${2:?}"; WITH_CHEAP=1; shift 2;; --strong-preset) STRONG_PRESET="${2:?}"; WITH_STRONG=1; shift 2;;
  --list-model-presets) "$KIT_ROOT/bin/workflow-configure" --list-presets; exit 0;;
  --non-interactive) NON_INTERACTIVE=1; shift;; --yes|-y) ASSUME_DEFAULTS=1; shift;;
  --update) UPDATE_MODE=1; NON_INTERACTIVE=1; shift;; -h|--help) usage; exit 0;;
  *) echo "Unknown option: $1" >&2; usage; exit 2;; esac; done

ask_yes_no(){ local p="$1" d="${2:-yes}" a; if [[ $ASSUME_DEFAULTS == 1 || $NON_INTERACTIVE == 1 || ! -t 0 ]]; then [[ $d == yes ]]; return; fi; while true; do read -r -p "$p $([[ $d == yes ]] && echo '[Y/n]' || echo '[y/N]') " a; a="${a,,}"; [[ -z $a ]] && a="$d"; case "$a" in y|yes)return 0;;n|no)return 1;;esac; done; }
ask_value(){ local p="$1" d="${2:-}" a; if [[ $NON_INTERACTIVE == 1 || ! -t 0 ]]; then printf '%s' "$d"; return; fi; read -r -p "$p${d:+ [$d]} " a; printf '%s' "${a:-$d}"; }

INSTALL_BASE_PACKAGES=0; INSTALL_GH=0; INSTALL_UV=0; INSTALL_CODEX=0; INSTALL_OPENCODE=0; INSTALL_SEMBLE=0; INSTALL_ROUTERS=0; INSTALL_GLOBAL_CODEX=0; INSTALL_REPO_WORKFLOW=0; INSTALL_ASCEND_SKILLS=0; INSTALL_BBUF_SKILLS=0; INSTALL_KERNEL_REPO=0; INSTALL_KERNEL_SKILLS=0; INSTALL_CANNBOT_SKILLS=0; INSTALL_KERNELHIVE_SKILLS=0; INSTALL_SERENA=0; INSTALL_VSCODE_CODEX=0; INSTALL_GLM=0

if [[ $UPDATE_MODE == 1 ]]; then
  [[ -f $INSTALL_MANIFEST ]] || { echo "No saved install manifest: $INSTALL_MANIFEST" >&2; exit 2; }
  # shellcheck disable=SC1090
  source "$INSTALL_MANIFEST"
  LEVEL="${INSTALL_LEVEL:-standard}"; WORKSPACE="${SGLANG_WORKSPACE:-$WORKSPACE}"; PRIMARY="${AI_PRIMARY_BACKEND:-codex}"; ROUTING="${AI_ROUTING_MODE:-primary}"; INSTALL_GLM="${INSTALL_GLM:-0}"
else
  if [[ -z $LEVEL ]]; then
    if [[ $NON_INTERACTIVE == 1 || ! -t 0 ]]; then LEVEL=standard; else
      cat <<'TXT'
Select installation level:
  1) Light    - SGLang + core Ascend skills only
  2) Standard - Codex-first workflow + core Ascend skills (Semble/Serena optional)
  3) Full     - Standard + Semble + CANNBot + KernelHive + kernel repo + Serena + BBuf
  4) Custom   - choose components
TXT
      c="$(ask_value 'Selection:' '2')"; case "$c" in 1|light)LEVEL=light;;2|standard)LEVEL=standard;;3|full)LEVEL=full;;4|custom)LEVEL=custom;;*)exit 2;;esac
    fi
  fi
  case "$LEVEL" in
    light) PRIMARY=none; INSTALL_ASCEND_SKILLS=1;;
    standard) INSTALL_BASE_PACKAGES=1; INSTALL_GH=1; INSTALL_CODEX=1; INSTALL_GLOBAL_CODEX=1; INSTALL_VSCODE_CODEX=1; INSTALL_ROUTERS=1; INSTALL_REPO_WORKFLOW=1; INSTALL_ASCEND_SKILLS=1;;
    full) INSTALL_BASE_PACKAGES=1; INSTALL_GH=1; INSTALL_UV=1; INSTALL_CODEX=1; INSTALL_GLOBAL_CODEX=1; INSTALL_VSCODE_CODEX=1; INSTALL_SEMBLE=1; INSTALL_ROUTERS=1; INSTALL_REPO_WORKFLOW=1; INSTALL_ASCEND_SKILLS=1; INSTALL_BBUF_SKILLS=1; INSTALL_KERNEL_REPO=1; INSTALL_KERNEL_SKILLS=1; INSTALL_CANNBOT_SKILLS=1; INSTALL_KERNELHIVE_SKILLS=1; INSTALL_SERENA=1;;
    custom)
      ask_yes_no 'Install Codex CLI + OpenAI VS Code extension?' yes && { INSTALL_CODEX=1; INSTALL_GLOBAL_CODEX=1; INSTALL_VSCODE_CODEX=1; }
      ask_yes_no 'Install workflow router/handoffs?' yes && { INSTALL_ROUTERS=1; INSTALL_REPO_WORKFLOW=1; }
      ask_yes_no 'Install Semble semantic search?' no && { INSTALL_SEMBLE=1; INSTALL_UV=1; }
      ask_yes_no 'Install core Ascend/torch_npu skills?' yes && INSTALL_ASCEND_SKILLS=1
      ask_yes_no 'Install CANNBot kernel skills?' yes && { INSTALL_CANNBOT_SKILLS=1; INSTALL_KERNEL_SKILLS=1; }
      ask_yes_no 'Install KernelHive experimental AscendC skills?' no && { INSTALL_KERNELHIVE_SKILLS=1; INSTALL_KERNEL_SKILLS=1; }
      ask_yes_no 'Clone sgl-kernel-npu?' yes && INSTALL_KERNEL_REPO=1
      ask_yes_no 'Install Serena?' no && { INSTALL_SERENA=1; INSTALL_UV=1; }
      INSTALL_BASE_PACKAGES=1; INSTALL_GH=1;;
    *) echo "Invalid level: $LEVEL" >&2; exit 2;;
  esac
  if [[ $LEVEL != light ]]; then
    if [[ -z $PRIMARY ]]; then ask_yes_no 'Use Codex / OpenAI extension as the primary harness?' yes && PRIMARY=codex || PRIMARY=none; fi
    case "$PRIMARY" in codex) INSTALL_CODEX=1; INSTALL_GLOBAL_CODEX=1; INSTALL_VSCODE_CODEX=1;; local|cheap|strong) INSTALL_OPENCODE=1;; none);; *) echo "Invalid primary: $PRIMARY" >&2; exit 2;; esac
    [[ "$PRIMARY" == local ]] && WITH_LOCAL=1
    [[ "$PRIMARY" == cheap ]] && WITH_CHEAP=1
    [[ "$PRIMARY" == strong ]] && WITH_STRONG=1
    if [[ -z $ENABLE_GLM && $INSTALL_CODEX == 1 && $NON_INTERACTIVE != 1 && -t 0 ]]; then ask_yes_no 'Enable GLM Coding Plan inside Codex?' no && ENABLE_GLM=1 || ENABLE_GLM=0; fi
    [[ ${ENABLE_GLM:-0} == 1 ]] && { INSTALL_GLM=1; INSTALL_CODEX=1; INSTALL_GLOBAL_CODEX=1; INSTALL_VSCODE_CODEX=1; INSTALL_ROUTERS=1; INSTALL_REPO_WORKFLOW=1; }
    [[ $WITH_LOCAL == 1 || $WITH_CHEAP == 1 || $WITH_STRONG == 1 ]] && INSTALL_OPENCODE=1
  fi
fi
case "$ROUTING" in primary|hybrid);;*) echo "Invalid routing: $ROUTING" >&2; exit 2;;esac
case "$GLM_REGION" in china|global);;*) echo "Invalid GLM region: $GLM_REGION" >&2; exit 2;;esac
case "$GLM_ROUTING" in balanced|openai|glm);;*) echo "Invalid GLM routing: $GLM_ROUTING" >&2; exit 2;;esac
mkdir -p "$CONFIG_DIR"
cat <<PLAN
Installation plan
-----------------
Level:              $LEVEL
Workspace:          $WORKSPACE
Primary backend:    $PRIMARY
Codex:              $INSTALL_CODEX
GLM in Codex:       $INSTALL_GLM ($GLM_REGION / $GLM_ROUTING)
OpenCode:           $INSTALL_OPENCODE
Core Ascend skills: $INSTALL_ASCEND_SKILLS
CANNBot skills:     $INSTALL_CANNBOT_SKILLS
KernelHive skills:  $INSTALL_KERNELHIVE_SKILLS
Semble:             $INSTALL_SEMBLE
Serena:             $INSTALL_SERENA
PLAN
[[ $UPDATE_MODE == 1 ]] || ask_yes_no 'Apply this plan?' yes || exit 0
export INSTALL_BASE_PACKAGES INSTALL_GH INSTALL_UV INSTALL_CODEX INSTALL_OPENCODE INSTALL_SEMBLE INSTALL_ROUTERS INSTALL_GLOBAL_CODEX INSTALL_REPO_WORKFLOW INSTALL_ASCEND_SKILLS INSTALL_BBUF_SKILLS INSTALL_KERNEL_REPO INSTALL_KERNEL_SKILLS INSTALL_CANNBOT_SKILLS INSTALL_KERNELHIVE_SKILLS INSTALL_SERENA INSTALL_VSCODE_CODEX INSTALL_GLM
export INSTALL_LEVEL="$LEVEL" SGLANG="$WORKSPACE" WORKFLOW_ACTION="$([[ $UPDATE_MODE == 1 ]] && echo update || echo install)"
[[ $LEVEL == light ]] || "$KIT_ROOT/wsl/02-bootstrap-wsl.sh"
[[ $INSTALL_SERENA == 1 ]] && "$KIT_ROOT/wsl/05-install-serena-optional.sh"
"$KIT_ROOT/wsl/03-setup-sglang-workspace.sh"

if [[ $INSTALL_ROUTERS == 1 ]]; then
  [[ -f $MODELS_CONFIG ]] || { cp "$KIT_ROOT/opencode/models.env.example" "$MODELS_CONFIG"; chmod 600 "$MODELS_CONFIG"; }
  "$KIT_ROOT/bin/workflow-configure" --primary "$PRIMARY" --routing "$ROUTING" --non-interactive
  if [[ $INSTALL_GLM == 1 && $UPDATE_MODE != 1 ]]; then
    if [[ $NON_INTERACTIVE == 1 ]]; then "$KIT_ROOT/bin/workflow-configure" --enable-glm --glm-region "$GLM_REGION" --glm-routing "$GLM_ROUTING" --non-interactive
    else "$KIT_ROOT/bin/workflow-configure" --enable-glm --glm-region "$GLM_REGION" --glm-routing "$GLM_ROUTING"
    fi
  elif [[ ${ENABLE_GLM:-} == 0 && $UPDATE_MODE != 1 ]]; then
    "$KIT_ROOT/bin/workflow-configure" --disable-glm --non-interactive
  fi
  configure_slot() {
    local slot="$1" preset="${2:-}"; local args=(--slot "$slot")
    [[ -n "$preset" ]] && args+=(--preset "$preset")
    [[ $NON_INTERACTIVE == 1 ]] && args+=(--non-interactive)
    "$KIT_ROOT/bin/workflow-configure" "${args[@]}"
  }
  [[ $WITH_LOCAL == 1 ]] && configure_slot local ""
  [[ $WITH_CHEAP == 1 ]] && configure_slot cheap "$CHEAP_PRESET"
  [[ $WITH_STRONG == 1 ]] && configure_slot strong "$STRONG_PRESET"
fi
cat > "$INSTALL_MANIFEST" <<MANIFEST
INSTALL_LEVEL=$LEVEL
SGLANG_WORKSPACE=$(printf '%q' "$WORKSPACE")
AI_PRIMARY_BACKEND=$PRIMARY
AI_ROUTING_MODE=$ROUTING
INSTALL_BASE_PACKAGES=$INSTALL_BASE_PACKAGES
INSTALL_GH=$INSTALL_GH
INSTALL_UV=$INSTALL_UV
INSTALL_CODEX=$INSTALL_CODEX
INSTALL_OPENCODE=$INSTALL_OPENCODE
INSTALL_SEMBLE=$INSTALL_SEMBLE
INSTALL_ROUTERS=$INSTALL_ROUTERS
INSTALL_GLOBAL_CODEX=$INSTALL_GLOBAL_CODEX
INSTALL_REPO_WORKFLOW=$INSTALL_REPO_WORKFLOW
INSTALL_ASCEND_SKILLS=$INSTALL_ASCEND_SKILLS
INSTALL_BBUF_SKILLS=$INSTALL_BBUF_SKILLS
INSTALL_KERNEL_REPO=$INSTALL_KERNEL_REPO
INSTALL_KERNEL_SKILLS=$INSTALL_KERNEL_SKILLS
INSTALL_CANNBOT_SKILLS=$INSTALL_CANNBOT_SKILLS
INSTALL_KERNELHIVE_SKILLS=$INSTALL_KERNELHIVE_SKILLS
INSTALL_SERENA=$INSTALL_SERENA
INSTALL_VSCODE_CODEX=$INSTALL_VSCODE_CODEX
INSTALL_GLM=$INSTALL_GLM
MANIFEST
chmod 600 "$INSTALL_MANIFEST"
printf '%s\n' "$(tr -d '[:space:]' < "$KIT_ROOT/VERSION")" > "$CONFIG_DIR/workflow-kit-version"
echo "Setup complete: $WORKSPACE"
