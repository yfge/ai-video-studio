---
id: 2026-01-30T04-07-56Z-video-duration-trim
date: 2026-01-30T04:07:56Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, video, storyboard]
related_paths:
  - ai-pic-backend/app/services/video/video_generation_service.py
  - ai-pic-backend/app/services/video/video_task_generation_metadata.py
  - ai-pic-backend/app/services/video/video_task_polling_service.py
  - ai-pic-backend/app/services/video/video_task_polling_parent_task.py
  - ai-pic-backend/app/services/video/video_task_submission_helpers.py
  - ai-pic-backend/app/services/video/video_task_submission_service.py
  - ai-pic-backend/app/services/video/video_task_utils.py
  - ai-pic-backend/app/services/video/video_trim.py
  - ai-pic-backend/app/services/video/video_upload_pipeline.py
  - ai-pic-backend/app/services/video/video_upload_utils.py
  - ai-pic-backend/tests/unit/services/video/test_video_upload_pipeline.py
  - tasks.md
summary: "Persist storyboard target vs provider durations for video tasks and trim provider videos to match the storyboard timeline."
---

## User Prompt

现在的问题在于，视频生成模型可能能提供 6/8 秒的视频，不同视频模型的时长有区别，但是分镜可能会生成时间过长的分镜帧。这种情况怎么解决比较好？

## Goals

- Persist both storyboard target duration and provider duration for each generated clip.
- If provider duration exceeds target duration, trim the provider clip and upload both versions to OSS.
- Keep the storyboard frame aligned to the target duration (timeline truth).

## Changes

- Video task submission now stores `target_duration_seconds` and `provider_duration_seconds` in `video_generation_tasks.parameters` and `generation_metadata`.
- Video polling success path passes the stored target duration into the video processing pipeline.
- Refactor: extracted parent Task status refresh into a helper to keep the polling service within the repo file-size limit.
- Added an upload/trim pipeline:
  - Downloads/decodes the provider video, uploads the untrimmed version to OSS.
  - Uses ffmpeg to trim to `target_duration_seconds`, uploads the trimmed version to OSS.
  - Stores both `untrimmed_video_url` and final `video_url` in task result JSON.
- Added unit test for the upload/trim pipeline.
- Updated `tasks.md` to mark Phase 1 (submission metadata + trim + Docker validation) complete.

## Validation

- `docker exec ai-video-backend sh -lc 'cd /app/ai-pic-backend && pytest tests/unit/services/video -q'`
- Docker E2E (API):
  - `POST /api/v1/scripts/117/storyboard/generate-video` with `model=google:veo-3.1-generate-preview`, `duration=5`, frame 0 → Task `5894` completed
  - Final video URL duration via `ffprobe` ~= 5.08s
  - DB check: `video_generation_tasks.result.untrimmed_video_url` kept the ~6s OSS URL, `result.video_url` is the trimmed ~5s OSS URL
- `./docker/build_prod_images.sh` (tag=611e3fd)

## Next Steps

- Implement Phase 1 remaining: capabilities registry (provider/model/resolution) to avoid hardcoding and to produce clearer `needs_split` errors when target > max.
- Phase 2: auto-split long (>max) storyboard segments on beat boundaries and preserve linkage for UI/auditing.

## Linked Commits

- fix(backend): trim storyboard videos to target duration
