---
id: 2025-12-19T10-50-02Z-keling-task-status-mapping
date: 2025-12-19T10:50:08Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, celery, video, bugfix]
related_paths:
  - ai-pic-backend/app/services/providers/polling_utils.py
summary: "Fix Keling task status mapping to use task_status field"
---

## User Prompt
- 查看 ai-video-celery-worker 日志，发现任务已生成但未更新；对照 docs/keling 修复逻辑。

## Goals
- Align Keling status mapping with the documented `task_status` field so completed tasks update correctly.

## Changes
- Updated `keling_status_mapper` to read `task_status` (fallback to `status`) per `docs/api/keling/imagetovideo.md`.

## Validation
- `docker logs --tail 200 ai-video-celery-worker` showed Keling responses with `task_status: succeed` but DB status stayed `processing`.
- `pytest` (ai-pic-backend) timed out after 120s with existing failures.
- `./docker/build_prod_images.sh` succeeded (tag `e126d24`).
- Chrome MCP: reloaded `http://localhost:8089/tasks`.

## Next Steps
- Restart the celery worker and confirm polled tasks transition to succeeded.

## Linked Commits
- Pending
