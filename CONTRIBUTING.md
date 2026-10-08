# Contributing

Keep the kit narrow: one Copilot Chat UI (Codex Bridge + GLM) + official Codex fallback + shared workflow + Ascend skills. Do not add another general-purpose agent harness without measured evidence that the existing split cannot solve the problem.

Before submitting changes:

```bash
bash -n setup.sh wsl/*.sh repo/.codex/scripts/*.sh scripts/package-release.sh
python3 -m py_compile bin/workflow-codex bin/workflow-copilot bin/workflow-skills bin/workflow-exp bin/workflow-setup codex/hooks/*.py repo/.codex/scripts/*.py scripts/*.py
python3 scripts/validate_repo.py
```

Do not add secrets, auth files, raw session dumps, or multi-megabyte logs to the repository.
