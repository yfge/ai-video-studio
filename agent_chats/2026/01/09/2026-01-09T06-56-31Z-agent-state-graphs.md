---
id: 2026-01-09T06-56-31Z-agent-state-graphs
date: "2026-01-09T06:56:31Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [docs, langgraph, agents]
related_paths:
  - scripts/generate_agent_graphs.py
  - docs/agent_graphs/story_langgraph_agent.png
  - docs/agent_graphs/episode_langgraph_agent.png
  - docs/agent_graphs/script_langgraph_agent.png
  - docs/agent_graphs/storyboard_react_reasoner.png
  - docs/agent_graphs/timeline_langgraph_agent.png
  - docs/agent_graphs/duration_orchestrator_agent.png
  - README.md
  - README_EN.md
  - docs/README.md
summary: "Generate and publish agent state diagrams (LangGraph → Mermaid/PNG) in README"
---

## User Prompt

langgraph 是支持生成状态图的吧？可不可以把现在所有 agent 都生成状态图片加到 readme 里？

## Goals

- 为当前主要 Agent 提供可视化状态图（PNG + Mermaid 源码）。
- 将状态图入口放进中英文 README，方便快速理解与排障。
- 提供一键再生成脚本，避免后续变更后手工维护。

## Changes

- 新增脚本 `scripts/generate_agent_graphs.py`，生成 LangGraph StateGraph 的 Mermaid/PNG 输出到 `docs/agent_graphs/`。
- 生成并提交 6 张状态图（Story/Episode/Script/Storyboard/Timeline/Duration Orchestrator）。
- 更新 `README.md` 与 `README_EN.md`，以折叠块形式嵌入状态图与源码路径。
- 更新 `docs/README.md` 索引，新增 `docs/agent_graphs/` 入口。

## Validation

- `python scripts/generate_agent_graphs.py`
- 打开 `README.md` / `README_EN.md`，确认图片引用路径正确。

## Next Steps

- 如需保证持续一致，可在 CI 中增加“状态图是否需要更新”的检查（对比脚本输出与仓库文件）。
- 对“概念流程”的图（Story/Episode）可进一步与实际实现对齐/注明约束（例如最大重试次数）。

## Linked Commits

- (this commit)
