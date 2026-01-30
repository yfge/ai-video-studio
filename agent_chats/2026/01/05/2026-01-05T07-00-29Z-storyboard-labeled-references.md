---
id: 2026-01-05T07-00-29Z-storyboard-labeled-references
date: 2026-01-05T07:00:29Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, frontend, storyboard]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx
  - ai-pic-frontend/src/components/shared/modals/index.ts
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts
summary: "Pass labeled reference images through storyboard image generation"
---

## User Prompt

Commit current changes and use localhost:8089.

## Goals

- Persist labeled reference images from the UI through to storyboard image generation.
- Validate via build/lint/tests and an end-to-end browser flow.
- Commit the current changes with a matching agent chat ledger entry.

## Changes

- Added labeled reference metadata to storyboard image generation request payloads and task worker handling.
- Injected labeled reference context into prompts to clarify character/environment intent for AI.
- Built labeled references in the image-to-image modal and threaded them through the storyboard page and API client.

## Validation

- `./docker/build_prod_images.sh` (success).
- `pytest` (failed: 90 failed, 7 errors; missing fixtures like `admin_token`/`username` plus multiple integration test failures).
- `npm run lint` (success; warnings in `src/components/features/episode/WorkspaceStoryboardTabContent.tsx`).
- Chrome MCP E2E on `http://localhost:8089`: logged in as `geyunfei`, opened story id `6d7c528b4b064a5f99689f095f5bef90`, entered episode id `cd378417b7f143eab5bc6d063cd7f6e7` storyboard, opened Image-to-Image modal on frame 2, submitted task, saw success toast.

## Next Steps

- Resolve the failing pytest suite or confirm expected failures before committing.
- Re-run pytest after fixture/test environment updates.

## Linked Commits

- (pending)
