---
name: ascend-log-analysis
description: Triage large SGLang CI and Ascend/NPU logs without dumping the full log into model context.
---
# Large SGLang / Ascend log analysis

For a local/downloaded log at least 1 MiB or 10,000 lines (or clearly large/repetitive), reduction is mandatory before raw-log reading.

1. Check file size/line count without reading the body.
2. Preserve the original log; never rewrite it.
3. **Do not read the full raw log first.** Run `.codex/scripts/extract-log-context.py <log-file>`.
4. Read the focused artifact printed by the reducer (normally `.codex/logs/<name>.focused.txt`).
5. Extract: first failure/traceback, HCCL/ACL/AICore errors, shapes/dtypes, timeout/hang signals, relevant latency/throughput/memory lines and nearby context.
6. Correlate timestamps only around the failure window before reading broader ranges.
7. Read a narrow raw-log range only when a concrete missing fact requires it.
8. Separate symptom from root cause; do not patch code from the first error line alone.

The user does not need to say "use the reducer". This skill and `AGENTS.override.md` define it as the default large-log workflow.
