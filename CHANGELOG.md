# Changelog

All notable workflow-kit changes are recorded here. The project follows Semantic Versioning (`MAJOR.MINOR.PATCH`).

## [0.2.0] - 2026-08-22

Multi-model and installer architecture release: the workflow is provider-neutral, Codex is an optional/replaceable primary backend, and self-hosted/cloud workers are opt-in.

### Added

- Root `setup.sh` as the single interactive/non-interactive installation and deployment entrypoint.
- Independent installation levels: `light`, `standard`, `full`, and `custom`.
- `light` mode installs the SGLang + core Ascend/`torch_npu` skill layer and no model clients, hooks, router, Semble, Serena, or runtime artifacts.
- Explicit primary-backend selection during first setup: Codex, self-hosted OpenAI-compatible model, external OpenAI-compatible API, or none.
- `workflow-configure` utility for later primary/worker/routing reconfiguration with hidden API-key input.
- Saved non-secret install manifest at `~/.config/sglang-workflow/install.env` for repeatable upgrades/deployment.
- Universal version markers independent of Codex installation.
- Minimal/generated OpenCode project configuration so Semble/Serena MCP entries are added only when those components are installed.
- Vendor-neutral `ai-task` router with `local`, `cheap`, `strong`, and four Codex tiers.
- `local-task`, `cheap-task`, and `strong-task` explicit overrides.
- OpenCode workspace configuration with Semble and `AGENTS.override.md` instructions.
- Private `~/.config/sglang-workflow/models.env` configuration for OpenAI-compatible self-hosted/cloud endpoints; setup creates it once and updates preserve it.
- Cross-model handoff metadata (`producer` / `consumer`) while retaining the existing PR/branch/worktree/topic/freshness resolver.
- `docs/MULTI_MODEL.md` covering routing, self-hosted endpoints, cloud slots, safety boundaries, and dry-run validation.
- `docs/MODELS.md` with release-dated model/provider options, reference prices, free tiers, self-hosted guidance, and source links.
- Provider presets in `workflow-configure` for common OpenAI-compatible services without coupling the router to a vendor, including DeepSeek, Z.AI, Kimi Code, MiniMax, OpenRouter Free, Alibaba Coding Plan, and Alibaba Qwen Coder PAYG.

### Changed

- Project-priority invariant: SGLang + Ascend correctness remains authoritative regardless of model/provider; routing must not bypass NPU compatibility, profiling, benchmark, or validation gates.
- Hybrid hard-task routing keeps the user-selected primary backend first for review/verify/Ascend/NPU/distributed/performance/kernel/deep classes.
- `alibaba-payg` Qwen Coder provider preset alongside the fixed-price Alibaba Coding Plan preset.
- `ai-task` defaults to `AI_ROUTING_MODE=primary`; automatic tasks use the selected primary backend instead of always preferring external workers or hard-coding Codex as the terminal tier.
- Codex is installed/configured only when selected as primary or explicitly requested as an optional backend.
- Hybrid routing is opt-in; when Codex is not primary it becomes a fallback only with `AI_ENABLE_CODEX_FALLBACK=1`.
- Windows bootstrap no longer installs the OpenAI/Codex VS Code extension before the primary backend is selected.
- Full installation adds extended BBuf/Ascend kernel skills and Serena without forcing Codex as the primary model.
- Update flow replays the saved install manifest via `setup.sh --update` and preserves model credentials.
- Installer/configuration prompts and script interaction text are English-only.
- When Codex is primary, Ascend/NPU/distributed/kernel/performance tasks keep Codex-hard first; with another primary backend, Codex participates only when explicitly enabled as a fallback.
- Workflow rules now apply one-editing-agent-per-worktree discipline to OpenCode workers as well as Codex.
- WSL bootstrap installs OpenCode only when a self-hosted/API backend is selected or configured; workspace setup generates `opencode.json`; updates refresh routers without overwriting user model credentials.

## [0.1.1] - 2026-08-22

Patch release after validating the first versioned installer on an existing SGLang workspace.

### Fixed

- Legacy handoff templates (`TEMPLATE.md`, `TEMPLATE-review.md`, and other `TEMPLATE*.md` files) are never migrated into `.codex-artifacts/handoffs/`, never upgraded as runtime handoffs, and are ignored by the resolver if an old copy already exists.
- The updater removes accidental runtime `TEMPLATE*.md` copies left by older releases.
- `workflow-doctor.py` now queries Codex `hooks/list` through the local app-server when available, so it can report the effective current hook trust state (`Trusted`, `Modified`, `Untrusted`, or `Managed`) and detect a stale trusted hash.
- When runtime hook inspection is unavailable, the doctor explicitly labels the stored trust-entry check as unverified and directs the user to `/hooks`.

## [0.1.0] - 2026-08-22

First versioned release of the workflow kit.

### Added

- VS Code + WSL Codex extension-first workflow with CLI fallback profiles.
- Automatic handoff discovery through `SessionStart` and `UserPromptSubmit` hooks after explicit Codex trust approval.
- Topic- and freshness-aware handoff resolver with consumed/open lifecycle metadata and an active continuation pointer to prevent same-PR stale-handoff guessing.
- Writable `.codex-artifacts/` runtime state for handoffs, Goals, and reduced logs.
- Mandatory large-log reduction before raw reads for logs >= 1 MiB or >= 10,000 lines.
- Session lifecycle rules for new objectives, strategy reversals, and one active Codex session per Git worktree.
- Bounded component-by-component PR-review retrieval rules.
- Workflow doctor for Git-ignore, hook trust, handoff resolver, and installed-version diagnostics.
- Measured SGLang session token-efficiency table in the README.
- Two-level installed-version tracking for the global Codex hook bundle and each SGLang workspace, plus versioned ZIP/SHA-256 release packaging.

### Fixed

- `.codex-artifacts/` is explicitly added to the SGLang worktree `.git/info/exclude` and verified with `git check-ignore`; relative `git rev-parse --git-path` output is now resolved against the SGLang worktree instead of the kit directory.
- Reduced logs no longer attempt to write under a potentially read-only repo `.codex/` directory.
- Updater no longer silently assumes lifecycle hooks are trusted.
