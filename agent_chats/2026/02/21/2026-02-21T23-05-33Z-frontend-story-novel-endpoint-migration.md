---
id: 2026-02-21T23-05-33Z-frontend-story-novel-endpoint-migration
date: 2026-02-21T23:05:33Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api, migration, "[refactor]"]
related_paths:
  - ai-pic-frontend/src/utils/api/endpoints/story-novel.endpoints.ts
  - ai-pic-frontend/src/utils/api/types/story-novel.types.ts
  - ai-pic-frontend/src/utils/api/endpoints/index.ts
  - ai-pic-frontend/src/utils/api/types/index.ts
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelExportSection.tsx
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelExportsHistory.tsx
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelPreviewButton.tsx
  - ai-pic-frontend/src/utils/storyNovelApi.ts
  - tasks.md
summary: "Migrated story novel export utilities into split API endpoints/types modules and removed legacy utility file."
---

## User Prompt

继续

## Goals

- Continue frontend API modularization after legacy import cleanup.
- Eliminate `src/utils/storyNovelApi.ts` special-path utility and move it into `src/utils/api/endpoints/*` and `src/utils/api/types/*`.
- Keep task board and validation evidence synchronized.

## Changes

- Added `ai-pic-frontend/src/utils/api/endpoints/story-novel.endpoints.ts`:
  - `generateStoryZhihuNovelAsync`
  - `listStoryNovelExports`
  - `downloadStoryNovel`
  - `fetchStoryNovelText`
  - `storyNovelAPI` namespace export
- Added `ai-pic-frontend/src/utils/api/types/story-novel.types.ts`:
  - `StoryNovelExportRequest`
  - `StoryNovelExportSummary`
  - `StoryNovelDownloadResult`
  - `StoryNovelTextResult`
- Updated barrel exports:
  - `ai-pic-frontend/src/utils/api/endpoints/index.ts`
  - `ai-pic-frontend/src/utils/api/types/index.ts`
- Migrated story detail UI imports from legacy util to split modules:
  - `StoryNovelExportSection.tsx`
  - `StoryNovelExportsHistory.tsx`
  - `StoryNovelPreviewButton.tsx`
- Deleted legacy file `ai-pic-frontend/src/utils/storyNovelApi.ts`.
- Updated `tasks.md` frontend migration line with explicit note that story novel API migration is completed in split endpoints.

## Validation

- `cd ai-pic-frontend && npm run lint` => pass (warnings only).
- `pre-commit run --files ...` => pass (after prettier auto-format on changed files).
- `./docker/build_prod_images.sh` => pass; backend/frontend images built and pushed for `linux/amd64,linux/arm64` with tag `9e8b097`.
- Chrome MCP E2E (on current repo dev server at `http://127.0.0.1:3100`):
  - Opened `/login`, logged in with `geyunfei / Gyf@845261`.
  - Opened `/stories`.
  - Entered a story detail page (`/stories/be3f0a9a256e430b8e3ce24a8022da1f`).
  - Verified “导出知乎体小说” section rendered and “历史导出/刷新列表” interaction executed without runtime breakage.

## Next Steps

- Continue decomposing oversized frontend pages/components toward AGENTS size targets.
- Optionally fold story novel endpoints into a `story/` submodule tree for stricter domain grouping consistency.

## Linked Commits

- refactor(frontend): migrate story novel api module
