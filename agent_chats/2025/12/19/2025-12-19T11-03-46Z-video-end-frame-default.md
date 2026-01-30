---
id: 2025-12-19T11-03-46Z-video-end-frame-default
date: 2025-12-19T11:03:52Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, video, bugfix]
related_paths:
  - ai-pic-backend/app/services/video/video_task_utils.py
summary: "Default storyboard video generation to not use end frames"
---

## User Prompt

- 最近的视频未传入尾帧却仍按尾帧生成，要求检查参数链路并修复。

## Goals

- Ensure end frames are only used when explicitly requested.

## Changes

- Changed `use_end_frame` default to `False` in `normalize_submission_options` so missing flags no longer fall back to storyboard end frames.

## Validation

- `docker logs --tail 200 ai-video-celery-worker` reviewed to confirm Keling status responses contain `task_status`.
- `pytest` (ai-pic-backend) timed out after 120s with existing failures.
- `./docker/build_prod_images.sh` succeeded (tag `0390f2f`).
- Chrome MCP: logged in and opened `http://localhost:8089/tasks`.

## Next Steps

- Restart worker and submit a new video task without `use_end_frame` to confirm no end frame is used.

## Linked Commits

- Pending
