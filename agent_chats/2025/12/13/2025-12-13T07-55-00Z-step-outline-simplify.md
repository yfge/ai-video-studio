---
id: 2025-12-13T07-55-00Z-step-outline-simplify
date: 2025-12-13T07:55:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, agent, episode]
related_paths:
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/app/prompts/templates/episode_step_outline.txt
  - ai-pic-backend/app/prompts/templates/episode_step_outline.yaml
  - ai-pic-backend/app/prompts/templates/episode_step_outline_repair.txt
  - ai-pic-backend/app/prompts/templates/episode_from_outline.txt
  - ai-pic-backend/app/prompts/templates/episode_from_outline.yaml
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/tests/unit/test_episode_step_outline_light.py
summary: "Simplified episode step outline to single-logline, ensured prompt propagation, and added lightweight agent tests."
---

## User Prompt
简化剧集 Step Outline，只保留一句话概要，后续细节在剧集生成环节完成，并修复当前卡死问题。

## Goals
- 减轻 Step Outline schema/提示复杂度，允许仅一句话 logline。
- 修复 episodes 生成时 prompt 缺失导致的 500 错误。
- 增加单元/模拟测试覆盖 outline 校验与逐集生成。

## Changes
- 放宽 `EpisodeStepOutlineModel` 中 beats 为可选；Step Outline 提示改为只要求一句话 logline，beats 允许留空；修订 repair 提示说明 beats 可选。
- Episode 生成提示支持无 beats 的场景，以 logline 驱动剧情拆分。
- `EpisodeLangGraphAgent`：过滤空 logline、保留 prompt/provider/model/usage 传递到后续节点；repair 阶段要求 logline 非空才算有效；返回 prompt 供存储使用。
- 端点 `episodes/generate`：容错 prompt 缺失，ai_model 支持回落 model_used，beats 为空时不落库。
- 新增模拟测试 `tests/unit/test_episode_step_outline_light.py`，覆盖 logline-only 路径和修复路径。

## Validation
- `pytest tests/unit/test_episode_step_outline_light.py` ✅
- `pytest` （全量）⏱️ 超时并有大量环境相关失败（外部依赖/权限），未完成；仅记录，未修复。

## Next Steps
- 修复/重跑全量 pytest 需准备外部服务与较长时间窗口。
- 重新跑端到端故事→剧集生成以验证 500 已消失。

## Linked Commits
- TODO: add commit hash after commit
