---
id: 2026-05-26T05-16-44Z-timeline-dialogue-audio-segments
date: "2026-05-26T05:16:44Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - timeline
  - render
  - dialogue-audio
  - provider-chain
  - seedance
related_paths:
  - ai-pic-backend/app/services/render/timeline_render_audio.py
  - ai-pic-backend/app/services/render/timeline_render_service.py
  - ai-pic-backend/app/services/render/timeline_render_types.py
  - ai-pic-backend/app/services/render/video_concat.py
  - ai-pic-backend/app/services/render/video_ffmpeg.py
  - scripts/harness/provider_chain_audio.py
  - scripts/harness/provider_chain_timeline_payloads.py
  - ai-pic-backend/tests/unit/services/render/test_timeline_render_audio.py
  - ai-pic-backend/tests/unit/services/render/test_video_concat.py
  - ai-pic-backend/tests/scripts/test_provider_chain_regression.py
  - docker/Dockerfile.backend.dev
  - docker/Dockerfile.backend.prod
  - docs/timeline-rendering-pipeline.md
  - tasks.md
summary: Add Timeline-timed dialogue audio segment rendering and verify a real full-30s provider-chain regression.
---

## User Prompt

继续；按“时间第一性”先生成时间轴，并用真实系统 API 回归 DeepSeek 生文、OpenAI 生图、Seedance 2.0 生视频。不能把手工拼片或单段音频冒充全流程。

## Goals

- 让 provider-chain harness 保持 Timeline-first：先创建 Timeline seed，再生成和回填媒体资产。
- 把 dialogue audio 从整轨 `source.episode_audio` 扩展到 per-dialogue clip audio，并按 `start_ms` / `end_ms` 混音。
- 证明 full-30s 真实链路：DeepSeek 剧本/对白、OpenAI `gpt-image-2` 卡通角色图、Volcengine Seedance 2.0 两段视频、Timeline render/export。
- 修复回归中暴露的 ffmpeg 分段音频无限输出和中文字幕字体缺失问题。

## Changes

- Added `TimelineAudioSegment` and changed Timeline dialogue audio resolution so source episode audio remains supported, while dialogue clip `asset_ref` URLs resolve into timed audio segments.
- Updated Timeline rendering to pass `VideoAudioSegment` values into `concat_video_clips`; render logs now expose `audio_segment_count`.
- Added ffmpeg audio segment composition with bounded output duration and timeout handling, then replaced final video audio with the composed Timeline audio.
- Updated provider-chain TTS generation to call `/api/v1/voice/tts` per dialogue clip and attach each returned public URL back to the matching Timeline `clip_id`, without writing fake `source.episode_audio`.
- Added Noto CJK subtitle font support in backend Dockerfiles and forced subtitle burn-in to use `Noto Sans CJK SC`.
- Updated docs and task board with the full-30s provider-chain evidence and the remaining production-quality caveats.

## Validation

- `python -m py_compile ai-pic-backend/app/services/render/timeline_render_types.py ai-pic-backend/app/services/render/timeline_render_audio.py ai-pic-backend/app/services/render/timeline_render_service.py ai-pic-backend/app/services/render/video_ffmpeg.py ai-pic-backend/app/services/render/video_concat.py scripts/harness/provider_chain_audio.py scripts/harness/provider_chain_timeline_payloads.py scripts/harness/provider_chain_regression.py` passed.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/unit/services/render/test_timeline_render_audio.py tests/unit/services/render/test_video_concat.py tests/scripts/test_provider_chain_regression.py -q` passed: `20 passed`.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/unit/services/render/test_timeline_render_service.py tests/unit/services/render/test_timeline_render_audio.py tests/unit/services/render/test_timeline_render_subtitles.py tests/unit/services/render/test_timeline_render_rework_assets.py tests/unit/services/render/test_video_concat.py tests/scripts/test_provider_chain_regression.py tests/unit/test_deepseek_provider_v4.py tests/unit/test_model_utils.py tests/unit/services/providers/test_oai_image_provider.py tests/unit/test_volcengine_provider_video.py -q` passed: `44 passed, 7 skipped`.
- Restarted `ai-video-celery-worker` and confirmed the container loaded the `audio_segments` render path.
- `python scripts/harness/provider_chain_regression.py --mode full-30s --run-id provider-chain-dialogue-segments-full-30s-20260526T045229Z --api-url http://localhost:8000 --episode-id 133 --script-id 117 --timeout-seconds 1800 --poll-interval-seconds 5` passed and wrote `artifacts/runs/provider-chain-dialogue-segments-full-30s-20260526T045229Z/provider_chain.json`.
- Full-30s harness evidence: DeepSeek `deepseek-v4-flash` generated title `电路朋友`; Timeline `19` seed was created before image/video generation with `dialogue=2`, `video=2`, `subtitle=2`; MiniMax `speech-2.6-hd` generated two dialogue audio URLs; OpenAI `gpt-image-2` generated character image `https://resource.lets-gpt.com/ai-generated/virtual-ip/image/20260526/045341/357f6b99.png`; Volcengine `doubao-seedance-2-0-260128` generated two 15 second video clips; render job `26` succeeded with `audio_source=timeline.dialogue.asset_ref`, `audio_segment_count=2`, and `subtitle_count=2`.
- The first full-30s render exposed unreadable Chinese subtitles because the worker lacked CJK fonts. Installed Noto CJK in the current worker container, patched Dockerfiles for repeatability, restarted worker, and rerendered the same Timeline `19` version `2` with job `27`.
- CJK-font rerender evidence: `artifacts/runs/provider-chain-dialogue-segments-full-30s-20260526T045229Z/subtitle_font_rerender.json`; output `https://resource.lets-gpt.com/timeline-renders/video/20260526/051434/7849fd70.mp4`.
- `ffprobe` for the CJK-font rerender output recorded video duration `30.125000` and audio duration `30.080000`; JSON saved to `artifacts/runs/provider-chain-dialogue-segments-full-30s-20260526T045229Z/final_ffprobe.json`.
- Extracted visual frames `frames/font_frame_02s.jpg` and `frames/font_frame_17s.jpg`; both show the robot character and readable Chinese subtitles.
- Browser/Chrome validation was not claimed. This run used system API, Docker worker logs, ffprobe, and extracted frame evidence because the requested regression target was the provider chain and render artifact.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` passed; no changed-file diff rules applied.
- `git diff --check` passed.
- `pre-commit run --files <changed files>` passed, including repository docs, contracts, ledger enforcement, and backend quick gate.
- `pre-commit run --all-files` was not rerun in this commit because the same worktree already showed historical whole-repo failures and auto-touched unrelated files earlier in the session; this commit used the repository file-scoped gate for the exact changed paths instead.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` passed. The classic Docker builder ignored the platform override but built backend and frontend images locally; backend build installed `fonts-noto-cjk`.

## Next Steps

- Do not treat this as proof of commercial content quality. Character consistency, acting direction, lip-sync, visual taste, and repeatable 10-sample production quality still need separate scored runs.
- Consider reducing subtitle font size or adding line wrapping rules for dense dialogue; the subtitles are now readable but visually too large for production.
- Consider persisting generated Seedance clips to project storage before render, because current provider URLs are signed Volcengine URLs.

## Linked Commits

Pending
