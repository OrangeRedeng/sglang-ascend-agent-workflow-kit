# Changelog

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
