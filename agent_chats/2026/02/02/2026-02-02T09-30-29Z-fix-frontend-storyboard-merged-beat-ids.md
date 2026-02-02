---
id: 2026-02-02T09-30-29Z-fix-frontend-storyboard-merged-beat-ids
date: 2026-02-02T09:30:29Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, build]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Fix Next.js build type error when rendering merged beat metadata in storyboard frames"
---

## User Prompt

commit and push

## Goals

- Unblock `./docker/build_prod_images.sh` by fixing a TypeScript error around `merged_beat_ids`.

## Changes

- Normalized `fr.merged_beat_ids` into a `string[] | null` and used that for `join()` and `length`.

## Validation

- `./docker/build_prod_images.sh` previously failed at `merged_beat_ids?.join(...)`; rerun after committing (script tags/pushes by git SHA).

## Next Steps

- Consider typing `merged_beat_ids` on `StoryboardFrame` in `ai-pic-frontend/src/utils/api.ts` to avoid repeated coercion.

## Linked Commits

- pending
