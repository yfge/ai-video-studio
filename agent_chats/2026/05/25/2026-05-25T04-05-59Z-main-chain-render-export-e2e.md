---
id: 2026-05-25T04-05-59Z-main-chain-render-export-e2e
date: "2026-05-25T04:05:59Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, timeline, render, harness, docs]
related_paths:
  - ai-pic-backend/app/services/timeline_import_service.py
  - ai-pic-backend/app/services/timeline_storyboard_spec_builder.py
  - ai-pic-backend/app/services/render/timeline_render_clips.py
  - ai-pic-backend/app/services/render/video_download.py
  - scripts/harness/timeline_export_flow.py
  - tasks.md
  - docs/exec-plans/active/main-chain-commercial-readiness.md
summary: "Bridge legacy storyboard video assets into Timeline render/export and record passing main-chain harness evidence"
---

## User Prompt

继续

## Goals

- Continue the active main-chain readiness plan after Phase 1 closure.
- Remove the blocker that kept real `Episode -> Timeline -> Render -> Export` from passing.
- Preserve Timeline as the production source of truth while providing a narrow legacy storyboard video migration bridge for existing sample data.
- Produce real local harness evidence and update the active docs with the new state.

## Changes

- Added `storyboard_has_assets()` and changed the timeline pipeline storyboard step to reuse existing storyboard assets instead of failing when `overwrite_storyboard=false`.
- Added a legacy storyboard video Timeline Spec builder for the narrow case where an old audio timeline is non-monotonic but the script already has renderable storyboard videos.
- Added Timeline render resolver fallback by legacy storyboard timing for frames without `timeline_clip_id`.
- Added retry, timeout, force-close headers, and harness failed-attempt retry support for Timeline video render/download.
- Split legacy matching, legacy storyboard spec building, video downloading, and FFmpeg helpers into focused modules so the changed backend service files stay under repository file-size limits.
- Updated `tasks.md`, `main-chain-commercial-readiness.md`, and Timeline execution plans to mark the real render/export evidence as passed and to keep first-class clip asset lineage as remaining work.

## Validation

- `cd ai-pic-backend && python -m py_compile app/services/audio/storyboard_timeline_helpers.py app/services/script/timeline_storyboard_queue.py app/services/render/timeline_render_clips.py app/services/render/timeline_render_legacy_match.py app/services/render/video_concat.py app/services/render/video_download.py app/services/render/video_ffmpeg.py app/services/timeline_import_service.py app/services/timeline_spec_builder.py app/services/timeline_storyboard_spec_builder.py tests/test_timeline_import_service.py tests/unit/services/render/test_timeline_render_service.py tests/unit/services/render/test_video_concat.py tests/unit/services/render/test_video_download.py tests/unit/services/script/test_timeline_storyboard_queue.py`: passed.
- `python -m py_compile scripts/harness/timeline_export_flow.py`: passed.
- `cd ai-pic-backend && pytest tests/test_timeline_import_service.py tests/unit/services/render/test_timeline_render_service.py tests/unit/services/render/test_video_concat.py tests/unit/services/render/test_video_download.py tests/unit/services/script/test_timeline_storyboard_queue.py tests/integration/test_timeline_pipeline_import_api.py -q`: passed, 20 tests.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`: passed.
- `python scripts/check_repo_contracts.py --mode audit`: passed.
- `git diff --check`: passed.
- `pre-commit run ruff --files <changed files>`, `pre-commit run black --files <changed files>`, `pre-commit run isort --files <changed files>`, and `pre-commit run prettier --files <changed files>`: passed.
- `pre-commit run --all-files`: failed on existing repository baseline issues, including historical ruff findings across unrelated files, a non-Python template parse failure in `app/cli/templates/migration_template.py`, and backend quick gate import failure `cannot import name 'check_cliffhanger' from 'app.services.script_quality.checks'`. Hook auto-edits to unrelated files were discarded.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`: passed; backend and frontend images built locally without push, tagged with `IMAGE_TAG=43c87a3d`.
- `python scripts/harness/run_golden_path.py --scenario timeline_export_end_to_end --run-id main-chain-e2e-lineage-20260525T035658Z --api-url http://localhost:8000 --base-url http://localhost:8089 --username geyunfei --password '<redacted>' --script-id 117 --timeout-seconds 600`: failed before the fallback because script `117` had non-monotonic legacy audio timeline beats and no Timeline row.
- `python scripts/harness/run_golden_path.py --scenario timeline_export_end_to_end --run-id main-chain-e2e-lineage-20260525T040109Z --api-url http://localhost:8000 --base-url http://localhost:8089 --username geyunfei --password '<redacted>' --script-id 117 --timeout-seconds 900`: reached Timeline `2` and render job `2`, but failed on remote video download with `Server disconnected`.
- Restarted `ai-video-celery-worker` so the worker loaded the download retry change.
- `python scripts/harness/run_golden_path.py --scenario timeline_export_end_to_end --run-id main-chain-e2e-lineage-20260525T040437Z --api-url http://localhost:8000 --base-url http://localhost:8089 --username geyunfei --password '<redacted>' --script-id 117 --timeout-seconds 900`: passed. Evidence is in `artifacts/runs/main-chain-e2e-lineage-20260525T040437Z/golden_path.json`; task `5989` completed, Timeline `2` version `1` rendered, render job `3` succeeded, and output asset `1` has `file_url=https://resource.lets-gpt.com/timeline-renders/video/20260525/040535/7220b9a3.mp4`.

## Next Steps

- Implement Timeline delete/rollback with permission and stale-version tests.
- Add stricter Timeline Spec schema/import validation.
- Replace the migration bridge with first-class clip asset lineage for storyboard images/videos, generated clip videos, and final render outputs.
- Start production sample validation only after delete/rollback and validation hardening are in place.

## Linked Commits

- Pending.
