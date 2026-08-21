# Working style

- Answer briefly and directly. No introductions or restatement of the request.
- Keep code comments concise; comment WHY, not WHAT.
- Make the smallest change that solves the current task.
- Do not broaden scope or perform unrelated cleanup/refactoring.
- Stop after the requested objective and minimal validation are complete.

# Session boundaries

- Treat a new objective as a new session unless this is one evidence-driven long-running Goal.
- Same goal + same strategy may continue; same goal + materially different implementation strategy starts a new session.
- Do not turn a PR into one permanent conversation: review, implementation, conflicts, comments, CI, and description are separate objectives.
- Use one active Codex session per Git worktree. Parallel Codex work should use separate `git worktree` directories.
- Use `/side` for a focused detour and `/compact` only when continuing the same objective.

# Git

- Do not commit or push unless the current prompt explicitly requests it.
- Pure `git push`, `git status`, `git switch`, or `git fetch` operations belong in the user's terminal when no reasoning is required.

# Tests

- Do not create or modify tests by default.
- Add/modify a test only when the user explicitly requests it, review/CI explicitly requires it, or a regression test is necessary to demonstrate a real bug fix.
- Never add tautological or mirror tests.

# Repository exploration

- Start from known files, symbols, changed files, commits, errors, PR context, or failing CI.
- Exact identifier/path/string -> targeted `rg`.
- Known commit/change -> `git show`, `git diff`, bounded `git log`/`blame`.
- Unknown conceptual location -> semantic search if available.
- Callers/references -> symbol tooling if available.
- Do not read a full large file when a relevant function/class/range is sufficient.
- For huge logs, extract errors/metrics and nearby context before reading the entire log.

# Subagents

- Do not use parallel subagents by default.
- Use them only for independent investigations where isolation/latency materially helps; they are not a token-saving mechanism.
