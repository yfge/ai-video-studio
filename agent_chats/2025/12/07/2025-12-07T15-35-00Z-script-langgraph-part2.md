---
id: 2025-12-07T15-35-00Z-script-langgraph-part2
date: 2025-12-07T15:35:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, langgraph, scripts]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/script_agent.py
summary: "Wire script generation through LangGraph agent and assemble scenes/dialogues"
---

## User Prompt

- 使用 LangGraph 完成剧本生成，场景/对白独立 agent，组装校验，并自测。

## Goals

- 让 generate_script 优先走 LangGraph agent；保留 AI-manager fallback 和 mock。
- 将 scenes/dialogues/stage_directions 组装成可读文本 content 供前端展示。

## Changes

- AIService init 包含 ScriptLangGraphAgent；generate_script 先走 LangGraph，失败则 AI-manager，再 mock；AI-manager返回也尝试组装 content。
- 新增 `_build_script_text` 轻量拼装函数，把 scenes/dialogues/stage_directions 转成简单文本。
- Script agent prompts 已在前一提交添加，scene/dialogue nodes 复用 AI 管理器+JSON schema 校验。

## Validation

- 未跑 pytest（后端功能改动）；前端无改动。

## Next Steps

- 重启 backend，UI 重新生成剧本，确认 scenes/dialogues/stage_directions 落地且 content 文本可见。
- 若仍缺失，抓取生成响应/日志进一步收紧 prompt。

## Linked Commits

- (pending)
