# Changelog

## [0.6.0] - 2026-10-08

### Changed
- Made GitHub Copilot Chat the primary daily UI for both OpenAI Codex and BigModel GLM.
- Added `grikomsn.openai-oauth-copilot-chat` (Codex Bridge) so ChatGPT/Codex models, reasoning controls, tool calls and quota are available from the same model picker as GLM.
- Replaced `workflow-glm-copilot` with a single `workflow-copilot` configure/status/doctor/guide command.
- Kept `OpenAI.chatgpt` and the user-local Codex CLI only as a fallback for native Codex runtime/hooks.
- Added VS Code version validation (GLM provider requires 1.127+; Codex Bridge requires 1.125+).

### Preserved
- Root `AGENTS.md`, canonical `.agents/skills/`, handoffs, Goals, bounded review/log tooling, pinned Ascend/CANNBot sources and non-destructive Codex configuration.
- BigModel China Coding Plan remains isolated from PAYG via the dedicated GLM Copilot provider.

### Migration
- Removes the obsolete `workflow-glm-copilot` command and installs Codex Bridge. Credentials are not migrated or read; ChatGPT OAuth and GLM API key stay in VS Code SecretStorage/UI.

## [0.5.0] - 2026-10-08

### Changed
- Replaced the Kilo multi-provider layer with two separate native VS Code surfaces: official OpenAI Codex and GitHub Copilot Chat with the dedicated GLM provider.
- Added automatic installation/configuration of `yijiazhen-qi.glm-for-github-copilot-chat` in BigModel China Coding Plan mode with quota status and GLM reasoning controls.
- Made root `AGENTS.md` and `.agents/skills/` the single shared project layer for Codex and Copilot.
- Canonicalized external skill links so directory names match `SKILL.md` names, as required by portable Agent Skills.
- Standardized Standard install on core Ascend + selected CANNBot skills; Full adds KernelHive, BBuf, and `sgl-kernel-npu`.

### Removed
- Kilo Code extension/runtime/configuration.
- OpenCode and external `local/cheap/strong` routing.
- Semble and Serena workflow integration.
- Codex-native GLM profiles, custom provider catalog, GLM aliases, and provider-token helper.
- Duplicate harness-specific instructions and Kilo agents/commands.
- Generated PRINT_RULES PDF/source from the runtime kit.

### Migration
- The updater uninstalls the kit-managed Kilo extension/CLI, deletes Kilo workspace files, strips legacy kit-managed Codex config blocks, removes old GLM profile files/commands, and rewrites the install manifest to the minimal v0.5 schema.

## [0.4.2] - 2026-10-07

### Added

- `workflow-skills dedupe --workspace <path>` self-heals duplicate skill aliases left by older workflow-kit versions. It removes only redundant symlinks and never deletes real skill directories.
- `workflow-setup` runs shared-skill hygiene automatically before the doctor suite, so normal update/setup converges without manual cleanup.

### Changed

- Workspace setup now deduplicates skills before generating `.skills-resolved.json` / `.skills-index.json`.
- When one real/native skill and one or more symlink aliases share the same frontmatter `name`, the real skill wins. When duplicate symlinks resolve to the same source, the current managed alias wins.

### Fixed

- Upgrades that retained legacy `ascend-*`, `bbuf-*`, or `upstream-*` aliases no longer fail Kilo `doctor-deep` solely because the same skill is exposed twice.
- Ambiguous duplicate names that come from different real sources are still reported as conflicts instead of being silently removed.

## [0.4.1] - 2026-10-07

### Added

- `workflow-kilo configure --with-glm` one-command setup for safe Kilo project permissions, BigModel China Coding Plan, Codex-to-Kilo MCP synchronization, extension installation and automatic deep verification.
- `workflow-kilo doctor-deep` checks WSL/VS Code context, Kilo config, all shared skill metadata, agents, commands, provider/key safety, MCP parity, git exclusions, version markers and workflow helpers; it also uses live Kilo CLI probes when available.
- Automatic trusted global Kilo provider `bigmodel-coding-cn` with `glm-5.3` / `glm-5.3-flash`, 1M context metadata and `low`/`high`/`max` reasoning variants.
- `/workflow-self-check` Kilo slash workflow for in-UI verification without modifying source.
- `workflow-kilo sync-mcp` translation for portable Codex local/remote MCP definitions.
- `workflow-setup` unified post-install command: repairs Codex when needed, installs the Kilo CLI diagnostics companion, configures Kilo/GLM/MCP, runs the complete doctor suite and opens the WSL workspace in VS Code.
- Interactive Standard/Full updates automatically invoke `workflow-setup`; use `--no-post-setup` or `WORKFLOW_SKIP_POST_SETUP=1` to opt out.

### Changed

- BigModel Coding Plan keys can now be stored automatically in `~/.config/sglang-workflow/bigmodel-coding.key` with mode `0600`; trusted global Kilo config references the private file and the repository never contains the secret.
- Synced MCP servers are disabled by default and can be toggled with `/mcps`, avoiding unnecessary MCP tool/instruction context in ordinary sessions.
- Kilo project defaults auto-allow read/glob/grep/skill/LSP/todo operations while keeping edits, shell, subagents, external directories and web access approval-gated.
- `workflow-kilo configure` runs its deep doctor automatically unless `--no-doctor` is explicitly requested; `workflow-setup doctor` provides the one-command all-harness verification path.
- The optional Kilo CLI is installed into the same user-owned `~/.local/npm` prefix so live MCP/model probes can run without `sudo`.
- Workspace updates no longer overwrite an existing `kilo.jsonc`, preserving user/provider/MCP settings across kit upgrades.

