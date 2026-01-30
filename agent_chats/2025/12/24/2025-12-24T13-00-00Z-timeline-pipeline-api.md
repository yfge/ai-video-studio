---
id: 2025-12-24T13-00-00Z-timeline-pipeline-api
date: 2025-12-24T13:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, frontend, api, celery, timeline]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-frontend/src/components/features/episode/AudioTimelineSection.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx
  - ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts
summary: "Add one-click timeline pipeline API combining dialogue audio, timeline, and storyboard generation"
---

## User Prompt

User requested: "生成对白音轨 生成时间轴 生成分镜帧占位 这三个流程是不是可以合并成一个？"

Translation: Can these three steps (dialogue audio, timeline, storyboard slots) be combined into one?

User selected "后端流水线API（推荐）" approach.

## Goals

1. Create a backend pipeline API that executes all three steps sequentially
2. Add Celery task for async execution
3. Add frontend API method
4. Update workspace UI with "一键生成全部" button

## Changes

### Backend

1. **`ai-pic-backend/app/services/task_worker.py`**

   - Added `timeline_pipeline_generate_task` Celery task
   - Calls `_process_timeline_pipeline_task` for execution

2. **`ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`**
   - Added `TimelinePipelineGenerateRequest` schema with all options:
     - `tts_model`: TTS model selection
     - `timing_model`: LLM model for timing calculation
     - `overwrite_audio`: Overwrite existing scene audio
     - `overwrite_timeline`: Overwrite existing timeline
     - `overwrite_storyboard`: Overwrite existing storyboard slots
     - `min_pause_seconds`: Minimum pause threshold for storyboard
   - Added `POST /{script_id}/timeline-pipeline/generate-async` endpoint
   - Added `_process_timeline_pipeline_task` function that:
     - Step 1/3: Generates dialogue audio for all scenes
     - Step 2/3: Generates episode audio timeline
     - Step 3/3: Generates storyboard frame slots from timeline

### Frontend

3. **`ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts`**

   - Added `generateTimelinePipelineAsync` API method
   - Exported in `scriptAPI` namespace

4. **`ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx`**

   - Added `pipelineBusy` and `pipelineTaskId` state
   - Added `handleGenerateTimelinePipeline` handler
   - Passes pipeline props to `AudioTimelineSection`

5. **`ai-pic-frontend/src/components/features/episode/AudioTimelineSection.tsx`**
   - Added `onGenerateTimelinePipeline`, `pipelineBusy`, `pipelineTaskId` props
   - Added gradient "一键生成全部" button before individual buttons
   - Added pipeline task status display in task grid
   - Individual buttons disabled during pipeline execution

## Validation

1. Frontend lint: `npm run lint` passes with no errors
2. Browser verification via Chrome DevTools MCP:
   - Timeline tab at `/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=timeline`
   - "一键生成全部" button visible with gradient styling
   - Separator "|" between pipeline button and individual buttons
   - All existing functionality preserved

## Next Steps

1. Test the actual pipeline execution with a fresh script
2. Add task progress polling to show real-time status
3. Consider adding task progress detail to the pipeline status card

## Linked Commits

- ebaa189 feat(timeline): add one-click pipeline for timeline generation
