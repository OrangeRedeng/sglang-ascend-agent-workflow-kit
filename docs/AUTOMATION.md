# Automation and enforcement

## Lifecycle hooks

The kit uses three Codex lifecycle hooks after user trust approval:

- `SessionStart`: resolve a fresh/task-compatible handoff.
- `UserPromptSubmit`: enforce prompt/session rules and reject high-cost trivial agent work.
- `PostToolUse`: track a tiny per-session retrieval budget.

Current Codex hook inputs include `session_id`, `turn_id`, `tool_name`, `tool_input` and `tool_response`; the governor keys state by `session_id` under `.codex-artifacts/session-budget/`.

The governor does not undo or block a completed tool call. It injects concise model-visible guidance only when:

- the session reaches the measured soft/checkpoint tool-call thresholds;
- an unchanged handoff or `SKILL.md` is read again;
- a giant high-context `git diff` is attempted;
- a direct raw `.log` read looks likely to bypass the large-log contract.

Default thresholds are 32 and 44 calls and can be overridden with `SGLANG_WORKFLOW_TOOL_SOFT_LIMIT` and `SGLANG_WORKFLOW_TOOL_CHECKPOINT_LIMIT`.

## PR review packet

Broad PR reviews should begin with one bounded packet:

```bash
python3 .codex/scripts/workflow-review-packet.py --pr <N>
```

or a local comparison:

```bash
python3 .codex/scripts/workflow-review-packet.py --base origin/main
```

The output lives under `.codex-artifacts/reviews/` and has a hard byte cap.

## Large logs

Logs >=1 MiB or >=10,000 lines must be reduced with `.codex/scripts/extract-log-context.py` before raw reading. v2 clusters repetitive signatures and caps first-stage output. Use `--expand <signature-id>` for a targeted second stage rather than globally increasing context.

## Handoff discovery and GC

Handoff discovery remains automatic by hook. `workflow-handoffs gc --older-than-hours 48` archives stale open handoffs and clears matching active pointers without deleting history.

## Provider routing

`ai-task` is deterministic from config/task kind. Provider fallback is availability routing, not semantic verification. OpenAI-vs-GLM quality routing should be changed only after matched eval evidence exists.
