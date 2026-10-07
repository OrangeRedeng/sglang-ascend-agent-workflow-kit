# External skills

`skills.lock.json` is the release lock for external skill repositories. v0.3.1 uses immutable commit pins rather than floating branches. Branch names are retained only as explicit update targets.

Each source records URL, branch, commit pin, local directory, tier, license note and the selected skill names expected to exist at that pin.

## Commands

```bash
workflow-skills status
workflow-skills install
workflow-skills snapshot
workflow-skills index
workflow-skills update --only cannbot-skills
```

`install` checks out the locked commit in detached HEAD state and refuses to change a dirty source checkout. `status` compares current HEAD to the lock. `snapshot` writes `.agents/.skills-resolved.json`; `index` writes `.agents/.skills-index.json` with compact source/path/title/description metadata.

`update` requires at least one `--only SOURCE`. It advances that source to the configured branch head and rewrites only the private installed lock (`~/.config/sglang-workflow/skills.lock.json`). A kit release remains reproducible until its repository lock is deliberately changed.

## Sources

Core:

- `awesome-ascend-skills`
- `Ascend/agent-skills`

Optional/full:

- CANNBot Skills: AscendC/CANN architecture, environment, tiling, API, debug, review, profiling and direct-invoke workflows.
- KernelHive `ascendc-skill`: generator/migration/docs helpers. `ascend-kernel-optimization` is deliberately not auto-linked because upstream currently assumes environment-specific evaluator/output/LLM settings.
- BBuf AI-Infra skills: selected SGLang review/history/profiling/incident workflows.

Load leaf skills selectively. The measured session corpus showed repeated `SKILL.md` reads as non-trivial retrieval overhead, so the PostToolUse governor warns on an unchanged duplicate read and `.skills-index.json` should be used for discovery before opening full skill bodies.
