# Contributing

Contributions should keep the kit small, reproducible, and easy to audit.

## Principles

- Prefer one clear workflow over several overlapping alternatives.
- Do not add a new MCP/RAG tool without a concrete use case and routing rule.
- Keep third-party skills external; link or clone them rather than vendoring unless there is a compelling reason.
- Keep the default setup usable without an Ascend device; NPU runtime validation belongs on the real target host, CI job, or container.
- Preserve user-owned existing config where practical; bootstrap scripts should back up or merge rather than silently destroy unrelated settings.

## Documentation

User-facing docs are intentionally limited to:

- `README.md` - landing page and quick start;
- `docs/INSTALLATION.md`;
- `docs/WORKFLOW.md`;
- `docs/TOOLING.md`;
- `docs/ASCEND.md`;
- `docs/TROUBLESHOOTING.md`;
- `PRINT_RULES.pdf` - one-page printable reference.
- `docs/AUTOMATION.md` - automation/enforcement contracts for logs, handoffs, and routing;
- `docs/UPDATING.md` - update an existing installation;
- `docs/VERSIONING.md` - release and installed-version policy.

Do not create another README-like file unless its topic does not fit an existing document.

## Validation before a pull request

From the repository root:

```bash
bash -n wsl/*.sh bin/cx-task repo/.codex/scripts/*.sh
python3 -m py_compile codex/hooks/*.py repo/.codex/scripts/*.py
python3 scripts/validate_repo.py
```

PowerShell scripts should also parse successfully on Windows/PowerShell. GitHub Actions performs the same checks on Linux and Windows.

If `PRINT_RULES.pdf` changes, update `docs/source/PRINT_RULES.md`, rebuild it with `python3 scripts/build_print_rules.py`, then render and visually verify that it remains one page with no clipped or overlapping content.

## Third-party updates

When changing selected skill names or repositories, verify that the referenced `SKILL.md` paths still exist upstream. Do not assume a historical skill path is still current.

## Versioning and releases

`VERSION` is the release source of truth and uses Semantic Versioning. Every release must also have a matching `CHANGELOG.md` heading and README current-release line.

Before creating a release tag/archive:

```bash
python3 scripts/kit-version.py verify
python3 scripts/validate_repo.py
./scripts/package-release.sh
```

Tag names use `vX.Y.Z` and must match `VERSION`; CI checks this on tag pushes. Installed copies are tracked separately by the global `~/.codex/workflow-kit-version` marker and the workspace `.codex/KIT_VERSION` marker.
