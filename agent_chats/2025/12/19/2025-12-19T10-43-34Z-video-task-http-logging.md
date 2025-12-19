---
id: 2025-12-19T10-43-34Z-video-task-http-logging
date: 2025-12-19T10:43:41Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, celery, logging, video]
related_paths:
  - ai-pic-backend/app/services/providers/keling_provider/video_tasks.py
  - ai-pic-backend/app/services/providers/minimax_provider/video_tasks.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video_tasks.py
summary: "Log provider HTTP responses for video task status polling"
---

## User Prompt
- 需要看到 HTTPS 请求的返回，怀疑查询任务的处理没有正确。

## Goals
- Log the raw provider responses for video task status polling in the celery worker.

## Changes
- Added info-level logs for task status HTTP responses in Keling, MiniMax, and Volcengine polling paths.

## Validation
- `pytest` (ai-pic-backend) timed out after 120s with existing failures.
- `./docker/build_prod_images.sh` succeeded (tag `73aa848`).
- Chrome MCP: reloaded `http://localhost:8089/tasks` to confirm the UI remains accessible.

## Next Steps
- Verify worker logs show the provider response bodies during the next polling run.

## Linked Commits
- Pending
