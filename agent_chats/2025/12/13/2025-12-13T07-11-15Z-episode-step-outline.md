---
id: 2025-12-13T07-11-15Z-episode-step-outline
date: 2025-12-13T07:11:15Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, langgraph, episodes]
related_paths:
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/app/services/story_structure_service.py
  - ai-pic-backend/app/prompts/templates/episode_step_outline.txt
  - ai-pic-backend/app/prompts/templates/episode_from_outline.txt
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/app/services/ai_service.py
summary: "Add step-outline-first LangGraph pipeline for episodes and persist beats to story_step_outlines"
---

## User Prompt

- 上阶梯式生成：先产出每集 Step Outline，再生成 Episode，并将 beats 落库。注意 ReAct 检查、上下文传入、逐集调用模型保证一致性。

## Goals

- 让 Episode agent 先生成 step outline，再按 outline 逐集生成 episodes。
- 回填 step outlines 至 `story_step_outlines`，并保持集数/情节点对齐。

## Changes

- 新增 Episode Step Outline/Pydantic 模型与 prompt 模板（outline/repair/from_outline）。
- 重写 `EpisodeLangGraphAgent`：outline→验证/修复→逐集 episode 生成，失败时让 AIService 回落。
- Episodes 生成接口写入 `story_step_outlines`（自动创建 treatment），附带 agent 元数据。
- Story structure service 增加 treatment 兜底和 step outline 批量插入。

## Validation

- pytest (backend): failed — 大量既有用例依赖外部服务/fixture 未配置（如 user token fixtures、OpenAI/Keling/OSS 连通性、迁移环境）。未跑 Chrome E2E（需后续在真实服务启动后补验证）。

## Next Steps

- 在可运行环境下重跑 pytest 并补 UI E2E（生成故事→剧集→落库 step outlines）。
- 视情况为 step outline 持久化增加集成测试/权限校验。

## Linked Commits

- (pending)
