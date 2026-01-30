---
id: 2026-01-30T06-45-58Z-fix-storyboard-video-use-end-frame
date: 2026-01-30T06:45:58Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, video, bugfix]
related_paths:
  - ai-pic-backend/app/services/task_worker_storyboard_media.py
summary: "Fix storyboard video generation to honor use_end_frame option"
---

## User Prompt

- Run a full end-to-end generation for a live-action short-drama episode and keep storyboard/video continuity stable.
- Storyboard video generation should support using both start/end keyframes (when available) instead of start-frame-only.

## Goals

- Ensure `use_end_frame` set by the API request reaches the Celery worker so video submissions can include `end_image_url`.

## Changes

- Pass through `use_end_frame` from payload into the storyboard video Celery task options.
- Fix `anyio.run()` misuse in storyboard video submission (wrap kwarg call) so Celery does not crash before creating provider tasks.

## Validation

- Restarted `ai-video-celery-worker` + `ai-video-celery-beat` to load the change.
- API smoke test: `POST /api/v1/scripts/118/storyboard/generate-video` with `use_end_frame=true` succeeded in submitting a Google Veo task and created a `video_generation_tasks` row with a non-null `end_image_url`.
- `cd ai-pic-backend && pytest tests/unit/services/video -q`
- `./docker/build_prod_images.sh` (tag=781ab65)

## Next Steps

- Generate Veo videos for all storyboard frames and render final MP4s (provider-audio vs our dialogue audio).

## Linked Commits

- fix(backend): honor use_end_frame for storyboard video generation
