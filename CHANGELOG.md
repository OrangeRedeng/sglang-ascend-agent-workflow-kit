# Changelog

All notable workflow-kit changes are recorded here. The project follows Semantic Versioning (`MAJOR.MINOR.PATCH`).

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
