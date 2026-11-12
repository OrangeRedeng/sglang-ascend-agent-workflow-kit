# Skills

`.agents/skills/` is the only project skill directory managed by this kit.

Current VS Code/Copilot agent tooling and Codex both support this location. To remain portable, every skill must satisfy:

```text
.agents/skills/<name>/SKILL.md
frontmatter: name: <name>
```

v0.5 removes prefixed aliases such as `upstream-*`, `official-*`, `ascend-*`, `bbuf-*`, `cannbot-*`, and `kernelhive-*`. External skills are linked under their canonical skill name; a real/native local skill takes precedence over a symlink.

Pinned sources are defined in `skills.lock.json`.

For PR CI reports, use `sglang-ci-report` to inspect current job evidence and prepare the `Job / Error / PR-related?` table. It drafts by default and publishes when requested. Example: “Use $sglang-ci-report to prepare and post a CI report for PR #42224.”

Useful commands:

```bash
workflow-skills status
workflow-skills doctor
workflow-skills dedupe --workspace ~/code/sglang
workflow-skills update --only <source>
```

Standard installs core Ascend sources plus selected CANNBot kernel skills. Full adds KernelHive and selected BBuf skills.
