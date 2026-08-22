# Version tracking

The workflow kit uses Semantic Versioning and keeps one source-of-truth release number in the repository root:

```text
VERSION
```

Release history is recorded in [`CHANGELOG.md`](../CHANGELOG.md).

## Installed versions

The kit has two layers, so it tracks two installed version markers:

```text
~/.codex/workflow-kit-version       global Codex hook bundle
~/code/sglang/.codex/KIT_VERSION    repo-local workflow/scripts/skills layer
```

Normally both should contain the same version. Check them with:

```bash
cat ~/.codex/workflow-kit-version
cat ~/code/sglang/.codex/KIT_VERSION
```

Or from the SGLang worktree:

```bash
python3 .codex/scripts/workflow-doctor.py
```

The doctor reports `OK` when the global and workspace versions match, and warns when a layer is missing or out of sync.

## Updating

`wsl/06-update-existing-workspace.sh` reads the incoming kit `VERSION` before making changes and prints:

```text
Global Codex layer: 0.1.0
Workspace layer:    0.1.0
Incoming kit:       0.2.0
```

After a successful update it writes both installed markers and appends an audit row to:

```text
.codex-artifacts/kit-version-history.tsv
```

The history contains UTC timestamp, action, previous workspace version, and new version. Runtime history stays local because `.codex-artifacts/` is Git-ignored.

The updater refuses a downgrade when either installed layer is newer than the incoming kit. An intentional downgrade requires:

```bash
ALLOW_DOWNGRADE=1 ./wsl/06-update-existing-workspace.sh
```

Reapplying the same version is allowed and remains useful for repairing configuration drift.

## Release policy

Use:

- **PATCH** for compatible bug fixes, rule clarifications, and installer fixes;
- **MINOR** for new workflow mechanisms, skills, hooks, or artifact formats that remain backward-compatible;
- **MAJOR** for incompatible install/layout/configuration changes requiring manual migration.

Before publishing a release:

```bash
python3 scripts/kit-version.py verify
python3 scripts/validate_repo.py
```

Then create a Git tag matching `VERSION`, for example:

```bash
git tag -a v0.2.0 -m "v0.2.0"
git push origin v0.2.0
```

CI rejects a `vX.Y.Z` tag when it does not match the repository `VERSION`.

## Build a versioned archive

Create the distributable ZIP and SHA-256 sidecar from `VERSION`:

```bash
./scripts/package-release.sh
```

Output:

```text
dist/codex-sglang-workflow-kit-vX.Y.Z.zip
dist/codex-sglang-workflow-kit-vX.Y.Z.zip.sha256
```

The packaging script runs version/repository validation first and excludes Git metadata, caches, temporary files, prior ZIPs, and `dist/` itself.
