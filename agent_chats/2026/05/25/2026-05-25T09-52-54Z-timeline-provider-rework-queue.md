---
id: 2026-05-25T09-52-54Z-timeline-provider-rework-queue
date: "2026-05-25T09:52:54Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, timeline, media-assets, rework]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/timelines.py
  - ai-pic-backend/app/schemas/timeline.py
  - ai-pic-backend/app/services/timeline_clip_video_rework_queue_service.py
  - ai-pic-backend/app/services/timeline_clip_video_rework_submission.py
  - ai-pic-backend/app/services/video/video_task_polling_service.py
  - ai-pic-backend/app/services/video/video_task_timeline_rework_updater.py
  - ai-pic-backend/tests/test_timeline_clip_video_rework_api.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Queue provider-backed Timeline clip video rework"
---

## User Prompt

- “按项目规范，依次完成对应计划，保证原子性提交”
- “connit 然后继续”
- “使用你的内置浏览器”

## Goals

- Continue the Timeline main-chain readiness plan with one atomic backend slice.
- Add provider-backed video rework queueing for a selected stable Timeline `clip_id`.
- Persist successful provider video task output as clip replacement lineage without changing the stable `clip_id`.
- Keep render/export automatic requeueing and operator UI provider controls out of this commit.

## Changes

- Added `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/rework/video`.
- Added `TimelineClipVideoReworkTaskRequest` and `TimelineClipVideoReworkTaskResponse`.
- Added a queue service that validates timeline access, optimistic version lock, and video clip identity before creating a parent `VIDEO_GENERATION` task.
- Added a Celery dispatch/worker path for Timeline clip video rework provider submissions.
- Added provider submission persistence that stores `timeline_rework` context on `VideoGenerationTask.parameters`.
- Updated video task polling so successful `timeline_rework` outputs create `provider_rework` `timeline_clip_assets` with `replacement_of_id` lineage.
- Added API/service tests for queueing, non-video clip rejection, and successful provider output lineage.
- Updated `tasks.md` and active execution plans to mark backend provider-backed rework queueing and success lineage complete while leaving operator UI provider entry and render queue orchestration pending.

## Validation

- `cd ai-pic-backend && pytest tests/test_timeline_clip_rework_api.py tests/test_timeline_clip_video_rework_api.py tests/test_timeline_api.py tests/test_timeline_import_service.py tests/test_timeline_lifecycle_api.py tests/test_timeline_spec_validation.py tests/unit/services/render/test_timeline_render_service.py tests/unit/services/video/test_video_task_polling_service.py tests/unit/services/video/test_video_task_generation_metadata.py -q`
  - Result: passed, 29 tests, 1 skipped.
- Browser validation was not run for this commit because this slice changes backend API/task orchestration and docs only. Per the user request, the next operator/UI slice should use the Codex built-in Browser rather than Chrome.

## Next Steps

- Wire Timeline operator rework controls to the new provider-backed rework task API.
- After provider rework success, enqueue the relevant locked Timeline render/export path.
- Continue legacy stability cleanup only after the main rework/render boundary is covered.

## Linked Commits

- Pending
