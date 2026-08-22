# Models, pricing, and free options

> Pricing/status checked: **2026-08-22**. Provider pricing, quotas, model IDs, and promotional discounts change frequently. Treat this page as a dated reference, not a billing guarantee. Always verify the provider's current pricing page before committing significant spend.

The workflow kit does not require a specific model vendor. The installer asks whether Codex should be the primary backend; if not, the primary backend can be a self-hosted OpenAI-compatible endpoint or an external API. Optional `local`, `cheap`, and `strong` slots can be configured later with `workflow-configure`.

> **SGLang + Ascend priority:** this table is for capacity/cost planning. It is not a recommendation to delegate hardware-sensitive conclusions to the cheapest model. Whichever model is primary must follow the same Ascend runtime/version/backend/profiling/benchmark gates. Use cheaper/free models primarily for bounded reconnaissance unless you have validated them on your own SGLang + Ascend tasks.

## Recommended roles

| Backend/model | Typical role in this kit | Notes |
|---|---|---|
| Codex / GPT-5.6 Luna | low-cost Codex profile | Good for bounded mechanical work when Codex is primary. |
| Codex / GPT-5.6 Terra | default Codex development profile | Balanced implementation/reasoning. |
| Codex / GPT-5.6 Sol | hard review, NPU/distributed/performance work | Highest-cost Codex tier in the bundled profiles. |
| DeepSeek V4 Flash | `cheap` API worker | Very low token price, 1M context, tool calls supported. |
| DeepSeek V4 Pro | `strong` API worker | Still inexpensive for broad repository investigation. |
| Z.AI GLM-4.7-Flash | free/experimental `cheap` worker | Provider lists token usage as free; 200K context. Rate limits/availability still apply. |
| Z.AI GLM-5.3 | `strong` coding worker | Available PAYG or through the Coding Plan; tuned for long-horizon coding. |
| Kimi K3-256K | `strong` coding worker | Recommended by Kimi for routine coding when 256K is sufficient. |
| MiniMax M2.7 | `cheap` or `strong` worker | Low pay-as-you-go price; coding/tool integrations available. |
| Qwen3-Coder-Flash | `cheap` worker | Low-cost coding model with up to 1M context depending on request size/region. |
| Qwen3-Coder-Plus | `strong` worker | Function calling and up to 1M context. |
| OpenRouter Free Models Router | free experimental worker | Zero token charge, but low request limits and model selection can vary. |
| Self-hosted coding model | `local` worker or primary | No per-token provider fee; you pay for hardware/server/electricity. |

A model that is cheap per token can still be expensive if it causes excessive retries or reads too much repository context. The handoff/log-reduction/session rules are intended to keep that overhead bounded.

## Free / zero-token-charge options

| Option | Token charge | Main limitation | Suggested use |
|---|---:|---|---|
| Z.AI `glm-4.7-flash` | Free at the checked provider price | Rate/availability limits can change | docs, CI classification, bounded reconnaissance |
| OpenRouter `openrouter/free` | $0 for selected free models | 50 requests/day normally; model may vary | experiments and non-critical worker tasks |
| Alibaba Qwen-Coder new-user quota | Free quota in Singapore International | Account/activation expiry and regional eligibility | initial evaluation of Qwen Coder |
| Self-hosted OpenAI-compatible model | No provider token fee | Hardware, power, hosting, maintenance | repeatable private worker/primary after local validation |

“Free” here means no per-token inference charge under the stated offer; it does not imply unlimited capacity or zero infrastructure cost. For Ascend/NPU conclusions, the same engineering gates apply regardless of price.

## OpenAI / Codex

The bundled Codex profiles use the Codex client. **ChatGPT/Codex subscription quota and OpenAI API billing are separate products.** Using the Codex CLI while authenticated through your eligible ChatGPT plan does not mean that the token prices below are charged to your API account. The API prices are included only as a cross-provider reference.

Reference OpenAI prices used by Codex/ChatGPT Work metering and the direct API can differ by service tier. The table below records the release-time standard rates relevant to the bundled model tiers for short context; verify the live OpenAI pricing page before API budgeting:

| Model | Input | Cached input | Output | Context |
|---|---:|---:|---:|---:|
| GPT-5.6 Luna | $0.20 | $0.02 | $1.20 | 1.05M |
| GPT-5.6 Terra | $2.00 | $0.20 | $12.00 | 1.05M |
| GPT-5.6 Sol | $5.00 | $0.50 | $30.00 | 1.05M |

Long-context requests can use different pricing. See:

