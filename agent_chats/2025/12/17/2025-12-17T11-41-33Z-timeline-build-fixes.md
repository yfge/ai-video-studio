---
id: 2025-12-17T11-41-33Z-timeline-build-fixes
date: 2025-12-17T11:41:33Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, timeline]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Hardened timeline item typing and storyboard page null guards to restore builds"
---

## User Prompt

Investigate script/episode timeline errors causing white screen and build failures.

## Goals

- Fix type errors introduced by the reusable timeline integration so Next.js build succeeds.
- Ensure storyboard page null handling does not crash when episode is missing.
- Verify the script detail page renders after the fix.

## Changes

- Made timeline item mapping on episode detail page strongly typed (map generics + record parsing helpers) to satisfy TimelineTrack item expectations.
- Guarded storyboard beats state updates and episode-not-found redirect button to use safe defaults.

## Validation

- `npm run build` (ai-pic-frontend): success.
- `npm run lint` (ai-pic-frontend): success.
- Browser check via DevTools: reloaded `http://localhost:8089/scripts/b40daa0d5f9848e0ae6c90bc02d7bb45`, page renders normally (only HMR websocket warning).

## Next Steps

- After deploy/restart, click scene cards on the script detail page to confirm no blank screen; optionally check storyboard page loads beats/frames timeline without console errors.

## Linked Commits

- Pending
