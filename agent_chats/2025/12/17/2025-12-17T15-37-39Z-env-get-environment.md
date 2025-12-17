---
id: 2025-12-17T15-37-39Z-env-get-environment
date: 2025-12-17T15:37:39Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, bugfix]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
summary: "Export getEnvironment in storyStructureAPI to fix build error"
---

## User Prompt

Build failed: Type error at environments detail page because `storyStructureAPI.getEnvironment` was missing.

## Goals

- Expose the existing `getEnvironment` client method through `storyStructureAPI` so the environments detail page compiles.

## Changes

- Added `getEnvironment` binding to `storyStructureAPI` export in `src/utils/api.ts`.

## Validation

- `npm run lint` ✅

## Next Steps

- Re-run Next.js build; proceed to doc updates after this fix.

## Linked Commits

- TBC: export getEnvironment
