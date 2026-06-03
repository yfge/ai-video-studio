---
id: 2026-06-01T11-19-04Z-grid-storyboard-mode
date: "2026-06-01T11:19:04Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, frontend, storyboard, timeline]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/timelines.py
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/prompts/templates/storyboard_grid_sheet.txt
  - ai-pic-backend/app/prompts/templates/storyboard_grid_sheet.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_grid_video.txt
  - ai-pic-backend/app/prompts/templates/storyboard_grid_video.yaml
  - ai-pic-backend/app/schemas/timeline.py
  - ai-pic-backend/app/services/storyboard/grid_storyboard_prompt_bridge.py
  - ai-pic-backend/app/services/storyboard/grid_storyboard_sheet_processor.py
  - ai-pic-backend/app/services/storyboard/grid_storyboard_sheet_service.py
  - ai-pic-backend/app/services/storyboard/grid_storyboard_sheet_spec.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/app/services/task_worker_grid_storyboard.py
  - ai-pic-backend/app/services/timeline_clip_video_grid_reference.py
  - ai-pic-backend/app/services/timeline_clip_video_rework_queue_service.py
  - ai-pic-backend/app/services/timeline_clip_video_rework_submission.py
  - ai-pic-backend/app/services/video/video_task_timeline_rework_updater.py
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardGridContent.tsx
  - docs/exec-plans/active/grid-storyboard-mode.md
summary: "Add grid storyboard support mode for Timeline-native short-drama production"
---

## User Prompt

现在对故事板的支持情况？是现在短剧生成已经变成了用生图模型直接生成宫格图的故事板，然后用故事板生成视频。

## Goals

- Add a grid storyboard support mode for short-drama generation.
- Bridge Timeline clip/image prompts into storyboard-grid image prompts.
- Persist the generated grid storyboard sheet as support metadata on the Timeline.
- Allow clip video rework/generation to use the storyboard grid sheet as a reference and target a specific panel.
- Expose the mode in the episode workspace Storyboard tab and in clip provider rework controls.

## Changes

- Added storyboard-grid prompt bridge, prompt templates, sheet specification, queue service, Celery processor task, and Timeline API endpoint:
  `POST /api/v1/timelines/{timeline_id}/storyboard-grid/generate`.
- Added Timeline support metadata for `storyboard_grid_sheet_asset_ref` and grid panel source references so generated videos can trace back to the sheet and panel.
- Added `storyboard_grid_panel` reference mode for clip video rework, including provider `reference_images` payload wiring and persisted task/media context.
- Added frontend API types/endpoints, a `逐镜头` / `宫格故事板` Storyboard tab mode, grid sheet preview/panel list UI, and rework checkbox for using `Panel N` as the video reference.
- Updated harness smoke text and documented the grid storyboard support mode in `docs/timeline-rendering-pipeline.md`.
- Added active execution plan at `docs/exec-plans/active/grid-storyboard-mode.md`.

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py tests/unit/test_storyboard_prompt_templates.py tests/test_timeline_storyboard_grid_api.py tests/test_timeline_storyboard_grid_processor.py tests/test_timeline_clip_video_rework_api.py tests/test_timeline_clip_video_grid_rework_api.py -q`
  - Result: 20 passed, 138 warnings.
- `cd ai-pic-frontend && npm run test`
  - Result: 25 passed.
- `cd ai-pic-frontend && npm run lint`
  - Result: passed with existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, `StoryboardEditor.js`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run build`
  - Result: passed; Next.js generated all static/dynamic routes successfully.
- `python scripts/check_repo_docs.py`
  - Result: passed.
- `python scripts/check_repo_contracts.py --mode audit`
  - Result: passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
  - Result: passed.
- Browser validation:
  - Existing local Next server was listening on `http://localhost:3091`; starting a new server on `3001` failed because `.next/dev/lock` was already held.
  - In-app browser access to `http://localhost:3091/episodes/1/workspace?tab=storyboard` was blocked by browser security policy, so no browser screenshot or interaction evidence was collected.

## Next Steps

- Run a real workspace browser flow once the local browser policy allows the selected dev-server URL or after the workspace is served on an allowed port.
- Run provider-backed generation with real credentials to verify actual grid sheet image generation and downstream video generation quality.

## Linked Commits

Pending.
