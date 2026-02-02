---
id: 2026-02-02T09-42-12Z-fix-frontend-story-readiness-hook-api-import
date: 2026-02-02T09:42:12Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, build]
related_paths:
  - ai-pic-frontend/src/hooks/useStoryReadiness.ts
summary: "Fix Next.js build by using modular storyAPI endpoints in useStoryReadiness"
---

## User Prompt

commit and push

## Goals

- Unblock `./docker/build_prod_images.sh` by fixing a TypeScript type mismatch in the story readiness hook.

## Changes

- Switched `useStoryReadiness` to import `storyAPI` from `@/utils/api/endpoints` (new modular API layer) to match the typed `ReadinessResult` response.

## Validation

- `./docker/build_prod_images.sh` previously failed at `setReadiness(result.data)` due to `{}` typing; rerun after committing.

## Next Steps

- Audit other hooks/components that import from `@/utils/api` (legacy) while using `@/utils/api/types/*` (modular) to avoid similar mismatches.

## Linked Commits

- pending
