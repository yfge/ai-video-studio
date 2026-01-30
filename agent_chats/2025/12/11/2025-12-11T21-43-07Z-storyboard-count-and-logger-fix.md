---
id: 2025-12-11T21-43-07Z-storyboard-count-and-logger-fix
date: 2025-12-11T21:43:07Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/services/task_worker.py
summary: "Fix storyboard img2img logger/count NameErrors so Celery tasks actually run and use requested count"
---

## User Prompt

给你所有权限了，你来处理！！！（分镜图生图任务一直快速成功但未触发生成）

## Goals

- Eliminate NameErrors in storyboard img2img handler and correctly propagate `count` from payload so tasks execute fully.

## Changes

- Added a local `logger = get_logger("storyboard_image_task")` in `_process_storyboard_image_task` and removed references to undefined `payload`.
- Extended `_process_storyboard_image_task` signature with `count: int = 1`, computing a clamped `count_int` there.
- Updated `storyboard_image_generate_task` to parse and clamp `payload["count"]` (1-4) and pass it into `_process_storyboard_image_task`.

## Validation

- Not yet re-run storyboard generation (pending next user-triggered request) but this removes the obvious NameError paths that previously short-circuited the task.

## Next Steps

- [ ] Re-run storyboard img2img for script 19 and verify `[SBIMG]` logs appear and images are generated.

## Linked Commits

- (pending)
