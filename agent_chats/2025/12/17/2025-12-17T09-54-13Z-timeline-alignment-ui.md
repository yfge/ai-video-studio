---
id: 2025-12-17T09-54-13Z-timeline-alignment-ui
date: 2025-12-17T09:54:13Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, timeline]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Align storyboard UI with dialogue beats/timeline by surfacing scene beat counts and duration windows."
---

## User Prompt
整体优化时间轴管理功能，使其在一个场景内达到到一致（对白-beats-分镜）

## Goals
- Surface scene-level beat data and audio timeline alignment in storyboard UI.
- Help operators see mismatches between dialogue beats, scene_beats, and storyboard frame durations.

## Changes
- Added SceneBeat typing and API client support to fetch beats for a scene.
- Storyboard page now loads scene beats, parses episode audio timeline beats, and computes scene-level windows/durations.
- Introduced a scene timeline alignment panel showing counts, duration windows, and warnings when beats/frames diverge or timeline is missing.

## Validation
- `npm run lint` (ai-pic-frontend) — pass.
- Manual UI check (Chrome via MCP): login as `geyunfei` → open `http://localhost:8089/episodes/8/storyboard`; new “场景时间轴对齐” section renders counts/warnings, showing beats=0 vs frames=7 when timeline absent.

## Next Steps
- Generate episode audio timeline and regenerate storyboard to confirm beats/frame counts align and windows populate; hook scene_beats offsets once available.

## Linked Commits
- (pending)