- https://openai.com/api/pricing/
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
- https://developers.openai.com/api/docs/models/gpt-5.6-terra
- https://developers.openai.com/api/docs/models/gpt-5.6-sol

## DeepSeek V4

DeepSeek exposes an OpenAI-compatible API at `https://api.deepseek.com` and supports tool calls for the V4 Flash/Pro models.

Per 1M tokens:

| Model ID | Cache-hit input | Cache-miss input | Output | Context |
|---|---:|---:|---:|---:|
| `deepseek-v4-flash` | $0.0028 | $0.14 | $0.28 | 1M |
| `deepseek-v4-pro` | $0.003625 | $0.435 | $0.87 | 1M |

Preset:

```bash
workflow-configure --slot cheap --preset deepseek
workflow-configure --slot strong --preset deepseek
```

Source: https://api-docs.deepseek.com/quick_start/pricing/

## Z.AI / GLM

Z.AI currently lists `GLM-4.7-Flash` as free for input, cached input, cache storage, and output, with a 200K context window. It is useful for experimentation and bounded low-cost tasks; free availability/rate limits can change.

Other published pay-as-you-go reference prices per 1M tokens include:

| Model | Input | Cached input | Output |
|---|---:|---:|---:|
| GLM-4.7-Flash | Free | Free | Free |
| GLM-4.7-FlashX | $0.07 | $0.01 | $0.40 |
| GLM-5 | $1.00 | $0.20 | $3.20 |
| GLM-5.1 | $1.40 | $0.26 | $4.40 |
| GLM-5.3 | $1.40 | $0.26 | $4.40 |

GLM-5.3 is available both as pay-as-you-go API access and through the GLM Coding Plan. Z.AI advertises the individual Lite plan at a **$18/month list price** (promotional discounts may be shown), with higher Pro/Max tiers. GLM-5.3 supports `low`, `high`, and `max` reasoning effort and is positioned for long-horizon coding tasks.

Presets:

```bash
workflow-configure --slot cheap --preset zai-free
workflow-configure --slot strong --preset zai-coding
```

Sources:

- https://docs.z.ai/guides/overview/pricing
- https://docs.z.ai/guides/llm/glm-4.7
- https://z.ai/blog/glm-5.3
- https://z.ai/subscribe

## Kimi

Kimi Code provides an OpenAI-compatible coding endpoint at `https://api.kimi.com/coding/v1`.

Useful coding model IDs:

| Model ID | Context | Role |
|---|---:|---|
| `k3` | up to 1M depending on membership | large-codebase / long-context work |
| `k3-256k` | 256K | routine coding; Kimi states it has the same result quality as K3 inside 256K while consuming about half the membership quota |
| `kimi-for-coding` | 256K | Kimi K2.7 Code |
| `kimi-for-coding-highspeed` | 256K | faster K2.7 Code tier |

For the direct Kimi K3 API, the official release-time price is:

| Model | Cache-hit input | Cache-miss input | Output | Context |
|---|---:|---:|---:|---:|
| Kimi K3 (`kimi-k3`) | $0.30 | $3.00 | $15.00 | 1M |

Kimi Code membership quotas are separate from direct pay-as-you-go API billing.

Preset for the coding membership endpoint:

```bash
workflow-configure --slot strong --preset kimi-code
```

Sources:

- https://www.kimi.com/code/docs/en/
- https://www.kimi.com/code/docs/en/kimi-code/models.html
- https://www.kimi.com/resources/kimi-k3-pricing
- https://platform.kimi.com/

## MiniMax

MiniMax publishes the following pay-as-you-go text prices per 1M tokens:

| Model | Input | Cache read | Cache write | Output |
|---|---:|---:|---:|---:|
| `MiniMax-M2.7` | $0.30 | $0.06 | $0.375 | $1.20 |
| `MiniMax-M2.7-highspeed` | $0.60 | $0.06 | $0.375 | $2.40 |

MiniMax also offers fixed-price Token Plans; the published standard plans start at $10/month, with larger request quotas at higher tiers.

Preset:

```bash
workflow-configure --slot strong --preset minimax
```

Sources:

- https://platform.minimax.io/docs/guides/pricing-paygo
- https://platform.minimax.io/docs/guides/pricing-token-plan

## Alibaba Cloud / Qwen Coder

For the international Model Studio deployment scope, Qwen Coder pricing varies with the request context length. Reference pay-as-you-go prices per 1M tokens are:

### Qwen3-Coder-Flash

