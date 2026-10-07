# Versioning

The kit follows Semantic Versioning. `VERSION` is the release source of truth and must match the README current-release line and a `CHANGELOG.md` heading.

Installed markers:

```text
~/.config/sglang-workflow/workflow-kit-version
<sglang>/.agents/.workflow-kit-version
<sglang>/.codex/KIT_VERSION
```

Non-secret topology is stored in `install.env`; secrets remain in `models.env`.

External skill source commit pins are recorded in `skills.lock.json`; exact installed commits are recorded per workspace in `.agents/.skills-resolved.json`. Branch metadata exists only as an explicit update target.

Before release:

```bash
python3 scripts/kit-version.py verify
python3 scripts/validate_repo.py
./scripts/package-release.sh
```
