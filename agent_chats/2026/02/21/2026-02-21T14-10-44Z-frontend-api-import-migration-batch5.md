---
id: 2026-02-21T14-10-44Z-frontend-api-import-migration-batch5
date: 2026-02-21T14:10:44Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api, migration, "[refactor]"]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/app/register/page.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentGenerationFields.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentVariantModal.tsx
  - ai-pic-frontend/src/components/features/episode/AudioTimelineSection.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceScriptTabContent.tsx
  - ai-pic-frontend/src/components/features/script/ScriptScenesTab.tsx
  - ai-pic-frontend/src/components/features/tasks/useTaskPersistedStyle.ts
  - ai-pic-frontend/src/components/shared/ModelSelector.tsx
  - ai-pic-frontend/src/components/shared/MultiModelSelector.tsx
  - ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx
  - ai-pic-frontend/src/components/shared/modals/StoryboardVideoModal.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/ImageToImageSettingsForm.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/types.ts
  - ai-pic-frontend/src/hooks/useApi.ts
  - ai-pic-frontend/src/hooks/useScriptDetail.ts
  - ai-pic-frontend/src/hooks/useStyleSchema.ts
  - ai-pic-frontend/src/hooks/useVirtualIPDetail.ts
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageGeneration.ts
  - ai-pic-frontend/src/utils/api/types/video.types.ts
  - tasks.md
summary: "Completed batch5 frontend API import migration, fixed two production-build TypeScript regressions, and reduced legacy '@/utils/api' imports to four apiClient call sites."
---

## User Prompt

继续

## Goals

- Continue the frontend API import migration workstream.
- Move remaining `@/utils/api` imports to split endpoint/type modules where possible.
- Update `tasks.md` migration progress and keep validation evidence current.

## Changes

- Migrated a broad set of frontend hooks/components/pages from legacy `@/utils/api` imports to `@/utils/api/endpoints/*` and `@/utils/api/types/*`.
- Updated register flow import usage to call `authAPI.register`.
- Updated storyboard page imports to split endpoint/type modules, and fixed image fetch call to `virtualIPImageAPI.getImages(...)`.
- Restored missing fields in split `StoryboardVideoGenerationOptions` type (`fps`, `watermark`, `seed`, `camera_fixed`, `camera_control`, `use_end_frame`, etc.) to align with existing modal payload usage and unblock production TypeScript build.
- Updated `tasks.md` P0 progress from `已完成 98 / 剩余 27` to `已完成 121 / 剩余 4（apiClient 旧调用点）`.
- Reduced remaining legacy `from "@/utils/api"` references to four files:
  - `ai-pic-frontend/src/hooks/useVirtualIPDetail.ts`
  - `ai-pic-frontend/src/components/features/SceneStructurePanel.tsx`
  - `ai-pic-frontend/src/utils/storyNovelApi.ts`

## Validation

- `cd ai-pic-frontend && npm run lint` (pass, warnings only).
- Chrome MCP manual verification:
  - Opened `/register`, verified register page/form renders.
  - Opened `/episodes/136/storyboard`; redirected to login, logged in with `geyunfei / Gyf@845261`, then storyboard page loaded and rendered.
- `rg -n 'from "@/utils/api"' ai-pic-frontend/src | wc -l` => `4`.
- `pre-commit run --files ...` (pass after auto-format).
- `./docker/build_prod_images.sh`:
  - First run exposed TS error in `storyboard/page.tsx` (`virtualIPAPI.getVirtualIPImages` missing); fixed by using `virtualIPImageAPI.getImages`.
  - Second run exposed TS error in `StoryboardVideoModal.tsx` (`fps` missing on `StoryboardVideoGenerationOptions`); fixed by restoring missing option fields in split type file.
  - Final run passed: backend/frontend images built and pushed for `linux/amd64,linux/arm64`.

## Next Steps

- Migrate the last four legacy `@/utils/api` call sites by replacing direct `apiClient` usage with split endpoint modules.
- Continue shrinking oversized frontend page/component files following AGENTS limits.

## Linked Commits

- refactor(frontend): migrate api imports batch5
