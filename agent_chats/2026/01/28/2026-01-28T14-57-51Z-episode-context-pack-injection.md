---
id: 2026-01-28T14-57-51Z-episode-context-pack-injection
date: "2026-01-28T14:57:51Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, episodes, context-pack, prompts, agent-run]
related_paths:
  - tasks.md
  - ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py
  - ai-pic-backend/app/services/continuity/episode_continuity.py
  - ai-pic-backend/app/services/continuity/episode_generation_flow.py
  - ai-pic-backend/app/prompts/templates/episode_step_outline.txt
  - ai-pic-backend/app/prompts/templates/episode_generation.txt
  - ai-pic-backend/app/prompts/templates/episode_generation_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_generation_tv_series.txt
  - ai-pic-backend/app/prompts/templates/episode_generation_film.txt
  - ai-pic-backend/app/prompts/templates/episode_from_outline.txt
  - ai-pic-backend/app/prompts/templates/episode_from_outline_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_duration_reject.txt
  - ai-pic-backend/app/prompts/templates/episode_duration_reject_short_drama.txt
summary: "Inject StoryContextPack into episode generation prompts and persist used_context into Task.agent_run (async flow)."
---

## User Prompt

- Phase 2：希望把 Context Pack 注入 episode 生成的 prompt/agent 输入，并把 used_context 写入 `Task.parameters.agent_run`，用于后续一致性与排障。

## Goals

- 异步 episode 生成（Celery worker）在调用模型前构建 `StoryContextPack`（预算裁剪），并注入到 prompt 上下文。
- 将本次实际使用的 context pack（used_context）写入 agent_run（任务页可见）。
- 更新 episode prompt 模板：显式展示 Context Pack（“必须遵守”）。
- 避免 continuity audit/ledger update prompt 因 `story|tojson` 带入 context pack 导致 prompt 过大。

## Changes

- Backend: `ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py`
  - `_build_story_data` 补齐 `premise/default_aspect_ratio/continuity_ledger` 等字段。
  - 在调用 `ai_service.generate_episodes(...)` 前构建 `StoryContextPack`，写入 `story_data["context_pack"]`。
  - 在 step outline 的 `agent_run` 中写入 `used_context`（由 `persist_task_agent_run` 汇总进任务页）。
  - fallback 路径同样写入 `used_context`。
- Backend: `ai-pic-backend/app/services/continuity/episode_continuity.py`
  - 渲染 continuity audit/rewrite/ledger_update prompt 时，从 `story` 中剔除 `context_pack`（避免 `story|tojson` 膨胀）。
- Backend: `ai-pic-backend/app/services/continuity/episode_generation_flow.py`
  - 渲染 `episode_rewrite_with_audit` prompt 时同样剔除 `context_pack`。
- Prompts: 显式注入 Context Pack 区块
  - `ai-pic-backend/app/prompts/templates/episode_step_outline.txt`
  - `ai-pic-backend/app/prompts/templates/episode_generation*.txt`
  - `ai-pic-backend/app/prompts/templates/episode_from_outline*.txt`
  - `ai-pic-backend/app/prompts/templates/episode_duration_reject*.txt`
- Docs: `tasks.md`
  - Phase 2「Episode 生成显式注入 context pack + used_context 落库」标记完成。

## Validation

- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py ai-pic-backend/app/services/continuity/episode_continuity.py ai-pic-backend/app/services/continuity/episode_generation_flow.py ai-pic-backend/app/prompts/templates/episode_step_outline.txt ai-pic-backend/app/prompts/templates/episode_generation.txt ai-pic-backend/app/prompts/templates/episode_generation_short_drama.txt ai-pic-backend/app/prompts/templates/episode_generation_tv_series.txt ai-pic-backend/app/prompts/templates/episode_generation_film.txt ai-pic-backend/app/prompts/templates/episode_from_outline.txt ai-pic-backend/app/prompts/templates/episode_from_outline_short_drama.txt ai-pic-backend/app/prompts/templates/episode_duration_reject.txt ai-pic-backend/app/prompts/templates/episode_duration_reject_short_drama.txt tasks.md`
- `./docker/build_prod_images.sh`（buildx build+push；tag 为执行时的 HEAD: `87d8265`）
- docker 重启（开发环境，确保 Celery worker 生效）：
  - `docker restart ai-video-backend ai-video-celery-worker`
- Chrome E2E（docker + Nginx，账号 `geyunfei / Gyf@845261`）：
  - 打开 Story：`http://localhost:8089/stories/6131b3857ce9413b9a1fbc6a5b23d1f8`（story_id=37）
  - 在「生成剧集」展开表单，勾选「异步任务」，设置 `episode_count=3`，点击「开始生成」
  - 任务页 `http://localhost:8089/tasks`：任务 `5862` 状态 `已完成`，result `episodes:127`
  - 详情中 `parameters.agent_run.outline.used_context` 可见（含 `meta.budget/max_total_chars` 等字段）

## Next Steps

- Phase 2：episode 生成后自动回填 `Episode.extra_metadata.episode_summary`（用于最近 N 集摘要）。
- 前端：生成剧集弹窗接入 context pack preview + 开关（角色卡/最近摘要/ledger）。

## Linked Commits

- (pending)
