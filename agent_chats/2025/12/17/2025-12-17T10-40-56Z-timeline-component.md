---
id: 2025-12-17T10-40-56Z-timeline-component
date: 2025-12-17T10:40:56Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, timeline]
related_paths:
  - ai-pic-frontend/src/components/Timeline/Timeline.tsx
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
summary: "Introduced a reusable timeline component and wired episode page to visualize beats vs storyboard frame windows."
---

## User Prompt

可以 ，按这个方向推进

## Goals

- Add a reusable timeline visualization component with zoom/pan for tracks of beats/frames.
- Surface the dialogue→timeline→storyboard flow on the episode page using the new component.

## Changes

- Added `Timeline` component (`src/components/Timeline/Timeline.tsx`) supporting tracks, markers, zoom slider, ticks, and optional current-time indicator.
- Episode page now maps episode `audio_timeline.beats` and storyboard frames (with start/end_ms) into tracks and renders them beneath the audio/timeline actions.
- Kept pipeline pills; added parsing helpers and safe guards for missing data.

## Validation

- `npm run lint` (frontend) — pass.
- Manual check via Chrome/MCP: attempted `http://localhost:8089/episodes/8` after changes; page returned 500 from `/episodes/cd378417b7f143eab5bc6d063cd7f6e7` so timeline UI not visible in this environment. Needs backend/page fix to view.

## Next Steps

- Fix `/episodes/:id` 500 in dev stack so timeline renders; verify timeline tracks once data available (beats + frame start/end_ms).
- Reuse the Timeline component on the storyboard page with scene-level windowing and audio syncing.

## Linked Commits

- (pending)
