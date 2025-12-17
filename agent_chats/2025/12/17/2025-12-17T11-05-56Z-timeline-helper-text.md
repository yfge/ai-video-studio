---
id: 2025-12-17T11-05-56Z-timeline-helper-text
date: 2025-12-17T11:05:56Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Clarify frame count helper text to show both timeline beats and current storyboard frame count."
---

## User Prompt
时间轴已生成：当前场景预计帧数 18（由 beats 决定） 这个应该是由分镜帧决定 吧？

## Goals
- Make helper text reflect both timeline-beat-derived frame count and current storyboard frame count.

## Changes
- Updated helper text under frame count input to show beat-derived estimate and current storyboard frame count simultaneously.

## Validation
- `npm run lint` (frontend) — pass.

## Next Steps
- If desired, adjust backend to align frames to beats automatically so these numbers match after sync.

## Linked Commits
- (pending)
