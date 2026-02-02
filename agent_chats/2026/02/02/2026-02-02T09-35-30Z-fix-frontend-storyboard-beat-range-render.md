---
id: 2026-02-02T09-35-30Z-fix-frontend-storyboard-beat-range-render
date: 2026-02-02T09:35:30Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, build]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Fix Next.js build error by guarding beat_range rendering for split frames"
---

## User Prompt

commit and push

## Goals

- Unblock `./docker/build_prod_images.sh` by fixing a TypeScript `ReactNode` error in storyboard frame rendering.

## Changes

- Parsed `fr.beat_range` with `parseMs()` and rendered the split-frame beat-range block via a ternary (no `unknown && JSX`).
- Guarded `parent_frame_id.slice(...)` with a string type check.

## Validation

- `./docker/build_prod_images.sh` previously failed at `isSplitFrame && fr.beat_range && (...)`; rerun after committing (script tags/pushes by git SHA).

## Next Steps

- Consider typing `beat_range` / `parent_frame_id` on `StoryboardFrame` to reduce runtime coercion in the storyboard page.

## Linked Commits

- pending
