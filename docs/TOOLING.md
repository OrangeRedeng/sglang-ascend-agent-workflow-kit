# Tooling and search routing

The tools in this kit solve different retrieval problems. They should not all run for every question. For which behaviors are automatic versus manual, see [Automation and enforcement](AUTOMATION.md).

## VS Code extension and tooling

The extension-first workflow uses the same WSL-side repository tooling layer:

```text
~/.codex/config.toml        -> model defaults + Semble MCP
AGENTS.override.md          -> search/log/handoff/session rules
.agents/skills/             -> task-specific workflows
.codex/                     -> static scripts and templates
.codex-artifacts/           -> writable handoffs, goals and focused logs
```

Open the repository with `cd ~/code/sglang && code .` and start a new Codex local session in the sidebar. You do not need to run `cx` at the same time. `cx` is an independent CLI session. See [VS Code + Codex](VSCODE.md).


## Search ladder

```text
Exact identifier/path/error
  -> rg / direct navigation

Known commit or PR
  -> git show / git diff / bounded git history

Model-specific historical question
  -> model-pr-history-knowledge

Unknown conceptual implementation location
  -> Semble

Known symbol, need callers/references/implementations
  -> Serena (optional)
```

Once semantic discovery identifies a concrete symbol, stop doing broad semantic discovery and switch to direct or symbol-aware navigation.

## `rg` - exact text search

Use when the literal thing is already known:

```bash
rg "AscendAttentionBackend"
rg "exact error text"
rg "some_config_flag"
```

Do not use Semble just to find a known class, function, filename, or exact error.

## Git - change/history search

If the suspected PR/commit is known, inspect it before broad repository exploration:

```bash
git show <commit>
git diff <base>..<head>
git log -- <path>
```

Known regressions should start from the known change boundary.

## Semble - conceptual code discovery

Semble indexes code locally and searches by meaning. Use it when the concept is known but the implementation location is not.

Example question:

```text
Where is the logic that selects the NPU attention implementation for decode?
```

Typical flow:

```text
conceptual question
  -> Semble search
  -> relevant code chunks
  -> concrete file/symbol
  -> direct navigation / Serena
```

Codex MCP configuration:

```toml
[mcp_servers.semble]
command = "uvx"
args = ["--from", "semble[mcp]", "semble"]
enabled = true
startup_timeout_sec = 120
```

The longer timeout avoids first-run failures while `uvx`, the embedding model, and caches warm up. During bootstrap, the installed user config is also pinned to the exact Semble CLI version so MCP startup does not silently fetch an unrelated future release.

Manual checks:

```bash
uvx --from "semble[mcp]" semble --version
semble search "attention backend selection" ~/code/sglang --top-k 5
semble savings
```

`.sembleignore` removes generated/build/binary noise while preserving tests and benchmarks.

## Serena - symbol relationships and refactoring

Serena is optional Phase 2 tooling. It uses language-server/IDE semantics and is useful after a concrete symbol is known.

Good Serena questions:

- all references to a symbol;
- callers of a function/method;
- declaration/implementation navigation;
- symbol-aware rename/refactor;
- impact across files.

It is not intended to replace `rg` for literal search or Semble for unknown conceptual discovery.

Install:

```bash
./wsl/05-install-serena-optional.sh
```

Then append `codex/config/serena.optional.toml` to `~/.codex/config.toml` and restart Codex.

## Model PR history skill

`model-pr-history-knowledge` is not a code index or LSP. It is a PR-driven historical knowledge base for model-family optimization paths across serving frameworks.

Use it to answer questions such as:

- which PR introduced or changed a model-specific fast path;
- which files/symbols historically changed for Qwen/DeepSeek/MiniMax/etc.;
- what regression risks were seen previously;
- whether a competitor framework already has a related optimization.

Historical evidence is context, not the source of truth for current `main`. Verify conclusions against the target Git commit/PR before editing.

## Prompt/session hooks

`codex/hooks/session_start.py` automatically discovers an open handoff for the current PR/branch/worktree and injects its path at session start. `codex/hooks/prompt_guard.py` performs a second task-aware handoff check for implementation-like prompts and also blocks standalone push-only prompts before model invocation:

```text
push
git push
push it
```

It intentionally does not block richer requests where Git operations are part of an engineering objective.

Manual handoff diagnostics:

```bash
python3 .codex/scripts/resolve-handoff.py --json
python3 .codex/scripts/handoff-status.py consume <handoff.md>
```

Normal users should not need to provide the handoff path in the prompt; the hook injects it.

## Large logs

### You do not need to mention the reducer in the prompt

For a **local or downloaded** log, `AGENTS.override.md` and the log-analysis skill define this as the default workflow:

```text
log >= 1 MiB OR >= 10,000 lines
  -> check size/line count without reading the body
  -> MUST NOT read the raw log in full
  -> run reducer
  -> read .codex-artifacts/logs/<name>.focused.txt
  -> inspect narrow raw ranges only if a concrete fact is missing
```

So this is enough:

```text
Analyze /tmp/npu-ci.log and find the root cause.
```

The reducer command is:

```bash
cd ~/code/sglang
.codex/scripts/extract-log-context.py /tmp/npu-ci.log
```

By default it **writes** the reduced artifact instead of dumping it into the tool output:

```text
.codex-artifacts/logs/npu-ci.log.focused.txt
```

The terminal receives only a short summary/path. This avoids replacing one huge raw-log read with a huge reduced-log tool response.

Typical output:

```text
Focused log: /home/user/code/sglang/.codex-artifacts/logs/npu-ci.log.focused.txt
Source: 7342812 bytes, 68144 lines
Matches: 407 total, 120 included
```

Then inspect the focused artifact for the first failure/traceback, HCCL/ACL/AICore errors, shapes/dtypes, timeout/hang signals, and relevant latency/throughput/memory lines. Read the original log only by a narrow range when a specific missing fact requires it.

The path `.codex/scripts/...` is **inside the configured SGLang checkout** after `03-setup-sglang-workspace.sh`; the source shipped by this kit lives at `repo/.codex/scripts/...`.

Use `--stdout` only when you intentionally want the focused content printed to the terminal/model context:

```bash
.codex/scripts/extract-log-context.py --stdout /tmp/npu-ci.log
```

## OpenCode external workers

OpenCode is the harness for `local`, `cheap`, and `strong` model tiers. The workspace contains `opencode.json`, which loads `AGENTS.override.md` and the Semble MCP server. Dynamic provider/model details come from `~/.config/sglang-workflow/models.env` and are injected by `ai-task`; API credentials are not stored in the SGLang checkout.

Use `ai-task --dry-run <kind> ...` to inspect a route. Use `local-task`, `cheap-task`, `strong-task`, or `ai-task --tier ...` when deterministic provider selection matters.

External model selection does not weaken the normal search ladder or artifact contracts. Once an exact path/symbol is known, use direct retrieval; large logs still go through the reducer; report-only actionable findings still become compact handoffs.

See [Multi-model routing](MULTI_MODEL.md).
