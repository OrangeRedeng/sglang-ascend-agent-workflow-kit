# Models and subscriptions

## Codex inside Copilot Chat

`grikomsn.openai-oauth-copilot-chat` registers a native Copilot Chat language-model provider backed by the user's ChatGPT/Codex subscription.

The kit only manages safe workspace defaults:

```json
{
  "openaiCodex.showUsageStatusBar": true,
  "openaiCodex.catalogCacheMinutes": 5,
  "openaiCodex.debugLogging": false
}
```

Do not pin a Codex model or reasoning effort in the repository. Choose them in the Copilot Chat model picker. The provider's authenticated live catalog is authoritative.

Authentication is intentionally manual:

```text
Codex Bridge: Add ChatGPT Account
profile: personal
→ complete OAuth

Chat: Manage Language Models
→ Add Models
→ Codex Bridge
→ profile: personal
```

## BigModel GLM inside Copilot Chat

`yijiazhen-qi.glm-for-github-copilot-chat` is configured for the Mainland China Coding Plan:

```json
{
  "glm-copilot.apiMode": "coding-plan",
  "glm-copilot.region": "china",
  "glm-copilot.thinking": "enabled",
  "glm-copilot.showUsageStatusBar": true,
  "glm-copilot.usageRefreshIntervalMinutes": 5
}
```

Set the key with `GLM: Set API Key`; VS Code stores it in SecretStorage. GLM-5.3 exposes Low/High/Max reasoning choices through the Copilot model configuration.

## Fallback official Codex

`OpenAI.chatgpt` remains installed but is not the default daily UI. Use it when native Codex hooks/session behavior is more important than keeping both providers in one Copilot conversation surface.
