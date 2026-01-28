---
id: 2026-01-28T02-28-44Z-storyboard-env-role-image-e2e
date: 2026-01-28T02:28:44Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, storyboard, docs, tests, tasks]
related_paths:
  - ai-pic-backend/tests/test_migration_environment_assets.py
  - docs/TESTING_GUIDE.md
  - tasks.md
summary: "补齐环境+角色 → 分镜图像生成 E2E 用例，并新增 environments 迁移回归测试。"
---

## User Prompt

- 继续完成 P0/P1 任务：补齐“选择环境 + 角色后分镜帧稳定生成对应图像”的端到端验证，并把用例写入 `TESTING_GUIDE.md`；同时为 `environments` 表与关联字段补迁移回归用例。

## Goals

- 在真实浏览器路径验证：绑定 `scene.environment_id` + `shot.character_ids` 后，分镜批量生图能稳定产出关键帧。
- 在 `/tasks` 中确认生成任务的 `task_type` 与 `parameters.agent_run` 可审计。
- 为 `environments` / `scenes.environment_id` / `shots.character_ids` 增补迁移回归测试。
- 更新 `tasks.md` 对应条目状态。

## Changes

- 新增迁移回归测试：`ai-pic-backend/tests/test_migration_environment_assets.py`
- 补齐 E2E 操作说明：`docs/TESTING_GUIDE.md`
- 看板条目完成：`tasks.md`

## Validation

- Chrome E2E（Docker+Nginx 开发环境，`http://localhost:8089`）：
  - 登录：`/login`，账号 `geyunfei`
  - 分镜页：`/episodes/124/storyboard`（当前剧本 `ID: 113`）
  - 场景 1：
    - 绑定环境：选择 `会议室 (indoor)`（`environment_id=4`）并保存，提示「场景环境已更新」
    - 绑定镜头角色：选择 `老拐` + `文闻`（`character_ids=[1,2]`）并保存，提示「镜头角色已更新」
    - 点击「为此场景批量生成图像」创建任务，任务完成后页面出现分镜关键帧图（`/ai-generated/storyboard/...`），并能看到 `参考图 9 张`
  - 任务页：`/tasks`
    - 任务 `5855` 类型为 `storyboard_image_generation`，状态「已完成」
    - 详情中可见 `Agent 执行轨迹`，`parameters.agent_run.generation_method=storyboard_image`
- pytest：`cd ai-pic-backend && pytest tests/test_migration_environment_assets.py -q`
- 生产镜像构建：`./docker/build_prod_images.sh`

## Next Steps

- 如需更强一致性：允许在分镜批量生图时显式选择可用的 image-to-image provider/model，减少自动 fallback 导致的锚点弱化。

## Linked Commits

- (pending)
