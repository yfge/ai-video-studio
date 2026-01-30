---
id: 2025-12-18T05-53-26Z-environment-images-list
date: 2025-12-18T05:53:26Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, environments]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-frontend/src/app/environments/[id]/page.tsx
summary: "Fixed environment images endpoint to return images for business_id paths and reflected on frontend."
---

## User Prompt

http://localhost:8089/environments/2b21e78c2504484a9d01417bea9f9d62 看不到图片

## Goals

- Ensure environment images load when visiting detail page via business_id.
- Align images API response shape so frontend receives URLs.

## Changes

- Backend `/environments/{env_id}/images` now resolves business_id/id and returns `EnvironmentImagesResponse` directly (no envelope), preserving stored URLs instead of being stripped by response_model.
- Frontend already uses business_id; no extra UI changes needed for this fix.

## Validation

- `curl /api/v1/auth/login` + `curl /api/v1/story-structure/environments/<business_id>/images` now returns image list (non-empty).
- `./docker/build_prod_images.sh` — pass (tag b68257a).

## Next Steps

- Deploy backend image `b68257a` and reload frontend to confirm images render on page.

## Linked Commits

- (pending)
