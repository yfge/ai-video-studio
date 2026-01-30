---
id: 2025-12-24T15-00-00Z-workspace-storyboard-embed
date: 2025-12-24T15:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, workspace, storyboard, no-navigation]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/index.ts
summary: "Embed storyboard frame grid directly in workspace, allowing image generation and viewing without navigation"
---

## User Prompt

User reported: "分镜没有移过来" (Storyboard hasn't been moved over)

Following up on the previous request that ALL operations for an episode must be completed in the workspace page.

## Goals

1. Create a new `WorkspaceStoryboardTabContent` component
2. Display storyboard frames in a grid with thumbnails
3. Allow image generation for selected frames
4. Provide link to full storyboard editor for advanced features

## Changes

### Frontend

1. **`ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx`** (new)

   - Created new component with ~275 lines
   - Fetches storyboard data using `scriptAPI.getStoryboard()`
   - Displays frame grid with:
     - Thumbnail images (or placeholder icons)
     - Frame numbers
     - Time ranges (formatted as MM:SS)
     - Description text (truncated)
     - Video indicator for frames with video
   - Selection functionality for batch image generation
   - Stats header: total frames, frames with images, frames pending
   - "选择全部" button to select all frames without images
   - "生成图像" button to generate images for selected frames
   - "打开完整编辑器 →" button to access full storyboard page

2. **`ai-pic-frontend/src/components/features/episode/index.ts`**

   - Added export for `WorkspaceStoryboardTabContent`

3. **`ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx`**
   - Added import for `WorkspaceStoryboardTabContent`
   - Replaced inline `StoryboardTabContent` placeholder with new component
   - Removed old inline component definition (~40 lines)

## Validation

1. Frontend lint: `npm run lint` - only warnings (unused vars, img element), no errors
2. Browser verification via Chrome DevTools MCP:
   - Navigated to `/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=storyboard`
   - Stats header visible: "共 24 帧 · 2 帧有图像 · 22 帧待生成"
   - Frame grid displays all 24 frames
   - Frames 1-2 show generated images
   - Frame 1 shows "视频" indicator
   - All frames show time ranges and descriptions
   - "选择全部" and "打开完整编辑器 →" buttons visible

## Next Steps

1. Add frame selection and batch image generation testing
2. Consider adding video generation directly from workspace
3. Add script selector for episodes with multiple scripts

## Linked Commits

- (pending commit)
