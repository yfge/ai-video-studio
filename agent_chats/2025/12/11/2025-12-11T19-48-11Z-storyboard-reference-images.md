---
id: 2025-12-11T19-48-11Z-storyboard-reference-images
date: 2025-12-11T19:48:11Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, storyboard]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Ensure storyboard async image tasks forward frame/request reference images to providers"
---

## User Prompt

"目前文图生图的异步任务里没有把参考图真正的传进去，仔细排查一下" — investigate missing reference images in async image generation.

## Goals

- Trace storyboard async image generation and ensure any frame-level or request-scope reference images reach the downstream provider calls.

## Changes

- Updated `_process_storyboard_image_task` to merge frame-stored references, request `reference_images`, character anchors, and environment anchors into a normalized, de-duplicated list (preserving user/frame refs first) before invoking `image_to_image`; prompt annotations now reflect frame/user reference usage.

## Validation

- `python -m compileall ai-pic-backend/app/api/v1/endpoints/scripts.py`
- Chrome/MCP end-to-end check pending (no running frontend/backend instance in this session).

## Next Steps

- Run a quick storyboard image generation via Chrome once the app stack is up to confirm reference images are honored end-to-end.

## Linked Commits

- pending
