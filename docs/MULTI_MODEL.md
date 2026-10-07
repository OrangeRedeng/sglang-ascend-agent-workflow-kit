# Multi-model routing

## v0.3.1 architecture

The workflow separates **harness**, **provider**, and **engineering policy**.

```text
SGLang workflow + skills + handoffs
              |
       +------+------+
       |             |
     Codex         OpenCode
   preferred       optional
       |             |
 OpenAI / GLM   local/cheap/strong
```

`AI_PRIMARY_HARNESS=codex` is the recommended setup. `AI_PRIMARY_PROVIDER=openai` describes the default interactive provider; `AI_CODEX_ROUTING` controls task routing when GLM is available.

Legacy `AI_PRIMARY_BACKEND` remains for v0.2 compatibility.

## Codex provider policy

```text
balanced  GLM for bounded/general work; OpenAI hard profile for verify/Ascend/NPU/distributed/perf/kernel/deep
openai    always OpenAI profiles
glm       GLM profiles whenever the plan is configured
```

`balanced` is a conservative policy, not an empirically proven OpenAI-vs-GLM quality ranking. Keep hardware-sensitive conclusions on the OpenAI hard profile until matched GLM/OpenAI evals justify changing the routing table.

## Reasoning levels

OpenAI continues to use the bundled profiles (`lite/default/hard/xhigh`). GLM exposes `low`, `high`, and `max` through separate Codex profiles.

## External workers

`local`, `cheap`, and `strong` remain OpenCode-based OpenAI-compatible slots. Configure them only when needed:

```bash
workflow-configure --slot local
workflow-configure --slot cheap --preset deepseek
workflow-configure --slot strong --preset minimax
```

Provider fallback is not semantic verification. A successful but wrong worker response is not automatically sent to another provider.

## Inspect routing

```bash
ai-task --dry-run docs "..."
ai-task --dry-run review 34855
ai-task --dry-run npu "..."
```

## Routing invariant: SGLang + Ascend comes first

Model cost never bypasses the compatibility baseline, profiler discipline, benchmark comparability, or required NPU validation. In hybrid routing, the user-selected primary backend is tried first for correctness-sensitive hard classes unless an explicit tier override is used.
