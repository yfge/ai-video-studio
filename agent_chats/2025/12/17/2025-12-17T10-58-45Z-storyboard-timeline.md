---
id: 2025-12-17T10-58-45Z-storyboard-timeline
date: 2025-12-17T10:58:45Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, timeline, storyboard]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Embed reusable timeline visualization into storyboard page to show beats vs frames per scene."
---

## User Prompt
http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/storyboard 没有用新的时间轴组件

## Goals
- Use the new timeline component on the storyboard page to visualize episode beats and frame windows for the selected scene.

## Changes
- Imported the shared `Timeline` component and mapped timeline beats + storyboard frames (with start/end_ms) into tracks.
- Added timeline visualization inside the “场景时间轴对齐” card; falls back with a placeholder when no timing data.

## Validation
- `npm run lint` (frontend) — pass.
- UI not fully verified yet (login/scene data required), but build is clean and component wired.

## Next Steps
- After login and with beats/frame start/end_ms present, recheck the storyboard page to ensure the timeline renders and aligns with the counts shown above.

## Linked Commits
- (pending)
