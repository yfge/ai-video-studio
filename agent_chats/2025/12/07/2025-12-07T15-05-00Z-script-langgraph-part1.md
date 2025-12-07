---
id: 2025-12-07T15-05-00Z-script-langgraph-part1
date: 2025-12-07T15:05:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, langgraph, scripts]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/prompts/templates/script_scenes.txt
  - ai-pic-backend/app/prompts/templates/script_dialogues.txt
summary: "Add script LangGraph agent scaffolding and prompts for scenes/dialogues"
---

## User Prompt

- 使用 LangGraph 完成剧本生成，场景/对白各自独立 agent，最终组装校验。

## Goals

- 引入 ScriptLangGraphAgent 承载场景规划与对白生成节点。
- 为场景/对白生成新增专用 prompt 模板。
- 让 AIService 初始化脚本 agent，为后续完整接管 generate_script 做准备。

## Changes

- 新增 `ScriptLangGraphAgent`（scene_plan → dialogue → assemble）和对应 prompts：`script_scenes.txt`、`script_dialogues.txt`。
- PromptTemplate 增加 SCRIPT_SCENES/SCRIPT_DIALOGUES 常量并登记分类。
- AIService 初始化脚本 agent；后续将把 generate_script 路由到该 agent（尚未完成全链路）。

## Validation

- 未跑 pytest（后端新功能搭建中）；前端无改动。

## Next Steps

- 完成 generate_script 的 LangGraph 路由和 AI-manager fallback 重构；重启后在 UI 触发剧本生成验证 scenes/dialogues 落地。

## Linked Commits

- (pending)
