---
name: sglang-ci-report
description: Prepare or publish an SGLang PR CI failure report with current-head job evidence, explicit Yes/No PR attribution, and short reasons. Use for CI analysis comments and failed-check reports; source fixes and CI reruns require separate authorization.
---

# SGLang CI report

Produce a concise report a reviewer can act on. Inspect the current CI rather than copying conclusions from another PR or an older head.

## Scope and delivery

- A request to prepare a report means save a Markdown draft and return its path. Post when the user explicitly requests posting, including “prepare and post” or a follow-up “post it”; do not ask again for authorization already given.
- Report work does not authorize source/test edits, baseline or GT changes, commits, pushes, reruns, labels, or merging. Explain needed fixes without applying them.
- Use related chats, handoffs, and existing comments when available to recover prior decisions and report style. They are context, not proof of current CI results or authority for new actions. Do not claim access to unavailable chats.
- For several PRs, keep each head, tested base, jobs, and draft separate. Cross-reference matching failures only after checking their actual logs.

## Establish the CI snapshot

1. Read the live PR head, changed files, relevant diff, labels, and recent CI comments. Save the head SHA and collection time with the evidence under `.codex-artifacts/ci-<PR>/<snapshot>/`.
2. Enumerate checks and workflow runs for that head. Paginate every collection: checks, runs, jobs, and comments can exceed one page. Convenience wrappers may return only the first page.
3. Get the latest attempt's jobs for each failed or unfinished workflow. Keep recovered earlier attempts out of the current failed-job list. Record job IDs, URLs, status, conclusion, attempt, and failed step.
4. Confirm the checkout SHA in the relevant job logs. When CI tests a synthetic merge, identify its parents and compare against the **tested main parent**, which may differ from today's main or PR metadata. Distinguish any jobs that actually checked out an older head.
5. Keep queued, running, skipped, and cancelled outcomes explicit. A successful workflow with skipped tests does not prove those tests ran.

Prefer connected GitHub tools when sufficient. If unavailable or limited, use read-only `gh api`/`gh run view` or repository objects. With `gh api`, use pagination and `filter=latest` for jobs; use `--allow-escape-sequences` when decoded logs require it. Never print credentials or signed download URLs.

## Extract and attribute failures

- Download failed-job logs and inspect failed steps, final testcase summaries, and nearby tracebacks. For large logs, start with `.codex/scripts/extract-log-context.py <log>` when available; otherwise extract bounded error windows. Do not dump multi-megabyte logs into chat.
- Separate actual failures from injected errors in passing tests, expected failures, optional-dependency warnings, and recovered retries. A nested pytest session can intentionally fail inside a passing outer test. Report the final remaining failures, not every initial failure.
- Trace each root error through the changed code and its direct callers. Inspect the exact tested-base implementation or make a small isolated reproduction when attribution depends on it. Unchanged filenames alone do not establish independence: shared hooks, argument schemas, imports, dispatch, and fixtures can be affected indirectly.
- For a stale golden/checksum assertion, compare both base and head inputs with the pinned expectation. A changed file can expose an already-stale pin; the PR changing its hash is not sufficient proof that it introduced the failure.
- For timing/memory failures, record the metric, units, actual value, baseline/limit, testcase, and final attempt. Check whether changed hooks run inside the measured interval. Without a matched base/head run, do not claim runner noise or a proven performance regression.
- If a log is unavailable, try step summaries, annotations, or relevant artifacts. State the evidence gap; never invent an initiating testcase or call the check passed.

Use exactly **Yes** or **No** followed by a short reason in the `PR-related?` column:

| Situation | Attribution |
| --- | --- |
| The PR introduces the failing condition, including missing documentation/schema entries or outdated fixtures reached by a new read | **Yes** — name the changed dependency or invariant. |
| The exact-base check also fails, or inspected execution is independent of the change | **No** — give the base evidence or independent path. |
| Missing opt-in label, download/credential failure, runner admission/cleanup failure before tests run | **No** — identify the external blocker supported by the trace. |
| Finish, coverage, stage gate, fail-fast, or matrix cancellation caused by another failure | Inherit the identified root's Yes/No; say “downstream” and name the root. Do not count it as another defect. |

Do not use `Undetermined` as a substitute verdict. Where **No** only means no PR cause identified, say so and state the unresolved evidence, such as unavailable logs or a missing controlled A/B. Do not turn that limited judgment into “proven unrelated.” If the evidence cannot support an honest attribution, keep the report incomplete and identify what is missing rather than fabricate certainty to fill the table.

## Write the comment

Lead with the reviewed head, tested main parent, and checkout merge when applicable. State whether PR-caused failures were identified. Use this shape, replacing all example text with verified facts:

```markdown
CI review of head `HEAD`, against tested main `BASE`. Inspected jobs checked out merge `MERGE`.

There are PR-related CI failures. ...

| Job | Error | PR-related? |
| --- | --- | --- |
| [Job/shard](JOB_URL) | Final testcase and concrete error or metric. | **Yes** — short causal reason. |
| [Gate](GATE_URL) / [finish](FINISH_URL) | Missing opt-in label; tests did not run. | **No** — admission gate and downstream finish. |

Required fixes: ...

Lint/NPU results, actual execution coverage, unfinished jobs, and material evidence limits. ...
```

- Link **every current failed check**, grouping jobs only when the error and attribution match. Include relevant cancellations and distinguish them from test failures. Give different causes separate rows even within one job.
- Keep prose ordinary and short. Name testcases, shards, errors, and the minimum measurements needed to understand the blocker. Fold long traces only when they add useful evidence.
- For PR-related failures, list narrow next fixes. Passing NPU CI does not clear CPU/schema regressions or establish that an opt-in INT8/quantized path was exercised. Host/mock/static checks do not establish device correctness, quality, memory, graph behavior, HCCL stability, or performance.
- “No extracted failures” is not a pass. Empty recommendations mean coverage comparison is unavailable, not that coverage succeeded. For NPU analyzer reports, recommendations originate in `recommended_pytest_paths.txt` exported as `coverage_paths`; distinguish testcase outcomes from successful jobs and from pytest file counts.
- Do not reuse old GT failures after current GT consistency passes. Identify the pin/configuration behind any quality or timing claim; do not promote combined-branch measurements to an isolated PR A/B result.

## Validate and publish

1. Check every failed-check ID against the draft's job links. Verify each verdict has a reason, metric units match, recovered retries are excluded, and pending jobs are not counted as passes.
2. Refresh the PR head and checks before publication. If the head changed, reassess affected evidence; if statuses changed, update the draft. When nothing changed, do not redo the investigation.
3. If posting is authorized, publish the exact reviewed body through a structured GitHub comment tool or `gh pr comment <PR> --body-file <draft>`. Preserve literal newlines and backticks. Exclude private chat transcripts, local memory citations, secrets, and unrelated material.
4. Read the posted comment back and compare its body with the draft. If a write times out, check whether it succeeded before retrying to avoid duplicates. Update an existing comment only when that is the requested delivery.
5. Return the verified comment link and the main blocker, or the local draft link when publication was not requested. Stop after the report is delivered; further fixes are a separate objective.
