---
id: 2026-01-30T03-34-07Z-video-duration-ceil
date: 2026-01-30T03:34:07Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, video, providers]
related_paths:
  - ai-pic-backend/app/services/video/video_duration.py
  - ai-pic-backend/app/services/video/video_task_utils.py
  - ai-pic-backend/app/services/providers/google_provider/video_helpers.py
  - ai-pic-backend/app/services/providers/keling_provider/video.py
  - ai-pic-backend/app/services/providers/keling_provider/video_tasks.py
  - ai-pic-backend/app/services/providers/minimax_provider/video.py
  - ai-pic-backend/app/services/providers/minimax_provider/video_tasks.py
  - ai-pic-backend/tests/unit/services/video/test_video_duration.py
  - tasks.md
summary: "Switch video duration normalization to ceil-to-allowed durations for providers with discrete duration options (Veo/Keling/MiniMax)."
---

## User Prompt

现在的问题在于，视频生成模型可能能提供 6/8 秒的视频，不同视频模型的时长有区别，但是分镜可能会生成时间过长的分镜帧。这种情况怎么解决比较好？

## Goals

- Avoid producing provider clips shorter than the storyboard target duration when providers only allow discrete durations (e.g., 4/6/8s).
- Make the rule reusable across providers and covered by unit tests.
- Keep changes small and auditable.

## Changes

- Added `app/services/video/video_duration.py` with a `resolve_duration_ceil()` helper (ceil-to-allowed strategy + needs_split flag).
- Updated Google Veo duration resolution to use ceil-to-allowed (prevents 5s resolving down to 4s).
- Updated Keling and MiniMax async/sync video submission paths to coerce duration via ceil-to-allowed discrete options.
- Updated video task duration coercion to use `ceil()` instead of `round()` to avoid requesting a shorter provider clip than the storyboard target.
- Added unit tests covering the ceil rule and Google Veo tie-break regression; marked the corresponding `tasks.md` checkbox complete.

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/video -q`
- `./docker/build_prod_images.sh` (tag=1dc731f)

## Next Steps

- Implement Phase 1 remaining items: persist `target_duration_seconds` vs `provider_duration_seconds` and trim provider videos back to target duration on success.
- Add a clear blocking error (or auto-splitting mode) for frames whose target duration exceeds provider max (`needs_split=true`).

## Linked Commits

- fix(backend): ceil video durations to supported options
