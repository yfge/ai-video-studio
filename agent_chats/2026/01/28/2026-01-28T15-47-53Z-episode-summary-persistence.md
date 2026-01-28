---
id: 2026-01-28T15-47-53Z-episode-summary-persistence
date: 2026-01-28T15:47:53Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, episode, context-pack]
related_paths:
  - ai-pic-backend/app/services/episode/episode_summary.py
  - ai-pic-backend/app/services/episode/episode_generation_persistence.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py
  - ai-pic-backend/tests/unit/services/episode/test_episode_summary.py
  - ai-pic-backend/tests/unit/services/episode/test_episode_generation_persistence.py
  - tasks.md
summary: "Persist per-episode episode_summary for context pack continuity."
---

## User Prompt

按 tasks.md 推进：新增/补齐“每集摘要”产物（episode_summary），用于后续连续性与上下文注入。

## Goals

- 生成剧集时持久化 `episode_summary`（用于 context pack 的 recent episodes）。
- 同步/异步两条生成链路都覆盖。
- 补单测并更新 `tasks.md` 进度。

## Changes

- 新增 `build_episode_summary()`：将模型输出的 summary（或 plot_points/conflicts 兜底）规范化为短摘要。
- 在 Episode 生成落库时写入 `Episode.extra_metadata["episode_summary"]`：
  - 同步：`create_episode_models()`
  - 异步：`episodes/async_tasks.py`（callbacks 路径 + fallback 路径）
- 新增单测覆盖 summary builder 与持久化。
- 更新 `tasks.md`：标记 episode_summary 已完成。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py ai-pic-backend/app/services/episode/episode_generation_persistence.py ai-pic-backend/app/services/episode/episode_summary.py ai-pic-backend/tests/unit/services/episode/test_episode_summary.py ai-pic-backend/tests/unit/services/episode/test_episode_generation_persistence.py tasks.md agent_chats/2026/01/28/2026-01-28T15-47-53Z-episode-summary-persistence.md`
- `./docker/build_prod_images.sh` (tag: `c94ea79`)
- Chrome (MCP):
  - 登录 `geyunfei / Gyf@845261`
  - 进入 Story：`/stories/cd0843195eb54cc28a7e3c9b0f8def63`（story_id=36），点击“开始生成”（异步）
  - MySQL 验证：`episodes.story_id=36` 新增 episode（id=128），`extra_metadata.episode_summary` 非空

## Next Steps

- 前端：在“生成剧集/再生成”弹窗提供 context pack 预览与开关，并接入 preview API。
- 验证：同一 Story 连续生成/再生成 2 次 episode，抽检关键设定一致性与 ledger 更新。

## Linked Commits

- (pending)
