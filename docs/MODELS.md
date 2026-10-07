# Models and provider roles

Status reviewed for this release: 2026-10-07. Provider models, quotas and subscription terms change; verify provider documentation before relying on a quota.

## OpenAI / Codex

OpenAI remains the default provider and the VS Code extension's native model/reasoning UI is preserved. The kit ships OpenAI profiles for light/default/hard/xhigh work.

## BigModel / Z.AI GLM Coding Plan

The kit supports GLM-5.3 through Codex's Responses-compatible custom provider path.

| Region | Endpoint | Reasoning |
|---|---|---|
| BigModel China | `https://open.bigmodel.cn/api/v1` | low / high / max |
| Z.AI Global | `https://api.z.ai/api/v1` | low / high / max |

The included GLM catalog declares a 1,048,576-token context window and freeform apply-patch support following the provider's Codex integration metadata. The API key is read from private workflow config at launch time.

Suggested role in this kit: bounded repository investigation, documentation, routine fixes/refactors, first-pass review, and iterative kernel scaffolding. `balanced` routing keeps hard NPU/distributed/performance/kernel verification on the OpenAI hard profile by default.

## Other external providers

`workflow-configure` retains presets for DeepSeek, Z.AI free API access, Kimi Code, MiniMax, OpenRouter free routing, Alibaba Coding Plan, and Alibaba Model Studio. These use the optional OpenCode harness and are independent of GLM's Codex-native integration.

## Self-hosted

Any OpenAI-compatible vLLM/SGLang/llama.cpp/gateway can occupy the `local` slot. Validate tool calling and long-context behavior before using it as an editing agent.
