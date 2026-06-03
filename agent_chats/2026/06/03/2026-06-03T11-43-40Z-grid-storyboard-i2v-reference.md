---
id: 2026-06-03T11-43-40Z-grid-storyboard-i2v-reference
date: "2026-06-03T11:43:40Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, storyboard-grid, video-generation, seedance]
related_paths:
  - ai-pic-backend/app/services/video/video_task_dispatcher.py
  - ai-pic-backend/app/services/timeline_clip_video_rework_submission.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video_request.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video_tasks.py
  - ai-pic-backend/tests/test_timeline_clip_video_grid_rework_api.py
  - ai-pic-backend/tests/unit/services/video/test_video_task_dispatcher.py
  - ai-pic-backend/tests/unit/services/video/test_timeline_clip_video_rework_submission.py
summary: "Treat grid storyboard sheet references as image-to-video inputs for Seedance rework"
---

## User Prompt

现在故事板机制是有问题，故事板指的是在分镜生成的部分，提示gpt-img-2 生成宫格图，即长镜头中每一步的展示 ，然后用这个宫格图使用seedance 2.0 生成视频

## Goals

- Preserve the Timeline-first grid storyboard support model.
- Keep the generated grid sheet as a Seedance 2.0 visual reference, not as a separate storyboard orchestration source.
- Fix the reference-only grid path so it is submitted and recorded as image-to-video instead of text-to-video.

## Changes

- Updated `VideoTaskDispatcher` to classify requests with `reference_images` / reference visual media as `image_to_video` even when `image_url` is absent.
- Updated Timeline clip video rework submission to persist reference-only grid rework tasks with `model_type="image_to_video"` and matching generation metadata.
- Added a Volcengine helper so exception fallback paths also classify reference-media requests as image-to-video.
- Kept the grid sheet in `reference_images`; did not set it as `first_frame`, because the sheet is a multi-panel reference image and should not become the generated video's opening frame.
- Added dispatcher and submission tests for the reference-only grid storyboard path, and updated the grid rework lineage test contract.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/unit/services/video/test_video_task_dispatcher.py tests/unit/services/video/test_timeline_clip_video_rework_submission.py tests/test_timeline_clip_video_grid_rework_api.py tests/unit/test_volcengine_provider_video.py -q` -> pass, 15 tests.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/video/video_task_dispatcher.py ai-pic-backend/app/services/video/video_task_dispatch_helpers.py ai-pic-backend/app/services/timeline_clip_video_rework_submission.py ai-pic-backend/app/services/providers/volcengine_provider/video_request.py ai-pic-backend/app/services/providers/volcengine_provider/video.py ai-pic-backend/app/services/providers/volcengine_provider/video_tasks.py ai-pic-backend/tests/test_timeline_clip_video_grid_rework_api.py ai-pic-backend/tests/unit/services/video/test_video_task_dispatcher.py ai-pic-backend/tests/unit/services/video/test_timeline_clip_video_rework_submission.py agent_chats/2026/06/03/2026-06-03T11-43-40Z-grid-storyboard-i2v-reference.md` -> pass after splitting dispatcher helpers under service file-size and legacy-reference contracts.
- `cd ai-pic-backend && python run_tests.py quick` -> not completed; setup failed during `pip install -r requirements-test.txt` because Python 3.13 dependency resolution found `pydantic==2.5.0` incompatible with `langchain-core==0.2.43` requiring `pydantic>=2.7.4`.

2. Browser or MCP validation:

- Not run. This change is a backend task-submission/model-type fix with no frontend/API shape change. A real Seedance browser flow would trigger paid provider work, so validation stayed at targeted backend and provider request-contract tests.

3. Conflict signals and corrections:

- Initial assumption: the grid path might need the storyboard sheet moved into `image_url`.
- Contradicting evidence: the existing prompt says "use panel N only" from a multi-panel sheet, and Volcengine Seedance 2.0 request code already supports `reference_images` as visual media.
- Correction: left `image_url` empty for grid mode, kept the sheet in `reference_images`, and fixed dispatcher/submission model-type inference so Seedance receives and records it as image-to-video.

## Next Steps

- A future provider-backed smoke can verify a real Seedance 2.0 task when budget/quota is available.

## Linked Commits

- This commit.
