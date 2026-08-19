# Acknowledgements

This workflow kit builds on the work and documentation of several open-source projects and communities.

## Core tooling

- [OpenAI Codex](https://developers.openai.com/codex/) - coding agent, CLI, configuration, MCP, hooks, profiles, and agent workflows used by this kit.
- [SGLang](https://github.com/sgl-project/sglang) - the primary serving repository this workflow targets.
- [sgl-kernel-npu](https://github.com/sgl-project/sgl-kernel-npu) - Ascend/NPU kernels and related optimized components used by SGLang.
- [Ascend/pytorch](https://github.com/Ascend/pytorch) - the PyTorch adapter that provides the `torch_npu` runtime used by Ascend PyTorch workloads.
- [Semble](https://github.com/MinishLab/semble) by MinishLab - local semantic code search and MCP integration.
- [Serena](https://github.com/oraios/serena) by Oraios - optional symbol-aware/LSP-based code navigation and refactoring.

## Skills and engineering workflows

- [AI-Infra-Auto-Driven-SKILLS](https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS) by BBuf - SGLang review, model PR history, profiler/pipeline analysis, incident triage, and evidence-driven optimization workflow ideas used by the selected skill set.
- [Ascend Agent Skills](https://github.com/Ascend/agent-skills) - official Ascend skills for NPU adaptation review, profiling anomalies, HCCL, Triton, AscendC, environment, and related workflows.
- [awesome-ascend-skills](https://github.com/ascend-ai-coding/awesome-ascend-skills) - community collection containing the `torch_npu`, profiling, operator benchmark, op-plugin, Triton-Ascend, and AscendC skills selected by this kit.

## Supporting developer tools

- [GitHub CLI](https://github.com/cli/cli)
- [uv](https://github.com/astral-sh/uv)
- [ripgrep](https://github.com/BurntSushi/ripgrep)
- [Visual Studio Code](https://code.visualstudio.com/) and the WSL extension
- [WSL](https://learn.microsoft.com/windows/wsl/) for the Windows/Linux development environment

## Methodology inspiration

The session/handoff/Goal/artifact-ledger approach is informed by the SGLang Team article [Agent-Assisted SGLang Development: An Initial Exploration](https://www.lmsys.org/blog/2026-07-02-agent-assisted-sglang-development), particularly the idea that repeatable engineering state should be externalized into scripts, skills, benchmark contracts, and artifacts instead of relying exclusively on long chat transcripts.

## Trademark and license note

Names and trademarks belong to their respective owners. This repository does not vendor the external skill repositories listed above; setup scripts clone them from their original sources and link selected skills into a local SGLang checkout. Each external project remains governed by its own license and terms.

This workflow kit is an independent project and is not affiliated with or endorsed by OpenAI, the SGLang project, Huawei/Ascend, MinishLab, Oraios, BBuf, or the other projects listed above.
