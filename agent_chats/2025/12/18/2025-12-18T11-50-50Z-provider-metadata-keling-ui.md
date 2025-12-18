---
id: 2025-12-18T11-50-50Z-provider-metadata-keling-ui
date: 2025-12-18T11:50:50Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, provider, metadata]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/providers/google_provider.py
  - ai-pic-backend/app/services/providers/jimeng_provider.py
  - ai-pic-backend/app/services/providers/keling_provider.py
  - ai-pic-backend/app/services/providers/minimax_provider.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-frontend/src/app/environments/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-frontend/src/components/ImageToImageModal.tsx
  - ai-pic-frontend/src/components/StoryboardVideoModal.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Expose provider UI metadata (aspect ratios, camera controls) to frontend and thread aspect_ratio/camera_control through image/video pipelines."
---

## User Prompt

Extend provider metadata, surface provider-specific fields in UI, and validate image→video generation with keling once backend is ready.

## Goals

- Add provider metadata for image/video knobs (aspect ratio, watermark, camera control).
- Let frontend render model-specific options from backend responses for text/image → image/video flows.
- Run an end-to-end UI validation with a keling model after backend deployment.

## Changes

- Backend: enriched provider metadata (keling, minimax, volcengine, google, jimeng) with UI hints for aspect ratios, watermark and camera control; threaded `aspect_ratio` and `camera_control` through virtual IP, storyboard, and service/task worker paths.
- Frontend: Image/Storyboard modals now read provider UI metadata for sizes/aspect ratios/camera control; virtual IP, environments, and storyboard pages pass `aspect_ratio` and camera control to APIs; API types updated accordingly.

## Validation

- `pytest tests/unit/test_generate_video_provider_model.py -q`
- `npm run lint`
- `./docker/build_prod_images.sh` (tag 42fa187)
- Chrome (docker dev stack on localhost:8089, login geyunfei): attempted storyboard scene image generation for “Step Outline E2E” but tasks failed (`未找到分镜数据` with no timeline/frames), so keling image→video run was blocked; stack shut down afterward.

## Next Steps

- Seed storyboard timeline/frames and rerun keling image→video generation in UI to confirm the new provider metadata is exercised end-to-end.

## Linked Commits

- (pending)
