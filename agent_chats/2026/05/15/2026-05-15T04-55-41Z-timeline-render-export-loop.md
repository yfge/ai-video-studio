---
id: 2026-05-15T04-55-41Z-timeline-render-export-loop
date: 2026-05-15T04:55:41Z
participants:
  - user
  - codex
models:
  - GPT-5
tags:
  - timeline
  - render
  - export
  - frontend
  - backend
  - harness
related_paths:
  - ai-pic-backend/app/services/timeline_service.py
  - ai-pic-backend/app/services/render/timeline_render_service.py
  - ai-pic-backend/app/services/render/timeline_render_clips.py
  - ai-pic-backend/app/services/render/timeline_render_output.py
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineWorkspace.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineRenderPanel.tsx
  - scripts/harness/run_golden_path.py
  - scripts/harness/timeline_export_flow.py
summary: Implemented Timeline render/export closure from queued render_jobs through worker execution, media_assets output, operator UI, and harness checks.
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: Timeline Operator Render/Export 闭环.

## Goals

- Keep `POST /api/v1/timelines/{timeline_id}/render` and `GET /render-jobs` as the operator-facing API surface.
- Turn render jobs from queue-only records into executable attempts with status, progress, failure logs, and output asset persistence.
- Block render/export when Timeline video clips have no video asset; do not auto-trigger AI video generation or still-frame fallback.
- Add a Timeline operator toolbar for proxy/final render, status polling, retry, missing-clip visibility, and output links.
- Extend the Timeline export harness to require a completed render job with `output_asset`.

## Changes

- Added `force_new_attempt` to render job creation and `output_asset` to render job responses.
- Added a Celery Timeline render task and `TimelineRenderService` that verifies locked timeline versions, resolves video clips from Timeline clips or storyboard frames, fails with `missing_clips` details, runs the concat renderer, persists output to `media_assets(origin=rendered, asset_type=video)`, and updates `render_jobs`.
- Added focused Timeline render service tests for success, missing clips, stale versions, and API idempotency/retry behavior.
- Added Timeline render/export UI state, preflight readiness, clip video-material status in the inspector, render/export toolbar, polling, retry, output links, and storyboard navigation for replace clip v1.
- Extended `timeline_export_end_to_end` to queue a render job, poll `/render-jobs`, and assert `output_asset.file_url` or `output_asset.file_path`.
- Updated the Timeline execution docs to reflect the implemented render/export closure.

## Validation

- `python -m py_compile scripts/harness/run_golden_path.py scripts/harness/timeline_export_flow.py ai-pic-backend/app/services/timeline_service.py ai-pic-backend/app/services/timeline_responses.py ai-pic-backend/app/services/render/timeline_render_service.py ai-pic-backend/app/services/render/timeline_render_clips.py ai-pic-backend/app/services/render/timeline_render_output.py ai-pic-backend/app/services/task_worker_timeline_render.py`: passed.
- `cd ai-pic-backend && pytest tests/test_timeline_api.py tests/unit/services/render/test_episode_render_service.py tests/unit/services/render/test_timeline_render_service.py -q`: passed, 18 tests.
- `cd ai-pic-frontend && npm run test`: passed, 16 tests.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only; git ls-files --others --exclude-standard)`: passed for tracked and new files.
- `python scripts/check_repo_docs.py`: passed.
- `git diff --check`: passed.
- `cd ai-pic-frontend && npm run lint`: passed with 18 existing warnings and 0 errors.
- `cd ai-pic-frontend && npm run build`: passed.
- `pre-commit run --all-files`: failed outside this commit boundary. Formatter hooks modified unrelated historical files and the backend quick gate failed while importing `tests.fixtures.client` because `app.services.script_quality.checks` does not export `check_cliffhanger`; the unrelated formatter mutations were reverted to keep commit atomicity.
- `BUILD_PUSH=false ./docker/build_prod_images.sh`: passed for the whole dirty worktree before final commits; backend and frontend images were built locally without push with `IMAGE_TAG=f6cc4461`.
- `python scripts/harness/browser_flow.py --scenario episode_timeline_smoke --run-id timeline-render-export-20260515T0457Z --base-url http://localhost:8089 --username geyunfei --password 'Gyf@845261' --episode-id 124`: failed and wrote artifacts under `artifacts/runs/timeline-render-export-20260515T0457Z/`; Chrome DevTools timed out on `http://127.0.0.1:9222`, Playwright could not keep Chrome open under local permissions, and Selenium also failed to create a Chrome session.
- `python scripts/harness/run_golden_path.py --scenario timeline_export_end_to_end --run-id timeline-render-export-20260515T0457Z --api-url http://localhost:8000 --username geyunfei --password 'Gyf@845261' --script-id 1 --timeout-seconds 30`: failed with `HTTPConnectionPool(host='localhost', port=8000): Read timed out. (read timeout=15)` before login; no render request was reached.

## Next Steps

- Rerun `episode_timeline_smoke` and `timeline_export_end_to_end` once the local backend on `localhost:8000` responds and a script with Timeline video clips is available.
- Add stricter Timeline Spec schema/import validation and delete/rollback coverage in a separate pass.

## Linked Commits

- Pending.