### Fixed

- Kilo setup is now verifiable from the shell rather than relying only on manual UI inspection.
- Release/update guidance now distinguishes automatable configuration from the one unavoidable manual ChatGPT OAuth authorization and the final provider quota checks.

## [0.4.0] - 2026-10-07

### Added

- Kilo Code companion VS Code frontend for unified ChatGPT/Codex + GLM model selection while keeping official Codex as the native OpenAI harness.
- Shared Kilo agents (`sglang-code`, `sglang-review`, `sglang-npu-perf`, `sglang-ask`) with bounded `steps` budgets and no pinned model.
- Kilo slash workflows for bounded review, session checkpointing, and structured performance Goals.
- `workflow-kilo` extension/status/doctor/setup-guide helper.
- `workflow-codex` WSL path diagnostics and user-local repair under `~/.local/npm`.
- `docs/KILO.md` with ChatGPT subscription, BigModel China Coding Plan, model/reasoning switching, quota, and migration guidance.

### Changed

- Standard and Full installs now include Kilo as a companion UI; `--without-kilo` opts out. OpenCode is demoted to optional/legacy external worker tiers.
- Codex CLI bootstrap no longer performs or requires a root-global npm update. Missing/Windows/broken Codex is repaired in a user-owned WSL prefix, and a failed CLI repair does not abort shared workflow/extension installation.
- `.agents/skills/`, handoffs, Goals, reducer/review artifacts and experiment ledgers are explicitly harness-neutral and shared between Codex and Kilo.
- Version markers for config, Codex, workspace and Kilo are written only after the complete selected install succeeds.

### Safety

- Kilo provider credentials are never written by the workflow kit.
- BigModel China Coding Plan documentation distinguishes the coding endpoint from the general PAYG/resource endpoint and requires a one-request quota verification before sustained use.

## [0.3.2] - 2026-10-07

### Fixed

- Legacy `0.1.1 -> 0.3.x` migration no longer advances `~/.codex/workflow-kit-version` before the workspace layer succeeds. All success markers are now written only after the complete setup finishes.
- Corrected the pinned `Ascend/agent-skills` manifest: removed the stale `ascendc-operator-frame-adapter-torch` entry that is documented upstream but absent from commit `155ac37bd169ddb89479af528297cfb2237400aa`.
- External skill validation now distinguishes required core skills from optional selected skills, preventing optional upstream drift from aborting a Standard migration while still failing on missing required skills.
- The optional AscendC bundle now links current pinned skills for project initialization, code generation, precision debugging/evaluation, performance evaluation/optimization, and code review.
- Re-running the updater after a partially failed `0.3.1` migration is supported and converges the global/config/workspace version markers to `0.3.2`.

## [0.3.1] - 2026-10-07

Evidence-driven retrieval/session optimization release based on 127 recorded Codex sessions.

### Added

- Codex `PostToolUse` retrieval-budget governor keyed by `session_id`, with measured soft/checkpoint thresholds and first-repeat warnings for unchanged handoff/skill reads.
- `workflow-review-packet.py` for one bounded changed-file/component/diff packet before broad PR review.
- `extract-log-context.py` v2 with normalized error-signature clustering, 32 KiB/400-line default cap and targeted `--expand` mode.
- `workflow-handoffs gc` plus `archived` handoff lifecycle state.
- `workflow-exp` structured `results.jsonl` ledger for performance Goals.
- Generated `.agents/.skills-index.json` and stricter external-skill pin status.
- `workflow-doctor --online` optional GLM Responses API smoke test.
- Direct migration path for legacy v0.1.x installs without `install.env`.
- Non-destructive Codex config/hook merge helpers.

### Changed

- `~/.codex/config.toml` is never replaced on update. Model/reasoning settings, project trust, hook trust state, memories and unrelated MCP configuration are preserved.
- `hooks.json` is merged: unrelated user hooks remain and unchanged kit hook definitions keep stable identities; only the new budget hook requires new trust review.
- Standard installation no longer installs Semble. Semble and Serena are optional/Full because the measured session corpus contained no actual calls.
- External skill sources are checked out at immutable commit pins rather than floating `main`/`master` refs. `workflow-skills update` requires explicit `--only SOURCE`.
- Performance Goals create `.active` and `results.jsonl` and encourage session rotation between experiment rounds.
- PR review guidance now prefers a deterministic first-pass packet over many repeated retrieval calls.

### Fixed

- Removed destructive copying of the kit's default Codex config over an existing user configuration.
- Removed destructive replacement of unrelated user hook definitions.
- Fixed external-skill installation reproducibility and pin drift reporting.

## [0.3.0] - 2026-10-06

Codex-native multi-provider and Ascend kernel engineering release: GLM Coding Plan profiles, CANNBot/KernelHive skill sources, harness/provider split and kernel/performance orchestration skills.

## [0.2.0] - 2026-08-22

Provider-neutral installer, multi-model router, installation levels, external OpenAI-compatible workers, extended Ascend skills, version tracking and update workflow.

## [0.1.1] - 2026-08-22

Handoff migration/trust diagnostics fixes.

## [0.1.0] - 2026-08-22

Initial versioned Codex + SGLang + Ascend workflow kit.
