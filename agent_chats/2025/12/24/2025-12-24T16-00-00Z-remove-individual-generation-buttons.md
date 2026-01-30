---
id: 2025-12-24T16-00-00Z-remove-individual-generation-buttons
date: 2025-12-24T16:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, timeline-tab, ui-simplification]
related_paths:
  - ai-pic-frontend/src/components/features/episode/AudioTimelineSection.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
summary: "Simplify timeline tab UI: remove buttons/options, keep only model selector"
---

## User Prompt

User requested two changes:

1. "生成对白音轨 生成时间轴 生成分镜帧占位 这个就都去掉吧" - Remove three individual generation buttons
2. "这些也没有用了吧：覆盖对白音轨/覆盖时间轴/覆盖分镜/pause阈值/时间轴模型/对白音轨任务/时间轴任务/分镜占位任务... 只保留模型和温度就可以了" - Remove unused options, keep only model selector

## Goals

1. Remove three individual generation buttons from timeline tab
2. Remove three overwrite checkboxes (覆盖对白音轨, 覆盖时间轴, 覆盖分镜)
3. Remove pause threshold input
4. Remove task status displays (对白音轨任务, 时间轴任务, 分镜占位任务)
5. Keep only "一键生成全部" button and model selector

## Changes

### Frontend

1. **`ai-pic-frontend/src/components/features/episode/AudioTimelineSection.tsx`**

   - Simplified interface: removed task props, busy states, overwrite options, pause threshold
   - Kept only: scripts, selectedScriptId/Script, audioTimeline/storyboard data, normalizedScenes, pipelineBusy, timingModel, pipeline actions
   - Removed Task type import
   - Removed `taskStatusText` function
   - Removed three overwrite checkboxes and pause threshold input
   - Removed three task status cards, keeping only pipeline task card
   - Renamed "时间轴模型" label to just "模型"
   - Fixed button disabled state to only use `pipelineBusy`

2. **`ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx`**

   - Simplified interface significantly (removed ~40 lines of props)
   - Removed handler functions for individual generation
   - Updated API call to use sensible defaults (overwrite=true, pause=1.5)
   - Simplified AudioTimelineSection props

3. **`ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx`**
   - Simplified state destructuring from useEpisodeDetail hook
   - Removed unused state variables (overwrite options, task IDs, busy states, etc.)
   - Simplified WorkspaceTimelineTabContent props

## Validation

1. Frontend lint: `npm run lint` - passes with only pre-existing warnings
2. Browser verification via Chrome DevTools MCP:
   - Navigated to `/episodes/b199d0900c74487c84ba432fb5d4a932/workspace?tab=timeline`
   - Verified UI shows only:
     - "一键生成全部" button
     - "模型" dropdown selector
   - Removed items verified absent:
     - Three overwrite checkboxes
     - Pause threshold input
     - Three task status cards

## Next Steps

1. Consider adding temperature input if needed
2. Consider cleaning up unused state in useEpisodeDetail hook

## Linked Commits

- 2be71f8 feat(frontend): simplify timeline tab UI to model-only options
