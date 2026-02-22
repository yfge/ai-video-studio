---
id: 2026-02-22T03-10-21Z-frontend-api-deep-import-ban
date: 2026-02-22T03:10:21Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api, lint, "[refactor]"]
related_paths:
  - ai-pic-frontend/eslint.config.mjs
  - ai-pic-frontend/src/hooks/useImageGenProfiles.ts
  - ai-pic-frontend/src/components/shared/GenerationProfileSelect.tsx
  - ai-pic-frontend/src/hooks/useStoryReadiness.ts
  - ai-pic-frontend/src/components/features/story-detail/StoryReadinessPanel.tsx
  - tasks.md
summary: "Removed remaining deep API alias imports and added lint guard to enforce barrel-only imports from '@/utils/api/endpoints' and '@/utils/api/types'."
---

## User Prompt

继续

## Goals

- Continue API modular cleanup after removing legacy `src/utils/api.ts`.
- Eliminate remaining deep alias imports under `@/utils/api/endpoints/*` and `@/utils/api/types/*`.
- Enforce barrel-only API imports via ESLint to prevent regressions.

## Changes

- Migrated remaining deep imports to barrel imports:
  - `ai-pic-frontend/src/hooks/useImageGenProfiles.ts`
  - `ai-pic-frontend/src/components/shared/GenerationProfileSelect.tsx`
  - `ai-pic-frontend/src/hooks/useStoryReadiness.ts`
  - `ai-pic-frontend/src/components/features/story-detail/StoryReadinessPanel.tsx`
- Updated lint guard in `ai-pic-frontend/eslint.config.mjs`:
  - Added `no-restricted-imports` patterns for:
    - `@/utils/api/endpoints/*`
    - `@/utils/api/types/*`
  - Message guides contributors to use barrel imports only.
- Updated `tasks.md` migration note to include deep alias cleanup and lint enforcement.

## Validation

- Deep import scan:
  - `rg -n "@/utils/api/endpoints/|@/utils/api/types/" ai-pic-frontend/src ai-pic-frontend/tests` => no matches.
- Frontend lint:
  - `cd ai-pic-frontend && npm run lint` => pass (warnings only).
- Production build gate:
  - `./docker/build_prod_images.sh` => pass; backend/frontend images built and pushed for `linux/amd64,linux/arm64` with tag `7365d66`.
- Chrome MCP E2E on repo dev server (`3100`):
  - Opened `/episodes/136/workspace`.
  - Verified workspace loaded normally and `当前剧本` section rendered (no runtime import regression).

## Next Steps

- Keep API import boundaries stable under current lint rules.
- Continue large-file refactor work (e.g., storyboard page decomposition).

## Linked Commits

- refactor(frontend): ban deep api alias imports
