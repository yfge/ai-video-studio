---
id: 2025-12-11T21-05-25Z-google-img2img-provider-infer
date: 2025-12-11T21:05:25Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/services/ai_service_manager.py
summary: "Infer google provider for img2img flows so Gemini receives reference images in async pipelines"
---

## User Prompt
现在在ip的图生图页面，火山引擎是正常的，google还是没有传入图片

## Goals
- Ensure google/Gemini img2img requests in async/sync flows receive reference images instead of falling back to other providers.

## Changes
- Added provider inference via `infer_provider_from_model` in virtual IP img2img sync/async routes and worker so Gemini is selected when model names lack a provider prefix.
- Updated environment inference helper to recognize Gemini and storyboard generator to infer providers when model lacks prefix.
- Extended ai_service_manager fallback to map Gemini models to the google provider.

## Validation
- Not run (pending environment with Google credentials); changes are routing-level and rely on existing tests. Manual verification deferred.

## Next Steps
- [ ] Re-run async IP/environment/storyboard img2img with Gemini model to confirm reference images are passed and logged.
- [ ] Add a focused test or log assertion for provider inference when model strings omit prefixes.

## Linked Commits
- (pending)
