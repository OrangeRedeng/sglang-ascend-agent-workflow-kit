# Troubleshooting

## My Codex config changed after update

v0.3.1 should not replace `~/.codex/config.toml`. Check for a pre-v0.3.1 backup created by an older installer (`config.toml.bak-*`) only if you previously installed v0.3.0. Current updates use `scripts/merge-codex-config.py` and preserve unrelated sections.

## Hooks show Untrusted / Modified

This is expected after installing a new hook definition. Start Codex and run `/hooks`, then review/approve the kit entries. `workflow-doctor.py` reports presence but never changes trust.

## Session-budget warnings are too early/late

Override thresholds for an experiment host/session:

```bash
export SGLANG_WORKFLOW_TOOL_SOFT_LIMIT=36
export SGLANG_WORKFLOW_TOOL_CHECKPOINT_LIMIT=52
```

Do not disable the governor merely to continue broad retrieval. For long Goals, checkpoint artifacts and rotate agent sessions.

## Focused log is still too large

v0.3.1 defaults to ~32 KiB / 400 lines. If one error needs more context, use:

```bash
.codex/scripts/extract-log-context.py run.log --expand <signature-id>
```

Do not increase the global cap first.

## Skill source reports DRIFT

```bash
workflow-skills status
```

If the checkout is dirty, the manager refuses to move it. Commit/stash/remove local changes intentionally. To restore the release pin, rerun setup/`workflow-skills install --only SOURCE`. To intentionally advance, use `workflow-skills update --only SOURCE`.

## Legacy v0.1.x says no install manifest

Use `./wsl/06-update-existing-workspace.sh`; v0.3.1 can create a conservative migration manifest from the legacy installation.

## GLM diagnostics

```bash
python3 .codex/scripts/workflow-doctor.py
python3 .codex/scripts/workflow-doctor.py --online
```

The online mode sends only a tiny smoke prompt and never prints the API key or response body on HTTP failure.
