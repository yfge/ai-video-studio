---
id: 2025-12-07T14-30-00Z-episode-langgraph-agent
date: 2025-12-07T14:30:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, langgraph, episodes]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/episode_agent.py
summary: "Route episode generation through a LangGraph agent when available, with AI-manager fallback"
---

## User Prompt

- 使用 LangGraph、agent 形式完成剧本/剧集生成，并在浏览器自测。

## Goals

- 引入 LangGraph agent 管线生成剧集；保持无 LangGraph/无密钥时的回退。

## Changes

- 新增 `EpisodeLangGraphAgent`（StateGraph plan→finalize）封装 AI 管理器调用，输出 episode 计划并标记 generation_method。
- AIService 优先尝试 LangGraph agent；提炼 `_call_ai_manager_episode` 复用 JSON Schema 调用逻辑，保持原有 fallback。

## Validation

- 未跑 pytest；前端 lint 依旧通过。后端需重启并配好模型 key 后再通过 UI 生成剧集验证。

## Next Steps

- 前端生成剧集后确认 scenes 已通过自动补全/AI 返回；必要时扩展 agent 节点评审/修复场景结构。

## Linked Commits

- (pending)
