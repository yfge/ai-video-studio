---
id: 2025-12-11T21-27-26Z-storyboard-logging
date: 2025-12-11T21:27:26Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Add detailed logging for storyboard img2img to see prompts and reference counts when tasks run"
---

## User Prompt

用户提供帧提示词与参考图，生成任务仍未触发；需要排查为什么。

## Goals

- Surface what the storyboard worker sees (frames, prompts, reference counts) to debug why generation might skip.

## Changes

- Added structured logging in `_process_storyboard_image_task` (frame index, scene, prompt length, ref counts, target indexes) and guard for out-of-range indexes.

## Validation

- Not run; logging will appear on next storyboard img2img run.

## Next Steps

- [ ] Re-run the storyboard generation for script 19 frame 5 and check Celery logs for the new messages to confirm prompt/ref processing.

## Linked Commits

- (pending)
