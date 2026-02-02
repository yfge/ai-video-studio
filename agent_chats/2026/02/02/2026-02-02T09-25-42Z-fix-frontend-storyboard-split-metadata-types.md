---
id: 2026-02-02T09-25-42Z-fix-frontend-storyboard-split-metadata-types
date: 2026-02-02T09:25:42Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, build]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Fix Next.js build type error when comparing storyboard split metadata"
---

## User Prompt

commit and push

## Goals

- Unblock `./docker/build_prod_images.sh` by fixing a TypeScript error in the storyboard page.

## Changes

- Coerced `fr.total_splits` / `fr.split_index` via `parseNumber()` before numeric comparisons and rendering.

## Validation

- `./docker/build_prod_images.sh` previously failed at `fr.total_splits > 1`; rerun after committing (script tags/pushes by git SHA).

## Next Steps

- Consider typing `split_index` / `total_splits` on `StoryboardFrame` in `ai-pic-frontend/src/utils/api.ts` to avoid repeated coercion sites.

## Linked Commits

- pending
