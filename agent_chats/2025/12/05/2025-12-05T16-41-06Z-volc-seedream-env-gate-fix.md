---
id: 2025-12-05T16-41-06Z-volc-seedream-env-gate-fix
date: 2025-12-05T16:41:06Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-providers, bugfix]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
summary: "Ensure Seedream 4.5 image model shows up when only VOLCENGINE_API_KEY is configured"
---
## User Prompt
图像生成模型里还是没有 SeeDream  你自己测试吧，我累了

## Goals
- Make Seedream 4.5 actually appear in the image model list given the real env variables in use.

## Changes
- Relaxed Volcengine provider initialization in `AIService._initialize_ai_manager` to require only `VOLCENGINE_API_KEY` (SECRET_KEY remains optional), matching Ark docs that use a single bearer token.
- Updated `virtual_ip_images.get_available_models` to gate Volcengine image models (including Seedream 4.5) on `VOLCENGINE_API_KEY` alone instead of requiring both key and secret.

## Validation
- ai-pic-backend: `cd ai-pic-backend && pytest tests/test_story_structure_endpoints.py -q`

## Next Steps
- After restarting the docker-compose stack with the existing `docker/.env` (which already has VOLCENGINE_API_KEY set), the Virtual IP image model selector should show `Seedream 4.5 — volcengine` in addition to the other image models.

## Linked Commits
- (pending)
