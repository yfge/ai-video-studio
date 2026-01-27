---
id: 2026-01-27T15-12-59Z-tasktype-production-backfill
date: 2026-01-27T15:12:59Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, tasks, audit]
related_paths:
  - ai-pic-backend/scripts/backfill_task_types.py
  - tasks.md
summary: "Ran production TaskType backfill for legacy image_generation tasks and updated the task board."
---

## User Prompt

继续完成 P0：生产执行历史任务 TaskType 回填（先 dry-run，按 user/时间分批），并确保 /tasks 可按正确 task_type 过滤。

## Goals

- 将历史 `Task.task_type=image_generation` 回填为更细粒度的 domain TaskType，提升可审计性与可筛选性。
- 覆盖老数据里不一致的 title/prompt 模式，避免回填遗漏。
- 在真实浏览器 `/tasks` 页面验证过滤效果。

## Changes

- 更新 `ai-pic-backend/scripts/backfill_task_types.py`：补充匹配中文 prompt（如“为虚拟IP … 生成…图像”）→ 回填为 `virtual_ip_image_generation`。
- 执行回填（docker / MySQL）：
  - `user_id=1`，`2026-01-01T00:00:00Z`~`2026-02-01T00:00:00Z`：74 条（22 storyboard_image / 16 virtual_ip_image / 14 virtual_ip_variant / 14 environment_image / 8 environment_variant）。
  - `user_id=1`，`2025-12-01T00:00:00Z`~`2026-01-01T00:00:00Z`：211 条（94 storyboard_image / 26 virtual_ip_image / 37 virtual_ip_variant / 30 environment_image / 24 environment_variant）。
  - `user_id=4`，`2025-12-01T00:00:00Z`~`2026-01-01T00:00:00Z`：2 条（story_generation）。
- 更新 `tasks.md`：标记“生产回填”已完成。

## Validation

- Dry-run + apply：
  - `docker exec ai-video-backend bash -lc 'cd /app/ai-pic-backend && python scripts/backfill_task_types.py --user-id 1 --after 2026-01-01T00:00:00Z --before 2026-02-01T00:00:00Z --show-unmatched 20'`
  - `docker exec ai-video-backend bash -lc 'cd /app/ai-pic-backend && python scripts/backfill_task_types.py --apply --user-id 1 --after 2026-01-01T00:00:00Z --before 2026-02-01T00:00:00Z --show-unmatched 20'`
  - `docker exec ai-video-backend bash -lc 'cd /app/ai-pic-backend && python scripts/backfill_task_types.py --apply --user-id 1 --after 2025-12-01T00:00:00Z --before 2026-01-01T00:00:00Z --show-unmatched 20'`
  - `docker exec ai-video-backend bash -lc 'cd /app/ai-pic-backend && python scripts/backfill_task_types.py --apply --user-id 4 --after 2025-12-01T00:00:00Z --before 2026-01-01T00:00:00Z --show-unmatched 20'`
- 结果确认：`remaining_image_generation: 0`（SQL 统计）。
- Pytest（pre-commit quick gate）：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（845 passed）。
- 生产镜像：`./docker/build_prod_images.sh` 构建并推送成功（tag=7911338）。
- Chrome E2E：
  - 登录 `geyunfei`，进入 `/tasks`。
  - 选择“虚拟IP文生图”过滤：可看到 `23/12/2025` 创建的任务，类型为 `virtual_ip_image_generation`，且 `updated_at` 更新到回填执行时间。
  - 选择“图像生成”过滤：页面提示“暂无任务”，确认 legacy `image_generation` 已清空。

## Next Steps

- 若后续仍出现 `image_generation` 新任务，需定位入口并改为更明确的 domain TaskType。
- 如需进一步细分（例如 environment/virtual_ip 的子类型），同步扩展 backfill 规则与前端过滤项。

## Linked Commits

- (current) 本次变更与日志同一提交。

