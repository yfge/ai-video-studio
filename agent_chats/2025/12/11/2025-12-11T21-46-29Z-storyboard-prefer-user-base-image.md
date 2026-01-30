---
id: 2025-12-11T21-46-29Z-storyboard-prefer-user-base-image
date: 2025-12-11T21:46:29Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Prefer user-provided storyboard reference images as base_image for img2img instead of stale frame/env placeholders"
---

## User Prompt

你现在可以查看 日志 了（分镜图生图仍优先用了 404 的 `symmetrical_architecture_shot.jpg` 而不是前端传入的参考图）。

## Goals

- Ensure storyboard img2img uses the user-selected reference image as the primary base_image so Seedream/Volcengine actually see the intended input.

## Changes

- Changed reference ordering in `_process_storyboard_image_task`: `ref_images_raw` now orders `payload_refs` (frontend reference_images) first, then existing frame_refs, then char_anchor_refs, then env_refs, while keeping `char_refs` description unchanged.

## Validation

- Not yet re-run, but next storyboard img2img call should show `image_to_image` base URL coming from a user-provided upload instead of the old `symmetrical_architecture_shot.jpg` placeholder.

## Next Steps

- [ ] Re-run the storyboard generation for script 19 frame 6 and confirm Celery logs show base_image pointing at one of the `/uploads/...png` URLs instead of the missing placeholder.

## Linked Commits

- (pending)
