---
id: 2025-12-22T15-44-11Z-model-ui-standardization
date: 2025-12-22T15:44:11Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, frontend, refactor]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_generation.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_variants.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/helpers.py
  - ai-pic-backend/app/services/providers/image_param_utils.py
  - ai-pic-backend/app/services/providers/google_provider/image.py
  - ai-pic-backend/app/services/providers/jimeng_provider.py
  - ai-pic-backend/app/services/providers/keling_provider/image.py
  - ai-pic-backend/app/services/providers/openai_provider/image.py
  - ai-pic-backend/app/services/providers/openai_provider/provider.py
  - ai-pic-backend/app/services/providers/volcengine_provider/image.py
  - ai-pic-backend/app/services/providers/volcengine_provider/provider.py
  - ai-pic-frontend/src/components/features/environments/EnvironmentCreateOverlay.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentGenerationFields.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentSidePanel.tsx
  - ai-pic-frontend/src/components/features/environments/types.ts
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx
  - ai-pic-frontend/src/components/shared/ModelUiFields.tsx
  - ai-pic-frontend/src/components/shared/ImageModelUiFields.tsx
  - ai-pic-frontend/src/components/shared/VideoModelUiFields.tsx
  - ai-pic-frontend/src/components/shared/modelUiTypes.ts
  - ai-pic-frontend/src/hooks/useVirtualIPImages.ts
  - ai-pic-frontend/src/hooks/virtual-ip/virtualIpImageConstants.ts
  - ai-pic-frontend/src/hooks/virtual-ip/virtualIpImageTypes.ts
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageData.ts
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageUpload.ts
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageActions.ts
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageGeneration.ts
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageVariants.ts
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/utils/modelUi.ts
summary: "Standardized image model UI metadata and split virtual IP image hooks"
---

## User Prompt

- Reported environment text-to-image could not select model parameters on the environment detail page.
- Noted environment text-to-image tasks failed when choosing Volcengine Seedream 4.5.
- Requested frontend + backend standardization and to continue checking.

## Goals

- Ensure environment text-to-image can select model parameters (size/ratio) and submit tasks reliably.
- Normalize image parameter handling and UI metadata across providers.
- Refactor front-end model UI and virtual IP image hooks into smaller modules.

## Changes

- Added shared image parameter normalization and size/aspect rules for providers, and applied normalization in image generation providers.
- Enriched OpenAI/Volcengine remote model listings with UI metadata so size options appear for Seedream and DALL-E models.
- Split model UI rendering into focused components and refactored virtual IP image hooks for clearer responsibilities.
- Wired environment generation fields and virtual IP image forms to the shared model UI and fixed virtual IP cache key usage.
- Passed aspect ratio through environment generation endpoints/tasks and auto-selected the first available model to surface ratio options where supported.

## Validation

- npm run lint (ai-pic-frontend): PASS.
- pytest (ai-pic-backend): TIMED OUT at 120s; multiple existing failures across diagnostic endpoints, user management e2e, keling tests, api/migrations/models suites.
- ./docker/build_prod_images.sh: PASS (backend + frontend images built and pushed).
- MCP Chrome E2E: Environment detail page -> Google model shows "画幅比例" options; switch provider to 火山引擎 and model doubao-seedream-4-5 -> only size (2K) shown, no ratio field.

## Next Steps

- Investigate baseline pytest failures/timeouts to enable clean backend test runs.
- Spot-check image-to-image and virtual IP image generation flows with the new UI metadata.

## Linked Commits

- d5e09eb
