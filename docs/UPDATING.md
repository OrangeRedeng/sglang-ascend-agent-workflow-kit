# Updating

Normal update:

```bash
chmod +x wsl/*.sh scripts/*.sh scripts/*.py repo/.codex/scripts/*
./wsl/06-update-existing-workspace.sh
```

or:

```bash
./setup.sh --update
```

## Legacy v0.1.x migration

v0.1.x predates `~/.config/sglang-workflow/install.env`. `wsl/06-update-existing-workspace.sh` detects a recognizable legacy installation and creates a conservative manifest from observable state (Codex, Semble, BBuf/kernel source directories, Serena), then replays the update.

The migration preserves `.codex-artifacts/`, `models.env`, existing `~/.codex/config.toml`, unrelated hooks and user-owned settings.

## Codex config safety

The updater never copies the repository `codex/config/config.toml` over an existing user file. Kit-managed optional config is merged. The hook merger removes/replaces only hook groups whose command points at kit-owned hook scripts and preserves unrelated hook groups.

Because the new `PostToolUse` hook has a new definition, use `/hooks` after updating and approve it if Codex reports it as untrusted. Existing unchanged SessionStart/UserPromptSubmit entries should remain structurally stable.

## Skill updates

Normal kit updates reinstall the pinned release revisions. They do not silently advance third-party repositories.

```bash
workflow-skills status
workflow-skills update --only awesome-ascend-skills
```

`update --only` intentionally advances the private installed lock and leaves release metadata in this repository unchanged.
