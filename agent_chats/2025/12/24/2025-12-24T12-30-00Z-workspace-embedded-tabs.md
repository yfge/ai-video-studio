---
id: 2025-12-24T12-30-00Z-workspace-embedded-tabs
date: 2025-12-24T12:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, workspace, refactor, embedding]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceScriptTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeWorkflowSteps.tsx
  - ai-pic-frontend/src/components/features/episode/index.ts
  - ai-pic-frontend/src/components/features/index.ts
summary: "Embed full script and timeline content directly in workspace tabs"
---

## User Prompt

User requested: "http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=script 能不能直接把查看完整剧本在这里进行合并？ 还有时间轴和分镜也是一样"

Translation: Can you merge the full script content directly here? Same for timeline and storyboard.

## Goals

1. Embed full script content (ScriptOverviewTab + ScriptScenesTab) in the Script tab
2. Embed full timeline content (AudioTimelineSection) in the Timeline tab
3. Keep storyboard as placeholder with link (3283-line page needs refactoring first)
4. Maintain the unified workspace workflow pattern

## Changes

### New Files Created

1. **`ai-pic-frontend/src/components/features/episode/WorkspaceScriptTabContent.tsx`** (~240 lines)
   - Wrapper component that loads script structure data
   - Renders sub-tabs: "概览" (Overview) and "场景" (Scenes)
   - Uses `ScriptOverviewTab` and `ScriptScenesTab` components
   - Loads normalized scenes, beats, and shots
   - Handles scene navigation and structure editing

2. **`ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx`** (~185 lines)
   - Wrapper component for `AudioTimelineSection`
   - Includes action handlers for:
     - Generate dialogue audio
     - Generate audio timeline
     - Generate storyboard from timeline
   - Passes all necessary props from `useEpisodeDetail`

### Modified Files

3. **`ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx`**
   - Extended `useEpisodeDetail` usage to include timeline state
   - Replaced placeholder `ScriptTabContent` with `WorkspaceScriptTabContent`
   - Replaced placeholder `TimelineTabContent` with `WorkspaceTimelineTabContent`
   - Removed old placeholder components (ScriptTabContent, TimelineTabContent)
   - Kept StoryboardTabContent as placeholder

4. **`ai-pic-frontend/src/components/features/episode/EpisodeWorkflowSteps.tsx`**
   - Exported `WorkflowStep` interface for external use

5. **`ai-pic-frontend/src/components/features/episode/index.ts`**
   - Added exports for new components and types

6. **`ai-pic-frontend/src/components/features/index.ts`**
   - Added exports for new workspace components

## Validation

Browser verification via Chrome DevTools MCP:

1. **Script Tab** (`?tab=script`):
   - Sub-tabs working: 概览/场景
   - Scene navigation with 4 scenes
   - Scene details: location, time, dialogue, stage directions
   - Structured info: 9 beats, 1 shot for scene 1
   - Edit structure button available

2. **Timeline Tab** (`?tab=timeline`):
   - Full AudioTimelineSection embedded
   - Script selector working
   - Timeline info: 50 beats, version 1
   - Episode audio playback available
   - Scene dialogue audio (4/4 scenes)
   - Timeline visualization with beats and frames
   - Generation buttons functional

3. **Storyboard Tab** (`?tab=storyboard`):
   - Placeholder with "进入分镜管理" link
   - Shows "分镜已生成" status

4. Lint validation: `npm run lint` passes with no errors

## Next Steps

1. Refactor the 3283-line storyboard page (Phase 3 of plan) to enable embedding
2. Consider adding script generation form to Script tab when no script exists
3. Add URL redirect from old episode pages to workspace

## Linked Commits

- a0cc47f feat(frontend): embed script and timeline content in workspace tabs
