---
name: ascend-log-analysis
description: Triage large SGLang/Ascend logs without dumping the full log into model context.
---
# Ascend log analysis

1. Preserve original log as artifact; never rewrite it.
2. Run `.codex/scripts/extract-log-context.py` first.
3. Extract: first failure/traceback, HCCL/ACL/AICore errors, shapes/dtypes, timeout/hang signals, relevant latency/throughput/memory lines and ±context.
4. Correlate timestamps only around the failure window before reading broader ranges.
5. Ask for the full log only when a concrete missing fact requires it.
6. Separate symptom from root cause; do not patch code from the first error line alone.
