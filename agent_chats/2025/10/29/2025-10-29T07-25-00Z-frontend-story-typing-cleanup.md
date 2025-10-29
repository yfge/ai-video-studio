---
id: 2025-10-29T07-25-00Z-frontend-story-typing-cleanup
date: 2025-10-29T07:25:00Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [frontend, typescript]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/app/stories/page.tsx
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
summary: "Replaced `any` usage across story/episode flows and aligned API typings with new generation payloads"
---

## User Prompt
检查tasks.md 规划下一步的工作；Feature“叙事结构与数据模型对齐” 类型清理；修复 lint `no-explicit-any` 等告警。

## Goals
- Remove lingering `any` casts from stories/episodes/script pages while keeping async flows functional.
- Extend API typings to cover optional generation parameters referenced by the UI.
- Ensure storyboard and script views operate on typed data structures instead of `any`.

## Changes
- Expanded `EpisodeGenerationRequest`, `ScriptGenerationRequest`, and storyboard payloads in `ai-pic-frontend/src/utils/api.ts`.
- Updated stories/episodes/script pages to use typed payload builders, `useCallback` hooks, and modal confirmations without `as any`.
- Cleaned storyboard page state/types to rely on exported API interfaces rather than local `any` definitions.

## Validation
- npm run lint

## Next Steps
- Convert remaining admin/virtual IP views away from confirm dialogs and raw `<img>` tags.
- Consider aligning TypeScript interfaces in legacy modals with shared API types to satisfy `tsc`.

## Linked Commits
N/A
