# VS Code workflow

Open the SGLang worktree from WSL:

```bash
cd ~/code/sglang
code .
```

Use **GitHub Copilot Chat** as the normal UI. The updater installs:

```text
GitHub.copilot-chat
grikomsn.openai-oauth-copilot-chat
yijiazhen-qi.glm-for-github-copilot-chat
OpenAI.chatgpt   # fallback only
```

Copilot Chat then hosts two independent providers:

- **Codex Bridge**: ChatGPT OAuth, live Codex model catalog, model-specific reasoning controls, agent tool calls and Codex quota status.
- **GLM Models**: BigModel China Coding Plan, GLM model picker entries, Low/High/Max for GLM-5.3 and Coding Plan quota status.

The official OpenAI Codex extension remains installed as a fallback because Codex-specific hooks execute only in the native Codex runtime, not when the Codex model is hosted by Copilot Chat.

Shared `AGENTS.md` and `.agents/skills/` apply to the project regardless of which provider is selected in Copilot Chat.
