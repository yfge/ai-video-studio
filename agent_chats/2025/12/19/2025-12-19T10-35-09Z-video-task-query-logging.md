---
id: 2025-12-19T10-35-09Z-video-task-query-logging
date: 2025-12-19T10:35:15Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, celery, logging, video]
related_paths:
  - ai-pic-backend/app/services/video/video_task_polling_service.py
summary: "Log video task poll query results in celery worker"
---

## User Prompt
- 将 ai-video-celery-worker 中任务查询的内容直接做日志输出。

## Goals
- Log the queried video generation tasks during the polling run so the worker logs show what was fetched.

## Changes
- Added pending-task query logging in `VideoTaskPollingService.poll_pending_tasks` with key fields per task.

## Validation
- `pytest` (ai-pic-backend) timed out after 120s with existing failures.
- `./docker/build_prod_images.sh` succeeded (tag `8b52891`).
- Chrome MCP: opened `http://localhost:8089/tasks` and verified the task list renders.

## Next Steps
- If needed, adjust the logged fields (e.g., include prompt length or parameters) to match debugging needs.

## Linked Commits
- Pending
