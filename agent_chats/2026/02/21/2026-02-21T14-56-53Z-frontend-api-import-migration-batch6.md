---
id: 2026-02-21T14-56-53Z-frontend-api-import-migration-batch6
date: 2026-02-21T14:56:53Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api, migration, "[refactor]"]
related_paths:
  - ai-pic-frontend/src/components/features/SceneStructurePanel.tsx
  - ai-pic-frontend/src/hooks/useVirtualIPDetail.ts
  - ai-pic-frontend/src/utils/storyNovelApi.ts
  - tasks.md
summary: "Completed batch6 by removing the final legacy '@/utils/api' imports and marking the migration task complete in tasks.md."
---

## User Prompt

继续

## Goals

- Continue migration from legacy `@/utils/api` entrypoint.
- Remove the final remaining import sites that still used `apiClient`/legacy type imports.
- Keep validation and task-board status up to date.

## Changes

- `useVirtualIPDetail.ts`: removed legacy `apiClient` import and dropped the obsolete `apiClient.updateToken()` effect.
- `SceneStructurePanel.tsx`: replaced fallback `apiClient` usage with explicit `storyStructureAPI` endpoint mappings while preserving `apiOverride`.
- `storyNovelApi.ts`: replaced `apiClient.makeRequest` with `httpClient` and imported `ApiResponse` from split types.
- `tasks.md`: marked frontend migration item complete and recorded that legacy `from "@/utils/api"` imports are now zero.

## Validation

- `rg -n 'from "@/utils/api"' ai-pic-frontend/src` => no results (legacy imports cleared).
- `pre-commit run --files ...` passed (after one prettier auto-format pass on `SceneStructurePanel.tsx`).
- `./docker/build_prod_images.sh` passed; backend/frontend images built and pushed for `linux/amd64,linux/arm64` with tag `2603ff3`.
- Chrome MCP:
  - Verified `/episodes/136/storyboard` page renders while logged in (snapshot captured).
  - Additional navigation attempts later in the same run hit MCP timeout; no contradictory runtime error was observed before timeout.

## Next Steps

- Replace direct `httpClient` use in `storyNovelApi.ts` with a dedicated `story` domain endpoint module for consistency.
- Continue reducing oversized frontend files toward AGENTS size targets.

## Linked Commits

- refactor(frontend): migrate api imports batch6
