---
id: 2025-12-10T07-34-22Z-img2img-model-visibility
date: 2025-12-10T07:34:22Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, ui]
related_paths:
  - ai-pic-frontend/src/components/MultiModelSelector.tsx
summary: "Ensure img2img modal shows provider models by relaxing type matching between image and image_to_image."
---

## User Prompt

- “图生图的 modal 调用了 /models/available 并返回，但页面没有展示。”

## Goals

- Make img2img modal actually render provider models when the backend returns image types that don’t exactly match `image_to_image`.

## Changes

- Added model type matching helper so image and image_to_image types are considered compatible in `MultiModelSelector`, preventing empty lists when backend returns image models.
- Kept lint clean (no warnings).

## Validation

- `npm run lint`

## Next Steps

- Re-open the img2img modal after fetching models to confirm the provider list now renders; if a provider still hides models, share the API response snippet for further mapping.

## Linked Commits

- pending
