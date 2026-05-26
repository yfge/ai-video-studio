---
id: 2026-05-26T04-03-59Z-timeline-subtitle-render
date: 2026-05-26T04:03:59Z
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - timeline
  - render
  - subtitles
  - ffmpeg
related_paths:
  - ai-pic-backend/app/services/render/timeline_render_service.py
  - ai-pic-backend/app/services/render/timeline_render_subtitles.py
  - ai-pic-backend/app/services/render/timeline_render_types.py
  - ai-pic-backend/app/services/render/video_concat.py
  - ai-pic-backend/app/services/render/video_ffmpeg.py
  - ai-pic-backend/tests/unit/services/render/test_timeline_render_service.py
  - ai-pic-backend/tests/unit/services/render/test_timeline_render_rework_assets.py
  - ai-pic-backend/tests/unit/services/render/test_timeline_render_subtitles.py
  - ai-pic-backend/tests/unit/services/render/test_video_concat.py
  - docs/timeline-rendering-pipeline.md
  - tasks.md
summary: Make Timeline render consume subtitle tracks and burn subtitle cues into final video output.
---

## User Prompt

继续

## Goals

- Continue past structured Timeline dialogue/subtitle evidence into actual render consumption.
- Resolve Timeline `subtitle` track clips into render subtitle cues.
- Burn subtitle cues into final video output through ffmpeg.
- Validate with local render tests and a real system API render job after ensuring the Celery worker loaded the current code.
- Keep the remaining limitation explicit: TTS dialogue audio replacement is still separate.

## Changes

- Added `TimelineSubtitleCue` and `resolve_timeline_subtitle_cues()` for Timeline subtitle track extraction.
- Updated `TimelineRenderService` to resolve subtitle cues, pass them to the video composer, and record `subtitle_count` in render progress and success logs.
- Added `VideoSubtitleCue` plus SRT writing in `concat_video_clips()`.
- Added `burn_subtitles_ffmpeg()` to burn SRT cues into the final MP4 using ffmpeg.
- Added focused render subtitle tests for subtitle cue propagation, SRT generation, and subtitle burn invocation without pushing existing render test files over the size threshold.
- Updated the existing rework-render test double for the new `_render_to_temp_file(clips, subtitles)` signature.
- Updated active docs and `tasks.md` to replace the old "render only consumes video track" limitation with the current subtitle burn-in proof and the remaining TTS limitation.

## Validation

- `python -m py_compile ai-pic-backend/app/services/render/timeline_render_service.py ai-pic-backend/app/services/render/timeline_render_subtitles.py ai-pic-backend/app/services/render/video_concat.py ai-pic-backend/app/services/render/video_ffmpeg.py ai-pic-backend/app/services/render/timeline_render_types.py ai-pic-backend/tests/unit/services/render/test_timeline_render_service.py ai-pic-backend/tests/unit/services/render/test_video_concat.py ai-pic-backend/tests/unit/services/render/test_timeline_render_subtitles.py` -> passed.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/unit/services/render/test_timeline_render_service.py tests/unit/services/render/test_video_concat.py tests/unit/services/render/test_timeline_render_subtitles.py -q` -> passed, 16 tests, warnings only.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/unit/services/render/test_timeline_render_service.py tests/unit/services/render/test_video_concat.py tests/unit/services/render/test_timeline_render_subtitles.py tests/unit/services/render/test_timeline_render_rework_assets.py tests/scripts/test_provider_chain_regression.py tests/unit/test_deepseek_provider_v4.py tests/unit/test_model_utils.py tests/unit/services/providers/test_oai_image_provider.py tests/unit/test_volcengine_provider_video.py -q` -> passed, 38 passed, 7 skipped, warnings only.
- Initial system API smoke `provider-chain-subtitle-render-smoke-20260526T035433Z` passed but was not accepted as subtitle-render proof because the running Celery worker had not loaded the new render code; render job `22` lacked `subtitle_count`.
- Restarted `ai-video-celery-worker` and verified the worker loaded `TimelineRenderService._render_to_temp_file(self, clips, subtitles)` and source containing `subtitle_count`.
- System API rerender:
  - Command path: login, then `POST /api/v1/timelines/17/render` with `timeline_version=2`, `force_new_attempt=true`, and preset `subtitle_burn_in=true`.
  - Artifact: `artifacts/runs/subtitle-render-rerender-20260526T040220Z/subtitle_render.json`.
  - Result: render job `23` succeeded.
  - Render log: `subtitle_count=1`, `clip_count=1`, `output_asset_id=148`.
  - Worker log recorded `Burning 1 subtitle cues...`.
  - Output: `https://resource.lets-gpt.com/timeline-renders/video/20260526/040227/904c677c.mp4`.
- `ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 https://resource.lets-gpt.com/timeline-renders/video/20260526/040227/904c677c.mp4` -> `duration=4.086213`, `size=1425966`.
- Chrome DevTools MCP check failed before browser validation: `list_pages` could not connect to Chrome at `http://127.0.0.1:9222/json/version` (`HTTP Not Found`). This was not recorded as Chrome verification.
- Fallback visual evidence: extracted frame `artifacts/runs/subtitle-render-rerender-20260526T040220Z/frame_2s.png` from the output MP4 with ffmpeg; the frame shows the burned subtitle text `B-OT: Oh! A light in the dark land!`.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --all-files` -> failed on historical all-repo issues outside this change: ruff errors, black failing to parse `ai-pic-backend/app/cli/templates/migration_template.py`, backend quick gate import failure for `check_cliffhanger`, and formatting hooks touching many unrelated old files. The hook-created changes to 247 non-scope files were reversed before continuing.
- `pre-commit run --files <changed files>` -> passed.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> passed; backend and frontend images built locally without push.

## Next Steps

- Run repo docs/contracts, diff whitespace, pre-commit, and production image build before commit.
- Next quality boundary: generate or attach TTS dialogue audio from Timeline dialogue track and replace/mix it during render with real system API evidence.

## Linked Commits

Pending
