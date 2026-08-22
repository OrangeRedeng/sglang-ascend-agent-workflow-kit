# Updating an existing installation

The updater now reuses the saved installation topology. It does not assume Codex is installed or primary.

## Recommended update

Extract the new release and run inside WSL:

```bash
chmod +x setup.sh wsl/*.sh bin/* repo/.codex/scripts/*
./wsl/06-update-existing-workspace.sh
```

The update wrapper calls:

```bash
./setup.sh --update
```

## Saved topology

New installations store non-secret deployment state in:

```text
~/.config/sglang-workflow/install.env
```

The updater reuses:

- installation level;
- workspace path;
- selected primary backend;
- routing mode;
- installed component flags.

It does **not** store or reconstruct API keys there.

Model credentials/endpoints remain in:

```text
~/.config/sglang-workflow/models.env
```

That file is preserved.

## Upgrading from a pre-manifest release

If `install.env` does not exist, `setup.sh --update` stops instead of guessing whether Codex or another backend should be installed. Establish the topology once with:

```bash
./setup.sh
```

or an explicit non-interactive deployment. Subsequent updates replay that saved manifest without changing `models.env`. This is intentional: upgrading an older Codex-only installation must not silently make Codex the primary backend if you want a different architecture.

## Version and downgrade protection

Universal global marker:

```text
~/.config/sglang-workflow/workflow-kit-version
```

Workspace skill marker:

```text
~/code/sglang/.agents/.workflow-kit-version
```

Full/core workflow installations also keep the compatibility marker:

```text
~/code/sglang/.codex/KIT_VERSION
```

Codex installations additionally keep:

```text
~/.codex/workflow-kit-version
```

Accidental downgrades are rejected. For an intentional downgrade only:

```bash
ALLOW_DOWNGRADE=1 ./wsl/06-update-existing-workspace.sh
```

## What is preserved

The update does not reset the SGLang branch, commit, remotes, worktree, or project code. Existing `.codex-artifacts/` state and `models.env` are preserved. Legacy mutable `.codex/{handoffs,goals,logs}` state is migrated by the workspace helper when applicable.

## After an update

Always inspect routing without calling a model:

```bash
ai-task --dry-run review 34855
```

If Codex hooks changed and Codex is installed, approve the new/current hook hashes again:

```text
cx
/hooks
```

Then restart the Codex/VS Code session.

For a non-Codex primary backend, no Codex hook action is required.

## Change installation level or primary backend

An update preserves topology. To intentionally change it, rerun:

```bash
./setup.sh
```

or only change model routing with:

```bash
workflow-configure
```
