# Replaceable model backends and routing

The workflow is model-provider-neutral at the router/artifact layer. Codex is the default primary choice offered by setup, not a mandatory dependency.

## Routing invariant: SGLang + Ascend comes first

Provider flexibility is a cost/capacity feature, not a relaxation of the engineering workflow. Every primary backend must follow the same SGLang repository rules and, for Ascend/NPU work, the same hardware/CANN/PyTorch/`torch_npu`/SGLang/backend/workload preflight and validation gates. `ai-task` chooses a harness/model; it does **not** certify that a model has enough evidence to make an NPU conclusion.

For correctness-sensitive `review`, `verify`, `ascend`, `npu`, `distributed`, `perf`, `kernel`, `deep`, and `xhigh` classes in hybrid mode, the **user-selected primary backend is tried first**. If the primary is Codex, the appropriate hard/xhigh Codex profile is first. If an external/self-hosted backend is primary, that exact primary is first. Other workers are fallbacks for availability or bounded reconnaissance; Codex is added behind a non-Codex primary only when `AI_ENABLE_CODEX_FALLBACK=1`.

## Configuration files

Topology (no secrets):

```text
~/.config/sglang-workflow/install.env
```

Model routing and credentials:

```text
~/.config/sglang-workflow/models.env
```

The second file is mode `0600` and is preserved across upgrades.

## Primary backend

```bash
AI_PRIMARY_BACKEND=codex
```

Allowed values:

- `codex` - use Codex profiles as the primary backend;
- `local` - self-hosted OpenAI-compatible endpoint through OpenCode;
- `cheap` - low-cost API slot through OpenCode;
- `strong` - stronger API slot through OpenCode;
- `none` - no automatic primary model.

The setup wizard asks:

```text
Use Codex as the primary model? [Y/n]
```

Answering `no` does not degrade the workflow into a special compatibility mode. The selected external/self-hosted backend becomes the normal primary backend.

## Routing modes

### Primary mode (default)

```bash
AI_ROUTING_MODE=primary
```

`ai-task` sends every task to the selected primary backend.

If the primary backend is Codex, task kind selects a Codex profile:

| Task class | Codex profile |
|---|---|
| docs / metadata / logs / search | `sglang-lite` |
| normal bug / CI / refactor / feature | `sglang` |
| review / verify / Ascend / NPU / distributed / perf / kernel | `sglang-hard` |
| deep / xhigh | `sglang-xhigh` |

If the primary backend is `local`, `cheap`, or `strong`, the chosen external tier receives the task instead.

### Hybrid mode (optional)

```bash
AI_ROUTING_MODE=hybrid
```

Hybrid routing chooses the first configured/available tier from a task-specific table. It is a **selection policy**, not a semantic multi-stage chain: a model that starts and returns a normal failure is not silently replaced by another model.

Typical preference for general/cost-sensitive classes:

| Task class | Worker preference in hybrid mode |
|---|---|
| docs / search / logs | local -> cheap -> strong -> primary |
| CI / bug / conflicts | cheap -> local -> strong -> primary |
| feature | strong -> cheap -> local -> primary |

For correctness-sensitive review and SGLang/Ascend hardware/performance classes, the selected **primary backend is first**. Configured workers follow only as availability fallbacks or for explicitly bounded reconnaissance. This prevents cost routing from silently replacing the model the user chose to own the NPU conclusion.

If Codex is not primary, it participates only when explicitly enabled:

```bash
AI_ENABLE_CODEX_FALLBACK=1
```

Provider fallback is not semantic verification.

## External slots

### Self-hosted slot

```bash
AI_LOCAL_BASE_URL=http://server:8000/v1
AI_LOCAL_MODEL=my-coder-model
AI_LOCAL_API_KEY=not-needed
AI_LOCAL_NPM=@ai-sdk/openai-compatible
AI_LOCAL_CONTEXT=131072
AI_LOCAL_OUTPUT=16384
```

Use any serving layer that exposes compatible model/tool-call behavior, for example vLLM, SGLang, llama.cpp, Ollama-compatible gateways, or another OpenAI-compatible proxy.

### Cheap API slot

```bash
AI_CHEAP_BASE_URL=https://provider.example/v1
AI_CHEAP_MODEL=cheap-coder
AI_CHEAP_API_KEY=...
```

### Strong API slot

```bash
AI_STRONG_BASE_URL=https://provider.example/v1
AI_STRONG_MODEL=strong-coder
AI_STRONG_API_KEY=...
```

The router deliberately does not hard-code DeepSeek, Qwen, GLM, Kimi, MiniMax, or any other vendor. `workflow-configure` provides convenience presets for public endpoint/model metadata, but those presets only populate the same generic slot fields. Change endpoint/model values without changing routing logic.

List presets:

```bash
workflow-configure --list-presets
```

See [Models, pricing, and free options](MODELS.md) for the current model table and source links.

## OpenCode harness

External tiers execute through OpenCode. Endpoint-specific provider configuration is injected dynamically through `OPENCODE_CONFIG_CONTENT`; API keys are provided through a temporary environment variable rather than committed to the SGLang worktree.

The project `opencode.json` loads `AGENTS.override.md`. Semble and Serena MCP entries are generated only when those tools were selected by installation, so a minimal/custom installation does not point OpenCode at missing MCP servers.

## Explicit overrides

```bash
ai-task --tier primary bug "Investigate the regression"
ai-task --tier local logs /tmp/npu-ci.log
ai-task --tier cheap ci "Classify the failures"
ai-task --tier strong review 34855
ai-task --tier codex-hard npu "Verify backend semantics"

local-task logs /tmp/npu-ci.log
cheap-task bug "Find the root cause"
strong-task review 34855
```

Codex-specific shortcuts exist only when Codex was installed:

```text
cxl
cx
cxh
cxx
```

## Cross-model artifacts

All full/core workflow backends share:

```text
.codex-artifacts/handoffs/
.codex-artifacts/goals/
.codex-artifacts/logs/
```

The `.codex/` directory name is retained for compatibility with previous releases, but most scripts under it are provider-neutral.

External workers export producer metadata such as:

```yaml
producer: opencode:kit-local/my-coder-model
consumer: codex
```

When another backend is primary, `consumer` records that primary backend instead. Handoff matching does not require the producer and consumer to be the same model.

Codex lifecycle hooks can inject a matching handoff automatically when Codex is installed. Other harnesses follow the explicit mandatory preflight:

```bash
python3 .codex/scripts/resolve-handoff.py --json
```

## Reconfiguration

Run:

```bash
workflow-configure
```

All prompts in the configuration utility are English. API keys use hidden terminal input.

Dry-run routing:

```bash
ai-task --dry-run review 34855
```
