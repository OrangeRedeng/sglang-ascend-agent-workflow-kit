# Version tracking

The workflow kit uses Semantic Versioning. The release source of truth is:

```text
VERSION
```

Release history is recorded in [`CHANGELOG.md`](../CHANGELOG.md).

## Provider-neutral installed markers

Global workflow version:

```text
~/.config/sglang-workflow/workflow-kit-version
```

Workspace skill-layer version:

```text
<sglang>/.agents/.workflow-kit-version
```

Core/full workflow installations also retain the historical compatibility marker:

```text
<sglang>/.codex/KIT_VERSION
```

When Codex is installed, its global bundle also keeps:

```text
~/.codex/workflow-kit-version
```

Codex-specific markers are no longer required for a non-Codex or Light installation.

## Installation manifest

Topology is stored in:

```text
~/.config/sglang-workflow/install.env
```

This records installation level, workspace, primary backend, routing mode, and component flags. It never contains API keys.

Model endpoint credentials are stored separately in:

```text
~/.config/sglang-workflow/models.env
```

## Updating

`wsl/06-update-existing-workspace.sh` delegates to `setup.sh --update`. The setup entrypoint reads the saved manifest and redeploys the same topology.

Core/full workflow updates append local audit history to:

```text
.codex-artifacts/kit-version-history.tsv
```

The updater refuses an accidental downgrade. For an intentional downgrade only:

```bash
ALLOW_DOWNGRADE=1 ./wsl/06-update-existing-workspace.sh
```

Reapplying the same version is allowed.

## Release policy

Use:

- **PATCH** for compatible bug fixes and documentation/installer corrections;
- **MINOR** for backward-compatible workflow, router, installation-level, or artifact features;
- **MAJOR** for incompatible layout/configuration changes requiring manual migration.

Validate before publishing:

```bash
python3 scripts/kit-version.py verify
python3 scripts/validate_repo.py
```

Create a matching tag, for example:

```bash
git tag -a v0.2.0 -m "v0.2.0"
git push origin v0.2.0
```

CI rejects a `vX.Y.Z` tag that does not match `VERSION`.

## Build archive

```bash
./scripts/package-release.sh
```

Output:

```text
dist/codex-sglang-workflow-kit-vX.Y.Z.zip
dist/codex-sglang-workflow-kit-vX.Y.Z.zip.sha256
```
