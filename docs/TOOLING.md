# Tooling and search routing

The tools in this kit solve different retrieval problems. They should not all run for every question.

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

## Prompt guard

`codex/hooks/prompt_guard.py` blocks standalone push-only prompts before model invocation:

```text
push
git push
push it
```

It intentionally does not block richer requests where Git operations are part of an engineering objective.

## Large logs

Do not paste or read a full multi-megabyte CI/NPU log first. Use the local reducer:

```bash
.codex/scripts/extract-log-context.py <log-file>
```

Then inspect the failure window, relevant errors, shapes/dtypes, HCCL/ACL/AICore messages, and performance/memory lines.
