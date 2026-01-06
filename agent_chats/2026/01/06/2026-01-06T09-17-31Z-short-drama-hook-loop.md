---
id: 2026-01-06T09-17-31Z-short-drama-hook-loop
date: 2026-01-06T09:17:31Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, prompts, storyboard, refactor]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/generation.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/regenerate.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/generation.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/api/v1/endpoints/stories/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/stories/generation.py
  - ai-pic-backend/app/prompts/templates/episode_duration_reject.txt
  - ai-pic-backend/app/prompts/templates/episode_from_outline.txt
  - ai-pic-backend/app/prompts/templates/episode_generation.txt
  - ai-pic-backend/app/prompts/templates/episode_step_outline.txt
  - ai-pic-backend/app/prompts/templates/script_dialogues.txt
  - ai-pic-backend/app/prompts/templates/script_generation.txt
  - ai-pic-backend/app/prompts/templates/storyboard_generation.txt
  - ai-pic-backend/app/prompts/templates/storyboard_plan.txt
  - ai-pic-backend/app/prompts/templates/storyboard_scene.txt
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/app/schemas/generation_requests.py
  - ai-pic-backend/app/schemas/script.py
  - ai-pic-backend/app/services/ai/episodes.py
  - ai-pic-backend/app/services/ai/scripts_ai_manager.py
  - ai-pic-backend/app/services/ai/storyboard_utils.py
  - ai-pic-backend/app/services/script/script_utils.py
  - ai-pic-backend/app/services/story/story_generation_service.py
  - ai-pic-backend/app/utils/marketing_meta.py
  - tasks.md
summary: "Extended episode/script/storyboard generation to carry micro-genre, hook, and ad metadata across schemas and prompts."
---

## User Prompt
开始进行 Feature: 短剧微类型与投流驱动创作闭环（故事→剧本→时间线→分镜）🔥，优先完成 Episode/Script/Storyboard schemas + prompts 扩展，并确保自测完整且原子提交。

## Goals
- 扩展 Episode/Script/Storyboard 生成 schema 与上下文，覆盖市场/微类型/爽点/投流素材字段
- 更新 episode/script/storyboard prompt 模板，注入微类型与 hook 规则
- 确保后端生成链路在额外元数据与 generation_params 中保留这些字段

## Changes
- 新增 `app/schemas/generation_requests.py` 并迁移 Story/Episode/Script generation 请求结构，补充 market/micro/hook/ad 字段
- 新增 `app/utils/marketing_meta.py`，在 episode/script/storyboard 生成链路合并与覆盖营销元数据
- 扩展 `app/schemas/generation.py` 中 EpisodePlanItem、ScriptMetadata、StoryboardFrame 字段
- Episode 生成（同步/异步/再生成）合并 hook/ad 元数据并写入 generation_params/extra_metadata
- Script 生成（legacy 同步/异步/再生成/预览）与 Storyboard 上下文注入微类型与爽点字段
- 更新 episode/script/storyboard prompt 模板以体现微类型/钩子/投流素材
- 更新 `tasks.md` 进度状态

## Validation
- `pytest` (ai-pic-backend): 超时 120s，过程中出现多处失败（约 11% 时终止）。
- `./docker/build_prod_images.sh`: 成功（tag 037e775）。
- Chrome MCP E2E：在 `http://localhost:8089/stories/90d90dea749448ffa40bcfdce8bc9711` 点击“生成剧集→开始生成”触发 `/api/v1/episodes/generate-async` 返回 404；随后在 DevTools 复现 `GET/POST http://localhost:8000/api/v1/*` 多个接口返回 404，账号重新登录返回 401（`Incorrect username or password`），未能完成生成验证。

## Next Steps
- 排查本地 `localhost:8000` API 路由/认证状态（确认 `/api/v1/episodes/generate-async` 是否可用），恢复 E2E 生成链路并补录验证。
- 继续补齐“投流素材生成模板”与评分/投流表 agent 任务。

## Linked Commits
- (pending)
