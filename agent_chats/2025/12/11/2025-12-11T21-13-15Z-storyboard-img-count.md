---
id: 2025-12-11T21-13-15Z-storyboard-img-count
date: 2025-12-11T21:13:15Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Pass storyboard img2img count from request to AI manager so multiple outputs are generated"
---

## User Prompt

所以并没有从前端把图片传过去
而且我选择的是四张图片，为什么只有一张？

## Goals

- Respect the requested image count for storyboard image generation.

## Changes

- Added `count` to `StoryboardImageRequest`, task payload, and `_process_storyboard_image_task`, passing it through to `image_to_image`/`generate_image` (capped at 4) so multiple images can be generated per frame.

## Validation

- Not run (logic change only); needs e2e verification with count=4.

## Next Steps

- [ ] Trigger storyboard img2img with count=4 to confirm multiple images are produced.

## Linked Commits

- (pending)
