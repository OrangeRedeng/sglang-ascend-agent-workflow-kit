# Updating an existing installation

Use this when the workflow kit was already installed into `~/code/sglang` and you downloaded a newer kit archive.

The update script changes only the workflow layer. It does **not** reset your SGLang branch, commit, working tree, Git remote, or project code.

## Recommended update

From the newly extracted kit directory inside WSL:

```bash
chmod +x wsl/*.sh repo/.codex/scripts/*
./wsl/06-update-existing-workspace.sh
```

Default target:

```text
~/code/sglang
```

For another worktree/path:

```bash
SGLANG=/path/to/sglang ./wsl/06-update-existing-workspace.sh
```

## What the updater changes

It:

1. backs up `~/.codex/hooks.json` and existing hook scripts;
2. installs the new `SessionStart` handoff-discovery hook and updated `UserPromptSubmit` guard;
3. migrates legacy mutable state:

```text
.codex/handoffs/ -> .codex-artifacts/handoffs/
.codex/goals/    -> .codex-artifacts/goals/
.codex/logs/     -> .codex-artifacts/logs/
```

4. adds metadata to legacy handoffs when needed;
5. updates `AGENTS.override.md`, `.codex/scripts/`, `.codex/templates/`, and repo-local skills;
6. adds `.codex-artifacts/` to `.git/info/exclude`;
7. runs the handoff resolver as a diagnostic.

Existing artifacts are preserved. The migration does not intentionally overwrite a newer artifact with an older legacy copy.

## After updating

Reload Codex so the hook configuration is reread:

```bash
cd ~/code/sglang
code .
```

Then in VS Code:

1. confirm `WSL: Ubuntu`;
2. reload/close the old Codex session;
3. start a **new local Codex session**.

You can verify discovery manually:

```bash
python3 .codex/scripts/resolve-handoff.py --json
```

If there is a matching open handoff, `selected` should contain its path.

## Handoff behavior after the update

Review session:

```text
Review PR #34855. Report only.
```

creates an open handoff when actionable findings exist.

New implementation session:

```text
Address the review findings.
```

should receive the handoff path automatically from the hook. You should no longer have to write:

```text
Address .codex-artifacts/handoffs/pr-34855-review.md
```

When implementation completes, Codex should mark the handoff consumed. Manual command:

```bash
python3 .codex/scripts/handoff-status.py consume \
  .codex-artifacts/handoffs/pr-34855-review.md
```
