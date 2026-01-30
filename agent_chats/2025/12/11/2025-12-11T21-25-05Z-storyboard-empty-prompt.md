---
id: 2025-12-11T21-25-05Z-storyboard-empty-prompt
date: 2025-12-11T21:25:05Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Fallback prompt for storyboard img2img frames with missing ai_prompt/description so tasks don’t short-circuit"
---

## User Prompt

目标是有prompt 的，你没有取到吧

## Goals

- Prevent storyboard img2img tasks from skipping frames when ai_prompt/description is empty.

## Changes

- Added a fallback prompt in `_process_storyboard_image_task` so frames without ai_prompt/description still generate with a generic, scene-aware prompt, ensuring the task runs and uses references.

## Validation

- Not run; requires retrying storyboard generation on frames lacking prompt to confirm images are produced.

## Next Steps

- [ ] Re-run the storyboard generation for frame 1 with the provided reference images to confirm it now generates instead of skipping.

## Linked Commits

- (pending)
