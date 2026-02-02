---
id: 2026-02-02T09-17-08Z-fix-frontend-storyboard-duration-adjustment
date: 2026-02-02T09:17:08Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, build]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Fix Next.js build type error when rendering storyboard duration adjustment meta"
---

## User Prompt

commit and push

## Goals

- Unblock the production Next.js build by fixing a TypeScript `ReactNode` error.
- Keep the change minimal and low-risk.

## Changes

- Render `storyboard.meta.duration_adjustment` via a guarded block so JSX never returns a non-ReactNode value.

## Validation

- `./docker/build_prod_images.sh` previously failed on this TypeScript error; rerun after committing (script tags/pushes by git SHA).

## Next Steps

- Consider adding a typed `duration_adjustment` field to `ai-pic-frontend/src/utils/api.ts` and refactoring the oversized storyboard page.

## Linked Commits

- pending
