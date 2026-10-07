# Contributing

Contributions should keep the kit small, reproducible, and easy to audit.

## Principles

- Prefer one clear workflow over several overlapping alternatives.
- Do not add a new MCP/RAG tool without a concrete use case and routing rule.
- Keep third-party skills external; link or clone them rather than vendoring unless there is a compelling reason.
- Keep the default setup usable without an Ascend device; NPU runtime validation belongs on the real target host, CI job, or container.
- Preserve user-owned existing config where practical; bootstrap scripts should back up or merge rather than silently destroy unrelated settings.
- Keep Codex/OpenAI as the default daily UI; custom providers must not silently replace the user's native OpenAI provider.

## Documentation

User-facing docs are intentionally limited to the files already present under `docs/`, plus `README.md` and `PRINT_RULES.pdf`.

## Validation before a pull request

From the repository root:

```bash
bash -n setup.sh wsl/*.sh bin/cx-task bin/local-task bin/cheap-task bin/strong-task repo/.codex/scripts/*.sh
python3 -m py_compile bin/ai-task bin/workflow-configure codex/hooks/*.py repo/.codex/scripts/*.py scripts/*.py
python3 scripts/validate_repo.py
```

PowerShell scripts should also parse successfully on Windows/PowerShell. GitHub Actions performs the same checks on Linux and Windows.

If `PRINT_RULES.pdf` changes, update `docs/source/PRINT_RULES.md`, rebuild it with `python3 scripts/build_print_rules.py`, then render and visually verify that it remains one page with no clipped or overlapping content.

## Third-party updates

When changing selected skill names or repositories, verify that the referenced `SKILL.md` paths still exist upstream. Keep `skills.lock.json` synchronized with the source URL, revision policy, and selected skills.

## Versioning and releases

`VERSION` is the release source of truth and uses Semantic Versioning. Every release must also have a matching `CHANGELOG.md` heading and README current-release line.

Before creating a release tag/archive:

```bash
python3 scripts/kit-version.py verify
python3 scripts/validate_repo.py
./scripts/package-release.sh
```

Tag names use `vX.Y.Z` and must match `VERSION`.
