---
id: 2026-05-26T04-30-00Z-timeline-dialogue-audio-render
date: 2026-05-26T04:30:00Z
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - timeline
  - render
  - dialogue-audio
  - tts
  - provider-chain
related_paths:
  - ai-pic-backend/app/services/render/timeline_render_audio.py
  - ai-pic-backend/app/services/render/timeline_render_service.py
  - ai-pic-backend/app/services/render/timeline_render_types.py
  - ai-pic-backend/app/services/render/video_ffmpeg.py
  - scripts/harness/provider_chain_audio.py
  - scripts/harness/provider_chain_regression.py
  - scripts/harness/provider_chain_timeline.py
  - scripts/harness/provider_chain_timeline_payloads.py
  - ai-pic-backend/tests/unit/services/render/test_timeline_render_audio.py
  - ai-pic-backend/tests/scripts/test_provider_chain_regression.py
  - docs/timeline-rendering-pipeline.md
  - tasks.md
summary: Make Timeline render consume dialogue audio URLs and extend provider-chain regression with real TTS audio.
---

## User Prompt

继续

## Goals

- Continue from subtitle burn-in to actual Timeline dialogue audio replacement.
- Do not treat video prompt dialogue or subtitle text as spoken dialogue proof.
- Generate real TTS audio through the system API in the provider-chain harness.
- Patch the returned audio URL back into Timeline before render.
- Prove the render worker replaces the final audio track with Timeline dialogue audio.

## Changes

- Added `resolve_timeline_audio_track()` for Timeline render audio resolution from
  `spec.source.episode_audio` or dialogue clip `asset_ref` URL.
- Updated `TimelineRenderService` to pass resolved audio into `concat_video_clips()`
  and record `audio_source` plus `has_replaced_audio` in render logs.
- Updated ffmpeg audio replacement to pad short audio with `apad`, preserving video
  duration instead of shortening output to the TTS file length.
- Extended provider-chain regression with `/api/v1/voice/tts` MiniMax
  `speech-2.6-hd` generation before image/video generation.
- Patched provider-chain Timeline updates to attach dialogue audio to
  `source.episode_audio` and dialogue clip `asset_ref`.
- Added retry handling for transient render-job poll `ConnectionError` responses.
- Added unit coverage for Timeline audio resolution, render audio propagation, and
  provider-chain audio attachment.
- Updated active docs and `tasks.md` to record the new audio replacement proof and
  remaining production-quality boundaries.

## Validation

- `python -m py_compile ai-pic-backend/app/services/render/timeline_render_service.py ai-pic-backend/app/services/render/timeline_render_audio.py ai-pic-backend/app/services/render/timeline_render_subtitles.py ai-pic-backend/app/services/render/video_concat.py ai-pic-backend/app/services/render/video_ffmpeg.py ai-pic-backend/app/services/render/timeline_render_types.py scripts/harness/provider_chain_regression.py scripts/harness/provider_chain_audio.py scripts/harness/provider_chain_timeline.py scripts/harness/provider_chain_timeline_payloads.py ai-pic-backend/tests/unit/services/render/test_timeline_render_audio.py ai-pic-backend/tests/unit/services/render/test_timeline_render_service.py ai-pic-backend/tests/unit/services/render/test_timeline_render_subtitles.py ai-pic-backend/tests/unit/services/render/test_video_concat.py ai-pic-backend/tests/scripts/test_provider_chain_regression.py` -> passed.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/unit/services/render/test_timeline_render_service.py tests/unit/services/render/test_timeline_render_audio.py tests/unit/services/render/test_timeline_render_subtitles.py tests/unit/services/render/test_timeline_render_rework_assets.py tests/unit/services/render/test_video_concat.py tests/scripts/test_provider_chain_regression.py -q` -> passed, 23 passed, warnings only.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/unit/services/render/test_timeline_render_service.py tests/unit/services/render/test_timeline_render_audio.py tests/unit/services/render/test_timeline_render_subtitles.py tests/unit/services/render/test_timeline_render_rework_assets.py tests/unit/services/render/test_video_concat.py tests/scripts/test_provider_chain_regression.py tests/unit/test_deepseek_provider_v4.py tests/unit/test_model_utils.py tests/unit/services/providers/test_oai_image_provider.py tests/unit/test_volcengine_provider_video.py -q` -> passed, 41 passed, 7 skipped, warnings only.
- Manual TTS API probe:
  - `POST /api/v1/auth/login` -> 200.
  - `POST /api/v1/voice/tts` with MiniMax `speech-2.6-hd` and text `B-OT: Oh! A light in the dark land!` -> 200 with public `audio_url`.
- Restarted `ai-video-celery-worker` and verified the worker loaded
  `TimelineRenderService._render_to_temp_file(self, clips, subtitles, audio_track)`
  and source containing `audio_source`.
- Provider-chain smoke `provider-chain-dialogue-audio-smoke-20260526T041900Z`:
  - DeepSeek script, Timeline seed, MiniMax TTS, OpenAI image, Seedance video,
    Timeline patch, and render queue all executed through system APIs.
  - Artifact: `artifacts/runs/provider-chain-dialogue-audio-smoke-20260526T041900Z/provider_chain.json`.
  - The artifact is not accepted as passing because the harness poll saw
    `RemoteDisconnected` after render was queued.
  - Follow-up API and worker logs confirmed render job `24` succeeded anyway with
    output `https://resource.lets-gpt.com/timeline-renders/video/20260526/042641/96a19325.mp4`.
  - Worker logs recorded `Replacing audio track...` and `Burning 1 subtitle cues...`.
- Clean system API rerender:
  - Artifact: `artifacts/runs/dialogue-audio-rerender-20260526T042900Z/dialogue_audio_render.json`.
  - Timeline `18` version `2`, render job `25`.
  - Render log: `has_replaced_audio=true`,
    `audio_source=timeline.source.episode_audio`, `subtitle_count=1`,
    `output_asset_id=152`.
  - Output: `https://resource.lets-gpt.com/timeline-renders/video/20260526/042743/e73796af.mp4`.
- `ffprobe -v error -show_entries format=duration,size -show_streams -of json https://resource.lets-gpt.com/timeline-renders/video/20260526/042743/e73796af.mp4` -> video stream duration `4.041667`, audio stream AAC stereo duration `4.032000`, format size `1128220`.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files <changed files>` -> first run reformatted two touched files with black, second run passed.
- `pre-commit run --all-files` was not rerun in this commit because the immediately previous all-files run on this worktree failed on historical all-repo ruff/black/template/import issues and auto-touched hundreds of unrelated files; those unrelated changes were reversed and this commit used changed-file pre-commit plus targeted backend tests instead.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> passed; backend and frontend images built locally without push.

## Next Steps

- Run repo docs/contracts, changed-file pre-commit, and production image build before commit.
- Next quality boundary: full 30 second provider-chain run with dialogue pacing and visual quality review, not just a 4 second smoke.

## Linked Commits

Pending