| Input length | Input | Output |
|---|---:|---:|
| <=32K | $0.30 | $1.50 |
| 32K-128K | $0.50 | $2.50 |
| 128K-256K | $0.80 | $4.00 |
| 256K-1M | $1.60 | $9.60 |

### Qwen3-Coder-Plus

| Input length | Input | Output |
|---|---:|---:|
| <=32K | $1.00 | $5.00 |
| 32K-128K | $1.80 | $9.00 |
| 128K-256K | $3.00 | $15.00 |
| 256K-1M | $6.00 | $60.00 |

For eligible new users in the Singapore International deployment, Alibaba currently lists a **1M-token free quota for each Qwen-Coder model**, generally valid for 90 days after Model Studio activation. Eligibility and expiry are account/region dependent, so check the Model Studio console before relying on the quota.

Alibaba Cloud also offers a Coding Plan. The current Pro plan is listed at $50/month with 6,000 requests per 5 hours, 45,000/week, and 90,000/month; its exact allowlist includes Qwen, GLM, Kimi, and MiniMax models.

Presets:

```bash
# Fixed-price Coding Plan
workflow-configure --slot strong --preset alibaba-coding

# Singapore International PAYG Qwen Coder
workflow-configure --slot cheap --preset alibaba-payg
workflow-configure --slot strong --preset alibaba-payg
```

`alibaba-payg` uses the generic Singapore-compatible endpoint shipped by the kit for portability. Alibaba's newest documentation also supports workspace-specific regional base URLs; use `workflow-configure --slot ...` with a custom base URL if your account requires one.

Sources:

- https://www.alibabacloud.com/help/en/model-studio/model-pricing
- https://www.alibabacloud.com/help/en/model-studio/qwen3-coder-plus
- https://www.alibabacloud.com/help/en/model-studio/qwen-coder
- https://www.alibabacloud.com/help/en/model-studio/new-free-quota
- https://www.alibabacloud.com/help/en/model-studio/coding-plan

## OpenRouter free models

OpenRouter exposes `openrouter/free`, which selects from currently available free models while filtering for requested capabilities such as tool calling or structured output.

Current free-tier limits documented by OpenRouter:

- **50 free-model requests/day** for a normal free account;
- **1,000 free-model requests/day** after purchasing at least $10 of credits;
- free-model availability and context limits can vary.

This is appropriate for experimentation, docs, classification, and bounded reconnaissance. It is not a reliable default for critical implementation because the selected free model can vary between requests.

Preset:

```bash
workflow-configure --slot cheap --preset openrouter-free
```

Sources:

- https://openrouter.ai/docs/guides/routing/routers/free-router
- https://openrouter.ai/docs/faq
- https://openrouter.ai/pricing

## Self-hosted models

A self-hosted endpoint has **no per-token provider charge**, but it is not literally free: GPU/CPU time, electricity, server rental, storage, and operations still have a cost.

The kit expects an OpenAI-compatible endpoint, for example:

```text
http://server:8000/v1
```

Common serving layers include:

- vLLM;
- SGLang;
- llama.cpp OpenAI-compatible server;
- Ollama through an OpenAI-compatible endpoint/gateway;
- LM Studio;
- another service that implements the OpenAI-compatible chat/tool-calling behavior needed by OpenCode.

Candidate open-weight coding models change quickly. Examples worth evaluating include Qwen Coder-family models and other coding/agent models that your hardware can serve. Do not select only by parameter count: tool calling, instruction following, long-context stability, diff understanding, and multi-step agent behavior matter more for this workflow.

Configure a local endpoint with:

```bash
workflow-configure --slot local
```

For unattended installation:

```bash
export AI_LOCAL_BASE_URL=http://server:8000/v1
export AI_LOCAL_MODEL=your-model-id
export AI_LOCAL_API_KEY=not-needed
./setup.sh --level standard --primary local --non-interactive --yes
```

## Choosing a cost strategy

A conservative setup is:

```text
primary = codex
routing = primary
```

Nothing outside Codex is required. Add external slots only when useful.

A cost-optimized setup is:

```text
local   -> self-hosted reconnaissance/logs/docs
cheap   -> DeepSeek Flash / Qwen Coder Flash / free provider
strong  -> DeepSeek Pro / GLM / Kimi / Qwen Coder Plus / MiniMax
primary -> whichever backend you trust as the main implementation agent
```

Then explicitly enable:

```text
AI_ROUTING_MODE=hybrid
```

Use `ai-task --dry-run ...` before real tasks to verify which backend would run. Hybrid fallback is **availability routing**, not semantic verification: if a configured model runs and returns a bad answer or an ordinary error, the router does not silently send the same task to another provider.
