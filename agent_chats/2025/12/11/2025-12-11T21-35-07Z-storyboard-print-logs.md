---
id: 2025-12-11T21-35-07Z-storyboard-print-logs
date: 2025-12-11T21:35:07Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Print storyboard img2img task details to stdout to debug missing generations"
---

## User Prompt

用户提供 prompt 和参考图，任务仍无生成日志，需要直接输出调试信息。

## Goals

- Emit visible stdout logs for storyboard img2img tasks (target indexes, prompts, refs) to trace why generation might skip.

## Changes

- Added print+logger statements for task start, frame index checks, prompt length, and reference counts; out-of-range indexes now printed explicitly.

## Validation

- Not run; expects to see `[SBIMG] ...` lines in Celery logs on next storyboard run.

## Next Steps

- [ ] Re-run storyboard generation for script 19 frame 6 and check worker logs for `[SBIMG]` lines to confirm prompt/ref handling.

## Linked Commits

- (pending)
