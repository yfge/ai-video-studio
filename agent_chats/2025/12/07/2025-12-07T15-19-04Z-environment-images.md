---
id: 2025-12-07T15-19-04Z-environment-images
date: 2025-12-07T15:19:04Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, environment, image]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Add environment image generation/variant APIs and frontend controls to manage environment reference images"
---

## User Prompt

先做环境的文生图和图生图管理？
可以，现在按照 tasks.md 对环境管理的规划，整体完成环境管理这个功能，注意要保证 chrome 测试完整。

## Goals

- Allow environments to manage reference images via AI (text-to-image and image-to-image) and deletion.
- Surface the controls in the `/environments` page so users can generate/variant/delete reference images without auto-generating anything.

## Changes

- Backend (`story_structure.py`):
  - Added environment image endpoints: list, generate (文生图 via ai_manager.generate_image), variants (图生图 via ai_manager.image_to_image), and delete.
  - Normalized downloads to `/uploads` and append to `Environment.reference_images`.
- Frontend (`/environments` page):
  - Display environment reference images as thumbnails with delete and variant buttons.
  - Added “AI 生成参考图” block per environment using `ModelSelector` (image type) and a one-click generate button.
  - Wired new API client methods (`listEnvironmentImages`, `generateEnvironmentImages`, `generateEnvironmentImageVariants`, `deleteEnvironmentImage`) in `src/utils/api.ts`.

## Validation

- Chrome manual: `/environments` loads without backend errors; cards now show thumbnails (if any), and the new generate button triggers the backend call (model selectable). Deleting/variant buttons hit the corresponding endpoints. No automated tests run.

## Next Steps

- Feed environment reference images into storyboard generation as environment anchors alongside character anchors.
- Consider adding a dedicated modal for custom prompt/model/size inputs and better progress feedback on generation tasks.

## Linked Commits

- pending
