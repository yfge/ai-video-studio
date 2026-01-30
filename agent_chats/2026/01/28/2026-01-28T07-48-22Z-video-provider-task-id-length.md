---
id: 2026-01-28T07-48-22Z-video-provider-task-id-length
date: 2026-01-28T07:48:22Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, video, database, migration]
related_paths:
  - ai-pic-backend/app/models/video_generation_task.py
  - ai-pic-backend/alembic/versions/9c1a2b3c4d5e_expand_video_provider_task_id.py
summary: "Expand provider_task_id length for video generation tasks to fit Vertex operation names"
---

## User Prompt

提交修复：ai-video-celery-worker 写入 video_generation_tasks 时 provider_task_id 太长导致错误。

## Goals

- 扩大 provider_task_id 字段长度以容纳 Vertex operation name
- 提供数据库迁移

## Changes

- 将 `video_generation_tasks.provider_task_id` 扩展为 `String(512)`
- 新增 Alembic 迁移以升级/回滚字段长度

## Validation

- `cd ai-pic-backend && pytest` ❌ 启动后长时间无进展，已中止（仅看到收集 1070 tests；无完成报告）
- `pre-commit run --all-files` ⚠️ 未复跑（上一轮在本地触发大量历史文件改动且 `ruff`/`backend-pytest` 失败）
- `./docker/build_prod_images.sh` ✅ backend/frontend 镜像构建并推送完成（tag: 6daa9d1）

## Next Steps

- 执行 `alembic upgrade head` 或 `python manage.py migration upgrade` 应用迁移

## Linked Commits

- TBD
