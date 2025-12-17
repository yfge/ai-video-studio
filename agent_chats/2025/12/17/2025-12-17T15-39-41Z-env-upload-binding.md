---
id: 2025-12-17T15-39-41Z-env-upload-binding
date: 2025-12-17T15:39:41Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, bugfix]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
summary: "Bind uploadEnvironmentImage on storyStructureAPI to fix build"
---

## User Prompt

Build failure: `storyStructureAPI.uploadEnvironmentImage` missing in build.

## Goals

- Expose the upload helper in `storyStructureAPI` so the environment detail page compiles.

## Changes

- Added `uploadEnvironmentImage` binding to `storyStructureAPI` export in `src/utils/api.ts`.

## Validation

- `npm run lint` ✅

## Next Steps

- Re-run production build (`./build_prod_images.sh`) per repo rule.

## Linked Commits

- TBC: bind environment upload helper
