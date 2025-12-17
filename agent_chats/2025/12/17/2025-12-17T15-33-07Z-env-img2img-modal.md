---
id: 2025-12-17T15-33-07Z-env-img2img-modal
date: 2025-12-17T15:33:07Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, environment, img2img]
related_paths:
  - ai-pic-frontend/src/app/environments/[id]/page.tsx
summary: "Reuse the shared ImageToImageModal for environment image variants"
---

## User Prompt

IP/环境/分镜的图生图交互统一，复用一套 ImageToImageModal。

## Goals

- Let environment images use the same ImageToImageModal variant flow as IP/分镜.
- Keep interaction/controls consistent.

## Changes

- Environment detail page now wires each reference图 to open the shared `ImageToImageModal` with the selected image as reference, default prompt from环境描述/名称, and submits to the existing `/environments/{id}/images/variants-async` API.
- Adds per-image “图生图” action alongside delete, reusing the common modal and model cache key (`environment-img2img`).

## Validation

- `npm run lint` ✅
- No live backend browser run in this step (same modal already validated earlier with mock); behavior mirrors IP/分镜 usage.

## Next Steps

- End-to-end check against real backend to confirm variant tasks create and new images appear after refresh.

## Linked Commits

- TBC: environment img2img modal hookup
