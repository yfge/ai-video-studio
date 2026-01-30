---
id: 2025-12-24T15-30-00Z-story-page-single-entry
date: 2025-12-24T15:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, story-page, navigation, ux-improvement]
related_paths:
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
  - ai-pic-frontend/src/components/features/story-detail/EpisodeListSection.tsx
  - ai-pic-frontend/src/hooks/useStoryDetail.ts
summary: "Simplify episode cards on story page to single workspace entry point"
---

## User Prompt

User reported: "http://localhost:8089/stories/6d7c528b4b064a5f99689f095f5bef90 这个页面里一个剧集就不要有多个入口了"

Translation: On this story page, each episode should not have multiple entry points.

## Goals

1. Remove multiple navigation buttons from episode cards
2. Replace with single "进入工作台 →" button
3. Simplify the component interface by removing unused navigation handlers

## Changes

### Frontend

1. **`ai-pic-frontend/src/components/features/story-detail/EpisodeListSection.tsx`**

   - Removed `onNavigateToStoryboard` and `onNavigateToScript` from `EpisodeListSectionProps`
   - Updated `EpisodeCardProps` to use single `onNavigateToWorkspace` prop
   - Replaced `ScriptsPreview` component with simpler `ScriptsInfo` that only displays script titles (no navigation buttons)
   - Moved the navigation button from header to bottom as a full-width "进入工作台 →" button
   - Removed the top-right "查看" button from episode card header
   - Removed the "分镜管理" button from scripts section

2. **`ai-pic-frontend/src/app/stories/[id]/page.tsx`**
   - Removed unused `navigateToStoryboard` and `navigateToScript` from destructured state
   - Updated `EpisodeListSection` component usage to only pass `onNavigateToEpisode`

## Validation

1. Frontend lint: `npm run lint` - passes with only warnings (same as before)
2. Browser verification via Chrome DevTools MCP:
   - Navigated to `/stories/6d7c528b4b064a5f99689f095f5bef90`
   - Reloaded page to get latest changes
   - Verified each episode card now shows only ONE button: "进入工作台 →"
   - Clicked button on Episode 1
   - Successfully navigated to `/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace`
   - Workspace page loaded correctly with all three tabs (剧本, 时间轴, 分镜)

## Next Steps

1. Consider adding episode status indicators on the story page cards
2. Consider adding quick action buttons on the workspace page for common operations

## Linked Commits

- 62ceb3d feat(frontend): simplify story page episode cards to single workspace entry
